"""Focused tests for explicit four-voice coverage inventory."""
import copy
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import four_source_group_inventory as inventory  # noqa: E402


SOURCES = inventory.SOURCES


def reference(source, *, status="RESOLVED", channels=None, selected=None,
              comparison_id=None, scenario=None, state_key=None, terms=None,
              identity=None):
    result = {"source": source, "id": source.replace(" ", "_"), "status": status,
              "channels": list(channels or []),
              "selected_weapon_channels": list(selected or [])}
    for key, value in (("comparison_id", comparison_id), ("scenario", scenario),
                       ("state_key", state_key), ("terms", terms)):
        if value is not None:
            result[key] = copy.deepcopy(value)
    if identity is not None:
        result["channel_identity"] = copy.deepcopy(identity)
    return result


def matrix(rows):
    return {"scope": "fixture", "summary": {"fixture": True}, "rows": rows}


def reference_voices(*, explicit=False, sources=None):
    sources = list(SOURCES if sources is None else sources)
    kwargs = {}
    if explicit:
        kwargs = {"comparison_id": "actor/base", "scenario": "vehicle",
                  "state_key": "base", "terms": {"Light": {"A": 1, "B": 0},
                                                     "Heavy": {"A": 2, "B": 0}}}
    return [reference(source, **kwargs) for source in sources]


def current_voice(*, explicit=False):
    result = {"status": "RESOLVED", "terms": {"Light": {"A": 1, "B": 0},
                                                  "Heavy": {"A": 2, "B": 0}}}
    if explicit:
        result.update({"comparison_id": "actor/base", "scenario": "vehicle",
                       "state_key": "base"})
    return result


class FourSourceGroupInventoryTests(unittest.TestCase):
    def test_uneven_reference_coverage_reports_missing_fixed_reference(self):
        row = {"actor": "alpha", "cameo_channels": [{"slot": "Armament"}],
               "references": reference_voices(sources=SOURCES[:3])}
        result = inventory.inventory_matrix(matrix([row]))

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["summary"]["actors"], 1)
        self.assertEqual(result["summary"]["complete_four_source"], 0)
        self.assertEqual(result["summary"]["complete_four_voice"], 1)
        self.assertEqual(result["summary"]["missing_by_source"]["DTA Enhanced"], 1)
        self.assertIn("missing_reference_source:DTA Enhanced",
                      result["summary"]["reference_gate_blockers"])

    def test_duplicate_source_is_retained_and_marked(self):
        refs = reference_voices(sources=("Combined Arms", "OpenRA Red Alert"))
        refs.append(reference("Combined Arms"))
        actor = inventory.inventory_matrix(matrix([{
            "actor": "dup", "cameo_channels": [{"slot": "Armament"}],
            "references": refs
        }]))["actors"][0]

        self.assertEqual(actor["source_presence"]["Combined Arms"], 2)
        self.assertEqual(actor["duplicate_sources"], ["Combined Arms"])
        self.assertFalse(actor["complete_four_source"])
        self.assertFalse(actor["complete_four_voice"])
        self.assertIn("duplicate_reference_voice:Combined Arms", actor["gate_blockers"])

    def test_complete_four_voice_still_needs_explicit_group_metadata(self):
        actor = inventory.inventory_matrix(matrix([{
            "actor": "metadata-missing", "cameo_channels": [{"slot": "Armament"}],
            "references": reference_voices(sources=SOURCES[:3])
        }]))["actors"][0]

        self.assertTrue(actor["complete_four_voice"])
        self.assertFalse(actor["gate_ready"])
        self.assertIn("explicit_group_metadata_missing", actor["gate_blockers"])
        self.assertEqual(actor["explicit_group"]["missing_fields"],
                         ["comparison_id", "scenario", "state_key"])

    def test_complete_four_voice_rows_are_gate_ready_only_with_explicit_terms(self):
        refs = reference_voices(explicit=True, sources=SOURCES[:3])
        actor = inventory.inventory_matrix(matrix([{
            "actor": "ready", "cameo_channels": [{"slot": "Armament"}],
            "current_voice": current_voice(explicit=True), "references": refs
        }]))["actors"][0]

        self.assertTrue(actor["complete_four_voice"])
        self.assertTrue(actor["gate_ready"])
        self.assertEqual(actor["explicit_group"]["comparison_id"], "actor/base")
        self.assertEqual(inventory.inventory_matrix(matrix([{
            "actor": "ready", "cameo_channels": [{"slot": "Armament"}],
            "current_voice": current_voice(explicit=True), "references": refs
        }]))["summary"]["gate_ready"], 1)

    def test_malformed_top_level_input_fails_closed(self):
        for supplied, reason in ((None, "matrix_not_object"),
                                 ({"rows": {}}, "rows_not_list")):
            with self.subTest(supplied=supplied):
                result = inventory.inventory_matrix(supplied)
                self.assertEqual(result["status"], "UNRESOLVED")
                self.assertIn(reason, result["reasons"])

    def test_candidate_coverage_names_every_actor_without_inferred_na(self):
        rows = [
            {"actor": "reviewed", "cameo_channels": [{}],
             "references": reference_voices(sources=SOURCES[:3])},
            {"actor": "candidate", "cameo_channels": [{}],
             "references": reference_voices(sources=SOURCES[:3])},
            {"actor": "partial", "cameo_channels": [{}],
             "references": reference_voices(sources=SOURCES[:1])},
            {"actor": "unarmed", "cameo_channels": [], "references": []},
        ]
        manifest_doc = {"groups": [{
            "comparison_id": "reviewed/vehicle/base",
            "scenario": "vehicle",
            "state_key": "base",
            "voices": [{"voice": "Current Cameo",
                        "expected": {"actor": "reviewed"}}],
        }]}
        result = inventory.reconcile_candidate_coverage(
            matrix(rows), manifest_doc,
            {"status": "UNRESOLVED", "reason": "fixture"},
        )
        dispositions = {row["actor"]: row["disposition"]
                        for row in result["actors"]}
        self.assertEqual(result["summary"]["accounted_actor_rows"], 4)
        self.assertEqual(dispositions["reviewed"],
                         "EXPLICIT_GROUPS_SELF_VOTE_UNBOUND")
        self.assertEqual(dispositions["candidate"],
                         "THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP")
        self.assertEqual(dispositions["partial"],
                         "UNRESOLVED_REFERENCE_COVERAGE")
        self.assertEqual(dispositions["unarmed"],
                         "UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL")
        self.assertEqual(result["summary"]["explicit_not_applicable"], 0)

    def test_input_is_unchanged_and_raw_reference_fields_are_retained(self):
        source = matrix([{"actor": "immutable", "references": [
            reference(SOURCES[0], channels=[{"raw": "keep"}], selected=[{"slot": "A"}])
        ]}])
        before = copy.deepcopy(source)
        result = inventory.inventory_matrix(source)

        self.assertEqual(source, before)
        self.assertEqual(result["actors"][0]["references"][0]["id"], "Combined_Arms")
        self.assertEqual(result["actors"][0]["references"][0]["channel_count"], 1)
        self.assertEqual(result["actors"][0]["references"][0]["selected_channel_count"], 1)


if __name__ == "__main__":
    unittest.main()
