"""Select the standing DTA base ruleset without counting mode files as extra votes."""
import copy
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
from reference_lineages import RULED_LINEAGES


def selected_sources(sources):
    result = copy.deepcopy(sources)
    if 'dta_enhanced' not in result:
        return result  # Preserve the available source when its representative is absent.
    if 'DTA Classic' not in RULED_LINEAGES.get('DTA Enhanced', set()):
        raise ValueError('DTA warhead selection no longer matches the shared lineage ruling')
    merged = {}
    for sid in ('dta_classic', 'dta_enhanced'):
        seen = set()
        for row in result.get(sid, {}).get('rows', []):
            name = row['warhead']
            if name in seen:
                raise ValueError('ambiguous duplicate DTA warhead: ' + name)
            seen.add(name)
            previous = merged.get(name, {})
            if 'versus' in row and 'versus' in previous:
                row = dict(row, versus={**previous['versus'], **row['versus']})
                row['arity'] = len(row['versus'])
            merged[name] = row
    result['dta_enhanced']['rows'] = list(merged.values())
    result['dta_enhanced']['selection'] = (
        'Enhanced overlays available Classic rows; one DTA vote. '
        'Historical GlobalCode map fragment is not an independent base ruleset. '
        'Per-profile generated-file inheritance audit status is retained; runtime is not certified.')
    result.pop('dta_classic', None)
    result.pop('dta_globalcode', None)
    return result
