---
name: run-audits
description: "Run the Cameo audit suite and report results"
triggers:
  - user
  - model
---

# Run-Audits — execute the Cameo audit suite

This skill runs the project's audit tooling and reports findings.

## Quick audit (targeted checks)

For a fast check after weapon conversions, run these individually:

```powershell
# Empty warhead audit (NRE crash detector) -- must be 0
python tools/audit/find_empty_warhead.py

# Orphaned old warhead keys (double-fire bug) -- must be 0 real
python tools/audit/find_orphan_old_keys.py

# AreaDamage type sweep (SpreadDamage regression) -- should be 0 candidates
python tools/balance/sweep_areadamage.py

# Multi-variant orphan check
python tools/audit/find_orphan_old_keys_multi.py

# Generator sync verification (⛔ drift is 10 as of 2026-08-23, not 1 — only
#  ^Warhead_Sniper_Light is accepted; the nine ^Warhead_Chem* entries are real
#  disagreements left by the W24 chemical split. See docs/HANDOFF.md §3.4.)
python tools/balance/verify_generator_sync.py
```

## Full audit suite

The canonical way to regenerate ALL audit reports:

```bash
bash tools/audit/run_all.sh
```

**IMPORTANT:** Use `bash`, NOT PowerShell for this. PowerShell's `>` redirect
writes UTF-16, which corrupts the audit report files. The bash script handles
encoding correctly.

`tools/audit/run_all.py` is a Python port for shells without `sh`; it reads its audit
list out of `run_all.sh`, so the two cannot drift apart. Either is fine — a PowerShell
`>` redirect is not.

Individual audit scripts can be run with `python tools/audit/audit_<name>.py`:
- `audit_empty_warheads.py` -- empty warhead type NRE detector
- `audit_balance_drift.py` -- yaml vs ledger disagreements
- `audit_multiplier_modifiers.py` -- non-integer Modifier values
- `audit_orphans.py` -- dangling weapon references
- `audit_inherits.py` -- dangling inherit targets
- `audit_weapon_uniqueness.py` -- duplicate weapons per faction
- `audit_nuclear_flash_bindings.py` -- directional flash warhead protection
  (needs `engine/glsl/`; it fails in a checkout without a built engine)
- `audit_duplicate_inherits.py` -- the `Parent type X was already inherited` crash class
- `audit_doc_claims.py` -- every pinned numeric claim vs the tree

## Interpreting results

- **0 empty warheads** = safe to commit (no NRE crash risk)
- **0 orphaned old keys** = no double-fire bugs from conversions
- **0 AreaDamage sweep candidates** = no SpreadDamage regressions
- **Generator sync drift** — `^Warhead_Sniper_Light` is the one ACCEPTED entry. Anything
  else is a real disagreement between `gen_weapon_template.py` and `weapons.yaml`. It is
  **10** today (nine live `^Warhead_Chem*` entries); do not read that as passing.
- **Balance drift = 0** = yaml matches committed ledgers

## Ledger refresh

After any weapon conversion, refresh the balance ledgers:

```powershell
python tools/balance/extract_stats.py
```

**Commit the ledgers WITH the yaml, in the same commit.** `audit_balance_drift` has gone red
twice because a weapon commit landed without a re-extract — and the second time nobody noticed
until a documentation pass ran the suite.

This updates all `docs/balance/*.json` files. The ledger diff in git shows
what changed structurally (new warhead keys, renamed keys, etc.).

## Phase B survey

To see remaining unconverted weapons:

```powershell
python tools/audit/phase_b_survey.py
```

Output goes to `docs/audit/latest/phase_b_survey.md`.
