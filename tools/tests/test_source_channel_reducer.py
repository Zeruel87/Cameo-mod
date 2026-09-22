"""Focused tests for explicit source-group channel reduction."""
import copy
import math
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import source_channel_reducer as reducer  # noqa: E402


SOURCE = "OpenRA Red Alert"
COMPARISON = "tank/base"
SCENARIO = "vehicle"
STATE = "base"


def terms(a, b):
    return {"None": {"A": a, "B": b},
            "Light": {"A": a + 1, "B": b + 1}}


def row(*, a=1, b=2, identity=None, status="RESOLVED", source=SOURCE,
        comparison_id=COMPARISON, scenario=SCENARIO, state_key=STATE,
        term_values=None, **evidence):
    result = {
        "source": source,
        "comparison_id": comparison_id,
        "scenario": scenario,
        "state_key": state_key,
        "status": status,
        "terms": copy.deepcopy(term_values if term_values is not None else terms(a, b)),
    }
    if identity is not None:
        result["channel_identity"] = copy.deepcopy(identity)
    result.update(copy.deepcopy(evidence))
    return result


def reduce_rows(rows, *, source=SOURCE, comparison_id=COMPARISON,
                scenario=SCENARIO, state_key=STATE):
    return reducer.reduce_source_group(rows, source, comparison_id, scenario, state_key)


class SourceChannelReducerTests(unittest.TestCase):
    def test_two_resolved_rows_sum_a_and_b_without_normalization(self):
        rows = [row(a=10, b=0.1, identity={"channel": "main"}),
                row(a=3, b=0.2, identity={"channel": "payload"})]

        result = reduce_rows(rows)

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["aggregation"], "explicit_source_group_sum")
        self.assertEqual(result["terms"], {
            "None": {"A": 13.0, "B": 0.30000000000000004,
                      "flat": 13.0, "max_hp_fraction": 0.30000000000000004},
            "Light": {"A": 15.0, "B": 2.3,
                       "flat": 15.0, "max_hp_fraction": 2.3},
        })
        self.assertEqual(result["source"], SOURCE)
        self.assertEqual(result["comparison_id"], COMPARISON)
        self.assertEqual(result["scenario"], SCENARIO)
        self.assertEqual(result["state_key"], STATE)
        self.assertEqual(result["provenance"]["aggregation"], reducer.AGGREGATION)

    def test_zero_terms_are_valid_and_aliases_are_accepted(self):
        result = reduce_rows([row(identity="zero", term_values={
            "None": {"flat": 0, "max_hp_fraction": 0},
            "Light": {"flat": 0.0, "max_hp_fraction": 0.0},
        })])

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["terms"]["None"]["A"], 0.0)
        self.assertEqual(result["terms"]["None"]["B"], 0.0)
        self.assertEqual(result["terms"]["Light"]["A"], 0.0)
        self.assertEqual(result["terms"]["Light"]["B"], 0.0)

    def test_mismatched_group_metadata_fails_closed(self):
        rows = [row(identity="first"), row(identity="second", state_key="upgrade")]

        result = reduce_rows(rows)

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["terms"])
        self.assertIn("state_key_mismatch:1:'upgrade'", result["reasons"])

    def test_duplicate_channel_identity_fails_closed(self):
        rows = [row(identity={"actor": "M1", "weapon": "Gun"}),
                row(identity={"weapon": "Gun", "actor": "M1"}, a=4)]

        result = reduce_rows(rows)

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["terms"])
        self.assertIn("duplicate_channel_identity:0,1", result["reasons"])

    def test_unresolved_input_row_is_not_summed(self):
        result = reduce_rows([row(identity="good"), row(identity="bad", status="UNRESOLVED")])

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["terms"])
        self.assertIn("status_not_resolved:1:'UNRESOLVED'", result["reasons"])

    def test_missing_negative_nonfinite_and_bool_terms_fail_closed(self):
        cases = (
            ("missing", {"None": {"A": 1}}, "term_missing:0:None.B"),
            ("negative", {"None": {"A": -1, "B": 0}}, "term_negative:0:None.A"),
            ("nonfinite", {"None": {"A": math.inf, "B": 0}}, "term_nonfinite:0:None.A"),
            ("bool", {"None": {"A": True, "B": 0}}, "term_bool:0:None.A"),
        )
        for name, term_values, expected_reason in cases:
            with self.subTest(name=name):
                result = reduce_rows([row(identity=name, term_values=term_values)])
                self.assertEqual(result["status"], "UNRESOLVED")
                self.assertIsNone(result["terms"])
                self.assertIn(expected_reason, result["reasons"])

    def test_axis_set_mismatch_fails_closed(self):
        rows = [row(identity="first"), row(identity="second", term_values={
            "None": {"A": 1, "B": 2},
            "Heavy": {"A": 3, "B": 4},
        })]

        result = reduce_rows(rows)

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["terms"])
        self.assertTrue(any(reason.startswith("axes_mismatch:1:")
                            for reason in result["reasons"]))

    def test_clamped_direct_and_ambient_evidence_are_flattened_and_kept_separate(self):
        clamped_first = [{"axis": "None", "coefficient": 0.1}]
        clamped_second = [{"axis": "Light", "coefficient": 0.2}]
        direct_first = [{"identity": "d1"}, [{"identity": "d2"}]]
        ambient_second = [{"identity": "a1"}]
        rows = [row(identity="first", a=10, b=1,
                    clamped_hp_components=clamped_first,
                    direct_components=direct_first),
                row(identity="second", a=5, b=2,
                    clamped_hp_components=clamped_second,
                    ambient_components=ambient_second)]
        before = copy.deepcopy(rows)

        result = reduce_rows(rows)

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["terms"]["None"]["A"], 15.0)
        self.assertEqual(result["terms"]["None"]["B"], 3.0)
        self.assertEqual(result["clamped_hp_components"], clamped_first + clamped_second)
        self.assertEqual(result["direct_components"], [{"identity": "d1"}, {"identity": "d2"}])
        self.assertEqual(result["ambient_components"], ambient_second)
        self.assertEqual(result["input_rows"], rows)
        self.assertEqual(result["input_rows"], before)
        self.assertNotEqual(result["direct_components"], result["ambient_components"])
        self.assertEqual(result["provenance"]["selection"],
                         "caller-supplied already-selected rows")

        result["input_rows"][0]["terms"]["None"]["A"] = 999
        self.assertEqual(rows, before)

    def test_empty_and_non_list_inputs_fail_closed(self):
        for supplied in ([], (row(identity="tuple"),)):
            with self.subTest(input_type=type(supplied).__name__):
                result = reduce_rows(supplied)
                self.assertEqual(result["status"], "UNRESOLVED")
                self.assertIsNone(result["terms"])
        self.assertIn("rows_empty", reduce_rows([])["reasons"])
        self.assertIn("rows_not_list", reduce_rows((row(identity="tuple"),))["reasons"])

    def test_non_object_row_is_retained_and_rejected(self):
        result = reduce_rows([row(identity="good"), "not-a-row"])

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["terms"])
        self.assertIn("row_not_object:1", result["reasons"])
        self.assertEqual(result["input_rows"][1], "not-a-row")


if __name__ == "__main__":
    unittest.main()
