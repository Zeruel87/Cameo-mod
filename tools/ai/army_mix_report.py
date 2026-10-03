#!/usr/bin/env python3
"""army_mix_report.py — what did each bot actually BUILD? (AI_ARCHITECTURE §12.11)

Maintainer 2026-09-29: "add a unit tracking to see the army composition so that you can easily
notice ... just Humvee and infantry spam instead of building a mix of all available units."

Reads the arsenal ledger (`arsenal[].created`) of every match record in one or more batch support
dirs (or `cameo-ai-matches.jsonl` files) and prints, per bot type, the mobile units built per
match: shares by class, the top types, and FLAGS for a lopsided mix. Buildings, upgrades and
anything without `Buildable` are left out.

Classes come from the resolved rules (CLAUDE.md rule 8e: miniyaml, never a line scanner):
  economy   — has `Harvester`, or `Transforms` (an MCV): counted apart, never in the army shares
  aircraft  — has `Aircraft`
  ship      — its `Mobile.Locomotor` name contains "naval" (the §12.4a ship rule)
  infantry  — a `Targetable.TargetTypes` list holds `Infantry`
  vehicle   — every other mobile unit; `heavy` when its `Armor.Type` is Heavy or Superheavy,
              `artillery` when its `BotRoles` hold `artillery` (the rules-derived role, §12.4a)

Flags (each threshold is a flag, with its default):
  --max-share 0.25   one unit type is more than this share of all units built
  --min-heavy 0.05   heavy vehicles are less than this share of all vehicles
  --min-artillery 0.05  artillery is less than this share of all vehicles
Exit status 1 when any bot type is flagged (usable as a batch check).

Usage:
  python tools/ai/army_mix_report.py <support-dir or jsonl> [...] [--bot hard] [--top 8]
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools" / "audit"), str(ROOT / "tools" / "balance"), str(ROOT / "tools")]

MATCH_LOG = "cameo-ai-matches.jsonl"
HEAVY_ARMOR = {"Heavy", "Superheavy"}


def record_files(paths: list[pathlib.Path]) -> list[pathlib.Path]:
    out = []
    for p in paths:
        if p.is_file():
            out.append(p)
        elif (p / "Logs" / MATCH_LOG).is_file():
            out.append(p / "Logs" / MATCH_LOG)
        elif (p / MATCH_LOG).is_file():
            out.append(p / MATCH_LOG)
        else:
            sys.exit(f"no {MATCH_LOG} under {p}")
    return out


def _traits(node, trait):
    return [c for c in node.children if c.key.split("@")[0] == trait]


def _value(node, trait, field):
    for c in _traits(node, trait):
        x = c.child(field)
        if x is not None and x.value is not None:
            return x.value
    return None


def classify(node) -> tuple[str, bool, bool] | None:
    """(class, heavy, artillery) for a buildable mobile unit, else None."""
    if node is None or not _traits(node, "Buildable") or _traits(node, "Building"):
        return None
    roles = {r.strip() for c in _traits(node, "BotRoles") for x in c.children if x.key == "Roles"
             for r in (x.value or "").split(",")}
    artillery = "artillery" in roles
    if _traits(node, "Harvester") or _traits(node, "Transforms"):
        return "economy", False, False
    if _traits(node, "Aircraft"):
        return "aircraft", False, artillery
    locomotor = _value(node, "Mobile", "Locomotor")
    if locomotor is None:
        return None
    if "naval" in locomotor.lower():
        return "ship", False, artillery
    target_types = {t.strip() for c in _traits(node, "Targetable") for x in c.children
                    if x.key == "TargetTypes" for t in (x.value or "").split(",")}
    if "Infantry" in target_types:
        return "infantry", False, artillery
    return "vehicle", _value(node, "Armor", "Type") in HEAVY_ARMOR, artillery


def summarise(records: list[dict], kind_of) -> dict:
    """Per bot type: matches, built counts per type, and class totals."""
    out = collections.defaultdict(lambda: {"matches": 0, "types": collections.Counter()})
    for r in records:
        bot = (r.get("player") or {}).get("bot_type") or "?"
        out[bot]["matches"] += 1
        for a in r.get("arsenal") or []:
            if kind_of(a["type"]) is not None and a.get("created", 0) > 0:
                out[bot]["types"][a["type"]] += a["created"]
    return out


def mix(entry: dict, kind_of) -> dict:
    types = entry["types"]
    army = [(t, n) for t, n in types.most_common() if kind_of(t)[0] != "economy"]
    total = sum(n for _, n in army)
    by_class = collections.Counter()
    heavy = artillery = 0
    for t, n in types.items():
        cls, is_heavy, is_art = kind_of(t)
        by_class[cls] += n
        if cls == "economy":
            continue
        heavy += n if cls == "vehicle" and is_heavy else 0
        artillery += n if is_art else 0
    vehicles = by_class["vehicle"]
    return {
        "total": total,
        "by_class": by_class,
        "heavy_share_of_vehicles": heavy / vehicles if vehicles else 0.0,
        "artillery_share_of_vehicles": artillery / vehicles if vehicles else 0.0,
        "top": army,
    }


def flags(m: dict, max_share: float, min_heavy: float, min_artillery: float) -> list[str]:
    out = []
    if m["total"] and m["top"]:
        name, n = m["top"][0]
        if n / m["total"] > max_share:
            out.append(f"one type dominates: {name} is {n / m['total']:.0%} of all units (> {max_share:.0%})")
    if m["by_class"]["vehicle"]:
        if m["heavy_share_of_vehicles"] < min_heavy:
            out.append(f"almost no heavy vehicles: {m['heavy_share_of_vehicles']:.0%} of vehicles (< {min_heavy:.0%})")
        if m["artillery_share_of_vehicles"] < min_artillery:
            out.append(f"almost no artillery: {m['artillery_share_of_vehicles']:.0%} of vehicles (< {min_artillery:.0%})")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+", type=pathlib.Path)
    ap.add_argument("--bot", help="only this bot type")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--max-share", type=float, default=0.25)
    ap.add_argument("--min-heavy", type=float, default=0.05)
    ap.add_argument("--min-artillery", type=float, default=0.05)
    args = ap.parse_args(argv)

    import miniyaml
    rules = miniyaml.Ruleset(ROOT)
    cache: dict[str, tuple | None] = {}

    def kind_of(name: str):
        if name not in cache:
            cache[name] = classify(rules.resolve(name))
        return cache[name]

    records = [json.loads(line) for f in record_files(args.paths)
               for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
    flagged = False
    for bot, entry in sorted(summarise(records, kind_of).items()):
        if args.bot and bot != args.bot:
            continue
        m, n = mix(entry, kind_of), entry["matches"]
        print(f"\n## `{bot}`: {n} match(es), {m['total'] / n:.0f} units built per match")
        print("| class | per match | share |\n|---|--:|--:|")
        for cls in ("infantry", "vehicle", "aircraft", "ship"):
            c = m["by_class"][cls]
            print(f"| {cls} | {c / n:.1f} | {c / m['total']:.0%} |" if m["total"] else f"| {cls} | 0 | — |")
        print(f"\nvehicles: {m['heavy_share_of_vehicles']:.0%} heavy, {m['artillery_share_of_vehicles']:.0%} artillery"
              f" · economy (harvesters, MCVs; not in the shares above): {m['by_class']['economy'] / n:.1f} per match")
        print("\n| top type | per match | share |\n|---|--:|--:|")
        for t, c in m["top"][:args.top]:
            print(f"| `{t}` | {c / n:.1f} | {c / m['total']:.0%} |")
        found = flags(m, args.max_share, args.min_heavy, args.min_artillery)
        for f in found:
            print(f"\n**FLAG** — {f}")
        flagged |= bool(found)
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
