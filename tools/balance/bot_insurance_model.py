#!/usr/bin/env python3
"""bot_insurance_model.py — executable reference model of `DynamicBotInsurance`.

    python tools/balance/bot_insurance_model.py            # behaviour table, all difficulties
    python tools/balance/bot_insurance_model.py --trace medium

⛔ WHY THIS EXISTS. `DynamicBotInsurance.cs` cannot be compiled, run or boot-gated from a cloud
container (no `engine/`, no dotnet — CLAUDE.md rule 7). The C# is therefore unverified *as code*.
But the part that is actually easy to get wrong is not the C# — it is the STATE MACHINE: a
threshold that falls, freezes, and re-arms, with a delay derived from a rolling average, has
several ways to oscillate, stick, or never fire. That much can be verified here, exactly, and it
is what `tools/tests/test_bot_insurance_model.py` asserts.

⚠ THIS FILE AND THE C# MUST BE CHANGED TOGETHER. It is a reference model, not documentation:
if they drift, the tests are testing a fiction. Keep `tick()` a line-for-line mirror of
`DynamicBotInsurance.ITick.Tick`.

THE MACHINE, in three phases:

  ARMING    the bar TRACKS the rolling average of total spendable funds, moving toward
             clamp(average, MinThreshold,
            MaxThreshold) by at most `rate_per_tick` a tick -- up when the average is above it,
             down when below, at the same rate either way. When the bar reaches the owner's liquid
             funds (`liquidity < threshold`) the owner qualifies -> freeze, compute the delay, go to
             DELAYING.

            ⛔ IT IS A SLEW-LIMITED TRACKER, NOT A ONE-WAY RAMP, AND NOT A FALLING BAR. Two
            earlier designs were tried and rejected against this model:
              * FALLING from MaxThreshold (the original spec) is DEAD MECHANICS. The trigger
                `liquidity < threshold` is easiest to satisfy when the bar is HIGHEST, so a falling bar
                fires on tick one for anyone under MaxThreshold and only ever makes triggering
                harder afterwards. Measured, every difficulty behaved identically and the whole
                ordering came from the delay divisor -- the rate did nothing at all.
              * RISING ONCE from zero works, but the bar never comes back down, so it stops
                describing the economy the moment the economy changes.
            Tracking in both directions keeps the rate meaningful (`cameogod` converges ten times
            faster than `easiest`) AND keeps the bar an honest smoothed picture of how the owner
            has actually been doing.
  DELAYING  wait `average / delay_divisor` ticks, clamped. Recovering above the frozen bar cancels
            outright and re-arms from the top.
  PAYING    grant a payout SCALED BY DEPTH until total spendable funds reach MaxThreshold, then
             re-arm. Resource-purifier deliveries bank only during this phase and every payout is
             capped at the remaining gap.

⭐ THE PAYOUT IS PROPORTIONAL TO DEPTH, WHICH IS WHERE THE OLD LADDER'S GRANULARITY CAME FROM.
The ten-rung ladder was not merely ten difficulties — the rungs STACKED, so a `cameogod` bot drew
1 credit/tick just under 10000 and 10 credits/tick near zero. A flat "on/off" payout throws that
away and makes the hardest bot draw its maximum the whole time it is insured. So:

    depth_permille = clamp(1000 * (MaxThreshold - liquidity) / MaxThreshold, 0, 1000)
    accumulator   += cash_per_tick * depth_permille
    grant          = accumulator // 1000        # and keep the remainder

Measured against the old ladder for `cameogod`: cash 9000 -> 1/tick (old: 1 rung), 5000 -> 5/tick
(old: 5 rungs), 0 -> 10/tick (old: 10 rungs). It REPRODUCES the ladder and then keeps going
between the rungs, which is the "more granular than before" the maintainer asked for.

⚠ Integer milli-credit accumulation, not floating point: the payout must be deterministic across
machines or it desyncs. The remainder carries, so a 0.5 credit/tick rate really pays 1 credit every
other tick rather than rounding to nothing — which is what a naive integer divide would do to every
low difficulty.

⚠ THE EXIT IS `MaxThreshold`, NOT THE FROZEN BAR. Leaving at the bar it entered on re-triggers
within a few ticks, forever — a payout oscillator. `test_paying_does_not_oscillate` pins that.

Everything scales by the owner's INDEX in the difficulty list, so a new difficulty is one more
name and no new traits or conditions — which is the whole point of replacing the ten-rung ladder.
"""
from __future__ import annotations

import argparse
import collections
import math
import sys

DIFFICULTIES = ["easiest", "veryeasy", "easy", "medium", "hard",
                "veryhard", "brutal", "challenger", "unbeatable", "cameogod"]

# Defaults mirroring DynamicBotInsuranceInfo. ⚠ AVERAGE_WINDOW is 1500 = ONE MINUTE at the mod's
# default 40ms timestep (mod.yaml GameSpeeds/default), not 3000.
#
# MIN_THRESHOLD is 1000 rather than 0, and with a STRICT `<` trigger that is load-bearing, not
# cosmetic: a persistently broke owner drives its own average to 0, the bar tracks it to 0, and
# `liquidity < 0` is unsatisfiable -- the mechanic would switch itself off in exactly the situation it
# exists for. The floor is the absolute poverty line: below it you are insured whatever your
# history says. See test_a_zero_floor_strands_a_bankrupt_bot.
#
# MAX_THRESHOLD is both the bar's ceiling AND the liquid-funds level at which a payout stops. Keep them the
# same number: a ceiling above the payout exit lets an owner trigger and then immediately stop
# paying, which is churn with no benefit.
AVERAGE_WINDOW = 1500
TICKS_PER_MINUTE = 1500        # 40ms timestep -- mods/cameo/mod.yaml GameSpeeds/default
MAX_THRESHOLD = 10000
MIN_THRESHOLD = 1000
MIN_RATE, MAX_RATE = 1, 10
MIN_DIVISOR, MAX_DIVISOR = 10, 100
MIN_DELAY, MAX_DELAY = 25, 1500
MIN_CASH, MAX_CASH = 1, 10
MIN_PURIFIER, MAX_PURIFIER = 5, 50
USE_PAR_CURVE = False

# --- net-worth layer (maintainer rulings, 2026-09-01) ---------------------------------------
# ARMY_VALUE_WEIGHT is 0 because PlayerStatistics exposes BOTH ArmyValue and AssetsValue and it is
# not settled here whether AssetsValue already counts combat units -- Common is not vendored, so
# it could not be checked from this container. At 0 the army is counted ONCE, through AssetsValue.
# ⚠ If Saturday shows AssetsValue excludes the army, raise this to 100. Do not guess: a wrong
# value double-counts the biggest term in the whole calculation.
ARMY_VALUE_WEIGHT = 0            # percent of ArmyValue added on top of AssetsValue

# The self-comparison is FOG-SAFE by ruling: a bot is measured against its OWN peak, never against
# another player's worth, which no player can see and which would rubber-band against the human.
MIN_SELF_RATIO = 100             # permille floor, so a total collapse cannot divide by ~0

# The par curve is disabled by default because its three magnitudes are provisional. Its ratio
# remains clamped so it can be enabled for measured tuning without dominating the self comparison.
PAR_RATIO_MIN, PAR_RATIO_MAX = 500, 2000        # permille

# Floor under the worth factor: a bot that is wealthy on paper but has no cash still gets SOME
# help, because assets it cannot sell do not rebuild a base.
MIN_WORTH_FACTOR = 250           # permille

# --- the par curve, as DETERMINISTIC INTEGER MATH ------------------------------------------------
# ⛔ NO exp() AND NO FLOATING POINT. This feeds a [Sync] value in a simulation OpenRA replays
# lockstep across machines; `Math.Exp` is not guaranteed bit-identical across platforms or
# runtimes, so a logistic evaluated live is a desync waiting for a multiplayer game. The curve is
# therefore SAMPLED into a table at authoring time and interpolated linearly between samples.
#
# ⭐ Which is also better for tuning: the shape is a yaml array, so retuning the economy model
# needs no rebuild -- exactly what "ship conservative, log for tuning" asks for.
#
# Samples run 0 to 3x the midpoint in steps of 0.125x, in permille of the way from the opening
# bank to the asymptote. Generated from the logistic k*t0 = 5.4 used by bot_difficulty_curve.py;
# index 8 is the midpoint and reads 498, i.e. half way, as a sigmoid must.
# ⚠ The 0.125x step is not cosmetic: at 0.25x, linear interpolation across the curve's steepest
# stretch diverged 22.5% from the logistic it was sampled from. Halving the step halves that.
PAR_SHAPE = [0, 4, 13, 29, 59, 113, 202, 334, 498, 661, 793, 883, 937, 967, 983, 991, 995, 998, 999, 999, 1000, 1000, 1000, 1000, 1000]
PAR_SHAPE_STEP = 125             # permille of the midpoint between samples

# Asymptote = PAR_BASE_WORTH + PAR_ASYMPTOTE_PER_RANK * (rank + 1).
# 15000 per rank == 5000 per harvester slot, since HarvesterLimit is exactly 3*(rank+1).
PAR_BASE_WORTH = 10000
PAR_ASYMPTOTE_PER_RANK = 15000
# Midpoint in ticks, interpolated by rank: easiest slowest. 12 min x ProductionTimeMultiplier/100,
# so 15.6 min (23400 ticks) at easiest down to 4.8 min (7200) at cameogod.
PAR_MIDPOINT_EASIEST, PAR_MIDPOINT_HARDEST = 23400, 7200


def par_worth(rank: int, ticks: int, count: int = len(DIFFICULTIES)) -> int:
    """Expected NET WORTH for this difficulty at this game time. Integer, deterministic."""
    midpoint = by_rank(PAR_MIDPOINT_EASIEST, PAR_MIDPOINT_HARDEST, rank, count)
    if midpoint <= 0:
        return PAR_BASE_WORTH

    progress = ticks * 1000 // midpoint                  # permille of the midpoint
    idx = progress // PAR_SHAPE_STEP
    if idx >= len(PAR_SHAPE) - 1:
        shape = PAR_SHAPE[-1]
    else:
        frac = progress - idx * PAR_SHAPE_STEP
        lo, hi = PAR_SHAPE[idx], PAR_SHAPE[idx + 1]
        shape = lo + (hi - lo) * frac // PAR_SHAPE_STEP

    asymptote = PAR_BASE_WORTH + PAR_ASYMPTOTE_PER_RANK * (rank + 1)
    return PAR_BASE_WORTH + (asymptote - PAR_BASE_WORTH) * shape // 1000


def by_rank(minimum: int, maximum: int, rank: int, count: int) -> int:
    """Integer interpolation across the difficulty list — the C# `ByRank`."""
    steps = count - 1
    if steps <= 0:
        return minimum
    return minimum + ((maximum - minimum) * rank) // steps


class Insurance:
    """One player's insurance state machine. `tick()` mirrors the C# `Tick` exactly."""

    def __init__(self, difficulty: str, difficulties: list[str] | None = None,
                 average_window: int = AVERAGE_WINDOW, max_threshold: int = MAX_THRESHOLD,
                 min_threshold: int = MIN_THRESHOLD, use_par_curve: bool = USE_PAR_CURVE):
        self.difficulties = difficulties or DIFFICULTIES
        self.rank = self.difficulties.index(difficulty) if difficulty in self.difficulties else -1
        self.max_threshold = max_threshold
        self.use_par_curve = use_par_curve
        self.min_threshold = min_threshold

        n = len(self.difficulties)
        self.rate_per_tick = max(1, by_rank(MIN_RATE, MAX_RATE, max(self.rank, 0), n))
        self.delay_divisor = max(1, by_rank(MIN_DIVISOR, MAX_DIVISOR, max(self.rank, 0), n))
        self.cash_per_tick = by_rank(MIN_CASH, MAX_CASH, max(self.rank, 0), n)
        self.purifier_modifier = by_rank(MIN_PURIFIER, MAX_PURIFIER, max(self.rank, 0), n)

        self.history: collections.deque[int] = collections.deque(maxlen=max(1, average_window))
        self.threshold = 0
        self.delay_remaining = 0
        self.banked = 0
        self.phase = "arming"
        self.paid = 0
        self.accumulator = 0            # milli-credits carried between ticks
        self.ticks = 0                  # game time, for the par curve
        self.peak_worth = 0             # the fog-safe self-reference
        self.last_worth_factor = 1000   # permille, for tracing

    def net_worth(self, cash: int, resources: int, assets: int, army: int) -> int:
        """Cash + resources + everything owned when PlayerStatistics is available."""
        return cash + resources + assets + army * ARMY_VALUE_WEIGHT // 100

    def worth_factor_permille(self, worth: int) -> int:
        """⭐ How much of the peak payout this owner's NET WORTH justifies, 0..1000.

        Two ratios, both clamped, combined by GEOMETRIC MEAN rather than by product:

            r_self   = worth / my own peak worth      (fog-safe -- ruling, 2026-09-01)
            r_target = worth / par curve at this time (clamped hard; its magnitudes are invented)
            w        = sqrt(r_self * r_target)

        ⛔ NOT a product. The two ratios are correlated -- a bot behind its own peak is usually
        also behind the curve -- so multiplying squares one piece of evidence: 0.5 x 0.5 = 0.25
        claims "four times worse than par" from two observations that each said "twice". The
        geometric mean keeps the answer on the scale of its inputs. See bot_difficulty_curve.py.

        The result is inverted into a factor: at par (w = 1) the owner is doing fine and the factor
        collapses to its floor; at total collapse (w -> 0) it reaches 1000.
        """
        if self.peak_worth <= 0:
            return 1000

        r_self = min(1000, max(MIN_SELF_RATIO, 1000 * worth // self.peak_worth))

        r_target = 1000
        if self.use_par_curve:
            target = par_worth(self.rank, self.ticks, len(self.difficulties))
            if target > 0:
                r_target = min(PAR_RATIO_MAX, max(PAR_RATIO_MIN, 1000 * worth // target))

        w = int(math.isqrt(r_self * r_target))          # integer sqrt -> deterministic
        shortfall = max(0, min(1000, 1000 - w))
        return MIN_WORTH_FACTOR + (1000 - MIN_WORTH_FACTOR) * shortfall // 1000

    def depth_permille(self, liquidity: int) -> int:
        """How deep below the cap the owner is, 0 (at the cap) to 1000 (broke).

        Measured against MaxThreshold rather than against the dynamic bar on purpose: this is the
        ABSOLUTE poverty scale the old ladder used, so the two agree rung for rung.
        """
        return max(0, min(1000, 1000 * (self.max_threshold - liquidity) // self.max_threshold))

    @property
    def average(self) -> int:
        return sum(self.history) // len(self.history) if self.history else 0

    def resource_accepted(self, value: int) -> None:
        """Mirror `INotifyResourceAccepted`: only distressed deliveries may earn purifier cash."""
        if self.rank >= 0 and self.phase == "paying":
            self.banked += value

    def tick(self, cash: int, resources: int = 0, assets: int = 0, army: int = 0,
              has_statistics: bool = True) -> int:
        """Advance one tick. Returns credits granted this tick.

        ⭐ TWO-FACTOR, by ruling: total immediately spendable funds decide WHETHER the insurance
        arms and fires, NET WORTH decides HOW MUCH. That fixes the false positive where a bot has
        no cash but enough stored ore to spend, or a bot holds a 30,000-credit army and is simply
        spending correctly while its harvesters will refill it.

        `has_statistics` models the C# trait's `stats != null` check. A real PlayerStatistics
        instance whose values are all zero is still statistics; only a missing trait leaves the
        worth factor neutral at 1000.
        """
        if self.rank < 0:
            return 0

        self.ticks += 1
        liquidity = cash + resources
        self.history.append(liquidity)
        granted = 0

        worth = self.net_worth(cash, resources, assets, army)
        self.peak_worth = max(self.peak_worth, worth)
        self.last_worth_factor = self.worth_factor_permille(worth) if has_statistics else 1000

        if self.phase == "arming":
            target = min(max(self.average, self.min_threshold), self.max_threshold)
            step = max(-self.rate_per_tick, min(self.rate_per_tick, target - self.threshold))
            self.threshold += step
            # ⛔ STRICTLY BELOW. With `<=` the bar converges to the average, the average converges
            # to a stable cash pile, and every bot under the cap eventually insures itself -- the
            # mechanic stops being an emergency measure and becomes baseline income. Strict `<`
            # means "poorer than your own recent normal", which is the actual signal wanted.
            if liquidity < self.threshold:
                self.delay_remaining = min(max(self.average // self.delay_divisor, MIN_DELAY),
                                           MAX_DELAY)
                self.phase = "delaying"

        elif self.phase == "delaying":
            if liquidity > self.threshold:
                # Unfreeze only. Slamming the bar back to zero would throw away the tracker and
                # make the next arming cycle start from a lie about the economy.
                self.phase = "arming"
            else:
                self.delay_remaining -= 1
                if self.delay_remaining <= 0:
                    self.phase = "paying"

        elif self.phase == "paying":
            if liquidity >= self.max_threshold:
                self.banked = 0
                self.accumulator = 0
                self.phase = "arming"
            else:
                depth = max(1, (self.depth_permille(liquidity) * self.last_worth_factor + 999) // 1000)
                self.accumulator += self.cash_per_tick * depth
                requested = self.accumulator // 1000
                self.accumulator %= 1000
                granted += min(requested, max(0, self.max_threshold - liquidity))

                if self.banked >= 250:
                    bonus = self.banked * self.purifier_modifier * depth // 100000
                    granted += min(bonus, max(0, self.max_threshold - liquidity - granted))
                    self.banked = 0

        self.paid += granted
        return granted


def simulate(difficulty: str, cash: int, ticks: int, spend_per_tick: int = 0) -> dict:
    """Run a bot that holds `cash` and optionally bleeds `spend_per_tick`, and report."""
    ins = Insurance(difficulty)
    first_payout = None
    for t in range(ticks):
        granted = ins.tick(max(0, cash))
        cash += granted - spend_per_tick
        if granted and first_payout is None:
            first_payout = t
    return {
        "difficulty": difficulty,
        "rate": ins.rate_per_tick,
        "divisor": ins.delay_divisor,
        "cash_per_tick": ins.cash_per_tick,
        "purifier": ins.purifier_modifier,
        "first_payout_tick": first_payout,
        "total_paid": ins.paid,
        "end_cash": cash,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cash", type=int, default=1500, help="starting (and held) cash")
    ap.add_argument("--ticks", type=int, default=3000, help="ticks to simulate")
    ap.add_argument("--trace", metavar="DIFFICULTY", help="print a phase trace for one difficulty")
    args = ap.parse_args()

    if args.trace:
        ins = Insurance(args.trace)
        print(f"# trace — {args.trace} (rate {ins.rate_per_tick}/tick, divisor {ins.delay_divisor}, "
              f"{ins.cash_per_tick} credits/tick, purifier {ins.purifier_modifier}%)\n")
        print("| tick | phase | threshold | avg | cash | granted |")
        print("|--:|---|--:|--:|--:|--:|")
        cash, last = args.cash, None
        for t in range(args.ticks):
            g = ins.tick(max(0, cash))
            cash += g
            if ins.phase != last or t % 500 == 0:
                print(f"| {t} | {ins.phase} | {ins.threshold} | {ins.average} | {cash} | {g} |")
                last = ins.phase
        return 0

    print(f"# DynamicBotInsurance — behaviour at cash {args.cash}, {args.ticks} ticks "
          f"({args.ticks / 25:.0f}s at the default 40ms timestep)\n")
    print("| difficulty | rate/tick | divisor | credits/tick | purifier | first payout | total paid |")
    print("|---|--:|--:|--:|--:|--:|--:|")
    for d in DIFFICULTIES:
        r = simulate(d, args.cash, args.ticks)
        first = r["first_payout_tick"]
        print(f"| {d} | {r['rate']} | {r['divisor']} | {r['cash_per_tick']} | {r['purifier']}% | "
              f"{'never' if first is None else first} | {r['total_paid']} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
