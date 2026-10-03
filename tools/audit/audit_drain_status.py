#!/usr/bin/env python3
"""audit_drain_status.py — per-file ContentPack drain status.

For every global weapons/sequences/audio yaml still mounted by mod.yaml,
count top-level defs that are live-referenced by the resolved ruleset vs
dead, and list which packs reference the live ones.

  R1  file summary table (nodes / live / dead / referrer packs)
  R2  files with zero live defs (pure dead inventory — unused-file audit
      candidates, NOT deletion candidates: map-script and dormant-actor
      references are invisible to the resolver)
  R3  live defs referenced by a DIFFERENT theme than the file's own —
      cross-theme inventory needing a Shared ruling or a move

Companion to audit_orphans.py (which is a flat zero-ref count); this is the
per-file, per-kind view used to plan pack drains.
"""

from __future__ import annotations

import pathlib
import re
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from miniyaml import Ruleset
from report import h1, h2, table

ROOT = pathlib.Path(__file__).resolve().parents[2]
MOD = ROOT / "mods/cameo"


def pack_of(path) -> str:
    f = str(path).replace("\\", "/")
    m = re.search(r"ContentPacks/([^/]+)/([^/]+)/", f)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    m = re.search(r"mods/cameo/([^/]+)/([^/]+)\.yaml", f)
    return f"GLOBAL:{m.group(2)}" if m else "GLOBAL"


def toplevel_names(fp: pathlib.Path) -> list[str]:
    out = []
    for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"^[^\s#]", line) and ":" in line:
            out.append(line.split(":")[0].strip())
    return out


def collect_refs(rs) -> tuple[dict, dict]:
    """weapon-name -> referrer packs; sequence-image -> referrer packs."""
    wref: dict[str, set] = defaultdict(set)
    sref: dict[str, set] = defaultdict(set)

    def walk(n, pk, into_w=None):
        k0 = n.key.split("@")[0]
        v = n.value or ""
        if v:
            if k0 == "Weapon" or k0.startswith("Weapon"):
                for tok in v.split(","):
                    if tok.strip():
                        wref[tok.strip()].add(pk)
            if k0 in ("Image", "Images"):
                for tok in v.split(","):
                    if tok.strip():
                        sref[tok.strip()].add(pk)
        for c in n.children:
            walk(c, pk)

    for name, raw in rs.actors.items():
        if name.startswith("^"):
            continue
        a = rs.resolve(name)
        if a is None:
            continue
        walk(a, pack_of(getattr(raw, "file", "") or ""))

    for name in list(rs.weapons):
        w = rs.resolve_weapon(name)
        if w is None:
            continue
        pk = pack_of(getattr(rs.weapons.get(name), "file", "") or "")
        walk(w, pk)
        for inh, _ in rs.inherits_of(w):
            wref[inh.lstrip("^")].add(pk)
    return wref, sref


def main() -> int:
    rs = Ruleset(repo_root=ROOT)
    wref, sref = collect_refs(rs)

    rows, zero_live, cross_theme = [], [], []
    for kind, refs, files in (
        ("weapons", wref, sorted(MOD.glob("weapons/*.yaml"))),
        ("sequences", sref, sorted(MOD.glob("sequences/*.yaml"))),
    ):
        for f in files:
            nodes = toplevel_names(f)
            if not nodes:
                continue
            live = [n for n in nodes if refs.get(n.lstrip("^"))]
            packs = sorted({p for n in live for p in refs[n.lstrip("^")]})
            theme = f.stem.lower()
            foreign = sorted({p for p in packs
                              if p.startswith("GLOBAL:") is False
                              and theme not in p.lower()})
            rows.append([f"{kind}/{f.name}", len(nodes), len(live),
                         len(nodes) - len(live),
                         ", ".join(packs[:6]) + ("…" if len(packs) > 6 else "")])
            if not live:
                zero_live.append(f"{kind}/{f.name}")
            if foreign:
                cross_theme.append([f"{kind}/{f.name}", ", ".join(foreign[:5])])

    print(h1("audit_drain_status — live vs dead defs per global file"))
    print(h2("R1 — file summary (nodes / live / dead / referrer packs)"))
    print(table(["file", "nodes", "live", "dead", "live referrers"], rows))
    print(h2(f"R2 — zero-live files ({len(zero_live)}) — dead inventory"))
    print(", ".join(zero_live) or "_none_")
    print(h2(f"R3 — cross-theme referrers ({len(cross_theme)})"))
    print(table(["file", "foreign packs"], cross_theme))
    return 0


if __name__ == "__main__":
    sys.exit(main())
