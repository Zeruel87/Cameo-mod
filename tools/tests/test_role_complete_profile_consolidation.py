import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/role_complete_profile_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_role_complete_profiles as cohort
from audit_three_way_split import RAW_SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (
        20, "c3239489ed89040e8ae62f9267dd875a5536bf1c7df4c350696b828689bb722a"),
    "percentage_damage": (
        8, "7358ff3208ab5f09c1368032cbcb44d4225acfca563ef436d406749a13075bb2"),
}


def destination_key(destination):
    """R12 retired the *FlatCompatibility payload names for *_Flat mains."""
    return f"{destination}_Flat"


# The reviewed W24 lane-3 fold (8330a1834) removed the airmine's 1Dam air
# marker and folded its payload into the flat main.
AIR_MINE_TOTAL = 22000


class RoleCompleteProfileConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        # Preserve the historical report's selection. Ruling 10(a), e76fb585c0,
        # deliberately made ordos_airmine self-contained; never reattach it.
        cls.historical_selection = {
            name: spec[0] for root, spec in cohort.ROOTS.items()
            for name in {root, *spec[2]}
        }
        cls.historical_selection.update(dict.fromkeys(cohort.MANTA_AG, "Bullet_Medium"))
        cls.historical_selection.update(dict.fromkeys(cohort.MANTA_AA, "Flak_Medium"))
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_historical_converter_rejects_changed_closure_but_live_profiles_hold(self):
        # selections() still fails closed on the deliberately detached airmine
        # (ruling 10(a)).  inspect() also rejects the live view: R12 retired the
        # *FlatCompatibility main names it looks for and W24 lane-3 dropped the
        # airmine's 1Dam marker, so plans/already cannot be produced.
        with self.assertRaisesRegex(RuntimeError, "ixian_airdrone: closure changed"):
            cohort.validate_result()
        with self.assertRaises(RuntimeError):
            cohort.inspect(self.rules, self.historical_selection)
        # The reviewed post-R12 contract: each member still resolves exactly its
        # (renamed) flat main at the recorded total and scale.
        for name, destination in self.historical_selection.items():
            _mains, total, scale, damage_types = cohort.expected_plan(name, destination)
            resolved = self.rules.resolve_weapon(name)
            self.assertEqual([destination_key(destination)],
                             main_warheads(resolved), name)
            node = next(child for child in resolved.children
                        if child.key == f"Warhead@{destination_key(destination)}")
            self.assertEqual(AIR_MINE_TOTAL if name == "ordos_airmine" else total,
                             int(str(node.get("Damage"))), name)
            self.assertEqual(scale, int(str(node.get("PercentageScale"))), name)
            if damage_types:
                self.assertEqual(damage_types, str(node.get("DamageTypes")), name)
        for root, spec in cohort.ROOTS.items():
            expected = set() if root == "ixian_airdrone" else spec[2]
            self.assertEqual(expected, cohort.descendants(self.rules, root), root)
        # The W7 flatten moved the AG-resonance branch off SteelMantaAG; only the
        # AA route (root included) still inherits from it.
        self.assertEqual(cohort.MANTA_AA,
                         cohort.descendants(self.rules, cohort.MANTA_ROOT))

    def test_report_covers_exactly_the_selected_definitions(self):
        selected = set(self.historical_selection)
        self.assertEqual(20, len(selected))
        self.assertEqual(selected, set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])

    def test_every_change_matches_the_accepted_manifest(self):
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (count, expected_hash) in ACCEPTED.items():
            payload = json.dumps(
                self.by_kind[kind], sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(count, len(self.by_kind[kind]), kind)
            self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest(), kind)

    def test_manta_percentage_delta_is_exactly_bounded(self):
        for weapon, changes in self.by_kind["percentage_damage"].items():
            rows = [row for group in changes for row in group]
            self.assertEqual([[160, 4, 6], [250, 8, 10]], rows, weapon)

    def test_ground_and_air_routes_have_only_their_role_profile(self):
        # R12 retired the *FlatCompatibility names; the mains are now *_Flat.
        for weapon in cohort.MANTA_AG:
            self.assertEqual(
                ["Bullet_Medium_Flat"],
                main_warheads(self.rules.resolve_weapon(weapon)), weapon)
        for weapon in cohort.MANTA_AA:
            self.assertEqual(
                ["Flak_Medium_Flat"],
                main_warheads(self.rules.resolve_weapon(weapon)), weapon)

    def test_authored_damage_types_are_explicit(self):
        expected = {}
        for root, (destination, _mains, children, _total, _scale,
                   damage_types) in cohort.ROOTS.items():
            if damage_types:
                for weapon in {root, *children}:
                    expected[weapon] = (destination, damage_types)
        selected = self.historical_selection
        self.assertEqual(8, len(expected))
        for weapon, (destination, damage_types) in expected.items():
            self.assertEqual(destination, selected[weapon])
            resolved = self.rules.resolve_weapon(weapon)
            node = next(child for child in resolved.children
                        if child.key == f"Warhead@{destination_key(destination)}")
            self.assertEqual(damage_types, str(node.get("DamageTypes")), weapon)

    def test_air_mine_folded_into_a_single_renamed_flat_main(self):
        # The W24 lane-3 fold (8330a1834) removed the 1Dam air marker and raised
        # the flat main to the shipped total; R12 renamed the payload.
        self.assertNotIn("ordos_airmine", cohort.descendants(self.rules, "ixian_airdrone"))
        resolved = self.rules.resolve_weapon("ordos_airmine")
        self.assertEqual({"MissileAP_Heavy_Flat"}, set(main_warheads(resolved)))
        node = next(child for child in resolved.children
                    if child.key == "Warhead@MissileAP_Heavy_Flat")
        self.assertEqual(AIR_MINE_TOTAL, int(str(node.get("Damage"))))

    def test_ratchets_match_the_live_reduction(self):
        # Upstream retired exemptions: enforce the raw ceiling, never subtract reviewed stacks.
        self.assertLessEqual(RAW_SPLIT_BASELINE, 322)
        self.assertLessEqual(BROADCAST_BASELINE, 69)


if __name__ == "__main__":
    unittest.main()
