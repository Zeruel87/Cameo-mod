#!/usr/bin/env python3
"""check_band.py — Balance-pipeline BASEBAND validator (BALANCE_PIPELINE §8.1).

For every ledger unit tagged design.class_anchor = <class>, compute its
class-formula price and the ratio price/cost0, then enforce the baseband law:

  * hard band     50%..400%  of the class baseline cost0
  * practical floor  ~75%   (formula breaks down below — units too weak/price)
  * sweet spot   100%..250%  (baseline..verifier) — target >=80% occupancy

Read-only. Emits a report and a nonzero exit if any member is below 75% or
above 400% (unless it is a BuildLimit:1 epic/hero, which is band-exempt).

Usage: python tools/balance/check_band.py [--class X] [--md docs/audit/latest/band.md]
"""
from __future__ import annotations
import argparse, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import formula  # noqa: E402
import tier_chain  # noqa: E402

LEDGER = ROOT / "docs/balance"
ANCHORS = LEDGER / "class_anchors.json"

FLOOR, SOFT_FLOOR, SWEET_LO, SWEET_HI, CEIL = 0.50, 0.75, 1.00, 2.50, 4.00


def fnum(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def unit_inputs(u, du=None):
    """(hp, speed, range_wdist, dps, special, unit_class, tech_tier) or None."""
    hp = fnum((u.get("hp") or {}).get("v"))
    speed = fnum((u.get("speed") or {}).get("v") or (u.get("speed_air") or {}).get("v"))
    d = u.get("design") or {}
    du = du or {}
    total_dps, best_range = 0.0, 0.0
    for arm in u.get("armaments", []):
        if not arm.get("pricing", True):
            continue
        st = arm.get("stats", arm)  # tolerate both nesting styles
        dmg = formula.spread_damage_sum(st.get("damage_warheads", arm.get("damage_warheads", [])))
        reload_ = fnum((st.get("reload_delay") or {}).get("v") if isinstance(st.get("reload_delay"), dict)
                       else st.get("reloaddelay") or (st.get("reload_delay")))
        if not dmg or not reload_:
            continue
        rng = st.get("range")
        rng = formula.wdist_value(rng, 0.0)
        burst = st.get("burst"); burst = int(fnum(burst.get("v") if isinstance(burst, dict) else burst) or 1)
        # Raw ledgers use ``burstdelays``. Keep the underscored fallback only
        # for the older nested fixture shape this reader still accepts.
        bd = st.get("burstdelays", st.get("burst_delays"))
        total_dps += formula.dps(dmg, reload_, burst, bd)
        best_range = max(best_range, rng)
    if hp is None or speed is None or total_dps == 0:
        return None
    tech_tier = tier_chain.effective_tier(
        d.get("tech_tier"), du.get("tier_multiplier"), default=1.0)
    return (hp, speed, best_range, total_dps,
            fnum(d.get("special")) or 1.0, fnum(d.get("unit_class")) or 1.0,
            tech_tier)


def price_for(cls, anchor, inp, anchor_tier: float = 1.0):
    """Price a unit under its class anchor. Handles both anchor forms."""
    hp, speed, rng, dps_v, special, uclass, tier = inp
    spec = anchor.get("spec")
    if spec:  # class-baseline form (infantry classes)
        if not spec.get("range0_wdist") or not spec.get("dps0"):
            return None  # ability-priced class (e.g. support) — not formula-priced
        # class_baseline_price receives the RELATIVE multiplier.
        rel_tier = tier / anchor_tier if anchor_tier else tier
        return formula.class_baseline_price(
            hp, speed, rng, dps_v,
            spec["hp0"], spec["speed0"], spec["range0_wdist"], spec["dps0"], spec["cost0"],
            special=special, tech_tier=rel_tier)
    if all(k in anchor for k in ("o0", "p0", "q0", "cost0")):  # o/p/q form (mbt)
        # class_anchor_price cancels the anchor's own absolute tier.
        o, p, q = formula.estimators(hp, speed, rng, dps_v, special, uclass, tier)
        return formula.class_anchor_price(o, p, q, anchor["o0"], anchor["p0"], anchor["q0"], anchor["cost0"])
    return None


def cost0_of(anchor):
    return (anchor.get("spec") or {}).get("cost0") or anchor.get("cost0")


def collect(tier_map):
    for jf in sorted(LEDGER.glob("*.json")):
        if jf.name == "class_anchors.json":
            continue
        doc = json.loads(jf.read_text(encoding="utf-8"))
        if "sections" not in doc:
            continue
        for sec in doc["sections"].values():
            for actor, u in sec.items():
                yield jf.name, actor, u, tier_map.get(actor, {})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls")
    ap.add_argument("--md")
    args = ap.parse_args()
    anchors = {k: v for k, v in json.loads(ANCHORS.read_text(encoding="utf-8")).items()
               if isinstance(v, dict)}
    tier_map = tier_chain.load_derived_map(LEDGER)
    anchor_tiers = {}
    for cls, a in anchors.items():
        if not isinstance(a, dict):
            continue
        if a.get("anchor_actor") and a["anchor_actor"] in tier_map:
            anchor_tiers[cls] = tier_map[a["anchor_actor"]].get("tier_multiplier", 1.0)
        else:
            anchor_tiers[cls] = fnum(a.get("tech_tier")) or 1.0

    per_class = {}
    for fname, actor, u, du in collect(tier_map):
        d = u.get("design") or {}
        cls = d.get("class_anchor")
        if not cls or (args.cls and cls != args.cls) or cls not in anchors:
            continue
        anchor = anchors[cls]; c0 = cost0_of(anchor)
        if not c0:
            continue
        inp = unit_inputs(u, du)
        if inp is None:
            continue
        pr = price_for(cls, anchor, inp, anchor_tiers.get(cls, 1.0))
        if pr is None:
            continue
        epic = bool(u.get("build_limit"))
        per_class.setdefault(cls, []).append((actor, pr, pr / c0, epic))

    out = ["# Baseband validator (BALANCE_PIPELINE §8.1)", "",
           f"band: floor {SOFT_FLOOR:.0%} - sweet {SWEET_LO:.0%}–{SWEET_HI:.0%} - ceil {CEIL:.0%}",
           ""]
    violations = 0
    for cls in sorted(per_class):
        rows = sorted(per_class[cls], key=lambda r: r[2])
        signed = anchors[cls].get("signed_off")
        n = len(rows)
        sweet = sum(1 for _, _, r, _ in rows if SWEET_LO <= r <= SWEET_HI)
        lo = [a for a, _, r, e in rows if r < SOFT_FLOOR and not e]
        hi = [a for a, _, r, e in rows if r > CEIL and not e]
        violations += len(lo) + len(hi)
        out.append(f"## `{cls}` — {n} members - sweet-spot {sweet}/{n} ({sweet/n:.0%}) "
                   f"- signed_off={signed}")
        if lo: out.append(f"  !! below {SOFT_FLOOR:.0%} floor (too weak/price): {', '.join(lo[:12])}")
        if hi: out.append(f"  !! above {CEIL:.0%} ceil (needs tech-tier gate): {', '.join(hi[:12])}")
        out.append("")

    text = "\n".join(out)
    if args.md:
        p = ROOT / args.md
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n", encoding="utf-8", newline="\n")
        print(f"report -> {args.md}")
    else:
        print(text)
    print(f"[{violations} band violations across {len(per_class)} classes]")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
