"""Passenger-sum closure after the accepted classic-four infantry prices."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from cameo_model import Model  # noqa: E402
import cargo_pricing  # noqa: E402


VALID_CARRIERS = {
    "ra1_allies_alliedapc": 1680,
    "ra1_allies_alliedchinooktransport": 4300,
    "ra1_allies_phasetransport": 2150,
    "ra1_soviets_btr80": 1800,
    "ra1_soviets_flaktruck": 980,
    "ra1_soviets_hiptransport": 2760,
    "td_gdi_apc": 1800,
    "td_gdi_assaultapc": 4120,
    "td_gdi_chinooktransport": 4120,
    "td_gdi_humveemkii": 900,
    "td_nod_buggymkii": 850,
    "td_nod_chinooktransport": 3853,
}


class AcceptedClassicFourCargoPriceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Model(ROOT).rs

    def test_valid_authored_loads_equal_purchase_price(self):
        for actor_name, expected in VALID_CARRIERS.items():
            with self.subTest(actor=actor_name):
                load = cargo_pricing.authored_load(self.rules, actor_name)
                self.assertEqual([], load["issues"])
                self.assertEqual(expected, load["passenger_sum"])
                self.assertEqual(
                    str(expected), self.rules.resolve(actor_name).child("Valued").get("Cost")
                )

if __name__ == "__main__":
    unittest.main()
