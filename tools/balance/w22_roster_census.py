#!/usr/bin/env python3
"""w22_roster_census.py — W22 roster census: liveness classifier + per-credit weighting.

`target_model._scan` counts EVERY concrete armored actor in the resolved tree —
including bodies no faction can field (unbuildable stubs, bot-gated variants,
spawn-only summons, unreachable prereqs). BALANCE_PROGRAM_PLAN W22 measured
**552 of 1,977 armored actors not buildable**, and pricing must not average
them in: `armor_weights()` feeds `weighted_versus` -> `K` -> every weapon price.

This tool produces the census the pricing inputs should use:

  liveness    in the union of every real faction's `buildable_roster`
              (fixpoint prerequisite closure — cameo_model.roster), else a
              reason: `bot_gated` (~botplayer/~hardbotplayer), `unbuildable`
              (no Buildable.Queue), `lobby_gated` (Queue set and reachable
              once a lobby option's tokens are granted — naval checkbox,
              base-reveal, derricklimit, …), `parked` (`~disabled`
              convention — see docs/balance/w22_known_parked.yaml),
              `unreachable` (Buildable but prereqs never satisfiable), or
              `spawn_only` (only produced by another actor or warhead).
  per-credit  inside the live set, body-count-per-credit share = count/cost —
              armies are bought by the credit, so a 2000 tank fields half as
              many bodies as a 1000 tank for equal spend.

Read-only: resolves the tree, writes docs/balance/w22_roster_census.{md,json}.
Never edits yaml, never touches --confirm.
"""

from __future__ import annotations

import collections
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
sys.path.insert(0, str(ROOT / "tools/balance"))

from cameo_model import Model          # noqa: E402
import target_model as tm              # noqa: E402  (ARMORS, ARMOR_MACRO, ENGAGEMENT)

OUT_MD = ROOT / "docs/balance/w22_roster_census.md"
OUT_JSON = ROOT / "docs/balance/w22_roster_census.json"

BOT_TOKENS = ("botplayer", "hardbotplayer", "easybotplayer", "mediumbotplayer")
# `~disabled` convention: the token is never provided, so these actors stay
# out of every roster on purpose. Maintainer ruling 2026-09-26: they are
# parked, not dead — the manifest is docs/balance/w22_known_parked.yaml.
DISABLE_TOKENS = {"disabled", "disable", "disabledactor"}
KNOWN_PARKED = ROOT / "docs/balance/w22_known_parked.yaml"
# Maintainer ruling 2026-09-26: wc2_neutral_daemon is a summon (spawn_only)
# even though no live producer node references it yet.
KNOWN_SPAWN_ONLY = {"wc2_neutral_daemon"}
# Trait roots whose subtrees PRODUCE an actor at runtime (airstrike UnitTypes,
# paratrooper loads, deploy-spawned turrets, crate grants, prisoner releases…).
# An actor referenced only here is field-visible but never queued.
import re as _re
PRODUCER_TRAIT = _re.compile(
    r"(spawn|produce|power|airstrike|paratroop|paradrop|drop|deploy|reinforce"
    r"|grant|crew|crate|squad|camera|prisoner|garrison|exit|harvest|capture"
    r"|chronoshift|demo|carry|transport|eject|evac|transform|undeploy|sell)",
    _re.IGNORECASE)


def _leaf_values(node) -> list[str]:
    out = [str(node.value)]
    for c in getattr(node, "children", []) or []:
        out.extend(_leaf_values(c))
    return out


def _cost(node) -> int | None:
    v = node.child("Valued")
    if v is None:
        return None
    raw = v.get("Cost")
    try:
        return int(float(str(raw))) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _spawned_names(node, all_names: set[str]) -> set[str]:
    """Armored actor ids this node can produce at runtime — any leaf value under a
    producer-ish trait equal to a known actor name (covers UnitTypes lists,
    comma-joined Actors fields, lone Actor/SpawnActor values, …)."""
    out: set[str] = set()
    for child in node.children:
        root = child.key.split("@", 1)[0]
        # *BotModule* traits (SquadManagerBotModuleCA, SupportPowerBotModule…)
        # are AI decision lists — build queues, not runtime producers.
        if "botmodule" in root.lower():
            continue
        if not PRODUCER_TRAIT.search(root):
            continue
        for leaf in _leaf_values(child):
            for tok in leaf.replace(",", " ").split():
                t = tok.strip().lower()
                if t in all_names:
                    out.add(t)
    return out


def _warhead_spawned_names(rs, all_names: set[str]) -> dict[str, set[str]]:
    """Actors spawned by `SpawnActor` WARHEADS (summons live behind weapons, not
    actor traits — e.g. wc2 skeleton/eye-of-kilrogg). Warhead nodes sit under
    weapon defs, so the actor-trait scan never sees them."""
    out: dict[str, set[str]] = collections.defaultdict(set)
    for wname, wnode in rs.weapons.items():
        if wname.startswith(("^", "$", "-")):
            continue
        res = rs.resolve_weapon(wname) if hasattr(rs, "resolve_weapon") else wnode
        if res is None:
            continue
        for child in res.children:
            if not child.key.startswith("Warhead"):
                continue
            if str(child.value).strip() != "SpawnActor":
                continue
            for tok in (child.get("Actors") or "").replace(",", " ").split():
                t = tok.strip().lower()
                if t in all_names:
                    out[t].add(wname.lower())
    return out


def main() -> int:
    m = Model()
    rs = m.rs
    tm.use_ruleset(rs)

    factions = [f.internal for f in m.real_factions()]
    live: set[str] = set()
    for fac in factions:
        live |= m.buildable_roster(fac)

    # Lobby-gated reachability: tokens granted only when a lobby option is
    # ticked (naval checkbox, base-reveal, derricklimit, tech level, …).
    lobby = frozenset(m.lobby_tokens())
    lobby_live: set[str] = set()
    for fac in factions:
        lobby_live |= m.buildable_roster(fac, lobby)

    # Armored concrete actors — same filter as target_model._scan.
    armored: dict[str, tuple[str, object]] = {}   # name -> (armor, resolved node)
    for name in rs.actors:
        if name.startswith(("^", "$", "-")) or "." in name:
            continue
        node = rs.resolve(name)
        if node is None:
            continue
        armor = None
        for child in node.children:
            if child.key == "Armor" or child.key.startswith("Armor@"):
                value = child.get("Type")
                if value and str(value).strip() in tm.ARMORS:
                    armor = str(value).strip()
                    break
        if armor is not None:
            armored[name.lower()] = (armor, node)

    # Spawn-only detection: names produced by any actor's spawn traits.
    producers: dict[str, set[str]] = collections.defaultdict(set)
    for name in rs.actors:
        if name.startswith(("^", "$", "-")) or "." in name:
            continue
        node = rs.resolve(name)
        if node is None:
            continue
        for spawned in _spawned_names(node, set(armored)):
            producers[spawned].add(name.lower())
    # Warhead-spawned producers (SpawnActor warheads behind weapons) — the
    # actor-trait scan above cannot see them.
    for spawned, by in _warhead_spawned_names(rs, set(armored)).items():
        producers[spawned] |= by
    # Maintainer-ruled summons with no wired producer yet.
    for n in KNOWN_SPAWN_ONLY:
        if n in armored:
            producers[n].add("(ruled spawn_only — no live producer)")

    reason_by: dict[str, str] = {}
    cost_by: dict[str, int | None] = {}
    factions_of: dict[str, list[str]] = {}
    for lname, (armor, node) in armored.items():
        cost_by[lname] = _cost(node)
        if lname in live:
            reason_by[lname] = "buildable"
            factions_of[lname] = sorted(
                f for f in factions if lname in m.buildable_roster(f))
            continue
        b = node.child("Buildable")
        prereqs = m.positive_prereqs(node)
        negated = [t for t in prereqs if any(btok in t for btok in BOT_TOKENS)]
        if b is None or not b.get("Queue"):
            reason_by[lname] = "spawn_only" if lname in producers else "unbuildable"
        elif negated:
            reason_by[lname] = "bot_gated"
        elif any(t in DISABLE_TOKENS for t in prereqs):
            # `~disabled` parks the actor — but a summon that is still produced
            # at runtime is spawn_only, not parked (maintainer ruling).
            reason_by[lname] = "spawn_only" if lname in producers else "parked"
        elif lname in lobby_live:
            reason_by[lname] = "lobby_gated"
        else:
            reason_by[lname] = "unreachable"
        if reason_by[lname] in ("unbuildable", "unreachable") and lname in producers:
            reason_by[lname] = "spawn_only"

    # ---- aggregate ------------------------------------------------------- #
    by_reason = collections.Counter(reason_by.values())
    census_all: collections.Counter[str] = collections.Counter()
    census_live: collections.Counter[str] = collections.Counter()
    credit_live: collections.Counter[str] = collections.Counter()  # bodies/credit
    for lname, (armor, _node) in armored.items():
        census_all[armor] += 1
        if reason_by[lname] == "buildable":
            census_live[armor] += 1
            c = cost_by[lname]
            if c and c > 0:
                credit_live[armor] += 1.0 / c          # bodies per unit cost
            else:
                credit_live[armor] += 1.0              # unpriced floor: count it

    def shares(counter) -> dict[str, float]:
        total = sum(counter.values())
        return {k: v / total for k, v in counter.items()} if total else {}

    share_all = shares(census_all)
    share_live = shares(census_live)
    share_credit = shares(credit_live)

    rows = []
    for armor in sorted(census_all, key=lambda a: -census_all[a]):
        rows.append({
            "armor": armor,
            "actors": census_all[armor],
            "live": census_live[armor],
            "dead": census_all[armor] - census_live[armor],
            "share_all": round(share_all.get(armor, 0) * 100, 3),
            "share_live": round(share_live.get(armor, 0) * 100, 3),
            "share_credit": round(share_credit.get(armor, 0) * 100, 3),
            "delta_all_vs_live": round(
                (share_live.get(armor, 0) - share_all.get(armor, 0)) * 100, 3),
        })

    payload = {
        "generated_by": "tools/balance/w22_roster_census.py",
        "factions": len(factions),
        "armored_actors": len(armored),
        "buildable": by_reason["buildable"],
        "not_buildable": len(armored) - by_reason["buildable"],
        "reasons": dict(by_reason),
        "per_armor": rows,
        "live_actors": sorted(n for n, r in reason_by.items() if r == "buildable"),
        "not_buildable_detail": {
            n: {"armor": armored[n][0], "reason": reason_by[n],
                "cost": cost_by[n],
                "produced_by": sorted(producers.get(n, ()))}
            for n, r in reason_by.items() if r != "buildable"
        },
    }

    # ---- report ----------------------------------------------------------- #
    out = [
        "# W22 roster census — liveness classifier + per-credit weighting",
        "",
        f"Generated by `tools/balance/w22_roster_census.py` — read-only, resolved tree.",
        "",
        f"Armored actors scanned: **{len(armored)}** — buildable (in some real faction's "
        f"roster): **{by_reason['buildable']}** — not buildable: "
        f"**{len(armored) - by_reason['buildable']}**",
        "",
        "Consumer note for `armor_weights()` / `weighted_versus`: `share_live` is the "
        "drop-in pricing census (queue-buildable only). `spawn_only` bodies are real "
        "match targets (airstrikes, MCV-deployed conyards, spawn children) but carry "
        "no queue cost — include them only if K should price non-queue threats. "
        "`unbuildable`/`unreachable`/`parked` must never enter the pricing roster; "
        "`lobby_gated` bodies are conditional content — they enter pricing only if "
        "the lobby option defaults them on.",
        "",
        "Plan-claim note: the W22 order quoted 552/1977 not-buildable/armored; this "
        "tree measures 996/2367 — the corpus grew with the ContentPack merge wave. "
        "The claim's substance holds: ~42% of armored defs must be excluded from pricing. "
        "2026-09-26 maintainer rulings added `lobby_gated` (lobby options are providers) "
        "and `parked` (the known `~disabled` set), retiring the last `unreachable` rows.",
        "",
        "## Liveness reasons (non-buildable)",
        "",
        "| reason | count | meaning |",
        "|---|--:|---|",
    ]
    meanings = {
        "bot_gated": "Buildable gated on a `~*botplayer*` token — bots only",
        "spawn_only": "produced by another actor or SpawnActor warhead, never queued",
        "lobby_gated": "reachable once a lobby option grants its token "
                       "(naval checkbox, base-reveal, derricklimit, …)",
        "parked": "`~disabled` convention — intentionally parked "
                  "(docs/balance/w22_known_parked.yaml)",
        "unreachable": "has Buildable.Queue but prereqs unsatisfiable by any faction",
        "unbuildable": "no Buildable at all — husk/prop/mission defs",
    }
    for reason, cnt in by_reason.most_common():
        if reason == "buildable":
            continue
        out.append(f"| `{reason}` | {cnt} | {meanings.get(reason, '')} |")

    out += [
        "",
        "## Per-armor shares — all actors vs live roster vs live/credit-weighted",
        "",
        "Within-macro prevalence is what `armor_weights()` consumes. `share_live` is the",
        "count-only live census; `share_credit` weights each live actor by bodies-per-credit",
        "(1/Cost — cheaper units field more bodies per equal spend; unpriced actors count 1).",
        "",
        "| armor | actors | live | dead | share_all % | share_live % | share_credit % | Δ live−all pp |",
        "|---|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for r in rows:
        out.append(
            f"| {r['armor']} | {r['actors']} | {r['live']} | {r['dead']} | "
            f"{r['share_all']} | {r['share_live']} | {r['share_credit']} | "
            f"{r['delta_all_vs_live']:+} |")

    dead_sorted = sorted(
        ((r["armor"], n) for n, r in payload["not_buildable_detail"].items()
         if r["reason"] not in ("parked",)),
        key=lambda t: t[1])
    out += ["", "## Largest dead-weight entries (first 30, alphabetical)", "",
            "(`parked` rows excluded — they are a maintainer-approved known set,",
            "listed under `parked` in the JSON detail and in",
            "`docs/balance/w22_known_parked.yaml`.)", "",
            "| actor | armor | reason | cost | produced by |", "|---|---|---|--:|---|"]
    for armor, n in dead_sorted[:30]:
        d = payload["not_buildable_detail"][n]
        out.append(f"| `{n}` | {d['armor']} | {d['reason']} | "
                   f"{d['cost'] or '—'} | {', '.join(d['produced_by'][:3]) or '—'} |")

    # Known-parked drift check: the `~disabled` set is maintainer-frozen; warn
    # when the census disagrees with the recorded manifest.
    parked_now = sorted(n for n, r in reason_by.items() if r == "parked")
    if KNOWN_PARKED.exists():
        known = [
            ln.split("#", 1)[0].strip().lstrip("-").strip()
            for ln in KNOWN_PARKED.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("-")
        ]
        known = [k.lower() for k in known if k]
        extra = [n for n in parked_now if n not in known]
        stale = [k for k in known if k not in parked_now
                 and reason_by.get(k) != "spawn_only"]
        if extra or stale:
            print(f"WARN known-parked drift — new: {extra} stale: {stale}")
        payload["parked_manifest_ok"] = not (extra or stale)

    OUT_MD.write_text("\n".join(out) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")

    print(f"armored={len(armored)} live={by_reason['buildable']} "
          f"dead={len(armored) - by_reason['buildable']} reasons={dict(by_reason)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)} + {OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
