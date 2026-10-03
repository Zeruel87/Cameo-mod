"""Exact payload and state closure for Naxis/Apocalypse h0 migration."""
import pathlib
import sys
import unittest
import _bootstrap  # noqa: F401
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
from miniyaml import Ruleset
from reviewed_weapon_history import ENDPOINT_COHORT, ALL_ENDPOINTS, restore_endpoint_weapon, current_endpoint_name
import percentage_damage as pd


class CannonAPEndpointCohort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(pathlib.Path(__file__).resolve().parents[2])

    def test_every_endpoint_preserves_all_nonprofile_payload(self):
        self.assertEqual(len(ENDPOINT_COHORT), 8)
        for name in sorted(ENDPOINT_COHORT):
            with self.subTest(weapon=name):
                weapon = self.rules.resolve_weapon(current_endpoint_name(self.rules, name))
                before = restore_endpoint_weapon(self, weapon)
                self.assertEqual(
                    [n.key.replace('CannonAP_Light', 'CannonAP') for n in before.children
                     if n.key.startswith('Warhead')],
                    [n.key for n in weapon.children if n.key.startswith('Warhead')])
                applications = pd.percentage_applications(weapon, 100000)
                self.assertTrue(all(a['runtime_units'] == 0 for a in applications
                                    if a['tag'] == 'CannonAP'))

    def test_historical_restore_rejects_reordered_events(self):
        for name in sorted(ALL_ENDPOINTS):
            with self.subTest(weapon=name):
                node = self.rules.resolve_weapon(current_endpoint_name(self.rules, name)).deep_copy()
                positions = [i for i, n in enumerate(node.children) if n.key.startswith('Warhead@')]
                a, b = positions[0], positions[-1]
                node.children[a], node.children[b] = node.children[b], node.children[a]
                with self.assertRaises(AssertionError):
                    restore_endpoint_weapon(self, node)

    def test_naxis_roots_have_three_preserved_layers(self):
        for name in ('NaxiHetzerDestroyer', 'NaxiAntiTankCannon'):
            self.assertEqual([p for _, p in self.rules.inherits_of(self.rules.weapon(name))],
                             ['^Effect_Explosion_Small_RA2', '^Projectile_Shell_Light', '^Warhead_CannonAP'])

    def test_extended_and_ordos_exact_payload_contracts(self):
        for name in sorted(ALL_ENDPOINTS):
            with self.subTest(weapon=name):
                restore_endpoint_weapon(self, self.rules.resolve_weapon(current_endpoint_name(self.rules, name)))

    def test_separate_percentage_routes_and_custom_geometry_survive(self):
        from reviewed_weapon_history import ORDOS_ENDPOINTS
        from dump_resolved import node_to_obj
        from effective_heaviness import scale_length
        for name in ORDOS_ENDPOINTS:
            weapon = self.rules.resolve_weapon(current_endpoint_name(self.rules, name))
            before = restore_endpoint_weapon(self, weapon)
            companions = lambda w: [node_to_obj(n) for n in w.children if n.value == 'AreaDamagePercentage']
            self.assertEqual(len(companions(weapon)), 4, name)
            self.assertEqual(companions(before), companions(weapon), name)
        for name in ('TSLaser90mm', 'TSLaser90mmDep'):
            weapon = self.rules.resolve_weapon(current_endpoint_name(self.rules, name))
            self.assertEqual(weapon.child('Warhead@LaserWeaponPercentage').get('Damage'), '3')
            folded = [a for a in pd.percentage_applications(weapon, 100000) if a['tag'] == 'CannonAP']
            self.assertEqual([a['runtime_units'] for a in folded], [60])
        cannon = self.rules.resolve_weapon(current_endpoint_name(self.rules, '2Inch')).child('Warhead@CannonAP')
        self.assertEqual(scale_length(int(cannon.get('Spread')), int(cannon.get('Heaviness'))), 300)

    def test_skyhawk_plasma_alternate_is_exactly_isolated(self):
        import json
        from dump_resolved import node_to_obj
        from miniyaml import Node
        fixture = json.loads((pathlib.Path(__file__).parent / 'fixtures' /
                              'cannonap_extended_before_20260910.json').read_text(encoding='utf-8'))
        def rebuild(row):
            return Node(row[0], row[1], [rebuild(c) for c in row[2]])
        before = rebuild(fixture['weapons']['SkyHawkPlasmaCannon'])
        current = self.rules.resolve_weapon('SkyHawkPlasmaCannon')
        self.assertEqual(node_to_obj(before), node_to_obj(current))
        self.assertEqual([n.key for n in before.children if n.key.startswith('Warhead')],
                         [n.key for n in current.children if n.key.startswith('Warhead')])
