"""Explicit-scenario shrapnel accounting, separate from approved pricing.

The caller supplies per-projectile direct damage and a random-hit credit.
Credit is a balance convention, never an engine probability measurement.
Target supply is explicit (unlimited by default); valid emitter impacts are assumed.
It must not be used as measured battle DPS or automatically invert parent Damage.
"""
from __future__ import annotations

import math

from formula import parse_bool, parse_int32


def expected_amount(raw=None):
    """FireShrapnel uses Random.Next(min, max), with max exclusive."""
    values = [parse_int32(v.strip(), 'FireShrapnel.Amount')
              for v in str(raw if raw is not None else '1').split(',')]
    if len(values) not in (1, 2) or any(v < 0 for v in values):
        raise ValueError('FireShrapnel.Amount requires one or two nonnegative integers')
    if len(values) == 1:
        return float(values[0])
    lo, hi = values
    if hi < lo:
        raise ValueError('FireShrapnel.Amount upper bound is below lower bound')
    return float(lo) if lo == hi else (lo + hi - 1) / 2


def fragment_credit(aim_chance, random_hit_credit, throw_without_target=True):
    """Expected fragment credit under the stated abundant-target scenario."""
    chance = parse_int32(aim_chance, 'FireShrapnel.AimChance', 0)
    if isinstance(random_hit_credit, bool):
        raise ValueError('random_hit_credit must be a fraction')
    credit = float(random_hit_credit)
    if not math.isfinite(credit) or not 0 <= credit <= 1:
        raise ValueError('random_hit_credit must be between zero and one')
    # Engine Next(100) < AimChance saturates outside the nominal 0..100 domain.
    aimed = min(1.0, max(0.0, chance / 100))
    fallback = parse_bool(throw_without_target, 'FireShrapnel.ThrowWithoutTarget', True)
    return aimed + (1 - aimed) * credit if fallback else aimed


def emission_counts(raw_amount, aim_chance, eligible_targets=None):
    """Expected aimed/random-attempt counts with the engine's consumed target list.

    None means unlimited eligible actors. Finite counts describe one specified
    epicenter; the caller must choose them separately for descendant impacts.
    Random attempts are returned before applying ThrowWithoutTarget.
    """
    amount = expected_amount(raw_amount)
    chance = min(1.0, max(0.0, parse_int32(aim_chance, 'AimChance', 0) / 100))
    if eligible_targets is None:
        return amount * chance, amount * (1 - chance)
    capacity = parse_int32(eligible_targets, 'eligible_targets')
    if capacity < 0:
        raise ValueError('eligible_targets must be nonnegative')
    values = [parse_int32(v.strip(), 'Amount') for v in str(raw_amount or '1').split(',')]
    amounts = range(values[0], values[1]) if len(values) == 2 and values[1] > values[0] else [values[0]]
    # Review inputs are small. Refuse impractical scenarios rather than hang.
    if max(amounts) > 10000 or len(amounts) > 10000:
        raise ValueError('finite-target scenario exceeds diagnostic count limit')
    expectations = []
    for n in amounts:
        cap = min(n, capacity)
        if cap == 0:
            expectations.append(0.0)
        elif chance == 1:
            expectations.append(float(cap))
        elif cap == n:
            expectations.append(n * chance)
        else:
            # Distribution of min(Binomial(n, chance), capacity).
            probabilities = [1.0] + [0.0] * cap
            for _ in range(n):
                nxt = [0.0] * (cap + 1)
                for used, probability in enumerate(probabilities):
                    nxt[used] += probability * (1 - chance)
                    nxt[min(used + 1, cap)] += probability * chance
                probabilities = nxt
            expectations.append(sum(i * p for i, p in enumerate(probabilities)))
    aimed = sum(expectations) / len(expectations)
    return aimed, amount - aimed


def damage_tree(name, resolve_weapon, direct_damage, *, random_hit_credit,
                impact_count=lambda weapon: 1.0,
                eligible_targets=lambda weapon, emitter: None, _path=()):
    """Count each emitter edge once, including recursively emitted projectiles.

    direct_damage(node) is direct payload per emitted projectile, already including
    its impact count. impact_count(node) applies separately to child emission.
    Child Burst and ReloadDelay never multiply emitted projectiles: the engine
    constructs one ProjectileArgs per fragment, not an armament firing cycle.
    Missing references and cycles are withheld rather than silently truncated.
    Branch credit propagates to descendants as a balance convention. This does
    not simulate random misses that still produce valid descendant impacts.
    """
    key = name.lower()
    if key in _path:
        raise ValueError('recursive shrapnel cycle: ' + ' -> '.join((*_path, key)))
    node = resolve_weapon(name)
    if node is None:
        raise ValueError('missing shrapnel weapon: ' + name)
    own = float(direct_damage(node))
    impacts = float(impact_count(node))
    if not math.isfinite(own) or own < 0 or not math.isfinite(impacts) or impacts < 0:
        raise ValueError('damage and impact count must be finite and nonnegative')
    edges = []
    for wh in node.children:
        if not wh.key.startswith('Warhead@') or wh.value != 'FireShrapnel':
            continue
        amount = expected_amount(wh.get('Amount'))
        # Reuse the validation of the explicitly supplied random credit.
        random_credit = fragment_credit(0, random_hit_credit)
        capacity = eligible_targets(node, wh)
        aimed, random = emission_counts(wh.get('Amount'), wh.get('AimChance'), capacity)
        if not parse_bool(wh.get('ThrowWithoutTarget'), 'ThrowWithoutTarget', True):
            random = 0.0
        effective_count = aimed + random * random_credit
        weight = effective_count / amount if amount else 0.0
        if effective_count == 0 or impacts == 0:
            edges.append({'warhead': wh.key, 'fragment': wh.get('Weapon'),
                          'amount': amount, 'credit': weight, 'damage': 0.0,
                          'eligible_targets': capacity, 'aimed_count': aimed,
                          'random_count': random})
            continue
        fragment = wh.get('Weapon')
        if not fragment:
            raise ValueError('missing FireShrapnel.Weapon in ' + name)
        subtree = damage_tree(fragment, resolve_weapon, direct_damage,
                              random_hit_credit=random_hit_credit,
                              impact_count=impact_count, eligible_targets=eligible_targets,
                              _path=(*_path, key))
        edges.append({'warhead': wh.key, 'fragment': fragment, 'amount': amount,
                      'credit': weight, 'parent_impacts': impacts,
                      'eligible_targets': capacity, 'aimed_count': aimed,
                      'random_count': random,
                      'damage': impacts * amount * weight * subtree['total'],
                      'subtree': subtree})
    extra = sum(edge['damage'] for edge in edges)
    return {'weapon': name, 'direct': own, 'shrapnel': extra, 'total': own + extra,
            'random_hit_credit': random_hit_credit,
            'status': 'scenario_only', 'edges': edges}
