#!/usr/bin/env python3
"""engagement_report.py - how each bot fights: the engagement log scored (AI_ARCHITECTURE 12.30 EL-0).

Reads `cameo-ai-engagements.jsonl` (schema engagement/1) of one or more match dirs (a batch support dir, its `Logs/`,
or a jsonl file). Skirmishes (below the value / death minimum) are counted but kept out of every statistic.

Per bot type x personality x kind (defend / attack / field):
  n / skirmish        scored engagements / skirmishes
  trade, vs_pred, objective, total   mean score parts (thousandths, -1000..1000)
  resp_med / resp_p90 defend only: seconds from the first own damage to the first own mobile unit dealing damage
  army_dist_med       defend only: median own army distance from the fight at its start (cells)
  art_first           attack only: share of attacks with defences where defences died before direct fire entered range
  suicide_med / suicide_gt2   attack only: median suicide_index and the share above 2.0
  pred_mae            mean |actual trade - predicted trade| (the predictor's calibration, thousandths)
  truth_gap           mean (real enemy value - seen enemy value) at the start, in value units

Game time is the nominal clock (DEFAULT_TIMESTEP_MS), never the recorded engine timestep.

Usage: python tools/ai/engagement_report.py <match dirs...> [--json]
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ai_log_common as c  # noqa: E402


def percentile(values, pct: float):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    idx = min(len(values) - 1, max(0, int(round(pct / 100.0 * (len(values) - 1)))))
    return values[idx]


def summarise(records: list[dict]) -> dict:
    scored = [r for r in records if not r.get("skirmish")]
    out = {"n": len(scored), "skirmish": len(records) - len(scored)}
    score = [r.get("score", {}) for r in scored]
    out["trade"] = c.mean([s.get("trade_milli") for s in score])
    out["vs_pred"] = c.mean([s.get("vs_prediction_milli") for s in score])
    out["objective"] = c.mean([s.get("objective_milli") for s in score])
    out["total"] = c.mean([s.get("total_milli") for s in score])
    out["pred_mae"] = c.mean([abs(s["vs_prediction_milli"]) for s in score if "vs_prediction_milli" in s])

    defends = [r for r in scored if r.get("kind") == "defend"]
    resp = [r["response"]["response_ticks"] * c.DEFAULT_TIMESTEP_MS / 1000.0 for r in defends
            if r.get("response", {}).get("response_ticks", -1) >= 0]
    out["resp_med"] = c.median(resp)
    out["resp_p90"] = percentile(resp, 90)
    out["army_dist_med"] = c.median([r["response"]["army_dist_at_start_cells"] for r in defends
                                     if r.get("response", {}).get("army_dist_at_start_cells", -1) >= 0])

    attacks = [r for r in scored if r.get("kind") == "attack"]
    with_def = [r for r in attacks if r.get("tactics", {}).get("defence_points", 0) > 0]
    out["art_first"] = (sum(1 for r in with_def if r["tactics"].get("artillery_first")) / len(with_def)) if with_def else None
    suicide = [r["tactics"]["suicide_index_milli"] / 1000.0 for r in attacks if "suicide_index_milli" in r.get("tactics", {})]
    out["suicide_med"] = c.median(suicide)
    out["suicide_gt2"] = (sum(1 for v in suicide if v > 2.0) / len(suicide)) if suicide else None

    gaps = []
    for r in scored:
        seen, truth = r.get("seen", {}).get("start"), r.get("truth", {}).get("start")
        if seen and truth:
            gaps.append(truth.get("enemy_unit_value", 0) + truth.get("enemy_defence_value", 0)
                        - seen.get("enemy_unit_value", 0) - seen.get("enemy_defence_value", 0))
    out["truth_gap"] = c.mean(gaps)
    return out


def build(data: dict[str, list[dict]]) -> dict:
    groups = collections.defaultdict(list)
    for r in data.get("engagements", []):
        if r.get("record") == "engagement":
            groups[(r.get("bot_type", ""), r.get("personality", ""), r.get("kind", ""))].append(r)
    rows = []
    for (bot, pers, kind), recs in sorted(groups.items()):
        row = {"bot_type": bot, "personality": pers, "kind": kind}
        row.update(summarise(recs))
        rows.append(row)
    postures = [r for r in data.get("engagements", []) if r.get("record") == "posture"]
    return {"groups": rows, "postures": len(postures)}


COLS = ["n", "skirmish", "trade", "vs_pred", "objective", "total", "resp_med", "resp_p90", "army_dist_med", "art_first",
        "suicide_med", "suicide_gt2", "pred_mae", "truth_gap"]
INT_COLS = {"trade", "vs_pred", "objective", "total", "pred_mae", "truth_gap", "army_dist_med"}


def render(result: dict) -> str:
    rows = [["bot", "personality", "kind"] + COLS]
    for g in result["groups"]:
        rows.append([g["bot_type"], g["personality"], g["kind"]] + [c.fmt(g[k], 0 if k in INT_COLS else 2) for k in COLS])
    return c.table(rows) + f"\n\nposture records: {result['postures']}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dirs", nargs="+", type=pathlib.Path)
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    args = ap.parse_args(argv)
    result = build(c.load(args.dirs))
    if not result["groups"]:
        print("no engagement records found", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
