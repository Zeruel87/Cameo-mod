import pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'balance'))
import reference_distribution as rd,reference_targets as rt

class FrozenCameoTest(unittest.TestCase):
 def test_live_mutation_cannot_move_vote_or_ruler(self):
  frozen=[{'id':'a','type':'vehicle','hp':100},{'id':'b','type':'vehicle','hp':200},{'id':'c','type':'vehicle','hp':300}]
  peers=[dict(row,source='Peer') for row in frozen]
  peer_dist=rd.build_distributions(peers)
  ruler=rd.build_distributions([dict(row,source='Cameo') for row in frozen])['Cameo']
  context=rt.FrozenCameoDistribution(ruler,frozen)
  before=rt.target_for([peers[0]],frozen[0],'hp',peer_dist,context)
  after=rt.target_for([peers[0]],dict(frozen[0],hp=999999,type='aircraft'),'hp',peer_dist,context)
  self.assertEqual(before,after)
  newcomer=rt.target_for([peers[0]],{'id':'new','hp':999999,'type':'vehicle'},'hp',peer_dist,context)
  self.assertEqual(newcomer[0],newcomer[1])

 def test_snapshot_corruption_is_not_silently_live(self):
  with patch.object(pathlib.Path,'read_bytes',return_value=b'changed'):
   with self.assertRaises(ValueError):rt.cameo_context()

 def test_frozen_population_loaded(self):
  self.assertEqual(len(rt.cameo_context().cameo_votes),893)

 def test_the_frozen_ruler_is_never_multiplied_by_burst_a_second_time(self):
  """⛔ THE RULER DOUBLE-COUNT. Maintainer, 2026-09-13: the GDI grenadier's damage target
  moved 22k -> 38k although all three of its references are Burst 1 and nothing about it
  changed. It was the RULER: `to_per_cycle` multiplied every Burst > 1 row by its burst, and
  `cameo_context()` feeds it the frozen snapshot, which ALREADY stores the burst total. 245 of
  893 rows were squared-up — the mammoth 32,000 -> 64,000, the MLRS 48,000 -> 288,000 — which
  lifted the distribution every damage target is projected onto. All 243 mapped actors inflated,
  median 2.01x, worst 8.31x, including the 153 whose own weapon has no burst at all."""
  frozen=rt.cameo_context().cameo_votes
  self.assertEqual(frozen['td_gdi_mammothtank']['w_damage'],32000.0)   # yaml 16000 x Burst 2
  self.assertEqual(frozen['td_gdi_mlrs']['w_damage'],48000.0)          # yaml  8000 x Burst 6
  self.assertEqual(rt.damage_per_shot(frozen['td_gdi_mammothtank']),16000.0)
  self.assertEqual(rt.damage_per_shot(frozen['td_gdi_mlrs']),8000.0)

 def test_a_peer_row_is_still_multiplied_and_a_cameo_row_is_not(self):
  """The guard is the SOURCE, and it has to cut exactly one way: peers publish damage per SHOT
  and must be raised to a cycle; Cameo publishes the cycle and must be left alone."""
  rows=rd.to_per_cycle([{'id':'p','source':'Peer','w_damage':4000.0,'w_burst':4},
                        {'id':'c','source':'Cameo','w_damage':4000.0,'w_burst':4}])
  by={r['id']:r for r in rows}
  self.assertEqual(by['p']['w_damage'],16000.0)
  self.assertEqual(by['p']['w_damage_per_shot'],4000.0)
  self.assertEqual(by['c']['w_damage'],4000.0)
  self.assertEqual(by['c']['w_damage_per_shot'],1000.0)
