"""Compare read-only consumers with PR328's first commit. No prices are applied.

Requires the baseline git object. Frozen baseline modules are loaded without main;
formula.py is unchanged by this follow-up. Workbook counts compare row factors,
not evaluated Excel prices. Output is a compact census plus explicit examples.
"""
import argparse
import json
import pathlib
import subprocess
import types
import contextlib
import io
import re
import sys
import check_band
import propose_rebalance
import update_ranges
from firepower import armament_firepower, priced_by_default

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = 'ffc753fb0a6430fa518869ba94027aef4cd8e7ba'
OUT = ROOT / 'docs/audit/latest/firepower_consumers.json'


def baseline(name):
    path = f'tools/balance/{name}.py'
    source = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT, text=True, encoding='utf-8')
    module = types.ModuleType('_baseline_' + name)
    module.__file__ = str(ROOT / path)
    # Trusted repository code at the fixed BASE SHA, selected by build's literal
    # module tuple. This deliberately remains visible to the raw security audit;
    # never substitute a user-supplied ref or downloaded source here.
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
    return module


def build():
    old_band, old_faction, old_ranges = [baseline(n) for n in
        ('check_band', 'propose_rebalance', 'update_ranges')]
    counts = {name: {'evaluated_entries': 0, 'changed_entries': 0, 'baseline_errors': 0}
              for name in ('band_dps', 'faction_primary_dps', 'range_dps', 'workbook_weapon_factors')}
    examples = []
    wanted = {'zerg_hydralisk', 'terran_marine', 'td_nod_minigunner',
              'ra1_allies_alliedmediumtank', 'cabal_rocketcyborg'}
    for path in sorted((ROOT / 'docs/balance').glob('*.json')):
        doc = json.loads(path.read_text(encoding='utf-8-sig'))
        for units in doc.get('sections', {}).values():
            for actor, unit in units.items():
                if not unit.get('armaments'):
                    continue
                legacy = float((unit.get('firepower_multiplier') or {}).get('v', 1))
                # Old workbook/range code divided an existing fraction again.
                old_factor = legacy / 100 if unit.get('firepower_multiplier') else 1
                pairs = {
                    'band_dps': (lambda: (old_band.unit_inputs(unit) or [0]*4)[3],
                                 lambda: (check_band.unit_inputs(unit) or [0]*4)[3]),
                    'faction_primary_dps': (lambda: old_faction.unit_row(unit)[3],
                                            lambda: propose_rebalance.unit_row(unit)[3]),
                    'range_dps': (lambda: old_ranges.unit_dps(unit, old_factor),
                                  lambda: update_ranges.unit_dps(unit)),
                    'workbook_weapon_factors': (
                        lambda: [old_factor for a in unit['armaments'] if not a.get('unresolved')],
                        lambda: [armament_firepower(unit, a) for a in unit['armaments'] if not a.get('unresolved')]),
                }
                values = {}
                for name, (before, after) in pairs.items():
                    counts[name]['evaluated_entries'] += 1
                    try:
                        old = before()
                    except (AttributeError, TypeError, ValueError) as error:
                        old = type(error).__name__
                        counts[name]['baseline_errors'] += 1
                    new = after()
                    changed = old != new if isinstance(old, (str, list)) else abs(old-new) > 1e-8
                    counts[name]['changed_entries'] += int(changed)
                    values[name] = {'before': old, 'after': new}
                if actor in wanted:
                    examples.append({'actor': actor, 'ledger': path.stem, 'values': values,
                                     'default_priced_rows': sum(priced_by_default(a) for a in unit['armaments'])})
    def band_summary(module):
        output = io.StringIO()
        saved = sys.argv
        try:
            sys.argv = ['check_band.py']
            with contextlib.redirect_stdout(output):
                code = module.main()
        finally:
            sys.argv = saved
        match = re.search(r'\[(\d+) band violations across (\d+) classes\]', output.getvalue())
        if match is None:
            raise ValueError('Missing band summary')
        return {'exit_code': code, 'violations': int(match[1]), 'classes': int(match[2])}

    return {'baseline': BASE, 'scope': 'Input estimates only; primary-only faction report differs '
            'deliberately from all-priced-armament totals. No cost/HP/weapon writes. '
            'Workbook values are factors, not recalculated Excel prices.',
            'counts': counts, 'examples': examples,
            'band_validation': {'before': band_summary(old_band), 'after': band_summary(check_band),
                                'note': 'Unrecalibrated class anchors; findings are model flags, not proven balance defects.'}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report = build()
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.write:
        OUT.write_text(text, encoding='utf-8')
    elif OUT.read_text(encoding='utf-8') != text:
        raise SystemExit('Consumer report is stale')
    print(json.dumps(report['counts'], indent=2))
