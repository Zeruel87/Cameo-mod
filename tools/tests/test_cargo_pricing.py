import pathlib
import sys
import unittest
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
sys.path.insert(0, str(ROOT / 'tools/balance'))
from miniyaml import Node
from cargo_pricing import authored_load


def node(key, value='', **fields):
    n = Node(key, value)
    n.children = [Node(k, str(v)) for k, v in fields.items()]
    return n


class CargoPricingTest(unittest.TestCase):
    def rules(self, capacity, names, armed=True):
        carrier = node('carrier')
        carrier.children = [node('Cargo', MaxWeight=capacity, Types='Infantry', InitialUnits=names)]
        if armed:
            carrier.children.append(node('Armament', Weapon='gun'))
        troop = node('troop')
        troop.children = [node('Passenger', CargoType='Infantry', Weight=2), node('Valued', Cost=300)]
        actors = {'carrier': carrier, 'troop': troop}
        return SimpleNamespace(resolve=actors.__getitem__, actor=actors.get)

    def test_weighted_full_load_and_special_budget(self):
        result = authored_load(self.rules(4, 'troop,troop'), 'carrier')
        self.assertEqual(result['issues'], [])
        self.assertEqual(result['passenger_sum'], 600)
        self.assertEqual(result['combat_stat_budget'], 480)

    def test_headcount_does_not_override_overweight(self):
        result = authored_load(self.rules(2, 'troop,troop'), 'carrier')
        self.assertIsNone(result['passenger_sum'])
        self.assertIn('filled weight 4/2', result['issues'])

    def test_empty_and_missing_loads_are_unresolved(self):
        for names in ('', 'missing'):
            result = authored_load(self.rules(2, names), 'carrier')
            self.assertIsNone(result['passenger_sum'])
            self.assertTrue(result['issues'])

    def test_unarmed_transport_has_no_combat_budget(self):
        result = authored_load(self.rules(2, 'troop', False), 'carrier')
        self.assertEqual(result['passenger_sum'], 300)
        self.assertIsNone(result['combat_stat_budget'])
