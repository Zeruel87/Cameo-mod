"""Resolved regressions for Aedis's ground/air damage policy, 2026-09-10."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'audit'))
from miniyaml import Ruleset


class TargetPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_future_tank_damage_and_emp_exclude_air_in_both_ranks(self):
        for name in ('FutureTankCannons', 'FutureTankCannons_elite'):
            weapon = self.rules.resolve_weapon(name)
            fields = {c.key: c.value for c in weapon.children}
            self.assertEqual(fields['ValidTargets'], 'Ground, Water')
            for warhead in weapon.children:
                if warhead.value not in ('AreaDamage', 'SpreadDamage',
                                         'AreaDamagePercentage', 'AffectsIntegrity'):
                    continue
                values = {c.key: c.value for c in warhead.children}
                allowed = values.get('ValidTargets', 'Ground, Water').split(', ')
                excluded = values.get('InvalidTargets', '').split(', ')
                self.assertTrue('Air' not in allowed or 'Air' in excluded,
                                (name, warhead.key))

    def test_gunboat_full_flat_and_percentage_payload_admits_air(self):
        for name in ('AAGunBoatFlak', 'AAGunBoatFlak_elite'):
            flat = 0
            for warhead in self.rules.resolve_weapon(name).children:
                if warhead.value not in ('AreaDamage', 'SpreadDamage', 'AreaDamagePercentage'):
                    continue
                fields = {c.key: c.value for c in warhead.children}
                self.assertIn('Air', fields.get('ValidTargets', '').split(', '), warhead.key)
                if warhead.value != 'AreaDamagePercentage':
                    flat += int(fields.get('Damage', '0'))
            self.assertEqual(flat, 8000)

    def test_td_dual_weapons_deliver_equal_base_payload_to_air_and_surface(self):
        for name, expected_flat in (
                ('td_nod_reconbike_rocket', 16000),
                ('td_gdi_empgrenadier_grenade_emp', 72000),
                ('td_gdi_empgrenadier_grenadeexplode_emp', 40000)):
            weapon = self.rules.resolve_weapon(name)
            payloads = {}
            for domain in ('Ground', 'Water', 'Air'):
                payload = []
                for warhead in weapon.children:
                    if warhead.value not in ('AreaDamage', 'SpreadDamage', 'AreaDamagePercentage'):
                        continue
                    allowed = set((warhead.get('ValidTargets') or 'Ground, Water').split(', '))
                    excluded = set((warhead.get('InvalidTargets') or '').split(', '))
                    if domain in allowed - excluded:
                        payload.append((warhead.key, warhead.value, int(warhead.get('Damage') or '0')))
                payloads[domain] = payload
            self.assertEqual(payloads['Air'], payloads['Ground'], name)
            self.assertEqual(payloads['Air'], payloads['Water'], name)
            self.assertEqual(sum(damage for _, kind, damage in payloads['Air']
                                 if kind != 'AreaDamagePercentage'), expected_flat, name)

    def test_devourer_cloud_keeps_damage_but_excludes_surface_targets(self):
        from dump_resolved import node_to_obj
        parent = self.rules.resolve_weapon('AnthraxCloudPurpleLarge')
        cloud = self.rules.resolve_weapon('sc_zerg_devourer_acidcloud_aa')
        self.assertEqual(self.rules.resolve_weapon('SCDevourerAA').get(
            'Warhead@Cloud', 'Weapon'), cloud.key)
        self.assertEqual(cloud.get('ValidTargets'), 'Air')
        self.assertEqual(cloud.get('Warhead@Toxic_Light', 'ValidTargets'), 'Air')
        expected = node_to_obj(parent)
        expected['ValidTargets'] = 'Air'
        expected['Warhead@Toxic_Light']['ValidTargets'] = 'Air'
        self.assertEqual(expected, node_to_obj(cloud))

    def test_soviet_tesla_secondary_routes_obey_root_target_policy(self):
        from target_payload_routes import DAMAGE, target_tags
        for stem in ('ra1_soviets_volkov_volkovmagneticweapontesla',
                     'ra1_soviets_volkov_volkovmagneticweaponincendiarytesla'):
            for suffix in ('', 'fragment1', 'fragment2'):
                name = stem + suffix
                weapon = self.rules.resolve_weapon(name)
                allowed, excluded = target_tags(weapon)
                self.assertNotIn('Air', allowed - excluded, name)
                self.assertIn('wall', excluded, name)
                for warhead in weapon.children:
                    if warhead.value in DAMAGE:
                        allowed, excluded = target_tags(warhead)
                        self.assertNotIn('Air', allowed - excluded, (name, warhead.key))
        dual_names = ['ra1_soviets_teslayak_yaktesla' + suffix
                      for suffix in ('gun', 'gunarc', 'arcfragment1', 'arcfragment2')]
        dual_names += ['ra1_soviets_kamovattackhelicopter_kamovtesla' + suffix
                       for suffix in ('', 'arc', 'arcfragment1', 'arcfragment2')]
        dual_names += ['ra1_soviets_migattackbomber_teslamaverick' + suffix
                       for suffix in ('', 'fragment1', 'fragment2')]
        for name in dual_names:
            weapon = self.rules.resolve_weapon(name)
            for node in [weapon] + [c for c in weapon.children if c.value in DAMAGE]:
                allowed, excluded = target_tags(node)
                self.assertTrue({'Ground', 'Water', 'Air'} <= allowed - excluded,
                                (name, node.key))

    def test_ground_tesla_roots_use_surface_only_copies_of_shared_fragments(self):
        from target_payload_routes import DAMAGE, target_tags
        from dump_resolved import node_to_obj
        prefix = 'MammothTuskTeslaFragment'
        for name in ('ra1_soviets_teslayak_tesla_bomb',):
            root = self.rules.resolve_weapon(name)
            self.assertNotIn('Air', target_tags(root)[0])
            self.assertEqual(root.get('Warhead@TeslaArc', 'Weapon'),
                             prefix + '1Ground_ExplicitDamage1of4')
        for number in ('1', '2'):
            parent = self.rules.resolve_weapon('MammothTuskTeslaFragment' + number)
            copy = self.rules.resolve_weapon(prefix + number + 'Ground')
            expected = node_to_obj(parent)
            expected['ValidTargets'] = 'Ground, Water'
            for warhead in parent.children:
                if warhead.value in DAMAGE:
                    allowed, excluded = target_tags(warhead)
                    self.assertIn('Air', allowed - excluded, warhead.key)
                    expected[warhead.key]['InvalidTargets'] = (
                        'Shielded, Air' if warhead.key == 'Warhead@EMPUnit' else 'Air')
                    self.assertIn('Air', target_tags(copy.child(warhead.key))[1])
            if number == '1':
                expected['Warhead@TeslaArc']['Weapon'] = prefix + '2Ground'
                expected['Warhead@TeslaArc']['ValidTargets'] = 'Ground, Water'
            self.assertEqual(expected, node_to_obj(copy))

    def test_reviewed_shrapnel_emitters_match_firing_parent(self):
        import json
        from target_payload_routes import target_tags
        fixture = pathlib.Path(__file__).parent / 'fixtures/pilot_shrapnel_routes_20260911.json'
        routes = json.loads(fixture.read_text())['routes']
        for name, tag, fragment in routes:
            parent = self.rules.resolve_weapon(name)
            emitter = parent.child(tag)
            self.assertEqual(emitter.value, 'FireShrapnel', (name, tag))
            self.assertEqual(emitter.get('Weapon'), fragment, (name, tag))
            self.assertEqual(target_tags(parent), target_tags(emitter), (name, tag))
            child = self.rules.resolve_weapon(fragment)
            self.assertEqual(target_tags(parent), target_tags(child), (name, fragment))

    def test_exclusive_surface_fragments_preserve_payloads_and_exclude_air(self):
        from reviewed_weapon_history import secondary_target_policy_changes, restore_secondary_target_policy
        from dump_resolved import node_to_obj
        records = secondary_target_policy_changes()
        self.assertEqual(set(records), {'ObeliskLaserFragment', 'TurretLaserFragment', 'NanoSmokeAG'})
        for name, record in records.items():
            live = self.rules.resolve_weapon(name)
            before = restore_secondary_target_policy(self, live)
            expected = node_to_obj(before)
            for tag, key, old, value in record['fields']:
                current = live.child(tag) if tag else live
                self.assertIn('Air', current.get(key).split(', '))
                (expected[tag] if tag else expected)[key] = value
            self.assertEqual(expected, node_to_obj(live), name)
        altered = self.rules.resolve_weapon('NanoSmokeAG').deep_copy()
        altered.child('ReloadDelay').value = '999'
        with self.assertRaises(AssertionError):
            restore_secondary_target_policy(self, altered)

    def test_ground_only_td_leaf_weapons_exclude_air_damage_and_status(self):
        names = ('td_gdi_guardtower_highvap', 'td_gdi_havoc_grenade',
                 'td_gdi_minigunner_minigun', 'td_gdi_minigunner_minigun_ap',
                 'td_gdi_shotgunner_shotgun', 'td_nod_laserturret_laser',
                 'td_nod_minigunner_minigun', 'td_nod_minigunner_minigun_laser',
                 'td_nod_obeliskoflight_laserobeliskburning')
        for name in names:
            weapon = self.rules.resolve_weapon(name)
            self.assertNotIn('Air', {c.key: c.value for c in weapon.children}
                             .get('ValidTargets', 'Ground').split(', '))
            for warhead in weapon.children:
                if warhead.value in ('AreaDamage', 'SpreadDamage', 'AreaDamagePercentage',
                                     'AffectsIntegrity', 'GrantExternalCondition'):
                    fields = {c.key: c.value for c in warhead.children}
                    self.assertIn('Air', fields.get('InvalidTargets', '').split(', '),
                                  (name, warhead.key))

    def test_gunboat_has_one_aa_ship_range_bonus_without_unconditional_firepower(self):
        actor = self.rules.resolve('gunb.asian')
        traits = {c.key: c for c in actor.children}
        self.assertNotIn('TooltipExtras@ScoutShip', traits)
        self.assertEqual({c.key: c.value for c in traits['RangeMultiplier@AntiAirShip'].children}
                         ['Modifier'], '150')
        # Aedis's later 00:18 ruling removes unconditional combat multipliers.
        self.assertNotIn('FirepowerMultiplier@ScoutShip', traits)

    def test_dual_target_missiles_use_ap_with_preserved_flat_totals(self):
        for name, total in (('227mm', 8000), ('RocketsRA', 20000), ('MammothTusk', 24000),
                            ('td_gdi_mlrs_227mmamt', 8000), ('MammothTuskGal', 24000),
                            ('MammothTuskTargetingComputer', 24000)):
            warheads = [c for c in self.rules.resolve_weapon(name).children
                        if c.value == 'AreaDamage']
            self.assertEqual(len(warheads), 1, name)
            self.assertIn('MissileAP', warheads[0].key)
            self.assertEqual({c.key: c.value for c in warheads[0].children}['Damage'], str(total))

    def test_rapier_dual_target_secondary_uses_ap_and_preserves_damage(self):
        weapon = self.rules.resolve_weapon('ra1_allies_rapierjumpjet_missile_AA')
        damage = [child for child in weapon.children if child.value == 'AreaDamage']
        ap = [child for child in damage if 'MissileAP' in child.key]
        self.assertEqual(len(ap), 1)
        self.assertEqual(ap[0].get('Damage'), '4000')
        self.assertEqual(sum(int(child.get('Damage') or '0') for child in damage), 8000)
        self.assertTrue(all('Air' in (child.get('ValidTargets') or '').split(', ')
                            for child in damage))

    def test_havoc_retains_existing_air_capability_pending_role_decision(self):
        for name in ('td_gdi_havoc_sniper', 'td_gdi_havoc_rifle'):
            weapon = self.rules.resolve_weapon(name)
            self.assertIn('Air', (weapon.get('ValidTargets') or '').split(', '))
            self.assertNotIn('Air', (weapon.get(
                'Warhead@ChaingunPercentage', 'InvalidTargets') or '').split(', '))
        rifle = self.rules.resolve_weapon('td_gdi_havoc_rifle')
        self.assertEqual(rifle.get('Warhead@Bullet_Medium', 'Damage'), '8000')
        self.assertIn('Air', rifle.get('Warhead@Bullet_Medium', 'ValidTargets').split(', '))
        rocket = self.rules.resolve_weapon('td_gdi_havoc_rocket')
        self.assertIn('Air', (rocket.get('ValidTargets') or '').split(', '))

    def test_annihilator_air_only_child_has_its_own_aa_payload(self):
        weapon = self.rules.resolve_weapon('D2K_Annihilator_AA')
        self.assertEqual({c.key: c.value for c in weapon.children}['ValidTargets'], 'Air')
        warheads = [c for c in weapon.children if c.value == 'AreaDamage']
        self.assertEqual([c.key for c in warheads], ['Warhead@MissileAA_Heavy'])
        fields = {c.key: c.value for c in warheads[0].children}
        self.assertEqual(fields['Damage'], '28500')
        self.assertEqual(fields['ValidTargets'], 'Air')

    def test_direct_single_domain_weapons_keep_damage_in_their_domain(self):
        bound = set()
        for name in self.rules.actors:
            if name.startswith('^'):
                continue
            for trait in self.rules.resolve(name).children:
                if trait.key.startswith('Armament'):
                    bound.update(c.value for c in trait.children if c.key == 'Weapon')
        checked = 0
        for name in sorted(bound):
            weapon = self.rules.resolve_weapon(name)
            if weapon is None:
                continue
            fields = {c.key: c.value for c in weapon.children}
            targets = set(fields.get('ValidTargets', 'Ground').split(', '))
            if targets == {'Air'}:
                for warhead in weapon.children:
                    if warhead.value in ('AreaDamage', 'SpreadDamage',
                                         'AreaDamagePercentage', 'AffectsIntegrity'):
                        self.assertEqual(warhead.get('ValidTargets'), 'Air',
                                         (name, warhead.key))
                continue
            if not targets.issubset({'Ground', 'Water'}):
                continue
            checked += 1
            for warhead in weapon.children:
                if warhead.value not in ('AreaDamage', 'SpreadDamage',
                                         'AreaDamagePercentage', 'AffectsIntegrity'):
                    continue
                values = {c.key: c.value for c in warhead.children}
                if 'Air' in values.get('ValidTargets', '').split(', '):
                    self.assertIn('Air', values.get('InvalidTargets', '').split(', '),
                                  (name, warhead.key))
        self.assertGreater(checked, 100)


if __name__ == '__main__':
    unittest.main()
