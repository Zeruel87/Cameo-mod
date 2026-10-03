"""Read-only target-domain inventory including declared secondary weapons.

DIAGNOSTIC, NOT A GATE. This reports candidates for human review. A clean report
is NOT proof of policy compliance, and a candidate is NOT proof that a payload
reaches an actor — blast geometry, relationships, conditions, map rules and
custom tags all remain open.

⚠ MASK APPROXIMATION. ``mask`` subtracts ``InvalidTargets`` from ``ValidTargets``
at the DOMAIN level. The engine instead tests
``ValidTargets.Overlaps(victimTypes) && !InvalidTargets.Overlaps(victimTypes)``
against the victim's WHOLE type set, so an actor carrying BOTH ``Air`` and an
excluded custom tag cannot be represented by subtraction. Raw valid/invalid tags
are therefore retained on every route node, and a custom tag in EITHER list sets
``requires_custom_tag_review``. Never treat a candidate — or its absence — as
settled while that flag is set.

⚠ DELIVERY SEMANTICS. A secondary weapon's own ``ValidTargets`` is consulted by
some referring warheads and ignored by others; see ``SECONDARY_MASK_ROLE``. A
SELECTION gate chooses which actor a projectile is aimed at — it does NOT bound
the impact's area effect, so it must never be read as excluding victims at impact
time.

Known coverage limits are enumerated in the report's ``limits``.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from miniyaml import Ruleset

ROOT = Path(__file__).resolve().parents[2]
DAMAGE = {'AreaDamage', 'SpreadDamage', 'AreaDamagePercentage', 'AffectsIntegrity'}
REFERENCES = {'Weapon', 'Weapons', 'Explosion', 'EmptyWeapon', 'ImpactWeapon', 'TriggerWeapon'}
DOMAINS = {'Ground', 'Water', 'Air'}
ISSUES = ('air_only_root_allows_surface_payload',
          'surface_only_root_allows_air_payload',
          'dual_root_payload_excludes_air',
          'dual_root_payload_excludes_surface')

# Engine default for BOTH WeaponInfo.ValidTargets and Warhead.ValidTargets.
DEFAULT_MASK = 'Ground, Water'

# How the REFERRING warhead treats the secondary weapon's own ValidTargets.
# 'inert_for_damage': the warhead calls WeaponInfo.Impact directly, which never
#   consults WeaponInfo.IsValidAgainst, so the secondary weapon's mask does not
#   constrain damage at all (source: SpawnSmokeParticleWarhead -> SmokeParticle).
# 'selection_only': the warhead checks weapon.IsValidAgainst to CHOOSE a target,
#   but the impact that follows is still bounded only by the secondary weapon's
#   WARHEAD masks — an air victim inside the blast radius is still hit
#   (source: FireShrapnelWarhead / FireClusterWarhead / FireClusterASWarhead /
#   FireRadiusWarhead).
# 'unverified': not yet source-checked; do NOT assume either behaviour.
SECONDARY_MASK_ROLE = {
    'SpawnSmokeParticle': 'inert_for_damage',
    'FireShrapnel': 'selection_only',
    'FireCluster': 'selection_only',
    'FireClusterAS': 'selection_only',
    'FireRadius': 'selection_only',
}


def tokens(value):
    return {x.strip() for x in value.split(',') if x.strip()}


def target_tags(node, default=DEFAULT_MASK):
    """Raw (ValidTargets, InvalidTargets) tag sets for a weapon or warhead node.

    An ABSENT ValidTargets takes the engine default; an EXPLICIT empty value
    yields the EMPTY set, because FieldLoader assigns an empty BitSet for a null
    yaml value rather than keeping the field's default. The two cases differ.
    """
    allowed = node.child('ValidTargets')
    excluded = node.child('InvalidTargets')
    return (tokens(allowed.value if allowed is not None else default),
            tokens(excluded.value if excluded is not None else ''))


def mask(node, default=DEFAULT_MASK):
    """DOMAIN-level approximation of the effective mask. See the module docstring."""
    allowed, excluded = target_tags(node, default)
    return allowed - excluded


def node_tags(node):
    """Raw and parsed target tags for one route node, with the review flag."""
    allowed, excluded = target_tags(node)
    valid = node.child('ValidTargets')
    invalid = node.child('InvalidTargets')
    custom = (allowed | excluded) - DOMAINS
    return {
        # Declared-empty ('') is kept distinct from absent (None).
        'valid_targets': valid.value if valid is not None else None,
        'invalid_targets': invalid.value if invalid is not None else None,
        'allowed_tags': sorted(allowed),
        'invalid_tags': sorted(excluded),
        'domain_tags': sorted((allowed - excluded) & DOMAINS),
        'custom_target_tags': sorted(allowed - DOMAINS),
        'excluded_custom_tags': sorted(excluded - DOMAINS),
        'requires_custom_tag_review': bool(custom),
    }


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def source_metadata(rs):
    """Provenance so a snapshot can be tied to the exact inputs that produced it."""
    tool = Path(__file__).resolve()
    meta = {'tool': 'tools/audit/target_payload_routes.py',
            'tool_path': tool.as_posix(), 'tool_sha256': _sha256(tool)}
    repo = getattr(rs, 'repo_root', None)
    manifest = getattr(rs, 'manifest', None)
    if repo is None or manifest is None:
        # Synthetic rulesets (unit tests) carry no manifest or repository root.
        meta.update({'generated_from': None, 'source_file_count': 0, 'source_sha256': {}})
        return meta
    repo = Path(repo).resolve()
    hashes = {}
    for path in list(manifest.rules) + list(manifest.weapons):
        path = Path(path).resolve()
        try:
            key = path.relative_to(repo).as_posix()
        except ValueError:
            key = path.as_posix()
        hashes[key] = _sha256(path)
    meta.update({'generated_from': repo.as_posix(),
        'source_file_count': len(hashes), 'source_sha256': dict(sorted(hashes.items()))})
    return meta


def inventory(rs):
    users = defaultdict(list)
    for name in rs.actors:
        if name.startswith('^'):
            continue
        for trait in rs.resolve(name).children:
            if trait.key.split('@')[0] == 'Armament' and trait.get('Weapon'):
                weapon = rs.weapon(trait.get('Weapon'))
                if weapon:
                    users[weapon.key].append({'actor': name, 'armament': trait.key,
                        'condition': trait.get('RequiresCondition')})

    edges = defaultdict(list)
    for name in rs.weapons:
        node = rs.resolve_weapon(name)

        def walk(parent, path='', warhead=None, warhead_node=None):
            for child in parent.children:
                here = path + '/' + child.key
                if child.key.split('@')[0] == 'Warhead':
                    current, current_node = child.value, child
                else:
                    current, current_node = warhead, warhead_node
                if child.key in REFERENCES:
                    # The REFERRING warhead's own mask also carries custom tags; retain it on
                    # the edge so its uncertainty travels with the route.
                    referrer = node_tags(current_node) if current_node is not None else None
                    for value in tokens(child.value):
                        target = rs.weapon(value)
                        if target:
                            edges[name].append({'target': target.key, 'path': here,
                                'referrer_key': child.key, 'referrer_warhead': current,
                                'referrer_target_tags': referrer,
                                'secondary_mask_role': SECONDARY_MASK_ROLE.get(current, 'unverified')})
                walk(child, here, current, current_node)

        walk(node)

    candidates = []
    visited_routes = 0
    analysed_roots = []
    roots_with_custom_tags = []
    excluded_roots = {'empty_mask': [], 'custom_only': []}

    def root_record(name, tags):
        return {'root': name, **tags, 'bindings': users[name]}

    for root in sorted(users):
        node = rs.resolve_weapon(root)
        root_tags = node_tags(node)
        domains = mask(node) & DOMAINS
        if not mask(node):
            excluded_roots['empty_mask'].append(root_record(root, root_tags))
            continue
        if not domains:
            # No domain bit to reason about. Do NOT guess one.
            excluded_roots['custom_only'].append(root_record(root, root_tags))
            continue
        analysed_roots.append(root)
        if root_tags['requires_custom_tag_review']:
            roots_with_custom_tags.append(root)
        pending = [(root, [])]
        visited = set()
        while pending:
            name, route = pending.pop()
            if name in visited:
                continue
            visited.add(name)
            visited_routes += 1
            weapon = rs.resolve_weapon(name)
            for wh in weapon.children:
                if wh.value not in DAMAGE:
                    continue
                allowed, excluded = target_tags(wh)
                effective = allowed - excluded
                outside = (effective & DOMAINS) - domains
                missing = domains - effective
                # Water/Ground differences can be intentional terrain rules;
                # isolate the requested air-versus-surface boundary.
                issue = None
                if domains == {'Air'} and outside & {'Ground', 'Water'}:
                    issue = 'air_only_root_allows_surface_payload'
                elif 'Air' not in domains and 'Air' in outside:
                    issue = 'surface_only_root_allows_air_payload'
                elif 'Air' in domains and domains & {'Ground', 'Water'}:
                    if 'Air' in missing:
                        issue = 'dual_root_payload_excludes_air'
                    elif not effective & {'Ground', 'Water'}:
                        issue = 'dual_root_payload_excludes_surface'
                if issue:
                    wh_tags = node_tags(wh)
                    route_nodes = [root_tags]
                    for step in route:
                        step_tags = node_tags(rs.resolve_weapon(step['target']))
                        step_tags['step'] = step
                        route_nodes.append(step_tags)
                    review = (wh_tags['requires_custom_tag_review']
                        or any(n['requires_custom_tag_review'] for n in route_nodes)
                        or any((s.get('referrer_target_tags') or {}).get(
                            'requires_custom_tag_review') for s in route))
                    candidates.append({'root': root, 'root_domains': sorted(domains),
                        'root_target_tags': root_tags,
                        'weapon': name, 'warhead': wh.key, 'type': wh.value,
                        'valid_targets': wh.child('ValidTargets').value if wh.child('ValidTargets') is not None else DEFAULT_MASK,
                        'invalid_targets': wh.get('InvalidTargets') or '',
                        'allowed_tags': sorted(allowed), 'invalid_tags': sorted(excluded),
                        'custom_target_tags': sorted(allowed - DOMAINS),
                        'excluded_custom_tags': sorted(excluded - DOMAINS),
                        'requires_custom_tag_review': review,
                        'damage': wh.get('Damage'), 'route': route,
                        'route_nodes': route_nodes,
                        'issue': issue, 'bindings': users[root]})

            for edge in edges[name]:
                pending.append((edge['target'], route + [{'from': name, **edge}]))
    counts = {issue: 0 for issue in ISSUES}
    for r in candidates:
        counts[r['issue']] += 1
    return {'scope': 'active concrete direct armaments and declared weapon references',
        'metadata': source_metadata(rs),
        'direct_weapons': len(users), 'visited_root_weapon_pairs': visited_routes,
        'roots': {'analysed': len(analysed_roots),
            'analysed_with_custom_tags': len(roots_with_custom_tags),
            'excluded': {k: len(v) for k, v in excluded_roots.items()},
            'excluded_roots': excluded_roots},
        'counts': counts,
        'secondary_candidate_count': sum(bool(r['route']) for r in candidates),
        'mask_semantics': 'ValidTargets-minus-InvalidTargets is a DOMAIN-level approximation of '
            'the engine\'s Overlaps()-based test; retain the raw tags and the '
            'requires_custom_tag_review flag when interpreting any candidate.',
        'candidates': candidates,
        'limits': [
            'No map-local, script, spawned-actor or support-power closure.',
            'No trait-level weapon roots: FireWarheadsOnDeath.Weapon/EmptyWeapon, '
            'Armament.CasingWeapon, FallsToEarth.Explosion and the *ImpactWeapon traits are NOT '
            'followed, so death, impact and support-power routes are invisible.',
            'Status and visual warheads are out of scope: DAMAGE covers AreaDamage, SpreadDamage, '
            'AreaDamagePercentage and AffectsIntegrity only, so GrantExternalCondition and '
            'ApplyPhysicalState payloads are never candidates.',
            'WeaponInfo.AirThreshold is not modelled: a terrain target above the threshold '
            'validates Air only, so the root-domain model approximates direct fire.',
            'Custom tags and eligibility can make a reported route non-actionable — and can also '
            'make an unreported one reachable. Raw valid/invalid tags are retained per route node '
            'for that review.',
            'Secondary impact activation, geometry and damage signs need review. A referring '
            'warhead that gates SELECTION does not bound the impact area effect.',
            'One reachability path per root/weapon; not multiplicity or DPS.',
            'Coverage is partial by construction: roots with no domain bit are excluded rather '
            'than guessed, so their secondary routes are not audited at all.',
        ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = inventory(Ruleset(ROOT))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    summary = {k: v for k, v in report.items() if k not in ('candidates', 'metadata')}
    summary['metadata'] = {k: v for k, v in report['metadata'].items() if k != 'source_sha256'}
    summary['metadata']['source_sha256_entries'] = report['metadata']['source_file_count']
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
