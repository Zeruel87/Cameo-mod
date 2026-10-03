# audit_code_duplication — copy-paste clone groups

Python files: **806** (min 5 statements), C# files: **475** (min 8 lines)


## Files that do not parse (not scanned)

| file | line | error |
|---|---|---|
| tools/tests/test_audit_k_linearity_inventory.py | 1 | invalid non-printable character U+FEFF |

| code | meaning | clone groups | baseline |
|---|---|---|---|
| C1 | identical Python function bodies | 29 | 10 |
| C2 | identical C# method bodies | 22 | 14 |
| C3 | identical module-level literal tables | 43 | 10 |


## C1 — Python function clones (29 group(s))

| copies | fingerprint | sites |
|---|---|---|
| 5 | 41d0c91332872de3 | tools/balance/consolidate_authorized_role_profiles.py:199 descendants(); tools/balance/consolidate_corroborated_role_profiles.py:301 descendants(); tools/balance/consolidate_delivery_identity_profiles.py:83 descendants(); tools/balance/consolidate_machinegun_profiles.py:56 descendants(); tools/balance/consolidate_role_complete_profiles.py:85 descendants() |
| 4 | 0c9e5a3408c1d09c | tools/balance/consolidate_exact_profile_duplicates.py:105 descendants(); tools/balance/consolidate_freedom_rocket_base.py:43 descendants(); tools/balance/consolidate_high_identity_profiles.py:66 descendants(); tools/balance/consolidate_laser_heavy_routes.py:82 descendants() |
| 4 | 2af465aa2475b428 | tools/gen_cryo_fog.py:29 fractal_noise(); tools/gen_fire.py:32 fractal_noise(); tools/gen_fire_smoke_glow.py:27 fractal_noise(); tools/gen_smoke.py:28 fractal_noise() |
| 4 | 65200300e1e889be | tools/ai/run_ai_match_batch.py:173 load_config(); tools/tests/ai_bot_player_gate.py:48 load_config(); tools/tests/ai_raid_gate.py:55 load_config(); tools/tests/ai_squad_gate.py:54 load_config() |
| 3 | 19cd94bfaa3c12ef | tools/balance/compare_nuke_area_damage.py:290 main(); tools/balance/reconcile_r12_consumer_closure.py:380 main(); tools/balance/reconcile_r13_templates.py:161 main() |
| 3 | 276f5256b8897b1c | tools/tests/ai_bot_player_gate.py:110 read_appended_records(); tools/tests/ai_raid_gate.py:117 read_appended_records(); tools/tests/ai_squad_gate.py:116 read_appended_records() |
| 3 | 8854ec3eda1c1b76 | tools/balance/cameo_channel_curves.py:533 main(); tools/balance/dta_channel_curves.py:501 main(); tools/balance/reference_weapon_geometry.py:565 main() |
| 3 | 89ffae39156fff00 | tools/tests/ai_bot_player_gate.py:66 support_directory(); tools/tests/ai_raid_gate.py:73 support_directory(); tools/tests/ai_squad_gate.py:72 support_directory() |
| 3 | b349b4fadfe93412 | tools/balance/consolidate_explicit_family_state_profiles.py:164 descendants(); tools/balance/consolidate_named_state_corrections.py:76 descendants(); tools/balance/consolidate_pinned_role_profiles.py:92 descendants() |
| 3 | e56561937b9ea65e | tools/balance/consolidate_explicit_family_state_profiles.py:300 add_removal(); tools/balance/consolidate_named_family_profiles.py:260 add_removal(); tools/balance/consolidate_pinned_role_profiles.py:209 add_removal() |
| 3 | f3f8811ecbc48273 | tools/gen_cryo_fog.py:51 warp(); tools/gen_fire_smoke_glow.py:50 warp(); tools/gen_smoke.py:51 warp() |
| 2 | 05c6a74eb9d37d10 | tools/reference/extract_emperor_units.py:833 write_exclusive(); tools/reference/extract_opendune_units.py:908 write_exclusive() |
| 2 | 0d67a0a30ddaeb8e | tools/tests/gen_cannonap_fixture.py:38 parse_generated_warhead(); tools/tests/test_cannonap_generated_fixture.py:42 parse_generated_warhead() |
| 2 | 11d29300c3f1eadc | tools/tilesets/generate_volcanic_tileset.py:168 build_palette(); tools/tilesets/volcanic_art_utils.py:84 build_palette() |
| 2 | 1dacd1e435667177 | tools/tilesets/generate_volcanic_tileset.py:588 base_clear_index(); tools/tilesets/volcanic_art_utils.py:132 base_clear_index() |
| 2 | 2bbde3b4a104ab45 | tools/tests/test_accepted_td_gdi_balance_batch.py:44 assert_weapon(); tools/tests/test_accepted_td_nod_balance_batch.py:48 assert_weapon() |
| 2 | 375206ce07b9e1fe | tools/balance/consolidate_adjacent_family_stacks.py:105 combined_percentage_scale(); tools/balance/consolidate_same_family_stacks.py:159 combined_percentage_scale() |
| 2 | 3ec58372f7614926 | tools/tilesets/generate_clear_lava.py:639 lattice(); tools/tilesets/generate_sh04_alpha_beach_prototype.py:1538 lattice() |
| 2 | 46d2974b41e97f9c | tools/audit/audit_promotion_superiority.py:559 main(); tools/balance/prepare_promotion_upgrade_interactions.py:339 main() |
| 2 | 4fa9c55d9990e939 | tools/balance/consolidate_freedom_rocket_base.py:64 resolved_hash(); tools/balance/consolidate_laser_heavy_routes.py:103 resolved_hash() |
| 2 | 62ed07d5aa1ca73a | tools/balance/consolidate_corroborated_role_profiles.py:675 main(); tools/balance/consolidate_delivery_identity_profiles.py:194 main() |
| 2 | 6a38f8704e6495e3 | tools/tilesets/generate_volcanic_tileset.py:576 tileable_noise(); tools/tilesets/volcanic_art_utils.py:120 tileable_noise() |
| 2 | 91e5e00bc8dcb778 | tools/tilesets/build_volcanic_basalt_gimp_brushes.py:58 checkerboard(); tools/tilesets/fix_tc_basalt_shadow_outlines.py:60 checkerboard() |
| 2 | 97800b303b1b47fb | tools/rename/apply.py:73 sub(); tools/rename/safe_rename.py:91 sub() |
| 2 | 99775302ed579094 | tools/tests/test_dead_warhead_fields.py:157 setUp(); tools/tests/test_dead_warhead_fields.py:206 setUp() |
| 2 | beec2625d556ef6b | tools/tilesets/generate_clear_lava.py:621 periodic_value_noise(); tools/tilesets/generate_sh04_alpha_beach_prototype.py:1520 periodic_value_noise() |
| 2 | ed0cd1830cbcac3c | tools/balance/consolidate_rule_driven_blast_ordnance.py:223 isolate_legacy_root(); tools/balance/consolidate_rule_driven_heavy_explosives.py:108 isolate_legacy_root() |
| 2 | f0e4b6e20114d0f8 | tools/rename/apply.py:35 load_map(); tools/rename/safe_rename.py:35 load_map() |
| 2 | f7586bdb04bd3e37 | tools/balance/consolidate_exact_profile_duplicates.py:231 remove_node(); tools/balance/consolidate_laser_heavy_routes.py:212 remove_node() |


## C2 — C# method clones (22 group(s))

| copies | fingerprint | sites |
|---|---|---|
| 4 | 6def834d295492bb | OpenRA.Mods.Cameo/Traits/BotModules/EngineerBotModule.cs:1164 EscortReady(); OpenRA.Mods.Cameo/Traits/BotModules/EngineerBotModule.cs:1171 DefenceValue(); OpenRA.Mods.Cameo/Traits/BotModules/EngineerBotModule.cs:1176 OwnArmedValueNear(); OpenRA.Mods.Cameo/Traits/BotModules/EngineerBotModule.cs:1196 BlockedByEscort() |
| 3 | 2049c109832a37b5 | OpenRA.Mods.Cameo/Widgets/ObserverBuildOrderIconsWidget.cs:184 Tick(); OpenRA.Mods.Cameo/Widgets/ObserverPromotionsIconsWidget.cs:158 Tick(); OpenRA.Mods.Cameo/Widgets/PlayerUpgradesIconsWidget.cs:151 Tick() |
| 3 | ec2ad77fd06bf5bb | OpenRA.Mods.Cameo/Traits/BotModules/BotSituation.cs:1906 TargetScore(); OpenRA.Mods.Cameo/Traits/BotModules/BotSituation.cs:1909 TargetScore(); OpenRA.Mods.Cameo/Traits/BotModules/BotSituation.cs:1913 TargetScore() |
| 2 | 05372eb40e5f4542 | OpenRA.Mods.Cameo/UtilityCommands/FactionBuildableReportCommand.cs:292 ExpandTransforms(); OpenRA.Mods.Cameo/UtilityCommands/TildeAuditCommand.cs:470 ExpandTransforms() |
| 2 | 07c66d79766bf896 | OpenRA.Mods.CA/Traits/BotModules/SquadManagerBotModuleCA.cs:1032 CanEscortArtillery(); OpenRA.Mods.CA/Traits/BotModules/SquadManagerBotModuleCA.cs:1045 CanHitAir() |
| 2 | 1c600b09b51924b2 | OpenRA.Mods.Cameo/Widgets/ClickMaskWidget.cs:28 HandleMouseInput(); OpenRA.Mods.Cameo/Widgets/CommanderTreeDismissWidget.cs:24 HandleMouseInput() |
| 2 | 1fe354611923a401 | OpenRA.Mods.Cameo/Traits/DroneSpawnerMasterCA.cs:235 SpawnIntoWorld(); OpenRA.Mods.Cameo/Traits/ShadeMaster.cs:139 SpawnIntoWorld() |
| 2 | 2a3b5caf2a992b8b | OpenRA.Mods.Cameo/Traits/DroneSpawnerMasterCA.cs:282 MoveSlaves(); OpenRA.Mods.Cameo/Traits/SlaveMinerSpawnerMaster.cs:193 MoveSlaves() |
| 2 | 36919d259764fdb5 | OpenRA.Mods.Cameo/Traits/DroneSpawnerMasterCA.cs:297 AssignSlaveActivity(); OpenRA.Mods.Cameo/Traits/SlaveMinerSpawnerMaster.cs:208 AssignSlaveActivity() |
| 2 | 3ccd15bbfaebfe44 | OpenRA.Mods.Cameo/Traits/BotModules/EngineerBotModule.cs:561 GuardingEnemies(); OpenRA.Mods.Cameo/Traits/BotModules/EngineerBotModule.cs:568 RankBySafety() |
| 2 | 45a43547d43ff3d8 | OpenRA.Mods.CA/Traits/BotModules/SquadManagerBotModuleCA.cs:2402 IsStealthDraftable(); OpenRA.Mods.CA/Traits/BotModules/SquadManagerBotModuleCA.cs:2404 FindNewUnits() |
| 2 | 522ab179c848a0ef | OpenRA.Mods.Cameo/Traits/DroneSpawnerMasterCA.cs:103 Created(); OpenRA.Mods.Cameo/Traits/SlaveMinerSpawnerMaster.cs:85 Created() |
| 2 | 5659cbf6c3b6a99d | OpenRA.Mods.CA/Traits/BotModules/Squads/States/GroundConcaveStateCA.cs:411 Valid(); OpenRA.Mods.CA/Traits/BotModules/Squads/States/GroundConcaveStateCA.cs:420 ShouldCommit() |
| 2 | 61d619290028a34b | OpenRA.Mods.CA/Projectiles/LinearPulse.cs:1509 TryProjectOntoCenterLine(); OpenRA.Mods.CA/Projectiles/LinearPulse.cs:1520 CalculateFalloffDistance() |
| 2 | 8ab419c8b1877522 | OpenRA.Mods.Cameo/Traits/BotModules/TacticalMapBotModule.cs:1684 GetUsefulChokepoints(); OpenRA.Mods.Cameo/Traits/BotModules/TacticalMapBotModule.cs:1705 GetDoorHotspots() |
| 2 | 918c59746a74f5f7 | OpenRA.Mods.CA/Projectiles/LinearPulse.cs:1531 TryProjectOntoCenterLine(); OpenRA.Mods.CA/Projectiles/LinearPulse.cs:1542 GetFalloffModifier() |
| 2 | 9b5c59ffeffd6c33 | OpenRA.Mods.Cameo/Widgets/CommanderTreeWidget.cs:338 HandleRightClick(); OpenRA.Mods.Cameo/Widgets/CommanderTreeWidget.cs:354 HandleMiddleClick() |
| 2 | b0d2492b62a8c3b9 | OpenRA.Mods.Cameo/Widgets/ObserverBuildOrderIconsWidget.cs:64 ObserverBuildOrderIconsWidget(); OpenRA.Mods.Cameo/Widgets/ObserverPromotionsIconsWidget.cs:62 ObserverPromotionsIconsWidget() |
| 2 | cfb1b41e7feda062 | OpenRA.Mods.Cameo/Traits/BotModules/TacticalMapBotModule.cs:1783 DoorApproachAxis(); OpenRA.Mods.Cameo/Traits/BotModules/TacticalMapBotModule.cs:1795 GetDoorKillZoneCells() |
| 2 | d2d42569b726aee5 | OpenRA.Mods.Cameo/Traits/AiMatchLogWriter.cs:93 CaptureAndAppend(); OpenRA.Mods.Cameo/Traits/AiSituationLogWriter.cs:75 CaptureAndAppend() |
| 2 | da8e9cfda4c70a44 | OpenRA.Mods.CA/Traits/BotModules/BaseBuilderBotModuleCA.cs:883 HasAdequateRefineryCount(); OpenRA.Mods.CA/Traits/BotModules/BaseBuilderBotModuleCA.cs:920 RecordOpeningStructureQueued() |
| 2 | edf49e24a44c5bb8 | OpenRA.Mods.CA/Traits/BotModules/BaseBuilderBotModuleCA.cs:971 CountQueuedBuildings(); OpenRA.Mods.CA/Traits/BotModules/BaseBuilderBotModuleCA.cs:979 SellUselessRefinery() |


## C3 — Duplicated constant tables (43 group(s))

| copies | fingerprint | sites |
|---|---|---|
| 5 | e90c0e4fa9ad2195 | tools/balance/consolidate_corroborated_role_profiles.py:285 CONTRACT_FIELDS; tools/balance/consolidate_explicit_family_state_profiles.py:158 CONTRACT_FIELDS; tools/balance/consolidate_high_identity_profiles.py:60 CONTRACT_FIELDS; tools/balance/consolidate_named_state_corrections.py:61 CONTRACT_FIELDS; tools/balance/consolidate_pinned_role_profiles.py:86 CONTRACT_FIELDS |
| 4 | 28fac3656bc8fc3b | tools/audit/find_orphan_old_keys.py:20 CENTRAL; tools/audit/find_orphan_old_keys_multi.py:18 CENTRAL; tools/balance/fix_orphan_old_keys.py:19 CENTRAL; tools/balance/fix_orphan_old_keys_multi.py:16 CENTRAL |
| 4 | 5573ff9b5f70fe4c | tools/audit/audit_original_coverage.py:42 ORIGINAL_SOURCES; tools/balance/armament_roles.py:628 ORIGINAL_SOURCES; tools/balance/assign_references.py:166 ORIGINAL_SOURCES; tools/balance/build_reference_report.py:38 ORIGINAL_SOURCES |
| 4 | 6c04bed7d433482f | tools/audit/audit_stat_uniqueness.py:44 STATS; tools/balance/faction_extrapolate.py:84 RATE_STATS; tools/balance/propose_reference_anchors.py:26 STATS; tools/balance/reference_targets.py:42 STATS |
| 4 | 9a62b7cb0c6b46dc | tools/audit/audit_heaviness_bell.py:99 COMPANION; tools/audit/audit_three_way_split.py:75 COMPANION_MARKERS; tools/audit/audit_tier_weapon_class.py:60 COMPANION_MARKERS; tools/balance/preview_bell.py:44 COMPANION |
| 4 | e432ed7c8925c7bf | tools/audit/audit_promotion_superiority.py:31 FACTIONS; tools/balance/prepare_promotion_discount.py:19 FACTIONS; tools/balance/prepare_promotion_upgrade_interactions.py:26 FACTIONS; tools/balance/tier_chain.py:39 PILOT_PROMOTION_FACTIONS |
| 4 | f9db917022226317 | tools/audit/four_source_group_inventory.py:18 SOURCES; tools/balance/explicit_voice_group_assembler.py:17 REFERENCE_SOURCES; tools/balance/four_source_synthesis_gate.py:21 SOURCES; tools/balance/reference_weapon_geometry.py:26 KNOWN_REFERENCE_SOURCES |
| 3 | 57c53e8c22119da8 | tools/audit/audit_upgrade_regression.py:54 AIR; tools/balance/four_source_synthesis_gate.py:31 AIRCRAFT_AXES; tools/balance/reference_channel_curves.py:229 AIRCRAFT_AXES |
| 3 | 5b6fb78177b324c0 | tools/balance/dta_channel_curves.py:23 ARMOR_AXES; tools/balance/four_source_synthesis_gate.py:27 BASE_AXES; tools/balance/reference_channel_curves.py:31 ARMOR_AXES |
| 3 | 783c5216cd3c1bf0 | tools/audit/audit_versus_profile.py:80 NON_ARMOR; tools/balance/analyse_flat_main_fold.py:55 NON_ARMOR; tools/balance/preview_bell.py:45 OFF_AXIS |
| 3 | 926a972c11b9232c | tools/audit/audit_heaviness_bell.py:146 AXIS_ORDER; tools/balance/effective_heaviness.py:58 BELL_AXIS_ORDER; tools/balance/gen_weapon_template.py:1046 BELL_AXIS_ORDER |
| 3 | 985c1fe34e42db41 | tools/audit/audit_local_effect_fields.py:25 CENTRAL; tools/audit/weapon_families.py:23 CENTRAL; tools/balance/sweep_areadamage.py:25 CENTRAL |
| 3 | afb2195b28b1f9b9 | tools/audit/audit_bot_insurance.py:51 DIFFICULTIES; tools/balance/bot_difficulty_curve.py:49 DIFFICULTIES; tools/balance/bot_insurance_model.py:76 DIFFICULTIES |
| 3 | b53e0f9e7578cc2a | tools/audit/audit_heaviness_bell.py:110 LADDERS; tools/reference/aggregate_archetype.py:63 CAMEO_LADDERS; tools/reference/armor_interpolate.py:42 LADDERS |
| 3 | e82cdb37ffc15514 | tools/audit/audit_versus_profile.py:82 LADDERS; tools/balance/gen_weapon_template.py:35 LADDERS; tools/reference/warhead_workbook.py:72 LADDERS |
| 3 | ee8795bea6c56142 | tools/audit/audit_versus_profile.py:96 LEVELS; tools/reference/cameo_families.py:38 LEVELS; tools/reference/propose_family_profiles.py:113 LEVEL_ORDER |
| 3 | fa43615e2785b256 | tools/reference/dta_armor.py:8 VANILLA; tools/reference/extract_versus.py:48 TS_ARMORS; tools/reference/warhead_matrix.py:1079 TS_ARMORS |
| 2 | 05b492a648a61f78 | tools/audit/audit_family_uniqueness.py:52 COMPANION; tools/audit/audit_versus_profile.py:97 COMPANION |
| 2 | 0ec5f6758f9956dd | tools/balance/peer_corpus.py:29 ROW_PROVENANCE; tools/reference/extract_peer_units.py:1710 ROW_PROVENANCE_KEYS |
| 2 | 14e3e91bbb89b6e6 | tools/aud_to_wav.py:25 INDEX_ADJUST; tools/wav_to_aud.py:32 INDEX_ADJUST |
| 2 | 153d4fc74c8cdd31 | tools/tilesets/build_ra_temperate_basalt_trees.py:20 ACTORS; tools/tilesets/build_volcanic_basalt_gimp_brushes.py:20 ACTORS |
| 2 | 197ef915493c61ff | tools/reference/extract_versus.py:46 YR_ARMORS; tools/reference/warhead_matrix.py:1077 YR_ARMORS |
| 2 | 1e84563c6800369e | tools/balance/effective_heaviness.py:70 GEO_DERIVED; tools/balance/gen_weapon_template.py:838 GEO_DERIVED |
| 2 | 2665d6950cd4417a | tools/audit/find_orphan_old_keys.py:27 OLD_TO_NEW; tools/balance/fix_orphan_old_keys.py:25 OLD_TO_NEW |
| 2 | 2ae9494faf6fdfef | tools/aud_to_wav.py:26 STEP_TABLE; tools/wav_to_aud.py:33 STEP_TABLE |
| 2 | 36eb3ca7dd9cb6fd | tools/tests/gen_cannonap_fixture.py:31 HEAVINESS_CASES; tools/tests/test_cannonap_generated_fixture.py:35 HEAVINESS_CASES |
| 2 | 41839a9d7e016b39 | tools/balance/consolidate_explicit_family_state_profiles.py:81 STATE_EXPANSION; tools/tests/test_explicit_family_state_profile_consolidation.py:32 EXPECTED_EXPANSION |
| 2 | 4979d18fd8f148a1 | tools/tilesets/detect_cliff_dark_noise.py:14 BLACK; tools/tilesets/process_ai_edge_mask.py:15 BLACK |
| 2 | 4e7af25b7a053de9 | tools/audit/target_payload_routes.py:34 DAMAGE; tools/balance/shrapnel_scenario_report.py:35 DAMAGE_TYPES |
| 2 | 590fa5489ca5f751 | tools/audit/find_orphan_old_keys_multi.py:25 OLD_KEY_FAMILIES; tools/balance/fix_orphan_old_keys_multi.py:22 OLD_KEY_FAMILIES |
| 2 | 599972d0cf395f28 | tools/audit/content_pack_dependencies.py:17 WEAPON_FIELDS; tools/audit/target_payload_routes.py:35 REFERENCES |
| 2 | 7b392ae5dfabff76 | tools/tilesets/apply_ai_edge_correction.py:16 MAGENTA; tools/tilesets/process_ai_edge_mask.py:14 MAGENTA |
| 2 | 820ecf9a9ca15705 | tools/art/generate_chrome_scales.py:46 FIELD_DENSITY; tools/audit/audit_chrome_scale_variants.py:69 DENSITY |
| 2 | 8ad665990352733b | tools/balance/build_workbook.py:62 TYPE_ORDER; tools/balance/import_workbook.py:37 TYPE_SHEETS |
| 2 | c15459229a835d70 | tools/tilesets/build_tc_basalt_from_gimp.py:18 ACTORS; tools/tilesets/fix_tc_basalt_shadow_outlines.py:18 ACTORS |
| 2 | d0b8ba1c2ccfa903 | tools/audit/audit_family_uniqueness.py:51 LEVELS; tools/balance/splice_templates.py:45 LEVEL_SUFFIXES |
| 2 | de57d7955065e638 | tools/balance/gen_effects.py:38 LEVELORDER; tools/balance/gen_projectiles.py:30 LEVELORDER |
| 2 | dfc91d27d37afdd1 | tools/balance/cameo_channel_curves.py:26 ARMOR_AXES; tools/balance/four_source_synthesis_gate.py:28 COMMON_AXES |
| 2 | e631e1af9577a4aa | tools/balance/reference_weapon_geometry.py:29 GEOMETRY_FIELDS; tools/balance/summarize_reference_geometry.py:16 GEOMETRY_FIELDS |
| 2 | eba2f9dc1c86d3e4 | tools/audit/audit_tier_weapon_class.py:64 LADDER; tools/balance/gen_weapon_template.py:2492 STORM_LEVELS |
| 2 | ee70e291636f426f | tools/balance/build_japan_pilot.py:68 CLASSIC_FACTIONS; tools/balance/validate_reference_holdout.py:62 CLASSIC_FACTIONS |
| 2 | eed204ad8ec23410 | tools/audit/propose_sonic_mapping.py:104 OLD_FAMILIES; tools/audit/weapon_families.py:29 OLD_FAMILIES |
| 2 | efe4c032c5c937c9 | tools/audit/audit_three_way_split.py:72 MAIN_DAMAGE_TYPES; tools/audit/audit_tier_weapon_class.py:59 MAIN_DAMAGE_TYPES |


## FAIL

- C1: 29 > baseline 10
- C2: 22 > baseline 14
- C3: 43 > baseline 10

