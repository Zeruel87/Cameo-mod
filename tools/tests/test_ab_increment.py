"""ab_increment.py: mirror-only shard construction, early-stop math, smoke verification.

The driver launches nothing in tests — the A/B corruption modes are all in the
pure pieces: a comma'd --factions smuggling the cross pairing into a shard,
catch-up arithmetic that stops a live pair (or never stops a dead one), smoke
verification that would pass a dead arm, and the tasklist parse the instance
cap stands on.
"""
import argparse
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ai"))

import ab_increment


def plan_args(*extra):
    """Parsed args for the defaults, with a tempdir --out."""
    return ab_increment.build_parser().parse_args(
        ["--ctrl", "aaa111", "--cand", "bbb222", "--out", tempfile.mkdtemp(prefix="abi_plan_")]
        + list(extra))


class ShardCommandTests(unittest.TestCase):
    def test_single_faction_per_shard(self):
        argv = ab_increment.shard_argv(
            pathlib.Path("C:/x/trees/ctrl"), faction="td_gdi",
            support=pathlib.Path("C:/x/ctrl_td_gdi"), bot_a="hard", bot_b="classic",
            repeats=8, time_limit=3, stall_timeout=400)
        i = argv.index("--factions")
        self.assertEqual(argv[i + 1], "td_gdi")
        self.assertNotIn(",", argv[i + 1])
        # The batch runs the TREE'S copy — cwd/pinning is what freezes the arm.
        self.assertTrue(argv[1].endswith(str(pathlib.Path("tools/ai/run_ai_match_batch.py"))))
        self.assertIn("--swap-bots", argv)
        self.assertIn("8", argv)
        self.assertIn("hard", argv)
        self.assertIn("classic", argv)

    def test_comma_faction_rejected(self):
        with self.assertRaises(SystemExit):
            ab_increment.enforce_single_faction("td_gdi,td_nod")
        with self.assertRaises(SystemExit):
            ab_increment.shard_argv(
                pathlib.Path("t"), faction="td_gdi,td_nod",
                support=pathlib.Path("s"), bot_a="hard", bot_b="classic",
                repeats=8, time_limit=3, stall_timeout=400)

    def test_two_mirror_shards_per_arm_no_cross(self):
        args = plan_args()
        arms, shards, smoke = ab_increment.build_plan(args)
        per_arm = {a.name: [s for s in shards if s.arm == a.name] for a in arms}
        self.assertEqual(set(per_arm), {"ctrl", "half", "all"})
        tree_by_arm = {a.name: a.tree for a in arms}
        for name, arm_shards in per_arm.items():
            self.assertEqual(len(arm_shards), 2)
            factions = {s.faction for s in arm_shards}
            self.assertEqual(factions, {"td_gdi", "td_nod"})
            for s in arm_shards:
                i = s.argv.index("--factions")
                self.assertNotIn(",", s.argv[i + 1])
                # cwd = the arm's frozen tree and argv[1] is the TREE'S batch
                # runner copy — that pinning is what actually freezes the arm.
                self.assertEqual(s.cwd, tree_by_arm[name])
                self.assertTrue(s.argv[1].startswith(str(tree_by_arm[name])))
                self.assertTrue(str(s.support).endswith(s.label))

    def test_arm_wiring(self):
        args = plan_args()
        arms, shards, _ = ab_increment.build_plan(args)
        by = {a.name: a for a in arms}
        self.assertIsNone(by["ctrl"].groups)
        self.assertEqual(by["half"].groups, "A_squad_tactics")
        self.assertEqual(by["all"].groups, "all")
        self.assertEqual(by["ctrl"].commit, "aaa111")
        self.assertEqual(by["half"].commit, "bbb222")
        self.assertEqual(by["all"].commit, "bbb222")
        # 2 factions x 8 repeats per arm = the spec's 16 matches per arm.
        self.assertEqual(sum(s.planned for s in shards), 3 * 2 * 8)

    def test_arms_subset(self):
        args = plan_args("--arms", "ctrl,all")
        arms, shards, _ = ab_increment.build_plan(args)
        self.assertEqual([a.name for a in arms], ["ctrl", "all"])
        self.assertEqual(len(shards), 4)

    def test_bad_arm_name_rejected(self):
        with self.assertRaises(SystemExit):
            ab_increment.build_plan(plan_args("--arms", "ctrl,nope"))

    def test_smoke_shards_one_repeat_separate_dir(self):
        args = plan_args("--smoke")
        arms, shards, smoke = ab_increment.build_plan(args)
        self.assertEqual(len(smoke), len(arms))
        for s in smoke:
            self.assertEqual(s.planned, 1)
            i = s.argv.index("--repeats")
            self.assertEqual(s.argv[i + 1], "1")
            # Smoke writes under <out>/smoke/ — its different config fingerprint
            # must never pool into the arm's shard dirs.
            self.assertIn("smoke", pathlib.Path(s.support).parts)
        self.assertFalse(any(s.kind == "smoke" for s in shards))


class EarlyStopTests(unittest.TestCase):
    def test_strictly_uncatchable(self):
        # 5 won, 5 left -> best possible 10 < 11: decided.
        self.assertTrue(ab_increment.trailing_cannot_catch_up(5, 5, 11))
        # 5 won, 6 left -> best possible 11 == 11: a tie is still reachable, not a stop.
        self.assertFalse(ab_increment.trailing_cannot_catch_up(5, 6, 11))
        self.assertFalse(ab_increment.trailing_cannot_catch_up(10, 6, 11))

    def test_decided_pair_names_leader(self):
        a = {"won": 12, "played": 14, "remaining": 2}
        b = {"won": 5, "played": 12, "remaining": 4}
        self.assertEqual(ab_increment.decided_pair(a, b), "a")
        self.assertEqual(ab_increment.decided_pair(b, a), "b")

    def test_decided_pair_none_while_catchable(self):
        a = {"won": 11, "played": 14, "remaining": 2}
        b = {"won": 5, "played": 10, "remaining": 6}
        # b can still reach 11 (tie) — the pair stays live.
        self.assertIsNone(ab_increment.decided_pair(a, b))

    def test_arm_tally_pools_shards(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            shards = []
            for arm, faction, rows in (
                ("ctrl", "td_gdi", [{"bot_outcomes": [
                    {"bot_type": "hard", "outcome": "won"},
                    {"bot_type": "classic", "outcome": "lost"}]}] * 3),
                ("ctrl", "td_nod", [{"bot_outcomes": [
                    {"bot_type": "hard", "outcome": "lost"},
                    {"bot_type": "classic", "outcome": "won"}]}] * 2),
            ):
                support = d / f"{arm}_{faction}"
                support.mkdir(parents=True)
                (support / "batch_results.jsonl").write_text(
                    "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
                shards.append(ab_increment.Shard(
                    arm, faction, "full", 8, support, [], support, f"{arm}_{faction}"))
            tally = ab_increment.arm_tally("ctrl", shards, "hard")
            self.assertEqual(tally, {"won": 3, "played": 5, "remaining": 11})
            # A finished shard can never play its leftovers.
            shards[0].done = True
            tally = ab_increment.arm_tally("ctrl", shards, "hard")
            self.assertEqual(tally["remaining"], 6)


class ShardRetryTests(unittest.TestCase):
    def _shard(self, td, rows_per_dir):
        base = pathlib.Path(td)
        dirs = []
        for i, rows in enumerate(rows_per_dir):
            d = base / ("ctrl_td_gdi" if i == 0 else f"ctrl_td_gdi_r{i + 1}")
            d.mkdir(parents=True)
            (d / "batch_results.jsonl").write_text(
                "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            dirs.append(d)
        s = ab_increment.Shard("ctrl", "td_gdi", "full", 8, dirs[0], [], base, "ctrl_td_gdi")
        s.dirs = dirs
        s.attempt = len(dirs)
        s.done = True
        return s

    def test_progress_pools_retry_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            row = {"bot_outcomes": [{"bot_type": "hard", "outcome": "won"},
                                    {"bot_type": "classic", "outcome": "lost"}]}
            s = self._shard(td, [[row] * 5, [row] * 3])
            self.assertEqual(ab_increment.shard_progress(s, "hard"), (8, 8))

    def test_fingerprints_pool_retry_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._shard(td, [[{"fingerprint": "fp-a"}], [{"fingerprint": "fp-a"}]])
            self.assertEqual(ab_increment.shard_fingerprints(s), ["fp-a"])
            # Drift between rounds still surfaces as two sightings.
            (s.dirs[1] / "batch_results.jsonl").write_text(
                json.dumps({"fingerprint": "fp-b"}) + "\n", encoding="utf-8")
            self.assertEqual(ab_increment.shard_fingerprints(s), ["fp-a", "fp-b"])

    def test_retry_predicate(self):
        with tempfile.TemporaryDirectory() as td:
            row = {"bot_outcomes": []}
            s = self._shard(td, [[row] * 5])
            self.assertTrue(ab_increment.shard_needs_retry(s, 5, 2))    # 5 < 8, attempt 1
            self.assertFalse(ab_increment.shard_needs_retry(s, 8, 2))   # plan complete
            s.attempt = 3
            self.assertFalse(ab_increment.shard_needs_retry(s, 5, 2))   # budget spent
            s.attempt = 1
            s.early_stopped = True
            self.assertFalse(ab_increment.shard_needs_retry(s, 5, 2))   # deliberate stop
            s.early_stopped = False
            s.kind = "smoke"
            self.assertFalse(ab_increment.shard_needs_retry(s, 0, 2))   # smoke aborts loudly


class TasklistParseTests(unittest.TestCase):
    def test_counts_only_openra_rows(self):
        out = (
            '"OpenRA.exe","1234","Console","1","123,456 K"\r\n'
            '"python.exe","4321","Console","1","45,678 K"\r\n'
            '"OpenRA.exe","9999","Console","1","223,456 K"\r\n'
        )
        self.assertEqual(ab_increment.parse_tasklist_count(out), 2)

    def test_no_match_info_line_is_zero(self):
        self.assertEqual(ab_increment.parse_tasklist_count(
            "INFO: No tasks are running which match the specified criteria.\r\n"), 0)


class SmokeVerificationTests(unittest.TestCase):
    def _smoke_dir(self, td, records, results_rows):
        support = pathlib.Path(td) / "smoke" / "ctrl_td_gdi"
        (support / "Logs").mkdir(parents=True)
        (support / "Logs" / "cameo-ai-matches.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
        (support / "batch_results.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in results_rows), encoding="utf-8")
        return support

    def test_pass_needs_records_and_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            support = self._smoke_dir(
                td,
                records=[{"game_uid": "g1", "player": {"bot_type": "hard", "outcome": "won"}},
                         {"game_uid": "g1", "player": {"bot_type": "classic", "outcome": "lost"}}],
                results_rows=[{"variant": "v", "status": "ok", "fingerprint": "abc123def456"}])
            ok, detail = ab_increment.smoke_verified(support)
            self.assertTrue(ok)
            self.assertIn("abc123def456", detail)

    def test_no_records_fails(self):
        with tempfile.TemporaryDirectory() as td:
            support = self._smoke_dir(td, records=[], results_rows=[{"fingerprint": "x"}])
            ok, detail = ab_increment.smoke_verified(support)
            self.assertFalse(ok)
            self.assertIn("no match records", detail)

    def test_no_fingerprint_fails(self):
        with tempfile.TemporaryDirectory() as td:
            support = self._smoke_dir(
                td,
                records=[{"game_uid": "g1", "player": {"bot_type": "hard", "outcome": "won"}}],
                results_rows=[{"variant": "v", "status": "ok"}])
            ok, detail = ab_increment.smoke_verified(support)
            self.assertFalse(ok)
            self.assertIn("no fingerprint", detail)


class ArmStatsTests(unittest.TestCase):
    def _record(self, uid, bot, outcome, **extra):
        r = {"game_uid": uid, "player": {"bot_type": bot, "outcome": outcome}}
        r.update(extra)
        return r

    def test_wld_and_watchdog_totals(self):
        recs = [
            self._record("m1", "hard", "won",
                         ownership={"checks": 10, "orphan": 2, "by_type": [{"kind": "orphan"}]},
                         order_gate={"refused": 3, "crossed": 1}),
            self._record("m1", "classic", "lost"),
            self._record("m2", "hard", "lost", ownership={"checks": 8, "orphan": 0},
                         order_gate={"refused": 1, "conflicts": 2}),
            self._record("m2", "classic", "lost"),  # timeout draw: both lost
        ]
        stats = ab_increment.arm_stats(iter(recs))
        self.assertEqual(stats["matches"], 2)
        self.assertEqual(stats["per_bot"]["hard"], {"won": 1, "lost": 0, "draw": 1})
        self.assertEqual(stats["per_bot"]["classic"], {"won": 0, "lost": 1, "draw": 1})
        self.assertEqual(stats["ownership"]["hard"], {"checks": 18, "orphan": 2})
        self.assertEqual(stats["order_gate"]["hard"], {"refused": 4, "crossed": 1, "conflicts": 2})
        self.assertNotIn("by_type", stats["ownership"]["hard"])
        self.assertNotIn("classic", stats["ownership"])

    def test_partial_games_skipped(self):
        stats = ab_increment.arm_stats(iter([self._record("m1", "hard", "won")]))
        self.assertEqual(stats["per_bot"], {})


if __name__ == "__main__":
    unittest.main()
