_required_in_credential = {
    "id": None,
    "format": None
}

def match_credental(credential, credential_store):
    matched_credentials = []

    for _item in _required_in_credential:
        if _item not in credential: 
            raise RuntimeError(f"{_item} missing from credential")
        _required_in_credential[_item] = credential.get(_item)

    # check for optional params
    meta = credential.get("meta", None)
    claims = credential.get("claims", None)
    claim_sets = credential.get("claim_sets", None)

    if claims is None and claim_sets is not None:
        raise RuntimeError("claim_set without claims")

    # Filter by format
    candidates = credential_store.get(_required_in_credential["format"], None)
    # Bail if there are no credentials matching this format
    if candidates is None:
        return matched_credentials

    # Filter by meta
    if meta is not None:
        # meta is intpreted on a per-format basis
        if _required_in_credential["format"] == "mso_mdoc":
            # Check for a doctype
            doctype_value = meta.get("doctype_value", None)
            if doctype_value is not None:
                # Filter by doctype
                candidates = candidates.get(doctype_value, None)
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
            matched_credential["id"] = candidate["id"]
            matched_claim_names = []

            # Matching logic is peformed on a per-format basis. This is a bit annoying
            if _required_in_credential["format"] == "mso_mdoc":
                for namespace, namespace_val in candidate["namespaces"].items():
                    for attr, attr_val in namespace_val.items():
                        matched_claim_names.append(attr_val["display"])
                matched_credential["matched_claim_names"] = matched_claim_names
                matched_credentials.append(matched_credential)
    else:
        if claim_sets is None:
            # Match candidates that contain all claims requested
            for candidate in candidates:
                matched_credential = {}
                matched_credential["id"] = candidate["id"]
                matched_claim_names = []

                for claim in claims:
                    claim_values = claim.get("values", None)
                    # Matching logic is peformed on a per-format basis. This is a bit annoying
                    if _required_in_credential["format"] == "mso_mdoc":
                        namespace = claim.get("namespace", None)
                        claim_name = claim.get("claim_name", None)
                        if namespace is None:
                            raise RuntimeError("namespace missing from an mso-mdoc claim")
                        if claim_name is None:
                            raise RuntimeError("claim_name missing from an mso-mdoc claim")
                        if namespace in candidate["namespaces"]:
                            if claim_name in candidate["namespaces"][namespace]:
                                if claim_values is not None:
                                    for v in claim_values:
                                        if v == candidate["namespaces"][namespace][claim_name]["value"]:
                                            matched_claim_names.append(candidate["namespaces"][namespace][claim_name]["display"])
                                            break
                                else:
                                    matched_claim_names.append(candidate["namespaces"][namespace][claim_name]["display"])

                matched_credential["matched_claim_names"] = matched_claim_names

                if len(matched_claim_names) == len(claims):
                    matched_credentials.append(matched_credential)
        else:
            # Match the claim sets
            for candidate in candidates:
                matched_credential = {}
                matched_credential["id"] = candidate["id"]
                matched_claim_ids = {}

                for claim in claims:
                    claim_values = claim.get("values", None)
                    claim_id = claim.get("id", None)
                    if claim_id is None:
                        raise RuntimeError(
                            "claim is missing ID when claim_set is present"
                        )

                    # Matching logic is peformed on a per-format basis. This is a bit annoying
                    if _required_in_credential["format"] == "mso_mdoc":
                        namespace = claim.get("namespace", None)
                        claim_name = claim.get("claim_name", None)
                        if namespace is None:
                            raise RuntimeError("namespace missing from an mso-mdoc claim")
                        if claim_name is None:
                            raise RuntimeError("claim_name missing from an mso-mdoc claim")
                        if namespace in candidate["namespaces"]:
                            if claim_name in candidate["namespaces"][namespace]:
                                if claim_values is not None:
                                    for v in claim_values:
                                        if v == candidate["namespaces"][namespace][claim_name]["value"]:
                                            matched_claim_ids[claim_id] = candidate["namespaces"][namespace][claim_name]["display"]
                                            break
                                else:
                                    matched_claim_ids[claim_id] = candidate["namespaces"][namespace][claim_name]["display"]

                for claim_set in claim_sets:
                    matched_claim_names = []
                    for c in claim_set:
                        if c in matched_claim_ids:
                            matched_claim_names.append(matched_claim_ids[c])
                    if len(matched_claim_names) == len(claim_set):
                        matched_credential["matched_claim_names"] = matched_claim_names
                        matched_credentials.append(matched_credential)
                        break

    return matched_credentials


def dcql_query(query, credential_store):
    matched_credentials = {}
    candidate_matched_credentials = {}
    credentials = query.get("credentials", None)
    credential_sets = query.get("credential_sets", None)
    if credentials is None:
        raise RuntimeError("credentials missing")

    for credential in credentials:
        _required_in_credential["id"] = credential.get("id", None)
        if _required_in_credential["id"] is None:
            raise RuntimeError("id missing from credential")
        matched = match_credental(credential, credential_store)
        if len(matched) > 0:
            candidate_matched_credentials[
                _required_in_credential["id"]
            ] = matched

    if credential_sets is None:
        if len(credentials) == len(candidate_matched_credentials.keys()):
            matched_credentials = candidate_matched_credentials
    else:
        matched_credential_set = {}
        matched_credential_set_optional = {}
        required_count = 0
        for credential_set in credential_sets:
            options = credential_set.get("options", None)
            if options is None:
                raise RuntimeError("options missing from credential_set")
            required = credential_set.get("required", True)
            if required:
                required_count = required_count + 1
            for option in options:
                matched_options = []
                for cred in option:
                    if cred in candidate_matched_credentials:
                        matched_options.append(cred)
                if len(matched_options) == len(option):
                    # This option matched
                    for m in matched_options:
                        if required:
                            matched_credential_set[m] = candidate_matched_credentials[m]
                        else:
                            matched_credential_set_optional[m] = candidate_matched_credentials[m]
                    break
        if required_count == len(matched_credential_set.keys()):
            matched_credentials = matched_credential_set | matched_credential_set_optional

    return matched_credentials
