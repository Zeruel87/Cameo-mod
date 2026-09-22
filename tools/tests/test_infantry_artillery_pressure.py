"""Focused checks for the static infantry-pressure receipt."""
import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import infantry_artillery_pressure as pressure  # noqa: E402


def record(actor, weapon, *, scenario="infantry", status="RESOLVED", terms=None):
    return {
        "actor": actor,
        "weapon": weapon,
        "scenario": scenario,
        "status": status,
        "terms": terms or {
            "None": {"A": 100.0, "B": 0.1},
            "Light": {"A": 50.0, "B": 0.05},
        },
    }


class InfantryArtilleryPressureTests(unittest.TestCase):
    def test_projection_keeps_flat_and_percentage_components(self):
        result, reason = pressure._projection(
            {"None": {"A": 100, "B": 0.1}}, 1000, "None"
        )
        self.assertIsNone(reason)
        self.assertEqual(result["flat_A"], 100)
        self.assertEqual(result["percentage_at_target_hp"], 100)
        self.assertEqual(result["uncapped_total"], 200)
        self.assertEqual(result["target_hp_bars"], 0.2)

    def test_explicit_case_resolves_and_identity_guard_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = pathlib.Path(directory) / "ledger.json"
            ledger_path.write_text(json.dumps({
                "sections": {"infantry": {
                    "target": {"hp": {"v": "1000"}, "armor": {"v": "None"}},
                    "artillery": {"armaments": [{"weapon": "shell"}]}
                }}
            }), encoding="utf-8")
            manifest = {"cases": [{
                "id": "test",
                "faction": "Test",
                "target_actor": "target",
                "target_ledger": str(ledger_path),
                "target_record_index": 0,
                "weapon_actor": "artillery",
                "weapon_ledger": str(ledger_path),
                "weapon_record_index": 1,
                "expected": {
                    "target_scenario": "infantry",
                    "target_weapon": "rifle",
                    "weapon_scenario": "infantry",
                    "weapon": "shell",
                },
            }]}
            cameo = {"records": [
                record("target", "rifle"),
                record("artillery", "shell"),
            ]}
            result = pressure.build_report(manifest, cameo)
            self.assertEqual(result["status"], "RESOLVED")
            self.assertEqual(result["rows"][0]["weapon"]["projections"]["None"]["uncapped_total"], 200)
            cameo["records"][1]["weapon"] = "wrong"
            failed = pressure.build_report(manifest, cameo)
            self.assertEqual(failed["status"], "UNRESOLVED")
            self.assertTrue(failed["rows"][0]["reasons"])


if __name__ == "__main__":
    unittest.main()
