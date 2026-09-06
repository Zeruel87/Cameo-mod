"""Audit the two additive runtime state routes, including inherited Hydra data."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
from miniyaml import Node, Ruleset
from audit_physical_state_warheads import (
    duplicate_state_problems, scaled_states, state_scale)


def warhead(singular=100, mapped=100, state='Corrosion', kind='AreaDamage'):
    return Node('Warhead@test', kind, [
        Node('PhysicalStateName', 'Corrosion'),
        Node('PhysicalStateScale', str(singular)),
        Node('PhysicalStates', '', [Node(state, str(mapped))]),
    ])


class StateBindingsTests(unittest.TestCase):
    def test_duplicate_adds_both_routes(self):
        self.assertEqual('200', state_scale(warhead(), 'Corrosion'))
        self.assertEqual(1, len(duplicate_state_problems(warhead())))

    def test_opposite_sign_routes_still_execute_separately(self):
        node = warhead(100, -100)
        self.assertEqual('0', state_scale(node, 'Corrosion'))
        self.assertEqual(1, len(duplicate_state_problems(node)))

    def test_zero_routes_are_inactive(self):
        self.assertEqual([], duplicate_state_problems(warhead(0, 100)))
        self.assertEqual(set(), scaled_states(warhead(0, 0)))

    def test_distinct_state_blend_is_valid(self):
        self.assertEqual([], duplicate_state_problems(warhead(state='Temperature')))

    def test_missing_scale_defaults_to_inactive(self):
        node = Node('Warhead@test', 'AreaDamage', [
            Node('PhysicalStateName', 'Corrosion'),
            Node('PhysicalStates', '', [Node('Corrosion', '100')]),
        ])
        self.assertEqual('100', state_scale(node, 'Corrosion'))
        self.assertEqual([], duplicate_state_problems(node))

    def test_each_standalone_route_is_valid(self):
        for children in ([Node('PhysicalStateName', 'Corrosion'),
                          Node('PhysicalStateScale', '100')],
                         [Node('PhysicalStates', '', [Node('Corrosion', '100')])]):
            node = Node('Warhead@test', 'AreaDamage', children)
            self.assertEqual('100', state_scale(node, 'Corrosion'))
            self.assertEqual([], duplicate_state_problems(node))

    def test_spread_damage_does_not_execute_area_state_fields(self):
        self.assertEqual([], duplicate_state_problems(warhead(kind='SpreadDamage')))

    def test_resolved_hydra_exposes_existing_duplicate_on_both_hits(self):
        weapon = Ruleset(ROOT).resolve_weapon('HydraSpit')
        for key in ('LightChemicalWeapon', 'LightChemicalWeaponPercentage'):
            node = weapon.child('Warhead@' + key)
            self.assertEqual('200', state_scale(node, 'Corrosion'))
            self.assertEqual(1, len(duplicate_state_problems(node)))


if __name__ == '__main__':
    unittest.main()
