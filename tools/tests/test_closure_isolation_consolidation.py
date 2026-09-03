"""Regression contract for the first closure-isolation redesign batch."""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/closure_isolation_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from audit_three_way_split import main_warhead_nodes, main_warheads
from miniyaml import Ruleset


CONSOLIDATED = {
    "AsianHowitzerSplash": ("Concussion_Medium", 40000),
    "TS155mm": ("Concussion_Medium", 60000),
    "TSAux155mm": ("Concussion_Medium", 60000),
    "TSInfantryMortar": ("Concussion_Medium", 32000),
}

PRESERVED_HASHES = {
    "TS155mm_bluenuke": "97a6765afdf585adf92ece0bbdfec067da014575966671eada8a4ca54f46817f",
    "GrenadeRA": "19d10234019c95012015db30a27922075fb2f736510b9141b467425504839afe",
    "GrenadeRAExplode": "463b5914bb50ab37d1d25754249953ddca938838709fb3626fecae3696d26b68",
    "GrenadeThermobaric": "0c9a10e9feacf943e2d83ee9eeb48adec2a564ad13f2aa7795711af3bc386760",
    "GrenadeThermobaricExplode": "d30dee2e543667518a319226aac7da2f8b7142a9da0bb3256fb5da613643946b",
}

EXPECTED_PERCENTAGE_DELTAS = {
    "TS155mm": [[250, 74, 75]],
    "TSAux155mm": [[250, 74, 75]],
    "TSInfantryMortar": [[20, 2, 3], [160, 24, 25]],
}


def node_payload(node):
    return [node.key, node.value, [node_payload(child) for child in node.children]]


def resolved_hash(node) -> str:
    raw = json.dumps(node_payload(node), separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def children_hash(node) -> str:
    raw = json.dumps(
        [node_payload(child) for child in node.children],
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def descendants(rules, root):
    children = {}
    for name, node in rules.weapons.items():
        for _key, parent in rules.inherits_of(node):
            if parent in rules.weapons:
                children.setdefault(parent, set()).add(name)
    seen = set()
    pending = list(children.get(root, set()))
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        pending.extend(children.get(name, set()))
    return {name for name in seen if not name.startswith("^")}


class ClosureIsolationConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_selected_roots_use_exact_concussion_profiles(self):
        for name, (profile, damage) in CONSOLIDATED.items():
            nodes = main_warhead_nodes(self.rules.resolve_weapon(name))
            self.assertEqual([profile], main_warheads(self.rules.resolve_weapon(name)), name)
            self.assertEqual(damage, int(nodes[0].get("Damage")), name)
            self.assertEqual("10000", nodes[0].get("PercentageScale"), name)

    def test_excluded_descendants_are_byte_stable_after_isolation(self):
        for name, expected in PRESERVED_HASHES.items():
            self.assertEqual(expected, resolved_hash(self.rules.resolve_weapon(name)), name)
        self.assertEqual({"TSAux155mm"}, descendants(self.rules, "TS155mm"))
        self.assertEqual(set(), descendants(self.rules, "TSInfantryMortar"))
        self.assertEqual(set(), descendants(self.rules, "GrenadeRA"))

    def test_kirov_uses_the_pinned_canonicalized_splash_payload(self):
        alias = self.rules.resolve_weapon("RA2KirovHowitzerSplash")
        self.assertEqual(
            "b77525d04f7bd02e15f288318bbd3e027f1232d9d4e1c2d1c522cb900b491bf0",
            children_hash(alias),
        )
        kirov = self.rules.resolve_weapon("RA2KirovBomb_fire")
        trigger = next(child for child in kirov.children if child.key == "Warhead@2Fire")
        self.assertEqual("RA2KirovHowitzerSplash", trigger.get("TriggerWeapon"))

    def test_whole_tree_comparison_is_exactly_the_authorized_scope(self):
        self.assertEqual(["RA2KirovHowitzerSplash"], self.report["added"])
        self.assertEqual([], self.report["removed"])
        self.assertEqual(
            {*CONSOLIDATED, "RA2KirovBomb_fire"},
            set(self.report["changed"]),
        )

        for name in CONSOLIDATED:
            kinds = {change[0] for change in self.report["changed"][name]}
            expected = {"armor_profile", "blast_shape"}
            if name in EXPECTED_PERCENTAGE_DELTAS:
                expected.add("percentage_damage")
                actual = next(
                    change[1] for change in self.report["changed"][name]
                    if change[0] == "percentage_damage"
                )
                self.assertEqual(EXPECTED_PERCENTAGE_DELTAS[name], actual, name)
            self.assertEqual(expected, kinds, name)

        self.assertEqual(
            ["non_damage_warheads"],
            [change[0] for change in self.report["changed"]["RA2KirovBomb_fire"]],
        )


if __name__ == "__main__":
    unittest.main()
