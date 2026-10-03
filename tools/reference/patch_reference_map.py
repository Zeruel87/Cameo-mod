#!/usr/bin/env python3
"""patch_reference_map.py — fold the warhead magnitude factor into the reference map's damage.

Maintainer order (2026-09-21): *"the weapon for each reference weapon needs to be also multiplied
by the relative versus value like the 0.7x I used as my example."*

WHAT IT DOES, AND WHY IT IS DEFENSIBLE
--------------------------------------
Each per-armament row of the map already names its VOTERS — the reference weapon each source
contributed, e.g. `= Combined Arms · Grenade`, `= DTA Enhanced · Grenade`, `= Tiberian Dawn ·
Grenade`. `docs/reference/warhead_factors.json` carries a magnitude factor per source weapon, so
the row's correction is the geometric mean of its voters' factors:

    reference_damage' = reference_damage x gmean(factor of each voting weapon)

That is EXACT if the projector pooled its sources geometrically, and close if it did not. It is
applied at the pooled figure rather than per source because the projector that produced the pooled
figure is not in this repository — the map's HTML was generated ad hoc and its generator is gone.
That limitation is stated on the page itself rather than hidden, and the original value is kept in
a `data-v-pre-versus` attribute so the correction is always reversible.

WHY THE DAMAGE NEEDED CORRECTING AT ALL
---------------------------------------
A reference `Damage` number is not comparable across warheads: 2500 from a rocket that doubles
against armour and 2500 from a machine gun that is quartered by it are different amounts of
delivered output. DESIGN.md §12.0 already discards the armour profile's magnitude when reading a
reference ("absolute lethality still lives in Damage") — this hands that magnitude back.

    python tools/reference/patch_reference_map.py IN.html --out OUT.html
    python tools/reference/patch_reference_map.py IN.html --dry-run
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
FACTORS = ROOT / "docs" / "reference" / "warhead_factors.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# The map writes a source's display name; the factor table is keyed by source id.
LABEL_TO_SOURCE = {
    "Combined Arms": "combined_arms",
    "DTA Enhanced": "dta_enhanced",
    "DTA Classic": "dta_classic",
    "Tiberian Dawn": "openra_td",
    "OpenRA Tiberian Dawn": "openra_td",
    "Red Alert": "openra_ra",
    "OpenRA Red Alert": "openra_ra",
}

VOTER_RE = re.compile(
    r'<span class="tag" title="[^"]*">\s*[=~]\s*([^&]+?)\s*&middot;\s*([^<]+?)\s*</span>')
# One per-armament <tr>. The damage cell is the SECOND `now → ref` cell in the row.
ROW_RE = re.compile(r"<tr>(?:(?!</tr>).)*</tr>", re.S)
TD_RE = re.compile(r"<td[ >](?:(?!</td>).)*</td>", re.S)
# role | Cameo weapon | range | DAMAGE/CYCLE | reload | burst | burst delay | DPS verifier | voters
DAMAGE_COLUMN = 3
# The cell's own "now" figure, before the arrow: `<td class="n">1,920 <span class="muted">→`
NOW_RE = re.compile(r'<td class="n">([0-9,]+)[^<]*<span class="muted">→</span>')
# `<b class="warn" title="...">3.39x</b>` — the ratio badge that sits after the reference span.
BADGE_RE = re.compile(r'(<b class="(?:warn|bad)"[^>]*>)([0-9.]+)x(</b>)')
DAMAGE_CELL_RE = re.compile(
    r'(<td class="n">[^<]*<span class="muted">→</span>\s*<span data-v="([0-9.]+)"'
    r'([^>]*)>)([0-9,]+)(<small class="evidence">[^<]*</small></span>)')


def _esc(text: str) -> str:
    """Attribute-safe. The note goes inside a double-quoted HTML title."""
    return (text.replace("&", "&amp;").replace('"', "&quot;")
                .replace("<", "&lt;").replace(">", "&gt;"))


LEDE = (
    '<p class="lede"><b>Damage is versus-corrected.</b> A reference <code>Damage</code> number is '
    'not comparable across warheads &mdash; 2,500 from a rocket that doubles against armour and '
    '2,500 from a machine gun that armour quarters are different amounts of delivered output. '
    'Every per-armament reference damage below is therefore multiplied by the magnitude of its '
    'warhead&#39;s armour profile: the geometric mean of that warhead&#39;s Versus row divided by '
    'its own mod&#39;s usage-weighted matrix centre, pooled geometrically across the row&#39;s '
    'voters. Hover any corrected figure for its working and its pre-correction value. '
    'Measured factors span 0.25&times; to 1.61&times;, median 1.03&times;: machine guns fall, '
    'missiles and cannons rise. Source: <code>docs/reference/warhead_factors.json</code>, built '
    'by <code>tools/reference/warhead_matrix.py</code>; each mod&#39;s matrix is normalised to a '
    'geometric mean of 100 inside Cameo&#39;s own [10, 200] window (DESIGN.md &sect;12.0 rule 4). '
    '&#9888; The pooled figure is corrected after pooling, not per source before it, because the '
    'projector that produced it is not in the repository.</p>')


def gmean(values: list[float]) -> float:
    return math.exp(sum(math.log(v) for v in values) / len(values))


def load_factors() -> dict:
    return json.loads(FACTORS.read_text(encoding="utf-8"))["sources"]


def row_multiplier(row_html: str, factors: dict) -> tuple[float | None, list, list]:
    """The geometric mean of this row's voters' factors, plus what resolved and what did not."""
    hit, missed = [], []
    for label, weapon in VOTER_RE.findall(row_html):
        source = LABEL_TO_SOURCE.get(label.strip())
        table = factors.get(source, {}).get("weapons_ci", {}) if source else {}
        value = table.get(weapon.strip().lower())
        if value is None:
            missed.append((label.strip(), weapon.strip()))
        else:
            hit.append((label.strip(), weapon.strip(), value))
    if not hit:
        return None, hit, missed
    return gmean([v for _, _, v in hit]), hit, missed


def patch(html: str, factors: dict, dry_run: bool = False) -> tuple[str, dict]:
    stats = collections.Counter()
    moves: list[tuple[str, float, float, float]] = []
    out = []
    last = 0

    for row in ROW_RE.finditer(html):
        text = row.group(0)
        if 'class="tag"' not in text:
            continue                                   # not a per-armament row
        mult, hit, missed = row_multiplier(text, factors)
        stats["rows"] += 1
        stats["voters_resolved"] += len(hit)
        stats["voters_missed"] += len(missed)
        if mult is None:
            stats["rows_unresolved"] += 1
            continue

        # ⚠ FIND THE DAMAGE CELL BY ITS COLUMN, NOT BY COUNTING `data-v` SPANS. The per-armament
        # columns are role, weapon, range, DAMAGE, reload, burst, ... and any of them can be an
        # em-dash with no `data-v` at all. Counting matches therefore slides the index and would
        # silently rewrite the RELOAD as if it were damage — a wrong number that still looks fine.
        tds = list(TD_RE.finditer(text))
        if len(tds) <= DAMAGE_COLUMN:
            stats["rows_no_damage_cell"] += 1
            continue
        td = tds[DAMAGE_COLUMN]
        cell = DAMAGE_CELL_RE.search(td.group(0))
        if cell is None:
            stats["rows_no_damage_cell"] += 1
            continue
        old_value = float(cell.group(2))
        new_value = old_value * mult
        moves.append((cell.group(4), old_value, new_value, mult))
        stats["rows_patched"] += 1

        # The working goes in the cell's own tooltip, so a reviewer can see WHY a number moved
        # without leaving the row: the pre-correction figure, the multiplier, and each voter's
        # own factor. A correction nobody can audit is a correction nobody should trust.
        note = (f"versus-corrected: {old_value:,.0f} x {mult:.3f} = {new_value:,.0f}. "
                f"Each voting reference weapon is scaled by its warhead's armor-profile "
                f"magnitude (geometric mean of its Versus row / its mod's matrix centre), "
                f"then pooled geometrically. Voters: "
                + "; ".join(f"{lbl} {w} x{v:.2f}" for lbl, w, v in hit)
                + (f". NOT corrected (no warhead resolved): "
                   f"{', '.join(w for _, w in missed)}" if missed else ""))
        head = cell.group(1)[:cell.group(1).index("data-v=")]
        title = re.search(r'title="([^"]*)"', cell.group(3))
        rest = cell.group(3)
        if title:
            rest = rest.replace(title.group(0),
                                f'title="{title.group(1)} — {_esc(note)}"')
        else:
            rest = f' title="{_esc(note)}"' + rest
        replacement = (
            f'{head}'
            f'data-v="{new_value:.6g}" data-v-pre-versus="{old_value:.6g}"'
            f'{rest}>'
            f'{new_value:,.0f}'
            f'{cell.group(5)}')
        # splice, keeping absolute offsets straight
        start = row.start() + td.start() + cell.start()
        end = row.start() + td.start() + cell.end()
        out.append(html[last:start])
        out.append(replacement if not dry_run else html[start:end])
        last = end

        # ⚠ THE RATIO BADGE MUST MOVE WITH THE NUMBER. Each damage cell carries a
        # `<b class="warn">3.39x</b>` comparing Cameo-now against the reference. Rewriting the
        # reference and leaving the badge alone leaves the row self-contradicting — and the badge
        # is the thing a reviewer actually reads. Recompute it from the cell's own "now" value.
        now = NOW_RE.match(td.group(0))
        badge = BADGE_RE.search(td.group(0), cell.end())
        if now and badge and not dry_run:
            now_value = float(now.group(1).replace(",", ""))
            if now_value > 0:
                ratio = new_value / now_value
                b_start = row.start() + td.start() + badge.start()
                b_end = row.start() + td.start() + badge.end()
                out.append(html[last:b_start])
                out.append(f"{badge.group(1)}{ratio:.2f}x{badge.group(3)}")
                last = b_end
                stats["badges_rewritten"] += 1
            else:
                stats["badges_skipped"] += 1
        elif badge:
            stats["badges_skipped"] += 1

    out.append(html[last:])
    result = "".join(out)

    # One explanation, immediately after the page's existing lede paragraphs.
    anchor = "<div class=\"wrap\">"
    if LEDE not in result and anchor in result:
        result = result.replace(anchor, LEDE + anchor, 1)
        stats["lede_added"] = 1
    return result, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--out")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    html = io.open(args.source, encoding="utf-8").read()
    factors = load_factors()
    patched, stats = patch(html, factors, dry_run=args.dry_run)

    for key in ("rows", "rows_patched", "rows_unresolved", "rows_no_damage_cell",
                "voters_resolved", "voters_missed", "badges_rewritten", "badges_skipped",
                "lede_added"):
        print(f"  {key:22s} {stats[key]}")

    if args.out and not args.dry_run:
        pathlib.Path(args.out).write_text(patched, encoding="utf-8")
        print(f"\nwrote {args.out}  ({len(patched):,} chars, was {len(html):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
