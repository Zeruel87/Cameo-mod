"""Focused proof checks for the R12 pure-rename writer and landed cohort."""

import json
import pathlib
import sys
import tempfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import rename_r12_compatibility_cohort as writer  # noqa: E402
from rename_r12_compatibility_cohort import resolved_dump, stale_source_references  # noqa: E402
from miniyaml import Ruleset  # noqa: E402


PROOF = json.loads((
    ROOT / "docs" / "audit" / "latest" / "r12_pure_rename_proof_20260913.json"
).read_text(encoding="utf-8"))


def test_frozen_maps_are_complete_unique_and_collision_free():
    templates = PROOF["template_renames"]
    payloads = PROOF["payload_renames"]
    assert len(templates) == len(set(templates.values())) == 36
    assert len(payloads) == len(set(payloads.values())) == 36
    assert payloads["LaserExtraDamageCompatibility"] == "LaserExtraDamage_Auxiliary"
    assert payloads["RailgunExtraDamageCompatibility"] == "RailgunExtraDamage_Auxiliary"
    assert PROOF["counts"]["source_replacements"] == 1027
    assert PROOF["resolved_dump"]["byte_identical_after_baseline_name_map"] is True


def test_current_tree_contains_only_the_renamed_cohort():
    rs = Ruleset(str(ROOT))
    templates = PROOF["template_renames"]
    payloads = PROOF["payload_renames"]
    assert not (set(templates) & set(rs.weapons))
    assert set(templates.values()) <= set(rs.weapons)
    assert stale_source_references(writer.active_sources(rs), templates, payloads) == []
    runtime_sources = writer.tracked_runtime_sources()
    assert len(runtime_sources) >= 1000
    assert stale_source_references(runtime_sources, templates, payloads) == []
    python_sources = writer.tracked_python_sources()
    assert len(python_sources) >= 100
    assert writer.python_reference_issues(python_sources, templates, payloads) == []
    archives = writer.tracked_oramap_archives()
    assert len(archives) >= 300
    assert writer.stale_oramap_references(archives, templates, payloads) == []


def test_canonical_dump_covers_templates_and_concrete_weapons():
    rs = Ruleset(str(ROOT))
    dump = resolved_dump(rs, {})
    assert dump.startswith(b'{"')
    assert len(rs.weapons) > 2448
    assert b'Wraith_ToxinMissiles' in dump


def transaction_patches(path, *, dirty=(), rewrite_side_effect=None):
    return (
        mock.patch.object(writer, "Ruleset", return_value=object()),
        mock.patch.object(writer, "rename_maps", return_value=(
            {"^Compatibility_X": "^Warhead_X"}, {"XCompatibility": "X"}, {})),
        mock.patch.object(writer, "active_sources", return_value=[path]),
        mock.patch.object(writer, "affected_sources", return_value=[path]),
        mock.patch.object(writer, "dirty_paths", return_value=list(dirty)),
        mock.patch.object(writer, "rewrite", side_effect=rewrite_side_effect),
        mock.patch.object(writer, "python_reference_issues", return_value=[]),
    )


def test_runtime_consumer_outside_active_sources_refuses_before_rewrite():
    with tempfile.TemporaryDirectory() as directory:
        active = pathlib.Path(directory) / "active.yaml"
        outside = pathlib.Path(directory) / "consumer.cs"
        active.write_text("^Compatibility_X", encoding="utf-8")
        outside.write_text("XCompatibility", encoding="utf-8")
        with (
            mock.patch.object(writer, "Ruleset", return_value=object()),
            mock.patch.object(writer, "rename_maps", return_value=(
                {"^Compatibility_X": "^Warhead_X"}, {"XCompatibility": "X"}, {})),
            mock.patch.object(writer, "active_sources", return_value=[active]),
            mock.patch.object(writer, "tracked_runtime_sources", return_value=[active, outside]),
            mock.patch.object(writer, "python_reference_issues", return_value=[]),
            mock.patch.object(writer, "norm", side_effect=lambda path: path.name),
            mock.patch.object(writer, "rewrite") as rewrite,
        ):
            try:
                writer.run(apply=False)
            except RuntimeError as exc:
                assert "outside active rule/weapon sources" in str(exc)
            else:
                raise AssertionError("outside runtime consumer must refuse")
            rewrite.assert_not_called()


def test_unreviewed_python_consumer_refuses_before_rewrite():
    with tempfile.TemporaryDirectory() as directory:
        active = pathlib.Path(directory) / "active.yaml"
        active.write_text("^Compatibility_X", encoding="utf-8")
        with (
            mock.patch.object(writer, "Ruleset", return_value=object()),
            mock.patch.object(writer, "rename_maps", return_value=(
                {"^Compatibility_X": "^Warhead_X"}, {"XCompatibility": "X"}, {})),
            mock.patch.object(writer, "active_sources", return_value=[active]),
            mock.patch.object(writer, "affected_sources", side_effect=[[active], []]),
            mock.patch.object(writer, "tracked_runtime_sources", return_value=[]),
            mock.patch.object(writer, "tracked_python_sources", return_value=[]),
            mock.patch.object(writer, "python_reference_issues", return_value=[{
                "file": "tools/new_consumer.py", "issue": "unreviewed legacy reference"}]),
            mock.patch.object(writer, "rewrite") as rewrite,
        ):
            try:
                writer.run(apply=False)
            except RuntimeError as exc:
                assert "Python tooling" in str(exc)
                assert "tools/new_consumer.py" in str(exc)
            else:
                raise AssertionError("unreviewed Python consumer must refuse")
            rewrite.assert_not_called()


def test_bare_payload_inside_oramap_is_detected():
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "consumer.oramap"
        with writer.zipfile.ZipFile(path, "w") as archive:
            archive.writestr("rules.yaml", "Payload: XCompatibility\n")
        with mock.patch.object(writer, "norm", return_value="consumer.oramap"):
            rows = writer.stale_oramap_references(
                [path], {"^Compatibility_X": "^Warhead_X"},
                {"XCompatibility": "X"})
        assert rows == [{
            "file": "consumer.oramap", "member": "rules.yaml",
            "line": 1, "tokens": ["XCompatibility"],
        }]


def test_undecodable_oramap_text_member_refuses():
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "consumer.oramap"
        with writer.zipfile.ZipFile(path, "w") as archive:
            archive.writestr("rules.yaml", b"\xff\xfe\x00")
        with mock.patch.object(writer, "norm", return_value="consumer.oramap"):
            try:
                writer.stale_oramap_references(
                    [path], {"^Compatibility_X": "^Warhead_X"},
                    {"XCompatibility": "X"})
            except RuntimeError as exc:
                assert "consumer.oramap!rules.yaml" in str(exc)
            else:
                raise AssertionError("undecodable tracked map text must refuse")


def test_python_inventory_detects_literal_and_generated_legacy_references():
    templates = PROOF["template_renames"]
    payloads = PROOF["payload_renames"]
    old_template = next(iter(templates))
    old_payload = next(iter(payloads))
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "consumer.py"
        path.write_text(
            f'LITERAL_TEMPLATE = "{old_template}"\n'
            f'LITERAL_PAYLOAD = "{old_payload}"\n'
            'generated_template = f"^Compatibility_{destination}Flat"\n'
            'generated_payload = f"{destination}FlatCompatibility"\n'
            'formatted_template = "^Compatibility_{}Flat".format(destination)\n'
            'joined_template = "^Compatibility_" + destination + "Flat"\n'
            'percent_payload = "%sFlatCompatibility" % destination\n'
            'formatted_payload = "{}FlatCompatibility".format(destination)\n',
            encoding="utf-8")
        with mock.patch.object(writer, "norm", return_value="tools/consumer.py"):
            records = writer.python_reference_records([path], templates, payloads)
        assert records["tools/consumer.py"] == sorted([
            f'LITERAL_TEMPLATE = "{old_template}"',
            f'LITERAL_PAYLOAD = "{old_payload}"',
            'generated_template = f"^Compatibility_{destination}Flat"',
            'generated_payload = f"{destination}FlatCompatibility"',
            'formatted_template = "^Compatibility_{}Flat".format(destination)',
            'joined_template = "^Compatibility_" + destination + "Flat"',
            'percent_payload = "%sFlatCompatibility" % destination',
            'formatted_payload = "{}FlatCompatibility".format(destination)',
        ])


def test_python_allowlist_accepts_exact_reviewed_lines_and_rejects_changes():
    templates = PROOF["template_renames"]
    payloads = PROOF["payload_renames"]
    with tempfile.TemporaryDirectory() as directory:
        directory = pathlib.Path(directory)
        path = directory / "consumer.py"
        allowlist_path = directory / "allowlist.json"
        path.write_text(
            'generated_template = f"^Compatibility_{destination}Flat"\n',
            encoding="utf-8")
        with mock.patch.object(writer, "norm", return_value="tools/consumer.py"):
            records = writer.python_reference_records([path], templates, payloads)
            lines = records["tools/consumer.py"]
            allowlist_path.write_text(json.dumps({
                "schema": 1,
                "files": {
                    "tools/consumer.py": {
                        "count": len(lines),
                        "sha256": writer.python_reference_digest(lines),
                        "reason": "Reviewed historical fixture.",
                    },
                },
            }), encoding="utf-8")
            assert writer.python_reference_issues(
                [path], templates, payloads, allowlist_path) == []

            assert writer.python_reference_issues(
                [], templates, payloads, allowlist_path) == [{
                    "file": "tools/consumer.py", "issue": "stale allowlist entry"}]

            path.write_text(
                path.read_text(encoding="utf-8")
                + 'generated_payload = f"{destination}FlatCompatibility"\n',
                encoding="utf-8")
            issues = writer.python_reference_issues(
                [path], templates, payloads, allowlist_path)
        assert issues[0]["issue"] == "reviewed legacy references changed"


def test_interrupted_write_restores_affected_file():
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "active.yaml"
        path.write_bytes(b"original")

        def interrupt(_paths, _replacements):
            path.write_bytes(b"partial rename")
            raise KeyboardInterrupt()

        patches = transaction_patches(path, rewrite_side_effect=interrupt)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
            try:
                writer.run(apply=False)
            except KeyboardInterrupt:
                pass
            else:
                raise AssertionError("KeyboardInterrupt should escape after rollback")
        assert path.read_bytes() == b"original"


def test_dirty_file_refuses_before_rewrite():
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "active.yaml"
        path.write_bytes(b"original")
        patches = transaction_patches(path, dirty=(" M active.yaml",))
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as rewrite, patches[6]:
            try:
                writer.run(apply=False)
            except RuntimeError as exc:
                assert "dirty" in str(exc)
            else:
                raise AssertionError("dirty affected source must refuse")
            rewrite.assert_not_called()


def test_proof_output_cannot_overlap_active_source():
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "active.yaml"
        path.write_bytes(b"original")
        patches = transaction_patches(path)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as rewrite, patches[6]:
            try:
                writer.run(apply=False, proof_path=path)
            except RuntimeError as exc:
                assert "overlaps active source" in str(exc)
            else:
                raise AssertionError("proof/source overlap must refuse")
            rewrite.assert_not_called()


if __name__ == "__main__":
    test_frozen_maps_are_complete_unique_and_collision_free()
    test_current_tree_contains_only_the_renamed_cohort()
    test_runtime_consumer_outside_active_sources_refuses_before_rewrite()
    test_unreviewed_python_consumer_refuses_before_rewrite()
    test_bare_payload_inside_oramap_is_detected()
    test_undecodable_oramap_text_member_refuses()
    test_python_inventory_detects_literal_and_generated_legacy_references()
    test_python_allowlist_accepts_exact_reviewed_lines_and_rejects_changes()
    test_canonical_dump_covers_templates_and_concrete_weapons()
    test_interrupted_write_restores_affected_file()
    test_dirty_file_refuses_before_rewrite()
    test_proof_output_cannot_overlap_active_source()
    print("R12 rename proof fixtures: PASS")
