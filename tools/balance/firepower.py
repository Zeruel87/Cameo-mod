"""Shared current-output estimate; never a replacement-damage or write-back knob."""
import formula


def armament_firepower(unit, arm):
    """Applicable unconditional product. Legacy values are fractions, not percents."""
    if 'resolved_firepower_modifiers' not in unit:
        value = (unit.get('firepower_multiplier') or {}).get('v')
        return 1.0 if value is None else float(value)
    name = arm.get('armament_name', 'primary')
    result = 1.0
    for entry in unit['resolved_firepower_modifiers']:
        types = entry['types']
        if not types or (name and name in types):
            result *= entry['modifier'] / 100.0
    return result


def priced_by_default(arm):
    return (arm.get('pricing', True) and not arm.get('unresolved')
            and formula.condition_holds_by_default(arm.get('requires')))
