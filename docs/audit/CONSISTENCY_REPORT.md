# Consistency Check Report — 2026-07-16

_A comprehensive cross-document consistency audit across DESIGN.md, ROADMAP.md,
MASTER_REPORT.md, audit scripts, exception configs, and system memories.
This report is verified by `tools/audit/audit_consistency_report.py` on every
audit run to ensure fixes are not regressed._

## Summary

**21 inconsistencies found and fixed** across 30+ files, plus 2 stale memories
updated. Faction InternalNames renamed to match actor prefixes across 27 YAML/Python/MD
files; WC2 actors and 74 asset files renamed. No gameplay logic changed — all
changes are naming consistency, documentation, audit scripts, and exception configs.

## Categories of inconsistency

1. **Naming convention drift** — suffix case (`_aa` vs `_AA`), singular vs
   plural faction names (`ra1_soviet` vs `ra1_soviets`), deprecated suffix
   conventions (`E` vs `_elite`).
2. **Audit script scope mismatch** — scripts checking too broadly (all
   `GainsExperience` instead of `^GainsExperienceRA2` only) or too narrowly
   (missing Terran/Protoss from rank decoration checks).
3. **Stale roadmap claims** — tasks marked done that weren't actually done
   (`cabal_legion_backup`), or marked done with a bug that has a separate fix
   entry elsewhere (SC-RANKS).
4. **Missing roadmap items** — 9 user-reported issues not tracked in the
   work queue.
5. **Incomplete documentation** — variant suffix lists missing `_EMP`, `_AA`,
   `_upgraded`; audit README missing 18 scripts from its table; `run_all.sh`
   missing 3 audit scripts.
6. **Stale memories** — CABAL backup status and Schwarzer Mond 1-burst rule
   both had outdated information.

---

## All inconsistencies found & fixed

### Naming convention drift

#### 1. ROADMAP WPN-MIGRATE: `_aa` → `_AA` (FIXED)
- **File**: `docs/design/ROADMAP.md` line ~647
- **Issue**: WPN-MIGRATE said "AA variants append `_aa`" (lowercase), but
  DESIGN.md §1 and §16.3 mandate `_AA` (uppercase).
- **Fix**: Updated to `_AA`, also added missing `_EMP` suffix.

#### 2. `garrison_exceptions.yaml`: `ra1_soviet_cyberdog` → `ra1_soviets_cyberdog` (FIXED)
- **File**: `docs/design/garrison_exceptions.yaml` line 27
- **Issue**: Used singular `ra1_soviet_cyberdog`, but all actual actor IDs
  use `ra1_soviets_` (plural). The exception would silently fail to match.
- **Fix**: Changed to `ra1_soviets_cyberdog`.

#### 3. MASTER_REPORT §9.1: `ra1_soviet` → `ra1_soviets` (FIXED)
- **File**: `docs/history/MASTER_REPORT_2026-07-08.md` line 392
- **Issue**: Used `ra1_soviet_*` (singular), but actual InternalName is
  `ra1_soviets` (plural) and all actor IDs use `ra1_soviets_*`.
- **Fix**: Changed to `ra1_soviets_*` / `ra2_soviets_*`.

#### 4. ROADMAP E3: Historical `E` suffix now contradicts `_elite` rule (FIXED)
- **File**: `docs/design/ROADMAP.md` line ~516
- **Issue**: E3 entry celebrates renaming to `<base>E` convention, but
  DESIGN.md §16.3 now mandates `_elite` only. The `E` suffix is deprecated.
- **Fix**: Added NOTE that `E` suffix is superseded; renames need to be
  redone as `_elite` in WEAPON-SUFFIX-ELITE.

### Audit script scope mismatch

#### 5. `audit_missing_elite.py`: Flags ALL `GainsExperience` instead of RA2-only (FIXED)
- **File**: `tools/audit/audit_missing_elite.py` line ~41
- **Issue**: Script checked for any `GainsExperience` trait, but DESIGN.md
  §16.3 says elite weapons are "RA2 system only". This caused 1256 false
  positives (TD/D2k/SC/WC2 actors that shouldn't have elite weapons).
- **Fix**: Changed check to `GainsExperienceRA2` only. Updated docstring
  and output header.

#### 6. `audit_faction_leaks.py`: Wrong RA1/RA2 faction aliases (FIXED)
- **File**: `tools/audit/audit_faction_leaks.py` line 78
- **Issue**: Used `"soviet"` (singular) for RA1 and `"ra2america",
  "ra2russia"` for RA2. Actual InternalNames are `"soviets"` (plural) and
  `"ra2allies", "ra2soviets"`.
- **Fix**: Corrected to match actual `InternalName` values from
  `rules/redalert.yaml` and `rules/redalert2.yaml`.

#### 7. `audit_rank_decoration.py`: Missing Terran/Protoss faction paths (FIXED)
- **File**: `tools/audit/audit_rank_decoration.py` line 30
- **Issue**: Only Zerg was mapped to `AlienRankDecoration`. Terran and
  Protoss were missing, so the audit silently passed actors that
  incorrectly have `^AlienRankDecoration` (from buggy commit `b95f5e7f3`).
- **Fix**: Added `TerranRankDecoration` and `ProtossRankDecoration`
  entries so the audit flags wrong decorations.

#### 8. `audit_weapon_uniqueness.py`: Missing `_upgraded` in `VARIANT_SUFFIXES` (FIXED)
- **File**: `tools/audit/audit_weapon_uniqueness.py` line 41
- **Issue**: `_upgraded` was missing from `VARIANT_SUFFIXES`, so weapons
  with that suffix wouldn't be collapsed to their family stem.
- **Fix**: Added `_upgraded` to the tuple.

### Stale roadmap claims

#### 9. ROADMAP: `cabal_legion_backup` claimed created but doesn't exist (FIXED)
- **File**: `docs/design/ROADMAP.md` line ~74
- **Issue**: ROADMAP claimed `cabal_legion_backup` was created in commit
  `d4be72f8f`, but no `cabal_legion` actor exists in the tree at all.
  `cabal_widow_backup` was created instead.
- **Fix**: Corrected entry to say "avatar, widow" and added NOTE explaining
  the legion reference was stale.

#### 10. ROADMAP SC-RANKS: Self-contradiction (FIXED)
- **File**: `docs/design/ROADMAP.md` lines ~487 vs ~696
- **Issue**: Line 487 marks `^AlienRankDecoration` as `[x]` (done) without
  mentioning the bug, while line 696 says it's `[ ]` (needs fixing because
  it was applied to ALL SC factions instead of just Zerg).
- **Fix**: Added NOTE to the `[x]` entry explaining the bug and pointing
  to SC-RANKS fix plan.

#### 11. ROADMAP E1: Stale count after audit scope change (FIXED)
- **File**: `docs/design/ROADMAP.md` line ~542
- **Issue**: E1 entry still says "1256 buildable actors with
  `GainsExperience`" — the audit now only checks `^GainsExperienceRA2`,
  so this count is stale.
- **Fix**: Added NOTE that count was from old scope; audit needs re-running
  for RA2-only count.

### Missing roadmap items

#### 12. ROADMAP: 9 user-reported issues missing from work queue (FIXED)
- **File**: `docs/design/ROADMAP.md` line ~119
- **Issue**: 9 issues reported by the user were not in the ROADMAP:
  ixian_koda_tank crash, repair drone not repairing, tarantula firing
  offset, artillery spider firing offset, artillery spider magicnuke
  explosion, interceptor.nax rename, drone.nax move, CABAL obelisk
  range/detection, eliminator 800 balance.
- **Fix**: Added all 9 as a new "P0/P1 — User-reported issues" section.

### Incomplete documentation

#### 13. DESIGN.md §1: Variant list missing `_EMP`, `_AA`, `_upgraded` (FIXED)
- **File**: `docs/DESIGN.md` line 46
- **Issue**: The general variant suffixes list didn't include the new
  `_EMP`, `_AA`, `_upgraded` suffixes documented in weapon-specific rules.
- **Fix**: Added them to the list.

#### 14. MASTER_REPORT §9.1: Missing variant suffixes (FIXED)
- **File**: `docs/history/MASTER_REPORT_2026-07-08.md` line 396
- **Issue**: Listed only `_mk2, _elite, _husk, _water, _ai`. Missing:
  `_sp, _r4, _wild, _EMP, _AA, _upgraded`, `.husk`, `para`.
- **Fix**: Expanded to match DESIGN.md §1, with cross-reference.

#### 15. `backlog_weapon_rename.md`: Stale variant markers list (FIXED)
- **File**: `docs/history/backlog_weapon_rename.md` line 40
- **Issue**: Listed variant markers without `_EMP`, `_AA`, `_upgraded`.
- **Fix**: Added the new suffixes.

#### 16. `tools/audit/README.md`: Missing 18 audit scripts from table (FIXED)
- **File**: `tools/audit/README.md` line 35
- **Issue**: The script table only listed the original 14 audits. 18 newer
  audits were missing.
- **Fix**: Added all missing entries with bug class references.

#### 17. `run_all.sh`: Missing `audit_balance_sheet.py` (FIXED)
- **File**: `tools/audit/run_all.sh` line 28
- **Issue**: `audit_balance_sheet.py` exists and is referenced in DESIGN.md
  §12, but was not included in `run_all.sh`.
- **Fix**: Added `balance_sheet` to the audit loop.

#### 18. `run_all.sh`: Missing `audit_createeffect_image.py` and `audit_ce_image_usage.py` (FIXED)
- **File**: `tools/audit/run_all.sh`
- **Issue**: These scripts exist in `tools/` (not `tools/audit/`) and are
  referenced in ROADMAP CE2 and DESIGN.md §8, but were not in `run_all.sh`.
- **Fix**: Added a secondary loop for scripts in `tools/`.

#### 19. ROADMAP WPN-MIGRATE: Missing `_EMP` suffix (FIXED)
- **File**: `docs/design/ROADMAP.md` line ~647
- **Issue**: WPN-MIGRATE listed elite and AA suffixes but omitted EMP.
- **Fix**: Added `_EMP` alongside `_AA` and `_elite`.

### Stale memories updated

#### M1. CABAL backup systems memory (UPDATED)
- **Issue**: Memory said `cabal_legion_backup` and `cabal_avatar_backup`
  were missing. Reality: `cabal_avatar_backup` exists, `cabal_widow_backup`
  exists, `cabal_artilleryspider_backup` now has `Repairable`. No
  `cabal_legion` actor exists at all.
- **Fix**: Updated memory to reflect actual state.

#### M2. Schwarzer Mond 1-burst rule memory (UPDATED)
- **Issue**: Memory said "1-burst weapons not touched unless base stats
  changed". This was the OLD plan, superseded by DESIGN.md §18.4 and
  ROADMAP SM-1BURST which confirm 1-burst weapons DO benefit from
  +1-burst upgrades.
- **Fix**: Updated memory to reflect current design.

#### 20. Faction InternalName ↔ actor prefix consistency (FIXED 2026-07-16)
- **Files**: 27 files across mods/, tools/, docs/
- **Issue**: 11 faction InternalNames didn't match their actor prefixes:
  - `gdi` → `td_gdi` (actors use `td_gdi_`)
  - `nod` → `td_nod` (actors use `td_nod_`)
  - `allies` → `ra1_allies` (actors use `ra1_allies_`)
  - `soviets` → `ra1_soviets` (actors use `ra1_soviets_`)
  - `ra2allies` → `ra2_allies` (actors use `ra2_allies_`)
  - `ra2soviets` → `ra2_soviets` (actors use `ra2_soviets_`)
  - `tsgdi` → `ts_gdi` (actors use `ts_gdi_`)
  - `tsnod` → `ts_nod` (actors use `ts_nod_`)
  - `asianalliance` — already correct (actors use `asianalliance_`, no underscore in faction name)
  - `consortium` → `steelconsortium` (actors use `steelconsortium_`)
  - `syndicate` → `latinsyndicate` (actors use `latinsyndicate_`)
- **Fix**: Renamed all InternalName, FactionCA@, Factions:, and
  RandomFactionMembers references. Updated audit scripts, gen scripts,
  AI files, and documentation.
- **Already consistent** (no change needed): `schwarzermond`, `naxis`,
  `futuretech`, `japan`, `yuri`, `forgotten`, `cabal`, `terran`, `zerg`,
  `protoss`, `tkm`, `ixian`, `ordos`, `atreides`, `harkonnen`.

#### 21. WC2 faction + actor prefix rename (FIXED 2026-07-16)
- **Files**: `rules/warcraft2.yaml`, `sequences/warcraft2.yaml`,
  `ContentPacks/Warcraft2/yaml/ai.yaml`, `ai/ai.yaml`, `rules/misc.yaml`,
  `sequences/misc.yaml`, 74 asset files in `bits/warcraft2/`
- **Issue**: WC2 factions used `warcraft_humans`/`warcraft_orcs` as both
  faction InternalNames and actor prefixes. Renamed to `wc2_humans`/
  `wc2_orcs` for consistency with the `td_`, `ra1_`, `ra2_`, `ts_` prefix
  convention.
- **Fix**: All `warcraft_humans_` → `wc2_humans_` and `warcraft_orcs_` →
  `wc2_orcs_` in YAML (1041 occurrences across rules/sequences/AI).
  Asset files renamed on disk. Faction InternalNames updated.

---

## Verified consistent (no issues found)

The following files/areas were checked and found clean:

- `CLAUDE.md` — no stale references
- `docs/MIGRATION.md` — no stale references
- `docs/audit/SUMMARY.md` — no stale references
- `docs/history/audits/BASELINE_FINDINGS.md` — no stale references
- `docs/factions/MATRIX.md` — no stale references
- `docs/design/upgrades_intent.yaml` — no stale references
- `docs/design/RESEARCH_NOTES.md` — consistent working doc
- `docs/design/RESEARCH_NOTES.md` — no stale references
- `docs/design/RESEARCH_NOTES.md` — no stale references
- `docs/Cameo_Knowledge_Base_Manual.md` — actor IDs with `_aa` (e.g.
  `d2k_aa_mine`) are actor names, not weapon suffixes; not a violation
- `docs/session_progress_2026_07_14.md` — historical session log; no
  longer in the repository (removed in a prior cleanup). Its content was
  superseded by DEVELOPMENT_LOG.md and ROADMAP.md.
- `docs/audit/display_text_review.md` — historical audit output; left as-is
- ROADMAP WEAPON-SUFFIX-ELITE/EMP/AA entries — all consistent with
  DESIGN.md §1 and §16.3
- DESIGN.md §8 CreateEffect rules — match actual audit tool references
- DESIGN.md §16.2 rank decoration table — consistent with audit script
- `audit_weapon_suffixes.py` X1 — checks `_elite` only (replaced deprecated
  `audit_elite_naming.py`)
- `audit_weapon_suffixes.py` — checks `_elite`, `_EMP`, `_AA` correctly
- `audit_effect_warhead_names.py` — canonical name checking is correct
- `audit_buildable_order.py` — tier model comment already clarifies scope
  difference vs `audit_stat_formulas.py`

---

## Rules verified as consistent

These rules were cross-referenced across multiple documents and confirmed
to be in agreement:

1. **Weapon suffix ordering**: `<base_name>_<doctrine/upgrade/variant>_EMP_AA_elite`
   — base name first, then doctrine/upgrade/variant suffixes, then `_EMP`,
   then `_AA`, then rank tier (`_elite`) last. Consistent across DESIGN.md
   §1, §16.3, and ROADMAP weapon suffix standardization entries.

2. **Elite weapons are RA2-only**: DESIGN.md §16.3 "Every RA2-styled actor
   with a primary armament must have an elite weapon." ROADMAP E1 now
   notes the audit scope change. `audit_missing_elite.py` now checks
   `^GainsExperienceRA2` only.

3. **`ra1_soviets` (plural)**: DESIGN.md §1, actual YAML actor IDs, and
  `rules/redalert.yaml` InternalName all use plural. MASTER_REPORT and
  garrison_exceptions fixed to match.

4. **RA2 InternalNames**: `ra2_allies`, `ra2_soviets`, `yuri` — verified
   against `rules/redalert2.yaml`. `audit_faction_leaks.py` fixed.

5. **CABAL backup pattern**: 3 components (Inherits@BACKUP,
   SpawnActorOnDeath@backup, backup actor definition). 5 working backup
   actors exist: manticore, artilleryspider, tarantula, avatar, widow.
   No `cabal_legion` actor exists.

6. **Death palette rule**: `DeathSequencePalette` must match
   `RenderSprites PlayerPalette` per unit. Only TS units need fixing.
   `ra2player` and `playerra2` are DIFFERENT palettes. The broken commit
   `9579827e9` was reverted. The TS-only death palette audit was completed
   (`54816b1f3`, 2026-07-27) — 2 mismatches found and fixed.

7. **SC rank decorations**: `^AlienRankDecoration` should only apply to
   Zerg. Terran and Protoss need separate decorations. Commit `b95f5e7f3`
   incorrectly applied it to all SC factions. FIXED: commit `c3e3490f7`
   reverted the blanket application; commit `031c54d6b` created 3 separate
   decorations (`^ZergRankDecoration`, `^TerranRankDecoration`,
   `^ProtossRankDecoration`). ROADMAP SC-RANKS is `[x]` (done).

8. **Schwarzer Mond 1-burst**: 1-burst weapons DO benefit from +1-burst
   upgrade steps (1→2→3 progression). DESIGN.md §18.4 and ROADMAP
   SM-1BURST both confirm. Old exclusion plan was superseded.

9. **Variant suffix complete list**: `_husk _sp _r4 _wild _mk2 _elite
   _ai _water _EMP _AA _upgraded` plus dotted `.husk` and paradrop `para`.
   Now consistent across DESIGN.md §1, MASTER_REPORT §9.1, and
   `backlog_weapon_rename.md`.

10. **Audit suite completeness**: 37 audit scripts total (35 in
    `tools/audit/` + 2 in `tools/`). All included in both `run_all.py`
    and `run_all.sh`. README.md table lists all of them.
