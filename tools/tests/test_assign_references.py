"""The matching law's mechanics — the clauses that fail silently if they regress.

PRIOR ART: `test_explain_unit.py` covers the routing variants and the vote floors on ONE unit;
`test_lineage_dedup.py` covers source de-duplication. Neither touches the assignment.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import unittest
import tempfile
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import assign_references as ar  # noqa: E402


class ReviewMissingScoreTest(unittest.TestCase):
    def test_override_without_computed_scores_remains_visible(self):
        record = {'confidence': 'STRONG', 'home': False, 'name': 'Explicit counterpart',
                  'raw_name': None, 'score': None}
        with tempfile.TemporaryDirectory() as folder, patch.object(ar, 'ROOT', pathlib.Path(folder)), \
                patch.object(ar, 'assign', return_value=({'unit': {'source': record},
                    'outside_class_override': {'source': record}}, [], 1)) as assigned, \
                patch.object(ar, 'ledger', return_value={'unit': {'design': {}, 'cost': 100}}), \
                patch.object(ar.rd, 'cameo_rows', return_value=[]), \
                patch.object(ar.cm, 'classify', return_value=('scout', 'fixture')):
            assigned.formula_only = {}
            self.assertEqual(ar.write_review('scout'), 0)
            report = (pathlib.Path(folder) / 'docs/balance/review/scout_references.md').read_text(encoding='utf-8')
            self.assertIn('Explicit counterpart | — | — | — |', report)
            self.assertIn('STRONG', report)
            self.assertIn('| assigned at least one reference | **1** |', report)
            self.assertIn('| members with NO reference at all | **0** |', report)
            self.assertNotIn('outside_class_override', report)


class TheCascadeIsACascadeTest(unittest.TestCase):
    """⛔ THE BUG THIS CLASS EXISTS FOR. A lexicographic tuple whose first key is a near-continuous
    float degenerates into "rank by that key alone" — exact ties never occur, so tier, role and
    cost are computed and then thrown away. Measured before the fix: 38% of assignments had a role
    score under 0.5 while the role step ran on every one of them."""

    def test_the_name_score_is_bucketed_not_continuous(self):
        seen = set()
        for peer_name in ("mammoth", "mammothtank", "mammoth tank mk ii", "grizzly", "zzzz"):
            cam = {"id": "td_gdi_mammothtank", "type": "vehicle"}
            s = ar.score(cam, {}, {"type": "vehicle", "name": peer_name}, None, None, False)
            if s:
                seen.add(s[0])
        self.assertTrue(seen <= {0, 1, 2, 3, 4}, f"name key is not bucketed: {seen}")

    def test_role_breaks_a_tie_inside_a_name_bucket(self):
        cam = {"id": "x_y_scout", "type": "infantry"}
        peer = {"type": "infantry", "name": "zzzzz"}
        good = ar.score(cam, {}, peer, None, None, False, [0.9, 0.9], [0.9, 0.9])
        poor = ar.score(cam, {}, peer, None, None, False, [0.9, 0.9], [0.1, 0.1])
        self.assertEqual(good[0], poor[0], "fixture broke: the two must share a name bucket")
        self.assertGreater(good, poor, "role does not break the tie — the cascade is dead below name")


class TheHardRefusalsTest(unittest.TestCase):
    def test_cross_type_is_refused(self):
        """The TYPE half of the ten relative values is meaningless if the types differ."""
        self.assertIsNone(ar.score({"id": "a_b_c", "type": "infantry"}, {},
                                   {"type": "vehicle", "name": "c"}, None, None, False))

    def test_a_zero_damage_row_never_matches_an_ARMED_unit(self):
        """Clause 5. MO lists an 'Apocalypse' at 620 HP with zero damage — a different device."""
        armed = {"armaments": [{"pricing": True}]}
        self.assertIsNone(ar.score({"id": "a_b_apocalypsetank", "type": "vehicle"}, armed,
                                   {"type": "vehicle", "name": "Apocalypse", "w_damage": 0},
                                   None, None, False))
        self.assertIsNotNone(ar.score({"id": "a_b_apocalypsetank", "type": "vehicle"}, armed,
                                      {"type": "vehicle", "name": "Apocalypse", "w_damage": 130},
                                      None, None, False))


class TheExemptionsTest(unittest.TestCase):
    def test_role_identical_units_are_exempt(self):
        for actor in ("ra2_allies_engineer", "yuri_mobileconstructionvehicle",
                      "asianalliance_droneminer"):
            self.assertIsNotNone(ar.exempt(actor, {}), actor)

    def test_an_ARMED_carrier_is_NOT_exempt(self):
        """⚠ The maintainer's carve-out: the test is the gun, not the name."""
        armed = {"armaments": [{"pricing": True}]}
        self.assertIsNone(ar.exempt("cabal_scarabapctransport", armed))
        self.assertIsNotNone(ar.exempt("x_y_transport", {}))

    def test_shape_similarity_needs_two_axes_to_mean_anything(self):
        self.assertIsNone(ar.shape_similarity([0.5, None], [0.5, None]))
        self.assertAlmostEqual(ar.shape_similarity([0.5, 0.5], [0.5, 0.5]), 1.0)
        self.assertAlmostEqual(ar.shape_similarity([1.0, 1.0], [0.0, 0.0]), 0.0)


class VariantRankDeterminismTest(unittest.TestCase):
    """⛔ THE BUG THIS CLASS EXISTS FOR (found 2026-09-09, regenerating for the Katyusha
    override). `variant_rank` removed faction words by iterating FACTION_WORDS, a frozenset,
    whose order Python randomizes per process — and the words OVERLAP ("japan" is a prefix of
    "japanese"; soviet/soviets, german/germany, america/american, russia/russian alike). Removing
    the shorter word first ate the longer's tail ("japanese" -> "ese", "germany" -> "y"), so the
    same (actor, peer) pair scored variant 1 in one process and 0 in the next, and the committed
    reference_assignment.json disagreed with a fresh run on `japan_japaneseflamethrower |
    RA2 Reborn "Flamethrower"`. The fix replaces in a stable longest-first, lexical order.
    """

    # (tail, peer, expected) — the residue after removing `peer` is exactly the LONGER faction
    # word of each overlapping pair, which shortest-first used to mangle into a leftover.
    OVERLAPPING = (
        ("japaneseflamethrower", "Flamethrower", 1),   # japan/japanese — the caught row
        ("germanytank", "Tank", 1),                    # german/germany
        ("americadozer", "Dozer", 1),                  # america/american
        ("russianspeaker", "Speaker", 1),              # russia/russian
        ("sovietsdog", "Dog", 1),                      # soviet/soviets
    )

    def test_overlapping_faction_words_remove_longest_first(self):
        for tail, peer, expected in self.OVERLAPPING:
            with self.subTest(tail=tail, peer=peer):
                self.assertEqual(ar.variant_rank(f"x_y_{tail}", peer), expected)

    def test_the_in_process_answers_did_not_move(self):
        """The fix must not re-rule the cases the docstring already records."""
        self.assertEqual(ar.variant_rank("a_b_sovietrocketsoldier", "Rocket Soldier"), 1)
        self.assertEqual(ar.variant_rank("a_b_firerocketsoldier", "Rocket Soldier"), 0)
        self.assertEqual(ar.variant_rank("a_b_scout", "Mammoth"), 1)   # peer not in tail

    def test_stable_across_bounded_process_hash_seeds(self):
        """The multi-process half: the original flip ONLY manifested across processes. Three
        fixed seeds, one tiny snippet each — bounded on purpose, no corpus load in the child."""
        balance_dir = str(ROOT / "tools" / "balance")
        snippet = (
            "import sys\n"
            f"sys.path.insert(0, r'{balance_dir}')\n"
            "import assign_references as ar\n"
            "print(ar.variant_rank('japan_japaneseflamethrower', 'Flamethrower'))\n"
        )
        env = dict(os.environ)
        outs = set()
        for seed in ("0", "1", "2"):
            env["PYTHONHASHSEED"] = seed
            proc = subprocess.run([sys.executable, "-c", snippet], capture_output=True,
                                  text=True, timeout=120, env=env, check=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            outs.add(proc.stdout.strip())
        self.assertEqual(len(outs), 1, f"variant_rank flips across hash seeds: {sorted(outs)}")


class TheSpawnOnlyIdiomTest(unittest.TestCase):
    """⛔ `~self` and `~!self` sit side by side in this tree and mean opposite things. Stripping
    the `!` before comparing — which the check did — collapses 562 legitimate one-offs and 3
    spawn-only actors into one bucket."""

    def setUp(self):
        sys.path.insert(0, str(ROOT / "tools" / "audit"))
        import extract_stats  # noqa: E402
        self.fn = extract_stats._is_balance_buildable

    def test_self_as_its_own_prerequisite_is_never_buildable(self):
        b = {"Queue": "Infantry", "Prerequisites": "~forgotten_mutant_wild"}
        self.assertFalse(self.fn(b, "forgotten_mutant_wild"))

    def test_NOT_self_is_a_build_limit_and_stays_buildable(self):
        """`~!tkm_bigshiee` means 'not already built' — a one-off, not a spawn-only unit."""
        b = {"Queue": "Vehicle",
             "Prerequisites": "~tkm_warfactory, tkm_techcenter, ~!tkm_bigshiee"}
        self.assertTrue(self.fn(b, "tkm_bigshiee"))

    def test_an_ordinary_unit_is_unaffected(self):
        b = {"Queue": "Vehicle", "Prerequisites": "~ra2_soviets_warfactory"}
        self.assertTrue(self.fn(b, "ra2_soviets_rhinoheavytank"))

    def test_the_check_is_skipped_when_no_actor_name_is_given(self):
        """Back-compat: the old one-argument call must keep working."""
        self.assertTrue(self.fn({"Queue": "Infantry", "Prerequisites": "~x"}))

    def test_normalization_and_exact_token_matching(self):
        for prerequisite, expected in (("  ~UNIT  ", False), ("unit", False),
                                       ("~!unit", True), ("~unit_upgrade", True)):
            with self.subTest(prerequisite=prerequisite):
                self.assertEqual(self.fn({"Queue": "Infantry",
                                          "Prerequisites": prerequisite}, "unit"), expected)

    def test_existing_disabling_gates_still_apply(self):
        for buildable in (None, {}, {"Queue": ""},
                          {"Queue": "Infantry", "Prerequisites": "~wip, ~!unit"}):
            with self.subTest(buildable=buildable):
                self.assertFalse(self.fn(buildable, "unit"))


class ResolvedBuildabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import extract_stats
        from miniyaml import Ruleset
        cls.extract = staticmethod(extract_stats.extract_actor)
        cls.rules = Ruleset(ROOT)

    def test_inherited_spawn_only_and_one_off_reach_the_ledger(self):
        for name, section, expected in (("forgotten_mutant_wild", "infantry", False),
                                        ("tkm_bigshiee", "vehicles", True)):
            with self.subTest(actor=name):
                row = self.extract(self.rules, name, section)
                self.assertIsNotNone(row)
                self.assertEqual(row["buildable"], expected)


if __name__ == "__main__":
    unittest.main()
