#!/usr/bin/env python3
"""weapon_families.py — the two constant tables the weapon-split tools share.

`audit_code_duplication.py` C3 flags identical module-level literal tables. Both
of these were copy-pasted across the Phase A/B survey and orphan-key tools, so a
family added to one copy silently went missing from the others. One definition
here; the scripts import it.

- ``CENTRAL`` / ``weapon_files()`` — every LIVE weapons yaml: the central files
  listed in ``mod.yaml`` plus each ContentPack's own ``weapons.yaml``.
- ``OLD_FAMILIES`` — the legacy full-stack ``^<Name>Weapon`` templates that the
  3-way split (``^Warhead_*`` / ``^Projectile_*`` / ``^Effect_*``) replaces.
  A weapon still inheriting one of these has not been converted yet.
"""

from __future__ import annotations

import pathlib

MOD = pathlib.Path(__file__).resolve().parents[2] / "mods" / "cameo"

# Central weapon files (the per-theme monoliths that survive migration).
CENTRAL = ["weapons/weapons.yaml", "weapons/tiberiandawn.yaml",
           "weapons/redalert2mod.yaml", "weapons/d2k.yaml",
           "weapons/starcraft.yaml", "weapons/warcraft2.yaml",
           "weapons/tiberiansun.yaml", "weapons/outpost2.yaml"]

# Legacy full-stack templates retired by the 3-way split.
OLD_FAMILIES = {
    "^SmallArms", "^Chaingun", "^TankDestroyerCannon", "^MediumCannon",
    "^HeavyCannon", "^LightMissile", "^MediumMissile", "^HeavyMissile",
    "^FlakWeapon", "^HeavyAAWeapon", "^Grenade", "^ShrapnelWeapon",
    "^HeavyBomb", "^LaserWeapon", "^RailgunWeapon", "^TeslaWeapon",
    "^TeslaChargedWeapon", "^SwordWeapon", "^ArrowWeapon", "^MagicWeapon",
    "^LightFlameWeapon", "^MediumFlameWeapon", "^HeavyFlameWeapon",
    "^LightChemicalWeapon", "^MediumChemicalWeapon", "^HeavyChemicalWeapon",
    "^NuclearWarhead", "^SniperWeapon", "^LightArms",
}


def weapon_files(mod: pathlib.Path = MOD) -> list[pathlib.Path]:
    """Central weapon files first, then every ContentPack `weapons.yaml`, sorted.

    Order matters to the callers' reports, so it matches what they each built by
    hand before: `CENTRAL` in listed order, ContentPacks sorted by path.
    """
    return [mod / p for p in CENTRAL] + sorted(
        (mod / "ContentPacks").glob("*/*/yaml/weapons.yaml"))
