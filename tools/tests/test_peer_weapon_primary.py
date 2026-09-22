"""Peer extraction must choose a positive-damage weapon over a utility slot."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Node  # noqa: E402
import extract_peer_units as peer  # noqa: E402


def weapon(name, warhead_type, damage=None, range_="5c0", reload_="30"):
    children = [Node("Range", range_), Node("ReloadDelay", reload_)]
    warhead = []
    if damage is not None:
        warhead.append(Node("Damage", str(damage)))
    children.append(Node("Warhead@hit", warhead_type, warhead))
    return Node(name, "", children)


class Rules:
    def __init__(self, weapons):
        self.weapons = weapons

    def resolve_weapon(self, name):
        return self.weapons.get(name)


def actor(*weapon_names):
    return Node("actor", "", [
        Node(f"Armament@{index}", "", [Node("Weapon", name)])
        for index, name in enumerate(weapon_names)
    ])


class PeerWeaponPrimaryTests(unittest.TestCase):
    def test_capture_utility_does_not_hide_first_damaging_weapon(self):
        rules = Rules({
            "commandeer": weapon("commandeer", "ChangeOwner", range_="1c0", reload_="5"),
            "M16Carbine": weapon("M16Carbine", "SpreadDamage", damage=1000),
        })
        result = peer.weapon_stats(rules, actor("commandeer", "M16Carbine"), "Combined Arms")
        self.assertEqual(result["weapon"], "M16Carbine")
        self.assertEqual(result["w_range"], 5120)
        self.assertEqual(result["w_damage"], 1000)
        self.assertEqual(result["w_reload"], 30)

    def test_genuinely_unarmed_actor_keeps_legacy_first_slot_fallback(self):
        rules = Rules({"commandeer": weapon("commandeer", "ChangeOwner")})
        result = peer.weapon_stats(rules, actor("commandeer"), "Combined Arms")
        self.assertEqual(result["weapon"], "commandeer")
        self.assertIsNone(result["w_damage"])


if __name__ == "__main__":
    unittest.main()
