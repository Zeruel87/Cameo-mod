import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
FREEDOM_REPORT = ROOT / "docs/audit/latest/freedom_rocket_base_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warhead_nodes, main_warheads
from consolidate_identical_main_profiles import (
    LOCKDOWN_PINS,
    SELECTED,
    remaining_groups,
)
import consolidate_freedom_rocket_base as freedom
from miniyaml import Ruleset
from reviewed_weapon_history import HistoricalView


class IdenticalMainProfileConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_selected_identical_groups_are_fully_consolidated(self):
        self.assertEqual([], remaining_groups(self.rules))

    def test_freedom_rocket_base_is_folded_but_elite_remains_split(self):
        freedom_expected = {
            "RA2FreedomRocket": {
                "MissileAP_Medium": ("180000", "3333"),
            },
            "RA2FreedomRocket_elite": {
                "MissileAP_MediumFlatCompatibility": ("240000", "0"),
                "MissileAP_Medium": ("120000", "10000"),
            },
        }
        for name, expected in freedom_expected.items():
            nodes = {
                node.key.removeprefix("Warhead@"): node
                for node in main_warhead_nodes(self.rules.resolve_weapon(name))
            }
            self.assertEqual(set(expected), set(nodes))
            for key, (damage, scale) in expected.items():
                self.assertEqual(damage, nodes[key].get("Damage"))
                self.assertEqual(scale, nodes[key].get("PercentageScale"))

        self.assertEqual(
            freedom.ELITE_MAIN_ORDER,
            main_warheads(self.rules.resolve_weapon("RA2FreedomRocket_elite")),
        )

        # b905d7679 regenerated canonical coupling armor; frozen compatibility
        # keeps its old table. The historical equality guard must reject replay.
        elite = self.rules.resolve_weapon("RA2FreedomRocket_elite")
        self.assertEqual("44", elite.child("Warhead@MissileAP_MediumFlatCompatibility").child("Versus").get("COMPOSITE"))
        self.assertEqual("45", elite.child("Warhead@MissileAP_Medium").child("Versus").get("COMPOSITE"))
        with self.assertRaisesRegex(RuntimeError, "selected profiles are no longer identical"):
            freedom.inspect(self.rules)
        self.assertTrue(freedom.inspect(HistoricalView(self, self.rules)))

    def test_freedom_rocket_whole_tree_comparison_is_structural_only(self):
        report = json.loads(FREEDOM_REPORT.read_text(encoding="utf-8"))
        self.assertEqual([], report["added"])
        self.assertEqual([], report["removed"])
        self.assertEqual({"RA2FreedomRocket"}, set(report["changed"]))
        self.assertEqual(
            ["blast_shape", "64|100, 0|-|- ; 64|100, 0|-|-", "64|100, 0|-|-"],
            report["changed"]["RA2FreedomRocket"][0],
        )

    def test_stateful_fireball_case_remains_separate(self):
        resolved = self.rules.resolve_weapon("SyndicateFireballLauncherExplode")
        fireball_nodes = {
            node.key.removeprefix("Warhead@"): node
            for node in main_warhead_nodes(resolved)
        }
        preserved = {
            "PreservedFlat_HeavyFlameWeapon",
            "PreservedFlat_LightFlameWeapon",
            "PreservedFlat_MediumFlameWeapon",
        }
        self.assertTrue(preserved <= set(fireball_nodes))
        for key in preserved:
            node = fireball_nodes[key]
            self.assertEqual("4000", node.get("Damage"))
            self.assertEqual("Temperature", node.get("PhysicalStateName"))
            self.assertEqual("100", node.get("PhysicalStateScale"))
        temperature_nodes = [
            node for node in resolved.children
            if node.key.startswith("Warhead@")
            and node.get("PhysicalStateName") == "Temperature"
            and node.get("PhysicalStateScale") == "100"
        ]
        self.assertEqual(9, len(temperature_nodes))

    def test_lockdown_descendants_keep_their_original_routes(self):
        for name, (flak_damage, chaingun_damage) in LOCKDOWN_PINS.items():
            resolved = self.rules.resolve_weapon(name)
            flak = resolved.child("Warhead@SniperFlak")
            chaingun = resolved.child("Warhead@SniperChaingun")
            self.assertEqual("AreaDamage", flak.value)
            self.assertEqual(str(flak_damage), flak.get("Damage"))
            self.assertEqual("Ground, Water, Air", flak.get("ValidTargets"))
            self.assertEqual("Enemy, Neutral", flak.get("ValidRelationships"))
            self.assertEqual(str(chaingun_damage), chaingun.get("Damage"))

    def test_selected_sniper_profiles_remain_point_like(self):
        for name in SELECTED:
            if "Sniper" not in name:
                continue
            for node in self.rules.resolve_weapon(name).children:
                if not node.key.startswith("Warhead@"):
                    continue
                if node.value not in {"AreaDamage", "SpreadDamage"}:
                    continue
                if "Sniper" not in node.key and "Bullet" not in node.key:
                    continue
                self.assertEqual("1", node.get("Spread"), (name, node.key))
                self.assertEqual("100, 0", node.get("Falloff"), (name, node.key))


if __name__ == "__main__":
    unittest.main()
