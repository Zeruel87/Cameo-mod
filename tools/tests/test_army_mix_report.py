"""army_mix_report: the army-mix flags that make Humvee-and-infantry spam visible (§12.11)."""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ai"))
sys.path.insert(0, str(ROOT / "tools/audit"))

import army_mix_report as mixr  # noqa: E402
from miniyaml import Ruleset  # noqa: E402

KINDS = {
    "rifle": ("infantry", False, False),
    "humvee": ("vehicle", False, False),
    "tank": ("vehicle", True, False),
    "artillery": ("vehicle", False, True),
    "harvester": ("economy", False, False),
    "barracks": None,
}


def record(bot, built):
    return {"player": {"bot_type": bot}, "arsenal": [{"type": t, "created": n} for t, n in built.items()]}


class MixFlags(unittest.TestCase):
    def check(self, built):
        entry = mixr.summarise([record("hard", built)], KINDS.get)["hard"]
        m = mixr.mix(entry, KINDS.get)
        return m, mixr.flags(m, max_share=0.25, min_heavy=0.05, min_artillery=0.05)

    def test_the_spectated_spam_raises_all_three_flags(self):
        m, found = self.check({"rifle": 185, "humvee": 72, "tank": 3, "artillery": 1, "harvester": 18})
        self.assertEqual(len(found), 3, found)
        self.assertEqual(m["total"], 261)  # the harvesters are economy, not army

    def test_a_balanced_mix_raises_none(self):
        m, found = self.check({"rifle": 10, "humvee": 10, "tank": 10, "artillery": 10})
        self.assertEqual(found, [])

    def test_harvesters_never_count_as_heavy_vehicles(self):
        m, found = self.check({"rifle": 10, "humvee": 10, "harvester": 40})
        self.assertEqual(m["heavy_share_of_vehicles"], 0.0)
        self.assertTrue(any("heavy" in f for f in found))

    def test_buildings_and_unknown_types_are_left_out(self):
        m, _ = self.check({"rifle": 5, "barracks": 3, "nonexistent": 7})
        self.assertEqual(m["total"], 5)


class RealRulesClassification(unittest.TestCase):
    """The classes come from resolved rules; pin the td_gdi units the spectated match turned on."""

    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def kind(self, name):
        return mixr.classify(self.rules.resolve(name))

    def test_td_gdi_units(self):
        self.assertEqual(self.kind("td_gdi_minigunner")[0], "infantry")
        self.assertEqual(self.kind("td_gdi_humveemkii"), ("vehicle", False, False))
        self.assertEqual(self.kind("td_gdi_predatortank"), ("vehicle", True, False))
        self.assertEqual(self.kind("td_gdi_archerartillery")[2], True)
        self.assertEqual(self.kind("td_gdi_orca")[0], "aircraft")
        self.assertEqual(self.kind("td_gdi_tiberiumharvester")[0], "economy")
        self.assertEqual(self.kind("td_gdi_mobileconstructionvehicle")[0], "economy")
        self.assertIsNone(self.kind("td_gdi_guardtower"))


if __name__ == "__main__":
    unittest.main()
