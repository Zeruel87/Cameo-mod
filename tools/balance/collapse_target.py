#!/usr/bin/env python3
"""collapse_target.py — the ONE number a W24 collapse is allowed to write.

Between 27 Aug and 3 Sep a consolidation series collapsed multi-main weapons and
wrote a survivor `Damage` that was neither the old per-main value nor the sum.
96 weapons ended up delivering 4x to 7.5x what they shipped, and every audit in
the tree said PASS, because every audit compared the tree to itself.

This tool removes the judgement from the step that went wrong. It does not
choose the family — `plan_warhead_collapse.py` already does that, with a
confidence rating — and it does not edit yaml. It answers exactly one question:

    when this weapon becomes ONE main warhead, what must its Damage be?

The law (DESIGN.md, maintainer ruling 2026-09-07):

    "make it so the total damage output remains the same after the collapse."

    The survivor's Damage = the SUM of the weapon's RESOLVED MAIN warheads.
    "Verbatim" is not a second rule — it is what that sum equals when the weapon
    resolves to exactly one main. Count the RESOLVED MAINS, never the inherits.

with one refinement the drift data forced:

  * the weapon SHIPPED in the release baseline -> the target is the SHIPPED
    total, not today's sum. Today's sum may already be inflated: `MarineMG`
    shipped 3 mains totalling 6,000 and now carries one main of 36,000, so
    summing today's value would bake in the 6x rather than repair it.
  * the weapon is NEWER than the baseline -> the target is the sum of its
    current mains. There is no shipped value to restore, so the tree is its own
    baseline and the weapon keeps delivering exactly what it delivers today.

Usage:
  python tools/balance/collapse_target.py --weapon HydraSpit
  python tools/balance/collapse_target.py --pack TiberianSun     # a whole lane
  python tools/balance/collapse_target.py --pack D2k --tsv       # machine-readable

⚠ This tool tells you the number. It does NOT verify you wrote it. After editing,
run — in this order, all of them:

    python tools/audit/find_empty_warhead.py          # must print 0
    python tools/audit/audit_release_drift.py         # D1-D4 must not rise
    python tools/audit/audit_weapon_shape.py          # W1-W6 must not rise
    launch-game.cmd                                   # menu, no new exception log
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from audit_three_way_split import main_warhead_nodes   # noqa: E402  the SHARED predicate
from miniyaml import Ruleset                           # noqa: E402

BASELINE_DIR = ROOT / "docs" / "reference"


def load_baseline() -> tuple[str, dict]:
    files = sorted(BASELINE_DIR.glob("release_baseline_*.json"))
    if not files:
        raise SystemExit("no release baseline — run tools/audit/gen_release_baseline.py")
    raw = json.loads(files[-1].read_text(encoding="utf-8"))
    return raw["_release_tag"], raw["weapons"]


def damage_of(node) -> int:
    v = node.get("Damage")
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return 0


def target_for(name: str, resolved, base: dict) -> dict:
    """The survivor's Damage, and the evidence for it."""
    mains = main_warhead_nodes(resolved)
    current = [(w.key, damage_of(w)) for w in mains]
    total_now = sum(d for _k, d in current)

    shipped = base.get(name)
    if shipped is not None and shipped.get("flat", 0) > 0:
        return {
            "weapon": name,
            "mains": current,
            "sum_now": total_now,
            "target": shipped["flat"],
            "source": "SHIPPED",
            "shipped_mains": shipped["mains"],
            "note": ("today's sum is already wrong — restore the shipped total"
                     if total_now != shipped["flat"] else "today's sum matches the shipped total"),
        }
    return {
        "weapon": name,
        "mains": current,
        "sum_now": total_now,
        "target": total_now,
        "source": "SUM",
        "shipped_mains": None,
        "note": "newer than the baseline — the tree is its own baseline",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weapon", action="append", default=[],
                    help="weapon id (repeatable)")
    ap.add_argument("--pack", default="",
                    help="only weapons defined under a ContentPack path containing this")
    ap.add_argument("--multi-only", action="store_true",
                    help="only weapons that still resolve to MORE THAN ONE main")
    ap.add_argument("--tsv", action="store_true", help="machine-readable")
    args = ap.parse_args()

    tag, base = load_baseline()
    rs = Ruleset(ROOT)

    names = args.weapon or sorted(n for n in rs.weapons if not n.startswith("^"))
    rows = []
    for name in names:
        src = rs.weapons.get(name)
        if src is None:
            print(f"⚠ unknown weapon: {name}", file=sys.stderr)
            continue
        if args.pack and args.pack.lower() not in str(getattr(src, "file", "")).lower():
            continue
        try:
            resolved = rs.resolve_weapon(name)
        except Exception:
            continue
        if resolved is None:
            continue
        info = target_for(name, resolved, base)
        if not info["mains"]:
            continue
        if args.multi_only and len(info["mains"]) < 2:
            continue
        rows.append(info)

    if args.tsv:
        print("weapon\tmains_now\tsum_now\ttarget\tsource")
        for r in rows:
            print(f"{r['weapon']}\t{len(r['mains'])}\t{r['sum_now']}\t{r['target']}\t{r['source']}")
        return 0

    if not rows:
        print("no weapon matched.")
        return 0

    changed = [r for r in rows if r["target"] != r["sum_now"]]
    print(f"# collapse targets — baseline `{tag}`\n")
    print(f"**{len(rows)}** weapon(s); **{len(changed)}** where the target differs from "
          f"today's summed damage.\n")

    for r in rows:
        flag = "  ⛔ CHANGES THE NUMBER" if r["target"] != r["sum_now"] else ""
        print(f"## `{r['weapon']}`{flag}")
        print(f"    resolved mains now : {len(r['mains'])}")
        for k, d in r["mains"]:
            print(f"        {k:<48} {d:>9}")
        print(f"    sum of those       : {r['sum_now']:>9}")
        if r["source"] == "SHIPPED":
            print(f"    shipped in {tag}: {r['target']:>9}  "
                  f"({r['shipped_mains']} main(s))")
        print(f"    ==> WRITE Damage   : {r['target']:>9}   [{r['source']}]")
        print(f"    {r['note']}")
        print()

    print("After editing, in this order — all four must pass:\n"
          "    python tools/audit/find_empty_warhead.py      # 0\n"
          "    python tools/audit/audit_release_drift.py     # D1-D4 must not rise\n"
          "    python tools/audit/audit_weapon_shape.py      # W1-W6 must not rise\n"
          "    launch-game.cmd                               # menu, no new exception log\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
