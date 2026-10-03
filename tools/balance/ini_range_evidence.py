"""Exact INI declared range, independently of the damage/cycle verdict."""
import json
from pathlib import Path
from peer_range_evidence import fingerprint
RELATIVE=Path('docs/reference/ini_range_evidence.json')
VERDICT='nominal_declared_ini_range'

def load(root):
    p=Path(root)/RELATIVE
    if not p.exists():return {}
    doc=json.loads(p.read_text(encoding='utf-8'))
    if doc.get('schema')!=1:raise ValueError('unsupported INI range profile')
    result={}
    for r in doc['rows']:
        key=(r['source'],r['id'])
        if key in result or type(r.get('range')) not in (int,float) or r['range']<=0:
            raise ValueError('invalid INI range profile')
        result[key]=r
    return result

def apply(row,raw,profile):
    p=profile.get((row['source'],row['id']))
    if p is None:return
    if fingerprint(raw)!=p['record_sha256'] or row.get('weapon')!=p['weapon'] or row.get('w_range')!=p['range']:
        raise ValueError('INI range no longer matches source row: '+row['id'])
    row.update(w_range_usable=True,w_range_evidence=VERDICT,w_range_scope=p['scope'])
