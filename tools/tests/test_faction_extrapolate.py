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

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import faction_extrapolate as fe   # noqa: E402
import faction_routes as fr        # noqa: E402


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
