"""Contract for the classic-four transport chassis-only batch."""

from __future__ import annotations

import pathlib
import json
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from cameo_model import Model  # noqa: E402
import cargo_pricing  # noqa: E402


TARGETS = {
    "td_gdi_chinooktransport": (4120, 82000, 124, 25, 33, 4100),
    "td_nod_chinooktransport": (3853, 82000, 124, 25, 33, 4100),
    "ra1_allies_alliedchinooktransport": (4300, 88000, 120, 24, 35, 4400),
    "ra1_soviets_hiptransport": (2760, 104000, 118, 24, 42, 5200),
}

# The four chassis rows inherit a separate cargo-price law.  Keep the authored
# list and capacity in this contract so a chassis edit cannot silently change
# the load, and assert the exact resolved weight totals as well as the price.
CARGO = {
    "td_gdi_chinooktransport": {
        "capacity": 8,
        "weight": 8,
        "cost": 4120,
        "units": "td_gdi_minigunner, td_gdi_grenadier, td_gdi_rocketsoldier, td_gdi_sonicmissilesoldier, td_gdi_empgrenadier, td_gdi_shotgunner, td_gdi_officer, td_gdi_heavysniper",
    },
    "td_nod_chinooktransport": {
        "capacity": 11,
        "weight": 11,
        "cost": 3853,
        "units": "td_nod_minigunner, td_nod_rocketsoldier, td_nod_flamethrower, td_nod_chemicalwarrior, td_nod_chemicalrocketsoldier, td_nod_lasertrooper, td_nod_stealthsoldier, td_nod_blackhandflamer",
    },
    "ra1_allies_alliedchinooktransport": {
        "capacity": 10,
        "weight": 10,
        "cost": 4300,
        "units": "ra1_allies_rifleinfantry, ra1_allies_alliedrocketsoldier, ra1_allies_alliedsniper, ra1_allies_medic, ra1_allies_machinegunner, ra1_allies_rifleinfantry, ra1_allies_alliedrocketsoldier, ra1_allies_alliedsniper, ra1_allies_medic, ra1_allies_machinegunner",
    },
    "ra1_soviets_hiptransport": {
        "capacity": 8,
        "weight": 8,
        "cost": 2760,
        "units": "ra1_soviets_dog, ra1_soviets_rifleinfantry, ra1_soviets_grenadier, ra1_soviets_rocketsoldier, ra1_soviets_flamethrower, ra1_soviets_shocktrooper, ra1_soviets_firerocketsoldier, ra1_soviets_mortarsoldier",
    },
}


class AcceptedClassicFourTransportChassisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Model(ROOT).rs

    def test_chassis_moves_and_cost_stays_on_passenger_sum(self):
        for name, values in TARGETS.items():
            cost, hp, speed, turn, step, repair = values
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertEqual(str(cost), actor.child("Valued").get("Cost"))
                self.assertEqual(str(hp), actor.child("Health").get("HP"))
                self.assertEqual(str(speed), actor.child("Aircraft").get("Speed"))
                self.assertEqual(str(turn), actor.child("Aircraft").get("TurnSpeed"))
                self.assertEqual(
                    str(step), actor.child("ChangesHealth@SelfHealing").get("Step")
                )
                self.assertEqual(str(repair), actor.child("Repairable").get("HpPerStep"))

    def test_aircraft_turn_speed_is_in_the_raw_ledger(self):
        for name, (_, _, _, turn, _, _) in TARGETS.items():
            with self.subTest(actor=name):
                hits = []
                for path in (ROOT / "docs" / "balance").glob("*.json"):
                    doc = json.loads(path.read_text(encoding="utf-8-sig"))
                    for section in (doc.get("sections") or {}).values():
                        if name in section:
                            hits.append(section[name])
                self.assertEqual(1, len(hits))
                slot = hits[0].get("turn_speed_air")
                self.assertEqual(str(turn), slot["v"])
                self.assertTrue(slot["src"].endswith("#Aircraft.TurnSpeed"))

    def test_authored_loads_are_valid_full_and_price_exactly(self):
        for name, expected in CARGO.items():
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                cargo = actor.child("Cargo")
                self.assertEqual(str(expected["capacity"]), cargo.get("MaxWeight"))
                self.assertEqual(expected["units"], cargo.get("InitialUnits"))
                load = cargo_pricing.authored_load(self.rules, name)
                self.assertEqual([], load["issues"])
                self.assertEqual(expected["capacity"], load["filled_weight"])
                self.assertEqual(expected["weight"], load["filled_weight"])
                self.assertEqual(expected["cost"], load["passenger_sum"])
                self.assertEqual(
                    str(expected["cost"]), actor.child("Valued").get("Cost")
                )


if __name__ == "__main__":
    unittest.main()
