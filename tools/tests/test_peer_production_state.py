"""Production/upgrade evidence is retained, never promoted to state certification."""
import pathlib
import tempfile
import unittest

from test_peer_weapon_evidence import build, epu


ACTORS = '''BASE:
    Buildable:
        Prerequisites: ~vehicles, ~!tow.upgrade
    ProducibleWithLevel:
        Prerequisites: vehicles.upgraded
        InitialLevels: 1
    GrantConditionOnDamageState:
        Condition: injured
    ReplacedInQueue:
        Actors: variant, missing
    Upgradeable@TOW:
        Actor: variant
        Type: tow.upgrade
        RequiresCondition: !mindcontrolled
        UpgradeAtActors: repair, depot
    Upgradeable@ARMOR:
        Condition: armor-upgraded
        Type: armor.upgrade
VARIANT:
    Inherits: BASE
    -ReplacedInQueue:
    -Upgradeable@TOW:
    Buildable:
        Prerequisites: ~vehicles, ~tow.upgrade
'''


class ProductionStateEvidence(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.rules = build(pathlib.Path(tmp.name), ACTORS, '')

    def evidence(self, actor):
        return epu.production_state_evidence(self.rules, self.rules.resolve(actor))

    def test_production_rank_and_grant_conditions_are_not_assumed_false(self):
        row = self.evidence('BASE')
        self.assertEqual([x['key'] for x in row['production_traits']],
                         ['Buildable', 'ProducibleWithLevel'])
        level = row['production_traits'][1]
        fields = {x['key']: x['value'] for x in level['children']}
        self.assertEqual(fields['Prerequisites'], 'vehicles.upgraded')
        self.assertEqual(fields['InitialLevels'], '1')
        self.assertEqual(row['condition_grants'][0]['key'], 'GrantConditionOnDamageState')
        self.assertEqual(row['factory_ready_certification'], 'none')

    def test_declared_routes_preserve_targets_and_unknown_existence(self):
        row = self.evidence('BASE')
        self.assertEqual(len(row['declared_routes']), 3)
        queue = row['declared_routes'][0]
        self.assertEqual(queue['targets'], [
            {'actor': 'variant', 'definition_exists': True},
            {'actor': 'missing', 'definition_exists': False}])
        self.assertEqual(queue['combination'], 'do_not_sum_declared_target_actors')
        self.assertTrue(all(x['activation'] == 'unverified' for x in row['declared_routes']))
        self.assertEqual(row['maximum_upgrade_certification'], 'none')

    def test_resolved_removals_do_not_resurrect_parent_routes(self):
        row = self.evidence('VARIANT')
        self.assertEqual([r['trait'] for r in row['declared_routes']], ['Upgradeable@ARMOR'])
        self.assertEqual(row['declared_routes'][0]['targets'], [])
        self.assertEqual(row['declared_routes'][0]['combination'],
                         'condition_upgrade_compatibility_unverified')

    def test_empty_inventory_is_not_certified_complete(self):
        rules = build(pathlib.Path(self.add_temp()), 'PLAIN:\n    Health:\n        HP: 100\n', '')
        row = epu.production_state_evidence(rules, rules.resolve('PLAIN'))
        self.assertEqual(row['declared_routes'], [])
        self.assertEqual(row['factory_ready_certification'], 'none')
        self.assertEqual(row['maximum_upgrade_certification'], 'none')

    def test_unarmed_modifiers_and_prerequisites_remain_unverified(self):
        actors = """TRUCK:
    Health:
        HP: 100
    SpeedMultiplier@POLICY:
        Modifier: 125
        RequiresCondition: policy && !driver-dead
    ProductionCostMultiplier:
        Prerequisites: is-hard-ai
        Multiplier: 80
    ChangesHealth:
        Step: 10
        PauseOnCondition: disabled
"""
        rules = build(pathlib.Path(self.add_temp()), actors, '')
        row = epu.production_state_evidence(rules, rules.resolve('TRUCK'), review_initial_state=True)
        review = row['initial_state_review']
        self.assertEqual(review['status'], 'unverified')
        self.assertEqual([x['expression'] for x in review['condition_uses']],
                         ['policy && !driver-dead', 'disabled'])
        self.assertTrue(all(x['initial_value'] == 'unverified' for x in review['condition_uses']))
        self.assertEqual(review['prerequisite_uses'], [{
            'trait': 'ProductionCostMultiplier', 'field': 'Prerequisites',
            'expression': 'is-hard-ai', 'satisfied': 'unverified'}])
        self.assertEqual([x['key'] for x in review['modifier_traits']],
                         ['SpeedMultiplier@POLICY', 'ProductionCostMultiplier', 'ChangesHealth'])
        self.assertEqual(row['factory_ready_certification'], 'none')
        self.assertEqual(row['maximum_upgrade_certification'], 'none')

    def test_state_review_is_opt_in_and_does_not_change_existing_evidence(self):
        plain = self.evidence('BASE')
        reviewed = epu.production_state_evidence(self.rules, self.rules.resolve('BASE'),
                                               review_initial_state=True)
        self.assertNotIn('initial_state_review', plain)
        self.assertEqual(reviewed.pop('initial_state_review')['status'], 'unverified')
        self.assertEqual(reviewed, plain)

    def test_reviewed_removals_and_empty_conditions_do_not_reappear(self):
        actors = """PARENT:
    SpeedMultiplier:
        Modifier: 150
        RequiresCondition: upgraded
CHILD:
    Inherits: PARENT
    -SpeedMultiplier:
    Pausable:
        PauseOnCondition:
"""
        rules = build(pathlib.Path(self.add_temp()), actors, '')
        row = epu.production_state_evidence(rules, rules.resolve('CHILD'), review_initial_state=True)
        self.assertEqual(row['initial_state_review']['modifier_traits'], [])
        self.assertEqual(row['initial_state_review']['condition_uses'], [])
        self.assertEqual(row['factory_ready_certification'], 'none')

    def test_pilot_is_explicitly_four_ca_actors_only(self):
        self.assertEqual(epu.STATE_REVIEW_COHORTS,
                         {'ca': frozenset(('HARV', 'LST', 'HMMV', 'HMMV.TOW'))})

    def add_temp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return tmp.name


if __name__ == '__main__':
    unittest.main()
