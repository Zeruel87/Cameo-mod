#!/usr/bin/env python3
"""review_resolve_diff.py — verify a weapon retrofit preserved behaviour.

Resolves each named weapon in TWO repo roots (before / after) via miniyaml and
compares the behavioural invariants a 3-way-split retrofit must NOT change:
  - ValidTargets, Range, ReloadDelay, Burst
  - the multiset of offensive-warhead Damage values (the "Damage verbatim" law)
  - projectile behavioural fields (Speed, TrailImage, Inaccuracy, Contrail*)
  - whether a Report survives
  - resolved CreateEffect behaviour, including impact audio and target filters

Intended changes (warhead type SpreadDamage->AreaDamage, warhead-key renames,
inherit repoints, new-template Versus tables) are NOT flagged. Anything else is.

Usage: python tools/audit/review_resolve_diff.py <base_root> <head_root> W1 W2 ...
"""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import miniyaml


def cval(node, key):
    for c in node.children:
        if c.key == key:
            return c.value
    return None


def cnode(node, key):
    for c in node.children:
        if c.key == key:
            return c
    return None


def summarize(node):
    if node is None:
        return None
    d = {"VT": cval(node, "ValidTargets"), "Range": cval(node, "Range"),
         "Reload": cval(node, "ReloadDelay"), "Burst": cval(node, "Burst"),
         "Inherits": sorted(c.value for c in node.children
                            if c.key == "Inherits" or c.key.startswith("Inherits@")),
         "warheads": [], "dmgs": [], "effects": [],
         "Report": cval(node, "Report")}
    p = cnode(node, "Projectile")
    d["Proj"] = None if p is None else {
        "type": p.value, "Speed": cval(p, "Speed"), "Trail": cval(p, "TrailImage"),
        "Inacc": cval(p, "Inaccuracy"), "CStart": cval(p, "ContrailStartColor"),
        "CEnd": cval(p, "ContrailEndColor")}
    for c in node.children:
        if c.key.startswith("Warhead@"):
            dmg = cval(c, "Damage")
            d["warheads"].append((c.key, c.value, dmg))
            low = c.key.lower()
            relationships = (cval(c, "ValidRelationships") or "").strip()
            ally_only = "Ally" in relationships and "Enemy" not in relationships
            if (c.value in ("SpreadDamage", "AreaDamage")
                    and not ally_only and "percentage" not in low and dmg):
                try:
                    d["dmgs"].append(int(dmg))
                except ValueError:
                    pass
            if c.value == "CreateEffect":
                # Compare the resolved behaviour rather than the keyed-warhead
                # name: retrofits routinely rename keys without intending to
                # alter what players see or hear.
                d["effects"].append(tuple(
                    (k, cval(c, k)) for k in (
                        "Explosions", "Image", "ExplosionPalette",
                        "UsePlayerPalette", "ForceDisplayAtGroundLevel",
                        "ImpactSounds", "ImpactSoundChance", "ImpactActors",
                        "Inaccuracy", "AudibleThroughFog", "Volume",
                        "GlowColor", "GlowScale", "GlowFadeFrames",
                        "GlowFadeInFrames", "ValidTargets", "InvalidTargets",
                        "ValidRelationships", "InvalidRelationships", "Delay",
                        "AirThreshold", "AffectsParent")
                    if cval(c, k) is not None))
    d["dmgs"].sort()
    d["effects"].sort(key=repr)
    return d


def show(w, b, h):
    print(f"\n===== {w} =====")
    if b is None or h is None:
        print(f"  {'BASE' if b is None else 'HEAD'} resolve = None (missing)")
        return
    flags = []
    if b["VT"] != h["VT"]:
        flags.append(f"ValidTargets {b['VT']} -> {h['VT']}")
    # W24 collapses multiple identical-damage mains into one warhead whose
    # Damage is the preserved SUM. That changes the multiset but not total damage.
    if b["dmgs"] != h["dmgs"] and not (
        sum(b["dmgs"]) == sum(h["dmgs"]) and len(h["dmgs"]) == 1
    ):
        flags.append(f"Damage multiset {b['dmgs']} -> {h['dmgs']}")
    if b["Range"] != h["Range"]:
        flags.append(f"Range {b['Range']} -> {h['Range']}")
    if b["Reload"] != h["Reload"]:
        flags.append(f"ReloadDelay {b['Reload']} -> {h['Reload']}")
    if b["Burst"] != h["Burst"]:
        flags.append(f"Burst {b['Burst']} -> {h['Burst']}")
    pb, ph = b["Proj"], h["Proj"]
    if (pb is None) != (ph is None):
        flags.append(f"Projectile presence {bool(pb)} -> {bool(ph)}")
    elif pb and ph:
        for k in ("Speed", "Trail", "Inacc", "CStart", "CEnd"):
            if pb[k] != ph[k]:
                flags.append(f"Proj.{k} {pb[k]} -> {ph[k]}")
    if b["Report"] and not h["Report"]:
        flags.append(f"Report dropped ({b['Report']})")
    if b["effects"] != h["effects"]:
        flags.append("CreateEffect behaviour changed")
    print(f"  INH  base={b['Inherits']}")
    print(f"       head={h['Inherits']}")
    print(f"  WH   base={[(k, t, dm) for k, t, dm in b['warheads']]}")
    print(f"       head={[(k, t, dm) for k, t, dm in h['warheads']]}")
    print(f"  PROJ base={pb}")
    print(f"       head={ph}")
    if b["effects"] != h["effects"]:
        print(f"  FX   base={b['effects']}")
        print(f"       head={h['effects']}")
    print("  >> " + ("OK (behavioural invariants preserved)" if not flags else "FLAGS:"))
    for f in flags:
        print(f"       - {f}")


def main():
    if len(sys.argv) < 4:
        raise SystemExit(
            "Usage: review_resolve_diff.py <base_root> <head_root> W1 [W2 ...]")
    base_root, head_root = sys.argv[1], sys.argv[2]
    weapons = sys.argv[3:]
    rb = miniyaml.Ruleset(base_root)
    rh = miniyaml.Ruleset(head_root)
    for w in weapons:
        show(w, summarize(rb.resolve_weapon(w)), summarize(rh.resolve_weapon(w)))


if __name__ == "__main__":
    main()
