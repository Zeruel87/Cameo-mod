"""Active-rule coverage and source guard checks; not an in-game simulation."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
from miniyaml import Ruleset


class HeadquartersRefineryCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.ai = cls.rules.resolve("Player").child("BaseBuilderBotModuleCA@generic")
        cls.protected = set(cls.ai.get("ConstructionYardTypes").split(", "))

    def test_all_starcraft_and_warcraft_headquarters_are_protected(self):
        for name in ("protoss_nexus", "terran_commandcenter", "zerg_hatchery",
                     "wc2_humans_townhall",
                     "wc2_orcs_greathall"):
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertIsNotNone(actor)
                self.assertTrue(actor.children_named("Refinery"))
                self.assertIn(name, self.protected)

    def test_normal_refineries_remain_unprotected(self):
        for name in ("protoss_assimilator", "terran_refinery", "zerg_extractor",
                     "ixian_refineryixian", "ra1_soviets_sovietorerefinery",
                     "wc2_humans_elvenlumbermill", "wc2_orcs_trolllumbermill"):
            with self.subTest(actor=name):
                actor = self.rules.resolve(name)
                self.assertIsNotNone(actor)
                self.assertTrue(actor.children_named("Refinery"))
                self.assertNotIn(name, self.protected)

    def test_cleanup_guard_precedes_both_sell_paths_without_changing_count(self):
        source = (ROOT / "OpenRA.Mods.CA/Traits/BotModules/BaseBuilderBotModuleCA.cs").read_text()
        cleanup = source.split("void SellUselessRefinery(IBot bot)", 1)[1].split(
            "List<MiniYamlNode>", 1)[0]
        self.assertIn("world.ActorsHavingTrait<Refinery>().Where(a => a.Owner == player).ToArray()", cleanup)
        guard = "if (Info.ConstructionYardTypes.Contains(refineries[i].Info.Name))"
        self.assertIn(guard, cleanup)
        # The diagnostic string contains braces, so inspect through the next loop.
        guard_body = cleanup.split(guard, 1)[1].split("for (var j =", 1)[0]
        self.assertIn("continue;", guard_body)
        self.assertLess(cleanup.index("if (refineries.Length <="), cleanup.index(guard))
        self.assertLess(cleanup.index("for (var i ="), cleanup.index(guard))
        self.assertLess(cleanup.index(guard), cleanup.index("for (var j ="))
        self.assertLess(cleanup.index(guard), cleanup.index("if (ResourceMapModule != null"))
        self.assertEqual(2, cleanup.count('new Order("Sell"'))


if __name__ == "__main__":
    unittest.main()
