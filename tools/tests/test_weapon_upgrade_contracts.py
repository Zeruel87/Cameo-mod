"""Resolved-rules contracts for paid weapon replacements."""

from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

import audit_upgrade_regression as upgrade
from audit_three_way_split import (
    RAW_SPLIT_BASELINE,
    main_warhead_nodes,
    validated_reviewed_predicate,
    main_warheads,
)
from cameo_model import Model


class WeaponUpgradeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rs = Model().rs

    def _warhead(self, weapon_name: str, key: str):
        node = self.rs.resolve_weapon(weapon_name)
        self.assertIsNotNone(node)
        warhead = next((c for c in node.children if c.key == key), None)
        self.assertIsNotNone(warhead, f"{weapon_name} must resolve {key}")
        return warhead

    def _assert_not_weaker(self, base: str, upgraded: str, armors):
        b = upgrade.armament_profile(self.rs, (base,))
        u = upgrade.armament_profile(self.rs, (upgraded,))
        self.assertIsNotNone(b)
        self.assertIsNotNone(u)
        for armor in armors:
            base_dps = b["per_armor"].get(armor, 0)
            if base_dps > 0:
                self.assertGreaterEqual(
                    u["per_armor"].get(armor, 0), base_dps,
                    f"{upgraded} regressed against {armor} versus {base}")

    def test_parallel_upgrade_beams_are_compared_as_one_firing_group(self):
        pairs = [p for p in upgrade.pairs(self.rs) if p[0] == "japan_waveforcetank"]
        self.assertIn((
            "japan_waveforcetank", ("WaveforceCannon",),
            ("WaveforceCannonChargedLaser", "WaveforceCannonDistortedBeam1",
             "WaveforceCannonDistortedBeam2"),
            "japan_upgrade_advancedplasmaweapons", "primary"), pairs)

    def test_attack_route_pairs_upgrades_that_switch_armament_names(self):
        pairs = [p for p in upgrade.pairs(self.rs) if p[0] == "ts_gdi_wolverine"]
        self.assertIn((
            "ts_gdi_wolverine", ("TSAssaultCannon",),
            ("TSAssaultCannonSonic",), "ts_gdi_upgrade_sonicweaponry", "attack"), pairs)

        pairs = [p for p in upgrade.pairs(self.rs) if p[0] == "ts_gdi_mammothmkii"]
        self.assertIn((
            "ts_gdi_mammothmkii", ("TSMechRailgunII",),
            ("TSMechRailgunRailII",), "ts_gdi_upgrade_railgunweaponry", "attack"), pairs)

    def test_air_only_base_keeps_air_verdict_if_upgrade_targets_more(self):
        self.assertEqual(
            upgrade.verdict_armors({"air_only": True}, list(upgrade.CORE)), upgrade.AIR)

    def test_garrisoned_mode_is_not_combined_with_primary_fire(self):
        pairs = [p for p in upgrade.pairs(self.rs) if p[0] == "ts_gdi_discthrower"]
        self.assertEqual({p[4] for p in pairs}, {"primary", "garrisoned"})

    def test_cryo_cargo_bomb_preserves_bomb_delivery_and_full_raw_payload(self):
        weapon = self.rs.resolve_weapon("ParaBombCryo")
        self.assertEqual(weapon.get("ReloadDelay"), "8")
        self.assertEqual(weapon.get("Range"), "5000")
        self.assertEqual(weapon.get("Projectile"), "GravityBomb")
        self.assertEqual(weapon.get("Projectile", "Image"), "PARABOMB")
        cryo = self._warhead("ParaBombCryo", "Warhead@CryoBlast_Heavy")
        self.assertEqual(cryo.get("Damage"), "40000")
        self.assertEqual(cryo.get("PhysicalStates", "Temperature"), "-67")
        self.assertEqual(
            {c.key for c in weapon.children if c.key.startswith("Warhead")},
            {"Warhead@CryoBlast_Heavy", "Warhead@Effect", "Warhead@EffectWater",
             "Warhead@EffectAir"})

    def test_thunderbolt_patriot_is_an_anti_air_upgrade(self):
        self.assertEqual(
            self._warhead("RA2PatriotThunderboltMissile", "Warhead@MissileAA_Heavy").get("Damage"),
            "10000")
        self._assert_not_weaker("RA2Patriot", "RA2PatriotThunderboltMissile", upgrade.AIR)

    def test_armor_piercing_officer_round_preserves_base_payload_and_range(self):
        weapon = self.rs.resolve_weapon("OfficerMachineGunAP")
        self.assertEqual(weapon.get("Range"), "5596")
        self.assertEqual(self._warhead("OfficerMachineGunAP", "Warhead@Bullet_Medium").get("Damage"),
                         "16000")
        self._assert_not_weaker("OfficerMachineGun", "OfficerMachineGunAP", upgrade.CORE)

    def test_ts_paid_replacements_do_not_reduce_centered_core_damage(self):
        for base, upgraded in (
                ("TSGrenadeG", "TSGrenadeSonic"),
                ("TS30mm", "TS30mmRail"),
                ("KodiakCannon", "KodiakCannonSonic"),
                ("TSHellfire", "TSHellfireSonic"),
                ("TSZoneHellfire", "TSZoneHellfireSonic")):
            with self.subTest(base=base, upgraded=upgraded):
                self._assert_not_weaker(base, upgraded, upgrade.CORE + upgrade.AIR)

        expected_delivery = {
            "TSGrenadeSonic": ("45", "6656", "Ground, Water"),
            "TS30mmRail": ("26", "6125", "Ground, Water, Air"),
            "TSAssaultCannonTalSonic": ("45", "6520", "Ground, Water, Air"),
            "KodiakCannonSonic": ("86", "9165", "Ground, Water"),
            "TSHellfireSonic": ("32", "6144", "Ground, Water, Air"),
            "TSZoneHellfireSonic": ("28", "6138", "Ground, Water, Air"),
        }
        for weapon_name, expected in expected_delivery.items():
            weapon = self.rs.resolve_weapon(weapon_name)
            self.assertEqual(
                (weapon.get("ReloadDelay"), weapon.get("Range"), weapon.get("ValidTargets")),
                expected)

        kodiak_projectile = self.rs.resolve_weapon("KodiakCannonSonic").child("Projectile")
        self.assertEqual(kodiak_projectile.value, "Bullet")
        self.assertIsNone(kodiak_projectile.get("TrailImage"))
        self.assertIsNone(kodiak_projectile.get("PointDefenseTypes"))

    def test_sonic_hellfire_remains_raw_debt_without_an_exemption(self):
        self.assertLessEqual(RAW_SPLIT_BASELINE, 322)
        mains = main_warheads(self.rs.resolve_weapon("TSHellfireSonic"))
        self.assertEqual(["MissileAP_Heavy", "Sonic_Medium"], mains)
        reviewed = validated_reviewed_predicate(self.rs, main_warhead_nodes)
        self.assertFalse(reviewed("TSHellfireSonic", mains))
        self.assertFalse(reviewed("CopiedHellfireSonic", mains))
        self.assertFalse(reviewed("TSHellfireSonic", mains + ["Sonic_Heavy"]))

    def test_quantum_emp_anti_air_replacements_increase_damage(self):
        for base, upgraded in (
                ("SteelScalpelRailgunAA", "SteelScalpelRailgun_EMP_AA"),
                ("ConsortiumMissileSystem", "ConsortiumMissileSystem_EMP")):
            with self.subTest(base=base, upgraded=upgraded):
                self._assert_not_weaker(base, upgraded, upgrade.AIR)


if __name__ == "__main__":
    unittest.main()
