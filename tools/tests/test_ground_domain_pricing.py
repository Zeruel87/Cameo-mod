"""Free AA must not buy ground DPS, range, K coverage or wind-up discounts."""
import copy
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/balance"), str(ROOT / "tools/audit")]
import fit_class
import derive_virtual_anchor as derive
import reference_distribution as reference
from miniyaml import Ruleset


def arm(slot="Armament", weapon="GroundGun", damage=2000, range_=4000, reload_=20, **extra):
    return dict(slot=slot, weapon=weapon, pricing=True, range=range_, reloaddelay=reload_, burst=1,
                damage_warheads=[dict(tag="Bullet", type="AreaDamage", damage=damage)], **extra)


def unit(*arms):
    return dict(hp={"v": 100000}, speed={"v": 100}, cost={"v": 800}, armaments=list(arms))


class GroundDomainTests(unittest.TestCase):
    def test_free_aa_is_detected_by_slot_or_weapon_not_only_primary(self):
        for aa in (arm(slot="Armament@AA", weapon="AirGun", range_=6000),
                   arm(slot="Armament@SECONDARY", weapon="Gun_AA", range_=6000),
                   arm(slot="Armament@SECONDARY", weapon="Gun_aa_elite", range_=6000)):
            with self.subTest(aa=aa["weapon"]):
                record = unit(arm(), aa)
                inputs, _ = fit_class.unit_inputs(record)
                self.assertEqual(inputs[2:4], (4000, 100))
                self.assertEqual(fit_class.pricing_armaments(record), reference.baseline_armaments(record["armaments"]))

    def test_simultaneous_ground_weapons_still_sum(self):
        record = unit(arm(), arm(slot="Armament@ROCKET", weapon="Rocket", damage=4000, range_=5000),
                      arm(slot="Armament@AA", range_=9000))
        inputs, _ = fit_class.unit_inputs(record)
        self.assertEqual(inputs[2:4], (5000, 300))

    def test_pure_aa_keeps_its_weapons(self):
        record = unit(arm(slot="Armament@AA", range_=6000), arm(weapon="Missile_AA", range_=7000))
        inputs, _ = fit_class.unit_inputs(record)
        self.assertEqual(inputs[2:4], (7000, 200))
        self.assertEqual(fit_class.pricing_armaments(record), record["armaments"])

    def test_inactive_or_unpriced_ground_does_not_erase_active_aa(self):
        for ground in (arm(requires="deployed"), dict(arm(), pricing=False)):
            record = unit(ground, arm(slot="Armament@AA", range_=6000))
            inputs, _ = fit_class.unit_inputs(record)
            self.assertEqual(inputs[2:4], (6000, 100))

    def test_does_not_adopt_reference_strongest_conditional_fallback(self):
        record = unit(arm(requires="deployed"), arm(weapon="Other_AA", requires="elite"))
        self.assertEqual(fit_class.pricing_armaments(record), [])
        self.assertEqual(fit_class.unit_inputs(record), (None, 0))

    def test_negated_upgrade_baseline_remains_active(self):
        record = unit(arm(requires="!upgraded"), arm(weapon="Elite", damage=99999, requires="upgraded"),
                      arm(slot="Armament@AA", requires="!upgraded"))
        inputs, _ = fit_class.unit_inputs(record)
        self.assertEqual(inputs[3], 100)

    def test_k_inputs_and_fallbacks_use_only_selected_domain(self):
        record = unit(arm(), arm(slot="Armament@AA", weapon="AirGun"))
        derived = dict(armaments=[dict(slot="Armament", weapon="GroundGun", effective_dps=25)])
        inputs, fallbacks = fit_class.unit_inputs(record, derived, use_k=True)
        self.assertEqual((inputs[3], fallbacks), (25, 0))
        inputs, fallbacks = fit_class.unit_inputs(record, {}, use_k=True)
        self.assertEqual((inputs[3], fallbacks), (100, 1))

    def test_free_aa_cannot_change_charge_cycle_fallback(self):
        record = unit(arm(reload_=20), arm(slot="Armament@AA", reload_=100))
        self.assertEqual(fit_class.charge_cycle_fallback(record), 20)
        record["armaments"] = record["armaments"][1:]
        self.assertEqual(fit_class.charge_cycle_fallback(record), 100)

    def test_derivation_range_uses_same_ground_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            record = unit(arm(), arm(slot="Armament@AA", range_=9000))
            record["design"] = {"class_anchor": "mbt"}
            path = pathlib.Path(directory)
            (path / "test.json").write_text(json.dumps({"sections": {"units": {"tank": record}}}), encoding="utf-8")
            self.assertEqual(derive.load_members(path)[0]["range_wdist"], 4000)


class CommittedGroundDomainTests(unittest.TestCase):
    def test_apc_and_btr_use_resolved_ground_weapon_not_free_air_variant(self):
        rules = Ruleset(ROOT)
        for ledger, actor in (("tiberiandawn_gdi", "td_gdi_apc"), ("redalert_soviets", "ra1_soviets_btr80")):
            with self.subTest(actor=actor):
                doc = json.loads((ROOT / "docs/balance" / f"{ledger}.json").read_text(encoding="utf-8"))
                record = next(section[actor] for section in doc["sections"].values() if actor in section)
                active = [a for a in record["armaments"] if a.get("pricing", True)
                          and fit_class.formula.condition_holds_by_default(a.get("requires"))]
                expected = reference.baseline_armaments(active)
                self.assertLess(len(expected), len(active))
                self.assertEqual(fit_class.pricing_armaments(record), expected)
                ground_only = copy.deepcopy(record)
                ground_only["armaments"] = expected
                self.assertEqual(fit_class.unit_inputs(record), fit_class.unit_inputs(ground_only))
                resolved_ranges = [fit_class.formula.wdist_value(rules.resolve_weapon(a["weapon"]).get("Range")) for a in expected]
                self.assertEqual(fit_class.unit_inputs(record)[0][2], max(resolved_ranges))
