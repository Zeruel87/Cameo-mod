"""Focused tests for explicit four-voice row assembly."""
import copy
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import explicit_voice_group_assembler as assembler  # noqa: E402
import four_source_synthesis_gate as gate  # noqa: E402


def terms(seed=1):
    return {
        "Light": {"A": seed, "B": seed / 100.0},
        "Heavy": {"A": seed + 1, "B": (seed + 1) / 100.0},
    }


def record(source, actor, *, scenario="vehicle", status="RESOLVED", seed=1,
           identity=None):
    result = {
        "source": source,
        "actor": actor,
        "slot": "Armament",
        "weapon": actor + "-weapon",
        "scenario": scenario,
        "state_key": "base",
        "status": status,
        "terms": terms(seed),
    }
    if identity is not None:
        result["channel_identity"] = copy.deepcopy(identity)
    return result


def datasets():
    return {
        "cameo": [record("Cameo", "cameo-tank", identity={"actor": "cameo-tank"})],
        "ca": [record("Combined Arms", "ca-tank", seed=2)],
        "dta": [record("DTA Enhanced", "dta-tank", seed=3)],
        "ora": [record("OpenRA Red Alert", "ora-tank", seed=4)],
        "td": [record("OpenRA Tiberian Dawn", "td-tank", seed=5)],
    }


def spec(*, sources=("ca", "dta", "ora"), scenario="vehicle", state_key="base"):
    voices = [
        {"voice": assembler.CURRENT_VOICE, "dataset": "cameo", "record_index": 0},
    ]
    for voice, dataset in zip(("Combined Arms", "DTA Enhanced", "OpenRA Red Alert"), sources):
        voices.append({"voice": voice, "dataset": dataset, "record_index": 0})
    return {"comparison_id": "tank/base", "scenario": scenario,
            "state_key": state_key, "voices": voices}


class ExplicitVoiceGroupAssemblerTests(unittest.TestCase):
    def test_explicit_selection_projects_gate_rows_and_preserves_identity(self):
        source = datasets()
        before = copy.deepcopy(source)
        result = assembler.assemble_group(spec(), source)

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual([row["source"] for row in result["source_rows"]], [
            "Current Cameo", "Combined Arms", "DTA Enhanced", "OpenRA Red Alert"])
        self.assertEqual(result["source_rows"][0]["channel_identity"],
                         {"actor": "cameo-tank"})
        self.assertEqual(result["source_rows"][1]["raw_record"], source["ca"][0])
        self.assertEqual(source, before)

    def test_same_actor_does_not_create_an_implicit_join(self):
        source = datasets()
        source["ca"][0]["actor"] = "cameo-tank"
        result = assembler.assemble_group(spec(), source)

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["source_rows"][0]["raw_record"]["actor"], "cameo-tank")
        self.assertEqual(result["source_rows"][1]["raw_record"]["actor"], "cameo-tank")
        self.assertIn("dataset and record_index", result["provenance"]["assembly"])

    def test_missing_duplicate_and_unknown_voices_fail_closed(self):
        missing = spec(sources=("ca", "dta", "td"))
        missing["voices"] = missing["voices"][:-1]
        result = assembler.assemble_group(missing, datasets())
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("voice_row_count:expected=4:actual=3", result["reasons"])
        self.assertIn("reference_voice_count:expected=3:actual=2", result["reasons"])

        duplicate = spec()
        duplicate["voices"][3]["voice"] = "DTA Enhanced"
        duplicate_result = assembler.assemble_group(duplicate, datasets())
        self.assertIn("duplicate_voice:DTA Enhanced", duplicate_result["reasons"])
        self.assertIn("reference_voice_count:expected=3:actual=2", duplicate_result["reasons"])

        unknown = spec()
        unknown["voices"][1]["voice"] = "Unknown"
        unknown_result = assembler.assemble_group(unknown, datasets())
        self.assertIn("unsupported_voice:'Unknown'", unknown_result["reasons"])

    def test_dataset_and_index_errors_retain_unresolved_rows(self):
        bad = spec()
        bad["voices"][1] = {"voice": "Combined Arms", "dataset": "missing", "record_index": 0}
        bad["voices"][2] = {"voice": "DTA Enhanced", "dataset": "dta", "record_index": 9}
        result = assembler.assemble_group(bad, datasets())
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("dataset_missing:'missing'", result["reasons"])
        self.assertIn("record_index_out_of_range:'dta':9", result["reasons"])
        self.assertEqual(result["source_rows"][1]["raw_record"], None)
        self.assertEqual(result["source_rows"][2]["raw_record"], None)

    def test_malformed_dataset_and_source_values_fail_closed(self):
        source = datasets()
        bad = spec()
        bad["voices"][1]["dataset"] = ["ca"]
        source["dta"][0]["source"] = ["DTA Enhanced"]
        result = assembler.assemble_group(bad, source)

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("dataset_invalid:['ca']", result["reasons"])
        self.assertIn("source_mismatch:2:['DTA Enhanced']!='DTA Enhanced'",
                      result["reasons"])

    def test_source_status_terms_and_raw_scenario_are_not_silently_overridden(self):
        source = datasets()
        source["ca"][0]["source"] = "Wrong Source"
        source["dta"][0]["status"] = "UNRESOLVED"
        source["ora"][0].pop("terms")
        result = assembler.assemble_group(spec(), source)

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("source_mismatch:1:'Wrong Source'!='Combined Arms'", result["reasons"])
        self.assertIn("status_not_resolved:2:'UNRESOLVED'", result["reasons"])
        self.assertIn("terms_missing_or_invalid:3", result["reasons"])

        source = datasets()
        mapped = spec(scenario="aircraft")
        for selection in mapped["voices"]:
            selection["record_scenario"] = "vehicle"
        mapped_result = assembler.assemble_group(mapped, source)
        self.assertEqual(mapped_result["status"], "RESOLVED")

    def test_dta_base_status_requires_explicit_whitelisted_alias(self):
        source = datasets()
        source["dta"][0]["status"] = "BASE_CHANNELS_RESOLVED"
        without_alias = assembler.assemble_group(spec(), source)
        self.assertEqual(without_alias["status"], "UNRESOLVED")
        self.assertIn("status_not_resolved:2:'BASE_CHANNELS_RESOLVED'",
                      without_alias["reasons"])

        with_alias = spec()
        with_alias["voices"][2]["status_alias"] = "DTA_BASE_CHANNELS_RESOLVED"
        resolved = assembler.assemble_group(with_alias, source)
        self.assertEqual(resolved["status"], "RESOLVED")
        dta_row = resolved["source_rows"][2]
        self.assertEqual(dta_row["status"], "RESOLVED")
        self.assertEqual(dta_row["raw_status"], "BASE_CHANNELS_RESOLVED")
        self.assertEqual(dta_row["status_basis"]["alias"],
                         "DTA_BASE_CHANNELS_RESOLVED")

    def test_status_alias_is_source_and_status_specific(self):
        source = datasets()
        source["ca"][0]["status"] = "BASE_CHANNELS_RESOLVED"
        wrong_voice = spec()
        wrong_voice["voices"][1]["status_alias"] = "DTA_BASE_CHANNELS_RESOLVED"
        result = assembler.assemble_group(wrong_voice, source)
        self.assertIn("status_alias_voice_mismatch:1:'Combined Arms'", result["reasons"])

        wrong_status = spec()
        wrong_status["voices"][2]["status_alias"] = "DTA_BASE_CHANNELS_RESOLVED"
        source["dta"][0]["status"] = "UNRESOLVED"
        result = assembler.assemble_group(wrong_status, source)
        self.assertIn("status_alias_raw_status_mismatch:2:'UNRESOLVED'!=",
                      " ".join(result["reasons"]))

    def test_malformed_voice_and_explicit_comparison_metadata_fail_closed(self):
        malformed = spec()
        malformed["voices"][1]["voice"] = ["Combined Arms"]
        result = assembler.assemble_group(malformed, datasets())
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("unsupported_voice:['Combined Arms']", result["reasons"])

        mismatched = spec()
        source = datasets()
        source["ca"][0]["comparison_id"] = "other/base"
        result = assembler.assemble_group(mismatched, source)
        self.assertIn("record_comparison_id_mismatch:1", result["reasons"])

    def test_record_selection_duplicates_and_input_immutability(self):
        source = datasets()
        duplicate = spec()
        duplicate["voices"][2]["dataset"] = "ca"
        before = copy.deepcopy(source)
        result = assembler.assemble_group(duplicate, source)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("duplicate_record_selection:1,2", result["reasons"])
        self.assertEqual(source, before)

    def test_resolved_assembly_feeds_the_corrected_voice_gate(self):
        assembled = assembler.assemble_group(spec(), datasets())
        gated = gate.combine_group(
            {
                "comparison_id": assembled["comparison_id"],
                "scenario": assembled["scenario"],
                "state_key": assembled["state_key"],
                "source_rows": assembled["source_rows"],
            },
            scenario_policy=True,
            voice_policy=True,
        )

        self.assertEqual(assembled["status"], "RESOLVED")
        self.assertEqual(gated["status"], "RESOLVED")
        self.assertEqual(gated["sources"], [
            "Current Cameo", "Combined Arms", "DTA Enhanced", "OpenRA Red Alert",
        ])
        self.assertEqual(gated["policy"]["voice_weights"], {
            source: 0.25 for source in gated["sources"]
        })

    def test_batch_is_deterministic_and_retains_partial_results(self):
        source = datasets()
        batch = assembler.assemble_groups([spec(), {"voices": []}], source)
        self.assertEqual(batch["summary"], {"groups": 2, "resolved": 1, "unresolved": 1})
        self.assertEqual(batch["status"], "UNRESOLVED")
        self.assertEqual(batch["groups"][0]["source_rows"][0]["source"], "Current Cameo")


if __name__ == "__main__":
    unittest.main()
