"""Regression checks for the post-consolidation weapon correctness fixes."""

from __future__ import annotations

import pathlib
import sys
import unittest
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import audit_impact_glow_preservation as glow_audit
from miniyaml import Ruleset, load


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


class WeaponCorrectnessFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_steel_runner_base_and_resonance_armaments_are_exclusive(self):
        actor = self.rules.resolve("steelconsortium_steelrunner")
        armaments = [node for node in actor.children if node.key.startswith("Armament@")]
        runner = [node for node in armaments
                  if (node.get("Weapon") or "").startswith("SteelRunnerPistols")]
        self.assertEqual(8, len(runner))

        for armament in runner:
            weapon = armament.get("Weapon")
            condition = armament.get("RequiresCondition") or ""
            if "Resonance" in weapon:
                self.assertIn("steelconsortium_upgrade_resonanceammo", condition)
                self.assertNotIn("!steelconsortium_upgrade_resonanceammo", condition)
            else:
                self.assertIn("!steelconsortium_upgrade_resonanceammo", condition)

    def test_quasar_weapons_have_one_definition_and_keep_merged_values(self):
        path = (ROOT / "mods" / "cameo" / "ContentPacks" / "RedAlert2Mod" /
                "AsianAlliance" / "yaml" / "weapons.yaml")
        keys = [node.key for node in load(path)]
        self.assertEqual(1, keys.count("AsianQuasarBoatAG"))
        self.assertEqual(1, keys.count("AsianQuasarBoat_AA"))

        expected = {
            "AsianQuasarBoatAG": ("7168", "3", "512", "192"),
            "AsianQuasarBoatAG_EMP": ("7168", "3", "512", "192"),
            "AsianQuasarBoat_AA": ("7168", "3", "250", "256"),
            "AsianQuasarBoat_EMP_AA": ("7168", "3", "250", "256"),
        }
        for name, (range_value, burst_delay, inaccuracy, launch_speed) in expected.items():
            weapon = self.rules.resolve_weapon(name)
            projectile = child(weapon, "Projectile")
            self.assertEqual(range_value, weapon.get("Range"), name)
            self.assertEqual(burst_delay, weapon.get("BurstDelays"), name)
            self.assertEqual(inaccuracy, projectile.get("Inaccuracy"), name)
            self.assertEqual(launch_speed, projectile.get("MaximumLaunchSpeed"), name)

    def test_new_effect_roots_are_explicitly_non_emissive(self):
        names = {
            "^Effect_Cryo",
            "^Effect_Demolition_Heavy_D2K_Orni",
            "^Effect_MissileAP_Heavy_D2K_ORocket",
        }
        self.assertTrue(names <= glow_audit.NON_EMISSIVE_EFFECT_ROOTS)
        effects = {
            name for name in self.rules.weapons if name.startswith("^Effect")
        }
        sprite_effects = {
            name for name in effects
            if glow_audit.has_impact_sprite(self.rules.resolve_weapon(name))
        }
        tier_memo = {}
        for name in names:
            resolved = self.rules.resolve_weapon(name)
            self.assertFalse(glow_audit.has_impact_glow(resolved), name)
            self.assertEqual(
                name, glow_audit.sprite_root(self.rules, name, sprite_effects), name)
            self.assertEqual(
                0, glow_audit.tier_path_count(self.rules, name, tier_memo), name)

    def test_mig_elite_doctrine_weapons_use_distinct_armament_slots(self):
        actor = self.rules.resolve("ra2_soviets_migbomber")
        expected = {
            "Armament@PRIMARYELITERad": (
                "MigMissiles_rad_elite",
                "rank-elite && ra2_soviets_doctrine_nuclearmunitions"),
            "Armament@PRIMARYELITEFire": (
                "MigMissiles_fire_elite",
                "rank-elite && ra2_soviets_doctrine_firemunitions"),
            "Armament@PRIMARYELITETesla": (
                "MigMissiles_tesla_elite",
                "rank-elite && ra2_soviets_doctrine_teslamunitions"),
        }
        for key, (weapon, condition) in expected.items():
            armament = actor.child(key)
            self.assertIsNotNone(armament, key)
            self.assertEqual(weapon, armament.get("Weapon"), key)
            self.assertEqual(condition, armament.get("RequiresCondition"), key)

    def test_tkm_rocketeer_garrison_tracks_each_rocket_upgrade(self):
        actor = self.rules.resolve("tkm_rocketeer")
        expected = {
            "Armament@GARRISONED": (
                "tkmrockets",
                "!tkm_upgrade_cryorocketsupgrade && "
                "!tkm_upgrade_twinrocketsupgrade && "
                "!tkm_upgrade_incendiaryrocketsupgrade"),
            "Armament@GARRISONEDTITAN": (
                "tkmcryorockets", "tkm_upgrade_cryorocketsupgrade"),
            "Armament@GARRISONEDBEREZKA": (
                "tkmtwinrockets", "tkm_upgrade_twinrocketsupgrade"),
            "Armament@GARRISONEDNATO": (
                "tkmfirerockets", "tkm_upgrade_incendiaryrocketsupgrade"),
        }
        for key, (weapon, condition) in expected.items():
            armament = actor.child(key)
            self.assertEqual("garrisoned", armament.get("Name"), key)
            self.assertEqual(weapon, armament.get("Weapon"), key)
            self.assertEqual(condition, armament.get("RequiresCondition"), key)

    def test_repair_defuse_warhead_keeps_merged_geometry(self):
        weapon = self.rules.resolve_weapon("^RepairWeapon")
        defuse = weapon.child("Warhead@Defuse1")
        self.assertEqual("DetachDelayedWeapon", defuse.value)
        self.assertEqual("2000", defuse.get("Spread"))
        self.assertEqual("100, 50", defuse.get("Falloff"))
        self.assertEqual("2000", defuse.get("Range"))
        self.assertEqual("defilerplague", defuse.get("Types"))
        self.assertEqual("Ally", defuse.get("ValidRelationships"))

    def test_reviewed_active_inheritance_labels_are_unique(self):
        names = {
            "^BasicUnit",
            "^RAFIX",
            "asianalliance_asianservicedepot",
            "cabal_cyborgcommando",
            "cabal_cyborgcommandov2",
            "cabal_eliminator800",
            "cabal_servicedepot",
            "forgotten_servicedepot",
            "harkonnen_repairpad",
            "ixian_repairpad",
            "japan_waveforceturret",
            "latinsyndicate_syndicateservicedepot",
            "naxis_naxibunker",
            "ordos_repairpad",
            "protoss_assimilator",
            "ra1_soviets_barracks",
            "ra2_allies_alliedservicedepot",
            "ra2_soviets_servicedepot",
            "td_gdi_advancedcommunicationscenter",
            "td_gdi_advancedguardtower",
            "td_gdi_repairfacility",
            "td_nod_chemicalattackbike",
            "td_nod_repairfacility",
            "td_nod_templeofnod",
            "terran_medivac",
            "terran_pythean",
            "terran_refinery",
            "terran_supplydepot",
            "tkm_airpad",
            "tkm_orerefinery",
            "tkmratflakdeployed",
            "ts_gdi_powerplant",
            "ts_gdi_servicedepot",
            "ts_nod_servicedepot",
            "wc2_humans_humanscouttower",
            "wc2_orcs_orcwatchtower",
            "zerg_creepcolony",
            "zerg_extractor",
            "zerg_spire",
            "latinsyndicate_missiletruck",
            "latinsyndicate_burrito",
            "latinsyndicate_lars",
            "latinsyndicate_mig21",
            "^ScoutVehicleTemplate",
            "^SupportVehicleTemplate",
        }
        for name in sorted(names):
            actor = self.rules.actor(name)
            labels = [node.key for node in actor.children
                      if node.key == "Inherits" or node.key.startswith("Inherits@")]
            self.assertEqual(len(labels), len(set(labels)), name)

    def test_active_actor_and_weapon_rules_have_no_exact_duplicate_traits(self):
        def fingerprint(node):
            return (node.key, node.value,
                    tuple(fingerprint(item) for item in node.children))

        findings = []

        def inspect(node, path):
            groups = defaultdict(list)
            for item in node.children:
                if item.key and not item.key.startswith("-"):
                    groups[item.key].append(item)

            for key, items in groups.items():
                fingerprints = [fingerprint(item) for item in items]
                if len(items) > 1 and len(set(fingerprints)) == 1:
                    findings.append(
                        f"{path} > {key} at "
                        f"{', '.join(str(item.line) for item in items)}")

            for item in node.children:
                inspect(item, f"{path} > {item.key}")

        paths = self.rules.manifest.rules + self.rules.manifest.weapons
        for path in paths:
            for node in load(path):
                inspect(node, f"{path.relative_to(ROOT)}:{node.key}")

        self.assertEqual([], findings)

    def test_reviewed_redundant_active_traits_are_unique(self):
        expected = {
            "^D2KInfantry": {"Passenger"},
            "SCSPIDERMINE": {"AutoTarget"},
            "SNOWHUT": {"RenderSprites"},
            "asianalliance_chaostower": {"Selectable"},
            "cabal_constructionyard": {"Selectable"},
            "cabal_core": {"Selectable", "WithIdleOverlay@LIGHTS2"},
            "duelist_tank.ixian": {"ActorStatValues"},
            "ixian_ixcombatsiege": {"ActorStatValues"},
            "ixian_rocketturret": {"AttackTurreted"},
            "japan_japaneseflamethrower": {"UpdatesPlayerStatistics"},
            "latinsyndicate_combatbarracks": {"GivesBuildableArea"},
            "latinsyndicate_defensebureau": {"GivesBuildableArea"},
            "latinsyndicate_spycenter": {"WithIdleOverlay@lights"},
            "ordos_airmine": {"AutoTarget"},
            "ra1_soviets_barracks": {"ProvidesPrerequisite"},
            "ra1_soviets_monstertank": {"WithAmmoPipsDecoration"},
            "ra2_allies_blackeagle": {"Selectable"},
            "ra2_allies_guardiangi": {"ActorStatValues"},
            "ra2_soviets_teslatrooper": {"ActorStatValues"},
            "ra2dest": {"Selectable"},
            "ra2sidewind": {"Voiced"},
            "ra2sqd": {"AttackFrontal"},
            "ts_gdi_constructionyard": {"Selectable"},
            "tkm_abrams": {"Selectable"},
            "tkm_as42": {"ActorStatValues"},
            "tkm_t72m": {"Selectable"},
            "tkm_technicaltank": {"Selectable"},
            "tkm_tornadoglauncher": {"ActorStatValues"},
            "tkm_trenchtank": {"Selectable"},
            "tkm_trenchtruck": {"Selectable"},
            "ts_gdi_techcenter": {"Selectable"},
            "ts_gdi_titan": {"RenderVoxels"},
            "ts_nod_constructionyard": {"Selectable"},
            "ts_nod_mobilestealthgenerator": {"ActorStatValues"},
            "tsun.asian": {"ActorStatValues"},
            "wc2_humans_townhall": {"Refinery"},
            "wc2_orcs_greathall": {"Refinery"},
            "yrbpln": {"Contrail@1", "Contrail@2"},
            "zerg_behemoth": {"ActorStatValues"},
        }
        for actor_name, keys in expected.items():
            actor = self.rules.actor(actor_name)
            self.assertIsNotNone(actor, actor_name)
            for key in keys:
                count = sum(item.key == key for item in actor.children)
                self.assertEqual(1, count, f"{actor_name} > {key}")

    def test_active_actor_and_weapon_rules_have_no_duplicate_traits(self):
        expected = set()
        findings = set()
        paths = self.rules.manifest.rules + self.rules.manifest.weapons
        for path in paths:
            for actor in load(path):
                groups = defaultdict(list)
                for index, item in enumerate(actor.children):
                    if item.key and not item.key.startswith("-"):
                        groups[item.key].append(index)

                for key, indexes in groups.items():
                    if len(indexes) <= 1:
                        continue
                    removal = f"-{key}"
                    between = actor.children[indexes[0] + 1:indexes[-1]]
                    marker = removal if any(
                        item.key == removal for item in between) else "<missing>"
                    findings.add((actor.key, key, marker))

        self.assertEqual(expected, findings)


if __name__ == "__main__":
    unittest.main()
