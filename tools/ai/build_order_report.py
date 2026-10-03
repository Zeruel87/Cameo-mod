#!/usr/bin/env python3
"""build_order_report.py - the building build order and what it scored (AI_ARCHITECTURE 12.25 BO-0).

Reads the placement log (`cameo-ai-placements.jsonl`) and the match log (`cameo-ai-matches.jsonl`) of one or more
match dirs (a batch support dir, its `Logs/`, or a jsonl file).

Per bot x match: the ordered building list (mm:ss, actor, category, reason), the time to the first building of each
category (conyard, power, refinery, production, tech, defence, support, superweapon, other), and the outcome.

SCORE (one number per bot per match; higher is better):
    win    = 1 if the player's outcome is "won", else 0
    margin = (killed - lost) / (killed + lost)           killed = stats.kills_cost, lost = stats.deaths_cost
             (0 when both are 0; range -1..1)
    speed  = SPEED_WEIGHT * (1 - duration_ticks / SPEED_REF_TICKS) clamped to [0, weight]; wins only
    score  = win + margin + speed                        the ONE shared objective: ai_log_common.match_score
A fast, lopsided win tops out near 2.25; a drawn-out loss with equal trades is 0. The constants are the
tuner's (the acceptance gate) - this report displays exactly what the gate optimizes.

Aggregates: by personality, and by knob vector (the BO-1 knobs, read from `player.knobs` or `knobs` of the match record
when present; "(none)" otherwise): matches, win rate, mean score and the mean time to first of each category.

Usage: python tools/ai/build_order_report.py <match dirs...> [--json]
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ai_log_common as c  # noqa: E402

CATEGORIES = ["conyard", "power", "refinery", "production", "tech", "defence", "support", "superweapon", "other"]


def knob_vector(match: dict | None) -> str:
    if not match:
        return "(none)"
    knobs = match.get("player", {}).get("knobs") or match.get("knobs")
    return json.dumps(knobs, sort_keys=True) if knobs else "(none)"


def build(data: dict[str, list[dict]]) -> dict:
    matches = {(m.get("game_uid"), m.get("player", {}).get("name")): m for m in data["matches"]}
    by_place = collections.defaultdict(list)
    for p in data["placements"]:
        by_place[(p.get("game_uid"), p.get("player"))].append(p)

    rows = []
    for key in sorted(by_place, key=lambda k: (str(k[0]), str(k[1]))):
        places = sorted(by_place[key], key=lambda p: (p.get("placed_tick", p["tick"]), p.get("actor", "")))
        match = matches.get(key)
        first = {}
        for p in places:
            first.setdefault(p["category"], p.get("placed_tick", p["tick"]))
        row = {
            "game_uid": key[0], "player": key[1], "bot_type": places[0].get("bot_type", ""),
            "personality": (match or {}).get("player", {}).get("personality") or places[0].get("personality", ""),
            "knobs": knob_vector(match),
            "order": [{"time": c.mmss(p.get("placed_tick", p["tick"])), "tick": p.get("placed_tick", p["tick"]),
                       "queued_tick": p.get("queued_tick"), "actor": p["actor"], "category": p["category"],
                       "reason": p["reason"]} for p in places],
            "first_by_category": {cat: round(c.minutes(t), 2) for cat, t in first.items()},
            "outcome": None,
        }
        if match:
            stats = match.get("stats", {})
            length = c.minutes(match.get("duration_ticks", 0))
            row["outcome"] = {"result": match.get("player", {}).get("outcome", ""), "length_min": round(length, 2),
                              "kills_cost": stats.get("kills_cost", 0), "deaths_cost": stats.get("deaths_cost", 0)}
            row["outcome"].update(c.match_score(row["outcome"]["result"], row["outcome"]["kills_cost"],
                                                row["outcome"]["deaths_cost"], match.get("duration_ticks", 0)))
        rows.append(row)

    def aggregate(keyname):
        groups = collections.defaultdict(list)
        for r in rows:
            groups[r[keyname]].append(r)
        out = []
        for k, members in sorted(groups.items()):
            scored = [m for m in members if m["outcome"]]
            out.append({keyname: k, "matches": len(members), "scored": len(scored),
                        "win_rate": c.mean([m["outcome"]["win"] for m in scored]),
                        "mean_score": c.mean([m["outcome"]["score"] for m in scored]),
                        "first_by_category": {cat: c.mean([m["first_by_category"].get(cat) for m in members])
                                              for cat in CATEGORIES}})
        return out

    return {"matches": rows, "by_personality": aggregate("personality"), "by_knobs": aggregate("knobs")}


def render(result: dict) -> str:
    out = []
    for r in result["matches"]:
        o = r["outcome"]
        head = f'{r["bot_type"]} {r["personality"]} {r["game_uid"]}/{r["player"]}'
        if o:
            head += (f' - {o["result"]} in {o["length_min"]:.1f} min, killed {o["kills_cost"]} lost {o["deaths_cost"]}, '
                     f'score {o["score"]:.3f} (win {o["win"]} + margin {o["margin"]:.3f} + speed {o["speed_bonus"]:.3f})')
        out.append(head)
        out.append(c.table([["time", "actor", "category", "reason"]]
                           + [[b["time"], b["actor"], b["category"], b["reason"]] for b in r["order"]]))
        out.append("first: " + ", ".join(f'{cat} {r["first_by_category"][cat]:.1f}m' for cat in CATEGORIES
                                         if cat in r["first_by_category"]))
        out.append("")
    for title, key, name in (("By personality", "by_personality", "personality"), ("By knob vector", "by_knobs", "knobs")):
        rows = [[name, "n", "win_rate", "mean_score"] + [f"first_{cat}" for cat in CATEGORIES]]
        for a in result[key]:
            rows.append([a[name], str(a["matches"]), c.fmt(a["win_rate"], 2), c.fmt(a["mean_score"], 3)]
                        + [c.fmt(a["first_by_category"][cat]) for cat in CATEGORIES])
        out += [title + " (first_* = mean minutes)", c.table(rows), ""]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dirs", nargs="+", type=pathlib.Path)
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    args = ap.parse_args(argv)
    result = build(c.load(args.dirs))
    if not result["matches"]:
        print("no placement records found", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
