import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/balance'))
import peer_base_state as state
import peer_corpus
import reference_distribution as rd
import reference_targets as rt

class BaseState(unittest.TestCase):
    def test_upgrade_chassis_remains_visible_but_never_votes(self):
        rows=rd.peer_rows()
        laser=next(r for r in rows if (r['source'],r['id'])==('Combined Arms','MTNK.Laser'))
        self.assertGreater(laser['hp'],0)
        for stat in ('hp','cost','speed','w_range','w_dps'):
            self.assertFalse(rd.eligible(laser,stat),stat)
        base=next(r for r in rows if (r['source'],r['id'])==('Combined Arms','MTNK'))
        self.assertTrue(rd.eligible(base,'hp'))
        self.assertTrue(rd.eligible(base,'w_dps'))
        dist=rd.build_distributions(rows);rt.add_cost_distribution(dist,rows)
        c=rd.cameo_rows()[0]
        self.assertEqual(rt.target_for([laser],c,'hp',dist,rt.cameo_context()),(None,None,0))

    def test_unlocking_a_distinct_unit_is_not_a_variant_upgrade(self):
        profile=state.load(ROOT)
        self.assertNotIn(('Combined Arms','BJET'),profile)
        self.assertNotIn(('Combined Arms','APOC'),profile)
        self.assertIn(('Combined Arms','APOC.ATOMIC'),profile)

    def test_changed_source_cannot_reuse_exclusion_proof(self):
        record=next(r for r in peer_corpus.load(ROOT)['Combined Arms'][1] if r['id']=='MTNK.Laser')
        changed=dict(record,hp=1)
        with self.assertRaises(ValueError):
            state.apply(dict(changed,source='Combined Arms'),changed,state.load(ROOT))

if __name__=='__main__':unittest.main()
