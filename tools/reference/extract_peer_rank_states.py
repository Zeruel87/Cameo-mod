"""Co-pinned OpenRA rank-only state projections; never complete unit/DPS certification.

Evaluate a deliberately small condition grammar against cumulative GainsExperience
counts. Unknown conditions, permanent grants and production-level overrides stay
unresolved. Factory purchase eligibility, non-rank modifiers, targeting, ammo,
damage channels and compatible purchased upgrades are outside this contract.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import re

import extract_peer_units as peer

PIN = 'bbd36d9e6a2d7f0d3b24f102858af6dc8caf8a78'
MODS = ('cnc', 'ra', 'ts', 'd2k')
ENGINE_FILES = (
    'OpenRA.Game/Actor.cs',
    'OpenRA.Game/Support/VariableExpression.cs',
    'OpenRA.Mods.Common/Traits/GainsExperience.cs',
    'OpenRA.Mods.Common/Traits/ProducibleWithLevel.cs',
    'OpenRA.Mods.Common/Traits/Conditions/ConditionalTrait.cs',
    'OpenRA.Mods.Common/Traits/Conditions/PausableConditionalTrait.cs',
    'OpenRA.Mods.Common/Traits/Conditions/GrantCondition.cs',
    'OpenRA.Mods.Common/Traits/Armament.cs',
    'OpenRA.Mods.Common/Traits/AmmoPool.cs',
    'OpenRA.Mods.Common/Traits/Multipliers/FirepowerMultiplier.cs',
    'OpenRA.Mods.Common/Traits/Multipliers/ReloadDelayMultiplier.cs',
    'OpenRA.Mods.Common/Traits/Multipliers/RangeMultiplier.cs',
)
ATOM = re.compile(r'([a-zA-Z_][a-zA-Z0-9_-]*)(?:\s*(==|!=|>=|<=|>|<)\s*([0-9]+))?\Z')
PROVIDER_FIELDS = ('Condition', 'AmmoCondition', 'Conditions', 'DeployedCondition',
                   'UndeployedCondition', 'ReloadingCondition')


def condition_value(expression, values):
    """No eval, no absent-variable default, no partial expression acceptance."""
    if expression is None or not expression.strip():
        return True
    if expression.strip().startswith('!'):
        token = expression.strip()[1:].strip()
        match = ATOM.fullmatch(token)
        return not bool(values[token]) if match and match[2] is None and token in values else None
    match = ATOM.fullmatch(expression.strip())
    if not match or match[1] not in values:
        return None
    value, op, target = values[match[1]], match[2], match[3]
    if op is None:
        return bool(value)
    target = int(target)
    return {'==': value == target, '!=': value != target, '>=': value >= target,
            '<=': value <= target, '>': value > target, '<': value < target}[op]


def weapon_modifiers(node, values, *, evaluator=condition_value):
    modifiers = []
    for item in node.children:
        if item.key.split('@')[0] not in ('FirepowerMultiplier', 'ReloadDelayMultiplier', 'RangeMultiplier'):
            continue
        raw = item.get('Modifier')
        enabled = evaluator(item.get('RequiresCondition'), values)
        valid = raw is not None and re.fullmatch(r'[0-9]+', raw) is not None
        modifiers.append({'trait': item.key, 'requires_condition': item.get('RequiresCondition'),
                          'enabled': enabled, 'authored_modifier': raw,
                          'effective_modifier': (int(raw) if enabled else 100)
                          if valid and enabled is not None else None})
    return modifiers


def activation_gates(node, values, *, evaluator=condition_value):
    """Trait gates only: not CanFire, targeting, facing, ammo or cadence proof."""
    slots = []
    for item in node.children:
        if item.key.split('@')[0] != 'Armament':
            continue
        enabled = evaluator(item.get('RequiresCondition'), values)
        pause = item.get('PauseOnCondition')
        paused = evaluator(pause, values) if pause and pause.strip() else False
        opened = (False if enabled is False or paused is True else
                  None if enabled is None or paused is None else True)
        slots.append({'trait': item.key, 'weapon': item.get('Weapon'),
                      'requires_condition': item.get('RequiresCondition'),
                      'pause_on_condition': pause, 'enabled': enabled, 'paused': paused,
                      'activation_gate_open': opened})
    return slots


def creation_ammo(node):
    """Exact AmmoPool creation defaults/counts, not sustained reload or max-rank ammo."""
    counts, pools, holds = {}, [], []
    pool_nodes = [c for c in node.children if c.key.split('@')[0] == 'AmmoPool']
    uncertain = set()
    for item in pool_nodes:
        condition = item.get('AmmoCondition')
        ammo, initial = item.get('Ammo') or '1', item.get('InitialAmmo') or '-1'
        row = {'trait': item.key, 'condition': condition, 'ammo': ammo, 'initial_ammo': initial,
               'creation_count': None}
        pools.append(row)
        if not condition:
            continue
        if not re.fullmatch(r'[0-9]+', ammo) or not re.fullmatch(r'-?[0-9]+', initial):
            uncertain.add(condition)
            holds.append(f'{item.key}: unsupported ammo value')
            continue
        maximum, declared = int(ammo), int(initial)
        count = declared if 0 <= declared < maximum else maximum
        row['creation_count'] = count
        counts[condition] = counts.get(condition, 0) + count
    for item in node.children:
        if item in pool_nodes:
            continue
        for field in item.children:
            if field.key in PROVIDER_FIELDS:
                candidates = {field.value} | {x.value for x in field.children}
                uncertain.update(candidates & counts.keys())
    for condition in uncertain:
        counts.pop(condition, None)
        holds.append(f'{condition}: condition count unresolved or another provider exists')
    return {'condition_counts': counts, 'pools': pools, 'holds': holds}


def project(node):
    ammo = creation_ammo(node)
    result = {'scope': 'rank-only projection, not complete factory/max-upgrade state',
              'factory_state_certification': 'none', 'max_state_certification': 'none',
              'scenario': 'fresh actor ExperienceInit=0; no production level override; no external rank grants',
              'scenario_independent_activation': activation_gates(node, {}),
              'scenario_independent_modifiers': weapon_modifiers(node, {}),
              'creation_ammo_evidence': ammo,
              'creation_armament_activation': activation_gates(node, ammo['condition_counts']),
              'states': [], 'holds': []}
    gains = [c for c in node.children if c.key.split('@')[0] == 'GainsExperience']
    if len(gains) != 1:
        result['status'] = 'no_single_rank_track'
        return result
    if any(c.key.split('@')[0] == 'ProducibleWithLevel' for c in node.children):
        result['status'] = 'scenario_required'
        result['holds'] = ['ProducibleWithLevel can change creation rank; player prerequisites not evaluated']
        return result
    conditions = next((c for c in gains[0].children if c.key == 'Conditions'), None)
    entries = conditions.children if conditions else []
    if not entries or any(not c.key.isdigit() or int(c.key) <= 0 or not ATOM.fullmatch(c.value)
                          or ATOM.fullmatch(c.value)[2] for c in entries):
        result['status'] = 'unsupported_rank_conditions'
        return result
    thresholds = [int(c.key) for c in entries]
    if thresholds != sorted(set(thresholds)):
        result['status'] = 'unsupported_rank_order'
        return result
    names = {c.value for c in entries}
    grants = [c for c in node.children if c.key.split('@')[0] == 'GrantCondition']
    # Identify only the closure of simple rank-dependent grants. Unrelated grant
    # conditions remain unknown and cannot affect the rank-only numeric result.
    selected = []
    pending = list(grants)
    while pending:
        ready = [c for c in pending if (m := ATOM.fullmatch((c.get('RequiresCondition') or '').strip()))
                 and m[1] in names]
        if not ready:
            break
        for item in ready:
            target = item.get('Condition')
            if not target or not ATOM.fullmatch(target) or ATOM.fullmatch(target)[2] or target in names:
                result['status'] = 'ambiguous_rank_provider'
                return result
            if (item.get('GrantPermanently') or 'false').lower() != 'false':
                result['status'] = 'history_dependent_rank_grant'
                return result
            names.add(target)
            selected.append(item)
            pending.remove(item)
    # Another provider of a rank condition invalidates the closed rank projection.
    for item in node.children:
        if item in gains or item in selected:
            continue
        if any(c.key in PROVIDER_FIELDS and
               (c.value in names or any(x.value in names for x in c.children)) for c in item.children):
            result['status'] = 'ambiguous_rank_provider'
            return result
    for label, level in (('unranked', 0), ('maximum_rank', len(entries))):
        values = {name: 0 for name in names}
        for item in entries[:level]:
            values[item.value] += 1
        for item in selected:
            values[item.get('Condition')] = int(condition_value(item.get('RequiresCondition'), values))
        if level == 0:
            values.update(ammo['condition_counts'])
        result['states'].append({'name': label, 'level': level, 'condition_counts': values,
                                 'weapon_modifiers': weapon_modifiers(node, values),
                                 'armament_activation': activation_gates(node, values)})
    result['status'] = 'rank_axis_evaluated'
    result['holds'] = ['not purchase eligibility or complete upgrade compatibility',
                       'non-rank modifiers and weapon operation remain separate; no DPS certified']
    return result


def build(source):
    source = pathlib.Path(source).resolve()
    before = peer.git_identity(source)
    if before['checkout_head'] != PIN or before['checkout_dirty'] is not False:
        raise ValueError('requires exact clean reviewed OpenRA source revision')
    inputs = set(ENGINE_FILES)
    for mod in MODS:
        inputs.update(peer.collect_read_inputs(source, mod))
    # collect_read_inputs returns relative-path mappings; preserve the exact bytes
    # of both YAML and inspected engine semantics, and refuse changes during read.
    paths = {str(p): source / p for p in inputs}
    if any(not path.resolve().is_relative_to(source) for path in paths.values()):
        raise ValueError('source input escapes checkout')
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    rows = []
    for mod in MODS:
        _label, data, error = peer.extract(mod, root_override=source)
        if error:
            raise ValueError(error)
        rules = peer.miniyaml.Ruleset(source, mod_id=mod)
        rows.extend({'mod': mod, 'actor': row['id'], **project(rules.resolve(row['id']))}
                    for row in data['rows'])
    after_inputs = set(ENGINE_FILES)
    for mod in MODS:
        after_inputs.update(peer.collect_read_inputs(source, mod))
    if after_inputs != inputs or peer.git_identity(source) != before or any(
            hashlib.sha256(path.read_bytes()).hexdigest() != hashes[name] for name, path in paths.items()):
        raise ValueError('source changed during rank projection')
    return {'schema': 1, 'source_commit': PIN, 'source_inputs': hashes,
            'status_counts': dict(collections.Counter(row['status'] for row in rows)), 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    document = build(args.source)
    text = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + '\n'
    out, identical = peer.ensure_external_output(args.output, text, [pathlib.Path(args.source), peer.ROOT])
    if not identical:
        with out.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
    print(json.dumps(document['status_counts'], sort_keys=True))


if __name__ == '__main__':
    main()
