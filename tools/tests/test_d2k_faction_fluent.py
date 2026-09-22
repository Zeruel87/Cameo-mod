"""Contract for active Dune Universe faction names and lobby descriptions."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from cameo_model import Model  # noqa: E402
from miniyaml import Ruleset  # noqa: E402


EXPECTED = {
    "RandomDU": ("faction_d2k_random", "Random Dune"),
    "atreides": ("faction_d2k_atreides", "Atreides"),
    "harkonnen": ("faction_d2k_harkonnen", "Harkonnen"),
    "ordos": ("faction_d2k_ordos", "Ordos"),
    "corrino": ("faction_d2k_corrino", "Corrino"),
    "ixian": ("faction_d2k_ixian", "Ixian"),
}

UNIT_OWNER_COUNTS = {
    "d2k/atreides": 18,
    "d2k/harkonnen": 19,
    "d2k/corrino": 19,
    "d2k/ordos": 32,
    "d2k/ixian": 26,
}

ORDOS_TURRETS = {"ordos_laserturret", "ordos_chemturret"}


def fluent_block(text: str, key: str) -> str:
    match = re.search(rf"(?ms)^{re.escape(key)} =\n(.*?)(?=^[a-z0-9_]+ =|\Z)", text)
    return match.group(0).rstrip() if match else ""


class D2KFactionFluentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = Model(ROOT)
        cls.rules = Ruleset(ROOT)
        cls.fluent = (ROOT / "mods/cameo/fluent/rules/en.ftl").read_text(encoding="utf-8")
        cls.d2k_fluent = "\npack_boundary =\n".join(
            (ROOT / f"mods/cameo/ContentPacks/D2k/{pack}/translations/en.ftl")
            .read_text(encoding="utf-8")
            .rstrip()
            for pack in ("Atreides", "Harkonnen", "Corrino", "Ordos", "Ixian")
        )

    def test_active_factions_use_fluent_name_and_description(self):
        world = self.rules.resolve("World")
        factions = {
            child.get("InternalName"): child
            for child in world.children
            if child.key.startswith("FactionCA@") and child.get("Game") == "Dune Universe"
        }
        self.assertEqual(set(EXPECTED), set(factions))

        for internal_name, (key, display_name) in EXPECTED.items():
            with self.subTest(faction=internal_name):
                faction = factions[internal_name]
                self.assertEqual(f"{key}.name", faction.get("Name"))
                self.assertEqual(f"{key}.description", faction.get("Description"))
                block = fluent_block(self.fluent, key)
                self.assertTrue(block, key)
                self.assertIn(f".name = {display_name}", block)
                self.assertIn(".description = ", block)

    def test_descriptions_share_current_role_format(self):
        for internal_name, (key, _) in EXPECTED.items():
            if internal_name == "RandomDU":
                continue
            with self.subTest(faction=internal_name):
                block = fluent_block(self.fluent, key)
                for field in ("Playstyle:", "Strengths:", "Weaknesses:", "Signature units:"):
                    self.assertEqual(1, block.count(field), (key, field))
                self.assertNotRegex(block, r"(?i)\b(?:AI-wired|WIP)\b")
                self.assertNotRegex(block, r"\b\d+/(?:\d+)\b")

    def test_active_yaml_has_no_du_display_suffix_or_inline_description(self):
        faction_files = list((ROOT / "mods/cameo/ContentPacks/D2k").glob("*/yaml/faction.yaml"))
        active_text = "\n".join(path.read_text(encoding="utf-8") for path in faction_files)
        self.assertNotRegex(active_text, r"(?m)^\s*Name:\s+.*\bDU\s*$")
        for key, _ in EXPECTED.values():
            self.assertIn(f"Name: {key}.name", active_text)
            self.assertIn(f"Description: {key}.description", active_text)

    def test_requested_units_and_ordos_turrets_use_standard_fluent_copy(self):
        by_owner = {owner: set() for owner in UNIT_OWNER_COUNTS}
        for actor in self.rules.actors:
            resolved = self.rules.resolve(actor)
            if resolved is None or not self.model.is_buildable(resolved):
                continue
            owner = self.model.owner_of(actor)
            if owner in by_owner and self.model.unit_type(actor) in {"inf", "veh", "air", "nav"}:
                by_owner[owner].add(actor)

        self.assertEqual(UNIT_OWNER_COUNTS, {owner: len(actors) for owner, actors in by_owner.items()})
        targets = set().union(*by_owner.values(), ORDOS_TURRETS)
        allowed_detail_lines = (
            "Strong vs ",
            "Weak vs ",
            "Detects ",
            "Transports ",
            "Unarmed",
            "Cloaked ",
            "Can ",
            "Detonates ",
            "Abilities: ",
        )

        for actor in sorted(targets):
            with self.subTest(actor=actor):
                resolved = self.rules.resolve(actor)
                key = f"actor_{actor.replace('.', '_')}"
                self.assertEqual(f"{key}.name", resolved.get("Tooltip", "Name"))
                self.assertEqual(f"{key}.description", resolved.get("Buildable", "Description"))
                block = fluent_block(self.d2k_fluent, key)
                self.assertTrue(block, key)
                self.assertNotRegex(block, r"(?m)^\s*\.name\s*=.*\bDU\s*$")
                self.assertNotIn(r"\n", block)

                description = block.split(".description = ", 1)[1].splitlines()
                self.assertTrue(description[0].endswith("."), (actor, description[0]))
                for detail in (line.strip() for line in description[1:] if line.strip()):
                    self.assertTrue(detail.startswith(allowed_detail_lines), (actor, detail))

                copy = "\n".join(description)
                if "Detects cloaked units" in copy:
                    self.assertIsNotNone(resolved.child("DetectCloaked"), actor)
                if "Transports " in copy:
                    self.assertTrue(
                        resolved.child("Cargo") is not None
                        or resolved.child("Carryall") is not None
                        or resolved.child("AutoCarryall") is not None,
                        actor,
                    )
                if any(term in copy for term in ("Cloaked ", "Stealth bomber", "Can gain stealth")):
                    self.assertIsNotNone(resolved.child("Cloak"), actor)


if __name__ == "__main__":
    unittest.main()
