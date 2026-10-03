"""Production-palette geometry contract for active D2K PNG icons."""

from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset  # noqa: E402


BITS = ROOT / "mods/cameo/bits/d2k"

DERIVED_BUILD_ICONS = {
    "atreides_advancedcarryall": ("atreides_advancedcarryall_build_icon.png", "3648f0711e74e154ad52b9ac426e7ac3991c5502fee51d8961c149308467bf1d"),
    "atreides_airdrone": ("atreides_airdrone_build_icon.png", "983d3314a0af3efaf13f7a1230c341100992927b8256a4c60dd1c0d75ea0a388"),
    "atreides_apc": ("atreides_apc_build_icon.png", "74384c256ab40ca057e1dbfb7610d7a752435222fb0b0d194a24791b86efcdbc"),
    "atreides_minotaurus": ("atreides_minotaurus_build_icon.png", "6048511a03cc254fe8a2c132b44ba958f26df3120c4426322ad98e866cca9ab0"),
    "atreides_mongoose": ("atreides_mongoose_build_icon.png", "31b4b368a17ceaa633d4ee2e3dcc420d18c57381261225e7ec2b55853643c1c4"),
    "atreides_ornithopter": ("atreides_ornithopter_build_icon.png", "728e92b55d2a91c37ffea369ab1f9757db812ebb97940da149fa2ccce215ccb4"),
    "atreides_repairtank": ("atreides_repairtank_build_icon.png", "13271db0f2b120c5723a9bef272709a737c99a9e242a60b825dfed36f3289926"),
    "atreides_sandbike": ("atreides_sandbike_build_icon.png", "359269efca826134c999855d90275c5e4d1ff461f97253b491e91385c9994129"),
    "atreides_sonictank": ("atreides_sonictank_build_icon.png", "8b12eef41d186bcc9458675a9c8944c5e33a9662843356a5fed6228f926ae7e6"),
    "atreides_spiceharvester": ("atreides_harvester_build_icon.png", "c88f157b6162fca0ab9579b4642d4021256023fa2e3cb07372c33b23be1190df"),
    "corrino_apc": ("corrino_apc_build_icon.png", "bafdbff47138caab790e7e6bb49081144609ec68277ce244cad5f74cdf05bd3d"),
    "harkonnen_devastatorturret": ("harkonnen_devastatorturret_build_icon.png", "bc372a692a64d61e803ecc6a91c3c555cb7d110fae9a1922f2001a437a60ac2f"),
    "ordos_chemturret": ("ordos_chemtur_build_icon.png", "0f0a17e59fa181ba0922241bf4c2c934cbb9e4ba88e549f39c42060e3438d815"),
    "ordos_laserturret": ("ordos_lasertur_build_icon.png", "e2f8694fd6377ff223ca0d56af6d294546e14c585b3b97340e54c0b6592e9df1"),
}


def png_size(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise AssertionError(f"{path} is not a PNG with an IHDR header")
    return struct.unpack(">II", payload[16:24])


class D2KProductionIconGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_derived_icons_are_standard_64_by_48_and_pinned(self):
        for actor_name, (filename, expected_hash) in DERIVED_BUILD_ICONS.items():
            with self.subTest(actor=actor_name):
                actor = self.rules.resolve(actor_name)
                image = actor.get("RenderSprites", "Image") or actor_name
                sequence = self.rules.sequence_image(image)
                self.assertIsNotNone(sequence, image)
                self.assertEqual(filename, sequence.child("icon").get("Filename"))
                path = BITS / filename
                self.assertEqual((64, 48), png_size(path))
                self.assertEqual(expected_hash, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_no_active_d2k_buildable_png_icon_exceeds_standard_canvas(self):
        failures = []
        for actor_name in sorted(self.rules.actors):
            if actor_name.startswith("^"):
                continue
            actor = self.rules.resolve(actor_name)
            buildable = actor.child("Buildable")
            render = actor.child("RenderSprites")
            if buildable is None or not buildable.get("Queue") or render is None:
                continue

            image = render.get("Image") or actor_name
            sequence = self.rules.sequence_image(image)
            if sequence is None or sequence.child("icon") is None:
                continue

            filename = sequence.child("icon").get("Filename")
            if not filename or not filename.lower().endswith(".png"):
                continue

            identity = " ".join((actor_name, buildable.get("Factions") or "",
                                 buildable.get("Prerequisites") or "", filename)).lower()
            if not any(token in identity for token in ("atreides", "harkonnen", "ordos", "corrino", "ixian", "d2k")):
                continue

            path = BITS / Path(filename).name
            if not path.is_file():
                continue
            width, height = png_size(path)
            if width > 64 or height > 48:
                failures.append(f"{actor_name}: {filename} is {width}x{height}")

        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
