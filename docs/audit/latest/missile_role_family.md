# audit_missile_role_family - the family must match the role

| code | check | count | ratchet |  |
|---|---|---|---|---|
| R1 | ground-only weapon not flying MissileHE | 11 | 51 | PASS |
| R2 | air-only weapon not flying MissileAA | 6 | 33 | PASS |
| R3 | dual-role weapon not flying MissileAP | 7 | 47 | PASS |
| R4 | MissileHE reachable against Air (hard rule) | 8 | 50 | PASS |


363 concrete weapon(s) fly a Missile* main; 267 already match their role.


## custom selectors - domain verdict withheld

| weapon | valid tags | invalid tags |
|---|---|---|
| AsianSmallTorpedo | Water, Underwater, Bridge |  |
| CycloneRocketsLockOn | lockon |  |
| Fremen_RPG | Air, Vehicle, Structure | Infantry |
| FutureMicrotorpedos | Water, Underwater, Bridge |  |
| MammothTusk | Ground, Water, Infantry, Monster, Air |  |
| MammothTuskTesla | Ground, Water, Infantry, Monster, Air | wall |
| MammothTuskTeslaInfantryFragment1 | Ground, Water, Infantry, Monster, Air | wall |
| MammothTuskTeslaInfantryFragment1_ExplicitDamage21of20 | Ground, Water, Infantry, Monster, Air | wall |
| MammothTuskTeslaInfantryFragment2 | Ground, Water, Infantry, Monster, Air | wall |
| NaxShoeRocket | Ground, Water, Ship, Submarine |  |
| NaxTorpTube | Water, Underwater, Bridge |  |
| RA2AkulaRockets | Ground, Water, Ship, Submarine |  |
| RA2FreedomRocket | Ground, Water, Air, Garrisoned |  |
| RA2FreedomRocket_elite | Ground, Water, Air, Garrisoned |  |
| RA2TorpTube | Water, Underwater, Bridge |  |
| RA2TorpTube_elite | Water, Underwater, Bridge |  |
| TSTorpTube | Water, Underwater, Bridge |  |
| TSTorpTube_elite | Water, Underwater, Bridge |  |
| YRBoomerTorpedo | Water, Underwater, Bridge |  |
| ra1_soviets_mammothtank_mammothtusk | Ground, Water, Infantry, Monster, Air |  |
| ra1_soviets_mammothtank_mammothtusktesla | Ground, Water, Infantry, Monster, Air | wall |
| ra1_soviets_monstertank_missile_tesla | Ground, Water, Infantry, Monster, Air | wall |
| ra1_soviets_siegemammothtank_mammothtusk2 | Ground, Water, Infantry, Monster, Air | wall |
| ra1_soviets_submarine_torpedo_thermobaric | Water, Underwater, Bridge |  |
| td_nod_attacksubmarine_nodtorptube | Water, Underwater, Bridge |  |
| td_nod_attacksubmarine_nodtorptubeblackmarket | Water, Underwater, Bridge |  |

These selectors need recipient-type evidence; they are not certified conforming.


## payload blends - counted, never failed

| family | weapons |
|---|---|
| MissileChem | 16 |
| MissileCryo | 4 |
| MissileFire | 7 |
| MissileQuantum | 4 |
| MissileSonic | 2 |
| MissileTesla | 13 |
| MissileThermobaric | 1 |


The ruling covers the three ROLE families only. A blend carries a
payload identity (chem, cryo, nuke) that outranks the role tag.


## Supplemental exact owner-wrapper equivalence — not the raw gate

Groups only enumerated one-parent wrappers whose current ordered payload equals the retained parent. Every concrete finding remains in the raw counts and exit gate above; equivalent payload does not make its role correct.

| code | raw findings | exact-equivalence groups |
|---|---|---|
| R1 | 11 | 11 |
| R2 | 6 | 6 |
| R3 | 7 | 7 |
| R4 | 8 | 8 |

