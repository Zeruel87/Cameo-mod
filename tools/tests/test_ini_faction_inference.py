"""Focused ownership/buildability contracts for the INI reference extractor."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
import extract_ini_units as extractor  # noqa: E402


class IniFactionInferenceTest(unittest.TestCase):
    def test_side_alias_and_house_exclusion_are_applied_without_fallback(self):
        countries = {"USA", "UK", "USSR"}
        side_map = {"Allies": {"USA", "UK"}}
        owner = extractor._direct_owner(
            {"Owner": "Allies", "ForbiddenHouses": "UK"}, countries, side_map)
        self.assertTrue(owner.known)
        self.assertEqual(set(owner.owners), {"USA"})

    def test_generic_prerequisite_unions_alternatives_and_intersects_conjunctions(self):
        ini = {
            "FACT": {"Owner": "USA"},
            "SOV": {"Owner": "USSR"},
            "UNIT": {"Prerequisite": "GENERIC,FACT"},
        }
        owners = extractor._resolve_owner(
            "UNIT", ini, {"USA", "USSR"}, set(ini), {}, {"GENERIC": ["FACT", "SOV"]})
        self.assertEqual(set(owners.owners), {"USA"})

    def test_universal_alternative_is_not_narrowed_to_specific_alternative(self):
        ini = {
            "ALL": {"Owner": "USA,USSR"},
            "USAFACT": {"Owner": "USA"},
            "UNIT": {"Prerequisite": "GENERIC"},
        }
        result = extractor._resolve_owner(
            "UNIT", ini, {"USA", "USSR"}, set(ini), {}, {"GENERIC": ["ALL", "USAFACT"]})
        self.assertEqual(set(result.owners), {"USA", "USSR"})
        self.assertTrue(result.known)

    def test_excluded_owner_does_not_reappear_through_prerequisites(self):
        ini = {
            "BARRACKS": {"Owner": "USA"},
            "UNIT": {"Owner": "USA", "ForbiddenHouses": "USA", "Prerequisite": "BARRACKS"},
        }
        rows = extractor.extract_rows_from_ini(
            {"InfantryTypes": {"0": "UNIT"}, "BuildingTypes": {"0": "BARRACKS"},
             "Countries": {"0": "USA"}, **ini},
            "Synthetic", "ra2")
        self.assertEqual(rows[0]["owners"], [])
        self.assertFalse(rows[0]["buildable"])

    def test_blocked_prerequisite_does_not_fall_back_to_direct_owner(self):
        ini = {
            "BARRACKS": {"Owner": "USSR"},
            "UNIT": {"Owner": "USA", "Prerequisite": "BARRACKS"},
        }
        rows = extractor.extract_rows_from_ini(
            {"InfantryTypes": {"0": "UNIT"}, "BuildingTypes": {"0": "BARRACKS"},
             "Countries": {"0": "USA", "1": "USSR"}, **ini}, "Synthetic", "ra2")
        self.assertEqual(rows[0]["owners"], [])
        self.assertFalse(rows[0]["buildable"])

    def test_inferred_universal_owner_is_filtered_by_required_houses(self):
        ini = {
            "ALLFACT": {"Owner": "USA,USSR"},
            "FACTORY": {"Prerequisite": "ALLFACT", "RequiredHouses": "USA"},
            "UNIT": {"Prerequisite": "FACTORY"},
        }
        rows = extractor.extract_rows_from_ini(
            {"BuildingTypes": {"0": "FACTORY", "1": "ALLFACT"},
             "InfantryTypes": {"0": "UNIT"},
             "Countries": {"0": "USA", "1": "USSR"}, **ini}, "Synthetic", "ra2")
        factory = next(row for row in rows if row["id"] == "FACTORY")
        self.assertEqual(factory["owners"], ["USA"])
        unit = next(row for row in rows if row["id"] == "UNIT")
        self.assertEqual(unit["owners"], ["USA"])

    def test_required_houses_completely_forbidden_is_not_buildable(self):
        ini = {"UNIT": {"RequiredHouses": "USA", "ForbiddenHouses": "USA",
                          "Prerequisite": "UNRESOLVED_TOKEN"}}
        rows = extractor.extract_rows_from_ini(
            {"InfantryTypes": {"0": "UNIT"}, "Countries": {"0": "USA"}, **ini},
            "Synthetic", "ra2")
        self.assertEqual(rows[0]["owners"], [])
        self.assertFalse(rows[0]["buildable"])

    def test_known_direct_owner_beats_broader_house_fallback(self):
        ini = {"UNIT": {"Owner": "USA", "RequiredHouses": "USA,UK",
                          "Prerequisite": "UNRESOLVED_TOKEN"}}
        rows = extractor.extract_rows_from_ini(
            {"InfantryTypes": {"0": "UNIT"}, "Countries": {"0": "USA", "1": "UK"}, **ini},
            "Synthetic", "ra2")
        self.assertEqual(rows[0]["owners"], ["USA"])

    def test_buildability_requires_a_production_claim(self):
        ini = {
            "InfantryTypes": {"0": "REAL", "1": "DECOR"},
            "BuildingTypes": {"0": "BARRACKS"},
            "Countries": {"0": "USA"},
            "REAL": {"Owner": "USA", "Prerequisite": "BARRACKS", "Strength": "100",
                     "Cost": "100", "Primary": "GUN"},
            "DECOR": {"Strength": "100000", "Cost": "1000000", "Primary": "GUN"},
            "GUN": {"Damage": "1", "ROF": "1", "Warhead": "WH"},
            "WH": {"Verses": "100,100,100,100,100,100,100,100,100,100,100"},
            "BARRACKS": {"Owner": "USA"},
        }
        rows = extractor.extract_rows_from_ini(ini, "Synthetic", "ra2")
        buildable = {row["id"]: row["buildable"] for row in rows}
        self.assertEqual(buildable, {"REAL": True, "DECOR": False, "BARRACKS": True})


if __name__ == "__main__":
    unittest.main()
