import copy
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/balance'))
import peer_corpus
import peer_nominal_evidence as nominal
import reference_distribution as rd


class NominalEvidenceTest(unittest.TestCase):
    def test_ground_batch_keeps_single_impacts_and_separate_ammunition_scope(self):
        profiles = nominal.load(ROOT)
        self.assertEqual(profiles['Combined Arms', 'LTUR']['dps'], 5500 / 34)
        pitbull = profiles['Combined Arms', 'PBUL']
        self.assertEqual(pitbull['burst_delays'], [4])
        self.assertEqual(pitbull['dps'], 14000 / 84)
        venom = profiles['Combined Arms', 'VENM']
        self.assertEqual(venom['dps'], 5500 / 30)
        self.assertIn('not sustained aircraft DPS', venom['scope'])

    def test_tomahawk_uses_spawned_impact_and_launcher_cadence(self):
        profile = nominal.load(ROOT)['Combined Arms', 'THWK']
        self.assertEqual(profile['weapon'], 'THWeapon')
        self.assertEqual(profile['damage'], 36000)
        self.assertEqual(profile['dps'], 144)
        self.assertLess(profile['delivery_path']['respawn_ticks'], profile['reload'])
        record = next(r for r in peer_corpus.load(ROOT)['Combined Arms'][1] if r['id'] == 'THWK')
        row = dict(record, source='Combined Arms')
        self.assertTrue(nominal.apply(row, record, {('Combined Arms', 'THWK'): profile}))
        self.assertEqual(row['weapon'], 'THWeapon')
        self.assertEqual(row['pre_nominal_weapon']['weapon'], 'THTargetter')

    def test_frontloaded_burst_uses_pre_attack_count_and_exact_integer_shots(self):
        p=nominal.load(ROOT)['Combined Arms','HFTK']
        self.assertEqual(p['shot_damage'],[1425]*10+[934]*15)
        self.assertEqual(p['firepower_modifiers_by_shot'],[125]*10+[82]*15)
        self.assertEqual(p['dps'],28260/128)
        self.assertAlmostEqual(p['damage'],1130.4)

    def test_expanded_base_models_keep_their_declared_weapon_mechanics(self):
        p=nominal.load(ROOT)
        flame=p['Combined Arms','BH']
        self.assertEqual(flame['burst'],28)
        self.assertEqual(flame['dps'],140)
        tesla=p['Combined Arms','TTRP']
        self.assertEqual(tesla['weapon'],'PortaTesla.UPG')
        self.assertEqual(tesla['dps'],5300/70.5)
        self.assertEqual(p['Combined Arms','N3C']['dps'],92)
        self.assertEqual(p['Combined Arms','RMBC']['dps'],260)

    def test_air_target_alternatives_are_not_double_counted(self):
        profile = nominal.load(ROOT)
        for ident, damage, rate in [('HELI', 3000, 12000 / 90),
                                    ('AGUN', 2500, 2500 / 8),
                                    ('SAM', 6750, 6750 / 20),
                                    ('NSAM', 6750, 6750 / 20),
                                    ('E3', 4000, 80), ('N3', 4000, 80)]:
            p = profile['Combined Arms', ident]
            scenario = p['target_scenario']
            tags = set(scenario['target_types'])
            matching = [h for h in scenario['warhead_alternatives']
                        if tags.intersection(h['valid_targets'])
                        and not tags.intersection(h['invalid_targets'])]
            self.assertEqual(len(matching), 1)
            self.assertEqual(p['damage'], damage)
            self.assertEqual(p['dps'], rate)
            self.assertEqual(p['damage_parts'][0]['warhead'], matching[0]['warhead'])
            self.assertIn('not sustained actor DPS', p['scope'])

    def test_exact_proof_is_required_and_original_verdict_survives(self):
        records = peer_corpus.load(ROOT)['OpenRA Tiberian Dawn'][1]
        record = next(r for r in records if r['id'] == 'MTNK')
        before = copy.deepcopy(record)
        row = dict(record, source='OpenRA Tiberian Dawn')
        self.assertFalse(nominal.apply(row, record, {}))
        self.assertIsNone(row['w_dps'])
        self.assertTrue(nominal.apply(row, record, nominal.load(ROOT)))
        self.assertEqual(row['w_dps'], 100)
        self.assertEqual(row['weapon_evidence_raw']['w_evidence'], 'incomplete')
        self.assertEqual(record, before)
        changed = dict(record, w_damage=5000)
        with self.assertRaises(ValueError):
            nominal.apply(row, changed, nominal.load(ROOT))

    def test_nominal_proof_does_not_enable_armor_or_complex_tank(self):
        rows = rd.peer_rows()
        tank = next(r for r in rows if (r['source'], r['id']) == ('OpenRA Tiberian Dawn', 'MTNK'))
        self.assertTrue(all(tank['dps_vs_' + ladder] is None for ladder in rd.LADDERS))
        base_tank = next(r for r in rows if (r['source'], r['id']) == ('Combined Arms', 'MTNK'))
        self.assertEqual(base_tank['w_dps'], 4600 / 55)
        self.assertEqual(base_tank['w_range'], 4864)
        self.assertEqual(len(base_tank['weapon_evidence']), 3)
        self.assertEqual(base_tank['weapon_evidence_raw']['w_evidence'], 'incomplete')
        complex_tank = next(r for r in rows if r['source'] == 'Combined Arms' and r['id'].casefold() == 'mtnk.laser')
        self.assertIsNone(complex_tank['w_dps'])

    def test_scheduled_beam_impacts_are_not_burst_shots(self):
        profile = nominal.load(ROOT)
        beam = profile['Combined Arms', 'PBOX']
        self.assertEqual(beam['damage_per_impact'], 1000)
        self.assertEqual(beam['impact_ticks'], [0, 2, 4, 6, 8, 10])
        self.assertEqual(beam['burst'], 1)
        self.assertEqual(beam['dps'], 6000 / 30)
        buggy = profile['Combined Arms', 'BGGY']
        self.assertEqual(buggy['dps'], 5000 / 50)

    def test_selected_weapon_scalars_replace_legacy_slot_together(self):
        profile = nominal.load(ROOT)
        record = next(r for r in peer_corpus.load(ROOT)['Combined Arms'][1] if r['id'] == '4TNK')
        row = dict(record, source='Combined Arms')
        original = copy.deepcopy(record)
        self.assertTrue(nominal.apply(row, record, profile))
        proof = profile['Combined Arms', '4TNK']
        self.assertEqual((row['weapon'], row['w_damage'], row['w_reload'], row['w_burst']),
                         (proof['weapon'], proof['damage'], proof['reload'], proof['burst']))
        self.assertEqual(row['pre_nominal_weapon']['w_damage'], original['w_damage'])
        self.assertNotIn('w_dps_raw', row)
        self.assertEqual(record, original)

    def test_mammoth_primary_does_not_sum_secondary_missiles(self):
        profile = nominal.load(ROOT)
        mammoth = profile['OpenRA Red Alert', '4TNK']
        self.assertEqual(mammoth['selected_slot'], 'Armament@PRIMARY')
        self.assertIn('Armament@SECONDARY', mammoth['other_slots'])
        self.assertEqual(mammoth['dps'], 12000 / 95)

    def test_burst_cycle_uses_source_delays(self):
        entry = nominal.load(ROOT)['Combined Arms', 'APC2']
        self.assertEqual(entry['burst'], 5)
        self.assertEqual(entry['burst_delays'], [3, 3, 3, 3])
        self.assertEqual(entry['dps'], 5000 / (38 + 12))

    def test_obelisk_charge_does_not_overlap_reload(self):
        profile = nominal.load(ROOT)
        td = profile['OpenRA Tiberian Dawn', 'OBLI']
        ca = profile['Combined Arms', 'OBLI']
        self.assertEqual(td['dps'], 36000 / 90)
        self.assertEqual(ca['dps'], 37500 / 145)
        self.assertEqual(td['charge_ticks'], 50)
        self.assertLess(td['dps'], td['damage'] / td['reload'])
        shok = profile['Combined Arms', 'SHOK']
        self.assertEqual(shok['charge_ticks_bounds'], [0, 1])
        self.assertEqual(shok['dps'], 5300 / 100.5)

    def test_same_target_delayed_warheads_sum_without_cosmetic_cluster(self):
        entry = nominal.load(ROOT)['Combined Arms', 'MLRS']
        self.assertEqual(entry['damage'], 12000)
        self.assertEqual([p['delay'] for p in entry['damage_parts']], [0, 3, 6, 9])
        self.assertEqual(entry['dps'], 24000 / 180)
        flame = nominal.load(ROOT)['Combined Arms', 'N4']
        self.assertEqual(flame['damage'], 10500)
        self.assertIn('centerline', flame['scope'])

    def test_garrison_slot_is_not_a_base_weapon_and_v2_uses_center_damage(self):
        profile = nominal.load(ROOT)
        rifle = profile['OpenRA Red Alert', 'E1']
        self.assertEqual(rifle['selected_slot'], 'Armament@PRIMARY')
        self.assertEqual(rifle['unbound_slots'], ['Armament@GARRISONED'])
        rows = rd.peer_rows()
        for source in ('Combined Arms', 'OpenRA Red Alert'):
            v2 = next(r for r in rows if (r['source'], r['id']) == (source, 'V2RL'))
            self.assertTrue(rd.eligible(v2, 'w_range'))
            proof = profile[source, 'V2RL']
            self.assertEqual(proof['damage'], proof['raw_weapon_damage'] * 10)
            self.assertEqual(v2['w_dps'], proof['damage'] / proof['reload'])


if __name__ == '__main__':
    unittest.main()
