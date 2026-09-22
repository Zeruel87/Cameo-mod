"""Pins the weapon-local Yuri Gatling Tank and Cannon ranges."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset  # noqa: E402


WRAPPER_RANGES = {
    "YuriGatlingCannonMG1": "7500",
    "YuriGatlingCannonMG1_AA": "10125",
    "YuriGatlingCannonMG2": "7875",
    "YuriGatlingCannonMG2_AA": "11250",
    "YuriGatlingCannonMG3": "8250",
    "YuriGatlingCannonMG3_AA": "12375",
    "YuriGatlingTankMG1": "5400",
    "YuriGatlingTankMG1_AA": "7290",
    "YuriGatlingTankMG2": "5670",
    "YuriGatlingTankMG2_AA": "8100",
    "YuriGatlingTankMG3": "5940",
    "YuriGatlingTankMG3_AA": "8910",
}

WRAPPER_BASES = {
    "YuriGatlingCannonMG1": ("RA2GattlingMG1", 100),
    "YuriGatlingCannonMG1_AA": ("RA2GattlingMG1_AA", 100),
    "YuriGatlingCannonMG2": ("RA2GattlingMG2", 100),
    "YuriGatlingCannonMG2_AA": ("RA2GattlingMG2_AA", 100),
    "YuriGatlingCannonMG3": ("RA2GattlingMG3", 100),
    "YuriGatlingCannonMG3_AA": ("RA2GattlingMG3_AA", 100),
    "YuriGatlingTankMG1": ("RA2GattlingMG1", 75),
    "YuriGatlingTankMG1_AA": ("RA2GattlingMG1_AA", 75),
    "YuriGatlingTankMG2": ("RA2GattlingMG2", 75),
    "YuriGatlingTankMG2_AA": ("RA2GattlingMG2_AA", 75),
    "YuriGatlingTankMG3": ("RA2GattlingMG3", 75),
    "YuriGatlingTankMG3_AA": ("RA2GattlingMG3_AA", 75),
}

SHARED_RANGES = {
    "RA2GattlingMG1": "5000",
    "RA2GattlingMG1_AA": "6750",
    "RA2GattlingMG2": "5250",
    "RA2GattlingMG2_AA": "7500",
    "RA2GattlingMG3": "5500",
    "RA2GattlingMG3_AA": "8250",
}

TANK_ARMAMENTS = {
    "Armament@1": "YuriGatlingTankMG1",
    "Armament@2": "YuriGatlingTankMG2",
    "Armament@3": "YuriGatlingTankMG3",
    "Armament@1AA": "YuriGatlingTankMG1_AA",
    "Armament@2AA": "YuriGatlingTankMG2_AA",
    "Armament@3AA": "YuriGatlingTankMG3_AA",
}

CANNON_ARMAMENTS = {
    "Armament@1": "YuriGatlingCannonMG1",
    "Armament@2": "YuriGatlingCannonMG2",
    "Armament@3": "YuriGatlingCannonMG3",
    "Armament@1AA": "YuriGatlingCannonMG1_AA",
    "Armament@2AA": "YuriGatlingCannonMG2_AA",
    "Armament@3AA": "YuriGatlingCannonMG3_AA",
}

UNRELATED_SHARED_CONSUMERS = {
    "ra2_c_abram": {"Armament@machinegun": "RA2GattlingMG1"},
    "ra2_c_hum": {
        "Armament": "RA2GattlingMG1",
        "Armament@elite": "RA2GattlingMG2",
    },
    "ra2_c_hum2": {
        "Armament": "RA2GattlingMG1",
        "Armament@elite": "RA2GattlingMG2",
    },
    "ra2_c_ifv": {
        "Armament": "RA2GattlingMG1",
        "Armament@elite": "RA2GattlingMG2",
        "Armament@AA": "RA2GattlingMG1_AA",
        "Armament@eliteAA": "RA2GattlingMG2_AA",
    },
    "ra2leopard": {"Armament@machinegun": "RA2GattlingMG1"},
}


class YuriGatlingRangeSplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_all_private_wrappers_resolve_to_preserved_effective_ranges(self):
        for weapon_name, expected_range in WRAPPER_RANGES.items():
            with self.subTest(weapon=weapon_name):
                self.assertEqual(
                    expected_range,
                    self.rules.resolve_weapon(weapon_name).get("Range"),
                )

    def test_private_damage_bakes_each_former_actor_modifier(self):
        main_warhead = "Warhead@Bullet_Medium_Flat"
        for weapon_name, (base_name, modifier) in WRAPPER_BASES.items():
            with self.subTest(weapon=weapon_name):
                local = self.rules.weapon(weapon_name)
                weapon = self.rules.resolve_weapon(weapon_name)
                base = self.rules.resolve_weapon(base_name)
                base_damage = int(base.child(main_warhead).get("Damage"))
                expected_damage = str(base_damage * modifier // 100)

                self.assertEqual(base_name, local.child("Inherits").value)

                self.assertEqual(
                    expected_damage,
                    local.child(main_warhead).get("Damage"),
                )
                self.assertEqual(
                    expected_damage,
                    weapon.child(main_warhead).get("Damage"),
                )

                # The folded percentage half derives its magnitude from Damage.
                # These values also preserve that channel after removing the
                # actor modifier: 200 -> 150 bp for ground and 400 -> 300 for AA.
                scale = int(base.child(main_warhead).get("PercentageScale"))
                base_units = (base_damage * scale + 100000) // 200000
                private_units = (int(expected_damage) * scale + 100000) // 200000
                self.assertEqual(base_units * modifier // 100, private_units)

    def test_private_target_masks_and_cadence_match_their_shared_bases(self):
        main_warhead = "Warhead@Bullet_Medium_Flat"
        for weapon_name, (base_name, _modifier) in WRAPPER_BASES.items():
            with self.subTest(weapon=weapon_name):
                weapon = self.rules.resolve_weapon(weapon_name)
                base = self.rules.resolve_weapon(base_name)
                for field in ("ReloadDelay", "Burst", "BurstDelays"):
                    self.assertEqual(base.get(field), weapon.get(field), field)

                self.assertEqual(
                    base.get("ValidTargets"), weapon.get("ValidTargets")
                )
                self.assertEqual(
                    base.child(main_warhead).get("ValidTargets"),
                    weapon.child(main_warhead).get("ValidTargets"),
                )
                self.assertEqual(
                    base.child(main_warhead).get("PercentageScale"),
                    weapon.child(main_warhead).get("PercentageScale"),
                )

    def test_yuri_actors_use_only_their_private_wrappers(self):
        for actor_name, expected in (
            ("yuri_gatlingtank", TANK_ARMAMENTS),
            ("yuri_gatlingcannon", CANNON_ARMAMENTS),
        ):
            with self.subTest(actor=actor_name):
                actor = self.rules.resolve(actor_name)
                actual = {
                    child.key: child.get("Weapon")
                    for child in actor.children
                    if child.key in expected
                }
                self.assertEqual(expected, actual)

    def test_baked_actor_level_range_and_firepower_multipliers_are_absent(self):
        for actor_name in ("yuri_gatlingtank", "yuri_gatlingcannon"):
            with self.subTest(actor=actor_name):
                local = self.rules.actor(actor_name)
                resolved = self.rules.resolve(actor_name)
                self.assertIsNone(local.child("RangeMultiplier@GatlingBuff"))
                self.assertIsNone(resolved.child("RangeMultiplier@GatlingBuff"))
                self.assertEqual(
                    [],
                    [
                        child.key
                        for child in resolved.children
                        if child.key.startswith("FirepowerMultiplier")
                        and child.get("RequiresCondition") is None
                    ],
                )

    def test_shared_base_ranges_and_unrelated_consumers_are_unchanged(self):
        for weapon_name, expected_range in SHARED_RANGES.items():
            with self.subTest(weapon=weapon_name):
                self.assertEqual(
                    expected_range,
                    self.rules.resolve_weapon(weapon_name).get("Range"),
                )

        shared_names = set(SHARED_RANGES)
        for actor_name, expected in UNRELATED_SHARED_CONSUMERS.items():
            with self.subTest(actor=actor_name):
                actor = self.rules.resolve(actor_name)
                actual = {
                    child.key: child.get("Weapon")
                    for child in actor.children
                    if (child.key == "Armament" or child.key.startswith("Armament@"))
                    and child.get("Weapon") in shared_names
                }
                self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
