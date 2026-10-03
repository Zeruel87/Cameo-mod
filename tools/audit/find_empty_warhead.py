#!/usr/bin/env python3
"""Find weapons whose resolved Warhead@X has an EMPTY type (-> engine builds the
abstract base `Warhead` -> GetConstructor([]) null -> CreateBasic NRE at boot).

Resolves inheritance across ALL live weapon files (parents applied in order,
child overrides last; bare `Warhead@K:` keeps the inherited type; `-Warhead@K:`
removes it). Reports any concrete weapon with a surviving empty-type warhead.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from collections import defaultdict

MOD = Path(__file__).resolve().parents[2] / "mods" / "cameo"
ROOT = MOD.parents[1]

# Live weapon files come from mod.yaml's Weapons: list — a hard-coded list
# misses newly mounted files (e.g. weapons/effects_<game>.yaml, ruling 5a).
def _live_files():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import miniyaml
        man = miniyaml.load_manifest(ROOT)
        out = []
        for entry in man.weapons:
            p = Path(str(entry))
            out.append(p if p.is_absolute() else ROOT / p)
        return [p for p in out if p.exists()]
    except Exception:
        return ([MOD / p for p in ("weapons/weapons.yaml",)]
                + sorted((MOD / "ContentPacks").glob("*/*/yaml/weapons.yaml")))

FILES = _live_files()

RE_INHERITS = re.compile(r"^Inherits(?:@\S+)?:\s*(\S+)")
RE_WARHEAD = re.compile(r"^(-?)Warhead@(\S+?):\s*(\S*)\s*(?:#.*)?$")
RE_TOP = re.compile(r"^([^\s#][^:]*):")


def indent_of(s):
    n = 0
    for ch in s:
        if ch == "\t":
            n += 8 - (n % 8)
        elif ch == " ":
            n += 1
        else:
            break
    return n


# name -> {"parents":[...], "wh":[(removal, key, type), ...] in file order}
nodes = {}

for path in FILES:
    lines = path.read_text(encoding="utf-8").splitlines()
    headers = [i for i, ln in enumerate(lines)
               if ln.strip() and not ln.lstrip().startswith("#") and indent_of(ln) == 0 and RE_TOP.match(ln)]
    for h, start in enumerate(headers):
        end = headers[h + 1] if h + 1 < len(headers) else len(lines)
        name = RE_TOP.match(lines[start]).group(1).strip()
        rec = nodes.setdefault(name, {"parents": [], "wh": []})
        child = [indent_of(lines[j]) for j in range(start + 1, end)
                 if lines[j].strip() and not lines[j].lstrip().startswith("#")]
        base = min(child) if child else 8
        for j in range(start + 1, end):
            raw = lines[j]
            if not raw.strip() or raw.lstrip().startswith("#") or indent_of(raw) != base:
                continue
            c = raw.strip()
            mi = RE_INHERITS.match(c)
            if mi:
                rec["parents"].append(mi.group(1).strip())
            mw = RE_WARHEAD.match(c)
            if mw:
                rec["wh"].append((mw.group(1) == "-", mw.group(2), mw.group(3)))


def resolve(name, stack=()):
    """Return dict key -> type (possibly '') for the fully merged warhead set."""
    if name not in nodes or name in stack:
        return {}
    rec = nodes[name]
    merged = {}
    for p in rec["parents"]:
        for k, t in resolve(p, stack + (name,)).items():
            # a bare Warhead@K: pin inside a template merges fields only —
            # it must NOT clobber an earlier-supplied type with ''
            if t or k not in merged:
                merged[k] = t
    for removal, key, wtype in rec["wh"]:
        if removal:
            merged.pop(key, None)
        elif wtype:
            merged[key] = wtype          # non-empty type overrides
        else:
            merged.setdefault(key, "")    # bare: keep inherited type, else empty
    return merged


bad = []
for name, rec in nodes.items():
    # ^ templates ARE instantiated standalone by WeaponInfo.LoadWarheads —
    # an empty-type node inside one NREs at boot (W27 batch-2 crash).
    for key, wtype in resolve(name).items():
        if wtype == "":
            bad.append((name, key))

print(f"live files: {len(FILES)}  |  nodes: {len(nodes)}  |  weapons + templates scanned")
print(f"EMPTY-TYPE warheads (would NRE at CreateBasic): {len(bad)}\n")
for name, key in sorted(bad):
    # which file defines this weapon?
    print(f"  {name:32s} Warhead@{key}")

# Blocking audit: any empty-type warhead crashes the boot (see the memory
# cameo-empty-warhead-crash). Exit non-zero so run_all.sh flags it red.
sys.exit(1 if bad else 0)
