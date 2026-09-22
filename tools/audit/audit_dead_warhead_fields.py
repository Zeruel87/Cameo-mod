#!/usr/bin/env python3
"""audit_dead_warhead_fields.py — yaml keys the engine SILENTLY THROWS AWAY.

    python tools/audit/audit_dead_warhead_fields.py [--root REPO] [--engine-root DIR]
                                                    [--json out.json]

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

HOW: parse every `*.cs` in the mod's six assemblies, resolve the inheritance chain, and compare
each resolved warhead node's keys against the fields its type actually owns. Assembly
precedence follows mod.yaml (AS, CA, Cameo, Cnc, D2k, Common), so a shadowed type resolves the
way `ObjectCreator.FindType` resolves it. Source locations: CA and Cameo are vendored at the
REPOSITORY ROOT; AS, Cnc, D2k and Common live in the engine checkout (`<root>/engine`, or
`--engine-root` when running from a worktree that has no engine/ of its own).

⚠ THIS IS A LINE-REGEX PARSER, NOT A C# COMPILER. It reads class declarations and public
instance field declarations line by line. Concrete-type precedence follows mod.yaml assembly
order, but inherited bases are bound by UNQUALIFIED class name: namespace resolution,
preprocessor/`#if` handling, partial classes spread over files and everything else a compiler
does are beyond it, and it does NOT claim to detect every construct it cannot parse. What it
cannot verify it says so: a warhead type absent from the scanned sources, a chain broken at
an unknown base, an inheritance cycle, a base that continues on the next line, an unreadable
source file or a missing assembly all make the run INCOMPLETE instead of "every field is read".

EXIT CODES:
    0  complete, trustworthy scan — dead kinds within the ratchet (OK, or WARN below it)
    1  complete, trustworthy scan — dead kinds above the RATCHET (lower-only; never raise)
    2  INCOMPLETE — schema coverage is partial (see above). Dead-field diagnostics found so
       far are still printed, but `--json` is NOT rewritten: any previous file is preserved
       so a partial run can never masquerade as a current result. Only a completed
       trustworthy scan writes the mapping — including `{}` when nothing is dead.
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

EXIT_OK = 0
EXIT_RATCHET = 1
EXIT_INCOMPLETE = 2

# Distinct (warhead type, dead field) pairs present when this audit was written (2026-08-22).
# ⚠ RATCHET — LOWER ONLY. Raising it hides a field the engine is throwing away.
DEAD_FIELD_BASELINE = 15

# mod.yaml `Assemblies:` order — first hit wins, exactly like ObjectCreator.FindType.
# location "repo" = vendored at the repository root (NOT under engine/ — that trap cost
# audit_unique_traits 14 trait types, see LESSONS_LEARNED 2026-08-23); "engine" = in the
# engine checkout, rooted at <root>/engine by default or --engine-root when given.
ASSEMBLY_DIRS: list[tuple[str, str, str]] = [
    ("AS", "engine", "OpenRA.Mods.AS"),
    ("CA", "repo", "OpenRA.Mods.CA"),
    ("Cameo", "repo", "OpenRA.Mods.Cameo"),
    ("Cnc", "engine", "OpenRA.Mods.Cnc"),
    ("D2k", "engine", "OpenRA.Mods.D2k"),
    ("Common", "engine", "OpenRA.Mods.Common"),
]
ASSEMBLY_ORDER = [name for name, _loc, _sub in ASSEMBLY_DIRS]

# Bases OUTSIDE the scanned assemblies that are known to contribute no serialisable fields,
# so a chain ending there is COMPLETE:
#   object / System.Object — the C# root type
#   IWarhead               — OpenRA.Game/Traits/TraitsInterfaces.cs:563, an interface, and
#                            C# interfaces cannot declare instance fields
# (The other concrete bases in the warhead chains — Warhead and WarheadAS — live in the
# scanned assemblies: OpenRA.Mods.Common/Warheads/Warhead.cs and
# OpenRA.Mods.AS/Warheads/WarheadAS.cs.)
# ANY other unknown base means the chain broke mid-way: the field set collected so far may
# be missing inherited fields, so the type is reported incomplete, never trusted.
SAFE_TERMINAL_BASES = {"object", "system.object", "iwarhead"}

# Sentinel base for a class whose `: Base` list continues on the NEXT line — the line
# parser cannot read it, so the chain must stop here as INCOMPLETE (never as "no base",
# which would wrongly pass as a valid terminal and hide the missing inherited fields).
UNPARSED_BASE = "<base-continues-on-next-line>"

CLASS_RE = re.compile(
    r"^\s*(?:public|internal)\s+(?:abstract\s+|sealed\s+)?class\s+(\w+)(?:\s*:\s*([\w<>, .]+))?")
# ⚠ NOT just `public readonly` — FieldLoader loads any public instance field, and some AS
# warheads declare mutable ones (CreateTintedCellsWarhead: `public int Level = 100;`).
# Matching only readonly fields reported 45 live radiation settings as dead.
# Requires the declaration to end in `=` or `;` so methods and properties are excluded.
# The keyword exclusions carry \b so a type merely NAMED like a keyword prefix
# (`public eventPayload Thing;`) still parses as a field.
FIELD_RE = re.compile(
    r"^\s*public\s+(?!readonly\s+static)(?:readonly\s+)?"
    r"(?!class\b|struct\b|enum\b|const\b|static\b|delegate\b|event\b"
    r"|abstract\b|override\b|virtual\b|sealed\b)"
    r"[\w<>\[\]\,\.\?\s]+?\s+(\w+)\s*(?:=|;)")
IGNORE_RE = re.compile(r"\[FieldLoader\.Ignore\]")


def parse_assembly(root: pathlib.Path) -> dict[str, tuple[str | None, set[str]]]:
    """{class name: (base class, own serialisable field names)} for one assembly.

    Raises OSError if a source file cannot be read — the caller must never fabricate a
    complete schema from a partially readable directory.
    """
    out: dict[str, tuple[str | None, set[str]]] = {}
    if not root.is_dir():
        return out
    for path in root.rglob("*.cs"):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        cur: str | None = None
        ignore_next = False
        for line in lines:
            m = CLASS_RE.match(line)
            if m:
                cur = m.group(1)
                if line.rstrip().endswith(":"):
                    base = UNPARSED_BASE          # base list continues on the next line
                else:
                    base = (m.group(2) or "").split(",")[0].strip() or None
                out.setdefault(cur, (base, set()))
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


def assembly_source_dirs(root: pathlib.Path,
                         engine_root: pathlib.Path | None = None,
                         ) -> list[tuple[str, pathlib.Path]]:
    """(assembly, source directory), every path ROOTED at `root`/`engine_root` — never CWD
    relative, which was the 2026-09-09 defect: run from any other directory the index came
    back empty and the audit answered "OK — every warhead field is read" on zero coverage."""
    engine_root = engine_root if engine_root is not None else root / "engine"
    return [(name, (root if loc == "repo" else engine_root) / sub)
            for name, loc, sub in ASSEMBLY_DIRS]


def build_index(root: pathlib.Path | str = ".",
                engine_root: pathlib.Path | str | None = None,
                ) -> dict[str, dict[str, tuple[str | None, set[str]]]]:
    """{assembly: {class: (base, own fields)}} for every assembly that exists.

    Default `root="."` keeps the historical behaviour (paths relative to the CWD when run
    from the repository root). A missing directory yields an empty entry; gate on
    `missing_assemblies` before trusting the result.
    """
    root = pathlib.Path(root)
    engine_root = pathlib.Path(engine_root) if engine_root is not None else None
    return {name: parse_assembly(d) for name, d in assembly_source_dirs(root, engine_root)}


def missing_assemblies(root: pathlib.Path | str,
                       engine_root: pathlib.Path | str | None = None,
                       ) -> list[tuple[str, pathlib.Path]]:
    """Assemblies whose C# source directory is absent or empty — with any of these the
    field schema cannot be fully covered and the audit must refuse a passing verdict."""
    return [(name, d) for name, d in assembly_source_dirs(pathlib.Path(root),
                                                          pathlib.Path(engine_root)
                                                          if engine_root is not None else None)
            if not (d.is_dir() and any(d.rglob("*.cs")))]


def resolve_fields(index, cls: str) -> tuple[set[str], str, bool] | None:
    """All serialisable field names on `cls` and its bases, plus the winning assembly.

    Returns None if `cls` is defined in no scanned assembly. The bool is False when the
    chain broke at an unknown, non-safe base: `fields` is then PARTIAL (it can be missing
    inherited fields) and must not be used to judge yaml keys dead.
    """
    for asm in ASSEMBLY_ORDER:
        if cls not in index.get(asm, {}):
            continue
        fields: set[str] = set()
        name, seen, complete = cls, set(), True
        while name and name not in seen:
            seen.add(name)
            found = next((index[a][name] for a in ASSEMBLY_ORDER if name in index[a]), None)
            if found is None:
                complete = name.lower() in SAFE_TERMINAL_BASES
                break
            base, own = found
            fields |= own
            name = base
        else:
            # The loop ended without break: either the chain reached a class declared
            # with no base (name is None — a valid terminal), or it returned to a class
            # already visited. An inheritance cycle cannot be verified — incomplete.
            if name:
                complete = False
        return fields, asm, complete
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".",
                    help="mod repository root (default: CWD). All source paths resolve under it.")
    ap.add_argument("--engine-root", default=None,
                    help="engine checkout holding OpenRA.Mods.AS/Common/Cnc/D2k "
                         "(default: <root>/engine). For worktrees without their own engine/.")
    ap.add_argument("--json")
    args = ap.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    engine_root = (pathlib.Path(args.engine_root).resolve() if args.engine_root
                   else root / "engine")

    # Pre-scan schema gate: with any assembly source missing the field sets are partial,
    # the audit under-reports and still says OK — the exact failure mode it exists to
    # prevent (docs/audit/SUMMARY.md). Fail BEFORE scanning, and before --json could
    # overwrite anything with data that was never scanned. An unreadable source file
    # counts the same: a partially readable directory must not fabricate a schema.
    try:
        missing = missing_assemblies(root, engine_root)
        index = build_index(root, engine_root)
    except OSError as exc:
        print(f"INCOMPLETE — could not read the C# sources under {root}: {exc}")
        if args.json:
            print(f"--json {args.json} NOT written (no scan performed).")
        return EXIT_INCOMPLETE
    if missing:
        print("INCOMPLETE — assembly C# sources missing, the field schema cannot be trusted:")
        for name, d in missing:
            print(f"    {name}: {d} (no *.cs found)")
        print("Point --engine-root at an engine checkout (one containing "
              "OpenRA.Mods.Common et al) or run from a tree that has engine/ built.")
        if args.json:
            print(f"--json {args.json} NOT written (no scan performed).")
        return EXIT_INCOMPLETE
    try:
        rs = Model(root).rs
    except Exception as exc:  # any model failure is a pre-scan failure, not a clean scan
        print(f"INCOMPLETE — could not load the ruleset under {root}: {exc}")
        if args.json:
            print(f"--json {args.json} NOT written (no scan performed).")
        return EXIT_INCOMPLETE

    dead: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    unresolved: collections.Counter = collections.Counter()
    broken_chains: collections.Counter = collections.Counter()
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
            fields, _asm, complete = got
            if not complete:
                broken_chains[wtype] += 1
                continue
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
    if broken_chains:
        print("⚠ warhead types whose inheritance chain breaks at an unknown base, a cycle, "
              "or an unreadable base continuation — inherited fields may be missing "
              "(not checked):")
        for t, n in broken_chains.most_common():
            print(f"    {n:5d}  {t}")
        print()

    if unresolved or broken_chains:
        weapons_hit = len(set().union(*dead.values())) if dead else 0
        print(f"INCOMPLETE — {len(dead)} dead field kind(s) on {weapons_hit} weapons found so "
              "far, but the schema coverage above is partial: this is NOT a complete audit.")
        if dead:
            print("Dead fields found so far (raw diagnostics):")
            for (wtype, key), weapons in sorted(dead.items(), key=lambda kv: -len(kv[1])):
                print(f"  {len(weapons):5d} weapons   {wtype}.{key}")
        if args.json:
            print(f"--json {args.json} NOT written — incomplete scan "
                  f"({sum(unresolved.values())} unresolved, "
                  f"{sum(broken_chains.values())} broken-chain nodes); "
                  "any previous file is preserved.")
        return EXIT_INCOMPLETE

    # Complete, trustworthy scan: emit the CURRENT mapping (even empty) so a stale file
    # from an earlier run can never masquerade as this run's result.
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(
            {f"{t}.{k}": sorted(v) for (t, k), v in dead.items()}, indent=1), encoding="utf-8")

    if not dead:
        print("OK — every warhead field is read by the type that declares it.")
        return EXIT_OK

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

    return EXIT_RATCHET if over else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
