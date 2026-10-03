#!/usr/bin/env python3
"""warhead_factors.py — the per-WEAPON magnitude factor, for consumers that price a weapon.

`warhead_matrix.py` measures a factor per WARHEAD. Everything downstream — the reference map,
the balance ledger — knows a reference unit by the WEAPON it fires, not by the warhead inside it.
This converts one to the other and freezes the result as a small JSON, so a consumer never has to
re-resolve five mod trees to price one row.

    factor(weapon) = geometric mean over that weapon's damage-warhead rows of (row gmean / centre)

A weapon whose warheads disagree (an anti-ground main plus an anti-air twin) therefore lands
between them, which is the honest answer for a single scalar. Weapons carrying no damage warhead
have no factor and are OMITTED rather than defaulted to 1.0 — a missing key is a question, a
silent 1.0 is a wrong answer that gets multiplied into a price.

    python tools/reference/warhead_factors.py            # summary
    python tools/reference/warhead_factors.py --write    # -> docs/reference/warhead_factors.json
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))

import warhead_matrix as wm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = ROOT / "docs" / "reference" / "warhead_factors.json"


def weapon_factors(entry: dict) -> dict[str, float]:
    """{weapon name: factor} for one source."""
    by_weapon: dict[str, list[float]] = collections.defaultdict(list)

    if entry.get("weapon_warhead"):
        # INI sources address a warhead by name from the weapon's `Warhead=` key.
        by_warhead = {row["node"]: row["factor"] for row in entry["rows"]}
        for weapon, warhead in entry["weapon_warhead"].items():
            if warhead in by_warhead:
                by_weapon[weapon].append(by_warhead[warhead])
    else:
        # OpenRA sources carry the warhead INSIDE the weapon, so the row already names it.
        for row in entry["rows"]:
            if row["weapon"]:
                by_weapon[row["weapon"]].append(row["factor"])

    return {weapon: wm.gmean(values) for weapon, values in by_weapon.items() if values}


def collect() -> dict:
    data = wm.collect()
    out = {"_method": {
        "floor_mode": wm.FLOOR_MODE,
        "window": [wm.WINDOW_LO * 100, wm.WINDOW_HI * 100],
        "note": ("factor = weapon's geometric-mean armor profile / its mod's usage-weighted "
                 "matrix centre. Multiply a reference Damage by it to make it comparable."),
    }, "sources": {}}
    for sid, entry in data.items():
        factors = weapon_factors(entry)
        out["sources"][sid] = {
            "label": entry["label"],
            "centre": entry["denominator_raw"],
            "weapons": {k: round(v, 5) for k, v in sorted(factors.items())},
            # ⚠ Consumers address a weapon by whatever spelling THEY hold, and the spellings do
            # not agree: the reference map writes CA's chaingun as `gtchaingun` where CA's own
            # yaml says `GTChainGun`. `miniyaml.Ruleset` is case-insensitive for exactly this
            # reason, so the frozen export has to be too, or 23 of 241 map voters silently miss.
            "weapons_ci": {k.lower(): round(v, 5) for k, v in sorted(factors.items())},
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--floor", choices=("absolute", "relative", "window"), default=None)
    args = ap.parse_args()
    if args.floor:
        wm.FLOOR_MODE = args.floor

    data = collect()
    print(f"{'source':18s} {'weapons':>8s} {'centre':>9s}   min..max factor")
    for sid, entry in data["sources"].items():
        values = list(entry["weapons"].values())
        span = f"{min(values):.2f} .. {max(values):.2f}" if values else "-"
        print(f"{sid:18s} {len(values):8d} {entry['centre']:9.1f}   {span}")

    if args.write:
        OUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
