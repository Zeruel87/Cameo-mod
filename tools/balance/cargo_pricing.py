"""Static passenger-sum valuation of an authored mixed Cargo.InitialUnits load."""
import math


def trait(node, kind):
    return next((c for c in node.children if c.key.split('@')[0] == kind), None)


def authored_load(rules, actor_name):
    actor = rules.resolve(actor_name)
    cargo = trait(actor, 'Cargo')
    if cargo is None:
        return {'issues': ['missing Cargo'], 'passenger_sum': None}
    capacity = int(cargo.get('MaxWeight') or 0)
    types = {s.strip() for s in (cargo.get('Types') or '').split(',')}
    names = [s.strip() for s in (cargo.get('InitialUnits') or '').split(',') if s.strip()]
    passengers, issues = [], []
    for name in names:
        if rules.actor(name) is None:
            issues.append(name + ': missing actor')
            continue
        passenger = rules.resolve(name)
        info, valued = trait(passenger, 'Passenger'), trait(passenger, 'Valued')
        if info is None or valued is None:
            issues.append(name + ': missing Passenger or Valued')
            continue
        weight = int(info.get('Weight') or 0)
        if weight <= 0:
            if trait(passenger, 'WithInfantryBody') is not None:
                weight = 1
            else:
                health = trait(passenger, 'Health')
                hp = int(health.get('HP') or 0) if health else 0
                if hp <= 0:
                    issues.append(name + ': missing positive HP for auto-weight')
                    continue
                weight = min(8, max(2, 2 + math.floor(math.log2(hp / 32768.0))))
        if info.get('CargoType') not in types:
            issues.append(name + ': cargo type mismatch')
        buildable = trait(passenger, 'Buildable')
        passengers.append({'actor': name, 'weight': weight,
                           'cost': int(valued.get('Cost') or 0),
                           'prerequisites': buildable.get('Prerequisites') if buildable else None})
    filled = sum(p['weight'] for p in passengers)
    if capacity <= 0 or filled != capacity:
        issues.append(f'filled weight {filled}/{capacity}')
    total = sum(p['cost'] for p in passengers) if not issues else None
    armed = bool(actor.children_named('Armament'))
    return {'passengers': passengers, 'capacity': capacity, 'filled_weight': filled,
            'issues': issues, 'passenger_sum': total, 'armed': armed,
            'combat_special_k': 1.25 if armed else None,
            'combat_stat_budget': total / 1.25 if armed and total is not None else None,
            'basis': 'authored InitialUnits; static capacity/type valuation, not tier or runtime approval'}
