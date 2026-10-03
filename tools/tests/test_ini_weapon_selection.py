import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/balance'))
import ini_weapon_selection as selection
import reference_distribution as rd


class ReviewedSelectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = selection.load(ROOT)
        cls.records = {(r['source'], r['id']): r for r in
                       map(json.loads, (ROOT / 'docs/reference/ini_corpus.json').read_text().splitlines())}

    def test_reviewed_tank_votes_and_original_slots_survive(self):
        raw = self.records['DTA Enhanced', 'MTNK']
        before = copy.deepcopy(raw)
        selected = selection.select(raw, self.profile)
        self.assertEqual(raw, before)
        self.assertEqual(selected['weapon'], '90mm')
        self.assertEqual(selected['wdummy_weapon'], '90mmDummy')
        self.assertEqual(selected['wdummy_damage'], 0)
        self.assertEqual(selected['w2_damage'], 30)
        row = next(r for r in rd.ini_rows() if (r['source'], r['id']) == ('DTA Enhanced', 'MTNK'))
        self.assertEqual(row['w_dps'], 30 / 51)
        self.assertEqual(row['pre_cycle_evidence']['w_dps'], 0.6)
        self.assertEqual(row['w_range'], 5.7)
        self.assertTrue(rd.eligible(row, 'w_range'))
        self.assertTrue(rd.eligible(row, 'w_dps'))
        self.assertTrue(all(row['dps_vs_' + ladder] is None for ladder in rd.LADDERS))

    def test_changed_record_is_refused(self):
        raw = copy.deepcopy(self.records['DTA Enhanced', 'MTNK'])
        raw['w2_damage'] = 300
        with self.assertRaises(ValueError):
            selection.select(raw, self.profile)

    def test_railgun_and_unreviewed_dummy_are_not_promoted(self):
        for actor in ('XO', 'AIMTNK'):
            raw = self.records['DTA Enhanced', actor]
            self.assertIs(selection.select(raw, self.profile), raw)
        raw = self.records['DTA Enhanced', 'XO']
        row = dict(raw)
        rd.apply_weapon_evidence(row, raw)
        self.assertIsNone(row.get('w_dps'))


if __name__ == '__main__':
    unittest.main()
