"""Aliases improve diagnostic visibility; they cannot waive raw gates or drift."""
import contextlib
import io
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
import ownership_lineage as lineage
import audit_release_drift as release
import audit_missile_role_family as missile
from miniyaml import Node, Ruleset


class ReleaseLineageTests(unittest.TestCase):
    def test_rename_drift_stays_visible_and_only_exact_accepted_value_is_excluded(self):
        base = {'old': {'flat': 100, 'mains': 2}, 'other': {'flat': 10, 'mains': 1}}
        now = {'new': {'flat': 400, 'mains': 1}}
        view = lineage.release_view(base, now, {'old': {'accepted': 300}}, {'old': 'new'})
        self.assertEqual(view['counts'], {'matched': 1, 'unmatched': 1, 'inflated': 1,
                                         'weakened': 0, 'extreme': 1, 'accepted': 0})
        self.assertEqual(view['drift'][0]['current_name'], 'new')
        exact = lineage.release_view(base, now, {'old': {'accepted': 400}}, {'old': 'new'})
        self.assertEqual(exact['counts']['accepted'], 1)
        self.assertEqual(exact['counts']['inflated'], 0)
        self.assertEqual(exact['recovered'][0]['status'], 'accepted exact value')

    def test_unproven_similarity_and_missing_targets_stay_unmatched(self):
        base = {'old': {'flat': 100, 'mains': 1}}
        now = {'similar': {'flat': 100, 'mains': 1}}
        for mapping in ({}, {'old': 'missing'}):
            view = lineage.release_view(base, now, {}, mapping)
            self.assertEqual(view['counts']['unmatched'], 1)
            self.assertEqual(view['recovered'], [])

    def test_cycles_collisions_and_live_old_alias_are_refused(self):
        for mapping in ({'old': 'old'}, {'old': 'new', 'new': 'old'},
                        {'a': 'target', 'b': 'target'}):
            with self.assertRaises(ValueError):
                lineage.release_view({}, {}, {}, mapping)
        with self.assertRaisesRegex(ValueError, 'live old identity'):
            lineage.release_view({'old': {'flat': 1, 'mains': 1}},
                                 {'old': {'flat': 1, 'mains': 1}}, {}, {'old': 'new'})

    def test_weakened_chained_identity_is_not_lost(self):
        view = lineage.release_view({'old': {'flat': 100, 'mains': 2}},
                                    {'last': {'flat': 25, 'mains': 1}}, {},
                                    {'old': 'middle', 'middle': 'last'})
        self.assertEqual(view['counts']['weakened'], 1)
        self.assertEqual(view['counts']['extreme'], 1)
        self.assertEqual(view['recovered'][0]['current_name'], 'last')

    def test_published_route_provenance_is_pinned_and_missing_evidence_fails(self):
        mapping = lineage.load_renames(ROOT)
        self.assertEqual(len(mapping), 194)
        self.assertEqual(mapping['BHRedDarts'], 'td_nod_stealthsoldier_bhreddarts')
        with patch.dict(lineage.ROUTE_HASHES, {'closed_remaining_names_20260910.json': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'unreviewed rename evidence'):
                lineage.load_renames(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(OSError):
                lineage.load_renames(pathlib.Path(directory))

    def test_supplemental_recovery_cannot_turn_raw_failure_green(self):
        old = {'old': {'flat': 100, 'mains': 1}}
        now = {'new': {'flat': 100, 'mains': 1}}
        with patch.object(release, 'load_baseline', return_value=({'_release_tag': 'fixture',
                '_release_commit': 'fixture', '_weapons': 1}, old)), \
                patch.object(release, 'snapshot', return_value=now), \
                patch.object(release, 'load_accepted', return_value={}), \
                patch.object(release, 'load_renames', return_value={'old': 'new'}), \
                patch.object(release, 'D4_BASELINE', 0), patch.object(sys, 'argv', ['audit']), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(release.main(), 1)
        self.assertIn('Recovered **1**', output.getvalue())
        self.assertIn('FAIL: D4 above ratchet', output.getvalue())


class MissileEquivalenceTests(unittest.TestCase):
    def rules(self, changed=False, reorder=False, same_unlisted=False):
        name = 'td_gdi_mlrs_227mm'
        raw = Node(name, '', [Node('Inherits', '227mm')])
        if changed:
            raw.children.append(Node('Range', '1'))
        children = [Node('ValidTargets', 'Ground, Air'), Node('Warhead@MissileHE_Light', 'AreaDamage', [Node('Damage', '100')]),
                    Node('Warhead@Effect', 'CreateEffect')]
        parent = Node('227mm', '', children)
        resolved = parent.deep_copy()
        resolved.key = name
        if reorder:
            resolved.children.reverse()
        nodes = {'227mm': parent, name: resolved}
        raw_nodes = {'227mm': parent, name: raw}
        if same_unlisted:
            nodes['unlisted'] = parent.deep_copy()
            raw_nodes['unlisted'] = Node('unlisted', '', [Node('Inherits', '227mm')])
        return SimpleNamespace(weapons=raw_nodes, resolve_weapon=nodes.__getitem__)

    def findings(self, extra=False):
        rows = [('227mm', 'both', 'MissileHE'), ('td_gdi_mlrs_227mm', 'both', 'MissileHE')]
        if extra:
            rows.append(('unlisted', 'both', 'MissileHE'))
        return {'R3': list(rows), 'R4': list(rows)}

    def test_only_exact_reviewed_wrappers_group_and_raw_input_survives(self):
        findings = self.findings(True)
        view = lineage.missile_view(self.rules(same_unlisted=True), findings)
        self.assertEqual(view['counts']['R3'], 2)
        self.assertEqual(view['counts']['R4'], 2)
        self.assertEqual(len(findings['R3']), 3)
        self.assertEqual(view['duplicates'][0]['members'], ['227mm', 'td_gdi_mlrs_227mm'])

    def test_override_or_reordered_payload_is_counted_independently(self):
        for rules in (self.rules(changed=True), self.rules(reorder=True)):
            view = lineage.missile_view(rules, self.findings())
            self.assertEqual(view['counts']['R3'], 2)
            self.assertEqual(view['nontransparent_reviewed_wrappers'], ['td_gdi_mlrs_227mm'])

    def test_raw_gate_remains_red_when_equivalence_group_is_within_old_count(self):
        with patch.object(missile.miniyaml, 'Ruleset', return_value=self.rules()), \
                patch.object(missile, 'R3_BASELINE', 1), patch.object(missile, 'R4_BASELINE', 1), \
                patch.object(sys, 'argv', ['audit']), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(missile.main(), 1)
        self.assertIn('| R3 | 2 | 1 |', output.getvalue())
        self.assertIn('FAIL: R3, R4 above ratchet', output.getvalue())


if __name__ == '__main__':
    unittest.main()
