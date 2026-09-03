"""Unit tests for the three audits added on 2026-08-23.

    tools/audit/audit_heaviness_bell.py
    tools/audit/audit_engine_freshness.py
    tools/audit/audit_upstream_adoption.py

All three were written on 2026-08-23, and two of them had a real defect on the first run. These
tests pin what broke, and the invariants the rulings rest on:

  * `audit_engine_freshness.read_version_file` read `engine/VERSION` as UTF-8. It is UTF-16 LE
    with a BOM — the SDK writes it from PowerShell, the same hazard that forces `bash
    run_all.sh` — so the audit reported a permanent, FALSE "the built engine is not the pinned
    one" on every machine.
  * `audit_heaviness_bell.belled` renormalises to a constant mean. That invariant IS the ruling
    in DESIGN §12.0i: if the mean drifts, `K` moves with heaviness and every weapon that sets an
    `h` is silently re-priced. A test is cheaper than discovering that in the ledger.
  * `audit_upstream_adoption.scan` binds each `[Desc(...)]` to the class BELOW it, and that
    association is what pairs a duplicate mechanic arriving under a different name. Get it wrong
    and a description leaks onto the next class, inventing duplicates that do not exist.
"""

from __future__ import annotations

import pathlib
import statistics
import tempfile
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

import audit_heaviness_bell as bell
import audit_engine_freshness as fresh
import audit_upstream_adoption as adopt


class CentreOfMass(unittest.TestCase):
    def test_anti_heavy_profile_sits_high_on_the_axis(self):
        # On ONE global scale the heaviest rungs no longer share x=2: Superheavy 2.0 is the only
        # armor there, Plate 1.833 and Concrete 1.333 sit below it.
        com = bell.centre_of_mass({"Plate": 100.0, "Concrete": 100.0, "Superheavy": 100.0})
        self.assertAlmostEqual(com, (1.8333 + 1.3333 + 2.0) / 3, places=3)
        self.assertGreater(com, 1.5)

    def test_heavy_is_below_superheavy_so_it_pulls_the_centre_down(self):
        heavier = bell.centre_of_mass({"Plate": 100.0, "Concrete": 100.0, "Superheavy": 100.0})
        lighter = bell.centre_of_mass({"Plate": 100.0, "Concrete": 100.0, "Heavy": 100.0})
        self.assertGreater(heavier, lighter)

    def test_anti_light_profile_sits_low(self):
        com = bell.centre_of_mass({"None": 100.0, "Wood": 100.0, "Scout": 100.0})
        self.assertLess(com, 0.5)

    def test_balanced_profile_sits_in_the_middle(self):
        # The infantry ladder is symmetric about 1.0, so its two ends average to exactly medium.
        com = bell.centre_of_mass({"None": 100.0, "Plate": 100.0})
        self.assertAlmostEqual(com, 1.0, places=3)

    def test_weighting_is_by_versus_not_by_count(self):
        # Two light rows at 10 vs one heavy row at 180: the heavy row dominates.
        com = bell.centre_of_mass({"None": 10.0, "Wood": 10.0, "Plate": 180.0})
        self.assertGreater(com, 1.5)

    def test_no_placeable_armor_returns_none(self):
        self.assertIsNone(bell.centre_of_mass({"Shield": 100.0}))

    def test_zero_rows_are_ignored_rather_than_dividing_by_zero(self):
        self.assertIsNone(bell.centre_of_mass({"None": 0.0, "Plate": 0.0}))


class BellPreservesTheMean(unittest.TestCase):
    """DESIGN §12.0i: heaviness redistributes, it never inflates. K must stay invariant in h."""

    PROFILE = {"None": 40.0, "Wood": 55.0, "Flak": 90.0, "Steel": 95.0,
               "Plate": 160.0, "Concrete": 150.0}

    def test_mean_is_unchanged_at_every_heaviness(self):
        before = statistics.mean(self.PROFILE.values())
        for h in (0.0, 0.5, 1.0, 1.5, 2.0):
            after = statistics.mean(bell.belled(self.PROFILE, bell.mu_of(self.PROFILE, h)).values())
            self.assertAlmostEqual(after, before, places=9, msg=f"mean drifted at h={h}")

    def test_off_axis_rows_pass_through_untouched_by_the_curve(self):
        profile = dict(self.PROFILE, Shield=200.0)
        out = bell.belled(profile, 1.0)
        # Shield has no x, so the curve does not apply — only the renormalisation scalar does.
        scale = out["None"] / profile["None"]
        self.assertNotAlmostEqual(scale, out["Shield"] / profile["Shield"], places=6)

    def test_shifting_heavier_raises_the_heavy_rows_relative_to_the_light_ones(self):
        com = bell.centre_of_mass(self.PROFILE)
        light = bell.belled(self.PROFILE, com - 0.25)
        heavy = bell.belled(self.PROFILE, com + 0.25)
        self.assertGreater(heavy["Plate"] / heavy["None"], light["Plate"] / light["None"])


class Direction(unittest.TestCase):
    RUNGS = ["Wood", "Steel", "Concrete"]

    def test_rising_profile_reads_up(self):
        self.assertEqual(
            bell.direction({"Wood": 50.0, "Steel": 80.0, "Concrete": 120.0}, self.RUNGS), "up")

    def test_falling_profile_reads_down(self):
        self.assertEqual(
            bell.direction({"Wood": 120.0, "Steel": 80.0, "Concrete": 50.0}, self.RUNGS), "down")

    def test_equal_endpoints_read_flat(self):
        self.assertEqual(
            bell.direction({"Wood": 90.0, "Steel": 10.0, "Concrete": 90.0}, self.RUNGS), "flat")

    def test_a_single_rung_is_unjudgeable(self):
        self.assertIsNone(bell.direction({"Wood": 90.0}, self.RUNGS))


class ArmorAxis(unittest.TestCase):
    """ONE GLOBAL 13-slot scale, 0..2, step 1/6 (maintainer 2026-08-24).

    Two earlier forms are retired. §12.0d's three coarse buckets tied armors INSIDE a ladder
    (Bomber and Helicopter both at x=1), and tied coordinates move together under the bell, so
    heaviness could not tell them apart at all. The per-ladder 0..2 normalisation that replaced it
    was unique within a ladder but collided four ways ACROSS ladders, which is what the maintainer
    rejected: every armor gets its own value.
    """

    RULED_ORDER = ["Scout", "None", "Fighter", "Light", "Wood", "Bomber",
                   "Flak", "Medium", "Steel",            # the one deliberate tie, all at 1.0
                   "Helicopter", "Concrete", "Heavy", "Spaceship", "Plate", "Superheavy"]

    def test_the_global_order_is_the_ruled_one(self):
        got = sorted(bell.BUCKET, key=lambda a: (bell.BUCKET[a], self.RULED_ORDER.index(a)))
        self.assertEqual(got, self.RULED_ORDER)

    def test_thirteen_evenly_spaced_slots_from_zero_to_two(self):
        slots = sorted(set(bell.BUCKET.values()))
        self.assertEqual(len(slots), 13)
        self.assertAlmostEqual(slots[0], 0.0)
        self.assertAlmostEqual(slots[-1], 2.0)
        for a, b in zip(slots, slots[1:]):
            self.assertAlmostEqual(b - a, 2.0 / 12, places=3)

    def test_every_ladder_is_centred_exactly_on_medium(self):
        """The property that makes h=1 mean "medium" in all four domains at once.

        My own candidate axis put infantry at 0.15..0.95, so a peak at h=1 sat ABOVE the whole
        infantry ladder and a Medium weapon would have favoured Plate. Centring every ladder on
        1.0 is what the maintainer's ordering gets right and mine did not.
        """
        for ladder, rungs in bell.LADDERS.items():
            centre = (bell.BUCKET[rungs[0]] + bell.BUCKET[rungs[-1]]) / 2
            self.assertAlmostEqual(centre, 1.0, places=3, msg=ladder)

    def test_the_only_tie_is_the_ruled_one_and_it_crosses_ladders(self):
        """Flak · Medium · Steel share exactly 1.0 — deliberate, and mechanically free.

        They sit in three DIFFERENT ladders, and the rank restore is per-ladder, so they are never
        in competition: de-tying them (Flak 0.95 / Steel 1.05) moves no row by more than 0.89%.
        The tie buys perfect symmetry. A tie WITHIN one ladder stays forbidden.
        """
        tied = [a for a, x in bell.BUCKET.items() if x == 1.0]
        self.assertEqual(sorted(tied), ["Flak", "Medium", "Steel"])
        self.assertEqual(len({bell.LADDERS_OF[a] for a in tied}), 3)

    def test_the_ladder_widths_are_the_ruled_design_claim(self):
        # Vehicles span the whole scale, infantry nearly as much, buildings least — they
        # compensate with HP, and a narrow ladder keeps anti-light weapons usable on bunkers.
        width = {k: round(bell.BUCKET[r[-1]] - bell.BUCKET[r[0]], 3)
                 for k, r in bell.LADDERS.items()}
        self.assertEqual(width["VEH"], 2.0)
        self.assertGreater(width["INF"], width["AIR"])
        self.assertGreater(width["AIR"], width["BLD"])

    def test_each_ladder_is_strictly_increasing(self):
        for ladder, rungs in bell.LADDERS.items():
            xs = [bell.BUCKET[r] for r in rungs]
            self.assertEqual(xs, sorted(xs), ladder)
            self.assertEqual(len(set(xs)), len(xs), f"{ladder} has tied coordinates")

    def test_helicopter_is_heavier_than_bomber(self):
        # Both read as "medium", but the helicopter is the heavier of the two. On ONE scale the
        # maintainer's statement becomes literally checkable against the VEHICLE rungs:
        # "helicopter is in between medium and heavy while bomber is between light and medium".
        self.assertGreater(bell.BUCKET["Helicopter"], bell.BUCKET["Bomber"])
        self.assertLess(bell.BUCKET["Light"], bell.BUCKET["Bomber"])
        self.assertLess(bell.BUCKET["Bomber"], bell.BUCKET["Medium"])
        self.assertLess(bell.BUCKET["Medium"], bell.BUCKET["Helicopter"])
        self.assertLess(bell.BUCKET["Helicopter"], bell.BUCKET["Heavy"])

    def test_scout_is_lighter_than_light_and_superheavy_heavier_than_heavy(self):
        self.assertLess(bell.BUCKET["Scout"], bell.BUCKET["Light"])
        self.assertGreater(bell.BUCKET["Superheavy"], bell.BUCKET["Heavy"])

    def test_the_rank_restore_preserves_every_ladder_order(self):
        """§12.0d: the tilt is applied to VALUES, then each armor is given back its RANK.

        Without this step the bell reorders ladders — 127 cases across 60 family/ladder pairs on
        the real profiles. With it, zero.
        """
        profile = {"Scout": 40.0, "Light": 55.0, "Medium": 90.0, "Heavy": 95.0,
                   "Superheavy": 160.0, "None": 30.0, "Flak": 70.0, "Plate": 150.0}
        want = {lad: sorted([a for a in rungs if a in profile], key=lambda a: profile[a])
                for lad, rungs in bell.LADDERS.items()}
        for mu in (0.0, 0.5, 1.0, 1.5, 2.0):
            out = bell.belled(profile, mu)
            for lad, rungs in bell.LADDERS.items():
                got = sorted([a for a in rungs if a in out], key=lambda a: out[a])
                if len(got) >= 2:
                    self.assertEqual(got, want[lad], f"{lad} reordered at mu={mu}")

    def test_the_rank_restore_does_not_disturb_the_mean(self):
        # It permutes values within a ladder, so the multiset — and the mean — are unchanged.
        profile = {"Scout": 40.0, "Light": 55.0, "Medium": 90.0, "Heavy": 95.0, "Superheavy": 160.0}
        before = statistics.mean(profile.values())
        for mu in (0.0, 1.0, 2.0):
            self.assertAlmostEqual(statistics.mean(bell.belled(profile, mu).values()),
                                   before, places=9)

    def test_a_heavier_shift_separates_bomber_from_helicopter(self):
        """The distinction the coarse axis could not express at all.

        Bomber (x=0.833) and Helicopter (x=1.167) both read as "medium", but the helicopter is the
        heavier of the two. As the peak moves heavier the gap between them must WIDEN. Under the
        three-bucket axis they shared x=1 and moved identically, so the gap never changed.

        ⚠ The profile needs a real gradient: after §12.0d's rank restore a FLAT profile has no
        order to preserve, so every ratio stays 1.0 no matter where the peak sits.
        """
        profile = {"Fighter": 50.0, "Bomber": 70.0, "Helicopter": 90.0, "Spaceship": 120.0}
        light = bell.belled(profile, 0.75)
        heavy = bell.belled(profile, 1.25)
        self.assertGreater(heavy["Helicopter"] / heavy["Bomber"],
                           light["Helicopter"] / light["Bomber"])

    def test_a_flat_profile_gets_its_ties_broken_toward_ladder_order(self):
        """What actually happens to a family with NO gradient, e.g. Sonic or Magic.

        The rank restore sorts by the value each armor held. With every value equal, Python's
        sort is stable, so the "rank held" falls back to the ladder's own lightest -> heaviest
        order — and the bell's tilted magnitudes are then handed out along it. So a flat family
        is not inert under heaviness: it picks up a mild gradient pointing the same way as the
        ladder. That is a reasonable tie-break rather than a defect, but it is worth pinning,
        because it means "flat family" does NOT mean "heaviness does nothing".
        """
        profile = {a: 100.0 for a in bell.LADDERS["AIR"]}
        out = bell.belled(profile, 1.5)
        ordered = [out[a] for a in bell.LADDERS["AIR"]]
        self.assertEqual(ordered, sorted(ordered), "ties should break toward ladder order")
        self.assertGreater(out["Helicopter"], out["Bomber"])
        # And the mean is still untouched, so it costs nothing in price terms.
        self.assertAlmostEqual(statistics.mean(out.values()), 100.0, places=9)

    def test_the_ruled_constants(self):
        """LO and sigma were BOTH re-ruled on 2026-08-24; SHIFT was deleted with the old peak.

        LO 0.80 was measured against the retired family-anchored model, where the peak moved only
        0.25. Under the blend it sweeps a full 1.0, and at 0.80 the continuous model came out much
        gentler than the discrete tilt that already ships (per-ladder 0.68-0.84 vs 0.50-0.52).
        0.667 is 1/TILT_RATIO — the same 1.5x span `class_tilt` uses.
        """
        self.assertAlmostEqual(bell.LO, 0.667)
        self.assertAlmostEqual(1 / bell.LO, 1.5, places=2)
        self.assertAlmostEqual(bell.SIGMA, 0.75)
        self.assertFalse(hasattr(bell, "SHIFT"), "SHIFT went with the family-anchored peak")

    def test_mu_blends_the_heaviness_with_the_family_mass(self):
        """§12.0i, ruled 2026-08-24: mu = (h + centre_of_mass) / 2.

        Neither pure form was ruled. `mu = centre_of_mass + 0.25*(h-1)` made h=1 mean "wherever
        this family already sits" rather than "medium"; `mu = h` was safe when re-measured (0
        reorderings, unlike the 26-of-42 recorded before the rank restore existed) but gives the
        family no formal say. The blend halves the distance.
        """
        profile = {"None": 40.0, "Flak": 100.0, "Plate": 160.0}
        com = bell.centre_of_mass(profile)
        for h in (0.0, 0.5, 1.0, 1.5, 2.0):
            self.assertAlmostEqual(bell.mu_of(profile, h), (h + com) / 2, places=9)
        # It always lies between the family's own mass and the requested heaviness.
        self.assertLess(bell.mu_of(profile, 2.0), 2.0)
        self.assertGreater(bell.mu_of(profile, 2.0), com)
        self.assertIsNone(bell.mu_of({"Shield": 100.0}, 1.0))

    def test_the_off_axis_armors_are_not_on_the_axis(self):
        # §12.0c Shield, §12.0b Heroic and the §12.0e platings are excluded by ruling.
        for armor in bell.OFF_AXIS:
            self.assertNotIn(armor, bell.BUCKET, armor)


class ReadVersionFile(unittest.TestCase):
    """engine/VERSION is written by the SDK from PowerShell, i.e. UTF-16 LE with a BOM."""

    HASH = "462fc1fc4bfc490c42b88b429670c7f0c64c7aca"

    def written(self, data: bytes) -> str | None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "VERSION"
            path.write_bytes(data)
            return fresh.read_version_file(path)

    def test_utf16_le_with_bom_is_the_real_case(self):
        self.assertEqual(self.written(("﻿" + self.HASH).encode("utf-16-le")), self.HASH)

    def test_utf16_be_with_bom(self):
        self.assertEqual(self.written(("﻿" + self.HASH).encode("utf-16-be")), self.HASH)

    def test_plain_utf8_still_works(self):
        self.assertEqual(self.written(self.HASH.encode("utf-8")), self.HASH)

    def test_utf8_with_bom_still_works(self):
        self.assertEqual(self.written(("﻿" + self.HASH).encode("utf-8")), self.HASH)

    def test_trailing_whitespace_and_newlines_are_stripped(self):
        self.assertEqual(self.written((self.HASH + "\r\n\r\n").encode("utf-8")), self.HASH)

    def test_a_missing_file_is_none_rather_than_an_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(fresh.read_version_file(pathlib.Path(tmp) / "absent"))


class GitHelper(unittest.TestCase):
    def test_a_failed_git_call_returns_none_rather_than_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(fresh.git(pathlib.Path(tmp), "rev-parse", "no-such-ref"))

    def test_indented_format_output_keeps_its_indent(self):
        # The helper strips newlines only: a --format that indents must survive it.
        root = pathlib.Path(__file__).resolve().parents[2]
        out = fresh.git(root, "log", "-1", "--format=  indented")
        if out is not None:                      # skip where git or history is unavailable
            self.assertTrue(out.startswith("  "), repr(out))


class DescriptionNormalisation(unittest.TestCase):
    """The pairing that catches a duplicate mechanic under a different name."""

    def test_case_punctuation_and_spacing_are_ignored(self):
        self.assertEqual(adopt.norm("This actor can be affected by temporal warheads."),
                         adopt.norm("this  actor CAN be affected by temporal warheads"))

    def test_genuinely_different_text_does_not_collide(self):
        self.assertNotEqual(adopt.norm("Creates a smudge in `SmudgeLayer`."),
                            adopt.norm("Spawn actors upon explosion."))

    def test_the_temporal_pair_that_started_this_is_recorded(self):
        # RV's Temporal/AffectedByTemporal ARE CA's WarpDamage/Warpable. The prose pairs the
        # traits; only reading both implementations pairs the warheads, so they are manual.
        self.assertIn("Temporal", adopt.KNOWN_EQUIVALENTS)
        self.assertIn("AffectedByTemporal", adopt.KNOWN_EQUIVALENTS)


class ScanAssociatesDescWithTheClassBelowIt(unittest.TestCase):
    def scan(self, source: str):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "Thing.cs").write_text(source, encoding="utf-8")
            return adopt.scan(root)

    def test_info_class_yields_the_yaml_name_without_the_suffix(self):
        names, _descs = self.scan("public class GrantConditionOnDeployInfo : TraitInfo { }")
        self.assertIn("GrantConditionOnDeploy", names)

    def test_warhead_class_yields_the_yaml_name_without_the_suffix(self):
        names, _descs = self.scan("public class SpreadDamageWarhead : Warhead { }")
        self.assertIn("SpreadDamage", names)

    def test_desc_binds_to_the_class_that_follows_it(self):
        _names, descs = self.scan(
            '[Desc("First mechanic.")]\n'
            'public class AlphaInfo : TraitInfo { }\n'
            '[Desc("Second mechanic.")]\n'
            'public class BetaInfo : TraitInfo { }\n')
        self.assertEqual(descs["Alpha"], "First mechanic.")
        self.assertEqual(descs["Beta"], "Second mechanic.")

    def test_a_desc_is_not_reused_by_a_later_undescribed_class(self):
        _names, descs = self.scan(
            '[Desc("Only Alpha has this.")]\n'
            'public class AlphaInfo : TraitInfo { }\n'
            'public class BetaInfo : TraitInfo { }\n')
        self.assertEqual(descs["Alpha"], "Only Alpha has this.")
        self.assertNotIn("Beta", descs)

    def test_obj_and_bin_output_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "obj").mkdir()
            (root / "obj" / "Generated.cs").write_text(
                "public class GeneratedInfo : TraitInfo { }", encoding="utf-8")
            names, _descs = adopt.scan(root)
        self.assertNotIn("Generated", names)

    def test_a_missing_directory_is_empty_rather_than_an_exception(self):
        names, descs = adopt.scan(pathlib.Path("no", "such", "dir"))
        self.assertEqual((names, descs), ({}, {}))


class UsageCount(unittest.TestCase):
    """A type its own mod never references is dead code there too, not a porting candidate."""

    def counts(self, yaml_text: str, names):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "mods").mkdir()
            (root / "mods" / "rules.yaml").write_text(yaml_text, encoding="utf-8")
            return adopt.usage_count(root, ["mods"], set(names))

    def test_a_bare_trait_declaration_counts(self):
        self.assertEqual(self.counts("actor:\n\tLaysMinefield:\n", {"LaysMinefield"}),
                         {"LaysMinefield": 1})

    def test_a_suffixed_trait_declaration_counts(self):
        self.assertEqual(self.counts("actor:\n\tLaysMinefield@x:\n", {"LaysMinefield"}),
                         {"LaysMinefield": 1})

    def test_a_value_reference_counts(self):
        self.assertEqual(self.counts("weapon:\n\tWarhead@1: CashHack\n", {"CashHack"}),
                         {"CashHack": 1})

    def test_an_unreferenced_type_counts_zero(self):
        self.assertEqual(self.counts("actor:\n\tSomethingElse:\n", {"LaysMinefield"}),
                         {"LaysMinefield": 0})


if __name__ == "__main__":
    unittest.main()
