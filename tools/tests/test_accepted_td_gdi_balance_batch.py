"""Focused contract for the accepted TD GDI balance batch."""

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
    "td_gdi_minigunner": (110, 22000, 58, 22),
    "td_gdi_grenadier": (230, 15000, 73, 15),
    "td_gdi_humvee": (560, 45000, 144, 18),
    "td_gdi_battletank": (1300, 151000, 74, 60),
    "td_gdi_mammothtank": (2740, 280000, 49, 112),
    "td_gdi_mlrs": (1350, 44000, 74, 18),
}


class AcceptedTdGdiBalanceBatchTests(unittest.TestCase):
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

    def test_single_baseline_weapons_reach_the_accepted_rates(self):
        self.assert_weapon("td_gdi_minigunner_minigun", "Bullet_Light", 3539, 4393, 239.94)
        self.assert_weapon("td_gdi_grenadier_grenade", "Demolition_Light", 19346, 4945, 460.616)
        self.assert_weapon("td_gdi_humvee_machinegun", "Bullet_Light", 4698, 4321, 671.187)
        self.assert_weapon("td_gdi_mlrs_227mm", "MissileAP_Medium", 14736, 9993, 650.133)

    def test_mlrs_upgrade_keeps_the_same_damage_budget(self):
        self.assert_weapon(
            "td_gdi_mlrs_227mmamt", "MissileAP_Medium", 14736, 9993, 650.133
        )

    def test_battle_tank_preserves_equal_cannon_and_missile_budget(self):
        cannon = self.rules.resolve_weapon("td_gdi_battletank_120mm")
        missile = self.rules.resolve_weapon("td_gdi_battletank_m1a1missiles")
        self.assertEqual("14848", cannon.child("Warhead@CannonHE_Medium").get("Damage"))
        self.assertEqual("14848", missile.child("Warhead@MissileAP_Medium").get("Damage"))
        self.assertEqual("5181", cannon.get("Range"))
        self.assertEqual("5145", missile.get("Range"))
        total = formula.dps(14848, 72) + formula.dps(14848, 72)
        self.assertAlmostEqual(412.432, total, delta=0.1)

    def test_mammoth_preserves_equal_cannon_and_missile_budget(self):
        cannon = self.rules.resolve_weapon("td_gdi_mammothtank_120mmdual")
        missile = self.rules.resolve_weapon("td_gdi_mammothtank_mammothmissiles")
        self.assertEqual("13892", cannon.child("Warhead@CannonHE_Heavy").get("Damage"))
        self.assertEqual("13892", missile.child("Warhead@MissileAP_Heavy").get("Damage"))
        self.assertEqual("5341", cannon.get("Range"))
        self.assertEqual("5341", missile.get("Range"))
        total = formula.dps(13892, 72, 2, "8") + formula.dps(13892, 68, 2, "12")
        self.assertAlmostEqual(694.616, total, delta=0.1)

    def test_newer_td_rocket_pair_is_not_reverted(self):
        actor = self.rules.resolve("td_gdi_rocketsoldier")
        weapon = self.rules.resolve_weapon("td_gdi_rocketsoldier_rockets")
        self.assertEqual("450", actor.child("Valued").get("Cost"))
        self.assertEqual("16000", actor.child("Health").get("HP"))
        self.assertEqual("6500", weapon.get("Range"))
        self.assertEqual("15800", weapon.child("Warhead@MissileAP_Light").get("Damage"))


if __name__ == "__main__":
    unittest.main()
