#!/usr/bin/env python3
"""Which legacy weapon templates are still OUTSIDE the `^Warhead_*` family system?

`^ToxicWeapon` turned out to be one of these: a pre-split template carrying its own
`Versus`, its own separate `*FriendlyFire` twin, and a `HealthPercentageDamage`
%-twin — everything the family system replaced. It was found by accident. This
finds the rest on purpose.

    python tools/audit/audit_unconverted_templates.py
    python tools/audit/audit_unconverted_templates.py --write

**The signature of "not converted"** is a `^Template` that declares `Versus` on its
own warheads while inheriting no `^Warhead_*` parent. That is precisely the state
DESIGN.md forbids — *"Versus lives ONLY in `^Warhead_*` templates"* — so every row
here is both a migration target and a live rule violation.

Ranked by DIRECT INHERITORS, because that is the blast radius: converting
`^ShrapnelWeapon` touches 105 weapons, converting `^MissileWeapon` touches 10.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import environment  # noqa: E402
import miniyaml  # noqa: E402
import gen_weapon_template as gwt  # noqa: E402

# This audit writes its OWN report rather than being redirected by run_all, so it has
# to honour the same guard the runners do: docs/audit/latest/ is tracked evidence and
# must not be written from a tree that cannot produce it. See tools/audit/environment.py.
REPORT = "unconverted_templates.md"


def out_path(force_latest: bool = False) -> pathlib.Path:
    dest, _ = environment.out_dir(force_latest)
    return ROOT / dest / REPORT

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Templates that are SUPPOSED to stay outside the family system, with the reason.
# `WEAPON_3WAY_SPLIT.md` also listed `^ToxicWeapon` here; that is now stale — the
# maintainer ordered it built into the system on 2026-08-15 and it is done.
KEEP = {
    "^HealingWeapon": "support — heals, has no armor profile to speak of",
    "^RepairWeapon": "support — repairs, same",
    "^SniperWeapon": "special — infantry-only, huge damage per shot, and its "
                     "OpenToppedDamage warhead is how a sniper hits passengers",
}

# Where each legacy template is headed, when that is already settled by an existing
# family. Recorded so the survey is a worklist and not just a complaint.
TARGET = {
    "^SmallArms": "Bullet_Light", "^Chaingun": "Bullet_Medium",
    "^ShrapnelWeapon": "Concussion_*", "^Grenade": "Demolition_* / Concussion_*",
    "^HeavyBomb": "Demolition_Heavy",
    "^LightMissile": "MissileHE/AP_Light", "^MediumMissile": "MissileHE/AP_Medium",
    "^HeavyMissile": "MissileHE/AP_Heavy", "^MissileWeapon": "MissileHE_*",
    "^HeavyAAWeapon": "MissileAA_Heavy", "^FlakWeapon": "Flak_*",
    "^TankDestroyerCannon": "CannonAP_Light", "^MediumCannon": "CannonHE_Medium",
    "^HeavyCannon": "CannonHE_Heavy",
    "^LightFlameWeapon": "Flame_Light / Inferno_*", "^MediumFlameWeapon": "Flame_Medium",
    "^HeavyFlameWeapon": "Flame_Heavy",
    "^LightChemicalWeapon": "Chemical_Light", "^MediumChemicalWeapon": "Chemical_Medium",
    "^HeavyChemicalWeapon": "Chemical_Heavy",
    "^LaserWeapon": "Laser_*", "^RailgunWeapon": "Railgun_Heavy",
    "^TeslaWeapon": "Tesla_*", "^TeslaChargedWeapon": "Tesla_Super",
    "^NuclearWarhead": "Nuclear_Super", "^MagicWeapon": "Magic_*",
    "^ArrowWeapon": "Arrow_*", "^SwordWeapon": "Melee_*",
}


def survey() -> list[dict]:
    rules = miniyaml.Ruleset(ROOT)
    inheritors: dict[str, set[str]] = collections.defaultdict(set)
    for name, node in rules.weapons.items():
        for child in node.children:
            if child.key.startswith("Inherits") and child.value:
                inheritors[child.value.strip()].add(name)

    rows = []
    for name, node in rules.weapons.items():
        if not name.startswith("^") or name.startswith("^Warhead_"):
            continue
        parents = [c.value.strip() for c in node.children
                   if c.key.startswith("Inherits") and c.value]
        if any(p.startswith("^Warhead_") for p in parents):
            continue                       # already inside the family system
        versus = friendly = pct = 0
        for child in node.children:
            if not (child.key == "Warhead" or child.key.startswith("Warhead@")):
                continue
            if child.child("Versus") is not None:
                versus += 1
            if "friendlyfire" in child.key.lower():
                friendly += 1
            if (child.value or "").strip() == "HealthPercentageDamage":
                pct += 1
        if not versus:
            continue
        rows.append({
            "template": name,
            "inheritors": len(inheritors.get(name, ())),
            "versus_nodes": versus,
            "retired_ff_twins": friendly,
            "legacy_pct_twins": pct,
            "target": TARGET.get(name, ""),
            "keep": KEEP.get(name, ""),
        })
    rows.sort(key=lambda r: -r["inheritors"])
    return rows


def render(rows: list[dict]) -> str:
    live = [r for r in rows if not r["keep"]]
    lines = [
        "# Weapon templates still outside the `^Warhead_*` family system",
        "",
        "Generated by `tools/audit/audit_unconverted_templates.py`.",
        "",
        "A template that declares its own `Versus` while inheriting no `^Warhead_*` "
        "parent has not been converted. DESIGN.md is explicit that **Versus lives ONLY "
        "in `^Warhead_*` templates**, so every row below is simultaneously a migration "
        "target and a live rule violation.",
        "",
        f"- unconverted templates: **{len(live)}**",
        f"- weapons inheriting them directly: **{sum(r['inheritors'] for r in live)}**",
        f"- retired-style `*FriendlyFire` twins still present: "
        f"**{sum(r['retired_ff_twins'] for r in live)}**",
        f"- legacy `HealthPercentageDamage` twins: "
        f"**{sum(r['legacy_pct_twins'] for r in live)}**",
        "",
        "Ranked by direct inheritors, which is the blast radius of converting each one.",
        "",
        "| template | inheritors | Versus nodes | old FF twins | legacy %-twins | target family |",
        "|---|--:|--:|--:|--:|---|",
    ]
    for r in live:
        lines.append(f"| `{r['template']}` | {r['inheritors']} | {r['versus_nodes']} | "
                     f"{r['retired_ff_twins']} | {r['legacy_pct_twins']} | "
                     f"{r['target'] or '**undecided**'} |")
    keep = [r for r in rows if r["keep"]]
    if keep:
        lines += ["", "## Deliberately outside the system", "",
                  "| template | inheritors | why |", "|---|--:|---|"]
        for r in keep:
            lines.append(f"| `{r['template']}` | {r['inheritors']} | {r['keep']} |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help=f"write docs/audit/<latest|degraded>/{REPORT}")
    ap.add_argument("--force-latest", action="store_true",
                    help="write docs/audit/latest/ even from an incomplete tree")
    args = ap.parse_args()
    out = out_path(args.force_latest)
    rows = survey()
    live = [r for r in rows if not r["keep"]]
    print(f"{len(live)} unconverted templates, "
          f"{sum(r['inheritors'] for r in live)} direct inheritors")
    for r in live[:15]:
        print(f"  {r['inheritors']:4d}  {r['template']:24s} -> {r['target'] or 'UNDECIDED'}")
    if args.write:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(rows) + "\n", encoding="utf-8")
        print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
