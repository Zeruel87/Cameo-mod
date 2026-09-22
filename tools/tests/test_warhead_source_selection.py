import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'reference'))
from warhead_source_selection import selected_sources


class WarheadSourceSelectionTest(unittest.TestCase):
    def test_one_dta_source_retains_base_fields_without_mutating_corpus(self):
        data = {
            'dta_classic': {'rows': [{'warhead': 'WH', 'versus': {'none': 100, 'heavy': 50}}]},
            'dta_enhanced': {'rows': [{'warhead': 'WH', 'versus': {'heavy': 75}}]},
            'dta_globalcode': {'rows': []},
        }
        before = copy.deepcopy(data)
        selected = selected_sources(data)
        self.assertEqual(set(selected), {'dta_enhanced'})
        self.assertEqual(selected['dta_enhanced']['rows'][0]['versus'], {'none': 100, 'heavy': 75})
        self.assertEqual(data, before)

    def test_missing_representative_keeps_available_classic(self):
        data = {'dta_classic': {'rows': []}}
        self.assertEqual(selected_sources(data), data)

    def test_undecoded_override_does_not_inherit_a_usable_old_value(self):
        data = {
            'dta_classic': {'rows': [{'warhead': 'WH', 'versus': {'none': 100}}]},
            'dta_enhanced': {'rows': [{'warhead': 'WH', 'undecoded': ['unknown']}]},
        }
        self.assertNotIn('versus', selected_sources(data)['dta_enhanced']['rows'][0])
