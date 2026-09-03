# audit_duplicate_keys — duplicate keys in one node (silent override)

Files scanned: **635** — D1 dropped inherits: **88**, D2 merged duplicates: **439**


## D1 — duplicate Inherits key with different values (one template is dropped)

| file | lines | node | key | values |
|---|---|---|---|---|
| mods/cameo/audio/d2k.yaml | 30, 31 | D2KGenericVoice | Inherits | ^D2KAudioDefaults vs ^D2KInfantryDeath |
| mods/cameo/audio/d2k.yaml | 51, 52 | D2KInfantryVoice | Inherits | ^D2KAudioDefaults vs ^D2KInfantryDeath |
| mods/cameo/audio/d2k.yaml | 79, 80 | D2KFremenVoice | Inherits | ^D2KAudioDefaults vs ^D2KInfantryDeath |
| mods/cameo/audio/d2k.yaml | 93, 94 | D2KSaboteurVoice | Inherits | ^D2KAudioDefaults vs ^D2KInfantryDeath |
| mods/cameo/chrome.yaml | 2659, 2660 | sidebar-swempire | Inherits | sidebar-allies vs ^SidebarStarWars |
| mods/cameo/chrome.yaml | 2684, 2685 | sidebar-swrebels | Inherits | sidebar-soviets vs ^SidebarStarWars |
| mods/cameo/chrome.yaml | 2711, 2712 | sidebar-swseparatist | Inherits | sidebar-allies vs ^SidebarStarWars2 |
| mods/cameo/chrome.yaml | 2736, 2737 | sidebar-swhutt | Inherits | sidebar-soviets vs ^SidebarStarWars2 |
| mods/cameo/ContentPacks/D2k/Harkonnen/yaml/buildings.yaml | 202, 203 | harkonnen_repairpad | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/D2k/Ixian/yaml/buildings.yaml | 283, 284 | ixian_repairpad | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/buildings.yaml | 336, 337 | ordos_repairpad | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/RedAlert/Japan/yaml/defenses.yaml | 221, 222 | japan_waveforceturret | Inherits@AntiTank | ^PrioritizeVehicle vs ^PrioritizeTank |
| mods/cameo/ContentPacks/RedAlert/Japan/yaml/templates.yaml | 432, 433 | ^RAFIX | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/buildings.yaml | 14, 15 | ra1_soviets_barracks | Inherits@ra1_soviets_barracks | ^IsBarrack vs ^Conscription |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 1948, 1950 | HammerTankCannonThermobaric | Inherits@3 | ^Projectile_Flame_Medium vs HammerTankCannon |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 2053, 2055 | KotinCannonThermobaric | Inherits@3 | ^Projectile_Flame_Medium vs KotinCannon |
| mods/cameo/ContentPacks/RedAlert2/Allies/yaml/buildings.yaml | 255, 256 | ra2_allies_alliedservicedepot | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/buildings.yaml | 246, 247 | ra2_soviets_servicedepot | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/buildings.yaml | 161, 162 | asianalliance_asianservicedepot | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/RedAlert2Mod/Naxis/yaml/buildings.yaml | 545, 553 | naxis_naxibunker | Inherits | ^RA2Defense vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/aircraft.yaml | 200, 201 | latinsyndicate_mig21 | Inherits@flamerup | ^CartelRocketsUpgrade vs ^LatinFlameUpgrades |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/buildings.yaml | 554, 555 | latinsyndicate_syndicateservicedepot | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 955, 956 | latinsyndicate_missiletruck | Inherits@flamerup | ^CartelRocketsUpgrade vs ^LatinFlameUpgrades |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 1026, 1027 | latinsyndicate_burrito | Inherits@flamerup | ^CartelRocketsUpgrade vs ^LatinFlameUpgrades |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 1095, 1096 | latinsyndicate_lars | Inherits@flamerup | ^CartelRocketsUpgrade vs ^LatinFlameUpgrades |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/buildings.yaml | 69, 73 | tkm_orerefinery | Inherits | ^RA2Building vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/buildings.yaml | 205, 207 | tkm_airpad | Inherits@shape | ^4x3Shape vs ^3x3Shape |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/defenses.yaml | 199, 202 | tkmratflakdeployed | Inherits@Template | ^BasicDefenseTemplate vs ^AntiAirDefenseTemplate |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml | 689, 690 | tkmkatyushalalauncherrocketsfire | Inherits@3 | ^Effect_Flame_Light vs tkmkatyushalalauncherrockets |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml | 791, 795 | SandmarineTuskFire | Inherits | ^Warhead_MissileAP_Light vs SandmarineTusk |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml | 842, 846 | ViperMissilesFire | Inherits | ^Warhead_MissileAP_Light vs ViperMissiles |
| mods/cameo/ContentPacks/StarCraft/Protoss/yaml/buildings.yaml | 137, 142 | protoss_assimilator | Inherits | ^BaseBuildingProtoss vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/StarCraft/Terran/yaml/aircraft.yaml | 455, 456 | terran_pythean | Inherits@weapon | ^TerranVehicleArmorUpgrades vs ^TerranShipArmorUpgrades |
| mods/cameo/ContentPacks/StarCraft/Terran/yaml/aircraft.yaml | 543, 544 | terran_medivac | Inherits@weapon | ^TerranShipArmorUpgrades vs ^TerranInfantryArmorUpgrades |
| mods/cameo/ContentPacks/StarCraft/Terran/yaml/buildings.yaml | 83, 87 | terran_supplydepot | Inherits | ^BaseBuilding vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/StarCraft/Terran/yaml/buildings.yaml | 173, 176 | terran_refinery | Inherits | ^BaseBuilding vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/buildings.yaml | 225, 228 | zerg_extractor | Inherits | ^BaseBuildingZerg vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/buildings.yaml | 514, 517 | zerg_spire | Inherits | ^BaseBuildingZerg vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/defenses.yaml | 2, 12 | zerg_creepcolony | Inherits | ^Defense vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/buildings.yaml | 189, 190 | td_gdi_repairfacility | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/buildings.yaml | 218, 226 | td_gdi_advancedcommunicationscenter | Inherits | ^TDBuilding vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/buildings.yaml | 442, 443 | td_gdi_advancedguardtower | Inherits@AntiTank | ^PrioritizeVehicle vs ^PrioritizeTank |
| mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/buildings.yaml | 199, 200 | td_nod_repairfacility | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/buildings.yaml | 228, 236 | td_nod_templeofnod | Inherits | ^TDBuilding vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/vehicles.yaml | 526, 531 | td_nod_chemicalattackbike | Inherits | ^Vehicle vs ^GenericGroundDetector |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/buildings.yaml | 216, 217 | cabal_servicedepot | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/infantry.yaml | 767, 768 | cabal_cyborgcommando | Inherits@Template | ^HeavyInfantryTemplate vs ^HeroInfantryTemplate |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/infantry.yaml | 854, 855 | cabal_cyborgcommandov2 | Inherits@Template | ^HeavyInfantryTemplate vs ^HeroInfantryTemplate |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/infantry.yaml | 943, 949 | cabal_eliminator800 | Inherits@EXPERIENCE | ^GainsExperienceTD vs ^GainsExperienceRA2 |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/buildings.yaml | 272, 273 | forgotten_servicedepot | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/buildings.yaml | 118, 122 | ts_gdi_powerplant | Inherits | ^BaseBuilding vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/buildings.yaml | 322, 323 | ts_gdi_servicedepot | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 531, 532, 533 | TSDestroyerMissiles | Inherits | ^FlakWeapon vs ^MediumMissile vs ^ShrapnelWeapon |
| mods/cameo/ContentPacks/TiberianSun/Nod/yaml/buildings.yaml | 362, 363 | ts_nod_servicedepot | Inherits@repair | ^RepairsUnits vs ^RepairFacility |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/defenses.yaml | 2, 10 | wc2_humans_humanscouttower | Inherits | ^Defense vs ^BuildingPlugProducer |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/defenses.yaml | 2, 10 | wc2_orcs_orcwatchtower | Inherits | ^Defense vs ^BuildingPlugProducer |
| mods/cameo/rules/advancewars.yaml | 4608, 4610 | awcity | Inherits | OILB.Building vs ^BaseBuilding |
| mods/cameo/rules/darkreign.yaml | 366, 367 | drwaterextract.freedomguard | Inherits@2 | ^BaseBuilding vs ^CashTricklerMultipliers |
| mods/cameo/rules/darkreign.yaml | 8627, 8631 | drahq.eodalien | Inherits | ^BaseBuilding vs ^Conyard |
| mods/cameo/rules/defaults.yaml | 1578, 1579 | ^ScoutVehicleTemplate | Inherits@upgrade | ^LightWeightArmorPlating vs ^AdvancedGuerillaTactics |
| mods/cameo/rules/defaults.yaml | 1600, 1601 | ^SupportVehicleTemplate | Inherits@upgrade | ^LightWeightArmorPlating vs ^AdvancedGuerillaTactics |
| mods/cameo/rules/defaults.yaml | 2407, 2410 | ^BasicUnit | Inherits@cloak | ^AcceptsCloakCrate vs ^StealthGenCloakable |
| mods/cameo/rules/generals.yaml | 2502, 2504 | glblackmarket | Inherits | OILB.Building vs ^BaseBuilding |
| mods/cameo/rules/generals.yaml | 11876, 11878 | usadropzone | Inherits | OILB.Building vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 586, 591 | CITYR | Inherits@2 | ^BaseBuilding vs ^CashTricklerMultipliers |
| mods/cameo/rules/simcity.yaml | 923, 925 | CITYHARBOR | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1041, 1043 | CITYAIRPORT | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1192, 1194 | CITYLIBRARY | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1222, 1224 | CITYBANK | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1265, 1267 | CITYPARK | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1296, 1298 | CITYFOUNTAIN | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1327, 1329 | CITYSTADIUM | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1355, 1357 | CITYEXPO | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1381, 1383 | CITYSTATION | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1439, 1441 | CITYMARIO | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1467, 1469 | CITYCASINO | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1526, 1528 | CITYWINDMILL | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1551, 1553 | CITYAMUSE | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/simcity.yaml | 1576, 1578 | CITYZOO | Inherits | SimCityBuildingLevelUp vs ^BaseBuilding |
| mods/cameo/rules/sow.yaml | 960, 962 | sowgoldmine | Inherits | OILB.Building vs ^BaseBuilding |
| mods/cameo/rules/wz2100.yaml | 307, 310 | 2100OIL | Inherits | OILB.Building vs ^BaseBuilding |
| mods/cameo/rules/wz2100.yaml | 1193, 1194 | 2100WCMG | Inherits@AUTOTARGET | ^2100WallTurreted vs ^AutoTargetAll |
| mods/cameo/rules/wz2100.yaml | 1214, 1215 | 2100WCL | Inherits@AUTOTARGET | ^2100WallTurreted vs ^AutoTargetGround |
| mods/cameo/rules/wz2100.yaml | 1232, 1233 | 2100WCM | Inherits@AUTOTARGET | ^2100WallTurreted vs ^AutoTargetGround |
| mods/cameo/rules/wz2100.yaml | 1252, 1253 | 2100WCH | Inherits@AUTOTARGET | ^2100WallTurreted vs ^AutoTargetGround |
| mods/cameo/rules/xcom.yaml | 588, 597 | XCOMHQ | Inherits | ^BaseBuilding vs ^CashTricklerMultipliers |
| mods/cameo/weapons/redalert2mod.yaml | 1278, 1280 | 12MissilesSpawnerScud | Inherits@3 | ^Projectile_Flame_Medium vs ^RA2Grenade |
| mods/cameo/weapons/redalert2mod.yaml | 1279, 1281 | 12MissilesSpawnerScud | Inherits@4 | ^Effect_Flame_Medium vs ^RA2HeavyMissile |


## D2 — duplicate keys by key name (top 40)

| key | occurrences |
|---|---|
| RenderSprites | 40 |
| Selectable | 28 |
| ActorStatValues | 18 |
| Voiced | 17 |
| ProvidesPrerequisite@buildingname | 16 |
| RevealsShroud | 14 |
| Report | 13 |
| Prerequisites | 11 |
| Defaults | 10 |
| HitShape | 8 |
| AutoTarget | 7 |
| WithDeathAnimation | 6 |
| ProvidesPrerequisite | 6 |
| muzzle | 6 |
| ValidTargets | 6 |
| Warhead@1Dam | 6 |
| AttackTurreted | 5 |
| WithAmmoPipsDecoration | 5 |
| SpawnActorOnDeath | 5 |
| WithSpriteTurret | 5 |
| DamagedByTerrain@TiberiumHeal | 5 |
| Power | 5 |
| cheer | 4 |
| AttackAircraft | 4 |
| Mobile | 4 |
| WithMuzzleOverlay | 3 |
| WithInfantryBody | 3 |
| ReloadDelay | 3 |
| AttackFrontal | 3 |
| WithMoveAnimation | 3 |
| StoresResources | 3 |
| DockClientManager | 3 |
| Projectile | 3 |
| DeathSounds | 3 |
| Range | 3 |
| RenderVoxels | 3 |
| Building | 3 |
| Health | 3 |
| GrantConditionOnPrerequisite@2 | 3 |
| stand | 3 |


## D2 — full list

| file | lines | node | key |
|---|---|---|---|
| mods/cameo/chrome/ingame_observer.yaml | 316, 320 | Container@OBSERVER_WIDGETS > Children > Image@REPLAY_PLAYER | Visible |
| mods/cameo/chrome/settings_display.yaml | 26, 80, 110, 141, 165, 191, 206, 228, 283, 344, 386, 399, 431, 444, 457, 470, 483, 496, 509 | Container@DISPLAY_PANEL > Children > ScrollPanel@SETTINGS_SCROLLPANEL > Children | Container@ROW |
| mods/cameo/chrome/settings_display.yaml | 66, 269 | Container@DISPLAY_PANEL > Children > ScrollPanel@SETTINGS_SCROLLPANEL > Children | Container@SPACER |
| mods/cameo/ContentPacks/D2k/Ixian/yaml/buildings.yaml | 731, 744 | ixian_rocketturret | AttackTurreted |
| mods/cameo/ContentPacks/D2k/Ixian/yaml/buildings.yaml | 1140, 1161 | ixian_stormlasher | WithMuzzleOverlay |
| mods/cameo/ContentPacks/D2k/Ixian/yaml/buildings.yaml | 1141, 1159 | ixian_stormlasher | WithSpriteBody |
| mods/cameo/ContentPacks/D2k/Ixian/yaml/vehicles.yaml | 1165, 1176 | ixian_ixcombatsiege | ActorStatValues |
| mods/cameo/ContentPacks/D2k/Ixian/yaml/vehicles.yaml | 1591, 1606 | duelist_tank.ixian | ActorStatValues |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/aircraft.yaml | 89, 142 | ordos_airmine | AutoTarget |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/aircraft.yaml | 945, 955 | carryall_huskvtol.ordos | FallsToEarth |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/sequences.yaml | 520, 521 | hightech.ordos | Defaults |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/sequences.yaml | 958, 982 | ordos_leech | die4 |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/vehicles.yaml | 817, 866 | ordos_cobratank | RangeMultiplier@deployed |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/vehicles.yaml | 933, 975 | ordos_pythontank | RangeMultiplier@deployed |
| mods/cameo/ContentPacks/D2k/Shared/yaml/aircraft.yaml | 160, 170 | carryall.huskVTOL | FallsToEarth |
| mods/cameo/ContentPacks/D2k/Shared/yaml/infantry.yaml | 239, 241 | engineer | ActorStatValues |
| mods/cameo/ContentPacks/D2k/Shared/yaml/templates.yaml | 229, 266 | ^D2KInfantry | Passenger |
| mods/cameo/ContentPacks/RedAlert/Allies/yaml/defenses.yaml | 209, 213 | ra1_allies_pillbox | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert/Allies/yaml/defenses.yaml | 392, 396 | ra1_allies_camopillbox | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert/Japan/yaml/buildings.yaml | 50, 56 | japan_waveforcereactor | WithDeathAnimation |
| mods/cameo/ContentPacks/RedAlert/Japan/yaml/infantry.yaml | 111, 121 | japan_tankbuster | WithInfantryBody |
| mods/cameo/ContentPacks/RedAlert/Japan/yaml/infantry.yaml | 144, 187 | japan_japaneseflamethrower | UpdatesPlayerStatistics |
| mods/cameo/ContentPacks/RedAlert/Japan/yaml/templates.yaml | 389, 406 | ^RAPROC | WithDeathAnimation |
| mods/cameo/ContentPacks/RedAlert/Shared/yaml/buildings.yaml | 33, 39 | ra1_powerplant | WithDeathAnimation |
| mods/cameo/ContentPacks/RedAlert/Shared/yaml/buildings.yaml | 76, 83 | ra1_advancedpowerplant | WithDeathAnimation |
| mods/cameo/ContentPacks/RedAlert/Shared/yaml/infantry.yaml | 222, 224 | ra1_engineer | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml | 349, 357 | ReimuOrbLauncher | Warhead@Shrapnel3 |
| mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml | 419, 428 | MagicOrbHailstormSpawner | Warhead@Shrapnel3 |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/buildings.yaml | 33, 35 | ra1_soviets_barracks | ProvidesPrerequisite |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/infantry.yaml | 731, 737 | ra1_soviets_commissar | WithDecoration@Carryall |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/vehicles.yaml | 1759, 1762 | ra1_soviets_monstertank | WithAmmoPipsDecoration |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 911, 913 | FLAK-23-AG | ReloadDelay |
| mods/cameo/ContentPacks/RedAlert2/Allies/yaml/aircraft.yaml | 155, 170 | ra2_allies_blackeagle | Selectable |
| mods/cameo/ContentPacks/RedAlert2/Allies/yaml/defenses.yaml | 266, 270 | ra2_allies_pillbox | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert2/Allies/yaml/infantry.yaml | 378, 380 | ra2_allies_guardiangi | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert2/Allies/yaml/sequences.yaml | 11, 37 | ra2_allies_alliedconstructionyard | dead |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 776, 796 | ra2sqd | AttackFrontal |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 889, 929 | ra2dest | Selectable |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 1361, 1369 | yrbpln | Contrail@1 |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 1364, 1375 | yrbpln | Contrail@2 |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 1367, 1384 | yrbpln | SpawnActorOnDeath |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 2166, 2168 | ra2sidewind | Voiced |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/sequences.yaml | 3731, 3737 | yrslav | cheer |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/sequences.yaml | 3870, 3874 | ra2howi | muzzle |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/sequences.yaml | 3883, 3887 | ra2arty | muzzle |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/aircraft.yaml | 317, 325, 333 | ra2_soviets_migbomber | Armament@PRIMARYELITERad |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/defenses.yaml | 190, 208 | ra2_soviets_battlebunker | Selectable |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/infantry.yaml | 493, 497 | ra2_soviets_teslatrooper | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/infantry.yaml | 637, 640 | ra2_soviets_boris | WithInfantryBody |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/buildings.yaml | 144, 146 | yuri_bioreactor | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/sequences.yaml | 4, 45 | yuri_constructionyard | build |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/vehicles.yaml | 485, 536 | yuri_mastermind | AttackTurreted |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/aircraft.yaml | 305, 336 | kami.asian | WithMoveAnimation |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/buildings.yaml | 775, 782 | asianalliance_chaostower | Selectable |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/naval.yaml | 434, 436 | tsun.asian | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/sequences.yaml | 11, 31 | asianalliance_asianconstructionyard | dead |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/sequences.yaml | 1275, 1304 | asianalliance_asianflametrooper | shoot |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/sequences.yaml | 1288, 1301 | asianalliance_asianflametrooper | cheer |
| mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/vehicles.yaml | 744, 778 | steelconsortium_consortiumminer | StoresResources |
| mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/vehicles.yaml | 764, 779 | steelconsortium_consortiumminer | DockClientManager |
| mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/vehicles.yaml | 928, 930 | steelconsortium_quantumtank | Selectable |
| mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml | 72, 79 | SteelVulcan | Report |
| mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml | 545, 547 | SteelMantaHunterCannons | ValidTargets |
| mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml | 1168, 1176 | SteelFortressWeapons | Report |
| mods/cameo/ContentPacks/RedAlert2Mod/FutureTech/yaml/buildings.yaml | 494, 563 | futuretech_multiturretsystem | AttackTurreted |
| mods/cameo/ContentPacks/RedAlert2Mod/FutureTech/yaml/weapons.yaml | 484, 485 | Future_CoilerFriend | Projectile |
| mods/cameo/ContentPacks/RedAlert2Mod/Naxis/yaml/aircraft.yaml | 49, 82 | naxis_interceptor | WithMoveAnimation |
| mods/cameo/ContentPacks/RedAlert2Mod/Naxis/yaml/buildings.yaml | 575, 593 | naxis_naxibunker | Selectable |
| mods/cameo/ContentPacks/RedAlert2Mod/Naxis/yaml/buildings.yaml | 595, 624 | naxis_naxibunker | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert2Mod/Naxis/yaml/sequences.yaml | 930, 936 | naxis_slave | cheer |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/aircraft.yaml | 43, 80 | schwarzermond_drone | WithMoveAnimation |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/vehicles.yaml | 776, 787 | schwarzermond_komet | WithFacingSpriteBody@EMPTY |
| mods/cameo/ContentPacks/RedAlert2Mod/Shared/yaml/templates.yaml | 485, 491 | ^SteelConsortiumNaniteInfusion | ChangesHealth@steelconsortium_upgrade_naniteinfusion |
| mods/cameo/ContentPacks/RedAlert2Mod/Shared/yaml/templates.yaml | 507, 509 | ^SteelConsortiumNaniteInfusionInfantry | ChangesHealth@steelconsortium_upgrade_naniteinfusion |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/buildings.yaml | 71, 100 | latinsyndicate_combatbarracks | GivesBuildableArea |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/buildings.yaml | 278, 286 | latinsyndicate_spycenter | SupportPowerChargeBar |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/buildings.yaml | 280, 283 | latinsyndicate_spycenter | WithIdleOverlay@lights |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/buildings.yaml | 365, 388 | latinsyndicate_defensebureau | GivesBuildableArea |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/sequences.yaml | 525, 583 | latinsyndicate_topolsilo | critical-idle |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 601, 621 | latinsyndicate_diablo | WithSpriteTurret |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 763, 773 | latinsyndicate_latinapc | WithSpriteTurret |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 848, 860 | latinsyndicate_narcohummer | WithSpriteTurret |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 929, 941 | latinsyndicate_carteltruck | WithSpriteTurret |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 1192, 1199 | latinsyndicate_collectiontruck | StoresResources |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 1379, 1428 | latinsyndicate_topolm | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 593, 600 | RA2GrenadePack | Report |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/buildings.yaml | 212, 236 | tkm_airpad | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/buildings.yaml | 245, 258 | tkm_observationvan | Selectable |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/buildings.yaml | 280, 289 | tkm_techcenter | Selectable |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/infantry.yaml | 402, 442 | tkm_rocketeer | Armament@GARRISONED |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/infantry.yaml | 545, 562 | tkm_engineer | RenderRangeCircleCA |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/vehicles.yaml | 143, 148 | tkm_as42 | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/vehicles.yaml | 271, 286 | tkm_technicaltank | Selectable |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/vehicles.yaml | 534, 549 | tkm_abrams | Selectable |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/vehicles.yaml | 616, 632 | tkm_t72m | Selectable |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/vehicles.yaml | 678, 684 | tkm_trenchtruck | Selectable |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/vehicles.yaml | 740, 758 | tkm_tornadoglauncher | ActorStatValues |
| mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/vehicles.yaml | 1034, 1040 | tkm_trenchtank | Selectable |
| mods/cameo/ContentPacks/StarCraft/Protoss/yaml/buildings.yaml | 16, 69 | protoss_nexus | Selectable |
| mods/cameo/ContentPacks/StarCraft/Protoss/yaml/sequences.yaml | 503, 505 | protoss_arbiter | idle |
| mods/cameo/ContentPacks/StarCraft/Protoss/yaml/templates.yaml | 26, 39 | ^SCWorker | StoresResources |
| mods/cameo/ContentPacks/StarCraft/Terran/yaml/aircraft.yaml | 799, 849 | terran_phobos | DeathSounds |
| mods/cameo/ContentPacks/StarCraft/Terran/yaml/defenses.yaml | 165, 182 | terran_sentinel | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/aircraft.yaml | 712, 717 | zerg_behemoth | ActorStatValues |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/aircraft.yaml | 13, 18 | td_gdi_chinooktransport | Buildable |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/aircraft.yaml | 444, 478 | gdirigdrone | AttackAircraft |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/buildings.yaml | 35, 53 | td_gdi_barracks | ProvidesPrerequisite |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/sequences.yaml | 388, 394 | td_gdi_advancedguardtower | muzzle |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/vehicles.yaml | 1150, 1224 | td_gdi_defenserig | WithMuzzleOverlay |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/vehicles.yaml | 1189, 1201 | td_gdi_defenserig | RejectsOrders@deployment |
| mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/weapons.yaml | 452, 457 | Vulcan | ReloadDelay |
| mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/buildings.yaml | 48, 64 | td_nod_handofnod | ProvidesPrerequisite |
| mods/cameo/ContentPacks/TiberianDawn/Shared/yaml/infantry.yaml | 79, 81 | E6 | ActorStatValues |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/aircraft.yaml | 13, 56 | cabal_overkillgunship | Selectable |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/buildings.yaml | 117, 139 | cabal_cyborgfactory | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/buildings.yaml | 172, 194 | cabal_mechfactory | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/buildings.yaml | 527, 542 | cabal_core | Selectable |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/buildings.yaml | 554, 557 | cabal_core | WithIdleOverlay@LIGHTS2 |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/defenses.yaml | 11, 26 | cabal_silo | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/infantry.yaml | 222, 226 | cabal_rocketcyborg | DamagedByTerrain@TiberiumHeal |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/infantry.yaml | 340, 344 | cabal_devout | DamagedByTerrain@TiberiumHeal |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/infantry.yaml | 438, 487 | cabal_ascended | Armament@GARRISONED |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/infantry.yaml | 456, 460 | cabal_ascended | DamagedByTerrain@TiberiumHeal |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/infantry.yaml | 583, 587 | cabal_enlighted | DamagedByTerrain@TiberiumHeal |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/infantry.yaml | 708, 712 | cabal_hackercyborg | DamagedByTerrain@TiberiumHeal |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/vehicles.yaml | 8, 47 | cabal_constructionyard | Selectable |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/vehicles.yaml | 135, 155 | cabal_cyborgreaper | WithDeathAnimation |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/vehicles.yaml | 784, 805 | cabal_heavyreaper | WithDeathAnimation |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/infantry.yaml | 783, 800 | forgotten_visceroid | WithMuzzleOverlay |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/sequences.yaml | 62, 66 | forgotten_chemsprayinfantry | prone-shoot |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/sequences.yaml | 334, 375 | forgotten_zombiemutant | standup |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/sequences.yaml | 369, 384 | forgotten_zombiemutant | die-crushed |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 557, 562 | TSJuggerFlakAA_boat | Range |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 722, 727 | TSVanMissile | Report |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 743, 748 | TSChemVanMissile | Report |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 778, 783 | TSMLRSMissile | Report |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 799, 804 | TSChemMLRSMissile | Report |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 1874, 1876, 1878, 1881, 1882 | TSMutApcCannon | ValidTargets |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/buildings.yaml | 6, 41 | ts_gdi_constructionyard | Selectable |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/buildings.yaml | 215, 237 | ts_gdi_barracks | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/buildings.yaml | 269, 293 | ts_gdi_warfactory | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/buildings.yaml | 512, 523 | ts_gdi_techcenter | Selectable |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/buildings.yaml | 555, 570 | ts_gdi_silo | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/vehicles.yaml | 272, 288 | ts_gdi_titan | RenderVoxels |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 497, 502 | TSHoverMissile | Report |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 535, 540 | TSDestroyerMissiles | Report |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 598, 612 | TSMammothTusk2II_AA | Projectile |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 940, 942, 944, 947, 948 | TSAAPCCannon | ValidTargets |
| mods/cameo/ContentPacks/TiberianSun/Nod/yaml/buildings.yaml | 6, 41 | ts_nod_constructionyard | Selectable |
| mods/cameo/ContentPacks/TiberianSun/Nod/yaml/buildings.yaml | 265, 288 | ts_nod_handof | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/TiberianSun/Nod/yaml/buildings.yaml | 316, 340 | ts_nod_warfactory | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/TiberianSun/Nod/yaml/defenses.yaml | 11, 26 | ts_nod_silo | ProvidesPrerequisite@buildingname |
| mods/cameo/ContentPacks/TiberianSun/Nod/yaml/vehicles.yaml | 486, 537 | ts_nod_mobilestealthgenerator | ActorStatValues |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/buildings.yaml | 73, 75 | wc2_humans_townhall | WithSpriteBody@keep |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/buildings.yaml | 115, 132 | wc2_humans_townhall | Refinery |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/buildings.yaml | 450, 465 | wc2_humans_sunwell | Building |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/infantry.yaml | 38, 49 | wc2_humans_militiapeasant | Voiced |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/infantry.yaml | 421, 437 | wc2_humans_mortarteam | Mobile |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/sequences.yaml | 150, 153 | wc2_humans_guardtower | Defaults |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/sequences.yaml | 158, 161 | wc2_humans_cannontower | Defaults |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/sequences.yaml | 166, 168 | wc2_humans_wall | Defaults |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/vehicles.yaml | 134, 159 | wc2_humans_ballista | Mobile |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/weapons.yaml | 632, 646 | wc2blizzardSuper | Warhead@InitialSpreader10 |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/weapons.yaml | 639, 653 | wc2blizzardSuper | Warhead@InitialSpreader11 |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/buildings.yaml | 115, 132 | wc2_orcs_greathall | Refinery |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/sequences.yaml | 165, 167 | wc2_orcs_wall | Defaults |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/sequences.yaml | 583, 587 | wc2_orcs_ogre | idle-ogremage |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/templates.yaml | 245, 262 | ^WC2Blacksmith | Power |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/templates.yaml | 301, 322 | ^WC2Stables | Health |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/templates.yaml | 305, 326 | ^WC2Stables | Power |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/templates.yaml | 339, 356 | ^WC2Church | Power |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/vehicles.yaml | 93, 122 | wc2_orcs_catapult | Mobile |
| mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/weapons.yaml | 514, 519 | wc2dragonFireExplosion | Projectile |
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
| mods/cameo/rules/defaults.yaml | 2738, 2766 | ^Submarine | Targetable |
| mods/cameo/rules/defaults.yaml | 3616, 3630 | ^CivInfantry | Passenger |
| mods/cameo/rules/defaults.yaml | 3688, 3722 | ^Monster | CombatDebugOverlay |
| mods/cameo/rules/defaults.yaml | 4079, 4178 | ^BaseBuilding | RepairableBuilding |
| mods/cameo/rules/defaults.yaml | 4129, 4180 | ^BaseBuilding | WithBuildingRepairDecoration |
| mods/cameo/rules/defaults.yaml | 6856, 6912 | ^Harvester | DockClientManager |
| mods/cameo/rules/defaults.yaml | 6899, 6916 | ^Harvester | WithStoresResourcesPipsDecoration |
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
| mods/cameo/rules/misc.yaml | 977, 1012 | spicebloom | RenderSprites |
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
| mods/cameo/rules/shared.yaml | 123, 128 | ^InfectionGamemode | ChangesHealth |
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
| mods/cameo/rules/starcraft.yaml | 276, 278 | SCSENTINELM | RenderSprites |
| mods/cameo/rules/starcraft.yaml | 382, 425 | SCSPIDERMINE | AutoTarget |
| mods/cameo/rules/starcraft.yaml | 613, 615 | SCCOMMANDCENTERM | RenderSprites |
| mods/cameo/rules/starcraft.yaml | 630, 632 | SCBARRACKSM | RenderSprites |
| mods/cameo/rules/starcraft.yaml | 647, 649 | SCENGINEERINGBAYM | RenderSprites |
| mods/cameo/rules/starcraft.yaml | 664, 666 | SCFACTORYM | RenderSprites |
| mods/cameo/rules/starcraft.yaml | 681, 683 | SCSTARPORTM | RenderSprites |
| mods/cameo/rules/starcraft.yaml | 698, 700 | SCSCIENCEFACILITYM | RenderSprites |
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
| mods/cameo/rules/tiberiansun.yaml | 191, 205 | tsmonstermaker1 | SpawnActorOnDeath@monstermaker3 |
| mods/cameo/rules/tiberiansun.yaml | 266, 317 | TSGTCNST | Selectable |
| mods/cameo/rules/trees.yaml | 686, 693 | SNOWHUT | RenderSprites |
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
| mods/cameo/rules/warcraft2.yaml | 718, 726 | ^WC2Foundry | Valued |
| mods/cameo/rules/warcraft2.yaml | 720, 739 | ^WC2Foundry | Health |
| mods/cameo/rules/warcraft2.yaml | 724, 743 | ^WC2Foundry | Power |
| mods/cameo/rules/warcraft2.yaml | 1346, 1358 | wc2_orc_skeleton | Power |
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
| mods/cameo/weapons/d2k.yaml | 934, 938 | D2KRepair | Warhead@2Defuse |
| mods/cameo/weapons/d2k.yaml | 1177, 1181 | Fremen_S | Report |
| mods/cameo/weapons/d2k.yaml | 1601, 1621 | d2k_flame_tank | ValidTargets |
| mods/cameo/weapons/generals.yaml | 1796, 1799 | USACrusaderCannon | Report |
| mods/cameo/weapons/generals.yaml | 1805, 1808 | USAPaladinCannon | Report |
| mods/cameo/weapons/lostunits.yaml | 278, 283 | InfantryExplode | Warhead@3Clust |
| mods/cameo/weapons/monsters.yaml | 792, 798 | MothershipExplosion | Warhead@11Dam_areanuke3 |
| mods/cameo/weapons/other.yaml | 1186, 1192 | MothershipExplosion | Warhead@11Dam_areanuke3 |
| mods/cameo/weapons/redalert2.yaml | 2718, 2726 | LightningBolt | Warhead@TeslaChargedExtraDamage |
| mods/cameo/weapons/shockwave.yaml | 1907, 1922 | SGLAngryMobMolotov | Warhead@3Eff |
| mods/cameo/weapons/sow.yaml | 28, 36 | ^SowFlame | ValidTargets |
| mods/cameo/weapons/starcraft2.yaml | 7, 18 | zealotPsionicBlades > Warhead@1Dam | Spread |
| mods/cameo/weapons/starcraft2.yaml | 8, 19 | zealotPsionicBlades > Warhead@1Dam | Damage |
| mods/cameo/weapons/starcraft2.yaml | 9, 21 | zealotPsionicBlades > Warhead@1Dam | Versus |
| mods/cameo/weapons/starwars.yaml | 814, 818 | SWNapalm | Burst |
| mods/cameo/weapons/starwars.yaml | 843, 847 | SWNapalm2 | Burst |
| mods/cameo/weapons/starwars.yaml | 867, 871 | SWNapalm3 | Burst |
| mods/cameo/weapons/tiberiansun.yaml | 1237, 1239 | TSEngineerPistol | ReloadDelay |
| mods/cameo/weapons/warcraft2.yaml | 360, 371 | wc2demolitionsquadExplode | Warhead@Concrete |
| mods/cameo/weapons/warcraft2.yaml | 402, 407 | wc2mageBlizzard | ValidTargets |
| mods/cameo/weapons/weapons.yaml | 2958, 2963 | ^RepairWeapon | Warhead@Defuse1 |
| mods/cameo/weapons/wh40k.yaml | 354, 357 | WH40KShootaBoyzGun | Warhead@1Dam |

