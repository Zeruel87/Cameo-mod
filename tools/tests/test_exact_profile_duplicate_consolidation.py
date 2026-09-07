import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_exact_profile_duplicates as cohort
from audit_three_way_split import RAW_SPLIT_BASELINE, main_warheads
from miniyaml import Ruleset
from reviewed_weapon_history import HistoricalView


class ExactProfileDuplicateConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_historical_converter_rejects_the_new_apocalypse_closure(self):
        # Aedis detached fire/Tesla/radiation into explicit canonical roles.
        # Never reattach those families to replay this historical converter.
        with self.assertRaisesRegex(RuntimeError, "RA2120xmm: descendant closure changed"):
            cohort.validate_result()
        self.assertEqual({"RA2120xmm_elite"}, cohort.descendants(self.rules, "RA2120xmm"))
        self.assertEqual(cohort.FLAK_DESCENDANTS, cohort.descendants(self.rules, "RA2FlakTrackGun"))
        self.assertEqual(cohort.TESLA_ARMOR - {"TeslaArmorDischargeArc"},
                         cohort.descendants(self.rules, "TeslaArmorDischargeArc"))
        self.assertEqual(set(), cohort.descendants(self.rules, "TSPulseCannon_EMP"))
        for name, (old_keys, _destination, _total, _scale) in cohort.SPECS.items():
            if name not in cohort.RA2120_SELECTED:
                self.assertEqual(cohort.PRESERVED_HASHES[name],
                                 cohort.resolved_hash(HistoricalView(self, self.rules), name, old_keys), name)
        for name, expected in cohort.BRANCH_HASHES.items():
            if not name.startswith("RA2120xmm"):
                self.assertEqual(expected, cohort.resolved_hash(HistoricalView(self, self.rules), name), name)
        for name, expected in cohort.FLAK_BRANCH_PRESERVED_HASHES.items():
            self.assertEqual(expected, cohort.resolved_hash(
                HistoricalView(self, self.rules), name, {"Flak_Medium", "Flak_MediumFlatCompatibility"}), name)

    def test_selected_definitions_have_one_destination_main(self):
        self.assertEqual(11, len(cohort.SPECS))
        for name, (_old, destination, total, scale) in cohort.SPECS.items():
            if name in cohort.RA2120_SELECTED:
                destination = ("CannonFire_Light" if "_fire" in name else
                               "CannonTesla_Light" if "_tesla" in name else "CannonAP_Light")
                total, scale = 12000, 10000
            resolved = self.rules.resolve_weapon(name)
            self.assertEqual([destination], main_warheads(resolved), name)
            node = next(child for child in resolved.children
                        if child.key == f"Warhead@{destination}")
            self.assertIn(destination, cohort.flat_nodes(resolved), name)
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
            self.assertNotIn("Warhead@TankDestroyerCannonPercentage", keys, name)
            self.assertNotIn("Warhead@ShrapnelWeaponPercentage", keys, name)

    def test_protected_role_branches_are_exact(self):
        expected_flak = {
            "RA2FlakTrackGun_elite": {
                "Flak_MediumFlatCompatibility": (8000, 2488, "Ground, Water")},
            "AAGunBoatFlak": {
                "Flak_Medium": (2000, 10000, "Ground, Water, Air"),
                "Flak_MediumFlatCompatibility": (6000, 0, "Ground, Water")},
            "AAGunBoatFlak_elite": {
                "Flak_Medium": (2000, 10000, "Ground, Water, Air"),
                "Flak_MediumFlatCompatibility": (6000, 0, "Ground, Water")},
        }
        for name, expected in expected_flak.items():
            resolved = self.rules.resolve_weapon(name)
            nodes = cohort.flat_nodes(resolved)
            self.assertEqual(set(expected), set(main_warheads(resolved)), name)
            actual = {key: (int(nodes[key].get("Damage")), int(nodes[key].get("PercentageScale")),
                            nodes[key].get("ValidTargets")) for key in expected}
            self.assertEqual(expected, actual, name)
        self.assertEqual(
            {"CannonChem_Light"},
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
        # Upstream retired exemptions: enforce the raw ceiling, never subtract reviewed stacks.
        self.assertLessEqual(RAW_SPLIT_BASELINE, 322)


if __name__ == "__main__":
    unittest.main()
