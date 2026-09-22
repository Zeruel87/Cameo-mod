import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'audit'))
from miniyaml import Node
import shrapnel_damage as sd


def node(key, value='', children=()):
    return Node(key, value, list(children), pathlib.Path('fixture.yaml'), 1)


def weapon(name, damage, child=None, chance='100', amount='1'):
    children = [node('Damage', str(damage)), node('Burst', '99')]
    if child:
        children.append(node('Warhead@fragments', 'FireShrapnel', [
            node('Weapon', child), node('AimChance', chance), node('Amount', amount)]))
    return node(name, children=children)


class ShrapnelDamageTests(unittest.TestCase):
    def test_engine_exclusive_amount(self):
        self.assertEqual(sd.expected_amount('2, 5'), 3)
        self.assertEqual(sd.expected_amount('2, 2'), 2)
        with self.assertRaises(ValueError):
            sd.expected_amount('5, 2')

    def test_explicit_credit_and_no_random_fallback(self):
        self.assertEqual([sd.fragment_credit(c, .5) for c in [0, 50, 100]], [.5, .75, 1])
        self.assertEqual(sd.fragment_credit(25, .5), .625)
        self.assertEqual(sd.fragment_credit(0, .5, False), 0)
        self.assertEqual(sd.fragment_credit(50, .5, False), .5)

    def test_recursive_payload_once_without_child_burst(self):
        weapons = {'a': weapon('a', 100, 'b', '50', '3'),
                   'b': weapon('b', 20, 'c'), 'c': weapon('c', 10)}
        result = sd.damage_tree('a', weapons.get, lambda n: float(n.get('Damage')),
                              random_hit_credit=.5)
        self.assertEqual(result['direct'], 100)
        self.assertEqual(result['shrapnel'], 67.5)
        self.assertEqual(result['total'], 167.5)

    def test_repeated_parent_impacts_multiply_emission_only(self):
        weapons = {'a': weapon('a', 200, 'b'), 'b': weapon('b', 10)}
        result = sd.damage_tree('a', weapons.get, lambda n: float(n.get('Damage')),
                              random_hit_credit=.5,
                              impact_count=lambda n: 2 if n.key == 'a' else 1)
        self.assertEqual(result['total'], 220)

    def test_missing_and_recursive_references_are_not_zero_damage(self):
        for weapons in [{'a': weapon('a', 100, 'absent')},
                        {'a': weapon('a', 100, 'b'), 'b': weapon('b', 10, 'a')}]:
            with self.assertRaises(ValueError):
                sd.damage_tree('a', weapons.get, lambda n: float(n.get('Damage')),
                               random_hit_credit=.5)

    def test_target_enumerator_is_consumed(self):
        self.assertEqual(sd.emission_counts('3', 100, 1), (1, 2))
        self.assertEqual(sd.emission_counts('3', 50, 1), (.875, 2.125))
        self.assertEqual(sd.emission_counts('2, 4', 100, 2), (2, .5))

    def test_no_target_no_throw_means_no_extra_damage(self):
        parent = weapon('a', 100, 'b')
        parent.child('Warhead@fragments').children.append(node('ThrowWithoutTarget','false'))
        weapons = {'a':parent,'b':weapon('b',20)}
        result = sd.damage_tree('a',weapons.get,lambda n:float(n.get('Damage')),
                               random_hit_credit=.5,eligible_targets=lambda n,w:0)
        self.assertEqual(result['total'],100)

    def test_no_target_with_random_fallback_uses_explicit_credit(self):
        weapons = {'a':weapon('a',100,'b'),'b':weapon('b',20)}
        result = sd.damage_tree('a',weapons.get,lambda n:float(n.get('Damage')),
                               random_hit_credit=.5,eligible_targets=lambda n,w:0)
        self.assertEqual(result['total'],110)

    def test_canonical_model_exposes_unmodeled_shrapnel(self):
        import effective_damage as ed
        parent = weapon('a',100,'b')
        self.assertIn('unmodeled_secondary_payload:FireShrapnel',ed.model_limitations(parent))

    def test_pure_emitter_is_not_certified_zero_damage(self):
        import extract_stats
        parent = weapon('a',0,'b')
        result = extract_stats.derived_metrics(parent,{})
        self.assertEqual(result['model_status'],'provisional')
        self.assertIn('unmodeled_secondary_payload:FireShrapnel',result['model_limitations'])


if __name__ == '__main__':
    unittest.main()
