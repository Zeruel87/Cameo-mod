"""Opt-in single-weapon nominal flat-DPS proposal. Prints JSON; never writes YAML.

Targets are engine damage units per simulation tick, before armor/falloff/defenses,
not effective combat DPS or formula prices. Old class/range generators stay gated.
"""
import argparse
import copy
from fractions import Fraction
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/audit'))
from miniyaml import Ruleset, Node
import formula
from extract_stats import resolved_firepower_modifiers

MAX_DAMAGE = 2**31 - 1
STEP = 100
COSMETIC = {'CreateEffect', 'LeaveSmudge'}
COSMETIC_ACTOR = {'ReloadArmamentsBar', 'WithChargeSpriteBody'}
PROJECTILES = {'Bullet', 'Missile', 'InstantHit', 'InstantHitWithFakeBullets'}
ATTACKS = {'AttackFrontal', 'AttackTurreted', 'AttackFollow', 'AttackMove', 'AttackWander'}
OWN_ATTACKS = {'AttackFrontal', 'AttackTurreted', 'AttackFollow'}


def selected_names(attack):
    """AttackBaseInfo default; an explicitly empty list must stay empty."""
    field = attack.child('Armaments')
    return ['primary', 'secondary'] if field is None else [
        s.strip() for s in field.value.split(',') if s.strip()]


def simple_condition_at_zero(expr):
    """Conservative one-token condition snapshot; None means unknown, not false.

    This is not an as-built condition resolver. Every named condition is assumed
    zero, and compound/arithmetic expressions deliberately require manual review.
    """
    match = re.fullmatch(r'\s*(!\s*)?([A-Za-z_][A-Za-z0-9_.-]*|[01])\s*', expr or '')
    if match is None:
        return None
    value = match[2] == '1'
    return not value if match[1] else value


def attack_activation(attack):
    requires = attack.get('RequiresCondition')
    pause = attack.get('PauseOnCondition')
    enabled = simple_condition_at_zero(requires) if requires else True
    paused = simple_condition_at_zero(pause) if pause else False
    if enabled is False:
        return 'disabled-at-zero-conditions'
    if paused is True:
        return 'paused-at-zero-conditions'
    if enabled is None or paused is None:
        return 'unknown-condition-expression'
    return 'enabled-at-zero-conditions'


class Unsupported(ValueError):
    pass


def shape(node):
    return [node.key, node.value, [shape(c) for c in node.children]]


def fingerprint(node):
    return hashlib.sha256(json.dumps(shape(node), separators=(',', ':')).encode()).hexdigest()


def walk(node, path=()):
    for child in node.children:
        yield path + (child.key,), child
        yield from walk(child, path + (child.key,))


def prospective_actor(rules, name, retire_trait):
    actor = rules.resolve(name)
    local = rules.actor(name)
    if actor is None or local is None or name.startswith('^'):
        raise Unsupported('concrete actor not found')
    if retire_trait is None:
        return actor, actor, None
    allowed = {'FirepowerMultiplier', 'FirepowerMultiplier@' + local.key.lower()}
    if retire_trait.lower() not in {s.lower() for s in allowed}:
        raise Unsupported('retirement must name a local unqualified or actor-specific knob, not a global/class trait')
    own = local.child(retire_trait)
    resolved = actor.child(retire_trait)
    if own is None or own.get('Modifier') is None or resolved is None:
        raise Unsupported('retirement requires an exact locally authored Modifier')
    if resolved.get('RequiresCondition') or resolved.get('Types'):
        raise Unsupported('conditional/scoped modifier retirement is unsupported')
    edited = local.deep_copy()
    edited.children = [c for c in edited.children if c.key != retire_trait]
    view = copy.copy(rules)
    view.actors = dict(rules.actors)
    view.actors[local.key] = edited
    view._resolve_cache = {}
    after = view.resolve(name)
    if after.child(retire_trait) is not None:
        raise Unsupported('removal reveals an inherited same-slot modifier; do not delete the override')
    expected = actor.deep_copy()
    expected.children = [c for c in expected.children if c.key != retire_trait]
    if shape(after) != shape(expected):
        raise Unsupported('prospective actor changes more than the selected trait')
    source = pathlib.Path(own.file)
    try:
        source = source.relative_to(ROOT)
    except ValueError:
        # Synthetic/external source provenance stays absolute when outside ROOT.
        source = pathlib.Path(own.file)
    return actor, after, {'trait': retire_trait, 'modifier': int(resolved.get('Modifier')),
                          'source': source.as_posix()}


def applicable(actor, local, arm):
    name = arm.get('Name') if arm.child('Name') is not None else 'primary'
    return [e for e in resolved_firepower_modifiers(actor, local)
            if not e['types'] or (name and name in e['types'])]


def product(entries):
    factor = Fraction(1)
    for entry in entries:
        value = entry['modifier']
        if not 0 < value <= 10000:
            raise Unsupported('zero, negative or excessive firepower modifier')
        factor *= Fraction(value, 100)
    return factor


def screen(rules, name, retire_trait=None):
    before, after, retired = prospective_actor(rules, name, retire_trait)
    arms = before.children_named('Armament')
    if len(arms) != 1 or not arms[0].get('Weapon'):
        raise Unsupported('requires exactly one actual armament, including alternate/garrison slots')
    arm = arms[0]
    arm_name = arm.get('Name') if arm.child('Name') is not None else 'primary'
    if arm_name != 'primary' or arm.get('RequiresCondition'):
        raise Unsupported('requires an unconditional primary armament')
    if attack_activation(arm) != 'enabled-at-zero-conditions':
        raise Unsupported('primary armament is paused or unknown at zero conditions')
    if arm.get('FireDelay') not in (None, '0') or arm.get('CasingWeapon'):
        raise Unsupported('delayed armament or secondary casing weapon')
    for node in before.children:
        kind = node.key.split('@')[0]
        if kind.startswith('Attack') and kind not in ATTACKS:
            raise Unsupported('unsupported attack cadence: ' + kind)
        if (kind not in COSMETIC_ACTOR and ('Reload' in kind or 'Charge' in kind or 'Ammo' in kind)
                and not node.get('RequiresCondition')):
            raise Unsupported('unmodeled cadence/ammunition trait: ' + kind)
        if 'Firepower' in kind and kind != 'FirepowerMultiplier':
            raise Unsupported('unmodeled firepower trait: ' + kind)
    own_attacks = [node for node in before.children
                   if node.key.split('@')[0] in OWN_ATTACKS and arm_name in selected_names(node)]
    if not own_attacks:
        raise Unsupported('primary armament is not selected by a supported own-actor attack')
    if not any(attack_activation(node) == 'enabled-at-zero-conditions' for node in own_attacks):
        raise Unsupported('selected own-actor attack is disabled, paused or unknown at zero conditions')
    weapon_case = screen_weapon(rules, arm)
    retained = applicable(after, rules.actor(name), arm)
    old = applicable(before, rules.actor(name), arm)
    factor = product(retained)
    if weapon_case['damage'] * product(old) > MAX_DAMAGE:
        raise Unsupported('current modified damage exceeds Int32 capacity')
    return dict(weapon_case, before=before, after=after, arm=arm, retired=retired,
                retained=retained, old_factor=product(old), factor=factor)


def screen_weapon(rules, arm):
    """Weapon-only structural screen, not actor/mode/proposal eligibility."""
    weapon = rules.resolve_weapon(arm.get('Weapon'))
    if weapon is None:
        raise Unsupported('weapon not found')
    projectile = weapon.child('Projectile')
    if projectile is None or projectile.value not in PROJECTILES:
        raise Unsupported('unsupported projectile delivery')
    if any(c.key in {'Bounces', 'BounceCount', 'Repeat', 'RepeatCount'} and c.value not in ('0', '')
           for c in projectile.children):
        raise Unsupported('repeating/bouncing projectile')
    mains = []
    for node in weapon.children_named('Warhead'):
        if node.value in COSMETIC:
            continue
        if node.value not in {'SpreadDamage', 'AreaDamage'}:
            raise Unsupported('non-flat or gameplay side-effect warhead: ' + node.value)
        if node.get('PercentageScale') not in (None, '0'):
            raise Unsupported('folded percentage damage needs a separate inversion model')
        if (node.get('PhysicalStateName') or node.child('PhysicalStates')
                or node.get('IntegrityScale') not in (None, '0')):
            raise Unsupported('physical-state/integrity feedback is unsupported')
        if (node.get('Ticks') not in (None, '1') or node.get('TickDelay') not in (None, '0')
                or node.child('TickDamage') is not None):
            raise Unsupported('scheduled or per-tick damage needs a separate model')
        if node.get('Delay') not in (None, '0'):
            raise Unsupported('delayed damage is unsupported')
        mains.append(node)
    if len(mains) != 1:
        raise Unsupported('requires exactly one flat damage warhead; chips are not discarded')
    damage = int(mains[0].get('Damage') or '0')
    if not 0 < damage <= MAX_DAMAGE:
        raise Unsupported('positive Int32 damage required')
    reload = int(weapon.get('ReloadDelay') or formula.ENGINE_DEFAULT_RELOAD_DELAY)
    burst = int(weapon.get('Burst') or formula.ENGINE_DEFAULT_BURST)
    if reload <= 0 or not 1 <= burst <= 512:
        raise Unsupported('invalid or excessive firing cycle')
    delays = weapon.get('BurstDelays')
    if delays:
        values = [int(s.strip()) for s in delays.split(',')]
        if min(values) < 0 or len(values) not in (1, max(burst - 1, 1)):
            raise Unsupported('invalid burst delays')
    cycle = Fraction(str(formula.eff_reload(reload, burst, delays)))
    return {'weapon': weapon, 'main': mains[0], 'cycle': cycle,
            'burst': burst, 'damage': damage}


def reference_index(rules, weapon_names):
    """Conservative base-YAML token scan, including non-armament refs/inheritance.

    No claim about map overrides or script-built weapon names. Those still require
    manual review; this tool emits no applicable patch.
    """
    targets = {name.lower() for name in weapon_names}
    uses = {name: set() for name in targets}
    for name in rules.actors:
        if name.startswith('^'):
            continue
        for path, node in walk(rules.resolve(name)):
            for target in targets.intersection(v.strip().lower() for v in node.value.split(',')):
                uses[target].add(('actor', name, path))
    for name in rules.weapons:
        for path, node in walk(rules.weapon(name)):
            for target in targets.intersection(v.strip().lower() for v in node.value.split(',')):
                uses[target].add(('weapon', name, path))
    return uses


def sharing(rules, selected_actor, selected_arm, weapon_name):
    uses = reference_index(rules, [weapon_name])[weapon_name.lower()]
    return sorted(kind + ':' + name + '/' + '/'.join(path) for kind, name, path in uses
                  if not (kind == 'actor' and name.lower() == selected_actor.lower()
                          and path == (selected_arm, 'Weapon')))


def solve_grid(target, factor, burst, cycle):
    """Nearest positive 100-grid raw Damage; exact rational forward check."""
    target = Fraction(str(target))
    if target <= 0 or factor <= 0 or cycle <= 0 or burst <= 0:
        raise Unsupported('target, retained factor and cadence must be positive')
    rate = factor * burst / cycle
    ideal = target / rate
    high = MAX_DAMAGE // STEP * STEP
    if ideal > high:
        raise Unsupported('target exceeds Int32 damage-grid capacity')
    lower = max(STEP, int(ideal // STEP) * STEP)
    candidates = {lower, min(high, lower + STEP)}
    # Smaller Damage wins exact ties; never silently change reload/range to hit target.
    damage = min(candidates, key=lambda d: (abs(d * rate - target), d))
    actual = damage * rate
    return damage, actual, actual - target


def propose(rules, name, target, retire_trait=None):
    case = screen(rules, name, retire_trait)
    weapon_name = case['arm'].get('Weapon')
    uses = sharing(rules, name, case['arm'].key, weapon_name)
    if uses:
        raise Unsupported('shared/referenced weapon requires separate clone review: ' + '; '.join(uses[:8]))
    damage, actual, residual = solve_grid(target, case['factor'], case['burst'], case['cycle'])
    if damage * case['factor'] > MAX_DAMAGE:
        raise Unsupported('forward modified damage exceeds Int32 capacity')
    candidate = case['weapon'].deep_copy()
    candidate.child(case['main'].key).child('Damage').value = str(damage)
    expected = candidate.deep_copy()
    expected.child(case['main'].key).child('Damage').value = case['main'].get('Damage')
    if shape(expected) != shape(case['weapon']):
        raise Unsupported('candidate changes more than Damage')
    return {'status': 'nominal-candidate-only', 'actor': name, 'weapon': weapon_name,
            'warhead': case['main'].key, 'old_damage': case['damage'], 'proposed_damage': damage,
            'burst': case['burst'], 'cycle_ticks': str(case['cycle']),
            'requested_dps': str(Fraction(str(target))), 'predicted_dps': str(actual),
            'residual_dps': str(residual), 'grid_floor_limited': Fraction(str(target)) < STEP * case['factor'] * case['burst'] / case['cycle'],
            'retire_exact_local_trait': case['retired'], 'retained_modifiers': case['retained'],
            'retained_factor': str(case['factor']),
            'current_nominal_dps': str(case['damage'] * case['old_factor'] * case['burst'] / case['cycle']),
            'source_weapon_sha256': fingerprint(case['weapon']),
            'prospective_weapon_sha256': fingerprint(candidate),
            'source_actor_sha256': fingerprint(case['before']),
            'prospective_actor_sha256': fingerprint(case['after']),
            'scope': 'Raw flat damage per tick before armor/falloff/defenses and per-hit rounding. '
                     'Conditional modifiers inactive. No price target inferred; no patch/YAML writes. '
                     'Attack/armament activation checked only at an assumed zero-condition snapshot, not actual spawn state. '
                     'Int32 checks cover raw modified damage, not all target-specific runtime intermediates. '
                     'Map/script references and gameplay effects still require manual review.'}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--actor', required=True)
    parser.add_argument('--target-damage-per-tick', required=True,
                        help='explicit nominal engine damage units per simulation tick, NOT per second')
    parser.add_argument('--retire-trait', help='exact local knob; omit to retain all modifiers')
    args = parser.parse_args()
    try:
        result = propose(Ruleset(ROOT), args.actor, args.target_damage_per_tick, args.retire_trait)
    except (Unsupported, ValueError, OverflowError) as error:
        print(json.dumps({'status': 'blocked', 'reason': str(error)}, indent=2))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
