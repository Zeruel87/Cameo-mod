import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warhead_nodes, main_warheads
from consolidate_corroborated_role_profiles import (
    BASELINE,
    ROOTS,
    TARGETS,
    remove_local_compatibility_removal,
    selections,
    set_state_scale,
)
from miniyaml import Ruleset
from percentage_damage import runtime_percentage_hp
from survey_weapon_structure import weapon_reference_sets


class CorroboratedRoleProfileConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.selected = selections(cls.rules)

    def test_selected_profiles_resolve_to_one_pinned_main(self):
        self.assertEqual(50, len(self.selected))
        for name, destination in self.selected.items():
            nodes = main_warhead_nodes(self.rules.resolve_weapon(name))
            self.assertEqual(1, len(nodes), name)
            node = nodes[0]
            self.assertEqual(
                f"Warhead@{destination}FlatCompatibility", node.key, name)
            _keys, damage, scale = BASELINE[name]
            self.assertEqual(str(damage), node.get("Damage"), name)
            self.assertEqual(str(scale), node.get("PercentageScale"), name)
            self.assertEqual(TARGETS[name], node.get("ValidTargets"), name)

    def test_selected_roots_keep_exact_inheritance_closures(self):
        selected = selections(self.rules)
        for root, (destination, descendants, _evidence) in ROOTS.items():
            self.assertEqual(destination, selected[root])
            self.assertTrue(descendants <= set(selected))

    def test_pinned_or_contradictory_roles_remain_outside_the_cohort(self):
        excluded = {
            "AtreusMG", "EpigraphMG", "GoliathMG", "GoliathMk2MG",
            "HMG_Duelist_upgrade", "autogun_tank",
            "TSRPGTowerRail", "VolkovMagneticWeapon",
            "BCLaser", "BCYamatoCannon",
            "edenMobileLaserTiger",
            "JimRaynorMachineGun",
        }
        self.assertTrue(excluded.isdisjoint(self.selected))
        for name in excluded:
            self.assertGreaterEqual(
                len(main_warheads(self.rules.resolve_weapon(name))), 2, name)
        for name in ("tkmjuggap", "tkmtechnicalmgap"):
            self.assertEqual(1, len(main_warheads(self.rules.resolve_weapon(name))), name)

    def test_new_bulk_roles_keep_special_companion_payloads(self):
        naxis = self.rules.resolve_weapon("NaxisBlackBombSmaller")
        self.assertIsNotNone(naxis.child("Warhead@LightChemicalWeaponPercentage"))
        self.assertIsNotNone(naxis.child("Warhead@HeavyBombPercentage"))
        self.assertIsNotNone(naxis.child("Warhead@Radiation"))

        for name in ("AsianPhotonCannon_EMP", "AsianPunisherAG_EMP",
                     "AsianQuasarAG_EMP", "AsianQuasar_EMP_AA"):
            weapon = self.rules.resolve_weapon(name)
            self.assertEqual(1, len(main_warheads(weapon)), name)
            self.assertIsNotNone(weapon.child("Warhead@EMPUnit"), name)
            self.assertIsNotNone(
                weapon.child("Warhead@PreservedFlat_MagicExtraDamage"), name)
            self.assertIsNotNone(
                weapon.child("Warhead@PreservedFlat_TeslaExtraDamage"), name)

    def test_all_selected_definitions_are_reachable(self):
        concrete = {
            name for name in self.rules.weapons
            if not name.startswith("^")
            and self.rules.resolve_weapon(name) is not None
        }
        _direct, reachable = weapon_reference_sets(self.rules, concrete)
        self.assertTrue(set(self.selected) <= reachable)

    def test_naxis_flak_preserves_counted_allied_damage(self):
        for name in (
            "NaxFlakAA", "NaxQuadCannon_AA", "NaxQuadCannon_AA_elite",
            "PortableFlak", "PortableFlak_elite", "SkyMageCannon_AA",
            "SkyMageCannon_AA_elite",
        ):
            node = self.rules.resolve_weapon(name).child(
                "Warhead@NaxFlakAllyCounted")
            self.assertEqual("1500", node.get("Damage"), name)

    def test_pulverizer_child_does_not_reinherit_parent_template(self):
        template = "^Compatibility_Bullet_MediumFlat"
        parent = self.rules.weapon("AsianPulverizerGatling")
        child_weapon = self.rules.weapon("AsianPulverizerMechaGatling")
        parent_inherits = {
            str(node.value).strip() for node in parent.children
            if node.key.startswith("Inherits")
        }
        child_inherits = {
            str(node.value).strip() for node in child_weapon.children
            if node.key.startswith("Inherits")
        }
        self.assertIn(template, parent_inherits)
        self.assertNotIn(template, child_inherits)

    def test_latin_molotov_keeps_temperature_and_fire_payloads(self):
        for name in (
                "latinsyndicate_latinmilitia_molotov",
                "latinsyndicate_latinmilitia_molotov_elite"):
            resolved = self.rules.resolve_weapon(name)
            main = main_warhead_nodes(resolved)[0]
            self.assertEqual("Temperature", main.get("PhysicalStateName"), name)
            self.assertEqual("75", main.get("PhysicalStateScale"), name)
            self.assertIsNotNone(resolved.child("Warhead@FireShrapnel"), name)

    def test_converter_helpers_remove_suppression_and_keep_state_field(self):
        path = pathlib.Path("unused")
        lines = [
            "Example:\n",
            "\t-Warhead@Flame_LightFlatCompatibility:\n",
            "\tWarhead@Flame_LightFlatCompatibility:\n",
            "\t\tDamage: 8000\n",
            "\t\tPhysicalStateScale: 100\n",
            "Next:\n",
        ]
        changed = {path: lines}
        remove_local_compatibility_removal(
            changed, path, "Example", "Flame_Light")
        self.assertNotIn(
            "\t-Warhead@Flame_LightFlatCompatibility:\n", lines)
        set_state_scale(changed, path, "Example", "Flame_Light", 75)
        self.assertIn("\t\tPhysicalStateScale: 75\n", lines)
        self.assertEqual(
            1, lines.count("\t\tPhysicalStateScale: 75\n"))

    def test_folded_percentage_rounding_delta_is_pinned_and_minimal(self):
        health_values = set()
        for name in self.rules.actors:
            if name.startswith("^"):
                continue
            actor = self.rules.resolve(name)
            health = actor.child("Health") if actor is not None else None
            if health is not None and health.get("HP"):
                health_values.add(int(health.get("HP")))
        health_values.add(200000)

        for applications in (2, 3):
            differences = {
                hp: runtime_percentage_hp(hp, applications * 100, 10000)
                    - applications * runtime_percentage_hp(hp, 100, 10000)
                for hp in health_values
            }
            # New actors may add rounding cases without a runtime regression.
            # 1250 HP is now present on devastator.husk; retain known edge cases
            # and check the quantization bound over the entire current roster.
            for hp in (160, 250, 1250):
                self.assertEqual(1, differences[hp], (applications, hp))
            for hp, delta in differences.items():
                self.assertGreaterEqual(delta, 0, (applications, hp))
                self.assertLessEqual(delta, applications - 1, (applications, hp))


if __name__ == "__main__":
    unittest.main()
