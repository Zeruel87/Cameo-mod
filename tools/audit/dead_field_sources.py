"""Map each audit_dead_warhead_fields finding to its SOURCE line and classify
the correct fix shape.

The dead-field audit tells you WHICH weapons carry a discarded field, but not
WHERE the field is written — and the right fix differs:

    SAFE-DELETE    the source line may be deleted: every consumer of that node
                   resolves it to a class that lacks the field (dead or absent
                   everywhere). Applies to supplier-template lines AND to local
                   dead lines whose weapon has no live retyped children.

    RETYPE-CANCEL  the field is dead on this weapon but LIVE on siblings: the
                   weapon (or an ancestor) retypes the node to a class lacking
                   the field while other consumers keep a type that uses it.
                   Fix = `-Field:` cancel on the retyping def, never a source
                   delete (that would strip live data from the siblings).

    DEFER          the dead line is written locally on a weapon whose children
                   retype the node back to a class that HAS the field. Neither
                   delete nor cancel helps (both propagate to children); the
                   topology needs restructuring — design decision, not a
                   mechanical edit.

Usage:
    python tools/audit/dead_field_sources.py [--engine-root PATH] [--json OUT]

Requires the same engine sources as audit_dead_warhead_fields (same
--engine-root convention). Exit 0 always — this is a diagnostic, not a gate.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "balance"))

import audit_dead_warhead_fields as adwf
from cameo_model import Model


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--engine-root", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    engine_root = (pathlib.Path(args.engine_root).resolve() if args.engine_root
                   else root / "engine")
    index = adwf.build_index(root, engine_root)
    missing = adwf.missing_assemblies(root, engine_root)
    if missing:
        print("INCOMPLETE — assembly sources missing:", ", ".join(n for n, _ in missing))
        return adwf.EXIT_INCOMPLETE
    rs = Model(root).rs

    resolved: dict[str, object] = {}
    for w in rs.weapons:
        if w.startswith("^"):
            continue
        n = rs.resolve_weapon(w)
        if n is not None:
            resolved[w] = n

    # dead[(type,field)] = {weapons} — same scan as audit_dead_warhead_fields.
    dead: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for name, node in resolved.items():
        for wh in node.children:
            if not wh.key.startswith("Warhead") or not (wh.value or "").strip():
                continue
            got = adwf.resolve_fields(index, wh.value.strip() + "Warhead")
            if got is None or not got[2]:
                continue
            for c in wh.children:
                key = c.key.split("@")[0].strip()
                if key and key not in got[0]:
                    dead[(wh.value.strip(), key)].add(name)

    # enclosing top-level def for each source line — a dead field sourced
    # inside the DEAD weapon's own def means live children inherit it:
    # DEFER (restructure). Sourced inside a `^` template or an ancestor the
    # dead weapon merely consumes: RETYPE-CANCEL on the dead weapons.
    import re
    def_spans: dict[str, list[tuple[int, int, str]]] = {}
    for p in rs.manifest.weapons:
        p = pathlib.Path(p)
        spans = []
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        heads = [i for i, l in enumerate(lines, 1)
                 if re.match(r"^[\w^][\w^]*:", l)]
        for i, h in enumerate(heads):
            end = heads[i + 1] - 1 if i + 1 < len(heads) else len(lines)
            spans.append((h, end, lines[h - 1].split(":")[0]))
        def_spans[str(p)] = spans

    def _norm(p: str) -> str:
        s = str(pathlib.PurePath(p).as_posix()).lower()
        i = s.find("mods/")
        return s[i:] if i >= 0 else s

    def enclosing_def(sfile: str, sline: int) -> str | None:
        key = _norm(sfile)
        for k, spans in def_spans.items():
            if _norm(k) != key:
                continue
            for h, e, name in spans:
                if h <= sline <= e:
                    return name
        return None

    # locate each dead field's source (file,line) and classify.
    sources: dict[tuple[str, int], dict] = {}
    for (wtype, field), wlist in dead.items():
        for wname in wlist:
            node = resolved[wname]
            for c in node.children:
                if not c.key.startswith("Warhead@") or c.value != wtype:
                    continue
                for f in c.children:
                    if f.key != field:
                        continue
                    s = sources.setdefault(
                        (str(f.file), int(f.line)),
                        {"node": c.key, "field": field, "wtype": wtype,
                         "dead": set(), "live": set()})
                    s["dead"].add(wname)

    for (sfile, sline), s in sorted(sources.items()):
        for w, n in resolved.items():
            for c in n.children:
                if c.key != s["node"]:
                    continue
                for f in c.children:
                    # consumers carry the field declared AT THIS EXACT LINE —
                    # file-only matching is wrong (same file holds hundreds of
                    # defs; it once inflated :2854's "consumers" to 585).
                    if f.key == s["field"] and str(f.file) == sfile \
                            and int(f.line) == sline:
                        got = adwf.resolve_fields(index, (c.value or "") + "Warhead")
                        if got is None or not got[2]:
                            # unverifiable consumer — treat as live (conservative)
                            if w not in s["dead"]:
                                s["live"].add(w + "?")
                        elif s["field"] in got[0]:
                            s["live"].add(w)
                        break

    report = []
    for (sfile, sline), s in sorted(sources.items()):
        if not s["live"]:
            shape = "SAFE-DELETE"
        else:
            enc = enclosing_def(sfile, sline)
            shape = ("DEFER(live-children)" if enc in s["dead"]
                     else "RETYPE-CANCEL")
        report.append((sfile, sline, s["node"], s["field"], s["wtype"],
                       sorted(s["dead"]), sorted(s["live"]), shape))

    for sfile, sline, nodekey, field, wtype, dead_l, live_l, shape in report:
        print(f"{sfile}:{sline}  {nodekey}.{field} ({wtype})  "
              f"dead-on={len(dead_l)} live-on={len(live_l)}  {shape}")
        if live_l:
            print(f"      live: {', '.join(live_l[:10])}")
        if shape.startswith("RETYPE") or shape.startswith("DEFER"):
            print(f"      dead: {', '.join(dead_l[:10])}")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps([
            {"file": s, "line": l, "node": nk, "field": f, "type": t,
             "dead": dl, "live": ll, "shape": sh}
            for s, l, nk, f, t, dl, ll, sh in report], indent=1))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
