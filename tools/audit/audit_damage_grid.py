#!/usr/bin/env python3
"""audit_damage_grid.py — enforce the universal damage grid and twin ratios.

Re-derived 2026-08-25 from the LIVE law in ``tools/balance/formula.py`` (W15/W17/W18):
the retired 2000-step grid and the retired ``main // 2000`` percentage twin are gone.
Import ``DAMAGE_STEP`` and ``percentage_twin`` rather than ever re-literalising them.

Rule (DESIGN.md §12, formula.distribute_damage):
- Main SpreadDamage/AreaDamage warheads must all carry the SAME value.
- That value must sit on the flat-damage grid (Damage % DAMAGE_STEP == 0; DAMAGE_STEP = 100).
- The percentage twin must equal ``percentage_twin(D, denominator)`` where ``denominator``
  is the node's own unit (read from the resolved ``PercentageDenominator`` field).
- SpreadDamage/AreaDamage twins (*FriendlyFire, *ExtraDamage) must equal D // 2 (50 %).

⚠ THE PERCENTAGE TWIN LANDSCAPE IS MID-TRANSITION — checked narrowly on purpose:
  * Folded weapons (AreaDamageWarhead fold) carry the percentage half as a
    ``PercentageScale`` FIELD on the main warhead, a free per-family dial
    (``basisPoints = Damage * PercentageScale / 200000``) that does NOT obey
    ``percentage_twin``. It is NOT checked here — ``audit_physical_state_warheads``
    guards the flame/chemical families' non-zero scale; other families' scale is a
    design choice, not a grid violation.
  * Separate ``*Percentage`` nodes still exist in TWO conventions:
      - basis-point (``AreaDamagePercentage`` + ``PercentageDenominator: 10000``): the
        W18 convention, Damage = ``percentage_twin(D, 10000)`` = D/100. CHECKED.
      - legacy whole-percent (``HealthPercentageDamage``, or ``AreaDamagePercentage``
        resolving to denominator 100): deliberately left by W18 ("1549 overrides
        deliberately left in whole percent — they resolve to LEGACY hand-written
        templates that never got the denominator"). They do NOT obey
        ``percentage_twin`` and are NOT bugs — SKIPPED, counted for transparency.

Templates (^ prefix) are skipped because they are baselines, not concrete weapons.

⚠ RATCHET, NOT A HARD GATE. The non-zero counts (off-grid, unequal mains, 50 %
twins) are existing LEGACY debt — hand-tuned "nice numbers" (3333, 7777, 11111),
measured Toxic-family values (177/197/213), and legacy FF/Extra twins that predate
the pipeline. The audit exits 1 only when a count EXCEEDS its baseline (a
REGRESSION), so wiring it into run_all.sh cannot block on the existing pile —
lower the baselines as the debt is paid, never raise them. Baselines were
measured 2026-08-25 against the current tree. NOT yet wired into run_all.sh:
W24 is actively collapsing multi-main weapons and the fold is replacing separate
twins, so these counts are moving targets — wiring is deferred until that work
settles, to avoid tripping a regression gate on in-flight conversions. Run on
demand with `python tools/audit/audit_damage_grid.py`.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import formula  # noqa: E402
from cameo_model import Model  # noqa: E402
from report import h1, h2, table  # noqa: E402

# Debt ratchets — measured 2026-08-25. Lower as the debt is paid; never raise.
# A count ABOVE its baseline is a regression (exit 1); at-or-below is accepted.
OFFGRID_BASELINE = 83        # main Damage off the DAMAGE_STEP grid (hand-tuned/measured)
UNEQUAL_BASELINE = 216       # weapons whose main warheads carry DIFFERENT values
PCT_TWIN_BASELINE = 0        # basis-point *Percentage twins disobeying percentage_twin
TWIN50_BASELINE = 353        # *FriendlyFire/*ExtraDamage twins != D // 2


def _int(v) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def _denominator(node) -> int:
    """The unit a percentage twin's Damage is written in, from the resolved node.

    Mirrors ``formula.twin_denominator`` but reads the resolved yaml field. Only
    ``AreaDamagePercentage`` can carry ``PercentageDenominator``; the stock
    ``HealthPercentageDamage`` has no such field and is always whole percent (100).
    An explicit value wins; absence means the engine default (100).
    """
    value = node.get("PercentageDenominator")
    if value in (None, ""):
        return formula.PERCENT_DENOMINATOR
    try:
        value = int(float(value))
    except (TypeError, ValueError):
        return formula.PERCENT_DENOMINATOR
    return value if value > 0 else formula.PERCENT_DENOMINATOR


def classify_warheads(resolved):
    """Return (mains, percentage, friendly, extra) lists of (tag, node).

    ``mains`` are flat SpreadDamage/AreaDamage nodes that are not FF/Extra twins.
    ``percentage`` are the separate *Percentage twins (both the stock
    HealthPercentageDamage and the W18 AreaDamagePercentage). Folded
    PercentageScale fields live ON a main warhead and are not a separate node.
    """
    mains, pct, ff, extra = [], [], [], []
    for c in resolved.children:
        if not c.key.startswith("Warhead@"):
            continue
        tag = c.key.split("@", 1)[1]
        low = tag.lower()
        if c.value in ("HealthPercentageDamage", "AreaDamagePercentage"):
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
    legacy_pct = 0  # whole-percent twins deliberately left by W18 — skipped, not bugs

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
            if d > 0 and d % formula.DAMAGE_STEP != 0:
                grid_rows.append([wname, tag, str(d)])

        non_zero = [d for d in main_dmgs if d > 0]
        if non_zero and len(set(non_zero)) > 1:
            eq_rows.append([wname, ", ".join(str(d) for d in main_dmgs)])

        # Use the largest main as the canonical D for twin checks.
        # When all mains are equal (the legal case), this is the common D.
        D = max(main_dmgs) if main_dmgs else 0

        for tag, c in pct:
            den = _denominator(c)
            if den != formula.BASIS_POINT_DENOMINATOR:
                # Legacy whole-percent twin (den 100, or any non-basis unit):
                # deliberately left by W18, does not obey percentage_twin. Skip.
                legacy_pct += 1
                continue
            actual = _int(c.get("Damage"))
            expected = formula.percentage_twin(D, den)
            if D > 0 and actual != expected:
                pct_rows.append([wname, tag, str(actual), str(expected)])

        for tag, c in ff + extra:
            actual = _int(c.get("Damage"))
            expected = D // 2
            if D > 0 and actual != expected:
                twin_rows.append([wname, tag, str(actual), str(expected)])

    step = formula.DAMAGE_STEP
    out = [h1(f"Damage-grid audit ({step}-step flat grid / percentage_twin)")]

    n_offgrid = len(grid_rows)
    n_unequal = len(eq_rows)
    n_pct = len(pct_rows)
    n_twin50 = len(twin_rows)
    # A REGRESSION is any count above its baseline. At-or-below is accepted debt.
    regressions = []
    if n_offgrid > OFFGRID_BASELINE:
        regressions.append(f"off-grid {n_offgrid} > {OFFGRID_BASELINE}")
    if n_unequal > UNEQUAL_BASELINE:
        regressions.append(f"unequal mains {n_unequal} > {UNEQUAL_BASELINE}")
    if n_pct > PCT_TWIN_BASELINE:
        regressions.append(f"basis-point pct twin {n_pct} > {PCT_TWIN_BASELINE}")
    if n_twin50 > TWIN50_BASELINE:
        regressions.append(f"50% twin {n_twin50} > {TWIN50_BASELINE}")
    failed = bool(regressions)

    out.append(h2(f"Off-grid main damage ({len(grid_rows)})"))
    if grid_rows:
        out.append(f"Main SpreadDamage/AreaDamage warheads must be on the "
                   f"{step}-step flat grid.\n")
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

    out.append(h2(f"Wrong percentage twin — basis-point only ({len(pct_rows)})"))
    if pct_rows:
        out.append(f"*Percentage twins written in basis points "
                   f"(PercentageDenominator {formula.BASIS_POINT_DENOMINATOR}) must equal "
                   f"percentage_twin(D, {formula.BASIS_POINT_DENOMINATOR}) = D/100.\n")
        out.append(table(["weapon", "warhead", "actual", "expected"], pct_rows))
    else:
        out.append("None.\n")

    out.append(h2(f"Wrong 50% twin ({len(twin_rows)})"))
    if twin_rows:
        out.append("*FriendlyFire / *ExtraDamage twins must equal main_damage // 2.\n")
        out.append(table(["weapon", "warhead", "actual", "expected"], twin_rows))
    else:
        out.append("None.\n")

    out.append(h2(f"Legacy whole-percent twins skipped ({legacy_pct})"))
    out.append("Deliberately left by W18 — they resolve to legacy hand-written "
               "templates that never got the basis-point denominator, so they do "
               "not obey percentage_twin and are not grid violations. Folded "
               "PercentageScale dials are not counted here either (free per-family).\n")

    out.append(h2("Ratchet (debt vs baseline)"))
    out.append(table(
        ["check", "count", "baseline", "status"],
        [
            ["off-grid main", str(n_offgrid), str(OFFGRID_BASELINE),
             "REGRESSION" if n_offgrid > OFFGRID_BASELINE else "accepted debt"],
            ["unequal mains", str(n_unequal), str(UNEQUAL_BASELINE),
             "REGRESSION" if n_unequal > UNEQUAL_BASELINE else "accepted debt"],
            ["basis-point pct twin", str(n_pct), str(PCT_TWIN_BASELINE),
             "REGRESSION" if n_pct > PCT_TWIN_BASELINE else "clean"],
            ["50% twin", str(n_twin50), str(TWIN50_BASELINE),
             "REGRESSION" if n_twin50 > TWIN50_BASELINE else "accepted debt"],
        ]))
    if regressions:
        out.append(f"\nFAIL — regression: {'; '.join(regressions)}\n")
    else:
        out.append("\nPASS — no regression (existing debt at or below baseline).\n")

    sys.stdout.write("\n".join(out) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
