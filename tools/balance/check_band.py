#!/usr/bin/env python3
"""check_band.py — Balance-pipeline BASEBAND validator (BALANCE_PIPELINE §8.1).

For every ledger unit classified by its reviewed tag or template, compute its
class-formula price and the ratio price/cost0, then enforce the baseband law:

  * hard band     50%..350%  of the class baseline cost0  (maintainer 2026-09-08)
  * practical floor  ~75%   (formula breaks down below — units too weak/price)
  * sweet spot   100%..250%  (baseline..verifier) — target >=80% occupancy

Read-only. Emits a report and a nonzero exit if any member is below 75% or
above 350% (unless it is a BuildLimit:1 epic/hero, which is band-exempt).

Usage: python tools/balance/check_band.py [--class X] [--md docs/audit/latest/band.md]
"""
from __future__ import annotations
import argparse, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import formula  # noqa: E402
import tier_chain  # noqa: E402
import class_membership  # noqa: E402
import cargo_pricing  # noqa: E402
import fit_class
from fit_class import eligible_virtual_member
from firepower import armament_firepower, priced_by_default

LEDGER = ROOT / "docs/balance"
ANCHORS = LEDGER / "class_anchors.json"

FLOOR, SOFT_FLOOR, SWEET_LO, SWEET_HI, CEIL = 0.50, 0.75, 1.00, 2.50, 3.50


def fnum(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def fitting_unit(u):
    """Adapt the legacy nested input shape to the canonical fitting reader."""
    arms = []
    for arm in u.get('armaments', []):
        st = arm.get("stats", arm)  # tolerate both nesting styles
        normalized = {**st, **arm}
        reload = st.get('reload_delay')
        normalized['reloaddelay'] = (reload.get('v') if isinstance(reload, dict)
                                      else st.get('reloaddelay') or reload)
        normalized['damage_warheads'] = st.get('damage_warheads', arm.get('damage_warheads', []))
        normalized['range'] = st.get('range')
        burst = st.get('burst')
        normalized['burst'] = burst.get('v') if isinstance(burst, dict) else burst
        normalized['burstdelays'] = st.get('burstdelays', st.get('burst_delays'))
        normalized.pop('stats', None)
        arms.append(normalized)
    return {**u, 'armaments': arms}


def unit_inputs(u, du=None):
    """Use the fitting pipeline's selected domain and charge-cycle handling."""
    return fit_class.unit_inputs(fitting_unit(u), du)[0]


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


def band_exempt(unit):
    """Only the documented BuildLimit: 1 epic/hero exemption."""
    value = unit.get("build_limit")
    if isinstance(value, dict):
        value = value.get("v")
    return fnum(value) == 1


def armament_scope_details(unit, rules):
    """Keep inactive-variant limitations separate from the raw-DPS input domain."""
    import effective_damage
    unit = fitting_unit(unit)
    selected = {id(a) for a in fit_class.pricing_armaments(unit)}
    rows = []
    for arm in unit.get('armaments', []):
        st = arm.get('stats', arm)
        name = arm.get('weapon') or st.get('weapon')
        weapon = rules.resolve_weapon(name) if name else None
        damage = formula.spread_damage_sum(st.get('damage_warheads', arm.get('damage_warheads', [])))
        reload = st.get('reload_delay')
        reload = fnum(reload.get('v') if isinstance(reload, dict) else st.get('reloaddelay') or reload)
        eligible = priced_by_default(arm)
        rows.append({'slot': arm.get('slot'), 'weapon': name, 'requires': arm.get('requires'),
                     'baseline_eligible': eligible,
                     'domain_selected': id(arm) in selected,
                     'contributes_to_raw_armament_term': bool(id(arm) in selected and damage and reload),
                     'authored_range': formula.wdist_value(arm.get('range'), 0.0),
                     'raw_main_damage': damage,
                     'source_limitations': effective_damage.model_limitations(weapon)
                     if weapon is not None else ['unresolved_weapon']})
    return rows


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
    ap.add_argument("--faction", action="append", default=[],
                    help="exact ledger name without .json; repeat to combine factions")
    ap.add_argument("--actor-prefix", action="append", default=[],
                    help="actor-name prefix, including actors stored in shared ledgers; repeat to combine")
    ap.add_argument("--md")
    ap.add_argument('--json', type=pathlib.Path, help='structured diagnostic with active/inactive armament scope')
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
    cargo_pending = []
    cargo_checked = []
    cargo_rules = None
    details, scopes = [], {}
    if args.json:
        sys.path.insert(0, str(ROOT / 'tools/audit'))
        from miniyaml import Ruleset
        cargo_rules = Ruleset(ROOT)
    for fname, actor, u, du in collect(tier_map):
        if args.faction and pathlib.Path(fname).stem not in args.faction:
            continue
        if args.actor_prefix and not actor.startswith(tuple(args.actor_prefix)):
            continue
        if not eligible_virtual_member(u):
            continue
        if args.json:
            scopes[actor] = armament_scope_details(u, cargo_rules)
        cargo = u.get("cargo_capacity")
        capacity = fnum(cargo.get("v") if isinstance(cargo, dict) else cargo)
        # §8.4b: cargo vehicles/aircraft use a named full passenger load, not
        # the combat class formula. A missing load valuation is unresolved,
        # never an exemption that turns an incomplete run green.
        if capacity and capacity > 0 and (u.get("speed") or u.get("speed_air")):
            if cargo_rules is None:
                sys.path.insert(0, str(ROOT / 'tools/audit'))
                from miniyaml import Ruleset
                cargo_rules = Ruleset(ROOT)
            if actor not in cargo_rules.actors:
                cargo_pending.append(actor)
                continue
            load = cargo_pricing.authored_load(cargo_rules, actor)
            if load['issues']:
                cargo_pending.append(actor + ' (' + '; '.join(load['issues']) + ')')
            else:
                cost = u.get('cost')
                current = fnum(cost.get('v') if isinstance(cost, dict) else cost)
                cargo_checked.append((actor, current, load['passenger_sum'], load['combat_stat_budget']))
            continue
        d = u.get("design") or {}
        cls, _reason = class_membership.classify(d)
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
        epic = band_exempt(u)
        per_class.setdefault(cls, []).append((actor, pr, pr / c0, epic))
        if args.json:
            active = [r for r in scopes[actor] if r['contributes_to_raw_armament_term']]
            inactive = [r for r in scopes[actor] if not r['baseline_eligible']]
            details.append({'actor': actor, 'class': cls, 'source_ledger': fname,
                'class_source': _reason, 'subtype': d.get('subtype'),
                'modeled_price': pr, 'class_cost0': c0, 'ratio': pr / c0,
                'actual_cost': (u.get('cost') or {}).get('v'),
                'signed_off': bool(anchor.get('signed_off')), 'band_exempt': epic,
                'flagged': not epic and (pr / c0 < SOFT_FLOOR or pr / c0 > CEIL),
                'inputs': dict(zip(('hp','speed','range','raw_dps','special','unit_class','tier'), inp)),
                'comparison_domain': 'ground' if any(not fit_class.is_anti_air_armament(a)
                    for a in fit_class.pricing_armaments(fitting_unit(u))) else 'air',
                'active_source_limitations': sorted({v for r in active for v in r['source_limitations']}),
                'inactive_variant_limitations': sorted({v for r in inactive for v in r['source_limitations']})})

    out = ["# Baseband validator (BALANCE_PIPELINE §8.1)", "",
           f"band: floor {SOFT_FLOOR:.0%} - sweet {SWEET_LO:.0%}–{SWEET_HI:.0%} - ceil {CEIL:.0%}",
           ""]
    if cargo_pending:
        out.append(f"Unresolved cargo passenger-sum checks ({len(cargo_pending)}): "
                   + ", ".join(sorted(cargo_pending)))
        out.append("These carriers need named full-load valuations; combat class prices are not used for them.\n")
    if not per_class and not cargo_checked:
        out.append("No applicable priced class members were evaluated; this is not a passing band check.")
    cargo_violations = sum(current != wanted for _, current, wanted, _ in cargo_checked)
    if cargo_checked:
        out.extend(['## Authored mixed cargo loads', '',
                    'Static passenger-sum check; tier suitability and runtime loading remain separate.', '',
                    '| Actor | Current cost | Passenger sum | Combat stat budget (K 1.25) |',
                    '|---|---:|---:|---:|'])
        out.extend(f'| {actor} | {current} | {wanted} | {budget} |'
                   for actor, current, wanted, budget in cargo_checked)
        out.append(f'\n{cargo_violations} cargo price mismatches; no price writeback.\n')
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
    if args.json:
        path = ROOT / args.json
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            'scope': 'Current raw main-channel class-band diagnostic, not gameplay certification or price writeback.',
            'notes': ['Ratio is model price / class C0, not model price / the actor current cost.',
                      'Inactive upgrade limitations do not explain a baseline ratio.',
                      'Input domain matches fitting: ground when present, otherwise air. Complementary ground/AA slots are never summed together.',
                      'AA-primary calibration for a dual-role unit requires reviewing its air domain separately.',
                      'The raw proxy excludes percentage/armor/splash/state terms even where other helpers model them.',
                      'Empty source-limit lists are not proof that all combat effects are represented.'],
            'summary': {'evaluated': len(details), 'classes': len(per_class), 'band_flags': violations,
                        'cargo_price_mismatches': cargo_violations, 'unresolved_cargo': len(cargo_pending)},
            'rows': sorted(details, key=lambda r: r['ratio']), 'armament_scopes': scopes,
            'cargo_checked': cargo_checked, 'cargo_pending': cargo_pending}, indent=2)+'\n', encoding='utf-8')
    return 1 if violations or cargo_pending or cargo_violations else (0 if per_class or cargo_checked else 2)


if __name__ == "__main__":
    sys.exit(main())
