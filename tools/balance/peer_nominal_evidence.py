"""Reviewed base-weapon damage/reload at the pinned declared base context.

Excludes target response, armor, splash totals, travel and upgrade-state effects.
The source's original broader withheld verdict remains in weapon_evidence_raw.
"""
import json
import math
from pathlib import Path
from peer_range_evidence import PIN, fingerprint

RELATIVE = Path('docs/reference/peer_nominal_evidence.json')
RANGE_VERDICT = 'nominal_selected_base_range'


def load(root):
    path = Path(root) / RELATIVE
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding='utf-8'))
    if doc.get('schema') != 1 or doc.get('source_commit') != PIN:
        raise ValueError('unsupported nominal weapon profile')
    result = {}
    for entry in doc['rows']:
        key = (entry['source'], entry['id'])
        if key in result:
            raise ValueError('duplicate nominal weapon proof')
        if type(entry.get('dps_usable', True)) is not bool:
            raise ValueError('invalid nominal DPS evidence flag')
        for field in ('damage', 'reload', 'dps'):
            value = entry.get(field)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError('invalid nominal weapon value')
        basis = entry.get('comparison_basis')
        if basis is not None and basis not in {'common_authored_damage', 'named_target_uncapped'}:
            raise ValueError('unsupported comparison basis')
        if basis == 'named_target_uncapped':
            scenario = entry.get('target_scenario', {})
            hp, percent = scenario.get('maximum_hp'), scenario.get('percent_damage')
            if (type(hp) not in (int, float) or type(percent) not in (int, float)
                    or hp <= 0 or percent <= 0 or not math.isfinite(hp + percent)
                    or entry['damage'] != hp * percent / 100):
                raise ValueError('named-target damage basis mismatch')
        if basis == 'common_authored_damage':
            channels = entry.get('channel_evidence', [])
            if len(channels) < 2 or any(float(c['fields']['Damage']) != entry['damage'] for c in channels):
                raise ValueError('common authored damage basis mismatch')
        if 'center_falloff_percent' in entry:
            raw = entry.get('raw_weapon_damage')
            center = entry['center_falloff_percent']
            if type(raw) not in (int, float) or type(center) not in (int, float) or raw <= 0 or center <= 0:
                raise ValueError('invalid center damage proof')
            if entry['damage'] != raw * center / 100:
                raise ValueError('center damage proof mismatch')
        if 'impact_count' in entry:
            impacts = entry['impact_count']
            raw = entry.get('damage_per_impact')
            if type(impacts) is not int or impacts < 1 or type(raw) not in (int, float) or raw <= 0:
                raise ValueError('invalid nominal projectile impact count')
            if entry['damage'] != raw * impacts:
                raise ValueError('nominal projectile damage mismatch')
        if 'damage_parts' in entry:
            parts = entry['damage_parts']
            if not parts or entry['damage'] != sum(p['damage'] * p['center_percent'] / 100 for p in parts):
                raise ValueError('nominal warhead sum mismatch')
        burst = entry.get('burst', 1)
        delays = entry.get('burst_delays', [])
        if type(burst) is not int or burst < 1 or len(delays) != burst - 1:
            raise ValueError('nominal weapon burst mismatch')
        if 'shot_damage' in entry:
            shots = entry['shot_damage']
            if len(shots) != burst or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in shots):
                raise ValueError('invalid nominal shot damage sequence')
            if not math.isclose(entry['damage'], sum(shots) / burst, rel_tol=1e-12):
                raise ValueError('nominal mean shot damage mismatch')
        if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in delays):
            raise ValueError('invalid nominal burst delay')
        charge_ticks = entry.get('charge_ticks', 0)
        if type(charge_ticks) not in (int, float) or not math.isfinite(charge_ticks) or charge_ticks < 0:
            raise ValueError('invalid nominal charge duration')
        if 'charge_ticks_bounds' in entry:
            bounds = entry['charge_ticks_bounds']
            if len(bounds) != 2 or not 0 <= bounds[0] <= charge_ticks <= bounds[1]:
                raise ValueError('invalid nominal charge bounds')
        burst_damage = sum(entry['shot_damage']) if 'shot_damage' in entry else entry['damage'] * burst
        if entry['dps'] != burst_damage / (entry['reload'] + sum(delays) + charge_ticks):
            raise ValueError('nominal weapon cycle mismatch')
        result[key] = entry
    return result


def apply(row, record, profile):
    entry = profile.get((row['source'], row['id']))
    if entry is None:
        return False
    if fingerprint(record) != entry['record_sha256']:
        raise ValueError('nominal proof no longer matches source row: ' + row['id'])
    if entry.get('range') is not None:
        row.update(w_range=entry['range'], w_range_usable=True,
                   w_range_evidence=RANGE_VERDICT,
                   w_range_scope='Reviewed selected base armament in its declared base context; not upgraded or factory-state certification.')
    if entry.get('dps_usable') is False:
        return False
    row['weapon_evidence_raw'] = {
        k: record.get(k) for k in ('w_evidence', 'w_evidence_reason', 'w_dps', 'w_dps_raw', 'w_dps_usable')}
    row['pre_nominal_weapon'] = {
        k: record.get(k) for k in ('weapon', 'w_damage', 'w_reload', 'w_burst', 'w_range', 'w_dps')}
    row.update(weapon=entry['weapon'], w_damage=entry['damage'],
               w_reload=entry['reload'], w_burst=entry.get('burst', 1),
               w_nominal_evidence=entry)
    row.pop('w_dps_raw', None)
    row.update(w_dps=entry['dps'], w_evidence='nominal_direct', w_dps_usable=True,
               w_evidence_reason='Reviewed nominal base damage/cycle in its declared base context; excludes armor, target response, splash totals and upgrades.')
    if entry.get('comparison_basis') == 'named_target_uncapped':
        row['w_evidence_reason'] = 'Approved named-target uncapped damage/cycle comparison; target HP is explicit, and this is not target-independent battle DPS.'
    elif entry.get('comparison_basis') == 'common_authored_damage':
        row['w_evidence_reason'] = 'Approved common authored damage/cycle basis for split armor channels; combined target/armor response is separate, not a sum of duplicate raw damage values.'
    if entry.get('scope'):
        row['w_evidence_reason'] += ' ' + entry['scope']
    return True
