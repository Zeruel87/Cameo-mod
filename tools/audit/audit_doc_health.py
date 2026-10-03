#!/usr/bin/env python3
"""audit_doc_health.py — the documentation's own gate.

`audit_doc_claims.py` checks whether the NUMBERS in the docs still match the tree.
This checks whether the docs are structurally sound at all. Both classes of rot were
found by hand on 2026-08-23 and neither had a detector:

  D1 literal control characters in a tracked document — four of them (BEL, FF) sat in
     `BALANCE_PROGRAM_PLAN.md`'s W24 row, left by a `\\a` / `\\f` escape, and had turned
     `audit_physical_state_warheads` into `udit_physical_state_warheads` on screen.
  D2 mojibake — UTF-8 bytes once decoded as cp1252 and re-encoded, so an em dash reads
     as `â€"`. Two docs carried it, one of them a machine-read registry.
  D3 a markdown link pointing at a file that does not exist.
  D4 a same-file `](#anchor)` with no matching heading — silent in every renderer.
  D5 a reference to a document this repository moved or deleted.
  D6 two sections sharing one id in DESIGN.md. `§12.0a` named two different BINDING
     laws at once, and code cites `§12.0a` — so the citation was ambiguous.
  D7 a document with a `## Contents` index that does not list every one of its own `##`
     sections. LESSONS_LEARNED's index had drifted twice, most recently listing 15 of 31 —
     including neither of the two crash classes, in the one file whose entire job is
     "read this before you repeat a mistake".
  D8 a citation that names one law and points at another. Renumbering DESIGN
     sections moves the ids but not the ~800 §<id> references scattered through the
     documents and the audit scripts, and a repointed citation is INVISIBLE — it still
     renders, still looks authoritative, and now sends the reader to a different
     BINDING law. This happened for real: a renumber left `audit_versus_profile.py`
     PRINTING `§12.0a MEAN-100` into a generated report after §12.0a had become
     PLATFORM and MEAN-100 had moved to §12.0h. D6 cannot see it (no id is
     duplicated) and D3/D4 cannot see it (nothing is a link).

D1, D2 and D6 are BLOCKING: they are corruption or an ambiguous law. D3–D5 are
reported and also block, because a dead pointer is how a reader ends up in the wrong
document. D8 blocks for the same reason one level deeper: the pointer resolves, it
just resolves to the wrong law. Nothing here needs the engine, so it runs anywhere.

Exceptions live in ALLOW_MOJIBAKE / GONE below and are deliberately narrow — several
documents QUOTE mojibake while explaining the bug, and must not be "fixed".
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

# ⛔ THIS AUDIT WAS FAILING ON ITS OWN OUTPUT. Windows gives Python a cp1252 stdout, and
# `main()` printed a finding containing `→` — so the run died with UnicodeEncodeError at
# the D3 section, never printed D3 or D7, and exited 1. That 1 was read as "documentation is
# unhealthy" when it meant "the reporter crashed": the audit could not report a finding whose
# text contained an arrow, in a repository whose docs are full of arrows. Same class as the
# other guards that failed on the evidence they were built from.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Documents that legitimately contain mojibake because they document the bug class.
ALLOW_MOJIBAKE = {
    # Each of these QUOTES the mojibake it is describing — the `Kübelwagen` weapon-name
    # incident, where `ü` became `Ã¼` and the weapon reference silently stopped matching.
    # "Fixing" the quote would delete the evidence.
    "docs/LESSONS_LEARNED.md",
    "docs/design/ROADMAP.md",
    "docs/history/ROADMAP_ARCHIVE_2026-07.md",
    "docs/history/handoffs/AI_AGENT_HANDOFF_2026-07-25.md",
}

# Huge generated reference; its thousands of image links are a known separate issue.
SKIP_LINKS = {"docs/Cameo_Knowledge_Base_Manual.md"}

# Documents this repository moved or removed. A live reference to one is stale.
GONE = {
    "docs/AI_HANDOFF_2026-08-05.md": "docs/history/handoffs/AI_HANDOFF_2026-08-05.md",
    "docs/design/AREADAMAGE_HANDOFF.md": "docs/history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md",
    "docs/design/CLAUDE_HANDOFF_2026-08-11.md": "docs/history/handoffs/CLAUDE_HANDOFF_2026-08-11.md",
    "docs/design/DEVIN_REPLY_2026_08_11.md": "docs/history/handoffs/DEVIN_REPLY_2026-08-11.md",
    "docs/design/DEVIN_HANDOFF_SP_RESEARCH_2026_08_11.md": "docs/history/handoffs/DEVIN_HANDOFF_SP_RESEARCH_2026-08-11.md",
    "docs/design/SESSION_CHECKPOINT_2026-08-03.md": "docs/history/handoffs/SESSION_CHECKPOINT_2026-08-03.md",
    "docs/design/MEGAPLAN.md": "docs/history/MEGAPLAN_2026-08-08.md",
    "docs/history/AI_AGENT_HANDOFF.md": "docs/history/handoffs/AI_AGENT_HANDOFF_2026-07-25.md",
    "docs/balance/LESSONS_LEARNED.md": "docs/LESSONS_LEARNED.md",
}

CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
MOJIBAKE = re.compile("[ÂÃâ][-ÿ]{1,3}")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ANCHOR = re.compile(r"\]\(#([^)]+)\)")
HEADING = re.compile(r"^#{1,6} (.+)$", re.M)
DESIGN_ID = re.compile(r"^#{2,4} (\d+(?:\.\d+)?[a-z]?)\.? ", re.M)

DESIGN_HEADING = re.compile(r"^#{2,4} (\d+(?:\.\d+)?[a-z]?)\.? +(.+)$", re.M)

# D8. A citation is `§<id>` optionally followed by a LABEL — the law's name written out,
# as in "§12.0h THE MEAN-100 LAW". Only the label shape is checked, never free prose:
# a sentence that happens to mention another law near a citation is normal writing,
# while `§<id> NAME` is an assertion that <id> IS that law.
CITATION = re.compile(r"§(\d+(?:\.\d+)?[a-z]?)\b[.,:]?[ \t]*"
                      r"((?:(?:the|The|THE)[ \t]+)?[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*"
                      r"(?:[ \t]+[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)?)")

# Words too common to identify a section on their own.
D8_STOPWORDS = {
    "THE", "AND", "NOT", "JUST", "FOR", "ITS", "IS", "ARE", "WAS", "ALL", "ONE", "TWO",
    "LAW", "RULE", "RULES", "BINDING", "MAINTAINER", "DESIGN", "SECTION", "PHASE",
    "STEP", "OPTION", "NOTE", "SEE", "PER", "VIA", "WITH", "FROM", "THIS", "THAT",
    "ADDS", "A", "AN", "OF", "IN", "ON", "TO", "BY", "IT", "AS", "AT", "OR",
}


def design_sections(design: str) -> dict[str, str]:
    """id -> heading title, for every numbered DESIGN.md section."""
    return {m.group(1): m.group(2).strip() for m in DESIGN_HEADING.finditer(design)}


def distinctive_names(sections: dict[str, str]) -> dict[str, str]:
    """Word -> the single section id whose heading uses it.

    A word owned by two headings identifies neither, so it is dropped. This is what
    keeps D8 quiet: it fires only on a word that can mean exactly one section.
    """
    owners: dict[str, set[str]] = {}
    for sid, title in sections.items():
        for w in re.findall(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*", title):
            # A hyphenated heading word claims its PARTS as well as the compound.
            # Without this, `ARMOR-PLATING` (§12.0e) leaves the bare word `ARMOR`
            # looking unique to `HEROIC ARMOR` (§12.0b) — and "§12.0e ARMOR layer"
            # would be reported as naming the wrong law. Claiming both halves makes
            # the shared word ambiguous, which is exactly what silences it.
            for u in {w.upper(), *(part.upper() for part in w.split("-"))}:
                if len(u) < 4 or u in D8_STOPWORDS:
                    continue
                owners.setdefault(u, set()).add(sid)
    return {w: next(iter(ids)) for w, ids in owners.items() if len(ids) == 1}




def tracked(*globs: str) -> list[pathlib.Path]:
    out = subprocess.run(["git", "ls-files", *globs], cwd=ROOT,
                         capture_output=True, text=True).stdout.split("\n")
    return [pathlib.Path(p) for p in out if p]


def slug(heading: str) -> str:
    """GitHub's heading -> anchor transform, close enough for our headings."""
    s = heading.strip().lower().replace("`", "")
    s = re.sub(r"\*\*|\*|_", "", s)
    s = "".join(c for c in s if c.isalnum() or c in " -")
    return re.sub(r"\s", "-", s)


def read(path: pathlib.Path) -> str | None:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def main() -> int:
    docs = tracked("*.md")
    for extra in ("docs/HANDOFF.md", "docs/history/ROADMAP_ARCHIVE_2026-07.md"):
        p = pathlib.Path(extra)
        if (ROOT / p).exists() and p not in docs:
            docs.append(p)

    d1: list[str] = []
    d2: list[str] = []
    d3: list[str] = []
    d4: list[str] = []
    d5: list[str] = []
    d6: list[str] = []
    d7: list[str] = []
    d8: list[str] = []

    for f in docs:
        text = read(f)
        if text is None:
            d1.append(f"`{f}` — not valid UTF-8")
            continue
        rel = str(f).replace("\\", "/")

        for m in CTRL.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            d1.append(f"`{rel}`:{line} — control character {hex(ord(m.group()))}")

        if rel not in ALLOW_MOJIBAKE:
            hits = sorted(set(MOJIBAKE.findall(text)))
            if hits:
                d2.append(f"`{rel}` — {len(hits)} distinct sequence(s), e.g. {hits[:3]}")

        if rel not in SKIP_LINKS:
            for m in LINK.finditer(text):
                target = m.group(1).split("#")[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                if not (ROOT / f.parent / target).exists():
                    d3.append(f"`{rel}` → `{target}`")

            heads = {slug(m.group(1)) for m in HEADING.finditer(text)}
            for m in ANCHOR.finditer(text):
                if m.group(1) not in heads:
                    d4.append(f"`{rel}` → `#{m.group(1)}`")

    # D5 — a live document naming a path this repo moved. History keeps its own
    # period-correct references on purpose.
    for f in tracked("*.md", "*.py", "*.json", "*.yaml", "*.sh"):
        rel = str(f).replace("\\", "/")
        # history keeps its own period-correct references on purpose, and this
        # script's own GONE table names every old path by definition. Generated
        # audit reports are the same case: `docs/audit/latest/recent_changes.md`
        # REPORTS on commits, so it quotes the paths those commits touched —
        # naming a since-moved file there is a factual record, not a stale
        # pointer. A guard must not fail on the evidence it is built from.
        if (rel.startswith("docs/history/")
                or rel.startswith("docs/audit/latest/")
                or rel.startswith("docs/audit/degraded/")
                or rel == "tools/audit/audit_doc_health.py"):
            continue
        text = read(f)
        if text is None:
            continue
        for old, new in GONE.items():
            if old in text:
                d5.append(f"`{rel}` names `{old}` — moved to `{new}`")

    # D7 — a "## Contents" index must list every "##" section of its own document.
    for f in docs:
        text = read(f)
        if text is None or "\n## Contents" not in text:
            continue
        rel = str(f).replace("\\", "/")
        linked = set(ANCHOR.findall(text))
        for m in re.finditer(r"^## (.+)$", text, re.M):
            title = m.group(1).strip()
            if title in ("Contents", "Required reading order for every new task"):
                continue
            if slug(title) not in linked:
                d7.append(f"`{rel}` — Contents omits `{title}`")

    design = read(pathlib.Path("docs/DESIGN.md"))
    if design:
        ids = DESIGN_ID.findall(design)
        for i in sorted({i for i in ids if ids.count(i) > 1}):
            d6.append(f"`DESIGN.md` §{i} is used {ids.count(i)} times")

    # D8 — a citation that names one law and points at another.
    #
    # Only FINE-GRAINED ids are checked (`12.0h`, `11b`, `16.3` …). A bare `§12` is
    # ambiguous: half the design documents number their own sections, so `§2` in
    # EMP_INTEGRITY_SYSTEM.md means that document's §2, not DESIGN's. Sub-numbered ids
    # are also the ones that actually move when someone renumbers — which is the bug.
    if design:
        sections = design_sections(design)
        names = distinctive_names(sections)
        checkable = {i for i in sections if not i.isdigit()}
        for f in tracked("*.md", "*.py", "*.yaml", "*.sh", "*.json"):
            rel = str(f).replace("\\", "/")
            # tools/tests/ is excluded on purpose: the D8 unit tests assert on the exact
            # wrong-law label this check fires on ("## §12.0a MEAN-100"), so scanning them
            # makes the check report its own fixtures and D8 can never pass. Same class as
            # the D5 self-references — a guard must not fail on the evidence it is built from.
            if (rel.startswith("docs/history/") or rel.startswith("tools/tests/")
                    or rel == "tools/audit/audit_doc_health.py"):
                continue
            text = read(f)
            if text is None:
                continue
            for m in CITATION.finditer(text):
                sid, label = m.group(1), m.group(2)
                if sid not in checkable:
                    continue
                for word in re.findall(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*", label):
                    owner = names.get(word.upper())
                    if owner and owner != sid:
                        line = text.count("\n", 0, m.start()) + 1
                        d8.append(
                            f"`{rel}`:{line} — cites §{sid} ({sections[sid][:40]}) but "
                            f"names `{word}`, which is §{owner} ({sections[owner][:40]})")
                        break

    print("# audit_doc_health — is the documentation structurally sound?\n")
    print(f"Documents scanned: **{len(docs)}**\n")
    print("`audit_doc_claims.py` checks whether the NUMBERS are still true. "
          "This checks whether the documents themselves are intact.\n")
    print("| code | what | count |")
    print("|---|---|--:|")
    for code, what, rows in (
        ("D1", "literal control characters", d1),
        ("D2", "mojibake (UTF-8 read as cp1252)", d2),
        ("D3", "markdown link to a missing file", d3),
        ("D4", "same-file anchor with no heading", d4),
        ("D5", "reference to a moved/removed document", d5),
        ("D6", "duplicate section id in DESIGN.md", d6),
        ("D7", "Contents index missing a section", d7),
        ("D8", "citation names a different section's law", d8),
    ):
        print(f"| {code} | {what} | {len(rows)} |")

    findings = 0
    for code, what, rows in (
        ("D1", "Control characters", d1),
        ("D2", "Mojibake", d2),
        ("D3", "Broken links", d3),
        ("D4", "Broken anchors", d4),
        ("D5", "Stale document references", d5),
        ("D6", "Duplicate DESIGN section ids", d6),
        ("D7", "Contents index out of date", d7),
        ("D8", "Citation points at the wrong law", d8),
    ):
        print(f"\n\n## {code} — {what} ({len(rows)})\n")
        if rows:
            findings += len(rows)
            for r in sorted(set(rows)):
                print(f"- {r}")
        else:
            print("_clean_")

    print()
    if findings:
        print(f"\n**FAIL — {findings} finding(s).** Fix the document; none of these are "
              "cosmetic. D1/D2 are corruption, D6 makes a cited law ambiguous, "
              "D3–D5 send a reader to the wrong place, D7 means a document is "
              "hiding its own content from the person who was told to read it, and "
              "D8 means a citation resolves — to the wrong law.")
        return 1
    print("\n**PASS** — no structural defects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
