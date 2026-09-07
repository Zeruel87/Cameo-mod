"""Readiness uses raw resolved structure, and never clears unknown weapons."""
import pathlib
import json
import io
import sys
import unittest
import tempfile
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import anchor_readiness as readiness
import audit_three_way_split as split
import miniyaml


class ReadinessFeatureTests(unittest.TestCase):
    def test_aircraft_speed_is_not_silently_omitted(self):
        self.assertEqual(125, readiness.features({"speed_air": {"v": 125}})["speed"])
        self.assertEqual(0, readiness.features({"speed": {"v": 0}, "speed_air": {"v": 125}})["speed"])
        self.assertIsNone(readiness.features({})["speed"])

    def test_range_accepts_world_distance_notation(self):
        self.assertEqual(5120, readiness.unit_range({"armaments": [{"range": "5c0"}]}))
        self.assertIsNone(readiness.unit_range({"armaments": [{"range": "unknown"}]}))

    def test_nominal_dps_uses_full_burst_and_excludes_percentage_twins(self):
        arm = {"pricing": True, "reloaddelay": "20", "burst": "3",
               "burstdelays": "5", "damage_warheads": [
                   {"type": "AreaDamage", "damage": 100},
                   {"type": "AreaDamagePercentage", "damage": 100}]}
        self.assertEqual(250, readiness.unit_dps({"armaments": [arm]}))
        arm["burstdelays"] = "2, 3"
        self.assertEqual(300, readiness.unit_dps({"armaments": [arm]}))
        del arm["burstdelays"]
        self.assertEqual(250, readiness.unit_dps({"armaments": [arm]}))
        arm["burst"] = "1"
        self.assertEqual(125, readiness.unit_dps({"armaments": [arm]}))
        arm["pricing"] = False
        self.assertIsNone(readiness.unit_dps({"armaments": [arm]}))

    def test_invalid_cadence_is_not_replaced_by_defaults(self):
        arm = {"pricing": True, "reloaddelay": "20",
               "damage_warheads": [{"type": "AreaDamage", "damage": 100}]}
        self.assertEqual(125, readiness.unit_dps({"armaments": [arm]}))
        for value in (0, -1, "bad", "NaN", "inf", 1.5):
            with self.subTest(burst=value):
                self.assertIsNone(readiness.unit_dps({"armaments": [{**arm, "burst": value}]}))
        for value in (0, -1, "bad", "NaN", "inf"):
            with self.subTest(reload=value):
                self.assertIsNone(readiness.unit_dps({"armaments": [{**arm, "reloaddelay": value}]}))
        for value in (None, "", "bad", "1.5", "1, 2, 3", [], "NaN", "inf"):
            with self.subTest(delays=value):
                self.assertIsNone(readiness.unit_dps({"armaments": [
                    {**arm, "burst": 3, "burstdelays": value}]}))


class SplitGateTests(unittest.TestCase):
    def gate(self, weapon="Composite"):
        return readiness.three_way_split_gate(
            {"actor": {"armaments": [{"weapon": weapon}]}}, {"actor": "mbt"})

    def test_reviewed_composite_remains_in_raw_count(self):
        with patch.object(miniyaml, "Ruleset") as rules, \
                patch.object(split, "main_warheads", return_value=[1, 2, 3, 4]):
            rules.return_value.resolve_weapon.return_value = object()
            (debt, counted), error = self.gate("HydraSpit")
        self.assertIsNone(error)
        self.assertEqual(debt["mbt"], [("actor", "HydraSpit", 4)])
        self.assertEqual(counted["mbt"], 1)

    def test_single_main_is_not_a_stacked_finding(self):
        with patch.object(miniyaml, "Ruleset"), \
                patch.object(split, "main_warheads", return_value=[1]):
            (debt, counted), error = self.gate()
        self.assertIsNone(error)
        self.assertFalse(debt)
        self.assertEqual(counted["mbt"], 1)

    def test_unresolved_weapon_fails_closed(self):
        with patch.object(miniyaml, "Ruleset") as rules:
            rules.return_value.resolve_weapon.return_value = None
            gate, error = self.gate()
        self.assertIsNone(gate)
        self.assertIn("unresolved weapon actor/Composite", error)

    def test_resolution_error_fails_closed(self):
        with patch.object(miniyaml, "Ruleset") as rules:
            rules.return_value.resolve_weapon.side_effect = ValueError("cycle")
            gate, error = self.gate()
        self.assertIsNone(gate)
        self.assertIn("cycle", error)

    def test_missing_weapon_identity_fails_closed(self):
        with patch.object(miniyaml, "Ruleset"):
            gate, error = self.gate(None)
        self.assertIsNone(gate)
        self.assertIn("unidentified armament", error)

    def test_manifest_failure_fails_closed(self):
        with patch.object(miniyaml, "Ruleset", side_effect=ValueError("bad include")):
            gate, error = self.gate()
        self.assertIsNone(gate)
        self.assertIn("bad include", error)


class AnchorMembershipTests(unittest.TestCase):
    def test_cli_renders_missing_baselines_and_still_writes_json(self):
        spec_rows = [
            ("mbt", "actor", True, None, 500, None, ["hp unavailable"], False),
            ("support", "other", True, 500, None, None, ["hp unavailable"], False),
        ]
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            report = pathlib.Path(directory) / "readiness.json"
            with patch.object(sys, "argv", ["anchor_readiness", "--json", str(report)]), \
                    patch.object(readiness, "anchor_actor_vs_spec", return_value=spec_rows), \
                    redirect_stdout(output):
                self.assertEqual(0, readiness.main())
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertIsNone(data["split_gate_error"])
            self.assertTrue(data["rows"])
            self.assertTrue(all(isinstance(row, dict) and "class" in row and "scored" in row
                                for row in data["rows"]))
            self.assertIn("support", {row["class"] for row in data["rows"]})
        self.assertIn("| unavailable | 500 |", output.getvalue())
        self.assertIn("| 500 | unavailable |", output.getvalue())

    def test_unreadable_ledger_does_not_silently_reduce_population(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = pathlib.Path(directory)
            (ledger / "broken.json").write_text("{", encoding="utf-8")
            with patch.object(readiness, "LEDGER", ledger):
                with self.assertRaisesRegex(ValueError, "readiness unavailable"):
                    readiness.load_units()

    def test_coverage_separates_structures_and_reports_unclassified_rows(self):
        units = [("f", "s", str(i), {"buildable": buildable, "design": {"subtype": subtype}})
                 for i, (subtype, buildable) in enumerate([
                     ("MainBattleTank", True), ("Building", True),
                     ("Helicopter", True), ("Misc", True), ("MainBattleTank", False)])]
        counts = readiness.coverage_counts(units)
        self.assertEqual(counts["buildable_rows"], 4)
        self.assertEqual(counts["non_structural_rows"], 3)
        self.assertEqual(counts["classified_rows"], 1)
        self.assertEqual(counts["no-template"], 1)
        self.assertEqual(counts["no-class-exists"], 1)
        self.assertEqual(readiness.coverage_counts([])["buildable_rows"], 0)

    def test_unfitted_anchor_still_gets_stat_review(self):
        rows = readiness.anchor_actor_vs_spec(
            {"mbt": {"anchor_actor": "actor", "spec": {"hp0": 100, "cost0": 500}}},
            {"actor": {"hp": {"v": "50"}}})
        self.assertEqual(len(rows), 1)
        self.assertIn("hp 50!=100", rows[0][6])
        self.assertIn("range unavailable (measured)", rows[0][6])
        self.assertIsNone(rows[0][5])
        self.assertFalse(rows[0][7])

    def test_every_anchor_belongs_to_its_declared_class(self):
        anchors = json.loads((ROOT / "docs/balance/class_anchors.json").read_text(encoding="utf-8"))
        units = {name: record for _, _, name, record in readiness.load_units()}
        for cls, anchor in anchors.items():
            if cls.startswith("_"):
                continue
            actor = anchor["anchor_actor"]
            with self.subTest(cls=cls, actor=actor):
                self.assertIn(actor, units)
                self.assertEqual(readiness.class_membership.classify(
                    units[actor].get("design") or {})[0], cls)

    def test_heavy_sniper_uses_explicit_role_not_template_mutation(self):
        units = {name: record for _, _, name, record in readiness.load_units()}
        rec = units["td_gdi_heavysniper"]
        self.assertEqual(rec["design"]["class_anchor"], "heavy_sniper")
        self.assertEqual(rec["design"]["subtype"], "SniperInfantry")
        self.assertEqual(rec["cost"]["v"], "700")
        self.assertEqual(rec["hp"]["v"], "25000")


if __name__ == "__main__":
    unittest.main()
