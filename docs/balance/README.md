# docs/balance — the balance ledger

Generated per-faction RAW-STAT mirrors of the live rules
(BALANCE_PIPELINE.md — read it before touching anything here).

- One JSON per faction pack (`<theme>_<faction>.json`) plus
  `shared_<theme>.json` for theme-shared actors. Sections mirror the
  pack's closed yaml file set.
- Values are RAW — exactly as the resolved rules state them (wdist
  stays wdist, no DPS, warheads listed one-by-one). Derived quantities
  exist only in the generated workbook's formula cells.
- Every value carries provenance: `file#Trait.Field`, or `inherited`
  when a template supplies it.
- `self_heal_step` is the canonical `ChangesHealth@SelfHealing.Step` value,
  falling back to a bare `ChangesHealth.Step` for actors without a named
  base-heal instance. If both instances exist, `self_heal_step_other` preserves
  the bare layer; other named instances are ability/condition effects and stay
  outside the base-heal pair. `repairable_hp_per_step` records
  `Repairable.HpPerStep`, and `turn_speed_air` records `Aircraft.TurnSpeed`.
- `design.*` fields (unit_class / special / tech_tier / class_anchor)
  are design judgments, not yaml facts — they are seeded from the
  legacy workbook in Phase 3 and live here afterwards.
- Regenerate: `python tools/balance/extract_stats.py`
- Drift check: `python tools/balance/extract_stats.py --check`
  (exit 1 = yaml and ledger disagree; joins run_all in Phase 6).

LAW: never hand-edit yaml balance numbers. The sanctioned loop is
ledger/workbook -> `balance push` (Phase 4) -> yaml. Hand edits are
caught by the drift check and reverted or ratified explicitly.

Not yet covered (extend in later phases): Outpost2 (unpacked monolith
faction), neutral/tech structures from core rules, weapon-class
template Versus tables (mirrored read-only in Phase 2).
