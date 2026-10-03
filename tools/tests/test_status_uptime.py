"""Prevent double-crediting overlapping status sources in diagnostic scenarios."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
from status_uptime import coverage, successful_hit_intervals


class StatusUptimeTest(unittest.TestCase):
    def test_identical_sources_do_not_double_team_benefit(self):
        result = coverage({'a': [(0, 50)], 'b': [(0, 50)]}, 100)
        self.assertEqual(result['covered_ticks'], 50)
        self.assertEqual(result['duplicate_credit_ticks'], 50)
        self.assertEqual(result['marginal_covered_ticks'], {'a': 0, 'b': 0})
        self.assertEqual(result['equal_share_ticks'], {'a': 25, 'b': 25})

    def test_repeated_hits_refresh_presence_without_stacking(self):
        result = coverage({'a': successful_hit_intervals([0, 25, 50], 50)}, 100)
        self.assertEqual(result['covered_ticks'], 100)
        self.assertEqual(result['duplicate_credit_ticks'], 0)
        self.assertEqual(result['equal_share_ticks'], {'a': 100})

    def test_partial_overlap_attributes_only_exclusive_marginal_ticks(self):
        result = coverage({'a': [(-10, 50)], 'b': [(25, 125)]}, 100)
        self.assertEqual(result['covered_ticks'], 100)
        self.assertEqual(result['marginal_covered_ticks'], {'a': 25, 'b': 50})
        self.assertEqual(result['equal_share_ticks'], {'a': 37.5, 'b': 62.5})

    def test_unknown_or_permanent_duration_is_not_assumed_finite(self):
        for duration in (None, 0, -1, True):
            with self.assertRaises(ValueError):
                successful_hit_intervals([0], duration)
        with self.assertRaises(ValueError):
            coverage({'a': [(5, 5)]}, 100)

    def test_streamed_hit_log_is_not_consumed_during_validation(self):
        intervals = successful_hit_intervals((t for t in (0, 25, 50)), 50)
        self.assertEqual(coverage({'stream': intervals}, 100)['covered_ticks'], 100)
        with self.assertRaises(ValueError):
            successful_hit_intervals(iter((0, '25')), 50)


if __name__ == '__main__':
    unittest.main()
