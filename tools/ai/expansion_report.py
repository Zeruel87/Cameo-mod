#!/usr/bin/env python3
"""expansion_report.py - the field-economy picture per bot and match (AI_ARCHITECTURE 12.24 FE-0).

Reads the `expansion` object of every situation snapshot (`cameo-ai-situations.jsonl`) and the placement log
(`cameo-ai-placements.jsonl`) of one or more match dirs (a batch support dir, its `Logs/`, or a jsonl file).

Per bot x match:
  first_refinery      mm:ss of the first refinery placed (placement log; else the first snapshot with one)
  harvested_5/10/20   fields with an own harvester on them at minute 5 / 10 / 20 (last snapshot at or before it;
                      '-' when the match ended earlier)
  peak_harvested      the most fields harvested at once
  peak_coverage       the best share of known fields in reach of, or served by, our buildings (0..1)
  max_excess          the most refineries beyond one per anchor (anchor = spreader, else a spreaderless field;
                      a refinery serves the nearest anchor within 12 cells, farther ones count as excess)
  anchor_dist_mean/max  refinery to nearest anchor distance in cells (mean of the snapshots' means / max of the maxima)
  angle_median / angle_lt45  the crawl target vs MCV site bearing angle from the main base (degrees; share of
                      snapshots below 45)
  conyards_peak       the most construction yards at once
Then an aggregate row per bot type + personality (mean over its matches).

Usage: python tools/ai/expansion_report.py <match dirs...> [--json]
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ai_log_common as c  # noqa: E402

METRICS = ["first_refinery_min", "harvested_5", "harvested_10", "harvested_20", "peak_harvested", "peak_coverage",
           "max_excess", "anchor_dist_mean", "anchor_dist_max", "angle_median", "angle_lt45", "conyards_peak"]


def summarise_match(snaps: list[dict], placements: list[dict], match: dict | None) -> dict:
    # Game time is always the nominal clock (DEFAULT_TIMESTEP_MS); the recorded engine `timestep` is the speed setting, not game time.
    snaps = sorted((s for s in snaps if s.get("expansion")), key=lambda s: s["tick"])
    first_ref = min((p["tick"] for p in placements if p.get("category") == "refinery"), default=None)
    if first_ref is None:
        first_ref = next((s["tick"] for s in snaps if s["expansion"].get("refineries", 0) > 0), None)
    last_tick = snaps[-1]["tick"] if snaps else 0

    def harvested_at(minute: int):
        limit = minute * 60000 / c.DEFAULT_TIMESTEP_MS
        if last_tick < limit:
            return None
        before = [s for s in snaps if s["tick"] <= limit]
        return before[-1]["expansion"].get("fields_harvested", 0) if before else None

    ex = [s["expansion"] for s in snaps]
    angles = [e["crawl_mcv_angle"] for e in ex if e.get("crawl_mcv_angle", -1) >= 0]
    with_ref = [e for e in ex if e.get("refineries", 0) > 0]
    return {
        "first_refinery_tick": first_ref,
        "first_refinery_min": None if first_ref is None else round(c.minutes(first_ref), 2),
        "harvested_5": harvested_at(5), "harvested_10": harvested_at(10), "harvested_20": harvested_at(20),
        "peak_harvested": max((e.get("fields_harvested", 0) for e in ex), default=None),
        "peak_coverage": max((e.get("coverage_milli", 0) for e in ex), default=None) if ex else None,
        "max_excess": max((e.get("excess_refineries", 0) for e in ex), default=None),
        "anchor_dist_mean": c.mean([e.get("anchor_dist_mean") for e in with_ref]),
        "anchor_dist_max": max((e.get("anchor_dist_max", 0) for e in with_ref), default=None),
        "angle_median": c.median(angles),
        "angle_lt45": (sum(1 for a in angles if a < 45) / len(angles)) if angles else None,
        "conyards_peak": max((e.get("conyards", 0) for e in ex), default=None),
        "snapshots": len(ex),
    }


def build(data: dict[str, list[dict]]) -> dict:
    matches = {(m.get("game_uid"), m.get("player", {}).get("name")): m for m in data["matches"]}
    by_snap = collections.defaultdict(list)
    for s in data["situations"]:
        by_snap[(s.get("game_uid"), s.get("player"))].append(s)
    by_place = collections.defaultdict(list)
    for p in data["placements"]:
        by_place[(p.get("game_uid"), p.get("player"))].append(p)

    rows = []
    for key in sorted(set(by_snap) | set(by_place), key=lambda k: (str(k[0]), str(k[1]))):
        snaps, places, match = by_snap.get(key, []), by_place.get(key, []), matches.get(key)
        ref = (snaps or places or [{}])[0]
        pers = collections.Counter(s.get("personality_current") for s in snaps if s.get("personality_current"))
        personality = (pers.most_common(1)[0][0] if pers else None) or (match or {}).get("player", {}).get("personality") \
            or ref.get("personality") or ""
        row = {"game_uid": key[0], "player": key[1],
               "bot_type": ref.get("bot_type") or (match or {}).get("player", {}).get("bot_type", ""),
               "personality": personality}
        row.update(summarise_match(snaps, places, match))
        rows.append(row)

    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r["bot_type"], r["personality"])].append(r)
    aggregate = []
    for (bot, pers), members in sorted(groups.items()):
        agg = {"bot_type": bot, "personality": pers, "matches": len(members)}
        for m in METRICS:
            agg[m] = c.mean([r.get(m) for r in members])
        aggregate.append(agg)
    return {"matches": rows, "aggregate": aggregate}


def render(result: dict) -> str:
    head = ["bot", "personality", "player", "first_ref", "h@5", "h@10", "h@20", "peak_h", "peak_cov", "max_excess",
            "dist_mean", "dist_max", "angle_med", "angle<45", "yards"]
    rows = [head]
    for r in result["matches"]:
        first = "-" if r["first_refinery_tick"] is None else c.mmss(r["first_refinery_tick"])
        cov = None if r["peak_coverage"] is None else r["peak_coverage"] / 1000
        rows.append([r["bot_type"], r["personality"], f'{r["game_uid"]}/{r["player"]}', first, c.fmt(r["harvested_5"]),
                     c.fmt(r["harvested_10"]), c.fmt(r["harvested_20"]), c.fmt(r["peak_harvested"]), c.fmt(cov, 2),
                     c.fmt(r["max_excess"]), c.fmt(r["anchor_dist_mean"]), c.fmt(r["anchor_dist_max"]),
                     c.fmt(r["angle_median"], 0), c.fmt(r["angle_lt45"], 2), c.fmt(r["conyards_peak"])])
    out = ["Per bot x match", c.table(rows), "", "Aggregate (mean over matches)"]
    arows = [["bot", "personality", "n", "first_ref_min", "h@5", "h@10", "h@20", "peak_h", "peak_cov", "max_excess",
              "dist_mean", "dist_max", "angle_med", "angle<45", "yards"]]
    for a in result["aggregate"]:
        cov = None if a["peak_coverage"] is None else a["peak_coverage"] / 1000
        arows.append([a["bot_type"], a["personality"], str(a["matches"]), c.fmt(a["first_refinery_min"]),
                      c.fmt(a["harvested_5"]), c.fmt(a["harvested_10"]), c.fmt(a["harvested_20"]),
                      c.fmt(a["peak_harvested"]), c.fmt(cov, 2), c.fmt(a["max_excess"]), c.fmt(a["anchor_dist_mean"]),
                      c.fmt(a["anchor_dist_max"]), c.fmt(a["angle_median"], 0), c.fmt(a["angle_lt45"], 2),
                      c.fmt(a["conyards_peak"])])
    out.append(c.table(arows))
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dirs", nargs="+", type=pathlib.Path)
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    args = ap.parse_args(argv)
    result = build(c.load(args.dirs))
    if not result["matches"]:
        print("no situation or placement records found", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
