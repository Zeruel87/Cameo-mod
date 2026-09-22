"""`reference_targets.target_for` may not leak an evidence-withheld weapon stat past the
`rd.eligible` gate that `build_distributions` already applies.

REVIEW CONFIRMED BYPASS, 2026-09-09: `target_for` tested only `if not x or x <= 0` on
`r[stat]`, not `rd.eligible`. An INI row whose weapon evidence is withheld by the consumer
policy in `reference_distribution.apply_weapon_evidence` carries `w_dps=None` BUT keeps its
raw `w_range`/`w_damage` (matching clause 5 needs them to tell "armed" from "unarmed") â€” and
those raw fields then voted in the target synthesis against the other rows' aggregates,
without a coordinate gate, without even joining the distributions that gate them. The Cameo
optional self-vote (`with_cameo`) had the same hole in mirror form.ã€‚

Contract pinned here:
  * a withheld row contributes NEITHER a target NOR a source count for `w_range`, `w_damage`
    or `w_dps` â€” target_for on rows+withheld equals target_for on the eligible rows alone;
  * mixed valid+invalid equals valid-only, for the same aggregate value AND source count;
  * a same-source VARIANT FAMILY still casts one vote (the R4 family ruling) â€” added family
    rows never raise the source count;
  * hp/cost eligibility is independent, so the withheld-weapon row still votes on the chassis;
  * an Ineligible Cameo self-vote is omitted â€” `with_cameo` equals `peers_only`;
  * a fully eligible population returns the same peers_only/with_cameo the pool always did.

â›” SYNTHETIC FIXTURES ONLY; no corpus, no assignment file, no shipped report is read.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import reference_distribution as rd  # noqa: E402
import reference_targets as rt      # noqa: E402


def peer(source, rid, hp, *, w_dps=None, w_range=None, w_damage=None, cost=500,
         w_evidence=None, w_dps_raw=None):
    """A peer row in the loader-OUTPUT shape (evidence applied)."""
    row = {"source": source, "raw_source": source, "id": rid, "name": rid,
           "type": "vehicle", "faction": "GDI", "turreted": False,
           "hp": hp, "speed": 7, "turn_speed": 5, "cost": cost}
    for key, val in (("w_dps", w_dps), ("w_range", w_range), ("w_damage", w_damage),
                     ("w_evidence", w_evidence), ("w_dps_raw", w_dps_raw)):
        if val is not None:
            row[key] = val
    return row


def cameo(cid, hp, *, w_dps=None, w_range=None, cost=800, speed=7):
    return {"source": "Cameo", "id": cid, "name": cid, "type": "vehicle",
            "hp": hp, "speed": speed, "turn_speed": 5, "cost": cost,
            "w_dps": w_dps, "w_range": w_range}


VALID_PEERS = [
    # A source that can define its own distributions: >=3 eligible rows per tested stat.
    peer("PeersA", "TA1", 300, w_dps=1.0, w_range=10, w_damage=10),
    peer("PeersA", "TA2", 500, w_dps=3.0, w_range=14, w_damage=30),
    peer("PeersA", "TA3", 450, w_dps=5.0, w_range=18, w_damage=50),
    # A second source â€” its w_dps votes below, and #4 explicitly withholds.
    peer("PeersB", "TB1", 320, w_dps=2.0, w_range=11, w_damage=12),
    peer("PeersB", "TB2", 480, w_dps=4.0, w_range=15, w_damage=32),
    peer("PeersB", "TB3", 460, w_dps=6.0, w_range=19, w_damage=52),
]
# Loader output for one evidence-withheld row: w_dps withheld, raw direct estimate aside,
# w_range/w_damage RAW retained so the armed test still reads it.
WITHHELD_B = peer("PeersB", "TB4", 400, w_dps=None, w_dps_raw=2.5, w_range=99,
                  w_damage=999, w_evidence="incomplete")
ALL_ROWS = VALID_PEERS + [WITHHELD_B]

DIST = rd.build_distributions(ALL_ROWS)
rt.add_cost_distribution(DIST, ALL_ROWS)
CAM = [cameo("c1", 350, w_dps=2.5, w_range=12),
       cameo("c2", 500, w_dps=4.5, w_range=16),
       cameo("c3", 420, w_dps=3.5, w_range=14)]
CDIST = rd.build_distributions(CAM)["Cameo"]
rt.add_cost_distribution(CDIST, CAM)


class WithheldStatLeakTest(unittest.TestCase):
    def _t(self, rows, cameo_row, stat, dist=None, cdist=None):
        return rt.target_for(rows, cameo_row, stat, dist or DIST, cdist or CDIST)

    def test_withheld_range_and_damage_vote_neither_target_nor_source_count(self):
        for stat in ("w_range", "w_damage", "w_dps"):
            clean = self._t([r for r in ALL_ROWS if r["id"] != "TB4"], CAM[0], stat)
            mixed = self._t(ALL_ROWS, CAM[0], stat)
            self.assertEqual(mixed, clean, stat)    # same targets AND same source count

    def test_mixed_valid_invalid_equals_valid_only(self):
        # The gate is ELIGIBILITY, not raw truthiness: a canonical withheld loader row
        # (raw w_range/w_damage present, w_dps=None, w_dps_raw aside) is equivalent to a
        # row with NO weapon fields at all, for every gated stat.
        armed_no_vote = peer("PeersB", "TB9", 400, w_dps=None, w_dps_raw=2.5,
                             w_range=99, w_damage=999, w_evidence="incomplete")
        unarmed = peer("PeersB", "TB9", 400)
        for stat in ("w_range", "w_damage", "w_dps"):
            self.assertEqual(self._t(ALL_ROWS + [armed_no_vote], CAM[0], stat),
                             self._t(ALL_ROWS + [unarmed], CAM[0], stat), stat)
            # and the precondition the bypass relied on is real: raw value present, gate shut
            if stat != "w_dps":
                self.assertTrue(armed_no_vote.get(stat))
            else:
                self.assertEqual(armed_no_vote["w_dps_raw"], 2.5)
            self.assertFalse(rd.eligible(armed_no_vote, stat))

    def test_same_source_family_is_one_vote(self):
        base = [r for r in ALL_ROWS if r["source"] == "PeersA"]
        family = base + [peer("PeersA", "TA1.Ion", 305)]
        t_base = self._t(base, CAM[0], "hp")
        t_family = self._t(family, CAM[0], "hp")
        # the R4 binding property: family rows pool but the source stays ONE vote
        self.assertEqual(t_base[2], 1)
        self.assertEqual(t_family[2], 1)

    def test_hp_and_cost_survive_the_withheld_weapon(self):
        valid = self._t([r for r in ALL_ROWS if r["id"] != "TB4"], CAM[0], "cost")
        mixed = self._t(ALL_ROWS, CAM[0], "cost")
        self.assertEqual(mixed, valid)          # no weapon gate on cost â€” eligibility only
        hp_t = self._t(ALL_ROWS, CAM[0], "hp")
        self.assertIsNotNone(hp_t[0])
        self.assertEqual(hp_t[2], 2)            # the withheld row's source votes on hp

    def test_ineligible_cameo_selfvote_omitted(self):
        bad_cameo = cameo("c1", 350, w_dps=None, w_range=50)   # w_range requires w_dps > 0
        p, w, n = self._t([r for r in ALL_ROWS if r["source"] == "PeersA"],
                          bad_cameo, "w_range")
        self.assertEqual(w, p)
        self.assertIsNone(bad_cameo["w_dps"])
        self.assertNotEqual(w, None)

    def test_fully_eligible_population_unchanged(self):
        rows = [r for r in ALL_ROWS if r["id"] != "TB4"] + \
               [peer("PeersB", "TB4", 400, w_dps=2.5, w_range=11, w_damage=13)]
        d = rd.build_distributions(rows)
        rt.add_cost_distribution(d, rows)
        p, w, n = rt.target_for(rows, CAM[0], "w_dps", d, CDIST)
        self.assertIsNotNone(p)
        self.assertGreater(w, 0)
        self.assertEqual(n, 2)
        # with_cameo is the R4 mean between the peers-only target and Cameo's own value
        self.assertGreaterEqual(w, min(p, CAM[0]["w_dps"]))
        self.assertLessEqual(w, max(p, CAM[0]["w_dps"]))

    def test_multi_armament_cameo_row_withholds_weapon_model_only(self):
        row = dict(CAM[0], weapon_model_eligible=False, w_damage=20, w_burst=2,
                   w_reload=30)
        self.assertFalse(rd.eligible(row, "w_damage"))
        self.assertTrue(rd.eligible(row, "hp"))
        self.assertEqual(self._t(VALID_PEERS, row, "w_damage"), (None, None, 0))

    def test_unknown_burst_cadence_cannot_become_zero_delay(self):
        current = dict(w_damage=200, w_damage_per_shot=100,
                       w_burst=2, w_reload=400, w_dps=.25)
        self.assertIsNone(rt.burst_delay_of(current))
        self.assertIsNone(rt.dps_guard(current, {}, None))
        self.assertIsNone(rt.dps_guard(current, {}, None, burst_delay_target=5))

    def test_reference_burst_delay_is_used_when_available(self):
        current = dict(w_damage=200, w_damage_per_shot=100,
                       w_burst=2, w_reload=90, w_dps=2)
        guarded = rt.dps_guard(current, {}, None, burst_delay_target=5)
        self.assertAlmostEqual(guarded["composed_dps"], 200 / 95)
        self.assertEqual(guarded["burst_delay_per_shot"], 5)

    def test_target_burst_without_delay_stays_withheld(self):
        current = dict(w_damage=100, w_damage_per_shot=100,
                       w_burst=1, w_reload=100, w_dps=1)
        self.assertIsNone(rt.dps_guard(
            current, {"w_damage": 200, "w_burst": 2, "w_reload": 100}, None))

    def test_multi_armament_actors_are_the_only_ones_withheld(self):
        """The weapon model abstains for MIXED armaments, and for nothing else.

        ⛔ THIS REPLACES `test_frozen_weapon_population_is_fixed_and_fail_closed`, which asserted
        that EVERY frozen row is stamped ineligible. Measured on the rebuilt map, that blanket
        stamp took live weapon targets from 266 to 0 and WITHHELD from 38 to 354 while leaving the
        headline counts identical — green-looking and empty. The eligibility flag itself is right
        and is kept; `armament_profile` sets it from `len(live) == 1`, which is exactly the
        maintainer's rule that a cannon and a missile may not be averaged into one number.
        """
        eligible = [r for r in rd.cameo_rows()
                    if r.get("weapon_model_eligible") is not False and r.get("w_damage")]
        withheld = [r for r in rd.cameo_rows() if r.get("weapon_model_eligible") is False]
        # Both populations must be non-empty: all-eligible means the guard is inert, and
        # all-withheld is the failure this test exists to catch.
        self.assertTrue(eligible, "no actor can be projected — the weapon model is blanket-withheld")
        self.assertTrue(withheld, "no actor is withheld — the multi-armament guard is inert")
        for row in withheld:
            self.assertFalse(rd.eligible(row, "w_damage"))
        for row in eligible:
            self.assertTrue(rd.eligible(row, "w_damage"))

    def test_missing_frozen_actor_cannot_receive_weapon_target(self):
        current = dict(CAM[0], id="new", weapon_model_eligible=True,
                       w_damage=20, w_burst=2, w_reload=30)
        frozen = rt.FrozenCameoDistribution(CDIST, [])
        self.assertEqual(self._t(VALID_PEERS, current, "w_burst", cdist=frozen),
                         (None, None, 0))

    def test_live_hero_rows_carry_cycle_and_per_shot_damage(self):
        rows = [row for row in rd.cameo_hero_rows()
                if row.get("w_damage") and float(row.get("w_burst") or 1) > 1]
        self.assertTrue(rows)
        for row in rows:
            self.assertAlmostEqual(
                row["w_damage_per_shot"], row["w_damage"] / float(row["w_burst"]))


if __name__ == "__main__":
    unittest.main()
