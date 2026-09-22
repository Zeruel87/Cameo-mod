"""Owner identities with an explicitly preserved abstract IFV borrower."""
import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/audit'), str(ROOT / 'tools/balance')]
from miniyaml import Ruleset
from dump_resolved import node_to_obj
from weapon_name_map_checks import assert_no_old_weapon_names, assert_owned_weapon_consumers
import consolidate_reviewed_weapon_roots as reviewed
import extract_stats


def digest(obj):
    from owned_weapon_history import restore_chained_identity_fields
    obj = restore_chained_identity_fields(obj)
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def ordered(node):
    return [node.key, node.value, [ordered(c) for c in node.children]]


class IFVOwnedNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT / 'tools/tests/fixtures/ifv_owned_names_20260910.json').read_text(encoding='utf-8'))
        cls.rules = Ruleset(ROOT)
        cls.mapping = {o: n for route in cls.before['routes'].values() for o, n in route.items()}

    def test_five_complete_ordered_weapon_payloads(self):
        self.assertEqual(len(self.mapping), 5)
        self.assertEqual(len(set(self.mapping.values())), 5)
        for old, new in self.mapping.items():
            self.assertNotIn(old, self.rules.weapons)
            node = self.rules.resolve_weapon(new)
            self.assertEqual(digest(node_to_obj(node)), self.before['weapon_hashes'][old], new)
            self.assertEqual(digest([ordered(c) for c in node.children]), self.before['ordered_hashes'][old], new)

    def test_original_classes_remain_unchanged(self):
        for old, new in self.mapping.items():
            entry = extract_stats.weapon_entry(self.rules, new)
            self.assertEqual({k: entry[k] for k in self.before['class_contracts'][old]},
                             self.before['class_contracts'][old], new)

    def test_four_complete_owners_only_change_seven_armaments(self):
        self.assertEqual(len(self.before['routes']), 4)
        count = 0
        for actor, route in self.before['routes'].items():
            reverse = {n: o for o, n in route.items()}
            obj = node_to_obj(self.rules.resolve(actor))
            for key, trait in obj.items():
                if key.split('@')[0] == 'Armament' and trait.get('Weapon') in reverse:
                    trait['Weapon'] = reverse[trait['Weapon']]
                    count += 1
            self.assertEqual(digest(obj), self.before['actor_hashes'][actor], actor)
        self.assertEqual(count, 7)

    def test_abstract_reference_and_all_seven_ifvs_are_preserved(self):
        obj = node_to_obj(self.rules.resolve('^IFVConditions'))
        self.assertEqual(obj['Armament@hmg']['Weapon'], self.mapping['RAVulcan'])
        obj['Armament@hmg']['Weapon'] = 'RAVulcan'
        self.assertEqual(digest(obj), self.before['ifv_abstract_hash'])
        parents = {a: [p for _, p in self.rules.inherits_of(n)] for a, n in self.rules.actors.items()}
        def is_ifv(actor):
            stack, seen = list(parents[actor]), set()
            while stack:
                name = stack.pop()
                if name == '^IFVConditions':
                    return True
                if name not in seen:
                    seen.add(name)
                    stack.extend(parents.get(name, []))
            return False
        actual = {a for a in self.rules.actors if not a.startswith('^') and is_ifv(a)}
        self.assertEqual(len(actual), 7)
        self.assertEqual(actual, set(self.before['ifv_actor_hashes']))
        for actor in actual:
            node = self.rules.resolve(actor)
            self.assertEqual(node.child('Armament@hmg').get('Weapon'), 'RA2CRM60H')
            self.assertEqual(digest(node_to_obj(node)), self.before['ifv_actor_hashes'][actor], actor)

    def test_no_other_concrete_consumers_or_old_active_references(self):
        assert_owned_weapon_consumers(self, self.rules, self.before['routes'])

    def test_tesla_bomb_remains_exact_preservation_not_a_role_mapping(self):
        name = self.mapping['YakTeslaBomb']
        self.assertIn(name, reviewed.EXACT_PRESERVE)
        self.assertNotIn(name, reviewed.ROLE)
        self.assertNotIn('YakTeslaBomb', reviewed.EXACT_PRESERVE)

    def test_historical_comparison_jsons_are_byte_identical(self):
        self.assertEqual(len(self.before['historical_json_hashes']), 2)
        for path, expected in self.before['historical_json_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected, path)

    def test_bundled_maps_have_no_old_names(self):
        assert_no_old_weapon_names(self, ROOT, self.mapping)


if __name__ == '__main__':
    unittest.main()
