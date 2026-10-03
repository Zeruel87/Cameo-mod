#!/usr/bin/env python3
"""Carry a hand-authored family assignment across a change of clustering threshold.

WHY THIS CAN WORK AT ALL. `warhead_family_assignment.yaml` is keyed by GROUP NAME, and group
names are an artefact of one compression run — the file says so in its own header, and the lane
handoff lists "group names shift on every re-run" among the traps that have already cost a
session. Re-applying such a file by name after moving `DEFAULT_TAU` would silently attach
reviewed decisions to groups that are not the ones reviewed.

But the decisions themselves are not about names. They are about WEAPONS, and the clustering is
COMPLETE-LINKAGE AGGLOMERATIVE, which means it NESTS: lowering tau can only SUBDIVIDE a group,
never reshuffle its members into different groups. So every new group falls into one of four
cases against the old grouping, and only the last two need a human:

  carried          all its weapons came from ONE old group   -> inherit that family verbatim
  split            likewise, but the old group produced      -> inherit, and FLAG: the old review
                   several new groups                           saw these weapons mixed with others
  all_overridden   every weapon is individually assigned     -> the group label is moot
  straddle         its weapons came from old groups that     -> `?`, needs a ruling
                   disagree about the family

Measured on the 0.50 -> 0.20 move for Combined Arms (118 -> 182 groups):

    carried  74   split  72   all_overridden  36   straddle  0   unreviewed  0

so all 182 new groups inherit a reviewed decision and NOTHING was sent back for re-review. The 82
per-weapon `overrides:` carry verbatim, because they were always keyed by weapon name — which is
exactly why R21 asked for them that way.

⚠ AN OVERRIDDEN WEAPON DOES NOT VOTE. A per-weapon override BEATS its group, so a weapon that has
one has already been decided individually and is not in any group's jurisdiction. Counting it as
a parent MANUFACTURES straddles: the first run of this tool reported `BulletHE_Veh_5` as a
CannonHE / `(resolved per weapon)` conflict, and it is nothing of the kind — three of its four
weapons come from one CannonHE group and the fourth (`HallucinationGrenade`) is separately
assigned to Concussion. Honouring override precedence took the straddle count from 1 to 0.

⚠ THIS SUPERSEDES AN EARLIER EXPLORATORY COUNT of "76 unchanged, 41 split, 4 straddle". That
script counted PARENT-GROUP MULTIPLICITY — how many new groups drew members from more than one
old group — which is not the same question. Only 4 new groups have several parents, and 3 of them
have parents that AGREE on the family (`Radiation_Veh`, `Laser_Inf`, `BulletHE_Veh_7`), so there
was never a decision to make. What matters is whether the DECISIONS conflict, not whether the
boundaries moved.

⚠ NESTING IS AN ASSUMPTION THIS TOOL CHECKS, NOT ONE IT TRUSTS. A new group whose weapons span
old groups with different families is reported as a straddle rather than guessed at, and
`--verify` prints every one in full. A large straddle count means the two runs were not produced
by the same compressor and the migration is not valid.

    python tools/reference/retau_assignment.py --old <snapshot.json>            # dry run
    python tools/reference/retau_assignment.py --old <snapshot.json> --write    # rewrite the yaml
    python tools/reference/retau_assignment.py --old <snapshot.json> --verify   # straddles in full
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import yaml

import assignment_store as store

ROOT = pathlib.Path(__file__).resolve().parents[2]

GROUPS = ROOT / "docs" / "reference" / "warhead_groups.json"
# ⚠ R54 - THERE IS NO SINGLE ASSIGNMENT DOCUMENT ANY MORE. This was a hardcoded path to Combined
# Arms' file from when CA was the only reviewed source, and `--source` switched only the GROUPS
# lookup. So `--source mental_omega` compared MO's new groups against CA's REVIEW and reported a
# confident migration of the wrong document — it did not fail, which is what made it dangerous.
# The document now comes from `assignment_store`, keyed by the same `source:` field everything
# else keys on. Same defect class as `family_matrix.load_assignment`, fixed the same way.


def doc_for(source: str) -> pathlib.Path:
    """The assignment file that CLAIMS `source`, not a filename guessed from it."""
    doc = store.load_source(source)
    if doc is None:
        raise SystemExit(f"no assignment file declares source {source!r} — "
                         f"reviewed sources are {', '.join(sorted(store.load()))}")
    return doc["_path"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_groups(path: pathlib.Path, source: str) -> dict:
    data = json.load(path.open(encoding="utf-8"))
    if source not in data:
        raise SystemExit(f"{path.name} has no source {source!r} "
                         f"(it has {', '.join(sorted(data))})")
    return data[source]


def weapon_owner(entry: dict) -> dict:
    """{weapon: group name} for one source's grouping."""
    out = {}
    for group in entry["groups"]:
        for weapon in group["weapons"]:
            out[weapon] = group["name"]
    return out


def migrate(old_entry: dict, new_entry: dict, doc: dict) -> dict:
    """Decide a family for every new group. Returns the full migration record."""
    old_owner = weapon_owner(old_entry)
    assigned = doc.get("groups") or {}
    # ⚠ A per-weapon override BEATS its group (R21), so an overridden weapon does not vote for
    # where it used to sit — it has already been decided individually and carries verbatim.
    # Counting its old group as a parent manufactures straddles: `BulletHE_Veh_5` looked like a
    # CannonHE/`(resolved per weapon)` conflict and is nothing of the kind, because the single
    # weapon pulling it the other way (`HallucinationGrenade` -> Concussion) is not in the group's
    # jurisdiction at all.
    overridden = set(doc.get("overrides") or {})

    rows, stats = {}, collections.Counter()
    # How many new groups each old group produced — the split detector.
    produced: collections.Counter = collections.Counter()
    def voters(group: dict) -> list:
        return [w for w in group["weapons"] if w not in overridden]

    for group in new_entry["groups"]:
        parents = {old_owner.get(w) for w in voters(group)}
        parents.discard(None)
        if len(parents) == 1:
            produced[next(iter(parents))] += 1

    for group in new_entry["groups"]:
        name = group["name"]
        members = voters(group)
        parents = collections.Counter(old_owner[w] for w in members if w in old_owner)
        known = {p for p in parents if p in assigned}
        fams = {assigned[p]["family"] for p in known}

        # ⚠ CARRY THE WHOLE MEASURED PAYLOAD. `propagate_families.py` reads `weapons` as the
        # NAME LIST, and `family_matrix.py` reads `profile`/`uses`/`factor`. An earlier draft of
        # this tool wrote `weapons` as a count and dropped the rest, which left a file that looked
        # fine and crashed its first consumer with `'int' object is not iterable`.
        row = {"band": group.get("band"), "delivery": group.get("delivery"),
               "element": group.get("element"), "uses": group.get("uses"),
               "members": group.get("members"), "factor": group.get("factor"),
               "flat": group.get("flat"), "examples": group.get("examples"),
               "profile": group.get("profile"), "weapons": group["weapons"]}
        if len(members) < len(group["weapons"]):
            row["overridden_members"] = len(group["weapons"]) - len(members)

        if not members:
            # Every weapon in this group is individually assigned; the group label is moot.
            row.update(family="(resolved per weapon)", status="confirmed", carry="all_overridden")
            stats["all_overridden"] += 1
            rows[name] = row
            continue

        if not known:
            # Weapons the old review never reached (new source, or all-new members).
            row.update(family="?", status="proposed", carry="unreviewed")
            stats["unreviewed"] += 1
        elif len(fams) == 1:
            parent = next(iter(known))
            row.update(family=next(iter(fams)),
                       status=assigned[parent].get("status", "proposed"),
                       carry="split" if produced[parent] > 1 else "carried",
                       carried_from=parent)
            if produced[parent] > 1:
                row["status"] = "proposed"
                row["review_note"] = (
                    f"carried from `{parent}`, which this threshold splits into "
                    f"{produced[parent]} groups — the old review saw these weapons mixed in "
                    f"with the others, so the label is inherited, not confirmed")
                stats["split"] += 1
            else:
                stats["carried"] += 1
        else:
            row.update(family="?", status="proposed", carry="straddle",
                       carried_from=sorted(known),
                       review_note=("its weapons come from old groups that disagree: "
                                    + ", ".join(sorted(fams))))
            stats["straddle"] += 1
        rows[name] = row

    return {"rows": rows, "stats": stats, "produced": produced}


def write_doc(new_entry: dict, result: dict, doc: dict, doc_path: pathlib.Path) -> str:
    """Rebuild the yaml, preserving the header comments and the per-weapon overrides."""
    header = []
    for line in doc_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("source:"):
            break
        header.append(line)

    lead = ("family", "status", "carry", "carried_from", "review_note")
    ordered = {name: dict(sorted(row.items(),
                                 key=lambda kv: (lead.index(kv[0]) if kv[0] in lead else len(lead),)))
               for name, row in result["rows"].items()}

    out = {"source": doc["source"],
           "tau": new_entry["tau"],
           "armors": new_entry["groups"][0]["armors"] if new_entry["groups"] else [],
           "totals": {"warheads": new_entry.get("rows"),
                      "groups": len(new_entry["groups"])},
           "groups": ordered,
           "overrides": doc.get("overrides") or {}}

    body = yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=100)
    return "\n".join(header) + "\n" + body


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", required=True, type=pathlib.Path,
                    help="a warhead_groups.json snapshot taken BEFORE the tau change")
    ap.add_argument("--source", required=True,
                    help="which source to migrate; its assignment file is found by that key")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true", help="print every straddle in full")
    args = ap.parse_args()

    source = args.source
    doc_path = doc_for(source)
    doc = yaml.safe_load(doc_path.read_text(encoding="utf-8"))

    old_entry = load_groups(args.old, source)
    new_entry = load_groups(GROUPS, source)
    # ⚠ R54 - THIS USED TO SAY "nothing to migrate" AND IT WAS WRONG. tau is not the only thing
    # that regroups: an ELEMENT VOCABULARY change does it too, and it is worse, because pulling
    # one weapon out of `Bullet_Veh_7` CASCADES the numbered suffixes — `Bullet_Veh_7/8/9` each
    # inherited the next group's weapons and three reviewed Combined Arms decisions silently
    # attached to weapons nobody had reviewed. The loader saw only ONE open row out of four wrong
    # ones, because the NAMES all still existed. Same tau is not the same grouping.
    if old_entry["tau"] == new_entry["tau"]:
        print(f"note: both groupings are at tau {old_entry['tau']}, so this is a re-key after a "
              f"vocabulary or corpus change rather than a tau move — still required, because "
              f"group names renumber.")
    result = migrate(old_entry, new_entry, doc)
    stats = result["stats"]

    print(f"## {source}: tau {old_entry['tau']} -> {new_entry['tau']}\n")
    print(f"  old groups        {len(old_entry['groups']):>5}")
    print(f"  new groups        {len(new_entry['groups']):>5}")
    print(f"  assigned before   {len(doc.get('groups') or {}):>5}")
    print(f"  per-weapon overrides carried verbatim   {len(doc.get('overrides') or {}):>5}\n")
    for key in ("carried", "split", "straddle", "all_overridden", "unreviewed"):
        print(f"  {key:<12} {stats[key]:>5}")
    reviewed = stats["carried"] + stats["split"] + stats["all_overridden"]
    total = sum(stats.values())
    print(f"\n  {reviewed} of {total} new groups inherit a reviewed decision "
          f"({reviewed / total:.0%}); {stats['straddle'] + stats['unreviewed']} need a look.")

    if args.verify:
        print("\n### straddles — the only groups where nesting did not hold\n")
        for name, row in sorted(result["rows"].items()):
            if row["carry"] != "straddle":
                continue
            print(f"  {name}  ({row['uses']} uses, {row['weapons']} weapons)")
            print(f"      from: {', '.join(row['carried_from'])}")
            print(f"      {row['review_note']}")

    if args.write:
        backup = doc_path.with_suffix(".yaml.bak")
        shutil.copy2(doc_path, backup)
        doc_path.write_text(write_doc(new_entry, result, doc, doc_path), encoding="utf-8")
        print(f"\nwrote {doc_path.relative_to(ROOT)}  (previous version kept at {backup.name})")
    else:
        print("\n(dry run — pass --write to rewrite the assignment file)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
