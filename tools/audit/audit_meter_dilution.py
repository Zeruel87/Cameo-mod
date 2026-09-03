#!/usr/bin/env python3
"""audit_meter_dilution.py — actors whose physical state comes from only SOME of their guns.

    python tools/audit/audit_meter_dilution.py

A physical-state meter fills from the damage of the warheads that FEED it, but the target dies
to the actor's WHOLE output. When one armament carries the state and the others do not, the
effect lands far later than that weapon's own `fill_ratio` says, and nothing in the pricing sees
it: `physical_state_price.fed_share` models exactly this dilution WITHIN a weapon and stops at
the weapon boundary.

    dilution = the actor's whole damage / the state weapon's damage

⚠ That is the ACTOR-level factor ONLY. The obvious formula — meter-feeding damage over the
actor's total — double-counts, because `fed_share` already prices the dilution INSIDE the
state weapon. Measured that way this audit reported 81 actors and scored `cobra.steel` at
5.20x on a ONE-gun loadout, where there is by construction nothing to dilute across.

`SheridanMissilesCryo`'s extreme hand-set Scale is a COMPENSATION for this, not an outlier —
which is why measuring it per-weapon says it is over-charged while the actor says otherwise.

⛔ THE MODEL IS "ARMAMENTS THAT CAN FIRE TOGETHER", AND GETTING IT WRONG IS THE WHOLE DIFFICULTY.

Two earlier measurements were wrong in opposite directions and both looked reasonable:

  * counting EVERY `Armament` reported 170 actors and gave each RA2 IFV variant 10.92x. An IFV
    carries 42 armaments, each gated on a distinct `ifv-<passenger>` condition, so exactly ONE
    is ever active. They are not diluted at all.
  * collapsing only NEGATION pairs (`X` / `!X`) fixed the Sheridan (3 weapons, not 4) but left
    the IFVs, because `ifv-flaktrooper` and `ifv-gi` are not each other's negation.

So this audit counts only what it can PROVE fires together: the UNCONDITIONAL armaments, plus
the state-carrying armament itself. A condition-gated non-state gun is never counted against a
state gun, because nothing here can show the two conditions are simultaneously satisfiable.
That makes the result a LOWER BOUND — an actor listed here is definitely diluted; an actor
absent from it may still be, through a condition pair this cannot evaluate.

DEFERRED BY MAINTAINER RULING: the IFV class ("the IFV kind of things need their own logic so
you should skip them") — they fall out of the model above on their own, and `--variants` lists
the actors that reach it that way so the deferral stays visible instead of silent.

EXIT CODE: 1 above the ratchet.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
from miniyaml import Ruleset            # noqa: E402
import physical_state_price as psp      # noqa: E402

# Measured 2026-08-22 through the resolver. LOWER ONLY, as carriers are reworked so that every
# weapon on a state unit feeds the same meter (the maintainer's preferred fix).
# ⚠ NOT comparable to the 58 an earlier scratchpad script produced: that one mixed the
# actor-level factor together with the intra-weapon `fed_share` the pricing already sees.
DILUTION_BASELINE = 32


def meter_damage(rs, weapon: str) -> tuple[float, float]:
    """(total main damage, damage that feeds a meter) for one weapon.

    `psp.damage_split` only sees DAMAGE-SCALED bindings, because those are the ones whose
    `fed_share` it needs. A discrete `ApplyPhysicalState` warhead carries no damage of its own
    yet still fills the bar per hit, so a weapon holding one counts as fully feeding — exactly
    how `fill_ratio` prices it (`fed_share` is 1.0 for `kind == "apply"`).
    """
    total, fed = psp.damage_split(rs, weapon)
    if fed:
        return total, fed
    node = rs.resolve_weapon(weapon)
    if node is not None:
        for wh in node.children:
            if not wh.key.startswith("Warhead"):
                continue
            if (wh.get("PhysicalStateName") or "").strip():
                return total, total
    return total, 0.0


def armaments(node) -> list[tuple[str, str, str]]:
    """[(key, weapon, condition)] for one resolved actor."""
    out = []
    for c in node.children:
        if c.key != "Armament" and not c.key.startswith("Armament@"):
            continue
        w = (c.get("Weapon") or "").strip()
        if w:
            out.append((c.key, w, (c.get("RequiresCondition") or "").strip()))
    return out


def measure(rs):
    """(diluted rows, condition-gated actors the model refuses to judge)."""
    rows, variant_only = [], []
    for actor in sorted(rs.actors):
        if actor.startswith("^"):
            continue
        node = rs.resolve(actor)
        if node is None:
            continue
        keys = {c.key for c in node.children}
        if "Health" not in keys or "Valued" not in keys:
            continue

        arms = armaments(node)
        if len(arms) < 2:
            continue
        split = {w: meter_damage(rs, w) for _k, w, _c in arms}
        carriers = {w for w, (_t, f) in split.items() if f > 0}
        if not carriers:
            continue

        if not any(not c for _k, _w, c in arms):
            # every gun is condition-gated: the IFV shape. Nothing here can judge it.
            variant_only.append((actor, len(arms), len(carriers)))
            continue

        # the provable simultaneous loadout: everything unconditional, plus the state gun
        loadout = {w for _k, w, c in arms if not c} | carriers
        total = sum(split[w][0] for w in loadout)
        # ⚠ ONLY THE ACTOR-LEVEL FACTOR. Comparing `fed` to `total` here measures the meter's
        # share of the actor's whole output, which DOUBLE-COUNTS the dilution inside the state
        # weapon itself — `physical_state_price.fed_share` already prices that half. Doing it
        # that way reported 81 actors and put `cobra.steel` at 5.20x on a ONE-gun loadout,
        # where there is by definition nothing to dilute across. What the pricing cannot see
        # is only the damage of the OTHER guns:
        #
        #     priced ratio  ∝ carrier_total / fed          (fed_share, already modelled)
        #     true ratio    ∝ actor_total  / fed
        #     missing       =  actor_total / carrier_total  <- this, and nothing else
        carrier_total = sum(split[w][0] for w in carriers & loadout)
        if carrier_total <= 0 or total <= 0:
            continue
        dilution = total / carrier_total
        if dilution < 1.001:
            continue
        rows.append((actor, len(loadout), len(carriers & loadout),
                     carrier_total / total, dilution))

    rows.sort(key=lambda r: -r[4])
    return rows, variant_only


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--variants", action="store_true",
                    help="also list the condition-gated (IFV-shaped) actors the model skips")
    ap.add_argument("--all", action="store_true", help="list every diluted actor, not the top 30")
    args = ap.parse_args()

    rs = Ruleset(ROOT)
    rows, variant_only = measure(rs)

    print(f"# audit_meter_dilution — {len(rows)} actors fire a state weapon alongside "
          "unconditional non-state weapons\n")
    print("| actor | guns | with state | state guns' share | dilution |")
    print("|---|--:|--:|--:|--:|")
    for a, n, c, s, d in (rows if args.all else rows[:30]):
        print(f"| `{a}` | {n} | {c} | {100*s:.1f}% | **{d:.2f}x** |")
    if not args.all and len(rows) > 30:
        print(f"\n_({len(rows)-30} more — pass `--all`)_")

    buckets = collections.Counter()
    for _a, _n, _c, _s, d in rows:
        buckets["1.0-1.5x" if d < 1.5 else "1.5-2.0x" if d < 2.0 else
                "2.0-3.0x" if d < 3.0 else "3.0x+"] += 1
    print("\n## distribution\n")
    for k in ("1.0-1.5x", "1.5-2.0x", "2.0-3.0x", "3.0x+"):
        if buckets[k]:
            print(f"- {k}: **{buckets[k]}**")

    print(f"\n## condition-gated actors the model cannot judge — {len(variant_only)}\n")
    print("Every armament is gated, so no two can be shown to fire together. This is the IFV")
    print("shape, DEFERRED by maintainer ruling; it needs a variant-aware model, not a count.")
    if args.variants:
        print("")
        for a, n, c in sorted(variant_only)[:40]:
            print(f"- `{a}` — {n} gated armaments, {c} carry a state")

    fail = len(rows) > DILUTION_BASELINE
    print(f"\n{'FAIL' if fail else 'WARN'} {len(rows)} diluted actors "
          f"(ratchet {DILUTION_BASELINE})")
    if fail:
        print("**A state carrier gained a non-feeding gun.** The fix is to make every weapon on "
              "a state unit feed the same meter, not to raise the ratchet.")
    else:
        print("Lower `DILUTION_BASELINE` as carriers are reworked; never raise it.")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
