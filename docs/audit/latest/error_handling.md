# audit_error_handling — Python tooling error handling

Files scanned: **806**

| code | meaning | count | baseline |
|---|---|---|---|
| E1 | bare except / except BaseException | 5 | 2 |
| E2 | handler discards the error | 141 | 30 |
| E3 | open() without encoding= | 161 | 90 |
| E4 | subprocess call without check= | 62 | 9 |


## Files that do not parse

| file | line | error |
|---|---|---|
| tools/tests/test_audit_k_linearity_inventory.py | 1 | invalid non-printable character U+FEFF |


## E1 — 5 finding(s)

| file | line | detail |
|---|---|---|
| tools/audit_ce_image_usage.py | 29 | bare `except:` |
| tools/audit_createeffect_image.py | 19 | bare `except:` |
| tools/balance/_patch_ledgers_from_reports.py | 143 | `except BaseException` |
| tools/balance/apply_carrier_slave_ammo.py | 290 | `except BaseException` |
| tools/balance/apply_harvester_durability.py | 420 | `except BaseException` |


## E2 — 141 finding(s)

| file | line | detail |
|---|---|---|
| tools/ai/ab_increment.py | 334 | handler body discards the error |
| tools/ai/ab_increment.py | 469 | handler body discards the error |
| tools/ai/ab_increment.py | 633 | handler body discards the error |
| tools/ai/ab_increment.py | 692 | handler body discards the error |
| tools/ai/derive_guerrilla_roles.py | 113 | handler body discards the error |
| tools/ai/derive_roles_preview.py | 94 | handler body discards the error |
| tools/ai/derive_roles_preview.py | 275 | handler body discards the error |
| tools/ai/fight_report.py | 32 | handler body discards the error |
| tools/ai/fit_arsenal_priors.py | 44 | handler body discards the error |
| tools/ai/gen_fransbot_lists.py | 140 | handler body discards the error |
| tools/ai/run_ai_match_batch.py | 719 | handler body discards the error |
| tools/ai/team_coordination_report.py | 48 | handler body discards the error |
| tools/ai/tune_build_order.py | 75 | handler body discards the error |
| tools/audit/audit_ai.py | 45 | handler body discards the error |
| tools/audit/audit_armor_upgrade_harm.py | 101 | handler body discards the error |
| tools/audit/audit_balance_sheet.py | 134 | handler body discards the error |
| tools/audit/audit_bot_insurance.py | 144 | handler body discards the error |
| tools/audit/audit_dune_rank_decoration.py | 15 | handler body discards the error |
| tools/audit/audit_elite_gating.py | 16 | handler body discards the error |
| tools/audit/audit_engine_freshness.py | 76 | handler body discards the error |
| tools/audit/audit_garrison_weapons.py | 77 | handler body discards the error |
| tools/audit/audit_k_linearity.py | 162 | handler body discards the error |
| tools/audit/audit_k_linearity.py | 180 | handler body discards the error |
| tools/audit/audit_missile_role_family.py | 134 | handler body discards the error |
| tools/audit/audit_missing_elite.py | 21 | handler body discards the error |
| tools/audit/audit_orphans.py | 93 | handler body discards the error |
| tools/audit/audit_plating_exclusivity.py | 94 | handler body discards the error |
| tools/audit/audit_power_budget.py | 100 | handler body discards the error |
| tools/audit/audit_rank_decoration.py | 49 | handler body discards the error |
| tools/audit/audit_rank_decoration.py | 68 | handler body discards the error |
| tools/audit/audit_scaled_bullet_overrides.py | 41 | handler body discards the error |
| tools/audit/audit_three_way_split.py | 119 | handler body discards the error |
| tools/audit/audit_tier_weapon_class.py | 81 | handler body discards the error |
| tools/audit/audit_turn_speed.py | 65 | handler body discards the error |
| tools/audit/audit_unique_traits.py | 73 | handler body discards the error |
| tools/audit/audit_upgrades.py | 158 | handler body discards the error |
| tools/audit/audit_upstream_adoption.py | 97 | handler body discards the error |
| tools/audit/audit_upstream_adoption.py | 138 | handler body discards the error |
| tools/audit/audit_weapon_suffixes.py | 115 | handler body discards the error |
| tools/audit/audit_weapon_suffixes.py | 162 | handler body discards the error |
| tools/audit/audit_weapon_suffixes.py | 228 | handler body discards the error |
| tools/audit/audit_weapon_suffixes.py | 350 | handler body discards the error |
| tools/audit/audit_weapon_uniqueness.py | 99 | handler body discards the error |
| tools/audit/gen_damage_matrix.py | 52 | handler body discards the error |
| tools/audit/gen_release_baseline.py | 50 | handler body discards the error |
| tools/audit/miniyaml.py | 223 | handler body discards the error |
| tools/audit/phase_b_survey.py | 40 | handler body discards the error |
| tools/audit/review_batch_diff.py | 80 | handler body discards the error |
| tools/audit/review_resolve_diff.py | 159 | handler body discards the error |
| tools/audit_ce_image_usage.py | 29 | handler body discards the error |
| tools/audit_createeffect_image.py | 19 | handler body discards the error |
| tools/balance/anchor_readiness.py | 670 | handler body discards the error |
| tools/balance/armament_roles.py | 214 | handler body discards the error |
| tools/balance/armor_exposure.py | 105 | handler body discards the error |
| tools/balance/armor_exposure.py | 141 | handler body discards the error |
| tools/balance/assign_references.py | 82 | handler body discards the error |
| tools/balance/assign_references.py | 567 | handler body discards the error |
| tools/balance/assign_references.py | 794 | handler body discards the error |
| tools/balance/audit_deprecated_name_lane.py | 51 | handler body discards the error |
| tools/balance/b3_intent_draft.py | 239 | handler body discards the error |
| tools/balance/build_armament_pairing_report.py | 138 | handler body discards the error |
| tools/balance/build_reference_report.py | 1474 | handler body discards the error |
| tools/balance/class_membership.py | 233 | handler body discards the error |
| tools/balance/collapse_target.py | 137 | handler body discards the error |
| tools/balance/compensate_retrofit.py | 113 | handler body discards the error |
| tools/balance/compensate_retrofit.py | 121 | handler body discards the error |
| tools/balance/consolidate_adjacent_family_stacks.py | 65 | handler body discards the error |
| tools/balance/consolidate_final_safe_cohorts.py | 133 | handler body discards the error |
| tools/balance/consolidate_reviewed_weapon_roots.py | 268 | handler body discards the error |
| tools/balance/consolidate_reviewed_weapon_roots.py | 320 | handler body discards the error |
| tools/balance/consolidate_same_family_stacks.py | 136 | handler body discards the error |
| tools/balance/derive_versus_columns.py | 72 | handler body discards the error |
| tools/balance/design_invented_profiles.py | 172 | handler body discards the error |
| tools/balance/design_invented_profiles.py | 186 | handler body discards the error |
| tools/balance/extract_stats.py | 301 | handler body discards the error |
| tools/balance/extract_stats.py | 365 | handler body discards the error |
| tools/balance/extract_stats.py | 1225 | handler body discards the error |
| tools/balance/formula.py | 589 | handler body discards the error |
| tools/balance/gen_derived_stats.py | 95 | handler body discards the error |
| tools/balance/measure_retrofit_gap.py | 134 | handler body discards the error |
| tools/balance/pending_classes.py | 34 | handler body discards the error |
| tools/balance/plan_firepower_retirement.py | 81 | handler body discards the error |
| tools/balance/propose_class_rebalance.py | 271 | handler body discards the error |
| tools/balance/reference_distribution.py | 923 | handler body discards the error |
| tools/balance/reference_distribution.py | 934 | handler body discards the error |
| tools/balance/reference_distribution.py | 1101 | handler body discards the error |
| tools/balance/reference_distribution.py | 1225 | handler body discards the error |
| tools/balance/reference_distribution.py | 1556 | handler body discards the error |
| tools/balance/report_versus_change.py | 74 | handler body discards the error |
| tools/balance/retrofit_legacy_template.py | 219 | handler body discards the error |
| tools/balance/retrofit_legacy_template.py | 322 | handler body discards the error |
| tools/balance/retrofit_legacy_template.py | 421 | handler body discards the error |
| tools/balance/retrofit_legacy_template.py | 516 | handler body discards the error |
| tools/balance/retrofit_legacy_template.py | 536 | handler body discards the error |
| tools/balance/retrofit_legacy_template.py | 547 | handler body discards the error |
| tools/balance/shield_uniqueness.py | 63 | handler body discards the error |
| tools/balance/synthesize_reference.py | 370 | handler body discards the error |
| tools/balance/target_model.py | 528 | handler body discards the error |
| tools/balance/target_model.py | 541 | handler body discards the error |
| tools/balance/tier_chain.py | 138 | handler body discards the error |
| tools/balance/tier_chain.py | 210 | handler body discards the error |
| tools/balance/tier_chain.py | 224 | handler body discards the error |
| tools/balance/tier_chain.py | 384 | handler body discards the error |
| tools/balance/verify_retrofit.py | 79 | handler body discards the error |
| tools/balance/verify_retrofit.py | 87 | handler body discards the error |
| tools/balance/w22_triage_unreachable.py | 119 | handler body discards the error |
| tools/balance/w22_triage_unreachable.py | 147 | handler body discards the error |
| tools/hooks/bash_guard.py | 117 | handler body discards the error |
| tools/hooks/bash_guard.py | 140 | handler body discards the error |
| tools/hooks/bash_guard.py | 154 | handler body discards the error |
| tools/hooks/bash_guard.py | 214 | handler body discards the error |
| tools/packs/migrate_assets.py | 226 | handler body discards the error |
| tools/packs/split_ai_rows.py | 66 | handler body discards the error |
| tools/reference/aggregate_archetype.py | 898 | handler body discards the error |
| tools/reference/compress_warheads.py | 412 | handler body discards the error |
| tools/reference/compress_warheads.py | 430 | handler body discards the error |
| tools/reference/extract_peer_units.py | 1008 | handler body discards the error |
| tools/reference/extract_peer_units.py | 1124 | handler body discards the error |
| tools/reference/extract_peer_units.py | 1212 | handler body discards the error |
| tools/reference/extract_peer_units.py | 1265 | handler body discards the error |
| tools/reference/extract_peer_units.py | 1303 | handler body discards the error |
| tools/reference/extract_versus.py | 207 | handler body discards the error |
| tools/reference/fit_families.py | 136 | handler body discards the error |
| tools/reference/warhead_matrix.py | 434 | handler body discards the error |
| tools/reference/warhead_matrix.py | 476 | handler body discards the error |
| tools/reference/warhead_matrix.py | 520 | handler body discards the error |
| tools/reference/warhead_matrix.py | 1307 | handler body discards the error |
| tools/reference/warhead_matrix.py | 1345 | handler body discards the error |
| tools/reference/warhead_matrix.py | 1373 | handler body discards the error |
| tools/rename/apply.py | 178 | handler body discards the error |
| tools/rename/safe_rename.py | 132 | handler body discards the error |
| tools/rename/safe_rename.py | 141 | handler body discards the error |
| tools/rename/safe_rename.py | 291 | handler body discards the error |
| tools/subset_judou_font.py | 56 | handler body discards the error |
| tools/tests/test_armament_roles.py | 306 | handler body discards the error |
| tools/tests/test_charge_aware_reference.py | 34 | handler body discards the error |
| tools/tests/test_charge_aware_reference.py | 49 | handler body discards the error |
| tools/tests/test_rename_r12_compatibility_cohort.py | 270 | handler body discards the error |
| tools/tests/test_support_armament_pricing.py | 21 | handler body discards the error |
| tools/tests/test_support_armament_pricing.py | 107 | handler body discards the error |
| tools/tilesets/generate_volcanic_tileset.py | 814 | handler body discards the error |


## E3 — 161 finding(s)

| file | line | detail |
|---|---|---|
| tools/art/generate_chrome_scales.py | 149 | `Image.open()` without encoding= |
| tools/audit/audit_effect_pairings.py | 112 | `args.baseline.read_text()` without encoding= |
| tools/audit/collapse_dead_warhead_inherits.py | 43 | `open()` without encoding= |
| tools/audit/collapse_dead_warhead_inherits.py | 80 | `open()` without encoding= |
| tools/audit/dead_field_sources.py | 173 | `write_text()` without encoding= |
| tools/audit/infantry_artillery_pressure.py | 33 | `path.open()` without encoding= |
| tools/bake_d2k_overlay.py | 28 | `Image.open()` without encoding= |
| tools/bake_d2k_overlay_zap.py | 10 | `Image.open()` without encoding= |
| tools/bake_d2k_zap.py | 41 | `Image.open()` without encoding= |
| tools/balance/assemble_four_voice_pilot.py | 49 | `path.open()` without encoding= |
| tools/balance/compare_defense_armor_curves.py | 116 | `args.matrix.read_text()` without encoding= |
| tools/balance/compare_defense_armor_curves.py | 126 | `payload_path.read_text()` without encoding= |
| tools/balance/derive_versus_columns.py | 114 | `read_text()` without encoding= |
| tools/balance/peer_corpus.py | 64 | `path.open()` without encoding= |
| tools/balance/prepare_promotion_discount.py | 37 | `path.open()` without encoding= |
| tools/balance/propose_reference_anchors.py | 427 | `read_text()` without encoding= |
| tools/balance/shrapnel_scenario_report.py | 47 | `path.open()` without encoding= |
| tools/check_hd_coverage.py | 10 | `open()` without encoding= |
| tools/d2k_to_openra.py | 153 | `Image.open()` without encoding= |
| tools/d2k_to_openra.py | 164 | `Image.open()` without encoding= |
| tools/dump_meg_names.py | 16 | `open()` without encoding= |
| tools/extract_insignias.py | 113 | `Image.open()` without encoding= |
| tools/hooks/bash_guard.py | 206 | `read_text()` without encoding= |
| tools/hooks/bash_guard.py | 232 | `perf.read_text()` without encoding= |
| tools/hooks/exec_guard.py | 69 | `perf.read_text()` without encoding= |
| tools/make_syndicate_insignia.py | 41 | `Image.open()` without encoding= |
| tools/make_syndicate_insignia.py | 63 | `Image.open()` without encoding= |
| tools/packs/migrate_assets.py | 149 | `cy.read_text()` without encoding= |
| tools/packs/migrate_assets.py | 288 | `write_text()` without encoding= |
| tools/reference/cameo_projectile_evidence.py | 71 | `read_text()` without encoding= |
| tools/reference/dta_projectile_evidence.py | 30 | `args.matrix.read_text()` without encoding= |
| tools/reference/extract_emperor_units.py | 477 | `path.open()` without encoding= |
| tools/reference/extract_emperor_units.py | 842 | `os.open()` without encoding= |
| tools/reference/extract_mix_ini.py | 78 | `path.open()` without encoding= |
| tools/reference/extract_opendune_units.py | 532 | `path.open()` without encoding= |
| tools/reference/extract_opendune_units.py | 917 | `os.open()` without encoding= |
| tools/reference/extract_ra3_units.py | 1348 | `os.open()` without encoding= |
| tools/tests/test_aedis_target_policy.py | 135 | `fixture.read_text()` without encoding= |
| tools/tests/test_ai_headquarters_refinery_cleanup.py | 39 | `read_text()` without encoding= |
| tools/tests/test_ai_logging_integration.py | 21 | `read_text()` without encoding= |
| tools/tests/test_anchor_dossier.py | 362 | `read_text()` without encoding= |
| tools/tests/test_chained_owned_names.py | 11 | `read_text()` without encoding= |
| tools/tests/test_check_band_membership.py | 20 | `anchors.write_text()` without encoding= |
| tools/tests/test_closed_remaining_names.py | 40 | `read_text()` without encoding= |
| tools/tests/test_closed_remaining_names.py | 44 | `read_text()` without encoding= |
| tools/tests/test_closed_remaining_names.py | 46 | `read_text()` without encoding= |
| tools/tests/test_converter_owned_names.py | 12 | `read_text()` without encoding= |
| tools/tests/test_defense_tooltip_accuracy.py | 30 | `read_text()` without encoding= |
| tools/tests/test_diagnostic_output.py | 38 | `two.read_text()` without encoding= |
| tools/tests/test_extract_versus_dta_overlay.py | 16 | `rules.write_text()` without encoding= |
| tools/tests/test_extract_versus_dta_overlay.py | 17 | `overlay.write_text()` without encoding= |
| tools/tests/test_extract_versus_dta_overlay.py | 25 | `path.write_text()` without encoding= |
| tools/tests/test_extract_versus_dta_overlay.py | 33 | `path.write_text()` without encoding= |
| tools/tests/test_extract_versus_dta_overlay.py | 43 | `path.write_text()` without encoding= |
| tools/tests/test_frozen_hero_reference.py | 13 | `read_text()` without encoding= |
| tools/tests/test_frozen_hero_reference.py | 14 | `read_text()` without encoding= |
| tools/tests/test_frozen_hero_reference.py | 23 | `read_text()` without encoding= |
| tools/tests/test_generate_chrome_scales.py | 158 | `Image.open()` without encoding= |
| tools/tests/test_ini_cycle_evidence.py | 63 | `read_text()` without encoding= |
| tools/tests/test_ini_weapon_selection.py | 18 | `read_text()` without encoding= |
| tools/tests/test_lookup_owned_names.py | 12 | `read_text()` without encoding= |
| tools/tests/test_lookup_owned_names.py | 16 | `read_text()` without encoding= |
| tools/tests/test_lookup_owned_names.py | 38 | `read_text()` without encoding= |
| tools/tests/test_openra_warhead_platforms.py | 15 | `path.write_text()` without encoding= |
| tools/tests/test_peer_corpus.py | 60 | `write_text()` without encoding= |
| tools/tests/test_peer_corpus.py | 70 | `write_text()` without encoding= |
| tools/tests/test_peer_corpus.py | 76 | `path.write_text()` without encoding= |
| tools/tests/test_peer_corpus.py | 134 | `write_text()` without encoding= |
| tools/tests/test_peer_corpus.py | 144 | `doc.write_text()` without encoding= |
| tools/tests/test_peer_corpus.py | 184 | `index.read_text()` without encoding= |
| tools/tests/test_peer_corpus.py | 186 | `index.write_text()` without encoding= |
| tools/tests/test_peer_corpus.py | 197 | `doc.write_text()` without encoding= |
| tools/tests/test_peer_state_scenarios.py | 173 | `read_text()` without encoding= |
| tools/tests/test_reference_map_requests.py | 27 | `read_text()` without encoding= |
| tools/tests/test_shared_owner_wrappers.py | 19 | `read_text()` without encoding= |
| tools/tests/test_td_naval_rename.py | 291 | `read_text()` without encoding= |
| tools/tests/test_td_naval_rename.py | 292 | `read_text()` without encoding= |
| tools/tests/test_virtual_anchor.py | 142 | `write_text()` without encoding= |
| tools/tests/test_warhead_source_paths.py | 21 | `rules.write_text()` without encoding= |
| tools/tests/test_warhead_source_paths.py | 31 | `base.write_text()` without encoding= |
| tools/tests/test_warhead_source_paths.py | 32 | `overlay.write_text()` without encoding= |
| tools/tilesets/apply_ai_edge_correction.py | 34 | `Image.open()` without encoding= |
| tools/tilesets/apply_ai_edge_correction.py | 78 | `Image.open()` without encoding= |
| tools/tilesets/apply_dark_noise_cleanup.py | 79 | `Image.open()` without encoding= |
| tools/tilesets/build_basalt_forest_bulk_review.py | 55 | `Image.open()` without encoding= |
| tools/tilesets/build_basalt_tree_imagegen_review.py | 39 | `Image.open()` without encoding= |
| tools/tilesets/build_cliff_connectivity_review.py | 84 | `Image.open()` without encoding= |
| tools/tilesets/build_cliff_connectivity_review.py | 85 | `Image.open()` without encoding= |
| tools/tilesets/build_cliff_connectivity_review.py | 86 | `Image.open()` without encoding= |
| tools/tilesets/build_cliff_offset_review.py | 87 | `Image.open()` without encoding= |
| tools/tilesets/build_cliff_offset_review.py | 88 | `Image.open()` without encoding= |
| tools/tilesets/build_cliff_offset_review.py | 89 | `Image.open()` without encoding= |
| tools/tilesets/build_cliff_offset_review.py | 94 | `Image.open()` without encoding= |
| tools/tilesets/build_ra_temperate_basalt_trees.py | 273 | `Image.open()` without encoding= |
| tools/tilesets/build_shoreline_mass_review.py | 181 | `Image.open()` without encoding= |
| tools/tilesets/build_t08_basalt_study.py | 250 | `Image.open()` without encoding= |
| tools/tilesets/build_t10_t11_basalt.py | 152 | `Image.open()` without encoding= |
| tools/tilesets/build_t10_t11_basalt.py | 153 | `Image.open()` without encoding= |
| tools/tilesets/build_t10_t11_basalt.py | 154 | `Image.open()` without encoding= |
| tools/tilesets/build_t10_t11_basalt.py | 171 | `Image.open()` without encoding= |
| tools/tilesets/build_tc_basalt_from_gimp.py | 75 | `Image.open()` without encoding= |
| tools/tilesets/compare_cliff_topology.py | 74 | `Image.open()` without encoding= |
| tools/tilesets/convert_semantic_mask_sample.py | 45 | `Image.open()` without encoding= |
| tools/tilesets/convert_semantic_mask_sample.py | 46 | `Image.open()` without encoding= |
| tools/tilesets/detect_cliff_dark_noise.py | 74 | `Image.open()` without encoding= |
| tools/tilesets/export_temperate_mask_sources.py | 140 | `path.read_text()` without encoding= |
| tools/tilesets/export_temperate_mask_sources.py | 168 | `path.read_text()` without encoding= |
| tools/tilesets/export_temperate_mask_sources.py | 296 | `write_text()` without encoding= |
| tools/tilesets/export_temperate_mask_sources.py | 298 | `open()` without encoding= |
| tools/tilesets/export_temperate_mask_sources.py | 349 | `write_text()` without encoding= |
| tools/tilesets/generate_inland_lava_rivers.py | 160 | `Image.open()` without encoding= |
| tools/tilesets/generate_lava_river_donor_layer_v2.py | 104 | `Image.open()` without encoding= |
| tools/tilesets/generate_lava_river_donor_layer_v2.py | 150 | `Image.open()` without encoding= |
| tools/tilesets/generate_molten_pool_study.py | 125 | `Image.open()` without encoding= |
| tools/tilesets/generate_sh04_alpha_beach_prototype.py | 568 | `Image.open()` without encoding= |
| tools/tilesets/generate_volcanic_rock_craters.py | 181 | `Image.open()` without encoding= |
| tools/tilesets/generate_volcanic_rock_craters.py | 182 | `Image.open()` without encoding= |
| tools/tilesets/generate_volcanic_tileset.py | 102 | `BARREN_TILESET.read_text()` without encoding= |
| tools/tilesets/generate_volcanic_tileset.py | 112 | `VOLCANIC_TILESET.write_text()` without encoding= |
| tools/tilesets/generate_volcanic_tileset.py | 143 | `path.read_text()` without encoding= |
| tools/tilesets/import_basalt_glow_envelopes.py | 134 | `Image.open()` without encoding= |
| tools/tilesets/manual_river_delta/install_production_vol.py | 38 | `Image.open()` without encoding= |
| tools/tilesets/manual_river_delta/prepare_production.py | 24 | `Image.open()` without encoding= |
| tools/tilesets/manual_river_delta/prepare_production.py | 25 | `Image.open()` without encoding= |
| tools/tilesets/manual_river_delta/prepare_production.py | 26 | `Image.open()` without encoding= |
| tools/tilesets/mark_semantic_cliff_sample.py | 63 | `Image.open()` without encoding= |
| tools/tilesets/mark_semantic_cliff_sample.py | 64 | `Image.open()` without encoding= |
| tools/tilesets/migrate_clear_lava_dependents.py | 207 | `Image.open()` without encoding= |
| tools/tilesets/migrate_clear_lava_dependents.py | 208 | `Image.open()` without encoding= |
| tools/tilesets/migrate_clear_lava_dependents.py | 233 | `Image.open()` without encoding= |
| tools/tilesets/migrate_clear_lava_dependents.py | 234 | `Image.open()` without encoding= |
| tools/tilesets/package_ai_cliff_batch.py | 81 | `Image.open()` without encoding= |
| tools/tilesets/package_ai_cliff_batch.py | 99 | `Image.open()` without encoding= |
| tools/tilesets/package_ai_cliff_batch.py | 100 | `Image.open()` without encoding= |
| tools/tilesets/package_ai_cliff_batch.py | 220 | `Image.open()` without encoding= |
| tools/tilesets/package_ai_cliff_batch.py | 252 | `Image.open()` without encoding= |
| tools/tilesets/place_authored_basalt_columns_on_shores.py | 425 | `Image.open()` without encoding= |
| tools/tilesets/place_authored_basalt_columns_on_shores.py | 437 | `Image.open()` without encoding= |
| tools/tilesets/place_basalt_columns_on_shores.py | 91 | `Image.open()` without encoding= |
| tools/tilesets/preview_thin_basalt_glow_envelope.py | 100 | `Image.open()` without encoding= |
| tools/tilesets/preview_thin_basalt_glow_envelope.py | 102 | `Image.open()` without encoding= |
| tools/tilesets/preview_thin_basalt_glow_envelope.py | 104 | `Image.open()` without encoding= |
| tools/tilesets/preview_yaml_rock_basalt_columns.py | 141 | `Image.open()` without encoding= |
| tools/tilesets/preview_yaml_rock_basalt_columns.py | 211 | `Image.open()` without encoding= |
| tools/tilesets/process_ai_edge_mask.py | 30 | `Image.open()` without encoding= |
| tools/tilesets/process_ai_edge_mask.py | 89 | `Image.open()` without encoding= |
| tools/tilesets/propose_semantic_mask.py | 43 | `Image.open()` without encoding= |
| tools/tilesets/propose_semantic_mask.py | 44 | `Image.open()` without encoding= |
| tools/tilesets/propose_semantic_mask.py | 91 | `open()` without encoding= |
| tools/tilesets/prototype_donor_recolored_bridge_ground.py | 72 | `Image.open()` without encoding= |
| tools/tilesets/prototype_liquid_lava_shore_transition.py | 237 | `Image.open()` without encoding= |
| tools/tilesets/prototype_liquid_lava_shore_transition.py | 240 | `Image.open()` without encoding= |
| tools/tilesets/recolor_basalt_tree_to_reference.py | 64 | `Image.open()` without encoding= |
| tools/tilesets/recolor_basalt_tree_to_reference.py | 65 | `Image.open()` without encoding= |
| tools/tilesets/recolor_basalt_tree_to_reference.py | 66 | `Image.open()` without encoding= |
| tools/tilesets/recolor_cliff_luminance.py | 105 | `Image.open()` without encoding= |
| tools/tilesets/recolor_volcanic_basalt_family.py | 44 | `Image.open()` without encoding= |
| tools/tilesets/recolor_volcanic_basalt_family.py | 68 | `Image.open()` without encoding= |
| tools/tilesets/replace_volcanic_debris_with_basalt.py | 60 | `Image.open()` without encoding= |
| tools/tilesets/shptd.py | 101 | `open()` without encoding= |
| tools/tilesets/transfer_ai_cliff_style.py | 101 | `Image.open()` without encoding= |


## E4 — 62 finding(s)

| file | line | detail |
|---|---|---|
| tools/ai/ab_increment.py | 249 | `subprocess.run()` without check= |
| tools/ai/ab_increment.py | 255 | `subprocess.run()` without check= |
| tools/ai/ab_increment.py | 276 | `subprocess.run()` without check= |
| tools/ai/ab_increment.py | 301 | `subprocess.run()` without check= |
| tools/ai/ab_increment.py | 481 | `subprocess.run()` without check= |
| tools/ai/ab_increment.py | 510 | `subprocess.run()` without check= |
| tools/ai/ab_increment.py | 559 | `subprocess.Popen()` without check= |
| tools/ai/ab_increment.py | 724 | `subprocess.run()` without check= |
| tools/ai/dump_bot_modules.py | 62 | `subprocess.Popen()` without check= |
| tools/ai/dump_bot_modules.py | 77 | `subprocess.run()` without check= |
| tools/ai/run_ai_match_batch.py | 645 | `subprocess.Popen()` without check= |
| tools/ai/run_ai_match_batch.py | 843 | `subprocess.run()` without check= |
| tools/ai/run_league.py | 357 | `subprocess.run()` without check= |
| tools/audit/audit_ai_arch_freshness.py | 36 | `subprocess.run()` without check= |
| tools/audit/audit_ai_frankenstein.py | 76 | `subprocess.run()` without check= |
| tools/audit/audit_ca_unused.py | 46 | `subprocess.run()` without check= |
| tools/audit/audit_central_ids.py | 26 | `subprocess.run()` without check= |
| tools/audit/audit_chrome_master_freshness.py | 136 | `subprocess.run()` without check= |
| tools/audit/audit_doc_claims.py | 104 | `subprocess.run()` without check= |
| tools/audit/audit_doc_health.py | 139 | `subprocess.run()` without check= |
| tools/audit/audit_engine_freshness.py | 52 | `subprocess.run()` without check= |
| tools/audit/audit_fransbot_lists.py | 33 | `subprocess.run()` without check= |
| tools/audit/audit_guerrilla_roles.py | 29 | `subprocess.run()` without check= |
| tools/audit/ca_vendor_sync.py | 107 | `subprocess.run()` without check= |
| tools/audit/ca_vendor_sync.py | 161 | `subprocess.run()` without check= |
| tools/audit/ca_vendor_sync.py | 183 | `subprocess.run()` without check= |
| tools/audit/gen_release_baseline.py | 94 | `subprocess.run()` without check= |
| tools/audit/gen_release_baseline.py | 112 | `subprocess.run()` without check= |
| tools/audit/run_all.py | 120 | `subprocess.run()` without check= |
| tools/audit/run_all.py | 144 | `subprocess.run()` without check= |
| tools/audit/run_all.py | 170 | `subprocess.run()` without check= |
| tools/audit/triage_release_identities.py | 139 | `subprocess.run()` without check= |
| tools/balance/check_determinism.py | 94 | `subprocess.run()` without check= |
| tools/balance/compensate_retrofit.py | 170 | `subprocess.run()` without check= |
| tools/balance/fit_baseband.py | 230 | `subprocess.run()` without check= |
| tools/balance/gen_derived_stats.py | 60 | `subprocess.run()` without check= |
| tools/balance/run_pipeline.py | 117 | `subprocess.run()` without check= |
| tools/balance/run_with_guard.py | 39 | `subprocess.Popen()` without check= |
| tools/balance/splice_templates.py | 115 | `subprocess.run()` without check= |
| tools/balance/verify_generator_sync.py | 56 | `subprocess.run()` without check= |
| tools/balance/verify_retrofit.py | 239 | `subprocess.run()` without check= |
| tools/hooks/bash_guard.py | 112 | `subprocess.run()` without check= |
| tools/hooks/bash_guard.py | 120 | `subprocess.run()` without check= |
| tools/hooks/bash_guard.py | 136 | `subprocess.run()` without check= |
| tools/hooks/bash_guard.py | 186 | `subprocess.run()` without check= |
| tools/hooks/bash_guard.py | 196 | `subprocess.run()` without check= |
| tools/hooks/bash_guard.py | 201 | `subprocess.run()` without check= |
| tools/hooks/exec_guard.py | 45 | `subprocess.run()` without check= |
| tools/hooks/test_bash_guard.py | 43 | `subprocess.run()` without check= |
| tools/hooks/test_bash_guard.py | 50 | `subprocess.run()` without check= |
| tools/hooks/test_bash_guard.py | 58 | `subprocess.run()` without check= |
| tools/hooks/test_bash_guard.py | 77 | `subprocess.run()` without check= |
| tools/prep_overmind_dataset.py | 132 | `subprocess.run()` without check= |
| tools/reference/splice_peer_section.py | 73 | `subprocess.run()` without check= |
| tools/tests/ai_bot_player_gate.py | 86 | `subprocess.Popen()` without check= |
| tools/tests/ai_d2k_production_gate.py | 70 | `subprocess.Popen()` without check= |
| tools/tests/ai_raid_gate.py | 93 | `subprocess.Popen()` without check= |
| tools/tests/ai_squad_gate.py | 92 | `subprocess.Popen()` without check= |
| tools/tests/test_family_bases.py | 68 | `subprocess.run()` without check= |
| tools/tests/test_peer_export.py | 454 | `subprocess.run()` without check= |
| tools/tests/test_peer_export.py | 541 | `subprocess.run()` without check= |
| tools/wav_to_aud.py | 128 | `subprocess.run()` without check= |


## FAIL

- E1: 5 > baseline 2
- E2: 141 > baseline 30
- E3: 161 > baseline 90
- E4: 62 > baseline 9
- 1 file(s) do not parse

