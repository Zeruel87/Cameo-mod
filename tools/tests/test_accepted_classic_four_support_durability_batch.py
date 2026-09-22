"""Contract for the classic-four MCV/support durability batch."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from cameo_model import Model  # noqa: E402


TARGETS = {
    "td_gdi_mobileconstructionvehicle": (4920, 294000, 65, 13, 118, 14700, "Medium"),
    "td_nod_mobileconstructionvehicle": (4920, 294000, 65, 13, 118, 14700, "Medium"),
    "ra1_allies_alliedmobileconstructionvehicle": (4650, 253000, 70, 14, 101, 12650, "Medium"),
    "ra1_soviets_mobileconstructionvehicle": (4650, 253000, 70, 14, 101, 12650, "Medium"),
    # Chassis-only reference rows: strategic shroud/jamming support has no
    # justified class/special price input, so both authored costs stay 5000.
    "ra1_allies_mobilegapgenerator": (5000, 96000, 76, 30, 38, 4800, "Light"),
    "ra1_allies_mobileradarjammer": (5000, 72000, 74, 30, 29, 3600, "Light"),
}


class AcceptedClassicFourSupportDurabilityBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Model(ROOT).rs

    def test_resolved_chassis_and_price_targets(self):
        for name, values in TARGETS.items():
            cost, hp, speed, turn, step, hp_per_step, armor = values
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertEqual(str(cost), actor.child("Valued").get("Cost"))
                self.assertEqual(str(hp), actor.child("Health").get("HP"))
                self.assertEqual(str(speed), actor.child("Mobile").get("Speed"))
                self.assertEqual(str(turn), actor.child("Mobile").get("TurnSpeed"))
                self.assertEqual(
                    str(step), actor.child("ChangesHealth@SelfHealing").get("Step")
                )
                self.assertEqual(
                    str(hp_per_step), actor.child("Repairable").get("HpPerStep")
                )
                self.assertEqual(armor, actor.child("Armor").get("Type"))

    def test_mcvs_do_not_leak_through_the_shared_template(self):
        """^MCV also feeds other packs; only the four classic actors move."""
        for name in (
            "ts_gdi_mobileconstructionvehicle",
            "ts_nod_mobileconstructionvehicle",
            "japan_japanesemobileconstructionvehicle",
            "ra2_allies_alliedmobileconstructionvehicle",
            "atreides_mobileconstructionvehicle",
        ):
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertEqual("5000", actor.child("Valued").get("Cost"))
                self.assertEqual("300000", actor.child("Health").get("HP"))
                self.assertEqual("75", actor.child("Mobile").get("Speed"))
                self.assertEqual("15", actor.child("Mobile").get("TurnSpeed"))


if __name__ == "__main__":
    unittest.main()
