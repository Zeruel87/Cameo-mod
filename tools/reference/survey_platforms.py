#!/usr/bin/env python3
"""W13 — which PLATFORM fires a warhead, so like is compared with like.

Maintainer, 2026-08-15: *"there is a huge difference between the obelisk of
light laser (which is a very big laser) and the small laser from the laser
turret and infantry laser weapons … light lasers are good against light and
heavy lasers are good against heavy … we take a careful look what type of unit
is using that weapon."*

That is the reason Cameo splits `HE` into `CannonHE` / `MissileHE` / `BulletHE`
rather than keeping one `HE`, and the same split has to be applied to the
REFERENCE data before any of it is averaged. A profile is only comparable to a
Cameo family if the unit firing it plays the same role.

So this walks every INI source the other way round — from the ACTOR, not the
warhead — and reports, for a weapon family, what each platform class actually
ships:

    python tools/reference/survey_platforms.py laser
    python tools/reference/survey_platforms.py tesla --detail
    python tools/reference/survey_platforms.py --list

Platform classes come from the engine's own registries (`[InfantryTypes]`,
`[VehicleTypes]`, `[AircraftTypes]`, `[BuildingTypes]`), then buildings are
split big/small and vehicles light/heavy by their own `Cost`/`Strength`, since
"a big defence" is a size statement and the rules already carry the sizes.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import statistics
import sys
import warnings

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
import aggregate_archetype as ag  # noqa: E402
import extract_versus as ev  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TYPE_LISTS = {"InfantryTypes": "INF", "VehicleTypes": "VEH",
              "AircraftTypes": "AIR", "BuildingTypes": "BLD"}
# INI registry keys are labels, not necessarily numeric (DTA uses A_01,
# ......131072, etc.). The value identifies the actor.
LIST_ENTRY = re.compile(r"^\s*([^=;\s]+)\s*=\s*([^;\s]+)")

# Weapon families, by the name of the warhead OR of the weapon firing it. Kept
# deliberately broad: the point of this tool is to SPLIT a broad family by
# platform, so over-matching here is corrected by the platform column.
FAMILIES = {
    "laser": r"laser|lasr|obel|beam|prism|photon|ion",
    "tesla": r"tesla|zap|bolt|electric|lightn|coil",
    "flame": r"flame|fire|napalm|burn|incend",
    "cannon": r"cannon|shell|105mm|120mm|90mm|gun\b",
    "missile": r"missile|rocket|heat|dragon|sabot|tow\b",
    "bullet": r"mg\b|machine|vulcan|gatling|carbine|rifle|minigun|chain",
}


def type_registry(path: pathlib.Path) -> dict[str, str]:
    """{ACTOR: macro class} from the engine's own type lists."""
    out, section = {}, None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lstrip().startswith(";"):
            continue
        head = re.match(r"^\s*\[([^\]]+)\]", line)
        if head:
            section = head.group(1)
            continue
        macro = TYPE_LISTS.get(section or "")
        if not macro:
            continue
        hit = LIST_ENTRY.match(line)
        if hit:
            # entries can read `AMCV;Allied` — the actor is before the comment
            out[hit.group(2).split(";")[0].strip().upper()] = macro
    return out


def platform_of(actor: str, macro: str, node: dict) -> str:
    """Refine a macro class into the role that matters for weapon design.

    Buildings split BIG vs SMALL defence, because that is precisely the
    distinction the maintainer is asking about — an Obelisk is not a laser
    turret. Vehicles split light/heavy the same way. Thresholds are read off the
    unit's own Cost, which every Westwood ruleset carries.
    """
    def num(key: str) -> float:
        try:
            return float(node.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    cost = num("cost")
    if macro == "BLD":
        return "defense_big" if cost >= 1400 else "defense_small"
    if macro == "VEH":
        if cost >= 1500:
            return "vehicle_heavy"
        return "vehicle_light" if cost <= 700 else "vehicle_medium"
    if macro == "AIR":
        return "aircraft"
    return "infantry"


def survey(family: str) -> list[dict]:
    from warhead_source_selection import selected_sources
    pattern = re.compile(FAMILIES[family], re.I)
    corpus = json.loads((ROOT / "docs/reference/versus_raw.json")
                        .read_text(encoding="utf-8"))
    corpus["sources"] = selected_sources(corpus["sources"])
    rows = []
    for sid, _lineage, kind, path, _engine in ev.SOURCES:
        if kind != "ini":
            continue
        entry = corpus["sources"].get(sid)
        if not entry:
            continue
        path = ag.source_path(sid, corpus["sources"])
        by_name = {str(r["warhead"]): r for r in entry["rows"] if "versus" in r}
        try:
            ini = ag.read_ini_resolved(sid, path, corpus["sources"])
        except FileNotFoundError as exc:
            warnings.warn(f"{sid}: platform survey unavailable: {exc}")
            continue
        registry = type_registry(path)
        if sid in ag.INI_BASE:                       # a delta inherits its base's lists
            base = ag.source_base_path(sid, corpus["sources"])
            if base and base.exists():
                registry = {**type_registry(base), **registry}

        for actor, macro in registry.items():
            node = ini.get(actor)
            if not node:
                continue
            for weapon, warhead in ag.trace_ini(ini, actor):
                if not (pattern.search(weapon) or pattern.search(warhead)):
                    continue
                row = by_name.get(warhead)
                if not row or len(row["versus"]) < ag.MIN_ARITY_FOR_AGGREGATE:
                    continue
                rows.append({
                    "source": sid, "actor": actor, "weapon": weapon,
                    "warhead": warhead, "platform": platform_of(actor, macro, node),
                    "cost": node.get("cost"),
                    "versus": ag.normalise({k: float(v)
                                            for k, v in row["versus"].items()}),
                })
    return rows


def direction(versus: dict) -> str:
    """Does this profile rise toward heavy armour, or fall away from it?"""
    vals = [versus.get(a) for a in ("light", "medium", "heavy")]
    known = [v for v in vals if v is not None]
    if len(known) < 2:
        return "?"
    delta = known[-1] - known[0]
    if abs(delta) < 5:
        return "flat"
    return "anti-HEAVY" if delta > 0 else "anti-LIGHT"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("family", nargs="?", choices=sorted(FAMILIES))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--detail", action="store_true", help="every row, not a summary")
    args = ap.parse_args()

    if args.list or not args.family:
        for name, pattern in FAMILIES.items():
            print(f"  {name:10} /{pattern}/")
        return 0

    rows = survey(args.family)
    if not rows:
        print(f"no {args.family} weapon resolves to a platform")
        return 1

    print(f"{args.family}: {len(rows)} platform-resolved profiles "
          f"from {len({r['source'] for r in rows})} sources\n")
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        groups[r["platform"]].append(r)

    print(f"{'platform':16} {'n':>3} {'INF':>6} {'LIGHT':>6} {'HEAVY':>6} "
          f"{'BLD':>6}  direction (majority)")
    for platform in ("infantry", "vehicle_light", "vehicle_medium", "vehicle_heavy",
                     "aircraft", "defense_small", "defense_big"):
        members = groups.get(platform)
        if not members:
            continue

        def med(key):
            vals = [m["versus"][key] for m in members if key in m["versus"]]
            return f"{statistics.median(vals):.0f}" if vals else "--"

        dirs = collections.Counter(direction(m["versus"]) for m in members)
        top = ", ".join(f"{k} {v}" for k, v in dirs.most_common(3))
        print(f"{platform:16} {len(members):3} {med('none'):>6} {med('light'):>6} "
              f"{med('heavy'):>6} {med('concrete'):>6}  {top}")

    if args.detail:
        print()
        for platform, members in groups.items():
            print(f"\n--- {platform} ---")
            for m in sorted(members, key=lambda m: (m["source"], m["actor"])):
                v = m["versus"]
                print(f"  {m['source']:18} {m['actor']:14} {m['warhead'][:20]:20} "
                      f"cost={str(m['cost'] or '?'):>5}  "
                      + " ".join(f"{a[:4]}={v[a]:.0f}"
                                 for a in ("none", "light", "heavy", "concrete")
                                 if a in v)
                      + f"  {direction(v)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
