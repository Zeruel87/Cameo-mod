"""Virtual anchors reuse final Formula V2 and never imply gameplay approval."""
import contextlib
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "balance"))
import derive_virtual_anchor as tool
import fit_class
import formula


def member(actor, hp=100000, faction="tiberiandawn_gdi"):
    unit = dict(hp={"v": hp}, speed={"v": 100}, cost={"v": 800}, armaments=[
        dict(pricing=True, range=5000, reloaddelay=20, burst=1,
             damage_warheads=[dict(type="AreaDamage", damage=600)])])
    return dict(actor=actor, cls="mbt", faction=faction, hp=hp, speed=100,
                range_wdist=5000, cost=800, unit=unit)


class VirtualAnchorTests(unittest.TestCase):
    def test_final_identity_and_verifier_not_legacy_estimators(self):
        spec = fit_class.virtual_spec("240000,95,5500,600,20,800")
        inputs = (240000, 95, 5500, 30, 1, 1, 1)
        self.assertEqual(fit_class.virtual_estimators(inputs, spec), (800, 800, 800))
        self.assertNotEqual(formula.estimators(*inputs), (800, 800, 800))
        verifier = (480000, 95, 5500, 60, 1, 1, 1)
        self.assertEqual(fit_class.virtual_price({}, {}, verifier, spec), 2000)

    def test_invalid_model_inputs(self):
        for value in ("1,2", "1,2,3,4,0,6", "1,2,3,4,-1,6", "1,2,3,4,5,nan", "1,2,3,4,5,inf"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                fit_class.virtual_spec(value)

    def test_reference_preference_and_no_dps_target(self):
        members = [member("a", 100000), member("b", 200000), member("c", 900000)]
        assignments = {"a": {"game": dict(id="TANK1", confidence="STRONG")},
                       "b": {"game": dict(id="TANK2", confidence="FAIR")},
                       "c": {"game": dict(id="TANK3", confidence="WEAK")}}
        result = tool.derive("mbt", members, assignments, model_damage=600, model_reload=20)
        self.assertEqual(result["fields"]["hp"]["value"], 150000)
        self.assertEqual(result["fields"]["hp"]["actors"], ["a", "b"])
        self.assertEqual(result["estimators"], [800, 800, 800])
        self.assertEqual(result["verifier"]["cost"], 2000)
        self.assertEqual(result["verifier"]["hp"], 300000)
        self.assertIn("UNAPPROVED", result["status"])
        self.assertNotIn("dps0", json.dumps(result))

    def test_no_source_does_not_borrow_other_class(self):
        result = tool.derive("dreadnought", [member("a")], {})
        self.assertEqual(result["status"], ["NO SOURCE"])
        self.assertNotIn("command", result)
        self.assertIsNone(result["verifier"])

    def test_bias_against_full_roster(self):
        members = [member("source", 900000)] + [member(str(i), 100000, "other") for i in range(20)]
        result = tool.derive("mbt", members, {})
        self.assertTrue(any("BIASED hp" in flag for flag in result["status"]))
        self.assertIn("THIN hp", result["status"])

    def test_constant_population_is_not_a_tail(self):
        result = tool.derive("mbt", [member(str(i)) for i in range(4)], {})
        self.assertEqual(result["fields"]["hp"]["percentile"], 50)
        self.assertFalse(any("BIASED" in flag for flag in result["status"]))

    def test_cost_is_on_coarse_nice_grid(self):
        row = member("a")
        row["cost"] = 837
        result = tool.derive("mbt", [row], {})
        self.assertEqual(result["fields"]["cost"]["value"], 800)

    def test_residuals_use_same_derived_modifiers_as_fit(self):
        row = member("a")
        row["derived"] = dict(tier_multiplier=.5, physical_state_weight=1)
        result = tool.derive("mbt", [row], {}, model_damage=600, model_reload=20)
        self.assertAlmostEqual(result["residuals"]["median"], -.375)

    def test_no_arbitrary_dps_model_or_prices_by_default(self):
        result = tool.derive("mbt", [member("a")], {})
        self.assertTrue(any("NO MODEL" in flag for flag in result["status"]))
        self.assertEqual(result["fields"]["hp"]["value"], 100000)
        self.assertNotIn("command", result)
        self.assertNotIn("residuals", result)
        self.assertIsNone(result["verifier"])

    def test_partial_model_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "both"):
            tool.derive("mbt", [member("a")], {}, model_damage=600)

    def test_missing_weapon_range_emits_no_combat_verifier(self):
        row = member("support")
        row["range_wdist"] = None
        result = tool.derive("mbt", [row], {})
        self.assertIn("MISSING range_wdist", result["status"])
        self.assertIsNone(result["verifier"])

    def test_support_never_gets_a_synthetic_weapon(self):
        row = member("apc")
        row["cls"] = "support"
        result = tool.derive("support", [row], {})
        self.assertNotIn("range_wdist", result["fields"])
        self.assertNotIn("model", result)
        self.assertIsNone(result["verifier"])

    def test_committed_population_matches_virtual_fit(self):
        members = tool.load_members(tool.ROOT / "docs/balance")
        for cls in ("mbt", "scout_vehicle", "support"):
            units, _ = fit_class.collect_units(cls, set())
            expected = {actor for actor, unit in units.items() if fit_class.eligible_virtual_member(unit)}
            self.assertEqual({m["actor"] for m in members if m["cls"] == cls}, expected)

    def test_derived_membership_and_air_speed(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory)
            unit = member("a")["unit"]
            unit.update(design={"subtype": "MainBattleTank"}, speed_air={"v": 150})
            del unit["speed"]
            (ledger / "test.json").write_text(json.dumps({"sections": {"units": {"a": unit}}}), encoding="utf-8")
            with patch.object(tool.class_membership, "classify", return_value=("mbt", "derived")) as classify:
                rows = tool.load_members(ledger)
            classify.assert_called_once_with(unit["design"])
            self.assertEqual(rows[0]["speed"], 150)

    def test_spawn_sibling_inclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory)
            unit = member("a")["unit"]
            unit.update(buildable=False, design={"class_anchor": "mbt", "balance_include": True})
            (ledger / "test.json").write_text(json.dumps({"sections": {"units": {"a": unit}}}), encoding="utf-8")
            self.assertEqual(len(tool.load_members(ledger)), 1)

    def test_shared_ledger_actor_stays_in_its_faction_calibration_pool(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory)
            unit = member('a')['unit']
            unit['design'] = {'subtype': 'ScoutInfantry'}
            (ledger / 'shared_redalert.json').write_text(json.dumps({
                'ledger': 'shared_redalert', 'sections': {'infantry': {
                    'ra1_allies_rifleinfantry': unit, 'unaffiliated_actor': unit}}}))
            rows = {row['actor']: row for row in tool.load_members(ledger)}
            self.assertEqual(rows['ra1_allies_rifleinfantry']['faction'], 'redalert_allies')
            self.assertEqual(rows['ra1_allies_rifleinfantry']['source_ledger'], 'shared_redalert')
            self.assertEqual(rows['unaffiliated_actor']['faction'], 'shared_redalert')

    def test_spec_cli_does_not_write_anchor_table(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory)
            anchors = ledger / "class_anchors.json"
            anchors.write_bytes(b"original\r\n")
            with patch.object(fit_class, "LEDGER", ledger), patch.object(fit_class, "ROOT", ledger), \
                    patch.object(fit_class, "ANCHORS", anchors), \
                    patch.object(fit_class, "collect_units", return_value=({}, {})), \
                    patch.object(sys, "argv", ["fit_class", "--class", "mbt", "--spec", "240000,95,5500,600,20,800"]), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(fit_class.main(), 0)
            self.assertIn("O0=800.00 P0=800.00 Q0=800.00", output.getvalue())
            self.assertEqual(anchors.read_bytes(), b"original\r\n")

    def test_virtual_k_requires_real_anchor(self):
        with patch.object(sys, "argv", ["fit_class", "--class", "mbt", "--spec", "1,1,1,100,1,1", "--use-k"]), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            fit_class.main()


class SourcePoolProvenanceTests(unittest.TestCase):
    """The dossier must be able to show which faction pool and which exact actors
    produced each median — including for NO SOURCE, where the selected factions,
    the 0-of-N count and the pool-only qualification must survive (review finding:
    dreadnought's NO SOURCE was unexplainable from output while five global members
    and reference consensus existed)."""

    def test_no_source_keeps_selected_factions_and_qualifies_pool(self):
        members = [member("a", faction="starcraft_terran"), member("b", faction="starcraft_terran")]
        assignments = {"a": {"game": dict(id="TANK1", confidence="STRONG")},
                       "b": {"game": dict(id="TANK2", confidence="FAIR")}}
        result = tool.derive("mbt", members, assignments, factions=("tiberiandawn_gdi",))
        self.assertEqual(result["status"], ["NO SOURCE"])
        self.assertEqual(result["selected_factions"], ["tiberiandawn_gdi"])
        self.assertEqual(result["source_count"], 0)
        self.assertEqual(result["source_actors"], [])
        self.assertEqual(result["full_count"], 2)
        self.assertIn("no eligible member", result["no_source"])
        self.assertIn("selected faction pool", result["no_source"])
        self.assertNotIn("no references", result["no_source"])

    def test_reference_backed_subset_excludes_outside_faction_refs(self):
        members = [member("a", 100000), member("b", 200000),
                   member("c", 900000, faction="starcraft_terran")]
        assignments = {"a": {"game": dict(id="TANK1", confidence="STRONG")},
                       "b": {"game": dict(id="TANK2", confidence="FAIR")},
                       "c": {"game": dict(id="TANK3", confidence="STRONG")}}
        result = tool.derive("mbt", members, assignments, factions=("tiberiandawn_gdi",))
        self.assertEqual(result["source_actors"], ["a", "b"])
        self.assertEqual(result["source_count"], 2)
        self.assertEqual(result["full_count"], 3)
        evidence = result["fields"]["hp"]
        self.assertEqual(evidence["actors"], ["a", "b"])
        self.assertTrue(evidence["reference_backed"])
        self.assertEqual(evidence["reference_preference"], "applied")

    def test_missing_stat_gives_axis_its_own_pool(self):
        a, b = member("a", 100000), member("b", 200000)
        b["cost"] = None
        result = tool.derive("mbt", [a, b], {})
        self.assertEqual(result["fields"]["hp"]["actors"], ["a", "b"])
        self.assertEqual(result["fields"]["cost"]["actors"], ["a"])

    def test_preference_vacated_by_missing_stat_is_not_reported_as_applied(self):
        a, b = member("a", 100000), member("b", 200000)
        a["cost"] = None
        assignments = {"a": {"game": dict(id="TANK1", confidence="STRONG")}}
        result = tool.derive("mbt", [a, b], assignments)
        self.assertEqual(result["fields"]["hp"]["reference_preference"], "applied")
        self.assertTrue(result["fields"]["hp"]["reference_backed"])
        self.assertEqual(result["fields"]["cost"]["reference_preference"], "vacated by missing stat")
        self.assertFalse(result["fields"]["cost"]["reference_backed"])
        self.assertEqual(result["fields"]["cost"]["actors"], ["b"])

    def test_derive_records_selected_factions_verbatim(self):
        result = tool.derive("mbt", [member("a", faction="redalert_japan")], {},
                             factions=("redalert_japan",))
        self.assertEqual(result["selected_factions"], ["redalert_japan"])
        self.assertEqual(result["source_actors"], ["a"])

    def test_custom_factions_cli_records_resolved_pool(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            ledger = root / "docs/balance"
            ledger.mkdir(parents=True)
            registry = ledger / "class_anchors.json"
            registry.write_text(json.dumps({"mbt": {"spec": {}}}), encoding="utf-8")
            provenance = dict(ledger_sha256={"class_anchors.json":
                hashlib.sha256(registry.read_bytes()).hexdigest()})
            with patch.object(tool, "ROOT", root), \
                    patch.object(tool, "load_evidence",
                                 return_value=([member("a", faction="redalert_japan")], {}, provenance)), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(tool.main(["--class", "mbt", "--factions", "japan"]), 0)
            text = output.getvalue()
            self.assertIn('"selected_factions"', text)
            self.assertIn("redalert_japan", text)


class SpeedGridTests(unittest.TestCase):
    """Speed snaps on the global 1-grid for EVERY type — DESIGN.md 2026-09-07
    ruling (the old per-class 5-step existed only to keep TurnSpeed = Speed/5
    an integer, which the derived turn-rate trait removed). TurnSpeed /
    Aircraft.Speed evidence must NOT flip the grid."""

    def foot(self, actor, speed=72.5, **kw):
        row = member(actor, **kw)
        row["speed"] = speed
        row["unit"]["speed"] = {"v": speed}
        return row

    def vehicle(self, actor, speed=72.5, **kw):
        row = self.foot(actor, speed, **kw)
        row["unit"]["turn_speed"] = {"src": "yaml#Mobile.TurnSpeed", "v": "10"}
        return row

    def aircraft(self, actor, speed=72.5, **kw):
        row = member(actor, **kw)
        del row["unit"]["speed"]
        row["unit"]["speed_air"] = {"src": "yaml#Aircraft.Speed", "v": str(speed)}
        row["speed"] = speed
        return row

    def test_foot_pool_snaps_72_5_to_73_on_grid_1(self):
        result = tool.derive("mbt", [self.foot("a"), self.foot("b")], {})
        evidence = result["fields"]["speed"]
        self.assertEqual(evidence["grid_step"], 1)
        self.assertEqual(evidence["median"], 72.5)
        self.assertEqual(evidence["value"], 73)

    def test_turn_speed_evidence_does_not_flip_grid(self):
        result = tool.derive("mbt", [self.vehicle("a"), self.vehicle("b")], {})
        evidence = result["fields"]["speed"]
        self.assertEqual(evidence["grid_step"], 1)
        self.assertEqual(evidence["median"], 72.5)
        self.assertEqual(evidence["value"], 73)

    def test_aircraft_speed_evidence_does_not_flip_grid(self):
        result = tool.derive("mbt", [self.aircraft("a"), self.aircraft("b")], {})
        evidence = result["fields"]["speed"]
        self.assertEqual(evidence["grid_step"], 1)
        self.assertEqual(evidence["value"], 73)

    def test_mixed_pool_stays_on_grid_1(self):
        result = tool.derive("mbt", [self.foot("a"), self.vehicle("b")], {})
        evidence = result["fields"]["speed"]
        self.assertEqual(evidence["grid_step"], 1)
        self.assertEqual(evidence["value"], 73)

    def test_nonpreferred_vehicle_row_does_not_flip_selected_foot_grid(self):
        rows = [self.foot("a"), self.foot("b"), self.vehicle("c")]
        assignments = {"a": {"game": dict(id="TANK1", confidence="STRONG")},
                       "b": {"game": dict(id="TANK2", confidence="FAIR")}}
        result = tool.derive("mbt", rows, assignments)
        evidence = result["fields"]["speed"]
        self.assertTrue(evidence["reference_backed"])
        self.assertEqual(evidence["actors"], ["a", "b"])
        self.assertEqual(evidence["grid_step"], 1)
        self.assertEqual(evidence["value"], 73)

    def test_vehicle_without_speed_value_is_not_in_the_pool(self):
        empty = self.vehicle("c")
        del empty["unit"]["speed"]
        empty["speed"] = None
        result = tool.derive("mbt", [self.foot("a"), self.foot("b"), empty], {})
        evidence = result["fields"]["speed"]
        self.assertEqual(evidence["actors"], ["a", "b"])
        self.assertEqual(evidence["grid_step"], 1)
        self.assertEqual(evidence["value"], 73)

    def test_invalid_turn_speed_evidence_does_not_crash(self):
        broken = self.foot("a")
        broken["unit"]["turn_speed"] = {"src": "yaml#Mobile.TurnSpeed", "v": None}
        garbage = self.foot("b")
        garbage["unit"]["turn_speed"] = {"src": "yaml#Mobile.TurnSpeed", "v": "not-a-number"}
        result = tool.derive("mbt", [broken, garbage], {})
        self.assertEqual(result["fields"]["speed"]["grid_step"], 1)

    def test_every_field_evidence_exposes_its_grid_step(self):
        result = tool.derive("mbt", [self.foot("a"), self.foot("b"), self.foot("c")], {})
        self.assertEqual(result["fields"]["hp"]["grid_step"], tool.STEPS["hp"])
        self.assertEqual(result["fields"]["speed"]["grid_step"], tool.STEPS["speed"])
        self.assertEqual(result["fields"]["range_wdist"]["grid_step"], tool.STEPS["range_wdist"])
        self.assertEqual(result["fields"]["cost"]["grid_step"], tool.STEPS["cost"])

    def test_resolved_ledger_mbt_speed_pool_snaps_72_5_to_73(self):
        # Verified bug baseline: the selected (reference-backed) MBT speed pool
        # has median 72.5, snapped to 73 on the global 1-grid. Evidence-driven:
        # pool composition may move, and then these assertions name the new
        # state instead of silently passing.
        members, assignments, _ = tool.load_evidence(tool.ROOT / "docs/balance")
        result = tool.derive("mbt", members, assignments)
        evidence = result["fields"]["speed"]
        self.assertTrue(evidence["reference_backed"])
        self.assertEqual(evidence["grid_step"], 1)
        self.assertEqual(evidence["median"], 72.5)
        self.assertEqual(evidence["value"], 73)


class RegistryRaceTests(unittest.TestCase):
    def test_registry_rewrite_between_read_and_evidence_refuses_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            ledger = root / "docs/balance"
            (ledger / "derived").mkdir(parents=True)
            registry = ledger / "class_anchors.json"
            registry.write_text(json.dumps({"mbt": {"spec": {}}}), encoding="utf-8")
            (ledger / "derived/reference_assignment.json").write_text(
                json.dumps({"assignment": {}}), encoding="utf-8")
            real_load_evidence = tool.load_evidence

            def replace_registry(_ledger):
                registry.write_text(json.dumps({"mbt": {"spec": {"hp0": 240000}}}), encoding="utf-8")
                return real_load_evidence(_ledger)

            with patch.object(tool, "ROOT", root), \
                    patch.object(tool, "load_evidence", side_effect=replace_registry), \
                    contextlib.redirect_stdout(io.StringIO()) as output, \
                    contextlib.redirect_stderr(io.StringIO()) as errors:
                with self.assertRaises(SystemExit):
                    tool.main(["--class", "mbt"])
            self.assertIn("class_anchors.json changed", errors.getvalue())
            self.assertEqual(output.getvalue(), "")

    def test_stable_registry_fingerprint_allows_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            ledger = root / "docs/balance"
            ledger.mkdir(parents=True)
            registry = ledger / "class_anchors.json"
            registry.write_text(json.dumps({"mbt": {"spec": {}}}), encoding="utf-8")
            provenance = dict(ledger_sha256={"class_anchors.json":
                hashlib.sha256(registry.read_bytes()).hexdigest()})
            with patch.object(tool, "ROOT", root), \
                    patch.object(tool, "load_evidence", return_value=([member("a")], {}, provenance)), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(tool.main(["--class", "mbt", "--factions", "tiberiandawn_gdi"]), 0)
            self.assertIn(hashlib.sha256(registry.read_bytes()).hexdigest(), output.getvalue())
