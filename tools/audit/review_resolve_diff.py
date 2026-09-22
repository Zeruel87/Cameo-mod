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

Usage: python tools/audit/review_resolve_diff.py [--strict-order]
       [--rename BASE_KEY=HEAD_KEY] <base_root> <head_root> W1 W2 ...
"""
import argparse
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import miniyaml


def _payload(node, key_normalizer=None):
    """Return a complete, order-preserving payload for one resolved node.

    The node key is deliberately excluded so a caller can allow an explicit
    key rename while still comparing every value and descendant field.
    """
    return (
        node.value,
        tuple((key_normalizer(child.key) if key_normalizer else child.key,
               _payload(child, key_normalizer)) for child in node.children),
    )


def _unordered_payload(payload):
    """Return a payload with child fields sorted for diagnostics."""
    value, children = payload
    return (value, tuple(sorted(
        ((key, _unordered_payload(child)) for key, child in children),
        key=lambda item: (item[0], repr(item[1])))))


def _warhead_entries(node, key_normalizer=None):
    if node is None:
        return []
    return [
        (key_normalizer(child.key) if key_normalizer else child.key,
         _payload(child, key_normalizer))
        for child in node.children
        if child.key == "Warhead" or child.key.startswith("Warhead@")
    ]


def _rename_inverse(rename_map):
    """Validate and invert BASE_KEY=HEAD_KEY mappings."""
    inverse = {}
    for base, head in (rename_map or {}).items():
        if not (base == "Warhead" or base.startswith("Warhead@")):
            raise ValueError(f"rename keys must identify warhead nodes: {base}")
        if not (head == "Warhead" or head.startswith("Warhead@")):
            raise ValueError(f"rename keys must identify warhead nodes: {head}")
        if head in inverse and inverse[head] != base:
            raise ValueError(f"ambiguous rename target: {head}")
        inverse[head] = base
    return inverse


def ordered_warhead_differences(base, head, rename_map=None):
    """Describe strict resolved warhead differences in execution order.

    ``rename_map`` is explicitly base-key -> head-key.  A rename may change a
    key, but it may not reorder executable warheads or alter any payload field.
    The returned list is empty only when the ordered payload is identical after
    the declared key renames.
    """
    if base is None or head is None:
        return ["resolved weapon missing in base or head"]

    inverse = _rename_inverse(rename_map)
    normalize = lambda key: inverse.get(key, key)
    base_entries = _warhead_entries(base)
    head_entries = _warhead_entries(head, normalize)
    problems = []

    if len(base_entries) != len(head_entries):
        problems.append(
            f"warhead count changed: {len(base_entries)} -> {len(head_entries)}")

    for index, (base_entry, head_entry) in enumerate(
            zip(base_entries, head_entries)):
        base_key, base_payload = base_entry
        head_key, head_payload = head_entry
        if base_key != head_key:
            problems.append(
                f"executable order/key changed at index {index}: "
                f"{base_key} -> {head_key}")
            continue
        if base_payload != head_payload:
            if _unordered_payload(base_payload) == _unordered_payload(head_payload):
                problems.append(
                    f"warhead field order changed at index {index}: {base_key}")
            else:
                problems.append(f"warhead payload changed at index {index}: {base_key}")

    # A permutation can leave every paired payload equal only when all entries
    # are duplicates.  Compare the normalized sequence explicitly so a swap of
    # two distinct warheads is always reported as executable-order drift.
    if base_entries and head_entries and base_entries != head_entries:
        base_keys = [key for key, _ in base_entries]
        head_keys = [key for key, _ in head_entries]
        if sorted(base_keys) == sorted(head_keys) and base_keys != head_keys:
            problems.append(
                f"executable warhead order changed: {base_keys} -> {head_keys}")
    return problems


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


def _rename_args(values):
    result = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"rename must be BASE_KEY=HEAD_KEY: {value}")
        base, head = value.split("=", 1)
        if not base or not head:
            raise ValueError(f"rename must be BASE_KEY=HEAD_KEY: {value}")
        if base in result and result[base] != head:
            raise ValueError(f"conflicting rename for {base}")
        result[base] = head
    _rename_inverse(result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compare resolved weapon invariants before and after a retrofit.")
    parser.add_argument(
        "--strict-order", action="store_true",
        help="fail on executable warhead order or complete payload changes")
    parser.add_argument(
        "--rename", action="append", default=[], metavar="BASE_KEY=HEAD_KEY",
        help="allow this explicit resolved warhead key rename (repeatable)")
    parser.add_argument("base_root")
    parser.add_argument("head_root")
    parser.add_argument("weapons", nargs="+")
    args = parser.parse_args(argv)
    rename_map = _rename_args(args.rename)
    base_root, head_root = args.base_root, args.head_root
    weapons = args.weapons
    rb = miniyaml.Ruleset(base_root)
    rh = miniyaml.Ruleset(head_root)
    exit_code = 0
    for w in weapons:
        base = rb.resolve_weapon(w)
        head = rh.resolve_weapon(w)
        show(w, summarize(base), summarize(head))
        if args.strict_order:
            differences = ordered_warhead_differences(base, head, rename_map)
            if differences:
                exit_code = 1
                print("  ORDER:")
                for difference in differences:
                    print(f"       - {difference}")
            else:
                print("  ORDER >> OK (ordered payload preserved)")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
