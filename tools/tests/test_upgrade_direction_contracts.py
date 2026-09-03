"""Resolved contracts for paid stat upgrades with intentional tradeoffs."""

from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401 - sys.path side effect

from audit_upgrades import is_deferred_inverted, load_intent
from cameo_model import Model


class UpgradeDirectionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = Model()
        cls.rules = cls.model.rs

    def test_elite_capacitors_preserve_authored_reload_tradeoff(self):
        recipients = {}
        condition = "td_nod_upgrade_elitecapacitors"
        for actor in sorted(self.rules.actors):
            if actor.startswith("^"):
                continue
            resolved = self.rules.resolve(actor)
            if resolved is None:
                continue
            for trait in resolved.children_named("ReloadDelayMultiplier"):
                if (trait.get("RequiresCondition") or "").strip() == condition:
                    recipients[actor] = int(trait.get("Modifier"))

        self.assertEqual({
            "nodlasercorvette": 115,
            "td_nod_lasercommando": 115,
            "td_nod_lasertrooper": 115,
            "td_nod_laserturret": 115,
            "td_nod_lighttankmkii": 115,
            "td_nod_obeliskoflight": 40,
            "td_nod_venom": 115,
        }, recipients)
        self.assertEqual(
            "reloaddelaymultiplier",
            load_intent(self.model.root)["td_nod_upgrade_elitecapacitors"]["drawbacks"],
        )

    def test_cybernetic_damage_amplification_is_an_authored_tradeoff(self):
        intent = load_intent(self.model.root)
        self.assertEqual(
            "damagemultiplier",
            intent["td_nod_upgrade_cyberneticmodifications"]["drawbacks"],
        )
        template = self.rules.resolve("^CyberneticModifications")
        damage = template.child(
            "DamageMultiplier@td_nod_upgrade_cyberneticmodifications")
        self.assertEqual("200", damage.get("Modifier"))

    def test_reviewed_multi_payload_and_armor_tradeoffs_are_declared(self):
        intent = load_intent(self.model.root)
        expected = {
            "asianalliance_doctrine_heavypulverizerweapons": "firepowermultiplier",
            "japan_upgrade_energizedarrows":
                "firepowermultiplier reloaddelaymultiplier",
            "japan_upgrade_advancedplasmaweapons": "firepowermultiplier",
            "ra1_allies_upgrade_cryomissiles": "firepowermultiplier",
            "ra1_soviets_doctrine_teslaandexperimentaltech":
                "reloaddelaymultiplier",
            "ra2_soviets_doctrine_heavyarmorplatings": "speedmultiplier",
            "ra2_soviets_doctrine_reactivearmor": "speedmultiplier",
            "ra2_soviets_doctrine_tesladischargearmor": "speedmultiplier",
            "steelconsortium_upgrade_resonanceammo": "firepowermultiplier",
        }
        self.assertEqual(
            expected,
            {name: intent[name]["drawbacks"] for name in expected},
        )

    def test_clone_trooper_pricing_linked_finding_is_exactly_deferred(self):
        fingerprint = (
            "steelconsortium_upgrade_pulseweapons",
            "steelconsortium_clonetrooper",
            "FirepowerMultiplier@steelconsortium_upgrade_pulseweapons",
        )
        self.assertTrue(is_deferred_inverted(*fingerprint, "91"))
        self.assertFalse(is_deferred_inverted(*fingerprint, "92"))
        self.assertFalse(is_deferred_inverted(
            fingerprint[0], "steelconsortium_otheractor", fingerprint[2], "91"))


if __name__ == "__main__":
    unittest.main()
