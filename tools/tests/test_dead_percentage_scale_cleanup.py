"""Zero PercentageScale fields must not sit on SpreadDamage, which ignores them."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit")]

from miniyaml import Ruleset  # noqa: E402


WEAPONS = {
    "NaxCorrosionRocketTrooper_elite",
    "SandmarineTuskTwin",
    "WaveTurretImpact",
}


class DeadPercentageScaleCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_spread_damage_has_no_ignored_percentage_scale(self):
        for name in WEAPONS:
            with self.subTest(name=name):
                resolved = self.rules.resolve_weapon(name)
                spread = [
                    node for node in resolved.children
                    if node.value == "SpreadDamage"
                ]
                self.assertTrue(spread)
                for node in spread:
                    self.assertIsNone(node.get("PercentageScale"), node.key)


if __name__ == "__main__":
    unittest.main()
