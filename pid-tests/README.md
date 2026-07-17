# PID checks

This directory contains tests for checking PaNET PIDs are functioning correct.

The following tests are provided:

|---|---|
|File| Target service |
|---|---|
| `check-w3id.json` | Redirections in `https://w3id.org/` |
|`check-purl.json` | Redirections in `https://purl.org/` |
|---|---|

To run the tests, you need the `test-redirection` script from [w3id-tester repo](https://github.com/pan-ontologies/w3id-tester).

Example command to check w3id.org: `../../w3id-tester/test-redirection -c check-w3c.json`

Example command to check purl.org: `./test-redirection -c check-purl.json`.
