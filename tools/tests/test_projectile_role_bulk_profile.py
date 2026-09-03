"""Regression checks for the projectile-role backlog batch."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset


ROOTS = {
    "CabalAscendedRockets": ("MissileHE_Heavy", 30000, 6),
    "CommandoGrenadeLauncher": ("Concussion_Medium", 40000, 2),
    "MachineGunBuggy2": ("Bullet_Medium", 6000, 3),
    "NanoArtilleryAG": ("Concussion_Heavy", 23331, 3),
    "155mm": ("Concussion_Heavy", 30000, 3),
    "ChronoTusk": ("MissileHE_Heavy", 20000, 5),
    "GDIRigPhalanx": ("Bullet_Medium", 24000, 6),
    "HMG_Duelist": ("Bullet_Medium", 12000, 6),
    "HermitShoot": ("Concussion_Medium", 12000, 6),
    "Nike": ("MissileHE_Heavy", 16000, 4),
    "PatriarchShoot": ("Concussion_Medium", 12000, 6),
    "SpithidSpit": ("Bullet_Light", 6000, 3),
    "ra120mm": ("CannonHE_Heavy", 24000, 4),
}

RETIRED = {
    "ArrowWeapon", "Chaingun", "FlakWeapon", "Grenade", "GrenadeFriendlyFire",
    "HeavyAAWeapon", "HeavyBomb", "HeavyCannon", "HeavyMissile", "LightMissile",
    "MediumCannon", "MediumMissile", "ShrapnelWeapon",
    "ShrapnelWeaponFriendlyFire", "SmallArms", "TankDestroyerCannon",
}

CLOSURE = tuple(ROOTS) + (
    "155mmBastion", "155mmBastionCryo", "155mmCryo", "ArtilleryExplode",
    "ChronoTuskCryo", "GDIRigPhalanxTower", "HermitShoot1", "HermitShoot2",
    "HermitShoot3", "HermitShoot4", "MachineGunBuggy2_AA", "PatriarchShoot1",
    "PatriarchShoot2", "PatriarchShoot3", "PatriarchShoot4", "DT120mm",
    "DT120mm1", "ra120mmTargetingComputer", "ra120mmirak", "ragal120mm",
)


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


class ProjectileRoleBulkProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_roots_have_one_standard_flat_destination_and_standalone_percentages(self):
        for name, (family, damage, percentage_count) in ROOTS.items():
            weapon = self.rules.resolve_weapon(name)
            main = child(weapon, f"Warhead@{family}")
            self.assertIsNotNone(main, name)
            self.assertEqual(str(damage), child(main, "Damage").value, name)
            self.assertEqual("0", child(main, "PercentageScale").value, name)
            percentages = [w for w in weapon.children if w.value == "AreaDamagePercentage"]
            self.assertEqual(percentage_count, len(percentages), name)

    def test_retired_flat_slots_are_absent_from_resolved_closures(self):
        for name in CLOSURE:
            weapon = self.rules.resolve_weapon(name)
            flats = {
                w.key.split("@", 1)[1]
                for w in weapon.children
                if w.key.startswith("Warhead@") and w.value in {"AreaDamage", "SpreadDamage"}
            }
            self.assertFalse(flats & RETIRED, f"{name}: {flats & RETIRED}")

    def test_commando_keeps_integrity_damage_separate(self):
        weapon = self.rules.resolve_weapon("CommandoGrenadeLauncher")
        emp = child(weapon, "Warhead@EMPUnit")
        self.assertEqual("AffectsIntegrity", emp.value)
        self.assertEqual("20000", child(emp, "Damage").value)

    def test_nike_damage_is_air_only(self):
        weapon = self.rules.resolve_weapon("Nike")
        main = child(weapon, "Warhead@MissileHE_Heavy")
        self.assertEqual("Air", child(main, "ValidTargets").value)

    def test_cabal_rockets_keep_the_ground_only_legacy_slice(self):
        weapon = self.rules.resolve_weapon("CabalAscendedRockets")
        main = child(weapon, "Warhead@MissileHE_Heavy")
        bonus = child(weapon, "Warhead@MissileHE_HeavyGroundBonus")
        self.assertEqual("Ground, Water, Air", child(main, "ValidTargets").value)
        self.assertEqual("Ground, Water", child(bonus, "ValidTargets").value)
        self.assertEqual("6000", child(bonus, "Damage").value)

    def test_buggy_aa_child_has_functional_air_damage(self):
        weapon = self.rules.resolve_weapon("MachineGunBuggy2_AA")
        main = child(weapon, "Warhead@Bullet_Medium")
        self.assertEqual("Air", child(main, "ValidTargets").value)
        self.assertEqual("6000", child(main, "Damage").value)


if __name__ == "__main__":
    unittest.main()
