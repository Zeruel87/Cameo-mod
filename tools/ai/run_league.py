#!/usr/bin/env python3
"""League runner for the Cameo bot program — AI_DEEP_RESEARCH §6.2 (LG),
AI_ARCHITECTURE §12.10.

A candidate must not land on one pairing; it lands on a LEAGUE SCORE pooled
across opponents, maps and factions. This tool expands a league spec into
one run_ai_match_batch.py invocation per cell and merges the cells into
`league_summary.json`.

League spec (JSON):

    {
      "candidate": "hard",
      "members": ["classic", "exploit_rush", "exploit_turtle", "exploit_guerrilla"],
      "maps": ["mods/cameo/maps/ai_duel_nuclear_winter"],
      "factions": ["td_gdi"],
      "repeats": 4,
      "swap_bots": true,
      "time_limit": 3,
      "team_size": 1
    }

With `"team_size": 2` every side is a homogeneous duo (2v2): the cells pass
`--team-size 2 --bot-a <candidate>,<candidate> --bot-b <member>,<member>` to
the batch runner on a 4-player doubles map (consecutive Multi pairs are the
teams), and aggregation dedupes to one datapoint per match — a team won iff
any candidate-side record reads "won".

`members` are the opposing bot types. The classic omniscient reference is
the standing anchor; the `exploit_*` types are the full genericbot stack
pinned to one personality pole (BotPersonalityController.PinnedPersonalities)
whose only job is exposing candidate flaws. "Past masters" is deliberately
NOT a git/binary pin: a master is frozen as a hidden bot TYPE so it replays
against any build — classic is the first such freeze; future freezes follow
the same mechanism when a stack is worth keeping as a regression wall.

Usage:
    python tools/ai/run_league.py --spec tools/ai/league_standard.json \
        --league-dir C:/tmp/league-01
    python tools/ai/run_league.py --spec ... --dry-run
    python tools/ai/run_league.py --league-dir C:/tmp/league-01 --aggregate-only
"""

import argparse
import json
import math
import pathlib
import subprocess
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
BATCH_RUNNER = REPO_ROOT / "tools" / "ai" / "run_ai_match_batch.py"


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def wilson(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Same interval ab_summary.py reports — keep the two tools consistent."""
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (centre - margin) / denom), min(1.0, (centre + margin) / denom))


def load_spec(path: pathlib.Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    for key in ("candidate", "members", "maps"):
        if key not in spec or not spec[key]:
            raise ValueError(f"spec needs a non-empty '{key}'")
    spec.setdefault("factions", ["td_gdi"])
    spec.setdefault("repeats", 4)
    spec.setdefault("swap_bots", True)
    spec.setdefault("time_limit", 3)
    spec.setdefault("team_size", 1)
    if spec["team_size"] < 1 or spec["team_size"] > 8:
        raise ValueError(f"spec 'team_size' must be 1-8, got {spec['team_size']}")
    for m in spec["maps"]:
        resolved = pathlib.Path(m) if pathlib.Path(m).is_absolute() else REPO_ROOT / m
        if not resolved.exists():
            raise ValueError(f"spec map does not exist: {m}")
    return spec


def league_cells(spec: dict) -> list[dict]:
    cells = []
    for member in spec["members"]:
        for map_path in spec["maps"]:
            for faction in spec["factions"]:
                cells.append({
                    "member": member,
                    "map": str(map_path),
                    "faction": faction,
                })
    return cells


def cell_summary(cell_dir: pathlib.Path) -> dict | None:
    summary_path = cell_dir / "batch_summary.json"
    if not summary_path.is_file():
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return {
        "completed": summary.get("completed", 0),
        "stalled": summary.get("stalled", 0),
        "timed_out": summary.get("timed_out", 0),
        "died": summary.get("died", 0),
        "norecord": summary.get("norecord", 0),
        "new_exceptions": summary.get("new_exceptions") or [],
        # LC7: a batch that aborted on fingerprint drift says so here, so the
        # league aggregate surfaces "arms changed mid-cell" instead of the
        # cell just reading as quietly incomplete.
        "aborted": summary.get("aborted"),
    }


def merge_cell(cell_dir: pathlib.Path, cell: dict, candidate: str, member: str, acc: dict,
               team_size: int = 1) -> None:
    """Fold one cell into the league accumulators.

    Reads `batch_results.jsonl` bot_outcomes rows (one per player per match,
    keyed by `record_id` = game_uid|slot) and keeps only candidate-perspective
    rows — the mirror member rows describe the same matches, so taking both
    would double-count. `spawn` on the row is already the candidate's physical
    spawn index (slot-derived, #619).

    team_size=2 (2v2): the same rows carry the full `allies`/`opponents`
    lists. Each match (game_uid = `record_id.rsplit("|",1)[0]`) counts ONCE:
    the candidate team won iff any of its member records reads "won" (an
    early-dead teammate still records "lost"), and the spawn axis is the
    team's sorted member-spawn pair ("0,1").
    """
    data = cell_summary(cell_dir)
    if data is None:
        acc["cells_missing"].append(cell["name"])
        return

    acc["completed"] += data["completed"]
    acc["stalled"] += data["stalled"]
    acc["timed_out"] += data["timed_out"]
    acc["died"] += data["died"]
    acc["norecord"] += data["norecord"]
    acc["exceptions"] += data["new_exceptions"]
    if data["aborted"]:
        acc["cells_aborted"].append(f"{cell['name']} ({data['aborted']})")

    results_path = cell_dir / "batch_results.jsonl"
    if not results_path.is_file():
        acc["cells_missing"].append(cell["name"] + " (no batch_results.jsonl)")
        return

    if team_size >= 2:
        # One datapoint per match uid: collect the candidate-side rows of each
        # match (both member rows qualify — the duo is homogeneous) and take
        # the team verdict "any member won".
        match_rows: dict[str, list[dict]] = {}
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            match = json.loads(line)
            for row in match.get("bot_outcomes") or []:
                if row.get("bot_type") != candidate:
                    continue
                opponents = [o.get("bot_type") for o in row.get("opponents") or []]
                if member not in opponents:
                    continue
                uid = str(row.get("record_id") or "").rsplit("|", 1)[0]
                match_rows.setdefault(uid, []).append(row)
        for uid, rows in match_rows.items():
            won = any(r.get("outcome") == "won" for r in rows)
            acc["won" if won else "lost"] += 1
            per = acc["per_member"].setdefault(member, {"won": 0, "lost": 0, "spawn": {}})
            per["won" if won else "lost"] += 1
            spawn = ",".join(sorted(str(r.get("spawn")) for r in rows if r.get("spawn") is not None))
            if spawn:
                for table in (acc["spawn"], per["spawn"]):
                    slot = table.setdefault(spawn, [0, 0])
                    slot[0 if won else 1] += 1
        return

    seen = set()
    for line in results_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        match = json.loads(line)
        for row in match.get("bot_outcomes") or []:
            if row.get("bot_type") != candidate or (row.get("opponent") or {}).get("bot_type") != member:
                continue
            record_id = row.get("record_id")
            if record_id in seen:
                continue
            seen.add(record_id)
            won = row.get("outcome") == "won"
            acc["won" if won else "lost"] += 1
            spawn = row.get("spawn")
            per = acc["per_member"].setdefault(member, {"won": 0, "lost": 0, "spawn": {}})
            per["won" if won else "lost"] += 1
            if spawn is not None:
                for table in (acc["spawn"], per["spawn"]):
                    slot = table.setdefault(str(spawn), [0, 0])
                    slot[0 if won else 1] += 1


def aggregate(league_dir: pathlib.Path, spec: dict) -> dict:
    acc = {
        "won": 0,
        "lost": 0,
        "spawn": {},
        "per_member": {},
        "completed": 0,
        "stalled": 0,
        "timed_out": 0,
        "died": 0,
        "norecord": 0,
        "exceptions": [],
        "cells_missing": [],
        "cells_aborted": [],
    }
    for cell in league_cells(spec):
        name = f"{spec['candidate']}_vs_{cell['member']}__{cell['faction']}__{pathlib.Path(cell['map']).stem}"
        cell["name"] = name
        merge_cell(league_dir / name, cell, spec["candidate"], cell["member"], acc,
                   team_size=spec.get("team_size", 1))

    total = acc["won"] + acc["lost"]
    lo, hi = wilson(acc["won"], total)
    per_member = {}
    for member, m in acc["per_member"].items():
        n = m["won"] + m["lost"]
        mlo, mhi = wilson(m["won"], n)
        per_member[member] = {
            "won": m["won"], "lost": m["lost"], "n": n,
            "winrate": round(m["won"] / n, 4) if n else None,
            "wilson95": [round(mlo, 4), round(mhi, 4)],
            "spawn": m["spawn"],
        }
    return {
        "candidate": spec["candidate"],
        "members": spec["members"],
        "cells": len(league_cells(spec)),
        "decided_matches": total,
        "won": acc["won"],
        "lost": acc["lost"],
        "league_score": round(acc["won"] / total, 4) if total else None,
        "league_wilson95": [round(lo, 4), round(hi, 4)],
        "spawn": acc["spawn"],
        "per_member": per_member,
        "completed": acc["completed"],
        "stalled": acc["stalled"],
        "timed_out": acc["timed_out"],
        "died": acc["died"],
        "norecord": acc["norecord"],
        "exceptions": acc["exceptions"],
        "cells_missing": acc["cells_missing"],
        "cells_aborted": acc["cells_aborted"],
    }


def print_summary(summary: dict) -> None:
    print(f"\nleague score for `{summary['candidate']}`: "
          f"{summary['won']}-{summary['lost']} decided "
          f"({summary['league_score']}, wilson95 {summary['league_wilson95']})")
    spawn = summary.get("spawn") or {}
    if spawn:
        print("  spawns: " + ", ".join(f"{s}: {w}-{l}" for s, (w, l) in sorted(spawn.items())))
    for member, m in summary["per_member"].items():
        print(f"  vs {member}: {m['won']}-{m['lost']} "
              f"(wr {m['winrate']}, wilson95 {m['wilson95']})")
    if summary["cells_missing"]:
        print(f"  MISSING CELLS: {summary['cells_missing']}")
    if summary["cells_aborted"]:
        print(f"  ABORTED CELLS: {summary['cells_aborted']}")
    bad = {k: summary[k] for k in ("stalled", "timed_out", "died", "norecord") if summary[k]}
    if bad or summary["exceptions"]:
        print(f"  anomalies: {bad or '{}'} exceptions={summary['exceptions'] or 'none'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", type=pathlib.Path, required=False,
                        help="league spec JSON (required unless --aggregate-only)")
    parser.add_argument("--league-dir", type=pathlib.Path, required=True,
                        help="directory that holds one subdirectory per league cell")
    parser.add_argument("--repeats", type=int, default=None, help="override spec repeats")
    parser.add_argument("--time-limit", type=int, default=None, choices=sorted({3, 6}),
                        help="override spec time_limit")
    parser.add_argument("--stall-timeout", type=int, default=400)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--aggregate-only", action="store_true",
                        help="skip launching; merge existing cell results only")
    args = parser.parse_args()

    if args.aggregate_only:
        spec_path = args.spec or (args.league_dir / "league_spec.json")
        if not spec_path.is_file():
            return fail(f"aggregate-only needs the spec at {spec_path} (or --spec)")
        spec = load_spec(spec_path)
        summary = aggregate(args.league_dir, spec)
        print_summary(summary)
        (args.league_dir / "league_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8")
        return 0

    if not args.spec:
        return fail("--spec is required for a league run")
    spec = load_spec(args.spec)
    if args.repeats:
        spec["repeats"] = args.repeats
    if args.time_limit:
        spec["time_limit"] = args.time_limit

    league_dir = args.league_dir
    league_dir.mkdir(parents=True, exist_ok=True)
    (league_dir / "league_spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")

    cells = league_cells(spec)
    for cell in cells:
        cell["name"] = (
            f"{spec['candidate']}_vs_{cell['member']}__{cell['faction']}__"
            f"{pathlib.Path(cell['map']).stem}")

    print(f"league: {spec['candidate']} vs {len(spec['members'])} members x "
          f"{len(spec['maps'])} map(s) x {len(spec['factions'])} faction(s) = {len(cells)} cells, "
          f"{spec['repeats']} matches each"
          + (" (swapped)" if spec["swap_bots"] else ""))
    if args.dry_run:
        for cell in cells:
            print(f"  cell {cell['name']}: {spec['candidate']} vs {cell['member']} "
                  f"on {cell['map']} as {cell['faction']}")
        return 0

    for index, cell in enumerate(cells, 1):
        cell_dir = league_dir / cell["name"]
        team_size = spec.get("team_size", 1)
        cmd = [
            sys.executable, str(BATCH_RUNNER),
            "--bot-a", ",".join([spec["candidate"]] * team_size),
            "--bot-b", ",".join([cell["member"]] * team_size),
            "--map", str(REPO_ROOT / cell["map"]) if not pathlib.Path(cell["map"]).is_absolute() else cell["map"],
            "--factions", cell["faction"],
            "--repeats", str(spec["repeats"]),
            "--time-limit", str(spec["time_limit"]),
            "--support-dir", str(cell_dir),
            "--stall-timeout", str(args.stall_timeout),
        ]
        if team_size >= 2:
            cmd += ["--team-size", str(team_size)]
        if spec["swap_bots"]:
            cmd.append("--swap-bots")
        print(f"[{index}/{len(cells)}] {cell['name']} ...", flush=True)
        proc = subprocess.run(cmd, cwd=REPO_ROOT)
        if proc.returncode not in (0,):
            print(f"  cell returned {proc.returncode} — continuing; aggregation surfaces anomalies")

    summary = aggregate(league_dir, spec)
    print_summary(summary)
    (league_dir / "league_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"league summary written to {league_dir / 'league_summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
