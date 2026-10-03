#!/usr/bin/env python3
"""pending_classes.py — the class map C46 WILL produce, for review before any yaml lands.

`armed_troop_transport` and `mobile_bunker` are defined in class_anchors.json and mapped in
class_membership.py, but have ZERO members: the yaml templates do not exist yet (C46). And a hand
tag cannot substitute -- `extract_stats.py:967` rewrites `design.class_anchor` to None on every run,
so `design.subtype`, i.e. the inherited `^...Template`, is the only durable membership signal.

This script derives the PENDING membership mechanically from the resolved ruleset so the maintainer
can review the reclassification BEFORE it is committed:

    mobile_bunker          buildable + resolved AttackOpenTopped + GROUND VEHICLE
    armed_troop_transport  buildable + Cargo + armed + ground vehicle + NOT open-topped.
                           The maintainer's "all 17 move" ruling overrides an existing combat
                           class; the Flak Trucks leave `anti_air_vehicle` and IFVs leave
                           `scout_vehicle`. All three classes already carry the 1.5x AA range.

    python tools/balance/pending_classes.py            # writes pending_classes.json to the OS temp dir
    python tools/balance/build_reference_report.py --faction ... --pending <that file>

WARNING 26 actors resolve AttackOpenTopped, not 16: three are AIRCRAFT and seven are IMMOBILE
bunkers/defenses. The Mobile-and-not-Aircraft filter is what makes the count 16, and dropping it
would turn seven static defenses into "mobile bunkers".
"""
import sys, json, glob, collections, pathlib, tempfile
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
        # Maintainer ruling 2026-09-08: cargo plus a weapon means armed troop
        # transport, with no exception for an existing combat class.
        if now != 'armed_troop_transport':
            pending[name]='armed_troop_transport'; stats['armed_troop_transport']+=1
            if now not in (None, 'support'):
                stats[f'  (overrode {now})'] += 1
output_path = pathlib.Path(tempfile.gettempdir()) / 'pending_classes.json'
output_path.write_text(json.dumps(pending, indent=1, sort_keys=True) + '\n', encoding='utf-8')
print(dict(stats), ' total', len(pending))
print('pending map ->', output_path)
