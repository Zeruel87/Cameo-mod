"""Identity-only weapon migration: resolved payloads and every owner trait stay fixed."""
import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
sys.path.insert(0, str(ROOT / 'tools/rename'))
import miniyaml
from dump_resolved import node_to_obj
from safe_rename import load_map
from owned_weapon_history import restore_chained_identity_fields
from reviewed_weapon_history import OwnedCheckpointView, restore_owned_checkpoint_actor

MAP = ROOT / 'tools/rename/rename_map_ra1_soviets_owned_weapons_20260910.yaml'
FIXTURE = ROOT / 'tools/tests/fixtures/soviet_owned_weapons_baseline_20260910.json'


class OwnedWeaponNames(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names, assets = load_map(MAP)
        if assets:
            raise AssertionError('This migration must not rename assets')
        cls.before = json.loads(FIXTURE.read_text(encoding='utf-8'))
        cls.rules = miniyaml.Ruleset(ROOT)

    def test_inventory_is_exact_and_destinations_do_not_collide(self):
        self.assertEqual(len(self.names), 13)
        self.assertEqual(set(self.names), set(self.before['weapons']))
        self.assertEqual(len({x.casefold() for x in self.names.values()}), 13)
        before_keys = json.loads((FIXTURE.parent /
            'soviet_owned_weapons_keys_20260910.json').read_text(encoding='utf-8'))
        self.assertEqual(len(before_keys), 2899)
        self.assertFalse({x.casefold() for x in before_keys} &
                         {x.casefold() for x in self.names.values()})
        for old, new in self.names.items():
            self.assertNotIn(old, self.rules.weapons)
            self.assertIn(new, self.rules.weapons)

    def test_all_resolved_weapon_payloads_are_identical(self):
        history = OwnedCheckpointView(self, self.rules, 'soviet')
        for old, new in self.names.items():
            with self.subTest(weapon=new):
                self.assertEqual(restore_chained_identity_fields(node_to_obj(history.resolve_weapon(new))),
                                 self.before['weapons'][old])

    def test_all_owner_traits_change_only_exact_armament_references(self):
        for actor, snapshot in self.before['actors'].items():
            expected = copy.deepcopy(snapshot)
            for key, trait in expected.items():
                if key.split('@')[0] == 'Armament' and isinstance(trait, dict):
                    weapon = trait.get('Weapon')
                    if weapon in self.names:
                        replacement = self.names[weapon]
                        self.assertTrue(replacement.startswith(actor + '_'))
                        trait['Weapon'] = replacement
            with self.subTest(actor=actor):
                self.assertEqual(restore_owned_checkpoint_actor(self, self.rules, 'soviet', actor),
                                 expected)

    def test_aa_sibling_suffix_is_retained(self):
        for old in ('BTRMachineGun_AA', 'BTRTeslaMachineGun_AA',
                    'BTRTeslaMachineGunArc_AA', 'FLAK-23-AA'):
            self.assertTrue(self.names[old].endswith('_AA'))


if __name__ == '__main__':
    unittest.main()
