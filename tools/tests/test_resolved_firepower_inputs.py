"""Pricing inputs must include inherited, applicable unconditional modifiers."""
import unittest
import pathlib
import sys
import json
from unittest.mock import Mock, patch
import _bootstrap  # noqa: F401
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
import extract_stats as extract
import fit_class
import firepower_input_report
from miniyaml import Node, Ruleset


def trait(key, modifier, condition=None, types=None):
    fields = [Node('Modifier', str(modifier))]
    if condition is not None:
        fields.append(Node('RequiresCondition', condition))
    if types is not None:
        fields.append(Node('Types', types))
    return Node(key, '', fields)


class SyntheticFirepowerTests(unittest.TestCase):
    def test_impact_report_matches_ledgers(self):
        self.assertEqual(firepower_input_report.build(), json.loads(
            firepower_input_report.OUTPUT.read_text(encoding='utf-8')))

    def test_extractor_preserves_explicit_empty_armament_name(self):
        actor = Node('unit', '', [Node('Valued', '', [Node('Cost', '100')]),
            Node('Armament', '', [Node('Weapon', 'test'), Node('Name', '')])])
        rules = Mock()
        rules.resolve.return_value = actor
        rules.actor.return_value = None
        with patch.object(extract, 'weapon_entry', return_value=None), \
             patch.object(extract, 'actor_subtype', return_value='Infantry'):
            unit = extract.extract_actor(rules, 'unit', 'infantry')
        self.assertEqual(unit['armaments'][0]['armament_name'], '')

    def test_inheritance_condition_and_scoped_traits(self):
        actor = Node('unit', '', [trait('FirepowerMultiplier@a', 50),
            trait('FirepowerMultiplier@b', 80, types='secondary'),
            trait('FirepowerMultiplier@upgrade', 200, 'upgraded')])
        entries = extract.resolved_firepower_modifiers(actor, None)
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e['src'] == 'inherited' for e in entries))
        unit = {'resolved_firepower_modifiers': entries,
                'firepower_multiplier': {'v': 99}}
        self.assertEqual(fit_class.armament_firepower(unit, {}), .5)
        self.assertEqual(fit_class.armament_firepower(unit, {'armament_name': 'secondary'}), .4)
        self.assertEqual(fit_class.armament_firepower(unit, {'armament_name': 'SECONDARY'}), .5)

    def test_empty_resolved_list_overrides_legacy(self):
        self.assertEqual(fit_class.armament_firepower(
            {'resolved_firepower_modifiers': [], 'firepower_multiplier': {'v': .5}}, {}), 1)

    def test_legacy_zero_is_not_unity(self):
        self.assertEqual(fit_class.armament_firepower({'firepower_multiplier': {'v': 0}}, {}), 0)
        self.assertEqual(fit_class.armament_firepower({}, {}), 1)

    def test_zero_and_multiple_local_modifiers(self):
        actor = Node('unit', '', [trait('FirepowerMultiplier', 0), trait('FirepowerMultiplier@b', 150)])
        self.assertEqual(fit_class.armament_firepower(
            {'resolved_firepower_modifiers': extract.resolved_firepower_modifiers(actor, None)}, {}), 0)

    def test_both_raw_and_derived_dps_apply_once(self):
        arm = {'slot': 'Armament', 'weapon': 'test', 'reloaddelay': '10',
               'range': '5c0', 'damage_warheads': [{'type': 'SpreadDamage', 'damage': '1000'}]}
        unit = {'hp': {'v': 100}, 'speed': {'v': 50}, 'armaments': [arm],
                'resolved_firepower_modifiers': [{'modifier': 50, 'types': []}],
                'firepower_multiplier': {'v': .1}}
        raw, _ = fit_class.unit_inputs(unit)
        self.assertEqual(raw[3], 50)
        derived, count = fit_class.unit_inputs(unit, {'armaments': [dict(arm, effective_dps=80)]}, True)
        self.assertEqual(derived[3], 40)
        self.assertEqual(count, 0)

    def test_multiple_armaments_get_their_own_multiplier(self):
        arms = [{'slot': 'Armament@' + name, 'armament_name': name, 'weapon': name,
                 'reloaddelay': '10', 'range': '5c0',
                 'damage_warheads': [{'type': 'SpreadDamage', 'damage': '1000'}]}
                for name in ('primary', 'secondary')]
        unit = {'hp': {'v': 100}, 'speed': {'v': 50}, 'armaments': arms,
                'resolved_firepower_modifiers': [{'modifier': 50, 'types': ['primary']},
                                                 {'modifier': 200, 'types': ['secondary']}]}
        self.assertEqual(fit_class.unit_inputs(unit)[0][3], 250)
        self.assertEqual(fit_class.armament_firepower(unit, {'armament_name': ''}), 1)


class ResolvedFirepowerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(extract.ROOT)

    def test_hydra_and_marine_include_inherited_modifiers(self):
        for name, percentages in (('zerg_hydralisk', [50, 110, 110, 99]),
                                  ('terran_marine', [50, 110, 110, 31])):
            actor = self.rules.resolve(name)
            entries = extract.resolved_firepower_modifiers(actor, None)
            self.assertGreater(len(entries), 1)
            self.assertEqual([e['modifier'] for e in entries], percentages)
            expected = 1.0
            for node in actor.children_named('FirepowerMultiplier'):
                if not node.get('RequiresCondition') and (not node.get('Types') or 'primary' in node.get('Types').split(', ')):
                    expected *= int(node.get('Modifier') or '100') / 100
            self.assertAlmostEqual(fit_class.armament_firepower({'resolved_firepower_modifiers': entries}, {}), expected)
            self.assertLess(expected, .99)


if __name__ == '__main__':
    unittest.main()
