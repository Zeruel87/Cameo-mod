import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "balance"))

import prepare_missile_role_decisions as packet


class MissileRoleDecisionPacketTests(unittest.TestCase):
    def _triage(self):
        strict = {
            "R1": [
                {
                    "weapon": "ground_ap",
                    "role": "ground",
                    "flies": "MissileAP",
                    "expected": "MissileHE",
                    "actor_consumers": [{"actor": "tank", "route": "Armament"}],
                    "inheritance_chain": [],
                    "family_sources": [],
                    "weapon_source": {"file": "mods/cameo/weapons.yaml", "line": 2},
                }
            ],
            "R2": [],
            "R3": [
                {
                    "weapon": "dual_he",
                    "role": "both",
                    "flies": "MissileHE",
                    "expected": "MissileAP",
                    "actor_consumers": [
                        {"actor": "a", "route": "Armament"},
                        {"actor": "b", "route": "Armament@SECONDARY"},
                    ],
                    "inheritance_chain": [],
                    "family_sources": [],
                    "weapon_source": {"file": "mods/cameo/weapons.yaml", "line": 3},
                }
            ],
            "R4": [
                {
                    "weapon": "dual_he",
                    "role": "both",
                    "flies": "MissileHE",
                    "expected": "MissileAP",
                    "actor_consumers": [
                        {"actor": "a", "route": "Armament"},
                        {"actor": "b", "route": "Armament@SECONDARY"},
                    ],
                    "inheritance_chain": [],
                    "family_sources": [],
                    "weapon_source": {"file": "mods/cameo/weapons.yaml", "line": 3},
                }
            ],
        }
        return {
            "strict_findings": strict,
            "custom_selectors": [
                {"bucket": "water-or-underwater", "actor_consumers": [{"actor": "ship"}]},
                {"bucket": "water-or-underwater", "actor_consumers": []},
            ],
            "policy_questions": [{"subject": "V2", "weapon": "v2", "review_status": "POLICY_REVIEW_REQUIRED"}],
        }

    def test_r4_is_merged_and_marked_critical(self):
        result = packet.build_packet(self._triage(), pathlib.Path("triage.json"))
        self.assertEqual(result["summary"]["unique_strict_weapon_count"], 2)
        self.assertEqual(result["summary"]["raw_strict_row_count"], 3)
        row = next(item for item in result["strict_cases"] if item["weapon"] == "dual_he")
        self.assertEqual(row["codes"], ["R3", "R4"])
        self.assertEqual(row["lane"], "DUAL_DOMAIN_ABSOLUTE_RULE")
        self.assertEqual(row["priority"], "critical")

    def test_single_domain_multi_consumer_is_high_priority(self):
        triage = self._triage()
        triage["strict_findings"]["R1"][0]["actor_consumers"] *= 2
        result = packet.build_packet(triage, pathlib.Path("triage.json"))
        row = next(item for item in result["strict_cases"] if item["weapon"] == "ground_ap")
        self.assertEqual(row["lane"], "SINGLE_DOMAIN_ROLE_REVIEW")
        self.assertEqual(row["priority"], "high")

    def test_packet_is_explicitly_review_only(self):
        result = packet.build_packet(self._triage(), pathlib.Path("triage.json"))
        self.assertEqual(result["source"]["status"], "REVIEW_ONLY")
        self.assertTrue(any("Do not change" in item for item in result["guardrails"]))
        self.assertEqual(result["summary"]["custom_bucket_counts"], {"water-or-underwater": 2})


if __name__ == "__main__":
    unittest.main()
