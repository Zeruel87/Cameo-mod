"""Exact test-only identities for immutable pre-owner comparison reports."""
import json
import pathlib

FIXTURES = pathlib.Path(__file__).resolve().parent / 'fixtures'


def restore_chained_identity_fields(obj, additional=None):
    """Reverse pinned later chain/wrapper identities for earlier frozen fixtures."""
    data = json.loads((FIXTURES / 'chained_owned_names_20260910.json').read_text(encoding='utf-8'))
    reverse = {new: old for route in data['routes'].values() for old, new in route.items()}
    wrappers = json.loads((FIXTURES / 'shared_owner_wrappers_20260910.json').read_text(encoding='utf-8'))
    reverse.update({new: old for route in wrappers['routes'].values() for old, new in route.items()})
    reverse.update(additional or {})

    def walk(value):
        if isinstance(value, dict):
            return {key: walk(child) for key, child in value.items()}
        if isinstance(value, list):
            return [walk(child) for child in value]
        if isinstance(value, str):
            parts = value.split(',')
            if any(part.strip() in reverse for part in parts):
                return ', '.join(reverse.get(part.strip(), part.strip()) for part in parts)
        return value

    return walk(obj)


def historical_weapon_names(names):
    reverse = {}
    for filename in ('closed_remaining_names_20260910.json',
                     'test_lookup_owned_names_20260910.json',
                     'converter_owned_names_20260910.json',
                     'chained_owned_names_20260910.json',
                     'shared_owner_wrappers_20260910.json'):
        data = json.loads((FIXTURES / filename).read_text(encoding='utf-8'))
        reverse.update({new: old for route in data['routes'].values() for old, new in route.items()})
    return {reverse.get(name, name) for name in names}


def restore_reviewed_katyusha_name(test, actor, obj):
    """Reverse only PR339's exact player name after verifying its reference override."""
    if actor != 'ra1_soviets_v1rockettruck':
        return obj
    name = obj['Tooltip']['Name']
    if name == 'V1 Rocket Truck':
        return obj
    test.assertEqual(name, 'Katyusha', actor)
    import sys
    sys.path.insert(0, str(FIXTURES.parents[1] / 'balance'))
    import assign_references
    test.assertEqual(assign_references.REFERENCE_OVERRIDES.get(
        (actor, 'Combined Arms')), 'KATY')
    restored = dict(obj)
    restored['Tooltip'] = dict(obj['Tooltip'], Name='V1 Rocket Truck')
    return restored
