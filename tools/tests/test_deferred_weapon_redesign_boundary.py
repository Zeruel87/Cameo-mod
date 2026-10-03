"""The remaining reachable backlog is an explicit set of gameplay holds.

⛔ SKIPPED: tools/audit/intentional_composites.py was DELETED 2026-09-06 by
maintainer ruling. The exemption registry no longer exists; these holds are
preserved for provenance but the test cannot run until rewritten against
the new audit framework.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))

from audit_three_way_split import main_warheads

try:
    from intentional_composites import resolved_referrer_index
except ImportError:
    resolved_referrer_index = None

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

EXPECTED_RESOLVED_WEAPON_DIGESTS = {
    "AlliedTankDestroyerCannon": "5edc06543f196b1483dc3cc6f98b2f2b57f491af8a4b8e740a2783ef5d3034a9",
    "Aphid_AA": "5948424b66abdff7d6b18e7b59b339ada133c335ca8d7e5a9a0edea03db87bbc",
    "JimRaynorMachineGun": "efc55beb826cd3ac8582f81292e19f7ff29711046c189e7bb5f5b995c2348658",
    "SheridanCannon": "9c60df9c1cf1143fb06cf8eb7cddc390a51f49bb05e11b0cf9eab84c2453bc00",
    "SheridanMissiles": "bba6b1407577d1914bacf10267a1fae35035e3f175c7dd729ac24de38460f4fe",
    "TSBoatcannon": "48d00b8daff86a09b9b78d228d69494077f0794af26ee8df23b3e0c4f751fd5c",
    "TSSonicZapWeapon": "f7ee64608192a3ece49153af99c72b1190732621f0cff50c3e58397ffd4c443e",
    "TigerCannon": "b6632ba5375786e750b09550bf0c5a6cb5b2066d4173703414f20a408174aeca",
    "Type97Cannon": "6f1f926b2dea65e053f61271c7a1a2bfc25dcaf969b73878a21cf004330ef706",
    "Type97PlasmaCannon": "0c1d022f05a0f0ab960b15588b05402169f3733b991a6de5a0f78f8cc2f049b3",
    "d2k_air_drone_guns": "f02d659b2d3a138ed090f35fa1b989620398440a4211613897bb121463a6e0cd",
    "d2k_air_drone_guns_upgrade": "7b8554fac22f1fa12e4697728fc8e8c03c3399861a0bec064c39d55d0e019072",
    "TSTacticalChemMissileDamage": "8006a1faebfc09d9c36a3f322a58c7e7a037ce2474cf2254bb767d42f1e1d34c",
    "TSTacticalMissileDamage": "c76fa788e03affba4bde5e1a5ded69d01555879b3dc85e57fc69c74bc855b7f8",
}

# These are resolved, active closures rather than direct textual references.
# Keep a hold visible until its complete player-facing delivery chain has an
# approved role decision.
EXPECTED_HOLD_CLOSURES = {
    ("AlliedTankDestroyerCannon",): (
        ("ra1_allies_alliedtankdestroyer",), ()),
    ("Aphid_AA",): (("ra1_allies_rapierjumpjet",), ()),
    ("JimRaynorMachineGun",): (
        ("terran_jimraynor", "terran_pythean"), ()),
    ("SheridanCannon",): (("ra1_allies_sheridanassaulttank",), ()),
    ("SheridanMissiles",): (("ra1_allies_sheridanassaulttank",), ()),
    ("TSBoatcannon",): (("forgotten_cannonboat",), ()),
    ("TSSonicZapWeapon",): (("ts_gdi_disruptor",), ()),
    ("TigerCannon",): (
        ("ra1_allies_alliedcybertank", "ra1_allies_alliedtigerheavytank"), ()),
    ("Type97Cannon",): (("japan_chihaheavytank",), ()),
    ("Type97PlasmaCannon",): (("japan_chihaheavytank",), ()),
    ("d2k_air_drone_guns", "d2k_air_drone_guns_upgrade"): (
        ("ixian_airdrone",), ()),
    ("TSTacticalChemMissileDamage", "TSTacticalMissileDamage"): (
        ("casinocrate", "ts_nod_missilesilo"),
        ("TSTacticalChemMissile", "TSTacticalMissile")),
}

# Full resolved Armament traits cover the paid/replacement channels that do not
# themselves point at a held weapon. They deliberately pin slot names, weapons,
# conditions, pauses, and every other Armament field through the node digest.
# Replacement weapon bodies and intermediate wrapper bodies are not pinned here.
EXPECTED_HOLD_ACTOR_ARMAMENT_DIGESTS = {
    "ra1_allies_alliedtankdestroyer": "5b72d6c9f6ff5729b5392462ef2ee00bdc11c712f0c18c2a94f0b9952969218f",
    "ra1_allies_rapierjumpjet": "43b11afb5268d4c1794ca0638523aeea61adf8c24d2aad285dd9d300bbbac09d",
    "terran_jimraynor": "37d13528cd3c52f26a0572d7528edbbd40fc88d2bdf8936b87ec94dc0412421e",
    "terran_pythean": "caa2c9c3b7a6a26b261db12ef432d789945581a910bf013a808793c73174d2e3",
    "ra1_allies_sheridanassaulttank": "e97958861cf763c66c39217cd79cd29244e18fa9845cd77f1d67eefa4afec041",
    "forgotten_cannonboat": "3e4bf659ab29ee65dae3ca9322a9838f9de2d43626e6864af6993a0a56bc184b",
    "ts_gdi_disruptor": "859fc5c00d7b02475617b2adf248fa1721a477ffe119f2520fa2eeb4b8fef9ba",
    "ra1_allies_alliedcybertank": "6adbd7ca9c1637b873276ad0a9cb402cbcdfa43abc5e1d929ae8ddc2573a097e",
    "ra1_allies_alliedtigerheavytank": "6adbd7ca9c1637b873276ad0a9cb402cbcdfa43abc5e1d929ae8ddc2573a097e",
    "japan_chihaheavytank": "00691a7be2132083e9442749eb43fb2b2869dabf03539fa83c5452794edea914",
    "ixian_airdrone": "31aec3009d13ca3148c687178348e0e5974c83952fc41cec5faa48cd1d9e21d3",
    "casinocrate": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "ts_nod_missilesilo": "7772d707a327fcc1e64c39c3d099fd8e35cfb4ba44a5e9067d167af044445f4a",
}

# Casino Crate reaches the chemical tactical delivery through a crate action,
# not an Armament. Keep that complete resolved action node under the same
# closure guard instead of treating its empty Armament list as evidence.
EXPECTED_HOLD_NON_ARMAMENT_NODE_DIGESTS = {
    ("casinocrate", "ExplodeCrateAction@chem"):
        "3bb0b0ab80cc7f90fab65df1bcde0eeb604c8ceedfb2b5386b5a6c98a5c2ab7a",
}


def node_payload(node):
    return [node.key, node.value, [node_payload(child) for child in node.children]]


def payload_digest(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


@unittest.skipIf(resolved_referrer_index is None,
                 "intentional_composites.py was deleted 2026-09-06; "
                 "exemption repealed by maintainer ruling")
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
        self.assertEqual(set(EXPECTED_HOLDS), set(EXPECTED_RESOLVED_WEAPON_DIGESTS))
        for name, expected in EXPECTED_HOLDS.items():
            self.assertEqual(
                expected, tuple(main_warheads(self.rules.resolve_weapon(name))), name)
        for name, expected in EXPECTED_RESOLVED_WEAPON_DIGESTS.items():
            self.assertEqual(
                expected, payload_digest(node_payload(self.rules.resolve_weapon(name))),
                name)

    def test_holds_keep_their_resolved_active_delivery_closures(self):
        index = resolved_referrer_index(self.rules)
        for names, expected in EXPECTED_HOLD_CLOSURES.items():
            actors = set()
            stages = set()
            pending = list(names)
            seen = {name.lower() for name in names}
            while pending:
                current = pending.pop()
                for referrer in index.get(current.lower(), []):
                    if referrer["kind"] == "actor":
                        actors.add(referrer["name"])
                        continue

                    stage = referrer["name"]
                    stages.add(stage)
                    if stage.lower() not in seen:
                        seen.add(stage.lower())
                        pending.append(stage)

            self.assertEqual(expected, (tuple(sorted(actors)), tuple(sorted(stages))))

        expected_actors = {
            actor for actors, _stages in EXPECTED_HOLD_CLOSURES.values()
            for actor in actors
        }
        self.assertEqual(expected_actors, set(EXPECTED_HOLD_ACTOR_ARMAMENT_DIGESTS))
        for name, expected in EXPECTED_HOLD_ACTOR_ARMAMENT_DIGESTS.items():
            armaments = [
                node_payload(node) for node in self.rules.resolve(name).children
                if node.key.startswith("Armament")
            ]
            self.assertEqual(expected, payload_digest(armaments), name)

        for (actor, key), expected in EXPECTED_HOLD_NON_ARMAMENT_NODE_DIGESTS.items():
            node = self.rules.resolve(actor).child(key)
            self.assertIsNotNone(node, f"{actor} > {key}")
            self.assertEqual(expected, payload_digest(node_payload(node)))

    def test_unreached_definitions_remain_outside_the_live_queue(self):
        self.assertEqual(
            100, self.inventory["counts"]["unreviewed_stacked_main_unreached"])
        self.assertTrue(
            set(EXPECTED_HOLDS).isdisjoint(self.inventory["sets"]["unreached"]))


if __name__ == "__main__":
    unittest.main()
