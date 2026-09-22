"""Inventory authored delivery/element combinations and active template usage.

An absent combination is an unrepresented design option, not an instruction to
add it. Multi-parent mixtures are reported verbatim to expose weighting choices.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

from miniyaml import Ruleset

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'balance'))
import gen_weapon_template as gen

DELIVERIES = ('Bullet', 'CannonAP', 'CannonHE', 'MissileAP', 'MissileHE',
              'MissileAA', 'Flak', 'Arrow', 'Melee', 'Demolition', 'Concussion')
ELEMENTS = ('Flame', 'Chemical', 'Toxic', 'Laser', 'Prism', 'Tesla', 'Sonic',
            'Magic', 'Nuclear', 'Railgun')
DELIVERY_GROUPS = {'Bullet': {'Bullet'}, 'Cannon': {'CannonAP', 'CannonHE'},
    'Missile': {'MissileAP', 'MissileHE', 'MissileAA'}, 'Flak': {'Flak'},
    'Arrow': {'Arrow'}, 'Melee': {'Melee'}, 'GrenadeBlast': {'Demolition', 'Concussion'}}
ELEMENT_COMPOSITIONS = {name: Counter([name]) for name in ELEMENTS}
ELEMENT_COMPOSITIONS.update(Cryo=Counter(['Laser', 'Prism']),
    Plasma=Counter(['Flame', 'Chemical']),
    Quantum=Counter(['Railgun', 'Laser', 'Tesla']),
    Thermobaric=Counter(['Demolition', 'Concussion', 'Flame']),
    Waveforce=Counter(['Flame', 'Chemical', 'Railgun', 'Laser', 'Tesla']))


def same_proportions(left, right):
    return bool(left) and set(left) == set(right) and all(
        left[k] * sum(right.values()) == right[k] * sum(left.values()) for k in left)


def inventory(rs):
    bindings = defaultdict(set)
    for name in rs.actors:
        actor = rs.resolve(name)
        for trait in actor.children:
            if trait.key.split('@')[0] == 'Armament':
                weapon = trait.get('Weapon')
                if weapon:
                    bindings[weapon.lower()].add(name)

    def ancestry(name, seen=None):
        seen = set() if seen is None else seen
        if name in seen:
            return seen
        seen.add(name)
        node = rs.weapon(name)
        if node:
            for _, parent in rs.inherits_of(node):
                ancestry(parent, seen)
        return seen

    used = defaultdict(set)
    for weapon in bindings:
        for parent in ancestry(weapon):
            if parent.startswith('^Warhead_'):
                used[parent].add(weapon)

    combinations = []
    covered = defaultdict(list)
    for family, (parents, states, levels) in sorted(gen.BLEND_FAMILIES.items()):
        delivery = sorted(set(parents) & set(DELIVERIES))
        elements = sorted(set(parents) & set(ELEMENTS))
        if not delivery:
            continue
        templates = ['^Warhead_' + family + '_' + level for level in levels]
        live = [name for name in templates if rs.weapon(name)]
        weapons = sorted(set().union(*(used[name] for name in templates)))
        row = dict(family=family, parents=dict(Counter(parents)),
                   deliveries=delivery, elements=elements, live_templates=live,
                   bound_weapons=weapons, states=states,
                   condition=gen.FAMILY_CONDITION.get(family))
        combinations.append(row)
        for d in delivery:
            for e in elements:
                covered[d, e].append(family)
    named_matrix = []
    for delivery, primitives in DELIVERY_GROUPS.items():
        for element, composition in ELEMENT_COMPOSITIONS.items():
            matches = []
            for row in combinations:
                parents = row['parents']
                if not primitives.intersection(parents):
                    continue
                remaining = Counter({k: v for k, v in parents.items() if k not in primitives})
                if same_proportions(remaining, composition):
                    matches.append(row['family'])
            named_matrix.append(dict(delivery=delivery, element=element, families=matches))
    return dict(
        scope='active manifest; authored generator blends; direct armament ancestry only',
        interpretation='coverage means a primitive participates in a blend, not an exact 50/50 pairing',
        deliveries=list(DELIVERIES), elements=list(ELEMENTS),
        combinations=combinations,
        matrix=[dict(delivery=d, element=e, families=covered[d, e])
                for d in DELIVERIES for e in ELEMENTS],
        named_element_matrix=named_matrix,
        named_matrix_interpretation='Remove delivery parents, then match exact elemental proportions; delivery-to-element weighting remains in combination rows.',
        limits=['Pure element weapons and bespoke per-weapon stacks are not combination families.',
                'Cryo, Plasma, Quantum and Thermobaric appear as their primitive parents with weights.',
                'Missing cells do not establish a gameplay need.',
                'Dynamic/map-local weapon use is not included.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = inventory(Ruleset(ROOT))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(combinations=len(report['combinations']),
        covered_cells=sum(bool(row['families']) for row in report['matrix']),
        total_cells=len(report['matrix']),
        generated_but_not_live=[row['family'] for row in report['combinations']
                               if not row['live_templates']]), indent=2))


if __name__ == '__main__':
    main()
