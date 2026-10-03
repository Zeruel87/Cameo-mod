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

All class candidates remain **UNAPPROVED**. Review warnings before any calibration or anchor decision.
