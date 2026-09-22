# audit_code_duplication — copy-paste clone groups

Python files: **510** (min 5 statements), C# files: **353** (min 8 lines)


## Files that do not parse (not scanned)

| file | line | error |
|---|---|---|
| tools/tests/test_audit_k_linearity_inventory.py | 1 | invalid non-printable character U+FEFF |

| code | meaning | clone groups | baseline |
|---|---|---|---|
| C1 | identical Python function bodies | 21 | 10 |
| C2 | identical C# method bodies | 15 | 14 |
| C3 | identical module-level literal tables | 26 | 10 |


## C1 — Python function clones (21 group(s))

| copies | fingerprint | sites |
|---|---|---|
| 5 | 41d0c91332872de3 | tools/balance/consolidate_authorized_role_profiles.py:199 descendants(); tools/balance/consolidate_corroborated_role_profiles.py:294 descendants(); tools/balance/consolidate_delivery_identity_profiles.py:76 descendants(); tools/balance/consolidate_machinegun_profiles.py:56 descendants(); tools/balance/consolidate_role_complete_profiles.py:85 descendants() |
| 4 | 0c9e5a3408c1d09c | tools/balance/consolidate_exact_profile_duplicates.py:105 descendants(); tools/balance/consolidate_freedom_rocket_base.py:43 descendants(); tools/balance/consolidate_high_identity_profiles.py:66 descendants(); tools/balance/consolidate_laser_heavy_routes.py:82 descendants() |
| 4 | 2af465aa2475b428 | tools/gen_cryo_fog.py:29 fractal_noise(); tools/gen_fire.py:32 fractal_noise(); tools/gen_fire_smoke_glow.py:27 fractal_noise(); tools/gen_smoke.py:28 fractal_noise() |
| 3 | 1126f101fc234323 | tools/tests/test_high_identity_profile_consolidation.py:55 test_full_ruleset_comparison_matches_accepted_manifest(); tools/tests/test_named_state_corrections.py:52 test_comparison_is_exactly_the_six_reviewed_definitions(); tools/tests/test_pinned_role_profile_consolidation.py:64 test_full_ruleset_comparison_matches_reviewed_manifest() |
| 3 | b349b4fadfe93412 | tools/balance/consolidate_explicit_family_state_profiles.py:164 descendants(); tools/balance/consolidate_named_state_corrections.py:76 descendants(); tools/balance/consolidate_pinned_role_profiles.py:92 descendants() |
| 3 | e56561937b9ea65e | tools/balance/consolidate_explicit_family_state_profiles.py:300 add_removal(); tools/balance/consolidate_named_family_profiles.py:260 add_removal(); tools/balance/consolidate_pinned_role_profiles.py:209 add_removal() |
| 3 | f3f8811ecbc48273 | tools/gen_cryo_fog.py:51 warp(); tools/gen_fire_smoke_glow.py:50 warp(); tools/gen_smoke.py:51 warp() |
| 2 | 05c6a74eb9d37d10 | tools/reference/extract_emperor_units.py:833 write_exclusive(); tools/reference/extract_opendune_units.py:908 write_exclusive() |
| 2 | 11d29300c3f1eadc | tools/tilesets/generate_volcanic_tileset.py:168 build_palette(); tools/tilesets/volcanic_art_utils.py:84 build_palette() |
| 2 | 1dacd1e435667177 | tools/tilesets/generate_volcanic_tileset.py:588 base_clear_index(); tools/tilesets/volcanic_art_utils.py:132 base_clear_index() |
| 2 | 375206ce07b9e1fe | tools/balance/consolidate_adjacent_family_stacks.py:105 combined_percentage_scale(); tools/balance/consolidate_same_family_stacks.py:159 combined_percentage_scale() |
| 2 | 3ec58372f7614926 | tools/tilesets/generate_clear_lava.py:639 lattice(); tools/tilesets/generate_sh04_alpha_beach_prototype.py:1538 lattice() |
| 2 | 4fa9c55d9990e939 | tools/balance/consolidate_freedom_rocket_base.py:64 resolved_hash(); tools/balance/consolidate_laser_heavy_routes.py:103 resolved_hash() |
| 2 | 6a38f8704e6495e3 | tools/tilesets/generate_volcanic_tileset.py:576 tileable_noise(); tools/tilesets/volcanic_art_utils.py:120 tileable_noise() |
| 2 | 91e5e00bc8dcb778 | tools/tilesets/build_volcanic_basalt_gimp_brushes.py:58 checkerboard(); tools/tilesets/fix_tc_basalt_shadow_outlines.py:60 checkerboard() |
| 2 | 97800b303b1b47fb | tools/rename/apply.py:73 sub(); tools/rename/safe_rename.py:91 sub() |
| 2 | 99775302ed579094 | tools/tests/test_dead_warhead_fields.py:157 setUp(); tools/tests/test_dead_warhead_fields.py:206 setUp() |
| 2 | beec2625d556ef6b | tools/tilesets/generate_clear_lava.py:621 periodic_value_noise(); tools/tilesets/generate_sh04_alpha_beach_prototype.py:1520 periodic_value_noise() |
| 2 | ed0cd1830cbcac3c | tools/balance/consolidate_rule_driven_blast_ordnance.py:223 isolate_legacy_root(); tools/balance/consolidate_rule_driven_heavy_explosives.py:108 isolate_legacy_root() |
| 2 | f0e4b6e20114d0f8 | tools/rename/apply.py:35 load_map(); tools/rename/safe_rename.py:35 load_map() |
| 2 | f7586bdb04bd3e37 | tools/balance/consolidate_exact_profile_duplicates.py:231 remove_node(); tools/balance/consolidate_laser_heavy_routes.py:212 remove_node() |


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
| 2 | edf49e24a44c5bb8 | OpenRA.Mods.CA/Traits/BotModules/BaseBuilderBotModuleCA.cs:825 CountQueuedBuildings(); OpenRA.Mods.CA/Traits/BotModules/BaseBuilderBotModuleCA.cs:833 SellUselessRefinery() |


## C3 — Duplicated constant tables (26 group(s))

| copies | fingerprint | sites |
|---|---|---|
| 5 | e90c0e4fa9ad2195 | tools/balance/consolidate_corroborated_role_profiles.py:278 CONTRACT_FIELDS; tools/balance/consolidate_explicit_family_state_profiles.py:158 CONTRACT_FIELDS; tools/balance/consolidate_high_identity_profiles.py:60 CONTRACT_FIELDS; tools/balance/consolidate_named_state_corrections.py:61 CONTRACT_FIELDS; tools/balance/consolidate_pinned_role_profiles.py:86 CONTRACT_FIELDS |
| 4 | 28fac3656bc8fc3b | tools/audit/find_orphan_old_keys.py:20 CENTRAL; tools/audit/find_orphan_old_keys_multi.py:18 CENTRAL; tools/balance/fix_orphan_old_keys.py:19 CENTRAL; tools/balance/fix_orphan_old_keys_multi.py:16 CENTRAL |
| 4 | 9a62b7cb0c6b46dc | tools/audit/audit_heaviness_bell.py:99 COMPANION; tools/audit/audit_three_way_split.py:75 COMPANION_MARKERS; tools/audit/audit_tier_weapon_class.py:60 COMPANION_MARKERS; tools/balance/preview_bell.py:44 COMPANION |
| 3 | 5573ff9b5f70fe4c | tools/audit/audit_original_coverage.py:42 ORIGINAL_SOURCES; tools/balance/assign_references.py:166 ORIGINAL_SOURCES; tools/balance/build_reference_report.py:31 ORIGINAL_SOURCES |
| 3 | 6c04bed7d433482f | tools/audit/audit_stat_uniqueness.py:44 STATS; tools/balance/faction_extrapolate.py:84 RATE_STATS; tools/balance/reference_targets.py:41 STATS |
| 3 | 926a972c11b9232c | tools/audit/audit_heaviness_bell.py:146 AXIS_ORDER; tools/balance/effective_heaviness.py:58 BELL_AXIS_ORDER; tools/balance/gen_weapon_template.py:1019 BELL_AXIS_ORDER |
| 3 | 985c1fe34e42db41 | tools/audit/find_empty_warhead.py:16 CENTRAL; tools/audit/weapon_families.py:23 CENTRAL; tools/balance/sweep_areadamage.py:25 CENTRAL |
| 2 | 05b492a648a61f78 | tools/audit/audit_family_uniqueness.py:52 COMPANION; tools/audit/audit_versus_profile.py:75 COMPANION |
| 2 | 0ec5f6758f9956dd | tools/balance/peer_corpus.py:29 ROW_PROVENANCE; tools/reference/extract_peer_units.py:1403 ROW_PROVENANCE_KEYS |
| 2 | 153d4fc74c8cdd31 | tools/tilesets/build_ra_temperate_basalt_trees.py:20 ACTORS; tools/tilesets/build_volcanic_basalt_gimp_brushes.py:20 ACTORS |
| 2 | 2665d6950cd4417a | tools/audit/find_orphan_old_keys.py:27 OLD_TO_NEW; tools/balance/fix_orphan_old_keys.py:25 OLD_TO_NEW |
| 2 | 41839a9d7e016b39 | tools/balance/consolidate_explicit_family_state_profiles.py:81 STATE_EXPANSION; tools/tests/test_explicit_family_state_profile_consolidation.py:32 EXPECTED_EXPANSION |
| 2 | 4979d18fd8f148a1 | tools/tilesets/detect_cliff_dark_noise.py:14 BLACK; tools/tilesets/process_ai_edge_mask.py:15 BLACK |
| 2 | 590fa5489ca5f751 | tools/audit/find_orphan_old_keys_multi.py:25 OLD_KEY_FAMILIES; tools/balance/fix_orphan_old_keys_multi.py:22 OLD_KEY_FAMILIES |
| 2 | 783c5216cd3c1bf0 | tools/audit/audit_versus_profile.py:65 NON_ARMOR; tools/balance/preview_bell.py:45 OFF_AXIS |
| 2 | 7b392ae5dfabff76 | tools/tilesets/apply_ai_edge_correction.py:16 MAGENTA; tools/tilesets/process_ai_edge_mask.py:14 MAGENTA |
| 2 | 8ad665990352733b | tools/balance/build_workbook.py:62 TYPE_ORDER; tools/balance/import_workbook.py:37 TYPE_SHEETS |
| 2 | b53e0f9e7578cc2a | tools/audit/audit_heaviness_bell.py:110 LADDERS; tools/reference/aggregate_archetype.py:62 CAMEO_LADDERS |
| 2 | c15459229a835d70 | tools/tilesets/build_tc_basalt_from_gimp.py:18 ACTORS; tools/tilesets/fix_tc_basalt_shadow_outlines.py:18 ACTORS |
| 2 | de57d7955065e638 | tools/balance/gen_effects.py:38 LEVELORDER; tools/balance/gen_projectiles.py:30 LEVELORDER |
| 2 | e82cdb37ffc15514 | tools/audit/audit_versus_profile.py:67 LADDERS; tools/balance/gen_weapon_template.py:35 LADDERS |
| 2 | eba2f9dc1c86d3e4 | tools/audit/audit_tier_weapon_class.py:64 LADDER; tools/balance/gen_weapon_template.py:2232 STORM_LEVELS |
| 2 | ee70e291636f426f | tools/balance/build_japan_pilot.py:68 CLASSIC_FACTIONS; tools/balance/validate_reference_holdout.py:62 CLASSIC_FACTIONS |
| 2 | ee8795bea6c56142 | tools/audit/audit_versus_profile.py:74 LEVELS; tools/reference/propose_family_profiles.py:113 LEVEL_ORDER |
| 2 | eed204ad8ec23410 | tools/audit/propose_sonic_mapping.py:104 OLD_FAMILIES; tools/audit/weapon_families.py:29 OLD_FAMILIES |
| 2 | efe4c032c5c937c9 | tools/audit/audit_three_way_split.py:72 MAIN_DAMAGE_TYPES; tools/audit/audit_tier_weapon_class.py:59 MAIN_DAMAGE_TYPES |


## FAIL

- C1: 21 > baseline 10
- C2: 15 > baseline 14
- C3: 26 > baseline 10

