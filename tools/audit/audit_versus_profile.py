#!/usr/bin/env python3
"""audit_versus_profile.py — guard DESIGN §12.0h / §12.0c / §12.0d on the LIVE profiles.

    python tools/audit/audit_versus_profile.py

Three binding maintainer rulings had NO guard at all — only `gen_weapon_template.py` implemented
them, so nothing checked that what the generator intends is what the tree actually carries:

  §12.0h  THE MEAN-100 LAW (2026-08-16) — every family's MAIN warhead has its 16 armor rows
          normalised to arithmetic MEAN 100. This is what makes `K` SHAPE-ONLY and `Damage` the
          sole magnitude knob, so a drifted mean is a HIDDEN price multiplier.
  §12.0d  THE CLASS TILT — each LEVEL tilts toward one end of every armor ladder, and
          *"the tilt MUST NEVER reorder a ladder ... it can never invert"*.
          ⚠ The guarantee is WITHIN a ladder. `None` is INF and `Superheavy` is VEH, so
          comparing them is a CROSS-ladder relation the tilt is DESIGNED to change — a Light
          tilt deliberately raises infantry relative to superheavy vehicles. A first version
          of this audit compared None vs Superheavy and reported 4 families "inverting"; that
          was a false positive. The real invariant is direction WITHIN each ladder.
  spread  Target band 2x-8x (aim 4x) between a profile's highest and lowest armor row.

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

# Measured 2026-08-22 through the resolver. LOWER ONLY.
MEAN_OFFENDERS_BASELINE = 2      # Nuclear_Super + Sniper_Light, both HAND_TUNED
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
DERIVED_ARMORS = ("Heroic", "Airborne")
LEVELS = ("Light", "Medium", "Heavy", "Super")
COMPANION = ("Percentage", "ExtraDamage", "ExtraRepair", "Concrete",
             "Effect", "ShieldHit", "Glow", "Smudge")
MEAN_LO, MEAN_HI = 95.0, 105.0
SPREAD_LO, SPREAD_HI = 2.0, 8.0


def profiles() -> dict[tuple[str, str], dict[str, float]]:
    """{(family, level): {armor: versus}} for every `^Warhead_<Family>_<Level>` MAIN warhead."""
    rs = Ruleset(ROOT)
    out: dict[tuple[str, str], dict[str, float]] = {}
    for name in rs.weapons:
        if not name.startswith("^Warhead_"):
            continue
        family, _, level = name[len("^Warhead_"):].rpartition("_")
        if level not in LEVELS or not family:
            continue
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        for wh in resolved.children:
            if not wh.key.startswith("Warhead@") or any(c in wh.key for c in COMPANION):
                continue
            versus = we.versus_of(wh)      # ⭐ the project's reader, not a hand parser
            if versus:
                out[(family, level)] = versus
            break
    return out


def armor_rows(profile):
    return {k: v for k, v in profile.items() if k not in NON_ARMOR}


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

    mean_bad, spread_bad, flips = [], [], []

    for key, prof in sorted(data.items()):
        rows = armor_rows(prof)
        if not rows:
            continue
        mean = statistics.mean(rows.values())
        if not (MEAN_LO <= mean <= MEAN_HI):
            mean_bad.append((key, mean, key in HAND_TUNED))

    for family in families:
        level = next((l for l in LEVELS if (family, l) in data), None)
        if level is None or family in FLAT_BY_DESIGN:
            continue
        # HAND_TUNED profiles are authored by hand and never generated, so the
        # generated laws do not apply to them.
        if (family, level) in HAND_TUNED:
            continue
        rows = [v for v in armor_rows(data[(family, level)]).values() if v > 0]
        if not rows:
            continue
        spread = max(rows) / min(rows)
        if not (SPREAD_LO <= spread <= SPREAD_HI):
            spread_bad.append((family, spread))

        levels = [l for l in LEVELS if (family, l) in data]
        for ladder_name, rungs in LADDERS.items():
            dirs = {d for d in (ladder_direction(data[(family, l)], rungs) for l in levels) if d}
            if len(dirs) > 1:
                flips.append((family, ladder_name, sorted(dirs)))

    print(f"# audit_versus_profile — {len(data)} MAIN profiles across {len(families)} families\n")

    print(f"## §12.0h MEAN-100 — {len(data) - len(mean_bad)} of {len(data)} conform\n")
    for key, mean, hand in mean_bad:
        tag = " _(HAND_TUNED — generator skips it, expected)_" if hand else " **UNEXPECTED**"
        print(f"  {key[0]}_{key[1]}  mean {mean:.1f}{tag}")

    print(f"\n## spread band {SPREAD_LO:.0f}x-{SPREAD_HI:.0f}x (target 4x) — "
          f"{len(families) - len(spread_bad) - len(FLAT_BY_DESIGN)} in band\n")
    for family, spread in sorted(spread_bad, key=lambda r: r[1]):
        why = "too FLAT" if spread < SPREAD_LO else "too SHARP"
        print(f"  {family:14s} {spread:6.2f}x   {why}")
    print(f"  _(flat by design, excluded: {', '.join(sorted(FLAT_BY_DESIGN))})_")

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

    unexpected_mean = [m for m in mean_bad if not m[2]]
    fail = (len(unexpected_mean) > 0
            or len(spread_bad) > SPREAD_OFFENDERS_BASELINE
            or len(flips) > FLIP_BASELINE)
    print(f"\n{'FAIL' if fail else 'WARN'} "
          f"mean {len(mean_bad)}/{MEAN_OFFENDERS_BASELINE} ({len(unexpected_mean)} unexpected) · "
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
