#!/usr/bin/env python3
"""build_reference_report.py — the reference map as a reviewable HTML page.

⭐ ORIGINALS AND EXPANSIONS ARE TWO DIFFERENT REPORTS (maintainer, 2026-09-07). Mixing them is
what made the first page unreadable. An ORIGINAL exists in OpenRA/OpenTD, so a counterpart
provably exists in every source: all three references must be present and must be the same unit,
and every row is checkable against the original game. An EXPANSION exists only in Cameo, Combined
Arms or DTA; it cannot always have three references, and holding it to the same standard buries
the rows that are genuinely wrong among rows that never could be right.

The two bands are therefore separated, counted and captioned apart, so a review pass over the
originals is a finite, decidable job.

    python tools/balance/build_reference_report.py --faction td_gdi td_nod ra1_allies ra1_soviets
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import reference_distribution as rd          # noqa: E402
import reference_targets as rt               # noqa: E402

ROOT = rd.ROOT
ASSIGN = ROOT / "docs/balance/derived/reference_assignment.json"
ORIGINAL_SOURCES = ("OpenRA Red Alert", "OpenRA Tiberian Dawn",
                    "OpenRA Tiberian Sun", "Romanov's Vengeance")
SECTIONS = (("infantry", "Infantry"), ("vehicle", "Vehicles"), ("aircraft", "Aircraft"),
            ("ship", "Naval"), ("defense", "Defenses"))
CONF_ORDER = {"STRONG": 0, "FAIR": 1, "SHAPE": 2, "WEAK": 3}

STYLE = """
:root{--bg:#f7f6f3;--fg:#1b1a17;--mut:#6f6a60;--line:#ddd8cd;--card:#fffefb;--accent:#8a5a2b;
--strong:#1f6b4a;--fair:#7a6320;--shape:#4a5a78;--weak:#8a4a3c;--bad:#a3312a;--tgt:#2e5c8a;}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161513;--fg:#eae6dd;
--mut:#9b948a;--line:#33302a;--card:#1e1c19;--accent:#d8a56a;--strong:#5fbf8f;--fair:#c9a94a;
--shape:#8fa8cc;--weak:#d08a78;--bad:#e0736a;--tgt:#7fb0e0;}}
:root[data-theme=dark]{--bg:#161513;--fg:#eae6dd;--mut:#9b948a;--line:#33302a;--card:#1e1c19;
--accent:#d8a56a;--strong:#5fbf8f;--fair:#c9a94a;--shape:#8fa8cc;--weak:#d08a78;--bad:#e0736a;
--tgt:#7fb0e0;}
body{background:var(--bg);color:var(--fg);font:14px/1.5 ui-sans-serif,system-ui,sans-serif;
margin:0;padding:28px clamp(12px,4vw,56px);}
h1{font-size:1.6rem;margin:0 0 4px;letter-spacing:-.01em}
h2{margin:34px 0 6px;font-size:1.15rem;border-bottom:2px solid var(--line);padding-bottom:5px}
h2.band{border-bottom:none;color:var(--accent);font-size:.95rem;text-transform:uppercase;
letter-spacing:.1em;margin:26px 0 2px}
h3{margin:18px 0 6px;font-size:.8rem;text-transform:uppercase;letter-spacing:.09em;color:var(--mut)}
.muted{color:var(--mut);font-weight:400;text-transform:none;letter-spacing:0}
.lede{color:var(--mut);max-width:78ch;margin:0 0 10px}
.wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--line);
border-radius:7px;overflow:hidden;margin-bottom:6px}
th,td{padding:6px 9px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);font-weight:600}
tr:last-child td{border-bottom:none}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.t{color:var(--tgt);font-weight:600}
code{font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace}
.chip{display:inline-block;border:1px solid var(--line);border-radius:5px;padding:1px 6px;
margin:1px 3px 1px 0;font-size:12px;white-space:nowrap}
.chip i{font-style:normal;color:var(--mut)}
.chip.strong{border-left:3px solid var(--strong)}
.chip.fair{border-left:3px solid var(--fair)}
.chip.shape{border-left:3px solid var(--shape)}
.chip.weak{border-left:3px solid var(--weak)}
.chip.fam{border-style:dashed;color:var(--mut)}
.bad{color:var(--bad)}
.warn{color:var(--fair)}
.tag{font-size:11px;color:var(--mut);border:1px dashed var(--line);border-radius:4px;padding:0 4px}
"""


def num(v, dash="—"):
    return f"{v:,.0f}" if isinstance(v, (int, float)) and v else dash


def is_original(srcs):
    """An actor is an ORIGINAL when an original-shipping mod matched it BY NAME.

    That is the maintainer's own rule made mechanical: OpenRA Red Alert and Tiberian Dawn ship
    the original rosters and nothing else, so a name-backed match against one of them is proof
    the unit existed in the original game — and therefore proof that DTA and Combined Arms, both
    supersets, must have it too.
    """
    return any(d.get("confidence") in ("STRONG", "FAIR") and s in ORIGINAL_SOURCES
               for s, d in (srcs or {}).items())


def emit(body, members, crows, assignment, attached, chassis_only, dist, cdist, counts):
    for kind, title in SECTIONS:
        group = [a for a in members if crows[a]["type"] == kind]
        if not group:
            continue
        body.append(f'<h3>{title} <span class="muted">· {len(group)}</span></h3>')
        body.append('<table><thead><tr><th>Cameo actor</th><th class="n">refs</th>'
                    '<th class="n">HP now</th><th class="n">HP →</th>'
                    '<th class="n">speed now</th><th class="n">speed →</th>'
                    '<th class="n">cost now</th><th class="n">cost →</th>'
                    '<th>reference units chosen</th></tr></thead><tbody>')
        for a in group:
            c = crows[a]
            rows = attached.get(a) or []
            chosen = assignment.get(a) or {}
            counts["actors"] += 1
            counts["refs"] += len(chosen)
            srcs = sorted(chosen.items(), key=lambda kv: (
                CONF_ORDER.get((kv[1] or {}).get("confidence", "WEAK"), 9), kv[0]))
            flag = ""
            if not srcs:
                counts["none"] += 1
                flag = ' <b class="bad">no reference — formula</b>'
            elif is_original(chosen) and len(srcs) < 3:
                counts["thin"] += 1
                flag = ' <b class="warn">original, &lt;3 sources</b>'
            chips = "".join(
                '<span class="chip {cls}"><i>{src}</i> <code>{rid}</code> {rname}</span>'.format(
                    cls=(d or {}).get("confidence", "WEAK").lower(),
                    src=html.escape(s),
                    rid=html.escape(str((d or {}).get("id") or "?")),
                    rname=html.escape(str((d or {}).get("name") or "")))
                for s, d in srcs)
            # ⭐ SHOW THE VARIANT FAMILY, because the chip list was hiding the actual evidence.
            # A target is computed from every variant of the assigned unit in that source — the
            # Mammoth Mk III already averages CA's Mammoth, Hover Mammoth, Ion Mammoth and Mammoth
            # Drone — but the report displayed only the one row the greedy picked, so it read as a
            # single arbitrary choice. The maintainer reasonably objected to a mapping that was in
            # fact four rows deep.
            extra = len(rows) - len(srcs)
            if extra > 0:
                fam = ", ".join(dict.fromkeys(
                    str(r.get("id")) for r in rows
                    if str(r.get("id")) not in {str((d or {}).get("id")) for d in chosen.values()}))
                chips += (f'<span class="chip fam">+{extra} variant'
                          f'{"s" if extra != 1 else ""}: {html.escape(fam[:90])}</span>')
            tgt = {s: (rt.target_for(rows, c, s, dist, cdist)[1] if rows else None)
                   for s in ("hp", "speed", "cost")}
            note = ' <span class="tag">chassis-only</span>' if a in chassis_only else ""
            empty = '<span class="muted">—</span>'
            body.append(
                f'<tr><td><code>{html.escape(a)}</code>{note}{flag}</td>'
                f'<td class="n">{len(srcs)}</td>'
                f'<td class="n">{num(c.get("hp"))}</td><td class="n t">{num(tgt["hp"])}</td>'
                f'<td class="n">{num(c.get("speed"))}</td><td class="n t">{num(tgt["speed"])}</td>'
                f'<td class="n">{num(c.get("cost"))}</td><td class="n t">{num(tgt["cost"])}</td>'
                f'<td>{chips or empty}</td></tr>')
        body.append("</tbody></table>")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--faction", nargs="+", required=True)
    ap.add_argument("--out", default="report_td_ra1.html")
    args = ap.parse_args()

    peers, cameo = rd.peer_rows(), rd.cameo_rows()
    dist = rd.build_distributions(peers)
    rt.add_cost_distribution(dist, peers)
    cdist_all = rd.build_distributions(cameo)
    rt.add_cost_distribution(cdist_all, cameo)
    cdist = cdist_all["Cameo"]
    doc = json.loads(ASSIGN.read_text(encoding="utf-8"))
    assignment, chassis_only = doc["assignment"], doc.get("chassis_only", {})
    attached = rt.expand_families(rt.attach(assignment, rt.peer_index(peers)), peers)
    crows = {c["id"]: c for c in cameo}

    body = []
    counts = {"actors": 0, "refs": 0, "thin": 0, "none": 0, "orig": 0, "exp": 0}
    for fac in args.faction:
        members = sorted(a for a in crows if a.startswith(fac + "_"))
        originals = [a for a in members if is_original(assignment.get(a))]
        expansions = [a for a in members if not is_original(assignment.get(a))]
        counts["orig"] += len(originals)
        counts["exp"] += len(expansions)
        body.append(f'<h2>{html.escape(fac)} <span class="muted">· {len(originals)} original, '
                    f'{len(expansions)} expanded</span></h2>')
        for band, label, note in (
            (originals, "Originals",
             "These exist in OpenRA/OpenTD, so a counterpart exists in every source and all "
             "three must be present and must be the same unit. Anything short of three, or any "
             "reference that is not plainly the same unit, is a defect worth reporting."),
            (expansions, "Expanded units",
             "Cameo, Combined Arms or DTA additions. No counterpart is guaranteed, so references "
             "here are accepted only on a name or id match — never on a similar stat shape, which "
             "is what used to hand these actors critters and hero units. An actor with no "
             "reference is priced by the formula from its class anchor, which is the intended "
             "outcome, not a gap.")):
            if not band:
                continue
            body.append(f'<h2 class="band">{label} '
                        f'<span class="muted">· {len(band)}</span></h2>'
                        f'<p class="lede">{note}</p>')
            emit(body, band, crows, assignment, attached, chassis_only, dist, cdist, counts)

    summary = (f'{counts["orig"]} originals · {counts["exp"]} expanded · '
               f'{counts["refs"]} references · {counts["none"]} priced by formula · '
               f'{counts["thin"]} originals under three sources')
    page = (
        "<title>TD &amp; RA1 Reference Map</title>\n"
        f"<style>{STYLE}</style>\n"
        "<h1>TD &amp; RA1 Reference Map</h1>\n"
        '<p class="lede">Every Cameo actor with the reference unit chosen from each source, by '
        'full id and name, split into units that exist in the original games and units that do '
        'not. The bar on each chip is match confidence. <b>HP →</b>, <b>speed →</b> and '
        '<b>cost →</b> are the R4 synthesis targets — references plus Cameo, one vote each. '
        'Nothing here has been written to yaml.</p>\n'
        f'<p class="lede">{summary}</p>\n'
        '<div class="wrap">\n' + "\n".join(body) + "\n</div>\n")
    pathlib.Path(args.out).write_text(page, encoding="utf-8")
    print(f"wrote {args.out}  ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
