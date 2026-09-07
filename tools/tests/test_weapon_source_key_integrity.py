"""Regression checks for active weapon source keys that MiniYAML merges by name."""

from __future__ import annotations

import collections
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset


EXPECTED_VALUES = {
    "FLAK-23-AG": {"ReloadDelay": "5"},
    "Fremen_S": {"Report": "MGUN2.WAV"},
    "RA2GrenadePack": {"Report": "toss1.aud"},
    "SteelFortressWeapons": {
        "Report": "vrhiatta.wav, vrhiattb.wav, vrhiattc.wav, vrhiattd.wav",
    },
    "SteelMantaHunterCannons": {"ValidTargets": "Ground, Water"},
    "SteelVulcan": {"Report": "pulseturretfire.wav"},
    "TSAAPCCannon": {"ValidTargets": "Ground, Water, Air"},
    "TSChemMLRSMissile": {"Report": "hovrmis1.aud"},
    "TSChemVanMissile": {"Report": "hovrmis1.aud"},
    "TSDestroyerMissiles": {"Report": "hovrmis1.aud"},
    "TSEngineerPistol": {"ReloadDelay": "25"},
    "TSHoverMissile": {"Report": "hovrmis1.aud"},
    "TSJuggerFlakAA_boat": {"Range": "11234"},
    "TSMLRSMissile": {"Report": "hovrmis1.aud"},
    "TSMutApcCannon": {"ValidTargets": "Ground, Water, Air"},
    "TSVanMissile": {"Report": "hovrmis1.aud"},
    "Vulcan": {"ReloadDelay": "125"},
    "d2k_flame_tank": {"ValidTargets": "Ground, Water"},
    "wc2mageBlizzard": {"ValidTargets": "Ground, Water, Air"},
}

EXPECTED_PARENTS = {
    "12MissilesSpawnerScud": {
        "^Projectile_Flame_Medium", "^Effect_Flame_Medium",
        "^RA2Grenade", "^RA2HeavyMissile",
    },
    "HammerTankCannonThermobaric": {
        "^Projectile_Flame_Medium", "HammerTankCannon",
    },
    # Upstream 4a1479b50 replaced the thermobaric role with a nuclear shell.
    "KotinCannonNuclearShell": {
        "^Warhead_CannonNuke_Heavy", "^Projectile_Shell_Heavy",
        "^Effect_CannonHE_Heavy", "^Effect_Nuclear_Super",
    },
    "SandmarineTuskFire": {
        "^Warhead_MissileAP_Light", "^SandmarineTuskLegacy"},
    "TSDestroyerMissiles": {"^FlakWeapon", "^MediumMissile", "^ShrapnelWeapon"},
    "ViperMissilesFire": {"^Warhead_MissileAP_Light", "^ViperMissilesLegacy"},
    "tkmkatyushalalauncherrocketsfire": {
        "^Effect_Flame_Light", "tkmkatyushalalauncherrockets",
    },
}


class WeaponSourceKeyIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.concrete = {
            name: node for name, node in cls.rules.weapons.items()
            if not name.startswith("^") and cls.rules.resolve_weapon(name) is not None
        }

    def test_ordos_apc_duplicate_merge_preserves_the_resolved_binding(self):
        name = "D2K_APC_Rocket_AA"
        key = "Warhead@MissileAA_MediumFlatCompatibility"
        self.assertEqual(1, sum(child.key == key for child in self.rules.weapon(name).children))
        weapon = self.rules.resolve_weapon(name)
        warhead = next(child for child in weapon.children if child.key == key)
        self.assertEqual("Air", weapon.get("ValidTargets"))
        self.assertEqual("AreaDamage", warhead.value)
        for field, expected in {
            "PhysicalStateName": "Temperature",
            "ValidTargets": "Ground, Water, Air",
            "Damage": "24000",
            "PercentageScale": "0",
        }.items():
            self.assertEqual(expected, warhead.get(field), field)

    def test_concrete_weapons_do_not_repeat_top_level_keys(self):
        duplicates = []
        for name, node in self.concrete.items():
            counts = collections.Counter(
                child.key for child in node.children
                if child.key and not child.key.startswith("-")
            )
            duplicates.extend(
                (name, key, count) for key, count in counts.items() if count > 1
            )
        self.assertEqual([], duplicates)

    def test_numbered_effect_stages_are_not_silently_suppressed(self):
        expected = {
            "D2KRepair": {
                "Warhead@2Defuse": ("Types", "ivanbomb"),
                "Warhead@3Defuse": ("Types", "lockdown"),
            },
            "ReimuOrbLauncher": {
                f"Warhead@Shrapnel{i}": ("Delay", str(96 + 4 * i))
                for i in range(1, 5)
            },
            "MagicOrbHailstormSpawner": {
                f"Warhead@Shrapnel{i}": ("Delay", str(i * i))
                for i in range(1, 5)
            },
            "wc2blizzardSuper": {
                f"Warhead@InitialSpreader{i}": (
                    "Delay",
                    "" if i == 1 else str(
                        (i - 1) * 20 if i <= 7 else 30 * i - 90
                    ),
                )
                for i in range(1, 14)
            },
        }
        for weapon, stages in expected.items():
            resolved = self.rules.resolve_weapon(weapon)
            for key, (field, value) in stages.items():
                node = resolved.child(key)
                self.assertIsNotNone(node, f"{weapon}/{key}")
                self.assertEqual(
                    value or None,
                    node.get(field),
                    f"{weapon}/{key}/{field}",
                )

    def test_restored_effect_stage_payloads_are_pinned(self):
        repair = self.rules.resolve_weapon("D2KRepair")
        self.assertEqual("ivanattached", repair.child("Warhead@2Defuse").get("ValidTargets"))
        self.assertEqual("lockdowned", repair.child("Warhead@3Defuse").get("ValidTargets"))
        for key in ("Warhead@2Defuse", "Warhead@3Defuse"):
            self.assertEqual("Ally", repair.child(key).get("ValidRelationships"))

        reimu = self.rules.resolve_weapon("ReimuOrbLauncher")
        for i in range(1, 5):
            node = reimu.child(f"Warhead@Shrapnel{i}")
            self.assertEqual("4", node.get("Amount"))
            self.assertEqual("50", node.get("AimChance"))

        hailstorm = self.rules.resolve_weapon("MagicOrbHailstormSpawner")
        for i in range(1, 5):
            node = hailstorm.child(f"Warhead@Shrapnel{i}")
            expected = str(i * i)
            self.assertEqual(expected, node.get("Amount"))
            self.assertEqual(expected, node.get("AimChance"))

        blizzard = self.rules.resolve_weapon("wc2blizzardSuper")
        counts = (2, 4, 6, 8, 10, 12, 14, 12, 10, 8, 6, 4, 2)
        for i, count in enumerate(counts, start=1):
            node = blizzard.child(f"Warhead@InitialSpreader{i}")
            self.assertEqual(str(count), node.get("RandomClusterCount"))
            self.assertEqual("wc2blizzardSuper_Spread", node.get("Weapon"))

    def test_collapsed_nodes_keep_the_previously_effective_behavior(self):
        expected = {
            "Future_CoilerFriend": ("Projectile", "LightningZap", "CoreWidth", "16"),
            "TSMammothTusk2II_AA": ("Projectile", "Missile", "Speed", "500"),
            "wc2dragonFireExplosion": (
                "Projectile", "Bullet", "Speed", "384"
            ),
            "wc2demolitionsquadExplode": (
                "Warhead@Concrete", "DamagesConcrete", "Damage", "25"
            ),
        }
        for weapon, (key, node_type, field, value) in expected.items():
            node = self.rules.resolve_weapon(weapon).child(key)
            self.assertEqual(node_type, node.value, f"{weapon}/{key}")
            self.assertEqual(value, node.get(field), f"{weapon}/{key}/{field}")

    def test_concrete_weapons_do_not_shadow_inheritance_parents(self):
        duplicates = []
        for name, node in self.concrete.items():
            counts = collections.Counter(
                child.key for child in node.children
                if child.key == "Inherits" or child.key.startswith("Inherits@")
            )
            duplicates.extend(
                (name, key, count) for key, count in counts.items() if count > 1
            )
        self.assertEqual([], duplicates)

    def test_cleanup_keeps_the_previously_effective_scalar_values(self):
        for name, fields in EXPECTED_VALUES.items():
            weapon = self.rules.resolve_weapon(name)
            for field, expected in fields.items():
                self.assertEqual(expected, weapon.get(field), f"{name}/{field}")

    def test_corrected_inheritance_keys_keep_every_authored_parent(self):
        for name, expected in EXPECTED_PARENTS.items():
            local = self.rules.weapon(name)
            self.assertIsNotNone(local, name)
            actual = {
                str(child.value) for child in local.children
                if child.key == "Inherits" or child.key.startswith("Inherits@")
            }
            self.assertTrue(expected <= actual, (name, expected - actual))


if __name__ == "__main__":
    unittest.main()
