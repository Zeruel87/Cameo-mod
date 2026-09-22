"""Focused tests for the fail-closed four-source synthesis gate."""
import copy
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import four_source_synthesis_gate as gate  # noqa: E402


def terms(offset=0):
    return {axis: {"A": 10 + offset + i, "B": 0.01 * (i + 1)}
            for i, axis in enumerate(("None", "Wood", "Concrete", "Light", "Heavy"))}


def row(source, *, scenario="vehicle", state_key="base", status="RESOLVED", offset=0,
        term_values=None, clamped=None, direct=None, ambient=None):
    return {"source": source, "scenario": scenario, "state_key": state_key,
            "status": status,
            "terms": copy.deepcopy(term_values if term_values is not None else terms(offset)),
            "clamped_hp_components": clamped or [], "direct_terms": direct,
            "ambient_terms": ambient, "identity": {"actor": source + "-actor"}}


def group(rows, *, comparison_id="tank/base", scenario="vehicle", state_key="base"):
    return {"comparison_id": comparison_id, "scenario": scenario,
            "state_key": state_key, "source_rows": rows}


SOURCES = list(gate.SOURCES)


def endpoint_terms(light=10, heavy=20, *, include_none=False):
    values = {
        "Light": {"A": light, "B": light / 100.0},
        "Heavy": {"A": heavy, "B": heavy / 100.0},
    }
    if include_none:
        values["None"] = {"A": 4, "B": 0.04}
    return values


def infantry_terms():
    return {
        "None": {"A": 4, "B": 0.04},
        "Light": {"A": 10, "B": 0.10},
    }


class FourSourceGateTests(unittest.TestCase):
    def test_aedis_voice_policy_accepts_cameo_plus_three_explicit_references(self):
        voice_sources = [gate.CURRENT_VOICE, "Combined Arms", "DTA Enhanced",
                         "OpenRA Red Alert"]
        rows = [row(source, term_values=endpoint_terms()) for source in voice_sources]
        result = gate.combine_group(group(rows), voice_policy=True,
                                    scenario_policy=True)

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["sources"], voice_sources)
        self.assertEqual(result["policy"]["current_voice"], gate.CURRENT_VOICE)
        self.assertEqual(result["policy"]["voices"], voice_sources)
        self.assertEqual(result["policy"]["voice_weights"],
                         {source: 0.25 for source in voice_sources})
        self.assertEqual(result["target_axes"], ["Scout", "Light", "Medium",
                                                   "Heavy", "Superheavy"])

    def test_aedis_voice_policy_accepts_tiberian_dawn_as_the_third_reference(self):
        voice_sources = [gate.CURRENT_VOICE, "Combined Arms", "DTA Enhanced",
                         "OpenRA Tiberian Dawn"]
        result = gate.combine_group(
            group([row(source, term_values=endpoint_terms()) for source in voice_sources]),
            voice_policy=True, scenario_policy=True)

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["sources"], voice_sources)
        self.assertNotIn("OpenRA Red Alert", result["sources"])

    def test_aedis_voice_policy_requires_cameo_and_exactly_three_references(self):
        no_cameo = gate.combine_group(
            group([row(source, term_values=endpoint_terms()) for source in SOURCES]),
            voice_policy=True, scenario_policy=True)
        self.assertEqual(no_cameo["status"], "UNRESOLVED")
        self.assertIn("missing_voice:Current Cameo", no_cameo["reasons"])
        self.assertIn("reference_voice_count:expected=3:actual=4", no_cameo["reasons"])

        duplicate = gate.combine_group(
            group([row(gate.CURRENT_VOICE, term_values=endpoint_terms()),
                   row("Combined Arms", term_values=endpoint_terms()),
                   row("Combined Arms", term_values=endpoint_terms(), offset=3),
                   row("DTA Enhanced", term_values=endpoint_terms())]),
            voice_policy=True, scenario_policy=True)
        self.assertEqual(duplicate["status"], "UNRESOLVED")
        self.assertIn("duplicate_reference_voice:Combined Arms", duplicate["reasons"])

    def test_complete_group_requires_opt_in_for_intermediate_axis_interpolation(self):
        g = group([row(source) for source in SOURCES])
        rejected = gate.combine_group(g)
        self.assertEqual(rejected["status"], "UNRESOLVED")
        self.assertEqual(
            set(rejected["reasons"]),
            {f"axes:{source}:missing_common_axes:Scout,Medium,Superheavy"
             for source in SOURCES},
        )
        resolved = gate.combine_group(g, interpolate_vehicle_axes=True)
        self.assertEqual(resolved["status"], "RESOLVED")
        self.assertEqual(resolved["normalized_terms"]["Combined Arms"]["Scout"]["A"],
                         resolved["normalized_terms"]["Combined Arms"]["Light"]["A"])
        self.assertEqual(resolved["normalized_terms"]["Combined Arms"]["Superheavy"]["A"],
                         resolved["normalized_terms"]["Combined Arms"]["Heavy"]["A"])

    def test_missing_source_is_unresolved_without_renormalization(self):
        result = gate.combine_group(group([row(source) for source in SOURCES[:-1]]),
                                    interpolate_vehicle_axes=True)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("missing_source:DTA Enhanced", result["reasons"])

    def test_duplicate_or_unresolved_source_fails_closed(self):
        rows = [row(source) for source in SOURCES]
        rows[-1]["status"] = "BASE_CHANNELS_RESOLVED"
        rows.append(row("Combined Arms", offset=9))
        result = gate.combine_group(group(rows), interpolate_vehicle_axes=True)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("status_not_fully_resolved:DTA Enhanced", result["reasons"])
        self.assertIn("duplicate_source:Combined Arms", result["reasons"])

    def test_unhashable_source_label_fails_closed_instead_of_raising(self):
        rows = [row(source) for source in SOURCES]
        rows[0]["source"] = ["Combined Arms"]
        result = gate.combine_group(group(rows), interpolate_vehicle_axes=True)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("unsupported_source:['Combined Arms']", result["reasons"])
        self.assertIn("missing_source:Combined Arms", result["reasons"])

    def test_scenario_and_state_mismatch_are_explicit(self):
        rows = [row(source) for source in SOURCES]
        rows[1]["state_key"] = "upgrade"
        rows[2]["scenario"] = "infantry"
        result = gate.combine_group(group(rows), interpolate_vehicle_axes=True)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("state_mismatch:OpenRA Red Alert", result["reasons"])
        self.assertIn("scenario_mismatch:OpenRA Tiberian Dawn", result["reasons"])

    def test_components_are_preserved_separately_and_inputs_are_immutable(self):
        clamped = [{"axis": "None", "coefficient": 0.1, "min_hp": 30000}]
        rows = [row(source, clamped=clamped, direct={"None": 4}, ambient={"None": 2})
                for source in SOURCES]
        original = copy.deepcopy(rows)
        result = gate.combine_group(group(rows), interpolate_vehicle_axes=True)
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["components"]["DTA Enhanced"]["clamped_hp_components"], clamped)
        self.assertEqual(result["components"]["Combined Arms"]["direct_terms"], {"None": 4})
        self.assertEqual(result["components"]["OpenRA Red Alert"]["ambient_terms"], {"None": 2})
        self.assertEqual(rows, original)

    def test_means_include_zero_without_missing_source_reweighting(self):
        rows = [row(source, offset=i) for i, source in enumerate(SOURCES)]
        rows[0]["terms"]["None"]["A"] = 0
        result = gate.combine_group(group(rows), interpolate_vehicle_axes=True)
        self.assertEqual(result["status"], "RESOLVED")
        values = [r["terms"]["None"]["A"] for r in rows]
        self.assertEqual(result["means"]["None"]["arithmetic"]["A"], sum(values) / 4)
        self.assertEqual(result["means"]["None"]["geometric"]["A"], 0.0)

    def test_aedis_vehicle_policy_extrapolates_equal_steps(self):
        rows = [row(source, term_values=endpoint_terms()) for source in SOURCES]
        result = gate.combine_group(group(rows), scenario_policy=True)
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["target_axes"], ["Scout", "Light", "Medium", "Heavy", "Superheavy"])
        normalized = result["normalized_terms"][SOURCES[0]]
        self.assertEqual(normalized["Scout"]["A"], 0)
        self.assertEqual(normalized["Light"]["A"], 10)
        self.assertEqual(normalized["Medium"]["A"], 15)
        self.assertEqual(normalized["Heavy"]["A"], 20)
        self.assertEqual(normalized["Superheavy"]["A"], 30)
        self.assertEqual(result["means"]["Medium"]["arithmetic"]["A"], 15)
        self.assertIn("one equal step below Light", result["policy"]["axis_mapping"])

    def test_aedis_aircraft_policy_maps_equal_endpoint_steps(self):
        rows = [row(source, scenario="aircraft", term_values=endpoint_terms())
                for source in SOURCES]
        result = gate.combine_group(group(rows, scenario="aircraft"), scenario_policy=True)
        self.assertEqual(result["status"], "RESOLVED")
        normalized = result["normalized_terms"][SOURCES[0]]
        self.assertEqual(result["target_axes"], ["Fighter", "Bomber", "Helicopter", "Spaceship"])
        self.assertEqual(normalized["Fighter"]["A"], 10)
        self.assertAlmostEqual(normalized["Bomber"]["A"], 13.3333333333)
        self.assertAlmostEqual(normalized["Helicopter"]["A"], 16.6666666667)
        self.assertEqual(normalized["Spaceship"]["A"], 20)
        self.assertAlmostEqual(result["means"]["Bomber"]["arithmetic"]["A"], 13.3333333333)

    def test_aedis_infantry_policy_maps_none_flak_plate(self):
        rows = [row(source, scenario="infantry", term_values=infantry_terms())
                for source in SOURCES]
        result = gate.combine_group(group(rows, scenario="infantry"), scenario_policy=True)
        self.assertEqual(result["status"], "RESOLVED")
        normalized = result["normalized_terms"][SOURCES[0]]
        self.assertEqual(result["target_axes"], ["None", "Flak", "Plate"])
        self.assertEqual(normalized["None"]["A"], 4)
        self.assertEqual(normalized["Flak"]["A"], 7)
        self.assertEqual(normalized["Plate"]["A"], 10)
        self.assertIn("Light maps to Plate", result["policy"]["axis_mapping"])

    def test_scenario_policy_unknown_scenario_and_missing_axis_fail_closed(self):
        unknown_rows = [row(source, scenario="mystery", term_values=endpoint_terms())
                        for source in SOURCES]
        unknown = gate.combine_group(group(unknown_rows, scenario="mystery"),
                                     scenario_policy=True)
        self.assertEqual(unknown["status"], "UNRESOLVED")
        self.assertIn("unsupported_scenario:mystery", unknown["reasons"])

        missing_rows = [row(source, term_values=endpoint_terms()) for source in SOURCES]
        del missing_rows[0]["terms"]["Heavy"]
        missing = gate.combine_group(group(missing_rows), scenario_policy=True)
        self.assertEqual(missing["status"], "UNRESOLVED")
        self.assertIn("axes:Combined Arms:axis_missing:Heavy", missing["reasons"])
        self.assertEqual(missing["target_axes"], ["Scout", "Light", "Medium", "Heavy", "Superheavy"])

    def test_legacy_custom_scenario_remains_accepted_without_policy(self):
        rows = [row(source, scenario="legacy_custom") for source in SOURCES]
        result = gate.combine_group(
            group(rows, scenario="legacy_custom"),
            interpolate_vehicle_axes=True,
            scenario_policy=False,
        )
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["policy"]["scenario_policy"], False)

    def test_group_batch_and_markdown_keep_unresolved_rows(self):
        data = {"groups": [group([row(source) for source in SOURCES]),
                            group([row(source) for source in SOURCES[:-1]],
                                  comparison_id="missing")]}
        before = copy.deepcopy(data)
        result = gate.combine_groups(data["groups"], interpolate_vehicle_axes=True)
        self.assertEqual(result["summary"]["groups"], 2)
        self.assertEqual(result["summary"]["resolved"], 1)
        self.assertEqual(result["summary"]["unresolved"], 1)
        self.assertEqual(data, before)
        markdown = gate.render_markdown(result)
        self.assertIn("tank/base", markdown)
        self.assertIn("missing_source:DTA Enhanced", markdown)


if __name__ == "__main__":
    unittest.main()
