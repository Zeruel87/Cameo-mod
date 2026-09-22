"""Pinned base-OpenRA transport: reviewed population changes, no state certification."""
import collections
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/balance'))
import peer_corpus as pc
import reference_distribution as rd

COHORT = {
    'OpenRA Tiberian Dawn': (48, 25, 77, set()),
    'OpenRA Red Alert': (88, 40, 102, set()),
    'OpenRA Tiberian Sun': (70, 30, 50, {'GACNST', 'GAFSDF', 'GASAND', 'ORCATRAN'}),
    'OpenRA Dune 2000': (50, 27, 63, {'conyard.atreides', 'conyard.harkonnen',
                                   'conyard.ordos', 'fremen', 'nsfremen', 'saboteur'}),
}


class BasePeerCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpora = pc.load(ROOT)
        cls.current = rd.peer_rows() + rd.peer_hero_rows()
        with patch.object(pc, 'load', return_value={k: v for k, v in cls.corpora.items()
                                                  if k not in COHORT}):
            cls.legacy = rd.peer_rows() + rd.peer_hero_rows()

    def test_exact_pinned_population_and_unchanged_inputs(self):
        for source, (count, armed, inputs, _removed) in COHORT.items():
            with self.subTest(source=source):
                meta, rows = self.corpora[source]
                self.assertEqual(len(rows), count)
                self.assertEqual(meta['row_count'], count)
                self.assertEqual(len(meta['inputs']), inputs)
                self.assertTrue(all(x['unchanged'] for x in meta['inputs']))
                self.assertEqual(meta['provenance']['checkout_head'],
                                 'bbd36d9e6a2d7f0d3b24f102858af6dc8caf8a78')
                self.assertFalse(meta['provenance']['checkout_dirty'])
                self.assertEqual(sum(bool(r.get('weapon_evidence')) for r in rows), armed)
                for row in rows:
                    self.assertEqual(row['provenance']['factory_state_certification'], 'none')
                    self.assertEqual(row['provenance']['max_state_certification'], 'none')
                    if row.get('weapon_evidence'):
                        self.assertEqual(row['w_evidence'], 'incomplete')
                        self.assertFalse(row['w_dps_usable'])
                        self.assertIsNone(row['w_dps'])

    def test_only_reviewed_removals_and_identical_retained_chassis(self):
        for source, (_count, _armed, _inputs, removed) in COHORT.items():
            old = {r['id']: r for r in self.legacy if r['source'] == source}
            new = {r['id']: r for r in self.current if r['source'] == source}
            self.assertEqual(old.keys() - new.keys(), removed, source)
            self.assertFalse(new.keys() - old.keys(), source)
            for name, row in new.items():
                for field in ('hp', 'cost', 'speed', 'type'):
                    self.assertEqual(row.get(field), old[name].get(field), (source, name, field))

    def test_other_sources_are_not_duplicated_or_changed(self):
        old = {(r['source'], r['id']): r for r in self.legacy if r['source'] not in COHORT}
        new = {(r['source'], r['id']): r for r in self.current if r['source'] not in COHORT}
        self.assertEqual(new, old)
        keys = [(r['source'], r['id']) for r in self.current if r['source'] in COHORT]
        self.assertEqual(len(keys), len(set(keys)))

    def test_ordinary_and_hero_weapon_votes_are_withheld(self):
        rows = [r for r in self.current if r['source'] in COHORT]
        self.assertEqual(len(rows), 256)
        self.assertEqual(collections.Counter(r['w_evidence'] for r in rows),
                         {'incomplete': 122, 'legacy-unassessed': 134})
        for row in rows:
            self.assertIsNone(row.get('w_dps'))
            for ladder in rd.LADDERS:
                self.assertIsNone(row.get(f'dps_vs_{ladder}'))


if __name__ == '__main__':
    unittest.main()
