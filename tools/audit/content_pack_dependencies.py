"""Inventory active content-pack references before selective-loading design.

This is a conservative source inventory, not a runtime dependency certificate.
Map scripts, conditional asset references and dynamic actor creation need separate
analysis. Shared-source ownership does not imply that all of a pack is required.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from miniyaml import Ruleset

ROOT = Path(__file__).resolve().parents[2]
WEAPON_FIELDS = {'Weapon', 'Weapons', 'Explosion', 'EmptyWeapon', 'ImpactWeapon', 'TriggerWeapon'}


def owner(node):
    path = Path(node.file).as_posix()
    if '/ContentPacks/' not in path:
        return 'global/shared'
    parts = path.split('/ContentPacks/', 1)[1].split('/')
    return '/'.join(parts[:2]) if len(parts) > 2 and parts[1] != 'yaml' else parts[0]


def inventory(rules):
    edges = []
    for kind, table in [('actor', rules.actors), ('weapon', rules.weapons)]:
        for name, node in table.items():
            source = owner(node)
            for _, parent in rules.inherits_of(node):
                target = rules.actor(parent) if kind == 'actor' else rules.weapon(parent)
                if target and owner(target) != source:
                    edges.append(dict(kind=kind + '_inheritance', source=source,
                                      target=owner(target), name=name, reference=parent))

            def walk(current, path=''):
                for child in current.children:
                    child_path = path + '/' + child.key
                    if child.key in WEAPON_FIELDS:
                        for reference in child.value.split(','):
                            reference = reference.strip()
                            target = rules.weapon(reference)
                            if target and owner(target) != source:
                                edges.append(dict(kind=kind + '_weapon_reference', source=source,
                                                  target=owner(target), name=name,
                                                  reference=reference, path=child_path))
                    walk(child, child_path)

            walk(node)
    edges.sort(key=lambda row: tuple(str(row.get(k, '')) for k in
                                    ('kind', 'source', 'target', 'name', 'reference', 'path')))
    return {
        'scope': 'active explicit inheritance and recognized weapon fields; incomplete runtime closure',
        'counts': dict(rules_files=len(rules.manifest.rules),
                       weapon_files=len(rules.manifest.weapons),
                       sequence_files=len(rules.manifest.sequences),
                       actor_definitions=len(rules.actors), weapon_definitions=len(rules.weapons)),
        'edge_counts': dict(sorted(Counter(row['kind'] for row in edges).items())),
        'cross_owner_edges': edges,
    }


def owner_closure(edges, seeds):
    graph = defaultdict(set)
    for edge in edges:
        graph[edge['source']].add(edge['target'])
    reached = set(seeds)
    pending = list(seeds)
    while pending:
        for target in graph[pending.pop()] - reached:
            reached.add(target)
            pending.append(target)
    return sorted(reached)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='optional JSON inventory destination')
    parser.add_argument('--seed', action='append', default=[], help='owner for coarse closure; repeatable')
    args = parser.parse_args()
    report = inventory(Ruleset(ROOT))
    if args.seed:
        report['coarse_owner_closure'] = owner_closure(report['cross_owner_edges'], args.seed)
        report['closure_seeds'] = args.seed
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'cross_owner_edges'}, indent=2))


if __name__ == '__main__':
    main()
