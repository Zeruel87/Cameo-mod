"""Synthetic tests for explicit OpenRA armor-channel selection."""
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
from armor_projection import channel_identity, select_channels  # noqa: E402


DEFAULTS = {
    "default_valid_targets": {"GroundActor", "WaterActor", "Infantry", "Air"},
    "default_invalid_targets": set(),
    "default_valid_relationships": {"Ally", "Neutral", "Enemy"},
    "default_invalid_relationships": set(),
}


def channel(slot, *, weapon="MGattG", warhead="Warhead@1Dam", actor="BTR.YURI",
            source="combined_arms", fields=None, **extra):
    row = {"source": source, "actor": actor, "slot": slot, "weapon": weapon,
           "warhead": warhead, "damage": "300", "warhead_type": "SpreadDamage",
           "fields": fields or {}}
    row.update(extra)
    return row


def select(channels, **kwargs):
    return select_channels(channels, active_slots=kwargs.pop("active_slots"),
                           target_types=kwargs.pop("target_types", {"GroundActor"}),
                           relationship=kwargs.pop("relationship", "Enemy"),
                           **DEFAULTS, **kwargs)


class ReferenceChannelSelectionTests(unittest.TestCase):
    def test_cold_and_warm_slots_are_disjoint_and_condition_text_is_not_parsed(self):
        cold = channel("Armament@GROUND", fields={"ValidTargets": "GroundActor"},
                        requires_condition="gattling-ground < 14")
        warm = channel("Armament@GROUND2", fields={"ValidTargets": "GroundActor"},
                        requires_condition="gattling-ground >= 14")
        cold_result = select([cold, warm], active_slots={"Armament@GROUND"})
        warm_result = select([cold, warm], active_slots={"Armament@GROUND2"})
        self.assertEqual(cold_result["selected"], [cold])
        self.assertEqual(warm_result["selected"], [warm])
        self.assertEqual(cold_result["excluded"][0]["reason"], "inactive_slot")
        self.assertEqual(warm_result["excluded"][0]["reason"], "inactive_slot")

    def test_ground_vehicle_target_excludes_infantry_only_channel(self):
        ground = channel("Armament@GROUND", fields={"ValidTargets": "GroundActor, WaterActor"})
        infantry = channel("Armament@INFANTRY", fields={"ValidTargets": "Infantry"},
                           weapon="MGattG.Infantry")
        result = select([ground, infantry],
                        active_slots={"Armament@GROUND", "Armament@INFANTRY"})
        self.assertEqual(result["selected"], [ground])
        self.assertEqual(result["excluded"][0]["reason"], "warhead_valid_targets_no_overlap")

    def test_target_and_slot_tokens_are_case_sensitive(self):
        upper = channel("Armament@GROUND", fields={"ValidTargets": "GroundActor"})
        lower = channel("Armament@ground", fields={"ValidTargets": "groundactor"})
        upper_result = select([upper, lower], active_slots={"Armament@GROUND", "Armament@ground"},
                              target_types={"GroundActor"})
        lower_result = select([upper, lower], active_slots={"Armament@GROUND", "Armament@ground"},
                              target_types={"groundactor"})
        self.assertEqual(upper_result["selected"], [upper])
        self.assertEqual(lower_result["selected"], [lower])
        self.assertEqual(channel_identity(upper)[2], "Armament@GROUND")
        self.assertEqual(channel_identity(lower)[2], "Armament@ground")

    def test_explicit_invalid_target_precedes_valid_and_empty_valid_stays_empty(self):
        invalid = channel("Armament@INVALID", fields={"ValidTargets": "GroundActor",
                                                        "InvalidTargets": "GroundActor"})
        empty = channel("Armament@EMPTY", fields={"ValidTargets": "",
                                                    "InvalidTargets": ""})
        absent = channel("Armament@DEFAULT")
        result = select([invalid, empty, absent],
                        active_slots={"Armament@INVALID", "Armament@EMPTY", "Armament@DEFAULT"})
        self.assertEqual(result["selected"], [absent])
        reasons = {row["channel"]["slot"]: row["reason"] for row in result["excluded"]}
        self.assertEqual(reasons["Armament@INVALID"], "warhead_invalid_target")
        self.assertEqual(reasons["Armament@EMPTY"], "warhead_valid_targets_no_overlap")

    def test_ally_only_healing_is_excluded_for_enemy_relationship(self):
        heal = channel("Armament@HEAL", weapon="Heal", warhead="Warhead@Heal",
                        fields={"ValidTargets": "Healable", "ValidRelationships": "Ally"},
                        damage="-3500")
        ally = select([heal], active_slots={"Armament@HEAL"}, target_types={"Healable"},
                      relationship="Ally")
        enemy = select([heal], active_slots={"Armament@HEAL"}, target_types={"Healable"},
                       relationship="Enemy")
        self.assertEqual(ally["selected"], [heal])
        self.assertEqual(enemy["selected"], [])
        self.assertEqual(enemy["excluded"][0]["reason"], "warhead_valid_relationships_no_match")

    def test_weapon_valid_target_gate_is_explicit_for_direct_vs_collateral(self):
        splash = channel("Armament@SPLASH", fields={"ValidTargets": "GroundActor"},
                         weapon_valid_targets="Air")
        missing = channel("Armament@MISSING", fields={"ValidTargets": "GroundActor"})
        null = channel("Armament@NULL", fields={"ValidTargets": "GroundActor"},
                       weapon_valid_targets=None)
        empty = channel("Armament@EMPTY", fields={"ValidTargets": "GroundActor"},
                        weapon_valid_targets="")
        none = select([splash], active_slots={"Armament@SPLASH"})
        collateral = select([splash], active_slots={"Armament@SPLASH"},
                             weapon_valid_target_mode="collateral")
        direct = select([splash], active_slots={"Armament@SPLASH"},
                        weapon_valid_target_mode="direct")
        self.assertEqual(none["selected"], [splash])
        self.assertEqual(collateral["selected"], [splash])
        self.assertEqual(direct["selected"], [])
        self.assertEqual(direct["excluded"][0]["reason"], "weapon_valid_targets_no_overlap")
        for row in (missing, null):
            with self.subTest(row=row["slot"]):
                direct_result = select([row], active_slots={row["slot"]},
                                       weapon_valid_target_mode="direct")
                collateral_result = select([row], active_slots={row["slot"]},
                                            weapon_valid_target_mode="collateral")
                self.assertEqual(direct_result["excluded"][0]["reason"],
                                 "weapon_valid_targets_unresolved")
                self.assertEqual(collateral_result["selected"], [row])
        empty_direct = select([empty], active_slots={"Armament@EMPTY"},
                              weapon_valid_target_mode="direct")
        empty_collateral = select([empty], active_slots={"Armament@EMPTY"},
                                  weapon_valid_target_mode="collateral")
        self.assertEqual(empty_direct["excluded"][0]["reason"],
                         "weapon_valid_targets_no_overlap")
        self.assertEqual(empty_collateral["selected"], [empty])

    def test_distinct_slots_and_warheads_are_preserved_duplicate_identity_is_rejected(self):
        first = channel("Armament@GROUND")
        second = channel("Armament@GROUND2")
        duplicate = copy.deepcopy(first)
        percentage = channel("Armament@PERCENT", warhead="Warhead@Percent",
                             warhead_type="AreaDamagePercentage", damage="6")
        rows = [first, second, duplicate, percentage]
        before = copy.deepcopy(rows)
        result = select(rows, active_slots={"Armament@GROUND", "Armament@GROUND2",
                                            "Armament@PERCENT"})
        self.assertEqual(result["selected"], [first, second, percentage])
        self.assertEqual(result["excluded"][0]["reason"], "duplicate_channel_identity")
        self.assertEqual(result["selected_identities"], [
            {"source": "combined_arms", "actor": "BTR.YURI", "slot": "Armament@GROUND",
             "weapon": "MGattG", "warhead": "Warhead@1Dam"},
            {"source": "combined_arms", "actor": "BTR.YURI", "slot": "Armament@GROUND2",
             "weapon": "MGattG", "warhead": "Warhead@1Dam"},
            {"source": "combined_arms", "actor": "BTR.YURI", "slot": "Armament@PERCENT",
             "weapon": "MGattG", "warhead": "Warhead@Percent"},
        ])
        self.assertEqual(result["selected"][2]["damage"], "6")
        self.assertEqual(result["selected"][2]["warhead_type"], "AreaDamagePercentage")
        self.assertEqual(rows, before)
        self.assertEqual(channel_identity(first), channel_identity(duplicate))
        self.assertNotEqual(channel_identity(first), channel_identity(second))

    def test_required_review_inputs_cannot_be_omitted_or_inferred(self):
        with self.assertRaises(ValueError):
            select_channels([], active_slots=None, target_types={"GroundActor"}, relationship="Enemy",
                            **DEFAULTS)
        with self.assertRaises(ValueError):
            select_channels([], active_slots=set(), target_types=None, relationship="Enemy", **DEFAULTS)
        with self.assertRaises(ValueError):
            select_channels([], active_slots=set(), target_types={"GroundActor"}, relationship="Enemy",
                            **{**DEFAULTS, "default_valid_targets": None})
        with self.assertRaises(ValueError):
            select_channels([], active_slots=set(), target_types={"GroundActor"}, relationship="Enemy",
                            **{**DEFAULTS, "default_invalid_relationships": None})


if __name__ == "__main__":
    unittest.main()
