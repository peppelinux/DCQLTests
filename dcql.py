

def match_credental(credential, credential_store):
    matched_credentials = [] 

    # Check for required params
    if 'id' not in credential:
        raise RuntimeError('id missing from credential')
    if 'format' not in credential:
        raise RuntimeError('format missing from credential')
    id = credential['id']
    format = credential['format']

    # check for optional params
    meta = None if 'meta' not in credential else credential['meta']
    claims = None if 'claims' not in credential else credential['claims']
    claim_sets = None if 'claim_sets' not in credential else credential['claim_sets']

    if claims is None and claim_sets is not None:
        raise RuntimeError('claim_set without claims')
    
    # Filter by format
    candidates = None if format not in credential_store else credential_store[format]
    # Bail if there are no credentials matching this format
    if candidates is None:
        return matched_credentials
    
    # Filter by meta
    if meta is not None:
        # meta is intpreted on a per-format basis
        if format == 'mso_mdoc':
            # Check for a doctype
            doctype_value = None if 'doctype_value' not in meta else meta['doctype_value']
            if doctype_value is not None:
                # Filter by doctype
                candidates = None if doctype_value not in candidates else candidates[doctype_value]
        else:
            # Unknown format. Can't parse meta, so bail
            return matched_credentials
        
    # Bail if there are no credentials after filtering on meta
    if candidates is None:
        return matched_credentials
    
    # Match on the claims
    if claims is None:
        # Match every candidate
        for candidate in candidates:
            matched_credential = {}
            matched_credential['id'] = candidate['id']
            matched_claim_names = []

            # Matching logic is peformed on a per-format basis. This is a bit annoying
            if format == 'mso_mdoc':
                for namespace, namespace_val in candidate['namespaces'].items():
                    for attr, attr_val in namespace_val.items():
                        matched_claim_names.append(attr_val['display'])
                matched_credential['matched_claim_names'] = matched_claim_names
                matched_credentials.append(matched_credential)
    else:
        if claim_sets is None:
            # Match candidates that contain all claims requested
            for candidate in candidates:
                matched_credential = {}
                matched_credential['id'] = candidate['id']
                matched_claim_names = []

                for claim in claims:
                    # Matching logic is peformed on a per-format basis. This is a bit annoying
                    if format == 'mso_mdoc':
                        namespace = None if 'namespace' not in claim else claim['namespace']
                        claim_name = None if 'claim_name' not in claim else claim['claim_name']
                        if namespace is None:
                            raise RuntimeError('namespace missing from an mso-mdoc claim')
                        if claim_name is None:
                            raise RuntimeError('claim_name missing from an mso-mdoc claim')
                        if namespace in candidate['namespaces']:
                            if claim_name in candidate['namespaces'][namespace]:
                                matched_claim_names.append(candidate['namespaces'][namespace][claim_name]['display'])

                matched_credential['matched_claim_names'] = matched_claim_names

                if len(matched_claim_names) == len(claims):
                    matched_credentials.append(matched_credential)
        else:
            # Match the claim sets
            for candidate in candidates:
                matched_credential = {}
                matched_credential['id'] = candidate['id']
                matched_claim_ids = {}

                for claim in claims:
                    claim_id = None if 'id' not in claim else claim['id']
                    if claim_id is None:
                        raise RuntimeError('claim is missing ID when claim_set is present')

                    # Matching logic is peformed on a per-format basis. This is a bit annoying
                    if format == 'mso_mdoc':
                        namespace = None if 'namespace' not in claim else claim['namespace']
                        claim_name = None if 'claim_name' not in claim else claim['claim_name']
                        if namespace is None:
                            raise RuntimeError('namespace missing from an mso-mdoc claim')
                        if claim_name is None:
                            raise RuntimeError('claim_name missing from an mso-mdoc claim')
                        if namespace in candidate['namespaces']:
                            if claim_name in candidate['namespaces'][namespace]:
                                matched_claim_ids[claim_id] = candidate['namespaces'][namespace][claim_name]['display']

                for claim_set in claim_sets:
                    matched_claim_names = []
                    for c in claim_set:
                        if c in matched_claim_ids:
                            matched_claim_names.append(matched_claim_ids[c])
                    if len(matched_claim_names) == len(claim_set):
                        matched_credential['matched_claim_names'] = matched_claim_names
                        matched_credentials.append(matched_credential)
                        break
                    

    return matched_credentials



def dcql_query(query, credential_store):
    matched_credentials = {} 
    
    if 'credentials' not in query:
        raise RuntimeError('credentials missing')
    credentials = query['credentials']


    for credential in credentials:
        id = None if 'id' not in credential else credential['id']
        if id is None:
            raise RuntimeError('id missing from credential')
        
        matched = match_credental(credential, credential_store)
        matched_credentials[id] = matched
        continue

    return matched_credentials
