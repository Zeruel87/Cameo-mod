import pathlib,sys,unittest,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/balance'))
import reference_targets as rt
import reference_distribution as rd
import propose_anchor_spec as spec
class HeroReference(unittest.TestCase):
    def test_hero_snapshot_is_separate_and_matches_original_inputs(self):
        ordinary=rt.cameo_context();hero=rt.hero_cameo_context()
        self.assertEqual(len(ordinary.cameo_votes),893)
        self.assertEqual(len(hero.cameo_votes),83)
        self.assertTrue(set(ordinary.cameo_votes).isdisjoint(hero.cameo_votes))
        doc=json.loads((ROOT/'docs/reference/cameo_baselines/pre_reference_heroes_20260910.json').read_text())
        parent=json.loads((ROOT/'docs/reference/cameo_baselines/pre_reference_20260910.json').read_text())
        self.assertTrue(all(parent['inputs'][k]==v for k,v in doc['inputs'].items()))
    def test_behemoth_cycle_stays_in_hero_lane(self):
        heroes=rd.peer_hero_rows()
        r=next(r for r in heroes if (r['source'],r['id'])==('DTA Enhanced','BEHEMOTH'))
        self.assertTrue(rd.eligible(r,'w_dps'))
        self.assertFalse(any((r['source'],r['id'])==('DTA Enhanced','BEHEMOTH') for r in rd.peer_rows()))

    def test_tanya_gets_hero_projections_without_ordinary_fallback(self):
        assignment=json.loads((ROOT/'docs/balance/derived/reference_assignment.json').read_text())['assignment']
        result=spec.hero_reference_evidence([{'actor':'ra1_allies_tanya'}],assignment)['ra1_allies_tanya']
        self.assertEqual(result['lane'],'frozen hero-only')
        self.assertEqual(result['targets']['hp']['sources'],3)
        self.assertGreater(result['targets']['hp']['value'],0)
if __name__=='__main__':unittest.main()
