"""Comparison arithmetic for reviewed per-source armor curves; no stat writeback.

Callers must first select applicable channels, target state and damage basis.
Interpolation is linear at equally spaced class positions, a diagnostic assumption.
This module does not infer missing armor mappings or battlefield hit probabilities.
"""
from collections.abc import Mapping
from fractions import Fraction
from math import exp, log

VEHICLE_ARMORS = ('scout', 'light', 'medium', 'heavy', 'superheavy')


_FIELD_ALIASES = {
    'valid_targets': {'validtargets', 'valid_targets'},
    'invalid_targets': {'invalidtargets', 'invalid_targets'},
    'valid_relationships': {'validrelationships', 'valid_relationships'},
    'invalid_relationships': {'invalidrelationships', 'invalid_relationships'},
    'weapon_valid_targets': {'weaponvalidtargets', 'weapon_valid_targets'},
    'weapon_invalid_targets': {'weaponinvalidtargets', 'weapon_invalid_targets'},
}


def _tokens(value):
    """Normalize an exported scalar/list field without assigning engine meaning."""
    if isinstance(value, str):
        values = value.replace(',', ' ').split()
    elif value is None:
        values = ()
    else:
        try:
            values = value
            iter(values)
        except TypeError:
            values = (value,)
    return frozenset(str(item).strip() for item in values if str(item).strip())


def _relationship_tokens(value):
    """Relationships are canonical names; target and slot tokens remain case-sensitive."""
    return frozenset(item.lower() for item in _tokens(value))


def _lookup(channel, field):
    """(present, value), preferring nested warhead fields over row aliases."""
    aliases = _FIELD_ALIASES[field]
    containers = []
    if isinstance(channel, Mapping) and isinstance(channel.get('fields'), Mapping):
        containers.append(channel['fields'])
    if isinstance(channel, Mapping):
        containers.append(channel)
    for container in containers:
        for key, value in container.items():
            if str(key).lower() in aliases:
                return True, value
    return False, None


def channel_identity(channel):
    """Return the source/actor/slot/weapon/warhead identity of one raw row."""
    if not isinstance(channel, Mapping):
        return (None, None, None, None, None)
    actor = channel.get('actor')
    if actor is None:
        actor = channel.get('source_actor')
    return (channel.get('source'), actor, channel.get('slot'),
            channel.get('weapon'), channel.get('warhead'))


def _identity_record(identity):
    return dict(zip(('source', 'actor', 'slot', 'weapon', 'warhead'), identity))


def _required_set(value, name):
    if value is None:
        raise ValueError(f'{name} must be supplied explicitly, including when empty')
    return _tokens(value)


def _target_reason(channel, target_types, relationship, defaults):
    present, value = _lookup(channel, 'invalid_targets')
    invalid_targets = _tokens(value) if present else defaults['invalid_targets']
    if invalid_targets & target_types:
        return 'warhead_invalid_target'

    present, value = _lookup(channel, 'valid_targets')
    valid_targets = _tokens(value) if present else defaults['valid_targets']
    if not valid_targets & target_types:
        return 'warhead_valid_targets_no_overlap'

    present, value = _lookup(channel, 'invalid_relationships')
    invalid_relationships = (_relationship_tokens(value) if present
                             else defaults['invalid_relationships'])
    if relationship in invalid_relationships:
        return 'warhead_invalid_relationship'

    present, value = _lookup(channel, 'valid_relationships')
    valid_relationships = (_relationship_tokens(value) if present
                           else defaults['valid_relationships'])
    if relationship not in valid_relationships:
        return 'warhead_valid_relationships_no_match'
    return None


def _weapon_target_reason(channel, target_types, mode):
    """Apply weapon target gating only for an explicitly direct attack."""
    if mode != 'direct':
        return None
    present, value = _lookup(channel, 'weapon_invalid_targets')
    invalid_targets = _tokens(value) if present and value is not None else frozenset()
    if invalid_targets & target_types:
        return 'weapon_invalid_target'
    present, value = _lookup(channel, 'weapon_valid_targets')
    # Direct attack selection must fail closed when the export has no weapon
    # target declaration. An explicit empty string/list remains an empty mask.
    if not present or value is None:
        return 'weapon_valid_targets_unresolved'
    if not _tokens(value) & target_types:
        return 'weapon_valid_targets_no_overlap'
    return None


def select_channels(channels, *, active_slots, target_types, relationship,
                    default_valid_targets, default_invalid_targets,
                    default_valid_relationships, default_invalid_relationships,
                    weapon_valid_target_mode=None):
    """Select reviewed raw channels for one explicit target state.

    ``active_slots`` is caller-reviewed state: this helper intentionally does
    not parse ``requires_condition`` or infer which armament is live.  Missing
    warhead masks use the four caller-supplied defaults; a present empty mask
    stays empty.  Weapon-valid-target gating is ignored unless the caller sets
    ``weapon_valid_target_mode='direct'``.  ``'collateral'`` is an explicit
    mode that keeps the weapon gate out of splash/secondary analysis.

    The selected rows are the original dictionaries, untouched.  Excluded
    entries wrap the same raw row with an identity and reason.  No damage is
    calculated here, and unsupported warhead types remain caller-owned data.
    """
    if active_slots is None:
        raise ValueError('active_slots is required caller-reviewed state')
    if weapon_valid_target_mode not in (None, 'direct', 'collateral'):
        raise ValueError("weapon_valid_target_mode must be None, 'direct' or 'collateral'")
    active_slots = _tokens(active_slots)
    target_types = _required_set(target_types, 'target_types')
    relationship = str(relationship).strip().lower() if relationship is not None else ''
    if not relationship:
        raise ValueError('relationship must be supplied explicitly')
    defaults = {
        'valid_targets': _required_set(default_valid_targets, 'default_valid_targets'),
        'invalid_targets': _required_set(default_invalid_targets, 'default_invalid_targets'),
        'valid_relationships': _relationship_tokens(
            _required_set(default_valid_relationships, 'default_valid_relationships')),
        'invalid_relationships': _relationship_tokens(
            _required_set(default_invalid_relationships, 'default_invalid_relationships')),
    }
    selected, excluded, identities, seen = [], [], [], set()
    for channel in channels:
        identity = channel_identity(channel)
        record = _identity_record(identity)
        if not isinstance(channel, Mapping):
            excluded.append({'channel': channel, 'identity': record,
                             'reason': 'invalid_channel'})
            continue
        if str(channel.get('slot', '')).strip() not in active_slots:
            excluded.append({'channel': channel, 'identity': record,
                             'reason': 'inactive_slot'})
            continue
        reason = _weapon_target_reason(channel, target_types,
                                       weapon_valid_target_mode)
        if reason is None:
            reason = _target_reason(channel, target_types, relationship, defaults)
        if reason is not None:
            excluded.append({'channel': channel, 'identity': record, 'reason': reason})
            continue
        key = tuple(None if value is None else str(value) for value in identity)
        if key in seen:
            excluded.append({'channel': channel, 'identity': record,
                             'reason': 'duplicate_channel_identity'})
            continue
        seen.add(key)
        selected.append(channel)
        identities.append(record)
    return {
        'selected': selected,
        'excluded': excluded,
        'selected_identities': identities,
        'selection': {
            'active_slots': sorted(active_slots),
            'target_types': sorted(target_types),
            'relationship': relationship,
            'weapon_valid_target_mode': weapon_valid_target_mode,
            'defaults': {key: sorted(value) for key, value in defaults.items()},
        },
    }


def interpolate_vehicle_endpoints(light, heavy):
    """Aedis mapping: source Light -> Scout, Heavy -> Superheavy."""
    a, b = Fraction(str(light)), Fraction(str(heavy))
    return {armor: a + (b - a) * Fraction(i, 4)
            for i, armor in enumerate(VEHICLE_ARMORS)}


def combined_flat_curve(channels, axes):
    """Sum selected flat channels WITHIN one source before source averaging.

Each channel supplies damage and a complete reviewed versus map. Missing values
are not silently treated as 100 or zero. Output is nominal center-impact damage;
engine rounding, bursts, modifiers and target eligibility belong to the caller.
"""
    if not channels:
        raise ValueError('no selected channels')
    return {axis: sum((Fraction(str(c['damage'])) * Fraction(str(c['versus'][axis])) / 100
                       for c in channels), Fraction()) for axis in axes}


def four_voice_means(curves, required_sources, axis, *, blend=None):
    """Exactly four unique voices, each 25%; no missing-source renormalization.

Optional blend is the explicit arithmetic share in [0,1]. There is no default
policy for mixing arithmetic and geometric results. Zero remains a real zero.
"""
    required = set(required_sources)
    if len(required) != 4 or set(curves) != required:
        raise ValueError('exactly the four named source curves are required')
    values = [float(curves[source][axis]) for source in sorted(required)]
    if any(v < 0 for v in values):
        raise ValueError('negative damage cannot use this comparison')
    arithmetic = sum(values) / 4
    geometric = 0.0 if 0 in values else exp(sum(log(v) for v in values) / 4)
    result = {'arithmetic': arithmetic, 'geometric': geometric}
    if blend is not None:
        if not 0 <= blend <= 1:
            raise ValueError('arithmetic share must be within [0,1]')
        result['blend'] = blend * arithmetic + (1 - blend) * geometric
    return result
