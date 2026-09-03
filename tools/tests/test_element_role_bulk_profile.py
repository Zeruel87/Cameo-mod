"""Regression checks for the percentage-safe chemical and flame role batch."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset


ROOTS = {
    "CabalDissolverSpray": ("CannonChem_Light", 4000, 2, "Corrosion", "20"),
    "TSHighVelocityChem": ("CannonChem_Light", 45000, 2, "Corrosion", "20"),
    "TSHighVelocity2Chem": ("CannonChem_Light", 60000, 3, "Corrosion", "20"),
    "TSHighVelocityTurChem": ("CannonChem_Light", 72000, 3, "Corrosion", "20"),
    "TSFiendShardUP": ("Chemical_Heavy", 18000, 3, "Corrosion", "100"),
    "TSChemsprayUP": ("Chemical_Heavy", 96000, 3, "Corrosion", "100"),
    "TSVisceroidSprayUP": ("Chemical_Heavy", 30000, 3, "Corrosion", "100"),
    "HarakanF": ("Flame_Heavy", 4000, 2, "Temperature", "100"),
    "MutHFlamer": ("Flame_Heavy", 40000, 2, "Temperature", "100"),
    "TSChemAdatsMissile": ("MissileChem_Light", 12000, 3, "Corrosion", "20"),
    "ChemicalBikeRockets": ("MissileChem_Medium", 32000, 4, "Corrosion", "33"),
    "ChemicalStealthTankMissiles": ("MissileChem_Medium", 30000, 3, "Corrosion", "33"),
    "TSMammothTuskChem": ("MissileChem_Heavy", 40000, 2, "Corrosion", "50"),
}

RESOLVED = tuple(ROOTS) + (
    "ChemicalBikeRocketsExplosion",
    "ChemicalStealthTankExplosion",
)

RETIRED = {
    "LightChemicalWeapon", "MediumChemicalWeapon", "HeavyChemicalWeapon",
    "TankDestroyerCannon", "FlakWeapon", "LightMissile", "MediumMissile",
    "HeavyMissile", "ShrapnelWeapon", "MediumFlameWeapon", "HeavyFlameWeapon",
}


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


class ElementRoleBulkProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_roots_use_one_standard_flat_destination(self):
        for name, (family, damage, percentage_count, state, scale) in ROOTS.items():
            weapon = self.rules.resolve_weapon(name)
            main = child(weapon, f"Warhead@{family}")
            self.assertIsNotNone(main, name)
            self.assertEqual(str(damage), child(main, "Damage").value, name)
            self.assertEqual("0", child(main, "PercentageScale").value, name)
            state_name = child(main, "PhysicalStateName")
            if state_name is not None:
                self.assertEqual(state, state_name.value, name)
                self.assertEqual(scale, child(main, "PhysicalStateScale").value, name)
            else:
                states = child(main, "PhysicalStates")
                self.assertIsNotNone(states, name)
                self.assertEqual(scale, child(states, state).value, name)
            percentages = [w for w in weapon.children if w.value == "AreaDamagePercentage"]
            self.assertEqual(percentage_count, len(percentages), name)

    def test_retired_flat_slots_are_absent_from_the_resolved_closure(self):
        for name in RESOLVED:
            weapon = self.rules.resolve_weapon(name)
            flats = {
                w.key.split("@", 1)[1]
                for w in weapon.children
                if w.key.startswith("Warhead@") and w.value in {"AreaDamage", "SpreadDamage"}
            }
            self.assertFalse(flats & RETIRED, f"{name}: {flats & RETIRED}")

    def test_adats_chemical_main_remains_ground_and_water_only(self):
        weapon = self.rules.resolve_weapon("TSChemAdatsMissile")
        main = child(weapon, "Warhead@MissileChem_Light")
        self.assertEqual("Ground, Water", child(main, "ValidTargets").value)


if __name__ == "__main__":
    unittest.main()
