# audit_stat_formulas — house stat formulas

Violations: **667** across 1994 roster actors (reference-clean units: gdiarcher, raider.ordos)


## F1 — Repairable.HpPerStep ≠ HP/20  (44)

| actor | actual | expected |
|---|---|---|
| atreides_spiceharvester | HpPerStep 10000 | expected 9000 (HP 180000/20) |
| corrino_spiceharvester | HpPerStep 10000 | expected 9000 (HP 180000/20) |
| forgotten_scoopertank | HpPerStep 10000 | expected 12500 (HP 250000/20) |
| futuretech_beehivedronecarrier | HpPerStep 6500 | expected 6250 (HP 125000/20) |
| harkonnen_devastatormech | HpPerStep 31250 | expected 27500 (HP 550000/20) |
| harkonnen_spiceharvester | HpPerStep 10000 | expected 12000 (HP 240000/20) |
| ixian_empbomber | HpPerStep 5555 | expected 5550 (HP 111000/20) |
| japan_coreairfield | HpPerStep 15000 | expected 2500 (HP 50000/20) |
| japan_corebarracks | HpPerStep 15000 | expected 2500 (HP 50000/20) |
| japan_corepowerplant | HpPerStep 15000 | expected 2500 (HP 50000/20) |
| japan_coreradar | HpPerStep 15000 | expected 2500 (HP 50000/20) |
| japan_corerefinery | HpPerStep 15000 | expected 2500 (HP 50000/20) |
| japan_coreservicedepot | HpPerStep 15000 | expected 2500 (HP 50000/20) |
| japan_coretechcenter | HpPerStep 15000 | expected 2500 (HP 50000/20) |
| japan_corewarfactory | HpPerStep 15000 | expected 2500 (HP 50000/20) |
| naxis_bmwbike | HpPerStep 4125 | expected 1100 (HP 22000/20) |
| naxis_imperialturbotank | HpPerStep 3125 | expected 4125 (HP 82500/20) |
| naxis_nokana | HpPerStep 3125 | expected 22500 (HP 450000/20) |
| naxis_oldtank | HpPerStep 7875 | expected 5500 (HP 110000/20) |
| naxis_shoekarn | HpPerStep 10000 | expected 7500 (HP 150000/20) |
| naxis_sturmtiger | HpPerStep 2000 | expected 12500 (HP 250000/20) |
| naxis_transportzeppelin | HpPerStep 2625 | expected 62500 (HP 1250000/20) |
| ra1_soviets_stalinfist | HpPerStep 15000 | expected 5000 (HP 100000/20) |
| schwarzermond_gravitycoretank | HpPerStep 3125 | expected 15000 (HP 300000/20) |
| schwarzermond_laserbeetle | HpPerStep 4375 | expected 2375 (HP 47500/20) |
| schwarzermond_spacezeppelin | HpPerStep 2625 | expected 67500 (HP 1350000/20) |
| tkm_abrams | HpPerStep 4800 | expected 6000 (HP 120000/20) |
| tkm_bigshiee | HpPerStep 6000 | expected 25000 (HP 500000/20) |
| tkm_dronepodtruck | HpPerStep 1375 | expected 3000 (HP 60000/20) |
| tkm_flakbus | HpPerStep 1375 | expected 6000 (HP 120000/20) |
| tkm_medictruck | HpPerStep 1375 | expected 2500 (HP 50000/20) |
| tkm_quadtruck | HpPerStep 1375 | expected 3250 (HP 65000/20) |
| tkm_radartruck | HpPerStep 1375 | expected 3750 (HP 75000/20) |
| tkm_repairtruck | HpPerStep 1375 | expected 2500 (HP 50000/20) |
| tkm_sandmarine | HpPerStep 6000 | expected 40000 (HP 800000/20) |
| tkm_stryker | HpPerStep 1375 | expected 4000 (HP 80000/20) |
| tkm_t30 | HpPerStep 2637 | expected 20000 (HP 400000/20) |
| tkm_t72m | HpPerStep 2637 | expected 5000 (HP 100000/20) |
| tkm_trenchtank | HpPerStep 2637 | expected 10000 (HP 200000/20) |
| tkm_trenchtruck | HpPerStep 2637 | expected 5000 (HP 100000/20) |
| ts_gdi_mobilesensorarray | HpPerStep 2637 | expected 3000 (HP 60000/20) |
| ts_nod_attackcycle | HpPerStep 100 | expected 1000 (HP 20000/20) |
| ts_nod_mobilestealthgenerator | HpPerStep 2637 | expected 1000 (HP 20000/20) |
| ts_nod_subterraneanapc | HpPerStep 2637 | expected 875 (HP 17500/20) |


## F2 — SelfHealing Step ≠ HP/2500 (inf: HP/1000)  (129)

| actor | actual | expected |
|---|---|---|
| asianalliance_pulverizermecha | Step 114 | expected 285 (HP 285000/1000) |
| atreides_combattank | Step 10 | expected 40 (HP 100000/2500) |
| atreides_missiletank | Step 10 | expected 20 (HP 50000/2500) |
| atreides_repairtank | Step 10 | expected 24 (HP 60000/2500) |
| atreides_rockettrooper | Step 10 | expected 40 (HP 40000/1000) |
| atreides_sandbike | Step 10 | expected 12 (HP 30000/2500) |
| atreides_siegetank | Step 10 | expected 16 (HP 40000/2500) |
| atreides_spiceharvester | Step 80 | expected 72 (HP 180000/2500) |
| cabal_beholder | Step 50 | expected 125 (HP 125000/1000) |
| combat_tank.harkonnen | Step 10 | expected 28 (HP 70000/2500) |
| corrino_bmp | Step 10 | expected 16 (HP 40000/2500) |
| corrino_combattank | Step 10 | expected 40 (HP 100000/2500) |
| corrino_missiletank | Step 10 | expected 20 (HP 50000/2500) |
| corrino_sardaukar_bazooka | Step 50 | expected 120 (HP 120000/1000) |
| corrino_sardaukar_berserker | Step 50 | expected 120 (HP 120000/1000) |
| corrino_sardaukar_javelin | Step 50 | expected 120 (HP 120000/1000) |
| corrino_sardaukar_laser | Step 50 | expected 120 (HP 120000/1000) |
| corrino_sardaukar_sword | Step 50 | expected 120 (HP 120000/1000) |
| corrino_siegetank | Step 10 | expected 16 (HP 40000/2500) |
| corrino_spiceharvester | Step 80 | expected 72 (HP 180000/2500) |
| corrino_trooper | Step 10 | expected 40 (HP 40000/1000) |
| eden_tiger_acidcloud | Step 10 | expected 24 (HP 60000/2500) |
| forgotten_mutant | Step 36 | expected 45 (HP 45000/1000) |
| forgotten_mutanthijacker | Step 10 | expected 25 (HP 25000/1000) |
| forgotten_scoopertank | Step 80 | expected 100 (HP 250000/2500) |
| futuretech_athenacannon | Step 10 | expected 25 (HP 62500/2500) |
| futuretech_beehivedronecarrier | Step 52 | expected 50 (HP 125000/2500) |
| futuretech_phalanxwip | Step 18 | expected 30 (HP 75000/2500) |
| futuretech_plasmastrider | Step 96 | expected 240 (HP 240000/1000) |
| futuretech_prospectormk2 | Step 60 | expected 48 (HP 120000/2500) |
| futuretech_shotgundroid | Step 22 | expected 55 (HP 55000/1000) |
| futuretech_spyfutu | Step 10 | expected 5 (HP 5000/1000) |
| futuretech_twister | Step 50 | expected 20 (HP 50000/2500) |
| harkonnen_adp | Step 10 | expected 20 (HP 50000/2500) |
| harkonnen_buzzsaw | Step 10 | expected 28 (HP 70000/2500) |
| harkonnen_devastatormech | Step 250 | expected 220 (HP 550000/2500) |
| harkonnen_flametank | Step 10 | expected 28 (HP 70000/2500) |
| harkonnen_inkvine | Step 10 | expected 18 (HP 45000/2500) |
| harkonnen_rockettrooper | Step 10 | expected 40 (HP 40000/1000) |
| harkonnen_sardaukar | Step 50 | expected 120 (HP 120000/1000) |
| harkonnen_spiceharvester | Step 80 | expected 96 (HP 240000/2500) |
| japan_chihaheavytank | Step 104 | expected 52 (HP 130000/2500) |
| japan_coreairfield | Step 120 | expected 20 (HP 50000/2500) |
| japan_corebarracks | Step 120 | expected 20 (HP 50000/2500) |
| japan_corepowerplant | Step 120 | expected 20 (HP 50000/2500) |
| japan_coreradar | Step 120 | expected 20 (HP 50000/2500) |
| japan_corerefinery | Step 120 | expected 20 (HP 50000/2500) |
| japan_coreservicedepot | Step 120 | expected 20 (HP 50000/2500) |
| japan_coretechcenter | Step 120 | expected 20 (HP 50000/2500) |
| japan_corewarfactory | Step 120 | expected 20 (HP 50000/2500) |
| japan_hovercraftflametank | Step 96 | expected 48 (HP 120000/2500) |
| japan_zerofighter | Step 30 | expected 12 (HP 30000/2500) |
| latinsyndicate_nuketruck | Step 10 | expected 24 (HP 60000/2500) |
| latinsyndicate_yakovlev | Step 40 | expected 16 (HP 40000/2500) |
| missile_tank | Step 10 | expected 20 (HP 50000/2500) |
| naxis_bf109 | Step 30 | expected 24 (HP 60000/2500) |
| naxis_bmwbike | Step 33 | expected 9 (HP 22000/2500) |
| naxis_coneheadsknights | Step 10 | expected 20 (HP 20000/1000) |
| naxis_imperialturbotank | Step 10 | expected 33 (HP 82500/2500) |
| naxis_me262 | Step 75 | expected 30 (HP 75000/2500) |
| naxis_nokana | Step 10 | expected 180 (HP 450000/2500) |
| naxis_nop03sarubia | Step 10 | expected 25 (HP 62500/2500) |
| naxis_oldtank | Step 63 | expected 44 (HP 110000/2500) |
| naxis_shoekarn | Step 80 | expected 60 (HP 150000/2500) |
| naxis_transportzeppelin | Step 21 | expected 500 (HP 1250000/2500) |
| ordos_swarmerdrone | Step 20 | expected 8 (HP 20000/2500) |
| plymouth_tiger_emp | Step 10 | expected 24 (HP 60000/2500) |
| plymouth_tiger_esg | Step 10 | expected 24 (HP 60000/2500) |
| plymouth_tiger_microwave | Step 10 | expected 24 (HP 60000/2500) |
| plymouth_tiger_rpg | Step 10 | expected 24 (HP 60000/2500) |
| plymouth_tiger_starflare | Step 10 | expected 36 (HP 90000/2500) |
| plymouth_tiger_stickyfoam | Step 10 | expected 24 (HP 60000/2500) |
| plymouth_tiger_supernova | Step 10 | expected 48 (HP 120000/2500) |
| ra1_allies_chronotank | Step 60 | expected 30 (HP 75000/2500) |
| ra1_allies_mechanic | Step 10 | expected 8 (HP 7500/1000) |
| ra1_allies_raspy | Step 10 | expected 5 (HP 5000/1000) |
| ra1_soviets_armoredyak | Step 80 | expected 32 (HP 80000/2500) |
| ra1_soviets_nuclearyak | Step 64 | expected 26 (HP 64000/2500) |
| ra1_soviets_stalinfist | Step 120 | expected 40 (HP 100000/2500) |
| ra1_soviets_su57attackbomber | Step 52 | expected 26 (HP 65000/2500) |
| ra1_soviets_teslayak | Step 64 | expected 26 (HP 64000/2500) |
| ra1_soviets_yakscoutplane | Step 32 | expected 13 (HP 32000/2500) |
| ra2_allies_attackdog | Step 2 | expected 5 (HP 5000/1000) |
| ra2_allies_harrier | Step 72 | expected 29 (HP 72000/2500) |
| ra2_allies_ra2spy | Step 10 | expected 5 (HP 5000/1000) |
| ra2_soviets_attackdog | Step 2 | expected 5 (HP 5000/1000) |
| schwarzermond_blackbomb | Step 7 | expected 15 (HP 37500/2500) |
| schwarzermond_corruptorpiercer | Step 7 | expected 15 (HP 37500/2500) |
| schwarzermond_dieglocke | Step 50 | expected 1500 (HP 3750000/2500) |
| schwarzermond_gravitycoretank | Step 10 | expected 120 (HP 300000/2500) |
| schwarzermond_laserbeetle | Step 35 | expected 19 (HP 47500/2500) |
| schwarzermond_spacezeppelin | Step 21 | expected 540 (HP 1350000/2500) |
| steelconsortium_katytank | Step 220 | expected 110 (HP 275000/2500) |
| steelconsortium_megalodon | Step 180 | expected 450 (HP 450000/1000) |
| steelconsortium_poseidontank | Step 50 | expected 125 (HP 125000/1000) |
| steelconsortium_twister | Step 50 | expected 20 (HP 50000/2500) |
| tkm_bigshiee | Step 48 | expected 200 (HP 500000/2500) |
| tkm_dronepodtruck | Step 11 | expected 24 (HP 60000/2500) |
| tkm_flakbus | Step 10 | expected 48 (HP 120000/2500) |
| tkm_juggernaut | Step 16 | expected 36 (HP 36000/1000) |
| tkm_medictruck | Step 11 | expected 20 (HP 50000/2500) |
| tkm_quadtruck | Step 11 | expected 26 (HP 65000/2500) |
| tkm_radartruck | Step 11 | expected 30 (HP 75000/2500) |
| tkm_repairtruck | Step 11 | expected 20 (HP 50000/2500) |
| tkm_rifleman | Step 32 | expected 29 (HP 29000/1000) |
| tkm_sandmarine | Step 48 | expected 320 (HP 800000/2500) |
| tkm_stryker | Step 80 | expected 32 (HP 80000/2500) |
| tkm_t30 | Step 10 | expected 160 (HP 400000/2500) |
| tkm_t72m | Step 10 | expected 40 (HP 100000/2500) |
| tkm_technicaltank | Step 35 | expected 28 (HP 70000/2500) |
| tkm_trenchtank | Step 10 | expected 80 (HP 200000/2500) |
| tkm_trenchtruck | Step 10 | expected 40 (HP 100000/2500) |
| tkm_zaza | Step 11 | expected 50 (HP 125000/2500) |
| ts_gdi_zonetrooper | Step 10 | expected 80 (HP 80000/1000) |
| ts_nod_chameleonspy | Step 10 | expected 30 (HP 30000/1000) |
| ts_nod_subterraneanapc | Step 10 | expected 7 (HP 17500/2500) |
| wc2_humans_alleria | Step 25 | expected 50 (HP 50000/1000) |
| wc2_humans_alleria_elite | Step 35 | expected 75 (HP 75000/1000) |
| wc2_humans_danath | Step 50 | expected 150 (HP 150000/1000) |
| wc2_humans_danath_elite | Step 80 | expected 250 (HP 250000/1000) |
| wc2_humans_knight | Step 67 | expected 168 (HP 167500/1000) |
| wc2_humans_militiapeasant | Step 8 | expected 20 (HP 20000/1000) |
| wc2_orcs_hellscream | Step 50 | expected 150 (HP 150000/1000) |
| wc2_orcs_hellscream_elite | Step 80 | expected 250 (HP 250000/1000) |
| wc2_orcs_ogre | Step 80 | expected 200 (HP 200000/1000) |
| wc2_orcs_zuljin | Step 25 | expected 50 (HP 50000/1000) |
| wc2_orcs_zuljin_elite | Step 35 | expected 75 (HP 75000/1000) |
| zerg_gorekraken | Step 150 | expected 140 (HP 350000/2500) |
| zerg_ultralisk | Step 160 | expected 400 (HP 400000/1000) |


## F3 — infantry with Repairable  (10)

| actor | actual | expected |
|---|---|---|
| asianalliance_pulverizermecha | infantry declares Repairable locally |  |
| cabal_beholder | infantry declares Repairable locally |  |
| futuretech_plasmastrider | infantry declares Repairable locally |  |
| futuretech_shotgundroid | infantry declares Repairable locally |  |
| latinsyndicate_mortarbike | infantry declares Repairable locally |  |
| plymouth_spider | infantry declares Repairable locally |  |
| schwarzermond_noidmgarmor | infantry declares Repairable locally |  |
| steelconsortium_megalodon | infantry declares Repairable locally |  |
| steelconsortium_poseidontank | infantry declares Repairable locally |  |
| wc2_humans_militiapeasant | infantry declares Repairable locally |  |


_267 further infantry inherit Repairable from the infantry base template (^DefaultInfantry RepairActors: drfghosp… — unloaded Dark Reign hospitals). One template-line fix covers them all._


## F4 — upgrade shield RegenAmount ≠ 2×SelfHealing Step  (69)

| actor | actual | expected |
|---|---|---|
| asianalliance_droneminer | RegenAmount 10 | expected 20 (2 x SelfHealing 10) |
| atreides_lightinfantry | RegenAmount 10 | expected 64 (2 x SelfHealing 32) |
| atreides_rockettrooper | RegenAmount 10 | expected 20 (2 x SelfHealing 10) |
| atreides_spiceharvester | RegenAmount 10 | expected 160 (2 x SelfHealing 80) |
| corrino_lightinfantry | RegenAmount 10 | expected 64 (2 x SelfHealing 32) |
| corrino_spiceharvester | RegenAmount 10 | expected 160 (2 x SelfHealing 80) |
| corrino_trooper | RegenAmount 10 | expected 20 (2 x SelfHealing 10) |
| duelist_tank.ixian | RegenAmount 158 | expected 192 (2 x SelfHealing 96) |
| eden_cargotruck_empty | RegenAmount 10 | expected 88 (2 x SelfHealing 44) |
| forgotten_engineer | RegenAmount 25 | expected 20 (2 x SelfHealing 10) |
| forgotten_tiberiumharvester | RegenAmount 10 | expected 120 (2 x SelfHealing 60) |
| futuretech_prospector | RegenAmount 10 | expected 80 (2 x SelfHealing 40) |
| futuretech_prospectormk2 | RegenAmount 10 | expected 120 (2 x SelfHealing 60) |
| harkonnen_lightinfantry | RegenAmount 10 | expected 64 (2 x SelfHealing 32) |
| harkonnen_rockettrooper | RegenAmount 10 | expected 20 (2 x SelfHealing 10) |
| harkonnen_sardaukar | RegenAmount 10 | expected 100 (2 x SelfHealing 50) |
| harkonnen_spiceharvester | RegenAmount 10 | expected 160 (2 x SelfHealing 80) |
| heavy_inf.ixian | RegenAmount 10 | expected 64 (2 x SelfHealing 32) |
| ixian_empbomber | RegenAmount 76 | expected 88 (2 x SelfHealing 44) |
| ixian_lightinfantry | RegenAmount 10 | expected 64 (2 x SelfHealing 32) |
| ixian_rockettrooper | RegenAmount 10 | expected 24 (2 x SelfHealing 12) |
| ixian_shockinfantry | RegenAmount 10 | expected 72 (2 x SelfHealing 36) |
| ixian_storminfantry | RegenAmount 10 | expected 88 (2 x SelfHealing 44) |
| ixian_stormlasher | RegenAmount 160 | expected 20 (2 x SelfHealing 10) |
| ixian_twinrockettrooper | RegenAmount 10 | expected 48 (2 x SelfHealing 24) |
| japan_japaneseoretruck | RegenAmount 10 | expected 60 (2 x SelfHealing 30) |
| latinsyndicate_collectiontruck | RegenAmount 10 | expected 68 (2 x SelfHealing 34) |
| light_inf | RegenAmount 10 | expected 80 (2 x SelfHealing 40) |
| naxis_slave | RegenAmount 10 | expected 20 (2 x SelfHealing 10) |
| ordos_chemicaltrooper | RegenAmount 10 | expected 60 (2 x SelfHealing 30) |
| ordos_combatautoguntank | RegenAmount 48 | expected 76 (2 x SelfHealing 38) |
| ordos_contaminator | RegenAmount 10 | expected 150 (2 x SelfHealing 75) |
| ordos_facedancer | RegenAmount 10 | expected 180 (2 x SelfHealing 90) |
| ordos_heavyautoguntank | RegenAmount 96 | expected 128 (2 x SelfHealing 64) |
| ordos_leech | RegenAmount 10 | expected 40 (2 x SelfHealing 20) |
| ordos_lightinfantry | RegenAmount 10 | expected 56 (2 x SelfHealing 28) |
| ordos_rockettrooper | RegenAmount 10 | expected 24 (2 x SelfHealing 12) |
| plymouth_cargotruck_empty | RegenAmount 10 | expected 96 (2 x SelfHealing 48) |
| ra1_allies_alliedoretruck | RegenAmount 10 | expected 80 (2 x SelfHealing 40) |
| ra1_soviets_sovietheavyindustrialminer | RegenAmount 10 | expected 108 (2 x SelfHealing 54) |
| ra1_soviets_sovietoretruck | RegenAmount 10 | expected 80 (2 x SelfHealing 40) |
| ra2_allies_chronominer | RegenAmount 10 | expected 80 (2 x SelfHealing 40) |
| ra2_soviets_warminer | RegenAmount 10 | expected 100 (2 x SelfHealing 50) |
| schwarzermond_noidharvester | RegenAmount 10 | expected 60 (2 x SelfHealing 30) |
| steelconsortium_consortiumminer | RegenAmount 10 | expected 80 (2 x SelfHealing 40) |
| td_gdi_tiberiumharvester | RegenAmount 10 | expected 120 (2 x SelfHealing 60) |
| td_nod_blackhandflamer | RegenAmount 25 | expected 72 (2 x SelfHealing 36) |
| td_nod_chemicalrocketsoldier | RegenAmount 25 | expected 36 (2 x SelfHealing 18) |
| td_nod_chemicalwarrior | RegenAmount 25 | expected 96 (2 x SelfHealing 48) |
| td_nod_commando | RegenAmount 25 | expected 160 (2 x SelfHealing 80) |
| td_nod_flamethrower | RegenAmount 25 | expected 40 (2 x SelfHealing 20) |
| td_nod_lasercommando | RegenAmount 25 | expected 114 (2 x SelfHealing 57) |
| td_nod_lasertrooper | RegenAmount 25 | expected 120 (2 x SelfHealing 60) |
| td_nod_minigunner | RegenAmount 25 | expected 60 (2 x SelfHealing 30) |
| td_nod_rocketsoldier | RegenAmount 25 | expected 18 (2 x SelfHealing 9) |
| td_nod_stealthharvester | RegenAmount 10 | expected 100 (2 x SelfHealing 50) |
| td_nod_stealthsoldier | RegenAmount 25 | expected 50 (2 x SelfHealing 25) |
| td_nod_tiberiumharvester | RegenAmount 10 | expected 120 (2 x SelfHealing 60) |
| terran_scv | RegenAmount 10 | expected 36 (2 x SelfHealing 18) |
| tkm_templateharvesterraname | RegenAmount 10 | expected 80 (2 x SelfHealing 40) |
| trooper | RegenAmount 10 | expected 24 (2 x SelfHealing 12) |
| ts_gdi_engineer | RegenAmount 25 | expected 20 (2 x SelfHealing 10) |
| ts_gdi_tiberiumharvester | RegenAmount 10 | expected 120 (2 x SelfHealing 60) |
| ts_nod_engineer | RegenAmount 25 | expected 20 (2 x SelfHealing 10) |
| ts_nod_tiberiumharvester | RegenAmount 10 | expected 120 (2 x SelfHealing 60) |
| wc2_humans_militiapeasant | RegenAmount 10 | expected 16 (2 x SelfHealing 8) |
| wc2_humans_peasant | RegenAmount 10 | expected 32 (2 x SelfHealing 16) |
| wc2_orcs_peon | RegenAmount 10 | expected 32 (2 x SelfHealing 16) |
| zerg_drone | RegenAmount 10 | expected 36 (2 x SelfHealing 18) |


## F5 — defense RevealsShroud.Range ≠ weapon range  (46)

| actor | actual | expected |
|---|---|---|
| asianalliance_spitfire | RevealsShroud 14000 | weapon range 12000 |
| cabal_heavycabalobelisk | RevealsShroud 7168 | weapon range 12288 |
| cabal_plasmaturret | RevealsShroud 7168 | weapon range 6487 |
| eden_gp_emp | RevealsShroud 6144 | weapon range 5500 |
| eden_gp_laser | RevealsShroud 6144 | weapon range 6656 |
| eden_gp_railgun | RevealsShroud 6144 | weapon range 7168 |
| forgotten_brokenrattytankturret | RevealsShroud 7168 | weapon range 6574 |
| forgotten_brokenscoopertankturret | RevealsShroud 7168 | weapon range 6404 |
| forgotten_brokenwarriortankturret | RevealsShroud 7168 | weapon range 9483 |
| forgotten_machineguntower | RevealsShroud 7168 | weapon range 6272 |
| harkonnen_devastatorturret | RevealsShroud 10684 | weapon range 7168 |
| harkonnen_flameturret | RevealsShroud 7979 | weapon range 6742 |
| latinsyndicate_latinsentrygun | RevealsShroud 6666 | weapon range 7777 |
| naxis_flak88 | RevealsShroud 6666 | weapon range 13200 |
| naxis_naxibunker | RevealsShroud 6666 | weapon range 12345 |
| naxis_rifletower | RevealsShroud 6666 | weapon range 8100 |
| ordos_chemturret | RevealsShroud 7710 | weapon range 14000 |
| ordos_laserturret | RevealsShroud 7710 | weapon range 7275 |
| plymouth_gp_microwave | RevealsShroud 6144 | weapon range 6656 |
| plymouth_gp_rpg | RevealsShroud 6144 | weapon range 7168 |
| plymouth_gp_stickyfoam | RevealsShroud 6144 | weapon range 6656 |
| ra1_allies_alliedgunturret | RevealsShroud 8683 | weapon range 7685 |
| ra2_soviets_teslacoil | RevealsShroud 10000 | weapon range 8842 |
| schwarzermond_sturmcannon | RevealsShroud 6666 | weapon range 14000 |
| steelconsortium_antiairquantummissileturret | RevealsShroud 12000 | weapon range 15000 |
| steelconsortium_bfg10000 | RevealsShroud 25000 | weapon range 10238976 |
| steelconsortium_consortiumsentryturret | RevealsShroud 6666 | weapon range 15000 |
| steelconsortium_quantumcannon | RevealsShroud 8888 | weapon range 15000 |
| td_nod_samsite | RevealsShroud 12588 | weapon range 12193 |
| tkm_quadturretbunker | RevealsShroud 6720 | weapon range 11604 |
| ts_gdi_empulsecannon | RevealsShroud 7168 | weapon range 40960 |
| ts_gdi_rpgtower | RevealsShroud 7168 | weapon range 8544 |
| ts_gdi_vulcantower | RevealsShroud 7168 | weapon range 6809 |
| ts_nod_laserturret | RevealsShroud 7168 | weapon range 6992 |
| ts_nod_missilesilo | RevealsShroud 5120 | weapon range 10238976 |
| ts_nod_obeliskoflight | RevealsShroud 7168 | weapon range 10435 |
| wc2_humans_cannontower | RevealsShroud 5000 | weapon range 10500 |
| wc2_humans_guardtower | RevealsShroud 5000 | weapon range 10500 |
| wc2_humans_humanscouttower | RevealsShroud 5000 | weapon range 10500 |
| wc2_orcs_cannontower | RevealsShroud 5000 | weapon range 10500 |
| wc2_orcs_guardtower | RevealsShroud 5000 | weapon range 10500 |
| wc2_orcs_orcwatchtower | RevealsShroud 5000 | weapon range 10500 |
| yuri_psychictower | RevealsShroud 10000 | weapon range 8000 |
| zerg_creepcolony_defense | RevealsShroud 5000 | weapon range 10160 |
| zerg_sporecolony | RevealsShroud 5000 | weapon range 10160 |
| zerg_sunkencolony_defense | RevealsShroud 5000 | weapon range 10160 |


## F6 — AA/advanced defense DetectCloaked.Range ≠ weapon range/2  (22)

| actor | actual | expected |
|---|---|---|
| asianalliance_spitfire | DetectCloaked 7000 | expected 6000 (range/2) |
| cabal_heavycabalobelisk | DetectCloaked 2560 | expected 6144 (range/2) |
| forgotten_brokenscoopertankturret | DetectCloaked 3072 | expected 3202 (range/2) |
| forgotten_brokenwarriortankturret | DetectCloaked 3072 | expected 4741 (range/2) |
| forgotten_juggerflakwall | DetectCloaked 4096 | expected 5617 (range/2) |
| harkonnen_devastatorturret | DetectCloaked 5342 | expected 3584 (range/2) |
| latinsyndicate_smlturret | DetectCloaked 7000 | expected 7500 (range/2) |
| ordos_chemturret | DetectCloaked 3855 | expected 7000 (range/2) |
| ordos_laserturret | DetectCloaked 3855 | expected 3637 (range/2) |
| protoss_photoncannon | DetectCloaked 4224 | expected 4114 (range/2) |
| ra2_soviets_teslacoil | DetectCloaked 5000 | expected 4421 (range/2) |
| steelconsortium_antiairquantummissileturret | DetectCloaked 6000 | expected 7500 (range/2) |
| steelconsortium_bfg10000 | DetectCloaked 12500 | expected 5119488 (range/2) |
| steelconsortium_quantumcannon | DetectCloaked 4444 | expected 7500 (range/2) |
| td_nod_samsite | DetectCloaked 6294 | expected 6096 (range/2) |
| tkm_quadturretbunker | DetectCloaked 6000 | expected 5802 (range/2) |
| ts_gdi_empulsecannon | DetectCloaked missing | expected 20480 |
| ts_gdi_rpgtower | DetectCloaked 3072 | expected 4272 (range/2) |
| ts_gdi_samtower | DetectCloaked 4096 | expected 6220 (range/2) |
| ts_nod_obeliskoflight | DetectCloaked 5120 | expected 5217 (range/2) |
| ts_nod_samsite | DetectCloaked 4096 | expected 6588 (range/2) |
| yuri_psychictower | DetectCloaked 5000 | expected 4000 (range/2) |


## F7 — defense Power.Amount ≠ -Cost/20  (99)

| actor | actual | expected |
|---|---|---|
| asianalliance_advancedcommunicationcenter | Power -200 | expected -500 (-Cost/20) |
| asianalliance_asiansentryflamer | Power -25 | expected -40 (-Cost/20) |
| asianalliance_chaosstorminductor | Power -200 | expected -250 (-Cost/20) |
| asianalliance_concretebarrier | Power missing | expected -10 |
| atreides_palace | Power -200 | expected -500 (-Cost/20) |
| atreides_storagesilo | Power -10 | expected -7 (-Cost/20) |
| brik | Power missing | expected -10 |
| corrino_storagesilo | Power -10 | expected -7 (-Cost/20) |
| cycl | Power missing | expected -3 |
| eden_gp_emp | Power -10 | expected -30 (-Cost/20) |
| eden_gp_laser | Power -10 | expected -30 (-Cost/20) |
| eden_gp_railgun | Power -10 | expected -30 (-Cost/20) |
| eden_light_tower | Power -5 | expected -2 (-Cost/20) |
| eden_mine_common | Power -50 | expected -40 (-Cost/20) |
| eden_storage_common | Power -10 | expected -5 (-Cost/20) |
| fenc | Power missing | expected -1 |
| forgotten_brokenrattytankturret | Power 0 | expected -40 (-Cost/20) |
| forgotten_brokenscoopertankturret | Power 0 | expected -87 (-Cost/20) |
| forgotten_brokenwarriortankturret | Power 0 | expected -75 (-Cost/20) |
| forgotten_juggerflakwall | Power -40 | expected -50 (-Cost/20) |
| forgotten_machineguntower | Power -20 | expected -30 (-Cost/20) |
| forgotten_silo | Power -10 | expected -15 (-Cost/20) |
| forgotten_veinhole | Power -150 | expected -500 (-Cost/20) |
| harkonnen_flameturret | Power -50 | expected -60 (-Cost/20) |
| harkonnen_palace | Power -200 | expected -500 (-Cost/20) |
| harkonnen_storagesilo | Power -10 | expected -7 (-Cost/20) |
| ixian_munitionssilo | Power -10 | expected -25 (-Cost/20) |
| ixian_storagesilo | Power -10 | expected -7 (-Cost/20) |
| ixian_supercomputer | Power -200 | expected -500 (-Cost/20) |
| japan_japaneseshrine | Power -200 | expected -500 (-Cost/20) |
| latinsyndicate_bunkertower | Power missing | expected -30 |
| latinsyndicate_latinsentrygun | Power -30 | expected -35 (-Cost/20) |
| latinsyndicate_topolsilo | Power -200 | expected -500 (-Cost/20) |
| naxis_flak88 | Power -40 | expected -60 (-Cost/20) |
| naxis_naxibunker | Power missing | expected -50 |
| naxis_naxirocketsilo | Power -200 | expected -500 (-Cost/20) |
| naxis_rifletower | Power -25 | expected -32 (-Cost/20) |
| ordos_chemturret | Power -55 | expected -60 (-Cost/20) |
| ordos_storagesilo | Power -10 | expected -7 (-Cost/20) |
| plymouth_gp_microwave | Power -10 | expected -30 (-Cost/20) |
| plymouth_gp_rpg | Power -10 | expected -30 (-Cost/20) |
| plymouth_gp_stickyfoam | Power -10 | expected -30 (-Cost/20) |
| plymouth_light_tower | Power -5 | expected -2 (-Cost/20) |
| plymouth_mine_common | Power -50 | expected -40 (-Cost/20) |
| plymouth_storage_common | Power -10 | expected -5 (-Cost/20) |
| ra1_allies_chronosphere | Power -200 | expected -500 (-Cost/20) |
| ra1_oresilo | Power -10 | expected -7 (-Cost/20) |
| ra1_soviets_ironcurtain | Power -200 | expected -250 (-Cost/20) |
| ra1_soviets_sovietmissilesilo | Power -200 | expected -500 (-Cost/20) |
| ra2_allies_chronosphere | Power -200 | expected -250 (-Cost/20) |
| ra2_allies_concretebarrier | Power missing | expected -10 |
| ra2_allies_grandcannon | Power -200 | expected -250 (-Cost/20) |
| ra2_allies_weathercontrolcenter | Power -200 | expected -500 (-Cost/20) |
| ra2_awall | Power missing | expected -10 |
| ra2_soviets_battlebunker | Power missing | expected -40 |
| ra2_soviets_concretebarrier | Power missing | expected -10 |
| ra2_soviets_ironcurtain | Power -200 | expected -250 (-Cost/20) |
| ra2_soviets_nuclearmissilesilo | Power -200 | expected -500 (-Cost/20) |
| ra2_swall | Power missing | expected -10 |
| ra2_ywall | Power missing | expected -10 |
| sbag | Power missing | expected -2 |
| schwarzermond_meteortractionray | Power -200 | expected -500 (-Cost/20) |
| schwarzermond_sturmcannon | Power -50 | expected -60 (-Cost/20) |
| silo | Power -10 | expected -5 (-Cost/20) |
| steelconsortium_antiairquantummissileturret | Power -45 | expected -50 (-Cost/20) |
| steelconsortium_bfg10000 | Power -1000 | expected -500 (-Cost/20) |
| steelconsortium_orbitalcannonactivator | Power -200 | expected -500 (-Cost/20) |
| terran_bunker | Power 0 | expected -60 (-Cost/20) |
| terran_missilesilo | Power 0 | expected -500 (-Cost/20) |
| tkm_bunker | Power missing | expected -30 |
| tkm_quadturretbunker | Power -25 | expected -45 (-Cost/20) |
| tkm_tankturretbunker | Power -25 | expected -40 (-Cost/20) |
| ts_gdi_rpgtower | Power -20 | expected -70 (-Cost/20) |
| ts_gdi_samtower | Power -30 | expected -40 (-Cost/20) |
| ts_gdi_silo | Power -10 | expected -7 (-Cost/20) |
| ts_gdi_vulcantower | Power -20 | expected -30 (-Cost/20) |
| ts_nod_laserfence | Power -25 | expected -10 (-Cost/20) |
| ts_nod_laserturret | Power -20 | expected -40 (-Cost/20) |
| ts_nod_missilesilo | Power -150 | expected -500 (-Cost/20) |
| ts_nod_obeliskoflight | Power -100 | expected -110 (-Cost/20) |
| ts_nod_samsite | Power -30 | expected -40 (-Cost/20) |
| ts_nod_silo | Power -10 | expected -7 (-Cost/20) |
| ts_nod_stealthgenerator | Power -150 | expected -125 (-Cost/20) |
| wall | Power missing | expected -6 |
| wc2_humans_cannontower | Power missing | expected -75 |
| wc2_humans_guardtower | Power missing | expected -75 |
| wc2_humans_humanscouttower | Power missing | expected -60 |
| wc2_humans_wall | Power missing | expected -15 |
| wc2_orcs_cannontower | Power missing | expected -80 |
| wc2_orcs_guardtower | Power missing | expected -80 |
| wc2_orcs_orcwatchtower | Power missing | expected -60 |
| wc2_orcs_wall | Power missing | expected -15 |
| yuri_concretebarrier | Power missing | expected -10 |
| yuri_geneticmutator | Power -200 | expected -250 (-Cost/20) |
| yuri_psychicdominator | Power -200 | expected -500 (-Cost/20) |
| yuri_tankbunker | Power missing | expected -50 |
| zerg_creepcolony_defense | Power missing | expected -50 |
| zerg_sporecolony | Power missing | expected -62 |
| zerg_sunkencolony_defense | Power missing | expected -62 |


## F8 — vehicle TurnSpeed ≠ Speed/5  (6)

| actor | actual | expected |
|---|---|---|
| atreides_apc | TurnSpeed 16 (Speed 65) | expected 13 = Speed/5 |
| atreides_siegetank | TurnSpeed 48 (Speed 43) | expected 9 = Speed/5 |
| corrino_apc | TurnSpeed 40 (Speed 100) | expected 20 = Speed/5 |
| corrino_bmp | TurnSpeed 40 (Speed 70) | expected 14 = Speed/5 |
| corrino_buggy | TurnSpeed 60 (Speed 85) | expected 17 = Speed/5 |
| harkonnen_adp | TurnSpeed 20 (Speed 64) | expected 13 = Speed/5 |


## F9 — Turreted.TurnSpeed ≠ Mobile.TurnSpeed  (2)

| actor | actual | expected |
|---|---|---|
| atreides_apc | Turreted 48 vs Mobile 16 | must match |
| harkonnen_adp | Turreted 48 vs Mobile 20 | must match |


## F10 — turretless TurnSpeed ≠ 2×Speed/5 (artillery: Speed/5)  (10)

| actor | actual | expected |
|---|---|---|
| atreides_missiletank | TurnSpeed 80 (Speed 64) | expected 26 = 2 x Speed/5 (turretless) |
| atreides_repairtank | TurnSpeed 16 (Speed 50) | expected 20 = 2 x Speed/5 (turretless) |
| atreides_sandbike | TurnSpeed 24 (Speed 90) | expected 36 = 2 x Speed/5 (turretless) |
| combat_tank.harkonnen | TurnSpeed 13 (Speed 65) | expected 26 = 2 x Speed/5 (turretless) |
| corrino_missiletank | TurnSpeed 80 (Speed 64) | expected 26 = 2 x Speed/5 (turretless) |
| corrino_siegetank | TurnSpeed 4 (Speed 56) | expected 22 = 2 x Speed/5 (turretless) |
| devastator | TurnSpeed 48 (Speed 33) | expected 14 = 2 x Speed/5 (turretless) |
| harkonnen_buzzsaw | TurnSpeed 48 (Speed 43) | expected 18 = 2 x Speed/5 (turretless) |
| harkonnen_flametank | TurnSpeed 13 (Speed 65) | expected 26 = 2 x Speed/5 (turretless) |
| harkonnen_inkvine | TurnSpeed 48 (Speed 43) | expected 18 = 2 x Speed/5 (turretless) |


## F11 — turreted artillery missing/incorrect firing-slow (Archer pattern)  (19)

| actor | actual | expected |
|---|---|---|
| atreides_siegetank | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| eden_lynx_railgun | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| eden_lynx_thorshammer | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| eden_tiger_railgun | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| eden_tiger_thorshammer | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| forgotten_warriortank | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| futuretech_beehivedronecarrier | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| futuretech_energizer | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| ixian_stormraider | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| japan_nanodronebuggy | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| ra1_soviets_heatraytank | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| ra1_soviets_teslatank | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| ra1_soviets_v1rockettruck | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| ra2_allies_prismtank | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| ra2_soviets_teslatank | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| schwarzermond_crystaltank | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| td_nod_ssmlauncher | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| yuri_magnetron | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |
| zerg_lurker | firing-slow pattern missing | see gdiarcher (GrantConditionOnAttack + 50% multipliers) |


## F12 — anti-air defense not gated by the faction's radar tier  (0)

_none found_


## F13 — advanced defense not gated by the faction's tech tier  (4)

| actor | actual | expected |
|---|---|---|
| ordos: ordos_autogunturret | prereqs: ordos_barracks, ordos_constructionyard (gate 2, radar tier 3) | DEFERRED: valid, but faction's only pre-radar defense — add a Tier-1 defense before regating |
| ordos: ordos_chemturret | prereqs: ordos_barracks, ordos_constructionyard (gate 2, radar tier 3) | DEFERRED: valid, but faction's only pre-radar defense — add a Tier-1 defense before regating |
| ordos: ordos_artilleryplatform | prereqs: ordos_barracks, ordos_constructionyard (gate 2, radar tier 3) | DEFERRED: valid, but faction's only pre-radar defense — add a Tier-1 defense before regating |
| schwarzermond: schwarzermond_lasertower | prereqs: schwarzermond_barracks, schwarzermond_constructionyard (gate 2, radar tier 3) | DEFERRED: valid, but faction's only pre-radar defense — add a Tier-1 defense before regating |


## F14 — StartingUnits referencing nonexistent actors (crash class)  (0)

_none found_


## F15 — Light Support composition (Tier-1 only, ~2000, 5:1 inf:veh)  (71)

| actor | actual | expected |
|---|---|---|
| td_gdi: defaultgdia | total cost 1500 | target ~2000 (±15%) |
| td_gdi: defaultgdia | e3 (cost 300) x2 vs e1 (cost 100) x1 | pricier units must not outnumber cheaper ones |
| td_nod: defaultnoda | total cost 1500 | target ~2000 (±15%) |
| td_nod: defaultnoda | td_nod_buggy | light support must be Tier-1 only (producer-building prereqs only) |
| ra1_allies: defaultallies | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| ra1_soviets: defaultsoviet | total cost 3000 | target ~2000 (±15%) |
| ra1_soviets: defaultsoviet | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| japan: defaultjapan | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| ts_gdi: defaulttsgdi | total cost 2460 | target ~2000 (±15%) |
| ts_gdi: defaulttsgdi | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| ts_nod: defaulttsnod | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| forgotten: defaultforgotten | total cost 3778 | target ~2000 (±15%) |
| forgotten: defaultforgotten | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| forgotten: defaultforgotten | forgotten_mutantsergeant (cost 1154) x2 vs forgotten_mutantsoldier (cost 250) x1 | pricier units must not outnumber cheaper ones |
| forgotten: defaultforgotten | forgotten_mutantsergeant (cost 1154) x2 vs forgotten_raidercar (cost 300) x1 | pricier units must not outnumber cheaper ones |
| forgotten: defaultforgotten | forgotten_mutantsergeant (cost 1154) x2 vs forgotten_rattytank (cost 600) x1 | pricier units must not outnumber cheaper ones |
| forgotten: defaultforgotten | forgotten_mutantsergeant | light support must be Tier-1 only (producer-building prereqs only) |
| ra2_allies: defaultra2allies | total cost 2650 | target ~2000 (±15%) |
| ra2_allies: defaultra2allies | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| ra2_soviets: defaultra2soviets | total cost 2882 | target ~2000 (±15%) |
| ra2_soviets: defaultra2soviets | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| yuri: defaultyuri | total cost 3350 | target ~2000 (±15%) |
| yuri: defaultyuri | 6 infantry : 2 vehicles | want ~5 infantry per vehicle |
| yuri: defaultyuri | yuri_brute (cost 400) x2 vs yrslav (cost 250) x1 | pricier units must not outnumber cheaper ones |
| asianalliance: defaultasianalliance | total cost 2680 | target ~2000 (±15%) |
| asianalliance: defaultasianalliance | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| steelconsortium: defaultconsortium | total cost 4579 | target ~2000 (±15%) |
| steelconsortium: defaultconsortium | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| steelconsortium: defaultconsortium | steelconsortium_quantummissiletrooper (cost 1150) x2 vs steelconsortium_manta (cost 850) x1 | pricier units must not outnumber cheaper ones |
| steelconsortium: defaultconsortium | steelconsortium_quantummissiletrooper (cost 1150) x2 vs steelconsortium_hammerheadartillerytank (cost 1000) x1 | pricier units must not outnumber cheaper ones |
| steelconsortium: defaultconsortium | steelconsortium_quantummissiletrooper | light support must be Tier-1 only (producer-building prereqs only) |
| latinsyndicate: defaultsyndicate | total cost 8990 | target ~2000 (±15%) |
| latinsyndicate: defaultsyndicate | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| latinsyndicate: defaultsyndicate | latinsyndicate_freedomfighter (cost 3000) x2 vs wirbelwind.nax (cost 1800) x1 | pricier units must not outnumber cheaper ones |
| latinsyndicate: defaultsyndicate | latinsyndicate_freedomfighter (cost 3000) x2 vs tiger.nax (cost 800) x1 | pricier units must not outnumber cheaper ones |
| latinsyndicate: defaultsyndicate | latinsyndicate_freedomfighter | light support must be Tier-1 only (producer-building prereqs only) |
| naxis: defaultnaxis | total cost 3380 | target ~2000 (±15%) |
| naxis: defaultnaxis | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| naxis: defaultnaxis | naxis_sssoldier | light support must be Tier-1 only (producer-building prereqs only) |
| schwarzermond: defaultschwarzermond | total cost 3850 | target ~2000 (±15%) |
| schwarzermond: defaultschwarzermond | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| schwarzermond: defaultschwarzermond | schwarzermond_lunarsoldier (cost 500) x3 vs schwarzermond_lunarrocket (cost 350) x2 | pricier units must not outnumber cheaper ones |
| futuretech: defaultfuturetech | total cost 3050 | target ~2000 (±15%) |
| futuretech: defaultfuturetech | 0 infantry : 7 vehicles | want ~5 infantry per vehicle |
| futuretech: defaultfuturetech | futuretech_cannondroid, futuretech_missiledroid, futuretech_scoutdroid | light support must be Tier-1 only (producer-building prereqs only) |
| tkm: defaulttstkm | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| ordos: ordos_L | total cost 3060 | target ~2000 (±15%) |
| ixian: ixian_L | total cost 3300 | target ~2000 (±15%) |
| ixian: ixian_L | 5 infantry : 2 vehicles | want ~5 infantry per vehicle |
| atreides: atreides_L | trooper (cost 300) x2 vs atreides_rockettrooper (cost 200) x1 | pricier units must not outnumber cheaper ones |
| harkonnen: harkonnen_L | total cost 1100 | target ~2000 (±15%) |
| harkonnen: harkonnen_L | 5 infantry : 0 vehicles | light set should include a vehicle |
| harkonnen: harkonnen_L | trooper (cost 300) x2 vs harkonnen_rockettrooper (cost 200) x1 | pricier units must not outnumber cheaper ones |
| corrino: corrino_L | total cost 1500 | target ~2000 (±15%) |
| corrino: corrino_L | 5 infantry : 0 vehicles | light set should include a vehicle |
| terran: defaultterran | total cost 4067 | target ~2000 (±15%) |
| terran: defaultterran | terran_marine (cost 689) x3 vs terran_firebat (cost 500) x1 | pricier units must not outnumber cheaper ones |
| terran: defaultterran | terran_marine (cost 689) x3 vs terran_medic (cost 600) x1 | pricier units must not outnumber cheaper ones |
| protoss: defaultprotoss | total cost 1500 | target ~2000 (±15%) |
| protoss: defaultprotoss | 1 infantry : 1 vehicles | want ~5 infantry per vehicle |
| protoss: defaultprotoss | protoss_zealot | light support must be Tier-1 only (producer-building prereqs only) |
| zerg: defaultzerg | total cost 7928 | target ~2000 (±15%) |
| zerg: defaultzerg | zerg_hydralisk (cost 3314) x2 vs zerg_overlord (cost 500) x1 | pricier units must not outnumber cheaper ones |
| plymouth: defaultplymouth | total cost 3050 | target ~2000 (±15%) |
| plymouth: defaultplymouth | 0 infantry : 6 vehicles | want ~5 infantry per vehicle |
| plymouth: defaultplymouth | plymouth_lynx_microwave (cost 500) x3 vs plymouth_scout (cost 350) x1 | pricier units must not outnumber cheaper ones |
| plymouth: defaultplymouth | plymouth_lynx_rpg (cost 600) x2 vs plymouth_scout (cost 350) x1 | pricier units must not outnumber cheaper ones |
| eden: defaulteden | total cost 4350 | target ~2000 (±15%) |
| eden: defaulteden | 0 infantry : 6 vehicles | want ~5 infantry per vehicle |
| eden: defaulteden | eden_lynx_laser (cost 750) x3 vs eden_scout (cost 300) x1 | pricier units must not outnumber cheaper ones |
| eden: defaulteden | eden_lynx_railgun (cost 900) x2 vs eden_scout (cost 300) x1 | pricier units must not outnumber cheaper ones |


## F16 — Heavy Support composition (all tiers, ~10000, 5:1 inf:veh)  (115)

| actor | actual | expected |
|---|---|---|
| td_gdi: heavygdia | total cost 3200 | target ~10000 (±15%) |
| td_gdi: heavygdia | 6 infantry : 3 vehicles | want ~5 infantry per vehicle |
| td_gdi: heavygdia | td_gdi_battletank (cost 900) x2 vs td_gdi_humvee (cost 400) x1 | pricier units must not outnumber cheaper ones |
| td_gdi: heavygdia | all units are Tier 1 | heavy support should mix all tiers |
| td_gdi: heavygdib | total cost 3800 | target ~10000 (±15%) |
| td_gdi: heavygdib | all units are Tier 1 | heavy support should mix all tiers |
| td_nod: heavynoda | total cost 3000 | target ~10000 (±15%) |
| td_nod: heavynoda | 6 infantry : 3 vehicles | want ~5 infantry per vehicle |
| td_nod: heavynodb | total cost 3000 | target ~10000 (±15%) |
| ra1_allies: heavyallies | total cost 3800 | target ~10000 (±15%) |
| ra1_allies: heavyallies | 5 infantry : 5 vehicles | want ~5 infantry per vehicle |
| ra1_allies: heavyallies | ra1_allies_alliedmediumtank (cost 700) x3 vs ra1_allies_alliedrocketsoldier (cost 300) x2 | pricier units must not outnumber cheaper ones |
| ra1_allies: heavyallies | ra1_allies_alliedmediumtank (cost 700) x3 vs ra1_allies_ranger (cost 300) x1 | pricier units must not outnumber cheaper ones |
| ra1_allies: heavyallies | ra1_allies_alliedmediumtank (cost 700) x3 vs ra1_allies_alliedlighttank (cost 500) x1 | pricier units must not outnumber cheaper ones |
| ra1_allies: heavyallies | all units are Tier 1 | heavy support should mix all tiers |
| ra1_soviets: heavysoviet | total cost 5000 | target ~10000 (±15%) |
| ra1_soviets: heavysoviet | 5 infantry : 4 vehicles | want ~5 infantry per vehicle |
| ra1_soviets: heavysoviet | ra1_soviets_sovietheavytank (cost 1000) x2 vs ra1_soviets_flaktruck (cost 800) x1 | pricier units must not outnumber cheaper ones |
| ra1_soviets: heavysoviet | all units are Tier 1 | heavy support should mix all tiers |
| japan: heavyjapan | total cost 6100 | target ~10000 (±15%) |
| japan: heavyjapan | 5 infantry : 6 vehicles | want ~5 infantry per vehicle |
| japan: heavyjapan | japan_igomediumtank (cost 800) x2 vs japan_scoutcar (cost 300) x1 | pricier units must not outnumber cheaper ones |
| japan: heavyjapan | japan_grenadebuggy (cost 900) x2 vs japan_scoutcar (cost 300) x1 | pricier units must not outnumber cheaper ones |
| japan: heavyjapan | all units are Tier 1 | heavy support should mix all tiers |
| ts_gdi: heavytsgdi | total cost 5310 | target ~10000 (±15%) |
| ts_gdi: heavytsgdi | 5 infantry : 5 vehicles | want ~5 infantry per vehicle |
| ts_gdi: heavytsgdi | ts_gdi_titan (cost 950) x4 vs tse1 (cost 120) x3 | pricier units must not outnumber cheaper ones |
| ts_gdi: heavytsgdi | ts_gdi_titan (cost 950) x4 vs ts_gdi_discthrower (cost 300) x2 | pricier units must not outnumber cheaper ones |
| ts_gdi: heavytsgdi | ts_gdi_titan (cost 950) x4 vs ts_gdi_wolverine (cost 550) x1 | pricier units must not outnumber cheaper ones |
| ts_gdi: heavytsgdi | all units are Tier 1 | heavy support should mix all tiers |
| ts_nod: heavytsnod | total cost 4610 | target ~10000 (±15%) |
| ts_nod: heavytsnod | 5 infantry : 5 vehicles | want ~5 infantry per vehicle |
| ts_nod: heavytsnod | ts_nod_ticktank (cost 800) x4 vs tse1 (cost 120) x3 | pricier units must not outnumber cheaper ones |
| ts_nod: heavytsnod | ts_nod_ticktank (cost 800) x4 vs ts_nod_rocketinfantry (cost 300) x2 | pricier units must not outnumber cheaper ones |
| ts_nod: heavytsnod | ts_nod_ticktank (cost 800) x4 vs ts_nod_attackbuggy (cost 450) x1 | pricier units must not outnumber cheaper ones |
| ts_nod: heavytsnod | all units are Tier 1 | heavy support should mix all tiers |
| forgotten: heavyforgotten | 5 infantry : 5 vehicles | want ~5 infantry per vehicle |
| forgotten: heavyforgotten | forgotten_mutantsergeant (cost 1154) x2 vs forgotten_mutantsoldier (cost 250) x1 | pricier units must not outnumber cheaper ones |
| forgotten: heavyforgotten | forgotten_mutantsergeant (cost 1154) x2 vs forgotten_raidercar (cost 300) x1 | pricier units must not outnumber cheaper ones |
| forgotten: heavyforgotten | forgotten_mutantsergeant (cost 1154) x2 vs forgotten_rattytank (cost 600) x1 | pricier units must not outnumber cheaper ones |
| forgotten: heavyforgotten | forgotten_warriortank (cost 2000) x3 vs forgotten_mutant (cost 160) x2 | pricier units must not outnumber cheaper ones |
| forgotten: heavyforgotten | forgotten_warriortank (cost 2000) x3 vs forgotten_mutantsoldier (cost 250) x1 | pricier units must not outnumber cheaper ones |
| forgotten: heavyforgotten | forgotten_warriortank (cost 2000) x3 vs forgotten_mutantsergeant (cost 1154) x2 | pricier units must not outnumber cheaper ones |
| forgotten: heavyforgotten | forgotten_warriortank (cost 2000) x3 vs forgotten_raidercar (cost 300) x1 | pricier units must not outnumber cheaper ones |
| forgotten: heavyforgotten | forgotten_warriortank (cost 2000) x3 vs forgotten_rattytank (cost 600) x1 | pricier units must not outnumber cheaper ones |
| ra2_allies: heavyra2allies | total cost 6150 | target ~10000 (±15%) |
| ra2_allies: heavyra2allies | 5 infantry : 6 vehicles | want ~5 infantry per vehicle |
| ra2_allies: heavyra2allies | ra2_allies_grizzlytank (cost 750) x3 vs ra2_allies_guardiangi (cost 400) x2 | pricier units must not outnumber cheaper ones |
| ra2_allies: heavyra2allies | ra2_allies_grizzlytank (cost 750) x3 vs ra2_allies_ifv (cost 500) x2 | pricier units must not outnumber cheaper ones |
| ra2_allies: heavyra2allies | all units are Tier 1 | heavy support should mix all tiers |
| ra2_soviets: heavyra2soviets | total cost 5482 | target ~10000 (±15%) |
| ra2_soviets: heavyra2soviets | 5 infantry : 4 vehicles | want ~5 infantry per vehicle |
| yuri: heavyyuri | total cost 6250 | target ~10000 (±15%) |
| yuri: heavyyuri | 6 infantry : 6 vehicles | want ~5 infantry per vehicle |
| yuri: heavyyuri | yuri_brute (cost 400) x2 vs yrslav (cost 250) x1 | pricier units must not outnumber cheaper ones |
| yuri: heavyyuri | yuri_gatlingtank (cost 1100) x2 vs yrslav (cost 250) x1 | pricier units must not outnumber cheaper ones |
| yuri: heavyyuri | yuri_lashertank (cost 600) x4 vs yuri_initiate (cost 200) x3 | pricier units must not outnumber cheaper ones |
| yuri: heavyyuri | yuri_lashertank (cost 600) x4 vs yuri_brute (cost 400) x2 | pricier units must not outnumber cheaper ones |
| yuri: heavyyuri | yuri_lashertank (cost 600) x4 vs yrslav (cost 250) x1 | pricier units must not outnumber cheaper ones |
| yuri: heavyyuri | all units are Tier 1 | heavy support should mix all tiers |
| asianalliance: heavyasianalliance | total cost 7680 | target ~10000 (±15%) |
| asianalliance: heavyasianalliance | 5 infantry : 6 vehicles | want ~5 infantry per vehicle |
| asianalliance: heavyasianalliance | asianalliance_lynxtank (cost 850) x3 vs asianalliance_asiantankkiller (cost 300) x2 | pricier units must not outnumber cheaper ones |
| steelconsortium: heavyconsortium | 5 infantry : 6 vehicles | want ~5 infantry per vehicle |
| steelconsortium: heavyconsortium | steelconsortium_quantumtank (cost 1600) x4 vs steelconsortium_clonetrooper (cost 143) x3 | pricier units must not outnumber cheaper ones |
| steelconsortium: heavyconsortium | steelconsortium_quantumtank (cost 1600) x4 vs steelconsortium_quantummissiletrooper (cost 1150) x2 | pricier units must not outnumber cheaper ones |
| steelconsortium: heavyconsortium | steelconsortium_quantumtank (cost 1600) x4 vs steelconsortium_manta (cost 850) x2 | pricier units must not outnumber cheaper ones |
| latinsyndicate: heavysyndicate | total cost 14790 | target ~10000 (±15%) |
| latinsyndicate: heavysyndicate | 5 infantry : 6 vehicles | want ~5 infantry per vehicle |
| latinsyndicate: heavysyndicate | latinsyndicate_freedomfighter (cost 3000) x2 vs ptnk.asian (cost 2400) x1 | pricier units must not outnumber cheaper ones |
| naxis: heavynaxis | 5 infantry : 6 vehicles | want ~5 infantry per vehicle |
| naxis: heavynaxis | wirbelwind.nax (cost 1800) x3 vs naxis_sssoldier (cost 240) x2 | pricier units must not outnumber cheaper ones |
| naxis: heavynaxis | tiger.nax (cost 800) x3 vs naxis_sssoldier (cost 240) x2 | pricier units must not outnumber cheaper ones |
| schwarzermond: heavyschwarzermond | total cost 6400 | target ~10000 (±15%) |
| schwarzermond: heavyschwarzermond | 5 infantry : 6 vehicles | want ~5 infantry per vehicle |
| schwarzermond: heavyschwarzermond | schwarzermond_laserbeetle (cost 700) x3 vs schwarzermond_lunarsoldier (cost 500) x2 | pricier units must not outnumber cheaper ones |
| schwarzermond: heavyschwarzermond | schwarzermond_laserbeetle (cost 700) x3 vs schwarzermond_lunarpanzer (cost 650) x2 | pricier units must not outnumber cheaper ones |
| schwarzermond: heavyschwarzermond | all units are Tier 1 | heavy support should mix all tiers |
| futuretech: heavyfuturetech | total cost 5325 | target ~10000 (±15%) |
| futuretech: heavyfuturetech | 0 infantry : 11 vehicles | want ~5 infantry per vehicle |
| futuretech: heavyfuturetech | futuretech_cannondroid (cost 525) x5 vs futuretech_scoutdroid (cost 200) x3 | pricier units must not outnumber cheaper ones |
| tkm: heavytstkm | total cost 3060 | target ~10000 (±15%) |
| tkm: heavytstkm | 5 infantry : 5 vehicles | want ~5 infantry per vehicle |
| tkm: heavytstkm | tkm_technical (cost 400) x4 vs tkm_rifleman (cost 120) x3 | pricier units must not outnumber cheaper ones |
| tkm: heavytstkm | tkm_technical (cost 400) x4 vs tkm_rocketeer (cost 200) x2 | pricier units must not outnumber cheaper ones |
| tkm: heavytstkm | all units are Tier 1 | heavy support should mix all tiers |
| ordos: ordos_h | total cost 6510 | target ~10000 (±15%) |
| ordos: ordos_h | 6 infantry : 3 vehicles | want ~5 infantry per vehicle |
| ordos: ordos_h | all units are Tier 1 | heavy support should mix all tiers |
| ixian: ixian_h | total cost 7100 | target ~10000 (±15%) |
| ixian: ixian_h | 5 infantry : 4 vehicles | want ~5 infantry per vehicle |
| atreides: atreides_h | total cost 2600 | target ~10000 (±15%) |
| atreides: atreides_h | 7 infantry : 2 vehicles | want ~5 infantry per vehicle |
| harkonnen: harkonnen_h | total cost 2650 | target ~10000 (±15%) |
| harkonnen: harkonnen_h | 6 infantry : 2 vehicles | want ~5 infantry per vehicle |
| corrino: corrino_h | total cost 3300 | target ~10000 (±15%) |
| corrino: corrino_h | 6 infantry : 2 vehicles | want ~5 infantry per vehicle |
| terran: heavyterran | 4 infantry : 3 vehicles | want ~5 infantry per vehicle |
| terran: heavyterran | terran_marine (cost 689) x2 vs terran_firebat (cost 500) x1 | pricier units must not outnumber cheaper ones |
| terran: heavyterran | terran_marine (cost 689) x2 vs terran_medic (cost 600) x1 | pricier units must not outnumber cheaper ones |
| terran: heavyterran | terran_siegetank (cost 2800) x2 vs terran_firebat (cost 500) x1 | pricier units must not outnumber cheaper ones |
| terran: heavyterran | terran_siegetank (cost 2800) x2 vs terran_medic (cost 600) x1 | pricier units must not outnumber cheaper ones |
| terran: heavyterran | terran_siegetank (cost 2800) x2 vs terran_vulture (cost 900) x1 | pricier units must not outnumber cheaper ones |
| protoss: heavyprotoss | total cost 3000 | target ~10000 (±15%) |
| protoss: heavyprotoss | 2 infantry : 2 vehicles | want ~5 infantry per vehicle |
| zerg: heavyzerg | total cost 15356 | target ~10000 (±15%) |
| zerg: heavyzerg | zerg_hydralisk (cost 3314) x4 vs zerg_overlord (cost 500) x1 | pricier units must not outnumber cheaper ones |
| plymouth: heavyplymouth | total cost 3650 | target ~10000 (±15%) |
| plymouth: heavyplymouth | 0 infantry : 7 vehicles | want ~5 infantry per vehicle |
| plymouth: heavyplymouth | plymouth_lynx_microwave (cost 500) x3 vs plymouth_scout (cost 350) x1 | pricier units must not outnumber cheaper ones |
| plymouth: heavyplymouth | plymouth_lynx_rpg (cost 600) x3 vs plymouth_scout (cost 350) x1 | pricier units must not outnumber cheaper ones |
| eden: heavyeden | total cost 5250 | target ~10000 (±15%) |
| eden: heavyeden | 0 infantry : 7 vehicles | want ~5 infantry per vehicle |
| eden: heavyeden | eden_lynx_laser (cost 750) x3 vs eden_scout (cost 300) x1 | pricier units must not outnumber cheaper ones |
| eden: heavyeden | eden_lynx_railgun (cost 900) x3 vs eden_scout (cost 300) x1 | pricier units must not outnumber cheaper ones |


## F17 — fighter/bomber TurnSpeed ≠ Speed/15 (frontal: 2×)  (0)

_none found_


## F18 — weapons targeting Air whose gameplay payload can't hit Air  (0)

_none found_


## F19 — helicopter/spaceship TurnSpeed ≠ Speed/5  (0)

_none found_


## F20 — AA support vehicle: air range ≠ 1.5 × ground range  (3)

| actor | actual | expected |
|---|---|---|
| latinsyndicate_latinapc | AA range 9610 vs ground 6740 | expected 10110 = 1.5 x ground range |
| ordos_laboratorycrawler | AA range 6500 vs ground 6500 | expected 9750 = 1.5 x ground range |
| protoss_analogue | AA range 2000 vs ground 1500 | expected 2250 = 1.5 x ground range |


## F22 — promotion tech gate ≠ unlocked unit's tech gate  (18)

| actor | actual | expected |
|---|---|---|
| futuretech: futuretech_cryolegionnaire | unit tech tier 7 | promotion futuretech_promotion_cryolegionnaire tier 0 — must match |
| futuretech: futuretech_futuretank | unit tech tier 7 | promotion futuretech_promotion_futuretank tier 0 — must match |
| futuretech: futuretech_harbingergunship | unit tech tier 7 | promotion futuretech_promotion_harbingergunship tier 0 — must match |
| ixian: heavy_rocket_raider.ixian | unit tech tier 5 | promotion ixian_promotion_heavyixraider tier 0 — must match |
| ixian: ixian_ixprojector | unit tech tier 5 | promotion ixian_promotion_ixprojector tier 0 — must match |
| ixian: ixian_ixsiegetank | unit tech tier 5 | promotion ixian_promotion_ixsiegetank tier 0 — must match |
| ixian: ixian_neocymek | unit tech tier 5 | promotion ixian_promotion_neocymek tier 0 — must match |
| ixian: ixian_stormraider | unit tech tier 5 | promotion ixian_promotion_stormraider tier 0 — must match |
| latinsyndicate: latinsyndicate_burrito | unit tech tier 5 | promotion latinsyndicate_promotion_burritos tier 0 — must match |
| latinsyndicate: latinsyndicate_lars | unit tech tier 5 | promotion latinsyndicate_promotion_lars tier 0 — must match |
| latinsyndicate: latinsyndicate_topolm | unit tech tier 5 | promotion latinsyndicate_promotion_topolm tier 0 — must match |
| ordos: ordos_deviatortank | unit tech tier 5 | promotion ordos_promotion_deviatortank tier 0 — must match |
| ordos: ordos_dustdrone | unit tech tier 5 | promotion ordos_promotion_dustdrone tier 0 — must match |
| ordos: ordos_laboratorycrawler | unit tech tier 5 | promotion ordos_promotion_laboratorycrawler tier 0 — must match |
| ordos: ordos_lasertank | unit tech tier 5 | promotion ordos_promotion_lasertank tier 0 — must match |
| ordos: ordos_pythontank | unit tech tier 5 | promotion ordos_promotion_python tier 0 — must match |
| ordos: ordos_stealthraider | unit tech tier 5 | promotion ordos_promotion_stealthraider tier 0 — must match |
| steelconsortium: steelconsortium_cloudbreaker | unit tech tier 5 | promotion steelconsortium_promotion_cloudbreaker tier 0 — must match |

