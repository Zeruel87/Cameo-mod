"""Regression checks for the consolidated direct-fire sniper family."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from miniyaml import Ruleset
from formula import dps
from percentage_damage import percentage_applications


ROOT_SNIPERS = (
    "AsianSniper", "GhostSniper", "SpecterSniper", "VonSniper",
    "GDISniperRifle", "CommandoSniper",
)
RESOLVED_SNIPERS = (
    "AsianSniper", "AsianSniperAP", "AsianSniperLockdown",
    "GhostSniper", "GhostSniperBunker", "GhostSniperLockdown",
    "SpecterSniper", "SpecterSniperLockdown",
    "VonSniper", "VonSniperAP", "VonSniperLockdown",
    "GDISniperRifle", "CommandoSniper", "DragunovSniper",
    "LightSniper", "CryoLightSniper", "RA2AWP", "RA2AWP_elite",
    "NaxiSniper", "NaxiSniper_elite", "tkmawp", "VanSniper",
    "TSSniper", "td_gdi_commando_sniper", "td_gdi_commando_sniper_elite",
    "RA2Virusgun", "RA2Virusgun2", "RA2Virusgun3", "RA2Virusgun_elite",
)
SPATIAL_DAMAGE_TYPES = {
    "AreaDamage", "AreaDamagePercentage", "OpenToppedDamage", "SpreadDamage",
}
FLAT_DAMAGE_TYPES = {"AreaDamage", "SpreadDamage", "TargetDamage"}
SNIPER_ACTORS = {
    "AsianSniper": "asianalliance_asiancommando",
    "GhostSniper": "terran_ghost",
    "SpecterSniper": "terran_specter",
    "VonSniper": "tkm_von",
}
RETIRED_FOLLOWUP_WARHEADS = {
    "GDISniperRifle": {
        "Warhead@SmallArms", "Warhead@Grenade", "Warhead@GrenadeFriendlyFire",
        "Warhead@FlakWeapon", "Warhead@Chaingun",
    },
    "CommandoSniper": {"Warhead@SniperWeapon", "Warhead@SniperWeaponExtraDamage", "Warhead@Chaingun"},
    "DragunovSniper": {
        "Warhead@TankDestroyerCannon", "Warhead@RailgunWeapon",
        "Warhead@RailgunExtraDamage", "Warhead@LightMissile",
        "Warhead@HeavyCannon", "Warhead@FlakWeapon",
    },
}


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


def int_field(node, key, default):
    field = child(node, key)
    return int(field.value) if field is not None else default


def armor_and_hp(actor):
    armor = child(child(actor, "Armor"), "Type").value
    hp = int(child(child(actor, "Health"), "HP").value)
    return armor, hp


def center_hit_damage(weapon, armor, hp):
    """Current positional-projectile damage at the struck actor's hit shape."""
    total = 0.0
    for warhead in weapon.children:
        if not warhead.key.startswith("Warhead") or warhead.value not in FLAT_DAMAGE_TYPES:
            continue
        if "FriendlyFire" in warhead.key:
            continue
        damage = int_field(warhead, "Damage", 0)
        versus = child(warhead, "Versus")
        values = {item.key: int(item.value) for item in versus.children} if versus else {}
        total += damage * values.get(armor, 100) / 100

    # These rifles and missiles use positional projectiles, so the current runtime
    # executes both folded and standalone percentage applications.
    for application in percentage_applications(weapon, hp):
        total += application["runtime_hp"] * application["versus"].get(armor, 100) / 100
    return total


def damage_per_tick(weapon, armor, hp):
    burst = int_field(weapon, "Burst", 1)
    delays = child(weapon, "BurstDelays")
    burst_delays = [int(value.strip()) for value in delays.value.split(",")] if delays else None
    return dps(
        center_hit_damage(weapon, armor, hp),
        int_field(weapon, "ReloadDelay", 1),
        burst,
        burst_delays,
    )


class SniperDamageProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_sniper_descendants_limit_spatial_damage_to_direct_impact(self):
        for name in RESOLVED_SNIPERS:
            weapon = self.rules.resolve_weapon(name)
            self.assertIsNotNone(weapon, name)
            spatial = [
                warhead
                for warhead in weapon.children
                if warhead.key.startswith("Warhead@")
                and warhead.value in SPATIAL_DAMAGE_TYPES
            ]
            self.assertTrue(spatial, name)
            for warhead in spatial:
                for radius_override in ("Range", "Ticks", "MaxRadius"):
                    self.assertIsNone(
                        child(warhead, radius_override),
                        f"{name}: {warhead.key}.{radius_override}",
                    )
                spread = child(warhead, "Spread")
                falloff = child(warhead, "Falloff")
                self.assertIsNotNone(spread, f"{name}: {warhead.key}")
                self.assertIsNotNone(falloff, f"{name}: {warhead.key}")
                self.assertEqual("1", spread.value, f"{name}: {warhead.key}")
                self.assertEqual("100, 0", falloff.value, f"{name}: {warhead.key}")

    def test_root_snipers_use_infantry_favoured_heavy_bullet_profile(self):
        for name in ROOT_SNIPERS:
            weapon = self.rules.resolve_weapon(name)
            warhead = child(weapon, "Warhead@Bullet_Heavy")
            self.assertIsNotNone(warhead, name)
            self.assertEqual("AreaDamage", warhead.value, name)
            versus = child(warhead, "Versus")
            values = {item.key: int(item.value) for item in versus.children}
            self.assertGreater(values["None"], values["Heavy"], name)
            self.assertGreater(values["Flak"], values["Superheavy"], name)
            self.assertGreater(values["Plate"], values["Superheavy"], name)

    def test_regular_snipers_lose_a_static_duel_to_baseline_mammoth(self):
        mammoth = self.rules.resolve("ra1_soviets_sovietmammothtank")
        self.assertIsNotNone(mammoth, "live Soviet Mammoth baseline")
        mammoth_armor, mammoth_hp = armor_and_hp(mammoth)
        tusk = self.rules.resolve_weapon("MammothTusk")

        for weapon_name, actor_name in SNIPER_ACTORS.items():
            sniper = self.rules.resolve(actor_name)
            sniper_armor, sniper_hp = armor_and_hp(sniper)
            rifle = self.rules.resolve_weapon(weapon_name)

            sniper_ttk = mammoth_hp / damage_per_tick(rifle, mammoth_armor, mammoth_hp)
            mammoth_ttk = sniper_hp / damage_per_tick(tusk, sniper_armor, sniper_hp)
            self.assertGreater(sniper_ttk, mammoth_ttk, weapon_name)

    def test_dragunov_keeps_anti_materiel_profile_and_loses_to_mammoth(self):
        weapon = self.rules.resolve_weapon("DragunovSniper")
        warhead = child(weapon, "Warhead@CannonAP_Heavy")
        self.assertIsNotNone(warhead)
        self.assertEqual("Ground, Water, Air", child(warhead, "ValidTargets").value)

        versus = {item.key: int(item.value) for item in child(warhead, "Versus").children}
        self.assertGreater(versus["Heavy"], versus["None"])
        self.assertGreater(versus["Superheavy"], versus["Flak"])

        mammoth = self.rules.resolve("ra1_soviets_sovietmammothtank")
        self.assertIsNotNone(mammoth, "live Soviet Mammoth baseline")
        mammoth_armor, mammoth_hp = armor_and_hp(mammoth)
        dragunov = self.rules.resolve("ra1_soviets_dragunovantimaterialsniper")
        dragunov_armor, dragunov_hp = armor_and_hp(dragunov)
        tusk = self.rules.resolve_weapon("MammothTusk")

        dragunov_ttk = mammoth_hp / damage_per_tick(weapon, mammoth_armor, mammoth_hp)
        mammoth_ttk = dragunov_hp / damage_per_tick(tusk, dragunov_armor, dragunov_hp)
        self.assertLess(center_hit_damage(weapon, mammoth_armor, mammoth_hp), mammoth_hp)
        self.assertGreater(dragunov_ttk, mammoth_ttk)

    def test_followup_snipers_remove_retired_flat_damage_slots(self):
        for name, retired in RETIRED_FOLLOWUP_WARHEADS.items():
            weapon = self.rules.resolve_weapon(name)
            resolved_keys = {node.key for node in weapon.children}
            self.assertFalse(retired & resolved_keys, f"{name}: {retired & resolved_keys}")


if __name__ == "__main__":
    unittest.main()
