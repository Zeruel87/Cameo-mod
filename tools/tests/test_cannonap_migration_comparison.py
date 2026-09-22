"""Fail-closed tests for the manual resolved pilot comparison, not balance assertions."""
import copy
import unittest
import pathlib
import sys

import _bootstrap  # noqa: F401
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "balance"))
import compare_cannonap_migration as migration


class PilotComparison(unittest.TestCase):
    def pair(self):
        main = {"__value": "AreaDamage", "Damage": "80000", "Spread": "80",
                "PercentageScale": "10000", "HeavinessMode": "Legacy",
                "Versus": {"Medium": "100"},
                "PercentageVersus": {"Medium": "10"}, "Falloff": "100, 0"}
        before = {"Warhead@CannonAP_Light": main, "ReloadDelay": "160",
                  "Projectile": {"__value": "Bullet", "Speed": "1408"},
                  "Warhead@Effect": {"__value": "CreateEffect", "Explosion": "small"}}
        after = copy.deepcopy(before)
        after["Warhead@CannonAP"] = after.pop("Warhead@CannonAP_Light")
        after["Warhead@CannonAP"].update({"Heaviness": "0", "Spread": "120",
            "HeavinessMode": "SharedVersus", "PercentageScale": "2000",
            "Versus": {"Medium": "120"}})
        del after["Warhead@CannonAP"]["PercentageVersus"]
        return before, after

    def test_intended_changes_pass(self):
        before, after = self.pair()
        self.assertEqual(migration.diff_pilot("RA2sabot", before, after)[1], [])

    def test_nonprofile_fields_cannot_change_or_disappear(self):
        for field in ("Damage", "__value", "Falloff"):
            for remove in (False, True):
                with self.subTest(field=field, remove=remove):
                    before, after = self.pair()
                    if remove:
                        del after["Warhead@CannonAP"][field]
                    else:
                        after["Warhead@CannonAP"][field] = "changed"
                    self.assertTrue(migration.diff_pilot("RA2sabot", before, after)[1])

    def test_shared_mode_requires_the_exact_new_values(self):
        for field, value in (("HeavinessMode", "Legacy"),
                             ("HeavinessMode", "Shared"),
                             ("PercentageScale", "10000"),
                             ("PercentageScale", "2500")):
            with self.subTest(field=field, value=value):
                before, after = self.pair()
                after["Warhead@CannonAP"][field] = value
                self.assertTrue(migration.diff_pilot("RA2sabot", before, after)[1])

    def test_retained_percentage_tables_fail_in_shared_mode(self):
        before, after = self.pair()
        after["Warhead@CannonAP"]["PercentageVersus"] = {"Medium": "10"}
        self.assertTrue(migration.diff_pilot("RA2sabot", before, after)[1])

    def test_projectile_effect_and_new_fields_fail(self):
        for key in ("Projectile", "Warhead@Effect", "Unknown", "Heaviness"):
            with self.subTest(key=key):
                before, after = self.pair()
                after[key] = "unexpected"
                self.assertTrue(migration.diff_pilot("RA2sabot", before, after)[1])
        before, after = self.pair()
        after["Warhead@CannonAP"]["Unknown"] = "unexpected"
        self.assertTrue(migration.diff_pilot("RA2sabot", before, after)[1])

    def test_wrong_heaviness_or_effective_spread_fails(self):
        for field, value in (("Heaviness", "1000"), ("Spread", "122"), ("Spread", "bad")):
            before, after = self.pair()
            after["Warhead@CannonAP"][field] = value
            self.assertTrue(migration.diff_pilot("RA2sabot", before, after)[1])

    def test_unexpected_weapon_is_never_accepted(self):
        before, after = self.pair()
        _, errors = migration.compare({"Other": before}, {"Other": after, "Unexpected": {}})
        self.assertTrue(any("UNEXPECTED legacy change" in e for e in errors))
        self.assertTrue(any("weapon appeared: Unexpected" in e for e in errors))

    def test_rename_only_and_missing_main_fail(self):
        before, after = self.pair()
        after["Warhead@CannonAP"] = copy.deepcopy(before["Warhead@CannonAP_Light"])
        self.assertTrue(migration.diff_pilot("RA2sabot", before, after)[1])
        del after["Warhead@CannonAP"]
        self.assertTrue(migration.diff_pilot("RA2sabot", before, after)[1])

    def test_base_must_exist(self):
        _, errors = migration.compare({}, {})
        self.assertIn("required continuous base missing", errors)


if __name__ == "__main__":
    unittest.main()
