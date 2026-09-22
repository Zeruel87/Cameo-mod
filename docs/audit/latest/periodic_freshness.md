# audit_periodic_freshness — mandatory recurring audits

Registry: `docs/audit/periodic.json` — grace **7** days. BROKEN: **0**, OVERDUE: **0**, DUE: **3**

| id | title | cadence (d) | age (d) | due in (d) | state | owner |
|---|---|---|---|---|---|---|
| code_duplication | Refactor duplicated code (audit tooling + yaml templates) | 30 | 31 | -1 | DUE | unassigned |
| test_coverage | Test coverage floor (OpenRA.Mods.Cameo + tools/) | 30 | 31 | -1 | DUE | unassigned |
| recent_changes_review | Review recent changes (regression review of the last N days of commits) | 14 | 4 | 10 | ok | unassigned |
| error_handling | Error handling in tools/ (bare except, silent pass, unguarded IO) | 30 | 31 | -1 | DUE | unassigned |
| security_scan | Security scan (dependencies, secrets, unsafe shell/deserialisation) | 14 | 4 | 10 | ok | unassigned |
| armor_exposure | Re-measure armor exposure (coverage x intensity) — it drifts with every weapon change | 30 | 26 | 4 | ok | unassigned |


## DUE — run these next

- code_duplication (31d old, cadence 30d)
- test_coverage (31d old, cadence 30d)
- error_handling (31d old, cadence 30d)

