"""Historical reconciliation must not hide unreviewed live changes."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools/audit"))
from miniyaml import Node
from reviewed_weapon_history import (historical_copy, restore_target_policy_fields,
    OwnedCheckpointView, restore_owned_checkpoint_actor, restore_owned_checkpoint_node)


class ReviewedHistoryTests(unittest.TestCase):
    def test_owned_checkpoint_rejects_unreviewed_payload_change(self):
        from miniyaml import Ruleset
        root = pathlib.Path(__file__).resolve().parents[2]
        rules = Ruleset(root)
        live = rules.resolve_weapon('ra1_allies_sheridanassaulttank_cannon')
        restored = OwnedCheckpointView(self, rules, 'additional').resolve_weapon(live.key)
        self.assertEqual(live.key, restored.key)
        self.assertEqual('2000', live.get('Warhead@CannonAP_Light', 'Damage'))
        self.assertEqual('8000', restored.get('Warhead@CannonAP_Light', 'Damage'))
        mutated = live.deep_copy()
        damage = next(child.child('Damage') for child in mutated.children
                      if child.key.startswith('Warhead@') and child.child('Damage'))
        damage.value = str(int(damage.value) + 1)
        with self.assertRaises(AssertionError):
            restore_owned_checkpoint_node(self, 'additional', 'resolved_weapons', mutated)

    def test_owned_actor_checkpoint_rejects_unreviewed_change(self):
        from miniyaml import Ruleset
        root = pathlib.Path(__file__).resolve().parents[2]
        rules = Ruleset(root)

        class MutatedRules:
            def resolve(_, actor):
                node = rules.resolve(actor).deep_copy()
                node.child('Valued').child('Cost').value = '1'
                return node

        with self.assertRaises(AssertionError):
            restore_owned_checkpoint_actor(
                self, MutatedRules(), 'soviet', 'ra1_soviets_btr80')

    def test_sonic_history_rejects_unrecorded_damage_change(self):
        from miniyaml import Ruleset
        from reviewed_weapon_history import restore_sonic_family
        root = pathlib.Path(__file__).resolve().parents[2]
        live = Ruleset(root).resolve_weapon('TSHellfireSonic')
        old = restore_sonic_family(self, live)
        self.assertEqual('42000', old.get('Warhead@Sonic_Medium', 'Damage'))
        self.assertEqual('42000', live.get('Warhead@MissileSonic_Medium', 'Damage'))
        live.child('Warhead@MissileSonic_Medium').child('Damage').value = '42001'
        with self.assertRaises(AssertionError):
            restore_sonic_family(self, live)

    def test_target_history_asserts_new_mask_and_preserves_live_node(self):
        from miniyaml import Ruleset
        root = pathlib.Path(__file__).resolve().parents[2]
        live = Ruleset(root).resolve_weapon('RA2FlakTrackAAGun')
        old = restore_target_policy_fields(self, live)
        self.assertEqual('Air', live.get('Warhead@SmallArmsPercentage', 'ValidTargets'))
        self.assertEqual('Ground, Water', old.get('Warhead@SmallArmsPercentage', 'ValidTargets'))
        live.child('Warhead@SmallArmsPercentage').child('ValidTargets').value = 'Ground'
        with self.assertRaises(AssertionError):
            restore_target_policy_fields(self, live)

    def fixture(self, value="102"):
        return Node("GrenadeRA", "", [Node("ReloadDelay", "40"),
            Node("Warhead@Demolition_Light", "AreaDamage", [
                Node("Damage", "12345"), Node("Versus", "", [Node("COMPOSITE", value)])])])

    def test_reverses_only_the_reviewed_field_without_mutating_live_node(self):
        live = self.fixture()
        old = historical_copy(self, live)
        self.assertEqual("102", live.get("Warhead@Demolition_Light", "Versus", "COMPOSITE"))
        self.assertEqual("101", old.get("Warhead@Demolition_Light", "Versus", "COMPOSITE"))
        self.assertEqual("12345", old.get("Warhead@Demolition_Light", "Damage"))
        self.assertEqual("40", old.get("ReloadDelay"))

    def test_unreviewed_value_is_rejected_not_normalized(self):
        with self.assertRaises(AssertionError):
            historical_copy(self, self.fixture("103"))

    def test_missing_reviewed_field_is_rejected(self):
        live = self.fixture()
        live.child("Warhead@Demolition_Light").child("Versus").children.clear()
        with self.assertRaises(AssertionError):
            historical_copy(self, live)

    def test_unlisted_weapon_is_not_rewritten(self):
        live = self.fixture()
        live.key = "UnreviewedWeapon"
        self.assertEqual("102", historical_copy(self, live).get("Warhead@Demolition_Light", "Versus", "COMPOSITE"))

    def test_corrosion_reconstruction_rejects_an_extra_live_field(self):
        warhead = Node("Warhead@HeavyChemicalWeaponPercentage", "AreaDamagePercentage",
                       [Node("Field" + str(n), str(n)) for n in range(7)] +
                       [Node("PhysicalStates", "", [Node("Corrosion", "100")])])
        live = Node("PhobosLaser", "", [warhead])
        old = historical_copy(self, live).children[0]
        self.assertEqual(["PhysicalStateName", "PhysicalStateScale"], [n.key for n in old.children[8:]])
        self.assertEqual(8, len(warhead.children))
        warhead.children.append(Node("NewField", "1"))
        with self.assertRaises(AssertionError):
            historical_copy(self, live)


if __name__ == "__main__":
    unittest.main()
