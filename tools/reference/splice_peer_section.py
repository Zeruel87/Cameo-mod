#!/usr/bin/env python3
"""splice_peer_section.py — refresh ONE source's section of the peer corpus, safely.

⛔ WHY THIS EXISTS. `extract_peer_units.py --mod <x>` does NOT update one section of
`docs/design/ORIGINAL_UNITS_PEER_OPENRA.md`; it REWRITES THE WHOLE FILE with only that mod's
rows. Running `--mod cnc` on a 2,583-row corpus leaves 57 rows and silently deletes the other
2,526 — six of the sixteen sources have no local checkout and can never be regenerated, so the
loss is permanent unless someone notices and reverts. CLAUDE.md rule 8 warns about the full-run
form of this; the `--mod` form does exactly the same thing, and it has now bitten twice.

This wraps the extractor so the destructive step is contained:

    1. snapshot the corpus,
    2. let the extractor clobber it,
    3. lift out just the requested source's section,
    4. restore the snapshot,
    5. substitute that one section, and
    6. REFUSE TO WRITE if any other source's row count moved.

Step 6 is the point. Everything before it is convenience; that check is what makes the operation
safe to run unattended.

    python tools/reference/splice_peer_section.py --mod cnc [--dry-run]
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs/design/ORIGINAL_UNITS_PEER_OPENRA.md"
EXTRACTOR = ROOT / "tools/reference/extract_peer_units.py"


def split_sections(text):
    """[(header_line, [body lines])] in file order, plus any preamble under the key None."""
    out, cur, body = [], None, []
    for line in text.splitlines():
        if line.startswith("## "):
            out.append((cur, body))
            cur, body = line, []
        else:
            body.append(line)
    out.append((cur, body))
    return out


def label_of(header):
    return header[3:].split("(")[0].strip() if header else None


def counts(text):
    return {label_of(h): sum(1 for line in b if line.startswith("| "))
            for h, b in split_sections(text) if h}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    before = CORPUS.read_text(encoding="utf-8")
    before_counts = counts(before)
    with tempfile.TemporaryDirectory() as td:
        backup = pathlib.Path(td) / "corpus.md"
        shutil.copy2(CORPUS, backup)
        try:
            r = subprocess.run([sys.executable, str(EXTRACTOR), "--mod", args.mod],
                               capture_output=True, text=True, cwd=ROOT)
            print(r.stdout.strip() or r.stderr.strip())
            if r.returncode != 0:
                print("extractor failed — corpus restored, nothing spliced")
                return 1
            produced = CORPUS.read_text(encoding="utf-8")
        finally:
            shutil.copy2(backup, CORPUS)   # the corpus is whole again no matter what happened

    fresh = [(h, b) for h, b in split_sections(produced) if h]
    if len(fresh) != 1:
        print(f"expected exactly one section from the extractor, got {len(fresh)}")
        return 1
    header, body = fresh[0]
    if any("⚠ not extracted" in line for line in body):
        print(f"source {label_of(header)!r} was not extracted; refusing to replace its existing "
              "corpus section with a missing-checkout placeholder")
        return 1
    label = label_of(header)
    if label not in before_counts:
        print(f"source {label!r} is not in the corpus; refusing to append a new section blindly")
        return 1

    rebuilt = []
    for h, b in split_sections(before):
        rebuilt.append((h, body if h and label_of(h) == label else b))
    text = "\n".join(("\n".join([h] + b) if h else "\n".join(b)) for h, b in rebuilt)
    if not text.endswith("\n"):
        text += "\n"

    after_counts = counts(text)
    moved = {k: (before_counts.get(k), after_counts.get(k))
             for k in set(before_counts) | set(after_counts)
             if k != label and before_counts.get(k) != after_counts.get(k)}
    if moved:
        print("REFUSING TO WRITE — sections other than the target changed:")
        for k, (a, b_) in sorted(moved.items()):
            print(f"   {k}: {a} -> {b_}")
        return 1

    print(f"{label}: {before_counts[label]} -> {after_counts[label]} rows; "
          f"{len(after_counts) - 1} other sections untouched")
    if args.dry_run:
        print("dry run, nothing written")
        return 0
    CORPUS.write_text(text, encoding="utf-8", newline="")
    print(f"wrote {CORPUS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
