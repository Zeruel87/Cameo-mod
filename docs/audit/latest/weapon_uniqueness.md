# Weapon uniqueness (DESIGN.md §10 — faction identity)

damaging armament weapons checked: 1511; W1 same-faction 40, W2 cross-faction 34, W3 carrier-only 86


## W1 — same faction, distinct actors, identical weapon (40)

| weapon | faction(s) | actors |
|---|---|---|
| 80mm_h | harkonnen | harkonnen_assaulttank, harkonnen_combat_tank |
| asianflamerturret | asianalliance | asianalliance_flametrooper, asianalliance_sentryflamer |
| asianrailtank2 | asianalliance | asianalliance_heavyrailguntank, asianalliance_railguntank |
| bcyamatocannon | terran | terran_battlecruiser, terran_phobos |
| cabalengineerrepairbeam | cabal | cabal_engineer, cabal_repairdrone |
| d2k_155mm | atreides | atreides_minotaurus, atreides_siegetank, corrino_siegetank |
| d2k_apc_rocket | ordos | ordos_apc, ordos_dustdrone |
| d2k_apc_rocket_aa | ordos | ordos_banshee, ordos_laboratorycrawler |
| d2k_bazooka2 | ixian | ixian_heavy_rocket_raider, ixian_rocket_raider |
| d2k_rocket_trooper | atreides, corrino, harkonnen, ixian, ordos | atreides_rockettrooper, corrino_sardaukar_bazooka, corrino_trooper, harkonnen_rockettrooper, harkonnen_sardaukar, ixian_rockettrooper, ordos_rockettrooper, trooper |
| d2k_towermissile | harkonnen | corrino_sardaukar_bazooka, harkonnen_rocketturret, harkonnen_sardaukar, ixian_rocketturret |
| devbullet | harkonnen | devastator, harkonnen_devastatormech |
| futuremicrotorpedos | futuretech | futuretech_phalanxwip, futuretech_riptideacv |
| harkonnenflameturret | harkonnen | harkonnen_flametank, harkonnen_flameturret |
| hmg | atreides | atreides_apc, atreides_sandbike |
| jimraynormachinegun | terran | terran_jimraynor, terran_pythean |
| laboratory_bioball | ordos | ordos_banshee, ordos_laboratorycrawler |
| light_inf_lmg | atreides, corrino, harkonnen, ixian, ordos | atreides_lightinfantry, corrino_lightinfantry, harkonnen_lightinfantry, ixian_lightinfantry, light_inf, ordos_lightinfantry |
| light_inf_lmg_upgrade | ixian | ixian_lightinfantry, light_inf |
| medicheal | terran | terran_medic, terran_medivac |
| mtank_pri | atreides, harkonnen | atreides_missiletank, atreides_mongoose, corrino_missiletank, harkonnen_rockettank, missile_tank |
| naxgrillearty | naxis | naxis_grille, naxis_naxibunker, naxis_shoekarn |
| naxiantitankcannon | naxis | naxis_antitankcannon, naxis_oldtank |
| naxijadgdestroyer | naxis | naxis_imperialturbotank, naxis_jagdpanzer |
| naxmauscannon | naxis | naxis_maus, naxis_nokana |
| naxplanegun_elite | naxis | naxis_bf109, naxis_me262 |
| naxquadcannon_aa_elite | naxis | naxis_naxibunker, naxis_ratte |
| ornimissile | atreides | atreides_airdrone, atreides_ornithopter |
| pdlaserbike | td_nod | td_nod_chemicalattackbike, td_nod_reconbike |
| scrinrepairbeam | scrin | scrin_corrupter, scrin_repair_drone |
| spore_aa | zerg | zerg_creepcolony, zerg_creepcolony_defense, zerg_sporecolony, zerg_sunkencolony_defense |
| tentacle | zerg | zerg_creepcolony, zerg_creepcolony_defense, zerg_sporecolony, zerg_sunkencolony_defense |
| tkmmedicheal | tkm | tkm_battlebus, tkm_medictruck |
| wc2_tower_arrow | wc2_humans, wc2_orcs | wc2_humans_cannontower, wc2_humans_guardtower, wc2_humans_humanscouttower, wc2_orcs_cannontower, wc2_orcs_guardtower, wc2_orcs_orcwatchtower |
| wc2arrowfire | wc2_humans | wc2_humans_elvenarcher, wc2_humans_elvenranger |
| wc2axefire | wc2_orcs | wc2_orcs_kodobeast, wc2_orcs_trollaxethrower, wc2_orcs_trollberserker |
| wc2cannontowerfire | wc2_humans, wc2_orcs | wc2_humans_cannontower, wc2_humans_guardtower, wc2_humans_humanscouttower, wc2_orcs_cannontower, wc2_orcs_guardtower, wc2_orcs_orcwatchtower |
| wc2footmanslice | wc2_humans | wc2_humans_footman, wc2_humans_militiapeasant |
| wc2magefire | wc2_humans | wc2_humans_highelfpriest, wc2_humans_highelfsorceress |
| wc2paladinexorcism | wc2_humans | wc2_humans_highelfpriest, wc2_humans_highelfsorceress |


## W2 — identical weapon across factions (34)

| weapon | families | factions | actors |
|---|---|---|---|
| d2k_rocket_trooper | 8 | atreides, corrino, harkonnen, ixian, ordos | atreides_rockettrooper, corrino_sardaukar_bazooka, corrino_trooper, harkonnen_rockettrooper, harkonnen_sardaukar, ixian_rockettrooper, ordos_rockettrooper, trooper |
| light_inf_lmg | 6 | atreides, corrino, harkonnen, ixian, ordos | atreides_lightinfantry, corrino_lightinfantry, harkonnen_lightinfantry, ixian_lightinfantry, light_inf, ordos_lightinfantry |
| wc2_tower_arrow | 6 | wc2_humans, wc2_orcs | wc2_humans_cannontower, wc2_humans_guardtower, wc2_humans_humanscouttower, wc2_orcs_cannontower, wc2_orcs_guardtower, wc2_orcs_orcwatchtower |
| wc2cannontowerfire | 6 | wc2_humans, wc2_orcs | wc2_humans_cannontower, wc2_humans_guardtower, wc2_humans_humanscouttower, wc2_orcs_cannontower, wc2_orcs_guardtower, wc2_orcs_orcwatchtower |
| mtank_pri | 5 | atreides, corrino, harkonnen | atreides_missiletank, atreides_mongoose, corrino_missiletank, harkonnen_rockettank, missile_tank |
| d2k_towermissile | 4 | corrino, harkonnen, ixian | corrino_sardaukar_bazooka, harkonnen_rocketturret, harkonnen_sardaukar, ixian_rocketturret |
| ra2ifvrepair | 4 | futuretech, naxis, schwarzermond, tkm | futuretech_repairdroid, naxis_engineeringtruck, schwarzermond_engineeringarmor, tkm_repairtruck |
| blackhawkcannon | 3 | latinsyndicate, ra2_allies, ra2_soviets | latinsyndicate_hindtransport, ra2_allies_nighthawk, ra2_soviets_transportkirov |
| d2k_155mm | 3 | atreides, corrino | atreides_minotaurus, atreides_siegetank, corrino_siegetank |
| ornigun | 3 | atreides, corrino, harkonnen | atreides_ornithopter, corrino_gunship, harkonnen_gunship |
| ra220mmrapid | 3 | ra2_allies, ra2_soviets, yuri | ra2_allies_battlefortress, ra2_allies_battlefortress_chrono, ra2_allies_battlefortress_empty, ra2_soviets_warminer, yuri_slaveminer, yuri_slaveminer_deployed |
| sealattach | 3 | futuretech, ra2_allies, tkm | futuretech_blackwidow, ra2_allies_seal, tkm_spetsnaz |
| tsengineerpistol | 3 | forgotten, ts_gdi, ts_nod | forgotten_engineer, ts_gdi_engineer, ts_nod_engineer |
| 80mm_a | 2 | atreides, corrino | atreides_combattank, corrino_bmp |
| light_inf_lmg_upgrade | 2 | atreides, corrino, harkonnen, ixian, ordos | ixian_lightinfantry, light_inf |
| naxlasert | 2 | schwarzermond, terran | schwarzermond_lasertower, terran_sentinel |
| naxsturmarty | 2 | naxis, schwarzermond | naxis_sturmtiger, schwarzermond_sturmcannon |
| plymouthrpgmines | 2 | eden, plymouth | eden_lynx_acidcloud, plymouth_lynx_esg |
| plymouthtigerrpgmines | 2 | eden, plymouth | eden_tiger_acidcloud, plymouth_tiger_esg |
| ra2rtruckrocket | 2 | futuretech, latinsyndicate | futuretech_phalanxwip, latinsyndicate_missiletruck |
| scvattack | 2 | protoss, terran | protoss_analogue, terran_scv |
| scvrepair | 2 | protoss, terran | protoss_analogue, terran_scv |
| siegeenginecannon | 2 | wc2_humans, wc2_orcs | wc2_humans_siegeengine, wc2_orcs_siegeengine |
| steeltwistermissiles | 2 | futuretech, steelconsortium | futuretech_twister, steelconsortium_twister |
| steeltwistermissiles_elite | 2 | futuretech, steelconsortium | futuretech_twister, steelconsortium_twister |
| syndicatefireballlauncher | 2 | latinsyndicate, naxis | latinsyndicate_latinflametrooper, naxis_nokana |
| tanyaattach | 2 | ra1_allies, ra2_allies | ra1_allies_tanya, ra2_allies_tanyaii |
| td_tanyaattach | 2 | td_gdi, td_nod | td_gdi_commando, td_nod_commando |
| ts_nod_mobilerepairvehicle | 2 | plymouth, ts_nod | plymouth_spider, ts_nod_mobilerepairvehicle |
| tsbazooka | 2 | forgotten, ts_nod | forgotten_rocketinfantry, ts_nod_rocketinfantry |
| tsminigun | 2 | ts_gdi, ts_nod | ts_gdi_lightinfantry, ts_nod_lightinfantry |
| wc2demolitionsquadmelee | 2 | wc2_humans, wc2_orcs | wc2_humans_demolitionsquad, wc2_orcs_goblinsappers |
| wc2gruntslice | 2 | naxis, wc2_orcs | naxis_coneheadsknights, wc2_orcs_grunt |
| wc2peasantsmack | 2 | wc2_humans, wc2_orcs | wc2_humans_peasant, wc2_orcs_peon |


## W3 — shared only with weapon-borrowing carriers (86)

| weapon | actors |
|---|---|
| bigflamer | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| dragunovsniper | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| drplasmatankweapon | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| fremen_l | atreides_fremen, futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| grenade | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ifvchronobeam | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| latinbuggychaingun | latinsyndicate_raiderbuggy, latinsyndicate_tortugatank |
| latinbuggychaingun_elite | latinsyndicate_raiderbuggy, latinsyndicate_tortugatank |
| latinbuggymg | latinsyndicate_raiderbuggy, latinsyndicate_tortugatank |
| latinbuggymg_elite | latinsyndicate_raiderbuggy, latinsyndicate_tortugatank |
| latinbuggyrocket_elite | latinsyndicate_raiderbuggy, naxis_nokana |
| lightsniper | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| lunar_amplifiedbeetlelaser | schwarzermond_laserbeetle, schwarzermond_spacezeppelin |
| lunar_amplifiedbeetlelaser_aa | schwarzermond_laserbeetle, schwarzermond_spacezeppelin |
| lunar_yellowbeetlelaser | schwarzermond_laserbeetle, schwarzermond_spacezeppelin |
| lunar_yellowbeetlelaser_aa | schwarzermond_laserbeetle, schwarzermond_spacezeppelin |
| migmissiles | latinsyndicate_mig21, ra2_soviets_migbomber |
| migmissiles_aa | latinsyndicate_mig21, ra2_soviets_migbomber |
| migmissiles_aa_elite | latinsyndicate_mig21, ra2_soviets_migbomber |
| migmissiles_elite | latinsyndicate_mig21, ra2_soviets_migbomber |
| naxgrillearty_elite | naxis_grille, schwarzermond_lunargrille |
| naxibeetlelaser_aa_elite | schwarzermond_laserbeetle, schwarzermond_spacezeppelin |
| naxibeetlelaser_elite | schwarzermond_laserbeetle, schwarzermond_spacezeppelin |
| naximp40laser | schwarzermond_noidharvester, schwarzermond_noidmgarmor |
| naximp40laser_elite | schwarzermond_noidharvester, schwarzermond_noidmgarmor |
| naxquadcannon | naxis_transportzeppelin, naxis_wirbelwind |
| naxquadcannon_aa | naxis_transportzeppelin, naxis_wirbelwind |
| naxquadcannon_elite | naxis_transportzeppelin, naxis_wirbelwind |
| oiflamer | japan_exorcistoitank, japan_oitank |
| oiplasmaflamer | japan_exorcistoitank, japan_oitank |
| oismallcannon | japan_exorcistoitank, japan_oitank |
| oismallplasmacannon | japan_exorcistoitank, japan_oitank |
| ra2120mm | naxis_shoekarn, ra2_soviets_rhinoheavytank |
| ra2120mm_elite | naxis_shoekarn, ra2_soviets_rhinoheavytank |
| ra2awp | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair, ra2_allies_sniper |
| ra2crm60 | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2crm60h | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2doublepistolsifv | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2flaktrackgun | ra2_soviets_flaktrack, ra2_soviets_seascorpion |
| ra2hovermissile | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2hovermissile_aa | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2hovermissile_aa_elite | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2hovermissile_elite | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2miragegun | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair, ra2_allies_miragetank |
| ra2multihovermissile | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2multihovermissile_aa | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2multihovermissile_aa_elite | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2multihovermissile_elite | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2multithunderboltmissile | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2multithunderboltmissile_aa | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2multithunderboltmissile_aa_elite | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2multithunderboltmissile_elite | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2radbeamweapon | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair, ra2_soviets_desolator |
| ra2thunderboltmissile | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2thunderboltmissile_aa | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2thunderboltmissile_aa_elite | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ra2thunderboltmissile_elite | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| sandmarinetuskcryo | tkm_bigshiee, tkm_sandmarine |
| sandmarinetuskfire | tkm_bigshiee, tkm_sandmarine |
| sandmarinetusktwin | tkm_bigshiee, tkm_sandmarine |
| steelinfrailgun | steelconsortium_defenderbot, steelconsortium_quantummissiletrooper |
| steelinfrailgun_elite | steelconsortium_defenderbot, steelconsortium_quantummissiletrooper |
| steelinfrailgun_emp | steelconsortium_defenderbot, steelconsortium_quantummissiletrooper |
| steelinfrailgun_emp_elite | steelconsortium_defenderbot, steelconsortium_quantummissiletrooper |
| steelmakogun | steelconsortium_hoverboardgrenadier, steelconsortium_mako |
| steelmakogun_elite | steelconsortium_hoverboardgrenadier, steelconsortium_mako |
| steelmakogun_emp | steelconsortium_hoverboardgrenadier, steelconsortium_mako |
| steelmakogun_emp_elite | steelconsortium_hoverboardgrenadier, steelconsortium_mako |
| swgbigredlaserg | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| swgreenlaserg | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| swlaserg | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| tkmcryorockets | tkm_as42, tkm_rocketeer |
| tkmfirerockets | tkm_as42, tkm_rocketeer |
| tkmtwinrockets | tkm_as42, tkm_rocketeer |
| tssoniczap | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| ttankzap | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| usalasercannonag | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| wc2knightslice | wc2_humans_knight, wc2_humans_paladin, wc2_humans_warcraft3knight |
| wc2mageblizzard | wc2_humans_archmage, wc2_humans_mage |
| wc2magefireballexplosion | wc2_humans_archmage, wc2_humans_mage |
| wc2magefireballvisible | wc2_humans_archmage, wc2_humans_mage |
| wc2mageslow | wc2_humans_archmage, wc2_humans_mage |
| wc2paladinhealing | wc2_humans_highelfsorceress, wc2_humans_knight, wc2_humans_paladin, wc2_humans_warcraft3knight |
| wc_tower_fire | futuretech_salamanderifv, ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg, ra2_allies_ifv_missile, ra2_allies_ifv_repair |
| zerofighterchaingun | japan_japanesebomber, japan_zerofighter |
| zerofighterchaingunwaveforce | japan_japanesebomber, japan_zerofighter |

