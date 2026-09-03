#!/usr/bin/env python3
"""audit_burst_delays.py — DESIGN.md burst-weapon timing rule.

For any weapon with Burst > 1:
    ReloadDelay must leave at least one configured gap after the last shot.

For a scalar delay this is the historical ``Burst * BurstDelays`` law. Lists
sum every actual inter-shot gap and reserve one longest gap as idle time.
Missing BurstDelays uses WeaponInfo's engine default of five ticks.
"""

from __future__ import annotations

import pathlib
import sys

from cameo_model import Model
from report import h1, h2, table

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import formula  # noqa: E402


def parse_num(value: str | None, default: int | None = None) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def main() -> int:
    m = Model()
    rs = m.rs
    violations: list[list[str]] = []

    for name in sorted(rs.weapons):
        w = rs.resolve_weapon(name)
        if w is None:
            continue
        burst = parse_num(w.get("Burst"), 1)
        raw_delays = w.get("BurstDelays")
        delays = formula.burst_delay_values(raw_delays)
        if delays is None:
            delays = [int(formula.ENGINE_DEFAULT_BURST_DELAY)]
        rd = parse_num(w.get("ReloadDelay"), 1)
        if not burst or burst <= 1 or rd is None:
            continue
        gap_total = formula.burst_delay_sum(burst, raw_delays)
        minimum = int(gap_total + max(delays))
        if rd < minimum:
            violations.append([
                name, str(rd), str(burst),
                formula.burst_delays_text(raw_delays) or "default 5", str(minimum)
            ])

    print(h1("Burst weapon delay audit"))
    if violations:
        print(h2("ReloadDelay leaves less than one full gap after the burst"))
        print(table(
            ["Weapon", "ReloadDelay", "Burst", "BurstDelays", "Minimum"],
            violations,
        ))
        return 1

    print("All burst weapons retain at least one full configured gap of idle time.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
