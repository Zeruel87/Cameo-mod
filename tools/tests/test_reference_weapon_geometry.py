"""Focused tests for the reference weapon geometry inventory."""
import copy
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import reference_weapon_geometry as geometry  # noqa: E402


class ReferenceWeaponGeometryTests(unittest.TestCase):
    def test_numeric_and_list_parsing_preserves_raw_and_source_tokens(self):
        spread = geometry.parse_geometry_field(
            "110", present=True, source_field="fields.Spread", kind="scalar")
        self.assertEqual(spread["status"], "PRESENT")
        self.assertEqual(spread["raw"], "110")
        self.assertEqual(spread["values"], [110.0])
        falloff = geometry.parse_geometry_field(
            "100, 50, 0", present=True, source_field="fields.Falloff", kind="list")
        self.assertEqual(falloff["status"], "PRESENT")
        self.assertEqual(falloff["values"], [100.0, 50.0, 0.0])
        range_field = geometry.parse_geometry_field(
            "0, 0c64", present=True, source_field="fields.Range", kind="list",
            allow_cell_tokens=True)
        self.assertEqual(range_field["status"], "PRESENT_WITH_UNPARSED_TOKENS")
        self.assertEqual(range_field["values"], [0.0])
        self.assertEqual(range_field["tokens"][1]["status"], "SOURCE_TOKEN_UNPARSED")

    def test_zero_empty_missing_and_inherited_unresolved_are_distinct(self):
        zero = geometry.parse_geometry_field(
            "0", present=True, source_field="spread", kind="scalar")
        empty = geometry.parse_geometry_field(
            "", present=True, source_field="falloff", kind="list")
        missing = geometry.parse_geometry_field(
            None, present=False, source_field="range", kind="list")
        inherited = geometry.parse_geometry_field(
            None, present=False, source_field="range", kind="list",
            inherited_unresolved=True)
        self.assertEqual(zero["status"], "PRESENT_ZERO")
        self.assertEqual(empty["status"], "EXPLICIT_EMPTY")
        self.assertEqual(missing["status"], "ABSENT")
        self.assertEqual(inherited["status"], "INHERITED_UNRESOLVED")

    def test_source_local_fields_are_not_compared_or_normalized(self):
        openra = geometry.extract_geometry(
            {"fields": {"Range": "0, 0c64", "Spread": "128"}},
            "Combined Arms")
        dta = geometry.extract_geometry(
            {"fields": {"range": "7.2", "projectilerange": "8"}},
            "DTA Enhanced")
        self.assertEqual(openra["range"]["source_field"], "fields.Range")
        self.assertEqual(openra["range"]["values"], [0.0])
        self.assertEqual(dta["range"]["values"], [7.2])
        self.assertEqual(dta["projectile_range"]["values"], [8.0])
        self.assertNotIn("normalized", openra["range"])
        self.assertNotIn("comparison", dta["range"])

    def test_build_extracts_current_and_selected_reference_channels(self):
        matrix = {
            "rows": [{
                "actor": "cameo_actor",
                "cameo_channels": [{
                    "slot": "Armament", "weapon": "CurrentGun",
                    "requires": "cold", "pricing": True,
                    "warheads": [{"tag": "CurrentWH", "type": "AreaDamage",
                                   "spread": "0", "falloff": "100, 0"}],
                }],
                "references": [{
                    "source": "Combined Arms", "id": "TEST",
                    "selected_weapon_channels": [{
                        "source": "combined_arms", "actor": "TEST",
                        "slot": "Armament", "weapon": "RefGun",
                        "warhead": "Warhead@1Dam", "warhead_type": "SpreadDamage",
                        "fields": {"Spread": "128", "Range": "0, 0c64",
                                    "Falloff": "100, 50"},
                    }],
                }],
            }]
        }
        before = copy.deepcopy(matrix)
        result = geometry.build(matrix)
        self.assertEqual(len(result["records"]), 2)
        current = next(r for r in result["records"] if r["source"] == "Cameo")
        reference = next(r for r in result["records"] if r["source"] == "Combined Arms")
        self.assertEqual(current["geometry"]["spread"]["status"], "PRESENT_ZERO")
        self.assertEqual(reference["geometry"]["range"]["status"],
                         "PRESENT_WITH_UNPARSED_TOKENS")
        self.assertEqual(matrix, before)

    def test_malformed_values_are_explicit_and_mark_record_unresolved(self):
        matrix = {"rows": [{
            "actor": "actor", "cameo_channels": [{
                "slot": "Armament", "weapon": "Gun",
                "warheads": [{"tag": "Bad", "type": "AreaDamage",
                               "spread": "not-a-number", "falloff": "100, nope"}],
            }], "references": [],
        }]}
        result = geometry.build(matrix)
        record = result["records"][0]
        self.assertEqual(record["status"], "MALFORMED")
        self.assertEqual(record["geometry"]["spread"]["status"], "MALFORMED")
        self.assertEqual(record["geometry"]["falloff"]["status"], "MALFORMED")
        self.assertTrue(record["geometry_gap"])

    def test_output_paths_are_guarded_and_differing_existing_files_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            output = pathlib.Path(temp) / "review.json"
            markdown = pathlib.Path(temp) / "review.md"
            geometry.diagnostic_output.write_outputs(
                geometry.ROOT, {output: "{}\n", markdown: "# review\n"})
            with self.assertRaises(ValueError):
                geometry.diagnostic_output.write_outputs(
                    geometry.ROOT, {output: "different\n"})
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    geometry.main(["--matrix", str(output), "--out", str(output),
                                   "--markdown", str(output)])
            self.assertEqual(output.read_text(encoding="utf-8"), "{}\n")
            json.loads(output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
