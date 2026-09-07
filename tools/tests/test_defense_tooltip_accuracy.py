"""Reported defense tooltips must agree with resolved active gameplay rules."""
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
from miniyaml import Ruleset


class DefenseTooltipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_bastion_description_matches_capacity(self):
        actor = self.rules.resolve("ra1_allies_bastionartillerybunker")
        self.assertEqual("actor_bastion.description", actor.get("Buildable", "Description"))
        text = (ROOT / "mods/cameo/fluent/rules/en.ftl").read_text(encoding="utf-8")
        entry = text.split("actor_bastion =", 1)[1].split("\n\n", 1)[0]
        capacity = re.search(r"for (\d+) garrisoned soldiers", entry).group(1)
        self.assertEqual(actor.get("Cargo", "MaxWeight"), capacity)

    def test_laser_tower_description_and_all_upgrade_weapons_allow_air(self):
        actor = self.rules.resolve("schwarzermond_lasertower")
        self.assertEqual("actor_schwarzermond_lasertower.description",
                         actor.get("Buildable", "Description"))
        pack = ROOT / "mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond"
        self.assertIn("SchwarzerMond/translations/en.ftl", (pack / "content.yaml").read_text())
        text = (pack / "translations/en.ftl").read_text(encoding="utf-8")
        self.assertEqual(1, text.count("actor_schwarzermond_lasertower ="))
        entry = text.split("actor_schwarzermond_lasertower =", 1)[1].split("\n\n", 1)[0]
        self.assertIn("Can attack aircraft.", entry)
        armaments = actor.children_named("Armament")
        self.assertEqual(3, len(armaments))
        for armament in armaments:
            with self.subTest(armament=armament.key):
                weapon = self.rules.resolve_weapon(armament.get("Weapon"))
                self.assertIn("Air", weapon.get("ValidTargets").split(", "))


if __name__ == "__main__":
    unittest.main()
