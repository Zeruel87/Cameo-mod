"""The routing variants, and the two floors that decide whether a target exists at all.

PRIOR ART: `test_lineage_dedup.py` covers source de-duplication (step 1); nothing covered the
per-unit synthesis or the routing question. `test_class_membership.py` covers template->class,
a different layer.

⛔ MAINTAINER ORDER 2026-09-03: *"let us first do some examples right? Starting with 1 rifle unit
and 1 main battle tank unit."* These two units are the evidence the routing ruling rests on, so
they are pinned here — if either stops behaving the way the ruling was made on, this fails.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import explain_unit as eu  # noqa: E402
import reference_distribution as rd  # noqa: E402


class FamilyRoutingTest(unittest.TestCase):
    def test_every_home_label_is_a_real_source_label_or_known_missing(self):
        """⚠ A label typed differently here routes to nothing, silently — the exact failure
        `reference_lineages.py` exists to stop. The three that legitimately have no rows yet are
        named, so a FOURTH typo cannot hide among them."""
        # MO and CnC Reloaded were wired in 2026-09-03; only DTA still has no roster.
        known_absent = {"DTA"}
        present = {p["source"] for p in rd.peer_rows()}
        for fam, sources in eu.HOME.items():
            for s in sources:
                self.assertTrue(s in present or s in known_absent,
                                f"{fam}: {s!r} is neither a source label nor a known gap")

    def test_faction_prefixes_route_to_the_right_family(self):
        for actor, fam in (("ra2_soviets_apocalypsetank", "ra2"), ("yuri_lashertank", "ra2"),
                           ("td_gdi_mammothtank", "td_ra1"), ("ra1_soviets_heavytank", "td_ra1"),
                           ("ts_gdi_lightinfantry", "ts"), ("cabal_engineer", "ts"),
                           ("forgotten_flametank", "ts")):
            self.assertEqual(eu.family_of(actor), fam, actor)

    def test_an_unrecognised_prefix_returns_None_rather_than_guessing(self):
        self.assertIsNone(eu.family_of("terran_marine"))
        self.assertIsNone(eu.family_of("zerg_hydralisk"))


class TheTwoFloorsTest(unittest.TestCase):
    """A target exists only when >=2 REFERENCE sources voted. Both floors were maintainer rulings
    and both are silent failures if they regress: too few sources produces a confident number
    from one opinion."""

    def setUp(self):
        self.peers, self.cameo = rd.peer_rows(), rd.cameo_rows()
        self.mapped = {s for s in {p["source"] for p in self.peers}
                       if sum(1 for p in self.peers if p["source"] == s
                              and any(p.get(f"dps_vs_{l}") for l in rd.LADDERS)) >= 8}
        self.pdist = eu.build(self.peers, self.mapped)
        self.cdist = eu.build(self.cameo, self.mapped)["Cameo"]

    def _row(self, actor):
        return next(c for c in self.cameo if c["id"] == actor)

    def test_one_source_yields_no_target_at_all(self):
        """Not a low-confidence target — NO target. A single reference row is one mod's opinion."""
        row = self._row("ra2_soviets_conscript")
        one = [p for p in self.peers if p["source"] == "Romanov's Vengeance"
               and rd.syn.norm(p["name"]) == "conscript"]
        self.assertTrue(one, "fixture gone: RV no longer lists a Conscript")
        t, used = eu.synthesize(one, row, "hp", self.pdist, self.cdist, cameo_votes=False)
        self.assertIsNone(t)
        self.assertEqual(len(used), 1)

    def test_cameo_never_exceeds_one_third_of_the_votes(self):
        """With N reference sources Cameo is pooled as 1 of N+1, so at the >=2 floor it is 33%
        and it only ever falls from there."""
        row = self._row("ra2_soviets_apocalypsetank")
        matches = [p for p in self.peers
                   if rd.syn.norm(p["name"]).startswith("apocalypsetank")]
        t_peers, used = eu.synthesize(matches, row, "hp", self.pdist, self.cdist, False)
        t_voted, _ = eu.synthesize(matches, row, "hp", self.pdist, self.cdist, True)
        self.assertGreaterEqual(len(used), 2)
        # the voted target is the peer target pooled with Cameo's own at weight 1/(n+1)
        expect = rd.gm([t_peers] * len(used) + [row["hp"]])
        self.assertAlmostEqual(t_voted, expect, delta=1.0)


class TheWeaponPopulationTest(unittest.TestCase):
    """Only weapons actually fired by regular buildable units and defences (maintainer 2026-09-03)."""

    def test_a_superweapon_structure_is_not_a_weapon(self):
        """SP's Iron Savior carries range 614400 and ZERO damage, and it was defining Shattered
        Paradise's range ceiling — 100x its own median."""
        self.assertFalse(eu.real_weapon(
            {"type": "building", "w_dps": 0, "w_damage": 0, "source": "Shattered Paradise"}, set()))

    def test_a_defence_IS_a_weapon(self):
        """'units and defenses' — a defence turret is a real combat weapon and must stay in."""
        row = {"type": "defense", "w_dps": 100, "w_damage": 5000,
               "source": "X", "dps_vs_INF": 100.0}
        self.assertTrue(eu.real_weapon(row, {"X"}))

    def test_an_instakill_with_no_armour_profile_is_excluded(self):
        """Attack Dog / Terror Dog: 100000 damage, no Versus at all, in three separate mods."""
        row = {"type": "infantry", "w_dps": 10000, "w_damage": 100000, "source": "X"}
        self.assertFalse(eu.real_weapon(row, {"X"}))

    def test_the_armour_condition_is_skipped_for_unmapped_sources(self):
        """⛔ THE GUARD THAT MATTERS. Without it the condition conflates 'does no damage' with
        'we could not map this mod's armour vocabulary' and deletes whole sources — Generals Alpha
        declares 37 armour types and maps none."""
        row = {"type": "vehicle", "w_dps": 256, "w_damage": 64000, "source": "Generals Alpha"}
        self.assertFalse(eu.real_weapon(row, {"Generals Alpha"}))   # mapped -> excluded
        self.assertTrue(eu.real_weapon(row, set()))                 # unmapped -> kept


if __name__ == "__main__":
    unittest.main()
