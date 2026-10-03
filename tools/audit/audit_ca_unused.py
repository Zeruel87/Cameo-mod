#!/usr/bin/env python3
"""audit_ca_unused — vendored C# that Cameo never uses, and what CA uses it FOR.

UPSTREAM_MODS.md §2/§5 (2026-08-23): "86 of the 142 vendored CA trait types are unused … wiring
them into yaml is the scarce work." That number was never turned into a list. And "unused in
Cameo" is not "dead code": on 2026-09-27 `HuntCA` looked dead only because its CALLER, the Lua
binding `Scripting/CombatCAProperties.cs`, had never been copied. CA used it for campaign
attack waves. So for every unused type this audit asks upstream CA where it is used, which
is the purpose Cameo would implement.

Scope: every yaml-visible type declared in OpenRA.Mods.CA and OpenRA.Mods.Cameo:
  trait / projectile  class FooInfo      -> yaml key `Foo` (`Foo@x`)  or `Projectile: Foo`
  warhead             class FooWarhead   -> `Warhead@x: Foo`
  widget              class FooWidget    -> chrome `Foo@x:`
  logic               class FooLogic     -> chrome `Logic: Foo`
  activity / helper   (no yaml name)     -> referenced from any other C# file (`new Foo(`, `Foo.`)
Scripting properties are skipped: the engine attaches them automatically.

Cameo usage = any yaml under mods/ (rules, maps, chrome, ContentPacks); C# references for
activities. CA usage = the same, in the FULL CAmod clone at origin/HEAD (mods/ca/**), plus Lua.

INFORMATIONAL: never fails. Which unused mechanics to wire is a maintainer decision.
    CA_ROOT=~/Documents/GitHub/CAmod python tools/audit/audit_ca_unused.py [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[2]
CODE = ["OpenRA.Mods.CA", "OpenRA.Mods.Cameo"]
CANDIDATES = [os.environ.get("CA_ROOT"), str(REPO.parent / "CAmod"),
              str(pathlib.Path.home() / "Documents" / "GitHub" / "CAmod")]

CLASS = re.compile(r"^\s*(?:(?:public|internal|sealed|abstract|static|partial)\s+)*class\s+(\w+)\s*(?::\s*([^{\n]+))?", re.M)


def git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def find_ca() -> pathlib.Path | None:
    for c in CANDIDATES:
        if c and (pathlib.Path(c).expanduser() / ".git").exists():
            return pathlib.Path(c).expanduser()
    return None


def classify(name: str, bases: str, path: str) -> tuple[str, str] | None:
    """(kind, yaml-visible name) or None for classes nobody names from yaml or code."""
    if "/Scripting/" in path or name.endswith("Properties") or name.endswith("Global"):
        return None
    if name.endswith("Warhead"):
        return "warhead", name[:-len("Warhead")]
    if name.endswith("Info") and bases and ("Info" in bases or "IProjectileInfo" in bases):
        return ("projectile" if "IProjectileInfo" in bases else "trait"), name[:-4]
    if name.endswith("Widget") and bases and "Widget" in bases:
        return "widget", name[:-len("Widget")]
    if name.endswith("Logic") and bases and "Logic" in bases:
        return "logic", name[:-len("Logic")]
    if "/Activities/" in path:
        return "activity", name
    return None


class Usage:
    """Where names occur in one mod tree: yaml trait keys, projectile/warhead/logic values,
    chrome widget keys, and free text (Lua, C#) for code-only classes."""

    def __init__(self, yaml_texts: list[tuple[str, str]], code_texts: list[tuple[str, str]]):
        self.keys = defaultdict(list)    # trait / widget key -> files
        self.values = defaultdict(list)  # Projectile / Warhead / Logic value -> files
        self.code = code_texts
        for path, text in yaml_texts:
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or ":" not in stripped:
                    continue
                key, _, value = stripped.partition(":")
                base = key.lstrip("-").split("@", 1)[0].strip()
                self.keys[base].append(path)
                value = value.strip()
                if value and (base in ("Projectile", "Logic") or base.startswith("Warhead")):
                    for v in value.split(","):
                        self.values[v.strip()].append(path)

    def uses(self, kind: str, name: str, own_file: str = "") -> list[str]:
        if kind in ("trait", "widget"):
            return self.keys.get(name, [])
        if kind in ("projectile", "warhead", "logic"):
            return self.values.get(name, [])
        pattern = re.compile(rf"\b{re.escape(name)}\b")
        return [p for p, t in self.code if p != own_file and pattern.search(t)]


def cameo_trees() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    yaml = [(str(p.relative_to(REPO)), p.read_text(encoding="utf-8", errors="replace"))
            for p in (REPO / "mods").rglob("*.yaml")]
    lua = [(str(p.relative_to(REPO)), p.read_text(encoding="utf-8", errors="replace"))
           for p in (REPO / "mods").rglob("*.lua")]
    cs = [(str(p.relative_to(REPO)).replace("\\", "/"), p.read_text(encoding="utf-8", errors="replace"))
          for d in CODE for p in (REPO / d).rglob("*.cs") if "obj" not in p.parts]
    return yaml, lua + cs


def ca_trees(ca: pathlib.Path) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    files = git(ca, "ls-tree", "-r", "--name-only", "origin/HEAD").splitlines()
    want = [f for f in files if (f.startswith("mods/") and f.endswith((".yaml", ".lua")))
            or (f.startswith("OpenRA.Mods.CA/") and f.endswith(".cs"))]
    raw = subprocess.run(["git", "-C", str(ca), "cat-file", "--batch"],
                         input=("\n".join(f"origin/HEAD:{f}" for f in want) + "\n").encode("utf-8"),
                         capture_output=True, check=True).stdout
    yaml, code, pos = [], [], 0
    for f in want:
        nl = raw.index(b"\n", pos)
        header = raw[pos:nl].split()
        pos = nl + 1
        if len(header) < 3 or header[-1] == b"missing":
            continue
        size = int(header[2])
        text = raw[pos:pos + size].decode("utf-8", errors="replace")
        pos += size + 1
        (yaml if f.endswith(".yaml") else code).append((f, text))
    return yaml, code


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--examples", type=int, default=3)
    args, _unknown = parser.parse_known_args()  # run_all.sh forwards its own flags

    print("# audit_ca_unused: vendored C# Cameo never uses, and what CA uses it for\n")
    types = []
    for d in CODE:
        for p in (REPO / d).rglob("*.cs"):
            if "obj" in p.parts:
                continue
            rel = str(p.relative_to(REPO)).replace("\\", "/")
            for name, bases in CLASS.findall(p.read_text(encoding="utf-8", errors="replace")):
                c = classify(name, bases, rel)
                if c:
                    types.append((c[0], c[1], rel))

    cameo = Usage(*cameo_trees())
    ca = find_ca()
    ca_usage = Usage(*ca_trees(ca)) if ca and git(ca, "rev-parse", "--is-shallow-repository").strip() == "false" else None
    if ca_usage is None:
        print("_no FULL CA clone found (CA_ROOT)_: the CA-usage column is empty. NOT a complete result.\n")

    rows = []
    for kind, name, path in sorted(set(types)):
        if cameo.uses(kind, name, path):
            continue
        ca_files = ca_usage.uses(kind, name, path.replace("OpenRA.Mods.Cameo/", "OpenRA.Mods.CA/")) if ca_usage else []
        rows.append({"kind": kind, "name": name, "file": path, "ca_uses": len(ca_files),
                     "ca_examples": sorted(set(ca_files))[:args.examples]})

    by_kind = defaultdict(lambda: [0, 0])
    for kind, _, _ in set(types):
        by_kind[kind][0] += 1
    for r in rows:
        by_kind[r["kind"]][1] += 1
    print("| kind | declared | unused in Cameo | of those, used by CA |\n|---|--:|--:|--:|")
    for kind, (declared, unused) in sorted(by_kind.items()):
        used_ca = sum(1 for r in rows if r["kind"] == kind and r["ca_uses"])
        print(f"| {kind} | {declared} | {unused} | {used_ca} |")

    print("\n## Unused here, USED by CA: the purpose to implement (most-used first)\n")
    for r in sorted((r for r in rows if r["ca_uses"]), key=lambda r: (-r["ca_uses"], r["name"])):
        print(f"- **{r['name']}** ({r['kind']}, `{r['file']}`): CA uses it {r['ca_uses']}x, e.g. "
              + ", ".join(f"`{e}`" for e in r["ca_examples"]))

    print("\n## Unused here AND in CA (truly dead, or a Cameo-only file never wired)\n")
    for r in sorted((r for r in rows if not r["ca_uses"]), key=lambda r: r["name"]):
        print(f"- {r['name']} ({r['kind']}, `{r['file']}`)")

    print("\n_Informational: never fails. Which mechanics to wire is a maintainer decision "
          "(UPSTREAM_MODS.md §5). Unused ≠ dead: check the CA column before deleting anything._")
    if args.json:
        args.json.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
