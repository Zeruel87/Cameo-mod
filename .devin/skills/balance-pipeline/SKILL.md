---
name: balance-pipeline
description: "Run the Cameo balance pipeline: extract, propose, apply stats"
triggers:
  - user
  - model
---

# Balance-Pipeline — the sanctioned balance workflow

**HARD RULE: Never hand-edit a balance number in yaml.** All balance changes
go through this pipeline. `--confirm` requires an explicit maintainer order.

## The pipeline steps

### 1. Extract current stats into ledgers

```powershell
python tools/balance/extract_stats.py
```

This refreshes all `docs/balance/*.json` ledger files with current stats
from the resolved ruleset. Each ledger contains raw stats + provenance
for every actor in a faction.

### 2. (Optional) Generate the workbench spreadsheet

```powershell
python tools/balance/build_workbook.py
```

Produces `docs/design/cameo_balance_v2.xlsx` (gitignored). Edit the
unlocked input cells, then read changes back:

```powershell
python tools/balance/import_workbook.py
```

**LEGACY workbook:** `docs/design/cameo_armor_system.xlsx` remains the
reference for design judgments. If `~$cameo_armor_system.xlsx` exists,
Excel has the file open -- do NOT write to it; queue and say so.

### 3. Apply balance changes (dry-run first!)

```powershell
# Dry run (shows what would change, makes no edits)
python tools/balance/apply_balance.py --faction X

# Apply for real (REQUIRES MAINTAINER ORDER)
python tools/balance/apply_balance.py --faction X --confirm
```

**`--confirm` needs a maintainer order.** Do not run it without explicit
permission from the maintainer.

### 4. Verify and commit

```powershell
# Re-extract to verify round-trip
python tools/balance/extract_stats.py

# Run audits
python tools/audit/audit_balance_drift.py
python tools/audit/audit_multiplier_modifiers.py

# Boot-gate (invoke the boot-gate skill)

# Commit yaml AND ledger TOGETHER
git add <changed_yaml_files> docs/balance/<faction>.json
```

## Key rules

- **SUM LAW:** effective per-shot damage = SUM of all offensive warheads
  (never max). `spread_damage_sum()` skips `*ExtraDamage`, `*Percentage`,
  and `*FriendlyFire`.
- **Damage grid:** main `Damage` sits on `formula.DAMAGE_STEP` = **100**
  (W15, 2026-08-15 — it was 2000 before that). The `%`-twin comes from
  `formula.percentage_twin()`, never from `damage // 2000`.
- **`FirepowerMultiplier` is RETIRED** (W17): `apply_balance` cannot write it,
  and the proposer always solves at `fp = 1.0`. Do not add new ones; when you
  restat an actor that has one, DELETE it — the prescribed `Damage` is already
  solved at `fp = 1`, so a surviving trait scales it a second time.
- **Range:** always a multiple of 10.
- **Speed:** infantry use steps of 1; vehicles/aircraft/ships use steps of 5.
- **Uniqueness:** 5 stats must be unique within a class: HP, Speed,
  Σ(offensive warhead `Damage`) × FirepowerMultiplier, ReloadDelay (RAW, not
  burst-adjusted), Range. ⚠ That third one is NOT the ledger's
  `effective_damage` column — see `docs/design/EFFECTIVE_DAMAGE.md` §1.
- **Dual-weapon units:** balance each weapon independently, sharing HP/Speed
  but with independent Range/Damage/ReloadDelay. FirepowerMultiplier is
  shared (affects both weapons).

## What the pipeline does NOT do

- It does not create new weapons or templates
- It does not change Versus profiles (those live in `^Warhead_*` templates)
- It does not change Burst/BurstDelays (need explicit permission)
- It does not handle the weapon 3-way split (use the cluster-convert skill)
