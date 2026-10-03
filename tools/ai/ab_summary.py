#!/usr/bin/env python3
"""Summarise bot A/B matches: wins per BOT TYPE, with the uncertainty that the sample size allows.

Reads the cameo-ai-matches.jsonl files written by AiMatchLogWriter (one record per bot per match;
tools/ai/run_ai_match_batch.py collects them in <support-dir>/Logs/). The acceptance test
(AI_ARCHITECTURE §0a, maintainer 2026-09-28) is a fog-blind candidate bot BEATING the omniscient
`classic` bot, so the question is "how often does bot type X win", not a faction/personality table.

Usage:
    python tools/ai/ab_summary.py <support-dir-or-jsonl> [...] [--timestep N]

A match whose two records both say "lost" is a timeout draw (the fixture's locked time limit).
`--timestep N` keeps only records written at that engine timestep — the speed-era separator:
the duel fixture ran `insane` (timestep 10) until 2026-09-29 and `maximum` (timestep 1) after,
and a reused support dir holds both populations, which must not be pooled (OrderLatency
differed too: 7 vs 10).
The 95% interval is Wilson's, so 3 wins of 3 reads as "somewhere between 44% and 100%", which is
the honest statement about three games.
"""
import collections
import json
import math
import pathlib
import sys


def wilson(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def records(paths: list[str]):
    for arg in paths:
        p = pathlib.Path(arg)
        files = [p] if p.is_file() else list(p.rglob("cameo-ai-matches.jsonl"))
        for f in files:
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def arm_fingerprints(paths: list[str]):
    """Per-batch fingerprint audit. One 'arm' is one batch_results.jsonl
    (a support dir's batch history). Pre-LC7 files carry no fingerprint
    field; LC7 files carry one per result. A file whose real results span
    more than one fingerprint is a mixed arm — the batch crossed a mid-run
    change and its matches are not one experiment. `fingerprint_drift`
    tombstones are the abort trail, not data, and don't count as mixing."""
    for arg in paths:
        p = pathlib.Path(arg)
        if p.is_file():
            files = [p] if p.name == "batch_results.jsonl" else []
        else:
            files = list(p.rglob("batch_results.jsonl"))
        for f in files:
            arms = collections.defaultdict(lambda: {"results": 0, "drift_only": True})
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                e = arms[r.get("fingerprint")]
                e["results"] += 1
                if r.get("status") != "fingerprint_drift":
                    e["drift_only"] = False
            yield f, arms


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2

    timestep = None
    paths = []
    it = iter(argv)
    for arg in it:
        if arg == "--timestep":
            try:
                timestep = int(next(it))
            except StopIteration:
                print(__doc__)
                return 2
        else:
            paths.append(arg)

    games = collections.defaultdict(list)
    for r in records(paths):
        if timestep is not None and r.get("timestep") != timestep:
            continue
        games[r.get("game_uid")].append(r)

    stats = collections.defaultdict(lambda: {"won": 0, "lost": 0, "draw": 0, "spawn_wins": collections.Counter(), "ticks": []})
    # Pooled spawn-position W/L: the map-asymmetry readout. `spawn` in a record
    # is the lobby slot, not the physical side — `home` (the start cell) is the
    # position. Per-bot "wins by side" stays above; this pools every bot so a
    # side bias shows even when each bot's row is thin.
    side = collections.defaultdict(lambda: {"won": 0, "lost": 0})
    # Watchdog counters (LC5 `ownership`, §19.6 `order_gate`): summed per bot
    # type across the corpus. Absent fields (pre-#695/#699 records, classic)
    # contribute nothing, so the block prints only what the data carries.
    health = collections.defaultdict(lambda: {"own": collections.Counter(), "gate": collections.Counter()})
    for uid, recs in games.items():
        if len(recs) != 2:
            continue
        outcomes = [r["player"]["outcome"] for r in recs]
        draw = all(o != "won" for o in outcomes)
        for r in recs:
            bot = r["player"]["bot_type"]
            s = stats[bot]
            home = r["player"].get("home") or r["player"].get("name", "?")
            if draw:
                s["draw"] += 1
            elif r["player"]["outcome"] == "won":
                s["won"] += 1
                # `spawn` is the lobby choice, 0 for every map-side harness player; the home
                # cell (or, in records older than it, the seat name) is what tells sides apart.
                s["spawn_wins"][home] += 1
                side[home]["won"] += 1
            else:
                s["lost"] += 1
                side[home]["lost"] += 1
            s["ticks"].append(r.get("duration_ticks") or 0)
            own = r.get("ownership")
            if isinstance(own, dict):
                for k, v in own.items():
                    if k != "by_type" and isinstance(v, int):
                        health[bot]["own"][k] += v
            gate = r.get("order_gate")
            if isinstance(gate, dict):
                for k, v in gate.items():
                    if isinstance(v, int):
                        health[bot]["gate"][k] += v

    print(f"{len(games)} match(es)")
    print("| bot type | won | lost | draw | win rate | 95% interval | wins by side | mean length (ticks) |")
    print("|---|--:|--:|--:|--:|---|---|--:|")
    for bot, s in sorted(stats.items()):
        n = s["won"] + s["lost"] + s["draw"]
        lo, hi = wilson(s["won"], n)
        mean = sum(s["ticks"]) // max(1, len(s["ticks"]))
        print(f"| `{bot}` | {s['won']} | {s['lost']} | {s['draw']} | {100 * s['won'] // max(1, n)}% | "
              f"{100 * lo:.0f}–{100 * hi:.0f}% | {dict(s['spawn_wins'])} | {mean} |")

    # The pooled side split answers "is one spawn position favoured" across the
    # whole corpus fed in — thin per-bot rows pool into one number per side.
    decided = sum(v["won"] + v["lost"] for v in side.values())
    if side and decided:
        print(f"spawn split (pooled, {decided} decided): " +
              " | ".join(f"{k}: {v['won']}W-{v['lost']}L" for k, v in sorted(side.items())))
    for bot, h in sorted(health.items()):
        if not h["own"] and not h["gate"]:
            continue
        parts = []
        if h["own"]:
            parts.append("ownership[" + " ".join(f"{k}={v}" for k, v in sorted(h["own"].items())) + "]")
        if h["gate"]:
            parts.append("order_gate[" + " ".join(f"{k}={v}" for k, v in sorted(h["gate"].items())) + "]")
        print(f"watchdogs `{bot}`: " + " ".join(parts))
    mixed = False
    for f, arms in arm_fingerprints(paths):
        fps = sorted(k for k in arms if k) or [None]
        real = [k for k in arms if k and not arms[k]["drift_only"]]
        for fp in fps:
            tag = f"{fp} ({arms[fp]['results']} results)" if fp else "none recorded (pre-LC7)"
            print(f"arm fingerprint {tag}: {f}")
        if len(real) > 1:
            print(f"FAIL: mixed fingerprints within one arm in {f}: "
                  + ", ".join(f"{k} ({arms[k]['results']} results)" for k in real))
            mixed = True
    return 1 if mixed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
