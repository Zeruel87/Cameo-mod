"""Pins Yuri's Level-1 AG gatling baseline and K=1.25 pricing input."""

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]
import extract_stats  # noqa: E402
import fit_class  # noqa: E402
from cameo_model import Model  # noqa: E402


EXPECTED = {
    "yuri_gatlingcannon": {
        "section": "defenses",
        "slot": "Armament@1",
        "weapon": "YuriGatlingCannonMG1",
        "range": 7500.0,
        "dps": 4000.0 / 6.0,
    },
    "yuri_gatlingtank": {
        "section": "vehicles",
        "slot": "Armament@1",
        "weapon": "YuriGatlingTankMG1",
        "range": 5400.0,
        "dps": 3000.0 / 6.0,
    },
}


class YuriGatlingPricingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Model().rs
        ledger = json.loads(
            (ROOT / "docs/balance/redalert2_yuri.json").read_text(encoding="utf-8")
        )
        cls.design = {
            actor: next(section[actor]["design"] for section in ledger["sections"].values()
                        if actor in section)
            for actor in EXPECTED
        }

    def record(self, actor):
        record = extract_stats.extract_actor(
            self.rules, actor, EXPECTED[actor]["section"]
        )
        record["design"].update(self.design[actor])
        # Formula-v2 supplies a synthetic defense speed at its caller boundary;
        # provide the same neutral input here so this focused test can exercise
        # Cannon range, DPS, and K through unit_inputs itself.
        if record.get("speed") is None:
            record["speed"] = {"v": 100}
        return record

    def test_extractor_prices_only_level_one_ground_for_both_actors(self):
        for actor, expected in EXPECTED.items():
            with self.subTest(actor=actor):
                record = self.record(actor)
                priced = [arm for arm in record["armaments"] if arm["pricing"]]
                self.assertEqual(
                    [(expected["slot"], expected["weapon"])],
                    [(arm["slot"], arm["weapon"]) for arm in priced],
                )
                excluded = [arm for arm in record["armaments"] if not arm["pricing"]]
                self.assertEqual(5, len(excluded))
                self.assertTrue(all(
                    arm["pricing_reason"] == "staged_gatling_nonbaseline"
                    for arm in excluded
                ))
                self.assertTrue(all(
                    arm["slot"].endswith("AA") or arm["slot"] in {"Armament@2", "Armament@3"}
                    for arm in excluded
                ))

    def test_fit_class_uses_that_single_weapon_for_range_and_dps(self):
        for actor, expected in EXPECTED.items():
            with self.subTest(actor=actor):
                record = self.record(actor)
                selected = fit_class.pricing_armaments(record)
                self.assertEqual([expected["weapon"]], [arm["weapon"] for arm in selected])
                inputs, fallbacks = fit_class.unit_inputs(record)
                self.assertEqual(0, fallbacks)
                self.assertEqual(expected["range"], inputs[2])
                self.assertAlmostEqual(expected["dps"], inputs[3])

    def test_both_committed_special_k_judgments_are_1_25(self):
        self.assertEqual(
            {actor: 1.25 for actor in EXPECTED},
            {actor: self.design[actor]["special"] for actor in EXPECTED},
        )
        for actor in EXPECTED:
            with self.subTest(actor=actor):
                inputs, _ = fit_class.unit_inputs(self.record(actor))
                self.assertEqual(1.25, inputs[4])


if __name__ == "__main__":
    unittest.main()
