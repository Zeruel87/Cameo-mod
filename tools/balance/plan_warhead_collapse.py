#!/usr/bin/env python3
"""plan_warhead_collapse.py — W24: propose ONE damage family per multi-warhead weapon.

Maintainer 2026-08-17: *"the many inherits were funny and intentional at the time they were made
but now we want to have a cleaner design with only one inherit for warheads. Try to find the best
fitting one."*

This writes a REVIEW TABLE and never touches yaml. The family choice is a design judgment, so it
has to be reviewable at a glance — which it is, because the question is not "which of 15 legacy
templates wins" but **"what IS this weapon?"**, and a weapon's name, projectile and firing sound
answer that directly. `wc2dragonFireVisible` fires a Missile projectile with `wc2_axe.aud`, is
named "dragon fire", and pulls in 15 templates: it is a FLAME weapon that accumulated copy-paste.

Confidence is reported per weapon so review effort goes where it is needed:

  HIGH   — already inherits exactly one `^Warhead_<Family>_<Level>`; keep it, drop the rest.
  NAME   — the weapon's own name names the family (fire/flame, laser, tesla, cannon, ...).
  LEGACY — no name signal; inferred from the legacy templates, weighted by how specific each is.
  NONE   — nothing decides it. These are the only ones needing a human ruling.

Usage:
  python tools/balance/plan_warhead_collapse.py                 # full table -> stdout
  python tools/balance/plan_warhead_collapse.py --unresolved    # only what needs a ruling
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from audit_three_way_split import main_warhead_nodes  # noqa: E402
from miniyaml import Ruleset  # noqa: E402

FAMILY_TPL = re.compile(r"^\^Warhead_([A-Za-z]+)_(\w+)$")

# Name tokens -> family. Ordered: the FIRST match wins, so put specific before generic
# ("chaingun" before "gun", "flamethrower" before "flame").
#
# ⚠ `Inferno` is deliberately NOT reachable from a name token. It is not "a fancy flame": the
# board defines it as ("Prism", "Temperature") — a PRISM CHASSIS THAT BURNS, i.e. a heat ray
# (`HeatRayBeam1/2`). Its ladder is FLAT (Scout 121 .. Helicopter 76, span 1.6x) where Flame's
# is SHARP (None 200 .. Concrete 92, span 2.2x), and its Shield row is 263 against Flame's
# 187-203 because it couples to shields as part-energy. A dragon's breath is fuel combustion
# and wants the sharp anti-infantry ladder: Flame. Route a weapon to Inferno by hand, or via an
# explicit `^Warhead_Inferno_*` inherit it already has.
# ⚠⚠ TWO TIERS, AND THE ORDER IS THE WHOLE POINT. A first version had one flat list with
# delivery words mixed in, and it mis-assigned weapons whose name carries BOTH:
#
#   japan_imperialscoutsman_rifle_waveforce -> matched 'rifle'  -> Bullet   (must be Waveforce)
#   ArmoredCarMGWaveforce                   -> matched 'mg'     -> Bullet   (must be Waveforce)
#
# A FAMILY name is a statement about what the weapon does; a delivery word (rifle, cannon, mg)
# only says how it is mounted. So every family token is tried before any delivery token.
NAME_FAMILY_SPECIFIC = [
    ("waveforce", "Waveforce"), ("quantum", "Quantum"), ("plasma", "Plasma"),
    ("prism", "Prism"), ("railgun", "Railgun"),
    ("tesla", "Tesla"), ("lightning", "Tesla"), ("emp", "Tesla"),
    ("laser", "Laser"),
    ("sonic", "Sonic"), ("resonan", "Sonic"),
    ("magic", "Magic"), ("spell", "Magic"), ("arcane", "Magic"),
    ("nuke", "Nuclear"), ("nuclear", "Nuclear"), ("atomic", "Nuclear"),
    ("thermobaric", "Thermobaric"),
    ("cryo", "Cryo"), ("freeze", "Cryo"), ("frost", "Cryo"),
    ("toxic", "Toxic"), ("anthrax", "Toxic"), ("virus", "Toxic"), ("poison", "Toxic"),
    ("chem", "Chemical"), ("acid", "Chemical"), ("corros", "Chemical"),
    ("flamethrow", "Flame"), ("fireball", "Flame"), ("flamer", "Flame"),
    ("napalm", "Flame"), ("incend", "Flame"), ("dragonfire", "Flame"),
    ("flame", "Flame"),
    ("concuss", "Concussion"), ("shrapnel", "Concussion"),
    ("demo", "Demolition"), ("satchel", "Demolition"),
    ("flak", "Flak"),
    ("arrow", "Arrow"), ("catapult", "Arrow"),
    ("sniper", "Sniper"),
]

# Delivery / mounting words. Only consulted when no family token matched.
NAME_FAMILY_GENERIC = [
    ("chaingun", "Bullet"), ("gatling", "Bullet"), ("minigun", "Bullet"),
    ("machinegun", "Bullet"), ("smallarms", "Bullet"), ("shotgun", "Bullet"),
    ("rifle", "Bullet"), ("pistol", "Bullet"), ("mg", "Bullet"),
    ("dragon", "Flame"), ("fire", "Flame"), ("burn", "Flame"),
    ("beam", "Laser"),
    ("grenade", "Concussion"), ("artillery", "Concussion"),
    ("mortar", "Concussion"), ("howitzer", "Concussion"),
    ("melee", "Melee"), ("sword", "Melee"), ("claw", "Melee"), ("axe", "Melee"),
    ("bite", "Melee"), ("punch", "Melee"),
    ("c4", "Demolition"), ("bomb", "Demolition"),
    ("torpedo", "MissileAP"),
    ("cannon", "CannonHE"), ("shell", "CannonHE"),
    ("missile", "MissileHE"), ("rocket", "MissileHE"), ("scud", "MissileHE"),
]

# Decisions already taken, where the NAME is actively misleading. Documented, not guessed.
EXPLICIT = {
    # A photon cannon is not a cannon (memory `cameo-live-dead-weapon-files` / W24 notes):
    # GladiusCannon inherits PhotonCannon and is a Plasma weapon.
    "GladiusCannon": ("Plasma", "photon cannon — Plasma, not a shell-firing cannon"),
}

# Legacy template -> family, for weapons whose NAME says nothing. Specificity weight: a
# template naming one clear family outranks a vague one, so a pileup still resolves.
LEGACY_FAMILY = {
    "^SmallArms": ("Bullet", 3), "^Chaingun": ("Bullet", 3), "^RALightMG": ("Bullet", 2),
    "^RAHeavyMG": ("Bullet", 2),
    "^LaserWeapon": ("Laser", 4), "^TeslaWeapon": ("Tesla", 4),
    "^TeslaChargedWeapon": ("Tesla", 4), "^TSRailgun": ("Railgun", 4),
    "^MagicWeapon": ("Magic", 4), "^SonicWeapon": ("Sonic", 4),
    "^LightFlameWeapon": ("Flame", 4), "^MediumFlameWeapon": ("Flame", 4),
    "^HeavyFlameWeapon": ("Flame", 4),
    "^LightChemicalWeapon": ("Chemical", 4), "^MediumChemicalWeapon": ("Chemical", 4),
    "^HeavyChemicalWeapon": ("Chemical", 4),
    "^NuclearWarhead": ("Nuclear", 5),
    "^TankDestroyerCannon": ("CannonAP", 3), "^MediumCannon": ("CannonHE", 2),
    "^HeavyCannon": ("CannonHE", 2), "^AACannon": ("Flak", 3),
    "^FlakWeapon": ("Flak", 3),
    "^LightMissile": ("MissileHE", 2), "^MediumMissile": ("MissileHE", 2),
    "^HeavyMissile": ("MissileHE", 2), "^HeavyAAWeapon": ("MissileAA", 3),
    "^Grenade": ("Concussion", 2), "^ShrapnelWeapon": ("Concussion", 2),
    "^HeavyBomb": ("Demolition", 2), "^Artillery": ("Concussion", 2),
    "^TSArtilleryWeapon": ("Concussion", 2),
}


def analyse(rs):
    fired = collections.Counter()
    for name in rs.actors:
        if name.startswith("^"):
            continue
        node = rs.resolve(name)
        if node is None:
            continue
        for c in node.children:
            if c.key == "Armament" or c.key.startswith("Armament@"):
                w = c.get("Weapon")
                if w:
                    fired[str(w).strip()] += 1

    rows = []
    for wname in sorted(fired):
        resolved = rs.resolve_weapon(wname)
        local = rs.weapon(wname)
        if resolved is None or local is None:
            continue
        # Use the exact same predicate as the all-concrete split audit.  This
        # table is the direct actor-armament subset of that survey, not a
        # separate flat-damage approximation with accidentally similar totals.
        mains = [(n.key.replace("Warhead@", ""), int(str(n.get("Damage")).strip()))
                 for n in main_warhead_nodes(resolved)]
        if len(mains) < 2:
            continue

        inherits = [str(c.value).strip() for c in local.children
                    if c.key.split("@")[0] == "Inherits" and c.value]
        families = [FAMILY_TPL.match(i).group(1) for i in inherits if FAMILY_TPL.match(i)]
        legacy = [i for i in inherits if i.startswith("^") and not FAMILY_TPL.match(i)]

        proj = resolved.child("Projectile")
        proj_type = str(proj.value) if proj is not None else ""
        report = str(resolved.get("Report") or "")

        family = None
        confidence = "NONE"
        why = ""
        if wname in EXPLICIT:
            family, reason = EXPLICIT[wname]
            confidence, why = "EXPLICIT", reason
        elif len(set(families)) == 1:
            family, confidence = families[0], "HIGH"
            why = f"already inherits ^Warhead_{family}_*"
        else:
            low = wname.lower()
            for tier, label in ((NAME_FAMILY_SPECIFIC, "family"),
                                (NAME_FAMILY_GENERIC, "delivery")):
                for token, fam in tier:
                    if token in low:
                        family, confidence = fam, "NAME"
                        why = f"{label} word '{token}'"
                        break
                if family:
                    break
        if family is None and legacy:
            scored = collections.Counter()
            for lg in legacy:
                if lg in LEGACY_FAMILY:
                    fam, weight = LEGACY_FAMILY[lg]
                    scored[fam] += weight
            if scored:
                top = scored.most_common()
                # A tie is not a decision — say so rather than picking alphabetically.
                if len(top) > 1 and top[0][1] == top[1][1]:
                    confidence = "NONE"
                    why = f"legacy tie: {top[0][0]}/{top[1][0]} both {top[0][1]}"
                else:
                    family, confidence = top[0][0], "LEGACY"
                    why = f"legacy templates score {family}={top[0][1]}"

        rows.append({"weapon": wname, "uses": fired[wname], "mains": len(mains),
                     "sum": sum(b for _t, b in mains),
                     "uniform": len({b for _t, b in mains}) == 1,
                     "family": family, "confidence": confidence, "why": why,
                     "legacy": legacy, "projectile": proj_type, "report": report})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unresolved", action="store_true",
                    help="only the weapons that need a human ruling")
    args = ap.parse_args()

    rows = analyse(Ruleset(ROOT))
    by_conf = collections.Counter(r["confidence"] for r in rows)

    print("# W24 collapse plan — one damage family per weapon")
    print()
    print(f"**{len(rows)}** directly actor-armed multi-main weapons. "
          "**No yaml is touched by this tool.**")
    print()
    print("| confidence | weapons | meaning |")
    print("|---|--:|---|")
    for conf, meaning in (
            ("EXPLICIT", "a decision already taken, because the name is misleading"),
            ("HIGH", "already inherits exactly one `^Warhead_*` family — keep it, drop the rest"),
            ("NAME", "the weapon's own name names the family (family words beat delivery words)"),
            ("LEGACY", "inferred from its legacy templates, weighted by specificity"),
            ("NONE", "**needs a ruling**")):
        print(f"| {conf} | {by_conf.get(conf, 0)} | {meaning} |")
    print()
    uniform = sum(1 for r in rows if r["uniform"])
    print(f"⚠ **{uniform} of {len(rows)}** have every main at the SAME damage — a useful "
          "broadcast fingerprint, not conversion authorization. Preserving the numeric sum does "
          "not preserve armor profile, geometry, relationships, damage types, or separately "
          "rounded percentage damage; every selected cohort still needs those guards.")
    print()

    show = [r for r in rows if r["confidence"] == "NONE"] if args.unresolved else rows
    if args.unresolved:
        print(f"## The {len(show)} needing a ruling")
    else:
        print("## Proposal, per weapon")
    print()
    print("| weapon | uses | mains | sum | -> family | conf | why | projectile |")
    print("|---|--:|--:|--:|---|---|---|---|")
    for r in sorted(show, key=lambda r: (r["confidence"] != "NONE", -r["mains"], r["weapon"])):
        fam = r["family"] or "**?**"
        print(f"| `{r['weapon']}` | {r['uses']} | {r['mains']} | {r['sum']:,} | {fam} | "
              f"{r['confidence']} | {r['why']} | {r['projectile']} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
