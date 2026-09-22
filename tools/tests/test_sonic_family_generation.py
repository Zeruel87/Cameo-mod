"""Contracts for the delivery-specific Sonic family candidate (not live YAML)."""
import sys
import unittest

import _bootstrap

sys.path.insert(0, str(_bootstrap.REPO_ROOT / 'tools' / 'balance'))
import gen_weapon_template as gen
from miniyaml import load_text
import preview_sonic_additions as scoped
import shield_uniqueness as shield


class SonicFamilyGenerationTest(unittest.TestCase):
    def test_scoped_additions_reserve_live_shields_and_restore_generator_state(self):
        live = (_bootstrap.REPO_ROOT / 'mods/cameo/weapons/weapons.yaml').read_text(encoding='utf-8')
        before = list(gen.BLEND_FAMILIES.items())
        result = scoped.generate(live)
        self.assertEqual(before, list(gen.BLEND_FAMILIES.items()))
        added = shield.find_main_shields(result.splitlines())
        reserved = {v for _, family, _, v in shield.find_main_shields(live.splitlines())
                    if family not in scoped.FAMILIES}
        values = [v for *_, v in added]
        self.assertEqual(len(added), 12)
        self.assertEqual(len(set(values)), 12)
        self.assertFalse(set(values) & reserved)
        self.assertTrue(all(100 <= value <= 400 for value in values))
        for family in scoped.FAMILIES:
            rows = sorted((shield.LEVEL_RANK[level], value)
                          for _, name, level, value in added if name == family)
            self.assertEqual([v for _, v in rows], sorted(v for _, v in rows))

    def test_flat_sonic_parent_has_no_invented_armor_order(self):
        for level in gen.L3:
            main, pct = gen._family_main_pct('Sonic', level)
            self.assertEqual(set(main), gen.CANON16 | {'Shield'})
            self.assertEqual(set(main.values()), {gen.FLAT_VALUES[level]})
            self.assertEqual(set(pct.values()), {gen.FLAT_PCT[level]})

    def test_delivery_identity_status_and_shapes_survive_generation(self):
        for name, delivery in [('BulletSonic', 'Bullet'),
                               ('MissileSonic', 'MissileAP'),
                               ('CannonSonic', 'CannonHE')]:
            with self.subTest(family=name):
                parents, states, levels = gen.BLEND_FAMILIES[name]
                self.assertEqual(parents, [delivery, 'Sonic'])
                self.assertEqual(gen.PHYSICS_RANK[name],
                                 (gen.PHYSICS_RANK[delivery] + gen.PHYSICS_RANK['Sonic']) / 2)
                spreads, falloffs = gen.shape_for(name)
                vt = gen.valid_targets(gen.WEAPONS[delivery][2])
                nodes = load_text(gen.family(name, None, vt, levels,
                    versus_override=gen.blend_versus(parents), physical_states=states,
                    spreads=spreads, falloffs=falloffs))
                self.assertEqual(len(nodes), 3)
                for node, level in zip(nodes, levels):
                    main = node.child('Warhead@' + name + '_' + level)
                    status = node.child('Warhead@' + name + '_' + level + '_Debuff')
                    self.assertIsNotNone(main)
                    self.assertIsNotNone(status)
                    self.assertEqual(status.get('Condition'), 'SonicDebuff')
                    self.assertEqual(status.get('Duration'), '50')
                    self.assertEqual(int(status.get('Range')), int(main.get('Spread')) * 2)
                    self.assertEqual(main.get('ValidTargets'), vt)
                    self.assertIsNone(main.child('PhysicalStates'))
                    direction = gen.WEAPONS[delivery][1]
                    none, heavy = (int(main.get('Versus', armor)) for armor in ('None', 'Superheavy'))
                    self.assertGreater(heavy, none) if direction == 'heavy' else self.assertGreater(none, heavy)

    def test_grenade_uses_authorized_three_way_blast(self):
        parents, states, levels = gen.BLEND_FAMILIES['BlastSonic']
        self.assertEqual(parents, ['Demolition', 'Concussion', 'Sonic'])
        self.assertEqual(levels, gen.L3)
        self.assertIsNone(states)
        spreads, falloffs = gen.shape_for('BlastSonic')
        nodes = load_text(gen.family('BlastSonic', None, gen.valid_targets(False), levels,
            versus_override=gen.blend_versus(parents), spreads=spreads, falloffs=falloffs))
        for node in nodes:
            main = next(c for c in node.children if c.value == 'AreaDamage')
            status = next(c for c in node.children if c.value == 'GrantExternalCondition')
            self.assertEqual(main.get('ValidTargets'), 'Ground, Water')
            self.assertEqual(status.get('Condition'), 'SonicDebuff')


if __name__ == '__main__':
    unittest.main()
