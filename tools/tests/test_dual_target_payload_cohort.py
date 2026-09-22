"""Full-air payload policy for the three dual-target leaf weapons (2026-09-10).

A dual-target weapon must deliver its full applicable damage to air as well as
surface. These three were the reviewed leaves whose weapon-level mask already
permitted Air while one DAMAGE event was still restricted to Ground/Water.

Ongoing coverage here is deliberately narrow: complete before/after resolved
snapshots and the exact field delta for these three weapons only. The
whole-inventory before/after fingerprint is external historical evidence
(`validation/deepseek-dual-target-inventory-fingerprint-20260910.json`), not a
frozen roster in this repository.
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'audit'))
from dump_resolved import node_to_obj
from miniyaml import Ruleset
from target_payload_routes import DAMAGE, DOMAINS, REFERENCES, target_tags, tokens

FIXTURE = (pathlib.Path(__file__).resolve().parent / 'fixtures'
           / 'dual_target_payload_history_20260910.json')
SELECTED = ('ASDFGun2', 'SteelFighterRailgun', 'TS30mmRail')
# The one DAMAGE event per weapon that was still Ground/Water before the change.
TARGETED_WARHEAD = {
    'ASDFGun2': 'Warhead@Railgun_Heavy_ExtraDamage',
    'SteelFighterRailgun': 'Warhead@Railgun_Heavy_ExtraDamage',
    'TS30mmRail': 'Warhead@RailgunWeaponPercentage',
}
FULL_AIR = 'Ground, Water, Air'


class DualTargetPayloadCohortTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))

    # ---- helpers --------------------------------------------------------- #

    @staticmethod
    def _flat(obj, prefix=''):
        flat = {}
        if isinstance(obj, dict):
            for key, value in obj.items():
                flat.update(DualTargetPayloadCohortTest._flat(value, prefix + '/' + key))
        else:
            flat[prefix] = obj
        return flat

    @classmethod
    def _delta(cls, before, after):
        """The exact field delta between two resolved snapshots."""
        flat_before, flat_after = cls._flat(before), cls._flat(after)
        return sorted((key, flat_before.get(key), flat_after.get(key))
                      for key in set(flat_before) | set(flat_after)
                      if flat_before.get(key) != flat_after.get(key))

    def _recorded(self, name):
        return sorted(tuple(row) for row in self.fixture['changed_fields'][name])

    def _damage_warheads(self, name):
        return {c.key: c for c in self.rules.resolve_weapon(name).children
                if c.value in DAMAGE}

    @classmethod
    def _inheritance_parents(cls, rules):
        """Canonical parent weapon -> [(raw child, inherit key)], case-insensitive."""
        parents = {}
        for name in rules.weapons:
            raw = rules.weapon(name)
            for key, target in rules.inherits_of(raw):
                canonical = rules.weapon(target)
                if canonical is not None:
                    parents.setdefault(canonical.key, []).append((name, key))
        return parents

    # ---- the qualifying conditions --------------------------------------- #

    def test_selected_weapons_have_no_inheritance_descendants(self):
        """Leaf = nothing inherits from it (raw-node check, canonical identity)."""
        parents = self._inheritance_parents(self.rules)
        for name in SELECTED:
            self.assertEqual(parents.get(name, []), [], name)
            self.assertEqual(self.fixture['qualification'][name]['inheritance_descendants'], [], name)

    def test_selected_weapons_have_no_secondary_referrers(self):
        referenced = set()
        for name in self.rules.weapons:
            def walk(parent):
                for child in parent.children:
                    if child.key in REFERENCES:
                        referenced.update(tokens(child.value))
                    walk(child)
            walk(self.rules.resolve_weapon(name))
        for name in SELECTED:
            self.assertNotIn(name, referenced, name)

    def test_selected_weapons_permit_air_at_weapon_level(self):
        for name in SELECTED:
            allowed, excluded = target_tags(self.rules.resolve_weapon(name))
            self.assertIn('Air', (allowed - excluded) & DOMAINS, name)

    def test_every_damage_event_now_permits_air(self):
        for name in SELECTED:
            self.assertTrue(self._damage_warheads(name), name)
            for key, warhead in self._damage_warheads(name).items():
                allowed, excluded = target_tags(warhead)
                self.assertIn('Air', allowed - excluded, (name, key))

    # ---- exact delta and preservation ------------------------------------ #

    def test_delta_is_exactly_the_one_recorded_air_field(self):
        for name in SELECTED:
            delta = self._delta(self.fixture['before'][name], self.fixture['after'][name])
            self.assertEqual(delta, self._recorded(name), name)
            self.assertEqual(len(delta), 1, name)
            path, old, new = delta[0]
            self.assertEqual(path, '/%s/ValidTargets' % TARGETED_WARHEAD[name], name)
            self.assertNotEqual(old, FULL_AIR, name)
            self.assertEqual(new, FULL_AIR, name)

    def test_targeted_warhead_kept_every_other_field(self):
        for name in SELECTED:
            key = TARGETED_WARHEAD[name]
            before = self.fixture['before'][name][key]
            after = self.fixture['after'][name][key]
            self.assertIsInstance(before, dict, (name, key))
            for field, value in before.items():
                if field == 'ValidTargets':
                    continue
                self.assertEqual(after.get(field), value, (name, key, field))
            self.assertNotEqual(before.get('ValidTargets'), FULL_AIR, (name, key))

    def test_resolved_state_matches_the_recorded_after_snapshot(self):
        for name in SELECTED:
            self.assertEqual(node_to_obj(self.rules.resolve_weapon(name)),
                             self.fixture['after'][name], name)

    def test_mutation_guard_rejects_unrelated_damage_or_timing_change(self):
        """The same comparator must reject an unrelated damage/timing edit.

        Mutates a copy in memory only -- no production converter fingerprint is
        touched or relaxed.
        """
        def bump(obj, path):
            node, parts = obj, [p for p in path.split('/') if p]
            for key in parts[:-1]:
                node = node[key]
            node[parts[-1]] = str(int(node[parts[-1]]) + 1)
            return '/'.join(parts)

        for name in SELECTED:
            recorded = self._recorded(name)
            for label, path in (('damage', '/%s/Damage' % TARGETED_WARHEAD[name]),
                                ('timing', '/ReloadDelay')):
                with self.subTest(weapon=name, mutation=label):
                    after = json.loads(json.dumps(self.fixture['after'][name]))
                    node = after
                    for key in [p for p in path.split('/') if p][:-1]:
                        node = node[key]
                    self.assertIn([p for p in path.split('/') if p][-1], node, (name, label))
                    mutated = bump(after, path)
                    delta = self._delta(self.fixture['before'][name], after)
                    self.assertNotEqual(recorded, delta, (name, mutated))
                    self.assertEqual(len(delta), len(recorded) + 1, (name, mutated))

    def test_weapon_level_custom_exclusions_survived(self):
        allowed, excluded = target_tags(self.rules.resolve_weapon('ASDFGun2'))
        self.assertIn('Air', allowed)
        self.assertEqual(excluded, {'Bridge', 'Structure', 'wall'})
        for name in ('SteelFighterRailgun', 'TS30mmRail'):
            self.assertEqual(target_tags(self.rules.resolve_weapon(name))[1], set(), name)


if __name__ == '__main__':
    unittest.main()
