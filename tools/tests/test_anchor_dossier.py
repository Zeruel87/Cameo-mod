"""Dossiers expose missing evidence and preserve hand-reviewed output."""
import contextlib
import copy
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/balance"), str(ROOT / "tools/audit")]
import propose_anchor_spec as dossier
import derive_virtual_anchor as virtual
import miniyaml


def member(actor="a", cls="mbt", cost=800):
    unit = dict(hp={"v": 100000}, speed={"v": 100}, cost={"v": cost},
                armaments=[dict(weapon="Gun", range=4000)])
    return dict(actor=actor, faction="tiberiandawn_gdi", cls=cls, unit=unit,
                **virtual.stat_values(unit))


def excluded_row(actor="huge", cost=9000):
    """A classified member that fails fitting eligibility (ledger row shape)."""
    unit = dict(hp={"v": 900000}, speed={"v": 100}, cost={"v": cost},
                armaments=[dict(weapon="Gun", range=4000)])
    return dict(actor=actor, faction="tiberiandawn_gdi", **virtual.stat_values(unit))


class ReferenceJoinTests(unittest.TestCase):
    def evidence(self, refs, peers, crows=None, heroes=None):
        with patch.object(dossier.rd, "peer_rows", return_value=peers), \
                patch.object(dossier.rd, "peer_hero_rows", return_value=heroes or []), \
                patch.object(dossier.rd, "cameo_rows", return_value=crows if crows is not None else [{"id": "a"}]), \
                patch.object(dossier.rd, "build_distributions", return_value={"Cameo": {}}), \
                patch.object(dossier.rt, "add_cost_distribution"), \
                patch.object(dossier.rt, "expand_families", side_effect=lambda rows, _: rows), \
                patch.object(dossier.rt, "target_for", return_value=(90, 100, 1)) as target:
            result = dossier.reference_evidence([member()], {"a": refs})["a"]
            return result, target.call_count

    def test_exact_id_wins_over_same_name(self):
        peers = [dict(source="s", id="first", name="Tank"), dict(source="s", id="second", name="Tank")]
        result, calls = self.evidence({"s": dict(id="second", confidence="STRONG")}, peers)
        self.assertEqual(result["used"], [dict(source="s", id="second")])
        self.assertEqual(calls, 5)  # HP, speed, range, cost and nominal DPS
        self.assertEqual(result["targets"]["hp"], dict(value=100, sources=1))

    def test_missing_or_duplicate_id_withholds_partial_synthesis(self):
        for peers in ([], [dict(source="s", id="id"), dict(source="s", id="id")]):
            result, calls = self.evidence({"s": dict(id="id", confidence="FAIR")}, peers)
            self.assertTrue(result["errors"])
            self.assertEqual(result["targets"], {})
            self.assertEqual(calls, 0)

    def test_accepted_assignment_without_id_is_reported(self):
        result, calls = self.evidence({"s": dict(name="Tank", confidence="STRONG")}, [])
        self.assertIn("lacks exact ID", result["errors"][0])
        self.assertEqual(calls, 0)

    def test_weak_reference_is_not_readmitted(self):
        result, calls = self.evidence({"s": dict(id="id", confidence="WEAK")}, [dict(source="s", id="id")])
        self.assertEqual(result["used"], [])
        self.assertEqual(calls, 0)

    def test_hero_absence_does_not_reinsert_into_ordinary_population(self):
        result, calls = self.evidence({"s": dict(id="id", confidence="STRONG")}, [dict(source="s", id="id")], [])
        self.assertIn("hero/eligibility", result["errors"][0])
        self.assertEqual(calls, 0)

    def test_hero_source_is_identified_without_polluting_distribution(self):
        result, calls = self.evidence({"s": dict(id="id", confidence="STRONG")}, [], [],
                                     heroes=[dict(source="s", id="id")])
        self.assertEqual(result["hero_references"], [dict(source="s", id="id")])
        self.assertEqual(result["used"], [])
        self.assertIn("hero-only evidence", result["errors"][0])
        self.assertEqual(calls, 0)


class SourceProvenanceTests(unittest.TestCase):
    def test_real_provenance_fingerprints_membership_tier_firepower_and_w24_predicate(self):
        modules = dossier.source_provenance(dossier.ROOT)["code_sha256"]
        for name in ("tools/balance/class_membership.py", "tools/balance/firepower.py",
                     "tools/balance/tier_chain.py", "tools/audit/audit_three_way_split.py"):
            self.assertIn(name, modules)

    def test_changed_module_evidence_refuses_output_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                run_fixture(root, ["--all"], source=[{}, dict(changed=True)])
            self.assertFalse((root / "docs/balance/anchors").exists())


class RegistryRaceTests(unittest.TestCase):
    def test_registry_rewrite_between_read_and_evidence_refuses_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            ledger = root / "docs/balance"
            (ledger / "derived").mkdir(parents=True)
            registry = ledger / "class_anchors.json"
            registry.write_text(json.dumps({"mbt": {}, "support": {}}), encoding="utf-8")
            (ledger / "derived/reference_assignment.json").write_text(
                json.dumps({"assignment": {}}), encoding="utf-8")
            real_load_evidence = virtual.load_evidence

            def replace_registry(_ledger):
                registry.write_text(json.dumps({"mbt": {"spec": {}}, "support": {}}), encoding="utf-8")
                return real_load_evidence(_ledger)

            with patch.object(dossier, "ROOT", root), \
                    patch.object(dossier, "source_provenance", side_effect=[{}, {}]), \
                    patch.object(virtual, "load_evidence", side_effect=replace_registry), \
                    contextlib.redirect_stdout(io.StringIO()) as output, \
                    contextlib.redirect_stderr(io.StringIO()) as errors:
                with self.assertRaises(SystemExit):
                    dossier.main(["--all"])
            self.assertIn("class_anchors.json changed", errors.getvalue())
            self.assertEqual(output.getvalue(), "")
            self.assertFalse((root / "docs/balance/anchors").exists())

    def test_stable_registry_fingerprint_allows_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.assertEqual(run_fixture(root, ["--all"]), 0)
            self.assertEqual(sorted(p.name for p in (root / "docs/balance/anchors").iterdir()),
                             ["mbt.md", "support.md"])


class DossierRenderTests(unittest.TestCase):
    def render(self, cls="mbt", members=None, debt=None, error=None, assignments=None, factions=None,
               excluded=()):
        members = members if members is not None else [member()]
        snapshots = {role: dict(actor=None, ledger={}, live={}, error="not nominated")
                     for role in ("anchor", "verifier")}
        return dossier.render(cls, {}, virtual.derive(cls, members, assignments or {},
                              factions=factions or virtual.DEFAULT_FACTIONS), members,
            assignments or {},
            {m["actor"]: dict(errors=[], used=[], targets={}) for m in members},
            snapshots, debt or [], error, {}, excluded_members=excluded)

    def test_fixed_sections_and_no_approval_or_dps_target(self):
        text = self.render()
        headings = [line for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(len(headings), 7)
        self.assertEqual([line.split()[1] for line in headings], [f"{i}." for i in range(1, 8)])
        self.assertIn("NOT READY / UNAPPROVED", text)
        self.assertNotIn("dps0", text)
        self.assertIn("THIN hp", text)
        self.assertIn("fit-eligible class percentile", text)

    def test_membership_sorted_by_cost(self):
        text = self.render(members=[member("expensive", cost=1000), member("cheap", cost=100)])
        self.assertLess(text.index("| cheap |"), text.index("| expensive |"))

    def test_no_source_and_no_automatic_borrowing(self):
        text = self.render(cls="dreadnought", members=[])
        self.assertIn("NO SOURCE", text)
        self.assertIn("unavailable", text)

    def test_section1_names_pool_and_per_axis_contributors(self):
        a, b = member("a", cost=800), member("b", cost=900)
        b["faction"] = "starcraft_terran"
        text = self.render(members=[a, b],
                           assignments={"a": {"game": dict(id="T1", confidence="STRONG")}},
                           factions=("tiberiandawn_gdi",))
        section1 = text.split("## 1. The proposal", 1)[1].split("## 2.", 1)[0]
        self.assertIn("Source pool: selected factions tiberiandawn_gdi", section1)
        self.assertIn("1 of 2 fit-eligible class members are in the selected factions", section1)
        self.assertIn("contributing actors", section1)
        self.assertIn("| a | reference-backed ledger medians", section1)
        # The outside-faction member carries its own REF assignment but is not a
        # contributor: section 1 names the selected pool, not global membership.
        self.assertNotIn("starcraft_terran", section1)
        self.assertNotIn("| a, b |", section1)

    def test_section1_denominator_is_fit_eligible_not_section4_rows(self):
        a, b = member("a", cost=800), member("b", cost=900)
        text = self.render(members=[a, b], excluded=[excluded_row("huge")])
        section1 = text.split("## 1. The proposal", 1)[1].split("## 2.", 1)[0]
        # full_count is fit-eligible only: the excluded section-4 row must not
        # inflate the pool denominator, nor appear as a contributor.
        self.assertIn("2 of 2 fit-eligible class members are in the selected factions", section1)
        self.assertNotIn("huge", section1)
        membership = text.split("## 4. Membership", 1)[1].split("## 5.", 1)[0]
        self.assertIn("| huge |", membership)

    def test_per_axis_contributor_sets_differ_when_a_member_lacks_a_stat(self):
        a, b = member("a", cost=800), member("b", cost=900)
        a["cost"] = None
        text = self.render(members=[a, b])
        section1 = text.split("## 1. The proposal", 1)[1].split("## 2.", 1)[0]
        self.assertIn("| a, b | ledger medians / no reference preference", section1)
        self.assertIn("| b | ledger medians / no reference preference", section1)

    def test_backed_members_lacking_stat_falls_back_with_plain_basis(self):
        a, b = member("a", cost=800), member("b", cost=900)
        a["cost"] = None
        text = self.render(members=[a, b],
                           assignments={"a": {"game": dict(id="T1", confidence="STRONG")}})
        section1 = text.split("## 1. The proposal", 1)[1].split("## 2.", 1)[0]
        self.assertIn("| a | reference-backed ledger medians", section1)
        self.assertIn("| b | ledger medians / no reference-backed member has this stat; "
                      "using available selected-faction members", section1)

    def test_no_source_dossier_qualifies_pool_not_global_absence(self):
        a = member("a", cls="dreadnought")
        a["faction"] = "starcraft_terran"
        text = self.render(cls="dreadnought", members=[a],
                           assignments={"a": {"game": dict(id="DN1", confidence="STRONG")}},
                           factions=("tiberiandawn_gdi",))
        self.assertIn("Status: NO SOURCE", text)
        self.assertIn("NO SOURCE means no eligible member", text)
        section1 = text.split("## 1. The proposal", 1)[1].split("## 2.", 1)[0]
        self.assertIn("0 of 1 fit-eligible class members are in the selected factions", section1)
        self.assertIn("tiberiandawn_gdi", section1)
        headings = [line for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(len(headings), 7)

    def test_reviewed_raw_debt_and_unavailable_gate_both_visible(self):
        self.assertIn("`HydraSpit`: 4 mains", self.render(debt=[("hydra", "HydraSpit", 4)]))
        self.assertIn("UNAVAILABLE — bad weapon", self.render(error="bad weapon"))

    def test_resolved_actor_snapshot_matches_committed_ground_domain(self):
        rules = miniyaml.Ruleset(ROOT)
        rows = {a: (section, rec) for _, section, a, rec in dossier.readiness.load_units()}
        snapshot = dossier.actor_snapshot("td_gdi_apc", rows, rules)
        self.assertEqual(snapshot["live"], snapshot["ledger"])
        self.assertEqual(snapshot["live"]["range_wdist"], 5668)
        self.assertIsNone(snapshot["error"])

    def test_snapshot_exposes_stale_ledger_instead_of_calling_it_live(self):
        rec = member()["unit"]
        fresh = copy.deepcopy(rec)
        fresh["hp"]["v"] = 200000
        with patch.object(dossier.extract_stats, "extract_actor", return_value=fresh):
            snapshot = dossier.actor_snapshot("a", {"a": ("vehicles", rec)}, object())
        self.assertEqual(snapshot["ledger"]["hp"], 100000)
        self.assertEqual(snapshot["live"]["hp"], 200000)

    def test_missing_tier_or_k_is_not_declared_equal_to_unity(self):
        rec = member()["unit"]
        rec["armaments"][0].update(slot="Armament", pricing=True, reloaddelay=20, burst=1,
                                   damage_warheads=[dict(type="AreaDamage", damage=2000)])
        with patch.object(dossier.extract_stats, "extract_actor", return_value=rec):
            snapshot = dossier.actor_snapshot("a", {"a": ("vehicles", rec)}, object())
            measured = dossier.actor_snapshot("a", {"a": ("vehicles", rec)}, object(),
                {"a": dict(tier_multiplier=.5, armaments=[dict(slot="Armament", weapon="Gun", effective_dps=50)])})
        self.assertIsNone(snapshot["metrics"]["tech_tier"])
        self.assertIsNone(snapshot["metrics"]["aggregate_K"])
        self.assertEqual(measured["metrics"]["aggregate_K"], .5)
        self.assertEqual(measured["metrics"]["tech_tier"], .5)


class MembershipLiveTests(unittest.TestCase):
    def render(self, members, excluded=(), live=None, spec=None, snapshots=None):
        cls = "mbt"
        snapshots = snapshots or {role: dict(actor=None, ledger={}, live={}, error="not nominated")
                                  for role in ("anchor", "verifier")}
        return dossier.render(cls, dict(spec=spec) if spec else {}, virtual.derive(cls, members, {}),
            members, {}, {m["actor"]: dict(errors=[], used=[], targets={}) for m in members},
            snapshots, [], None, {}, excluded_members=excluded, live_by_actor=live or {})

    @staticmethod
    def live_row(**axes):
        return dict(values=axes, issue=None)

    def test_membership_shows_live_axes_with_explicit_basis(self):
        text = self.render(members=[member()], live={"a": self.live_row(
            hp=100000, speed=100, range_wdist=4000, cost=800)})
        row = [line for line in text.splitlines() if line.startswith("| a |")][0]
        self.assertIn("| live resolved YAML |", row)
        for value in ("100000", "100", "4000", "800"):
            self.assertIn(value, row)

    def test_membership_sorted_by_live_cost_unavailable_last(self):
        members = [member("a_mid", cost=800), member("z_cheap", cost=100), member("b_ghost", cost=999)]
        text = self.render(members=members, live={
            "a_mid": self.live_row(hp=100000, speed=100, range_wdist=4000, cost=800),
            "z_cheap": self.live_row(hp=100000, speed=100, range_wdist=4000, cost=100),
            "b_ghost": dict(values={}, issue="unresolved or non-balance actor")})
        membership = text.split("## 4. Membership", 1)[1].split("## 5.", 1)[0]
        self.assertLess(membership.index("| z_cheap |"), membership.index("| a_mid |"))
        self.assertLess(membership.index("| a_mid |"), membership.index("| b_ghost |"))

    def test_unresolved_member_is_unavailable_with_explicit_issue_never_live(self):
        text = self.render(members=[member("ghost")], live={
            "ghost": dict(values={}, issue="unresolved or non-balance actor")})
        row = [line for line in text.splitlines() if line.startswith("| ghost |")][0]
        self.assertIn("unavailable", row)
        self.assertIn("live unavailable: unresolved or non-balance actor", row)
        self.assertNotIn("live resolved YAML", row)
        self.assertIn("| ghost / hp | 100000 | unavailable | unavailable | "
                      "unavailable — unresolved or non-balance actor |", text)

    def test_excluded_member_displayed_but_never_fitted(self):
        excluded = excluded_row()
        text = self.render(members=[member("fitted", cost=800)], excluded=[excluded], live={
            "fitted": self.live_row(hp=100000, speed=100, range_wdist=4000, cost=800),
            "huge": self.live_row(hp=900000, speed=100, range_wdist=4000, cost=9000)})
        membership = text.split("## 4. Membership", 1)[1].split("## 5.", 1)[0]
        self.assertIn("| huge |", membership)
        self.assertIn("excluded from fit (buildable=False and no explicit balance_include)", membership)
        self.assertIn("| hp0 | 100000 |", text)
        self.assertNotIn("500000", text)

    def test_anchor_ruled_spec_gap_is_signed_and_percentage_anchor_only(self):
        snapshots = {
            "anchor": dict(actor="anchor", ledger={}, live=dict(hp=100000, speed=56, range_wdist=4000, cost=800),
                           error=None),
            "verifier": dict(actor="verifier", ledger={}, live=dict(hp=200000, speed=56, range_wdist=4000, cost=2000),
                             error=None)}
        text = self.render(members=[member()], snapshots=snapshots,
                           spec=dict(hp0=240000, speed0=56, range0_wdist=4000, cost0=800))
        self.assertIn("| hp | 100000 | 240000 | -140000 | -58.3% |", text)
        section = text.split("Anchor versus ruled spec", 1)[1].split("Live resolved YAML versus", 1)[0]
        rows = [line for line in section.splitlines()
                if line.startswith("| ") and "axis |" not in line and "---" not in line]
        self.assertEqual(len(rows), 4)
        self.assertFalse(any("verifier" in row for row in rows))

    def test_stale_member_ledger_exposed_with_signed_and_percentage_gap(self):
        text = self.render(members=[member("stale")], live={
            "stale": self.live_row(hp=200000, speed=100, range_wdist=4000, cost=800)})
        self.assertIn("| stale / hp | 100000 | 200000 | +100000 | +100.0% |", text)

    def test_member_and_snapshot_share_one_extraction_per_actor(self):
        rec = member()["unit"]
        with patch.object(dossier.extract_stats, "extract_actor", return_value=rec) as extract:
            cache = {}
            live = dossier.member_live("a", {"a": ("vehicles", rec)}, object(), cache)
            snapshot = dossier.actor_snapshot("a", {"a": ("vehicles", rec)}, object(), None, cache)
        self.assertEqual(extract.call_count, 1)
        self.assertEqual(live["values"]["hp"], 100000)
        self.assertEqual(snapshot["live"]["hp"], 100000)


class DossierOutputTests(unittest.TestCase):
    def test_all_writes_only_dossiers_and_idempotently_preserves_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.assertEqual(run_fixture(root, ["--all"]), 0)
            out = root / "docs/balance/anchors"
            self.assertEqual(sorted(p.name for p in out.iterdir()), ["mbt.md", "support.md"])
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            self.assertEqual(run_fixture(root, ["--all"]), 0)
            self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})

    def test_different_dossier_refuses_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            out = root / "docs/balance/anchors"
            out.mkdir(parents=True)
            (out / "support.md").write_text("human judgement", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                run_fixture(root, ["--all"])
            self.assertFalse((out / "mbt.md").exists())
            self.assertEqual((out / "support.md").read_text(), "human judgement")

    def test_repository_output_cannot_target_gameplay_or_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for suffix in ("mods/cameo", "docs/balance", "tools"):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    run_fixture(root, ["--all", "--out", str(root / suffix)])

    def test_single_class_is_stdout_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.assertEqual(run_fixture(root, ["--class", "mbt"]), 0)
            self.assertFalse((root / "docs/balance/anchors").exists())


def run_fixture(root, args, source=None):
    """Run main() against a synthetic ledger; `source` mocks the two provenance reads."""
    ledger = root / "docs/balance"
    ledger.mkdir(parents=True, exist_ok=True)
    (ledger / "class_anchors.json").write_text(json.dumps({"mbt": {}, "support": {}}), encoding="utf-8")
    provenance = dict(ledger_sha256={"class_anchors.json":
        hashlib.sha256((ledger / "class_anchors.json").read_bytes()).hexdigest()})
    with patch.object(dossier, "ROOT", root), \
            patch.object(dossier, "source_provenance", side_effect=source or [{}, {}]), \
            patch.object(virtual, "load_evidence", return_value=([], {}, provenance)), \
            patch.object(virtual, "input_fingerprints", return_value=provenance), \
            patch.object(dossier, "reference_evidence", return_value={}), \
            patch.object(dossier.readiness, "load_units", return_value=[]), \
            patch.object(dossier.readiness, "three_way_split_gate", return_value=(({}, {}), None)), \
            patch.object(dossier.miniyaml, "Ruleset"), \
            contextlib.redirect_stdout(io.StringIO()):
        return dossier.main(args)


if __name__ == "__main__":
    unittest.main()
