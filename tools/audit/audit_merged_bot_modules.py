"""Merged bot modules stay current with their parents (DESIGN §19.3).

A merged module (e.g. `BaseRepairBotModule` = OpenRA `BuildingRepairBotModule` + CA
`BuildingRepairBotModuleCA`) is a SEPARATE file: an upstream fix to a parent lands in the parent's
copy (CA via `ca_vendor_sync.py`, OpenRA/AS via the engine pin) and never reaches the merge by itself.
The parents stay in the tree verbatim (`classic` runs the CA copies), so their content is the signal.

`merged_bot_modules.json` records, per merged module, each parent file and the hash of its content at
the time of the merge. When a parent's hash changes, this audit FAILS until someone ports the change
into the merged module (or rules it irrelevant) and re-baselines:

  python tools/audit/audit_merged_bot_modules.py            # check
  python tools/audit/audit_merged_bot_modules.py --write    # after porting: record today's parents

Hashes ignore line endings, so a checkout's CRLF/LF setting cannot trip it. A parent under `engine/`
is missing in a tree without a built engine: it is reported UNVERIFIED (the run says how many were
checked), never counted as a pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = REPO / "tools" / "audit" / "merged_bot_modules.json"


def content_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="record the current parent hashes (after porting)")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures, unverified, checked = [], [], 0
    for name, entry in manifest["merged"].items():
        merged = REPO / entry["file"]
        if not merged.is_file():
            failures.append(f"{name}: merged module file {entry['file']} is gone - update {MANIFEST.name}")
            continue
        for parent in entry["parents"]:
            path = REPO / parent["file"]
            if not path.is_file():
                unverified.append(f"{name}: parent {parent['file']} not in this tree (engine not built?)")
                continue
            now = content_hash(path)
            if args.write:
                parent["sha"] = now
            elif now != parent["sha"]:
                failures.append(f"{name}: parent {parent['file']} changed since the merge ({parent['sha']} -> {now}) - "
                                f"port the change into {entry['file']}, then run with --write")
            checked += 1

    if args.write:
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {MANIFEST.name}: {checked} parent hash(es) recorded")
        return 0 if not unverified else 1

    for u in unverified:
        print(f"UNVERIFIED: {u}")
    for f in failures:
        print(f"FAIL: {f}")
    total = sum(len(e["parents"]) for e in manifest["merged"].values())
    if failures:
        print(f"{len(failures)} merged module parent(s) changed - the merge is behind its parent")
        return 1
    print(f"PASS: {len(manifest['merged'])} merged module(s), {checked} of {total} parent file(s) verified unchanged"
          + (" - the rest UNVERIFIED" if unverified else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
