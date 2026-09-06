"""Regression checks for the remaining override-free element-role roots."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset


ROOTS = {
    "LeechSpit": ("Chemical_Light", 12000, 4, "Corrosion", "100"),
    "LurkerSpinesImpact": ("Chemical_Medium", 5000, 2, "Corrosion", "100"),
    "QueenSpine": ("Chemical_Medium", 20000, 2, "Corrosion", "100"),
    "TSBusMortarChem": ("Chemical_Heavy", 128000, 4, "Corrosion", "100"),
    "TSChemBoatcannon": ("Chemical_Medium", 25000, 3, "Corrosion", "100"),
    "TSChemRuinerMissile": ("MissileChem_Medium", 54000, 4, "Corrosion", "33"),
    "TSFiendShardBlue": ("Chemical_Medium", 24000, 4, "Corrosion", "100"),
    "TSFiendShardBlueUP": ("Chemical_Heavy", 36000, 6, "Corrosion", "100"),
    "YakNapalm": ("Flame_Heavy", 40000, 4, "Temperature", "100"),
}

RETIRED = {
    "ArrowWeapon", "Grenade", "GrenadeFriendlyFire", "HeavyBomb",
    "HeavyChemicalWeapon", "HeavyFlameWeapon", "LightChemicalWeapon",
    "LightMissile", "MediumChemicalWeapon", "MediumFlameWeapon",
    "MediumMissile", "ShrapnelWeapon", "ShrapnelWeaponFriendlyFire",
    "SmallArms", "SwordWeapon", "SwordWeaponFriendlyFire",
}


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


class RemainingElementRoleProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_roots_use_the_selected_element_role(self):
        for name, (family, damage, percentage_count, state, scale) in ROOTS.items():
            weapon = self.rules.resolve_weapon(name)
            main = child(weapon, f"Warhead@{family}")
            self.assertIsNotNone(main, name)
            self.assertEqual(str(damage), child(main, "Damage").value, name)
            self.assertEqual("0", child(main, "PercentageScale").value, name)
            states = child(main, "PhysicalStates")
            if states is not None:
                self.assertEqual(scale, child(states, state).value, name)
            else:
                self.assertEqual(state, child(main, "PhysicalStateName").value, name)
                self.assertEqual(scale, child(main, "PhysicalStateScale").value, name)
            percentages = [w for w in weapon.children if w.value == "AreaDamagePercentage"]
            self.assertEqual(percentage_count, len(percentages), name)

    def test_retired_flat_slots_are_absent(self):
        for name in ROOTS:
            weapon = self.rules.resolve_weapon(name)
            flats = {
                w.key.split("@", 1)[1]
                for w in weapon.children
                if w.key.startswith("Warhead@") and w.value in {"AreaDamage", "SpreadDamage"}
            }
            self.assertFalse(flats & RETIRED, f"{name}: {flats & RETIRED}")

    def test_leech_infection_and_queen_broodling_behaviors_remain(self):
        leech = child(self.rules.resolve_weapon("LeechSpit"), "Warhead@Chemical_Light")
        self.assertIn("LeechTankInfect", child(leech, "DamageTypes").value)
        self.assertEqual("Vehicle", child(leech, "ValidTargets").value)

        queen = child(self.rules.resolve_weapon("QueenSpine"), "Warhead@Chemical_Medium")
        self.assertIn("QueenBroodlingSpawn", child(queen, "DamageTypes").value)
        self.assertEqual("Broodling", child(queen, "InvalidTargets").value)


if __name__ == "__main__":
    unittest.main()
