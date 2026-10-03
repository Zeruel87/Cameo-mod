"""Exact-row reviewed nominal weapon selection; original corpus stays untouched.

This is a nominal direct-weapon comparison, not total unit or runtime DPS.
Never infer a dummy from a zero damage value or a weapon name alone.
"""
import copy
import json
from pathlib import Path

from peer_range_evidence import fingerprint

RELATIVE = Path('docs/reference/ini_weapon_selection.json')


def load(root):
    path = Path(root) / RELATIVE
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding='utf-8'))
    if doc.get('schema') != 1:
        raise ValueError('unsupported INI weapon selection profile')
    result = {}
    for entry in doc['rows']:
        key = (entry['source'], entry['id'])
        if key in result or entry.get('selection') != 'reviewed_nominal_secondary':
            raise ValueError('duplicate or unsupported INI weapon selection')
        result[key] = entry
    return result


def select(record, profile):
    entry = profile.get((record['source'], record['id']))
    if entry is None:
        return record
    if fingerprint(record) != entry['record_sha256']:
        raise ValueError('INI selection no longer matches source row: ' + record['id'])
    if (record.get('weapon') != entry['primary']
            or record.get('w2_weapon') != entry['secondary']
            or record.get('w2_evidence') != 'nominal_direct'
            or record.get('w2_dps_usable') is not True):
        raise ValueError('reviewed secondary is no longer nominal direct')
    selected = copy.deepcopy(record)
    for key in list(selected):
        if key == 'weapon' or key.startswith('w_'):
            selected.pop(key)
            selected['wdummy_weapon' if key == 'weapon' else 'wdummy_' + key[2:]] = record[key]
    for key, value in record.items():
        if key.startswith('w2_'):
            selected['weapon' if key == 'w2_weapon' else 'w_' + key[3:]] = copy.deepcopy(value)
    selected['w_from_secondary'] = True
    selected['w_dummy_primary'] = record['weapon']
    selected['w_evidence_reason'] = entry['scope']
    return selected
