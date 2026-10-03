"""Closed owner identity migration: no payload or consumer changes."""
import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
from miniyaml import Ruleset
from dump_resolved import node_to_obj
from weapon_name_map_checks import assert_no_old_weapon_names, assert_owned_weapon_consumers
from owned_weapon_history import restore_chained_identity_fields


def digest(obj):
    obj = restore_chained_identity_fields(obj)
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def ordered(node):
    return [node.key, node.value, [ordered(child) for child in node.children]]


def restore(obj, reverse):
    if isinstance(obj, dict):
        return {key: restore(value, reverse) for key, value in obj.items()}
    if isinstance(obj, list):
        return [restore(value, reverse) for value in obj]
    if isinstance(obj, str):
        parts = obj.split(',')
        if any(part.strip() in reverse for part in parts):
            return ', '.join(reverse.get(part.strip(), part.strip()) for part in parts)
    return obj


class ClosedRemainingNamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT / 'tools/tests/fixtures/closed_remaining_names_20260910.json').read_text())
        cls.rules = Ruleset(ROOT)
        cls.mapping = {old: new for route in cls.before['routes'].values() for old, new in route.items()}
        cls.reverse = {new: old for old, new in cls.mapping.items()}
        later = json.loads((ROOT / 'tools/tests/fixtures/test_lookup_owned_names_20260910.json').read_text())
        cls.later_reverse = {new: old for route in later['routes'].values() for old, new in route.items()}
        latest = json.loads((ROOT / 'tools/tests/fixtures/converter_owned_names_20260910.json').read_text())
        cls.later_reverse.update({new: old for route in latest['routes'].values() for old, new in route.items()})

    def test_fifty_raw_and_resolved_weapon_bodies_are_exact(self):
        self.assertEqual(len(self.mapping), 50)
        self.assertEqual(len(self.reverse), 50)
        for old, new in self.mapping.items():
            self.assertNotIn(old, self.rules.weapons)
            resolved = self.rules.resolve_weapon(new)
            self.assertEqual(digest(restore(node_to_obj(resolved), self.reverse)), self.before['all_weapon_hashes'][old], new)
            for key, node in [('raw_ordered_hashes', self.rules.weapon(new)), ('resolved_ordered_hashes', resolved)]:
                self.assertEqual(digest(restore(restore([ordered(c) for c in node.children], self.later_reverse), self.reverse)), self.before[key][old], new)

    def test_every_complete_owner_is_unchanged_after_identity_reversal(self):
        for actor, expected in self.before['all_actor_hashes'].items():
            self.assertEqual(digest(restore(restore(node_to_obj(self.rules.resolve(actor)), self.later_reverse), self.reverse)), expected, actor)

    def test_exact_consumers_and_map_closure(self):
        assert_owned_weapon_consumers(self, self.rules, self.before['routes'])
        assert_no_old_weapon_names(self, ROOT, self.mapping)

    def test_identity_reversal_does_not_hide_unrelated_strings(self):
        reverse = {'owner_weapon': 'OldWeapon'}
        self.assertEqual(restore({'Weapon': 'owner_weapon', 'Comment': 'prefix owner_weapon suffix'}, reverse),
                         {'Weapon': 'OldWeapon', 'Comment': 'prefix owner_weapon suffix'})


if __name__ == '__main__':
    unittest.main()
