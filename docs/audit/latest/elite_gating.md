# Elite weapon gating audit (E2)

Armament@*ELITE* blocks without RequiresCondition: rank-elite: **21**

| File | Line | Actor | Trait | Issue |
|---|---|---|---|---|
| ContentPacks/RedAlert2/Allies/yaml/defenses.yaml | 313 | ra2_allies_patriotmissilesystem | Armament@missileeliteThunderbolt | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/aircraft.yaml | 202 | td_nod_venom | Armament@Elite | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/buildings.yaml | 484 | td_nod_laserturret | Armament@Elite | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/buildings.yaml | 590 | td_nod_obeliskoflight | Armament@Elite | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/vehicles.yaml | 785 | td_nod_buggymkii | Armament@LaserElite | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/vehicles.yaml | 806 | td_nod_buggymkii | Armament@LaserAAElite | RequiresCondition but NOT rank-elite |
| rules/generals.yaml | 3949 | glmaura | Armament@NormalElite | RequiresCondition but NOT rank-elite |
| rules/generals.yaml | 3956 | glmaura | Armament@ToxinElite | RequiresCondition but NOT rank-elite |
| rules/generals.yaml | 3963 | glmaura | Armament@ToxinBetaElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9356 | glsmaura | Armament@NormalElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9363 | glsmaura | Armament@ToxinElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9370 | glsmaura | Armament@ToxinBetaElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9377 | glsmaura | Armament@NormalElite2 | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9384 | glsmaura | Armament@ToxinElite2 | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9391 | glsmaura | Armament@ToxinBetaElite2 | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 10517 | sgldemomaura | Armament@NormalElite | no RequiresCondition |
| rules/shockwave.yaml | 10519 | sgldemomaura | Armament@ToxinElite | no RequiresCondition |
| rules/shockwave.yaml | 10521 | sgldemomaura | Armament@ToxinBetaElite | no RequiresCondition |
| rules/shockwave.yaml | 12034 | eglpickuptank | Armament@NormalElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 12041 | eglpickuptank | Armament@ToxinElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 12048 | eglpickuptank | Armament@ToxinBetaElite | RequiresCondition but NOT rank-elite |
