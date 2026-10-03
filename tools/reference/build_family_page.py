#!/usr/bin/env python3
"""Render `warhead_families.json` as the reviewable warhead-map page.

⚠ The page is GENERATED, never hand-edited: it exists so the maintainer can read the collapsed
map, and a hand edit would immediately disagree with the pipeline it is supposed to show.
Publish it to the SAME artifact URL each time (see docs/design/REFERENCE_EXTRACTION_PLAN.md R26).
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "reference" / "warhead_families.json"
OUT = ROOT / "docs" / "reference" / "warhead_map.html"

HEAD = """<title>Combined Arms Warhead Map</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root{
  --ground:#f2f1ee; --surface:#fbfaf8; --raise:#ffffff;
  --ink:#191b1d; --mut:#6b7076; --faint:#9aa0a6;
  --line:#dcdad4; --line2:#e9e7e2;
  --accent:#2f5d7c; --accent-soft:#dce8f0;
  --warn:#9a5b2a; --warn-soft:#f3e5d6;
  --bar:#7fa6bf; --bar-hi:#2f5d7c; --bar-lo:#c2b9ae;
  --sans:"IBM Plex Sans",ui-sans-serif,system-ui,sans-serif;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans",ui-sans-serif,system-ui,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ground:#15171a; --surface:#1c1f23; --raise:#22262b;
  --ink:#e8e6e1; --mut:#949aa1; --faint:#6f767d;
  --line:#2f343a; --line2:#272b30;
  --accent:#74a6c8; --accent-soft:#1e333f;
  --warn:#d59c62; --warn-soft:#3a2b1b;
  --bar:#4f7d99; --bar-hi:#74a6c8; --bar-lo:#4a4640;
}}
:root[data-theme="dark"]{
  --ground:#15171a; --surface:#1c1f23; --raise:#22262b;
  --ink:#e8e6e1; --mut:#949aa1; --faint:#6f767d;
  --line:#2f343a; --line2:#272b30;
  --accent:#74a6c8; --accent-soft:#1e333f;
  --warn:#d59c62; --warn-soft:#3a2b1b;
  --bar:#4f7d99; --bar-hi:#74a6c8; --bar-lo:#4a4640;
}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font:15px/1.55 var(--sans);margin:0}
.wrap{padding-block:26px;padding-left:clamp(16px,3.5vw,44px);padding-right:clamp(16px,3.5vw,44px);
  max-width:1180px;margin:0 auto}
h1{font:600 1.65rem/1.15 var(--cond);letter-spacing:-.005em;margin:0 0 6px;text-wrap:balance}
.lede{color:var(--mut);max-width:72ch;margin:0 0 12px}
.lede b{color:var(--ink);font-weight:600}
code{font:.86em/1.4 var(--mono)}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 6px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:8px 13px;min-width:104px}
.stat .n{font:600 1.22rem/1.1 var(--mono);font-variant-numeric:tabular-nums;display:block}
.stat .k{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);margin-top:3px;display:block}
.tools{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--ground);
  border-bottom:1px solid var(--line);padding:12px 0 11px;margin:16px 0 0;
  display:flex;flex-wrap:wrap;gap:8px;align-items:center}
select,input[type=search],input[type=text],button{font:14px var(--sans);color:var(--ink);
  background:var(--surface);border:1px solid var(--line);border-radius:5px;padding:6px 9px}
input[type=search]{min-width:min(230px,100%);flex:1 1 180px}
button{cursor:pointer;font-weight:500}
button.primary{background:var(--accent);color:#fff;border-color:transparent}
button:focus-visible,select:focus-visible,input:focus-visible,summary:focus-visible{
  outline:2px solid var(--accent);outline-offset:2px}
.rows{display:flex;flex-direction:column;gap:9px;margin-top:16px}
.row{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:7px;padding:12px 14px}
.row.park{border-left-color:var(--warn);border-left-style:dashed}
.row.hide{display:none}
.top{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:baseline}
.fname{font:600 1.02rem/1.3 var(--mono);letter-spacing:-.01em}
.chip{font-size:.7rem;text-transform:uppercase;letter-spacing:.07em;padding:2px 7px;border-radius:99px;
  background:var(--accent-soft);color:var(--accent);font-weight:600;white-space:nowrap}
.chip.w{background:var(--warn-soft);color:var(--warn)}
.metrics{margin-left:auto;display:flex;gap:14px;font:.8rem var(--mono);
  font-variant-numeric:tabular-nums;color:var(--mut);white-space:nowrap}
.metrics b{color:var(--ink);font-weight:600}
.prof{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:7px;margin:11px 0 3px}
@media (max-width:620px){.prof{grid-template-columns:repeat(3,minmax(0,1fr))}}
.cell .lbl{font-size:.66rem;text-transform:uppercase;letter-spacing:.06em;color:var(--faint);display:block;margin-bottom:3px}
.cell .v{font:600 .84rem var(--mono);font-variant-numeric:tabular-nums;display:block;margin-bottom:3px}
.cell .t{height:5px;background:var(--line2);border-radius:99px;overflow:hidden}
.cell .f{height:100%;background:var(--bar);border-radius:99px}
.cell.hi .f{background:var(--bar-hi)} .cell.lo .f{background:var(--bar-lo)}
.cell.na{opacity:.45}
.cell.na .v{color:var(--faint);font-style:italic}
.cell.der .v{color:var(--warn)}
.cell.der .f{background:repeating-linear-gradient(90deg,var(--warn) 0 3px,transparent 3px 6px)}
details{margin-top:9px}
summary{cursor:pointer;font-size:.8rem;color:var(--accent);font-weight:500}
.wlist{font:.78rem/1.7 var(--mono);color:var(--mut);margin-top:6px;word-break:break-word}
.derived{font-size:.8rem;color:var(--warn);margin:9px 0 0;padding-left:9px;
  border-left:2px solid var(--warn)}
.derived b{font-weight:600}
.note{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:11px;padding-top:10px;
  border-top:1px solid var(--line2)}
.note label{font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;color:var(--mut)}
.note input{flex:1 1 220px;min-width:0}
.callout{background:var(--warn-soft);border:1px solid var(--line);border-left:3px solid var(--warn);
  border-radius:7px;padding:12px 14px;margin:18px 0 0}
.callout h2{font:600 .78rem/1.2 var(--cond);text-transform:uppercase;letter-spacing:.09em;
  color:var(--warn);margin:0 0 7px}
.pairs{font:.8rem/1.9 var(--mono);color:var(--ink);font-variant-numeric:tabular-nums}
.out{margin-top:26px;background:var(--surface);border:1px solid var(--line);border-radius:7px;padding:14px}
.out h2{font:600 .78rem/1.2 var(--cond);text-transform:uppercase;letter-spacing:.09em;color:var(--mut);margin:0 0 8px}
textarea{width:100%;min-height:130px;font:12px/1.6 var(--mono);color:var(--ink);background:var(--raise);
  border:1px solid var(--line);border-radius:5px;padding:10px;resize:vertical}
.foot{font-size:.8rem;color:var(--mut);margin-top:9px}
.dmark{color:var(--warn)}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
"""

BODY_TOP = """<div class="wrap">
  <h1>Combined Arms Warhead Map</h1>
  <p class="lede"><b>One row per Cameo warhead</b> — every Combined Arms weapon that maps to the
  same warhead is pooled here exactly once. The {weapons} weapons CA fires became {groups} review
  groups, and those groups collapse onto the <b>{live} warheads</b> below by usage-weighted
  geometric mean.</p>
  <p class="lede">Each weapon contributes <b>its own measured row</b>, never its group's shape —
  a group is a reading aid, and a per-weapon override routinely sends one member elsewhere.
  Percentage warheads are priced as flat damage against the <b>typical unit of the armour they
  hit</b> (infantry 6,336 HP · light 18,774 · heavy 52,994 · wood 89,166), weighted by how much
  of that class they can actually reach.</p>
  <p class="lede"><b>An armour a warhead cannot touch reads <i>n/a</i>, not 100.</b> A dual-purpose
  unit's ground and air armaments are folded into one weapon — a flak track's AG and AA halves are
  one warhead, not two — so the ground warheads carry a real Aircraft figure instead of a blank.</p>
  <p class="lede"><b>No Cameo warhead is air-only.</b> A SAM still has to hurt something that lands
  under it, so where every source weapon in a family is air-only its ground rows are
  <b class="dmark">derived</b> from the same delivery's measured warheads and placed below the air
  value. Those cells are marked; a mod that gives its AA real ground rows will replace them.</p>
  <div class="stats" id="stats"></div>
  <div class="tools">
    <input type="search" id="q" placeholder="Search warhead or weapon…" aria-label="Search">
    <select id="fkind" aria-label="Filter"><option value="">All warheads</option>
      <option value="live">Live warheads only</option>
      <option value="park">Drops and parks only</option></select>
    <select id="sort" aria-label="Sort">
      <option value="uses">Sort by usage</option>
      <option value="name">Sort by name</option>
      <option value="factor">Sort by factor</option></select>
  </div>
  <div class="rows" id="rows"></div>
"""


def build(data: dict) -> str:
    src = data["combined_arms"]
    live = src["live"]
    weapons = sum(len(f['weapons']) for f in src['families'])
    group_count = len({g for f in src['families'] for g in f['groups']})
    body = [HEAD, BODY_TOP.format(live=live, weapons=weapons, groups=group_count)]

    pairs = src.get("collisions") or []
    if pairs:
        body.append('  <div class="callout"><h2>Warheads that are not yet distinct</h2>'
                    '<p class="lede" style="margin:0 0 7px">RMS log distance between profiles. '
                    'Combined Arms is one vote of twenty, so these are recorded rather than acted '
                    'on — separation happens once every source is averaged in.</p>'
                    '<div class="pairs">'
                    + "<br>".join(f"{d:.3f} &nbsp; {a} &nbsp;·&nbsp; {b}" for d, a, b in pairs)
                    + "</div></div>")

    body.append("""  <div class="out">
    <h2>Corrections to hand back</h2>
    <textarea id="dump" readonly aria-label="Corrections"></textarea>
    <button class="primary" id="copy" style="margin-top:9px">Copy corrections</button>
    <p class="foot">Notes are kept in this browser as you type. Copy this block back into the
    conversation and it will be applied to the pipeline.</p>
  </div>
</div>
""")
    body.append('<script id="data" type="application/json">'
                + json.dumps(src, separators=(",", ":")) + "</script>")
    body.append(SCRIPT)
    return "\n".join(body)


SCRIPT = r"""<script>
const D = JSON.parse(document.getElementById('data').textContent);
const ARM = D.armors, ROWS = document.getElementById('rows');
const KEY = 'ca-warhead-map-notes';
let notes = {};
try { notes = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { notes = {}; }

const isPark = f => f.family.startsWith('(');
const live = D.families.filter(f => !isPark(f));
const park = D.families.filter(isPark);

document.getElementById('stats').innerHTML = [
  ['Cameo warheads', live.length],
  ['weapons mapped', live.reduce((a, f) => a + f.weapons.length, 0)],
  ['usage votes', Math.round(live.reduce((a, f) => a + f.uses, 0))],
  ['dropped or parked', park.reduce((a, f) => a + f.weapons.length, 0)]
].map(([k, n]) => `<div class="stat"><span class="n">${n}</span><span class="k">${k}</span></div>`).join('');

function cells(f) {
  const der = !!f.derived_ground, airI = ARM.findIndex(a => a.toLowerCase() === 'aircraft');
  return ARM.map((a, i) => {
    const v = f.profile[i];
    if (v == null) return `<div class="cell na"><span class="lbl">${a}</span>
      <span class="v">n/a</span><div class="t"></div></div>`;
    let cls = v >= 150 ? 'hi' : (v <= 60 ? 'lo' : '');
    if (der && i !== airI) cls += ' der';
    return `<div class="cell ${cls}"><span class="lbl">${a}</span>
      <span class="v">${v}</span><div class="t"><div class="f" style="width:${Math.min(100, v / 2)}%"></div></div></div>`;
  }).join('');
}

function render() {
  const q = document.getElementById('q').value.trim().toLowerCase();
  const kind = document.getElementById('fkind').value;
  const sort = document.getElementById('sort').value;
  let list = D.families.slice();
  if (kind === 'live') list = list.filter(f => !isPark(f));
  if (kind === 'park') list = list.filter(isPark);
  if (sort === 'name') list.sort((a, b) => a.family.localeCompare(b.family));
  else if (sort === 'factor') list.sort((a, b) => b.factor - a.factor);
  else list.sort((a, b) => (isPark(a) - isPark(b)) || (b.uses - a.uses));

  ROWS.innerHTML = list.map(f => {
    const hit = !q || f.family.toLowerCase().includes(q)
      || f.weapons.some(w => w.toLowerCase().includes(q));
    const id = f.family.replace(/[^A-Za-z0-9]/g, '_');
    return `<div class="row ${isPark(f) ? 'park' : ''} ${hit ? '' : 'hide'}">
      <div class="top">
        <span class="fname">${f.family}</span>
        <span class="chip ${isPark(f) ? 'w' : ''}">${f.weapons.length} weapon${f.weapons.length === 1 ? '' : 's'}</span>
        <span class="metrics"><span>uses <b>${f.uses}</b></span><span>factor <b>${f.factor}</b></span></span>
      </div>
      <div class="prof">${cells(f)}</div>
      ${f.derived_ground ? `<p class="derived">Ground rows are <b>derived, not measured</b> —
        every source weapon here is air-only. Shape borrowed from this mod's
        ${f.derived_ground.donor_delivery} warheads (${f.derived_ground.donors.join(', ')}),
        placed at ${f.derived_ground.ratio * 100}% of the measured air value so air stays the peak.
        Another reference mod that gives its AA real ground rows will replace these.</p>` : ''}
      <details><summary>${f.weapons.length} weapons, from ${f.groups.length} group${f.groups.length === 1 ? '' : 's'}</summary>
        <div class="wlist">${f.weapons.join(' · ')}</div>
        <div class="wlist" style="margin-top:6px;color:var(--faint)">groups: ${f.groups.join(', ')}</div>
      </details>
      <div class="note">
        <label for="n_${id}">Correction</label>
        <input type="text" id="n_${id}" data-fam="${f.family}" value="${(notes[f.family] || '').replace(/"/g, '&quot;')}"
               placeholder="wrong warhead, wrong weapons, missing profile…">
      </div>
    </div>`;
  }).join('');

  ROWS.querySelectorAll('input[data-fam]').forEach(el => {
    el.addEventListener('input', () => {
      const k = el.dataset.fam;
      if (el.value.trim()) notes[k] = el.value.trim(); else delete notes[k];
      try { localStorage.setItem(KEY, JSON.stringify(notes)); } catch (e) {}
      dump();
    });
  });
  dump();
}

function dump() {
  const keys = Object.keys(notes).sort();
  document.getElementById('dump').value = keys.length
    ? keys.map(k => `${k}: ${notes[k]}`).join('\n')
    : 'No corrections yet — type in a Correction field on any row.';
}

['q', 'fkind', 'sort'].forEach(id =>
  document.getElementById(id).addEventListener('input', render));
document.getElementById('copy').addEventListener('click', async () => {
  const b = document.getElementById('copy');
  try { await navigator.clipboard.writeText(document.getElementById('dump').value);
        b.textContent = 'Copied'; } catch (e) { b.textContent = 'Select and copy manually'; }
  setTimeout(() => { b.textContent = 'Copy corrections'; }, 1800);
});
render();
</script>"""


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    src = data["combined_arms"]

    # Near-identical pairs, measured the same way the clustering measures shape distance.
    livef = [f for f in src["families"] if not f["family"].startswith("(")]
    pairs = []
    for i, a in enumerate(livef):
        for b in livef[i + 1:]:
            both = [(x, y) for x, y in zip(a["profile"], b["profile"])
                    if x and y and math.isfinite(x) and math.isfinite(y)]
            if len(both) < 2:
                continue
            d = math.sqrt(sum((math.log(x) - math.log(y)) ** 2 for x, y in both) / len(both))
            if d < 0.20:
                pairs.append((round(d, 3), a["family"], b["family"]))
    src["collisions"] = sorted(pairs)

    OUT.write_text(build(data), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size // 1024} KB, "
          f"{src['live']} live warheads, {len(pairs)} near-identical pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
