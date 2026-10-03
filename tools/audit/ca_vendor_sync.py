#!/usr/bin/env python3
"""ca_vendor_sync — bring Cameo's hand-copied CA files up to upstream CA, safely.

Cameo's engine is the RV fork, so CA code arrives only by copying (see audit_ca_drift.py).
This tool does the copying, in the order of risk:

  STALE           (an old upstream copy, no Cameo edits)  -> replaced with upstream HEAD
  MODIFIED+STALE  (Cameo edits + upstream changes)        -> 3-way `git merge-file`
                   base = the upstream version Cameo started from, ours = Cameo, theirs = CA HEAD
                   clean merge -> written; conflict -> left untouched and listed (or written
                   with conflict markers under --write-conflicts, for a human to resolve)

⛔ Files that carry RV-merged or Cameo-added behaviour (tools/audit/ai_frankenstein_manifest.json,
i.e. the bot modules) are SKIPPED unless --include-frankenstein. Even a clean textual merge can
break merged behaviour, so those are synced deliberately, one reviewed PR at a time, with the
behaviour checks in docs/design/AI_SYNTHESIS.md §3. The Frankenstein guard runs after every
--apply either way.

Dry run by default (prints the plan). `--apply` writes files into THIS checkout; do it in a
worktree on a branch, then: C# build, the AI gates, boot to the menu, one PR.

    python tools/audit/ca_vendor_sync.py [--apply] [--only STALE|MERGE] [--path SUBSTR]
                                          [--include-frankenstein] [--write-conflicts]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
AUDIT = REPO / "tools" / "audit" / "audit_ca_drift.py"
GUARD = REPO / "tools" / "audit" / "audit_ai_frankenstein.py"
MANIFEST = REPO / "tools" / "audit" / "ai_frankenstein_manifest.json"
sys.path.insert(0, str(REPO / "tools" / "audit"))
import vector_codemod  # noqa: E402
DEFAULT_CA = pathlib.Path.home() / "Documents" / "GitHub" / "CAmod"


def git_bytes(repo: pathlib.Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def with_endings(text: bytes, like: bytes) -> bytes:
    """Keep the Cameo file's line-ending style so the diff shows content, not CRLF churn."""
    lf = text.replace(b"\r\n", b"\n")
    return lf.replace(b"\n", b"\r\n") if b"\r\n" in like else lf


INFO_FIELD = re.compile(r"^\s*public\s+(?:readonly\s+)?[\w<>\[\],\.\? ]+?\s+(\w+)\s*(?:=|;)", re.M)
INFO_CLASS = re.compile(r"class\s+(\w+Info)\b[^{]*\{(.*?)^\t\}", re.S | re.M)


def info_fields(text: str) -> set[tuple[str, str]]:
    """(InfoClass, field) pairs: the yaml-visible surface of every trait in a file."""
    return {(cls, f) for cls, body in INFO_CLASS.findall(text) for f in INFO_FIELD.findall(body)}


_yaml_pairs: set[tuple[str, str]] | None = None


def yaml_uses(info_class: str, field: str) -> bool:
    """Does any Cameo yaml set `field` on THIS trait (`Foo` / `Foo@x` for class FooInfo)?
    FieldLoader drops unknown keys SILENTLY (CLAUDE.md rule 8b), so a field a sync removes would
    lose its yaml value without any error. Scoped per trait: a key name alone (e.g.
    `Notification:`) matches dozens of unrelated traits."""
    global _yaml_pairs
    if _yaml_pairs is None:
        _yaml_pairs = set()
        for path in (REPO / "mods").rglob("*.yaml"):
            trait = None
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.lstrip("	")
                depth = len(line) - len(stripped)
                key = stripped.split(":", 1)[0].strip().lstrip("-")
                if not key or stripped.startswith("#"):
                    continue
                if depth == 1:
                    trait = key.split("@", 1)[0]
                elif depth == 2 and trait:
                    _yaml_pairs.add((trait, key))
                elif depth == 0:
                    trait = None
    trait = info_class[:-4] if info_class.endswith("Info") else info_class
    return (trait, field) in _yaml_pairs


def main() -> int:
    # Windows consoles default to cp1252; report text contains non-Latin-1 marks.
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--ca", type=pathlib.Path, default=DEFAULT_CA, help="FULL CAmod clone (default: CA_ROOT or ~/Documents/GitHub/CAmod)")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--only", choices=["STALE", "MERGE"])
    parser.add_argument("--path", help="only files whose path contains this")
    parser.add_argument("--include-frankenstein", action="store_true")
    parser.add_argument("--write-conflicts", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        report = pathlib.Path(tmp) / "drift.json"
        run = subprocess.run([sys.executable, str(AUDIT), "--ca", str(args.ca), "--json", str(report)],
                             capture_output=True, text=True)
        if run.returncode != 0 or not report.exists():
            print(run.stdout or run.stderr)
            return 2
        drift = json.loads(report.read_text(encoding="utf-8"))
    head = drift["ca_head"]
    # Upstream CA still says float2/float3; the engine (bleed, #569) does not. Convert what comes from
    # upstream so a STALE copy compiles and a 3-way merge compares like with like (Cameo's side is converted).
    vectors = vector_codemod.is_vector_engine(REPO)

    def upstream(data: bytes) -> bytes:
        return vector_codemod.convert(data.decode("utf-8")).encode("utf-8") if vectors else data

    protected = set(json.loads(MANIFEST.read_text(encoding="utf-8"))) if MANIFEST.exists() else set()

    plan = []
    for row in drift["rows"]:
        kind = {"STALE": "STALE", "MODIFIED+STALE": "MERGE"}.get(row["status"])
        if not kind or (args.only and kind != args.only) or (args.path and args.path not in row["path"]):
            continue
        skip = "frankenstein (RV/Cameo behaviour inside)" if row["path"] in protected and not args.include_frankenstein else ""
        plan.append((kind, row, skip))

    print(f"# CA vendor sync plan vs CAmod `{head[:9]}` ({'APPLY' if args.apply else 'dry run'})"
          f"{' - upstream converted to System.Numerics vectors' if vectors else ''}\n")
    results = {"synced": [], "merged": [], "conflict": [], "skipped": [], "field_loss": []}

    def check_fields(path: str, before: bytes, after: bytes) -> None:
        lost = info_fields(before.decode("utf-8", "replace")) - info_fields(after.decode("utf-8", "replace"))
        for cls, field in sorted(lost):
            if yaml_uses(cls, field):
                results["field_loss"].append(f"{path}: {cls}.{field} is set in Cameo yaml but gone after the sync")
    for kind, row, skip in plan:
        path = row["path"]
        if skip:
            results["skipped"].append(f"{path}: {skip}")
            continue
        ours_file = REPO / path
        ours = ours_file.read_bytes()
        theirs = upstream(git_bytes(args.ca, "show", f"{head}:{row.get('upstream_path') or path}"))
        if kind == "STALE":
            results["synced"].append(path)
            check_fields(path, ours, theirs)
            if args.apply:
                ours_file.write_bytes(with_endings(theirs, ours))
            continue

        base = upstream(git_bytes(args.ca, "cat-file", "-p", row["base_blob"]))
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            (t / "ours").write_bytes(ours.replace(b"\r\n", b"\n"))
            (t / "base").write_bytes(base.replace(b"\r\n", b"\n"))
            (t / "theirs").write_bytes(theirs.replace(b"\r\n", b"\n"))
            merge = subprocess.run(["git", "merge-file", "-p", "-L", "cameo", "-L", "ca-base", "-L", f"ca-{head[:9]}",
                                    str(t / "ours"), str(t / "base"), str(t / "theirs")], capture_output=True)
        merged = merge.stdout
        if merge.returncode == 0:
            results["merged"].append(path)
            check_fields(path, ours, merged)
            if args.apply:
                ours_file.write_bytes(with_endings(merged, ours))
        else:
            results["conflict"].append(f"{path}: {merge.returncode} conflict hunk(s)")
            if args.apply and args.write_conflicts:
                ours_file.write_bytes(with_endings(merged, ours))

    for key, title in (("synced", "STALE, replaced with upstream"), ("merged", "3-way merged cleanly"),
                       ("conflict", "3-way CONFLICTS, need a human"), ("skipped", "skipped"),
                       ("field_loss", "⛔ YAML FIELD LOSS: fix the yaml (or keep the field) BEFORE applying")):
        print(f"## {title} ({len(results[key])})\n")
        for item in results[key]:
            print(f"- `{item}`")
        print()

    if args.apply:
        guard = subprocess.run([sys.executable, str(GUARD)], capture_output=True, text=True)
        print(guard.stdout)
        print("Next: C# build, python tools/tests/ai_bot_player_gate.py, boot to the menu, one PR.")
        return guard.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
