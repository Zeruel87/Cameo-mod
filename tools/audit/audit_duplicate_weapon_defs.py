#!/usr/bin/env python3
"""audit_duplicate_weapon_defs.py — same weapon key defined in more than one live file.

⛔ THE SILENT-MERGE CLASS. The MiniYAML loader merges identically-named top-level weapon
blocks across EVERY file the manifest lists — so when the ContentPack migration copies a
weapon into `ContentPacks/<X>/yaml/weapons.yaml` and the legacy `mods/cameo/weapons/*.yaml`
original stays in the manifest, BOTH definitions are live and their children merge. An edit
made in only one copy leaves the other's nodes in the resolved weapon:

    d2k25mm      — ContentPacks/D2k/Ordos + weapons/d2k.yaml
    BikeRockets  — ContentPacks/TiberianDawn/Nod + weapons/missiles.yaml (the 7,000 vs
                   16,000 contradiction that sent two agents chasing a phantom)

Fixing one copy is not a fix; deleting a node in one file while the other file still defines
it resurrects it. Until each duplicated weapon has a canonical-file ruling, this list is the
hazard map for every weapon edit.

Ratchet: LOWER-ONLY, established by this script's first run.
"""

import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import miniyaml  # noqa: E402

RATCHELS = {"DUP": 25}


def audit(rs):
    """{weapon key: [(file, line)], ...} for concrete weapons defined in 2+ live files."""
    locs = collections.defaultdict(list)
    for path in rs.manifest.weapons:
        try:
            for n in miniyaml.load(pathlib.Path(path)):
                if n.key.startswith("^"):
                    continue
                locs[n.key].append((str(path), n.line))
        except Exception:
            continue
    return {k: v for k, v in locs.items() if len(v) > 1}


def main() -> int:
    rs = miniyaml.Ruleset(ROOT)
    dups = audit(rs)
    n = len(dups)
    base = RATCHELS["DUP"]
    short = lambda p: p.replace("\\", "/").split("cameo/")[-1]

    out = [f"## duplicate weapon definitions ({n} vs ratchet {base})", ""]
    out.append("| weapon | files |")
    out.append("|---|---|")
    for key in sorted(dups):
        files = "; ".join(f"`{short(p)}:{ln}`" for p, ln in dups[key])
        out.append(f"| `{key}` | {files} |")
    if n > base:
        out.append(f"\n**FAIL — DUP rose above baseline.** Another weapon now silently merges "
                   f"from two live files.\n")
    else:
        out.append("\n_at or below ratchet — this is the known backlog; every entry needs a "
                   "canonical-file ruling (usually: delete the legacy copy once the pack is "
                   "verified complete)._\n")
    print("\n".join(out))
    return 1 if n > base else 0


if __name__ == "__main__":
    raise SystemExit(main())
