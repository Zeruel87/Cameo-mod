"""Focused tests for the C19 release-identity triage diagnostic.

Pure helpers + stubbed git/fixtures only (plus one tiny real-git binding
test) - no real repo parse, no network.
Run: python tools/tests/test_release_identity_triage.py
"""
import pathlib
import subprocess
import sys
import tempfile
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools/audit"))
import triage_release_identities as tri

FULL = "a" * 40


def diff_text(*lines):
    return "\n".join(lines) + "\n"


def file_header(path):
    return [
        f"diff --git a/{path} b/{path}",
        "index 1111111..2222222 100644",
        f"--- a/{path}",
        f"+++ b/{path}",
    ]


WEAPONS = "mods/cameo/ContentPacks/X/yaml/weapons.yaml"
ROOT_WEAPONS = "mods/cameo/weapons/tier1.yaml"
ACTOR_YAML = "mods/cameo/ContentPacks/RA/Allies/yaml/aircraft.yaml"
VEHICLES_YAML = "mods/cameo/ContentPacks/RA/Allies/yaml/vehicles.yaml"

GOOD_RENAME = diff_text(*file_header(WEAPONS), "@@ -10 +10 @@", "-HydraSpit:",
                        "+HydraSpit_AA:")

FIELD_EDITS = diff_text(*file_header(WEAPONS), "@@ -10 +10 @@",
                        "-\t\tWeapon: Aphid", "+\t\tWeapon: Aphid_AA")

MULTI_HEADER = diff_text(*file_header(WEAPONS), "@@ -10,4 +10,4 @@",
                         "-HydraSpit:", "+HydraSpit_AA:", "-Aphid:", "+Aphid_AA:")

NONADJACENT = diff_text(*file_header(WEAPONS), "@@ -10,3 +10,3 @@",
                        "-HydraSpit:", " \tInherits: ^Base", "+HydraSpit_AA:")

TEMPLATE_HEADER = diff_text(*file_header(WEAPONS), "@@ -10 +10 @@",
                            "-^BaseWeapon:", "+^BaseWeapon_AA:")

CANCELLATION = diff_text(*file_header(WEAPONS), "@@ -10 +10 @@",
                         "--StaleWeapon:", "+StaleWeaponReborn:")

NON_YAML = diff_text(*file_header("docs/notes.md"), "@@ -10 +10 @@",
                     "-HydraSpit:", "+HydraSpit_AA:")

ACTOR_RENAME = diff_text(*file_header(ACTOR_YAML), "@@ -10 +10 @@",
                         "-Aphid:", "+Aphid_AA:")

NONCONFORMING_YAML = diff_text(*file_header(VEHICLES_YAML), "@@ -10 +10 @@",
                               "-Aphid:", "+Aphid_AA:")

DOTTED_LEGACY = diff_text(
    *file_header("mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml"),
    "@@ -530 +530 @@", "-EMPDisable.anim:", "+Ixian_EMP_charge:")

HYPHEN_LEGACY = diff_text(*file_header(WEAPONS), "@@ -7 +7 @@",
                          "-TSCABAL_EMP_Disable.end:", "+TSCABAL_EMP_disable:")

DOTTED_CANCELLATION = diff_text(*file_header(WEAPONS), "@@ -9 +9 @@",
                                "--EMPDisable.anim:", "+EMPDisable.anim2:")

NEGATIVE_HYPHEN = diff_text(*file_header(WEAPONS), "@@ -11 +11 @@",
                            "--Weapon-hack:", "+Weapon-hack2:")

INLINE_VALUE = diff_text(*file_header(WEAPONS), "@@ -13 +13 @@",
                         "-Dotted.legacy: inherit-me", "+Dotted.legacy2:")


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def fake_git(responses):
    """run(cmd) -> first CompletedProcess whose needle appears in the cmd."""
    def run(cmd):
        joined = " ".join(cmd)
        for needle, cp in responses.items():
            if needle in joined:
                return cp
        raise AssertionError(f"unexpected git call: {joined}")
    return run


def recording_run(returncode=0, stdout=""):
    calls = []

    def run(cmd):
        calls.append(list(cmd))
        return completed(returncode, stdout)

    return run, calls


class WeaponLayoutTests(unittest.TestCase):
    def test_pack_weapons_yaml_accepted(self):
        self.assertTrue(tri.is_weapon_yaml(WEAPONS))

    def test_root_weapons_yaml_accepted(self):
        self.assertTrue(tri.is_weapon_yaml(ROOT_WEAPONS))

    def test_actor_yaml_refused(self):
        self.assertFalse(tri.is_weapon_yaml(ACTOR_YAML))

    def test_non_weapons_pack_yaml_refused(self):
        self.assertFalse(tri.is_weapon_yaml(VEHICLES_YAML))

    def test_root_rules_sequences_chrome_refused(self):
        for path in ("mods/cameo/rules/redalert2.yaml",
                     "mods/cameo/sequences/315custom.yaml",
                     "mods/cameo/audio/advancewars.yaml",
                     "mods/cameo/chrome/lobby.yaml"):
            self.assertFalse(tri.is_weapon_yaml(path))

    def test_nested_root_weapons_subdir_refused(self):
        self.assertFalse(tri.is_weapon_yaml("mods/cameo/weapons/sub/x.yaml"))

    def test_contentpacks_yaml_weapons_without_faction_refused(self):
        self.assertFalse(
            tri.is_weapon_yaml("mods/cameo/ContentPacks/yaml/weapons.yaml"))

    def test_outside_cameo_refused(self):
        self.assertFalse(tri.is_weapon_yaml("mods/other/weapons/x.yaml"))


class ParseRenamePairsTests(unittest.TestCase):
    def test_exact_adjacent_rename_is_evidence_with_path(self):
        pairs = tri.parse_rename_pairs(GOOD_RENAME)
        self.assertEqual(1, len(pairs))
        self.assertEqual({"path": WEAPONS, "old": "HydraSpit",
                          "new": "HydraSpit_AA"}, pairs[0])

    def test_root_weapons_layout_accepted(self):
        pairs = tri.parse_rename_pairs(
            diff_text(*file_header(ROOT_WEAPONS), "@@ -3 +3 @@",
                      "-OldGun:", "+NewGun:"))
        self.assertEqual([{"path": ROOT_WEAPONS, "old": "OldGun",
                           "new": "NewGun"}], pairs)

    def test_actor_yaml_with_matching_weapon_names_refused(self):
        self.assertEqual([], tri.parse_rename_pairs(ACTOR_RENAME))

    def test_nonconforming_pack_yaml_refused(self):
        self.assertEqual([], tri.parse_rename_pairs(NONCONFORMING_YAML))

    def test_field_edits_are_never_name_pairs(self):
        self.assertEqual([], tri.parse_rename_pairs(FIELD_EDITS))

    def test_hunk_with_multiple_headers_is_ignored(self):
        self.assertEqual([], tri.parse_rename_pairs(MULTI_HEADER))

    def test_nonadjacent_headers_are_ignored(self):
        self.assertEqual([], tri.parse_rename_pairs(NONADJACENT))

    def test_template_headers_excluded(self):
        self.assertEqual([], tri.parse_rename_pairs(TEMPLATE_HEADER))

    def test_cancellation_node_removal_is_not_a_rename(self):
        self.assertEqual([], tri.parse_rename_pairs(CANCELLATION))

    def test_non_yaml_path_ignored(self):
        self.assertEqual([], tri.parse_rename_pairs(NON_YAML))

    def test_names_are_bare_ids_without_colon(self):
        for pair in tri.parse_rename_pairs(GOOD_RENAME):
            self.assertFalse(pair["old"].endswith(":"))
            self.assertFalse(pair["new"].endswith(":"))

    def test_dotted_legacy_pair_accepted(self):
        pairs = tri.parse_rename_pairs(DOTTED_LEGACY)
        self.assertEqual([{"path": "mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml",
                           "old": "EMPDisable.anim",
                           "new": "Ixian_EMP_charge"}], pairs)

    def test_hyphenated_legacy_pair_accepted(self):
        pairs = tri.parse_rename_pairs(HYPHEN_LEGACY)
        self.assertEqual([{"path": WEAPONS,
                           "old": "TSCABAL_EMP_Disable.end",
                           "new": "TSCABAL_EMP_disable"}], pairs)

    def test_dotted_cancellation_removal_still_rejected(self):
        self.assertEqual([], tri.parse_rename_pairs(DOTTED_CANCELLATION))

    def test_leading_hyphen_name_never_a_header(self):
        # A diff line `--Name:` is a cancellation removal (content `-Name:`);
        # a name can never begin with `-`, so this is never a rename pair.
        self.assertEqual([], tri.parse_rename_pairs(NEGATIVE_HYPHEN))

    def test_inline_value_never_a_header(self):
        self.assertEqual([], tri.parse_rename_pairs(INLINE_VALUE))

    def test_dotted_legacy_survives_full_pipeline(self):
        pairs = tri.parse_rename_pairs(DOTTED_LEGACY)
        edges, rejected = tri.resolve_evidence(
            [dict(p, commit=FULL) for p in pairs])
        base = {"EMPDisable.anim": {"flat": 500, "mains": 1}}
        now = {"Ixian_EMP_charge": {"flat": 500, "mains": 1}}
        rows, counts = tri.classify(["EMPDisable.anim"], base, now, set(),
                                    edges, rejected, lambda n: object())
        self.assertEqual(tri.STATUS_RENAMED, rows[0]["status"])
        self.assertEqual("Ixian_EMP_charge", rows[0]["renamed_to"])
        self.assertEqual(1, sum(counts.values()))


class ParseToClassifyIntegrationTests(unittest.TestCase):
    """Regression: a colon retained anywhere in old/new must not classify."""

    def test_parse_resolve_classify_produces_renamed_candidate(self):
        pairs = tri.parse_rename_pairs(GOOD_RENAME)
        evidences = [dict(p, commit=FULL) for p in pairs]
        edges, rejected = tri.resolve_evidence(evidences)
        self.assertEqual({}, rejected)
        base = {"HydraSpit": {"flat": 8000, "mains": 4}}
        now = {"HydraSpit_AA": {"flat": 8000, "mains": 4}}
        rows, counts = tri.classify(["HydraSpit"], base, now, set(), edges,
                                    rejected, lambda n: object())
        self.assertEqual(tri.STATUS_RENAMED, rows[0]["status"])
        self.assertEqual("HydraSpit_AA", rows[0]["renamed_to"])
        self.assertEqual(FULL, rows[0]["evidence"]["commit"])
        self.assertEqual(WEAPONS, rows[0]["evidence"]["path"])
        self.assertEqual(1.0, rows[0]["ratio"])

    def test_colon_contaminated_names_cannot_classify(self):
        edges = {"HydraSpit:": {"commit": FULL, "path": WEAPONS,
                                "old": "HydraSpit:", "new": "HydraSpit_AA:"}}
        base = {"HydraSpit": {"flat": 8000, "mains": 4}}
        now = {"HydraSpit_AA": {"flat": 8000, "mains": 4}}
        rows, counts = tri.classify(["HydraSpit"], base, now, set(), edges,
                                    {}, lambda n: object())
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual(1, counts[tri.STATUS_UNRESOLVED])


class ResolveEvidenceTests(unittest.TestCase):
    @staticmethod
    def ev(old, new, commit="c1"):
        return {"commit": commit, "path": WEAPONS, "old": old, "new": new}

    def test_unique_edge_survives(self):
        edges, rejected = tri.resolve_evidence([self.ev("A", "B")])
        self.assertEqual("B", edges["A"]["new"])
        self.assertEqual({}, rejected)

    def test_one_to_many_rejected(self):
        edges, rejected = tri.resolve_evidence(
            [self.ev("A", "B", "c1"), self.ev("A", "C", "c2")])
        self.assertNotIn("A", edges)
        self.assertEqual("ambiguous_multiple_targets", rejected["A"]["reason"])
        self.assertEqual(2, len(rejected["A"]["evidence"]))

    def test_many_to_one_rejected(self):
        edges, rejected = tri.resolve_evidence(
            [self.ev("A", "Z"), self.ev("B", "Z")])
        self.assertNotIn("A", edges)
        self.assertNotIn("B", edges)
        self.assertEqual("ambiguous_shared_target", rejected["A"]["reason"])
        self.assertEqual("ambiguous_shared_target", rejected["B"]["reason"])

    def test_fan_in_uses_edges_of_one_to_many_rejected_source(self):
        # A->X, B->X, B->Y: B is one-to-many, but A->X must STILL be rejected.
        edges, rejected = tri.resolve_evidence(
            [self.ev("A", "X"), self.ev("B", "X", "c2"), self.ev("B", "Y", "c2")])
        self.assertEqual({}, edges)
        self.assertEqual("ambiguous_shared_target", rejected["A"]["reason"])
        self.assertIn("A", {e["old"] for e in rejected["A"]["evidence"]})

    def test_cycle_rejected(self):
        edges, rejected = tri.resolve_evidence(
            [self.ev("A", "B"), self.ev("B", "A")])
        self.assertEqual({}, edges)
        self.assertEqual("ambiguous_cycle", rejected["A"]["reason"])
        self.assertEqual("ambiguous_cycle", rejected["B"]["reason"])

    def test_longer_cycle_rejected(self):
        edges, rejected = tri.resolve_evidence(
            [self.ev("A", "B"), self.ev("B", "C"), self.ev("C", "A")])
        self.assertEqual({}, edges)
        self.assertEqual({"A", "B", "C"}, set(rejected))

    def test_self_loop_rejected(self):
        edges, rejected = tri.resolve_evidence([self.ev("A", "A")])
        self.assertNotIn("A", edges)
        self.assertEqual("ambiguous_cycle", rejected["A"]["reason"])


class ClassifyTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            "Active1": {"flat": 100, "mains": 1},
            "Old1": {"flat": 8000, "mains": 4},
            "NoEv": {"flat": 500, "mains": 2},
            "Old2": {"flat": 300, "mains": 1},
            "Old3": {"flat": 300, "mains": 1},
            "Survivor": {"flat": 900, "mains": 3},
        }
        self.now = {"New1": {"flat": 16000, "mains": 4},
                    "Survivor": {"flat": 900, "mains": 3}}
        self.active = {"Active1"}
        self.edge = {"commit": "c1", "path": WEAPONS, "old": "Old1", "new": "New1"}
        self.resolver = lambda name: object()  # noqa: E731 - healthy resolve

    def rows(self, ids, edges=None, rejected=None, resolver=None):
        return tri.classify(ids, self.base, self.now, self.active,
                            edges or {}, rejected or {},
                            resolver or self.resolver)

    def test_active_unmeasured(self):
        rows, counts = self.rows(["Active1"])
        self.assertEqual(tri.STATUS_ACTIVE, rows[0]["status"])
        self.assertEqual(1, counts[tri.STATUS_ACTIVE])

    def test_active_wins_over_rename_evidence(self):
        edges = {"Active1": dict(self.edge, old="Active1")}
        rows, _ = self.rows(["Active1"], edges=edges)
        self.assertEqual(tri.STATUS_ACTIVE, rows[0]["status"])

    def test_resolver_exception_is_resolution_failed_not_harmless(self):
        def broken(name):
            raise RuntimeError("boom")
        rows, _ = self.rows(["Active1"], resolver=broken)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("resolution_failed", rows[0]["reason"])
        self.assertIn("RuntimeError: boom", rows[0]["error"])

    def test_resolver_none_is_resolution_failed(self):
        rows, _ = self.rows(["Active1"], resolver=lambda name: None)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("resolution_failed", rows[0]["reason"])

    def test_renamed_candidate_reports_flats_mains_ratio_and_evidence(self):
        rows, _ = self.rows(["Old1"], edges={"Old1": dict(self.edge)})
        row = rows[0]
        self.assertEqual(tri.STATUS_RENAMED, row["status"])
        self.assertEqual("New1", row["renamed_to"])
        self.assertEqual(8000, row["baseline_flat"])
        self.assertEqual(4, row["baseline_mains"])
        self.assertEqual(16000, row["current_flat"])
        self.assertEqual(4, row["current_mains"])
        self.assertEqual(2.0, row["ratio"])
        self.assertEqual({"commit": "c1", "path": WEAPONS,
                          "old": "Old1", "new": "New1"}, row["evidence"])

    def test_unresolved_without_evidence(self):
        rows, _ = self.rows(["NoEv"])
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("no_rename_evidence", rows[0]["reason"])

    def test_target_in_baseline_is_collision_not_double_assignment(self):
        edges = {"Old2": {"commit": "c1", "path": WEAPONS, "old": "Old2",
                          "new": "Survivor"}}
        rows, _ = self.rows(["Old2"], edges=edges)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("target_in_baseline_collision", rows[0]["reason"])

    def test_target_not_measured_is_unresolved_no_chains(self):
        edges = {"Old2": {"commit": "c1", "path": WEAPONS, "old": "Old2",
                          "new": "GhostTarget"}}
        rows, _ = self.rows(["Old2"], edges=edges)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("target_not_measured", rows[0]["reason"])

    def test_rejected_ambiguity_lands_on_unresolved_with_evidence(self):
        raw = [{"commit": "c1", "path": WEAPONS, "old": "Old3", "new": "A"},
               {"commit": "c1", "path": WEAPONS, "old": "Old3", "new": "B"}]
        _, rejected = tri.resolve_evidence(raw)
        rows, _ = self.rows(["Old3"], rejected=rejected)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("ambiguous_multiple_targets", rows[0]["reason"])
        self.assertEqual(raw, rows[0]["evidence"])

    def test_partition_one_row_per_raw_id_and_sum_matches(self):
        ids = ["Active1", "Old1", "NoEv", "Old2", "Old3"]
        edges = {"Old1": dict(self.edge)}
        _, rejected = tri.resolve_evidence(
            [{"commit": "c1", "path": WEAPONS, "old": "Old2", "new": "P"},
             {"commit": "c1", "path": WEAPONS, "old": "Old3", "new": "P"}])
        rows, counts = self.rows(ids, edges=edges, rejected=rejected)
        self.assertEqual([r["id"] for r in rows], ids)
        self.assertEqual(len(set(r["id"] for r in rows)), len(ids))
        self.assertEqual(len(ids), sum(counts.values()))


class GitGuardTests(unittest.TestCase):
    def test_all_git_calls_bind_repo_explicitly(self):
        run, calls = recording_run(0, FULL + "\n")
        tri.resolve_commit("7a296c96d", "R:/repo", run)
        tri.require_ancestor(FULL, "R:/repo", run)
        tri.extract_commit_pairs(FULL, "R:/repo", run)
        tri.head_commit("R:/repo", run)
        tri.worktree_dirty("R:/repo", run)
        self.assertTrue(calls)
        for cmd in calls:
            self.assertEqual(["git", "-C", "R:/repo"], cmd[:3])
        joined = [" ".join(cmd) for cmd in calls]
        self.assertTrue(any("rev-parse" in c for c in joined))
        self.assertTrue(any("merge-base" in c for c in joined))
        self.assertTrue(any(" show " in c for c in joined))
        self.assertTrue(any("status" in c for c in joined))

    def test_rev_parse_uses_end_of_options(self):
        run, calls = recording_run(0, FULL + "\n")
        tri.resolve_commit("-weird-ref", "R:/repo", run)
        self.assertIn("--end-of-options", calls[0])

    def test_unknown_commit_refused_with_exit_2(self):
        run = fake_git({"bogus^{commit}": completed(
            128, stderr="fatal: ambiguous argument")})
        with self.assertRaises(SystemExit) as cm:
            tri.resolve_commit("bogus", "R:/repo", run)
        self.assertEqual(2, cm.exception.code)

    def test_valid_commit_resolves_to_full_hash(self):
        run = fake_git({"7a296c96d^{commit}": completed(0, stdout=FULL + "\n")})
        self.assertEqual(FULL, tri.resolve_commit("7a296c96d", "R:/repo", run))

    def test_non_hash_resolution_refused(self):
        run = fake_git({"^{commit}": completed(0, stdout="abc123\n")})
        with self.assertRaises(SystemExit) as cm:
            tri.resolve_commit("abc123", "R:/repo", run)
        self.assertEqual(2, cm.exception.code)

    def test_head_failure_refused(self):
        run = fake_git({"rev-parse": completed(128, stderr="fatal: not a repo")})
        with self.assertRaises(SystemExit) as cm:
            tri.head_commit("R:/repo", run)
        self.assertEqual(2, cm.exception.code)

    def test_non_ancestor_refused_with_exit_2(self):
        run = fake_git({"merge-base": completed(1)})
        with self.assertRaises(SystemExit) as cm:
            tri.require_ancestor(FULL, "R:/repo", run)
        self.assertEqual(2, cm.exception.code)

    def test_git_show_failure_refused_with_exit_2(self):
        run = fake_git({"show": completed(128, stderr="fatal: bad object")})
        with self.assertRaises(SystemExit) as cm:
            tri.extract_commit_pairs(FULL, "R:/repo", run)
        self.assertEqual(2, cm.exception.code)

    def test_git_status_failure_refused_with_exit_2(self):
        run = fake_git({"status": completed(128, stderr="fatal")})
        with self.assertRaises(SystemExit) as cm:
            tri.worktree_dirty("R:/repo", run)
        self.assertEqual(2, cm.exception.code)

    def test_worktree_dirty_flag(self):
        clean, _ = recording_run(0, "")
        dirty, _ = recording_run(0, " M tools/audit/x.py\n")
        self.assertFalse(tri.worktree_dirty("R:/repo", clean))
        self.assertTrue(tri.worktree_dirty("R:/repo", dirty))


class RealGitBindingTests(unittest.TestCase):
    """Real git, external CWD: commands must address the bound repo only."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tmp.name) / "bound-repo"
        self.repo.mkdir()
        for args in (["init"],
                     ["-c", "user.email=t@example.com",
                      "-c", "user.name=t", "commit", "--allow-empty",
                      "-m", "init"]):
            subprocess.run(["git", "-C", str(self.repo)] + args,
                           capture_output=True, text=True, check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_resolve_and_ancestry_from_external_cwd(self):
        head = tri.head_commit(self.repo)
        self.assertRegex(head, r"^[0-9a-f]{40}$")
        self.assertEqual(head, tri.resolve_commit("HEAD", self.repo))
        tri.require_ancestor(head, self.repo)
        with self.assertRaises(SystemExit) as cm:
            tri.resolve_commit("does-not-exist", self.repo)
        self.assertEqual(2, cm.exception.code)


class ChainCoreTests(unittest.TestCase):
    """Opt-in chain mode (--follow-rename-chains): 6 core behaviours."""

    H1, H2, H3 = "1" * 40, "2" * 40, "3" * 40

    def setUp(self):
        self.base = {"Orig": {"flat": 8000, "mains": 4},
                     "Orig2": {"flat": 400, "mains": 2}}
        self.now = {"Final": {"flat": 8000, "mains": 4},
                    "Final2": {"flat": 400, "mains": 2},
                    "Measured": {"flat": 100, "mains": 1}}
        self.active = {"Final", "Final2", "Measured"}
        self.resolver = lambda name: object()  # noqa: E731 - healthy resolve

    @staticmethod
    def hop(old, new, commit, path=WEAPONS):
        return {"commit": commit, "path": path, "old": old, "new": new}

    class FakeAncestry:
        def __init__(self, ok=True, allowed=None):
            self.ok = ok
            self.allowed = dict(allowed or {})
            self.calls = []

        def strictly_ancestral(self, earlier, later):
            self.calls.append((earlier, later))
            if (earlier, later) in self.allowed:
                return self.allowed[(earlier, later)]
            return self.ok

    def chain_classify(self, ids, edges, rejected=None, ancestry=None,
                       resolver=None, active=None, base=None):
        return tri.classify(
            ids, base if base is not None else self.base, self.now,
            self.active if active is None else active,
            edges, rejected or {}, resolver or self.resolver,
            follow_chains=True, ancestry=ancestry or self.FakeAncestry())

    def test_valid_two_hop_chain_followed(self):
        edges = {"Orig": self.hop("Orig", "Mid", self.H1),
                 "Mid": self.hop("Mid", "Final", self.H2)}
        rows, counts = self.chain_classify(["Orig"], edges)
        row = rows[0]
        self.assertEqual(tri.STATUS_RENAMED, row["status"])
        self.assertEqual("Final", row["renamed_to"])
        self.assertEqual(8000, row["baseline_flat"])
        self.assertEqual(8000, row["current_flat"])
        self.assertEqual(1.0, row["ratio"])
        self.assertEqual([{"commit": self.H1, "path": WEAPONS,
                           "old": "Orig", "new": "Mid"},
                          {"commit": self.H2, "path": WEAPONS,
                           "old": "Mid", "new": "Final"}],
                         row["evidence_chain"])
        self.assertEqual(row["evidence_chain"][0], row["evidence"])
        self.assertEqual(1, counts[tri.STATUS_RENAMED])
        self.assertEqual(1, sum(counts.values()))

    def test_no_flag_one_hop_unchanged_schema(self):
        edges = {"Orig": self.hop("Orig", "Final", self.H1)}
        rows, counts = tri.classify(["Orig"], self.base, self.now,
                                    self.active, edges, {}, self.resolver)
        row = rows[0]
        self.assertEqual(tri.STATUS_RENAMED, row["status"])
        self.assertEqual("Final", row["renamed_to"])
        self.assertEqual(1.0, row["ratio"])
        self.assertNotIn("evidence_chain", row)
        self.assertEqual({"id", "baseline_flat", "baseline_mains", "status",
                          "renamed_to", "current_flat", "current_mains",
                          "ratio", "evidence"}, set(row))
        self.assertEqual({"commit": self.H1, "path": WEAPONS,
                          "old": "Orig", "new": "Final"}, row["evidence"])

    def test_same_commit_hop_rejected(self):
        edges = {"Orig": self.hop("Orig", "Mid", self.H1),
                 "Mid": self.hop("Mid", "Final", self.H1)}
        anc = self.FakeAncestry()
        rows, _ = self.chain_classify(["Orig"], edges, ancestry=anc)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("chain_same_commit", rows[0]["reason"])
        self.assertEqual([], anc.calls)
        self.assertEqual(2, len(rows[0]["evidence_chain"]))

    def test_reverse_chronology_rejected_independent_of_input_order(self):
        # Hop 1 commits later than hop 2: ancestry must fail regardless of
        # the order refs/evidence were supplied.
        edges = {"Orig": self.hop("Orig", "Mid", self.H2),
                 "Mid": self.hop("Mid", "Final", self.H1)}
        anc = self.FakeAncestry(ok=False, allowed={(self.H1, self.H2): True})
        rows, _ = self.chain_classify(["Orig"], edges, ancestry=anc)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("chain_not_ancestrally_ordered", rows[0]["reason"])
        self.assertEqual([(self.H2, self.H1)], anc.calls)

    def test_active_unmeasured_intermediate_rejected(self):
        edges = {"Orig": self.hop("Orig", "Mid", self.H1),
                 "Mid": self.hop("Mid", "Final", self.H2)}
        rows, _ = self.chain_classify(["Orig"], edges,
                                      active=self.active | {"Mid"})
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("intermediate_still_active", rows[0]["reason"])
        self.assertEqual([{"commit": self.H1, "path": WEAPONS,
                           "old": "Orig", "new": "Mid"}],
                         rows[0]["evidence_chain"])

    def test_conflicting_provenance_edge_quarantined(self):
        # Same old->new bound to two distinct commits is ambiguity - the hop
        # must never "pick the convenient first".
        raw = [self.hop("Orig", "Mid", self.H1),
               self.hop("Orig", "Mid", self.H2)]
        edges, rejected = tri.resolve_evidence_strict(raw)
        self.assertEqual({}, edges)
        self.assertEqual("ambiguous_multiple_provenance",
                         rejected["Orig"]["reason"])
        rows, _ = self.chain_classify(["Orig"], edges, rejected)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("ambiguous_multiple_provenance", rows[0]["reason"])
        self.assertEqual(raw, rows[0]["evidence"])


class ChainFoldTests(unittest.TestCase):
    """resolve_evidence_strict: provenance unambiguity + unchanged globals."""

    H1, H2 = "1" * 40, "2" * 40

    @staticmethod
    def hop(old, new, commit, path=WEAPONS):
        return {"commit": commit, "path": path, "old": old, "new": new}

    def test_duplicate_identical_evidence_collapses_harmlessly(self):
        edges, rejected = tri.resolve_evidence_strict(
            [self.hop("A", "B", self.H1), self.hop("A", "B", self.H1)])
        self.assertEqual({}, rejected)
        self.assertEqual("B", edges["A"]["new"])

    def test_same_pair_distinct_paths_rejected(self):
        raw = [self.hop("A", "B", self.H1),
               self.hop("A", "B", self.H1, "mods/cameo/weapons/tier1.yaml")]
        edges, rejected = tri.resolve_evidence_strict(raw)
        self.assertEqual({}, edges)
        self.assertEqual("ambiguous_multiple_provenance",
                         rejected["A"]["reason"])
        self.assertEqual(raw, rejected["A"]["evidence"])

    def test_fan_in_uses_all_raw_edges_including_rejected_sources(self):
        edges, rejected = tri.resolve_evidence_strict(
            [self.hop("A", "X", self.H1), self.hop("B", "X", self.H2),
             self.hop("B", "Y", self.H2)])
        self.assertEqual({}, edges)
        self.assertEqual("ambiguous_shared_target", rejected["A"]["reason"])
        self.assertEqual("ambiguous_multiple_targets", rejected["B"]["reason"])

    def test_cycles_still_rejected_in_strict_fold(self):
        edges, rejected = tri.resolve_evidence_strict(
            [self.hop("A", "B", self.H1), self.hop("B", "A", self.H2)])
        self.assertEqual({}, edges)
        self.assertEqual({"A", "B"}, set(rejected))
        self.assertTrue(all(r["reason"] == "ambiguous_cycle"
                            for r in rejected.values()))


class ChainNegativeTests(unittest.TestCase):
    """Remaining opt-in chain-mode coverage (negative + accounting)."""

    H1, H2, H3 = "1" * 40, "2" * 40, "3" * 40

    def setUp(self):
        self.base = {"Orig": {"flat": 8000, "mains": 4},
                     "Orig2": {"flat": 400, "mains": 2},
                     "MidBase": {"flat": 100, "mains": 1}}
        self.now = {"Final": {"flat": 8000, "mains": 4},
                    "Final2": {"flat": 400, "mains": 2}}
        self.active = {"Final", "Final2"}
        self.resolver = lambda name: object()  # noqa: E731 - healthy resolve

    @staticmethod
    def hop(old, new, commit, path=WEAPONS):
        return {"commit": commit, "path": path, "old": old, "new": new}

    class FakeAncestry:
        def __init__(self, ok=True, allowed=None):
            self.ok = ok
            self.allowed = dict(allowed or {})
            self.calls = []

        def strictly_ancestral(self, earlier, later):
            self.calls.append((earlier, later))
            if (earlier, later) in self.allowed:
                return self.allowed[(earlier, later)]
            return self.ok

    def chain_classify(self, ids, edges, rejected=None, ancestry=None,
                       resolver=None, active=None, base=None, now=None):
        return tri.classify(
            ids, base if base is not None else self.base,
            now if now is not None else self.now,
            self.active if active is None else active,
            edges, rejected or {}, resolver or self.resolver,
            follow_chains=True, ancestry=ancestry or self.FakeAncestry())

    def test_valid_three_hop_chain(self):
        edges = {"Orig": self.hop("Orig", "M1", self.H1),
                 "M1": self.hop("M1", "M2", self.H2),
                 "M2": self.hop("M2", "Final", self.H3)}
        rows, counts = self.chain_classify(["Orig"], edges)
        self.assertEqual(tri.STATUS_RENAMED, rows[0]["status"])
        self.assertEqual("Final", rows[0]["renamed_to"])
        self.assertEqual(3, len(rows[0]["evidence_chain"]))
        self.assertEqual(1, counts[tri.STATUS_RENAMED])

    def test_ref_input_order_independence(self):
        # Evidence gathered in reverse ref order folds and walks the same.
        ev = [self.hop("M1", "Final", self.H2),
              self.hop("Orig", "M1", self.H1)]
        edges, rejected = tri.resolve_evidence_strict(ev)
        rows, _ = self.chain_classify(["Orig"], edges, rejected)
        self.assertEqual(tri.STATUS_RENAMED, rows[0]["status"])
        self.assertEqual("Final", rows[0]["renamed_to"])
        self.assertEqual([self.H1, self.H2],
                         [h["commit"] for h in rows[0]["evidence_chain"]])

    def test_incomparable_branches_rejected(self):
        edges = {"Orig": self.hop("Orig", "M", self.H1),
                 "M": self.hop("M", "Final", self.H2)}
        rows, _ = self.chain_classify(["Orig"], edges,
                                      ancestry=self.FakeAncestry(ok=False))
        self.assertEqual("chain_not_ancestrally_ordered", rows[0]["reason"])

    def test_repeated_node_cycle_rejected_with_full_chain(self):
        edges = {"Orig": self.hop("Orig", "M", self.H1),
                 "M": self.hop("M", "Orig", self.H2)}
        rows, _ = self.chain_classify(["Orig"], edges)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("chain_cycle", rows[0]["reason"])
        self.assertEqual(2, len(rows[0]["evidence_chain"]))

    def test_self_loop_repeated_node_rejected(self):
        edges = {"Orig": self.hop("Orig", "M", self.H1),
                 "M": self.hop("M", "M", self.H2)}
        rows, _ = self.chain_classify(["Orig"], edges)
        self.assertEqual("chain_cycle", rows[0]["reason"])

    def test_fan_in_from_rejected_source_blocks_chain(self):
        raw = [self.hop("A", "X", self.H1), self.hop("B", "X", self.H2),
               self.hop("B", "Y", self.H2)]
        edges, rejected = tri.resolve_evidence_strict(raw)
        rows, _ = self.chain_classify(["A"], edges, rejected)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("ambiguous_shared_target", rows[0]["reason"])

    def test_intermediate_outgoing_ambiguity_never_routed_around(self):
        edges = {"Orig": self.hop("Orig", "Mid", self.H1)}
        rejected = {"Mid": {"reason": "ambiguous_multiple_targets",
                            "evidence": [self.hop("Mid", "X", self.H2),
                                         self.hop("Mid", "Y", self.H2)]}}
        rows, _ = self.chain_classify(["Orig"], edges, rejected)
        row = rows[0]
        self.assertEqual(tri.STATUS_UNRESOLVED, row["status"])
        self.assertEqual("ambiguous_multiple_targets", row["reason"])
        self.assertEqual([{"commit": self.H1, "path": WEAPONS,
                           "old": "Orig", "new": "Mid"}],
                         row["evidence_chain"])
        self.assertEqual(row["evidence"], row["evidence_chain"][0])
        self.assertEqual(rejected["Mid"]["evidence"], row["rejection_evidence"])

    def test_baseline_measured_intermediate_rejected(self):
        edges = {"Orig": self.hop("Orig", "MidBase", self.H1),
                 "MidBase": self.hop("MidBase", "Final", self.H2)}
        rows, _ = self.chain_classify(["Orig"], edges)
        self.assertEqual("intermediate_in_baseline_collision",
                         rows[0]["reason"])

    def test_baseline_measured_terminal_rejected(self):
        edges = {"Orig": self.hop("Orig", "MidBase", self.H1)}
        rows, _ = self.chain_classify(["Orig"], edges)
        self.assertEqual("target_in_baseline_collision", rows[0]["reason"])
        self.assertEqual(1, len(rows[0]["evidence_chain"]))

    def test_missing_hop_no_fuzzy_bridging(self):
        # Ghost has no evidence anywhere: no fuzzy bridging, precise reason,
        # partial chain visible.
        edges = {"Orig": self.hop("Orig", "Ghost", self.H1)}
        rows, _ = self.chain_classify(["Orig"], edges)
        row = rows[0]
        self.assertEqual(tri.STATUS_UNRESOLVED, row["status"])
        self.assertEqual("terminal_not_active", row["reason"])
        self.assertEqual("Ghost", row["chain_terminal"])
        self.assertEqual([{"commit": self.H1, "path": WEAPONS,
                           "old": "Orig", "new": "Ghost"}],
                         row["evidence_chain"])

    def test_active_unmeasured_terminal_is_target_not_measured(self):
        edges = {"Orig": self.hop("Orig", "ActGhost", self.H1)}
        rows, _ = self.chain_classify(["Orig"], edges,
                                      active=self.active | {"ActGhost"})
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("target_not_measured", rows[0]["reason"])

    def test_inactive_measured_terminal_is_terminal_not_active(self):
        edges = {"Orig": self.hop("Orig", "Final", self.H1)}
        rows, _ = self.chain_classify(["Orig"], edges, active=set())
        self.assertEqual("terminal_not_active", rows[0]["reason"])

    def test_terminal_resolver_none_is_explicit_failure(self):
        edges = {"Orig": self.hop("Orig", "Final", self.H1)}
        rows, _ = self.chain_classify(["Orig"], edges,
                                      resolver=lambda name: None)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("terminal_resolution_failed", rows[0]["reason"])
        self.assertIn("None", rows[0]["error"])

    def test_terminal_resolver_raises_is_explicit_failure(self):
        def boom(name):
            raise RuntimeError("boom")
        edges = {"Orig": self.hop("Orig", "Final", self.H1)}
        rows, _ = self.chain_classify(["Orig"], edges, resolver=boom)
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("terminal_resolution_failed", rows[0]["reason"])
        self.assertIn("RuntimeError: boom", rows[0]["error"])

    def test_two_origins_one_terminal_both_downgraded(self):
        h4 = "4" * 40
        edges = {"Orig": self.hop("Orig", "M1", self.H1),
                 "M1": self.hop("M1", "Final", self.H2),
                 "Orig2": self.hop("Orig2", "M2", self.H3),
                 "M2": self.hop("M2", "Final", h4)}
        rows, counts = self.chain_classify(["Orig", "Orig2"], edges)
        for row in rows:
            self.assertEqual(tri.STATUS_UNRESOLVED, row["status"])
            self.assertEqual("ambiguous_converging_terminal", row["reason"])
            self.assertEqual("Final", row["chain_terminal"])
            self.assertNotIn("renamed_to", row)
            self.assertEqual(2, len(row["evidence_chain"]))
        self.assertEqual(["Orig", "Orig2"], rows[0]["converging_origins"])
        self.assertEqual(0, counts[tri.STATUS_RENAMED])
        self.assertEqual(2, counts[tri.STATUS_UNRESOLVED])

    def test_raw_sum_and_one_row_per_id_with_chains(self):
        base = dict(self.base, NoEv={"flat": 5, "mains": 1},
                    Act1={"flat": 6, "mains": 1})
        active = self.active | {"Act1"}
        edges = {"Orig": self.hop("Orig", "M1", self.H1),
                 "M1": self.hop("M1", "Final", self.H2),
                 "Orig2": self.hop("Orig2", "MidBase", self.H3),
                 "MidBase": self.hop("MidBase", "Gone", self.H3)}
        ids = ["Orig", "Orig2", "MidBase", "NoEv", "Act1"]
        rows, counts = self.chain_classify(ids, edges, active=active,
                                           base=base)
        self.assertEqual(ids, [r["id"] for r in rows])
        self.assertEqual(len(ids), sum(counts.values()))
        self.assertEqual(1, counts[tri.STATUS_RENAMED])   # Orig
        self.assertEqual(1, counts[tri.STATUS_ACTIVE])    # Act1
        self.assertEqual(3, counts[tri.STATUS_UNRESOLVED])

    def test_invalid_hop_commit_hash_refused_exit_2(self):
        anc = tri.AncestryChecker("R:/repo",
                                  run=lambda cmd: completed(0, "y"))
        edges = {"Orig": self.hop("Orig", "Mid", self.H1),
                 "Mid": self.hop("Mid", "Final", "abc")}
        with self.assertRaises(SystemExit) as cm:
            self.chain_classify(["Orig"], edges, ancestry=anc)
        self.assertEqual(2, cm.exception.code)


class AncestryCheckerTests(unittest.TestCase):
    def test_binds_repo_and_uses_merge_base(self):
        run, calls = recording_run(0, "y\n")
        anc = tri.AncestryChecker("R:/repo", run=run)
        anc.strictly_ancestral(FULL, "b" * 40)
        self.assertTrue(calls)
        for cmd in calls:
            self.assertEqual(["git", "-C", "R:/repo"], cmd[:3])
        joined = [" ".join(cmd) for cmd in calls]
        self.assertTrue(any("merge-base" in c and "--is-ancestor" in c
                            for c in joined))

    def test_rc0_true_rc1_false(self):
        run = fake_git({"is-ancestor": completed(0, "")})
        anc = tri.AncestryChecker("R:/repo", run=run)
        self.assertTrue(anc.strictly_ancestral(FULL, "b" * 40))
        run1 = fake_git({"is-ancestor": completed(1, "")})
        anc1 = tri.AncestryChecker("R:/repo", run=run1)
        self.assertFalse(anc1.strictly_ancestral(FULL, "b" * 40))

    def test_rc_above_one_refuses_exit_2(self):
        run = fake_git({"is-ancestor": completed(2, stderr="fatal")})
        anc = tri.AncestryChecker("R:/repo", run=run)
        with self.assertRaises(SystemExit) as cm:
            anc.strictly_ancestral(FULL, "b" * 40)
        self.assertEqual(2, cm.exception.code)

    def test_same_hash_false_without_git_call(self):
        run, calls = recording_run(0, "")
        anc = tri.AncestryChecker("R:/repo", run=run)
        self.assertFalse(anc.strictly_ancestral(FULL, FULL))
        self.assertEqual([], calls)

    def test_cached_per_ordered_pair(self):
        calls = []

        def counting(cmd):
            calls.append(list(cmd))
            return completed(0 if len(calls) == 1 else 1, "")

        anc = tri.AncestryChecker("R:/repo", run=counting)
        self.assertTrue(anc.strictly_ancestral(FULL, "b" * 40))
        self.assertTrue(anc.strictly_ancestral(FULL, "b" * 40))  # cached
        self.assertFalse(anc.strictly_ancestral("b" * 40, FULL))  # reversed
        self.assertEqual(2, len(calls))

    def test_invalid_hash_refused_before_git_call(self):
        run, calls = recording_run(0, "")
        anc = tri.AncestryChecker("R:/repo", run=run)
        with self.assertRaises(SystemExit) as cm:
            anc.strictly_ancestral(FULL, "abc")
        self.assertEqual(2, cm.exception.code)
        self.assertEqual([], calls)


class _TempGitRepoTestCase(unittest.TestCase):
    X_FILE = "mods/cameo/ContentPacks/X/yaml/weapons.yaml"
    Y_FILE = "mods/cameo/ContentPacks/Y/yaml/weapons.yaml"
    A_YAML = "A:\n\tInherits: ^Base\n"
    B_YAML = "B:\n\tInherits: ^Base\n"
    C_YAML = "C:\n\tInherits: ^Base\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self._git(["init"])

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, args):
        subprocess.run(["git", "-C", str(self.repo)] + args,
                       capture_output=True, text=True, check=True)

    def _commit(self, files, msg, allow_empty=False):
        for rel, content in files:
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content.encode("utf-8"))
            self._git(["add", rel])
        argv = ["-c", "user.email=t@example.com", "-c", "user.name=t",
                "commit", "-m", msg]
        if allow_empty and files:
            argv.append("--allow-empty")
        if not files:
            argv.append("--allow-empty")
        self._git(argv)
        return tri.head_commit(self.repo)

    def _pairs(self, commit):
        return [{"commit": commit, **p}
                for p in tri.extract_commit_pairs(commit, self.repo)]

    def _chain_rows(self, evidences, ids=("A",), base=None, now=None,
                    active=None):
        edges, rejected = tri.resolve_evidence_strict(evidences)
        ancestry = tri.AncestryChecker(self.repo)
        return tri.classify(ids, base, now, active, edges, rejected,
                            lambda n: object(), follow_chains=True,
                            ancestry=ancestry)


class AncestryRealGitTests(_TempGitRepoTestCase):
    def test_proper_ancestor_asymmetry_and_cache(self):
        c1 = self._commit([], "one")
        c2 = self._commit([], "two")
        calls = []

        def counting(cmd):
            calls.append(list(cmd))
            return tri._git(cmd)

        anc = tri.AncestryChecker(self.repo, run=counting)
        self.assertTrue(anc.strictly_ancestral(c1, c2))
        self.assertFalse(anc.strictly_ancestral(c2, c1))
        self.assertTrue(anc.strictly_ancestral(c1, c2))  # cached
        self.assertEqual(2, len(calls))

    def test_incomparable_two_branches_both_false(self):
        c0 = self._commit([], "root")
        c_master = self._commit([], "master-only")
        self._git(["checkout", "-q", "-b", "side", c0])
        c_side = self._commit([], "side-only")
        self._git(["checkout", "-q", "-"])
        anc = tri.AncestryChecker(self.repo)
        self.assertFalse(anc.strictly_ancestral(c_master, c_side))
        self.assertFalse(anc.strictly_ancestral(c_side, c_master))


class ChainRealGitTests(_TempGitRepoTestCase):
    def setUp(self):
        super().setUp()
        self.c0 = self._commit([(self.X_FILE, self.A_YAML),
                                (self.Y_FILE, self.B_YAML)], "base")

    def test_ordered_two_hop_end_to_end(self):
        c1 = self._commit([(self.X_FILE, self.B_YAML)], "A to B")
        c2 = self._commit([(self.Y_FILE, self.C_YAML)], "B to C")
        rows, counts = self._chain_rows(
            self._pairs(c1) + self._pairs(c2),
            base={"A": {"flat": 8000, "mains": 4}},
            now={"C": {"flat": 8000, "mains": 4}}, active={"C"})
        row = rows[0]
        self.assertEqual(tri.STATUS_RENAMED, row["status"])
        self.assertEqual("C", row["renamed_to"])
        self.assertEqual([c1, c2], [h["commit"] for h in
                                    row["evidence_chain"]])
        self.assertEqual(1, counts[tri.STATUS_RENAMED])

    def test_reverse_ref_input_order_same_result(self):
        c1 = self._commit([(self.X_FILE, self.B_YAML)], "A to B")
        c2 = self._commit([(self.Y_FILE, self.C_YAML)], "B to C")
        rows, _ = self._chain_rows(
            self._pairs(c2) + self._pairs(c1),
            base={"A": {"flat": 8000, "mains": 4}},
            now={"C": {"flat": 8000, "mains": 4}}, active={"C"})
        self.assertEqual(tri.STATUS_RENAMED, rows[0]["status"])
        self.assertEqual("C", rows[0]["renamed_to"])
        self.assertEqual([c1, c2], [h["commit"] for h in
                                    rows[0]["evidence_chain"]])

    def test_reverse_chronology_rejected(self):
        c1 = self._commit([(self.Y_FILE, self.C_YAML)], "B to C first")
        c2 = self._commit([(self.X_FILE, self.B_YAML)], "A to B later")
        rows, _ = self._chain_rows(
            self._pairs(c2) + self._pairs(c1),
            base={"A": {"flat": 8000, "mains": 4}}, now={}, active=set())
        self.assertEqual(tri.STATUS_UNRESOLVED, rows[0]["status"])
        self.assertEqual("chain_not_ancestrally_ordered", rows[0]["reason"])

    def test_same_commit_two_hunks_rejected(self):
        c = self._commit([(self.X_FILE, self.B_YAML),
                          (self.Y_FILE, self.C_YAML)], "both in one")
        rows, _ = self._chain_rows(
            self._pairs(c), base={"A": {"flat": 8000, "mains": 4}},
            now={}, active=set())
        self.assertEqual("chain_same_commit", rows[0]["reason"])

    def test_incomparable_branches_rejected(self):
        c_master = self._commit([(self.X_FILE, self.B_YAML)], "A to B")
        self._git(["checkout", "-q", "-b", "side", self.c0])
        c_side = self._commit([(self.Y_FILE, self.C_YAML)], "B to C side")
        self._git(["checkout", "-q", "-"])
        rows, _ = self._chain_rows(
            self._pairs(c_master) + self._pairs(c_side),
            base={"A": {"flat": 8000, "mains": 4}}, now={}, active=set())
        self.assertEqual("chain_not_ancestrally_ordered", rows[0]["reason"])

    def test_non_ancestor_ref_still_refused_real_git(self):
        c_master = self._commit([(self.X_FILE, self.B_YAML)], "A to B")
        self._git(["checkout", "-q", "-b", "side", self.c0])
        c_side = self._commit([(self.Y_FILE, self.C_YAML)], "side only")
        self._git(["checkout", "-q", "-"])
        # An ancestor-of-HEAD commit is accepted...
        tri.require_ancestor(c_master, self.repo)
        # ...an unmerged side-branch commit is refused with exit 2.
        with self.assertRaises(SystemExit) as cm:
            tri.require_ancestor(c_side, self.repo)
        self.assertEqual(2, cm.exception.code)


class BuildReportSchemaTests(unittest.TestCase):
    BASE_KEYS = {"what", "measurement_basis", "worktree_dirty", "caveat",
                 "gitHEAD", "releasecommit", "release_tag", "raw_unmatched",
                 "classified", "classified_sum", "rename_commits", "rows"}

    @staticmethod
    def _run():
        return fake_git({"rev-parse": completed(0, FULL + "\n"),
                         "status": completed(0, "")})

    def test_default_schema_unchanged_optin_adds_keys_only_when_opted(self):
        meta = {"_release_commit": FULL, "_release_tag": "baseline"}
        base = {"A": {"flat": 100, "mains": 1}}
        now = {"B": {"flat": 100, "mains": 1}}
        saved = (tri.load_baseline, tri.snapshot, tri.miniyaml)

        class FakeRS:
            weapons = {"B"}

            def resolve_weapon(self, name):
                return object()

        tri.load_baseline = lambda repo: (meta, base)
        tri.snapshot = lambda repo: now
        tri.miniyaml = types.SimpleNamespace(Ruleset=lambda repo: FakeRS())
        try:
            default = tri.build_report("R:/repo", [], run=self._run())
            opted = tri.build_report("R:/repo", [], run=self._run(),
                                     follow_chains=True)
        finally:
            tri.load_baseline, tri.snapshot, tri.miniyaml = saved
        self.assertEqual(self.BASE_KEYS, set(default))
        self.assertNotIn("follow_rename_chains", default)
        self.assertEqual(self.BASE_KEYS | {"follow_rename_chains",
                                           "chain_collision_coverage"},
                         set(opted))
        self.assertTrue(opted["follow_rename_chains"])
        self.assertEqual(default["rows"], opted["rows"])
        self.assertEqual(default["raw_unmatched"], opted["raw_unmatched"])
        self.assertEqual(1, opted["classified_sum"])


if __name__ == "__main__":
    unittest.main()
