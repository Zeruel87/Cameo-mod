"""Count actor ids written in the central mods/cameo/ai/ai.yaml: the §2.8 progress metric.

AI_ARCHITECTURE.md §2.8 moves faction ids out of the central file (dictionary rows into their
ContentPacks, lists into roles on actors). The metric is lower-only and ends at 0. An id counts
once per place it is written: as a node KEY (a dictionary row such as `UnitsToBuild`) or as an
entry of a comma-separated VALUE (a list such as `HarvesterTypes`). Actors are the resolved
ruleset's, so a dead id (its rules file not loaded) does not count; `--dead` lists those instead.

    python tools/ai/count_central_ids.py            # the count, split into rows and list entries
    python tools/ai/count_central_ids.py --max N    # exit 1 if the count rose above N
"""
from __future__ import annotations

import argparse
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "audit"))
import miniyaml  # noqa: E402

CENTRAL = REPO / "mods" / "cameo" / "ai" / "ai.yaml"


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.children)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--max", type=int, help="fail (exit 1) if the count is above this")
    ap.add_argument("--file", type=pathlib.Path, default=CENTRAL, help="ai.yaml to count (default: the central file)")
    ap.add_argument("--dead", action="store_true", help="list written tokens that look like ids but name no loaded actor")
    args = ap.parse_args()

    # exact case: a trait key such as `Refinery` must not match an actor id such as `refinery`
    actors = {k for k in miniyaml.Ruleset(REPO).actors if not k.startswith("^")}
    rows = entries = 0
    dead: set[str] = set()
    for n in walk(miniyaml.load(args.file)):
        key = n.key.split("@", 1)[0].lstrip("-")
        if key in actors:
            rows += 1
        if n.value and ("," in n.value or n.value.strip() in actors):
            for tok in (t.strip() for t in n.value.split(",")):
                if tok in actors:
                    entries += 1
                elif args.dead and tok and "_" in tok and " " not in tok:
                    dead.add(tok)

    total = rows + entries
    print(f"central ai.yaml actor ids: {total} ({rows} dictionary rows + {entries} list entries)")
    if args.dead:
        print(f"underscore tokens naming no loaded actor ({len(dead)}; faction ids such as td_gdi are expected here): "
              f"{', '.join(sorted(dead))}")
    if args.max is not None and total > args.max:
        print(f"FAIL: {total} > --max {args.max} (the metric is lower-only)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
