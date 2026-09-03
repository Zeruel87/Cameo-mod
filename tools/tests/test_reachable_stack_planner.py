"""The inheritance-root planner must be a true partition, not a cover."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools" / "audit")]

import plan_reachable_stack_backlog as planner  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
from survey_weapon_structure import inventory  # noqa: E402


class ReachableStackPlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = planner.build()
        cls.names = [
            member["name"]
            for group in cls.data["groups"]
            for member in group["members"]
        ]
        cls.inventory = inventory(Ruleset(ROOT))

    def test_every_reachable_stack_occurs_exactly_once(self):
        self.assertEqual(self.data["reachable_stacked"], len(self.names))
        self.assertEqual(len(self.names), len(set(self.names)))
        raw = (
            set(self.inventory["sets"]["direct_actor_armament"])
            | set(self.inventory["sets"]["indirect_weapon_graph"])
        )
        self.assertEqual(raw, set(self.names))
        self.assertEqual(240, len(raw))
        self.assertEqual(
            226,
            self.inventory["counts"]["reviewed_stacked_main_transitive_weapon_graph"],
        )

    def test_multiple_inheritance_descendant_is_not_duplicated(self):
        self.assertEqual(1, self.names.count("GLBarrelExplode"))


if __name__ == "__main__":
    unittest.main()
