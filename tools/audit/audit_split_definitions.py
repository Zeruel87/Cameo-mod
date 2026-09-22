#!/usr/bin/env python3
"""audit_split_definitions.py — one weapon, two files, one silent merge.

⛔ THE INCIDENT THAT BUILT THIS (2026-09-06). `HMG` is defined at
`ContentPacks/D2k/Atreides/yaml/weapons.yaml:202` AND at `weapons/d2k.yaml:1570`.
Both files are LIVE in the manifest, so the engine MERGES them into one weapon.
A W24 collapse removed the local `Warhead@1Dam` from the ContentPack copy and set
the surviving main's damage — and nothing happened, because the legacy copy still
supplied `Warhead@1Dam`. Worse than nothing: the merge left the two mains at the
SAME value, which is the broadcast fingerprint, so `HMG` and its inheritor `HMGh`
*entered* `audit_warhead_split` FAIL 1 as a result of being collapsed.

That is the shape of the bug in general: **you edit the copy you can see, and the
copy you cannot see puts the field back.** The boot gate cannot catch it (the merge
is legal), `audit_duplicate_keys` cannot see it (it looks for duplicate keys INSIDE
one node, not the same node in two files), and a resolved-node reader shows only the
merged result, which looks intentional.

Almost all of the current findings are ContentPack-migration residue: Ruling 9 moved
weapons OUT of the legacy `mods/cameo/weapons/*.yaml` globals into per-faction packs
and, in these cases, left the original behind.

Two buckets, because they are different problems:

  S1  a weapon defined in BOTH a legacy global and a ContentPack — migration residue,
      and the dangerous one: two owners, two lanes, and an invisible merge.
  S2  a weapon defined twice within the same tier (two packs, or two globals).

⚠ LIVE FILES ONLY. The file list comes from the manifest, never from a glob —
several `mods/cameo/weapons/*.yaml` files are dead and their duplicates are harmless
dead code. Scanning a glob would report ~244 findings instead of the real number.

Exit 1 when a bucket rises above its baseline. Lower the baselines as the duplicates
are resolved (delete the legacy copy once the pack copy is complete); never raise.
"""

from __future__ import annotations

import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import miniyaml  # noqa: E402
from report import h1, h2, table  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Ratchets, established 2026-09-06 on the first run. LOWER ONLY.
S1_BASELINE = 56
S2_BASELINE = 2

TOP_LEVEL = re.compile(r"^([A-Za-z_^][A-Za-z0-9_.^]*):")


def definitions() -> dict[str, list[str]]:
    """{weapon name: [\"path:line\", ...]} across the manifest's LIVE weapon files."""
    man = miniyaml.load_manifest(ROOT)
    found: dict[str, list[str]] = collections.defaultdict(list)
    for entry in man.weapons:
        path = pathlib.Path(str(entry))
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            continue
        short = path.as_posix()
        short = short.split("mods/cameo/", 1)[-1]
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            m = TOP_LEVEL.match(line)
            if m:
                found[m.group(1)].append(f"{short}:{lineno}")
    return found


def is_global(place: str) -> bool:
    return place.startswith("weapons/")


def main() -> int:
    found = definitions()
    dupes = {k: v for k, v in found.items() if len(v) > 1}

    s1, s2 = [], []
    for name in sorted(dupes):
        places = dupes[name]
        globals_ = [p for p in places if is_global(p)]
        packs = [p for p in places if not is_global(p)]
        row = [f"`{name}`", " · ".join(f"`{p}`" for p in places)]
        (s1 if globals_ and packs else s2).append(row)

    out = [h1("Split definitions — one weapon, two live files, one silent merge")]
    out.append(
        f"Live weapon files in the manifest: **{len(miniyaml.load_manifest(ROOT).weapons)}** "
        f"· names defined more than once: **{len(dupes)}**\n")
    out.append(
        "The engine MERGES same-named top-level nodes across files. Editing one copy leaves "
        "the other supplying its own fields, so a removal can silently do nothing — see the "
        "`HMG` incident in this file's docstring.\n")
    out.append(f"| bucket | count | baseline |\n|---|--:|--:|")
    out.append(f"| S1 legacy global + ContentPack | {len(s1)} | {S1_BASELINE} |")
    out.append(f"| S2 same tier twice | {len(s2)} | {S2_BASELINE} |\n")

    out.append(h2(f"S1 — defined in a legacy global AND a ContentPack ({len(s1)})"))
    out.append(
        "ContentPack-migration residue. **Fix by deleting the LEGACY copy** once the pack "
        "copy is complete — never by editing both, which is how the two drift apart. "
        "⚠ Check `mod.yaml` load order before deleting: if the global loads LATER it is the "
        "one whose fields win today, so a naive delete changes behaviour. Diff the resolved "
        "weapon before and after with `tools/audit/review_resolve_diff.py`.\n")
    out.append(table(["weapon", "defined at"], s1[:60]))
    if len(s1) > 60:
        out.append(f"\n_... and {len(s1) - 60} more._\n")

    out.append(h2(f"S2 — defined twice within the same tier ({len(s2)})"))
    out.append(table(["weapon", "defined at"], s2[:40]))

    failed = len(s1) > S1_BASELINE or len(s2) > S2_BASELINE
    if failed:
        out.append(
            f"\n**FAIL** — S1 {len(s1)}/{S1_BASELINE}, S2 {len(s2)}/{S2_BASELINE}. A new "
            "split definition landed. Delete the duplicate rather than editing both copies.\n")
    else:
        out.append(
            f"\n_at or below baseline_ — pre-existing migration residue. **Lower "
            "`S1_BASELINE`/`S2_BASELINE` as duplicates are deleted; never raise them.**\n")

    print("\n".join(out).rstrip())
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
