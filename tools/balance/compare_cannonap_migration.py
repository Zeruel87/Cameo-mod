#!/usr/bin/env python3
"""compare_cannonap_migration.py — resolved scope-preservation comparison for the
^Warhead_CannonAP continuous-heaviness pilot (DESIGN §12.0i activation).

Reads yaml only through `miniyaml.Ruleset.resolve_weapon` (never hand-parse), in the
same pattern as dump_resolved.py. Two commands:

  --capture OUT.json   resolve the CURRENT tree and write a per-weapon snapshot.
                       Run this BEFORE the migration edits, on the worktree as it
                       stands (so unrelated live WIP, e.g. the RA1
                       AlliedTankDestroyerCannon draft in RedAlert/Allies, is
                       baked into the baseline instead of being flagged twice).

  --compare BASE.json  resolve the CURRENT tree, diff weapon-by-weapon against the
                       baseline, and exit 0 only when every difference is one the
                       pilot actually intends:
                         * the FIVE pilot weapons and nothing else;
                        * per pilot: the warhead keys renamed onto the new base
                            (^Warhead_CannonAP -> Warhead@CannonAP),
                            Heaviness authored, Versus values replaced (the
                            intentional provisional role-profile migration —
                            profiles are NOT expected to be equal), Spread
                            authoring moved onto the base (runtime-equal after
                            the h scaling), and THE SHARED-PROFILE hop:
                            HeavinessMode: SharedVersus, PercentageScale exactly
                            2000, and the percentage tables removed;
                         * every OTHER weapon: equal canonical resolved snapshot, or a
                           hard non-zero exit (stop-and-report rule).

Anything else is printed as an UNEXPECTED change and fails the run: this tool never
re-ranks, never edits ratchets or exception lists, and does not hide the duplicate
levelled templates — it only measures.
The allowed profile fields are intentionally not required to be equal: separate
generator and C# runtime tests validate their tables and endpoint semantics.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
from miniyaml import Ruleset  # noqa: E402
from dump_resolved import node_to_obj  # noqa: E402
from effective_heaviness import scale_length

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# The pilot scope, verbatim from the maintainer order: 5 weapons, 3 actors, h fixed
# per weapon. Nothing outside this set may change.
PILOT_H = {
    "RA2sabot": 0,            # ra2_allies_tankdestroyer (RA2 saboteur closure)
    "RA2sabot_elite": 0,      # ra2_allies_tankdestroyer elite closure
    "TS90mm": 1000,           # ts_nod_ticktank
    "TS90mmDep": 1000,        # ts_nod_ticktank deployed
    "corrino_buggy_gun": 0,   # corrino buggy
}
# Allowed NEW top-level keys on a pilot's resolved node (added by the base).
PILOT_NEW_KEYS = set()
# The only NEW resolved entry the migration introduces: the live base template.
EXPECTED_NEW_WEAPONS = {"^Warhead_CannonAP"}
# Per-pilot warhead-key renames: the child override keys move WITH the template
# onto the new base's actual keys (TS90mm precedent; a stale key would orphan
# into an abstract warhead). Old key -> new key.
PILOT_RENAMES = {
    "RA2sabot": {"Warhead@CannonAP_Light": "Warhead@CannonAP"},
    "RA2sabot_elite": {"Warhead@CannonAP_Light": "Warhead@CannonAP"},
    "TS90mm": {"Warhead@CannonAP_Medium": "Warhead@CannonAP"},
    "TS90mmDep": {"Warhead@CannonAP_Medium": "Warhead@CannonAP"},
    "corrino_buggy_gun": {"Warhead@CannonAP_Light": "Warhead@CannonAP"},
}
# Warhead nodes whose payload may differ: the main carries the intentional
# provisional role-profile migration (Versus replacement, the h-scaled Spread
# authoring, Heaviness) AND the SHARED-PROFILE hop (HeavinessMode: SharedVersus,
# PercentageScale 10000 -> 2000, the percentage tables REMOVED — the percentage
# half now follows the flat Versus table).
PILOT_MAIN_KEYS = ("Warhead@CannonAP",)
PROFILE_FIELDS = {"Versus", "Heaviness", "Spread", "HeavinessMode",
                  "PercentageScale"}
# THE SHARED PROFILE's required EXACT new resolved values (never merely permitted):
PILOT_EXACT_NEW = {"HeavinessMode": "SharedVersus", "PercentageScale": "2000"}
# The percentage tables the LEGACY baseline carried and the shared mode REMOVES.
PILOT_REMOVED_TABLES = ("PercentageVersus", "PercentageVersusLight",
                        "PercentageVersusHeavy")


def snapshot(repo_root: pathlib.Path | None = None) -> dict:
    rs = Ruleset(repo_root or pathlib.Path.cwd())
    out = {}
    for name in sorted(rs.weapons):
        node = rs.resolve_weapon(name)
        out[name] = node_to_obj(node) if node is not None else None
    return out


def diff_pilot(name, before, after):
    """Permitted differences for one pilot -> (info lines, hard problems).

    Info lines report the raw profile delta (the parent's counterfactual — the
    intentional provisional role-profile migration, never auto-"fixed").
    Problems are anything OUTSIDE the permitted classes.
    """
    renames = PILOT_RENAMES.get(name, {})
    b = {renames.get(k, k): v for k, v in (before or {}).items()}
    a = dict(after or {})
    info, problems = [], []
    main = a.get("Warhead@CannonAP")
    if not isinstance(main, dict):
        problems.append("required migrated main missing")
    elif str(main.get("Heaviness")) != str(PILOT_H[name]):
        problems.append("wrong or missing Heaviness")
    for k in sorted(set(b) - set(a)):
        problems.append(f"REMOVED key {k} (no rename pair)")
    for k in sorted(set(a) - set(b)):
        if k in PILOT_NEW_KEYS:
            info.append(f"new key {k} (base anchor)")
        else:
            problems.append(f"unexpected NEW key {k}")
    for k in sorted(set(a) & set(b)):
        av, bv = a[k], b[k]
        if av == bv:
            continue
        if k in PILOT_MAIN_KEYS and isinstance(av, dict) and isinstance(bv, dict):
            info.append(f"main {k} migrated onto the base (intentional):")
            for sk in sorted(set(av) | set(bv)):
                if av.get(sk) != bv.get(sk):
                    if sk in PILOT_REMOVED_TABLES and sk not in av:
                        # THE SHARED PROFILE removes the percentage tables.
                        info.append(f"  main.{sk} removed (shared profile)")
                        continue
                    if sk not in PROFILE_FIELDS:
                        problems.append(f"main.{sk} unexpectedly changed/added/removed")
                    else:
                        info.append(f"  main.{sk} changed")
            try:
                if str(av.get("Heaviness")) != str(PILOT_H[name]):
                    problems.append("wrong or missing Heaviness")
                for sk, exact in PILOT_EXACT_NEW.items():
                    if str(av.get(sk, "")) != exact:
                        problems.append(
                            f"main.{sk} must be the SHARED-PROFILE exact value "
                            f"{exact}, got {av.get(sk)!r}")
                for sk in PILOT_REMOVED_TABLES:
                    if sk in av and av[sk]:
                        problems.append(
                            f"main.{sk} must be ABSENT in the shared profile")
                old_spread = scale_length(int(bv["Spread"]), int(bv.get("Heaviness", -1)))
                new_spread = scale_length(int(av["Spread"]), PILOT_H[name])
                if old_spread != new_spread:
                    problems.append(f"effective Spread changed: {old_spread} -> {new_spread}")
            except (KeyError, TypeError, ValueError) as exc:
                problems.append(f"invalid geometry: {exc}")
        else:
            problems.append(f"key {k} -> {json.dumps(av, sort_keys=True)[:220]}")
    return info, problems


def compare(base, snap):
    problems = [f"weapon disappeared: {w}" for w in sorted(set(base) - set(snap))]
    if not EXPECTED_NEW_WEAPONS.issubset(snap):
        problems.append("required continuous base missing")
    problems += [f"weapon appeared: {w}" for w in sorted(set(snap) - set(base)
                                                         - EXPECTED_NEW_WEAPONS)]
    changed = []
    for name in sorted(set(snap) & set(base)):
        if snap[name] == base[name]:
            continue
        changed.append(name)
        if name in PILOT_H:
            _info, failures = diff_pilot(name, base[name], snap[name])
            problems += [f"{name}: {p}" for p in failures]
        else:
            problems.append(f"{name}: UNEXPECTED legacy change")
    if set(PILOT_H) - set(changed):
        problems.append("pilot weapons with NO resolved change: " +
                        ", ".join(sorted(set(PILOT_H) - set(changed))))
    return changed, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture", metavar="OUT.json")
    mode.add_argument("--compare", metavar="BASE.json")
    ap.add_argument("--root", default=None, help="repo root (default: CWD's parent heuristics)")
    args = ap.parse_args()
    root = pathlib.Path(args.root) if args.root else \
        pathlib.Path(__file__).resolve().parents[2]
    snap = snapshot(root)
    if args.capture:
        output = pathlib.Path(args.capture).resolve()
        if output.is_relative_to(root.resolve()):
            ap.error("capture output must be outside the repository")
        with output.open("x", encoding="utf-8") as stream:
            json.dump(snap, stream, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        print(f"captured {len(snap)} resolved weapons -> {args.capture}")
        return 0
    if not args.compare:
        ap.error("give --capture OUT.json or --compare BASE.json")
    base = json.loads(pathlib.Path(args.compare).read_text(encoding="utf-8"))
    changed, problems = compare(base, snap)
    if changed:
        print(f"changed resolved weapons ({len(changed)}): {', '.join(changed)}")
    if problems:
        print(f"[X] {len(problems)} problem(s):")
        for p in problems:
            print(f"      {p}")
        return 1
    print(f"[OK] {len(snap)} resolved weapons; {len(changed)}/{len(PILOT_H)} pilots "
          f"changed, 0 legacy weapons changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
