"""Synthetic positive/negative cases for bounded map weapon-name scans."""
import pathlib
import tempfile
import types
import unittest
from unittest import mock
import zipfile

from weapon_name_map_checks import assert_no_old_weapon_names, assert_owned_weapon_consumers


class WeaponNameMapCheckTests(unittest.TestCase):
    def test_owner_scan_rejects_old_abstract_values_and_foreign_consumers(self):
        def node(key, value='', children=()):
            return types.SimpleNamespace(key=key, value=value, children=children,
                                         get=lambda field: value if field == 'Weapon' else None)
        routes = {'owner': {'OldWeapon': 'NewWeapon'}}
        good = node('owner', children=[node('Armament', 'NewWeapon')])
        rules = types.SimpleNamespace(actors={'owner': good}, weapons={},
                                      resolve=lambda actor: rules.actors[actor])
        assert_owned_weapon_consumers(self, rules, routes)
        rules.actors['intruder'] = good
        with self.assertRaises(AssertionError):
            assert_owned_weapon_consumers(self, rules, routes)
        del rules.actors['intruder']
        rules.actors['^Abstract'] = node('^Abstract', children=[node('Weapon', 'oldweapon')])
        with self.assertRaises(AssertionError):
            assert_owned_weapon_consumers(self, rules, routes)
        with self.assertRaises(AssertionError):
            assert_owned_weapon_consumers(self, rules, {})

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.maps = self.root / 'mods/cameo/maps'
        self.maps.mkdir(parents=True)
        self.archive = self.maps / 'sample.oramap'
        self.write_archive('rules.yaml', 'Weapon: OtherWeapon\n')

    def write_archive(self, member, text):
        with zipfile.ZipFile(self.archive, 'w') as archive:
            archive.writestr(member, text)

    def test_similar_names_are_not_exact_weapon_tokens(self):
        self.write_archive('rules.yaml', 'Weapon: OldWeaponSuffix\n')
        assert_no_old_weapon_names(self, self.root, ['OldWeapon'])

    def test_archived_yaml_and_lua_references_are_rejected(self):
        for member in ('rules.yaml', 'script.lua'):
            with self.subTest(member=member):
                self.write_archive(member, 'Weapon: OldWeapon\n')
                with self.assertRaises(AssertionError):
                    assert_no_old_weapon_names(self, self.root, ['OldWeapon'])

    def test_loose_references_are_rejected(self):
        (self.maps / 'rules.yaml').write_text('Weapon: OldWeapon\n', encoding='utf-8')
        with self.assertRaises(AssertionError):
            assert_no_old_weapon_names(self, self.root, ['OldWeapon'])

    def test_oversize_members_fail_before_decompression(self):
        entry = types.SimpleNamespace(filename='rules.yaml', file_size=10_000_001)
        with mock.patch('weapon_name_map_checks.zipfile.ZipFile') as factory:
            archive = factory.return_value.__enter__.return_value
            archive.infolist.return_value = [entry]
            with self.assertRaises(AssertionError):
                assert_no_old_weapon_names(self, self.root, ['OldWeapon'])
            archive.read.assert_not_called()

    def test_empty_inventory_and_missing_archives_fail_closed(self):
        with self.assertRaises(AssertionError):
            assert_no_old_weapon_names(self, self.root, [])
        self.archive.unlink()
        with self.assertRaises(AssertionError):
            assert_no_old_weapon_names(self, self.root, ['OldWeapon'])


if __name__ == '__main__':
    unittest.main()
