"""Actor-level attack cadence must reach Cameo's reference weapon model."""

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools" / "audit"), str(ROOT / "tools" / "balance")]

import armament_roles as ar  # noqa: E402
import miniyaml  # noqa: E402
import reference_distribution as rd  # noqa: E402


def armament(weapon="TestZap", damage="100", reload_delay="3"):
    return {"slot": "Armament", "weapon": weapon, "pricing": True,
            "reloaddelay": reload_delay, "burst": "1", "range": "5000",
            "damage_warheads": [{"damage": damage, "tag": "Tesla_Heavy"}]}


class RoleRules:
    def resolve_weapon(self, weapon):
        targets = "Air" if weapon.endswith("_AA") else "Ground, Water"
        return miniyaml.Node(weapon, "", [miniyaml.Node("ValidTargets", targets)])


def actor_record(actor):
    for path in sorted((ROOT / "docs" / "balance").glob("*.json")):
        if "class_anchors" in path.name:
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for units in (doc.get("sections") or {}).values():
            if isinstance(units, dict) and actor in units:
                return units[actor]
    raise AssertionError("missing ledger actor: " + actor)


def attack_tesla_actors():
    found = set()
    for path in sorted((ROOT / "docs" / "balance").glob("*.json")):
        if "class_anchors" in path.name:
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for units in (doc.get("sections") or {}).values():
            for actor, rec in (units.items() if isinstance(units, dict) else []):
                if (rec.get("charge_up") or {}).get("v") == "AttackTesla":
                    found.add(actor)
    return found


class ChargeAwareArmamentProfileTests(unittest.TestCase):
    def test_attack_tesla_uses_the_actor_cycle(self):
        charge = {"v": "AttackTesla", "ticks": 25.0,
                  "cycle_reload": 100.0, "burst": 3}
        row, debt, _ = rd.armament_profile([armament()], float, charge)
        self.assertFalse(debt)
        self.assertEqual(3, row["w_burst"])
        self.assertEqual(100.0, row["w_reload"])
        self.assertEqual(300.0, row["w_damage"])
        # ⭐ 131, NOT 106 - THE CHARGE IS IN THE CYCLE NOW (#392, maintainer 2026-09-14:
        # "take into account the ammo reload delay to calculate how long a full cycle takes").
        # 100 reload + 2 x 3 burst delay = 106 was the cadence BEFORE the wind-up was counted;
        # the charge costs 25 more ticks every cycle, so the honest period is 131 and the rate
        # drops accordingly. This assertion was left pinned to the old law when the law shipped.
        self.assertAlmostEqual(300 / 131, row["w_dps"])

    def test_charge_level_traits_do_not_invent_a_sustained_cycle(self):
        charge = {"v": "AttackCharges", "ticks": 25.0}
        row, _debt, _ = rd.armament_profile([armament()], float, charge)
        self.assertEqual(1, row["w_burst"])
        self.assertEqual(3.0, row["w_reload"])
        self.assertEqual(100.0, row["w_damage"])
        self.assertAlmostEqual(100 / 3, row["w_dps"])

    def test_multi_armament_actor_keeps_the_existing_fail_closed_model(self):
        charge = {"v": "AttackTesla", "ticks": 25.0,
                  "cycle_reload": 100.0, "burst": 3}
        row, _debt, _ = rd.armament_profile(
            [armament("A"), armament("B", damage="50", reload_delay="10")], float, charge)
        self.assertFalse(row["weapon_model_eligible"])
        self.assertEqual(1, row["w_burst"])
        self.assertEqual(3.0, row["w_reload"])

    def test_hidden_aa_arm_does_not_make_charge_ownership_look_unique(self):
        charge = {"v": "AttackTesla", "ticks": 25.0,
                  "cycle_reload": 100.0, "burst": 3}
        ground = armament("GroundGun")
        aa = dict(armament("AirGun_AA"), slot="Armament@AA")
        row, _debt, _ = rd.armament_profile([ground, aa], float, charge)
        self.assertTrue(row["weapon_model_eligible"])
        self.assertEqual(1, row["w_burst"])
        self.assertEqual(3.0, row["w_reload"])
        views = ar.cameo_views({"armaments": [ground, aa], "charge_up": charge}, RoleRules())
        self.assertEqual({3.0}, {view["cycle"] for view in views})

    def test_fallback_armament_does_not_receive_a_default_inactive_charge_cycle(self):
        charge = {"v": "AttackTesla", "ticks": 25.0,
                  "cycle_reload": 100.0, "burst": 3}
        deployed = dict(armament(), requires="deployed")
        row, _debt, _ = rd.armament_profile([deployed], float, charge)
        self.assertEqual(1, row["w_burst"])
        self.assertEqual(3.0, row["w_reload"])
        view = ar.cameo_views({"armaments": [deployed], "charge_up": charge}, RoleRules())[0]
        self.assertEqual(3.0, view["cycle"])


class LiveLedgerChargeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = miniyaml.Ruleset(ROOT)
        cls.rows = {row["id"]: row for row in rd.cameo_rows()}

    def test_all_attack_tesla_rows_use_the_same_actor_cycle_in_both_consumers(self):
        # ⭐ THE CYCLES CARRY THE CHARGE (#392). Was 106 / 75 / 160, which is what these three
        # cost with the wind-up ignored; the applied law adds it, so they are 131 / 95 / 210 and
        # all three defences were being read as firing faster than they do. The Rail Tower is
        # the charge-PER-SHOT case (weapon reload 40 > ChargeDelay 3, so every one of its five
        # shots pays the wind-up); the coils charge once per volley.
        expected = {
            "ra1_soviets_teslacoil": (3, 100.0, 131.0, 144000.0),
            "ra2_soviets_teslacoil": (1, 75.0, 95.0, 96000.0),
            "asianalliance_railtower": (5, 120.0, 210.0, 155000.0),
        }
        self.assertEqual(set(expected), attack_tesla_actors())
        for actor, (burst, reload_delay, cycle, damage) in expected.items():
            with self.subTest(actor=actor):
                rec = actor_record(actor)
                row = self.rows[actor]
                baseline = [view for view in ar.cameo_views(rec, self.rules)
                            if view["baseline"]]
                self.assertEqual(1, len(baseline))
                view = baseline[0]
                self.assertEqual(burst, row["w_burst"])
                self.assertEqual(reload_delay, row["w_reload"])
                self.assertEqual(damage, row["w_damage"])
                self.assertAlmostEqual(damage / cycle, row["w_dps"])
                self.assertEqual(burst, view["burst"])
                self.assertEqual(cycle, view["cycle"])
                self.assertEqual(view["damage_per_cycle"], row["w_damage"])
                self.assertAlmostEqual(view["rate"], row["w_dps"])


if __name__ == "__main__":
    unittest.main()
