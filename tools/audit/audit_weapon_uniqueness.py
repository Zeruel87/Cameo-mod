#!/usr/bin/env python3
"""audit_weapon_uniqueness.py — DESIGN.md §10 detector (actor uniqueness).

Every armed unit or defense owns its own weapons; no two actors may fire
the identical weapon (identical = same weapon id after resolution).

  W1 weapon fired by >=2 actor families of the SAME faction
  W2 weapon fired by actor families of DIFFERENT factions
     (worst class: cross-faction sameness kills faction identity)
  W3 sharing that only involves weapon-borrowing carriers (IFV-style
     actors whose mechanic is mounting donor units' weapons) — separate
     because the mechanic requires the copy; design may still theme them

Never reported:
  - one actor's own variant family (dotted variants, _sp/_elite/_husk/
    paradrop twins, `x` vs `xbotmg` presets — prefix collapse);
  - the same shared base actor appearing in several factions' rosters;
  - systemic utility weapons (C4, DefuseKit, capture/heal tools);
  - zero-damage targeting dummies (order plumbing, not guns; damage is
    resolved through warhead sub-weapon closure so cluster weapons count).

Findings are balance/design work (propose stat divergence, let design
choose) — this audit never suggests mechanical merges.
"""

from __future__ import annotations

from collections import defaultdict

from cameo_model import Model
from report import h1, h2, table

# systemic mechanics every faction shares by design
UTILITY_WEAPONS = {
    "genericc4", "defusekit", "leechdisinfect", "repair", "heal",
    "healextra", "medikit",
}

# structural variant suffixes from DESIGN.md §1 + legacy paradrop twins
VARIANT_SUFFIXES = (
    "_husk", "_sp", "_r4", "_wild", "_mk2", "_elite", "_ai", "_water",
    "_EMP", "_AA", "_upgraded", "para", ".husk",
)

ARMED_TYPES = {"inf", "veh", "air", "nav", "def"}


def family(lname: str) -> str:
    """Collapse an actor id to its variant-family stem."""
    f = lname.lower()
    if "." in f:                      # dotted variants: e1.gdi, twr.nax2
        f = f.split(".", 1)[0]
    changed = True
    while changed:
        changed = False
        for suf in VARIANT_SUFFIXES:
            if f.endswith(suf) and len(f) > len(suf) + 2:
                f = f[: -len(suf)]
                changed = True
    return f


def merge_prefix_families(fams: set[str]) -> dict[str, str]:
    """Within one weapon's user set, fold `xbotmg` into `x` (AI presets)."""
    out = {}
    for f in fams:
        best = f
        for g in fams:
            if g != f and f.startswith(g) and len(g) < len(best):
                best = g
        out[f] = best
    return out


def main() -> int:
    m = Model()
    rs = m.rs

    damage_memo: dict[str, bool] = {}

    def deals_damage(wname: str, depth: int = 0) -> bool:
        """Nonzero warhead damage anywhere in the sub-weapon closure."""
        key = wname.lower()
        if key in damage_memo:
            return damage_memo[key]
        damage_memo[key] = False          # cycle guard
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

    # weapon -> family -> {actors}; family metadata
    users: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    fam_factions: dict[str, set[str]] = defaultdict(set)
    carrier_fams: set[str] = set()

    for fac in sorted(f.internal for f in m.real_factions()):
        for lname in sorted(m.buildable_roster(fac)):
            if m.unit_type(lname) not in ARMED_TYPES:
                continue
            res = rs.resolve(lname)
            if res is None:
                continue
            fam = family(lname)
            fam_factions[fam].add(fac)
            arms = res.children_named("Armament")
            gated = {a.get("Weapon") for a in arms
                     if a.get("Weapon") and a.get("RequiresCondition")}
            if len(gated) >= 4:           # IFV-style weapon-borrowing carrier
                carrier_fams.add(fam)
            for arm in arms:
                w = arm.get("Weapon")
                if not w or w.lower() in UTILITY_WEAPONS:
                    continue
                if not deals_damage(w):
                    continue              # targeting dummy / pure-effect
                users[w.lower()][fam].add(lname)

    w1_rows, w2_rows, w3_rows = [], [], []
    for w, fams_raw in sorted(users.items()):
        fold = merge_prefix_families(set(fams_raw))
        fams: dict[str, set[str]] = defaultdict(set)
        for f, actors in fams_raw.items():
            fams[fold[f]].update(actors)
        if len(fams) < 2:
            continue
        core = {f for f in fams if f not in carrier_fams}
        actors_of = lambda fs: ", ".join(
            sorted({a for f in fs for a in fams[f]}))
        if len(core) < 2:                 # only a carrier borrows it
            w3_rows.append([w, actors_of(set(fams))])
            continue
        facs = sorted({x for f in core for x in fam_factions[f]})
        per_fac: dict[str, set[str]] = defaultdict(set)
        for f in core:
            for x in fam_factions[f]:
                per_fac[x].add(f)
        same = sorted(x for x, fs in per_fac.items() if len(fs) > 1)
        if same:
            w1_rows.append([w, ", ".join(same), actors_of(core)])
        if len(facs) > 1:
            w2_rows.append([w, str(len(core)), ", ".join(facs),
                            actors_of(core)])

    print(h1("Weapon uniqueness (DESIGN.md §10 — faction identity)"))
    print(f"damaging armament weapons checked: {len(users)}; "
          f"W1 same-faction {len(w1_rows)}, W2 cross-faction {len(w2_rows)}, "
          f"W3 carrier-only {len(w3_rows)}\n")
    print(h2(f"W1 — same faction, distinct actors, identical weapon "
             f"({len(w1_rows)})"))
    print(table(["weapon", "faction(s)", "actors"], w1_rows))
    print(h2(f"W2 — identical weapon across factions ({len(w2_rows)})"))
    w2_rows.sort(key=lambda r: -int(r[1]))
    print(table(["weapon", "families", "factions", "actors"], w2_rows))
    print(h2(f"W3 — shared only with weapon-borrowing carriers "
             f"({len(w3_rows)})"))
    print(table(["weapon", "actors"], w3_rows))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
