# audit_duplicate_keys — duplicate keys in one node (ambiguous merges)

Files scanned: **650** — D1 ambiguous inheritance labels: **0**, D2 merged duplicates: **261**


## D1 — duplicate inheritance labels with different parent values

_none found_


## D2 — duplicate keys by key name (top 40)

| key | occurrences |
|---|---|
| RenderSprites | 31 |
| Voiced | 15 |
| RevealsShroud | 14 |
| Prerequisites | 11 |
| Defaults | 10 |
| HitShape | 8 |
| Selectable | 7 |
| muzzle | 6 |
| Warhead@1Dam | 6 |
| AutoTarget | 5 |
| ProvidesPrerequisite@buildingname | 5 |
| cheer | 4 |
| SpawnActorOnDeath | 4 |
| WithAmmoPipsDecoration | 4 |
| AttackAircraft | 3 |
| GrantConditionOnPrerequisite@2 | 3 |
| ProvidesPrerequisite | 3 |
| stand | 3 |
| gtwrmake | 3 |
| Report | 3 |
| Burst | 3 |
| dead | 2 |
| idle | 2 |
| Building | 2 |
| ProducibleWithLevel | 2 |
| RequiresCondition | 2 |
| GiveUnitCrateAction | 2 |
| Armament | 2 |
| Explodes@6 | 2 |
| AttackFrontal | 2 |
| DeathSounds | 2 |
| susabomber.laser | 2 |
| DetectCloaked | 2 |
| RenderVoxels | 2 |
| GiveCashCrateAction@1 | 2 |
| BaseBuilding | 2 |
| AttackTurreted | 2 |
| Scale | 2 |
| die5 | 2 |
| Warhead@2Eff | 2 |


## D2 — full list

| file | lines | node | key |
|---|---|---|---|
| mods/cameo/chrome/ingame_observer.yaml | 316, 320 | Container@OBSERVER_WIDGETS > Children > Image@REPLAY_PLAYER | Visible |
| mods/cameo/chrome/settings_display.yaml | 26, 80, 110, 141, 165, 191, 206, 228, 283, 344, 386, 399, 431, 444, 457, 470, 483, 496, 509 | Container@DISPLAY_PANEL > Children > ScrollPanel@SETTINGS_SCROLLPANEL > Children | Container@ROW |
| mods/cameo/chrome/settings_display.yaml | 66, 269 | Container@DISPLAY_PANEL > Children > ScrollPanel@SETTINGS_SCROLLPANEL > Children | Container@SPACER |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/sequences.yaml | 520, 521 | hightech.ordos | Defaults |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/sequences.yaml | 966, 990 | ordos_leech | die4 |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml | 1195, 1282 | D2K_APC_Rocket_AA | Warhead@MissileAA_MediumFlatCompatibility |
| mods/cameo/ContentPacks/RedAlert2/Allies/yaml/sequences.yaml | 11, 37 | ra2_allies_alliedconstructionyard | dead |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/sequences.yaml | 3731, 3737 | yrslav | cheer |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/sequences.yaml | 3870, 3874 | ra2howi | muzzle |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/sequences.yaml | 3883, 3887 | ra2arty | muzzle |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/sequences.yaml | 4, 45 | yuri_constructionyard | build |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/sequences.yaml | 11, 31 | asianalliance_asianconstructionyard | dead |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/sequences.yaml | 1275, 1304 | asianalliance_asianflametrooper | shoot |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/sequences.yaml | 1288, 1301 | asianalliance_asianflametrooper | cheer |
| mods/cameo/ContentPacks/RedAlert2Mod/Naxis/yaml/sequences.yaml | 930, 936 | naxis_slave | cheer |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/sequences.yaml | 525, 583 | latinsyndicate_topolsilo | critical-idle |
| mods/cameo/ContentPacks/StarCraft/Protoss/yaml/sequences.yaml | 503, 505 | protoss_arbiter | idle |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/sequences.yaml | 388, 394 | td_gdi_advancedguardtower | muzzle |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/sequences.yaml | 62, 66 | forgotten_chemsprayinfantry | prone-shoot |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/sequences.yaml | 334, 375 | forgotten_zombiemutant | standup |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/sequences.yaml | 369, 384 | forgotten_zombiemutant | die-crushed |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/sequences.yaml | 150, 153 | wc2_humans_guardtower | Defaults |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/sequences.yaml | 158, 161 | wc2_humans_cannontower | Defaults |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/sequences.yaml | 166, 168 | wc2_humans_wall | Defaults |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/sequences.yaml | 165, 167 | wc2_orcs_wall | Defaults |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/sequences.yaml | 583, 587 | wc2_orcs_ogre | idle-ogremage |
| mods/cameo/rules/advancewars.yaml | 1068, 1071 | ^AdvanceWarsUniversalPowers | RevealsShroudMultiplier@sonjapower1 |
| mods/cameo/rules/advancewars.yaml | 1136, 1146 | ^AdvanceWarsVehicleAttack | SpeedMultiplier@jesspower1 |
| mods/cameo/rules/advancewars.yaml | 2389, 2394 | hq.orange | Production@Research |
| mods/cameo/rules/advancewars.yaml | 5118, 5152 | awfortress | Building |
| mods/cameo/rules/advancewars.yaml | 5638, 5643 | awyard.orange | HitShape |
| mods/cameo/rules/advancewars.yaml | 5972, 5975, 5978, 5981, 5984, 5987, 5990, 5993 | awlab > ClassicAirstrikePower@Duster > Squad | awdustersupport |
| mods/cameo/rules/advancewars.yaml | 10784, 10845 | awbomber | ProducibleWithLevel |
| mods/cameo/rules/advancewars.yaml | 10946, 10951 | awblackbomb | ProducibleWithLevel |
| mods/cameo/rules/advancewars.yaml | 12322, 12329 | awhydrosupport | RenderSprites |
| mods/cameo/rules/advancewars.yaml | 12346, 12353 | awdustersupport | RenderSprites |
| mods/cameo/rules/ants.yaml | 71, 80 | QANT | Voiced |
| mods/cameo/rules/ants.yaml | 754, 774 | defenseant | AutoTarget |
| mods/cameo/rules/camea.yaml | 583, 584 | mslo.camea > RevealsShroud | RequiresCondition |
| mods/cameo/rules/casino.yaml | 232, 253 | Casino_Regular_Crate_1 | GiveUnitCrateAction@e6 |
| mods/cameo/rules/challenge.yaml | 27, 33 | World > FactionCA@x_monsters | Name |
| mods/cameo/rules/challenge.yaml | 28, 34 | World > FactionCA@x_monsters | InternalName |
| mods/cameo/rules/challenge.yaml | 30, 37 | World > FactionCA@x_monsters | Side |
| mods/cameo/rules/challenge.yaml | 31, 38 | World > FactionCA@x_monsters | Description |
| mods/cameo/rules/darkreign.yaml | 3469, 3476 | drnavyard.freedomguard | HitShape |
| mods/cameo/rules/darkreign.yaml | 7100, 7111 | drvortextank | WithSpriteTurret |
| mods/cameo/rules/darkreign.yaml | 7699, 7706 | drnavyard.terror | HitShape |
| mods/cameo/rules/darkreign.yaml | 9116, 9123 | drnavyard.eodalien | HitShape |
| mods/cameo/rules/darkreign.yaml | 10864, 10866 | drshelter | RenderSprites |
| mods/cameo/rules/darkreign.yaml | 11017, 11024 | satanclawzcrate | GiveUnitCrateAction |
| mods/cameo/rules/darkreign.yaml | 11263, 11265 | drsubterrean | RenderSprites |
| mods/cameo/rules/darkreign.yaml | 11278, 11280 | drfarm | RenderSprites |
| mods/cameo/rules/darkreign.yaml | 11298, 11300 | drfarm2 | RenderSprites |
| mods/cameo/rules/darkreign.yaml | 11318, 11320 | drfarm3 | RenderSprites |
| mods/cameo/rules/darkreign.yaml | 11338, 11340 | drrural | RenderSprites |
| mods/cameo/rules/darkreign.yaml | 11353, 11355 | drcomercial | RenderSprites |
| mods/cameo/rules/darkreign.yaml | 11368, 11370 | drctech | RenderSprites |
| mods/cameo/rules/darkreign.yaml | 11383, 11385 | drconcessionaire | RenderSprites |
| mods/cameo/rules/darkreign.yaml | 11398, 11400 | drtents | RenderSprites |
| mods/cameo/rules/dune2.yaml | 621, 625 | dunemcv | RenderSprites |
| mods/cameo/rules/generals.yaml | 3618, 3654 | glbggy | RenderSprites |
| mods/cameo/rules/generals.yaml | 4905, 4937 | glworker | AutoTarget |
| mods/cameo/rules/generals.yaml | 7386, 7401 | charty | Explodes |
| mods/cameo/rules/generals.yaml | 7595, 7596 | choverlord > WithRangeCircle@propaganda | RequiresCondition |
| mods/cameo/rules/generals.yaml | 8125, 8140 | checm | Turreted |
| mods/cameo/rules/generals.yaml | 9157, 9175 | chhelix | ReloadDelayMultiplier@BUNKER |
| mods/cameo/rules/generals.yaml | 11423, 11425 | usasupply | CustomSellValue |
| mods/cameo/rules/generals.yaml | 11510, 11533 | usahook | SpawnActorOnDeath |
| mods/cameo/rules/generals.yaml | 12472, 12475 | usastealth | GrantConditionOnPrerequisite@selectusaairforce |
| mods/cameo/rules/generals.yaml | 12768, 12774 | usacomanche | ProductionCostMultiplier@selectusaairforce |
| mods/cameo/rules/generals.yaml | 12810, 12904 | usafirebase | RenderSprites |
| mods/cameo/rules/halloween.yaml | 247, 257 | halloween_crypto | Voiced |
| mods/cameo/rules/halloween.yaml | 585, 587 | halloween_spirittower | SpawnActorOnDeath@death1 |
| mods/cameo/rules/halloween.yaml | 999, 1013 | halloween_skeleton | Armament |
| mods/cameo/rules/halloween.yaml | 1046, 1051 | halloween_demon | RenderSprites |
| mods/cameo/rules/halloween.yaml | 1140, 1145 | halloween_cow | RenderSprites |
| mods/cameo/rules/halloween.yaml | 1325, 1327 | halloween_franky | RenderSprites |
| mods/cameo/rules/halloween.yaml | 1468, 1473 | halloween_clown3 | ChangesHealth |
| mods/cameo/rules/heroes.yaml | 636, 639 | volkovcc > Buildable | Prerequisites |
| mods/cameo/rules/heroes.yaml | 1053, 1057, 1060 | TSNASHWA | WithAmmoPipsDecoration |
| mods/cameo/rules/heroes.yaml | 1084, 1087 | TSNASHWABIKE | ProvidesPrerequisite@nashwabike |
| mods/cameo/rules/heroes.yaml | 1386, 1404 | mutantseverus | RevealsShroud |
| mods/cameo/rules/heroes.yaml | 1438, 1462 | severuscabal | PeriodicExplosion@circle2 |
| mods/cameo/rules/heroes.yaml | 1441, 1465 | severuscabal | PeriodicExplosion@circleheal2 |
| mods/cameo/rules/heroes.yaml | 1507, 1530 | severuscabal | RevealsShroud |
| mods/cameo/rules/heroes.yaml | 1679, 1683 | JACK | WithHarvesterPipsDecoration |
| mods/cameo/rules/infected.yaml | 220, 223 | zbio | Explodes@6 |
| mods/cameo/rules/iok.yaml | 562, 566 | IOKPROC | ProvidesPrerequisite@buildingname |
| mods/cameo/rules/iok.yaml | 571, 575 | IOKPROC | SpawnActorOnDeath@hole |
| mods/cameo/rules/iok.yaml | 1000, 1002 | IOKSITE > Buildable | Prerequisites |
| mods/cameo/rules/iok.yaml | 1192, 1202 | IOKJETPLANE | AttackAircraft |
| mods/cameo/rules/lostunits.yaml | 1214, 1323 | dalek | AttackFrontal |
| mods/cameo/rules/mindustry.yaml | 110, 115 | mindclass_core | RenderSprites |
| mods/cameo/rules/monsters.yaml | 158, 180 | trex | Buildable |
| mods/cameo/rules/monsters.yaml | 284, 289 | RA2DEMON | RenderSprites |
| mods/cameo/rules/monsters.yaml | 433, 447 | RA2SKELETON | Armament |
| mods/cameo/rules/monsters.yaml | 595, 601 | RA2TRIPOD | DeathSounds |
| mods/cameo/rules/redalert2.yaml | 1082, 1102 | ra2sqd | AttackFrontal |
| mods/cameo/rules/redalert2.yaml | 1195, 1235 | ra2dest | Selectable |
| mods/cameo/rules/redalert2.yaml | 1667, 1675 | yrbpln | Contrail@1 |
| mods/cameo/rules/redalert2.yaml | 1670, 1681 | yrbpln | Contrail@2 |
| mods/cameo/rules/redalert2.yaml | 1673, 1690 | yrbpln | SpawnActorOnDeath |
| mods/cameo/rules/redalert2.yaml | 2472, 2474 | ra2sidewind | Voiced |
| mods/cameo/rules/sc2k.yaml | 1006, 1013 | SC2KMARINA | HitShape |
| mods/cameo/rules/sc2k.yaml | 1296, 1303 | SC2KMISSILESILO | Building |
| mods/cameo/rules/sc2k.yaml | 1825, 1835 | SC2KJETPLANE | AttackAircraft |
| mods/cameo/rules/sc2k.yaml | 2026, 2062 | SC2KPOLICECAR | Voiced |
| mods/cameo/rules/sc2k.yaml | 2114, 2123 | SC2KFIRETRUCK | Voiced |
| mods/cameo/rules/shockwave.yaml | 1083, 1086, 1089, 1092, 1095, 1098, 1101, 1104, 1107, 1110, 1113, 1116, 1119 | ^ShockwaveUSASupportPowers > ClassicAirstrikePower@susaf16sp > Squad | susaf16 |
| mods/cameo/rules/shockwave.yaml | 1183, 1186 | ^ShockwaveUSASupportPowers > ClassicAirstrikePower@susaucav2 > Squad | susabomber.laser |
| mods/cameo/rules/shockwave.yaml | 1218, 1221, 1224 | ^ShockwaveUSASupportPowers > ClassicAirstrikePower@susaucav3 > Squad | susabomber.laser |
| mods/cameo/rules/shockwave.yaml | 3150, 3187 | susadecoydrone | Disguise |
| mods/cameo/rules/shockwave.yaml | 3833, 3876 | susaunstableeffects | RenderSprites |
| mods/cameo/rules/shockwave.yaml | 5370, 5377 | susaacolytedrone | RevealsShroud |
| mods/cameo/rules/shockwave.yaml | 5930, 5951 | susastarlifter | SpawnActorOnDeath |
| mods/cameo/rules/shockwave.yaml | 6621, 6624 | susaphalynx | Selectable |
| mods/cameo/rules/shockwave.yaml | 6992, 7003 | susamissilesilo | Selectable |
| mods/cameo/rules/shockwave.yaml | 7193, 7212, 7236 | susaamdggrenade.para | WithSpriteBody |
| mods/cameo/rules/shockwave.yaml | 7829, 7844 | sglairpad | Reservable |
| mods/cameo/rules/shockwave.yaml | 8336, 8347 | sglkatyusha | RenderSprites |
| mods/cameo/rules/shockwave.yaml | 8993, 9007 | sglmobilesupplytruck | RenderSprites |
| mods/cameo/rules/shockwave.yaml | 9337, 9352 | sglbadger | RenderSprites |
| mods/cameo/rules/shockwave.yaml | 12737, 12770 | schchaff | RenderSprites |
| mods/cameo/rules/shockwave.yaml | 14004, 14007 | schramjet | Selectable |
| mods/cameo/rules/shockwave.yaml | 15241, 15249 | schtankhunter_nuke | Valued |
| mods/cameo/rules/shockwave.yaml | 16452, 16474 | schsupplyhelicopterleang | SpawnActorOnDeath |
| mods/cameo/rules/simcity.yaml | 242, 245 | CITYTRUCK > Buildable | Prerequisites |
| mods/cameo/rules/simcity.yaml | 361, 370 | CITYFIRETRUCK | Voiced |
| mods/cameo/rules/simcity.yaml | 1669, 1676 | CITYFIREFIGHTER | Voiced |
| mods/cameo/rules/simcity.yaml | 1726, 1732 | CITYPOLICEOFFICER | Voiced |
| mods/cameo/rules/sow.yaml | 200, 203 | ^SowPowerBoost | ProductionTimeMultiplier@power5 |
| mods/cameo/rules/sow.yaml | 268, 276 | sowheadquarters | Armor |
| mods/cameo/rules/sow.yaml | 435, 438 | sowlightfactory | GrantConditionOnPrerequisite@2 |
| mods/cameo/rules/sow.yaml | 531, 542 | sowmediumfactory | GrantConditionOnDamageState |
| mods/cameo/rules/sow.yaml | 573, 576 | sowmediumfactory | GrantConditionOnPrerequisite@2 |
| mods/cameo/rules/sow.yaml | 640, 653 | sowheavyfactory | ProvidesPrerequisite@buildingname |
| mods/cameo/rules/sow.yaml | 695, 698 | sowheavyfactory | GrantConditionOnPrerequisite@2 |
| mods/cameo/rules/sow.yaml | 626, 631 | sowheavyfactory > Buildable | Prerequisites |
| mods/cameo/rules/sow.yaml | 762, 773 | sowabcfactory | ProvidesPrerequisite@buildingname |
| mods/cameo/rules/sow.yaml | 1042, 1045 | sowgoldmine | CashTricklerMultiplier@goldupgrade2 |
| mods/cameo/rules/sow.yaml | 1186, 1189 | sowpower | GrantConditionOnPrerequisite@sowpower |
| mods/cameo/rules/sow.yaml | 2690, 2700 | sow_ht_antiair | DetectCloaked |
| mods/cameo/rules/sow.yaml | 3070, 3084 | sow_mech_avenger | Voiced |
| mods/cameo/rules/sow.yaml | 3190, 3202 | sow_mech_kodiak | Voiced |
| mods/cameo/rules/sow.yaml | 3302, 3315 | sow_mech_gatling | Voiced |
| mods/cameo/rules/sow.yaml | 3422, 3434 | sow_mech_jaguar | Voiced |
| mods/cameo/rules/sow.yaml | 3547, 3559 | sow_mech_achilles | Voiced |
| mods/cameo/rules/sow.yaml | 4034, 4092 | sowfighter | RenderSprites |
| mods/cameo/rules/starwars.yaml | 207, 226 | ^SWFortressBuilding | Selectable |
| mods/cameo/rules/starwars.yaml | 3706, 3767 | swpalace | DetectCloaked |
| mods/cameo/rules/starwars.yaml | 3746, 3751 | swpalace | ProvidesPrerequisite@buildingname |
| mods/cameo/rules/starwars.yaml | 4307, 4315 | swindustrialplant | HitShape |
| mods/cameo/rules/starwars.yaml | 7116, 7123 | swexecutor.husk | RenderSprites |
| mods/cameo/rules/starwars.yaml | 8582, 8611 | swjabbaparty | Cargo |
| mods/cameo/rules/test.yaml | 547, 553 | TRIPOD | DeathSounds |
| mods/cameo/rules/tiberiaalliances.yaml | 1229, 1233 | tajugg | RenderVoxels |
| mods/cameo/rules/tiberiaalliances.yaml | 3468, 3470 | tagdiyard | RenderSprites |
| mods/cameo/rules/tiberiaalliances.yaml | 3661, 3667 | taelecyard | RenderSprites |
| mods/cameo/rules/tiberiaalliances.yaml | 4354, 4368 | tagdihq | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 4443, 4457 | tagdihq2 | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 4488, 4502 | tanodhq2 | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 4675, 4689 | tagdiskystrike | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 4742, 4756 | tagdifalcon | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 4827, 4841 | tagdiion | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 4899, 4913 | tanodbladeofkane | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 4966, 4980 | tanodeyeofkane | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 5051, 5065 | tafistofkane | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 5223, 5237 | tatacitus | RevealsShroud |
| mods/cameo/rules/tiberiaalliances.yaml | 5549, 5562 | tamgnod | RenderVoxels |
| mods/cameo/rules/valentine.yaml | 91, 94 | LOVECRATE | GiveCashCrateAction@1 |
| mods/cameo/rules/valentine.yaml | 742, 749 | valentines_sc2kmarina | HitShape |
| mods/cameo/rules/valentine.yaml | 1645, 1649 | valovecraft | WithAmmoPipsDecoration |
| mods/cameo/rules/valentine.yaml | 1830, 1834 | giantcupido | WithAmmoPipsDecoration |
| mods/cameo/rules/valentine.yaml | 2384, 2387 | valentines_teletubby_po | Explodes@6 |
| mods/cameo/rules/valentine.yaml | 2553, 2557 | valentines_dd | WithAmmoPipsDecoration |
| mods/cameo/rules/warcraft1.yaml | 261, 324 | wc_h_townhall | BaseBuilding |
| mods/cameo/rules/warcraft1.yaml | 568, 613 | wc_h_lumbermill | ProvidesPrerequisite |
| mods/cameo/rules/warcraft1.yaml | 1412, 1415 | wc_h_mcv.bot > Buildable | Prerequisites |
| mods/cameo/rules/warcraft1.yaml | 1742, 1756 | wc_h_cleric | AutoTarget |
| mods/cameo/rules/wh40k.yaml | 734, 737 | wh40kstrategyo | WithSpriteTurret@addon2 |
| mods/cameo/rules/wh40k.yaml | 2070, 2076 | ^WH40KGuardArmorUpgrade | DamageMultiplier@wh40kupguardarmor |
| mods/cameo/rules/wh40k.yaml | 2613, 2647 | wh40kcommisair | Health |
| mods/cameo/rules/wh40k.yaml | 3098, 3103 | wh40kpsyker | AutoTarget |
| mods/cameo/rules/wh40k.yaml | 8526, 8549 | wh40kgretchin | AutoTarget |
| mods/cameo/rules/wh40k.yaml | 11740, 11746 | wh40kraptor2 | WithDecoration@addon |
| mods/cameo/rules/win98.yaml | 75, 121 | WIN98_MYCOMPUTER | BaseBuilding |
| mods/cameo/rules/win98.yaml | 182, 188 | WIN98_BARRACKS > Buildable | Prerequisites |
| mods/cameo/rules/win98.yaml | 245, 258 | WIN98_RECYCLEBIN | Selectable |
| mods/cameo/rules/win98.yaml | 311, 365 | WIN98_INPUT_DEVICES | ProvidesPrerequisite |
| mods/cameo/rules/win98.yaml | 313, 319 | WIN98_INPUT_DEVICES > Buildable | Prerequisites |
| mods/cameo/rules/win98.yaml | 388, 390 | WIN98_POWERPLANTADVANCED > Buildable | Prerequisites |
| mods/cameo/rules/win98.yaml | 421, 428 | WIN98_AQUANET | HitShape |
| mods/cameo/rules/win98.yaml | 942, 946 | WIN98_HARDWARE | Voiced |
| mods/cameo/rules/win98.yaml | 1550, 1552 | WIN98_KEYBOARD > Buildable | Prerequisites |
| mods/cameo/rules/win98.yaml | 1583, 1590 | WIN98_BITCOIN | WithInfantryBody |
| mods/cameo/rules/win98.yaml | 1620, 1630 | WIN98_MSN_BUTTERFLY | AttackAircraft |
| mods/cameo/rules/worms.yaml | 1417, 1444 | WTRUCK | Voiced |
| mods/cameo/rules/wz2100.yaml | 1126, 1145 | 2100WALL | Selectable |
| mods/cameo/rules/wz2100.yaml | 1342, 1349 | 2100FB | AttackTurreted |
| mods/cameo/rules/wz2100.yaml | 1421, 1431 | 2100RADT | RevealsShroud |
| mods/cameo/rules/wz2100.yaml | 1963, 2015 | 2100CHOPSHOPADV | ProvidesPrerequisite |
| mods/cameo/rules/wz2100.yaml | 4144, 4148 | 2100MCV.ALPHA | RenderSprites |
| mods/cameo/rules/wz2100.yaml | 4117, 4119 | 2100MCV.ALPHA > Buildable | Prerequisites |
| mods/cameo/rules/wz2100.yaml | 4707, 4711 | 2100CYCAN > Buildable | Prerequisites |
| mods/cameo/rules/xcom.yaml | 985, 998 | large_gun_turret.xcom | AttackTurreted |
| mods/cameo/rules/xcom.yaml | 1181, 1203 | xcom_drmn | RenderSprites |
| mods/cameo/rules/xcom.yaml | 1183, 1199 | xcom_drmn | Mobile |
| mods/cameo/rules/xcom.yaml | 1191, 1205 | xcom_drmn | DockClientManager |
| mods/cameo/rules/xmas.yaml | 51, 54 | XMASCRATE | GiveCashCrateAction@1 |
| mods/cameo/rules/xmas.yaml | 90, 95 | EVILCRATE | GiveUnitCrateAction |
| mods/cameo/rules/z.yaml | 1072, 1079 | zfort | ProvidesPrerequisite@buildingname |
| mods/cameo/sequences/advancewars.yaml | 408, 411, 416 | awmegatnk | Scale |
| mods/cameo/sequences/d2k.yaml | 1317, 1318 | hightech.harkonnen | Defaults |
| mods/cameo/sequences/d2k.yaml | 2241, 2242 | d2k_editor-overlay | Defaults |
| mods/cameo/sequences/d2k.yaml | 2519, 2520 | d2k_shroud | Defaults |
| mods/cameo/sequences/generals.yaml | 139, 142 | glamob | stand |
| mods/cameo/sequences/infected.yaml | 26, 29 | civzombie | stand |
| mods/cameo/sequences/infected.yaml | 93, 97 | zombiee6 | idle |
| mods/cameo/sequences/infected.yaml | 100, 103 | zombiee6 | stand |
| mods/cameo/sequences/iok.yaml | 329, 331 | iokpalace | Defaults |
| mods/cameo/sequences/lostunits.yaml | 28, 31 | rathf | die5 |
| mods/cameo/sequences/misc.yaml | 1493, 1497 | resources | ra2gold18 |
| mods/cameo/sequences/misc.yaml | 3572, 3581 | overlay | target-select |
| mods/cameo/sequences/n64.yaml | 631, 633 | n64gtwr > make > Combine | gtwrmake |
| mods/cameo/sequences/redalert2.yaml | 3735, 3741 | yrslav | cheer |
| mods/cameo/sequences/redalert2.yaml | 3867, 3871 | ra2howi | muzzle |
| mods/cameo/sequences/redalert2.yaml | 3880, 3884 | ra2arty | muzzle |
| mods/cameo/sequences/shared_effects.yaml | 232, 237 | tscloud1 | Filename |
| mods/cameo/sequences/starwars.yaml | 1016, 1018 | swgtwr > make > Combine | gtwrmake |
| mods/cameo/sequences/starwars.yaml | 1143, 1145 | swtmpl | Defaults |
| mods/cameo/sequences/starwars.yaml | 2472, 2475 | swjedi | die5 |
| mods/cameo/sequences/structures.yaml | 501, 503 | td_gdi_guardtower > make > Combine | gtwrmake |
| mods/cameo/sequences/tiberiandawn.yaml | 1485, 1488 | gdirigtower | muzzle |
| mods/cameo/sequences/warcraft1.yaml | 1368, 1374, 1383 | wc_n_portal | Scale |
| mods/cameo/tilesets/arrakis.yaml | 8238, 8244 | MultiBrushCollections > Segmented | MultiBrush@161 |
| mods/cameo/tilesets/snow.yaml | 2518, 2519 | Templates > Template@2086 > Tiles | 1 |
| mods/cameo/weapons/advacewars.yaml | 265, 267 | AWGarrisonMG | Warhead@2Eff |
| mods/cameo/weapons/advacewars.yaml | 1083, 1085 | AWTeslaCrystal | Range |
| mods/cameo/weapons/advacewars.yaml | 1150, 1152 | AWLaserTurretRailgun | Warhead@1Dam |
| mods/cameo/weapons/advancewars.yaml | 259, 261 | AWGarrisonMG | Warhead@2Eff |
| mods/cameo/weapons/advancewars.yaml | 1068, 1070 | AWTeslaCrystal | Range |
| mods/cameo/weapons/advancewars.yaml | 1136, 1138 | AWLaserTurretRailgun | Warhead@1Dam |
| mods/cameo/weapons/classicdoom.yaml | 74, 76 | WolfenGrooseMinigun | Warhead@1Dam |
| mods/cameo/weapons/classicdoom.yaml | 92, 94 | WolfenMechaHetlerMinigun | Warhead@1Dam |
| mods/cameo/weapons/classicdoom.yaml | 101, 103 | WolfenMechaHetlerMinigun2 | Warhead@1Dam |
| mods/cameo/weapons/classicdoom.yaml | 250, 255 | WolfenSchabbsMutate | Report |
| mods/cameo/weapons/generals.yaml | 1796, 1799 | USACrusaderCannon | Report |
| mods/cameo/weapons/generals.yaml | 1805, 1808 | USAPaladinCannon | Report |
| mods/cameo/weapons/lostunits.yaml | 278, 283 | InfantryExplode | Warhead@3Clust |
| mods/cameo/weapons/monsters.yaml | 792, 798 | MothershipExplosion | Warhead@11Dam_areanuke3 |
| mods/cameo/weapons/other.yaml | 1186, 1192 | MothershipExplosion | Warhead@11Dam_areanuke3 |
| mods/cameo/weapons/redalert2.yaml | 2723, 2731 | LightningBolt | Warhead@TeslaChargedExtraDamage |
| mods/cameo/weapons/shockwave.yaml | 1907, 1922 | SGLAngryMobMolotov | Warhead@3Eff |
| mods/cameo/weapons/sow.yaml | 28, 36 | ^SowFlame | ValidTargets |
| mods/cameo/weapons/starcraft2.yaml | 7, 18 | zealotPsionicBlades > Warhead@1Dam | Spread |
| mods/cameo/weapons/starcraft2.yaml | 8, 19 | zealotPsionicBlades > Warhead@1Dam | Damage |
| mods/cameo/weapons/starcraft2.yaml | 9, 21 | zealotPsionicBlades > Warhead@1Dam | Versus |
| mods/cameo/weapons/starwars.yaml | 814, 818 | SWNapalm | Burst |
| mods/cameo/weapons/starwars.yaml | 843, 847 | SWNapalm2 | Burst |
| mods/cameo/weapons/starwars.yaml | 867, 871 | SWNapalm3 | Burst |
| mods/cameo/weapons/wh40k.yaml | 354, 357 | WH40KShootaBoyzGun | Warhead@1Dam |


**FAIL** — D2 count 261 exceeds the baseline 260: a new duplicate key was introduced.

