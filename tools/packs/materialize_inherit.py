#!/usr/bin/env python3
"""Materialize a cross-pack `Inherits`/`Inherits@x` edge: inline the donor node's
children into the consumer, then drop the foreign Inherits key.

WHY CONCATENATION, NOT MERGE (hard-won lesson, DEVELOPMENT_LOG 2026-10-01):
when the donor's own children carry `Inherits@x` template refs, a child-level
merge silently drops consumer `-Key:` removals that target keys which only
exist *after* the donor's inherits expand (measured: +82 phantom resolved keys
on AAGunBoatFlak). OpenRA resolves Inherits@/-Key:/re-adds in document order,
so emitting donor children verbatim followed by the consumer's children (minus
the foreign Inherits) replicates the original two-hop cascade inside one node.

The result keeps the donor's Inherits@x refs as refs — those are global
(^Warhead_* templates live in core-mounted files) and stay resolvable.

ALWAYS verify afterwards with a resolved dump diff, e.g.:
    utility.cmd cameo --resolved-weapons <NAME>   (before + after)
    python tools/packs/compare_resolved.py before.txt after.txt
Exit 0 only means the transform ran — not that behaviour was preserved.

Usage:
    materialize_inherit.py <consumer.yaml> <ConsumerKey> <donor.yaml> <DonorKey>
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
import miniyaml  # noqa: E402


def emit(node, depth=0):
    lines = ["\t" * depth + node.key + (f": {node.value}" if node.value else ":")]
    for c in node.children:
        lines += emit(c, depth + 1)
    return lines


def top_level(path, key):
    node = next((n for n in miniyaml.load(path) if n.key == key), None)
    if node is None:
        raise SystemExit(f"{key} not found at top level of {path}")
    return node


def replace_block(path, key, new_lines):
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l == key + ":")
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i] and not lines[i].startswith(("\t", " "))),
        len(lines),
    )
    lines[start:end] = new_lines
    pathlib.Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    consumer_file, consumer_key, donor_file, donor_key = sys.argv[1:5]
    consumer = top_level(consumer_file, consumer_key)
    donor = top_level(donor_file, donor_key)

    foreign = [c for c in consumer.children
               if (c.key == "Inherits" or c.key.startswith("Inherits@")) and c.value == donor_key]
    if not foreign:
        raise SystemExit(f"{consumer_key} does not inherit {donor_key} — nothing to do")

    remaining = [c for c in consumer.children
                 if not ((c.key == "Inherits" or c.key.startswith("Inherits@")) and c.value == donor_key)]
    out = [consumer_key + ":"]
    for c in donor.children:
        out += emit(c, 1)
    for c in remaining:
        out += emit(c, 1)
    replace_block(consumer_file, consumer_key, out)
    print(f"{consumer_key} <- {donor_key}: materialized {len(out)} lines into {consumer_file}")
    print("VERIFY: resolved-dump before/after must be 0 diffs (compare_resolved.py).")


if __name__ == "__main__":
    main()
