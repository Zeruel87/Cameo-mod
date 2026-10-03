import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference'))
from dta_armor import ArmorResolver


class ArmorTests(unittest.TestCase):
    def test_explicit_zero_beats_base(self):
        r = ArmorResolver({'WH': {'Modifier.light': '0%', 'Modifier.wood': '500%'},
                           'light': {'BaseArmor': 'wood'}})
        self.assertEqual(r.resolve('WH', 'light')['percent'], 0)

    def test_base_uses_warhead_value_before_own_default(self):
        r = ArmorResolver({'ArmorTypes': {'0': 'naval_light'},
                           'naval_light': {'BaseArmor': 'light', 'Modifier': '1000%'},
                           'light': {'BaseArmor': 'wood'}, 'WH': {'Modifier.wood': '500%'}})
        got = r.resolve('WH', 'naval_light')
        self.assertEqual(got['percent'], 500)
        self.assertEqual(got['route'], ['naval_light', 'light', 'wood'])

    def test_declared_and_engine_defaults(self):
        r = ArmorResolver({'ArmorTypes': {'0': 'medium'},
                           'medium': {'Modifier': '10'}, 'WH': {}})
        self.assertEqual(r.resolve('WH', 'medium')['percent'], 1000)
        self.assertEqual(r.resolve('WH', 'none')['percent'], 100)

    def test_cycle_and_unsupported_positional_are_not_silently_filled(self):
        r = ArmorResolver({'light': {'BaseArmor': 'wood'},
                           'wood': {'BaseArmor': 'light'}, 'WH': {}})
        with self.assertRaises(ValueError):
            r.resolve('WH', 'light')
        with self.assertRaises(ValueError):
            ArmorResolver({'WH': {'Verses': '100%,0%'}}).resolve('WH', 'none')


if __name__ == '__main__':
    unittest.main()
