#!/usr/bin/env python3
"""review_batch_diff.py — did a whole W24 batch preserve behaviour?

`review_resolve_diff.py` verifies weapons you NAME. This verifies the ones you did not think
to name, which is where the defects were: it resolves **every** weapon in two repo roots and
diffs the invariants a structural retrofit must never change.

    python tools/audit/review_batch_diff.py <base_root> <head_root> [--json out.json]

⛔ WHY THIS EXISTS (2026-08-19). A 39-commit W24 batch shipped seven weapons with 30–93% of
their damage missing — `SCUDNUKE` 300000 -> 20000 — plus a weapon that lost its firing sound
and two that silently gained air-targeting. Every existing guard passed: the tree booted, 227
tests were green, `find_empty_warhead` was 0, every doc claim matched. The maintainer found it
by asking *"did it just delete all the other warheads without adjusting the sum?"* — which is a
question no guard in the suite was asking. This asks it.

⚠ THE MEASUREMENT TRAP THAT MADE IT LOOK 7x WORSE. A raw total-damage diff flagged **52**
weapons. Only 7 were defects; the other 45 were the intended `DamagesConcrete` dedup, which
collapses two concrete warheads into one and legitimately moves the total by 1–7%. So
`Warhead@*Concrete*` is excluded from the damage comparison by default (`--with-concrete` to
include it). Judge main damage on main warheads, or the real signal drowns.

⚠ BLAST SHAPE IS REPORTED, NEVER FAILED, and it is the subtlest check here.
`AreaDamageWarhead.cs` splits Damage ACROSS ticks (`perTickModifier = Ticks > 1 ? 100 / Ticks
: 100`), so `Ticks` is TOTAL-PRESERVING: collapsing a 10-ring nuclear shockwave onto a family
with no `Ticks` keeps every point of damage and still turns an expanding blast into one
instantaneous thump. A damage check alone cannot see that, so `Spread`/`Falloff`/`Ticks`/
`MaxRadius` are diffed too — as a REPORT, because changing the shape is often the whole point
of moving a weapon onto a family.

EXIT CODE: 1 if damage, runtime percentage damage, armor/percentage-armor profiles,
percentage-warhead profiles, cadence, targeting, reports, projectiles, or non-damage warheads
change. Blast shape remains report-only because choosing a standard family may intentionally
replace the old stack's geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "balance"))
from cameo_model import Model  # noqa: E402
import percentage_damage as pd  # noqa: E402


# Keep the design reference in the matrix even when no active actor currently
# authors that exact HP. Active authored HP values are added below so the audit
# also catches live folded-percentage quantisation and checked-result overflow.
PERCENTAGE_REFERENCE_HP = 200_000


def _dmg(node) -> float | None:
    try:
        return float(str(node.get("Damage")).strip())
    except (TypeError, ValueError):
        return None


def active_health_values(root: str) -> list[int]:
    """Every positive Health.HP value on an active concrete actor."""
    rs = Model(pathlib.Path(root)).rs
    values = {PERCENTAGE_REFERENCE_HP}
    for name in rs.actors:
        if name.startswith("^"):
            continue
        node = rs.resolve(name)
        health = node.child("Health") if node is not None else None
        raw = health.get("HP") if health is not None else None
        if raw is None:
            continue
        try:
            hp = int(str(raw).strip())
        except ValueError:
            continue
        if hp > 0:
            values.add(hp)
    return sorted(values)


def _node_fingerprint(node) -> tuple:
    """Order-insensitive recursive MiniYAML fingerprint."""
    return (
        node.key,
        node.value,
        tuple(sorted(_node_fingerprint(child) for child in node.children)),
    )


def _behavior_fingerprint(node) -> tuple:
    """Recursive fingerprint that ignores only the local slot name."""
    return (
        node.value,
        tuple(sorted(_node_fingerprint(child) for child in node.children)),
    )


def _target_tokens(raw: str | None) -> tuple[str, ...]:
    return tuple(sorted(token.strip() for token in (raw or "").split(",") if token.strip()))


def _versus_profile(node, field: str) -> tuple[tuple[str, str], ...]:
    block = node.child(field)
    if block is None:
        return ()
    return tuple(sorted((child.key, str(child.value)) for child in block.children))


def _physical_state_entries(node) -> tuple[tuple[str, str], ...]:
    """Enabled physical-state bindings, including the singular and map forms."""
    out: list[tuple[str, str]] = []
    name = node.get("PhysicalStateName")
    scale = node.get("PhysicalStateScale") or "0"
    if name and scale.strip() != "0":
        out.append((name, scale))
    states = node.child("PhysicalStates")
    if states is not None:
        for entry in states.children:
            entry_scale = entry.value or "0"
            if entry.key and entry_scale.strip() != "0":
                out.append((entry.key, entry_scale))
    return tuple(sorted(out))


def snapshot(root: str, with_concrete: bool, health_values: list[int]) -> dict[str, dict]:
    """Resolved behavioural fingerprint for every concrete weapon in one repo root."""
    rs = Model(pathlib.Path(root)).rs
    for owner, raw in rs.weapons.items():
        for child in raw.children:
            if not child.key.startswith("Inherits"):
                continue
            parent = child.value.strip()
            if parent and parent not in rs.weapons:
                location = f"{child.file}:{child.line}" if child.file else owner
                raise ValueError(
                    f"{location}: weapon {owner} inherits missing parent {parent}")
    out: dict[str, dict] = {}
    for name in rs.weapons:
        if name.startswith("^"):
            continue
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        total, mains, shape, armor_profiles = 0.0, [], [], []
        valid_target_damage: dict[str, float] = {}
        invalid_target_damage: dict[str, float] = {}
        relationship_stat_damage: dict[tuple[str, bool, str], float] = {}
        physical_state_bindings: dict[tuple, float] = {}
        for wh in node.children:
            if not wh.key.startswith("Warhead"):
                continue
            if not with_concrete and "Concrete" in wh.key:
                continue
            rel = (wh.get("ValidRelationships") or "").strip()
            d = _dmg(wh)
            if d is not None and d > 0:
                for physical_state, state_scale in _physical_state_entries(wh):
                    state_key = (
                        physical_state,
                        state_scale,
                        wh.value,
                        _target_tokens(wh.get("ValidTargets")),
                        _target_tokens(wh.get("InvalidTargets")),
                    )
                    physical_state_bindings[state_key] = physical_state_bindings.get(state_key, 0) + d
            if d is not None and d > 0 and "Percentage" not in wh.key:
                relationships = _target_tokens(rel) or ("Ally", "Enemy", "Neutral")
                targets = _target_tokens(wh.get("ValidTargets")) or ("*",)
                updates_stats = (wh.get("UpdatesUnitStatistics") or "true").lower() != "false"
                try:
                    friendly_modifier = float(wh.get("FriendlyFireDamage") or 100) / 100
                except ValueError:
                    friendly_modifier = 1.0
                for relationship in relationships:
                    relationship_damage = d * (friendly_modifier if relationship == "Ally" else 1)
                    for target in targets:
                        key = (relationship, updates_stats, target)
                        relationship_stat_damage[key] = relationship_stat_damage.get(key, 0) + relationship_damage
                if "Ally" in rel and "Enemy" not in rel:  # friendly-fire twin, not a main
                    continue
                total += d
                mains.append(int(d))
                armor_profiles.append((
                    wh.key.split("@", 1)[-1],
                    int(d),
                    _versus_profile(wh, "Versus"),
                    _versus_profile(wh, "PercentageVersus"),
                ))
                for target in _target_tokens(wh.get("ValidTargets")):
                    valid_target_damage[target] = valid_target_damage.get(target, 0) + d
                for target in _target_tokens(wh.get("InvalidTargets")):
                    invalid_target_damage[target] = invalid_target_damage.get(target, 0) + d
                # The blast GEOMETRY. Damage says how much; this says where and over how long.
                # `Ticks` is the expanding-shockwave count — `AreaDamageWarhead.cs` splits Damage
                # ACROSS ticks (`perTickModifier = 100 / Ticks`), so dropping it preserves the sum
                # and silently changes a 10-ring nuclear shockwave into one instantaneous blast.
                shape.append("|".join(str(wh.get(k) or "-")
                                      for k in ("Spread", "Falloff", "Ticks", "MaxRadius")))
        projectile = node.child("Projectile")
        top_level = tuple(sorted(
            _node_fingerprint(child)
            for child in node.children
            if child.key != "Projectile" and not child.key.startswith("Warhead")
        ))
        non_damage_warheads = []
        percentage_warheads = []
        for wh in node.children:
            if not wh.key.startswith("Warhead"):
                continue
            if wh.value in ("AreaDamage", "SpreadDamage", "AreaDamagePercentage",
                            "HealthPercentageDamage"):
                if wh.value in ("AreaDamagePercentage", "HealthPercentageDamage"):
                    percentage_warheads.append(_behavior_fingerprint(wh))
                continue
            non_damage_warheads.append(_node_fingerprint(wh))

        out[name] = {
            "damage": total,
            "mains": sorted(mains, reverse=True),
            "percentage_damage": {
                hp: sum(
                    app["runtime_hp"]
                    for app in pd.percentage_applications(node, hp)
                    if "friendlyfire" not in app["tag"].lower())
                for hp in health_values
            },
            "shape": sorted(shape),
            "armor_profile": tuple(sorted(armor_profiles)),
            "valid_target_damage": tuple(sorted(valid_target_damage.items())),
            "invalid_target_damage": tuple(sorted(invalid_target_damage.items())),
            "relationship_stat_damage": tuple(sorted(relationship_stat_damage.items())),
            "physical_state_bindings": tuple(sorted(physical_state_bindings.items())),
            "Range": node.get("Range"),
            "ReloadDelay": node.get("ReloadDelay"),
            "Burst": node.get("Burst"),
            "ValidTargets": node.get("ValidTargets"),
            "InvalidTargets": node.get("InvalidTargets"),
            "Report": node.get("Report"),
            "StartBurstReport": node.get("StartBurstReport"),
            "top_level": top_level,
            "projectile": _node_fingerprint(projectile) if projectile is not None else None,
            "non_damage_warheads": tuple(sorted(non_damage_warheads)),
            "percentage_warheads": tuple(sorted(percentage_warheads)),
        }
    return out


OPERATING_BEHAVIOR = (
    "Range", "ReloadDelay", "Burst", "ValidTargets", "InvalidTargets",
    "Report", "StartBurstReport", "valid_target_damage", "invalid_target_damage",
    "relationship_stat_damage",
    "physical_state_bindings",
    "armor_profile",
    "percentage_warheads",
    "top_level", "projectile", "non_damage_warheads",
)


def compare(base: dict, head: dict) -> tuple[dict, list, list]:
    gone = sorted(set(base) - set(head))
    added = sorted(set(head) - set(base))
    changed: dict[str, list] = {}
    for w in sorted(set(base) & set(head)):
        b, h = base[w], head[w]
        diffs = []
        if abs(b["damage"] - h["damage"]) > 0.5:
            diffs.append(["main_damage", b["damage"], h["damage"]])
        percentage_mismatches = [
            [hp, b["percentage_damage"][hp], h["percentage_damage"][hp]]
            for hp in b["percentage_damage"]
            if abs(b["percentage_damage"][hp] - h["percentage_damage"][hp]) > 0.5
        ]
        if percentage_mismatches:
            diffs.append(["percentage_damage", percentage_mismatches])
        for k in OPERATING_BEHAVIOR:
            if (b[k] or "") != (h[k] or ""):
                diffs.append([k, b[k], h[k]])
        if b["shape"] != h["shape"]:
            diffs.append(["blast_shape", " ; ".join(b["shape"]), " ; ".join(h["shape"])])
        if diffs:
            changed[w] = diffs
    return changed, gone, added


def snapshot_digest(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=list)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base_root")
    ap.add_argument("head_root")
    ap.add_argument("--json", help="write the full per-weapon findings here")
    ap.add_argument("--with-concrete", action="store_true",
                    help="include Warhead@*Concrete* in the damage total (default: excluded — "
                         "the DamagesConcrete dedup is an INTENDED change and drowns the signal)")
    a = ap.parse_args()

    health_values = sorted(set(active_health_values(a.base_root)) |
                           set(active_health_values(a.head_root)))
    base = snapshot(a.base_root, a.with_concrete, health_values)
    head = snapshot(a.head_root, a.with_concrete, health_values)
    changed, gone, added = compare(base, head)

    print(f"# review_batch_diff — {len(base)} weapons in base, {len(head)} in head")
    if not a.with_concrete:
        print("_`Warhead@*Concrete*` excluded from damage (see --with-concrete)._")
    print()
    if gone:
        print(f"**{len(gone)} weapon(s) REMOVED:** {', '.join(gone[:12])}"
              f"{' …' if len(gone) > 12 else ''}")
    if added:
        print(f"**{len(added)} weapon(s) ADDED:** {', '.join(added[:12])}"
              f"{' …' if len(added) > 12 else ''}")

    by_kind: dict[str, list[str]] = {}
    for w, diffs in changed.items():
        for d in diffs:
            by_kind.setdefault(d[0], []).append(w)

    dmg = by_kind.get("main_damage", [])
    if dmg:
        print(f"\n## ⛔ FAIL — main damage changed on {len(dmg)} weapon(s)\n")
        print("`WEAPON_3WAY_SPLIT.md`: the retrofit *\"PRESERVES the weapon's existing on-grid "
              "value verbatim; it invents NO numbers\"*. A collapse must carry the TOTAL.\n")
        print("| factor | before | after | weapon |")
        print("|--:|--:|--:|---|")
        rows = []
        for w in dmg:
            b, h = base[w]["damage"], head[w]["damage"]
            rows.append((h / b if b else 999.0, b, h, w))
        for f, b, h, w in sorted(rows):
            print(f"| {f:.2f} | {b:.0f} | {h:.0f} | `{w}` |")
    else:
        print("\n## ✅ main damage preserved on every weapon")

    pct = by_kind.get("percentage_damage", [])
    if pct:
        print(f"\n## ⛔ FAIL — percentage damage changed on {len(pct)} weapon(s)\n")
        print(f"Values use the engine's integer arithmetic across {len(health_values)} "
              "active/design HP values, including the active maximum.\n")
        print("| target HP | before | after | weapon |")
        print("|--:|--:|--:|---|")
        for w in pct:
            mismatches = next(x[1] for x in changed[w] if x[0] == "percentage_damage")
            hp, b, h = max(mismatches, key=lambda row: abs(row[1] - row[2]))
            print(f"| {hp} | {b:.0f} | {h:.0f} | `{w}` |")
    else:
        print("\n## ✅ percentage damage preserved on every weapon")

    for kind in OPERATING_BEHAVIOR + ("blast_shape",):
        ws = by_kind.get(kind)
        if not ws:
            continue
        marker = "⚠" if kind == "blast_shape" else "⛔ FAIL —"
        print(f"\n### {marker} {kind} changed on {len(ws)} weapon(s)")
        for w in ws[:10]:
            d = next(x for x in changed[w] if x[0] == kind)
            if kind in (
                    "top_level", "projectile", "non_damage_warheads",
                    "armor_profile"):
                print(f"- `{w}`: resolved {kind.replace('_', ' ')} changed")
            else:
                print(f"- `{w}`: {d[1]!r} → {d[2]!r}")
        if len(ws) > 10:
            print(f"- … {len(ws) - 10} more")

    if a.json:
        pathlib.Path(a.json).write_text(
            json.dumps({
                "meta": {
                    "base_snapshot_sha256": snapshot_digest(base),
                    "head_snapshot_sha256": snapshot_digest(head),
                    "health_values": health_values,
                    "with_concrete": a.with_concrete,
                },
                "changed": changed,
                "removed": gone,
                "added": added,
            }, indent=1),
            encoding="utf-8")
        print(f"\n_wrote {a.json}_")

    operating_changes = any(by_kind.get(kind) for kind in OPERATING_BEHAVIOR)
    return 1 if dmg or pct or operating_changes else 0


if __name__ == "__main__":
    sys.exit(main())
