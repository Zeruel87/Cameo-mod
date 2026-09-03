"""The remaining reachable backlog is an explicit set of gameplay holds."""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))

from audit_three_way_split import main_warhead_nodes, main_warheads
from miniyaml import Ruleset
from survey_weapon_structure import inventory


EXPECTED_HOLDS = {
    "AlliedTankDestroyerCannon": ("CannonHE_Medium", "CannonAP_Light"),
    "Aphid_AA": ("Concussion_Medium", "MissileHE_Heavy"),
    "JimRaynorMachineGun": ("MissileHE_Heavy", "CannonHE_Heavy"),
    "SheridanCannon": ("CannonAP_Light", "CannonHE_Medium"),
    "SheridanMissiles": ("MissileHE_Medium", "MissileHE_Light"),
    "TSBoatcannon": ("Concussion_Medium", "Demolition_Heavy"),
    "TSSonicZapWeapon": ("Tesla_Heavy", "Magic_Heavy"),
    "TigerCannon": ("CannonHE_Heavy", "CannonHE_Medium"),
    "Type97Cannon": ("CannonHE_Heavy", "CannonHE_Medium"),
    "Type97PlasmaCannon": ("Tesla_Heavy", "Railgun_Heavy", "CannonHE_Heavy"),
    "d2k_air_drone_guns": ("MissileAP_Heavy", "Bullet_Light", "Bullet_Medium"),
    "d2k_air_drone_guns_upgrade": (
        "CannonHE_Heavy", "MissileAP_Heavy", "Bullet_Light", "Bullet_Medium"),
    "TSTacticalChemMissileDamage": ("MediumMissile", "LightMissile"),
    "TSTacticalMissileDamage": ("MediumMissile", "LightMissile"),
}

EXPECTED_MAIN_PROFILE_SHA256 = (
    "6b5065686fbe061d09a8981dfba5dd81c6792a9c98f90ea1dd14c476281e446d"
)


def node_payload(node):
    return [node.key, node.value, [node_payload(child) for child in node.children]]


class DeferredWeaponRedesignBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.inventory = inventory(cls.rules)

    def test_unreviewed_reachable_queue_is_exactly_the_documented_holds(self):
        sets = self.inventory["sets"]
        actual = (set(sets["unreviewed_direct_actor_armament"])
                  | set(sets["unreviewed_indirect_weapon_graph"]))
        self.assertEqual(set(EXPECTED_HOLDS), actual)
        self.assertEqual(14, len(actual))

    def test_hold_profiles_remain_unmodified(self):
        for name, expected in EXPECTED_HOLDS.items():
            self.assertEqual(
                expected, tuple(main_warheads(self.rules.resolve_weapon(name))), name)

        payload = {
            name: [node_payload(node) for node in main_warhead_nodes(
                self.rules.resolve_weapon(name))]
            for name in sorted(EXPECTED_HOLDS)
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(EXPECTED_MAIN_PROFILE_SHA256, hashlib.sha256(raw).hexdigest())

    def test_unreached_definitions_remain_outside_the_live_queue(self):
        self.assertEqual(
            100, self.inventory["counts"]["unreviewed_stacked_main_unreached"])
        self.assertTrue(
            set(EXPECTED_HOLDS).isdisjoint(self.inventory["sets"]["unreached"]))


if __name__ == "__main__":
    unittest.main()
