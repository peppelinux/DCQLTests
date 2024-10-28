# DCQLTests
Test cases for the DCQL query language

## Test Runner

To run the tests:
`python runtests.py`

[dcql](dcql.py) provides a reference implementation in python.

## Test Cases

- [credentials.json](credentials.json) contains a database of test credentials on which the queries are performed.
- The testcase-* files contain the test cases. Each one contains a dcql_query and the expected results when executed against the credentials stored in the test database.