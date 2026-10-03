"""mission_story.py (MC2): mission-card grouping, terminal detection, dangling attempts.

The archive is one line per record (schema mission-card/1, AiMissionLogWriter).
Post-#691 the line stream carries two kinds (fransotto's boundary ruling):
record_kind="mission" events (PUBLISHED/DENIED/DORMANT/REOPENED — the shelf) and
record_kind="attempt" transitions (an attempt exists only from COMMIT). Pre-#691
records carry no record_kind and are all attempt lines. Tests pin both.
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

import mission_story


def card(uid, mid, attempt, state, tick, by="Squads", terminal=None, reason=None, type_="raid", bot="hard", kind="attempt"):
    r = {
        "schema": "mission-card/1", "game_uid": uid, "map_uid": "m", "map_title": "A Nuclear Winter",
        "player": "Multi0", "faction": "td_gdi", "bot": bot,
        "mission_id": mid, "by": by, "tick": tick, "type": type_,
    }
    if kind is not None:
        r["record_kind"] = kind
    if kind == "mission":
        r["event"] = state
    else:
        # attempt-kind and pre-#691 (kind=None) records both carry the fields
        r["attempt_id"] = f"{mid}|A{attempt}"
        r["attempt"] = attempt
        r["state"] = state
    if terminal is not None:
        r["terminal"] = terminal
    if reason:
        r["reason"] = reason
    return r


def run(records, args=()):
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "batch" / "Logs"
        p.mkdir(parents=True)
        with open(p / "cameo-ai-missions.jsonl", "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = mission_story.main([td, *args])
    return rc, out.getvalue()


class MissionStoryTests(unittest.TestCase):
    def test_attempts_group_under_mission_and_order_by_tick(self):
        recs = [
            card("g1", "raid:t:r3", 2, "COMMITTED", 500),
            card("g1", "raid:t:r3", 1, "COMMITTED", 100),
            card("g1", "raid:t:r3", 1, "FAILED", 300, terminal=True, reason="lost_units"),
            card("g1", "raid:t:r3", 2, "SUCCESS", 700, terminal=True, reason="done"),
        ]
        rc, out = run(recs)
        self.assertEqual(rc, 0)
        self.assertLess(out.index("A1 Squads"), out.index("A2 Squads"))
        self.assertIn("1 match(es), 1 mission(s)", out)

    def test_terminal_flag_wins_over_state_name(self):
        recs = [card("g1", "m:x", 1, "FAILED", 10, terminal=False)]
        rc, out = run(recs)
        self.assertIn("*open*", out)
        self.assertIn("no terminal line", out)

    def test_state_name_fallback_without_terminal_field(self):
        recs = [card("g1", "m:x", 1, "SUCCESS", 10)]
        rc, out = run(recs)
        self.assertIn("no dangling attempts", out)

    def test_dangling_reports_executor_and_last_state(self):
        recs = [
            card("g1", "raid:t:r9", 1, "COMMITTED", 100, by="Squads"),
            card("g1", "raid:t:r9", 1, "STALLED", 250, by="Squads", reason="stuck"),
        ]
        rc, out = run(recs)
        self.assertIn("raid:t:r9 A1: last STALLED@250 stuck by Squads", out)

    def test_per_type_success_rate(self):
        recs = [
            card("g1", "capture:a:1", 1, "COMMITTED", 10, type_="capture"),
            card("g1", "capture:a:1", 1, "SUCCESS", 50, terminal=True, type_="capture"),
            card("g1", "capture:a:2", 1, "COMMITTED", 60, type_="capture"),
            card("g1", "capture:a:2", 1, "FAILED", 90, terminal=True, reason="lost_units", type_="capture"),
        ]
        rc, out = run(recs)
        self.assertIn("success 1 (50%)", out)
        self.assertIn("failed 1", out)

    def test_match_and_mission_filters(self):
        recs = [
            card("g1", "m:a", 1, "SUCCESS", 10, terminal=True),
            card("g2", "m:b", 1, "FAILED", 10, terminal=True),
        ]
        _, out = run(recs, args=["--match", "g2"])
        self.assertIn("1 match(es), 1 mission(s)", out)
        self.assertIn("m:b", out)
        _, out = run(recs, args=["--mission", "m:a"])
        self.assertIn("m:a", out)
        self.assertNotIn("m:b", out)

    # -- the #691 boundary: mission-level events vs attempt records --

    def test_mission_events_print_as_shelf_not_attempt(self):
        # DENIED is mission-level feedback post-#691 — it must not invent an attempt.
        recs = [
            card("g1", "raid:t:r3", None, "PUBLISHED", 50, kind="mission"),
            card("g1", "raid:t:r3", None, "DENIED", 100, kind="mission", reason="no_units"),
            card("g1", "raid:t:r3", None, "DORMANT", 110, kind="mission"),
        ]
        rc, out = run(recs)
        self.assertIn("shelf: PUBLISHED@50  ->  DENIED@100 no_units  ->  DORMANT@110", out)
        self.assertIn("never-attempted", out)
        self.assertNotIn("A1", out)
        self.assertIn("1 mission-level DENIED", out)

    def test_dormant_reopened_then_attempt_succeeds(self):
        recs = [
            card("g1", "raid:t:r3", None, "PUBLISHED", 50, kind="mission"),
            card("g1", "raid:t:r3", None, "DORMANT", 100, kind="mission", reason="outmatched"),
            card("g1", "raid:t:r3", None, "REOPENED", 400, kind="mission", reason="target_gone"),
            card("g1", "raid:t:r3", 1, "COMMITTED", 410, by="Squads"),
            card("g1", "raid:t:r3", 1, "SUCCESS", 700, terminal=True, reason="done"),
        ]
        rc, out = run(recs)
        self.assertIn("shelf: PUBLISHED@50  ->  DORMANT@100 outmatched  ->  REOPENED@400 target_gone", out)
        self.assertIn("A1 Squads: COMMITTED@410  ->  SUCCESS@700 done", out)
        self.assertNotIn("never-attempted", out)

    def test_pre_691_records_group_as_attempts(self):
        # No record_kind at all = the pre-split corpus; every line is an attempt line.
        recs = [
            card("g1", "m:x", 1, "COMMITTED", 10, kind=None),
            card("g1", "m:x", 1, "FAILED", 20, kind=None, terminal=True, reason="lost_units"),
        ]
        rc, out = run(recs)
        self.assertIn("A1 Squads: COMMITTED@10  ->  FAILED@20 lost_units", out)
        self.assertNotIn("shelf:", out)


if __name__ == "__main__":
    unittest.main()
