"""Regression coverage for the active legacy gatling migration."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from cameo_model import Model  # noqa: E402


MIGRATED = (
    "ra1_allies_alliedheavyaatank",
    "ra1_soviets_gatlingtank",
    "ra1_soviets_btr80",
    "japan_armoredcar",
    "japan_japanesespeedboat",
    "tkm_zaza",
)


class GatlingUnificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Model(ROOT).rs

    def test_migrated_actors_resolve_the_standard_spin_up_contract(self):
        for actor in MIGRATED:
            with self.subTest(actor=actor):
                local = self.rules.actors[actor]
                resolved = self.rules.resolve(actor)
                self.assertEqual(
                    local.child("Inherits@gat").value,
                    "^GatlingSpinUpUnitBehavior",
                )

                for trait in (
                    "PhysicalState@SpinUp",
                    "SynchronizesPhysicalStateWithCondition@SpinUp",
                    "SelectedPhysicalStateBar@SpinUp",
                    "ModifiesCombatProportionalToPhysicalState@SpinUp",
                    "GrantConditionOnAttack@gatling",
                    "GrantConditionOnAttack@elitegatling",
                ):
                    self.assertEqual(
                        sum(child.key == trait for child in resolved.children),
                        1,
                        trait,
                    )

                modifier = resolved.child(
                    "ModifiesCombatProportionalToPhysicalState@SpinUp"
                )
                self.assertEqual(modifier.get("ReloadDelayTo"), "60")
                self.assertEqual(modifier.get("RangeTo"), "122")
                self.assertEqual(modifier.get("SpeedTo"), "60")

                normal = resolved.child("GrantConditionOnAttack@gatling")
                elite = resolved.child("GrantConditionOnAttack@elitegatling")
                self.assertEqual(normal.get("MaximumInstances"), "10")
                self.assertEqual(elite.get("MaximumInstances"), "10")
                self.assertEqual(normal.get("ArmamentNames"), "primary, garrisoned")
                self.assertEqual(elite.get("ArmamentNames"), "primary, garrisoned")

                if actor != "ra1_soviets_btr80":
                    self.assertEqual(normal.get("RequiresCondition"), "!rank-elite")
                    self.assertEqual(elite.get("RequiresCondition"), "rank-elite")
                    self.assertIsNone(local.child("GrantConditionOnAttack@gatling"))
                    self.assertIsNone(local.child("GrantConditionOnAttack@elitegatling"))

    def test_dummy_ammo_ladders_are_removed(self):
        for actor in MIGRATED:
            with self.subTest(actor=actor):
                local = self.rules.actors[actor]
                legacy = [
                    child.key
                    for child in local.children
                    if child.key.startswith((
                        "ReloadDelayMultiplier@GattlingSpeed",
                        "RangeMultiplier@GattlingSpeed",
                        "FirepowerMultiplier@GattlingSpeed1",
                        "FirepowerMultiplier@GattlingSpeed2",
                        "FirepowerMultiplier@GattlingSpeed3",
                    ))
                ]
                self.assertEqual(legacy, [])

        for actor in (
            "ra1_allies_alliedheavyaatank",
            "ra1_soviets_gatlingtank",
            "ra1_soviets_btr80",
            "japan_armoredcar",
        ):
            with self.subTest(actor=actor):
                local = self.rules.actors[actor]
                self.assertIsNone(local.child("AmmoPool"))
                self.assertIsNone(local.child("ReloadAmmoPool"))

    def test_btr_spin_up_is_fully_promotion_gated(self):
        actor = self.rules.resolve("ra1_soviets_btr80")
        promotion = "ra1_soviets_promotion_gatlingtank"
        self.assertEqual(
            actor.child("ModifiesCombatProportionalToPhysicalState@SpinUp").get(
                "RequiresCondition"
            ),
            promotion,
        )
        self.assertEqual(
            actor.child("SelectedPhysicalStateBar@SpinUp").get("RequiresCondition"),
            promotion,
        )
        self.assertEqual(
            actor.child("GrantConditionOnAttack@gatling").get("RequiresCondition"),
            f"!rank-elite && {promotion}",
        )
        self.assertEqual(
            actor.child("GrantConditionOnAttack@elitegatling").get(
                "RequiresCondition"
            ),
            f"rank-elite && {promotion}",
        )

    def test_btr_decay_allows_sustained_single_armament_spin_up(self):
        actor = self.rules.resolve("ra1_soviets_btr80")
        normal = actor.child("GrantConditionOnAttack@gatling")
        elite = actor.child("GrantConditionOnAttack@elitegatling")
        modifier = actor.child("ModifiesCombatProportionalToPhysicalState@SpinUp")

        base_weapon = self.rules.resolve_weapon(
            actor.child("Armament").get("Weapon")
        )
        tesla_weapon = self.rules.resolve_weapon(
            actor.child("Armament@TeslaUpgrade1").get("Weapon")
        )
        for weapon in (base_weapon, tesla_weapon):
            self.assertEqual(weapon.get("ReloadDelay"), "20")
            self.assertEqual(weapon.get("Burst"), "4")

        def sustained_stacks(
            producer,
            revoke_delay,
            rank_reload=100,
            doctrine_reload=200,
            arms_per_shot=1,
        ):
            requirements = [
                int(value)
                for value in producer.get("RequiredShotsPerInstance").split(",")
            ]
            maximum = int(producer.get("MaximumInstances"))
            start = int(modifier.get("ReloadDelayFrom"))
            end = int(modifier.get("ReloadDelayTo"))
            stacks = progress = cooldown = 0

            def wait(ticks):
                nonlocal stacks, progress, cooldown
                for _ in range(ticks):
                    if progress > 0 or stacks > 0:
                        cooldown -= 1
                        if cooldown == 0:
                            cooldown = revoke_delay
                            progress = 0
                            stacks = max(0, stacks - 1)

            for _ in range(40):
                for shot in range(4):
                    for _ in range(arms_per_shot):
                        cooldown = revoke_delay
                        if stacks < maximum:
                            progress += 1
                            required = requirements[
                                min(stacks, len(requirements) - 1)
                            ]
                            if progress >= required:
                                stacks += 1
                                progress = 0

                    if shot < 3:
                        wait(int(base_weapon.get("BurstDelays")))

                spin_modifier = round(start + (end - start) * stacks / maximum)
                reload_ticks = int(
                    int(base_weapon.get("ReloadDelay"))
                    * doctrine_reload
                    / 100
                    * rank_reload
                    / 100
                    * spin_modifier
                    / 100
                )
                wait(reload_ticks)

            return stacks

        self.assertLess(sustained_stacks(normal, 36), 10)
        self.assertEqual(sustained_stacks(normal, 37), 10)
        self.assertEqual(sustained_stacks(normal, 37, doctrine_reload=100), 10)
        self.assertEqual(sustained_stacks(normal, 37, arms_per_shot=2), 10)
        self.assertEqual(int(normal.get("RevokeDelay")), 37)

        elite_rank = int(actor.child("ReloadDelayMultiplier@RANK-ELITE").get("Modifier"))
        self.assertEqual(elite_rank, 60)
        self.assertEqual(int(elite.get("RevokeDelay")), 15)
        self.assertEqual(sustained_stacks(elite, 15, elite_rank), 10)
        self.assertEqual(
            sustained_stacks(elite, 15, elite_rank, doctrine_reload=100),
            10,
        )

        # At full spin each qualifying shot refreshes the cooldown. Once fire
        # stops, RevokeAll=false removes exactly one stack at the delay.
        self.assertEqual(normal.get("RevokeAll"), "false")
        self.assertEqual(elite.get("RevokeAll"), "false")

    def test_other_migrations_keep_standard_decay(self):
        for actor_name in set(MIGRATED) - {"ra1_soviets_btr80"}:
            with self.subTest(actor=actor_name):
                actor = self.rules.resolve(actor_name)
                self.assertEqual(
                    actor.child("GrantConditionOnAttack@gatling").get("RevokeDelay"),
                    "30",
                )
                self.assertEqual(
                    actor.child("GrantConditionOnAttack@elitegatling").get(
                        "RevokeDelay"
                    ),
                    "15",
                )

    def test_remaining_soviet_non_spin_compensators_remain_intact(self):
        for actor_name in ("ra1_soviets_btr80", "ra1_soviets_gatlingtank"):
            with self.subTest(actor=actor_name):
                actor = self.rules.resolve(actor_name)
                doctrine = actor.child("ReloadDelayMultiplier@Gatling")
                self.assertEqual(doctrine.get("Modifier"), "200")
                self.assertEqual(
                    doctrine.get("RequiresCondition"),
                    "ra1_soviets_doctrine_teslaandexperimentaltech",
                )


if __name__ == "__main__":
    unittest.main()
