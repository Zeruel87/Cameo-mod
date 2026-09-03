#!/usr/bin/env python3
"""effective_damage.py — READ-ONLY area-integrated damage metric per weapon.

Ranks weapons on ONE comparable axis so single-target energy warheads (laser /
tesla / railgun + their extra-damage chips) sit next to wide-spread AoE warheads
(HE / cannon / nuke). Integrates each flat-damage warhead over its spread+falloff
curve, weights it by single-target hit reliability (accuracy + travel), and sums
the main + every *_ExtraDamage chip.

FORMULA (locked with maintainer 2026-08-11):
  effective = SUM over(main + *_ExtraDamage)  base * ( reliability + SWARM_W * footprint_cells2 )
    footprint   = 2*pi * INT (F(r)/100) * r dr  / CELL^2                 (cell^2, damage-weighted area)
    reliability = average F over a scatter disc of radius sigma          (= center Falloff at sigma 0)
    sigma       = Inaccuracy + LEAD * TARGET_SPEED * Range / min(Speed, SPEED_CAP)
    area defaults: Spread 43; Falloff 100,37,14,5,0 (unless authored)
    true hitscans have no travel drift but keep authored scatter; tracked LaserZap
    and direct TargetActorCenter hits reset that scatter at impact.

Excludes the %-twin (AreaDamagePercentage / HealthPercentageDamage — a different
currency), the baked *FriendlyFire twins, EMP (AffectsIntegrity) and effects.

Writes/edits NOTHING. Usage:
  python tools/balance/effective_damage.py                 # full table, sorted desc
  python tools/balance/effective_damage.py --top 40        # only the top 40
  python tools/balance/effective_damage.py NAME [NAME...]   # just these weapons, verbose
"""
from __future__ import annotations
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
from cameo_model import Model  # noqa: E402
from formula import parse_bool, parse_int32, parse_wdist  # noqa: E402
import percentage_damage as pd  # noqa: E402

CELL = 1024.0
SWARM_W = 0.25          # anti-swarm area weight (you rarely hit a full blob)
LEAD = 0.20             # engine leads/tracks -> real miss is ~20% of raw displacement
TARGET_SPEED = 100      # typical dodging vehicle speed (WDist/tick)
SPEED_CAP = 10000       # ~10 cells/tick: at/above this a projectile is "basically instant"
DEFAULT_AREA_SPREAD = 43
DEFAULT_AREA_FALLOFF = (100, 37, 14, 5, 0)
# Synthetic radius used only to approximate a point target for TargetDamage and
# moving direct-Actor projectiles. Area warheads use their runtime Spread exactly,
# including authored values below 100.
POINT_TARGET_RADIUS = 100
BULLET_DEFAULT_SPEED = 17
# Instant projectiles have no travel drift, but the hitscan variants retain their
# authored scatter unless they use the direct-Actor center path. A projectile with
# no known scalar Speed is modeled without travel drift and explicitly marked
# provisional when its trajectory is known to need a richer model. Direct-Actor
# impacts bypass warhead falloff separately.
INSTANT_PROJECTILES = {"InstantHit", "LaserZap", "Railgun", "InstantHitLine", "InstantHitAS",
                       "SupportPowerInstantExplode", "InstantExplode",
                       "LightningZap", "RadBeam", "KKNDLaser", "LaserZapCA",
                       # Cameo hitscan tracer: damage lands on the firing tick, the streak is
                       # decoration. Named explicitly rather than relying on "has no Speed",
                       # because a weapon that inherits a SECOND projectile template can drag a
                       # foreign `Speed` in and would then be priced as a slow shell.
                       "InstantHitWithFakeBullets"}
INSTANT_SCATTER_PROJECTILES = {
    "InstantHit", "InstantHitWithFakeBullets", "Railgun",
    "InstantHitLine", "InstantHitAS",
}
TRACKED_ZAP_PROJECTILES = {"LaserZap", "LaserZapCA"}
UNMODELED_TRAJECTORY_PROJECTILES = {"GravityBomb", "NukeLaunch"}

# Moving projectile defaults supplied by C# when MiniYAML omits Speed. Only
# types whose scalar Speed/Inaccuracy map to this reliability approximation
# belong here; ballistic GravityBomb/NukeLaunch motion is flagged provisional.
MOVING_PROJECTILE_DEFAULT_SPEEDS = {
    "Bullet": BULLET_DEFAULT_SPEED,
    "ScaledBullet": BULLET_DEFAULT_SPEED,
    "Missile": 384,
    "AreaBeam": 128,
    "SpriteAthenaLaser": 90,
    "LinearPulse": 6 * 1024,
}
INACCURACY_PROJECTILES = (
    INSTANT_SCATTER_PROJECTILES | TRACKED_ZAP_PROJECTILES |
    {"Bullet", "ScaledBullet", "Missile", "AreaBeam", "LinearPulse"}
)

# Projectile implementations that pass Actor targets to Weapon.Impact. The
# DamageWarhead base then applies one direct hit and bypasses warhead
# Spread/Falloff/Ticks. This is narrower than INSTANT_PROJECTILES: several
# instant visuals still impact a position, while LinearPulse shape modes are
# moving projectiles that explicitly enumerate actors.
CENTER_TARGET_ACTOR_PROJECTILES = {"InstantHit", "InstantHitWithFakeBullets"}
LINE_WIDTH_ACTOR_PROJECTILES = {"SpriteRailgun", "SmokeParticleRailgun"}
LINEAR_PULSE_ACTOR_IMPACTS = {"rectangle", "cone", "trapezoid"}
AREA_BEAM_DEFAULT_DURATION = 10
AREA_BEAM_DEFAULT_DAMAGE_INTERVAL = 3
LASER_ZAP_DEFAULT_DURATION = 10
LASER_ZAP_DEFAULT_DAMAGE_DURATION = 1
LASER_ZAP_DEFAULT_DAMAGE_INTERVAL = 1
SPRITE_ATHENA_DEFAULT_EXPLOSION_INTERVAL = 3
SPRITE_ATHENA_DEFAULT_PIERCE_TICKS = 0
SPRITE_ATHENA_DEFAULT_STAY_TICKS = 8
LIGHTNING_ZAP_DEFAULT_DURATION = 3
LIGHTNING_ZAP_DEFAULT_DAMAGE_DURATION = 1


def _truthy(raw, field: str = "boolean") -> bool:
    return parse_bool(raw, field, False)


def direct_actor_impact(resolved) -> bool:
    """Whether the projectile invokes DamageWarhead's direct-Actor path.

    This describes the ordinary, unobstructed Actor-target path only. A
    TargetActorCenter hitscan falls back to a positional impact if its target
    becomes invalid, and a blockable hitscan impacts the blocker position.

    AreaBeam, line railguns, and shaped LinearPulse projectiles may invoke the
    direct hit for several actors; their projectile-level corridor/shape is a
    separate contribution from the warhead geometry classified here.
    """
    projectile = resolved.child("Projectile")
    projectile_type = projectile.value if projectile is not None else None
    if projectile_type == "AreaBeam":
        return True
    if projectile_type == "Railgun":
        return _truthy(
            resolved.get("Projectile", "DamageActorsInLine"),
            "Railgun.DamageActorsInLine")
    if projectile_type in LINE_WIDTH_ACTOR_PROJECTILES:
        raw_width = resolved.get("Projectile", "LineWidth")
        return bool(raw_width and parse_wdist(raw_width) > 0)
    if projectile_type == "LinearPulse":
        impact_type = str(
            resolved.get("Projectile", "ImpactType") or "StandardImpact").strip().lower()
        return impact_type in LINEAR_PULSE_ACTOR_IMPACTS
    return (projectile_type in CENTER_TARGET_ACTOR_PROJECTILES and _truthy(
        resolved.get("TargetActorCenter"), "Weapon.TargetActorCenter"))


def projectile_impact_multiplier(resolved) -> float:
    """Expected warhead applications made by one weapon fire.

    Most projectiles call ``Weapon.Impact`` once. ``AreaBeam`` calls it every
    ``DamageInterval`` ticks while a target remains inside the moving beam.
    For a stationary target exposed for the full uninterrupted beam, the
    phase-average count is ``Duration / DamageInterval``. The exact count is
    floor or ceil of that ratio when the fields are not evenly divisible; all
    live percentage-bearing AreaBeams divide exactly.

    Invalid non-positive cadence fields are rejected instead of silently
    publishing a made-up DPS for a projectile that would not have valid runtime
    cadence semantics.
    """
    projectile = resolved.child("Projectile")
    if projectile is not None and projectile.value == "SpriteAthenaLaser":
        # Positive cadence is distributed along a moving corridor, so it cannot
        # honestly multiply one target's K. A nominal count of zero is exact,
        # however: the projectile never invokes its warheads at all.
        nominal = projectile_nominal_impact_count(resolved)
        return 0.0 if nominal == 0 else 1.0
    if projectile is not None and projectile.value in TRACKED_ZAP_PROJECTILES:
        duration = parse_int32(
            resolved.get("Projectile", "Duration"),
            f"{projectile.value}.Duration", LASER_ZAP_DEFAULT_DURATION)
        damage_duration = parse_int32(
            resolved.get("Projectile", "DamageDuration"),
            f"{projectile.value}.DamageDuration", LASER_ZAP_DEFAULT_DAMAGE_DURATION)
        interval = parse_int32(
            resolved.get("Projectile", "DamageInterval"),
            f"{projectile.value}.DamageInterval", LASER_ZAP_DEFAULT_DAMAGE_INTERVAL)
        # A zap always executes its first Tick, even when Duration <= 0. A
        # positive interval impacts at ticks 0, interval, 2*interval...;
        # non-positive intervals reset ready and impact every active tick.
        active_ticks = max(min(damage_duration, max(duration, 1)), 0)
        if interval <= 0:
            return float(active_ticks)
        return float((active_ticks + interval - 1) // interval)
    if projectile is not None and projectile.value == "LightningZap":
        duration = parse_int32(
            resolved.get("Projectile", "Duration"), "LightningZap.Duration",
            LIGHTNING_ZAP_DEFAULT_DURATION)
        damage_duration = parse_int32(
            resolved.get("Projectile", "DamageDuration"),
            "LightningZap.DamageDuration", LIGHTNING_ZAP_DEFAULT_DAMAGE_DURATION)
        return float(max(min(damage_duration, duration), 0))
    if projectile is None or projectile.value != "AreaBeam":
        return 1.0

    duration = parse_int32(
        resolved.get("Projectile", "Duration"), "AreaBeam.Duration",
        AREA_BEAM_DEFAULT_DURATION)
    interval = parse_int32(
        resolved.get("Projectile", "DamageInterval"), "AreaBeam.DamageInterval",
        AREA_BEAM_DEFAULT_DAMAGE_INTERVAL)
    if duration <= 0 or interval <= 0:
        raise ValueError(
            f"AreaBeam cadence must be positive (Duration={duration}, "
            f"DamageInterval={interval})")
    return duration / interval


def projectile_nominal_impact_count(resolved) -> int | None:
    """Max-range total impacts for corridor projectiles not reducible to one-target K."""
    projectile = resolved.child("Projectile")
    if projectile is None or projectile.value != "SpriteAthenaLaser":
        return None
    range_raw = resolved.get("Range")
    weapon_range = parse_wdist(range_raw) if range_raw else 0
    speed_raw = resolved.get("Projectile", "Speed")
    speed = parse_wdist(speed_raw) if speed_raw else \
        MOVING_PROJECTILE_DEFAULT_SPEEDS["SpriteAthenaLaser"]
    interval_raw = resolved.get("Projectile", "ExplosionInterval")
    pierce_raw = resolved.get("Projectile", "PierceTicks")
    stay_raw = resolved.get("Projectile", "StayTicks")
    interval = max(parse_int32(
        interval_raw, "SpriteAthenaLaser.ExplosionInterval",
        SPRITE_ATHENA_DEFAULT_EXPLOSION_INTERVAL), 1)
    pierce = parse_int32(
        pierce_raw, "SpriteAthenaLaser.PierceTicks",
        SPRITE_ATHENA_DEFAULT_PIERCE_TICKS)
    stay = parse_int32(
        stay_raw, "SpriteAthenaLaser.StayTicks",
        SPRITE_ATHENA_DEFAULT_STAY_TICKS)
    flight = max(weapon_range // max(speed, 1), 1)
    # Tick() always runs once before checking LifeExpired, even if negative
    # authored stay/pierce values make maxticks less than zero.
    final_tick = max(flight + pierce + stay + 1, 1)
    return final_tick // interval


def model_limitations(resolved) -> list[str]:
    """Machine-readable gaps that make a derived weapon value provisional."""
    projectile = resolved.child("Projectile")
    projectile_type = projectile.value if projectile is not None else None
    limitations = []
    if projectile_type == "AreaBeam":
        # Cadence for one actor is modeled, but Width/line length and secondary
        # actors returned by FindActorsOnLine are not yet priced.
        limitations.append("unmodeled_projectile_geometry:AreaBeam")
    elif (projectile_type == "Railgun" and
          _truthy(resolved.get("Projectile", "DamageActorsInLine"),
                  "Railgun.DamageActorsInLine")):
        limitations.append("unmodeled_projectile_geometry:Railgun.line")
    elif projectile_type in LINE_WIDTH_ACTOR_PROJECTILES:
        raw_width = resolved.get("Projectile", "LineWidth")
        if raw_width and parse_wdist(raw_width) > 0:
            limitations.append(
                f"unmodeled_projectile_geometry:{projectile_type}.line")
    elif projectile_type == "LinearPulse":
        impact_type = str(
            resolved.get("Projectile", "ImpactType") or "StandardImpact").strip()
        if impact_type.lower() in LINEAR_PULSE_ACTOR_IMPACTS:
            # The direct warhead hit is modeled, but the projectile's corridor,
            # extra actor catches, and DamageFalloff modifiers are not yet.
            limitations.append(
                f"unmodeled_projectile_geometry:LinearPulse.{impact_type}")
    elif projectile_type == "SpriteAthenaLaser":
        limitations.extend([
            "unmodeled_projectile_cadence:SpriteAthenaLaser",
            "unmodeled_projectile_geometry:SpriteAthenaLaser",
        ])
    elif projectile_type in UNMODELED_TRAJECTORY_PROJECTILES:
        limitations.append(f"unmodeled_projectile_trajectory:{projectile_type}")
    if projectile_type == "Missile":
        raw_probability = resolved.get("Projectile", "LockOnProbability")
        probability = parse_int32(
            raw_probability, "Missile.LockOnProbability", 100)
        # Random.Next(100) returns 0..99 and the engine uses <=. Values 0..98
        # therefore produce a real mixture of tracked and untracked trajectories.
        if 0 <= probability < 99:
            limitations.append("unmodeled_projectile_lock_on:Missile")
    if projectile_type in TRACKED_ZAP_PROJECTILES:
        duration = parse_int32(
            resolved.get("Projectile", "Duration"),
            f"{projectile_type}.Duration", LASER_ZAP_DEFAULT_DURATION)
        damage_duration = parse_int32(
            resolved.get("Projectile", "DamageDuration"),
            f"{projectile_type}.DamageDuration", LASER_ZAP_DEFAULT_DAMAGE_DURATION)
        hit_anim = resolved.get("Projectile", "HitAnim")
        if (hit_anim is not None and str(hit_anim).strip() and
                damage_duration > max(duration, 1)):
            limitations.append(
                f"unmodeled_projectile_hitanim_lifetime:{projectile_type}")
    if projectile_type == "AreaBeam":
        multiplier = projectile_impact_multiplier(resolved)
        if not multiplier.is_integer():
            limitations.append("phase_averaged_projectile_cadence:AreaBeam")
    speed_raw = resolved.get("Projectile", "Speed")
    if projectile_type in {"Bullet", "ScaledBullet"} and speed_raw and "," in str(speed_raw):
        limitations.append(
            f"approximated_projectile_speed_distribution:{projectile_type}")
    return limitations


def parse_ints(s) -> list[int]:
    return [parse_int32(x.strip(), "integer list value")
            for x in str(s).split(",") if x.strip() != ""]


def csharp_div(numerator: int, denominator: int) -> int:
    """C# integer division: truncate toward zero, including signed values."""
    if denominator == 0:
        raise ZeroDivisionError("runtime geometry divides by a zero-width range step")
    sign = -1 if (numerator < 0) != (denominator < 0) else 1
    return sign * (abs(numerator) // abs(denominator))


def _field_present(node, key: str) -> bool:
    """Whether MiniYAML authored a field, preserving explicit blank arrays."""
    child = getattr(node, "child", None)
    if child is not None:
        return child(key) is not None
    return node.get(key) is not None


def falloff_and_radii(node, spread: int | None = None):
    """(falloff percents, radii in WDist). Warhead Range overrides Spread geometry.

    Mirrors AreaDamageWarhead/SpreadDamageWarhead EXACTLY, including the engine's
    single-Range footgun (verified 2026-08-11 against
    `OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs` and the upstream
    `SpreadDamageWarhead.cs`, which behave identically):

        if (Range != null) effectiveRange = Range;            // NO expansion
        else effectiveRange = [i * Spread for i in Falloff];

    and `GetDamageFalloff` walks `for (i = 1; i < effectiveRange.Length; i++)`,
    returning 0 when the loop never runs. So a `Range:` with a SINGLE value and a
    multi-step `Falloff` makes the warhead deal ZERO damage at every distance —
    the metric must score that as zero rather than inventing a per-step grid, or
    it silently over-values a broken weapon. `has_geometry` is False for that case
    so callers can report it.
    """
    falloff_present = _field_present(node, "Falloff")
    fo_raw = node.get("Falloff")
    fo = parse_ints(fo_raw) if falloff_present else list(DEFAULT_AREA_FALLOFF)
    if not fo:
        raise ValueError("area warhead Falloff cannot be empty")
    if spread is None:
        spread_raw = node.get("Spread")
        spread = (DEFAULT_AREA_SPREAD if spread_raw is None or
                  str(spread_raw).strip() == "" else parse_wdist(spread_raw))
    range_present = _field_present(node, "Range")
    rng = node.get("Range")
    if range_present:
        radii = [parse_wdist(x) for x in str(rng or "").split(",") if x.strip() != ""]
        if not radii:
            raise ValueError("area warhead Range cannot be empty")
        if len(radii) != 1 and len(radii) != len(fo):
            raise ValueError(
                "area warhead Range length must be one or equal Falloff length")
        if any(a > b for a, b in zip(radii, radii[1:])):
            raise ValueError("area warhead Range values must be nondecreasing")
    else:
        radii = [i * spread for i in range(len(fo))]
    # A single effective range or one Falloff entry loads successfully, but the
    # runtime loop never enters and therefore returns zero at every distance.
    return fo, radii, len(fo) >= 2 and len(radii) >= 2


def runtime_falloff(fo, radii, distance: float) -> int:
    """Area/SpreadDamage GetDamageFalloff, including inward extrapolation."""
    if len(fo) < 2 or len(radii) < 2:
        return 0
    distance = max(int(distance), 0)
    inner = int(radii[0])
    for i in range(1, len(radii)):
        outer = int(radii[i])
        if outer > distance:
            return int(fo[i - 1]) + csharp_div(
                (int(fo[i]) - int(fo[i - 1])) * (distance - inner),
                outer - inner)
        inner = outer
    return 0


def _falloff_line(fo, radii, distance: float) -> tuple[float, float]:
    """(intercept, slope) for the runtime segment selected at distance."""
    if len(fo) < 2 or len(radii) < 2:
        return 0.0, 0.0
    inner = float(radii[0])
    for i in range(1, len(radii)):
        outer = float(radii[i])
        if outer > distance:
            span = outer - inner
            if span == 0:
                raise ZeroDivisionError(
                    "runtime geometry divides by a zero-width range step")
            slope = (float(fo[i]) - float(fo[i - 1])) / span / 100.0
            intercept = float(fo[i - 1]) / 100.0 - slope * inner
            return intercept, slope
        inner = outer
    return 0.0, 0.0


def footprint_cells2(fo, radii, cutoff: int | None = None) -> float:
    """2*pi*INT F(r)rdr over runtime falloff, starting at impact distance zero."""
    if len(fo) < 2 or len(radii) < 2:
        return 0.0
    limit = int(radii[-1]) if cutoff is None else min(int(radii[-1]), int(cutoff))
    if limit <= 0:
        return 0.0
    boundaries = sorted({0.0, float(limit), *(
        float(r) for r in radii[1:] if 0 < r < limit)})
    total = 0.0
    for a, b in zip(boundaries, boundaries[1:]):
        if b <= a:
            continue
        intercept, slope = _falloff_line(fo, radii, (a + b) / 2.0)
        total += (intercept * (b * b - a * a) / 2.0 +
                  slope * (b ** 3 - a ** 3) / 3.0)
    return (2 * math.pi * total) / (CELL * CELL)


def target_damage_radius(node) -> tuple[int, bool]:
    """Uniform positional catch radius for TargetDamage and its subclasses.

    Their runtime default Spread is zero, which means positional impacts return
    without damaging anything. Positive Spread applies full damage uniformly to
    actors caught within the radius; it does not use area-warhead Falloff.
    """
    spread_raw = node.get("Spread")
    spread = 0 if spread_raw is None or str(spread_raw).strip() == "" \
        else parse_wdist(spread_raw)
    return spread, spread > 0


def uniform_footprint_cells2(radius: int) -> float:
    return math.pi * max(radius, 0) ** 2 / (CELL * CELL)


def area_tick_modifiers(node) -> list[int]:
    """AreaDamage's validated C# per-tick modifiers."""
    raw_ticks = node.get("Ticks")
    ticks = parse_int32(raw_ticks, "AreaDamage.Ticks", 1)
    weights_present = _field_present(node, "TickDamage")
    weights = parse_ints(node.get("TickDamage") or "") if weights_present else None
    if weights is not None and len(weights) != ticks:
        raise ValueError("TickDamage length must equal Ticks")
    if ticks <= 0:
        return []
    if weights is not None and sum(weights) > 0:
        total = sum(weights)
        return [csharp_div(100 * weight, total) for weight in weights]
    return [csharp_div(100, ticks)] * ticks


def validate_damage_warheads(resolved) -> None:
    """Mirror ruleset-time area geometry validation for every resolved node."""
    for node in resolved.children:
        if not node.key.startswith("Warhead"):
            continue
        if node.value not in {"SpreadDamage", "AreaDamage", "AreaDamagePercentage"}:
            continue
        falloff_and_radii(node)
        if node.value in {"AreaDamage", "AreaDamagePercentage"}:
            area_tick_modifiers(node)


def area_geometry_samples(node, fo, radii, sigma: float,
                          radius_scale: int = 100):
    """(weight, reliability, footprint) for every runtime AreaDamage tick."""
    modifiers = area_tick_modifiers(node)
    ticks = len(modifiers)
    if ticks == 0:
        return []
    final_outer = int(radii[-1])
    max_radius = parse_wdist(node.get("MaxRadius") or 0)
    min_radius = parse_wdist(node.get("MinRadius") or 0)
    samples = []
    for tick, modifier in enumerate(modifiers):
        outer = final_outer
        if max_radius > 0 and ticks > 1:
            outer = min_radius + csharp_div(
                (max_radius - min_radius) * (tick + 1), ticks)
        scaled_outer = csharp_div(outer * int(radius_scale), 100)
        cutoff = min(outer, scaled_outer)
        samples.append((
            modifier / 100.0,
            reliability(fo, radii, sigma, cutoff=cutoff),
            footprint_cells2(fo, radii, cutoff=cutoff),
        ))
    return samples


def scatter_pdf(t: float) -> float:
    """Radial density of the ENGINE's scatter at radius t*sigma, t in [0, sqrt(2)].

    The engine does NOT scatter uniformly over a disc. `Bullet.cs`:

        target += WVec.FromPDF(world.SharedRandom, 2) * maxInaccuracyOffset / 1024

    and `WVec.FromPDF(r, 2)` draws EACH AXIS as `WDist.FromPDF(r, 2)` = the sum of
    two uniforms = a TRIANGULAR density on [-sigma, sigma]. So hits cluster near
    the aim point: mean radius 0.52*sigma (Monte-Carlo, 200k samples) versus
    0.67*sigma for a uniform disc, and P(r < sigma/4) is 15.7% versus 6.2%.

    Modelling it as a uniform disc therefore throws ~28% of the hits too far out
    and systematically UNDER-values inaccurate/slow weapons. This returns the
    radial density of |(X, Y)| with X, Y iid triangular, evaluated numerically
    once and cached, so `reliability` integrates against the real distribution.
    """
    return _RADIAL_PDF(t)


def _build_radial_pdf(bins: int = 256, samples: int = 400_000):
    """Monte-Carlo the radial density of the engine's 2-axis triangular scatter."""
    import random
    rng = random.Random(20260811)             # fixed seed: the table must be reproducible
    hi = math.sqrt(2.0)
    hist = [0.0] * bins
    for _ in range(samples):
        x = (rng.uniform(-1, 1) + rng.uniform(-1, 1)) / 2
        y = (rng.uniform(-1, 1) + rng.uniform(-1, 1)) / 2
        b = int(math.hypot(x, y) / hi * bins)
        if b < bins:
            hist[b] += 1.0
    total = sum(hist)
    width = hi / bins
    dens = [h / total / width for h in hist]  # normalised so INT dens dt = 1

    def pdf(t: float) -> float:
        if t < 0 or t >= hi:
            return 0.0
        return dens[int(t / hi * bins)]
    return pdf


_RADIAL_PDF = _build_radial_pdf()


def reliability(fo, radii, sigma, cutoff: int | None = None) -> float:
    """Expected falloff at the impact point, over the engine's scatter (POINT target).

    E[F(R)] where R is the miss distance. A perfect center impact evaluates the
    same runtime curve at distance zero, including nonzero-first-Range inward
    extrapolation. ``cutoff`` models an AreaDamage tick/folded radius gate.
    """
    if sigma <= 0:
        if cutoff is not None and cutoff < 0:
            return 0.0
        return runtime_falloff(fo, radii, 0) / 100.0
    n = 400
    hi = math.sqrt(2.0)
    acc = weight = 0.0
    step = hi / n
    for i in range(n):
        t = (i + 0.5) * step
        w = scatter_pdf(t) * step
        distance = t * sigma
        if cutoff is None or distance <= cutoff:
            acc += runtime_falloff(fo, radii, distance) / 100.0 * w
        weight += w
    return acc / weight if weight else 1.0


def uniform_reliability(radius: int, sigma: float) -> float:
    """Probability a point impact lands inside TargetDamage's closed disc."""
    if radius <= 0:
        return 0.0
    if sigma <= 0:
        return 1.0
    n = 400
    hi = math.sqrt(2.0)
    step = hi / n
    caught = weight = 0.0
    for i in range(n):
        t = (i + 0.5) * step
        w = scatter_pdf(t) * step
        if t * sigma <= radius:
            caught += w
        weight += w
    return caught / weight if weight else 0.0


def damage_value(raw):
    """A warhead's `Damage` as an int, or None when the field is not numeric.

    Non-numeric means an unresolved placeholder (an inherited value the resolver
    could not fold), which this metric skips. Returning None keeps the reason
    explicit instead of swallowing the parse error at the call site — see
    `audit_error_handling.py` E2.
    """
    try:
        return parse_int32(raw, "Damage")
    except ValueError:
        # FieldLoader rejects numeric-but-non-Int32 values. Preserve the old
        # explicit skip only for unresolved symbolic placeholders.
        try:
            float(str(raw).strip())
        except (TypeError, ValueError):
            return None
        raise


def number(raw):
    """`raw` as a float, or None when it is not numeric.

    Same contract as `damage_value` for fields that must keep their fractional part
    (Versus percentages, %-of-HP damage): the caller decides what a missing value
    means instead of a handler quietly swallowing it — `audit_error_handling.py` E2.
    """
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return None


def flat_damage_warheads(resolved):
    """Main + extra-damage flat warheads (exclude %-twin, FriendlyFire, EMP, effects)."""
    out = []
    for c in resolved.children:
        if not c.key.startswith("Warhead@"):
            continue
        tag = c.key.split("@", 1)[1]
        if "FriendlyFire" in tag:
            continue
        if c.value not in ("AreaDamage", "SpreadDamage", "TargetDamage"):
            continue
        base = damage_value(c.get("Damage"))
        if base is None or base <= 0:
            continue
        out.append((tag, c.value, base, c))
    return out


def weapon_reliability_ctx(resolved):
    """(zero travel drift, sigma), with runtime projectile defaults and scatter."""
    proj = resolved.child("Projectile")
    ptype = proj.value if proj is not None else None
    rng = resolved.get("Range")
    rng = parse_wdist(rng) if rng else 0
    if ptype in UNMODELED_TRAJECTORY_PROJECTILES:
        # These classes do not declare scalar Speed/Inaccuracy fields. Foreign
        # keys surviving MiniYAML inheritance are ignored by their C# Info type,
        # so they must not invent scatter or travel drift here either.
        return False, 0.0
    speed_raw = resolved.get("Projectile", "Speed")
    inacc_raw = (resolved.get("Projectile", "Inaccuracy")
                  if ptype in INACCURACY_PROJECTILES else None)

    def inaccuracy_at_range(base: float) -> float:
        kind = str(
            resolved.get("Projectile", "InaccuracyType") or "Maximum").strip().lower()
        if kind == "percellincrement":
            return csharp_div(int(base) * rng, 1024)
        return base  # Maximum and Absolute both equal base at nominal max range.

    inacc = parse_wdist(inacc_raw) if inacc_raw else 0
    if ptype in INSTANT_PROJECTILES:
        if ptype in CENTER_TARGET_ACTOR_PROJECTILES and direct_actor_impact(resolved):
            inacc = 0
        elif ptype in TRACKED_ZAP_PROJECTILES:
            raw_track = resolved.get("Projectile", "TrackTarget")
            track_target = parse_bool(raw_track, f"{ptype}.TrackTarget", True)
            if track_target:
                inacc = 0
        elif ptype not in INSTANT_SCATTER_PROJECTILES:
            inacc = 0
        return True, float(inaccuracy_at_range(inacc))

    if ptype == "AreaBeam":
        raw_track = resolved.get("Projectile", "TrackTarget")
        if parse_bool(raw_track, "AreaBeam.TrackTarget", False):
            # Tick() refreshes the beam line from the guided target before
            # FindActorsOnLine. The selected actor then receives a direct warhead
            # impact, so initial scatter and travel drift do not reduce its hit.
            return False, 0.0

    if ptype == "Missile":
        raw_probability = resolved.get("Projectile", "LockOnProbability")
        probability = parse_int32(
            raw_probability, "Missile.LockOnProbability", 100)
        raw_lock_inaccuracy = resolved.get("Projectile", "LockOnInaccuracy")
        lock_inaccuracy = (-1 if raw_lock_inaccuracy is None
                           else parse_wdist(raw_lock_inaccuracy))
        # Random.Next(100) <= 99 is always true. For an always-locked missile,
        # the runtime selects LockOnInaccuracy before calculating its offset.
        if probability >= 99 and lock_inaccuracy >= 0:
            inacc = lock_inaccuracy

    # MiniYAML resolution does not materialize C# field defaults. Bullet is a
    # moving projectile even when Speed is absent: BulletInfo supplies 17.
    # ScaledBullet starts from the same defaults, then its ruleset-loaded hook
    # derives values from the weapon range while the base values still equal
    # those defaults.
    if ptype in MOVING_PROJECTILE_DEFAULT_SPEEDS:
        scaled_speed_sentinel = False
        if speed_raw and "," in str(speed_raw) and ptype in {"Bullet", "ScaledBullet"}:
            values = [parse_wdist(x) for x in str(speed_raw).split(",") if x.strip()]
            if len(values) >= 2:
                if values[1] < values[0]:
                    raise ValueError("Bullet Speed range must be nondecreasing")
                speed = (float(values[0]) if values[0] == values[1] else
                         (values[0] + values[1] - 1) / 2.0)
            else:
                speed = float(values[0])
        else:
            speed = (parse_wdist(speed_raw) if speed_raw else
                     MOVING_PROJECTILE_DEFAULT_SPEEDS[ptype])
            scaled_speed_sentinel = ptype == "ScaledBullet" and speed == BULLET_DEFAULT_SPEED
        if ptype == "ScaledBullet" and rng > 0:
            speed_pct = parse_int32(
                resolved.get("Projectile", "ProjectileSpeedPercentage"),
                "ScaledBullet.ProjectileSpeedPercentage", 0)
            inacc_pct = parse_int32(
                resolved.get("Projectile", "InaccuracyPercentage"),
                "ScaledBullet.InaccuracyPercentage", 0)
            if speed_pct > 0 and scaled_speed_sentinel:
                speed = csharp_div(rng * speed_pct, 100)
            if inacc_pct > 0 and inacc == 0:
                inacc = csharp_div(rng * inacc_pct, 100)
    else:
        if not speed_raw:
            # Unknown/no-scalar trajectories have no modeled travel drift, but
            # retain any authored scatter and carry a limitation where known.
            return True, float(inaccuracy_at_range(inacc))
        speed = parse_wdist(speed_raw)

    inacc = inaccuracy_at_range(inacc)
    eff_speed = max(min(float(speed), SPEED_CAP), 1.0)
    drift = LEAD * TARGET_SPEED * rng / eff_speed if rng else 0.0
    return False, inacc + drift


def effective_damage(resolved):
    """Return (effective, base_total, footprint_total, avg_reliability) or None."""
    validate_damage_warheads(resolved)
    # This legacy flat-only metric still runs after the engine's complete
    # ruleset validation, including percentage fields on otherwise inert nodes.
    pd.percentage_applications(resolved, 1)
    whs = flat_damage_warheads(resolved)
    if not whs:
        return None
    is_instant, sigma = weapon_reliability_ctx(resolved)
    is_direct_actor = direct_actor_impact(resolved)
    eff = base_total = foot_total = 0.0
    rel_weighted = 0.0
    for _tag, wtype, base, node in whs:
        fo = radii = None
        live = True
        if wtype in {"AreaDamage", "SpreadDamage"}:
            # Validate even when the projectile uses DamageWarhead's direct-Actor
            # path: the runtime ruleset loader validates these fields first.
            fo, radii, live = falloff_and_radii(node)
            if wtype == "AreaDamage":
                area_tick_modifiers(node)
        if is_direct_actor:
            rel = reliability([100, 0], [0, POINT_TARGET_RADIUS], sigma)
            eff += base * rel
            base_total += base
            rel_weighted += rel * base
            continue
        if wtype == "TargetDamage":
            radius, live = target_damage_radius(node)
        if not live:
            # Engine deals 0 damage here (single Range + multi-step Falloff).
            # Count the base so the misconfiguration is visible as effective << base.
            base_total += base
            continue
        if wtype == "TargetDamage":
            fp = uniform_footprint_cells2(radius)
            rel = uniform_reliability(radius, sigma)
        elif wtype == "AreaDamage":
            samples = area_geometry_samples(node, fo, radii, sigma)
            rel = sum(weight * tick_rel for weight, tick_rel, _fp in samples)
            fp = sum(weight * tick_fp for weight, _rel, tick_fp in samples)
        else:
            fp = footprint_cells2(fo, radii)
            rel = reliability(fo, radii, sigma)
        contrib = base * (rel + SWARM_W * fp)
        eff += contrib
        base_total += base
        foot_total += fp
        rel_weighted += rel * base
    # AreaBeam invokes every warhead repeatedly within one weapon fire. Keep
    # ``base_total`` as the authored per-impact Damage (the pricing model's
    # inversion variable), but make the per-fire effective metric and cumulative
    # footprint include every expected internal impact.
    impact_multiplier = projectile_impact_multiplier(resolved)
    eff *= impact_multiplier
    foot_total *= impact_multiplier
    avg_rel = rel_weighted / base_total if base_total else 0.0
    return eff, base_total, foot_total, avg_rel, sigma


def main() -> int:
    args = [a for a in sys.argv[1:]]
    top = None
    if "--top" in args:
        i = args.index("--top")
        top = int(args[i + 1])
        del args[i:i + 2]
    names = args
    rs = Model().rs
    verbose = bool(names)
    targets = names if names else [n for n in rs.weapons if not n.startswith("^")]

    rows = []
    for wname in targets:
        resolved = rs.resolve_weapon(wname)
        if resolved is None:
            if verbose:
                print(f"{wname}: UNRESOLVED")
            continue
        r = effective_damage(resolved)
        if r is None:
            if verbose:
                print(f"{wname}: no flat-damage warheads")
            continue
        eff, base_total, foot_total, avg_rel, sigma = r
        rows.append((eff, wname, base_total, foot_total, avg_rel, sigma))

    rows.sort(reverse=True)
    if top:
        rows = rows[:top]

    print(f"# effective_damage  (SWARM_W={SWARM_W} LEAD={LEAD} TARGET_SPEED={TARGET_SPEED} "
          f"SPEED_CAP={SPEED_CAP} DEFAULT_AREA_SPREAD={DEFAULT_AREA_SPREAD} "
          f"POINT_TARGET_RADIUS={POINT_TARGET_RADIUS})  read-only")
    print(f"# {'weapon':30} {'effective':>11} {'base':>9} {'reliab':>6} {'footprint':>9} {'sigma':>6}")
    for eff, wname, base_total, foot_total, avg_rel, sigma in rows:
        print(f"  {wname:30} {eff:11.0f} {base_total:9.0f} {avg_rel:6.2f} {foot_total:9.2f} {sigma:6.0f}")
    print(f"# {len(rows)} weapons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
