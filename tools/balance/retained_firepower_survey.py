"""Bounded eligibility census; no gameplay changes or inferred balance targets."""
from collections import Counter
import argparse
import json
from propose_retained_firepower import ROOT, Ruleset, screen, sharing, Unsupported

OUT = ROOT / 'docs/audit/latest/retained_firepower_survey.json'


def build():
    rules = Ruleset(ROOT)
    actors = set()
    for path in (ROOT / 'docs/balance').glob('*.json'):
        doc = json.loads(path.read_text(encoding='utf-8'))
        for units in doc.get('sections', {}).values():
            actors.update(name for name, unit in units.items() if unit.get('armaments'))
    reasons = Counter()
    accepted = []
    structural = []
    for name in sorted(actors):
        try:
            case = screen(rules, name)
        except (Unsupported, ValueError) as error:
            reasons[str(error)] += 1
            continue
        structural.append(name)
        uses = sharing(rules, name, case['arm'].key, case['arm'].get('Weapon'))
        if uses:
            reasons['shared/referenced weapon requires separate clone review'] += 1
            continue
        accepted.append({'actor': name, 'weapon': case['arm'].get('Weapon'),
                         'damage': case['damage'], 'retained_factor': str(case['factor']),
                         'current_nominal_dps': str(case['damage'] * case['factor'] * case['burst'] / case['cycle'])})
    return {'scope': 'Ledger-listed armed actors resolved from active base YAML; not an exhaustive census of every actor definition. '
                     'All modifiers retained. No target or retirement inferred. '
                     'Does not prove gameplay balance, map/script safety, or approval to edit.',
            'ledger_listed_armed_actors': len(actors), 'structurally_supported': len(structural),
            'supported_unshared': len(accepted), 'blocked': sum(reasons.values()),
            'blocked_reasons': dict(sorted(reasons.items())), 'candidates': accepted}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = build()
    text = json.dumps(result, sort_keys=True, indent=2) + '\n'
    if args.write:
        OUT.write_text(text, encoding='utf-8')
    elif OUT.read_text(encoding='utf-8') != text:
        raise SystemExit('Retained-firepower survey is stale')
    print(text)
