"""Explicit, settled non-rank condition views from the co-pinned base OpenRA source.

Inputs describe resolved player prerequisite keys and current effective terrain;
they do not certify that a player can acquire them or that the actor can reach it.
Unknown providers, permanent grants and cycles remain unknown. No DPS is emitted.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import re

import extract_peer_rank_states as rank

ENGINE_FILES = (
    'OpenRA.Mods.Common/Traits/Conditions/GrantConditionOnPrerequisite.cs',
    'OpenRA.Mods.Common/Traits/Player/GrantConditionOnPrerequisiteManager.cs',
    'OpenRA.Mods.Common/Traits/Player/TechTree.cs',
    'OpenRA.Mods.Common/Traits/Conditions/GrantConditionOnTerrain.cs',
    'OpenRA.Mods.Common/Traits/Conditions/GrantConditionOnDamageState.cs',
    'OpenRA.Game/Traits/TraitsInterfaces.cs',
    'OpenRA.Mods.Common/Traits/Conditions/GrantConditionOnDeploy.cs',
    'OpenRA.Mods.Common/Traits/Pluggable.cs',
    'OpenRA.Mods.Common/Traits/Conditions/GrantConditionOnLayer.cs',
    'OpenRA.Mods.Common/Traits/Conditions/GrantConditionOnSubterraneanLayer.cs',
    'OpenRA.Mods.Common/Traits/Conditions/GrantConditionOnAttack.cs',
)
KEY = re.compile(r'[a-zA-Z_][a-zA-Z0-9_.-]*\Z')
ATOM = re.compile(r'([a-zA-Z_][a-zA-Z0-9_.-]*)(?:\s*(==|!=|>=|<=|>|<)\s*([0-9]+))?\Z')
DAMAGE_STATES = {'Undamaged', 'Light', 'Medium', 'Heavy', 'Critical', 'Dead'}


def damage_count(item, state):
    if state is None or (item.get('GrantPermanently') or 'false').lower() != 'false':
        return None
    allowed = {x.strip() for x in (item.get('ValidDamageStates') or 'Heavy, Critical').split(',')}
    return int(state in allowed) if allowed <= DAMAGE_STATES else None


def condition_value(expression, values):
    """Bounded &&/|| grammar; no absent-variable defaults or partial parsing.

    AND binds tighter than OR in the inspected VariableExpression implementation.
    Parentheses/arithmetic are deliberately withheld. Even logically redundant
    unknown terms stay unknown, so this never proves absence of an unknown state.
    """
    if expression is None or not expression.strip():
        return True
    groups = []
    for group in expression.split('||'):
        terms = []
        for term in group.split('&&'):
            if not term.strip():
                return None
            term = term.strip()
            if term.startswith('!') and KEY.fullmatch(term[1:].strip()):
                key = term[1:].strip()
                value = not bool(values[key]) if key in values else None
            else:
                match = ATOM.fullmatch(term)
                value = None
                if match and match[1] in values:
                    count, op, target = values[match[1]], match[2], match[3]
                    if op is None:
                        value = bool(count)
                    else:
                        target = int(target)
                        value = {'==': count == target, '!=': count != target, '>=': count >= target,
                                 '<=': count <= target, '>': count > target, '<': count < target}[op]
            if value is None:
                return None
            terms.append(value)
        groups.append(all(terms))
    return any(groups)


def project(node, *, prerequisites=None, terrain=None, rank_state=None,
            damage_state=None, deploy_states=None, plugs=None,
            subterranean_position=None, fresh_no_attacks=None):
    """A single explicit scenario; never combine incompatible scenario outputs.

    prerequisites=None means unknown; [] means explicitly no provided keys.
    terrain is the effective, in-map terrain after the terrain trait has ticked.
    rank_state optionally selects one already-supported rank-axis projection.
    """
    if prerequisites is not None and (not isinstance(prerequisites, list) or
            any(not isinstance(x, str) or not KEY.fullmatch(x) for x in prerequisites)):
        raise ValueError('prerequisites must be an explicit list of resolved keys')
    if terrain is not None and (not isinstance(terrain, str) or not KEY.fullmatch(terrain)):
        raise ValueError('terrain must be an effective terrain name')
    if damage_state is not None and (not isinstance(damage_state, str) or damage_state not in DAMAGE_STATES):
        raise ValueError('damage_state must be one exact source DamageState')
    if fresh_no_attacks is not None and type(fresh_no_attacks) is not bool:
        raise ValueError('fresh_no_attacks must be boolean or omitted')
    if fresh_no_attacks is True and rank_state == 'maximum_rank':
        raise ValueError('fresh no-attack scenario cannot assert the earned maximum-rank history')
    if subterranean_position is not None and subterranean_position not in (
            'after-position-change-below-threshold-on-subterranean',
            'after-position-change-above-threshold-off-subterranean'):
        raise ValueError('subterranean position must specify a proven post-event threshold side')
    for mapping, kind in ((deploy_states, 'GrantConditionOnDeploy'), (plugs, 'Pluggable')):
        if mapping is not None and (not isinstance(mapping, dict) or
                any(k not in {x.key for x in node.children if x.key.split('@')[0] == kind}
                    for k in mapping)):
            raise ValueError(f'{kind}: expected exact trait-key mapping')
    if deploy_states and any(value not in ('Deployed', 'Undeployed') for value in deploy_states.values()):
        raise ValueError('deploy states require completed Deployed or Undeployed; transitions are history-dependent')
    for item in node.children:
        if plugs and item.key in plugs:
            options = next((x for x in item.children if x.key == 'Conditions'), None)
            accepted = {x.key for x in options.children} if options else set()
            if not isinstance(plugs[item.key], str) or plugs[item.key] not in accepted | {''}:
                raise ValueError('one accepted active plug per socket, or explicit empty string, is required')
    values, holds = {}, []
    if rank_state is not None:
        projection = rank.project(node)
        state = next((s for s in projection['states'] if s['name'] == rank_state), None)
        if state is None:
            raise ValueError('requested rank axis is not supported for this actor')
        # A settled scenario does not assert fresh ammunition or combat history.
        ammo_names = rank.creation_ammo(node)['condition_counts']
        values.update({k: v for k, v in state['condition_counts'].items() if k not in ammo_names})

    providers = collections.defaultdict(list)
    for item in node.children:
        for field in item.children:
            if field.key in rank.PROVIDER_FIELDS:
                for name in ([field.value] if field.value else []) + [x.value for x in field.children]:
                    if name:
                        providers[name].append(item)

    pending = {}
    for name, items in providers.items():
        if name in values:
            continue  # rank.project already verified all providers of these names
        if len(items) != 1:
            if all(x.key.split('@')[0] == 'GrantConditionOnDamageState' for x in items):
                counts = [damage_count(x, damage_state) for x in items]
                if all(x is not None for x in counts):
                    values[name] = sum(counts)
                    continue
            holds.append(f'{name}: multiple providers; count unresolved')
            continue
        item = items[0]
        kind = item.key.split('@')[0]
        if kind == 'GrantConditionOnPrerequisite':
            raw = item.get('Prerequisites')
            keys = [x.strip() for x in raw.split(',')] if raw else []
            if not keys:
                values[name] = 0  # empty arrays do not register with the manager
            elif prerequisites is not None and all(re.fullmatch(r'~?!?[a-zA-Z_][a-zA-Z0-9_.-]*', x) for x in keys):
                values[name] = int(all((x.replace('~', '').startswith('!')) !=
                    (x.replace('~', '').replace('!', '') in prerequisites) for x in keys))
            else:
                holds.append(f'{name}: resolved player prerequisites required or unsupported declaration')
        elif kind == 'GrantConditionOnTerrain':
            raw = item.get('TerrainTypes')
            if terrain is not None and raw:
                values[name] = int(terrain in [x.strip() for x in raw.split(',')])
            else:
                holds.append(f'{name}: effective in-map terrain after tick required')
        elif kind == 'GrantConditionOnDamageState' and damage_count(item, damage_state) is not None:
            values[name] = damage_count(item, damage_state)
        elif kind == 'GrantConditionOnDeploy' and deploy_states is not None and item.key in deploy_states:
            field = 'DeployedCondition' if deploy_states[item.key] == 'Deployed' else 'UndeployedCondition'
            values[name] = int(item.get(field) == name)
        elif kind == 'Pluggable' and plugs is not None and item.key in plugs:
            mapping = next(x for x in item.children if x.key == 'Conditions')
            selected = next((x.value for x in mapping.children if x.key == plugs[item.key]), None)
            values[name] = int(selected == name)
        elif kind == 'GrantConditionOnSubterraneanLayer' and subterranean_position is not None and not item.get('RequiresCondition'):
            # CenterPositionChanged grants below the threshold on the custom layer,
            # revokes above it off-layer; equality and other combinations retain history.
            values[name] = int(subterranean_position == 'after-position-change-below-threshold-on-subterranean')
        elif kind == 'GrantConditionOnAttack' and fresh_no_attacks is True:
            values[name] = 0  # token stack is constructed empty; no attacks have run
        elif kind == 'Armament' and fresh_no_attacks is True:
            values[name] = 0  # base Armament FireDelay starts at zero; disabled does not grant reload
        elif kind == 'GrantCondition' and (item.get('GrantPermanently') or 'false').lower() == 'false':
            pending[name] = item
        else:
            holds.append(f'{name}: unsupported or history-dependent provider {item.key}')

    while pending:
        ready = {name: condition_value(item.get('RequiresCondition'), values)
                 for name, item in pending.items()}
        ready = {name: value for name, value in ready.items() if value is not None}
        if not ready:
            break
        for name, value in ready.items():
            values[name] = int(value)
            del pending[name]
    holds.extend(f'{name}: unresolved grant dependency, cycle or expression' for name in pending)
    # Reuse the stable record shape with the extended, conservative expression
    # evaluator passed explicitly rather than mutating the rank module globally.
    return {'scope': 'explicit settled condition scenario; not availability or whole-unit operation',
            'scenario': {'resolved_player_prerequisites': prerequisites,
                         'effective_in_map_terrain_after_tick': terrain, 'rank_state': rank_state},
            'explicit_dynamic_inputs': {'damage_state': damage_state, 'completed_deploy_states': deploy_states,
                'active_plugs': plugs, 'subterranean_position': subterranean_position,
                'fresh_no_attacks': fresh_no_attacks},
            'condition_counts': values,
            'weapon_modifiers': rank.weapon_modifiers(node, values, evaluator=condition_value),
            'armament_activation': rank.activation_gates(node, values, evaluator=condition_value),
            'holds': sorted(holds), 'factory_state_certification': 'none',
            'max_state_certification': 'none'}


def build(source, scenarios):
    """Verify source identity and every read input before/after explicit views."""
    source = pathlib.Path(source).resolve()
    if not isinstance(scenarios, list) or any(not isinstance(x, dict) for x in scenarios):
        raise ValueError('scenarios must be an array of scenario objects')
    if len({x.get('name') for x in scenarios}) != len(scenarios):
        raise ValueError('scenario names must be unique')
    identity = rank.peer.git_identity(source)
    if identity['checkout_head'] != rank.PIN or identity['checkout_dirty'] is not False:
        raise ValueError('requires exact clean reviewed OpenRA source revision')
    inputs = set(rank.ENGINE_FILES) | set(ENGINE_FILES)
    for mod in rank.MODS:
        inputs.update(rank.peer.collect_read_inputs(source, mod))
    paths = {name: source / name for name in inputs}
    if any(not p.resolve().is_relative_to(source) for p in paths.values()):
        raise ValueError('source input escapes checkout')
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    rows = []
    for scenario in scenarios:
        fields = {'prerequisites', 'terrain', 'rank_state', 'damage_state', 'deploy_states',
                  'plugs', 'subterranean_position', 'fresh_no_attacks'}
        if set(scenario) - ({'name', 'mod', 'actor'} | fields):
            raise ValueError('unknown scenario fields')
        if scenario.get('mod') not in rank.MODS or not scenario.get('name') or not scenario.get('actor'):
            raise ValueError('scenario needs name, supported mod and actor')
        rules = rank.peer.miniyaml.Ruleset(source, mod_id=scenario['mod'])
        rows.append({'name': scenario['name'], 'mod': scenario['mod'], 'actor': scenario['actor'],
                     **project(rules.resolve(scenario['actor']), **{k: scenario[k] for k in fields if k in scenario})})
    after = set(rank.ENGINE_FILES) | set(ENGINE_FILES)
    for mod in rank.MODS:
        after.update(rank.peer.collect_read_inputs(source, mod))
    if after != inputs or rank.peer.git_identity(source) != identity or any(
            hashlib.sha256(path.read_bytes()).hexdigest() != hashes[name] for name, path in paths.items()):
        raise ValueError('source changed during scenario projection')
    return {'schema': 1, 'source_commit': rank.PIN, 'source_inputs': hashes, 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--scenarios', required=True, help='JSON array of explicit scenarios')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    scenarios = json.loads(pathlib.Path(args.scenarios).read_text(encoding='utf-8'))
    document = build(args.source, scenarios)
    text = json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + '\n'
    out, identical = rank.peer.ensure_external_output(args.output, text, [pathlib.Path(args.source), rank.peer.ROOT])
    if not identical:
        with out.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
    print(f'{len(document["rows"])} explicit views; no whole-unit certification')


if __name__ == '__main__':
    main()
