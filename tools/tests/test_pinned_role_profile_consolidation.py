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
from reviewed_weapon_history import HistoricalView


ACCEPTED = {
    "blast_shape": (12, "d2dda768c5a81a1a49d53c55c14603d35bd9b02deaa969a37d2852688074f951"),
    "percentage_damage": (11, "320b7fcd938fbccb7f4b978293b6128e8b7c3f2167f4cd48ef97bd76b8beb262"),
}

STATE_DEFERRED = {
    "AsianChemicalBombs", "TSSAPCCoreMissiles", "PhobosLaser",
    "ThermobaricMaverick", "d2kCarryallChainGun_upgrade",
    "d2kChainGun_upgrade", "ra1_soviets_rifleinfantry_carbine_incendiary",
    "IncendiaryM1Carbine", "LMG_ordos_upgrade", "SteelFighterRailgun",
}


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
        with self.assertRaisesRegex(RuntimeError, "non-selected behavior hash changed"):
            cohort.inspect(self.rules)
        self.assertTrue(cohort.inspect(HistoricalView(self, self.rules)))
        self.assertEqual(12, len(cohort.selections(self.rules)))
        for root, (_destination, expected, _total, _scale) in cohort.ROOTS.items():
            self.assertEqual(expected, cohort.descendants(self.rules, root), root)

    def test_each_member_has_one_pinned_destination_main(self):
        for name, (destination, total, scale) in cohort.selections(self.rules).items():
            key = f"{destination}FlatCompatibility"
            resolved = self.rules.resolve_weapon(name)
            self.assertEqual([key], main_warheads(resolved), name)
            node = next(child for child in resolved.children
                        if child.key == f"Warhead@{key}")
            self.assertEqual(total, int(str(node.get("Damage"))), name)
            self.assertEqual(scale, int(str(node.get("PercentageScale"))), name)

    def test_full_ruleset_comparison_matches_reviewed_manifest(self):
        self.assertEqual(set(cohort.selections(self.rules)), set(self.report["changed"]))
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
        self.assertEqual(set(cohort.selections(self.rules)) - {"SpecterArtilleryShellUpgrade"},
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
