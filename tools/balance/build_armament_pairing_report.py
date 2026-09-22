#!/usr/bin/env python3
"""Per-armament reference pairing: the cannon's reference, and the missile's, kept apart.

    python tools/balance/build_armament_pairing_report.py            # summary
    python tools/balance/build_armament_pairing_report.py --actor td_gdi_firehawk
    python tools/balance/build_armament_pairing_report.py --write    # docs/balance/derived/

WHAT THIS IS, AND WHAT IT IS NOT. It reads the EXISTING actor-to-actor assignment
(`reference_assignment.json`) and, inside each already-decided pair, matches the two units'
armaments by targeting role. It re-scores nothing, re-assigns nothing and writes no balance
number — clause 2 of the matching law ("at most ONE reference unit per source") is untouched,
because this splits what the pair MEANS, not which pair it is.

⛔ THE DEFECT IT MEASURES. `armament_profile` folds an actor's baseline armaments into one
`w_range` / `w_damage` / `w_dps`, taking `max(ranges)` for the range. On a single-weapon unit that
is exactly right. On `td_gdi_firehawk` it reports the Sidewinders' 12,500 for a bomb that reaches
1,250 — a TEN-FOLD error inside one row, and the maintainer named it before the tooling found it:

    "those fire bombs and the sidewinder anti air missiles have separate ranges ...
     Those two weapons are so different they should not be mixed."

⭐ THE PAIRING KEY IS THE TARGETING ENVELOPE, not the weapon's name — see `armament_roles`, which
carries the reasoning, the measured token vocabularies and the reason a name test cannot work.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "reference"))

import armament_roles as ar           # noqa: E402
import assign_references as asg       # noqa: E402
import miniyaml                       # noqa: E402
import peer_corpus                    # noqa: E402
import reference_distribution as rd   # noqa: E402
import extract_ini_projectile_roles as ipr  # noqa: E402
import extract_ini_armament_roles as iar     # noqa: E402
import extract_ini_elite_weapons as ielite     # noqa: E402

ROOT = rd.ROOT
ASSIGNMENT = ROOT / "docs" / "balance" / "derived" / "reference_assignment.json"
OUT = ROOT / "docs" / "balance" / "derived" / "armament_pairing.json"
PAIRING_SCHEMA = 3

PAIR_FIELDS = ("slot", "weapon", "role", "range", "range_unit", "range_wdist",
               "damage_per_shot", "damage_per_cycle", "cycle", "rate", "gate",
               "weapon_reload", "weapon_burst", "weapon_burst_delays")

# Sources that reach the reference map as hand-maintained Doc 5 markdown tables rather than as an
# extracted corpus. They carry ONE folded weapon column by construction, so there is no second
# armament to pair and never was. Listed explicitly so a NEW source that fails to index is
# reported as the defect it would be, instead of joining a silent bucket.
STRUCTURELESS_SOURCES = frozenset({
    "Romanov's Vengeance", "Shattered Paradise", "Valiant Shades", "Crystallized Nexus",
    "Generals Alpha", "OpenRA Dune II", "OpenE2140", "OpenHV",
})


def peer_index():
    """{(source, ID): record} over BOTH corpora, keyed the way the assignment names them.

    The OpenRA half keeps `weapon_evidence` verbatim (`structured_peer_rows` copies the record),
    and the INI half is read raw rather than through `ini_rows`, because `ini_rows` carries the
    `w2_*` twin only for the handful of rows in the reviewed selection profile — and the secondary
    weapon is precisely what this tool exists to pair.
    """
    index = {}
    for source, (_meta, records) in peer_corpus.load(ROOT).items():
        for record in records:
            index[(source, str(record.get("id", "")).upper())] = ("openra", record)
    path = ROOT / "docs" / "reference" / "ini_corpus.json"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        index.setdefault((record.get("source"), str(record.get("id", "")).upper()),
                         ("ini", record))
    return index


DATA_INPUT_FILES = (
    "docs/reference/ini_corpus.json",
    "docs/reference/ini_armament_role_evidence.json",
    "docs/reference/ini_source_pins.json",
    "docs/reference/ini_projectile_role_evidence.json",
    "docs/reference/ini_elite_weapon_evidence.json",
    "docs/balance/derived/reference_assignment.json",
    "docs/reference/peer_corpus/index.json",
)

TOOL_INPUT_FILES = (
    "tools/audit/miniyaml.py",
    "tools/balance/armament_roles.py",
    "tools/balance/assign_references.py",
    "tools/balance/build_armament_pairing_report.py",
    "tools/balance/class_membership.py",
    "tools/balance/explain_unit.py",
    "tools/balance/faction_routes.py",
    "tools/balance/formula.py",
    "tools/balance/ini_cycle_evidence.py",
    "tools/balance/ini_range_evidence.py",
    "tools/balance/ini_weapon_selection.py",
    "tools/balance/peer_base_state.py",
    "tools/balance/peer_corpus.py",
    "tools/balance/peer_nominal_evidence.py",
    "tools/balance/peer_range_evidence.py",
    "tools/balance/reference_distribution.py",
    "tools/balance/reference_lineages.py",
    "tools/balance/synthesize_reference.py",
    "tools/reference/extract_ini_elite_weapons.py",
    "tools/reference/extract_ini_armament_roles.py",
    "tools/reference/extract_ini_projectile_roles.py",
    "tools/reference/extract_ini_units.py",
    "tools/reference/ini_source_pins.py",
)


def input_paths(root=ROOT):
    """Every repository file whose contents can change the pairing artifact."""
    root = pathlib.Path(root).resolve()
    paths = {root / rel for rel in DATA_INPUT_FILES + TOOL_INPUT_FILES}
    paths.update(peer_corpus.input_paths(root))
    paths.update(path for path in (root / "docs" / "balance").glob("*.json")
                 if path.name != "class_anchors.json")

    rules = miniyaml.Ruleset(root)
    for path in rules.manifest.sources + rules.manifest.rules + rules.manifest.weapons:
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            continue
        # engine/ is an ignored local runtime whose presence differs by checkout. The portable
        # artifact is derived from the repository-owned Cameo sources and must verify identically
        # in a clean worktree without an engine junction.
        if rel.parts and rel.parts[0] != "engine":
            paths.add(resolved)

    missing = [path for path in paths if not path.is_file()]
    if missing:
        names = ", ".join(sorted(path.relative_to(root).as_posix() for path in missing))
        raise ValueError(f"armament pairing input missing: {names}")
    return tuple(sorted(paths, key=lambda path: path.relative_to(root).as_posix()))


def input_fingerprints(root=ROOT):
    """Portable {repo-relative path: sha256} for every text input to this artifact.

    Git may materialise the same text as LF or CRLF in different worktrees. Canonicalise line
    endings so that checkout policy cannot make an unchanged artifact look stale. Raw byte pins
    for external evidence remain enforced separately by peer_corpus and the INI extractors.
    """
    root = pathlib.Path(root).resolve()
    return {path.relative_to(root).as_posix(): canonical_text_sha256(path)
            for path in input_paths(root)}


def canonical_text_sha256(path):
    data = pathlib.Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def peer_views_for(kind, record, projectile_roles, elite_weapons):
    return (ar.peer_views(record) if kind == "openra"
            else ar.ini_views(record, projectile_roles, elite_weapons))


def build(only_actor=None):
    assignment = json.loads(ASSIGNMENT.read_text(encoding="utf-8"))["assignment"]
    ledger = asg.ledger()
    rules = miniyaml.Ruleset(ROOT)
    projectile_roles = ipr.load(ROOT)
    projectile_roles.update(iar.load(ROOT))
    elite_weapons = ielite.load(ROOT)
    peers = peer_index()

    actors, unknown_tokens = {}, collections.Counter()
    stats = collections.Counter()
    # Coverage is keyed by weapon identity. A successful match for one cannon must not hide a
    # second cannon merely because both share the same role.
    covered, wanted, structured = {}, {}, set()
    for actor in sorted(assignment):
        if only_actor and actor != only_actor:
            continue
        record = ledger.get(actor)
        if record is None:
            continue
        cam = ar.cameo_views(record, rules)
        if not cam:
            continue
        for v in cam:
            unknown_tokens.update(v["unknown_targets"])
        cam_armaments = ar.cameo_armaments(cam)
        cam_roles = {view["role"] for view in cam_armaments}
        # ⭐ THE TIER DECIDES WHICH PEER WEAPONS ARE ON THE BENCH (maintainer, 2026-09-13):
        # originals reference the BASE weapon, promotion/expanded actors the elite or upgraded
        # replacement. See `armament_roles.tier_bench` for the rule and for why MTNK's dummy is
        # the one case where an elite weapon is genuinely additional.
        tier = ar.reference_tier(assignment[actor])
        stats[f"actors_tier_{tier}"] += 1
        stats["actors"] += 1
        wanted[actor] = {(view["weapon"], view["role"]) for view in cam_armaments}
        if len(cam_roles) > 1:
            stats["multi_role_actors"] += 1

        sources = {}
        for source, meta in sorted(assignment[actor].items()):
            found = peers.get((source, str(meta.get("id", "")).upper()))
            if found is None:
                # ⚠ TWO VERY DIFFERENT ABSENCES, AND LUMPING THEM WAS THE FIRST DRAFT'S BUG.
                # `STRUCTURELESS_SOURCES` never had per-armament evidence to begin with — they
                # reach the map as hand-maintained Doc 5 markdown TABLES with one folded weapon
                # column — so abstaining is the correct and permanent answer for them. A miss in
                # any OTHER source means the assignment names a row the corpus does not hold,
                # which is a real finding. Measured 2026-09-13: 157 misses, ALL of them the
                # first kind, across eight sources.
                structureless = source in STRUCTURELESS_SOURCES
                sources[source] = {
                    "peer": meta.get("id"),
                    "status": ("no structured corpus for this source — Doc 5 markdown only"
                               if structureless else "peer row absent from the structured corpus"),
                }
                stats["abstained_structureless" if structureless
                      else "peer_row_missing_UNEXPECTED"] += 1
                continue
            kind, peer_record = found
            structured.add(actor)
            peer = peer_views_for(kind, peer_record, projectile_roles, elite_weapons)
            for v in peer:
                unknown_tokens.update(v["unknown_targets"])
            pairs, cam_only, peer_only = ar.pair_by_role(cam, peer, tier=tier)
            stats["pairs"] += len(pairs)
            stats["exact_pairs"] += sum(1 for p in pairs if p[3])
            stats["cameo_armaments_without_a_reference"] += len(cam_only)
            for role, cameo_view, peer_view, exact in pairs:
                stats[f"pairs_role_{role}"] += 1
                covered.setdefault(actor, set()).add(cameo_view["weapon"])
                # Two admitted kinds of pair remain: an exact role match, and a proven `both`
                # stand-in. An unproven role has already abstained in pair_by_role.
                if peer_view.get("gate"):
                    stats["pairs_from_a_rank_gated_weapon"] += 1
                if exact:
                    continue
                stats["pairs_role_unproven" if peer_view["role"] is None
                      else "pairs_via_both_fallback"] += 1
            for v in cam_only:
                stats[f"unreferenced_role_{v['role']}"] += 1
            # ⛔ THE HEADLINE. A pair is CONTAMINATED when the actor fires in more than one role
            # and the folded model gave it a single number — every such row is a number the map
            # currently draws between two different weapons.
            if len(cam_roles) > 1 and pairs:
                stats["contaminated_rows"] += 1
            sources[source] = {
                "peer": peer_record.get("id"),
                "peer_name": peer_record.get("name"),
                "kind": kind,
                "pairs": [{"role": role, "exact": exact,
                           "cameo": {k: c[k] for k in PAIR_FIELDS},
                           "peer": {k: p[k] for k in PAIR_FIELDS}}
                          for role, c, p, exact in pairs],
                "cameo_unpaired": [v["weapon"] for v in cam_only],
                "peer_unpaired": [v["weapon"] for v in peer_only],
            }
        actors[actor] = {
            "roles": sorted(cam_roles, key=lambda role: (role is None, str(role))),
            "armaments": [{k: v[k] for k in PAIR_FIELDS + ("baseline", "note")} for v in cam],
            "sources": sources,
        }
    # ⛔ TWO REASONS A WEAPON ENDS UP UNCOVERED, AND COUNTING THEM TOGETHER MAKES THE NUMBER LIE.
    # Track whether any assigned source supplied a structured row independently from whether a
    # compatible weapon pair was found. Then report every missing weapon identity, so one matched
    # cannon cannot hide a second cannon with the same role.
    uncovered, no_structured = {}, []
    for actor, armaments in wanted.items():
        missing = sorted((weapon, role) for weapon, role in armaments
                         if weapon not in covered.get(actor, set()))
        if not missing:
            continue
        if actor in structured:
            uncovered[actor] = [{"weapon": weapon, "role": role}
                                for weapon, role in missing]
            for _weapon, role in missing:
                stats[f"uncovered_despite_a_structured_reference_{role or 'unproven'}"] += 1
        else:
            no_structured.append(actor)
    stats["actors_with_an_uncovered_armament"] = len(uncovered)
    stats["actors_with_no_structured_reference_at_all"] = len(no_structured)
    return {
        "schema": PAIRING_SCHEMA,
        # ⛔ WHAT THIS DOCUMENT WAS BUILT FROM, so a consumer can refuse a STALE one (Astra,
        # PR #375 blocker 4 and follow-up). `build_reference_report.pairing_document` rebuilds
        # this complete input set and fails rather than render a pairing whose evidence moved.
        # The two extractors' own pins are re-checked separately, at load, per source — this
        # guards the layer above them: the artifact itself.
        "inputs": input_fingerprints(),
        "scope": ("Per-armament reference pairing inside the existing actor assignment. "
                  "No reference is re-scored and no balance number is written."),
        "role_vocabulary": list(ar.ROLES),
        "stats": dict(sorted(stats.items())),
        # ⚠ A TOKEN NOBODY CLASSIFIED IS A GAP IN THE VOCABULARY, NOT A NEUTRAL FACT. It is
        # failed closed so the weapon abstains, and reported here so the next reader can see that
        # it happened and add the token deliberately.
        "unknown_targets": dict(sorted(unknown_tokens.items())),
        "uncovered_armaments": dict(sorted(uncovered.items())),
        "no_structured_reference": sorted(no_structured),
        "actors": actors,
    }


def _rng(view):
    """Always the WDist figure, so no reader ever compares a cell count to a WDist.

    A cell-unit source is marked with `c` so the conversion stays visible rather than looking
    like a measurement — see `armament_roles.WDIST_PER_CELL`.
    """
    if view["range_wdist"] is None:
        return "-"
    return "%d%s" % (round(view["range_wdist"]), "c" if view["range_unit"] == "cells" else "")


def print_actor(doc, actor):
    entry = doc["actors"].get(actor)
    if entry is None:
        print(f"{actor}: not in the assignment, or it carries no priced armament")
        return
    print(f"== {actor}   roles: {', '.join(role or 'unknown / unproven' for role in entry['roles'])}")
    for arm in entry["armaments"]:
        flag = "" if arm["baseline"] else "  (upgrade/alternative)"
        print("   %-8s %-44s range %-7s dmg/cycle %-9s rate %s%s"
              % (arm["role"], arm["weapon"], _rng(arm), arm["damage_per_cycle"],
                 round(arm["rate"], 3) if arm["rate"] else None, flag))
    for source, info in entry["sources"].items():
        if "pairs" not in info:
            print(f"   -- {source}: {info['status']}")
            continue
        print(f"   -- {source}  ->  {info['peer']} ({info['peer_name']})")
        for pair in info["pairs"]:
            mark = "=" if pair["exact"] else "~"
            print("      %s %-8s %-34s range %-7s  <->  %-26s range %s"
                  % (mark, pair["role"], pair["cameo"]["weapon"], _rng(pair["cameo"]),
                     pair["peer"]["weapon"], _rng(pair["peer"])))
        for name in info["cameo_unpaired"]:
            print(f"      ! {name}: no armament in this source covers that role")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--actor", help="print one actor's pairing in full")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    doc = build()
    if args.actor:
        print_actor(doc, args.actor)
    else:
        for key, value in doc["stats"].items():
            print(f"{key:40s} {value}")
        if doc["unknown_targets"]:
            print("unknown target tokens:", doc["unknown_targets"])
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
