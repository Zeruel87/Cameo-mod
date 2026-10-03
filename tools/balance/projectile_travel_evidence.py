"""Read the separate, partial travel comparison without changing DPS votes."""
import json
from functools import lru_cache


@lru_cache(maxsize=1)
def load(root):
    path = root / "docs/reference/projectile_travel_evidence.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    index = {}
    for source in data["sources"]:
        speed = source.get('game_speed_declaration') or {}
        default_ms = speed.get('timestep_ms_by_speed', {}).get(speed.get('declared_default'))
        for actor in source.get('actors_without_armament', []):
            index[source['source'], actor] = [{'slot': 'N/A', 'weapon': 'N/A',
                'status': 'not_applicable', 'reason': 'No authored armament weapon in this comparison scope.'}]
        for actor, reason in source.get('actor_issues', {}).items():
            index[source['source'], actor] = [{'slot': '?', 'weapon': '?', 'status': 'unresolved', 'reason': reason}]
        for row in source["rows"]:
            for user in row["users"]:
                index.setdefault((source["source"], user["actor"]), []).append({
                    **row, "slot": user["slot"],
                    "requires_condition": user.get("requires_condition"),
                    "pause_on_condition": user.get("pause_on_condition"),
                    "distance": source["distance_world_units"], 'source_default_timestep_ms': default_ms})
    return index


def describe(rows):
    if not rows:
        return "unavailable; no reviewed travel evidence for this source actor"
    parts = []
    for row in rows:
        text = f'{row["slot"]} / {row["weapon"]}: '
        if row["status"] in ("unresolved", 'no_impact', 'source_impact', 'not_applicable'):
            text += row["reason"]
        else:
            lo, hi = row["projectile_tick_calls"]
            count = str(lo) if lo == hi else f"{lo}–{hi}"
            text += f'{row["status"]}, first impact after {count} projectile Tick calls over {row["distance"] / 1024:g} cells'
            if row.get('first_impact_phase') == 'constructor':
                text += ' (impact during creation)'
            if row.get('source_default_timestep_ms'):
                text += f'; source default {row["source_default_timestep_ms"]} ms/update'
            tracer = row.get('cosmetic_tracers')
            if tracer and tracer['count'] > 0:
                text += f'; cosmetic tracer speed {tracer["speed_world_units_per_update"]} units/update, separate from damage'
            if row.get("within_authored_range") is False:
                text += " (outside authored range)"
        if row.get("requires_condition"):
            text += f'; requires {row["requires_condition"]}'
        if row.get("pause_on_condition"):
            text += f'; paused by {row["pause_on_condition"]}'
        motion = row.get('motion_parameters')
        if motion:
            text += (f'; max speed {motion["speed_world_units_per_update"]:g} units/update'
                     f'; launch {motion["minimum_launch_speed"]:g}–{motion["maximum_launch_speed"]:g}'
                     f'; acceleration {motion["acceleration_world_units_per_update_squared"]:g} units/update²')
            if row.get('source_default_timestep_ms'):
                text += f'; source default {row["source_default_timestep_ms"]} ms/update'
        source_motion = row.get('source_motion_parameters')
        if source_motion:
            text += (f'; INI Speed {source_motion["authored_speed_input"]}'
                     f' decodes to {source_motion["configured_max_speed_leptons_per_frame"]} leptons/frame'
                     f' ({source_motion["configured_max_speed_cells_per_frame"]:g} cells/frame); frame period unverified')
        elif row.get('authored_speed_input') is not None:
            text += f'; authored INI Speed {row["authored_speed_input"]}'
        parts.append(text)
    return " | ".join(parts)
