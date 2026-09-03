#!/usr/bin/env python3
"""audit_damage_grid.py — enforce the universal 2000/1% damage rule.

⛔ **STALE — QUARANTINED, deliberately NOT in run_all.sh.**
This script still encodes the RETIRED 2000-step damage grid and the retired
`main // 2000` percentage twin. Both were replaced by W15/W17:

    live grid : tools/balance/formula.py -> DAMAGE_STEP = 100
    live twin : tools/balance/formula.py -> percentage_twin()

Run as-is it reports ~300 "off-grid" weapons that are perfectly legal under the
current law. Re-derive it from `formula` (import DAMAGE_STEP and
percentage_twin instead of the literals below), then wire it into run_all.sh.
Until then treat its output as historical. See docs/HANDOFF.md.

Rule (DESIGN.md §12):
- Main SpreadDamage/AreaDamage warheads must all carry the SAME value.
- That value must sit on the 2000-step grid (Damage % 2000 == 0).
- The HealthPercentageDamage twin (*Percentage) must equal
  main_damage // 2000 (1 per 2000).
- SpreadDamage/AreaDamage twins (*FriendlyFire, *ExtraDamage) must equal
  main_damage // 2 (50 % twins).

Templates (^ prefix) are skipped because they are baselines, not concrete
weapons.
"""
from __future__ import annotations

import sys

from cameo_model import Model
from report import h1, h2, table


def _int(v) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def classify_warheads(resolved):
    """Return (mains, percentage, friendly, extra) lists of (tag, node)."""
    mains, pct, ff, extra = [], [], [], []
    for c in resolved.children:
        if not c.key.startswith("Warhead@"):
            continue
        tag = c.key.split("@", 1)[1]
        low = tag.lower()
        if c.value == "HealthPercentageDamage":
            pct.append((tag, c))
        elif c.value in ("SpreadDamage", "AreaDamage"):
            if low.endswith("friendlyfire"):
                ff.append((tag, c))
            elif low.endswith("extradamage"):
                extra.append((tag, c))
            else:
                mains.append((tag, c))
    return mains, pct, ff, extra


def main() -> int:
    m = Model()
    rs = m.rs

    grid_rows = []
    eq_rows = []
    pct_rows = []
    twin_rows = []

    for wname in sorted(rs.weapons):
        if wname.startswith("^"):
            continue
        resolved = rs.resolve_weapon(wname)
        if resolved is None:
            continue
        mains, pct, ff, extra = classify_warheads(resolved)
        if not mains:
            continue

        main_dmgs = [_int(c.get("Damage")) for _, c in mains]
        if all(d == 0 for d in main_dmgs):
            continue

        for tag, c in mains:
            d = _int(c.get("Damage"))
            if d > 0 and d % 2000 != 0:
                grid_rows.append([wname, tag, str(d)])

        non_zero = [d for d in main_dmgs if d > 0]
        if non_zero and len(set(non_zero)) > 1:
            eq_rows.append([wname, ", ".join(str(d) for d in main_dmgs)])

        # Use the largest main as the canonical D for twin checks.
        # When all mains are equal, this is the common D.
        D = max(main_dmgs) if main_dmgs else 0

        for tag, c in pct:
            actual = _int(c.get("Damage"))
            expected = D // 2000
            if D > 0 and actual != expected:
                pct_rows.append([wname, tag, str(actual), str(expected)])

        for tag, c in ff + extra:
            actual = _int(c.get("Damage"))
            expected = D // 2
            if D > 0 and actual != expected:
                twin_rows.append([wname, tag, str(actual), str(expected)])

    out = [h1("Damage-grid audit (2000-step / 1% rule)")]
    failed = bool(grid_rows or eq_rows or pct_rows or twin_rows)

    out.append(h2(f"Off-grid main damage ({len(grid_rows)})"))
    if grid_rows:
        out.append("Main SpreadDamage/AreaDamage warheads must be on the "
                   "2000-step grid.\n")
        out.append(table(["weapon", "warhead", "damage"], grid_rows))
    else:
        out.append("None.\n")

    out.append(h2(f"Unequal main damage ({len(eq_rows)})"))
    if eq_rows:
        out.append("All main SpreadDamage/AreaDamage warheads of a weapon "
                   "must carry the identical flat value.\n")
        out.append(table(["weapon", "main damages"], eq_rows))
    else:
        out.append("None.\n")

    out.append(h2(f"Wrong percentage twin ({len(pct_rows)})"))
    if pct_rows:
        out.append("*Percentage warheads must equal main_damage // 2000 "
                   "(1 per 2000).\n")
        out.append(table(["weapon", "warhead", "actual", "expected"],
                         pct_rows))
    else:
        out.append("None.\n")

    out.append(h2(f"Wrong 50% twin ({len(twin_rows)})"))
    if twin_rows:
        out.append("*FriendlyFire / *ExtraDamage warheads must equal "
                   "main_damage // 2.\n")
        out.append(table(["weapon", "warhead", "actual", "expected"],
                         twin_rows))
    else:
        out.append("None.\n")

    sys.stdout.write("\n".join(out) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
