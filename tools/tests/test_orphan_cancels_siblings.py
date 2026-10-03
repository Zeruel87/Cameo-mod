"""Same-key sibling provider fixtures for audit_orphan_cancels.

The engine merges duplicate keys within one node set before applying
anything (MiniYaml.cs MergeSelfPartial: "Node with the same key has
already been added: merge new node over the existing one"). So a
`-TrailImage:` inside a SECOND `Projectile:` block can see the field a
FIRST `Projectile:` block defines — the audit must union same-key
siblings before recursing, matching the engine.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import miniyaml  # noqa: E402
from audit_orphan_cancels import _check_level  # noqa: E402


def findings(text):
    node = miniyaml.load_text(text, "fixture.yaml")[0]
    out: list[str] = []
    _check_level(node, [], (), "weapon:" + node.key, out)
    return out


def test_cancel_sees_field_from_same_key_sibling():
    # -TrailImage lives in the second Projectile: sibling; its provider is
    # declared in the first. The engine merges them, so this is legal.
    out = findings("""\
w:
\tProjectile: Bullet
\t\tTrailImage: trail
\tProjectile:
\t\t-TrailImage:
""")
    assert out == [], out


def test_cancel_without_provider_still_flags():
    # Same shape, but neither sibling defines TrailImage -> true orphan.
    out = findings("""\
w:
\tProjectile: Bullet
\t\tSpeed: 100
\tProjectile:
\t\t-TrailImage:
""")
    assert len(out) == 1 and "TrailImage" in out[0], out


def test_provider_in_first_sibling_cancel_in_third():
    out = findings("""\
w:
\tProjectile: Bullet
\t\tTrailImage: trail
\tProjectile:
\t\tSpeed: 100
\tProjectile:
\t\t-TrailImage:
""")
    assert out == [], out


def test_distinct_siblings_do_not_leak_providers():
    # TrailImage sits under Projectile, NOT under Warhead@x — an orphan.
    out = findings("""\
w:
\tProjectile: Bullet
\t\tTrailImage: trail
\tWarhead@x: CreateEffect
\t\t-TrailImage:
""")
    assert len(out) == 1, out


if __name__ == "__main__":
    test_cancel_sees_field_from_same_key_sibling()
    test_cancel_without_provider_still_flags()
    test_provider_in_first_sibling_cancel_in_third()
    test_distinct_siblings_do_not_leak_providers()
    print("orphan-cancels same-key sibling fixtures: PASS")
