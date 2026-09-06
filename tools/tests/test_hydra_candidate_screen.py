"""Bounded worksheet tests; no full inventory or large comparison snapshots."""
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/balance'))
import hydra_candidate_screen as screen


class HydraScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules=screen.Ruleset(ROOT)
        cls.hydra=cls.rules.resolve_weapon('HydraSpit')

    def test_current_nominal_none_and_duplicate_corrosion(self):
        self.assertEqual((51480,135,25200),screen.nominal(self.hydra,'None',30000))

    def test_staged_candidate_has_reported_large_increase(self):
        self.assertEqual((137520,1296,27504),screen.nominal(screen.candidate(72000,10000),'None',30000))

    def test_infantry_anchor_preserves_flak_only_approximately(self):
        self.assertEqual((51150,184,10230),screen.nominal(screen.candidate(33000,2098),'Flak',41000))

    def test_real_wraith_is_not_fighter_armor(self):
        self.assertEqual('Helicopter',self.rules.resolve('terran_wraith').get('Armor','Type'))

    def test_candidate_radius_does_not_preserve_old_splash(self):
        node=screen.candidate(33000,2098).children[0]
        fo,radii,_=screen.falloff_and_radii(node)
        self.assertEqual(220,radii[-1])
        self.assertEqual(0,screen.runtime_falloff(fo,radii,220))

    def test_candidate_creation_never_mutates_current_weapon(self):
        screen.candidate(33000,2098)
        mains=[n for n in self.hydra.children if n.value in ('AreaDamage','SpreadDamage')]
        self.assertEqual([18000]*4,[int(n.get('Damage')) for n in mains])


if __name__=='__main__':
    unittest.main()
