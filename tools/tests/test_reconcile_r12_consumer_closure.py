"""Focused checks for the frozen R12 audit and the landed rename state."""

import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from reconcile_r12_consumer_closure import build_report  # noqa: E402


FROZEN_REPORT = json.loads((
    ROOT / "docs" / "audit" / "latest" / "r12_consumer_closure_20260913.json"
).read_text(encoding="utf-8"))
CURRENT_REPORT = build_report()


def test_frozen_inventory_includes_the_template_consumer():
    report = FROZEN_REPORT
    assert report["counts"] == {
        "compatibility_templates": 36,
        "all_direct_relationships": 370,
        "concrete_weapon_relationships": 369,
        "template_relationships": 1,
        "distinct_concrete_weapons": 361,
        "distinct_template_consumers": 1,
        "already_inherits_twin_all_consumers": 140,
        "exposed_without_twin_all_consumers": 214,
        "missing_twin_all_consumers": 16,
    }
    assert report["template_consumers"] == [{
        "consumer": "^Warhead_IncendiaryYakComposition",
        "consumer_kind": "template",
        "file": "mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml",
        "line": 1710,
        "compatibility_template": "^Compatibility_Flame_LightFlat",
        "matching_twin": "^Warhead_Flame_Light",
        "classification": "already_inherits_twin",
    }]


def test_literal_chain_proposal_fails_the_order_aware_gate():
    simulation = FROZEN_REPORT["simulation"]
    assert simulation["changed_concrete_weapons_in_full_descendant_closure"] == 290
    assert simulation["warhead_order_changes"] == 287
    assert simulation["pure_warhead_reorders"] == 101
    already = simulation["direct_consumer_groups"]["already_inherits_twin"]
    measures = (already["changed_direct_weapons"], already["warhead_order_changes"],
                already["pure_warhead_reorders"], already["with_field_deltas"])
    assert measures == (30, 30, 27, 3)


def test_pure_rename_preserves_every_resolved_weapon_and_avoids_payload_collisions():
    rename = FROZEN_REPORT["pure_rename_simulation"]
    assert rename["changed_concrete_weapons"] == 0
    assert rename["collision_avoidance"] == {
        "LaserExtraDamageCompatibility": "LaserExtraDamage_Auxiliary",
        "RailgunExtraDamageCompatibility": "RailgunExtraDamage_Auxiliary",
    }


def test_current_tree_has_no_compatibility_cohort_left_to_reconcile():
    assert CURRENT_REPORT["counts"] == {
        "compatibility_templates": 0,
        "all_direct_relationships": 0,
        "concrete_weapon_relationships": 0,
        "template_relationships": 0,
        "distinct_concrete_weapons": 0,
        "distinct_template_consumers": 0,
        "already_inherits_twin_all_consumers": 0,
        "exposed_without_twin_all_consumers": 0,
        "missing_twin_all_consumers": 0,
    }
    assert CURRENT_REPORT["template_consumers"] == []
    assert CURRENT_REPORT["templates"] == []
    assert CURRENT_REPORT["simulation"][
        "changed_concrete_weapons_in_full_descendant_closure"] == 0
    assert CURRENT_REPORT["pure_rename_simulation"]["template_renames"] == {}
    assert CURRENT_REPORT["pure_rename_simulation"]["payload_renames"] == {}


if __name__ == "__main__":
    test_frozen_inventory_includes_the_template_consumer()
    test_literal_chain_proposal_fails_the_order_aware_gate()
    test_pure_rename_preserves_every_resolved_weapon_and_avoids_payload_collisions()
    test_current_tree_has_no_compatibility_cohort_left_to_reconcile()
    print("R12 consumer closure fixtures: PASS")
