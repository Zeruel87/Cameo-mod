# gen_rename_maps — §9.1 naming compliance (RA1-Soviet baseline)


## Actor-id compliance per faction (faction-exclusive buildables)

| faction | compliant | % | proposal collisions | asset files to rename | unrepairable stems |
|---|---|---|---|---|---|
| asianalliance | 73/73 | 100% | 0 | 0 | 0 |
| atreides | 34/34 | 100% | 0 | 0 | 0 |
| cabal | 80/80 | 100% | 0 | 0 | 0 |
| corrino | 31/31 | 100% | 0 | 0 | 0 |
| eden | 43/43 | 100% | 0 | 0 | 0 |
| forgotten | 78/78 | 100% | 0 | 1 | 0 |
| futuretech | 56/56 | 100% | 0 | 0 | 0 |
| harkonnen | 48/50 | 96% | 0 | 0 | 0 |
| ixian | 64/65 | 98% | 0 | 0 | 0 |
| japan | 68/68 | 100% | 0 | 0 | 0 |
| latinsyndicate | 65/65 | 100% | 0 | 0 | 0 |
| naxis | 73/73 | 100% | 0 | 0 | 0 |
| ordos | 73/73 | 100% | 0 | 0 | 0 |
| plymouth | 44/44 | 100% | 0 | 0 | 0 |
| protoss | 72/72 | 100% | 0 | 0 | 0 |
| ra1_allies | 62/62 | 100% | 0 | 0 | 0 |
| ra1_soviets | 106/106 | 100% | 0 | 0 | 0 |
| ra2_allies | 66/66 | 100% | 0 | 0 | 0 |
| ra2_soviets | 56/56 | 100% | 0 | 1 | 0 |
| schwarzermond | 59/59 | 100% | 0 | 0 | 0 |
| scrin | 49/49 | 100% | 0 | 0 | 0 |
| steelconsortium | 60/60 | 100% | 0 | 0 | 0 |
| td_gdi | 60/60 | 100% | 0 | 0 | 0 |
| td_nod | 66/66 | 100% | 0 | 0 | 0 |
| terran | 77/77 | 100% | 0 | 0 | 0 |
| tkm | 72/72 | 100% | 0 | 0 | 0 |
| ts_gdi | 65/65 | 100% | 0 | 0 | 0 |
| ts_nod | 46/46 | 100% | 0 | 0 | 0 |
| wc2_humans | 73/73 | 100% | 0 | 0 | 0 |
| wc2_orcs | 64/64 | 100% | 0 | 0 | 0 |
| yuri | 64/64 | 100% | 0 | 0 | 0 |
| zerg | 75/75 | 100% | 0 | 0 | 0 |


## Icon filename compliance (_icon suffix rule)

| faction | icons compliant | % |
|---|---|---|
| asianalliance | 1/1 | 100% |
| atreides | 0/0 | — |
| cabal | 2/2 | 100% |
| corrino | 0/0 | — |
| eden | 0/0 | — |
| forgotten | 58/58 | 100% |
| futuretech | 1/1 | 100% |
| harkonnen | 0/0 | — |
| ixian | 0/0 | — |
| japan | 0/0 | — |
| latinsyndicate | 3/3 | 100% |
| naxis | 1/1 | 100% |
| ordos | 0/0 | — |
| plymouth | 0/0 | — |
| protoss | 53/53 | 100% |
| ra1_allies | 0/0 | — |
| ra1_soviets | 0/0 | — |
| ra2_allies | 8/8 | 100% |
| ra2_soviets | 6/7 | 85% |
| schwarzermond | 0/0 | — |
| scrin | 0/0 | — |
| steelconsortium | 1/1 | 100% |
| td_gdi | 38/38 | 100% |
| td_nod | 42/42 | 100% |
| terran | 55/55 | 100% |
| tkm | 2/2 | 100% |
| ts_gdi | 46/46 | 100% |
| ts_nod | 36/36 | 100% |
| wc2_humans | 0/0 | — |
| wc2_orcs | 0/0 | — |
| yuri | 4/4 | 100% |
| zerg | 51/51 | 100% |


_Ownership is data-driven: an actor counts for a faction only if no other faction's prerequisite closure can build it. Sequence filenames referenced by more than 3 images are treated as shared archives and exempted. Rename proposals written to tools/rename/rename_map_<faction>.yaml (actors: + files: sections); collisions need manual `_variant` suffixes before applying._

