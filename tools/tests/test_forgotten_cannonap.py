"""Resolved runtime contract for the bounded Forgotten light CannonAP cohort."""
import pathlib
import hashlib
import json
import sys
import unittest

import _bootstrap  # noqa: F401

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/audit'), str(ROOT / 'tools/balance')]
from miniyaml import Ruleset
from dump_resolved import node_to_obj
import effective_heaviness as eh
import percentage_damage as pd


class ForgottenCannonAP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_resolved_profile_and_firing_contract(self):
        for name, damage, reload, range_, speed in (
            ('TSHighVelocity', 30000, 90, 7701, 850),
            ('TSHighVelocity2', 40000, 55, 8207, 850),
            ('TSHighVelocityTur', 48000, 30, 9483, 1280),
        ):
            with self.subTest(weapon=name):
                weapon = self.rules.resolve_weapon(name)
                main = weapon.child('Warhead@CannonAP')
                self.assertIsNotNone(main)
                self.assertIsNone(weapon.child('Warhead@CannonAP_Light'))
                self.assertEqual(main.get('Damage'), str(damage))
                self.assertEqual(main.get('Heaviness'), '0')
                self.assertEqual(main.get('HeavinessMode'), 'SharedVersus')
                self.assertEqual(main.get('PercentageScale'), '2000')
                self.assertEqual(eh.scale_length(int(main.get('Spread')), 0), 80)
                self.assertEqual(weapon.get('ReloadDelay'), str(reload))
                self.assertEqual(weapon.get('Range'), str(range_))
                self.assertEqual(weapon.child('Projectile').get('Speed'), str(speed))
                for hp in (10000, 100000, 1000000):
                    self.assertTrue(all(a['runtime_units'] == 0 for a in
                                        pd.percentage_applications(weapon, hp)))

    def test_warhead_execution_order_matches_published_source(self):
        # Resolved from source5a931844, replacing only the old main tag.
        expected = ['Warhead@3Eff', 'Warhead@2Smu', 'Warhead@4EffWater',
                    'Warhead@CannonAP', 'Warhead@Glow', 'Warhead@Smudge',
                    'Warhead@DuneRock', 'Warhead@DuneSand', 'Warhead@RA2Crater',
                    'Warhead@Effect', 'Warhead@EffectWater', 'Warhead@EffectAir',
                    'Warhead@ShieldHit', 'Warhead@Concrete', 'Warhead@ShieldHitEffect']
        def assert_order(node):
            self.assertEqual([n.key for n in node.children if n.key.startswith('Warhead@')], expected)
        for name in ('TSHighVelocity', 'TSHighVelocity2', 'TSHighVelocityTur'):
            with self.subTest(weapon=name):
                node = self.rules.resolve_weapon(name).deep_copy()
                assert_order(node)
                a = next(i for i, n in enumerate(node.children) if n.key == 'Warhead@CannonAP')
                b = next(i for i, n in enumerate(node.children) if n.key == 'Warhead@3Eff')
                node.children[a], node.children[b] = node.children[b], node.children[a]
                with self.assertRaises(AssertionError):
                    assert_order(node)

    def test_chemical_alternates_remain_legacy(self):
        baseline = {
            'TSHighVelocityChem': '46a714c8d35603fcd19c51b7a4c669f4d09b151a4db91408b5e5fdc35131de7c',
            'TSHighVelocity2Chem': 'f37eb48f8f6cbe9c5e05a1b7c57e27a7e633b48cfc2ce704e99ddfe336f138ac',
        }
        for name, damage in (('TSHighVelocityChem', '45000'),
                             ('TSHighVelocity2Chem', '60000')):
            weapon = self.rules.resolve_weapon(name)
            self.assertEqual(hashlib.sha256(json.dumps(node_to_obj(weapon),
                                                      sort_keys=True).encode()).hexdigest(),
                             baseline[name])
            self.assertIsNone(weapon.child('Warhead@CannonAP'))
            self.assertEqual(weapon.child('Warhead@CannonChem_Light').get('Damage'), damage)
            self.assertIsNotNone(weapon.child('Warhead@Cloud'))

    def test_nonprofile_payload_matches_pre_migration(self):
        # Captured from 5a931844a3c6184fbfdd9f50fc8724b37543c5e0.
        baseline = {
            'TSHighVelocity': '25d51895685cd0732f318b10df87d2c88ca81ca4332a58cc6a30dadb1983a562',
            'TSHighVelocity2': '178f6dcbfe2e528090b67a27f3032da2764454407b85ad1566574ce36fd33c65',
            'TSHighVelocityTur': 'ede76b8592fe450251545aac41f38ba781d4c7bcec489ef8f0db09d4c8b8cd33',
        }
        profile = {'Versus', 'PercentageVersus', 'PercentageVersusLight',
                   'PercentageVersusHeavy', 'PercentageScale', 'Heaviness',
                   'HeavinessMode', 'Spread'}
        for name, expected in baseline.items():
            weapon = node_to_obj(self.rules.resolve_weapon(name))
            main = weapon.pop('Warhead@CannonAP')
            weapon['main'] = {k: v for k, v in main.items() if k not in profile}
            self.assertEqual(hashlib.sha256(json.dumps(weapon, sort_keys=True).encode())
                             .hexdigest(), expected, name)

    def test_third_owner_and_no_weapon_descendants(self):
        actor = self.rules.resolve('forgotten_brokenwarriortankturret')
        self.assertEqual(actor.child('Armament@PRIMARY').get('Weapon'), 'TSHighVelocityTur')
        self.assertIsNone(actor.child('Armament@UPGRADE'))
        cohort = {'TSHighVelocity', 'TSHighVelocity2', 'TSHighVelocityTur'}
        owners = set()
        def scan(node, owner):
            if node.key == 'Weapon' and node.value in cohort:
                owners.add((owner, node.value))
            for child in node.children:
                scan(child, owner)
        for name in self.rules.actors:
            scan(self.rules.actor(name), name)
        self.assertEqual(owners, {
            ('forgotten_tankkiller', 'TSHighVelocity'),
            ('forgotten_warriortank', 'TSHighVelocity2'),
            ('forgotten_brokenwarriortankturret', 'TSHighVelocityTur'),
        })
        for name in self.rules.weapons:
            raw = self.rules.weapon(name)
            self.assertFalse(any(n.key.split('@')[0] == 'Inherits' and n.value in cohort
                                 for n in raw.children), name)

    def test_owner_switches_are_not_enabled_by_this_migration(self):
        for actor, normal, chemical in (
            ('forgotten_tankkiller', 'TSHighVelocity', 'TSHighVelocityChem'),
            ('forgotten_warriortank', 'TSHighVelocity2', 'TSHighVelocity2Chem'),
        ):
            resolved = self.rules.resolve(actor)
            self.assertEqual(resolved.child('Armament@PRIMARY').get('Weapon'), normal)
            self.assertEqual(resolved.child('Armament@UPGRADE').get('Weapon'), chemical)
            self.assertEqual(resolved.child('Armament@PRIMARY').get('RequiresCondition'),
                             '!forgotten_upgrade_chemicalweapons')
            self.assertEqual(resolved.child('Armament@UPGRADE').get('RequiresCondition'),
                             'forgotten_upgrade_chemicalweapons')
            self.assertFalse(any(n.get('Condition') == 'forgotten_upgrade_chemicalweapons'
                                 for n in resolved.children))


if __name__ == '__main__':
    unittest.main()
