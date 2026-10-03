#!/usr/bin/env python3
"""Every source's group -> Cameo family review, loaded as one keyed store.

WHY A STORE AND NOT A FILE. The review began as a single hand-authored file because there was a
single reviewed source (Combined Arms). There are twenty sources, and the lane handoff had been
carrying an open question — *"a second source needs either a second file or a `source:` key per
block, decide that before starting, not halfway"* — since before the first one landed. This is
that decision, made the way the file itself already pointed: every assignment file ALREADY carries
a `source:` field, so the key exists and only the loader was missing.

Layout: `docs/reference/warhead_family_assignment*.yaml`, one file per source, keyed by the
`source:` inside it rather than by its filename. The filename is a convenience for humans; the
field is the identity, because a file can be renamed and a review cannot.

⚠ THE FILES STAY HAND-AUTHORED. R21 forbids rebuilding them from a name-matching pass, and R46
measured why: four independent matchers score ~20% against a 75% ceiling, and name evidence is
right 40% of the time on the 42% of weapons it can guess at all. This module LOADS reviews; it
must never generate one.

⚠ A PER-WEAPON OVERRIDE BEATS ITS GROUP. That is what makes a review survive re-clustering, and
`resolve()` is the one place that precedence is implemented — every consumer should call it rather
than reimplementing the `overrides` lookup, which is how `retau_assignment.py` came to manufacture
a straddle by letting an overridden weapon vote for its old group (R41).

    python tools/reference/assignment_store.py            # what is reviewed, and how far
    python tools/reference/assignment_store.py --source mental_omega
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
REF = ROOT / "docs" / "reference"
PATTERN = "warhead_family_assignment*.yaml"
GROUPS = REF / "warhead_groups.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Families that are a DECISION NOT TO ASSIGN rather than a family. They are spelled in
# parentheses so they can never collide with a real `^Warhead_<Family>` name.
NON_FAMILY_PREFIX = "("

# Sources that will never get an assignment file, and why. Counting their weapons as
# outstanding work overstates the job by roughly 1,600 — most of it Cameo answering a question
# about itself.
NEEDS_NO_REVIEW = {
    "cameo": "a `^Warhead_<Family>_<Level>` template IS its family (R37)",
    "cameo_resolved": "Cameo's own weapons state their family in the inherit chain (R37)",
    "d2k_mod": "a transcribed table with no actors — it votes on the armour ladder only (R38)",
}


def paths() -> list[pathlib.Path]:
    """Every assignment file on disk, in a stable order."""
    return sorted(REF.glob(PATTERN))


def load() -> dict:
    """{source: parsed document}. Raises on a duplicate or a missing `source:`."""
    out: dict = {}
    for path in paths():
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        sid = doc.get("source")
        if not sid:
            raise SystemExit(f"{path.name} has no `source:` field — it cannot be keyed")
        if sid in out:
            raise SystemExit(f"two files both claim source {sid!r}: "
                             f"{out[sid]['_path'].name} and {path.name}")
        doc["_path"] = path
        out[sid] = doc
    return out


def load_source(sid: str) -> dict | None:
    """One source's document, or None if it has not been reviewed yet."""
    return load().get(sid)


def resolve(sid: str, groups: list | None = None) -> dict:
    """{weapon: family} for one source, with per-weapon overrides beating their group.

    Returns {} for an unreviewed source rather than raising, so a caller can sweep all twenty.
    """
    doc = load_source(sid)
    if not doc:
        return {}
    if groups is None:
        groups = json.load(GROUPS.open(encoding="utf-8")).get(sid, {}).get("groups", [])
    overrides = doc.get("overrides") or {}
    assigned = doc.get("groups") or {}
    out = {}
    for group in groups:
        family = (assigned.get(group["name"]) or {}).get("family", "?")
        for weapon in group["weapons"]:
            out[weapon] = (overrides[weapon]["family"] if weapon in overrides else family)
    return out


def stale_rows() -> dict:
    """{source: [group names whose reviewed row no longer holds the weapons it was written for]}.

    ⛔ R54 - THE ONE CHECK THAT MATTERS, AND IT WAS MISSING. Every assignment row records the
    WEAPONS it was written about, precisely so it can be audited later — and nothing audited it.
    Dropping `CorrupterSpew` out of Combined Arms' `Bullet_Veh_7` into its own Toxin group
    CASCADED the numbered suffixes, so `Bullet_Veh_7`, `_8` and `_9` each silently inherited the
    next group's weapon. Three maintainer-reviewed decisions were then attached to weapons nobody
    had looked at, and `coverage()` reported **one** open row, because a row is only "open" when
    its NAME disappears. A name surviving proves nothing; the weapon list is the identity.

    A non-empty result means the grouping moved under a review and
    `retau_assignment.py --source <sid> --write` must be run before anything trusts `resolve()`.
    """
    data = json.load(GROUPS.open(encoding="utf-8"))
    out: dict = {}
    for sid, doc in load().items():
        have = {g["name"]: set(g["weapons"]) for g in data.get(sid, {}).get("groups", [])}
        bad = [name for name, row in (doc.get("groups") or {}).items()
               if name not in have or set(row.get("weapons") or []) != have[name]]
        if bad:
            out[sid] = sorted(bad)
    return out


def coverage() -> list:
    """[(source, groups, decided, open)] over every source in the groups file."""
    data = json.load(GROUPS.open(encoding="utf-8"))
    store = load()
    rows = []
    for sid in sorted(data):
        groups = data[sid]["groups"]
        # ⚠ `open` is counted against the source's OWN weapons, not against what resolve()
        # returned. An unreviewed source resolves to {}, and reporting that as "0 open" said
        # the work was finished everywhere nobody had started — the opposite of the truth.
        weapons = sum(len(g["weapons"]) for g in groups)
        families = resolve(sid, groups)
        decided = sum(1 for f in families.values()
                      if f and f != "?" and not f.startswith(NON_FAMILY_PREFIX))
        parked = sum(1 for f in families.values()
                     if f and f.startswith(NON_FAMILY_PREFIX))
        rows.append((sid, len(groups), decided, parked,
                     0 if sid in NEEDS_NO_REVIEW else weapons - decided - parked,
                     sid in store))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", help="show one source's decided families instead of the summary")
    args = ap.parse_args()

    if args.source:
        fams = resolve(args.source)
        if not fams:
            print(f"{args.source}: no assignment file "
                  f"(looked for `source: {args.source}` in {PATTERN})")
            return 0
        per = collections.Counter(fams.values())
        print(f"## {args.source} — {len(fams)} weapons over {len(per)} families\n")
        for family, n in per.most_common():
            print(f"  {family:<28}{n:>5}")
        return 0

    print(f"## Assignment coverage — {len(paths())} file(s) in {REF.name}/\n")
    print(f"  {'source':<24}{'groups':>7}{'decided':>9}{'parked':>8}{'open':>7}  file")
    tg = td = tp = to = 0
    for sid, groups, decided, parked, undecided, has_file in coverage():
        tg += groups; td += decided; tp += parked; to += undecided
        skip = sid in NEEDS_NO_REVIEW
        mark = "n/a" if skip else ("yes" if has_file else "-")
        shown = "-" if skip else str(undecided)
        print(f"  {sid:<24}{groups:>7}{decided:>9}{parked:>8}{shown:>7}  {mark}")
    print(f"\n  {'TOTAL':<24}{tg:>7}{td:>9}{tp:>8}{to:>7}")
    print("\n`decided` counts WEAPONS with a real family; `parked` are the deliberate "
          "`(drop: ...)` / `(park: ...)` calls; `open` is everything still unreviewed.")
    for sid, why in sorted(NEEDS_NO_REVIEW.items()):
        print(f"  `{sid}` needs no review — {why}")

    stale = stale_rows()
    if stale:
        print("\n⛔ STALE REVIEWS — the grouping moved under these rows and `resolve()` is "
              "returning decisions for weapons they were not written about:")
        for sid, names in sorted(stale.items()):
            print(f"  {sid}: {len(names)} row(s) — {', '.join(names[:6])}"
                  f"{' …' if len(names) > 6 else ''}")
            print(f"     fix: python tools/reference/retau_assignment.py --old <snapshot.json> "
                  f"--source {sid} --write")
        return 1
    print("\n✓ every reviewed row still holds exactly the weapons it was written about.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
