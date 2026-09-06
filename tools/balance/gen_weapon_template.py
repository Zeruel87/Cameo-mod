#!/usr/bin/env python3
"""gen_weapon_template.py — generate weapon-class template families.

THE TWO-LEVEL ORDERING LAW (maintainer 2026-08-01 — the most important part):
A weapon's Versus ORDER is built, never hand-typed, from two decisions:

  1. MACRO-TYPE PRIORITY — which unit TYPE it is strong against, best->worst:
     Infantry / Vehicle / Building / Aircraft. Types may be TIED (combined,
     interleaved) when a weapon is equally good vs several.
  2. LIGHT<->HEAVY DIRECTION — within every type, is it better vs LIGHT or
     HEAVY armor? Applied to the armor SUB-LADDERS (lightest -> heaviest):
        Infantry : None < Flak < Plate < Heroic
        Vehicle  : Scout < Light < Medium < Heavy < Superheavy
        Building : Wood < Steel < Concrete
        Aircraft : Fighter < Bomber < Helicopter < Spaceship
     anti-LIGHT weapons (HE, flame, bullets) hit None > ... > Heroic;
     anti-HEAVY weapons (AP, tesla, railgun) hit Heroic > ... > None.

The 16-armor order = concatenate the macro blocks in priority order; inside
each block list the sub-ladder in the chosen direction; interleave tied blocks
round-robin. Then LEVEL (Light/Medium/Heavy = step 6/5/4 = WC 0.75/1.0/1.25)
only changes the falloff slope — ONE order per weapon TYPE, shared by L/M/H.

Naming: UNIFIED `^Warhead_<Family>_<Level>` (family-first, underscore).
Usage:  gen_weapon_template.py [family ...] | --list | --orders
"""
from __future__ import annotations
import json
import os
import math
import pathlib
import statistics
import sys

LADDERS = {  # lightest -> heaviest
    "INF": ["None", "Flak", "Plate", "Heroic"],
    "VEH": ["Scout", "Light", "Medium", "Heavy", "Superheavy"],
    "BLD": ["Wood", "Steel", "Concrete"],
    "AIR": ["Fighter", "Bomber", "Helicopter", "Spaceship"],
}
CANON16 = {a for arms in LADDERS.values() for a in arms}
# Level = step (falloff slope) = WeaponClass. Super (step 3, floor 55, WC 1.5, Shield 155)
# is the superweapon band for Nuclear + charged Tesla — one notch above Heavy (maintainer 2026-08-02).
LEVELS = {"Light": (6, 10, 16), "Medium": (5, 25, 20), "Heavy": (4, 40, 25), "Super": (3, 55, 30),
          # `Trace` is the SUB-LIGHT tier (WC 0.5) that WEAPON_TYPE_SYSTEM.md specifies for
          # Toxic: a lingering field a delivery weapon leaves behind, not an armament.
          # ⚠ **It MUST stay last in this dict.** `li = list(LEVELS).index(level)` indexes the
          # `spreads` and `falloffs` TUPLES positionally, so inserting a level anywhere but the
          # end silently shifts every other family's spread and falloff by one slot. Its own
          # index is therefore 4, and any family using it needs 5-long tuples.
          # Body is Light's: a family on this tier is expected to carry a designed profile, so
          # the even-ramp fallback is never reached, and Light's is the sane default if it is.
          "Trace": (6, 10, 16)}
WC = {"Light": 0.75, "Medium": 1.0, "Heavy": 1.25, "Super": 1.5, "Trace": 0.5}
# FLAT / "ignores armor" (Sonic): flat SpreadDamage, same value vs every armor. Tunable.
FLAT_VALUES = {"Light": 45, "Medium": 55, "Heavy": 65}   # main SpreadDamage vs ALL armors
FLAT_PCT = {"Light": 5, "Medium": 8, "Heavy": 10}        # its modest % chip
# PCT / "%-equalizer" (Magic): tiny flat + a LARGE uniform % of max HP (ignores armor) = giant-killer.
MAGIC_MAIN = {"Light": 22, "Medium": 27, "Heavy": 32, "Super": 38}   # Magic flat = 1/2 Sonic flat (uniform)
MAGIC_PCT  = {"Light": 25, "Medium": 40, "Heavy": 50, "Super": 65}   # Magic percentage profile; magnitude follows main Damage through PercentageScale


def block_seq(group, direction):
    """One priority block -> ordered armor list. group = macro str or tuple of
    macro strs (combined = interleaved round-robin).

    Interleave rule (maintainer 2026-08-02): the LONGEST sub-ladder LEADS, then
    round-robin, so the categories alternate evenly and the extra entries of the
    longer ladder are spread out. inf(4)+veh(5) heavy ->
    Superheavy Heroic Heavy Plate Medium Flak Light None Scout (V I V I V I V I V).
    Ties (inf 4 vs air 4) keep the tuple order (stable sort)."""
    macs = (group,) if isinstance(group, str) else group
    ladders = [list(LADDERS[m]) for m in macs]
    ladders.sort(key=len, reverse=True)  # longest leads; stable keeps tie order
    if direction == "heavy":
        for l in ladders:
            l.reverse()
    out, i = [], 0
    while any(i < len(l) for l in ladders):
        for l in ladders:
            if i < len(l):
                out.append(l[i])
        i += 1
    return out


def build_order(blocks, direction):
    order = []
    for g in blocks:
        order += block_seq(g, direction)
    assert set(order) == CANON16, ("order not a permutation", set(order) ^ CANON16)
    return order


# --- THE WEAPON-TYPE MATRIX: (macro-priority blocks, direction, hits_air, levels) ---
# blocks: list of macro names / tuples (tuple = combined+interleaved). direction
# applies to ALL blocks. hits_air controls ValidTargets. Grounded in the extracted
# "how they used to be" orders, corrected to the clean sub-ladders.
L3 = ["Light", "Medium", "Heavy"]
WEAPONS = {
    "Bullet":     (["INF", ("VEH", "AIR", "BLD")],      "light", True,  L3),
    "CannonAP":   (["VEH", "BLD", "INF", "AIR"],        "heavy", False, L3),
    "CannonHE":   ([("VEH", "BLD"), "INF", "AIR"],      "light", False, L3),
    "MissileAP":  (["VEH", "AIR", "BLD", "INF"],        "heavy", True,  L3),
    "MissileHE":  ([("VEH", "BLD"), "AIR", "INF"],      "light", True,  L3),
    "MissileAA":  (["AIR", "VEH", "BLD", "INF"],        "heavy", True,  L3),
    "Flak":       (["AIR", "INF", "VEH", "BLD"],        "light", True,  L3),
    # Laser = equally good vs ALL 4 types, anti-HEAVY (starts Superheavy), HITS air.
    "Laser":      ([("VEH", "INF", "AIR", "BLD")],      "heavy", True,  L3),
    # Prism = Laser mirrored to anti-LIGHT (starts Scout), GROUND-ONLY (air last) —
    # keeps AP/TankDestroyers relevant (prism = anti-light, AP = anti-heavy).
    "Prism":      ([("VEH", "INF", "BLD"), "AIR"],      "light", False, L3),
    "Flame":      ([("INF", "BLD"), "VEH", "AIR"],      "light", False, L3),
    "Chemical":   ([("INF", "VEH"), "BLD", "AIR"],      "heavy", False, L3),
    # Toxic = the ANTI-INFANTRY GAS, and a DIFFERENT weapon from Chemical, which is CORROSION
    # (PHYSICAL_STATE_SYSTEM.md maps Chemical to the Corrosion meter — "pure corrosion" — and
    # W9 notes "corrosion eats vehicles"; SPREAD_FALLOFF_PLAN.md calls Chemical a green blast
    # and explicitly "NOT the gas cloud"). That is exactly why the two point OPPOSITE ways:
    # Chemical is anti-HEAVY because acid eats armour, Toxic is anti-LIGHT because gas kills
    # people. Order and direction are MEASURED from the mod's own 28 gas/toxin weapons, not
    # invented — see tools/balance/design_invented_profiles.py.
    # Hits air (low, non-zero) because the legacy ^ToxicWeapon always did; W13 rule 8 wants
    # "cannot really fight air" expressed by ranking air LAST, never by omitting it.
    "Toxic":      (["INF", "BLD", "VEH", "AIR"],        "light", True,  ["Trace", "Light", "Medium"]),
    "Melee":      (["INF", "VEH", "BLD", "AIR"],        "light", False, L3),
    "Arrow":      (["INF", "AIR", "VEH", "BLD"],        "light", True,  L3),
    # Magic = %-EQUALIZER (maintainer 2026-08-02): ground-only, tiny flat + big uniform %
    # of max HP (ignores armor) = giant-killer (melts high-HP units, useless vs swarms).
    # The mirror of Sonic (Sonic = flat/anti-low-HP; Magic = %/anti-high-HP).
    "Magic":      ("PCT", "pct", False, L3 + ["Super"]),
    # Demolition = BUILDINGS first, infantry second (maintainer 2026-08-02).
    "Demolition": (["BLD", "INF", "VEH", "AIR"],        "light", False, L3),
    "Concussion": ([("INF", "VEH", "BLD"), "AIR"],      "light", False, L3),
    # Sonic = FLAT / "ignores armor" (maintainer 2026-08-02): every armor takes the
    # same per-level value — no light/heavy gradient, no macro preference. A pure
    # generalist (never great, never useless). Values in FLAT_VALUES (tunable).
    "Sonic":      ("FLAT", "flat", False, L3),
    # tier-locked (late-game only) -------------------------------------------
    "Railgun":     (["VEH", "INF", "BLD", "AIR"],       "heavy", False, ["Heavy"]),
    "Tesla":       ([("INF", "VEH"), "BLD", "AIR"],     "heavy", False, L3 + ["Super"]),  # 4-tier (L/M/H/Super); was TeslaCharged at Super
    # Nuclear = BUILDING-first heavy (levels structures+heavy units+air, weak vs inf) — distinct
    # from Chemical/Tesla (inf+veh). Super tier (step 3, WC 1.5). Maintainer 2026-08-02.
    "Nuclear":     (["BLD", "VEH", "AIR", "INF"],       "heavy", True,  L3 + ["Super"]),
}


# --- PAID-FOR ExtraDamage chips (AREADAMAGE_WARHEAD_REBALANCE.md §3 REVISION 2026-08-08) ---
# Only energy weapons carry a chip, and only because each PAYS for it (K, a charge delay, or a
# structural handicap). Chip = SpreadDamage, Damage = 50% of main, EXCLUDED from price (suffix
# _ExtraDamage). Bespoke per-family Versus (NOT formula-generated). Armors omitted => floor 10.
# Per-family floor for armors not listed in the chip ladder (buildings/air/Shield).
CHIP_FLOOR = {"Laser": 9, "Railgun": 10, "Tesla": 10}
CHIPS = {
    # Laser: anti-LIGHT (inf+veh), reversed ladder — floor 9 (bldg/air), Superheavy 12, +3/step toward light.
    # Pays for: thin energy spread + 4 air ladder-slots diluting its ground damage.
    "Laser": {"Scout": 36, "None": 33, "Light": 30, "Flak": 27, "Medium": 24,
              "Plate": 21, "Heavy": 18, "Heroic": 15, "Superheavy": 12},
    # Railgun: anti-BUILDING + superheavy siege. Pays for: a charge delay (per-weapon, = 50% reload).
    "Railgun": {"Concrete": 200, "Steel": 175, "Wood": 150, "Superheavy": 125, "Heavy": 100,
                "Medium": 75, "Light": 50, "Scout": 25},
    # Tesla L/M/H: anti-armored-inf + shield (restored old TeslaExtraDamage). Pays for: K=1.25 (weak EMP).
    "Tesla": {"REFLECTOR": 50, "Shield": 300, "Heroic": 200, "Plate": 175, "Flak": 150, "None": 125,
              "Superheavy": 100, "Heavy": 75, "Medium": 50, "Light": 25},
}
# Tesla_Super uses a STRONGER chip (was TeslaCharged), keyed by level. Pays for: Super tier + K.
CHIPS_LEVEL = {
    ("Tesla", "Super"): {"REFLECTOR": 50, "Shield": 400, "Heroic": 300, "Plate": 275, "Flak": 250,
                         "None": 225, "Superheavy": 200, "Heavy": 175, "Medium": 150, "Light": 125,
                         "Scout": 100, "Steel": 75, "Concrete": 50, "Wood": 25},
}
CHIP_SPREAD = {"Tesla": 200, "Laser": 200, "Railgun": 200}
# Tesla_Super has wider chip spread (was TeslaCharged 400).
CHIP_SPREAD_LEVEL = {("Tesla", "Super"): 400}
# Energy mains thinned to near single-target = 50% of the chip spread (the "low spread" the
# chip/utility compensates for). Prism has no chip -> nominal 100.
ENERGY_THIN_SPREAD = {f: s // 2 for f, s in CHIP_SPREAD.items()}
ENERGY_THIN_SPREAD["Prism"] = 100
ENERGY_THIN_SPREAD["Inferno"] = 100
ENERGY_THIN_SPREAD["Cryo"] = 100
# Level-specific thin-spread (same rule: half the chip spread).
ENERGY_THIN_SPREAD_LEVEL = {k: v // 2 for k, v in CHIP_SPREAD_LEVEL.items()}


def emit_chip(tag, family_name, damage, vt, level=None):
    """Emit the paid-for ExtraDamage chip (SpreadDamage, 50% of main, bespoke Versus).
    Uses CHIPS_LEVEL[(family, level)] if present, else CHIPS[family].
    For integrity-affecting families, the chip carries Tesla in DamageTypes so the passive
    INotifyDamage drain fires. SpreadDamage has no IntegrityScale field — the passive drain
    from the Tesla DamageType is the only mechanism for the chip."""
    d = CHIPS_LEVEL.get((family_name, level), CHIPS[family_name])
    floor = CHIP_FLOOR[family_name]
    spread = CHIP_SPREAD_LEVEL.get((family_name, level), CHIP_SPREAD[family_name])
    order = list(PLATING_CYCLE) + ["Shield", "None", "Flak", "Plate", "Heroic",
             "Scout", "Light", "Medium", "Heavy", "Superheavy",
             "Wood", "Steel", "Concrete", "Fighter", "Bomber", "Helicopter", "Spaceship"]
    # Through `emit_versus` so the chip obeys the same descending rule as the main and the
    # %-twin — the platings and Shield stay pinned at the front, the armors sort by value.
    # The platings come from `plating_rows`, not from the CHIPS table: the chip belongs to
    # the same family, and an armor plating cannot care which warhead of a weapon hit it.
    # The hand-set `REFLECTOR: 50` the Tesla chip used to carry was a second source for one
    # cell, which is the same trap that let Tesla's Shield be contested for months.
    overlays = dict(plating_rows(family_name))
    rows = emit_versus([(a, overlays.get(a, d.get(a, floor))) for a in order
                       if a not in PLATING_CYCLE or a in overlays])
    dt = "Prone75Percent, TriggerProne, ExplosionDeath"
    if family_name in FAMILY_INTEGRITY_SCALE:
        dt += ", Tesla"
    return "\n".join([
        f"\tWarhead@{tag}_ExtraDamage: SpreadDamage",
        f"\t\tValidTargets: {vt}",
        f"\t\tSpread: {spread}",
        f"\t\tDamage: {damage // 2}",
        f"\t\tFalloff: 100, 75, 50, 25",
        f"\t\tVersus:",
        rows,
        f"\t\tDamageTypes: {dt}"])


# THE VERSUS WINDOW (maintainer 2026-08-15, DESIGN.md §12.0) — every shipped Versus value
# sits in [10, 200], a 20:1 maximum span. Declared HERE, ahead of its own commentary further
# down, because the Shield damping below is derived from the window at import time and a
# module-level constant cannot be used before it is bound.
VERSUS_CEILING = 200
VERSUS_FLOOR = 10


# --------------------------------------------------------------------------- #
# Shield — a rock-paper-scissors axis, NOT a function of the profile's shape
# --------------------------------------------------------------------------- #
# Maintainer 2026-08-16: "shields have their own armor type so they feel unique. Energy
# weapons deal more damage to shields than physical weapons but physical weapons deal more
# damage to vehicle armor than energy weapons."
#
# The OLD law was `Shield = top + floor`, written when every profile peaked at exactly 100,
# so it produced the ceiling + floor (110/125/140). W13 renormalised to median-100, "top"
# became a function of each family's SHARPNESS, and the rule silently started rewarding
# sharpness instead of anti-shield design — Melee read 200 while Tesla read 151. A sword
# out-damaged a Tesla coil against an energy shield.
#
# ⚠ MEASURED (see SHIELD_AND_NORMALISATION_PLAN.md §5b): NO structural formula can carry the
# identity. `floor` and `top` are ANTI-CORRELATED by construction — a normalised profile that
# is sharp necessarily has a low floor and a high top, and a flat one the reverse — so any
# product of them cancels out to an invariant of the normalisation rather than a property of
# the weapon (`200+floor` spans just 1.26x, the geometric mean 1.54x, both with >50% ties).
#
# So the structural term sets the SCALE and the physics rank sets the ORDER:
#
#     Shield = PHYSICS_RANK[family] x SHIELD_LEVEL[level] x sqrt((200+floor)(100+top)) x K
#
# K is calibrated so `Tesla_Super` lands on exactly 400 — the value Tesla carried before its
# anti-shield `ExtraDamage` chip was merged into the main warhead by the AreaDamage
# conversion, which is what deleted the identity's carrier in the first place.
#
# ⚠ Shield is exempt from the [10,200] window in BOTH directions now. It used to be "the one
# value always ABOVE the cap" because shields were assumed uniformly soft; under the ruling
# above they are soft to ENERGY and HARD to kinetics, so physical families land below 100
# (Melee 76 — a blade is the canonical thing a shield stops). The old invariant was a
# consequence of the old assumption, not a law in its own right.
PHYSICS_RANK = {
    # direct electrical / EM — current couples straight into the field; the shield IS the conductor
    "Tesla": 1.00, "Storm": 0.95,
    # coherent energy — delivers energy the emitter must absorb; scales with coherence
    "Quantum": 0.82, "Railgun": 0.78, "Prism": 0.76, "Cryo": 0.75,
    # Cryo = Laser×Prism coldray: coherent energy with freeze-kinetic. 0.75 sits between its parents.
    "Laser": 0.74,
    # blended energy — part field-coupling, part thermal
    "Waveforce": 0.70, "Plasma": 0.68,
    # exotic / field-adjacent
    "Sonic": 0.60, "Magic": 0.58, "Inferno": 0.57, "Nuclear": 0.56, "MissileQuantum": 0.57, "MissileTesla": 0.66, "CannonTesla": 0.66,
    # Inferno = Flame×Prism heatray: thermo-led but still some field-coupling.
    # thermal / chemical — a shield stops heat and reagents well; little field coupling
    "CannonFire": 0.52, "MissileFire": 0.52, "Flame": 0.50, "CannonChem": 0.50, "CannonNuke": 0.45, "MissileNuke": 0.44,
    "MissileChem": 0.50, "Chemical": 0.48, "Toxic": 0.46, "Thermobaric": 0.44, "MissileThermobaric": 0.39,
    # kinetic / explosive — momentum is exactly what a shield is designed for
    "Flak": 0.38, "Concussion": 0.36, "Demolition": 0.35, "Bullet": 0.34,
    "MissileAA": 0.34, "CannonHE": 0.33, "MissileHE": 0.33, "CannonAP": 0.32,
    "MissileAP": 0.32, "Sniper": 0.30,
    # Bullet blends (maintainer 2026-08-22): the mean of their parents, same as every other
    # blend in this table. A bullet couples to a shield poorly (0.34), so each blend lands just
    # above Bullet by however much its payload couples.
    "BulletFire": 0.42, "BulletThermobaric": 0.39, "BulletHE": 0.35, "BulletTesla": 0.67,
    # physical contact — the canonical thing a shield stops
    "Arrow": 0.24, "Melee": 0.22,
}
# A shield is an ENERGY BUDGET, so a bigger discharge depletes proportionally more of it.
SHIELD_LEVEL = {"Trace": 0.80, "Light": 0.90, "Medium": 1.00, "Heavy": 1.12, "Super": 1.25}
SHIELD_DEFAULT_RANK = 0.40  # unlisted family: mid-kinetic, so a new family is never silently strong
SHIELD_FLOOR_TARGET = 100   # maintainer 2026-08-16: floor 100, ceiling 400, exactly 4.00x
SHIELD_CEIL_TARGET = 400

# --------------------------------------------------------------------------- #
# DAMPING the structural term (W25 S1, 2026-08-16)
# --------------------------------------------------------------------------- #
# §5b promised the structural term would "anchor the band without fighting the physics rank
# for control of the ordering". Post-S1 that was MEASURABLY FALSE at the very top: the scale
# swings 1.198x across the set while `Tesla -> Storm` is only a 1.053x rank gap, so
# `Storm_Super` (rank 0.95) overtook `Tesla_Super` (1.00) — 425.3 against 420.5. It did the
# same at Heavy and Medium. That inverts the maintainer's anchor law ("the only thing that
# should deal extreme damage to shields is tesla") through a term that was only ever meant
# to set the band.
#
# So the term is DAMPED to the one job §5b actually left it: separating families whose
# physics rank is EQUAL (`CannonChem`/`MissileChem` both 0.50, `CannonHE`/`MissileHE` both
# 0.33). The exponent is derived, not chosen — it is exactly the largest damping under which
# the SMALLEST genuine rank gap still wins:
#
#     damp = ln(smallest distinct rank ratio) / ln(the scale term's own swing)
#
# Both inputs come from things that do not move when profiles do: `PHYSICS_RANK` is a design
# table, and the swing is bounded by the WINDOW — with the mean pinned at 100 the profile's
# floor cannot exceed 100 and its top cannot exceed 200, so
# `sqrt((200+floor)(100+top))` lives in `sqrt(210x200) .. sqrt(300x300)` = 204.9 .. 300.0.
# Using the window bound rather than the measured spread slightly OVER-damps, which is the
# safe direction: it can only make a real rank gap more decisive, never less.
_SCALE_LO = math.sqrt((VERSUS_CEILING + VERSUS_FLOOR) * (100 + 100))
_SCALE_HI = math.sqrt((VERSUS_CEILING + 100) * (100 + VERSUS_CEILING))
SHIELD_SCALE_CENTRE = math.sqrt(_SCALE_LO * _SCALE_HI)
_RANKS = sorted(set(PHYSICS_RANK.values()))
SHIELD_SCALE_DAMP = (math.log(min(b / a for a, b in zip(_RANKS, _RANKS[1:])))
                     / math.log(_SCALE_HI / _SCALE_LO))

# Phase 1 emits Shield in CENTI-UNITS (x100) because the final value is not knowable here.
# The compression to [100, 400] is a property of the whole SET, so it belongs to phase 2
# (`shield_uniqueness.apply`) — and moving it there is what retires the three hand-calibrated
# constants (`SHIELD_GEOMEAN`/`ALPHA`/`ANCHOR`) that this very step would have invalidated.
# They were correct for the pre-S1 profiles and silently wrong the moment those moved, which
# is a hazard no comment can fix; derived-every-run cannot go stale at all.
#
# The x100 is not cosmetic: after damping, two equal-rank families differ by ~1%, which at a
# raw value of 50 rounds to the SAME integer and would lose the separation the damping exists
# to preserve. Centi-units keep it. Phase 2 is therefore MANDATORY — it asserts it converted
# every block, so a missed one fails loudly instead of shipping a Shield of 4900.
SHIELD_RAW_SCALE = 100


def shield_for(family, level, rows):
    """RAW Shield (centi-units) for a finished profile — phase 2 sets the final value.

    Applied LAST, overriding every other path. Both the measured path (`reference_main`)
    and the designed path (`table`) used to compute their own Shield, so two rules
    contested one cell and the measured one won — which is why Tesla's hand-set 300/400
    never took effect. This is now the single source.
    """
    vals = [v for a, v in rows if a not in NON_ARMOR_ROWS]
    if not vals:
        return None
    scale = math.sqrt((VERSUS_CEILING + min(vals)) * (100 + max(vals)))
    damped = SHIELD_SCALE_CENTRE * (scale / SHIELD_SCALE_CENTRE) ** SHIELD_SCALE_DAMP
    rank = PHYSICS_RANK.get(family, SHIELD_DEFAULT_RANK)
    return max(1, round(rank * SHIELD_LEVEL.get(level, 1.0) * damped * SHIELD_RAW_SCALE))


# --------------------------------------------------------------------------- #
# HAZMAT and REFLECTOR — the two OVERLAY armors (maintainer, 2026-08-16)
# --------------------------------------------------------------------------- #
# *"reflector armor is basically the same as HAZMAT but for energy weapons ... why is it
#  missing from the waveforce when it is combining plasma and quantum which is an energy
#  weapon? the values need to somehow reflect that"*
#
# These are not ladder rungs. They are CONDITIONAL overlay armors granted by upgrades —
# `Armor@HAZMAT` (hazmat suits, Soviet reactive armor: 329 actors) and `Armor@REFLECTOR`
# (Allied reflective plating: 16 actors) — carried IN ADDITION to the actor's real armor.
#
# ⚠ **THE ARITHMETIC CHANGED UNDER W21 AND THE VALUES DID NOT.** When armor types
# MULTIPLIED, a row of 50 meant exactly "halve the incoming damage", independent of the
# target. They now AVERAGE, so the same 50 gives
#
#     effective = (base + 50) / 2   ->   at base 100, that is 75, a 25% cut, NOT 50%.
#
# **Averaging silently halved every overlay's effect.** And it caps the mechanic: with one
# overlay the best possible is `(base + 10) / 2`, i.e. ~45% — no row value can ever reach
# the old 50%, because that would need a row of 0, which is immunity.
#
# So the row is solved from the REDUCTION it should produce rather than written directly:
#
#     effective = (100 + x) / 2 = 100 - R x 100      ->      x = 100 - 200 R
#
# The reference base of 100 is not an assumption — W25 S1 pinned every family's Versus MEAN
# to exactly 100, so 100 IS the average armor row a weapon writes. That is the second thing
# S1 bought: overlay armors became solvable.
#
# With `OVERLAY_DEPTH = 0.45` (the ceiling above), `x = 100 - 90 x share`. A share of 1.0
# lands on the window floor of 10 and reproduces the old multiplicative feel as closely as
# averaging permits; a share of 0 OMITS the row.
#
# ⚠ **OMITTING IS NOT THE SAME AS WRITING 100.** Both the engine and Cameo's override filter
# on `Versus.ContainsKey(armorType)`, so an absent row drops the overlay OUT of the average
# entirely, while `100` pulls the result toward 100. Omission is the only way to say "this
# weapon does not care about the plating", and it is what a zero share must produce.
# --------------------------------------------------------------------------- #
# THE FIVE ARMOR PLATINGS (maintainer, 2026-08-16)
# --------------------------------------------------------------------------- #
# *"Hazmat against fire, chemical and radiation, BLAST against all the HE weapons,
#  reflector against energy, composite against AP weapons and bullets ... they are all good
#  against a certain family but bad against another and medium against everything else ...
#  also they will average on 100% each across all weapon types ... and we need to make sure
#  that every weapon family has an armor counter and every armor type has a weapon counter"*
#
# ⚠ **These get a row in EVERY template, exactly like `Shield`.** That is what makes LAYER
# SELECTION safe: the plating replaces the class armor while it is on, and a sparse row set
# would leave the armor list empty for the weapon classes it does not counter — which both
# the engine and `AreaDamageWarhead.DamageVersus` answer with 100, i.e. a superheavy tank
# taking full damage from bullets. Full columns, no gaps.
#
# ⚠ **A plating is a TRADE, not an upgrade.** Being WEAK against something is the design, so
# the "an upgrade must never increase damage" invariant does NOT apply to these the way it
# applied to the old additive overlays — it is superseded by the column law below. What makes
# that safe is selection: only one row is ever read, so a weak row is a chosen exposure
# rather than a penalty stacked on top of the class armor.
#
# THE COLUMN LAW: every plating's mean across all templates is the SAME, so no plating is
# stronger overall — they differ only in WHAT they are strong against. This is the transpose
# of W25 S1 (which pins each WEAPON's mean across armors) and the two cannot conflict:
# platings live in NON_ARMOR_ROWS, so they never entered S1's row mean, and S1's armors never
# enter this column mean.
#
# ⚠ **The common mean is 70, NOT 100, and the difference is a measured bug fix.** A plating
# REPLACES the class armor, so what matters is how its column compares to the one it
# displaces — and six of the sixteen class armors already average better than 100 (`Heroic`
# 74.3, the four aircraft 76-80). At a mean of 100 a hero or an aircraft that took a plating
# got 25-35% WORSE, and `td_gdi_upgrade_heavyaircraftarmorplating` is live. That is the same
# failure as the old averaging bug arriving by a different route: not stacking badly, but
# DISPLACING SOMETHING BETTER. 70 sits just under `Heroic`'s 74.3, so a plating is a genuine
# upgrade for every armor it can replace. The maintainer's law is untouched — its purpose was
# that platings be equal to EACH OTHER, which any common mean satisfies. The ~30% durability
# this grants must then be PRICED (see E1); it is not free, it is merely not yet charged for.
PLATING_TARGET_MEAN = 70.0
#
# NAMING: every plating is ALL CAPS (maintainer, 2026-08-16) — the class armors are
# TitleCase (`None`, `Superheavy`, `Concrete`), so the case alone tells a reader which LAYER
# a Versus row belongs to without having to remember the taxonomy. Each name is the most
# recognisable real term for its role rather than a coined one:
#
#   HAZMAT     the sealed / filtered suit — already an all-caps acronym in the real world
#   COMPOSITE  Chobham-type ceramic matrix, the standard word for modern armour
#   BLAST      names the threat, as HAZMAT does; `SPALL` (the liner) was the alternative and
#              is more precise but less legible — this is a one-word revert either way
#   REFLECTOR  the mirrored / ablative coating
#
# THE CYCLE: FOUR platings over the roster's four real damage axes, each countering one and
# weak to the next — `thermo -> kinetic -> blast -> energy -> thermo`. Every step is a defeat
# mechanism, not flavour:
#
#   HAZMAT     counters thermochemical  weak to KINETIC  a seal has no mass; a bullet passes
#                                                        through a rubber suit
#   COMPOSITE  counters kinetic+SHAPED  weak to BLAST    ceramic shatters a penetrator and ERA
#                                                        breaks a jet — a real tank carries
#                                                        both — but neither spreads an impulse
#   BLAST      counters blast           weak to ENERGY   a liner absorbs mechanical impulse,
#                                                        and a beam delivers none
#   REFLECTOR  counters energy          weak to THERMO   flame and corrosives foul the surface,
#                                                        and a dull mirror is just thin plate
#
# ⚠ **`Reactive` was cut on the measurement, not on taste** (§H2). Composition share across
# all 33 families: thermochemical 27.4%, kinetic 23.4%, blast 22.7%, energy 20.1% — and
# shaped charge **6.4%**, with only `MissileAP` shaped-led. It failed the maintainer's own
# niche test, the one that already retired `Insulated`, `Damping` and `Warding`. The `shaped`
# AXIS survives as an honest description of what those warheads are; it is simply counted
# under `COMPOSITE`, which is how a real tank is built anyway.
#
# A four-cycle is not degenerate: each plating is weak to what the NEXT one counters, so it is
# one 4-cycle rather than two mirrored 2-cycles. (An earlier note claimed only an ODD cycle
# could avoid that collapse — wrong; what matters is that no two platings counter each other's
# weakness.)
PLATING_AXES = ("thermo", "kinetic", "shaped", "blast", "energy")
PLATING_CYCLE = {                  # plating: (axes it counters, axes it is weak to)
    "HAZMAT":          (("thermo",),            ("kinetic", "shaped")),
    "COMPOSITE":       (("kinetic", "shaped"),  ("blast",)),
    "BLAST":           (("blast",),             ("energy",)),
    "REFLECTOR":       (("energy",),            ("thermo",)),
    # --- THE GENERIC PLATING (maintainer, 2026-08-17) --------------------------------- #
    # *"there should also be a generic ARMOR armor type called ARMOR that receives 100%
    #  damage from everything. This is for the things like Scrap or Junkarmor and the
    #  StarCraft and Warcraft armor upgrades. So in a way this could be our fifth armor
    #  type."*
    #
    # It counters nothing and is weak to nothing, so `plating_raw` returns a FLAT 100 for
    # every family — "100% damage from everything", exactly as stated — and the column law
    # then scales that flat row to the common mean like any other plating. No special case
    # is needed anywhere: the empty tuples ARE the definition.
    #
    # It is the fifth plating the roster CAN support, and it sidesteps §H2 entirely: it is
    # not a fifth damage AXIS (which the measurement showed cannot be even) but a fifth
    # CHOICE with no axis at all. So the four-way partition stays exactly as even as it was.
    #
    # In play it is the HEDGE: identical average durability to the four specialists, but
    # flat, so it is never punished for guessing wrong. Against a known opponent a specialist
    # beats it; against an unknown one it does not. That is a real decision rather than a
    # filler option — and it is the honest home for every generic "+armor" upgrade
    # (Yuri scrap, Forgotten junk armor, the StarCraft/Warcraft armor and carapace levels),
    # which have no business carrying a counter-play identity they were never designed with.
    "ARMOR":           ((), ()),
}
# How much a full share moves the row away from the mean — so a pure-thermo weapon reads half
# against HAZMAT and half again as much against REFLECTOR, before the column is normalised.
PLATING_DEPTH = 0.50

# Each PRIMITIVE family's damage composition over the five axes; shares sum to 1. Blends
# average their parents, so a new blend is classified for free. This is the same kind of
# design table as PHYSICS_RANK — measured against nothing, argued from what the weapon IS.
#
# ⚠ EVERY EMITTED FAMILY'S ROW MUST BE UNIQUE (maintainer, 2026-08-17: *"I want all weapon
# families to be a bit more unique so don't put 3 energy weapons exactly on the same versus
# value"*), and the ONLY way a family can earn a distinct row is to move mass ACROSS a group
# boundary. The cycle reads `kinetic` and `shaped` as one SET, so five axes give exactly FOUR
# distinguishable groups — {thermo} / {kinetic+shaped} / {blast} / {energy} — and refining
# WITHIN one group is arithmetically INERT: `Bullet` 0.90/0.10 against `Arrow` 0.65/0.35 was
# measured as BYTE-IDENTICAL. So every secondary share below names a SECOND real defeat
# mechanism; none is a fudge to break a tie, because a fabricated difference is a lie about the
# model (`b182fd228`). `tools/tests/test_plating_composition.py` pins the uniqueness, and
# `docs/design/ARMOR_LAYERS.md` argues every line one at a time.
COMPOSITION = {
    # --- KINETIC: a solid mass arrives at speed. Defeated by hard, brittle ceramic that
    # shatters or erodes the penetrator before it reaches the backing plate — which is what
    # composite (Chobham-type) armour IS.
    #
    # These four were all `kinetic 1.00`, i.e. one four-way tie. They are separated by what
    # happens BEHIND the plate, which is the only honest non-kinetic share a solid projectile
    # has: a penetration event throws SPALL, and a spall liner (`BLAST`) is the real answer to
    # it — that is what spall liners are FOR. So the share tracks how violent the event is.
    "Arrow":       {"kinetic": 1.00},                   # the pure point: no spall, no flash
    "Sniper":      {"kinetic": 0.95, "blast": 0.05},    # one round, one channel, little spall
    "Bullet":      {"kinetic": 0.90, "blast": 0.10},    # deforms, cavitates, sprays spall
    # A blade is a slow sharp penetrator, but this family also covers the swung mass, and blunt
    # trauma is the one melee mechanism rigid armour cannot simply stop: a mace transmits SHOCK
    # THROUGH the plate instead of trying to pass through it, which is overpressure behaviour.
    # Hence composite helps LESS against melee than against a rifle, and padding helps more.
    "Melee":       {"kinetic": 0.75, "blast": 0.25},
    "Railgun":     {"kinetic": 0.85, "energy": 0.15},   # a SLUG; the energy is in the launcher
    # APFSDS, the canonical KE dart — and a dart is PYROPHORIC (depleted uranium ignites) with
    # adiabatic heating at the contact point, so the documented behind-armour effect is
    # incendiary as much as mechanical. That thermal share is what separates it from a bullet.
    "CannonAP":    {"kinetic": 0.70, "shaped": 0.15, "thermo": 0.15},
    # Fragments are METAL MOVING FAST, not overpressure — which is exactly why "flak jacket"
    # is a real garment and why fragmentation sleeves are rated in kinetic terms. Both of
    # these were blast-led in the first draft, which credited them to the wrong counter.
    "Flak":        {"kinetic": 0.60, "blast": 0.40},
    "MissileAA":   {"kinetic": 0.55, "blast": 0.45},    # continuous-rod / frag warheads
    # --- SHAPED CHARGE: a metal JET formed by an explosive-driven liner, defeated by making
    # the jet form early or wander — ERA, slat, spaced plate. Nothing about mass or hardness.
    "MissileAP":   {"shaped": 0.85, "blast": 0.10, "thermo": 0.05},   # HEAT/ATGM + BAI
    "MissileHE":   {"blast": 0.75, "shaped": 0.25},
    # --- BLAST: overpressure and shock through the structure, defeated by absorbing and
    # spreading impulse — spall liners, V-hulls, standoff.
    "CannonHE":    {"blast": 0.90, "kinetic": 0.10},
    # `Demolition` and `Concussion` were both `blast 1.00`. A concussion shell is the pure
    # overpressure archetype; a demolition charge is placed in contact and its detonation
    # delivers a real thermal flash (that is what an incendiary cutting charge exploits), so a
    # sealed suit gives a little protection against one and none against the other.
    "Concussion":  {"blast": 1.00},
    "Demolition":  {"blast": 0.85, "thermo": 0.15},
    "Sonic":       {"blast": 0.70, "energy": 0.30},     # a pressure wave IS overpressure
    "Thermobaric": {"blast": 0.60, "thermo": 0.40},     # fuel-air: overpressure + burn
    # --- THERMOCHEMICAL: agents and thermal load, defeated by SEALING and insulating.
    #
    # `Flame`/`Chemical`/`Toxic`/`Cryo` were a four-way tie at `thermo 1.00`. A sealed insulated
    # suit really is the right counter to all four, so they keep a thermo LEAD and separate on
    # their second mechanism:
    "Toxic":       {"thermo": 1.00},                    # an agent vs the CREW: the pure case
    "Flame":       {"thermo": 0.85, "blast": 0.15},     # fuel DEFLAGRATES: pressure + O2 loss
    # Chemical is CORROSION, not gas (`PHYSICAL_STATE_SYSTEM.md`) — a reaction that eats a
    # channel through the material itself, which is localised material removal. Ceramics are
    # chemically INERT where steel and reactive armour are not, so `COMPOSITE` earns a real
    # (partial) answer to it and that is what separates it from flame.
    "Chemical":    {"thermo": 0.75, "shaped": 0.25},
    # Cryo is a Laser×Prism coldray: coherent energy delivery that freezes, so the shield
    # sees mostly field coupling (energy). The thermal load is still real (insulation stops it),
    # and the kill has a small kinetic share from cryogenic embrittlement of frozen material.
    "Cryo":        {"energy": 0.55, "thermo": 0.25, "kinetic": 0.20},   # Laser×Prism coldray: energy-led with embrittlement
    "Nuclear":     {"thermo": 0.50, "blast": 0.40, "energy": 0.10},
    # --- ENERGY: radiated or conducted, defeated by REFLECTING or ablating it away.
    #
    # `Laser`/`Prism`/`Tesla` were a three-way tie at `energy 1.00`, so one REFLECTOR row
    # answered all three identically. They separate on how much of the delivered damage is
    # THERMAL, which is also the order in which a mirrored coating stops being the right idea:
    "Prism":       {"energy": 0.90, "thermo": 0.10},    # focused visible light: purest radiant
    # Maintainer 2026-08-17: *"the tesla is the opposite [of Inferno]: it's mostly energy and a
    # bit of thermal"*. A conducted arc is the field-coupling champion (PHYSICS_RANK 1.00); what
    # it delivers to MATTER is resistive heating (the thermo share) plus the arc channel's
    # thunderclap — thunder is literally an overpressure wave, which is the blast share. And a
    # mirrored plating is a METAL skin, so it spreads and grounds an arc rather than reflecting
    # it: same benefit, different mechanism, which is why REFLECTOR still helps here.
    "Tesla":       {"energy": 0.75, "thermo": 0.20, "blast": 0.05},
    "Storm":       {"energy": 0.80, "thermo": 0.10, "blast": 0.10},   # lightning: fires+thunder
    "Laser":       {"energy": 0.65, "thermo": 0.35},    # coherent IR, but the KILL is ablation
    "Magic":       {"energy": 0.60, "thermo": 0.20, "blast": 0.20},
}
# Where a blend's parent list understates what the weapon physically IS.
COMPOSITION_OVERRIDE = {
    # Flame + Chemical gives Plasma a pure thermo reading, but plasma is ionised and radiates.
    "Plasma": {"thermo": 0.55, "energy": 0.45},
    # Inferno is a Flame×Prism heatray: thermo-led, but delivered as a coherent beam so both
    # HAZMAT (sealed/insulated) and REFLECTOR (mirror) reduce it, with HAZMAT doing more.
    "Inferno": {"thermo": 0.65, "energy": 0.35},   # Flame×Prism heatray: thermo-led with field coupling
}

# The PHYSICS_RANK band boundary, read OFF that table rather than chosen: everything at or below
# 0.52 sits in its "thermal / chemical" band and everything at or above 0.56 is at least
# "exotic / field-adjacent".
ENERGY_COUPLING_RANK = 0.56


def rank_composition_conflicts():
    """Families whose PHYSICS_RANK band and COMPOSITION disagree about field coupling.

    ⚠ **This REPLACES `_rank_blend`**, which derived Inferno's thermo/energy split from its rank
    arithmetically. That over-reached: the two tables answer DIFFERENT questions — rank asks how
    much of a discharge a FORCE FIELD absorbs, composition asks what reaches MATTER — and
    `Railgun` has always been the standing proof that they are not one axis (rank 0.78, a nearly
    pure kinetic slug). Deriving one from the other therefore had to be overruled the moment a
    ruling touched either table, which is exactly what happened.

    So the guard keeps only the part the two tables genuinely share, and constrains no share: a
    family the shield table calls field-coupling must have SOME energy in it, and one it calls
    thermal/kinetic must have none. That catches precisely the drift that shipped TWICE — both
    `Inferno` (0.64) and `Cryo` (0.66) sat at `thermo 1.00` while being prism-chassis weapons.
    """
    bad = []
    for fam, rank in sorted(PHYSICS_RANK.items()):
        energy = composition(fam)["energy"]
        if rank >= ENERGY_COUPLING_RANK and energy <= 0:
            bad.append((fam, rank, energy, "ranked field-coupling, but no energy share"))
        elif rank < ENERGY_COUPLING_RANK and energy > 0 and fam not in BLEND_FAMILIES:
            # ⚠ The converse holds for PRIMITIVES only. A blend's rank is the MEAN of its
            # parents', so a mostly-ordnance blend can sit below the band boundary while still
            # carrying a real energy share from one parent — `PhotonCannon` (rank 0.46, one
            # third Waveforce) is the case that proved it. Applying the converse there would
            # forbid a legitimate family rather than catch drift, which is the opposite of what
            # this guard is for: the drift it exists to catch (`Inferno`, `Cryo`) was in the
            # PRIMITIVE table both times.
            bad.append((fam, rank, energy, "ranked thermal/kinetic, but has an energy share"))
    return bad


def composition(name):
    """A family's share over PLATING_AXES; blends average their parents."""
    if name in COMPOSITION_OVERRIDE:
        raw = COMPOSITION_OVERRIDE[name]
    elif name in COMPOSITION:
        raw = COMPOSITION[name]
    elif name in BLEND_FAMILIES:
        parents = BLEND_FAMILIES[name][0]
        raw = {}
        for p in parents:
            for axis, share in composition(p).items():
                raw[axis] = raw.get(axis, 0.0) + share / len(parents)
    else:
        raw = {}
    total = sum(raw.values())
    return {a: raw.get(a, 0.0) / total if total else 0.0 for a in PLATING_AXES}


def plating_raw(family):
    """Un-normalised row per plating: flat, minus what it counters, plus what beats it.

    Counter and weakness are SETS of axes, not single axes — `COMPOSITE` answers both
    kinetic penetrators and shaped-charge jets, so it sums both shares.
    """
    comp = composition(family)
    return {p: 100.0 * (1 - PLATING_DEPTH * sum(comp[a] for a in counters)
                        + PLATING_DEPTH * sum(comp[a] for a in weak))
            for p, (counters, weak) in PLATING_CYCLE.items()}


def _plating_scales():
    """Per-plating factor pinning each COLUMN's mean to 100 across every emitted template.

    Computed here rather than in a second phase because a plating value depends only on the
    FAMILY, and the set of templates the generator emits is fully determined by the tables
    above — so the column mean is knowable without generating anything.
    """
    families = []
    for nm, (_b, _d, _a, levels) in WEAPONS.items():
        if nm not in HAND_TUNED:
            families += [nm] * len(levels)
    for nm, (_p, _n, _s, levels) in INHERIT_FAMILIES.items():
        families += [nm] * len(levels)
    for nm, (_p, _s, levels) in BLEND_FAMILIES.items():
        families += [nm] * len(levels)
    families += ["Storm"] * len(STORM_LEVELS)
    scales = {}
    for p in PLATING_CYCLE:
        vals = [plating_raw(f)[p] for f in families]
        mean = sum(vals) / len(vals) if vals else 100.0
        scales[p] = PLATING_TARGET_MEAN / mean if mean else 1.0
    return scales


_PLATING_SCALES = None


def plating_rows(family):
    """`[(plating, value)]` — the five columns, each normalised to a mean of 100.

    The scales are computed once, on first use, because `_plating_scales` reads WEAPONS /
    BLEND_FAMILIES / STORM_LEVELS, which are defined further down this file.
    """
    global _PLATING_SCALES
    if _PLATING_SCALES is None:
        _PLATING_SCALES = _plating_scales()
    raw = plating_raw(family)
    return [(p, max(VERSUS_FLOOR, min(VERSUS_CEILING,
                                      round(raw[p] * _PLATING_SCALES[p]))))
            for p in PLATING_CYCLE]


# ⚠ The earlier two-axis overlay model (CHEM_SHARE / ENERGY_SHARE / OVERLAY_DEPTH, with
# a clamp keeping every row below the class floor) is SUPERSEDED by the five-plating
# matrix above. It solved the wrong problem: it treated a plating as an ADDITIVE overlay
# averaged into the class armor, so it had to guarantee the row could never make things
# worse. Under layer SELECTION only one row is ever read, and being weak against one axis
# is the whole design — so the clamp would have deleted the counter-play it was protecting.


def table(order16, step, top, floor, shield):
    rows = [("Shield", shield)]
    for i, a in enumerate(order16):
        rows.append((a, top - i * step))
    assert rows[-1][1] == floor, (rows[-1], floor)
    return rows


# --------------------------------------------------------------------------- #
# W13 — MEASURED Versus profiles (the reference corpus), replacing the even ramp
# --------------------------------------------------------------------------- #
# `table()` above is a LINEAR ladder: 100, 100-step, 100-2*step ... Equal steps
# were a generator artifact and produce exactly the "moderate middle" the warhead
# rebuild exists to escape (DESIGN.md §12.0 rule 3). Where the reference corpus
# measured a family at a platform tier, its profile is used INSTEAD — plateaus,
# cliffs and all — and `table()` remains the fallback for the families Cameo
# invented, which have no cross-mod equivalent to learn from.
#
# The data is FROZEN into a committed JSON rather than computed here on purpose:
# deriving it needs `tools/reference/survey_platforms.py`, which traces the source
# mods' INI files out of `~/Downloads`. Nobody else has those, so a generator that
# imported the derivation would only run on one machine. Regenerate the JSON with
#   python tools/reference/propose_family_profiles.py --json
# and the ORDER still comes from `build_order()` here — the corpus supplies
# magnitudes, the law supplies order (DESIGN.md §12.0).
# THE VERSUS WINDOW (maintainer, 2026-08-15, DESIGN.md §12.0): every shipped Versus
# value sits in [10, 200] — a 20:1 maximum span, which is the SAME extreme the old
# peak-100 law wrote as "100 against a floor of 5", re-expressed on the median-100
# scale. A legal maximum, not a target: the reference mods' own profiles span only
# 1.3x-7.2x, so anything beyond that is Cameo's design choice, not the field's.
# (`VERSUS_CEILING` / `VERSUS_FLOOR` are bound near the top of the file — see the note there.)
REFERENCE_JSON = (pathlib.Path(__file__).resolve().parents[2]
                  / "docs" / "reference" / "family_profiles.json")
# The families Cameo INVENTED, which have no cross-mod equivalent to measure. Kept in
# a separate file under docs/design/ rather than merged into the reference JSON, so
# the two provenances can never be confused: docs/reference/ is what the field said,
# docs/design/ is what we decided. Regenerate with
#   python tools/balance/design_invented_profiles.py --write
DESIGNED_JSON = (pathlib.Path(__file__).resolve().parents[2]
                 / "docs" / "design" / "invented_family_profiles.json")


def _load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))["families"]
    except (OSError, ValueError, KeyError):   # missing/damaged data must not break the generator
        return {}


REFERENCE_PROFILES = _load(REFERENCE_JSON)
DESIGNED_PROFILES = _load(DESIGNED_JSON)


def distinct_ints(rows):
    """No two values identical, on INTEGERS — the last step of the shape law.

    The frozen profiles are floats separated by at least 2, but `Versus` is an
    `int` dictionary in the engine (`DamageWarhead.Versus`), and rounding can
    re-create a tie the float profile had already separated. Walks DOWN from the
    peak, which is the direction with room: nudging up pins ties against the top
    and silently re-creates the duplicate (the bug that shipped Tesla with
    `Plate 100` AND `Superheavy 100`). `sorted` is stable, so armors that tie
    keep the order the ordering law gave them.
    """
    ranked = sorted(range(len(rows)), key=lambda i: -rows[i][1])
    fixed, previous = {}, None
    for i in ranked:
        armor, value = rows[i]
        if previous is not None and value >= previous:
            value = previous - 1
        fixed[armor] = value
        previous = value
    # THE VERSUS WINDOW (maintainer 2026-08-15): 10 <= Versus <= 200, a 20:1 span,
    # the same maximum specialisation the peak-100 law expressed as 100-against-5.
    # The descent above can breach the floor, so repair from the BOTTOM up: raise
    # only what fell through and leave the measured shape above it alone.
    if fixed and min(fixed.values()) < VERSUS_FLOOR:
        previous = None
        for i in reversed(ranked):
            armor = rows[i][0]
            lowest = VERSUS_FLOOR if previous is None else previous + 1
            fixed[armor] = min(max(fixed[armor], lowest), VERSUS_CEILING)
            previous = fixed[armor]
    return [(armor, fixed[armor]) for armor, _ in rows]


BAND_LOW = 2.0                      # DESIGN.md §12.0 rule 5 — the target band's flat end
BAND_MARGIN = 1.03                  # headroom so integer rounding cannot fall back out of band
DERIVED_ARMORS = ("Heroic", "Airborne")
# Rows that live on a Versus node but are not armor classes, so they never enter a
# profile statistic: the shield LAYER, the HAZMAT gate, Tesla's REFLECTOR.
NON_ARMOR_ROWS = ("Shield",) + tuple(PLATING_CYCLE)


# --------------------------------------------------------------------------- #
# W25 S1 — THE MEAN-100 LAW (maintainer, 2026-08-16)
# --------------------------------------------------------------------------- #
# *"all warheads average all versus values at 100 to make them comparable"*
#
# W13 normalised each profile to its MEDIAN. That left every family's MEAN free, and
# a family's mean is not a shape statistic — it is a MAGNITUDE. `K` is a share-weighted
# average of the profile, so the mean IS the family's contribution to priced DPS, and
# picking a family silently changed a weapon's total output as well as its shape.
# Measured across the 94 shipped templates before this change: means ran 22.0
# (`Magic_Light`) to 106.1 (`MissileAA_Light`), averaging 75.0 — i.e. up to a 4.8x
# hidden multiplier between two families that both looked "normalised".
#
# Pinning the mean at 100 makes:
#   * `K` SHAPE-ONLY — choosing a family redistributes output across armors without
#     changing how much of it there is;
#   * `Damage` the sole magnitude knob, which is what the balance pipeline wants;
#   * families directly comparable, which is the maintainer's stated goal.
#
# The mean is UNWEIGHTED over the 16 armor rows, deliberately. A share-weighted mean
# would be a better predictor of realised DPS, but it would make a profile's legality
# depend on the current unit roster — every roster change would silently move every
# template. Uniform weighting is a property of the profile alone.
#
# ⚠ **The window makes this a constraint, not just a rescale.** With the mean pinned at
# 100, `max <= 200` becomes `max <= 2 x mean`: a profile that is brilliant against three
# armors and useless against thirteen CANNOT keep its peak, because thirteen low values
# drag the mean down. Measured: 11 of 94 templates breach the ceiling under a plain
# rescale, worst `Melee_Medium` at 316 (median 35.5 against a peak of 174 — the extreme
# bottom-heavy profile). Those 11 are brought back by the POWER LAW about the geometric
# mean, `v' = G x (v/G) ** alpha`, never by clamping. Three reasons it is the right
# instrument, the third specific to this step:
#
#   1. it is monotone, so the ordering law's sequence survives untouched;
#   2. it preserves the geometric mean, the correct centre for a set of MULTIPLIERS;
#   3. **it preserves the derived-armor relation exactly.** §12.0b sets
#      `Heroic = Plate x Scout / peak`, and the power law satisfies
#      `G(P/G)^a x G(S/G)^a / G(peak/G)^a == G(H/G)^a` identically — so Heroic stays
#      derived without being recomputed. A clamp or an affine squeeze breaks that.
#
# The cost is real and is reported by `report_versus_change.py`: the 11 compressed
# templates lose sharpness (Melee 6.69x -> 2.86x, Arrow 4.71x -> 3.01x; the other eight
# move by less than 1.0x). Median spread across all 94 barely moves, 3.06x -> 3.00x, so
# the field band (2/4/8) still holds. If the maintainer wants Melee's skew back, the
# lever is the CEILING, not this function — under mean-100 a peak of 2x the average is
# arithmetic, not policy.
#
# ⚠ **Scope: the MAIN warhead only.** `PercentageVersus` encodes the percentage half's
# armor profile while `PercentageScale` derives its magnitude from main Damage, so
# normalising those rows would multiply every percentage effect by ~5x.
MEAN_TARGET = 100.0


# --------------------------------------------------------------------------- #
# W25 S2 — THE CLASS TILT (maintainer, 2026-08-16)
# --------------------------------------------------------------------------- #
# *"light weapons have a bigger damage to light armor types while heavy weapons have a
#  bigger damage to heavy armor types with medium weapons having bigger damage to medium
#  armor types ... all inside their own family (compared for example light, medium and
#  heavy flame weapons) ... and super just deals a more flat damage to everything so it's
#  overall good (but still doesn't have the same values, just a more flat curve)"*
#
# With the mean pinned at 100 by S1, a tilt is FREE: it costs nothing in total output, it
# only moves where the output lands. That is what makes this expressible at all.
#
# The maintainer wrote the tilt as three armor SETS (SHIELD_AND_NORMALISATION_PLAN §6c):
#
#     Light  -> None · Wood · Scout · Light · Fighter
#     Medium -> Flak · Steel · Medium · Bomber · Helicopter
#     Heavy  -> Plate · Concrete · Heavy · Superheavy · Spaceship
#
# Implemented as ladder POSITION rather than as a hard-coded set, because position is what
# those sets ARE: the lightest rung of every ladder, the middle rung of every ladder, the
# heaviest rung of every ladder. Reading them off `LADDERS` reproduces all three sets
# exactly and keeps working if a ladder ever gains a rung, where a literal set would
# silently leave the new armor untilted.
#
# ⚠ **THE TILT MUST NEVER REORDER A LADDER.** The two-level ordering law (maintainer
# 2026-08-01, "the most important part") fixes which armor in a ladder takes the biggest
# value, and a Heavy-level tilt on an anti-LIGHT family pushes exactly the wrong way — left
# alone it would invert `None > Flak > Plate` and make a rifle best against plate. So the
# tilt is applied to the VALUES, and then each armor is given back the RANK it held before:
#
#   * where the tilt agrees with the family's direction it SHARPENS the ladder;
#   * where it disagrees it FLATTENS it;
#   * it can never invert it, and it needs no `direction` argument — the profile's own
#     order is the authority, which is what makes this work for the blends too (they have
#     no `build_order` at all, their shape comes from averaging their parents).
#
# The relative statement the maintainer asked for survives intact: `Scout` takes a larger
# share of Flame_Light's output than of Flame_Heavy's, and `Superheavy` the reverse.
#
# `TILT_RATIO` is the weight span across a ladder, so 1.5 means the favoured end is pulled
# 1.5x harder than the disfavoured end BEFORE renormalisation. Chosen to stay inside the
# measured field band (2/4/8) after the sharpening it causes — see the audit below.
TILT_RATIO = 1.5
# Super is not merely untilted, it is actively FLATTENED to the band's flat end: it is the
# generalist, so it should have the shallowest curve of any level. Never to EQUAL values —
# the no-ties law still binds; "flat" here means "lowest spread", not "uniform".
SUPER_RATIO = BAND_LOW


def tilt_exponent(level, pos, n):
    """Where position `pos` of `n` sits in this level's favour, in [-0.5, +0.5].

    All three tilts share one range, so `TILT_RATIO` means the same thing at every level.
    `Trace` is the sub-Light tier and tilts with Light.
    """
    if n <= 1:
        return 0.0
    t = pos / (n - 1)
    if level in ("Light", "Trace"):
        return 0.5 - t                       # favours the lightest rung
    if level == "Medium":
        return 0.5 - 2 * abs(t - 0.5)        # favours the middle rungs
    if level == "Heavy":
        return t - 0.5                       # favours the heaviest rung
    return 0.0                               # Super: no tilt, flattened instead


def class_tilt(rows, level):
    """Apply the level's class tilt to a MAIN profile, preserving every ladder's order."""
    vals = dict(rows)
    live = [v for a, v in rows if a not in NON_ARMOR_ROWS]
    if not live or max(live) <= min(live):
        return rows          # Sonic / Magic are flat BY DESIGN; a tilt would destroy that
    out = dict(vals)
    for ladder in LADDERS.values():
        # Derived armors are excluded: `Heroic` is a PRODUCT of two other cells (§12.0b),
        # so it has to be recomputed from the finished profile rather than tilted like an
        # independent rung. That is also why §6c assigns it to no tier.
        rungs = [a for a in ladder if a in vals and a not in DERIVED_ARMORS]
        if len(rungs) < 2:
            continue
        n = len(rungs)
        tilted = [vals[a] * TILT_RATIO ** tilt_exponent(level, i, n)
                  for i, a in enumerate(rungs)]
        # Give each armor back the rank it held BEFORE the tilt (see the warning above).
        # `-vals[a]` ranks descending; the index breaks ties stably, so a ladder that
        # already had two equal values keeps the ordering law's sequence between them.
        order = sorted(range(n), key=lambda i: (-vals[rungs[i]], i))
        for slot, i in enumerate(order):
            out[rungs[i]] = sorted(tilted, reverse=True)[slot]
    if level == "Super":
        # The generalist: compress toward the band's flat end about the geometric mean.
        body = [v for a, v in out.items() if a not in NON_ARMOR_ROWS and v > 0]
        lo, hi = min(body), max(body)
        if lo > 0 and hi / lo > SUPER_RATIO:
            g = statistics.geometric_mean(body)
            alpha = math.log(SUPER_RATIO) / math.log(hi / lo)
            out = {a: (v if a in NON_ARMOR_ROWS else g * (max(v, 1.0) / g) ** alpha)
                   for a, v in out.items()}
    # Re-derive the products LAST, from the finished profile (§12.0b) — a derived value
    # computed before the last cell moves is not derived, it is stale.
    peak = max(v for a, v in out.items()
               if a not in NON_ARMOR_ROWS and a not in DERIVED_ARMORS)
    for name, (first, second) in (("Heroic", ("Plate", "Scout")),
                                  ("Airborne", ("Helicopter", "Scout"))):
        if name in out and first in out and second in out and peak > 0:
            out[name] = out[first] * out[second] / peak
    return [(a, out[a]) for a, _ in rows]


# --------------------------------------------------------------------------- #
# §12.0i — THE CONTINUOUS-HEAVINESS BELL (maintainer 2026-08-23/24)
# --------------------------------------------------------------------------- #
# The continuous successor to `class_tilt` above. DESIGN §12.0i is binding and holds the
# derivation; this is the implementation, and it is OFF until the maintainer authorises the
# regeneration (rule 4 — a warhead's Versus may not change without explicit permission).
#
#     x(armor)      = ONE GLOBAL 13-slot scale, 0..2, step 1/6
#     mu(family, h) = ( h + centre_of_mass(base_profile) ) / 2
#     curve(x)      = BELL_LO + (1 - BELL_LO) * exp( -(x - mu)^2 / (2 * BELL_SIGMA^2) )
#     out(a)        = base(a) * curve(x(a))   then renormalised, then RANK-RESTORED per ladder
#
# ⭐ EVERY LADDER IS CENTRED EXACTLY ON 1.000 — VEH width 2.000, INF 1.667, AIR 1.333,
# BLD 0.667 — so h = 0 / 1 / 2 is the lightest / middle / heaviest rung of every ladder at
# once, which is what makes this a drop-in successor to `tilt_exponent`'s ramp/tent.
#
# ⛔ THE THREE-WAY TIE AT 1.0 IS DELIBERATE AND IS THE ONLY TIE. Flak, Medium and Steel sit
# in three DIFFERENT ladders, and the rank restore is per-ladder, so they are never in
# competition: de-tying them moves no row by more than 0.89%. A tie WITHIN one ladder stays
# forbidden — that was the retired bucket axis, where Bomber and Helicopter shared a
# coordinate and heaviness could not tell them apart at all.
BELL_AXIS_ORDER = [["Scout"], ["None"], ["Fighter"], ["Light"], ["Wood"], ["Bomber"],
                   ["Medium", "Flak", "Steel"],
                   ["Helicopter"], ["Concrete"], ["Heavy"], ["Spaceship"], ["Plate"],
                   ["Superheavy"]]
BELL_AXIS = {a: i * 2.0 / (len(BELL_AXIS_ORDER) - 1)
             for i, slot in enumerate(BELL_AXIS_ORDER) for a in slot}
# `LO` = 1/TILT_RATIO on purpose: the bell must span the SAME 1.5x the discrete tilt already
# spans, or collapsing three templates into one flattens the game. 0.80 was ruled on
# 2026-08-23 against a peak that moved only 0.25 and was re-ruled on 2026-08-24.
BELL_LO = 1.0 / TILT_RATIO
BELL_SIGMA = 0.75
# Which `h` each discrete level maps to, so the bell can reproduce today's templates.
# `Trace` tilts with Light exactly as `tilt_exponent` has it. ⚠ `Super` is NOT a point on the
# bell: §12.0d makes it the FLAT generalist, which no value of `h` produces — it keeps
# `class_tilt`'s SUPER_RATIO compression instead.
BELL_H = {"Light": 0.0, "Trace": 0.0, "Medium": 1.0, "Heavy": 2.0}


def bell_centre_of_mass(vals):
    """Where on the 0..2 axis a profile's strength sits, weighted by its own Versus."""
    pairs = [(BELL_AXIS[a], v) for a, v in vals.items() if a in BELL_AXIS and v > 0]
    total = sum(v for _x, v in pairs)
    return sum(x * v for x, v in pairs) / total if total else None


def heaviness_bell(rows, level):
    """`class_tilt`'s continuous successor. Same signature, same guarantees.

    Identical in every structural respect: the derived armors are excluded, `Super` is
    flattened rather than tilted, each ladder's rank is restored afterwards, and `Heroic` /
    `Airborne` are re-derived LAST from the finished profile.
    """
    vals = dict(rows)
    live = [v for a, v in rows if a not in NON_ARMOR_ROWS]
    if not live or max(live) <= min(live):
        return rows          # Sonic / Magic are flat BY DESIGN; a bell would destroy that
    out = dict(vals)

    h = BELL_H.get(level)
    if h is not None:
        tiltable = {a: v for a, v in vals.items()
                    if a in BELL_AXIS and a not in DERIVED_ARMORS}
        com = bell_centre_of_mass(tiltable)
        if com is not None:
            mu = (h + com) / 2.0
            belled = {a: v * (BELL_LO + (1 - BELL_LO)
                              * math.exp(-((BELL_AXIS[a] - mu) ** 2) / (2 * BELL_SIGMA ** 2)))
                      for a, v in tiltable.items()}
            # Renormalise so heaviness redistributes and never inflates (§12.0i law 2). The
            # mean is re-pinned by `mean_normalise` later, but doing it here keeps the
            # rank-restore step reading comparable magnitudes.
            before = statistics.fmean(tiltable.values())
            after = statistics.fmean(belled.values())
            if after > 0:
                belled = {a: v * before / after for a, v in belled.items()}
            # ⛔ THE RANK RESTORE (§12.0d, §12.0i law 5) — give each armor back the rank it
            # held. Without it the bell changes a ladder's internal order in 127 cases across
            # 60 family/ladder pairs; with it, zero. It permutes values inside one ladder, so
            # the multiset and therefore the mean are untouched.
            for ladder in LADDERS.values():
                rungs = [a for a in ladder if a in belled]
                if len(rungs) < 2:
                    continue
                order = sorted(range(len(rungs)), key=lambda i: (-vals[rungs[i]], i))
                ranked = sorted((belled[a] for a in rungs), reverse=True)
                for slot, i in enumerate(order):
                    out[rungs[i]] = ranked[slot]

    if level == "Super":
        # The generalist: compress toward the band's flat end about the geometric mean.
        # Unchanged from `class_tilt` — no `h` makes a bell flat.
        body = [v for a, v in out.items() if a not in NON_ARMOR_ROWS and v > 0]
        lo, hi = min(body), max(body)
        if lo > 0 and hi / lo > SUPER_RATIO:
            g = statistics.geometric_mean(body)
            alpha = math.log(SUPER_RATIO) / math.log(hi / lo)
            out = {a: (v if a in NON_ARMOR_ROWS else g * (max(v, 1.0) / g) ** alpha)
                   for a, v in out.items()}

    # Re-derive the products LAST, from the finished profile (§12.0b).
    peak = max(v for a, v in out.items()
               if a not in NON_ARMOR_ROWS and a not in DERIVED_ARMORS)
    for name, (first, second) in (("Heroic", ("Plate", "Scout")),
                                  ("Airborne", ("Helicopter", "Scout"))):
        if name in out and first in out and second in out and peak > 0:
            out[name] = out[first] * out[second] / peak
    return [(a, out[a]) for a, _ in rows]


# ⚠ OFF BY DEFAULT, and it must stay off until the maintainer authorises the regeneration:
# switching it rewrites the `Versus` of every `^Warhead_*` template, which CLAUDE.md rule 4
# forbids without explicit permission. `tools/balance/preview_bell.py` measures exactly what
# would change without writing a byte of yaml.
USE_BELL = os.environ.get("CAMEO_HEAVINESS_BELL") == "1"


def level_tilt(rows, level):
    """The single call site's entry point: the ruled bell, or today's discrete tilt."""
    return heaviness_bell(rows, level) if USE_BELL else class_tilt(rows, level)


def _powerlaw(vals, alpha):
    g = statistics.geometric_mean([max(v, 1.0) for v in vals])
    return [g * (max(v, 1.0) / g) ** alpha for v in vals]


def _to_mean(vals, target):
    m = statistics.fmean(vals)
    return [v * target / m for v in vals] if m > 0 else list(vals)


def fit_band_floor(rows):
    """Expand a too-FLAT profile up to `BAND_LOW` about its geometric mean (DESIGN 12.0 rule 5).

    The same floor already existed inside `finish_blend`, but that is the BLEND-only path and it
    runs BEFORE `class_tilt` — the last thing that reshapes a profile. Two families slipped
    through: `CannonAP` (a standard WEAPONS family, so `finish_blend` never ran on it) sat at
    1.81x, and `Cryo` (a blend) was floored to exactly 2.00 and then nudged back to 1.97x by the
    tilt. Applying it to EVERY family AFTER the tilt closes both holes.

    Order-preserving (a power law about the geometric mean is monotonic), and safe to run before
    `mean_normalise` because that rescale is multiplicative, so the ratio set here survives.
    A profile that is flat BY DESIGN (`Sonic`, `Magic`) has hi/lo == 1.0 and is left alone.
    """
    live = [v for a, v in rows
            if a not in NON_ARMOR_ROWS and a not in DERIVED_ARMORS and v > 0]
    if len(live) < 2:
        return rows
    hi, lo = max(live), min(live)
    if not (1.0 < hi / lo < BAND_LOW):
        return rows
    centre = statistics.geometric_mean(live)
    # ⚠ Aim slightly ABOVE the floor. `mean_normalise` rounds to ints afterwards, and landing
    # exactly on 2.00 let rounding drop Prism_Heavy to 1.98x and Laser_Light to 1.99x — still
    # out of band, from a fix that had just put them in it.
    alpha = math.log(BAND_LOW * BAND_MARGIN) / math.log(hi / lo)
    return [(a, v if a in NON_ARMOR_ROWS else centre * (max(v, 1.0) / centre) ** alpha)
            for a, v in rows]


def mean_normalise(rows, target=MEAN_TARGET):
    """Rescale a MAIN profile so the MEAN of its armor rows is `target` (see above).

    Returns rows in the SAME ORDER — the emit order is the ordering law's output and
    `shield_for` overwrites `Shield` immediately after, so nothing here may reshuffle.
    """
    idx = [i for i, (a, _) in enumerate(rows) if a not in NON_ARMOR_ROWS]
    vals = [float(rows[i][1]) for i in idx]
    if not vals:
        return rows
    if max(vals) <= min(vals):
        # Sonic / Magic are flat BY DESIGN ("ignores armor"). Flat at 100 says exactly
        # that and nothing else; the level ladder they used to carry here (45/55/65,
        # 22/27/32/38) was magnitude, which now belongs to Damage and WC.
        fitted = [target] * len(vals)
    else:
        def fits(alpha):
            out = _to_mean(_powerlaw(vals, alpha), target)
            return max(out) <= VERSUS_CEILING + 1e-9 and min(out) >= VERSUS_FLOOR - 1e-9
        if fits(1.0):
            fitted = _to_mean(vals, target)
        else:
            lo, hi = 0.0, 1.0            # largest alpha = least distortion
            for _ in range(60):
                mid = (lo + hi) / 2.0
                if fits(mid):
                    lo = mid
                else:
                    hi = mid
            fitted = _to_mean(_powerlaw(vals, lo), target)
    armor = [(rows[i][0], int(round(v))) for i, v in zip(idx, fitted)]
    if max(vals) > min(vals):
        armor = distinct_ints(armor)     # rounding can re-tie what the floats separated
    fixed = dict(armor)
    return [(a, fixed.get(a, v)) for a, v in rows]


def blend_direction(name, values):
    """A blend's LIGHT/HEAVY direction: its parents' majority, else its own lean.

    A blend has no `WEAPONS` entry, so `build_order` never runs for it and it has no
    declared direction — which is exactly how eight families came to violate the ordering
    law (see `relay_ladders`). The parents do declare one, and for seven of the eight they
    agree unanimously.

    The eighth is `Plasma` = `Flame`(light) + `Chemical`(heavy), a genuine 50/50 split. A
    coin-flip default would be a hidden design decision, so the tie is settled by the
    AVERAGED PROFILE ITSELF: whichever way the measured average already leans is the way it
    is laid out. That keeps the answer derived from data rather than chosen, and it stays
    correct if either parent's profile is ever re-measured.
    """
    parents = BLEND_FAMILIES.get(name, ([], None, None))[0]
    votes = [WEAPONS[p][1] for p in parents if p in WEAPONS]
    heavy, light = votes.count("heavy"), votes.count("light")
    if heavy != light:
        return "heavy" if heavy > light else "light"
    # A TIE is settled by the measured lean -- but ACROSS THE WHOLE FAMILY, not per level.
    #
    # ⚠ Deciding it per level made `Cryo` (= Laser heavy + Prism light) lay itself out BOTH
    # ways: its averaged profile leaned heavy at Light (None 68 / Superheavy 83) and Medium
    # (68 / 88), then light at Heavy by a ONE-POINT margin (83 / 82). A single point flipped
    # the entire level's ladder, so one family read anti-heavy at two levels and anti-light at
    # the third -- the only family in the tree to do so. A family has ONE identity; the level
    # decides how big it is, never which way it points.
    cached = _BLEND_DIRECTION.get(name)
    if cached is not None:
        return cached
    levels = BLEND_FAMILIES.get(name, ([], None, []))[2] or []
    leans = []
    for lvl in levels or [None]:
        rows = values if lvl is None else _blend_rows_for(name, parents, lvl)
        if not rows:
            continue
        leans.append(_lean_of(rows))
    if not leans:
        leans = [_lean_of(values)]
    direction = "heavy" if sum(leans) > 0 else "light"
    if levels:
        _BLEND_DIRECTION[name] = direction        # one identity per family, computed once
    return direction


_BLEND_DIRECTION: dict[str, str] = {}


def _lean_of(values):
    """Sum of (heaviest rung - lightest rung) over every ladder. >0 means anti-heavy."""
    lean = 0.0
    for ladder in LADDERS.values():
        rungs = [a for a in ladder if a in values and a not in DERIVED_ARMORS]
        if len(rungs) >= 2:
            lean += values[rungs[-1]] - values[rungs[0]]
    return lean


def _blend_rows_for(name, parents, level):
    """The averaged parent profile at one level, for the family-wide lean vote."""
    try:
        main, _pct = blend_versus(parents)(level)
    except Exception:
        return None
    return dict(main)


def relay_ladders(values, direction):
    """Re-lay every macro ladder in `direction`, keeping the VALUES exactly.

    ⚠ **This is the ordering law applied to blends, and it was missing.** The law
    (maintainer 2026-08-01, "the most important part") fixes each ladder's direction, and
    the reference side enforces it via `aggregate_archetype.lawful_profile`. Blends skipped
    it entirely: `blend_versus` averages its parents per-armor, and averaging profiles that
    disagree about direction produces a ladder that is monotone in NEITHER — measured, 23
    ladders across 8 families, e.g. `Quantum_Light AIR` reading
    `Fighter 65 · Bomber 63 · Helicopter 52 · Spaceship 81`. A player cannot predict that
    from the weapon's type, which is the entire point the law exists to serve.

    Only the PAIRING changes: the measured magnitudes, plateaus and cliffs all survive, and
    are simply reassigned along the ladder in the lawful order. Same method, and same
    justification, as `lawful_profile` on the reference side.
    """
    out = dict(values)
    for ladder in LADDERS.values():
        rungs = [a for a in ladder if a in values and a not in DERIVED_ARMORS]
        if len(rungs) < 2:
            continue
        # `heavy` = best against the heaviest rung, so the biggest value goes to the END.
        targets = list(reversed(rungs)) if direction == "heavy" else rungs
        for armor, value in zip(targets, sorted((values[a] for a in rungs), reverse=True)):
            out[armor] = value
    return out


def finish_blend(rows, name=None):
    """Repair a BLEND profile: re-derive its derived armors, then re-sharpen it.

    A blend is the per-armor AVERAGE of its parents, and averaging does two things
    that have to be undone before it ships:

    1. **It computes the derived armors instead of deriving them.** §12.0b says
       `Heroic = Plate x Scout / peak` **of the profile it belongs to** — and the
       average of the parents' Heroic is not the product of the blend's own Plate
       and Scout (`avg(ab/p) != avg(a)avg(b)/avg(p)`). Measured: 5 of 21 blend
       levels were off, `CannonFire_Light` by 12 points. Same failure as the
       `/100` divisor bug — a derived value has to be derived LAST, from the
       finished profile.
    2. **It flattens.** Averaging profiles that disagree cancels the
       disagreement — the identical effect that makes a per-family aggregate mush
       (DESIGN §12.0 rule 5). `MissileChem_Heavy` came out at 1.8x, under the
       band. It is re-sharpened back to the band floor with the same POWER LAW the
       reference side uses (`v' = G * (v/G) ** alpha` about the geometric mean),
       never by clamping: clamping would move two cells and change the shape,
       where the power law moves every cell proportionally and preserves both the
       ordering and the geometric centre.
    """
    values = dict(rows)
    # 0. THE ORDERING LAW, which blends used to skip entirely. Must run FIRST: the derived
    #    armors below are computed from `Plate`/`Scout`, so re-laying afterwards would
    #    derive them from cells that are about to move.
    if name is not None:
        values = relay_ladders(values, blend_direction(name, values))

    peak = max(v for a, v in values.items()
               if a not in NON_ARMOR_ROWS and a not in DERIVED_ARMORS)
    for derived, (first, second) in (("Heroic", ("Plate", "Scout")),
                                     ("Airborne", ("Helicopter", "Scout"))):
        if derived in values and first in values and second in values and peak > 0:
            values[derived] = values[first] * values[second] / peak

    ladder = [v for a, v in values.items()
              if a not in NON_ARMOR_ROWS and a not in DERIVED_ARMORS and v > 0]
    if len(ladder) >= 2:
        hi, lo = max(ladder), min(ladder)
        if lo > 0 and 1.0 < hi / lo < BAND_LOW:
            centre = statistics.geometric_mean(ladder)
            alpha = math.log(BAND_LOW) / math.log(hi / lo)
            values = {a: centre * (max(v, 1.0) / centre) ** alpha
                      for a, v in values.items()}

    # Back inside the window, multiplicatively so the spread just set survives.
    #
    # ⚠ **THE WINDOW SCALE MUST IGNORE THE PSEUDO-ARMORS.** `max(values.values())` used to
    # include `Shield`, which is deliberately OUTSIDE the [10, 200] window in both
    # directions — so the shield row, not the armor ladder, decided the scale for the whole
    # profile. That was a quiet 2x crush while Shield ran 100..400; once phase 1 began
    # emitting Shield in CENTI-UNITS it became catastrophic: `Quantum_Light` scaled by
    # 200/18535 = 0.011, every armor rounded to 0 or 1, and `distinct_ints`' floor-repair
    # pass then FABRICATED the entire ladder from the emit order (10, 11, 12, 14 ...).
    #
    # It was invisible because `mean_normalise` runs afterwards and scales the garbage back
    # up to a mean of 100, so the profiles looked plausible and passed every window check.
    # The only symptom was the 23 non-monotone ladders logged as E9 — which were never a
    # missing ordering pass at all, but a ladder that had stopped carrying data.
    ladder_top = max((v for a, v in values.items() if a not in NON_ARMOR_ROWS),
                     default=0.0)
    scale = min(1.0, VERSUS_CEILING / ladder_top) if ladder_top > 0 else 1.0
    out = distinct_ints([(a, int(round(values[a] * scale))) for a, _ in rows])
    # Re-lay ONE more time, on the finished integers. `distinct_ints` separates ties by
    # walking the row list, and that list is in emit order rather than ladder order — so a
    # raw tie (`Storm_Light` had `Bomber 16` and `Helicopter 16`) gets broken in whichever
    # direction the list happened to run, re-inverting a ladder that was already lawful.
    # A second pass is safe by construction: it only PERMUTES an already-valid multiset
    # within each ladder, so distinctness and the window both survive untouched.
    if name is not None:
        final = relay_ladders(dict(out), blend_direction(name, dict(out)))
        out = [(a, final[a]) for a, _ in out]
    return sorted(out, key=lambda r: -r[1])


def reference_main(name, order16, level):
    """The measured main-warhead rows for a family+level, or None if unmeasured.

    `Shield` keeps the rule it always had — one floor above the profile's best
    target (`table()` passes `100 + floor`, i.e. top + floor). Expressed against
    the profile's OWN top and floor it is the same rule, and it reduces to exactly
    the old constant whenever the profile peaks at 100. That matters: shields are
    the softest layer by design, so pinning them to a constant while the profile
    moves would make a specialist's best target tougher than a shield.
    """
    # Measured wins over designed: if the corpus ever gains coverage for a family we
    # had to invent, the evidence should displace the design without anyone having to
    # remember to delete the old entry.
    entry = (REFERENCE_PROFILES.get(name, {}).get(level)
             or DESIGNED_PROFILES.get(name, {}).get(level))
    if entry is None:
        return None
    profile = entry["profile"]
    if not all(a in profile for a in order16):
        return None                       # partial data is not usable data
    values = [profile[a] for a in order16]
    shield = max(values) + min(values)
    # `Shield` is a Versus row like any other, so the window binds on it too — and it
    # is the row most likely to breach, because its rule puts it one floor ABOVE the
    # profile's best target and the best target may already be at the ceiling. Scale
    # the whole set down together rather than clamping Shield alone: clamping would
    # tie it with the top armor, and a shield that is no softer than the toughest
    # thing the weapon can hit is not a shield.
    scale = min(1.0, VERSUS_CEILING / shield) if shield > 0 else 1.0
    rows = ([("Shield", int(round(shield * scale)))]
            + [(a, int(round(profile[a] * scale))) for a in order16])
    rows = distinct_ints(rows)
    # Emit DESCENDING. The law's order produced the assignment, but `Heroic` is
    # DERIVED (`Plate x Scout / peak`) and lands wherever its product falls, not in
    # the infantry slot the order gave it — so the law's sequence is no longer a
    # descending list and a reader can no longer check the ladder by eye. Sorting
    # is display only: for the even-ramp families it is exactly the order they
    # already emit, so nothing moves except the derived armors.
    return sorted(rows, key=lambda r: -r[1])


def emit_versus(rows, indent="\t\t\t"):
    """Emit a `Versus:` node: pseudo-rows first, then armors DESCENDING by value.

    Maintainer 2026-08-16: *"the percentage versus values are not ordered by power like
    they are for the normal variants ... enforce this rule so percentage values are also
    always ordered by descending value (except for hazmat and shield which are always
    first)"*.

    The main warhead already arrived sorted (`reference_main` / `finish_blend` end with a
    descending sort), but the `_Percentage` twin and the `_ExtraDamage` chip did not: they
    were emitted in the ORDERING LAW's sequence — macro blocks INF, VEH, BLD, AIR, each
    ascending for a light-favouring family — which reads as `9 10 11 13 · 7 9 10 12 13`,
    restarting at every block. The law decides which armor gets which VALUE; it was never
    meant to decide the print order, and a reader cannot check a ladder that restarts.

    Sorting HERE rather than at each call site makes the invariant unconditional: every
    Versus node the generator emits is descending, whoever built the rows. The sort is
    STABLE, so armors that tie keep the ordering law's sequence — which is the right
    tiebreak, because the law's order is the design statement about them.

    `HAZMAT` and `Shield` are pinned first and excluded from the sort: neither is an armor
    class (one is a gate, the other the shield LAYER), and `Shield` is deliberately outside
    the [10, 200] window in both directions, so sorting it in would drag it to an end and
    hide the ladder it is not part of.
    """
    out = []
    lead = [r for r in rows if r[0] in NON_ARMOR_ROWS]
    body = sorted((r for r in rows if r[0] not in NON_ARMOR_ROWS), key=lambda r: -r[1])
    for a, v in lead + body:
        out.append(f"{indent}{a}: {v}")
    return "\n".join(out)


def valid_targets(hits_air, ground_only=False):
    if hits_air:
        return "Ground, Water, Air"
    return "Ground" if ground_only else "Ground, Water"


# Damage falloff profiles (maintainer 2026-08-11): 6-wide, ALL end in 0 so damage reaches 0 at the
# outer ring. One profile per level (Light/Medium/Heavy/Super); higher tiers fall off STEEPER (more
# concentrated). Radius = (len-1) x Spread; damage LERPs between points. Per-family overrides below.
DEFAULT_FALLOFFS = ("100, 50, 33, 25, 20, 0", "100, 60, 30, 15, 5, 0",
                    "100, 50, 25, 10, 5, 0", "100, 40, 20, 10, 5, 0")
# Even / linear ramp (opt-in via FAMILY_FALLOFFS): equal steps to 0 = a flat line.
EVEN_FALLOFFS = ("100, 80, 60, 40, 20, 0",) * 4


def family(name, order16, vt, levels, *, mode=None, damage=2000,
           spreads=(400, 600, 800, 1000),
           falloffs=DEFAULT_FALLOFFS,
           damage_types="Prone75Percent, TriggerProne, ExplosionDeath",
           overlays=True, reload=25, rng=5120, versus_override=None, physical_states=None,
           profile_family=None):
    """mode: None = sloped (from order16); 'flat' = Sonic (uniform flat, small %);
    'pct' = Magic (tiny uniform flat + LARGE uniform % of max HP).
    Every main warhead is AreaDamage with baked UNIVERSAL friendly fire
    (ValidRelationships: Ally, Neutral, Enemy + FriendlyFireDamage/Spread 50) —
    the old separate _FriendlyFire twin is retired. See cameo-expanding-damage-trait
    and docs/design/AREADAMAGE_WARHEAD.md."""
    blocks = []
    allr = sorted(CANON16)
    for level in levels:
        li = list(LEVELS).index(level)
        if versus_override is not None:          # blend family (e.g. Plasma = avg of Flame + Chemical)
            main, pct = versus_override(level)
            main = finish_blend(main, name)      # ordering law, re-derive Heroic/Airborne, un-flatten
            hz = overlays
        elif mode == "flat":                       # Sonic: ignores armor on FLAT
            fv, fp = FLAT_VALUES[level], FLAT_PCT[level]
            main = [("Shield", fv)] + [(a, fv) for a in allr]
            pct = [("Shield", fp)] + [(a, fp) for a in allr]
            hz = None
        elif mode == "pct":                      # Magic: 1/2 Sonic flat + 5x Sonic %-of-maxHP (giant-killer)
            mv = MAGIC_MAIN[level]
            main = [("Shield", mv)] + [(a, mv) for a in allr]
            pv = MAGIC_PCT[level]                 # percentage profile; magnitude follows main Damage
            pct = [("Shield", pv)] + [(a, pv) for a in allr]
            hz = None
        else:                                    # standard sloped profile
            step, mfloor, ptop = LEVELS[level]
            pfloor = ptop - 15
            # Measured profile if the corpus has one, otherwise the even ramp.
            # `profile_family` lets an INHERITING family (Cryo, Inferno) read its
            # PARENT's measured profile — the whole premise of those families is
            # that they reuse the parent's ladder and only add a PhysicalState, so
            # looking the profile up under their own name silently fell through to
            # the even ramp and split them off from the parent they inherit.
            main = (reference_main(profile_family or name, order16, level)
                    or table(order16, step, 100, mfloor, 100 + mfloor))
            # PercentageVersus stays the 1-step ladder, deliberately. Its window is only
            # 16 wide (`ptop` down to `ptop-15`), so 16 armors that must all differ
            # can only be the even ramp — there is no room left for a second shape.
            # PercentageScale supplies the magnitude; this table carries the armor order.
            pct = table(order16, 1, ptop, pfloor, ptop + pfloor)
            hz = overlays
        # W25 S2 — the class tilt, BEFORE the mean is pinned: the tilt moves output between
        # armors and would otherwise leave the mean off 100. Order-preserving by
        # construction (see class_tilt), so the two-level ordering law is untouched.
        main = level_tilt(main, level)
        # DESIGN 12.0 rule 5 — the 2x band floor, applied to EVERY family and AFTER the tilt.
        # See fit_band_floor: the blend-only copy inside finish_blend missed CannonAP entirely
        # and let the tilt undo it for Cryo.
        main = fit_band_floor(main)
        # W25 S1 — pin the profile's MEAN to 100 before anything reads it. Must run on
        # EVERY branch and BEFORE `shield_for`: Shield's structural term is
        # `sqrt((200+floor)(100+top))`, so it has to see the final ladder, not the
        # pre-normalisation one. See MEAN_TARGET above for why, and for what it costs.
        main = mean_normalise(main)
        # SINGLE SOURCE for Shield, applied to EVERY branch (flat, pct and standard):
        # overrides whatever the measured or designed path put there, so the two can never
        # contest the cell again (see shield_for). Placed after the if/else on purpose —
        # scoping it to one branch left the FLAT/PCT families on their old value.
        sv = shield_for(name, level, main)
        if sv is not None:
            main = [("Shield", sv)] + [(a, v) for a, v in main if a != "Shield"]
        # The OVERLAY armors, derived from the family's composition (see overlay_rows).
        # Carried inside `main` rather than passed separately so they are automatically
        # excluded from the mean, the tilt and the Shield scale — all three key off
        # NON_ARMOR_ROWS — and pinned ahead of the ladder by `emit_versus`.
        #
        # ⚠ **EVERY template gets all five, with no exceptions — including Sonic and Magic.**
        # The flat families used to be skipped because "they ignore armor", and under the old
        # additive overlay that was harmless. Under layer SELECTION it is a hole: a plated
        # unit hit by a weapon with no row for its plating leaves the armor list EMPTY, which
        # `DamageVersus` answers with 100 — so skipping the row would make Sonic and Magic
        # ignore the plating layer entirely and hit plated units HARDER than unplated ones.
        # Their identity is untouched: "ignores armor" is a statement about the 16 CLASS
        # armors, which stay flat. A plating designed against pressure may still blunt a
        # sonic weapon, and that is the correct reading.
        main = [r for r in main if r[0] not in PLATING_CYCLE]
        main = plating_rows(name) + main
        tag = f"{name}_{level}"
        # ⚠ `spreads` (the PHYSICS_SHAPES value) WINS. ENERGY_THIN_SPREAD is the older
        # "thin the energy mains to near single-target" rule and it is now only a FALLBACK for a
        # family with no physics shape. It used to win outright, which pinned Tesla, Laser,
        # Railgun, Prism, Inferno and Cryo to a flat Spread 100 at every level and made Laser
        # collide with Railgun and with Bullet — the physics table was computed and then thrown
        # away for exactly the six families whose identity is "a thin beam".
        main_spread = at(spreads, li) if spreads else ENERGY_THIN_SPREAD_LEVEL.get(
            (name, level), ENERGY_THIN_SPREAD.get(name, 400))
        invalid = FAMILY_INVALID_TARGETS.get(name)
        inv_weapon = [f"\tInvalidTargets: {invalid}"] if invalid else []
        inv_warhead = [f"\t\tInvalidTargets: {invalid}"] if invalid else []
        main_wh = [f"^Warhead_{tag}:",
             f"\tValidTargets: {vt}",
             *inv_weapon,
             f"\tReloadDelay: {reload}",
             f"\tRange: {rng}",
             f"\tTargetActorCenter: true",
             f"\tWarhead@{tag}: AreaDamage",
             f"\t\tValidRelationships: Ally, Neutral, Enemy",
             f"\t\tFriendlyFireDamage: 50",
             f"\t\tFriendlyFireSpread: 50",
             f"\t\tValidTargets: {vt}",
             *inv_warhead,
             f"\t\tSpread: {main_spread}",
             f"\t\tDamage: {damage}",
             f"\t\tFalloff: {at(falloffs, li)}",
             f"\t\tVersus:",
             emit_versus(main),
             f"\t\tDamageTypes: {damage_types}"]
        if name in FAMILY_PHYSICAL_STATE:  # heat/cold/corrosion meter, scaled by main damage
            ps = FAMILY_PHYSICAL_STATE[name]
            if isinstance(ps, dict):
                main_wh.append("\t\tPhysicalStates:")
                main_wh += [f"\t\t\t{k}: {v}" for k, v in _physical_states_for_level(ps, level).items()]
            else:
                psn, pss = ps
                main_wh += [f"\t\tPhysicalStateName: {psn}", f"\t\tPhysicalStateScale: {pss}"]
        if physical_states:  # multi-state blend (e.g. Plasma: Temperature 50 + Corrosion 50)
            resolved = _physical_states_for_level(physical_states, level)
            main_wh.append("\t\tPhysicalStates:")
            main_wh += [f"\t\t\t{k}: {v}" for k, v in resolved.items()]
        integ = FAMILY_INTEGRITY_SCALE.get(name)  # ELECTRONICS (EMP) auto-drain — NOT a shield
        if integ:
            main_wh.append(f"\t\tIntegrityScale: {integ}")
        # ⭐ THE FOLD (UNIFIED_AREADAMAGE_WARHEAD.md). The percentage half is no longer a second
        # warhead — it is four fields on the main one, so an inline weapon carries ONE Damage
        # number and the percentage follows from it instead of being hand-typed alongside and
        # drifting. Measured before the change: 2287 of 2469 twins were already exactly
        # `main // 100`, and the 182 that were not drifted by clean fractions (x0.5, x0.25,
        # x0.2, x2) — i.e. deliberate per-weapon dials, which is what PercentageScale is.
        #
        # ⚠ NO x5 on these Versus values. W18 multiplied the standalone twin's band by 5 to pair
        # with `Damage = flat // 100`; the fold derives its own basis points as
        # `Damage x PercentageScale / 200000`, which already carries that factor. (D/100)x5V is
        # (D/20)xV, so PercentageVersus stays in the natural band.
        #
        # IntegrityScale, PhysicalStateName/Scale and PhysicalStates already sit on the main
        # warhead and AreaDamageWarhead.InflictPercentage applies them to the percentage hit
        # too, so the twin's copies of all three are simply no longer needed.
        main_wh += [f"		PercentageScale: 10000",
                    f"		PercentageSpread: 50",
                    f"		PercentageVersus:",
                    emit_versus(pct)]
        parts = main_wh
        if name in CHIPS:  # paid-for ExtraDamage chip (energy families only)
            parts.append(emit_chip(tag, name, damage, vt, level=level))
        if name in FAMILY_CONDITION:  # on-hit status mark (Sonic -> SonicDebuff)
            cname, dmul, rmul = FAMILY_CONDITION[name]
            parts.append(emit_condition(tag, cname, reload * dmul, main_spread * rmul, vt))
        blocks.append("\n".join(parts))
    return "\n\n".join(blocks)


def macro_summary(blocks):
    if blocks == "FLAT":
        return "FLAT (ignores armor)"
    if blocks == "PCT":
        return "PCT (%-equalizer)"
    def lbl(g):
        return "+".join(g) if isinstance(g, tuple) else g
    return " > ".join(lbl(g) for g in blocks)


SPECIAL_MODE = {"FLAT": "flat", "PCT": "pct"}

# Friendly fire is now UNIVERSAL and baked into every main warhead (AreaDamage +
# FriendlyFireDamage/Spread 50), so there is no longer a per-family FF twin.
# ^Warhead_Nuclear_Super is HAND-TUNED (10 expanding rings + AreaDamagePercentage
# subclass) — the generator cannot reproduce it, so it is excluded from emission
# (regenerating it would revert the hand-tuned superweapon). See the memory
# cameo-expanding-damage-trait.
HAND_TUNED = {"Nuclear"}

# Per-family spread overrides. Default is (400, 600, 800, 1000) for
# Light/Medium/Heavy/Super. Indices beyond a family's level count are ignored.
# ⚠ Indexed POSITIONALLY by `list(LEVELS).index(level)`, i.e.
#     0 Light · 1 Medium · 2 Heavy · 3 Super · 4 Trace
# so any family using `Trace` needs five entries. `at()` below tolerates a short tuple rather
# than raising IndexError, but a family should still state its own value instead of inheriting
# whatever happens to sit last.
FAMILY_SPREADS = {
    "MissileAA": (200, 300, 400),
    # A gas FIELD is wide and thin by nature — it is area denial, not a hit. Trace (slot 4) is
    # the faint wisp, Light the standard cloud, Medium the heavy/Large variants.
    "Toxic": (900, 1100, 800, 800, 700),
}

# Per-family falloff overrides (default = DEFAULT_FALLOFFS, indexed by level). Bullets are a single
# max-radius linear ramp (near single-target); EVEN_FALLOFFS is available for any family that wants a
# flat line. Nuclear is HAND_TUNED (11-wide, hand-set in its yaml template).
FAMILY_FALLOFFS = {
    "Bullet": ("100, 0", "100, 0", "100, 0"),   # pure max-radius linear
    # A drifting cloud has no blast centre: concentration is near-even across the field and
    # only tails off at the edge. Slot order as in FAMILY_SPREADS (Trace is slot 4).
    "Toxic": ("100, 90, 75, 55, 30, 0",) * 5,
}


# ---------------------------------------------------------------------------------------------
# SPREAD_FALLOFF_PLAN.md §8 — the per-type PHYSICS shape (maintainer ruling 2026-08-08, built
# 2026-08-22). Every damage TYPE gets its own curve derived from how that weapon really spreads
# energy; the LEVEL scales the radius but never the shape.
#
# ⛔ WHY THIS EXISTS. Before this table 103 of 117 families shared just THREE curves, one per
# level, so the shape encoded the weapon's LEVEL and not its TYPE: 23 different Heavy families —
# Melee, Arrow, PhotonCannon, Sonic, Flame, CannonNuke — all sat at Spread 800 / radius 4000 /
# `100,50,25,10,5,0`. A melee strike had the same four-cell blast as a nuclear tank shell.
#
# radius = the MEDIUM radius in WDist (1024 = one cell); Spread = radius / (len(Falloff) - 1),
# because AreaDamageWarhead.cs:143 lays the falloff points at 0, S, 2S ... (N-1)S.
PHYSICS_SHAPES = {
    # -- kinetic point impact ---------------------------------------------------------------
    # ⚠ These are NOT all "100, 0 at whatever radius". Maintainer 2026-08-22: *"every family
    # needs to be unique as fuck"*. A pinpoint weapon still has a real lateral energy spread and
    # the ladder below is that spread, smallest first — a coherent beam deposits on a spot, a
    # shaped-charge jet is a narrow cone, a broadhead is physically wide, a proximity fuze never
    # touches the target at all. No two families share BOTH a radius and a curve.
    "Sniper":     (40,   "100, 0"),          # one aimed round, tighter than a burst
    "Laser":      (48,   "100, 0"),          # coherent light: no lateral spread whatsoever
    "MissileAP":  (64,   "100, 0"),          # shaped-charge jet — narrow, deep, all energy forward
    "Railgun":    (72,   "100, 0"),          # hypervelocity slug + plasma sheath on impact
    "Arrow":      (88,   "100, 0"),          # a broadhead is physically wide but slow
    "Magic":      (96,   "100, 0"),          # non-physical %HP, no blast at all
    "Bullet":     (100,  "100, 0"),          # the reference point impact
    "CannonAP":   (120,  "100, 0"),          # big penetrator: spall sprays behind the plate
    "Melee":      (0,    "100, 0"),          # adjacent contact only
    # -- pinpoint WITH a real secondary spread: these earn their own curve -------------------
    "Prism":      (150,  "100, 40, 0"),      # beam plus a refraction scatter halo
    "Tesla":      (140,  "100, 55, 0"),      # the arc jumps to nearby conductors
    "MissileAA":  (180,  "100, 70, 30, 0"),  # proximity fuze: never hits, detonates NEAR
    # -- overpressure: convex, ~1/r near-field ----------------------------------------------
    "CannonHE":   (900,  "100, 50, 20, 0"),
    "MissileHE":  (450,  "100, 45, 15, 0"),
    # Airburst fragmentation (maintainer: *"flak could get a slightly different shape that makes
    # it more like explosion or shrapnel"*). A shell bursting in the air throws fragments outward,
    # so it is NOT the plain convex blast of an HE shell: a sharp drop off the detonation point
    # and then a long thin fragment tail. Smaller and sharper-cored than Concussion, which is the
    # same physics at ground level and twice the size.
    "Flak":       (550,  "100, 58, 32, 16, 6, 0"),
    "Demolition": (1400, "100, 45, 18, 6, 0"),        # concentrated charge, ~1/r^3, punchy centre
    # -- fragmentation: frags fly OUTWARD, so the field is broad with a long thin tail -------
    "Concussion": (2100, "100, 72, 50, 32, 18, 8, 0"),
    # -- sustained zone: fire covers an area evenly and stops at a hard edge -----------------
    "Flame":      (1200, "100, 90, 78, 60, 0"),
    "Chemical":   (1100, "100, 88, 72, 50, 0"),
    # -- wave: sound pressure falls ~1/r, near-linear ----------------------------------------
    "Sonic":      (1600, "100, 75, 50, 25, 0"),
    # An electrical STORM is many discrete arcs over an area: broad reach, but each arc is a
    # point, so the field thins quickly rather than holding a plateau like fire.
    "Storm":      (1600, "100, 70, 45, 25, 10, 0"),
    # Nuclear's own template is HAND_TUNED (11 expanding rings) and the generator skips it, but
    # it must appear here or the blends that cross it — CannonNuke, MissileNuke — silently drop
    # their nuclear half and come out the size of a plain HE shell.
    "Nuclear":    (10000, "100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0"),
}


# Radius by level, relative to the family's MEDIUM radius. Preserves the ratios of the old
# global (400, 600, 800, 1000) tuple — 0.67 / 1 / 1.33 / 1.67 — so the level ladder is unchanged
# and only the per-family SHAPE and SCALE move. Trace is the sub-light lingering tier.
LEVEL_RADIUS_SCALE = {"Light": 2 / 3, "Medium": 1.0, "Heavy": 4 / 3, "Super": 5 / 3, "Trace": 0.5}


def _curve(text):
    return [int(x) for x in text.split(",")]


def _resample(curve, n):
    """`curve` re-expressed on `n` evenly spaced points over the SAME normalised radius.

    Blending a 2-point `100, 0` with a 5-point fire curve needs both on one grid; resampling
    the pinpoint curve to 5 points yields `100, 75, 50, 25, 0`, i.e. the same straight line
    it always described. Linear interpolation, matching GetDamageFalloff's own int2.Lerp.
    """
    if n == len(curve):
        return list(curve)
    out = []
    for i in range(n):
        pos = i * (len(curve) - 1) / (n - 1)
        lo = int(pos)
        hi = min(lo + 1, len(curve) - 1)
        out.append(round(curve[lo] + (curve[hi] - curve[lo]) * (pos - lo)))
    return out


def blend_shape(parents):
    """A crossover family's shape, built from the shapes of the families it crosses.

    Maintainer 2026-08-22: *"if one warhead is like a crossover of different other warheads they
    should take the original shapes into account and then create a crossover shape as well"*.

    - RADIUS is the GEOMETRIC mean, because the notation is `Bullet x Flame` and scales
      multiply: an incendiary bullet leaves a small fire (sqrt(100 x 1200) = 346), not half a
      flamethrower (arithmetic would say 650). Over parents of similar size the two agree.
    - The CURVE is the arithmetic mean per point, on the finest parent's grid — percentages
      average, and keeping the most detailed grid means no parent's shape detail is lost.
    """
    shapes = [PHYSICS_SHAPES[p] for p in parents if p in PHYSICS_SHAPES]
    if not shapes:
        return None
    radius = 1.0
    for r, _ in shapes:
        radius *= max(r, 1)
    radius = round(radius ** (1 / len(shapes)))
    n = max(len(_curve(c)) for _, c in shapes)
    grids = [_resample(_curve(c), n) for _, c in shapes]
    avg = [round(sum(g[i] for g in grids) / len(grids)) for i in range(n)]
    avg[0], avg[-1] = 100, 0                     # every curve starts full and reaches zero
    return radius, ", ".join(str(v) for v in avg)


def shape_for(name):
    """(spreads, falloffs) tuples for one family, indexed by level position in LEVELS.

    Returns None when the family is governed by an explicit FAMILY_SPREADS/FAMILY_FALLOFFS
    override (Toxic's spawned gas field) or is HAND_TUNED (Nuclear's 11 expanding rings).
    """
    shape = PHYSICS_SHAPES.get(name)
    if shape is None:
        parents = BLEND_FAMILIES.get(name, ([],))[0]
        shape = blend_shape(parents) if parents else None
    if shape is None:
        return None
    radius, falloff = shape
    steps = len(_curve(falloff)) - 1
    spreads, falloffs = [], []
    for level in LEVELS:
        r = round(radius * LEVEL_RADIUS_SCALE[level])
        spreads.append(max(r // steps, 1) if steps else 1)
        falloffs.append(falloff)
    return tuple(spreads), tuple(falloffs)


def at(seq, index):
    """`seq[index]`, tolerating a tuple shorter than the level count.

    The per-family spread/falloff tuples are indexed positionally by the level's place in
    `LEVELS`, so adding a level made every 4-long tuple a latent IndexError for any family
    that used it. Falling back to the last entry keeps the generator running; the fix for a
    family that cares is to state its own value.
    """
    return seq[index] if index < len(seq) else seq[-1]

# Per-family PhysicalState wiring (docs/design/PHYSICAL_STATE_SYSTEM.md): the main AreaDamage warhead
# adds `damage x Scale%` to a named meter on hit (Temperature = heat/cold, Corrosion = acid).
# Flame and Chemical also emit meter-aware AreaDamagePercentage twins so their percentage damage
# contributes to the same meter. The _ExtraDamage chip remains excluded.
# Cryo is a separate thin child of Prism (Temperature -100), not listed here.
# ⭐ FULL STRENGTH IS ONE KNOB — `METER_FULL`. Everything below is a FRACTION of it, so the
# maintainer can move the whole system with a single edit instead of 13 hand-divided numbers.
#
# The race, corrected 2026-08-18 (`tools/balance/physical_state_price.py` owns the arithmetic):
#
#     hits_to_fill / hits_to_kill = MaxValue x 100 / (Scale x range) = 50 / Scale
#
# `range = MaxValue - MinValue` = 40000 on BOTH meters now that Corrosion is signed like
# Temperature. The target's HP and the weapon's damage BOTH cancel, so the constant alone decides
# it, and the bar ("full effect while 25% HP remains") is ratio <= 0.75.
#
# ⚠ A previous revision here claimed the ratio was `200 / scale`, concluded that every
# flamethrower filled its meter twice as slowly as it killed, and had the maintainer raise the
# constant to 300 to fix it. That derivation trusted `PhysicalStateInfo.RelativeToHealth`'s stale
# [Desc] ("divided by HP/10000") instead of `ScaleChangeToHealth`, and was wrong by 4x.
# **METER_FULL = 100 already gives ratio 0.50** — full effect with half the target's life left,
# comfortably inside the bar. 300 was a 3x faster fill than anything needed it to be.
METER_FULL = 100


def _m(fraction: float) -> int:
    """A meter strength expressed as a share of full. Keeps the per-parent-average rule exact."""
    return int(round(METER_FULL * fraction))


def _physical_states_for_level(states, level):
    """Resolve a physical-states spec to the current level.

    Supports level-scaled dicts like {"Corrosion": {"Light": 20, "Medium": 33, "Heavy": 50}}
    alongside plain constants like {"Corrosion": 50}.  Missing levels fall back to Heavy.
    """
    if not states:
        return {}
    resolved = {}
    for k, v in states.items():
        if isinstance(v, dict):
            resolved[k] = v.get(level, v.get("Heavy", v.get("Light", 0)))
        else:
            resolved[k] = v
    return resolved


FAMILY_PHYSICAL_STATE = {
    "Flame":    ("Temperature", _m(1.00)),   # heat -> overheat/pop
    "Laser":    ("Temperature", _m(0.75)),   # laser overheats (main only, chip excluded)
    "Chemical": {"Corrosion": _m(1.00)},     # acid -> corrosion meter (mapping form)
    # ⭐ SUPPORT WEAPONS, maintainer 2026-08-22: Cryo and Inferno fill the meter TWICE as fast as
    # Flame (Scale 200 vs 100), so they freeze/ignite after 25% of lethal damage instead of 50%.
    # The intent is "mostly apply the physical effect without dealing too much direct damage" —
    # most of their output is INDIRECT. That is only expressible now that `speed_weight` prices
    # fill RATE (the old delivery-average metric charged Scale 400 the same as Scale 67), so the
    # doubled rate is paid for and the pipeline can take the direct damage back out.
    "Cryo":     ("Temperature", _m(-2.00)),  # prism beam that freezes — 2x Flame
    "Inferno":  ("Temperature", _m(2.00)),   # prism beam that burns — 2x Flame
    # Plasma (Temperature + Corrosion) needs two states on one warhead -> handled at family build.
}

# Per-family Integrity ELECTRONICS auto-scale: the C# AreaDamage.IntegrityScale drains the victim's
# shield by `damage x Scale%` on hit, EXACTLY like PhysicalStateScale (auto-tracks the real post-armor
# damage, so no flat EMP number is ever hand-set and the ordering can't drift). Tesla-content law:
# Scale = round(100 x Tesla-parents / total-parents) -> pure Tesla 100, Storm (Tesla+Magic) 50,
# Quantum (Railgun+Laser+Tesla) 33. Emitted on BOTH the main AreaDamage and the _Percentage
# AreaDamagePercentage warheads (both extend AreaDamageWarhead and support IntegrityScale). The
# _ExtraDamage chip (SpreadDamage) has no IntegrityScale field but carries Tesla in DamageTypes for
# the passive INotifyDamage drain. The flat AffectsIntegrity warhead stays UPGRADE-only (a concrete
# bonus on top), so no template emits it. See PHYSICAL_STATE_SYSTEM.md.
FAMILY_INTEGRITY_SCALE = {
    "Tesla": 100,                          # pure Tesla = full drain (the EMP-disable specialist)
    "Storm": 50,                          # Tesla+Magic -> 1/2
    "Quantum": 33,                        # Railgun+Laser+Tesla -> 1/3
    "MissileTesla": 50,                   # Tesla + MissileAP -> 1/2
    "CannonTesla": 50,                    # Tesla + CannonAP -> 1/2
    "BulletTesla": 50,                    # Tesla + Bullet -> 1/2
    "MissileQuantum": 17,                 # (Railgun+Laser+Tesla) + 3xMissileAP -> 1/6 Tesla
    # ⚠ `Waveforce: 20` DELETED 2026-08-16 (maintainer order) — it could never fire.
    #
    # The drain rate is `(1 if the damage carries the `Tesla` type else 0) + IntegrityScale/100`
    # per point of damage, against a pool of 100% of max HP. Waveforce is the one integrity
    # family that never received `Tesla` in its DamageTypes, so it lost the 1:1 passive drain and
    # kept only its 20% scale — needing **5x the target's max HP** to reach the disable. The
    # target dies five times over first. Measured, not inferred (PSEUDO_ARMOR_AND_INTEGRITY §B).
    #
    # Maintainer: *"waveforce should remove the integrity damage entirely because it can never
    # actually reach a full integrity damage, so that it is not calculated in the balance formula
    # without any effect."* Exactly right, and the second half is the important half: a knob that
    # does nothing in play but is still read by the pricing model is worse than no knob at all,
    # because the weapon is charged for an effect it cannot deliver.
    #
    # The alternative — granting Waveforce the `Tesla` damage type — was NOT taken: that would
    # give a 3/5-kinetic blend the same EMP status as a Tesla coil, which is a design claim
    # nobody made. If Waveforce should have an EMP role it needs both halves, deliberately.
}

# Per-family DamageTypes override. Every family that affects Integrity (has IntegrityScale) MUST carry
# the `Tesla` DamageType so the Integrity trait's passive INotifyDamage drain fires. IntegrityScale
# values already account for the passive drain stacking. `ElectricityDeath` = tesla death animation.
# Families NOT listed use the default (Prone75Percent, TriggerProne, ExplosionDeath).
FAMILY_DAMAGE_TYPES = {
    "Tesla":      "Prone75Percent, TriggerProne, ElectricityDeath, Tesla",
    "Quantum":    "Prone75Percent, TriggerProne, ElectricityDeath, Tesla",
    "Inferno":    "Prone75Percent, TriggerProne, FireDeath, Incendiary",
    "CannonNuke":    "Prone75Percent, TriggerProne, FireDeath, Incendiary",
    "MissileNuke":    "Prone75Percent, TriggerProne, FireDeath, Incendiary",
    "CannonFire":    "Prone75Percent, TriggerProne, FireDeath, Incendiary",
    "MissileFire":    "Prone75Percent, TriggerProne, FireDeath, Incendiary",
    "MissileTesla":   "Prone75Percent, TriggerProne, ElectricityDeath, Tesla",
    "CannonTesla":   "Prone75Percent, TriggerProne, ElectricityDeath, Tesla",
    "BulletFire":     "Prone75Percent, TriggerProne, FireDeath, Incendiary",
    "BulletThermobaric": "Prone75Percent, TriggerProne, FireDeath, Incendiary",
    "BulletTesla":    "Prone75Percent, TriggerProne, ElectricityDeath, Tesla",
    "MissileQuantum": "Prone75Percent, TriggerProne, ElectricityDeath, Tesla",
    "MissileThermobaric": "Prone75Percent, TriggerProne, FireDeath, Incendiary",
    "CannonChem": "Prone75Percent, TriggerProne, TiberiumDeath",
    "MissileChem":"Prone75Percent, TriggerProne, TiberiumDeath",
    "BulletChem": "Prone75Percent, TriggerProne, TiberiumDeath",
    # Storm is handled at its own call site (Prone100Percent + Tesla).
}

# Per-family STATUS CONDITION (PHYSICAL_STATE_SYSTEM.md §6 decision 4). Some families mark the target
# with a short external condition on every hit instead of (or as well as) filling a PhysicalState meter.
# Sonic = `SonicDebuff` (^SonicDebuff in defaults.yaml: +50% incoming damage, -25% speed, blue tint) —
# the resonance that softens what the beam is standing on. Both numbers are DERIVED, never hand-picked:
#   Duration = duration_x_reload x ReloadDelay  -> continuous fire keeps the mark up, and it lapses a
#              couple of shots after the beam stops (the maintainer's "short duration, on hit only").
#   Range    = range_x_spread x the main warhead Spread -> the half-damage radius of the same blast.
# {family: (condition, duration_x_reload, range_x_spread)}
FAMILY_CONDITION = {
    "Sonic": ("SonicDebuff", 2, 2),
}

# Per-family InvalidTargets, emitted on the weapon AND its damaging warheads.
# WEAPON_TYPE_SYSTEM.md specifies Toxic as "no-op vs robotic": a gas kills people, so a drone
# or a robot walks through it untouched. That is a TARGETING rule, not a Versus value — W13
# rule 8 forbids expressing immunity as a zero multiplier, and `ToxinImmune` is the existing
# target-type the legacy ^ToxicWeapon already used for exactly this.
FAMILY_INVALID_TARGETS = {
    "Toxic": "wall, Mine, ToxinImmune",
}


def emit_condition(tag, cname, duration, rng, vt):
    """Emit the on-hit status-condition warhead (never damages, so it is price-neutral)."""
    return "\n".join([
        f"\tWarhead@{tag}_Debuff: GrantExternalCondition",
        f"\t\tCondition: {cname}",
        f"\t\tDuration: {duration}",
        f"\t\tRange: {rng}",
        f"\t\tValidRelationships: Enemy, Neutral",
        f"\t\tValidTargets: {vt}, Structure, wall"])


# Inheriting families: a thin child that inherits a parent family template and overrides ONLY the main
# warhead to add a PhysicalState. Keeps the parent's Versus + warhead key.
# {name: (parent, PhysicalStateName, PhysicalStateScale, levels)}.
# Cryo and Inferno were promoted to BLEND_FAMILIES below so they get their own Versus averages.
INHERIT_FAMILIES = {
}


def emit_inherit_family(name, parent, psn, pss, levels):
    """A full family that reuses the parent's ladder and adds a PhysicalState to the main + %-twin."""
    parent_cfg = WEAPONS[parent]
    order16 = build_order(parent_cfg[0], parent_cfg[1])
    vt = valid_targets(parent_cfg[2])
    dt = FAMILY_DAMAGE_TYPES.get(name)
    return family(name, order16, vt, levels, profile_family=parent,
                  **({"damage_types": dt} if dt else {}))


# Blend families: a NEW family whose Versus is the per-armor AVERAGE of parent families, plus a
# multi-state. Plasma = Flame x Chemical Versus + Temperature 150 + Corrosion 150 ("as close as possible
# to the flame + chemical combo"). {name: (parents, {StateName: Scale}, levels)}.
BLEND_FAMILIES = {
    "Plasma": (["Flame", "Chemical"], {"Temperature": _m(0.50), "Corrosion": _m(0.50)}, L3),
    # Thermobaric = fuel-air incendiary blast: the per-armor AVERAGE of Demolition + Concussion +
    # Flame ("demolition + concussion + fire"). Heat = Flame 300 / 3 parents = 100 (per-parent-average
    # rule, Plasma-consistent). Collapses the thermobaric frankenstein weapons onto one warhead.
    "Thermobaric": (["Demolition", "Concussion", "Flame"], {"Temperature": _m(1 / 3)}, L3),
    # Quantum = high-tech energy blend: per-armor AVERAGE of Railgun + Laser + Tesla (Heavy-only
    # parents extrapolated to L/M via the level step). Heat = Laser's 225 / 3 parents = 75 (only Laser
    # contributes a meter; Plasma-consistent per-parent averaging). EMP auto-scales via IntegrityScale
    # 33 (Tesla = 1/3 parents, FAMILY_INTEGRITY_SCALE); the ExtraDamage chip stays per-weapon.
    "Quantum": (["Railgun", "Laser", "Tesla"], {"Temperature": _m(0.25)}, L3),
    # Element + delivery blends (maintainer 2026-08-10): per-armor AVERAGE of the element family and the
    # delivery family + the element's meter / 2 parents (150). FIRE = anti-light -> pairs with HE delivery
    # (better vs infantry/buildings); CHEMICAL = anti-armor -> pairs with AP delivery (better vs armor).
    "CannonFire":  (["Flame", "CannonHE"],    {"Temperature": _m(0.50)}, L3),
    "MissileFire": (["Flame", "MissileHE"],   {"Temperature": _m(0.50)}, L3),
    "CannonChem":  (["Chemical", "CannonAP"], {"Corrosion": {"Light": 20, "Medium": 33, "Heavy": 50}}, L3),
    "MissileChem": (["Chemical", "MissileAP"],{"Corrosion": {"Light": 20, "Medium": 33, "Heavy": 50}}, L3),
    # Waveforce = a resonant energy weapon: "a bit like a mix of the plasma warhead and the
    # quantum warheads" (maintainer 2026-08-16), adopted for the Japanese energy rifles —
    # which inherit `^WaveforceBulletWarhead` and were never railguns — and for the Protoss
    # photon cannons ("the protoss photon cannons should behave like the waveforce").
    #
    # Declared as the five UNDERLYING primitives rather than as a blend-of-blends, because
    # the blend machinery averages PARENT FAMILIES and nesting would need the parents built
    # first. Plasma = Flame+Chemical, Quantum = Railgun+Laser+Tesla, so the union is exact;
    # only the weighting differs (20% each here vs 25/25/16.7/16.7/16.7 for a true 50/50 of
    # the two blends). The thermal half gives it anti-infantry reach, the coherent-energy
    # half gives armour piercing and the anti-shield coupling.
    #
    # Meters follow the documented per-parent-average rule, same as Quantum's comment above:
    # Temperature = (Flame 300 + Laser 225) / 5 parents = 105; Corrosion = (Chemical 300) / 5 = 60.
    # BULLET blends (maintainer 2026-08-22): *"BulletFire = Bullet x Flame, BulletHE = Bullet x
    # Demolition, BulletThermobaric = Bullet x Thermobaric, BulletTesla = Bullet x Tesla"*. These
    # are the small-arms payload rounds — incendiary, explosive and electrified ammunition — and
    # they give the ~17 Incendiary* weapons and Volkov's electrified rounds a real family instead
    # of a plain Bullet warhead. The blend machinery does the rest: the Versus profile averages the
    # parents, and blend_shape() crosses their SHAPES, so an incendiary bullet gets a small fire
    # (geometric mean of Bullet 100 and Flame 1200 = 346) rather than half a flamethrower.
    #
    # Thermobaric is itself a blend, so it is expanded to its own primitives and Bullet is repeated
    # three times to keep the split 50/50 — the same repetition-as-weight convention PhotonCannon
    # uses. Meters follow the per-parent-average rule: Flame's 300 over 2 parents = 150 for
    # BulletFire, over 6 parents = 50 for BulletThermobaric.
    "BulletFire":  (["Bullet", "Flame"],      {"Temperature": _m(0.50)}, L3),
    "BulletHE":    (["Bullet", "Demolition"], None, L3),
    "BulletThermobaric": (["Bullet", "Bullet", "Bullet", "Demolition", "Concussion", "Flame"],
                          {"Temperature": _m(1 / 6)}, L3),
    "BulletTesla": (["Bullet", "Tesla"],      None, L3),
    # BulletChem = Bullet x Chemical (maintainer 2026-09-02, for the Hydralisk W24 collapse):
    # "a new BulletChem that is like Bullet x Chemical so it's more similar to what it was
    # before but more damage against infantry and aircraft with a little bit damage against
    # tanks from the chemical side". It is the BULLET delivery member of the element+delivery
    # Chem set, alongside CannonChem and MissileChem, and it exists because HydraSpit stacked
    # ^SmallArms (Bullet) + ^LightChemicalWeapon + ^LightMissile + ^ArrowWeapon: no single
    # existing family reproduces a corrosive small-arms round, so collapsing it to plain
    # Chemical moved every ground matchup (see docs/design/W24_COLLAPSE_REVIEW.md).
    # Corrosion follows the CHEM convention, not the Bullet-blend one. CannonChem and
    # MissileChem ramp {Light 20, Medium 33, Heavy 50}; the Bullet blends use the flat
    # per-parent average _m(0.50) = 50. The two AGREE at Heavy (Chemical 100 over 2
    # parents), so the ramp is the same rule with a level curve, and being the third member
    # of the Chem set outranks being the fifth member of the Bullet set.
    "BulletChem":  (["Bullet", "Chemical"],
                    {"Corrosion": {"Light": 20, "Medium": 33, "Heavy": 50}}, L3),
    "Waveforce": (["Flame", "Chemical", "Railgun", "Laser", "Tesla"],
                  {"Temperature": _m(0.35), "Corrosion": _m(0.20)}, L3),
    # PhotonCannon = the maintainer's 3-way — Waveforce 25% / CannonHE 25% / MissileAA 50% — and
    # DELIBERATELY WITHOUT METERS (2026-08-18: *"a Waveforce x ... combo but without the physical
    # states"* … *"use a 3 way: waveforce x cannonHE x MissileAA"* … *"the photon cannon should
    # NOT be better against air than against ground"*). The resonant quarter gives anti-shield
    # coupling and anti-infantry reach, the HE quarter the ground punch, the AA half the air
    # defence. It neither burns nor corrodes — no Temperature, no Corrosion — which also makes it
    # the first family whose price is pure damage, with nothing for E2 to weight.
    #
    # ⭐ THE TARGET IS PARITY, and the weighting is what achieves it. Measured air/ground ratios:
    #
    #     equal thirds (Wave/HE/AA)      0.88   air WORSE than ground — fails the brief
    #     Wave x AA 50/50                0.99   parity, but Fighter sits at 95, below baseline
    #     Wave x AA 1/3 : 2/3            1.11   air-LED — overshot, and shipped once by mistake
    #     Wave 25 / HE 25 / AA 50        1.01   ⭐ parity with every row healthy
    #
    # ⚠ Equal thirds fails for a specific reason worth keeping: `CannonHE` is anti-air HOSTILE
    # (Fighter 79, Helicopter 51, Spaceship 43), so one AA share cannot cancel it. Doubling the
    # AA parent is what buys the ground punch back WITHOUT tipping into an AA-led ladder.
    #
    # ⭐ THE REPEATED PARENTS ARE THE WEIGHTING, not a typo. `blend_versus` averages over the
    # LIST, so 5 Waveforce primitives : 5 CannonHE : 10 MissileAA is exactly 25/25/50 — a
    # weighted blend of a blend and two primitives, which the machinery cannot express any other
    # way (it averages PARENT FAMILIES, and a blend-of-blends would need the parents built first
    # — see Waveforce above).
    "PhotonCannon": (["Flame", "Chemical", "Railgun", "Laser", "Tesla"]
                     + ["CannonHE"] * 5 + ["MissileAA"] * 10, {}, L3),
    # Inferno = a Flame×Prism heatray: thermo-led (mostly fire), but delivered as a coherent
    # energy beam so REFLECTOR still helps. Ground-only, thin spread, FireDeath.
    "Inferno": (["Flame", "Prism"], {}, L3),
    # Cryo = a Laser×Prism coldray: coherent energy delivery that freezes. Mostly energy-field
    # coupling, some thermal load, and a small kinetic share from cryogenic embrittlement.
    # Air-capable (Laser parent), thin spread, negative Temperature scaling.
    # Nuclear delivery blends (A1b): the nuclear family is Super-only, so expanding it to L/M/H
    # in WEAPONS makes it available as a blend parent while keeping it hand-tuned (not emitted).
    "CannonNuke":  (["Nuclear", "CannonHE"], {}, L3),
    "MissileNuke":  (["Nuclear", "MissileAP"], {}, L3),
    # Tesla/Quantum thermobaric missile blends (A1b). Expanded to primitives for the generator.
    "MissileTesla":   (["Tesla", "MissileAP"], {}, L3),
    "CannonTesla":    (["Tesla", "CannonAP"], {}, L3),
    "MissileQuantum": (["Railgun", "Laser", "Tesla"] + ["MissileAP"] * 3, {"Temperature": _m(0.125)}, L3),
    "MissileThermobaric": (["Demolition", "Concussion", "Flame"] + ["MissileHE"] * 3, {"Temperature": _m(0.17)}, L3),
    "Cryo": (["Laser", "Prism"], {}, L3),
    # ⭐ CRYO DELIVERY BLENDS (maintainer 2026-08-22): *"we do need to create those new like
    # CannonCryo, BulletCryo, MissileCryo"* plus *"a cryo explosion which is demolition x cryo
    # for the heavy bombs that carry the cryo load"*. They exist because a cryo weapon whose
    # OTHER guns do not freeze is diluted at the ACTOR level (audit_meter_dilution) — the fix is
    # to give every gun on a cryo unit a cryo family, not to hand-crank one weapon's Scale.
    #
    # ⭐ THE DELIVERY HALF IS AP AND HE TOGETHER, by ruling: *"use an in between blend of HE and
    # AP so it fits with both versions"*. Cryo does not fit the documented FIRE→HE / CHEM→AP
    # split — freezing both embrittles armour AND controls soft targets — and the weapons prove
    # it: `SheridanCannon` is already `CannonAP_Light + CannonHE_Medium`, so either pure choice
    # would have changed its role. Averaging both cannon halves keeps it.
    #
    # Cryo is itself a blend, so it is expanded to its primitives (Laser + Prism) and the
    # delivery side is listed twice — the repetition-as-weight convention PhotonCannon and
    # BulletThermobaric already use. 2 Cryo primitives : 2 delivery = exactly 50/50, with the
    # delivery half split 25/25 between AP and HE.
    #
    # Meter: the per-parent-average rule over the TOP-LEVEL halves, which is how MissileQuantum
    # (Quantum 0.25 → 0.125) and MissileThermobaric (Thermobaric 1/3 → 0.17) are derived —
    # Cryo's -2.00 over 2 halves = -1.00. NOT over the four primitives: Laser's meter is
    # POSITIVE (it heats), so deriving from the expanded list would flip the sign of a cryo
    # weapon. The explicit dict is what keeps that from happening.
    "BulletCryo":     (["Laser", "Prism", "Bullet", "Bullet"],
                       {"Temperature": _m(-1.00)}, L3),
    "CannonCryo":     (["Laser", "Prism", "CannonAP", "CannonHE"],
                       {"Temperature": _m(-1.00)}, L3),
    "MissileCryo":    (["Laser", "Prism", "MissileAP", "MissileHE"],
                       {"Temperature": _m(-1.00)}, L3),
    # FlakCryo — the AA cell of the cryo grid (maintainer 2026-08-23: the cryo upgrade is
    # GLOBAL for RA1 Allies, "this is the same for bullets, cannons, missiles, bombs, etc").
    # Three Allies weapons resolve to Flak_Medium and had no cryo cell to swap to:
    # APCGunAllies, APCGunAllies_AA and zsu_23. Flak is doubled to hold the 50/50 against
    # the two-primitive Cryo half, exactly as BulletCryo doubles Bullet.
    #
    # ⚠ Sniper deliberately gets NO cell. It is not a generator family (it is a hand-made
    # ^Warhead_Sniper_Light, which is why verify_generator_sync accepts it as an exception),
    # so a SniperCryo would mean promoting Sniper to a family first and re-ranking every
    # ladder. DESIGN §11c's reuse test settles it: a cryo sniper round IS a cryo bullet, so
    # Colt45 maps to BulletCryo. Reuse beats a new family that only exists for the label.
    "FlakCryo":       (["Laser", "Prism", "Flak", "Flak"],
                       {"Temperature": _m(-1.00)}, L3),
    # ⭐ CryoBlast = THE CRYO SIBLING OF THERMOBARIC (maintainer 2026-08-22): *"change the
    # DemolitionCryo into a new thing: CryoBlast (which is like a cryo explosion) and it
    # combines Demolition x Concussion x Cryo … It should increase the spread a bit and also
    # make the versus values feel more like a detonation"*. Confirmed on all three counts.
    #
    # Same construction as `Thermobaric` (Demolition + Concussion + Flame) with Cryo in the
    # element slot, so the two are exact siblings: the fire blast and the cold blast. EQUAL
    # THIRDS, and Cryo expands to two primitives, so Demolition and Concussion are each listed
    # twice to hold the 1/3 : 1/3 : 1/3 split.
    #
    # ⭐ CONCUSSION IS WHAT MAKES IT AN EXPLOSION, and it is the biggest single lever in the
    # whole shape table: radius 2100 (the widest of any family) on a SEVEN-point curve
    # (100, 72, 50, 32, 18, 8, 0), i.e. a shockwave that still does half damage at half its
    # radius. Measured against the DemolitionCryo it replaces:
    #
    #     radius   345 -> 630 (+83%)      Spread 86 -> 105
    #     falloff  100,59,32,14,0  ->  100,72,50,32,19,9,0
    #     Versus   spread 1.90x -> 1.84x — FLATTER, which is the detonation feel: it gives up
    #              anti-soft-target discrimination (Wood/None/Steel -3..-8) and gains the
    #              vehicle rows (Scout/Light/Medium/Heroic +6..+8). A shaped charge picks a
    #              target; a blast does not.
    #
    # Carries the cryo weapons whose delivery IS the explosion — `RapierBombsCryo` (a pure
    # `Demolition_Heavy` today), and the `155mmBastionCryo` / `155mmCryo` artillery shells.
    # Meter: Cryo's -200 over 3 top-level halves = -67, the Thermobaric derivation exactly.
    "CryoBlast": (["Laser", "Prism", "Demolition", "Demolition", "Concussion", "Concussion"],
                  {"Temperature": _m(-2 / 3)}, L3),
}
# Fixed emission order for a blend (it has no single light/heavy direction).
BLEND_ARMOR_ORDER = ["None", "Flak", "Plate", "Heroic", "Scout", "Light", "Medium", "Heavy",
                     "Superheavy", "Wood", "Steel", "Concrete", "Fighter", "Bomber", "Helicopter", "Spaceship"]


def _family_main_pct(pname, level):
    """(main_dict, pct_dict) armor -> value for a standard family at a level (incl Shield).

    Reads the measured profile through the same path `family()` does, so a blend
    (Plasma, Thermobaric, Quantum, the Fire*/Chem* pairs, Storm) averages the
    parents' REAL profiles and cannot drift from what the parents themselves emit.
    """
    bl, d, air, lv = WEAPONS[pname]
    order = build_order(bl, d)
    step, mfloor, ptop = LEVELS[level]
    pfloor = ptop - 15
    main = reference_main(pname, order, level) or table(order, step, 100, mfloor, 100 + mfloor)
    # Blends average their PARENTS' profiles, and averaging their parents' Shield rows would
    # average the physics too — a Plasma (Flame+Chemical) would inherit a kinetic Shield.
    # Recompute from the blend's OWN rank instead, same single source as everything else.
    sv = shield_for(pname, level, main)
    if sv is not None:
        main = [("Shield", sv)] + [(a, v) for a, v in main if a != "Shield"]
    return (dict(main), dict(table(order, 1, ptop, pfloor, ptop + pfloor)))


def blend_versus(parents):
    """-> function(level) -> (main_rows, pct_rows) averaging the parents' Versus per armor."""
    def fn(level):
        mains, pcts = zip(*(_family_main_pct(p, level) for p in parents))
        n = len(parents)
        keys = ["Shield"] + BLEND_ARMOR_ORDER
        return ([(a, sum(m[a] for m in mains) // n) for a in keys],
                [(a, sum(p[a] for p in pcts) // n) for a in keys])
    return fn


# Storm = Ixian Tesla + Magic superweapon blend (maintainer 2026-08-10). The SUPER tier is the 3-way
# AVERAGE of Tesla_Super main + its full ExtraDamage chip + the new Magic — for BOTH the flat main and
# the %-twin. Every lower tier is that SUPER profile SCALED by WC[level]/WC[Super]. The %-magnitude lives
# in PercentageVersus while PercentageScale derives magnitude from the main Damage.
STORM_LEVELS = ["Light", "Medium", "Heavy", "Super"]


def storm_versus(level):
    tc_main, tc_pct = _family_main_pct("Tesla", "Super")
    extra, ef = CHIPS_LEVEL[("Tesla", "Super")], CHIP_FLOOR["Tesla"]
    keys = ["Shield"] + BLEND_ARMOR_ORDER
    base_main = {a: (tc_main[a] + extra.get(a, ef) + MAGIC_MAIN["Super"]) // 3 for a in keys}
    base_pct = {a: (tc_pct[a] + extra.get(a, ef) + MAGIC_PCT["Super"]) // 3 for a in keys}
    f = WC[level] / WC["Super"]                     # Super 1.0, Heavy .833, Medium .667, Light .5
    return ([(a, int(base_main[a] * f)) for a in keys],
            [(a, int(base_pct[a] * f)) for a in keys])


def _generate():
    argv = sys.argv[1:]
    if "--list" in argv:
        for nm, (bl, d, air, lv) in WEAPONS.items():
            print(f"{nm:11s} {macro_summary(bl):26s} dir={d:5s} air={str(air):5s} {','.join(lv)}")
        sys.exit(0)
    if "--orders" in argv:
        for nm, (bl, d, air, lv) in WEAPONS.items():
            if isinstance(bl, str) and bl in SPECIAL_MODE:
                extra = (", ".join(f"{x}:{FLAT_VALUES[x]}" for x in lv) if bl == "FLAT"
                         else "%-Versus " + ", ".join(f"{x}:{MAGIC_PCT[x]}" for x in lv))
                print(f"\n{nm:11s} [{macro_summary(bl)}] air={air}\n   {extra}")
                continue
            order = build_order(bl, d)
            print(f"\n{nm:11s} [{macro_summary(bl)}] dir={d} air={air}")
            print("   " + " > ".join(order))
        sys.exit(0)
    wanted = {a.lower() for a in argv if not a.startswith("--")}
    print("# GENERATED by gen_weapon_template.py (two-level ordering law). DO NOT hand-edit rows.")
    print("# Sidecar WeaponClass entries for docs/balance/weapon_classes.yaml:")
    for nm, (bl, d, air, lv) in WEAPONS.items():
        if wanted and nm.lower() not in wanted:
            continue
        for level in lv:
            print(f"#   ^Warhead_{nm}_{level}: {WC[level]}")
    for nm, (parent, psn, pss, lv) in INHERIT_FAMILIES.items():
        if wanted and nm.lower() not in wanted:
            continue
        for level in lv:
            print(f"#   ^Warhead_{nm}_{level}: {WC[level]}  (inherits {parent})")
    for nm, (parents, states, lv) in BLEND_FAMILIES.items():
        if wanted and nm.lower() not in wanted:
            continue
        for level in lv:
            print(f"#   ^Warhead_{nm}_{level}: {WC[level]}  (blend of {'+'.join(parents)})")
    if not wanted or "storm" in wanted:
        for level in STORM_LEVELS:
            print(f"#   ^Warhead_Storm_{level}: {WC[level]}  (Tesla+Magic superweapon blend)")
    print()
    for nm, (bl, d, air, lv) in WEAPONS.items():
        if wanted and nm.lower() not in wanted:
            continue
        if nm in HAND_TUNED:  # hand-authored; never regenerate (would revert)
            continue
        vt = valid_targets(air, ground_only=(nm == "Melee"))
        physics = shape_for(nm)
        spreads = FAMILY_SPREADS.get(nm) or (physics[0] if physics else (400, 600, 800, 1000))
        falloffs = FAMILY_FALLOFFS.get(nm) or (physics[1] if physics else DEFAULT_FALLOFFS)
        if isinstance(bl, str) and bl in SPECIAL_MODE:
            print(f"###### {nm}: {macro_summary(bl)} ######")
            print(family(nm, None, vt, lv, mode=SPECIAL_MODE[bl], spreads=spreads, falloffs=falloffs))
            print()
            continue
        order = build_order(bl, d)
        dt = FAMILY_DAMAGE_TYPES.get(nm)
        print(f"###### {nm}: {macro_summary(bl)} ({d}, air={air}) ######")
        print(family(nm, order, vt, lv, spreads=spreads, falloffs=falloffs, **({"damage_types": dt} if dt else {})))
        print()
    for nm, (parent, psn, pss, lv) in INHERIT_FAMILIES.items():
        if wanted and nm.lower() not in wanted:
            continue
        print(f"###### {nm}: inherits {parent} + PhysicalState {psn} {pss} ######")
        print(emit_inherit_family(nm, parent, psn, pss, lv))
        print()
    for nm, (parents, states, lv) in BLEND_FAMILIES.items():
        if wanted and nm.lower() not in wanted:
            continue
        # ⚠ Air capability is INHERITED FROM THE PARENTS, not assumed. This used to be a flat
        # `valid_targets(False)` with the note "plasma is a ground weapon (like flame/chem)" —
        # true of Plasma and false as a rule: `PhotonCannon` exists precisely to be the Protoss
        # AIR defence, and a hardcoded ground-only target list would have shipped an AA family
        # that cannot shoot at aircraft.
        #
        # The test is a WEIGHTED SHARE, not "any parent": a blend can engage air when at least a
        # third of what it is made of can. "Any" would have promoted `Waveforce` on the strength
        # of one Laser in five parents — an unrelated family silently gaining AA. A third is also
        # exactly what the repeated-parent weighting expresses, so it reads off the list directly.
        air_share = (sum(1 for p in parents if p in WEAPONS and WEAPONS[p][2]) / len(parents)
                     if parents else 0)
        vt = valid_targets(air_share >= 1 / 3)
        dt = FAMILY_DAMAGE_TYPES.get(nm)
        states_note = f"+ PhysicalStates {states}" if states else "no PhysicalStates"
        # The blend's SHAPE crosses its parents' shapes exactly as its Versus crosses their
        # profiles — see blend_shape(). Without this the 17 blend families kept the old
        # one-curve-per-level default while every primitive moved to its physics curve.
        bphysics = shape_for(nm)
        bspreads = FAMILY_SPREADS.get(nm) or (bphysics[0] if bphysics else (400, 600, 800, 1000))
        bfalloffs = FAMILY_FALLOFFS.get(nm) or (bphysics[1] if bphysics else DEFAULT_FALLOFFS)
        print(f"###### {nm}: blend of {'+'.join(parents)} + {states_note} ######")
        print(family(nm, None, vt, lv, versus_override=blend_versus(parents), physical_states=states,
                     spreads=bspreads, falloffs=bfalloffs,
                     **({"damage_types": dt} if dt else {})))
        print()
    if not wanted or "storm" in wanted:
        print("###### Storm: Tesla_Super + Magic + TeslaSuperExtraDamage/5 (Super-anchored, scaled down) ######")
        sphysics = shape_for("Storm")
        print(family("Storm", None, valid_targets(False), STORM_LEVELS,
                     versus_override=storm_versus,
                     spreads=sphysics[0], falloffs=sphysics[1],
                     damage_types="Prone100Percent, TriggerProne, ElectricityDeath, Tesla"))
        print()



if __name__ == "__main__":
    # TWO-PHASE generation. Phase 1 emits every family independently (per-family logic,
    # which is all `shield_for` can see) with Shield in RAW centi-units; phase 2 compresses
    # the finished set onto [100, 400] and reassigns so no two templates share a value.
    # Both the band and uniqueness are properties of the whole SET, so neither can be
    # decided while generating one family at a time — and deriving the band here each run
    # is what keeps it from going stale when the profiles move (as S1 just did).
    import io
    from contextlib import redirect_stdout
    import shield_uniqueness
    _buf = io.StringIO()
    with redirect_stdout(_buf):
        _generate()
    sys.stdout.write(shield_uniqueness.apply(
        _buf.getvalue(), SHIELD_FLOOR_TARGET, SHIELD_CEIL_TARGET))
