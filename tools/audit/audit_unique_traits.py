#!/usr/bin/env python3
"""audit_unique_traits.py — catch duplicate traits that only crash at PRODUCTION time.

`self.Trait<T>()` resolves through `TraitDictionary.TraitContainer<T>.Get`, which
throws `Actor <name> has multiple traits of type T` when an actor declares more
than one.  That throw happens in the ACTOR CONSTRUCTOR, so nothing before it
catches the mistake:

  * the yaml parses,
  * `--check-yaml` lints clean,
  * the game BOOTS to the main menu,

and the crash only arrives the moment somebody builds the unit.  The commit gate
is a boot gate, so this class of bug walks straight through it.  That is not
hypothetical — `schwarzermond_noidmgarmor` shipped with a second `Shielded`
(2026-08-15) and killed a live game; every unit already inherits one from
`^BasicUnit` -> `^ShieldedShieldable`.

The check: any trait type that some C# resolves with `.Trait<T>()` must appear at
most ONCE per actor.  Traits read with `TraitsImplementing<T>()` or
`TraitOrDefault<T>()` are fine with duplicates and are not flagged.
"""
from __future__ import annotations

import pathlib
import re
import sys

from cameo_model import Model

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Sources that make up the running game: the engine assemblies plus the mod's own.
SOURCE_ROOTS = [
    ROOT / "engine" / "OpenRA.Game",
    ROOT / "engine" / "OpenRA.Mods.Common",
    ROOT / "engine" / "OpenRA.Mods.AS",
    # CA is vendored at the repo root, not in engine/ — this read engine/OpenRA.Mods.CA,
    # which does not exist, so 185 CA source files were silently missing from the scan.
    ROOT / "OpenRA.Mods.CA",
    ROOT / "engine" / "OpenRA.Mods.Cnc",
    ROOT / "engine" / "OpenRA.Mods.D2k",
    ROOT / "OpenRA.Mods.Cameo",
]

TRAIT_CALL_RE = re.compile(r"\.Trait<([A-Za-z0-9_]+)>\(\)")
TRAIT_INFO_RE = re.compile(r"\bclass\s+([A-Za-z0-9_]+)Info\b")

# Traits that ARE resolved with .Trait<T>() somewhere, but whose duplicates are the
# engine's own idiom rather than a mistake.
#
# Several conditional sprite bodies on one actor (loaded/empty, upgraded building
# stages, hunkered/deployed forms) is how OpenRA has always done alternate artwork —
# 41 actors here rely on it. The only unique resolve is `MadTank.cs:173`, on an actor
# that has exactly one, so the pattern never reaches the throw. Leaving these in would
# bury a real find under 41 rows of noise.
ALLOW_DUPLICATES = {
    "WithSpriteBody",
    "WithFacingSpriteBody",
}


def scan_sources() -> tuple[set[str], set[str]]:
    """Return (types resolved via .Trait<T>(), concrete trait names)."""
    unique: set[str] = set()
    concrete: set[str] = set()
    for root in SOURCE_ROOTS:
        if not root.is_dir():
            continue
        for path in root.rglob("*.cs"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            unique.update(TRAIT_CALL_RE.findall(text))
            concrete.update(TRAIT_INFO_RE.findall(text))
    return unique, concrete


def base_name(node_key: str) -> str:
    """`Armor@Plating` -> `Armor`, `Shielded` -> `Shielded`."""
    return node_key.split("@", 1)[0].strip()


def main() -> int:
    unique, concrete = scan_sources()

    # Interfaces (IMove, IHealth, ...) are resolved uniquely too, but mapping a yaml
    # node name onto the interfaces it implements needs real type information, so
    # restrict to CONCRETE traits — which is where the yaml-authoring mistakes live.
    watched = {t for t in unique if t in concrete} - ALLOW_DUPLICATES

    model = Model()
    actors = sorted(n for n in model.rs.actors if not n.startswith("^"))

    findings: list[tuple[str, str, list[str]]] = []
    for name in actors:
        resolved = model.rs.resolve(name)
        if resolved is None:
            continue

        seen: dict[str, list[str]] = {}
        for child in resolved.children:
            key = child.key
            if key.startswith("-"):
                continue
            seen.setdefault(base_name(key), []).append(key)

        for trait, keys in sorted(seen.items()):
            if len(keys) > 1 and trait in watched:
                findings.append((name, trait, keys))

    print("# audit_unique_traits — traits that must be unique per actor\n")
    print(f"_Scanned {len(actors)} actors against {len(watched)} trait types "
          "resolved with `.Trait<T>()`._\n")

    if not findings:
        print("_clean_ — no actor declares two nodes of a trait the engine resolves "
              "uniquely.\n")
        return 0

    print(f"**{len(findings)} duplicate(s)** — each one throws "
          "`has multiple traits of type` the first time the actor is BUILT, which a "
          "boot gate cannot catch.\n")
    print("| actor | trait | nodes |")
    print("|---|---|---|")
    for name, trait, keys in findings:
        print(f"| `{name}` | `{trait}` | {', '.join(f'`{k}`' for k in keys)} |")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
