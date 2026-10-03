#!/usr/bin/env python3
"""gen_rename_maps.py — §9.1 naming-compliance report + rename map generation.

Grammar (RA1-Soviet baseline, see MASTER_REPORT §9.1):
  unit/building id :=  [game_]faction_name[_variant]      (no type words)
  tech item id     :=  [game_]faction_(upgrade|promotion|doctrine)_name
  sequence assets  :=  filenames stem = owning actor id; icons end _icon

For every real faction: checks each faction-exclusive actor id against the
grammar and writes a machine-readable proposal to
tools/rename/rename_map_<faction>.yaml with two sections:
  actors:  old_id: new_id
  files:   old_filename: new_filename       (sequence Filename entries)
DOES NOT apply anything — apply.py (§9.6) consumes these maps later.

Stdout: per-faction compliance percentages + collision warnings + asset
filename compliance (including the _icon suffix rule).
"""

from __future__ import annotations

import pathlib
import re
import sys
from collections import Counter, defaultdict

from cameo_model import Model, slugify
from report import h1, h2, table

# internal faction id -> (game prefix or "", faction slug)  per §9.1/§9.2.
# Game prefix ONLY where the faction name actually collides across games.
# ⛔ THE GAME PREFIX GOES IN THE `game` SLOT **OR** IN THE SLUG — NEVER BOTH.
# `want_prefix` below joins them: ("ra1", "ra1_soviets") produced `ra1_ra1_soviets_`,
# which NOTHING can match, so all eight factions whose slug already carried their game
# prefix reported **0% compliant** and this generator proposed doubling every id
# (`ra1_soviets_btr80` -> `ra1_ra1_soviets_btr80`) and QUADRUPLING sub-sprites
# (`ra1_soviets_btr80_new_btr.shp` ->
#  `ra1_ra1_soviets_btr80_ra1_soviets_btr80_new_btr.shp`).
# That fake 0% was read as a 526-actor renaming backlog for months. Fixed 2026-09-06 by
# emptying the `game` slot wherever the slug already begins with it.
FACTION_SLUG = {
    "td_gdi": ("", "td_gdi"), "td_nod": ("", "td_nod"),
    "ts_gdi": ("", "ts_gdi"), "ts_nod": ("", "ts_nod"),
    "cabal": ("", "cabal"), "forgotten": ("", "forgotten"),
    "ra1_allies": ("", "ra1_allies"), "ra1_soviets": ("", "ra1_soviets"),
    "modjapan": ("", "japan"),
    "ra2_allies": ("", "ra2_allies"), "ra2_soviets": ("", "ra2_soviets"),
    "yuri": ("", "yuri"),
    "asianalliance": ("", "asianalliance"), "steelconsortium": ("", "steelconsortium"),
    "latinsyndicate": ("", "latinsyndicate"), "naxis": ("", "naxis"),
    "schwarzermond": ("", "schwarzermond"), "futuretech": ("", "futuretech"),
    "tkm": ("", "tkm"),
    "atreides": ("", "atreides"), "harkonnen": ("", "harkonnen"),
    "ordos": ("", "ordos"), "ixian": ("", "ixian"),
    "terran": ("", "terran"), "zerg": ("", "zerg"), "protoss": ("", "protoss"),
    "human2": ("", "wc2_humans"), "orc2": ("", "wc2_orcs"),
    "plymouthl": ("", "plymouth"), "edenl": ("", "eden"),
}
# slug -> the English adjective(s) a display name repeats the faction with, longest
# first.  Kept in step with REDUNDANT_WORD in tools/audit/audit_naming_damage.py,
# which counts the ids that already carry the duplication.
FACTION_ADJECTIVE = {
    "ra1_soviets": ("soviet",), "ra1_allies": ("allied", "allies"),
    "ra2_soviets": ("soviet",), "ra2_allies": ("allied", "allies"),
    "td_gdi": ("gdi",), "td_nod": ("nod",),
    "ts_gdi": ("gdi",), "ts_nod": ("nod",),
    "wc2_humans": ("human",), "wc2_orcs": ("orc",),
    "japan": ("japanese", "japan"), "naxis": ("naxis",), "yuri": ("yuri",),
    "cabal": ("cabal",), "atreides": ("atreides",), "harkonnen": ("harkonnen",),
    "ordos": ("ordos",), "ixian": ("ixian",), "terran": ("terran",),
    "zerg": ("zerg",), "protoss": ("protoss",),
    "asianalliance": ("asian",), "latinsyndicate": ("latin",),
    "steelconsortium": ("steel",), "futuretech": ("future",),
    "schwarzermond": ("schwarzer",), "forgotten": ("forgotten",),
    "plymouth": ("plymouth",), "eden": ("eden",),
}
VALID_ID = re.compile(r"^[a-z0-9_]+$")
# set from --files in main(); the files: half of every map is opt-in (see main).
WRITE_FILES = False
# A fluent KEY leaking out of Tooltip/Name.  Both separators occur in this tree
# (`actor-stats` and `actor_dog.name`), and the trailing `.name` is part of the key.
FLUENT_KEY = re.compile(r"^(actor|meta)[-_](.+?)(?:\.(?:name|description))?$", re.I)


def tech_marker(m: Model, lname: str) -> str | None:
    """'upgrade' | 'promotion' | 'doctrine' for tech items, else None."""
    res = m.rs.resolve(lname)
    if res is None:
        return None
    b = res.child("Buildable")
    queue = (b.get("Queue") or "").lower() if b else ""
    if "promotion" in queue:
        return "promotion"
    if "upgrade" in queue or "research" in queue:
        node = m.rs.actor(lname)
        for _, target in m.rs.inherits_of(node):
            if "doctrine" in target.lower():
                return "doctrine"
        return "upgrade"
    return None


def proposed_id(m: Model, faction: str, lname: str) -> str:
    # ⚠ `faction` must be a Model.real_factions() `.internal` id ("ra1_soviets"),
    # NOT the result of Model.owner_of(), which returns a PACK PATH
    # ("redalert/soviets").  Feeding a pack path here misses FACTION_SLUG entirely
    # and the fallback slugifies it into `redalert_soviets_*`, proposing to rename
    # every already-compliant `ra1_soviets_*` actor.  Fail loudly instead.
    if "/" in faction:
        raise AssertionError(
            f"proposed_id got a pack path {faction!r}; pass the faction's "
            "`.internal` id (Model.real_factions()), not Model.owner_of().")
    game, slug = FACTION_SLUG.get(faction, ("", slugify(faction)))
    marker = tech_marker(m, lname)
    disp = m.display_name(lname)
    # ⛔ Tooltip/Name is a FLUENT KEY, not English — and the keys use BOTH separators
    # (`actor-stats`, `actor_dog.name`).  A guard that tested only `actor-` let
    # `actor_dog.name` through slugify() and minted the actor id
    # `ra1_soviets_actordogname`, which then propagated into 4 sprite filenames,
    # ai.yaml GuerrillaTypes, an InitialUnits list and a `Targetable@` suffix in an
    # unrelated D2k pack.  Match BOTH separators, and strip the `.name` tail.
    key = FLUENT_KEY.match(disp or "")
    if key:
        name = slugify(key.group(2))
    elif disp:
        name = slugify(disp)
    else:
        name = slugify(lname.replace(".", "_"))
    if lname.endswith(".husk") or lname.endswith("husk"):
        if not name.endswith("husk"):
            name += "_husk"
    # display names often repeat the faction ("CABAL Core") — dedupe
    if name.startswith(slug + "_"):
        name = name[len(slug) + 1:]
    # ⛔ …and they repeat it as an ADJECTIVE far more often than as the slug:
    # "Soviet Airfield" under slug `ra1_soviets` gives `ra1_soviets_sovietairfield`,
    # "Japanese Barracks" under `japan` gives `japan_japanesebarracks`.  The slug
    # already carries the faction; saying it twice is the same defect as the doubled
    # game prefix, just spelled in English.  Strip it, but never down to nothing —
    # an actor genuinely called "Soviet" keeps its name.
    for adj in FACTION_ADJECTIVE.get(slug, ()):
        head = adj + "_"
        if name.startswith(head) and len(name) > len(head):
            name = name[len(head):]
            break
        if name == adj:
            break
    # RA1 baseline: the name is ONE group without underscores
    # (ra_heatraytank, ra_upgrade_nuclearshells), variants stay suffixed
    name = name.replace("_", "")
    parts = [p for p in (game, slug, marker, name) if p]
    out = "_".join(parts)
    return re.sub(r"_{2,}", "_", out)


def collect_filenames(m: Model) -> Counter:
    """How many sequence images reference each Filename (shared archives
    are exempt from per-actor naming)."""
    usage: Counter = Counter()
    for img, node in m.rs.sequences.items():
        seen: set[str] = set()
        for c in [node] + node.children:
            for sub in [c] + c.children:
                if sub.key == "Filename" and sub.value:
                    seen.add(sub.value.lower())
        for f in seen:
            usage[f] += 1
    return usage


def sequence_files_of(m: Model, image: str) -> dict[str, list[str]]:
    """sequence name -> [filenames] for one sequences image."""
    node = m.rs.sequence_image(image)
    out: dict[str, list[str]] = defaultdict(list)
    if node is None:
        return out
    for seq in node.children:
        for sub in [seq] + seq.children:
            if sub.key == "Filename" and sub.value:
                out[seq.key].append(sub.value)
    return out


def main() -> int:
    m = Model()
    # ⚠ This OVERWRITES tools/rename/rename_map_<faction>.yaml for every faction it
    # has a proposal for, and several agents keep hand-corrected maps there.  Pass
    # `--out DIR` to write somewhere else before you trust a regenerated proposal.
    global WRITE_FILES
    WRITE_FILES = "--files" in sys.argv
    out_dir = m.root / "tools/rename"
    if "--out" in sys.argv:
        out_dir = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])
    out_dir.mkdir(parents=True, exist_ok=True)
    file_usage = collect_filenames(m)

    print(h1("gen_rename_maps — §9.1 naming compliance (RA1-Soviet baseline)"))
    rows, icon_rows = [], []
    factions = sorted(f.internal for f in m.real_factions())
    rosters = {fac: m.buildable_roster(fac) for fac in factions}

    # ⛔ Which FACTIONS does each sprite file serve?  The old guard exempted a file
    # only when more than three sequence images used it, so a sprite shared by
    # exactly two factions was captured by whichever faction was renamed first:
    #   ra1_allies_alliedorerefinery_raproc.shp
    #   -> ra1_soviets_sovietorerefinery_ra1_allies_alliedorerefinery_raproc.shp
    # A shared asset belongs to NEITHER faction's namespace and must never be
    # renamed by a per-faction pass.  audit_naming_damage.py N2 counts the damage.
    file_owners: dict[str, set[str]] = defaultdict(set)
    for fac2, roster in rosters.items():
        for lname2 in roster:
            res2 = m.rs.resolve(lname2)
            img2 = ((res2.get("RenderSprites", "Image") if res2 else None)
                    or lname2).lower()
            for files2 in sequence_files_of(m, img2).values():
                for f2 in files2:
                    file_owners[f2.lower()].add(fac2)

    for fac in factions:
        game, slug = FACTION_SLUG.get(fac, ("", slugify(fac)))
        if game and slug.startswith(game + "_"):
            raise AssertionError(
                f"FACTION_SLUG[{fac!r}] doubles its game prefix: "
                f"game={game!r} slug={slug!r} would want {game}_{slug}_. "
                "Put the game prefix in the `game` slot OR in the slug, never both.")
        want_prefix = "_".join(p for p in (game, slug) if p) + "_"
        others: set[str] = set()
        for g, r in rosters.items():
            if g != fac:
                others |= r
        owned = sorted(rosters[fac] - others)

        compliant, renames = [], {}
        collisions: dict[str, list[str]] = defaultdict(list)
        file_renames: dict[str, str] = {}
        unrepairable: list[str] = []
        icon_total = icon_ok = 0

        for lname in owned:
            new = None
            if lname.startswith(want_prefix) and VALID_ID.fullmatch(lname):
                compliant.append(lname)
            else:
                new = proposed_id(m, fac, lname)
                n, i = new, 2
                while n in collisions and lname not in collisions[n]:
                    n = f"{new}_{i}"
                    i += 1
                renames[lname] = n
                collisions[n].append(lname)

            # asset filename checks against the (new or current) id
            target_id = renames.get(lname, lname)
            res = m.rs.resolve(lname)
            image = ((res.get("RenderSprites", "Image") if res else None)
                     or lname).lower()
            for seq, files in sequence_files_of(m, image).items():
                for f in files:
                    lf = f.lower()
                    if file_usage[lf] > 3:
                        continue  # shared archive (DATA.R16 style)
                    if len(file_owners.get(lf, ())) > 1:
                        continue  # shared across factions — belongs to no namespace
                    if "|" in lf:
                        # ⛔ `cabal_icons|cabal_cyborgfactory_icon.png` names a MEMBER
                        # of a mounted package, not a loose file.  Treating it as a
                        # filename glued the id in front of the whole string —
                        # `cabal_cyborgfactory_cabal_icons|cabal_cyborgfactory_icon.png`
                        # — which no package can resolve.  677 refs are qualified.
                        continue
                    if any(lf.startswith(sib + "_") or lf.startswith(sib + ".")
                           for sib in owned if sib != lname):
                        # Named after a SIBLING actor of the same faction — a
                        # deliberate share (`ra1_soviets_nuclearyak.shp` used by the
                        # yakscoutplane image).  Renaming it into THIS actor's
                        # namespace was proposing to steal a file that already has a
                        # correct, compliant owner.
                        continue
                    stem = pathlib.PurePosixPath(lf).stem
                    ext = pathlib.PurePosixPath(lf).suffix
                    if seq.lower() == "icon":
                        icon_total += 1
                        if stem.endswith("_icon"):
                            icon_ok += 1
                        want = f"{target_id}_icon{ext}"
                        if stem != f"{target_id}_icon":
                            file_renames[f] = want
                    elif not stem.startswith(target_id):
                        # ⛔ REPLACE the old id, never PREPEND the new one in front of
                        # it.  `f"{target_id}_{stem}"` on a stem that already carries
                        # the old id produces `newid_oldid_sub`, e.g.
                        #   ra1_soviets_btr80_new_btr.shp
                        #   -> ra1_soviets_btr80_ra1_soviets_btr80_new_btr.shp
                        # 25 files in this tree still carry that shape (2026-09-06);
                        # audit_naming_damage.py N1 counts them.
                        if stem == lname:
                            new_stem = target_id
                        elif stem.startswith(lname + "_"):
                            new_stem = target_id + stem[len(lname):]
                        elif stem.startswith(slug + "_"):
                            # The stem already carries THIS faction's slug, so it is
                            # an OLD id spelled differently from `lname` (file
                            # `atreides_airdrone.png` for actor `up_airdrone.atreides`
                            # renaming to `atreides_promotion_airdrone`).  Prepending
                            # would mint `atreides_promotion_airdrone_atreides_airdrone`.
                            # Where the old id ends is not derivable — flag for review.
                            unrepairable.append(f)
                            continue
                        else:
                            new_stem = f"{target_id}_{stem}"
                        # A stem that is ALREADY damaged (newid_oldid_sub from an
                        # earlier bad run) cannot be repaired by a prefix rule —
                        # prefix replacement just shifts the residue along.  Leave it
                        # to the dedicated repair pass and say so.
                        if re.search(r"(^|_)([a-z0-9]+_[a-z0-9_]{8,})_.*\2", new_stem):
                            unrepairable.append(f)
                            continue
                        file_renames[f] = f"{new_stem}{ext}"

        dupes = {k: v for k, v in collisions.items() if len(v) > 1}
        pct = f"{100 * len(compliant) // len(owned)}%" if owned else "—"
        ipct = f"{100 * icon_ok // icon_total}%" if icon_total else "—"
        rows.append([fac, f"{len(compliant)}/{len(owned)}", pct,
                     str(len(dupes)), str(len(file_renames)),
                     str(len(unrepairable))])
        icon_rows.append([fac, f"{icon_ok}/{icon_total}", ipct])

        # ⛔ The `files:` half is OPT-IN.  Six separate defects have been found in it
        # (doubled stems, cross-faction capture, sibling-share theft, package-
        # qualified refs, level-N icons proposed onto level-N-1 names, and stems that
        # are already damaged).  The `actors:` half is trustworthy; the file half must
        # be eyeballed before it is applied, so it is written only under --files.
        if not WRITE_FILES:
            file_renames = {}

        if renames or file_renames:
            path = out_dir / f"rename_map_{fac}.yaml"
            lines = [f"# rename_map_{fac}.yaml — generated by gen_rename_maps.py",
                     "# §9.1 grammar (RA1-Soviet baseline); NOT applied — see §9.6",
                     "actors:"]
            for old, new in sorted(renames.items()):
                lines.append(f"\t{old}: {new}")
            lines.append("files:")
            for old, new in sorted(file_renames.items()):
                lines.append(f"\t{old}: {new}")
            path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(h2("Actor-id compliance per faction (faction-exclusive buildables)"))
    print(table(["faction", "compliant", "%", "proposal collisions",
                 "asset files to rename", "unrepairable stems"], rows))
    print(h2("Icon filename compliance (_icon suffix rule)"))
    print(table(["faction", "icons compliant", "%"], icon_rows))
    print("\n_Ownership is data-driven: an actor counts for a faction only if "
          "no other faction's prerequisite closure can build it. Sequence "
          "filenames referenced by more than 3 images are treated as shared "
          "archives and exempted. Rename proposals written to "
          "tools/rename/rename_map_<faction>.yaml (actors: + files: sections); "
          "collisions need manual `_variant` suffixes before applying._\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
