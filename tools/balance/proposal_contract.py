"""Shared damage-column contract for class proposals and ledger ingestion.

The cell is per-main damage times main count, NOT total damage or a multiplier
relative to the largest old warhead. Old reports must be regenerated.

Calibration (anchor/verifier) rows instead carry their CURRENT per-shot SUM as
``<total>Σ<count>`` — the report displays where the unit is, never a proposal:
current mains may be unequal and off-grid, so they must never masquerade as
equal proposed mains. ``Σ`` cells are refused on editable rows.
"""
import re

DAMAGE_COLUMN = "dmg/wh×n"
COLUMNS = ("actor", "faction", "HP", "spd", "rng", "cost", DAMAGE_COLUMN,
           "rl", "burst", "legacy FP%", "eff DPS", "price", "Δ", "flags",
           "dmg_filter", "weapon")


def table_header():
    return "| " + " | ".join(COLUMNS) + " |"


def table_separator():
    return "|" + "|".join("---" for _ in COLUMNS) + "|"


def format_damage(per_main, count):
    return f"{per_main}×{count}"


def format_current_total(total, count):
    """CURRENT per-shot SUM over `count` mains — calibration display only."""
    return f"{total}Σ{count}"


def parse_damage(value):
    """Return (damage, count, is_current_total).

    ``A×B`` is a proposed target: A per main, B mains, B >= 1. ``AΣB`` is a
    calibration row's current SUM (uneven/off-grid allowed); it is never a
    target. Anything else is refused.
    """
    value = value.strip()
    match = re.fullmatch(r"([0-9]+)×([1-9][0-9]*)", value)
    if match:
        per_main, count = map(int, match.groups())
        return per_main, count, False
    match = re.fullmatch(r"([0-9]+)Σ([1-9][0-9]*)", value)
    if match:
        total, count = map(int, match.groups())
        return total, count, True
    raise ValueError(f"invalid {DAMAGE_COLUMN} target: {value!r}")
