"""Reference armament selection uses one canonical built-state condition context."""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import reference_distribution as reference  # noqa: E402


def record(ledger, actor):
    doc = json.loads((ROOT / "docs" / "balance" / f"{ledger}.json").read_text(encoding="utf-8"))
    return next(section[actor] for section in doc["sections"].values() if actor in section)


class BuiltStateSelectionTests(unittest.TestCase):
    def test_tesla_coil_keeps_one_uncharged_mode(self):
        arms = reference.baseline_armaments(record("redalert2_soviets", "ra2_soviets_teslacoil")["armaments"])
        self.assertEqual([a["weapon"] for a in arms], ["RA2CoilBolt"])

    def test_ifv_keeps_one_ground_primary_and_excludes_passenger_modes(self):
        arms = reference.baseline_armaments(record("redalert2_allies", "ra2_allies_ifv")["armaments"])
        self.assertEqual([a["weapon"] for a in arms], ["RA2HoverMissile"])

    def test_battle_tank_keeps_both_unupgraded_parallel_weapons(self):
        arms = reference.baseline_armaments(record("tiberiandawn_gdi", "td_gdi_battletank")["armaments"])
        self.assertEqual(
            {a["weapon"] for a in arms},
            {"td_gdi_battletank_120mm", "td_gdi_battletank_m1a1missiles"},
        )


if __name__ == "__main__":
    unittest.main()
