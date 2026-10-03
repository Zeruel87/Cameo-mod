"""One canonical main with an exact positive-hit percentage companion contract."""
import pathlib
import unittest
import _bootstrap  # noqa: F401
from miniyaml import Ruleset
from reviewed_weapon_history import restore_freedom_elite
from audit_three_way_split import main_warhead_nodes
from dump_resolved import node_to_obj


def runtime_falloff(distance, radii, values):
    # AreaDamageWarhead.GetDamageFalloff: exclusive final endpoint, C# division.
    for i in range(1, len(radii)):
        if radii[i] > distance:
            numerator = (values[i] - values[i - 1]) * (distance - radii[i - 1])
            delta = abs(numerator) // (radii[i] - radii[i - 1])
            return values[i - 1] + (-delta if numerator < 0 else delta)
    return 0


class FreedomEliteSingleMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(pathlib.Path(__file__).resolve().parents[2])

    def test_total_and_exact_preserved_payload(self):
        now = self.rules.resolve_weapon('RA2FreedomRocket_elite')
        before = restore_freedom_elite(self, now)
        self.assertEqual(sum(int(n.get('Damage')) for n in main_warhead_nodes(before)), 360000)
        mains = list(main_warhead_nodes(now))
        self.assertEqual([n.key for n in mains], ['Warhead@MissileAP_Medium'])
        self.assertEqual(mains[0].get('Damage'), '360000')
        self.assertEqual(mains[0].get('PercentageScale'), '0')
        for tag in ('Warhead@FlakWeaponPercentage', 'Warhead@ShrapnelWeaponPercentage'):
            self.assertEqual(node_to_obj(before.child(tag)), node_to_obj(now.child(tag)))

    def test_historical_restore_rejects_reordered_events(self):
        node = self.rules.resolve_weapon('RA2FreedomRocket_elite').deep_copy()
        a = next(i for i, n in enumerate(node.children) if n.key == 'Warhead@MissileAP_Medium')
        b = next(i for i, n in enumerate(node.children) if n.key == 'Warhead@Effect')
        node.children[a], node.children[b] = node.children[b], node.children[a]
        with self.assertRaises(AssertionError):
            restore_freedom_elite(self, node)

    def test_percentage_integer_distance_and_friendly_cutoffs(self):
        now = self.rules.resolve_weapon('RA2FreedomRocket_elite')
        before = restore_freedom_elite(self, now)
        old = before.child('Warhead@MissileAP_Medium')
        new = now.child('Warhead@FreedomElitePreservedPercentage')
        self.assertEqual(old.get('Spread'), '64')
        self.assertEqual(new.get('Range'), '0, 32, 33')
        self.assertEqual(new.get('Falloff'), '100, 50, 0')
        self.assertEqual(new.get('Damage'), '6000')
        self.assertEqual(new.get('PercentageDenominator'), '10000')
        self.assertEqual(node_to_obj(old.child('PercentageVersus')), node_to_obj(new.child('Versus')))
        for ally in (False, True):
            old_outer = 64 * (50 if ally else 100) // 100
            new_outer = 33 * (50 if ally else 100) // 100
            for distance in range(66):
                expected = runtime_falloff(distance, [0, 64], [100, 0]) if distance <= old_outer // 2 else 0
                actual = runtime_falloff(distance, [0, 32, 33], [100, 50, 0]) if distance <= new_outer else 0
                self.assertEqual(expected, actual, (distance, ally))
        # The naive clipped endpoint fails exactly at the inclusive old cutoff.
        self.assertEqual(runtime_falloff(32, [0, 32], [100, 50]), 0)
        self.assertEqual(runtime_falloff(32, [0, 32, 33], [100, 50, 0]), 50)
