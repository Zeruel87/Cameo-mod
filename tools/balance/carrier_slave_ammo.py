#!/usr/bin/env python3
"""carrier_slave_ammo.py — the ammo-pool sizing law for carrier slaves (DESIGN §11b.0 R8).

MAINTAINER RULING R8, quoted because the arithmetic is theirs:

  "ammo pool should be made so that firing all weapons on the target in a single burst attack
   will empty the ammo completely. For example the carrier slave has a machinegun that fires a
   burst of 10 then the carrier slave should also have ammo of 10 and deplete with one attack
   round completely and reloading from empty to full should always take 100 ticks so in this
   case reloading 1 ammo every 10 ticks. If the unit has more than one weapons you need to make
   the ammo pool and the ammo consumption per weapon so that both consume the ammo pool equally
   fast. For example if the previous slave now has an additional dual rocket they would consume
   each 5 ammo per shot so both the machine gun and the rockets would use the 10 ammo so the
   ammo pool would need to be at 20 and the ammo reload would be 1 ammo per 5 ticks instead so
   at 100 ticks it's full again"

THE LAW, and it reproduces both of those worked examples exactly (see `_self_test`). The law
sizes the pool and reload rate; it does not by itself stop an empty pool from firing. The
generated actor contract also carries `AmmoCondition`, `AttackAircraft.RequiresCondition`, and
per-armament minimum-ammo pause gates (`ammo < AmmoUsage`). The carrier engine refills the pool when the slave re-enters its carrier;
`ReloadAmmoPool` is the explicit deployed/in-flight recovery policy.

    share    = lcm(Burst_i) over the SCORING armaments
    usage_i  = share / Burst_i          -- so every armament spends `share` per full burst
    Ammo     = N x share                -- N = the largest mutually-engageable group
    Count    = Ammo / gcd(Ammo, 100)    -- empty to full in exactly 100 ticks
    Delay    = 100  / gcd(Ammo, 100)

`Count`/`Delay` is reduced by the gcd rather than written as `Delay = 100/Ammo`, because that
division is only exact when Ammo divides 100. Ammo 16 needs `Count 4 / Delay 25`, not a
truncated delay of 6 that would refill in 96 ticks.

WHICH ARMAMENTS SCORE. Three cases, and only the first is in the ruling as written:

  * UNCONDITIONAL -> scores.
  * ADDITIVE UPGRADE (`RequiresCondition: X` with no sibling requiring `!X`) -> `AmmoUsage: 0`,
    per the ruling: "if they get an extra weapon from an upgrade then that new weapon needs to
    have ammo usage of 0 so that it will not interfere with the ammo system".
  * REPLACEMENT PAIR (`X` and `!X` on siblings) -> ONE slot, not two. Both sides get the SAME
    usage and the slot is counted ONCE. ⚠ Treating the `X` side as an additive upgrade and
    zeroing it — which the ruling's wording invites — would leave `japan_zerofighter_slave`
    consuming NO ammo at all once its waveforce upgrade is bought, because both of its live
    armaments are on the `X` side.

N IS NOT SIMPLY THE ARMAMENT COUNT. `A10Carrier` carries `Armament@AA` (`ValidTargets: Air`)
and `Armament@BOMBS` (`Ground, Water`); they can never fire at the same target, so counting
them as concurrent would inflate the pool and the unit could never empty it in one attack.
N is therefore the size of the largest group of scoring armaments that share a target class.
An AA-only engagement then drains only the AA share, which is correct — nothing else fired.

⚠ SUICIDE SLAVES ARE OUT OF SCOPE and the maintainer's two names are not the whole set. They
named `tkmsuicidedrone` and `farasha_drone_ixian`, whose self-destruct is in the WEAPON (its
name is the actor's own, or `*Explosion`) and shows up in no trait. Three more qualify under
the same rule via `SpawnedExplodes` or a self-destruct weapon: `SCSCOURGEDRONE`, `kami.asian`,
`tsprobe`. A reload trait on a unit that dies when it attacks is dead weight, so all five are
skipped and named in the report. Scope is **14 actors, not the 17** that 19-minus-2 implied.
"""
from __future__ import annotations

import math

# Named by the maintainer. Their self-destruct lives in the weapon, not in any trait, so no
# detector finds them -- keep the explicit list alongside the detector.
NAMED_SUICIDE = ("tkmsuicidedrone", "farasha_drone_ixian")
SUICIDE_TRAITS = ("SpawnedExplodes", "Explodes")
RELOAD_TICKS = 100          # empty -> full, always, per the ruling
DEFAULT_POOL_ARMAMENTS = ("primary", "secondary")


def minimum_ammo_pause(condition: str, usage: int) -> str:
    """Pause an armament until its whole AmmoUsage can be paid."""
    usage = max(int(usage or 1), 1)
    return f"!{condition}" if usage == 1 else f"{condition} < {usage}"


def pause_gate_sufficient(condition: str, usage: int, pause: str | None,
                          requires: str | None, *, global_gate: bool = False) -> bool:
    """Whether a resolved armament gate prevents undercharged shots."""
    usage = max(int(usage or 1), 1)
    if usage == 1 and global_gate:
        return True
    expected = minimum_ammo_pause(condition, usage)
    if pause == expected or _generated_or_term(pause, expected):
        return True
    if usage == 1 and condition in {x.strip() for x in (requires or "").split(",")}:
        return True
    return False


def _split_top_level_or(expression: str) -> list[str]:
    parts, start, depth, i = [], 0, 0, 0
    while i < len(expression):
        char = expression[i]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "|" and i + 1 < len(expression) and expression[i + 1] == "|" and depth == 0:
            parts.append(expression[start:i])
            i += 1
            start = i + 1
        i += 1
    parts.append(expression[start:])
    return parts


def _strip_balanced_outer_parentheses(expression: str) -> str:
    expression = expression.strip()
    while expression.startswith("(") and expression.endswith(")"):
        depth = 0
        closes_at = None
        for i, char in enumerate(expression):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    closes_at = i
                    break
        if closes_at != len(expression) - 1:
            break
        expression = expression[1:-1].strip()
    return expression


def _generated_or_term(expression: str | None, expected: str) -> bool:
    """Accept only an exact term or our top-level OR wrapper, never a substring."""
    if not expression:
        return False
    for part in _split_top_level_or(expression):
        if _strip_balanced_outer_parentheses(part) == expected:
            return True
    return False


def preserved_pause(existing: str | None, condition: str, usage: int) -> str:
    """Combine a required ammo threshold with an authored pause expression."""
    expected = minimum_ammo_pause(condition, usage)
    if not existing or existing == expected:
        return expected
    if _generated_or_term(existing, expected):
        return existing
    return f"({existing}) || ({expected})"


def lcm_all(values) -> int:
    out = 1
    for v in values:
        out = out * max(int(v), 1) // math.gcd(out, max(int(v), 1))
    return out


def reload_rate(ammo: int, ticks: int = RELOAD_TICKS) -> tuple[int, int]:
    """(Count, Delay) refilling `ammo` in exactly `ticks`. Reduced, never truncated."""
    g = math.gcd(max(ammo, 1), ticks)
    return max(ammo, 1) // g, ticks // g


def is_suicide(actor_name: str, trait_stems, armament_weapons) -> str | None:
    """Why this slave is out of scope, or None."""
    if actor_name.lower() in {n.lower() for n in NAMED_SUICIDE}:
        return "named by the maintainer"
    for t in SUICIDE_TRAITS:
        if t in trait_stems:
            return f"trait {t}"
    for w in armament_weapons:
        if w and (w.lower() == actor_name.lower() or "explosion" in w.lower()):
            return f"self-destruct weapon {w}"
    return None


def negation_of(cond: str | None) -> str | None:
    if not cond:
        return None
    c = cond.strip()
    return c[1:].strip() if c.startswith("!") else "!" + c


def classify(arms: list[dict]) -> None:
    """Tag each armament with `role` in {score, mirror, additive} and its `slot`.

    `arms` entries need `key`, `burst`, `cond`, `targets`. Mutated in place.
    """
    conds = {a["cond"] for a in arms if a["cond"]}
    for a in arms:
        c = a["cond"]
        if not c:
            a["role"], a["slot"] = "score", a["key"]
            continue
        if negation_of(c) in conds:
            # replacement pair: the two branches are the same slot. The branch whose
            # condition is NEGATED is the default-on one, so it carries the slot identity
            # and the other mirrors it.
            a["role"] = "score" if c.startswith("!") else "mirror"
            a["slot"] = None       # paired up by the caller, which knows the ordering
        else:
            a["role"], a["slot"] = "additive", a["key"]


def pair_mirrors(arms: list[dict]) -> None:
    """Give every `mirror` the slot of the `score` armament it replaces.

    Pairing is positional within a condition group: the Nth `!X` armament is replaced by the
    Nth `X` armament. That is how these actors are authored (PRIMARY/SECONDARY mirrored by
    Upgrade/UpgradeSECONDARY) and it is asserted, not assumed -- an unpaired mirror raises.
    """
    scored = [a for a in arms if a["role"] == "score" and a["cond"]]
    mirrors = [a for a in arms if a["role"] == "mirror"]
    if len(mirrors) > len(scored):
        raise ValueError(f"{len(mirrors)} mirrors but only {len(scored)} negated slots")
    for m, s in zip(mirrors, scored):
        m["slot"] = s["key"]
        m["burst_of_slot"] = s["burst"]


def target_set(targets: str | None) -> set[str]:
    raw = targets or "Ground, Water"
    return {t.strip().lower() for t in raw.split(",") if t.strip()}


def largest_engageable_group(scoring: list[dict]) -> int:
    """|largest set of scoring armaments sharing at least one target class|."""
    if not scoring:
        return 0
    classes: set[str] = set()
    for a in scoring:
        classes |= target_set(a.get("targets"))
    best = 1
    for cls in classes:
        n = sum(1 for a in scoring if cls in target_set(a.get("targets")))
        best = max(best, n)
    return best


def plan(arms: list[dict]) -> dict:
    """The full ammo plan for one slave. `arms` as for `classify`."""
    classify(arms)
    pair_mirrors(arms)
    scoring = [a for a in arms if a["role"] == "score"]
    if not scoring:
        return {"ammo": 0, "count": 0, "delay": 0, "share": 0, "n": 0, "usage": {}}

    share = lcm_all(a["burst"] for a in scoring)
    usage = {a["key"]: share // max(a["burst"], 1) for a in scoring}
    for a in arms:
        if a["role"] == "mirror":
            usage[a["key"]] = share // max(a["burst"], 1)
        elif a["role"] == "additive":
            usage[a["key"]] = 0

    n = largest_engageable_group(scoring)
    ammo = n * share
    count, delay = reload_rate(ammo)
    return {"ammo": ammo, "count": count, "delay": delay, "share": share, "n": n,
            "usage": usage,
            "roles": {a["key"]: a["role"] for a in arms}}


def pool_armaments(arms) -> list[str] | None:
    """The `Armaments` list the pool needs, or None when the default already covers it.

    `AmmoPoolInfo.Armaments` defaults to ("primary", "secondary") and consumption is gated on
    it — `AmmoPool.Attacking` only calls `TakeAmmo` when `Info.Armaments.Contains(a.Info.Name)`.
    An armament named anything else therefore spends NO ammo, silently.
    """
    names = sorted({a.get("name") or "primary" for a in arms})
    if set(names) <= set(DEFAULT_POOL_ARMAMENTS):
        return None
    return names


def _self_test() -> int:
    # the ruling's first example: one machinegun, Burst 10
    p = plan([{"key": "Armament", "burst": 10, "cond": None, "targets": "Ground, Water"}])
    assert (p["ammo"], p["count"], p["delay"]) == (10, 1, 10), p
    assert p["usage"]["Armament"] == 1

    # the ruling's second example: the same machinegun plus a dual rocket (Burst 2)
    p = plan([{"key": "MG", "burst": 10, "cond": None, "targets": "Ground, Water"},
              {"key": "Rockets", "burst": 2, "cond": None, "targets": "Ground, Water"}])
    assert (p["ammo"], p["count"], p["delay"]) == (20, 1, 5), p
    assert p["usage"] == {"MG": 1, "Rockets": 5}, p["usage"]
    # and the stated invariant: one full burst from everything empties the pool exactly
    assert 10 * 1 + 2 * 5 == p["ammo"]

    # Ammo that does not divide 100 must still refill in exactly 100 ticks
    assert reload_rate(16) == (4, 25) and 16 / 4 * 25 == 100
    assert reload_rate(30) == (3, 10) and 30 / 3 * 10 == 100

    # target-exclusive armaments are not concurrent: AA cannot fire with the bombs
    p = plan([{"key": "GUNS", "burst": 1, "cond": None, "targets": "Ground, Water, Air"},
              {"key": "BOMBS", "burst": 1, "cond": None, "targets": "Ground, Water"},
              {"key": "AA", "burst": 1, "cond": None, "targets": "Air"}])
    assert p["n"] == 2, f"ground group is GUNS+BOMBS, so N=2, got {p['n']}"

    # a replacement pair is ONE slot and BOTH sides spend ammo
    p = plan([{"key": "A", "burst": 12, "cond": "!up", "targets": "Ground"},
              {"key": "B", "burst": 12, "cond": "!up", "targets": "Ground"},
              {"key": "UpA", "burst": 12, "cond": "up", "targets": "Ground"},
              {"key": "UpB", "burst": 12, "cond": "up", "targets": "Ground"},
              {"key": "Bomb", "burst": 1, "cond": None, "targets": "Ground"}])
    assert p["n"] == 3, f"A + B + Bomb, not 5; got {p['n']}"
    assert p["usage"]["UpA"] == p["usage"]["A"] == 1, p["usage"]
    assert p["usage"]["Bomb"] == 12, p["usage"]
    assert p["ammo"] == 36 and 12 * 1 + 12 * 1 + 1 * 12 == 36

    # an ADDITIVE upgrade is zeroed and does not enlarge the pool
    p = plan([{"key": "Main", "burst": 2, "cond": None, "targets": "Ground"},
              {"key": "Extra", "burst": 1, "cond": "bought", "targets": "Ground"}])
    assert p["usage"]["Extra"] == 0 and p["ammo"] == 2, p

    assert pool_armaments([{"name": "primary"}, {"name": "secondary"}]) is None
    assert pool_armaments([{"name": "tertiary"}]) == ["tertiary"]

    # Runtime-gate regressions: a global one-token gate is not enough for a ten-token shot,
    # and an authored pause expression is preserved when the minimum-ammo threshold is added.
    assert not pause_gate_sufficient("ammo", 10, None, None, global_gate=True)
    assert pause_gate_sufficient("ammo", 10, "ammo < 10", None)
    assert minimum_ammo_pause("ammo", 10) == "ammo < 10"
    assert preserved_pause("reload_lock", "ammo", 10) == "(reload_lock) || (ammo < 10)"
    assert pause_gate_sufficient("ammo", 10, "(reload_lock) || (ammo < 10)", None)
    assert not pause_gate_sufficient("ammo", 10, "lock && (ammo < 10)", None)
    assert not pause_gate_sufficient("ammo", 10, "!(ammo < 10)", None)
    assert not pause_gate_sufficient("ammo", 10, "lock && (other || (ammo < 10) || third)", None)
    assert not pause_gate_sufficient("ammo", 1, "!ammo_other", None)
    assert preserved_pause("lock && (ammo < 10)", "ammo", 10) == "(lock && (ammo < 10)) || (ammo < 10)"
    print("carrier_slave_ammo self-test: PASS (both of the ruling's worked examples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
