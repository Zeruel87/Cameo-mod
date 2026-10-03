import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
AGGREGATOR = ROOT / "tools" / "ai" / "aggregate_ai_matches.py"


def record(record_id="game|Multi0", outcome="won", duration_ticks=2400, opponents=None):
    return {
        "schema": 1,
        "record_id": record_id,
        "duration_ticks": duration_ticks,
        "player": {
            "faction": "td_gdi",
            "bot_type": "medium",
            "handicap": 0,
            "outcome": outcome,
            "personality": "rush",
            "personality_switches": 0,
        },
        "stats": {"kills_cost": 100, "deaths_cost": 50},
        "opponents": opponents if opponents is not None else [
            {
                "faction": "td_nod",
                "bot_type": "medium",
                "handicap": 0,
                "outcome": "lost",
            }
        ],
        "allies": [],
    }


class AggregateAiMatchesTest(unittest.TestCase):
    def test_skip_counts_and_below_threshold_significance(self):
        valid = record()
        duplicate = record()
        undecided = record("game|Undecided", outcome="undecided")
        short = record("game|Short", duration_ticks=2399)
        team_game = record("game|Team", opponents=[
            {"faction": "td_nod", "bot_type": "medium", "handicap": 0, "outcome": "lost"},
            {"faction": "td_nod", "bot_type": "hard", "handicap": 0, "outcome": "lost"},
        ])
        team_game["player"]["personality"] = "tech"

        lines = [
            json.dumps(valid),
            json.dumps(duplicate),
            "{malformed json",
            json.dumps({**valid, "schema": 3, "record_id": "game|Unsupported"}),
            json.dumps(undecided),
            json.dumps(short),
            json.dumps(team_game),
        ]

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "matches.jsonl"
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(AGGREGATOR),
                    str(log_path),
                    "--min-samples",
                    "2",
                    "--min-ticks",
                    "2400",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("skipped 6 line(s)/record(s):", result.stdout)
        for reason in (
            "duplicate record_id",
            "malformed json line",
            "unsupported schema 3",
            "outcome undecided",
            "shorter than 2400 ticks",
            "not a 1v1 (matchup table only)",
        ):
            self.assertRegex(result.stdout, rf"\s+1\s+{re.escape(reason)}")

        self.assertIn("(below sample threshold)", result.stdout)
        matchup = next(line for line in result.stdout.splitlines() if "td_gdi" in line and "td_nod" in line)
        self.assertTrue(matchup.rstrip().endswith("-"), matchup)

    def test_schema2_episode_table_attributes_deltas_between_boundaries(self):
        """A record with two episodes must split its match stats at the boundary."""
        rec = record(record_id="game|Episodes")
        rec["schema"] = 2
        rec["stats"] = {"kills_cost": 300, "deaths_cost": 120}
        rec["player"]["personality"] = "tech"
        rec["player"]["composition"] = "lategame"
        rec["player"]["episode_timeline"] = [
            {"tick": 0, "personality": "rush", "composition": "opener", "kills_cost": 0, "deaths_cost": 0},
            {"tick": 1000, "personality": "tech", "composition": "lategame", "kills_cost": 200, "deaths_cost": 100},
        ]

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "matches.jsonl"
            log_path.write_text(json.dumps(rec) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(AGGREGATOR), str(log_path), "--min-samples", "2", "--min-ticks", "2400"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("episode table", result.stdout)
        # Episode 0 (rush/opener, ticks 0-1000): kills 200, deaths 100 -> etrade 2.00
        # Episode 1 (tech/lategame, ticks 1000-2400): kills 100, deaths 20 -> etrade 5.00
        opener = next(line for line in result.stdout.splitlines() if "opener" in line)
        lategame = next(line for line in result.stdout.splitlines() if "lategame" in line)
        self.assertIn("rush", opener)
        self.assertIn("2.00", opener)
        self.assertIn("1000", opener)
        self.assertIn("tech", lategame)
        self.assertIn("5.00", lategame)
        self.assertIn("1400", lategame)

    def test_schema1_records_have_no_episode_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "matches.jsonl"
            log_path.write_text(json.dumps(record()) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(AGGREGATOR), str(log_path), "--min-samples", "2", "--min-ticks", "2400"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("(no episode records - schema 1 carries none)", result.stdout)


if __name__ == "__main__":
    unittest.main()
