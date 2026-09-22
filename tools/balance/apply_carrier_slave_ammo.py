#!/usr/bin/env python3
"""apply_carrier_slave_ammo.py — give every carrier slave a sized pool and a reload (R8).

GENERATED, never hand-typed: the numbers come from `carrier_slave_ammo.plan()`, whose
self-test reproduces both of the maintainer's worked examples. This script only decides WHERE
to write them.

THE BUG BEING FIXED. Carrier slaves need an ammo pool, an explicit ammo-dependent firing gate,
and a reload policy. A pool alone does not stop a shot: `AmmoPool` consumes ammo from its
`INotifyAttack` callback after the attack has been selected. `AmmoCondition` plus the attack and
armament gates below make an empty pool refuse the next attack.

The carrier engine also refills every pool when a slave re-enters its carrier. The generated
`ReloadAmmoPool` is therefore an explicit in-flight reload policy, not a repair for a nonexistent
carrier refill path.

All 19 `CarrierSlave` actors originally broke the pool/reload/gate contract, in two opposite ways:

  * NO POOL  -> `CarrierSlave.cs:59-65` returns early, commented "The unit may not have ammo
    but will have unlimited ammunitions." The slave never expends, never needs to dock, and
    the carrier's launch/expend/return cycle never runs at all.
  * POOL, NO RELOAD -> the slave has no explicit in-flight reload policy. The carrier itself
    refills the pool on re-entry; whether it can attack between launches still depends on the
    carrier cycle and the attack gate.

⚠ `AmmoPool.Armaments` DEFAULTS to ("primary", "secondary") and consumption is gated on it —
`AmmoPool.Attacking` calls `TakeAmmo` only when `Info.Armaments.Contains(a.Info.Name)`. An
armament with any other `Name` silently spends nothing, so the pool would never empty. The
list is written whenever the default does not cover every armament.

Usage:  python tools/balance/apply_carrier_slave_ammo.py [--apply]
        (dry run prints the plan and restores the tree; --apply leaves it dirty -- BOOT GATE)
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import carrier_slave_ammo as law  # noqa: E402
import miniyaml  # noqa: E402
import yaml_ops  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
POOL_STEMS = ("AmmoPool", "AmmoPoolCA")
RELOAD_STEMS = ("ReloadAmmoPool", "ReloadAmmoPoolCA")


def checked_plan_paths(root: pathlib.Path, manifest_paths, plan) -> list[str]:
    """Return repo-relative plan paths after proving they are active rule files."""
    resolved_root = root.resolve()
    allowed = {pathlib.Path(path).resolve() for path in manifest_paths}
    out = []
    for raw in plan:
        path = (root / raw).resolve()
        try:
            rel = path.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"plan path escapes repository root: {raw}") from exc
        if path not in allowed:
            raise ValueError(f"plan path is not an active rules file: {rel.as_posix()}")
        out.append(rel.as_posix())
    return sorted(set(out))


def dirty_plan_paths(root: pathlib.Path, paths: list[str]) -> list[str]:
    """Porcelain records for affected files only; an unrelated dirty file is preserved."""
    if not paths:
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *paths],
        cwd=root, check=True, capture_output=True, text=True, encoding="utf-8")
    return [line for line in result.stdout.splitlines() if line.strip()]


def kv(node):
    return {c.key: str(c.value).strip() for c in node.children}


def stem(key: str) -> str:
    return key.split("@")[0].lstrip("-")


def collect(rs):
    """[(actor_name, src_node, resolved, arms, plan)] for the in-scope slaves, plus skips."""
    out, skipped = [], []
    for name in sorted(rs.actors):
        if name.startswith(("^", "-")):
            continue
        res = rs.resolve(name)
        if res is None or not any(stem(c.key) == "CarrierSlave" for c in res.children):
            continue
        src = rs.actors[name]
        stems = {stem(c.key) for c in res.children}
        arms = []
        for a in [c for c in res.children if stem(c.key) == "Armament"]:
            d = kv(a)
            w = rs.resolve_weapon(d.get("Weapon", "") or "")
            wv = kv(w) if w is not None else {}
            try:
                burst = int(wv.get("Burst", "1").split(",")[0])
            except ValueError:
                burst = 1
            arms.append({"key": a.key, "name": d.get("Name", "primary"), "burst": burst,
                         "cond": d.get("RequiresCondition"), "targets": wv.get("ValidTargets"),
                         "weapon": d.get("Weapon"), "cur_usage": d.get("AmmoUsage"),
                         "local": src.child(a.key), "resolved": a})
        why = law.is_suicide(name, stems, [a["weapon"] for a in arms])
        if why:
            skipped.append((name, why))
            continue
        out.append((name, src, res, arms, law.plan(arms)))
    return out, skipped


def build_plan(rs):
    plan = yaml_ops.new_plan()
    rows, skipped = collect(rs)
    notes = []

    for name, src, res, arms, p in rows:
        if p["ammo"] <= 0:
            notes.append((name, "no scoring armament - skipped"))
            continue
        after = yaml_ops.insert_after_inherits(src)
        add: list[str] = []

        # ---- the pool ---------------------------------------------------- #
        pools = [c for c in res.children if stem(c.key) in POOL_STEMS]
        want_arms = law.pool_armaments(arms)
        if pools:
            local = src.child(pools[0].key)
            cur = kv(pools[0])
            if local is not None and local.child("Ammo") is not None:
                node = local.child("Ammo")
                plan[node.file][node.line].append(
                    ("sub", f"Ammo: {cur['Ammo']}", f"Ammo: {p['ammo']}"))
            else:
                # inherited pool: override just the field, keyed identically so it merges
                add.append(f"\t{pools[0].key}:")
                add.append(f"\t\tAmmo: {p['ammo']}")
            if cur.get("AmmoCondition") is None:
                if local is not None:
                    plan[local.file][local.line].append(("ins", ["\t\tAmmoCondition: ammo"]))
                else:
                    add.append(f"\t\tAmmoCondition: ammo")
            if want_arms and cur.get("Armaments") is None:
                add.append(f"\t{pools[0].key}:" if not add else "")
                add.append(f"\t\tArmaments: {', '.join(want_arms)}")
        else:
            add.append("\tAmmoPool:")
            add.append(f"\t\tAmmo: {p['ammo']}")
            add.append("\t\tAmmoCondition: ammo")
            if want_arms:
                add.append(f"\t\tArmaments: {', '.join(want_arms)}")

        # ---- empty-pool firing gate ------------------------------------- #
        pool_condition = (kv(pools[0]).get("AmmoCondition") if pools else None) or "ammo"
        attack = res.child("AttackAircraft")
        if attack is not None and kv(attack).get("RequiresCondition") is None:
            local_attack = src.child("AttackAircraft")
            if local_attack is not None:
                plan[local_attack.file][local_attack.line].append(
                    ("ins", [f"\t\tRequiresCondition: {pool_condition}"]))
            else:
                add.extend(["\tAttackAircraft:", f"\t\tRequiresCondition: {pool_condition}"])

        pool_names = set(want_arms or law.DEFAULT_POOL_ARMAMENTS)
        for a in arms:
            try:
                usage = int(str(p["usage"].get(a["key"], a.get("cur_usage") or "1")).split(",")[0])
            except ValueError:
                usage = 1
            if a["name"] not in pool_names or usage <= 0:
                continue
            expected_pause = law.minimum_ammo_pause(pool_condition, usage)
            existing_pause = kv(a["resolved"]).get("PauseOnCondition")
            existing_requires = kv(a["resolved"]).get("RequiresCondition", "")
            if law.pause_gate_sufficient(pool_condition, usage, existing_pause,
                                         existing_requires,
                                         global_gate=False):
                continue
            local_arm = a["local"]
            if local_arm is not None:
                pause_node = local_arm.child("PauseOnCondition")
                if existing_pause is not None and pause_node is not None:
                    plan[pause_node.file][pause_node.line].append(
                        ("sub", f"\t\tPauseOnCondition: {existing_pause}",
                         f"\t\tPauseOnCondition: {law.preserved_pause(existing_pause, pool_condition, usage)}"))
                else:
                    plan[local_arm.file][local_arm.line].append(
                        ("ins", [f"\t\tPauseOnCondition: {law.preserved_pause(existing_pause, pool_condition, usage)}"]))
            else:
                add.extend([f"\t{a['key']}:",
                            f"\t\tPauseOnCondition: {law.preserved_pause(existing_pause, pool_condition, usage)}"])

        # ---- the reload -------------------------------------------------- #
        reloads = [c for c in res.children if stem(c.key) in RELOAD_STEMS]
        if reloads:
            notes.append((name, f"already has {reloads[0].key} - left alone"))
        else:
            add.append("\tReloadAmmoPool:")
            add.append(f"\t\tDelay: {p['delay']}")
            add.append(f"\t\tCount: {p['count']}")

        # ---- per-armament AmmoUsage -------------------------------------- #
        for a in arms:
            want = p["usage"].get(a["key"])
            if want is None or str(want) == str(a["cur_usage"]):
                continue
            local = a["local"]
            if local is not None:
                existing = local.child("AmmoUsage")
                if existing is not None:
                    plan[existing.file][existing.line].append(
                        ("sub", f"AmmoUsage: {str(existing.value).strip()}",
                         f"AmmoUsage: {want}"))
                else:
                    plan[local.file][local.line].append(("ins", [f"\t\tAmmoUsage: {want}"]))
            else:
                # inherited armament: a bare local override merges onto it by key
                add.append(f"\t{a['key']}:")
                add.append(f"\t\tAmmoUsage: {want}")

        add = [ln for ln in add if ln]
        if add:
            plan[src.file][after].append(("ins", add))

    return plan, rows, skipped, notes


def report_result(n, rows, skipped, notes):
    print(f"SKIPPED {len(skipped)} suicide slaves (a reload is dead weight on a unit that "
          f"dies when it attacks):")
    for name, why in skipped:
        print(f"   {name:24s} {why}")

    print(f"\nIN SCOPE {len(rows)} — edits {n}\n")
    print(f"{'actor':26s} {'Ammo':>5s} {'N':>2s} {'share':>5s} {'Count':>5s} {'Delay':>5s}  "
          f"refill  AmmoUsage")
    for name, _src, _res, arms, p in rows:
        if p["ammo"] <= 0:
            continue
        refill = p["ammo"] / p["count"] * p["delay"]
        usage = " ".join(
            f"{a['key'].replace('Armament', 'A')}={p['usage'].get(a['key'])}"
            f"{'' if p['roles'][a['key']] == 'score' else '(' + p['roles'][a['key']][0] + ')'}"
            for a in arms)
        print(f"{name:26s} {p['ammo']:5d} {p['n']:2d} {p['share']:5d} {p['count']:5d} "
              f"{p['delay']:5d}  {refill:5.0f}t  {usage}")

    # The invariant the ruling states, asserted per actor rather than trusted.
    bad = []
    for name, _src, _res, arms, p in rows:
        if p["ammo"] <= 0:
            continue
        if p["ammo"] / p["count"] * p["delay"] != law.RELOAD_TICKS:
            bad.append((name, "refill is not 100 ticks"))
        groups = {}
        for a in arms:
            if p["roles"][a["key"]] != "score":
                continue
            for target in law.target_set(a.get("targets")):
                groups.setdefault(target, 0)
                groups[target] += a["burst"] * p["usage"][a["key"]]
        if groups and max(groups.values()) != p["ammo"]:
            bad.append((name, f"a full attack spends {max(groups.values())}, pool {p['ammo']}"))
    print("\nINVARIANTS (refill == 100 ticks; one full attack empties the pool exactly)")
    if bad:
        for name, why in bad:
            print(f"   FAIL {name:24s} {why}")
    else:
        print("   all pass")
    for name, note in notes:
        print(f"   note {name:24s} {note}")
    return bad


def apply_with_cleanup(plan, root: pathlib.Path, paths: list[str], keep_on_success: bool,
                       evaluator):
    """Apply a clean plan and restore it on dry run, failed invariants, or any exception."""
    try:
        n = yaml_ops.apply_plan(plan, root)
        result = evaluator(n)
    except BaseException:
        yaml_ops.git_restore(root, paths)
        raise
    if not keep_on_success or result:
        yaml_ops.git_restore(root, paths)
    return n, result


def main() -> int:
    apply_it = "--apply" in sys.argv
    rs = miniyaml.Ruleset(str(ROOT))

    plan, rows, skipped, notes = build_plan(rs)
    paths = checked_plan_paths(ROOT, rs.manifest.rules, plan)
    dirty = dirty_plan_paths(ROOT, paths)
    if dirty:
        print("REFUSED: affected rule files already have local changes:")
        for line in dirty:
            print(f"   {line}")
        print("Commit, stash, or move those changes before running this writer.")
        return 2

    n, bad = apply_with_cleanup(
        plan, ROOT, paths, apply_it,
        lambda edits: report_result(edits, rows, skipped, notes))

    if not apply_it or bad:
        print("\ntree restored." if bad else
              "\ndry run - tree restored. Re-run with --apply, then BOOT GATE.")
        return 1 if bad else 0
    print("\nWRITTEN. Boot-gate before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
