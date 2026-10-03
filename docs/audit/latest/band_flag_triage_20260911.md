# Baseband flag triage

**REVIEW REQUIRED; diagnostic only.** Every listed action is HOLD. A flag does not prove a gameplay regression and does not authorize repricing, anchor movement or YAML writeback.

## Policy

- Hard floor: **50%**; soft floor: **75%**; hard ceiling: **350%**.
- Input rows: **83**; flagged rows: **37**; classes: **14**.
- Band counts: `{'HARD_HIGH': 5, 'HARD_LOW': 19, 'SOFT_LOW': 13}`; review lanes: `{'ANCHOR_OR_INPUT': 30, 'CLASS_MEMBERSHIP': 7}`.
- Derived class membership, source limitations, inactive variants and unsigned anchors stay visible as blockers.

## Flagged rows

| actor | class | ratio | band | lane | blockers |
|---|---|---:|---|---|---|
| `td_nod_stealthtank` | `missile_vehicle` | 0.135x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; INACTIVE_VARIANT_LIMITATION; below_hard_floor |
| `td_gdi_exosuit` | `fire_support` | 0.188x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `ra1_soviets_gatlingtank` | `anti_air_vehicle` | 0.276x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; INACTIVE_VARIANT_LIMITATION; below_hard_floor |
| `ra1_soviets_teslatank` | `fire_support` | 0.290x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; INACTIVE_VARIANT_LIMITATION; below_hard_floor |
| `td_nod_ssmlauncher` | `fire_support` | 0.297x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `td_gdi_mlrs` | `missile_vehicle` | 0.304x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `ra1_soviets_gorynychtank` | `line_breaker` | 0.347x | HARD_LOW | CLASS_MEMBERSHIP | CLASS_ANCHOR_NOT_SIGNED_OFF; DERIVED_CLASS_MEMBERSHIP; below_hard_floor |
| `td_nod_flametankmkii` | `line_breaker` | 0.358x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `td_nod_flametank` | `line_breaker` | 0.381x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `td_nod_reconbike` | `missile_vehicle` | 0.383x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `td_gdi_mammothtankmkiii` | `high_tech_tank` | 0.409x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `ra1_allies_alliedheavyaatank` | `anti_air_vehicle` | 0.414x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `ra1_allies_alliedmediumtank` | `mbt` | 0.424x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `td_nod_chemicalattackbike` | `missile_vehicle` | 0.441x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `ra1_soviets_heavytank` | `mbt` | 0.453x | HARD_LOW | CLASS_MEMBERSHIP | CLASS_ANCHOR_NOT_SIGNED_OFF; DERIVED_CLASS_MEMBERSHIP; below_hard_floor |
| `ra1_soviets_mortarsoldier` | `mortar` | 0.465x | HARD_LOW | CLASS_MEMBERSHIP | CLASS_ANCHOR_NOT_SIGNED_OFF; DERIVED_CLASS_MEMBERSHIP; below_hard_floor |
| `td_gdi_battletank` | `mbt` | 0.480x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `ra1_soviets_heatraytank` | `fire_support` | 0.494x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `td_nod_artillery` | `artillery` | 0.497x | HARD_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_hard_floor |
| `ra1_soviets_flamethrower` | `heavy_infantry` | 0.566x | SOFT_LOW | CLASS_MEMBERSHIP | CLASS_ANCHOR_NOT_SIGNED_OFF; DERIVED_CLASS_MEMBERSHIP; below_soft_floor |
| `ra1_soviets_mammothtank` | `high_tech_tank` | 0.569x | SOFT_LOW | CLASS_MEMBERSHIP | CLASS_ANCHOR_NOT_SIGNED_OFF; DERIVED_CLASS_MEMBERSHIP; INACTIVE_VARIANT_LIMITATION; below_soft_floor |
| `ra1_allies_alliedtigerheavytank` | `mbt` | 0.578x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `td_gdi_mammothtank` | `high_tech_tank` | 0.591x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `td_gdi_archerartillery` | `artillery_tank` | 0.600x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `td_gdi_predatortank` | `mbt` | 0.606x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `td_nod_specterartillery` | `artillery` | 0.621x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `ra1_allies_alliedartillery` | `artillery` | 0.635x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `ra1_soviets_hammertank` | `mbt` | 0.639x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `ra1_allies_alliedlighttank` | `light_tank` | 0.670x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `ra1_allies_sheridanassaulttank` | `light_tank` | 0.724x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `ra1_soviets_kotinnucleartank` | `mbt` | 0.741x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `td_nod_lighttank` | `light_tank` | 0.744x | SOFT_LOW | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; below_soft_floor |
| `td_nod_stealthsoldier` | `special_forces` | 4.094x | HARD_HIGH | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; above_hard_ceiling |
| `ra1_allies_machinegunner` | `special_forces` | 4.164x | HARD_HIGH | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; above_hard_ceiling |
| `ra1_soviets_commissar` | `pure_sniper` | 4.737x | HARD_HIGH | CLASS_MEMBERSHIP | CLASS_ANCHOR_NOT_SIGNED_OFF; DERIVED_CLASS_MEMBERSHIP; above_hard_ceiling |
| `td_gdi_empgrenadier` | `grenadier` | 10.119x | HARD_HIGH | CLASS_MEMBERSHIP | CLASS_ANCHOR_NOT_SIGNED_OFF; DERIVED_CLASS_MEMBERSHIP; above_hard_ceiling |
| `td_gdi_officer` | `special_forces` | 11.442x | HARD_HIGH | ANCHOR_OR_INPUT | CLASS_ANCHOR_NOT_SIGNED_OFF; above_hard_ceiling |

No row is a calibration or anchor recommendation. Resolve class membership, source coverage and role validity before reconsidering any flag.
