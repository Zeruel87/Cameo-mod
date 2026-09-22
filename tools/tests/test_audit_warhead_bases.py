"""Focused synthetic fixtures for the NEW level-less warhead-base audit path.

    tools/audit/audit_family_uniqueness.py    — resolved reader, base/legacy census,
                                                RAW Shield duplicate groups, and the
                                                distinct-NEW-family Shield failure
    tools/audit/audit_versus_profile.py       — the base's mean/band/direction inclusion
    tools/audit/audit_heaviness_bell.py       — ACTUAL-base selection vs the explicit
                                                legacy-first-level diagnostic label

Background (Aedis 2026-09-10 02:10, the coexistence approval): the generator is activating
ONE level-less `^Warhead_CannonAP` base with `Heaviness: 1000`. Legacy level templates
temporarily coexist, so the base's Shield DUPLICATES its own family's Medium Shield by
design — that duplicate must stay VISIBLE in the raw groups, while a Shield shared by two
DISTINCT families must FAIL. Everything here is synthetic: no yaml, no repo corpus.
"""

from __future__ import annotations

import unittest
from unittest import mock

import _bootstrap  # noqa: F401 — sys.path side effect

from miniyaml import Node
import audit_family_uniqueness as fam
import audit_heaviness_bell as bell
import audit_versus_profile as vp


def node(key, value="", children=None):
    return Node(key, value, children or [], "<fixture>", 1)


def warhead(name, spread=100, falloff="100, 0", shield=120, heaviness=None,
            percentage_twin=False):
    """A main-warhead node the way a resolved template carries it."""
    wh = node(f"Warhead@{name}", "AreaDamage", [
        node("Spread", str(spread)),
        node("Damage", "2000"),
        node("Falloff", falloff),
        node("Versus", "", [node("Shield", str(shield)), node("Medium", "100")]),
    ])
    if heaviness is not None:
        wh.children.append(node("Heaviness", str(heaviness)))
    if percentage_twin:
        wh.children.append(node("Warhead@" + name + "_Percentage", "AreaDamage", [
            node("Spread", str(spread // 2)),
            node("Falloff", falloff),
            node("Versus", "", [node("Shield", "1"), node("Medium", "2")]),
        ]))
    return wh


def template(name, wh):
    return node(name, "", [node("ValidTargets", "Ground"), wh])


class FakeRuleset:
    def __init__(self, nodes):
        self.weapons = {n.key: n for n in nodes}
        self._by_name = {n.key: n for n in nodes}

    def resolve_weapon(self, name):
        return self._by_name.get(name)


def levelled(family, level, spread=100, shield=120, falloff="100, 0"):
    return template(f"^Warhead_{family}_{level}",
                    warhead(f"{family}_{level}", spread, falloff, shield))


def base(family, spread=120, shield=144, heaviness=1000, falloff="100, 0"):
    return template(f"^Warhead_{family}",
                    warhead(family, spread, falloff, shield, heaviness))


class SplitName(unittest.TestCase):
    def test_a_legacy_level_template_parses(self):
        self.assertEqual(fam.split_name("CannonAP_Light"), ("CannonAP", "Light"))

    def test_a_level_less_base_parses_to_family_no_level(self):
        self.assertEqual(fam.split_name("CannonAP"), ("CannonAP", None))

    def test_a_levelled_variant_is_excluded_like_the_old_variant_re(self):
        # ^Warhead_Demolition_Heavy_D2K_Orni and friends: one-offs, not a family census row.
        self.assertIsNone(fam.split_name("Demolition_Heavy_D2K_Orni"))
        self.assertIsNone(vp.split_name("CannonAP_Light_D2K_Orni"))
        self.assertIsNone(bell.split_name("Foo_Trace_Bar"))

    def test_trace_is_included_in_the_legacy_family_census(self):
        self.assertEqual(fam.split_name("Chemical_Trace"), ("Chemical", "Trace"))

    def test_the_versus_audit_still_skips_trace_like_before(self):
        # vp.LEVELS keeps the audit's own four-level census (Light..Super).
        self.assertIsNone(vp.split_name("Chemical_Trace"))


class CensusCounts(unittest.TestCase):
    def rs(self, nodes):
        return FakeRuleset(nodes)

    def test_base_and_legacy_counts_are_reported_separately_and_in_total(self):
        nodes = [levelled("CannonAP", l) for l in ("Light", "Medium", "Heavy", "Super")]
        nodes.append(base("CannonAP"))
        lev, bases, shields = fam.read_census(self.rs(nodes))
        self.assertEqual(len(lev), 4)
        self.assertEqual(list(bases), ["CannonAP"])
        self.assertEqual(len(lev) + len(bases), 5)

    def test_a_disabled_sentinel_base_is_not_active(self):
        legacy, bases, _shields = fam.read_census(self.rs([base("CannonAP", heaviness=-1)]))
        self.assertEqual(bases, {})
        self.assertEqual(legacy, {})
        # but a carried Shield row stays in the raw census — visibility is not activation
        _legacy, _bases, shields = fam.read_census(self.rs([base("CannonAP", heaviness=-1, shield=7)]))
        self.assertEqual(shields.get(("CannonAP", "^Warhead_CannonAP")), 7)

    def test_a_base_without_a_shape_still_participates_in_shield_uniqueness(self):
        t = template("^Warhead_CannonAP", node("Warhead@CannonAP", "AreaDamage",
                                               [node("Heaviness", "1000"),
                                                node("Versus", "", [node("Shield", "144")])]))
        legacy, bases, shields = fam.read_census(self.rs([t, base("Bullet")]))
        self.assertEqual(legacy, {})
        self.assertEqual(bases["CannonAP"], (None, None, 144))
        self.assertEqual(len(fam.shield_conflicts(shields, frozenset(bases))), 1)

    def test_heaviness_is_parsed_and_screened(self):
        self.assertEqual(fam.heaviness_of(warhead("X", heaviness=1000)), 1000.0)
        self.assertIsNone(fam.heaviness_of(warhead("X")))
        for bad in ("abc", "NaN", "Inf", "1.5", "-2", "2001", "2147483648"):
            for reader in (fam.heaviness_of, bell.heaviness_of, vp.heaviness_active):
                with self.subTest(value=bad, reader=reader.__module__):
                    with self.assertRaises(ValueError):
                        reader(warhead("X", heaviness=bad))
        self.assertIsNone(bell.heaviness_of(node("Spread", "80")))


class RawShieldDuplicateReporting(unittest.TestCase):
    def same_family_census(self):
        # The approved compatibility preview: the base borrows its own Medium Shield.
        shields = {("CannonAP", "^Warhead_CannonAP"): 144.0,
                   ("CannonAP", "^Warhead_CannonAP_Medium"): 144.0,
                   ("Bullet", "^Warhead_Bullet_Medium"): 128.0}
        return shields

    def test_the_approved_base_medium_pair_stays_visible_in_the_raw_groups(self):
        raw = fam.raw_shield_groups(self.same_family_census())
        self.assertEqual(raw, {144.0: ["CannonAP (^Warhead_CannonAP)",
                                       "CannonAP (^Warhead_CannonAP_Medium)"]})

    def test_same_family_pairs_never_fail_uniqueness(self):
        self.assertEqual(fam.shield_conflicts(self.same_family_census()), [])

    def test_two_distinct_new_families_sharing_a_shield_are_a_conflict(self):
        shields = {("CannonAP", "^Warhead_CannonAP"): 144.0,
                   ("Bullet", "^Warhead_Bullet"): 144.0}
        value, members = fam.shield_conflicts(
            shields, frozenset({"CannonAP", "Bullet"}))[0]
        self.assertEqual(value, 144.0)
        self.assertEqual(len(members), 2)

    def test_a_base_joining_a_distinct_legacy_shield_is_raw_only(self):
        shields = {("CannonAP", "^Warhead_CannonAP"): 144.0,
                   ("CannonAP", "^Warhead_CannonAP_Medium"): 144.0,
                   ("Bullet", "^Warhead_Bullet_Medium"): 144.0}
        self.assertEqual(fam.shield_conflicts(shields, frozenset({"CannonAP"})), [])
        self.assertEqual(len(fam.raw_shield_groups(shields)[144.0]), 3)

    def test_a_legacy_only_shield_duplicate_is_visible_but_not_this_check_s_failure(self):
        # Pre-existing tree state: MissileThermobaric_Light / Nuclear_Super both sit on 155
        # (found live 2026-09-10). No base is involved, so it stays a RAW report only.
        shields = {("MissileThermobaric", "^Warhead_MissileThermobaric_Light"): 155.0,
                   ("Nuclear", "^Warhead_Nuclear_Super"): 155.0}
        self.assertEqual(fam.shield_conflicts(shields, frozenset()), [])
        self.assertEqual(len(fam.raw_shield_groups(shields)), 1)


class MainVerdicts(unittest.TestCase):
    """main() with an injected census — the collision-failure paths, ratchets intact."""

    def run_main(self, census):
        with mock.patch.object(fam, "read_census", return_value=census):
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = fam.main()
        return code, buf.getvalue()

    def test_distinct_new_families_sharing_a_shield_fail(self):
        census = ({("CannonAP", "Medium"): (120, "100,0")},
                  {"CannonAP": (120, "100,0", 144.0),
                   "Sonic": (120, "100,0", 144.0)},
                  {("CannonAP", "^Warhead_CannonAP"): 144.0,
                   ("CannonAP", "^Warhead_CannonAP_Medium"): 144.0,
                   ("Sonic", "^Warhead_Sonic"): 144.0})
        code, out = self.run_main(census)
        self.assertEqual(code, 1)
        self.assertIn("Shield-uniqueness violation", out)

    def test_the_approved_same_family_duplicate_is_visible_but_not_failing(self):
        census = ({("CannonAP", "Medium"): (120, "100,0")},
                  {"CannonAP": (120, "100,0", 144.0)},
                  {("CannonAP", "^Warhead_CannonAP"): 144.0,
                   ("CannonAP", "^Warhead_CannonAP_Medium"): 144.0})
        code, out = self.run_main(census)
        self.assertEqual(code, 0)
        self.assertIn("RAW Shield duplicate groups", out)
        self.assertIn("CannonAP (^Warhead_CannonAP_Medium)", out)

    def test_a_base_bucket_shape_collision_between_distinct_families_fails(self):
        census = ({},
                  {"CannonAP": (120, "100,0", 144.0),
                   "Bullet": (120, "100,0", 130.0)},
                  {("CannonAP", "^Warhead_CannonAP"): 144.0,
                   ("Bullet", "^Warhead_Bullet"): 130.0})
        code, out = self.run_main(census)
        self.assertEqual(code, 1)
        self.assertIn("BASE COLLISION", out)

    def test_legacy_shape_collisions_still_fail(self):
        census = ({("CannonAP", "Medium"): (120, "100,0"),
                   ("Bullet", "Medium"): (120, "100,0")},
                  {},
                  {})
        code, _out = self.run_main(census)
        self.assertEqual(code, 1)


class VersusIncludesTheBase(unittest.TestCase):
    def profiles_with(self, nodes):
        with mock.patch.object(vp, "Ruleset", lambda root: FakeRuleset(nodes)):
            return vp.profiles()

    def test_an_active_base_enters_the_profile_map_as_Base(self):
        nodes = [base("CannonAP", heaviness=1000), levelled("CannonAP", "Medium")]
        data = self.profiles_with(nodes)
        self.assertIn(("CannonAP", vp.BASE_KEY), data)
        self.assertIn(("CannonAP", "Medium"), data)

    def test_a_disabled_sentinel_base_does_not_enter_the_map(self):
        data = self.profiles_with([base("CannonAP", heaviness=-1)])
        self.assertNotIn(("CannonAP", vp.BASE_KEY), data)

    def test_legacy_census_is_untouched(self):
        data = self.profiles_with([levelled("CannonAP", "Light"),
                                   levelled("CannonAP", "Medium")])
        self.assertEqual(sorted(k[1] for k in data), ["Light", "Medium"])
        self.assertEqual({k[1] for k in data}, {"Light", "Medium"})

    def test_the_percentage_twin_is_never_read_as_the_main(self):
        t = template("^Warhead_Bullet_Light",
                     warhead("Bullet_Light", 100, "100, 0", 120, percentage_twin=True))
        data = self.profiles_with([t])
        # the main must win — the twin carries Shield 1
        self.assertEqual(data[("Bullet", "Light")]["Shield"], 120)


class BellActualBaseSelection(unittest.TestCase):
    def sources_with(self, nodes):
        with mock.patch.object(bell, "Ruleset", lambda root: FakeRuleset(nodes)):
            return bell.profiles()

    def test_a_family_with_an_active_base_uses_the_actual_base(self):
        nodes = [base("CannonAP", heaviness=1000, shield=144),
                 levelled("CannonAP", "Heavy"), levelled("CannonAP", "Light")]
        got = self.sources_with(nodes)
        self.assertIn("CannonAP", got)
        profile, tag, name, h = got["CannonAP"]
        self.assertEqual(tag, "base")
        self.assertEqual(name, "^Warhead_CannonAP")
        self.assertEqual(h, 1000.0)
        # Also proves the base is chosen even though the legacy Heavy sorts first.

    def test_a_family_without_a_base_is_an_explicit_legacy_diagnostic(self):
        nodes = [levelled("Bullet", "Heavy"), levelled("Bullet", "Light")]
        profile, tag, name, h = self.sources_with(nodes)["Bullet"]
        self.assertEqual(tag, "legacy")
        self.assertEqual(name, "^Warhead_Bullet_Heavy")   # legacy first-pick preserved
        self.assertIsNone(h)

    def test_legacy_census_still_wins_for_empty_versus_mains(self):
        t = template("^Warhead_Bullet_Heavy", warhead("Bullet_Heavy", 100, "100, 0", 0))
        data = self.sources_with([t])
        self.assertEqual(data["Bullet"][1], "legacy")


if __name__ == "__main__":
    unittest.main()
