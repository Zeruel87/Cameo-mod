"""Regression coverage for the Nod Chinook's authored initial cargo capacity."""

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]
from miniyaml import Ruleset  # noqa: E402
from cargo_pricing import authored_load  # noqa: E402


EXPECTED_PASSENGERS = [
    "td_nod_minigunner",
    "td_nod_rocketsoldier",
    "td_nod_flamethrower",
    "td_nod_chemicalwarrior",
    "td_nod_chemicalrocketsoldier",
    "td_nod_lasertrooper",
    "td_nod_stealthsoldier",
    "td_nod_blackhandflamer",
]


class NodChinookCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = authored_load(Ruleset(ROOT), "td_nod_chinooktransport")

    def test_capacity_equals_the_actual_authored_weight(self):
        self.assertEqual(11, self.result["capacity"])
        self.assertEqual(11, self.result["filled_weight"])
        self.assertEqual([], self.result["issues"])

    def test_the_eight_unit_initial_load_is_preserved(self):
        self.assertEqual(
            EXPECTED_PASSENGERS,
            [passenger["actor"] for passenger in self.result["passengers"]],
        )
        self.assertEqual(8, len(self.result["passengers"]))

    def test_unarmed_transport_price_rule_is_the_passenger_sum(self):
        self.assertFalse(self.result["armed"])
        self.assertIsNone(self.result["combat_special_k"])
        self.assertEqual(
            sum(passenger["cost"] for passenger in self.result["passengers"]),
            self.result["passenger_sum"],
        )


if __name__ == "__main__":
    unittest.main()
