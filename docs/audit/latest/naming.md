# gen_rename_maps — §9.1 naming compliance (RA1-Soviet baseline)


## Actor-id compliance per faction (faction-exclusive buildables)

| faction | compliant | % | proposal collisions | asset files to rename | unrepairable stems |
|---|---|---|---|---|---|
| asianalliance | 73/73 | 100% | 0 | 1 | 6 |
| atreides | 21/23 | 91% | 0 | 4 | 10 |
| cabal | 80/80 | 100% | 0 | 0 | 0 |
| corrino | 22/25 | 88% | 0 | 5 | 1 |
| eden | 43/43 | 100% | 0 | 0 | 0 |
| forgotten | 78/78 | 100% | 0 | 1 | 0 |
| futuretech | 56/56 | 100% | 0 | 1 | 0 |
| harkonnen | 27/35 | 77% | 0 | 1 | 1 |
| ixian | 60/65 | 92% | 0 | 2 | 0 |
| japan | 68/68 | 100% | 0 | 1 | 0 |
| latinsyndicate | 65/65 | 100% | 0 | 0 | 0 |
| naxis | 73/73 | 100% | 0 | 4 | 2 |
| ordos | 72/72 | 100% | 0 | 3 | 6 |
| plymouth | 44/44 | 100% | 0 | 0 | 0 |
| protoss | 72/72 | 100% | 0 | 0 | 0 |
| ra1_allies | 62/62 | 100% | 0 | 0 | 0 |
| ra1_soviets | 106/106 | 100% | 0 | 3 | 14 |
| ra2_allies | 66/66 | 100% | 0 | 0 | 0 |
| ra2_soviets | 56/56 | 100% | 0 | 1 | 0 |
| schwarzermond | 59/59 | 100% | 0 | 0 | 0 |
| steelconsortium | 60/60 | 100% | 0 | 6 | 0 |
| td_gdi | 60/60 | 100% | 0 | 0 | 0 |
| td_nod | 65/65 | 100% | 0 | 0 | 0 |
| terran | 77/77 | 100% | 0 | 0 | 0 |
| tkm | 72/72 | 100% | 0 | 1 | 0 |
| ts_gdi | 65/65 | 100% | 0 | 9 | 0 |
| ts_nod | 46/46 | 100% | 0 | 0 | 0 |
| wc2_humans | 73/73 | 100% | 0 | 0 | 0 |
| wc2_orcs | 64/64 | 100% | 0 | 0 | 0 |
| yuri | 64/64 | 100% | 0 | 1 | 0 |
| zerg | 75/75 | 100% | 0 | 0 | 0 |


## Icon filename compliance (_icon suffix rule)

| faction | icons compliant | % |
|---|---|---|
| asianalliance | 56/57 | 98% |
| atreides | 6/7 | 85% |
| cabal | 2/2 | 100% |
| corrino | 1/1 | 100% |
| eden | 41/41 | 100% |
| forgotten | 58/58 | 100% |
| futuretech | 43/43 | 100% |
| harkonnen | 8/8 | 100% |
| ixian | 32/32 | 100% |
| japan | 43/44 | 97% |
| latinsyndicate | 45/45 | 100% |
| naxis | 56/56 | 100% |
| ordos | 36/36 | 100% |
| plymouth | 44/44 | 100% |
| protoss | 53/53 | 100% |
| ra1_allies | 42/42 | 100% |
| ra1_soviets | 84/84 | 100% |
| ra2_allies | 51/51 | 100% |
| ra2_soviets | 48/49 | 97% |
| schwarzermond | 47/47 | 100% |
| steelconsortium | 44/45 | 97% |
| td_gdi | 38/38 | 100% |
| td_nod | 41/41 | 100% |
| terran | 55/55 | 100% |
| tkm | 53/53 | 100% |
| ts_gdi | 44/46 | 95% |
| ts_nod | 36/36 | 100% |
| wc2_humans | 12/12 | 100% |
| wc2_orcs | 5/5 | 100% |
| yuri | 60/61 | 98% |
| zerg | 51/51 | 100% |


_Ownership is data-driven: an actor counts for a faction only if no other faction's prerequisite closure can build it. Sequence filenames referenced by more than 3 images are treated as shared archives and exempted. Rename proposals written to tools/rename/rename_map_<faction>.yaml (actors: + files: sections); collisions need manual `_variant` suffixes before applying._

