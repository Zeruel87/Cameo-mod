# audit_doc_claims — do the documents still match the tree?

Registry: `docs/audit/doc_claims.yaml` — **19** claims.

A number in prose is true only on the day it is written. These are the claims a DECISION rests on, re-measured every run.

| claim | documented | measured | status |
|---|--:|--:|---|
| `shield_versus_mean` | 175.919 | 176.598 | ✅ |
| `shield_hp_factor` | 0.568442 | 0.566258 | ✅ |
| `shield_damage_share` | 0.0152182 | 0.0151465 | ✅ |
| `always_on_shield_actors` | 58 | 58 | ✅ |
| `always_on_shielded_buildings` | 16 | 16 | ✅ |
| `live_damage_multipliers` | 356 | 356 | ✅ |
| `multi_main_fired_weapons` | 192 | 856 | **MISMATCH** |
| `percentage_denominator_unset` | 183 | 183 | ✅ |
| `unmigrated_scout_damage_multiplier` | 18 | 18 | ✅ |
| `meters_filling_before_death` | 269 | 216 | **MISMATCH** |
| `corrosion_meter_actors` | 817 | 817 | ✅ |
| `w24_multi_main_fed` | 429 | 455 | **MISMATCH** |
| `physical_state_fired_weapons` | 533 | 539 | **MISMATCH** |
| `plating_row_ties` | 0 | 0 | ✅ |
| `plating_families` | 48 | 48 | ✅ |
| `signed_off_class_anchors` | 0 | 0 | ✅ |
| `warhead_family_reach` | 1415 | 1415 | ✅ |
| `unconverted_template_inheritors` | 1595 | 1601 | **MISMATCH** |
| `ledgers_drifted` | 0 | 0 | ✅ |

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
