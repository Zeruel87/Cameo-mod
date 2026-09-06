"""Regression checks for the explicit full-family state-expansion cohort."""

from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/explicit_family_state_profile_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_explicit_family_state_profiles as cohort
from audit_three_way_split import SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (18, "e1a30d446193241d0e4018ad3630fb086ca38a085864724dc60125046b2e7f2f"),
    "percentage_damage": (7, "3fe1cf69397e7a6b119d2c35f273b9211f968c587562c7179f947fc69aef6ce1"),
    "physical_state_bindings": (17, "7b3764b66633ccbfdbc95a0b8ed66adbd885112c672d9f8c1c3d373539bfc299"),
}

EXPECTED_EXPANSION = {
    "ConscriptMolotovExplode": (4000, 8000, 200, 400),
    "GrenadeRAExplode": (4000, 8000, 200, 400),
    "IncendiaryM1Carbine": (2000, 4000, 100, 200),
    "ra1_soviets_rifleinfantry_carbine_incendiary": (2000, 4000, 100, 200),
    "HeavyPlasmaFlamer": (2000, 4000, 100, 200),
    "OIPlasmaFlamer": (2000, 4000, 100, 200),
    "PhobosLaser": (42000, 48000, 0, 300),
    "d2kCarryallChainGun_upgrade": (2000, 6000, 100, 300),
    "d2kChainGun_upgrade": (4000, 8000, 200, 400),
    "LMG_ordos_upgrade": (2000, 6000, 100, 300),
    "light_inf_lmg_ordos_upgrade": (2000, 6000, 100, 300),
    "SteelFighterRailgun": (4000, 10000, 0, 300),
    "ThermobaricMaverick": (36000, 48000, 0, 600),
    "AsianChemicalBombs": (2000, 4000, 100, 200),
    "TSSAPCCoreMissiles": (8000, 24000, 400, 400),
    "FutureMechPlasma": (20000, 30000, 0, 500),
    "BuggyPlasmaGrenade": (40000, 60000, 0, 1000),
    "PositronGrenade": (32000, 40000, 0, 100),
}


class ExplicitFamilyStateProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_converter_is_fully_applied_and_fail_closed(self):
        self.assertTrue(cohort.inspect(self.rules))
        self.assertEqual(EXPECTED_EXPANSION, cohort.STATE_EXPANSION)

    def test_report_covers_exactly_the_selected_definitions(self):
        self.assertEqual(set(cohort.SPECS), set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])

    def test_only_reviewed_state_percentage_and_shape_changes_occur(self):
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (count, expected_hash) in ACCEPTED.items():
            payload = json.dumps(
                self.by_kind[kind], sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(count, len(self.by_kind[kind]), kind)
            self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest(), kind)

    def test_percentage_delta_is_bounded_to_one_hp(self):
        deltas = []
        for changes in self.by_kind["percentage_damage"].values():
            for mismatch_rows in changes:
                deltas.extend(abs(before - after)
                              for _hp, before, after in mismatch_rows)
        self.assertEqual(1, max(deltas))

    def test_each_selected_definition_has_one_pinned_destination(self):
        for name, (destination, total, scale) in cohort.SPECS.items():
            resolved = self.rules.resolve_weapon(name)
            mains = set(main_warheads(resolved))
            compatibility = f"{destination}FlatCompatibility"
            self.assertEqual({compatibility}, mains, name)
            node = cohort.flat_main_nodes(resolved, mains)[compatibility]
            self.assertEqual(str(total), str(node.get("Damage")), name)
            self.assertEqual(str(scale), str(node.get("PercentageScale")), name)

    def test_unsafe_routes_and_user_deferred_weapons_remain_stacked(self):
        deferred_stacks = {
            "PositronBounce1", "PositronBounce2",
        }
        for name in deferred_stacks:
            self.assertGreater(len(main_warheads(self.rules.resolve_weapon(name))), 1, name)
        untouched = {"HMGo", "HMGstealth", "GDISniperRifle", "Dragunov"}
        self.assertTrue(untouched.isdisjoint(self.report["changed"]))

    def test_pinned_descendant_is_exact(self):
        for name, expected in cohort.PINNED_HASHES.items():
            self.assertEqual(expected, cohort.full_hash(self.rules, name), name)

    def test_positron_cannon_parent_is_not_inherited_twice(self):
        root_parents = {parent for _key, parent in
                        self.rules.inherits_of(self.rules.weapon("PositronGrenade"))}
        self.assertNotIn("^Warhead_CannonHE_Medium", root_parents)
        for name in ("PositronBounce1", "PositronBounce2"):
            child_parents = {parent for _key, parent in
                             self.rules.inherits_of(self.rules.weapon(name))}
            self.assertIn("^Warhead_CannonHE_Medium", child_parents, name)

    def test_ratchets_match_the_live_reduction(self):
        self.assertEqual(114, SPLIT_BASELINE)
        self.assertEqual(90, BROADCAST_BASELINE)


if __name__ == "__main__":
    unittest.main()
