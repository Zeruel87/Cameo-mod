"""ONE map from unit template to balance class — and the three that disagreed before it.

PRIOR ART: `test_audit_class_templates.py` covers the structural "exactly one `Inherits@Template:`"
audit; `test_audit_infantry_class_bands.py` covers the §6b range bands. Neither touches the
template→class map. `test_class_anchor_merge.py` covers ledger merge behaviour for the tag, not
where the tag comes from.

⛔ PRIORITY 0 item 1. `anchor_readiness.py` reported 336 of 1870 buildable units tagged (18%) and
fitted every anchor against that 18%. The class was always derivable from `design.subtype`; three
incomplete, mutually disagreeing copies of the map were the reason it was not.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import class_membership as cm  # noqa: E402


class TheMapIsCompleteAndCorrectTest(unittest.TestCase):
    def test_every_class_it_names_exists_in_class_anchors(self):
        """⛔ A map entry pointing at a class that does not exist silently drops those units out
        of every fit. Checked against the real file, not a copy of its key list."""
        import json
        anchors = json.loads((ROOT / "docs" / "balance" / "class_anchors.json")
                             .read_text(encoding="utf-8"))
        known = {k for k in anchors if not k.startswith("_")}
        unknown = {v for v in cm.SUBTYPE_TO_CLASS.values()} - known
        self.assertEqual(unknown, set(), f"classes not in class_anchors.json: {unknown}")

    def test_line_breaker_is_its_own_class_not_mbt(self):
        """⛔ THE LIVE BUG ALL THREE OLD COPIES CARRIED. `linebreaker -> mbt` folded 40
        line-breakers into the MBT population in the workbook and the range tool, while
        `line_breaker` is one of the 27 classes and the ledger tags 30 of its 31 members with
        it."""
        self.assertEqual(cm.subtype_to_anchor("LineBreaker"), "line_breaker")

    def test_it_knows_the_ground_vehicle_classes_the_5_entry_copies_did_not(self):
        """The two 5-entry copies knew only scout/closecombat/special_forces/mbt/linebreaker —
        no vehicle class at all, though the hand tags map thirteen of them one-to-one."""
        for subtype, cls in (("Artillery", "artillery"), ("HighTechTank", "high_tech_tank"),
                             ("EpicVehicle", "epic_vehicle"), ("LightTank", "light_tank"),
                             ("ArtilleryTank", "artillery_tank"),
                             ("MissileVehicle", "missile_vehicle"),
                             ("AntiAirVehicle", "anti_air_vehicle"),
                             ("TankDestroyer", "tank_destroyer"),
                             ("Dreadnought", "dreadnought"), ("ScoutVehicle", "scout_vehicle"),
                             ("FireSupport", "fire_support")):
            self.assertEqual(cm.subtype_to_anchor(subtype), cls, subtype)

    def test_it_fills_the_five_classes_that_had_zero_members(self):
        """`anchor_readiness` reported commando, flying_infantry, grenadier, mortar and
        pure_sniper with ZERO tagged members — three of them SIGNED, i.e. signed off against
        nothing. Each has a template; only the map was missing."""
        for subtype, cls in (("HeroInfantry", "commando"), ("FlyingInfantry", "flying_infantry"),
                             ("GrenadierInfantry", "grenadier"), ("MortarInfantry", "mortar"),
                             ("SniperInfantry", "pure_sniper")):
            self.assertEqual(cm.subtype_to_anchor(subtype), cls, subtype)

    def test_normalisation_is_case_and_separator_insensitive(self):
        for spelling in ("MainBattleTank", "mainbattletank", "Main_Battle_Tank", "MAIN-BATTLE-TANK"):
            self.assertEqual(cm.subtype_to_anchor(spelling), "mbt", spelling)

    def test_unknown_and_empty_return_None_rather_than_a_guess(self):
        for value in (None, "", "NoSuchTemplate"):
            self.assertIsNone(cm.subtype_to_anchor(value))


class GenericSubtypesAreDefectsNotClassesTest(unittest.TestCase):
    """⛔ `Infantry`, `Vehicle`, `Aircraft`, `Ship`, `Misc` are `SECTION_DEFAULT_SUBTYPE` — what an
    actor gets when it inherits NO role template. Mapping them to a class would launder PRIORITY 0
    item 2 into a fake tag, and the 114 units concerned would stop being visible as defects."""

    def test_they_are_never_mapped_to_a_class(self):
        for subtype in ("Infantry", "Vehicle", "Aircraft", "Ship", "Misc", "Unclassified"):
            self.assertIsNone(cm.subtype_to_anchor(subtype), subtype)

    def test_they_report_as_no_template_not_as_unmapped(self):
        """The three reasons a class comes back None are DIFFERENT problems and must not be
        collapsed: no template at all, no class exists for the template, or not a unit."""
        self.assertEqual(cm.classify({"subtype": "Vehicle"}), (None, "no-template"))
        self.assertEqual(cm.classify({"subtype": "Helicopter"}), (None, "no-class-exists"))
        self.assertEqual(cm.classify({"subtype": "Building"}), (None, "not-a-unit"))

    def test_air_and_naval_have_no_class_to_map_to(self):
        """`class_anchors.json` holds 27 classes and not one is an air or naval class. That is a
        DESIGN gap needing a ruling — inventing a mapping here would hide it."""
        import json
        anchors = json.loads((ROOT / "docs" / "balance" / "class_anchors.json")
                             .read_text(encoding="utf-8"))
        known = {k for k in anchors if not k.startswith("_")}
        for word in ("air", "aircraft", "helicopter", "naval", "ship", "bomber", "fighter"):
            self.assertNotIn(word, known, f"an {word} class now exists — map it and drop this")
        for subtype in ("Helicopter", "Bomber", "Fighter", "ScoutShip", "BattleShip", "Harvester"):
            self.assertIn(cm._norm(subtype), cm.NEEDS_A_NEW_CLASS, subtype)


class ExplicitTagStillWinsTest(unittest.TestCase):
    def test_a_maintainer_override_survives_re_derivation(self):
        """The hand tag is the drifted copy, and it STILL wins: an override a person set must not
        be silently overwritten by a derivation. Disagreements are reported instead."""
        self.assertEqual(
            cm.classify({"class_anchor": "support", "subtype": "ScoutInfantry"}),
            ("support", "explicit"))

    def test_derivation_only_fills_what_the_tag_left_empty(self):
        self.assertEqual(cm.classify({"subtype": "ScoutInfantry"}), ("scout", "derived"))


class ConsumersUseTheSharedMapTest(unittest.TestCase):
    def test_the_three_old_copies_now_delegate(self):
        """Three copies that can drift apart is what produced the `linebreaker -> mbt` bug in all
        three at once and the missing vehicle classes in two. They must not be re-forked."""
        for name in ("build_workbook", "update_ranges", "propose_class_rebalance"):
            src = (ROOT / "tools" / "balance" / f"{name}.py").read_text(encoding="utf-8")
            self.assertIn("import class_membership", src, name)
            self.assertIn("return class_membership.subtype_to_anchor(st)", src, name)

    def test_anchor_readiness_no_longer_reads_the_raw_tag(self):
        """⛔ THE 18% WAS A PROPERTY OF THE READER. `anchor_readiness` read
        `design.class_anchor` raw while the template was sitting in the same row."""
        src = (ROOT / "tools" / "balance" / "anchor_readiness.py").read_text(encoding="utf-8")
        self.assertIn("class_membership.classify", src)
        offenders = [ln for ln in src.splitlines()
                     if 'get("class_anchor")' in ln or '["class_anchor"]' in ln]
        self.assertEqual(offenders, [], f"raw class_anchor reads remain: {offenders}")


if __name__ == "__main__":
    unittest.main()


class StatIdenticalVariantsFoldTest(unittest.TestCase):
    """⛔ A variant that overrides NO balance trait cannot differ from its parent, so counting it
    separately inflates the class population and every fit denominator built on it.
    Maintainer 2026-09-03: *"since they just inherited the main variant it doesn't make sense to
    give them different stats"*."""

    def test_the_eight_measured_duplicates_fold(self):
        for variant, parent in (("ts_gdi_engineer", "TSENGINEER"),
                                ("ts_nod_engineer", "TSENGINEER"),
                                ("forgotten_engineer", "TSENGINEER"),
                                ("wc2_humans_elvenranger", "wc2_humans_elvenarcher"),
                                ("wc2_orcs_trollberserker", "wc2_orcs_trollaxethrower")):
            self.assertEqual(cm.fold(variant), parent, variant)
            self.assertTrue(cm.is_folded(variant), variant)

    def test_a_variant_that_overrides_a_stat_does_NOT_fold(self):
        """⚠ 37 of the 45 variants DO override a balance trait and stay distinct — the split is
        the whole point. `ts_nod_lightinfantry` overrides Armament; `forgotten_mutantsniper`
        overrides Armament, Health, Mobile and Valued."""
        for keep in ("ts_nod_lightinfantry", "forgotten_mutantsniper",
                     "asianalliance_heavyrailguntank", "ra2_allies_ifv_missile"):
            self.assertFalse(cm.is_folded(keep), keep)
            self.assertEqual(cm.fold(keep), keep, keep)

    def test_an_ordinary_actor_folds_to_itself(self):
        self.assertEqual(cm.fold("ra2_soviets_rhinoheavytank"), "ra2_soviets_rhinoheavytank")

    def test_folding_is_a_counting_rule_and_never_a_deletion(self):
        """The actors stay in the game and in the ledger. If a fold target ever stopped existing
        the map would be pointing at nothing, so every parent must be a real actor id."""
        for parent in set(cm.FOLD_INTO_PARENT.values()):
            self.assertNotIn(parent, cm.FOLD_INTO_PARENT,
                             f"{parent} is both a fold target and folded — a chain, not a map")
