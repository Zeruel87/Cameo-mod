"""Boundary examples from the reviewed Bullet Tick/ShouldExplode ordering."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference"))
from projectile_travel import timing


def projectile(kind, **fields):
    return {"value": kind, "children": [
        {"key": k, "value": str(v), "children": []} for k, v in fields.items()]}


class TravelTests(unittest.TestCase):
    def test_first_tick_starts_at_source(self):
        # Four interpolation intervals: positions at 0, 1, 2, 3, 4; impact on call 5.
        self.assertEqual(timing(projectile("Bullet", Speed=1024), 4096)["projectile_tick_calls"], [5, 5])

    def test_floor_and_minimum_length(self):
        self.assertEqual(timing(projectile("Bullet", Speed=853), 4096)["flight_interpolation_ticks"], [4, 4])
        self.assertEqual(timing(projectile("Bullet", Speed=10000), 1)["projectile_tick_calls"], [2, 2])

    def test_random_upper_bound_excluded(self):
        self.assertEqual(timing(projectile("Bullet", Speed="512, 1025"), 4096)["projectile_tick_calls"], [5, 9])

    def test_instant_and_guided_are_distinct(self):
        self.assertEqual(timing(projectile("InstantHit"), 4096)["projectile_tick_calls"], [1, 1])
        self.assertEqual(timing(projectile("MissileCA", Speed=853), 4096)["status"], "unresolved")
        motion = timing(projectile('MissileCA', Speed=853, MinimumLaunchSpeed=100, MaximumLaunchSpeed=-1), 4096)['motion_parameters']
        self.assertEqual((motion['minimum_launch_speed'], motion['maximum_launch_speed']), (100, 853))

    def test_visual_beam_duration_and_foreign_speed_do_not_delay_first_hit(self):
        self.assertEqual(timing(projectile('LaserZapCA', Duration=99, Speed=1), 4096)['projectile_tick_calls'], [1, 1])
        self.assertEqual(timing(projectile('ElectricBolt'), 4096)['projectile_tick_calls'], [0, 0])

    def test_disabled_beam_damage_has_no_impact(self):
        self.assertEqual(timing(projectile('TeslaZapCA', Duration=0), 4096)['status'], 'no_impact')
        self.assertEqual(timing(projectile('LaserZapCA', DamageDuration=0), 4096)['status'], 'no_impact')

    def test_cameo_streak_ceil_and_cosmetic_tracers_are_distinct(self):
        self.assertEqual(timing(projectile('Bullet', Speed=853), 4096, bullet_round_up=True)['projectile_tick_calls'], [6, 6])
        tracer = timing(projectile('InstantHitWithFakeBullets', FakeBulletNumber=1, FakeBulletSpeed=1), 4096)
        self.assertEqual(tracer['projectile_tick_calls'], [1, 1])
        self.assertEqual(tracer['cosmetic_tracers']['speed_world_units_per_update'], 1)
        self.assertEqual(timing(projectile('InstantExplode'), 4096)['status'], 'source_impact')

    def test_airburst_offset_changes_endpoint_distance(self):
        sample = timing(projectile('Bullet', Speed=1024, AirburstAltitude='4c0'), 3072)
        self.assertEqual(sample['endpoint_distance_world_units'], 5120)
        self.assertEqual(sample['projectile_tick_calls'], [6, 6])


if __name__ == "__main__":
    unittest.main()
