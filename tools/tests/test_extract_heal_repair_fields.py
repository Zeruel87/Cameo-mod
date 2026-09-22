"""Ledger contract for named self-heal and repair fields."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "balance"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))


class ExtractHealRepairFieldsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cameo_model import Model
        cls.rules = Model(ROOT).rs

    @staticmethod
    def row(actor: str) -> dict:
        hits = []
        for path in sorted(LEDGER.glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
            for section in (doc.get("sections") or {}).values():
                if actor in section:
                    hits.append((path.name, section[actor]))
        if len(hits) != 1:
            raise AssertionError(f"expected one ledger row for {actor}, got {len(hits)}")
        return hits[0][1]

    def assert_extracted(self, actor: str, key: str, trait: str, field: str):
        slot = self.row(actor).get(key)
        self.assertIsInstance(slot, dict)
        self.assertTrue(
            slot["src"] == "inherited" or slot["src"].endswith(f"#{trait}.{field}")
        )
        resolved = self.rules.resolve(actor)
        self.assertEqual(slot["v"], str(resolved.child(trait).get(field)))

    def test_named_self_heal_and_repair_are_present(self):
        for actor in (
            "td_gdi_mobileconstructionvehicle",
            "td_gdi_tiberiumharvester",
            "japan_japaneseoretruck",
            "ra1_allies_mobilegapgenerator",
            "ra1_allies_mobileradarjammer",
        ):
            with self.subTest(actor=actor):
                self.assert_extracted(
                    actor, "self_heal_step", "ChangesHealth@SelfHealing", "Step"
                )
                self.assert_extracted(
                    actor, "repairable_hp_per_step", "Repairable", "HpPerStep"
                )

    def test_repairable_provenance_is_carried_for_local_batch_fields(self):
        for actor in (
            "td_gdi_tiberiumharvester",
            "td_gdi_mobileconstructionvehicle",
            "ra1_allies_mobilegapgenerator",
        ):
            with self.subTest(actor=actor):
                slot = self.row(actor)["repairable_hp_per_step"]
                self.assertTrue(slot["src"].endswith("#Repairable.HpPerStep"))

    def test_conditional_named_heal_is_not_the_canonical_self_heal(self):
        # The IFV's upgrade heal is conditional and must not replace the
        # unconditional/base SelfHealing field in the canonical ledger key.
        slot = self.row("ra2_allies_ifv")["self_heal_step"]
        self.assertNotIn("#ChangesHealth@ra2_allies_upgrade_vanguardtraining.Step", slot["src"])
        self.assertEqual("10", slot["v"])

    def test_bare_and_named_instances_are_not_collapsed(self):
        for actor in (
            "cabal_cyborgreaper",
            "cabal_heavyreaper",
            "protoss_starshipsovereign",
        ):
            with self.subTest(actor=actor):
                row = self.row(actor)
                self.assertIn("#ChangesHealth@SelfHealing.Step", row["self_heal_step"]["src"])
                self.assertIn("#ChangesHealth.Step", row["self_heal_step_other"]["src"])

    def test_bare_only_actor_keeps_the_applyable_canonical_key(self):
        actor = "devastator"
        row = self.row(actor)
        slot = row["self_heal_step"]
        self.assertIn("#ChangesHealth.Step", slot["src"])
        self.assertEqual(
            str(self.rules.resolve(actor).child("ChangesHealth").get("Step")),
            slot["v"],
        )
        self.assertNotIn("self_heal_step_other", row)


if __name__ == "__main__":
    unittest.main()
