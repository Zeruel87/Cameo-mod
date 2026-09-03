"""Regression checks for weapons that advertise Air as a valid target."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import audit_stat_formulas as formulas
from miniyaml import Ruleset


class AirPayloadContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_advertised_air_damage_cohort_delivers_an_air_payload(self):
        names = {
            "TSAssaultCannon",
            "TSAssaultCannonSonic",
            "TSAssaultCannonTal",
            "TSAssaultCannonTalSonic",
            "TSFiendShard",
            "TSFiendShardUP",
            "TSFiendShardBlue",
            "TSFiendShardBlueUP",
            "VenomLaserInferno",
            "VenomLaserBurning",
            "CabalOverkillCharge",
            "PsionicShockwave",
        }
        for name in sorted(names):
            weapon = self.rules.resolve_weapon(name)
            self.assertTrue(formulas.targets_air(weapon), name)
            self.assertTrue(
                formulas.has_air_payload(self.rules, weapon), name)

    def test_fiend_damage_layers_all_reach_air(self):
        for name in ("TSFiendShard", "TSFiendShardUP",
                     "TSFiendShardBlue", "TSFiendShardBlueUP"):
            weapon = self.rules.resolve_weapon(name)
            damage_layers = [
                node for node in weapon.children
                if node.value in ("AreaDamage", "AreaDamagePercentage")
                and formulas.positive_damage(node)
            ]
            self.assertTrue(damage_layers, name)
            self.assertTrue(
                all(formulas.targets_air(node) for node in damage_layers), name)

    def test_ground_cloud_does_not_advertise_air_targeting(self):
        weapon = self.rules.resolve_weapon("NaxDieGlocke")
        self.assertFalse(formulas.targets_air(weapon))
        damage = weapon.child("Warhead@Chemical_Heavy")
        self.assertEqual("10000", damage.get("Damage"))
        self.assertEqual("Ground, Water", damage.get("ValidTargets"))

        source = self.rules.actor("schwarzermond_dieglocke")
        parents = {node.key: node.value for node in source.children
                   if node.key.startswith("Inherits")}
        self.assertNotIn("^PrioritizeAir", parents.values())

    def test_archon_autonomous_targeting_matches_its_air_weapon(self):
        source = self.rules.actor("protoss_archon")
        parent = source.child("Inherits@AUTOTARGET")
        self.assertEqual("^AutoTargetAllAssaultMove", parent.value)
        resolved = self.rules.resolve("protoss_archon")
        priorities = resolved.children_named("AutoTargetPriority")
        target_sets = [node.get("ValidTargets") or "" for node in priorities]
        self.assertTrue(any("Air" in targets for targets in target_sets))

    def test_delayed_and_cluster_payloads_are_not_false_positives(self):
        for name in ("DefilerPlague", "wc2DeathKnightDeathAndDecay",
                     "wc2MageBlizzard"):
            weapon = self.rules.resolve_weapon(name)
            self.assertTrue(formulas.targets_air(weapon), name)
            self.assertTrue(
                formulas.has_air_payload(self.rules, weapon), name)

        plague_dummy = self.rules.resolve_weapon("RemovableDebuffDummy")
        cloud_delivery = plague_dummy.child("Warhead@Cloud")
        self.assertEqual("SpawnSmokeParticle", cloud_delivery.value)
        self.assertEqual("AnthraxCloudBlueLarge", cloud_delivery.get("Weapon"))
        cloud = self.rules.resolve_weapon(cloud_delivery.get("Weapon"))
        toxic = cloud.child("Warhead@Toxic_Light")
        self.assertTrue(formulas.positive_damage(toxic))
        self.assertTrue(formulas.targets_air(toxic))

    def test_target_only_helpers_are_not_positive_damage(self):
        weapon = self.rules.resolve_weapon("BeeHiveCarrierTarget")
        target = weapon.child("Warhead@1Dam")
        self.assertEqual("TargetDamage", target.value)
        self.assertFalse(formulas.positive_damage(target))

        harpy = self.rules.resolve_weapon("TSHarpyMultiClaw")
        self.assertEqual("0", harpy.child("Warhead@Bullet_Medium").get("Damage"))
        concrete = harpy.child("Warhead@Concrete")
        self.assertEqual("25", concrete.get("Damage"))
        self.assertFalse(formulas.positive_damage(concrete))
        self.assertFalse(formulas.has_air_payload(self.rules, harpy))

    def test_point_defense_is_not_misclassified_as_unit_anti_air(self):
        for name in ("PDLaserBike", "PDLaserLTNK2", "TKMPDLaser"):
            weapon = self.rules.resolve_weapon(name)
            self.assertTrue(formulas.targets_air(weapon), name)
            self.assertTrue(formulas.is_point_defense(weapon), name)

    def test_missing_warhead_targets_keep_engine_all_target_default(self):
        weapon = self.rules.resolve_weapon("PDLaserBike")
        damage = weapon.child("Warhead@1Dam")
        self.assertIsNone(damage.get("ValidTargets"))
        self.assertTrue(formulas.targets_air(damage, default_all=True))


if __name__ == "__main__":
    unittest.main()
