"""Tests for tools/reference/extract_opendune_units.py.

Fixtures are SYNTHETIC (invented units, invented numbers) — no copyrighted
OpenDUNE/Westwood text is copied into the repository. Tests that assert
native values from the real raw checkout are OPT-IN via the
`CAMEO_REFERENCE_RAW_SOURCES` environment variable (pointing at the directory
containing the `opendune/` checkout) — no personal path is baked into the
tests or the tool, and the variable is absent in CI by default.
"""
import hashlib
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
sys.path.insert(0, str(ROOT / "tools" / "tests"))
import _bootstrap  # noqa: F401,E402

import extract_opendune_units as ex  # noqa: E402

# Opt-in integration fixtures: no personal directory default.
RAW_SOURCES = os.environ.get("CAMEO_REFERENCE_RAW_SOURCES")
REAL_SOURCE = pathlib.Path(RAW_SOURCES, "opendune") if RAW_SOURCES else None

# Hostile enum expressions: a crafted header must NEVER execute, only be
# reported. Call/attribute/pow/recursive-shift payloads must land as issues.
HOSTILE_H = """typedef enum Hostile {
\tH_CALL         = __import__('os').system('echo pwned'),
\tH_ATTR         = ().__class__,
\tH_POW          = 2 ** 3000000,
\tH_BIGSHIFT     = 1 << 99999,
\tH_REC_SHIFT    = 1 << (1 << 99),
\tH_FLOAT        = 1.5,
\tH_UNKNOWN      = UNDEFINED_THING,
\tH_OK_FACTOR    = 1 << 4,
\tH_NEG_SENTINEL = -1
} Hostile;
"""

UNITINFO_MINI = """/** mini table */
const uint16 g_table_actionsAI[4] = {ACTION_HUNT, ACTION_GUARD, ACTION_AMBUSH, ACTION_STOP};

UnitInfo g_table_unitInfo[UNIT_MAX] = {
\t{ /* 0 */
\t\t{ /* objectInfo */
\t\t/* stringID_abbrev      */ STR_BEAR,
\t\t/* name                 */ "Bear",
\t\t/* wsa                  */ "bear.wsa",
\t\t{ /* flags */
\t\t/* hasShadow            */ true,
\t\t/* tabSelectable        */ true,
\t\t/* priority             */ true
\t\t},
\t\t/* spawnChance          */ 0,
\t\t/* hitpoints            */ 90,
\t\t/* fogUncoverRadius     */ 2,
\t\t/* spriteID             */ 7,
\t\t/* buildCredits         */ 250,
\t\t/* buildTime            */ 50,
\t\t/* availableCampaign    */ 0,
\t\t/* structuresRequired   */ FLAG_STRUCTURE_NONE,
\t\t/* sortPriority         */ 5,
\t\t/* upgradeLevelRequired */ 0,
\t\t/* actionsPlayer        */ { ACTION_ATTACK, ACTION_MOVE, ACTION_STOP, ACTION_GUARD },
\t\t/* available            */ 0,
\t\t/* hintStringID         */ STR_NULL,
\t\t/* priorityBuild        */ 10,
\t\t/* priorityTarget       */ 10,
\t\t/* availableHouse       */ FLAG_HOUSE_ALL,
\t\t},
\t\t/* indexStart           */ 22,
\t\t/* indexEnd             */ 101,
\t\t{ /* flags */
\t\t/* isBullet             */ false,
\t\t/* isTracked            */ true,
\t\t/* isGroundUnit         */ true,
\t\t/* firesTwice           */ true,
\t\t/* isNotDeviatable      */ false,
\t\t/* isNormalUnit         */ true
\t\t},
\t\t/* dimension            */ 16,
\t\t/* movementType         */ MOVEMENT_TRACKED,
\t\t/* movingSpeedFactor    */ 30,
\t\t/* turningSpeed         */ 1,
\t\t/* fireDelay            */ 70,
\t\t/* fireDistance         */ 4,
\t\t/* damage               */ 20,
\t\t/* explosionType        */ EXPLOSION_IMPACT_MEDIUM,
\t\t/* bulletType           */ UNIT_BULLET,
\t\t/* bulletSound          */ 57
\t},

\t{ /* 1 */
\t\t{ /* objectInfo */
\t\t/* stringID_abbrev      */ STR_ZAP,
\t\t/* name                 */ "Zap",
\t\t/* wsa                  */ "zap.wsa",
\t\t{ /* flags */
\t\t/* hasShadow            */ false,
\t\t/* tabSelectable        */ false,
\t\t/* priority             */ false
\t\t},
\t\t/* spawnChance          */ 0,
\t\t/* hitpoints            */ 5,
\t\t/* fogUncoverRadius     */ 0,
\t\t/* spriteID             */ 0,
\t\t/* buildCredits         */ 999,
\t\t/* buildTime            */ 1,
\t\t/* availableCampaign    */ 0,
\t\t/* structuresRequired   */ FLAG_STRUCTURE_NONE,
\t\t/* sortPriority         */ 0,
\t\t/* upgradeLevelRequired */ 0,
\t\t/* actionsPlayer        */ { ACTION_STOP, ACTION_STOP, ACTION_STOP, ACTION_STOP },
\t\t/* available            */ 0,
\t\t/* hintStringID         */ STR_NULL,
\t\t/* priorityBuild        */ 0,
\t\t/* priorityTarget       */ 0,
\t\t/* availableHouse       */ FLAG_HOUSE_HARKONNEN | FLAG_HOUSE_ORDOS,
\t\t},
\t\t/* indexStart           */ 12,
\t\t/* indexEnd             */ 15,
\t\t{ /* flags */
\t\t/* isBullet             */ true,
\t\t/* isNormalUnit         */ false
\t\t},
\t\t/* dimension            */ 8,
\t\t/* movementType         */ MOVEMENT_WINGER,
\t\t/* movingSpeedFactor    */ 200,
\t\t/* turningSpeed         */ 2,
\t\t/* fireDelay            */ 0,
\t\t/* fireDistance         */ 9,
\t\t/* damage               */ 55,
\t\t/* explosionType        */ EXPLOSION_IMPACT_EXPLODE,
\t\t/* bulletType           */ UNIT_INVALID,
\t\t/* bulletSound          */ 42
\t}
};
"""

UNIT_H_MINI = """typedef enum UnitType {
\tUNIT_BEAR             = 0,
\tUNIT_ZAP              = 1,
\tUNIT_HARVESTER        = 2,
\tUNIT_MCV              = 3,
\tUNIT_MISSILE_HOUSE    = 4,
\tUNIT_SANDWORM         = 5,
\tUNIT_MAX              = 6,
\tUNIT_INVALID          = 0xFF
} UnitType;

typedef enum ActionType {
\tACTION_ATTACK        = 0,
\tACTION_MOVE          = 1,
\tACTION_GUARD         = 3,
\tACTION_STOP          = 7,
\tACTION_HUNT          = 11,
\tACTION_INVALID       = 0xFF
} ActionType;

typedef enum MovementType {
\tMOVEMENT_FOOT        = 0,
\tMOVEMENT_TRACKED     = 1,
\tMOVEMENT_WINGER      = 4
} MovementType;
"""

HOUSE_H_MINI = """typedef enum HouseType {
\tHOUSE_HARKONNEN = 0,
\tHOUSE_ATREIDES  = 1,
\tHOUSE_ORDOS     = 2,
\tHOUSE_MAX       = 3,
\tHOUSE_INVALID   = 0xFF
} HouseType;

typedef enum HouseFlag {
\tFLAG_HOUSE_HARKONNEN    = 1 << HOUSE_HARKONNEN,
\tFLAG_HOUSE_ATREIDES     = 1 << HOUSE_ATREIDES,
\tFLAG_HOUSE_ORDOS        = 1 << HOUSE_ORDOS,
\tFLAG_HOUSE_ALL          = FLAG_HOUSE_ORDOS | FLAG_HOUSE_ATREIDES | FLAG_HOUSE_HARKONNEN
} HouseFlag;
"""

HOUSEINFO_MINI = """const HouseInfo g_table_houseInfo[HOUSE_MAX] = {
\t{ /* 0 */
\t\t/* name                 */ "Dark",
\t\t/* toughness            */ 200,
\t\t/* specialCountDown     */ 600,
\t\t/* specialWeapon        */ 1,
\t\t/* voiceFilename        */ "dark.voc"
\t}
};
"""

STRUCTURE_H_MINI = """typedef enum StructureType {
\tSTRUCTURE_SLAB_1x1          = 0,
\tSTRUCTURE_HOUSE_OF_IX       = 6
} StructureType;

typedef enum StructureFlag {
\tFLAG_STRUCTURE_SLAB_1x1          = 1 << STRUCTURE_SLAB_1x1,
\tFLAG_STRUCTURE_HOUSE_OF_IX       = 1 << STRUCTURE_HOUSE_OF_IX,
\tFLAG_STRUCTURE_NONE              = 0
} StructureFlag;
"""


def write_fixture(root: pathlib.Path, unitinfo=UNITINFO_MINI, unit_h=UNIT_H_MINI):
    (root / "src" / "table").mkdir(parents=True)
    (root / "src" / "table" / "unitinfo.c").write_text(unitinfo, encoding="utf-8")
    (root / "src" / "table" / "houseinfo.c").write_text(HOUSEINFO_MINI, encoding="utf-8")
    (root / "src" / "unit.h").write_text(unit_h, encoding="utf-8")
    (root / "src" / "house.h").write_text(HOUSE_H_MINI, encoding="utf-8")
    (root / "src" / "structure.h").write_text(STRUCTURE_H_MINI, encoding="utf-8")


def extract_fixture(root: pathlib.Path):
    issues = []
    data = ex.extract(root, issues)
    return data, issues


def serious(issues):
    """Issues other than the expected no-.git provenance gap of a fixture."""
    return [i for i in issues if i["severity"] != "provenance_unverified"]


class NoExecutionGuardTests(unittest.TestCase):
    """Downloaded source must never be executed — eval/exec must not exist."""

    def test_tool_source_contains_no_eval_or_exec(self):
        text = pathlib.Path(ex.__file__).read_text(encoding="utf-8")
        self.assertNotIn("eval(", text)
        self.assertNotIn("exec(", text)

    def test_hostile_enum_expressions_are_reported_never_run(self):
        hostile_names = ("H_CALL", "H_ATTR", "H_POW", "H_BIGSHIFT",
                         "H_REC_SHIFT", "H_FLOAT", "H_UNKNOWN")
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            marker = root / "pwned_proof"
            header = root / "hostile.h"
            header.write_text(HOSTILE_H, encoding="utf-8")
            issues = []
            enums = ex.parse_enums(header, issues)
            failures = [i for i in issues
                        if i["severity"] == "unresolved_enum_value"]
            self.assertEqual(len(failures), len(hostile_names), issues)
            joined = " ".join(i["detail"] for i in failures)
            for name in hostile_names:
                self.assertIn(name, joined)
            # The benign members still evaluated under the whitelist.
            hostile = enums.get("Hostile", {})
            self.assertEqual(hostile.get("H_OK_FACTOR"), 16)
            self.assertEqual(hostile.get("H_NEG_SENTINEL"), -1)
            for name in hostile_names:
                self.assertNotIn(name, hostile)
            self.assertFalse(marker.exists(), "side effect executed!")


SEQ_CHAIN_H = "typedef enum Seq { A = 1, B = UNKNOWN, C, D = 7, E } Seq;\n"
SEQ_CHAIN_MULTILINE_H = """typedef enum Seq {
\tA = 1,
\tB = UNDEFINED,
\tC,
\tD = 7,
\tE
} Seq;
"""


class ChainSemanticsTests(unittest.TestCase):
    """An unresolved explicit value invalidates the implicit chain until a
    valid explicit reset; withheld members keep the chain invalid."""

    def _parse(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            header = pathlib.Path(tmp) / "seq.h"
            header.write_text(text, encoding="utf-8")
            issues = []
            enums = ex.parse_enums(header, issues)
            return enums, issues

    def test_chain_invalidated_until_explicit_reset(self):
        enums, issues = self._parse(SEQ_CHAIN_H)
        seq = enums["Seq"]
        self.assertEqual(seq["A"], 1)
        self.assertNotIn("B", seq)          # unresolved explicit: no value
        self.assertNotIn("C", seq)          # implicit successor WITHHELD
        self.assertEqual(seq["D"], 7)       # valid explicit resets the chain
        self.assertEqual(seq["E"], 8)       # successor of a valid explicit
        severities = {i["severity"] for i in issues}
        self.assertIn("unresolved_enum_value", severities)
        self.assertIn("implicit_successor_withheld", severities)

    def test_multiline_chain_same_semantics(self):
        enums, issues = self._parse(SEQ_CHAIN_MULTILINE_H)
        seq = enums["Seq"]
        self.assertEqual(seq["A"], 1)
        self.assertNotIn("B", seq)
        self.assertNotIn("C", seq)
        self.assertEqual(seq["D"], 7)
        self.assertEqual(seq["E"], 8)
        self.assertEqual(sum(1 for i in issues
                             if i["severity"] == "implicit_successor_withheld"), 1)

    def test_withholding_propagates_until_explicit(self):
        text = "typedef enum Seq { A = 1, B = UNDEF, C, D, E = 5, F } Seq;\n"
        enums, issues = self._parse(text)
        seq = enums["Seq"]
        self.assertEqual(seq["A"], 1)
        self.assertNotIn("B", seq)
        self.assertNotIn("C", seq)
        self.assertNotIn("D", seq)          # still chained to a withheld value
        self.assertEqual(seq["E"], 5)
        self.assertEqual(seq["F"], 6)       # implicit successor of E=5
        withheld = [i for i in issues if i["severity"] == "implicit_successor_withheld"]
        self.assertEqual(len(withheld), 2)  # C and D; E=5 ends the chain defect


class EvaluatorUnitTests(unittest.TestCase):
    def test_allowed_shapes(self):
        visible = {"A": 1, "B": 2, "UNIT_X": 4, "MAX": ex._INT_LIMIT}
        self.assertEqual(ex.eval_enum_expr("A | B", visible, "E", "K"), 3)
        self.assertEqual(ex.eval_enum_expr("1 << UNIT_X", visible, "E", "K"), 16)
        self.assertEqual(ex.eval_enum_expr("-1", visible, "E", "K"), -1)
        self.assertEqual(ex.eval_enum_expr("0xFF", visible, "E", "K"), 255)
        self.assertEqual(ex.eval_enum_expr("(A + B) & 3", visible, "E", "K"), 3)

    def test_disallowed_shapes(self):
        cases = ["open(1)", "().__class__", "A.inf", "2 ** 30", "A[0]",
                 "1 << 99999", "1 << (1 << 99)", "1.5", "UNKNOWN", "lambda: 1",
                 "1+" * 60 + "1"]
        for expr in cases:
            with self.subTest(expr=expr):
                with self.assertRaises(ex.EnumExpressionError):
                    ex.eval_enum_expr(expr, {"A": 1, "B": 2}, "E", "K")

    def test_bound_applies_to_constants_names_unary_and_binary(self):
        limit = ex._INT_LIMIT
        forbidden = ex.EnumExpressionError
        # constants
        self.assertEqual(ex.eval_enum_expr(str(limit), {}, "E", "K"), limit)
        with self.assertRaises(forbidden):
            ex.eval_enum_expr(str(limit + 1), {}, "E", "K")
        # names
        with self.assertRaises(forbidden):
            ex.eval_enum_expr("BIG", {"BIG": limit + 1}, "E", "K")
        self.assertEqual(ex.eval_enum_expr("MAX", {"MAX": limit}, "E", "K"), limit)
        # unary
        with self.assertRaises(forbidden):
            ex.eval_enum_expr(f"-({limit + 1})", {}, "E", "K")
        self.assertEqual(ex.eval_enum_expr(f"-{limit}", {}, "E", "K"), -limit)
        with self.assertRaises(forbidden):
            ex.eval_enum_expr(f"-(-({limit + 1}))", {}, "E", "K")
        # binary results
        self.assertEqual(ex.eval_enum_expr("MAX + 0", {"MAX": limit}, "E", "K"),
                         limit)
        with self.assertRaises(forbidden):
            ex.eval_enum_expr("MAX + 1", {"MAX": limit}, "E", "K")
        with self.assertRaises(forbidden):
            ex.eval_enum_expr("0 - (0 - (BIG + 2))", {"BIG": limit - 1}, "E", "K")

    def test_shift_boundaries(self):
        self.assertEqual(ex.eval_enum_expr("1 << 32", {}, "E", "K"), 1 << 32)
        with self.assertRaises(ex.EnumExpressionError):
            ex.eval_enum_expr("1 << 33", {}, "E", "K")
        with self.assertRaises(ex.EnumExpressionError):
            ex.eval_enum_expr("1 << -1", {}, "E", "K")


class ParserShapeTests(unittest.TestCase):
    """The parser reproduces the native field shape of a table entry."""

    def test_native_fields_are_extracted_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root)
            data, issues = extract_fixture(root)
            self.assertEqual(serious(issues), [])
            bear = data["records"][0]
            self.assertEqual(bear["name"], "Bear")
            self.assertEqual(bear["hp"], 90)
            self.assertEqual(bear["cost"], 250)
            self.assertEqual(bear["speed"], 30)
            self.assertEqual(bear["fire_delay"], 70)
            self.assertEqual(bear["damage"], 20)
            self.assertEqual(bear["range"], 4)
            self.assertEqual(bear["movement_type"], "MOVEMENT_TRACKED")
            self.assertEqual(bear["turn_speed"], 1)
            self.assertEqual(bear["unit_flags"]["firesTwice"], True)
            self.assertEqual(bear["object_flags"]["hasShadow"], True)
            self.assertEqual(bear["available_house_default"], ["FLAG_HOUSE_ALL"])
            self.assertEqual(bear["available_house_resolved"],
                             ["FLAG_HOUSE_HARKONNEN", "FLAG_HOUSE_ATREIDES",
                              "FLAG_HOUSE_ORDOS"])
            self.assertEqual(bear["actions_player"],
                             ["ACTION_ATTACK", "ACTION_MOVE", "ACTION_STOP",
                              "ACTION_GUARD"])
            self.assertEqual(bear["structures_required"], ["FLAG_STRUCTURE_NONE"])

    def test_inline_action_list_is_a_list_not_a_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root)
            data, _issues = extract_fixture(root)
            self.assertIsInstance(data["records"][0]["actions_player"], list)
            self.assertEqual(len(data["records"][0]["actions_player"]), 4)

    def test_row_boundaries_are_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root)
            data, _issues = extract_fixture(root)
            self.assertEqual(data["records"][0]["index_start"], 22)
            self.assertEqual(data["records"][0]["index_end"], 101)
            self.assertEqual(data["records"][1]["index_start"], 12)
            self.assertEqual(data["records"][1]["index_end"], 15)
            self.assertEqual(data["records"][0]["index"], 0)
            self.assertEqual(data["records"][1]["index"], 1)


class MalformedAndMissingTests(unittest.TestCase):
    def test_missing_build_credits_is_recorded_not_fatal(self):
        mini = UNITINFO_MINI.replace("\t\t/* buildCredits         */ 250,\n", "")
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root, unitinfo=mini)
            data, issues = extract_fixture(root)
            self.assertEqual(len(data["records"]), 2)
            self.assertIn("buildCredits_missing", data["records"][0]["issues"])
            self.assertIsNone(data["records"][0]["cost"])
            self.assertEqual(serious(issues), [])

    def test_duplicate_field_keeps_first_and_reports(self):
        mini = UNITINFO_MINI.replace(
            "\t\t/* hitpoints            */ 90,\n",
            "\t\t/* hitpoints            */ 90,\n\t\t/* hitpoints            */ 77,\n")
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root, unitinfo=mini)
            data, issues = extract_fixture(root)
            self.assertEqual(data["records"][0]["hp"], 90)
            self.assertTrue(any(i["severity"] == "duplicate_field" and
                                i["field"] == "hitpoints" for i in issues))

    def test_unbalanced_brace_is_reported_not_fatal(self):
        mini = UNITINFO_MINI.replace("\t\t/* bulletSound          */ 57\n\t},", "")
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root, unitinfo=mini)
            data, issues = extract_fixture(root)
            self.assertTrue(any(i["severity"] == "malformed_source" for i in issues))
            self.assertGreaterEqual(len(data["records"]), 1)

    def test_unterminated_comment_is_reported(self):
        mini = UNITINFO_MINI.replace(
            "\t\t/* bulletSound          */ 42\n\t}\n};",
            "\t\t/* bulletSound          */ 42\n\t}\n/* dangling comment\n};")
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root, unitinfo=mini)
            data, issues = extract_fixture(root)
            self.assertTrue(any("unterminated comment" in i["detail"]
                                for i in issues if i["severity"] == "malformed_source"))
            self.assertEqual(len(data["records"]), 2)

    def test_missing_source_file_aborts_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "unit.h").write_text(UNIT_H_MINI, encoding="utf-8")
            issues = []
            self.assertIsNone(ex.extract(root, issues))
            self.assertTrue(any(i["severity"] == "source_missing" for i in issues))

    def test_unresolved_flag_token_is_an_issue(self):
        mini = UNITINFO_MINI.replace(
            "/* availableHouse       */ FLAG_HOUSE_ALL,",
            "/* availableHouse       */ FLAG_HOUSE_ALL | FLAG_HOUSE_GHOST,")
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root, unitinfo=mini)
            _data, issues = extract_fixture(root)
            self.assertTrue(any(i["severity"] == "unresolved_flag" and
                                "FLAG_HOUSE_GHOST" in i["detail"] for i in issues))


class CollectionCandidateTests(unittest.TestCase):
    """NO auto-certified balance eligibility — every record is a candidate."""

    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root)
            cls.data, _issues = extract_fixture(root)
        cls.recs = {r["index"]: r for r in cls.data["records"]}

    def test_normal_unit_is_candidate_only_not_certified(self):
        bear = self.recs[0]
        self.assertEqual(bear["extraction_class"], "unit")
        self.assertTrue(bear["collection_candidate"])
        self.assertIsNone(bear["balance_eligible"])
        self.assertIn("NOT certified", bear["eligibility_note"])

    def test_bullet_is_projectile_even_when_priced(self):
        # index 1 carries buildCredits=999 AND isBullet=true: it stays a
        # projectile — cost > 0 is never a buildability or eligibility proof.
        zap = self.recs[1]
        self.assertEqual(zap["extraction_class"], "projectile")
        self.assertFalse(zap["balance_eligible"])
        self.assertTrue(zap["collection_only"])
        self.assertFalse(zap["manual_review_only"])

    def test_economy_units_are_manual_review_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            extra = """
\t{ /* 2 */
\t\t{ /* objectInfo */
\t\t/* name                 */ "Digger",
\t\t{ /* flags */
\t\t/* hasShadow            */ false
\t\t},
\t\t/* hitpoints            */ 150,
\t\t/* buildCredits         */ 300,
\t\t/* availableHouse       */ FLAG_HOUSE_ALL,
\t\t},
\t\t{ /* flags */
\t\t/* isNormalUnit         */ true
\t\t},
\t\t/* movementType         */ MOVEMENT_TRACKED,
\t\t/* movingSpeedFactor    */ 20,
\t\t/* fireDelay            */ 0,
\t\t/* fireDistance         */ 0,
\t\t/* damage               */ 0,
\t\t/* bulletType           */ UNIT_INVALID
\t},

\t{ /* 3 */
\t\t{ /* objectInfo */
\t\t/* name                 */ "Factoryvan",
\t\t{ /* flags */
\t\t/* hasShadow            */ false
\t\t},
\t\t/* hitpoints            */ 150,
\t\t/* buildCredits         */ 900,
\t\t/* availableHouse       */ FLAG_HOUSE_ALL,
\t\t},
\t\t{ /* flags */
\t\t/* isNormalUnit         */ true
\t\t},
\t\t/* movementType         */ MOVEMENT_TRACKED,
\t\t/* movingSpeedFactor    */ 20,
\t\t/* fireDelay            */ 0,
\t\t/* fireDistance         */ 0,
\t\t/* damage               */ 0,
\t\t/* bulletType           */ UNIT_INVALID
\t}
};
"""
            write_fixture(root, unitinfo=UNITINFO_MINI.replace("};", extra))
            data, _issues = extract_fixture(root)
            recs = {r["index"]: r for r in data["records"]}
            self.assertEqual(recs[2]["unit_type"], "UNIT_HARVESTER")
            self.assertEqual(recs[2]["extraction_class"], "economy_unit")
            self.assertFalse(recs[2]["balance_eligible"])
            self.assertTrue(recs[2]["manual_review_only"])
            self.assertEqual(recs[3]["unit_type"], "UNIT_MCV")
            self.assertTrue(recs[3]["manual_review_only"])

    def test_house_missile_is_superweapon_and_sandworm_wildlife(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            extra = """
\t{ /* 4 */
\t\t{ /* objectInfo */
\t\t/* name                 */ "BigOne",
\t\t{ /* flags */
\t\t/* isBullet             */ true
\t\t},
\t\t/* hitpoints            */ 70,
\t\t/* buildCredits         */ 0,
\t\t/* availableHouse       */ FLAG_HOUSE_HARKONNEN,
\t\t},
\t\t{ /* flags */
\t\t/* isNormalUnit         */ false
\t\t},
\t\t/* movementType         */ MOVEMENT_WINGER,
\t\t/* movingSpeedFactor    */ 250,
\t\t/* fireDelay            */ 0,
\t\t/* fireDistance         */ 15,
\t\t/* damage               */ 100,
\t\t/* bulletType           */ UNIT_INVALID
\t},

\t{ /* 5 */
\t\t{ /* objectInfo */
\t\t/* name                 */ "Sandworm",
\t\t{ /* flags */
\t\t/* hasShadow            */ false
\t\t},
\t\t/* hitpoints            */ 1000,
\t\t/* buildCredits         */ 0,
\t\t/* availableHouse       */ FLAG_HOUSE_ATREIDES,
\t\t},
\t\t{ /* flags */
\t\t/* isNormalUnit         */ false
\t\t},
\t\t/* movementType         */ MOVEMENT_SLITHER,
\t\t/* movingSpeedFactor    */ 35,
\t\t/* fireDelay            */ 20,
\t\t/* fireDistance         */ 0,
\t\t/* damage               */ 300,
\t\t/* bulletType           */ UNIT_SANDWORM
\t}
};
"""
            write_fixture(root, unitinfo=UNITINFO_MINI.replace("};", extra))
            data, _issues = extract_fixture(root)
            recs = {r["index"]: r for r in data["records"]}
            self.assertEqual(recs[4]["unit_type"], "UNIT_MISSILE_HOUSE")
            self.assertEqual(recs[4]["extraction_class"], "superweapon_missile")
            self.assertTrue(recs[4]["collection_only"])
            self.assertEqual(recs[5]["extraction_class"], "wildlife")
            self.assertTrue(recs[5]["collection_only"])


class OutputBoundaryTests(unittest.TestCase):
    """Output goes to stdout or EXTERNAL paths only — repo/source guarded."""

    def test_output_inside_repo_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root)
            bad = ROOT / "corpus_dump.json"   # inside the repo
            with self.assertRaises(SystemExit):
                ex.main(["--source", str(root), "--out", str(bad)])

    def test_output_inside_source_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root)
            bad = root / "out.json"           # inside the source tree
            with self.assertRaises(SystemExit):
                ex.main(["--source", str(root), "--out", str(bad)])

    def test_output_equal_to_source_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root)
            with self.assertRaises(SystemExit):
                ex.main(["--source", str(root), "--out",
                         str(root / "src" / "unit.h")])

    def test_missing_required_arguments_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root)
            for argv in ([], ["--source", str(root)],
                         ["--out", str(pathlib.Path(tmp) / "x.json")]):
                with self.subTest(argv=argv):
                    with self.assertRaises(SystemExit):
                        ex.main(argv)

    def test_stdout_mode_writes_canonical_json(self):
        import io
        context = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root)
            real_stdout = sys.stdout
            sys.stdout = context
            try:
                code = ex.main(["--source", str(root), "--out", "-",
                                "--quiet"])
            finally:
                sys.stdout = real_stdout
            self.assertEqual(code, 0)
            payload = json.loads(context.getvalue())
            self.assertEqual(payload["counts"]["unit_records"], 2)
            self.assertIn("provenance", payload)

    def test_exclusive_creation_differing_existing_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = tmp / "source"
            source.mkdir()
            write_fixture(source)
            ext = tmp / "external"
            out = ext / "out.json"
            self.assertEqual(ex.main(["--source", str(source), "--out", str(out),
                                      "--quiet"]), 0)
            first = out.read_bytes()
            # second run with identical content: no-op success, not a rewrite
            self.assertEqual(ex.main(["--source", str(source), "--out", str(out),
                                      "--quiet"]), 0)
            self.assertEqual(out.read_bytes(), first)
            # differing existing content: refusal, original untouched
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
            source = tmp / "source"
            source.mkdir()
            write_fixture(source)
            out = tmp / "external" / "race.json"

            def runner():
                results.append(ex.main(["--source", str(source), "--out",
                                        str(out), "--quiet"]))

            def compute_expected():
                nonlocal expected_payload_text
                issues = []
                data = ex.extract(source.resolve(), issues)
                payload = {
                    "schema_version": ex.SCHEMA_VERSION,
                    "tool": "tools/reference/extract_opendune_units.py",
                    "provenance": data["provenance"],
                    "counts": data["counts"],
                    "records": data["records"],
                    "houses": data["houses"],
                    "enums": data["enums"],
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
            # One O_EXCL creator wins; identical-content losers are no-ops,
            # partial-write losers refuse — never corruption.
            self.assertIn(0, results)
            self.assertTrue(all(code in (0, 3) for code in results), results)
            self.assertEqual(out.read_text(encoding="utf-8"),
                             expected_payload_text)


class DeterminismTests(unittest.TestCase):
    def test_two_runs_produce_byte_identical_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            source = tmp / "source"
            source.mkdir()
            write_fixture(source)
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


@unittest.skipUnless(REAL_SOURCE and REAL_SOURCE.is_dir(),
                     "set CAMEO_REFERENCE_RAW_SOURCES to opt in")
class RealSourceTests(unittest.TestCase):
    """Hand-audited native values from the raw checkout (read-only)."""

    @classmethod
    def setUpClass(cls):
        cls.issues = []
        cls.data = ex.extract(REAL_SOURCE, cls.issues)
        cls.recs = {r["index"]: r for r in cls.data["records"]}

    def test_commit_and_tree_verification(self):
        git = self.data["provenance"]["git"]
        self.assertTrue(git["available"])
        self.assertEqual(git["head"], ex.DECLARED_COMMIT)
        self.assertTrue(git["head_matches_declared"])
        self.assertFalse(git["checkout_dirty"])
        self.assertEqual(git["parsed_files_dirty"], [])

    def test_source_hashes_before_after_and_vs_head(self):
        for entry in self.data["provenance"]["files"]:
            self.assertTrue(entry["unchanged_during_run"])
            self.assertTrue(entry["matches_head"])
        self.assertEqual(self.issues, [])

    def test_table_shape_matches_unit_max(self):
        self.assertEqual(len(self.data["records"]), 27)
        self.assertEqual(self.data["counts"]["declared_unit_max"], 27)

    def test_first_and_last_entries(self):
        self.assertEqual(self.recs[0]["unit_type"], "UNIT_CARRYALL")
        self.assertEqual(self.recs[26]["unit_type"], "UNIT_FRIGATE")
        self.assertEqual(self.recs[26]["extraction_class"], "starport_transport")

    def test_native_infantry_and_tank_values(self):
        inf = self.recs[2]
        self.assertEqual((inf["hp"], inf["cost"], inf["fire_delay"],
                          inf["damage"], inf["range"]), (50, 100, 45, 3, 2))
        self.assertEqual((inf["index_start"], inf["index_end"]), (22, 101))
        tank = self.recs[9]
        self.assertEqual((tank["hp"], tank["cost"], tank["fire_delay"],
                          tank["damage"], tank["range"]), (200, 300, 80, 25, 4))
        self.assertEqual(tank["available_house_default"], ["FLAG_HOUSE_ALL"])
        self.assertEqual(len(tank["available_house_resolved"]), 6)

    def test_economy_superweapon_projectile_split(self):
        self.assertEqual(self.recs[16]["extraction_class"], "economy_unit")
        self.assertTrue(self.recs[16]["manual_review_only"])
        self.assertTrue(self.recs[16]["collection_only"])  # collected, manual only
        self.assertFalse(self.recs[16]["balance_eligible"])
        self.assertEqual(self.recs[17]["extraction_class"], "economy_unit")
        self.assertEqual(self.recs[18]["extraction_class"], "superweapon_missile")
        for idx in (19, 20, 21, 22, 23):
            self.assertEqual(self.recs[idx]["extraction_class"], "projectile")
        self.assertEqual(self.recs[24]["extraction_class"], "special")
        self.assertEqual(self.recs[25]["extraction_class"], "wildlife")

    def test_static_records_stay_collection_candidates(self):
        for record in self.data["records"]:
            self.assertTrue(record["collection_candidate"])
            self.assertIn("balance_eligible", record)

    def test_houses_and_special_weapon_axis(self):
        houses = {h["name"]: h for h in self.data["houses"]}
        self.assertEqual(len(houses), 6)
        self.assertEqual(houses["Harkonnen"]["special_countdown"], 600)
        self.assertEqual(houses["Atreides"]["special_weapon"], "2")


if __name__ == "__main__":
    unittest.main()
