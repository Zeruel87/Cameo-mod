"""Retain upgraded identities while excluding them from base-state projections."""
import json
from pathlib import Path
from peer_range_evidence import fingerprint
RELATIVE = Path('docs/reference/peer_base_state.json')

def load(root):
    path = Path(root) / RELATIVE
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding='utf-8'))
    if doc.get('schema') != 1:
        raise ValueError('unsupported base-state profile')
    result = {}
    for entry in doc['rows']:
        key = (entry['source'], entry['id'])
        if key in result or not entry.get('positive_upgrade_prerequisites'):
            raise ValueError('invalid base-state exclusion')
        result[key] = entry
    return result

def apply(row, record, profile):
    entry = profile.get((row['source'], row['id']))
    if entry is None:
        return
    if fingerprint(record) != entry['record_sha256']:
        raise ValueError('base-state profile no longer matches source row: ' + row['id'])
    row['reference_base_eligible'] = False
    row['reference_base_reason'] = entry['reason']
    row['reference_base_id'] = entry['base_id']
