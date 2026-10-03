import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/balance'))
import reference_distribution as rd
class IniRange(unittest.TestCase):
    def test_flame_tank_range_is_separate_from_reviewed_cycle_damage(self):
        r=next(r for r in rd.ini_rows() if r['source']=='DTA Enhanced' and r['id']=='FTNK')
        self.assertGreater(r['w_range'],0)
        self.assertTrue(rd.eligible(r,'w_range'))
        self.assertEqual(r['pre_cycle_evidence']['w_evidence'], 'incomplete')
        self.assertIn('w_cycle_evidence', r)
        self.assertTrue(rd.eligible(r,'w_dps'))
    def test_selected_medium_tank_uses_cannon_not_dummy_range(self):
        r=next(r for r in rd.ini_rows() if r['source']=='DTA Enhanced' and r['id']=='MTNK')
        self.assertEqual(r['weapon'],'90mm')
        self.assertEqual(r['w_range'],5.7)
        self.assertTrue(rd.eligible(r,'w_range'))
if __name__=='__main__':unittest.main()
