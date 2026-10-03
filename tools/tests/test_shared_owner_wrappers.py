"""Transparent owner identities preserve shared roots and outside consumers."""
import hashlib
import json
import sys
import unittest
from test_closed_remaining_names import ROOT, Ruleset, node_to_obj, ordered, restore
sys.path.insert(0, str(ROOT / 'tools/balance'))
import extract_stats
from owned_weapon_wrappers import IDENTITY_WRAPPERS, is_reviewed_owner_wrapper


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class SharedOwnerWrapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT / 'tools/tests/fixtures/shared_owner_wrappers_20260910.json').read_text())
        cls.rules = Ruleset(ROOT)
        cls.reverse = {new: old for route in cls.before['routes'].values() for old, new in route.items()}

    def test_fifty_seven_wrappers_pin_shared_roots_and_materialized_bodies(self):
        self.assertEqual(len(self.reverse), 57)
        self.assertEqual(self.reverse, IDENTITY_WRAPPERS)
        aliases = [new for new in self.reverse if is_reviewed_owner_wrapper(self.rules, new)]
        self.assertEqual(len(aliases), 4)
        for new, old in self.reverse.items():
            self.assertIn(old, self.rules.weapons)
            raw = self.rules.weapon(new)
            if is_reviewed_owner_wrapper(self.rules, new):
                self.assertEqual([(c.key, c.value, c.children) for c in raw.children], [('Inherits', old, [])])
                targets = [(old, self.before['all_weapon_hashes'][old]),
                           (new, self.before['all_weapon_hashes'][old])]
            else:
                targets = [(old, self.before['all_weapon_hashes'][old]),
                           (new, self.before['materialized_wrappers'][new]['resolved'])]
            for name, expected in targets:
                resolved = self.rules.resolve_weapon(name)
                self.assertEqual(digest(node_to_obj(resolved)), expected, name)
                if name == old:
                    self.assertEqual(digest([ordered(c) for c in resolved.children]),
                                     self.before['resolved_ordered_hashes'][old], name)
                    entry = extract_stats.weapon_entry(self.rules, name)
                    self.assertEqual([entry['design_weapon_class'], entry['weapon_class_source']],
                                     self.before['class_contracts'][old], name)

    def test_historical_closure_exception_is_exact_and_fail_closed(self):
        from miniyaml import Node
        from types import SimpleNamespace
        name = 'td_gdi_apc_apcgun'
        original = Node(name, '', [Node('Inherits', 'APCGun')])
        self.assertTrue(is_reviewed_owner_wrapper(SimpleNamespace(weapons={name: original}), name))
        for changed in (
            Node(name, '', [Node('Inherits', 'OtherWeapon')]),
            Node(name, '', [Node('Inherits', 'APCGun'), Node('ReloadDelay', '1')]),
            Node(name, '', [Node('Inherits', 'APCGun', [Node('Damage', '1')])]),
            Node(name, 'Unexpected', [Node('Inherits', 'APCGun')]),
        ):
            self.assertFalse(is_reviewed_owner_wrapper(SimpleNamespace(weapons={name: changed}), name))
        self.assertFalse(is_reviewed_owner_wrapper(SimpleNamespace(weapons={'unlisted': original}), 'unlisted'))

    def test_complete_owners_change_only_declared_identity_values(self):
        for actor, route in self.before['routes'].items():
            node = self.rules.resolve(actor)
            weapons = {c.get('Weapon') for c in node.children}
            self.assertTrue(set(route.values()) <= weapons, actor)
            self.assertFalse(set(route) & weapons, actor)
            self.assertEqual(digest(restore(node_to_obj(node), self.reverse)), self.before['all_actor_hashes'][actor], actor)

    def test_legacy_map_alias_is_exactly_unchanged(self):
        self.assertEqual(digest(node_to_obj(self.rules.resolve('E3'))),
                         'ae386061df6f2cc2cd6d06a7bf4267f11df76d12132aa0861dee42312f1932a5')
        weapons = {c.get('Weapon') for c in self.rules.resolve('E3').children_named('Armament')}
        self.assertEqual(weapons, {'Rockets', 'RocketsAMT'})

    def test_only_canonical_owner_uses_wrapper(self):
        owners = {new: actor for actor, route in self.before['routes'].items() for new in route.values()}
        seen = set()
        for actor in self.rules.actors:
            if actor.startswith('^'):
                continue
            for trait in self.rules.resolve(actor).children:
                weapon = trait.get('Weapon')
                if weapon in owners:
                    self.assertIn(actor, {owners[weapon]}, weapon)
                    seen.add(weapon)
        self.assertEqual(seen, set(owners))


if __name__ == '__main__':
    unittest.main()
