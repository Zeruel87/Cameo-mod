"""ab_summary.py: pooled spawn-position split.

`player.spawn` is the lobby slot, not the physical side — the asymmetry
readout must group by `player.home` (start cell), falling back to `name`
in records older than the home field. These tests pin that contract so a
future "fix" cannot quietly go back to reading the slot.
"""
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ai"))

import ab_summary


def record(uid, bot, outcome, home=None, name="Bot", ticks=1000, timestep=1):
    player = {"bot_type": bot, "outcome": outcome, "name": name}
    if home is not None:
        player["home"] = home
    return {"game_uid": uid, "player": player, "duration_ticks": ticks, "timestep": timestep}


def run_summary(records):
    """Write records as one jsonl per batch dir and return main()'s stdout."""
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "batch" / "Logs"
        p.mkdir(parents=True)
        with open(p / "cameo-ai-matches.jsonl", "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = ab_summary.main([td])
    assert rc == 0
    return out.getvalue()


class PooledSpawnSplitTests(unittest.TestCase):
    def test_split_pools_across_bots_and_swaps(self):
        # Three matches: side A wins two (once as each bot), side B wins one.
        # Pooling must ignore bot identity — the question is the position.
        recs = []
        for uid, winner_home, loser_home, wbot, lbot in [
            ("m1", "90,24", "11,45", "hard", "classic"),
            ("m2", "90,24", "11,45", "classic", "hard"),  # swapped bots, same side outcome
            ("m3", "11,45", "90,24", "hard", "classic"),
        ]:
            recs += [
                record(uid, wbot, "won", home=winner_home),
                record(uid, lbot, "lost", home=loser_home),
            ]
        out = run_summary(recs)
        self.assertIn("spawn split (pooled, 6 decided): 11,45: 1W-2L | 90,24: 2W-1L", out)

    def test_name_fallback_when_home_missing(self):
        recs = [
            record("m1", "hard", "won", home=None, name="Multi1"),
            record("m1", "classic", "lost", home=None, name="Multi0"),
        ]
        out = run_summary(recs)
        self.assertIn("Multi0: 0W-1L | Multi1: 1W-0L", out)

    def test_draws_do_not_enter_the_split(self):
        recs = [
            record("m1", "hard", "lost", home="90,24"),
            record("m1", "classic", "lost", home="11,45"),  # timeout draw: both "lost"
            record("m2", "hard", "won", home="90,24"),
            record("m2", "classic", "lost", home="11,45"),
        ]
        out = run_summary(recs)
        # Only the decided match feeds the split; the draw's two "lost" records stay out.
        self.assertIn("spawn split (pooled, 2 decided): 11,45: 0W-1L | 90,24: 1W-0L", out)

    def test_lobby_spawn_slot_is_not_the_side(self):
        # Same game, both records carry spawn: 0 (the harness default) — if the
        # split read the slot it would print one merged "0" row, not two sides.
        recs = [
            {**record("m1", "hard", "won", home="90,24"), "player": {"bot_type": "hard", "outcome": "won", "name": "A", "home": "90,24", "spawn": 0}},
            {**record("m1", "classic", "lost", home="11,45"), "player": {"bot_type": "classic", "outcome": "lost", "name": "B", "home": "11,45", "spawn": 0}},
        ]
        out = run_summary(recs)
        self.assertIn("11,45: 0W-1L | 90,24: 1W-0L", out)
        self.assertNotIn("0: 1W-1L", out)


class WatchdogReadoutTests(unittest.TestCase):
    def test_ownership_and_order_gate_sum_per_bot(self):
        # LC5 `ownership` and §19.6 `order_gate` (post-#695/#699 records) sum per
        # bot type across the corpus; `by_type` detail and absent fields stay out.
        recs = [
            {**record("m1", "hard", "won"), "ownership": {"checks": 10, "double_owner": 1, "orphan": 2, "by_type": [{"kind": "orphan", "type": "e1", "units": 2}]}, "order_gate": {"refused": 3, "conflicts": 0, "crossed": 4}},
            {**record("m1", "classic", "lost")},
            {**record("m2", "hard", "lost"), "ownership": {"checks": 8, "double_owner": 0, "orphan": 1}, "order_gate": {"refused": 1, "conflicts": 2, "crossed": 1}},
            {**record("m2", "classic", "won")},
        ]
        out = run_summary(recs)
        self.assertIn("watchdogs `hard`: ownership[checks=18 double_owner=1 orphan=3] "
                      "order_gate[conflicts=2 crossed=5 refused=4]", out)
        self.assertNotIn("watchdogs `classic`", out)
        self.assertNotIn("by_type", out)

    def test_pre_watchdog_records_print_nothing(self):
        recs = [
            record("m1", "hard", "won"),
            record("m1", "classic", "lost"),
        ]
        out = run_summary(recs)
        self.assertNotIn("watchdogs", out)


if __name__ == "__main__":
    unittest.main()
