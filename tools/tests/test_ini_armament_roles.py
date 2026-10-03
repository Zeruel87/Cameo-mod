from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import extract_ini_armament_roles as roles  # noqa: E402
import extract_ini_elite_weapons as elite  # noqa: E402
import armament_roles as armament  # noqa: E402


class TargetPolicyTests(unittest.TestCase):
    def test_all_explicit_ra2_combinations_resolve(self):
        expected = {
            ("no", "no"): "special",
            ("yes", "no"): "air",
            ("no", "yes"): "ground",
            ("yes", "yes"): "both",
        }
        for flags, role in expected.items():
            verdict, reason = roles.projectile_verdict(
                {"P": {"AA": flags[0], "AG": flags[1]}}, "P", "ra2")
            self.assertIsNone(reason)
            self.assertEqual(role, verdict["role"])
            self.assertEqual(["AA", "AG"], verdict["declared"])

    def test_ra2_missing_either_flag_abstains(self):
        for section in ({"AA": "yes"}, {"AG": "yes"}, {}):
            verdict, reason = roles.projectile_verdict({"P": section}, "P", "ra2")
            self.assertIsNone(verdict)
            self.assertEqual("ra2_target_default_unverified", reason)

    def test_ts_uses_declared_engine_defaults(self):
        verdict, reason = roles.projectile_verdict({"P": {}}, "P", "ts")
        self.assertIsNone(reason)
        self.assertEqual("ground", verdict["role"])
        self.assertEqual([], verdict["declared"])

    def test_malformed_or_empty_boolean_abstains_everywhere(self):
        for invalid in ("", "maybe", "?"):
            verdict, reason = roles.projectile_verdict(
                {"P": {"AA": invalid, "AG": "yes"}}, "P", "ts")
            self.assertIsNone(verdict)
            self.assertEqual("invalid_target_boolean", reason)
            self.assertEqual((None, []), elite.projectile_role(
                {"P": {"AA": invalid, "AG": "yes"}}, "P"))

    def test_missing_projectile_section_abstains(self):
        self.assertEqual((None, "projectile_section_absent"),
                         roles.projectile_verdict({}, "Missing", "ra2"))


class ConsumerGateTests(unittest.TestCase):
    def row(self, **changes):
        row = {
            "source": "S", "weapon": "Gun", "w_projectile": "P",
            "w_damage": 10, "w_reload": 5, "w_range": 6, "w_burst": 1,
        }
        row.update(changes)
        return row

    def test_legacy_or_incomplete_slot_cannot_vote(self):
        evidence = {("S", "P"): {"role": "ground"}}
        for changes in ({}, {"w_evidence": "incomplete", "w_dps_usable": False}):
            view = armament.ini_views(self.row(**changes), evidence)[0]
            self.assertFalse(view["eligible"])
            self.assertEqual([], armament.candidates_by_role([view]).get("ground", []))

    def test_one_slot_never_authorizes_its_sibling(self):
        row = self.row(w_evidence="nominal_direct", w_dps_usable=True,
                       w2_weapon="Other", w2_projectile="Q", w2_damage=20,
                       w2_reload=5, w2_range=7, w2_burst=1,
                       w2_evidence="incomplete")
        evidence = {("S", "P"): {"role": "ground"},
                    ("S", "Q"): {"role": "air"}}
        views = armament.ini_views(row, evidence)
        self.assertTrue(views[0]["eligible"])
        self.assertFalse(views[1]["eligible"])
        self.assertEqual({"ground"}, set(armament.candidates_by_role(views)))

    def test_exact_sidecar_values_replace_untrusted_corpus_numbers(self):
        exact = {("S", "Gun", "P"): {
            "status": "resolved", "role": "air", "damage": 30,
            "reload": 10, "range": 9, "burst": 1,
            "weapon_evidence": "nominal_direct", "w_dps_usable": True,
        }}
        view = armament.ini_views(self.row(w_damage=999, w_reload=1, w_range=99), exact)[0]
        self.assertTrue(view["eligible"])
        self.assertEqual((30.0, 10.0, 9.0),
                         (view["damage_per_shot"], view["cycle"], view["range"]))
        self.assertEqual("air", view["role"])

    def test_exact_status_cannot_bypass_the_evidence_contract(self):
        exact = {("S", "Gun", "P"): {
            "status": "resolved", "role": "ground", "damage": 30,
            "reload": 10, "range": 9, "burst": 1,
            "weapon_evidence": "incomplete", "w_dps_usable": False,
        }}
        view = armament.ini_views(self.row(), exact)[0]
        self.assertFalse(view["eligible"])
        self.assertEqual({}, armament.candidates_by_role([view]))

    def test_case_aliases_do_not_match_exact_evidence(self):
        exact = {("S", "gun", "p"): {
            "status": "resolved", "role": "ground", "damage": 30,
            "reload": 10, "range": 9, "burst": 1,
        }}
        view = armament.ini_views(self.row(), exact)[0]
        self.assertFalse(view["eligible"])

    def test_a_readable_burst_folds_at_one_tick_instead_of_being_benched(self):
        """⭐ THE BURST FOLD (maintainer, 2026-09-14).

        `{"burst": 2}` used to sit in the `bad` tuple below, refused as `burst_unfolded`. The
        refusal existed because nothing could say how long a multi-shot cycle takes; the ruling
        says it takes the engine minimum between shots: *"if there is no burst delay you can use
        the minimal allowed value of 1 ticks between the bursts"*. So two shots of 30 over a
        10-tick reload plus one 1-tick gap: cycle 11, 60 damage in it.

        ⚠ The INVALID numbers around it are untouched and still bench - a burst of 0 or 1.5 is
        not a cadence this can fold, it is a declaration nobody can read.
        """
        exact = {("S", "Gun", "P"): {
            "status": "resolved", "role": "ground",
            "weapon_evidence": "nominal_direct", "w_dps_usable": True,
            "damage": 30, "reload": 10, "range": 9, "burst": 2,
        }}
        view = armament.ini_views(self.row(), exact)[0]
        self.assertTrue(view["eligible"])
        self.assertEqual(11, view["cycle"])
        self.assertEqual(60, view["damage_per_cycle"])

    def test_burst_and_invalid_numbers_never_enter_the_bench(self):
        bad = (
            {"damage": 30, "reload": 10, "range": 9, "burst": 0},
            {"damage": float("nan"), "reload": 10, "range": 9, "burst": 1},
            {"damage": -3, "reload": 10, "range": 9, "burst": 1},
            {"damage": 30, "reload": 0, "range": 9, "burst": 1},
            {"damage": 30, "reload": 10, "range": 9, "burst": 1.5},
        )
        for record in bad:
            exact = {("S", "Gun", "P"): {
                "status": "resolved", "role": "ground",
                "weapon_evidence": "nominal_direct", "w_dps_usable": True,
                **record,
            }}
            view = armament.ini_views(self.row(), exact)[0]
            self.assertFalse(view["eligible"], record)
            self.assertIsNone(view["cycle"], record)
            self.assertEqual({}, armament.candidates_by_role([view]), record)

    def test_withheld_elite_still_supersedes_its_base_for_expanded_units(self):
        base = armament.view("ini", "primary", "Gun", "ground",
                             damage_per_shot=30, cycle=10, rng=6)
        held = armament.view("ini", "elite", "GunE", "ground",
                             damage_per_shot=60, cycle=None, rng=7, baseline=False,
                             gate="elite", replaces="Gun", additive=False,
                             eligible=False, refusal="burst_unfolded")
        bench = armament.tier_bench([base, held], armament.TIER_EXPANDED)
        self.assertEqual(["GunE"], [view["weapon"] for view in bench])
        self.assertEqual({}, armament.candidates_by_role(bench))


class RepositoryEvidenceTests(unittest.TestCase):
    def mutated_root(self, mutation):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name)
        target = root / "docs" / "reference"
        target.mkdir(parents=True)
        for name in ("ini_corpus.json", "ini_source_pins.json",
                     "ini_armament_role_evidence.json"):
            shutil.copy2(ROOT / "docs" / "reference" / name, target / name)
        path = target / "ini_armament_role_evidence.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        source = next(entry for entry in doc["sources"] if entry["engine"] == "ra2")
        record = next(record for record in source["armaments"].values()
                      if record["status"] == "resolved")
        mutation(record)
        path.write_text(json.dumps(doc), encoding="utf-8")
        return root

    def test_all_seven_sources_load_and_bind_to_current_corpus(self):
        loaded = roles.load(ROOT)
        self.assertEqual([], roles.load.dropped)
        self.assertEqual(496, len(loaded))

        doc = json.loads((ROOT / "docs/reference/ini_armament_role_evidence.json")
                         .read_text(encoding="utf-8"))
        self.assertEqual(7, len(doc["sources"]))
        self.assertEqual(496, sum(s["resolved_armaments"] for s in doc["sources"]))
        for source in doc["sources"]:
            for record in source["armaments"].values():
                if record["status"] == "resolved":
                    self.assertEqual(1, record["burst"])
                    self.assertEqual("nominal_direct", record["weapon_evidence"])
                    self.assertIs(record["w_dps_usable"], True)

    def test_known_unsafe_elite_weapons_are_withheld_from_every_pair(self):
        names = {"TNKDCannonE", "BehemortarE", "70mmMslxE", "Arty155mmE",
                 "HeavyRaiderCannonE", "105mmAE"}
        elite_doc = json.loads((ROOT / "docs/reference/ini_elite_weapon_evidence.json")
                               .read_text(encoding="utf-8"))
        records = {record["weapon"]: record for source in elite_doc["sources"]
                   for record in source["units"].values() if record["weapon"] in names}
        self.assertEqual(names, set(records))
        self.assertTrue(all(record["status"] == "abstained" for record in records.values()))
        pairing = json.loads((ROOT / "docs/balance/derived/armament_pairing.json")
                             .read_text(encoding="utf-8"))
        paired = {pair["peer"]["weapon"] for actor in pairing["actors"].values()
                  for source in actor["sources"].values() for pair in source.get("pairs", ())}
        self.assertTrue(names.isdisjoint(paired))

    def test_pairing_fingerprints_include_both_source_pin_dependencies(self):
        import build_armament_pairing_report as report
        self.assertIn("docs/reference/ini_source_pins.json", report.DATA_INPUT_FILES)
        self.assertIn("tools/reference/ini_source_pins.py", report.TOOL_INPUT_FILES)

    def test_source_change_during_armament_extraction_refuses_publication(self):
        configured = {"S": {"source": "S", "file": "s.ini", "engine": "ra2",
                            "rules_sha256": "a" * 64,
                            "corpus_weapon_links_sha256": "b" * 64}}
        with tempfile.TemporaryDirectory() as temp:
            ini_dir = pathlib.Path(temp)
            (ini_dir / "s.ini").write_text("[P]\nAA=yes\nAG=no\n", encoding="latin-1")
            with (patch.object(roles.pins, "verify_all", return_value=[{"source": "S"}]),
                  patch.object(roles.pins, "load", return_value=configured),
                  patch.object(roles.pins, "file_sha256",
                               side_effect=["a" * 64, "c" * 64])):
                with self.assertRaisesRegex(ValueError, "changed during"):
                    roles.build(ini_dir, ROOT)

    def test_loader_refuses_ra2_record_without_both_declarations(self):
        root = self.mutated_root(lambda record: record.update(declared=[]))
        with self.assertRaisesRegex(ValueError, "RA2 targeting defaults"):
            roles.load(root)

    def test_loader_refuses_boolean_burst(self):
        root = self.mutated_root(lambda record: record.update(burst=True))
        with self.assertRaisesRegex(ValueError, "resolved evidence violates"):
            roles.load(root)


if __name__ == "__main__":
    unittest.main()
