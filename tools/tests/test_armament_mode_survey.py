"""Resolved armament topology must not imply simultaneous fire or eligibility."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
import armament_mode_survey as survey
import propose_retained_firepower as proposal
from test_retained_firepower_proposal import fixture, n


def pair_fixture():
    rules = fixture()
    # Inherit the alternate slot: local-only scans must not miss it.
    rules.actors['^BASE'].children.append(n('Armament@Garrison', Weapon='test', Name='garrisoned'))
    return rules


class ModeSurveyTests(unittest.TestCase):
    def test_pair_references_exclude_only_its_two_weapon_fields(self):
        rules = pair_fixture()
        rules.actors['unit'].children.append(n('Explodes', Weapon='TEST'))
        rules.actors['other'] = n('other')
        rules.actors['other'].children.append(n('Armament', Weapon='Test'))
        rules._actor_ci['other'] = 'other'
        rules.weapons['Child'] = n('Child')
        rules.weapons['Child'].children.append(n('Inherits', 'Test'))
        rules._weapon_ci['child'] = 'Child'
        result = survey.build(rules, ['unit'])
        pair = result['same_weapon_pairs'][0]
        self.assertEqual(pair['other_base_yaml_reference_count'], 3)
        self.assertEqual(pair['other_base_yaml_reference_examples'], [
            'actor:other/Armament/Weapon', 'actor:unit/Explodes/Weapon', 'weapon:Child/Inherits'])
        self.assertEqual(result['same_weapon_pairs_with_other_base_yaml_references'], 1)
        self.assertIn('actor:unit/Armament@Garrison/Weapon', proposal.sharing(rules, 'unit', 'Armament', 'TEST'))

    def test_activation_unknown_is_not_false(self):
        self.assertEqual(proposal.attack_activation(n('AttackFrontal', RequiresCondition='deployed')), 'disabled-at-zero-conditions')
        self.assertEqual(proposal.attack_activation(n('AttackFrontal', PauseOnCondition='!enabled')), 'paused-at-zero-conditions')
        self.assertEqual(proposal.attack_activation(n('AttackFrontal', PauseOnCondition='a && b')), 'unknown-condition-expression')
        self.assertEqual(proposal.attack_activation(n('AttackFrontal', PauseOnCondition='disabled')), 'enabled-at-zero-conditions')

    def test_inherited_pair_and_case_insensitive_weapon_reference(self):
        rules = pair_fixture()
        self.assertEqual(survey.topology(rules.resolve('unit')), 'same-weapon-primary-garrison-pair')
        result = survey.pair_detail(rules, 'unit')
        modes = {a['name']: a for a in result['armaments']}
        self.assertEqual(modes['primary']['selected_by_known_own_attacks'], ['AttackFrontal'])
        self.assertEqual(modes['garrisoned']['selected_by_known_own_attacks'], [])
        self.assertIsNone(result['weapon_only_first_blocker'])
        with self.assertRaisesRegex(proposal.Unsupported, 'exactly one actual'):
            proposal.screen(rules, 'unit')

    def test_scoped_factors_are_per_name_not_slot_or_sum(self):
        rules = pair_fixture()
        rules.actors['^BASE'].children.append(n('FirepowerMultiplier@Garrison', Modifier=50, Types='garrisoned'))
        rules.actors['unit'].children.append(n('FirepowerMultiplier@Conditional', Modifier=200, RequiresCondition='inside'))
        result = survey.pair_detail(rules, 'unit')
        factors = {a['name']: a['unconditional_firepower_factor'] for a in result['armaments']}
        self.assertEqual(factors, {'primary': '2/5', 'garrisoned': '1/5'})
        self.assertEqual(result['conditional_firepower_traits'], ['FirepowerMultiplier@Conditional'])

    def test_host_selecting_both_is_not_assumed_exclusive(self):
        rules = pair_fixture()
        rules.actors['host'] = n('host')
        rules.actors['host'].children = [n('AttackGarrisoned', Armaments='primary, garrisoned')]
        rules._actor_ci['host'] = 'host'
        result = survey.build(rules, ['unit'])
        self.assertEqual(result['passenger_attack_hosts'][0]['selectors'][0]['names'], ['primary', 'garrisoned'])
        self.assertEqual(result['ledger_listed_armed_actors'], 1)
        self.assertEqual(result['same_weapon_pair_weapon_only_first_blockers'], {'weapon-only-screen-passed': 1})

    def test_attack_defaults_empty_and_case_are_distinct(self):
        self.assertEqual(survey.selected_names(n('AttackFrontal')), ['primary', 'secondary'])
        self.assertEqual(survey.selected_names(n('AttackFrontal', Armaments='')), [])
        self.assertEqual(survey.selected_names(n('AttackFrontal', Armaments='Primary')), ['Primary'])
        self.assertEqual(survey.selectors(n('unit')), [])

    def test_order_traits_are_not_own_attacks(self):
        actor = n('unit')
        actor.children = [n('AttackMove'), n('AttackWander')]
        self.assertEqual(survey.selectors(actor), [])

    def test_empty_name_does_not_default_to_primary(self):
        rules = pair_fixture()
        rules.actors['unit'].child('Armament').children.append(n('Name', ''))
        self.assertEqual(survey.topology(rules.resolve('unit')), 'other-same-weapon-slots')

    def test_third_slot_and_different_weapons_not_simple_pair(self):
        rules = pair_fixture()
        rules.actors['unit'].children.append(n('Armament@Third', Weapon='test', Name='secondary'))
        self.assertEqual(survey.topology(rules.resolve('unit')), 'other-same-weapon-slots')
        rules = pair_fixture()
        rules.actors['unit'].child('Armament').child('Weapon').value = 'Other'
        self.assertEqual(survey.topology(rules.resolve('unit')), 'different-weapon-primary-garrison-pair')

    def test_selector_inheritance_override_is_resolved(self):
        rules = pair_fixture()
        rules.actors['^BASE'].children.append(n('AttackFrontal', Armaments='garrisoned'))
        # Local empty AttackFrontal inherits this field; it does not restore defaults.
        result = survey.pair_detail(rules, 'unit')
        self.assertEqual(result['attack_selectors'][0]['names'], ['garrisoned'])

    def test_weapon_blocker_and_unknown_attacks_stay_visible(self):
        rules = pair_fixture()
        rules.weapons['Test'].child('Warhead@Damage').children.append(n('PercentageScale', '10000'))
        rules.actors['unit'].children.append(n('AttackTesla'))
        result = survey.pair_detail(rules, 'unit')
        self.assertIn('percentage', result['weapon_only_first_blocker'])
        self.assertEqual(result['unknown_attack_traits'], ['AttackTesla'])

    def test_build_is_deterministic_and_does_not_mutate_sources(self):
        rules = pair_fixture()
        before = {key: proposal.fingerprint(node) for key, node in rules.actors.items()}
        self.assertEqual(survey.build(rules, ['unit', 'missing', 'unit']), survey.build(rules, ['missing', 'unit']))
        self.assertEqual(before, {key: proposal.fingerprint(node) for key, node in rules.actors.items()})
        self.assertEqual(survey.build(rules, ['missing'])['topology_counts'], {'missing-active-actor': 1})


if __name__ == '__main__':
    unittest.main()
