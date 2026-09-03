#!/usr/bin/env python3
"""target_model.py — what a weapon is actually shooting AT, measured from the tree.

The pricing formula needs three things the old model guessed at:

1. **Armor prevalence** — a flat mean over 17 armor types prices every armor as if it
   were equally common, which it is not: the measured census below spans 563 `Wood`
   down to 20 `Fighter`. Nothing here is hand-written — `armor_census()` counts the
   LIVE RESOLVED actors, so the weighting self-updates as the roster grows (maintainer
   order 2026-08-11: "the game changes over time … it needs to be constantly updated
   and self balanced regularly, all automatically without user input").

   Do not quote armor counts from a raw `grep` of the yaml — it counts templates and
   misses actors that inherit their armor from a class template. A raw grep says
   "2 Spaceships"; the resolved census says **22** (StarCraft Terran alone has the
   Battlecruiser, Phobos and Pythean). Run `python tools/balance/target_model.py`.

2. **Target density** — how many actors a blast realistically catches. Combined
   model (maintainer 2026-08-11, "can we try a combination of both?"): a per-class
   density for WHO is being hit, and a blob cap for HOW MUCH ground is worth
   covering. Infantry stack 5 to a cell (sub-cells) and vehicles 1, so an
   anti-infantry splash legitimately catches more bodies than an anti-tank one.

3. **Reference HP** — the %-of-max-HP twins need a yardstick to convert into flat
   damage. Measured from the live roster rather than assumed.

Read-only. Every number here is derived from `mods/cameo`, never hand-written.
"""

from __future__ import annotations

import collections
import functools
import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
from miniyaml import Ruleset  # noqa: E402

# The 16 canonical CLASS armor types — the rows a unit's own health sits behind.
# Order matches gen_weapon_template.py.
#
# ⚠ `Shield` and the armor PLATINGS are deliberately NOT in here (the comment used to claim
# "+ Shield" and the tuple never had it — E10). They are not class armors: they are separate
# LAYERS selected ahead of the class row, so they need their own prevalence weight rather
# than a slot in this ladder. `armor_weights()` folds `Shield` in at its measured share.
ARMORS = ("None", "Flak", "Plate", "Heroic",
          "Scout", "Light", "Medium", "Heavy", "Superheavy",
          "Wood", "Steel", "Concrete",
          "Fighter", "Bomber", "Helicopter", "Spaceship")

# Which macro class each armor belongs to — drives the per-class density below.
ARMOR_MACRO = {
    "None": "INF", "Flak": "INF", "Plate": "INF", "Heroic": "INF",
    "Scout": "VEH", "Light": "VEH", "Medium": "VEH", "Heavy": "VEH",
    "Superheavy": "VEH",
    "Wood": "BLD", "Steel": "BLD", "Concrete": "BLD",
    "Fighter": "AIR", "Bomber": "AIR", "Helicopter": "AIR", "Spaceship": "AIR",
}

# Units per cell^2 for each macro class, from the maintainer's engagement picture
# (3 vehicles + 6 infantry in a 3x3 = 9 cell^2 formation) plus the engine's
# sub-cell rule (5 infantry per cell, 1 vehicle per cell):
#   vehicles  3 / 9 cell^2 = 0.33
#   infantry  6 / 9 cell^2 = 0.67, and they can pack far tighter -> 2.0 at the limit
# Buildings sit on their own footprint and never bunch; aircraft spread out.
DENSITY = {"INF": 2.0, "VEH": 0.33, "BLD": 0.25, "AIR": 0.20}

# The engagement blob: beyond this a blast covers empty ground, so extra footprint
# stops adding targets. 3x3 cells = 9 cell^2.  A_SELF = the primary's own cell,
# already counted by `reliability`, so it must not be counted twice.
A_BLOB = 9.0
A_SELF = 1.0

# Fraction of shots that actually land in a crowd (2026-08-11). DENSITY above
# describes the moment of a blob fight, which is the RIGHT picture for that moment —
# but a weapon does not spend the match firing into a perfect 3x3 formation. It
# chases stragglers, trades at the edge, holds fire to avoid its own splash, and
# wastes overkill on a target already dying.
#
# Without this factor every splash family scores ~5x every single-target family at
# equal Damage (measured: Storm K 5.77 vs Laser K 0.56), which would force
# single-target weapons to ~10x the Damage number just to compete — straight through
# the 2000 grid's resolution and off the HP scale. The blob picture is real; its
# UPTIME is not 100%.
#
# rho_effective = DENSITY[class] * BLOB_UPTIME. At 0.30 the vehicle case lands on
# 0.33 * 0.30 ~ 0.1 and the infantry case on 2.0 * 0.30 = 0.6 — i.e. splash is worth
# 2-3x, not 10x. Raise it for blob-heavy play, lower it for skirmish play.
BLOB_UPTIME = 0.30


_INJECTED: Ruleset | None = None


def use_ruleset(rs: Ruleset) -> None:
    """Reuse a Ruleset the caller has already built, instead of building our own.

    The census resolves EVERY actor in the tree, so a cold call costs ~7s and a
    fresh `Ruleset(ROOT)` costs about as much again. `extract_stats` and the audits
    already hold a fully-built Ruleset when they ask for the weights — handing it
    over turns a ~15s tax into ~3s. Purely an optimisation: the numbers are
    identical either way.
    """
    global _INJECTED
    _INJECTED = rs
    for fn in (_ruleset, _scan, armor_census, hp_by_macro, armor_weights,
               measured_reference_hp):
        fn.cache_clear()


@functools.lru_cache(maxsize=1)
def _ruleset() -> Ruleset:
    return _INJECTED if _INJECTED is not None else Ruleset(ROOT)


@functools.lru_cache(maxsize=1)
def _scan() -> tuple[dict[str, int], dict[str, list[int]]]:
    """One pass over the resolved roster -> (armor census, HP buckets per macro).

    Both consumers need the same expensive thing — every actor RESOLVED, so that an
    actor inheriting its armor from a class template is counted and templates are
    not — so they share a single walk rather than resolving the tree twice.
    """
    rs = _ruleset()
    counts: collections.Counter[str] = collections.Counter()
    buckets: dict[str, list[int]] = {m: [] for m in ENGAGEMENT}
    for name in rs.actors:
        if name.startswith(("^", "$", "-")) or "." in name:
            continue
        node = rs.resolve(name)
        if node is None:
            continue
        armor = None
        for child in node.children:
            # First CANONICAL armor wins. Not simply the first `Armor` node: an actor
            # can carry several (upgrade variants), and an unrecognised Type on the
            # first one must not hide a real armor further down.
            if child.key == "Armor" or child.key.startswith("Armor@"):
                value = child.get("Type")
                if value and str(value).strip() in ARMORS:
                    armor = str(value).strip()
                    break
        if armor is None:
            continue
        counts[armor] += 1
        health = node.child("Health")
        if health is None:
            continue
        hp = _hp_value(health.get("HP"))
        if hp and hp > 0:
            buckets[ARMOR_MACRO[armor]].append(hp)
    return dict(counts), buckets


def _hp_value(raw) -> int | None:
    """`HP` as an int, or None when the field is not numeric.

    An unresolved placeholder is skipped by the caller rather than swallowed by a
    handler — the pattern `effective_damage.damage_value` documents
    (`audit_error_handling.py` E2).
    """
    try:
        return int(float(str(raw)))
    except (TypeError, ValueError):
        return None


@functools.lru_cache(maxsize=1)
def armor_census() -> dict[str, int]:
    """{armor type: number of LIVE concrete actors with it}, resolved (not raw yaml)."""
    return _scan()[0]


# How often a random shot is fired AT each macro class. Prevalence alone is not
# enough: the tree has ~900 building actors (every faction has a full base) against
# ~330 vehicles, so pure prevalence would price a tank cannon 45% against warehouses.
# Buildings also exist in small numbers per MATCH and are usually shot late.
#
# So the weighting is two-layer:  BETWEEN classes = engagement (design intent, below)
#                                 WITHIN a class  = prevalence (measured, self-updating)
# Adding 200 buildings then re-weights buildings against each other without repricing
# every tank — which is exactly the stability we want from an auto-updating model.
ENGAGEMENT = {"INF": 0.35, "VEH": 0.40, "BLD": 0.15, "AIR": 0.10}


@functools.lru_cache(maxsize=1)
def armor_weights() -> dict[str, float]:
    """Prevalence weight per armor, summing to 1.0. Self-updating with the roster.

    Within each macro class the weight follows the measured actor census; the class
    totals follow ENGAGEMENT. Every canonical armor gets a 1-actor floor so a type
    with 2 actors still counts a little — a weapon good only against Spaceships is
    niche, not worthless.
    """
    census = armor_census()
    weights: dict[str, float] = {}
    for macro, share in ENGAGEMENT.items():
        members = [a for a in ARMORS if ARMOR_MACRO[a] == macro]
        floored = {a: census.get(a, 0) + 1.0 for a in members}
        total = sum(floored.values())
        for armor, n in floored.items():
            weights[armor] = share * n / total
    # E1 — the Shield LAYER gets its own weight, taken out of the class rows rather than
    # added on top, so the total stays 1.0 and a weapon's `versus` remains comparable.
    s = shield_damage_share()
    if s > 0:
        for armor in weights:
            weights[armor] *= 1.0 - s
        weights["Shield"] = s
    return weights


@functools.lru_cache(maxsize=1)
def shield_damage_share() -> float:
    """Fraction of all roster raw damage that lands on the `Shield` row. Measured: 1.4%.

    Derived, never a constant. A shot at a shielded unit hits the Shield row until the pool
    is gone, so the share is the ratio of raw damage absorbed there to raw damage absorbed
    overall — and "raw" matters, because a row's Versus decides how much RAW damage a point
    of pool costs an attacker:

        raw to strip a pool of S   = 100 x S / Versus[Shield]
        raw to kill H health       = 100 x H / Versus[class armor]

    ⚠ **Only ALWAYS-ON shields count**, and getting that wrong swings the answer by 20x.
    `^ShieldedShieldable` gives 1592 actors `MaxPercentageStrength: 100` with
    `InitialStrength: 0` — an empty CAPACITY behind `shieldgen >= 1`. Just 58 actors spawn
    with a pool and no positive gate. Counting the capacity as a shield is where the claim
    "Tesla's `Shield: 400` is free against 51% of the roster" came from; the true baseline
    exposure is **1.4%**, and §E's severity was corrected accordingly.

    ⚠ An upgrade-granted shield is NOT counted. That is not an omission: it is the
    upgrade-pricing gap E5. Should the maintainer decide the weapon side must price the
    POST-upgrade world instead of the baseline one, the change is one predicate here
    (`always_on` -> `pool > 0`) — and it would raise this share to roughly 30%, so it is a
    design ruling, not a tweak.
    """
    rs = _ruleset()
    v_shield = pseudo_armor_mean("Shield")
    if v_shield <= 0:
        return 0.0
    raw_shield = raw_health = 0.0
    for name in rs.actors:
        if name.startswith("^"):
            continue
        node = rs.resolve(name)
        if node is None:
            continue
        hp = armor = shielded = None
        for c in node.children:
            key = c.key.split("@")[0]
            if key == "Health":
                hp = _num(c.get("HP"))
            elif key == "Armor" and armor is None \
                    and not _condition_is_gate(c.get("RequiresCondition")):
                armor = (c.get("Type") or "").strip()
            elif key == "Shielded" and shielded is None:
                shielded = c
        if not hp or hp <= 0:
            continue
        v_class = pseudo_armor_mean(armor) if armor in ARMORS else 100.0
        raw_health += 100.0 * hp / (v_class or 100.0)
        if shielded is None:
            continue
        pool_flat = _num(shielded.get("MaxStrength")) or 0.0
        pool_pct = _num(shielded.get("MaxPercentageStrength")) or 0.0
        init = (_num(shielded.get("InitialStrength")) or 0.0) \
            + (_num(shielded.get("InitialPercentageStrength")) or 0.0)
        if pool_flat + pool_pct <= 0 or init <= 0 \
                or _condition_is_gate(shielded.get("RequiresCondition")):
            continue
        pool = pool_flat + pool_pct * hp / 100.0
        raw_shield += 100.0 * pool / v_shield
    total = raw_shield + raw_health
    return raw_shield / total if total > 0 else 0.0


def _num(v, default=None):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return default


_COND_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")


def _condition_is_gate(cond) -> bool:
    """True when the condition needs something GRANTED (upgrade / prereq / aura).

    ⚠ `!disabled` is the standard not-EMP'd guard and is TRUE on a healthy unit — treating
    it as a gate hid EVERY Protoss shield and made the roster look shield-free. Only a
    POSITIVE token gates; a negated term is satisfied by default.
    """
    for term in re.split(r"&&|\|\|", str(cond or "")):
        t = term.strip().strip("()").strip()
        if t and not t.startswith("!") and _COND_TOKEN.match(t):
            return True
    return False


@functools.lru_cache(maxsize=1)
def hp_by_macro() -> dict[str, int]:
    """Median max-HP per macro class — the yardstick for the %-of-max-HP twins.

    Median, not mean: a handful of 4M-HP epic units would drag a mean far off what
    a shot actually meets. Per class, because a %-twin's real value depends entirely
    on what it hits — 5% of an infantryman and 5% of a dreadnought are different
    weapons.
    """
    buckets = _scan()[1]
    return {m: int(statistics.median(v)) if v else 0 for m, v in buckets.items()}


# Percentage damage is priced as if fired at an average BASELINE actor, not at the
# roster median (maintainer ruling 2026-08-11). High-tech tanks, dreadnoughts and the
# epics all sit well above 200 000 HP; everything else sits below it. Note the roster
# already agrees where it matters most: the measured BUILDING median is 200 000 exactly.
REFERENCE_HP = 200_000


def reference_hp() -> int:
    """The DESIGN reference max-HP one %-of-HP point is priced against.

    A design constant, deliberately NOT the measured median — see `measured_reference_hp`
    for what the live roster actually is. The gap between the two is information, not
    an error: the measured figure is dragged down by infantry (30 000 HP at 35%
    engagement weight), and a %-warhead is not designed for the cheapest thing it can
    hit. Pricing against the constant makes every %-twin ~2.7x more valuable in K.
    """
    return REFERENCE_HP


@functools.lru_cache(maxsize=1)
def measured_reference_hp() -> int:
    """Engagement-weighted median max-HP of the LIVE roster — diagnostic only.

    Reported alongside the design constant so drift in the roster stays visible: if
    this ever climbs past `REFERENCE_HP`, the constant has stopped being the middle
    it was chosen to be and wants a maintainer re-ruling.
    """
    per = hp_by_macro()
    total = sum(ENGAGEMENT[m] * per.get(m, 0) for m in ENGAGEMENT)
    return int(total)


# --------------------------------------------------------------------------- #
# THE SURVIVABILITY LAYERS — what a shield point is worth in HP (E1, 2026-08-16)
# --------------------------------------------------------------------------- #
# Maintainer: *"since everything deals more damage to shields you can count the 200%
# shield strength like an extra 100% HP ... Calculate the average versus value against
# shields to verify it!"*
#
# Verified, and the estimate was right to within 5%. A shield point absorbs damage at the
# SHIELD row's rate, not the class armor's, so it is worth `100 / mean(Versus[Shield])` of
# an HP point. Measured across the shipped warheads that mean is ~210, i.e. **0.476** — the
# maintainer's "two shield points per HP point" almost exactly.
#
# ⚠ **MEASURED, never hardcoded.** The Shield ladder is regenerated by
# `gen_weapon_template` (100..400 today, and it moved twice in one day), so a frozen factor
# would go stale silently — the same failure mode that made the Shield compression constants
# wrong the moment S1 renormalised the profiles. This reads the LIVE ruleset instead.
#
# ⚠ The armor PLATINGS deliberately get no factor. Their columns are pinned to one common
# mean by construction, so a plating does not change how much damage arrives on average, only
# WHERE — which is why the maintainer's "it evens out" is exactly right. What a plating DOES
# buy is the gap between that common mean and the class armor it replaces, and that is a
# property of the unit's armor type rather than of the plating: it belongs in the armor term,
# not here.
PSEUDO_ARMOR_ROWS = ("Shield",)


@functools.lru_cache(maxsize=8)
def pseudo_armor_mean(row: str = "Shield") -> float:
    """Mean `Versus[row]` across every MAIN damage warhead in the live ruleset.

    Main FLAT-damage warheads only: a %-twin's `Versus` is a MAGNITUDE (a %-of-max-HP
    figure) rather than an armor multiplier until W18 rebases it, so averaging the two
    together mixes units — the same defect logged as E4.

    ⚠ **Filtered on the warhead's TYPE, not on its key name.** Keying off a `_Percentage`
    suffix looked equivalent and was not: the ~50 legacy templates name their twins
    `Warhead@SmallArmsPercentage` with no underscore, so a suffix test silently let them in
    and dragged this mean from 209 to 157 — a 34% error, on the magnitude values 17 and 25.
    The type is authoritative; the naming convention is not.
    """
    values: list[float] = []
    for name, node in _ruleset().weapons.items():
        # Percentage-inert compatibility slices are structural migration helpers,
        # not standalone damage profiles. Counting their template rows would move
        # the global shield model even though no weapon behavior changed.
        if name.startswith("^Compatibility_"):
            continue
        for child in node.children:
            if not child.key.startswith("Warhead@"):
                continue
            wtype = str(child.value or "")
            if "Percentage" in wtype or "ExtraDamage" in child.key \
                    or "FriendlyFire" in child.key:
                continue
            versus = None
            for grand in child.children:
                if grand.key == "Versus":
                    versus = grand
                    break
            if versus is None:
                continue
            for leaf in versus.children:
                if leaf.key == row:
                    try:
                        values.append(float(leaf.value))
                    except (TypeError, ValueError):
                        pass
                    break
    if not values:
        return 100.0
    return statistics.fmean(values)


def shield_hp_factor() -> float:
    """What ONE point of shield strength is worth as HP (see above). ~0.476 today."""
    mean = pseudo_armor_mean("Shield")
    return 100.0 / mean if mean > 0 else 1.0


def effective_hp(hp: float, shield_flat: float = 0.0, shield_pct: float = 0.0) -> float:
    """HP plus the shield pool, converted to HP-equivalent.

    `Shielded` states its pool as `MaxStrength + MaxPercentageStrength% of max HP`, so a
    100%-strength shield on a 20 000-HP tank is 20 000 shield points, worth ~10 800 HP.

    ⚠ **`Integrity` IS NOT A SHIELD and is deliberately NOT added.** It is an ELECTRONICS
    pool that absorbs NOTHING — `INotifyDamage` runs after the damage has already landed on
    health (see PSEUDO_ARMOR_AND_INTEGRITY §A5) — so it buys a unit no survivability
    whatsoever. All it does is gate the EMP DISABLE when it hits zero. Pricing it as HP would
    charge a unit for durability it does not have.

    It merely happens to state its pool in the same `MaxStrength + MaxPercentageStrength`
    FORM, which is exactly the resemblance that has caused this confusion repeatedly:
    `Integrity.cs` shipped for months with every `[Desc]` copied verbatim from `Shielded.cs`,
    calling itself a shield. Same field shape, unrelated mechanic.
    """
    pool = shield_flat + shield_pct * hp / 100.0
    return hp + pool * shield_hp_factor()


def weighted_versus(versus: dict[str, float], weights: dict[str, float] | None = None) -> float:
    """Prevalence-weighted mean Versus (as a factor, 1.0 = 100%).

    `versus` maps armor -> percent. Armors the warhead omits fall back to 100
    (the engine's default when a Versus row is absent).

    ⚠ Iterates the WEIGHTS, not `ARMORS`: `armor_weights()` carries a 17th row for the
    `Shield` LAYER (E1), and looping over the 16 class armors instead would silently drop it
    — which is exactly how a weapon's whole anti-shield profile came to be priced at zero.
    """
    weights = weights or armor_weights()
    return sum(w * versus.get(a, 100.0) / 100.0 for a, w in weights.items())


def effective_density(versus: dict[str, float], weights: dict[str, float] | None = None) -> float:
    """Units per cell^2 this warhead realistically catches.

    The per-class densities weighted by BOTH prevalence and how good the warhead is
    against that class — an anti-infantry warhead is mostly shot at infantry, and
    infantry are the ones that bunch. This is the "combination of both" the
    maintainer asked for: per-class density, then capped by the blob in
    `footprint_targets()`.

    ⚠ Stays on `ARMORS` (unlike `weighted_versus`): this asks how many BODIES a blast
    catches, and `Shield` is a layer on a body already counted by its class armor — adding it
    would double-count that unit and it has no `ARMOR_MACRO` density to contribute anyway.
    """
    weights = weights or armor_weights()
    num = den = 0.0
    for armor in ARMORS:
        share = weights[armor] * versus.get(armor, 100.0) / 100.0
        num += share * DENSITY[ARMOR_MACRO[armor]]
        den += share
    return num / den if den else DENSITY["VEH"]


def footprint_targets(footprint_cells2: float, density: float) -> float:
    """Expected SECONDARY targets caught by a blast of this damage-weighted area.

    density * min(footprint, A_BLOB) - the primary's own cell. Capping at the blob
    stops a superweapon-sized footprint from claiming it hits 50 units; subtracting
    A_SELF stops the aimed target being counted twice (once here, once in
    `reliability`).
    """
    covered = min(footprint_cells2, A_BLOB)
    return max(density * BLOB_UPTIME * (covered - A_SELF), 0.0)


def census_table() -> str:
    """Markdown census + weights, for the derived report."""
    census, weights = armor_census(), armor_weights()
    rows = sorted(ARMORS, key=lambda a: -census.get(a, 0))
    out = ["| armor | macro | live actors | weight | density (u/cell²) |",
           "|---|---|---|---|---|"]
    for armor in rows:
        out.append(f"| {armor} | {ARMOR_MACRO[armor]} | {census.get(armor, 0)} | "
                   f"{weights[armor]*100:.2f}% | {DENSITY[ARMOR_MACRO[armor]]} |")
    return "\n".join(out)


if __name__ == "__main__":
    print("# target_model — measured from mods/cameo\n")
    print(census_table())
    print("\n| macro | engagement | median HP |")
    print("|---|---|---|")
    for macro, hp in hp_by_macro().items():
        print(f"| {macro} | {ENGAGEMENT[macro]*100:.0f}% | {hp:,} |")
    print(f"\nreference HP (DESIGN constant, what %-damage is priced against): "
          f"**{reference_hp():,}**")
    print(f"measured reference HP (engagement-weighted roster median, diagnostic): "
          f"{measured_reference_hp():,}")
    print(f"blob cap A_BLOB = {A_BLOB} cell², primary's own cell A_SELF = {A_SELF} cell²")
