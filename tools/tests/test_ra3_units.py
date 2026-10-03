"""Bounded RA3 base-roster extractor — mechanics tests on SYNTHETIC FIXTURES ONLY.

Nothing in this module reads the real EA source tree; every fixture is a tiny
synthetic AssetDeclaration written into a temp directory. The real tree is
exercised only by running the tool by hand against the external checkout.

Covers, per the task order: XML namespace handling, local vs inherited body/cost,
weapon mode conditions, missing/duplicate ids, unsupported expressions, entity/path
safety (escape + cycle + case collision), determinism, and economic exclusion
(MCV/harvester manual-review-only; structures/props/eggs/campaign excluded).
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
import extract_ra3_units as era  # noqa: E402

XMLDECL = '<?xml version="1.0" encoding="utf-8"?>\n'
NSDECL = ('xmlns="uri:ea.com:eala:asset" '
          'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
          'xmlns:xai="uri:ea.com:eala:asset:instance"')


def decl(body: str, extra_ns: str = "") -> str:
    return (XMLDECL + "<AssetDeclaration " + NSDECL + (" " + extra_ns if extra_ns else "")
            + ">\n" + body + "</AssetDeclaration>\n")


def decl_includes(body: str, extra_ns: str = "") -> str:
    return decl("<Includes>\n" + body + "</Includes>\n", extra_ns)


def include(source: str, itype: str = "all") -> str:
    return '<Include type="%s" source="%s" />\n' % (itype, source)


TANK = decl("""
<GameObject id="SampleTank" inheritFrom="BaseVehicle" Side="Japan" EditorSorting="UNIT"
    BuildTime="10" KindOf="SELECTABLE VEHICLE" CommandSet="SampleTankCommandSet">
  <DisplayName xai:joinAction="Replace">Name:SampleTank</DisplayName>
  <GameDependency><NeededUpgrade>Upgrade_Tech2</NeededUpgrade></GameDependency>
  <ObjectResourceInfo><BuildCost Account="=$ACCOUNT_ORE" Amount="1000"/></ObjectResourceInfo>
  <ArmorSet Armor="FooArmor" Conditions="PLAYER_UPGRADE" DamageFX="VehicleDamageFX"/>
  <LocomotorSet Locomotor="FooLoco" Condition="NORMAL" Speed="75.0"/>
  <Behaviors>
    <WeaponSetUpdate id="ModuleTag_WSU">
      <WeaponSlotTurret ID="1">
        <Weapon Ordering="PRIMARY_WEAPON" Template="FooCannon"
            ForbiddenObjectStatus="GENERIC_TOGGLE_STATE"/>
      </WeaponSlotTurret>
    </WeaponSetUpdate>
  </Behaviors>
  <Body><ActiveBody id="ModuleTag_Body" MaxHealth="380"/></Body>
</GameObject>
""")

NAVAL = decl("""
<GameObject id="SampleTank_Naval" inheritFrom="SampleTank" ProductionQueueType="WATERCRAFT">
  <EquivalentTo>SampleTank</EquivalentTo>
</GameObject>
""")

MINER = decl("""
<GameObject id="SampleMiner" inheritFrom="BaseVehicle" Side="Japan" EditorSorting="UNIT"
    KindOf="SELECTABLE VEHICLE HARVESTER">
  <DisplayName>Name:SampleMiner</DisplayName>
  <Body><ActiveBody id="ModuleTag_Body" MaxHealth="500"/></Body>
  <ObjectResourceInfo><BuildCost Account="=$ACCOUNT_ORE" Amount="1400"/></ObjectResourceInfo>
  <LocomotorSet Locomotor="FooLoco" Condition="NORMAL" Speed="40.0"/>
</GameObject>
""")

MCV = decl("""
<GameObject id="SampleMCV" inheritFrom="BaseVehicle" Side="Japan" EditorSorting="UNIT"
    KindOf="SELECTABLE VEHICLE MCV UNPACKS_INTO_BUILDING">
  <DisplayName>Name:SampleMCV</DisplayName>
  <Body><ActiveBody id="ModuleTag_Body" MaxHealth="5000"/></Body>
  <Behaviors>
    <ReplaceSelfSpecialAbility id="ModuleTag_ReplaceSelf">
      <ReplacementTemplate>SampleStructure</ReplacementTemplate>
    </ReplaceSelfSpecialAbility>
  </Behaviors>
</GameObject>
""")

STRUCTURE = decl("""
<GameObject id="SampleStructure" inheritFrom="BaseObject" Side="Japan" EditorSorting="STRUCTURE">
  <DisplayName>Name:SampleStructure</DisplayName>
  <Body><ActiveBody id="ModuleTag_Body" MaxHealth="3000"/></Body>
</GameObject>
""")

PROP = decl("""
<GameObject id="SampleProp" inheritFrom="BaseObject">
  <Body><ActiveBody id="ModuleTag_Body" MaxHealth="50"/></Body>
</GameObject>
""")

EGG = decl("""
<GameObject id="SampleEgg" inheritFrom="BaseObject">
  <Body><ActiveBody id="ModuleTag_Body" MaxHealth="10"/></Body>
</GameObject>
""")

CAMPAIGN = decl("""
<GameObject id="SampleTank_S07" inheritFrom="BaseVehicle" Side="Japan" EditorSorting="UNIT">
  <DisplayName>Name:SampleTank_S07</DisplayName>
</GameObject>
""")

BASE_IN_UNITS_DIR = decl("""
<GameObject id="BaseSampleSupport" inheritFrom="BaseVehicle" Side="Japan" EditorSorting="UNIT">
  <DisplayName>Name:BaseSampleSupport</DisplayName>
</GameObject>
""")

APPEND_CHILD = decl("""
<GameObject id="AppendChild" inheritFrom="SampleTank" Side="Japan" EditorSorting="UNIT">
  <DisplayName xai:joinAction="Append">Name:AppendChild</DisplayName>
</GameObject>
""")

REMOVE_CHILD = decl("""
<GameObject id="RemoveChild" inheritFrom="SampleTank" Side="Japan" EditorSorting="UNIT">
  <DisplayName xai:joinAction="Remove"/>
</GameObject>
""")

DUP_A = decl('<GameObject id="MultiplayerBeacon" EditorSorting="UNIT"/>')
DUP_B = decl('<GameObject id="MultiplayerBeacon" EditorSorting="UNIT"/>')

MACRO_UNIT = decl("""
<GameObject id="MacroUnit" inheritFrom="BaseVehicle" Side="Japan" EditorSorting="UNIT"
    BuildTime="AUTO">
  <Body><ActiveBody id="ModuleTag_Body" MaxHealth="=$BASE_HP"/></Body>
  <ObjectResourceInfo><BuildCost Account="=$ACCOUNT_ORE" Amount="=$COST_MACRO"/></ObjectResourceInfo>
  <LocomotorSet Locomotor="FooLoco" Condition="NORMAL" Speed="=$WARP_SPEED"/>
</GameObject>
""")

BASE_OBJECTS = decl("""
<GameObject id="BaseObject">
  <Behaviors/>
  <Body/>
</GameObject>
<GameObject id="BaseVehicle" inheritFrom="BaseObject" EditorSorting="UNIT">
  <ArmorSet Armor="GenericArmor"/>
  <Body><ActiveBody id="ModuleTag_Body" MaxHealth="100"/></Body>
</GameObject>
""")

GLOBALDATA_WEAPON = decl("""
<WeaponTemplate id="FooCannon" />
<WeaponTemplate id="GenericWeapon" />
""")
GLOBALDATA_ARMOR = decl("""
<ArmorTemplate id="FooArmor" />
<ArmorTemplate id="GenericArmor" />
""")
GLOBALDATA_LOCOMOTOR = decl("""
<LocomotorTemplate id="FooLoco" />
""")


def standard_fixture(root: str) -> None:
    w = lambda rel, text: write(root, rel, text)  # noqa: E731
    w("StaticGameObjects.xml", decl_includes(
        include("DATA:Japan/Japan.xml")))
    w("japan/Japan.xml", decl_includes(
        include("DATA:BaseObjects/BaseObject.xml")
        + include("Units/SampleTank.xml")        # uppercase dir on purpose (casing portability)
        + include("units/SampleTank_Naval.xml")
        + include("units/SampleMiner.xml")
        + include("units/SampleMCV.xml")
        + include("units/AppendChild.xml")
        + include("units/RemoveChild.xml")
        + include("units/MacroUnit.xml")
        + include("units/BaseSampleSupport.xml")
        + include("units/SampleTank_S07.xml")
        + include("units/NoIdUnit.xml")
        + include("structures/SampleStructure.xml")
        + include("props/SampleProp.xml")
        + include("eggs/SampleEgg.xml")
        + include("Units/MissingUnit.xml")     # missing on purpose
        + "<!-- " + include("units/CommentedOut.xml") + " -->\n"
        + include("DATA:Neutral/NeutralProps.xml")))
    w("japan/units/SampleTank.xml", TANK)
    w("japan/units/SampleTank_Naval.xml", NAVAL)
    w("japan/units/SampleMiner.xml", MINER)
    w("japan/units/SampleMCV.xml", MCV)
    w("japan/units/AppendChild.xml", APPEND_CHILD)
    w("japan/units/RemoveChild.xml", REMOVE_CHILD)
    w("japan/units/MacroUnit.xml", MACRO_UNIT)
    w("japan/units/BaseSampleSupport.xml", BASE_IN_UNITS_DIR)
    w("japan/units/SampleTank_S07.xml", CAMPAIGN)
    w("japan/units/NoIdUnit.xml",
      decl('<GameObject inheritFrom="BaseVehicle"/>\n'))
    w("japan/structures/SampleStructure.xml", STRUCTURE)
    w("japan/props/SampleProp.xml", PROP)
    w("japan/eggs/SampleEgg.xml", EGG)
    w("neutral/props/MultiplayerBeacon.xml", DUP_A)
    w("neutral/props2/ChronoSwapBeacon.xml", DUP_B)
    w("Neutral/NeutralProps.xml", decl_includes(
        include("props/MultiplayerBeacon.xml") + include("props2/ChronoSwapBeacon.xml")))
    w("GlobalData/Weapon.xml", GLOBALDATA_WEAPON)
    w("GlobalData/Armor.xml", GLOBALDATA_ARMOR)
    w("GlobalData/Locomotor.xml", GLOBALDATA_LOCOMOTOR)
    w("BaseObjects/BaseObject.xml", BASE_OBJECTS)


def write(root: str, rel: str, text: str) -> None:
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def run(root: str, entry: str = "StaticGameObjects.xml") -> dict:
    return era.build_document(root, [entry])


def by_id(doc: dict, object_id: str) -> dict | None:
    for r in doc["units"]:
        if r["id"] == object_id:
            return r
    return None


def excluded_by_id(doc: dict, object_id: str) -> list[dict]:
    return [r for r in doc["excluded_objects"] if r["id"] == object_id]


def codes(doc: dict, code: str) -> list[dict]:
    return [d for d in doc["diagnostics"] if d["code"] == code]


class NamespaceHandlingTest(unittest.TestCase):
    def test_join_action_matches_by_uri_not_prefix(self):
        """The xai namespace URI is what matters, not the prefix spelling."""
        with tempfile.TemporaryDirectory() as root:
            write(root, "StaticGameObjects.xml", decl_includes(include("DATA:Japan/Japan.xml")))
            write(root, "Japan/Japan.xml", decl_includes(include("units/U.xml")))
            write(root, "japan/units/U.xml", decl("""
<GameObject id="U" Side="Japan" EditorSorting="UNIT"
    xmlns:xai2="uri:ea.com:eala:asset:instance">
  <DisplayName xai2:joinAction="Replace">Name:U</DisplayName>
</GameObject>
"""))
            doc = run(root)
            rec = by_id(doc, "U")
            self.assertEqual(rec["display_name_key"]["value"], "Name:U")
            self.assertEqual(rec["display_name_key"]["status"], era.STATUS_LOCAL)


class LocalVsInheritedTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        standard_fixture(self._tmp.name)
        self.doc = run(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_local_body_and_cost_win_and_resolve_as_local(self):
        rec = by_id(self.doc, "SampleTank")
        self.assertEqual(rec["body"]["max_health"]["value"], 380.0)
        self.assertEqual(rec["body"]["status"], era.STATUS_LOCAL)
        self.assertEqual(rec["build_cost"]["build_costs"][0]["amount_value"], 1000.0)
        self.assertEqual(rec["build_time"]["value"], 10.0)

    def test_inherited_fields_come_from_the_parent_and_say_so(self):
        rec = by_id(self.doc, "SampleTank_Naval")
        self.assertEqual(rec["body"]["max_health"]["value"], 380.0)
        self.assertEqual(rec["body"]["status"], era.STATUS_INHERITED)
        self.assertEqual(rec["body"]["resolution"], "SampleTank")
        self.assertEqual(rec["build_cost"]["build_costs"][0]["amount_value"], 1000.0)
        self.assertEqual(rec["build_cost"]["build_costs"][0]["amount_status"], era.STATUS_OK)
        # uniform rule: even a fully-populated unit is NEVER auto eligible
        self.assertIs(rec["auto_balance_eligible"], False)
        self.assertIs(rec["static_candidate"], True)
        self.assertIn("explicit downstream validation", rec["downstream_validation_required"])

    def test_auto_balance_eligibility_is_uniformly_false(self):
        for r in self.doc["units"]:
            self.assertIs(r["auto_balance_eligible"], False, r["id"])
            self.assertTrue(r.get("downstream_validation_required"), r["id"])

    def test_ancestor_defaults_survive_for_keys_the_child_never_declared(self):
        rec = by_id(self.doc, "AppendChild")
        armors = [a["armor"] for a in rec["armor_refs"]]
        self.assertIn("FooArmor", armors)
        self.assertIn("GenericArmor", armors)

    def test_variants_stay_distinct_but_linked(self):
        base = by_id(self.doc, "SampleTank")
        naval = by_id(self.doc, "SampleTank_Naval")
        self.assertIsNot(base, naval)
        self.assertEqual(naval["equivalent_to"]["value"], "SampleTank")
        self.assertEqual(naval["inherits_from"], "SampleTank")

    def test_join_action_remove_drops_the_inherited_value(self):
        rec = by_id(self.doc, "RemoveChild")
        self.assertEqual(rec["display_name_key"]["status"], era.STATUS_REMOVED)
        self.assertIsNone(rec["display_name_key"]["value"])
        self.assertNotIn("display_name_key",
                         [f["field"] for f in rec.get("unavailable_fields") or []])

    def test_unsupported_join_action_is_unverified_never_guessed(self):
        rec = by_id(self.doc, "AppendChild")
        self.assertEqual(rec["display_name_key"]["status"],
                         era.STATUS_MERGE_UNSUPPORTED)
        self.assertIn("Append", doc_resolution_model(self.doc)["join_action_unsupported_observed"])


def doc_resolution_model(doc: dict) -> dict:
    return doc["resolution_model"]


class WeaponModeConditionsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        standard_fixture(self._tmp.name)
        self.doc = run(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_weapon_template_reference_and_mode_conditions(self):
        rec = by_id(self.doc, "SampleTank")
        self.assertEqual(len(rec["weapon_refs"]), 1)
        w = rec["weapon_refs"][0]
        self.assertEqual(w["template"], "FooCannon")
        self.assertEqual(w["slot"], {"tag": "WeaponSlotTurret", "id": "1"})
        self.assertEqual(w["ordering"], "PRIMARY_WEAPON")
        self.assertEqual(w["conditions"], {"forbidden_object_status": "GENERIC_TOGGLE_STATE"})
        self.assertIs(w["weapon_template"]["resolved"], True)
        self.assertEqual(w["module"], {"tag": "WeaponSetUpdate", "id": "ModuleTag_WSU"})

    def test_weapon_stats_are_never_extracted(self):
        rec = by_id(self.doc, "SampleTank")
        self.assertNotIn("damage", rec["weapon_refs"][0])
        self.assertNotIn("dps", rec["weapon_refs"][0])
        self.assertNotIn("reload", rec["weapon_refs"][0])

    def test_mcv_replacement_template_is_recorded_as_a_transform_link(self):
        rec = by_id(self.doc, "SampleMCV")
        self.assertEqual([r["value"] for r in rec["replaces_into"]], ["SampleStructure"])
        self.assertEqual(rec["classification"], "manual_review_only")

    def test_unresolved_weapon_template_ref_is_a_diagnostic(self):
        with tempfile.TemporaryDirectory() as root:
            write(root, "StaticGameObjects.xml", decl_includes(include("DATA:Japan/Japan.xml")))
            write(root, "Japan/Japan.xml", decl_includes(include("units/U.xml")))
            write(root, "japan/units/U.xml", decl("""
<GameObject id="U" Side="Japan" EditorSorting="UNIT">
  <Behaviors><WeaponSetUpdate id="W">
    <Weapon Template="NoSuchWeapon"/>
  </WeaponSetUpdate></Behaviors>
</GameObject>
"""))
            write(root, "GlobalData/Weapon.xml", GLOBALDATA_WEAPON)
            doc = run(root)
            self.assertTrue(codes(doc, "weapon_template_ref_unresolved"))
            self.assertIs(by_id(doc, "U")["weapon_refs"][0]["weapon_template"]["resolved"],
                          False)


class MissingAndDuplicateIdsTest(unittest.TestCase):
    def test_missing_object_id_is_a_diagnostic_not_a_crash(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            doc = run(root)
            self.assertTrue(codes(doc, "missing_object_id"))

    def test_duplicate_ids_are_ambiguous_and_never_counted(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            doc = run(root)
            dup = codes(doc, "duplicate_object_id")
            self.assertEqual(len(dup), 1)
            self.assertEqual(dup[0]["detail"], "multiplayerbeacon")
            rows = excluded_by_id(doc, "MultiplayerBeacon")
            self.assertEqual(len(rows), 2)
            for row in rows:
                self.assertEqual(row["exclusion_reason"], "ambiguous_duplicate_id")


class UnsupportedExpressionsTest(unittest.TestCase):
    def test_macros_are_recorded_raw_and_never_evaluated(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            doc = run(root)
            rec = by_id(doc, "MacroUnit")
            mh = rec["body"]["max_health"]
            self.assertEqual(mh["raw"], "=$BASE_HP")
            self.assertIsNone(mh["value"])
            self.assertEqual(mh["status"], era.STATUS_MACRO)
            sp = rec["locomotors"][0]["speed"]
            self.assertEqual(sp["status"], era.STATUS_MACRO)
            self.assertIsNone(sp["value"])
            amt = rec["build_cost"]["build_costs"][0]
            self.assertEqual(amt["account_status"], era.STATUS_MACRO)
            self.assertIsNone(amt["amount_value"])
            self.assertIn("hp", [f["field"] for f in rec["unavailable_fields"]])

    def test_nonnumeric_values_are_unverified(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            doc = run(root)
            rec = by_id(doc, "MacroUnit")
            self.assertEqual(rec["build_time"]["raw"], "AUTO")
            self.assertEqual(rec["build_time"]["status"], era.STATUS_NONNUMERIC)
            self.assertIsNone(rec["build_time"]["value"])


class EntityAndPathSafetyTest(unittest.TestCase):
    def test_path_escape_is_rejected_and_never_followed(self):
        with tempfile.TemporaryDirectory() as root:
            outside = os.path.join(os.path.dirname(root), "outside.xml")
            write(os.path.dirname(root), "outside.xml",
                  decl('<GameObject id="OutsideObject"/>'))
            try:
                write(root, "StaticGameObjects.xml", decl_includes(include("../../outside.xml")))
                doc = run(root)
                self.assertTrue(codes(doc, "path_escape"))
                self.assertIsNone(by_id(doc, "OutsideObject"))
                self.assertTrue(all(r["id"] != "OutsideObject"
                                    for r in doc["excluded_objects"]))
            finally:
                if os.path.exists(outside):
                    os.remove(outside)

    def test_include_cycle_is_detected(self):
        with tempfile.TemporaryDirectory() as root:
            write(root, "StaticGameObjects.xml", decl_includes(include("a.xml")))
            write(root, "a.xml", decl_includes(include("b.xml")))
            write(root, "b.xml", decl_includes(include("a.xml")))
            doc = run(root)
            self.assertTrue(codes(doc, "include_cycle"))

    def test_case_collision_is_ambiguous_and_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            files: dict[str, list[str]] = {}
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    rel = os.path.relpath(os.path.join(dirpath, fn), root)
                    files.setdefault(era.norm_key(rel), []).append(
                        rel.replace("\\", "/"))
            key = era.norm_key("japan/units/SampleTank.xml")
            files[key] = ["Japan/Units/SampleTank.xml", "japan/units/SampleTank.xml"]
            doc = era.build_document(root, ["StaticGameObjects.xml"], index_files=files)
            self.assertTrue(codes(doc, "case_collision"))
            self.assertIsNone(by_id(doc, "SampleTank"))

    def test_ea_include_casing_is_portable(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            doc = run(root)
            self.assertIsNotNone(by_id(doc, "SampleTank"))  # included as Units/...

    def test_commented_out_include_is_not_followed(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            doc = run(root)
            self.assertNotIn("CommentedOut", json.dumps(doc["diagnostics"]))


class DeterminismTest(unittest.TestCase):
    def test_two_runs_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            b1 = era.render_document(run(root))
            b2 = era.render_document(run(root))
            self.assertEqual(b1, b2)

    def test_output_refuses_to_overwrite_different_content(self):
        with tempfile.TemporaryDirectory() as out_tmp:
            source_tmp = tempfile.TemporaryDirectory()
            try:
                root = source_tmp.name
                standard_fixture(root)
                doc = run(root)
                out = os.path.join(out_tmp, "o.json")
                era.write_output(doc, out)
                with open(out, "rb") as fh:
                    first = fh.read()
                # mutate the fixture so the document changes
                tank = os.path.join(root, "japan", "units", "SampleTank.xml")
                with open(tank, "r", encoding="utf-8") as fh:
                    text = fh.read()
                with open(tank, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text.replace('MaxHealth="380"', 'MaxHealth="381"'))
                doc2 = run(root)
                with self.assertRaises(SystemExit) as cm:
                    era.write_output(doc2, out)
                self.assertIn("REFUSING", str(cm.exception))
                with open(out, "rb") as fh:
                    self.assertEqual(fh.read(), first)
            finally:
                source_tmp.cleanup()

    def test_identical_rerun_is_an_idempotent_success(self):
        with tempfile.TemporaryDirectory() as out_tmp:
            source_tmp = tempfile.TemporaryDirectory()
            try:
                root = source_tmp.name
                standard_fixture(root)
                doc = run(root)
                out = os.path.join(out_tmp, "o.json")
                era.write_output(doc, out)
                era.write_output(run(root), out)  # must not raise
            finally:
                source_tmp.cleanup()


class EconomicExclusionTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        standard_fixture(self._tmp.name)
        self.doc = run(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_mcv_and_harvester_are_manual_review_only(self):
        for oid in ("SampleMCV", "SampleMiner"):
            rec = by_id(self.doc, oid)
            self.assertEqual(rec["classification"], "manual_review_only", oid)
            self.assertIs(rec["auto_balance_eligible"], False)
            self.assertTrue(rec["manual_review_reason"])

    def test_buildings_props_eggs_base_templates_and_campaign_are_excluded(self):
        expected = {
            "SampleStructure": "building_or_structure",
            "SampleProp": "prop_or_neutral_or_system",
            "SampleEgg": "egg",
            "BaseSampleSupport": "base_template",
            "SampleTank_S07": "campaign_variant",
        }
        for oid, reason in expected.items():
            rows = excluded_by_id(self.doc, oid)
            self.assertEqual(len(rows), 1, oid)
            self.assertEqual(rows[0]["exclusion_reason"], reason, oid)
            self.assertNotIn(oid, {r["id"] for r in self.doc["units"]})

    def test_ordinary_units_are_counted_per_faction(self):
        counts = self.doc["counts"]
        self.assertEqual(counts["unit_records"],
                         len([r for r in self.doc["units"]
                              if r["classification"] == "unit"]))
        self.assertEqual(counts["manual_review_only_records"], 2)
        self.assertIn("unit/Japan", counts["by_faction"])

    def test_exclusions_are_reported_not_silent(self):
        reasons = self.doc["counts"]["exclusions_by_reason"]
        for reason in ("building_or_structure", "prop_or_neutral_or_system", "egg",
                       "base_template", "campaign_variant", "ambiguous_duplicate_id"):
            self.assertIn(reason, reasons)


class ProvenanceTest(unittest.TestCase):
    def test_per_record_provenance_is_present(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            doc = run(root)
            rec = by_id(doc, "SampleTank")
            prov = rec["provenance"]
            self.assertIsNone(prov["source_revision"])  # fixture is not a git repo
            self.assertFalse(doc["source"]["revision_verified"])
            self.assertEqual(len(prov["declaring_file_sha256"]), 64)
            self.assertEqual(prov["include_chain"][-1], "japan/units/SampleTank.xml")
            self.assertEqual(prov["inherit_chain"],
                             ["SampleTank", "BaseVehicle", "BaseObject"])
            self.assertIn("NOT verified to be the final retail patch",
                          prov["ea_source_caveat"])
            self.assertIn("GPL-3.0-or-later", prov["license"])

    def test_limitations_are_carried_by_the_document_itself(self):
        with tempfile.TemporaryDirectory() as root:
            standard_fixture(root)
            doc = run(root)
            joined = "\n".join(doc["limitations"])
            self.assertIn("NOT verified to be the final retail patch", joined)
            self.assertIn("never evaluated", joined)


class ArtDependenciesTest(unittest.TestCase):
    def test_art_references_are_reported_unresolved_never_fabricated(self):
        with tempfile.TemporaryDirectory() as root:
            write(root, "StaticGameObjects.xml", decl_includes(include("DATA:Japan/Japan.xml")))
            write(root, "Japan/Japan.xml", decl_includes(
                include("ART:SomeModel.w3x") + include("units/U.xml")))
            write(root, "japan/units/U.xml", decl(
                '<GameObject id="U" Side="Japan" EditorSorting="UNIT"/>'))
            doc = run(root)
            self.assertTrue(codes(doc, "art_dependency_unresolved"))
            self.assertIsNotNone(by_id(doc, "U"))


class ExternalDestinationTest(unittest.TestCase):
    DOC = {"schema": "x", "units": []}

    def test_rejects_targets_inside_protected_roots(self):
        with tempfile.TemporaryDirectory() as base:
            repo_dir = os.path.join(base, "cameo_repo")
            source_dir = os.path.join(base, "ea_checkout")
            os.makedirs(os.path.join(repo_dir, "tools", "reference"))
            os.makedirs(os.path.join(source_dir, "Xml"))
            for guard, rel in ((repo_dir, "out.json"),
                               (repo_dir, "tools/reference/out.json"),
                               (source_dir, "o.json"),
                               (source_dir, "Xml/o.json")):
                with self.assertRaises(SystemExit) as cm:
                    era.write_output(self.DOC, os.path.join(guard, rel),
                                     forbid_inside=[repo_dir, source_dir])
                self.assertIn("protected", str(cm.exception), rel)

    def test_exclusive_creation_refuses_an_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "o.json")
            with open(p, "wb") as fh:
                fh.write(b"{}")
            with self.assertRaises(FileExistsError):
                era._create_exclusive(p)

    def test_racing_identical_writers_both_succeed_via_exclusive_creation(self):
        """Two writers start past a barrier on a FRESH path; the loser must lose the
        O_CREAT|O_EXCL open and fall back to the byte-compare rule (identical = ok)."""
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "o.json")
            data = era.render_document(self.DOC)
            barrier = threading.Barrier(2)
            outcomes: list[str] = []

            def writer() -> None:
                barrier.wait()
                try:
                    era.write_output(self.DOC, p)
                    outcomes.append("ok")
                except SystemExit:
                    outcomes.append("refused")

            ts = [threading.Thread(target=writer) for _ in range(2)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
            self.assertEqual(outcomes, ["ok", "ok"])
            with open(p, "rb") as fh:
                self.assertEqual(fh.read(), data)

    def test_empty_guard_list_still_yields_mandatory_defaults(self):
        """An empty/omitted guard list must NOT bypass protection: the mandatory
        defaults (running repo, EA checkout) are always active."""
        with tempfile.TemporaryDirectory() as tmp:
            # a synthetic document claiming a source root inside tmp: defaults must
            # then protect that root even though no explicit guards are passed
            doc = {"schema": "x", "source": {"root": os.path.join(tmp, "ea_source")}}
            era.write_output(doc, os.path.join(tmp, "elsewhere", "o.json"))  # external ok
            with self.assertRaises(SystemExit) as cm:
                era.write_output(doc, os.path.join(tmp, "ea_source", "o.json"))
            self.assertIn("protected", str(cm.exception))
            # explicit empty list behaves the same as omitted
            with self.assertRaises(SystemExit):
                era.write_output({"schema": "x",
                                  "source": {"root": os.path.join(tmp, "s2")}},
                                 os.path.join(tmp, "s2", "o.json"), forbid_inside=[])

    def _make_dir_link(self, link: str, target: str) -> bool:
        """Directory symlink/junction when the platform+privileges allow; else False
        (the fixture test then skips — coverage degrades honestly)."""
        try:
            os.symlink(target, link, target_is_directory=True)
            return True
        except (OSError, NotImplementedError):
            try:
                subprocess.run(["cmd", "/c", "mklink", "/J",
                                os.path.abspath(link), os.path.abspath(target)],
                               check=True, capture_output=True, timeout=30)
                return True
            except Exception:
                return False

    def test_symlink_or_junction_into_protected_root_cannot_bypass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = os.path.join(tmp, "repo_l")
            os.makedirs(repo)
            link = os.path.join(tmp, "external_link")
            if not self._make_dir_link(link, repo):
                self.skipTest("symlink/junction creation not permitted here")
            doc = {"schema": "x", "source": {"root": os.path.join(tmp, "ea_source")}}
            out_via_link = os.path.join(link, "out.json")
            # lexical abspath of out_via_link does NOT name the repo; realpath must
            with self.assertRaises(SystemExit) as cm:
                era.write_output(doc, out_via_link, forbid_inside=[repo])
            self.assertIn("protected", str(cm.exception))
            self.assertFalse(os.path.exists(out_via_link))
            # and a truly external sibling path still works while the race-safe
            # exclusive creation is exercised: a fresh target + identical rerun
            era.write_output(doc, os.path.join(tmp, "real_out", "o.json"))
            era.write_output(doc, os.path.join(tmp, "real_out", "o.json"))


class AutoEligibilityTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        standard_fixture(self._tmp.name)
        self.doc = run(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_static_candidates_are_kept_but_never_eligible(self):
        rec = by_id(self.doc, "SampleTank")
        self.assertEqual(rec["classification"], "unit")
        self.assertIs(rec["static_candidate"], True)
        self.assertIs(rec["auto_balance_eligible"], False)
        self.assertIn("explicit downstream validation",
                      rec["downstream_validation_required"])

    def test_ordinary_looking_unit_with_ambiguous_weapon_module_is_never_eligible(self):
        """An ordinary, fully-statted-looking unit whose weapon module id is
        duplicated must NEVER come out auto eligible."""
        with tempfile.TemporaryDirectory() as root:
            write(root, "StaticGameObjects.xml", decl_includes(include("DATA:Japan/Japan.xml")))
            write(root, "Japan/Japan.xml", decl_includes(include("units/U.xml")))
            write(root, "japan/units/U.xml", decl("""
<GameObject id="U" Side="Japan" EditorSorting="UNIT" BuildTime="12">
  <DisplayName>Name:U</DisplayName>
  <ObjectResourceInfo><BuildCost Account="=$ACCOUNT_ORE" Amount="900"/></ObjectResourceInfo>
  <Body><ActiveBody id="B" MaxHealth="600"/></Body>
  <Behaviors>
    <WeaponSetUpdate id="ModuleTag_W"><Weapon Template="FooCannon"/></WeaponSetUpdate>
    <WeaponSetUpdate id="ModuleTag_W"><Weapon Template="FooCannon"
        Ordering="PRIMARY_WEAPON"/></WeaponSetUpdate>
  </Behaviors>
</GameObject>
"""))
            doc = run(root)
            rec = by_id(doc, "U")
            self.assertEqual(rec["classification"], "unit")
            self.assertEqual(rec["weapon_refs"][0]["status"],
                             era.STATUS_AMBIGUOUS_DUPLICATE)
            self.assertIs(rec["auto_balance_eligible"], False)
            self.assertIs(rec["static_candidate"], True)

    def test_concurrent_different_writers_never_double_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "o.json")
            doc_a = {"schema": "a"}
            doc_b = {"schema": "b"}
            barrier = threading.Barrier(2)
            results: list[str] = []

            def writer(doc):
                barrier.wait()
                try:
                    era.write_output(doc, p)
                    results.append("ok")
                except SystemExit:
                    results.append("refused")

            ts = [threading.Thread(target=writer, args=(d,)) for d in (doc_a, doc_b)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
            self.assertEqual(sorted(results), ["ok", "refused"])
            with open(p, "rb") as fh:
                got = json.loads(fh.read().decode("utf-8"))
            self.assertIn(got["schema"], ("a", "b"))


class SameDepthDuplicateTest(unittest.TestCase):
    def test_duplicate_locomotor_key_is_ambiguous_never_last_wins(self):
        with tempfile.TemporaryDirectory() as root:
            write(root, "StaticGameObjects.xml", decl_includes(include("DATA:Japan/Japan.xml")))
            write(root, "Japan/Japan.xml", decl_includes(include("units/U.xml")))
            write(root, "japan/units/U.xml", decl("""
<GameObject id="U" Side="Japan" EditorSorting="UNIT">
  <DisplayName>Name:U</DisplayName>
  <LocomotorSet Locomotor="FooLoco" Condition="NORMAL" Speed="70.0"/>
  <LocomotorSet Locomotor="FooLoco" Condition="NORMAL" Speed="90.0"/>
</GameObject>
"""))
            write(root, "GlobalData/Locomotor.xml", GLOBALDATA_LOCOMOTOR)
            doc = run(root)
            rec = by_id(doc, "U")
            self.assertEqual(len(rec["locomotors"]), 1)
            entry = rec["locomotors"][0]
            self.assertEqual(entry["status"], era.STATUS_AMBIGUOUS_DUPLICATE)
            self.assertNotIn("speed", entry)  # no numeric is claimed
            self.assertTrue(codes(doc, "ambiguous_duplicate_key"))
            uncertain = doc["counts"]["uncertain_semantics"]
            self.assertGreaterEqual(
                uncertain["roster_records_with_unverified_stat_fields"], 1)
            self.assertGreaterEqual(uncertain["diagnostic_code_counts"]
                                    ["ambiguous_duplicate_key"], 1)

    def test_duplicate_module_id_is_ambiguous_and_refs_carry_the_status(self):
        with tempfile.TemporaryDirectory() as root:
            write(root, "StaticGameObjects.xml", decl_includes(include("DATA:Japan/Japan.xml")))
            write(root, "Japan/Japan.xml", decl_includes(include("units/U.xml")))
            write(root, "japan/units/U.xml", decl("""
<GameObject id="U" Side="Japan" EditorSorting="UNIT">
  <Behaviors>
    <WeaponSetUpdate id="ModuleTag_W"><Weapon Template="FooCannon"/></WeaponSetUpdate>
    <WeaponSetUpdate id="ModuleTag_W"><Weapon Template="FooCannon"/></WeaponSetUpdate>
  </Behaviors>
</GameObject>
"""))
            write(root, "GlobalData/Weapon.xml", GLOBALDATA_WEAPON)
            doc = run(root)
            rec = by_id(doc, "U")
            self.assertEqual(len(rec["weapon_refs"]), 1)
            self.assertEqual(rec["weapon_refs"][0]["status"],
                             era.STATUS_AMBIGUOUS_DUPLICATE)
            self.assertTrue(codes(doc, "ambiguous_duplicate_key"))

    def test_unsupported_join_action_is_unverified_without_any_predecessor(self):
        with tempfile.TemporaryDirectory() as root:
            write(root, "StaticGameObjects.xml", decl_includes(include("DATA:Japan/Japan.xml")))
            write(root, "Japan/Japan.xml", decl_includes(include("units/U.xml")))
            write(root, "japan/units/U.xml", decl("""
<GameObject id="U" Side="Japan" EditorSorting="UNIT">
  <DisplayName xai:joinAction="Append">Name:U</DisplayName>
</GameObject>
"""))
            doc = run(root)
            dn = by_id(doc, "U")["display_name_key"]
            self.assertEqual(dn["status"], era.STATUS_MERGE_UNSUPPORTED)
            self.assertNotEqual(dn["status"], era.STATUS_LOCAL)


class InheritanceBreakTest(unittest.TestCase):
    def run_broken(self, extra_files: dict[str, str], entry_body: str) -> tuple[dict, object]:
        with tempfile.TemporaryDirectory() as root:
            write(root, "StaticGameObjects.xml", decl_includes(include("DATA:Japan/Japan.xml")))
            write(root, "Japan/Japan.xml", decl_includes(entry_body))
            for rel, text in extra_files.items():
                write(root, rel, text)
            return run(root)

    def test_missing_parent_makes_a_locally_complete_unit_ineligible(self):
        doc = self.run_broken(
            {"japan/units/U.xml": decl("""
<GameObject id="U" inheritFrom="NoSuchParent" Side="Japan" EditorSorting="UNIT" BuildTime="7">
  <DisplayName>Name:U</DisplayName>
  <Body><ActiveBody id="B" MaxHealth="250"/></Body>
  <ObjectResourceInfo><BuildCost Account="=$ACCOUNT_ORE" Amount="800"/></ObjectResourceInfo>
</GameObject>
""")},
            include("units/U.xml"))
        rec = by_id(doc, "U")
        self.assertEqual(rec["classification"], "manual_review_only")
        self.assertIs(rec["auto_balance_eligible"], False)
        self.assertEqual(rec["inheritance_status"]["cause"], "missing_parent")
        self.assertEqual(rec["inheritance_status"]["status"],
                         "unverified_broken_inheritance")
        # the local fields are still visible, but they never certify the unit
        self.assertEqual(rec["body"]["max_health"]["value"], 250.0)
        self.assertIn("broken_inheritance", rec["manual_review_reason"])

    def test_ambiguous_parent_is_ineligible(self):
        parent = decl('<GameObject id="SharedParent"><Body/></GameObject>')
        doc = self.run_broken(
            {"parent_a.xml": parent, "parent_b.xml": parent,
             "japan/units/U.xml": decl("""
<GameObject id="U" inheritFrom="SharedParent" Side="Japan" EditorSorting="UNIT">
  <DisplayName>Name:U</DisplayName>
</GameObject>
""")},
            include("DATA:parent_a.xml") + include("DATA:parent_b.xml")
            + include("units/U.xml"))
        rec = by_id(doc, "U")
        self.assertIs(rec["auto_balance_eligible"], False)
        self.assertEqual(rec["inheritance_status"]["cause"], "ambiguous_parent")

    def test_inheritance_cycle_is_ineligible(self):
        doc = self.run_broken(
            {"japan/units/U.xml": decl("""
<GameObject id="A" inheritFrom="B" Side="Japan" EditorSorting="UNIT"/>
<GameObject id="B" inheritFrom="A" Side="Japan" EditorSorting="UNIT"/>
""")},
            include("units/U.xml"))
        for oid in ("A", "B"):
            rec = by_id(doc, oid)
            self.assertIs(rec["auto_balance_eligible"], False, oid)
            self.assertEqual(rec["inheritance_status"]["cause"], "cycle", oid)
            self.assertEqual(rec["classification"], "manual_review_only", oid)


class SourceVerificationTest(unittest.TestCase):
    def _git_repo(self, root: str) -> None:
        def git(*args: str) -> None:
            subprocess.run(["git"] + list(args), cwd=root, check=True,
                           capture_output=True, text=True, timeout=60)
        git("init", "-q", root)
        git("config", "user.email", "fixture@example.com")
        git("config", "user.name", "fixture")
        git("add", "-A")
        git("commit", "-q", "-m", "fixture")

    def minimal_fixture(self, root: str) -> None:
        write(root, "StaticGameObjects.xml", decl_includes(include("DATA:Japan/Japan.xml")))
        write(root, "Japan/Japan.xml", decl_includes(include("units/U.xml")))
        write(root, "japan/units/U.xml", decl(
            '<GameObject id="U" Side="Japan" EditorSorting="UNIT"/>'))

    def test_clean_checkout_is_certified(self):
        with tempfile.TemporaryDirectory() as root:
            self.minimal_fixture(root)
            self._git_repo(root)
            doc = run(root)
            self.assertTrue(doc["source"]["revision_verified"])
            self.assertIs(doc["source"]["worktree_clean"], True)
            self.assertEqual(len(doc["source"]["revision"]), 40)
            rec = by_id(doc, "U")
            self.assertIs(rec["provenance"]["source_worktree_clean"], True)

    def test_dirty_checkout_is_never_certified(self):
        with tempfile.TemporaryDirectory() as root:
            self.minimal_fixture(root)
            self._git_repo(root)
            # uncommitted modification after the commit
            write(root, "japan/units/U.xml", decl(
                '<GameObject id="U" Side="Japan" EditorSorting="UNIT" Touched="1"/>'))
            doc = run(root)
            self.assertFalse(doc["source"]["revision_verified"])
            self.assertIs(doc["source"]["worktree_clean"], False)
            self.assertGreaterEqual(doc["source"]["dirty_entries"], 1)
            self.assertTrue(codes(doc, "dirty_source_worktree"))
            rec = by_id(doc, "U")
            self.assertIs(rec["provenance"]["source_worktree_clean"], False)

    def test_non_repo_source_is_uncertified_not_fabricated(self):
        with tempfile.TemporaryDirectory() as root:
            self.minimal_fixture(root)
            doc = run(root)
            self.assertFalse(doc["source"]["revision_verified"])
            self.assertIsNone(doc["source"]["worktree_clean"])
            self.assertIsNone(by_id(doc, "U")["provenance"]["source_worktree_clean"])
            self.assertTrue(codes(doc, "source_revision_unknown"))


if __name__ == "__main__":
    unittest.main()
