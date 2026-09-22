#!/usr/bin/env python3
"""Aggregate the record-only AI match log into per-matchup outcome tables.

Reads the JSONL written by AiMatchLogWriter (schema 1) and reports, per
(bot faction x personality x enemy faction), how often that combination won.
This is the OFFLINE half of the learning loop: the game never reads this
output. Nothing here adjusts the bots; a human reviews the table and decides.

Deliberate restrictions, because a plausible-looking number is worse than no
number:

  * only 1v1 records are aggregated into the matchup table (exactly one
    opponent, no allies) - a 2v2 loss says nothing about which matchup lost;
  * records with outcome "undecided" are dropped;
  * records shorter than --min-ticks are dropped (a match that ended before
    the bots did anything carries no signal);
  * mixed difficulty tiers and mixed handicaps are NOT pooled - they are
    separate rows, since both are cheat axes;
  * rows below --min-samples are reported but never marked significant, and
    --only-significant hides them entirely.

Usage:
    python tools/ai/aggregate_ai_matches.py [LOG ...] [options]

With no LOG argument the default support-directory path is used.

Exit codes: 0 = report produced, 2 = no usable records, 1 = bad input.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA = 1

# A record must have these top-level keys to be usable at all.
REQUIRED_TOP = ("schema", "record_id", "duration_ticks", "player", "stats", "opponents", "allies")
REQUIRED_PLAYER = ("faction", "bot_type", "handicap", "outcome", "personality")
REQUIRED_OPPONENT = ("faction", "bot_type", "handicap", "outcome")


def default_log_paths() -> list[Path]:
    """Mirror Platform.SupportDir for the common cases; used only as a default."""
    candidates: list[Path] = []
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "OpenRA" / "Logs" / "cameo-ai-matches.jsonl")
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            candidates.append(Path(userprofile) / "Documents" / "OpenRA" / "Logs" / "cameo-ai-matches.jsonl")
    else:
        home = Path.home()
        candidates.append(home / ".config" / "openra" / "Logs" / "cameo-ai-matches.jsonl")
        candidates.append(home / "Library" / "Application Support" / "OpenRA" / "Logs" / "cameo-ai-matches.jsonl")
    return candidates


class Skips:
    def __init__(self) -> None:
        self.counts: dict[str, int] = defaultdict(int)

    def add(self, reason: str) -> None:
        self.counts[reason] += 1

    def total(self) -> int:
        return sum(self.counts.values())


def load_records(paths: list[Path], skips: Skips) -> list[dict]:
    """Parse JSONL, dropping malformed lines and duplicate record_ids."""
    records: list[dict] = []
    seen: set[str] = set()
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            skips.add(f"missing file {path}")
            continue
        except OSError as e:
            skips.add(f"unreadable file {path}: {e}")
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skips.add("malformed json line")
                continue
            if not isinstance(record, dict):
                skips.add("line is not an object")
                continue
            if record.get("schema") != SCHEMA:
                skips.add(f"unsupported schema {record.get('schema')!r}")
                continue
            if any(k not in record for k in REQUIRED_TOP):
                skips.add("missing required field")
                continue
            player = record["player"]
            if not isinstance(player, dict) or any(k not in player for k in REQUIRED_PLAYER):
                skips.add("missing required player field")
                continue
            record_id = record["record_id"]
            if not isinstance(record_id, str) or not record_id:
                skips.add("missing record_id")
                continue
            # The writer is append-only and may retry, so the same match can appear twice.
            if record_id in seen:
                skips.add("duplicate record_id")
                continue
            seen.add(record_id)
            record["_source"] = f"{path}:{line_number}"
            records.append(record)
    return records


def wilson_low(wins: int, n: int, z: float = 1.96) -> float:
    """Lower bound of the Wilson score interval - a pessimistic win rate.

    Ranking by raw win rate makes 1/1 = 100% outrank 40/50 = 80%; the lower
    bound is what makes a small sample rank low on its own.
    """
    if n == 0:
        return 0.0
    p = wins / n
    denominator = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return max(0.0, (centre - margin) / denominator)


class Cell:
    __slots__ = ("matches", "wins", "losses", "kills_cost", "deaths_cost", "duration_ticks", "switches")

    def __init__(self) -> None:
        self.matches = 0
        self.wins = 0
        self.losses = 0
        self.kills_cost = 0
        self.deaths_cost = 0
        self.duration_ticks = 0
        self.switches = 0

    def add(self, record: dict) -> None:
        stats = record.get("stats") or {}
        self.matches += 1
        if record["player"]["outcome"] == "won":
            self.wins += 1
        else:
            self.losses += 1
        self.kills_cost += int(stats.get("kills_cost") or 0)
        self.deaths_cost += int(stats.get("deaths_cost") or 0)
        self.duration_ticks += int(record.get("duration_ticks") or 0)
        self.switches += int(record["player"].get("personality_switches") or 0)

    @property
    def win_rate(self) -> float:
        return self.wins / self.matches if self.matches else 0.0

    @property
    def trade(self) -> float:
        """Value destroyed per value lost. >1 means the bot traded up."""
        return self.kills_cost / self.deaths_cost if self.deaths_cost else float("inf")


def usable(record: dict, min_ticks: int, skips: Skips) -> bool:
    outcome = record["player"]["outcome"]
    if outcome not in ("won", "lost"):
        skips.add(f"outcome {outcome}")
        return False
    if int(record.get("duration_ticks") or 0) < min_ticks:
        skips.add(f"shorter than {min_ticks} ticks")
        return False
    if not record["player"].get("personality"):
        skips.add("no personality recorded")
        return False
    return True


def is_duel(record: dict) -> bool:
    opponents = record.get("opponents") or []
    allies = record.get("allies") or []
    if len(opponents) != 1 or allies:
        return False
    opponent = opponents[0]
    return isinstance(opponent, dict) and all(k in opponent for k in REQUIRED_OPPONENT)


def aggregate(records: list[dict], min_ticks: int, skips: Skips):
    """Return (matchup cells, personality cells, team-game count)."""
    matchups: dict[tuple, Cell] = defaultdict(Cell)
    personalities: dict[tuple, Cell] = defaultdict(Cell)
    team_games = 0

    for record in records:
        if not usable(record, min_ticks, skips):
            continue
        player = record["player"]
        # The personality table does not need a clean duel, only a clean outcome.
        personalities[(player["faction"], player["personality"], player["bot_type"], int(player.get("handicap") or 0))].add(record)
        if not is_duel(record):
            team_games += 1
            skips.add("not a 1v1 (matchup table only)")
            continue
        opponent = record["opponents"][0]
        key = (
            player["faction"],
            player["personality"],
            opponent["faction"],
            player["bot_type"],
            opponent["bot_type"],
            int(player.get("handicap") or 0),
            int(opponent.get("handicap") or 0),
        )
        matchups[key].add(record)

    return matchups, personalities, team_games


def fmt_rate(cell: Cell) -> str:
    return f"{100.0 * cell.win_rate:5.1f}%"


def fmt_trade(cell: Cell) -> str:
    return "  inf" if cell.trade == float("inf") else f"{cell.trade:5.2f}"


def print_matchups(matchups: dict[tuple, Cell], min_samples: int, only_significant: bool, top: int) -> None:
    print("== matchup table: bot faction x personality vs enemy faction (1v1 only) ==")
    if not matchups:
        print("  (no 1v1 records)")
        return
    rows = sorted(
        matchups.items(),
        key=lambda kv: (-wilson_low(kv[1].wins, kv[1].matches), kv[0]),
    )
    print(f"  {'faction':<28} {'personality':<12} {'vs faction':<28} {'tier':<10} {'hcp':>7} {'n':>5} {'win':>7} {'wilson':>7} {'trade':>7} {'sig':>4}")
    shown = 0
    for key, cell in rows:
        faction, personality, enemy, tier, enemy_tier, handicap, enemy_handicap = key
        significant = cell.matches >= min_samples
        if only_significant and not significant:
            continue
        if top and shown >= top:
            break
        tiers = tier if tier == enemy_tier else f"{tier}/{enemy_tier}"
        handicaps = f"{handicap}/{enemy_handicap}"
        print(
            f"  {faction:<28} {personality:<12} {enemy:<28} {tiers:<10} {handicaps:>7} "
            f"{cell.matches:>5} {fmt_rate(cell):>7} {100.0 * wilson_low(cell.wins, cell.matches):6.1f}% "
            f"{fmt_trade(cell):>7} {'yes' if significant else '-':>4}"
        )
        shown += 1
    hidden = len(rows) - shown
    if hidden > 0:
        print(f"  ... {hidden} further row(s) not shown")


def print_personalities(personalities: dict[tuple, Cell], min_samples: int) -> None:
    print()
    print("== personality table: per faction, all opponent counts ==")
    if not personalities:
        print("  (no records)")
        return
    by_faction: dict[tuple[str, str, int], list[tuple[str, Cell]]] = defaultdict(list)
    for (faction, personality, tier, handicap), cell in personalities.items():
        by_faction[(faction, tier, handicap)].append((personality, cell))

    for (faction, tier, handicap), entries in sorted(by_faction.items()):
        total = sum(c.matches for _, c in entries)
        print(f"  {faction} [{tier}, handicap {handicap}] - {total} record(s)")
        entries.sort(key=lambda pc: (-wilson_low(pc[1].wins, pc[1].matches), pc[0]))
        for personality, cell in entries:
            flag = "" if cell.matches >= min_samples else "   (below sample threshold)"
            switches = cell.switches / cell.matches if cell.matches else 0.0
            print(
                f"    {personality:<12} n={cell.matches:<5} win={fmt_rate(cell)} "
                f"wilson={100.0 * wilson_low(cell.wins, cell.matches):5.1f}% trade={fmt_trade(cell)} "
                f"switches/match={switches:4.1f}{flag}"
            )
        # Compare only candidates that individually have enough samples; a single
        # under-sampled personality must not suppress advice about the others.
        ranked = [pc for pc in entries if pc[1].matches >= min_samples]
        if len(ranked) > 1:
            best, worst = ranked[0], ranked[-1]
            gap = best[1].win_rate - worst[1].win_rate
            if gap >= 0.15:
                print(
                    f"    -> '{worst[0]}' trails '{best[0]}' by {100.0 * gap:.1f} points "
                    f"over {worst[1].matches} and {best[1].matches} matches; candidate for retuning"
                )


def to_json(matchups: dict[tuple, Cell], personalities: dict[tuple, Cell], min_samples: int) -> dict:
    def cell_json(cell: Cell) -> dict:
        return {
            "matches": cell.matches,
            "wins": cell.wins,
            "losses": cell.losses,
            "win_rate": round(cell.win_rate, 4),
            "wilson_low": round(wilson_low(cell.wins, cell.matches), 4),
            "kills_cost": cell.kills_cost,
            "deaths_cost": cell.deaths_cost,
            "trade": None if cell.trade == float("inf") else round(cell.trade, 4),
            "mean_duration_ticks": cell.duration_ticks // cell.matches if cell.matches else 0,
            "personality_switches": cell.switches,
            "significant": cell.matches >= min_samples,
        }

    return {
        "schema": SCHEMA,
        "min_samples": min_samples,
        "matchups": [
            {
                "faction": key[0],
                "personality": key[1],
                "enemy_faction": key[2],
                "bot_type": key[3],
                "enemy_bot_type": key[4],
                "handicap": key[5],
                "enemy_handicap": key[6],
                **cell_json(cell),
            }
            for key, cell in sorted(matchups.items())
        ],
        "personalities": [
            {
                "faction": key[0],
                "personality": key[1],
                "bot_type": key[2],
                "handicap": key[3],
                **cell_json(cell),
            }
            for key, cell in sorted(personalities.items())
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("logs", nargs="*", type=Path, help="JSONL log files (default: support directory)")
    parser.add_argument("--min-samples", type=int, default=20, help="matches needed before a row counts as significant (default 20)")
    parser.add_argument("--min-ticks", type=int, default=2400, help="drop matches shorter than this many ticks (default 2400 = 1 min at 40ms)")
    parser.add_argument("--only-significant", action="store_true", help="hide rows below the sample threshold")
    parser.add_argument("--top", type=int, default=40, help="limit matchup rows printed (0 = all)")
    parser.add_argument("--json", type=Path, help="also write the aggregate as JSON to this path")
    args = parser.parse_args(argv)

    if args.min_samples < 1 or args.min_ticks < 0:
        print("error: --min-samples must be >= 1 and --min-ticks >= 0", file=sys.stderr)
        return 1

    paths = args.logs or [p for p in default_log_paths() if p.exists()] or default_log_paths()[:1]
    skips = Skips()
    records = load_records(list(paths), skips)

    print(f"read {len(records)} record(s) from {len(paths)} file(s): {', '.join(str(p) for p in paths)}")
    if not records:
        for reason, count in sorted(skips.counts.items(), key=lambda kv: -kv[1]):
            print(f"  skipped {count}: {reason}")
        print("no usable records - run some AI matches first")
        return 2

    matchups, personalities, team_games = aggregate(records, args.min_ticks, skips)
    print_matchups(matchups, args.min_samples, args.only_significant, args.top)
    print_personalities(personalities, args.min_samples)

    print()
    print(f"skipped {skips.total()} line(s)/record(s):")
    for reason, count in sorted(skips.counts.items(), key=lambda kv: -kv[1]):
        print(f"  {count:>6}  {reason}")
    if team_games:
        print(f"note: {team_games} team-game record(s) counted in the personality table only")
    print(f"note: rows below {args.min_samples} matches are reported but never treated as evidence")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(to_json(matchups, personalities, args.min_samples), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
