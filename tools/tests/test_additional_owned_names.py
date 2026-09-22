"""Identity-only names preserve mixed profiles, unknown classes and all owners."""
import hashlib
import json
import pathlib
import re
import sys
import unittest
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools/audit'),str(ROOT/'tools/balance')]
from miniyaml import Ruleset
from dump_resolved import node_to_obj
import extract_stats
from reviewed_weapon_history import OwnedCheckpointView, restore_owned_checkpoint_actor


def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ordered(n):return [n.key,n.value,[ordered(c) for c in n.children]]


class AdditionalOwnedNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=json.loads((ROOT/'tools/tests/fixtures/additional_owned_names_20260910.json').read_text(encoding='utf-8'))
        cls.rules=Ruleset(ROOT)
        cls.mapping={o:n for r in cls.before['routes'].values() for o,n in r.items()}

    def test_eleven_full_ordered_payloads_and_aa_suffixes_preserved(self):
        history = OwnedCheckpointView(self, self.rules, 'additional')
        self.assertEqual(len(self.mapping),11)
        self.assertEqual(len(set(self.mapping.values())),11)
        for old,new in self.mapping.items():
            with self.subTest(weapon=new):
                self.assertNotIn(old,self.rules.weapons)
                node=history.resolve_weapon(new)
                self.assertEqual(digest(node_to_obj(node)),self.before['weapon_hashes'][old])
                self.assertEqual(digest([ordered(c) for c in node.children]),self.before['ordered_hashes'][old])
                if old.endswith('_AA') or old=='Nike':self.assertTrue(new.endswith('_AA'))

    def test_original_class_values_and_unknowns_are_preserved(self):
        for old,new in self.mapping.items():
            entry=extract_stats.weapon_entry(self.rules,new)
            self.assertEqual({k:entry[k] for k in self.before['class_contracts'][old]},
                             self.before['class_contracts'][old],new)

    def test_five_complete_actors_only_change_twelve_armament_identities(self):
        count=0
        for actor,route in self.before['routes'].items():
            reverse={n:o for o,n in route.items()}
            obj=restore_owned_checkpoint_actor(self,self.rules,'additional',actor)
            for key,trait in obj.items():
                if key.split('@')[0]=='Armament' and trait.get('Weapon') in reverse:
                    trait['Weapon']=reverse[trait['Weapon']]
                    count+=1
            self.assertEqual(digest(obj),self.before['actor_hashes'][actor],actor)
        self.assertEqual(count,12)

    def _reverse_later_sheridan_names(self, actor, obj):
        if actor != 'ra1_allies_sheridanassaulttank':
            return
        for slot, old, new in (
                ('Armament@MG', 'SheridanVulcan', 'ra1_allies_sheridanassaulttank_chaingun'),
                ('Armament@MGCryo', 'SheridanVulcanCryo', 'ra1_allies_sheridanassaulttank_chaingun_cryo')):
            self.assertEqual(obj[slot]['Weapon'], new)
            obj[slot]['Weapon'] = old

    def test_later_sheridan_identity_adapter_is_slot_exact(self):
        actor = 'ra1_allies_sheridanassaulttank'
        normal, cryo = actor + '_chaingun', actor + '_chaingun_cryo'
        obj = {'Armament@MG': {'Weapon': normal}, 'Armament@MGCryo': {'Weapon': cryo}}
        self._reverse_later_sheridan_names('other_actor', obj)
        self.assertEqual(obj['Armament@MG']['Weapon'], normal)
        self.assertEqual(obj['Armament@MGCryo']['Weapon'], cryo)
        for wrong in ('SheridanVulcan', cryo, 'OtherWeapon'):
            bad = {'Armament@MG': {'Weapon': wrong}, 'Armament@MGCryo': {'Weapon': cryo}}
            with self.assertRaises(AssertionError):
                self._reverse_later_sheridan_names(actor, bad)
        with self.assertRaises(KeyError):
            self._reverse_later_sheridan_names(actor, {'Armament@OTHER': {'Weapon': normal}})
        self._reverse_later_sheridan_names(actor, obj)
        self.assertEqual(obj['Armament@MG']['Weapon'], 'SheridanVulcan')
        self.assertEqual(obj['Armament@MGCryo']['Weapon'], 'SheridanVulcanCryo')

    def test_no_other_owners_or_old_active_references(self):
        owners={n:a for a,r in self.before['routes'].items() for n in r.values()}
        old={n.casefold() for n in self.mapping}
        for actor in self.rules.actors:
            if actor.startswith('^'):continue
            for arm in self.rules.resolve(actor).children_named('Armament'):
                name=arm.get('Weapon')
                self.assertNotIn((name or '').casefold(),old)
                if name in owners:self.assertEqual(actor,owners[name])
        def walk(node):
            self.assertFalse(old & {v.casefold() for v in re.split(r'[\s,]+',node.value)},node.key)
            for c in node.children:walk(c)
        for node in list(self.rules.actors.values())+list(self.rules.weapons.values()):walk(node)

    def test_no_old_names_in_bundled_maps(self):
        pattern=re.compile(r'(?i)(?<![A-Za-z0-9_])(?:'+'|'.join(re.escape(n) for n in self.mapping)+r')(?![A-Za-z0-9_])')
        maps=list((ROOT/'mods/cameo/maps').rglob('*.oramap'))
        self.assertTrue(maps)
        for path in maps:
            with zipfile.ZipFile(path) as archive:
                for entry in archive.infolist():
                    if not entry.filename.lower().endswith(('.yaml','.lua')):continue
                    self.assertLessEqual(entry.file_size,10_000_000)
                    self.assertIsNone(pattern.search(archive.read(entry).decode('utf-8-sig')),str(path))
        for path in (ROOT/'mods/cameo/maps').rglob('*'):
            if path.is_file() and path.suffix.lower() in ('.yaml','.lua'):
                self.assertIsNone(pattern.search(path.read_text(encoding='utf-8-sig')),str(path))


if __name__=='__main__':unittest.main()
