"""Contracts for the independently reviewed conventional six-weapon core."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/conventional_weapon_core_summary.json"
sys.path[:0] = [str(ROOT / "tools/audit")]

from audit_three_way_split import (  # noqa: E402
    RAW_SPLIT_BASELINE,
    SPLIT_BASELINE,
    main_warhead_nodes,
    main_warheads,
)
from audit_warhead_split import BROADCAST_BASELINE  # noqa: E402
from miniyaml import Ruleset  # noqa: E402


EXPECTED = {
    "DeviatorMissile": ("MissileAP_Heavy", 40000, 4998),
    "DeviatorMissile_Artillery": ("MissileAP_Heavy", 60000, 3332),
    "Wraith_ToxinMissiles": ("MissileAP_Heavy", 60000, 3332),
    "FlakbusAA": ("Flak_Medium", 32000, 9997),
    "RA2KirovHowitzerSplash": ("Concussion_Medium", 40000, 9998),
    "wc2ballistaFire": ("Demolition_Heavy", 90000, 9999),
}


def descendants(rules: Ruleset, root: str) -> set[str]:
    children = {}
    for name, node in rules.weapons.items():
        for _key, parent in rules.inherits_of(node):
            if parent in rules.weapons:
                children.setdefault(parent, set()).add(name)
    seen, pending = set(), list(children.get(root, ()))
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        pending.extend(children.get(name, ()))
    return {name for name in seen if not name.startswith("^")}


class ConventionalWeaponCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_deviator_closure_is_complete_and_paid_aphid_is_out_of_scope(self):
        self.assertEqual(
            {"DeviatorMissile_Artillery", "Wraith_ToxinMissiles"},
            descendants(self.rules, "DeviatorMissile"),
        )
        self.assertNotIn("Aphid_AA", EXPECTED)
        self.assertNotIn("AphidCryo_AA", EXPECTED)

    def test_each_selected_weapon_has_one_named_main_with_pinned_fold(self):
        for name, (main, damage, scale) in EXPECTED.items():
            with self.subTest(name=name):
                resolved = self.rules.resolve_weapon(name)
                self.assertEqual([main], main_warheads(resolved))
                nodes = main_warhead_nodes(resolved)
                self.assertEqual(1, len(nodes))
                self.assertEqual(str(damage), str(nodes[0].get("Damage")))
                self.assertEqual(str(scale), str(nodes[0].get("PercentageScale")))

    def test_whole_ruleset_comparison_is_exactly_the_reviewed_role_change(self):
        self.assertEqual(set(EXPECTED), set(self.report["changed"]))
        self.assertEqual({
            "armor_profile": 6,
            "blast_shape": 6,
            "percentage_damage": 5,
        }, self.report["change_kind_counts"])
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])
        self.assertEqual(
            {
                "armor_profile": "b427eeba570c2c07896e0764a82f3f9801b0a9c9326c127e88b3af1aa3d1e1ce",
                "blast_shape": "db24dcd88636f68574a6f4dd3786f3b171a2ad76eb8693da8ace32c5a5792d81",
                "percentage_damage": "d5f11d8cf029ecd3bbac8d8b6a799210605b8d980290afa4a7bb831e5f7beaf5",
            },
            self.report["change_kind_digests"],
        )

    def test_percentage_rounding_is_bounded_to_six_one_hp_rows(self):
        self.assertEqual({
            "digest": "3f5cbff66f2b7a66eee59071ce7e57aade5e888d6b817591fd7d13faa302e8a0",
            "max_absolute_delta": 1,
            "row_count": 6,
        }, self.report["percentage_rounding"])

    def test_ratchets_match_the_live_structural_reduction(self):
        self.assertEqual(340, RAW_SPLIT_BASELINE)
        self.assertEqual(114, SPLIT_BASELINE)
        self.assertEqual(90, BROADCAST_BASELINE)


if __name__ == "__main__":
    unittest.main()
