#!/usr/bin/env python3
"""audit_dead_warhead_fields.py — yaml keys the engine SILENTLY THROWS AWAY.

    python tools/audit/audit_dead_warhead_fields.py [--json out.json]

⛔ WHY THIS EXISTS (2026-08-22). 2059 `Warhead@…Percentage` nodes across 1284 weapons carry a
`Falloff:` line — on `HealthPercentageDamage`, a type that HAS NO SUCH FIELD. 104 more carry
`IntegrityScale`, so the Tesla/EMP drain of the percentage half never fired. Nothing complained:
the tree booted, every audit was green, `--docs` listed the field on a DIFFERENT warhead.

⚠ THE TRAP: two Cameo docs state "an unknown field throws at load". That is TRUE of
`FieldLoader.LoadField` (FieldLoader.cs:758 -> UnknownFieldAction) and FALSE of
`FieldLoader.Load` (FieldLoader.cs:676), which iterates the TYPE's fields and never looks at
the leftover yaml keys. Warheads load through `Load` (`WeaponInfo.LoadWarheads`,
WeaponInfo.cs:178), so a misplaced field is discarded in silence. The linter (`--check-yaml`)
swaps the action and would catch it — it is not part of `run_all.sh`.

HOW: parse every `*Warhead.cs` in every assembly, resolve the inheritance chain, and compare
each resolved warhead node's keys against the fields its type actually owns. Assembly
precedence follows mod.yaml (AS, CA, Cameo, Cnc, D2k, Common), so a shadowed type resolves the
way `ObjectCreator.FindType` resolves it.

EXIT CODE: 1 above the RATCHET. A discarded field is never intentional, but the tree starts
with a known backlog, so DEAD_FIELD_BASELINE holds today's count and may only ever FALL. Lower
it as each kind is fixed; never raise it to make the suite green.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from cameo_model import Model  # noqa: E402

# Distinct (warhead type, dead field) pairs present when this audit was written (2026-08-22).
# ⚠ RATCHET — LOWER ONLY. Raising it hides a field the engine is throwing away.
DEAD_FIELD_BASELINE = 15

# mod.yaml `Assemblies:` order — first hit wins, exactly like ObjectCreator.FindType.
ASSEMBLY_DIRS = [
    ("AS", "engine/OpenRA.Mods.AS"),
    ("CA", "OpenRA.Mods.CA"),
    ("Cameo", "OpenRA.Mods.Cameo"),
    ("Cnc", "engine/OpenRA.Mods.Cnc"),
    ("D2k", "engine/OpenRA.Mods.D2k"),
    ("Common", "engine/OpenRA.Mods.Common"),
]

CLASS_RE = re.compile(r"^\s*(?:public|internal)\s+(?:abstract\s+|sealed\s+)?class\s+(\w+)\s*:\s*([\w<>, .]+)")
# ⚠ NOT just `public readonly` — FieldLoader loads any public instance field, and some AS
# warheads declare mutable ones (CreateTintedCellsWarhead: `public int Level = 100;`).
# Matching only readonly fields reported 45 live radiation settings as dead.
# Requires the declaration to end in `=` or `;` so methods and properties are excluded.
FIELD_RE = re.compile(
    r"^\s*public\s+(?!readonly\s+static)(?:readonly\s+)?"
    r"(?!class|struct|enum|const|static|delegate|event|abstract|override|virtual|sealed)"
    r"[\w<>\[\]\,\.\?\s]+?\s+(\w+)\s*(?:=|;)")
IGNORE_RE = re.compile(r"\[FieldLoader\.Ignore\]")


def parse_assembly(root: pathlib.Path) -> dict[str, tuple[str | None, set[str]]]:
    """{class name: (base class, own serialisable field names)} for one assembly."""
    out: dict[str, tuple[str | None, set[str]]] = {}
    if not root.is_dir():
        return out
    for path in root.rglob("*.cs"):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        cur: str | None = None
        ignore_next = False
        for line in lines:
            m = CLASS_RE.match(line)
            if m:
                cur = m.group(1)
                base = m.group(2).split(",")[0].strip()
                out.setdefault(cur, (base or None, set()))
                continue
            if cur is None:
                continue
            if IGNORE_RE.search(line):
                ignore_next = True
                continue
            f = FIELD_RE.match(line)
            if f:
                if not ignore_next:
                    out[cur][1].add(f.group(1))
                ignore_next = False
            elif line.strip() and not line.strip().startswith(("[", "//", "*", "/*")):
                ignore_next = False
    return out


def build_index() -> dict[str, dict[str, tuple[str | None, set[str]]]]:
    return {name: parse_assembly(pathlib.Path(d)) for name, d in ASSEMBLY_DIRS}


def resolve_fields(index, cls: str) -> tuple[set[str], str] | None:
    """All serialisable field names on `cls` and its bases, plus the winning assembly."""
    for asm, _ in ASSEMBLY_DIRS:
        if cls in index[asm]:
            fields: set[str] = set()
            name, seen = cls, set()
            while name and name not in seen:
                seen.add(name)
                found = next((index[a][name] for a, _ in ASSEMBLY_DIRS if name in index[a]), None)
                if found is None:
                    break
                base, own = found
                fields |= own
                name = base
            return fields, asm
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--json")
    args = ap.parse_args()

    index = build_index()
    rs = Model(pathlib.Path(args.root)).rs

    dead: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    unresolved: collections.Counter = collections.Counter()
    nodes_scanned = 0

    for name in rs.weapons:
        if name.startswith("^"):
            continue
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        for wh in node.children:
            if not wh.key.startswith("Warhead"):
                continue
            wtype = (wh.value or "").strip()
            if not wtype:
                continue
            got = resolve_fields(index, wtype + "Warhead")
            if got is None:
                unresolved[wtype] += 1
                continue
            fields, _asm = got
            nodes_scanned += 1
            for c in wh.children:
                key = c.key.split("@")[0].strip()
                if key and key not in fields:
                    dead[(wtype, key)].add(name)

    print(f"scanned {nodes_scanned} resolved warhead nodes across {len(rs.weapons)} weapons\n")
    if unresolved:
        print("⚠ warhead types with no C# source found (not checked):")
        for t, n in unresolved.most_common():
            print(f"    {n:5d}  {t}")
        print()

    if not dead:
        print("OK — every warhead field is read by the type that declares it.")
        return 0

    print("DEAD FIELDS — written in yaml, silently discarded by FieldLoader.Load:\n")
    rows = sorted(dead.items(), key=lambda kv: -len(kv[1]))
    for (wtype, key), weapons in rows:
        print(f"  {len(weapons):5d} weapons   {wtype}.{key}")
    weapons_hit = len(set().union(*dead.values()))
    over = len(rows) > DEAD_FIELD_BASELINE
    verdict = "FAIL" if over else "WARN"
    print()
    print(f"{verdict} {len(rows)} dead field kind(s) on {weapons_hit} weapons "
          f"(ratchet {DEAD_FIELD_BASELINE})")
    if over:
        print("**A warhead field was just written that the engine will silently discard.** "
              "Fix the field or the type; do not raise DEAD_FIELD_BASELINE.")
    else:
        print("Lower `DEAD_FIELD_BASELINE` as each kind is fixed; never raise it.")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(
            {f"{t}.{k}": sorted(v) for (t, k), v in dead.items()}, indent=1), encoding="utf-8")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
