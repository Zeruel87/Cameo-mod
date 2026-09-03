# audit_doc_claims — do the documents still match the tree?

Registry: `docs/audit/doc_claims.yaml` — **19** claims.

A number in prose is true only on the day it is written. These are the claims a DECISION rests on, re-measured every run.

| claim | documented | measured | status |
|---|--:|--:|---|
| `shield_versus_mean` | 189.088 | 189.805 | ✅ |
| `shield_hp_factor` | 0.528855 | 0.526855 | ✅ |
| `shield_damage_share` | 0.01432 | 0.0146486 | ✅ |
| `always_on_shield_actors` | 58 | 58 | ✅ |
| `always_on_shielded_buildings` | 16 | 16 | ✅ |
| `live_damage_multipliers` | 354 | 354 | ✅ |
| `multi_main_fired_weapons` | 925 | 925 | ✅ |
| `percentage_denominator_unset` | 0 | 0 | ✅ |
| `unmigrated_scout_damage_multiplier` | 15 | 15 | ✅ |
| `meters_filling_before_death` | 137 | 137 | ✅ |
| `corrosion_meter_actors` | 785 | 785 | ✅ |
| `w24_multi_main_fed` | 380 | 380 | ✅ |
| `physical_state_fired_weapons` | 460 | 460 | ✅ |
| `plating_row_ties` | 0 | 0 | ✅ |
| `plating_families` | 46 | 46 | ✅ |
| `signed_off_class_anchors` | 0 | 0 | ✅ |
| `warhead_family_reach` | 1245 | 1245 | ✅ |
| `unconverted_template_inheritors` | 1162 | 1162 | ✅ |
| `ledgers_drifted` | 0 | 0 | ✅ |

_clean_ — every registered claim still matches the tree.

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
