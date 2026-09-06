# gen_rename_maps — §9.1 naming compliance (RA1-Soviet baseline)


## Actor-id compliance per faction (faction-exclusive buildables)

| faction | compliant | % | proposal collisions | asset files to rename |
|---|---|---|---|---|
| asianalliance | 73/73 | 100% | 0 | 116 |
| atreides | 21/23 | 91% | 0 | 12 |
| cabal | 80/80 | 100% | 0 | 147 |
| corrino | 22/25 | 88% | 0 | 9 |
| eden | 43/43 | 100% | 0 | 2 |
| forgotten | 78/78 | 100% | 0 | 49 |
| futuretech | 56/56 | 100% | 0 | 36 |
| harkonnen | 27/35 | 77% | 0 | 7 |
| ixian | 59/60 | 98% | 0 | 28 |
| japan | 68/68 | 100% | 0 | 40 |
| latinsyndicate | 65/65 | 100% | 0 | 44 |
| naxis | 73/73 | 100% | 0 | 35 |
| ordos | 71/71 | 100% | 0 | 36 |
| plymouth | 44/44 | 100% | 0 | 2 |
| protoss | 72/72 | 100% | 0 | 46 |
| ra1_allies | 0/62 | 0% | 0 | 123 |
| ra1_soviets | 0/106 | 0% | 0 | 181 |
| ra2_allies | 0/66 | 0% | 0 | 233 |
| ra2_soviets | 0/56 | 0% | 0 | 141 |
| schwarzermond | 59/59 | 100% | 0 | 24 |
| steelconsortium | 60/60 | 100% | 0 | 33 |
| td_gdi | 0/60 | 0% | 0 | 106 |
| td_nod | 0/65 | 0% | 0 | 116 |
| terran | 77/77 | 100% | 0 | 58 |
| tkm | 72/72 | 100% | 0 | 39 |
| ts_gdi | 0/65 | 0% | 0 | 153 |
| ts_nod | 0/46 | 0% | 0 | 127 |
| wc2_humans | 73/73 | 100% | 0 | 17 |
| wc2_orcs | 64/64 | 100% | 0 | 14 |
| yuri | 64/64 | 100% | 0 | 6 |
| zerg | 75/75 | 100% | 0 | 60 |


## Icon filename compliance (_icon suffix rule)

| faction | icons compliant | % |
|---|---|---|
| asianalliance | 71/72 | 98% |
| atreides | 6/7 | 85% |
| cabal | 80/80 | 100% |
| corrino | 1/1 | 100% |
| eden | 43/43 | 100% |
| forgotten | 76/78 | 97% |
| futuretech | 56/56 | 100% |
| harkonnen | 9/9 | 100% |
| ixian | 44/44 | 100% |
| japan | 64/67 | 95% |
| latinsyndicate | 65/65 | 100% |
| naxis | 73/73 | 100% |
| ordos | 50/50 | 100% |
| plymouth | 44/44 | 100% |
| protoss | 72/72 | 100% |
| ra1_allies | 61/61 | 100% |
| ra1_soviets | 105/105 | 100% |
| ra2_allies | 65/65 | 100% |
| ra2_soviets | 54/55 | 98% |
| schwarzermond | 59/59 | 100% |
| steelconsortium | 59/60 | 98% |
| td_gdi | 60/60 | 100% |
| td_nod | 65/65 | 100% |
| terran | 77/77 | 100% |
| tkm | 72/72 | 100% |
| ts_gdi | 63/65 | 96% |
| ts_nod | 46/46 | 100% |
| wc2_humans | 19/20 | 95% |
| wc2_orcs | 10/10 | 100% |
| yuri | 63/64 | 98% |
| zerg | 75/75 | 100% |


_Ownership is data-driven: an actor counts for a faction only if no other faction's prerequisite closure can build it. Sequence filenames referenced by more than 3 images are treated as shared archives and exempted. Rename proposals written to tools/rename/rename_map_<faction>.yaml (actors: + files: sections); collisions need manual `_variant` suffixes before applying._

