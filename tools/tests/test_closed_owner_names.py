"""Closed combat-owner identities, including inheritance and death weapons."""
import ast
import collections
import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/audit'), str(ROOT / 'tools/balance')]
from miniyaml import Ruleset
from dump_resolved import node_to_obj
import extract_stats
from weapon_name_map_checks import assert_no_old_weapon_names, assert_owned_weapon_consumers


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def ordered(node):
    return [node.key, node.value, [ordered(c) for c in node.children]]


class ClosedOwnerNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT / 'tools/tests/fixtures/closed_owner_names_20260910.json').read_text(encoding='utf-8'))
        cls.rules = Ruleset(ROOT)
        cls.mapping = {o: n for r in cls.before['routes'].values() for o, n in r.items()}
        cls.reverse = {n: o for o, n in cls.mapping.items()}

    def test_twenty_five_complete_ordered_weapon_payloads(self):
        self.assertEqual(len(self.mapping), 25)
        self.assertEqual(len(self.reverse), 25)
        for old, new in self.mapping.items():
            self.assertNotIn(old, self.rules.weapons)
            node = self.rules.resolve_weapon(new)
            self.assertEqual(digest(node_to_obj(node)), self.before['weapon_hashes'][old], new)
            self.assertEqual(digest([ordered(c) for c in node.children]), self.before['ordered_hashes'][old], new)
            if old.endswith('_AA'):
                self.assertTrue(new.endswith('_AA'))

    def test_source_bodies_only_change_ten_internal_inheritance_links(self):
        actual_links = []
        for old, new in self.mapping.items():
            node = self.rules.weapon(new).deep_copy()
            for child in node.children:
                if child.key.split('@')[0] == 'Inherits' and child.value in self.reverse:
                    child.value = self.reverse[child.value]
                    actual_links.append([old, child.key, child.value])
            self.assertEqual(digest([ordered(c) for c in node.children]),
                             self.before['raw_ordered_hashes'][old], new)
        self.assertEqual(len(actual_links), 10)
        self.assertEqual(sorted(actual_links), sorted(self.before['renamed_inheritance_links']))

    def test_original_classes_are_preserved(self):
        for old, new in self.mapping.items():
            entry = extract_stats.weapon_entry(self.rules, new)
            self.assertEqual({k: entry[k] for k in self.before['class_contracts'][old]},
                             self.before['class_contracts'][old], new)

    def test_twelve_complete_actors_only_change_thirty_three_exact_slots(self):
        self.assertEqual(len(self.before['routes']), 12)
        counts = collections.Counter()
        for actor, slots in self.before['weapon_slots'].items():
            obj = node_to_obj(self.rules.resolve(actor))
            for slot, old in slots.items():
                counts[slot.split('@')[0]] += 1
                self.assertEqual(obj[slot]['Weapon'], self.mapping[old], (actor, slot))
                obj[slot]['Weapon'] = old
            self.assertEqual(digest(obj), self.before['actor_hashes'][actor], actor)
        self.assertEqual(dict(counts), {'Armament': 27, 'FireWarheadsOnDeath': 6})

    def test_no_other_consumers_or_old_active_references(self):
        assert_owned_weapon_consumers(self, self.rules, self.before['routes'])

    def test_external_flame_reference_selector_is_not_a_cameo_identity(self):
        tree = ast.parse((ROOT / 'tools/reference/aggregate_archetype.py').read_text(encoding='utf-8'))
        value = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'ARCHETYPES' for t in n.targets))
        names = ast.literal_eval(value)['flame']['openra_warheads']
        self.assertEqual(names, self.before['external_flame_selector'])
        self.assertIn('FireballLauncher', names)
        self.assertNotIn(self.mapping['FireballLauncher'], names)

    def test_historical_comparison_files_are_byte_identical(self):
        self.assertEqual(len(self.before['historical_json_hashes']), 4)
        for path, expected in self.before['historical_json_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected, path)

    def test_bundled_map_references_are_complete(self):
        assert_no_old_weapon_names(self, ROOT, self.mapping)


if __name__ == '__main__':
    unittest.main()
