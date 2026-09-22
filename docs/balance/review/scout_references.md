# `scout` — reference assignment for review

**Generated** by `python tools/balance/assign_references.py --review scout`. Regenerates — record decisions and re-run rather than hand-editing.

> ⛔ **A PROPOSAL LIST, NOT EVIDENCE.** Until this review is done the class has no grounded
> members and therefore no anchor (`REFERENCE_METHOD.md` §9.9).

## §0 — State of the class

| | |
|---|--:|
| members | **33** |
| assigned at least one reference | **9** |
| **with ≥2 NAME-backed references** | **9** |
| with ≥2 name-or-shape references | 9 |
| members with NO reference at all | **24** |
| of those, FORMULA-ONLY by routing | **4** |

⭐ **Routed.** Every proposal below comes from a reference FACTION this unit's Cameo faction is mapped to (`tools/balance/faction_routes.py`), never from the whole corpus. A member whose faction has no route is formula-only by ruling, not unmatched by accident.

Confidence: FAIR 8 · **STRONG 27**

* **STRONG** exact/alias name, or name overlap backed by matching shape
* **FAIR** a real name overlap, shape unconfirmed
* **SHAPE** same position in its own roster; the name says nothing — evidence for a distribution method, NOT a claim the two are the same unit
* **WEAK** neither; the greedy assigned the best of a bad field

⚠ **No reference at all** — formula-only unless the review rescues them:

* `E1` — cost 100.0
* `asianalliance_asianmilitia` — cost 110.0
* `atreides_lightinfantry` — cost 150.0
* `corrino_lightinfantry` — cost 150.0 — ⛔ no route for faction 'corrino'
* `forgotten_mutant_sp` — cost 160.0
* `forgotten_mutant_wild` — cost 160.0
* `forgotten_mutantsoldier` — cost 250.0
* `forgotten_mutantsoldier_sp` — cost 250.0
* `futuretech_scoutdroid` — cost 200.0
* `harkonnen_lightinfantry` — cost 150.0
* `ixian_lightinfantry` — cost 150.0 — ⛔ no route for faction 'ixian'
* `latinsyndicate_latinmilitia` — cost 130.0
* `light_inf` — cost 150.0 — ⛔ no declared Cameo faction in the id
* `naxis_conehead2` — cost 500.0
* `naxis_coneheadsknights` — cost 1000.0
* `naxis_naxiriflerecruit` — cost 75.0
* `naxis_naxiriflesoldier` — cost 100.0
* `naxis_undead` — cost 100.0
* `ordos_lightinfantry` — cost 120.0
* `ra1_soviets_ak47conscript` — cost 200.0
* `ra2e2.black` — cost 150.0
* `tkm_marine` — cost 300.0
* `tkm_rifleman` — cost 120.0
* `zerg_spithid` — cost 300.0 — ⛔ no declared Cameo faction in the id

---

## §1 — NAME-backed proposals — confirm or strike

| ok? | conf | unit | source | reference unit | name | role | cost |
|:--:|---|---|---|---|--:|--:|--:|
| ☐ | STRONG | `forgotten_mutant` | Twisted Insurrection | Warrior | 1.00 | 0.00 | 0.60 |
| ☐ | FAIR | `forgotten_mutant` | Shattered Paradise **(home)** | Tyrant | 0.67 | 0.00 | 0.50 |
| ☐ | STRONG | `ra1_allies_rifleinfantry` | Combined Arms **(home)** | Rifle Infantry | 1.00 | 0.00 | 0.63 |
| ☐ | STRONG | `ra1_allies_rifleinfantry` | DTA Enhanced | Rifle Infantry | 1.00 | 0.00 | 0.70 |
| ☐ | STRONG | `ra1_allies_rifleinfantry` | OpenRA Red Alert **(home)** | Rifle Infantry | 1.00 | 0.00 | 0.85 |
| ☐ | STRONG | `ra1_soviets_rifleinfantry` | Combined Arms **(home)** | Rifle Infantry | 1.00 | 0.00 | 0.65 |
| ☐ | STRONG | `ra1_soviets_rifleinfantry` | DTA Enhanced | Rifle Infantry | 1.00 | 0.00 | 0.72 |
| ☐ | STRONG | `ra1_soviets_rifleinfantry` | OpenRA Red Alert **(home)** | Rifle Infantry | 1.00 | 0.00 | 0.73 |
| ☐ | STRONG | `ra2_allies_gi` | CnC Reloaded **(home)** | GI | 1.00 | 0.00 | 0.74 |
| ☐ | STRONG | `ra2_allies_gi` | Mental Omega **(home)** | G.I. | 1.00 | 0.00 | 0.76 |
| ☐ | STRONG | `ra2_allies_gi` | RA2 Reborn | GI | 1.00 | 0.00 | 0.74 |
| ☐ | STRONG | `ra2_allies_gi` | Red Resurrection | GI | 1.00 | 0.00 | 0.66 |
| ☐ | STRONG | `ra2_allies_gi` | Romanov's Vengeance **(home)** | G.I. | 1.00 | 0.00 | 0.70 |
| ☐ | STRONG | `ra2_allies_gi` | Valiant Shades | G.I. | 1.00 | 0.00 | 0.63 |
| ☐ | STRONG | `ra2_allies_gi` | RA2 0XX | Allied Guardian GI | 0.80 | 0.00 | 0.78 |
| ☐ | STRONG | `ra2_soviets_conscript` | CnC Reloaded **(home)** | Conscript | 1.00 | 0.00 | 0.76 |
| ☐ | STRONG | `ra2_soviets_conscript` | Mental Omega **(home)** | Conscript | 1.00 | 0.00 | 0.83 |
| ☐ | STRONG | `ra2_soviets_conscript` | Red Resurrection | Conscript | 1.00 | 0.00 | 0.72 |
| ☐ | STRONG | `ra2_soviets_conscript` | Romanov's Vengeance **(home)** | Conscript | 1.00 | 0.00 | 0.92 |
| ☐ | STRONG | `ra2_soviets_conscript` | Valiant Shades | Conscript | 1.00 | 0.00 | 0.73 |
| ☐ | FAIR | `ra2_soviets_conscript` | RA2 0XX | Soviet Conscript | 0.85 | 0.00 | 0.72 |
| ☐ | STRONG | `td_gdi_minigunner` | Combined Arms **(home)** | Mini-Gunner | 1.00 | 0.00 | 0.48 |
| ☐ | STRONG | `td_gdi_minigunner` | DTA Enhanced | Minigunner | 1.00 | 0.00 | 0.60 |
| ☐ | STRONG | `td_gdi_minigunner` | OpenRA Tiberian Dawn **(home)** | Minigunner | 1.00 | 0.00 | 0.70 |
| ☐ | STRONG | `td_nod_minigunner` | Combined Arms **(home)** | Mini-Gunner | 1.00 | 0.00 | 0.57 |
| ☐ | STRONG | `td_nod_minigunner` | DTA Enhanced | Minigunner | 1.00 | 0.00 | 0.67 |
| ☐ | STRONG | `td_nod_minigunner` | OpenRA Tiberian Dawn **(home)** | Minigunner | 1.00 | 0.00 | 0.74 |
| ☐ | STRONG | `ts_gdi_lightinfantry` | OpenRA Tiberian Sun **(home)** | Light Infantry | 1.00 | 0.00 | 0.89 |
| ☐ | FAIR | `ts_gdi_lightinfantry` | CnC Reloaded | Jumpjet Infantry | 0.64 | 0.00 | 0.75 |
| ☐ | FAIR | `ts_gdi_lightinfantry` | Shattered Paradise **(home)** | Jumpjet Infantry | 0.64 | 0.00 | 0.72 |
| ☐ | FAIR | `ts_gdi_lightinfantry` | Twisted Insurrection | Ranger | — | 0.00 | 0.94 |
| ☐ | STRONG | `ts_nod_lightinfantry` | OpenRA Tiberian Sun **(home)** | Light Infantry | 1.00 | 0.00 | 0.89 |
| ☐ | FAIR | `ts_nod_lightinfantry` | CnC Reloaded | Rocket Infantry | 0.67 | 0.00 | 0.62 |
| ☐ | FAIR | `ts_nod_lightinfantry` | Crystallized Nexus **(home)** | Rocket Infantry | 0.67 | 0.00 | 0.64 |
| ☐ | FAIR | `ts_nod_lightinfantry` | Twisted Insurrection | Tank Hunter | — | 0.00 | 0.81 |

---

## §2 — SHAPE-only proposals

Same position in its own roster, unrelated name. Real evidence for the distribution method; your call whether it counts.

| ok? | conf | unit | source | reference unit | name | role | cost |
|:--:|---|---|---|---|--:|--:|--:|

