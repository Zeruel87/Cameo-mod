#!/usr/bin/env python3
"""Audit scalable K, standalone percentage floors, and folded-damage coverage.

The whole pricing model rests on one claim (`weapon_efficiency` docstring):

    effective_per_shot = Damage_total x K_flat_context
                         + pct_absolute_context
                         + folded_rounding_context

so that solving for Damage is closed-form. That claim is only true if `K_flat` really is
invariant under a change of flat `Damage`. Nothing proved it, and for two years it was
FALSE of the number the ledger actually published:

  E4, measured 2026-08-17 — `k` folded the %-of-max-HP twin's contribution in as
  `share = ref_hp x pct_damage / 100 / flat_total`. That share carries `flat_total` in its
  DENOMINATOR, so `k` moves when Damage moves: doubling `AnthraxCloudLarge`'s flat Damage
  drops its `k` by 37%. Inverting through it to reach 2x the DPS prescribes 40% of the
  Damage actually needed, and asking for LESS than the twin already delivers yields a
  negative headroom that the old code silently returned as a positive Damage.

  ⚠ `k` is not WRONG as a measurement — `effective_per_shot = damage_total x k_context`
  reproduces the truth exactly at the weapon's current Damage, so every `effective_*`
  number in the ledger is sound. `k` is wrong as a SHAPE COEFFICIENT. This audit exists to
  keep those two roles from being confused again.

Three checks:

  **L1 — `k_flat` is invariant** under scaling every flat `Damage` by 2x and by 0.5x.
  **L0 — every positive offensive runtime percentage application is modeled**, whether
  folded or standalone. Negative repair/healing applications are outside damage pricing.
  **L2 — the measurement identity holds**, including the folded runtime residual.
  **L3 — standalone percentage FLOORS are reported.** Folded ``PercentageScale`` damage is
  scalable and explicitly excluded from the floor.
  **L4 — folded rounding is visible**, never silently promoted into a permanent floor.
"""
from __future__ import annotations

from collections import Counter
import copy
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import weapon_efficiency as we  # noqa: E402
import percentage_damage as pd  # noqa: E402
from formula import parse_int32  # noqa: E402
from miniyaml import Ruleset  # noqa: E402

# k_flat is a ratio of sums, so only float noise should move it.
TOL = 1e-9
# Above this share of output, a weapon's %-twin floor dominates its price. Reported, not failed.
FLOOR_NOTE = 0.25
# ⚠ INTEGER factors only. Damage is an engine Int32, so a 0.5x factor would require choosing
# how to round odd values such as 1755 and would
# shifts the per-warhead shares by a fraction of a unit. That artifact of the TEST showed up as
# a 0.01% drift on 10 weapons and would have been read as a defect in the MODEL. Multiplying an
# integer Damage by an integer stays exact, so any drift these report is real. Proportionality
# is symmetric: invariance under 2x/4x/10x is the same claim as invariance under 0.5x.
SCALES = (2, 4, 10)
RUNTIME_STANDALONE_TYPES = frozenset({"AreaDamagePercentage", "HealthPercentageDamage"})


def _positive_int(raw, default: int | None = None) -> int | None:
    try:
        value = parse_int32(raw, default=default)
    except (TypeError, ValueError):
        value = default
    return value if value is not None and value > 0 else None


def runtime_percentage_inventory(node) -> Counter:
    """Independently enumerate positive offensive percentage shapes in the C# types.

    This deliberately does not call percentage_damage.percentage_applications:
    comparing a helper to itself would let a newly missed warhead type pass L0.
    """
    found = Counter()
    for child in node.children:
        if not child.key.startswith("Warhead"):
            continue
        tag = child.key.split("@", 1)[1] if "@" in child.key else child.key
        damage = _positive_int(child.get("Damage"))
        if damage is None:
            continue
        if child.value == "HealthPercentageDamage":
            # This C# type always uses whole-percent units and owns no
            # PercentageDenominator field.
            found[(pd.PCT_STANDALONE, tag)] += 1
        elif child.value == "AreaDamagePercentage":
            denominator = _positive_int(
                child.get("PercentageDenominator"), pd.STANDALONE_DEFAULT_DENOMINATOR)
            if denominator is not None:
                found[(pd.PCT_STANDALONE, tag)] += 1
        # AreaDamagePercentage inherits the folded implementation too, but the
        # C# loader now rejects that nonsensical double-percentage combination.
        # Keep it in this independent inventory so L0 still fails if such a node
        # ever slips into the rules without validation.
        if child.value in {"AreaDamage", "AreaDamagePercentage"}:
            scale = _positive_int(child.get("PercentageScale"))
            denominator = _positive_int(
                child.get("PercentageDenominator"), pd.FOLDED_DEFAULT_DENOMINATOR)
            if scale is not None and denominator is not None:
                found[(pd.PCT_FOLDED, tag)] += 1
    return found


def scale_flat(node, factor: float):
    """The weapon with every flat warhead's Damage multiplied.

    Standalone percentage warheads stay untouched. Folded percentage damage follows
    automatically because its PercentageScale lives on the scaled AreaDamage node.

    The audit factors are integers, so every transformed Damage remains a valid exact
    engine Int32. This preserves per-warhead shares without introducing a rounding choice.
    """
    out = copy.deepcopy(node)
    for c in out.children:
        if not c.key.startswith("Warhead") or "Percentage" in str(c.value or ""):
            continue
        for g in c.children:
            if g.key != "Damage":
                continue
            try:
                original = parse_int32(g.value, "Damage")
                g.value = str(parse_int32(original * factor, "scaled Damage"))
            except (TypeError, ValueError):
                pass
    return out


def main() -> int:
    rs = Ruleset(ROOT)
    nodes = []
    rows = []
    for name in rs.weapons:
        if name.startswith("^"):
            continue
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        nodes.append((name, node))
        try:
            res = we.analyse(node)
        except Exception:  # noqa: BLE001 - a broken weapon is another audit's job
            continue
        if res is not None:
            rows.append((name, node, res))

    failed = 0
    print("# audit_k_linearity — the flat K must not move when Damage moves")
    print()
    print(f"Analysed **{len(rows)}** concrete weapons.")
    print()

    # ---- L0 -----------------------------------------------------------------
    print("## L0 — every positive offensive runtime percentage application is modeled")
    print()
    uncovered = []
    result_by_name = {name: res for name, _node, res in rows}
    for name, node in nodes:
        expected = runtime_percentage_inventory(node)
        res = result_by_name.get(name)
        modeled = Counter(
            (part["kind"], part["tag"])
            for part in (res or {}).get("parts", []) if part["kind"].startswith("pct_"))
        if expected != modeled:
            uncovered.append((name, expected - modeled, modeled - expected))
    if uncovered:
        failed = 1
        print(f"**FAIL — {len(uncovered)} weapon(s) have unmodeled or duplicate percentage hits.**")
        print()
        print("| weapon | missing | unexpected |")
        print("|---|---|---|")
        for name, missing, unexpected in uncovered[:25]:
            miss = ", ".join(f"{kind}:{tag} x{count}" for (kind, tag), count in missing.items())
            extra = ", ".join(
                f"{kind}:{tag} x{count}" for (kind, tag), count in unexpected.items())
            print(f"| `{name}` | {miss or '—'} | {extra or '—'} |")
    else:
        folded = sum(
            part["kind"] == pd.PCT_FOLDED for _name, _node, res in rows
            for part in res["parts"])
        standalone = sum(
            part["kind"] == pd.PCT_STANDALONE for _name, _node, res in rows
            for part in res["parts"])
        print(f"_clean_ — modeled {folded} folded and {standalone} standalone applications.")
    print()

    # ---- L1 -----------------------------------------------------------------
    print("## L1 — `k_flat` is invariant under a change of flat Damage")
    print()
    drifted = []
    scale_errors = []
    for name, node, res in rows:
        if res["k_flat"] <= 0:
            continue
        for factor in SCALES:
            try:
                alt = we.analyse(scale_flat(node, factor))
            except Exception as exc:  # noqa: BLE001
                scale_errors.append((name, factor, str(exc)))
                continue
            if alt is None:
                scale_errors.append((name, factor, "scaled analysis returned no result"))
                continue
            drift = abs(alt["k_flat"] - res["k_flat"]) / res["k_flat"]
            if drift > TOL:
                drifted.append((name, factor, res["k_flat"], alt["k_flat"], drift))
    if drifted or scale_errors:
        failed = 1
        print(f"**FAIL — {len(drifted)} drift(s) and {len(scale_errors)} "
              "failed scaled analysis case(s).**")
        print()
        if drifted:
            print("| weapon | Damage x | k_flat | k_flat scaled | drift |")
            print("|---|--:|--:|--:|--:|")
            for name, factor, a, b, d in sorted(drifted, key=lambda r: -r[4])[:25]:
                print(f"| `{name}` | {factor:g} | {a:.4f} | {b:.4f} | {d:.2%} |")
        if scale_errors:
            print()
            print("| weapon | Damage x | analysis error |")
            print("|---|--:|---|")
            for name, factor, error in scale_errors[:25]:
                print(f"| `{name}` | {factor:g} | {error} |")
    else:
        print(f"_clean_ — `k_flat` held to within {TOL:g} across "
              f"{len(SCALES)} scalings of every weapon.")
    print()

    # ---- L2 -----------------------------------------------------------------
    print("## L2 — the scalable/absolute split decomposes the published `k`")
    print()
    print("`k == k_flat + (pct_absolute + folded_rounding) / damage_total`. The "
          "standalone term is a floor; the folded term is the current runtime "
          "quantisation residual.")
    print()
    broken = []
    undefined = []
    for name, _node, res in rows:
        total = res["damage_total"]
        if total <= 0:
            if res["k"] is not None or res["k_context"] is not None:
                broken.append((name, res["k"], None))
            else:
                undefined.append(name)
            continue
        rebuilt = res["k_flat"] + (
            res["pct_absolute"] + res["folded_rounding"]) / total
        if res["k"] is None or (res["k"] > 0 and
                                abs(rebuilt - res["k"]) / res["k"] > 1e-9):
            broken.append((name, res["k"], rebuilt))
    if broken:
        failed = 1
        print(f"**FAIL — {len(broken)} weapon(s) where the identity does not hold.**")
        print()
        print("| weapon | k | rebuilt k |")
        print("|---|--:|--:|")
        for name, k, rebuilt in broken[:25]:
            k_text = "undefined" if k is None else f"{k:.6f}"
            rebuilt_text = "undefined" if rebuilt is None else f"{rebuilt:.6f}"
            print(f"| `{name}` | {k_text} | {rebuilt_text} |")
    else:
        suffix = (f"; {len(undefined)} percentage-only weapon(s) correctly have no "
                  "flat-Damage denominator" if undefined else "")
        print(f"_clean_ — the identity holds for every analysed weapon{suffix}.")
    print()

    # ---- L3 -----------------------------------------------------------------
    print("## L3 — weapons with a standalone percentage DPS floor")
    print()
    floors = []
    for name, _node, res in rows:
        total = (res["flat_total"] * res["k_flat_context"] +
                 res["pct_absolute_context"] + res["folded_rounding_context"])
        if total > 0 and res["pct_absolute_context"] > 0:
            floors.append((name, res["pct_absolute_context"] / total))
    heavy = sorted((r for r in floors if r[1] >= FLOOR_NOTE), key=lambda r: -r[1])
    print(f"{len(floors)} weapon(s) carry a standalone percentage hit; **{len(heavy)}** "
          f"have a floor at or "
          f"above {FLOOR_NOTE:.0%} of output.")
    print()
    if heavy:
        print("A price target below the floor is UNREACHABLE by lowering flat Damage — "
              "`required_damage()` returns None rather than a wrong positive number. To "
              "price these lower, the standalone percentage hit has to shrink.")
        print()
        print("| weapon | floor as share of output |")
        print("|---|--:|")
        for name, share in heavy[:30]:
            print(f"| `{name}` | {share:.1%} |")
        if len(heavy) > 30:
            print()
            print(f"_... and {len(heavy) - 30} more._")
    else:
        print("_none above the reporting threshold._")
    print()

    # ---- L4 -----------------------------------------------------------------
    print("## L4 — folded runtime quantisation residual")
    print()
    rounded = sorted(
        ((name, res["folded_rounding_context"])
         for name, _node, res in rows if abs(res["folded_rounding_context"]) >= 1e-9),
        key=lambda row: -abs(row[1]))
    print(f"{len(rounded)} weapon(s) have a non-zero current folded runtime residual.")
    print("This residual is included in measured output but excluded from `k_flat` and "
          "`dps_floor`; recompute it after snapping a proposed Damage value.")
    if rounded:
        print()
        print("| weapon | context-adjusted residual per shot |")
        print("|---|--:|")
        for name, residual in rounded[:30]:
            print(f"| `{name}` | {residual:+.4f} |")
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
