# audit_packs — content-pack conversion & placement (DESIGN §2)

## P1 — conversion coverage (faction prefixes with actors OUTSIDE packs)

| prefix | in packs | outside packs | sample outside file |
|---|---|---|---|
| ra2 | 166 | 164 | mods\cameo\rules\misc.yaml |
| wc | 0 | 79 | mods\cameo\rules\warcraft1.yaml |
| halloween | 0 | 39 | mods\cameo\rules\halloween.yaml |
| sow | 0 | 38 | mods\cameo\rules\sow.yaml |
| xmas | 0 | 22 | mods\cameo\rules\xmas.yaml |
| mindclass | 0 | 17 | mods\cameo\rules\mindustry.yaml |
| valentine | 0 | 15 | mods\cameo\rules\valentine.yaml |
| xcom | 0 | 14 | mods\cameo\rules\xcom.yaml |
| valentines | 0 | 13 | mods\cameo\rules\valentine.yaml |
| wc2_orc | 0 | 11 | mods\cameo\rules\warcraft2.yaml |
| ra2_lt | 10 | 10 | mods\cameo\rules\redalert2.yaml |
| shockwave | 0 | 9 | mods\cameo\rules\shockwave.yaml |
| wc2_human | 0 | 9 | mods\cameo\rules\warcraft2.yaml |
| sc2k | 0 | 8 | mods\cameo\rules\sc2k.yaml |
| ambiance | 0 | 7 | mods\cameo\rules\misc.yaml |
| d2 | 0 | 7 | mods\cameo\rules\dune2.yaml |
| factory | 0 | 4 | mods\cameo\rules\sow.yaml |
| ra2_c | 4 | 4 | mods\cameo\rules\redalert2.yaml |
| simcity | 0 | 4 | mods\cameo\rules\simcity.yaml |
| wc2_critter | 0 | 4 | mods\cameo\rules\warcraft2.yaml |
| eden | 0 | 3 | mods\cameo\rules\outpost2.yaml |
| ra1_soviets | 121 | 3 | mods\cameo\rules\heroes.yaml |
| sglmobilesupplytruck | 0 | 3 | mods\cameo\rules\shockwave.yaml |
| op2 | 0 | 2 | mods\cameo\rules\outpost2.yaml |
| ra2_ambu | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_bcab | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_bus | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_car | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_cona | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_cop | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_ddbx | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_euroc | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_jeep | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_limo | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_ptruck | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_stang | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_suvb | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_suvw | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_taxi | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_tractor | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_trucka | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_truckb | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| ra2_ycab | 2 | 2 | mods\cameo\rules\redalert2.yaml |
| satelliteprotection | 0 | 2 | mods\cameo\rules\sow.yaml |
| schsupply | 0 | 2 | mods\cameo\rules\shockwave.yaml |
| sglrpgtrooper | 0 | 2 | mods\cameo\rules\shockwave.yaml |
| susacannon | 0 | 2 | mods\cameo\rules\shockwave.yaml |
| susapower | 0 | 2 | mods\cameo\rules\shockwave.yaml |
| susasupply | 0 | 2 | mods\cameo\rules\shockwave.yaml |
| wc2_h | 0 | 2 | mods\cameo\rules\warcraft2.yaml |
| wc2_o | 0 | 2 | mods\cameo\rules\warcraft2.yaml |
| win98 | 0 | 2 | mods\cameo\rules\win98.yaml |
| aircraft | 0 | 1 | mods\cameo\rules\husks.yaml |
| camea | 0 | 1 | mods\cameo\rules\camea.yaml |
| cute | 0 | 1 | mods\cameo\rules\valentine.yaml |
| dummy | 1 | 1 | mods\cameo\rules\redalert2.yaml |
| hta | 0 | 1 | mods\cameo\rules\sow.yaml |
| htb | 0 | 1 | mods\cameo\rules\sow.yaml |
| htc | 0 | 1 | mods\cameo\rules\sow.yaml |
| htd | 0 | 1 | mods\cameo\rules\sow.yaml |
| hte | 0 | 1 | mods\cameo\rules\sow.yaml |
| large | 0 | 1 | mods\cameo\rules\xcom.yaml |
| medium | 0 | 1 | mods\cameo\rules\xcom.yaml |
| mta | 0 | 1 | mods\cameo\rules\sow.yaml |
| mtb | 0 | 1 | mods\cameo\rules\sow.yaml |
| mtc | 0 | 1 | mods\cameo\rules\sow.yaml |
| mtd | 0 | 1 | mods\cameo\rules\sow.yaml |
| mte | 0 | 1 | mods\cameo\rules\sow.yaml |
| ra | 0 | 1 | mods\cameo\rules\husks.yaml |
| ra1 | 11 | 1 | mods\cameo\rules\civilian.yaml |
| ra2_ctmisc06 | 1 | 1 | mods\cameo\rules\redalert2.yaml |
| sc | 0 | 1 | mods\cameo\rules\starcraft.yaml |
| schhacker | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| schlotus | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| schredguard | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| schsiegesoldier | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| schtankhunter | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| sglaangrymob1 | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| sglaangrymob2 | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| sglamob | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| sglterrorist | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| sgltoxinrebel | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| sowbomber | 0 | 1 | mods\cameo\rules\sow.yaml |
| sowfighter | 0 | 1 | mods\cameo\rules\sow.yaml |
| sowtripler | 0 | 1 | mods\cameo\rules\sow.yaml |
| swa10 | 0 | 1 | mods\cameo\rules\starwars.yaml |
| swdroidheli | 0 | 1 | mods\cameo\rules\starwars.yaml |
| swlaat | 0 | 1 | mods\cameo\rules\starwars.yaml |
| swxwing | 0 | 1 | mods\cameo\rules\starwars.yaml |
| td_nod | 65 | 1 | mods\cameo\rules\tiberiaalliances.yaml |
| ts | 0 | 1 | mods\cameo\rules\misc.yaml |
| upsusagunship3 | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| upusaleaflet | 0 | 1 | mods\cameo\rules\generals.yaml |
| wc2 | 0 | 1 | mods\cameo\rules\warcraft2.yaml |
| wc2_camera | 0 | 1 | mods\cameo\rules\warcraft2.yaml |
| wc2_neutral | 0 | 1 | mods\cameo\rules\warcraft2.yaml |
| wc2_support | 0 | 1 | mods\cameo\rules\warcraft2.yaml |
| wh40kcommisair | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kguardmobslave | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kguardsquad | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kkarsmobslave | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kkarssquad | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kmarine | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kogrynmobslave | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kogrynsquad | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kpsyker | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kscoutmobslave | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40kscoutsquad | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| wh40ktechpriest | 0 | 1 | mods\cameo\rules\wh40k.yaml |
| worms | 0 | 1 | mods\cameo\rules\worms.yaml |
| zmcv | 0 | 1 | mods\cameo\rules\z.yaml |

Fully converted prefixes (76): air, asianalliance, atreides, banshee, bomber, cabal, cargoship, carryall, cgcnst, combat, corrino, cruiser, cryo, d2k, deathcash, drone, duelist, egcnst, eye, farasha, forgotten, fremen, futuretech, grun, harbinger, harkonnen, heavy, heavydrone, inspect, ixian, japan, kami, landcarr, latinsyndicate, light, mig, missile, nax, naxis, ordos, ornithopter, pelican, phoenix, protoss, qacst, ra1_allies, ra1_badger, ra2_allies, ra2_soviets, ra2_yuri, ra2hind, resonance, rocket, schwarzermond, scrapcar, scrapcar2, siege, sietch, sonic, steelconsortium, swarmer, td_gdi, team, terran, tkm, ts_gdi, ts_nod, twister, up, upgrade, wc2_humans, wc2_orcs, wraith, yakolev, yuri, zerg

## P2 — actors whose id does not match the pack's dominant prefix

| pack | actor | dominant prefix |
|---|---|---|
| D2k/Atreides | ornithopter_husk.atreides | atreides |
| D2k/Atreides | upgrade_conyard.atreides | atreides |
| D2k/Atreides | upgrade_barracks.atreides | atreides |
| D2k/Atreides | upgrade_light.atreides | atreides |
| D2k/Atreides | upgrade_heavy.atreides | atreides |
| D2k/Atreides | upgrade_radar.atreides | atreides |
| D2k/Atreides | combat_tank_husk.atreides | atreides |
| D2k/Atreides | sonic_tank_husk.atreides | atreides |
| D2k/Atreides | siege_tank_husk.atreides | atreides |
| D2k/Corrino | carryall_husk.corrino | corrino |
| D2k/Corrino | upgrade_conyard.corrino | corrino |
| D2k/Corrino | upgrade_barracks.corrino | corrino |
| D2k/Corrino | upgrade_light.corrino | corrino |
| D2k/Corrino | upgrade_heavy.corrino | corrino |
| D2k/Corrino | upgrade_radar.corrino | corrino |
| D2k/Corrino | siege_tank_husk.corrino | corrino |
| D2k/Harkonnen | carryall_husk.harkonnen | harkonnen |
| D2k/Harkonnen | upgrade_conyard.harkonnen | harkonnen |
| D2k/Harkonnen | upgrade_barracks.harkonnen | harkonnen |
| D2k/Harkonnen | upgrade_light.harkonnen | harkonnen |
| D2k/Harkonnen | upgrade_heavy.harkonnen | harkonnen |
| D2k/Harkonnen | upgrade_radar.harkonnen | harkonnen |
| D2k/Harkonnen | combat_tank.harkonnen | harkonnen |
| D2k/Harkonnen | missile_tank | harkonnen |
| D2k/Ixian | air_drone_husk.ixian | ixian |
| D2k/Ixian | drone_husk.ixian | ixian |
| D2k/Ixian | resonance_drone_husk.ixian | ixian |
| D2k/Ixian | farasha_husk.ixian | ixian |
| D2k/Ixian | heavydrone_husk.ixian | ixian |
| D2k/Ixian | farasha_drone_ixian | ixian |
| D2k/Ixian | farasha_drone_husk.ixian | ixian |
| D2k/Ixian | heavy_inf.ixian | ixian |
| D2k/Ixian | team_upgrade.d2k_advanced_ixian_technology | ixian |
| D2k/Ixian | rocket_raider.ixian | ixian |
| D2k/Ixian | heavy_rocket_raider.ixian | ixian |
| D2k/Ixian | duelist_tank.ixian | ixian |
| D2k/Ordos | wraith_husk.ordos | ordos |
| D2k/Ordos | swarmer_husk.ordos | ordos |
| D2k/Ordos | banshee_husk.ordos | ordos |
| D2k/Ordos | eye_husk.ordos | ordos |
| D2k/Ordos | carryall_reinforce.ordos | ordos |
| D2k/Ordos | carryall_husk.ordos | ordos |
| D2k/Ordos | carryall_huskvtol.ordos | ordos |
| D2k/Ordos | team_upgrade.ordos_stealthtechnology | ordos |
| RedAlert2Mod/AsianAlliance | kami_chemical.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | kami_asdf.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | kami_husk.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | kami_chemical_husk.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | phoenix_husk.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | harbinger_husk.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | pelican_husk.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | bomber_minebomb.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | bomber_minebomb2.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | bomber_husk.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | cgcnst_infiltrated.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | up_tsunami.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | up_dragonway_proxy_actor.asian | asianalliance |
| RedAlert2Mod/AsianAlliance | up_team_diplomacy_proxy_actor.asian | asianalliance |
| RedAlert2Mod/Consortium | inspect_husk.steel | steelconsortium |
| RedAlert2Mod/Consortium | twister_husk.steel | steelconsortium |
| RedAlert2Mod/Consortium | grun_husk.steel | steelconsortium |
| RedAlert2Mod/Consortium | cargoship_husk.steel | steelconsortium |
| RedAlert2Mod/Consortium | cruiser_husk.steel | steelconsortium |
| RedAlert2Mod/Consortium | cruiser_f_husk.steel | steelconsortium |
| RedAlert2Mod/Consortium | cruiser_f.steel | steelconsortium |
| RedAlert2Mod/Consortium | qacst_infiltrated.steel | steelconsortium |
| RedAlert2Mod/Consortium | up_team_shielresistance.steel | steelconsortium |
| RedAlert2Mod/FutureTech | cryo_husk.futu | futuretech |
| RedAlert2Mod/FutureTech | harbinger_husk.futu | futuretech |
| RedAlert2Mod/FutureTech | landcarr_drone.futu | futuretech |
| RedAlert2Mod/FutureTech | egcnst_infiltrated.futu | futuretech |
| RedAlert2Mod/Naxis | nax_bitsmark | naxis |
| RedAlert2Mod/Syndicate | ra2hind_husk.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | yakolev_husk.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | mig_husk.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | cgcnst_infiltrated.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | up_team_ngbunk2.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | up_team_cashrecover.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | deathcash_small.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | scrapcar_demo.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | scrapcar_driveby.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | scrapcar2_demo.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | scrapcar2_driveby.latin | latinsyndicate |
| TiberianDawn/GDI | team_upgrade.up_lightweightarmorplating | td_gdi |
| TiberianDawn/Nod | team_upgrade.up_advancedguerillatactics | td_nod |

## P3 — content.yaml manifest vs disk / nonstandard filenames

_clean_

## P4 — naming summary (counts; details via gen_rename_maps)

- actor ids violating the lowercase grammar: **1510** (e.g. 1TNK.camea, 2100A2MAT, 2100A2PT, 2100A2TIT, 2100A2VET, 2100AA, 2100AACH, 2100AAMAT)

Total findings: 689
