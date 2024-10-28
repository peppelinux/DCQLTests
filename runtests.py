import json
import os

import dcql

def get_test_cases(path):
    return [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.startswith('testcase')]

def load_json(path):
    with open(path) as f:
        return json.load(f)

def main():
    test_cases = get_test_cases(os.getcwd())
    test_cases.sort()
    print(test_cases)
    credential_store = load_json('credentials.json')
    for test_path in test_cases:
        test = load_json(test_path)
        print('Running test: {}'.format(test['name']))

        matched_credentials = dcql.dcql_query(test['dcql_query'], credential_store['credentials'])
        expected_result = test['expected_result']['matched_credentials']
        print('Matched : {}'.format(json.dumps(matched_credentials, indent=None)))
        if expected_result == matched_credentials:
            print('PASS')
        else:
            print('Expected: {}'.format(json.dumps(expected_result)))
            print('FAIL')
        
if __name__ == '__main__':
    main()