"""Paired events distinguish damage-weighted value from time coverage."""
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
from status_uptime import paired_damage_value

class EventWeightedStatusTest(unittest.TestCase):
    def test_equal_coverage_does_not_imply_equal_damage_gain(self):
        # Identical ten-tick coverage, but a hit lands inside vs outside it.
        inside = paired_damage_value([('hit', 5, 100, 150)], 20, 10)
        outside = paired_damage_value([('hit', 15, 100, 100)], 20, 10)
        self.assertEqual(inside['added_damage'], 50)
        self.assertEqual(inside['added_dps'], 25)
        self.assertEqual(outside['added_damage'], 0)

    def test_streamed_multiple_same_tick_hits_and_zero_baseline(self):
        result = paired_damage_value((row for row in [('a', 0, 0, 0), ('b', 0, 10, 5)]), 10, 10)
        self.assertEqual(result['event_count'], 2)
        self.assertEqual(result['relative_gain'], -0.5)
        self.assertIsNone(paired_damage_value([], 10, 10)['relative_gain'])

    def test_duplicate_out_of_horizon_and_unknown_damage_refused(self):
        for rows in ([('a', 1, 10, 15), ('a', 2, 10, 15)], [('a', 10, 1, 1)], [('a', 1, None, 1)], [('a', 1, 1, float('nan'))]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                paired_damage_value(rows, 10, 10)
