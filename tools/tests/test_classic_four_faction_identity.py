"""Resolved contract for the classic-four Rocket Soldier identity split."""

from fractions import Fraction
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset  # noqa: E402


ROCKET_SOLDIERS = {
    # actor: cost, hp, speed, self-heal, weapon, range, damage, reload
    "td_gdi_rocketsoldier":
        (450, 16000, 42, 16, "td_gdi_rocketsoldier_rockets", 6500, 15800, 56),
    "td_nod_rocketsoldier":
        (390, 14000, 48, 14, "td_nod_rocketsoldier_rockets", 6028, 16882, 56),
    "ra1_allies_alliedrocketsoldier":
        (480, 13000, 54, 13,
         "ra1_allies_alliedrocketsoldier_rocketsra", 7500, 11500, 50),
    "ra1_soviets_rocketsoldier":
        (440, 15000, 46, 15,
         "ra1_soviets_rocketsoldier_rocketsra", 6910, 13216, 50),
}

DAMAGE_TRAITS = {
    "td_gdi_rocketsoldier_rockets": "Warhead@MissileAP_Light",
    "td_gdi_rocketsoldier_rocketsamt": "Warhead@MissileAP_Light",
    "td_nod_rocketsoldier_rockets": "Warhead@MissileAP_Light",
    "ra1_allies_alliedrocketsoldier_rocketsra":
        "Warhead@MissileAP_Medium_Flat",
    "ra1_allies_alliedrocketsoldier_rocketsracryo":
        "Warhead@MissileCryo_Medium",
    "ra1_soviets_rocketsoldier_rocketsra":
        "Warhead@MissileAP_Medium_Flat",
}


class ClassicFourFactionIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def weapon_damage(self, weapon_name):
        weapon = self.rules.resolve_weapon(weapon_name)
        return int(weapon.child(DAMAGE_TRAITS[weapon_name]).get("Damage"))

    def test_each_faction_has_a_distinct_resolved_identity(self):
        axes = {"cost": [], "hp": [], "speed": [], "range": [], "damage": []}
        for actor_name, spec in ROCKET_SOLDIERS.items():
            actor = self.rules.resolve(actor_name)
            cost, hp, speed, healing, weapon_name, range_, damage, _ = spec
            weapon = self.rules.resolve_weapon(weapon_name)

            self.assertEqual("Flak", actor.child("Armor").get("Type"), actor_name)
            self.assertEqual(cost, int(actor.child("Valued").get("Cost")), actor_name)
            self.assertEqual(hp, int(actor.child("Health").get("HP")), actor_name)
            self.assertEqual(speed, int(actor.child("Mobile").get("Speed")), actor_name)
            self.assertEqual(
                healing,
                int(actor.child("ChangesHealth@SelfHealing").get("Step")),
                actor_name,
            )
            self.assertEqual(range_, int(weapon.get("Range")), weapon_name)
            self.assertEqual(damage, self.weapon_damage(weapon_name), weapon_name)

            for axis, value in zip(
                axes,
                (cost, hp, speed, range_, damage),
            ):
                axes[axis].append(value)

        for axis, values in axes.items():
            self.assertEqual(4, len(set(values)), axis)

    def test_cohort_means_and_source_cadence_budgets_are_preserved(self):
        specs = list(ROCKET_SOLDIERS.values())
        self.assertEqual(Fraction(440), Fraction(sum(x[0] for x in specs), 4))
        self.assertEqual(Fraction(14500), Fraction(sum(x[1] for x in specs), 4))
        self.assertEqual(30000, specs[0][1] + specs[1][1])
        self.assertEqual(28000, specs[2][1] + specs[3][1])
        self.assertEqual(Fraction(95, 2), Fraction(sum(x[2] for x in specs), 4))
        self.assertEqual(Fraction(13469, 2), Fraction(sum(x[5] for x in specs), 4))
        self.assertEqual(Fraction(28699, 2), Fraction(sum(x[6] for x in specs), 4))

        # Keeping each source pair's damage sum also keeps exact total nominal DPS,
        # because both TD weapons use reload 56 and both RA weapons use reload 50.
        self.assertEqual(32682, specs[0][6] + specs[1][6])
        self.assertEqual(24716, specs[2][6] + specs[3][6])
        old_total_dps = 2 * Fraction(16341, 56) + 2 * Fraction(12358, 50)
        new_total_dps = sum(Fraction(x[6], x[7]) for x in specs)
        self.assertEqual(old_total_dps, new_total_dps)

    def test_targeting_cadence_armor_and_upgrade_gates_are_unchanged(self):
        for actor_name, spec in ROCKET_SOLDIERS.items():
            weapon_name, reload = spec[4], spec[7]
            weapon = self.rules.resolve_weapon(weapon_name)
            self.assertEqual("Ground, Water, Air", weapon.get("ValidTargets"), weapon_name)
            self.assertEqual(reload, int(weapon.get("ReloadDelay")), weapon_name)
            self.assertIsNone(weapon.get("Burst"), weapon_name)
            self.assertIsNone(weapon.get("BurstDelays"), weapon_name)

        gdi = self.rules.resolve("td_gdi_rocketsoldier")
        self.assertEqual(
            "!td_gdi_upgrade_advancedmissiletargeting",
            gdi.child("Armament@PRIMARY").get("RequiresCondition"),
        )
        self.assertEqual(
            "td_gdi_upgrade_advancedmissiletargeting",
            gdi.child("Armament@AdvancedMissileTargeting").get("RequiresCondition"),
        )
        allies = self.rules.resolve("ra1_allies_alliedrocketsoldier")
        self.assertEqual(
            "!ra1_allies_upgrade_cryomissiles",
            allies.child("Armament@PRIMARY").get("RequiresCondition"),
        )
        self.assertEqual(
            "ra1_allies_upgrade_cryomissiles",
            allies.child("Armament@Upgrade").get("RequiresCondition"),
        )

    def test_actor_owned_upgrade_weapons_stay_synchronized(self):
        pairs = (
            ("td_gdi_rocketsoldier_rockets", "td_gdi_rocketsoldier_rocketsamt"),
            ("ra1_allies_alliedrocketsoldier_rocketsra",
             "ra1_allies_alliedrocketsoldier_rocketsracryo"),
        )
        for normal_name, upgrade_name in pairs:
            normal = self.rules.resolve_weapon(normal_name)
            upgrade = self.rules.resolve_weapon(upgrade_name)
            self.assertEqual(normal.get("Range"), upgrade.get("Range"), normal_name)
            self.assertEqual(normal.get("ReloadDelay"), upgrade.get("ReloadDelay"), normal_name)
            self.assertEqual(
                self.weapon_damage(normal_name),
                self.weapon_damage(upgrade_name),
                normal_name,
            )

    def test_generic_e3_map_alias_keeps_compatibility_stats_and_weapons(self):
        actor = self.rules.resolve("e3")
        self.assertEqual("300", actor.child("Valued").get("Cost"))
        self.assertEqual("9000", actor.child("Health").get("HP"))
        self.assertEqual("50", actor.child("Mobile").get("Speed"))
        self.assertEqual("9", actor.child("ChangesHealth@SelfHealing").get("Step"))
        self.assertEqual("Rockets", actor.child("Armament@PRIMARY").get("Weapon"))
        self.assertEqual(
            "RocketsAMT",
            actor.child("Armament@AdvancedMissileTargeting").get("Weapon"),
        )


if __name__ == "__main__":
    unittest.main()
