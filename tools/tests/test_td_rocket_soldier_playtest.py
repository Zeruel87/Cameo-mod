"""Focused contract for the first applied classic-four balance pair."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from cameo_model import Model  # noqa: E402
import cargo_pricing  # noqa: E402
import check_band  # noqa: E402


ACTORS = ("td_gdi_rocketsoldier", "td_nod_rocketsoldier")
ACTOR_STATS = {
    "td_gdi_rocketsoldier": ("450", "16000", "16", "42"),
    "td_nod_rocketsoldier": ("390", "14000", "14", "48"),
}
WEAPONS = (
    "td_gdi_rocketsoldier_rockets",
    "td_gdi_rocketsoldier_rocketsamt",
    "td_nod_rocketsoldier_rockets",
)
WEAPON_STATS = {
    "td_gdi_rocketsoldier_rockets": ("6500", "15800"),
    "td_gdi_rocketsoldier_rocketsamt": ("6500", "15800"),
    "td_nod_rocketsoldier_rockets": ("6028", "16882"),
}
CARGO_COSTS = {
    "td_gdi_apc": 1800,
    "td_gdi_assaultapc": 4120,
    "td_gdi_chinooktransport": 4120,
    "td_gdi_humveemkii": 900,
    "td_nod_buggymkii": 850,
}


class TdRocketSoldierPlaytestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = Model(ROOT)
        cls.rules = cls.model.rs

    def test_actor_pair_uses_the_reviewed_faction_identity_split(self):
        for actor_name in ACTORS:
            with self.subTest(actor=actor_name):
                actor = self.rules.resolve(actor_name)
                cost, hp, healing, speed = ACTOR_STATS[actor_name]
                self.assertEqual(actor.child("Valued").get("Cost"), cost)
                self.assertEqual(actor.child("Health").get("HP"), hp)
                self.assertEqual(actor.child("ChangesHealth@SelfHealing").get("Step"), healing)
                self.assertEqual(actor.child("Mobile").get("Speed"), speed)

    def test_owned_weapon_family_uses_one_component_proposal(self):
        parents = {
            "td_gdi_rocketsoldier_rockets": "Rockets",
            "td_gdi_rocketsoldier_rocketsamt": "RocketsAMT",
            "td_nod_rocketsoldier_rockets": "Rockets",
        }
        for weapon_name in WEAPONS:
            with self.subTest(weapon=weapon_name):
                local = self.rules.weapon(weapon_name)
                self.assertEqual(local.child("Inherits").value, parents[weapon_name])
                weapon = self.rules.resolve_weapon(weapon_name)
                self.assertEqual(weapon.get("ReloadDelay"), "56")
                range_value, damage = WEAPON_STATS[weapon_name]
                self.assertEqual(weapon.get("Range"), range_value)
                self.assertEqual(int(weapon.get("Burst") or 1), 1)
                self.assertEqual(
                    weapon.child("Warhead@MissileAP_Light").get("Damage"),
                    damage,
                )

    def test_map_import_alias_keeps_the_old_chassis_and_shared_weapons(self):
        actor = self.rules.resolve("E3")
        self.assertEqual(actor.child("Valued").get("Cost"), "300")
        self.assertEqual(actor.child("Health").get("HP"), "9000")
        self.assertEqual(actor.child("ChangesHealth@SelfHealing").get("Step"), "9")
        self.assertEqual(actor.child("Mobile").get("Speed"), "50")
        self.assertEqual(actor.child("Armament@PRIMARY").get("Weapon"), "Rockets")
        weapon = self.rules.resolve_weapon("Rockets")
        self.assertEqual(weapon.get("ReloadDelay"), "63")
        self.assertEqual(weapon.get("Range"), "6368")
        self.assertEqual(
            weapon.child("Warhead@MissileAP_Light").get("Damage"), "18000"
        )

    def test_every_valid_authored_load_keeps_passenger_sum_pricing(self):
        for actor_name, expected in CARGO_COSTS.items():
            with self.subTest(actor=actor_name):
                load = cargo_pricing.authored_load(self.rules, actor_name)
                self.assertEqual([], load["issues"])
                self.assertEqual(expected, load["passenger_sum"])
                self.assertEqual(
                    str(expected), self.rules.resolve(actor_name).child("Valued").get("Cost")
                )

    def test_nod_chinook_load_is_valid_and_uses_passenger_sum(self):
        load = cargo_pricing.authored_load(self.rules, "td_nod_chinooktransport")
        self.assertEqual([], load["issues"])
        self.assertEqual(3853, load["passenger_sum"])
        self.assertEqual(
            "3853",
            self.rules.resolve("td_nod_chinooktransport").child("Valued").get("Cost"),
        )

    def test_final_ledger_formula_keeps_the_pre_identity_420_baseline(self):
        raw = json.loads(
            (ROOT / "docs" / "balance" / "tiberiandawn_gdi.json").read_text(
                encoding="utf-8"
            )
        )["sections"]["infantry"]["td_gdi_rocketsoldier"]
        derived = json.loads(
            (ROOT / "docs" / "balance" / "derived" / "tiberiandawn_gdi.json").read_text(
                encoding="utf-8"
            )
        )["sections"]["infantry"]["td_gdi_rocketsoldier"]
        anchor = json.loads(
            (ROOT / "docs" / "balance" / "class_anchors.json").read_text(
                encoding="utf-8"
            )
        )["rocket_trooper"]
        inputs = check_band.unit_inputs(raw, derived)
        price = check_band.price_for("rocket_trooper", anchor, inputs)
        self.assertEqual(420, round(price / 10) * 10)
        self.assertEqual(
            "450",
            self.rules.resolve("td_gdi_rocketsoldier").child("Valued").get("Cost"),
        )


if __name__ == "__main__":
    unittest.main()
