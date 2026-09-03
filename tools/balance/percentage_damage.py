#!/usr/bin/env python3
"""Shared runtime model for percentage-of-max-health weapon damage.

Cameo currently has two independent percentage-damage shapes:

* a standalone ``AreaDamagePercentage`` / ``HealthPercentageDamage`` warhead;
* a folded second hit on an ``AreaDamage`` warhead with ``PercentageScale``.

The folded hit runs for both positional and direct-Actor impacts. Positional
impacts apply its smaller authored radius; direct hits bypass area geometry and
apply it once to the struck actor.

The distinction is load-bearing for pricing.  A standalone warhead is an
absolute contribution at the reference target HP and therefore creates a DPS
floor.  Folded damage is derived from that warhead's own flat ``Damage`` and
falls to zero with it, so it belongs to the scalable coefficient instead.

This module mirrors the arithmetic in the current ``AreaDamageWarhead.cs`` and
``AreaDamagePercentageWarhead.cs``. Authored fields and final damage remain
Int32, while intermediate products use Int64 to prevent wraparound. It
deliberately knows nothing about target density or projectile
reliability; callers layer those concerns on top of the same runtime
applications returned here.
"""

from __future__ import annotations

from collections.abc import Iterable
from formula import parse_int32


PCT_FOLDED = "pct_folded"
PCT_STANDALONE = "pct_standalone"

STANDALONE_TYPES = frozenset({"AreaDamagePercentage", "HealthPercentageDamage"})

FOLDED_SCALE_DENOMINATOR = 200_000
FOLDED_ROUNDING_BIAS = FOLDED_SCALE_DENOMINATOR // 2
FOLDED_DEFAULT_DENOMINATOR = 10_000
STANDALONE_DEFAULT_DENOMINATOR = 100
DEFAULT_PERCENTAGE_SPREAD = 50
INT32_MIN = -(2 ** 31)
INT32_MAX = 2 ** 31 - 1


def _truncate_div(numerator: int, denominator: int) -> int:
    """Integer division truncated toward zero, matching C# and decimal.Truncate."""
    if denominator == 0:
        raise ZeroDivisionError("percentage denominator must be non-zero")
    magnitude = abs(numerator) // abs(denominator)
    return -magnitude if (numerator < 0) != (denominator < 0) else magnitude


def _runtime_int32(value: int) -> int:
    """Validate an engine Int32 result after wide intermediate arithmetic."""
    if value < INT32_MIN or value > INT32_MAX:
        raise OverflowError("percentage damage exceeds the runtime Int32 result")
    return value


def versus_table(node, field: str = "Versus") -> dict[str, int]:
    """Return one armor table from a MiniYAML warhead node."""
    block = node.child(field)
    if block is None:
        return {}
    out: dict[str, int] = {}
    for child in block.children:
        out[child.key] = parse_int32(
            child.value, f"{field}.{child.key}")
    return out


def folded_units(damage: int, scale: int) -> tuple[float, int]:
    """Continuous and engine-rounded percentage units for one folded hit.

    The engine expression is ``(Damage * PercentageScale + 100000) / 200000``
    using an Int64 intermediate and integer division. The
    continuous wide value is kept separately because it is the scalable design
    coefficient; the difference to the runtime value is a quantisation residual.
    """
    continuous = damage * scale / FOLDED_SCALE_DENOMINATOR
    numerator = damage * scale + FOLDED_ROUNDING_BIAS
    rounded = _runtime_int32(
        _truncate_div(numerator, FOLDED_SCALE_DENOMINATOR))
    return continuous, rounded


def runtime_percentage_hp(reference_hp: float, units: int, denominator: int) -> int:
    """Neutral-armor HP damage with the current C# wide-intermediate path."""
    hp = int(reference_hp)
    after_units = _truncate_div(hp * units, 100)
    after_units = _runtime_int32(after_units)
    return _runtime_int32(_truncate_div(after_units * 100, denominator))


def percentage_applications(resolved, reference_hp: float) -> list[dict]:
    """Return every positive runtime percentage application on a weapon.

    Applications are identified by warhead TYPE, never by a tag suffix.  A
    weapon that carries folded and standalone percentage hits really executes
    both, so no weapon-level deduplication is performed.
    """
    out: list[dict] = []
    for node in resolved.children:
        if not node.key.startswith("Warhead"):
            continue
        tag = node.key.split("@", 1)[1] if "@" in node.key else node.key

        if node.value == "AreaDamage":
            damage = parse_int32(node.get("Damage"), f"{tag}.Damage")
            scale = parse_int32(
                node.get("PercentageScale"), f"{tag}.PercentageScale", 0)
            denominator = parse_int32(
                node.get("PercentageDenominator"),
                f"{tag}.PercentageDenominator", FOLDED_DEFAULT_DENOMINATOR)
            percentage_spread = parse_int32(
                node.get("PercentageSpread"),
                f"{tag}.PercentageSpread", DEFAULT_PERCENTAGE_SPREAD)
            # AreaDamageWarhead validates this field unconditionally, even
            # when Damage or PercentageScale would make the folded hit inert.
            if denominator <= 0:
                raise ValueError(
                    f"{tag}: AreaDamage PercentageDenominator must be positive")
            if damage is None or damage <= 0 or scale <= 0:
                continue

            continuous_units, runtime_units = folded_units(damage, scale)
            if runtime_units <= 0 and continuous_units <= 0:
                continue
            continuous_hp = reference_hp * continuous_units / denominator
            runtime_hp = runtime_percentage_hp(reference_hp, runtime_units, denominator)
            pct_versus = versus_table(node, "PercentageVersus")
            out.append({
                "kind": PCT_FOLDED,
                "tag": tag,
                "node": node,
                "damage": damage,
                "scale": scale,
                "denominator": denominator,
                "continuous_units": continuous_units,
                "runtime_units": runtime_units,
                "continuous_hp": continuous_hp,
                "runtime_hp": runtime_hp,
                "rounding_hp": runtime_hp - continuous_hp,
                "versus": pct_versus or versus_table(node),
                "percentage_spread": percentage_spread,
            })
            continue

        if node.value not in STANDALONE_TYPES:
            continue
        if node.value == "AreaDamagePercentage":
            # This class inherits the field even though its standalone hit does
            # not use it; FieldLoader still requires valid Int32 syntax.
            parse_int32(
                node.get("PercentageSpread"),
                f"{tag}.PercentageSpread", DEFAULT_PERCENTAGE_SPREAD)
            denominator = parse_int32(
                node.get("PercentageDenominator"),
                f"{tag}.PercentageDenominator", STANDALONE_DEFAULT_DENOMINATOR)
            if denominator <= 0:
                raise ValueError(
                    f"{tag}: AreaDamagePercentage PercentageDenominator "
                    "must be positive")
            scale = parse_int32(
                node.get("PercentageScale"), f"{tag}.PercentageScale", 0)
            if scale > 0:
                raise ValueError(
                    f"{tag}: AreaDamagePercentage cannot also set PercentageScale")
        else:
            # HealthPercentageDamage has no PercentageDenominator field. Its
            # runtime divisor is always 100, so a foreign inherited key must
            # not alter the analysis.
            denominator = STANDALONE_DEFAULT_DENOMINATOR
        damage = parse_int32(node.get("Damage"), f"{tag}.Damage")
        if damage is None or damage <= 0:
            continue
        hp_equiv = reference_hp * damage / denominator
        runtime_hp = runtime_percentage_hp(reference_hp, damage, denominator)
        out.append({
            "kind": PCT_STANDALONE,
            "tag": tag,
            "node": node,
            "damage": damage,
            "denominator": denominator,
            "continuous_units": float(damage),
            "runtime_units": damage,
            "continuous_hp": hp_equiv,
            "runtime_hp": runtime_hp,
            "rounding_hp": runtime_hp - hp_equiv,
            "versus": versus_table(node),
            "percentage_spread": None,
        })
    return out


def _falloff_at(falloff: list[float], radii: list[float], radius: float) -> float:
    if radius <= radii[0]:
        return float(falloff[0])
    for index in range(len(falloff) - 1):
        inner, outer = radii[index], radii[index + 1]
        if radius <= outer:
            if outer <= inner:
                return float(falloff[index])
            position = (radius - inner) / (outer - inner)
            return falloff[index] + (falloff[index + 1] - falloff[index]) * position
    return 0.0


def clip_falloff(
        falloff: Iterable[float], radii: Iterable[float], percentage_spread: int | None
        ) -> tuple[list[float], list[float]]:
    """Clip a main falloff curve at the folded percentage radius.

    Runtime does not compress the curve.  It computes the normal main falloff,
    then rejects victims beyond ``outer * PercentageSpread / 100``.  Keeping the
    original inner radii and adding one interpolated endpoint reproduces that
    shape for reliability and footprint integration.
    """
    spread = DEFAULT_PERCENTAGE_SPREAD if percentage_spread is None else percentage_spread
    rs = [float(value) for value in radii]
    if not rs:
        return [float(value) for value in falloff], rs
    outer = int(rs[-1])
    cutoff = min(outer, max(0, outer * int(spread) // 100))
    return clip_falloff_at_radius(falloff, rs, cutoff)


def clip_falloff_at_radius(
        falloff: Iterable[float], radii: Iterable[float], cutoff: int | float
        ) -> tuple[list[float], list[float]]:
    """Clip a falloff curve at one absolute runtime victim radius."""
    fo = [float(value) for value in falloff]
    rs = [float(value) for value in radii]
    if len(fo) < 2 or len(fo) != len(rs):
        return fo, rs
    cutoff = min(rs[-1], max(0.0, float(cutoff)))
    if cutoff >= rs[-1]:
        return fo, rs
    if cutoff <= rs[0]:
        return [fo[0], 0.0], [rs[0], rs[0]]

    clipped_fo: list[float] = []
    clipped_rs: list[float] = []
    for value, radius in zip(fo, rs):
        if radius < cutoff:
            clipped_fo.append(value)
            clipped_rs.append(radius)
        else:
            break
    clipped_fo.append(_falloff_at(fo, rs, cutoff))
    clipped_rs.append(float(cutoff))
    return clipped_fo, clipped_rs
