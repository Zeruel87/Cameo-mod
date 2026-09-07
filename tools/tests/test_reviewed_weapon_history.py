"""Historical reconciliation must not hide unreviewed live changes."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools/audit"))
from miniyaml import Node
from reviewed_weapon_history import historical_copy


class ReviewedHistoryTests(unittest.TestCase):
    def fixture(self, value="102"):
        return Node("GrenadeRA", "", [Node("ReloadDelay", "40"),
            Node("Warhead@Demolition_Light", "AreaDamage", [
                Node("Damage", "12345"), Node("Versus", "", [Node("COMPOSITE", value)])])])

    def test_reverses_only_the_reviewed_field_without_mutating_live_node(self):
        live = self.fixture()
        old = historical_copy(self, live)
        self.assertEqual("102", live.get("Warhead@Demolition_Light", "Versus", "COMPOSITE"))
        self.assertEqual("101", old.get("Warhead@Demolition_Light", "Versus", "COMPOSITE"))
        self.assertEqual("12345", old.get("Warhead@Demolition_Light", "Damage"))
        self.assertEqual("40", old.get("ReloadDelay"))

    def test_unreviewed_value_is_rejected_not_normalized(self):
        with self.assertRaises(AssertionError):
            historical_copy(self, self.fixture("103"))

    def test_missing_reviewed_field_is_rejected(self):
        live = self.fixture()
        live.child("Warhead@Demolition_Light").child("Versus").children.clear()
        with self.assertRaises(AssertionError):
            historical_copy(self, live)

    def test_unlisted_weapon_is_not_rewritten(self):
        live = self.fixture()
        live.key = "UnreviewedWeapon"
        self.assertEqual("102", historical_copy(self, live).get("Warhead@Demolition_Light", "Versus", "COMPOSITE"))

    def test_corrosion_reconstruction_rejects_an_extra_live_field(self):
        warhead = Node("Warhead@HeavyChemicalWeaponPercentage", "AreaDamagePercentage",
                       [Node("Field" + str(n), str(n)) for n in range(7)] +
                       [Node("PhysicalStates", "", [Node("Corrosion", "100")])])
        live = Node("PhobosLaser", "", [warhead])
        old = historical_copy(self, live).children[0]
        self.assertEqual(["PhysicalStateName", "PhysicalStateScale"], [n.key for n in old.children[8:]])
        self.assertEqual(8, len(warhead.children))
        warhead.children.append(Node("NewField", "1"))
        with self.assertRaises(AssertionError):
            historical_copy(self, live)


if __name__ == "__main__":
    unittest.main()
