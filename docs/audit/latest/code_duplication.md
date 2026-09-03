# audit_code_duplication — copy-paste clone groups

Python files: **273** (min 5 statements), C# files: **346** (min 8 lines)

| code | meaning | clone groups | baseline |
|---|---|---|---|
| C1 | identical Python function bodies | 10 | 10 |
| C2 | identical C# method bodies | 15 | 14 |
| C3 | identical module-level literal tables | 17 | 10 |


## C1 — Python function clones (10 group(s))

| copies | fingerprint | sites |
|---|---|---|
| 4 | 2af465aa2475b428 | tools/gen_cryo_fog.py:29 fractal_noise(); tools/gen_fire.py:32 fractal_noise(); tools/gen_fire_smoke_glow.py:27 fractal_noise(); tools/gen_smoke.py:28 fractal_noise() |
| 3 | f3f8811ecbc48273 | tools/gen_cryo_fog.py:51 warp(); tools/gen_fire_smoke_glow.py:50 warp(); tools/gen_smoke.py:51 warp() |
| 2 | 11d29300c3f1eadc | tools/tilesets/generate_volcanic_tileset.py:168 build_palette(); tools/tilesets/volcanic_art_utils.py:84 build_palette() |
| 2 | 1dacd1e435667177 | tools/tilesets/generate_volcanic_tileset.py:588 base_clear_index(); tools/tilesets/volcanic_art_utils.py:132 base_clear_index() |
| 2 | 3ec58372f7614926 | tools/tilesets/generate_clear_lava.py:639 lattice(); tools/tilesets/generate_sh04_alpha_beach_prototype.py:1538 lattice() |
| 2 | 6a38f8704e6495e3 | tools/tilesets/generate_volcanic_tileset.py:576 tileable_noise(); tools/tilesets/volcanic_art_utils.py:120 tileable_noise() |
| 2 | 91e5e00bc8dcb778 | tools/tilesets/build_volcanic_basalt_gimp_brushes.py:58 checkerboard(); tools/tilesets/fix_tc_basalt_shadow_outlines.py:60 checkerboard() |
| 2 | 97800b303b1b47fb | tools/rename/apply.py:73 sub(); tools/rename/safe_rename.py:91 sub() |
| 2 | beec2625d556ef6b | tools/tilesets/generate_clear_lava.py:621 periodic_value_noise(); tools/tilesets/generate_sh04_alpha_beach_prototype.py:1520 periodic_value_noise() |
| 2 | f0e4b6e20114d0f8 | tools/rename/apply.py:35 load_map(); tools/rename/safe_rename.py:35 load_map() |


## C2 — C# method clones (15 group(s))

| copies | fingerprint | sites |
|---|---|---|
| 3 | 2049c109832a37b5 | OpenRA.Mods.Cameo/Widgets/ObserverBuildOrderIconsWidget.cs:183 Tick(); OpenRA.Mods.Cameo/Widgets/ObserverPromotionsIconsWidget.cs:157 Tick(); OpenRA.Mods.Cameo/Widgets/PlayerUpgradesIconsWidget.cs:150 Tick() |
| 2 | 05372eb40e5f4542 | OpenRA.Mods.Cameo/UtilityCommands/FactionBuildableReportCommand.cs:292 ExpandTransforms(); OpenRA.Mods.Cameo/UtilityCommands/TildeAuditCommand.cs:470 ExpandTransforms() |
| 2 | 1c600b09b51924b2 | OpenRA.Mods.Cameo/Widgets/ClickMaskWidget.cs:28 HandleMouseInput(); OpenRA.Mods.Cameo/Widgets/CommanderTreeDismissWidget.cs:24 HandleMouseInput() |
| 2 | 1fe354611923a401 | OpenRA.Mods.Cameo/Traits/DroneSpawnerMasterCA.cs:235 SpawnIntoWorld(); OpenRA.Mods.Cameo/Traits/ShadeMaster.cs:139 SpawnIntoWorld() |
| 2 | 2a3b5caf2a992b8b | OpenRA.Mods.Cameo/Traits/DroneSpawnerMasterCA.cs:282 MoveSlaves(); OpenRA.Mods.Cameo/Traits/SlaveMinerSpawnerMaster.cs:193 MoveSlaves() |
| 2 | 2c7861f2ea9c9096 | OpenRA.Mods.Cameo/Traits/World/HeatDistortionRenderer.cs:86 RegisterDistortion(); OpenRA.Mods.Cameo/Traits/World/ShockwaveDistortionRenderer.cs:85 RegisterShockwave() |
| 2 | 2ed6818d4fa1dcc1 | OpenRA.Mods.CA/Traits/AttachOnCreation.cs:43 Attach(); OpenRA.Mods.CA/Traits/AttachOnTransform.cs:45 Attach() |
| 2 | 36919d259764fdb5 | OpenRA.Mods.Cameo/Traits/DroneSpawnerMasterCA.cs:297 AssignSlaveActivity(); OpenRA.Mods.Cameo/Traits/SlaveMinerSpawnerMaster.cs:208 AssignSlaveActivity() |
| 2 | 522ab179c848a0ef | OpenRA.Mods.Cameo/Traits/DroneSpawnerMasterCA.cs:103 Created(); OpenRA.Mods.Cameo/Traits/SlaveMinerSpawnerMaster.cs:85 Created() |
| 2 | 61d619290028a34b | OpenRA.Mods.CA/Projectiles/LinearPulse.cs:1509 TryProjectOntoCenterLine(); OpenRA.Mods.CA/Projectiles/LinearPulse.cs:1520 CalculateFalloffDistance() |
| 2 | 88ddeee6df34ebf1 | OpenRA.Mods.Cameo/Widgets/ObserverBuildOrderIconsWidget.cs:63 ObserverBuildOrderIconsWidget(); OpenRA.Mods.Cameo/Widgets/ObserverPromotionsIconsWidget.cs:61 ObserverPromotionsIconsWidget() |
| 2 | 918c59746a74f5f7 | OpenRA.Mods.CA/Projectiles/LinearPulse.cs:1531 TryProjectOntoCenterLine(); OpenRA.Mods.CA/Projectiles/LinearPulse.cs:1542 GetFalloffModifier() |
| 2 | 9b5c59ffeffd6c33 | OpenRA.Mods.Cameo/Widgets/CommanderTreeWidget.cs:337 HandleRightClick(); OpenRA.Mods.Cameo/Widgets/CommanderTreeWidget.cs:353 HandleMiddleClick() |
| 2 | 9f8a4e4f976a99f2 | OpenRA.Mods.CA/Traits/Render/WithColoredSelectionBox.cs:108 Update(); OpenRA.Mods.CA/Traits/Render/WithNameTagDecorationCA.cs:121 Update() |
| 2 | fccb77d01668aded | OpenRA.Mods.CA/Traits/BotModules/BaseBuilderBotModuleCA.cs:825 CountQueuedBuildings(); OpenRA.Mods.CA/Traits/BotModules/BaseBuilderBotModuleCA.cs:833 SellUselessRefinery() |


## C3 — Duplicated constant tables (17 group(s))

| copies | fingerprint | sites |
|---|---|---|
| 5 | 28fac3656bc8fc3b | tools/audit/find_orphan_old_keys.py:20 CENTRAL; tools/audit/find_orphan_old_keys_multi.py:18 CENTRAL; tools/audit/weapon_families.py:23 CENTRAL; tools/balance/fix_orphan_old_keys.py:19 CENTRAL; tools/balance/fix_orphan_old_keys_multi.py:16 CENTRAL |
| 3 | 9a62b7cb0c6b46dc | tools/audit/audit_heaviness_bell.py:95 COMPANION; tools/audit/audit_three_way_split.py:65 COMPANION_MARKERS; tools/audit/audit_tier_weapon_class.py:55 COMPANION_MARKERS |
| 2 | 153d4fc74c8cdd31 | tools/tilesets/build_ra_temperate_basalt_trees.py:20 ACTORS; tools/tilesets/build_volcanic_basalt_gimp_brushes.py:20 ACTORS |
| 2 | 2665d6950cd4417a | tools/audit/find_orphan_old_keys.py:27 OLD_TO_NEW; tools/balance/fix_orphan_old_keys.py:25 OLD_TO_NEW |
| 2 | 4979d18fd8f148a1 | tools/tilesets/detect_cliff_dark_noise.py:14 BLACK; tools/tilesets/process_ai_edge_mask.py:15 BLACK |
| 2 | 590fa5489ca5f751 | tools/audit/find_orphan_old_keys_multi.py:25 OLD_KEY_FAMILIES; tools/balance/fix_orphan_old_keys_multi.py:22 OLD_KEY_FAMILIES |
| 2 | 7b392ae5dfabff76 | tools/tilesets/apply_ai_edge_correction.py:16 MAGENTA; tools/tilesets/process_ai_edge_mask.py:14 MAGENTA |
| 2 | 8ad665990352733b | tools/balance/build_workbook.py:58 TYPE_ORDER; tools/balance/import_workbook.py:36 TYPE_SHEETS |
| 2 | 985c1fe34e42db41 | tools/audit/find_empty_warhead.py:16 CENTRAL; tools/balance/sweep_areadamage.py:25 CENTRAL |
| 2 | b53e0f9e7578cc2a | tools/audit/audit_heaviness_bell.py:106 LADDERS; tools/reference/aggregate_archetype.py:62 CAMEO_LADDERS |
| 2 | c15459229a835d70 | tools/tilesets/build_tc_basalt_from_gimp.py:18 ACTORS; tools/tilesets/fix_tc_basalt_shadow_outlines.py:18 ACTORS |
| 2 | de57d7955065e638 | tools/balance/gen_effects.py:38 LEVELORDER; tools/balance/gen_projectiles.py:30 LEVELORDER |
| 2 | e82cdb37ffc15514 | tools/audit/audit_versus_profile.py:66 LADDERS; tools/balance/gen_weapon_template.py:34 LADDERS |
| 2 | eba2f9dc1c86d3e4 | tools/audit/audit_tier_weapon_class.py:59 LADDER; tools/balance/gen_weapon_template.py:2045 STORM_LEVELS |
| 2 | ee8795bea6c56142 | tools/audit/audit_versus_profile.py:73 LEVELS; tools/reference/propose_family_profiles.py:113 LEVEL_ORDER |
| 2 | eed204ad8ec23410 | tools/audit/propose_sonic_mapping.py:104 OLD_FAMILIES; tools/audit/weapon_families.py:29 OLD_FAMILIES |
| 2 | efe4c032c5c937c9 | tools/audit/audit_three_way_split.py:62 MAIN_DAMAGE_TYPES; tools/audit/audit_tier_weapon_class.py:54 MAIN_DAMAGE_TYPES |


## FAIL

- C2: 15 > baseline 14
- C3: 17 > baseline 10

