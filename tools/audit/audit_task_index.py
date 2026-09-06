#!/usr/bin/env python3
"""audit_task_index.py — keep `docs/TASK_INDEX.md` honest.

THE POINT OF THE INDEX. Maintainer order 2026-09-06: *"every task must have a clear
reference to the docs, so when you start any task the correct document and the correct
section is automatically read, so you will never do duplicate work again that has already
been done."* The index routes a task to the document it must read and to the tools that
ALREADY EXIST for it.

⛔ WHY IT NEEDS A GUARD. An index of pointers rots faster than prose, and a rotted pointer
is worse than none: it sends the reader somewhere confidently wrong. Three real duplicates
preceded this file — a spec written for a resolver check that exists twice (`fit_class.py`,
`check_band.py`), a virtual-anchor mechanism re-designed when `fit_class.py --spec` already
implements it, and a whole session re-deriving a weapon-tier model DESIGN.md had shipped.

Checks, all cheap and all about the index pointing at real things:

  T1  every relative document link in the index resolves to a file
  T2  every `tools/...` path named in the index exists
  T3  every document the README lists as required reading is routed by the index
  T4  every task row names at least one document to read first

⚠ Link ANCHORS (`#section`) are deliberately NOT checked here — `audit_doc_health` D3/D4
already does exactly that for every document, and a second implementation of the same check
is the duplication this file exists to prevent.
"""

from __future__ import annotations

import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs" / "TASK_INDEX.md"
README = ROOT / "docs" / "README.md"

# Required reading, as `docs/README.md` defines it. The index must route every one of them —
# a document nobody is told to read is a document that gets re-derived.
REQUIRED_READING = [
    "LESSONS_LEARNED.md", "AGENT_WORKSPACE.md", "HANDOFF.md", "DESIGN.md",
    "design/ROADMAP.md",
]

LINK = re.compile(r"\[[^\]]+\]\(([^)#]+)(#[^)]*)?\)")
TOOL = re.compile(r"`(tools/[A-Za-z0-9_/]+\.(?:py|sh))`")
ROW = re.compile(r"^\|\s*\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")


def main() -> int:
    if not INDEX.exists():
        print(f"⛔ {INDEX.relative_to(ROOT)} is missing — the task routing table is the "
              f"maintainer's stated defence against duplicate work.")
        return 1

    text = INDEX.read_text(encoding="utf-8")
    findings: list[str] = []

    # T1 — document links resolve
    broken = [m.group(1) for m in LINK.finditer(text)
              if not (INDEX.parent / m.group(1)).resolve().exists()]

    # T2 — tool paths exist
    tools = sorted({m.group(1) for m in TOOL.finditer(text)})
    missing_tools = [t for t in tools if not (ROOT / t).exists()]

    # T3 — required reading is routed
    unrouted = [d for d in REQUIRED_READING if d.rsplit("/", 1)[-1] not in text]

    # T4 — every task row names a document to read
    rows = [m for m in (ROW.match(l) for l in text.splitlines()) if m]
    no_read = [m.group(1) for m in rows
               if m.group(1) not in ("task", "gate", "kind of statement")
               and not LINK.search(m.group(2)) and m.group(2).strip() not in ("—", "")]

    print("# audit_task_index — is the task routing table pointing at real things?\n")
    print(f"task rows          : **{len(rows)}**")
    print(f"documents linked   : **{len(list(LINK.finditer(text)))}**")
    print(f"tools referenced   : **{len(tools)}**\n")
    print(f"| check | finding |\n|---|--:|")
    print(f"| T1 broken document links | {len(broken)} |")
    print(f"| T2 tool paths that do not exist | {len(missing_tools)} |")
    print(f"| T3 required-reading documents not routed | {len(unrouted)} |")
    print(f"| T4 task rows with nothing to read first | {len(no_read)} |")

    for label, items, why in (
        ("T1 — broken document links", broken,
         "a pointer to a file that does not exist is worse than no pointer"),
        ("T2 — tools named that do not exist", missing_tools,
         "the ALREADY BUILT column is the duplicate-work defence; a wrong entry defeats it"),
        ("T3 — required reading not routed", unrouted,
         "README lists it as required; the index must say WHEN to read it"),
        ("T4 — task rows with no document", no_read,
         "a task with no reading is a task someone will re-derive"),
    ):
        if items:
            findings += items
            print(f"\n## {label}\n\n_{why}_\n")
            for i in items:
                print(f"- `{i}`")

    if findings:
        print(f"\n**FAIL — {len(findings)} finding(s).** Fix the index; it is the "
              f"maintainer's stated defence against repeating work already done.")
        return 1
    print("\n**PASS** — every route points at a document and a tool that exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
