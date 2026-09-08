#!/usr/bin/env python3
"""pending_classes.py — the class map C46 WILL produce, for review before any yaml lands.

`armed_troop_transport` and `mobile_bunker` are defined in class_anchors.json and mapped in
class_membership.py, but have ZERO members: the yaml templates do not exist yet (C46). And a hand
tag cannot substitute -- `extract_stats.py:967` rewrites `design.class_anchor` to None on every run,
so `design.subtype`, i.e. the inherited `^...Template`, is the only durable membership signal.

This script derives the PENDING membership mechanically from the resolved ruleset so the maintainer
can review the reclassification BEFORE it is committed:

    mobile_bunker          buildable + resolved AttackOpenTopped + GROUND VEHICLE
    armed_troop_transport  buildable + Cargo + armed + ground vehicle + NOT open-topped,
                           and ONLY where the actor's current class is `support` or None
    ...?                   the same test where the actor ALREADY carries a combat class --
                           emitted with a trailing '?' because overriding a real class is a
                           maintainer decision, not a mechanical one

    python tools/balance/pending_classes.py            # writes /tmp/pending_classes.json
    python tools/balance/build_reference_report.py --faction ... --pending <that file>

WARNING 26 actors resolve AttackOpenTopped, not 16: three are AIRCRAFT and seven are IMMOBILE
bunkers/defenses. The Mobile-and-not-Aircraft filter is what makes the count 16, and dropping it
would turn seven static defenses into "mobile bunkers".
"""
import sys, json, glob, collections
sys.path.insert(0,'tools/audit'); sys.path.insert(0,'tools/balance')
sys.stdout.reconfigure(encoding='utf-8')
import miniyaml, class_membership as cm
rs=miniyaml.Ruleset('.')
led={}
for p in sorted(glob.glob('docs/balance/*.json')):
    if 'class_anchors' in p: continue
    try: d=json.load(open(p,encoding='utf-8'))
    except Exception: continue
    for s,u in (d.get('sections') or {}).items():
        if isinstance(u,dict):
            for n,r in u.items():
                if isinstance(r,dict): led[n]=r
pending={}
stats=collections.Counter()
for name,r in led.items():
    if r.get('buildable') is not True: continue
    node=rs.resolve(name)
    if node is None: continue
    base=[c.key.split('@')[0] for c in node.children]
    ot='OpenTopped' in ' '.join(c.key for c in node.children)
    mobile='Mobile' in base; air='Aircraft' in base
    now=cm.classify(r.get('design') or {})[0]
    if not (mobile and not air):      # ground vehicles only
        continue
    if ot:
        if now!='mobile_bunker': pending[name]='mobile_bunker'; stats['mobile_bunker']+=1
    elif 'Cargo' in base and r.get('armaments'):
        if now in (None,'support'):
            pending[name]='armed_troop_transport'; stats['armed_troop_transport']+=1
        else:
            pending[name]='armed_troop_transport?'; stats['CONTESTED']+=1
json.dump(pending, open('/tmp/pending_classes.json','w'), indent=1, sort_keys=True)
print(dict(stats), ' total', len(pending))
print("\nCONTESTED — already carry a combat class, would be overridden:")
for n in sorted(k for k,v in pending.items() if v.endswith('?')):
    print(f"   {cm.classify(led[n].get('design') or {})[0]:20s} {n}")
