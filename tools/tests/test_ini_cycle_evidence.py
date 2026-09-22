import pathlib,sys,unittest,json
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/balance'))
import reference_distribution as rd
import ini_cycle_evidence as cycle
class Cycle(unittest.TestCase):
    def test_mammoth_explicit_delay_and_jitter(self):
        rows=rd.ini_rows()
        r=next(r for r in rows if (r['source'],r['id'])==('DTA Enhanced','4TNK'))
        self.assertEqual(r['w_dps'],88/86)
        proof=r['w_cycle_evidence']
        self.assertEqual((proof['cycle_min'],proof['cycle_max']),(85,87))
        self.assertEqual(proof['burst_delays'][0]['raw'],'5')
        self.assertTrue(rd.eligible(r,'w_dps'))
        self.assertTrue(all(r['dps_vs_'+ladder] is None for ladder in rd.LADDERS))
    def test_zero_authored_delay_preserves_raw_and_uses_tick_floor(self):
        p=cycle.load(ROOT)['DTA Enhanced','3TNK']
        zero=next(d for d in p['burst_delays'] if d['raw']=='0')
        self.assertEqual(zero['mean'],1)
        self.assertIn('scheduler_floor',zero)

    def test_tesla_ammo_cycle_does_not_relabel_authored_weapon_burst(self):
        p=cycle.load(ROOT)['DTA Enhanced','RATSLA']
        self.assertEqual(p['burst'],1)
        self.assertEqual(p['cycle_shots'],3)
        self.assertEqual(p['cycle_mean'],173)
        self.assertEqual(p['dps'],300/173)
        self.assertEqual(p['ammo_charge_proof']['trace_first_shots'],[0,1,2,173,174,175,346,347,348])
        self.assertEqual(p['charge_ticks'],51)
        self.assertIn('Particle lifetime gates',p['scope'])
    def test_cosmetic_particle_branch_uses_rof_after_every_emission(self):
        profile=cycle.load(ROOT)
        mlrs=profile['DTA Enhanced','MLRS']
        self.assertEqual(mlrs['burst'],2)
        self.assertEqual(mlrs['cycle_mean'],800)
        self.assertEqual(mlrs['dps'],100/400)
        self.assertEqual(mlrs['post_burst_jitter']['mean'],0)
        tank=profile['DTA Enhanced','FTNK']
        self.assertEqual(tank['particle_proof']['system_definition']['BehavesLike'],'Smoke')
        self.assertEqual(tank['dps'],118/50)
    def test_naval_units_and_unlimited_ammo_defenses_use_burst_model(self):
        profile=cycle.load(ROOT)
        self.assertEqual(profile['DTA Enhanced','CRUISER']['dps'],96/166)
        self.assertEqual(profile['DTA Enhanced','ATWR']['dps'],60/50)
        self.assertEqual(profile['DTA Enhanced','SAM']['dps'],80/100)
        self.assertEqual(profile['DTA Enhanced','APACHE']['dps'],50/15)
    def test_aircraft_nominal_timers_exclude_mission_cycle_and_include_jitter(self):
        profile=cycle.load(ROOT)
        for ident,rate in [('APACHE',50/15),('MIG',72/12),('YAK',60/8),('ORCA',34/9)]:
            p=profile['DTA Enhanced',ident]
            self.assertEqual(p['dps'],rate)
            self.assertFalse(p['aircraft_ammo_proof']['normal_emission_decrements_ammo'])
            self.assertFalse(p['aircraft_ammo_proof']['mission_cycle_included'])
            self.assertEqual(p['post_burst_jitter']['mean'],1)
    def test_charged_building_includes_animation_and_correlated_poll(self):
        p=cycle.load(ROOT)['DTA Enhanced','OBLI']
        self.assertEqual(p['charge_ticks'],72)
        self.assertEqual(p['ammo_charge_proof']['cycle_ticks_by_jitter'],[163,165,165])
        self.assertEqual((p['cycle_min'],p['cycle_max']),(163,165))
        self.assertEqual(p['dps'],220/p['cycle_mean'])
        self.assertLess(p['dps'],220/90)
    def test_changed_source_is_not_reused(self):
        raw=next(json.loads(line) for line in (ROOT/'docs/reference/ini_corpus.json').read_text().splitlines() if json.loads(line).get('source')=='DTA Enhanced' and json.loads(line).get('id')=='4TNK')
        raw['w_damage']=1
        with self.assertRaises(ValueError):cycle.apply(dict(raw),raw,cycle.load(ROOT))
if __name__=='__main__':unittest.main()
