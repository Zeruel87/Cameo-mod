#!/usr/bin/env python3
"""audit_packs.py — content-pack conversion & placement audit (DESIGN §2).

P1  Conversion coverage: per faction prefix, how many actors live inside
    its ContentPack vs outside (monolith rules/*). Factions with actors
    outside packs are unconverted/partially converted.
P2  Wrong-pack detector: actors inside a faction pack whose id does not
    carry the pack's dominant prefix (Shared/Core packs exempt).
P3  Manifest-vs-disk: content.yaml must list exactly the yaml files on
    disk; filenames must come from the closed standard set.
P4  Naming summary: actor-id grammar violations (quick counts) so the
    remaining WPN/SEQ migrations stay measurable.
"""
from __future__ import annotations

import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
MOD = ROOT / "mods/cameo"
PACKS = MOD / "ContentPacks"

STANDARD_FILES = {
    "faction.yaml", "buildings.yaml", "defenses.yaml", "infantry.yaml",
    "vehicles.yaml", "aircraft.yaml", "naval.yaml", "upgrades.yaml",
    "promotions.yaml", "husks.yaml", "templates.yaml", "weapons.yaml",
    "sequences.yaml", "ai.yaml", "misc.yaml",
}
SHARED_NAMES = {"Shared", "Core"}
ID_GRAMMAR = re.compile(r"^[a-z0-9]+(?:[._][a-zA-Z0-9]+)*$")


def top_keys(path: pathlib.Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return []
    return re.findall(r"^([^\t\n #][^:\n]*):", text, re.M)


def main() -> int:
    findings = 0

    # ---- collect actor definitions: pack files vs monolith files ---------- #
    pack_actor_files: dict[str, str] = {}
    monolith_actor_files: dict[str, str] = {}
    pack_of: dict[str, list[str]] = defaultdict(list)   # pack dir -> actor keys
    rules_like = lambda n: n not in ("weapons.yaml", "sequences.yaml", "ai.yaml")

    for yml in PACKS.glob("*/*/yaml/*.yaml"):
        if not rules_like(yml.name):
            continue
        pack = f"{yml.parts[-4]}/{yml.parts[-3]}"
        for k in top_keys(yml):
            if k.startswith("^"):
                continue
            pack_actor_files[k] = str(yml.relative_to(ROOT))
            pack_of[pack].append(k)
    for yml in PACKS.glob("*/yaml/*.yaml"):        # theme-level packs (wrappers)
        if not rules_like(yml.name):
            continue
        pack = yml.parts[-3]
        for k in top_keys(yml):
            if k.startswith("^"):
                continue
            pack_actor_files[k] = str(yml.relative_to(ROOT))
            pack_of[pack].append(k)
    for yml in (MOD / "rules").glob("*.yaml"):
        for k in top_keys(yml):
            if not k.startswith("^"):
                monolith_actor_files[k] = str(yml.relative_to(ROOT))

    # faction prefixes = two leading sections of prefixed ids (heuristic)
    def prefix_of(actor: str) -> str | None:
        m = re.match(r"^((?:td|ts|ra1|ra2|wc2)_[a-z0-9]+|[a-z][a-z0-9]+)_", actor)
        return m.group(1) if m else None

    print("# audit_packs — content-pack conversion & placement (DESIGN §2)\n")

    # ---- P1: conversion coverage per prefix -------------------------------- #
    in_pack = Counter()
    outside = defaultdict(list)
    for a in pack_actor_files:
        p = prefix_of(a)
        if p:
            in_pack[p] += 1
    for a, f in monolith_actor_files.items():
        p = prefix_of(a)
        if p:
            outside[p].append((a, f))
    # ⚠ The name is the TIE-BREAK, and it is not optional: the input is a SET, so its iteration
    # order varies between runs, and a stable sort on the count alone therefore ordered equal-count
    # rows differently every time. docs/audit/latest/ is TRACKED evidence (CLAUDE.md rule 8) and
    # that churn diffed ~140 lines on every regeneration for no reason.
    prefixes = sorted(set(in_pack) | set(outside), key=lambda p: (-len(outside.get(p, [])), p))
    print("## P1 — conversion coverage (faction prefixes with actors OUTSIDE packs)\n")
    print("| prefix | in packs | outside packs | sample outside file |")
    print("|---|---|---|---|")
    for p in prefixes:
        out = outside.get(p, [])
        if not out and in_pack.get(p):
            continue  # fully converted — listed in the summary line only
        if len(out) < 1:
            continue
        findings += len(out)
        print(f"| {p} | {in_pack.get(p, 0)} | {len(out)} | {out[0][1]} |")
    fully = sorted(p for p in in_pack if not outside.get(p))
    print(f"\nFully converted prefixes ({len(fully)}): {', '.join(fully)}\n")

    # ---- P2: wrong-pack actors --------------------------------------------- #
    print("## P2 — actors whose id does not match the pack's dominant prefix\n")
    print("| pack | actor | dominant prefix |")
    print("|---|---|---|")
    p2 = 0
    for pack, actors in sorted(pack_of.items()):
        leaf = pack.split("/")[-1]
        if leaf in SHARED_NAMES or "/" not in pack:
            continue  # theme wrappers + shared packs exempt
        prefs = Counter(prefix_of(a) for a in actors if prefix_of(a))
        if not prefs:
            continue
        dom, _ = prefs.most_common(1)[0]
        for a in actors:
            p = prefix_of(a)
            if p and p != dom:
                print(f"| {pack} | {a} | {dom} |")
                p2 += 1
    if not p2:
        print("| _none_ | | |")
    findings += p2
    print()

    # ---- P3: manifest vs disk + closed file set ----------------------------- #
    print("## P3 — content.yaml manifest vs disk / nonstandard filenames\n")
    p3 = 0
    for pack_dir in sorted(PACKS.glob("*/*/")) + sorted(PACKS.glob("*/")):
        ydir = pack_dir / "yaml"
        manifest = pack_dir / "content.yaml"
        if not ydir.is_dir() or not manifest.is_file():
            continue
        on_disk = {f.name for f in ydir.glob("*.yaml")}
        listed = set(re.findall(r"yaml/([a-z_0-9]+\.yaml)", manifest.read_text(encoding="utf-8-sig")))
        rel = pack_dir.relative_to(PACKS)
        for f in sorted(on_disk - listed):
            print(f"- `{rel}`: `{f}` on disk but NOT in content.yaml")
            p3 += 1
        for f in sorted(listed - on_disk):
            print(f"- `{rel}`: `{f}` in content.yaml but MISSING on disk (crash risk)")
            p3 += 1
        for f in sorted(on_disk - STANDARD_FILES):
            print(f"- `{rel}`: nonstandard filename `{f}` (closed set, DESIGN §2)")
            p3 += 1
    if not p3:
        print("_clean_")
    findings += p3
    print()

    # ---- P4: naming-grammar summary ------------------------------------------ #
    print("## P4 — naming summary (counts; details via gen_rename_maps)\n")
    bad_ids = [a for a in list(pack_actor_files) + list(monolith_actor_files)
               if not ID_GRAMMAR.match(a) and not a.startswith("^")]
    print(f"- actor ids violating the lowercase grammar: **{len(bad_ids)}**"
          + (f" (e.g. {', '.join(sorted(bad_ids)[:8])})" if bad_ids else ""))
    print(f"\nTotal findings: {findings}")
    return 1 if p3 else 0


if __name__ == "__main__":
    sys.exit(main())
