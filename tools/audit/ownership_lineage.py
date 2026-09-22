"""Supplemental ownership diagnostics. Never substitutes for the raw audit gates.

Rename provenance is the frozen, published ownership evidence, not a name guess
or a current-payload match. Thus later damage drift remains visible after a rename.
Wrapper equivalence, in contrast, requires exact CURRENT ordered payload equality.
"""
import collections
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'balance'))
from owned_weapon_wrappers import IDENTITY_WRAPPERS, is_reviewed_owner_wrapper

SOURCE_COMMIT = '6278225df00c0aa0356961036c44670847321027'
# Hash only canonical route metadata: checkout CRLF translation cannot alter it.
ROUTE_HASHES = {
    'closed_remaining_names_20260910.json': 'ae3d0dcc7663c28e26f68a29ba60ba606addd8b16f6a5a842717893d41796c8e',
    'test_lookup_owned_names_20260910.json': '52c789fb4c18f70bf4b4b333b46ae2f13bde79425965a225cf144e8c34756da8',
    'converter_owned_names_20260910.json': '133048360862ff162a35e9c1baca35c42f159ccdeb7c4923b6f4bbac1428f968',
    'chained_owned_names_20260910.json': '2af0489154745bdc393c0b22fb504a1a48e14241372d1bfee1d3ec94bda64ee4',
}


def validate_renames(renames):
    if any(not isinstance(k, str) or not isinstance(v, str) or not k or not v
           for k, v in renames.items()):
        raise ValueError('invalid rename identity')
    if len(set(renames.values())) != len(renames):
        raise ValueError('ambiguous many-to-one rename lineage')
    for name in renames:
        seen = set()
        while name in renames:
            if name in seen:
                raise ValueError('cyclic rename lineage')
            seen.add(name)
            name = renames[name]


def load_renames(repo):
    """Read immutable evidence data, never execute test helpers or rewrite fixtures."""
    result = {}
    for filename, expected in ROUTE_HASHES.items():
        data = json.loads((pathlib.Path(repo) / 'tools/tests/fixtures' / filename).read_text(encoding='utf-8'))
        routes = data['routes']
        digest = hashlib.sha256(json.dumps(routes, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if data.get('source_commit') != SOURCE_COMMIT or digest != expected:
            raise ValueError(f'unreviewed rename evidence: {filename}')
        for route in routes.values():
            for old, new in route.items():
                if old in result:
                    raise ValueError(f'duplicate rename identity: {old}')
                result[old] = new
    validate_renames(result)
    return result


def release_view(base, now, accepted, renames, min_ratio=3.0):
    """Per-release-identity flat comparison; raw name-only counters stay separate.

Only proven renames are followed. Unknown/deleted names stay unmatched. Both
old and new live identities are ambiguous, not grounds to silently choose one.
Accepted values are still checked against the exact released-name value pin.
"""
    validate_renames(renames)
    counts = dict.fromkeys(('matched', 'unmatched', 'inflated', 'weakened', 'extreme', 'accepted'), 0)
    recovered, drift, unresolved = [], [], []
    for old, before in base.items():
        name = old
        while name in renames:
            if name in now:
                raise ValueError(f'ambiguous live old identity in rename lineage: {name}')
            name = renames[name]
        if name not in now:
            counts['unmatched'] += 1
            unresolved.append({'released_name': old, 'expected_name': name})
            continue
        counts['matched'] += 1
        row = {'released_name': old, 'current_name': name, 'was': before,
               'now': now[name], 'status': 'unchanged', 'ratio': None}
        if name != old:
            recovered.append(row)
        if before['flat'] <= 0:
            row['status'] = 'no-positive-baseline'
            continue
        ratio = now[name]['flat'] / before['flat']
        row['ratio'] = ratio
        if abs(ratio - 1.0) < .01:
            continue
        if accepted.get(old, {}).get('accepted') == now[name]['flat']:
            row['status'] = 'accepted exact value'
            counts['accepted'] += 1
            continue
        row['status'] = 'inflated' if ratio > 1 else 'weakened'
        counts[row['status']] += 1
        if ratio >= min_ratio or ratio <= 1 / min_ratio:
            counts['extreme'] += 1
        drift.append(row)
    return {'counts': counts, 'recovered': recovered, 'drift': drift, 'unresolved': unresolved}


def ordered_payload(node):
    return [(n.key, n.value, ordered_payload(n)) for n in node.children]


def missile_view(rules, findings):
    """Group only reviewed transparent wrappers; never infer aliases by similarity."""
    canonical = {}
    rejected = set()
    for rows in findings.values():
        for name, _role, _family in rows:
            if name in canonical:
                continue
            canonical[name] = name
            if name not in IDENTITY_WRAPPERS:
                continue
            if not is_reviewed_owner_wrapper(rules, name):
                rejected.add(name)
                continue
            parent = IDENTITY_WRAPPERS[name]
            if ordered_payload(rules.resolve_weapon(name)) != ordered_payload(rules.resolve_weapon(parent)):
                rejected.add(name)
                continue
            canonical[name] = parent
    groups = collections.defaultdict(list)
    for code, rows in findings.items():
        for name, role, family in rows:
            groups[(code, canonical[name], role, family)].append(name)
    counts = {code: sum(key[0] == code for key in groups) for code in ('R1', 'R2', 'R3', 'R4')}
    duplicates = [{'code': code, 'parent': parent, 'role': role, 'family': family,
                   'members': sorted(members)}
                  for (code, parent, role, family), members in sorted(groups.items()) if len(members) > 1]
    return {'counts': counts, 'duplicates': duplicates, 'nontransparent_reviewed_wrappers': sorted(rejected)}
