# audit_naming_damage - what a botched rename left behind

| code | pathology | count | ratchet |  |
|---|---|---|---|---|
| N1 | DOUBLED_ID (file carries one actor id twice) | 2 | 25 | PASS |
| N2 | CROSS_FACTION (file carries two factions' ids) | 16 | 16 | PASS |
| N3 | FLUENT_LEAK (a fluent key became an id) | 0 | 5 | PASS |
| N4 | REDUNDANT_WORD (faction named twice) | 97 | 345 | PASS |
| N5 | DOTTED_FACTION (dot carries a faction, not a variant) | 3 | 109 | PASS |
| N6 | HYPHEN (DESIGN rule 9) | 0 | 1 | PASS |


## Per-faction breakdown

| faction | N1 | N2 | N3 | N4 | N5 | N6 |
|---|---|---|---|---|---|---|
| japan | 0 | 0 | 0 | 49 | 0 | 0 |
| latinsyndicate | 0 | 0 | 0 | 19 | 2 | 0 |
| ra1_allies | 0 | 16 | 0 | 0 | 0 | 0 |
| steelconsortium | 0 | 0 | 0 | 8 | 1 | 0 |
| wc2_humans | 1 | 0 | 0 | 5 | 0 | 0 |
| wc2_orcs | 1 | 0 | 0 | 5 | 0 | 0 |
| zerg | 0 | 0 | 0 | 6 | 0 | 0 |
| yuri | 0 | 0 | 0 | 4 | 0 | 0 |
| futuretech | 0 | 0 | 0 | 1 | 0 | 0 |


**0 of 6 ratchets exceeded.**
