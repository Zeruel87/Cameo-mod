"""Negative guards for exact published-profile historical adapters."""
import json
import pathlib
import unittest
import _bootstrap  # noqa: F401
from miniyaml import Ruleset
from reviewed_weapon_history import restore_later_profile, historical_copy, trajectory_changes, current_profile_name

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LaterProfileHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.fixture = json.loads((ROOT / 'tools/tests/fixtures/later_profile_history_20260910.json').read_text(encoding='utf-8'))

    def test_exact_checkpoint_provenance_and_modern_payloads(self):
        self.assertEqual(15, len(self.fixture))
        for name, record in self.fixture.items():
            with self.subTest(weapon=name):
                self.assertEqual('584a5e4cb4667820b60388fd05d90090c88513d7', record['current_commit'])
                self.assertRegex(record['before_commit'], r'^[0-9a-f]{40}$')
                current = current_profile_name(self.rules, name)
                before = restore_later_profile(self, self.rules.resolve_weapon(current))
                self.assertEqual(current, before.key)

    def test_changed_numeric_payload_is_rejected(self):
        for name in self.fixture:
            with self.subTest(weapon=name):
                node = self.rules.resolve_weapon(current_profile_name(self.rules, name)).deep_copy()
                main = next(n for n in node.children if n.key.startswith('Warhead@') and n.child('Damage'))
                main.child('Damage').value = str(int(main.get('Damage')) + 1)
                with self.assertRaises(AssertionError):
                    restore_later_profile(self, node)

    def test_reordered_warhead_execution_is_rejected(self):
        for name in self.fixture:
            with self.subTest(weapon=name):
                node = self.rules.resolve_weapon(current_profile_name(self.rules, name)).deep_copy()
                positions = [i for i, n in enumerate(node.children) if n.key.startswith('Warhead@')]
                a, b = positions[0], positions[-1]
                self.assertNotEqual(a, b)
                node.children[a], node.children[b] = node.children[b], node.children[a]
                with self.assertRaises(AssertionError):
                    restore_later_profile(self, node)

    def test_unexpected_trajectory_value_is_rejected(self):
        name = 'RA2LarsRocket'
        self.assertIn(name, trajectory_changes())
        node = self.rules.resolve_weapon(name).deep_copy()
        node.child('Projectile').child('VerticalRateOfTurn').value = '17'
        with self.assertRaises(AssertionError):
            historical_copy(self, node)
