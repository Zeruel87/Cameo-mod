"""Conservative nominal proposal lane: no global edits or hidden retirement."""
import json
import pathlib
import sys
import unittest
from fractions import Fraction
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
import propose_retained_firepower as tool
from miniyaml import Node, Ruleset


def n(key, value='', **fields):
    return Node(key, str(value), [Node(k, str(v)) for k, v in fields.items()],
                str(tool.ROOT / 'mods/cameo/fixture.yaml'))


def fixture():
    rules = object.__new__(Ruleset)
    base = n('^BASE')
    base.children = [n('FirepowerMultiplier@GlobalBuffs', Modifier=50)]
    actor = n('unit')
    actor.children = [n('Inherits', '^BASE'), n('FirepowerMultiplier', Modifier=80),
                      n('Armament', Weapon='Test'), n('AttackFrontal')]
    weapon = n('Test', ReloadDelay=10)
    weapon.children += [n('Projectile', 'Bullet'), n('Warhead@Damage', 'SpreadDamage', Damage=1000)]
    rules.actors = {'^BASE': base, 'unit': actor}
    rules.weapons = {'Test': weapon}
    rules._actor_ci = {k.lower(): k for k in rules.actors}
    rules._weapon_ci = {k.lower(): k for k in rules.weapons}
    rules._resolve_cache = {}
    return rules


class ProposalTests(unittest.TestCase):
    def test_paused_or_unknown_armament_is_rejected(self):
        for condition in ('!enabled', 'a && b'):
            rules = fixture()
            rules.actors['unit'].child('Armament').children.append(n('PauseOnCondition', condition))
            with self.assertRaisesRegex(tool.Unsupported, 'armament is paused or unknown'):
                tool.propose(rules, 'unit', '40')

    def test_disabled_paused_or_unknown_attack_does_not_supply_baseline_fire(self):
        for field, value in (('RequiresCondition', 'deployed'), ('PauseOnCondition', '!enabled'),
                             ('RequiresCondition', '!a && !b'), ('PauseOnCondition', 'bad ? expression')):
            rules = fixture()
            rules.actors['unit'].child('AttackFrontal').children.append(n(field, value))
            with self.assertRaisesRegex(tool.Unsupported, 'disabled, paused or unknown'):
                tool.propose(rules, 'unit', '40')

    def test_zero_snapshot_accepts_simple_unpaused_attack_not_general_readiness(self):
        rules = fixture()
        rules.actors['unit'].child('AttackFrontal').children += [n('RequiresCondition', '!disabled'),
                                                              n('PauseOnCondition', 'emp')]
        self.assertEqual(tool.propose(rules, 'unit', '40')['proposed_damage'], 1000)

    def test_primary_must_be_selected_by_an_actual_attack(self):
        for fields in ('secondary', '', 'Primary'):
            rules = fixture()
            rules.actors['unit'].child('AttackFrontal').children.append(n('Armaments', fields))
            with self.assertRaisesRegex(tool.Unsupported, 'not selected'):
                tool.propose(rules, 'unit', '40')

    def test_attack_move_or_wander_does_not_supply_an_attack(self):
        for kind in ('AttackMove', 'AttackWander'):
            rules = fixture()
            rules.actors['unit'].child('AttackFrontal').key = kind
            with self.assertRaisesRegex(tool.Unsupported, 'not selected'):
                tool.propose(rules, 'unit', '40')

    def test_inherited_attack_selector_must_select_primary(self):
        rules = fixture()
        rules.actors['^BASE'].children.append(n('AttackFrontal', Armaments='secondary'))
        with self.assertRaisesRegex(tool.Unsupported, 'not selected'):
            tool.propose(rules, 'unit', '40')

    def test_actor_specific_local_retirement(self):
        rules = fixture()
        rules.actors['unit'].child('FirepowerMultiplier').key = 'FirepowerMultiplier@unit'
        result = tool.propose(rules, 'unit', '40', 'FirepowerMultiplier@unit')
        self.assertEqual(result['proposed_damage'], 800)
        self.assertEqual(result['retire_exact_local_trait']['trait'], 'FirepowerMultiplier@unit')

    def test_burst_cycle_preserves_all_intershot_delays(self):
        rules = fixture()
        rules.weapons['Test'].children += [n('Burst', '3'), n('BurstDelays', '2, 7')]
        result = tool.propose(rules, 'unit', '720/19')
        self.assertEqual(result['proposed_damage'], 600)
        self.assertEqual(result['cycle_ticks'], '19')
        self.assertEqual(result['predicted_dps'], '720/19')

    def test_omitted_reload_uses_engine_one_tick_default(self):
        rules = fixture()
        rules.weapons['Test'].children = [c for c in rules.weapons['Test'].children if c.key != 'ReloadDelay']
        result = tool.propose(rules, 'unit', '400')
        self.assertEqual(result['proposed_damage'], 1000)
        self.assertEqual(result['predicted_dps'], '400')

    def test_retains_everything_by_default(self):
        r = tool.propose(fixture(), 'unit', '40')
        self.assertIsNone(r['retire_exact_local_trait'])
        self.assertEqual(r['retained_factor'], '2/5')
        self.assertEqual(r['proposed_damage'], 1000)

    def test_explicit_local_retirement_keeps_global_factor(self):
        r = tool.propose(fixture(), 'unit', '40', 'FirepowerMultiplier')
        self.assertEqual(r['retained_factor'], '1/2')
        self.assertEqual(r['proposed_damage'], 800)
        self.assertEqual(r['predicted_dps'], '40')
        self.assertEqual(r['residual_dps'], '0')
        self.assertEqual([e['trait'] for e in r['retained_modifiers']], ['FirepowerMultiplier@GlobalBuffs'])

    def test_inherited_override_resurfacing_blocks(self):
        rules = fixture()
        rules.actors['^BASE'].children.append(n('FirepowerMultiplier', Modifier=90))
        with self.assertRaisesRegex(tool.Unsupported, 'reveals an inherited'):
            tool.propose(rules, 'unit', '40', 'FirepowerMultiplier')

    def test_global_and_nonexistent_retirements_block(self):
        for key in ('FirepowerMultiplier@GlobalBuffs', 'FirepowerMultiplier@unit'):
            with self.assertRaises(tool.Unsupported):
                tool.propose(fixture(), 'unit', '40', key)

    def test_conditional_or_scoped_local_retirement_blocks(self):
        for field in ('RequiresCondition', 'Types'):
            rules = fixture()
            rules.actors['unit'].child('FirepowerMultiplier').children.append(n(field, 'x'))
            with self.assertRaisesRegex(tool.Unsupported, 'conditional/scoped'):
                tool.propose(rules, 'unit', '40', 'FirepowerMultiplier')

    def test_nonapplicable_scoped_and_conditional_modifiers_are_unchanged(self):
        rules = fixture()
        rules.actors['unit'].children += [n('FirepowerMultiplier@secondary', Modifier=20, Types='secondary'),
                                         n('FirepowerMultiplier@upgrade', Modifier=200, RequiresCondition='upgrade')]
        before = tool.fingerprint(rules.actors['unit'])
        r = tool.propose(rules, 'unit', '40', 'FirepowerMultiplier')
        self.assertEqual(r['retained_factor'], '1/2')
        self.assertEqual(tool.fingerprint(rules.actors['unit']), before)

    def test_nearest_grid_ties_choose_lower_and_low_targets_are_flagged(self):
        self.assertEqual(tool.solve_grid('15', Fraction(1), 1, 10), (100, Fraction(10), Fraction(-5)))
        result = tool.propose(fixture(), 'unit', '1')
        self.assertTrue(result['grid_floor_limited'])
        self.assertEqual(result['proposed_damage'], 100)
        self.assertEqual(result['residual_dps'], '3')

    def test_zero_negative_and_overflow_targets_rejected(self):
        for value in ('0', '-1', '1e30', 'NaN', 'Infinity'):
            with self.assertRaises((tool.Unsupported, ValueError)):
                tool.propose(fixture(), 'unit', value)

    def test_zero_retained_firepower_rejected(self):
        rules = fixture()
        rules.actors['^BASE'].child('FirepowerMultiplier@GlobalBuffs').child('Modifier').value = '0'
        with self.assertRaisesRegex(tool.Unsupported, 'zero, negative'):
            tool.propose(rules, 'unit', '40')

    def test_other_actor_nonarmament_reference_blocks(self):
        rules = fixture()
        rules.actors['other'] = n('other')
        rules.actors['other'].children = [n('Explodes', Weapon='Test')]
        with self.assertRaisesRegex(tool.Unsupported, 'shared/referenced'):
            tool.propose(rules, 'unit', '40')

    def test_weapon_delivery_and_inheritance_references_block(self):
        for fields in ([n('Inherits', 'Test')], [n('Warhead@Spawn', 'FireCluster', Weapon='Test')]):
            rules = fixture()
            rules.weapons['other'] = n('other')
            rules.weapons['other'].children = fields
            with self.assertRaisesRegex(tool.Unsupported, 'shared/referenced'):
                tool.propose(rules, 'unit', '40')

    def test_alternate_armament_and_casing_weapon_block(self):
        rules = fixture()
        rules.actors['unit'].children.append(n('Armament@Garrison', Weapon='Test', Name='garrisoned'))
        with self.assertRaisesRegex(tool.Unsupported, 'exactly one actual'):
            tool.propose(rules, 'unit', '40')
        rules = fixture()
        rules.actors['unit'].child('Armament').children.append(n('CasingWeapon', 'Test'))
        with self.assertRaisesRegex(tool.Unsupported, 'casing'):
            tool.propose(rules, 'unit', '40')

    def test_damage_feedback_and_scheduling_block(self):
        for field, value in (('PercentageScale', '10000'), ('IntegrityScale', '1'),
                             ('PhysicalStateName', 'Corrosion'), ('Ticks', '2'), ('TickDamage', '100, 200')):
            rules = fixture()
            rules.weapons['Test'].child('Warhead@Damage').children.append(n(field, value))
            with self.assertRaises(tool.Unsupported):
                tool.propose(rules, 'unit', '40')

    def test_cadence_and_repeated_projectiles_block(self):
        for trait in ('ReloadDelayMultiplier', 'AttackTesla', 'AmmoPool'):
            rules = fixture()
            rules.actors['unit'].children.append(n(trait))
            with self.assertRaises(tool.Unsupported):
                tool.propose(rules, 'unit', '40')
        rules = fixture()
        rules.weapons['Test'].child('Projectile').children.append(n('BounceCount', '1'))
        with self.assertRaisesRegex(tool.Unsupported, 'bouncing'):
            tool.propose(rules, 'unit', '40')

    def test_success_and_rejection_do_not_mutate_input_or_write(self):
        rules = fixture()
        before = (tool.fingerprint(rules.actors['unit']), tool.fingerprint(rules.weapons['Test']))
        with patch.object(pathlib.Path, 'write_text', side_effect=AssertionError('write forbidden')):
            tool.propose(rules, 'unit', '45', 'FirepowerMultiplier')
            with self.assertRaises(tool.Unsupported):
                tool.propose(rules, 'unit', '0')
        self.assertEqual(before, (tool.fingerprint(rules.actors['unit']), tool.fingerprint(rules.weapons['Test'])))

    def test_grid_search_matches_exhaustive_neighborhood(self):
        for factor in (Fraction(1, 2), Fraction(121, 200), Fraction(11, 10)):
            for target in (Fraction(31, 7), Fraction(199, 3), Fraction(301, 2)):
                damage, actual, residual = tool.solve_grid(target, factor, 3, Fraction(17))
                best = min(range(100, 10000, 100), key=lambda d: (abs(d * factor * 3 / 17 - target), d))
                self.assertEqual(damage, best)
                self.assertEqual(actual - target, residual)


class LiveProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(tool.ROOT)

    def test_spy_is_a_supported_retained_factor_case(self):
        result = tool.propose(self.rules, 'ra1_allies_raspy', '1815/16')
        self.assertEqual(result['proposed_damage'], 15000)
        self.assertEqual(result['retained_factor'], '121/200')
        self.assertEqual(result['residual_dps'], '0')

    def test_hydra_stays_blocked(self):
        with self.assertRaises(tool.Unsupported):
            tool.propose(self.rules, 'zerg_hydralisk', '100')


if __name__ == '__main__':
    unittest.main()
