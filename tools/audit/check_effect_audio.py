#!/usr/bin/env python3
"""Guard source-family impact audio in the 3-way-split effect library.

The AP/HE and Demolition/Concussion splits may change damage semantics and
visuals, but must not silently replace the source weapon family's impact audio.

Usage: python tools/audit/check_effect_audio.py [repo_root]
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import miniyaml


EXPECTED = {
    "^Effect_CannonAP_Light": ("xplosml2.aud", "kaboom25.aud"),
    "^Effect_CannonAP_Medium": ("kaboom12.aud", "kaboom25.aud"),
    "^Effect_CannonAP_Heavy": ("kaboom15.aud", "kaboom25.aud"),
    "^Effect_CannonHE_Light": ("xplosml2.aud", "kaboom25.aud"),
    "^Effect_CannonHE_Medium": ("kaboom12.aud", "kaboom25.aud"),
    "^Effect_CannonHE_Heavy": ("kaboom15.aud", "kaboom25.aud"),
    "^Effect_MissileAP_Light": ("xplos.aud", "xplos.aud"),
    "^Effect_MissileAP_Medium": ("xplos.aud", "xplos.aud"),
    "^Effect_MissileAP_Heavy": ("xplobig4.aud", "kaboom25.aud"),
    "^Effect_MissileHE_Light": ("xplos.aud", "xplos.aud"),
    "^Effect_MissileHE_Medium": ("xplos.aud", "xplos.aud"),
    "^Effect_MissileHE_Heavy": ("xplobig4.aud", "kaboom25.aud"),
    "^Effect_Demolition_Light": ("xplos.aud", None),
    "^Effect_Demolition_Medium": ("xplos.aud", None),
    "^Effect_Demolition_Heavy": ("siege_impact.aud", None),
    "^Effect_Concussion_Light": ("xplos.aud", None),
    "^Effect_Concussion_Medium": ("xplos.aud", None),
    "^Effect_Concussion_Heavy": ("siege_impact.aud", None),
    "^Effect_Magic_Light": ("xplos.aud", None),
    "^Effect_Magic_Medium": ("xplos.aud", None),
    "^Effect_Magic_Heavy": ("xplos.aud", None),
    "^Effect_Sonic_Light": (None, None),
    "^Effect_Sonic_Medium": ("xplos.aud", None),
    "^Effect_Sonic_Heavy": ("xplos.aud", None),
}

SHELL_SHIELD = ("shielded_shell_hit1.wav, shielded_shell_hit2.wav, "
                "shielded_shell_hit3.wav, shielded_shell_hit4.wav")
BULLET_SHIELD = ("shielded_bullet_hit1.wav, shielded_bullet_hit2.wav, "
                 "shielded_bullet_hit3.wav, shielded_bullet_hit4.wav")


def child_value(node, key):
    return next((child.value for child in node.children if child.key == key), None)


def row(sound, valid=None, invalid=None, delay=None):
    return sound, valid, invalid, delay


def sound_rows(node):
    return {
        child.key: row(
            sound,
            child_value(child, "ValidTargets"),
            child_value(child, "InvalidTargets"),
            child_value(child, "Delay"))
        for child in node.children
        if child.key.startswith("Warhead@") and child.value == "CreateEffect"
        if (sound := child_value(child, "ImpactSounds")) is not None
    }


def expected_template_rows(name, ground, air):
    rows = {}
    if "Cannon" in name:
        rows = {
            "Warhead@Effect": row(ground, "Ground, Ship"),
            "Warhead@EffectWater": row(
                "splash9.aud", "Water, Underwater", "Ship, Structure, Bridge"),
            "Warhead@EffectAir": row(air, "Air"),
        }
        shield = SHELL_SHIELD
    elif "Missile" in name:
        rows = {
            "Warhead@Effect": row(ground, "Ground, Water"),
            "Warhead@EffectAir": row(air, "Air"),
        }
        shield = SHELL_SHIELD
    elif "Demolition" in name or "Concussion" in name:
        if name.endswith("Heavy"):
            rows = {
                "Warhead@Effect1": row(ground, "Ground, Ship"),
                "Warhead@Effect2": row("gexp14a.wav", "Ground, Ship", delay="6"),
                "Warhead@EffectWater": row("gexpwasa.wav", "Water, Underwater"),
            }
        else:
            rows = {
                "Warhead@Effect": row(ground, "Ground, Ship"),
                "Warhead@EffectWater": row(
                    "splash9.aud", "Water, Underwater", "Ship, Structure, Bridge"),
            }
        shield = SHELL_SHIELD
    else:
        if ground is not None:
            rows["Warhead@Effect"] = row(ground, "Ground, Ship")
        shield = BULLET_SHIELD

    rows["Warhead@ShieldHitEffect"] = row(shield, "Shielded")
    return rows


CONCRETE_EXPECTED = {
    # The Ixian Rocket Turret uses this weapon. Its local D2K impact and the
    # inherited heavy-missile air impact intentionally coexist.
    "D2K_TowerMissile": {
        "Warhead@Effect": row("EXPLSML1.WAV", "Ground, Air"),
        "Warhead@EffectWater": row(
            "splash9.aud", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@EffectAir": row("kaboom25.aud", "Air"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
    "TSSonicZapWeapon": {
        "Warhead@ShieldHitEffect": row(BULLET_SHIELD, "Shielded"),
    },
    "TSSonicZapWeaponSonic": {
        "Warhead@ShieldHitEffect": row(BULLET_SHIELD, "Shielded"),
    },
    "TSHellfireSonic": {
        "Warhead@Effect": row("xplos.aud", "Ground, Ship"),
        "Warhead@EffectAir": row("xplos.aud", "Air"),
        "Warhead@EffectWater": row(
            "splash9.aud", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@ShieldHitEffect": row(BULLET_SHIELD, "Shielded"),
    },
    "TSZoneHellfireSonic": {
        "Warhead@Effect": row("xplos.aud", "Ground, Ship"),
        "Warhead@EffectAir": row("xplos.aud", "Air"),
        "Warhead@EffectWater": row(
            "splash9.aud", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@ShieldHitEffect": row(BULLET_SHIELD, "Shielded"),
    },
    "CabalReaperMissiles": {
        "Warhead@Effect": row("expnew12.aud", "Ground, Ship, Air"),
        "Warhead@EffectAir": row("xplos.aud", "Air"),
        "Warhead@EffectWater": row(
            "splash9.aud", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
    "CabalHeavyReaperMissiles": {
        "Warhead@Effect": row("expnew12.aud", "Ground, Ship, Air"),
        "Warhead@EffectAir": row("kaboom25.aud", "Air"),
        "Warhead@EffectWater": row(
            "splash9.aud", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
    "CabalRocketCyborgRockets": {
        "Warhead@Effect": row("expnew12.aud", "Ground, Ship, Air"),
        "Warhead@EffectAir": row("xplos.aud", "Air"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
    "NaxShoeRocket": {
        "Warhead@Effect": row("snukexpl.wav", "Ground, Ship"),
        "Warhead@Effect2": row("gexp14a.wav", "Ground, Ship", delay="6"),
        "Warhead@EffectAir": row("xplos.aud", "Air"),
        "Warhead@EffectWater": row(
            "gexpwasa.wav", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
    "RA2AkulaRockets": {
        "Warhead@Effect": row("snukexpl.wav", "Ground, Ship"),
        "Warhead@Effect2": row("gexp14a.wav", "Ground, Ship", delay="6"),
        "Warhead@EffectAir": row("xplos.aud", "Air"),
        "Warhead@EffectWater": row(
            "gexpwasa.wav", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
    "RA2HornetMissile": {
        "Warhead@Effect": row("gexp14a.wav", "Ground, Ship"),
        "Warhead@Effect2": row("gexp14a.wav", "Ground, Ship", delay="6"),
        "Warhead@EffectAir": row("xplos.aud", "Air"),
        "Warhead@EffectWater": row(
            "gexpwasa.wav", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
    "RA2PatriotThunderboltMissile": {
        "Warhead@Effect": row("xplos.aud", "Ground, Water"),
        "Warhead@EffectAir": row("xplos.aud", "Air"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
    "SteelKatyCannons": {
        "Warhead@Effect": row("xplos.aud", "Ground, Water, Air"),
        "Warhead@EffectAir": row("kaboom25.aud", "Air"),
        "Warhead@EffectWater": row(
            "gexpwasa.wav", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
    "ra1_soviets_v2rocketlauncher_scudthermobaric": {
        "Warhead@Effect": row("firebl3.aud", "Ground, Water"),
        "Warhead@Effect1": row("siege_impact.aud", "Ground, Ship"),
        "Warhead@Effect2": row("gexp14a.wav", "Ground, Ship", delay="6"),
        "Warhead@EffectAir": row("kaboom25.aud", "Air"),
        "Warhead@EffectWater": row("gexpwasa.wav", "Water, Underwater"),
        "Warhead@ShieldHitEffect": row(BULLET_SHIELD, "Shielded"),
    },
    "12MissilesSpawnerScud": {
        "Warhead@Effect": row("snukexpl.wav", "Ground, Ship"),
        "Warhead@Effect1": row("siege_impact.aud", "Ground, Ship"),
        "Warhead@Effect2": row("gexp14a.wav", "Ground, Ship", delay="6"),
        "Warhead@EffectAir": row("kaboom25.aud", "Air"),
        "Warhead@EffectWater": row(
            "gexpwasa.wav", "Water, Underwater", "Ship, Structure, Bridge"),
        "Warhead@ShieldHitEffect": row(SHELL_SHIELD, "Shielded"),
    },
}


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    rules = miniyaml.Ruleset(str(root))
    failures = []
    for name, (ground, air) in EXPECTED.items():
        node = rules.resolve_weapon(name)
        if node is None:
            failures.append(f"{name}: missing")
            continue
        expected = expected_template_rows(name, ground, air)
        actual = sound_rows(node)
        if actual != expected:
            failures.append(f"{name}: expected {expected}, got {actual}")

    for name, expected in CONCRETE_EXPECTED.items():
        node = rules.resolve_weapon(name)
        if node is None:
            failures.append(f"{name}: missing")
            continue
        actual = sound_rows(node)
        if actual != expected:
            failures.append(f"{name}: expected {expected}, got {actual}")

    if failures:
        print("Effect audio regression(s):", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        raise SystemExit(1)

    print(f"OK: {len(EXPECTED)} source-family mappings and "
          f"{len(CONCRETE_EXPECTED)} concrete weapon chains")


if __name__ == "__main__":
    main()
