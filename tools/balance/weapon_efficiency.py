#!/usr/bin/env python3
"""weapon_efficiency.py — the K coefficient, and the family comparison table.

K is the whole pricing model in one dimensionless number:

    effective_dps = Damage_total x (burst / eff_reload) x FirepowerMultiplier x K

    K = SUM over warheads   share_w x versus_w x ( reliability_w + secondary_w )

      share_w      the application's reference-HP equivalent as a fixed fraction
                   of total flat damage (flat, chip, folded %, or standalone %)
      versus_w     Versus averaged over armors, weighted by how common each armor
                   actually is (target_model.armor_weights)
      reliability  P-weighted falloff at the impact point, over the ENGINE's scatter
      secondary_w  expected extra bodies caught = density x min(footprint, blob) - own cell

**The scalable part of K does not depend on the Damage magnitude.** It includes flat
damage, shield chips, and each folded ``PercentageScale`` hit that the current runtime
actually invokes, because all three fall to zero with the main Damage. A standalone
percentage warhead does not, so the honest model is AFFINE rather than a single
multiplier (E4, corrected 2026-08-25):

    effective_per_shot = Damage_total x K_flat_context
                         + pct_absolute_context
                         + folded_rounding_context

    Damage_required = (target_per_shot - pct_absolute_context) / K_flat_context
    Damage_yaml     = formula.snap_damage_step(Damage_required)   # the 100 grid

⚠ **`k` / `k_context` are the contaminated measurement forms**: ``k_flat`` plus a
standalone absolute contribution and the folded hit's current runtime residual,
both divided by the modeled Damage. They reproduce current output but are not shape
coefficients and must never be inverted. Invert through ``k_flat_context`` and
``pct_absolute_context``, snap the result to the Damage grid, then recompute runtime
rounding/wrap behavior for that snapped value. Overflowing folded products are explicitly
provisional because their residual is non-linear rather than a tiny quantisation step.

**Only ``pct_absolute_context`` is a DPS floor.** It contains standalone
``AreaDamagePercentage`` / ``HealthPercentageDamage`` warheads. Folded percentage damage
is never put there: it derives from the main Damage and reaches zero with it. A target below
the standalone floor is unreachable and must be reported, not rounded to a positive Damage.

That is the answer to "how does 2351.85 get into the yaml": it does not. The
designer sets geometry for FEEL, K measures it, and the pipeline solves for Damage.

Usage:
  python tools/balance/weapon_efficiency.py --families      # the family table
  python tools/balance/weapon_efficiency.py NAME [NAME...]  # concrete weapons
"""

from __future__ import annotations

import functools
import math
import pathlib
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
sys.path.insert(0, str(ROOT / "tools/balance"))
from miniyaml import Ruleset  # noqa: E402
import effective_damage as ed  # noqa: E402
import percentage_damage as pd  # noqa: E402
import target_model as tm  # noqa: E402

# The families the maintainer asked to compare, all at the Heavy level.
FAMILIES = ["CannonHE", "CannonAP", "MissileAP", "MissileHE", "Railgun", "Tesla",
            "Laser", "Prism", "Magic", "Sonic", "Flame", "Chemical", "Demolition",
            "Concussion", "Bullet", "Flak", "Plasma", "Thermobaric", "Quantum", "Storm"]

CHIP_SUFFIX = "_ExtraDamage"


def versus_of(node) -> dict[str, float]:
    """Compatibility wrapper for the project's canonical Versus reader.

    Registered audits and hook guidance import this public helper.  Keep the
    stable API here while the implementation lives beside the percentage
    damage readers in ``percentage_damage``.
    """
    return pd.versus_table(node)


def direct_actor_impact(resolved) -> bool:
    """Compatibility wrapper for the shared projectile runtime classifier."""
    return ed.direct_actor_impact(resolved)

# ---------------------------------------------------------------------------
# W5 CONTEXT FACTORS — what K alone cannot see.
#
# Each is a SEPARATE named factor, never one blended fudge: a price that moved
# has to be explainable by pointing at the factor that moved it.
#
# Three of them (targets / range / deadzone) are INDEPENDENT OF DAMAGE, so they
# fold into `k_flat_context` and the pricing inversion stays closed-form:
#     Damage_required = (target_per_shot - pct_absolute_context) / k_flat_context
# `overkill` is NOT: it compares per-shot damage against target HP, so it moves
# when Damage moves. Folding it into K would turn the closed-form inversion into
# a fixed-point iteration, so it is reported ALONGSIDE K, never inside it.
#
# Standalone percentage warheads are additive and therefore stay on the other side of
# the inversion. Folded PercentageScale damage is proportional and belongs in k_flat.
# ---------------------------------------------------------------------------

# A weapon that cannot hit air still fights 90% of the game. The floor stops a
# specialist being priced into irrelevance: AA units are separately class-anchored,
# so a raw share (Air-only = 0.10) would penalise them twice. Raise the floor for a
# more forgiving model, lower it to punish narrow weapons harder.
TARGETS_FLOOR = 0.5

# Outranging is worth more than DPS, but not without limit — a siege weapon already
# pays for its range in cost and mobility. Bounded so one long-range outlier cannot
# dominate the price. NOTE: at weight 0.25 the LOW bound is the asymptote (a range of
# 0 gives 1-0.25 = 0.75), so only the high bound actually clamps today; raising the
# weight past 0.25 makes the low one bite too.
RANGE_WEIGHT = 0.25
RANGE_BOUNDS = (0.75, 1.50)

# A MinRange dead zone costs the ANNULUS you cannot cover, which goes as the square
# of the radius ratio — a MinRange of half the range loses a quarter of the circle.
DEADZONE_WEIGHT = 1.0

_INJECTED = None


def use_ruleset(rs) -> None:
    """Reuse a caller's Ruleset for the weapon-side census (see target_model)."""
    global _INJECTED
    _INJECTED = rs
    median_weapon_range.cache_clear()


@functools.lru_cache(maxsize=1)
def median_weapon_range() -> float:
    """Median `Range` over every live weapon — the yardstick for range advantage.

    Measured, not assumed, so it self-updates as the roster grows (the same rule
    target_model follows). Weapons without a Range are skipped rather than counted
    as zero, which would drag the median down.
    """
    rs = _INJECTED if _INJECTED is not None else Ruleset(ROOT)
    ranges = []
    for name in rs.weapons:
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        raw = resolved.get("Range")
        if raw:
            value = ed.parse_wdist(raw)
            if value > 0:
                ranges.append(value)
    return statistics.median(ranges) if ranges else 6000.0


def targets_factor(resolved) -> float:
    """How much of the game this weapon can legally shoot at.

    `ValidTargets` maps onto the engagement weights: `Ground` (with `Water`/`Ship`)
    covers infantry + vehicles + buildings, `Air` covers aircraft. A ground-only
    weapon reaches 90% of the engagement mass, an AA-only weapon 10%.
    """
    raw = resolved.get("ValidTargets")
    if not raw:
        return 1.0                      # engine default = everything
    tokens = {t.strip().lower() for t in str(raw).split(",") if t.strip()}
    ground = bool(tokens & {"ground", "water", "ship", "trees", "wall"})
    air = "air" in tokens
    if not ground and not air:
        return 1.0                      # exotic set (Shielded, ...) — do not guess
    share = 0.0
    if ground:
        share += tm.ENGAGEMENT["INF"] + tm.ENGAGEMENT["VEH"] + tm.ENGAGEMENT["BLD"]
    if air:
        share += tm.ENGAGEMENT["AIR"]
    return TARGETS_FLOOR + (1.0 - TARGETS_FLOOR) * share


def range_factor(resolved, median: float | None = None) -> float:
    """Bounded reward for outranging the median weapon."""
    raw = resolved.get("Range")
    if not raw:
        return 1.0
    rng = ed.parse_wdist(raw)
    median = median or median_weapon_range()
    if rng <= 0 or median <= 0:
        return 1.0
    lo, hi = RANGE_BOUNDS
    return min(max(1.0 + RANGE_WEIGHT * (rng / median - 1.0), lo), hi)


def deadzone_factor(resolved) -> float:
    """Cost of a `MinRange` hole: the fraction of the engagement disc lost."""
    raw_min, raw_max = resolved.get("MinRange"), resolved.get("Range")
    if not raw_min or not raw_max:
        return 1.0
    lo, hi = ed.parse_wdist(raw_min), ed.parse_wdist(raw_max)
    if lo <= 0 or hi <= 0 or lo >= hi:
        return 1.0
    return 1.0 - DEADZONE_WEIGHT * (lo / hi) ** 2


def overkill_factor(per_shot: float, target_hp: float | None = None) -> float:
    """Fraction of dealt damage that is NOT wasted on an already-dead target.

    A shot only overkills on the LAST hit, so the waste is the remainder of the
    final shot: `ceil(HP/dmg)` shots deal `ceil(HP/dmg)*dmg` to remove `HP`.
    A 200k burst on a 50k target keeps 25%; anything that needs several shots
    tends to ~1.0.

    DAMAGE-DEPENDENT — reported next to K, never folded into it.
    """
    target_hp = target_hp or tm.reference_hp()
    if per_shot <= 0 or target_hp <= 0:
        return 1.0
    shots = math.ceil(target_hp / per_shot)
    return target_hp / (shots * per_shot)


def area_geometry_terms(node, fo, radii, density: float, sigma: float,
                        radius_scale: int = 100):
    """Tick-weighted runtime geometry for AreaDamage and its percentage subclass."""
    rel_total = secondary_total = footprint_total = 0.0
    for weight, reliability, footprint in ed.area_geometry_samples(
            node, fo, radii, sigma, radius_scale):
        rel_total += weight * reliability
        secondary_total += weight * tm.footprint_targets(footprint, density)
        footprint_total += weight * footprint
    return rel_total, secondary_total, footprint_total


def warhead_terms(node, wtype: str, sigma: float, is_direct_actor: bool = False):
    """(versus_factor, reliability, secondary, footprint) for one warhead node."""
    vs = pd.versus_table(node)
    versus = tm.weighted_versus(vs)
    density = tm.effective_density(vs)
    fo = radii = None
    live = True
    if wtype in {"AreaDamage", "SpreadDamage"}:
        fo, radii, live = ed.falloff_and_radii(node)
        if wtype == "AreaDamage":
            ed.area_tick_modifiers(node)
    if is_direct_actor:
        reliability = ed.reliability(
            [100, 0], [0, ed.POINT_TARGET_RADIUS], sigma)
        return versus, reliability, 0.0, 0.0
    if wtype == "TargetDamage":
        radius, live = ed.target_damage_radius(node)
    if not live:
        return versus, 0.0, 0.0, 0.0
    if wtype == "TargetDamage":
        footprint = ed.uniform_footprint_cells2(radius)
        rel = ed.uniform_reliability(radius, sigma)
        return versus, rel, tm.footprint_targets(footprint, density), footprint
    if wtype == "AreaDamage":
        rel, secondary, footprint = area_geometry_terms(
            node, fo, radii, density, sigma)
        return versus, rel, secondary, footprint
    footprint = ed.footprint_cells2(fo, radii)
    rel = ed.reliability(fo, radii, sigma)
    return versus, rel, tm.footprint_targets(footprint, density), footprint


def percentage_terms(app: dict, sigma: float, is_direct_actor: bool = False):
    """Weighted armor/reliability/area terms for one percentage application."""
    node = app["node"]
    if node.value == "AreaDamagePercentage" or app["kind"] == pd.PCT_FOLDED:
        fo, radii, live = ed.falloff_and_radii(node)
        ed.area_tick_modifiers(node)
    else:
        fo = radii = None
        live = True
    if is_direct_actor:
        reliability = ed.reliability(
            [100, 0], [0, ed.POINT_TARGET_RADIUS], sigma)
        return tm.weighted_versus(app["versus"]), reliability, 0.0, 0.0
    if node.value == "HealthPercentageDamage":
        # This inherits TargetDamageWarhead. Spread 0 is one selected actor;
        # a positive Spread is a uniform catch radius on positional impacts.
        vs = app["versus"]
        versus = tm.weighted_versus(vs)
        density = tm.effective_density(vs)
        radius, live = ed.target_damage_radius(node)
        if live:
            footprint = ed.uniform_footprint_cells2(radius)
            reliability = ed.uniform_reliability(radius, sigma)
            return (versus, reliability,
                    tm.footprint_targets(footprint, density), footprint)
        # TargetDamageWarhead's positional path returns immediately at Spread 0.
        return versus, 0.0, 0.0, 0.0
    vs = app["versus"]
    versus = tm.weighted_versus(vs)
    density = tm.effective_density(vs)
    if not live:
        return versus, 0.0, 0.0, 0.0
    radius_scale = (app["percentage_spread"]
                    if app["kind"] == pd.PCT_FOLDED else 100)
    rel, secondary, footprint = area_geometry_terms(
        node, fo, radii, density, sigma, radius_scale)
    return versus, rel, secondary, footprint


def analyse(resolved, damage_total: float | None = None):
    """Full breakdown for one resolved weapon at a nominal total damage."""
    ed.validate_damage_warheads(resolved)
    whs = ed.flat_damage_warheads(resolved)
    ref_hp = tm.reference_hp()
    is_instant, sigma = ed.weapon_reliability_ctx(resolved)
    is_direct_actor = direct_actor_impact(resolved)
    applications = pd.percentage_applications(resolved, ref_hp)
    if not whs and not applications:
        return None
    impact_multiplier = ed.projectile_impact_multiplier(resolved)
    nominal_impacts = ed.projectile_nominal_impact_count(resolved)
    limitations = ed.model_limitations(resolved)
    parts = []
    flat_total = sum(base for _t, _w, base, _n in whs)
    # Shares need a non-zero normalizer, but that implementation detail must not
    # invent one point of flat Damage for a percentage-only weapon.  With no
    # caller-supplied nominal Damage, its ratio-form K is correctly undefined.
    share_total = flat_total or 1.0
    damage_total = flat_total if damage_total is None else damage_total
    for tag, wtype, base, node in whs:
        versus, rel, secondary, footprint = warhead_terms(
            node, wtype, sigma, is_direct_actor)
        parts.append({"tag": tag, "share": base / share_total, "versus": versus,
                      "rel": rel, "secondary": secondary, "footprint": footprint,
                      "rounding_share": 0.0,
                      "kind": "chip" if tag.endswith(CHIP_SUFFIX.lstrip("_")) or
                              CHIP_SUFFIX in f"_{tag}" else "flat"})

    for app in applications:
        versus, rel, secondary, footprint = percentage_terms(
            app, sigma, is_direct_actor)
        rounding_hp = app["rounding_hp"]
        if app["kind"] == pd.PCT_FOLDED and damage_total != flat_total:
            # The family table may ask for a nominal Damage different from the template's
            # placeholder. Recompute the engine's basis-point rounding at that magnitude.
            modeled_damage = int(round(app["damage"] * damage_total / share_total))
            continuous_units, runtime_units = pd.folded_units(modeled_damage, app["scale"])
            denominator = app["denominator"]
            continuous_hp = ref_hp * continuous_units / denominator
            runtime_hp = pd.runtime_percentage_hp(ref_hp, runtime_units, denominator)
            rounding_hp = runtime_hp - continuous_hp
        application_hp = (app["continuous_hp"] if app["kind"] == pd.PCT_FOLDED
                          else app["runtime_hp"])
        parts.append({"tag": app["tag"], "share": application_hp / share_total,
                      "versus": versus, "rel": rel, "secondary": secondary,
                      "footprint": footprint, "kind": app["kind"],
                      "rounding_share": rounding_hp / share_total})

    def contrib(p):
        return p["share"] * p["versus"] * (p["rel"] + p["secondary"])

    # ---- E4: the affine split (see the module docstring) ---------------------
    # Flat/chip/folded shares are scale-invariant. Only standalone percentage
    # applications are absolute. Folded runtime rounding/Int32 wrap is reported as
    # a separate current-shot residual so it cannot masquerade as a permanent floor.
    scalable = {"flat", "chip", pd.PCT_FOLDED}
    # A normal projectile invokes its warheads once. AreaBeam invokes all of
    # them repeatedly during one fire, so its internal impact cadence belongs
    # in per-shot output before the armament Burst/reload cadence is applied.
    k_flat = sum(contrib(p) for p in parts if p["kind"] in scalable) * impact_multiplier
    pct_absolute = sum(
        contrib(p) for p in parts if p["kind"] == pd.PCT_STANDALONE
    ) * share_total * impact_multiplier
    folded_rounding = sum(
        p["rounding_share"] * p["versus"] * (p["rel"] + p["secondary"])
        for p in parts if p["kind"] == pd.PCT_FOLDED
    ) * share_total * impact_multiplier
    k = (k_flat + (pct_absolute + folded_rounding) / damage_total
         if damage_total > 0 else None)

    # W5 context factors. The damage-independent three multiply into k_context, so
    # the pricing inversion stays closed-form; overkill is reported separately
    # because it moves with Damage (see the constants block).
    factors = {"targets": targets_factor(resolved),
               "range": range_factor(resolved),
               "deadzone": deadzone_factor(resolved)}
    ctx = factors["targets"] * factors["range"] * factors["deadzone"]
    k_context = k * ctx if k is not None else None
    effective_uncontextual = (
        damage_total * k_flat + pct_absolute + folded_rounding)
    effective = (
        damage_total * k_flat * ctx + pct_absolute * ctx + folded_rounding * ctx)
    overkill = overkill_factor(effective_uncontextual, ref_hp)

    return {"k": k, "k_context": k_context, "factors": factors,
            "k_flat": k_flat, "k_flat_context": k_flat * ctx,
            "pct_absolute": pct_absolute, "pct_absolute_context": pct_absolute * ctx,
            "folded_rounding": folded_rounding,
            "folded_rounding_context": folded_rounding * ctx,
            "flat_total": flat_total,
            "damage_total": damage_total,
            "overkill": overkill, "sigma": sigma, "instant": is_instant,
            "direct_actor": is_direct_actor,
            "projectile_impact_multiplier": impact_multiplier,
            "nominal_projectile_impacts": nominal_impacts,
            "model_limitations": limitations,
            "parts": parts, "effective": effective, "ref_hp": ref_hp}


def required_damage(target_per_shot: float, k_flat_context: float,
                    pct_absolute_context: float = 0.0) -> float | None:
    """Invert the AFFINE model: the flat `Damage` total that hits `target_per_shot`.

    Returns **None when the target is below the %-twin floor** — that is not an error to
    round away, it is the model reporting that no flat Damage can get there (the twin
    alone already exceeds the target, so the weapon needs a smaller twin or a different
    warhead). The old single-K inversion returned a confidently wrong positive number.
    """
    if k_flat_context <= 0:
        return None
    headroom = target_per_shot - pct_absolute_context
    return headroom / k_flat_context if headroom > 0 else None


def family_table(damage_total: float = 20000.0, level: str = "Heavy") -> str:
    rs = Ruleset(ROOT)
    rows = []
    for fam in FAMILIES:
        name = f"^Warhead_{fam}_{level}"
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        res = analyse(node, damage_total)
        if res is None:
            continue
        flat = [p for p in res["parts"] if p["kind"] == "flat"]
        chip = [p for p in res["parts"] if p["kind"] == "chip"]
        pct = [p for p in res["parts"] if p["kind"].startswith("pct_")]
        main = flat[0] if flat else None
        # Ranked on the CONTEXT-adjusted number — that is what the weapon is
        # actually worth; the bare K stays visible as its own column.
        rows.append((res["k_context"] * damage_total, fam, res, main, chip, pct))
    rows.sort(key=lambda r: (-r[0], r[1]))

    out = [f"| # | family (Heavy) | avgVersus | reliab | footprint cell² | secondary | "
           f"chip | %-twin | **K** | targets | range | deadzone | overkill | "
           f"**K ctx** | **effective @ {damage_total:,.0f}** |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, (eff, fam, res, main, chip, pct) in enumerate(rows, 1):
        f = res["factors"]
        out.append(
            f"| {i} | {fam} | {main['versus']:.2f} | {main['rel']:.2f} | "
            f"{main['footprint']:.2f} | {main['secondary']:.2f} | "
            f"{'yes' if chip else '—'} | {'yes' if pct else '—'} | "
            f"**{res['k']:.2f}** | {f['targets']:.2f} | {f['range']:.2f} | "
            f"{f['deadzone']:.2f} | {res['overkill']:.2f} | "
            f"**{res['k_context']:.2f}** | **{eff:,.0f}** |")
    return "\n".join(out)


def main() -> int:
    args = sys.argv[1:]
    if not args or "--families" in args:
        print(f"# Weapon efficiency K — all families at Heavy, 20 000 total damage\n")
        print(f"reference HP {tm.reference_hp():,} (design; roster measures "
              f"{tm.measured_reference_hp():,}) · blob {tm.A_BLOB} cell² · "
              f"own cell {tm.A_SELF} cell²\n")
        print(family_table())
        return 0
    rs = Ruleset(ROOT)
    for name in args:
        node = rs.resolve_weapon(name)
        if node is None:
            print(f"{name}: UNRESOLVED")
            continue
        res = analyse(node)
        if res is None:
            print(f"{name}: no damage warheads")
            continue
        k_text = f"{res['k']:.3f}" if res["k"] is not None else "undefined"
        print(f"\n## {name}   K = {k_text}   sigma = {res['sigma']:.0f}"
              f"{'  (instant)' if res['instant'] else ''}")
        print("| warhead | kind | share | avgVersus | reliab | footprint | secondary |")
        print("|---|---|---|---|---|---|---|")
        for p in res["parts"]:
            print(f"| {p['tag']} | {p['kind']} | {p['share']:.3f} | {p['versus']:.2f} | "
                  f"{p['rel']:.2f} | {p['footprint']:.2f} | {p['secondary']:.2f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
