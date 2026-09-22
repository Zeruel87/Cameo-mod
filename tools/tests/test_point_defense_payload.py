"""Static coverage checks for point-defense projectile impacts."""

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
from miniyaml import Ruleset  # noqa: E402


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


def value(node, key):
    item = child(node, key)
    return item.value if item is not None else None


class PointDefensePayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_shared_pd_laser_damage_covers_both_missile_altitudes(self):
        weapon = self.rules.resolve_weapon("PDLaser")
        self.assertIsNotNone(weapon)
        weapon_targets = {item.strip() for item in (value(weapon, "ValidTargets") or "").split(",")}
        damage = child(weapon, "Warhead@1Dam")
        self.assertIsNotNone(damage)
        warhead_targets = {item.strip() for item in (value(damage, "ValidTargets") or "").split(",")}
        self.assertEqual(warhead_targets, {"Ground", "Missile", "BulletAS", "BallisticMissile"})
        self.assertTrue({"Missile", "BallisticMissile"} <= weapon_targets)
        self.assertNotIn("Air", warhead_targets)

    def test_active_pd_laser_descendants_keep_the_fixed_target_mask(self):
        for name in ("PDLaserLTNK2", "PDLaserBike"):
            with self.subTest(weapon=name):
                weapon = self.rules.resolve_weapon(name)
                damage = child(weapon, "Warhead@1Dam")
                targets = {item.strip() for item in (value(damage, "ValidTargets") or "").split(",")}
                self.assertTrue({"Ground", "Missile", "BallisticMissile"} <= targets)
                self.assertNotIn("Air", targets)

    def test_reported_live_consumers_resolve_to_the_fixed_root(self):
        expected = {
            "td_nod_lighttankmkii": "PDLaserLTNK2",
            "td_nod_reconbike": "PDLaserBike",
            "td_nod_chemicalattackbike": "PDLaserBike",
            "ra1_soviets_heavyteslatank": "PointDefenseTesla",
        }
        for actor_name, weapon_name in expected.items():
            with self.subTest(actor=actor_name):
                actor = self.rules.resolve(actor_name)
                armament = next(item for item in actor.children
                                if item.key == "Armament@pointdefense")
                self.assertEqual(value(armament, "Weapon"), weapon_name)
                weapon = self.rules.resolve_weapon(weapon_name)
                if weapon_name == "PointDefenseTesla":
                    warheads = [item for item in weapon.children
                                if item.key in ("Warhead@Tesla_Heavy",
                                                "Warhead@Tesla_Heavy_ExtraDamage")]
                    self.assertEqual(len(warheads), 2)
                else:
                    warheads = [child(weapon, "Warhead@1Dam")]
                for warhead in warheads:
                    targets = {item.strip() for item in
                               (value(warhead, "ValidTargets") or "").split(",")}
                    required = ({"Air", "BallisticMissile"}
                                if weapon_name == "PointDefenseTesla"
                                else {"Ground", "BallisticMissile"})
                    self.assertTrue(required <= targets)


if __name__ == "__main__":
    unittest.main()
