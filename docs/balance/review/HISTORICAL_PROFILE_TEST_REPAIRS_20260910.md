# Historical profile test repairs, 10 September 2026

This is test tooling only. No weapon, actor, price, HP, engine, converter or original
historical report/fixture/hash changes. Source starts at
`584a5e4cb4667820b60388fd05d90090c88513d7`. The reopened audit identified fourteen
retained historical-converter failure/error identities, distinct from the real
upgrade-damage regressions handled separately.

## Causes and exact boundaries

Blackrobe's published missile trajectory rollout `9a80607fe` deliberately changes
projectile turn/launch fields. The older converter fingerprints still correctly
reject live replay. Their test-only historical view reverses only exact recorded
scalar changes after asserting current values; the original rollout evidence has
a pinned canonical SHA256. It does not suppress a different projectile change.

Published lane batches superseded fifteen named profiles. The new fixture stores
complete ordered resolved current payloads at source `584a5e4cb` and immutable
historical payloads, with the before commit on each record:

| Historical checkpoint | Weapons |
|---|---|
| Parent of `5be0ad305` | AtreusMG, EpigraphMG, GoliathMG, GoliathMk2MG, HMG_Duelist_upgrade, autogun_tank, TSRPGTowerRail, BCLaser, BCYamatoCannon, HMGo_upgrade, BlackHandLaser |
| Parent of `334cff6ef` | GhostSniperLockdown, SpecterSniperLockdown, HMGstealth_upgrade |
| Parent of `e779558f5` | TSBombSonic |

The adapter asserts the entire modern ordered tree before returning the old tree.
Unknown weapons pass through unchanged. Negative tests mutate damage and swap
warhead execution order independently for all fifteen records; each must reject.
The trajectory guard also rejects an unexpected turn rate. Historical converter
source files remain unchanged and live invocation remains fail-closed.

The old merge-repair report describes an immutable whole-roster checkpoint, not
today's roster. Its test now recomputes the original snapshot from Git commit
`5bb76c22d7bc3315999a5accdbf6cfdf57321776`, using manifest order and the resolver's
merge rules. It still requires original head digest
`55530c7b8b06bc79f9ad5544dca1ea6c224e07e41d6d181a4ce5535eed2d5f28` and the original
complete report hash. Missing historical blobs fail closed. This is not a copied
constant replacing snapshot verification.

## Focused evidence

Source baseline: 76 tests, six failures and eight errors across ten historical
modules. Implementation checks were grouped, with affected reruns after fixes:
trajectory group 33 tests (32 passed; later Lockdown failure fixed), lane group
49 tests (48 passed; exact expected live refusal text then corrected), and final
15-test authorized/negative-guard group passed. Those affected passing results
cover all fourteen original identities and eighty distinct tests including four
new guards. They are not represented as one all-pass full-suite execution.

External validation logs: `gameplay-reopened-historical-baseline.log`,
`gameplay-reopened-trajectories.log`, `gameplay-reopened-lane-adapters.log`,
`gameplay-reopened-final-guards.log`. The integration owner runs all consumers of
the changed history helper together once, retaining ownership-name adapters.
Real paid-upgrade regression tests are excluded from this historical repair claim.
