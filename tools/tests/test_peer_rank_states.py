"""Rank projections preserve count semantics and refuse unsupported activation."""
import pathlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/reference'))
sys.path.insert(0, str(ROOT / 'tools/tests'))
import extract_peer_rank_states as rank
from test_peer_weapon_evidence import build


ACTOR = '''UNIT:
    GainsExperience:
        Conditions:
            200: rank
            400: rank
    GrantCondition@VETERAN:
        RequiresCondition: rank == 1
        Condition: veteran
    GrantCondition@ELITE:
        RequiresCondition: rank >= 2
        Condition: elite
    FirepowerMultiplier@VETERAN:
        RequiresCondition: veteran
        Modifier: 110
    FirepowerMultiplier@ELITE:
        RequiresCondition: elite
        Modifier: 130
    ReloadDelayMultiplier@ELITE:
        RequiresCondition: elite
        Modifier: 75
'''


class RankStateTests(unittest.TestCase):
    def project(self, text=ACTOR):
        with tempfile.TemporaryDirectory() as folder:
            rules = build(pathlib.Path(folder), text, '')
            return rank.project(rules.resolve('UNIT'))

    def test_condition_grammar_does_not_default_unknowns(self):
        for expression in ('missing', 'missing == 0', '!missing', 'rank || missing',
                           'rank >= 2 trailing', '__import__("os")'):
            self.assertIsNone(rank.condition_value(expression, {'rank': 2}))
        self.assertTrue(rank.condition_value('rank >= 2', {'rank': 2}))
        self.assertFalse(rank.condition_value('rank == 1', {'rank': 2}))
        self.assertFalse(rank.condition_value('rank', {'rank': 0}))
        self.assertTrue(rank.condition_value(None, {}))
        self.assertTrue(rank.condition_value('!rank', {'rank': 0}))
        self.assertFalse(rank.condition_value('!rank', {'rank': 2}))
        self.assertIsNone(rank.condition_value('!rank >= 2', {'rank': 2}))

    def test_mutually_exclusive_veteran_and_elite_are_not_summed(self):
        result = self.project()
        self.assertEqual(result['status'], 'rank_axis_evaluated')
        base, maximum = result['states']
        self.assertEqual(base['condition_counts'], {'rank': 0, 'veteran': 0, 'elite': 0})
        self.assertEqual(maximum['condition_counts'], {'rank': 2, 'veteran': 0, 'elite': 1})
        self.assertEqual([x['effective_modifier'] for x in base['weapon_modifiers']], [100, 100, 100])
        self.assertEqual([x['effective_modifier'] for x in maximum['weapon_modifiers']], [100, 130, 75])
        self.assertEqual(result['factory_state_certification'], 'none')
        self.assertEqual(result['max_state_certification'], 'none')

    def test_production_level_needs_player_scenario(self):
        result = self.project(ACTOR + '    ProducibleWithLevel:\n        Prerequisites: upgrade\n')
        self.assertEqual(result['status'], 'scenario_required')
        self.assertEqual(result['states'], [])

    def test_permanent_grants_require_history(self):
        result = self.project(ACTOR.replace('Condition: veteran', 'Condition: veteran\n        GrantPermanently: true'))
        self.assertEqual(result['status'], 'history_dependent_rank_grant')

    def test_external_rank_provider_refuses(self):
        result = self.project(ACTOR + '    ExternalCondition:\n        Condition: rank\n')
        self.assertEqual(result['status'], 'ambiguous_rank_provider')

    def test_duplicate_grant_target_refuses(self):
        result = self.project(ACTOR.replace('Condition: elite', 'Condition: veteran'))
        self.assertEqual(result['status'], 'ambiguous_rank_provider')

    def test_unknown_non_rank_modifier_stays_unknown(self):
        result = self.project(ACTOR + '    FirepowerMultiplier@UPGRADE:\n        RequiresCondition: purchased\n        Modifier: 150\n')
        for state in result['states']:
            modifier = state['weapon_modifiers'][-1]
            self.assertIsNone(modifier['enabled'])
            self.assertIsNone(modifier['effective_modifier'])

    def test_unconditional_activation_is_known_without_guessing_other_conditions(self):
        result = self.project(ACTOR + '''    Armament:
        Weapon: Rifle
    Armament@GATED:
        Weapon: Rocket
        PauseOnCondition: ammo-empty
''')
        plain, gated = result['scenario_independent_activation']
        self.assertTrue(plain['activation_gate_open'])
        self.assertIsNone(gated['activation_gate_open'])
        self.assertIsNone(gated['paused'])

    def test_rank_activation_and_range_stay_separate_between_views(self):
        result = self.project(ACTOR + '''    Armament:
        Weapon: Rifle
        PauseOnCondition: elite
    RangeMultiplier:
        RequiresCondition: elite
        Modifier: 125
''')
        base, maximum = result['states']
        self.assertTrue(base['armament_activation'][0]['activation_gate_open'])
        self.assertFalse(maximum['armament_activation'][0]['activation_gate_open'])
        self.assertEqual(base['weapon_modifiers'][-1]['effective_modifier'], 100)
        self.assertEqual(maximum['weapon_modifiers'][-1]['effective_modifier'], 125)

    def test_known_disabled_gate_dominates_unknown_pause(self):
        result = self.project(ACTOR + '''    Armament:
        Weapon: Rifle
        RequiresCondition: elite
        PauseOnCondition: unknown
''')
        self.assertFalse(result['states'][0]['armament_activation'][0]['activation_gate_open'])
        self.assertIsNone(result['states'][1]['armament_activation'][0]['activation_gate_open'])

    def test_initial_ammo_is_full_by_default_but_not_at_maximum_rank(self):
        result = self.project(ACTOR + '''    AmmoPool:
        Ammo: 3
        AmmoCondition: ammo
    Armament:
        Weapon: Rocket
        PauseOnCondition: !ammo
''')
        self.assertEqual(result['creation_ammo_evidence']['condition_counts'], {'ammo': 3})
        self.assertTrue(result['creation_armament_activation'][0]['activation_gate_open'])
        self.assertTrue(result['states'][0]['armament_activation'][0]['activation_gate_open'])
        self.assertIsNone(result['states'][1]['armament_activation'][0]['activation_gate_open'])

    def test_initial_ammo_zero_and_over_maximum_follow_source_defaults(self):
        for declared, expected in (('0', 0), ('1', 1), ('9', 3), ('-2', 3)):
            result = self.project(ACTOR + f'    AmmoPool:\n        Ammo: 3\n        InitialAmmo: {declared}\n        AmmoCondition: ammo\n')
            self.assertEqual(result['creation_ammo_evidence']['condition_counts'], {'ammo': expected})

    def test_unknown_or_conflicting_ammo_provider_does_not_guess(self):
        for extra in ('        Ammo: bad\n', '    ExternalCondition:\n        Condition: ammo\n'):
            result = self.project(ACTOR + '    AmmoPool:\n        AmmoCondition: ammo\n' + extra)
            self.assertEqual(result['creation_ammo_evidence']['condition_counts'], {})
            self.assertTrue(result['creation_ammo_evidence']['holds'])

    def test_no_rank_is_not_a_factory_certification(self):
        result = self.project('UNIT:\n    Health:\n        HP: 100\n')
        self.assertEqual(result['status'], 'no_single_rank_track')
        self.assertEqual(result['states'], [])

    def test_unsupported_or_unordered_track_refuses(self):
        for text in (ACTOR.replace('200: rank', 'bad: rank'),
                     ACTOR.replace('200: rank', '800: rank'),
                     ACTOR.replace('200: rank', '0: rank')):
            self.assertNotEqual(self.project(text)['status'], 'rank_axis_evaluated')

    def test_wrong_or_dirty_source_is_refused_before_extraction(self):
        for identity in ({'checkout_head': 'wrong', 'checkout_dirty': False},
                         {'checkout_head': rank.PIN, 'checkout_dirty': True},
                         {'checkout_head': rank.PIN, 'checkout_dirty': None}):
            with patch.object(rank.peer, 'git_identity', return_value=identity):
                with self.assertRaisesRegex(ValueError, 'exact clean'):
                    rank.build(ROOT)

    def test_installed_rank_snapshot_is_not_a_certified_unit_state(self):
        document = json.loads((ROOT / 'docs/reference/peer_corpus/base_rank_bbd36d9e.json').read_text(encoding='utf-8'))
        self.assertEqual(document['source_commit'], rank.PIN)
        self.assertEqual(len(document['rows']), 256)
        self.assertEqual(document['status_counts'], {'rank_axis_evaluated': 80,
                         'no_single_rank_track': 147, 'scenario_required': 29})
        self.assertTrue(set(rank.ENGINE_FILES) <= document['source_inputs'].keys())
        for row in document['rows']:
            self.assertEqual(row['factory_state_certification'], 'none')
            self.assertEqual(row['max_state_certification'], 'none')
            self.assertNotIn('dps', row)
        rifle = next(r for r in document['rows'] if (r['mod'], r['actor']) == ('cnc', 'E1'))
        self.assertEqual(rifle['states'][1]['condition_counts'], {'rank-veteran': 3, 'rank-elite': 1})
        self.assertEqual([r['effective_modifier'] for r in rifle['states'][1]['weapon_modifiers']],
                         [100, 100, 150, 125])


if __name__ == '__main__':
    unittest.main()
