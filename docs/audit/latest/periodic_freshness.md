# audit_periodic_freshness — mandatory recurring audits

Registry: `docs/audit/periodic.json` — grace **7** days. BROKEN: **0**, OVERDUE: **2**, DUE: **0**

| id | title | cadence (d) | age (d) | due in (d) | state | owner |
|---|---|---|---|---|---|---|
| code_duplication | Refactor duplicated code (audit tooling + yaml templates) | 30 | 27 | 3 | ok | unassigned |
| test_coverage | Test coverage floor (OpenRA.Mods.Cameo + tools/) | 30 | 27 | 3 | ok | unassigned |
| recent_changes_review | Review recent changes (regression review of the last N days of commits) | 14 | 27 | -13 | OVERDUE | unassigned |
| error_handling | Error handling in tools/ (bare except, silent pass, unguarded IO) | 30 | 27 | 3 | ok | unassigned |
| security_scan | Security scan (dependencies, secrets, unsafe shell/deserialisation) | 14 | 27 | -13 | OVERDUE | unassigned |
| armor_exposure | Re-measure armor exposure (coverage x intensity) — it drifts with every weapon change | 30 | 22 | 8 | ok | unassigned |


## OVERDUE — a scheduled scan is late

- recent_changes_review (27d old, cadence 14d)
- security_scan (27d old, cadence 14d)

Run the command from the registry, then stamp it with `--record <id>`.
The tree itself is fine — this is a calendar fact, so it does NOT block the per-commit suite.

