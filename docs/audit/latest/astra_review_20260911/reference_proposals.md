# Reference anchor proposal review

**UNAPPROVED diagnostic only.** The JSON proposal values and existing R4 contributors are carried through unchanged; this report adds review evidence and writes no registry or gameplay values.

## Caveats

- UNAPPROVED cross-metric DPS comparison: R4 armament_profile sums positive damage warheads over baseline armaments with burst/cycle; current fitting uses the main-channel reducer. Values and ratios are diagnostic only and are not directly comparable.
- Current-vs-frozen R4 differences may reflect an already-authorized firepower bake; they are not regression proof.
- The mismatch tolerance is relative 1e-6 with absolute 1e-9 and only suppresses floating-point noise.
- Equal DPS does not prove full combat equivalence: armor, range, accuracy, splash, burst timing, states and target access still matter.

## Class summary

| class | contributors | thin | HP0 | speed0 | range0 | DPS0 | C0 | max abs cost residual | explicit/template disagreements | warning counts |
|---|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---|
| `artillery` | 3 | no | 30,000 | 58 | 11,840 | 768.059 | 1,000 | 26.8% | 0 | R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE=1 |
| `fire_support` | 1 | yes | 41,000 | 83 | 10,480 | 582.930 | 1,400 | 2.1% | 0 | THIN_COHORT=1 |
| `grenadier` | 2 | yes | 14,000 | 73 | 5,000 | 420.251 | 200 | 5.2% | 0 | THIN_COHORT=1 |
| `heavy_infantry` | 1 | yes | 31,000 | 48 | 5,970 | 357.900 | 800 | 3.3% | 0 | R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE=1, THIN_COHORT=1 |
| `high_tech_tank` | 2 | yes | 291,000 | 46 | 5,450 | 742.628 | 3,800 | 10.6% | 0 | R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE=1, THIN_COHORT=1 |
| `light_tank` | 2 | yes | 93,000 | 100 | 4,820 | 406.611 | 1,000 | 13.2% | 0 | CURRENT_R4_DIFFERS_FROM_FROZEN_R4_MAY_REFLECT_AUTHORIZED_FP_BAKE=1, R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE=1, THIN_COHORT=1 |
| `line_breaker` | 1 | yes | 119,000 | 83 | 2,560 | 1,187.085 | 900 | 2.2% | 0 | THIN_COHORT=1 |
| `mbt` | 3 | no | 151,000 | 74 | 5,180 | 412.432 | 1,300 | 19.5% | 0 | none |
| `melee` | 2 | yes | 42,000 | 62 | 2,690 | 710.508 | 400 | 16.6% | 0 | THIN_COHORT=1 |
| `missile_vehicle` | 3 | no | 43,000 | 131 | 6,110 | 686.352 | 1,300 | 62.8% | 0 | R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE=1 |
| `rocket_trooper` | 4 | no | 14,000 | 48 | 7,000 | 271.815 | 400 | 16.0% | 0 | none |
| `scout` | 4 | no | 22,000 | 57 | 4,450 | 220.791 | 100 | 19.8% | 0 | CURRENT_R4_DIFFERS_FROM_FROZEN_R4_MAY_REFLECT_AUTHORIZED_FP_BAKE=4 |
| `scout_vehicle` | 3 | no | 40,000 | 157 | 4,290 | 615.443 | 500 | 31.9% | 0 | none |

## Contributors

| class | actor | frozen R4 DPS | current R4 DPS | current fitting DPS | projected DPS | current/frozen | fitting/current R4 | warnings |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `artillery` | `ra1_allies_alliedartillery` | 375.188 | 375.188 | 375.000 | 768.059 | 1.000x | 1.000x | R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE |
| `artillery` | `ra1_soviets_v2rocketlauncher` | 1,000.000 | 1,000.000 | 1,000.000 | 861.550 | 1.000x | 1.000x | none |
| `artillery` | `td_nod_artillery` | 285.714 | 285.714 | 285.714 | 681.461 | 1.000x | 1.000x | none |
| `fire_support` | `td_nod_ssmlauncher` | 400.000 | 400.000 | 400.000 | 582.930 | 1.000x | 1.000x | none |
| `grenadier` | `ra1_soviets_grenadier` | 400.000 | 400.000 | 400.000 | 356.135 | 1.000x | 1.000x | none |
| `grenadier` | `td_gdi_grenadier` | 380.952 | 380.952 | 380.952 | 484.367 | 1.000x | 1.000x | none |
| `heavy_infantry` | `ra1_soviets_shocktrooper` | 750.000 | 750.000 | 500.000 | 357.900 | 1.000x | 0.667x | R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE |
| `high_tech_tank` | `ra1_soviets_mammothtank` | 932.272 | 932.272 | 932.039 | 790.640 | 1.000x | 1.000x | R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE |
| `high_tech_tank` | `td_gdi_mammothtank` | 400.000 | 400.000 | 400.000 | 694.616 | 1.000x | 1.000x | none |
| `light_tank` | `ra1_allies_alliedlighttank` | 324.459 | 162.297 | 162.162 | 471.324 | 0.500x | 0.999x | CURRENT_R4_DIFFERS_FROM_FROZEN_R4_MAY_REFLECT_AUTHORIZED_FP_BAKE<br>R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE |
| `light_tank` | `td_nod_lighttank` | 133.333 | 133.333 | 133.333 | 341.899 | 1.000x | 1.000x | none |
| `line_breaker` | `td_nod_flametank` | 466.667 | 466.667 | 466.667 | 1,187.085 | 1.000x | 1.000x | none |
| `mbt` | `ra1_allies_alliedmediumtank` | 170.213 | 170.213 | 170.213 | 323.615 | 1.000x | 1.000x | none |
| `mbt` | `ra1_soviets_heavytank` | 246.914 | 246.914 | 246.914 | 491.485 | 1.000x | 1.000x | none |
| `mbt` | `td_gdi_battletank` | 222.222 | 222.222 | 222.222 | 412.432 | 1.000x | 1.000x | none |
| `melee` | `td_nod_chemicalwarrior` | 1,000.000 | 1,000.000 | 1,000.000 | 939.107 | 1.000x | 1.000x | none |
| `melee` | `td_nod_flamethrower` | 333.333 | 333.333 | 333.333 | 481.908 | 1.000x | 1.000x | none |
| `missile_vehicle` | `td_gdi_mlrs` | 352.941 | 352.941 | 352.941 | 686.352 | 1.000x | 1.000x | none |
| `missile_vehicle` | `td_nod_reconbike` | 492.554 | 492.554 | 492.308 | 516.740 | 1.000x | 1.000x | R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE |
| `missile_vehicle` | `td_nod_stealthtank` | 363.636 | 363.636 | 363.636 | 711.410 | 1.000x | 1.000x | none |
| `rocket_trooper` | `ra1_soviets_rocketsoldier` | 400.000 | 400.000 | 400.000 | 258.613 | 1.000x | 1.000x | none |
| `rocket_trooper` | `ra1_allies_alliedrocketsoldier` | 400.000 | 400.000 | 400.000 | 258.613 | 1.000x | 1.000x | none |
| `rocket_trooper` | `td_gdi_rocketsoldier` | 285.714 | 285.714 | 285.714 | 285.018 | 1.000x | 1.000x | none |
| `rocket_trooper` | `td_nod_rocketsoldier` | 285.714 | 285.714 | 285.714 | 285.018 | 1.000x | 1.000x | none |
| `scout` | `ra1_soviets_rifleinfantry` | 100.000 | 42.000 | 42.000 | 188.688 | 0.420x | 1.000x | CURRENT_R4_DIFFERS_FROM_FROZEN_R4_MAY_REFLECT_AUTHORIZED_FP_BAKE |
| `scout` | `ra1_allies_rifleinfantry` | 103.448 | 48.621 | 48.621 | 190.294 | 0.470x | 1.000x | CURRENT_R4_DIFFERS_FROM_FROZEN_R4_MAY_REFLECT_AUTHORIZED_FP_BAKE |
| `scout` | `td_gdi_minigunner` | 135.593 | 32.542 | 32.542 | 251.288 | 0.240x | 1.000x | CURRENT_R4_DIFFERS_FROM_FROZEN_R4_MAY_REFLECT_AUTHORIZED_FP_BAKE |
| `scout` | `td_nod_minigunner` | 142.857 | 41.429 | 41.429 | 254.588 | 0.290x | 1.000x | CURRENT_R4_DIFFERS_FROM_FROZEN_R4_MAY_REFLECT_AUTHORIZED_FP_BAKE |
| `scout_vehicle` | `ra1_allies_ranger` | 640.000 | 640.000 | 640.000 | 526.888 | 1.000x | 1.000x | none |
| `scout_vehicle` | `td_gdi_humvee` | 857.143 | 857.143 | 857.143 | 707.501 | 1.000x | 1.000x | none |
| `scout_vehicle` | `td_nod_buggy` | 600.000 | 600.000 | 600.000 | 615.443 | 1.000x | 1.000x | none |

## Per-unit proposal routing

| class | actor | HP current→target | speed current→target | range current→target | nominal DPS current→target | cost current→reference | candidate formula price | disposition |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `artillery` | `ra1_allies_alliedartillery` | 20,000→29,950 | 60→58 | 13,350→11,842 | 375.188→768.059 | 600→982 | 1,240 | HOLD_CLASS_DPS_METRIC_BASIS |
| `artillery` | `ra1_soviets_v2rocketlauncher` | 30,000→44,857 | 85→67 | 14,110→12,626 | 1,000.000→861.550 | 1,600→1,504 | 1,410 | HOLD_CLASS_DPS_METRIC_BASIS |
| `artillery` | `td_nod_artillery` | 17,500→28,671 | 55→54 | 12,345→11,320 | 285.714→681.461 | 400→819 | 850 | HOLD_CLASS_DPS_METRIC_BASIS |
| `fire_support` | `td_nod_ssmlauncher` | 20,000→40,827 | 100→83 | 8,940→10,477 | 400.000→582.930 | 800→1,270 | 1,240 | HOLD_THIN_CLASS_COHORT |
| `grenadier` | `ra1_soviets_grenadier` | 8,000→13,786 | 75→72 | 5,791→5,011 | 400.000→356.135 | 200→237 | 220 | HOLD_THIN_CLASS_COHORT |
| `grenadier` | `td_gdi_grenadier` | 8,000→15,027 | 75→73 | 6,097→4,983 | 380.952→484.367 | 200→236 | 230 | HOLD_THIN_CLASS_COHORT |
| `heavy_infantry` | `ra1_soviets_shocktrooper` | 40,000→30,549 | 40→48 | 4,652→5,973 | 750.000→357.900 | 600→704 | 680 | HOLD_CLASS_DPS_METRIC_BASIS |
| `high_tech_tank` | `ra1_soviets_mammothtank` | 375,000→301,654 | 50→44 | 6,412→5,566 | 932.272→790.640 | 2,000→2,733 | 2,450 | HOLD_CLASS_DPS_METRIC_BASIS |
| `high_tech_tank` | `td_gdi_mammothtank` | 225,000→280,061 | 60→49 | 6,141→5,341 | 400.000→694.616 | 1,600→2,481 | 2,740 | HOLD_CLASS_DPS_METRIC_BASIS |
| `light_tank` | `ra1_allies_alliedlighttank` | 50,000→75,294 | 120→111 | 4,720→4,922 | 162.297→471.324 | 500→923 | 1,050 | HOLD_CLASS_DPS_METRIC_BASIS |
| `light_tank` | `td_nod_lighttank` | 80,000→110,354 | 110→89 | 4,993→4,721 | 133.333→341.899 | 600→982 | 930 | HOLD_CLASS_DPS_METRIC_BASIS |
| `line_breaker` | `td_nod_flametank` | 100,000→119,259 | 80→83 | 2,390→2,563 | 466.667→1,187.085 | 800→1,104 | 1,130 | HOLD_THIN_CLASS_COHORT |
| `mbt` | `ra1_allies_alliedmediumtank` | 90,000→127,417 | 100→81 | 5,159→5,143 | 170.213→323.615 | 700→1,134 | 1,360 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `mbt` | `ra1_soviets_heavytank` | 150,000→171,660 | 70→66 | 5,469→5,219 | 246.914→491.485 | 1,000→1,561 | 1,540 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `mbt` | `td_gdi_battletank` | 125,000→151,133 | 80→74 | 5,438→5,181 | 222.222→412.432 | 900→1,305 | 1,300 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `melee` | `td_nod_chemicalwarrior` | 48,000→56,189 | 48→58 | 3,414→2,851 | 1,000.000→939.107 | 500→604 | 500 | HOLD_THIN_CLASS_COHORT |
| `melee` | `td_nod_flamethrower` | 20,000→28,559 | 60→65 | 2,085→2,521 | 333.333→481.908 | 200→284 | 330 | HOLD_THIN_CLASS_COHORT |
| `missile_vehicle` | `td_gdi_mlrs` | 25,000→43,882 | 80→74 | 9,920→10,022 | 352.941→686.352 | 1,000→1,396 | 1,350 | HOLD_CLASS_DPS_METRIC_BASIS |
| `missile_vehicle` | `td_nod_reconbike` | 17,500→34,990 | 200→184 | 6,000→5,404 | 492.554→516.740 | 500→736 | 1,140 | HOLD_CLASS_DPS_METRIC_BASIS |
| `missile_vehicle` | `td_nod_stealthtank` | 25,000→43,311 | 150→131 | 7,432→6,110 | 363.636→711.410 | 900→1,394 | 520 | HOLD_CLASS_DPS_METRIC_BASIS |
| `rocket_trooper` | `ra1_soviets_rocketsoldier` | 10,000→13,854 | 55→50 | 6,643→7,253 | 400.000→258.613 | 300→436 | 410 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `rocket_trooper` | `ra1_allies_alliedrocketsoldier` | 10,000→13,854 | 55→50 | 6,643→7,253 | 400.000→258.613 | 300→436 | 510 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `rocket_trooper` | `td_gdi_rocketsoldier` | 9,000→14,581 | 50→45 | 6,368→6,743 | 285.714→285.018 | 300→433 | 400 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `rocket_trooper` | `td_nod_rocketsoldier` | 9,000→14,581 | 50→45 | 6,368→6,743 | 285.714→285.018 | 300→433 | 400 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `scout` | `ra1_soviets_rifleinfantry` | 34,000→21,064 | 54→55 | 4,668→4,547 | 42.000→188.688 | 100→138 | 110 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `scout` | `ra1_allies_rifleinfantry` | 27,000→19,884 | 55→56 | 5,500→4,737 | 48.621→190.294 | 100→138 | 110 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `scout` | `td_gdi_minigunner` | 31,000→22,377 | 63→58 | 5,499→4,353 | 32.542→251.288 | 100→132 | 110 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `scout` | `td_nod_minigunner` | 30,000→22,194 | 66→59 | 4,609→4,165 | 41.429→254.588 | 100→132 | 130 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `scout_vehicle` | `ra1_allies_ranger` | 22,500→39,554 | 175→157 | 4,359→4,278 | 640.000→526.888 | 300→562 | 510 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `scout_vehicle` | `td_gdi_humvee` | 27,500→45,467 | 150→144 | 4,792→4,349 | 857.143→707.501 | 400→584 | 560 | REVIEWABLE_NO_AUTOMATIC_WRITE |
| `scout_vehicle` | `td_nod_buggy` | 20,000→35,651 | 200→161 | 4,540→4,290 | 600.000→615.443 | 300→450 | 590 | HOLD_CLASS_FIT_RESIDUAL |

All class candidates remain **UNAPPROVED**. Review warnings before any calibration or anchor decision.
