"""Nominal base weapon-timer models; applicability to DTA runtime unverified."""
import json,math
from pathlib import Path
from peer_range_evidence import fingerprint
RELATIVE=Path('docs/reference/ini_cycle_evidence.json')

def load(root):
    path=Path(root)/RELATIVE
    if not path.exists():return {}
    doc=json.loads(path.read_text(encoding='utf-8'))
    if doc.get('schema')!=1:raise ValueError('unsupported INI cycle profile')
    result={}
    for p in doc['rows']:
        key=(p['source'],p['id'])
        if key in result:raise ValueError('duplicate cycle proof')
        if type(p.get('burst')) is not int or p['burst']<1:raise ValueError('invalid burst')
        for field in ('damage','reload','cycle_min','cycle_mean','cycle_max','dps'):
            v=p.get(field)
            if type(v) not in (int,float) or not math.isfinite(v) or v<=0:raise ValueError('invalid cycle value')
        shots=p.get('cycle_shots',p['burst'])
        if type(shots) is not int or shots<1:raise ValueError('invalid cycle shot count')
        charge=p.get('charge_ticks',0)
        if type(charge) not in (int,float) or not math.isfinite(charge) or charge<0:raise ValueError('invalid cycle charge')
        if len(p['burst_delays'])!=shots-1:raise ValueError('burst delay count mismatch')
        for label,suffix in (('minimum','min'),('mean','mean'),('maximum','max')):
            expected=p['reload']+p['post_burst_jitter'][label]+sum(d[label] for d in p['burst_delays'])+charge
            if p['cycle_'+suffix]!=expected:raise ValueError('cycle timing mismatch')
        if not p['cycle_min']<=p['cycle_mean']<=p['cycle_max']:raise ValueError('cycle bounds mismatch')
        if p['dps']!=p['damage']*shots/p['cycle_mean']:raise ValueError('cycle damage mismatch')
        result[key]=p
    return result

def apply(row,raw,profile):
    p=profile.get((row['source'],row['id']))
    if p is None:return False
    if fingerprint(raw)!=p['record_sha256'] or row.get('weapon')!=p['weapon']:
        raise ValueError('cycle proof no longer matches source row: '+row['id'])
    row['pre_cycle_evidence']={k:row.get(k) for k in ('w_dps','w_dps_raw','w_evidence','w_evidence_reason')}
    row.pop('w_dps_raw', None)  # Original estimate remains in pre_cycle_evidence.
    row.update(w_dps=p['dps'],w_dps_usable=True,w_evidence='nominal_direct',w_evidence_reason=p['scope'],w_cycle_evidence=p)
    return True
