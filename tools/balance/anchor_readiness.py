#!/usr/bin/env python3
"""anchor_readiness.py — which class anchors can actually be signed off, and why not.

    python tools/balance/anchor_readiness.py
    python tools/balance/anchor_readiness.py --json out.json

WHY THIS IS THE CRITICAL PATH
-----------------------------
Pricing is blocked on class anchors and **0 of 27 are signed off**. Nothing said
WHY. This measures it.

`fit_class.py` validates an anchor by pricing every MEMBER of its class from that
anchor's spec, so an anchor is only signable if (a) it has members and (b) those
members sit near it in the space DESIGN §12 prices in:

    Cost = cost0 * (O/O0 + P/P0 + Q/Q0) / 3

This reports, per class, how far its tagged members actually sit from its anchor.
A class whose members cluster tightly can be validated today; one whose members
are scattered will produce large residuals and needs its anchor or its membership
revisited first. That turns "0 of 27, unknown why" into a work order.

WHAT THE MEASUREMENT FOUND (2026-08-29)
---------------------------------------
* **Median distance from a tagged unit to its OWN anchor: 1.95.**
* **Median distance between two DIFFERENT anchors: 1.21.**

Units are FURTHER from their own class anchor than the anchors are from each
other. So class membership is not recoverable from (hp, dps, range, speed): a
nearest-anchor classifier scores **17.6%** against the 346 known labels, and that
number is reported here as evidence rather than hidden — see `--classifier`.

That is not automatically a defect. It says class is a ROLE judgement, which is
why `fit_class.py` step 1 has the maintainer tag members by hand. But it has two
consequences the pipeline must respect:

* Several anchors are statistically indistinguishable — `anti_air_vehicle` and
  `missile_vehicle` sit **0.024** apart, `archer` and `flying_infantry` 0.048,
  `rocket_trooper` and `special_forces` 0.053. They are separated by what they
  SHOOT AT, not by their stats, so no stat-based check can police their boundary.
* Classes differ enormously in how well their anchor describes them, from
  `support` at 0.24 to `melee` at 12.04. They are NOT equally ready to sign, and
  signing them as one batch would bake the loose ones in.

⚠ Cost is deliberately NOT a feature. Cost is what the formula SOLVES FOR;
feeding it back would let a mispriced unit justify its own class and make the
anchor fit look better than it is.
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import statistics
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
import class_membership  # noqa: E402
import formula  # noqa: E402

LEDGER = ROOT / "docs" / "balance"
TICKS_PER_SECOND = 25

FEATURES = ("hp", "dps", "range", "speed")
SPEC_KEY = {"hp": "hp0", "dps": "dps0", "range": "range0_wdist", "speed": "speed0"}

# `dps` is deliberately NOT compared against `spec.dps0` in anchor_actor_vs_spec. The two are
# not on the same scale — `unit_dps` here reads raw per-shot damage out of the ledger while a
# spec dps0 is the design ladder's figure — and, more importantly, the decisions log marks the
# DPS restat DEFERRED to the cannon/weapon rebuild ("current in-game DPS is confounded by
# warhead-mixing"). Reporting that gap as anchor drift would publish ~20x "mismatches" that are
# a units difference plus a known deferral, not a finding.
SPEC_COMPARABLE = ("hp", "range", "speed")


def fnum(v):
    if v is None:
        return None
    try:
        value = float(str(v).strip())
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def unit_dps(unit):
    """Peak nominal single-armament DPS, with full burst cadence.

    This diagnostic is not summed live output, a matchup model, or a sign-off:
    activation conditions, charge traits and actor modifiers are not modeled.
    """
    best = None
    for arm in unit.get("armaments") or []:
        if not arm.get("pricing"):
            continue
        reload_ = fnum(arm.get("reloaddelay"))
        if reload_ is None or reload_ <= 0:
            continue
        damage = 0.0
        for wh in arm.get("damage_warheads") or []:
            if (wh.get("type") or "") == "AreaDamagePercentage":
                continue                     # a percentage twin, not flat damage
            d = fnum(wh.get("damage"))
            if d:
                damage += d
        if damage <= 0:
            continue
        burst = fnum(arm.get("burst", 1))
        if burst is None or burst < 1 or not burst.is_integer():
            continue
        if "burstdelays" in arm:
            delays = formula.burst_delay_values(arm["burstdelays"])
            if not delays or (burst > 1 and len(delays) not in (1, int(burst) - 1)):
                continue
        if formula.eff_reload(reload_, int(burst), arm.get("burstdelays")) <= 0:
            continue
        dps = formula.dps(damage, reload_, int(burst), arm.get("burstdelays")) * TICKS_PER_SECOND
        best = dps if best is None else max(best, dps)
    return best


def unit_range(unit):
    best = None
    for arm in unit.get("armaments") or []:
        r = formula.wdist_value(arm.get("range"))
        if r:
            best = r if best is None else max(best, r)
    return best


def features(unit):
    return {"hp": fnum((unit.get("hp") or {}).get("v")),
            "dps": unit_dps(unit),
            "range": unit_range(unit),
            "speed": fnum((unit.get("speed") or {}).get("v")
                          if (unit.get("speed") or {}).get("v") is not None
                          else (unit.get("speed_air") or {}).get("v"))}


def load_units():
    """[(faction, section, name, record)] over every ledger."""
    out = []
    for path in sorted(glob.glob(str(LEDGER / "*.json"))):
        if "class_anchors" in path:
            continue
        try:
            doc = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ValueError(f"readiness unavailable: cannot read {path}: {exc}") from exc
        for section, units in (doc.get("sections") or {}).items():
            if not isinstance(units, dict):
                continue
            for name, rec in units.items():
                if isinstance(rec, dict):
                    out.append((doc.get("ledger", ""), section, name, rec))
    return out


def coverage_counts(units):
    """Report ledger-row coverage without calling structures unclassified units."""
    counts = collections.Counter()
    for _f, _s, _n, rec in units:
        if not rec.get("buildable"):
            continue
        cls, reason = class_membership.classify(rec.get("design") or {})
        counts["buildable_rows"] += 1
        counts[reason] += 1
        counts["classified_rows"] += bool(cls)
        counts["non_structural_rows"] += reason != "not-a-unit"
    return counts


def distance(feat, spec):
    """Mean squared log-ratio over the features both sides define."""
    terms = []
    for key in FEATURES:
        got, want = feat.get(key), fnum(spec.get(SPEC_KEY[key]))
        if got is None or not want or got <= 0:
            continue
        terms.append(math.log(got / want) ** 2)
    if not terms:
        return None
    return sum(terms) / len(terms)


def predict(feat, section, anchors, sections_of):
    """(class, distance, runner_up_distance) or (None, ...) when unclassifiable."""
    scored = []
    for cls, entry in anchors.items():
        if cls.startswith("_"):
            continue
        allowed = sections_of.get(cls)
        if allowed and section not in allowed:
            continue                          # never cross an aircraft into a tank class
        d = distance(feat, entry.get("spec") or {})
        if d is not None:
            scored.append((d, cls))
    if not scored:
        return None, None, None
    scored.sort()
    runner = scored[1][0] if len(scored) > 1 else None
    return scored[0][1], scored[0][0], runner


VALIDATION = re.compile(
    r"\|\s*`([^`]+)`\s*\|\s*([\d.]+)\s*\|\s*(.+?)\s*\|\s*([+-]?\d+)%")


def residuals():
    """{class: [abs percent error]} from fit_class.py's validation tables.

    ⚠ THIS, NOT STAT DISTANCE, IS READINESS. A class can cluster tightly in
    (hp, dps, range, speed) and still price badly, because the formula weights
    those axes against an anchor rather than measuring nearness to it —
    `fire_support` has a tight 0.88 median distance and a 35% median pricing
    error. Only the residual says whether an anchor can be signed.
    """
    out, unscored = {}, {}
    for path in sorted(LEDGER.glob("formula_v2_*.md")):
        cls = path.stem.replace("formula_v2_", "")
        if cls == "classes":                   # a design note, not a fit table
            continue
        deltas, nostats = [], 0
        for line in path.read_text(encoding="utf-8").splitlines():
            m = VALIDATION.match(line)
            if m:
                deltas.append(abs(int(m.group(4))))
            elif "(no combat stats)" in line:
                nostats += 1
        if deltas:
            out[cls] = deltas
            unscored[cls] = nostats
    return out, unscored


def anchor_spread(anchors):
    """Pairwise distance between anchor SPECS — how separable the classes are."""
    specs = {k: (v.get("spec") or {}) for k, v in anchors.items()
             if not k.startswith("_")}
    pairs = []
    for a in specs:
        for b in specs:
            if a >= b:
                continue
            feat = {k: fnum(specs[a].get(SPEC_KEY[k])) for k in FEATURES}
            d = distance(feat, specs[b])
            if d is not None:
                pairs.append((d, a, b))
    return sorted(pairs)


def anchor_actor_vs_spec(anchors, units):
    """Does each class's ANCHOR ACTOR actually carry the stats its spec rules for it?

    PRIOR ART: this file already measures how far MEMBERS sit from `spec` (`residuals`,
    `distance`). What it never checked is the zero point itself — whether the nominated
    anchor ACTOR is at its ruled stats, and whether the FITTED `cost0` agrees with
    `spec.cost0`. Those are different questions and the second one gates sign-off.

    `class_anchors.json` holds two things per class, both correct:
      * `spec.{cost0,hp0,speed0,dps0,range0_wdist}` — the LOCKED target from
        `docs/balance/anchor_decisions_log.md` (the source of truth for anchors).
      * top-level `cost0/o0/p0/q0` — FITTED from the anchor actor as it exists in yaml TODAY.

    They disagree because the decisions log's own PER-UNIT APPLICATION LAW step 1 — "2c sets
    ONLY the 13 baseline actors to the exact table stats" — has not run. Since
    `price = cost0 * (h + r + d) / 3`, the anchor IS the class's zero point, so signing a
    class freezes whatever the actor happens to be. Measured 2026-08-30: 0 of 13 vehicle
    anchor actors were at their locked stats and 13 of 26 classes had fitted cost0 !=
    spec.cost0, worst `tank_destroyer` at 2.17x.
    """
    rows = []
    for cls in sorted(anchors):
        entry = anchors[cls]
        if cls.startswith("_") or not isinstance(entry, dict) or not entry.get("anchor_actor"):
            continue
        spec = entry.get("spec") or {}
        fitted, want = fnum(entry.get("cost0")), fnum(spec.get("cost0"))
        actor = entry.get("anchor_actor")
        rec = units.get(actor)
        off = []
        if rec is not None:
            feat = features(rec)
            for key in SPEC_COMPARABLE:
                got, target = feat.get(key), fnum(spec.get(SPEC_KEY[key]))
                if got is None or target in (None, 0):
                    off.append(f"{key} unavailable ({'measured' if got is None else 'target'})")
                    continue
                # range comes from armaments and carries per-weapon jitter; the ladder
                # itself moves in steps of 500, so anything inside 250 is on target.
                tol = 250 if key == "range" else 0
                if abs(got - target) > tol:
                    off.append(f"{key} {got:g}!={target:g}")
        ratio = (fitted / want) if (fitted and want) else None
        rows.append((cls, actor, rec is not None, fitted, want, ratio, off,
                     fitted is not None and
                     entry.get("o0") == entry.get("p0") == entry.get("q0") == fitted))
    return rows


def three_way_split_gate(units, classes):
    """Which class members still fire MORE THAN ONE main damage warhead (W24 debt).

    PRIOR ART: the predicate is `audit_three_way_split.main_warhead_nodes` and it is IMPORTED,
    not restated. That audit's own docstring records it being wrong once — a source-yaml scan
    could not tell an OVERRIDE from an ADDITION and reported 393 against a number that was
    simultaneously too high and too low — so it now measures the RESOLVED node. Re-deriving the
    predicate here would re-introduce exactly that bug in a second place.

    WHY THIS GATES EVERYTHING ELSE. §0a of BALANCE_PROGRAM_PLAN is binding and is the maintainer's
    own ruling (2026-08-17): *"shouldn't we first finish the 3 way split like documented before we
    start applying the balance formula to our actors? It would be double work splitting the multi
    warheads later on."* A price is a function of K, and K is share-weighted over each warhead's
    armor profile — so collapsing N mains into 1 preserves the damage SUM but MOVES K, and
    therefore moves the price. Pricing a member before its weapons are split prices an input that
    is about to be replaced. `class_anchors.json` said so first: mbt.provisional carries
    "DPS restat DEFERRED to the cannon/weapon rebuild."

    So the real order for a class is:

        3-way split its members  ->  set the baseline actor (2c)  ->  synthesise the members

    and this reports how much of step 1 each class still owes.
    """
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
    try:
        import audit_three_way_split as tws
        import miniyaml
    except ImportError as exc:                  # keep readiness usable without the audit tree
        return None, f"split gate unavailable: {exc}"

    try:
        rules = miniyaml.Ruleset(ROOT)
    except Exception as exc:
        return None, f"split gate unavailable: cannot load active rules: {exc}"
    debt = collections.defaultdict(list)
    counted = collections.Counter()
    for actor, rec in units.items():
        cls = classes.get(actor)
        if not cls:
            continue
        counted[cls] += 1
        worst, worst_w = 0, None
        for arm in rec.get("armaments") or []:
            wname = arm.get("weapon") or arm.get("name")
            if not wname:
                # the ledger stores the weapon under whichever key extract_stats had; fall back
                # to the slot's template list, whose LAST entry is the concrete weapon.
                tpl = arm.get("versus_templates") or []
                wname = tpl[-1] if tpl else None
            if not wname:
                return None, f"split gate unavailable: {actor} has an unidentified armament"
            try:
                resolved = rules.resolve_weapon(wname)
            except Exception as exc:
                return None, f"split gate unavailable: {actor}/{wname}: {exc}"
            if resolved is None:
                return None, f"split gate unavailable: unresolved weapon {actor}/{wname}"
            mains = tws.main_warheads(resolved)
            # Raw structure counts include reviewed composites; review status is
            # a separate decision, never an exemption from measurement.
            if len(mains) > 1:
                if len(mains) > worst:
                    worst, worst_w = len(mains), (wname, mains)
        if worst > 1:
            debt[cls].append((actor, worst_w[0], worst))
    return (debt, counted), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write the readiness table here")
    ap.add_argument("--propose-anchors", action="store_true",
                    help="rank each class's members as candidate anchors by SWEET-SPOT "
                         "OCCUPANCY (BALANCE_PIPELINE 8.1), and report which classes are "
                         "wider than the band itself. Evidence for a ruling, never an assignment.")
    ap.add_argument("--classifier", action="store_true",
                    help="also self-score a nearest-anchor classifier on the "
                         "known labels (the 17.6% evidence)")
    args = ap.parse_args()

    anchors = json.loads((LEDGER / "class_anchors.json").read_text(encoding="utf-8"))
    units = load_units()
    # ⛔ MEMBERSHIP COMES FROM THE TEMPLATE, NOT FROM THE HAND TAG (PRIORITY 0 item 1,
    # 2026-09-02). Reading `design.class_anchor` raw was why this board said 18%: the tag is a
    # hand-maintained copy covering a third of the roster, while `design.subtype` -- the
    # ^<Name>Template the actor inherits -- is re-derived from yaml for every row on every
    # extract. `class_membership.classify` prefers an explicit tag and falls back to the
    # template, which takes coverage from 346 to 660 of 993 units with no new tagging.
    tagged = [(f, s, n, r) for f, s, n, r in units
              if class_membership.classify(r.get("design") or {})[0]]

    coverage = coverage_counts(units)
    buildable = coverage["buildable_rows"]
    classes = [c for c in anchors if not c.startswith("_")]
    signed = [c for c in classes if anchors[c].get("signed_off")]

    print("# Class anchor readiness\n")
    print(f"classes defined      : {len(classes)}")
    print(f"signed off           : **{len(signed)}**")
    print(f"buildable ledger rows: {buildable} (includes structures and upgrades)")
    tagged_buildable = sum(1 for _f, _s, _n, r in units
                           if r.get("buildable")
                           and class_membership.classify(r.get("design") or {})[0])
    print(f"tagged with a class  : {tagged_buildable} of the buildable "
          f"({tagged_buildable / buildable * 100 if buildable else 0:.1f}%); {len(tagged)} including "
          "non-buildable\n")
    candidates = coverage["non_structural_rows"]
    print(f"excluding structure/upgrade rows: {tagged_buildable} of {candidates} "
          f"({100 * tagged_buildable / candidates if candidates else 0:.1f}%) classified")
    print(f"remaining buildable gaps: {coverage['no-template']} without a unit template; "
          f"{coverage['no-class-exists']} without a defined class; "
          f"{coverage['unmapped']} unmapped templates. These are rows, not deduplicated units.\n")

    # --- ⛔ ANCHOR INTEGRITY — measured 2026-08-30, and it outranks the fit table ---- #
    #
    # A class formula measures its members against the ANCHOR, so the anchor has to BE a
    # member and it has to sit somewhere near the middle of what it describes. Neither was
    # ever checked, and the sign-off queue below cannot see the difference between "this
    # class fits badly" and "this class has nothing to fit".
    #
    # What the first run found: 10 of 27 anchors carry NO class tag at all, 5 classes have
    # ZERO tagged members (3 of them SIGNED), and `special_forces` -- 15 members, signed --
    # anchors on an actor at the 13th percentile of its own class. That last one IS its 57%
    # median pricing error: the zero point is an outlier at the bottom of the population it
    # defines, so every member is measured against a ruler planted in the wrong place.
    # Fixable by moving the anchor, without touching the formula.
    tag_of = {n: class_membership.classify(r.get("design") or {})[0]
              for _f, _s, n, r in tagged}
    hp_of = {}
    for _f, _s, n, r in units:
        v = r.get("hp")
        v = v.get("v") if isinstance(v, dict) else v
        try:
            hp_of[n] = float(v)
        except (TypeError, ValueError):
            pass
    by_class = collections.defaultdict(list)
    for n, c in tag_of.items():
        by_class[c].append(n)

    untagged_anchor, empty, off_centre = [], [], []
    for cls in classes:
        a = (anchors.get(cls) or {}).get("anchor_actor")
        sg = " **SIGNED**" if anchors[cls].get("signed_off") else ""
        if not by_class.get(cls):
            empty.append(f"{cls}{sg}")
        if a and tag_of.get(a) != cls:
            untagged_anchor.append(f"{cls} -> `{a}` ({tag_of.get(a) or 'UNTAGGED'}){sg}")
        elif a and a in hp_of:
            hps = sorted(hp_of[n] for n in by_class[cls] if n in hp_of)
            if len(hps) >= 4:
                pct = 100 * sum(1 for h in hps if h <= hp_of[a]) / len(hps)
                if pct <= 25 or pct >= 75:
                    off_centre.append(f"{cls} -> `{a}` at the {pct:.0f}th percentile of "
                                      f"{len(hps)} members{sg}")

    if args.propose_anchors:
        # ⭐ RANKED BY THE RULED CRITERION, NOT A PROXY I INVENTED.
        #
        # The first version of this mode ranked candidates by CENTRALITY — how close a member
        # sits to its class median. That was a guess. The maintainer asked the right question:
        # "must the anchor be at the CENTRE of the band?" — and the answer was already ruled.
        # `check_band.py` enforces BALANCE_PIPELINE §8.1:
        #
        #     hard band     50%..400% of cost0
        #     target band  72.9%..250% of cost0, target >=80% occupancy
        #
        # ⚠ 72.9%, not 75%: BALANCE_PIPELINE §8.1a — the ring is the price of a STAT
        # window, and 3/4 of the anchor's HP and DPS costs 0.729, not 0.75.
        #
        # So the anchor is the FLOOR of the sweet spot — the cheapest typical member — and the
        # class extends UPWARD from it. It is deliberately NOT the centre. Centrality would
        # have moved every anchor to the wrong place.
        #
        # This therefore scores each candidate by what actually matters: if THIS actor were the
        # anchor, how much of the class lands in 72.9%..250%? That is the law, computed, and it
        # imports check_band's pricing so there is ONE implementation of it.
        #
        # ⛔ Still evidence for a ruling, never an assignment: an anchor must also be
        # ROLE-typical (the class's recognisable entry unit), and no stat can see role.
        sys.path.insert(0, str(ROOT / "tools" / "balance"))
        import check_band as cb
        SWEET_WIDTH = cb.SWEET_HI / cb.SWEET_LO

        tier_map = {}
        rows_by_class = collections.defaultdict(list)
        for _fn, actor, u, du in cb.collect(tier_map):
            cls = class_membership.classify(u.get("design") or {})[0]
            if not cls or cls not in anchors:
                continue
            inp = cb.unit_inputs(u, du)
            if inp is None:
                continue
            cost = cb.fnum((u.get("cost") or {}).get("v")
                           if isinstance(u.get("cost"), dict) else u.get("cost"))
            rows_by_class[cls].append((actor, inp, cost, bool(u.get("build_limit"))))

        def occupancy(cls, spec, rows):
            """Share of non-epic members landing in the sweet spot under `spec`."""
            hits = tot = 0
            for _a, inp, _c, epic in rows:
                if epic:
                    continue
                pr = cb.price_for(cls, {"spec": spec}, inp, 1.0)
                if pr is None or not spec.get("cost0"):
                    continue
                tot += 1
                if cb.SWEET_LO <= pr / spec["cost0"] <= cb.SWEET_HI:
                    hits += 1
            return (hits / tot if tot else None), tot

        print("# Candidate anchors — ranked by SWEET-SPOT OCCUPANCY (BALANCE_PIPELINE §8.1)\n")
        print("The anchor sits at the LOWER QUARTILE of the target band "
              "(72.9%–250% of `cost0`, §8.1a), not at its centre: "
              "the cheapest TYPICAL member, with the class extending upward. Each candidate is "
              "scored by how much of its class would land in that band if it were the anchor.\n")
        print("⛔ Evidence for a ruling, never an assignment — an anchor must also be the "
              "class's recognisable ENTRY unit, and no stat can see role.\n")
        for cls in sorted(classes):
            rows = rows_by_class.get(cls) or []
            if len(rows) < 4:
                continue
            cand = []
            for actor, inp, cost, epic in rows:
                hp, speed, rng, dps_v, _sp, _uc, _t = inp
                if not (hp and speed and rng and dps_v and cost):
                    continue
                spec = {"hp0": hp, "speed0": speed, "range0_wdist": rng,
                        "dps0": dps_v, "cost0": cost}
                occ, tot = occupancy(cls, spec, rows)
                if occ is not None:
                    cand.append((occ, actor, tot))
            if not cand:
                continue
            cand.sort(key=lambda r: -r[0])
            cur = (anchors.get(cls) or {}).get("anchor_actor")
            cur_occ = next((f"{o:.0%}" for o, a, _ in cand if a == cur), None)
            sg = " **SIGNED**" if anchors[cls].get("signed_off") else ""

            # ⛔ THE CEILING ON RE-ANCHORING. A class's members are priced by RATIOS to the
            # anchor, so moving the anchor SLIDES the whole class along the band — it never
            # narrows it. The sweet spot is SWEET_HI/SWEET_LO = 2.5x wide, so a class whose
            # own priced spread exceeds 2.5x CANNOT reach 100% occupancy from ANY anchor.
            # That is arithmetic, not a tuning failure: those classes need their MEMBERS
            # repriced (which is what the pipeline is for) or their SCOPE narrowed.
            best = cand[0][0]
            width = None
            ref = {"hp0": None}
            spread_rows = []
            for actor, inp, cost, epic in rows:
                if epic:
                    continue
                hp, speed, rng, dps_v, _sp, _uc, _t = inp
                if not (hp and speed and rng and dps_v and cost):
                    continue
                spread_rows.append((actor, inp))
            if len(spread_rows) >= 2:
                a0, i0 = spread_rows[0]
                h0, s0, r0, d0, _a, _b, _c = i0
                base = {"hp0": h0, "speed0": s0, "range0_wdist": r0,
                        "dps0": d0, "cost0": 100.0}
                pr = [cb.price_for(cls, {"spec": base}, i, 1.0) for _a, i in spread_rows]
                pr = [x for x in pr if x and x > 0]
                if len(pr) >= 2:
                    width = max(pr) / min(pr)

            print(f"### `{cls}` — {cand[0][2]} priced members{sg}\n")
            print(f"current anchor `{cur}`: "
                  f"**{cur_occ + ' occupancy' if cur_occ else 'not a priced member'}** "
                  f"(target >=80%)\n")
            if width is not None:
                verdict = ("any anchor can reach 100%" if width <= SWEET_WIDTH
                           else f"⛔ NO anchor can reach 100% — the class is "
                                f"{width / SWEET_WIDTH:.1f}x TOO WIDE")
                print(f"priced spread across the class: **{width:.1f}x** "
                      f"against a **{SWEET_WIDTH:.1f}x** sweet spot -> {verdict}\n")
            print(f"best achievable occupancy from any member: **{best:.0%}**\n")
            for occ, actor, _ in cand[:3]:
                mark = "  ← current" if actor == cur else ""
                print(f"  {occ:>5.0%}  `{actor}`{mark}")
            print()
        return 0

    print("## Anchor integrity — class membership and diagnostic HP percentiles\n")
    print(f"anchors tagged into the class they anchor : "
          f"**{len(classes) - len(untagged_anchor)} of {len(classes)}**\n")
    if empty:
        print(f"**{len(empty)} classes have ZERO tagged members** — nothing to fit, and a "
              "one-member fit table reads 0% because an anchor prices ITSELF at 0%:\n")
        for e in sorted(empty):
            print(f"  - {e}")
        print()
    if untagged_anchor:
        print(f"**{len(untagged_anchor)} anchors are not tagged into their own class** — the "
              "zero point sits outside the population it defines:\n")
        for e in sorted(untagged_anchor):
            print(f"  - {e}")
        print()
    if off_centre:
        print("**Anchors outside the middle half of current member HP.** This is descriptive, "
              "not a failed rule: the intended anchor is a typical entry unit, not necessarily "
              "the median. Existing role rulings and deferred restats take precedence. "
              "Do not move anchors from this percentile alone.\n")
        for e in sorted(off_centre):
            print(f"  - {e}")
        print()

    # --- per-class fit ------------------------------------------------------ #
    members = collections.defaultdict(list)
    for _f, _s, _n, rec in tagged:
        cls = class_membership.classify(rec.get("design") or {})[0]
        d = distance(features(rec), (anchors.get(cls) or {}).get("spec") or {})
        if d is not None:
            members[cls].append(d)

    resid, unscored = residuals()
    rows = []
    for cls in classes:
        ds = members.get(cls) or []
        rs_ = resid.get(cls) or []
        # A class "scored" only on members the formula could actually price, and
        # a table containing nothing but its own anchor proves nothing: the
        # anchor prices itself at exactly 0% by construction.
        scored = len(rs_)
        rows.append({
            "class": cls,
            "members": len(ds),
            "scored": scored,
            "median_error_pct": round(statistics.median(rs_)) if rs_ else None,
            "within_10pct": round(sum(1 for d in rs_ if d <= 10) / scored * 100)
                            if scored else None,
            "worst_error_pct": max(rs_) if rs_ else None,
            "unpriceable": unscored.get(cls, 0),
            "signed_off": bool(anchors[cls].get("signed_off")),
        })
    rows.sort(key=lambda r: (r["median_error_pct"] is None,
                             r["median_error_pct"] if r["median_error_pct"] is not None else 0,
                             -(r["scored"] or 0)))

    print("## Fit-review queue — ranked by pricing residual, not sign-off eligibility\n")
    print("`median |Δ|` is how far the class formula's price sits from the unit's "
          "actual cost, from `fit_class.py`'s validation table. **A class needs at "
          "least 3 scored members to mean anything** — an anchor prices itself at "
          "0% by construction.\n")
    print("| class | scored | median \\|Δ\\| | within 10% | worst | verdict |")
    print("|---|--:|--:|--:|--:|---|")
    ready = blocked = empty = 0
    for r in rows:
        if r["median_error_pct"] is None:
            verdict = "⛔ not fitted — no anchor, or the anchor has no stats"
            empty += 1
        elif r["scored"] < 3:
            verdict = f"⚠ only {r['scored']} scored — too few to judge"
            blocked += 1
        elif r["median_error_pct"] <= 10:
            verdict = "low residual — structure, spec and role review still required"
            ready += 1
        elif r["median_error_pct"] <= 25:
            verdict = "review outliers and prerequisite gates"
            blocked += 1
        else:
            verdict = "large residual — review inputs, membership and current prices"
            blocked += 1
        cells = [f"`{r['class']}`", str(r["scored"]),
                 f"{r['median_error_pct']}%" if r["median_error_pct"] is not None else "—",
                 f"{r['within_10pct']}%" if r["within_10pct"] is not None else "—",
                 f"{r['worst_error_pct']}%" if r["worst_error_pct"] is not None else "—",
                 verdict]
        print("| " + " | ".join(cells) + " |")

    alld = [d for ds in members.values() for d in ds]
    pairs = anchor_spread(anchors)
    print(f"\n**{ready} classes have low pricing residuals**, {blocked} need fit review, "
          f"{empty} could not be fitted. Residuals alone never authorize sign-off.\n")
    if alld and pairs:
        own = statistics.median(alld)
        between = statistics.median([d for d, _a, _b in pairs])
        print(f"Median distance to OWN anchor: **{own:.2f}**. Median distance "
              f"BETWEEN anchors: **{between:.2f}**.")
        if own > between:
            print("\n⚠ Units sit FURTHER from their own class anchor than the "
                  "anchors sit from each other, so the class boundaries are not "
                  "recoverable from stats — they are role judgements. Any check "
                  "that tries to police membership numerically will be wrong.")

    spec_rows = anchor_actor_vs_spec(anchors, {n: rec for _f, _sec, n, rec in units})
    drift = [r for r in spec_rows if r[5] is not None and abs(r[5] - 1.0) > 1e-9]
    offspec = [r for r in spec_rows if r[6]]
    gate, gate_err = three_way_split_gate(
        {n: r for _f, _sec, n, r in units}, {n: class_membership.classify(r.get("design") or {})[0]
                                             for _f, _sec, n, r in units})
    print("\n## The 3-way split gate — what must be fixed BEFORE a class is priced\n")
    print("§0a of `BALANCE_PROGRAM_PLAN.md` is binding: weapon structure comes before pricing. "
          "Changing armor profiles can change `K` even when total damage is preserved. "
          "These are raw resolved main-warhead counts, including reviewed composites; "
          "a finding requires review, not an automatic collapse.\n")
    if gate_err:
        print(f"⚠ {gate_err}\n")
    else:
        debt, counted = gate
        tot = sum(len(v) for v in debt.values())
        print(f"* class-tagged members still firing 2+ main warheads: **{tot}**\n")
        if debt:
            print("| class | members with stacked mains | of tagged | largest stack |")
            print("|---|--:|--:|---|")
            for cls in sorted(debt, key=lambda c: -len(debt[c])):
                stack_rows = sorted(debt[cls], key=lambda r: -r[2])
                a, w, n = stack_rows[0]
                print(f"| `{cls}` | {len(stack_rows)} | {counted[cls]} | "
                      f"`{a}` via `{w}` ({n} mains) |")
        clean = sorted(c for c in counted if not debt.get(c))
        print(f"\n**{len(clean)} class(es) have no observed stacked-main finding"
              + (": " + ", ".join(f"`{c}`" for c in clean) if clean else "") + ".** "
              "This is not full weapon-structure clearance or anchor sign-off.")

    print("\n## Anchor actor vs its ruled spec\n")
    print("`spec.*` is the LOCKED target from `anchor_decisions_log.md`; the top-level "
          "`cost0/o0/p0/q0` are FITTED from the anchor actor as it stands in yaml today. "
          "They disagree wherever the decisions log's application-law step 2c (restat the "
          "baseline actors to the table) has not run. Formula V2 averages the normalized "
          "O/P/Q terms; the anchor defines their baseline, so missing or mismatched "
          "baselines require review before sign-off.\n")
    print(f"* fitted `cost0` != `spec.cost0`: **{len(drift)} of {len(spec_rows)}** classes")
    print(f"* missing fitted or target cost baseline: **{sum(r[5] is None for r in spec_rows)}**")
    print(f"* anchor actor off its ruled stats: **{len(offspec)} of {len(spec_rows)}** "
          "(of those whose actor is in a ledger)")
    ident = [r[0] for r in spec_rows if r[7]]
    print(f"* satisfying the baseline identity `o0 = p0 = q0 = cost0`: "
          f"**{len(ident)} of {len(spec_rows)}**"
          + (f" ({', '.join('`%s`' % c for c in ident)})" if ident else "") + "\n")
    if drift or offspec:
        print("| class | anchor actor | fitted cost0 | spec cost0 | ratio | actor off spec |")
        print("|---|---|--:|--:|--:|---|")
        for cls, actor, seen, fitted, want, ratio, off, _id in spec_rows:
            if ratio is not None and abs(ratio - 1.0) < 1e-9 and not off:
                continue
            note = ", ".join(off) if off else ("not in a ledger" if not seen else "on spec")
            rs = f"{ratio:.2f}x" if ratio is not None else "-"
            fitted_text = f"{fitted:g}" if fitted is not None else "unavailable"
            wanted_text = f"{want:g}" if want is not None else "unavailable"
            print(f"| `{cls}` | `{actor}` | {fitted_text} | "
                  f"{wanted_text} | {rs} | {note} |")

    print("\n## Anchors that are statistically indistinguishable\n")
    print("Separated by what they SHOOT AT, not by their stats. No stat-based "
          "check can police these boundaries.\n")
    for d, a, b in pairs[:8]:
        print(f"  {d:6.3f}  `{a}` <-> `{b}`")

    if args.classifier:
        hit = miss = skipped = 0
        sections_of = collections.defaultdict(set)
        for _f, section, _n, rec in tagged:
            sections_of[class_membership.classify(rec.get("design") or {})[0]].add(section)
        confusion = collections.Counter()
        for _f, section, _n, rec in tagged:
            truth = class_membership.classify(rec.get("design") or {})[0]
            got, _d, _r = predict(features(rec), section, anchors, sections_of)
            if got is None:
                skipped += 1
            elif got == truth:
                hit += 1
            else:
                miss += 1
                confusion[(truth, got)] += 1
        total = hit + miss
        print(f"\n## Classifier self-score (the evidence for 'role, not stats')\n")
        print(f"A nearest-anchor classifier re-predicting the {total} known labels "
              f"scores **{hit / total * 100:.1f}%** top-1.\n")
        for (truth, got), n in confusion.most_common(6):
            print(f"  {truth:22} -> {got:22} {n}")

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps({"rows": rows,
                        "coverage": dict(coverage),
                        "split_gate_error": gate_err,
                        "closest_anchor_pairs": [
                            {"a": a, "b": b, "d": round(d, 4)}
                            for d, a, b in pairs[:12]]},
                       indent=1, sort_keys=True), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 1 if gate_err else 0


if __name__ == "__main__":
    sys.exit(main())
