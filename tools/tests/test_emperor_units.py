"""Tests for tools/reference/extract_emperor_units.py.

Fixtures are SYNTHETIC (invented units "AC*" etc., invented numbers) — no
copyrighted Emperor/Westwood text is copied into the repository. Tests that
assert native values from the real archived Rules.txt are OPT-IN via the
`CAMEO_REFERENCE_RAW_SOURCES` environment variable (directory containing
`emperor/Rules.txt`) — no personal path is baked into tests or tool.
"""
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import threading
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
sys.path.insert(0, str(ROOT / "tools" / "tests"))
import _bootstrap  # noqa: F401,E402

import extract_emperor_units as ex  # noqa: E402

# Opt-in integration fixtures: no personal directory default.
RAW_SOURCES = os.environ.get("CAMEO_REFERENCE_RAW_SOURCES")
REAL_SOURCE = pathlib.Path(RAW_SOURCES, "emperor", "Rules.txt") if RAW_SOURCES else None

RULES_MINI = """// synthetic demonstration file for the extractor tests
[General]
Version = 1.23

[HouseTypes]
Atreides
Ordos
Harkonnen
Incidental		//these are the story characters

[ArmourTypes]
None
Light
Heavy
Invulnerable

[UnitGroupTypes]
FromBarracks

[WarheadTypes]
SmallArms_W
Rocket_W

[BulletTypes]
Rifle_B
Rocket_B

[TurretTypes]
ACRifleGun
ACRocketGun

[UnitTypes]
ACRifleman			//AC house only
ACBuggy				//AC house only
ACHarvester			//all houses
ACDeathRay			//AC house only
ACSquid
ACStory
ACGhostUnit			//declared but never defined below
//ACOldUnit			//declared in retail, absent here

[BuildingGroupTypes]
SmWindtrap

[TurretTypes]
ACUnattachedGun

[ACUnattachedGun]
Bullet = Rifle_B
ReloadCount = 10

[ACRifleGun]
Bullet = Rifle_B
ReloadCount = 30

[ACRocketGun]
Bullet = Rocket_B
ReloadCount = 90
TurretNextJoint = ACRifleGun

[Rifle_B]
MaxRange = 6
Speed = 20
Damage = 40
Warhead = SmallArms_W

[Rocket_B]
MaxRange = 12
MinRange = 2
Homing = true
Speed = 28
Damage = 250
Warhead = Rocket_W

[SmallArms_W]
None = 20
Light = 65
Heavy = 100
Invulnerable = 0

[Rocket_W]
None = 30
Light = 65
Heavy = 80
Invulnerable = 0

[ACRifleman]
Score = 2
House = Ordos
PrimaryBuilding = ACBarracks
UnitGroup = FromBarracks
Terrain = Rock, Sand
Cost = 60
BuildTime = 87
Size = 1
Speed = 6.0						//game coord per update
TurretAttach = ACRifleGun
TurnRate = 0.2					//radians per tick
Armour = None, 50, InfRock
Health = 600
Infantry = true
ViewRange = 7
TechLevel = 1
Crushable = TRUE
AlertString IngameMessages HarvAttack	// strings.txt message
AlertTimeOut 300

// LEVEL 1 ----------------------------------
VeterancyLevel = 5	// Score required
Health = 800
ExtraDamage = 25

// LEVEL 2 ----------------------------------
VeterancyLevel = 10
CanSelfRepair = 1

[ACBuggy]
Score = 2
House = Ordos
PrimaryBuilding = ACFactory
UnitGroup = FromBarracks
Cost = 500
BuildTime = 300
Speed = 8.0
TurretAttach = ACRocketGun, ACRifleGun
TurnRate = 0.15
Armour = Light
Health = 900
TechLevel = 2
ExtraDamage = 25

// LEVEL 1 ----------------------------------
VeterancyLevel = 13
ExtraDamage = 50
ExtraArmour = 50

[ACHarvester]
Score = 4
House = Ordos
PrimaryBuilding = ACFactory
UnitGroup = FromBarracks
Cost = 1000
BuildTime = 504
Speed = 4.0
Armour = Heavy
Health = 3500
Harvester = TRUE
TechLevel = 2

[ACDeathRay]
DeathHand = TRUE
House = Ordos
PrimaryBuilding = ACPalace
UnitGroup = FromBarracks
Cost = 0
BuildTime = 5184
Speed = 40
Size = 3
AiSpecial = TRUE

[ACSquid]
Worm = TRUE
Projectable = FALSE
Cost = 850

[ACSquid]
House = Incidental
Cost = 700

[ACStory]
House = Incidental
Cost = 850
Speed = 2.0
Armour = Medium
Health = 500
"""


class Harness(unittest.TestCase):
    def extract(self, text=RULES_MINI):
        issues = []
        with tempfile.TemporaryDirectory() as tmp:
            src = pathlib.Path(tmp) / "Rules.txt"
            src.write_text(text, encoding="utf-8")
            data = ex.extract(pathlib.Path(tmp), issues)
        return data, issues

    def recs(self, data):
        return {r["id"]: r for r in data["records"]}


class ParserShapeTests(Harness):
    def test_unit_fields_are_extracted_verbatim(self):
        data, issues = self.extract()
        recs = self.recs(data)
        rifle = recs["ACRifleman"]
        self.assertEqual((rifle["cost"], rifle["build_time"], rifle["health"]),
                         (60, 87, 600))
        # Armour triple stays RAW — nothing interpreted, nothing guessed.
        self.assertEqual(rifle["armour"], ["None", "50", "InfRock"])
        self.assertEqual(rifle["speed"], "6.0")
        self.assertEqual(rifle["turn_rate"], "0.2")
        self.assertEqual(rifle["house"], ["Ordos"])
        self.assertEqual(rifle["primary_building"], ["ACBarracks"])
        self.assertEqual(rifle["unit_group"], "FromBarracks")
        self.assertEqual(
            {i["severity"] for i in issues},
            {"duplicate_section", "dangling_declaration", "repeated_level_field"})

    def test_weapon_variants_are_not_flattened(self):
        data, _issues = self.extract()
        buggy = self.recs(data)["ACBuggy"]
        variants = buggy["weapon_variants"]
        self.assertEqual(len(variants), 2)
        self.assertEqual([v["turret"] for v in variants],
                         ["ACRocketGun", "ACRifleGun"])
        rocket, rifle = variants
        self.assertEqual((rocket["bullet"], rocket["damage"], rocket["max_range"],
                          rocket["min_range"], rocket["reload_count"],
                          rocket["homing"]),
                         ("Rocket_B", 250, 12, 2, 90, True))
        self.assertEqual((rifle["bullet"], rifle["damage"], rifle["max_range"],
                          rifle["reload_count"]), ("Rifle_B", 40, 6, 30))
        self.assertEqual(rifle["versus"], {"None": 20, "Light": 65,
                                           "Heavy": 100, "Invulnerable": 0})
        self.assertEqual(rocket["versus"], {"None": 30, "Light": 65,
                                            "Heavy": 80, "Invulnerable": 0})

    def test_veterancy_levels_stay_ordered(self):
        data, _issues = self.extract()
        rifle = self.recs(data)["ACRifleman"]
        stripped = [{k: v for k, v in lvl.items() if k != "line"}
                    for lvl in rifle["veterancy"]]
        self.assertEqual(stripped, [
            {"score_required": 5, "health": 800, "extra_damage": 25},
            {"score_required": 10, "can_self_repair": True},
        ])

    def test_two_token_directive_lines_are_kept(self):
        data, _issues = self.extract()
        rifle = self.recs(data)["ACRifleman"]
        self.assertEqual(rifle["misc"].get("AlertString"),
                         "IngameMessages HarvAttack")
        self.assertEqual(rifle["misc"].get("AlertTimeOut"), "300")

    def test_inline_comments_do_not_corrupt_values(self):
        data, _issues = self.extract()
        rifle = self.recs(data)["ACRifleman"]
        self.assertEqual(rifle["speed"], "6.0")
        self.assertEqual(rifle["misc"].get("Infantry"), "true")


AMB_RULES = RULES_MINI.replace(
    "[ACBuggy]\nScore = 2\nHouse = Ordos\n",
    "[ACBuggy]\nScore = 2\nHouse = Ordos\nArmour = Light\nArmour = Heavy\n"
    "StormDamage = 5\nStormDamage = 5\n",
    1).replace(
    "VeterancyLevel = 13\nExtraDamage = 50\nExtraArmour = 50",
    "VeterancyLevel = 13\nExtraDamage = 50\nExtraDamage = 99\nExtraArmour = 50\n"
    "VeterancyLevel = 40\nExtraDamage = 60", 1)


class VeterancyContextTests(Harness):
    """Categorize by ACTUAL VeterancyLevel boundaries, not key vocabulary."""

    def test_same_level_repetition_is_ambiguous_never_overwritten(self):
        data, issues = self.extract(AMB_RULES)
        buggy = self.recs(data)["ACBuggy"]
        # ExtraDamage twice INSIDE VeterancyLevel=13: explicit ambiguity,
        # first-in-block value kept in the level dict, all raw occurrences
        # preserved in order (base 25, level0 50, level0 99, level1 60).
        ambiguous = [i for i in issues if i["severity"] == "ambiguous_level_field"]
        self.assertTrue(any("ExtraDamage" in i["detail"] and "level0" in i["detail"]
                            for i in ambiguous), ambiguous)
        self.assertEqual(buggy["veterancy"][0]["extra_damage"], 50)
        self.assertEqual(buggy["veterancy"][1]["extra_damage"], 60)
        self.assertEqual(buggy["repeated_level_values"]["ExtraDamage"],
                         ["25", "50", "99", "60"])

    def test_before_any_level_conflict_is_genuine(self):
        data, issues = self.extract(AMB_RULES)
        buggy = self.recs(data)["ACBuggy"]
        self.assertTrue(any(i["severity"] == "conflicting_key" and
                            "Armour" in i["detail"] and "before any" in i["detail"]
                            for i in issues))
        # StormDamage repeats with the SAME value before any level: raw
        # occurrences kept, no conflict claimed.
        self.assertFalse(any(i["severity"] == "conflicting_key" and
                             "StormDamage" in i["detail"] for i in issues))
        self.assertEqual(buggy["repeated_values"]["StormDamage"], ["5", "5"])

    def test_across_distinct_levels_is_normal_repetition(self):
        data, issues = self.extract(AMB_RULES)
        buggy = self.recs(data)["ACBuggy"]
        normal = [i for i in issues if i["severity"] == "repeated_level_field"]
        self.assertTrue(any("ExtraDamage" in i["detail"] and "level0" in i["detail"]
                            and "level1" in i["detail"] for i in normal), normal)

    def test_ambiguity_and_override_ladder_together(self):
        data, issues = self.extract(AMB_RULES)
        buggy = self.recs(data)["ACBuggy"]
        # synthetic AMB_RULES: base 25 -> level0 50 (override), 50/99 in one
        # block (ambiguity), 99 -> level1 60 (distinct levels, normal).
        self.assertEqual(buggy["veterancy"][0]["extra_damage"], 50)
        self.assertEqual(buggy["veterancy"][1]["extra_damage"], 60)
        self.assertEqual(buggy["repeated_level_values"]["ExtraDamage"],
                         ["25", "50", "99", "60"])
        severities = {i["severity"] for i in issues}
        self.assertIn("ambiguous_level_field", severities)
        self.assertIn("repeated_level_field", severities)
        self.assertIn("conflicting_key", severities)


class MalformedAndMissingTests(Harness):
    def test_missing_house_is_null_with_issue(self):
        text = RULES_MINI.replace("[ACHarvester]\nScore = 4\nHouse = Ordos\n",
                                  "[ACHarvester]\nScore = 4\n")
        data, issues = self.extract(text)
        harv = self.recs(data)["ACHarvester"]
        self.assertIsNone(harv["house"])
        self.assertTrue(any(i["code"] == "house_missing" for i in harv["issues"]))

    def test_duplicate_section_keeps_first_and_reports(self):
        data, issues = self.extract()
        squid = self.recs(data)["ACSquid"]
        self.assertEqual(squid["cost"], 850)          # first definition wins
        self.assertIsNone(squid["house"])
        self.assertTrue(any(i["severity"] == "duplicate_section" for i in issues))

    def test_repeated_level_field_is_contextual_and_occurrences_kept(self):
        data, issues = self.extract()
        rifle = self.recs(data)["ACRifleman"]
        # base Health=600, level-1 Health=800: the archive's expected shape
        self.assertTrue(any(i["severity"] == "repeated_level_field" and
                            "Health" in i["detail"] for i in issues))
        self.assertEqual(rifle["repeated_level_values"]["Health"], ["600", "800"])
        # and it is NOT a conflicting_key
        self.assertFalse(any(i["severity"] == "conflicting_key" and
                             "ACRifleman" in i["detail"] for i in issues))

    def test_conflicting_repeated_key_outside_level_context_is_reported(self):
        data, issues = self.extract()
        buggy = self.recs(data)["ACBuggy"]
        # ACBuggy's top-level ExtraDamage precedes the veterancy block; the
        # field belongs to the level-vocabulary, so it is contextual, but the
        # values 25 vs 50 are all kept.
        self.assertEqual(buggy["repeated_level_values"]["ExtraDamage"],
                         ["25", "50"])
        self.assertEqual(buggy["veterancy"][0]["extra_damage"], 50)
        self.assertNotIn("ExtraDamage", buggy.get("repeated_values") or {})
        # ACDeathRay repeats nothing: prove conflicting_key still fires.
        text = RULES_MINI.replace(
            "[ACHarvester]\nScore = 4\n",
            "[ACHarvester]\nScore = 4\nSpeed = 5.0\nScore = 9\n")
        data2, issues2 = self.extract(text)
        harv = self.recs(data2)["ACHarvester"]
        self.assertTrue(any(i["severity"] == "conflicting_key" and
                            "ACHarvester" in i["detail"] for i in issues2))
        self.assertIn("Score", harv["repeated_values"])

    def test_dangling_declaration_is_reported(self):
        data, issues = self.extract()
        self.assertTrue(any(i["severity"] == "dangling_declaration" and
                            "ACGhostUnit" in i["detail"] for i in issues))
        # A COMMENTED declaration is absence data, not a dangling reference.
        self.assertFalse(any("ACOldUnit" in i.get("detail", "")
                             for i in issues if i["severity"] == "dangling_declaration"))
        self.assertNotIn("ACGhostUnit", self.recs(data))

    def test_commented_declaration_is_recorded_as_data_absence(self):
        data, _issues = self.extract()
        commented = data["declared"]["unit_types_commented_out"]
        self.assertEqual([c["name"] for c in commented], ["ACOldUnit"])

    def test_undeclared_house_token_is_reported(self):
        text = RULES_MINI.replace("House = Ordos\nPrimaryBuilding = ACFactory",
                                  "House = Sideways\nPrimaryBuilding = ACFactory",
                                  1)
        _data, issues = self.extract(text)
        self.assertTrue(any(i["severity"] == "undeclared_house" and
                            "Sideways" in i["detail"] for i in issues))

    def test_unresolved_weapon_ref_is_reported(self):
        text = RULES_MINI.replace("TurretAttach = ACRifleGun",
                                  "TurretAttach = ACGhostGun")
        data, issues = self.extract(text)
        rifle = self.recs(data)["ACRifleman"]
        self.assertFalse(rifle["weapon_variants"][0]["turret_found"])
        self.assertTrue(any(i["severity"] == "unresolved_ref" and
                            "ACGhostGun" in i["detail"] for i in issues))

    def test_missing_bullet_key_is_recorded_not_guessed(self):
        text = RULES_MINI.replace("[ACRifleGun]\nBullet = Rifle_B\n",
                                  "[ACRifleGun]\n//Bullet = Rifle_B\n")
        data, issues = self.extract(text)
        variant = self.recs(data)["ACRifleman"]["weapon_variants"][0]
        self.assertIsNone(variant["bullet"])
        self.assertTrue(variant["bullet_commented_out"])
        self.assertTrue(any(i["severity"] == "missing_field" and
                            "ACRifleGun" in i["detail"] for i in issues))

    def test_undeclared_versus_armour_row_is_reported(self):
        text = RULES_MINI.replace("[SmallArms_W]\nNone = 20",
                                  "[SmallArms_W]\nGhostArmour = 20\nNone = 20")
        _data, issues = self.extract(text)
        self.assertTrue(any(i["severity"] == "undeclared_armour_row" and
                            "GhostArmour" in i["detail"] for i in issues))


class CollectionCandidateTests(Harness):
    """Buildability is never proven by cost; nothing is auto-certified."""

    def test_buildable_is_production_evidence_not_certification(self):
        data, _issues = self.extract()
        recs = self.recs(data)
        rifle = recs["ACRifleman"]
        self.assertTrue(rifle["buildable"])
        self.assertEqual(rifle["buildability_rule"],
                         "primary_building_and_positive_cost")
        self.assertIsNone(rifle["balance_eligible"])
        self.assertTrue(rifle["collection_candidate"])
        self.assertIn("NOT certified", rifle["eligibility_note"])

    def test_positive_cost_without_building_is_not_buildable(self):
        data, _issues = self.extract()
        story = self.recs(data)["ACStory"]
        self.assertEqual(story["cost"], 850)
        self.assertFalse(story["buildable"])
        self.assertFalse(story["balance_eligible"])
        self.assertEqual(story["buildability_rule"], "no_production_building")
        self.assertTrue(any(i["code"] == "buildability" and "cost alone" in
                            i["detail"] for i in story["issues"]))

    def test_superweapon_is_collection_only_despite_zero_cost(self):
        data, _issues = self.extract()
        ray = self.recs(data)["ACDeathRay"]
        self.assertEqual(ray["extraction_class"], "superweapon")
        self.assertTrue(ray["collection_only"])
        self.assertFalse(ray["balance_eligible"])
        self.assertFalse(ray["buildable"])
        self.assertFalse(ray["manual_review_only"])
        self.assertTrue(any(i["code"] == "superweapon_zero_cost"
                            for i in ray["issues"]))

    def test_aispecial_alone_is_not_a_superweapon(self):
        # ACRifleman's fixture has no AiSpecial; prove the flag rule directly.
        self.assertEqual(ex.classify("ACNormal", {"AiSpecial": "TRUE"})[0], None)

    def test_economy_unit_is_manual_review_only(self):
        data, _issues = self.extract()
        harv = self.recs(data)["ACHarvester"]
        self.assertEqual(harv["extraction_class"], "economy_unit")
        self.assertTrue(harv["manual_review_only"])
        self.assertFalse(harv["balance_eligible"])
        self.assertFalse(harv["buildable"])
        self.assertEqual(harv["buildability_rule"],
                         "manual_review_only_class:economy_unit")

    def test_worm_is_wildlife(self):
        data, _issues = self.extract()
        squid = self.recs(data)["ACSquid"]
        self.assertEqual(squid["extraction_class"], "wildlife")
        self.assertTrue(squid["collection_only"])

    def test_weapon_corpus_counts_unreferenced_parts(self):
        data, _issues = self.extract()
        counts = data["counts"]
        self.assertEqual(counts["turrets"], 3)          # incl. ACUnattachedGun
        self.assertEqual(counts["unreferenced_turrets"], 1)
        self.assertEqual(counts["warheads"], 2)
        self.assertEqual(counts["unreferenced_warheads"], 0)
        self.assertEqual(counts["bullets"], 2)
        self.assertEqual(counts["superweapons"], 1)
        self.assertEqual(counts["economy_units"], 1)
        self.assertEqual(counts["commented_out_unit_declarations"], 1)

    def test_version_label_is_recorded_as_a_label(self):
        data, _issues = self.extract()
        self.assertEqual(data["counts"]["general_version_label"], "1.23")
        self.assertIn("FILE label", data["provenance"]["version_notes"][0])
        self.assertIn("archived-original/unverified patch",
                      data["provenance"]["source_kind"])

    def test_source_hashes_before_and_after(self):
        data, issues = self.extract()
        prov = data["provenance"]
        self.assertEqual(prov["sha256_before"], prov["sha256_after"])
        self.assertTrue(prov["unchanged_during_run"])
        self.assertNotIn("forced", json.dumps(issues))
        for record in data["records"]:
            self.assertTrue(record["collection_candidate"])


class OutputBoundaryTests(unittest.TestCase):
    def _fixture(self, tmp: pathlib.Path):
        source = tmp / "source"
        source.mkdir()
        (source / "Rules.txt").write_text(RULES_MINI, encoding="utf-8")
        return source

    def test_output_inside_repo_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = self._fixture(tmp)
            with self.assertRaises(SystemExit):
                ex.main(["--source", str(source), "--out",
                         str(ROOT / "corpus_dump.json")])

    def test_output_inside_source_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = self._fixture(tmp)
            with self.assertRaises(SystemExit):
                ex.main(["--source", str(source), "--out",
                         str(source / "out.json")])

    def test_output_equal_to_source_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = self._fixture(tmp)
            with self.assertRaises(SystemExit):
                ex.main(["--source", str(source), "--out", str(source / "Rules.txt")])

    def test_missing_required_arguments_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = self._fixture(tmp)
            for argv in ([], ["--source", str(source)], ["--out", str(tmp / "x")]):
                with self.subTest(argv=argv):
                    with self.assertRaises(SystemExit):
                        ex.main(argv)

    def test_stdout_mode_writes_canonical_json(self):
        import io
        context = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = self._fixture(tmp)
            real_stdout = sys.stdout
            sys.stdout = context
            try:
                code = ex.main(["--source", str(source), "--out", "-",
                                "--quiet"])
            finally:
                sys.stdout = real_stdout
            self.assertEqual(code, 0)
            payload = json.loads(context.getvalue())
            self.assertEqual(payload["counts"]["unit_records"], 6)

    def test_exclusive_creation_differing_existing_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = self._fixture(tmp)
            ext = tmp / "external"
            out = ext / "out.json"
            self.assertEqual(ex.main(["--source", str(source), "--out", str(out),
                                      "--quiet"]), 0)
            first = out.read_bytes()
            self.assertEqual(ex.main(["--source", str(source), "--out", str(out),
                                      "--quiet"]), 0)
            self.assertEqual(out.read_bytes(), first)
            out.write_bytes(b"different")
            self.assertEqual(ex.main(["--source", str(source), "--out", str(out),
                                      "--quiet"]), 3)
            self.assertEqual(out.read_bytes(), b"different")

    def test_no_force_option_exists(self):
        text = pathlib.Path(ex.__file__).read_text(encoding="utf-8")
        self.assertNotIn("--force", text)

    def test_race_never_corrupts_the_output(self):
        expected_payload_text = None
        results = []
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = self._fixture(tmp).resolve()
            out = tmp / "external" / "race.json"

            def runner():
                results.append(ex.main(["--source", str(source), "--out",
                                        str(out), "--quiet"]))

            def compute_expected():
                nonlocal expected_payload_text
                issues = []
                data = ex.extract(source, issues)
                payload = {
                    "schema_version": ex.SCHEMA_VERSION,
                    "tool": "tools/reference/extract_emperor_units.py",
                    "provenance": data["provenance"],
                    "counts": data["counts"],
                    "records": data["records"],
                    "weapons": data["weapons"],
                    "declared": data["declared"],
                    "general": data["general"],
                    "issues": sorted(issues, key=lambda i: (i.get("severity", ""),
                                                            i.get("detail", ""))),
                }
                expected_payload_text = ex.canonical_json(payload)

            compute_expected()
            threads = [threading.Thread(target=runner) for _ in range(6)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            self.assertIn(0, results)
            self.assertTrue(all(code in (0, 3) for code in results), results)
            self.assertEqual(out.read_text(encoding="utf-8"),
                             expected_payload_text)

    def test_two_runs_produce_byte_identical_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = self._fixture(tmp)
            out1, out2 = tmp / "one.json", tmp / "two.json"
            self.assertEqual(ex.main(["--source", str(source), "--out", str(out1),
                                      "--quiet"]), 0)
            self.assertEqual(ex.main(["--source", str(source), "--out", str(out2),
                                      "--quiet"]), 0)
            b1, b2 = out1.read_bytes(), out2.read_bytes()
            self.assertEqual(b1, b2)
            self.assertEqual(hashlib.sha256(b1).hexdigest(),
                             hashlib.sha256(b2).hexdigest())
            payload = json.loads(b1.decode("utf-8"))
            self.assertNotIn("generated", json.dumps(payload).lower())


@unittest.skipUnless(REAL_SOURCE and REAL_SOURCE.is_file(),
                     "set CAMEO_REFERENCE_RAW_SOURCES to opt in")
class RealSourceTests(unittest.TestCase):
    """Hand-audited native values from the archived Rules.txt (read-only)."""

    @classmethod
    def setUpClass(cls):
        cls.issues = []
        cls.data = ex.extract(REAL_SOURCE, cls.issues)
        cls.recs = {r["id"]: r for r in cls.data["records"]}

    def test_sha256_before_after_and_expected(self):
        prov = self.data["provenance"]
        self.assertEqual(prov["sha256_before"], prov["sha256_after"])
        self.assertTrue(prov["unchanged_during_run"])
        self.assertTrue(prov["sha256_matches_expected"])
        self.assertEqual(prov["sha256_after"].upper(),
                         "A1DE5044AEBC837D439892A081674CEB919007B87887ABDF999CF099FF5F692D")

    def test_roster_counts(self):
        counts = self.data["counts"]
        self.assertEqual(counts["unit_records"], 99)
        self.assertEqual(counts["superweapons"], 3)
        self.assertGreaterEqual(counts["buildable"], 50)
        self.assertEqual(counts["commented_out_unit_declarations"], 3)
        self.assertEqual(counts["general_version_label"], "1.23")

    def test_issue_categorization(self):
        severities = {i["severity"] for i in self.issues}
        self.assertIn("repeated_level_field", severities)
        self.assertIn("conflicting_key", severities)
        conflicting = [i["detail"] for i in self.issues
                       if i["severity"] == "conflicting_key"]
        # Only genuine non-level repeats survive as conflicts (Speed/…), and
        # every occurrence stays visible on the record.
        self.assertTrue(all("[ATAPC] 'Speed'" in d or "[ATKindjal] 'StormDamage'"
                            in d or "[ATOrni] 'Speed'" in d or
                            "[ATTrike] 'Speed'" in d or
                            "[HKBuzzsaw] 'Speed'" in d or
                            "[IXInfiltrator] 'ExplosionType'" in d or
                            "[ORAPC] 'Speed'" in d or
                            "[ORKobra] 'Speed'" in d for d in conflicting),
                            conflicting)
        for record in self.data["records"]:
            for key, values in (record.get("repeated_values") or {}).items():
                self.assertGreaterEqual(len(values), 2)

    def test_hkdevastator_native_values(self):
        dev = self.recs["HKDevastator"]
        self.assertEqual((dev["cost"], dev["health"]), (1750, 5000))
        self.assertEqual(dev["armour"], ["Heavy"])
        self.assertEqual(dev["house"], ["Harkonnen"])
        self.assertEqual([v["turret"] for v in dev["weapon_variants"]],
                         ["HKDevastatorGun", "HKDevastatorMissile"])
        self.assertEqual([v["bullet"] for v in dev["weapon_variants"]],
                         ["DevPlasma_B", "DevRocket_B"])
        self.assertEqual([v["reload_count"] for v in dev["weapon_variants"]],
                         [60, 80])
        self.assertEqual(dev["weapon_variants"][0]["damage"], 813)

    def test_versus_rows_survive_the_variant_chain(self):
        trooper = self.recs["HKTrooper"]
        variant = trooper["weapon_variants"][0]
        self.assertEqual(variant["turret"], "HKTrooperGun")
        self.assertEqual(variant["bullet"], "HEATInf_B")
        self.assertEqual((variant["damage"], variant["max_range"]), (375, 8))
        self.assertEqual(variant["warhead"], "HEATINF_W")
        self.assertEqual(variant["versus"]["Heavy"], 100)
        self.assertEqual(variant["versus"]["Light"], 65)

    def test_atinfantry_armour_triple_is_raw(self):
        self.assertEqual(self.recs["ATInfantry"]["armour"],
                         ["None", "50", "InfRock"])
        self.assertEqual(self.recs["ATInfantry"]["weapon_variants"][0]["bullet"],
                         "LMG_B")

    def test_economy_superweapon_story_split(self):
        self.assertEqual(self.recs["Harvester"]["extraction_class"], "economy_unit")
        self.assertTrue(self.recs["Harvester"]["manual_review_only"])
        self.assertFalse(self.recs["Harvester"]["balance_eligible"])
        self.assertEqual(self.recs["MCV"]["extraction_class"], "economy_unit")
        for sw in ("HKDeathHand", "ORBeamWeapon", "ATHawkWeapon"):
            self.assertEqual(self.recs[sw]["extraction_class"], "superweapon")
            self.assertTrue(self.recs[sw]["collection_only"])
            self.assertFalse(self.recs[sw]["balance_eligible"])
            self.assertEqual(self.recs[sw]["cost"], 0)
        self.assertEqual(self.recs["INYak"]["house"], ["Incidental"])
        self.assertFalse(self.recs["INYak"]["buildable"])
        self.assertFalse(self.recs["INYak"]["balance_eligible"])
        self.assertEqual(self.recs["INYak"]["buildability_rule"],
                         "no_production_building")

    def test_nothing_is_auto_certified(self):
        for record in self.data["records"]:
            self.assertTrue(record["collection_candidate"])
            self.assertNotEqual(record["balance_eligible"], True)

    def test_carryall_house_is_null_not_guessed(self):
        carry = self.recs["Carryall"]
        self.assertIsNone(carry["house"])
        self.assertEqual(carry["extraction_class"], "transport_unit")
        self.assertTrue(carry["manual_review_only"])

    def test_known_dangling_declarations_and_refs_are_recorded(self):
        danglings = [i["detail"] for i in self.issues
                     if i["severity"] == "dangling_declaration"]
        # IMTANK is declared uppercase while the section is [IMTank] — the
        # case mismatch is reported, never silently folded.
        self.assertIn("declared type 'IMTANK' has no definition section", danglings)
        self.assertIn("declared type 'AntiPersonnel' has no definition section",
                      danglings)
        self.assertTrue(any(i["severity"] == "unresolved_ref" for i in self.issues))


if __name__ == "__main__":
    unittest.main()
