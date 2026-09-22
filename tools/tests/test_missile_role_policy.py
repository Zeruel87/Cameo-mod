"""Domain-selected missile family contracts for the reviewed leaf cohort."""
import hashlib
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'audit'))
from miniyaml import Node, Ruleset
from dump_resolved import node_to_obj
from reviewed_weapon_history import missile_role_changes, missile_parent_role_changes, restore_missile_role


ROOT = pathlib.Path(__file__).resolve().parents[2]
BAKE_ROOT = (ROOT / 'docs/balance/checkpoints/20260911/four-faction-sunday-pilot' /
             'hidden-base-multipliers/local-firepower-bake-20260911')
BAKE_EVIDENCE = {
    BAKE_ROOT / 'plan.json': 'c5148dd0637969d4996dd0717bd4c1ce715bb919a6ac24b653a526bc9b11f4f8',
    BAKE_ROOT / 'remaining-batch/receipt.json': 'e5578fdc85326055b2b2fd8d48febde619543caaeff5d70e89652775caed12d7',
    BAKE_ROOT / 'exact-first-batch/receipt.json': 'cf5f7b1d78d0a1c78b135ff43c50021697394e6f299c27fa60d1ded06742b634',
}
BAKED_MISSILE_ROLE_WEAPONS = {
    'ra1_allies_sheridanassaulttank_missile',
    'ra1_soviets_monstertank_missile',
    'ra1_soviets_samsite_missile_AA',
    'ra1_soviets_su57attackbomber_missile',
    'td_gdi_humveemkii_rocketshumvee2',
    'td_gdi_humveemkii_rocketshumvee2_AA',
    'td_gdi_humveemkii_rocketshumvee2amt',
    'td_gdi_humveemkii_rocketshumvee2amt_AA',
}
BAKE_MUTATED_FIELDS = {'Damage', 'PercentageScale', 'PercentageDenominator'}


def rebuild(row):
    return Node(row[0], row[1], [rebuild(c) for c in row[2]])


def local_firepower_bake_changes():
    """Exact later transformation layered after the missile-role policy checkpoint."""
    documents = {}
    for path, expected in BAKE_EVIDENCE.items():
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise AssertionError(f'local-firepower evidence changed: {path} ({actual})')
        documents[path] = json.loads(raw)

    plan = documents[BAKE_ROOT / 'plan.json']
    planned = {}
    for actor in plan['actors']:
        for weapon in actor['weapons']:
            for channel in weapon['channels']:
                key = weapon['weapon'], channel['tag']
                value = weapon['factor'], channel['fields']
                if key in planned and planned[key] != value:
                    raise AssertionError(f'conflicting local-firepower plan for {key}')
                planned[key] = value

    changes = {}

    def record(weapon, warhead, field, before, after, factor):
        before = None if before is None else str(before)
        after = None if after is None else str(after)
        if before == after:
            return
        bucket = changes.setdefault(weapon, {'factor': factor, 'changes': []})
        if bucket['factor'] != factor:
            raise AssertionError(f'conflicting local-firepower factors for {weapon}')
        row = (warhead, field, before, after)
        if row not in bucket['changes']:
            bucket['changes'].append(row)

    remaining = documents[BAKE_ROOT / 'remaining-batch/receipt.json']
    for proof in remaining['proofs']:
        if not proof.get('fields'):
            continue
        key = proof['weapon'], proof['warhead']
        if key not in planned:
            raise AssertionError(f'unplanned local-firepower receipt row: {key}')
        factor, before_fields = planned[key]
        if factor != proof['factor']:
            raise AssertionError(f'local-firepower factor mismatch for {key}')
        for field in (set(before_fields) | set(proof['fields'])) & BAKE_MUTATED_FIELDS:
            record(proof['weapon'], proof['warhead'], field,
                   before_fields.get(field), proof['fields'].get(field), factor)

    exact = documents[BAKE_ROOT / 'exact-first-batch/receipt.json']
    for change in exact['changes']:
        key = change['weapon'], change['warhead']
        if key not in planned:
            raise AssertionError(f'unplanned exact local-firepower receipt row: {key}')
        factor, _before_fields = planned[key]
        record(change['weapon'], change['warhead'], change['field'],
               change['before'], change['after'], factor)

    return changes


def apply_local_firepower_bake(test, node, record):
    copy = node.deep_copy()
    for warhead_name, field_name, before, after in record.get('changes', []):
        warhead = copy.child(warhead_name)
        if warhead is None and warhead_name.startswith('Warhead@Missile'):
            # The bake receipt names the post-role main. The historical checkpoint still has
            # the pre-role family name, so bind the receipt to its sole damage main by shape.
            mains = [child for child in copy.children
                     if child.value == 'AreaDamage' and child.get('Damage')]
            if len(mains) == 1:
                warhead = mains[0]
        test.assertIsNotNone(warhead, (copy.key, warhead_name))
        field = warhead.child(field_name)
        test.assertEqual(before, field.value if field is not None else None,
                         (copy.key, warhead_name, field_name))
        if after is None:
            warhead.children = [child for child in warhead.children if child.key != field_name]
        elif field is None:
            warhead.children.append(Node(field_name, after))
        else:
            field.value = after
    return copy


def assert_live_local_firepower_bake(test, node, record):
    """Bind every documented post-bake field to the current resolved weapon."""
    for warhead_name, field_name, _before, after in record.get('changes', []):
        warhead = node.child(warhead_name)
        test.assertIsNotNone(warhead, (node.key, warhead_name))
        field = warhead.child(field_name)
        test.assertEqual(after, field.value if field is not None else None,
                         (node.key, warhead_name, field_name))


class MissileRolePolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rs = Ruleset(pathlib.Path(__file__).resolve().parents[2])

    def test_role_profiles_preserve_payload_and_all_other_behavior(self):
        records = missile_parent_role_changes() | missile_role_changes()
        baked = local_firepower_bake_changes()
        self.assertEqual(77, len(records))
        for name, record in records.items():
            with self.subTest(weapon=name):
                role_checkpoint = rebuild(record['before'])
                before = apply_local_firepower_bake(
                    self, role_checkpoint, baked.get(name, {}))
                now = self.rs.resolve_weapon(name)
                assert_live_local_firepower_bake(
                    self, now, baked.get(name, {}))
                targets = set(now.get('ValidTargets').split(', '))
                family = 'MissileAA' if targets == {'Air'} else 'MissileAP' if 'Air' in targets else 'MissileHE'
                mains = [c for c in now.children if c.value == 'AreaDamage' and c.get('Damage')]
                old = [c for c in before.children if c.value == 'AreaDamage' and c.get('Damage')]
                self.assertEqual(len(mains), 1)
                self.assertEqual(len(old), 1)
                main = mains[0]
                self.assertTrue(main.key.startswith('Warhead@' + family + '_'))
                self.assertEqual(main.get('Damage'), old[0].get('Damage'))
                self.assertEqual(
                    {c.key: node_to_obj(c) for c in before.children if c is not old[0]},
                    {c.key: node_to_obj(c) for c in now.children if c is not main})
                template = self.rs.resolve_weapon('^Warhead_' + main.key.split('@')[1]).child(main.key)
                # Already-correct child families keep their existing reviewed
                # profile overrides while an ancestor changes role.
                expected_profile = old[0] if old[0].key.startswith('Warhead@' + family + '_') else template
                for key in ('Versus', 'PercentageVersus', 'Spread', 'Falloff'):
                    expected = expected_profile.child(key) or template.child(key)
                    self.assertEqual(node_to_obj(main.child(key)), node_to_obj(expected))

    def test_later_firepower_bake_is_exactly_the_eight_explained_missile_changes(self):
        records = missile_parent_role_changes() | missile_role_changes()
        baked = local_firepower_bake_changes()
        overlap = {
            weapon for weapon in records
            if any(field == 'Damage' for _warhead, field, _before, _after
                   in baked.get(weapon, {}).get('changes', []))
        }
        self.assertEqual(BAKED_MISSILE_ROLE_WEAPONS, overlap)

    def test_bake_history_rejects_unrecorded_live_percentage_change(self):
        weapon = 'ra1_allies_sheridanassaulttank_missile'
        baked = local_firepower_bake_changes()[weapon]
        live = self.rs.resolve_weapon(weapon).deep_copy()
        assert_live_local_firepower_bake(self, live, baked)
        live.child('Warhead@MissileAP_Medium').child('PercentageDenominator').value = '1'
        with self.assertRaises(AssertionError):
            assert_live_local_firepower_bake(self, live, baked)

    def test_history_rejects_unrecorded_live_cadence_change(self):
        live = self.rs.resolve_weapon('TSGDIRedEye').deep_copy()
        old = restore_missile_role(self, live)
        self.assertIsNotNone(old.child('Warhead@MissileAP_Heavy'))
        live.child('ReloadDelay').value = '999'
        with self.assertRaises(AssertionError):
            restore_missile_role(self, live)


if __name__ == '__main__':
    unittest.main()
