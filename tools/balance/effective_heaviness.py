#!/usr/bin/env python3
"""Shared runtime model for DESIGN §12.0i continuous heaviness (effective profiles).

One module, imported by ``percentage_damage`` / ``effective_damage`` /
``weapon_efficiency`` — it imports only ``formula``, so no pricing module can
create a circular import. It mirrors the C# in
``OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs`` (validation, radius
scaling, percentage-band interpolation) and
``OpenRA.Mods.Cameo/Warheads/HeavinessBell.cs`` (the bell) exactly:

* ``Heaviness`` is ``-1`` or omitted = disabled (authored values verbatim);
  ``0..2000`` are active thousandths of ``h``. ``0`` is ACTIVE h = 0.0 —
  distinct from disabled by ruling (Aedis 2026-09).
* The percentage half's additive per-armor bands: optional full
  ``PercentageVersusLight`` / ``PercentageVersusHeavy`` anchor tables. Both
  must be present, both must carry exactly the key set of the explicit
  ``PercentageVersus`` (the h = 1 medium anchor). Interpolation is piecewise
  L->M on h in [0,1] and M->H on h in (1,2], rounded ties-even per armor,
  THEN the bell runs ONCE over the interpolated table. ``PercentageScale``
  stays the scalar dial it always was.
* Active ``h`` scales ``Spread``, explicit ``Range`` and ``MinRadius`` /
  ``MaxRadius`` consistently by ``(h + 2) / 3`` with the C# ``(int)`` cast's
  truncate-toward-zero, so footprint geometry (K) sees the real splash.
* Heaviness is loaded by the engine on ``AreaDamage`` AND on its subclass
  ``AreaDamagePercentageWarhead`` (fields inherit; nothing is dropped for a
  subclass of a labelled type). Parity covers both: the subclass gets the
  bell on its Versus and the geometry scaling, but NEVER the folded-half
  anchors — ``PercentageVersusLight``/``Heavy`` are rejected there. On
  ``SpreadDamage`` / ``TargetDamage`` / ``HealthPercentageDamage`` the field
  is genuinely unknown and DROPPED (FieldLoader), so callers must not honour
  it there.

K is NOT assumed invariant in h (Aedis review rejected that): the bell moves the mean
Versus and the radius scale moves the geometry, and pricing is expected to read those
actual effects through this module. (The audit's mean check is the arithmetic mean —
see audit_heaviness_bell.py.)
"""

from __future__ import annotations

import math

from formula import parse_int32

DISABLED = -1
HEAVINESS_MAX = 2000
INT32_MAX = 2 ** 31 - 1
INT32_MIN = -(2 ** 31)

# HeavinessMode values (FieldLoader enum: heaviest-case unknown value fails at
# load, before RulesetLoaded). Legacy = the endpoint implementation; SharedVersus
# = the approved §12.0i shared profile (Aedis 2026-09-10 03:17).
MODE_LEGACY = "Legacy"
MODE_SHARED = "SharedVersus"
HEAVINESS_MODES = (MODE_LEGACY, MODE_SHARED)

# HeavinessBell.cs — one global 13-slot scale, 0..2, step 1/6.
BELL_AXIS_ORDER = [
    ["Scout"], ["None"], ["Fighter"], ["Light"], ["Wood"], ["Bomber"],
    ["Medium", "Flak", "Steel"], ["Helicopter"], ["Concrete"], ["Heavy"],
    ["Spaceship"], ["Plate"], ["Superheavy"],
]
BELL_AXIS = {armor: i * 2.0 / (len(BELL_AXIS_ORDER) - 1)
             for i, slot in enumerate(BELL_AXIS_ORDER) for armor in slot}
BELL_LO = 1.0 / 1.5
BELL_SIGMA = 0.75

DERIVED_ARMORS = frozenset({"Heroic", "Airborne"})
NON_ARMOR_ROWS = frozenset(
    {"Shield", "HAZMAT", "COMPOSITE", "BLAST", "REFLECTOR", "ARMOR"})

# Ladders, lightest -> heaviest, for the rank-restore step.
LADDERS = [
    ["None", "Flak", "Plate", "Heroic"],
    ["Scout", "Light", "Medium", "Heavy", "Superheavy"],
    ["Wood", "Steel", "Concrete"],
    ["Fighter", "Bomber", "Helicopter", "Spaceship"],
]


class HeavinessError(ValueError):
    """A heaviness / anchor configuration the engine would reject at RulesetLoaded."""


def heaviness_mode_of(node) -> str:
    """Read and canonicalise ``HeavinessMode`` (Legacy default). Unknown values
    fail clear: the engine's FieldLoader enum parse also accepts a numeric
    member outside the enum, so the C# gates it with Enum.IsDefined at
    RulesetLoaded — mirror that here by only accepting the two defined
    members, by name or by their numeric index."""
    raw = node.get("HeavinessMode")
    if raw is None or str(raw).strip() == "":
        return MODE_LEGACY
    value = str(raw).strip()
    names = {MODE_LEGACY.lower(), MODE_SHARED.lower()}
    if value.lstrip("-").isdigit():
        index = int(value)
        if 0 <= index < len(HEAVINESS_MODES):
            return HEAVINESS_MODES[index]
        raise HeavinessError(
            f"Unknown HeavinessMode {raw!r}: numeric value outside "
            f"{len(HEAVINESS_MODES)} defined modes (Enum.IsDefined rejects it "
            f"at rules load on the C# side).")
    for known in HEAVINESS_MODES:
        if value.lower() == known.lower():
            return known
    raise HeavinessError(
        f"Unknown HeavinessMode {raw!r}: must be one of "
        f"{', '.join(HEAVINESS_MODES)} (by name, or by their "
        f"{len(HEAVINESS_MODES)}-value numeric index).")


def heaviness_profile_config(node, light: dict, medium: dict, heavy: dict,
                             *, subclass_twin: bool = False) -> tuple[str, int]:
    """Validate the (mode, Heaviness, percentage tables) triple exactly as

    the C# RulesetLoaded does, and return the effective configuration. Legacy
    mode mirrors ``validate_anchors``; the SharedVersus mode requires an active
    Heaviness and rejects every percentage table and endpoint dictionary.
    """
    mode = heaviness_mode_of(node)
    heaviness = heaviness_of(node)
    if mode == MODE_SHARED:
        if subclass_twin:
            raise HeavinessError(
                "AreaDamagePercentage does not support the SharedVersus "
                "heaviness mode: only the Legacy mode (the default) is "
                "available here.")
        if heaviness < 0:
            raise HeavinessError(
                "HeavinessMode SharedVersus requires an active Heaviness "
                "(0..2000); omitting Heaviness disables heaviness entirely.")
        has_pct = bool(medium) or bool(light) or bool(heavy)
        if has_pct:
            raise HeavinessError(
                "HeavinessMode SharedVersus rejects PercentageVersus and the "
                "PercentageVersusLight/Heavy endpoints: the percentage half "
                "follows the SAME belled table as the flat half.")
        return mode, heaviness
    validate_anchors(heaviness, light, medium, heavy,
                     subclass_twin=subclass_twin)
    return mode, heaviness


def validate_shared_numeric(mode: str, heaviness: int, versus: dict,
                            damage: int | None = None,
                            scale: int | None = None) -> None:
    """THE SHARED PROFILE's nonnegative-input contract + load-time overflow

    check, mirroring the C# RulesetLoaded block (review follow-up items 2–3):
    a negative Damage, PercentageScale or Shield coefficient fails even at
    h = 0 (where the percentage units happen to be zero), and the combined
    fraction is computed so an Int32-bound overflow fails at load, not first
    on impact. Non-shared modes return unchanged — legacy healing/default
    behavior is never gated here."""
    if mode != MODE_SHARED:
        return
    if damage is not None and damage < 0:
        raise HeavinessError(
            f"HeavinessMode SharedVersus rejects a negative Damage ({damage}); "
            f"the approved conversion is nonnegative.")
    if scale is not None and scale < 0:
        raise HeavinessError(
            f"HeavinessMode SharedVersus rejects a negative PercentageScale "
            f"({scale}); the approved conversion is nonnegative.")
    if versus.get("Shield", 0) < 0:
        raise HeavinessError(
            f"HeavinessMode SharedVersus rejects a negative Shield coefficient "
            f"({versus['Shield']}); the approved (2000 + h) / 2000 scaling is "
            f"nonnegative.")
    if damage is not None and scale is not None:
        # Raises OverflowError on an Int32-bound result — fail clear at load,
        # without any lazy cross-import (the same arrow runs the other way).
        denominator = 200_000 * 2000
        rounded = (damage * scale * heaviness + denominator // 2) // denominator
        if rounded > INT32_MAX:
            raise OverflowError(
                f"HeavinessMode SharedVersus: percentage units (Damage {damage} "
                f"x PercentageScale {scale} x Heaviness {heaviness}) exceed "
                f"Int32.")


def shield_coefficient(value: int, heaviness: int) -> int:
    """The shared profile's ONE Shield scaling: <c>(2000 + h) / 2000</c>, half-up
    over the (nonnegative) belled value — 100% at h=0, 200% at h=2. Shared with
    the C# ``ScaleShieldCoefficient``; never applied a second time."""
    return (value * (2000 + heaviness) + 1000) // 2000


def shared_versus_profile(versus: dict, heaviness: int) -> dict[str, int]:
    """THE SHARED PROFILE's single effective table: the flat Versus belled ONCE,

    then the Shield row's coefficient scaled ONCE by (2000 + h) / 2000. The
    percentage half reuses this exact result (no second transform anywhere).
    Disabled heaviness is a configuration error in this mode — callers already
    validated that (heaviness_config) before reaching here.
    """
    belled = bell_transform(versus, heaviness / 1000.0)
    out = dict(belled)
    if "Shield" in out:
        out["Shield"] = shield_coefficient(out["Shield"], heaviness)
    return out


def heaviness_of(node) -> int:
    """Read ``Heaviness`` from an AreaDamage warhead node (-1 when omitted)."""
    value = parse_int32(node.get("Heaviness"), "Heaviness", DISABLED)
    if value < DISABLED or value > HEAVINESS_MAX:
        raise HeavinessError(
            f"Heaviness must be -1 (disabled) or 0..{HEAVINESS_MAX} "
            f"(thousandths of h), got {value}")
    return value


def validate_anchors(heaviness: int, light: dict, medium: dict,
                     heavy: dict, *, subclass_twin: bool = False) -> None:
    """Mirror the C# anchor validation (same order, same conditions).

    ``subclass_twin``: the AreaDamagePercentage subclass is itself a percentage
    weapon; it forbids the folded half the endpoints parameterise, so the C#
    subclass rejects their presence outright — mirror that here instead of
    honouring half a configuration nobody reads.
    """
    has_bands = bool(light) or bool(heavy)
    if subclass_twin and has_bands:
        raise HeavinessError(
            "AreaDamagePercentage cannot set PercentageVersusLight/Heavy: these "
            "endpoints parameterise the folded percentage half, which this "
            "warhead forbids entirely.")
    if heaviness < 0 and has_bands:
        raise HeavinessError(
            "PercentageVersusLight/Heavy endpoints require an active Heaviness "
            "(0..2000); omitting Heaviness disables heaviness entirely.")
    if not has_bands:
        return
    if not light or not heavy:
        raise HeavinessError(
            "PercentageVersusLight and PercentageVersusHeavy must both be set.")
    if not medium:
        raise HeavinessError(
            "PercentageVersusLight/Heavy require an explicit PercentageVersus "
            "(the h=1 medium anchor).")
    if (set(light) != set(medium)) or (set(heavy) != set(medium)):
        raise HeavinessError(
            "PercentageVersusLight/Heavy keys must match PercentageVersus exactly.")
    for table_name, anchor in (("PercentageVersus", medium),
                               ("PercentageVersusLight", light),
                               ("PercentageVersusHeavy", heavy)):
        for armor, value in anchor.items():
            if value < 0:
                raise HeavinessError(
                    f"{table_name} anchor values must be non-negative "
                    f"({armor}: {value}).")


def round_half_even(numerator: int, denominator: int) -> int:
    """Integer half-to-even rounding, truncating toward zero on non-ties."""
    if denominator == 0:
        raise ZeroDivisionError("round_half_even denominator must be non-zero")
    negative = (numerator < 0) != (denominator < 0)
    magnitude = abs(numerator)
    denom = abs(denominator)
    quotient, remainder = divmod(magnitude, denom)
    twice = 2 * remainder
    if twice > denom or (twice == denom and quotient % 2 != 0):
        quotient += 1
    return -quotient if negative else quotient


def scale_length(length: int, heaviness: int) -> int:
    """One bounded radius scale shared with the C# (ScaledRadiusLength).

    <c>length * (h + 2) / 3</c> must fit Int32 before the engine cast — BOTH
    bounds are checked (review 2026-09-10): a NEGATIVE authored WDist scales
    MORE negative, so h=2's 4/3 can underflow below Int32 exactly like    h=0 can overflow above Int32; either would wrap silently in the unchecked
    C# cast, so fail clear on exactly that overflow. Normal values truncate
    toward zero like the C# cast. Disabled: verbatim — including negative
    authored radii (legacy behavior preserved, no active-path rejection).
    """
    if heaviness < 0:
        return length
    scale = (heaviness / 1000.0 + 2.0) / 3.0
    scaled = length * scale
    if scaled > INT32_MAX or scaled < INT32_MIN:
        raise HeavinessError(
            f"Scaled radius {scaled:f} (authored {length} x {scale:f} at "
            f"h={heaviness / 1000.0}) overflows Int32.")
    return int(scaled)


def interpolate_percentage_bands(light: dict, medium: dict, heavy: dict,
                                 heaviness: int) -> dict[str, int]:
    """Piecewise per-armor interpolation between the three anchor tables.

    L->M for h in [0,1] and M->H for h in (1,2], exact integer arithmetic,
    ties-even per armor. ``medium`` drives the iteration order (the anchors
    share one key set, validated by ``validate_anchors``).
    """
    interpolated: dict[str, int] = {}
    for armor, medium_value in medium.items():
        if heaviness <= 1000:
            product = light[armor] * (1000 - heaviness) + medium_value * heaviness
        else:
            product = (medium_value * (HEAVINESS_MAX - heaviness)
                       + heavy[armor] * (heaviness - 1000))
        interpolated[armor] = round_half_even(product, 1000)
    return interpolated


def _centre_of_mass(values: dict[str, float]) -> float | None:
    total = 0.0
    weighted = 0.0
    for armor, value in values.items():
        if value > 0 and armor in BELL_AXIS:
            total += value
            weighted += BELL_AXIS[armor] * value
    return weighted / total if total else None


def bell_transform(table: dict, h: float) -> dict[str, int]:
    """Exact mirror of ``HeavinessBell.Transform`` (float math, int output)."""
    values = {armor: float(value) for armor, value in table.items()}
    live = [value for armor, value in values.items()
            if armor not in NON_ARMOR_ROWS]
    if not live or max(live) <= min(live):
        return {armor: int(value) for armor, value in table.items()}

    tiltable = {armor: value for armor, value in values.items()
                if armor in BELL_AXIS and armor not in DERIVED_ARMORS}
    com = _centre_of_mass(tiltable)
    if com is not None:
        mu = (h + com) / 2.0
        belled = {armor: value * (BELL_LO + (1.0 - BELL_LO)
                                  * math.exp(-((BELL_AXIS[armor] - mu) ** 2)
                                             / (2.0 * BELL_SIGMA * BELL_SIGMA)))
                  for armor, value in tiltable.items()}

        before = sum(tiltable.values()) / len(tiltable)
        after = sum(belled.values()) / len(belled)
        if after > 0:
            factor = before / after
            belled = {armor: value * factor for armor, value in belled.items()}

        for ladder in LADDERS:
            rungs = [armor for armor in ladder if armor in belled]
            if len(rungs) < 2:
                continue
            order = sorted(range(len(rungs)),
                           key=lambda i: (-values[rungs[i]], i))
            ranked = sorted((belled[armor] for armor in rungs), reverse=True)
            for slot, i in enumerate(order):
                values[rungs[i]] = ranked[slot]

    # Re-derive the product armors LAST from the finished profile (§12.0b).
    # ⚠ Two guards: an empty candidate set (a table with ONLY derived / non-slot
    # rows) must not call max() — it would raise — and the ORIGINAL peak > 0 rule
    # must stay, because a non-positive peak (zero or negative values) would
    # divide by zero or flip the product below. Fail safe: skip in both cases.
    peak_values = [value for armor, value in values.items()
                   if armor not in NON_ARMOR_ROWS and armor not in DERIVED_ARMORS]
    if peak_values and max(peak_values) > 0:
        peak = max(peak_values)
        for name, first, second in (("Heroic", "Plate", "Scout"),
                                    ("Airborne", "Helicopter", "Scout")):
            if name in values and first in values and second in values:
                values[name] = values[first] * values[second] / peak

    return {armor: round(value) for armor, value in values.items()}


def versus_profile(versus: dict, heaviness: int) -> dict[str, int]:
    """Effective main Versus table: verbatim when disabled, bell once when active."""
    if heaviness < 0:
        return dict(versus)
    return bell_transform(versus, heaviness / 1000.0)


def percentage_profile(versus: dict, percentage_versus: dict,
                       light: dict, heavy: dict, heaviness: int) -> dict[str, int]:
    """Effective percentage-half table, mirroring the C# branch exactly.

    Disabled: the authored table (or the main Versus when absent). Active with
    both anchors: piecewise interpolation rounded ties-even, then ONE bell pass.
    Active without anchors: one bell pass over the authored table (or Versus).
    """
    validate_anchors(heaviness, light, percentage_versus, heavy)
    if heaviness < 0:
        return dict(percentage_versus) if percentage_versus else dict(versus)
    h = heaviness / 1000.0
    if light or heavy:
        return bell_transform(
            interpolate_percentage_bands(light, percentage_versus, heavy, heaviness),
            h)
    if percentage_versus:
        return bell_transform(percentage_versus, h)
    return bell_transform(versus, h)


def effective_geometry(spread: int, range_list: list[int] | None,
                       min_radius: int, max_radius: int,
                       heaviness: int) -> dict:
    """Effective radius geometry: verbatim when disabled, scaled consistently when active."""
    if heaviness < 0:
        return {"spread": spread, "range": range_list,
                "min_radius": min_radius, "max_radius": max_radius}
    return {
        "spread": scale_length(spread, heaviness),
        "range": None if range_list is None
        else [scale_length(radius, heaviness) for radius in range_list],
        "min_radius": scale_length(min_radius, heaviness),
        "max_radius": scale_length(max_radius, heaviness),
    }
