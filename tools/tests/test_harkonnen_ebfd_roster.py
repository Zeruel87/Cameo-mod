"""Static contract for the Harkonnen EBFD identity and promotion batch."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Node, Ruleset, load  # noqa: E402


EBFD_ACTORS = (
    "harkonnen_assaulttank",
    "harkonnen_flametank",
    "harkonnen_devastatormech",
    "harkonnen_buzzsaw",
    "harkonnen_rockettank",
    "harkonnen_inkvine",
    "harkonnen_gunship",
    "harkonnen_adp",
    "harkonnen_advancedcarryall",
)

PROMOTIONS = {
    "harkonnen_promotion_assaulttank": "harkonnen_assaulttank",
    "harkonnen_promotion_flametank": "harkonnen_flametank",
    "harkonnen_promotion_devastatormech": "harkonnen_devastatormech",
    "harkonnen_promotion_buzzsaw": "harkonnen_buzzsaw",
    "harkonnen_promotion_rockettank": "harkonnen_rockettank",
    "harkonnen_promotion_inkvine": "harkonnen_inkvine",
    "harkonnen_promotion_gunship": "harkonnen_gunship",
    "harkonnen_promotion_adp": "harkonnen_adp",
    "harkonnen_promotion_advancedcarryall": "harkonnen_advancedcarryall",
}

BRANCHES = (
    (
        "harkonnen_promotion_assaulttank",
        "harkonnen_promotion_flametank",
        "harkonnen_promotion_devastatormech",
    ),
    (
        "harkonnen_promotion_buzzsaw",
        "harkonnen_promotion_rockettank",
        "harkonnen_promotion_inkvine",
    ),
    (
        "harkonnen_promotion_gunship",
        "harkonnen_promotion_adp",
        "harkonnen_promotion_advancedcarryall",
    ),
)

CLASSIC_SEQUENCE_STARTS = {
    "combat_tank.harkonnen": {
        "idle": 2051,
        "turret": 2115,
        "muzzle": 4028,
        "icon": 4282,
    },
    "missile_tank": {"idle": 1603, "icon": 4285},
    "devastator": {"idle": 2083, "muzzle": 4060, "active": 3839},
}

D2K_UPGRADE_IMAGES = {
    "upgrade_conyard.harkonnen": "conyard.harkonnen",
    "upgrade_barracks.harkonnen": "barracks.harkonnen",
    "upgrade_light.harkonnen": "light.harkonnen",
    "upgrade_heavy.harkonnen": "heavy.harkonnen",
    "upgrade_radar.harkonnen": "outpost.harkonnen",
    "upgrade_conyard.atreides": "conyard.atreides",
    "upgrade_barracks.atreides": "barracks.atreides",
    "upgrade_light.atreides": "light.atreides",
    "upgrade_heavy.atreides": "heavy.atreides",
    "upgrade_radar.atreides": "outpost.atreides",
    "upgrade_conyard.corrino": "conyard.harkonnen",
    "upgrade_barracks.corrino": "barracks.harkonnen",
    "upgrade_light.corrino": "light.harkonnen",
    "upgrade_heavy.corrino": "heavy.harkonnen",
    "upgrade_radar.corrino": "outpost.harkonnen",
}


def walk(node: Node):
    yield node
    for child in node.children:
        yield from walk(child)


def prereq_tokens(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


class HarkonnenEbfdRosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.ebfd_dir = ROOT / "mods/cameo/ContentPacks/D2k/Harkonnen/yaml"
        cls.asset_dir = ROOT / "mods/cameo/bits/d2k"

    def test_nine_distinct_actors_and_sequences(self):
        self.assertEqual(9, len(set(EBFD_ACTORS)))
        for actor_name in EBFD_ACTORS:
            with self.subTest(actor=actor_name):
                actor = self.rules.resolve(actor_name)
                self.assertIsNotNone(actor)
                sequence = self.rules.sequence_image(actor_name)
                self.assertIsNotNone(sequence)
                self.assertEqual(actor_name, actor.get("RenderSprites", "Image"))
                self.assertEqual(
                    actor_name,
                    sequence.key,
                )
                self.assertIsNotNone(sequence.child("idle"))
                self.assertIsNotNone(sequence.child("icon"))

    def test_historical_assault_tank_role_and_cadence(self):
        actor = self.rules.resolve("harkonnen_assaulttank")
        source_actor = self.rules.actor("harkonnen_assaulttank")
        self.assertEqual("^FrontalEMP", source_actor.child("Inherits@EMP").value)
        self.assertEqual("actor_harkonnen_assaulttank.name", actor.get("Tooltip", "Name"))
        self.assertEqual("600", actor.get("Valued", "Cost"))
        self.assertEqual("70000", actor.get("Health", "HP"))
        self.assertEqual("Heavy", actor.get("Armor", "Type"))
        self.assertEqual("65", actor.get("Mobile", "Speed"))
        self.assertEqual("80mm_H", actor.get("Armament", "Weapon"))
        self.assertIsNotNone(actor.child("AttackFrontal"))
        self.assertIsNone(actor.child("AttackTurreted"))
        self.assertIsNone(actor.child("Turreted"))
        weapon = self.rules.resolve_weapon("80mm_H")
        self.assertIsNotNone(weapon)
        self.assertEqual("55", weapon.get("ReloadDelay"))

    def test_classic_data_r16_sequences_keep_exact_starts(self):
        for sequence_name, starts in CLASSIC_SEQUENCE_STARTS.items():
            sequence = self.rules.sequence_image(sequence_name)
            self.assertIsNotNone(sequence, sequence_name)
            for child_name, start in starts.items():
                with self.subTest(sequence=sequence_name, child=child_name):
                    child = sequence.child(child_name)
                    self.assertIsNotNone(child)
                    self.assertEqual("DATA.R16", child.get("Filename"))
                    self.assertEqual(str(start), child.get("Start"))

        for actor_name in ("combat_tank.harkonnen", "missile_tank", "devastator"):
            prerequisites = self.rules.resolve(actor_name).get("Buildable", "Prerequisites")
            self.assertNotIn("harkonnen_promotion_", prerequisites or "", actor_name)

    def test_promotions_are_one_to_one_and_form_three_branches(self):
        self.assertEqual(9, len(PROMOTIONS))
        orders = []
        for promotion_name, consumer_name in PROMOTIONS.items():
            promotion = self.rules.resolve(promotion_name)
            consumer = self.rules.resolve(consumer_name)
            self.assertIsNotNone(promotion, promotion_name)
            self.assertIsNotNone(consumer, consumer_name)
            buildable = promotion.child("Buildable")
            self.assertEqual("harkonnen", buildable.get("Factions"), promotion_name)
            self.assertEqual("Promotions", buildable.get("Queue"), promotion_name)
            self.assertIn("~harkonnen_constructionyard", prereq_tokens(buildable.get("Prerequisites")))
            self.assertIn("rank1", prereq_tokens(buildable.get("Prerequisites")))
            self.assertIn("!" + promotion_name, prereq_tokens(buildable.get("Prerequisites")))
            orders.append(int(buildable.get("BuildPaletteOrder")))

            consumer_prereqs = prereq_tokens(consumer.get("Buildable", "Prerequisites"))
            self.assertEqual(
                ["~" + promotion_name],
                [token for token in consumer_prereqs if "promotion_" in token],
                consumer_name,
            )

        self.assertEqual(list(range(109, 134, 3)), orders)
        for branch in BRANCHES:
            for previous, current in zip(branch, branch[1:]):
                self.assertIn(previous, prereq_tokens(self.rules.resolve(current).get("Buildable", "Prerequisites")))

    def test_ai_has_promotions_new_units_and_dependency_safe_order(self):
        player = self.rules.resolve("Player")
        unit_builder = player.child("UnitBuilderBotModuleCA@generic")
        units = unit_builder.child("UnitsToBuild")
        self.assertIsNotNone(units)
        names = [child.key for child in units.children]
        for promotion_name in PROMOTIONS:
            self.assertIn(promotion_name, names)
        self.assertIn("harkonnen_assaulttank", names)
        self.assertIn("harkonnen_rockettank", names)
        self.assertIn("missile_tank", names)
        for promotion_name, consumer_name in PROMOTIONS.items():
            self.assertLess(names.index(promotion_name), names.index(consumer_name), consumer_name)

    def test_assets_are_mapped_and_assault_assets_are_no_longer_unused(self):
        for actor_name in EBFD_ACTORS:
            sequence = self.rules.sequence_image(actor_name)
            body = sequence.child("Defaults").get("Filename")
            icon = sequence.child("icon").get("Filename")
            with self.subTest(actor=actor_name, asset=body):
                self.assertTrue((self.asset_dir / body).is_file())
            with self.subTest(actor=actor_name, asset=icon):
                self.assertTrue((self.asset_dir / icon).is_file())

        assault_sequence_text = (self.ebfd_dir / "sequences.yaml").read_text(encoding="utf-8")
        self.assertIn("Filename: harkonnen_assaulttank.png", assault_sequence_text)
        self.assertIn("Filename: harkonnen_assaulttank_icon.png", assault_sequence_text)

    def test_d2k_building_upgrades_have_production_palette_icons(self):
        for actor_name, image_name in D2K_UPGRADE_IMAGES.items():
            with self.subTest(actor=actor_name):
                actor = self.rules.resolve(actor_name)
                self.assertEqual("Upgrades", actor.get("Buildable", "Queue"))
                self.assertEqual(image_name, actor.get("RenderSprites", "Image"))
                sequence = self.rules.sequence_image(image_name)
                self.assertIsNotNone(sequence, image_name)
                self.assertIsNotNone(sequence.child("icon"), image_name)

    def test_dead_devastator_husk_sequence_has_no_active_reference(self):
        self.assertIsNone(self.rules.sequence_image("devastator_husk.harkonnen"))
        live_refs = [
            node.value
            for path in (*self.rules.manifest.rules, *self.rules.manifest.sequences, *self.rules.manifest.weapons)
            for top in load(path)
            for node in walk(top)
            if node.value == "devastator_husk.harkonnen" or node.key == "devastator_husk.harkonnen"
        ]
        self.assertEqual([], live_refs)

    def test_actor_sequence_and_weapon_resolution(self):
        for actor_name in EBFD_ACTORS:
            actor = self.rules.resolve(actor_name)
            image = actor.get("RenderSprites", "Image")
            self.assertIsNotNone(self.rules.sequence_image(image), actor_name)
            for armament in actor.children_named("Armament"):
                weapon_name = armament.get("Weapon")
                if weapon_name:
                    self.assertIsNotNone(self.rules.resolve_weapon(weapon_name), (actor_name, weapon_name))


if __name__ == "__main__":
    unittest.main()
