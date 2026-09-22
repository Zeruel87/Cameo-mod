#!/usr/bin/env python3
"""DTA projectile declarations and bounded OpenTS speed decoding.

No first-impact time is invented for an unmodeled trajectory or unknown frame rate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from extract_ini_units import read_ini, merge_overlay, bool_value, num


def decode_speed(value):
    """OpenTS Get_MPHType / _Scale_To_256, with WeaponType's zero default."""
    number = 0 if value is None else int(value)
    return min(255, min(100, max(0, number)) * 256 // 100)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', required=True, type=Path)
    parser.add_argument('--ini-dir', required=True, type=Path)
    parser.add_argument('--engine-root', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    inputs = {name: hashlib.sha256((args.ini_dir/name).read_bytes()).hexdigest()
              for name in ('Rules.ini', 'Enhance.ini')}
    matrix = json.loads(args.matrix.read_text())
    provenance = matrix['export_sha256']['DTA Enhanced']
    assert inputs['Rules.ini'] == provenance['rules_sha256']
    assert inputs['Enhance.ini'] == provenance['enhance_sha256']
    ini = merge_overlay(read_ini(args.ini_dir/'Rules.ini'), read_ini(args.ini_dir/'Enhance.ini'))
    actors = sorted({ref['id'] for row in matrix['rows'] for ref in row['references']
                     if ref['source'] == 'DTA Enhanced'})
    users, empty, issues = {}, [], {}
    for actor in actors:
        if actor not in ini:
            issues[actor] = 'Actor absent from the supplied DTA INIs'
            continue
        bindings = []
        for slot in ('Primary', 'Secondary', 'Elite', 'ElitePrimary', 'EliteSecondary'):
            weapon = ini[actor].get(slot)
            if weapon and weapon.lower() != 'none':
                bindings.append(weapon)
                users.setdefault(weapon, []).append({'actor': actor, 'slot': slot,
                    'requires_condition': 'elite state' if slot.startswith('Elite') else None,
                    'actor_trainable_declaration': ini[actor].get('Trainable')})
        if not bindings:
            empty.append(actor)
    rows = []
    for name, slots in sorted(users.items()):
        weapon = ini.get(name, {})
        projectile = ini.get(weapon.get('Projectile'), {})
        row = {'weapon': name, 'users': slots, 'status': 'unresolved',
               'weapon_fields': weapon, 'projectile_type': weapon.get('Projectile'),
               'projectile_fields': projectile,
               'reason': 'DTA first-impact timing is not yet modeled.'}
        reach, minimum = num(weapon.get('Range')), num(weapon.get('MinimumRange'), 0)
        row['within_authored_range'] = minimum <= 4 <= reach if reach is not None else None
        if not weapon or not projectile:
            row['reason'] = 'Missing weapon or projectile section in the supplied INIs'
        elif bool_value(projectile.get('Inviso')):
            row['reason'] = 'Invisible projectile; first-impact frame not certified from this declaration alone.'
            row['authored_speed_input'] = weapon.get('Speed')
        elif int(projectile.get('ROT', '0')) == 0:
            row['reason'] = 'Ballistic: reviewed OpenTS initialization derives speed from range/gravity, replacing the INI speed.'
            row['authored_speed_input'] = weapon.get('Speed')
        else:
            speed = decode_speed(weapon.get('Speed'))
            row['source_motion_parameters'] = {
                'authored_speed_input': weapon.get('Speed'),
                'configured_max_speed_leptons_per_frame': speed,
                'configured_max_speed_cells_per_frame': speed / 256,
                'configured_acceleration_leptons_per_frame_squared': int(projectile.get('Acceleration', '3')),
                'rot': int(projectile['ROT']),
                'scope': 'Reviewed OpenTS parameter decoding; launch/turn/target/altitude and actual DTA frame period remain unmodeled.'}
        rows.append(row)
    for name, digest in inputs.items():
        assert hashlib.sha256((args.ini_dir/name).read_bytes()).hexdigest() == digest
    engine_files = ('ccini.cpp', 'mph.hh', 'weapon.cpp', 'bullettype.cpp', 'bullet.cpp')
    result = {'schema': 1, 'source': 'DTA Enhanced', 'actor_count': len(actors),
              'distance_world_units': 4096, 'distance_source_cells': 4,
              'distance_source_leptons': 1024,
              'distance_basis': 'world_units uses the shared 1024-units-per-cell comparison convention; DTA uses 256 leptons per cell.',
              'scope': 'All bound primary/secondary/elite weapons of selected DTA reference actors; declarations, not additional votes or runtime certification.',
              'inputs': inputs, 'actors_without_armament': empty, 'actor_issues': issues,
              'engine_commit': subprocess.check_output(['git', '-C', str(args.engine_root), 'rev-parse', 'HEAD'], text=True).strip(),
              'engine_sources': {p: hashlib.sha256((args.engine_root/'code'/p).read_bytes()).hexdigest() for p in engine_files},
              'game_speed_declaration': None, 'frame_period_status': 'Not established from supplied files; no cross-engine seconds or averaging inferred.',
              'rows': rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'actors': len(actors), 'weapons': len(rows),
                      'decoded_motion_parameters': sum('source_motion_parameters' in r for r in rows), 'actor_issues': issues}))


if __name__ == '__main__':
    main()
