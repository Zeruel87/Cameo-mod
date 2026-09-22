"""TD owner identities preserve full payloads, exact slots and source namespaces."""
import ast
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
from owned_weapon_history import restore_chained_identity_fields
from weapon_name_map_checks import assert_no_old_weapon_names, assert_owned_weapon_consumers


def digest(obj):
    obj = restore_chained_identity_fields(obj)
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def ordered(node):
    return [node.key, node.value, [ordered(c) for c in node.children]]


class TDOwnedNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT / 'tools/tests/fixtures/td_owned_names_20260910.json').read_text(encoding='utf-8'))
        cls.rules = Ruleset(ROOT)
        cls.mapping = {old: new for route in cls.before['routes'].values() for old, new in route.items()}

    def test_sixteen_raw_and_resolved_ordered_bodies_are_unchanged(self):
        self.assertEqual(len(self.mapping), 16)
        self.assertEqual(len(set(self.mapping.values())), 16)
        self.assertEqual(self.before['renamed_inheritance_links'], [])
        for old, new in self.mapping.items():
            self.assertNotIn(old, self.rules.weapons)
            resolved = self.rules.resolve_weapon(new)
            self.assertEqual(digest(node_to_obj(resolved)), self.before['weapon_hashes'][old], new)
            self.assertEqual(digest([ordered(c) for c in resolved.children]), self.before['ordered_hashes'][old], new)
            self.assertEqual(digest([ordered(c) for c in self.rules.weapon(new).children]),
                             self.before['raw_ordered_hashes'][old], new)

    def test_twenty_three_exact_armaments_preserve_eight_complete_owners(self):
        self.assertEqual(len(self.before['routes']), 8)
        count = 0
        for actor, slots in self.before['weapon_slots'].items():
            obj = node_to_obj(self.rules.resolve(actor))
            for slot, old in slots.items():
                self.assertEqual(slot.split('@')[0], 'Armament')
                self.assertEqual(obj[slot]['Weapon'], self.mapping[old], (actor, slot))
                obj[slot]['Weapon'] = old
                count += 1
            self.assertEqual(digest(obj), self.before['actor_hashes'][actor], actor)
        self.assertEqual(count, 23)
        self.assertIn('Armament@ra1_allies_alliedsniper', self.before['weapon_slots']['td_gdi_havoc'])

    def test_class_contracts_and_concrete_ownership_remain_exact(self):
        assert_owned_weapon_consumers(self, self.rules, self.before['routes'])
        for old, new in self.mapping.items():
            entry = extract_stats.weapon_entry(self.rules, new)
            expected = self.before['class_contracts'][old]
            self.assertEqual({key: entry[key] for key in expected}, expected, new)

    def test_bike_external_reference_selector_is_not_renamed(self):
        tree = ast.parse((ROOT / 'tools/reference/aggregate_archetype.py').read_text(encoding='utf-8'))
        value = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'ARCHETYPES' for t in n.targets))
        names = ast.literal_eval(value)['missile_he']['openra_warheads']
        self.assertEqual(names, self.before['external_missile_selector'])
        self.assertIn('BikeRockets', names)
        self.assertNotIn(self.mapping['BikeRockets'], names)

    def test_frozen_comparison_files_and_maps_keep_original_contracts(self):
        self.assertEqual(len(self.before['historical_json_hashes']), 2)
        for path, expected in self.before['historical_json_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected, path)
        assert_no_old_weapon_names(self, ROOT, self.mapping)


if __name__ == '__main__':
    unittest.main()
