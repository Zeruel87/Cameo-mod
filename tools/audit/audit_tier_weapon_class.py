#!/usr/bin/env python3
"""audit_tier_weapon_class.py — does every weapon obey the Tier<->WeaponClass law?

    python tools/audit/audit_tier_weapon_class.py

Maintainer law (2026-08-03, `docs/balance/weapon_classes.yaml` header, memory
`cameo-tier-weaponclass-law`): unit Tech Tier drives WeaponClass drives warhead LEVEL.

    Light 0.75   Medium 1.0   Heavy 1.25   Super 1.5
    T1 -> Light      T2 -> Medium      T3+ -> Heavy      super-weapon unit -> Super

**Between-tier units MIX the two ADJACENT levels.** A between-T1/T2 unit carries
`Bullet_Light + Bullet_Medium`; a T2 elite carries medium + heavy. That mix is the SANCTIONED
encoding of a between-tier unit -- it is NOT a legacy bug, and collapsing it would erase the
unit's tier identity. `^TSDefaultMissile`'s stacked Medium+Light is the canonical example.

⚠ THIS IS THE TRAP THIS AUDIT EXISTS TO PREVENT. Two levels of one family look exactly like a
botched merge, and 79 `Bullet_Light + Bullet_Medium` weapons were once queued for "repair" on
that assumption. What separates a legal mix from a real defect is ADJACENCY and COUNT, not the
mere fact of having two.

WARHEAD BUDGET = TYPES x LEVELS
    TYPES   distinct lore families combined. Normally 1; 2 only for a genuine hybrid
            (a chemical missile = missile + chemical).
    LEVELS  1 when squarely in-tier, 2 when between-tier (adjacent only).
    totals  1 normal | 2 hybrid OR between-tier | 4 ONLY for a hybrid that is ALSO
            between-tier. 4 is the ceiling.

Twins never count toward the budget: `*_Percentage` (the W18 twin), `*_ExtraDamage` (the twin
law), `*_Concrete` (DamagesConcrete) and `*_ExtraRepair`.

WHAT THIS AUDIT CANNOT YET CHECK. Whether a weapon's level matches its OWNING UNIT's tier needs
a tech tier per actor, and `design.tech_tier` is populated on only 393 of 2100 ledger units. The
structural half below is fully computable and is reported as a ratchet; the alignment half is
reported as coverage, not as a pass/fail, until the tier tagging is finished.

EXIT CODE: 1 above the ratchet.
"""
from __future__ import annotations

import collections
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from miniyaml import Ruleset  # noqa: E402

# Structural budget violations when this was written (2026-08-22). LOWER ONLY.
TIER_BASELINE = 48

MAIN_DAMAGE_TYPES = {"AreaDamage", "SpreadDamage", "HealthPercentageDamage", "TargetDamage"}
COMPANION_MARKERS = ("Percentage", "ExtraDamage", "ExtraRepair", "Concrete")

# The level ladder. Adjacency is measured on this order; Trace is a tracer artefact that sits
# below Light and never pairs.
LADDER = ["Light", "Medium", "Heavy", "Super"]
LEVELS = set(LADDER) | {"Trace"}


def main_warheads(resolved) -> list[str]:
    out = []
    for wh in resolved.children:
        if not (wh.key.startswith("Warhead@") or wh.key == "Warhead"):
            continue
        if (wh.value or "").strip() not in MAIN_DAMAGE_TYPES:
            continue
        if any(m in wh.key for m in COMPANION_MARKERS):
            continue
        damage = wh.get("Damage")
        try:
            if damage is not None and int(str(damage).strip()) == 0:
                continue
        except ValueError:
            pass
        out.append(wh.key.replace("Warhead@", ""))
    return out


def parse(w: str):
    """('Bullet','Medium') from 'Bullet_Medium'; None for a LEGACY-named warhead."""
    p = w.split("_")
    return ("_".join(p[:-1]), p[-1]) if len(p) > 1 and p[-1] in LEVELS else None


def adjacent(levels: set[str]) -> bool:
    if not levels <= set(LADDER):
        return False
    idx = sorted(LADDER.index(x) for x in levels)
    return len(idx) == 2 and idx[1] - idx[0] == 1


def main() -> int:
    rs = Ruleset(pathlib.Path("."))
    legal = collections.Counter()
    bad: list[tuple[str, str, list[str]]] = []
    legacy = 0
    shapes = collections.Counter()

    for name in sorted(rs.weapons):
        if name.startswith("^"):
            continue
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        mains = main_warheads(resolved)
        if not mains:
            continue
        parts = [parse(w) for w in mains]
        if any(p is None for p in parts):
            legacy += 1
            continue

        types = {p[0] for p in parts}
        levels = {p[1] for p in parts}
        t, lv = len(types), len(levels)

        if t == 1 and lv == 1:
            legal["1 type, 1 level - squarely in tier"] += 1
        elif t == 1 and lv == 2 and adjacent(levels):
            legal["1 type, 2 ADJACENT levels - between-tier mix"] += 1
        elif t == 2 and lv == 1:
            legal["2 types, 1 level - lore hybrid"] += 1
        elif t == 2 and lv == 2 and adjacent(levels):
            legal["2 types, 2 adjacent levels - hybrid AND between-tier (budget 4)"] += 1
        else:
            if lv > 2:
                why = f"{lv} LEVELS ({'+'.join(sorted(levels))}) - max is 2"
            elif lv == 2 and not adjacent(levels):
                why = f"NON-ADJACENT levels ({'+'.join(sorted(levels))})"
            elif t > 2:
                why = f"{t} TYPES ({', '.join(sorted(types))}) - max is 2"
            else:
                why = f"budget {t}x{lv} exceeds the ceiling"
            bad.append((name, why, mains))
            shapes[why.split(" (")[0]] += 1

    total = sum(legal.values()) + len(bad)
    print(f"# audit_tier_weapon_class — {len(bad)} of {total} classifiable weapons break the "
          f"TYPES x LEVELS budget\n")
    print("LEGAL shapes:")
    for k, v in legal.most_common():
        print(f"  {v:5d}  {k}")
    print(f"\n  {legacy:5d}  weapons skipped — at least one LEGACY-named main warhead "
          f"(no Family_Level), so the budget cannot be judged until they are 3-way split")

    print(f"\nVIOLATIONS by shape:")
    for k, v in shapes.most_common():
        print(f"  {v:5d}  {k}")

    if bad:
        print("\n| weapon | problem | main warheads |\n|---|---|---|")
        for n, why, mains in sorted(bad)[:40]:
            print(f"| {n} | {why} | {', '.join(sorted(mains))} |")
        if len(bad) > 40:
            print(f"\n_({len(bad) - 40} more)_")

    over = len(bad) > TIER_BASELINE
    print(f"\n{'FAIL' if over else 'WARN'} {len(bad)} budget violations (ratchet {TIER_BASELINE})")
    if over:
        print("**A weapon just broke the TYPES x LEVELS budget.** Give it one level, or two "
              "ADJACENT levels if the unit is genuinely between tiers — do not raise the ratchet.")
    else:
        print("Lower `TIER_BASELINE` as weapons are brought onto the law; never raise it.")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
