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
import collections
import hashlib
import html
import json
import math
import re
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import reference_distribution as rd          # noqa: E402
import reference_targets as rt               # noqa: E402
import build_armament_pairing_report as bap  # noqa: E402
import armament_roles as ar                   # noqa: E402

ROOT = rd.ROOT
ASSIGN = ROOT / "docs/balance/derived/reference_assignment.json"
SINGLETON_SELF_VOTES = ROOT / "docs/reference/cameo_singleton_armament_self_votes_20260914.json"
ORIGINAL_SOURCES = ("OpenRA Red Alert", "OpenRA Tiberian Dawn",
                    "OpenRA Tiberian Sun", "Romanov's Vengeance")
SECTIONS = (("infantry", "Infantry"), ("vehicle", "Vehicles"), ("aircraft", "Aircraft"),
            ("ship", "Naval"), ("defense", "Defenses"))
CONF_ORDER = {"STRONG": 0, "FAIR": 1, "SHAPE": 2, "WEAK": 3}
UNARMED_COUNTERPARTS = {('Combined Arms', 'SPY'), ('DTA Enhanced', 'SPY'), ('DTA Classic', 'SPY')}

STYLE = """
.cls{font-size:11px;color:var(--mut);white-space:nowrap}
.evidence{display:block;font-size:10px;font-weight:400;color:var(--mut)}
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


def arm_note(actor, led_arms, model_eligible):
    """Explain why a multi-armament row is withheld from the one-armament model.

    The ledger total and the primary cadence cannot be composed safely — 495 of 822 armed actors
    carry several, and `ra2_allies_ifv` carries 39 mutually-exclusive ones. The marker keeps the
    structural fact visible without presenting an aggregate as one weapon's per-shot damage.
    """
    n = led_arms.get(actor, 0)
    if n <= 1:
        return ""
    # ⭐ SAY HOW MANY FIRE TOGETHER, not just how many exist. `x4` on the mammoth was answering a
    # question nobody asked: it has four priced armaments and can only ever fire two, because the
    # cannons and the missiles are each an upgrade pair gated on `C` / `!C`. Reading "x4" as "this
    # tank has four guns" is the mistake the maintainer was worried about when they asked whether
    # a single collapsed damage number would be better.
    sim, total = simultaneous_armaments(actor)
    if model_eligible is True:
        return (f'<span class="muted" title="{total or n} priced armaments; exactly one is in '
                'the baseline firing set, so the displayed components describe that armament.'
                f'">1 of {total or n} guns</span>')
    if sim is None:
        return (f'<span class="muted" title="{total or n} priced armaments; the active '
                'simultaneous set is not proven, so the one-armament component model is '
                f'withheld.">&#215;{n}</span>')
    if sim and total and sim < total:
        return (f'<span class="muted" title="{total} priced armaments, but only {sim} can fire at '
                f'once — the rest are mutually exclusive upgrade variants gated on a condition. '
                f'The one-armament component model is withheld.">{sim} of {total} guns</span>')
    return (f'<span class="muted" title="{n} priced armaments may fire together; the '
            f'one-armament component model is withheld">&#215;{n}</span>')


_SIM_CACHE = {}
_RULESET = []


def _ruleset():
    """The resolved ruleset, loaded once — the only place armament CONDITIONS exist."""
    if not _RULESET:
        sys.path.insert(0, str(ROOT / "tools" / "audit"))
        import miniyaml
        _RULESET.append(miniyaml.Ruleset(str(ROOT)))
    return _RULESET[0]


def simultaneous_condition_bound(conditions):
    """Maximum simultaneous arms for simple `C`/`!C` gates, or None if not provable."""
    groups = collections.defaultdict(lambda: [0, 0])
    loose = 0
    for raw in conditions:
        cond = (raw or "").strip()
        if not cond:
            loose += 1
            continue
        if re.fullmatch(r"!?[A-Za-z_][A-Za-z0-9_.-]*", cond) is None:
            return None
        negated = cond.startswith("!")
        token = cond[1:] if negated else cond
        groups[token][1 if negated else 0] += 1
    return loose + sum(max(polarities) for polarities in groups.values())


def simultaneous_armaments(actor):
    """(fire together, priced total) — because `x4` on the mammoth means neither.

    ⛔ THE PRICED COUNT IS NOT THE SIMULTANEOUS COUNT, and the maintainer spotted the problem
    from the other end: *"it gets more complicated for dual weapons then like the mammoth tank
    dual cannons and dual missiles"*. `td_gdi_mammothtank` carries four priced armaments and
    fires exactly TWO of them, ever:

        Armament@PRIMARY                    !td_gdi_upgrade_highvelocitycannons
        Armament@HV                          td_gdi_upgrade_highvelocitycannons
        Armament@SECONDARY                  !td_gdi_upgrade_advancedmissiletargeting
        Armament@AdvancedMissileTargeting    td_gdi_upgrade_advancedmissiletargeting

    Two mutually exclusive PAIRS — one cannon and one missile launcher, whichever upgrades are
    held. Summing four would describe a tank that cannot exist, which is exactly why the damage
    column shows one armament rather than a total.

    For a simple condition token, `C` and `!C` are opposite states; the larger side of that split
    is the simultaneous bound. Repeated `C` arms each count because they can fire together. Any
    compound expression is reported unknown instead of guessed. Unconditioned armaments each
    contribute one. ⚠ The LEDGER cannot answer this — its armament records carry
    `requires_condition: None` for all four — so it is read from the resolved yaml, through
    `miniyaml` rather than by hand.
    """
    if actor in _SIM_CACHE:
        return _SIM_CACHE[actor]
    try:
        node = _ruleset().resolve(actor)
    except Exception:                                   # a missing actor is not a report failure
        node = None
    if node is None:
        return _SIM_CACHE.setdefault(actor, (None, None))
    conditions = []
    total = 0
    for child in node.children:
        if not child.key.startswith("Armament"):
            continue
        fields = {g.key: g.value for g in child.children}
        if not fields.get("Weapon"):
            continue
        total += 1
        conditions.append(fields.get("RequiresCondition") or "")
    return _SIM_CACHE.setdefault(actor, (simultaneous_condition_bound(conditions), total))


_BASELINE_SIM_CACHE = {}


def as_built_weapons(actor):
    """The set of weapon NAMES that fire on the unit AS BUILT - nothing bought, nothing earned.

    ⛔ THIS IS NOT `simultaneous_armaments`, AND THE DIFFERENCE IS THE WHOLE POINT.
    That one returns the MAXIMUM the actor can ever have firing at once; this one returns what
    fires the moment it rolls off the production line. `td_gdi_battletank` separates them:

        Armament              !td_gdi_upgrade_highvelocitycannons      <- as built
        Armament@HV            td_gdi_upgrade_highvelocitycannons
        Armament@Missile      !td_gdi_upgrade_advancedmissiletargeting <- as built
        Armament@Advanced...   td_gdi_upgrade_advancedmissiletargeting
        Armament@MachineGun    td_gdi_upgrade_armorpiercingbullets     <- ADDITIVE upgrade

    The machine gun has no `!` twin, so it is an EXTRA gun bought later rather than a swap. The
    maximum is 3 and the as-built loadout is 2, and both numbers are true. Summing the maximum
    would price every Battle Tank as though it had already paid for an upgrade it may never buy,
    so the combined figure describes the as-built unit - the same state every other column on
    this row is measured in.

    A negated gate (`!upgrade`) is ACTIVE as built and belongs here; a plain gate (`upgrade`) is
    not and does not. Anything this cannot read - a compound expression - returns None, and the
    caller withholds rather than guesses.

    ⚠ WEAPONS, NOT SLOTS. `Armament@PRIMARY` and `Armament@GARRISONED` are the same gun fired
    from two places, and counting slots made a rifleman look like a two-gun unit.
    """
    if actor in _BASELINE_SIM_CACHE:
        return _BASELINE_SIM_CACHE[actor]
    try:
        node = _ruleset().resolve(actor)
    except Exception:                                   # a missing actor is not a report failure
        node = None
    if node is None:
        return _BASELINE_SIM_CACHE.setdefault(actor, None)
    built = set()
    for child in node.children:
        if not child.key.startswith("Armament"):
            continue
        fields = {g.key: g.value for g in child.children}
        weapon = fields.get("Weapon")
        if not weapon:
            continue
        cond = (fields.get("RequiresCondition") or "").strip()
        if not cond:
            built.add(weapon)
        elif re.fullmatch(r"!?[A-Za-z_][A-Za-z0-9_.-]*", cond) is None:
            return _BASELINE_SIM_CACHE.setdefault(actor, None)
        elif cond.startswith("!"):
            built.add(weapon)
    return _BASELINE_SIM_CACHE.setdefault(actor, frozenset(built))


def burst_note(cameo_row):
    """`= 16,000 x 2` beneath a per-CYCLE damage figure — the breakdown, not a multiplier.

    ⛔ THE BRACKET USED TO BE A MULTIPLIER AND THAT IS NOW WRONG. The maintainer asked for
    "10k damage (2x) which means the total damage is 2x of 10k so 20k", and while the column held
    damage PER SHOT that is exactly what `(x2)` meant. The column now holds damage PER CYCLE — the
    quantity the reference actually projects, because burst is a delivery choice and the cycle
    total is the comparable magnitude — so `32,000 (x2)` would read as "multiply by two" on a
    number that already includes the burst, and invite a reader to double it.

    Same information, stated the way round the value now demands: the cycle total leads, and the
    shot it is built from is shown underneath.
    """
    if cameo_row.get("weapon_model_eligible") is False:
        return ""
    burst = float(cameo_row.get("w_burst") or 1)
    cycle = cameo_row.get("w_damage")
    if burst <= 1 or not cycle:
        return ""
    return (f'<small class="evidence" title="the figure above is one full cycle; this is the '
            f'shot it is built from">= {cycle / burst:,.0f} &#215; {burst:.0f}</small>')


def component_num(cameo_row, stat):
    if cameo_row.get("weapon_model_eligible") is False:
        return ('<span class="muted" title="multiple baseline armaments, and a cadence does not '
                'sum: two guns firing together have two reload delays and two bursts. The '
                'combined DAMAGE is in the damage column; the per-weapon cadence is in the '
                'per-armament block below.">WITHHELD</span>')
    return num(cameo_row.get(stat))


def recovered_burst_delay(row):
    """Ticks between shots INSIDE a burst, recovered from the row's own identity.

    It is recovered, not read: no source publishes a usable per-shot delay on the unit row.
    `w_damage` is normalized to a full-cycle total and `reference_targets.damage_per_shot`
    derives the formula input before the cycle identity is inverted.

    ⚠ A SINGLE-SHOT WEAPON HAS NO BURST DELAY, so this returns None rather than a number. With
    `Burst: 1` there is no gap to measure, and the leftover cycle time is charge-up or rounding
    rather than a delay between shots. Measured across the tree, all 477 single-shot rows recover
    exactly 0.00, so printing "0" would read as a real measurement of something that does not
    exist; 245 rows carry a genuine burst.
    """
    # Ask the one convention-aware helper; it also rejects the 334 rows whose recorded rate used
    # the burst-1 identity despite declaring Burst > 1.
    return rt.burst_delay_of(row)


def burst_delay_cell(cameo_row, rows):
    """`now -> reference` for burst delay, marked as RECOVERED rather than projected.

    ⭐ ADDED 2026-09-12 at the maintainer's request: "with damage per shot, burst, burst delay,
    reload delay instead of just the DPS". That REVERSES an earlier instruction recorded in this
    file — "the burst delay should be referenced but not in the reference map" — and the newer
    one wins. The old claim is struck rather than left sitting next to the new behaviour.

    ⚠ THIS CELL DELIBERATELY DOES NOT GO THROUGH `estimate_cell`. Every other target is normalised
    against a per-source distribution before projection; burst delay has no such population,
    because it is not a published statistic anywhere — it is derived per row. Forcing it through
    that pipeline would mean inventing a distribution for it and would dress a recovered quantity
    up as a projected one. The reference figure is the plain MEDIAN of whatever the assigned
    reference rows recover, and the cell says exactly that in its tooltip.
    """
    if cameo_row.get("weapon_model_eligible") is False:
        return ('<span class="muted" title="multiple baseline armaments: cadence model '
                'withheld">WITHHELD</span>')
    cur = recovered_burst_delay(cameo_row)
    vals = sorted(v for v in (recovered_burst_delay(r) for r in rows) if v is not None)
    if cur is None and not vals:
        return '<span class="muted">—</span>'
    left = f'{cur:.0f}' if cur is not None else '<span class="muted">—</span>'
    if not vals:
        return (f'{left} <span class="muted">→</span> '
                f'<span class="muted" title="no assigned reference carries a burst">—</span>')
    mid = len(vals) // 2
    med = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
    title = (f'median of {len(vals)} reference row(s) that carry a burst; RECOVERED from each '
             f'row&#39;s own damage/dps/reload identity, not a normalised projection')
    return (f'{left} <span class="muted">→</span> <span title="{title}">{med:.0f}'
            f'<small class="evidence">{len(vals)} recovered</small></span>')


def reference_burst_delay(rows):
    """Median usable reference delay, or None when every assigned row abstains."""
    vals = sorted(v for v in (recovered_burst_delay(row) for row in rows) if v is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def dps_verifier_cell(cameo_row, rows, tgt):
    """Total DPS as R1's GUARD RAIL: never a target, only a verdict on the components.

    Three things can come back, and the middle one is why the ruling exists:

      no change / a ratio  composing the component targets moves DPS by this much.
      DISAGREES            the components and the independent DPS projection tell materially
                           different stories. `td_gdi_mammothtank` produced the ruling: the
                           DPS projection alone said +73.7%, damage-plus-reload said +21.2%,
                           1.43x apart. Neither is wrong — they are separate votes, and a
                           human picks.
      EXTREME              the composed move alone exceeds EXTREME_RATIO.

    ⭐ THE CONVENTION IS KNOWN FOR ONE-ARMAMENT ROWS. Multi-armament Cameo rows aggregate damage
    and rate but borrow burst/reload from one primary, so they are explicitly withheld. A parallel
    fix (`41d0dad57`)
    made this cell fail closed on the premise that "the source corpus currently lacks that
    compatible evidence", which would print WITHHELD on every row. The premise is falsifiable and
    the AUTHORED YAML falsifies it: `td_gdi_mammothtank_120mmdualhv` declares `Damage: 16000`,
    `Burst: 2`, `BurstDelays: 8`, `ReloadDelay: 72` and the snapshot carries `w_damage` 32,000 —
    so Cameo stores the burst TOTAL, provably, and `td_gdi_mlrs_227mm` (8,000 x 6 = 48,000) says
    the same. The cure for an ambiguous unit is to resolve it, not to stop reporting.

    Eligible peer and Cameo rows expose one per-cycle damage coordinate and a derived per-shot
    formula input (`reference_distribution.to_per_cycle`). What IS kept from that fix is its better
    refusal: a recovered burst time below zero means the row's own DPS identity is shorter than
    its ReloadDelay, which is impossible, and clamping it to zero would certify a broken timing
    model. That still withholds.

    Burst delays ARE in the cycle and, as of 2026-09-12, are also their own column — see
    `burst_delay_cell`, which supersedes the earlier "referenced but not in the reference map"
    instruction (maintainer, 2026-09-12: "with damage per shot, burst, burst delay, reload delay
    instead of just the DPS").
    """
    if cameo_row.get("weapon_model_eligible") is False:
        return ('<span class="muted" title="withheld: multiple baseline armaments do not form '
                'one damage/burst/reload cadence">WITHHELD</span>')
    keys = ("w_damage", "w_burst", "w_reload")
    cur = {k: cameo_row.get(k) for k in keys}
    cur["w_dps"] = cameo_row.get("w_dps")
    comp = {k: _cell_value(tgt.get(k)) for k in keys}
    if not any(value is not None for value in comp.values()):
        return ('<span class="muted" title="withheld: no admitted component projection '
                'to verify">WITHHELD</span>')
    g = rt.dps_guard(cur, comp, _cell_value(tgt.get("w_dps")),
                     reference_burst_delay(rows))
    if g is None:
        return ('<span class="muted" title="withheld: explicit damage convention and complete '
                'burst-delay evidence required">WITHHELD</span>')
    pct = f'{g["composed_ratio"] * 100:.0f}%'
    bd = f'burst delay {g["burst_delay_per_shot"]:.0f}t/shot (recovered)'
    if g["verdict"] == "ok":
        tag = (f'<span class="tag" title="{bd}">no change</span>'
               if abs(g["composed_ratio"] - 1) < 0.02
               else f'<span class="tag" title="{bd}">{pct} of now</span>')
    elif g["verdict"] == "extreme":
        tag = (f'<b class="warn" title="the composed move alone exceeds '
               f'{rt.EXTREME_RATIO:g}x; {bd}">EXTREME {pct}</b>')
    else:
        tag = (f'<b class="warn" title="components say {pct} of now, the DPS projection says '
               f'{g["projected_ratio"] * 100:.0f}% — {1 / g["disagreement"]:.2f}x apart; '
               f'separate votes, pick one. {bd}">DISAGREES {pct}</b>')
    return f'{g["composed_dps"]:.0f} {tag}'


def _cell_value(cell):
    """Pull the unrounded projection back out of a rendered estimate cell.

    `estimate_cell` returns HTML, and the guard needs the NUMBER. Parsing display output would
    be fragile, so `estimate_cell` stashes the value it used on the string via a data
    attribute; absent that, there is nothing to verify and the guard abstains rather than
    guessing.
    """
    if isinstance(cell, (int, float)):
        return cell
    if not isinstance(cell, str):
        return None
    m = re.search(r'data-v="([-0-9.eE+]+)"', cell)
    return float(m.group(1)) if m else None


def estimate_cell(rows, cameo_row, stat, dist, cdist, assigned_sources, flag_change=None):
    """Show metric evidence separately from identity matches; never relax eligibility.

    `flag_change` is the CURRENT value of an integer-valued stat. When given, the cell marks
    whether the reference target would actually MOVE it once snapped to its grid, and shows
    the unrounded projection in the tooltip. That distinction is the whole point for `Burst`:
    its raw target on `td_gdi_mammothtank` is **1.67**, which `num()` renders as "2" -- the
    same as the current value -- so the column reads as a change when it is not one. Burst may
    not be touched without the maintainer's explicit permission, so "would this move?" is a
    FLAG, not a routine number, and it has to be legible at a glance in the big table.
    """
    try:
        _, value, used = rt.target_for(rows, cameo_row, stat, dist, cdist) if rows else (None, None, 0)
        failure = None
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        value, used, failure = None, 0, type(exc).__name__
    reasons = []
    required = rd.ELIGIBILITY.get(stat, {}).get('requires')
    for row in rows:
        if rd.eligible(row, stat):
            if row.get(stat) and not any(dist.get(row['source'], {}).get(pop, {}).get(stat)
                    for pop in ('overall', row.get('type'))):
                reasons.append(f"{row['source']} / {row['id']}: raw statistic available, but insufficient normalization population (minimum three usable rows)")
            continue
        if stat in ('w_range', 'w_dps') and (row['source'], row['id']) in UNARMED_COUNTERPARTS:
            reasons.append(f"{row['source']} / {row['id']}: N/A, unarmed counterpart; identity match retained")
            continue
        if row.get('reference_base_eligible') is False:
            reasons.append(f"{row['source']} / {row['id']}: upgraded variant, excluded from base estimates")
            continue
        if required and not (row.get(required) is not None and row[required] > 0):
            reason = ('weapon estimate withheld' if required == 'w_dps'
                      else required + ' unavailable')
            raw_reason = row.get('w_evidence_reason') or ''
            categories = []
            if any(k in raw_reason for k in ('conditional', 'activation_trait', 'weapon_modifier', 'cadence_trait')):
                categories.append('conditional firing or modifiers not fully resolved')
            if any(k in raw_reason for k in ('unknown_warhead', 'nonconventional', 'non_damage', 'direct_undeclared')):
                categories.append('weapon damage/effect evidence incomplete')
            if 'multi_armament' in raw_reason:
                categories.append('multiple weapon slots not fully resolved')
            detail = ', '.join(categories) if required == 'w_dps' else None
        else:
            reason, detail = stat + ' unavailable', None
        reasons.append(f"{row['source']} / {row['id']}: {reason}" + (f" ({detail})" if detail else ''))
    status = f'{used}/{assigned_sources} sources used'
    if value is None:
        explanation = ('Calculation failed: ' + failure if failure else
                       'No usable source projection under the current evidence rules.')
    else:
        explanation = 'Sources counted once after pooling eligible variants; Cameo self-vote, if eligible, is additional.'
    badge = ""
    if flag_change is not None and value is not None:
        explanation += f' Unrounded projection {value:.4g}.'
        moved = round(value) != round(flag_change)
        badge = (f' <b class="warn" title="needs explicit maintainer permission">'
                 f'would change {round(flag_change):g}&rarr;{round(value):g}</b>' if moved
                 else ' <span class="tag" title="raw target rounds to the current value">'
                      'no change</span>')
    tooltip = html.escape(explanation + (' ' + '; '.join(reasons) if reasons else ''), quote=True)
    # `data-v` carries the UNROUNDED projection so the DPS verifier can compose the component
    # targets arithmetically. Re-deriving it by parsing the displayed number would silently
    # feed the guard a rounded value, and rounding is exactly what hid the burst 1.67 -> "2".
    dv = "" if value is None else f' data-v="{value:.10g}"'
    return (f'<span{dv} title="{tooltip}">{num(value)}'
            f'<small class="evidence">{status}</small></span>{badge}')


def weapon_calculation_details(rows, cameo_actor=None):
    """Expose source scalars and reviewed cycles without inventing missing delays."""
    import peer_nominal_evidence as nominal
    import projectile_travel_evidence as travel
    profile = nominal.load(ROOT)
    travel_profiles = travel.load(ROOT)
    parts = []
    if cameo_actor:
        parts.append('<p><b>Current Cameo projectile comparison</b><br>' + html.escape(
            travel.describe(travel_profiles.get(('Cameo current', cameo_actor), []))) + '</p>')
    def value(v):
        if isinstance(v, (int, float)):
            return f"{v:g}"
        return str(v) if v is not None else "unavailable"
    for row in rows:
        proof = profile.get((row.get('source'), row.get('id')))
        cycle = row.get('w_cycle_evidence')
        fields = [('weapon', row.get('weapon')),
                  ('damage per cycle (reference coordinate)', row.get('w_damage')),
                  ('derived damage per shot', rt.damage_per_shot(row)),
                  ('reload delay / ROF (source ticks)', row.get('w_reload')),
                  ('burst', row.get('w_burst'))]
        if proof:
            fields = [('weapon', proof.get('weapon') or row.get('weapon')),
                      ('uncapped damage against named target' if proof.get('comparison_basis') == 'named_target_uncapped' else
                       'common authored damage basis per shot' if proof.get('comparison_basis') == 'common_authored_damage' else
                       'damage per shot after spin-up' if proof.get('warmup_shots') else
                       'mean damage per shot' if proof.get('shot_damage') else 'damage per shot (raw source units)', proof['damage']),
                      ('reload delay (source ticks)', proof['reload']),
                      ('burst', proof.get('burst', 1)),
                      ('burst delays (source ticks)', proof.get('burst_delays', []))]
        elif cycle:
            fields.extend([('cycle emission delay model (source ticks)', cycle['burst_delays']),
                           ('post-reload jitter/scheduling adjustment (source ticks)', cycle['post_burst_jitter'])])
            if 'cycle_shots' in cycle:
                fields.extend([('shots in modeled cycle (distinct from weapon Burst)', cycle['cycle_shots']),
                               ('additional charge and scheduling ticks', cycle.get('charge_ticks', 0)),
                               ('ammunition and charge proof', cycle.get('ammo_charge_proof'))])
        else:
            fields.append(('burst delays (source ticks)', row.get('w_burst_delays')))
        fields.append(('separate projectile travel comparison',
                       'N/A, reviewed unarmed counterpart' if (row['source'], row['id']) in UNARMED_COUNTERPARTS
                       else travel.describe(travel_profiles.get((row.get('source'), row.get('id')), []))))
        if proof and 'center_falloff_percent' in proof:
            fields.extend([('raw weapon Damage', proof['raw_weapon_damage']),
                           ('center falloff percent', proof['center_falloff_percent'])])
        if proof and proof.get('damage_parts'):
            fields.append(('included damage warheads', proof['damage_parts']))
        if proof and proof.get('shot_damage'):
            fields.extend([('authored weapon damage', proof.get('authored_damage')),
                           ('damage sequence across the burst', proof['shot_damage']),
                           ('per-shot firepower modifiers', proof.get('firepower_modifiers_by_shot'))])
        if proof and proof.get('warmup_shots'):
            fields.extend([('authored weapon damage', proof.get('authored_damage')),
                           ('damage sequence before full spin-up', proof['warmup_shots']),
                           ('first full-stage shot (ticks after first shot)', proof['first_full_stage_shot_tick']),
                           ('cold nominal rate (damage/tick)', proof['cold_nominal_rate'])])
        if proof and proof.get('delivery_path'):
            fields.append(('launcher to impact delivery path', proof['delivery_path']))
        if proof and proof.get('target_scenario'):
            fields.append(('target scenario and alternative warheads (not summed)', proof['target_scenario']))
        if proof and proof.get('basis_note'):
            fields.append(('comparison convention', proof['basis_note']))
        if proof and proof.get('linear_pulse_falloffs'):
            fields.append(('pulse falloffs; rate uses full-damage region', proof['linear_pulse_falloffs']))
        if proof and proof.get('charge_ticks_bounds'):
            fields.append(('additional charge ticks, minimum/maximum; formula uses mean', proof['charge_ticks_bounds']))
        if proof and proof.get('impact_count', 1) > 1:
            fields.extend([('raw damage per impact', proof['damage_per_impact']),
                           ('scheduled impacts per shot', proof['impact_count']),
                           ('impact ticks after emission', proof['impact_ticks'])])
        if row.get('range_selection'):
            fields.append(('selected base range weapon', row['range_selection'].get('weapon')))
        text = '; '.join(k + ': ' + value(v) for k, v in fields)
        if proof and proof.get('dps_usable', True):
            charge = f" + {proof['charge_ticks']:g} charge" if proof.get('charge_ticks') else ''
            text += (f"; reviewed nominal calculation: {proof['damage']:g} × "
                     f"{proof.get('burst', 1)} / ({proof['reload']:g} + "
                     f"{sum(proof.get('burst_delays', [])):g}{charge}) = {proof['dps']:.6g} damage/tick")
        elif cycle:
            text += (f"; nominal cycle model: {cycle['damage']:g} × {cycle.get('cycle_shots', cycle['burst'])} / "
                     f"{cycle['cycle_mean']:g} mean ticks = {cycle['dps']:.6g} damage/tick; "
                     f"cycle bounds {cycle['cycle_min']:g}–{cycle['cycle_max']:g} ticks; DTA runtime applicability unverified")
        else:
            text += '; retained source rate (damage/source tick): ' + value(row.get('w_dps_raw', row.get('w_dps')))
            text += '; cycle not independently reconstructed here'
        text += '; model damage/tick eligible: ' + ('yes' if rd.eligible(row, 'w_dps') else 'no')
        if row.get('reference_base_eligible') is False:
            text += '; base-state exclusion: ' + row['reference_base_reason']
        text += '; evidence: ' + str(row.get('w_evidence', 'unassessed'))
        if row.get('w_evidence_reason'):
            text += '; ' + row['w_evidence_reason']
        if (row['source'], row['id']) in UNARMED_COUNTERPARTS:
            text += '; weapon range and damage/tick: N/A, reviewed unarmed counterpart'
        parts.append('<p><b>' + html.escape(str(row.get('source')) + ' / ' + str(row.get('id'))) +
                     '</b><br>' + html.escape(text) + '</p>')
    if not parts:
        return ''
    return ('<details><summary>Weapon calculation details</summary>'
            '<p>Raw source values are not directly comparable across games. The model normalizes each source '
            'before projection; the rate below is a source-local damage/tick estimate, not a sustained gameplay DPS claim. Unknown delays remain unavailable. '
            'Reviewed nominal cycles exclude armor, splash totals, travel and upgrades. '
            'The separate travel sample uses fixed endpoints without scatter, blockers or speed modifiers. '
            'Tick calls start at the first projectile update, not the firing order; seconds depend on game speed. '
            'Unmodeled guided/custom projectiles remain unavailable, and conditional slots are not summed.</p>' + ''.join(parts) + '</details>')


def _projection_context(actor, crows, dist, cdist, hero_context=None):
    row = crows.get(actor) or {}
    return hero_context if row.get("hero") and hero_context else (dist, cdist)


def emit(body, members, crows, assignment, attached, chassis_only, dist, cdist, counts, klass, led_arms, hero_context=None):
    for kind, title in SECTIONS:
        group = [a for a in members if crows[a]["type"] == kind]
        if not group:
            continue
        body.append(f'<h3>{title} <span class="muted">· {len(group)}</span></h3>')
        reference_details = []
        generic_details = []
        # ⭐ CLASS, RANGE and damage/tick added 2026-09-08 at the maintainer's request. The class is what
        # the virtual anchor will be derived from (EXTRAPOLATION_PROGRAM.md), so a row whose class
        # looks wrong is a finding BEFORE any anchor is signed — and range/damage were the two stats
        # a reference actually moves that the table never showed.
        # ⭐ BURST added 2026-09-12 (sixth column). Burst delays deliberately stay OUT of the map at
        # the maintainer's request — they are collected and reported separately, not shown here.
        # Keep the map itself to the direct actor stats requested by Aedis.
        # Mapping confidence, class labels and generic weapon/delivery evidence
        # are emitted below as a separate review section.
        body.append('<table><thead><tr><th>Cameo actor</th>'
                    '<th class="n">HP (now → reference)</th>'
                    '<th class="n">Speed (now → reference)</th>'
                    '<th class="n">Range (now → reference)</th>'
                    '<th class="n">Damage/cycle <span class="muted">= shot &#215; burst</span></th>'
                    '<th class="n">Reload (now → reference)</th>'
                    '<th class="n">Burst (now → reference)</th>'
                    '<th class="n">Burst delay <span class="muted">t/shot, recovered</span></th>'
                    '<th class="n">DPS verifier</th>'
                    '<th class="n">Cost (now → reference)</th>'
                    '</tr></thead><tbody>')
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
            selected_dist, selected_cdist = _projection_context(
                a, crows, dist, cdist, hero_context)
            tgt = {stat: estimate_cell(rows, c, stat, selected_dist, selected_cdist, len(srcs))
                   for stat in ('hp', 'speed', 'cost', 'w_range', 'w_dps')}
            # ⭐ R1, 2026-09-12: the WEAPON COMPONENTS are the referenced inputs and total DPS
            # is only a guard rail. Damage and reload therefore get their own columns, and the
            # old `damage/tick` column becomes the verifier — it reports whether composing the
            # components produces something extreme, or something that disagrees with what the
            # DPS projection independently claims (the mammoth was 1.43x apart).
            for stat in rt.COMPONENT_STATS:
                if stat == 'w_burst':
                    continue
                tgt[stat] = estimate_cell(rows, c, stat, selected_dist, selected_cdist,
                                          len(srcs), flag_change=c.get(stat))
            # ⭐ BURST added 2026-09-12 at the maintainer's request: "update the reference map to
            # also display burst since that's important and if it should change I should know it
            # in the big reference map table". It carries `flag_change` because `Burst` may not be
            # touched without explicit permission, so the actionable fact is whether the target
            # MOVES it, not the number — and the raw target rounds, which hid that distinction.
            tgt['w_burst'] = estimate_cell(rows, c, 'w_burst', selected_dist, selected_cdist,
                                           len(srcs), flag_change=c.get('w_burst'))
            # ⭐ LAW 3a.3 FIRST, #397's ROUTING SECOND. Master routes every weapon cell of a
            # multi-armament actor to "see per-armament components", which is a better answer than
            # WITHHELD but still not the one the maintainer asked for: *"the combined DPS is what
            # counts and it is what should be DISPLAYED in the reference data"*. So where the sum
            # is provably honest it is shown here, and the routing text remains the fallback for
            # every cell that genuinely has no single value - reload, burst, burst delay, the DPS
            # verifier, and any actor whose guns cannot be summed.
            #
            # ⚠ ORDER MATTERS: `combined_range_cell` reads `tgt["w_range"]`, and the routing
            # branch below OVERWRITES `tgt` with link text. Compute both cells first.
            ctype_a = c.get("type")
            withheld_actor = c.get("weapon_model_eligible") is False
            combined = (combined_damage_cell(a, c, rows, selected_dist, selected_cdist, ctype_a)
                        if withheld_actor else None)
            shared_range = (combined_range_cell(a, tgt["w_range"]) if withheld_actor else None)
            per_armament = has_structured_armament_components(a)
            if per_armament:
                route = ('<span class="muted" title="actor-level weapon folding can select a '
                         'different peer armament">see per-armament components</span>')
                for stat in ("w_range", "w_damage", "w_reload", "w_burst", "w_dps"):
                    tgt[stat] = route
                burst_delay = route
                dps_verifier = route
            else:
                burst_delay = burst_delay_cell(c, rows)
                dps_verifier = dps_verifier_cell(c, rows, tgt)
            damage_cell = combined or (
                f'{component_num(c, "w_damage")} {burst_note(c)}'
                f'{arm_note(a, led_arms, c.get("weapon_model_eligible"))} '
                f'<span class="muted">\u2192</span> {tgt["w_damage"]}')
            range_cell = shared_range or (
                f'{component_num(c, "w_range")} <span class="muted">\u2192</span> {tgt["w_range"]}')
            note = ' <span class="tag">chassis-only</span>' if a in chassis_only else ""
            if c.get('hero'):
                note += ' <span class="tag">hero-only model</span>'
            empty = '<span class="muted">—</span>'
            reference_details.append((a, klass.get(a) or "—", len(srcs), chips or empty))
            generic = weapon_calculation_details(rows, a)
            if generic:
                generic_details.append((a, generic))
            body.append(
                f'<tr><td><code>{html.escape(a)}</code>{note}{flag}</td>'
                f'<td class="n">{num(c.get("hp"))} <span class="muted">→</span> {tgt["hp"]}</td>'
                f'<td class="n">{num(c.get("speed"))} <span class="muted">→</span> {tgt["speed"]}</td>'
                f'<td class="n">{range_cell}</td>'
                f'<td class="n">{damage_cell}</td>'
                f'<td class="n">{component_num(c, "w_reload")} <span class="muted">→</span> {tgt["w_reload"]}</td>'
                f'<td class="n">{component_num(c, "w_burst")} <span class="muted">→</span> {tgt["w_burst"]}</td>'
                f'<td class="n">{burst_delay}</td>'
                f'<td class="n">{dps_verifier}</td>'
                f'<td class="n">{num(c.get("cost"))} <span class="muted">→</span> {tgt["cost"]}</td></tr>')
        body.append("</tbody></table>")
        if reference_details:
            body.append('<h4>Reference mapping and generic group evidence</h4>')
            body.append('<p class="lede">The table above stays focused on HP, speed, range, DPS and cost. '
                        'This section keeps class/mapping provenance and the generic weapon, projectile, '
                        'spread, falloff and delivery evidence separate from the actor stats.</p>')
            body.append('<table><thead><tr><th>Cameo actor</th><th>class</th>'
                        '<th class="n">assigned refs</th><th>reference units chosen</th></tr></thead><tbody>')
            for actor, actor_class, ref_count, chips in reference_details:
                body.append(f'<tr><td><code>{html.escape(actor)}</code></td>'
                            f'<td class="cls">{html.escape(actor_class)}</td>'
                            f'<td class="n">{ref_count}</td><td>{chips}</td></tr>')
            body.append('</tbody></table>')
            for actor, details in generic_details:
                body.append(f'<div><code>{html.escape(actor)}</code>{details}</div>')
        # ⛔ `members` HERE WOULD RE-EMIT THE WHOLE BAND ONCE PER SECTION. This call sits inside
        # the `for kind, title in SECTIONS` loop, so passing the band printed every actor's block
        # again under infantry, vehicles, aircraft and ships alike — 155 blocks for 35 actors.
        # `group` is this section's actors, which is what the heading above it claims.
        emit_armament_pairing(body, group, attached, dist, cdist, crows, hero_context)


# ── PER-ARMAMENT REFERENCES ──────────────────────────────────────────────────────────────────
# ⛔ THE MAINTAINER ASKED FOR EXACTLY THIS (2026-09-13): *"the reference map needs to show each
# weapon per actor and try to find the weapon for each reference. If the reference unit does not
# have the weapon it should not vote on it."* The table above shows ONE folded weapon per actor,
# which on `td_gdi_firehawk` means the bomb is reported at the Sidewinders' range.
#
# It READS `armament_pairing.json` and computes nothing — the mechanism, its role vocabulary and
# its measurements live in `armament_roles.py` and `docs/design/ARMAMENT_PAIRING.md`.
_PAIRING = []
_SINGLETON_BINDINGS = []
SINGLETON_SELF_VOTE_STATS = (
    "hp", "speed", "cost", "w_range", "w_damage", "w_reload", "w_burst", "w_dps",
)


def singleton_self_vote_bindings():
    """Hash-pinned frozen rows whose one priced armament is independently identified."""
    if _SINGLETON_BINDINGS:
        return _SINGLETON_BINDINGS[0]
    doc = json.loads(SINGLETON_SELF_VOTES.read_text(encoding="utf-8"))
    if doc.get("schema") != 1:
        raise ValueError("singleton self-vote receipt has an unsupported schema")
    snapshot = doc.get("immutable_snapshot") or {}
    snapshot_path = ROOT / str(snapshot.get("path") or "")
    if not snapshot_path.is_file():
        raise ValueError("singleton self-vote receipt does not match the immutable snapshot")
    snapshot_raw = snapshot_path.read_bytes()
    if hashlib.sha256(snapshot_raw).hexdigest() != snapshot.get("sha256"):
        raise ValueError("singleton self-vote receipt does not match the immutable snapshot")
    snapshot_doc = json.loads(snapshot_raw)
    frozen_rows = {row.get("id"): row for row in snapshot_doc.get("rows", ())}
    bindings = doc.get("bindings")
    if not isinstance(bindings, dict) or not bindings:
        raise ValueError("singleton self-vote receipt has no bindings")
    source_ledgers = doc.get("source_ledgers") or {}
    for actor, binding in bindings.items():
        source = source_ledgers.get(binding.get("source_ledger")) or {}
        source_hash = str(source.get("sha256") or "")
        source_key = f'docs/balance/{binding.get("source_ledger")}'
        if (not re.fullmatch(r"[0-9a-f]{64}", source_hash)
                or snapshot_doc.get("inputs", {}).get(source_key) != source_hash):
            raise ValueError(f"singleton self-vote source hash does not match for {actor}")
        values = binding.get("snapshot_values")
        if not isinstance(values, dict) or set(values) != set(SINGLETON_SELF_VOTE_STATS):
            raise ValueError(f"singleton self-vote values are incomplete for {actor}")
        frozen = frozen_rows.get(actor)
        if frozen is None or any(frozen.get(stat) != values[stat]
                                 for stat in SINGLETON_SELF_VOTE_STATS):
            raise ValueError(f"singleton self-vote values do not match for {actor}")
    _SINGLETON_BINDINGS.append(bindings)
    return bindings


def singleton_self_vote_row(actor, main_rows, cdist):
    """Return one admitted frozen row, or fail if its bound armament shape moved."""
    binding = singleton_self_vote_bindings().get(actor)
    if binding is None:
        return None
    if len(main_rows) != 1:
        raise ValueError(f"singleton self-vote armament count moved for {actor}")
    main = main_rows[0]
    if binding.get("weapon") != main.get("weapon") or binding.get("slot") != main.get("slot"):
        raise ValueError(f"singleton self-vote armament binding moved for {actor}")
    frozen = getattr(cdist, "cameo_votes", None) or {}
    row = frozen.get(actor)
    if row is None:
        raise ValueError(f"singleton self-vote row is absent for {actor}")
    for stat, expected in binding["snapshot_values"].items():
        if row.get(stat) != expected:
            raise ValueError(f"singleton self-vote {stat} moved for {actor}")
    return row


def _validate_pairing_document(doc, expected_inputs):
    if not isinstance(doc, dict) or doc.get("schema") != bap.PAIRING_SCHEMA:
        raise ValueError("armament_pairing.json has an unsupported schema; rebuild it")
    actors = doc.get("actors")
    if not isinstance(actors, dict) or not actors:
        raise ValueError("armament_pairing.json has no actor coverage; rebuild it")
    stats = doc.get("stats")
    if not isinstance(stats, dict) or stats.get("actors") != len(actors):
        raise ValueError("armament_pairing.json actor coverage metadata is inconsistent")
    recorded = doc.get("inputs")
    if not isinstance(recorded, dict) or recorded != expected_inputs:
        missing = sorted(set(expected_inputs) - set(recorded or {}))
        extra = sorted(set(recorded or {}) - set(expected_inputs))
        drift = sorted(key for key in set(expected_inputs) & set(recorded or {})
                       if expected_inputs[key] != recorded[key])
        detail = "; ".join(part for part in (
            f"missing {missing}" if missing else "",
            f"unexpected {extra}" if extra else "",
            f"changed {drift}" if drift else "",
        ) if part)
        raise ValueError(f"armament_pairing.json input fingerprints are incomplete or stale: {detail}")
    return doc


def pairing_document():
    """The per-armament pairing artifact, REFUSED when its inputs have moved since it was built.

    ⛔ A RECORDED HASH THAT NOBODY RE-CHECKS IS A COMMENT (Astra, PR #375 blocker 4). The artifact
    names its complete reproducibility closure and each input's sha256; if the exact set or any
    hash differs now, the pairing on disk describes a corpus that no longer exists and the map
    would render it as current evidence. Stale evidence is worse than missing evidence, because it
    looks the same as the real thing — so this raises rather than degrades.

    A document with no `inputs` block at all is a pre-fingerprint artifact and is refused for the
    same reason: it cannot prove it is fresh. Regenerate with
    `python tools/balance/build_armament_pairing_report.py --write`.
    """
    if not _PAIRING:
        path = ROOT / "docs/balance/derived/armament_pairing.json"
        if not path.is_file():
            raise ValueError("armament_pairing.json is missing; rebuild it with --write")
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("armament_pairing.json is unreadable or malformed") from exc
        _PAIRING.append(_validate_pairing_document(doc, bap.input_fingerprints(ROOT)))
    return _PAIRING[0]


def has_structured_armament_components(actor):
    entry = pairing_document().get("actors", {}).get(actor)
    return bool(entry and any("pairs" in source for source in entry["sources"].values()))


def _short_source(name):
    return name.replace("OpenRA ", "").replace("Twisted Insurrection", "Twisted Ins.")


def _range_cell(view):
    """Always the WDist figure; `c` marks a value converted from TS cells."""
    if view.get("range_wdist") is None:
        return "&#8212;"
    return "%s%s" % (f'{round(view["range_wdist"]):,}',
                     "c" if view.get("range_unit") == "cells" else "")


def _armament_rows(entry):
    """The armaments worth a row: the BASELINE firing set, strongest first within each role.

    An upgrade-gated twin (`Armament@Upgrade`, `@AdvancedMissileTargeting`) is the same gun with a
    different warhead and would triple the table without adding a reference; `baseline` is the flag
    `armament_roles.view` already sets for exactly this. If an actor has no baseline armament at
    all, everything it has is shown rather than nothing.
    """
    arms = [a for a in entry["armaments"] if a.get("baseline")] or list(entry["armaments"])
    # ⚠ ONE ROW PER WEAPON, NOT PER SLOT. `Armament@PRIMARY` and `Armament@GARRISONED` are the
    # same gun fired from two places, so keying on the slot printed `OIFlamer` and the Hind's
    # chaingun twice. The weapon NAME is the identity the pairing votes on.
    seen, uniq = set(), []
    for a in arms:
        key = (a.get("weapon"), a.get("role"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(a)
    order = {role: i for i, role in enumerate(entry["roles"])}
    return sorted(uniq, key=lambda a: (order.get(a["role"], 99), -(a["damage_per_cycle"] or 0)))


def _peer_row_for(attached_rows, source, peer_id):
    """The assigned peer ROW behind a pairing vote — needed for its source and TYPE.

    `armament_pairing.json` records which peer WEAPON was paired, not the row it came from, and
    the projection needs the row: the normalising population is picked by the peer's own type
    ("overall" plus e.g. "vehicle"). Matched on source first and id second, because a source can
    contribute a family of rows and any of them carries the same type.
    """
    same = [r for r in attached_rows if r.get("source") == source]
    for r in same:
        if (r.get("id") or "") == peer_id:
            return r
    return same[0] if same else None


ARMAMENT_COMPONENTS = {
    "w_range": "range",
    "w_damage": "damage_per_cycle",
    "w_reload": "weapon_reload",
    "w_burst": "weapon_burst",
    "w_dps": "rate",
}


# ⛔ WHICH DOMAIN EACH ROLE CAN REACH. `both` is not a third domain - it is a weapon that
# reaches BOTH, which is why a plain set intersection is the right test and a role-equality test
# is not.
_ROLE_DOMAINS = {"ground": frozenset("G"), "air": frozenset("A"), "both": frozenset("GA")}

_VALID_TARGETS = {}


def _valid_targets(weapon):
    """The weapon own `ValidTargets` tokens, or None when it declares none.

    ⚠ An ABSENT `ValidTargets` is not an empty one - the engine defaults it - so this returns
    None and the caller falls back to the coarse role rather than concluding "hits nothing".
    """
    if weapon in _VALID_TARGETS:
        return _VALID_TARGETS[weapon]
    try:
        node = _ruleset().resolve_weapon(weapon)
    except Exception:
        node = None
    tokens = None
    if node is not None:
        child = next((c for c in node.children if c.key == "ValidTargets"), None)
        if child is not None and child.value:
            tokens = frozenset(t.strip().lower() for t in str(child.value).split(",") if t.strip())
    return _VALID_TARGETS.setdefault(weapon, tokens)


def firing_together(actor, entry):
    """The armaments whose damage may honestly be ADDED, or None.

    Three filters, and each one exists because skipping it produces a number that is wrong in a
    specific, checkable way:

    1. AS BUILT. Upgrade-gated guns are excluded (`as_built_weapons`), so no unit is priced with
       hardware it has not bought.

    2. ⛔ AN AA SPLIT IS ONE WEAPON (DESIGN §3a.1). `td_gdi_apc_apcgun` and
       `td_gdi_apc_apcgun_AA` are a single gun that OpenRA forced into two armaments because one
       armament cannot have 1.5x reach against air. ADDING them would double the APC firepower
       outright. Five actors in the classic four alone carry such a twin - the two APCs, the
       Allied heavy AA tank, the flak truck, and the Humvee Mk II with TWO of them - so this is
       the difference between a combined figure and a fabricated one. The twin test is the same
       one `doc_claims.aa_split_pairs_compliant` uses: an `_AA` name whose base weapon exists.

    3. ⛔ THEY MUST BE ABLE TO HIT THE SAME TARGET. The test is that the INTERSECTION of every
       armament domain is non-empty: `ground` + `both` share the ground and sum; `ground` + `air`
       share nothing. Connectivity would be the WRONG test - ground/air/both is a connected chain
       with no common target.

       ⭐ A DISJOINT SET IS NOT A DEFECT, IT IS A DIFFERENT KIND OF UNIT, so it returns the
       sentinel "exclusive" rather than None and the caller says which (maintainer, 2026-09-14,
       on the depth-charge boats): *"Those should be regarded like the anti air weapons since
       they are mutually exclusive with their other weapon ... it must resolve to the same cost
       for both weapons for the same actor individually as if they were twin units (imagine one
       ship with only rockets and the same ship with only depth charges) ... but the DPS is never
       summed up for those!"* `ra1_allies_destroyer` carries a missile for `Ground, Water, Air`
       and a depth charge for `Underwater, Submarine`: two weapons that can never engage one
       target, so each is resolved alone and the actor pays once.
    """
    built = as_built_weapons(actor)
    if built is None:
        return None
    arms = [a for a in _armament_rows(entry) if a.get("weapon") in built]
    if len(arms) != len(built):                 # a priced armament the pairing never saw
        return None
    twins = {w for w in built if str(w).endswith("_AA") and str(w)[:-3] in built}
    arms = [a for a in arms if a.get("weapon") not in twins]
    if len(arms) < 2:
        return None
    # ⛔ `ValidTargets` FIRST, THE ROLE ONLY AS A FALLBACK. The pairing role vocabulary is
    # ground/air/both and has NO underwater domain, so a depth charge declaring
    # `Underwater, Submarine` is filed as "ground" and looks like it shares a target with the
    # ship cannon beside it. It cannot: the two never engage the same thing. Reading the weapon
    # declaration directly is what separates `ra1_allies_destroyer` (missile Ground/Water/Air vs
    # depth charge Underwater/Submarine - exclusive) from `td_gdi_humveemkii` (both Ground/Water,
    # genuinely simultaneous). The role stays as the fallback for a weapon that declares nothing.
    targets = [_valid_targets(a.get("weapon")) for a in arms]
    if all(t for t in targets):
        common = set(targets[0])
        for t in targets[1:]:
            common &= t
        return arms if common else "exclusive"
    domains = [_ROLE_DOMAINS.get(a.get("role")) for a in arms]
    if any(d is None for d in domains):
        return None
    common = frozenset("GA")
    for d in domains:
        common &= d
    return arms if common else "exclusive"


def combined_armament_totals(actor, attached_rows, dist, cdist, ctype):
    """⭐ LAW 3: ARMAMENTS THAT FIRE TOGETHER SUM, and the map must show the total.

    Maintainer, 2026-09-14: *"for the balance formula you need to count both weapons if they are
    truly activated at the same time ... the combined DPS is what counts and it is what should be
    displayed in the reference data instead of the WITHHELD status!"*

    Returns `(now, reference, guns, sources_used)` or None. None means the sum would be a lie,
    and there are three separate ways for that to be true - each one a refusal, not a gap:

      * the simultaneous set is not PROVEN. `simultaneous_armaments` reads the resolved yaml and
        reports a bound only for simple `C` / `!C` conditions; a compound expression comes back
        unknown. Summing a set nobody proved is how `x4` got onto the mammoth in the first place.
      * the baseline armaments and that bound DISAGREE in size. The baseline set is the one that
        fires with no upgrades held, so when its size equals the bound the two descriptions agree
        and the set is known. When they do not, something is gated in a way this cannot read.
      * any one armament has no target. A PARTIAL sum is the worst of the three outcomes: it
        looks like a complete answer and reads low, so a unit would be priced as though one of
        its guns were free. Better to withhold the row than to under-report it.

    ⚠ DAMAGE PER CYCLE SUMS; CADENCE DOES NOT. Reload, burst and burst delay stay withheld
    above, because two guns firing together have two cadences and no single one describes them.
    """
    entry = pairing_document().get("actors", {}).get(actor)
    if entry is None:
        return None
    arms = firing_together(actor, entry)
    if arms is None or arms == "exclusive":
        return arms
    # ⭐ ONE CYCLE PER ACTOR IS THE CONVENTION (maintainer, 2026-09-14): *"the cycle time is the
    # same for both! Reload delay + sum of burst delays must be identical between weapons."*
    # Verified in the tree: the Mammoth runs 80/80, the Sheridan 64/64/64 with a Burst-4 chaingun
    # landing on the same cycle as its cannon, the Battle Tank 72/72. When it holds, per-cycle
    # damage adds directly and the sum is proportional to the summed DPS.
    #
    # ⛔ WHEN IT DOES NOT HOLD, DAMAGE PER CYCLE HAS NO SINGLE MEANING and adding two different
    # cycles' worth of damage would produce a figure describing no interval at all. 8 of the 23
    # multi-weapon actors in the classic four are in that state, so the cell reports the breach
    # instead of a number - the same way the range cell reports a 3a.2 breach.
    cycles = {a.get("cycle") for a in arms}
    if len(cycles) != 1 or None in cycles:
        return "cycles_differ"
    votes_by_role = collections.defaultdict(list)
    for source, info in entry["sources"].items():
        for pair in info.get("pairs", ()):
            votes_by_role[pair["role"]].append((source, pair))
    now_total, ref_total = 0.0, 0.0
    sources_used = set()
    for main in arms:
        now = main.get("damage_per_cycle")
        role = main.get("role")
        if not now or role is None:
            return None
        # ⭐ THE NOW TOTAL NEVER DEPENDS ON THE REFERENCE. It is arithmetic over our OWN yaml,
        # so a gun no source happens to carry cannot make the unit's current firepower unknowable.
        # Only the REFERENCE half abstains, and it abstains WHOLE: a partial projection reads low
        # while looking complete, which is the one failure mode worth refusing outright.
        now_total += now
        cast = [(src, pair) for src, pair in votes_by_role.get(role, ())
                if pair["cameo"].get("weapon") == main["weapon"]]
        if not cast or ref_total is None:
            ref_total = None
            continue
        peer_votes = [(_peer_row_for(attached_rows, source, entry["sources"][source].get("peer")),
                       pair["peer"].get("damage_per_cycle")) for source, pair in cast]
        target, _used = rt.armament_target(peer_votes, dist, cdist, ctype)
        if not target:
            ref_total = None
            continue
        ref_total += target
        sources_used.update(source for source, _pair in cast)
    return now_total, ref_total, len(arms), len(sources_used)


def combined_damage_cell(actor, cameo_row, attached_rows, dist, cdist, ctype):
    """The Damage/cycle cell for a multi-gun actor: the SUM, where the sum is honest.

    Falls back to the old WITHHELD marker by returning None, so the caller keeps one code path.
    """
    totals = combined_armament_totals(actor, attached_rows, dist, cdist, ctype)
    if totals is None:
        return None
    if totals == "exclusive":
        return ('<span class="muted" title="these weapons can never engage the same target - a '
                'depth charge reaches Underwater/Submarine and the ship gun does not - so their '
                'damage is NOT summed. Each is resolved on its own, as though the actor were two '
                'twin units sharing one HP, speed and cost; see the per-armament block below.'
                '">resolved per weapon <b class="warn">not summed</b></span>')
    if totals == "cycles_differ":
        return ('<span class="muted" title="these armaments fire together but do NOT share one '
                'attack cycle, so there is no interval their damage can be added over. One cycle '
                'per actor is the convention (reload + burst delays identical between weapons); '
                'this actor breaks it, and that is the thing to fix.">WITHHELD '
                '<b class="warn">cycles differ</b></span>')
    now, ref, guns, used = totals
    if ref is None:
        return (f'<span data-v="{now}" title="the {guns} armaments this actor fires at the same '
                f'time AS BUILT, summed over their one shared cycle">{now:,.0f}'
                f'<small class="evidence">combined, {guns} guns</small></span> '
                f'<span class="muted">\u2192</span> '
                f'<span class="muted" title="at least one of these armaments has no reference '
                f'weapon in any source, and a PARTIAL sum would read low while looking '
                f'complete">no complete reference</span>')
    ratio = (f' <b class="warn" title="needs explicit maintainer permission">{ref / now:.2f}x</b>'
             if now and abs(ref / now - 1) > 0.005 else '')
    return (f'<span data-v="{now}" title="the {guns} armaments this actor fires at the same time '
            f'AS BUILT, summed - combined damage per cycle is what the unit actually delivers. '
            f'Upgrade-gated guns are excluded: they are not part of the unit being priced.'
            f'">{now:,.0f}'
            f'<small class="evidence">combined, {guns} guns</small></span> '
            f'<span class="muted">→</span> '
            f'<span data-v="{ref}" title="each armament projected separately from the sources '
            f'that carry a weapon in its role, then summed - same coordinates and the same frozen '
            f'ruler as every other target here">{ref:,.0f}'
            f'<small class="evidence">{used} source(s)</small></span>{ratio}')


def combined_range_cell(actor, tgt_range):
    """⭐ LAW 2 MAKES THIS CELL WELL-DEFINED. Every weapon that can hit the same target shares
    one range, so a multi-gun actor normally has ONE reach and withholding it said nothing true.
    Reported only when the simultaneous armaments actually agree; a disagreement is a law
    violation and keeps the WITHHELD marker rather than being averaged away.
    """
    entry = pairing_document().get("actors", {}).get(actor)
    if entry is None:
        return None
    arms = firing_together(actor, entry)
    if arms is None or arms == "exclusive":
        # Mutually exclusive weapons legitimately carry DIFFERENT reaches - a depth charge is
        # short and its ship's missile is long - so there is no single actor range to show.
        return None
    reaches = {a.get("range_wdist") for a in arms}
    if len(reaches) != 1 or None in reaches:
        return None
    reach = reaches.pop()
    return (f'<span data-v="{reach}" title="every armament that fires together shares this reach '
            f'(DESIGN §3a.2)">{reach:,.0f}</span> <span class="muted">→</span> {tgt_range}')


def _armament_component_target(entry, cast, attached_rows, dist, cdist, ctype, stat,
                               cameo_vote=None):
    """One role-paired component target, without reusing the actor-level selected weapon."""
    field = ARMAMENT_COMPONENTS[stat]
    votes = [(_peer_row_for(attached_rows, source, entry["sources"][source].get("peer")),
              pair["peer"].get(field)) for source, pair in cast]
    return rt.armament_target(votes, dist, cdist, ctype, stat, cameo_vote)


def _snap_armament_component(stat, target):
    """Snap writeable fields to their one-unit grids; refuse fractional discrete counts."""
    if target is None:
        return None
    snapped = round(target)
    if stat in ("w_burst", "w_burst_delay") and not math.isclose(
            float(target), snapped, rel_tol=0, abs_tol=1e-9):
        return None
    return snapped


def _armament_component_cell(now, raw_target, target, used, nsources, stat,
                             has_cameo_vote):
    """Render one per-armament component, with integer writeback visibility."""
    if raw_target is None:
        return '<span class="muted" title="paired weapons could not produce this component">abstains</span>'
    if target is None:
        return (f'<span class="warn" title="discrete component target {raw_target:g} is not an '
                f'integer and cannot be written">HOLD {raw_target:g}</span>')
    rendered = f'{target:,.0f}'
    evidence = f'{used} of {nsources} peer sources' + (' + Cameo self' if has_cameo_vote else '')
    ratio = ""
    if now and abs(float(target) / float(now) - 1) > 0.005:
        ratio = (f' <b class="warn" title="needs explicit maintainer permission">'
                 f'{float(target) / float(now):.2f}x</b>')
    return (f'<span data-v="{target}" title="role-paired component projection; unrounded '
            f'{raw_target:g}; {evidence}">'
            f'{rendered}<small class="evidence">{evidence}</small></span>{ratio}')


def _mean_weapon_burst_delay(view):
    burst = int(view.get("weapon_burst") or 1)
    delays = list(view.get("weapon_burst_delays") or ())
    if burst <= 1:
        return None
    if not delays:
        return 5.0
    if len(delays) == 1:
        return float(delays[0])
    if len(delays) == burst - 1:
        return sum(float(value) for value in delays) / (burst - 1)
    return None


def _armament_burst_delay_target(cast):
    values = [_mean_weapon_burst_delay(pair["peer"]) for _source, pair in cast]
    values = sorted(value for value in values if value is not None)
    if not values:
        return None, 0
    mid = len(values) // 2
    target = values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2
    return target, len(values)


def _armament_burst_delay_cell(main, raw_target, target, used):
    current = _mean_weapon_burst_delay(main)
    left = f'{current:.0f}' if current is not None else '<span class="muted">—</span>'
    if raw_target is None:
        return left + ' <span class="muted">→ —</span>'
    if target is None:
        return left + f' <span class="muted">→</span> <span class="warn">HOLD {raw_target:g}</span>'
    return (f'{left} <span class="muted">→</span> {target:.0f}'
            f'<small class="evidence">{used} authored</small>')


def _armament_dps_guard_cell(main, targets, dps_target, burst_delay_target,
                             rejected_component=False):
    """Verify composed authored components only when they reproduce the modeled Cameo cycle."""
    if rejected_component:
        return ('<span class="muted" title="a fractional burst or burst-delay proposal is on '
                'HOLD; the verifier cannot substitute the current value">WITHHELD</span>')
    authored_cycle = ar.cycle_ticks(
        main.get("weapon_reload"), main.get("weapon_burst"),
        main.get("weapon_burst_delays") or ())
    if (authored_cycle is None or main.get("cycle") is None
            or abs(float(authored_cycle) - float(main["cycle"])) > 1e-9):
        return ('<span class="muted" title="modeled actor cycle contains charge, jitter or other '
                'timing beyond the authored weapon components">WITHHELD</span>')
    current = {
        "w_damage": main.get("damage_per_cycle"),
        "w_burst": main.get("weapon_burst"),
        "w_reload": main.get("weapon_reload"),
        "w_dps": main.get("rate"),
    }
    guard = rt.dps_guard(current, targets, dps_target, burst_delay_target)
    if guard is None:
        return '<span class="muted">WITHHELD</span>'
    ratio = f'{guard["composed_ratio"] * 100:.0f}%'
    if guard["verdict"] == "ok":
        return f'{guard["composed_dps"]:.0f} <span class="tag">{ratio} of now</span>'
    return f'{guard["composed_dps"]:.0f} <b class="warn">{guard["verdict"].upper()} {ratio}</b>'


def emit_armament_pairing(body, members, attached, dist, cdist, crows, hero_context=None):
    """One block per actor in this class that fires in more than one targeting role.

    ⭐ EACH ARMAMENT NOW CARRIES ITS OWN TARGET (maintainer, 2026-09-13: "td gdi battle tank and
    mammoth tank are now withheld" -> wire the pairs in). The actor-level damage cell above stays
    WITHHELD for these rows and that is correct — there is no single honest number for a unit that
    fires a cannon and an anti-air missile. The number lives here instead, one per weapon, each
    projected only from the sources that carry a weapon in that role."""
    actors = pairing_document().get("actors", {})
    # ⛔ MULTI-ROLE WAS THE WRONG GATE AND HID 17 OF THE WITHHELD ACTORS. The actor-level cell is
    # withheld for carrying more than one ARMAMENT, not more than one ROLE, so a destroyer with
    # four ground guns was blanked above and had no block down here either. Both conditions admit
    # a block now: a multi-role actor because its folded number mixes two kinds of gun, and any
    # withheld actor because this section is the only place its damage can be reported at all.
    rows = [(a, actors[a]) for a in members
            if a in actors
            and any("pairs" in s for s in actors[a]["sources"].values())]
    if not rows:
        return
    body.append('<h4>Per-armament references &mdash; one weapon, one vote</h4>')
    body.append('<p class="lede">Here each armament finds its own '
                'reference weapon and gets its own target, and a source that does not carry a '
                'weapon in that role does not vote on it. '
                'This also covers a one-gun Cameo actor whose reference actor has several guns; '
                'the actor-level fold may otherwise select the wrong peer weapon. '
                '<b>=</b> exact role match &middot; <b>~</b> a dual-role weapon stood in. '
                'An unproven role abstains rather than voting. '
                'Air is never paired with ground. A <code>c</code> on a range marks a value '
                'converted from TS cells (1 cell = 1024 WDist). The reference column is projected '
                'through the same coordinates and the same frozen ruler as every other target on '
                'this page.</p>')
    for actor, entry in rows:
        votes = collections.defaultdict(list)
        for source, info in entry["sources"].items():
            for pair in info.get("pairs", ()):
                votes[pair["role"]].append((source, pair))
        n = sum(1 for s in entry["sources"].values() if "pairs" in s)
        body.append(f'<div><code>{html.escape(actor)}</code>')
        arows = attached.get(actor) or []
        ctype = (crows.get(actor) or {}).get("type")
        selected_dist, selected_cdist = _projection_context(
            actor, crows, dist, cdist, hero_context)
        body.append('<table><thead><tr><th>role</th><th>Cameo weapon</th>'
                    '<th class="n">range now → ref</th><th class="n">damage/cycle now → ref</th>'
                    '<th class="n">reload now → ref</th><th class="n">burst now → ref</th>'
                    '<th class="n">burst delay now → ref</th><th class="n">DPS verifier</th>'
                    '<th>voters</th></tr></thead><tbody>')
        # ⭐ ONE ROW PER ARMAMENT, NOT PER ROLE. Taking the strongest weapon of each role was a
        # second fold wearing the first one's clothes: `ra1_allies_destroyer` has four ground
        # armaments and would have reported one. An armament that drew no pair still gets its row
        # and says it abstains, because "no reference has this weapon" is a finding.
        main_rows = _armament_rows(entry)
        for main in main_rows:
            role = main.get("role")
            role_label = role or "unknown / unproven"
            cast = ([] if role is None else
                    [(src, pair) for src, pair in votes.get(role, ())
                     if pair["cameo"].get("weapon") == main["weapon"]])
            if cast:
                chips = " ".join(
                    '<span class="tag" title="{t}">{mark} {src} &middot; {w}</span>'.format(
                        t=html.escape("%s — %s" % (entry["sources"][source]["peer"],
                                                   pair["peer"]["weapon"])),
                        mark=("=" if pair["exact"]
                              else "?" if pair["peer"]["role"] is None else "~"),
                        src=html.escape(_short_source(source)),
                        w=html.escape(str(pair["peer"]["weapon"])))
                    for source, pair in cast)
                tally = f'<b>{len(cast)} of {n}</b> {chips}'
            elif role is None:
                tally = ('<span class="muted">unknown targeting role &mdash; this armament '
                         'abstains and has no reference target</span>')
            else:
                tally = ('<span class="muted">no source carries a weapon in this role &mdash; '
                         'this armament abstains and has no reference target</span>')
            self_row = singleton_self_vote_row(actor, main_rows, selected_cdist)
            has_self = bool(self_row and self_row.get("weapon_model_eligible") is not False)
            targets = {}
            cells = {}
            rejected_component = False
            current = {
                "w_range": main.get("range_wdist"),
                "w_damage": main.get("damage_per_cycle"),
                "w_reload": main.get("weapon_reload"),
                "w_burst": main.get("weapon_burst"),
            }
            for stat in ("w_range", "w_damage", "w_reload", "w_burst"):
                cameo_vote = self_row.get(stat) if has_self else None
                raw_target, used = _armament_component_target(
                    entry, cast, arows, selected_dist, selected_cdist, ctype, stat,
                    cameo_vote)
                target = _snap_armament_component(stat, raw_target)
                rejected_component |= raw_target is not None and target is None
                targets[stat] = target
                cells[stat] = _armament_component_cell(
                    current[stat], raw_target, target, used, n, stat,
                    has_self and stat != "w_burst")
            dps_vote = self_row.get("w_dps") if has_self else None
            dps_target, _dps_used = _armament_component_target(
                entry, cast, arows, selected_dist, selected_cdist, ctype, "w_dps",
                dps_vote)
            raw_burst_delay, delay_used = _armament_burst_delay_target(cast)
            burst_delay_target = _snap_armament_component(
                "w_burst_delay", raw_burst_delay)
            rejected_component |= raw_burst_delay is not None and burst_delay_target is None
            body.append(f'<tr><td class="cls">{html.escape(role_label)}</td>'
                        f'<td><code>{html.escape(str(main["weapon"]))}</code></td>'
                        f'<td class="n">{_range_cell(main)} <span class="muted">→</span> {cells["w_range"]}</td>'
                        f'<td class="n">{num(main["damage_per_cycle"])} <span class="muted">→</span> {cells["w_damage"]}</td>'
                        f'<td class="n">{num(main.get("weapon_reload"))} <span class="muted">→</span> {cells["w_reload"]}</td>'
                        f'<td class="n">{num(main.get("weapon_burst"))} <span class="muted">→</span> {cells["w_burst"]}</td>'
                        f'<td class="n">{_armament_burst_delay_cell(main, raw_burst_delay, burst_delay_target, delay_used)}</td>'
                        f'<td class="n">{_armament_dps_guard_cell(main, targets, dps_target, burst_delay_target, rejected_component)}</td>'
                        f'<td>{tally}</td></tr>')
        body.append('</tbody></table></div>')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--faction", nargs="+", required=True)
    ap.add_argument("--out", default="report_td_ra1.html")
    ap.add_argument("--include-heroes", action="store_true", help="Include a separate frozen hero comparison population.")
    ap.add_argument("--pending", help="JSON map actor -> PENDING class (C46). Renders the class "
                                      "cell as 'today -> after'. A trailing '?' marks a "
                                      "reclassification that OVERRIDES an existing combat class "
                                      "and is not yet ruled.")
    args = ap.parse_args()

    peers, cameo = rd.peer_rows(), rd.cameo_rows()
    dist = rd.build_distributions(peers)
    rt.add_cost_distribution(dist, peers)
    cdist = rt.cameo_context()
    doc = json.loads(ASSIGN.read_text(encoding="utf-8"))
    assignment, chassis_only = doc["assignment"], doc.get("chassis_only", {})
    # ⚠ THE INDEX MUST HOLD EVERY POOL THE ASSIGNMENT COULD DRAW FROM. It is built from
    # `peer_rows()`, which by construction EXCLUDES the hero and variant lanes — so a row either
    # lane assigned cannot be recovered here and silently renders as no reference at all. The
    # variant lane made that visible: `td_gdi_humveemkii` holds DTA's `JEEPPTNK` and the page
    # showed the cell empty, which is the worst of both worlds — a mapping that exists in the
    # data and reads as missing work in the report.
    #
    # ⛔ AND I MADE EXACTLY THAT MISTAKE AGAIN ONE LINE LATER, which is why this comment is now
    # a list rather than a sentence. The first fix added the VARIANT lane and forgot the HERO
    # lane, so `td_gdi_exosuit` reported "1 of 2 sources used" on HP, speed AND cost while DTA's
    # `XO` — a perfectly good row with hp 7,000, speed 6, cost 2,000 — sat unrecoverable. The
    # maintainer spotted it from the map. Every lane the ASSIGNMENT can write must be here:
    #   peer_rows()          the ordinary corpus
    #   peer_variant_rows()  chassis variants the population rule drops
    #   peer_hero_rows()     heroes and build-limited units
    # ⚠ This is the RECOVERY index and is independent of `--include-heroes`, which controls a
    # separate hero comparison POPULATION. Recovering a row is not the same as pooling it.
    index_rows = peers + rd.peer_variant_rows() + rd.peer_hero_rows()
    attached = rt.expand_families(rt.attach(assignment, rt.peer_index(index_rows)), peers)
    hero_context = None
    if args.include_heroes:
        hero_peers = [r for r in rd.peer_hero_rows() if r.get('hero') is True]
        hero_dist = rd.build_distributions(hero_peers)
        rt.add_cost_distribution(hero_dist, hero_peers)
        hero_context = (hero_dist, rt.hero_cameo_context())
        heroes = rd.cameo_hero_rows()
        hero_index = {(r['source'], r['id']): r for r in hero_peers}
        for hero in heroes:
            attached[hero['id']] = [hero_index[(source, ref['id'])]
                for source, ref in assignment.get(hero['id'], {}).items()
                if ref.get('confidence') in ('STRONG', 'FAIR')
                and (source, ref.get('id')) in hero_index]
        cameo += heroes
    crows = {c["id"]: c for c in cameo}
    # The class comes from `class_membership.classify`, NEVER from the raw `design.class_anchor`
    # field: membership is DERIVED from `subtype` when no explicit tag exists, so reading the tag
    # alone reports `commando` as empty when it has 30 members.
    import class_membership as cm
    led_arms = {}
    for _p in sorted((ROOT / "docs" / "balance").glob("*.json")):
        if "class_anchors" in _p.name:
            continue
        try:
            _d = json.loads(_p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for _sec in (_d.get("sections") or {}).values():
            if not isinstance(_sec, dict):
                continue
            for _n, _r in _sec.items():
                if isinstance(_r, dict):
                    led_arms[_n] = sum(1 for x in (_r.get("armaments") or [])
                                       if isinstance(x, dict) and x.get("pricing"))
    klass = {}
    for actor, design in cm.ledger_rows():
        c, _why = cm.classify(design)
        if c:
            klass[actor] = c
        else:
            reason = {"no-class-exists": "anchor class pending",
                      "no-template": "role template missing",
                      "not-a-unit": "separate defense lane"}.get(_why, "class unresolved")
            klass[actor] = f"{design.get('subtype') or 'Unknown role'} ({reason})"

    # ⚠ PENDING classes are NOT in the ledger and cannot be: `^ArmedTroopTransportTemplate` and
    # `^MobileBunkerTemplate` do not exist in yaml yet (C46), and `extract_stats` rewrites
    # `design.class_anchor` to None on every run, so subtype — i.e. the inherited template — is the
    # only durable membership signal. This overlay exists so the maintainer can review the
    # reclassification BEFORE any yaml lands, not to assert it has happened.
    if args.pending:
        pend = json.loads(pathlib.Path(args.pending).read_text(encoding="utf-8"))
        for actor, new_class in pend.items():
            klass[actor] = f"{klass.get(actor) or '—'} → {new_class}"

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
            emit(body, band, crows, assignment, attached, chassis_only, dist, cdist, counts, klass, led_arms, hero_context)

    summary = (f'{counts["orig"]} originals · {counts["exp"]} expanded · '
               f'{counts["refs"]} references · {counts["none"]} priced by formula · '
               f'{counts["thin"]} originals under three sources')
    title = "Cameo Reference Map"
    page = (
        f"<title>{title}</title>\n"
        f"<style>{STYLE}</style>\n"
        f"<h1>{title}</h1>\n"
        '<p class="lede">Every Cameo actor with the reference unit chosen from each source, by '
        'full id and name, split into units that exist in the original games and units that do '
        'not. The bar on each chip is match confidence. <b>HP →</b>, <b>speed →</b> and '
        '<b>cost →</b> are the R4 synthesis targets — references plus Cameo, one vote each. '
        'This report is read-only: current values come from live YAML, while the arrows are diagnostic synthesis targets.</p>\n'
        f'<p class="lede">{summary}</p>\n'
        '<div class="wrap">\n' + "\n".join(body) + "\n</div>\n")
    pathlib.Path(args.out).write_text(page, encoding="utf-8")
    print(f"wrote {args.out}  ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
