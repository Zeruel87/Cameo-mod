"""Read-only input comparison; --write updates this diagnostic report only."""
import argparse
import copy
import json
from pathlib import Path
import fit_class

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'docs/audit/latest/firepower_inputs.json'


def build():
    rows = []
    for path in sorted((ROOT / 'docs/balance').glob('*.json')):
        doc = json.loads(path.read_text(encoding='utf-8-sig'))
        for section, units in doc.get('sections', {}).items():
            for actor, unit in sorted(units.items()):
                if 'resolved_firepower_modifiers' not in unit:
                    continue
                legacy = copy.deepcopy(unit)
                del legacy['resolved_firepower_modifiers']
                before, _ = fit_class.unit_inputs(legacy)
                after, _ = fit_class.unit_inputs(unit)
                if before is None and after is None:
                    continue
                old = before[3] if before else 0
                new = after[3] if after else 0
                if abs(old - new) < 1e-8:
                    continue
                rows.append({'ledger': path.stem, 'section': section, 'actor': actor,
                             'old_class_fit_dps': round(old, 6),
                             'new_class_fit_dps': round(new, 6),
                             'ratio': round(new / old, 6) if old else None})
    return {'scope': 'Class-fit raw DPS inputs, not combat DPS or proposed actor costs. '
                     'Legacy comparison uses the corrected zero handling. '
                     'Conditional traits and other modifier trait types excluded.',
            'changed_actor_entries': len(rows), 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report = build()
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.write:
        OUTPUT.write_text(text, encoding='utf-8')
    elif OUTPUT.read_text(encoding='utf-8') != text:
        raise SystemExit('Firepower input report is stale')
    print(f'{report["changed_actor_entries"]} actor entries change class-fit DPS input')
