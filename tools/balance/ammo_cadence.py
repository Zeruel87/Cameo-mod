#!/usr/bin/env python3
"""The FOUR cadence regimes. An ammo pool makes `ReloadDelay` the wrong clock.

    MAINTAINER, 2026-09-12, three rulings in one session:
      "there are units that work with an ammo pool. For example the SSM launcher reload delay
       in cameo doesn't matter since it requires ammo to shoot which regenerates on the actor
       itself! Also our helicopters have a reloading ammo pool and combined with their ammo
       pool and ammo consumption per shot it means they are designed to shoot for 5 seconds at
       full speed and then after that at half speed"
      "For helicopters what we compare is only that time they shoot at full speed ... we take
       into account how much damage they can deal from full to empty ammo pool and in what time
       and calculate that as the DPS."
      "For planes that need to reload on the airfield we also compare the maximum damage they
       can deal from their ammo pool before it's empty but reload delay means nothing there so
       we only compare the maximum damage per sortie."

WHY THIS MODULE EXISTS. The ledger computes one number for every armed actor —
`damage x burst / (reload + burst delays)` — and NOTHING in `extract_stats`,
`reference_distribution` or `formula` mentions `AmmoPool`. Measured: **145 Cameo actors have
one**. For all 145 the weapon's `ReloadDelay` is
not the clock, so the ledger's DPS is measuring something the unit cannot sustain — and a
pipeline-written reload change would move the ledger's number while changing nothing in game.

`td_nod_ssmlauncher` is the proof, and it is exact:

    weapon honestjohn   ReloadDelay 225 + BurstDelays 25   -> cycle 250 ticks, burst 2
    AmmoPool            Ammo 2
    ReloadAmmoPool      Delay 125, Count 1                 -> 2 rounds per 250 ticks

Weapon rate and ammo rate are IDENTICAL (2 shots / 250 ticks). The reload is decorative: ammo
gates the launcher either way, which is exactly what the maintainer said.

THE FOUR REGIMES:

  1. NO POOL          dps = damage x burst / cycle              (today's formula, correct)
  2. SELF-RELOADING   dps = pool damage / time to empty
     (`ReloadAmmoPool`)  a RATE. The pool bounds the DURATION of full-rate fire, not the rate
                         within it, so the trailing reload never happens and is excluded.
  3. AIRFIELD REARM   sortie_damage = pool damage, and NO dps at all
     (`Rearmable`)       a TOTAL. Comparing a rate would be a category error: the plane empties
                         its pool, flies home and is out of the fight. Ruled explicitly.
  4. FINITE, UNCLASSIFIED   a pool with neither self-reload nor `Rearmable` -- no replenishment
     (neither trait)    mechanism this module knows. Reported, never scored. It is where the
                        spell-charge pools land (`wc2_humans_mage`, `Ammo: 255`).
  ⚠ SINGLE-SHOT POOLS, orthogonal to the four: a pool affording ONE shot delivers its damage
    instantly, so no elapsed time exists to divide by and no rate does either. Flagged
    `single_shot` with `dps: None`; the regime label is KEPT, because an airfield plane carrying
    one bomb is still an airfield plane.

ENGINE FACTS, read from source rather than assumed (OpenRA checkout, not guessed):
  * `AmmoPoolInfo.Ammo` (default 1) is the magazine; `ReloadCount` 1 and `ReloadDelay` 50 are
    the AIRFIELD rearm, NOT self-reload -- `AmmoPool.cs` sets `RemainingTicks` from it only in
    the rearm path.
  * Self-reload is a SEPARATE trait, `ReloadAmmoPool` -- `Delay` (default 50) and `Count`
    (default 1). Its ABSENCE does not imply an airfield plane -- see the gate note below.
  * `Armament.AmmoUsage` (default 1) is consumed per `Attacking` notification, i.e. per SHOT,
    not per burst (`AmmoPool.cs` `INotifyAttack.Attacking` -> `TakeAmmo(self, a.Info.AmmoUsage)`).
  * `WeaponInfo.BurstDelays` defaults to `[5]`, NOT 0 -- so an undeclared burst delay still
    lengthens the cycle. A single entry applies between every pair of shots; otherwise the list
    must be `Burst - 1` long (`Armament.cs` throws otherwise).

⚠ `time_to_empty` DROPS THE TRAILING RELOAD, and includes any reload ticks that occur before
the magazine empties. A pool holding exactly one burst never waits at all: the SSM launcher
fires 2 rounds 25 ticks apart and is empty, so its per-sortie rate is `2 x damage / 25`, not
`2 x damage / 250` -- a 10x difference on one unit. Including the trailing reload would measure
a cycle the unit never completes.
"""
from __future__ import annotations

NO_POOL = "no_pool"
SELF_RELOADING = "self_reloading"
AIRFIELD_REARM = "airfield_rearm"
FINITE_UNCLASSIFIED = "finite_unclassified"

# ⛔ REGIME 3 IS GATED ON `Rearmable`, NOT ON THE ABSENCE OF SELF-RELOAD. The first cut used
# "has AmmoPool, has no ReloadAmmoPool" and that misclassified 44 actors, most of them not
# aircraft at all:
#   * `wc2_humans_mage`  Mobile, seven Armaments, `AmmoPool Ammo: 255` -> a SPELL CHARGE pool
#     with a sentinel size. Reporting 4,590,000 "sortie damage" for a mage is nonsense.
#   * `A10Carrier`       Aircraft + AttackAircraft + `Ammo: 16` but NO `Rearmable` -> a
#     one-pass strike craft that never returns to rearm.
#   * `atreides_ornithopter`  Aircraft + AttackAircraft + `Rearmable` (19 RearmActors) +
#     `AmmoPool@PRIMARY Ammo: 5` -> THIS is the plane the ruling is about.
# `Rearmable` is the trait that actually sends an actor to an airfield, so it is the gate. A
# pool with neither self-reload nor `Rearmable` replenishes by NO mechanism this module knows,
# and is reported as FINITE_UNCLASSIFIED rather than given a number.


def cycle_ticks(reload_delay: int, burst: int, burst_delays) -> int:
    """Ticks from the first shot of one burst to the first shot of the next.

    A single `BurstDelays` entry applies between every pair of shots; a list is `Burst - 1`
    long and is summed. `[5]` is the engine default, so an absent declaration is 5, not 0.
    """
    bd = list(burst_delays) if burst_delays else [5]
    if burst <= 1:
        return max(int(reload_delay), 1)
    within = sum(bd) if len(bd) > 1 else bd[0] * (burst - 1)
    return max(int(reload_delay) + int(within), 1)


def _burst_gaps(burst: int, burst_delays) -> list[int]:
    """Expand the engine's single-delay shorthand into per-shot gaps."""
    if burst <= 1:
        return []
    bd = list(burst_delays) if burst_delays else [5]
    if len(bd) == 1:
        return [int(bd[0])] * (burst - 1)
    if len(bd) != burst - 1:
        raise ValueError(f"BurstDelays has {len(bd)} entries for burst {burst}")
    return [int(x) for x in bd]


def elapsed_for_shots(shots: int, reload_delay: int, burst: int, burst_delays) -> int:
    """Elapsed firing ticks through the requested shot, without pool reloads."""
    if shots <= 1:
        return 0
    gaps = _burst_gaps(burst, burst_delays)
    completed, position = divmod(shots - 1, max(int(burst), 1))
    return completed * cycle_ticks(reload_delay, burst, burst_delays) + sum(gaps[:position])


def simulate_depletion(ammo: int, ammo_usage: int, burst: int, reload_delay: int,
                       burst_delays, reload_count: int, reload_delay_pool: int,
                       *, max_shots: int = 100000) -> dict:
    """Walk shots and self-reload events until the pool empties or sustains fire."""
    capacity = max(int(ammo), 0)
    usage = max(int(ammo_usage or 1), 1)
    burst = max(int(burst or 1), 1)
    refill = max(int(reload_count or 0), 0)
    pool_delay = max(int(reload_delay_pool or 50), 1)
    gaps = _burst_gaps(burst, burst_delays)
    current, now, next_reload = capacity, 0, None
    position, shots = 0, 0

    while shots < max_shots:
        if next_reload is not None and next_reload <= now:
            while next_reload is not None and next_reload <= now and current < capacity:
                current = min(capacity, current + refill)
                next_reload += pool_delay
                if current >= capacity:
                    current, next_reload = capacity, None

        if current < usage:
            if next_reload is None or refill <= 0:
                return dict(empty=False, sustained=False, shots=shots, elapsed=now,
                            final_ammo=current)
            if next_reload > now:
                last = elapsed_for_shots(shots, reload_delay, burst, burst_delays)
                return dict(empty=False, sustained=False, starved=True, shots=shots,
                            elapsed=last, starvation_elapsed=now,
                            final_ammo=current)
            now = next_reload
            continue

        current -= usage
        shots += 1
        if current == 0:
            return dict(empty=True, sustained=False, shots=shots, elapsed=now,
                        final_ammo=0)
        if current < capacity and next_reload is None:
            next_reload = now + pool_delay

        if position < burst - 1:
            now += gaps[position]
            position += 1
        else:
            now += max(int(reload_delay), 1)
            position = 0

    return dict(empty=False, sustained=False, simulation_limit=True, shots=shots,
                elapsed=now, final_ammo=current)


def regime(has_pool: bool, has_self_reload: bool, has_rearmable: bool = False) -> str:
    if not has_pool:
        return NO_POOL
    if has_self_reload:
        return SELF_RELOADING
    return AIRFIELD_REARM if has_rearmable else FINITE_UNCLASSIFIED


def cadence(damage_per_shot: float, burst: int, reload_delay: int, burst_delays,
            *, ammo: int | None = None, ammo_usage: int = 1,
            reload_count: int | None = None, reload_delay_pool: int | None = None,
            rearmable: bool = False) -> dict:
    """The comparable figure for one armament, under whichever regime applies.

    Returns `regime`, `cycle`, `dps` (None in regimes 3 and 4), `sortie_damage` (None in
    regime 1),
    `seconds_at_full_rate` and `sustain_factor` (the fraction of the weapon's own rate the pool
    can sustain indefinitely; 1.0 where nothing limits it, None where nothing sustains it).
    """
    burst = max(int(burst or 1), 1)
    cyc = cycle_ticks(reload_delay, burst, burst_delays)
    weapon_dps = damage_per_shot * burst / cyc
    kind = regime(ammo is not None, reload_count is not None, rearmable)
    out = {"regime": kind, "cycle": cyc, "dps": weapon_dps, "sortie_damage": None,
           "seconds_at_full_rate": None, "sustain_factor": 1.0}
    if kind == NO_POOL:
        return out

    if kind == SELF_RELOADING:
        sim = simulate_depletion(ammo, ammo_usage, burst, reload_delay, burst_delays,
                                 reload_count, reload_delay_pool)
        shots, elapsed = sim["shots"], sim["elapsed"]
        out["sustained"] = sim["sustained"]
        out["simulation_limit"] = sim.get("simulation_limit", False)
        out["starved"] = sim.get("starved", False)
    else:
        shots = max(int(ammo) // max(int(ammo_usage), 1), 1)
        elapsed = elapsed_for_shots(shots, reload_delay, burst, burst_delays)
    out["sustained"] = False
    pool_damage = shots * damage_per_shot
    out["sortie_damage"] = pool_damage
    out["shots"] = shots
    out["seconds_at_full_rate"] = elapsed / 25.0

    # ⛔ ONE SHOT HAS NO RATE. A pool affording a single shot delivers its damage instantly:
    # elapsed is 0 and a DPS would be infinite, so the comparable figure is the TOTAL, exactly
    # as the maintainer ruled for airfield planes. Reported, never divided.
    out["single_shot"] = elapsed <= 0 or shots < 2
    if out["single_shot"]:
        # The REGIME LABEL IS KEPT -- an airfield plane carrying one bomb is still an airfield
        # plane, and overwriting its regime threw that away. Only the rate is withheld.
        out["dps"] = None
        out["sustain_factor"] = None
        if out.get("starved"):
            out["cadence_status"] = "STARVED_AFTER_RELOAD"
            out["starvation_elapsed"] = sim.get("starvation_elapsed")
        return out
    time_to_empty = float(elapsed)

    if kind == SELF_RELOADING and out.get("starved"):
        out["dps"] = pool_damage / time_to_empty if time_to_empty else None
        ammo_rate = (reload_count / max(int(reload_delay_pool or 50), 1)) / max(int(ammo_usage), 1)
        weapon_rate = burst / cyc
        out["sustain_factor"] = min(1.0, ammo_rate / weapon_rate) if weapon_rate else None
        out["cadence_status"] = "STARVED_AFTER_RELOAD"
        out["starvation_elapsed"] = sim.get("starvation_elapsed")
        return out

    if kind == SELF_RELOADING and out["sustained"]:
        out["dps"] = weapon_dps
        out["sustain_factor"] = 1.0
        return out

    if kind == SELF_RELOADING and out.get("simulation_limit"):
        out["dps"] = None
        out["sustain_factor"] = None
        out["cadence_status"] = "WITHHELD_SIMULATION_LIMIT"
        return out

    if kind in (AIRFIELD_REARM, FINITE_UNCLASSIFIED):
        # Ruled: "reload delay means nothing there so we only compare the maximum damage per
        # sortie". A rate would be a category error, so there is deliberately no dps.
        out["dps"] = None
        out["sustain_factor"] = None
        return out

    out["dps"] = pool_damage / time_to_empty
    ammo_rate = (reload_count / max(int(reload_delay_pool or 50), 1)) / max(int(ammo_usage), 1)
    weapon_rate = burst / cyc
    out["sustain_factor"] = min(1.0, ammo_rate / weapon_rate) if weapon_rate else None
    return out


def _selftest() -> None:
    # cycle: a single BurstDelays entry applies between every pair of shots
    assert cycle_ticks(111, 6, [5]) == 111 + 25
    assert cycle_ticks(100, 4, [0, 4, 0]) == 104        # OpenRA MSAM, summed
    assert cycle_ticks(30, 1, None) == 30               # burst 1 -> no delay applies
    assert cycle_ticks(70, 2, None) == 75               # engine default [5], not 0

    # regime 1 is unchanged from the ledger's formula
    r = cadence(8000, 2, 72, [8])
    assert r["regime"] == NO_POOL and r["cycle"] == 80 and r["dps"] == 8000 * 2 / 80
    assert r["sortie_damage"] is None

    # regime 2, the SSM launcher: one burst empties the pool, so the reload never elapses
    r = cadence(1000, 2, 225, [25], ammo=2, ammo_usage=1, reload_count=1,
                reload_delay_pool=125)
    assert r["single_shot"] is False
    assert r["regime"] == SELF_RELOADING
    assert r["cycle"] == 250
    assert r["sortie_damage"] == 2000
    assert abs(r["seconds_at_full_rate"] - 1.0) < 1e-9      # 25 ticks
    assert r["dps"] == 2000 / 25                            # 10x the ledger's 2000/250
    # weapon rate 2/250 == ammo rate (1/125)/1 -> exactly sustainable
    assert abs(r["sustain_factor"] - 1.0) < 1e-9

    # regime 2, a helicopter whose reload replenishes during depletion
    r = cadence(500, 1, 20, None, ammo=12, ammo_usage=1, reload_count=1, reload_delay_pool=40)
    assert r["regime"] == SELF_RELOADING
    assert r["shots"] == 22 and r["seconds_at_full_rate"] == 420 / 25.0
    assert abs(r["sustain_factor"] - 0.5) < 1e-9            # (1/40) vs 1/20

    # A multi-delay burst uses each authored gap for a partial burst; it must not reuse the
    # first delay for the second gap.
    assert elapsed_for_shots(3, 100, 4, [1, 10, 2]) == 11

    # An underfilled magazine starves at the next weapon cycle; it is not labeled sustained
    # merely because a long simulation limit was reached.
    r = cadence(100, 1, 1, None, ammo=3, ammo_usage=2, reload_count=2,
                reload_delay_pool=100)
    assert r["dps"] is None and r["cadence_status"] == "STARVED_AFTER_RELOAD"
    assert r["starvation_elapsed"] == 1
    r = cadence(100, 1, 1, None, ammo=2, ammo_usage=2, reload_count=2,
                reload_delay_pool=100)
    assert r["dps"] is None and r["single_shot"] is True

    # regime 3: a total, never a rate
    r = cadence(4000, 1, 50, None, ammo=16, ammo_usage=1, rearmable=True)
    assert r["regime"] == AIRFIELD_REARM
    assert r["dps"] is None and r["sustain_factor"] is None
    assert r["sortie_damage"] == 64000

    # a pool with no replenishment mechanism at all is reported, never scored
    r = cadence(4000, 1, 50, None, ammo=255, ammo_usage=1)
    assert r["regime"] == FINITE_UNCLASSIFIED and r["dps"] is None

    # a single-shot pool has no rate, and keeps its regime label
    r = cadence(9000, 1, 60, None, ammo=1, ammo_usage=1, reload_count=1, reload_delay_pool=200)
    assert r["single_shot"] is True and r["dps"] is None
    assert r["regime"] == SELF_RELOADING and r["sortie_damage"] == 9000

    # AmmoUsage > 1 reduces the shots a pool affords
    r = cadence(1000, 1, 25, None, ammo=6, ammo_usage=3, reload_count=1, reload_delay_pool=100)
    assert r["sortie_damage"] == 2000                       # 6 // 3 == 2 shots
    print("ammo_cadence self-test OK")


if __name__ == "__main__":
    _selftest()
