# Elite weapon gating audit (E2)

Armament@*ELITE* blocks without RequiresCondition: rank-elite: **21**

| File | Line | Actor | Trait | Issue |
|---|---|---|---|---|
| ContentPacks/RedAlert2/Allies/yaml/defenses.yaml | 313 | ra2_allies_patriotmissilesystem | Armament@missileeliteThunderbolt | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/aircraft.yaml | 202 | td_nod_venom | Armament@Elite | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/buildings.yaml | 484 | td_nod_laserturret | Armament@Elite | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/buildings.yaml | 590 | td_nod_obeliskoflight | Armament@Elite | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/vehicles.yaml | 757 | td_nod_buggymkii | Armament@LaserElite | RequiresCondition but NOT rank-elite |
| ContentPacks/TiberianDawn/Nod/yaml/vehicles.yaml | 778 | td_nod_buggymkii | Armament@LaserAAElite | RequiresCondition but NOT rank-elite |
| rules/generals.yaml | 3950 | glmaura | Armament@NormalElite | RequiresCondition but NOT rank-elite |
| rules/generals.yaml | 3957 | glmaura | Armament@ToxinElite | RequiresCondition but NOT rank-elite |
| rules/generals.yaml | 3964 | glmaura | Armament@ToxinBetaElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9412 | glsmaura | Armament@NormalElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9419 | glsmaura | Armament@ToxinElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9426 | glsmaura | Armament@ToxinBetaElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9433 | glsmaura | Armament@NormalElite2 | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9440 | glsmaura | Armament@ToxinElite2 | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 9447 | glsmaura | Armament@ToxinBetaElite2 | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 10573 | sgldemomaura | Armament@NormalElite | no RequiresCondition |
| rules/shockwave.yaml | 10575 | sgldemomaura | Armament@ToxinElite | no RequiresCondition |
| rules/shockwave.yaml | 10577 | sgldemomaura | Armament@ToxinBetaElite | no RequiresCondition |
| rules/shockwave.yaml | 12090 | eglpickuptank | Armament@NormalElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 12097 | eglpickuptank | Armament@ToxinElite | RequiresCondition but NOT rank-elite |
| rules/shockwave.yaml | 12104 | eglpickuptank | Armament@ToxinBetaElite | RequiresCondition but NOT rank-elite |
