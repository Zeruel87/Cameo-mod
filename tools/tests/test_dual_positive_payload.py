"""Reviewed positive dual-target payloads; zero/status-only events stay untouched."""
import copy
import json
import pathlib
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
from dump_resolved import node_to_obj
from miniyaml import Ruleset

class PositiveDualPayloadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.fixture = json.loads((pathlib.Path(__file__).parent / 'fixtures/dual_positive_payload_history_20260910.json').read_text(encoding='utf-8'))

    def test_only_reviewed_masks_changed(self):
        for name, changes in self.fixture['changed_fields'].items():
            expected = copy.deepcopy(self.fixture['before'][name])
            for path, old, new in changes:
                _, key, field = path.split('/')
                self.assertEqual(field, 'ValidTargets')
                self.assertGreater(int(expected[key]['Damage']), 0)
                self.assertEqual(expected[key].get(field), old)
                self.assertEqual(new, (old if old is not None else 'Ground, Water') + ', Air')
                expected[key][field] = new
            self.assertEqual(expected, self.fixture['after'][name])
            self.assertEqual(expected, node_to_obj(self.rules.resolve_weapon(name)))

    def test_custom_ship_scope_preserved(self):
        node = self.rules.resolve_weapon('FutureHarbingerCannon_elite')
        self.assertEqual(node.get('Warhead@HeavyBombPercentage', 'ValidTargets'), 'Ground, Ship, Air')

    def test_zero_damage_events_unchanged(self):
        for name, keys in {'RA2CosmonautLaser': ['Warhead@Bullet_Light', 'Warhead@Bullet_Light_Percentage'], 'TSProton': ['Warhead@1Dam']}.items():
            current = node_to_obj(self.rules.resolve_weapon(name))
            for key in keys:
                self.assertEqual(int(current[key].get('Damage', '0')), 0)
                self.assertEqual(current[key], self.fixture['before'][name][key])

