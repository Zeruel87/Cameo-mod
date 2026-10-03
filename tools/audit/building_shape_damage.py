"""Read-only nearest-edge splash comparison for the three pilot shape exceptions.

Run with --out to save a source-backed diagnostic. Coordinates are actor-local,
unrotated and at the same height; only the main channel's falloff is compared.
This is not expected battlefield damage, a compensation factor, or a game test.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/audit'), str(ROOT / 'tools/balance')]
from miniyaml import Ruleset
from effective_damage import falloff_and_radii, runtime_falloff


def rectangle_distance(point, top_left, bottom_right):
    dx = max(top_left[0] - point[0], 0, point[0] - bottom_right[0])
    dy = max(top_left[1] - point[1], 0, point[1] - bottom_right[1])
    return math.isqrt(dx * dx + dy * dy)


def pair(value):
    return tuple(int(x.strip()) for x in value.split(','))


def build():
    rules = Ruleset(ROOT)
    names = ['^1x1Shape', 'td_nod_samsite', 'ra1_soviets_samsite',
             'ra1_allies_bastionartillerybunker']
    shapes = {}
    for name in names:
        actor = rules.resolve(name)
        shape = actor.child('HitShape').child('Type')
        assert shape.value == 'Rectangle', name
        shapes[name] = {'top_left': pair(shape.get('TopLeft')),
                        'bottom_right': pair(shape.get('BottomRight'))}
    weapons = [('ra1_soviets_v2rocketlauncher_scud', 'Warhead@MissileHE_Heavy'),
               ('ra1_allies_bastionartillerybunker_155mmbastion', 'Warhead@Concussion_Heavy')]
    scenarios = []
    for name, tag in weapons:
        weapon = rules.resolve_weapon(name)
        main = [w for w in weapon.children if w.value == 'AreaDamage' and w.key == tag]
        assert len(main) == 1, name
        warhead = main[0]
        assert (warhead.get('DamageCalculationType') or 'HitShape') == 'HitShape'
        fo, radii, supported = falloff_and_radii(warhead)
        assert supported, name
        rows = []
        for pos in [(0, 0), (1024, 0), (1536, 0), (2048, 0), (1536, 1536)]:
            values = {}
            for actor, shape in shapes.items():
                distance = rectangle_distance(pos, shape['top_left'], shape['bottom_right'])
                values[actor] = {'distance_from_edge': distance,
                                 'flat_falloff_percent': runtime_falloff(fo, radii, distance)}
            rows.append({'impact_offset': pos, 'shapes': values})
        path = Path(rules.weapon(name).file)
        scenarios.append({'weapon': name, 'warhead': warhead.key, 'falloff': fo,
                          'radii': radii, 'rows': rows,
                          'weapon_file': str(path.relative_to(ROOT)),
                          'weapon_file_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'scope': __doc__, 'shapes': shapes, 'scenarios': scenarios,
            'interpretation': [
                'AreaDamage and SpreadDamage select the closest active shape and apply a channel once per actor per tick, not once per occupied cell.',
                'A larger rectangle puts its edge closer to nearby impacts. At the center every shape gets the same100% main falloff in these examples.',
                'UseTargetableCellsOffsets adds aiming positions, not repeated rectangle damage applications.',
                'The old incoming modifiers also reduced direct damage and other affected health changes; they are not splash-only corrections.',
                'No universal inverse-footprint factor follows from these samples. Armor, percentage contribution, blast profile, approach angle and impact distribution matter.',
                'Keep hit geometry physically meaningful. Price/calibrate exposure in the balance model, or separately design an explicit area-only compensation policy; do not silently replace it with global HP scaling.'
            ]}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    result = build()
    text = json.dumps(result, indent=2) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding='utf-8')
    else:
        print(text)
    print(json.dumps({'weapons': len(result['scenarios']), 'shapes': len(result['shapes'])}))
