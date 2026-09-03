#!/usr/bin/env python3
"""audit_duplicate_keys.py — duplicate keys inside one node (ambiguous merges).

MiniYaml does NOT generally reject a key that appears twice in the same node.
Ordinary duplicates merge the second node over the first, and the merged value is
``overrideNodes.Value ?? existingNodes.Value``. The LAST scalar value wins silently
and neither static loading nor the boot gate complains. Inheritance directives are
handled specially as described below.

Two severities:

D1 — duplicate ``Inherits``/``Inherits@X`` labels with DIFFERENT values.
    OpenRA resolves every inheritance directive that survives source merging, so
    repeated labels inside one definition do not by themselves drop a parent.
    They are still ambiguous for source overlays and audit tooling: merging another
    definition through the same label can replace one parent.  Fix by giving each
    inheritance directive a unique ``@suffix``.

D2 — every other duplicate key (same trait or field declared twice, or a
    duplicated ``Inherits`` with an identical value). The nodes merge, so the
    result is usually what the author wanted, but any field set by both copies
    resolves to the last one. Hygiene: collapse them into one node.

Exit code 1 when the D1 or D2 count rises above its baseline. The pre-existing
findings are ratchets, not a green light. Renaming a label is behavior-preserving
only when a resolved before/after comparison confirms it; otherwise the case needs
individual review. Lower each baseline as findings are fixed; never raise them.

Usage: python tools/audit/audit_duplicate_keys.py
"""

from __future__ import annotations

import collections
import pathlib
import sys

from miniyaml import Node, find_repo_root, load
from report import h1, h2, relpath, table

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Directories whose yaml the engine loads as rules/weapons/sequences/audio.
SCAN_DIRS = ("mods/cameo",)
SKIP_PARTS = ("maps", "bits")

# Ratchets: lower them as duplicates are resolved; never raise without a note.
D1_BASELINE = 35
D2_BASELINE = 260


def duplicate_children(node: Node) -> dict[str, list[Node]]:
    groups: dict[str, list[Node]] = collections.defaultdict(list)
    for child in node.children:
        if child.key and not child.key.startswith("-"):
            groups[child.key].append(child)
    return {k: v for k, v in groups.items() if len(v) > 1}


def walk(node: Node, path: str, out: list[tuple[str, str, list[Node]]]) -> None:
    for key, nodes in duplicate_children(node).items():
        out.append((path, key, nodes))
    for child in node.children:
        walk(child, f"{path} > {child.key}", out)


def main() -> int:
    root = find_repo_root()
    d1_rows: list[list[str]] = []
    d2_counts: collections.Counter[str] = collections.Counter()
    d2_rows: list[list[str]] = []

    files = []
    for scan in SCAN_DIRS:
        for path in sorted((root / scan).rglob("*.yaml")):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            files.append(path)

    for path in files:
        rel = relpath(str(path), root)
        try:
            doc = load(path)
        except Exception as exc:  # noqa: BLE001 — report, never abort the suite
            d2_rows.append([rel, "-", "load error", str(exc)])
            continue
        for top in doc:
            findings: list[tuple[str, str, list[Node]]] = []
            walk(top, top.key, findings)
            for owner, key, nodes in findings:
                lines = ", ".join(str(n.line) for n in nodes)
                values = [n.value for n in nodes]
                is_inherit = key == "Inherits" or key.startswith("Inherits@")
                if is_inherit and len(set(values)) > 1:
                    d1_rows.append([rel, lines, owner, key,
                                    " vs ".join(v or "(empty)" for v in values)])
                else:
                    d2_counts[key] += 1
                    d2_rows.append([rel, lines, owner, key])

    print(h1("audit_duplicate_keys — duplicate keys in one node (ambiguous merges)"))
    print(f"Files scanned: **{len(files)}** — D1 ambiguous inheritance labels: "
          f"**{len(d1_rows)}**, D2 merged duplicates: **{len(d2_rows)}**\n")

    print(h2("D1 — duplicate inheritance labels with different parent values"))
    print(table(["file", "lines", "node", "key", "values"], d1_rows))

    print(h2("D2 — duplicate keys by key name (top 40)"))
    print(table(["key", "occurrences"],
                [[k, str(c)] for k, c in d2_counts.most_common(40)]))

    print(h2("D2 — full list"))
    print(table(["file", "lines", "node", "key"], d2_rows))

    if len(d1_rows) > D1_BASELINE:
        print(f"\n**FAIL** — D1 count {len(d1_rows)} exceeds the baseline "
              f"{D1_BASELINE}: a new ambiguous inheritance label was introduced.\n")
        return 1

    if len(d1_rows) < D1_BASELINE:
        print(f"\nD1 count {len(d1_rows)} is below the baseline {D1_BASELINE} — "
              f"lower D1_BASELINE in this script to lock the fix in.\n")

    if len(d2_rows) > D2_BASELINE:
        print(f"\n**FAIL** — D2 count {len(d2_rows)} exceeds the baseline "
              f"{D2_BASELINE}: a new duplicate key was introduced.\n")
        return 1

    if len(d2_rows) < D2_BASELINE:
        print(f"\nD2 count {len(d2_rows)} is below the baseline {D2_BASELINE} — "
              f"lower D2_BASELINE in this script to lock the fix in.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
