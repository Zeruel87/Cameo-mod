# audit_missile_role_family - the family must match the role

| code | check | count | ratchet |  |
|---|---|---|---|---|
| R1 | ground-only weapon not flying MissileHE | 51 | 51 | PASS |
| R2 | air-only weapon not flying MissileAA | 33 | 33 | PASS |
| R3 | dual-role weapon not flying MissileAP | 47 | 47 | PASS |
| R4 | MissileHE reachable against Air (hard rule) | 50 | 50 | PASS |


358 concrete weapon(s) fly a Missile* main; 190 already match their role.


## payload blends - counted, never failed

| family | weapons |
|---|---|
| MissileChem | 16 |
| MissileCryo | 6 |
| MissileFire | 5 |
| MissileNuke | 1 |
| MissileQuantum | 4 |
| MissileTesla | 9 |
| MissileThermobaric | 1 |


The ruling covers the three ROLE families only. A blend carries a
payload identity (chem, cryo, nuke) that outranks the role tag.

