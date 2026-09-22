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

## Complete candidate roster

All 163 active candidate actors are listed. Blank targets are deliberately unresolved or subject to a separate pricing rule; they are not zero prices.

| actor | type | class | current HP | current speed | current cost | proposal/disposition | reason |
|---|---|---|---:|---:|---:|---|---|
| `ra1_allies_alliedaagun` | def | — | 62,500 | — | 500 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_allies_alliedapc` | veh | support | 50,000 | 105 | 1,300 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `ra1_allies_alliedartillery` | veh | artillery | 20,000 | 60 | 600 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_allies_alliedchinooktransport` | air | — | 125,000 | 125 | 3,920 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `ra1_allies_alliedgunturret` | def | — | 100,000 | — | 800 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_allies_alliedheavyaatank` | veh | anti_air_vehicle | 125,000 | 75 | 1,250 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_allies_alliedlighttank` | veh | light_tank | 50,000 | 120 | 500 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_allies_alliedmediumtank` | veh | mbt | 90,000 | 100 | 700 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_allies_alliedmobileconstructionvehicle` | veh | support | 300,000 | 75 | 5,000 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `ra1_allies_alliedoretruck` | veh | — | 100,000 | 90 | 1,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_allies_alliedrocketsoldier` | inf | rocket_trooper | 10,000 | 55 | 300 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_allies_alliedsniper` | inf | pure_sniper | 10,000 | 60 | 500 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_allies_alliedtankdestroyer` | veh | tank_destroyer | 120,000 | 60 | 1,200 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_allies_alliedtigerheavytank` | veh | mbt | 160,000 | 75 | 1,300 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_allies_bastionartillerybunker` | def | — | 350,000 | — | 2,000 | GARRISON_DEFENSE_SEPARATE_REVIEW | A garrison defense is outside this mobile-anchor cohort; its occupancy and pricing need explicit treatment. |
| `ra1_allies_blackhawk` | air | — | 50,000 | 130 | 1,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_allies_camopillbox` | def | — | 122,500 | — | 1,300 | GARRISON_DEFENSE_SEPARATE_REVIEW | A garrison defense is outside this mobile-anchor cohort; its occupancy and pricing need explicit treatment. |
| `ra1_allies_chronotank` | veh | epic_vehicle | 75,000 | 100 | 2,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `ra1_allies_cruiser` | nav | — | 225,000 | 40 | 3,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_allies_destroyer` | nav | — | 125,000 | 85 | 1,600 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_allies_gapgenerator` | def | — | 50,000 | — | 5,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `ra1_allies_gunboat` | nav | — | 60,000 | 120 | 1,300 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_allies_longbow` | air | — | 35,000 | 150 | 2,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_allies_machinegunner` | inf | special_forces | 19,000 | 49 | 560 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_allies_mechanic` | inf | support | 7,500 | 50 | 500 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `ra1_allies_medic` | inf | support | 10,000 | 50 | 500 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `ra1_allies_minelayer` | veh | support | 30,000 | 128 | 800 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `ra1_allies_mobilegapgenerator` | veh | — | 25,000 | 75 | 5,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `ra1_allies_mobileradarjammer` | veh | — | 25,000 | 100 | 5,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `ra1_allies_phasetransport` | veh | armed_troop_transport | 30,000 | 125 | 1,960 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `ra1_allies_pillbox` | def | — | 90,000 | — | 400 | GARRISON_DEFENSE_SEPARATE_REVIEW | A garrison defense is outside this mobile-anchor cohort; its occupancy and pricing need explicit treatment. |
| `ra1_allies_ranger` | veh | scout_vehicle | 22,500 | 175 | 300 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_allies_rapierjumpjet` | air | — | 77,500 | 210 | 1,300 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_allies_raspy` | inf | support | 5,000 | 60 | 500 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `ra1_allies_reconranger` | veh | support | 25,000 | 160 | 500 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `ra1_allies_rifleinfantry` | inf | scout | 27,000 | 55 | 100 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_allies_sheridanassaulttank` | veh | light_tank | 85,000 | 85 | 600 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_allies_tanya` | inf | commando | 44,000 | 77 | 3,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `ra1_soviets_ak47conscript` | inf | scout | 44,000 | 71 | 200 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_armoredyak` | air | — | 80,000 | 135 | 1,600 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_btr80` | veh | armed_troop_transport | 90,000 | 90 | 1,620 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `ra1_soviets_commissar` | inf | pure_sniper | 30,000 | 70 | 700 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_cyberdog` | inf | melee | 50,000 | 100 | 1,000 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_dog` | inf | melee | 5,000 | 100 | 200 | PRICING_INPUT_REVIEW_REQUIRED | No compatible nominal fitting inputs |
| `ra1_soviets_dragunovantimaterialsniper` | inf | heavy_sniper | 20,000 | 40 | 420 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_firerocketsoldier` | inf | rocket_trooper | 16,000 | 48 | 400 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_flaktruck` | veh | anti_air_vehicle | 30,000 | 120 | 800 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `ra1_soviets_flamethrower` | inf | heavy_infantry | 16,000 | 56 | 200 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_flametower` | def | — | 64,000 | — | 600 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_gatlingtank` | veh | anti_air_vehicle | 75,000 | 75 | 1,100 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_gorynychtank` | veh | line_breaker | 150,000 | 70 | 1,300 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_grad` | veh | artillery_tank | 50,000 | 75 | 1,400 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_grenadier` | inf | grenadier | 8,000 | 75 | 200 | HOLD_THIN_CLASS_COHORT | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_soviets_hammertank` | veh | mbt | 210,000 | 60 | 1,500 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_heatraytank` | veh | fire_support | 60,000 | 60 | 1,900 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_heavyindustrialminer` | veh | — | 135,000 | 80 | 1,200 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_heavytank` | veh | mbt | 150,000 | 70 | 1,000 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_soviets_heavyteslatank` | veh | high_tech_tank | 150,000 | 60 | 3,500 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_hindattackhelicopter` | air | — | 100,000 | 120 | 1,800 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_hiptransport` | air | — | 150,000 | 100 | 2,500 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `ra1_soviets_kamovattackhelicopter` | air | — | 122,500 | 125 | 2,100 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_kotinnucleartank` | veh | mbt | 240,000 | 65 | 1,800 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_madtank` | veh | epic_vehicle | 300,000 | 60 | 3,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `ra1_soviets_mammothtank` | veh | high_tech_tank | 375,000 | 50 | 2,000 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_soviets_migattackbomber` | air | — | 40,000 | 200 | 1,400 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_missilesubmarine` | nav | — | 70,000 | 60 | 3,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_mobileconstructionvehicle` | veh | support | 300,000 | 75 | 5,000 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `ra1_soviets_monstertank` | veh | epic_vehicle | 1,000,000 | 45 | 10,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `ra1_soviets_mortarsoldier` | inf | mortar | 16,000 | 48 | 500 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_nuclearv2launcher` | veh | artillery | 40,000 | 80 | 2,300 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_nuclearyak` | air | — | 64,000 | 190 | 2,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_nukedemotruck` | veh | — | 20,000 | 100 | 1,500 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_oretruck` | veh | — | 100,000 | 90 | 1,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_rifleinfantry` | inf | scout | 34,000 | 54 | 100 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_soviets_rocketsoldier` | inf | rocket_trooper | 10,000 | 55 | 300 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_soviets_samsite` | def | — | 75,000 | — | 700 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_shocktrooper` | inf | heavy_infantry | 40,000 | 40 | 600 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_soviets_siegemammothtank` | veh | high_tech_tank | 625,000 | 45 | 4,000 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_stalinfist` | veh | support | 100,000 | 60 | 7,000 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `ra1_soviets_su57attackbomber` | air | — | 65,000 | 220 | 3,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_submarine` | nav | — | 100,000 | 75 | 1,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_supersonicnuclearbomber` | air | — | 125,000 | 200 | 7,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `ra1_soviets_teslacoil` | def | — | 90,000 | — | 1,500 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_teslatank` | veh | fire_support | 40,000 | 80 | 1,700 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_teslayak` | air | — | 64,000 | 190 | 2,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_v1rockettruck` | veh | artillery | 25,000 | 100 | 850 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `ra1_soviets_v2rocketlauncher` | veh | artillery | 30,000 | 85 | 1,600 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `ra1_soviets_volkov` | inf | commando | 400,000 | 55 | 10,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `ra1_soviets_yakscoutplane` | air | — | 32,000 | 170 | 800 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `ra1_soviets_zapper` | inf | heavy_infantry | 60,000 | 30 | 1,200 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_advancedguardtower` | def | — | 140,000 | — | 1,600 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_gdi_apc` | veh | armed_troop_transport | 47,500 | 100 | 1,400 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `td_gdi_archerartillery` | veh | artillery_tank | 35,000 | 70 | 750 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_assaultapc` | veh | line_breaker | 250,000 | 100 | 3,930 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `td_gdi_battletank` | veh | mbt | 125,000 | 80 | 900 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_gdi_boxer` | veh | support | 110,000 | 80 | 1,550 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `td_gdi_chinooktransport` | air | — | 100,000 | 150 | 3,930 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `td_gdi_commando` | inf | commando | 80,000 | 65 | 3,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `td_gdi_defenserig` | veh | epic_vehicle | 400,000 | 60 | 5,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `td_gdi_empgrenadier` | inf | grenadier | 32,000 | 60 | 500 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_exosuit` | veh | fire_support | 50,000 | 100 | 1,200 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_firehawk` | air | — | 180,000 | 180 | 2,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_gdi_grenadier` | inf | grenadier | 8,000 | 75 | 200 | HOLD_THIN_CLASS_COHORT | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_gdi_guardtower` | def | — | 60,000 | — | 500 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_gdi_havoc` | inf | commando | 100,000 | 75 | 4,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `td_gdi_heavysniper` | inf | heavy_sniper | 25,000 | 78 | 700 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_humvee` | veh | scout_vehicle | 27,500 | 150 | 400 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_gdi_humveemkii` | veh | scout_vehicle | 37,500 | 115 | 700 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `td_gdi_landingcraft` | veh | — | 75,000 | 125 | 500 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `td_gdi_mammothtank` | veh | high_tech_tank | 225,000 | 60 | 1,600 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_gdi_mammothtankmkiii` | veh | high_tech_tank | 500,000 | 55 | 3,000 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_minigunner` | inf | scout | 31,000 | 63 | 100 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_gdi_missileboat` | nav | — | 75,000 | 100 | 1,600 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_gdi_mlrs` | veh | missile_vehicle | 25,000 | 80 | 1,000 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_gdi_mobileconstructionvehicle` | veh | support | 300,000 | 75 | 5,000 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `td_gdi_officer` | inf | special_forces | 32,000 | 79 | 1,530 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_orca` | air | — | 32,500 | 175 | 1,700 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_gdi_predatortank` | veh | mbt | 170,000 | 70 | 1,250 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_railgunbattleship` | nav | — | 167,500 | 50 | 2,600 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_gdi_rocketsoldier` | inf | rocket_trooper | 9,000 | 50 | 300 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_gdi_shotgunner` | inf | closecombat | 50,000 | 75 | 200 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_skyshield` | def | — | 93,000 | — | 900 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_gdi_sonicmissilesoldier` | inf | heavy_infantry | 25,000 | 50 | 400 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_gdi_supercarrier` | nav | — | 300,000 | 50 | 4,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_gdi_tiberiumharvester` | veh | — | 150,000 | 60 | 1,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_apacheattackhelicopter` | air | — | 45,000 | 160 | 1,600 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_artillery` | veh | artillery | 17,500 | 55 | 400 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_attacksubmarine` | nav | — | 160,000 | 80 | 1,600 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_ballisticmissilesubmarine` | nav | — | 200,000 | 60 | 2,800 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_blackhandflamer` | inf | heavy_infantry | 36,000 | 66 | 600 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_buggy` | veh | scout_vehicle | 20,000 | 200 | 300 | HOLD_CLASS_FIT_RESIDUAL | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_buggymkii` | veh | scout_vehicle | 25,000 | 120 | 600 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `td_nod_chemicalattackbike` | veh | missile_vehicle | 22,500 | 175 | 750 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_chemicalrocketsoldier` | inf | rocket_trooper | 18,000 | 60 | 400 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_chemicalssmlauncher` | veh | artillery | 32,500 | 75 | 1,200 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_chemicalstealthtank` | veh | high_tech_tank | 90,000 | 120 | 1,800 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_chemicalwarrior` | inf | melee | 48,000 | 48 | 500 | HOLD_THIN_CLASS_COHORT | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_chinooktransport` | air | — | 100,000 | 150 | 3,100 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `td_nod_commando` | inf | commando | 80,000 | 65 | 3,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `td_nod_flametank` | veh | line_breaker | 100,000 | 80 | 800 | HOLD_THIN_CLASS_COHORT | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_flametankmkii` | veh | line_breaker | 200,000 | 75 | 1,300 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_flamethrower` | inf | melee | 20,000 | 60 | 200 | HOLD_THIN_CLASS_COHORT | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_gunturret` | def | — | 150,000 | — | 700 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_lasercommando` | inf | commando | 57,000 | 79 | 5,000 | LIMITED_UNIT_SEPARATE_REVIEW | BuildLimit 1 is outside the ordinary anchor population; retain its separate hero/epic or support review. |
| `td_nod_lasercorvette` | nav | — | 150,000 | 60 | 2,300 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_lasertrooper` | inf | special_forces | 59,000 | 51 | 750 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_laserturret` | def | — | 72,500 | — | 1,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_lighttank` | veh | light_tank | 80,000 | 110 | 600 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_lighttankmkii` | veh | light_tank | 80,000 | 100 | 800 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_minigunner` | inf | scout | 30,000 | 66 | 100 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_mobileconstructionvehicle` | veh | support | 300,000 | 75 | 5,000 | SUPPORT_PRICE_EXEMPT | The support pricing exception applies; no combat formula target is invented. |
| `td_nod_obeliskoflight` | def | — | 242,500 | — | 1,800 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_reconbike` | veh | missile_vehicle | 17,500 | 200 | 500 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_rocketsoldier` | inf | rocket_trooper | 9,000 | 50 | 300 | REVIEWABLE_NO_AUTOMATIC_WRITE | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_samsite` | def | — | 100,000 | — | 800 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_specterartillery` | veh | artillery | 22,500 | 100 | 900 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_ssmlauncher` | veh | fire_support | 20,000 | 100 | 800 | HOLD_THIN_CLASS_COHORT | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_stealthharvester` | veh | — | 125,000 | 75 | 1,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_stealthsoldier` | inf | special_forces | 25,000 | 72 | 753 | SCALAR_REFERENCE_COVERAGE_REQUIRED | Not full external-plus-frozen-self coverage on all five calibration axes |
| `td_nod_stealthtank` | veh | missile_vehicle | 25,000 | 150 | 900 | HOLD_CLASS_DPS_METRIC_BASIS | Reference-complete anchor-cohort proposal; class sign-off and gameplay remain pending. |
| `td_nod_tiberiumharvester` | veh | — | 150,000 | 60 | 1,000 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |
| `td_nod_transportsubmarine` | veh | — | 50,000 | 150 | 500 | CARGO_AWAITS_FINAL_PASSENGER_PRICES | Apply the passenger-sum rule after the selected infantry prices are settled. |
| `td_nod_venom` | air | — | 27,500 | 200 | 900 | CLASS_MEMBERSHIP_REQUIRED | No eligible mapped class member |

All class candidates remain **UNAPPROVED**. Review warnings before any calibration or anchor decision.
