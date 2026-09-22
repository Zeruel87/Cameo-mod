"""Fixture-freshness proof for the CannonAP generated-heaviness fixture.

The committed fixture under tools/tests/fixtures must stay in lockstep with
TWO independent sources:

1. the APPROVED generator command `gen_weapon_template.py --continuous-family
   CannonAP` (its stdout, parsed through the SHARED miniyaml — never a bespoke
   grep), and
2. the Python effective-profile model (tools/balance/effective_heaviness).

If either drifts, this test fails until the fixture is regenerated — the
end-to-end generator/runtime-adapter proof is only sound while the expected
tables are fresh on both sides.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import effective_heaviness as eh  # noqa: E402
from miniyaml import load_text  # noqa: E402

GENERATED = ROOT / "tools/tests/fixtures/cannonap_continuous_generated.yaml"
FIXTURE = ROOT / "tools/tests/fixtures/cannonap_continuous_fixture.json"
HEAVINESS_CASES = [0, 500, 1000, 1500, 2000]
NUMERIC_FIELDS = frozenset({
    "Damage", "Spread", "PercentageScale", "PercentageSpread", "Heaviness",
    "MinRadius", "MaxRadius",
})


def parse_generated_warhead(text):
    nodes = load_text(text)
    weapon = next(n for n in nodes if n.key == "^Warhead_CannonAP")
    warhead = next(n for n in weapon.children if n.key.startswith("Warhead@"))
    fields = {}
    for child in warhead.children:
        if child.children:
            fields[child.key] = {row.key: int(row.value)
                                 for row in child.children}
        elif child.key in NUMERIC_FIELDS:
            fields[child.key] = int(child.value)
        else:
            fields[child.key] = child.value
    return warhead.value, fields


def effective_geometry(fields, heaviness):
    spread_eff = eh.scale_length(fields["Spread"], heaviness)
    falloff_len = len(str(fields["Falloff"]).split(","))
    return {
        "effective_spread": spread_eff,
        "effective_range": [i * spread_eff for i in range(falloff_len)],
        "effective_min_radius": eh.scale_length(fields.get("MinRadius", 0), heaviness),
        "effective_max_radius": eh.scale_length(fields.get("MaxRadius", 0), heaviness),
    }


class CannonAPGeneratedFixtureFreshnessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.warhead_type, cls.authored = parse_generated_warhead(
            GENERATED.read_text(encoding="utf-8"))

    def test_generated_yaml_block_is_the_fixture_parsed_by_shared_miniyaml(self):
        self.assertEqual(self.warhead_type, "AreaDamage")
        self.assertEqual(self.fixture["authored"], self.authored,
                         "the committed fixture's authored block drifted from the "
                         "generator output — regenerate both fixtures")
        for scalar in ("Damage", "Spread", "Heaviness", "PercentageScale",
                       "PercentageSpread"):
            self.assertIsInstance(self.authored[scalar], int, scalar)
        # THE SHARED PROFILE: HeavinessMode is the explicit opt-in and NO
        # percentage table exists — the percentage half follows the flat Versus.
        self.assertEqual(self.authored["HeavinessMode"], "SharedVersus")
        for absent in ("PercentageVersus", "PercentageVersusLight",
                       "PercentageVersusHeavy"):
            self.assertNotIn(absent, self.authored, absent)

    def test_generator_run_reproduces_the_committed_yaml_block(self):
        # The approved command itself (stdout only), not a reimplementation.
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/balance/gen_weapon_template.py"),
             "--continuous-family", "CannonAP"],
            capture_output=True, text=True, check=True, cwd=ROOT)
        _, fresh_authored = parse_generated_warhead(result.stdout)
        self.assertEqual(self.authored, fresh_authored,
                         "the generator output drifted from the committed "
                         "generated fixture — regenerate")

    def test_expected_effective_fields_fresh_from_the_python_model(self):
        versus = self.authored["Versus"]
        for value in HEAVINESS_CASES:
            expected = self.fixture["per_heaviness"][str(value)]
            shared = eh.shared_versus_profile(versus, value)
            self.assertEqual(expected["effective_versus"],
                             shared,
                             f"effectiveVersus at h={value / 1000.0}")
            # THE SHARED PROFILE: the percentage half reads the SAME table.
            self.assertEqual(
                expected["effective_percentage_versus"],
                shared,
                f"effectivePercentageVersus at h={value / 1000.0}")
            geometry = {k: expected[k] for k in (
                "effective_spread", "effective_range",
                "effective_min_radius", "effective_max_radius")}
            self.assertEqual(geometry, effective_geometry(self.authored, value),
                             f"geometry at h={value / 1000.0}")

    def test_disabled_case_fresh_from_the_python_model(self):
        # The disabled contract runs the LEGACY mode (SharedVersus requires an
        # active Heaviness): authored tables verbatim, no percentage table.
        self.assertEqual(self.fixture["disabled"]["effective_versus"],
                         dict(self.authored["Versus"]))
        self.assertEqual(self.fixture["disabled"]["effective_percentage_versus"],
                         dict(self.authored["Versus"]))
        geometry = {k: self.fixture["disabled"][k] for k in (
            "effective_spread", "effective_range",
            "effective_min_radius", "effective_max_radius")}
        self.assertEqual(geometry, effective_geometry(self.authored, eh.DISABLED))

    def test_fixture_covers_every_actual_armor_key_including_shield_plating(self):
        versus = self.authored["Versus"]
        for armor in ("Shield", "HAZMAT", "COMPOSITE", "BLAST", "REFLECTOR",
                      "ARMOR", "Heroic", "Superheavy", "Fighter", "Scout"):
            self.assertIn(armor, versus)
        self.assertEqual(len(versus), 22)
        # THE SHARED PROFILE: the MAIN Versus table is the ONLY profile — the
        # plating/derived armors live here, and no percentage table exists.
        self.assertEqual(len(versus), 22)


if __name__ == "__main__":
    unittest.main()
