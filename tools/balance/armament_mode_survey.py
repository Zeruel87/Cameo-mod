"""Active-ledger armament topology, not combat DPS or proposal approval."""
import argparse
from collections import Counter
import json

from propose_retained_firepower import (ROOT, Ruleset, OWN_ATTACKS, ATTACKS,
                                        selected_names, attack_activation, applicable, product,
                                        screen_weapon, reference_index, Unsupported)

OUT = ROOT / 'docs/audit/latest/armament_mode_survey.json'
BORROWED_ATTACKS = {'AttackGarrisoned', 'AttackOpenTopped'}


def arm_name(arm):
    field = arm.child('Name')
    return 'primary' if field is None else field.value


def topology(actor):
    arms = actor.children_named('Armament')
    if len(arms) < 2:
        return 'fewer-than-two-slots'
    if any(not arm.get('Weapon') for arm in arms):
        return 'missing-weapon-reference'
    weapons = {arm.get('Weapon').lower() for arm in arms}
    names = [arm_name(arm) for arm in arms]
    if len(arms) == 2 and set(names) == {'primary', 'garrisoned'}:
        return 'same-weapon-primary-garrison-pair' if len(weapons) == 1 else 'different-weapon-primary-garrison-pair'
    return 'other-same-weapon-slots' if len(weapons) == 1 else 'other-multiple-weapons'


def selectors(actor):
    """Only known AttackBase selectors; unrelated AttackMove is not an attack."""
    rows = []
    for node in actor.children:
        kind = node.key.split('@')[0]
        if kind in OWN_ATTACKS | BORROWED_ATTACKS:
            rows.append({'trait': node.key, 'source': 'passenger' if kind in BORROWED_ATTACKS else 'self',
                         'names': selected_names(node),
                         'activation_at_zero_conditions': attack_activation(node),
                         'requires_condition': node.get('RequiresCondition'),
                         'pause_on_condition': node.get('PauseOnCondition')})
    return rows


def pair_detail(rules, name):
    actor = rules.resolve(name)
    if topology(actor) != 'same-weapon-primary-garrison-pair':
        raise ValueError('not a same-weapon primary/garrison pair')
    arms = actor.children_named('Armament')
    attacks = selectors(actor)
    unknown = sorted(node.key for node in actor.children
                     if node.key.split('@')[0].startswith('Attack')
                     and node.key.split('@')[0] not in ATTACKS | BORROWED_ATTACKS)
    rows = []
    for arm in arms:
        entries = applicable(actor, rules.actor(name), arm)
        try:
            factor = str(product(entries))
        except (Unsupported, ValueError):
            factor = None
        rows.append({'slot': arm.key, 'name': arm_name(arm), 'weapon': arm.get('Weapon'),
                     'requires_condition': arm.get('RequiresCondition'),
                     'pause_on_condition': arm.get('PauseOnCondition'),
                     'activation_at_zero_conditions': attack_activation(arm),
                     'fire_delay': arm.get('FireDelay') or '0',
                     'casing_weapon': arm.get('CasingWeapon'),
                     'unconditional_firepower_factor': factor,
                     'selected_by_known_own_attacks': [a['trait'] for a in attacks
                         if a['source'] == 'self' and arm_name(arm) in a['names']]})
    try:
        screen_weapon(rules, arms[0])
        weapon_blocker = None
    except (Unsupported, ValueError) as error:
        weapon_blocker = str(error)
    return {'actor': name, 'armaments': rows, 'attack_selectors': attacks,
            'unknown_attack_traits': unknown, 'weapon_only_first_blocker': weapon_blocker,
            'conditional_firepower_traits': sorted(n.key for n in actor.children_named('FirepowerMultiplier')
                                                   if n.get('RequiresCondition'))}


def ledger_actors():
    actors = set()
    for path in (ROOT / 'docs/balance').glob('*.json'):
        doc = json.loads(path.read_text(encoding='utf-8'))
        for units in doc.get('sections', {}).values():
            actors.update(name for name, unit in units.items() if unit.get('armaments'))
    return sorted(actors)


def build(rules=None, names=None):
    rules = rules if rules is not None else Ruleset(ROOT)
    names = ledger_actors() if names is None else sorted(set(names))
    counts = Counter()
    pairs = []
    for name in names:
        actor = rules.resolve(name)
        if actor is None:
            counts['missing-active-actor'] += 1
            continue
        kind = topology(actor)
        counts[kind] += 1
        if kind == 'same-weapon-primary-garrison-pair':
            pairs.append(pair_detail(rules, name))
    hosts = []
    for name in sorted(rules.actors):
        if name.startswith('^'):
            continue
        rows = [a for a in selectors(rules.resolve(name)) if a['source'] == 'passenger']
        if rows:
            hosts.append({'actor': name, 'selectors': rows})
    refs = reference_index(rules, [p['armaments'][0]['weapon'] for p in pairs]) if pairs else {}
    for pair in pairs:
        selected_paths = {(arm['slot'], 'Weapon') for arm in pair['armaments']}
        others = sorted(kind + ':' + name + '/' + '/'.join(path)
                        for kind, name, path in refs[pair['armaments'][0]['weapon'].lower()]
                        if not (kind == 'actor' and name.lower() == pair['actor'].lower() and path in selected_paths))
        pair['other_base_yaml_reference_count'] = len(others)
        pair['other_base_yaml_reference_examples'] = others[:8]
    blockers = Counter(p['weapon_only_first_blocker'] or 'weapon-only-screen-passed' for p in pairs)
    return {'scope': 'Topology of ledger-listed armed actors resolved from active base YAML. '
                     'Host inventory covers all concrete active base actors, not only ledger entries. '
                     'Slot names and host selectors do not establish cargo compatibility, exclusivity or simultaneous fire. '
                     'Factors exclude conditional modifiers; host conditions, ports, range, reload, armor and runtime uptime are not simulated. '
                     'Activation is a conservative assumed zero-condition snapshot, not actual spawn state; compound expressions remain unknown. '
                     'Weapon-only passes are not actor eligibility or proposals. No armaments removed, no damage summed, no gameplay changes.',
            'ledger_listed_armed_actors': len(names), 'topology_counts': dict(sorted(counts.items())),
            'same_weapon_pair_weapon_only_first_blockers': dict(sorted(blockers.items())),
            'same_weapon_pairs_with_other_base_yaml_references': sum(p['other_base_yaml_reference_count'] > 0 for p in pairs),
            'same_weapon_pairs': pairs, 'passenger_attack_hosts': hosts}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--write', action='store_true', help='update diagnostic JSON only')
    args = parser.parse_args()
    result = build()
    text = json.dumps(result, sort_keys=True, indent=2) + '\n'
    if args.write:
        OUT.write_text(text, encoding='utf-8')
    elif not OUT.exists() or OUT.read_text(encoding='utf-8') != text:
        raise SystemExit('Armament-mode survey is stale')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in {'same_weapon_pairs', 'passenger_attack_hosts'}}, indent=2))


if __name__ == '__main__':
    main()
