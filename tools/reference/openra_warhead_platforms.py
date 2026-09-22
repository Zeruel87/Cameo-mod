"""Trace declared armor profiles from retained, provenance-bearing peer exports.

This is review evidence, not automatic family voting: alternative armaments,
multi-channel damage, custom warheads and actor eligibility need selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def trace_export(path: Path, source: str) -> dict:
    raw = path.read_bytes()
    records = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    if not records or records[0].get('record') != 'meta':
        raise ValueError('peer export must begin with its provenance metadata')
    meta = records[0]
    if not meta.get('inputs') or any(item.get('unchanged') is not True for item in meta['inputs']):
        raise ValueError('peer export does not prove stable input hashes during extraction')
    seen, rows, missing = set(), [], []
    for actor in records[1:]:
        actor_id = actor.get('id')
        if not actor_id or actor_id in seen:
            raise ValueError(f'missing or duplicate actor ID: {actor_id}')
        seen.add(actor_id)
        for slot in actor.get('weapon_evidence', []):
            if not slot.get('weapon_resolved'):
                missing.append({'actor': actor_id, 'slot': slot.get('slot'), 'reason': 'weapon unresolved'})
                continue
            for wh in slot.get('warheads', []):
                if not wh.get('versus') and wh.get('damage') is None:
                    continue
                values, errors = {}, []
                for armor, value in wh.get('versus', {}).items():
                    try:
                        number = float(value)
                        if not math.isfinite(number):
                            raise ValueError()
                        values[armor] = number
                    except (ValueError, TypeError):
                        errors.append(f'invalid Versus {armor}={value}')
                rows.append({'source': source, 'actor': actor_id, 'actor_type': actor.get('type'),
                             'cost': actor.get('cost'), 'hp': actor.get('hp'), 'build_limit': actor.get('limit'),
                             'weapon': slot.get('weapon'), 'slot': slot.get('slot'),
                             'requires_condition': slot.get('requires_condition'),
                             'pause_on_condition': slot.get('pause_on_condition'),
                             'upgrade_types': slot.get('upgrade_types'),
                             'weapon_valid_targets': slot.get('valid_targets'),
                             'warhead': wh.get('key'), 'warhead_type': wh.get('type'),
                             'damage': wh.get('damage'), 'fields': wh.get('fields', {}),
                             'declared_versus': values if not errors else None,
                             'armor_scope': 'declared values' if values else 'no explicit Versus; engine/type default requires interpretation',
                             'errors': errors, 'extraction_channels': wh.get('channels', []),
                             'actor_production_state': actor.get('production_state_evidence'),
                             'status': 'review-only; not an admitted family vote'})
    return {'source': source, 'export_sha256': hashlib.sha256(raw).hexdigest(),
            'source_metadata': meta, 'actors': len(seen), 'rows': rows, 'missing': missing,
            'scope': 'Resolved damage/armor channels; omitted armor defaults are not invented. '
                     'Alternative channels remain separate. Extraction metadata does not certify current runtime or independent lineage.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', dest='export_path', type=Path, required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = trace_export(args.export_path, args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'source': args.source, 'actors': result['actors'], 'profile_rows': len(result['rows']),
                      'malformed_profiles': sum(bool(row['errors']) for row in result['rows']),
                      'unresolved_slots': len(result['missing'])}))


if __name__ == '__main__':
    main()
