#!/usr/bin/env python3
"""audit_ai_frankenstein — guard the RV x CA x Cameo merges inside Cameo's CA bot modules.

Cameo's bot modules are a deliberate "Frankenstein": CA's modules (OpenRA.Mods.CA/Traits/BotModules)
with RV-engine features merged in (the guerrilla squads from engine Common's GuerrillaStates) plus
Cameo's own phases (master module, fog, risk gate, routing, artillery). A CA upstream sync
(tools/audit/audit_ca_drift.py) must never silently delete any of that.

This audit lists every symbol DECLARED in Cameo's CA bot files (classes, enums and enum values,
fields, properties, methods) that upstream CA does NOT have (neither the file's upstream base
version nor CA HEAD), and says where it came from:

  RV       the name is also declared in the RV engine's bot code (engine/OpenRA.Mods.Common or
           engine/OpenRA.Mods.AS BotModules): merged in on purpose from RV
  CAMEO    Cameo's own addition

`--write` records the current set as the protected manifest
(tools/audit/ai_frankenstein_manifest.json). Without it, the audit FAILS (exit 1) when a
protected symbol is gone from its file, which is how a sync that dropped RV or Cameo behaviour is
caught before review. Removing one on purpose = run with --write in the same commit and say
why in the message.

Regex-level parsing: it finds declarations, not semantics. A symbol that survives but no longer
does anything is NOT caught here; that is what the behaviour checks in the sync runbook are for
(docs/design/AI_SYNTHESIS.md §3).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BOT_DIR = "OpenRA.Mods.CA/Traits/BotModules/"
MANIFEST = REPO / "tools" / "audit" / "ai_frankenstein_manifest.json"
DEFAULT_CA = pathlib.Path.home() / "Documents" / "GitHub" / "CAmod"
RV_DIRS = [REPO / "engine" / "OpenRA.Mods.Common" / "Traits" / "BotModules",
           REPO / "engine" / "OpenRA.Mods.AS" / "Traits" / "BotModules"]

# A generic method (`PreferSquadTargets<T>(...)`) carries its type parameters after the name.
# Types may be declared with NO modifier (`class GroundUnitsIdleStateCA : ...` is internal).
TYPE_DECL = re.compile(r"^\s*(?:\[[^\]]*\]\s*)*(?:(?:public|internal|protected|private|static|sealed|abstract|partial)\s+)*"
                       r"(?:class|enum|interface|struct)\s+(?P<type>\w+)")
DECL = re.compile(
    r"^\s*(?:\[[^\]]*\]\s*)*"
    r"(?:(?:public|internal|protected|private|static|readonly|sealed|abstract|virtual|override|partial|const)\s+)+"
    r"(?:(?:class|enum|interface|struct)\s+(?P<type>\w+)"
    r"|[\w<>\[\],\.\? ]+?\s+(?P<member>\w+)\s*(?:<[\w, ]+>\s*)?(?:[=;({]|=>))")
ENUM_BLOCK = re.compile(r"enum\s+(\w+)\s*\{([^}]*)\}", re.S)


def symbols(text: str) -> set[str]:
    found = set()
    for line in text.splitlines():
        t = TYPE_DECL.match(line)
        if t:
            found.add(t.group("type"))
            continue
        m = DECL.match(line)
        if m:
            found.add(m.group("type") or m.group("member"))
    for enum, body in ENUM_BLOCK.findall(text):
        for item in body.split(","):
            name = item.split("=")[0].strip()
            name = re.sub(r"//.*", "", name).strip()
            if re.fullmatch(r"\w+", name or ""):
                found.add(f"{enum}.{name}")
    return found


def git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def upstream_symbols(ca: pathlib.Path, path: str) -> set[str]:
    """Union over EVERY upstream version of the path: a symbol CA ever had is not ours."""
    found: set[str] = set()
    blobs = {line.split()[3] for line in git(ca, "log", "origin/HEAD", "--raw", "--no-abbrev", "--no-renames",
                                                 "--format=", "--", path).splitlines() if line.startswith(":")}
    for blob in blobs:
        if set(blob) != {"0"}:
            found |= symbols(git(ca, "cat-file", "-p", blob))
    return found


def rv_symbols() -> set[str]:
    found: set[str] = set()
    for d in RV_DIRS:
        for p in d.rglob("*.cs"):
            found |= symbols(p.read_text(encoding="utf-8", errors="replace"))
    return found


def main() -> int:
    # Windows consoles default to cp1252; report text contains non-Latin-1 marks.
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--ca", type=pathlib.Path, default=DEFAULT_CA)
    parser.add_argument("--write", action="store_true", help="record the current set as the manifest")
    args, _unknown = parser.parse_known_args()  # run_all.sh forwards its own flags

    current: dict[str, dict[str, str]] = {}
    files = [p for p in git(REPO, "ls-files", BOT_DIR).splitlines() if p.endswith(".cs")]

    if args.write:
        if not (args.ca / ".git").exists() or git(args.ca, "rev-parse", "--is-shallow-repository").strip() == "true":
            print("--write needs a FULL CAmod clone (git fetch --unshallow)")
            return 2
        if not RV_DIRS[0].is_dir():
            print("--write needs engine/ (run make.cmd all): RV origin is read from engine sources")
            return 2
        rv = rv_symbols()
        for path in files:
            ours = symbols((REPO / path).read_text(encoding="utf-8", errors="replace"))
            added = ours - upstream_symbols(args.ca, path)
            if added:
                current[path] = {s: ("RV" if s.split(".")[-1] in rv or s in rv else "CAMEO") for s in sorted(added)}
        MANIFEST.write_text(json.dumps(current, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        n = sum(len(v) for v in current.values())
        n_rv = sum(1 for v in current.values() for o in v.values() if o == "RV")
        print(f"wrote {MANIFEST.relative_to(REPO)}: {n} protected symbols in {len(current)} files ({n_rv} RV, {n - n_rv} CAMEO)")
        return 0

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing = []
    for path, syms in sorted(manifest.items()):
        file = REPO / path
        present = symbols(file.read_text(encoding="utf-8", errors="replace")) if file.exists() else set()
        for sym, origin in sorted(syms.items()):
            if sym not in present:
                missing.append(f"{origin:5} {path}: {sym}")

    total = sum(len(v) for v in manifest.values())
    print(f"# AI Frankenstein guard: {total} protected symbols in {len(manifest)} files\n")
    if missing:
        print(f"**FAIL**: {len(missing)} protected RV/Cameo symbol(s) are gone. A CA sync or refactor removed them.\n")
        for m in missing:
            print(f"- {m}")
        print("\nIf the removal is intentional: `--write` in the same commit and say why in the message.")
        return 1
    print("**PASS**: every RV-merged and Cameo-added symbol is still declared.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
