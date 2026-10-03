#!/usr/bin/env python3
"""Resolve projectile declarations for an existing pinned peer corpus.

This separate evidence lane does not change nominal DPS or invent travel times.
Missing fields require defaults from the matching engine, not another checkout.
"""
import argparse
import hashlib
import json
from pathlib import Path

import extract_peer_units as peer


def tree(node):
    return {"key": node.key, "value": node.value,
            "children": [tree(c) for c in node.children]}


def extract(root, corpus):
    raw = corpus.read_bytes()
    records = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    meta = records[0]
    provenance = meta["provenance"]
    mod = provenance["mod_id"]
    identity = peer.git_identity(root)
    expected = provenance["checkout_head"]
    # A different commit cannot silently supply missing fields for this corpus.
    import subprocess
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if actual != expected:
        raise ValueError(f"Source commit mismatch: {actual} != {expected}")
    inputs = peer.collect_read_inputs(root, mod)
    before = peer.hash_inputs(inputs)
    if peer.engine_input_digest(before) != provenance["inputs_digest"]:
        raise ValueError("Source inputs differ from the pinned corpus")
    rules = peer.miniyaml.Ruleset(root, mod)
    speed_nodes = [n for path in rules.manifest.sources for n in peer.miniyaml.load(path)
                   if n.key == 'GameSpeeds']
    timebase = None
    if len(speed_nodes) == 1:
        definition = speed_nodes[0]
        default = definition.get('DefaultSpeed')
        speeds = definition.child('Speeds')
        if speeds and default:
            timebase = {'declared_default': default,
                        'timestep_ms_by_speed': {n.key: int(n.get('Timestep')) for n in speeds.children},
                        'scope': 'Declared source defaults; actual lobby speed not observed.'}
    users = {}
    for actor in records[1:]:
        for slot in actor.get("weapon_evidence", []):
            weapon = slot.get("weapon")
            if weapon:
                users.setdefault(weapon, []).append({
                    "actor": actor["id"], "slot": slot["slot"],
                    "requires_condition": slot.get("requires_condition"),
                    "pause_on_condition": slot.get("pause_on_condition")})
    weapons = []
    for weapon, slots in sorted(users.items()):
        resolved = rules.resolve_weapon(weapon)
        projectile = resolved.child("Projectile") if resolved else None
        weapons.append({"weapon": weapon, "users": slots,
                        "range": resolved.get("Range") if resolved else None,
                        'min_range': resolved.get('MinRange') if resolved else None,
                        "projectile": tree(projectile) if projectile else None,
                        "status": "declarations_only" if projectile else "unresolved"})
    after = peer.hash_inputs(inputs)
    if before != after:
        raise ValueError("Source inputs changed during extraction")
    return {"schema": 1, "source": provenance["source_label"],
            "mod_id": mod, "checkout_head": actual,
            "checkout_identity": identity,
            "corpus_sha256": hashlib.sha256(raw).hexdigest(),
            "source_inputs_match_corpus": True,
            'game_speed_declaration': timebase,
            'actors_without_armament': [r['id'] for r in records[1:]
                if not any(s.get('weapon') for s in r.get('weapon_evidence', []))],
            "source_inputs": before, "weapons": weapons,
            "limitations": ["Resolved YAML declarations; engine defaults not applied.",
                "No travel-time, hit-probability or runtime certification.",
                "Conditional slots are retained, not assumed simultaneously active."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = extract(args.root.resolve(), args.corpus)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source": result["source"], "weapons": len(result["weapons"])}))


if __name__ == "__main__":
    main()
