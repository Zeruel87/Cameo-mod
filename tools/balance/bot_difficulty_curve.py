#!/usr/bin/env python3
"""bot_difficulty_curve.py — the expected-net-worth curve behind adaptive bot difficulty.

    python tools/balance/bot_difficulty_curve.py              # the target curves
    python tools/balance/bot_difficulty_curve.py --combine    # product vs geometric mean

⛔ WHAT THIS IS FOR. The maintainer's proposal (2026-09-01): stop measuring bot distress by cash
alone and measure it against NET WORTH -- cash + army + other assets -- compared two ways:

    r_target = worth / T(t, difficulty)      how am I doing against where this difficulty
                                             SHOULD be at this point in the match?
    r_peers  = worth / mean(opponent worth)  how am I doing against the field?

...then combine them into one distress multiplier that stands in for "effective cash" in
`DynamicBotInsurance`.

TWO THINGS THIS FILE EXISTS TO SETTLE, both of which change the answer:

1. THE CURVE IS A LOGISTIC, NOT AN EXPONENTIAL APPROACH. "Rises slowly, then grows exponentially,
   then flattens to an asymptote" is a SIGMOID. The function people usually reach for --
   `A - (A-S)*exp(-t/tau)`, variously called the monomolecular, Mitscherlich, or Newton-cooling
   curve, or "exponential rise to a maximum" -- has NO slow start: it grows FASTEST at t=0 and
   decelerates from there. Both are plotted below so the difference is visible rather than argued.
   An RTS economy really is sigmoid: a fixed opening bank, slow income while the first harvesters
   pay themselves off, compounding as refineries multiply, then a ceiling at the build limits.

2. THE TWO RATIOS MUST NOT BE MULTIPLIED. They are strongly CORRELATED -- a bot behind the curve
   is usually also behind the field, because both measure the same underlying failure. Multiplying
   squares that one piece of evidence: 0.5 x 0.5 = 0.25 claims "four times worse than par" from
   two observations that each said "twice". The geometric mean sqrt(a*b) = 0.5 is the standard fix
   and keeps the result on the same scale as its inputs. `--combine` shows the divergence.

⭐ THE ASYMPTOTE SCALE IS ALREADY IN THE TREE. `BotLimits` HarvesterLimit is 3*(rank+1) --
3, 6, 9 ... 30 -- an exact 1x to 10x ladder, which is the scale the maintainer guessed at. Income
capacity IS harvester count, so the per-difficulty asymptote needs no new invented numbers.

⭐ AND THE TIME CONSTANT IS TOO. ProductionTimeMultiplier runs 130 (easiest) to 40 (cameogod), so
scaling the curve's midpoint by it makes harder bots ramp proportionally sooner, reusing a number
that is already balanced rather than adding a second one to keep in sync.
"""
from __future__ import annotations

import argparse
import math
import pathlib
import re
import sys

DIFFICULTIES = ["easiest", "veryeasy", "easy", "medium", "hard",
                "veryhard", "brutal", "challenger", "unbeatable", "cameogod"]

def _harvester_limits() -> dict[str, int]:
    """HarvesterLimit per difficulty, READ from ai.yaml rather than hardcoded.

    ⚠ The whole point of deriving the asymptote from the build limits is that it stays tied to
    them. A copy pasted in here would drift the moment someone retunes `BotLimits`, and the curve
    would keep quoting numbers the mod no longer has.
    ⚠ `BotLimits@god` is the block name but `cameogod` is the bot type — a naming inconsistency in
    ai.yaml, mapped here rather than "fixed", because renaming the block is a yaml change needing
    a boot gate.
    """
    src = pathlib.Path("mods/cameo/ai/ai.yaml").read_text(encoding="utf-8")
    found = dict(re.findall(r"BotLimits@(\w+):\n(?:\s+\w+:.*\n)*?\s+HarvesterLimit:\s*(\d+)", src))
    found = {("cameogod" if k == "god" else k): int(v) for k, v in found.items()}
    missing = [d for d in DIFFICULTIES if d not in found]
    if missing:
        raise SystemExit(f"ai.yaml has no HarvesterLimit for: {', '.join(missing)}")
    return found


def _production_time() -> dict[str, int]:
    """ProductionTimeMultiplier per difficulty, read from defaults.yaml."""
    src = pathlib.Path("mods/cameo/rules/defaults.yaml").read_text(encoding="utf-8")
    found = {k: int(v) for k, v in
             re.findall(r"ProductionTimeMultiplier@(\w+)botplayer:\n\s+Multiplier:\s*(\d+)", src)}
    missing = [d for d in DIFFICULTIES if d not in found]
    if missing:
        raise SystemExit(f"defaults.yaml has no ProductionTimeMultiplier for: {', '.join(missing)}")
    return found


HARVESTER_LIMIT = _harvester_limits()
PRODUCTION_TIME = _production_time()

TICKS_PER_MINUTE = 1500          # 40ms timestep -- mods/cameo/mod.yaml GameSpeeds/default
START_CASH = 10000               # opening bank; the curve must equal this at t=0
ASYMPTOTE_PER_HARVESTER = 5000   # tuning knob: net worth a bot converges to, per harvester slot
MIDPOINT_MINUTES = 12.0          # when a MEDIUM bot reaches halfway to its asymptote
# ⚠ Steepness is expressed RELATIVE TO THE MIDPOINT, not per minute. A fixed per-minute k would
# give faster difficulties a relatively shallower S-curve -- an artifact of the parameterisation,
# not a design intent -- and it made this tool disagree with the shipped integer table by 25%.
# k * midpoint = 5.4 means every difficulty follows the SAME economic story, just faster or slower.
STEEPNESS_X_MIDPOINT = 5.4


def asymptote(difficulty: str) -> int:
    """Where this difficulty's economy flattens out. Derived from its harvester cap."""
    return START_CASH + ASYMPTOTE_PER_HARVESTER * HARVESTER_LIMIT[difficulty]


def midpoint(difficulty: str) -> float:
    """Minutes to half the asymptote, scaled by the difficulty's own production speed."""
    return MIDPOINT_MINUTES * PRODUCTION_TIME[difficulty] / 100.0


def logistic(difficulty: str, minutes: float) -> int:
    """⭐ The curve. Slow, then steep, then flat — and exactly START_CASH at t=0.

    Anchored so T(0) == START_CASH rather than merely approaching it: a raw logistic starts a
    little above its floor, and an opening bank that does not match the lobby's starting cash makes
    every bot look behind from tick one.
    """
    a, t0 = asymptote(difficulty), midpoint(difficulty)
    k = STEEPNESS_X_MIDPOINT / t0
    raw = lambda m: 1.0 / (1.0 + math.exp(-k * (m - t0)))
    span = 1.0 - raw(0.0)
    return int(START_CASH + (a - START_CASH) * (raw(minutes) - raw(0.0)) / span)


def mitscherlich(difficulty: str, minutes: float) -> int:
    """The curve people usually reach for. NO slow start — fastest growth is at t=0."""
    a, tau = asymptote(difficulty), midpoint(difficulty)
    return int(a - (a - START_CASH) * math.exp(-minutes / tau))


def combine(r_target: float, r_peers: float, how: str) -> float:
    if how == "product":
        return r_target * r_peers
    if how == "geometric":
        return math.sqrt(max(r_target, 0.0) * max(r_peers, 0.0))
    if how == "min":
        return min(r_target, r_peers)
    raise ValueError(how)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--combine", action="store_true", help="show product vs geometric mean")
    args = ap.parse_args()

    if args.combine:
        print("# Combining the two ratios — product vs geometric mean\n")
        print("The maintainer's worked example is the second row.\n")
        print("| behind the curve | behind the field | product | geometric mean | min |")
        print("|--:|--:|--:|--:|--:|")
        for a, b in ((1.0, 1.0), (0.5, 0.5), (0.5, 1.0), (1.0, 0.5),
                     (0.8, 0.8), (0.25, 0.25), (0.5, 2.0), (2.0, 2.0)):
            print(f"| {a:.2f} | {b:.2f} | {combine(a,b,'product'):.3f} | "
                  f"{combine(a,b,'geometric'):.3f} | {combine(a,b,'min'):.3f} |")
        print("\n⛔ Row 2 is the case that matters: two observations each saying \"about half par\" "
              "become \"a quarter of par\" under the product. Row 6 is worse — 0.25 and 0.25 "
              "compound to 0.0625, which would pin the insurance at maximum permanently.")
        print("⭐ Row 7 shows the other virtue of the geometric mean: being twice the field while "
              "half the curve reads as 1.0 (par), which is the honest answer.")
        return 0

    print(f"# Expected NET WORTH by difficulty and game time\n")
    print(f"Asymptote = {START_CASH} + {ASYMPTOTE_PER_HARVESTER} x HarvesterLimit  "
          f"(HarvesterLimit = 3x(rank+1), measured from ai.yaml)\n"
          f"Midpoint  = {MIDPOINT_MINUTES} min x ProductionTimeMultiplier/100 "
          f"(measured from defaults.yaml)\n")

    mins = [0, 5, 10, 15, 20, 30, 45]
    print("| difficulty | harv | asymptote | midpoint | " + " | ".join(f"{m}m" for m in mins) + " |")
    print("|---|--:|--:|--:|" + "--:|" * len(mins))
    for d in DIFFICULTIES:
        row = " | ".join(f"{logistic(d, m):,}" for m in mins)
        print(f"| {d} | {HARVESTER_LIMIT[d]} | {asymptote(d):,} | "
              f"{midpoint(d):.1f}m | {row} |")

    print("\n## Shape check — logistic vs the exponential approach (medium)\n")
    print("| minutes | " + " | ".join(f"{m}m" for m in mins) + " |")
    print("|---|" + "--:|" * len(mins))
    print("| logistic (slow, steep, flat) | " + " | ".join(f"{logistic('medium', m):,}" for m in mins) + " |")
    print("| Mitscherlich (fastest at t=0) | " + " | ".join(f"{mitscherlich('medium', m):,}" for m in mins) + " |")
    print("\n⭐ The first five minutes are the tell: the logistic barely moves (a bot is still "
          "paying off its first harvesters) while the Mitscherlich curve has already spent a third "
          "of its growth. Judging a bot against the wrong one makes every early game look like a "
          "disaster and fires the insurance for everybody.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
