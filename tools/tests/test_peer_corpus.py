"""Bounded structured source validation and replacement regression tests."""
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
import peer_corpus as pc
import reference_distribution as rd
import synthesize_reference as syn


def fixture():
    digest = hashlib.sha256(b'mods/ca/mod.yaml\t' + b'a' * 64 + b'\n').hexdigest()
    local = hashlib.sha256(b'tools/extractor.py\t' + b'b' * 64 + b'\n').hexdigest()
    prov = {key: None for key in pc.ROW_PROVENANCE}
    prov.update(source_label='Combined Arms', mod_id='ca', checkout_head='c' * 40,
                checkout_head_status='ok', expect_commit='c' * 40,
                checkout_dirty=False, checkout_dirty_entries=0,
                inputs_digest=digest, local_dependencies_digest=local,
                source_runtime_applicability='unverified', factory_state_certification='none',
                max_state_certification='none', mode='explicit_root',
                extractor='tools/reference/extract_peer_units.py', engine_pin='test')
    meta = {'record': 'meta', 'schema': 1, 'row_count': 1,
            'rifle': {'id': 'E1', 'hp': 100, 'cost': 50},
            'inputs': [{'path': 'mods/ca/mod.yaml', 'sha256_before': 'a' * 64,
                        'sha256_after': 'a' * 64, 'unchanged': True}],
            'provenance': {**prov, 'input_count': 1, 'local_dependencies': [
                {'path': 'tools/extractor.py', 'sha256': 'b' * 64}]}}
    row = {'record': 'unit', 'id': 'E1', 'name': 'Rifle', 'type': 'infantry',
           'hp': 100, 'cost': 50, 'speed': 20, 'turn_speed': None, 'limit': None,
           'faction': 'gdi', 'w_damage': 10, 'w_dps': None, 'w_dps_raw': 2,
           'w_evidence': 'incomplete', 'w_evidence_reason': 'conditional_armament',
           'w_dps_usable': False, 'weapon_evidence': [{'slot': 'Armament', 'weapon': 'Rifle'}],
           'provenance': prov}
    return meta, row


class CorpusTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.folder = self.root / pc.INDEX.parent
        self.folder.mkdir(parents=True)
        self.meta, self.row = fixture()

    def install(self, records=None, *, text=None):
        if text is None:
            text = '\n'.join(json.dumps(x) for x in (records or [self.meta, self.row])) + '\n'
        data = text.encode()
        path = self.folder / 'ca.jsonl'
        path.write_bytes(data)
        selection = {'source': 'Combined Arms', 'mod_id': 'ca', 'file': path.name,
                     'sha256': hashlib.sha256(data).hexdigest()}
        (self.root / pc.INDEX).write_text(json.dumps({'schema': 1, 'sources': [selection]}))
        return path, selection

    def test_roundtrip_preserves_nested_evidence(self):
        self.install()
        meta, rows = pc.load(self.root)['Combined Arms']
        self.assertEqual(rows[0], self.row)
        self.assertEqual(meta, self.meta)

    def test_absent_index_is_legacy_but_unlisted_file_is_inert(self):
        (self.folder / 'unlisted.jsonl').write_text('not json')
        self.assertEqual(pc.load(self.root), {})
        self.assertEqual(pc.input_paths(self.root), [])

    def test_wrong_payload_hash_refuses(self):
        path, _ = self.install()
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            pc.load(self.root)

    def test_missing_selected_file_does_not_fall_back(self):
        path, _ = self.install()
        path.unlink()
        with self.assertRaises(OSError):
            pc.load(self.root)

    def test_duplicate_case_insensitive_actor_refuses(self):
        self.meta['row_count'] = 2
        self.install([self.meta, self.row, {**self.row, 'id': 'e1'}])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            pc.load(self.root)

    def test_metadata_or_row_count_or_schema_refuses(self):
        for field, value in [('row_count', 2), ('schema', 99), ('schema', True), ('record', 'unit')]:
            with self.subTest(field=field, value=value):
                self.meta, self.row = fixture()
                self.meta[field] = value
                self.install()
                with self.assertRaises(ValueError):
                    pc.load(self.root)

    def test_nonfinite_and_duplicate_json_fields_refuse(self):
        for text in ('{"record":"meta","schema":1,"schema":1}',
                     '{"number":NaN}', '{"number":1e999}'):
            self.install(text=text)
            with self.assertRaises(ValueError):
                pc.load(self.root)

    def test_row_provenance_cannot_disagree(self):
        self.row['provenance']['checkout_head'] = 'd' * 40
        self.install()
        with self.assertRaisesRegex(ValueError, 'row provenance'):
            pc.load(self.root)

    def test_digest_and_source_identity_are_checked(self):
        for key, value in [('inputs_digest', '0' * 64), ('local_dependencies_digest', '0' * 64),
                           ('source_label', 'Other'), ('mod_id', 'wrong'), ('checkout_dirty', True)]:
            with self.subTest(key=key):
                self.meta, self.row = fixture()
                self.meta['provenance'][key] = value
                self.install()
                with self.assertRaises(ValueError):
                    pc.load(self.root)

    def test_changed_or_escaping_source_input_refuses(self):
        for key, value in [('unchanged', False), ('path', '../secret'), ('path', 'C:/secret')]:
            self.meta, self.row = fixture()
            self.meta['inputs'][0][key] = value
            self.install()
            with self.assertRaises(ValueError):
                pc.load(self.root)

    def test_input_paths_include_only_selected_payload_and_index(self):
        path, _ = self.install()
        (self.folder / 'other.jsonl').write_text('inert')
        self.assertEqual(pc.input_paths(self.root), [(self.root / pc.INDEX).resolve(), path.resolve()])

    def test_source_replaces_stale_ordinary_and_hero_rows(self):
        hero = copy.deepcopy(self.row)
        hero.update(id='HERO', limit=1)
        self.meta['row_count'] = 2
        self.install([self.meta, self.row, hero])
        doc = self.root / 'docs/design/ORIGINAL_UNITS_PEER_OPENRA.md'
        doc.parent.mkdir(parents=True)
        doc.write_text('## Combined Arms\n| id | unit | type | hp | cost | limit |\n'
                       '| OLD | Stale | infantry | 999 | 999 | |\n'
                       '| OLDHERO | Stale hero | infantry | 999 | 999 | 1 |\n'
                       '## Other source\n| id | unit | type | hp | cost | limit |\n'
                       '| OTHER | Other rifle | infantry | 120 | 60 | |\n')
        with patch.multiple(rd, ROOT=self.root, INI_CORPUS=self.root / 'absent'), \
                patch.object(rd, 'doc1_rows', return_value=[]):
            ordinary = rd.peer_rows()
            heroes = rd.peer_hero_rows()
        self.assertEqual([x['id'] for x in ordinary], ['E1', 'OTHER'])
        self.assertEqual([x['id'] for x in heroes], ['HERO'])
        self.assertIsNone(ordinary[0]['w_dps'])
        self.assertEqual(ordinary[0]['w_dps_raw'], 2)
        self.assertEqual(ordinary[0]['weapon_evidence'], self.row['weapon_evidence'])
        with patch.multiple(syn, ROOT=self.root, DOC5=doc):
            chassis = syn.parse_doc5()
        self.assertEqual(len(chassis), 2)
        self.assertEqual(chassis[0]['x_hp'], 1)

    def test_lineage_filter_applies_to_structured_rows(self):
        self.install()
        with patch.object(rd, 'LINEAGE_MEMBERS', {'Combined Arms'}):
            self.assertEqual(rd.structured_peer_rows(pc.load(self.root)), [])

    def test_required_chassis_and_weapon_numbers_refuse_before_consumption(self):
        for field, value in [('hp', None), ('hp', 0), ('hp', True),
                             ('type', None), ('name', ''), ('w_damage', '10'),
                             ('w_range', True), ('eff_vs_light', '0.5')]:
            with self.subTest(field=field, value=value):
                self.meta, self.row = fixture()
                self.row[field] = value
                self.install()
                with patch.object(rd, 'ROOT', self.root):
                    for consumer in (rd.peer_rows, rd.peer_hero_rows):
                        with self.assertRaises(ValueError):
                            consumer()

    def test_misspelled_selection_does_not_create_an_extra_source(self):
        self.install()
        index = self.root / pc.INDEX
        doc = json.loads(index.read_text())
        doc['sources'][0]['source'] = 'Combined Arm'
        index.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, 'source/mod pair'):
            pc.load(self.root)

    def test_ai_only_structured_rows_are_filtered(self):
        ai = copy.deepcopy(self.row)
        ai['id'] = 'E1_AI'
        self.meta['row_count'] = 2
        self.install([self.meta, self.row, ai])
        doc = self.root / 'docs/design/ORIGINAL_UNITS_PEER_OPENRA.md'
        doc.parent.mkdir(parents=True)
        doc.write_text('')
        with patch.multiple(rd, ROOT=self.root, INI_CORPUS=self.root / 'absent'), \
                patch.object(rd, 'doc1_rows', return_value=[]):
            self.assertEqual([r['id'] for r in rd.peer_rows()], ['E1'])


class InstalledCorpusTests(unittest.TestCase):
    def test_pinned_ca_population_and_incomplete_weapon_gate(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        meta, rows = pc.load(root)['Combined Arms']
        self.assertEqual(meta['row_count'], 377)
        self.assertEqual(sum(r.get('w_evidence') == 'incomplete' for r in rows), 288)
        self.assertEqual(sum(bool(r['production_state_evidence']['declared_routes']) for r in rows), 57)
        states = {r['id']: r['production_state_evidence'] for r in rows}
        self.assertEqual(len(states['HMMV']['declared_routes']), 2)
        self.assertEqual(states['HMMV.TOW']['declared_routes'], [])
        self.assertEqual({name for name, state in states.items() if 'initial_state_review' in state},
                         {'HARV', 'LST', 'HMMV', 'HMMV.TOW'})
        harv = states['HARV']['initial_state_review']
        self.assertEqual(harv['status'], 'unverified')
        self.assertTrue(harv['condition_uses'])
        self.assertTrue(harv['prerequisite_uses'])
        self.assertIn('DamageMultiplier@TIBSTEALTH',
                      [x['key'] for x in harv['modifier_traits']])
        self.assertTrue(all(r['factory_ready_certification'] == 'none' and
                            r['maximum_upgrade_certification'] == 'none'
                            for r in states.values()))
        disabled = {'AFAC', 'FACT', 'SFAC', 'TRUK', 'TRUK.DROP'}
        self.assertFalse(disabled & {r['id'] for r in rows})
        self.assertEqual(sum(r['source'] == 'Combined Arms' for r in rd.peer_rows()), 341)
        self.assertEqual(sum(r['source'] == 'Combined Arms' for r in rd.peer_hero_rows()), 25)
        sys.path.insert(0, str(root / 'tools/reference'))
        import peer_cost_grid
        cost_rows = [r for r in peer_cost_grid.parse() if r['mod'] == 'Combined Arms']
        self.assertEqual(len(cost_rows), 377)
        self.assertTrue(all(r['dps'] is None for r in cost_rows))


if __name__ == '__main__':
    unittest.main()
