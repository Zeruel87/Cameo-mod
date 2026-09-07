#!/usr/bin/env python3
"""audit_missile_role_family.py - a missile's FAMILY must match the role it flies.

Maintainer ruling, 2026-09-07:

    "if the unit is using the weapon against ground it will be missile he, and if
     the weapon is anti air then missile aa, but if the same missile is used
     against both then only missile AP. And missile he should never be used for
     anti air - that one is for anti ground rockets only."

So the weapon's own `ValidTargets` decides the family, and there is exactly one
right answer per role:

    ground only  (Ground / Water, no Air)  ->  ^Warhead_MissileHE_*
    air only     (Air, no Ground / Water)  ->  ^Warhead_MissileAA_*
    both                                   ->  ^Warhead_MissileAP_*

This is not cosmetic. The three families are different DELIVERIES, not three
labels for one rocket - `PHYSICS_SHAPES` in `gen_weapon_template.py` gives
`MissileAA` a proximity fuze (Spread 300, `Falloff 100, 70, 30, 0`, so a blast
radius of 900) precisely because an anti-air missile has to detonate NEAR a
moving target, while `MissileAP` is a shaped-charge direct hit (Spread 64,
`Falloff 100, 0`). Putting an AP rocket on an AA mount does not merely retag it,
it removes the mechanism that lets it connect.

  R1 GROUND-ONLY weapon flying an AA or dual family      -> should be MissileHE
  R2 AIR-ONLY weapon flying an AP or HE family           -> should be MissileAA
  R3 DUAL-ROLE weapon flying an HE or AA family          -> should be MissileAP
  R4 MissileHE reachable against Air - the hard "never"  (subset of R2 + R3)

All four are LOWER-ONLY ratchets. R4 is the one the ruling states as absolute;
it is reported separately because it is the clause to clear first.

⚠ Only the three role families are judged. `MissileChem`, `MissileCryo`,
`MissileFire`, `MissileNuke`, `MissileQuantum`, `MissileTesla` and
`MissileThermobaric` are BLENDS carrying a payload identity, and the ruling did
not cover them - they are counted and shown, never failed.

Usage: python tools/audit/audit_missile_role_family.py [--list] [--code R1]
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import miniyaml
from report import h1, h2, table

# Measured 2026-09-07 on aec54e103. LOWER ONLY - never raise one to make a
# batch pass; a batch that raises a row has broken more than it fixed.
R1_BASELINE = 51
R2_BASELINE = 33
R3_BASELINE = 47
R4_BASELINE = 50

DAMAGE_TYPES = {"SpreadDamage", "AreaDamage", "TargetDamage"}
# the halves of one main, not mains themselves (DESIGN 11b.1)
TWIN_MARKERS = ("percentage", "friendlyfire", "extradamage")

ROLE_FAMILY = {"ground": "MissileHE", "air": "MissileAA", "both": "MissileAP"}
ROLE_FAMILIES = set(ROLE_FAMILY.values())

# Warhead@MissileAP_MediumFlatCompatibility -> MissileAP
FAMILY_RE = re.compile(r"^Warhead@(Missile[A-Za-z]*?)_(?:Light|Medium|Heavy|Super)")


def weapon_role(node) -> str:
    """Ground / air / both, from the weapon's own ValidTargets.

    The engine default is `Ground, Water` (WeaponInfo.cs:116), so a weapon that
    never writes ValidTargets is ground-only.
    """
    raw = next((c.value for c in node.children if c.key == "ValidTargets"), None)
    targets = {t.strip() for t in (raw or "Ground, Water").split(",") if t.strip()}
    air = "Air" in targets
    ground = bool(targets & {"Ground", "Water"})
    if air and ground:
        return "both"
    return "air" if air else "ground"


def main_families(node) -> set[str]:
    """The Missile* families of this weapon's MAIN damage warheads."""
    families = set()
    for child in node.children:
        if not child.key.startswith("Warhead@"):
            continue
        if (child.value or "").strip() not in DAMAGE_TYPES:
            continue
        if any(m in child.key.lower() for m in TWIN_MARKERS):
            continue
        match = FAMILY_RE.match(child.key)
        if match:
            families.add(match.group(1))
    return families


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true",
                    help="print every offending weapon, not just the counts")
    ap.add_argument("--code", default="", help="restrict --list to one code")
    args = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parents[2]
    rs = miniyaml.Ruleset(root)

    findings = collections.defaultdict(list)   # code -> [(weapon, role, family)]
    blends = collections.Counter()
    conforming = 0
    scanned = 0

    for name in sorted(rs.weapons):
        if name.startswith("^"):
            continue
        try:
            node = rs.resolve_weapon(name)
        except Exception:
            continue
        if node is None:
            continue
        families = main_families(node)
        if not families:
            continue
        scanned += 1
        role = weapon_role(node)
        want = ROLE_FAMILY[role]
        for family in sorted(families):
            if family not in ROLE_FAMILIES:
                blends[family] += 1
                continue
            if family == want:
                conforming += 1
                continue
            code = {"ground": "R1", "air": "R2", "both": "R3"}[role]
            findings[code].append((name, role, family))
            if family == "MissileHE" and role in ("air", "both"):
                findings["R4"].append((name, role, family))

    print(h1("audit_missile_role_family - the family must match the role"))
    rows = []
    for code, desc, base in (
        ("R1", "ground-only weapon not flying MissileHE", R1_BASELINE),
        ("R2", "air-only weapon not flying MissileAA", R2_BASELINE),
        ("R3", "dual-role weapon not flying MissileAP", R3_BASELINE),
        ("R4", "MissileHE reachable against Air (hard rule)", R4_BASELINE),
    ):
        count = len(findings[code])
        rows.append([code, desc, str(count), str(base),
                     "PASS" if count <= base else "FAIL"])
    print(table(["code", "check", "count", "ratchet", ""], rows))

    print(f"\n{scanned} concrete weapon(s) fly a Missile* main; "
          f"{conforming} already match their role.\n")

    if blends:
        print(h2("payload blends - counted, never failed"))
        print(table(["family", "weapons"],
                    [[f, str(n)] for f, n in sorted(blends.items())]))
        print("\nThe ruling covers the three ROLE families only. A blend carries a\n"
              "payload identity (chem, cryo, nuke) that outranks the role tag.\n")

    if args.list:
        for code in ("R1", "R2", "R3", "R4"):
            if args.code and args.code.upper() != code:
                continue
            if not findings[code]:
                continue
            print(h2(f"{code} - {len(findings[code])} weapon(s)"))
            print(table(["weapon", "role", "flies", "should fly"],
                        [[w, r, f, ROLE_FAMILY[r]]
                         for w, r, f in sorted(findings[code])]))
            print()

    over = [c for c, b in (("R1", R1_BASELINE), ("R2", R2_BASELINE),
                           ("R3", R3_BASELINE), ("R4", R4_BASELINE))
            if len(findings[c]) > b]
    if over:
        print(f"\n**FAIL: {', '.join(over)} above ratchet.** "
              "Lower a baseline as the conversion progresses; never raise one.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
