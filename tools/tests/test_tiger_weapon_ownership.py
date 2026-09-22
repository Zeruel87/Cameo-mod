"""Tiger/Cybertank identities preserve full ordered combat and actor payloads."""
import hashlib
import json
import pathlib
import re
import sys
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools/audit'), str(ROOT/'tools/balance')]
from miniyaml import Ruleset
from dump_resolved import node_to_obj
import extract_stats


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def ordered(node):
    return [node.key, node.value, [ordered(c) for c in node.children]]


class TigerOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT/'tools/tests/fixtures/tiger_owned_weapons_20260910.json').read_text(encoding='utf-8'))
        cls.rules = Ruleset(ROOT)

    def test_four_definitions_have_three_canonical_parents_and_no_local_effect(self):
        names = [n for route in self.before['routes'].values() for n in route.values()]
        self.assertEqual(len(set(names)), 4)
        for name in names:
            node = self.rules.weapon(name)
            parents = [p for _,p in self.rules.inherits_of(node)]
            self.assertEqual(len(parents), 3)
            for prefix in ('^Warhead_', '^Projectile_', '^Effect_'):
                self.assertEqual(sum(p.startswith(prefix) for p in parents), 1)
            self.assertFalse(any(c.value=='CreateEffect' for c in node.children))

    def test_full_payload_and_warhead_order_preserved(self):
        for actor,route in self.before['routes'].items():
            for old,new in route.items():
                with self.subTest(weapon=new):
                    node = self.rules.resolve_weapon(new)
                    self.assertEqual(digest(node_to_obj(node)), self.before['weapon_hashes'][old])
                    self.assertEqual(digest([ordered(c) for c in node.children]), self.before['ordered_hashes'][old])
                    entry = extract_stats.weapon_entry(self.rules,new)
                    self.assertEqual(entry['weapon_class_source'], 'template')
                    self.assertEqual(entry['design_weapon_class'], self.before['weapon_classes'][old])

    def test_complete_actor_payloads_only_change_four_weapon_values(self):
        count = 0
        for actor,route in self.before['routes'].items():
            reverse = {n:o for o,n in route.items()}
            obj = node_to_obj(self.rules.resolve(actor))
            for key,value in obj.items():
                if key.split('@')[0]=='Armament' and value.get('Weapon') in reverse:
                    value['Weapon'] = reverse[value['Weapon']]
                    count += 1
            self.assertEqual(digest(obj),self.before['actor_hashes'][actor])
        self.assertEqual(count,4)

    def test_old_ids_absent_and_new_guns_have_no_other_owners(self):
        owners = {n:a for a,r in self.before['routes'].items() for n in r.values()}
        old = set(self.before['weapon_hashes'])
        self.assertFalse(old & self.rules.weapons.keys())
        for actor in self.rules.actors:
            if actor.startswith('^'): continue
            for arm in self.rules.resolve(actor).children_named('Armament'):
                if arm.get('Weapon') in owners:
                    self.assertEqual(actor,owners[arm.get('Weapon')])
        def walk(node):
            self.assertFalse({x.casefold() for x in re.split(r'[\s,]+',node.value)} &
                             {x.casefold() for x in old},node.key)
            for child in node.children: walk(child)
        for node in list(self.rules.actors.values())+list(self.rules.weapons.values()): walk(node)

    def test_bundled_maps_have_no_old_weapon_references(self):
        pattern = re.compile(r'(?i)(?<![A-Za-z0-9_])(TigerCannon|TigerCannonCryo)(?![A-Za-z0-9_])')
        paths = list((ROOT/'mods/cameo/maps').rglob('*.oramap'))
        self.assertTrue(paths)
        for path in paths:
            with zipfile.ZipFile(path) as archive:
                for entry in archive.infolist():
                    if not entry.filename.lower().endswith(('.yaml','.lua')): continue
                    self.assertLessEqual(entry.file_size,10_000_000)
                    self.assertIsNone(pattern.search(archive.read(entry).decode('utf-8-sig')),
                                      str(path)+':'+entry.filename)
        for path in (ROOT/'mods/cameo/maps').rglob('*'):
            if path.is_file() and path.suffix.lower() in ('.yaml','.lua'):
                self.assertIsNone(pattern.search(path.read_text(encoding='utf-8-sig')),str(path))


if __name__=='__main__': unittest.main()
