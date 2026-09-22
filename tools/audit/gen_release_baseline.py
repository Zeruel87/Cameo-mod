#!/usr/bin/env python3
"""gen_release_baseline.py - snapshot a SHIPPED release as an external baseline.

Every gate in this tree measures the tree against itself, so a defect that lands
in one commit becomes the baseline for the next one. That is how 238 weapons
drifted away from the last shipped build without a single audit going red.

This writes the one thing the tree cannot derive from itself: what a weapon
actually dealt in a release players played.

    python tools/audit/gen_release_baseline.py --tag playtest-20260709
    python tools/audit/gen_release_baseline.py --tree /c/tmp/rel2607   # existing checkout

The metric is TOTAL FLAT MAIN damage per weapon, resolved through
`miniyaml.Ruleset` (never a hand parser - CLAUDE.md rule 8e), with `*Percentage`,
`*FriendlyFire` and `*ExtraDamage` twins excluded because they are halves of a
main rather than mains. `mains` records how many damage warheads produced that
total, which is what makes a collapse visible: 4 -> 1 with the total unchanged is
a correct collapse; 4 -> 1 with the total quartered is HydraSpit.

Consumed by `audit_release_drift.py`.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import miniyaml

DAMAGE_TYPES = {"SpreadDamage", "AreaDamage", "TargetDamage"}
TWIN_MARKERS = ("percentage", "friendlyfire", "extradamage")


def snapshot(root: pathlib.Path) -> dict[str, dict[str, int]]:
    """{weapon: {flat, mains}} for every concrete weapon under `root`."""
    rs = miniyaml.Ruleset(root.resolve())
    out: dict[str, dict[str, int]] = {}
    for name in rs.weapons:
        if name.startswith("^"):
            continue
        try:
            node = rs.resolve_weapon(name)
        except Exception:
            continue
        if node is None:
            continue
        total = count = 0
        for child in node.children:
            if not child.key.startswith("Warhead@"):
                continue
            if (child.value or "").strip() not in DAMAGE_TYPES:
                continue
            if any(m in child.key.lower() for m in TWIN_MARKERS):
                continue
            dmg = next((x.value for x in child.children if x.key == "Damage"), None)
            if dmg and dmg.strip().isdigit():
                total += int(dmg)
                count += 1
        if count:
            out[name] = {"flat": total, "mains": count}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", help="release tag to snapshot (a temp worktree is made and removed)")
    ap.add_argument("--tree", help="path to an existing checkout to snapshot instead")
    ap.add_argument("--out", help="output json (default docs/reference/release_baseline_<tag>.json)")
    args = ap.parse_args()

    if not args.tag and not args.tree:
        ap.error("one of --tag or --tree is required")

    repo = pathlib.Path(__file__).resolve().parents[2]
    temp = None
    try:
        if args.tree:
            root = pathlib.Path(args.tree)
            tag = args.tag or root.name
        else:
            tag = args.tag
            temp = pathlib.Path(tempfile.mkdtemp(prefix="relbase_"))
            root = temp / "tree"
            subprocess.run(["git", "worktree", "add", "--detach", str(root), tag],
                           cwd=repo, check=True, capture_output=True, text=True)

        commit = subprocess.run(["git", "rev-parse", "--short", tag], cwd=repo,
                                capture_output=True, text=True).stdout.strip()
        data = snapshot(root)
        out = pathlib.Path(args.out) if args.out else (
            repo / "docs/reference" / f"release_baseline_{tag.replace('-', '_')}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "_what": "Total FLAT main-warhead damage per weapon, as SHIPPED in "
                     f"{tag}. The external baseline a collapse is verified against. "
                     "Regenerate with tools/audit/gen_release_baseline.py.",
            "_release_tag": tag,
            "_release_commit": commit,
            "_weapons": len(data),
            "weapons": dict(sorted(data.items())),
        }, indent=1), encoding="utf-8", newline="")
        print(f"{len(data)} weapons snapshotted from {tag} ({commit}) -> {out}")
    finally:
        if temp is not None:
            subprocess.run(["git", "worktree", "remove", "--force", str(temp / "tree")],
                           cwd=repo, capture_output=True, text=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
