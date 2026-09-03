#!/usr/bin/env python3
"""Compact a whole-ruleset comparison while retaining deterministic fingerprints."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib


def digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    data = json.loads(args.source.read_text(encoding="utf-8"))
    kinds = collections.Counter()
    changed = {}
    percentage_rows = []
    kind_payloads = collections.defaultdict(dict)
    for weapon, changes in sorted(data["changed"].items()):
        names = []
        for change in changes:
            kind = change[0]
            names.append(kind)
            kinds[kind] += 1
            kind_payloads[kind][weapon] = change[1:]
            if kind == "percentage_damage":
                percentage_rows.extend(change[1])
        changed[weapon] = sorted(names)
    compact = {
        "source_digest": digest(data),
        "counts": {
            "changed": len(data["changed"]),
            "added": len(data["added"]),
            "removed": len(data["removed"]),
        },
        "added": data["added"],
        "removed": data["removed"],
        "change_kind_counts": dict(sorted(kinds.items())),
        "change_kind_digests": {
            kind: digest(payload) for kind, payload in sorted(kind_payloads.items())
        },
        "changed": changed,
        "percentage_rounding": {
            "row_count": len(percentage_rows),
            "max_absolute_delta": max(
                (abs(before - after) for _hp, before, after in percentage_rows),
                default=0),
            "digest": digest(percentage_rows),
        },
    }
    args.output.write_text(
        json.dumps(compact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({len(changed)} changed weapons)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
