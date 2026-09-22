"""Bounded explicit-route (--root / --json) export tests for `extract_peer_units`.

ALL FIXTURES ARE SYNTHETIC in temp directories: a peer-shaped checkout
(`mods/ca/mod.yaml` + rules/weapons + one .ftl), optionally `git init`-ed and
optionally carrying a `mod.config` engine pin. No real peer checkout is read,
no source file is executed, no corpus document or YAML is touched, and the
legacy CLI contract is pinned (it must survive the explicit route unchanged).

The requirements pinned here (OPENRA_WEAPON_EVIDENCE_PLAN P4 + the export
contract):
  * exactly one --mod under an explicit --root; external --json only;
  * provenance: git HEAD + dirty state + engine pin if present; every ACTUALLY
    read input (manifests, rules/weapons, fluent loader reads) hashed before
    AND after, checkout-relative names, never private absolute paths;
  * runtime applicability unverified; no factory-ready / max-state certification;
  * --expect-commit guards the version (40 hex) with READ-ONLY git;
  * the output path must reject every git repo / source checkout (junction
    aliases included), refuse overwriting DIFFERENT content, and strict JSON
    (allow_nan=False) must fail BEFORE any file is created;
  * fail closed on missing root/manifest, conflicting mods, source change,
    bad numerics — no output on any failure;
  * every nested armament/ammo/modifier record survives the JSONL roundtrip;
  * PEERS is never mutated.
"""

from __future__ import annotations

import copy
import io
import json
import contextlib
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "reference"))
import miniyaml  # noqa: E402
import extract_peer_units as epu  # noqa: E402

DOC5 = ROOT / "docs" / "design" / "ORIGINAL_UNITS_PEER_OPENRA.md"

MOD_YAML = "Rules:\n    rules/actors.yaml\nWeapons:\n    weapons/weapons.yaml\n"

ACTORS = """\
E1:
    Health:
        HP: 5000
    Valued:
        Cost: 100
    Mobile:
        Speed: 56
    Buildable:
        Queue: Infantry
    Armament:
        Weapon: M60
    AttackTurreted:
HMMV:
    Health:
        HP: 12000
    Valued:
        Cost: 400
    Mobile:
        Speed: 144
    Buildable:
        Queue: Vehicle
    Armament:
        Weapon: M60
    AttackTurreted:
HMMV.TOW:
    Inherits: HMMV
    Buildable:
        Queue: Vehicle
        Prerequisites: ~tow.upgrade
    Armament@SECONDARY:
        Name: secondary
        Weapon: TOW
        PauseOnCondition: !ammo
    AmmoPool:
        Armaments: secondary
        Ammo: 1
        AmmoCondition: ammo
    ReloadAmmoPoolCA:
        Delay: 200
        Count: 1
    FirepowerMultiplier@elite:
        UpgradeTypes: elite
        Modifier: 140
    DamageMultiplier@shield:
        UpgradeTypes: shielded
        Modifier: 60
"""

WEAPONS = """\
M60:
    Range: 6c0
    ReloadDelay: 38
    Burst: 5
    BurstDelays: 5, 5, 6, 6
    Warhead@1: SpreadDamage
        Damage: 1000
TOW:
    ReloadDelay: 50
    Warhead@1: SpreadDamage
        Damage: 600
"""


def build_checkout(tmp, *, git=False, engine_pin=True, actors=ACTORS):
    """A minimal peer-shaped checkout for mod_id `ca` (rifle E1 @ 5000 = the
    PEERS expectation, so no anchor note). Returns the checkout root."""
    base = tmp / "mods" / "ca"
    (base / "rules").mkdir(parents=True, exist_ok=True)
    (base / "weapons").mkdir(parents=True, exist_ok=True)
    (base / "langs").mkdir(parents=True, exist_ok=True)
    (base / "mod.yaml").write_text(MOD_YAML, encoding="utf-8")
    (base / "rules" / "actors.yaml").write_text(actors, encoding="utf-8")
    (base / "weapons" / "weapons.yaml").write_text(WEAPONS, encoding="utf-8")
    (base / "langs" / "test.ftl").write_text("actor-e1.name = Rifleman\n", encoding="utf-8")
    if engine_pin:
        (tmp / "mod.config").write_text(
            'ENGINE_VERSION="ca-engine/1.09"\n', encoding="utf-8")
    if git:
        for argv in (["init", "-q"],
                     ["config", "user.name", "test"],
                     ["config", "user.email", "test@example.com"],
                     ["add", "-A"], ["commit", "-q", "-m", "init"]):
            subprocess.run(["git", "-C", str(tmp), *argv],
                           check=True, capture_output=True)
    return tmp


def git_head(checkout):
    out = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                         check=True, capture_output=True)
    return out.stdout.decode().strip()


def read_jsonl(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


class ExportTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._out_tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.out_dir = pathlib.Path(self._out_tmp.name)
        self._armor = epu._ARMOR_MAP
        epu._ARMOR_MAP = {"sources": {}}          # hermetic: no ladder columns
        self._peers = copy.deepcopy(epu.PEERS)

    def tearDown(self):
        epu._ARMOR_MAP = self._armor
        self.assertEqual(epu.PEERS, self._peers)   # PEERS must never be mutated
        self._tmp.cleanup()
        self._out_tmp.cleanup()

    def run_main(self, argv):
        """In-process CLI run with captured streams; returns (rc, out, err)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = epu.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def export_args(self, name="out.jsonl", **kw):
        return ["--root", kw.get("root", str(self.tmp)), "--mod", kw.get("mod", "ca"),
                "--json", str(self.out_dir / name)] + kw.get("extra", [])


class FullRoundtripTest(ExportTestBase):
    def setUp(self):
        super().setUp()
        build_checkout(self.tmp)

    def test_full_nested_roundtrip(self):
        out = self.out_dir / "roundtrip.jsonl"
        rc, _, err = self.run_main(self.export_args("roundtrip.jsonl"))
        self.assertEqual(rc, 0, err)
        records = read_jsonl(out)
        self.assertEqual(records[0]["record"], "meta")
        units = {r["id"]: r for r in records if r["record"] == "unit"}
        self.assertEqual(set(units), {"E1", "HMMV", "HMMV.TOW"})
        # every nested armament/ammo/modifier record survives, byte-equal to the
        # in-process weapon_stats of the SAME checkout
        rules = miniyaml.Ruleset(self.tmp, "ca")
        for aid in units:
            expected = epu.weapon_stats(rules, rules.resolve(aid), "Combined Arms")
            got = {k: v for k, v in units[aid].items() if k in expected}
            self.assertEqual(got, expected, aid)
        tow = units["HMMV.TOW"]
        self.assertEqual([s["weapon"] for s in tow["weapon_evidence"]], ["M60", "TOW"])
        self.assertEqual(tow["weapon_evidence"][1]["pause_on_condition"], "!ammo")
        self.assertEqual(tow["weapon_evidence"][1]["ammo_pool"]["binding"], "bound")
        self.assertEqual(tow["ammo_rearm"][0]["delay"], "200")
        self.assertEqual([m["trait"] for m in tow["weapon_modifiers"]],
                         ["FirepowerMultiplier@elite"])
        self.assertEqual([d["trait"] for d in tow["defensive_modifiers"]],
                         ["DamageMultiplier@shield"])
        self.assertEqual(tow["ammo_pools"][0]["fields"]["AmmoCondition"], "ammo")
        # chassis fields + the fluent-resolved display name travelled too
        self.assertEqual(units["E1"]["name"], "Rifleman")
        self.assertEqual(units["E1"]["hp"], 5000)
        self.assertEqual(tow["hp"], 12000)

    def test_metadata_record(self):
        out = self.out_dir / "meta.jsonl"
        rc, _, _ = self.run_main(self.export_args("meta.jsonl"))
        self.assertEqual(rc, 0)
        meta = read_jsonl(out)[0]
        self.assertEqual(meta["record"], "meta")
        p = meta["provenance"]
        self.assertEqual(p["mode"], "explicit_root")
        self.assertEqual(p["mod_id"], "ca")
        self.assertEqual(p["source_label"], "Combined Arms")
        self.assertIsNone(p["checkout_head"])           # not a git checkout here
        self.assertIsNone(p["checkout_dirty"])
        self.assertEqual(p["engine_pin"], "ca-engine/1.09")
        self.assertEqual(p["engine_pin_applicability"], "unverified")
        self.assertEqual(p["source_runtime_applicability"], "unverified")
        self.assertEqual(p["factory_state_certification"], "none")
        self.assertEqual(p["max_state_certification"], "none")
        self.assertIsNone(p["expect_commit"])
        self.assertEqual(meta["rifle"], {"id": "E1", "hp": 5000, "cost": 100})
        self.assertEqual(meta["row_count"], 3)
        # every ACTUALLY-read input, hashed before AND after, checkout-relative
        rels = {e["path"] for e in meta["inputs"]}
        self.assertIn("mods/ca/mod.yaml", rels)
        self.assertIn("mods/ca/rules/actors.yaml", rels)
        self.assertIn("mods/ca/weapons/weapons.yaml", rels)
        self.assertIn("mods/ca/langs/test.ftl", rels)   # the fluent loader's read
        self.assertIn("mod.config", rels)               # the engine-pin source
        self.assertEqual(len(rels), meta["provenance"]["input_count"])
        for e in meta["inputs"]:
            self.assertRegex(e["path"], r"^[A-Za-z0-9_.@/-]+$")   # relative posix only
            self.assertNotIn("\\", e["path"])
            self.assertRegex(e["sha256_before"], r"^[0-9a-f]{64}$")
            self.assertTrue(e["unchanged"])
            self.assertEqual(e["sha256_before"], e["sha256_after"])
        self.assertRegex(p["inputs_digest"], r"^[0-9a-f]{64}$")
        # bounded git status: never a raw diagnostic, never a path
        self.assertEqual(p["checkout_head_status"], "git_unavailable")
        self.assertNotIn("checkout_head_error", p)
        # the local toolchain claim is a documented finite fingerprint set
        self.assertEqual(p["input_scope"],
                         "source_checkout_inputs_hashed_plus_documented_local_dependencies")
        deps = {e["path"]: e for e in p["local_dependencies"]}
        self.assertEqual(set(deps), set(epu.LOCAL_DEPENDENCIES))
        for e in deps.values():
            self.assertRegex(e["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(p["local_dependencies_digest"], r"^[0-9a-f]{64}$")
        text = out.read_text(encoding="utf-8")
        self.assertNotIn(str(self.tmp), text)           # no private absolute path
        self.assertNotIn("WindowsPath", text)
        # per-row provenance carries the same identity + digests
        for rec in read_jsonl(out):
            if rec["record"] != "unit":
                continue
            rp = rec["provenance"]
            self.assertEqual(rp["inputs_digest"], p["inputs_digest"])
            self.assertEqual(rp["local_dependencies_digest"], p["local_dependencies_digest"])
            self.assertEqual(rp["checkout_head"], p["checkout_head"])
            self.assertEqual(rp["checkout_head_status"], p["checkout_head_status"])
            self.assertEqual(rp["engine_pin"], p["engine_pin"])
            self.assertEqual(rp["source_label"], "Combined Arms")
            self.assertNotIn("checkout_head_error", rp)

    def test_no_pathlib_leaks_into_rows(self):
        out = self.out_dir / "paths.jsonl"
        rc, _, _ = self.run_main(self.export_args("paths.jsonl"))
        self.assertEqual(rc, 0)
        for rec in read_jsonl(out):
            blob = json.dumps(rec)
            self.assertNotIn("Path", blob)
            self.assertNotIn(str(self.tmp), blob)


class GitProvenanceTest(ExportTestBase):
    def setUp(self):
        super().setUp()
        if shutil.which("git") is None:
            self.skipTest("git not available")
        build_checkout(self.tmp, git=True)

    def test_head_dirty_and_expect_commit(self):
        head = git_head(self.tmp)
        out = self.out_dir / "git.jsonl"
        rc, _, err = self.run_main(
            self.export_args("git.jsonl", extra=["--expect-commit", head]))
        self.assertEqual(rc, 0, err)
        meta = read_jsonl(out)[0]
        p = meta["provenance"]
        self.assertEqual(p["checkout_head"], head)
        self.assertFalse(p["checkout_dirty"])
        self.assertEqual(p["checkout_dirty_entries"], 0)
        self.assertEqual(p["expect_commit"], head)
        # a dirty worktree is RECORDED, never certified — extraction still runs
        actors = self.tmp / "mods" / "ca" / "rules" / "actors.yaml"
        actors.write_text(actors.read_text(encoding="utf-8") + "# dirty\n",
                          encoding="utf-8")
        out2 = self.out_dir / "git2.jsonl"
        rc, _, _ = self.run_main(self.export_args("git2.jsonl"))
        self.assertEqual(rc, 0)
        p2 = read_jsonl(out2)[0]["provenance"]
        self.assertTrue(p2["checkout_dirty"])
        self.assertEqual(p2["checkout_dirty_entries"], 1)
        self.assertEqual(p2["checkout_head"], head)

    def test_expect_commit_mismatch_and_bad_format(self):
        for commit, why in (("0" * 40, "mismatch"), ("xyz", "40 hex"),
                            ("ab" * 19, "40 hex")):
            out = self.out_dir / f"expect_{why}.jsonl"
            rc, _, err = self.run_main(
                self.export_args(f"expect_{why}.jsonl", extra=["--expect-commit", commit]))
            self.assertEqual(rc, 1, why)
            self.assertFalse(out.exists(), why)
        rc, _, err = self.run_main(
            self.export_args("expect_head.jsonl",
                             extra=["--expect-commit", git_head(self.tmp)]))
        self.assertEqual(rc, 0)

    def test_bounded_head_status_never_leaks_paths(self):
        """A broken .git pointer makes raw git stderr quote absolute paths; the export
        must still succeed while serializing ONLY the bounded, path-free status."""
        bogus = self.out_dir / "no_such_gitdir"
        # git marks object files read-only, so move the whole .git dir out of the
        # checkout instead of deleting it
        (self.tmp / ".git").rename(self.out_dir / "disabled_git_store")
        (self.tmp / ".git").write_text(f"gitdir: {bogus}\n", encoding="utf-8")
        out = self.out_dir / "leak.jsonl"
        rc, _, err = self.run_main(self.export_args("leak.jsonl"))
        self.assertEqual(rc, 0)
        text = out.read_text(encoding="utf-8")
        meta = read_jsonl(out)[0]
        p = meta["provenance"]
        self.assertIsNone(p["checkout_head"])
        self.assertEqual(p["checkout_head_status"], "git_unavailable")
        self.assertNotIn("no_such_gitdir", text)        # bounded status only
        self.assertNotIn("fatal", text)
        self.assertNotIn(str(self.tmp), text)
        self.assertNotIn("no_such_gitdir", json.dumps(meta["inputs"]))
        self.assertIn("git", err)                       # details went to console stderr


class RefusalTest(ExportTestBase):
    def setUp(self):
        super().setUp()
        build_checkout(self.tmp)

    def assert_refused(self, argv, fragment, out=None):
        rc, _, err = self.run_main(argv)
        self.assertEqual(rc, 1)
        self.assertIn(fragment, err)
        if out is not None:
            self.assertFalse(out.exists())

    def test_invalid_args(self):
        out = self.out_dir / "never.jsonl"
        self.assert_refused(["--json", str(out)], "--root", out)
        self.assert_refused(["--root", str(self.tmp)], "exactly one")
        self.assert_refused(self.export_args()[:-2] + ["--mod", "sp", "--json",
                                                       str(self.out_dir / "x.jsonl")],
                            "exactly one")
        self.assert_refused(["--root", str(self.tmp / "nope"), "--mod", "ca",
                             "--json", str(out)], "not a directory", out)
        empty = self.out_dir / "emptyroot"
        empty.mkdir()
        self.assert_refused(["--root", str(empty), "--mod", "ca", "--json", str(out)],
                            "no manifest", out)
        self.assert_refused(["--root", str(self.tmp), "--mod", "ca"], "external --json")
        self.assert_refused(self.export_args(extra=["--dry-run"]), "--dry-run")
        self.assert_refused(self.export_args(extra=["--expect-commit", "zz"]),
                            "40 hex")

    def test_legacy_cli_unchanged(self):
        before = DOC5.read_bytes()
        # hermetic + fast: no candidate can resolve, so the legacy loop extracts nothing
        orig = epu.find_checkout
        epu.find_checkout = lambda cands, mod_id: None
        try:
            rc, out, err = self.run_main(["--mod", "ca", "--dry-run"])
            self.assertEqual(rc, 0, err)
            self.assertIn("DRY RUN", out)
            self.assertEqual(DOC5.read_bytes(), before)   # Document 5 untouched
            with self.assertRaises(SystemExit) as cm:    # argparse still guards choices
                epu.main(["--mod", "not_a_peer"])
            self.assertEqual(cm.exception.code, 2)
        finally:
            epu.find_checkout = orig

    def test_openra_legacy_route_has_no_cameo_engine_fallback(self):
        """Upstream OpenRA rows must go absent unless a reviewed root is explicit.

        `cameo-engine` is the fork we ship, so allowing any automatic candidate to satisfy an
        OpenRA base peer would emit fork data under an upstream label. The explicit route remains
        available for a reviewed checkout and commit; the automatic route must stay fail-closed.
        """
        for mod_id in ("ra", "cnc", "ts", "d2k"):
            label, data, err = epu.extract(mod_id)
            self.assertIsNone(data, mod_id)
            self.assertIn("automatic extraction disabled", err, label)

    def test_openra_legacy_cli_refuses_before_corpus_write(self):
        out = self.out_dir / "corpus.md"
        out.write_bytes(b"existing corpus sentinel\n")
        before = out.read_bytes()
        original_out = epu.OUT
        epu.OUT = out
        try:
            rc, _, err = self.run_main(["--mod", "ra"])
        finally:
            epu.OUT = original_out
        self.assertEqual(rc, 1)
        self.assertIn("automatic extraction is disabled", err)
        self.assertEqual(out.read_bytes(), before)

    def test_source_change_refused(self):
        out = self.out_dir / "changed.jsonl"
        orig = epu.extract
        actors = self.tmp / "mods" / "ca" / "rules" / "actors.yaml"
        original = actors.read_text(encoding="utf-8")

        def mutating_extract(mod_id, root_override=None):
            actors.write_text(original + "# mid-run edit\n", encoding="utf-8")
            return orig(mod_id, root_override=root_override)

        epu.extract = mutating_extract
        try:
            rc, _, err = self.run_main(self.export_args("changed.jsonl"))
        finally:
            epu.extract = orig
        self.assertEqual(rc, 1)
        self.assertIn("changed during extraction", err)
        self.assertFalse(out.exists())

    def test_verify_inputs_unchanged_reports_all_kinds(self):
        self.assertEqual(epu.verify_inputs_unchanged({"a": "1"}, {"a": "1"}), [])
        problems = epu.verify_inputs_unchanged({"a": "1", "b": "2"}, {"a": "9"})
        self.assertTrue(any("a" in p for p in problems))
        self.assertTrue(any("removed" in p for p in problems))

    @unittest.skipUnless(sys.platform == "win32", "junctions are Windows")
    def test_junction_source_escape(self):
        """A source tree reached THROUGH a junction looks in-tree lexically; containment
        must judge the RESOLVED target and refuse the escape."""
        external = self.out_dir / "external_src"
        build_checkout(external)
        shutil.rmtree(self.tmp / "mods" / "ca")
        made = subprocess.run(["cmd", "/c", "mklink", "/J",
                               str(self.tmp / "mods" / "ca"),
                               str(external / "mods" / "ca")], capture_output=True)
        if made.returncode != 0:
            self.skipTest("mklink /J unavailable")
        out = self.out_dir / "escape.jsonl"
        rc, _, err = self.run_main(self.export_args("escape.jsonl"))
        self.assertEqual(rc, 1)
        self.assertIn("outside the checkout", err)
        self.assertFalse(out.exists())

    def test_engine_pin_window_changes_refused(self):
        """mod.config is inventoried AND its pin is read at BOTH ends of the extraction
        window: mutation, disappearance and mid-run file appearance all refuse."""
        modconfig = self.tmp / "mod.config"
        original_cfg = modconfig.read_text(encoding="utf-8")
        orig = epu.extract

        def run_with(mutate, name, fragment):
            out = self.out_dir / name

            def mutator(mod_id, root_override=None):
                mutate()
                return orig(mod_id, root_override=root_override)

            epu.extract = mutator
            try:
                rc, _, err = self.run_main(self.export_args(name))
            finally:
                epu.extract = orig
            self.assertEqual(rc, 1, name)
            self.assertIn(fragment, err, name)
            self.assertFalse(out.exists(), name)

        run_with(lambda: modconfig.write_text(
            original_cfg.replace("ca-engine/1.09", "ca-engine/9.9"), encoding="utf-8"),
            "pin_mutation.jsonl", "engine pin changed")
        run_with(lambda: modconfig.unlink(), "pin_removed.jsonl", "removed")
        run_with(lambda: (self.tmp / "mods" / "ca" / "langs" / "late.ftl")
                 .write_text("late = x\n", encoding="utf-8"),
                 "file_added.jsonl", "added")

    def test_bad_numeric_refused(self):
        bad = ACTORS + "BAD:\n    Health:\n        HP: nan\n    Valued:\n        Cost: 1\n" \
                         "    Mobile:\n        Speed: 5\n    Buildable:\n        Queue: Infantry\n"
        build_checkout(self.tmp, actors=bad)
        out = self.out_dir / "badnum.jsonl"
        rc, _, err = self.run_main(self.export_args("badnum.jsonl"))
        self.assertEqual(rc, 1)
        self.assertIn("before any output", err)
        self.assertFalse(out.exists())

    def test_strict_json_gate_before_creation(self):
        with self.assertRaises(ValueError):
            epu.jsonl_line({"v": float("nan")})
        with self.assertRaises(ValueError):
            epu.jsonl_line({"v": float("inf")})
        with self.assertRaises(TypeError):      # pathlib must not serialize
            epu.jsonl_line({"v": pathlib.Path("x")})

    def test_overwrite_different_content_refused(self):
        out = self.out_dir / "overwrite.jsonl"
        rc, _, err = self.run_main(self.export_args("overwrite.jsonl"))
        self.assertEqual(rc, 0, err)
        first = out.read_text(encoding="utf-8")
        # rerun against the SAME source: identical content is a successful no-op
        rc, _, _ = self.run_main(self.export_args("overwrite.jsonl"))
        self.assertEqual(rc, 0)
        self.assertEqual(out.read_text(encoding="utf-8"), first)
        # changed source -> different export -> REFUSED, original file intact
        actors = self.tmp / "mods" / "ca" / "rules" / "actors.yaml"
        actors.write_text(actors.read_text(encoding="utf-8").replace("HP: 5000", "HP: 4999"),
                          encoding="utf-8")
        rc, _, err = self.run_main(self.export_args("overwrite.jsonl"))
        self.assertEqual(rc, 1)
        self.assertIn("different content", err)
        self.assertEqual(out.read_text(encoding="utf-8"), first)

    def test_output_rejections(self):
        # inside the source checkout (plain and junction-aliased) and inside any git repo
        self.assert_refused(self.export_args_named(self.tmp / "inside.jsonl"),
                            "protected tree")
        self.assert_refused(
            self.export_args_named(ROOT / "docs" / "audit" / "peer_export_probe.jsonl"),
            "sits inside the git repo")
        if sys.platform == "win32":
            junc = self.out_dir / "junc"
            made = subprocess.run(["cmd", "/c", "mklink", "/J", str(junc), str(self.tmp)],
                                  capture_output=True)
            if made.returncode == 0:
                self.assert_refused(self.export_args_named(junc / "inside.jsonl"),
                                    "protected tree")

    def export_args_named(self, path):
        return ["--root", str(self.tmp), "--mod", "ca", "--json", str(path)]


if __name__ == "__main__":
    unittest.main()
