"""Guard the identical Ordos copies removed beside their Atreides originals."""
import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
from miniyaml import Ruleset
from dump_resolved import node_to_obj
from audit_split_definitions import definitions

# Full canonical resolved payloads captured from 0dba5542ff8068179066321ab1aa633a1a4cf82b.
EXPECTED = {
    'OrniBombC': '5ed0f9584957c277f4fc7f653a573ca26fab96ee810b26552a0abbf7fb958cb9',
    'OrniGunC': 'c112974da9e796a0967959e2b082cf30bab7d1736335c680ec0ba2df2d8ba623',
}


class IdenticalDuneCopiesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_one_active_definition_beside_each_parent(self):
        found = definitions()
        for name in EXPECTED:
            with self.subTest(weapon=name):
                self.assertEqual(len(found[name]), 1)
                self.assertTrue(found[name][0].startswith(
                    'ContentPacks/D2k/Atreides/yaml/weapons.yaml:'))

    def test_full_resolved_payloads_unchanged(self):
        for name, expected in EXPECTED.items():
            with self.subTest(weapon=name):
                payload = node_to_obj(self.rules.resolve_weapon(name))
                digest = hashlib.sha256(json.dumps(
                    payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                self.assertEqual(digest, expected)

    def test_range_targets_and_damage_preserved(self):
        bomb = self.rules.resolve_weapon('OrniBombC')
        gun = self.rules.resolve_weapon('OrniGunC')
        self.assertEqual(bomb.get('Range'), '2500')
        self.assertEqual(gun.get('Range'), '6000')
        self.assertEqual(gun.get('MinRange'), '1200')
        self.assertEqual(gun.get('ValidTargets'), 'Ground, Air')
        self.assertEqual(gun.get('Warhead@1Dam', 'ValidTargets'), 'Ground, Air')
        self.assertEqual(gun.get('Warhead@1Dam', 'Damage'), '800')


if __name__ == '__main__':
    unittest.main()
