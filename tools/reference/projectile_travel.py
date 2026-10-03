#!/usr/bin/env python3
"""Common-distance first-impact timing for reviewed OpenRA projectiles.

Counts projectile Tick calls, not fire-order latency or wall-clock seconds.
Other projectile classes remain explicit unresolved rows until modeled.
"""
import argparse
import hashlib
import json
from math import isqrt
from pathlib import Path

from extract_peer_units import _cell_num


def timing(projectile, distance, *, bullet_round_up=False):
    if distance < 0 or int(distance) != distance:
        raise ValueError("Distance must be a nonnegative integer in world units")
    if not projectile:
        return {"status": "unresolved", "reason": "missing projectile"}
    kind = projectile["value"]
    fields = {c["key"]: c["value"] for c in projectile["children"]}
    if kind == 'InstantHitWithFakeBullets':
        return {'status': 'instant', 'projectile_tick_calls': [1, 1],
                'flight_interpolation_ticks': [0, 0], 'first_impact_phase': 'first Tick',
                'cosmetic_tracers': {'count': int(fields.get('FakeBulletNumber', '0')),
                    'speed_world_units_per_update': int(fields.get('FakeBulletSpeed', '1024')),
                    'spawn_interval_updates': int(fields.get('FakeBulletSpawnInterval', '3')),
                    'scope': 'Visual only; these fields do not delay the damage impact.'}}
    if kind == 'InstantExplode':
        return {'status': 'source_impact', 'reason': 'Impact at firing source on first Tick; no travel to the sampled target.'}
    if kind == 'ElectricBolt':
        return {'status': 'instant_on_create', 'projectile_tick_calls': [0, 0],
                'flight_interpolation_ticks': [0, 0], 'first_impact_phase': 'constructor'}
    if kind in ('LaserZap', 'LaserZapCA', 'TeslaZap', 'TeslaZapCA', 'LightningZap'):
        duration = int(fields.get('DamageDuration', '1'))
        if kind in ('TeslaZap', 'TeslaZapCA', 'LightningZap'):
            duration = min(duration, int(fields.get('Duration', '3' if kind == 'LightningZap' else '2')))
        if duration <= 0:
            return {'status': 'no_impact', 'reason': 'DamageDuration suppresses weapon impacts'}
        return {'status': 'instant', 'projectile_tick_calls': [1, 1],
                'flight_interpolation_ticks': [0, 0], 'first_impact_phase': 'first Tick',
                'later_impact_schedule': 'separate from first-impact travel'}
    if kind in ('InstantHit', 'RadBeam', 'Railgun', 'RailgunCA'):
        return {"status": "instant", "projectile_tick_calls": [1, 1],
                "flight_interpolation_ticks": [0, 0], 'first_impact_phase': 'first Tick'}
    if kind in ('Missile', 'MissileCA'):
        speed = _cell_num(fields.get('Speed', '384'))
        minimum = _cell_num(fields.get('MinimumLaunchSpeed', '-1'))
        maximum = _cell_num(fields.get('MaximumLaunchSpeed', '-1'))
        acceleration = _cell_num(fields.get('Acceleration', '5'))
        if any(v is None for v in (speed, minimum, maximum, acceleration)):
            return {'status': 'unresolved', 'reason': 'unreadable missile motion parameter'}
        return {'status': 'unresolved',
                'reason': 'Guided arrival needs a trajectory model; parameters below are not arrival times.',
                'motion_parameters': {'speed_world_units_per_update': speed,
                    'minimum_launch_speed': speed if minimum < 0 else minimum,
                    'maximum_launch_speed': speed if maximum < 0 else maximum,
                    'acceleration_world_units_per_update_squared': acceleration,
                    'basis': 'Resolved declarations with reviewed engine defaults; launch selection and guidance not simulated.'}}
    if kind not in ("Bullet", 'BulletCA'):
        return {"status": "unresolved", "reason": f"unmodeled class: {kind}"}
    if int(fields.get("BounceCount", "0")):
        return {"status": "unresolved", "reason": "bouncing projectile"}
    speeds = [_cell_num(v.strip()) for v in fields.get("Speed", "17").split(",")]
    if len(speeds) not in (1, 2) or any(v is None or v <= 0 or int(v) != v for v in speeds):
        return {"status": "unresolved", "reason": "invalid speed interval"}
    lo = int(speeds[0])
    # SharedRandom.Next(min,max) excludes max in both reviewed engines.
    hi = int(speeds[1]) - 1 if len(speeds) == 2 else lo
    if hi < lo:
        return {"status": "unresolved", "reason": "empty speed interval"}
    altitude = _cell_num(fields.get('AirburstAltitude')) or 0
    if int(altitude) != altitude:
        return {'status': 'unresolved', 'reason': 'noninteger airburst altitude'}
    path_distance = isqrt(distance * distance + max(int(altitude), 0) ** 2)
    def length(speed):
        return max((path_distance + speed - 1) // speed if bullet_round_up else path_distance // speed, 1)
    lengths = [length(hi), length(lo)]
    return {"status": "nominal_bullet", "speed_world_units_per_tick": [lo, hi],
            "flight_interpolation_ticks": lengths,
            "projectile_tick_calls": [v + 1 for v in lengths],
            'endpoint_distance_world_units': path_distance,
            'flight_length_rounding': 'up' if bullet_round_up else 'down'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--distance", type=int, default=4096)
    args = parser.parse_args()
    source = json.loads(args.evidence.read_text(encoding="utf-8"))
    expected = ("ab9e477c3db818e91946d4cfdc86e71012966141" if source["mod_id"] == "ca"
                else "bbd36d9e6a2d7f0d3b24f102858af6dc8caf8a78")
    if source["mod_id"] not in ("ra", "cnc", "ts", "d2k", "ca") or source["checkout_head"] != expected:
        raise ValueError("Engine behavior has not been reviewed for this mod")
    rows = []
    for weapon in source["weapons"]:
        row = {"weapon": weapon["weapon"], "users": weapon["users"],
               **timing(weapon["projectile"], args.distance)}
        reach = _cell_num(weapon.get("range"))
        minimum = _cell_num(weapon.get('min_range')) or 0
        row["within_authored_range"] = minimum <= args.distance <= reach if reach is not None else None
        rows.append(row)
    result = {"schema": 1, "source": source["source"],
              'game_speed_declaration': source.get('game_speed_declaration'),
              'actors_without_armament': source.get('actors_without_armament', []),
              "declarations_sha256": hashlib.sha256(args.evidence.read_bytes()).hexdigest(),
              "checkout_head": source["checkout_head"],
              "distance_world_units": args.distance, "rows": rows,
              "scenario": "Same-height fixed source/target with stated horizontal separation; Bullet airburst offset included. No scatter, obstacles, speed modifiers or bounce.",
              "limitations": [
                  "Tick calls start at the projectile's first Tick, not the firing order.",
                  "Seconds require the chosen game speed; none is assumed here.",
                  "Out-of-range samples are mathematical comparisons, not legal firing scenarios.",
                  "No hit probability or moving-target guidance claim.",
                  "First impact only: beam visual duration and later impacts are separate.",
                  "Guided missiles and other unreviewed classes remain unresolved."]}
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    from collections import Counter
    print(json.dumps(dict(Counter(r["status"] for r in rows))))


if __name__ == "__main__":
    main()
