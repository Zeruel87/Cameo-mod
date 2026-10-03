"""The rosters do not line up 1:1 — and three ways the extrapolation quietly lies about it.

PRIOR ART: `test_faction_routes.py` covers WHICH reference units a Cameo unit may see;
`test_assign_references.py` covers the 1:1 matching law. Neither covers what happens to the units
that get no pair, which is 122 of the 447 routed Cameo units and is the maintainer's question of
2026-09-04: *"only a small portion of the units could be mapped but that's still okay because we
can use... the unused extra reference units from their factions to somehow extrapolate."*

⛔ EACH TEST BELOW IS A BUG THAT WAS REAL DURING THE BUILD, not a hypothetical:
  1. with no reference roster the rank placement returns the unit's own value — an identity
     dressed as evidence (`ordos` reported 20 such placements);
  2. nearest-point placement collapses a small roster (OpenE2140 `ed`'s four infantry rows put
     SIX Naxis infantry on one HP);
  3. a reference population with no spread flattens a varied Cameo roster and still looks like a
     measurement (the same four rows: HP 28/28/28/20, speed 50/50/50/50).
"""

from __future__ import annotations

import math
import pathlib
import sys
import unittest
from unittest.mock import patch
import contextlib
import io

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import faction_extrapolate as fe   # noqa: E402
import faction_routes as fr        # noqa: E402


class PairedIdentityTests(unittest.TestCase):
    def setUp(self):
        self.first = dict(source="S", id="amcv", name="MCV", hp=1000, cost=500)
        self.second = dict(self.first, id="smcv")
        self.assignment = {"td_gdi_mcv": {"S": dict(id="smcv", name="MCV", hp=1000, cost=500)}}

    def test_exact_id_beats_identical_name_stats_and_retains_object_identity(self):
        notes = {}
        result = fe.paired_rows(self.assignment, [self.first, self.second], notes)
        self.assertIs(result["td_gdi_mcv"]["S"], self.second)
        self.assertEqual(len(notes["joined"]), 1)

    def test_absent_id_does_not_fall_back_to_same_name(self):
        notes = {}
        with patch.object(fe.rd, "peer_hero_rows", return_value=[]):
            result = fe.paired_rows(self.assignment, [self.first], notes)
        self.assertEqual(result, {})
        self.assertEqual(notes["unresolved_in_available_pools"][0]["ordinary_rows"], 0)

    def test_duplicate_source_id_refuses(self):
        notes = {}
        self.assertEqual(fe.paired_rows(self.assignment, [self.second, dict(self.second)], notes), {})
        self.assertEqual(notes["ambiguous_id"][0]["ordinary_rows"], 2)

    def test_no_id_is_not_joined_even_to_an_idless_peer(self):
        for rid in (None, "", " "):
            with self.subTest(rid=rid):
                notes = {}
                result = fe.paired_rows({"actor": {"S": dict(id=rid, name="MCV")}},
                                       [dict(self.first, id=rid)], notes)
                self.assertEqual(result, {})
                self.assertEqual(len(notes["missing_id"]), 1)

    def test_hero_evidence_remains_outside_ordinary_population(self):
        notes = {}
        with patch.object(fe.rd, "peer_hero_rows", return_value=[self.second]):
            result = fe.paired_rows(self.assignment, [self.first], notes)
        self.assertEqual(result, {})
        self.assertEqual(notes["hero_only"][0]["hero_rows"], 1)
        self.assertNotIn("unresolved_in_available_pools", notes)

    def test_source_is_part_of_identity_and_missing_join_is_reported(self):
        output = io.StringIO()
        with patch.object(fe.rd, "peer_hero_rows", return_value=[]), contextlib.redirect_stderr(output):
            result = fe.paired_rows(self.assignment, [dict(self.second, source="Other")])
        self.assertEqual(result, {})
        self.assertIn("td_gdi_mcv / S / smcv", output.getvalue())

    def test_actual_assigned_ids_are_not_replaced_by_same_name_variants(self):
        # Committed regression cohort; no matcher rerun or mapping changes.
        import json
        assignment = json.loads((ROOT / "docs/balance/derived/reference_assignment.json").read_text(encoding="utf-8"))["assignment"]
        actors = ("td_gdi_apc", "td_gdi_mammothtank", "ra1_soviets_samsite", "ra2_soviets_mobileconstructionvehicle")
        cohort = {actor: assignment[actor] for actor in actors}
        peers = fe.rd.peer_rows()
        result = fe.paired_rows(cohort, peers, {})
        for actor, refs in cohort.items():
            for source, ref in refs.items():
                with self.subTest(actor=actor, source=source):
                    self.assertEqual(result[actor][source]["id"], ref["id"])
                    self.assertTrue(any(result[actor][source] is row for row in peers))


class TestQuantile(unittest.TestCase):
    def test_interpolates_in_log_space(self):
        # 1,000 and 100,000 at the midpoint is 10,000, not 50,500. Every aggregate in this
        # pipeline is geometric; a linear midpoint would import an arithmetic assumption.
        self.assertAlmostEqual(fe.quantile([1000.0, 100000.0], 0.5), 10000.0, places=6)

    def test_ends_are_exact(self):
        vals = [2.0, 4.0, 8.0, 16.0]
        self.assertEqual(fe.quantile(vals, 0.0), 2.0)
        self.assertEqual(fe.quantile(vals, 1.0), 16.0)

    def test_is_monotonic(self):
        vals = [10.0, 30.0, 31.0, 900.0]
        seen = [fe.quantile(vals, q / 20) for q in range(21)]
        self.assertEqual(seen, sorted(seen))

    def test_does_not_collapse_distinct_percentiles(self):
        # The bug: nearest-point snapping mapped 0.25, 0.50, 0.83 and 1.00 onto one value.
        vals = [10.0, 20.0, 40.0, 80.0]
        got = {fe.quantile(vals, q) for q in (0.25, 0.5, 0.83, 1.0)}
        self.assertEqual(len(got), 4)

    def test_single_point(self):
        self.assertEqual(fe.quantile([7.0], 0.4), 7.0)

    def test_non_positive_values_fall_back_to_linear(self):
        self.assertAlmostEqual(fe.quantile([0.0, 10.0], 0.5), 5.0)


class TestPlaceUnpaired(unittest.TestCase):
    @staticmethod
    def _members(hps):
        return [{"id": f"u{i}", "type": "vehicle", "hp": hp} for i, hp in enumerate(hps)]

    def test_a_reference_with_no_spread_places_nothing(self):
        # OpenE2140 `ed` infantry, exactly: four rows, three distinct... no, ONE distinct HP and
        # one distinct speed. A point cannot rank anybody, and averaging it away would delete a
        # varied Cameo roster while looking like a measurement.
        pool = {("vehicle", "hp"): [28.0, 28.0, 28.0]}
        out = fe.place_unpaired("x", self._members([8000, 20000, 96000]), pool, set())
        self.assertEqual(out, {})

    def test_an_empty_reference_places_nothing(self):
        # The identity bug: with no reference the pool is the unit's own roster, so `placed`
        # equals `now` and the row counts as coverage while carrying nothing.
        out = fe.place_unpaired("x", self._members([100, 200, 300]), {}, set())
        self.assertEqual(out, {})

    def test_a_thin_cameo_side_places_nothing(self):
        pool = {("vehicle", "hp"): [10.0, 20.0, 40.0, 80.0]}
        out = fe.place_unpaired("x", self._members([100, 200]), pool, set())
        self.assertEqual(out, {})

    def test_places_by_rank_onto_the_reference_spread(self):
        # Cameo's roster decides the ORDER; the reference decides the SPREAD.
        members = self._members([100, 200, 400, 800])
        pool = {("vehicle", "hp"): [10.0, 20.0, 40.0, 80.0]}
        out = fe.place_unpaired("x", members, pool, set())
        self.assertEqual(sorted(out), ["u0", "u1", "u2", "u3"])
        placed = [out[f"u{i}"]["hp"]["placed"] for i in range(4)]
        self.assertEqual(placed, sorted(placed))
        self.assertAlmostEqual(placed[0], 10.0)
        self.assertAlmostEqual(placed[-1], 80.0)

    def test_paired_units_are_skipped(self):
        members = self._members([100, 200, 400, 800])
        pool = {("vehicle", "hp"): [10.0, 20.0, 40.0, 80.0]}
        out = fe.place_unpaired("x", members, pool, {"u1", "u2"})
        self.assertEqual(sorted(out), ["u0", "u3"])
        # ⚠ and the SKIPPED units still count in `own` — they are part of the Cameo roster whose
        # ordering the placement reads. Dropping them would change everyone else's percentile.
        self.assertEqual(out["u0"]["hp"]["own_n"], 4)


class TestNum(unittest.TestCase):
    def test_unwraps_the_ledger_value_dict(self):
        self.assertEqual(fe._num({"cost": {"v": 500}}, "cost"), 500.0)

    def test_rejects_zero_and_missing(self):
        self.assertIsNone(fe._num({"hp": 0}, "hp"))
        self.assertIsNone(fe._num({}, "hp"))
        self.assertIsNone(fe._num({"hp": None}, "hp"))
        self.assertIsNone(fe._num({"hp": "abc"}, "hp"))

    def test_rejects_bools(self):
        self.assertIsNone(fe._num({"hp": True}, "hp"))
        self.assertIsNone(fe._num({"hp": False}, "hp"))
        self.assertIsNone(fe._num({"hp": {"v": True}}, "hp"))

    def test_rejects_non_finite(self):
        for v in (float("inf"), float("-inf"), float("nan"), "inf", "-inf", "nan", "1e400"):
            with self.subTest(v=v):
                self.assertIsNone(fe._num({"hp": v}, "hp"))

    def test_rejects_unrepresentable_overflow(self):
        self.assertIsNone(fe._num({"hp": 10 ** 400}, "hp"))
        self.assertIsNone(fe._num({"hp": {"v": 10 ** 400}}, "hp"))

    def test_admits_finite_positive_values_unchanged(self):
        for v, want in ((500, 500.0), ("500", 500.0), ({"v": 500}, 500.0), (1e-300, 1e-300)):
            with self.subTest(v=v):
                self.assertEqual(fe._num({"hp": v}, "hp"), want)


class TestExchangeRates(unittest.TestCase):
    def test_the_rate_is_the_geometric_mean_of_the_pair_ratios(self):
        pairs = {f"cabal_u{i}": {"S": {"hp": v}} for i, v in enumerate((10.0, 20.0, 40.0))}
        cameo = {f"cabal_u{i}": {"hp": 100.0} for i in range(3)}
        rates = fe.exchange_rates(pairs, cameo, min_pairs=3)
        self.assertAlmostEqual(rates[("cabal", "S")]["hp"]["k"],
                               math.exp((math.log(10) + math.log(5) + math.log(2.5)) / 3))
        self.assertEqual(rates[("cabal", "S")]["hp"]["n"], 3)

    def test_below_the_floor_no_rate_is_emitted(self):
        pairs = {"cabal_u0": {"S": {"hp": 10.0}}}
        cameo = {"cabal_u0": {"hp": 100.0}}
        self.assertEqual(fe.exchange_rates(pairs, cameo, min_pairs=3), {})

    def test_spread_is_1_when_every_pair_agrees(self):
        pairs = {f"cabal_u{i}": {"S": {"hp": 10.0}} for i in range(3)}
        cameo = {f"cabal_u{i}": {"hp": 100.0} for i in range(3)}
        rates = fe.exchange_rates(pairs, cameo, min_pairs=3)
        self.assertAlmostEqual(rates[("cabal", "S")]["hp"]["spread"], 1.0, places=9)


class ThinExchangeRateTests(unittest.TestCase):
    """The Phase B gate: a rate below the pair floor is marked THIN and withheld."""

    @staticmethod
    def _pairs(n):
        return {f"cabal_u{i}": {"S": {"hp": 10.0}} for i in range(n)}

    @staticmethod
    def _cameo(n):
        return {f"cabal_u{i}": {"hp": 100.0} for i in range(n)}

    def test_two_pairs_are_thin_and_excluded_from_rates(self):
        diag = {}
        rates = fe.exchange_rates(self._pairs(2), self._cameo(2), 3, diag)
        self.assertEqual(rates, {})
        self.assertEqual(diag[("cabal", "S", "hp")],
                         {"n": 2, "invalid": 0, "required": 3, "status": "THIN"})

    def test_three_pairs_are_usable(self):
        diag = {}
        rates = fe.exchange_rates(self._pairs(3), self._cameo(3), 3, diag)
        self.assertEqual(diag[("cabal", "S", "hp")]["status"], "usable")
        self.assertEqual(rates[("cabal", "S")]["hp"]["n"], 3)

    def test_an_explicit_lower_positive_threshold_stays_testable(self):
        diag = {}
        rates = fe.exchange_rates(self._pairs(2), self._cameo(2), 2, diag)
        self.assertEqual(rates[("cabal", "S")]["hp"]["n"], 2)
        self.assertEqual(diag[("cabal", "S", "hp")]["status"], "usable")

    def test_zero_and_negative_thresholds_are_refused(self):
        for bad in (0, -1):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                fe.exchange_rates(self._pairs(2), self._cameo(2), bad, {})

    def test_counts_use_only_valid_per_stat_values(self):
        pairs = self._pairs(4)
        del pairs["cabal_u3"]["S"]["hp"]        # the peer side has no hp on this pair
        pairs["cabal_u3"]["S"]["cost"] = 5.0    # ...and the cameo side has no cost at all
        diag = {}
        rates = fe.exchange_rates(pairs, self._cameo(4), 3, diag)
        self.assertEqual(set(diag), {("cabal", "S", "hp"), ("cabal", "S", "cost")})
        self.assertEqual(diag[("cabal", "S", "hp")],
                         {"n": 3, "invalid": 1, "required": 3, "status": "usable"})
        self.assertEqual(diag[("cabal", "S", "cost")],
                         {"n": 0, "invalid": 1, "required": 3, "status": "THIN"})
        self.assertEqual(rates[("cabal", "S")]["hp"]["n"], 3)
        self.assertNotIn("cost", rates[("cabal", "S")])

    def test_overflow_and_underflow_ratios_are_counted_not_propagated(self):
        pairs = self._pairs(3)
        pairs["cabal_u0"]["S"]["hp"] = 1e-308   # 100 / 1e-308 overflows to inf
        cameo = self._cameo(3)
        cameo["cabal_u1"]["hp"] = 1e-300        # 1e-300 / 1e308 underflows to 0.0
        pairs["cabal_u1"]["S"]["hp"] = 1e308
        diag = {}
        rates = fe.exchange_rates(pairs, cameo, 3, diag)
        self.assertEqual(diag[("cabal", "S", "hp")],
                         {"n": 1, "invalid": 2, "required": 3, "status": "THIN"})
        self.assertEqual(rates, {})

    def test_a_usable_rate_never_carries_infinite_evidence(self):
        pairs = self._pairs(3)
        pairs["cabal_u2"]["S"]["hp"] = 1e-308   # inf ratio: dropped, not summed into k
        diag = {}
        rates = fe.exchange_rates(pairs, self._cameo(3), 2, diag)
        self.assertEqual(diag[("cabal", "S", "hp")]["invalid"], 1)
        self.assertEqual(diag[("cabal", "S", "hp")]["n"], 2)
        k = rates[("cabal", "S")]["hp"]["k"]
        self.assertTrue(math.isfinite(k) and k > 0)

    def test_thin_rates_never_reach_virtual_or_converted_populations(self):
        peer_a = {"source": "Shattered Paradise", "id": "sp_a", "faction": "cab",
                  "type": "vehicle", "hp": 10.0}
        peer_b = {"source": "Shattered Paradise", "id": "sp_b", "faction": "cab",
                  "type": "vehicle", "hp": 20.0}
        peers = [peer_a, peer_b]
        pairs = {"cabal_u0": {"Shattered Paradise": peer_a},
                 "cabal_u1": {"Shattered Paradise": peer_a}}
        cameo = {"cabal_u0": {"hp": 100.0}, "cabal_u1": {"hp": 100.0}}
        diag = {}
        rates = fe.exchange_rates(pairs, cameo, 3, diag)
        self.assertEqual(rates, {})
        self.assertEqual(dict(fe.virtual_members(rates, pairs, peers)), {})
        self.assertEqual(fe.converted_pool("cabal", rates, peers), {})
        # control: the same evidence at a floor of 2 is usable and converts
        rates = fe.exchange_rates(pairs, cameo, 2, diag)
        self.assertEqual(diag[("cabal", "Shattered Paradise", "hp")]["status"], "usable")
        virt = fe.virtual_members(rates, pairs, peers)
        self.assertEqual(len(virt["cabal"]), 1)
        self.assertAlmostEqual(virt["cabal"][0]["hp"], 200.0, places=6)   # 20 * k(=10)
        self.assertTrue(virt["cabal"][0]["virtual"])
        pool = fe.converted_pool("cabal", rates, peers)
        self.assertEqual([round(v, 6) for v in sorted(pool[("vehicle", "hp")])],
                         [100.0, 200.0])


class CliContractTests(unittest.TestCase):
    """The CLI refuses an invalid floor before the corpus is loaded, and shows what it withheld."""

    @staticmethod
    def _fake_build(diag, rates=None):
        def build(min_pairs, join_diagnostics=None, rate_diagnostics=None):
            rate_diagnostics.update(diag)
            return [], [], {}, (rates or {}), {}, {}
        return build

    def test_min_pairs_below_the_floor_is_refused_before_any_build(self):
        with patch.object(fe, "build", side_effect=SystemExit(99)) as mock_build, \
             patch.object(sys, "argv",
                          ["faction_extrapolate.py", "--rates", "--min-pairs", "2"]):
            with self.assertRaises(SystemExit) as cm:
                fe.main()
        self.assertEqual(cm.exception.code, 2)
        mock_build.assert_not_called()

    def test_zero_and_negative_min_pairs_are_refused(self):
        for bad in ("0", "-1"):
            with self.subTest(bad=bad):
                with patch.object(fe, "build", side_effect=SystemExit(99)), \
                     patch.object(sys, "argv", ["faction_extrapolate.py", "--min-pairs", bad]):
                    with self.assertRaises(SystemExit) as cm:
                        fe.main()
                self.assertEqual(cm.exception.code, 2)

    def test_rates_shows_thin_rows(self):
        diag = {("cabal", "Shattered Paradise", "hp"):
                {"n": 2, "invalid": 0, "required": 3, "status": "THIN"}}
        out = io.StringIO()
        with patch.object(fe, "build", side_effect=self._fake_build(diag)), \
             patch.object(sys, "argv", ["faction_extrapolate.py", "--rates"]):
            with contextlib.redirect_stdout(out):
                fe.main()
        self.assertIn("THIN", out.getvalue())
        self.assertIn("Shattered Paradise", out.getvalue())
        self.assertIn("n=2", out.getvalue())

    def test_faction_shows_only_its_own_thin_rows(self):
        diag = {("cabal", "Shattered Paradise", "hp"):
                {"n": 2, "invalid": 0, "required": 3, "status": "THIN"},
                ("yuri", "Combined Arms", "hp"):
                {"n": 2, "invalid": 0, "required": 3, "status": "THIN"}}
        out = io.StringIO()
        with patch.object(fe, "build", side_effect=self._fake_build(diag)), \
             patch.object(sys, "argv", ["faction_extrapolate.py", "--faction", "cabal"]):
            with contextlib.redirect_stdout(out):
                self.assertEqual(fe.main(), 0)
        self.assertIn("cabal", out.getvalue())
        self.assertNotIn("yuri", out.getvalue())

    def test_report_carries_a_thin_summary(self):
        diag = {("cabal", "Shattered Paradise", "hp"):
                {"n": 2, "invalid": 0, "required": 3, "status": "THIN"}}
        out = io.StringIO()
        with patch.object(fe, "build", side_effect=self._fake_build(diag)), \
             patch.object(sys, "argv", ["faction_extrapolate.py", "--report"]):
            with contextlib.redirect_stdout(out):
                fe.main()
        self.assertIn("THIN:", out.getvalue())

    def test_by_class_carries_a_thin_summary(self):
        diag = {("cabal", "Shattered Paradise", "hp"):
                {"n": 2, "invalid": 0, "required": 3, "status": "THIN"}}
        out = io.StringIO()
        with patch.object(fe, "build", side_effect=self._fake_build(diag)), \
             patch.object(fe.ar, "ledger", return_value={}), \
             patch.object(sys, "argv", ["faction_extrapolate.py", "--by-class"]):
            with contextlib.redirect_stdout(out):
                fe.main()
        self.assertIn("THIN:", out.getvalue())


class BuildContractTests(unittest.TestCase):
    def test_build_returns_six_items_and_plumbs_rate_diagnostics(self):
        peers = [{"source": "Shattered Paradise", "id": "sp_a", "faction": "cab",
                  "type": "vehicle", "hp": 10.0}]
        cameo = [{"id": "cabal_u0", "type": "vehicle", "hp": 100.0}]
        assignment = {"cabal_u0": {"Shattered Paradise": {"id": "sp_a", "hp": 10.0}}}
        diag = {}
        with patch.object(fe.rd, "peer_rows", return_value=peers), \
             patch.object(fe.rd, "cameo_rows", return_value=cameo), \
             patch.object(fe.ar, "assign", return_value=(assignment, [], [])), \
             patch.object(fe.ar, "ledger", return_value={}):
            got = fe.build(3, rate_diagnostics=diag)
        self.assertEqual(len(got), 6)
        self.assertEqual(got[3], {})
        self.assertEqual(diag[("cabal", "Shattered Paradise", "hp")],
                         {"n": 1, "invalid": 0, "required": 3, "status": "THIN"})


class TestAgainstTheTree(unittest.TestCase):
    """One end-to-end run, asserting the properties that make the output usable."""

    @classmethod
    def setUpClass(cls):
        (cls.peers, cls.cameo, cls.pairs,
         cls.rates, cls.virt, cls.placements) = fe.build()

    def test_placements_are_never_the_identity(self):
        same = [(cid, stat) for cid, d in self.placements.items() for stat, e in d.items()
                if e["now"] == e["placed"]]
        self.assertEqual(same, [], "a placement returned the unit's own value")

    def test_every_placed_unit_is_unpaired_and_routed(self):
        for cid in self.placements:
            self.assertNotIn(cid, self.pairs, f"{cid} was placed AND paired")
            fac = fr.faction_of(cid)
            self.assertTrue(fac and fr.routes_for(fac), f"{cid} was placed with no route")

    def test_virtual_members_are_combat_types_only(self):
        # Unfiltered, the leftovers are mostly the reference mod's economy: 36 of Shattered
        # Paradise's 48 unused `gdi` rows are buildings, and a construction yard is not evidence
        # about a tank.
        for fac, rows in self.virt.items():
            for row in rows:
                self.assertIn(row["type"], {"infantry", "vehicle", "aircraft", "ship", "defense"},
                              f"{fac}: {row['name']} is a {row['type']}")

    def test_every_rate_names_a_routed_source(self):
        for (fac, src) in self.rates:
            self.assertIn(src, fr.routed_sources(fac))


if __name__ == "__main__":
    unittest.main()
