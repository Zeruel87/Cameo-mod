"""Regression tests for audit_dead_warhead_fields.py.

Every fixture is a minimal fake repository — tiny C# source roots plus a stub Model — so the
suite is cheap and never touches the real ruleset. The original defects are reproduced as
BEHAVIOUR (exit codes, emitted json), never as implementation strings:

  - source paths were CWD-relative and ignored --root: run from any other directory the
    field index came back EMPTY and the audit answered "OK — every warhead field is read";
  - missing assembly sources produced those empty indexes just as silently (same false OK);
  - unresolved warhead types were skipped silently and still allowed success;
  - an unknown base class silently ended the inherited-field walk, so a partial field set
    was trusted (false dead verdicts possible);
  - a scan that was NOT trustworthy (unresolved types, broken chains, cycles, unreadable
    sources) rewrote --json, so partial results could masquerade as current — now only a
    completed trustworthy scan writes the mapping (a clean scan resets stale output to {}).
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

import _bootstrap  # noqa: F401 — sys.path side effect

import audit_dead_warhead_fields as audit

# --- minimal C# fixtures --------------------------------------------------- #
# Mirrors the real layout: CA/Cameo vendored at the repo root, AS/Common/Cnc/D2k
# under the engine checkout. Warhead's base IWarhead lives outside every scanned
# assembly (OpenRA.Game) and is the audit's one safe non-object terminal.

CAMEO_CS = "namespace OpenRA.Mods.Cameo {\n}\n"
CNC_CS = "namespace OpenRA.Mods.Cnc {\n}\n"
D2K_CS = "namespace OpenRA.Mods.D2k {\n}\n"

COMMON_CS = """namespace OpenRA.Mods.Common.Warheads {
	public abstract class Warhead : IWarhead {
	}

	public abstract class DamageWarhead : Warhead {
		public readonly int Damage = 0;

		public int Spread;  // mutable public — FieldLoader reads it too
	}
}
"""

AS_CS = """namespace OpenRA.Mods.AS.Warheads {
	public class CreateTintedCellsWarhead : DamageWarhead {
		public int Level = 100;

		[FieldLoader.Ignore]
		public readonly int Ignored = 0;
	}

	public class ShadowWarhead : DamageWarhead {
		public readonly int FromAS = 0;
	}
}
"""

CA_CS = """namespace OpenRA.Mods.CA.Warheads {
	public class AreaDamageWarhead : DamageWarhead {
		public readonly int Radius = 0;
	}

	public class ShadowWarhead : DamageWarhead {
		public readonly int FromCA = 0;
	}

	public class GhostWarhead : NoSuchBaseAnywhere {
		public readonly int Own = 0;
	}

	public class CycleA : CycleB {
		public readonly int FromA = 0;
	}

	public class CycleB : CycleA {
		public readonly int FromB = 0;
	}

	public class ContinuationWarhead :
		DamageWarhead
	{
		public readonly int Own = 0;
	}
}
"""


def write_cs(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_repo_assemblies(root: pathlib.Path) -> None:
    """The two assemblies vendored at the repository root."""
    write_cs(root / "OpenRA.Mods.CA" / "Warheads" / "ca.cs", CA_CS)
    write_cs(root / "OpenRA.Mods.Cameo" / "cameo.cs", CAMEO_CS)


def write_engine_assemblies(engine: pathlib.Path) -> pathlib.Path:
    """The four engine-checkout assemblies; returns the engine root."""
    write_cs(engine / "OpenRA.Mods.AS" / "Warheads" / "as.cs", AS_CS)
    write_cs(engine / "OpenRA.Mods.Common" / "Warheads" / "common.cs", COMMON_CS)
    write_cs(engine / "OpenRA.Mods.Cnc" / "cnc.cs", CNC_CS)
    write_cs(engine / "OpenRA.Mods.D2k" / "d2k.cs", D2K_CS)
    return engine


# --- stub Model ------------------------------------------------------------ #

class Yaml:
    """Stand-in for a miniyaml Node: only key/value/children are consulted."""

    def __init__(self, key, value=None, children=()):
        self.key = key
        self.value = value
        self.children = list(children)


class FakeRuleset:
    def __init__(self, weapons):
        self._weapons = dict(weapons)
        self.weapons = list(weapons)

    def resolve_weapon(self, name):
        return self._weapons.get(name)


@contextlib.contextmanager
def stub_model(ruleset):
    class FakeModel:
        def __init__(self, root):
            self.rs = ruleset
    with mock.patch.object(audit, "Model", FakeModel):
        yield


def warhead_node(suffix, wtype, keys):
    return Yaml(f"Warhead@{suffix}", wtype, [Yaml(k, "0") for k in keys])


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ParseTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        write_repo_assemblies(self.root)
        self.engine = write_engine_assemblies(self.root / "engine")

    def test_mutable_public_field_is_recognized(self):
        # CreateTintedCellsWarhead declares `public int Level = 100;` — matching only
        # readonly once reported 45 live radiation settings as dead.
        fields = audit.parse_assembly(self.engine / "OpenRA.Mods.AS")
        self.assertIn("Level", fields["CreateTintedCellsWarhead"][1])

    def test_fieldloader_ignore_is_skipped(self):
        fields = audit.parse_assembly(self.engine / "OpenRA.Mods.AS")
        self.assertNotIn("Ignored", fields["CreateTintedCellsWarhead"][1])

    def test_class_without_base_is_parsed_with_none_base(self):
        src = self.root / "OpenRA.Mods.CA" / "Warheads" / "loner.cs"
        write_cs(src, "namespace X {\n\tpublic class Loner {\n\t\tpublic int A;\n\t}\n}\n")
        fields = audit.parse_assembly(src.parent)
        self.assertEqual(fields["Loner"], (None, {"A"}))
        # A class with truly no inheritance is a VALID terminal — never flagged incomplete.
        got = audit.resolve_fields(audit.build_index(self.root), "Loner")
        self.assertIsNotNone(got)
        self.assertTrue(got[2])

    def test_keyword_prefix_type_name_is_a_field(self):
        # A type merely NAMED like a keyword prefix must not be dropped as a field —
        # dropping it would make every yaml use of it look dead.
        src = self.root / "OpenRA.Mods.CA" / "Warheads" / "kwprefix.cs"
        write_cs(src, "namespace X {\n\tpublic class Kw {\n\t\tpublic eventPayload Thing;\n"
                      "\t\tpublic eventishCount Count = 0;\n\t}\n}\n")
        fields = audit.parse_assembly(src.parent)["Kw"][1]
        self.assertEqual(fields, {"Thing", "Count"})

    def test_real_keyword_declarations_are_excluded(self):
        src = self.root / "OpenRA.Mods.CA" / "Warheads" / "keywords.cs"
        write_cs(src, "namespace X {\n\tpublic class Kw {\n"
                      "\t\tpublic static int S = 0;\n"
                      "\t\tpublic const int C = 0;\n"
                      "\t\tpublic event System.EventHandler Boom;\n"
                      "\t\tpublic delegate void Handler(int x);\n"
                      "\t\tpublic struct Inner { }\n"
                      "\t}\n}\n")
        self.assertEqual(audit.parse_assembly(src.parent)["Kw"][1], set())


class IndexAndResolveTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        write_repo_assemblies(self.root)
        self.engine = write_engine_assemblies(self.root / "engine")

    def test_build_index_roots_at_root_argument(self):
        index = audit.build_index(self.root)
        self.assertIn("AreaDamageWarhead", index["CA"])

    def test_build_index_default_resolves_from_cwd(self):
        # Historical default contract: with no arguments the paths resolve from the CWD.
        old = os.getcwd()
        self.addCleanup(os.chdir, old)
        os.chdir(self.root)
        index = audit.build_index()
        self.assertIn("CreateTintedCellsWarhead", index["AS"])

    def test_missing_assemblies_names_the_absent_engine_dirs(self):
        # Repo-root assemblies only; engine checkout absent entirely.
        shutil.rmtree(self.root / "engine")
        missing = dict(audit.missing_assemblies(self.root))
        self.assertEqual(set(missing), {"AS", "Cnc", "D2k", "Common"})
        self.assertNotIn("CA", missing)

    def test_missing_assemblies_empty_on_complete_repo(self):
        self.assertEqual(audit.missing_assemblies(self.root), [])

    def test_precedence_first_assembly_wins(self):
        index = audit.build_index(self.root)
        got = audit.resolve_fields(index, "ShadowWarhead")
        self.assertIsNotNone(got)
        fields, asm, complete = got
        self.assertEqual(asm, "AS")
        self.assertIn("FromAS", fields)
        self.assertNotIn("FromCA", fields)
        self.assertTrue(complete)

    def test_chain_through_iwarhead_terminal_is_complete(self):
        index = audit.build_index(self.root)
        got = audit.resolve_fields(index, "AreaDamageWarhead")
        fields, _asm, complete = got
        self.assertTrue(complete)
        # Own field plus the whole inherited chain (DamageWarhead, Warhead).
        self.assertLessEqual({"Radius", "Damage", "Spread"}, fields)

    def test_unknown_base_makes_chain_incomplete(self):
        index = audit.build_index(self.root)
        got = audit.resolve_fields(index, "GhostWarhead")
        _fields, _asm, complete = got
        self.assertFalse(complete)

    def test_inheritance_cycle_is_incomplete(self):
        # A -> B -> A: the old walk exited the cycle with complete=True, trusting a
        # field set it could not verify. Now: incomplete.
        index = audit.build_index(self.root)
        got = audit.resolve_fields(index, "CycleA")
        self.assertIsNotNone(got)
        fields, _asm, complete = got
        self.assertFalse(complete)
        self.assertEqual(fields, {"FromA", "FromB"})

    def test_newline_base_continuation_is_incomplete(self):
        # `public class X :` with the base on the NEXT line: the line parser cannot
        # read the base, so the class must be incomplete — never silently baseless.
        index = audit.build_index(self.root)
        got = audit.resolve_fields(index, "ContinuationWarhead")
        self.assertIsNotNone(got)
        fields, _asm, complete = got
        self.assertFalse(complete)
        self.assertIn("Own", fields)

    def test_missing_intermediate_base_makes_chain_incomplete(self):
        # Common holds DamageWarhead/Warhead; without it the CA chain breaks mid-way.
        index = audit.build_index(self.root, self.root / "missing-engine")
        got = audit.resolve_fields(index, "AreaDamageWarhead")
        fields, _asm, complete = got
        self.assertFalse(complete)
        self.assertIn("Radius", fields)  # own fields still collected


class AuditRunTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        write_repo_assemblies(self.root)
        self.engine = write_engine_assemblies(self.root / "engine")
        self.json_path = self.root / "dead.json"
        self.ruleset = FakeRuleset({})

    def set_weapons(self, weapons):
        self.ruleset = FakeRuleset(weapons)

    def run_audit(self, *extra):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), stub_model(self.ruleset):
            code = audit.main(["--root", str(self.root), *extra])
        return code, out.getvalue()

    def chdir_away_from_repo(self):
        # Any directory that is not the repository — exercises the CWD independence.
        old = os.getcwd()
        self.addCleanup(os.chdir, old)
        os.chdir(self._tmp.name)

    def write_json_sentinel(self) -> bytes:
        """Pre-existing --json content that an incomplete run must leave byte-identical."""
        sentinel = b'{"sentinel": ["do-not-touch"]}'
        self.json_path.write_bytes(sentinel)
        return sentinel

    # -- the CWD-relative path defect ---------------------------------------- #

    def test_explicit_root_wins_over_cwd(self):
        # Reproduces the original bug: run from a foreign CWD with an explicit --root,
        # the old script ignored --root when building the field index and, with the
        # empty index it got, reported "OK" on zero coverage.
        self.chdir_away_from_repo()
        self.set_weapons({
            "ttnk": Yaml("ttnk", None, [
                warhead_node("main", "AreaDamage", ["Damage", "Radius", "Spread", "Bogus"]),
            ]),
        })
        with mock.patch.object(audit, "DEAD_FIELD_BASELINE", 0):
            code, _out = self.run_audit("--json", str(self.json_path))
        self.assertEqual(code, audit.EXIT_RATCHET)   # 1 — complete scan, above ratchet
        self.assertEqual(read_json(self.json_path), {"AreaDamage.Bogus": ["ttnk"]})

    # -- engine root --------------------------------------------------------- #

    def test_repo_without_engine_is_incomplete_without_flag(self):
        # A worktree whose engine/ is not checked out: the four engine assemblies are
        # missing and the audit must refuse a passing verdict.
        shutil.rmtree(self.root / "engine")
        elsewhere = write_engine_assemblies(self.root / "engine-elsewhere")
        self.ruleset = FakeRuleset({
            "ttnk": Yaml("ttnk", None, [warhead_node("main", "AreaDamage", ["Damage"])])
        })
        code, _out = self.run_audit()
        self.assertEqual(code, audit.EXIT_INCOMPLETE)

        code, _out = self.run_audit("--engine-root", str(elsewhere))
        self.assertEqual(code, audit.EXIT_OK)

    # -- missing assemblies --------------------------------------------------- #

    def test_missing_assembly_fails_prescan_without_touching_json(self):
        # Reproduces the original bug: a missing assembly silently produced an empty
        # index and the audit answered "OK". Also: a pre-scan failure must not
        # overwrite an existing --json file with data that was never scanned.
        stale = {"StaleType.Stale": ["weapon"]}
        self.json_path.write_text(json.dumps(stale), encoding="utf-8")
        for cs in (self.engine / "OpenRA.Mods.Common" / "Warheads").glob("*.cs"):
            cs.unlink()
        self.set_weapons({
            "ttnk": Yaml("ttnk", None, [warhead_node("main", "AreaDamage", ["Damage"])])
        })
        code, _out = self.run_audit("--json", str(self.json_path))
        self.assertEqual(code, audit.EXIT_INCOMPLETE)
        self.assertEqual(read_json(self.json_path), stale)

    # -- unresolved types / broken chains ------------------------------------- #

    def test_unresolved_type_withholds_json_but_prints_findings(self):
        # Reproduces the original bug: unresolved types were skipped silently and the
        # run could still report success. Raw partial findings stay on stdout, but the
        # pre-existing --json must survive byte-identical — no partial masquerade.
        sentinel = self.write_json_sentinel()
        self.set_weapons({
            "ttnk": Yaml("ttnk", None, [
                warhead_node("main", "AreaDamage", ["Bogus"]),
                warhead_node("alt", "Mystery", ["Whatever"]),
            ]),
        })
        code, out = self.run_audit("--json", str(self.json_path))
        self.assertEqual(code, audit.EXIT_INCOMPLETE)
        self.assertIn("Mystery", out)
        self.assertIn("AreaDamage.Bogus", out)
        self.assertEqual(self.json_path.read_bytes(), sentinel)

    def test_unresolved_type_alone_is_not_success(self):
        sentinel = self.write_json_sentinel()
        self.set_weapons({
            "ttnk": Yaml("ttnk", None, [warhead_node("main", "Mystery", ["Whatever"])])
        })
        code, _out = self.run_audit("--json", str(self.json_path))
        self.assertEqual(code, audit.EXIT_INCOMPLETE)
        self.assertEqual(self.json_path.read_bytes(), sentinel)

    def test_broken_chain_partial_fields_are_not_trusted(self):
        # GhostWarhead's base is unknown, so its field set is partial: a yaml key it
        # does not own may live on that base. The old code trusted the partial set and
        # reported "Bogus" dead — a false positive. Now: incomplete, never judged, and
        # the previous --json is preserved.
        sentinel = self.write_json_sentinel()
        self.set_weapons({
            "gh": Yaml("gh", None, [warhead_node("main", "Ghost", ["Own", "Bogus"])])
        })
        code, _out = self.run_audit("--json", str(self.json_path))
        self.assertEqual(code, audit.EXIT_INCOMPLETE)
        self.assertEqual(self.json_path.read_bytes(), sentinel)

    def test_inheritance_cycle_is_incomplete_and_withholds_json(self):
        sentinel = self.write_json_sentinel()
        self.set_weapons({
            "ca": Yaml("ca", None, [warhead_node("main", "CycleA", ["FromA", "Whatever"])])
        })
        code, out = self.run_audit("--json", str(self.json_path))
        self.assertEqual(code, audit.EXIT_INCOMPLETE)
        self.assertIn("CycleA", out)
        self.assertEqual(self.json_path.read_bytes(), sentinel)

    def test_unreadable_source_fails_before_scan_and_json(self):
        # A partially readable source directory must never fabricate a complete schema:
        # the read failure propagates to an INCOMPLETE verdict before any scan or
        # --json overwrite.
        sentinel = self.write_json_sentinel()
        self.set_weapons({
            "ttnk": Yaml("ttnk", None, [warhead_node("main", "AreaDamage", ["Damage"])])
        })

        def denied(_path, *_args, **_kwargs):
            raise PermissionError(13, "denied")

        with mock.patch.object(pathlib.Path, "read_text", denied):
            code, out = self.run_audit("--json", str(self.json_path))
        self.assertEqual(code, audit.EXIT_INCOMPLETE)
        self.assertIn("denied", out)
        self.assertEqual(self.json_path.read_bytes(), sentinel)

    # -- ratchet & json freshness ---------------------------------------------- #

    def test_warn_below_ratchet_exits_zero(self):
        self.set_weapons({
            "ttnk": Yaml("ttnk", None, [warhead_node("main", "AreaDamage", ["Bogus"])])
        })
        code, _out = self.run_audit()
        self.assertEqual(code, audit.EXIT_OK)

    def test_dead_above_ratchet_fails(self):
        self.set_weapons({
            "ttnk": Yaml("ttnk", None, [warhead_node("main", "AreaDamage", ["Bogus"])])
        })
        with mock.patch.object(audit, "DEAD_FIELD_BASELINE", 0):
            code, _out = self.run_audit()
        self.assertEqual(code, audit.EXIT_RATCHET)

    def test_clean_scan_rewrites_stale_json_empty(self):
        # Reproduces the original bug: a clean scan never touched --json, so the file
        # from an earlier failing run kept masquerading as the current result.
        self.json_path.write_text('{"AreaDamage.Bogus": ["ttnk"]}', encoding="utf-8")
        self.set_weapons({
            "ttnk": Yaml("ttnk", None, [warhead_node("main", "AreaDamage",
                                                     ["Damage", "Radius", "Spread"])])
        })
        code, _out = self.run_audit("--json", str(self.json_path))
        self.assertEqual(code, audit.EXIT_OK)
        self.assertEqual(read_json(self.json_path), {})

    def test_template_weapons_are_skipped(self):
        self.set_weapons({
            "^BaseWeapon": Yaml("^BaseWeapon", None,
                                [warhead_node("main", "Mystery", ["Whatever"])]),
            "ttnk": Yaml("ttnk", None, [warhead_node("main", "AreaDamage", ["Damage"])]),
        })
        code, _out = self.run_audit()
        self.assertEqual(code, audit.EXIT_OK)


if __name__ == "__main__":
    unittest.main()
