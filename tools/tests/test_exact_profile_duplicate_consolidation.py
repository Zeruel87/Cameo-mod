import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_exact_profile_duplicates as cohort
from audit_three_way_split import SPLIT_BASELINE, main_warheads
from miniyaml import Ruleset


class ExactProfileDuplicateConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_converter_is_fully_applied_and_idempotent(self):
        cohort.validate_result()

    def test_selected_definitions_have_one_destination_main(self):
        self.assertEqual(11, len(cohort.SPECS))
        for name, (_old, destination, total, scale) in cohort.SPECS.items():
            resolved = self.rules.resolve_weapon(name)
            self.assertEqual([destination], main_warheads(resolved), name)
            node = next(child for child in resolved.children
                        if child.key == f"Warhead@{destination}")
            self.assertEqual(total, int(str(node.get("Damage"))), name)
            if scale:
                self.assertEqual(scale, int(str(node.get("PercentageScale"))), name)

    def test_separate_percentage_runtime_companions_remain(self):
        expected = {
            "TSPulseCannon_EMP": {
                "Warhead@TeslaWeaponPercentage": 5,
                "Warhead@TeslaChargedWeaponPercentage": 5,
            },
            "TeslaArmorDischargeArc": {
                "Warhead@LightMissilePercentage": 6,
                "Warhead@TeslaWeaponPercentage": 6,
            },
            "TeslaArmorDischargeFragment1": {
                "Warhead@LightMissilePercentage": 3,
                "Warhead@TeslaWeaponPercentage": 3,
            },
            "TeslaArmorDischargeFragment2": {
                "Warhead@LightMissilePercentage": 4,
                "Warhead@TeslaWeaponPercentage": 4,
            },
        }
        for name, companions in expected.items():
            resolved = self.rules.resolve_weapon(name)
            actual = {
                child.key: int(str(child.get("Damage")))
                for child in resolved.children if child.key in companions
            }
            self.assertEqual(companions, actual, name)

        for name in cohort.RA2120_SELECTED:
            keys = {child.key for child in self.rules.resolve_weapon(name).children}
            self.assertIn("Warhead@TankDestroyerCannonPercentage", keys, name)
            self.assertIn("Warhead@ShrapnelWeaponPercentage", keys, name)

    def test_protected_role_branches_are_exact(self):
        self.assertEqual(
            {"CannonChem_HeavyFlatCompatibility", "CannonHE_Heavy", "CannonAP_Light"},
            set(main_warheads(self.rules.resolve_weapon("RA2120xmm_rad"))),
        )
        self.assertEqual(
            {"Flak_MediumFlatCompatibility", "Flak_Medium"},
            set(main_warheads(self.rules.resolve_weapon("AAGunBoatFlak"))),
        )
        self.assertEqual(
            ["Flak_Medium"],
            main_warheads(self.rules.resolve_weapon("RA2FlakTrackAAGun")),
        )

    def test_structural_backlog_ratchet_is_777(self):
        self.assertEqual(114, SPLIT_BASELINE)


if __name__ == "__main__":
    unittest.main()
