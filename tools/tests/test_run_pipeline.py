"""Unit tests for tools/balance/run_pipeline.py.

The runner's whole value is that it executes BALANCE_PIPELINE.md §0 in the documented
order instead of leaving that order in prose. Two properties have to hold or it is worse
than nothing:

  1. It can NEVER apply. CLAUDE.md rule 3 puts `apply_balance --confirm` behind an
     explicit maintainer order. A wrapper able to reach it converts "a human decided"
     into "a script ran", and the gate stops being a gate. This is asserted against the
     built plan AND against the module source, because the dangerous version of this
     regression is someone adding a convenience flag later.

  2. Its exit code is the worst REAL stage code. Reporting a wrapper's success instead
     of the thing it wrapped is how the audit suite was believed green for a week while
     exiting 1 on every run (HANDOFF §3.0c).
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "balance"))
import run_pipeline as rp  # noqa: E402


def args(**kw):
    ns = argparse.Namespace(extract=False, workbook=False, faction=None,
                            dry_run=False, determinism=False)
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


class NeverApplies(unittest.TestCase):
    def test_no_planned_stage_can_apply(self):
        for a in (args(), args(extract=True), args(workbook=True),
                  args(extract=True, workbook=True, faction="ra1_soviets")):
            for stage in rp.plan(a):
                joined = " ".join(stage.cmd)
                self.assertNotIn("apply_balance", joined)
                self.assertNotIn("--confirm", joined)

    def test_the_module_never_names_confirm_as_an_argument(self):
        # A future `--confirm` / `--yes` flag would defeat the gate. The string may
        # appear in prose and in the command the runner PRINTS for the maintainer to
        # type, but never as something argparse accepts.
        src = pathlib.Path(rp.__file__).read_text(encoding="utf-8")
        for flag in ('add_argument("--confirm"', "add_argument('--confirm'",
                     'add_argument("--yes"', 'add_argument("--apply"'):
            self.assertNotIn(flag, src)


class PlanOrder(unittest.TestCase):
    def test_verify_default_writes_nothing(self):
        self.assertTrue(all(not s.writes for s in rp.plan(args())))

    def test_the_drift_check_runs_BEFORE_the_extract(self):
        """The ordering that makes the check mean anything.

        `extract_stats.py --check` re-extracts in memory and diffs against the ledger
        ON DISK. Extract first and the check compares the file it just wrote against
        itself: it passes unconditionally and the runner reports a clean tree while
        the ledger was stale. Check first and it answers the real question.
        """
        p = rp.plan(args(extract=True))
        steps = [s.step for s in p]
        self.assertLess(steps.index("7"), steps.index("1"))
        extract = p[steps.index("1")]
        self.assertTrue(extract.writes)
        self.assertNotIn("--check", " ".join(extract.cmd))

    def test_a_stale_ledger_does_not_fail_a_repair_run(self):
        # A stale ledger is the condition --extract exists to fix, so the diagnostic
        # check reports without gating. Everything after the extract still gates.
        repair = rp.plan(args(extract=True))
        self.assertFalse(repair[0].blocking)
        self.assertTrue(all(s.blocking for s in repair[1:]))
        # Without --extract nothing is being repaired, so the same stage gates.
        self.assertTrue(rp.plan(args())[0].blocking)

    def test_workbook_is_last(self):
        p = rp.plan(args(workbook=True))
        self.assertTrue(p[-1].writes)
        self.assertIn("build_workbook.py", " ".join(p[-1].cmd))

    def test_faction_filter_reaches_the_tools_that_accept_it(self):
        cmds = [" ".join(s.cmd) for s in rp.plan(args(extract=True, faction="d2k_ordos"))]
        passing = [c for c in cmds if "d2k_ordos" in c]
        self.assertTrue(passing)
        for c in passing:
            self.assertIn("extract_stats.py", c)


class DeterminismStage(unittest.TestCase):
    def test_off_by_default(self):
        self.assertTrue(all("check_determinism" not in " ".join(s.cmd)
                            for s in rp.plan(args())))

    def test_runs_last_when_asked_for(self):
        # It answers "is the compiler property holding", which is not worth asking of
        # a tree that already failed a structural gate.
        p = rp.plan(args(determinism=True, workbook=True))
        self.assertIn("check_determinism", " ".join(p[-1].cmd))

    def test_it_writes_nothing(self):
        self.assertFalse(rp.plan(args(determinism=True))[-1].writes)


class ExitCode(unittest.TestCase):
    """The runner reports the worst real stage code, never a wrapper's."""

    def worst(self, codes):
        stages = rp.plan(args())
        for s, c in zip(stages, codes):
            s.code = c
        return max((s.code for s in stages if s.blocking and s.code), default=0)

    def test_all_clean(self):
        self.assertEqual(self.worst([0, 0, 0, 0, 0]), 0)

    def test_one_failure_surfaces(self):
        self.assertEqual(self.worst([0, 1, 0, 0, 0]), 1)

    def test_worst_of_several_wins(self):
        self.assertEqual(self.worst([1, 0, 2, 0, 0]), 2)

    def test_a_dry_run_stage_is_not_a_pass(self):
        s = rp.plan(args())[0]
        rp.run(s, dry=True)
        self.assertIsNone(s.code)
        self.assertEqual(s.skipped, "dry-run")


if __name__ == "__main__":
    unittest.main()
