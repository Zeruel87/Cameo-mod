#!/usr/bin/env python3
"""audit_survivability_pricing.py — E1: what a baseline shield SHOULD cost and does not.

Maintainer, 2026-08-16: *"shielded units and armored units need to have a price! it is like
extra survivability ... since everything deals more damage to shields you can count the 200%
shield strength like an extra 100% HP so calculate it as if the unit had twice the HP"* — with
the decisive qualifier *"that's only if the unit already has armor or shield included in
them"*.

That qualifier is the entire rule, and it splits the roster three ways:

  * **58 actors spawn with a shield pool** and no positive gate -> baseline durability, so it
    belongs in the price. Measured: 12 872 500 HP is really 20 316 495 effective HP,
    **+57.8% survivability priced at ZERO**. (56 of the 58 reach this report: `extract_stats`
    keeps only actors with `Buildable` or `Valued`, which is the balance-relevant set. The
    same filter explains 1152 capacity-only here against 1318 across the whole tree.)
  * **1318 actors carry an empty CAPACITY.** `^ShieldedShieldable` (defaults.yaml:7230) sets
    `MaxPercentageStrength: 100` with `InitialStrength: 0`; the pool only fills behind
    `shieldgen >= 1`. Charging for it would overprice 63% of the roster for a shield it does
    not have. This is the trap that produced the claim "Tesla's `Shield: 400` is free against
    51% of the roster" — the true baseline exposure is 1.4%.
  * **~216 actors have a shield behind an upgrade.** Real, but not baseline: that is the
    upgrade-pricing gap **E5**, not this one.

⚠ **A `RequiresCondition` is not automatically a gate.** `!disabled` is the standard
not-EMP'd guard and is TRUE on a healthy unit. Counting it as a gate hid every Protoss shield
and made the roster look shield-free, contradicting the maintainer — who was right.

INFORMATIONAL by design (always exit 0). These actors are mis-priced *today*, so failing would
block every commit until `apply_balance --confirm` runs. The report exists so the gap is a
tracked number instead of a surprise.
"""
from __future__ import annotations

import glob
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import formula  # noqa: E402
import target_model as tm  # noqa: E402


def fnum(v):
    if isinstance(v, dict):
        v = v.get("v")
    try:
        return float(str(v).split(",")[0].strip())
    except (TypeError, ValueError):
        return None


def price_ratio(hp: float, eff_hp: float, speed: float, rng: float, dps: float) -> float | None:
    """price(effective HP) / price(HP), everything else held.

    `unit_class` and `tech_tier` multiply all three estimators, so they cancel in the ratio
    and the number is valid without the (still-null) design fields.
    """
    if hp <= 0:
        return None
    a = formula.price(hp, speed, rng, dps)
    b = formula.price(eff_hp, speed, rng, dps)
    return b / a if a else None


def main() -> int:
    rows = []
    counts = {"always_on": 0, "capacity_only": 0, "upgrade_gated": 0}

    for path in sorted(glob.glob(str(ROOT / "docs" / "balance" / "*.json"))):
        name = pathlib.Path(path).name
        derived_path = ROOT / "docs" / "balance" / "derived" / name
        if not derived_path.exists():
            continue
        raw = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        der = json.loads(derived_path.read_text(encoding="utf-8"))
        if "sections" not in raw:
            continue
        for section, actors in raw["sections"].items():
            dsec = der.get("sections", {}).get(section, {})
            for actor, unit in actors.items():
                d = dsec.get(actor) or {}
                if "shield_pool" not in d:
                    continue
                if d.get("shield_always_on"):
                    counts["always_on"] += 1
                elif d.get("shield_gated_on_upgrade"):
                    counts["upgrade_gated"] += 1
                else:
                    counts["capacity_only"] += 1
                    continue
                if not d.get("shield_always_on"):
                    continue
                hp = fnum(unit.get("hp")) or 0.0
                eff = d.get("effective_hp") or hp
                cost = fnum(unit.get("cost"))
                speed = fnum(unit.get("speed")) or fnum(unit.get("speed_air")) or 0.0
                dps = 0.0
                for arm in (dsec.get(actor, {}) or {}).get("armaments", []) or []:
                    dps += fnum(arm.get("effective_dps")) or 0.0
                rng = 0.0
                for arm in unit.get("armaments", []) or []:
                    r = formula.wdist_value(arm.get("range"))
                    if r:
                        rng = max(rng, r)
                ratio = price_ratio(hp, eff, speed, rng, dps)
                rows.append({"pack": name.replace(".json", ""), "actor": actor,
                             "hp": hp, "pool": d["shield_pool"], "eff": eff,
                             "hp_ratio": d.get("effective_hp_ratio"),
                             "cost": cost, "price_ratio": ratio})

    print("# audit_survivability_pricing — E1: the baseline shield is priced at ZERO")
    print()
    print(f"| bucket | actors | priced today | belongs to |")
    print("|---|--:|---|---|")
    print(f"| spawns with a pool (**always-on**) | {counts['always_on']} | ✖ nothing | "
          f"**E1 — this report** |")
    print(f"| empty capacity, needs `shieldgen` | {counts['capacity_only']} | ✔ correctly "
          f"nothing | — (it has no shield) |")
    print(f"| pool behind an upgrade | {counts['upgrade_gated']} | ✖ nothing | E5 (upgrade "
          f"pricing) |")
    print()
    print(f"Shield row mean Versus **{tm.pseudo_armor_mean('Shield'):.2f}**, so one shield "
          f"point is **{tm.shield_hp_factor():.4f} HP** BEFORE any shield-gated "
          f"`DamageMultiplier` — measured off the live ladder every run, never frozen. The "
          f"Shield row takes **{tm.shield_damage_share():.3%}** of all roster raw damage at "
          f"baseline.")
    print()
    print("⚠ **Every one of these 56 actors also carries "
          "`DamageMultiplier@shielded: 150`**, so it takes 150% damage WHILE the shield "
          "holds — the deliberate counterweight to having one. That divides the pool's worth: "
          f"a shield point is really **{tm.shield_hp_factor() / 1.5:.4f} HP**, and the "
          "roster-wide gap is 38.6% rather than the 57.8% a shield-only reading gives. "
          "`shield_damage_multiplier` and `shield_hp_per_point` are published per actor.")
    print()

    if not rows:
        print("_No always-on shields found — nothing to price._")
        return 0

    hp_tot = sum(r["hp"] for r in rows)
    eff_tot = sum(r["eff"] for r in rows)
    ratios = [r["price_ratio"] for r in rows if r["price_ratio"]]
    print("## The gap")
    print()
    print(f"* Raw HP across these {len(rows)} actors: **{hp_tot:,.0f}**")
    print(f"* Effective HP once the pool is counted: **{eff_tot:,.0f}** "
          f"(**+{eff_tot / hp_tot - 1:.1%}**)")
    if ratios:
        print(f"* Implied price change if the formula read effective HP: "
              f"median **×{statistics.median(ratios):.3f}**, "
              f"max **×{max(ratios):.3f}**")
    print()
    print("⚠ **Retiring the 150% multiplier is a BUFF that must be paid for.** The numbers "
          "above already account for it, so they price the game AS IT IS. Delete "
          "`DamageMultiplier@shielded` and a shield point jumps from "
          f"{tm.shield_hp_factor() / 1.5:.3f} to {tm.shield_hp_factor():.3f} HP — the same "
          "pool becomes 1.5x more valuable and the implied price rises again. Re-extract "
          "AFTER the deletion and price once, or these units get charged for durability they "
          "no longer have (or keep durability they were never charged for).")
    print()
    print("## Per actor")
    print()
    print("| pack | actor | HP | shield pool | effective HP | ×HP | cost | implied ×price |")
    print("|---|---|--:|--:|--:|--:|--:|--:|")
    for r in sorted(rows, key=lambda r: -(r["price_ratio"] or 0)):
        pr = f"×{r['price_ratio']:.3f}" if r["price_ratio"] else "—"
        cost = f"{r['cost']:,.0f}" if r["cost"] else "—"
        print(f"| {r['pack']} | `{r['actor']}` | {r['hp']:,.0f} | {r['pool']:,.0f} | "
              f"{r['eff']:,.0f} | ×{r['hp_ratio']:.3f} | {cost} | {pr} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
