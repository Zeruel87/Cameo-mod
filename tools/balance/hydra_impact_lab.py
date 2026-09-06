"""Bounded, offline Hydra impact experiment. Never edits gameplay or pricing.

Models one positional enemy impact, fixed edge distance, base unshielded actors,
ordered warheads, TakeCover and Corrosion feedback. Targets are held alive so
overkill cannot conceal differences: numbers are potential damage, not HP lost,
kills, sustained DPS or a substitute for an engine/gameplay test.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from math import prod
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
from miniyaml import Node, Ruleset
from formula import condition_holds_by_default
from effective_damage import falloff_and_radii, runtime_falloff
import percentage_damage as pd
from hydra_candidate_screen import candidate, TARGETS


def trunc_div(a, b):
    return (abs(a) // abs(b)) * (-1 if (a < 0) != (b < 0) else 1)


def modifiers(value, factors):
    """One final truncation, not one per factor (Util.ApplyPercentageModifiers)."""
    factors = tuple(factors)
    return trunc_div(value * prod(factors), 100 ** len(factors))


def f32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


def enabled(node):
    # Explicit scenario: every named condition starts at zero. Not a general
    # condition/upgrade solver; dynamically granted conditions are out of scope.
    return condition_holds_by_default(node.get('RequiresCondition'))


def split(value):
    return tuple(x.strip() for x in (value or '').split(',') if x.strip())


@dataclass
class Target:
    name: str
    hp: int
    armor: str
    incoming: tuple[int, ...] = ()
    cover: dict[str, int] = field(default_factory=dict)
    triggers: tuple[str, ...] = ()
    corrosion: dict | None = None
    vulnerability: dict | None = None


def target_from_actor(actor):
    armors = [n.get('Type') for n in actor.children_named('Armor') if enabled(n)]
    if len(armors) != 1:
        raise ValueError(f'{actor.key}: scenario requires exactly one enabled class armor: {armors}')
    states = [n for n in actor.children_named('PhysicalState')
              if n.get('Name') == 'Corrosion' and enabled(n)]
    state = None
    if states:
        n = states[0]
        state = {k: int(n.get(k) or default) for k, default in (
            ('MinValue', 0), ('MaxValue', 100), ('InitialValue', 0), ('RelaxedValue', 0))}
        state['RelativeToHealth'] = n.get('RelativeToHealth') == 'true'
        state['ApplyDamageModifiers'] = n.get('ApplyDamageModifiers') == 'true'
    vulnerability = None
    for n in actor.children_named('DamageMultiplierProportionalToPhysicalState'):
        if n.get('PhysicalStateName') == 'Corrosion':
            condition = n.get('RequiresCondition')
            grant = next((g for g in actor.children_named('GrantConditionOnPhysicalState')
                          if g.get('PhysicalStateName') == 'Corrosion'
                          and g.get('Condition') == condition and enabled(g)), None)
            if condition and grant is None:
                raise ValueError(f'Unsupported dynamic Corrosion condition: {condition}')
            vulnerability = {
                'min': int(n.get('DamageMultiplierAtMinimum') or 100),
                'max': int(n.get('DamageMultiplierAtMaximum') or 1000),
                'deviation': n.get('UseDeviationFromRelaxed') == 'true',
                'active_range': (int(grant.get('LowerValue') or 0), int(grant.get('UpperValue') or 100)) if grant else None}
    cover = next((n for n in actor.children_named('TakeCover') if enabled(n)), None)
    return Target(actor.key, int(actor.get('Health', 'HP')), armors[0],
                  tuple(int(n.get('Modifier')) for n in actor.children_named('DamageMultiplier') if enabled(n)),
                  {} if cover is None else pd.versus_table(cover, 'DamageModifiers'),
                  () if cover is None else split(cover.get('DamageTriggers')),
                  state, vulnerability)


def vulnerability_at(target, meter):
    if target.corrosion is None or target.vulnerability is None:
        return 100
    info, v = target.corrosion, target.vulnerability
    if v.get('active_range') is not None and not v['active_range'][0] <= meter <= v['active_range'][1]:
        return 100
    if v['deviation']:
        offset = meter - info['RelaxedValue']
        span = (info['MaxValue'] - info['RelaxedValue'] if offset >= 0
                else info['RelaxedValue'] - info['MinValue'])
        normalized = f32(abs(offset) / span) if span else 0
    else:
        span = info['MaxValue'] - info['MinValue']
        normalized = f32((meter - info['MinValue']) / span) if span else 0
    return int(f32(v['min'] + f32((v['max'] - v['min']) * normalized)))


def state_bindings(node):
    values = []
    if node.get('PhysicalStateName') == 'Corrosion':
        values.append(int(node.get('PhysicalStateScale') or 0))
    values.append(int(node.get('PhysicalStates', 'Corrosion') or 0))
    return [x for x in values if x]


def change_meter(target, meter, amount):
    if target.corrosion is None:
        return meter
    info = target.corrosion
    if info['RelativeToHealth']:
        amount = trunc_div(amount * (info['MaxValue'] - info['MinValue']), target.hp)
    if info['ApplyDamageModifiers']:
        amount = modifiers(amount, (*target.incoming, vulnerability_at(target, meter)))
    return max(info['MinValue'], min(info['MaxValue'], meter + amount))


def impact(weapon, target, firepower, distance=0, initial_prone=False,
           initial_corrosion=None):
    """Return ordered potential damage and state, holding the victim alive.

    No ticks elapse, so no DoT, healing, state relaxation or subsequent shots.
    No shields, armor upgrades, alliances, projectile misses, player bonuses,
    directional armor or world spatial-search/hitshape-discovery simulation.
    """
    meter = (target.corrosion['InitialValue'] if target.corrosion else 0)
    if initial_corrosion is not None:
        meter = initial_corrosion
    prone = initial_prone
    trace = []
    for node in weapon.children:
        if node.value not in ('AreaDamage', 'SpreadDamage', 'AreaDamagePercentage'):
            continue
        if int(node.get('Ticks') or 1) != 1 or node.get('DamageCalculationType') not in (None, 'HitShape'):
            raise ValueError('Only single-tick hitshape-distance warheads are modeled')
        fo, radii, _ = falloff_and_radii(node)
        falloff = runtime_falloff(fo, radii, distance)
        if falloff == 0:
            continue
        applications = [('percentage' if node.value == 'AreaDamagePercentage' else 'flat',
                         int(node.get('Damage') or 0), pd.versus_table(node),
                         int(node.get('PercentageDenominator') or 100))]
        scale = int(node.get('PercentageScale') or 0)
        if node.value == 'AreaDamage' and scale > 0 and distance <= radii[-1] * int(node.get('PercentageSpread') or 50) // 100:
            _, units = pd.folded_units(int(node.get('Damage')), scale)
            applications.append(('percentage', units,
                                 pd.versus_table(node, 'PercentageVersus') or pd.versus_table(node),
                                 int(node.get('PercentageDenominator') or 10000)))
        damage_types = split(node.get('DamageTypes'))
        for kind, units, table, denominator in applications:
            factors = (*firepower, falloff, table.get(target.armor, 100))
            raw = (modifiers(units, factors) if kind == 'flat' else
                   trunc_div(modifiers(target.hp, (*factors, units)) * 100, denominator))
            cover = (modifiers(100, [target.cover[x] for x in damage_types if x in target.cover])
                     if prone else 100)
            vulnerability = vulnerability_at(target, meter)
            taken = modifiers(raw, (*target.incoming, cover, vulnerability))
            meter_before = meter
            if taken > 0 and set(damage_types).intersection(target.triggers):
                prone = True
            state_steps = []
            if node.value != 'SpreadDamage':
                for percentage in state_bindings(node):
                    before = meter
                    meter = change_meter(target, meter, trunc_div(raw * percentage, 100))
                    state_steps.append([percentage, before, meter])
            trace.append(dict(tag=node.key, kind=kind, pre_defense=raw,
                              potential_damage=taken, cover=cover, vulnerability=vulnerability,
                              meter_before=meter_before, meter_after=meter, state_steps=state_steps))
    return dict(flat=sum(t['potential_damage'] for t in trace if t['kind'] == 'flat'),
                percentage=sum(t['potential_damage'] for t in trace if t['kind'] == 'percentage'),
                total=sum(t['potential_damage'] for t in trace),
                corrosion=meter if target.corrosion else None, trace=trace)


def replace(node, key, value):
    existing = node.child(key)
    if existing is None:
        node.children.append(Node(key, str(value)))
    else:
        existing.value = str(value)


def make_variants(current):
    staged = candidate(72000, 10000)
    scaled = candidate(33000, 2098)
    # Explicit role experiment, not a new generated canonical family. Retains
    # roughly the old nominal air rows at 33000, independently of ground rows.
    air_restored = candidate(33000, 2098)
    for armor, value in {'Fighter':120, 'Bomber':117, 'Helicopter':113, 'Spaceship':107}.items():
        replace(air_restored.children[0].child('Versus'), armor, value)
    # Isolate secondary effects: preserve current standalone percentage nodes
    # instead of forcing four response tables into one scaling constant.
    payload_control = air_restored.deep_copy()
    replace(payload_control.children[0], 'PercentageScale', 0)
    payload_control.children.extend(n.deep_copy() for n in current.children if n.value == 'AreaDamagePercentage')
    # Center-impact control: retain the original chemical pre-hit/state routes;
    # combine only the three other flat profiles. Geometry is NOT equivalent.
    two_stage = Node('two_stage', '', [])
    others = [n for n in current.children if n.value == 'SpreadDamage']
    merged = others[0].deep_copy()
    merged.key = 'Warhead@NonChemicalCenterControl'
    replace(merged, 'Damage', sum(int(n.get('Damage')) for n in others))
    keys = set().union(*(pd.versus_table(n) for n in others))
    merged.child('Versus').children = [Node(k, str(sum(pd.versus_table(n).get(k,100) for n in others)//3)) for k in sorted(keys)]
    for n in current.children:
        if n.value == 'AreaDamage' or n.value == 'AreaDamagePercentage':
            two_stage.children.append(n.deep_copy())
            if n.key == 'Warhead@LightChemicalWeaponPercentage':
                two_stage.children.append(merged)
    for weapon in (staged, scaled, air_restored, payload_control):
        replace(weapon.children[0], 'DamageTypes', 'Prone75Percent, TriggerProne, TiberiumDeath')
    return {'current':current, 'staged_72000':staged, 'scaled_33000':scaled,
            'air_restored_33000':air_restored, 'percentage_control':payload_control,
            'two_stage_control':two_stage}


def build():
    rules = Ruleset(ROOT)
    current = rules.resolve_weapon('HydraSpit')
    shooter = rules.resolve('zerg_hydralisk')
    firepower = tuple(int(n.get('Modifier')) for n in shooter.children_named('FirepowerMultiplier') if enabled(n))
    targets = [target_from_actor(rules.resolve(name)) for name in TARGETS]
    variants = make_variants(current)
    results = {target.name: {key: {str(d):impact(v,target,firepower,d) for d in (0,55,110,220,350)}
                            for key,v in variants.items()} for target in targets}
    return dict(schema=1, assumptions='potential single enemy positional impact; victim held alive; no ticks, shields or upgrades',
                shooter_firepower=list(firepower), targets=[vars(t) for t in targets],
                variants=list(variants), results=results)


def render(data):
    lines = ['# Hydralisk ordered-impact laboratory', '',
        'Offline experiment only; no candidate is applied to gameplay.',
        'Source baseline: 4deaee086. Staged BulletChem rows: PR325 e42eb991.', '',
        '## Scenario and limits', '',
        'One enemy positional impact at a stated distance from the target hitshape edge.',
        'Actors start unupgraded, unshielded, standing, with zero Corrosion; external conditions',
        'start at zero, while the Corroding condition follows its authored meter thresholds.',
        'Hydra outgoing modifiers: ' + ', '.join(map(str,data['shooter_firepower'])) + '%.',
        'Includes selected actor incoming modifiers, ordered TakeCover activation, individual',
        'state bindings, health-relative state scaling, clamping and immediate Corrosion vulnerability.',
        '**Victims are held alive for the whole impact**: results are potential damage, not',
        'actual HP removed, kills, DPS or time-to-kill. No tick effects, DoT, relaxation, shields,',
        'world hitshape discovery, target eligibility or projectile interception is simulated.',
        'This is a source-derived Python projection, not engine execution or playtest evidence.', '',
        '## Close-impact potential damage', '',
        '| Target | Current | Staged 72000 | Scaled 33000 | Air-restored 33000 | Percentage control | Two-stage control |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for target in data['targets']:
        results = data['results'][target['name']]
        baseline = results['current']['0']['total']
        cells = [str(baseline)] + [f"{results[k]['0']['total']} ({results[k]['0']['total']/baseline:.2f}x)" for k in data['variants'][1:]]
        lines.append('| ' + target['name'] + ' | ' + ' | '.join(cells) + ' |')
    lines += ['', '## Corrosion meter after the complete potential impact', '',
        'Meter units are not HP damage. No meter means no received Corrosion; cap is 20000.',
        'Held-alive assumption still applies, including to low-HP targets.', '',
        '| Target | Current | Staged | Scaled | Air-restored | Percentage control | Two-stage |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for target in data['targets']:
        cells = [data['results'][target['name']][k]['0']['corrosion'] for k in data['variants']]
        lines.append('| ' + target['name'] + ' | ' + ' | '.join('no meter' if x is None else str(x) for x in cells) + ' |')
    lines += ['', '## Distance sensitivity: potential damage, not crowd effectiveness', '',
        '| Target / distance | Current | Air-restored | Two-stage control |', '|---|---:|---:|---:|']
    for target in ('terran_marine','ra1_allies_alliedmediumtank','terran_wraith'):
        for d in ('0','55','110','220','350'):
            cells = [str(data['results'][target][k][d]['total']) for k in ('current','air_restored_33000','two_stage_control')]
            lines.append(f'| {target} / {d} | ' + ' | '.join(cells) + ' |')
    lines += ['', '## What the controls mean', '',
        '- Scaled 33000 uses the staged shape, 20% Corrosion and PercentageScale 2098.',
        '- Air-restored changes only four nominal flat air rows (120/117/113/107). It is',
        '  a bespoke role experiment, not a generated canonical family or exact preservation.',
        '- Percentage control restores the four original percentage nodes. It demonstrates',
        '  why percentage payload choice is separate from flat damage; geometry/order still differ.',
        '- Two-stage control retains the original chemical flat pre-hit and four percentage hits,',
        '  combining the other three flat profiles. This is a close-impact diagnostic only:',
        '  it borrows missile geometry and changes targeting/death-type behavior. Not a safe patch.',
        '- Every new single-main candidate loses parts of the current distributed splash.', '',
        'The JSON companion contains individual applications, defense modifiers and meter changes.',
        'No candidate is approved; do not regenerate weapon families or remove Hydra guards based on this report.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    data = build()
    if args.write:
        (ROOT/'docs/design/HYDRALISK_IMPACT_LAB.md').write_text(render(data), encoding='utf-8')
        (ROOT/'docs/audit/latest/hydralisk_impact_lab.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    else:
        print(render(data))
