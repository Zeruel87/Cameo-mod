# Cameo Design/Instruction Document Review


> ⚠ **SUPERSEDED 2026-08-23.** This review's findings were acted on by the documentation
> audit (#269/#270/#272): the handoffs it cites are archived under `docs/history/handoffs/`
> and the drift numbers it reports were re-measured — generator sync is now drift = 0.
> Kept for the reasoning, not for the numbers.

**Scope:** Review the primary design, instruction, and audit documents for contradictions, stale claims, conflicting authority statements, and missing/incomplete cross-references.  
**Method:** Read listed docs, run `git log`, the audit suite, and targeted `grep`/Python counts against the live tree.  
**Constraint:** Only `docs/research/doc_review.md` is created; no source, YAML, or tracked documentation was edited and no commit was made.

---

## 1. Executive Summary

The Cameo document set is large, layered, and intentionally historical in places.  It is **not free of significant conflicts**.  The two strongest healthy signals are:

- `tools/audit/find_empty_warhead.py` reports **0** empty warheads, so the boot-gating guard for warhead type NREs is currently clean.
- `tools/audit/audit_doc_claims.py` exists and is catching stale numeric claims; it currently flags **five** registry mismatches.

The most serious problems are:

1. **Generator-sync drift is misreported.**  Several docs claim `drift = 0` or `drift = 1`; live `tools/balance/verify_generator_sync.py` reports **drift = 10** plus one ungenerated template (`^Warhead_Sniper_Light`).
2. **`BALANCE_PROGRAM_PLAN.md` has internal status contradictions** for W2, W4, W20, and stale W24 numbers (39% / 805 of 2053).
3. **Template-library counts and proposed naming are out of date** (`55/24/27`, `55/25/45`, `^Proj*`/`^Fx*`) versus the live `weapons.yaml` (`99/30/47`, `^Projectile_*`/`^Effect_*`).
4. **The `Warhead@1Dam` retirement is not true in the live tree** (95 fired weapons still use it; 1,434 raw occurrences in `mods/cameo`).
5. **Authority over balance status is split** among `BALANCE_PROGRAM_PLAN.md`, `BALANCE_MEGAPLAN.md`, `ROADMAP.md`, and the historical `AREADAMAGE_HANDOFF.md`, with inconsistent pointers.

Historical disclaimers are present on `AREADAMAGE_HANDOFF.md` and (implicitly) on `AI_HANDOFF_2026-08-05.md`, but those disclaimers do not prevent stale numeric claims from being read as current.

---

## 2. Contradictions / Conflicts

| # | Topic | Conflicting Documents & Claims | File / Line or Section | Live Evidence | Notes |
|---|-------|-------------------------------|------------------------|---------------|-------|
| 1 | **Generator sync drift** | `AREADAMAGE_HANDOFF.md` §0: "`verify_generator_sync.py` reports **drift = 0**" | `docs/history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md` lines 28-33 | `python tools/balance/verify_generator_sync.py` exits 1 and reports: <br>• 1 ungenerated template (`^Warhead_Sniper_Light`) <br>• 10 template blocks with drift <br>• `drift = 10` | `AREADAMAGE_HANDOFF.md` is marked historical, but the drift=0 claim is still present. |
|   |   | `BALANCE_MEGAPLAN.md` §1: "A1 generator reconcile: ✅ DONE ... `verify_generator_sync.py` reports **drift = 0**" | `docs/design/BALANCE_MEGAPLAN.md` lines 57-59 |   |   |
|   |   | `BALANCE_PIPELINE_ESTIMATE.md` §1: "`verify_generator_sync.py` proves **drift = 0**" | `docs/design/BALANCE_PIPELINE_ESTIMATE.md` lines 40-43 |   |   |
|   |   | `AI_HANDOFF_2026-08-05.md`: "`verify_generator_sync.py` must report `drift = 0`" | `docs/history/handoffs/AI_HANDOFF_2026-08-05.md` line 376 |   |   |
|   |   | `BALANCE_PROGRAM_PLAN.md`: "drift = 1 (`^Warhead_Sniper_Light`)" | `docs/design/BALANCE_PROGRAM_PLAN.md` lines 460, 1229 |   | Even the "drift = 1" figure is now stale (live = 10). |
|   |   | `PHYSICAL_STATE_SYSTEM.md`: "`verify_generator_sync` drift stays **1**" | `docs/design/PHYSICAL_STATE_SYSTEM.md` line 432 |   |   |
|   |   | `ROADMAP.md`: "Generator drift stays 1" | `docs/design/ROADMAP.md` line 83 |   |   |
|   |   | `SHIELD_AND_NORMALISATION_PLAN.md` S4: "`verify_generator_sync.py` drift = 1" | `docs/design/SHIELD_AND_NORMALISATION_PLAN.md` line 193 |   |   |
| 2 | **W2 `^LightFlameWeapon` 3-way split — status/owner** | `ROADMAP.md`: "**W2 ⬜ ready, owner Devin**" | `docs/design/ROADMAP.md` line 31 | `grep` for `Inherits.*^LightFlameWeapon` in `mods/cameo` returns **28** matches. | Three-way status split; the live tree shows the work is not finished. |
|   |   | `BALANCE_PROGRAM_PLAN.md` board: "W2 **ABANDONED** ... set B is FREE" | `docs/design/BALANCE_PROGRAM_PLAN.md` line 77 |   |   |
|   |   | `BALANCE_PROGRAM_PLAN.md` W2 section: "**🔵 IN PROGRESS (Devin, 2026-08-11) · owner Devin**" | `docs/design/BALANCE_PROGRAM_PLAN.md` line 496 |   |   |
|   |   | `BALANCE_PROGRAM_PLAN.md` W2 section: "`^LightFlameWeapon` has zero remaining inheritors, then is deleted (38 matches remain ...)" | `docs/design/BALANCE_PROGRAM_PLAN.md` line 530 |   | Section already knew 38 matches; live has 28, so progress is not zero. |
| 3 | **W4 weapon-class K retirement — status** | `BALANCE_PROGRAM_PLAN.md` board: "**W4 ✅ DONE**" | `docs/design/BALANCE_PROGRAM_PLAN.md` line 79 | W4 section body lists all DONE checkboxes. | Internal contradiction in the same file. |
|   |   | `BALANCE_PROGRAM_PLAN.md` W4 section: "**W4 ⬜ READY**" | `docs/design/BALANCE_PROGRAM_PLAN.md` line 587 |   |   |
| 4 | **W20 multi-armor combination rule — status** | `BALANCE_PROGRAM_PLAN.md` board: "W20 **⬜ MECHANISM DONE, rule = maintainer**" | `docs/design/BALANCE_PROGRAM_PLAN.md` line 95 | `OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs` has `MultiArmorCombination = Average` per W20 section. | Board says rule is not settled; section says it is live. |
|   |   | `BALANCE_PROGRAM_PLAN.md` W20 section: "**W20 ✅ DONE (`Average` is live)**" | `docs/design/BALANCE_PROGRAM_PLAN.md` line 1650 |   |   |
| 5 | **Template library size and naming** | `WEAPON_3WAY_SPLIT.md`: "the 55-template library" and proposes `^Proj*` / `^Fx*` | `docs/design/WEAPON_3WAY_SPLIT.md` line 34; lines 46-67 (projectile); lines 72-92 (effect) | `mods/cameo/weapons/weapons.yaml`: <br>• 99 `^Warhead_*` (96 above the `DO NOT INHERIT` divider + 3 `^Warhead_Inferno_*` below) <br>• 30 `^Projectile_*` <br>• 47 `^Effect_*` | The live naming is `^Projectile_*` / `^Effect_*`, not the proposed `^Proj*` / `^Fx*`. |
|   |   | `AI_HANDOFF_2026-08-05.md`: "55 warhead, 24 projectile, 27 effect families" | `docs/history/handoffs/AI_HANDOFF_2026-08-05.md` line 11 |   |   |
|   |   | `Cameo_Knowledge_Base_Manual.md` v0.5: "55 weapon-class, 24 projectile, 27 effect templates" | `docs/Cameo_Knowledge_Base_Manual.md` lines 17-18 |   |   |
|   |   | `BALANCE_PIPELINE_ESTIMATE.md`: "55 warhead, 25 projectile, 45 effect families above the divider" | `docs/design/BALANCE_PIPELINE_ESTIMATE.md` lines 44-45 |   |   |
| 6 | **W24 one-main-weapon scope / multi-main counts** | `BALANCE_PROGRAM_PLAN.md` W24/W25 section: "Only **39%** of weapons comply (805 of 2053); 61% carry 2 or more" | `docs/design/BALANCE_PROGRAM_PLAN.md` lines 2213-2214 | `python scratchpad/count_mains.py`: <br>• 1,622 fired weapons <br>• 558 one-main <br>• 939 multi-main <br>• compliance = 34.4% | Denominator and metric undefined; live count differs from both 39%/805 and the `audit_doc_claims` 975 figure. |
|   |   | `BALANCE_MEGAPLAN.md`: "~350+ mixed weapons in ~250 groups remain" | `docs/design/BALANCE_MEGAPLAN.md` line 72 | `python tools/audit/audit_unconverted_templates.py`: <br>• 45 unconverted templates <br>• 1,196 direct inheritors <br>• 574 concrete weapons on ≥1 old template |   |
|   |   | `AI_HANDOFF_2026-08-05.md`: "~609 mixed weapons" and "396 concrete weapons still inherit at least one old full-stack family" | `docs/history/handoffs/AI_HANDOFF_2026-08-05.md` lines 12, 292 |   |   |
|   |   | `BALANCE_PROGRAM_PLAN.md` board W24: "61% of weapons carry 2+" and long cluster list | `docs/design/BALANCE_PROGRAM_PLAN.md` line 99 | `python tools/audit/audit_doc_claims.py`: `multi_main_fired_weapons` documented 975, **measured 939** |   |
| 7 | **Armor/plating rule: average vs. layer selection** | `DESIGN.md` §12.0e law 1: "**LAYER SELECTION, not combination.** A plating REPLACES the class armor while active" | `docs/DESIGN.md` line 951 | `AreaDamageWarhead.MultiArmorCombination: Average` is live. | The design law is for platings; `PSEUDO_ARMOR` and `WEAPON_TYPE_SYSTEM` discuss class/dual armors averaging. The docs are not cross-linked clearly enough, so a reader can treat A1 as applying to platings. |
|   |   | `PSEUDO_ARMOR_AND_INTEGRITY.md` §A1: "**Multiple armor types AVERAGE** (they do not multiply)" | `docs/design/PSEUDO_ARMOR_AND_INTEGRITY.md` lines 43-47 |   |   |
|   |   | `WEAPON_TYPE_SYSTEM.md` §10b: "Two armors now **AVERAGE** (`AreaDamageWarhead.MultiArmorCombination: Average`)" | `docs/design/WEAPON_TYPE_SYSTEM.md` line 231 |   |   |
|   |   | `PSEUDO_ARMOR_AND_INTEGRITY.md` note: "§A1–A4 describe the AVERAGING world, which still governs class armors but NO LONGER governs platings — §F replaced that with selection" | `docs/design/PSEUDO_ARMOR_AND_INTEGRITY.md` lines 21-24 |   | Self-disclaimer exists but is easy to miss. |
| 8 | **Warhead `@1Dam` is retired vs. still live** | `DESIGN.md` §870: "The legacy generic `Warhead@1Dam` is **RETIRED** ... a bare `1Dam` ... is a bug" | `docs/DESIGN.md` lines 1314-1316 | `grep -c "Warhead@1Dam" mods/cameo` = **1,434** raw occurrences; `python scratchpad/count_1dam.py` = **95 fired weapons** still with `Warhead@1Dam`. | `AI_HANDOFF` says 297; live is 95. Either way, the pattern is not retired. |
|   |   | `AI_HANDOFF_2026-08-05.md` W4.5: "`297` live weapons still use the deprecated `Warhead@1Dam` pattern" | `docs/history/handoffs/AI_HANDOFF_2026-08-05.md` lines 364-366 |   |   |
| 9 | **Shield = top + floor — retired but still written** | `DESIGN.md`: "`Shield = 100+floor`" (in the Versus construction note) and later "`Shield = top + floor` is **RETIRED**" | `docs/DESIGN.md` line 856, line 867 | `audit_doc_claims.py` explicitly lists this as a surviving old statement. | The old formula is retired but still appears in the same or related docs. |
|   |   | `ARMOR_SYSTEM.md`: "`Shield = top + floor` is **RETIRED**" but table still uses `Shield % (= top + floor)` | `docs/design/ARMOR_SYSTEM.md` line 43; lines 66-71 |   |   |
| 10 | **Balance authority / source of truth** | `BALANCE_PROGRAM_PLAN.md`: "single source of truth for balance status and ownership" | `docs/design/BALANCE_PROGRAM_PLAN.md` board (lines 72-103) and §0 | Multiple files claim overlapping authority. | A new reader cannot tell which doc to trust for status vs. sequencing. |
|   |   | `BALANCE_MEGAPLAN.md`: "THIS is the authoritative **phase-sequence map**" | `docs/design/BALANCE_MEGAPLAN.md` lines 7-10 |   |   |
|   |   | `ROADMAP.md`: "The balance program's board, ownership and acceptance criteria live in ONE file: `BALANCE_PROGRAM_PLAN.md`" | `docs/design/ROADMAP.md` lines 25-29 |   |   |
|   |   | `AREADAMAGE_HANDOFF.md`: "for **remaining** work and current status read `BALANCE_MEGAPLAN.md` §1 + `ROADMAP.md`" | `docs/history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md` lines 7-8 |   | Does not point to `BALANCE_PROGRAM_PLAN.md`, which ROADMAP says owns status. |

---

## 3. Stale / Out-of-Date Claims (verified against live tree)

| Claim | Document / Source | Live Evidence | Status |
|---|---|---|---|
| `multi_main_fired_weapons` = 975 | `docs/audit/doc_claims.yaml` claim + `docs/design/BALANCE_PROGRAM_PLAN.md` W24 | `audit_doc_claims.py` **measured 939**; `count_mains.py` = 939 multi-main | Stale |
| `meters_filling_before_death` = 118 | `docs/audit/doc_claims.yaml` claim + `docs/design/PHYSICAL_STATE_SYSTEM.md` | `audit_doc_claims.py` **measured 122** | Stale |
| `corrosion_meter_actors` = 783 | `docs/audit/doc_claims.yaml` claim + `docs/design/PHYSICAL_STATE_SYSTEM.md` | `audit_doc_claims.py` **measured 785** | Stale |
| `w24_multi_main_fed` = 386 | `docs/audit/doc_claims.yaml` claim + weapon/physical-state docs | `audit_doc_claims.py` **measured 385** | Stale |
| `physical_state_fired_weapons` = 449 | `docs/audit/doc_claims.yaml` claim + `PSEUDO_ARMOR_AND_INTEGRITY.md` | `audit_doc_claims.py` **measured 450** | Stale |
| W24 one-main compliance 39% (805/2053) | `docs/design/BALANCE_PROGRAM_PLAN.md` lines 2213-2214 | `count_mains.py` = 34.4% one-main (558/1622); `audit_doc_claims` multi-main = 939 | Stale and metric-ambiguous |
| Generator drift = 0 or 1 | Multiple docs (see table above) | `verify_generator_sync.py` = **drift 10** + 1 ungenerated | Stale/False |
| 55/24/27 or 55/25/45 template-library counts | `WEAPON_3WAY_SPLIT.md`, `AI_HANDOFF_2026-08-05.md`, `Cameo_Knowledge_Base_Manual.md`, `BALANCE_PIPELINE_ESTIMATE.md` | `weapons.yaml` = **99 warhead (96 above + 3 below divider), 30 projectile, 47 effect** | Stale |
| `^LightFlameWeapon` 0 inheritors / W2 done | `BALANCE_PROGRAM_PLAN.md` W2 verify (line 536) and done-when (line 530) | `grep` = **28** `^LightFlameWeapon` inheritors | Not done |
| 47 legacy templates remain | `BALANCE_PROGRAM_PLAN.md` board W23 (line 98) | `audit_unconverted_templates.py` = **45** unconverted templates | Stale |
| 297 `Warhead@1Dam` live weapons | `AI_HANDOFF_2026-08-05.md` line 366 | `count_1dam.py` = **95** fired weapons; 1,434 raw `Warhead@1Dam` matches | Stale |
| 88 templates to regenerate (S4) | `docs/design/SHIELD_AND_NORMALISATION_PLAN.md` line 193 | `weapons.yaml` has **99** `^Warhead_*` definitions | Stale |
| 32 raw ledgers / 32 sidecars | `BALANCE_PROGRAM_PLAN.md` W3 line 559, `AI_HANDOFF_2026-08-05.md` line 291 | `docs/balance/*.json` = 33; `docs/balance/derived/*.json` = 33 | Partly stale |

### Live counts captured for reference

- `git log --oneline -10` head: `06542215b D2K: 3-way split DevBullet and PlasBullet.`
- `find_empty_warhead.py`: live files 38, nodes 2,708, concrete weapons scanned, **0** empty-type warheads.
- `audit_warhead_split.py`: broadcast fingerprint **952** vs baseline **952**, friendly-fire louder than shot **0**.
- `audit_unconverted_templates.py`: **45** unconverted templates, **1,196** direct inheritors, **574** concrete weapons still on ≥1 old template.
- `verify_generator_sync.py`: **10** drifts, **1** ungenerated `^Warhead_Sniper_Light`, exit code 1.
- `mods/cameo/weapons/weapons.yaml`: **99** `^Warhead_*` (96 above the `DO NOT INHERIT` divider), **30** `^Projectile_*`, **47** `^Effect_*`.
- `Warhead@1Dam`: **1,434** raw occurrences in `mods/cameo`; **95** fired weapons still use it.

---

## 4. Missing / Incomplete Cross-References

| Missing / Incomplete | Where Found | Issue |
|---|---|---|
| `SPREAD_FALLOFF_PLAN.md` | `CLAUDE.md` mentions it for weapon work; the user-prescribed read order did not include it; `BALANCE_MEGAPLAN.md` lists it as a companion but `AI_HANDOFF_2026-08-05.md` does not | Weapon-work reading lists are inconsistent. |
| Balance doc authority index | `BALANCE_PIPELINE.md`, `BALANCE_PIPELINE_ESTIMATE.md`, `BALANCE_PROGRAM_PLAN.md`, `BALANCE_MEGAPLAN.md`, `MEGAPLAN.md`, `ROADMAP.md` | No single index explains the difference between: machinery (`BALANCE_PIPELINE.md`), effort estimate (`BALANCE_PIPELINE_ESTIMATE.md`), live status board (`BALANCE_PROGRAM_PLAN.md`), and phase-sequence map (`BALANCE_MEGAPLAN.md`). `BALANCE_PIPELINE_ESTIMATE.md` does not point to the newer `BALANCE_PROGRAM_PLAN.md` or `BALANCE_MEGAPLAN.md`. |
| Status pointer from `AREADAMAGE_HANDOFF.md` | `docs/history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md` lines 7-8 | Directs readers to `BALANCE_MEGAPLAN.md` §1 + `ROADMAP.md` for current status, but `ROADMAP.md` says status lives in `BALANCE_PROGRAM_PLAN.md`. |
| `AI_HANDOFF_2026-08-05.md` companion list | `docs/history/handoffs/AI_HANDOFF_2026-08-05.md` line 3 | Lists `BALANCE_PIPELINE.md`, `AREADAMAGE_HANDOFF.md`, `WEAPON_3WAY_SPLIT.md`, `ROADMAP.md`, `AGENT_WORKSPACE.md`; omits `BALANCE_PROGRAM_PLAN.md` and `BALANCE_MEGAPLAN.md`. Its counts (55/24/27, ~609, 297) are not explicitly framed as a 2026-08-05 snapshot. |
| `Cameo_Knowledge_Base_Manual.md` freshness | `docs/Cameo_Knowledge_Base_Manual.md` lines 15-20 | v0.5 is dated 2026-08-02; counts and engine pin are stale. No prominent link to current `audit_doc_claims`/`BALANCE_PROGRAM_PLAN` status. |
| `WEAPON_3WAY_SPLIT.md` naming | `docs/design/WEAPON_3WAY_SPLIT.md` lines 46-67 and 72-92 | Proposes `^Proj*` and `^Fx*`; the shipped tree uses `^Projectile_*` and `^Effect_*`. No "superseded by actual naming" note. |
| `docs/audit/SUMMARY.md` current evidence | `docs/audit/SUMMARY.md` lines 3-4, 11 | Headline links to `FINDINGS.md` and `baseline/`; current generated outputs are in `latest/`. The stale-count warning is present but not prominent. |
| `PSEUDO_ARMOR_AND_INTEGRITY.md` §A1 historical caveat | `docs/design/PSEUDO_ARMOR_AND_INTEGRITY.md` lines 21-24, 43-47 | The averaging claim in §A1 is only disclaimed after the section. It does not link directly to `DESIGN.md` §12.0e or its own §F. |
| `MASTER_REPORT.md` classification | `CLAUDE.md`, `README.md` | Called historical/reference, but still cited for bug taxonomy. A top-of-file "do not use as live roadmap" banner would prevent mis-use. |

---

## 5. Prioritized Top-Five Documentation Edits

1. **Reconcile `BALANCE_PROGRAM_PLAN.md` status contradictions** — Fix W2 (board vs. section/ROADMAP), W4 (✅ DONE vs. ⬜ READY heading), W20 (mechanism-done vs. ✅ DONE), and W24 (39% / 805 of 2053). This is the highest priority because the file is explicitly the single source of truth for balance status and ownership.

2. **Update generator-drift claims everywhere** — Add a historical/stale note to `AREADAMAGE_HANDOFF.md`, `BALANCE_MEGAPLAN.md` A1, `BALANCE_PIPELINE_ESTIMATE.md` §1, `PHYSICAL_STATE_SYSTEM.md` guardrails, `SHIELD_AND_NORMALISATION_PLAN.md` S4, and `ROADMAP.md` to reflect live `verify_generator_sync.py` output (10 drifts + `^Warhead_Sniper_Light` ungenerated). This prevents an agent from believing a regenerate is a no-op.

3. **Refresh template-library counts and naming** — Update `WEAPON_3WAY_SPLIT.md`, `AI_HANDOFF_2026-08-05.md`, `Cameo_Knowledge_Base_Manual.md`, and `BALANCE_PIPELINE_ESTIMATE.md` to live `weapons.yaml` counts (99 warheads — 96 above the divider, 30 projectiles, 47 effects) and the actual `^Projectile_*` / `^Effect_*` naming.

4. **Define and update the W24 / `Warhead@1Dam` metrics** — Replace `BALANCE_PROGRAM_PLAN.md` 805/2053 and `AI_HANDOFF_2026-08-05.md` 297 with live, labeled numbers (fired-weapon vs. all-weapon counts; raw vs. fired `Warhead@1Dam`). Point to `count_mains.py`/`count_1dam.py` or `audit_doc_claims` for re-measurement.

5. **Clarify the armor/plating rule cross-links** — Add a prominent cross-reference block: `DESIGN.md` §12.0e (plating layer selection), `PSEUDO_ARMOR_AND_INTEGRITY.md` §F (selection), and `WEAPON_TYPE_SYSTEM.md` §10b (dual class-armor averaging). Flag `PSEUDO_ARMOR` §A1–A4 as historical/averaging-world reasoning, not current for platings.

---

## 6. Significant Conflicts Found

**Yes — significant conflicts were found.**  The most important are:

- Generator-sync drift is reported as `0` or `1` in multiple documents while the live tool reports `10`.
- `BALANCE_PROGRAM_PLAN.md` contradicts itself on W2, W4, and W20 status.
- W24 / multi-main / old-template migration numbers use different, unstated metrics and disagree with the live tree.
- `Warhead@1Dam` is described as retired while it remains in 95 fired weapons.
- The authority over balance status is fragmented across `BALANCE_PROGRAM_PLAN.md`, `BALANCE_MEGAPLAN.md`, `ROADMAP.md`, and the historical `AREADAMAGE_HANDOFF.md`.

The `audit_doc_claims` registry and `verify_generator_sync` guard are already catching the drift; the documentation now needs to be brought in line with those tools.
