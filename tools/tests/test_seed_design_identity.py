"""Regression tests for seed_design.py — CABAL historical actor-id reuse,
two-phase target-conflict preflight, --dry-run zero-write guarantee, header
scan, and actor-ID alias wiring.

Identity provenance: commit 833f7123e9978918730bbcf8ce716dfed5d9dc2d (the old
cabal_widow definition was removed and the id replaced under the former
cabal_legion) and commit 86eee6bcadb5cbe567ec1f470eb5617d5bb9c713 (six CABAL
aircraft actor ids merged their internal underscores).

EVERY behavioral test runs seed_design.run() against TEMP fixtures with
explicit paths. The default main() (real repository paths) is NEVER invoked
here; main() is only exercised with a mocked run() to prove argument wiring.
The single real-file test is read-only (name_map.yaml contents).
"""
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import seed_design as sd

COMMIT = "833f7123e9978918730bbcf8ce716dfed5d9dc2d"
WITHHELD_SECTION = "## Withheld legacy rows (historical actor-id reuse — needs a maintainer decision, NOT auto-seeded)"
CONFLICT_SECTION = "## Conflicting source rows (ALL workbook-derived values withheld for the target)"
UNRESOLVED_SECTION = "## Unresolved legacy rows (missing actor ID or unmatched display name — extend name_map.yaml)"
NO_JUDGMENT_SECTION = "## Ledger units with no design judgments populated"
UNRESOLVED_MSG = "(missing actor ID — unresolved identity)"

SIX_ALIASES = [
    ("cabal_overkill_gunship", "cabal_overkillgunship"),
    ("cabal_hunter_drone_carrier", "cabal_hunterdronecarrier"),
    ("cabal_hunter_drone", "cabal_hunterdrone"),
    ("cabal_orb_drone", "cabal_orbdrone"),
    ("cabal_cyborg_assassin", "cabal_cyborgassassin"),
    ("cabal_repair_drone", "cabal_repairdrone"),
]


def cabal_row(name, actor, special, unit_class, tier, cost):
    # CABAL columns: A mod, B name, C actor, K special, L unit class, M tier, R cost
    return ["TS", name, actor, None, None, None, None, None, None, None,
            special, unit_class, tier, None, None, None, None, cost]


def type_row(name, hp, special, unit_class, tier, cost):
    # type tabs: B name, D hp, K special, L unit class, M tier, S cost
    return [None, name, None, hp, None, None, None, None, None, None,
            special, unit_class, tier, None, None, None, None, None, cost]


DUMMY = [None, None, None, None]  # verbatim sheet row 1 (scanner starts at 2)


def build_workbook(path, cabal_rows, extra_sheets=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CABAL"
    ws.append(["mod", "name", "actor"] + [f"col{i}" for i in range(4, 19)])
    for row in cabal_rows:
        ws.append(row)
    for title, rows in (extra_sheets or {}).items():
        sheet = wb.create_sheet(title)
        for row in rows:  # verbatim; index 0 lands on sheet row 1
            sheet.append(row)
    wb.save(path)
    wb.close()


def snapshot(root: pathlib.Path):
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = p.read_bytes()
    return out


class SeedDesignIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.ledger = self.root / "docs/balance"
        self.ledger.mkdir(parents=True)
        self.legacy = self.root / "cameo_armor_system.xlsx"
        self.report = self.ledger / "discrepancies.md"
        self.namemap = self.ledger / "name_map.yaml"

    # --- fixtures -------------------------------------------------------

    def write_ledger(self, doc, name="test"):
        (self.ledger / f"{name}.json").write_text(
            json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8", newline="\n")

    def read_ledger(self, name="test"):
        return json.loads((self.ledger / f"{name}.json").read_text(encoding="utf-8"))

    def write_namemap(self, text):
        self.namemap.write_text(text, encoding="utf-8", newline="\n")

    def unit(self, name, cost, design=None):
        u = {"name": name, "cost": {"v": cost}}
        if design:
            u["design"] = dict(design)
        return u

    def cabal_ledger(self, widow_design=None, avatar_design=None):
        vehicles = {
            "cabal_widow": self.unit("Widow", 3500, widow_design),
            "cabal_avatar": self.unit("Avatar", 500, avatar_design),
        }
        return {"schema": 2, "ledger": "test", "sections": {"vehicles": vehicles}}

    def standard_cabal_rows(self):
        # row 2 = unrelated valid row, row 3 = obsolete Widow (old HighTechTank
        # values), row 4 = dead Legion row (today's sheet B16/C16/M16 analog).
        return [
            cabal_row("Avatar", "cabal_avatar", 1.0, 3.0, 2.0, 500),
            cabal_row("Widow", "cabal_widow", 4.0, 2.0, 1.0, 3000),
            cabal_row("Legion", "cabal_legion", 3.0, 2.0, 0.5, 3500),
        ]

    def make_workbook(self, cabal_rows=None, extra_sheets=None):
        build_workbook(self.legacy, self.standard_cabal_rows()
                       if cabal_rows is None else cabal_rows, extra_sheets)

    def run_seed(self, dry_run=False):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = sd.run(dry_run=dry_run, ledger_dir=self.ledger,
                        legacy_path=self.legacy, name_map_path=self.namemap,
                        report_path=self.report)
        return rc, out.getvalue()

    def design_of(self, actor, section=None):
        sections = self.read_ledger()["sections"]
        if section:
            return sections.get(section, {}).get(actor, {}).get("design")
        for sec in sections.values():
            if actor in sec:
                return sec[actor].get("design")
        return {}

    # --- 1. Widow special/unit_class/tier withheld, fallback distinct ----

    def test_widow_legacy_values_withheld_and_reported(self):
        self.write_ledger(self.cabal_ledger())
        self.make_workbook()
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_widow")
        self.assertIsNone(d.get("special"))
        self.assertIsNone(d.get("unit_class"))
        self.assertIsNone(d.get("tech_tier"))
        # ordinary section fallback is NOT withheld (not a legacy numeric import)
        self.assertEqual(d.get("category"), "Vehicles")
        self.assertEqual(d.get("subtype"), "Unclassified")
        report = self.report.read_text(encoding="utf-8")
        self.assertIn(WITHHELD_SECTION, report)
        self.assertIn(COMMIT, report)
        self.assertIn("CABAL row 3 (C3=`cabal_widow`, B3=`Widow`)", report)
        self.assertIn(f"CABAL: `Legion` -> `cabal_legion` {UNRESOLVED_MSG}", report)
        # the obsolete row must not even produce a cost mismatch (other definition)
        self.assertNotIn("yaml cost 3500 vs legacy sheet 3000", report)
        self.assertIn("withheld 1", out)

    # --- 2. existing tier1 untouched -------------------------------------

    def test_existing_tier1_unchanged(self):
        self.write_ledger(self.cabal_ledger(widow_design={"tech_tier": 1.0}))
        self.make_workbook()
        rc, _ = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_widow")
        self.assertEqual(d.get("tech_tier"), 1.0)
        self.assertIsNone(d.get("special"))
        self.assertIsNone(d.get("unit_class"))

    # --- 3. Legion stays unresolved --------------------------------------

    def test_legion_row_stays_unresolved(self):
        self.write_ledger(self.cabal_ledger())
        self.make_workbook()
        rc, _ = self.run_seed()
        self.assertEqual(rc, 0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn(UNRESOLVED_SECTION, report)
        self.assertIn(f"CABAL: `Legion` -> `cabal_legion` {UNRESOLVED_MSG}", report)
        for p in self.ledger.glob("*.json"):
            self.assertNotIn("cabal_legion", p.read_text(encoding="utf-8"))
            self.assertNotIn("0.5", p.read_text(encoding="utf-8"))

    # --- 4. unrelated valid CABAL row still fills (negative counterpart) -

    def test_unrelated_cabal_row_fills_in_write_mode(self):
        self.write_ledger(self.cabal_ledger())
        self.make_workbook()
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_avatar")
        self.assertEqual(d.get("special"), 1.0)
        self.assertEqual(d.get("unit_class"), 3.0)
        self.assertEqual(d.get("tech_tier"), 2.0)
        # direct/mapped are raw resolution counts (unresolved rows included),
        # never presented as imports
        self.assertIn("matched 1 legacy rows across 1 unique targets", out)
        self.assertIn("applied 7 design fields", out)
        self.assertIn("resolution: 2 by CABAL actor id", out)
        self.assertIn("withheld 1", out)

    # --- 5. dry-run writes nothing, shows real proposals ------------------

    def test_dry_run_zero_writes_with_existing_report(self):
        self.write_ledger(self.cabal_ledger())
        self.make_workbook()
        self.report.write_text("SENTINEL-REPORT\n", encoding="utf-8", newline="\n")
        before = snapshot(self.root)
        rc, out = self.run_seed(dry_run=True)
        self.assertEqual(rc, 0)
        self.assertEqual(snapshot(self.root), before)
        # honest labelling — no seeded/written claim
        self.assertNotIn("seeded 1 units", out)
        self.assertIn("DRY-RUN: nothing seeded, nothing written", out)
        self.assertIn("NO ledger, workbook or report was written", out)
        self.assertIn("would fill 7 design fields", out)
        self.assertIn("## Design import diagnostics (10 records", out)
        # actual proposals with coordinates, source, field, values, disposition
        self.assertIn("- CABAL row 2: name `Avatar`, actor `cabal_avatar` — "
                      "design.tech_tier: <missing> -> 2.0 [propose fill (legacy sheet)]", out)
        self.assertIn("- CABAL row 3: name `Widow`, actor `cabal_widow` — "
                      "design.tech_tier: <missing> -> 1.0 "
                      "[WITHHELD (historical actor-id reuse — see withheld section)]", out)
        self.assertIn(COMMIT, out)
        self.assertIn("- ledger section `vehicles`: actor `cabal_widow` — "
                      "design.category: <missing> -> Vehicles "
                      "[propose fallback (section-derived — NOT a legacy numeric import)]", out)
        self.assertIn(f"CABAL: `Legion` -> `cabal_legion` {UNRESOLVED_MSG}", out)
        self.assertEqual(self.report.read_text(encoding="utf-8"), "SENTINEL-REPORT\n")

    def test_dry_run_creates_no_report_when_absent(self):
        self.write_ledger(self.cabal_ledger())
        self.make_workbook()
        before = snapshot(self.root)
        rc, out = self.run_seed(dry_run=True)
        self.assertEqual(rc, 0)
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse(self.report.exists())
        self.assertIn("propose fill (legacy sheet)", out)

    # --- 6. name_map display-alias behaviors unchanged ---------------------

    def test_name_map_behaviors_unchanged(self):
        doc = {"schema": 2, "ledger": "test", "sections": {"infantry": {
            "cabal_ghost": self.unit("Ghost", 300),
            "cabal_commando": self.unit("Commando", 400),
            "cabal_ranger": self.unit("Ranger", 500),
        }}}
        self.write_ledger(doc)
        self.write_namemap("Legacy Ghost: cabal_ghost\n"
                           "Legacy Commando: cabal_commando\n"
                           "Legacy Ranger: cabal_ranger\n"
                           "Phantom: -\n")
        infantry = [DUMMY,
                    type_row("Legacy Ghost", 100, 1.0, 1.0, 1.0, 300),
                    type_row("Legacy Commando", 120, 2.0, 1.0, 2.0, 400),
                    type_row("Legacy Ranger", 140, 2.0, 2.0, 2.0, 500),
                    type_row("Phantom", 160, 3.0, 1.0, 3.0, 600),
                    type_row("Unheard Unit", 180, 1.0, 2.0, 3.0, 700)]
        self.make_workbook(cabal_rows=[], extra_sheets={"Infantry": infantry})
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        sections = self.read_ledger()["sections"]["infantry"]
        self.assertEqual(sections["cabal_ghost"]["design"]["special"], 1.0)
        self.assertEqual(sections["cabal_commando"]["design"]["tech_tier"], 2.0)
        self.assertEqual(sections["cabal_ranger"]["design"]["unit_class"], 2.0)
        self.assertEqual(sections["cabal_ghost"]["design"]["category"], "Infantry")
        self.assertIn("matched 3 legacy rows across 3 unique targets", out)
        self.assertIn("applied 15 design fields", out)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("Infantry: `Unheard Unit`", report)
        self.assertNotIn("Phantom", report)

    # --- 7. Excel lock refuses before writes (both modes) ------------------

    def test_lock_refuses_before_writes(self):
        self.write_ledger(self.cabal_ledger())
        self.make_workbook()
        (self.root / "~$cameo_armor_system.xlsx").write_text("lock", encoding="utf-8")
        before = snapshot(self.root)
        rc, out = self.run_seed()
        self.assertEqual(rc, 2)
        self.assertIn("~$ lock", out)
        rc, out = self.run_seed(dry_run=True)
        self.assertEqual(rc, 2)
        self.assertIn("~$ lock", out)
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse(self.report.exists())

    # --- 8. main() argument wiring (run mocked — repo never touched) -------

    def test_main_arg_wiring(self):
        with patch.object(sd, "run") as runmock:
            self.assertEqual(sd.main(["--dry-run"]), runmock.return_value)
            runmock.assert_called_once_with(dry_run=True)
        with patch.object(sd, "run") as runmock:
            self.assertEqual(sd.main([]), runmock.return_value)
            runmock.assert_called_once_with(dry_run=False)
        with patch.object(sd, "run") as runmock:
            self.assertEqual(sd.main(["--bogus"]), 2)
            runmock.assert_not_called()

    # === revision 2: two-phase target-conflict preflight ===================

    def gi_fixture(self, design=None):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"infantry": {
            "ra2_allies_gi": self.unit("G.I.", 300, design)}}})
        self.make_workbook(cabal_rows=[], extra_sheets={"Infantry": [
            DUMMY,
            [None, "Scout Infantry", None, "HP"],                      # row 2 first-group header
            type_row("G.I.", 300, 1.25, 1.0, 1.0, 300),                # row 18 analog
            type_row("G.I.(deployed)", 400, 1.0, 1.0, 1.0, 300),       # row 19 analog
        ]})

    def test_gi_conflict_withholds_all_legacy_fields(self):
        self.gi_fixture()
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("ra2_allies_gi")
        for field in ("special", "unit_class", "tech_tier"):
            self.assertIsNone(d.get(field), f"{field} must stay unfilled on conflict")
        # section fallback is ordinary and distinct from the withheld rows
        self.assertEqual(d.get("category"), "Infantry")
        self.assertEqual(d.get("subtype"), "Unclassified")
        report = self.report.read_text(encoding="utf-8")
        self.assertIn(CONFLICT_SECTION, report)
        self.assertIn("`ra2_allies_gi` design.special: Infantry row 3 `G.I.`=1.25 "
                      "vs Infantry row 4 `G.I.(deployed)`=1.0", report)
        self.assertIn("conflicts 1", out)
        # B2 header honored but never counted as a unit
        self.assertIn("matched 2 legacy rows across 1 unique targets", out)
        self.assertIn("applied 2 design fields", out)  # fallback only — conflict withheld
        self.assertNotIn("Scout Infantry", report)

    def test_conflict_still_reported_with_existing_ledger_values(self):
        self.gi_fixture(design={"special": 1.25, "unit_class": 1.0, "tech_tier": 1.0})
        rc, _ = self.run_seed()
        self.assertEqual(rc, 0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn(CONFLICT_SECTION, report)
        self.assertIn("`ra2_allies_gi` design.special: Infantry row 3 `G.I.`=1.25 "
                      "vs Infantry row 4 `G.I.(deployed)`=1.0", report)
        d = self.design_of("ra2_allies_gi")
        self.assertEqual(d.get("special"), 1.25)  # existing values untouched
        self.assertEqual(d.get("tech_tier"), 1.0)

    def test_cross_cabal_and_type_tab_conflict(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_x": self.unit("Exunit", 500)}}})
        self.make_workbook(
            cabal_rows=[cabal_row("Exunit", "cabal_x", 1.0, 1.0, 1.0, 500)],
            extra_sheets={"Infantry": [DUMMY, type_row("Exunit", 100, 2.0, 1.0, 1.0, 500)]})
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("`cabal_x` design.special: CABAL row 2 `Exunit`=1.0 "
                      "vs Infantry row 2 `Exunit`=2.0", report)
        d = self.design_of("cabal_x")
        self.assertIsNone(d.get("special"))
        self.assertEqual(d.get("category"), "Vehicles")  # fallback still ordinary
        self.assertIn("conflicts 1", out)

    def test_two_aliases_to_same_target_conflict(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_x": self.unit("Xunit", 300)}}})
        self.write_namemap("Legacy Alpha: cabal_x\nLegacy Beta: cabal_x\n")
        self.make_workbook(cabal_rows=[], extra_sheets={"Infantry": [
            DUMMY,
            type_row("Legacy Alpha", 100, 1.0, 1.0, 1.0, 100),
            type_row("Legacy Beta", 200, 2.0, 1.0, 1.0, 200)]})
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("`cabal_x` design.special: Infantry row 2 `Legacy Alpha`=1.0 "
                      "vs Infantry row 3 `Legacy Beta`=2.0", report)
        self.assertIsNone(self.design_of("cabal_x").get("special"))
        self.assertIn("conflicts 1", out)

    def test_identical_duplicates_accepted(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_x": self.unit("Dup", 500)}}})
        self.make_workbook(cabal_rows=[
            cabal_row("Dup", "cabal_x", 1.0, 2.0, 3.0, 500),
            cabal_row("Dup", "cabal_x", 1.0, 2.0, 3.0, 500)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_x")
        self.assertEqual(d.get("special"), 1.0)
        self.assertEqual(d.get("unit_class"), 2.0)
        self.assertEqual(d.get("tech_tier"), 3.0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("## Conflicting source rows", report)
        self.assertIn("- none", report)
        self.assertIn("conflicts 0", out)

    def test_complementary_partials_accepted(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_x": self.unit("Part", 500)}}})
        self.make_workbook(cabal_rows=[
            cabal_row("Part", "cabal_x", 1.0, None, None, 500),
            cabal_row("Part", "cabal_x", None, 2.0, 3.0, 500)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_x")
        self.assertEqual(d.get("special"), 1.0)
        self.assertEqual(d.get("unit_class"), 2.0)
        self.assertEqual(d.get("tech_tier"), 3.0)
        self.assertIn("conflicts 0", out)

    def test_zero_vs_none_accepted_and_zero_vs_one_conflict(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_zero": self.unit("Zero", 100),
            "cabal_conf": self.unit("Conf", 200)}}})
        self.make_workbook(cabal_rows=[
            cabal_row("Zero", "cabal_zero", 0, 1.0, 1.0, 100),
            cabal_row("Zero", "cabal_zero", None, 1.0, 1.0, 100),
            cabal_row("Conf", "cabal_conf", 0, 1.0, 1.0, 200),
            cabal_row("Conf", "cabal_conf", 1, 1.0, 1.0, 200)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        self.assertEqual(self.design_of("cabal_zero").get("special"), 0.0)  # 0 is populated
        self.assertIsNone(self.design_of("cabal_conf").get("special"))      # 0 vs 1 conflicts
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("`cabal_conf` design.special: CABAL row 4 `Conf`=0.0 "
                      "vs CABAL row 5 `Conf`=1.0", report)
        self.assertIn("conflicts 1", out)

    def test_reversed_source_row_order_same_result(self):
        rows = [cabal_row("Part", "cabal_x", 1.0, None, None, 500),
                cabal_row("Part", "cabal_x", None, 2.0, 3.0, 500)]
        doc = {"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_x": self.unit("Part", 500)}}}
        results = []
        for variant in (rows, list(reversed(rows))):
            self.write_ledger(doc)
            self.make_workbook(cabal_rows=variant)
            rc, _ = self.run_seed()
            self.assertEqual(rc, 0)
            results.append(self.design_of("cabal_x"))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0].get("special"), 1.0)
        self.assertEqual(results[0].get("tech_tier"), 3.0)

    def test_conflict_target_does_not_block_unrelated_target(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_x": self.unit("Bad", 100),
            "cabal_ok": self.unit("Good", 200)}}})
        self.make_workbook(cabal_rows=[
            cabal_row("Bad", "cabal_x", 1.0, 1.0, 1.0, 100),
            cabal_row("Bad", "cabal_x", 2.0, 1.0, 1.0, 100),
            cabal_row("Good", "cabal_ok", 1.0, 2.0, 3.0, 200)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        self.assertIsNone(self.design_of("cabal_x").get("special"))
        d = self.design_of("cabal_ok")
        self.assertEqual(d.get("special"), 1.0)
        self.assertEqual(d.get("tech_tier"), 3.0)
        self.assertIn("conflicts 1", out)

    def test_differing_costs_alone_accepted(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_y": self.unit("Costly", 500)}}})
        self.make_workbook(cabal_rows=[
            cabal_row("Costly", "cabal_y", 1.0, 2.0, 3.0, 500),
            cabal_row("Costly", "cabal_y", 1.0, 2.0, 3.0, 600)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_y")
        self.assertEqual(d.get("special"), 1.0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("`cabal_y`: yaml cost 500 vs legacy sheet 600 (CABAL)", report)
        self.assertIn("- none", report.split("## Conflicting source rows")[1].split("##")[0])
        self.assertIn("conflicts 0", out)

    def test_conflicting_category_subtype_withheld(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_dual": self.unit("Dualunit", 100)}}})
        self.write_namemap("Dual Role: cabal_dual\n")
        self.make_workbook(cabal_rows=[], extra_sheets={
            "Infantry": [DUMMY, type_row("Dual Role", 100, 1.0, 1.0, 1.0, 100)],
            "Vehicles": [DUMMY, type_row("Dual Role", 200, 1.0, 1.0, 1.0, 200)]})
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("`cabal_dual` design.category: Infantry row 2 `Dual Role`=Infantry "
                      "vs Vehicles row 2 `Dual Role`=Vehicles", report)
        d = self.design_of("cabal_dual")
        self.assertIsNone(d.get("special"))  # whole target withheld
        self.assertEqual(d.get("category"), "Vehicles")  # section fallback only

    def test_dry_run_shows_conflict_and_writes_nothing(self):
        self.gi_fixture()
        before = snapshot(self.root)
        rc, out = self.run_seed(dry_run=True)
        self.assertEqual(rc, 0)
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse(self.report.exists())
        self.assertIn("`ra2_allies_gi` design.special: Infantry row 3 `G.I.`=1.25 "
                      "vs Infantry row 4 `G.I.(deployed)`=1.0", out)
        self.assertIn("1 conflict targets", out)
        self.assertIn("NO ledger, workbook or report was written", out)

    # === revision 2: first-group header scan ===============================

    def test_header_row2_recognized_not_counted(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"infantry": {
            "scout1": self.unit("Scout", 50)}}})
        self.make_workbook(cabal_rows=[], extra_sheets={"Infantry": [
            DUMMY,
            [None, "Scout Infantry", None, "HP"],                 # row 2 header (D2='HP')
            type_row("Scout", 50, 1.0, 1.0, 1.0, 50)]})           # row 3 data
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.read_ledger()["sections"]["infantry"]["scout1"]["design"]
        self.assertEqual(d.get("special"), 1.0)
        self.assertEqual(d.get("subtype"), "Scout Infantry")
        self.assertEqual(d.get("category"), "Infantry")
        self.assertIn("matched 1 legacy rows", out)
        self.assertIn("applied 5 design fields", out)
        self.assertIn("conflicts 0", out)

    def test_later_header_switches_subtype(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"infantry": {
            "t1": self.unit("Early", 100), "t2": self.unit("Late", 200)}}})
        self.make_workbook(cabal_rows=[], extra_sheets={"Infantry": [
            DUMMY,
            type_row("Early", 100, 1.0, 1.0, 1.0, 100),
            [None, "Elite", None, "HP"],
            type_row("Late", 200, 2.0, 2.0, 2.0, 200)]})
        rc, _ = self.run_seed()
        self.assertEqual(rc, 0)
        sections = self.read_ledger()["sections"]["infantry"]
        self.assertEqual(sections["t1"]["design"]["subtype"], "Unclassified")
        self.assertEqual(sections["t2"]["design"]["subtype"], "Elite")

    def test_blank_row2_skipped(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"infantry": {
            "solo": self.unit("Solo", 100)}}})
        self.make_workbook(cabal_rows=[], extra_sheets={"Infantry": [
            DUMMY, [None, None, None, None], type_row("Solo", 100, 1.0, 1.0, 1.0, 100)]})
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.read_ledger()["sections"]["infantry"]["solo"]["design"]
        self.assertEqual(d.get("special"), 1.0)
        self.assertEqual(d.get("subtype"), "Unclassified")
        self.assertIn("matched 1 legacy rows", out)
        self.assertIn("applied 5 design fields", out)

    def test_defense_header3_recognized(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"defenses": {
            "tower": self.unit("Tower", 500)}}})
        self.make_workbook(cabal_rows=[], extra_sheets={"Defenses": [
            DUMMY, [None, None, None, None],
            [None, "Basic Defense", None, "HP"],                  # row 3 header (Defenses layout)
            type_row("Tower", 500, 1.0, 1.0, 1.0, 500)]})         # row 4 data
        rc, _ = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.read_ledger()["sections"]["defenses"]["tower"]["design"]
        self.assertEqual(d.get("special"), 1.0)
        self.assertEqual(d.get("subtype"), "Basic Defense")

    # === revision 2: no-design-judgment predicate ==========================

    def test_no_design_judgments_label_and_predicate(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"infantry": {
            "u_none": self.unit("NoJudg", 500),
            "u_tier0": self.unit("Tier0", 10, design={"tech_tier": 0.0})}}})
        self.make_workbook(cabal_rows=[])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn(f"{NO_JUDGMENT_SECTION} (1)", report)
        self.assertIn("- `u_none`", report)          # real cost 500 + fallback metadata, 3 missing
        self.assertNotIn("`u_tier0`", report)        # tech_tier 0.0 counts as populated
        self.assertNotIn("never priced in the legacy sheet", report)
        self.assertNotIn("Combat units", report)
        self.assertIn("no design judgments 1", out)

    # === revision 2: CABAL actor-ID alias wiring ===========================

    def test_direct_id_wins_over_explicit_mapping(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_avatar": self.unit("Avatar", 500),
            "cabal_other": self.unit("Other", 999)}}})
        self.write_namemap("cabal_avatar: cabal_other\n")
        self.make_workbook(cabal_rows=[cabal_row("Avatar", "cabal_avatar", 1.0, 2.0, 3.0, 500)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_avatar")  # original id kept, filled from its own row
        self.assertEqual(d.get("special"), 1.0)
        self.assertEqual(d.get("unit_class"), 2.0)
        self.assertEqual(d.get("tech_tier"), 3.0)
        other = self.design_of("cabal_other")
        for field in ("special", "unit_class", "tech_tier"):
            self.assertIsNone(other.get(field))
        self.assertIn("aliases 0", out)

    def test_unknown_id_without_alias_stays_unresolved(self):
        self.write_ledger(self.cabal_ledger())
        self.make_workbook(cabal_rows=[cabal_row("Ghost", "cabal_nope", 1.0, 1.0, 1.0, 100)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn(f"CABAL: `Ghost` -> `cabal_nope` {UNRESOLVED_MSG}", report)
        self.assertIn("aliases 0", out)
        self.assertNotIn("cabal_nope", self.read_ledger_text())

    def test_missing_alias_target_stays_unresolved(self):
        self.write_ledger(self.cabal_ledger())
        self.write_namemap("cabal_ghostid: cabal_absent\n")
        self.make_workbook(cabal_rows=[cabal_row("Ghostid", "cabal_ghostid", 1.0, 1.0, 1.0, 100)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn(f"CABAL: `Ghostid` -> `cabal_ghostid` {UNRESOLVED_MSG}", report)
        self.assertIn("aliases 0", out)
        self.assertNotIn("cabal_ghostid", self.read_ledger_text())

    def test_alias_plus_direct_conflict_withholds_target(self):
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_new": self.unit("Newname", 300)}}})
        self.write_namemap("cabal_old: cabal_new\n")
        self.make_workbook(cabal_rows=[
            cabal_row("Newname", "cabal_new", 1.0, 1.0, 1.0, 300),
            cabal_row("Oldname", "cabal_old", 2.0, 1.0, 1.0, 300)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("CABAL row 3 (C3=`cabal_old`) — actor-ID alias -> `cabal_new`", report)
        self.assertIn("`cabal_new` design.special: CABAL row 2 `Newname`=1.0 "
                      "vs CABAL row 3 `Oldname`=2.0", report)
        self.assertIsNone(self.design_of("cabal_new").get("special"))
        self.assertIn("aliases 1", out)
        self.assertIn("conflicts 1", out)

    def test_six_real_registry_alias_targets(self):
        ledger = {"schema": 2, "ledger": "test", "sections": {"aircraft": {
            new: self.unit(f"Unit{i}", 100 + i)
            for i, (_, new) in enumerate(SIX_ALIASES)}}}
        self.write_ledger(ledger)
        self.write_namemap("".join(f"{old}: {new}\n" for old, new in SIX_ALIASES))
        rows = [cabal_row(old, old, 1.0, 2.0, 3.0, 100 + i)
                for i, (old, _) in enumerate(SIX_ALIASES)]
        rows.append(cabal_row("Legion", "cabal_legion", 3.0, 2.0, 0.5, 3500))
        self.make_workbook(cabal_rows=rows)
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        # 7 raw missing legacy ids -> 6 alias matches + 1 unresolved Legion
        self.assertIn("aliases 6", out)
        self.assertIn("unresolved 1", out)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn(f"CABAL: `Legion` -> `cabal_legion` {UNRESOLVED_MSG}", report)
        for i, (old, new) in enumerate(SIX_ALIASES):
            self.assertIn(f"CABAL row {i + 2} (C{i + 2}=`{old}`) — actor-ID alias -> `{new}`", report)
            d = self.read_ledger()["sections"]["aircraft"][new]["design"]
            self.assertEqual(d.get("special"), 1.0)
            self.assertEqual(d.get("unit_class"), 2.0)
            self.assertEqual(d.get("tech_tier"), 3.0)
        self.assertNotIn("cabal_legion", self.read_ledger_text())

    def test_real_name_map_unique_normalized_keys_and_nine_entries(self):
        # read-only check against the real committed name_map.yaml
        keys = sd.load_name_map(ROOT / "docs/balance/name_map.yaml")
        self.assertEqual(len(keys), len(set(keys)), "normalized keys must stay unique")
        for k in ("terranmarine", "ordostankdestroyer", "ixiangunturret"):
            self.assertIn(k, keys)
        for old, _new in SIX_ALIASES:
            self.assertIn(sd.norm(old), keys)

    # === revision 3: quarantined TARGET ids authoritative on every path ===

    def widowed_ledger(self, widow_design=None):
        return {"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_widow": self.unit("Widow", 3500, widow_design),
            "cabal_ok": self.unit("OKunit", 200)}},
            # keep the ledger small: only these two combat units
        }

    def test_type_tab_unique_name_to_widow_blocked(self):
        self.write_ledger(self.widowed_ledger())
        # NO original CABAL Widow row at all — the blocked TARGET must still hold
        self.make_workbook(cabal_rows=[cabal_row("OKunit", "cabal_ok", 1.0, 2.0, 3.0, 200)],
                           extra_sheets={"Infantry": [
                               DUMMY, type_row("Widow", 3000, 4.0, 2.0, 1.0, 3000)]})
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_widow")
        for field in ("special", "unit_class", "tech_tier"):
            self.assertIsNone(d.get(field))
        self.assertEqual(d.get("category"), "Vehicles")     # section fallback stays separate
        self.assertEqual(d.get("subtype"), "Unclassified")
        ok = self.design_of("cabal_ok")                      # unrelated valid target works
        self.assertEqual(ok.get("special"), 1.0)
        self.assertEqual(ok.get("tech_tier"), 3.0)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("Infantry row 2: name `Widow`, actor `cabal_widow` — "
                      "special/unit_class/tier withheld from automatic seeding "
                      "(quarantined target id): commit " + COMMIT, report)
        self.assertIn("withheld 1", out)

    def test_explicit_alias_to_widow_blocked(self):
        self.write_ledger(self.widowed_ledger())
        self.write_namemap("Old Widow: cabal_widow\n")
        self.make_workbook(cabal_rows=[], extra_sheets={"Infantry": [
            DUMMY, type_row("Old Widow", 3000, 4.0, 2.0, 1.0, 3000)]})
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_widow")
        for field in ("special", "unit_class", "tech_tier"):
            self.assertIsNone(d.get(field))
        self.assertEqual(d.get("category"), "Vehicles")
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("Infantry row 2: name `Old Widow`, actor `cabal_widow` — "
                      "special/unit_class/tier withheld from automatic seeding "
                      "(quarantined target id): commit " + COMMIT, report)

    def test_cabal_actor_alias_to_widow_blocked(self):
        self.write_ledger(self.widowed_ledger())
        self.write_namemap("cabal_oldwidow: cabal_widow\n")
        self.make_workbook(cabal_rows=[cabal_row("OldWidow", "cabal_oldwidow",
                                                 4.0, 2.0, 1.0, 3000)])
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_widow")
        for field in ("special", "unit_class", "tech_tier"):
            self.assertIsNone(d.get(field))
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("CABAL row 2: name `OldWidow`, actor `cabal_oldwidow` -> target "
                      "`cabal_widow` (actor-ID alias) — special/unit_class/tier withheld "
                      "from automatic seeding (quarantined target id): commit " + COMMIT, report)
        self.assertIn("CABAL row 2 (C2=`cabal_oldwidow`) — actor-ID alias -> `cabal_widow`", report)

    def test_blocked_target_keeps_existing_judgments(self):
        self.write_ledger(self.widowed_ledger(widow_design={"tech_tier": 1.0}))
        self.write_namemap("Old Widow: cabal_widow\n")
        self.make_workbook(cabal_rows=[], extra_sheets={"Infantry": [
            DUMMY, type_row("Old Widow", 3000, 4.0, 2.0, 1.0, 3000)]})
        rc, _ = self.run_seed()
        self.assertEqual(rc, 0)
        d = self.design_of("cabal_widow")
        self.assertEqual(d.get("tech_tier"), 1.0)   # existing judgments untouched
        self.assertIsNone(d.get("special"))
        self.assertIsNone(d.get("unit_class"))

    # === revision 3: truthful apply counts =================================

    def test_no_positive_apply_count_for_kept_or_withheld_records(self):
        full = {"special": 1.0, "unit_class": 1.0, "tech_tier": 1.0,
                "category": "Vehicles", "subtype": "Unclassified"}
        self.write_ledger({"schema": 2, "ledger": "test", "sections": {"vehicles": {
            "cabal_keep": self.unit("Keeper", 100, design=full),
            "cabal_hold": self.unit("Holder", 200, design=full)}}})
        self.make_workbook(cabal_rows=[
            cabal_row("Keeper", "cabal_keep", 1.0, 1.0, 1.0, 100),   # all kept
            cabal_row("Holder", "cabal_hold", 1.0, 1.0, 1.0, 200),   # conflicting pair:
            cabal_row("Holder", "cabal_hold", 2.0, 1.0, 1.0, 200)])  # withheld only
        before = snapshot(self.root)
        rc, out = self.run_seed(dry_run=True)
        self.assertEqual(rc, 0)
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse(self.report.exists())
        self.assertIn("matched 3 legacy rows across 2 unique targets", out)
        self.assertIn("would fill 0 design fields", out)   # no real transitions exist
        self.assertNotIn("would fill 1 design fields", out)
        self.assertIn("1 conflict targets", out)
        self.assertIn("NO ledger, workbook or report was written", out)
        rc, out = self.run_seed()
        self.assertEqual(rc, 0)
        self.assertIn("applied 0 design fields", out)
        self.assertIn("conflicts 1", out)

    def read_ledger_text(self):
        return (self.ledger / "test.json").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
