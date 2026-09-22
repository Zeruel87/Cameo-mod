"""Focused checks for armament-level support pricing and its safety guard."""

import json
import pathlib
import sys
import unittest
from unittest.mock import Mock, patch


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import extract_stats  # noqa: E402
import fit_class  # noqa: E402
from miniyaml import Node  # noqa: E402


def find_actor(actor):
    for path in (ROOT / "docs" / "balance").glob("*.json"):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for section in (document.get("sections") or {}).values():
            if actor in section:
                return section[actor]
    raise AssertionError(f"missing ledger actor: {actor}")


class SupportArmamentPricingTests(unittest.TestCase):
    def test_extractor_tags_point_defense_by_armament_key(self):
        actor = Node("unit", "", [
            Node("Buildable", "", [Node("Queue", "Vehicle")]),
            Node("Armament@pointdefense", "", [Node("Weapon", "pd")]),
            Node("Armament", "", [Node("Weapon", "cannon")]),
        ])
        rules = Mock()
        rules.resolve.return_value = actor
        rules.actor.return_value = None

        def weapon(_rules, name):
            return {
                "weapon": name,
                "damage_warheads": [{"type": "AreaDamage", "damage":
                                      "1" if name == "pd" else "8000"}],
                "defined_in": "mods/cameo/weapons/test.yaml",
            }

        with patch.object(extract_stats, "weapon_entry", side_effect=weapon), \
             patch.object(extract_stats, "actor_subtype", return_value="LightTank"):
            unit = extract_stats.extract_actor(rules, "unit", "vehicles")
        support, cannon = unit["armaments"]
        self.assertTrue(support["support_armament"])
        self.assertFalse(support["pricing"])
        self.assertEqual(support["pricing_reason"], "support_armament")
        self.assertTrue(cannon["pricing"])

    def test_light_tank_point_defense_is_excluded_but_cannon_remains_priced(self):
        unit = find_actor("td_nod_lighttankmkii")
        support = [arm for arm in unit["armaments"] if arm.get("support_armament")]
        priced = [arm for arm in unit["armaments"] if arm.get("pricing")]
        self.assertEqual([(arm["slot"], arm["weapon"]) for arm in support],
                         [("Armament@pointdefense", "PDLaserLTNK2")])
        self.assertTrue(all(arm["pricing"] is False for arm in support))
        self.assertTrue(any(arm["slot"] == "Armament" for arm in priced))
        self.assertEqual(extract_stats.pricing_guard(unit["armaments"], True)["status"], "OK")

    def test_deployed_point_defense_uses_the_same_armament_tag(self):
        unit = find_actor("td_gdi_defenserig")
        deployed = [arm for arm in unit["armaments"]
                    if arm["slot"] == "Armament@pointdefensedeployed"]
        self.assertEqual(len(deployed), 1)
        self.assertTrue(deployed[0]["support_armament"])
        self.assertFalse(deployed[0]["pricing"])

    def test_pure_positive_all_unpriced_state_is_guarded(self):
        unit = find_actor("td_nod_reconbike")
        self.assertEqual(extract_stats.pricing_guard(unit["armaments"], True)["status"], "OK")
        self.assertGreater(
            extract_stats.pricing_guard(unit["armaments"], True)[
                "priced_positive_armament_count"
            ],
            0,
        )

        bad = [{"pricing": False, "damage_warheads": [{"damage": "100"}]}]
        self.assertEqual(
            extract_stats.pricing_guard(bad, True)["status"],
            "ALL_POSITIVE_ARMAMENTS_UNPRICED",
        )
        support_only = [{
            "pricing": False,
            "support_armament": True,
            "damage_warheads": [{"damage": "100"}],
        }]
        self.assertEqual(extract_stats.pricing_guard(support_only, True)["status"], "OK")
        with self.assertRaises(fit_class.PricingScopeError):
            fit_class.pricing_armaments({
                "pricing_guard": extract_stats.pricing_guard(bad, True),
                "armaments": bad,
            })

    def test_all_committed_ledger_buildable_positive_actors_have_a_priced_armament(self):
        failures = []
        for path in (ROOT / "docs" / "balance").glob("*.json"):
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for section in (document.get("sections") or {}).values():
                for actor, unit in section.items():
                    guard = extract_stats.pricing_guard(
                        unit.get("armaments", []), bool(unit.get("buildable"))
                    )
                    if guard["status"] != "OK":
                        failures.append(actor)
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
