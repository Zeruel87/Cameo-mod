import pathlib
import sys
import unittest
from subprocess import CompletedProcess
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from promote_compatibility_warheads import require_clean_checkout  # noqa: E402


class CompatibilityPromotionSafetyTests(unittest.TestCase):
    @patch("promote_compatibility_warheads.subprocess.run")
    def test_dirty_checkout_is_rejected_before_mutation(self, run):
        run.return_value = CompletedProcess(
            ["git", "status"], 0, stdout=" M mods/cameo/weapons/weapons.yaml\n")
        with self.assertRaisesRegex(RuntimeError, "dirty checkout"):
            require_clean_checkout()
        run.assert_called_once()

    @patch("promote_compatibility_warheads.subprocess.run")
    def test_clean_checkout_is_allowed(self, run):
        run.return_value = CompletedProcess(
            ["git", "status"], 0, stdout="")
        require_clean_checkout()
        args = run.call_args.args[0]
        self.assertEqual(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"], args)


if __name__ == "__main__":
    unittest.main()
