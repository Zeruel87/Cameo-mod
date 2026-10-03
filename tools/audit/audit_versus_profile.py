#!/usr/bin/env python3
"""audit_versus_profile.py — guard DESIGN §12.0h / §12.0c / §12.0d on the LIVE profiles.

    python tools/audit/audit_versus_profile.py

Three binding maintainer rulings had NO guard at all — only `gen_weapon_template.py` implemented
them, so nothing checked that what the generator intends is what the tree actually carries:

  §12.0h  THE MEAN-100 LAW (2026-08-16) — every family's MAIN warhead has its 16 armor rows
          normalised to MEAN 100. This is what makes `K` SHAPE-ONLY and `Damage` the
          sole magnitude knob, so a drifted mean is a HIDDEN price multiplier.
          ⭐ R16 (maintainer, 2026-09-24): the binding measure is now the GEOMETRIC mean —
          *"All versus values of a warhead must always have a geometric mean of 100%"*.
          Geometric is the correct centre for multipliers (a 200/50 pair centres at 100
          geometrically but 125 arithmetically); §12.0j already ruled the regeneration
          normalises geometrically, and R16 makes it the checked law NOW. The arithmetic
          mean is still reported alongside as a drift signal, not a law.
  §12.0d  THE CLASS TILT — each LEVEL tilts toward one end of every armor ladder, and
          *"the tilt MUST NEVER reorder a ladder ... it can never invert"*.
          ⚠ The guarantee is WITHIN a ladder. `None` is INF and `Superheavy` is VEH, so
          comparing them is a CROSS-ladder relation the tilt is DESIGNED to change — a Light
          tilt deliberately raises infantry relative to superheavy vehicles. A first version
          of this audit compared None vs Superheavy and reported 4 families "inverting"; that
          was a false positive. The real invariant is direction WITHIN each ladder.
  spread  R16 (maintainer, 2026-09-24): HARD BOUND 2x–20x (the Versus range itself is
          10%–200%), with the roster's spread distribution a bell curve PEAKING AT 4x–5x —
          2x (super-generalist) and 20x (super-specialist) are the low-occupancy asymptotes,
          legal only as deliberate exceptions. Supersedes R5's 2x–8x band.

⛔ WHY THIS EXISTS — AND WHY IT READS THROUGH THE RESOLVER, NEVER A HAND PARSER.

On 2026-08-22 I measured these laws with a bespoke yaml parser and got every number wrong. The
parser never CLOSED the `Versus:` block, so the `PercentageVersus:` rows that the AreaDamage fold
added inside the SAME warhead node silently overwrote the profile:

    Warhead@Bullet_Light: AreaDamage
        Versus:            None: 200 ... Superheavy 48   <- the real profile
        PercentageVersus:  None: 16  ... Superheavy  1   <- what the parser read

I reported "0 of 125 conform" and "every family violates the spread band". The truth was 123 of
125 and 37 of 42. Every downstream figure — means, spreads, ratios, inversion counts — was
internally consistent and wrong. This audit therefore uses `miniyaml.Ruleset.resolve_weapon` and
`weapon_efficiency.versus_of`, the project's own readers, which cannot make that mistake.

EXIT CODE: 1 above any ratchet.
"""
from __future__ import annotations

import pathlib
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
from miniyaml import Ruleset            # noqa: E402
import weapon_efficiency as we          # noqa: E402
from effective_heaviness import heaviness_of as validated_heaviness

# Measured through the resolver. LOWER ONLY.
MEAN_OFFENDERS_BASELINE = 2      # Nuclear_Super + Sniper_Light, both HAND_TUNED
GMEAN_OFFENDERS_BASELINE = 2     # R16 geomean-100. Was 105 on 2026-09-24 (the tree was
                                 # normalised to ARITHMETIC 100, §12.0h, and AM >= GM put every
                                 # shaped profile at ~88-95 geometric). PAID DOWN 2026-09-25 by
                                 # `mean_normalise` targeting the GEOMETRIC mean + splice --all:
                                 # only the two HAND_TUNED templates remain (Nuclear_Super,
                                 # Sniper_Light). The arithmetic count is now informational.
SPREAD_OFFENDERS_BASELINE = 0    # CLEARED 2026-08-22 by fit_band_floor in gen_weapon_template
                                 # (Nuclear and Sniper excluded: their only level is HAND_TUNED)
FLIP_BASELINE = 0                # CLEARED 2026-08-22 — the blend tiebreak is now family-wide

# The generator skips these entirely, so they are not expected to obey the generated laws.
HAND_TUNED = {("Nuclear", "Super"), ("Sniper", "Light")}
# Flat BY DESIGN — `mean_normalise` special-cases them ("ignores armor").
FLAT_BY_DESIGN = {"Sonic", "Magic"}

NON_ARMOR = {"Shield", "HAZMAT", "COMPOSITE", "BLAST", "REFLECTOR", "ARMOR"}
# The armor LADDERS, from gen_weapon_template.LADDERS. Direction is only meaningful WITHIN one.
LADDERS = {
    "INF": ["None", "Flak", "Plate", "Heroic"],
    "VEH": ["Scout", "Light", "Medium", "Heavy", "Superheavy"],
    "BLD": ["Wood", "Steel", "Concrete"],
    "AIR": ["Fighter", "Bomber", "Helicopter", "Spaceship"],
}
# Mirror of gen_weapon_template.DERIVED_ARMORS (DESIGN §12.0l, 2026-09-26): derived columns are
# functions of the finished profile, so they stay OUT of the MEAN-100 / spread statistics.
# test_derived_armor_types pins the two lists together.
DERIVED_ARMORS = ("Heroic", "FlyingInfantry",
                  "CyborgLight", "CyborgMedium", "CyborgHeavy", "CyborgHeroic",
                  "AntiAirInfantry", "AntiAirVehicle", "AntiAirBuilding",
                  "ShipLight", "ShipMedium", "ShipHeavy", "ShipSuperheavy", "AntiAirShip",
                  "SubmarineLight", "SubmarineHeavy")
LEVELS = ("Light", "Medium", "Heavy", "Super")
COMPANION = ("Percentage", "ExtraDamage", "ExtraRepair", "Concrete",
             "Effect", "ShieldHit", "Glow", "Smudge")
MEAN_LO, MEAN_HI = 95.0, 105.0
# R16: geometric mean of the armor rows = 100; same tolerance as the arithmetic check.
GMEAN_LO, GMEAN_HI = 95.0, 105.0
SPREAD_LO, SPREAD_HI = 2.0, 20.0     # R16 hard bound — the Versus range itself is 10–200%
SPREAD_TARGET_LO, SPREAD_TARGET_HI = 4.0, 5.0   # bell-curve peak (census, not a fail)


BASE_KEY = "Base"      # a level-less continuous-heaviness `^Warhead_<Family>` base


def split_name(tail):
    """(^Warhead_ stripped) -> (family, level) legacy, (family, None) for a level-less
    base, None for a variant — the same census the old rpartition parse produced."""
    family, sep, level = tail.rpartition("_")
    if not sep:
        return (level, None)
    return (family, level) if level in LEVELS else None


def heaviness_active(wh) -> bool:
    """A NEW base is active only with an explicit non-disabled Heaviness scalar (>= 0)."""
    return wh.child("Heaviness") is not None and validated_heaviness(wh) >= 0


def profiles() -> dict[tuple[str, str], dict[str, float]]:
    """{(family, level|Base): {armor: versus}} for every `^Warhead_<Family>_<Level>` MAIN
    warhead plus every ACTIVE level-less base."""
    rs = Ruleset(ROOT)
    out: dict[tuple[str, str], dict[str, float]] = {}
    for name in sorted(rs.weapons):
        if not name.startswith("^Warhead_"):
            continue
        kind = split_name(name[len("^Warhead_"):])
        if kind is None:
            continue
        family, level = kind
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        for wh in resolved.children:
            if not wh.key.startswith("Warhead@") or any(c in wh.key for c in COMPANION):
                continue
            versus = we.versus_of(wh)      # ⭐ the project's reader, not a hand parser
            if versus:
                key = (family, BASE_KEY) if level is None else (family, level)
                if level is None and not heaviness_active(wh):
                    break                  # a disabled sentinel is not an active base
                out[key] = versus
            break
    return out


def armor_rows(profile):
    # Heroic IS one of the 16 rows the law averages (it always was); the §12.0l geometric-mean
    # columns are not — they are exact functions of those rows, added after normalisation.
    return {k: v for k, v in profile.items()
            if k not in NON_ARMOR and (k == "Heroic" or k not in DERIVED_ARMORS)}


def ladder_direction(profile, rungs):
    """'up' if the profile rises along this ladder, 'down' if it falls, None if unjudgeable.

    Derived armors are excluded — `Heroic` is a PRODUCT of two other cells (§12.0b) and is
    recomputed from the finished profile, so it is not an independent rung.
    """
    present = [a for a in rungs if a in profile and a not in DERIVED_ARMORS]
    if len(present) < 2:
        return None
    return "up" if profile[present[-1]] > profile[present[0]] else "down"


def main() -> int:
    data = profiles()
    families = sorted({f for f, _l in data})

    mean_bad, gmean_bad, spread_bad, flips = [], [], [], []
    spread_census = {}        # family -> spread, for the R16 bell-curve census

    for key, prof in sorted(data.items()):
        rows = armor_rows(prof)
        if not rows:
            continue
        mean = statistics.mean(rows.values())
        if not (MEAN_LO <= mean <= MEAN_HI):
            mean_bad.append((key, mean, key in HAND_TUNED))
        # R16 — the binding law is the GEOMETRIC mean. Zero-valued rows (an armor the
        # warhead is flatly immune to) collapse a geomean to 0, so they are counted
        # separately rather than folded into a meaningless ratio.
        positive = [v for v in rows.values() if v > 0]
        zero_rows = len(rows) - len(positive)
        if positive:
            gmean = statistics.geometric_mean(positive)
            if not (GMEAN_LO <= gmean <= GMEAN_HI) or zero_rows:
                gmean_bad.append((key, gmean, zero_rows, key in HAND_TUNED))

    for family in families:
        # A NEW base carries the profile the C# bell actually anchors, so when one
        # exists the band is measured on IT; otherwise the legacy first level.
        level = (BASE_KEY if (family, BASE_KEY) in data
                 else next((l for l in LEVELS if (family, l) in data), None))
        if level is None or family in FLAT_BY_DESIGN:
            continue
        # HAND_TUNED profiles are authored by hand and never generated, so the
        # generated laws do not apply to them — at ANY of their profiles.
        if any((family, l) in HAND_TUNED for l in list(LEVELS) + [BASE_KEY]):
            continue
        rows = [v for v in armor_rows(data[(family, level)]).values() if v > 0]
        if not rows:
            continue
        spread = max(rows) / min(rows)
        spread_census[family] = spread
        if not (SPREAD_LO <= spread <= SPREAD_HI):
            spread_bad.append((family, spread))

        levels = [l for l in LEVELS if (family, l) in data]
        if (family, BASE_KEY) in data:
            levels.append(BASE_KEY)
        for ladder_name, rungs in LADDERS.items():
            dirs = {d for d in (ladder_direction(data[(family, l)], rungs) for l in levels) if d}
            if len(dirs) > 1:
                flips.append((family, ladder_name, sorted(dirs)))

    n_base = sum(1 for f, l in data if l == BASE_KEY)
    print(f"# audit_versus_profile — {len(data)} MAIN profiles across {len(families)} families "
          f"({len(data) - n_base} legacy level + {n_base} level-less base)\n")

    print(f"## §12.0h+R16 MEAN-100 — geometric {len(data) - len(gmean_bad)} of {len(data)} "
          f"conform · arithmetic {len(data) - len(mean_bad)} of {len(data)}\n")
    for key, gmean, zeros, hand in gmean_bad:
        tag = " _(HAND_TUNED — generator skips it, expected)_" if hand else " **UNEXPECTED**"
        zero = f", {zeros} zero rows" if zeros else ""
        print(f"  {key[0]}_{key[1]}  geomean {gmean:.1f}{zero}{tag}")
    if mean_bad and not gmean_bad:
        print("  _(arithmetic offenders only — informational; geometric is the binding law)_")
    for key, mean, hand in mean_bad:
        if not any(k == key for k, _g, _z, _h in gmean_bad):
            tag = " _(HAND_TUNED)_" if hand else ""
            print(f"  {key[0]}_{key[1]}  arithmetic mean {mean:.1f}{tag} — informational")

    print(f"\n## R16 spread hard bound {SPREAD_LO:.0f}x-{SPREAD_HI:.0f}x "
          f"(bell peak {SPREAD_TARGET_LO:.0f}x-{SPREAD_TARGET_HI:.0f}x) — "
          f"{len(families) - len(spread_bad) - len(FLAT_BY_DESIGN)} in bound\n")
    for family, spread in sorted(spread_bad, key=lambda r: r[1]):
        why = "too FLAT" if spread < SPREAD_LO else "too SHARP"
        print(f"  {family:14s} {spread:6.2f}x   {why}")
    print(f"  _(flat by design, excluded: {', '.join(sorted(FLAT_BY_DESIGN))})_")

    # R16 bell-curve census — the DISTRIBUTION of spreads should peak at 4x-5x with
    # 2x and 20x as low-occupancy asymptotes. Reported, not failed: the bell is a
    # population law, and a single outlier family is a design exception, not a bug.
    if spread_census:
        buckets = {"<2x": 0, "2-4x": 0, "4-5x": 0, "5-8x": 0, "8-20x": 0, ">20x": 0}
        for s in spread_census.values():
            if s < 2.0:
                buckets["<2x"] += 1
            elif s < 4.0:
                buckets["2-4x"] += 1
            elif s <= 5.0:
                buckets["4-5x"] += 1
            elif s <= 8.0:
                buckets["5-8x"] += 1
            elif s <= 20.0:
                buckets["8-20x"] += 1
            else:
                buckets[">20x"] += 1
        print(f"\n## R16 spread distribution (target: bell peaking at 4x-5x)\n")
        for label, count in buckets.items():
            bar = "#" * count
            print(f"  {label:>6s}  {count:3d}  {bar}")

    print("")
    print("## §12.0d DIRECTION WITHIN A LADDER - must not change between a family's levels")
    print("")
    if flips:
        print("⛔ The tilt may never reorder a ladder, yet these family/ladder pairs rise at")
        print("   one level and fall at another. A near-FLAT profile has no stable direction,")
        print("   so the fix is the family's spread, not the tilt.")
        print("")
        for family, ladder_name, dirs in flips:
            print("  {:14s} ladder {:4s} {}".format(family, ladder_name, " / ".join(dirs)))
    else:
        print("  OK - every family keeps one direction within every ladder, at every level.")

    unexpected_gmean = [m for m in gmean_bad if not m[3]]
    fail = (len(unexpected_gmean) > GMEAN_OFFENDERS_BASELINE
            or len(spread_bad) > SPREAD_OFFENDERS_BASELINE
            or len(flips) > FLIP_BASELINE)
    print(f"\n{'FAIL' if fail else 'WARN'} "
          f"geomean {len(gmean_bad)}/{GMEAN_OFFENDERS_BASELINE} "
          f"({len(unexpected_gmean)} unexpected) · "
          f"arithmetic {len(mean_bad)}/{MEAN_OFFENDERS_BASELINE} (informational) · "
          f"spread {len(spread_bad)}/{SPREAD_OFFENDERS_BASELINE} · "
          f"orientation flips {len(flips)}/{FLIP_BASELINE}")
    if fail:
        print("**A profile law regressed.** Fix the profile — never raise a ratchet, and never "
              "hand-edit a Versus value (they are generated; `Versus` lives only in ^Warhead_*).")
    else:
        print("Lower the ratchets as profiles are brought onto the laws; never raise them.")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
