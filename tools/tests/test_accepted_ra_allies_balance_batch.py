"""Resolved regressions for the accepted RA Allies reference-anchor batch."""

from fractions import Fraction
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset


ACTORS = {
    "ra1_allies_alliedartillery": (1240, 30000, 58, 1500, 12),
    "ra1_allies_alliedlighttank": (1040, 75000, 111, 3750, 30),
    "ra1_allies_alliedmediumtank": (1280, 127000, 81, 6350, 51),
    "ra1_allies_alliedrocketsoldier": (480, 13000, 54, None, 13),
    "ra1_allies_rifleinfantry": (110, 20000, 56, None, 21),
    "ra1_allies_ranger": (510, 40000, 157, 2000, 16),
}

WEAPONS = {
    # weapon: (range, reload, burst, burst delay, main warhead, main damage,
    #          fixed percentage damage per cycle, exact nominal DPS)
    "ra1_allies_alliedartillery_155mm":
        (11813, 80, 1, 0, "Warhead@Concussion_Heavy", 58173, 15,
         Fraction(58188, 80)),
    "ra1_allies_alliedartillery_155mmcryo":
        (11813, 80, 1, 0, "Warhead@Concussion_Heavy", 58173, 15,
         Fraction(58188, 80)),
    "ra1_allies_alliedlighttank_25mm":
        (4897, 37, 1, 0, "Warhead@CannonHE_Medium", 16591, 5,
         Fraction(16596, 37)),
    "ra1_allies_alliedmediumtank_cannon":
        (5117, 47, 1, 0, "Warhead@CannonHE_Medium", 14554, 0,
         Fraction(14554, 47)),
    "ra1_allies_alliedmediumtank_cannon_cryo":
        (5117, 47, 1, 0, "Warhead@CannonCryo_Medium", 14554, 0,
         Fraction(14554, 47)),
    "ra1_allies_alliedrocketsoldier_rocketsra":
        (7500, 50, 1, 0, "Warhead@MissileAP_Medium_Flat", 11500, 0,
         Fraction(11500, 50)),
    "ra1_allies_alliedrocketsoldier_rocketsracryo":
        (7500, 50, 1, 0, "Warhead@MissileCryo_Medium", 11500, 0,
         Fraction(11500, 50)),
    "ra1_allies_rifleinfantry_carbine":
        (4778, 50, 3, 4, "Warhead@Bullet_Light", 3513, 0,
         Fraction(3 * 3513, 58)),
    "ra1_allies_rifleinfantry_carbine_cryo":
        (4778, 50, 3, 4, "Warhead@BulletCryo_Light", 3513, 0,
         Fraction(3 * 3513, 58)),
    "ra1_allies_ranger_machinegun":
        (4252, 10, 4, 5, "Warhead@Bullet_Light", 3137, 0,
         Fraction(4 * 3137, 25)),
    "ra1_allies_ranger_machinegun_cryo":
        (4252, 10, 4, 5, "Warhead@BulletCryo_Light", 3137, 0,
         Fraction(4 * 3137, 25)),
}

PERCENTAGE_WARHEADS = {
    "ra1_allies_alliedartillery_155mm": {
        "Warhead@HeavyCannonPercentage": (5, None),
        "Warhead@ShrapnelWeaponPercentage": (5, None),
        "Warhead@GrenadePercentage": (5, None),
    },
    "ra1_allies_alliedartillery_155mmcryo": {
        "Warhead@HeavyCannonPercentage": (5, None),
        "Warhead@ShrapnelWeaponPercentage": (5, None),
        "Warhead@GrenadePercentage": (5, None),
    },
    "ra1_allies_alliedlighttank_25mm": {
        "Warhead@GrenadePercentage": (1, 200),
        "Warhead@ShrapnelWeaponPercentage": (1, 200),
        "Warhead@LightFlameWeaponPercentage": (1, 200),
        "Warhead@MediumChemicalWeaponPercentage": (1, 200),
        "Warhead@TankDestroyerCannonPercentage": (1, 200),
    },
}


class AcceptedRaAlliesBalanceBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_resolved_actor_stats_match_the_accepted_targets(self):
        for actor, expected in ACTORS.items():
            with self.subTest(actor=actor):
                resolved = self.rules.resolve(actor)
                actual = (
                    int(resolved.get("Valued", "Cost")),
                    int(resolved.get("Health", "HP")),
                    int(resolved.get("Mobile", "Speed")),
                    (int(resolved.get("Repairable", "HpPerStep"))
                     if resolved.get("Repairable", "HpPerStep") else None),
                    int(resolved.get("ChangesHealth@SelfHealing", "Step")),
                )
                self.assertEqual(expected, actual)

    def test_resolved_weapon_ranges_cycles_and_nominal_dps_are_exact(self):
        for weapon, expected in WEAPONS.items():
            with self.subTest(weapon=weapon):
                resolved = self.rules.resolve_weapon(weapon)
                range_, reload, burst, burst_delay, warhead, damage, fixed, dps = expected
                actual_burst = int(resolved.get("Burst") or 1)
                actual_delay = int(resolved.get("BurstDelays") or 0)
                cycle = int(resolved.get("ReloadDelay")) + (actual_burst - 1) * actual_delay
                main_damage = int(resolved.child(warhead).get("Damage"))
                actual_dps = Fraction(actual_burst * (main_damage + fixed), cycle)

                self.assertEqual(range_, int(resolved.get("Range")))
                self.assertEqual((reload, burst, burst_delay),
                                 (int(resolved.get("ReloadDelay")), actual_burst, actual_delay))
                self.assertEqual(damage, main_damage)
                self.assertEqual(dps, actual_dps)

    def test_percentage_payloads_remain_fixed(self):
        for weapon, warheads in PERCENTAGE_WARHEADS.items():
            resolved = self.rules.resolve_weapon(weapon)
            for key, (damage, denominator) in warheads.items():
                with self.subTest(weapon=weapon, warhead=key):
                    node = resolved.child(key)
                    self.assertEqual("AreaDamagePercentage", node.value)
                    self.assertEqual(damage, int(node.get("Damage")))
                    actual_denominator = node.get("PercentageDenominator")
                    self.assertEqual(denominator,
                                     int(actual_denominator) if actual_denominator else None)

        light_main = self.rules.resolve_weapon(
            "ra1_allies_alliedlighttank_25mm").child("Warhead@CannonHE_Medium")
        self.assertEqual("1659", light_main.get("PercentageScale"))
        self.assertEqual("10000", light_main.get("PercentageDenominator"))

    def test_mutually_exclusive_weapon_pairs_stay_synchronized(self):
        pairs = (
            ("ra1_allies_alliedartillery_155mm",
             "ra1_allies_alliedartillery_155mmcryo"),
            ("ra1_allies_alliedmediumtank_cannon",
             "ra1_allies_alliedmediumtank_cannon_cryo"),
            ("ra1_allies_alliedrocketsoldier_rocketsra",
             "ra1_allies_alliedrocketsoldier_rocketsracryo"),
            ("ra1_allies_rifleinfantry_carbine",
             "ra1_allies_rifleinfantry_carbine_cryo"),
            ("ra1_allies_ranger_machinegun",
             "ra1_allies_ranger_machinegun_cryo"),
        )
        for normal, cryo in pairs:
            with self.subTest(normal=normal, cryo=cryo):
                normal_spec = WEAPONS[normal]
                cryo_spec = WEAPONS[cryo]
                self.assertEqual(normal_spec[:4], cryo_spec[:4])
                self.assertEqual(normal_spec[5:], cryo_spec[5:])

    def test_ranger_preserves_ground_water_and_air_access(self):
        for weapon in ("ra1_allies_ranger_machinegun",
                       "ra1_allies_ranger_machinegun_cryo"):
            resolved = self.rules.resolve_weapon(weapon)
            self.assertEqual("Ground, Water, Air", resolved.get("ValidTargets"), weapon)

    def test_upgrade_conditions_remain_mutually_exclusive(self):
        actors = {
            "ra1_allies_alliedartillery": ("Armament", "Armament@Upgrade"),
            "ra1_allies_alliedmediumtank": ("Armament", "Armament@Cryo"),
            "ra1_allies_alliedrocketsoldier": ("Armament@PRIMARY", "Armament@Upgrade"),
            "ra1_allies_rifleinfantry": ("Armament@PRIMARY", "Armament@Upgrade"),
            "ra1_allies_ranger": ("Armament", "Armament@Cryo"),
        }
        for actor, (normal, cryo) in actors.items():
            resolved = self.rules.resolve(actor)
            self.assertEqual("!ra1_allies_upgrade_cryomissiles",
                             resolved.child(normal).get("RequiresCondition"), actor)
            self.assertEqual("ra1_allies_upgrade_cryomissiles",
                             resolved.child(cryo).get("RequiresCondition"), actor)


if __name__ == "__main__":
    unittest.main()
