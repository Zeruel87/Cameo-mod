# audit_missile_role_family - the family must match the role

| code | check | count | ratchet |  |
|---|---|---|---|---|
| R1 | ground-only weapon not flying MissileHE | 51 | 51 | PASS |
| R2 | air-only weapon not flying MissileAA | 33 | 33 | PASS |
| R3 | dual-role weapon not flying MissileAP | 52 | 47 | FAIL |
| R4 | MissileHE reachable against Air (hard rule) | 55 | 50 | FAIL |


367 concrete weapon(s) fly a Missile* main; 191 already match their role.


## payload blends - counted, never failed

| family | weapons |
|---|---|
| MissileChem | 16 |
| MissileCryo | 6 |
| MissileFire | 7 |
| MissileNuke | 1 |
| MissileQuantum | 4 |
| MissileTesla | 10 |
| MissileThermobaric | 1 |


The ruling covers the three ROLE families only. A blend carries a
payload identity (chem, cryo, nuke) that outranks the role tag.


## Supplemental exact owner-wrapper equivalence — not the raw gate

Groups only enumerated one-parent wrappers whose current ordered payload equals the retained parent. Every concrete finding remains in the raw counts and exit gate above; equivalent payload does not make its role correct.

| code | raw findings | exact-equivalence groups |
|---|---|---|
| R1 | 51 | 51 |
| R2 | 33 | 33 |
| R3 | 52 | 47 |
| R4 | 55 | 50 |

| code | retained parent | role | family | all concrete members |
|---|---|---|---|---|
| R3 | 227mm | both | MissileHE | 227mm, ra1_soviets_missilesubmarine_227mm, td_gdi_mlrs_227mm |
| R3 | MammothTusk | both | MissileHE | MammothTusk, ra1_soviets_mammothtank_mammothtusk |
| R3 | RocketsRA | both | MissileHE | RocketsRA, ra1_allies_alliedrocketsoldier_rocketsra, ra1_soviets_rocketsoldier_rocketsra |
| R4 | 227mm | both | MissileHE | 227mm, ra1_soviets_missilesubmarine_227mm, td_gdi_mlrs_227mm |
| R4 | MammothTusk | both | MissileHE | MammothTusk, ra1_soviets_mammothtank_mammothtusk |
| R4 | RocketsRA | both | MissileHE | RocketsRA, ra1_allies_alliedrocketsoldier_rocketsra, ra1_soviets_rocketsoldier_rocketsra |


**FAIL: R3, R4 above ratchet.** Lower a baseline as the conversion progresses; never raise one.

