"""Focused tests for source-local geometry shape summaries."""
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
import summarize_reference_geometry as summary  # noqa: E402


def field(status, values=None, raw=None, tokens=None):
    return {"status": status, "values": list(values or []), "raw": raw,
            "tokens": list(tokens or [])}


def record(source="Combined Arms", warhead_type="SpreadDamage", *, actor="actor",
           falloff=None, falloff_status="ABSENT", raw_spread="128",
           raw_range=None, geometry_gap=False):
    return {
        "source": source, "actor": actor, "source_actor": "SRC",
        "reference_id": "REF", "slot": "Armament", "weapon": "Gun",
        "warhead": "Warhead@1Dam", "warhead_type": warhead_type,
        "channel_index": 0, "warhead_index": None, "status": "PARTIAL",
        "geometry_gap": geometry_gap,
        "inheritance_status": None,
        "geometry": {
            "spread": field("PRESENT", [128], raw_spread),
            "range": field("ABSENT", raw=raw_range),
            "projectile_range": field("ABSENT"),
            "falloff": field(falloff_status, falloff, raw=falloff),
        },
    }


class SummarizeReferenceGeometryTests(unittest.TestCase):
    def test_falloff_shape_metrics_cover_zero_repeats_and_non_monotonic_values(self):
        metrics = summary.falloff_shape_metrics(field(
            "PRESENT", [100, 50, 50, 75, 0], raw="100, 50, 50, 75, 0"))
        self.assertEqual(metrics["numeric_token_count"], 5)
        self.assertEqual(metrics["first"], 100.0)
        self.assertEqual(metrics["last"], 0.0)
        self.assertEqual(metrics["zero_index"], 4)
        self.assertEqual(metrics["zero_indices"], [4])
        self.assertFalse(metrics["non_increasing"])
        self.assertEqual(metrics["repeated_values"], [50.0])
        self.assertTrue(metrics["has_repeated_values"])

    def test_missing_empty_malformed_and_unparsed_falloff_remain_distinct(self):
        missing = summary.falloff_shape_metrics(field("ABSENT"))
        empty = summary.falloff_shape_metrics(field("EXPLICIT_EMPTY", raw=""))
        malformed = summary.falloff_shape_metrics(field(
            "MALFORMED", [100], raw="100, nope",
            tokens=[{"status": "NUMERIC", "value": 100},
                    {"status": "MALFORMED", "raw": "nope"}]))
        unparsed = summary.falloff_shape_metrics(field(
            "PRESENT_WITH_UNPARSED_TOKENS", [100], raw="100, 0c64",
            tokens=[{"status": "NUMERIC", "value": 100},
                    {"status": "SOURCE_TOKEN_UNPARSED", "raw": "0c64"}]))
        self.assertEqual(missing["field_status"], "ABSENT")
        self.assertIsNone(missing["non_increasing"])
        self.assertEqual(empty["field_status"], "EXPLICIT_EMPTY")
        self.assertEqual(malformed["malformed_token_count"], 1)
        self.assertEqual(unparsed["unparsed_token_count"], 1)
        self.assertEqual(unparsed["numeric_token_count"], 1)

    def test_grouping_preserves_identity_raw_geometry_and_does_not_mutate_input(self):
        data = {"schema": 1, "source_geometry_semantics": {"Combined Arms": {}},
                "records": [
                    record(actor="one", falloff=[100, 50, 0],
                           falloff_status="PRESENT", geometry_gap=True),
                    record(actor="two", falloff=[100, 100],
                           falloff_status="PRESENT", geometry_gap=True),
                    record(source="DTA Enhanced", warhead_type=None, actor="three",
                           falloff_status="EXPLICIT_EMPTY", falloff="", geometry_gap=True),
                ]}
        before = copy.deepcopy(data)
        result = summary.build(data)
        self.assertEqual(result["summary"]["group_count"], 2)
        ca_group = result["groups"]["Combined Arms"]["warhead_types"]["SpreadDamage"]
        first = ca_group["records"][0]
        self.assertEqual(first["identity"]["actor"], "one")
        self.assertEqual(first["identity"]["slot"], "Armament")
        self.assertEqual(first["raw_geometry"]["falloff"], [100, 50, 0])
        self.assertEqual(ca_group["falloff_shape"]["records_with_repeated_values"], 1)
        self.assertEqual(data, before)

    def test_output_guard_rejects_same_paths_and_different_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output = pathlib.Path(temp) / "summary.json"
            markdown = pathlib.Path(temp) / "summary.md"
            summary.diagnostic_output.write_outputs(
                summary.ROOT, {output: "{}\n", markdown: "# summary\n"})
            with self.assertRaises(ValueError):
                summary.diagnostic_output.write_outputs(
                    summary.ROOT, {output: "different\n"})
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    summary.main(["--input", str(output), "--out", str(output),
                                  "--markdown", str(output)])
            self.assertEqual(output.read_text(encoding="utf-8"), "{}\n")
            json.loads(output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
