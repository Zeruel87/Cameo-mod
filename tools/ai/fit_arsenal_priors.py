"""fit_arsenal_priors — the offline half of the bot's learning (CA-1b / OM / LG of AI_DEEP_RESEARCH.md).

Reads A/B batch directories (each a `run_ai_match_batch.py --support-dir`, holding `Logs/`) and fits:

1. **Per-enemy-faction profiles (DESIGN.md §19.2, "one profile per enemy faction")**: for every
   (own faction, enemy faction) pair and every own unit type, the value it destroyed per value it
   lost, pooled over all matches and SHRUNK toward an even trade (1.0) until it has enough data —
   a type seen in one skirmish must not dominate. This is "what is effective against that faction".
2. **Visibility factor per game phase**: how much of the enemy's ACTUAL army (its own
   `stats_timeline`) the bot REMEMBERED (situation log), median per 6000-tick phase — the fog
   correction the combat predictor needs (AI_DEEP_RESEARCH.md §2.3).
3. **Elo per bot variant** (AI_DEEP_RESEARCH.md §13 item 11): every match updates the two players'
   ratings in time order; a variant is the batch directory name without its trailing `_N` plus the
   bot type, so `ab_r7_active_1` and `ab_r7_active_2` pool as `ab_r7_active/hard`.

    python tools/ai/fit_arsenal_priors.py <batch-dir> [...] [--write mods/cameo/ai/learned/arsenal_priors.yaml]

Without --write it prints a report. The yaml is a committed, reviewed data file read at match start
(AI_ARCHITECTURE.md §6.1 tier 4); no game code reads it yet.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import statistics
import sys

PHASE_TICKS = 6000
SHRINK_VALUE = 5000  # value of "even trade" pseudo-evidence mixed into every type's ratio
ELO_K = 24
ELO_START = 1500


def read_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


# Reference bots are the same program in every batch: pool them under their bot type, so every
# candidate variant is rated against one anchor.
REFERENCE_BOTS = {"classic", "classic_hard"}


def variant_of(batch_dir: pathlib.Path, bot_type: str) -> str:
    if bot_type in REFERENCE_BOTS:
        return bot_type
    return f"{re.sub(r'_\d+$', '', batch_dir.name)}/{bot_type}"


def shrunk_ratio(killed: float, lost: float, prior: float = SHRINK_VALUE) -> float:
    """Value destroyed per value lost, pulled toward 1.0 by `prior` of pseudo-evidence on both sides."""
    return (killed + prior) / (lost + prior)


def expected(a: float, b: float) -> float:
    return 1 / (1 + 10 ** ((b - a) / 400))


def fit(batch_dirs: list[pathlib.Path]) -> dict:
    trades: dict[tuple[str, str], dict[str, list[int]]] = {}
    visibility: dict[int, list[float]] = {}
    matches = []

    for d in batch_dirs:
        records = read_jsonl(d / "Logs" / "cameo-ai-matches.jsonl")
        situations = read_jsonl(d / "Logs" / "cameo-ai-situations.jsonl")
        by_game: dict[str, list[dict]] = {}
        for r in records:
            by_game.setdefault(r.get("game_uid", ""), []).append(r)

        for uid, players in by_game.items():
            if len(players) != 2:
                continue
            a, b = players
            matches.append((a.get("recorded_utc", ""), variant_of(d, a["player"]["bot_type"]), a["player"]["outcome"],
                            variant_of(d, b["player"]["bot_type"]), b["player"]["outcome"]))

            for me, foe in ((a, b), (b, a)):
                key = (me["player"]["faction"], foe["player"]["faction"])
                per_type = trades.setdefault(key, {})
                for e in me.get("arsenal") or []:
                    t = per_type.setdefault(e["type"], [0, 0, 0])
                    t[0] += e.get("killed_value", 0)
                    t[1] += e.get("lost_value", 0)
                    t[2] += e.get("created", 0)

                # Visibility: what `me` remembered of `foe`'s army vs what `foe` actually had.
                stats = foe.get("stats") or {}
                fields = (stats.get("stats_timeline_fields") or "").split(",")
                actual = {row[0]: dict(zip(fields, row)).get("army_value", 0) for row in stats.get("stats_timeline") or []}
                for s in situations:
                    if s.get("game_uid") != uid or s.get("player") != me["player"]["name"] or not s.get("enemies"):
                        continue
                    tick = (s["tick"] // 750) * 750
                    act = actual.get(tick)
                    if act and act >= 2000:
                        seen = s["enemies"][0].get("army_value", 0)
                        visibility.setdefault(min(tick // PHASE_TICKS, 6), []).append(min(seen / act, 1.0))

    ratings: dict[str, float] = {}
    for _, va, oa, vb, ob in sorted(matches):
        ra, rb = ratings.setdefault(va, ELO_START), ratings.setdefault(vb, ELO_START)
        score = 1.0 if oa == "won" and ob != "won" else 0.0 if ob == "won" and oa != "won" else 0.5
        ea = expected(ra, rb)
        ratings[va] = ra + ELO_K * (score - ea)
        ratings[vb] = rb + ELO_K * ((1 - score) - (1 - ea))

    return {"trades": trades, "visibility": visibility, "ratings": ratings, "matches": len(matches)}


def report(result: dict, top: int) -> str:
    out = [f"{result['matches']} matches"]
    out.append("\n## Visibility (remembered / actual enemy army, median by phase)")
    for phase in sorted(result["visibility"]):
        v = result["visibility"][phase]
        out.append(f"- ticks {phase * PHASE_TICKS}-{phase * PHASE_TICKS + PHASE_TICKS - 1}: {statistics.median(v):.2f} (n={len(v)})")
    out.append("\n## Elo by variant")
    for name, r in sorted(result["ratings"].items(), key=lambda kv: -kv[1]):
        out.append(f"- {name}: {r:.0f}")
    for (mine, theirs), per_type in sorted(result["trades"].items()):
        out.append(f"\n## {mine} vs {theirs}: best and worst trading types (shrunk ratio, killed/lost value, built)")
        ranked = sorted(per_type.items(), key=lambda kv: -shrunk_ratio(kv[1][0], kv[1][1]))
        for t, (k, l, c) in ranked[:top] + [("…", (0, 0, 0))] + ranked[-top:]:
            out.append("- …" if t == "…" else f"- {t}: {shrunk_ratio(k, l):.2f} ({k}/{l}, {c} built)")
    return "\n".join(out)


def to_yaml(result: dict) -> str:
    lines = ["# GENERATED by tools/ai/fit_arsenal_priors.py — do not edit by hand; regenerate and review.",
             "# Offline priors (AI_ARCHITECTURE.md §6.1 tier 4, DESIGN.md §19.2): read at match start, frozen.",
             f"# {result['matches']} matches.", "BotArsenalPriors:"]
    lines.append("\tVisibilityPercentByPhase: " + ", ".join(
        str(round(100 * statistics.median(result["visibility"][p]))) for p in sorted(result["visibility"])))
    for (mine, theirs), per_type in sorted(result["trades"].items()):
        lines.append(f"\tTradePercent@{mine}__vs__{theirs}:")
        for t, (k, l, _) in sorted(per_type.items()):
            lines.append(f"\t\t{t}: {round(100 * shrunk_ratio(k, l))}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("batch_dirs", nargs="+", type=pathlib.Path)
    ap.add_argument("--write", type=pathlib.Path, help="write the priors yaml here")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    result = fit([d for d in args.batch_dirs if d.is_dir()])
    print(report(result, args.top))
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(to_yaml(result), encoding="utf-8", newline="\n")
        print(f"\nwrote {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
