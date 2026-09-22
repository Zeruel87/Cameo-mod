"""Read-only emitter/receiver inventory for conditional status valuation.

This reports declared routes, not hit probability, uptime, eligibility, or prices.
Only directly bound weapons and concrete active actor definitions are included.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

from miniyaml import Ruleset
from dump_resolved import node_to_obj

ROOT = Path(__file__).resolve().parents[2]
TOKEN = re.compile(r'[A-Za-z_][A-Za-z0-9_.-]*')


def inventory(rs):
    bindings = defaultdict(list)
    receivers = defaultdict(list)
    consumers = defaultdict(list)
    for name in rs.actors:
        if name.startswith('^'):
            continue
        actor = rs.resolve(name)
        for trait in actor.children:
            kind = trait.key.split('@')[0]
            if kind == 'Armament' and trait.get('Weapon'):
                bindings[trait.get('Weapon').lower()].append(dict(
                    actor=name, trait=trait.key, requires=trait.get('RequiresCondition')))
            if kind == 'ExternalCondition' and trait.get('Condition'):
                receivers[trait.get('Condition')].append(dict(
                    actor=name, trait=trait.key, fields=node_to_obj(trait)))
            expression = trait.get('RequiresCondition')
            if expression:
                for token in set(TOKEN.findall(expression)):
                    consumers[token].append(dict(actor=name, trait=trait.key,
                        requires=expression, fields=node_to_obj(trait)))

    emitted = defaultdict(list)
    for name, users in sorted(bindings.items()):
        weapon = rs.resolve_weapon(name)
        if weapon is None:
            continue
        for wh in weapon.children:
            if wh.value == 'GrantExternalCondition' and wh.get('Condition'):
                emitted[wh.get('Condition')].append(dict(weapon=weapon.key,
                    warhead=wh.key, fields=node_to_obj(wh), bindings=users))
    statuses = {}
    for condition, emitters in sorted(emitted.items()):
        statuses[condition] = dict(emitters=emitters,
            receivers=receivers[condition], consumers=consumers[condition],
            receiver_count=len({x['actor'] for x in receivers[condition]}),
            consumer_trait_types=sorted({x['trait'].split('@')[0] for x in consumers[condition]}))
    return dict(scope='active manifest, concrete actor definitions, direct armament bindings',
        statuses=statuses, limits=[
            'Receiver presence does not prove target-mask or relationship eligibility.',
            'RequiresCondition expressions are reported without assuming they are active.',
            'Token counts, source caps, resistances and duration refresh need runtime semantics.',
            'PhysicalState and integrity meters remain in their separate diagnostics.',
            'Script grants, spawned actors and other secondary routes need separate coverage.',
            'No scalar status cost or upgrade price is inferred.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = inventory(Ruleset(ROOT))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for condition, row in report['statuses'].items():
        print(condition, 'emitters=' + str(len(row['emitters'])),
              'receivers=' + str(row['receiver_count']),
              'consumers=' + ','.join(row['consumer_trait_types']))


if __name__ == '__main__':
    main()
