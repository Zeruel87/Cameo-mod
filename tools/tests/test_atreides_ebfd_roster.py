"""Focused static contract for the EBFD Atreides completion batch.

The archive supplied for this batch is represented by nine new Atreides visual
families already present in ``mods/cameo/bits/d2k``.  This test pins their
provenance and checks the active ruleset resolves the actors, sequences,
weapons, promotion gates, and global bot roster without relying on a game boot.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from cameo_model import Model  # noqa: E402


ARCHIVE_SHA256 = "8b3223a8c57505fd2ad7286e2ff391aaa39bfc966ee1b06c1c391c5531da1224"

# These are the nine Atreides EBFD unit families added by the archive batch.
# Turret sheets are included where the actor's sequence consumes them.
ARCHIVE_ASSETS = {
    "atreides_airdrone": {
        "atreides_airdrone.png": "a72c5e019453e5dfccabd9d83963117e51230c832265c7b247e76f977e3db355",
        "atreides_airdrone_icon.png": "286375ce5813cbf50b1d661027dc68831e60939cd1ce439b559816131b869a3e",
    },
    "atreides_advancedcarryall": {
        "atreides_advancedcarryall.png": "2e38f3cf0793ad84395a8c65c9dfe8aa4ab9951443617ad22aeaf5bfbb191384",
        "atreides_advancedcarryall_icon.png": "ab3bd7c2705cc62dafd779a7977c45d36ffd7f234e4aa3fd324216f2a498d5cb",
    },
    "atreides_apc": {
        "atreides_apc.png": "4606f5c640053da0cbfbdb44a347cbc0d1a546a823471118bfe4ea3adfc8f032",
        "atreides_apc_turret.png": "63f11a0ecd745b0f6c966307baf5875f6dbc488fb5c2124b3b60a5cc43911c7a",
        "atreides_apc_icon.png": "42fb71ae1c86df8de0298547a9308c9ee54b1d5ee1d39a926fe103d6b4c235a0",
    },
    "atreides_minotaurus": {
        "atreides_minotaurus.png": "c9634eee6be5deeeb7608db89f9749dc14a53148e23e0778328e5c9da89f6797",
        "atreides_minotaurus_icon.png": "d0c4f0c80ab1ec32d8b28e69f3c25686c7619c748cf9d03a2d3b62b67c9aa564",
    },
    "atreides_mongoose": {
        "atreides_mongoose.png": "2a7d2b0370dec1fadd65bd1075318d9f829707f5adfb933647eb2b65298518db",
        "atreides_mongoose_turret.png": "e9e3fb01f11b643202b309ff1fbf39641ac2ef40d971635ea59ac51d974a0255",
        "atreides_mongoose_icon.png": "2f2475d8aa977a599287a593ac9436cd2e7a56a66bb8dd03c8e5fd3b8ff3aea9",
    },
    "atreides_ornithopter": {
        "atreides_ornithopter.png": "4dafee0ef3a3de0153e034ae5c3c564f66609fe25cc64f28cb41f461b9c83f39",
        "atreides_ornithopter_icon.png": "91cc7a4d8e479eb984076f9655231736eeefe69cbce0bf56da131d022a1f3af3",
    },
    "atreides_repairtank": {
        "atreides_repairtank.png": "788698f534d5e46adf5b39bfdbad6e5c1426466849f79a778eb4c7825a00d864",
        "atreides_repairtank_icon.png": "53e5af8ba93fa6bdbdfb90a2493a4e05603b7d9b68fbcfd2e7723cbb522584f8",
    },
    "atreides_sandbike": {
        "atreides_sandbike.png": "a377a7e7dd90f979f36960957a46d2ffeef131ce14999d57c639026171d424ff",
        "atreides_sandbike_icon.png": "dc2b6b16eb85c6251c6ece968168c30c15408d85411b9cff2aeb9563e31ec4b4",
    },
    "atreides_sonictank": {
        "atreides_sonictank.png": "e84771891eb9e627be96332c3de89cd7ae5c535975f2bc4d1713e077390ff0ea",
        "atreides_sonictank_icon.png": "7f2e7bcf02c68d3a66554352d9438e70f236d3c374af8bf38208390eb7b13612",
    },
}

ACTOR_TO_SEQUENCE = {
    "atreides_airdrone": "atreides_airdrone",
    "atreides_advancedcarryall": "atreides_advancedcarryall",
    "atreides_apc": "atreides_apc",
    "atreides_minotaurus": "atreides_minotaurus",
    "atreides_mongoose": "atreides_mongoose",
    "atreides_ornithopter": "ornithopter",
    "atreides_repairtank": "atreides_repairtank",
    "atreides_sandbike": "atreides_sandbike",
    "atreides_sonictank": "atreides_sonictank",
}

BUILD_ICONS = {
    "atreides_airdrone": "atreides_airdrone_build_icon.png",
    "atreides_advancedcarryall": "atreides_advancedcarryall_build_icon.png",
    "atreides_apc": "atreides_apc_build_icon.png",
    "atreides_minotaurus": "atreides_minotaurus_build_icon.png",
    "atreides_mongoose": "atreides_mongoose_build_icon.png",
    "atreides_ornithopter": "atreides_ornithopter_build_icon.png",
    "atreides_repairtank": "atreides_repairtank_build_icon.png",
    "atreides_sandbike": "atreides_sandbike_build_icon.png",
    "atreides_sonictank": "atreides_sonictank_build_icon.png",
}

PROMOTION_ORDER = [
    "atreides_promotion_fremen",
    "atreides_promotion_sonictank",
    "atreides_promotion_airdrone",
    "atreides_promotion_minotaurus",
    "atreides_promotion_mongoose",
]


def top_level_block(text: str, key: str) -> str:
    """Return one tab-indented YAML top-level block, including its key."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line == f"{key}:":
            end = index + 1
            while end < len(lines) and (not lines[end] or lines[end][0].isspace()):
                end += 1
            return "\n".join(lines[index:end])
    return ""


def child(node, key: str):
    return node.child(key) if node is not None else None


class AtreidesEbfdRosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = Model(ROOT)
        cls.rules = cls.model.rs
        cls.sequences_path = ROOT / "mods/cameo/ContentPacks/D2k/Atreides/yaml/sequences.yaml"
        cls.vehicles_path = ROOT / "mods/cameo/ContentPacks/D2k/Atreides/yaml/vehicles.yaml"
        cls.promotions_path = ROOT / "mods/cameo/ContentPacks/D2k/Atreides/yaml/promotions.yaml"
        cls.ai_path = ROOT / "mods/cameo/ai/ai.yaml"

    def test_archive_provenance_and_nine_assets_are_byte_identical(self):
        self.assertEqual(len(ARCHIVE_ASSETS), 9)
        self.assertRegex(ARCHIVE_SHA256, r"^[0-9a-f]{64}$")
        for files in ARCHIVE_ASSETS.values():
            for filename, expected_hash in files.items():
                path = ROOT / "mods/cameo/bits/d2k" / filename
                self.assertTrue(path.is_file(), filename)
                actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(actual_hash, expected_hash, filename)

    def test_nine_actors_resolve_to_archived_body_icon_and_turret_sequences(self):
        for actor, image in ACTOR_TO_SEQUENCE.items():
            resolved = self.rules.resolve(actor)
            self.assertIsNotNone(resolved, actor)
            render = child(resolved, "RenderSprites")
            self.assertIsNotNone(render, actor)
            self.assertEqual(render.get("Image"), image, actor)

            sequence = self.rules.sequence_image(image)
            self.assertIsNotNone(sequence, image)
            defaults = child(sequence, "Defaults")
            self.assertIsNotNone(defaults, image)
            body = defaults.get("Filename")
            self.assertTrue(body.endswith(".png"), image)
            self.assertIn(body, ARCHIVE_ASSETS[actor], body)

            icon = child(sequence, "icon")
            self.assertIsNotNone(icon, image)
            icon_file = icon.get("Filename")
            self.assertEqual(BUILD_ICONS[actor], icon_file)
            self.assertTrue((ROOT / "mods/cameo/bits/d2k" / icon_file).is_file(), icon_file)

            for trait in sequence.children:
                filename = trait.get("Filename")
                if filename and filename in ARCHIVE_ASSETS[actor]:
                    self.assertEqual(
                        hashlib.sha256((ROOT / "mods/cameo/bits/d2k" / filename).read_bytes()).hexdigest(),
                        ARCHIVE_ASSETS[actor][filename],
                    )

            for armament in resolved.children:
                if not armament.key.startswith("Armament"):
                    continue
                weapon = armament.get("Weapon")
                if weapon:
                    self.assertIsNotNone(self.rules.resolve_weapon(weapon), f"{actor}: {weapon}")

    def test_sonic_namespace_palette_and_classic_sequence_provenance(self):
        local = self.sequences_path.read_text(encoding="utf-8")
        vehicles = self.vehicles_path.read_text(encoding="utf-8")
        promotions = self.promotions_path.read_text(encoding="utf-8")
        global_sequences_path = ROOT / "mods/cameo/sequences/d2k.yaml"
        global_sequences = global_sequences_path.read_text(encoding="utf-8")

        self.assertIn("atreides_sonictank:\n", local)
        self.assertNotRegex(local, r"(?m)^sonic_tank:")
        self.assertNotIn("d2k_atreides_apc:", local)

        for block in (top_level_block(vehicles, "atreides_sonictank"),
                      top_level_block(vehicles, "sonic_tank_husk.atreides")):
            self.assertIn("Image: atreides_sonictank", block)
            self.assertIn("PlayerPalette: player_rgba", block)
        self.assertIn("Image: atreides_sonictank", top_level_block(promotions, "atreides_promotion_sonictank"))

        sonic = self.rules.sequence_image("atreides_sonictank")
        self.assertIsNotNone(sonic)
        self.assertEqual(child(sonic, "Defaults").get("Filename"), "atreides_sonictank.png")
        self.assertEqual(child(sonic, "idle").get("Length"), "8")
        self.assertEqual(child(sonic, "move").get("Length"), "8")
        self.assertEqual(child(sonic, "icon").get("Filename"), "atreides_sonictank_build_icon.png")
        sonic_actor = self.rules.resolve("atreides_sonictank")
        move_animation = child(sonic_actor, "WithMoveAnimation")
        self.assertIsNotNone(move_animation)
        self.assertEqual(move_animation.get("MoveSequence"), "move")

        classic = top_level_block(global_sequences, "sonic_tank")
        base_global = subprocess.run(
            ["git", "show", "9d04f7abf:mods/cameo/sequences/d2k.yaml"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertEqual(classic, top_level_block(base_global, "sonic_tank"))
        self.assertIn("d2k_atreides_apc:", global_sequences)

    def test_promotions_are_dependency_safe_and_bot_reachable(self):
        for actor in PROMOTION_ORDER:
            resolved = self.rules.resolve(actor)
            self.assertIsNotNone(resolved, actor)
            buildable = child(resolved, "Buildable")
            self.assertEqual(buildable.get("Queue"), "Promotions", actor)
            self.assertEqual(buildable.get("Factions"), "atreides", actor)

        prereqs = {
            actor: child(self.rules.resolve(actor), "Buildable").get("Prerequisites")
            for actor in PROMOTION_ORDER
        }
        self.assertIn("atreides_promotion_fremen", prereqs["atreides_promotion_sonictank"])
        self.assertIn("atreides_promotion_sonictank", prereqs["atreides_promotion_airdrone"])
        self.assertIn("atreides_promotion_sonictank", prereqs["atreides_promotion_minotaurus"])
        self.assertIn("atreides_promotion_minotaurus", prereqs["atreides_promotion_mongoose"])

        ai = self.ai_path.read_text(encoding="utf-8")
        units = top_level_block(ai, "Player")
        positions = []
        for actor in PROMOTION_ORDER:
            match = re.search(rf"(?m)^\t\t\t{re.escape(actor)}: (\d+)$", units)
            self.assertIsNotNone(match, actor)
            self.assertEqual(match.group(1), "1", actor)
            positions.append(match.start())
        self.assertEqual(positions, sorted(positions))
        self.assertIn("atreides_promotion_fremen: 1", units)
        self.assertIn("atreides_fremen: 3", units)
        self.assertIn("atreides_sonictank: 5", units)
        self.assertIn("atreides_minotaurus: 3", units)
        self.assertIn("atreides_mongoose: 5", units)
        self.assertIn("atreides_airdrone: 1", units)
        for actor, limit in {
            "atreides_spiceharvester": 20,
            "atreides_advancedcarryall": 5,
            "atreides_ornithopter": 10,
        }.items():
            self.assertRegex(units, rf"(?m)^\t\t\t{re.escape(actor)}: {limit}$")

        local_ai = (ROOT / "mods/cameo/ContentPacks/D2k/Atreides/yaml/ai.yaml").read_text(encoding="utf-8")
        self.assertIn("global mods/cameo/ai/ai.yaml", local_ai)
        self.assertNotIn("No faction-specific entries found", local_ai)

    def test_mongoose_muzzle_overlay_keeps_mtank_primary(self):
        mongoose = self.rules.resolve("atreides_mongoose")
        armament = child(mongoose, "Armament")
        self.assertEqual(armament.get("Weapon"), "mtank_pri")
        self.assertEqual(armament.get("MuzzleSequence"), "muzzle")
        self.assertEqual(armament.get("MuzzlePalette"), "d2keffect")
        self.assertIsNotNone(child(mongoose, "WithMuzzleOverlay"))
        self.assertIsNotNone(self.rules.resolve_weapon("mtank_pri"))
        self.assertNotIn("MongooseRocket", top_level_block(
            self.vehicles_path.read_text(encoding="utf-8"), "atreides_mongoose"))

    def test_removed_local_apc_sequence_has_no_active_atreides_reference(self):
        pack = ROOT / "mods/cameo/ContentPacks/D2k/Atreides/yaml"
        for path in pack.glob("*.yaml"):
            active_lines = [line.split("#", 1)[0] for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertNotIn("d2k_atreides_apc", "\n".join(active_lines), path.name)


if __name__ == "__main__":
    unittest.main()
