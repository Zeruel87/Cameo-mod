#!/usr/bin/env python3
"""audit_effect_pairings.py — impact effect/sound pairing guard.

    python tools/audit/audit_effect_pairings.py [--baseline PATH]

Maintainer rulings encoded (2026-09-23/24):

* Rule 2 — NO impact effect is ever silent. A resolved `CreateEffect` (or any
  `Warhead@Effect*`) node that declares `Explosions` must also declare
  `ImpactSounds`.
* Ruling 1 exemption — bullet puffs stay silent ("Explosions only"; the
  gun's firing sound carries them). Corpus sprite names covered:
  `piff`/`piffs`, `water_piff`/`water_piffs`, the per-game variants
  `ra2_piff`/`ra2_piffs`/`d2k_piffs`, and the `*_poof`/`poof` puff family.
* Rule 3 — foreign sounds on D2k visuals are defects: a resolved node whose
  `Explosions` names a `d2k_*` sprite must not use a `.aud` sound (D2k's
  sounds are `EXPL*.WAV`; `splash9.aud` pairs with `small_splash`, a non-D2k
  visual, so it never trips this rule).

Counts are LOWER-ONLY: ratchet lives in tools/audit/ratchet_effect_pairings.json.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import miniyaml  # noqa: E402

import re as _re  # noqa: E402

# Bullet-puff sprites the maintainer ruled stay silent (2026-09-24 ruling 1):
# any piff/poof-family visual in any game's naming scheme.
_PUFF = _re.compile(
    r"^(?:[a-z0-9]+_)?(?:water_)?piffs?$|^(?:[a-z0-9]+_)?poofs?$", _re.I)


def _is_puff(visual: str) -> bool:
    return bool(_PUFF.match(visual))
RATCHET = pathlib.Path(__file__).resolve().parent / "ratchet_effect_pairings.json"


def _nodes(resolved):
    for c in resolved.children:
        if c.key.startswith("Warhead@"):
            yield c


def _val(node, key):
    for c in node.children:
        if c.key == key:
            return c.value
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=pathlib.Path, default=RATCHET)
    args = ap.parse_args()

    rs = miniyaml.Ruleset(miniyaml.find_repo_root())

    silent: list[tuple[str, str, str]] = []      # (weapon, node, visual)
    foreign: list[tuple[str, str, str, str]] = []  # (weapon, node, visual, sound)
    exempt_seen = collections.Counter()

    for name, src in rs.weapons.items():
        if name.startswith("^"):
            continue
        r = rs.resolve_weapon(name)
        if r is None:
            continue
        for node in _nodes(r):
            if (node.value or "").strip() != "CreateEffect":
                continue
            visuals = (_val(node, "Explosions") or "").strip()
            sounds = (_val(node, "ImpactSounds") or "").strip()
            if not visuals:
                continue
            for vis in (v.strip() for v in visuals.split(",") if v.strip()):
                if not sounds:
                    if _is_puff(vis):
                        exempt_seen[vis] += 1
                    else:
                        silent.append((name, node.key, vis))
                elif vis.startswith("d2k_") and sounds.lower().endswith(".aud"):
                    foreign.append((name, node.key, vis, sounds))

    print("# audit_effect_pairings — resolved CreateEffect pairing guard\n")
    print(f"Silent bullet-puff exemptions (ruled OK): "
          f"{dict(exempt_seen)}\n")

    print(f"## Silent impacts (Explosions w/o ImpactSounds): {len(silent)}")
    for w, n, v in silent[:60]:
        print(f"| `{w}` | `{n}` | `{v}` |")
    if len(silent) > 60:
        print(f"_… {len(silent) - 60} more_")

    print(f"\n## Foreign .aud sound on d2k_* visual: {len(foreign)}")
    for w, n, v, s in foreign[:60]:
        print(f"| `{w}` | `{n}` | `{v}` → `{s}` |")
    if len(foreign) > 60:
        print(f"_… {len(foreign) - 60} more_")

    if args.baseline.exists():
        base = json.loads(args.baseline.read_text())
        ok = (len(silent) <= base.get("silent", 0)
              and len(foreign) <= base.get("foreign", 0))
        print(f"\n{'PASS' if ok else 'FAIL'}: silent {len(silent)} "
              f"<= {base.get('silent')}, foreign {len(foreign)} "
              f"<= {base.get('foreign')}  (lower-only ratchet)")
        return 0 if ok else 1
    print("\n_no baseline set — reporting only_")
    return 0


if __name__ == "__main__":
    sys.exit(main())
