"""Focused contract for the accepted classic-four harvester durability batch."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from cameo_model import Model  # noqa: E402


# actor -> (cost, hp, speed, self-healing step, hp per repair step, turn speed, armor)
HARVESTER_DURABILITY = {
    "td_gdi_tiberiumharvester": (1670, 240000, 69, 96, 12000, 14, "Heavy"),
    "td_nod_tiberiumharvester": (1670, 240000, 69, 96, 12000, 14, "Heavy"),
    "td_nod_stealthharvester": (1520, 175000, 77, 70, 8750, 15, "Heavy"),
    "ra1_allies_alliedoretruck": (1560, 210000, 81, 84, 10500, 16, "Medium"),
    "ra1_soviets_oretruck": (1560, 210000, 81, 84, 10500, 16, "Medium"),
}

# Shared templates must keep their old inherited values.
SHARED_TEMPLATE_DEFAULTS = {
    "ts_gdi_tiberiumharvester": (150000, 60, 1000),
    "ts_nod_tiberiumharvester": (150000, 60, 1000),
    "forgotten_tiberiumharvester": (150000, 60, 1000),
    "cabal_tiberiumharvester": (150000, 60, 1000),
    "japan_japaneseoretruck": (75000, 120, 1000),
    "ra1_soviets_heavyindustrialminer": (135000, 80, 1200),
}

# Shared/other-faction actors whose heal/repair/turn maths the batch must
# not touch (F1/F2/F8 guards on the six non-targets).
SHARED_TEMPLATE_MOTION = {
    "ts_gdi_tiberiumharvester": (12, 60, 7500),
    "ts_nod_tiberiumharvester": (12, 60, 7500),
    "forgotten_tiberiumharvester": (12, 60, 7500),
    "cabal_tiberiumharvester": (12, 60, 7500),
    "japan_japaneseoretruck": (24, 30, 3750),
    "ra1_soviets_heavyindustrialminer": (16, 54, 6750),
}

# Harvesting behaviour the batch must not disturb: actor -> (capacity,
# BaleLoadDelay, BaleUnloadDelay).
HARVESTER_CAPACITIES = {
    "td_gdi_tiberiumharvester": (45, 4, 1),
    "td_nod_tiberiumharvester": (45, 4, 1),
    "td_nod_stealthharvester": (30, 2, 1),
    "ra1_allies_alliedoretruck": (30, 3, 1),
    "ra1_soviets_oretruck": (30, 3, 1),
}


class AcceptedClassicFourHarvesterBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Model(ROOT).rs

    def test_chassis_and_prices(self):
        for name, values in HARVESTER_DURABILITY.items():
            cost, hp, speed, step, hp_per_step, turn_speed, armor = values
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertEqual(str(cost), actor.child("Valued").get("Cost"))
                self.assertEqual(str(hp), actor.child("Health").get("HP"))
                self.assertEqual(str(speed), actor.child("Mobile").get("Speed"))
                self.assertEqual(
                    str(step), actor.child("ChangesHealth@SelfHealing").get("Step")
                )
                self.assertEqual(
                    str(hp_per_step), actor.child("Repairable").get("HpPerStep")
                )
                self.assertEqual(
                    str(turn_speed), actor.child("Mobile").get("TurnSpeed")
                )
                self.assertEqual(armor, actor.child("Armor").get("Type"))

    def test_shared_templates_unmoved(self):
        for name, (hp, speed, cost) in SHARED_TEMPLATE_DEFAULTS.items():
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertEqual(str(hp), actor.child("Health").get("HP"))
                self.assertEqual(str(speed), actor.child("Mobile").get("Speed"))
                self.assertEqual(str(cost), actor.child("Valued").get("Cost"))

    def test_shared_templates_heal_repair_and_turn_unmoved(self):
        for name, (turn, step, hp_per_step) in SHARED_TEMPLATE_MOTION.items():
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertEqual(str(turn), actor.child("Mobile").get("TurnSpeed"))
                self.assertEqual(
                    str(step), actor.child("ChangesHealth@SelfHealing").get("Step")
                )
                self.assertEqual(
                    str(hp_per_step), actor.child("Repairable").get("HpPerStep")
                )

    def test_harvesting_behaviour_unmoved(self):
        """A hasty materialization must not clobber capacity or bale cadence."""
        for name, (capacity, load_delay, unload_delay) in HARVESTER_CAPACITIES.items():
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertEqual(
                    str(capacity), actor.child("StoresResources").get("Capacity")
                )
                self.assertEqual(
                    str(load_delay), actor.child("Harvester").get("BaleLoadDelay")
                )
                self.assertEqual(
                    str(unload_delay), actor.child("Harvester").get("BaleUnloadDelay")
                )


if __name__ == "__main__":
    unittest.main()
