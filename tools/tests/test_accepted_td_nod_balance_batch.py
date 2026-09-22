"""Focused contract for the accepted TD Nod balance batch."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from cameo_model import Model  # noqa: E402
import formula  # noqa: E402


ACTORS = {
    "td_nod_minigunner": (130, 22000, 59, 22),
    "td_nod_flamethrower": (330, 29000, 65, 29),
    "td_nod_chemicalwarrior": (500, 56000, 58, 56),
    "td_nod_artillery": (850, 29000, 54, 12),
    "td_nod_flametank": (1130, 119000, 83, 48),
    "td_nod_buggy": (590, 36000, 161, 14),
    "td_nod_reconbike": (1140, 35000, 184, 14),
    "td_nod_lighttank": (930, 110000, 89, 44),
    "td_nod_ssmlauncher": (1710, 41000, 83, 16),
    "td_nod_stealthtank": (520, 43000, 131, 17),
}


class AcceptedTdNodBalanceBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Model(ROOT).rs

    def test_actor_chassis_and_prices(self):
        for name, (cost, hp, speed, healing) in ACTORS.items():
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertEqual(str(cost), actor.child("Valued").get("Cost"))
                self.assertEqual(str(hp), actor.child("Health").get("HP"))
                self.assertEqual(str(speed), actor.child("Mobile").get("Speed"))
                self.assertEqual(
                    str(healing), actor.child("ChangesHealth@SelfHealing").get("Step")
                )

    def assert_weapon(self, name, damage_tag, damage, range_, expected_dps):
        weapon = self.rules.resolve_weapon(name)
        self.assertEqual(str(range_), weapon.get("Range"))
        self.assertEqual(str(damage), weapon.child(f"Warhead@{damage_tag}").get("Damage"))
        actual = formula.dps(
            damage,
            int(weapon.get("ReloadDelay")),
            int(weapon.get("Burst") or 1),
            weapon.get("BurstDelays"),
        )
        self.assertAlmostEqual(expected_dps, actual, delta=0.1)

    def test_single_channel_baselines_reach_the_accepted_rates(self):
        cases = (
            ("td_nod_minigunner_minigun", "Bullet_Light", 3403, 4203, 243.091),
            ("td_nod_flamethrower_flamethrower", "Flame_Light", 27494, 2495, 458.241),
            ("td_nod_chemicalwarrior_chemspray", "Chemical_Light", 42792, 2822, 891.490),
            ("td_nod_artillery_artilleryshell", "Concussion_Medium_Flat", 72263, 11291, 645.203),
            ("td_nod_flametank_bigflamer", "Flame_Medium", 33642, 2532, 1121.395),
            ("td_nod_buggy_machinegun", "Bullet_Light", 3896, 4263, 584.369),
            ("td_nod_lighttank_70mm", "CannonHE_Medium", 14679, 4694, 326.197),
            ("td_nod_ssmlauncher_honestjohn", "MissileFire_Heavy", 69017, 10449, 552.133),
            ("td_nod_stealthtank_stealthtankmissiles", "MissileAP_Medium", 22230, 6081, 673.620),
        )
        for case in cases:
            with self.subTest(weapon=case[0]):
                self.assert_weapon(*case)

    def test_recon_bike_keeps_both_compatibility_channels_equal(self):
        weapon = self.rules.resolve_weapon("td_nod_reconbike_rocket")
        self.assertEqual("5376", weapon.get("Range"))
        self.assertEqual("7985", weapon.child("Warhead@MissileAP_Medium").get("Damage"))
        self.assertEqual(
            "7985", weapon.child("Warhead@CollapseTargetCompatibility1").get("Damage")
        )
        # Four preserved percentage channels contribute 8 nominal points per shot.
        total = formula.dps(7985 + 7985 + 8, 55, 2, "10")
        self.assertAlmostEqual(491.630, total, delta=0.1)

    def test_newer_td_rocket_pair_is_not_reverted(self):
        actor = self.rules.resolve("td_nod_rocketsoldier")
        weapon = self.rules.resolve_weapon("td_nod_rocketsoldier_rockets")
        self.assertEqual("390", actor.child("Valued").get("Cost"))
        self.assertEqual("14000", actor.child("Health").get("HP"))
        self.assertEqual("6028", weapon.get("Range"))
        self.assertEqual("16882", weapon.child("Warhead@MissileAP_Light").get("Damage"))


if __name__ == "__main__":
    unittest.main()
