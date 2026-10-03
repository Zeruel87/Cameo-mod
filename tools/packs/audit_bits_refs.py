#!/usr/bin/env python3
"""Census every file under mods/cameo/bits against yaml references.

Three buckets per file (matched on whole basename, case-insensitive):
  live      -- basename appears in a yaml that is actually loaded
               (non-commented cameo|*.yaml in mod.yaml, or a file listed by
               an Include'd ContentPack content.yaml)
  dormant   -- basename appears only in yamls that are commented out /
               not mounted (legacy monoliths kept for reference)
  unref     -- basename appears in NO yaml at all

CAUTION: `unref` is NOT "safe to delete". The engine hardcodes some names
(noicon.shp, mouse*, shadow.shp...), Lua maps can spawn assets by string,
and tileset .yaml under `tilesets/` reference .pal/.shp frames. This report
is evidence for a cleanup decision, not a deletion list.

Usage: python tools/packs/audit_bits_refs.py [--out docs/migration/bits_refs.json]
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "mods" / "cameo"
FILE_TOKEN = re.compile(r"[A-Za-z0-9_][\w.\-]*\.[a-z0-9]{2,5}", re.IGNORECASE)


def live_yaml_paths():
    live = set()
    my = (MOD / "mod.yaml").read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"^\s*cameo\|(\S+\.ya?ml)", my, re.M):
        live.add(MOD / m.group(1))
    for m in re.finditer(r"^\s*Include:\s*(\S+)", my, re.M):
        cy = MOD / m.group(1)
        live.add(cy)
        if cy.exists():
            txt = cy.read_text(encoding="utf-8", errors="replace")
            for mm in re.finditer(r"^\s*cameo\|(\S+\.ya?ml)", txt, re.M):
                live.add(MOD / mm.group(1))
    return {p for p in live if p.exists()}


def tokens_of(paths):
    toks = set()
    for p in paths:
        txt = p.read_text(encoding="utf-8", errors="replace")
        toks.update(t.lower() for t in FILE_TOKEN.findall(txt))
    return toks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    live = live_yaml_paths()
    all_yaml = {p for p in MOD.rglob("*.yaml")}
    dormant = all_yaml - live
    # also .yaml spelled .yml, and fluent/ftl files carry no file refs
    live_toks = tokens_of(live)
    dorm_toks = tokens_of(dormant) - live_toks

    rows = {"live": [], "dormant": [], "unref": []}
    for f in sorted((MOD / "bits").rglob("*")):
        if not f.is_file():
            continue
        rel = str(f.relative_to(MOD)).replace("\\", "/")
        n = f.name.lower()
        if n in live_toks:
            rows["live"].append(rel)
        elif n in dorm_toks:
            rows["dormant"].append(rel)
        else:
            rows["unref"].append(rel)

    # per-directory rollup for readability (bits root vs theme dirs)
    def rollup(lst):
        from collections import Counter
        return dict(Counter(str(Path(r).parent).replace("\\", "/")
                            for r in lst).most_common())

    out = {
        "live_yaml_files": len(live),
        "dormant_yaml_files": len(dormant),
        "bits_files": sum(len(v) for v in rows.values()),
        "live": len(rows["live"]),
        "dormant": len(rows["dormant"]),
        "unref": len(rows["unref"]),
        "live_by_dir": rollup(rows["live"]),
        "dormant_by_dir": rollup(rows["dormant"]),
        "unref_by_dir": rollup(rows["unref"]),
        "unref_files": rows["unref"],
    }
    print(f"bits={out['bits_files']} live={out['live']} "
          f"dormant={out['dormant']} unref={out['unref']}")
    print("unref_by_dir:", json.dumps(out["unref_by_dir"], indent=1)[:4000])
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n",
                               encoding="utf-8")


if __name__ == "__main__":
    main()
