import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference'))
from openra_warhead_platforms import trace_export


class Traces(unittest.TestCase):
    def run_export(self, records):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'export.jsonl'
            path.write_text('\n'.join(json.dumps(row) for row in records))
            return trace_export(path, 'fixture')

    def test_channels_and_zero_preserved_without_inventing_default_armors(self):
        meta = {'record': 'meta', 'inputs': [{'unchanged': True}]}
        actor = {'id': 'TANK', 'weapon_evidence': [{'weapon_resolved': True, 'weapon': 'Gun',
                  'requires_condition': 'upgrade', 'warheads': [
                      {'key': 'Warhead@1', 'versus': {'None': '0', 'Heavy': '100'}},
                      {'key': 'Warhead@2', 'versus': {'Heavy': 'NaN'}},
                      {'key': 'Warhead@3', 'damage': '100', 'versus': {}}]}]}
        result = self.run_export([meta, actor])
        self.assertEqual(result['rows'][0]['declared_versus'], {'None': 0, 'Heavy': 100})
        self.assertEqual(result['rows'][0]['requires_condition'], 'upgrade')
        self.assertIsNone(result['rows'][1]['declared_versus'])
        self.assertTrue(result['rows'][1]['errors'])
        self.assertEqual(result['rows'][2]['declared_versus'], {})
        self.assertIn('default requires interpretation', result['rows'][2]['armor_scope'])

    def test_unstable_inputs_and_duplicate_actors_rejected(self):
        with self.assertRaises(ValueError):
            self.run_export([{'record': 'meta', 'inputs': [{'unchanged': False}]}])
        with self.assertRaises(ValueError):
            self.run_export([{'record': 'meta', 'inputs': [{'unchanged': True}]},
                             {'id': 'TANK'}, {'id': 'TANK'}])
