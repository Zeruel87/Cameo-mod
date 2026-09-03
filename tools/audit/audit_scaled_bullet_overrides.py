#!/usr/bin/env python3
"""Reject reachable Bullet projectiles that fall back to runtime Speed 17.

``ProjectileSpeedPercentage`` is implemented by ``ScaledBulletInfo``, not ordinary
``BulletInfo``.  If mixed inheritance changes the resolved type back to ``Bullet``
and no explicit ``Speed`` survives, the projectile silently uses Bullet's default
speed of 17 while carrying inert scaling metadata.

The InstantTracer migration exposed the same fallback on ordinary Bullet overrides:
their old projectile templates supplied Speed 2000/4000/10000, but the replacement
templates supply ``FakeBulletSpeed`` instead.  A child that deliberately keeps the
real Bullet type must therefore retain an explicit Speed.
"""
from __future__ import annotations

import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset  # noqa: E402
from survey_weapon_structure import weapon_reference_sets  # noqa: E402


def violations(rules: Ruleset) -> list[str]:
    concrete = {
        name for name in rules.weapons
        if not name.startswith("^") and rules.resolve_weapon(name) is not None
    }
    _direct, reachable = weapon_reference_sets(rules, concrete)
    out = []
    for name in sorted(reachable):
        resolved = rules.resolve_weapon(name)
        projectile = resolved.child("Projectile") if resolved is not None else None
        if projectile is None or str(projectile.value).strip() != "Bullet":
            continue
        try:
            percentage = int(str(projectile.get("ProjectileSpeedPercentage") or "0"))
        except ValueError:
            continue
        if percentage > 0 and projectile.get("Speed") is None:
            out.append(name)
    return out


def default_speed_violations(rules: Ruleset) -> list[str]:
    concrete = {
        name for name in rules.weapons
        if not name.startswith("^") and rules.resolve_weapon(name) is not None
    }
    _direct, reachable = weapon_reference_sets(rules, concrete)
    out = []
    for name in sorted(reachable):
        resolved = rules.resolve_weapon(name)
        projectile = resolved.child("Projectile") if resolved is not None else None
        if (projectile is not None
                and str(projectile.value).strip() == "Bullet"
                and projectile.get("Speed") is None):
            out.append(name)
    return out


def main() -> int:
    rules = Ruleset(ROOT)
    rows = violations(rules)
    defaults = default_speed_violations(rules)
    if rows or defaults:
        if defaults:
            print("FAIL reachable Bullet projectiles fall back to runtime Speed 17:")
            for name in defaults:
                print(f"- {name}")
        if rows:
            print("FAIL reachable Bullet projectiles carry active-looking speed scaling "
                  "that ordinary Bullet ignores:")
            for name in rows:
                print(f"- {name}")
        return 1
    print("PASS no reachable Bullet projectile falls back to runtime Speed 17")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
