#!/usr/bin/env python3
"""audit_three_way_split.py — a weapon fires ONE main warhead. Measured on the RESOLVED node.

    python tools/audit/audit_three_way_split.py

Maintainer 2026-08-22, looking at `IxianCombatTankCannon`: *"has 2 projectiles and 2 effects and
2 warheads and then the d2k cannon on top? can we please finish the 3 way split so there are no
more multiple of those things there?"*

⛔ THIS AUDIT WAS WRONG ONCE — read why before changing it back.

The first version counted, in the SOURCE yaml, any `^Template` that inherited a `^Warhead_*` while
also carrying its own `Warhead@` node, called it a "legacy bundle", and flagged every weapon using
one. That produced 393, and 393 was both too high and too low:

  TOO HIGH — it cannot tell an OVERRIDE from an ADDITION. `^D2K_Cannon` inherits
    `^Warhead_CannonHE_Medium` and writes `Warhead@CannonHE_Medium:` — the SAME key, so it tunes
    the single warhead it already has. That is a correctly-formed 3-way intermediate with local
    damage tuning, and it was being reported as a bundle.

  TOO LOW  — it only looked at a weapon's DIRECT inherits. A weapon that picks up three warheads
    through an intermediate, which itself pulled a legacy pile-up, resolved to a mess the source
    scan never saw.

The property we actually care about is a RESOLVED one — "how many damaging warheads does this
weapon fire when the engine builds it" — so that is what this measures now. Same lesson as
`cameo-resolved-not-source`: a child's node is usually a MODIFICATION of an inherited one.

WHAT COUNTS AS A VIOLATION. One main damaging warhead per weapon. These are NOT violations and
are excluded deliberately, because the design mandates them:

  *_Percentage    the percentage twin, the paired half of the main (W18 / the AreaDamage fold)
  *_ExtraDamage   the twin law — an ExtraDamage chip at 50% of the main is the documented pattern
                  for Tesla / Laser / Railgun upgrade variants
  *_Concrete      DamagesConcrete, the concrete-slab mechanism; folding it away is its own task
  *_ExtraRepair   the healer equivalent of the twin

⚠ RATCHET, LOWER-ONLY. Never raise it to make the suite green — that is how the old number hid a
threefold undercount for a day.

EXIT CODE: 1 above the ratchet.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import io
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from miniyaml import Ruleset  # noqa: E402
from intentional_composites import (  # noqa: E402
    intentional_composite,
    reviewed_fingerprints,
    validated_reviewed_predicate,
)

# Weapons resolving to >1 main damaging warhead when this was measured (2026-08-28). LOWER ONLY.
# 1190 -> 1178 the same day: a MEASUREMENT fix, not converted weapons. See FRIENDLY_FIRE below.
# Hydralisk was deliberately restored as an exact four-profile composite after
# its single-main fold caused a live 1.6x-2.38x ground-damage regression.
RAW_SPLIT_BASELINE = 340
SPLIT_BASELINE = 114
INTENTIONAL_COMPOSITES = reviewed_fingerprints()
REPORT = pathlib.Path(__file__).resolve().parents[2] / "docs/audit/latest/three_way_split.md"

# Warhead types that inflict damage on a normal target. Everything else (CreateEffect,
# LeaveSmudge, GrantExternalCondition, SpawnActor, GlowImpact, ...) is cosmetic or utility and
# belongs to the ^Effect_ layer, so it is not counted here.
MAIN_DAMAGE_TYPES = {"AreaDamage", "SpreadDamage", "HealthPercentageDamage", "TargetDamage"}

# Key fragments marking a warhead as a DESIGNED companion of the main rather than a second main.
COMPANION_MARKERS = ("Percentage", "ExtraDamage", "ExtraRepair", "Concrete")

# ⛔ A FRIENDLY-FIRE TWIN IS NOT A SECOND MAIN. It is the SAME main at reduced damage aimed at
# allies (the twin law: FF = 50% of main), so counting it doubled a correctly-split weapon.
# `physical_state_price` has excluded these from day one via ValidRelationships; this audit
# did not, and the effect was visible in its own output: `Heal` and `MedicHeal` — healing
# weapons, one warhead plus its ally-only twin — were reported as "stacked mains".
#
# BOTH tests are needed. 356 twins declare an Ally-only `ValidRelationships`, but 24 more are
# only identifiable by name (`Warhead@GrenadeFriendlyFire`), and the legacy Grenade/Shrapnel
# templates are exactly where those live. Either test alone leaves twins counted as mains.
FRIENDLY_FIRE_MARKER = "FriendlyFire"


def is_friendly_fire(wh) -> bool:
    """An ally-only twin of the main warhead, by relationship or by name."""
    if FRIENDLY_FIRE_MARKER in wh.key:
        return True
    rel = (wh.get("ValidRelationships") or "").strip()
    return "Ally" in rel and "Enemy" not in rel


def main_warhead_nodes(resolved):
    """Positive, non-companion damage warheads a resolved weapon fires.

    OpenRA's DamageWarheadInfo.Damage defaults to zero.  Missing, zero,
    negative, or symbolic Damage values therefore cannot make a weapon a
    stacked-main violation.  This predicate is shared with the collapse
    planner so the survey and its direct-armament subset cannot drift again.
    """
    out = []
    for wh in resolved.children:
        if not (wh.key.startswith("Warhead@") or wh.key == "Warhead"):
            continue
        if (wh.value or "").strip() not in MAIN_DAMAGE_TYPES:
            continue
        if any(m in wh.key for m in COMPANION_MARKERS):
            continue
        if is_friendly_fire(wh):
            continue
        damage = wh.get("Damage")
        try:
            if damage is None or int(str(damage).strip()) <= 0:
                continue
        except ValueError:
            continue
        out.append(wh)
    return out


def main_warheads(resolved) -> list[str]:
    """Names of the warheads accepted by :func:`main_warhead_nodes`."""
    return [wh.key.replace("Warhead@", "") for wh in main_warhead_nodes(resolved)]


def run(rs: Ruleset) -> int:
    reviewed_predicate = validated_reviewed_predicate(rs, main_warhead_nodes)
    hist = collections.Counter()
    combos = collections.Counter()
    rows: list[tuple[str, list[str]]] = []
    reviewed: list[tuple[str, list[str]]] = []

    for name in sorted(rs.weapons):
        if name.startswith("^"):
            continue
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        mains = main_warheads(resolved)
        hist[len(mains)] += 1
        if len(mains) > 1:
            if reviewed_predicate(name, mains):
                reviewed.append((name, mains))
            else:
                rows.append((name, mains))
                combos[tuple(sorted(mains))] += 1

    total = sum(hist.values())
    raw_count = len(rows) + len(reviewed)
    print(f"# audit_three_way_split — {raw_count} raw stacked weapons; "
          f"{len(rows)} remain unreviewed\n")
    print(f"  {hist[1]:5d}  correct — exactly one main warhead")
    print(f"  {hist[0]:5d}  none — utility / effect-only weapons")
    print(f"  {raw_count:5d}  RAW STACKS — structural inventory")
    print(f"  {len(reviewed):5d}  reviewed — exact intentional composites")
    print(f"  {len(rows):5d}  UNREVIEWED — classification backlog\n")

    print("  mains  weapons")
    for k in sorted(hist):
        if k > 1:
            print(f"  {k:5d}  {hist[k]:5d}")

    print(f"\n{len(combos)} distinct stacked combinations; the 20 most common:\n")
    print("| count | combination |\n|---|---|")
    for combo, n in combos.most_common(20):
        print(f"| {n} | {' + '.join(combo)} |")

    print(f"\nReviewed exact composites ({len(reviewed)}):\n")
    if reviewed:
        for name, mains in reviewed:
            print(f"- `{name}`: {' + '.join(sorted(mains))}")
    else:
        print("_none_")

    raw_over = raw_count > RAW_SPLIT_BASELINE
    review_over = len(rows) > SPLIT_BASELINE
    over = raw_over or review_over
    print(f"\n{'FAIL' if over else 'WARN'} raw {raw_count}/{RAW_SPLIT_BASELINE}; "
          f"unreviewed {len(rows)}/{SPLIT_BASELINE}")
    if raw_over:
        print("**A weapon just gained a second main warhead.** Split it into the 3 layers instead "
              "of raising RAW_SPLIT_BASELINE.")
    elif review_over:
        print("**A reviewed fingerprint drifted or a new stack needs classification.**")
    else:
        print("Lower raw ratchets only for structural consolidation; lower the unreviewed "
              "ratchet only for exact reviewed decisions.")
    return 1 if over else 0


def rendered(rs: Ruleset) -> tuple[str, int]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        status = run(rs)
    return stream.getvalue(), status


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text, status = rendered(Ruleset(pathlib.Path(".")))
    if args.write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {REPORT}")
        return status
    if args.check:
        if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != text:
            print(f"FAIL {REPORT} is stale; run with --write")
            return 1
        print(f"PASS {REPORT} matches live rules")
        return status
    print(text, end="")
    return status


if __name__ == "__main__":
    sys.exit(main())
