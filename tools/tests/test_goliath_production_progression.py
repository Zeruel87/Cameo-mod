import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
from miniyaml import Ruleset


class GoliathProductionProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def prerequisites(self, actor_name):
        actor = self.rules.resolve(actor_name)
        self.assertIsNotNone(actor, actor_name)
        buildable = actor.child("Buildable")
        self.assertIsNotNone(buildable, actor_name)
        value = buildable.get("Prerequisites")
        self.assertIsNotNone(value, actor_name)
        return tuple(token.strip() for token in value.split(","))

    def test_mk1_is_replaced_in_production_after_mk2_promotion(self):
        self.assertEqual(
            ("~terran_armory", "~!terran_promotion_goliathmk2"),
            self.prerequisites("terran_goliath"),
        )

    def test_mk2_requires_its_promotion(self):
        self.assertEqual(
            ("~terran_armory", "~terran_promotion_goliathmk2"),
            self.prerequisites("terran_goliathmk2"),
        )


if __name__ == "__main__":
    unittest.main()
