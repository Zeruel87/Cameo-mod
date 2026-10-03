"""Mask defaults, root classification and graph reachability for the diagnostic route audit."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'audit'))
from miniyaml import Node
from target_payload_routes import ISSUES, inventory, mask, target_tags


class _Stub:
    """Minimal Ruleset stand-in: actors and weapons are plain dicts of Nodes."""

    def __init__(self, actor_weapon, weapons):
        pairs = actor_weapon if isinstance(actor_weapon, dict) else {'unit': actor_weapon}
        self.actors = {name: Node(name, '',
            [Node('Armament', '', [Node('Weapon', weapon)])]) for name, weapon in pairs.items()}
        self.weapons = weapons

    def resolve(self, name):
        return self.actors[name]

    def weapon(self, name):
        return self.weapons.get(name)

    def resolve_weapon(self, name):
        return self.weapons[name]


def cloud(name='Cloud', warhead='AreaDamage', valid='Ground, Water, Air', extra=()):
    return Node(name, '', [Node('Warhead@hit', warhead,
        [Node('Damage', '100'), Node('ValidTargets', valid), *extra])])


class PayloadRouteTest(unittest.TestCase):
    def test_missing_mask_uses_engine_default_but_explicit_empty_does_not(self):
        self.assertEqual(mask(Node('W', '')), {'Ground', 'Water'})
        self.assertEqual(mask(Node('W', '', [Node('ValidTargets', '')])), set())

    def test_invalid_targets_override_valid_targets(self):
        self.assertEqual(mask(Node('W', '', [Node('ValidTargets', 'Ground, Water, Air'),
            Node('InvalidTargets', 'Air, Shielded')])), {'Ground', 'Water'})

    def test_target_tags_retains_raw_allowed_and_excluded_tags(self):
        allowed, excluded = target_tags(Node('W', '', [
            Node('ValidTargets', 'Ground, Air'), Node('InvalidTargets', 'Air, ToxinImmune')]))
        self.assertEqual(allowed, {'Ground', 'Air'})
        self.assertEqual(excluded, {'Air', 'ToxinImmune'})

    def test_secondary_cycle_reports_leak_once_with_root_provenance(self):
        actor = Node('unit', '', [Node('Armament', '', [Node('Weapon', 'Root')])])
        root = Node('Root', '', [Node('ValidTargets', 'Ground, Water'),
            Node('Warhead@spawn', 'FireCluster', [Node('Weapon', 'Cloud')])])
        cloud_node = Node('Cloud', '', [Node('Warhead@hit', 'AreaDamage', [
            Node('Damage', '100'), Node('ValidTargets', 'Ground, Water, Air')]),
            Node('Warhead@cycle', 'FireCluster', [Node('Weapon', 'Root')])])
        class Rules:
            actors = {'unit': actor}
            weapons = {'Root': root, 'Cloud': cloud_node}
            def resolve(self, name): return self.actors[name]
            def weapon(self, name): return self.weapons.get(name)
            def resolve_weapon(self, name): return self.weapons[name]
        report = inventory(Rules())
        self.assertEqual(report['visited_root_weapon_pairs'], 2)
        self.assertEqual(len(report['candidates']), 1)
        candidate = report['candidates'][0]
        self.assertEqual(candidate['root'], 'Root')
        self.assertEqual(candidate['weapon'], 'Cloud')
        self.assertEqual(candidate['route'][0]['path'], '/Warhead@spawn/Weapon')

    def test_trigger_weapon_is_a_followed_reference(self):
        root = Node('Root', '', [Node('ValidTargets', 'Ground, Water'),
            Node('Warhead@arc', 'TriggerLayerWeapon', [
                Node('ValidTargets', 'Ground, Water'), Node('TriggerWeapon', 'Cloud')])])
        report = inventory(_Stub('Root', {'Root': root, 'Cloud': cloud()}))
        self.assertEqual(len(report['candidates']), 1)
        route = report['candidates'][0]['route'][0]
        self.assertEqual(route['path'], '/Warhead@arc/TriggerWeapon')
        self.assertEqual(route['referrer_warhead'], 'TriggerLayerWeapon')
        self.assertEqual(route['secondary_mask_role'], 'unverified')

    def test_domain_plus_custom_root_is_analysed_on_its_domain_portion(self):
        root = Node('Root', '', [Node('ValidTargets', 'Ground, Vehicle'),
            Node('Warhead@spawn', 'SpawnSmokeParticle', [Node('Weapon', 'Cloud')])])
        report = inventory(_Stub('Root', {'Root': root, 'Cloud': cloud()}))
        self.assertEqual(report['roots']['analysed'], 1)
        self.assertEqual(report['roots']['analysed_with_custom_tags'], 1)
        self.assertEqual(report['roots']['excluded'], {'empty_mask': 0, 'custom_only': 0})
        candidate = report['candidates'][0]
        self.assertEqual(candidate['root_domains'], ['Ground'])
        self.assertTrue(candidate['requires_custom_tag_review'])
        self.assertEqual(candidate['root_target_tags']['custom_target_tags'], ['Vehicle'])

    def test_custom_only_root_is_excluded_rather_than_guessed(self):
        root = Node('Root', '', [Node('ValidTargets', 'Infantry, Vehicle'),
            Node('Warhead@spawn', 'SpawnSmokeParticle', [Node('Weapon', 'Cloud')])])
        report = inventory(_Stub('Root', {'Root': root, 'Cloud': cloud()}))
        self.assertEqual(report['candidates'], [])
        self.assertEqual(report['roots']['excluded'], {'empty_mask': 0, 'custom_only': 1})
        self.assertEqual([r['root'] for r in report['roots']['excluded_roots']['custom_only']],
                         ['Root'])
        self.assertEqual(report['roots']['analysed'], 0)

    def test_explicitly_empty_root_mask_is_reported_as_excluded(self):
        root = Node('Root', '', [Node('ValidTargets', ''),
            Node('Warhead@spawn', 'SpawnSmokeParticle', [Node('Weapon', 'Cloud')])])
        report = inventory(_Stub('Root', {'Root': root, 'Cloud': cloud()}))
        self.assertEqual(report['roots']['excluded'], {'empty_mask': 1, 'custom_only': 0})
        self.assertEqual([r['root'] for r in report['roots']['excluded_roots']['empty_mask']],
                         ['Root'])

    def test_excluded_roots_retain_raw_tags_and_bindings(self):
        custom_only = Node('Root', '', [Node('ValidTargets', 'Infantry, Vehicle')])
        blank = Node('EmptyRoot', '', [Node('ValidTargets', 'Air'), Node('InvalidTargets', 'Air')])
        report = inventory(_Stub({'unit': 'Root', 'other': 'EmptyRoot'},
                                 {'Root': custom_only, 'EmptyRoot': blank}))
        self.assertEqual(report['roots']['excluded'], {'empty_mask': 1, 'custom_only': 1})
        custom = report['roots']['excluded_roots']['custom_only'][0]
        self.assertEqual(custom['root'], 'Root')
        self.assertEqual(custom['valid_targets'], 'Infantry, Vehicle')
        self.assertEqual(custom['custom_target_tags'], ['Infantry', 'Vehicle'])
        self.assertTrue(custom['requires_custom_tag_review'])
        self.assertEqual(custom['bindings'],
                         [{'actor': 'unit', 'armament': 'Armament', 'condition': None}])
        empty = report['roots']['excluded_roots']['empty_mask'][0]
        self.assertEqual(empty['root'], 'EmptyRoot')
        self.assertEqual(empty['valid_targets'], 'Air')
        self.assertEqual(empty['invalid_targets'], 'Air')
        self.assertFalse(empty['requires_custom_tag_review'])
        self.assertEqual(empty['bindings'][0]['actor'], 'other')

    def test_referrer_warhead_tags_are_retained_and_propagate_uncertainty(self):
        root = Node('Root', '', [Node('ValidTargets', 'Ground, Water'),
            Node('Warhead@Cloud', 'SpawnSmokeParticle', [
                Node('ValidTargets', 'Air'), Node('InvalidTargets', 'ToxinImmune'),
                Node('Weapon', 'Cloud')])])
        report = inventory(_Stub('Root', {'Root': root, 'Cloud': cloud()}))
        candidate = report['candidates'][0]
        step = candidate['route'][0]
        self.assertEqual(step['referrer_warhead'], 'SpawnSmokeParticle')
        self.assertEqual(step['referrer_target_tags']['valid_targets'], 'Air')
        self.assertEqual(step['referrer_target_tags']['excluded_custom_tags'], ['ToxinImmune'])
        self.assertTrue(step['referrer_target_tags']['requires_custom_tag_review'])
        # The ONLY custom tag on this route sits on the referring warhead, so the
        # propagated flag proves it travels.
        self.assertTrue(candidate['requires_custom_tag_review'])

    def test_all_four_issue_counts_are_emitted_even_when_zero(self):
        root = Node('Root', '', [Node('ValidTargets', 'Ground, Water'),
            Node('Warhead@spawn', 'SpawnSmokeParticle', [Node('Weapon', 'Cloud')])])
        report = inventory(_Stub('Root', {'Root': root,
            'Cloud': cloud(valid='Ground, Water')}))
        self.assertEqual(report['candidates'], [])
        self.assertEqual(set(report['counts']), set(ISSUES))
        self.assertEqual(set(report['counts'].values()), {0})

    def test_invalid_custom_tag_on_an_intermediate_weapon_sets_the_review_flag(self):
        root = Node('Root', '', [Node('ValidTargets', 'Ground, Water'),
            Node('Warhead@Cloud', 'SpawnSmokeParticle', [Node('Weapon', 'Cloud')])])
        misty = cloud()
        misty.children.insert(0, Node('InvalidTargets', 'ToxinImmune'))
        report = inventory(_Stub('Root', {'Root': root, 'Cloud': misty}))
        candidate = report['candidates'][0]
        self.assertTrue(candidate['requires_custom_tag_review'])
        step = candidate['route'][0]
        self.assertEqual(step['secondary_mask_role'], 'inert_for_damage')
        self.assertEqual(step['referrer_warhead'], 'SpawnSmokeParticle')
        self.assertEqual(candidate['route_nodes'][1]['excluded_custom_tags'], ['ToxinImmune'])

    def test_selection_gate_is_recorded_and_not_read_as_an_impact_exclusion(self):
        root = Node('Root', '', [Node('ValidTargets', 'Ground, Water'),
            Node('Warhead@Cluster', 'FireShrapnel', [Node('Weapon', 'Cloud')])])
        gated = cloud(name='Cloud')
        gated.children.insert(0, Node('ValidTargets', 'Infantry'))
        report = inventory(_Stub('Root', {'Root': root, 'Cloud': gated}))
        candidate = report['candidates'][0]
        self.assertEqual(candidate['issue'], 'surface_only_root_allows_air_payload')
        self.assertEqual(candidate['route'][0]['secondary_mask_role'], 'selection_only')
        # The intermediate mask is RETAINED, never used to dismiss the candidate:
        # a selection gate does not bound the impact area effect.
        self.assertEqual(candidate['route_nodes'][1]['valid_targets'], 'Infantry')
        self.assertTrue(candidate['requires_custom_tag_review'])


if __name__ == '__main__':
    unittest.main()
