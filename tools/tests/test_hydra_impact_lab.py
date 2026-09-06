"""Focused arithmetic/order tests for the explicitly bounded Hydra experiment."""
import pathlib
import json
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/balance'))
import hydra_impact_lab as lab


def hit(damage=100, state=None, kind='AreaDamage'):
    n = lab.Node('Warhead@test', kind, [lab.Node('Damage', str(damage)),
        lab.Node('Spread','100'), lab.Node('Falloff','100, 0'),
        lab.Node('DamageTypes','TriggerProne, Prone75Percent')])
    if state:
        n.children.extend([lab.Node('PhysicalStateName','Corrosion'),
                           lab.Node('PhysicalStateScale',str(state))])
    return n


class ImpactArithmeticTests(unittest.TestCase):
    def test_modifiers_round_once_and_truncate_negative_toward_zero(self):
        self.assertEqual(1, lab.modifiers(3,[50,90]))
        self.assertEqual(-1, lab.modifiers(-3,[50,90]))

    def test_percentage_armor_precedes_denominator(self):
        n=hit(1,kind='AreaDamagePercentage')
        lab.replace(n,'PercentageDenominator',10000)
        n.children.append(lab.Node('Versus','',[lab.Node('None','150')]))
        result=lab.impact(lab.Node('w','',[n]),lab.Target('test',9999,'None'),())
        # int(9999 * .01 * 1.5) =149, then /100 =>1; early HP truncation gives0.
        self.assertEqual(1,result['percentage'])

    def test_first_hit_triggers_cover_before_second(self):
        t=lab.Target('test',10000,'None',cover={'Prone75Percent':75},triggers=('TriggerProne',))
        result=lab.impact(lab.Node('w','',[hit(),hit()]),t,())
        self.assertEqual([100,75],[x['potential_damage'] for x in result['trace']])

    def test_no_meter_means_no_realized_state(self):
        result=lab.impact(lab.Node('w','',[hit(state=100)]),lab.Target('test',10000,'None'),())
        self.assertIsNone(result['corrosion'])

    def test_bindings_are_separate_and_feedback_changes_second(self):
        t=lab.Target('test',10000,'None',corrosion={'MinValue':0,'MaxValue':1000,'InitialValue':0,'RelaxedValue':0,
            'RelativeToHealth':False,'ApplyDamageModifiers':True},
            vulnerability={'min':100,'max':200,'deviation':True})
        n=hit(state=100)
        n.children.append(lab.Node('PhysicalStates','',[lab.Node('Corrosion','100')]))
        result=lab.impact(lab.Node('w','',[n]),t,())
        self.assertEqual([[100,0,100],[100,100,210]],result['trace'][0]['state_steps'])

    def test_clamping_occurs_between_positive_and_negative_routes(self):
        t=lab.Target('test',10000,'None',corrosion={'MinValue':0,'MaxValue':100,'InitialValue':90,'RelaxedValue':0,
            'RelativeToHealth':False,'ApplyDamageModifiers':False})
        n=hit(20,state=100)
        n.children.append(lab.Node('PhysicalStates','',[lab.Node('Corrosion','-100')]))
        self.assertEqual(80,lab.impact(lab.Node('w','',[n]),t,())['corrosion'])

    def test_folded_percentage_has_half_radius_but_parent_falloff(self):
        n=hit(2000)
        lab.replace(n,'PercentageScale',10000)
        w=lab.Node('w','',[n]); t=lab.Target('test',100000,'None')
        self.assertEqual(500,lab.impact(w,t,(),50)['percentage'])
        self.assertEqual(0,lab.impact(w,t,(),51)['percentage'])
        self.assertGreater(lab.impact(w,t,(),51)['flat'],0)


class ResolvedHydraImpactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules=lab.Ruleset(ROOT)
        cls.hydra=cls.rules.resolve_weapon('HydraSpit')

    def test_corrosion_vulnerability_activates_from_meter_condition(self):
        t=lab.target_from_actor(self.rules.resolve('zerg_hydralisk'))
        self.assertIsNotNone(t.vulnerability)
        self.assertEqual(100,lab.vulnerability_at(t,0))
        self.assertEqual(125,lab.vulnerability_at(t,10000))
        self.assertEqual(100,lab.vulnerability_at(t,199))
        self.assertEqual(100,lab.vulnerability_at(t,200))  # active, but interpolation truncates
        self.assertEqual(150,lab.vulnerability_at(t,20000))
        self.assertEqual((200,20000),t.vulnerability['active_range'])

    def test_real_nod_cover_and_hydra_outgoing_modifiers(self):
        t=lab.target_from_actor(self.rules.resolve('td_nod_minigunner'))
        shooter=self.rules.resolve('zerg_hydralisk')
        fp=[int(n.get('Modifier')) for n in shooter.children_named('FirepowerMultiplier') if lab.enabled(n)]
        self.assertEqual([50,110,110,99],fp)
        result=lab.impact(self.hydra,t,fp)
        self.assertEqual(100,result['trace'][0]['cover'])
        self.assertTrue(all(x['cover']==75 for x in result['trace'][1:]))
        self.assertGreater(result['total'],t.hp)  # intentionally potential damage, not HP removed

    def test_secondary_corrosion_binding_observes_first(self):
        t=lab.target_from_actor(self.rules.resolve('zerg_hydralisk'))
        result=lab.impact(self.hydra,t,[50,110,110,99])
        steps=result['trace'][0]['state_steps']
        self.assertEqual(2,len(steps))
        self.assertGreater(steps[1][2]-steps[1][1],steps[0][2]-steps[0][1])

    def test_candidate_generation_preserves_control(self):
        before=repr(self.hydra)
        lab.make_variants(self.hydra)
        self.assertEqual(before,repr(self.hydra))

    def test_generated_evidence_matches_current_rules_and_evaluator(self):
        data=lab.build()
        self.assertEqual(json.loads(json.dumps(data)),json.loads((ROOT/'docs/audit/latest/hydralisk_impact_lab.json').read_text(encoding='utf-8')))
        self.assertEqual(lab.render(data),(ROOT/'docs/design/HYDRALISK_IMPACT_LAB.md').read_text(encoding='utf-8'))


if __name__=='__main__':
    unittest.main()
