"""Non-rank projections require explicit scenarios and withhold unknown providers."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/reference'))
sys.path.insert(0, str(ROOT / 'tools/tests'))
import peer_state_scenarios as scenario
from test_peer_weapon_evidence import build

ACTOR = '''UNIT:
    GrantConditionOnPrerequisite:
        Condition: bio
        Prerequisites: biolab, !disabled
    GrantConditionOnTerrain:
        Condition: terrain
        TerrainTypes: Tiberium, BlueTiberium
    GrantCondition:
        Condition: active
        RequiresCondition: bio && terrain
    FirepowerMultiplier:
        RequiresCondition: active
        Modifier: 120
    Armament:
        Weapon: Rifle
        RequiresCondition: !active
'''


class ScenarioTests(unittest.TestCase):
    def project(self, text=ACTOR, **kwargs):
        with tempfile.TemporaryDirectory() as folder:
            rules = build(pathlib.Path(folder), text, '')
            return scenario.project(rules.resolve('UNIT'), **kwargs)

    def test_compatible_axes_remain_separate_views(self):
        for keys, terrain, expected in (([], 'Tiberium', 0), (['biolab'], 'Clear', 0),
                                       (['biolab'], 'Tiberium', 1), (['biolab', 'disabled'], 'Tiberium', 0)):
            row = self.project(prerequisites=keys, terrain=terrain)
            self.assertEqual(row['condition_counts']['active'], expected)
            self.assertEqual(row['weapon_modifiers'][0]['effective_modifier'], 120 if expected else 100)
            self.assertEqual(row['armament_activation'][0]['activation_gate_open'], not expected)
            self.assertEqual(row['max_state_certification'], 'none')

    def test_unspecified_is_unknown_not_empty(self):
        row = self.project(terrain='Tiberium')
        self.assertNotIn('bio', row['condition_counts'])
        self.assertIsNone(row['weapon_modifiers'][0]['effective_modifier'])
        self.assertIsNone(self.project(prerequisites=[])['weapon_modifiers'][0]['effective_modifier'])

    def test_empty_prerequisites_do_not_register(self):
        row = self.project(ACTOR.replace('Prerequisites: biolab, !disabled', 'Prerequisites:'))
        self.assertEqual(row['condition_counts']['bio'], 0)

    def test_unknown_duplicate_permanent_and_cycles_are_withheld(self):
        for text in (ACTOR + '    ExternalCondition:\n        Condition: bio\n',
                     ACTOR.replace('Condition: active', 'Condition: active\n        GrantPermanently: true'),
                     ACTOR.replace('RequiresCondition: bio && terrain', 'RequiresCondition: active')):
            row = self.project(text, prerequisites=['biolab'], terrain='Tiberium')
            self.assertNotIn('active', row['condition_counts'])
            self.assertIsNone(row['weapon_modifiers'][0]['effective_modifier'])

    def test_compound_grammar_precedence_and_refusals(self):
        values = {'a': 1, 'b': 0, 'c': 0}
        self.assertTrue(scenario.condition_value('a || b && c', values))
        self.assertFalse(scenario.condition_value('a && b || c', values))
        for text in ('a &&', 'a || missing', '(a)', 'a + 1', 'a & b'):
            self.assertIsNone(scenario.condition_value(text, values))

    def test_explicit_input_validation(self):
        for kwargs in ({'prerequisites': 'bio'}, {'prerequisites': [True]}, {'terrain': True}, {'rank_state': 'elite'},
                       {'fresh_no_attacks': True, 'rank_state': 'maximum_rank'}):
            with self.assertRaises(ValueError):
                self.project(**kwargs)

    def test_non_rank_provider_cannot_overwrite_rank_axis(self):
        text = '''UNIT:
    GainsExperience:
        Conditions:
            100: rank
    GrantConditionOnDeploy:
        DeployedCondition: rank
'''
        with self.assertRaises(ValueError):
            self.project(text, rank_state='unranked', deploy_states={'GrantConditionOnDeploy': 'Deployed'})

    def test_pin_and_dirty_refusal(self):
        for identity in ({'checkout_head': 'wrong', 'checkout_dirty': False},
                         {'checkout_head': scenario.rank.PIN, 'checkout_dirty': True}):
            with patch.object(scenario.rank.peer, 'git_identity', return_value=identity):
                with self.assertRaisesRegex(ValueError, 'exact clean'):
                    scenario.build(ROOT, [])

    def test_deploy_completed_endpoints_do_not_mix_or_guess_transitions(self):
        text = '''UNIT:
    GrantConditionOnDeploy:
        DeployedCondition: deployed
        UndeployedCondition: undeployed
        PauseOnCondition: unknown
    Armament:
        Weapon: Gun
        RequiresCondition: deployed
'''
        for state in ('Deployed', 'Undeployed'):
            row = self.project(text, deploy_states={'GrantConditionOnDeploy': state})
            self.assertEqual(row['condition_counts'], {'deployed': int(state == 'Deployed'),
                                                     'undeployed': int(state == 'Undeployed')})
        for state in ('Deploying', 'Undeploying'):
            with self.assertRaises(ValueError):
                self.project(text, deploy_states={'GrantConditionOnDeploy': state})
        self.assertIsNone(self.project(text)['armament_activation'][0]['activation_gate_open'])

    def test_plugs_allow_exactly_one_active_choice_per_socket(self):
        text = '''UNIT:
    Pluggable:
        Conditions:
            gun: tower.gun
            rocket: tower.rocket
    Armament:
        Weapon: Gun
        RequiresCondition: tower.gun
'''
        for selected in ('', 'gun', 'rocket'):
            row = self.project(text, plugs={'Pluggable': selected})
            self.assertEqual(row['condition_counts'], {'tower.gun': int(selected == 'gun'),
                                                     'tower.rocket': int(selected == 'rocket')})
            self.assertEqual(row['armament_activation'][0]['activation_gate_open'], selected == 'gun')
        for value in ('unknown', ['gun', 'rocket']):
            with self.assertRaises(ValueError):
                self.project(text, plugs={'Pluggable': value})

    def test_damage_state_counts_duplicate_providers_but_refuses_permanence(self):
        text = '''UNIT:
    GrantConditionOnDamageState@ONE:
        Condition: damaged
    GrantConditionOnDamageState@TWO:
        Condition: damaged
'''
        self.assertEqual(self.project(text, damage_state='Heavy')['condition_counts']['damaged'], 2)
        self.assertEqual(self.project(text, damage_state='Undamaged')['condition_counts']['damaged'], 0)
        self.assertNotIn('damaged', self.project(text)['condition_counts'])
        permanent = text.replace('Condition: damaged', 'Condition: damaged\n        GrantPermanently: true', 1)
        self.assertNotIn('damaged', self.project(permanent, damage_state='Heavy')['condition_counts'])

    def test_subterranean_layer_alone_is_not_condition_proof(self):
        text = 'UNIT:\n    GrantConditionOnSubterraneanLayer:\n        Condition: submerged\n'
        self.assertEqual(self.project(text)['condition_counts'], {})
        for position, count in (('below-threshold-on-subterranean', 1), ('above-threshold-off-subterranean', 0)):
            row = self.project(text, subterranean_position='after-position-change-' + position)
            self.assertEqual(row['condition_counts']['submerged'], count)
        with self.assertRaises(ValueError):
            self.project(text, subterranean_position='on-subterranean')

    def test_fresh_no_attack_is_explicit_and_never_a_max_history_default(self):
        text = '''UNIT:
    GrantConditionOnAttack:
        Condition: firing
    Armament:
        ReloadingCondition: reloading
        Weapon: Gun
        PauseOnCondition: reloading
'''
        row = self.project(text, fresh_no_attacks=True)
        self.assertEqual(row['condition_counts'], {'firing': 0, 'reloading': 0})
        self.assertTrue(row['armament_activation'][0]['activation_gate_open'])
        self.assertEqual(self.project(text)['condition_counts'], {})

    def test_installed_scenarios_are_source_pinned_and_separate(self):
        document = json.loads((ROOT / 'docs/reference/peer_corpus/base_scenarios_bbd36d9e.json').read_text())
        self.assertEqual(document['source_commit'], scenario.rank.PIN)
        self.assertTrue(set(scenario.ENGINE_FILES) <= document['source_inputs'].keys())
        self.assertEqual(len(document['rows']), 15)
        self.assertEqual([x['condition_counts']['hazmatsuits'] for x in document['rows'][:4]], [0, 0, 0, 1])
        for row in document['rows'][:4]:
            self.assertNotIn('damaged', row['condition_counts'])
            self.assertNotIn('hospitalheal', row['condition_counts'])
        for row in document['rows']:
            self.assertEqual(row['factory_state_certification'], 'none')
            self.assertEqual(row['max_state_certification'], 'none')
            self.assertNotIn('dps', row)
        by_name = {x['name']: x for x in document['rows']}
        for plug in ('none', 'vulcan', 'rocket', 'sam'):
            states = by_name['ts-tower-' + plug]['armament_activation']
            self.assertEqual(sum(x['activation_gate_open'] is True for x in states), int(plug != 'none'))
        self.assertTrue(by_name['ts-artillery-Deployed']['armament_activation'][0]['activation_gate_open'])
        self.assertFalse(by_name['ts-artillery-Undeployed']['armament_activation'][0]['activation_gate_open'])
        self.assertFalse(by_name['ts-subtank-submerged']['armament_activation'][0]['activation_gate_open'])
        self.assertTrue(by_name['ts-subtank-surfaced']['armament_activation'][0]['activation_gate_open'])
        self.assertTrue(all(x['activation_gate_open'] for x in by_name['cnc-apc-fresh-no-attacks']['armament_activation']))
        self.assertEqual(by_name['cnc-e1-hospital-Heavy']['condition_counts']['hospitalheal'], 1)
        self.assertEqual(by_name['cnc-e1-hospital-Undamaged']['condition_counts']['hospitalheal'], 0)


if __name__ == '__main__':
    unittest.main()
