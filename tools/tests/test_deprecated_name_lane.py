"""Focused fixtures for the read-only R10-R15 lane audit."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_deprecated_name_lane import (  # noqa: E402
    NUKE_COMPANION_KEYS,
    NUKE_RING_KEYS,
    direct_template_users,
    has_nuclear_ring,
    payload_row,
)


class Node:
    def __init__(self, key, value=None, children=(), file="mods/cameo/test.yaml", line=1):
        self.key = key
        self.value = value
        self.children = list(children)
        self.file = file
        self.line = line

    def get(self, key):
        child = next((c for c in self.children if c.key == key), None)
        return child.value if child else None

    def child(self, key):
        return next((c for c in self.children if c.key == key), None)


class Ruleset:
    def __init__(self, weapons):
        self.weapons = weapons


def test_generic_damage_is_not_a_nuclear_ring_selector():
    generic = Node("weapon", children=[Node("Warhead@Damage", "WarpDamage")])
    ring = Node("weapon", children=[Node("Warhead@4Dam_areanuke1", "SpreadDamage")])
    assert not has_nuclear_ring(generic)
    assert has_nuclear_ring(ring)
    assert "Damage" in NUKE_COMPANION_KEYS
    assert "Damage" not in NUKE_RING_KEYS


def test_payload_row_keeps_timing_and_ordered_payloads():
    resolved = Node("weapon", children=[
        Node("ReloadDelay", "25"), Node("Burst", "2"), Node("BurstDelays", "8"),
        Node("Projectile", "LightningZap"),
        Node("Warhead@4Dam_areanuke1", "SpreadDamage", [
            Node("Damage", "17500"), Node("Delay", "3"), Node("Spread", "2000")
        ]),
    ])
    row = payload_row("Nuke", Node("Nuke"), resolved, resolved.children[-1])
    assert row["delay"] == "3"
    assert row["reload_delay"] == "25"
    assert row["burst"] == "2"
    assert row["burst_delays"] == "8"
    assert row["payload_order"] == ["Warhead@4Dam_areanuke1"]


def test_template_users_are_direct_only():
    users = direct_template_users(Ruleset({
        "^Compatibility_Bullet_MediumFlat": Node("^Compatibility_Bullet_MediumFlat"),
        "Parent": Node("Parent", children=[Node("Inherits", "^Compatibility_Bullet_MediumFlat")]),
        "Child": Node("Child", children=[Node("Inherits", "Parent")]),
    }))
    assert [u["weapon"] for u in users["^Compatibility_Bullet_MediumFlat"]] == ["Parent"]


if __name__ == "__main__":
    test_generic_damage_is_not_a_nuclear_ring_selector()
    test_payload_row_keeps_timing_and_ordered_payloads()
    test_template_users_are_direct_only()
    print("deprecated-name lane fixtures: PASS")
