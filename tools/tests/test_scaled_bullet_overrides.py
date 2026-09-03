import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_scaled_bullet_overrides import default_speed_violations, violations
from effective_damage import parse_wdist
from miniyaml import Ruleset
from survey_weapon_structure import weapon_reference_sets


EXPECTED_SPEEDS = {
    "Lunar_Green105mm": 500,
    "Lunar_Green105mm_elite": 600,
    "NaxiAlienPistol": 277,
    "NaxiAlienPistol_elite": 350,
    "UbermenschLaser": 580,
    "UbermenschLaser_elite": 680,
    "AsianPelicanMG": 610,
    "AsianPelicanMG_elite": 710,
    "GoliathMG": 600,
    "SteelVulcan": 666,
    "SteelVulcanResonance": 666,
    "SteelVulcanResonanceBounce1": 333,
    "SteelVulcanResonanceBounce2": 222,
}

EXPECTED_ORDINARY_BULLET_SPEEDS = {
    "ASDFGun2": 4000,
    "BlackWidowPistols": 10000,
    "BlackWidowPistols_elite": 10000,
    "Colt45": 10000,
    "Colt45Cryo": 10000,
    "CryoLightSniper": 10000,
    "Future_Wheel_MG_elite": 4000,
    "NaxiRifleCons_elite": 2000,
    "RA2AWP_elite": 10000,
    "RA2DoublePistols": 10000,
    "RA2DoublePistolsIFV": 10000,
    "RA2DoublePistols_elite": 10000,
    "RA2MP5": 10000,
    "RA2MP5_elite": 10000,
    "SkyHawkChainGun": 4000,
    "TSHarpyMultiClaw": 4000,
    "TSJumpCannon": 4000,
    "TSShadowTeamPistols": 10000,
    "asianalliance_fanatic_shotgun": 4000,
    "asianalliance_fanatic_shotgun_elite": 4000,
    "asianalliance_fanatic_shotgun_upgrade": 4000,
    "naxis_sssoldier_smg": 4000,
    "naxis_sssoldier_smg_elite": 4000,
    "ra1_allies_rifleinfantry_carbine_cryo": 2000,
    "td_gdi_commando_sniper_elite": 10000,
    "td_gdi_shotgunner_shotgun": 4000,
    "tkmsmg": 10000,
}


class ScaledBulletOverrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_reachable_regression_set_is_empty(self):
        self.assertEqual([], violations(self.rules))
        self.assertEqual([], default_speed_violations(self.rules))

    def test_real_bullet_overrides_keep_their_pre_instant_tracer_speeds(self):
        for name, expected in EXPECTED_ORDINARY_BULLET_SPEEDS.items():
            projectile = self.rules.resolve_weapon(name).child("Projectile")
            self.assertEqual("Bullet", projectile.value, name)
            self.assertEqual(str(expected), projectile.get("Speed"), name)

    def test_repaired_closures_use_scaled_bullet_at_expected_speed(self):
        for name, expected in EXPECTED_SPEEDS.items():
            resolved = self.rules.resolve_weapon(name)
            projectile = resolved.child("Projectile")
            self.assertEqual("ScaledBullet", projectile.value, name)
            percentage = int(projectile.get("ProjectileSpeedPercentage"))
            actual = parse_wdist(resolved.get("Range")) * percentage // 100
            self.assertEqual(expected, actual, name)

    def test_unused_ra28inch_remains_out_of_scope(self):
        concrete = {
            name for name in self.rules.weapons
            if not name.startswith("^") and self.rules.resolve_weapon(name) is not None
        }
        _direct, reachable = weapon_reference_sets(self.rules, concrete)
        self.assertNotIn("RA28Inch", reachable)
        resolved = self.rules.resolve_weapon("RA28Inch")
        self.assertEqual("Bullet", resolved.child("Projectile").value)
        self.assertIsNone(resolved.get("Projectile", "Speed"))


if __name__ == "__main__":
    unittest.main()
