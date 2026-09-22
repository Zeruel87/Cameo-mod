# Baseband feasibility and where the baseline has to go

band ratio = class price / cost0.  cost0 CANCELS — only hp0/speed0/range0/dps0 move it.
the baseline sits at exactly 100%; the 2x-HP/2x-DPS verifier at exactly 250%.

recomputation cross-check against check_band: 404/404 ratios identical

| class | members | in band now | best single-k | k* | min% | max% | span | verdict |
|---|--:|--:|--:|--:|--:|--:|--:|---|
| `melee` | 35 | 15 (43%) | 21 (60%) | 1.111 | 24% | 680% | 33.7x | CURRENT-ANCHOR SPAN > 2.5 |
| `heavy_infantry` | 35 | 19 (54%) | 22 (63%) | 0.745 | 81% | 4079% | 31.6x | CURRENT-ANCHOR SPAN > 2.5 |
| `pure_sniper` | 9 | 2 (22%) | 6 (67%) | 1.284 | 38% | 861% | 31.5x | CURRENT-ANCHOR SPAN > 2.5 |
| `artillery` | 30 | 9 (30%) | 20 (67%) | 0.752 | 26% | 956% | 24.3x | CURRENT-ANCHOR SPAN > 2.5 |
| `rocket_trooper` | 39 | 15 (38%) | 21 (54%) | 1.168 | 78% | 1401% | 22.0x | CURRENT-ANCHOR SPAN > 2.5 |
| `special_forces` | 16 | 3 (19%) | 10 (62%) | 1.215 | 68% | 960% | 18.3x | CURRENT-ANCHOR SPAN > 2.5 |
| `scout_vehicle` | 16 | 11 (69%) | 11 (69%) | 0.887 | 36% | 673% | 15.2x | CURRENT-ANCHOR SPAN > 2.5 |
| `fire_support` | 28 | 1 (4%) | 17 (61%) | 0.475 | 38% | 1138% | 13.6x | CURRENT-ANCHOR SPAN > 2.5 |
| `scout` | 27 | 13 (48%) | 14 (52%) | 1.145 | 53% | 560% | 12.6x | CURRENT-ANCHOR SPAN > 2.5 |
| `grenadier` | 7 | 2 (29%) | 4 (57%) | 1.433 | 101% | 895% | 12.6x | CURRENT-ANCHOR SPAN > 2.5 |
| `mbt` | 42 | 1 (2%) | 32 (76%) | 0.580 | 48% | 1164% | 11.9x | CURRENT-ANCHOR SPAN > 2.5 |
| `missile_vehicle` | 14 | 1 (7%) | 9 (64%) | 0.432 | 64% | 1231% | 10.7x | CURRENT-ANCHOR SPAN > 2.5 |
| `artillery_tank` | 7 | 1 (14%) | 5 (71%) | 0.667 | 47% | 487% | 8.3x | CURRENT-ANCHOR SPAN > 2.5 |
| `closecombat` | 4 | 1 (25%) | 3 (75%) | 0.811 | 101% | 526% | 4.6x | CURRENT-ANCHOR SPAN > 2.5 |
| `anti_air_vehicle` | 9 | 0 (0%) | 7 (78%) | 0.458 | 46% | 372% | 4.5x | CURRENT-ANCHOR SPAN > 2.5 |
| `mortar` | 5 | 2 (40%) | 4 (80%) | 0.896 | 58% | 249% | 3.9x | CURRENT-ANCHOR SPAN > 2.5 |
| `high_tech_tank` | 24 | 3 (12%) | 21 (88%) | 0.657 | 89% | 442% | 3.9x | CURRENT-ANCHOR SPAN > 2.5 |
| `light_tank` | 15 | 6 (40%) | 12 (80%) | 0.839 | 96% | 413% | 3.8x | CURRENT-ANCHOR SPAN > 2.5 |
| `line_breaker` | 16 | 0 (0%) | 9 (56%) | 0.423 | 81% | 948% | 3.7x | CURRENT-ANCHOR SPAN > 2.5 |
| `archer` | 4 | 2 (50%) | 3 (75%) | 1.384 | 101% | 287% | 3.6x | CURRENT-ANCHOR SPAN > 2.5 |
| `flying_infantry` | 9 | 6 (67%) | 7 (78%) | 1.057 | 98% | 330% | 3.6x | CURRENT-ANCHOR SPAN > 2.5 |
| `heavy_sniper` | 3 | 2 (67%) | 3 (100%) | 0.942 | 101% | 231% | 2.2x | fits fully |
| `dreadnought` | 5 | 0 (0%) | 5 (100%) | 0.440 | 100% | 231% | 1.7x | fits fully |
| `tank_destroyer` | 5 | 0 (0%) | 5 (100%) | 0.795 | 101% | 154% | 1.6x | fits fully |

**115/404 (28%) of priced members sit in the sweet spot today; re-scaling each class baseline alone reaches 271/404 (67%).**

**21 of 24 classes exceed the 2.5x envelope at the recorded current anchor** — this is a current-anchor observation, not a feasibility proof.
The spread is concentrated, not general: below is each class's current-anchor ratio window and the members outside that window.

| class | current-anchor window | window span | members outside the current-anchor ratio window |
|---|--:|--:|---|
| `melee` | 21/35 | 2.4x | `naxis_slave` (27%), `zerg_zergling` (64%), `td_nod_flamethrower` (92%), `asianalliance_japanesesamurai` (120%), `asianalliance_alligator` (127%) +9 more |
| `heavy_infantry` | 24/35 | 2.4x | `naxis_naxiflamer` (50%), `ixian_shockinfantry` (55%), `ra1_soviets_flamethrower` (57%), `ixian_storminfantry` (60%), `tkm_juggernaut` (66%) +6 more |
| `pure_sniper` | 6/9 | 2.4x | `naxis_naximercenarysniper` (60%), `forgotten_mutantsniper` (129%), `terran_reaper` (1883%) |
| `artillery` | 21/30 | 2.5x | `harkonnen_inkvine` (17%), `harkonnen_buzzsaw` (26%), `tkm_dronepodtruck` (29%), `ra1_soviets_nuclearv2launcher` (136%), `ts_gdi_juggernautmkii` (174%) +4 more |
| `rocket_trooper` | 20/39 | 2.3x | `td_gdi_rocketsoldier` (110%), `td_nod_rocketsoldier` (110%), `tkm_rocketeer` (119%), `futuretech_missiledroid` (411%), `ra2_allies_guardiangi` (453%) +14 more |
| `special_forces` | 10/16 | 1.8x | `japan_imperialscoutsman` (105%), `tkm_trooper` (122%), `cabal_eliminator800` (725%), `td_gdi_officer` (1144%), `terran_ghost` (1274%) +1 more |
| `scout_vehicle` | 12/16 | 2.5x | `atreides_sandbike` (30%), `naxis_bmwbike` (40%), `protoss_positron` (277%), `ordos_raider` (460%) |
| `fire_support` | 22/28 | 2.3x | `futuretech_energizer` (11%), `td_gdi_exosuit` (19%), `naxis_antitankcannon` (22%), `schwarzermond_korruptesbiest` (77%), `schwarzermond_crystaltank` (97%) +1 more |
| `scout` | 13/27 | 2.3x | `forgotten_mutant` (173%), `ordos_lightinfantry` (231%), `ra1_soviets_ak47conscript` (281%), `naxis_coneheadsknights` (303%), `forgotten_mutantsoldier` (311%) +9 more |
| `grenadier` | 4/7 | 1.4x | `latinsyndicate_grenademonkey` (890%), `td_gdi_empgrenadier` (1012%), `steelconsortium_hoverboardgrenadier` (3080%) |
| `mbt` | 36/42 | 2.5x | `corrino_buggy` (23%), `atreides_sonictank` (24%), `combat_tank.harkonnen` (27%), `naxis_kingtigerheavytank` (83%), `harkonnen_flametank` (151%) +1 more |
| `missile_vehicle` | 11/14 | 2.1x | `td_nod_stealthtank` (14%), `missile_tank` (16%), `ixian_ixmissiletank` (145%) |
| `artillery_tank` | 5/7 | 1.6x | `asianalliance_howitzer` (22%), `forgotten_mlrs` (184%) |
| `closecombat` | 3/4 | 1.8x | `asianalliance_fanatic` (276%) |
| `anti_air_vehicle` | 8/9 | 2.1x | `harkonnen_adp` (13%) |
| `mortar` | 4/5 | 2.2x | `ra1_soviets_mortarsoldier` (46%) |
| `high_tech_tank` | 21/24 | 2.1x | `naxis_maus` (104%), `japan_oitank` (147%), `cabal_avatar` (160%) |
| `light_tank` | 13/15 | 2.4x | `cabal_ravager` (232%), `terran_vulture` (256%) |
| `line_breaker` | 13/16 | 2.4x | `ts_gdi_disruptor` (24%), `ordos_heavyautoguntank` (84%), `protoss_archon` (88%) |
| `archer` | 3/4 | 1.9x | `wc2_humans_highelvenarcher` (744%) |
| `flying_infantry` | 7/9 | 2.2x | `zerg_shriek` (110%), `naxis_skymage` (390%) |

**114 members across those classes sit outside their current-anchor ratio window.** Each is one of three things, and only a maintainer can say which:
  * misclassified — `futuretech_blackwidow` is in `melee` with a range of 9000, and `corrino_buggy` is in `mbt`;
  * a legitimate higher tier that needs a tech-tier gate rather than a wider band;
  * genuinely mis-stated, which is what the pipeline exists to fix.

⛔ Until that triage happens, no baseline for these classes can be signed: the current-anchor window does not determine class membership or baseline feasibility.

## The fitted baselines, on the grid

| class | hp0 | speed0 | range0_wdist | dps0 | (cost0 unchanged — it cannot move the band) |
|---|--:|--:|--:|--:|---|
| `anti_air_vehicle` | 78000 | 50 | 2750 | 573 | 1000 |
| `archer` | 28000 | 97 | 9690 | 277 | 500 |
| `artillery` | 45000 | 56 | 11280 | 376 | 500 |
| `artillery_tank` | 93000 | 57 | 8000 | 350 | 700 |
| `closecombat` | 41000 | 61 | 2840 | 203 | 200 |
| `dreadnought` | 506000 | 22 | 3080 | 1652 | 3000 |
| `fire_support` | 57000 | 43 | 4750 | 997 | 1400 |
| `flying_infantry` | 19000 | 85 | 5280 | 264 | 600 |
| `grenadier` | 11000 | 107 | 7880 | 172 | 200 |
| `heavy_infantry` | 37000 | 37 | 3720 | 745 | 800 |
| `heavy_sniper` | 24000 | 75 | 7530 | 377 | 700 |
| `high_tech_tank` | 460000 | 43 | 4270 | 1314 | 2000 |
| `light_tank` | 84000 | 105 | 4200 | 168 | 400 |
| `line_breaker` | 317000 | 34 | 1060 | 677 | 1600 |
| `mbt` | 139000 | 55 | 3190 | 348 | 800 |
| `melee` | 30000 | 100 | 1670 | 333 | 280 |
| `missile_vehicle` | 69000 | 43 | 3450 | 518 | 1200 |
| `mortar` | 27000 | 45 | 8960 | 358 | 500 |
| `pure_sniper` | 14000 | 77 | 12840 | 385 | 320 |
| `rocket_trooper` | 12000 | 64 | 7590 | 234 | 300 |
| `scout` | 23000 | 69 | 5720 | 69 | 100 |
| `scout_vehicle` | 27000 | 177 | 3990 | 399 | 300 |
| `special_forces` | 18000 | 61 | 7290 | 292 | 200 |
| `tank_destroyer` | 119000 | 56 | 5960 | 715 | 600 |

## Per-outlier evidence — FOR A MAINTAINER DECISION, never applied

A member is listed when it sits outside its current-anchor ratio window.

⛔ **The band does not determine class membership or baseline feasibility.** Measured: the median member is accepted by **6 of 27** class baselines (mean 5.6, max 9), so "another class would take it" is true of nearly everything and is not evidence. `anchor_readiness.py` says why — these classes are *"separated by what they SHOOT AT, not by their stats. No stat-based check can police these boundaries."* An earlier version of this table used the best-fitting class as the deciding signal and labelled 81 of these MISCLASSIFIED, which put `terran_ghost` in `artillery` on one arbitrary pick out of six. The `accepts` column is therefore a COUNT, and only 0 or 1 discriminates.

| class | actor | % of own baseline | worst axis vs core | accepts | signal | evidence |
|---|---|--:|---|--:|---|---|
| `anti_air_vehicle` | `harkonnen_adp` | 13% | raw_dps 0.4x | 6 | **AXIS OUTLIER** | raw_dps 0.4x its class core — checkable; 6 classes would accept it, so that says nothing |
| `archer` | `wc2_humans_highelvenarcher` | 744% | raw_dps 1.8x | 5 | **ROLE REVIEW** | 744% of baseline, no axis dominates, 5 classes accept it — stats cannot decide this one |
| `artillery` | `harkonnen_inkvine` | 17% | raw_dps 0.0x | 0 | **NO CLASS ACCEPTS** | outside every class baseline; raw_dps 0.0x its own core |
| `artillery` | `harkonnen_buzzsaw` | 26% | range 0.4x | 6 | **AXIS OUTLIER** | range 0.4x its class core — checkable; 6 classes would accept it, so that says nothing |
| `artillery` | `tkm_dronepodtruck` | 29% | raw_dps 0.0x | 2 | **AXIS OUTLIER** | raw_dps 0.0x its class core — checkable; 2 classes would accept it, so that says nothing |
| `artillery` | `ra1_soviets_nuclearv2launcher` | 136% | raw_dps 3.0x | 5 | **AXIS OUTLIER** | raw_dps 3.0x its class core — checkable; 5 classes would accept it, so that says nothing |
| `artillery` | `ts_gdi_juggernautmkii` | 174% | raw_dps 2.7x | 6 | **AXIS OUTLIER** | raw_dps 2.7x its class core — checkable; 6 classes would accept it, so that says nothing |
| `artillery` | `ixian_ixsiegetank` | 199% | raw_dps 1.6x | 5 | **ROLE REVIEW** | 199% of baseline, no axis dominates, 5 classes accept it — stats cannot decide this one |
| `artillery` | `wc2_humans_siegeengine` | 245% | raw_dps 2.2x | 6 | **AXIS OUTLIER** | raw_dps 2.2x its class core — checkable; 6 classes would accept it, so that says nothing |
| `artillery` | `wc2_orcs_siegeengine` | 251% | raw_dps 2.2x | 6 | **AXIS OUTLIER** | raw_dps 2.2x its class core — checkable; 6 classes would accept it, so that says nothing |
| `artillery` | `cabal_artilleryspider` | 421% | raw_dps 4.1x | 4 | **AXIS OUTLIER** | raw_dps 4.1x its class core — checkable; 4 classes would accept it, so that says nothing |
| `artillery_tank` | `asianalliance_howitzer` | 22% | raw_dps 0.5x | 6 | **ROLE REVIEW** | 22% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `artillery_tank` | `forgotten_mlrs` | 184% | raw_dps 4.8x | 6 | **AXIS OUTLIER** | raw_dps 4.8x its class core — checkable; 6 classes would accept it, so that says nothing |
| `closecombat` | `asianalliance_fanatic` | 276% | raw_dps 2.0x | 6 | **ROLE REVIEW** | 276% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `fire_support` | `futuretech_energizer` | 11% | speed 0.7x | 4 | **ROLE REVIEW** | 11% of baseline, no axis dominates, 4 classes accept it — stats cannot decide this one |
| `fire_support` | `td_gdi_exosuit` | 19% | speed 1.3x | 3 | **ROLE REVIEW** | 19% of baseline, no axis dominates, 3 classes accept it — stats cannot decide this one |
| `fire_support` | `naxis_antitankcannon` | 22% | hp 0.3x | 7 | **AXIS OUTLIER** | hp 0.3x its class core — checkable; 7 classes would accept it, so that says nothing |
| `fire_support` | `schwarzermond_korruptesbiest` | 77% | hp 4.0x | 5 | **AXIS OUTLIER** | hp 4.0x its class core — checkable; 5 classes would accept it, so that says nothing |
| `fire_support` | `schwarzermond_crystaltank` | 97% | hp 6.7x | 4 | **AXIS OUTLIER** | hp 6.7x its class core — checkable; 4 classes would accept it, so that says nothing |
| `fire_support` | `protoss_reaver` | 144% | raw_dps 4.6x | 4 | **AXIS OUTLIER** | raw_dps 4.6x its class core — checkable; 4 classes would accept it, so that says nothing |
| `flying_infantry` | `zerg_shriek` | 110% | range 0.2x | 8 | **AXIS OUTLIER** | range 0.2x its class core — checkable; 8 classes would accept it, so that says nothing |
| `flying_infantry` | `naxis_skymage` | 390% | raw_dps 1.9x | 7 | **LATER TECH** | tier 0.75 vs core 1.00 — a tech-tier gate may explain the 390% |
| `grenadier` | `latinsyndicate_grenademonkey` | 890% | hp 3.2x | 7 | **AXIS OUTLIER** | hp 3.2x its class core — checkable; 7 classes would accept it, so that says nothing |
| `grenadier` | `td_gdi_empgrenadier` | 1012% | hp 3.4x | 8 | **AXIS OUTLIER** | hp 3.4x its class core — checkable; 8 classes would accept it, so that says nothing |
| `grenadier` | `steelconsortium_hoverboardgrenadier` | 3080% | raw_dps 4.5x | 8 | **AXIS OUTLIER** | raw_dps 4.5x its class core — checkable; 8 classes would accept it, so that says nothing |
| `heavy_infantry` | `naxis_naxiflamer` | 50% | raw_dps 0.5x | 4 | **AXIS OUTLIER** | raw_dps 0.5x its class core — checkable; 4 classes would accept it, so that says nothing |
| `heavy_infantry` | `ixian_shockinfantry` | 55% | hp 0.8x | 5 | **ROLE REVIEW** | 55% of baseline, no axis dominates, 5 classes accept it — stats cannot decide this one |
| `heavy_infantry` | `ra1_soviets_flamethrower` | 57% | hp 0.3x | 5 | **AXIS OUTLIER** | hp 0.3x its class core — checkable; 5 classes would accept it, so that says nothing |
| `heavy_infantry` | `ixian_storminfantry` | 60% | range 1.2x | 6 | **ROLE REVIEW** | 60% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `heavy_infantry` | `tkm_juggernaut` | 66% | hp 0.8x | 6 | **ROLE REVIEW** | 66% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `heavy_infantry` | `ts_gdi_zonetrooper` | 194% | hp 1.7x | 6 | **ROLE REVIEW** | 194% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `heavy_infantry` | `steelconsortium_quantummissiletrooper` | 198% | raw_dps 1.7x | 6 | **ROLE REVIEW** | 198% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `heavy_infantry` | `schwarzermond_ubermensch` | 210% | raw_dps 2.4x | 6 | **AXIS OUTLIER** | raw_dps 2.4x its class core — checkable; 6 classes would accept it, so that says nothing |
| `heavy_infantry` | `terran_marauder` | 219% | hp 1.9x | 6 | **ROLE REVIEW** | 219% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `heavy_infantry` | `forgotten_viniferafiend` | 486% | raw_dps 4.5x | 5 | **AXIS OUTLIER** | raw_dps 4.5x its class core — checkable; 5 classes would accept it, so that says nothing |
| `heavy_infantry` | `cabal_enlighted` | 1570% | raw_dps 28.0x | 3 | **AXIS OUTLIER** | raw_dps 28.0x its class core — checkable; 3 classes would accept it, so that says nothing |
| `high_tech_tank` | `naxis_maus` | 104% | hp 3.3x | 5 | **AXIS OUTLIER** | hp 3.3x its class core — checkable; 5 classes would accept it, so that says nothing |
| `high_tech_tank` | `japan_oitank` | 147% | hp 3.6x | 4 | **AXIS OUTLIER** | hp 3.6x its class core — checkable; 4 classes would accept it, so that says nothing |
| `high_tech_tank` | `cabal_avatar` | 160% | hp 5.6x | 4 | **AXIS OUTLIER** | hp 5.6x its class core — checkable; 4 classes would accept it, so that says nothing |
| `light_tank` | `cabal_ravager` | 232% | raw_dps 5.7x | 5 | **AXIS OUTLIER** | raw_dps 5.7x its class core — checkable; 5 classes would accept it, so that says nothing |
| `light_tank` | `terran_vulture` | 256% | raw_dps 4.3x | 5 | **AXIS OUTLIER** | raw_dps 4.3x its class core — checkable; 5 classes would accept it, so that says nothing |
| `line_breaker` | `ts_gdi_disruptor` | 24% | raw_dps 0.1x | 5 | **AXIS OUTLIER** | raw_dps 0.1x its class core — checkable; 5 classes would accept it, so that says nothing |
| `line_breaker` | `ordos_heavyautoguntank` | 84% | range 3.1x | 3 | **AXIS OUTLIER** | range 3.1x its class core — checkable; 3 classes would accept it, so that says nothing |
| `line_breaker` | `protoss_archon` | 88% | raw_dps 2.4x | 5 | **AXIS OUTLIER** | raw_dps 2.4x its class core — checkable; 5 classes would accept it, so that says nothing |
| `mbt` | `corrino_buggy` | 23% | hp 0.2x | 6 | **AXIS OUTLIER** | hp 0.2x its class core — checkable; 6 classes would accept it, so that says nothing |
| `mbt` | `atreides_sonictank` | 24% | raw_dps 0.2x | 7 | **AXIS OUTLIER** | raw_dps 0.2x its class core — checkable; 7 classes would accept it, so that says nothing |
| `mbt` | `combat_tank.harkonnen` | 27% | raw_dps 0.6x | 6 | **ROLE REVIEW** | 27% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `mbt` | `naxis_kingtigerheavytank` | 83% | hp 1.8x | 4 | **ROLE REVIEW** | 83% of baseline, no axis dominates, 4 classes accept it — stats cannot decide this one |
| `mbt` | `harkonnen_flametank` | 151% | raw_dps 7.9x | 5 | **AXIS OUTLIER** | raw_dps 7.9x its class core — checkable; 5 classes would accept it, so that says nothing |
| `mbt` | `cabal_widow` | 272% | raw_dps 11.7x | 5 | **AXIS OUTLIER** | raw_dps 11.7x its class core — checkable; 5 classes would accept it, so that says nothing |
| `melee` | `naxis_slave` | 27% | raw_dps 0.1x | 0 | **NO CLASS ACCEPTS** | outside every class baseline; raw_dps 0.1x its own core |
| `melee` | `zerg_zergling` | 64% | hp 0.2x | 4 | **AXIS OUTLIER** | hp 0.2x its class core — checkable; 4 classes would accept it, so that says nothing |
| `melee` | `td_nod_flamethrower` | 92% | hp 0.4x | 4 | **AXIS OUTLIER** | hp 0.4x its class core — checkable; 4 classes would accept it, so that says nothing |
| `melee` | `asianalliance_japanesesamurai` | 120% | range 0.5x | 5 | **ROLE REVIEW** | 120% of baseline, no axis dominates, 5 classes accept it — stats cannot decide this one |
| `melee` | `asianalliance_alligator` | 127% | range 0.4x | 5 | **AXIS OUTLIER** | range 0.4x its class core — checkable; 5 classes would accept it, so that says nothing |
| `melee` | `protoss_zealot` | 130% | range 0.4x | 4 | **AXIS OUTLIER** | range 0.4x its class core — checkable; 4 classes would accept it, so that says nothing |
| `melee` | `japan_samurai` | 142% | range 0.5x | 4 | **ROLE REVIEW** | 142% of baseline, no axis dominates, 4 classes accept it — stats cannot decide this one |
| `melee` | `futuretech_enforcer` | 150% | hp 0.6x | 5 | **ROLE REVIEW** | 150% of baseline, no axis dominates, 5 classes accept it — stats cannot decide this one |
| `melee` | `wc2_humans_militiapeasant` | 154% | hp 0.4x | 4 | **AXIS OUTLIER** | hp 0.4x its class core — checkable; 4 classes would accept it, so that says nothing |
| `melee` | `ts_nod_shadowteam` | 570% | range 2.6x | 6 | **AXIS OUTLIER** | range 2.6x its class core — checkable; 6 classes would accept it, so that says nothing |
| `melee` | `wc2_humans_warcraft3footman` | 571% | raw_dps 2.2x | 7 | **AXIS OUTLIER** | raw_dps 2.2x its class core — checkable; 7 classes would accept it, so that says nothing |
| `melee` | `protoss_amaranth` | 759% | raw_dps 2.7x | 7 | **AXIS OUTLIER** | raw_dps 2.7x its class core — checkable; 7 classes would accept it, so that says nothing |
| `melee` | `wc2_orcs_warcraft3grunt` | 772% | raw_dps 2.4x | 5 | **AXIS OUTLIER** | raw_dps 2.4x its class core — checkable; 5 classes would accept it, so that says nothing |
| `melee` | `futuretech_blackwidow` | 926% | range 2.9x | 7 | **AXIS OUTLIER** | range 2.9x its class core — checkable; 7 classes would accept it, so that says nothing |
| `missile_vehicle` | `td_nod_stealthtank` | 14% | raw_dps 0.7x | 4 | **ROLE REVIEW** | 14% of baseline, no axis dominates, 4 classes accept it — stats cannot decide this one |
| `missile_vehicle` | `missile_tank` | 16% | raw_dps 0.6x | 4 | **ROLE REVIEW** | 16% of baseline, no axis dominates, 4 classes accept it — stats cannot decide this one |
| `missile_vehicle` | `ixian_ixmissiletank` | 145% | raw_dps 9.0x | 2 | **AXIS OUTLIER** | raw_dps 9.0x its class core — checkable; 2 classes would accept it, so that says nothing |
| `mortar` | `ra1_soviets_mortarsoldier` | 46% | hp 0.6x | 6 | **ROLE REVIEW** | 46% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `pure_sniper` | `naxis_naximercenarysniper` | 60% | raw_dps 0.3x | 1 | **ONE CLASS ACCEPTS** | only `scout` takes it at 110% |
| `pure_sniper` | `forgotten_mutantsniper` | 129% | raw_dps 0.2x | 4 | **AXIS OUTLIER** | raw_dps 0.2x its class core — checkable; 4 classes would accept it, so that says nothing |
| `pure_sniper` | `terran_reaper` | 1883% | hp 2.9x | 7 | **AXIS OUTLIER** | hp 2.9x its class core — checkable; 7 classes would accept it, so that says nothing |
| `rocket_trooper` | `td_gdi_rocketsoldier` | 110% | hp 0.5x | 4 | **ROLE REVIEW** | 110% of baseline, no axis dominates, 4 classes accept it — stats cannot decide this one |
| `rocket_trooper` | `td_nod_rocketsoldier` | 110% | hp 0.5x | 4 | **ROLE REVIEW** | 110% of baseline, no axis dominates, 4 classes accept it — stats cannot decide this one |
| `rocket_trooper` | `tkm_rocketeer` | 119% | hp 0.5x | 3 | **ROLE REVIEW** | 119% of baseline, no axis dominates, 3 classes accept it — stats cannot decide this one |
| `rocket_trooper` | `futuretech_missiledroid` | 411% | hp 4.1x | 3 | **AXIS OUTLIER** | hp 4.1x its class core — checkable; 3 classes would accept it, so that says nothing |
| `rocket_trooper` | `ra2_allies_guardiangi` | 453% | hp 2.7x | 5 | **AXIS OUTLIER** | hp 2.7x its class core — checkable; 5 classes would accept it, so that says nothing |
| `rocket_trooper` | `corrino_sardaukar_javelin` | 456% | hp 7.3x | 7 | **AXIS OUTLIER** | hp 7.3x its class core — checkable; 7 classes would accept it, so that says nothing |
| `rocket_trooper` | `corrino_sardaukar_laser` | 456% | hp 7.3x | 7 | **AXIS OUTLIER** | hp 7.3x its class core — checkable; 7 classes would accept it, so that says nothing |
| `rocket_trooper` | `ixian_twinrockettrooper` | 485% | raw_dps 2.3x | 7 | **AXIS OUTLIER** | raw_dps 2.3x its class core — checkable; 7 classes would accept it, so that says nothing |
| `rocket_trooper` | `wc2_orcs_trollaxethrower` | 517% | hp 1.8x | 6 | **ROLE REVIEW** | 517% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `rocket_trooper` | `wc2_orcs_trollberserker` | 517% | hp 1.8x | 6 | **ROLE REVIEW** | 517% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `rocket_trooper` | `wc2_humans_elvenranger` | 631% | raw_dps 1.9x | 7 | **ROLE REVIEW** | 631% of baseline, no axis dominates, 7 classes accept it — stats cannot decide this one |
| `rocket_trooper` | `cabal_rocketcyborg` | 695% | hp 2.7x | 7 | **AXIS OUTLIER** | hp 2.7x its class core — checkable; 7 classes would accept it, so that says nothing |
| `rocket_trooper` | `terran_marine` | 1055% | raw_dps 2.9x | 6 | **AXIS OUTLIER** | raw_dps 2.9x its class core — checkable; 6 classes would accept it, so that says nothing |
| `rocket_trooper` | `corrino_sardaukar_bazooka` | 1092% | hp 7.3x | 6 | **AXIS OUTLIER** | hp 7.3x its class core — checkable; 6 classes would accept it, so that says nothing |
| `rocket_trooper` | `wc2_orcs_trollheadhunter` | 1169% | hp 2.4x | 6 | **AXIS OUTLIER** | hp 2.4x its class core — checkable; 6 classes would accept it, so that says nothing |
| `rocket_trooper` | `cabal_ascended` | 1915% | hp 4.2x | 7 | **AXIS OUTLIER** | hp 4.2x its class core — checkable; 7 classes would accept it, so that says nothing |
| `rocket_trooper` | `terran_madcap` | 2188% | raw_dps 4.0x | 7 | **AXIS OUTLIER** | raw_dps 4.0x its class core — checkable; 7 classes would accept it, so that says nothing |
| `rocket_trooper` | `wc2_orcs_kodobeast` | 2221% | hp 7.6x | 4 | **AXIS OUTLIER** | hp 7.6x its class core — checkable; 4 classes would accept it, so that says nothing |
| `rocket_trooper` | `zerg_hydralisk` | 2424% | hp 4.8x | 5 | **AXIS OUTLIER** | hp 4.8x its class core — checkable; 5 classes would accept it, so that says nothing |
| `scout` | `forgotten_mutant` | 173% | hp 1.8x | 6 | **ROLE REVIEW** | 173% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `scout` | `ordos_lightinfantry` | 231% | raw_dps 1.9x | 7 | **ROLE REVIEW** | 231% of baseline, no axis dominates, 7 classes accept it — stats cannot decide this one |
| `scout` | `ra1_soviets_ak47conscript` | 281% | hp 1.8x | 6 | **ROLE REVIEW** | 281% of baseline, no axis dominates, 6 classes accept it — stats cannot decide this one |
| `scout` | `naxis_coneheadsknights` | 303% | raw_dps 12.5x | 6 | **AXIS OUTLIER** | raw_dps 12.5x its class core — checkable; 6 classes would accept it, so that says nothing |
| `scout` | `forgotten_mutantsoldier` | 311% | raw_dps 2.2x | 5 | **AXIS OUTLIER** | raw_dps 2.2x its class core — checkable; 5 classes would accept it, so that says nothing |
| `scout` | `atreides_lightinfantry` | 325% | raw_dps 2.8x | 6 | **AXIS OUTLIER** | raw_dps 2.8x its class core — checkable; 6 classes would accept it, so that says nothing |
| `scout` | `corrino_lightinfantry` | 325% | raw_dps 2.8x | 6 | **AXIS OUTLIER** | raw_dps 2.8x its class core — checkable; 6 classes would accept it, so that says nothing |
| `scout` | `harkonnen_lightinfantry` | 325% | raw_dps 2.8x | 6 | **AXIS OUTLIER** | raw_dps 2.8x its class core — checkable; 6 classes would accept it, so that says nothing |
| `scout` | `light_inf` | 343% | raw_dps 2.6x | 5 | **AXIS OUTLIER** | raw_dps 2.6x its class core — checkable; 5 classes would accept it, so that says nothing |
| `scout` | `ixian_lightinfantry` | 361% | raw_dps 3.2x | 5 | **AXIS OUTLIER** | raw_dps 3.2x its class core — checkable; 5 classes would accept it, so that says nothing |
| `scout` | `ra2_allies_gi` | 367% | hp 2.0x | 5 | **ROLE REVIEW** | 367% of baseline, no axis dominates, 5 classes accept it — stats cannot decide this one |
| `scout` | `futuretech_scoutdroid` | 423% | raw_dps 5.4x | 6 | **AXIS OUTLIER** | raw_dps 5.4x its class core — checkable; 6 classes would accept it, so that says nothing |
| `scout` | `tkm_marine` | 561% | raw_dps 7.0x | 5 | **AXIS OUTLIER** | raw_dps 7.0x its class core — checkable; 5 classes would accept it, so that says nothing |
| `scout` | `zerg_spithid` | 869% | raw_dps 5.6x | 5 | **AXIS OUTLIER** | raw_dps 5.6x its class core — checkable; 5 classes would accept it, so that says nothing |
| `scout_vehicle` | `atreides_sandbike` | 30% | raw_dps 0.2x | 5 | **AXIS OUTLIER** | raw_dps 0.2x its class core — checkable; 5 classes would accept it, so that says nothing |
| `scout_vehicle` | `naxis_bmwbike` | 40% | raw_dps 0.3x | 6 | **AXIS OUTLIER** | raw_dps 0.3x its class core — checkable; 6 classes would accept it, so that says nothing |
| `scout_vehicle` | `protoss_positron` | 277% | hp 2.2x | 6 | **AXIS OUTLIER** | hp 2.2x its class core — checkable; 6 classes would accept it, so that says nothing |
| `scout_vehicle` | `ordos_raider` | 460% | raw_dps 2.2x | 7 | **AXIS OUTLIER** | raw_dps 2.2x its class core — checkable; 7 classes would accept it, so that says nothing |
| `special_forces` | `japan_imperialscoutsman` | 105% | raw_dps 0.4x | 5 | **AXIS OUTLIER** | raw_dps 0.4x its class core — checkable; 5 classes would accept it, so that says nothing |
| `special_forces` | `tkm_trooper` | 122% | raw_dps 0.1x | 6 | **AXIS OUTLIER** | raw_dps 0.1x its class core — checkable; 6 classes would accept it, so that says nothing |
| `special_forces` | `cabal_eliminator800` | 725% | hp 2.8x | 7 | **AXIS OUTLIER** | hp 2.8x its class core — checkable; 7 classes would accept it, so that says nothing |
| `special_forces` | `td_gdi_officer` | 1144% | raw_dps 3.0x | 8 | **AXIS OUTLIER** | raw_dps 3.0x its class core — checkable; 8 classes would accept it, so that says nothing |
| `special_forces` | `terran_ghost` | 1274% | raw_dps 2.2x | 7 | **AXIS OUTLIER** | raw_dps 2.2x its class core — checkable; 7 classes would accept it, so that says nothing |
| `special_forces` | `terran_specter` | 1915% | raw_dps 3.0x | 7 | **AXIS OUTLIER** | raw_dps 3.0x its class core — checkable; 7 classes would accept it, so that says nothing |

**Signal counts:** 80 AXIS OUTLIER, 30 ROLE REVIEW, 2 NO CLASS ACCEPTS, 1 LATER TECH, 1 ONE CLASS ACCEPTS

**Which axis puts them outside their core:** 61 raw_dps, 41 hp, 9 range, 2 speed

⭐ `raw_dps` dominates, and that agrees with the binding order of operations rather than fighting it: `BALANCE_PROGRAM_PLAN.md` §0a puts weapon STRUCTURE before pricing, W24 is still moving, and every anchor dossier already says *"No DPS target is proposed while W24 moves"*. So the majority of band failures are attributable to the one axis the pipeline has deliberately not settled — the band cannot be fitted before W24 closes, and the DPS-driven outliers here are not yet evidence about class membership.

⚠ `AXIS OUTLIER` is the only line that is checkable without a role judgement: one stat sits more than 2x off its class core, which is a fact about the unit. `ROLE REVIEW` means the stats genuinely cannot decide it.
