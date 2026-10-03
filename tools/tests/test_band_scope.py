import sys
from pathlib import Path
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'balance'),
               str(Path(__file__).resolve().parents[1]/'audit')]
from miniyaml import Node
from check_band import armament_scope_details


class Rules:
    def resolve_weapon(self, name):
        return Node(name, '', [Node('Warhead@Shrapnel', 'FireShrapnel')] if name == 'upgrade' else [])


def arm(name, requires=None, damage=100):
    return {'slot': name, 'weapon': name, 'requires': requires,
            'damage_warheads': [{'tag':'Main','type':'AreaDamage','damage':damage}],
            'reload_delay': 10}


class BandScopeTests(unittest.TestCase):
    def test_upgrade_payload_is_not_a_baseline_limitation(self):
        rows = armament_scope_details({'armaments':[arm('base'),arm('upgrade','upgrade')]}, Rules())
        self.assertTrue(rows[0]['contributes_to_raw_armament_term'])
        self.assertFalse(rows[1]['baseline_eligible'])
        self.assertIn('unmodeled_secondary_payload:FireShrapnel', rows[1]['source_limitations'])

    def test_pure_emitter_is_eligible_but_omitted_by_raw_damage_proxy(self):
        row = armament_scope_details({'armaments':[arm('upgrade',damage=0)]}, Rules())[0]
        self.assertTrue(row['baseline_eligible'])
        self.assertFalse(row['contributes_to_raw_armament_term'])
        self.assertIn('unmodeled_secondary_payload:FireShrapnel', row['source_limitations'])


if __name__ == '__main__':
    unittest.main()
