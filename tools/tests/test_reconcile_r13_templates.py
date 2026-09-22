"""Focused checks for the R13 reconciliation report."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from reconcile_r13_templates import (  # noqa: E402
    build_report,
    normalized_inner_key,
    payload_signature,
)


class Node:
    def __init__(self, key, value="", children=()):
        self.key = key
        self.value = value
        self.children = list(children)


def test_compatibility_suffix_is_removed_without_changing_payload_role():
    assert normalized_inner_key("Warhead@LaserExtraDamageCompatibility") == \
        "Warhead@LaserExtraDamage"
    assert normalized_inner_key("Warhead@TankBusterBeamUnscopedCompatibility") == \
        "Warhead@TankBusterBeamUnscoped"


def test_current_r13_count_distinguishes_definitions_from_users():
    report = build_report()
    assert report["counts"] == {
        "missing_template_definitions": 3,
        "direct_relationships": 16,
        "distinct_weapons": 14,
        "with_exact_legacy_payload": 2,
        "family_level_generator_targets": 0,
    }


def test_payload_equality_includes_warhead_type():
    fields = [Node("Damage", "100")]
    spread = Node("Warhead@X", "SpreadDamage", fields)
    area = Node("Warhead@Y", "AreaDamage", fields)
    assert payload_signature(spread) != payload_signature(area)


if __name__ == "__main__":
    test_compatibility_suffix_is_removed_without_changing_payload_role()
    test_current_r13_count_distinguishes_definitions_from_users()
    test_payload_equality_includes_warhead_type()
    print("R13 reconciliation fixtures: PASS")
