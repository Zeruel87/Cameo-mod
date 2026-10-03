"""Independent nominal range evidence for the co-pinned base OpenRA corpus.

Does not certify DPS, factory readiness, projectile reach or battle effectiveness.
Only a single unconditional Armament with no active default RangeMultiplier is admitted.
"""
import hashlib
import json
import math
from pathlib import Path

RELATIVE = Path('docs/reference/peer_range_evidence.json')
PIN = 'bbd36d9e6a2d7f0d3b24f102858af6dc8caf8a78'
VERDICT = 'nominal_single_armament_range'
SELECTED_VERDICT = 'nominal_selected_armament_range'


def fingerprint(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()


def load(root):
    path = Path(root) / RELATIVE
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding='utf-8'))
    if doc.get('schema') != 1 or doc.get('source_commit') != PIN:
        raise ValueError('unsupported range evidence profile')
    result = {}
    for item in doc['rows']:
        key = (item['source'], item['id'])
        if key in result or item.get('evidence') not in (VERDICT, SELECTED_VERDICT):
            raise ValueError('duplicate or unsupported range evidence')
        value = item.get('range')
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError('invalid range evidence value')
        result[key] = item
    return result


def apply(row, record, profile):
    entry = profile.get((row['source'], row['id']))
    if entry is None:
        return
    if (fingerprint(record) != entry['record_sha256']
            or (entry.get('evidence') != SELECTED_VERDICT and record.get('w_range') != entry['range'])):
        raise ValueError('range evidence no longer matches source row: ' + row['id'])
    if entry.get('evidence') == SELECTED_VERDICT:
        row['w_range_raw'] = row.get('w_range')
        row['w_range'] = entry['range']
        row['range_selection'] = entry
    row['w_range_usable'] = True
    row['w_range_evidence'] = entry.get('evidence', VERDICT)
    row['w_range_scope'] = entry.get('scope', 'single unconditional weapon, range modifiers absent or rank-elite disabled at definition default; nominal range only')
