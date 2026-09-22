"""Safety regressions for the generated carrier-ammo writer."""

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from apply_carrier_slave_ammo import (  # noqa: E402
    apply_with_cleanup,
    checked_plan_paths,
    dirty_plan_paths,
)


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_writer_checks_only_affected_active_paths():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        active = root / "active.yaml"
        unrelated = root / "unrelated.yaml"
        active.write_text("Actor:\n", encoding="utf-8")
        unrelated.write_text("Other:\n", encoding="utf-8")
        git(root, "init")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "test")
        git(root, "add", "active.yaml", "unrelated.yaml")
        git(root, "commit", "-m", "fixture")

        plan = {str(active): {1: [("ins", ["\tField: value"])]}}
        paths = checked_plan_paths(root, [active, unrelated], plan)
        assert paths == ["active.yaml"]

        unrelated.write_text("Other:\n\tUserWork: true\n", encoding="utf-8")
        assert dirty_plan_paths(root, paths) == []

        active.write_text("Actor:\n\tUserWork: true\n", encoding="utf-8")
        assert dirty_plan_paths(root, paths), "affected dirty file must refuse the writer"


def test_writer_rejects_paths_outside_active_manifest():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        active = root / "active.yaml"
        inactive = root / "inactive.yaml"
        active.write_text("Actor:\n", encoding="utf-8")
        inactive.write_text("Other:\n", encoding="utf-8")
        try:
            checked_plan_paths(root, [active], {str(inactive): {}})
        except ValueError as exc:
            assert "not an active rules file" in str(exc)
        else:
            raise AssertionError("inactive plan path was accepted")


def test_writer_rolls_back_failed_mutation_without_touching_unrelated_work():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        active = root / "active.yaml"
        unrelated = root / "unrelated.yaml"
        active.write_text("Actor:\n", encoding="utf-8")
        unrelated.write_text("Other:\n", encoding="utf-8")
        git(root, "init")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "test")
        git(root, "add", "active.yaml", "unrelated.yaml")
        git(root, "commit", "-m", "fixture")

        original = active.read_bytes()
        unrelated.write_text("Other:\n\tUserWork: true\n", encoding="utf-8")
        unrelated_work = unrelated.read_bytes()
        plan = {"active.yaml": {1: [("ins", ["\tGenerated: true"])]}}

        def fail_after_write(_edits):
            raise RuntimeError("injected post-write failure")

        try:
            apply_with_cleanup(plan, root, ["active.yaml"], False, fail_after_write)
        except RuntimeError as exc:
            assert "injected post-write failure" in str(exc)
        else:
            raise AssertionError("injected failure did not propagate")

        assert active.read_bytes() == original
        assert unrelated.read_bytes() == unrelated_work


if __name__ == "__main__":
    test_writer_checks_only_affected_active_paths()
    test_writer_rejects_paths_outside_active_manifest()
    test_writer_rolls_back_failed_mutation_without_touching_unrelated_work()
    print("carrier-ammo writer safety fixtures: PASS")
