"""Inventory explicit trait-level secondary weapon routes.

This is a diagnostic-only inventory. It records authored references and their
resolution status; it does not infer damage, activation, reachability, or
runtime impact. The allowlist is deliberately narrow so unknown trait fields
are left unclassified instead of being guessed as weapon references.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from miniyaml import Ruleset


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "secondary-payload-routes.v1"

# Keep the field allowlist visible and explicit. Trait suffixes (for example
# FireWarheadsOnDeath@Upgrade) are matched by the base key before ``@``.
TRAIT_FIELDS = {
    "Armament": {"CasingWeapon": "casing"},
    "FallsToEarth": {"Explosion": "falls_to_earth_explosion"},
    "FireWarheadsOnDeath": {
        "Weapon": "death_weapon",
        "Weapons": "death_weapon",
        "EmptyWeapon": "death_empty_weapon",
    },
    "FireWarheadsOnDeathCA": {
        "Weapon": "death_weapon",
        "Weapons": "death_weapon",
        "EmptyWeapon": "death_empty_weapon",
    },
    # ``Explodes`` was renamed by the engine update rule. It remains an
    # explicit compatibility alias; no other similarly named traits match.
    "Explodes": {
        "Weapon": "death_weapon",
        "Weapons": "death_weapon",
        "EmptyWeapon": "death_empty_weapon",
    },
    "FireWarheads": {
        "Weapons": "fire_warheads_weapon",
    },
}

# These are the effect/support traits whose C# info types explicitly declare
# ImpactWeapon. TeleportWeapon is intentionally outside this allowlist.
IMPACT_WEAPON_TRAITS = {
    "ExplodeWeaponTeleportEffect",
    "RA2ChronoshiftPower",
    "RecallPower",
}


def _tokens(value: str | None) -> list[str]:
    """Split an authored reference list while preserving token spelling."""

    if value is None:
        return []
    return [token.strip() for token in value.split(",") if token.strip()]


def _location(node):
    """Return a JSON-safe source location for a MiniYAML node."""

    return {"file": node.file or None, "line": node.line or None}


def _provenance(actor, trait, field):
    """Keep the resolved actor, trait, and field source locations explicit."""

    return {
        "actor": _location(actor),
        "trait": _location(trait),
        "field": _location(field),
    }


def _route_spec(trait_key: str, field_key: str):
    base = trait_key.split("@", 1)[0]
    if base in TRAIT_FIELDS and field_key in TRAIT_FIELDS[base]:
        return TRAIT_FIELDS[base][field_key]
    if base in IMPACT_WEAPON_TRAITS and field_key == "ImpactWeapon":
        return "impact_weapon"
    return None


def _resolved_weapon(rs, token):
    target = rs.weapon(token)
    return target, (getattr(target, "key", None) if target is not None else None)


def _route_record(actor_name, actor, trait, field, token, route_kind, rs):
    target, resolved_name = _resolved_weapon(rs, token)
    resolution = "resolved" if target is not None else "missing"
    return {
        "actor": actor_name,
        "trait_key": trait.key,
        "field_path": f"{trait.key}.{field.key}",
        "weapon_token": token,
        "resolved_weapon": resolved_name,
        "resolution": resolution,
        "route_kind": route_kind,
        "raw_field_value": field.value,
        "provenance": _provenance(actor, trait, field),
        "duplicate_count": 1,
    }


def inventory(rs):
    """Return unique explicit trait-level references from an active Ruleset.

    Actor and trait resolution is delegated to ``miniyaml.Ruleset``. A route
    identity is ``(actor, trait key, field path, raw token, route kind)``;
    repeated identities are collapsed and represented by ``duplicate_count``.
    Counts are over unique route records, while each record retains its raw
    authored value and occurrence count.
    """

    routes = []
    by_identity = {}
    actors = getattr(rs, "actors", {})
    for actor_name in sorted(actors):
        if actor_name.startswith("^"):
            continue
        actor = rs.resolve(actor_name)
        if actor is None:
            continue
        for trait in actor.children:
            for field in trait.children:
                route_kind = _route_spec(trait.key, field.key)
                if route_kind is None:
                    continue
                for token in _tokens(field.value):
                    route = _route_record(actor_name, actor, trait, field, token,
                                          route_kind, rs)
                    identity = (actor_name, trait.key, route["field_path"],
                                token, route_kind)
                    existing = by_identity.get(identity)
                    if existing is None:
                        by_identity[identity] = route
                        routes.append(route)
                    else:
                        existing["duplicate_count"] += 1

    by_kind = Counter(route["route_kind"] for route in routes)
    by_resolution = Counter(route["resolution"] for route in routes)
    duplicate_occurrences = sum(route["duplicate_count"] - 1 for route in routes)
    counts = {
        "route_kind": dict(sorted(by_kind.items())),
        "resolution": dict(sorted(by_resolution.items())),
        "unique_routes": len(routes),
        "total_occurrences": sum(route["duplicate_count"] for route in routes),
        "duplicate_occurrences": duplicate_occurrences,
    }
    return {
        "schema": SCHEMA,
        "scope": "active concrete actor definitions; resolved trait-level allowlist",
        "counts": counts,
        "routes": routes,
        "limitations": [
            "This is diagnostic-only: no damage, activation, reachability, geometry, or DPS inference.",
            "Only the explicit TRAIT_FIELDS and IMPACT_WEAPON_TRAITS allowlist is classified.",
            "Unknown traits and fields, script/map references, spawned actors, and weapon graph edges are omitted.",
            "Only concrete actors are enumerated; actor names beginning with '^' are templates and excluded.",
            "Resolved field provenance identifies the MiniYAML node retained by Ruleset resolution; it does not prove runtime activation.",
            "TeleportWeapon and other non-allowlisted support/effect fields are intentionally unclassified.",
            "Counts are over unique route identities; duplicate authored occurrences remain in duplicate_count.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        help="write the JSON inventory to this path; stdout otherwise")
    args = parser.parse_args(argv)
    report = inventory(Ruleset(ROOT))
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
