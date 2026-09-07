#!/usr/bin/env python3
"""audit_naming_damage.py - the six naming pathologies a botched rename leaves behind.

Renaming is done by `gen_rename_maps.py` (proposes) + `tools/rename/safe_rename.py`
(applies).  When the PROPOSAL is wrong the apply step is faithful, every reference is
updated, the boot gate passes - and the tree is silently full of garbage names.  That
is exactly what happened on 2026-09-06: a doubled game prefix in FACTION_SLUG made
eight factions read 0% compliant for months, and the file-rename branch prepended the
NEW id to the OLD stem instead of replacing it.

This audit reads the RESULT, not the proposal, so it catches damage no matter which
tool or which agent produced it.  Every count is a LOWER-ONLY ratchet.

  N1 DOUBLED_ID          a filename carries a full actor id TWICE
                         (ra1_soviets_btr80_ra1_soviets_btr80_new_btr.shp)
  N2 CROSS_FACTION       a filename carries two DIFFERENT factions' actor ids
                         (ra1_soviets_sovietorerefinery_ra1_allies_alliedorerefinery_raproc.shp)
  N3 FLUENT_LEAK         a fluent KEY was slugified into an id or filename
                         (Tooltip/Name `actor_dog.name` -> ra1_soviets_actordogname)
  N4 REDUNDANT_WORD      the faction is named twice, once as slug once as adjective
                         (ra1_allies_alliedaagun, japan_japanesebarracks)
  N5 DOTTED_FACTION      an actor id whose DOT SUFFIX names a faction, putting the
                         faction where the grammar requires a variant.  DESIGN's dot
                         rule (2026-09-06): a dot marks a VARIANT of the base actor
                         (`camera.spysat`, `.husk`) and may NEVER carry a faction.
  N6 HYPHEN              DESIGN rule 9: underscore is the only separator.

Usage: python tools/audit/audit_naming_damage.py [--list N1,N4] [--faction ra1_soviets]
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from cameo_model import Model
from report import h1, h2, table

# --- ratchets - LOWER ONLY.  Set 2026-09-06 from this audit's own first run.
# Never raise one.  Never set one from a scratch measurement: on 2026-09-06 a
# throwaway scan said 602/237/30/72 where the real audit said 583/221/21/61.
N1_BASELINE = 25
N2_BASELINE = 16
N3_BASELINE = 5
N4_BASELINE = 345
N5_BASELINE = 109
N6_BASELINE = 1

# DESIGN.md "The dot rule" (maintainer ruling 2026-09-06): a dot marks a VARIANT of
# the base actor named before it, and is LEGAL - `.husk`, `.spysat`, `.emp`,
# `.infiltrated`, `.colorpicker`, `.rank_3`.  What is NOT legal is a dot carrying a
# FACTION: `ptnk.asian` puts in the suffix what the grammar requires as the prefix.
# So the test is not "which suffixes are sanctioned" but "does this suffix name a
# faction" - DOT_FACTION below is the whole of it.

# faction slug -> the human adjective(s) that must not be repeated after it
REDUNDANT_WORD = {
    "ra1_soviets": ("soviet",), "ra1_allies": ("allied", "allies"),
    "ra2_soviets": ("soviet",), "ra2_allies": ("allied", "allies"),
    "td_gdi": ("gdi",), "td_nod": ("nod",),
    "ts_gdi": ("gdi",), "ts_nod": ("nod",),
    "wc2_humans": ("human",), "wc2_orcs": ("orc",),
    "japan": ("japan", "japanese"), "naxis": ("naxis",), "yuri": ("yuri",),
    "cabal": ("cabal",), "atreides": ("atreides",), "harkonnen": ("harkonnen",),
    "ordos": ("ordos",), "ixian": ("ixian",), "terran": ("terran",),
    "zerg": ("zerg",), "protoss": ("protoss",),
    "asianalliance": ("asian",), "latinsyndicate": ("latin",),
    "steelconsortium": ("steel",), "futuretech": ("future",),
    "schwarzermond": ("schwarzer",), "forgotten": ("forgotten",),
    "plymouth": ("plymouth",), "eden": ("eden",),
}
# A dotted id carries its faction in the SUFFIX instead of the prefix
# (`ptnk.asian` -> `asianalliance_ptnk`).  Attribute those to the owning faction
# so the per-faction table is directly usable as a work assignment.
DOT_FACTION = {
    "asian": "asianalliance", "latin": "latinsyndicate", "steel": "steelconsortium",
    "ixian": "ixian", "atreides": "atreides", "ordos": "ordos",
    "corrino": "corrino", "harkonnen": "harkonnen", "futu": "futuretech",
    "nax": "naxis", "nax2": "naxis", "cabal": "cabal", "ra2": "ra2_allies",
    "ts": "ts_gdi", "d2k": "d2k",
}
FLUENT_LEAK = re.compile(r"(actor|meta)[a-z0-9]*name")
SPRITE_EXT = {".shp", ".png", ".tga", ".r8", ".r16", ".vxl", ".hva", ".dds"}


def self_test(id_re):
    """The N1/N2 detector must be able to SEE a doubled id.  It once could not.

    The first cut of this audit matched each id with a CONSUMING separator,
    `(?:^|_)<id>(?:_|$)`.  re.finditer resumed after the consumed `_`, so in
    `ra1_soviets_btr80_ra1_soviets_btr80_new_btr` the second occurrence could no
    longer match its required `(?:^|_)` prefix - and the doubled id this check
    exists to find was structurally invisible.  It reported N1 4 / N2 0 where the
    truth was 25 / 16, and an exact zero looked like a clean bill of health.
    Had that run set the baselines, N2 would have been ratcheted at 0: a check
    incapable of failing, with 16 real findings hidden behind a green PASS.

    The fix is the lookahead `(?=_|$)`, which consumes nothing.  This guard fails
    loudly if anyone rewrites the pattern back into a consuming form.
    """
    probe = "ra1_soviets_btr80_ra1_soviets_btr80_new_btr"
    n = len(id_re.findall(probe))
    if n < 2:
        raise AssertionError(
            f"id_re found {n} occurrence(s) in {probe!r}, expected 2 or more. "
            "The pattern must not CONSUME the trailing separator - use `(?=_|$)`, "
            "not `(?:_|$)`, or N1/N2 silently stop detecting doubled ids.")


def faction_of_id(actor_id, slugs):
    for s in slugs:                       # slugs are longest-first
        if actor_id.startswith(s + "_"):
            return s
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default="", help="comma-separated codes to list in full")
    ap.add_argument("--faction", default="", help="restrict listings to one faction")
    args = ap.parse_args()
    want = {c.strip().upper() for c in args.list.split(",") if c.strip()}

    m = Model()
    root = m.root
    slugs = sorted(REDUNDANT_WORD, key=len, reverse=True)
    actors = [a for a in m.rs.actors if not a.startswith("^")]
    # ids long enough to be recognisable inside a filename
    ids = sorted((a.lower() for a in actors if len(a) >= 8), key=len, reverse=True)
    # ONE alternation, longest-first, so the longest id wins at each position.
    # Scanning 28k files x 3200 ids separately takes minutes; this takes seconds.
    id_re = re.compile(r"(?:^|_)(" + "|".join(re.escape(i) for i in ids) + r")(?=_|$)")
    self_test(id_re)

    hits = collections.defaultdict(list)

    # -- actor ids -----------------------------------------------------------
    for a in actors:
        la = a.lower()
        fac = faction_of_id(la, slugs)
        if "-" in la:
            hits["N6"].append((fac or "?", a))
        if FLUENT_LEAK.search(la):
            hits["N3"].append((fac or "?", a))
        if "." in la:
            owner = DOT_FACTION.get(la.rsplit(".", 1)[1])
            if owner:            # the dot carries a FACTION - renaming debt
                hits["N5"].append((fac or owner, a))
        if fac:
            rest = la[len(fac) + 1:]
            if rest.startswith(REDUNDANT_WORD[fac]):
                hits["N4"].append((fac, a))

    # -- asset filenames -----------------------------------------------------
    for p in (root / "mods/cameo/bits").rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SPRITE_EXT:
            continue
        stem, rel = p.stem.lower(), p.relative_to(root).as_posix()
        found = [(mt.start(1), mt.group(1)) for mt in id_re.finditer(stem)]
        if len(found) >= 2:
            facs = {faction_of_id(i, slugs) for _, i in found} - {None}
            code = "N2" if len(facs) >= 2 else "N1"
            hits[code].append((sorted(facs)[0] if facs else "?", rel))
        fac0 = faction_of_id(stem, slugs)
        if FLUENT_LEAK.search(stem):
            hits["N3"].append((fac0 or "?", rel))
        if fac0 and stem[len(fac0) + 1:].startswith(REDUNDANT_WORD[fac0]):
            hits["N4"].append((fac0, rel))
        if "-" in p.name:
            hits["N6"].append((fac0 or "?", rel))

    print(h1("audit_naming_damage - what a botched rename left behind"))
    labels = {"N1": "DOUBLED_ID (file carries one actor id twice)",
              "N2": "CROSS_FACTION (file carries two factions' ids)",
              "N3": "FLUENT_LEAK (a fluent key became an id)",
              "N4": "REDUNDANT_WORD (faction named twice)",
              "N5": "DOTTED_FACTION (dot carries a faction, not a variant)",
              "N6": "HYPHEN (DESIGN rule 9)"}
    base = {"N1": N1_BASELINE, "N2": N2_BASELINE, "N3": N3_BASELINE,
            "N4": N4_BASELINE, "N5": N5_BASELINE, "N6": N6_BASELINE}

    rows, failed = [], 0
    for code in ("N1", "N2", "N3", "N4", "N5", "N6"):
        n = len(hits[code])
        state = "PASS" if n <= base[code] else "FAIL"
        if n > base[code]:
            failed += 1
        rows.append([code, labels[code], str(n), str(base[code]), state])
    print(table(["code", "pathology", "count", "ratchet", ""], rows))

    print(h2("Per-faction breakdown"))
    facs = sorted({f for v in hits.values() for f, _ in v})
    brk = [[f] + [str(sum(1 for g, _ in hits[c] if g == f))
                  for c in ("N1", "N2", "N3", "N4", "N5", "N6")] for f in facs]
    brk = [r for r in brk if any(x != "0" for x in r[1:])]
    brk.sort(key=lambda r: -sum(int(x) for x in r[1:]))
    print(table(["faction", "N1", "N2", "N3", "N4", "N5", "N6"], brk))

    for code in sorted(want):
        rowsl = [(f, v) for f, v in hits.get(code, [])
                 if not args.faction or f == args.faction]
        print(h2(f"{code} - {labels.get(code, '?')} ({len(rowsl)})"))
        for f, v in sorted(rowsl):
            print(f"    {f:18s} {v}")

    print(f"\n**{failed} of 6 ratchets exceeded.**")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
