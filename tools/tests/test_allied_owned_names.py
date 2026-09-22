"""Fourteen identities preserve combat, full owners, muzzle smoke and map data."""
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
from owned_weapon_history import restore_chained_identity_fields


def digest(obj):
    obj = restore_chained_identity_fields(obj)
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def ordered(n): return [n.key,n.value,[ordered(c) for c in n.children]]


from reviewed_weapon_history import restore_target_policy_fields

class AlliedOwnedNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads((ROOT/'tools/tests/fixtures/allied_owned_names_20260910.json').read_text(encoding='utf-8'))
        cls.rules = Ruleset(ROOT)
        cls.mapping = {o:n for route in cls.before['routes'].values() for o,n in route.items()}

    def test_all_fourteen_definitions_and_ordered_payloads_are_preserved(self):
        self.assertEqual(len(self.mapping),14)
        self.assertEqual(len(set(self.mapping.values())),14)
        for old,new in self.mapping.items():
            with self.subTest(weapon=new):
                self.assertNotIn(old,self.rules.weapons)
                node = self.rules.resolve_weapon(new)
                if new == 'ra1_allies_gunboat_cannon' and node.child('Warhead@CannonAP') is not None:
                    from reviewed_weapon_history import restore_endpoint_weapon
                    node = restore_endpoint_weapon(self, node)
                else:
                    node = restore_target_policy_fields(self, node)
                self.assertEqual(digest(node_to_obj(node)),self.before['weapon_hashes'][old])
                self.assertEqual(digest([ordered(c) for c in node.children]),self.before['ordered_hashes'][old])
                self.assertEqual(len(self.rules.inherits_of(self.rules.weapon(new))),3)

    def test_all_diagnostic_classes_are_unchanged(self):
        for old,new in self.mapping.items():
            entry = extract_stats.weapon_entry(self.rules,new)
            if new == 'ra1_allies_gunboat_cannon' and self.rules.resolve_weapon(new).child('Warhead@CannonAP') is not None:
                from reviewed_weapon_history import restore_endpoint_weapon
                restore_endpoint_weapon(self, self.rules.resolve_weapon(new))
                self.assertEqual(entry['design_weapon_class'], 1.0, new)
                self.assertEqual(entry['weapon_class_source'], 'template', new)
                continue
            self.assertEqual(entry['design_weapon_class'],self.before['weapon_classes'][old],new)
            self.assertEqual(entry['weapon_class_source'],'template',new)

    def test_complete_seven_actors_change_only_eighteen_arms_and_one_smoke_reference(self):
        arms = smoke = 0
        for actor,route in self.before['routes'].items():
            reverse = {n:o for o,n in route.items()}
            obj = node_to_obj(self.rules.resolve(actor))
            for key,trait in obj.items():
                if key.split('@')[0]=='Armament' and trait.get('Weapon') in reverse:
                    trait['Weapon'] = reverse[trait['Weapon']]
                    arms += 1
                if key.split('@')[0]=='WithMuzzleSmoke' and trait.get('Weapons') in reverse:
                    self.assertEqual(actor,'ra1_allies_alliedmediumtank')
                    trait['Weapons'] = reverse[trait['Weapons']]
                    smoke += 1
            self.assertEqual(digest(obj),self.before['actor_hashes'][actor],actor)
        self.assertEqual((arms,smoke),(18,1))

    def test_active_roster_has_only_expected_owners_and_no_old_references(self):
        owners = {n:a for a,r in self.before['routes'].items() for n in r.values()}
        old = {n.casefold() for n in self.mapping}
        for actor in self.rules.actors:
            if actor.startswith('^'):continue
            for arm in self.rules.resolve(actor).children_named('Armament'):
                name = arm.get('Weapon')
                self.assertNotIn((name or '').casefold(),old)
                if name in owners:self.assertEqual(actor,owners[name])
        def walk(node):
            if node.key.split('@')[0] in ('Weapon','Weapons','Inherits'):
                self.assertFalse(old & {x.casefold() for x in re.split(r'[\s,]+',node.value)},node.key)
            self.assertNotIn(node.value.casefold(),old,node.key)
            for child in node.children:walk(child)
        for node in list(self.rules.actors.values())+list(self.rules.weapons.values()):walk(node)

    def test_survival_member_order_metadata_and_bytes_are_preserved(self):
        expected = self.before['map']
        old = b'\t\tWeapon: Colt45'
        new = b'\t\tWeapon: ra1_allies_tanya_pistol'
        with zipfile.ZipFile(ROOT/expected['path']) as archive:
            self.assertEqual(archive.comment.hex(),expected['comment_hex'])
            self.assertEqual(archive.namelist(),[m['metadata']['filename'] for m in expected['members']])
            for entry,record in zip(archive.infolist(),expected['members']):
                for key,value in record['metadata'].items():
                    actual = (getattr(entry,key[:-4]).hex() if key.endswith('_hex')
                              else list(entry.date_time) if key=='date_time' else getattr(entry,key))
                    self.assertEqual(actual,value,(entry.filename,key))
                data = archive.read(entry)
                if entry.filename=='rules.yaml':
                    self.assertEqual(data.count(new),1)
                    self.assertNotIn(old,data)
                    data = data.replace(new,old)
                self.assertEqual(hashlib.sha256(data).hexdigest(),record['sha256'],entry.filename)

    def test_no_old_tokens_in_any_bundled_map(self):
        pattern = re.compile(r'(?i)(?<![A-Za-z0-9_])(?:'+'|'.join(re.escape(n) for n in self.mapping)+r')(?![A-Za-z0-9_])')
        for path in (ROOT/'mods/cameo/maps').rglob('*.oramap'):
            with zipfile.ZipFile(path) as archive:
                for entry in archive.infolist():
                    if not entry.filename.lower().endswith(('.yaml','.lua')):continue
                    self.assertLessEqual(entry.file_size,10_000_000)
                    self.assertIsNone(pattern.search(archive.read(entry).decode('utf-8-sig')),
                                      str(path)+':'+entry.filename)
        for path in (ROOT/'mods/cameo/maps').rglob('*'):
            if path.is_file() and path.suffix.lower() in ('.yaml','.lua'):
                self.assertIsNone(pattern.search(path.read_text(encoding='utf-8-sig')),str(path))


if __name__=='__main__':unittest.main()
