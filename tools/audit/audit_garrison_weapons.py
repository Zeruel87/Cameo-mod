#!/usr/bin/env python3
"""audit_garrison_weapons.py — DESIGN.md §11 detector (garrison weapons).

  G1 garrison-capable infantry (Passenger CargoType Infantry) with a
     damaging weapon but no `Name: garrisoned` armament — unless listed
     in docs/design/garrison_exceptions.yaml (melee, suicide, casters)
  G2 an Armament@*GARRISON* block without `Name: garrisoned`: it silently
     becomes a second primary (double-fire in the open, mute in bunkers)
  G3 garrisoned armaments never carry a FireDelay
  G4 every infantry must be garrison-accepting (ruling 2026-09-26): a
     buildable inf actor whose resolved `Garrisoner` node is missing or
     whose `GarrisonType` is not `Infantry` is a defect. Pure aircraft
     (Aircraft, no Mobile) are structurally incapable and excluded, and
     vehicle-queue units are exempt (ruling: the G4 law covers units
     BUILT as infantry — `vehicle_queue` in the exceptions file).

Utility-only infantry (defuse kits, capture tools — see UTILITY_WEAPONS)
and units garrisons cannot accept are auto-exempt from G1.
"""

from __future__ import annotations

import pathlib
import re

from audit_weapon_uniqueness import UTILITY_WEAPONS
from cameo_model import Model
from report import h1, h2, table

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXCEPTIONS_FILE = ROOT / "docs/design/garrison_exceptions.yaml"


def load_exceptions() -> tuple[set[str], set[str]]:
    """(all exempt ids, vehicle_queue ids). The vehicle_queue category is
    G4-only (ruling 2026-09-26): units BUILT as vehicles are not covered by
    "all infantry garrison". G1's flat set unchanged."""
    ids: set[str] = set()
    vehicle: set[str] = set()
    cat = ""
    for line in EXCEPTIONS_FILE.read_text(encoding="utf-8-sig").splitlines():
        cm = re.match(r"^([a-z_]+):", line)
        if cm:
            cat = cm.group(1)
        mo = re.match(r"\s*-\s*([\w.\-]+)", line)
        if mo:
            ids.add(mo.group(1).lower())
            if cat == "vehicle_queue":
                vehicle.add(mo.group(1).lower())
    return ids, vehicle


def main() -> int:
    m = Model()
    rs = m.rs
    exceptions, vehicle_exempt = load_exceptions()

    damage_memo: dict[str, bool] = {}

    def deals_damage(wname: str, depth: int = 0) -> bool:
        key = wname.lower()
        if key in damage_memo:
            return damage_memo[key]
        damage_memo[key] = False
        w = rs.resolve_weapon(wname)
        if w is None:
            return False
        subs = []
        for c in w.children:
            if c.key.lower().startswith("warhead"):
                d = c.get("Damage")
                if d is not None:
                    try:
                        if int(d) != 0:
                            damage_memo[key] = True
                            return True
                    except ValueError:
                        pass
                sw = c.get("Weapon")
                if sw:
                    subs.append(sw)
            elif c.key == "Projectile":
                for f in ("AirburstWeapon", "ImpactActorWeapon",
                          "DetonationWeapon"):
                    sw = c.get(f)
                    if sw:
                        subs.append(sw)
        if depth < 4:
            for sw in subs:
                if deals_damage(sw, depth + 1):
                    damage_memo[key] = True
                    return True
        return False

    g1_rows, g2_rows, g3_rows, g4_rows = [], [], [], []
    flyers = 0
    seen: set[str] = set()
    for fac in sorted(f.internal for f in m.real_factions()):
        for lname in sorted(m.buildable_roster(fac)):
            if m.unit_type(lname) != "inf" or lname in seen:
                continue
            seen.add(lname)
            res = rs.resolve(lname)
            if res is None:
                continue

            # G4 (ruling 2026-09-26): ALL infantry can garrison — a garrison
            # must accept every inf actor. Acceptance is Garrisoner.GarrisonType
            # vs Garrisonable.Types (Infantry), NOT Passenger.CargoType (that is
            # the transport system). Pure aircraft (Aircraft, no Mobile) can
            # never CanEnterCell a building — structurally incapable, excluded.
            # Everything else missing Garrisoner/GarrisonType=Infantry is a defect.
            g = res.child("Garrisoner")
            gtype = (g.get("GarrisonType") if g else None) or None
            if gtype != "Infantry" and lname not in vehicle_exempt:
                if res.child("Mobile") is None and res.child("Aircraft") is not None:
                    flyers += 1
                else:
                    qb = res.child("Buildable")
                    g4_rows.append([fac, lname,
                                    (qb.get("Queue") or "?") if qb else "?",
                                    "no Garrisoner" if g is None
                                    else f"GarrisonType={gtype!r}"])
            prim, garr = [], []
            for arm in res.children_named("Armament"):
                w = arm.get("Weapon")
                if not w:
                    continue
                name = (arm.get("Name") or "primary").lower()
                if name == "garrisoned":
                    garr.append(w)
                    if arm.get("FireDelay"):
                        g3_rows.append([fac, lname, arm.key,
                                        arm.get("FireDelay")])
                else:
                    prim.append(w)
                    if "GARRISON" in arm.key.upper():
                        g2_rows.append([fac, lname, arm.key, w])
            if garr or lname in exceptions:
                continue
            p = res.child("Passenger")
            if p is None or (p.get("CargoType") or "Infantry") != "Infantry":
                continue
            combat = sorted({w for w in prim
                             if w.lower() not in UTILITY_WEAPONS
                             and deals_damage(w)})
            if combat:
                g1_rows.append([fac, lname, ", ".join(combat)])

    print(h1("Garrison weapons (DESIGN.md §11)"))
    print(f"exceptions loaded: {len(exceptions)} "
          f"({len(vehicle_exempt)} vehicle_queue → G4-exempt); "
          f"G1 missing {len(g1_rows)}, G2 miswired {len(g2_rows)}, "
          f"G3 fire-delayed {len(g3_rows)}, G4 non-garrisonable {len(g4_rows)} "
          f"({flyers} pure aircraft excluded)\n")
    print(h2(f"G1 — armed garrison-capable infantry without a garrison "
             f"weapon ({len(g1_rows)})"))
    print(table(["faction", "actor", "combat weapons"], g1_rows))
    print(h2(f"G2 — GARRISON-suffixed armament missing Name: garrisoned "
             f"({len(g2_rows)})"))
    print(table(["faction", "actor", "armament", "weapon"], g2_rows))
    print(h2(f"G3 — garrisoned armament with FireDelay ({len(g3_rows)})"))
    print(table(["faction", "actor", "armament", "FireDelay"], g3_rows))
    print(h2(f"G4 — infantry a garrison cannot accept ({len(g4_rows)}) "
           f"[ruling: all infantry garrison, 2026-09-26]"))
    print(table(["faction", "actor", "queue", "reason"], g4_rows))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
