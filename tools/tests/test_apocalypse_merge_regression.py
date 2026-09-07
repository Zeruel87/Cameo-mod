"""Restore Aedis's authored Apocalypse roles, not a mixture of merge parents."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]
from audit_three_way_split import main_warhead_nodes, main_warheads
from audit_impact_glow_preservation import EMISSIVE_EFFECT_ROOTS, tier_path_count
from miniyaml import Ruleset, load

NAMES = ("RA2120xmm", "RA2120xmm_elite", "RA2120xmm_rad", "RA2120xmm_rad_elite")


def payload(node):
    return node.key, node.value, [payload(child) for child in node.children]


class ApocalypseMergeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_all_four_resolved_routes_match_the_authored_parent(self):
        actual = {name: payload(self.rules.resolve_weapon(name)) for name in NAMES}
        reference = Ruleset(ROOT)
        for node in load(pathlib.Path(__file__).parent / "fixtures/apocalypse_premerge.yaml"):
            reference.weapons[node.key] = node
        reference._resolve_cache.clear()
        for name in NAMES:
            expected = reference.resolve_weapon(name).deep_copy()
            if "_rad" in name:
                # Extracting the authored effects into one template moves only
                # these four cosmetic nodes before the deterministic radiation
                # update. Their mutual order and every field remain pinned.
                moved_keys = ["Warhead@EffectAir", "Warhead@Smudge", "Warhead@DuneRock", "Warhead@DuneSand"]
                moved = [expected.child(key) for key in moved_keys]
                self.assertTrue(all(node is not None for node in moved))
                expected.children = [node for node in expected.children if node.key not in moved_keys]
                position = next(i for i, node in enumerate(expected.children) if node.key == "Warhead@Radiation")
                expected.children[position:position] = moved
                self.assertIsNone(expected.child("Warhead@EffectAir").child("Inaccuracy"))
            self.assertEqual(payload(expected), actual[name], name)

    def test_effect_templates_do_not_hide_damage_or_radiation_mechanics(self):
        allowed_effects = {"CreateEffect", "LeaveSmudge", "GlowImpact", "FlashPaletteEffect",
                           "GrantExternalCondition", "DamagesConcrete"}
        for name, template in (("RA2120xmm", "^Effect_Apoc_AP_RA2"),
                               ("RA2120xmm_rad", "^Effect_Apoc_Chem_RA2")):
            local = self.rules.weapon(name)
            parents = [parent for _, parent in self.rules.inherits_of(local)]
            self.assertEqual([template], [p for p in parents if p.startswith("^Effect_")])
            self.assertFalse(any(n.key.startswith("Warhead@") and n.value in allowed_effects for n in local.children))
            effect = self.rules.resolve_weapon(template)
            self.assertIn(template, EMISSIVE_EFFECT_ROOTS)
            self.assertEqual(1, tier_path_count(self.rules, template, {}))
            self.assertEqual([("Inherits@glow", "^ImpactGlow")], self.rules.inherits_of(self.rules.weapon(template)))
            self.assertTrue(all(n.key.startswith("Warhead@") and n.value in allowed_effects for n in effect.children))
            self.assertIsNone(effect.child("Warhead@Radiation"))
        self.assertEqual("^RA2RadShell", self.rules.weapon("RA2120xmm_rad").get("Inherits@rad"))

    def test_single_canonical_main_and_no_legacy_percentage_companions(self):
        for name in NAMES:
            with self.subTest(weapon=name):
                resolved = self.rules.resolve_weapon(name)
                chemical = "_rad" in name
                tag = "CannonChem_Light" if chemical else "CannonAP_Light"
                self.assertEqual([tag], main_warheads(resolved))
                self.assertEqual("16000" if chemical else "12000", main_warhead_nodes(resolved)[0].get("Damage"))
                self.assertFalse(any(n.value == "AreaDamagePercentage" for n in resolved.children))
                if chemical:
                    self.assertEqual("100", resolved.child("Warhead@" + tag).child("PhysicalStates").get("Corrosion"))

    def test_cadence_and_projectile_contract_for_normal_and_elite(self):
        for name in NAMES:
            elite = name.endswith("_elite")
            weapon = self.rules.resolve_weapon(name)
            self.assertEqual(("63", "4" if elite else "2", "3" if elite else "5",
                              "7992" if elite else "6992", "vapoat1a.wav"),
                             tuple(weapon.get(k) for k in ("ReloadDelay", "Burst", "BurstDelays", "Range", "Report")), name)
            projectile = weapon.child("Projectile")
            self.assertEqual(("Bullet", "699", "150"),
                             (projectile.value, projectile.get("Speed"), projectile.get("Inaccuracy")), name)


if __name__ == "__main__":
    unittest.main()
