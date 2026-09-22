"""Synthetic tests for the bounded secondary-payload route inventory."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Node  # noqa: E402
from secondary_payload_routes import inventory  # noqa: E402


def field(key, value, line):
    return Node(key, value, [], "fixture/rules.yaml", line)


def trait(key, children, line):
    return Node(key, "", children, "fixture/rules.yaml", line)


class SyntheticRuleset:
    def __init__(self, actors, weapons):
        self.actors = {node.key: node for node in actors}
        self.weapons = {node.key.lower(): node for node in weapons}

    def resolve(self, name):
        return self.actors.get(name)

    def weapon(self, name):
        return self.weapons.get(name.lower())


class SecondaryPayloadRoutesTest(unittest.TestCase):
    def setUp(self):
        actor = Node("unit", "", [
            trait("Armament@primary", [field("CasingWeapon", "CasingFx", 2)], 1),
            trait("FallsToEarth", [field("Explosion", "CrashFx", 4)], 3),
            trait("FireWarheadsOnDeath", [
                field("Weapons", "DeathFx, MissingFx, DeathFx", 6),
                field("EmptyWeapon", "EmptyFx", 7),
            ], 5),
            trait("FireWarheads", [field("Weapons", "PeriodicFx, OtherFx", 9)], 8),
            trait("RecallPower", [field("ImpactWeapon", "ImpactFx", 11)], 10),
            # Explicitly unknown fields remain outside the inventory.
            trait("UnknownEffect", [field("Weapon", "ShouldNotAppear", 13)], 12),
        ], "fixture/actors.yaml", 1)
        template = Node("^Template", "", [
            trait("Armament", [field("CasingWeapon", "CasingFx", 20)], 19),
        ], "fixture/templates.yaml", 1)
        weapons = [Node(name, "", [], "fixture/weapons.yaml", index)
                   for index, name in enumerate(
                       ("CasingFx", "CrashFx", "DeathFx", "EmptyFx",
                        "PeriodicFx", "OtherFx", "ImpactFx"), start=1)]
        self.report = inventory(SyntheticRuleset([actor, template], weapons))

    def test_all_allowlisted_route_kinds_and_statuses_are_present(self):
        routes = self.report["routes"]
        self.assertEqual({route["route_kind"] for route in routes}, {
            "casing", "falls_to_earth_explosion", "death_weapon",
            "death_empty_weapon", "fire_warheads_weapon", "impact_weapon",
        })
        self.assertEqual(self.report["counts"]["resolution"],
                         {"missing": 1, "resolved": 7})

    def test_comma_separated_values_are_independent_and_duplicates_are_collapsed(self):
        routes = self.report["routes"]
        death = [route for route in routes if route["weapon_token"] == "DeathFx"]
        self.assertEqual(len(death), 1)
        self.assertEqual(death[0]["duplicate_count"], 2)
        self.assertEqual(death[0]["raw_field_value"], "DeathFx, MissingFx, DeathFx")
        self.assertEqual(self.report["counts"]["unique_routes"], 8)
        self.assertEqual(self.report["counts"]["total_occurrences"], 9)
        self.assertEqual(self.report["counts"]["duplicate_occurrences"], 1)

    def test_missing_reference_is_retained_with_field_provenance(self):
        route = next(route for route in self.report["routes"]
                     if route["weapon_token"] == "MissingFx")
        self.assertEqual(route["resolution"], "missing")
        self.assertIsNone(route["resolved_weapon"])
        self.assertEqual(route["actor"], "unit")
        self.assertEqual(route["trait_key"], "FireWarheadsOnDeath")
        self.assertEqual(route["field_path"], "FireWarheadsOnDeath.Weapons")
        self.assertEqual(route["provenance"]["field"],
                         {"file": "fixture/rules.yaml", "line": 6})

    def test_templates_and_unknown_fields_are_excluded(self):
        actors = {route["actor"] for route in self.report["routes"]}
        self.assertEqual(actors, {"unit"})
        self.assertNotIn("ShouldNotAppear",
                         {route["weapon_token"] for route in self.report["routes"]})


if __name__ == "__main__":
    unittest.main()
