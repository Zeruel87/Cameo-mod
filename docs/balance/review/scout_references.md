# `scout` — reference assignment for review

**Generated** by `python tools/balance/assign_references.py --review scout`. Regenerates — record decisions and re-run rather than hand-editing.

> ⛔ **A PROPOSAL LIST, NOT EVIDENCE.** Until this review is done the class has no grounded
> members and therefore no anchor (`REFERENCE_METHOD.md` §9.9).

## §0 — State of the class

| | |
|---|--:|
| members | **30** |
| assigned at least one reference | **17** |
| **with ≥2 NAME-backed references** | **4** |
| with ≥2 name-or-shape references | 8 |
| members with NO reference at all | **13** |
| of those, FORMULA-ONLY by routing | **5** |

⭐ **Routed.** Every proposal below comes from a reference FACTION this unit's Cameo faction is mapped to (`tools/balance/faction_routes.py`), never from the whole corpus. A member whose faction has no route is formula-only by ruling, not unmatched by accident.

Confidence: FAIR 5 · SHAPE 11 · **STRONG 7** · **WEAK 5**

* **STRONG** exact/alias name, or name overlap backed by matching shape
* **FAIR** a real name overlap, shape unconfirmed
* **SHAPE** same position in its own roster; the name says nothing — evidence for a distribution method, NOT a claim the two are the same unit
* **WEAK** neither; the greedy assigned the best of a bad field

⚠ **No reference at all** — formula-only unless the review rescues them:

* `E1` — cost 100.0
* `conehead2.nax` — cost 500.0
* `forgotten_mutant_sp` — cost 160.0
* `forgotten_mutant_wild` — cost 160.0
* `forgotten_mutantsoldier_sp` — cost 250.0
* `ixian_lightinfantry` — cost 150.0 — ⛔ no route for faction 'ixian'
* `light_inf` — cost 150.0 — ⛔ no declared Cameo faction in the id
* `ordos_lightinfantry` — cost 120.0
* `ra2e2.black` — cost 150.0
* `tkm_marine` — cost 300.0 — ⛔ no route for faction 'tkm'
* `tkm_rifleman` — cost 120.0 — ⛔ no route for faction 'tkm'
* `undead.nax` — cost 100.0
* `zerg_spithid` — cost 300.0 — ⛔ no declared Cameo faction in the id

---

## §1 — NAME-backed proposals — confirm or strike

| ok? | conf | unit | source | reference unit | name | role | cost |
|:--:|---|---|---|---|--:|--:|--:|
| ☐ | STRONG | `forgotten_mutant` | Shattered Paradise **(home)** | Mutant Engineer | 0.90 | 0.36 | 0.54 |
| ☐ | FAIR | `ra1_soviets_rifleinfantry` | OpenRA Red Alert **(home)** | Flame Infantry | 0.85 | 0.59 | 0.66 |
| ☐ | STRONG | `ra2_allies_gi` | Romanov's Vengeance **(home)** | G.I. | 1.00 | 0.84 | 0.68 |
| ☐ | STRONG | `ra2_allies_gi` | Valiant Shades | G.I. | 1.00 | 0.75 | 0.95 |
| ☐ | STRONG | `ra2_soviets_conscript` | Romanov's Vengeance **(home)** | Conscript | 1.00 | 0.92 | 0.61 |
| ☐ | STRONG | `ra2_soviets_conscript` | Valiant Shades | Conscript | 1.00 | 0.75 | 0.99 |
| ☐ | STRONG | `td_gdi_minigunner` | OpenRA Tiberian Dawn **(home)** | Minigunner | 1.00 | 0.71 | 0.99 |
| ☐ | STRONG | `td_nod_minigunner` | Combined Arms **(home)** | Mini-Gunner | 1.00 | 0.61 | 0.99 |
| ☐ | FAIR | `ts_gdi_lightinfantry` | OpenRA Tiberian Sun **(home)** | Jump Jet Infantry | 0.64 | 0.72 | 0.49 |
| ☐ | FAIR | `ts_gdi_lightinfantry` | Shattered Paradise **(home)** | Jumpjet Infantry | 0.64 | 0.71 | 0.60 |
| ☐ | FAIR | `ts_nod_lightinfantry` | Crystallized Nexus **(home)** | Rocket Infantry | 0.67 | 0.68 | 0.85 |
| ☐ | FAIR | `ts_nod_lightinfantry` | OpenRA Tiberian Sun **(home)** | Rocket Infantry | 0.67 | 0.63 | 0.78 |

---

## §2 — SHAPE-only proposals

Same position in its own roster, unrelated name. Real evidence for the distribution method; your call whether it counts.

| ok? | conf | unit | source | reference unit | name | role | cost |
|:--:|---|---|---|---|--:|--:|--:|
| ☐ | SHAPE | `asianalliance_asianmilitia` | Generals Alpha | Red Guard | 0.10 | 0.92 | 0.96 |
| ☐ | SHAPE | `forgotten_mutantsoldier` | Shattered Paradise **(home)** | Tiberian Fiend | 0.39 | 0.82 | 0.98 |
| ☐ | SHAPE | `latinsyndicate_latinmilitia` | Generals Alpha | Rebel | 0.12 | 0.85 | 0.99 |
| ☐ | SHAPE | `naxis_naxiriflerecruit` | OpenE2140 | Android A02 | 0.15 | 0.83 | 0.62 |
| ☐ | SHAPE | `ra1_allies_rifleinfantry` | OpenRA Red Alert **(home)** | Medic | 0.11 | 0.86 | 0.83 |
| ☐ | SHAPE | `ra1_allies_rifleinfantry` | Combined Arms **(home)** | Cryo Trooper | 0.25 | 0.84 | 0.16 |
| ☐ | SHAPE | `ra1_soviets_ak47conscript` | OpenRA Red Alert **(home)** | Thief | 0.11 | 0.98 | 0.29 |
| ☐ | SHAPE | `ra1_soviets_rifleinfantry` | Combined Arms **(home)** | Shock Trooper | 0.16 | 0.81 | 0.56 |
| ☐ | SHAPE | `td_gdi_minigunner` | Combined Arms **(home)** | Zone Raider | 0.30 | 0.84 | 0.16 |
| ☐ | SHAPE | `td_nod_minigunner` | OpenRA Tiberian Dawn **(home)** | Visceroid | 0.32 | 0.79 | 0.51 |
| ☐ | SHAPE | `ts_nod_lightinfantry` | Shattered Paradise **(home)** | Militant | 0.57 | 0.85 | 0.97 |

---

## §3 — WEAK proposals — STRUCK, not reviewed

**5 rows across 5 members** were the greedy taking the best of a bad field. Struck per the maintainer's ruling so this sheet only asks about proposals worth judging.

⚠ Listed so nothing vanishes silently — a member whose only proposals were weak should look struck, not unmatched.

| unit | struck | what they were |
|---|--:|---|
| `futuretech_scoutdroid` | 1 | OpenE2140: SILVER R |
| `naxis_coneheadsknights` | 1 | OpenE2140: Android A03 |
| `naxis_naxiriflesoldier` | 1 | OpenE2140: Android A01 |
| `ra1_soviets_ak47conscript` | 1 | Combined Arms: Soviet Flamethrower |
| `ts_gdi_lightinfantry` | 1 | Crystallized Nexus: Marine |

⛔ **Members left with NOTHING after the strike** — formula-only unless the review rescues them:

* `futuretech_scoutdroid`
* `naxis_coneheadsknights`
* `naxis_naxiriflesoldier`

