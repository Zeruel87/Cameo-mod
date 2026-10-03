import pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'tools/balance'))
from armor_projection import combined_flat_curve, interpolate_vehicle_endpoints, four_voice_means


class ArmorProjectionTest(unittest.TestCase):
    def test_flame_split_channels_are_combined_before_interpolation(self):
        curve = combined_flat_curve([
            {'damage': 30000, 'versus': {'light': 0, 'heavy': 8}},
            {'damage': 30000, 'versus': {'light': 50, 'heavy': 0}},
        ], ['light', 'heavy'])
        projected = interpolate_vehicle_endpoints(curve['light'], curve['heavy'])
        self.assertEqual(list(projected.values()), [15000, 11850, 8700, 5550, 2400])

    def test_four_sources_and_real_zero(self):
        curves = {k: {'scout': n} for k, n in zip('abcd', [0, 4, 4, 8])}
        result = four_voice_means(curves, 'abcd', 'scout', blend=.5)
        self.assertEqual(result, {'arithmetic': 4, 'geometric': 0, 'blend': 2})
        with self.assertRaises(ValueError):
            four_voice_means({k: v for k, v in curves.items() if k != 'd'}, 'abcd', 'scout')

    def test_missing_armor_is_not_an_invented_default(self):
        with self.assertRaises(KeyError):
            combined_flat_curve([{'damage': 50, 'versus': {}}], ['light'])
