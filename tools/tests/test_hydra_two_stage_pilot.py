"""The inactive implementation must preserve its stated boundaries honestly."""
import json
import pathlib
import sys
import unittest
from fractions import Fraction

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/balance'))
import hydra_two_stage_pilot as pilot
import hydra_impact_lab as lab
import hydra_history


class TwoStagePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules=pilot.Ruleset(ROOT)
        cls.current=hydra_history.weapon()
        cls.targets,cls.firepower=hydra_history.scenario(lab)
        cls.proposed,cls.armors,cls.knots,cls.curve=pilot.fit(cls.current)

    def test_pilot_is_not_in_active_includes_or_weapon_inventory(self):
        self.assertNotIn(pilot.PILOT.resolve(),[p.resolve() for p in self.rules.manifest.weapons])
        self.assertNotIn(pilot.NAME,self.rules.weapons)
        self.assertEqual(4,len([n for n in self.current.children if n.value in ('AreaDamage','SpreadDamage')]))

    def test_exactly_two_mains_preserve_raw_total(self):
        mains=[n for n in self.proposed.children if n.value in ('AreaDamage','SpreadDamage')]
        self.assertEqual(['Warhead@LightChemicalWeapon','Warhead@LightMissile'],[n.key for n in mains])
        self.assertEqual([18000,54000],[int(n.get('Damage')) for n in mains])

    def test_all_other_nodes_and_order_are_preserved(self):
        before=[pilot.fingerprint(n) for n in self.current.children if n.key not in pilot.NONCHEMICAL]
        after=[pilot.fingerprint(n) for n in self.proposed.children if n.key not in pilot.NONCHEMICAL]
        self.assertEqual(before,after)

    def test_four_percentage_hits_remain_in_original_order(self):
        before=[pilot.fingerprint(n) for n in self.current.children if n.value=='AreaDamagePercentage']
        after=[pilot.fingerprint(n) for n in self.proposed.children if n.value=='AreaDamagePercentage']
        self.assertEqual(4,len(before))
        self.assertEqual(before,after)

    def test_ordinary_center_table_is_exact(self):
        before=[self.current.child(k) for k in pilot.NONCHEMICAL]
        after=[self.proposed.child(pilot.NONCHEMICAL[0])]
        for armor in self.armors:
            self.assertEqual(pilot.damage(before,armor,0),pilot.damage(after,armor,0),armor)

    def test_distinct_target_masks_cannot_be_hidden(self):
        before=[self.current.child(k) for k in pilot.NONCHEMICAL]
        after=[self.proposed.child(pilot.NONCHEMICAL[0])]
        expected=(38880,20880,20880,2880)
        for flags,value in zip(pilot.MASKS,expected):
            self.assertEqual(value,pilot.damage(before,'None',0,flags))
            self.assertEqual(38880,pilot.damage(after,'None',0,flags))

    def test_radius_response_is_not_separable(self):
        nodes=[self.current.child(k) for k in pilot.NONCHEMICAL]
        ratios=[Fraction(pilot.damage(nodes,a,350),pilot.damage(nodes,a,0)) for a in ('None','Heavy')]
        self.assertGreater(abs(ratios[0]-ratios[1]),Fraction(1,100))

    def test_fitted_geometry_includes_every_original_knot_and_is_monotone(self):
        self.assertEqual((0,800),(self.knots[0],self.knots[-1]))
        self.assertEqual((100,0),(self.curve[0],self.curve[-1]))
        self.assertTrue(all(a>=b for a,b in zip(self.curve,self.curve[1:])))
        for key in pilot.NONCHEMICAL:
            self.assertTrue(set(pilot.falloff_and_radii(self.current.child(key))[1]).issubset(self.knots))

    def test_standalone_miniyaml_round_trip(self):
        nodes=pilot.load(pilot.PILOT)
        self.assertEqual(1,len(nodes))
        self.assertEqual(pilot.fingerprint(self.proposed),pilot.fingerprint(nodes[0]))
        self.assertEqual(pilot.yaml_text(self.proposed),pilot.PILOT.read_text(encoding='utf-8'))

    def test_historical_grid_and_artifacts_reproduce_from_frozen_inputs(self):
        data=pilot.evidence(None,self.current,self.proposed,self.armors,self.knots,self.curve,
                            targets=self.targets,firepower=self.firepower)
        self.assertEqual(json.loads(json.dumps(data)),json.loads(pilot.DATA.read_text(encoding='utf-8')))
        self.assertEqual(pilot.report(data),pilot.REPORT.read_text(encoding='utf-8'))
        self.assertEqual('blocked: preservation checks fail',data['activation'])
        self.assertTrue(data['protected_nodes_unchanged'])
        self.assertEqual(4*len(self.armors)*801,sum(r['cases'] for r in data['comparison']))
        self.assertTrue(all(r['changed_cases']>0 for r in data['comparison']))

    def test_live_bulletchem_weapon_is_not_a_supported_historical_fit(self):
        with self.assertRaisesRegex(ValueError,'Historical four-profile'):
            pilot.fit(self.rules.resolve_weapon('HydraSpit'))


if __name__=='__main__':
    unittest.main()
