#!/usr/bin/env python3
"""audit_ca_drift — how far Cameo's vendored OpenRA.Mods.CA has drifted from upstream CA.

Cameo began as a fork of Combined Arms, which is why `OpenRA.Mods.CA/` is vendored at the
repo root (NOT under engine/ — it is mod code, like OpenRA.Mods.Cameo). Cameo's ENGINE then
moved to a different fork, so the vendored files have been adapted rather than mirrored, and
the drift runs in BOTH directions: some files we forward-ported to newer engine APIs, some CA
fixed after we copied them.

This audit measures that, so "are we up to date with CA?" is answerable in one command instead
of by eye. It is INFORMATIONAL — it never fails a build, because adopting upstream CA code is a
maintainer decision, not a correctness gate.

Point it at a CA checkout:
    CA_ROOT=~/Documents/GitHub/CAmod python tools/audit/audit_ca_drift.py
It looks in a few conventional places if CA_ROOT is unset, and says so plainly when it cannot
find one rather than reporting a clean tree.
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OURS = ROOT / "OpenRA.Mods.CA"
CANDIDATES = [
    os.environ.get("CA_ROOT"),
    ROOT.parent / "CAmod",
    pathlib.Path.home() / "Documents" / "GitHub" / "CAmod",
]
SMALL = 6          # a diff this size is usually a rename/refactor, not a behaviour change
LARGE = 50         # a diff this size is a genuinely different implementation


def find_ca():
    for c in CANDIDATES:
        if not c:
            continue
        p = pathlib.Path(c).expanduser() / "OpenRA.Mods.CA"
        if p.is_dir():
            return p
    return None


def diff_lines(a: pathlib.Path, b: pathlib.Path) -> int:
    import difflib
    try:
        x = a.read_text(encoding="utf-8", errors="replace").splitlines()
        y = b.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return -1
    return sum(1 for d in difflib.unified_diff(x, y, n=0) if d[:1] in "+-" and d[:3] not in ("---", "+++"))


def main():
    print("# audit_ca_drift — vendored OpenRA.Mods.CA vs upstream Combined Arms\n")
    ca = find_ca()
    if ca is None:
        print("_no CA checkout found_ — set `CA_ROOT` to a clone of https://github.com/Inq8/CAmod.")
        print("\nNOT a clean result: this audit could not run.")
        return 0

    print(f"Upstream: `{ca}`\n")
    ours = {p.relative_to(OURS).as_posix() for p in OURS.rglob("*.cs") if "/obj/" not in p.as_posix()}
    theirs = {p.relative_to(ca).as_posix() for p in ca.rglob("*.cs") if "/obj/" not in p.as_posix()}

    same, drifted, only_ours = [], [], sorted(ours - theirs)
    for rel in sorted(ours & theirs):
        n = diff_lines(OURS / rel, ca / rel)
        (same if n == 0 else drifted).append((rel, n))
    missing = sorted(theirs - ours)

    print("| | files |")
    print("|---|--:|")
    print(f"| vendored here | {len(ours)} |")
    print(f"| upstream | {len(theirs)} |")
    print(f"| identical | {len(same)} |")
    print(f"| drifted | {len(drifted)} |")
    print(f"| ours only (not upstream) | {len(only_ours)} |")
    print(f"| upstream only (NOT adopted) | {len(missing)} |")

    small = [r for r in drifted if 0 < r[1] <= SMALL]
    large = [r for r in drifted if r[1] > LARGE]
    total = sum(n for _r, n in drifted)
    print(f"\n**{total} differing lines** across {len(drifted)} files — "
          f"{len(small)} of them <= {SMALL} lines (usually a refactor to adopt), "
          f"{len(large)} over {LARGE} (a different implementation; port by hand or not at all).\n")

    print(f"## Upstream files never adopted ({len(missing)}), by area\n")
    areas = {}
    for rel in missing:
        parts = rel.split("/")
        areas.setdefault("/".join(parts[:2]) if len(parts) > 1 else parts[0], []).append(rel)
    for area, files in sorted(areas.items(), key=lambda kv: -len(kv[1])):
        print(f"- `{area}` — **{len(files)}**")

    print(f"\n## Cheapest to re-sync — drifted by <= {SMALL} lines ({len(small)})\n")
    for rel, n in sorted(small, key=lambda kv: kv[1])[:40]:
        print(f"- {n:2d}  `{rel}`")

    print(f"\n## Diverged the most ({len(large)}) — do NOT bulk-copy these\n")
    for rel, n in sorted(large, key=lambda kv: -kv[1])[:20]:
        print(f"- {n:4d}  `{rel}`")

    print("\n_Informational: this audit never fails. Adopting upstream CA code is a maintainer "
          "decision — see `docs/design/UPSTREAM_MODS.md`._")
    return 0


if __name__ == "__main__":
    sys.exit(main())
