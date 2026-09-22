"""Failure-injection tests: confirmation must not destroy proposals or lie."""
import contextlib
import copy
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import apply_balance as apply
from apply_transaction import ApplyError, Transaction


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.ledger = self.root / "docs/balance"
        self.ledger.mkdir(parents=True)
        (self.ledger / "derived").mkdir()
        self.yaml = self.root / "mods/cameo/rules/test.yaml"
        self.yaml.parent.mkdir(parents=True)
        self.original = b'\xef\xbb\xbfunit:\r\n\tValued:\r\n\t\tCost: 100\r\n\tHealth:\r\n\t\tHP: 500\r\n'
        self.yaml.write_bytes(self.original)
        self.weapon = self.yaml.parent / "weapons.yaml"
        self.weapon.write_text("Gun:\n\tReloadDelay: 20\n\tWarhead@Hit: SpreadDamage\n\t\tDamage: 100\n", encoding="utf-8")
        (self.root / "mods/cameo/mod.yaml").write_text(
            "Rules:\n\tcameo|rules/test.yaml:\nWeapons:\n\tcameo|rules/weapons.yaml:\n", encoding="utf-8")
        self.unit = {"cost": {"v": 100, "src": "mods/cameo/rules/test.yaml#Valued.Cost"},
                     "hp": {"v": 500, "src": "mods/cameo/rules/test.yaml#Health.HP"},
                     "armaments": [{"slot": "Armament", "weapon": "Gun",
                                    "defined_in": "mods/cameo/rules/weapons.yaml", "reloaddelay": "20",
                                    "damage_warheads": [{"tag": "Hit", "damage": 100}]}]}
        self.fresh = {"test": {"schema": 2, "ledger": "test", "sections": {"infantry": {"unit": self.unit}}}}
        self.desired = copy.deepcopy(self.fresh)
        self.write_ledgers()
        self.model = self.ledger / "derived/_model.json"
        self.model.write_bytes(b'{"old": true}\n')
        self.sidecar = self.ledger / "derived/test.json"
        self.sidecar.write_bytes(b'{"old": true}\n')
        self.patches = [patch.object(apply, "ROOT", self.root),
                        patch.object(apply, "LEDGER", self.ledger),
                        patch.object(apply, "fresh_ledgers", return_value=self.fresh),
                        patch.object(apply, "reference_problems", return_value=[])]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def write_ledgers(self):
        for name, doc in self.desired.items():
            (self.ledger / f"{name}.json").write_text(json.dumps(doc), encoding="utf-8")

    def change_cost(self):
        self.desired["test"]["sections"]["infantry"]["unit"]["cost"]["v"] = 150
        self.write_ledgers()

    def run_apply(self, *args, runner=None):
        output = io.StringIO()
        with patch.object(sys, "argv", ["apply_balance.py", *args]), contextlib.redirect_stdout(output), \
                patch.object(apply.subprocess, "run", side_effect=runner) as child:
            result = apply.main()
        return result, output.getvalue(), child

    def successful_child(self, command, **kwargs):
        self.assertTrue(kwargs["check"])
        self.assertEqual(kwargs["cwd"], self.root)
        if "--output-dir" in command:
            self.assertEqual(len(command), 4)
            stage = pathlib.Path(command[-1])
            stage.mkdir()
            (stage / "derived").mkdir()
            for name, doc in self.desired.items():
                (stage / f"{name}.json").write_text(json.dumps(doc), encoding="utf-8")
                (stage / f"derived/{name}.json").write_text('{"new": true}', encoding="utf-8")
            (stage / "derived/_model.json").write_text('{"new": true}', encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    def test_dry_run_never_writes_or_runs_children(self):
        self.change_cost()
        code, text, child = self.run_apply()
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN: 1", text)
        self.assertEqual(self.yaml.read_bytes(), self.original)
        child.assert_not_called()

    def test_shadowed_values_refuse_but_consistent_noops_pass(self):
        baseline = copy.deepcopy(self.fresh)
        original_weapon = self.weapon.read_bytes()
        for field in ("cost", "reload", "damage"):
            with self.subTest(field=field):
                self.fresh.clear()
                self.fresh.update(copy.deepcopy(baseline))
                self.desired = copy.deepcopy(self.fresh)
                unit = self.desired["test"]["sections"]["infantry"]["unit"]
                self.yaml.write_bytes(self.original)
                self.weapon.write_bytes(original_weapon)
                if field == "cost":
                    unit["cost"]["v"] = 150
                    self.yaml.write_bytes(self.original.replace(b"Cost: 100", b"Cost: 150"))
                elif field == "reload":
                    unit["armaments"][0]["reloaddelay"] = "30"
                    self.weapon.write_bytes(original_weapon.replace(b"ReloadDelay: 20", b"ReloadDelay: 30"))
                else:
                    unit["armaments"][0]["damage_warheads"][0]["damage"] = 200
                    self.weapon.write_bytes(original_weapon.replace(b"Damage: 100", b"Damage: 200"))
                self.write_ledgers()
                before = (self.yaml.read_bytes(), self.weapon.read_bytes())
                code, text, child = self.run_apply("--confirm")
                self.assertEqual(code, 1, text)
                self.assertIn("SHADOWED", text)
                child.assert_not_called()
                self.assertEqual((self.yaml.read_bytes(), self.weapon.read_bytes()), before)
                self.fresh.clear()
                self.fresh.update(copy.deepcopy(self.desired))
                code, text, child = self.run_apply("--confirm")
                self.assertEqual(code, 0, text)
                self.assertIn("NO CHANGES", text)
                child.assert_not_called()

    def test_retired_multiplier_change_refuses_but_preservation_passes(self):
        unit = self.fresh["test"]["sections"]["infantry"]["unit"]
        unit["firepower_multiplier"] = {"v": .5, "src": "inherited"}
        self.desired = copy.deepcopy(self.fresh)
        self.change_cost()
        code, text, child = self.run_apply()
        self.assertEqual(code, 0, text)
        self.assertIn("DRY RUN: 1", text)
        self.desired["test"]["sections"]["infantry"]["unit"]["firepower_multiplier"]["v"] = 1
        self.write_ledgers()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1, text)
        self.assertIn("RETIRED KNOB", text)
        child.assert_not_called()

    def test_untouched_inherited_stat_and_utility_arm_do_not_block(self):
        unit = self.fresh["test"]["sections"]["infantry"]["unit"]
        unit["hp"]["src"] = "inherited"
        unit["armaments"].append({"slot": "Armament@UTILITY", "reloaddelay": "20"})
        self.desired = copy.deepcopy(self.fresh)
        self.change_cost()
        code, text, _ = self.run_apply()
        self.assertEqual(code, 0, text)
        self.assertIn("DRY RUN: 1", text)
        self.desired["test"]["sections"]["infantry"]["unit"]["hp"]["v"] = 600
        self.write_ledgers()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1, text)
        self.assertIn("inherited edit", text)
        child.assert_not_called()

    def test_represented_weapon_consumer_and_unrelated_inheritance_pass(self):
        self.patches[-1].stop()
        self.yaml.write_bytes(self.original + b"\tArmament:\r\n\t\tWeapon: Gun\r\n"
                              b"unrelated:\r\n\tValued:\r\n\t\tCost: 1\r\n"
                              b"child:\r\n\tInherits: unrelated\r\n")
        self.assertEqual(apply.reference_problems(self.desired, {"unit"}, {"Gun"}), [])

    def test_noop_confirmation_does_not_refresh_ledgers(self):
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 0)
        self.assertIn("NO CHANGES", text)
        child.assert_not_called()
        self.assertEqual(self.yaml.read_bytes(), self.original)

    def test_unsupported_edit_is_not_a_successful_noop(self):
        cases = ("delete_cost", "delete_actor", "scalar_cost", "change_weapon", "delete_armament", "delete_reload")
        for case in cases:
            with self.subTest(case=case):
                self.desired = copy.deepcopy(self.fresh)
                units = self.desired["test"]["sections"]["infantry"]
                unit = units["unit"]
                if case == "delete_cost":
                    del unit["cost"]
                elif case == "delete_actor":
                    del units["unit"]
                elif case == "scalar_cost":
                    unit["cost"] = 150
                elif case == "change_weapon":
                    unit["armaments"][0]["weapon"] = "Other"
                elif case == "delete_reload":
                    del unit["armaments"][0]["reloaddelay"]
                else:
                    unit["armaments"] = []
                self.write_ledgers()
                code, text, child = self.run_apply("--confirm")
                self.assertEqual(code, 1, text)
                self.assertIn("unsupported ledger edit", text)
                if case == "change_weapon":
                    self.assertIn("missing or stale armament provenance", text)
                self.assertNotIn("NO CHANGES", text)
                child.assert_not_called()

    def test_success_preserves_bom_and_crlf(self):
        self.change_cost()
        code, text, child = self.run_apply("--confirm", runner=self.successful_child)
        self.assertEqual(code, 0, text)
        self.assertIn("APPLIED AND VERIFIED", text)
        self.assertEqual(self.yaml.read_bytes(), self.original.replace(b"100", b"150"))
        self.assertEqual(child.call_count, 2)
        self.assertEqual(json.loads(self.sidecar.read_text(encoding="utf-8")), {"new": True})

    def _add_heal_repair_fields(self):
        self.yaml.write_bytes(
            self.original
            + b"\tChangesHealth@SelfHealing:\r\n"
            + b"\t\tStep: 10\r\n"
            + b"\tRepairable:\r\n"
            + b"\t\tHpPerStep: 100\r\n"
        )
        unit = self.fresh["test"]["sections"]["infantry"]["unit"]
        unit["self_heal_step"] = {
            "v": "10",
            "src": "mods/cameo/rules/test.yaml#ChangesHealth@SelfHealing.Step",
        }
        unit["repairable_hp_per_step"] = {
            "v": "100",
            "src": "mods/cameo/rules/test.yaml#Repairable.HpPerStep",
        }
        self.desired = copy.deepcopy(self.fresh)
        target = self.desired["test"]["sections"]["infantry"]["unit"]
        target["self_heal_step"]["v"] = "20"
        target["repairable_hp_per_step"]["v"] = "200"
        self.write_ledgers()

    def test_heal_and_repair_write_through_exact_file_provenance(self):
        self._add_heal_repair_fields()
        code, text, child = self.run_apply("--confirm", runner=self.successful_child)
        self.assertEqual(0, code, text)
        self.assertIn("APPLIED AND VERIFIED", text)
        content = self.yaml.read_bytes()
        self.assertIn(b"Step: 20", content)
        self.assertIn(b"HpPerStep: 200", content)
        child.assert_called()

    def test_inherited_heal_source_refuses_without_writing_any_file(self):
        self._add_heal_repair_fields()
        target = self.desired["test"]["sections"]["infantry"]["unit"]
        target["self_heal_step"]["src"] = "inherited"
        self.write_ledgers()
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(1, code, text)
        self.assertIn("inherited edit is unsupported", text)
        child.assert_not_called()
        self.assertEqual(before, {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()})

    def test_extractor_failure_rolls_back_yaml_and_keeps_proposal(self):
        self.change_cost()
        proposal = (self.ledger / "test.json").read_bytes()
        def failure(command, **kwargs):
            raise subprocess.CalledProcessError(2, command)
        code, text, child = self.run_apply("--confirm", runner=failure)
        self.assertEqual(code, 1)
        self.assertNotIn("APPLIED", text)
        self.assertEqual(self.yaml.read_bytes(), self.original)
        self.assertEqual((self.ledger / "test.json").read_bytes(), proposal)
        self.assertEqual(child.call_count, 1)

    def test_audit_failure_rolls_back_without_publishing_staged_ledgers(self):
        self.change_cost()
        def failure(command, **kwargs):
            if "--output-dir" in command:
                return self.successful_child(command, **kwargs)
            raise subprocess.CalledProcessError(1, command)
        code, text, _ = self.run_apply("--confirm", runner=failure)
        self.assertEqual(code, 1)
        self.assertEqual(self.yaml.read_bytes(), self.original)
        self.assertEqual(self.model.read_bytes(), b'{"old": true}\n')
        self.assertNotIn("APPLIED", text)

    def test_resolved_mismatch_rolls_back(self):
        self.change_cost()
        def mismatch(command, **kwargs):
            result = self.successful_child(command, **kwargs)
            if "--output-dir" in command:
                (pathlib.Path(command[-1]) / "test.json").write_text(json.dumps(self.fresh["test"]), encoding="utf-8")
            return result
        code, text, child = self.run_apply("--confirm", runner=mismatch)
        self.assertEqual(code, 1)
        self.assertIn("resulting raw ledger differs", text)
        self.assertEqual(self.yaml.read_bytes(), self.original)
        self.assertEqual(child.call_count, 1)

    def test_invalid_second_edit_prevents_first_write(self):
        self.change_cost()
        unit = self.desired["test"]["sections"]["infantry"]["unit"]
        unit["hp"] = {"v": 800, "src": "inherited"}
        self.write_ledgers()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1)
        self.assertIn("inherited edit is unsupported", text)
        self.assertEqual(self.yaml.read_bytes(), self.original)
        child.assert_not_called()

    def test_stale_provenance_is_rejected(self):
        self.change_cost()
        self.desired["test"]["sections"]["infantry"]["unit"]["cost"]["src"] = "mods/cameo/rules/test.yaml#Health.HP"
        self.write_ledgers()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1)
        self.assertIn("stale provenance", text)
        child.assert_not_called()

    def test_structure_injection_is_rejected(self):
        self.desired["test"]["sections"]["infantry"]["unit"]["cost"]["v"] = "100\n\tInherits: ^Other"
        self.write_ledgers()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1)
        self.assertIn("unsupported scalar", text)
        child.assert_not_called()

    def test_invalid_engine_values_refuse_without_writes(self):
        cases = [("cost", value) for value in (150.5, "1c0", "2, 3", True, 2 ** 31, -(2 ** 31) - 1)]
        cases += [("hp", "1c0"), ("reloaddelay", "2, 3"),
                  ("reloaddelay", 0), ("burst", 0), ("damage", "1.5"),
                  ("range", "1.5c0"), ("range", "2097152c0"),
                  ("burstdelays", ""), ("burstdelays", "1.5")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.desired = copy.deepcopy(self.fresh)
                unit = self.desired["test"]["sections"]["infantry"]["unit"]
                # A valid first edit must not leak out when a later edit is refused.
                unit["cost"]["v"] = 150
                if field in ("cost", "hp"):
                    unit[field]["v"] = value
                elif field == "damage":
                    unit["armaments"][0]["damage_warheads"][0]["damage"] = value
                else:
                    unit["armaments"][0][field] = value
                self.write_ledgers()
                before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
                code, text, child = self.run_apply("--confirm")
                self.assertEqual(1, code, text)
                self.assertIn("REFUSED", text)
                child.assert_not_called()
                self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_changed_burst_revalidates_unchanged_delay_list(self):
        self.unit["armaments"][0].update(burst="3", burstdelays="2, 3")
        self.desired = copy.deepcopy(self.fresh)
        self.desired["test"]["sections"]["infantry"]["unit"]["armaments"][0]["burst"] = "4"
        self.write_ledgers()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(1, code, text)
        self.assertIn("Burst - 1", text)
        child.assert_not_called()
        self.assertEqual(self.original, self.yaml.read_bytes())

    def test_engine_scalar_types_and_bounds(self):
        int_fields = [f for f in apply.UNIT_FIELDS if f != "sight"] + ["burst", "reloaddelay", "damage"]
        for field in int_fields:
            for value in (-2 ** 31, 2 ** 31 - 1, "-1", "0", "+120"):
                with self.subTest(field=field, value=value):
                    self.assertTrue(apply.scalar_value(value, field))
            for value in (True, 1.0, "1.0", "1c0", "1,2", "１２", float("nan"),
                          float("inf"), 2 ** 31, -2 ** 31 - 1, "9" * 100):
                with self.subTest(field=field, value=value):
                    self.assertFalse(apply.scalar_value(value, field))
        for field in ("sight", "range", "minrange"):
            for value in ("1C0", "-1c2", "-1c-2", "2097151c1023", "-2097152c0", 2048):
                self.assertTrue(apply.scalar_value(value, field), (field, value))
            for value in ("1.5c0", "2097152c0", "2097151c1024", "-2097152c1", "0c2147483648"):
                self.assertFalse(apply.scalar_value(value, field), (field, value))
        self.assertTrue(apply.scalar_value("0, 5, -1", "burstdelays"))
        self.assertFalse(apply.scalar_value("1,", "burstdelays"))
        self.assertFalse(apply.scalar_value("1, 2147483648", "burstdelays"))
        self.assertFalse(apply.scalar_value(1, "unknown_field"))

    def test_valid_weapon_cadence_uses_engine_defaults(self):
        self.assertIsNone(apply.weapon_cadence_error({}))
        self.assertIsNone(apply.weapon_cadence_error({"burst": "3", "burstdelays": "2, 3"}))
        self.assertIsNone(apply.weapon_cadence_error({"burst": "8"}))
        self.assertIsNone(apply.weapon_cadence_error({"burst": "8", "burstdelays": "5"}))

    def test_duplicate_block_is_rejected(self):
        self.yaml.write_bytes(self.original + self.original.removeprefix(b"\xef\xbb\xbf"))
        self.change_cost()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1)
        self.assertIn("ambiguous duplicate", text)
        child.assert_not_called()

    def test_duplicate_trait_or_field_is_rejected(self):
        for extra in (b"\tValued:\r\n\t\tCost: 100\r\n", b"\tHealth:\r\n\t\tHP: 500\r\n"):
            with self.subTest(extra=extra):
                self.yaml.write_bytes(self.original + extra)
                self.change_cost()
                if b"Health" in extra:
                    self.desired["test"]["sections"]["infantry"]["unit"]["hp"]["v"] = 600
                    self.write_ledgers()
                code, text, child = self.run_apply("--confirm")
                self.assertEqual(code, 1)
                self.assertIn("ambiguous duplicate", text)
                child.assert_not_called()

    def test_inline_comment_is_preserved(self):
        original = self.original.replace(b"Cost: 100", b"Cost: 100  # reviewed cost")
        self.yaml.write_bytes(original)
        self.change_cost()
        code, text, _ = self.run_apply("--confirm", runner=self.successful_child)
        self.assertEqual(code, 0, text)
        self.assertEqual(self.yaml.read_bytes(), original.replace(b"100", b"150"))

    def test_shared_changed_and_unchanged_rows_conflict(self):
        unit = self.desired["test"]["sections"]["infantry"]["unit"]
        self.desired["test"]["sections"]["infantry"]["other"] = copy.deepcopy(unit)
        self.fresh["test"]["sections"]["infantry"]["other"] = copy.deepcopy(self.unit)
        unit["armaments"][0]["damage_warheads"][0]["damage"] = 200
        self.write_ledgers()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1)
        self.assertIn("conflicting shared-weapon", text)
        self.assertEqual(self.weapon.read_text(encoding="utf-8").count("Damage: 100"), 1)
        child.assert_not_called()

    def test_missing_warhead_is_a_problem(self):
        self.weapon.write_text("Gun:\n\tReloadDelay: 20\n", encoding="utf-8")
        self.desired["test"]["sections"]["infantry"]["unit"]["armaments"][0]["damage_warheads"][0]["damage"] = 200
        self.write_ledgers()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1)
        self.assertIn("Damage not found", text)
        child.assert_not_called()

    def test_identical_shared_requests_are_counted_once(self):
        unit = self.desired["test"]["sections"]["infantry"]["unit"]
        unit["armaments"][0]["damage_warheads"][0]["damage"] = 200
        self.desired["test"]["sections"]["infantry"]["other"] = copy.deepcopy(unit)
        self.fresh["test"]["sections"]["infantry"]["other"] = copy.deepcopy(self.unit)
        self.write_ledgers()
        code, text, _ = self.run_apply("--confirm", runner=self.successful_child)
        self.assertEqual(code, 0, text)
        self.assertIn("1 planned values", text)

    def test_actor_inheritance_is_rejected_from_resolved_graph(self):
        self.patches[-1].stop()
        self.yaml.write_bytes(self.original + b"child:\r\n\tInherits: unit\r\n")
        problems = apply.reference_problems(self.desired, {"unit"}, set())
        self.assertTrue(any("inherits an edited actor" in p for p in problems))

    def test_nonledger_weapon_consumer_is_rejected_from_resolved_graph(self):
        self.patches[-1].stop()
        self.yaml.write_bytes(self.original + b"hidden:\r\n\tArmament:\r\n\t\tWeapon: Gun\r\n")
        problems = apply.reference_problems(self.desired, set(), {"Gun"})
        self.assertTrue(any("actor:hidden" in p for p in problems))

    def test_weapon_descendant_is_rejected_from_resolved_graph(self):
        self.patches[-1].stop()
        with self.weapon.open("a", encoding="utf-8") as file:
            file.write("ChildGun:\n\tInherits: Gun\n")
        problems = apply.reference_problems(self.desired, set(), {"Gun"})
        self.assertTrue(any("weapon:ChildGun" in p for p in problems))

    def test_missing_armament_provenance_is_rejected(self):
        arm = self.desired["test"]["sections"]["infantry"]["unit"]["armaments"][0]
        arm["defined_in"] = None
        arm["reloaddelay"] = "99"
        self.write_ledgers()
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1)
        self.assertIn("no writable provenance", text)
        child.assert_not_called()

    def test_inserted_weapon_field_is_counted(self):
        self.desired["test"]["sections"]["infantry"]["unit"]["armaments"][0]["range"] = "5c0"
        self.write_ledgers()
        code, text, _ = self.run_apply("--confirm", runner=self.successful_child)
        self.assertEqual(code, 0, text)
        self.assertIn("1 planned values", text)
        self.assertIn("\tRange: 5c0", self.weapon.read_text(encoding="utf-8"))

    def test_unknown_faction_is_not_success(self):
        code, text, child = self.run_apply("--faction", "missing", "--confirm")
        self.assertEqual(code, 1)
        self.assertIn("no actor ledger matches", text)
        child.assert_not_called()

    def test_non_ledger_metadata_is_ignored(self):
        (self.ledger / "reference.json").write_text('{"classes": []}', encoding="utf-8")
        code, text, _ = self.run_apply()
        self.assertEqual(code, 0, text)

    def test_missing_raw_ledger_requires_baseline_refresh(self):
        self.fresh["missing"] = {"ledger": "missing", "sections": {}}
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 1)
        self.assertIn("extracted ledger is missing", text)
        child.assert_not_called()

    def test_missing_extraction_or_actor_refuses_and_valid_fixture_passes(self):
        original_fresh = copy.deepcopy(self.fresh)
        for failure in ("ledger", "actor"):
            with self.subTest(failure=failure):
                self.fresh.clear()
                self.fresh.update(copy.deepcopy(original_fresh))
                if failure == "ledger":
                    self.fresh.clear()
                    message = "no current extracted ledger"
                else:
                    self.fresh["test"]["sections"]["infantry"].clear()
                    message = "no current resolved actor in this ledger section"
                code, text, child = self.run_apply("--confirm")
                self.assertEqual(code, 1, text)
                self.assertIn(message, text)
                self.assertEqual(self.yaml.read_bytes(), self.original)
                child.assert_not_called()
        self.fresh.clear()
        self.fresh.update(original_fresh)
        code, text, child = self.run_apply("--confirm")
        self.assertEqual(code, 0, text)
        self.assertIn("NO CHANGES", text)
        child.assert_not_called()

    def test_missing_local_unit_or_weapon_refuses_before_writes(self):
        original_weapon = self.weapon.read_bytes()
        for failure in ("unit", "weapon"):
            with self.subTest(failure=failure):
                self.desired = copy.deepcopy(self.fresh)
                self.yaml.write_bytes(self.original)
                self.weapon.write_bytes(original_weapon)
                if failure == "unit":
                    self.change_cost()
                    self.yaml.write_text("unit:\n\tHealth:\n\t\tHP: 500\n", encoding="utf-8")
                    message = "Valued.Cost` not written locally"
                else:
                    self.desired["test"]["sections"]["infantry"]["unit"]["armaments"][0]["reloaddelay"] = "30"
                    self.write_ledgers()
                    self.weapon.write_text("Other:\n\tReloadDelay: 20\n", encoding="utf-8")
                    message = "weapon `Gun` not found"
                before = {path: path.read_bytes() for path in (self.yaml, self.weapon)}
                code, text, child = self.run_apply("--confirm")
                self.assertEqual(code, 1, text)
                self.assertIn(message, text)
                self.assertEqual(before, {path: path.read_bytes() for path in before})
                child.assert_not_called()

    def test_interrupt_during_extraction_rolls_back(self):
        self.change_cost()
        with self.assertRaises(KeyboardInterrupt):
            self.run_apply("--confirm", runner=lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt()))
        self.assertEqual(self.yaml.read_bytes(), self.original)

    def test_unexpected_exception_during_audit_rolls_back(self):
        self.change_cost()
        def failure(command, **kwargs):
            if "--output-dir" in command:
                return self.successful_child(command, **kwargs)
            raise RuntimeError("unexpected")
        with self.assertRaisesRegex(RuntimeError, "unexpected"):
            self.run_apply("--confirm", runner=failure)
        self.assertEqual(self.yaml.read_bytes(), self.original)

    def test_concurrent_other_active_yaml_edit_prevents_success(self):
        self.change_cost()
        def concurrent(command, **kwargs):
            result = self.successful_child(command, **kwargs)
            if "--output-dir" not in command:
                self.weapon.write_text("Gun:\n\tRange: 6c0\n", encoding="utf-8")
            return result
        code, text, _ = self.run_apply("--confirm", runner=concurrent)
        self.assertEqual(code, 1)
        self.assertIn("concurrent edit", text)
        self.assertEqual(self.yaml.read_bytes(), self.original)
        self.assertIn("6c0", self.weapon.read_text(encoding="utf-8"))

    def test_unselected_pending_proposal_is_not_erased(self):
        other = copy.deepcopy(self.fresh["test"])
        other["ledger"] = "other"
        self.fresh["other"] = copy.deepcopy(other)
        other["sections"]["infantry"]["unit"]["cost"]["v"] = 999
        self.desired["other"] = other
        self.change_cost()
        proposal = (self.ledger / "other.json").read_bytes()
        code, text, child = self.run_apply("--faction", "test", "--confirm")
        self.assertEqual(code, 1)
        self.assertIn("unselected ledger has pending changes", text)
        self.assertEqual((self.ledger / "other.json").read_bytes(), proposal)
        self.assertEqual(self.yaml.read_bytes(), self.original)
        child.assert_not_called()

    def test_unchanged_unselected_ledger_allows_explicit_selected_faction(self):
        other = copy.deepcopy(self.fresh["test"])
        other["ledger"] = "other"
        self.fresh["other"] = copy.deepcopy(other)
        self.desired["other"] = other
        self.change_cost()
        before = (self.ledger / "other.json").read_bytes()
        code, text, child = self.run_apply("--faction", "test")
        self.assertEqual(code, 0, text)
        self.assertIn("DRY RUN: 1", text)
        self.assertNotIn("unselected ledger has pending changes", text)
        self.assertEqual((self.ledger / "other.json").read_bytes(), before)
        self.assertEqual(self.yaml.read_bytes(), self.original)
        child.assert_not_called()

    def test_partial_ledger_publish_rolls_back(self):
        self.change_cost()
        originals = {path: path.read_bytes() for path in self.ledger.rglob("*.json")}
        original_write = Transaction.write
        def fail(transaction, path, data):
            if path == self.sidecar:
                raise OSError("disk failure")
            return original_write(transaction, path, data)
        with patch.object(Transaction, "write", fail):
            code, text, _ = self.run_apply("--confirm", runner=self.successful_child)
        self.assertEqual(code, 1, text)
        self.assertEqual(self.yaml.read_bytes(), self.original)
        for path, data in originals.items():
            self.assertEqual(path.read_bytes(), data)


class TransactionTests(unittest.TestCase):
    def test_fsync_failure_closes_temporary_before_cleanup(self):
        import apply_transaction
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "file"
            path.write_bytes(b"original")
            with patch.object(apply_transaction.os, "fsync", side_effect=OSError("disk full")), \
                    self.assertRaisesRegex(OSError, "disk full"):
                apply_transaction.atomic_write(path, b"ours")
            self.assertEqual(path.read_bytes(), b"original")
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_interrupt_after_replace_is_tracked_and_recoverable(self):
        import apply_transaction
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "file"
            path.write_bytes(b"original")
            transaction = Transaction({path: b"original"})
            real_write = apply_transaction.atomic_write
            def interrupt(target, data):
                real_write(target, data)
                raise KeyboardInterrupt()
            with patch.object(apply_transaction, "atomic_write", interrupt), self.assertRaises(KeyboardInterrupt):
                transaction.write(path, b"ours")
            self.assertEqual(transaction.rollback(), [])
            self.assertEqual(path.read_bytes(), b"original")

    def test_concurrent_change_before_write_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "file"
            path.write_bytes(b"original")
            transaction = Transaction({path: b"original"})
            path.write_bytes(b"someone else")
            with self.assertRaises(ApplyError):
                transaction.write(path, b"ours")
            self.assertEqual(path.read_bytes(), b"someone else")


class StagedExtractorTests(unittest.TestCase):
    def test_output_directory_never_retargets_input_ledgers(self):
        import extract_stats
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            live, staged = directory / "live", directory / "staged"
            live.mkdir()
            original = live / "faction.json"
            original.write_bytes(b'{"proposal": true}\n')
            def build(model, faction):
                self.assertEqual(extract_stats.OUT, live)
                self.assertEqual(original.read_bytes(), b'{"proposal": true}\n')
                return {"faction": {"sections": {}}}, {"faction": {"derived": True}}
            with patch.object(extract_stats, "OUT", live), patch.object(extract_stats, "Model"), \
                    patch.object(extract_stats, "build_both", side_effect=build), \
                    patch.object(extract_stats, "model_constants", return_value={}), \
                    patch.object(sys, "argv", ["extract_stats.py", "--output-dir", str(staged)]), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(extract_stats.main(), 0)
            self.assertEqual(original.read_bytes(), b'{"proposal": true}\n')
            self.assertTrue((staged / "faction.json").exists())
            self.assertTrue((staged / "derived/faction.json").exists())
            self.assertTrue((staged / "derived/_model.json").exists())

    def test_check_and_output_directory_are_incompatible(self):
        import extract_stats
        with patch.object(sys, "argv", ["extract_stats.py", "--check", "--output-dir", "unused"]), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            extract_stats.main()
        self.assertEqual(error.exception.code, 2)

    def test_rollback_preserves_concurrent_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "file"
            path.write_bytes(b"original")
            transaction = Transaction({path: b"original"})
            transaction.write(path, b"ours")
            path.write_bytes(b"someone else")
            self.assertEqual(transaction.rollback(), [str(path)])
            self.assertEqual(path.read_bytes(), b"someone else")


class SuperweaponLockTests(unittest.TestCase):
    """The second superweapon lock must refuse an EDIT and pass an untouched row.

    ⛔ It did neither. `changed_paths` is a generator FUNCTION, so `and changed_paths(...)` tested
    a generator OBJECT — always truthy — and the lock fired on every superweapon row whether the
    ledger had touched it or not. `apply_balance --faction tiberiandawn_gdi` therefore reported
    `REFUSED: 1 problem(s)` on a tree with zero pending edits, and every faction that ships a
    superweapon was permanently unappliable. A guard that cannot pass is an outage, not a guard.
    """

    # Borrowed rather than INHERITED: subclassing `ApplyTests` would re-run all 37 of its tests
    # against a ledger whose only unit is a superweapon, and 20 of them would fail for a reason
    # that has nothing to do with what is under test here.
    write_ledgers = ApplyTests.write_ledgers
    run_apply = ApplyTests.run_apply
    successful_child = ApplyTests.successful_child
    change_cost = ApplyTests.change_cost

    def setUp(self):
        ApplyTests.setUp(self)
        unit = self.fresh["test"]["sections"]["infantry"]["unit"]
        unit["prerequisites"] = ["~techlevel.superweapons"]
        self.desired = copy.deepcopy(self.fresh)
        self.write_ledgers()

    def test_untouched_superweapon_does_not_refuse(self):
        code, text, _ = self.run_apply()
        self.assertEqual(code, 0, text)
        self.assertNotIn("SUPERWEAPON", text)
        self.assertIn("DRY RUN: 0", text)

    def test_edited_superweapon_is_refused(self):
        self.change_cost()
        code, text, _ = self.run_apply()
        self.assertNotEqual(code, 0)
        self.assertIn("SUPERWEAPON", text)
        self.assertEqual(self.yaml.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
