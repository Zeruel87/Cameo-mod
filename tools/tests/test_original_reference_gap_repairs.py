from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import assign_references as assignment  # noqa: E402
import reference_distribution as distribution  # noqa: E402


EXPECTED = {
    ("ra2_allies_engineer", "Valiant Shades"): "AENGINEER",
    ("ra2_soviets_engineer", "Valiant Shades"): "SENGINEER",
    ("ra2_soviets_sentrygun", "Mental Omega"): "NALASR",
    ("ra2_soviets_sentrygun", "CnC Reloaded"): "NALASR",
    ("ra2_soviets_sentrygun", "RA2 Reborn"): "NALASR",
    ("ra2_soviets_sentrygun", "Red Resurrection"): "NALASR",
    ("ts_gdi_mobileconstructionvehicle", "Shattered Paradise"): "MCV",
    ("ts_gdi_mobilesensorarray", "Crystallized Nexus"): "LPST",
    ("ts_nod_lightinfantry", "Shattered Paradise"): "ALTNODE1",
    ("ts_nod_lightinfantry", "Twisted Insurrection"): "E1NOD",
    ("ra1_soviets_gatlingtank", "DTA Enhanced"): "SHILKA",
}

# Rows the ALIAS tables must fill — not REFERENCE_OVERRIDES pins, so the override-map
# assertion does not apply; they land through `name_score` alone.
EXPECTED_ALIAS_FILLED = {
    ("ra1_soviets_flamethrower", "OpenRA Red Alert"): "E4",
    ("ts_gdi_lightinfantry", "Shattered Paradise"): "GDIE1",
    ("ts_gdi_lightinfantry", "Crystallized Nexus"): "GASOL",
}

EXPECTED_NAMES = {
    ("Valiant Shades", "AENGINEER"): "Engineer",
    ("Valiant Shades", "SENGINEER"): "Engineer",
    ("Mental Omega", "NALASR"): "Sentry Gun",
    ("CnC Reloaded", "NALASR"): "Soviet Sentry Gun",
    ("RA2 Reborn", "NALASR"): "Soviet Sentry Gun",
    ("Red Resurrection", "NALASR"): "Soviet Sentry Gun",
    ("Shattered Paradise", "MCV"): "GDI MCV",
    ("Crystallized Nexus", "LPST"): "Mobile Sensor Array",
    ("Shattered Paradise", "ALTNODE1"): "Militant",
    ("Twisted Insurrection", "E1NOD"): "Militant",
    ("DTA Enhanced", "SHILKA"): "Quad Tank",
    ("Shattered Paradise", "GDIE1"): "Marine",
    ("Crystallized Nexus", "GASOL"): "Marine",
    ("OpenRA Red Alert", "E4"): "Flame Infantry",
}


class OriginalReferenceGapRepairs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = json.loads(
            (ROOT / "docs/balance/derived/reference_assignment.json").read_text(encoding="utf-8")
        )["assignment"]

    def test_overrides_are_exact_and_present_in_the_generated_assignment(self):
        for key, peer_id in EXPECTED.items():
            self.assertEqual(peer_id, assignment.REFERENCE_OVERRIDES.get(key), key)
            actor, source = key
            self.assertEqual(peer_id, self.saved[actor][source]["id"].upper(), key)
            self.assertEqual("STRONG", self.saved[actor][source]["confidence"], key)

    def test_completed_gaps_have_three_or_more_sources(self):
        for actor in ("ra2_soviets_sentrygun", "ts_gdi_mobileconstructionvehicle",
                      "ts_gdi_mobilesensorarray", "ts_nod_lightinfantry",
                      "ts_gdi_lightinfantry", "ra1_soviets_flamethrower"):
            self.assertGreaterEqual(len(self.saved[actor]), 3, actor)

    def test_alias_rows_land_in_the_generated_assignment(self):
        for (actor, source), peer_id in EXPECTED_ALIAS_FILLED.items():
            self.assertEqual(peer_id, self.saved[actor][source]["id"].upper(), (actor, source))
            self.assertEqual("STRONG", self.saved[actor][source]["confidence"], (actor, source))

    def test_peer_rows_have_the_exact_reviewed_id_and_name(self):
        rows = (distribution.peer_rows() + distribution.peer_variant_rows()
                + distribution.peer_hero_rows())
        index = {(row["source"], str(row.get("id") or "").upper()): row for row in rows}
        for key, name in EXPECTED_NAMES.items():
            self.assertIn(key, index)
            self.assertEqual(name, index[key]["name"], key)

    def test_new_rows_remain_unique_in_the_assignment(self):
        for (actor, source), peer_id in {**EXPECTED, **EXPECTED_ALIAS_FILLED}.items():
            claims = [other for other, refs in self.saved.items()
                      if str(refs.get(source, {}).get("id") or "").upper() == peer_id]
            self.assertEqual([actor], claims, (source, peer_id))

    def test_bot_only_battle_fortress_variant_does_not_steal_the_base_rows(self):
        base = self.saved["ra2_allies_battlefortress"]
        empty = self.saved["ra2_allies_battlefortress_empty"]
        for source in ("Romanov's Vengeance", "Valiant Shades", "CnC Reloaded",
                       "RA2 Reborn", "Red Resurrection"):
            self.assertEqual("BFRT", base[source]["id"].upper(), source)
            self.assertNotEqual("BFRT", empty.get(source, {}).get("id", "").upper(), source)


if __name__ == "__main__":
    unittest.main()
