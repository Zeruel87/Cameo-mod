#!/usr/bin/env python3
"""update_ranges.py — Balance Pipeline Phase 3.5 (range solver).

Reads the extracted ledgers and class_anchors.json, computes the class-
baseline range that makes each unit's formula price equal its cost, rounds
to the nearest 10, and updates the ledger weapon ranges.

Usage:
    python tools/balance/update_ranges.py                 # dry run
    python tools/balance/update_ranges.py --confirm       # write ledger
    python tools/balance/update_ranges.py --faction tkm   # filter

This script is gated: it only writes JSON when --confirm is passed. After
reviewing the dry-run output, the maintainer can confirm and then run
apply_balance.py to propagate the ledger ranges into YAML.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import formula  # noqa: E402
import class_membership  # noqa: E402

LEDGER_DIR = ROOT / "docs/balance"
ANCHORS_FILE = LEDGER_DIR / "class_anchors.json"


def fnum(v):
    try:
        f = float(v)
        return int(f) if f == int(f) else f
    except (TypeError, ValueError):
        return None


def subtype_to_anchor(st):
    """DELEGATES to `tools/balance/class_membership.py`, the single map.

    ⛔ There were THREE copies of this function and they disagreed: `build_workbook.py` and
    this one knew 5 subtypes, `propose_class_rebalance.py` knew 17, and all three said
    `linebreaker -> mbt` when `line_breaker` is its own class — 40 line-breakers were being
    folded into the MBT population. Kept as a name so the call sites do not all have to
    change at once.
    """
    return class_membership.subtype_to_anchor(st)


def load_anchors():
    data = json.loads(ANCHORS_FILE.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if isinstance(v, dict) and "spec" in v}


def unit_dps(u, fp_factor: float):
    total = 0.0
    for arm in u.get("armaments", []):
        if not arm.get("pricing", True):
            continue
        dmg = formula.spread_damage_sum(arm.get("damage_warheads", []))  # SUM law, chips excluded
        if not dmg:
            continue
        rd = fnum(arm.get("reloaddelay")) or 1
        burst = int(fnum(arm.get("burst")) or 1)
        bd = arm.get("burstdelays")
        total += formula.dps(dmg, rd, burst, bd, fp_factor)
    return total


def process_ledger(path: pathlib.Path, anchors, faction_filter, confirm: bool):
    doc = json.loads(path.read_text(encoding="utf-8"))
    if faction_filter and faction_filter not in doc.get("ledger", ""):
        return 0
    changes = 0
    for section, sec in doc.get("sections", {}).items():
        for aid, u in sec.items():
            design = u.get("design") or {}
            cls = design.get("class_anchor") or subtype_to_anchor(design.get("subtype"))
            if cls not in anchors:
                continue
            spec = anchors[cls]["spec"]
            cost = fnum((u.get("cost") or {}).get("v"))
            hp = fnum((u.get("hp") or {}).get("v"))
            speed = fnum((u.get("speed") or {}).get("v")
                         or (u.get("speed_air") or {}).get("v"))
            special = fnum(design.get("special")) or 1.0
            tech_tier = fnum(design.get("tech_tier")) or 1.0
            fp_raw = fnum((u.get("firepower_multiplier") or {}).get("v"))
            fp = (fp_raw / 100) if fp_raw is not None else 1.0
            if None in (cost, hp, speed):
                continue
            dps_eff = unit_dps(u, fp)
            if dps_eff <= 0:
                continue
            rng = formula.solve_class_baseline_range(
                cost, hp, speed, dps_eff,
                spec["hp0"], spec["speed0"], spec["range0_wdist"], spec["dps0"], spec["cost0"],
                special, tech_tier,
            )
            rng = int(round(rng / 10)) * 10
            if rng <= 0:
                continue
            for arm in u.get("armaments", []):
                if not arm.get("pricing", True):
                    continue
                old = formula.wdist_value(arm.get("range"))
                if old is not None and int(old) == rng:
                    continue
                if confirm:
                    arm["range"] = str(rng)
                print(f"{aid}/{arm.get('slot')}: {old} -> {rng} ({cls})")
                changes += 1
    if confirm and changes:
        path.write_text(json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
    return changes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="write updated ledgers")
    ap.add_argument("--faction", help="ledger name substring filter")
    args = ap.parse_args()

    anchors = load_anchors()
    total = 0
    for jf in sorted(LEDGER_DIR.glob("*.json")):
        if jf.name == "class_anchors.json":
            continue
        total += process_ledger(jf, anchors, args.faction, args.confirm)
    if args.confirm:
        print(f"WROTE {total} range updates to ledgers")
    else:
        print(f"DRY RUN: {total} range values would change (re-run with --confirm)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
