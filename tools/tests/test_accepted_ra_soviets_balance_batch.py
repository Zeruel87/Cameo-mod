"""Resolved regressions for the accepted RA Soviet reference-anchor batch."""

from fractions import Fraction
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset


ACTORS = {
    # actor: cost, hp, speed, repair step, self-heal step, base armor
    "ra1_soviets_v2rocketlauncher": (1410, 45000, 67, 2250, 18, "Light"),
    "ra1_soviets_teslatank": (1440, 58000, 78, 2900, 23, "Light"),
    "ra1_soviets_grenadier": (230, 14000, 72, None, 14, "None"),
    "ra1_soviets_shocktrooper": (680, 31000, 48, None, 31, "Plate"),
    "ra1_soviets_heavytank": (1450, 172000, 66, 8600, 69, "Heavy"),
    "ra1_soviets_rifleinfantry": (110, 21000, 55, None, 21, "None"),
    "ra1_soviets_rocketsoldier": (440, 15000, 46, None, 15, "Flak"),
}

BASE_WEAPONS = {
    # weapon: range, min range, reload, burst, burst delay, direct damage map, DPS
    "ra1_soviets_v2rocketlauncher_scud": (
        12596, 2519, 120, 1, 0,
        {"Warhead@MissileHE_Heavy": 48998, "Warhead@Flame_Heavy": 48998},
        Fraction(97996, 120)),
    "ra1_soviets_teslatank_ttankzap": (
        7898, None, 80, 1, 0,
        {"Warhead@Tesla_Heavy": 32798,
         "Warhead@Tesla_Heavy_ExtraDamage": 16399},
        Fraction(49197, 80)),
    "ra1_soviets_grenadier_grenade": (
        4973, None, 40, 1, 0, {"Warhead@Demolition_Light": 13577},
        Fraction(13577, 40)),
    "ra1_soviets_shocktrooper_portatesla": (
        5932, None, 40, 1, 0,
        {"Warhead@Tesla_Heavy": 9102,
         "Warhead@Tesla_Heavy_ExtraDamage": 4551},
        Fraction(13653, 40)),
    "ra1_soviets_heavytank_105mm": (
        5193, None, 76, 2, 5, {"Warhead@CannonHE_Medium": 18909},
        Fraction(2 * 18909, 81)),
    "ra1_soviets_rifleinfantry_carbine": (
        4586, None, 50, 3, 5, {"Warhead@Bullet_Light": 3604},
        Fraction(3 * 3604, 60)),
    "ra1_soviets_rocketsoldier_rocketsra": (
        6910, None, 50, 1, 0, {"Warhead@MissileAP_Medium_Flat": 13216},
        Fraction(13216, 50)),
}

UPGRADE_DIRECT_DAMAGE = {
    "ra1_soviets_v2rocketlauncher_scudthermobaric": {
        "Warhead@MissileHE_Heavy": 48998,
        "Warhead@Flame_Heavy": 48998,
        "Warhead@Demolition_Heavy": 32665,
        "Warhead@HeavyMissile": 32665,
        "Warhead@HeavyFlameWeapon": 32665,
    },
    "ra1_soviets_v2rocketlauncher_scudtesla": {
        "Warhead@MissileHE_Heavy": 48998,
        "Warhead@Flame_Heavy": 48998,
        "Warhead@Tesla_Heavy": 24499,
        "Warhead@Tesla_Heavy_ExtraDamage": 12250,
        "Warhead@HeavyMissile": 24499,
        "Warhead@HeavyFlameWeapon": 24499,
    },
    "ra1_soviets_v2rocketlauncher_scudteslafragment1": {
        "Warhead@MissileTesla_Heavy": 14699,
    },
    "ra1_soviets_v2rocketlauncher_scudteslafragment2": {
        "Warhead@MissileTesla_Heavy": 7350,
    },
    "ra1_soviets_teslatank_ttankzap_emp": {
        "Warhead@Tesla_Heavy": 32798,
        "Warhead@Tesla_Heavy_ExtraDamage": 16399,
    },
    "ra1_soviets_teslatank_ttankzaparc_emp": {
        "Warhead@Tesla_Heavy": 32798,
        "Warhead@Tesla_Heavy_ExtraDamage": 16399,
    },
    "ra1_soviets_teslatank_ttankzaparcteslafragment1_emp": {
        "Warhead@Tesla_Heavy": 16399,
        "Warhead@Tesla_Heavy_ExtraDamage": 8200,
    },
    "ra1_soviets_teslatank_ttankzaparcteslafragment2_emp": {
        "Warhead@Tesla_Heavy": 8200,
        "Warhead@Tesla_Heavy_ExtraDamage": 4100,
    },
    "ra1_soviets_grenadier_grenadethermobaric": {
        "Warhead@Thermobaric_Light": 13577,
    },
    "ra1_soviets_shocktrooper_portatesla_emp": {
        "Warhead@Tesla_Heavy": 9102,
        "Warhead@Tesla_Heavy_ExtraDamage": 4551,
    },
    "ra1_soviets_shocktrooper_portateslaarc_emp": {
        "Warhead@Tesla_Heavy": 9102,
        "Warhead@Tesla_Heavy_ExtraDamage": 4551,
    },
    "ra1_soviets_shocktrooper_portateslafragment": {
        "Warhead@Tesla_Heavy": 4551,
        "Warhead@Tesla_Heavy_ExtraDamage": 2275,
    },
    "ra1_soviets_heavytank_105mmthermobaric": {
        "Warhead@Flame_Medium_Flat": 22690,
    },
    "ra1_soviets_rifleinfantry_carbine_incendiary": {
        "Warhead@Flame_Light_Flat": 7208,
    },
}


class AcceptedRaSovietsBalanceBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_resolved_actor_stats_and_armor_match_the_accepted_targets(self):
        for actor, expected in ACTORS.items():
            with self.subTest(actor=actor):
                resolved = self.rules.resolve(actor)
                repair = resolved.get("Repairable", "HpPerStep")
                actual = (
                    int(resolved.get("Valued", "Cost")),
                    int(resolved.get("Health", "HP")),
                    int(resolved.get("Mobile", "Speed")),
                    int(repair) if repair else None,
                    int(resolved.get("ChangesHealth@SelfHealing", "Step")),
                    resolved.get("Armor", "Type"),
                )
                self.assertEqual(expected, actual)

    def test_base_weapon_geometry_cycles_and_nominal_dps_are_exact(self):
        for weapon, expected in BASE_WEAPONS.items():
            with self.subTest(weapon=weapon):
                resolved = self.rules.resolve_weapon(weapon)
                range_, min_range, reload, burst, burst_delay, damages, dps = expected
                actual_burst = int(resolved.get("Burst") or 1)
                actual_delay = int(resolved.get("BurstDelays") or 0)
                cycle = int(resolved.get("ReloadDelay")) + (actual_burst - 1) * actual_delay
                damage_per_shot = sum(
                    int(resolved.child(warhead).get("Damage"))
                    for warhead in damages)

                self.assertEqual(range_, int(resolved.get("Range")))
                actual_min = resolved.get("MinRange")
                self.assertEqual(min_range, int(actual_min) if actual_min else None)
                self.assertEqual((reload, burst, burst_delay),
                                 (int(resolved.get("ReloadDelay")), actual_burst, actual_delay))
                self.assertEqual(damages, {
                    key: int(resolved.child(key).get("Damage")) for key in damages})
                self.assertEqual(dps, Fraction(actual_burst * damage_per_shot, cycle))

    def test_mutually_exclusive_upgrade_flat_damage_is_scaled(self):
        for weapon, damages in UPGRADE_DIRECT_DAMAGE.items():
            resolved = self.rules.resolve_weapon(weapon)
            with self.subTest(weapon=weapon):
                self.assertEqual(damages, {
                    key: int(resolved.child(key).get("Damage")) for key in damages})

        family_ranges = {
            "ra1_soviets_v2rocketlauncher_scudthermobaric": (12596, 2519),
            "ra1_soviets_v2rocketlauncher_scudtesla": (12596, 2519),
            "ra1_soviets_teslatank_ttankzap_emp": (7898, None),
            "ra1_soviets_teslatank_ttankzaparc_emp": (7898, None),
            "ra1_soviets_grenadier_grenadethermobaric": (4973, None),
            "ra1_soviets_shocktrooper_portatesla_emp": (5932, None),
            "ra1_soviets_shocktrooper_portateslaarc_emp": (5932, None),
            "ra1_soviets_heavytank_105mmthermobaric": (5193, None),
            "ra1_soviets_rifleinfantry_carbine_incendiary": (4586, None),
        }
        for weapon, (range_, min_range) in family_ranges.items():
            resolved = self.rules.resolve_weapon(weapon)
            self.assertEqual(range_, int(resolved.get("Range")), weapon)
            actual_min = resolved.get("MinRange")
            self.assertEqual(min_range, int(actual_min) if actual_min else None, weapon)

    def test_percentage_and_emp_payloads_remain_unchanged(self):
        expected = {
            "ra1_soviets_v2rocketlauncher_scudthermobaric": {
                "Warhead@HeavyMissilePercentage": 20,
                "Warhead@HeavyFlameWeaponPercentage": 20,
            },
            "ra1_soviets_v2rocketlauncher_scudtesla": {
                "Warhead@HeavyMissilePercentage": 15,
                "Warhead@HeavyFlameWeaponPercentage": 15,
                "Warhead@EMPUnit": 45000,
            },
            "ra1_soviets_teslatank_ttankzap": {"Warhead@EMPUnit": 1000},
            "ra1_soviets_teslatank_ttankzap_emp": {"Warhead@EMPUnit": 20000},
            "ra1_soviets_teslatank_ttankzaparc_emp": {"Warhead@EMPUnit": 20000},
            "ra1_soviets_shocktrooper_portatesla": {"Warhead@EMPUnit": 1000},
            "ra1_soviets_shocktrooper_portatesla_emp": {"Warhead@EMPUnit": 10000},
            "ra1_soviets_shocktrooper_portateslaarc_emp": {"Warhead@EMPUnit": 10000},
            "ra1_soviets_grenadier_grenadethermobaric": {
                "Warhead@ShrapnelWeaponPercentage": 2,
                "Warhead@MediumFlameWeaponPercentage": 2,
            },
        }
        for weapon, warheads in expected.items():
            resolved = self.rules.resolve_weapon(weapon)
            for key, damage in warheads.items():
                self.assertEqual(damage, int(resolved.child(key).get("Damage")),
                                 f"{weapon}:{key}")

    def test_v2_min_range_ratio_and_on_death_weapon_identity_are_preserved(self):
        actor = self.rules.resolve("ra1_soviets_v2rocketlauncher")
        expected = {
            "Armament@PRIMARY": "ra1_soviets_v2rocketlauncher_scud",
            "Armament@HE": "ra1_soviets_v2rocketlauncher_scudthermobaric",
            "Armament@Tesla": "ra1_soviets_v2rocketlauncher_scudtesla",
            "FireWarheadsOnDeath": "ra1_soviets_v2rocketlauncher_scud",
            "FireWarheadsOnDeath@HE": "ra1_soviets_v2rocketlauncher_scudthermobaric",
            "FireWarheadsOnDeath@Tesla": "ra1_soviets_v2rocketlauncher_scudtesla",
        }
        self.assertEqual(expected, {
            key: actor.child(key).get("Weapon") for key in expected})
        for weapon in expected.values():
            resolved = self.rules.resolve_weapon(weapon)
            self.assertLessEqual(
                abs(Fraction(int(resolved.get("MinRange")), int(resolved.get("Range")))
                    - Fraction(1, 5)),
                Fraction(1, int(resolved.get("Range"))))

    def test_shared_weapon_roots_are_not_changed_for_unrelated_consumers(self):
        expected = {
            "RocketsRA": (6643, {"Warhead@MissileAP_Medium_Flat": 20000}),
            "PortaTesla": (4652, {"Warhead@Tesla_Heavy": 20000,
                                  "Warhead@Tesla_Heavy_ExtraDamage": 10000}),
            "TTankZap": (7300, {"Warhead@Tesla_Heavy": 40000,
                                 "Warhead@Tesla_Heavy_ExtraDamage": 20000}),
            "SCUD": (14110, {"Warhead@MissileHE_Heavy": 60000,
                             "Warhead@Flame_Heavy": 60000}),
        }
        for weapon, (range_, damages) in expected.items():
            resolved = self.rules.resolve_weapon(weapon)
            self.assertEqual(range_, int(resolved.get("Range")), weapon)
            self.assertEqual(damages, {
                key: int(resolved.child(key).get("Damage")) for key in damages}, weapon)


if __name__ == "__main__":
    unittest.main()
