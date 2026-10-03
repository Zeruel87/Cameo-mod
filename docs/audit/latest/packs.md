# audit_packs — content-pack conversion & placement (DESIGN §2)

## P1 — conversion coverage (faction prefixes with actors OUTSIDE packs)

| prefix | in packs | outside packs | sample outside file |
|---|---|---|---|
| ra2 | 180 | 165 | mods\cameo\rules\misc.yaml |
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
| sglmobilesupplytruck | 0 | 3 | mods\cameo\rules\shockwave.yaml |
| aircraft | 0 | 2 | mods\cameo\rules\husks.yaml |
| op2 | 0 | 2 | mods\cameo\rules\outpost2.yaml |
| ra1_soviets | 121 | 2 | mods\cameo\rules\heroes.yaml |
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
| ts | 40 | 2 | mods\cameo\rules\misc.yaml |
| wc2_h | 0 | 2 | mods\cameo\rules\warcraft2.yaml |
| wc2_o | 0 | 2 | mods\cameo\rules\warcraft2.yaml |
| win98 | 0 | 2 | mods\cameo\rules\win98.yaml |
| camea | 0 | 1 | mods\cameo\rules\camea.yaml |
| cute | 0 | 1 | mods\cameo\rules\valentine.yaml |
| dummy | 0 | 1 | mods\cameo\rules\redalert2.yaml |
| hta | 0 | 1 | mods\cameo\rules\sow.yaml |
| htb | 0 | 1 | mods\cameo\rules\sow.yaml |
| htc | 0 | 1 | mods\cameo\rules\sow.yaml |
| htd | 0 | 1 | mods\cameo\rules\sow.yaml |
| hte | 0 | 1 | mods\cameo\rules\sow.yaml |
| infantry | 0 | 1 | mods\cameo\rules\misc.yaml |
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
| td_nod | 71 | 1 | mods\cameo\rules\tiberiaalliances.yaml |
| techbuilding | 0 | 1 | mods\cameo\rules\misc.yaml |
| upsusagunship3 | 0 | 1 | mods\cameo\rules\shockwave.yaml |
| upusaleaflet | 0 | 1 | mods\cameo\rules\generals.yaml |
| vehicles | 0 | 1 | mods\cameo\rules\misc.yaml |
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

Fully converted prefixes (56): asianalliance, atreides, cabal, corrino, d2k, farasha, forgotten, fremen, futu, futuretech, harkonnen, ixian, japan, latin, latinsyndicate, light, missile, nax, naxis, ordos, protoss, ra1_allies, ra1_badger, ra2_allies, ra2_soviets, ra2_yuri, ra2e2, ra2gacnst, ra2nacnst, schwarzermond, scrin, siege, sietch, steel, steelconsortium, td, td_gdi, team, terran, tkm, ts_bus, ts_gdi, ts_nod, ts_pickup, ts_pickupb, ts_sedan, ts_trucka, ts_truckb, ts_wini, up, upgrade, wc2_humans, wc2_orcs, yrnacnst, yuri, zerg

## P2 — actors whose id does not match the pack's dominant prefix

| pack | actor | dominant prefix |
|---|---|---|
| D2k/Harkonnen | missile_tank | harkonnen |
| D2k/Ixian | farasha_drone_ixian | ixian |
| D2k/Ixian | team_upgrade.d2k_advanced_ixian_technology | ixian |
| D2k/Ordos | team_upgrade.ordos_stealthtechnology | ordos |
| RedAlert2Mod/Consortium | steel_inspect_husk | steelconsortium |
| RedAlert2Mod/Consortium | steel_twister_husk | steelconsortium |
| RedAlert2Mod/Consortium | steel_grun_husk | steelconsortium |
| RedAlert2Mod/Consortium | steel_cargoship_husk | steelconsortium |
| RedAlert2Mod/Consortium | steel_cruiser_husk | steelconsortium |
| RedAlert2Mod/Consortium | steel_cruiser_f_husk | steelconsortium |
| RedAlert2Mod/Consortium | steel_cruiser_f | steelconsortium |
| RedAlert2Mod/Consortium | steel_scalpelMG | steelconsortium |
| RedAlert2Mod/Consortium | steel_scalpelQuantumCannon | steelconsortium |
| RedAlert2Mod/Consortium | steel_scalpelAA | steelconsortium |
| RedAlert2Mod/Consortium | steel_qacst_infiltrated | steelconsortium |
| RedAlert2Mod/Consortium | up_team_shielresistance.steel | steelconsortium |
| RedAlert2Mod/Consortium | steel_cougar | steelconsortium |
| RedAlert2Mod/Consortium | steel_hummer | steelconsortium |
| RedAlert2Mod/Consortium | steel_oldqtnk | steelconsortium |
| RedAlert2Mod/Consortium | steel_cobra | steelconsortium |
| RedAlert2Mod/FutureTech | futu_cryo_husk | futuretech |
| RedAlert2Mod/FutureTech | futu_harbinger_husk | futuretech |
| RedAlert2Mod/FutureTech | futu_landcarr_drone | futuretech |
| RedAlert2Mod/FutureTech | futu_egcnst_infiltrated | futuretech |
| RedAlert2Mod/Naxis | nax_bitsmark | naxis |
| RedAlert2Mod/Syndicate | latin_ra2hind_husk | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_yakolev_husk | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_mig_husk | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_cgyard | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_triton | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_sub | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_rammax | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_cgcnst_infiltrated | latinsyndicate |
| RedAlert2Mod/Syndicate | up_team_ngbunk2.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | up_team_cashrecover.latin | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_deathcash | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_deathcash_small | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_scrapcar | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_scrapcar_demo | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_scrapcar_driveby | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_scrapcar2 | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_scrapcar2_demo | latinsyndicate |
| RedAlert2Mod/Syndicate | latin_scrapcar2_driveby | latinsyndicate |

## P3 — content.yaml manifest vs disk / nonstandard filenames

- `D2k\Atreides`: nonstandard filename `voices.yaml` (closed set, DESIGN §2)
- `D2k\Harkonnen`: nonstandard filename `voices.yaml` (closed set, DESIGN §2)
- `D2k\Ixian`: nonstandard filename `voices.yaml` (closed set, DESIGN §2)
- `D2k\Ordos`: nonstandard filename `voices.yaml` (closed set, DESIGN §2)
- `D2k\Shared`: nonstandard filename `voices.yaml` (closed set, DESIGN §2)
- `TiberianSun\Shared`: `misc.yaml` on disk but NOT in content.yaml
- `TiberiumWars\Scrin`: `voices.yaml` on disk but NOT in content.yaml
- `TiberiumWars\Scrin`: nonstandard filename `buildup-palettes.yaml` (closed set, DESIGN §2)
- `TiberiumWars\Scrin`: nonstandard filename `palettes.yaml` (closed set, DESIGN §2)
- `TiberiumWars\Scrin`: nonstandard filename `voices.yaml` (closed set, DESIGN §2)

## P4 — naming summary (counts; details via gen_rename_maps)

- actor ids violating the lowercase grammar: **1576** (e.g. 1TNK.camea, 2100A2MAT, 2100A2PT, 2100A2TIT, 2100A2VET, 2100AA, 2100AACH, 2100AAMAT)

Total findings: 662
