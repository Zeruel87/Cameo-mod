"""Pins the Forgotten M113 ADATS air-first role and chemical progression."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "docs/audit/latest/adats_air_first_summary.json"
COMPARISON = ROOT / "docs/audit/latest/adats_air_first_comparison.json"
DERIVED_LEDGER = ROOT / "docs/balance/derived/tiberiansun_forgotten.json"
sys.path[:0] = [str(ROOT / "tools/audit")]

from audit_three_way_split import main_warhead_nodes, main_warheads  # noqa: E402
from miniyaml import Ruleset  # noqa: E402


EXPECTED_CHANGE_KIND_DIGESTS = {
    "armor_profile": "4383dce9fd6b8e20fb316d629fb12187a59d814aacb7501ca6f6218544133b7d",
    "blast_shape": "da08ede271e6f6764e1a39ffa19da01e1c60254cc59008f04c5a7e71c94e4747",
    "percentage_damage": "790ea8448dbd2f94a46a1717c6ee6ed96bff51663b9aee91393f63d48c0080d2",
}


class ADATSAirFirstRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.comparison = json.loads(COMPARISON.read_text(encoding="utf-8"))
        cls.derived = json.loads(DERIVED_LEDGER.read_text(encoding="utf-8"))

    def test_base_routes_have_one_role_specific_main(self):
        expected = {
            "TSAdatsMissile": (
                "MissileHE_LightFlatCompatibility", "8000", "9988",
                "Ground, Water", "5606",
                {"None": "93", "Light": "156", "Heavy": "96"}),
            "TSAdatsMissile_AA": (
                "Flak_MediumFlatCompatibility", "8000", "9988",
                "Air", "8409",
                {"Fighter": "197", "Bomber": "196", "Helicopter": "155"}),
        }
        for name, (profile, damage, scale, targets, weapon_range, versus) in expected.items():
            weapon = self.rules.resolve_weapon(name)
            self.assertEqual([profile], main_warheads(weapon), name)
            main = main_warhead_nodes(weapon)[0]
            self.assertEqual(damage, main.get("Damage"), name)
            self.assertEqual(scale, main.get("PercentageScale"), name)
            self.assertEqual(targets, main.get("ValidTargets"), name)
            self.assertEqual(weapon_range, weapon.get("Range"), name)
            self.assertEqual(
                versus,
                {armor: main.child("Versus").get(armor) for armor in versus},
                name,
            )

    def test_chemical_upgrade_routes_are_live_and_stronger(self):
        expected = {
            "TSChemAdatsMissile": (
                "MissileChem_Light", "12000", "Ground, Water"),
            "TSChemAdatsMissileAA": (
                "Flak_MediumFlatCompatibility", "12000", "Air"),
        }
        for name, (profile, damage, targets) in expected.items():
            weapon = self.rules.resolve_weapon(name)
            self.assertEqual([profile], main_warheads(weapon), name)
            main = main_warhead_nodes(weapon)[0]
            self.assertEqual(damage, main.get("Damage"), name)
            self.assertEqual(targets, main.get("ValidTargets"), name)

        chemical = self.rules.resolve_weapon("TSChemAdatsMissile")
        corrosion = chemical.child("Warhead@LightChemicalWeaponPercentage")
        self.assertEqual("Corrosion", corrosion.get("PhysicalStateName"))
        self.assertEqual("100", corrosion.get("PhysicalStateScale"))
        self.assertEqual("false", chemical.get("TargetActorCenter"))
        self.assertEqual("wall", chemical.get("InvalidTargets"))
        self.assertIsNotNone(chemical.child("Warhead@Cloud"))
        for tag in (
                "LightChemicalWeaponPercentage", "FlakWeaponPercentage",
                "LightMissilePercentage"):
            self.assertEqual("2", chemical.child(f"Warhead@{tag}").get("Damage"))

        chemical_aa = self.rules.resolve_weapon("TSChemAdatsMissileAA")
        self.assertFalse(any(
            node.get("PhysicalStateName") == "Corrosion"
            for node in chemical_aa.children
        ))

    def test_actor_selects_exact_base_and_upgrade_pairs(self):
        actor = self.rules.resolve("forgotten_m113adats")
        armaments = {
            arm.key: (arm.get("Weapon"), arm.get("RequiresCondition"))
            for arm in actor.children_named("Armament")
        }
        self.assertEqual({
            "Armament@PRIMARY": (
                "TSAdatsMissile", "!forgotten_upgrade_chemicalweapons"),
            "Armament@SECONDARY": (
                "TSAdatsMissile_AA", "!forgotten_upgrade_chemicalweapons"),
            "Armament@UPGRADE": (
                "TSChemAdatsMissile", "forgotten_upgrade_chemicalweapons"),
            "Armament@UPGRADEAA": (
                "TSChemAdatsMissileAA", "forgotten_upgrade_chemicalweapons"),
        }, armaments)
        priorities = {
            child.key for child in actor.children
            if child.key.startswith("AutoTargetPriority@")
        }
        self.assertIn("AutoTargetPriority@AIR", priorities)
        self.assertEqual("30", actor.child("AutoTargetPriority@AIR").get("Priority"))
        self.assertEqual(
            "actor_forgotten_m113adats.description",
            actor.child("Buildable").get("Description"),
        )
        grant = actor.child(
            "GrantConditionOnPrerequisite@forgotten_upgrade_chemicalweapons")
        self.assertEqual("forgotten_upgrade_chemicalweapons", grant.get("Condition"))
        self.assertEqual(
            "forgotten_upgrade_chemicalweapons", grant.get("Prerequisites"))

        research = self.rules.resolve("forgotten_upgrade_chemicalweapons")
        self.assertEqual("5000", research.child("Valued").get("Cost"))
        self.assertEqual("Research", research.child("Buildable").get("Queue"))
        self.assertEqual(
            "~forgotten_church, !forgotten_upgrade_chemicalweapons",
            research.child("Buildable").get("Prerequisites"),
        )

    def test_weapon_inheritance_closure_is_exact(self):
        children = {}
        for name, node in self.rules.weapons.items():
            for _key, parent in self.rules.inherits_of(node):
                if parent in self.rules.weapons:
                    children.setdefault(parent, set()).add(name)

        seen = set()
        pending = list(children.get("TSAdatsMissile", set()))
        while pending:
            child = pending.pop()
            if child in seen:
                continue
            seen.add(child)
            pending.extend(children.get(child, set()))
        self.assertEqual({"TSAdatsMissile_AA", "TSChemAdatsMissileAA"}, seen)
        self.assertNotIn("TSChemAdatsMissile", seen)

    def test_paid_upgrade_improves_both_firing_routes(self):
        rows = {
            row["slot"]: row
            for row in self.derived["sections"]["vehicles"][
                "forgotten_m113adats"]["armaments"]
        }
        self.assertEqual(234.16, rows["Armament@PRIMARY"]["effective_dps"])
        self.assertEqual(369.89, rows["Armament@UPGRADE"]["effective_dps"])
        self.assertEqual(165.39, rows["Armament@SECONDARY"]["effective_dps"])
        self.assertEqual(248.08, rows["Armament@UPGRADEAA"]["effective_dps"])
        self.assertGreater(
            rows["Armament@UPGRADE"]["effective_dps"],
            rows["Armament@PRIMARY"]["effective_dps"],
        )
        self.assertGreater(
            rows["Armament@UPGRADEAA"]["effective_dps"],
            rows["Armament@SECONDARY"]["effective_dps"],
        )

    def test_whole_tree_comparison_is_exact_and_bounded(self):
        self.assertEqual({
            "TSAdatsMissile", "TSAdatsMissile_AA", "TSChemAdatsMissileAA",
        }, set(self.comparison["changed"]))
        self.assertEqual([], self.comparison["added"])
        self.assertEqual([], self.comparison["removed"])
        self.assertEqual({
            "armor_profile", "blast_shape", "percentage_damage",
        }, {
            change[0] for changes in self.comparison["changed"].values()
            for change in changes
        })
        self.assertEqual({
            "source_digest": "05ca54cf18f2aa326ad65c6a03d192e6b24751f4c0afd323a0efbeb5063047f9",
            "counts": {"changed": 3, "added": 0, "removed": 0},
            "added": [],
            "removed": [],
            "change_kind_counts": {
                "armor_profile": 3,
                "blast_shape": 3,
                "percentage_damage": 1,
            },
            "change_kind_digests": EXPECTED_CHANGE_KIND_DIGESTS,
            "changed": {
                "TSAdatsMissile": ["armor_profile", "blast_shape"],
                "TSAdatsMissile_AA": ["armor_profile", "blast_shape"],
                "TSChemAdatsMissileAA": [
                    "armor_profile", "blast_shape", "percentage_damage"],
            },
            "percentage_rounding": {
                "row_count": 3,
                "max_absolute_delta": 1,
                "digest": "624603063d51218ef1cc2641e3ce8d8477b0eb4d729bf8a56d5ff7a979ba65ab",
            },
        }, self.summary)


if __name__ == "__main__":
    unittest.main()
