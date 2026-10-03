# audit_doc_claims — do the documents still match the tree?

Registry: `docs/audit/doc_claims.yaml` — **43** claims.

A number in prose is true only on the day it is written. These are the claims a DECISION rests on, re-measured every run.

| claim | documented | measured | status |
|---|--:|--:|---|
| `ai_contract_distinct_module_types` | 68 | 68 | ✅ |
| `ai_contract_player_module_instances` | 93 | 93 | ✅ |
| `ai_contract_world_module_instances` | 1 | 1 | ✅ |
| `shield_versus_mean` | 97.6157 | 184.71 | **MISMATCH** |
| `shield_hp_factor` | 1.02443 | 0.541389 | **MISMATCH** |
| `shield_damage_share` | 0.0183167 | 0.0160276 | **MISMATCH** |
| `always_on_shield_actors` | 58 | 58 | ✅ |
| `always_on_shielded_buildings` | 16 | 16 | ✅ |
| `live_damage_multipliers` | 326 | 326 | ✅ |
| `multi_main_fired_weapons` | 1 | 1 | ✅ |
| `percentage_denominator_unset` | 436 | 423 | **MISMATCH** |
| `unmigrated_scout_damage_multiplier` | 0 | 0 | ✅ |
| `meters_filling_before_death` | 329 | 329 | ✅ |
| `corrosion_meter_actors` | 856 | 856 | ✅ |
| `w24_multi_main_fed` | 217 | 217 | ✅ |
| `physical_state_fired_weapons` | 549 | 549 | ✅ |
| `plating_row_ties` | 0 | 0 | ✅ |
| `plating_families` | 52 | 52 | ✅ |
| `signed_off_class_anchors` | 0 | 0 | ✅ |
| `warhead_family_reach` | 1509 | 1509 | ✅ |
| `unconverted_template_inheritors` | 402 | 402 | ✅ |
| `ledgers_drifted` | 0 | 1 | **MISMATCH** |
| `armament_multi_role_actors` | 104 | 104 | ✅ |
| `armament_air_role_invisible_to_the_name_test` | 41 | 41 | ✅ |
| `dta_projectile_roles_resolved` | 60 | 60 | ✅ |
| `dta_elite_weapons_reachable` | 131 | 131 | ✅ |
| `armament_unproven_peer_votes` | 0 | 0 | ✅ |
| `armament_reference_tier_original` | 140 | 141 | **MISMATCH** |
| `armament_pairing_input_fingerprints` | 476 | 514 | **MISMATCH** |
| `shared_attack_cycle_actors` | 15 | 15 | ✅ |
| `mammoth_armament_voters` | 3 | 3 | ✅ |
| `ini_armament_views_eligible` | 1388 | 1388 | ✅ |
| `aa_split_pairs_compliant` | 39 | 39 | ✅ |
| `same_target_range_groups` | 387 | 387 | ✅ |
| `mammoth_named_dual_slot_separation_ratio` | 1.71 | 1.71 | ✅ |
| `charged_actor_cycle_actors` | 14 | 14 | ✅ |
| `ranged_charge_actors` | 4 | 4 | ✅ |
| `railtower_immediate_reacquisition_period` | 210 | 210 | ✅ |
| `tesla_coil_attack_period` | 131 | 131 | ✅ |
| `cameo_family_labelled_weapons` | 1567 | 1567 | ✅ |
| `warhead_reference_groups` | 1674 | 1674 | ✅ |
| `cameo_shaped_families` | 53 | 53 | ✅ |
| `cameo_element_bearing_families` | 23 | 23 | ✅ |

**FAIL — a document and the tree disagree.**

Fix whichever is wrong, and if the tree is right update `value` in `doc_claims.yaml` **and every doc listed under `docs:`** in the SAME commit. That co-update is the point: it is how the `Shield = top + floor` duplication survived in two documents for weeks.

## Review cadence (for what a number cannot capture)

This audit pins numeric claims. **Prose contradictions — two documents asserting incompatible LAWS in words — still need a human read.** The failure mode is specific and worth naming: a ruling gets made, written into one document, and the older statement is left standing somewhere else. Both then look authoritative.

Known instances of exactly that, all found by accident rather than by process:

| the newer ruling | what still contradicted it |
|---|---|
| Shield ladder is derived (DESIGN §12.0c) | `Shield = top + floor` in DESIGN **and** ARMOR_SYSTEM |
| R1 — veterancy grants HP | advice to keep veterancy multipliers, accepted |
| Platings are layer-SELECTED | "armor types AVERAGE" in memory + §A1–A4 |
| W24 answers the 3-same-family question | W23 still listed as blocked on a ruling |

**The rule that would have caught all four:** a ruling is not landed until the OLD statement is struck in every document that carries it. Grep for the old claim before writing the new one — `docs:` lists in this registry exist to make that mechanical for numbers, and the same discipline applies to laws.
