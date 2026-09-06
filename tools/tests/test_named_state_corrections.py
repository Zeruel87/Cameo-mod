"""Regression checks for the guarded Waveforce, Quantum, and Cryo corrections."""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/named_state_corrections_comparison.json"
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

import consolidate_named_state_corrections as cohort
from audit_three_way_split import SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (6, "4ff2dd2066342eabcd32c27208b02dea64828f34a90588cd9c6a53fb36f7646c"),
    "percentage_damage": (3, "8700af0223e73090ed983ddb69290d64b9aef4e939658247af24783f27a60877"),
    "physical_state_bindings": (6, "2ed73922f9fd277b8f3599854bf8c5debf53011dca9d40766086bf22e2d79f0e"),
}

EMP_WALL_PINS = {
    "eden_EMP", "eden_EMP_AA", "edenTiger_EMP", "edenTiger_EMP_AA",
    "plymouth_EMP", "eden_EMP_GP", "plymouth_EMP_AA", "plymouth_EMP_Tiger",
}


class NamedStateCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_converter_is_fully_applied_and_closures_are_exact(self):
        self.assertTrue(cohort.inspect(self.rules))
        self.assertEqual(6, len(cohort.selections(self.rules)))
        for root, (_destination, expected, _total, _scale) in cohort.ROOTS.items():
            self.assertEqual(expected, cohort.descendants(self.rules, root), root)

    def test_comparison_is_exactly_the_six_reviewed_definitions(self):
        self.assertEqual(set(cohort.selections(self.rules)), set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (count, digest) in ACCEPTED.items():
            payload = json.dumps(
                self.by_kind[kind], sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(count, len(self.by_kind[kind]), kind)
            self.assertEqual(digest, hashlib.sha256(payload).hexdigest(), kind)

    def test_percentage_delta_is_bounded_and_non_overflowing(self):
        for name, groups in self.by_kind["percentage_damage"].items():
            for _hp, before, after in [row for group in groups for row in group]:
                self.assertGreaterEqual(before, 0, name)
                self.assertGreaterEqual(after, 0, name)
                self.assertLessEqual(abs(after - before), 1, name)

    def test_selected_state_scopes_are_explicit(self):
        for name, (destination, _total, _scale, root) in cohort.selections(self.rules).items():
            mains = set(main_warheads(self.rules.resolve_weapon(name)))
            self.assertEqual({f"{destination}FlatCompatibility"}, mains, name)
            nodes = cohort.flat_main_nodes(self.rules.resolve_weapon(name), mains)
            for state, (_before, after, scale) in cohort.STATE_SCOPES[root].items():
                self.assertEqual((after, {scale}), cohort.state_scope(nodes, state), name)

    def test_emp_wall_contract_remains_deferred_and_exact(self):
        self.assertTrue(EMP_WALL_PINS.isdisjoint(self.report["changed"]))
        for name in EMP_WALL_PINS:
            resolved = self.rules.resolve_weapon(name)
            self.assertEqual({"TemperatureCompatibility", "Tesla_Super"},
                             set(main_warheads(resolved)), name)
            temperature = resolved.child("Warhead@TemperatureCompatibility")
            self.assertEqual("wall", str(temperature.get("InvalidTargets")), name)

    def test_ratchets_match_live_reduction(self):
        self.assertEqual(114, SPLIT_BASELINE)
        self.assertEqual(90, BROADCAST_BASELINE)


if __name__ == "__main__":
    unittest.main()
