"""Independent range evidence cannot silently re-enable withheld DPS."""
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/balance'))
import reference_distribution as rd
import peer_range_evidence as pe

class RangeEvidenceTest(unittest.TestCase):
    def test_only_explicit_range_proof_reopens_range(self):
        row={'w_range':5000,'w_dps':None,'w_evidence':'incomplete'}
        self.assertFalse(rd.eligible(row,'w_range'))
        row.update(w_range_usable=True,w_range_evidence=pe.VERDICT)
        self.assertTrue(rd.eligible(row,'w_range'))
        self.assertFalse(rd.eligible(row,'w_dps'))
        for value in ('True',False,None):
            row['w_range_usable']=value
            self.assertFalse(rd.eligible(row,'w_range'))
        row.update(w_range_usable=True,w_range_evidence='unknown')
        self.assertFalse(rd.eligible(row,'w_range'))

    def test_sniper_percentage_damage_does_not_block_independent_range(self):
        sniper=next(r for r in rd.peer_rows() if (r['source'],r['id'])==('Combined Arms','SNIP'))
        self.assertTrue(rd.eligible(sniper,'w_range'))
        self.assertFalse(rd.eligible(sniper,'w_dps'))
        self.assertEqual(sniper['w_range_evidence'],pe.SELECTED_VERDICT)

    def test_changed_source_row_refuses_saved_proof(self):
        record={'id':'UNIT','w_range':100,'w_dps':None}
        row=dict(record,source='Test')
        profile={('Test','UNIT'):{'range':100,'record_sha256':pe.fingerprint(record)}}
        pe.apply(row,record,profile)
        self.assertTrue(row['w_range_usable'])
        for changed in (dict(record,w_range=101),dict(record,w_dps=1)):
            with self.assertRaises(ValueError):pe.apply(row,changed,profile)

    def test_current_tank_has_separately_reviewed_nominal_dps(self):
        rows=rd.peer_rows()
        tank=next(r for r in rows if r['source']=='OpenRA Tiberian Dawn' and r['id']=='MTNK')
        self.assertEqual(tank['w_range'],4864)
        self.assertTrue(rd.eligible(tank,'w_range'))
        self.assertEqual(tank['w_dps'],100)
        self.assertEqual(tank['weapon_evidence_raw']['w_evidence'],'incomplete')
        self.assertEqual(tank['provenance']['factory_state_certification'],'none')
