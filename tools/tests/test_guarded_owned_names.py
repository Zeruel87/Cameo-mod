"""Guarded current names preserve historical evidence and other namespaces."""
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
from weapon_name_map_checks import assert_no_old_weapon_names
from owned_weapon_history import restore_chained_identity_fields


def digest(obj):
    obj = restore_chained_identity_fields(obj)
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def ordered(node):
    return [node.key, node.value, [ordered(c) for c in node.children]]


class GuardedOwnedNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT / 'tools/tests/fixtures/guarded_owned_names_20260910.json').read_text(encoding='utf-8'))
        cls.rules = Ruleset(ROOT)
        cls.mapping = {o: n for r in cls.before['routes'].values() for o, n in r.items()}

    def test_five_full_ordered_weapon_payloads_are_unchanged(self):
        self.assertEqual(len(self.mapping), 5)
        self.assertEqual(len(set(self.mapping.values())), 5)
        for old, new in self.mapping.items():
            self.assertNotIn(old, self.rules.weapons)
            node = self.rules.resolve_weapon(new)
            self.assertEqual(digest(node_to_obj(node)), self.before['weapon_hashes'][old], new)
            self.assertEqual(digest([ordered(c) for c in node.children]), self.before['ordered_hashes'][old], new)

    def test_classes_are_unchanged(self):
        for old, new in self.mapping.items():
            entry = extract_stats.weapon_entry(self.rules, new)
            self.assertEqual({k: entry[k] for k in self.before['class_contracts'][old]},
                             self.before['class_contracts'][old], new)

    def test_three_complete_actors_only_change_six_weapon_references(self):
        count = 0
        for actor, route in self.before['routes'].items():
            reverse = {n: o for o, n in route.items()}
            obj = node_to_obj(self.rules.resolve(actor))
            for key, trait in obj.items():
                if key.split('@')[0] == 'Armament' and trait.get('Weapon') in reverse:
                    trait['Weapon'] = reverse[trait['Weapon']]
                    count += 1
            self.assertEqual(digest(obj), self.before['actor_hashes'][actor], actor)
        self.assertEqual(count, 6)

    def test_exact_references_and_owners(self):
        owners = {n: a for a, route in self.before['routes'].items() for n in route.values()}
        old = {name.casefold() for name in self.mapping}
        for actor in self.rules.actors:
            if actor.startswith('^'):
                continue
            for arm in self.rules.resolve(actor).children_named('Armament'):
                name = arm.get('Weapon')
                self.assertNotIn((name or '').casefold(), old)
                if name in owners:
                    self.assertEqual(actor, owners[name])
        def walk(node):
            # Complete scalar/list entries, not whitespace words within another name.
            self.assertFalse(old & {v.strip().casefold() for v in node.value.split(',')}, node.key)
            for child in node.children:
                walk(child)
        for node in list(self.rules.actors.values()) + list(self.rules.weapons.values()):
            walk(node)

    def test_unrelated_order_name_is_preserved(self):
        order = self.rules.resolve('Player').child('SupportPowerBotASModule').child('Decisions').child('wh40kDeepStrike8').get('OrderName')
        self.assertEqual(order, 'Hellfire Dreadnought Deep Strike')
        self.assertEqual(order, self.before['unrelated_order_name'])

    def test_historical_json_evidence_is_byte_identical(self):
        self.assertEqual(len(self.before['historical_json_hashes']), 3)
        for path, expected in self.before['historical_json_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected, path)

    def test_bundled_maps_have_no_old_weapon_names(self):
        assert_no_old_weapon_names(self, ROOT, self.mapping)


if __name__ == '__main__':
    unittest.main()
