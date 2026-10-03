"""run_league.py: spec parsing, cell expansion, and league aggregation.

The league score is the landing gate for every CA phase (AI_ARCHITECTURE
§12.10), so its bookkeeping gets unit tests: candidate-perspective rows only
(the mirror row in a match must not double-count), spawn splits preserved,
and missing cells surfaced rather than silently pooled away.
"""
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ai"))

import run_league


def write_cell(cell_dir: pathlib.Path, rows: list[dict], completed: int = 1) -> None:
    cell_dir.mkdir(parents=True, exist_ok=True)
    (cell_dir / "batch_summary.json").write_text(json.dumps({
        "completed": completed, "stalled": 0, "timed_out": 0, "died": 0,
        "new_exceptions": [],
    }), encoding="utf-8")
    matches = {}
    for row in rows:
        matches.setdefault(row["game"], []).append(row)
    with (cell_dir / "batch_results.jsonl").open("w", encoding="utf-8") as fh:
        for game, game_rows in matches.items():
            outcomes = [
                {
                    "record_id": f"{game}|{r['slot']}",
                    "bot_type": r["bot"],
                    "outcome": r["outcome"],
                    "spawn": r["spawn"],
                    "opponent": {"bot_type": r["opp"]},
                }
                for r in game_rows
            ]
            fh.write(json.dumps({"name": game, "bot_outcomes": outcomes}) + "\n")


def candidate_won(game, slot, spawn, member, opp_slot, opp_spawn):
    return [
        {"game": game, "slot": f"Multi{slot}", "bot": "hard", "outcome": "won", "spawn": spawn, "opp": member},
        {"game": game, "slot": f"Multi{opp_slot}", "bot": member, "outcome": "lost", "spawn": opp_spawn, "opp": "hard"},
    ]


class SpecTests(unittest.TestCase):
    def test_requires_candidate_members_maps(self):
        with tempfile.TemporaryDirectory() as td:
            spec = pathlib.Path(td) / "spec.json"
            spec.write_text(json.dumps({"candidate": "hard", "members": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                run_league.load_spec(spec)

    def test_defaults_fill(self):
        with tempfile.TemporaryDirectory() as td:
            map_file = pathlib.Path(td) / "m.oramap"
            map_file.write_text("x", encoding="utf-8")
            spec = pathlib.Path(td) / "spec.json"
            spec.write_text(json.dumps({
                "candidate": "hard", "members": ["classic"], "maps": [str(map_file)],
            }), encoding="utf-8")
            loaded = run_league.load_spec(spec)
            self.assertEqual(loaded["repeats"], 4)
            self.assertTrue(loaded["swap_bots"])

    def test_missing_map_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            spec = pathlib.Path(td) / "spec.json"
            spec.write_text(json.dumps({
                "candidate": "hard", "members": ["classic"],
                "maps": ["mods/cameo/maps/does_not_exist.oramap"],
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                run_league.load_spec(spec)

    def test_standard_spec_maps_resolve(self):
        loaded = run_league.load_spec(ROOT / "tools/ai/league_standard.json")
        for m in loaded["maps"]:
            resolved = pathlib.Path(m) if pathlib.Path(m).is_absolute() else ROOT / m
            self.assertTrue(resolved.exists(), m)

    def test_cell_matrix_is_member_by_map_by_faction(self):
        spec = {"candidate": "h", "members": ["a", "b"], "maps": ["m1", "m2"], "factions": ["f1"]}
        cells = run_league.league_cells(spec)
        self.assertEqual(len(cells), 4)
        self.assertEqual({(c["member"], c["map"]) for c in cells},
                         {("a", "m1"), ("a", "m2"), ("b", "m1"), ("b", "m2")})


class AggregateTests(unittest.TestCase):
    def test_candidate_perspective_only_no_double_count(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            cell = root / "hard_vs_classic__td_gdi__m1"
            write_cell(cell, candidate_won("g1", 0, 0, "classic", 1, 1))
            spec = {"candidate": "hard", "members": ["classic"], "maps": ["m1"], "factions": ["td_gdi"]}
            # cell naming must match league_cells' convention
            s = run_league.aggregate(root, spec)
            self.assertEqual((s["won"], s["lost"]), (1, 0))
            self.assertEqual(s["decided_matches"], 1)

    def test_spawn_split_and_per_member(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            rows = (
                candidate_won("g1", 0, 0, "classic", 1, 1)
                + candidate_won("g2", 1, 1, "classic", 0, 0)
                + [
                    {"game": "g3", "slot": "Multi0", "bot": "hard", "outcome": "lost", "spawn": 0, "opp": "exploit_rush"},
                    {"game": "g3", "slot": "Multi1", "bot": "exploit_rush", "outcome": "won", "spawn": 1, "opp": "hard"},
                ]
            )
            write_cell(root / "hard_vs_classic__td_gdi__m1", rows[:4])
            write_cell(root / "hard_vs_exploit_rush__td_gdi__m1", rows[4:])
            spec = {"candidate": "hard", "members": ["classic", "exploit_rush"],
                    "maps": ["m1"], "factions": ["td_gdi"]}
            s = run_league.aggregate(root, spec)
            self.assertEqual((s["won"], s["lost"]), (2, 1))
            self.assertEqual(s["per_member"]["classic"]["won"], 2)
            self.assertEqual(s["per_member"]["exploit_rush"]["won"], 0)
            self.assertEqual(s["per_member"]["exploit_rush"]["lost"], 1)
            self.assertEqual(s["spawn"]["0"], [1, 1])   # spawn 0: one win (g1), one loss (g3)
            self.assertEqual(s["spawn"]["1"], [1, 0])   # spawn 1: one win (g2)

    def test_missing_cell_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            spec = {"candidate": "hard", "members": ["ghost"], "maps": ["m1"], "factions": ["f1"]}
            s = run_league.aggregate(pathlib.Path(td), spec)
            self.assertEqual(s["decided_matches"], 0)
            self.assertEqual(len(s["cells_missing"]), 1)
            self.assertIsNone(s["league_score"])

    def test_league_score_and_wilson(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            rows = []
            for i in range(3):
                rows += candidate_won(f"w{i}", 0, 0, "classic", 1, 1)
            rows += [
                {"game": "l0", "slot": "Multi0", "bot": "hard", "outcome": "lost", "spawn": 0, "opp": "classic"},
                {"game": "l0", "slot": "Multi1", "bot": "classic", "outcome": "won", "spawn": 1, "opp": "hard"},
            ]
            write_cell(root / "hard_vs_classic__f1__m1", rows, completed=4)
            spec = {"candidate": "hard", "members": ["classic"], "maps": ["m1"], "factions": ["f1"]}
            s = run_league.aggregate(root, spec)
            self.assertEqual(s["league_score"], 0.75)
            lo, hi = s["league_wilson95"]
            self.assertLess(lo, 0.75)
            self.assertGreater(hi, 0.75)


if __name__ == "__main__":
    unittest.main()
