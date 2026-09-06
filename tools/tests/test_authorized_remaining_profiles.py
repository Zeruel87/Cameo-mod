"""Regression boundary for the final authorized live weapon-profile batch."""

from __future__ import annotations

import json
import hashlib
import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

from consolidate_authorized_remaining_profiles import inspect
from consolidate_authorized_remaining_profiles import CLEANUP_NAMES
from miniyaml import Ruleset
from review_batch_diff import active_health_values, snapshot, snapshot_digest
from survey_weapon_structure import inventory


class AuthorizedRemainingProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.comparison = json.loads((
            ROOT / "docs/audit/latest/authorized_remaining_profile_comparison.json"
        ).read_text(encoding="utf-8"))

    def test_converter_accepts_the_resolved_ruleset(self):
        self.assertTrue(inspect(self.rules))

    def test_comparison_has_no_definition_or_delivery_drift(self):
        self.assertEqual([], self.comparison["added"])
        self.assertEqual([], self.comparison["removed"])
        forbidden = {"cadence", "projectile", "report"}
        observed = {
            change[0]
            for changes in self.comparison["changed"].values()
            for change in changes
        }
        self.assertTrue(forbidden.isdisjoint(observed))

    def test_historical_comparison_metadata_remains_unmodified(self):
        # This artifact records PR #320, not subsequent upstream gameplay edits.
        # Keep its original baseline, head digest and HP matrix as provenance.
        self.assertEqual(
            "8ddfb4e9bc5a5d25765ce635845b4004e3e2a485e015b712192554e333b0393f",
            snapshot_digest(self.comparison["meta"]))

    def test_followup_preserves_the_refreshed_upstream_weapon_snapshot(self):
        # Independently pin upstream 4deaee086; never relabel the historical
        # authorized batch artifact as evidence for these later changes.
        health_values = sorted(set(active_health_values(ROOT)))
        self.assertEqual(
            "6984adb9be04b1f7c056159aa33f3c2a31b16e400e9062af13b0912a8124a737",
            snapshot_digest(snapshot(ROOT, False, health_values)))

    def test_comparison_payload_is_exactly_reviewed(self):
        payload = {
            key: self.comparison[key] for key in ("changed", "removed", "added")
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(
            "e65496668e328c845f3e86bdbba8360d10a92ffaf678679b9706c1ee119b322b",
            hashlib.sha256(raw).hexdigest())

    def test_only_intentional_flat_total_and_target_route_changed(self):
        main_damage = {
            name: change[1:]
            for name, changes in self.comparison["changed"].items()
            for change in changes
            if change[0] == "main_damage"
        }
        self.assertEqual({"TSBombSonic": [20000.0, 30000.0]}, main_damage)

        top_level = {
            name
            for name, changes in self.comparison["changed"].items()
            if any(change[0] == "top_level" for change in changes)
        }
        self.assertEqual({"TSAegisMissile"}, top_level)

        non_damage = {
            name
            for name, changes in self.comparison["changed"].items()
            if any(change[0] == "non_damage_warheads" for change in changes)
        }
        self.assertEqual({"GrenadeRA"}, non_damage)

    def test_reachable_backlog_is_reduced_to_the_review_boundary(self):
        # Do not retain a fully resolved roster throughout this test class: the
        # snapshot and converter tests otherwise hold another roster concurrently.
        counts = inventory(Ruleset(ROOT))["counts"]
        self.assertEqual(240, counts["stacked_main_transitive_weapon_graph"])
        self.assertEqual(226, counts["reviewed_stacked_main_transitive_weapon_graph"])
        self.assertEqual(14, counts["unreviewed_stacked_main_transitive_weapon_graph"])
        self.assertEqual(100, counts["unreviewed_stacked_main_unreached"])

    def test_t30_profile_keeps_the_authorized_railgun_geometry(self):
        node = self.rules.resolve_weapon("t30shell").child(
            "Warhead@Railgun_HeavyFlatCompatibility")
        self.assertEqual("80000", node.get("Damage"))
        self.assertEqual("512", node.get("Spread"))
        self.assertEqual("100, 0", node.get("Falloff"))
        self.assertEqual("3000", node.get("PercentageScale"))
        self.assertEqual(1200, (80000 * 3000 + 100000) // 200000)

    def test_paid_thermobaric_routes_do_not_regress_core_vehicle_damage(self):
        armors = ("Scout", "Light", "Medium", "Heavy", "Superheavy")
        for base_name, paid_name in (
                ("HammerTankCannon", "HammerTankCannonThermobaric"),
                ("KotinCannon", "KotinCannonThermobaric")):
            base = self.rules.resolve_weapon(base_name).child("Warhead@CannonHE_Heavy")
            paid = self.rules.resolve_weapon(paid_name).child("Warhead@Thermobaric_Heavy")
            base_versus = {node.key: int(node.value) for node in base.child("Versus").children}
            paid_versus = {node.key: int(node.value) for node in paid.child("Versus").children}
            base_damage = int(base.get("Damage"))
            paid_damage = int(paid.get("Damage"))
            for armor in armors:
                self.assertGreaterEqual(
                    paid_damage * paid_versus[armor],
                    base_damage * base_versus[armor],
                    f"{paid_name} regresses {armor}")

    def test_converter_default_mode_is_read_only(self):
        paths = {
            pathlib.Path(self.rules.weapons[name].file)
            for name in CLEANUP_NAMES
            if name in self.rules.weapons
        }
        before = {path: path.read_bytes() for path in paths}
        subprocess.run(
            [sys.executable, str(ROOT / "tools/balance/consolidate_authorized_remaining_profiles.py")],
            cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertEqual(before, {path: path.read_bytes() for path in paths})


if __name__ == "__main__":
    unittest.main()
