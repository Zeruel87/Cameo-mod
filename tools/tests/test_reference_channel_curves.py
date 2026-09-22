"""Synthetic tests for per-slot source channel curve reduction."""
import contextlib
import copy
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import armor_projection  # noqa: E402
import reference_channel_curves as curves  # noqa: E402


def channel(slot="Armament", *, source="combined_arms", actor="TEST", weapon="Gun",
            warhead="Warhead@1Dam", kind="SpreadDamage", damage="100",
            fields=None, versus=None, fallback=100, requires_condition=None,
            pause_on_condition=None):
    return {
        "source": source, "actor": actor, "slot": slot, "weapon": weapon,
        "warhead": warhead, "warhead_type": kind, "damage": damage,
        "fields": fields if fields is not None else {"ValidTargets": "Ground"},
        "declared_versus": versus if versus is not None else {
            "None": 100, "Wood": 100, "Concrete": 100, "Light": 100, "Heavy": 100},
        "undeclared_armor_multiplier": fallback,
        "requires_condition": requires_condition, "pause_on_condition": pause_on_condition,
    }


def select(rows, *, source="Combined Arms", scenario="vehicle",
           mode="collateral"):
    return armor_projection.select_channels(
        rows,
        active_slots={row["slot"] for row in rows},
        target_types=curves.scenario_target_types(source, scenario),
        relationship="Enemy",
        default_valid_targets=curves.DEFAULT_VALID_TARGETS,
        default_invalid_targets=curves.DEFAULT_INVALID_TARGETS,
        default_valid_relationships=curves.DEFAULT_VALID_RELATIONSHIPS,
        default_invalid_relationships=curves.DEFAULT_INVALID_RELATIONSHIPS,
        weapon_valid_target_mode=mode,
    )


class ChannelCurveTests(unittest.TestCase):
    def _matched_percentage_proof(self):
        return {"status": "MATCHED", "default": 100,
                "evidence_path": "docs/reference/openra_percentage_armor_evidence.json",
                "evidence_sha256": "evidence", "health_percentage_source_path":
                "OpenRA.Mods.Common/Warheads/HealthPercentageDamageWarhead.cs",
                "health_percentage_source_sha256": curves.PERCENTAGE_SOURCE_SHA256,
                "source": "Combined Arms", "engine_commit": "fixture",
                "base_class_hashes": {"DamageWarhead.cs": "damage",
                                       "TargetDamageWarhead.cs": "target"},
                "derivation": "fixture proof"}

    def _matched_clamped_proof(self):
        return {"status": "MATCHED", "default": 100,
                "evidence_path": "docs/reference/ca_clamped_percentage_evidence.json",
                "evidence_sha256": "clamped-evidence", "source": "Combined Arms",
                "source_commit": curves.CLAMPED_PERCENTAGE_SOURCE_COMMIT,
                "source_path": curves.CLAMPED_PERCENTAGE_SOURCE_PATH,
                "git_blob": curves.CLAMPED_PERCENTAGE_GIT_BLOB,
                "warhead_type": curves.CLAMPED_PERCENTAGE_TYPE,
                "derivation": "fixture proof"}

    def test_clamped_component_caps_then_floors_without_changing_affine_terms(self):
        flat = channel(damage="300")
        clamped = channel(kind="HealthPercentageSpreadDamage", damage="100",
                          warhead="Warhead@Clamp", fields={
                              "ValidTargets": "Ground", "MinReferenceHp": "30000",
                              "MaxReferenceHp": "60000", "Falloff": "100, 50"})
        before = copy.deepcopy([flat, clamped])
        result = curves.reduce_selected_channels(
            [flat, clamped], clamped_percentage_default=self._matched_clamped_proof())
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["terms"]["None"]["A"], 300)
        self.assertEqual(result["terms"]["None"]["B"], 0)
        self.assertEqual(len(result["clamped_hp_components"]), 5)
        component = result["clamped_hp_components"][0]
        self.assertEqual(component["coefficient"], 1.0)
        self.assertEqual(component["min_hp"], 30000)
        self.assertEqual(component["max_hp"], 60000)
        self.assertEqual([curves.evaluate_nominal(
            result["terms"], hp, clamped_hp_components=result["clamped_hp_components"])
            for hp in (10000, 45000, 100000)], [30300, 45300, 60300])
        self.assertEqual([curves.evaluate_nominal(
            {"None": {"A": 0, "B": 0}}, hp,
            clamped_hp_components=result["clamped_hp_components"])
            for hp in (10000, 45000, 100000)], [30000, 45000, 60000])
        self.assertEqual([flat, clamped], before)

    def test_clamped_nonpositive_bounds_are_explicitly_disabled(self):
        clamped = channel(kind="HealthPercentageSpreadDamage", damage="100", fields={
            "ValidTargets": "Ground", "MinReferenceHp": "0", "MaxReferenceHp": "-1"})
        result = curves.reduce_selected_channels(
            [clamped], clamped_percentage_default=self._matched_clamped_proof())
        self.assertEqual(result["status"], "RESOLVED")
        component = result["clamped_hp_components"][0]
        self.assertIsNone(component["min_hp"])
        self.assertIsNone(component["max_hp"])
        self.assertEqual(component["min_status"], "disabled_nonpositive")
        self.assertEqual(component["max_status"], "disabled_nonpositive")
        self.assertEqual(curves.evaluate_nominal(
            result["terms"], 12345, clamped_hp_components=result["clamped_hp_components"]), 12345)

    def test_clamped_explicit_zero_versus_precedes_default(self):
        clamped = channel(kind="HealthPercentageSpreadDamage", damage="100",
                          versus={"Light": 0}, fields={"ValidTargets": "Ground"})
        result = curves.reduce_selected_channels(
            [clamped], clamped_percentage_default=self._matched_clamped_proof())
        by_axis = {row["axis"]: row for row in result["clamped_hp_components"]}
        self.assertEqual(by_axis["Light"]["coefficient"], 0.0)
        self.assertEqual(by_axis["None"]["coefficient"], 1.0)

    def test_clamped_mismatched_proof_or_source_withholds_component(self):
        clamped = channel(kind="HealthPercentageSpreadDamage", damage="100")
        mismatch = curves.reduce_selected_channels([clamped], clamped_percentage_default={
            "status": "UNRESOLVED", "reason": "clamped_percentage_evidence_unproven:hash_mismatch"})
        self.assertEqual(mismatch["status"], "UNRESOLVED")
        self.assertIsNone(mismatch["terms"])
        self.assertIsNone(mismatch["clamped_hp_components"])
        foreign = dict(clamped, source="openra_ra")
        foreign_result = curves.reduce_selected_channels(
            [foreign], clamped_percentage_default=self._matched_clamped_proof())
        self.assertEqual(foreign_result["status"], "UNRESOLVED")
        self.assertIn("unsupported_source_for_clamped_warhead", foreign_result["reason"])

    def test_matched_percentage_proof_supplies_missing_armor_at_100(self):
        percentage = channel(kind="HealthPercentageDamage", damage="6", versus={"Light": 1},
                             fallback=None, fields={"ValidTargets": "Infantry"})
        before = copy.deepcopy(percentage)
        result = curves.reduce_selected_channels(
            [percentage], percentage_default=self._matched_percentage_proof())
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["terms"]["None"]["B"], 0.06)
        self.assertEqual(result["terms"]["Light"]["B"], 0.0006)
        evidence = result["channel_terms"][0]["percentage_default_evidence"]
        self.assertIn("None", evidence["axes_defaulted"])
        self.assertNotIn("Light", evidence["axes_defaulted"])
        self.assertEqual(percentage, before)

    def test_mismatched_percentage_proof_withholds_missing_armor(self):
        percentage = channel(kind="HealthPercentageDamage", damage="6", versus={"Light": 1},
                             fallback=None, fields={"ValidTargets": "Infantry"})
        result = curves.reduce_selected_channels([percentage], percentage_default={
            "status": "UNRESOLVED", "reason": "percentage_armor_default_unproven:hash_mismatch"})
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("percentage_armor_default_unproven:hash_mismatch", result["reason"])
        self.assertIsNone(result["terms"])

    def test_explicit_zero_versus_precedes_matched_percentage_default(self):
        percentage = channel(kind="HealthPercentageDamage", damage="6", versus={"Light": 0},
                             fallback=None, fields={"ValidTargets": "Infantry"})
        result = curves.reduce_selected_channels(
            [percentage], percentage_default=self._matched_percentage_proof())
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["terms"]["Light"]["B"], 0.0)
        self.assertEqual(result["terms"]["None"]["B"], 0.06)

    def test_percentage_proof_requires_both_retained_base_class_hashes(self):
        evidence = {"undeclared_armor_multiplier": 100,
                    "source_bindings": {"Combined Arms": {
                        "engine_commit": "fixture", "damage_warhead_sha256": "damage",
                        "target_damage_sha256": "target"}},
                    "health_percentage_source_sha256": curves.PERCENTAGE_SOURCE_SHA256,
                    "health_percentage_source_path": curves.PERCENTAGE_SOURCE_PATH}
        matrix = {"export_sha256": {"Combined Arms": {"engine_default_proof": {"files": {
            r"OpenRA.Mods.Common\Warheads\DamageWarhead.cs": "damage",
            r"OpenRA.Mods.Common\Warheads\TargetDamageWarhead.cs": "target"}}}}}
        with patch.object(curves, "_sha256", return_value="evidence"):
            proof, reason = curves.percentage_default_proof(matrix, "Combined Arms", evidence)
        self.assertIsNone(reason)
        self.assertEqual(proof["status"], "MATCHED")
        matrix["export_sha256"]["Combined Arms"]["engine_default_proof"]["files"][
            r"OpenRA.Mods.Common\Warheads\TargetDamageWarhead.cs"] = "changed"
        with patch.object(curves, "_sha256", return_value="evidence"):
            proof, reason = curves.percentage_default_proof(matrix, "Combined Arms", evidence)
        self.assertIsNone(proof)
        self.assertIn("base_class_hash_mismatch", reason)

    def test_mixed_flat_and_percentage_terms_use_their_distinct_bases(self):
        flat = channel(fields={"ValidTargets": "Ground", "Falloff": "50, 20"},
                       damage="300", versus={"None": 200, "Wood": 100, "Concrete": 100,
                                               "Light": 50, "Heavy": 0})
        percentage = channel(fields={"ValidTargets": "Infantry"}, kind="HealthPercentageDamage",
                             warhead="Warhead@Perc", damage="6", versus={
                                 "None": 100, "Wood": 100, "Concrete": 100, "Light": 100, "Heavy": 100})
        picked = select([flat, percentage], scenario="infantry")["selected"]
        result = curves.reduce_selected_channels(picked)
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["clamped_hp_components"], [])
        self.assertEqual(result["terms"]["None"]["A"], 300)
        self.assertEqual(result["terms"]["None"]["B"], 0.06)
        percentage_term = next(item for item in result["channel_terms"]
                               if item["warhead_type"] == "HealthPercentageDamage")
        self.assertEqual(percentage_term["base_max_hp_fraction"], 0.06)
        self.assertEqual(result["terms"]["Light"]["A"], 75)
        self.assertEqual(result["terms"]["Heavy"]["A"], 0)

    def test_percentage_channel_is_excluded_from_vehicle_scenario(self):
        flat = channel(damage="300")
        percentage = channel(kind="HealthPercentageDamage", warhead="Warhead@Perc", damage="6",
                             fields={"ValidTargets": "Infantry"})
        result = select([flat, percentage], scenario="vehicle")
        self.assertEqual(result["selected"], [flat])
        self.assertEqual(result["excluded"][0]["reason"], "warhead_valid_targets_no_overlap")
        reduced = curves.reduce_selected_channels(result["selected"])
        self.assertTrue(all(axis["B"] == 0 for axis in reduced["terms"].values()))

    def test_alternate_slots_are_reduced_separately_and_never_summed(self):
        cold = channel("Armament@GROUND", damage="300",
                       fields={"ValidTargets": "Ground"},
                       requires_condition="gattling-ground < 14")
        warm = channel("Armament@GROUND2", damage="300",
                       fields={"ValidTargets": "Ground"},
                       requires_condition="gattling-ground >= 14")
        cold_pick = armor_projection.select_channels(
            [cold, warm], active_slots={cold["slot"]}, target_types={"Ground"}, relationship="Enemy",
            default_valid_targets={"Ground", "Water"}, default_invalid_targets=set(),
            default_valid_relationships={"Ally", "Neutral", "Enemy"},
            default_invalid_relationships=set(), weapon_valid_target_mode="collateral")
        warm_pick = armor_projection.select_channels(
            [cold, warm], active_slots={warm["slot"]}, target_types={"Ground"}, relationship="Enemy",
            default_valid_targets={"Ground", "Water"}, default_invalid_targets=set(),
            default_valid_relationships={"Ally", "Neutral", "Enemy"},
            default_invalid_relationships=set(), weapon_valid_target_mode="collateral")
        self.assertEqual(cold_pick["selected"], [cold])
        self.assertEqual(warm_pick["selected"], [warm])
        self.assertEqual(curves.reduce_selected_channels(cold_pick["selected"])["terms"]["None"]["A"], 300)
        self.assertEqual(curves.reduce_selected_channels(warm_pick["selected"])["terms"]["None"]["A"], 300)

    def test_zero_versus_is_honored_while_missing_fallback_is_unresolved(self):
        zero = channel(kind="TargetDamage", damage="10", versus={"Light": 0}, fallback=100)
        zero_result = curves.reduce_selected_channels([zero])
        self.assertEqual(zero_result["status"], "RESOLVED")
        self.assertEqual(zero_result["terms"]["Light"]["A"], 0)
        self.assertEqual(zero_result["terms"]["None"]["A"], 10)
        lowercase = channel(kind="TargetDamage", damage="10", versus={"light": 0}, fallback=100)
        lowercase_result = curves.reduce_selected_channels([lowercase])
        self.assertEqual(lowercase_result["status"], "RESOLVED")
        self.assertEqual(lowercase_result["terms"]["Light"]["A"], 10)
        missing = channel(kind="TargetDamage", damage="10", versus={"Light": 50}, fallback=None)
        missing_result = curves.reduce_selected_channels([missing])
        self.assertEqual(missing_result["status"], "UNRESOLVED")
        self.assertIn("versus_unresolved:None", missing_result["reason"])

    def test_unsupported_positive_is_unresolved_but_target_excluded_is_not_applicable(self):
        unsupported = channel(kind="FireShrapnel", damage="100")
        selected = select([unsupported], scenario="vehicle")
        unresolved = curves.reduce_selected_channels(selected["selected"])
        self.assertEqual(unresolved["status"], "UNRESOLVED")
        self.assertIn("unsupported_positive_warhead_type", unresolved["reason"])
        excluded = channel(kind="FireShrapnel", damage="100",
                           fields={"ValidTargets": "Infantry"})
        not_applicable = select([excluded], scenario="vehicle")
        self.assertEqual(not_applicable["selected"], [])
        self.assertEqual(curves.reduce_selected_channels(not_applicable["selected"])["status"],
                         "NOT_APPLICABLE")

    def test_negative_healing_and_nonfinite_values_are_unresolved(self):
        healing = channel(kind="TargetDamage", damage="-500")
        self.assertEqual(curves.reduce_selected_channels([healing])["status"], "UNRESOLVED")
        self.assertIn("healing_or_negative_damage",
                      curves.reduce_selected_channels([healing])["reason"])
        nan_damage = channel(damage="nan")
        inf_versus = channel(kind="TargetDamage", damage="10", versus={"None": "inf"}, fallback=100)
        self.assertIn("damage_nonfinite", curves.reduce_selected_channels([nan_damage])["reason"])
        self.assertIn("versus_nonfinite", curves.reduce_selected_channels([inf_versus])["reason"])

    def test_ra_ground_and_air_masks_select_explicit_overrides(self):
        ground = channel(source="openra_ra", actor="E1", weapon="M1", slot="Armament",
                         fields={"ValidTargets": "GroundActor"})
        air = channel(source="openra_ra", actor="YAK", weapon="Gun", slot="Armament",
                      fields={"ValidTargets": "AirborneActor"})
        ground_pick = armor_projection.select_channels(
            [ground], active_slots={"Armament"},
            target_types=curves.scenario_target_types("OpenRA Red Alert", "infantry"),
            relationship="Enemy", default_valid_targets={"Ground", "Water"},
            default_invalid_targets=set(), default_valid_relationships={"Ally", "Neutral", "Enemy"},
            default_invalid_relationships=set(), weapon_valid_target_mode="collateral")
        air_pick = armor_projection.select_channels(
            [air], active_slots={"Armament"},
            target_types=curves.scenario_target_types("OpenRA Red Alert", "small_aircraft"),
            relationship="Enemy", default_valid_targets={"Ground", "Water"},
            default_invalid_targets=set(), default_valid_relationships={"Ally", "Neutral", "Enemy"},
            default_invalid_relationships=set(), weapon_valid_target_mode="collateral")
        self.assertEqual(ground_pick["selected"], [ground])
        self.assertEqual(air_pick["selected"], [air])

    def test_source_specific_ship_masks_select_surface_water_and_exclude_submerged(self):
        ca_surface = channel("Armament@SHIP", fields={"ValidTargets": "Water"})
        ca_submerged = channel("Armament@SUB", fields={"ValidTargets": "Underwater"})
        ca = select([ca_surface, ca_submerged], source="Combined Arms", scenario="ship")
        self.assertEqual(ca["selected"], [ca_surface])
        self.assertEqual(ca["excluded"][0]["reason"], "warhead_valid_targets_no_overlap")

        ra_surface = channel("Armament@SHIP", fields={"ValidTargets": "WaterActor"})
        ra = select([ra_surface], source="OpenRA Red Alert", scenario="ship")
        self.assertEqual(ra["selected"], [ra_surface])

        td_ground = channel("Armament@SHIP", fields={"ValidTargets": "Ground"})
        td = select([td_ground], source="OpenRA Tiberian Dawn", scenario="ship")
        self.assertEqual(td["selected"], [td_ground])

    def test_aircraft_interpolation_preserves_endpoints_and_equal_intermediates(self):
        terms = {"Light": {"A": 10, "B": 2}, "Heavy": {"A": 40, "B": 8}}
        result = curves.interpolate_aircraft_terms(terms)
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["terms"]["Fighter"]["A"], 10)
        self.assertEqual(result["terms"]["Fighter"]["B"], 2)
        self.assertEqual(result["terms"]["Bomber"]["A"], 20)
        self.assertEqual(result["terms"]["Bomber"]["B"], 4)
        self.assertEqual(result["terms"]["Helicopter"]["A"], 30)
        self.assertEqual(result["terms"]["Helicopter"]["B"], 6)
        self.assertEqual(result["terms"]["Spaceship"]["A"], 40)
        self.assertEqual(result["terms"]["Spaceship"]["B"], 8)

    def test_aircraft_zero_endpoint_is_valid_but_negative_or_missing_is_unresolved(self):
        zero = curves.interpolate_aircraft_terms(
            {"Light": {"A": 0, "B": 0}, "Heavy": {"A": 10, "B": 2}})
        self.assertEqual(zero["status"], "RESOLVED")
        self.assertEqual(zero["terms"]["Fighter"]["A"], 0)
        negative = curves.interpolate_aircraft_terms(
            {"Light": {"A": -1, "B": 0}, "Heavy": {"A": 10, "B": 2}})
        self.assertEqual(negative["status"], "UNRESOLVED")
        missing = curves.interpolate_aircraft_terms({"Light": {"A": 1, "B": 1}})
        self.assertEqual(missing["status"], "UNRESOLVED")

    def test_aircraft_interpolation_does_not_mutate_endpoints_and_marks_clamped_unsupported(self):
        terms = {"Light": {"A": 10, "B": 2}, "Heavy": {"A": 40, "B": 8}}
        before = copy.deepcopy(terms)
        result = curves.interpolate_aircraft_terms(terms, [{"axis": "Light"}])
        self.assertEqual(result["status"], "RESOLVED_AFFINE_ONLY")
        self.assertEqual(result["clamped_components"]["status"], "UNSUPPORTED")
        self.assertEqual(terms, before)

    def test_aircraft_field_is_limited_to_small_aircraft_records(self):
        vehicle = {"source": "Combined Arms", "scenario": "vehicle", "status": "RESOLVED",
                   "terms": {"Light": {"A": 1, "B": 1}, "Heavy": {"A": 2, "B": 2}}}
        self.assertIs(curves.attach_aircraft_interpolation(vehicle), vehicle)
        self.assertNotIn("aircraft_interpolation", vehicle)
        aircraft = {"source": "Combined Arms", "scenario": "small_aircraft", "status": "RESOLVED",
                    "terms": {"Light": {"A": 1, "B": 1}, "Heavy": {"A": 2, "B": 2}}}
        curves.attach_aircraft_interpolation(aircraft)
        self.assertEqual(aircraft["aircraft_interpolation"]["status"], "RESOLVED")

    def test_build_keeps_alternates_and_marks_unsupported_source_explicitly(self):
        cold = channel("Armament@GROUND", requires_condition="cold")
        warm = channel("Armament@GROUND2", requires_condition="warm")
        matrix = {"rows": [{"actor": "cameo_tank", "references": [
            {"source": "Combined Arms", "id": "BTR", "selected_comparison_weapon": "MGattG",
             "selected_weapon_channels": [cold, warm]},
            {"source": "DTA Enhanced", "id": "DTA", "selected_weapon_channels": [cold]},
        ]}]}
        before = copy.deepcopy(matrix)
        result = curves.build(matrix)
        self.assertEqual(matrix, before)
        ca = [r for r in result["records"] if r["source"] == "Combined Arms"
              and r["scenario"] == "vehicle"]
        self.assertEqual(len(ca), 2)
        self.assertEqual({r["slot"] for r in ca}, {"Armament@GROUND", "Armament@GROUND2"})
        self.assertTrue(all(r["status"] == "RESOLVED" for r in ca))
        dta = [r for r in result["records"] if r["source"] == "DTA Enhanced"]
        self.assertEqual(len(dta), len(curves.SCENARIOS))
        self.assertTrue(all(r["status"] == "UNRESOLVED" for r in dta))

    def test_missing_channels_and_duplicate_selected_identities_are_unresolved(self):
        duplicate = channel("Armament", warhead="Warhead@1Dam")
        matrix = {"rows": [{"actor": "cameo", "references": [
            {"source": "Combined Arms", "id": "EMPTY", "selected_weapon_channels": []},
            {"source": "Combined Arms", "id": "DUP", "selected_weapon_channels": [duplicate,
                                                                                         copy.deepcopy(duplicate)]},
        ]}]}
        result = curves.build(matrix)
        missing = [r for r in result["records"] if r["reference_id"] == "EMPTY"]
        self.assertTrue(all(r["status"] == "UNRESOLVED" and r["terms"] is None for r in missing))
        duplicate_rows = [r for r in result["records"] if r["reference_id"] == "DUP"]
        vehicle = next(r for r in duplicate_rows if r["scenario"] == "vehicle")
        self.assertEqual(vehicle["status"], "UNRESOLVED")
        self.assertIn("duplicate_channel_identity", vehicle["reason"])
        self.assertEqual(result["summary"]["unsupported_source_records"], 0)

    def test_cli_writes_guarded_json_markdown_and_before_after_hashes(self):
        row = channel(source="openra_ra", actor="E1", weapon="M1",
                      fields={"ValidTargets": "GroundActor"})
        matrix = {"export_sha256": {"OpenRA Red Alert": {"export_sha256": "fixture"}},
                  "rows": [{"actor": "cameo", "references": [{
                      "source": "OpenRA Red Alert", "id": "E1", "selected_weapon_channels": [row]}]}]}
        with tempfile.TemporaryDirectory() as directory:
            directory = pathlib.Path(directory)
            matrix_path = directory / "matrix.json"
            out = directory / "curves.json"
            markdown = directory / "curves.md"
            matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(curves.main(["--matrix", str(matrix_path), "--out", str(out),
                                              "--markdown", str(markdown)]), 0)
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(result["input_guard"]["unchanged"])
            self.assertEqual(result["input_guard"]["before"], result["input_guard"]["after"])
            self.assertIn("Source target masks", markdown.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
