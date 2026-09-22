from fractions import Fraction
import pathlib,sys,unittest
sys.path[:0]=[str(pathlib.Path(__file__).resolve().parents[1]/'audit'),str(pathlib.Path(__file__).resolve().parents[1]/'balance')]
from miniyaml import Node
import firepower_bake as bake
from percentage_damage import folded_units

def wh(kind,damage,**fields):
    return Node('Warhead@main',kind,[Node('Damage',str(damage))]+[Node(k,str(v)) for k,v in fields.items()])

class FirepowerBakeTests(unittest.TestCase):
    def test_half_flat_damage(self):
        self.assertEqual(bake.plan_channel(wh('AreaDamage',8000),Fraction(1,2))['fields'],{'Damage':'4000'})
    def test_percentage_half_does_not_round_one_percent_to_zero(self):
        p=bake.plan_channel(wh('AreaDamagePercentage',1),Fraction(1,2))['fields']
        self.assertEqual(Fraction(int(p['Damage']),int(p['PercentageDenominator'])),Fraction(1,200))
    def test_folded_fraction_keeps_exact_old_runtime_coefficient(self):
        w=wh('AreaDamage',11000,PercentageScale=3333)
        p=bake.plan_channel(w,Fraction(1,4),allow_off_grid=True)['fields']
        units=folded_units(int(p['Damage']),int(p.get('PercentageScale',3333)))[1]
        self.assertEqual(Fraction(units,int(p.get('PercentageDenominator',10000))),Fraction(folded_units(11000,3333)[1],40000))
    def test_ignored_custom_damage_is_not_scaled(self):
        for kind in ['DamagesConcrete','AffectsIntegrity']:
            self.assertEqual(bake.plan_channel(wh(kind,1000),Fraction(1,4))['fields'],{})
    def test_one_point_grid_accepts_integers_and_rejects_fractions(self):
        self.assertEqual(bake.plan_channel(wh('AreaDamage',1020),Fraction(1,4))['fields']['Damage'],'255')
        with self.assertRaises(ValueError):bake.plan_channel(wh('AreaDamage',1021),Fraction(1,4))
        self.assertEqual(bake.plan_channel(wh('AreaDamage',2000),Fraction(6,25),allow_off_grid=True)['fields']['Damage'],'480')
    def test_fractional_flat_requires_explicit_rounding(self):
        with self.assertRaises(ValueError):bake.plan_channel(wh('AreaDamage',120250),Fraction(21,20),allow_off_grid=True)
        p=bake.plan_channel(wh('AreaDamage',120250),Fraction(21,20),allow_off_grid=True,allow_rounding=True)
        self.assertEqual(p['fields']['Damage'],'126263')
        self.assertEqual(p['flat_rounding_error'],'1/2')
        rounded=bake.plan_channel(wh('AreaDamage',120250),Fraction(21,20),allow_rounding=True)
        self.assertEqual(rounded['fields']['Damage'],'126263')
        self.assertEqual(rounded['flat_rounding_error'],'1/2')
