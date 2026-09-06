# audit_security — credentials, code execution, supply chain

Files scanned: **3081**

| code | meaning | count | baseline |
|---|---|---|---|
| S1 | committed credential shapes | 0 | 0 |
| S2 | code execution from data | 4 | 0 |
| S3 | plaintext http:// download | 0 | 0 |
| S4 | unpinned third-party GitHub Action | 0 | 0 |
| S5 | unpinned/floating NuGet package | 0 | 0 |
| S6 | installer download without SHA | 0 | 0 |


## S1 — 0 finding(s)

_none found_


## S2 — 4 finding(s)

| file | line | detail |
|---|---|---|
| tools/balance/formula.py | 59 | `eval()` |
| tools/tests/test_audit_run_all_parser.py | 34 | `exec()` |
| wt_base/tools/balance/formula.py | 58 | `eval()` |
| wt_base/tools/tests/test_audit_run_all_parser.py | 34 | `exec()` |


## S3 — 0 finding(s)

_none found_


## S4 — 0 finding(s)

_none found_


## S5 — 0 finding(s)

_none found_


## S6 — 0 finding(s)

_none found_


## Not covered here

- Known-vulnerable NuGet/npm advisories: needs network; run
  `dotnet list CameoMod.sln package --vulnerable --include-transitive`
  as part of the periodic security run and paste the output into the
  evidence file.


## FAIL

- S2: 4 > baseline 0

