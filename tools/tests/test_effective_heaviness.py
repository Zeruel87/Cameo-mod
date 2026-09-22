"""Focused tests for §12.0i continuous heaviness (effective_heaviness + pricing wiring).

Covers the bounded CORE: sentinel -1 vs active 0, anchor validation, piecewise
ties-even band interpolation, the single bell pass, radius geometry scaling,
byte-equivalence of omitted behaviour on the committed golden fixture, and the
mirror honesty checks for flat families. The C#-execution differential lives in
``OpenRA.Mods.Cameo.Test/AreaDamageWarheadHeavinessTest.cs`` (needs a parent
build to run; see the gaps note in the session report).
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import effective_heaviness as eh  # noqa: E402
import percentage_damage as pd  # noqa: E402
import weapon_efficiency as we  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
import target_model as tm  # noqa: E402


def field(key: str, value="", children=None):
    from miniyaml import Node
    return Node(key, str(value), list(children or []))


def table(key: str, **values):
    return field(key, children=[field(name, value) for name, value in values.items()])


LIGHT = {"None": 10, "Flak": 30, "Plate": 50, "Medium": 40}
MEDIUM = {"None": 20, "Flak": 35, "Plate": 40, "Medium": 38}
HEAVY = {"None": 30, "Flak": 28, "Plate": 60, "Medium": 36}


class HeavinessValidationTest(unittest.TestCase):
    def test_invalid_heaviness_rejected(self):
        with self.assertRaisesRegex(eh.HeavinessError, "must be -1"):
            eh.heaviness_of(field("W", "AreaDamage", [field("Heaviness", 2500)]))
        with self.assertRaisesRegex(eh.HeavinessError, "must be -1"):
            eh.heaviness_of(field("W", "AreaDamage", [field("Heaviness", -500)]))

    def test_omitted_means_disabled_and_zero_is_active(self):
        self.assertEqual(eh.heaviness_of(field("W", "AreaDamage")), eh.DISABLED)
        self.assertEqual(eh.heaviness_of(field("W", "AreaDamage",
                                              [field("Heaviness", 0)])), 0)

    def test_endpoints_rejected_with_disabled_heaviness(self):
        with self.assertRaisesRegex(eh.HeavinessError, "require an active Heaviness"):
            eh.validate_anchors(-1, LIGHT, MEDIUM, HEAVY)
        # Omitted (absent) endpoints on a disabled warhead are fine — no bands.
        eh.validate_anchors(-1, {}, {}, {})

    def test_single_endpoint_rejected(self):
        with self.assertRaisesRegex(eh.HeavinessError, "must both be set"):
            eh.validate_anchors(1000, LIGHT, MEDIUM, {})

    def test_endpoints_require_explicit_medium(self):
        with self.assertRaisesRegex(eh.HeavinessError, "explicit PercentageVersus"):
            eh.validate_anchors(1000, LIGHT, {}, HEAVY)

    def test_mismatched_anchor_keys_rejected(self):
        short = {k: v for k, v in HEAVY.items() if k != "Medium"}
        with self.assertRaisesRegex(eh.HeavinessError, "keys must match"):
            eh.validate_anchors(1000, LIGHT, MEDIUM, short)
        with self.assertRaisesRegex(eh.HeavinessError, "keys must match"):
            eh.validate_anchors(1000, short, MEDIUM, HEAVY)

    def test_matching_anchors_accepted(self):
        eh.validate_anchors(0, LIGHT, MEDIUM, HEAVY)
        eh.validate_anchors(2000, LIGHT, MEDIUM, HEAVY)


class TieEvenInterpolationTest(unittest.TestCase):
    def test_ties_even_rounding_rule(self):
        self.assertEqual(eh.round_half_even(5, 2), 2)      # 2.5 -> 2 (even)
        self.assertEqual(eh.round_half_even(7, 2), 4)      # 3.5 -> 4 (even)
        self.assertEqual(eh.round_half_even(3, 2), 2)      # 1.5 -> 2 (even)
        self.assertEqual(eh.round_half_even(1, 2), 0)      # 0.5 -> 0 (even)
        self.assertEqual(eh.round_half_even(2501, 1000), 3)
        self.assertEqual(eh.round_half_even(1500, 1000), 2)
        self.assertEqual(eh.round_half_even(-1500, 1000), -2)

    def test_h500_interpolates_halfway_lower_band(self):
        out = eh.interpolate_percentage_bands(LIGHT, MEDIUM, HEAVY, 500)
        for armor in MEDIUM:
            expected = eh.round_half_even(
                LIGHT[armor] * 500 + MEDIUM[armor] * 500, 1000)
            self.assertEqual(out[armor], expected)

    def test_h1000_lands_on_medium_exactly(self):
        out = eh.interpolate_percentage_bands(LIGHT, MEDIUM, HEAVY, 1000)
        self.assertEqual(out, MEDIUM)

    def test_h1500_interpolates_halfway_upper_band(self):
        out = eh.interpolate_percentage_bands(LIGHT, MEDIUM, HEAVY, 1500)
        for armor in MEDIUM:
            expected = eh.round_half_even(
                MEDIUM[armor] * 500 + HEAVY[armor] * 500, 1000)
            self.assertEqual(out[armor], expected)

    def test_h0_and_h2000_lands_on_endpoints(self):
        self.assertEqual(eh.interpolate_percentage_bands(LIGHT, MEDIUM, HEAVY, 0), LIGHT)
        self.assertEqual(eh.interpolate_percentage_bands(LIGHT, MEDIUM, HEAVY, 2000), HEAVY)

    def test_5_8_10_profile_is_not_a_linear_midpoint_at_h1000(self):
        # The 5/8/10 family band is NOT linear: interpolation between the 5 and
        # 10 endpoints gives 7.5 -> ties-even 8 at h=1 — coincidentally equal to
        # the authored 8, but for the 25/40/50 Magic band the midpoint is 37.5,
        # NOT 40. The provisional ruling (interpolated) is recorded here.
        self.assertEqual(eh.round_half_even(75, 10), 8)
        self.assertEqual(eh.round_half_even(375, 10), 38)
        self.assertNotEqual(eh.round_half_even(375, 10), 40)


class BellAndProfileTest(unittest.TestCase):
    def test_flat_family_returns_table_unchanged(self):
        flat = {a: 55 for a in
                ("Scout", "Light", "Medium", "Heavy", "Superheavy", "None",
                 "Flak", "Plate", "Wood", "Steel", "Concrete", "Fighter",
                 "Bomber", "Helicopter", "Spaceship", "Shield")}
        for h in (0.0, 1.0, 2.0):
            out = eh.bell_transform(flat, h)
            self.assertEqual(out, {a: int(v) for a, v in flat.items()})

    def test_active_profile_bells_once_not_twice(self):
        versus = dict(LIGHT)
        once = eh.versus_profile(versus, 1000)
        twice = eh.bell_transform({k: float(v) for k, v in once.items()}, 1.0)
        # A second bell on an already-belled table is not idempotent in general;
        # the pipeline must apply it exactly once, which the profile helper does.
        self.assertIsInstance(once, dict)
        self.assertNotEqual(once, twice)

    def test_disabled_profile_is_verbatim(self):
        versus = dict(LIGHT)
        self.assertEqual(eh.versus_profile(versus, -1), versus)
        self.assertEqual(
            eh.percentage_profile(versus, MEDIUM, {}, {}, -1), MEDIUM)
        self.assertEqual(
            eh.percentage_profile(versus, {}, {}, {}, -1), versus)

    def test_bands_activation_path(self):
        out = eh.percentage_profile(LIGHT, MEDIUM, LIGHT, HEAVY, 500)
        raw = eh.bell_transform(
            eh.interpolate_percentage_bands(LIGHT, MEDIUM, HEAVY, 500), 0.5)
        self.assertEqual(out, raw)

    def test_percentage_scale_dial_is_untouched(self):
        # PercentageScale stays the scalar dial: the folded basis-point
        # arithmetic (and therefore runtime_units) is identical with and
        # without an active Heaviness.
        from miniyaml import Node
        node = Node("Warhead@p", "AreaDamage", [
            field("Damage", 6000),
            field("PercentageScale", 10000),
        ])
        apps_plain = pd.percentage_applications(field("W", None, [node]),
                                                tm.reference_hp())
        node.children.append(field("Heaviness", 1500))
        apps_active = pd.percentage_applications(field("W", None, [node]),
                                                 tm.reference_hp())
        self.assertEqual(apps_plain[0]["runtime_units"],
                         apps_active[0]["runtime_units"])
        self.assertEqual(apps_plain[0]["scale"], apps_active[0]["scale"])


class GeometryTest(unittest.TestCase):
    def test_scale_length_truncates_toward_zero_like_the_c_cast(self):
        # Spread 43 at h=0: 43 * 2/3 = 28.67 -> 28
        self.assertEqual(eh.scale_length(43, 0), 28)
        # h=1 -> identity
        self.assertEqual(eh.scale_length(43, 1000), 43)
        # h=2: 43 * 4/3 = 57.33 -> 57
        self.assertEqual(eh.scale_length(43, 2000), 57)

    def test_explicit_range_and_shockwave_scale_consistently(self):
        geom = eh.effective_geometry(600, [600, 1200, 2400], 500, 4000, 1000)
        self.assertEqual(geom, {"spread": 600, "range": [600, 1200, 2400],
                                "min_radius": 500, "max_radius": 4000})
        geom = eh.effective_geometry(600, [600, 1200, 2400], 500, 4000, 0)
        self.assertEqual(geom["spread"], 400)
        self.assertEqual(geom["range"], [400, 800, 1600])
        self.assertEqual(geom["min_radius"], 333)
        self.assertEqual(geom["max_radius"], 2666)

    def test_disabled_geometry_is_verbatim(self):
        geom = eh.effective_geometry(43, [100, 200], 250, 4000, -1)
        self.assertEqual(geom, {"spread": 43, "range": [100, 200],
                                "min_radius": 250, "max_radius": 4000})


class ByteEquivalenceGoldenTest(unittest.TestCase):
    """Legacy-content compatibility fixture, isolated from intentional pilot changes.

    The live new base changes the template Shield mean used by pricing globally.
    Remove it ONLY in this frozen legacy test and restore the captured TS90mm
    payload; live audits and ledgers retain every compatibility duplicate.
    """

    GOLDEN = ROOT / "tools/tests/fixtures/heaviness_pricing_golden.json"

    @classmethod
    def setUpClass(cls):
        if not cls.GOLDEN.exists():
            raise unittest.SkipTest("golden fixture not committed")
        cls.golden = json.loads(cls.GOLDEN.read_text(encoding="utf-8"))

    def test_pricing_output_matches_pre_change_golden(self):
        rs = Ruleset(ROOT)
        # The census reads authored rows, so restore the exact reviewed source
        # checkpoint as well as the original template set for this legacy test.
        from reviewed_weapon_history import (
            missile_role_changes, missile_parent_role_changes, restore_missile_role)
        for name in missile_role_changes().keys() | missile_parent_role_changes().keys():
            rs.weapons[name] = restore_missile_role(self, rs.weapon(name), source=True)
        rs.weapons.pop("^Warhead_CannonAP", None)
        # The later Sonic additions alter the live diagnostic shield census.
        # This frozen wiring-equivalence test retains its original family set.
        sonic_additions = [name for name in rs.weapons if name.startswith((
            '^Warhead_BulletSonic_', '^Warhead_MissileSonic_',
            '^Warhead_CannonSonic_', '^Warhead_BlastSonic_'))]
        self.assertEqual(len(sonic_additions), 12)
        for name in sonic_additions:
            rs.weapons.pop(name)
        legacy = json.loads((self.GOLDEN.parent / "heaviness_legacy_ts90mm.json").read_text(encoding="utf-8"))

        def from_obj(key, value):
            if not isinstance(value, dict):
                return field(key, value)
            return field(key, value.get("__value", ""),
                         [from_obj(k, v) for k, v in value.items() if k != "__value"])

        self.addCleanup(we.use_ruleset, we._INJECTED)
        self.addCleanup(tm.use_ruleset, tm._INJECTED)
        we.use_ruleset(rs)
        tm.use_ruleset(rs)
        cache = {}
        for name, record in self.golden["weapons"].items():
            if name == "FirehawkBomb" and name not in rs.weapons:
                name = "td_gdi_firehawk_firehawkbomb"
            resolved = from_obj(name, legacy) if name == "TS90mm" else rs.resolve_weapon(name)
            self.assertIsNotNone(resolved, name)

            def clean(value):
                if isinstance(value, float):
                    return round(value, 10)
                if isinstance(value, dict):
                    return {k: (round(v, 10) if isinstance(v, float) else v)
                            for k, v in sorted(value.items())}
                return value

            apps = []
            for app in pd.percentage_applications(resolved, self.golden["reference_hp"]):
                apps.append({k: clean(v) for k, v in app.items() if k != "node"})
            self.assertEqual(len(apps), len(record["pct"]), name)
            for got, want in zip(apps, record["pct"]):
                for key, value in want.items():
                    self.assertEqual(got.get(key), value,
                                     f"{name}: {key} moved under the new wiring")
            res = we.analyse(resolved)
            got = {}
            if res is not None:
                got = {k: (round(res[k], 10) if isinstance(res[k], float) else res[k])
                       for k in ("k", "sigma", "instant")}
                got["parts"] = [{k: (round(v, 10) if isinstance(v, float) else v)
                                 for k, v in sorted(p.items())}
                                for p in res["parts"]]
            if want_or_none := record["analyse"]:
                for key, value in want_or_none.items():
                    self.assertEqual(got.get(key), value,
                                     f"{name}: analyse.{key} moved")
            else:
                self.assertIsNone(res, name)


class PricingWiringTest(unittest.TestCase):
    """Synthetic AreaDamage nodes through the real ed/pd entry points."""

    def test_switching_rulesets_clears_shield_census_caches(self):
        from types import SimpleNamespace
        self.addCleanup(tm.use_ruleset, tm._INJECTED)
        def rules(shield):
            return SimpleNamespace(actors={}, weapons={"W": field("W", children=[
                field("Warhead@Main", "AreaDamage", [table("Versus", Shield=shield)])])})
        tm.use_ruleset(rules(200))
        self.assertEqual(tm.pseudo_armor_mean("Shield"), 200)
        self.assertEqual(tm.shield_damage_share(), 0)
        self.assertEqual(tm.shield_damage_share.cache_info().currsize, 1)
        tm.use_ruleset(rules(400))
        self.assertEqual(tm.shield_damage_share.cache_info().currsize, 0)
        self.assertEqual(tm.pseudo_armor_mean("Shield"), 400)

    @staticmethod
    def area_warhead(*extra):
        from miniyaml import Node
        return Node("Warhead@main", "AreaDamage", [
            field("Damage", 2000),
            field("Spread", 600),
            field("Falloff", "100, 37, 14, 5, 0"),
            field("Ticks", 4),
            field("MaxRadius", 4000),
            field("MinRadius", 500),
            *extra,
        ])

    def test_active_heaviness_scales_geometry_through_ed(self):
        import effective_damage as ed
        active = self.area_warhead(field("Heaviness", 500))
        fo, radii, live = ed.falloff_and_radii(active)
        self.assertTrue(live)
        # Authored radii [0,600,1200,1800,2400] scale by (0.5+2)/3 = 5/6.
        self.assertEqual(radii, [0, 500, 1000, 1500, 2000])
        samples = ed.area_geometry_samples(active, fo, radii, 300.0)
        self.assertEqual(len(samples), 4)
        # Effective shockwave endpoints scale consistently (Min 500 -> 416,
        # Max 4000 -> 3333 under the C# truncate-toward-zero cast).
        geom = eh.effective_geometry(600, None, 500, 4000, 500)
        self.assertEqual((geom["min_radius"], geom["max_radius"]), (416, 3333))

    def test_disabled_geometry_is_byte_identical_through_ed(self):
        import effective_damage as ed
        plain = self.area_warhead()
        fo, radii, live = ed.falloff_and_radii(plain)
        self.assertEqual(radii, [0, 600, 1200, 1800, 2400])
        self.assertTrue(live)
        samples = ed.area_geometry_samples(plain, fo, radii, 300.0)
        self.assertEqual(len(samples), 4)

    def test_percentages_carry_heaviness_metadata(self):
        runner = pd.percentage_applications(
            field("W", None, [self.area_warhead()]), tm.reference_hp())
        for app in runner:
            self.assertEqual(app.get("heaviness"), eh.DISABLED)

    @staticmethod
    def versus_table_node(name, values):
        from miniyaml import Node
        return Node(name, "", [Node(k, str(v), [])
                               for k, v in sorted(values.items())])

    def test_anchor_validation_fires_through_the_pricing_path(self):
        broken = self.area_warhead(
            field("Heaviness", 1000),
            self.versus_table_node("PercentageVersus", {"None": 20, "Flak": 35}),
            self.versus_table_node("PercentageVersusLight", {"None": 10, "Flak": 30}),
            self.versus_table_node("PercentageVersusHeavy", {"None": 30}),
        )
        with self.assertRaisesRegex(eh.HeavinessError, "keys must match"):
            pd.percentage_applications(
                field("W", None, [broken]), tm.reference_hp())


class ChecklistRegressionTest(unittest.TestCase):
    """Independent-review checklist (HEAVINESS_CORE_REVIEW_CHECKLIST_20260910).

    Regression guards for the review findings — none of the earlier tests are
    weakened by these; they only ADD coverage.
    """

    @staticmethod
    def versus_table_node(name, values):
        from miniyaml import Node
        return Node(name, "", [Node(k, str(v), [])
                               for k, v in sorted(values.items())])

    @staticmethod
    def percentage_twin(*extra_nodes):
        from miniyaml import Node
        return Node("Warhead@pct", "AreaDamagePercentage", [
            field("Damage", 20),
            field("Spread", 600),
            *extra_nodes,
        ])

    # --- checklist: subclass inherits Heaviness, nothing silently dropped ---
    def test_subclass_active_heaviness_bells_its_own_versus(self):
        runner = pd.percentage_applications(field("W", None, [self.percentage_twin(
            field("Heaviness", 1000),
            self.versus_table_node("Versus", {"Heavy": 19, "Light": 17, "Scout": 16}),
        )]), tm.reference_hp())
        self.assertEqual(len(runner), 1)
        self.assertEqual(runner[0]["heaviness"], 1000)
        # Python mirror for {"Heavy":19,"Light":17,"Scout":16} at h=1.0.
        self.assertEqual(runner[0]["versus"], {"Heavy": 19, "Light": 18, "Scout": 15})

    def test_subclass_disabled_heaviness_is_verbatim(self):
        runner = pd.percentage_applications(field("W", None, [self.percentage_twin(
            field("Heaviness", -1),
            self.versus_table_node("Versus", {"Heavy": 19, "Light": 17, "Scout": 16}),
        )]), tm.reference_hp())
        self.assertEqual(runner[0]["versus"], {"Heavy": 19, "Light": 17, "Scout": 16})

    def test_subclass_rejects_percentage_versus_anchors(self):
        twin = self.percentage_twin(
            field("Heaviness", 1000),
            self.versus_table_node("PercentageVersus", {"None": 20, "Flak": 35}),
            self.versus_table_node("PercentageVersusLight", {"None": 10, "Flak": 30}),
            self.versus_table_node("PercentageVersusHeavy", {"None": 30, "Flak": 28}),
        )
        with self.assertRaisesRegex(eh.HeavinessError, "forbids entirely"):
            pd.percentage_applications(field("W", None, [twin]), tm.reference_hp())

    def test_subclass_geometry_scales_under_active_h(self):
        import effective_damage as ed
        twin = self.percentage_twin(field("Heaviness", 500))
        _, radii, live = ed.falloff_and_radii(twin)
        self.assertTrue(live)
        self.assertEqual(radii, [0, 500, 1000, 1500, 2000])

    # --- non-negative endpoint values, mirrored from the C# rules-load ---
    def test_negative_endpoint_value_rejected(self):
        with self.assertRaisesRegex(eh.HeavinessError, "non-negative"):
            eh.validate_anchors(1000, {k: -1 for k in MEDIUM}, MEDIUM, HEAVY)
        with self.assertRaisesRegex(eh.HeavinessError, "non-negative"):
            eh.validate_anchors(1000, LIGHT, {k: -5 for k in MEDIUM}, HEAVY)
        with self.assertRaisesRegex(eh.HeavinessError, "non-negative"):
            eh.validate_anchors(1000, LIGHT, MEDIUM, {k: -1 for k in HEAVY})

    # --- unsafe tables fail SAFE (unchanged), never crash ---
    def test_all_unknown_armor_table_handled_safely(self):
        out = eh.bell_transform({"Foo": 100, "Bar": 50}, 1.0)
        self.assertEqual(out, {"Foo": 100, "Bar": 50})

    def test_derived_only_armor_table_handled_safely(self):
        out = eh.bell_transform({"Heroic": 10, "Airborne": 5}, 1000)
        self.assertEqual(out, {"Heroic": 10, "Airborne": 5})

    # --- no double bell, including the percentage -> flat Versus fallback ---
    def test_fallback_to_flat_versus_bells_exactly_once(self):
        versus = dict(LIGHT)
        effective_pct = eh.percentage_profile(versus, {}, {}, {}, 1000)
        self.assertEqual(effective_pct, eh.versus_profile(versus, 1000))
        # A second bell on the already-belled result differs (single application).
        self.assertNotEqual(effective_pct,
                            eh.bell_transform({k: float(v) for k, v in effective_pct.items()}, 1.0))

    # --- authored MaxRadius>0 branch preserved under scaling truncation ---
    def test_shockwave_branch_survives_truncated_tiny_radii(self):
        import effective_damage as ed
        from miniyaml import Node
        twin = Node("Warhead@w", "AreaDamage", [
            field("Spread", 600),
            field("Falloff", "100, 37, 14, 5, 0"),
            field("Ticks", 4),
            field("MinRadius", 1),
            field("MaxRadius", 1),
            field("Heaviness", 0),
        ])
        fo, radii, live = ed.falloff_and_radii(twin)
        self.assertTrue(live)
        samples = ed.area_geometry_samples(twin, fo, radii, 300.0)
        self.assertEqual(len(samples), 4)
        # Effective endpoints are both 0, yet the branch yields expanding rings:
        # the first tick's cutoff is min(outer, effective_outer) == 0 footprint.
        self.assertEqual(samples[0][2], 0)      # zero footprint at zero cutoff
        self.assertEqual(samples[3][2], 0)

    def test_range_collapsing_after_truncation_fails_clear(self):
        import effective_damage as ed
        from miniyaml import Node
        twin = Node("Warhead@w", "AreaDamage", [
            field("Spread", 600),
            field("Falloff", "100, 37"),
            field("Range", "1023, 1024"),
            field("Heaviness", 0),
        ])
        with self.assertRaisesRegex(eh.HeavinessError,
                                    "collapsed to a positive duplicate"):
            ed.falloff_and_radii(twin)

    def test_zero_front_after_truncation_is_harmless_not_rejected(self):
        # Segment 1 is entered only when `outer > distance`; a zero front (0 == 0)
        # never satisfies that for any distance >= 0, so the authored 0/1 ->
        # scaled 0/0 collapse is harmless and MUST be preserved, not rejected.
        import effective_damage as ed
        from miniyaml import Node
        twin = Node("Warhead@w", "AreaDamage", [
            field("Spread", 600),
            field("Falloff", "100, 37"),
            field("Range", "0, 1"),
            field("Heaviness", 0),
        ])
        fo, radii, live = ed.falloff_and_radii(twin)
        self.assertEqual(radii, [0, 0])

    def test_scaled_radius_overflow_rejected_consistently(self):
        # Near Int32.MaxValue: 1_700_000_000 * 4/3 = 2_266_666_666 > Int32 max.
        with self.assertRaisesRegex(eh.HeavinessError, "overflows Int32"):
            eh.scale_length(1_700_000_000, 2000)
        # Normal magnitude: 1_500_000_000 * 4/3 = 2_000_000_000 fits.
        self.assertEqual(eh.scale_length(1_500_000_000, 2000), 2_000_000_000)
        # Lower bound, symmetric: authored NEGATIVE WDist scales MORE negative,
        # so h=2's 4/3 underflows Int32 in exactly the same way (-2_000_000_000
        # * 4/3 = -2_666_666_666 < Int32 min).
        with self.assertRaisesRegex(eh.HeavinessError, "overflows Int32"):
            eh.scale_length(-2_000_000_000, 2000)
        # Normal negative magnitude fits: -1_500_000_000 * 4/3 = -2_000_000_000.
        self.assertEqual(eh.scale_length(-1_500_000_000, 2000), -2_000_000_000)
        # Disabled keeps EVERY authored value verbatim — including negative
        # radii (legacy behavior preserved; no active-path rejection applies).
        self.assertEqual(eh.scale_length(-2_000_000_000, -1), -2_000_000_000)

    def test_single_entry_range_still_accepted(self):
        import effective_damage as ed
        from miniyaml import Node
        twin = Node("Warhead@w", "AreaDamage", [
            field("Spread", 600),
            field("Falloff", "100, 37, 14, 5, 0"),
            field("Range", "1024"),
            field("Heaviness", 0),
        ])
        fo, radii, live = ed.falloff_and_radii(twin)
        self.assertEqual(radii, [682])
        self.assertFalse(live)   # documented single-Range footgun: zero damage

    def test_tail_duplicates_after_truncation_are_preserved(self):
        # Control flow: GetDamageFalloff dynamically SKIPS duplicate segments at
        # i >= 2 (used only when distance < Range[i] while entering requires
        # distance >= Range[i-1] — impossible when equal). Only a FRONT collapse
        # divides zero, so an equal tail (authored or truncation-created) must be
        # preserved untouched, not rejected.
        import effective_damage as ed
        from miniyaml import Node
        tail_dup = Node("Warhead@w", "AreaDamage", [
            field("Spread", 600),
            field("Falloff", "100, 37, 14"),
            field("Range", "600, 1023, 1024"),
            field("Heaviness", 0),
        ])
        fo, radii, live = ed.falloff_and_radii(tail_dup)
        self.assertEqual(radii, [400, 682, 682])
        self.assertTrue(live)

    # Exact live activation closure: original pilot plus Forgotten follow-up.
    def test_resolved_inventory_has_only_the_authorized_pilot_heaviness(self):
        rs = Ruleset(ROOT)
        found = {}
        modes = {}
        for name in rs.weapons:
            resolved = rs.resolve_weapon(name)
            if resolved is None:
                continue
            for node in resolved.children:
                if not node.key.startswith("Warhead"):
                    continue
                if node.get("Heaviness") is not None:
                    found[(name, node.key)] = int(node.get("Heaviness"))
                    mode = node.get("HeavinessMode")
                    modes[(name, node.key)] = None if mode is None else mode
        from reviewed_weapon_history import current_endpoint_name
        expected = {("^Warhead_CannonAP", "Warhead@CannonAP"): 1000}
        expected.update({(current_endpoint_name(rs, name), "Warhead@CannonAP"): h for name, h in {
            "RA2sabot": 0, "RA2sabot_elite": 0, "TS90mm": 1000,
            "TS90mmDep": 1000, "corrino_buggy_gun": 0,
            "TSHighVelocity": 0, "TSHighVelocity2": 0,
            "TSHighVelocityTur": 0, "RA2120xmm": 0, "RA2120xmm_elite": 0,
            "NaxiHetzerDestroyer": 0, "NaxiHetzerDestroyer_elite": 0,
            "NaxiHetzerDestroyerCorrosion": 0, "NaxiAntiTankCannon": 0,
            "NaxiAntiTankCannon_elite": 0, "NaxiAntiTankCannonCorrosion": 0,
            "AlliedTankDestroyerCannon": 0, "SkyHawkCannon": 0, "2Inch": 0,
            "TSLaser90mm": 1000, "TSLaser90mmDep": 1000,
            "120mm_cobra": 0, "120mm_cobra_deploy": 0,
            "120mm_python": 0, "120mm_python_deploy": 0}.items()})
        self.assertEqual(found, expected)
        # The SHARED PROFILE is explicit on the live base; the enumerated live
        # consumers inherit the mode through the base's resolved merge (every
        # resolved pilot node flattens it the same way).
        expected_modes = {key: "SharedVersus" for key in expected}
        self.assertEqual(modes, expected_modes)

class SharedProfileMirrorTest(unittest.TestCase):
    """THE SHARED PROFILE (HeavinessMode SharedVersus, Aedis 2026-09-10 03:17)."""

    def flat_versus(self):
        return {"None": 20, "Flak": 35, "Plate": 40, "Medium": 38, "Shield": 25}

    def test_shield_coefficient_scales_once_half_up(self):
        self.assertEqual(eh.shield_coefficient(25, 0), 25)
        self.assertEqual(eh.shield_coefficient(25, 500), 31)     # 31.25
        self.assertEqual(eh.shield_coefficient(25, 1000), 38)    # 37.5 -> HALF-UP
        self.assertEqual(eh.shield_coefficient(25, 1500), 44)    # 43.75
        self.assertEqual(eh.shield_coefficient(25, 2000), 50)

    def test_shared_table_bells_once_and_scales_shield_once(self):
        versus = self.flat_versus()
        raw = eh.bell_transform(versus, 1.0)
        shared = eh.shared_versus_profile(versus, 1000)
        for armor, value in raw.items():
            if armor == "Shield":
                self.assertEqual(shared[armor], eh.shield_coefficient(raw[armor], 1000))
            else:
                self.assertEqual(shared[armor], value, armor)

    def test_percentage_half_reads_the_same_table(self):
        versus = self.flat_versus()
        shared = eh.shared_versus_profile(versus, 1000)
        flat = eh.versus_profile(versus, 1000)
        # Same bell result for every row; only the Shield row differs (its own
        # once scaling), which the percentage half INHERITS rather than re-scaling.
        for armor in versus:
            self.assertEqual(armor in {"Shield"} or flat[armor] == shared[armor],
                             True, armor)
        self.assertEqual(shared["Shield"], eh.shield_coefficient(flat["Shield"], 1000))

    def test_shared_mode_rejects_percentage_table(self):
        node = field("Warhead@w", "AreaDamage", [
            field("Heaviness", 1000), field("HeavinessMode", "SharedVersus"),
            field("PercentageVersus", children=[field("None", 20)]),
        ])
        with self.assertRaisesRegex(eh.HeavinessError, "rejects PercentageVersus"):
            eh.heaviness_profile_config(node, {}, {"None": 20}, {},
                                        subclass_twin=False)

    def test_shared_mode_rejects_endpoints(self):
        node = field("Warhead@w", "AreaDamage", [
            field("Heaviness", 1000), field("HeavinessMode", "SharedVersus"),
        ])
        with self.assertRaisesRegex(eh.HeavinessError, "rejects PercentageVersus"):
            eh.heaviness_profile_config(node, LIGHT, {}, HEAVY)

    def test_shared_mode_requires_active_heaviness(self):
        node = field("Warhead@w", "AreaDamage", [field("HeavinessMode", "SharedVersus")])
        with self.assertRaisesRegex(eh.HeavinessError, "requires an active Heaviness"):
            eh.heaviness_profile_config(node, {}, {}, {})

    def test_shared_mode_rejected_on_the_subclass(self):
        node = field("Warhead@w", "AreaDamagePercentage", [
            field("Heaviness", 1000), field("HeavinessMode", "SharedVersus"),
        ])
        with self.assertRaisesRegex(eh.HeavinessError, "does not support the SharedVersus"):
            eh.heaviness_profile_config(node, {}, {}, {}, subclass_twin=True)

    def test_unknown_mode_value_rejected(self):
        node = field("Warhead@w", "AreaDamage", [field("HeavinessMode", "NotAMode")])
        with self.assertRaisesRegex(eh.HeavinessError, "Unknown HeavinessMode"):
            eh.heaviness_profile_config(node, {}, {}, {})

    def test_numeric_mode_values(self):
        # Review item 1: FieldLoader/Enum parsing besieges numeric members, so
        # the DEFINED indices are accepted by name-equivalent and an UNDEFINED
        # numeric member must fail clear exactly like the C# IsDefined gate.
        self.assertEqual(eh.heaviness_mode_of(field(
            "W", "AreaDamage", [field("HeavinessMode", 0)])), eh.MODE_LEGACY)
        self.assertEqual(eh.heaviness_mode_of(field(
            "W", "AreaDamage", [field("HeavinessMode", 1)])), eh.MODE_SHARED)
        with self.assertRaisesRegex(eh.HeavinessError, "numeric value outside"):
            eh.heaviness_mode_of(field("W", "AreaDamage", [field("HeavinessMode", 7)]))

    def test_omitted_mode_defaults_to_legacy(self):
        self.assertEqual(eh.heaviness_mode_of(field("W", "AreaDamage")), eh.MODE_LEGACY)

    def test_shared_folded_units_combined_fraction_half_up(self):
        # ONE rounding of the combined fraction; h = 0 -> 0 exactly.
        self.assertEqual(pd.shared_folded_units(2000, 2000, 0), (0.0, 0))
        continuous, rounded = pd.shared_folded_units(100, 2000, 2000)
        self.assertEqual(rounded, 1)                  # 100 x 2000 x 2 / 4e8 = 1.0
        self.assertEqual(continuous, 1.0)
        self.assertEqual(pd.shared_folded_units(100, 2000, 1000)[1], 1)   # 0.5 -> half-UP
        self.assertEqual(pd.shared_folded_units(100, 2000, 500)[1], 0)    # 0.25 -> 0
        self.assertEqual(pd.shared_folded_units(6000, 2500, 1000)[1], 38) # 37.5 -> half-UP

    def test_shared_folded_units_large_values(self):
        # 160000 x 8000 x 1000 / 4e8 = 3200 — RA2sabot_elite scale.
        self.assertEqual(pd.shared_folded_units(160000, 8000, 1000)[1], 3200)
        self.assertEqual(pd.shared_folded_units(160000, 8000, 2000)[1], 6400)

    # --- review follow-up items 2–4: nonnegative contract + load-time gates ---
    def test_shared_numeric_negative_inputs_rejected_even_at_h0(self):
        versus = self.flat_versus()
        for kwargs in ({"damage": -1}, {"scale": -1}):
            with self.subTest(**kwargs):
                with self.assertRaisesRegex(eh.HeavinessError, "rejects a negative"):
                    eh.validate_shared_numeric(eh.MODE_SHARED, 0, versus, **kwargs)
        # ... and the negative Shield row specifically:
        with self.assertRaisesRegex(eh.HeavinessError, "negative Shield coefficient"):
            eh.validate_shared_numeric(
                eh.MODE_SHARED, 0, {**versus, "Shield": -25}, 6000, 2000)

    def test_shared_numeric_overflow_fails_at_load(self):
        with self.assertRaisesRegex(OverflowError, "exceed Int32"):
            eh.validate_shared_numeric(
                eh.MODE_SHARED, 2000, self.flat_versus(),
                2000000000, 2000000000)
        # The helper and runtime helper agree at that bound.
        with self.assertRaises(OverflowError):
            pd.shared_folded_units(2000000000, 2000000000, 2000)

    def test_shared_numeric_gate_does_not_touch_legacy(self):
        # Legacy healing/zero-damage behavior is NEVER gated by the shared
        # nonnegative contract.
        eh.validate_shared_numeric(eh.MODE_LEGACY, eh.DISABLED,
                                   {"Shield": -25}, -6000, 10000)
        eh.validate_shared_numeric(eh.MODE_SHARED, 2000, self.flat_versus(),
                                   0, 0)  # zero damage/scale is legal


if __name__ == "__main__":
    unittest.main()
