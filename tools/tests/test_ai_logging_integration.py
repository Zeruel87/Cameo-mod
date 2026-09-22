"""One active logging pipeline and a permanent loaded-save exclusion."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
from miniyaml import Ruleset


class AiLoggingIntegrationTests(unittest.TestCase):
    def test_only_the_upstream_logging_traits_are_active(self):
        rules = Ruleset(ROOT)
        player, world = rules.resolve("Player"), rules.resolve("World")
        self.assertIsNotNone(player.child("AiMatchLogRecorder"))
        self.assertIsNotNone(world.child("AiMatchLogWriter"))
        self.assertIsNone(player.child("CameoMatchPlayerState"))
        self.assertIsNone(world.child("CameoMatchRecorder"))

    def test_save_exclusion_is_captured_before_replay_in_clears_the_flag(self):
        source = (ROOT / "OpenRA.Mods.Cameo/Traits/AiMatchLogWriter.cs").read_text()
        load = source.split("void IWorldLoaded.WorldLoaded", 1)[1].split("void ITick.Tick", 1)[0]
        self.assertIn("eligibleAtWorldLoad = Eligible(world.Type, world.IsReplay, world.IsLoadingGameSave, Game.IsHost);", load)
        self.assertIn("written = true;", load)
        capture = source.split("void CaptureAndAppend", 1)[1].split("void TryAppend", 1)[0]
        self.assertLess(capture.index("!eligibleAtWorldLoad"), capture.index("BuildLog(world)"))
        self.assertEqual(1, source.count("eligibleAtWorldLoad ="))


if __name__ == "__main__":
    unittest.main()
