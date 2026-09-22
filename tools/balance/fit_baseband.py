#!/usr/bin/env python3
"""fit_baseband.py — can a class fit the 100%-250% baseband, and where does its baseline go?

MAINTAINER RULING R3: reference -> virtual baseline per class -> fit the 100%-250% band ->
parameterise the formula per class -> only THEN price. And, asked directly which moves:
⭐ **"Move the BASELINE, not the actors."**

This tool answers the two questions that ruling raises, and the first answer is geometric
rather than statistical.

⛔ **`cost0` CANNOT MOVE THE BAND.** The band ratio is `class price / cost0`, and
`class_baseline_estimators` multiplies every estimator BY `cost0`:

    o = (h+s+r+d) * cost0/4      p = (h*s + r*d) * cost0/2      q = h*s*r*d * cost0

so the ratio is `[(h+s+r+d)/4 + (h*s+r*d)/2 + h*s*r*d] / 3`, in which `cost0` has cancelled
out completely. Re-pricing a baseline changes what the class COSTS and moves nothing into the
band. Only the four STAT axes (`hp0`, `speed0`, `range0_wdist`, `dps0`) do that, through
`h = hp/hp0` and its siblings.

⛔ **AND THE BAND IS NOT A WINDOW AROUND THE BASELINE — IT STARTS AT IT.** At the baseline
h=s=r=d=1, so the ratio is exactly 1.000: the baseline sits precisely on the 100% edge. The
250% edge is exactly the 2x-HP / 2x-DPS verifier. So "every member inside 100%-250%" means:

    the baseline must be at or BELOW the weakest member on the combined axes,
    and the whole class must span no more than the verifier envelope.

That is why a MEDIAN-derived baseline can never satisfy the band: it puts half the class
below 100% by construction. `derive_virtual_anchor` proposes reference-backed class MEDIANS,
which is right for "what is typical" and wrong for "where does the band start". The two are
different questions and the pipeline currently asks the first to answer the second.

The decay is steep, which is why the occupancy numbers are so low: a member weaker than the
baseline by just 10% on every axis already prices at **78.9%**, below the 75% floor. There is
no gentle shoulder.

WHAT THIS TOOL COMPUTES, per class:

  span      max_ratio / min_ratio at the CURRENT anchor. The formula is nonlinear in the
            baseline axes, so this span can change under a uniform rescale; it is a current-
            anchor observation only. `best_k` reports the result of the bounded scalar scan,
            while neither value proves that an anisotropic baseline or role split cannot fit.
  k*        the single scale applied to all four stat axes that maximises sweet-spot
            occupancy (ties broken toward the weakest member landing on 100%).
  fitted    occupancy at k*, and the members still outside.

It writes nothing. Choosing a baseline is a maintainer act; this says what each choice costs.

Usage: python tools/balance/fit_baseband.py [--json <band.json>] [--class X]
       (--json defaults to regenerating it via check_band --json into a temp file)
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import statistics
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import formula  # noqa: E402
import tier_chain  # noqa: E402

SWEET_LO, SWEET_HI = 1.00, 2.50
SOFT_FLOOR, CEIL = 0.75, 3.50
# Grid steps for reporting a fitted baseline, from derive_virtual_anchor.STEPS.
STEPS = dict(hp0=1000, speed0=1, range0_wdist=10, dps0=1)


def ratio_of(inp, spec, anchor_tier, k=1.0):
    """The band ratio for one member, with every baseline STAT axis scaled by `k`.

    `cost0` is deliberately absent: it cancels. Passing it would invite the belief that
    re-pricing a baseline moves the band.
    """
    hp, speed, rng, dps_v, special, tier = inp
    rel = tier / anchor_tier if anchor_tier else tier
    o, p, q = formula.class_baseline_estimators(
        hp, speed, rng, dps_v,
        spec["hp0"] * k, spec["speed0"] * k, spec["range0_wdist"] * k, spec["dps0"] * k,
        1.0, special=special, tech_tier=rel)
    return (o + p + q) / 3


def core_window(ratios, span_cap=SWEET_HI):
    """(lo_index, hi_index) of the longest current-anchor ratio window.

    The current-anchor ratios are one-dimensional, so sort and take the longest contiguous run
    whose max/min fits the envelope. This is a descriptive window at the recorded anchor;
    it is not a proof of the largest feasible subset after re-fitting the axes.

    This is what makes the span number actionable. A class with a wide current-anchor spread
    usually has a tight observed window plus members that need a role or tier review;
    `futuretech_blackwidow` is in `melee` with a range of 9000, and `corrino_buggy` is in `mbt`.
    The band is reporting a triage signal, not proving a classification defect.
    """
    rs = sorted(ratios)
    best = (0, 0, 0)
    lo = 0
    for hi in range(len(rs)):
        while rs[hi] / rs[lo] > span_cap:
            lo += 1
        if hi - lo + 1 > best[0]:
            best = (hi - lo + 1, lo, hi)
    return best[1], best[2]


def occupancy(members, spec, anchor_tier, k):
    rs = [ratio_of(m, spec, anchor_tier, k) for m in members]
    return sum(1 for r in rs if SWEET_LO <= r <= SWEET_HI), rs


def best_k(members, spec, anchor_tier):
    """The uniform stat-axis scale maximising sweet-spot occupancy.

    Scanned rather than solved: the ratio is monotone in `k` per member but the COUNT in
    band is a step function of it, so there is no derivative to set to zero. A log-spaced
    scan is exact enough for a decision and cannot mistake a local step for an optimum.
    """
    best = (-1, 1.0, None)
    for i in range(-400, 401):
        k = math.exp(i / 200.0)          # ~0.135x .. ~7.4x
        n, rs = occupancy(members, spec, anchor_tier, k)
        # tie-break: prefer the k that puts the weakest member closest to 100% from above
        slack = min(rs) - SWEET_LO
        key = (n, -abs(slack) if slack >= 0 else -100 + slack)
        if key > (best[0], best[2] if best[2] is not None else -1e9):
            best = (n, k, key[1])
    return best[1]



AXES = ("hp", "speed", "range", "raw_dps")


def worst_axis(member_inputs, core_medians):
    """The axis on which this member deviates most from its class core, as (axis, x-factor).

    Reported in multiplicative terms because the price formula is multiplicative: a unit at
    6x its class's median range is not "a bit long", it is in the wrong class. This is the
    evidence that makes `futuretech_blackwidow` (range 9000 in `melee`) obvious at a glance
    rather than something a reader has to notice.
    """
    worst = (None, 1.0)
    for ax in AXES:
        cur, med = member_inputs.get(ax), core_medians.get(ax)
        if not cur or not med:
            continue
        factor = cur / med
        if abs(math.log(factor)) > abs(math.log(worst[1])):
            worst = (ax, factor)
    return worst


def candidate_classes(member, specs, anchor_tiers, exclude):
    """Every OTHER class whose CURRENT baseline would put this member in 100%-250%.

    ⛔ MEASURE THIS BEFORE TREATING IT AS EVIDENCE — it is almost never discriminating.
    Across the 404 priced members, the MEDIAN member is accepted by **6 of the 27** classes
    that have a usable spec (mean 5.6, max 9, and only 6 members are accepted by one class or
    none). So "another class would take it" is true of nearly everything.

    The first version of this triage used it as the deciding signal and confidently labelled
    **81 of 114** outliers MISCLASSIFIED, naming the single best-fitting class — which put
    `terran_ghost` in `artillery` on the strength of one arbitrary pick out of six. Those
    labels would have looked authoritative and carried no information.

    `anchor_readiness.py` already says why, and it is worth quoting because it is the binding
    limit here: the statistically indistinguishable class pairs are *"separated by what they
    SHOOT AT, not by their stats. No stat-based check can police these boundaries."*

    So the COUNT is reported, never a name — except at the two ends, where it really does
    discriminate: 0 accepting classes, or exactly 1.
    """
    out = []
    for cls, spec in specs.items():
        if cls == exclude:
            continue
        r = ratio_of(member, spec, anchor_tiers.get(cls, 1.0), 1.0)
        if SWEET_LO <= r <= SWEET_HI:
            out.append((cls, r))
    return sorted(out, key=lambda x: abs(x[1] - 1.5))


def propose(band_ratio, axis, factor, cands, tier, core_tier):
    """The EVIDENCE for one outlier, ranked by how much it actually discriminates.

    Deliberately NOT a recommendation of a target class. Class membership is a role judgement
    (what a unit shoots at) and no stat test can make it — see `candidate_classes`. What the
    band can honestly contribute is: this member sits outside its current-anchor class window,
    here is the axis responsible, and here is whether anything else would even accept it.
    """
    off = factor is not None and (factor > 2.0 or factor < 0.5)
    if not cands:
        return "NO CLASS ACCEPTS", (
            f"outside every current-anchor class window" +
            (f"; {axis} {factor:.1f}x its current-anchor window" if off else ""))
    if len(cands) == 1:
        return "ONE CLASS ACCEPTS", f"only `{cands[0][0]}` takes it at {cands[0][1] * 100:.0f}%"
    if off:
        return "AXIS OUTLIER", (
            f"{axis} {factor:.1f}x its class core — checkable; "
            f"{len(cands)} classes would accept it, so that says nothing")
    if band_ratio > SWEET_HI and tier and core_tier and tier < core_tier * 0.85:
        return "LATER TECH", (f"tier {tier:.2f} vs core {core_tier:.2f} — a tech-tier gate may "
                              f"explain the {band_ratio * 100:.0f}%")
    return "ROLE REVIEW", (f"{band_ratio * 100:.0f}% of baseline, no axis dominates, "
                           f"{len(cands)} classes accept it — stats cannot decide this one")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=pathlib.Path)
    ap.add_argument("--class", dest="cls")
    ap.add_argument("--triage", action="store_true",
                    help="per-outlier proposals with the evidence behind each")
    args = ap.parse_args()

    path = args.json
    if path is None:
        path = pathlib.Path(tempfile.gettempdir()) / "fit_baseband_band.json"
        subprocess.run([sys.executable, str(ROOT / "tools/balance/check_band.py"),
                        "--json", str(path)], cwd=ROOT, capture_output=True)
    data = json.loads(path.read_text(encoding="utf-8"))
    anchors = {k: v for k, v in json.loads(
        (ROOT / "docs/balance/class_anchors.json").read_text(encoding="utf-8")).items()
        if isinstance(v, dict)}
    # Same anchor-tier resolution as check_band, or the recomputation does not match it.
    tier_map = tier_chain.load_derived_map(ROOT / "docs/balance")
    anchor_tiers = {}
    for cls, a in anchors.items():
        actor = a.get("anchor_actor")
        if actor and actor in tier_map:
            anchor_tiers[cls] = tier_map[actor].get("tier_multiplier", 1.0)
        else:
            try:
                anchor_tiers[cls] = float(a.get("tech_tier")) or 1.0
            except (TypeError, ValueError):
                anchor_tiers[cls] = 1.0

    by_class: dict[str, list] = {}
    reported: dict[str, list] = {}
    names: dict[str, list] = {}
    for row in data["rows"]:
        if row.get("band_exempt"):
            continue
        cls = row["class"]
        if args.cls and cls != args.cls:
            continue
        i = row["inputs"]
        by_class.setdefault(cls, []).append(
            (i["hp"], i["speed"], i["range"], i["raw_dps"], i["special"], i["tier"]))
        reported.setdefault(cls, []).append(row["ratio"])
        names.setdefault(cls, []).append((row["actor"], i))

    print("# Baseband feasibility and where the baseline has to go\n")
    print("band ratio = class price / cost0.  cost0 CANCELS — only hp0/speed0/range0/dps0 move it.")
    print("the baseline sits at exactly 100%; the 2x-HP/2x-DPS verifier at exactly 250%.\n")

    rows, infeasible, checked, mismatched = [], [], 0, 0
    for cls in sorted(by_class):
        anchor = anchors.get(cls) or {}
        spec = anchor.get("spec")
        if not spec or not spec.get("dps0") or not spec.get("range0_wdist"):
            continue
        # ⚠ The anchor's tier comes from the TIER MAP via `anchor_actor`, and only falls back
        # to the anchor's own `tech_tier` field. Reading the field first made 257 of 404
        # recomputed ratios disagree with check_band — caught by the cross-check below, which
        # is the only reason this tool's numbers can be trusted at all.
        at = anchor_tiers.get(cls, 1.0)
        members = by_class[cls]

        # ⚠ Verify the recomputation against check_band's own numbers before trusting it.
        mine = [ratio_of(m, spec, at, 1.0) for m in members]
        for a, b in zip(mine, reported[cls]):
            checked += 1
            if not math.isclose(a, b, rel_tol=1e-6):
                mismatched += 1

        n0 = sum(1 for r in mine if SWEET_LO <= r <= SWEET_HI)
        span = max(mine) / min(mine)
        k = best_k(members, spec, at)
        nk, rk = occupancy(members, spec, at, k)
        rows.append((cls, len(members), n0, nk, span, k, min(rk), max(rk), spec))
        if span > SWEET_HI:
            infeasible.append((cls, span, len(members)))

    print(f"recomputation cross-check against check_band: {checked - mismatched}/{checked} "
          f"ratios identical" + ("" if not mismatched else f"  ⚠ {mismatched} MISMATCH") + "\n")

    print("| class | members | in band now | best single-k | k* | min% | max% | span | verdict |")
    print("|---|--:|--:|--:|--:|--:|--:|--:|---|")
    for cls, n, n0, nk, span, k, lo, hi, _spec in sorted(rows, key=lambda r: -r[4]):
        verdict = ("fits fully" if nk == n
                   else "CURRENT-ANCHOR SPAN > 2.5" if span > SWEET_HI else "partial")
        print(f"| `{cls}` | {n} | {n0} ({n0/n:.0%}) | {nk} ({nk/n:.0%}) | {k:.3f} | "
              f"{lo*100:.0f}% | {hi*100:.0f}% | {span:.1f}x | {verdict} |")

    tot = sum(r[1] for r in rows)
    now = sum(r[2] for r in rows)
    fit = sum(r[3] for r in rows)
    print(f"\n**{now}/{tot} ({now/tot:.0%}) of priced members sit in the sweet spot today; "
          f"re-scaling each class baseline alone reaches {fit}/{tot} ({fit/tot:.0%}).**")
    print(f"\n**{len(infeasible)} of {len(rows)} classes exceed the 2.5x envelope at the "
          "recorded current anchor** — this is a current-anchor observation, not a feasibility "
          "proof.")
    print("The spread is concentrated, not general: below is each class's current-anchor ratio "
          "window and the members outside that window.\n")

    print("| class | current-anchor window | window span | members outside the current-anchor ratio window |")
    print("|---|--:|--:|---|")
    triage_total = 0
    for cls, span, _n in sorted(infeasible, key=lambda r: -r[1]):
        paired = sorted(zip(reported[cls], names[cls]), key=lambda x: x[0])
        lo, hi = core_window([r for r, _ in paired])
        core = paired[lo:hi + 1]
        out = paired[:lo] + paired[hi + 1:]
        triage_total += len(out)
        shown = ", ".join(f"`{a}` ({r * 100:.0f}%)" for r, (a, _i) in out[:5])
        more = "" if len(out) <= 5 else f" +{len(out) - 5} more"
        cspan = core[-1][0] / core[0][0] if core else 0
        print(f"| `{cls}` | {len(core)}/{len(paired)} | {cspan:.1f}x | {shown}{more} |")

    print(f"\n**{triage_total} members across those classes sit outside their current-anchor "
          "ratio window.** Each is one of three things, and only a maintainer can say which:")
    print("  * misclassified — `futuretech_blackwidow` is in `melee` with a range of 9000, "
          "and `corrino_buggy` is in `mbt`;")
    print("  * a legitimate higher tier that needs a tech-tier gate rather than a wider band;")
    print("  * genuinely mis-stated, which is what the pipeline exists to fix.")
    print("\n⛔ Until that triage happens, no baseline for these classes can be signed: the "
          "current-anchor window does not determine class membership or baseline feasibility.")

    print("\n## The fitted baselines, on the grid\n")
    print("| class | hp0 | speed0 | range0_wdist | dps0 | (cost0 unchanged — it cannot move the band) |")
    print("|---|--:|--:|--:|--:|---|")
    for cls, _n, _n0, _nk, _span, k, _lo, _hi, spec in sorted(rows):
        vals = {}
        for key, step in STEPS.items():
            vals[key] = max(step, round(spec[key] * k / step) * step)
        print(f"| `{cls}` | {vals['hp0']:g} | {vals['speed0']:g} | {vals['range0_wdist']:g} | "
              f"{vals['dps0']:g} | {spec['cost0']:g} |")

    if args.triage:
        specs = {c: a["spec"] for c, a in anchors.items()
                 if (a.get("spec") or {}).get("dps0") and a["spec"].get("range0_wdist")}
        print()
        print("## Per-outlier evidence — FOR A MAINTAINER DECISION, never applied")
        print()
        print("A member is listed when it sits outside its current-anchor ratio window.")
        print()
        print("⛔ **The band does not determine class membership or baseline feasibility.** "
              "Measured: the median member is accepted by **6 of 27** class baselines "
              "(mean 5.6, max 9), so \"another class would take it\" is true of nearly "
              "everything and is not evidence. `anchor_readiness.py` says why — these classes "
              "are *\"separated by what they SHOOT AT, not by their stats. No stat-based check "
              "can police these boundaries.\"* An earlier version of this table used the "
              "best-fitting class as the deciding signal and labelled 81 of these "
              "MISCLASSIFIED, which put `terran_ghost` in `artillery` on one arbitrary pick "
              "out of six. The `accepts` column is therefore a COUNT, and only 0 or 1 "
              "discriminates.")
        print()
        print("| class | actor | % of own baseline | worst axis vs core | accepts | signal | evidence |")
        print("|---|---|--:|---|--:|---|---|")
        counts = collections.Counter()
        axes = collections.Counter()
        for cls in sorted(by_class):
            if cls not in specs:
                continue
            paired = sorted(zip(reported[cls], names[cls], by_class[cls]), key=lambda x: x[0])
            lo, hi = core_window([r for r, _n, _m in paired])
            core = paired[lo:hi + 1]
            if len(core) == len(paired):
                continue
            med = {ax: statistics.median([n[1][ax] for _r, n, _m in core])
                   for ax in AXES if all(n[1].get(ax) for _r, n, _m in core)}
            core_tier = statistics.median([n[1]["tier"] for _r, n, _m in core])
            for r, (actor, inp), member in paired[:lo] + paired[hi + 1:]:
                ax, factor = worst_axis(inp, med)
                cands = candidate_classes(member, specs, anchor_tiers, cls)
                verdict, why = propose(r, ax, factor, cands, inp.get("tier"), core_tier)
                counts[verdict] += 1
                if ax and (factor > 1.25 or factor < 0.8):
                    axes[ax] += 1
                fits = str(len(cands))
                axs = f"{ax} {factor:.1f}x" if ax else "—"
                print(f"| `{cls}` | `{actor}` | {r * 100:.0f}% | {axs} | {fits} | "
                      f"**{verdict}** | {why} |")
        print()
        print("**Signal counts:** " +
              ", ".join(f"{v} {k}" for k, v in counts.most_common()))
        print()
        print("**Which axis puts them outside their core:** " +
              ", ".join(f"{v} {k}" for k, v in axes.most_common()))
        print()
        print("⭐ `raw_dps` dominates, and that agrees with the binding order of operations "
              "rather than fighting it: `BALANCE_PROGRAM_PLAN.md` §0a puts weapon STRUCTURE "
              "before pricing, W24 is still moving, and every anchor dossier already says "
              "*\"No DPS target is proposed while W24 moves\"*. So the majority of band "
              "failures are attributable to the one axis the pipeline has deliberately not "
              "settled — the band cannot be fitted before W24 closes, and the DPS-driven "
              "outliers here are not yet evidence about class membership.")
        print()
        print("⚠ `AXIS OUTLIER` is the only line that is checkable without a role "
              "judgement: one stat sits more than 2x off its class core, which is a fact "
              "about the unit. `ROLE REVIEW` means the stats genuinely cannot decide it.")

    return 1 if mismatched else 0


if __name__ == "__main__":
    sys.exit(main())
