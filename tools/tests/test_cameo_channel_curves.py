"""Synthetic tests for current Cameo channel HP curves."""
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
from miniyaml import Node  # noqa: E402
import armor_projection  # noqa: E402
import cameo_channel_curves as curves  # noqa: E402
import percentage_damage as pd  # noqa: E402


def child(key, value="", children=None):
    return Node(key, value, children or [])


def versus(value="100"):
    return child("Versus", children=[child(axis, value) for axis in curves.ARMOR_AXES])


def weapon(*warheads):
    return Node("TestWeapon", "", list(warheads))


def warhead(key, kind, damage, *, extra=None, table_value="100"):
    fields = [child("Damage", str(damage)), versus(table_value)]
    fields.extend(child(name, str(value)) for name, value in (extra or {}).items())
    return child(key, kind, fields)


def row(actor, slot, weapon_name, node, *, fields=None):
    return curves.channel_row(actor, slot, weapon_name, node) | {"fields": fields or curves._field_map(node)}


def open_topped(key="Warhead@Passenger", damage="7777", amount=None):
    fields = [child("ValidTargets", "Ground"), child("Damage", str(damage)), versus()]
    if amount is not None:
        fields.append(child("Amount", str(amount)))
    return child(key, "OpenToppedDamage", fields)


class CameoChannelCurveTests(unittest.TestCase):
    def test_folded_and_standalone_percentage_terms_are_b_terms_not_flat_damage(self):
        folded = warhead("Warhead@Fold", "AreaDamage", 100,
                         extra={"Falloff": "50, 25", "PercentageScale": "1000"})
        standalone = warhead("Warhead@Standalone", "HealthPercentageDamage", 20,
                             extra={"Falloff": "111, 22"})
        area_percentage = warhead("Warhead@AreaPercentage", "AreaDamagePercentage", 100,
                                  extra={"Falloff": "111, 22"})
        gun = weapon(folded, standalone, area_percentage)
        applications = pd.percentage_applications(gun, 1)
        result = curves.compile_selected_nodes(
            [folded, standalone, area_percentage],
            [row("test", "Armament", "Gun", folded), row("test", "Armament", "Gun", standalone),
             row("test", "Armament", "Gun", area_percentage)],
            applications)
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["terms"]["None"]["flat"], 50)
        # Folded AreaDamage uses rounded runtime units (1), not continuous
        # units (0.0005), and its first Falloff is 50%. HealthPercentageDamage
        # has no spread falloff; AreaDamagePercentage does.
        self.assertAlmostEqual(result["terms"]["None"]["max_hp_fraction"], 0.2 + 0.00005 + 1.11)
        folded_app = next(item for item in result["channel_terms"]
                          if item["warhead_type"] == "AreaDamage")
        self.assertNotEqual(folded_app["percentage_application"]["continuous_units"],
                            folded_app["percentage_application"]["runtime_units"])
        self.assertEqual(folded_app["percentage_units_basis"], "runtime_units")

    def test_extra_flat_chip_is_added_without_percentage_double_count(self):
        main = warhead("Warhead@Main", "AreaDamage", 100)
        chip = warhead("Warhead@Chip", "SpreadDamage", 25)
        gun = weapon(main, chip)
        result = curves.compile_selected_nodes(
            [main, chip], [row("test", "Armament", "Gun", main), row("test", "Armament", "Gun", chip)],
            pd.percentage_applications(gun, 1))
        self.assertEqual(result["status"], "RESOLVED")
        self.assertNotIn("additional_target_payloads", result)
        self.assertEqual(result["terms"]["None"]["flat"], 125)
        self.assertEqual(result["terms"]["None"]["max_hp_fraction"], 0)

    def test_target_and_relationship_filtering_excludes_channel_before_reduction(self):
        ally_infantry = warhead("Warhead@Ally", "AreaDamage", 100)
        r = row("test", "Armament", "Gun", ally_infantry,
                fields={"ValidTargets": "Infantry", "ValidRelationships": "Ally"})
        selected = armor_projection.select_channels(
            [r], active_slots={"Armament"}, target_types={"Ground", "Vehicle"},
            relationship="Enemy", default_valid_targets={"Ground", "Water"},
            default_invalid_targets=set(),
            default_valid_relationships={"Ally", "Neutral", "Enemy"},
            default_invalid_relationships=set(), weapon_valid_target_mode="collateral")
        self.assertEqual(selected["selected"], [])
        self.assertEqual(selected["excluded"][0]["reason"], "warhead_valid_targets_no_overlap")

    def test_selected_shrapnel_withholds_the_whole_combined_total(self):
        main = warhead("Warhead@Main", "AreaDamage", 100)
        shrapnel = warhead("Warhead@Shrapnel", "FireShrapnel", 5)
        gun = weapon(main, shrapnel)
        result = curves.compile_selected_nodes(
            [main, shrapnel], [row("test", "Armament", "Gun", main), row("test", "Armament", "Gun", shrapnel)],
            pd.percentage_applications(gun, 1))
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["terms"])
        self.assertIn("fire_shrapnel_payload_unresolved", result["reason"])

    def test_compile_armament_keeps_damage_less_shrapnel_and_withholds_total(self):
        main = warhead("Warhead@Main", "AreaDamage", 100)
        shrapnel = child("Warhead@Shrapnel", "FireShrapnel",
                         [child("ValidTargets", "Ground")])
        gun = weapon(main, shrapnel)
        actor = Node("actor", "", [child("Armament", children=[child("Weapon", "Gun")])])
        records = curves.compile_armament(
            "actor", {"slot": "Armament", "weapon": "Gun", "pricing": True}, actor, gun)
        vehicle = next(record for record in records if record["scenario"] == "vehicle")
        self.assertEqual(vehicle["status"], "UNRESOLVED")
        self.assertIsNone(vehicle["terms"])
        self.assertIn("fire_shrapnel_payload_unresolved", vehicle["reason"])

    def test_main_damage_keeps_carrier_terms_and_separates_passenger_payload(self):
        main = warhead("Warhead@Main", "AreaDamage", 100)
        passenger = open_topped(damage="7777", amount=1)
        gun = weapon(main, passenger)
        actor = Node("actor", "", [child("Armament", children=[child("Weapon", "Gun")])])
        records = curves.compile_armament(
            "actor", {"slot": "Armament", "weapon": "Gun", "pricing": True}, actor, gun)
        vehicle = next(record for record in records if record["scenario"] == "vehicle")
        self.assertEqual(vehicle["status"], "RESOLVED_PRIMARY_TARGET")
        self.assertFalse(vehicle["full_effect_resolved"])
        self.assertEqual(vehicle["terms"]["None"]["A"], 100)
        self.assertEqual(vehicle["terms"]["None"]["B"], 0)
        payload = vehicle["additional_target_payloads"][0]
        self.assertEqual(payload["type"], "passenger_damage")
        self.assertEqual(payload["damage"], 7777)
        self.assertEqual(payload["amount"], 1)
        self.assertEqual(payload["carrier_hp_contribution"], 0.0)
        self.assertTrue(payload["requires_dynamic_passenger_population"])

    def test_open_topped_only_is_carrier_zero_with_unresolved_passenger_hp(self):
        passenger = open_topped(damage="10000")
        gun = weapon(passenger)
        actor = Node("actor", "", [child("Armament", children=[child("Weapon", "Gun")])])
        records = curves.compile_armament(
            "actor", {"slot": "Armament", "weapon": "Gun", "pricing": True}, actor, gun)
        vehicle = next(record for record in records if record["scenario"] == "vehicle")
        self.assertEqual(vehicle["status"], "RESOLVED_PRIMARY_TARGET")
        self.assertEqual(vehicle["terms"]["None"]["A"], 0)
        self.assertEqual(vehicle["terms"]["None"]["B"], 0)
        self.assertEqual(len(vehicle["additional_target_payloads"]), 1)
        self.assertEqual(vehicle["additional_target_payloads"][0]["amount"], -1)

    def test_open_topped_amount_zero_and_positive_cap_keep_source_semantics(self):
        actor = "actor"
        rows, nodes = [], []
        for amount in (None, 0, 2):
            node = open_topped(key=f"Warhead@Passenger{amount}", amount=amount)
            nodes.append(node)
            rows.append(row(actor, "Armament", "Gun", node))
        result = curves.compile_selected_nodes(nodes, rows, [])
        self.assertEqual(result["status"], "RESOLVED_PRIMARY_TARGET")
        amounts = [payload["amount"] for payload in result["additional_target_payloads"]]
        self.assertEqual(amounts, [-1, 0, 2])
        self.assertTrue(all("random subset" in payload["amount_semantics"]
                            for payload in result["additional_target_payloads"]))

    def test_ticks_are_recorded_without_multiplying_damage(self):
        area = warhead("Warhead@Area", "AreaDamage", 100,
                       extra={"Ticks": "4", "TickDelay": "3", "MaxRadius": "256"})
        gun = weapon(area)
        result = curves.compile_selected_nodes(
            [area], [row("test", "Armament", "Gun", area)],
            pd.percentage_applications(gun, 1))
        self.assertEqual(result["terms"]["None"]["flat"], 100)
        self.assertEqual(result["channel_terms"][0]["shape"],
                         {"Ticks": "4", "TickDelay": "3", "MaxRadius": "256"})

    def test_raw_node_and_exported_row_remain_unchanged(self):
        area = warhead("Warhead@Area", "AreaDamage", 100)
        gun = weapon(area)
        exported = row("test", "Armament", "Gun", area)
        before = copy.deepcopy((gun, exported))
        curves.compile_selected_nodes([area], [exported], pd.percentage_applications(gun, 1))
        self.assertEqual((gun, exported), before)

    def test_actor_slot_weapon_mismatch_is_unresolved_and_no_whole_unit_zero(self):
        actor = Node("actor", "", [child("Armament", children=[child("Weapon", "OtherGun")])])
        records = curves.compile_armament(
            "actor", {"slot": "Armament", "weapon": "Gun", "pricing": True,
                       "requires": "state"}, actor, None)
        self.assertEqual(len(records), len(curves.SCENARIOS))
        self.assertTrue(all(record["status"] == "UNRESOLVED" for record in records))
        self.assertTrue(all("actor_slot_weapon_mismatch" in record["reason"] for record in records))


if __name__ == "__main__":
    unittest.main()
