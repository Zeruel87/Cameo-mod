import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/pinned_role_profile_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_pinned_role_profiles as cohort
import consolidate_explicit_family_state_profiles as explicit
from audit_three_way_split import RAW_SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset
from owned_weapon_history import historical_weapon_names


ACCEPTED = {
    "blast_shape": (12, "d2dda768c5a81a1a49d53c55c14603d35bd9b02deaa969a37d2852688074f951"),
    "percentage_damage": (11, "320b7fcd938fbccb7f4b978293b6128e8b7c3f2167f4cd48ef97bd76b8beb262"),
}

STATE_DEFERRED = {
    "AsianChemicalBombs", "TSSAPCCoreMissiles", "PhobosLaser",
    "ra1_soviets_migattackbomber_thermobaricmaverick", "d2kCarryallChainGun_upgrade",
    "d2kChainGun_upgrade", "ra1_soviets_rifleinfantry_carbine_incendiary",
    "IncendiaryM1Carbine", "LMG_ordos_upgrade", "SteelFighterRailgun",
}


def members():
    """The pinned cohort: every root plus its recorded closure members.

    Membership is pinned by name rather than re-derived from live inherits: the
    W7 held-ExtraDamage materialization (450dcea59) flattened
    CannonAttackRobotGun_elite into a standalone weapon, so it remains a cohort
    member but is no longer a live descendant of its root.
    """
    selected = {}
    for root, (destination, expected, total, scale) in cohort.ROOTS.items():
        for name in {root, *expected}:
            selected[name] = (destination, total, scale)
    return selected


# Live descendant closures after the W7 flatten — everything else is unchanged.
CURRENT_CLOSURES = {
    "CannonAttackRobotGun": set(),
    "RA2GrenadePack": {"RA2GrenadePack_elite"},
    "SteelDaggerCannon": {"SteelDaggerCannon_elite"},
    "LatinSmokerCannon": {"LatinSmokerCannon_elite"},
    "RA2LarsRocket": set(),
    "td_nod_specterartillery_specterartilleryshellupgrade": set(),
    "LatinAADefenderCannon": set(),
    "WyvernRockets": set(),
}


def destination_key(destination):
    """R12 retired the pre-rename compatibility payload names for *_Flat; the
    Concussion_Light root consolidated onto the family main itself."""
    return "Concussion_Light" if destination == "Concussion_Light" else f"{destination}_Flat"


# The W7 ExtraDamage fold raised this member's consolidated flat Damage.
APPLIED_TOTALS = {"CannonAttackRobotGun_elite": 9000}


class PinnedRoleProfileConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_converter_is_applied_and_closures_are_exact(self):
        # The frozen converter still fails closed on the live tree — the failure
        # point moved from the preserved-hash pin to closure selection after W7
        # flattened CannonAttackRobotGun_elite into a standalone weapon and R12
        # retired the compatibility payload names it looks for.
        with self.assertRaises(RuntimeError):
            cohort.inspect(self.rules)
        self.assertEqual(12, len(members()))
        for root, expected in CURRENT_CLOSURES.items():
            self.assertEqual(expected, cohort.descendants(self.rules, root), root)

    def test_each_member_has_one_pinned_destination_main(self):
        for name, (destination, total, scale) in members().items():
            key = destination_key(destination)
            resolved = self.rules.resolve_weapon(name)
            self.assertEqual([key], main_warheads(resolved), name)
            node = next(child for child in resolved.children
                        if child.key == f"Warhead@{key}")
            self.assertEqual(APPLIED_TOTALS.get(name, total), int(str(node.get("Damage"))), name)
            self.assertEqual(scale, int(str(node.get("PercentageScale"))), name)

    def test_full_ruleset_comparison_matches_reviewed_manifest(self):
        self.assertEqual(historical_weapon_names(members()), set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (count, expected_hash) in ACCEPTED.items():
            payload = json.dumps(
                self.by_kind[kind], sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(count, len(self.by_kind[kind]), kind)
            self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest(), kind)

    def test_percentage_deltas_are_only_bounded_plus_one_rounding(self):
        self.assertEqual(set(members()) - {"td_nod_specterartillery_specterartilleryshellupgrade"},
                         set(self.by_kind["percentage_damage"]))
        for name, groups in self.by_kind["percentage_damage"].items():
            rows = [row for group in groups for row in group]
            self.assertTrue(rows, name)
            for _health, before, after in rows:
                self.assertEqual(1, after - before, name)

    def test_state_carrying_candidates_are_now_explicitly_reviewed(self):
        for name in STATE_DEFERRED:
            self.assertIn(name, explicit.SPECS)
            self.assertEqual(1, len(main_warheads(self.rules.resolve_weapon(name))), name)

    def test_ratchets_match_reduction(self):
        # Upstream retired exemptions: enforce the raw ceiling, never subtract reviewed stacks.
        self.assertLessEqual(RAW_SPLIT_BASELINE, 322)
        self.assertLessEqual(BROADCAST_BASELINE, 69)


if __name__ == "__main__":
    unittest.main()
