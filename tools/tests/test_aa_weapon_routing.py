"""Regression checks for split ground/air weapon target routing."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit")]

from audit_three_way_split import main_warhead_nodes, main_warheads
from audit_warhead_split import ROUTING_REVEALED_BROADCASTS
from miniyaml import Ruleset


class AaWeaponRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def assert_main_warheads_target(self, weapon_name: str, targets: str,
                                    expected_mains: dict[str, str]):
        weapon = self.rules.resolve_weapon(weapon_name)
        self.assertIsNotNone(weapon, weapon_name)
        self.assertEqual(targets, weapon.child("ValidTargets").value, weapon_name)
        mains = set(main_warheads(weapon))
        self.assertEqual(set(expected_mains), mains, weapon_name)
        for key, damage in expected_mains.items():
            warhead = weapon.child(f"Warhead@{key}")
            self.assertIsNotNone(warhead, f"{weapon_name}/{key}")
            self.assertEqual(damage, warhead.child("Damage").value,
                             f"{weapon_name}/{key}")
            self.assertEqual(targets, warhead.child("ValidTargets").value,
                             f"{weapon_name}/{key}")

    def test_flak_23_ground_and_air_routes_match_their_armaments(self):
        mains = {"Flak_MediumFlatCompatibility": "4000"}
        self.assert_main_warheads_target("FLAK-23-AG", "Ground, Water", mains)
        self.assert_main_warheads_target("FLAK-23-AA", "Air", mains)

    def test_manifold_ground_and_air_routes_match_their_armaments(self):
        mains = {"Bullet_MediumFlatCompatibility": "6000"}
        self.assert_main_warheads_target("ManifoldMG", "Ground, Water", mains)
        self.assert_main_warheads_target("ManifoldMG_AA", "Air", mains)

    def test_consolidated_aa_families_route_every_main_to_air(self):
        expected = {
            "ArmoredCarMG_AA": {"Bullet_Medium": "16000"},
            "NaxQuadCannon_AA": {
                "Flak_MediumFlatCompatibility": "7000"},
            "NaxQuadCannon_AA_elite": {
                "Flak_MediumFlatCompatibility": "7000"},
            "SkyMageCannon_AA": {
                "Flak_MediumFlatCompatibility": "7000"},
            "SkyMageCannon_AA_elite": {
                "Flak_MediumFlatCompatibility": "7000"},
            "RA2MultiHoverMissile_AA": {
                "MissileAA_LightFlatCompatibility": "4000"},
            "RA2MultiHoverMissile_AA_elite": {
                "MissileAA_LightFlatCompatibility": "4000"},
        }
        for weapon_name, mains in expected.items():
            weapon = self.rules.resolve_weapon(weapon_name)
            self.assertEqual("Air", weapon.child("ValidTargets").value, weapon_name)
            self.assertEqual(set(mains), set(main_warheads(weapon)), weapon_name)
            for key, damage in mains.items():
                warhead = weapon.child(f"Warhead@{key}")
                self.assertEqual(damage, warhead.child("Damage").value,
                                 f"{weapon_name}/{key}")
                targets = {x.strip() for x in
                           warhead.child("ValidTargets").value.split(",")}
                self.assertIn("Air", targets, f"{weapon_name}/{key}")

    def test_active_air_only_armaments_have_no_ground_only_main_damage(self):
        failures = []
        checked = set()
        for actor_name in sorted(self.rules.actors):
            actor = self.rules.resolve(actor_name)
            if actor is None:
                continue
            for armament in actor.children_named("Armament"):
                weapon_name = armament.get("Weapon")
                if not weapon_name or weapon_name in checked:
                    continue
                checked.add(weapon_name)
                weapon = self.rules.resolve_weapon(weapon_name)
                if weapon is None or weapon.get("ValidTargets") != "Air":
                    continue
                for warhead in main_warhead_nodes(weapon):
                    targets = {x.strip() for x in
                               (warhead.get("ValidTargets") or "").split(",") if x.strip()}
                    if "Air" not in targets:
                        failures.append(f"{weapon_name}/{warhead.key}: "
                                        f"{warhead.get('ValidTargets') or '<default>'}")
        self.assertEqual([], failures)

    def test_routing_revealed_audit_exceptions_are_exact(self):
        self.assertEqual({}, ROUTING_REVEALED_BROADCASTS)


if __name__ == "__main__":
    unittest.main()
