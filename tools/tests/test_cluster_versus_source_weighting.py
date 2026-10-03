import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'reference'))
import cluster_versus as cv
import propose_family_profiles as families


class SourceWeightingTest(unittest.TestCase):
    def test_large_source_does_not_outvote_small_source(self):
        a = dict(source='a', means={'INF': 100}, span=70)
        b = dict(source='b', means={'INF': 0}, span=10)
        result = cv.profile_of([a] * 9 + [b])
        self.assertEqual(result['macro']['INF'], 50)
        self.assertEqual(result['median_span'], 40)
        self.assertEqual((result['n'], result['sources']), (10, 2))

    def test_missing_axis_is_not_a_zero_vote(self):
        result = cv.profile_of([
            dict(source='a', means={'INF': 10, 'VEH': 80}, span=70),
            dict(source='a', means={'INF': 30, 'VEH': 100}, span=70),
            dict(source='b', means={'INF': 60}, span=10),
        ])
        self.assertEqual(result['macro'], {'INF': 40, 'VEH': 90})

    def test_family_aggregation_receives_one_value_per_source_and_armor(self):
        rows = [dict(source='a', versus={'None': 100})] * 9
        rows += [dict(source='b', versus={'None': 20, 'Light': 80})]
        with patch.object(families.ag, 'to_cameo', side_effect=lambda v: (v, {})):
            buckets = families.source_balanced_buckets(rows)
        self.assertEqual(buckets, {'None': [100, 20], 'Light': [80]})


if __name__ == '__main__':
    unittest.main()
