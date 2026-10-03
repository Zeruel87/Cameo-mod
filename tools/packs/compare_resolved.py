#!/usr/bin/env python3
"""Compare two `utility.cmd cameo --resolved-rules <Actor>` dumps as CONTENT.

Moving AI rows into a ContentPack reorders dictionary keys (packs merge first;
AI_ARCHITECTURE.md §1.2 ordering caveat), so a byte diff always differs. This compares
keys and values recursively with siblings sorted, which is what the bot modules consume.
Exit 0 = identical content, 1 = different (the differences are printed).
Usage: compare_resolved.py before.txt after.txt
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
import miniyaml  # noqa: E402


def canon(nodes, path=""):
    out = {}
    for n in nodes:
        k = f"{path}/{n.key}"
        out[k] = n.value or ""
        out.update(canon(n.children, k))
    return out


def load(p):
    text = pathlib.Path(p).read_text(encoding="utf-8", errors="replace")
    # the utility prints log lines before the yaml; keep from the first top-level key on
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l and not l.startswith(("\t", " ")) and l.rstrip().endswith(":")), 0)
    return canon(miniyaml.load_text("\n".join(lines[start:]), p))


a, b = load(sys.argv[1]), load(sys.argv[2])
only_a = sorted(set(a) - set(b))
only_b = sorted(set(b) - set(a))
changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
print(f"keys: before={len(a)} after={len(b)}  only-before={len(only_a)} only-after={len(only_b)} changed={len(changed)}")
for title, ks in (("ONLY BEFORE", only_a), ("ONLY AFTER", only_b), ("CHANGED", changed)):
    for k in ks[:15]:
        print(f"  {title}: {k} = {a.get(k, b.get(k))!r}")
sys.exit(0 if not (only_a or only_b or changed) else 1)
