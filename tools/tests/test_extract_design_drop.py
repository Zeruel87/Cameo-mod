"""extract_stats must never drop a committed design value silently.

Design values (`unit_class`, `special`, `tech_tier`, `class_anchor`) never exist in yaml; a
re-extract carries them over by ACTOR ID only. After #519 renamed `ra2e2.black` ->
`ra2e2_black`, every plain re-extract on master turned its `unit_class` 1.0 into null, and three
PRs (#534, #535, #516) shipped that loss at once. The guard records every design value whose
actor is no longer emitted and makes `main` refuse to write it.
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import _bootstrap  # noqa: F401 — sys.path side effect

sys.path.insert(0, str(pathlib.Path(_bootstrap.REPO_ROOT) / "tools" / "balance"))
sys.path.insert(0, str(pathlib.Path(_bootstrap.REPO_ROOT) / "tools" / "audit"))
import extract_stats  # noqa: E402


def _ledger(actors: dict) -> str:
    return json.dumps({"schema": 2, "ledger": "fake", "pack": "Fake",
                       "sections": {"units": actors}})


class DesignDropGuard(unittest.TestCase):
    def _build(self, committed: dict, roster: list[str]):
        """Run the real `build_both` on a fake roster, every heavy dependency stubbed."""
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            (out / "fake.json").write_text(_ledger(committed), encoding="utf-8")
            extract = lambda rs, a, section, ps, chain: {  # noqa: E731
                "design": {"unit_class": None, "special": None, "tech_tier": None,
                           "class_anchor": None, "subtype": None}}
            with mock.patch.object(extract_stats, "OUT", out), \
                    mock.patch.object(extract_stats, "pack_rosters", return_value={
                        "fake": {"pack": "Fake", "sections": {"units": roster}}}), \
                    mock.patch.object(extract_stats, "extract_actor", side_effect=extract), \
                    mock.patch.object(extract_stats, "split_derived",
                                      side_effect=lambda doc: (doc, {})), \
                    mock.patch.object(extract_stats, "tm"), mock.patch.object(extract_stats, "we"), \
                    mock.patch.object(extract_stats, "psp") as psp, \
                    mock.patch.object(extract_stats, "tier_chain"):
                psp.actor_multipliers.return_value = []
                ledgers, _ = extract_stats.build_both(mock.MagicMock())
            return ledgers, dict(extract_stats._DROPPED_DESIGN)

    def test_a_renamed_actor_records_the_dropped_value(self):
        # The #519 case: the committed ledger holds the OLD id, the roster emits the NEW one.
        _, dropped = self._build({"ra2e2.black": {"design": {"unit_class": 1.0}}},
                                 ["ra2e2_black"])
        self.assertEqual(dropped, {("fake", "ra2e2.black"): {"unit_class": 1.0}})

    def test_a_kept_actor_carries_its_value_and_drops_nothing(self):
        ledgers, dropped = self._build({"ra2e2_black": {"design": {"unit_class": 1.0}}},
                                       ["ra2e2_black"])
        self.assertEqual(dropped, {})
        unit = ledgers["fake"]["sections"]["units"]["ra2e2_black"]
        self.assertEqual(unit["design"]["unit_class"], 1.0)

    def test_null_and_subtype_only_blocks_are_not_design_values(self):
        _, dropped = self._build({"gone": {"design": {"unit_class": None, "subtype": "X"}}}, [])
        self.assertEqual(dropped, {})

    def test_state_does_not_leak_between_passes(self):
        self._build({"ra2e2.black": {"design": {"unit_class": 1.0}}}, ["ra2e2_black"])
        _, dropped = self._build({"ra2e2_black": {"design": {"unit_class": 1.0}}},
                                 ["ra2e2_black"])
        self.assertEqual(dropped, {})


class MainRefusesToWrite(unittest.TestCase):
    def _main(self, *flags):
        def build(model, faction):
            extract_stats._DROPPED_DESIGN[("fake", "ra2e2.black")] = {"unit_class": 1.0}
            return {"fake": {"sections": {}}}, {"fake": {}}
        with tempfile.TemporaryDirectory() as tmp:
            staged = pathlib.Path(tmp) / "staged"
            buf = io.StringIO()
            with mock.patch.object(extract_stats, "Model"), \
                    mock.patch.object(extract_stats, "build_both", side_effect=build), \
                    mock.patch.object(extract_stats, "model_constants", return_value={}), \
                    mock.patch.object(sys, "argv", ["extract_stats.py", "--output-dir",
                                                    str(staged), *flags]), \
                    contextlib.redirect_stdout(buf):
                code = extract_stats.main()
            extract_stats._DROPPED_DESIGN.clear()
            return code, (staged / "fake.json").exists(), buf.getvalue()

    def test_refuses_and_writes_nothing(self):
        code, written, text = self._main()
        self.assertEqual(code, 2)
        self.assertFalse(written)
        self.assertIn("ra2e2.black", text)
        self.assertIn("rename its key", text)

    def test_explicit_flag_writes(self):
        code, written, _ = self._main("--allow-design-drop")
        self.assertEqual(code, 0)
        self.assertTrue(written)


if __name__ == "__main__":
    unittest.main()
