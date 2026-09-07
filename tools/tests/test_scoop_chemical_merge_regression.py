"""The Scooper upgrade must not combine two alternative merge-parent payloads."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]
from audit_three_way_split import main_warhead_nodes, main_warheads
from miniyaml import Ruleset
from percentage_damage import percentage_applications


class ScooperChemicalMergeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.weapon = cls.rules.resolve_weapon("TSScoopDualChem")

    def test_one_inherited_chemical_cannon_not_two_alternative_payloads(self):
        # a92a4bc1bf explicitly chose CannonChem_Medium30000/Corrosion100.
        # Merge4fd9937f3 accidentally combined it with PR320's alternative30000.
        self.assertEqual(["CannonChem_Medium"], main_warheads(self.weapon))
        main = main_warhead_nodes(self.weapon)[0]
        self.assertEqual("AreaDamage", main.value)
        self.assertEqual("30000", main.get("Damage"))
        self.assertEqual("100", main.child("PhysicalStates").get("Corrosion"))
        self.assertIsNone(main.get("PhysicalStateName"))
        canonical = self.rules.resolve_weapon("^Warhead_CannonChem_Medium").child("Warhead@CannonChem_Medium")
        for field in ("Spread", "Falloff", "PercentageScale", "PercentageSpread",
                      "ValidTargets", "ValidRelationships", "FriendlyFireDamage", "DamageTypes"):
            self.assertEqual(canonical.get(field), main.get(field), field)
        for field in ("Versus", "PercentageVersus"):
            self.assertEqual([(x.key, x.value) for x in canonical.child(field).children],
                             [(x.key, x.value) for x in main.child(field).children], field)
        self.assertIsNone(self.weapon.child("Warhead@Chemical_MediumFlatCompatibility"))
        # The Python subset ignores missing removals; the engine rejects them.
        local = self.rules.weapon("TSScoopDualChem")
        self.assertIsNone(local.child("-Warhead@CannonHE_Medium"))
        self.assertIsNone(local.child("-Warhead@Chemical_Medium"))
        self.assertEqual([1500], [x["runtime_units"] for x in percentage_applications(self.weapon, 200000)])

    def test_core_firing_operation_and_effects_are_preserved(self):
        expected = {"ReloadDelay": "60", "Burst": "2", "BurstDelays": "2",
                    "Range": "6224", "Report": "flamer2.aud"}
        for key, value in expected.items():
            self.assertEqual(value, self.weapon.get(key), key)
        projectile = self.weapon.child("Projectile")
        self.assertEqual("Bullet", projectile.value)
        self.assertEqual("3500", projectile.get("Speed"))
        effect = self.weapon.child("Warhead@Effect")
        self.assertEqual("med_tibnapalm", effect.get("Explosions"))
        self.assertEqual("xplobig6.aud", effect.get("ImpactSounds"))
        self.assertEqual("1.5", effect.get("GlowScale"))
        cloud = self.weapon.child("Warhead@Cloud")
        self.assertEqual("TSSmoke", cloud.get("Weapon"))
        self.assertEqual("2", cloud.get("Count"))
        self.assertEqual("50", cloud.get("Duration"))

    def test_actor_switches_to_the_repaired_upgrade_exclusively(self):
        actor = self.rules.resolve("forgotten_scoopertank")
        base = actor.child("Armament@PRIMARY")
        upgraded = actor.child("Armament@UPGRADE")
        self.assertEqual("TSScoopDual", base.get("Weapon"))
        self.assertEqual("!forgotten_upgrade_chemicalweapons", base.get("RequiresCondition"))
        self.assertEqual("TSScoopDualChem", upgraded.get("Weapon"))
        self.assertEqual("forgotten_upgrade_chemicalweapons", upgraded.get("RequiresCondition"))


if __name__ == "__main__":
    unittest.main()
