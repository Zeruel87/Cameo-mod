import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/rule_driven_final_tranches_manifest.json"
INVENTORY = ROOT / "docs/audit/latest/weapon_structure_inventory.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_rule_driven_blast_ordnance as blast
import consolidate_rule_driven_legacy_energy as legacy
from audit_three_way_split import SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset


EXPECTED_SOURCE_DIGEST = (
    "9c29d1c92b029ce73a6e8dc98b15464e69bd469250ca80bbbb518b6b5cf480ec")
EXPECTED_CHANGE_KIND_DIGESTS = {
    "armor_profile": "f99cc89dd067ce5fd60500bed481fb0dc0c25801fcb6094bbd8a0f9c79bce649",
    "blast_shape": "9abf6c8897774c9b2da03e096e9e54f80ac7e5c17190b2715a7e56706a656eee",
    "invalid_target_damage": "ac797644e1b51e615fedaeb000f82692b4ada9a01a6a805c6d662c4601f1538e",
    "percentage_damage": "e4f5b1361839eb99b8c136e5b893c9156c11c5ebdd71e67c7149b662e1003c50",
    "percentage_warheads": "92da644b83a26e37d79aec4f0584c7943255675fe62fb510dae3b33eac85da35",
    "physical_state_bindings": "1912186ff3d59fcaba83dc09fcac97ea7c18f2cb1b6a0d433744d506d0d16bf9",
    "relationship_stat_damage": "e32e52856c5d0f845e53f98b081e03d13e1dbd356f91ed54ef78aade6554572f",
    "valid_target_damage": "93cd1c31a9bc8ae53c61081a3b610f2ec25567b58bd441a1a7f2ee0f303a32d7",
}
EXPECTED_PERCENTAGE_ROUNDING = {
    "digest": "367b54adc7f441a9ab1c3d4dc3e6ea7a7db2d343e4844e2525cc1cb1ebd29dd3",
    "max_absolute_delta": 1,
    "row_count": 93,
}


class RuleDrivenFinalTrancheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.rules = Ruleset(ROOT)
        cls.selected = set(blast.SELECTED) | set(legacy.DESTINATIONS)

    def test_converters_are_fully_applied(self):
        blast.validate_result()
        legacy.validate_result()

    def test_comparison_scope_is_exact(self):
        self.assertEqual(151, len(self.selected))
        self.assertEqual(self.selected, set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])

    def test_only_authorized_role_dimensions_change(self):
        allowed = {
            "percentage_damage", "valid_target_damage",
            "invalid_target_damage", "relationship_stat_damage",
            "physical_state_bindings", "armor_profile",
            "percentage_warheads", "blast_shape",
        }
        kinds = {
            kind for changes in self.report["changed"].values()
            for kind in changes
        }
        self.assertTrue(kinds <= allowed, sorted(kinds - allowed))
        self.assertNotIn("main_damage", kinds)
        self.assertNotIn("non_damage_warheads", kinds)

    def test_comparison_values_are_exactly_pinned(self):
        self.assertEqual(EXPECTED_SOURCE_DIGEST, self.report["source_digest"])
        self.assertEqual(
            EXPECTED_CHANGE_KIND_DIGESTS,
            self.report["change_kind_digests"])

    def test_percentage_rounding_is_bounded(self):
        self.assertEqual(
            EXPECTED_PERCENTAGE_ROUNDING, self.report["percentage_rounding"])

    def test_every_selected_weapon_has_one_main(self):
        destinations = dict(blast.SELECTED)
        destinations.update(legacy.DESTINATIONS)
        for name, destination in sorted(destinations.items()):
            self.assertEqual(
                [f"{destination}FlatCompatibility"],
                main_warheads(self.rules.resolve_weapon(name)), name)

    def test_generated_parent_percentage_routes_do_not_accumulate(self):
        for name in sorted(self.selected):
            pending = [
                parent for _key, parent
                in self.rules.inherits_of(self.rules.weapon(name))
            ]
            seen = set()
            parent_companions = set()
            while pending:
                parent = pending.pop()
                if parent in seen:
                    continue
                seen.add(parent)
                local = self.rules.weapon(parent)
                if local is None:
                    continue
                if parent in self.selected:
                    parent_companions.update(
                        child.key for child in local.children
                        if child.key.startswith(f"Warhead@Collapsed{parent}"))
                pending.extend(
                    grandparent for _key, grandparent
                    in self.rules.inherits_of(local))
            resolved_keys = {
                child.key for child in self.rules.resolve_weapon(name).children
            }
            self.assertTrue(
                parent_companions.isdisjoint(resolved_keys),
                f"{name}: inherited {sorted(parent_companions & resolved_keys)}")

    def test_legacy_children_remain_outside_the_changed_set(self):
        isolated = {
            child
            for _root, (_legacy, children) in blast.ISOLATIONS.items()
            for child in children
        } - self.selected | {"IdolCannon"}
        self.assertTrue(isolated.isdisjoint(self.report["changed"]))

    def test_sandmarine_cryo_keeps_only_its_fixed_state_payload(self):
        weapon = self.rules.resolve_weapon("SandmarineTuskCryo")
        main = weapon.child("Warhead@MissileCryo_HeavyFlatCompatibility")
        self.assertIsNone(main.child("PhysicalStates"))
        self.assertIsNone(main.get("PhysicalStateName"))
        self.assertEqual(
            "-2000", weapon.child("Warhead@PhysicalStateCryo").get("Amount"))

    def test_backlog_and_audit_ratchets_match_the_checkpoint(self):
        counts = self.inventory["counts"]
        self.assertEqual(240, counts["stacked_main_transitive_weapon_graph"])
        self.assertEqual(190, counts["stacked_main_direct_actor_armament"])
        self.assertEqual(50, counts["stacked_main_indirect_weapon_graph"])
        self.assertEqual(340, counts["stacked_main_all_concrete"])
        self.assertEqual(114, SPLIT_BASELINE)
        self.assertEqual(90, BROADCAST_BASELINE)


if __name__ == "__main__":
    unittest.main()
