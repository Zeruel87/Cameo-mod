#!/usr/bin/env python3
"""Current pilot armament travel evidence, separate from frozen self-vote stats."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools/audit'), str(ROOT/'tools/balance')]
from miniyaml import Ruleset, load, load_manifest
import reference_distribution as rd
from projectile_evidence import tree
from projectile_travel import timing
from extract_peer_units import _cell_num


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    manifest = load_manifest(ROOT)
    inputs = set(manifest.sources + manifest.rules + manifest.weapons)
    before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    rules = Ruleset(ROOT)
    if inputs != set(rules.manifest.sources + rules.manifest.rules + rules.manifest.weapons):
        raise ValueError('Cameo manifest changed during extraction')
    actors = sorted({r['id'] for r in rd.cameo_rows()+rd.cameo_hero_rows()
                     if r['id'].startswith(('td_gdi_', 'td_nod_', 'ra1_allies_', 'ra1_soviets_'))})
    users = {}
    for actor in actors:
        for arm in rules.resolve(actor).children_named('Armament'):
            name = arm.get('Weapon')
            if name:
                users.setdefault(name, []).append({'actor': actor, 'slot': arm.key,
                    'requires_condition': arm.get('RequiresCondition'),
                    'pause_on_condition': arm.get('PauseOnCondition')})
    rows = []
    for name, slots in sorted(users.items()):
        weapon = rules.resolve_weapon(name)
        projectile = weapon.child('Projectile')
        kind = projectile.value if projectile else None
        streak = (_cell_num(projectile.get('ProjectileStreakLength')) or 0) if projectile else 0
        result = timing(tree(projectile) if projectile else None, 4096,
                        bullet_round_up=kind == 'Bullet' and streak > 0)
        if projectile is None:
            result = {'status': 'not_applicable',
                      'reason': 'No projectile declared; trait-driven actions are outside this timing lane.'}
        reach = _cell_num(weapon.get('Range'))
        minimum = _cell_num(weapon.get('MinRange')) or 0
        rows.append({'weapon': name, 'users': slots, 'projectile_type': kind,
                     'projectile_declaration': tree(projectile) if projectile else None,
                     'within_authored_range': minimum <= 4096 <= reach if reach is not None else None,
                     **result})
    speed_nodes = [n for p in rules.manifest.sources for n in load(p) if n.key == 'GameSpeeds']
    if len(speed_nodes) != 1:
        raise ValueError('Ambiguous Cameo game-speed declaration')
    speed = speed_nodes[0]
    engine_files = ('OpenRA.Mods.Common/Projectiles/Bullet.cs',
                    'OpenRA.Mods.Common/Projectiles/Missile.cs',
                    'OpenRA.Mods.Common/Projectiles/InstantHit.cs',
                    'OpenRA.Mods.Common/Projectiles/LaserZap.cs',
                    'OpenRA.Mods.Common/Projectiles/Railgun.cs',
                    'OpenRA.Mods.AS/Projectiles/RadBeam.cs',
                    'OpenRA.Mods.AS/Projectiles/InstantExplode.cs')
    engine_hashes = {p: hashlib.sha256((args.engine_root/p).read_bytes()).hexdigest() for p in engine_files}
    custom = ('OpenRA.Mods.Cameo/Projectiles/InstantHitWithFakeBullets.cs',
              'OpenRA.Mods.Cameo/Projectiles/LightningZap.cs')
    custom_hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in custom}
    reviewed = json.loads((ROOT/'docs/reference/cameo_projectile_engine_review.json').read_text())
    if engine_hashes != reviewed['engine_sources'] or custom_hashes != reviewed['custom_sources']:
        raise ValueError('Projectile source changed since model review')
    after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    if before != after:
        raise ValueError('Cameo inputs changed during extraction')
    data = {'source': 'Cameo current', 'actor_count': len(actors), 'distance_world_units': 4096,
            'scope': 'Current pilot armament slots; conditional variants retained, not summed. Local source model, not DLL/runtime certification. Descendant shrapnel travel is not included.',
            'source_inputs': before, 'engine_sources': engine_hashes,
            'custom_sources': custom_hashes,
            'actors_without_armament': sorted(set(actors) - {u['actor'] for slots in users.values() for u in slots}),
            'game_speed_declaration': {'declared_default': speed.get('DefaultSpeed'),
                'timestep_ms_by_speed': {s.key: int(s.get('Timestep')) for s in speed.child('Speeds').children},
                'scope': 'Declared source default; actual lobby speed not observed.'}, 'rows': rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    from collections import Counter
    print(json.dumps({'actors': len(actors), 'weapons': len(rows),
                      'status': dict(Counter(r['status'] for r in rows))}))


if __name__ == '__main__':
    main()
