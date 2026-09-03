"""Unit tests for tools/audit/weapon_families.py.

The two tables used to be copy-pasted across the weapon-split tools; these tests
pin the contract the callers rely on so a future edit cannot quietly drop a
family or reorder the file list (both change what a survey reports).
"""

from __future__ import annotations

import pathlib
import tempfile
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

import weapon_families as wf


class OldFamiliesTest(unittest.TestCase):
    def test_every_entry_is_a_template_reference(self):
        for family in wf.OLD_FAMILIES:
            self.assertTrue(family.startswith("^"), family)
            self.assertNotIn(" ", family)

    def test_no_hyphens_underscore_only_naming(self):
        """DESIGN.md rule 9: underscore is the only separator."""
        self.assertEqual([f for f in wf.OLD_FAMILIES if "-" in f], [])

    def test_known_families_are_present(self):
        for family in ("^SmallArms", "^Chaingun", "^TeslaWeapon", "^MagicWeapon",
                       "^NuclearWarhead", "^LightArms"):
            self.assertIn(family, wf.OLD_FAMILIES)

    def test_is_a_set_so_membership_tests_are_exact(self):
        self.assertIsInstance(wf.OLD_FAMILIES, set)


class WeaponFilesTest(unittest.TestCase):
    def test_central_list_matches_current_active_monoliths(self):
        self.assertIn("weapons/d2k.yaml", wf.CENTRAL)
        self.assertIn("weapons/starcraft.yaml", wf.CENTRAL)
        self.assertIn("weapons/outpost2.yaml", wf.CENTRAL)
        self.assertNotIn("weapons/redalert2.yaml", wf.CENTRAL)
        self.assertNotIn("weapons/missiles.yaml", wf.CENTRAL)

    def test_central_files_come_first_and_in_listed_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = pathlib.Path(tmp)
            (mod / "ContentPacks").mkdir()
            files = wf.weapon_files(mod)
            self.assertEqual([p.relative_to(mod).as_posix() for p in files],
                             wf.CENTRAL)

    def test_contentpack_weapons_are_appended_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = pathlib.Path(tmp)
            for theme, faction in (("Zeta", "B"), ("Alpha", "A")):
                pack = mod / "ContentPacks" / theme / faction / "yaml"
                pack.mkdir(parents=True)
                (pack / "weapons.yaml").write_text("x\n", encoding="utf-8")
            tail = [p.relative_to(mod).as_posix()
                    for p in wf.weapon_files(mod)[len(wf.CENTRAL):]]
            self.assertEqual(tail, [
                "ContentPacks/Alpha/A/yaml/weapons.yaml",
                "ContentPacks/Zeta/B/yaml/weapons.yaml",
            ])

    def test_only_weapons_yaml_is_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = pathlib.Path(tmp)
            pack = mod / "ContentPacks" / "Theme" / "Faction" / "yaml"
            pack.mkdir(parents=True)
            (pack / "weapons.yaml").write_text("x\n", encoding="utf-8")
            (pack / "vehicles.yaml").write_text("x\n", encoding="utf-8")
            names = [p.name for p in wf.weapon_files(mod)[len(wf.CENTRAL):]]
            self.assertEqual(names, ["weapons.yaml"])

    def test_the_live_mod_tree_resolves(self):
        """MOD must point at mods/cameo, not somewhere above it."""
        self.assertEqual(wf.MOD.name, "cameo")
        self.assertEqual(wf.MOD.parent.name, "mods")


if __name__ == "__main__":
    unittest.main()
