#!/usr/bin/env python3
"""sim_attack_tesla.py — a source-derived `AttackTesla` timing model.

Earlier work published 160, 172, 180 and 220 ticks for the Rail Tower. The first
three omitted or mis-modelled its repeated wind-up; 220 was the immediate-reacquisition
model while `InitialChargeDelay` was 12. The current deliberate value is 10, so that
same ideal model is now 210. This file transcribes the engine state machine and keeps
the ideal calculation separate from sampled AutoTarget timing.

THE MODEL, file by file:

  AttackTesla.cs      `ChargeAttack` queues `Wait(InitialChargeDelay)` then `ChargeFire`.
                      `ITick` refills `charges` when `timeToRecharge` expires, and
                      `INotifyAttack.Attacking` resets that to the trait's `ReloadDelay` on
                      every real shot — so the trait reload runs from the LAST shot.
  AttackBase.cs       `CanAttack` calls `HasAnyValidWeapons(target, reloadingIsInvalid: true)`,
                      whose loop sets `reloadingStateIsValid = !reloadingIsInvalid ||
                      !armament.IsReloading`. **A reloading armament therefore makes
                      `CanAttack` FALSE.**
  Armament.cs         `IsReloading` is `FireDelay > 0`; `Tick` decrements `FireDelay`.
  Activity.cs:126-133 "avoid a single tick delay if the childactivity was just queued" — a
                      freshly queued child ticks in the same tick, which is what makes
                      `Wait(N)` block its parent for exactly N ticks rather than N+1.

⭐ THE LOAD-BEARING LINE, and the one I got wrong twice:

    ChargeFire.Tick:  if (IsCanceling || !attack.CanAttack(self, target)) return true;

`ChargeFire` does **not** spin while the weapon reloads — it EXITS. `ChargeAttack` carries
the identical guard, so it exits too and the whole attack activity ends. The actor then
reacquires and comes back in through `ChargeAttack`, which pays `InitialChargeDelay` AGAIN.

That gives the mode detection the maintainer asked for, with no per-actor knowledge and no
trait-name special case — just `ChargeDelay` against the weapon's reload:

    weapon reload <= ChargeDelay   the volley is never interrupted.  CHARGE-ONCE:
                                   gap = ChargeDelay
    weapon reload >  ChargeDelay   ChargeFire exits after every shot. CHARGE-PER-SHOT:
                                   gap = weapon reload + InitialChargeDelay

    cycle = (MaxCharges - 1) * gap + trait ReloadDelay + InitialChargeDelay

With immediate reacquisition this reproduces the current priced values — 131, 95 and
210 — including
*"for the asian alliance railgun tower it needs to charge for every shot unlike the tesla
coil! So at 5 shots the initial charge delay is used 5 times!"*, which is precisely what
the guard produces.

⭐⭐ THE REACQUISITION INPUT IS NO LONGER UNRESOLVED — IT IS MEASURED, AND IT IS A RANGE.
`AutoTarget` is what restarts a charged actor whose activity ended, and its schedule is not
a mystery: `INotifyIdle.TickIdle` -> `ScanAndAttack` -> `ScanForTarget`, which does nothing
unless `nextScanTime <= 0` and then re-arms it with

    nextScanTime = self.World.SharedRandom.Next(MinimumScanTimeInterval, MaximumScanTimeInterval)

`AutoTargetInfo` declares 3 and 8, no Cameo yaml overrides either, and .NET's
`Random.Next(min, max)` excludes its upper bound — so the scan interval is uniform over
{3, 4, 5, 6, 7}: mean 5, never 8. Note the re-arm happens BEFORE `ChooseTarget`, so a scan
costs its interval whether or not it leads to a shot, and `ChooseTarget` does not care that
the weapon is reloading — it returns the target, `ChargeAttack` is queued, and `CanAttack`
kills it again. The actor therefore polls its own reload on a 3-7 tick lattice.

⭐ WHICH IS WHY THIS AFFECTS THE RAIL TOWER AND ONLY THE RAIL TOWER. A charge-once actor
never goes idle: after its last zap `ChargeFire` returns true, and `ChargeAttack` — reached
in the same tick — finds `charges == 0` with the weapon ready and returns FALSE, holding the
activity open through the whole trait reload. No idle tick, no scan, no latency. Only the
charge-per-shot mode ends its activity mid-volley, and only it pays.

So the Rail Tower has no single runtime period. `--autotarget` samples the distribution.
For 300 seeds it reports a 210 minimum, 218 mean and 232 maximum; those are sample
statistics, not mathematical bounds. A legal repeating scan path can produce 234, so
the sampled maximum must never be called a ceiling. The pricing pipeline deliberately
uses the 210 immediate-reacquisition floor and records the runtime spread separately.

⚠ A SECOND-ORDER EFFECT THIS MODEL DOES INCLUDE: `timeToRecharge` is reset by every shot,
so scan latency inside a volley pushes the last shot later and delays the refill with it.
The volley period therefore grows by the accumulated latency, not by a single interval.

⚠ `DoAttack` calls `CheckFire` on every armament and `Attacking` decrements charges once
per firing armament. The 131 and 95 baseline calculations therefore require exactly one
enabled armament. The RA2 coil's elite/no-overload conditions previously enabled two; the
playtest-readiness integration makes those conditions mutually exclusive and tests them.

The charge term is applied by `formula.charge_attack_cycle`: the priced baseline periods
are 131, 95 and 210. The AutoTarget sample is diagnostic and is not added to the price.

Usage:
    python tools/balance/sim_attack_tesla.py            # the three charged actors
    python tools/balance/sim_attack_tesla.py --check    # exit 1 on any disagreement
    python tools/balance/sim_attack_tesla.py --autotarget   # the real scan lattice
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys

# The three `AttackTesla` actors in the tree, every field resolved from the ruleset.
# `ChargeDelay` is written by NONE of them — 3 is AttackTeslaInfo's own default, so the
# comparison that decides the mode is invisible in the yaml.
#   name: (MaxCharges, trait ReloadDelay, InitialChargeDelay, ChargeDelay, weapon ReloadDelay)
ACTORS = {
    "ra1_soviets_teslacoil":   (3, 100, 25, 3, 3),
    "ra2_soviets_teslacoil":   (1, 75, 20, 3, 3),
    "asianalliance_railtower": (5, 120, 10, 3, 10),
}

# Every period ever claimed for these actors, kept beside the simulation that adjudicates
# them so the verdict cannot drift away from the claim in some other document.
RULINGS = {
    "ra1_soviets_teslacoil": 131,
    "ra2_soviets_teslacoil": 95,
    "asianalliance_railtower": 210,
}
CLAIMED = {
    "ra1_soviets_teslacoil":   {"maintainer 2026-09-14": 131},
    "ra2_soviets_teslacoil":   {"maintainer 2026-09-14": 95},
    "asianalliance_railtower": {"maintainer ruling / immediate model": 210, "#385": 160,
                                "my spin trace (withdrawn)": 172,
                                "my quantised trace (withdrawn)": 180},
}


def charge_mode(charge_delay: int, weapon_reload: int) -> str:
    """CHARGE-ONCE or CHARGE-PER-SHOT, decided by the engine's own reloading guard."""
    return "once" if weapon_reload <= charge_delay else "per-shot"


def formula(max_charges, trait_reload, initial_charge, charge_delay, weapon_reload) -> int:
    """The immediate-reacquisition closed form."""
    gap = (charge_delay if charge_mode(charge_delay, weapon_reload) == "once"
           else weapon_reload + initial_charge)
    return (max_charges - 1) * gap + trait_reload + initial_charge


def simulate(max_charges, trait_reload, initial_charge, charge_delay, weapon_reload,
             reacquire: int = 0, ticks: int = 6000) -> list[int]:
    """Tick indices of every shot, running the trait's state machine as transcribed above."""
    charges, time_to_recharge, fire_delay = max_charges, 0, 0
    state, wait, shots = "ChargeAttack", 0, []

    for t in range(ticks):
        can_attack = fire_delay == 0          # HasAnyValidWeapons(reloadingIsInvalid: true)

        # An activity that finishes hands control to its parent in the SAME tick
        # (Activity.cs:117, `lastRun = TickChild(self) && (finishing || Tick(self))`), so
        # unwinding out of ChargeFire into ChargeAttack costs nothing. Hence a loop, not a
        # state that burns a tick - modelling the unwind as a tick was worth 4 ticks of
        # error on the Rail Tower and is exactly the kind of slip this file exists to catch.
        while wait == 0:
            if state == "ChargeFire":
                if not can_attack or charges == 0:
                    # ⛔ THE LINE THIS FILE EXISTS FOR. ChargeFire RETURNS TRUE here; it
                    # does not keep ticking through the weapon's reload.
                    state = "ChargeAttack"
                    continue
                fire_delay = weapon_reload
                charges -= 1
                time_to_recharge = trait_reload            # INotifyAttack.Attacking
                shots.append(t)
                wait = charge_delay                        # QueueChild(Wait(ChargeDelay))
                break
            # ChargeAttack, carrying the identical guard.
            if not can_attack:
                wait = reacquire                           # the whole activity ends
                break
            if charges == 0:
                break                                      # returns false: spins in place
            wait, state = initial_charge, "ChargeFire"
            break

        if wait > 0:
            wait -= 1
        if fire_delay > 0:
            fire_delay -= 1
        time_to_recharge -= 1
        if time_to_recharge <= 0:
            charges = max_charges

    return shots


# `AutoTargetInfo.MinimumScanTimeInterval` / `MaximumScanTimeInterval`, neither overridden by
# any Cameo yaml. `Random.Next(min, max)` excludes max, so the draw is U{3..7}.
SCAN_MIN, SCAN_MAX = 3, 8


def simulate_autotarget(max_charges, trait_reload, initial_charge, charge_delay, weapon_reload,
                        seed: int = 0, scan_min: int = SCAN_MIN, scan_max: int = SCAN_MAX,
                        queue_latency: int = 1, ticks: int = 40000) -> list[int]:
    """Shot ticks, with AutoTarget restarting the activity instead of a free reacquisition.

    The difference from `simulate` is one state: when `ChargeAttack` exits because the
    armament is reloading, the actor becomes IDLE rather than instantly re-entering. It
    leaves idle only on a scan tick, and scans are a renewal process on U{scan_min..scan_max-1}.

    `queue_latency` is the tick between `Attack()` queueing the activity and the activity
    first ticking. It is 1 here; it moves every charge-per-shot gap by exactly that amount
    and is reported rather than hidden, because nothing in the source pins it harder.
    """
    rng = random.Random(seed)
    charges, time_to_recharge, fire_delay = max_charges, 0, 0
    state, wait, next_scan, shots = "ChargeAttack", 0, 0, []

    for t in range(ticks):
        can_attack = fire_delay == 0          # HasAnyValidWeapons(reloadingIsInvalid: true)

        while wait == 0:
            if state == "idle":
                # AutoTarget.INotifyIdle.TickIdle -> ScanAndAttack -> ScanForTarget.
                if next_scan > 0:
                    break
                # Re-armed BEFORE ChooseTarget, so a fruitless scan still costs its interval.
                next_scan = rng.randrange(scan_min, scan_max)
                state, wait = "ChargeAttack", queue_latency
                break
            if state == "ChargeFire":
                if not can_attack or charges == 0:
                    state = "ChargeAttack"                 # returns true, unwinds same tick
                    continue
                fire_delay = weapon_reload
                charges -= 1
                time_to_recharge = trait_reload
                shots.append(t)
                wait = charge_delay
                break
            # ChargeAttack
            if not can_attack:
                state = "idle"                             # the whole activity ENDS
                break
            if charges == 0:
                break                                      # returns false: holds, no idle
            wait, state = initial_charge, "ChargeFire"
            break

        if wait > 0:
            wait -= 1
        if fire_delay > 0:
            fire_delay -= 1
        if next_scan > 0:
            next_scan -= 1                                 # AutoTarget.ITick.Tick
        time_to_recharge -= 1
        if time_to_recharge <= 0:
            charges = max_charges

    return shots


def periods_autotarget(spec, seeds: int = 200, **kw) -> list[int]:
    """Volley periods across many RNG seeds - the Rail Tower has a distribution, not a value."""
    out = []
    for seed in range(seeds):
        shots = simulate_autotarget(*spec, seed=seed, **kw)
        if len(shots) < 2 * spec[0]:
            continue
        gaps = [b - a for a, b in zip(shots, shots[1:])]
        cut = max(gaps)
        firsts = [shots[0]] + [b for a, b in zip(shots, shots[1:]) if b - a == cut]
        out.extend(b - a for a, b in zip(firsts, firsts[1:]))
    return out


def analyse(name, spec, reacquire: int = 0):
    """(period, closed form, inter-shot gaps, shots per volley) for one actor."""
    shots = simulate(*spec, reacquire=reacquire)
    closed = formula(*spec) if reacquire == 0 else None
    if len(shots) < 2:
        return None, closed, [], len(shots)
    gaps = [b - a for a, b in zip(shots, shots[1:])]
    volley_gap = max(gaps)
    firsts = [shots[0]] + [b for a, b in zip(shots, shots[1:]) if b - a == volley_gap]
    periods = sorted({b - a for a, b in zip(firsts, firsts[1:])})
    inner = sorted({g for g in gaps if g != volley_gap})
    per_volley = spec[0] if len(periods) == 1 else None
    return (periods[0] if len(periods) == 1 else periods), closed, inner, per_volley


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if simulation, closed form and ruling disagree")
    ap.add_argument("--reacquire", type=int, default=0,
                    help="ticks to reacquire after the attack activity ends (default 0)")
    ap.add_argument("--autotarget", action="store_true",
                    help="model AutoTarget's U{3..7} scan lattice instead of free reacquisition")
    ap.add_argument("--seeds", type=int, default=200,
                    help="RNG seeds for --autotarget (default 200)")
    args = ap.parse_args()

    if args.autotarget:
        print(f"AutoTarget scan interval: Random.Next({SCAN_MIN}, {SCAN_MAX}) -> "
              f"U{{{SCAN_MIN}..{SCAN_MAX - 1}}}, mean "
              f"{statistics.mean(range(SCAN_MIN, SCAN_MAX)):.1f} ticks")
        print(f"{'actor':<26} {'mode':<9} {'immediate':>9} {'min':>5} {'mean':>7} "
              f"{'max':>5}   ruling")
        print("-" * 92)
        for name, spec in ACTORS.items():
            ps = periods_autotarget(spec, seeds=args.seeds)
            mode = charge_mode(spec[3], spec[4])
            ruled = RULINGS[name]
            note = "unchanged - never goes idle" if mode == "once" else "a DISTRIBUTION"
            print(f"{name:<26} {mode:<9} {formula(*spec):>9} {min(ps):>5} "
                  f"{statistics.mean(ps):>7.1f} {max(ps):>5}   {ruled}  {note}")
        print("-" * 92)
        print("The priced 210 is the FLOOR of the Rail Tower's range, not its runtime cadence.")
        print("The floor is what is priced; the AutoTarget spread above it is not. See DESIGN.md.")
        return 0

    bad = 0
    print(f"{'actor':<26} {'mode':<9} {'gap':>5} {'SIMULATED':>10} {'formula':>8}   claims")
    print("-" * 104)
    for name, spec in ACTORS.items():
        period, closed, inner, _ = analyse(name, spec, args.reacquire)
        mode = charge_mode(spec[3], spec[4])
        agree = closed is None or period == closed
        bad += not agree
        gap = inner[0] if len(inner) == 1 else (inner or "-")
        claims = "  ".join(f"{who} {val}" + ("  <== MATCHES" if val == period else "")
                           for who, val in CLAIMED[name].items())
        print(f"{name:<26} {mode:<9} {str(gap):>5} {str(period):>10} {str(closed or '-'):>8}"
              f"{'' if agree else '  DISAGREE'}   {claims}")
    print("-" * 104)
    print("APPLIED: formula.charge_attack_cycle now counts the wind-up. These are its inputs.")

    if args.check:
        for name, spec in ACTORS.items():
            period, _, _, _ = analyse(name, spec, args.reacquire)
            ruled = RULINGS[name]
            if args.reacquire == 0 and period != ruled:
                print(f"FAIL: {name} simulates {period}, the ruling says {ruled}",
                      file=sys.stderr)
                bad += 1
        if bad:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
