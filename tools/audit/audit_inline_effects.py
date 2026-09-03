#!/usr/bin/env python3
"""audit_inline_effects.py — are effect warheads inherited or inline?

    python tools/audit/audit_inline_effects.py [--exempt superweapons.txt] [--baseline N]

⛔ WHY THIS EXISTS (maintainer, 2026-08-19), reading the A2 review:

    *"effects should never be inline on a unit! they should always be inherited right?
    The only thing where it would be fine is for super weapons because those are sometimes
    more complex and require multiple animations"*

The 3-way split design (WEAPON_3WAY_SPLIT.md) puts ALL non-damage warheads in a single
`^Effect_*` template that is inherited via `Inherits@fx`. Declaring `Warhead@Effect*` on a
concrete weapon duplicates the visual layer across the tree, makes the split harder to
reason about, and lets an inherited `^Effect_*` and a local `Warhead@Effect` silently fight.

WHAT IT MEASURES:
- Concrete weapons (not `^templates`) that declare `Warhead@Effect*` nodes inline.
- Any `Warhead@*` node whose value is exactly `CreateEffect` (catches ad-hoc effect keys).
- Whether the weapon has an `Inherits@fx` or any `^Effect_*` inherit (so the inline is an
  override on top of a family).
- Superweapons are EXEMPT by design; the script tries to auto-detect them from support-power
  traits and accepts a manual `--exempt` list.

⚠ NOT EVERY INLINE IS A BUG TODAY. Superweapons are exempt, and a few weapons carry a
deliberate one-off visual override. This reports for review; `--baseline N` arms the ratchet.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from cameo_model import Model  # noqa: E402


# Known support-power / superweapon trait names in actor definitions.
SUPER_POWER_TRAITS = (
    "NukePower", "NukePowerCA", "FireArmamentPower",
    "IonCannonPower", "AirstrikePower", "AirStrikePower",
    "ParatroopersPower", "ChronoshiftPower", "IronCurtainPower",
    "GrantExternalConditionPower", "DroppodPower",
)


def _is_inline_effect(node) -> bool:
    """A warhead node that is an effect, not a damage warhead."""
    if not node.key.startswith("Warhead"):
        return False
    if node.key.startswith("Warhead@Effect"):
        return True
    # Generic CreateEffect key, e.g. Warhead@1Eff, Warhead@Foo
    if (node.value or "").strip() == "CreateEffect":
        return True
    return False


def _collect_weapons(node, out: set[str]):
    """Recursively collect all 'Weapon:', 'EmptyWeapon:', and 'MissileWeapons:' values under a node."""
    if node.key in ("Weapon", "EmptyWeapon") and node.value:
        for w in node.value.split(","):
            out.add(w.strip())
    elif node.key == "MissileWeapons" and node.value:
        # Inline comma list
        for w in re.split(r"[,;]", node.value):
            out.add(w.strip())
    elif node.key == "MissileWeapons" and not node.value:
        # Numeric-key list, e.g. 1: CabalMagicNuke
        for c in node.children:
            if c.value:
                for w in c.value.split(","):
                    out.add(w.strip())
    for c in node.children:
        _collect_weapons(c, out)


def _is_superweapon_weapon(rs, name: str, manual_exempt: set[str]) -> bool:
    if name in manual_exempt:
        return True
    source = rs.weapons.get(name)
    if source is None:
        return False
    # Heuristic: a weapon that explicitly inherits a *_Super family is likely a superweapon.
    inherits = [c.value.strip() for c in source.children if c.key.startswith("Inherits") and c.value]
    for i in inherits:
        if "_Super" in i or i in ("^NuclearWarhead",):
            return True
    return False


def _scan_superweapon_weapons(rs) -> set[str]:
    """Auto-detect weapons referenced by support-power traits."""
    out: set[str] = set()
    for actor in rs.actors.values():
        for child in actor.children:
            if child.key in SUPER_POWER_TRAITS or child.key.endswith("Power") and "super" in child.key.lower():
                _collect_weapons(child, out)
    # Also scan support-power orders if they live as separate top-level actors.
    # The engine resolves them through OrderName; we do a cheap global search for
    # actors whose name matches a known order and that carry a Weapon field.
    for actor_name in rs.actors:
        if any(sw in actor_name.lower() for sw in ("nuke", "ion", "deathhand", "supernova", "tactical")):
            resolved = rs.resolve(actor_name)
            if resolved is None:
                continue
            for child in resolved.children:
                _collect_weapons(child, out)
    return out


def _effect_inherits(source) -> list[str]:
    return [
        c.value.strip()
        for c in source.children
        if c.key.startswith("Inherits") and c.value
        and ("Effect" in c.value or c.key == "Inherits@fx")
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exempt", type=pathlib.Path, default=None,
                    help="File with one superweapon-weapon id per line to exclude.")
    ap.add_argument("--baseline", type=int, default=None,
                    help="Enable ratchet: fail if non-exempt inline count exceeds this.")
    a = ap.parse_args()

    manual_exempt: set[str] = set()
    if a.exempt:
        manual_exempt = {ln.strip() for ln in a.exempt.read_text(encoding="utf-8").splitlines() if ln.strip()}

    rs = Model().rs
    super_weps = _scan_superweapon_weapons(rs) | manual_exempt

    rows = []
    for name in sorted(rs.weapons):
        if name.startswith("^"):
            continue
        source = rs.weapons[name]
        effects = [c for c in source.children if _is_inline_effect(c)]
        if not effects:
            continue
        rows.append((
            name,
            len(effects),
            ",".join(c.key for c in effects),
            _effect_inherits(source),
            name in super_weps,
        ))

    non_super = [r for r in rows if not r[4]]
    super = [r for r in rows if r[4]]
    all_nodes = sum(r[1] for r in rows)

    print("# audit_inline_effects — concrete weapons with inline effect warheads\n")
    print(f"Auto-detected superweapon weapons: **{len(super_weps)}**")
    print(f"Concrete weapons with inline effects: **{len(rows)}**  ({all_nodes} nodes)")
    print(f"After superweapon exemption: **{len(non_super)}** weapons  ({sum(r[1] for r in non_super)} nodes)\n")

    print("## Non-exempt weapons with the most inline effect nodes\n")
    print("| weapon | inline effect keys | has `Inherits@fx` / `^Effect_*` |")
    print("|---|---|---|")
    for name, n, keys, inherits, _ in sorted(non_super, key=lambda x: -x[1])[:60]:
        fx = "yes" if inherits else "no"
        print(f"| `{name}` | {keys} | {fx} |")
    if len(non_super) > 60:
        print(f"\n_… {len(non_super) - 60} more_")

    print("\n## Superweapon-exempt examples\n")
    if super:
        print("| weapon | inline effect keys |")
        print("|---|---|")
        for name, _n, keys, _in, _ in super[:20]:
            print(f"| `{name}` | {keys} |")
        if len(super) > 20:
            print(f"\n_… {len(super) - 20} more_")
    else:
        print("_none auto-detected_")

    print(f"\n**total inline effect nodes on non-super weapons: {sum(r[1] for r in non_super)}**")

    if a.baseline is None:
        print("\n_no baseline set — reporting only. Measure on a settled tree, then ratchet DOWN._")
        return 0

    count = sum(r[1] for r in non_super)
    if count > a.baseline:
        print(f"\n**FAIL — {count} non-exempt inline effect nodes exceeds the baseline of {a.baseline}.**")
        return 1
    print(f"\n_at or below baseline ({a.baseline})._")
    return 0


if __name__ == "__main__":
    sys.exit(main())
