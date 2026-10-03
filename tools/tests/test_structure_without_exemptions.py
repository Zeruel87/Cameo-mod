"""Raw reachability remains usable after retirement of composite approvals."""
import unittest
from types import SimpleNamespace
import _bootstrap  # noqa: F401
from miniyaml import Node
from survey_weapon_structure import inventory, weapon_reference_sets


def stacked(name, child=None):
    nodes = [Node('Warhead@' + key, 'AreaDamage', [Node('Damage', '100')])
             for key in ('A', 'B')]
    if child:
        nodes.append(Node('Warhead@Shard', 'FireShrapnel', [Node('Weapon', child)]))
    return Node(name, '', nodes)


class RawStructureTests(unittest.TestCase):
    def setUp(self):
        weapons = {'direct': stacked('direct', 'child'),
                   'child': stacked('child'), 'unused': stacked('unused')}
        actor = Node('unit', '', [Node('Armament', '', [Node('Weapon', 'direct')])])
        self.rules = SimpleNamespace(weapons=weapons, actors={'unit': actor},
                                     resolve=lambda name: actor,
                                     resolve_weapon=weapons.get)

    def test_all_raw_stacks_and_excess_are_counted(self):
        counts = inventory(self.rules)['counts']
        self.assertEqual(3, counts['stacked_main_all_concrete'])
        self.assertEqual(2, counts['stacked_main_transitive_weapon_graph'])
        self.assertEqual(1, counts['stacked_main_unreached'])
        self.assertEqual(3, counts['excess_main_warhead_instances_all_concrete'])
        self.assertEqual(0, counts['reviewed_stacked_main_all_concrete'])
        self.assertEqual(3, counts['unreviewed_stacked_main_all_concrete'])

    def test_reference_closure_needs_no_approval_registry(self):
        direct, reachable = weapon_reference_sets(self.rules, set(self.rules.weapons))
        self.assertEqual({'direct'}, direct)
        self.assertEqual({'direct', 'child'}, reachable)

    def test_callers_cannot_restore_exemptions(self):
        with self.assertRaises(TypeError):
            inventory(self.rules, reviewed_predicate=lambda *_: True)


if __name__ == '__main__':
    unittest.main()
