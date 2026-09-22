"""Focused R14 expressibility tests."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from compare_nuke_area_damage import PAYLOAD_KEYS, analyse_weapon, engine_contract  # noqa: E402


def rows(spreads, damages, targets=None):
    targets = targets or ["Ground, Water, Air"] * len(PAYLOAD_KEYS)
    out = []
    for index, (key, spread, damage, valid) in enumerate(
            zip(sorted(PAYLOAD_KEYS), spreads, damages, targets)):
        out.append({
            "weapon": "FixtureNuke",
            "file": "fixture.yaml",
            "warhead": key,
            "type": "SpreadDamage",
            "damage": str(damage),
            "delay": str(index * 2),
            "spread": str(spread),
            "falloff": "100, 0",
            "valid_targets": valid,
        })
    return out


def test_uniform_fixture_still_requires_full_review():
    result = analyse_weapon("FixtureNuke", rows([100] * 7, [10] * 7))
    assert result["status"] == "requires_review", result
    assert result["observed_differences"] == []


def test_per_tick_geometry_and_targets_hold_conversion():
    target_sets = ["Ground, Water, Air"] + ["Ground, Water, Underwater, Air"] * 6
    result = analyse_weapon(
        "FixtureNuke", rows([100, 200, 300, 400, 500, 600, 700],
                            [64, 32, 16, 8, 4, 2, 1], target_sets))
    reasons = " ".join(result["observed_differences"])
    assert "non-proportional Spread/Falloff" in reasons
    assert "ValidTargets sets differ" in reasons
    assert result["spatial_ratio_witness"] is not None


def test_engine_contract_matches_reviewed_implementation():
    contract = engine_contract()
    assert "uniform" in contract["delay"]
    assert "linear" in contract["radius"]
    assert "shared" in contract["falloff"]


if __name__ == "__main__":
    test_uniform_fixture_still_requires_full_review()
    test_per_tick_geometry_and_targets_hold_conversion()
    test_engine_contract_matches_reviewed_implementation()
    print("R14 AreaDamage comparison fixtures: PASS")
