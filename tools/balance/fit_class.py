#!/usr/bin/env python3
"""fit_class.py — Balance Pipeline Phase 5 (Formula v2, DESIGN §12).

Derives a class-anchor entry from a maintainer-picked anchor unit and
validates it across every unit of that class, writing a sign-off report.

Workflow per class (one class at a time, maintainer-driven):
1. Maintainer tags class members: set design.class_anchor = "<class>"
   in the ledger for every unit of the class (or pass --actors).
2. Maintainer picks the ANCHOR unit (a unit whose current cost is
   considered correct).
3.   python tools/balance/fit_class.py --class bomber \
         --anchor ra1_badger_bomber
   -> computes O0/P0/Q0 at the anchor's raw stats, cost0 = its cost,
      writes the candidate into docs/balance/class_anchors.json
      (signed_off: false) and the validation table
      docs/balance/formula_v2_<class>.md: every member's
      class-formula price vs actual cost.
4. Maintainer reviews the table; on approval set "signed_off": true —
   build_workbook.py then prices that class with the anchor formula.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import formula  # noqa: E402
import tier_chain  # noqa: E402

LEDGER = ROOT / "docs/balance"
ANCHORS = LEDGER / "class_anchors.json"


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def derived_dps_index(du):
    """{(slot, weapon): effective_dps} for one actor's derived sidecar entry.

    `effective_dps` is what W1's K coefficient buys: k_context x damage x burst /
    eff_reload, i.e. DPS already discounted for accuracy, spread, falloff, range,
    dead zone and how many targets the shot can actually reach. It is computed by
    extract_stats (via weapon_efficiency.analyse) and is NOT recomputed here — one
    definition of K, in one place.
    """
    idx = {}
    for arm in (du or {}).get("armaments", []):
        dps_v = fnum(arm.get("effective_dps"))
        if dps_v is not None:
            idx[(arm.get("slot"), arm.get("weapon"))] = dps_v
    return idx


def unit_inputs(u, du=None, use_k=False):
    """((hp, speed, range_wdist, dps, special, unit_class, tech_tier), fallbacks),
    or (None, 0) when the unit has no usable combat stats.

    With use_k, each armament contributes its K-adjusted `effective_dps` from the
    derived sidecar instead of raw damage/reload. Armaments the sidecar has no
    entry for fall back to raw DPS and are COUNTED, so the report can state its
    coverage rather than quietly mixing two units of measurement.

    The return shape is the same either way on purpose: a tuple that changes shape
    with a flag is exactly the kind of thing that silently misprices a roster.
    """
    hp = fnum((u.get("hp") or {}).get("v"))
    speed = fnum((u.get("speed") or {}).get("v") or (u.get("speed_air") or {}).get("v"))
    d = u.get("design") or {}
    # Unconditional per-actor FirepowerMultiplier scales EFFECTIVE damage output;
    # balance prices on effective DPS = raw x FP-mult (cameo-firepower-mult-in-dps). Default 1.0.
    fp = fnum((u.get("firepower_multiplier") or {}).get("v")) or 1.0
    kidx = derived_dps_index(du) if use_k else {}
    total_dps, best_range = 0.0, 0.0
    fallbacks = 0
    for arm in u.get("armaments", []):
        if not arm.get("pricing", True):
            continue
        # Price the weapon the unit fires AS BUILT. The old rule skipped every
        # armament that had any `requires` at all, which threw away the BASE
        # weapon of each unit that merely owns an elite variant: 371 of 863
        # actors with priced armaments came out at zero DPS and dropped out of
        # pricing entirely, `tiger.nax` — the recorded `mbt` anchor — among them.
        if not formula.condition_holds_by_default(arm.get("requires")):
            continue
        dmg = formula.spread_damage_sum(arm.get("damage_warheads", []))  # SUM law, chips excluded
        reload_ = fnum(arm.get("reloaddelay"))
        if not dmg or not reload_:
            continue
        # ⚠ A charge trait may OVERRIDE the weapon's reload entirely. `AttackTesla`
        # does: its own ReloadDelay is the cycle, it fires MaxCharges zaps inside
        # it, and the weapon's reload is only the gap between them. A Tesla Coil's
        # weapon reloads every 3 ticks, so reading the weapon alone prices the coil
        # as firing 20 times a second when it fires 3 zaps per 106 ticks — DPS
        # overstated 11.8x, and DPS drives the price.
        own = formula.charge_attack_cycle(u.get("charge_up"), reload_)
        if own:
            cycle, shots = own
            raw = dmg * shots / cycle
        else:
            raw = formula.dps(dmg, reload_,
                              int(fnum(arm.get("burst")) or 1),
                              arm.get("burstdelays"))
        if use_k:
            keyed = kidx.get((arm.get("slot"), arm.get("weapon")))
            if keyed is None:
                fallbacks += 1
            total_dps += raw if keyed is None else keyed
        else:
            total_dps += raw
        best_range = max(best_range, formula.wdist_value(arm.get("range"), 0.0))
    total_dps *= fp   # apply the actor-level FirepowerMultiplier to effective DPS
    if hp is None or speed is None or total_dps == 0:
        return None, 0
    # Tech tier: manual design.tech_tier is the maintainer override;
    # otherwise fall back to the derived sidecar's computed f(C).
    tech_tier = tier_chain.effective_tier(d.get("tech_tier"),
                                          (du or {}).get("tier_multiplier"),
                                          default=1.0)
    return ((hp, speed, best_range, total_dps,
             fnum(d.get("special")) or 1.0, fnum(d.get("unit_class")) or 1.0,
             tech_tier), fallbacks)


def physical_state_weight(u, du=None) -> float:
    """Delivery weight for the physical-state price multiplier, or 0.

    The value is read from the derived sidecar first (the canonical place after
    `extract_stats.split_derived`), then from a still-attached `_derived` blob,
    then from a raw top-level field, so the helper works whether the caller has
    already merged the sidecar or not.
    """
    for src in (u.get("_derived") if isinstance(u, dict) else None,
                du or {},
                u if isinstance(u, dict) else {}):
        if src and "physical_state_weight" in src:
            return float(src["physical_state_weight"])
    return 0.0


def price_unit(u, du, inp, o0, p0, q0, cost0) -> float:
    """Formula-v2 price for one ledger unit, including the actor-level modifiers.

    The charge-up discount is applied to the PRICE, after the estimators, not to
    DPS: O/P/Q are degree 1/2/3 in their inputs, so scaling DPS would not produce
    a clean 0.75x on the result. Charging is an ACTOR property (W4) — the delay
    inflates the effective reload AND the unit is helpless while it winds up.

    The physical-state surcharge (E2) is also an actor-level price multiplier:
    it is proportional to delivery, so a heat/chemical unit that does not fill
    the meter pays less than the 1.25x ceiling. The weight comes from the derived
    sidecar so it cannot desync from the raw ledger.
    """
    o, p, q = formula.estimators(*inp)
    v2 = formula.class_anchor_price(o, p, q, o0, p0, q0, cost0)
    return (v2
            * formula.charge_price_multiplier(u.get("charge_up"),
                                              charge_cycle_fallback(u))
            * formula.physical_state_price_multiplier(
                physical_state_weight(u, du)))


def charge_cycle_fallback(u) -> float | None:
    """The reload a wind-up competes with, for traits that govern no reload of their own.

    `AttackTesla` carries its own `ReloadDelay`, so it never needs this. The
    `ChargeLevel` family does: the charge gates the actor's attack, so the share is
    measured against the gun it delays.

    Takes the LONGEST base-weapon reload, not the shortest: a charge gates the heavy
    shot, and an actor with a fast secondary (the Terran siege tank's 37 next to its
    sieged 148) would otherwise look like it charges for most of its cycle and earn a
    discount it has not paid for. An approximation either way — it assumes the
    slowest weapon is the charged one, which is true for every charging actor in the
    tree today.
    """
    reloads = [fnum(a.get("reloaddelay")) for a in u.get("armaments", [])
               if a.get("pricing", True)
               and formula.condition_holds_by_default(a.get("requires"))]
    reloads = [r for r in reloads if r]
    return max(reloads) if reloads else None


def collect_units(cls, actors_filter, always=()):
    """(raw units, derived units) keyed by actor.

    `actors_filter` is the EXPLICIT --actors list and nothing else. The anchor is
    passed via `always` instead of being unioned into the filter: a non-empty
    filter switches off the `design.class_anchor == cls` branch, so folding the
    anchor in made every run collect exactly one unit — the anchor — and report a
    one-row validation table for the whole class.

    The derived sidecar is loaded from the matching file in docs/balance/derived/
    so K comes from the SAME extract run as the raw stats. Reading it from a
    different source, or recomputing it here, would let the two drift apart
    silently — and `audit_balance_drift` only guards raw yaml vs ledger.
    """
    out, derived = {}, {}
    for jf in sorted(LEDGER.glob("*.json")):
        if jf.name in ("class_anchors.json",):
            continue
        doc = json.loads(jf.read_text(encoding="utf-8"))
        if "sections" not in doc:
            continue

        dfile = LEDGER / "derived" / jf.name
        ddoc = json.loads(dfile.read_text(encoding="utf-8")) if dfile.is_file() else {}
        dsec = ddoc.get("sections") or {}

        for secname, sec in doc["sections"].items():
            for actor, u in sec.items():
                keep = (actor in actors_filter if actors_filter
                        else (u.get("design") or {}).get("class_anchor") == cls)
                if not keep and actor not in always:
                    continue
                out[actor] = u
                derived[actor] = (dsec.get(secname) or {}).get(actor)
    return out, derived


def write_comparison(args, units, derived, fit) -> int:
    """W11: price the class both ways and report the difference.

    Deliberately writes NO candidate to class_anchors.json. The plan is explicit
    that pricing and content never flip in one commit: this produces evidence for
    the maintainer, and switching the pipeline is a separate, signed-off decision.
    """
    raw = fit(False)
    kfit = fit(True)
    if raw is None or kfit is None:
        print(f"anchor `{args.anchor}` lacks hp/speed/weapon stats")
        return 2

    _, rc0, ro0, rp0, rq0, rrows, _ = raw
    _, kc0, ko0, kp0, kq0, krows, kfb = kfit
    kmap = {a: v for a, _c, v, _d in krows}

    both = [(a, c, v, kmap.get(a)) for a, c, v, _d in rrows
            if v is not None and kmap.get(a) is not None and c]
    shifts = [(kv / v - 1.0) for _a, _c, v, kv in both if v]

    out = ROOT / "docs/balance/derived" / f"k_comparison_{args.cls}.md"
    L = [f"# W11 — K comparison for class `{args.cls}`", "",
         f"Anchor `{args.anchor}`, cost0 {rc0:.0f}. Every member priced twice: on RAW",
         "damage/reload, and on K-adjusted `effective_dps` from the derived sidecar",
         "(accuracy, spread, falloff, range, dead zone, reachable targets).",
         "",
         "The anchor is re-fitted in each mode, so each column is internally",
         "consistent; only the SHAPE of the class changes between them.", ""]

    if kfb:
        L += [f"⚠ **{kfb} armament(s) had no derived entry and fell back to raw DPS.**",
              "Those rows mix the two scales — re-run `extract_stats.py` and check "
              "coverage before trusting them.", ""]

    L += [f"| estimator | raw | K |", "|---|---|---|",
          f"| O0 | {ro0:.2f} | {ko0:.2f} |",
          f"| P0 | {rp0:.2f} | {kp0:.2f} |",
          f"| Q0 | {rq0:.2f} | {kq0:.2f} |", "",
          "| unit | cost | raw price | K price | raw Δ | K Δ | K vs raw |",
          "|---|---|---|---|---|---|---|"]

    for actor, cost, v, kv in sorted(both, key=lambda r: -(abs(r[3] / r[2] - 1.0) if r[2] else 0)):
        rd, kd, shift = (v - cost) / cost, (kv - cost) / cost, kv / v - 1.0
        flag = "" if abs(shift) < 0.10 else (" ⚠" if abs(shift) < 0.30 else " ❗")
        L.append(f"| `{actor}` | {cost:.0f} | {v:.0f} | {kv:.0f} | "
                 f"{rd:+.0%} | {kd:+.0%} | {shift:+.0%}{flag} |")

    if shifts:
        shifts.sort()
        n = len(shifts)
        med = shifts[n // 2] if n % 2 else (shifts[n // 2 - 1] + shifts[n // 2]) / 2
        worse = sum(1 for _a, c, v, kv in both if abs(kv - c) > abs(v - c))
        L += ["", "## What the switch would do", "",
              f"- **{n} units** priced both ways.",
              f"- Median price shift: **{med:+.1%}**; range "
              f"**{shifts[0]:+.1%} … {shifts[-1]:+.1%}**.",
              f"- Moves AWAY from the current cost for **{worse}/{n}** units, "
              f"towards it for **{n - worse}**.", "",
              "A K switch is worth taking when it moves prices TOWARDS current costs for",
              "units the maintainer already considers correctly priced — that is evidence",
              "the coefficient is capturing something real rather than adding noise.",
              "It is not a target to optimise: a weapon that genuinely is inaccurate",
              "SHOULD price below its raw damage.", ""]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"comparison -> {out.relative_to(ROOT)}  "
          f"({len(both)} units, median shift {med:+.1%})" if shifts else
          f"comparison -> {out.relative_to(ROOT)} (no comparable units)")
    print("no candidate written — --compare-k is a report, not a fit")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls", required=True)
    ap.add_argument("--anchor", help="anchor actor id (real-unit anchor)")
    ap.add_argument("--spec", help="virtual anchor `hp,speed,range_wdist,"
                    "damage,reload,cost0` — a round-number model unit that "
                    "need not exist in game (Tiger-style baseline)")
    ap.add_argument("--actors", nargs="*", help="explicit member list "
                    "(otherwise: design.class_anchor == --class)")
    ap.add_argument("--use-k", action="store_true",
                    help="price on K-adjusted effective DPS (derived sidecar) "
                         "instead of raw damage/reload (W11)")
    ap.add_argument("--compare-k", action="store_true",
                    help="W11: price the class BOTH ways and write a comparison "
                         "report to docs/balance/derived/. Writes no candidate "
                         "anchor — it is a report, not a fit.")
    args = ap.parse_args()
    if not args.anchor and not args.spec:
        ap.error("need --anchor or --spec")
    if args.compare_k and args.spec:
        ap.error("--compare-k needs a real --anchor: a virtual --spec has no "
                 "armaments, so it has no K to compare")

    units, derived = collect_units(args.cls, set(args.actors or []),
                                   always={args.anchor} if args.anchor else set())
    def fit(use_k):
        """(anchor_id, cost0, o0, p0, q0, rows, fallbacks) for one pricing mode.

        The ANCHOR is re-fitted in the same mode as the members. Pricing members
        on K against an anchor fitted on raw DPS would compare two different
        scales and make every delta meaningless.
        """
        if args.spec:
            hp, speed, rng, dmg, reload_, c0 = (float(x) for x in args.spec.split(","))
            d0 = formula.dps(dmg, reload_)
            e0 = formula.estimators(hp, speed, rng, d0)
            return (f"SPEC({args.spec})", c0) + e0 + ([], 0)

        ai, af = unit_inputs(units[args.anchor], derived.get(args.anchor), use_k)
        if ai is None:
            return None
        c0 = fnum((units[args.anchor].get("cost") or {}).get("v"))
        e0 = formula.estimators(*ai)
        rws, fb = [], af
        for actor, u in sorted(units.items()):
            inp, f = unit_inputs(u, derived.get(actor), use_k)
            fb += f
            cost = fnum((u.get("cost") or {}).get("v"))
            if inp is None or cost is None:
                rws.append((actor, cost, None, None))
                continue
            v2 = price_unit(u, derived.get(actor), inp, *e0, c0)
            rws.append((actor, cost, v2, (v2 - cost) / cost if cost else None))
        return (args.anchor, c0) + e0 + (rws, fb)

    if args.anchor and args.anchor not in units:
        print(f"anchor `{args.anchor}` not found in the ledger")
        return 2

    fitted = fit(args.use_k)
    if fitted is None:
        print(f"anchor `{args.anchor}` lacks hp/speed/weapon stats")
        return 2
    anchor_id, cost0, o0, p0, q0, rows, fallbacks = fitted

    if args.compare_k:
        return write_comparison(args, units, derived, fit)

    print(f"anchor {anchor_id}: cost0={cost0:.0f} O0={o0:.2f} P0={p0:.2f} Q0={q0:.2f}"
          + (f"  [K mode, {fallbacks} armament(s) fell back to raw DPS]"
             if args.use_k else ""))

    rep = LEDGER / f"formula_v2_{args.cls}.md"
    lines = [f"# Formula v2 validation — class `{args.cls}`",
             "", f"anchor: `{args.anchor}` (cost0 {cost0:.0f}, "
             f"O0 {o0:.2f}, P0 {p0:.2f}, Q0 {q0:.2f})", "",
             "| unit | cost (actual) | class-formula price | delta |",
             "|---|---|---|---|"]
    for actor, cost, v2, delta in rows:
        if v2 is None:
            lines.append(f"| `{actor}` | {cost or '?'} | (no combat stats) | |")
        else:
            flag = "" if abs(delta) < 0.10 else (" ⚠" if abs(delta) < 0.30 else " ❗")
            lines.append(f"| `{actor}` | {cost:.0f} | {v2:.0f} | {delta:+.0%}{flag} |")
    rep.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    anchors = json.loads(ANCHORS.read_text(encoding="utf-8"))
    # ⚠⚠ **MERGE, NEVER REPLACE.** This used to be `anchors[args.cls] = {...}`, which
    # DESTROYED the rest of the entry — measured 2026-08-17 on `mbt`: one run wiped `spec`
    # (cost0/dps0/hp0/range0_wdist/speed0), `armor`, `tech_tier`, `tech_tier_flag`,
    # `verifier_actor`, `reveals_shroud` and the "★ LOCKED 2026-08-01" provisional note,
    # leaving six keys behind. Those are the maintainer's DESIGN inputs, not fit outputs —
    # `formula.class_baseline_price` reads `spec`, and the tier/verifier pair enforces the
    # 2.5x identity ([[cameo-verifier-tier-k-match]]). The sign-off workflow is "run
    # fit_class for each of the 27 classes, then review", so the obvious next step would
    # have silently erased ALL 27 locked specs, with a clean exit 0 and a plausible report.
    entry = dict(anchors.get(args.cls) or {})
    was_signed = bool(entry.get("signed_off"))
    entry.update({"anchor_actor": args.anchor or anchor_id, "cost0": cost0,
                  "o0": round(o0, 4), "p0": round(p0, 4), "q0": round(q0, 4),
                  # A fresh fit moves the numbers, so any previous approval is void.
                  "signed_off": False,
                  # Its OWN key: `comment` carries the maintainer's design rationale.
                  "fit_comment": "candidate — maintainer sign-off pending"})
    anchors[args.cls] = entry
    ANCHORS.write_text(json.dumps(anchors, sort_keys=True, indent=1,
                                  ensure_ascii=False) + "\n",
                       encoding="utf-8", newline="\n")
    if was_signed:
        print(f"⚠ `{args.cls}` was signed_off — this fit RESET it to false. "
              f"Re-review before relying on it.")
    print(f"candidate written to class_anchors.json (signed_off: false); "
          f"validation -> {rep.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
