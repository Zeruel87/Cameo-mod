#!/usr/bin/env python3
"""audit_turn_speed.py — TurnSpeed must be DERIVED from Speed, and a turret must match its hull.

DESIGN.md ("Vehicle turning", and the granularity block): turreted ground units turn at
`Speed / 5`, turretless / fixed-weapon units at `2 x Speed / 5`, and `Turreted.TurnSpeed`
equals the hull's. Maintainer 2026-09-07 moved Speed onto a step of 1, so the quotient is no
longer an integer and the value is ROUNDED to the nearest WAngle -- which is all the engine can
store anyway (`new WAngle(Util.ApplyPercentageModifiers(...))`), so rounding here loses nothing.

⛔ WHY THIS IS AN AUDIT AND NOT A C# TRAIT. Turn speed is an integer WAngle at every layer, and
the two runtime hooks (`ITurnSpeedModifier`, `ITurretTurnSpeedModifier`) take an integer
PERCENTAGE -- so a derived-in-code turn speed produces byte-identical values to a generated yaml
one. `Aircraft` exposes no hook at all and reads `Info.TurnSpeed` directly, so code could not
cover it without shadowing one of the largest traits in the engine. Generating the value and
GUARDING it here gets the same numbers for every unit type at no engine risk.

Read-only. Ratchets are LOWER-ONLY.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import miniyaml  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]

# LOWER-ONLY ratchets. Measured 2026-09-07 on master.
T1_BASELINE = 37    # hull TurnSpeed != round(Speed/5)   (turreted ground)
T2_BASELINE = 142   # hull TurnSpeed != round(2*Speed/5) (turretless ground)
#   ⚠ T2 includes deliberate exceptions — SCSPIDERMINE turns instantly (speed 200,
#   hull 200) on purpose. Lower it as real drift is fixed; do not chase it to zero
#   without checking each row.
T3_BASELINE = 27    # Turreted.TurnSpeed != Mobile.TurnSpeed
T4_BASELINE = 137   # turreted actor with NO hull speed (immobile turret, own rule pending)


def field(node, trait, key):
    for c in node.children:
        if c.key == trait or c.key.startswith(trait + "@"):
            for f in c.children:
                if f.key == key:
                    return f.value
    return None


def has(node, trait):
    return any(c.key == trait or c.key.startswith(trait + "@") for c in node.children)


def num(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def main() -> int:
    rs = miniyaml.Ruleset(ROOT, "cameo")
    t1, t2, t3, t4 = [], [], [], []
    for aid in sorted(rs.actors):
        try:
            n = rs.resolve(aid)
        except Exception:
            continue
        if not has(n, "Mobile") and not has(n, "Turreted"):
            continue
        speed = num(field(n, "Mobile", "Speed"))
        hull = num(field(n, "Mobile", "TurnSpeed"))
        turret = num(field(n, "Turreted", "TurnSpeed"))
        turreted = has(n, "Turreted")

        if turreted and hull is None:
            t4.append((aid, turret))
            continue
        if speed is None or hull is None:
            continue

        want = round(speed / 5) if turreted else round(2 * speed / 5)
        if hull != want:
            (t1 if turreted else t2).append((aid, speed, hull, want))
        if turret is not None and turret != hull:
            t3.append((aid, hull, turret))

    def block(code, desc, rows, baseline, render):
        bad = len(rows) > baseline
        print(f"\n## {code} — {desc}: **{len(rows)}** (ratchet {baseline}) "
              f"{'⛔ RAISED' if bad else 'ok'}")
        for r in rows[:12]:
            print("   " + render(r))
        if len(rows) > 12:
            print(f"   … and {len(rows) - 12} more")
        return bad

    print("# TurnSpeed derivation (DESIGN.md — Vehicle turning)")
    failed = False
    failed |= block("T1", "turreted ground: hull != round(Speed/5)", t1, T1_BASELINE,
                    lambda r: f"{r[0]:36} speed={r[1]:<5} hull={r[2]:<5} want={r[3]}")
    failed |= block("T2", "turretless ground: hull != round(2*Speed/5)", t2, T2_BASELINE,
                    lambda r: f"{r[0]:36} speed={r[1]:<5} hull={r[2]:<5} want={r[3]}")
    failed |= block("T3", "turret turn speed != hull turn speed", t3, T3_BASELINE,
                    lambda r: f"{r[0]:36} hull={r[1]:<6} turret={r[2]}")
    failed |= block("T4", "turreted actor with NO hull speed (immobile — own rule pending)",
                    t4, T4_BASELINE, lambda r: f"{r[0]:36} turret={r[1]}")
    print(f"\nexit={1 if failed else 0}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
