"""All-trait, descendant and fragment ownership closures retain all payloads."""
import json
import unittest
from test_closed_remaining_names import ROOT, Ruleset, digest, node_to_obj, ordered, restore
from weapon_name_map_checks import assert_no_old_weapon_names, assert_owned_weapon_consumers, assert_owned_dependency_consumers


class ChainedOwnedNamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT / 'tools/tests/fixtures/chained_owned_names_20260910.json').read_text())
        cls.rules = Ruleset(ROOT)
        cls.mapping = {old: new for route in cls.before['routes'].values() for old, new in route.items()}
        cls.reverse = {new: old for old, new in cls.mapping.items()}

    def test_ninety_one_raw_resolved_and_ordered_payloads_are_exact(self):
        self.assertEqual(len(self.mapping), 91)
        self.assertEqual(len(self.reverse), 91)
        for old, new in self.mapping.items():
            self.assertNotIn(old, self.rules.weapons)
            resolved = self.rules.resolve_weapon(new)
            self.assertEqual(digest(restore(node_to_obj(resolved), self.reverse)), self.before['all_weapon_hashes'][old], new)
            for key, node in [('raw_ordered_hashes', self.rules.weapon(new)), ('resolved_ordered_hashes', resolved)]:
                self.assertEqual(digest(restore([ordered(c) for c in node.children], self.reverse)), self.before[key][old], new)

    def test_complete_actors_and_all_consumer_routes_are_exact(self):
        for actor, expected in self.before['all_actor_hashes'].items():
            self.assertEqual(digest(restore(node_to_obj(self.rules.resolve(actor)), self.reverse)), expected, actor)
        assert_owned_weapon_consumers(self, self.rules, self.before['routes'])
        assert_owned_dependency_consumers(self, self.rules, self.before['routes'])

    def test_map_closure(self):
        assert_no_old_weapon_names(self, ROOT, self.mapping)


if __name__ == '__main__':
    unittest.main()
