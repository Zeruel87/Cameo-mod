#!/usr/bin/env python3
"""derive_versus_columns.py — write the DESIGN §12.0l derived armour rows into EVERY Versus table.

The generator (`gen_weapon_template.derive_rows`) already writes them into the tables it emits.
This tool covers everything else: the hand-kept `^Warhead_*` templates it does not emit and the
legacy weapons that still declare `Versus` locally (A5). Until they carry the rows, a unit that
wears a derived type (`CyborgLight`, `AntiAirVehicle`, `ShipHeavy`, …) would be hit by those
weapons for a flat 100% — the engine answers an absent row with 100.

How it decides, per LOCAL `Versus` / `PercentageVersus` node (a node declared in that file):
  * the values come from the RESOLVED table of the weapon or template that declares it, so an
    inherited parent value is used exactly as the engine will see it;
  * each `GEO_DERIVED` type whose two parents are present gets `round(sqrt(a x b))`, in
    `GEO_DERIVED` order (a parent is final before its child reads it);
  * a row already present is updated in place, a missing one is appended to the node;
  * `Heroic` is NOT touched here: in a hand-kept table it is a hand value, and moving it moves
    hero balance against those weapons (a separate maintainer call).
A weapon with no local table inherits its parent's rows, which this tool made correct.

Idempotent: a second `--write` changes nothing. Encoding, BOM and line endings are preserved.
Parsing goes through `miniyaml` (CLAUDE.md rule 8e); only the edit itself is textual, at the
line numbers the parser reports.

Usage:
    python tools/balance/derive_versus_columns.py            # dry run: count, exit 1 if any
    python tools/balance/derive_versus_columns.py --write
    python tools/balance/derive_versus_columns.py --files mods/cameo/weapons/weapons.yaml --write
"""
from __future__ import annotations

import argparse
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import miniyaml  # noqa: E402
from gen_weapon_template import GEO_DERIVED, NON_ARMOR_ROWS  # noqa: E402

TABLES = ("Versus", "PercentageVersus")
INT = re.compile(r"^-?\d+$")


def desired_rows(resolved: dict[str, int]) -> dict[str, int]:
    """The derived rows a table with these resolved values must carry."""
    vals = dict(resolved)
    out = {}
    for name, parents in GEO_DERIVED:
        if all(p in vals and vals[p] >= 0 for p in parents):
            product = 1.0
            for p in parents:
                product *= vals[p]
            vals[name] = int(round(product ** (1.0 / len(parents))))
            out[name] = vals[name]
    return out


def as_int_table(node) -> dict[str, int]:
    return {c.key: int(c.value) for c in node.children
            if c.value is not None and INT.match(c.value.strip())}


def read_text(path: pathlib.Path) -> tuple[str, str, bool]:
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc), enc, bom
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"cannot decode {path}")


def plan_file(rs, path: pathlib.Path):
    """[(line_index_0based, kind, key, value, indent)] edits for one file."""
    edits = []
    for top in miniyaml.load(path):
        if top.key.startswith("-"):
            continue
        resolved_top = rs.resolve_weapon(top.key)
        if resolved_top is None:
            continue
        for wh in top.children:
            if not wh.key.startswith("Warhead"):
                continue
            for tbl in wh.children:
                if tbl.key not in TABLES or not tbl.children:
                    continue
                rwh = next((c for c in resolved_top.children if c.key == wh.key), None)
                rtbl = next((c for c in rwh.children if c.key == tbl.key), None) if rwh else None
                if rtbl is None:
                    continue
                base = {k: v for k, v in as_int_table(rtbl).items()
                        if k not in dict(GEO_DERIVED)}
                want = desired_rows(base)
                if not want:
                    continue
                local = {c.key: c for c in tbl.children}
                last = max(c.line for c in tbl.children)
                for name, value in want.items():
                    have = local.get(name)
                    if have is not None:
                        if have.value is None or have.value.strip() != str(value):
                            edits.append((have.line - 1, "set", name, value, None))
                    else:
                        edits.append((last - 1, "add", name, value, tbl.children[-1].line - 1))
    return edits


def apply(path: pathlib.Path, edits) -> int:
    text, enc, bom = read_text(path)
    crlf = "\r\n" in text
    lines = text.split("\r\n" if crlf else "\n")
    adds: dict[int, list[str]] = {}
    changed = 0
    for idx, kind, name, value, ref in edits:
        if kind == "set":
            m = re.match(r"^(\s*)([^:]+):", lines[idx])
            lines[idx] = f"{m.group(1)}{m.group(2)}: {value}"
            changed += 1
        else:
            indent = re.match(r"^(\s*)", lines[ref]).group(1)
            adds.setdefault(idx, []).append(f"{indent}{name}: {value}")
            changed += 1
    for idx in sorted(adds, reverse=True):
        lines[idx + 1:idx + 1] = adds[idx]
    out = ("\r\n" if crlf else "\n").join(lines)
    data = out.encode("utf-8" if enc == "utf-8-sig" else enc)
    if bom and not data.startswith(b"\xef\xbb\xbf"):
        data = b"\xef\xbb\xbf" + data
    path.write_bytes(data)
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--files", nargs="*", help="limit to these weapon files (repo-relative)")
    args = ap.parse_args()
    rs = miniyaml.Ruleset(ROOT)
    man = miniyaml.load_manifest(ROOT)
    files = []
    for entry in man.weapons:
        p = pathlib.Path(str(entry))
        p = p if p.is_absolute() else ROOT / p
        if p.exists():
            files.append(p)
    if args.files:
        wanted = {(ROOT / f).resolve() for f in args.files}
        files = [f for f in files if f.resolve() in wanted]
    total = 0
    for f in files:
        edits = plan_file(rs, f)
        if not edits:
            continue
        rel = f.relative_to(ROOT).as_posix()
        n_add = sum(1 for e in edits if e[1] == "add")
        n_set = len(edits) - n_add
        print(f"{rel}: {n_add} rows to add, {n_set} to correct")
        total += len(edits)
        if args.write:
            apply(f, edits)
    print(f"{'written' if args.write else 'pending'}: {total} derived rows")
    return 0 if (args.write or total == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
