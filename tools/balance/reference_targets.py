#!/usr/bin/env python3
"""reference_targets.py — the R4 synthesis for real actors: 3 references + Cameo, one vote each.

PRIOR ART, and why this is not a fourth copy of it:
  * `assign_references.py` chooses WHICH reference units a Cameo actor may use. It stops at the
    pairing and stores only the reference's name/hp/cost.
  * `reference_distribution.py` owns the coordinate machinery (`aggregates`, `coordinates`,
    `project`, `gm`) and builds every source's own distributions. All of it is imported here.
  * `explain_unit.py` shows ONE actor's working, and re-matches with the superseded prefix test
    rather than reading the assignment.
This module is the missing join: the ASSIGNMENT's pairs, run through the DISTRIBUTION's
coordinates, for a whole faction at a time.

⛔ R4 — EQUAL THIRDS, AND CAMEO ALWAYS VOTES (maintainer, `REFERENCE_EXTRACTION_PLAN.md`):
   `Cameo TD GDI = DTA GDI x Combined Arms GDI x current Cameo TD GDI`, each 1/3, geometric mean.
   Generalised: every voice is equal, so with 3 references Cameo is 1 of 4 = 25%.

⛔ RAW STATS ARE NEVER AVERAGED ACROSS SOURCES. DTA runs ~2,500 HP vehicles and Combined Arms
~30,000; their mean belongs to no game. Only the DIMENSIONLESS coordinates are pooled, then
projected onto Cameo's own distribution. See `REFERENCE_METHOD.md` §1-§2.

    python tools/balance/reference_targets.py --faction td_gdi td_nod ra1_allies ra1_soviets
    python tools/balance/reference_targets.py --faction td_gdi --md docs/balance/targets_td.md
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
import faction_routes as fr  # noqa: E402
import formula  # noqa: E402  — the ONE owner of the burst-cycle arithmetic
import reference_distribution as rd  # noqa: E402

ROOT = rd.ROOT
ASSIGN = ROOT / "docs" / "balance" / "derived" / "reference_assignment.json"
STATS = ("hp", "speed", "w_range", "w_dps", "cost")

# ⛔ DISCRETE COUNTS ARE TAKEN DIRECTLY, NEVER PROJECTED (maintainer caught this 2026-09-12:
# "the mammoth tank always has 2 bursts for all weapons from all sources right? and you
# averaged it to 1.67x?" -- correct, and the projection was the culprit, not an average).
#
# `target_for`'s normal path converts a raw value into its POSITION within that source's own
# distribution and maps the position onto Cameo's. That is right for HP, speed, cost, range
# and DPS: continuous magnitudes spanning orders of magnitude, where "this unit is a heavy in
# its own game" is the transferable fact and the raw number is not.
#
# It is WRONG for `w_burst`. Burst is a small integer the engine can only take whole, the
# distributions have wildly different supports, and they are dominated by outliers that have
# nothing to do with the unit in hand:
#
#     DTA Enhanced        burst min 2  max   4
#     OpenRA Tiberian Dawn          1        5
#     Combined Arms                 1       30
#     Cameo (projected onto)        1      100
#
# So a Mammoth's 2 -- low inside a 1..30 support -- maps low into a 1..100 support and lands
# at 1.67, even though EVERY eligible source says exactly 2. (The three `HTNK.*` Combined Arms
# variants that say 1 or 2 are `reference_base_eligible: False` upgraded variants and never
# voted at all.)
#
# MEASURED over the 209 actors that have both a burst and a burst target: 163 have UNANIMOUS
# agreement among their eligible sources, and projection contradicts that unanimous value on a
# large share of them -- `cabal_plasmaturret` every source 5, projected 2.21; `forgotten_mlrs`
# every source 8, projected 5.08; `cabal_cyborginfantry` every source 3, projected 1.92.
#
# Direct pooling reports a CHANGE on 98 of 209 against projection's 77, and that is the point:
# the extra ones are real disagreements between Cameo and its sources, which is exactly what
# the maintainer asked to see flagged in the map. `Burst` may not be touched without explicit
# permission, so the number has to be the sources' actual burst, not a position-derived one.
#
# One vote per source (median across that source's eligible rows), then the median of the
# source votes -- median, not mean, because the answer must be a count and an even split
# between 2 and 4 should read as one of them, not as 3.
DIRECT_STATS = ("w_burst",)

# ⛔ LAW-GOVERNED STATS TAKE NO REFERENCE TARGET AT ALL.
# `turn_speed` and `turn_ratio` are not free parameters in Cameo — DESIGN.md fixes them:
# `TurnSpeed = Speed / 5` for turreted units, `2 x Speed / 5` for turretless/frontal ones,
# DERIVED IN C# and not written in yaml (maintainer 2026-09-07), with a turret always matching
# its hull and `audit_turn_speed.py` T3 guarding it. Cameo's `turn_ratio` is therefore 5.0 or
# 2.5 BY LAW, and asking the peers what it should be is asking a question Cameo has already
# answered — a reference target here can only contradict a shipped ruling.
#
# And the projection made that contradiction loud, because `turn_ratio` is DIMENSIONLESS
# (speed / turn_speed), so the peers' raw values are directly comparable and projecting a
# position in a distribution is meaningless. Measured 2026-09-12 on actors whose sources all
# agree:
#     asianalliance_howitzer      all sources 1.00   projected 3.83
#     asianalliance_pulverizer    all sources 0.60   projected 3.51
#     asianalliance_harbinger     all sources 4.67   projected 11.55
# An 11.55 turn ratio is not a number any mod authored; it is an artifact.
#
# ⚠ Two different repairs, and the distinction matters. `w_burst` is scale-free AND a real
# design input, so it moved to DIRECT_STATS and still produces a target. `turn_*` is scale-free
# and NOT an input, so it produces none. Do not "fix" these by adding them to DIRECT_STATS.
#
# Verified safe: nothing consumes a turn target. `build_reference_report` shows hp/speed/range/
# dps/burst/cost, `build_japan_pilot.AXES` is hp/speed/w_range/cost, and `apply_balance` writes
# `turn_speed` from the LEDGER (where the derived law put it), never from a reference.
LAW_GOVERNED_STATS = ("turn_speed", "turn_ratio")

# ---------------------------------------------------------------------------------------- #
# R1 — THE WEAPON STATS ARE THE INPUTS; TOTAL DPS IS A GUARD RAIL, NOT A FIFTH INPUT.
#
# Maintainer ruling, 2026-09-12, asked directly: "each individual stat like damage per shot,
# burst, burst delay, reload delay should be referenced separately but also at the same time
# the total DPS should kept as a verifier so nothing suddenly becomes too extreme right?"
#
# ⛔ WHY THIS HAD TO BE RULED. `target_for` projects EVERY stat against its own distribution
# independently, so `w_dps`, `w_damage`, `w_burst`, `w_reload` and `w_range` were five separate
# votes with nothing tying them together — and they are mutually inconsistent BY CONSTRUCTION,
# not by accident. On `td_gdi_mammothtank` (3 sources, STRONG on all three):
#
#     w_dps projected alone            400 -> 695   (+73.7%)
#     damage +9.1% with reload -11.1%  400 -> 485   (+21.2%)  through the identity below
#     the two answers are 1.43x apart
#
# Applying more than one of them at once silently picks a rebalance nobody chose. R1 resolves
# it: the COMPONENTS are applied, and `w_dps` is only ever consulted to ask "did composing the
# components produce something extreme?".
COMPONENT_STATS = ("w_damage", "w_burst", "w_reload")   # separately referenced, applied
VERIFIER_STATS = ("w_dps",)                             # consulted, never applied

# The composed target may not be wilder than this against the CURRENT value. DISAGREE_RATIO
# sits BELOW the mammoth's own 1.43x component-vs-aggregate gap, so the case that motivated
# the ruling is flagged rather than waved through.
EXTREME_RATIO = 2.00
DISAGREE_RATIO = 1.25


def recover_burst_time(damage, dps, reload_ticks):
    """The ticks spent INSIDE the burst, recovered from the row's own identity.

    ⛔ DO NOT TAKE `w_damage` AS DAMAGE PER SHOT. The convention differs by source and reading
    it wrong double-counts burst:
      * `extract_peer_units` sets `w_damage = audit["damage_pos"]`, damage per SHOT, and its
        `w_dps = damage_pos * burst / cycle`.
      * the frozen Cameo snapshot's `w_damage` is BURST-INCLUSIVE, and its identity is
        `w_dps = w_damage / cycle` with no burst factor at all.
    Proven on the shipped rows: mammoth `32000/400 = 80` ticks against `w_reload 72`, and
    MLRS `48000/352.94 = 136` against `w_reload 111`. Multiplying by burst as well gives the
    mammoth 800 dps against a true 400, and reported a bogus "EXTREME" verdict for the MLRS.

    This is safe across both conventions because it never assumes one: the cycle comes out of
    `damage / dps`, whatever those two mean, and the burst time is what is left after reload.
    A target projected by `target_for` arrives in the SAME units as the Cameo row it is
    projected onto, so composing in Cameo's convention is correct by construction.
    """
    if not damage or not dps:
        return None
    return max(0.0, float(damage) / float(dps) - float(reload_ticks or 0))


def burst_delay_of(row):
    """Per-shot burst delay recovered from a row, under the ONE formula.

    Invert `damage_per_tick`: the cycle is `per_shot * burst / rate`, and what is left after
    `ReloadDelay` is spread across the `burst - 1` gaps. Single-shot weapons return None — there
    is no gap to measure, and all 477 such rows in the tree recover exactly 0.00, so a printed
    zero would look like a measurement of something that does not exist.
    """
    burst = float(row.get("w_burst") or 1)
    per_shot, rate = damage_per_shot(row), row.get("w_dps")
    if burst <= 1 or not per_shot or not rate:
        return None
    # ⭐ A REVIEWED CYCLE PROOF IS READ, NEVER INVERTED. `ini_cycle_evidence` carries a
    # hand-reviewed timing model for 444 DTA rows — `cycle = reload + sum(burst gaps) +
    # post-burst jitter + charge`, with `dps = damage * shots / cycle_mean`. That IS the one
    # formula, so those rows need no recovery at all: the gaps are stated outright.
    #
    # ⛔ AND INVERTING THEM WAS WRONG IN BOTH DIRECTIONS, measured 2026-09-13 over the 91 proven
    # rows in the pools — 32 of them disagreed with their own proof:
    #   * CONTAMINATION. The inversion cannot see `post_burst_jitter`, so it charges that time to
    #     the burst gaps. Every mean-1-tick jitter row came back exactly one tick high — `HTNK`
    #     6.0 against a proven 5.0, `3TNK` 2.0 against 1.0, `MSAM` 10.0 against 9.0.
    #   * FALSE WITHHOLDING. `MLRS` "SSM Launcher" (damage 100, burst 2, reload 400, rate 0.25)
    #     satisfies `rate == damage / reload` BY COINCIDENCE — its proof puts the single gap at
    #     400 ticks (the attached-particle Rearm_Delay branch returns ROF after each emission),
    #     so `100 x 2 / (400 + 400) = 0.25` as well. Both identities hold at once whenever the
    #     gap happens to equal the reload, and the burst-1 test below then refused a delay that
    #     was sitting there, proven, in the sidecar. Generals Alpha's Dragon Tank is the same
    #     coincidence. That row is `td_nod_ssmlauncher`'s reference, so the withholding was
    #     visible in the map.
    proof = row.get("w_cycle_evidence")
    if proof:
        shots = proof.get("cycle_shots", proof["burst"])
        if shots <= 1:
            return None
        return sum(d["mean"] for d in proof["burst_delays"]) / (shots - 1.0)
    reload_ticks = float(row.get("w_reload") or 0)
    # ⛔ 334 OF 621 BURST ROWS PUBLISH A RATE THAT NEVER FOLDED BURST IN, and recovering a delay
    # from one of those produces a confident, meaningless number. Measured 2026-09-13 across the
    # peer corpus: those rows satisfy `rate == damage / reload` exactly — the burst-1 identity —
    # while declaring `Burst > 1`, so the cadence they describe is one shot per cycle no matter
    # what their own `w_burst` says. DTA's `MLRS` is the case the maintainer surfaced: damage 100,
    # burst 2, reload 400, rate 0.25 = 100/400. Treating that rate as `damage * burst / cycle`
    # implies a cycle of 800 ticks and hands back a 400-tick "burst delay" — exactly its reload,
    # which is the signature of the arithmetic folding back on itself.
    #
    # This is NOT the same as the negative-remainder case below: there the numbers contradict each
    # other, here they are self-consistent under a DIFFERENT formula. Both are withheld, and both
    # for the same reason — a recovered value is only meaningful if the row's own rate was built
    # the way this function inverts it.
    if reload_ticks and abs(float(rate) - per_shot / reload_ticks) < 1e-9 * max(1.0, float(rate)):
        return None
    remaining = per_shot * burst / float(rate) - reload_ticks
    # ⭐ AN IMPOSSIBLE TIMING MODEL IS REFUSED, NOT CLAMPED (adopted from `41d0dad57`, and the
    # better half of that change). A cycle SHORTER than the row's own `ReloadDelay` cannot
    # happen — the reload is a floor — so a negative remainder means the row's damage, rate and
    # reload do not describe one weapon. `max(0.0, ...)` would quietly turn that contradiction
    # into "this weapon has no burst delay" and certify it.
    if remaining < -1e-6:
        return None
    return max(0.0, remaining) / (burst - 1.0)


def damage_per_shot(row):
    """The row's damage PER SHOT — derived, because `w_damage` is now per CYCLE.

    ⭐ THE REFERENCED COORDINATE IS PER CYCLE (maintainer, 2026-09-13) — burst is a delivery
    choice and the whole-burst total is the comparable magnitude. `reference_distribution.
    to_per_cycle` therefore puts every corpus in per-cycle units and carries the per-shot figure
    alongside as `w_damage_per_shot`, so the formula can still be written the way it was ruled:

        rate = damage_per_shot * burst / (reload + sum of the Burst - 1 delays)

    Both spellings are the same number — `per_shot * burst` IS the cycle total — so nothing about
    the anchors moves. What changes is which quantity gets PROJECTED, and that had to change:
    Shattered Paradise ships the Mammoth Mk. II at Burst 4 where OpenRA TS ships it at Burst 2,
    and per shot both read 4,000, so projecting per-shot called them identical while their real
    output differs 16,000 to 8,000.
    """
    d = row.get("w_damage_per_shot")
    if d is not None:
        return float(d)
    # A row that never went through `to_per_cycle` still answers correctly.
    raw, burst = row.get("w_damage"), float(row.get("w_burst") or 1)
    return None if raw is None else float(raw) / burst if burst > 1 else float(raw)


def damage_per_cycle(row):
    """The row's damage for one FULL cycle — the quantity the reference map projects."""
    d = row.get("w_damage")
    return None if d is None else float(d)


def burst_time(burst, burst_delays):
    """Total ticks spent INSIDE the burst — the sum of its `Burst - 1` gaps.

    ⛔ THIS DELEGATES TO `formula.burst_delay_sum` AND MUST KEEP DOING SO. The pricing pipeline
    has owned this arithmetic since long before the reference layer existed, it already reads
    `WeaponInfo.BurstDelays = [5]` as its default, and it already implements exactly the rule the
    maintainer stated on 2026-09-13: *"if burst delays vary between bursts then you need to simply
    add all the burst delays up together with the reload delay"*. I briefly shipped a second copy
    here — including a duplicate `ENGINE_DEFAULT_BURST_DELAY` — which is the `allows()` mistake
    this repo has already paid for twice: two implementations agree until one of them is fixed.

    ⭐ THE ENGINE'S RULE, checked against source rather than assumed
    (`OpenRA.Mods.Common/Traits/Armament.cs`):

        line 146  if (Burst > 1 && BurstDelays.Length > 1 && BurstDelays.Length != Burst - 1)
                      throw new YamlException("... must be single entry or Burst - 1");
        line 476  if (BurstDelays.Length == 1) FireDelay = BurstDelays[0];
                  else                         FireDelay = BurstDelays[Burst - (remaining + 1)];

    An array is legal ONLY at length 1 (used for every gap) or exactly `Burst - 1` (walked in
    order). There is no "repeat the last entry" — a partial array refuses to boot. So the
    maintainer's "the number of burst delays should always be bursts - 1" is the engine's own
    rule, with the single entry as its shorthand, and `WeaponInfo.cs:129` supplies `[5]` to the
    36 Cameo weapons with `Burst > 1` that declare none.

    ⚠ ONE DIFFERENCE, AND IT IS UNREACHABLE TODAY. On an ILLEGAL array length `formula` returns
    `sum(values[:gaps])` for a deterministic diagnostic, where withholding would arguably be
    safer. Measured across the tree: 829 weapons use a single entry, 36 declare none, 0 vary and
    **0 carry an illegal length** — nothing in Cameo reaches that branch, and a weapon that did
    would fail the boot gate before it could reach a ledger.
    """
    return formula.burst_delay_sum(int(float(burst or 1)), burst_delays)


def damage_per_tick(damage_per_shot_value, burst, reload_ticks, burst_delay):
    """⭐ THE RATE FORMULA. One formula, everywhere, for Cameo and reference alike.

        rate = damage_per_shot * burst / (reload_delay + (burst - 1) * burst_delay)

    ⚠ THE UNIT IS DAMAGE PER **TICK**, NOT PER SECOND (maintainer, 2026-09-12: *"Actually it's
    damage per tick and not damage per second so the term is misleading"*). Every term in the
    divisor — `ReloadDelay`, `BurstDelays` — is authored in engine ticks, so the quotient is
    per tick and converting to seconds needs the tick rate, which is a separate question and
    varies with game speed. The stored FIELD is still called `w_dps` across the ledgers and
    corpora and renaming it is a migration of its own; this function, and every label it feeds,
    say "per tick" so the misnomer stops spreading.

    Maintainer's ruling, 2026-09-12: *"That cameo formula must always be used even for the
    reference for checking! ... and that same formula should be used everywhere so yeah please
    use that one formula for all the DPS calculation"*.

    It is the engine's own cycle, and both extractors already agreed with it — they simply said
    it differently. `extract_peer_units` computes `damage_pos * burst / (reload + burst_time)`,
    which is this verbatim. The Cameo snapshot computes `w_damage / cycle` with no burst factor,
    which is the SAME NUMBER only because its `w_damage` is already the burst total. Feeding this
    function a burst total would therefore multiply by burst twice and hand the mammoth 800 DPS
    against a true 400 — so damage comes in through `damage_per_shot()`, never off the row.

    Pinned to the authored yaml in `_rate_self_test`:
      mammoth  16,000 x 2 / (72 + 1x8)  = 400    damage/tick
      MLRS      8,000 x 6 / (111 + 5x5) = 352.94 damage/tick
    """
    b = float(burst or 1)
    bt = burst_time(b, 0 if burst_delay is None else burst_delay)
    if bt is None:
        return None                       # cadence unresolved — withheld, never inferred
    cycle = float(reload_ticks or 0) + bt
    if cycle <= 0 or not damage_per_shot_value:
        return None
    return float(damage_per_shot_value) * b / cycle


def rate_of(row, burst_delay):
    """`damage_per_tick` straight off a row, in whichever convention that row uses."""
    return damage_per_tick(damage_per_shot(row), row.get("w_burst") or 1,
                           row.get("w_reload"), burst_delay)


def compose_dps(damage, reload_ticks, burst=1, burst_delay_per_shot=0.0):
    """Deprecated alias kept for callers that already hold a PER-SHOT damage figure.

    ⚠ It forwards to `damage_per_tick()`, so it now MULTIPLIES BY BURST where the old
    implementation did not. That is the correction the maintainer ruled, not a regression: the
    old version was only ever right because every caller happened to hand it Cameo's
    burst-inclusive `w_damage`, which already had the burst folded in.
    """
    return damage_per_tick(damage, burst, reload_ticks, burst_delay_per_shot)


def dps_guard(current, component_targets, dps_target, burst_delay_target=None):
    """Check a set of component targets against the DPS verifier.

    `current` carries `w_damage` / `w_burst` / `w_reload` / `w_dps`; `component_targets` the
    same keys, and a MISSING one falls back to the current value — a stat with no reference is
    not a stat being changed to zero, and zeroing it would make every partial row look extreme.

    Returns a dict, or None when there is not enough to judge. `verdict` is one of:
      ok         composing the components moves DPS by less than EXTREME_RATIO and lands
                 within DISAGREE_RATIO of what the DPS projection independently says.
      extreme    the composed move is itself wilder than EXTREME_RATIO.
      disagrees  the composed move and the DPS projection tell materially different stories —
                 the mammoth class. NOT an error: the components and the aggregate are
                 separate votes, and a human has to choose which to believe.
    """
    def pick(key):
        v = component_targets.get(key)
        return v if v not in (None, 0) else current.get(key)

    cur_dps = current.get("w_dps")
    if cur_dps is None or current.get("weapon_model_eligible") is False:
        return None
    current_burst = float(current.get("w_burst") or 1)
    current_delay = burst_delay_of(current)
    if current_burst > 1 and current_delay is None:
        return None
    # ⛔ `pick("w_damage")` IS PER CYCLE, and `damage_per_tick` multiplies by burst, so the cycle
    # total must be divided back down first or burst is counted twice — 969.86 instead of 485 on
    # the mammoth. Dividing by the TARGET burst is what makes the two spellings identical:
    # `(cycle/burst) * burst / ticks` is `cycle / ticks`.
    tgt_burst = float(pick("w_burst") or 1)
    per_shot = (float(burst_delay_target) if burst_delay_target is not None
                else current_delay)
    if tgt_burst > 1 and per_shot is None:
        return None
    per_shot = per_shot or 0.0
    tgt_cycle_damage = pick("w_damage")
    new = damage_per_tick(
        (tgt_cycle_damage / tgt_burst) if (tgt_cycle_damage and tgt_burst) else None,
        tgt_burst, pick("w_reload"), per_shot)
    if not new or not cur_dps:
        return None
    out = dict(current_dps=float(cur_dps), composed_dps=new, composed_ratio=new / cur_dps,
               burst_delay_per_shot=per_shot, projected_dps=dps_target,
               projected_ratio=None, disagreement=None, verdict="ok")
    if out["composed_ratio"] > EXTREME_RATIO or out["composed_ratio"] < 1 / EXTREME_RATIO:
        out["verdict"] = "extreme"
    if dps_target:
        out["projected_ratio"] = float(dps_target) / cur_dps
        d = new / float(dps_target)
        out["disagreement"] = d
        if (d > DISAGREE_RATIO or d < 1 / DISAGREE_RATIO) and out["verdict"] == "ok":
            out["verdict"] = "disagrees"
    return out


def _guard_self_test():
    """The shipped mammoth and MLRS rows are the regression cases — both were got wrong once."""
    # conventions recovered from the frozen snapshot, not assumed
    assert recover_burst_time(32000, 400, 72) == 8.0, "mammoth burst time"
    assert abs(recover_burst_time(48000, 352.94117647058823, 111) - 25.0) < 1e-6, "MLRS"
    # ⭐ THE ONE FORMULA, against the AUTHORED YAML rather than against the derived snapshot.
    # `td_gdi_mammothtank_120mmdualhv` declares Damage 16000 / Burst 2 / BurstDelays 8 /
    # ReloadDelay 72; `td_gdi_mlrs_227mm` declares 8000 / 6 / 5 / 111. Both are damage per TICK.
    assert damage_per_tick(16000, 2, 72, 8) == 400, "mammoth, from authored yaml"
    assert abs(damage_per_tick(8000, 6, 111, 5) - 352.941) < 0.01, "MLRS, from authored yaml"

    # ⭐ VARYING BURST DELAYS (maintainer, 2026-09-13). A list is summed rather than multiplied,
    # and the constant case is just the list with every entry equal — so the anchors above are
    # unchanged and both spellings of the SAME cadence agree exactly.
    assert burst_time(6, 5) == 25, "a single entry covers all Burst-1 gaps"
    assert burst_time(6, [5]) == 25, "the one-entry array is the same shorthand"
    assert burst_time(6, [5, 5, 5, 5, 5]) == 25, "spelled out in full, identical"
    assert burst_time(4, [10, 2, 3]) == 15, "varying gaps are SUMMED"
    assert burst_time(1, None) == 0.0, "a single shot has no gap to declare"
    # ⚠ NO DECLARED CADENCE FALLS BACK TO THE ENGINE DEFAULT `[5]`, it is not withheld — 36 Cameo
    # weapons with Burst > 1 declare no BurstDelays and really do run at 5 ticks a gap in game.
    assert burst_time(3, None) == 10, "two gaps at the engine default of 5"
    # ⚠ An ILLEGAL length consumes what the engine would consume, for a deterministic diagnostic
    # rather than a withheld one. Unreachable in this tree — 0 weapons carry an illegal array, and
    # one that did would fail the boot gate before reaching a ledger.
    assert burst_time(6, [5, 5]) == 10, "formula's documented diagnostic behaviour"
    assert damage_per_tick(8000, 6, 111, [5, 5, 5, 5, 5]) == damage_per_tick(8000, 6, 111, 5)
    # a front-loaded burst lands the same damage in a shorter cycle, so the rate is higher
    assert damage_per_tick(1000, 4, 100, [1, 1, 1]) > damage_per_tick(1000, 4, 100, [9, 9, 9])
    assert damage_per_tick(1000, 4, 100, [2, 4, 6]) == 1000 * 4 / (100 + 12)
    # ⭐ `w_damage` IS PER CYCLE on every row — that is the referenced coordinate. Per shot is
    # derived from it, and both spellings reach the same rate.
    assert damage_per_cycle(dict(w_damage=32000, w_burst=2)) == 32000, "the mammoth's cycle"
    assert damage_per_shot(dict(w_damage=32000, w_burst=2)) == 16000, "derived back to one shot"
    assert damage_per_shot(dict(w_damage=32000, w_burst=2, w_damage_per_shot=16000)) == 16000
    # a single-shot row is the same number either way
    assert damage_per_cycle(dict(w_damage=4000, w_burst=1)) == 4000
    assert compose_dps(16000, 72, 2, 8) == 400, "the per-shot alias"
    # ⚠ feeding the BURST TOTAL in would double-count burst — the bug this convention prevents
    assert damage_per_tick(32000, 2, 72, 8) == 800, "burst counted twice, as expected"

    # PER SHOT, like every row in the project: authored Damage 16000 with Burst 2.
    mam = dict(w_damage=32000, w_damage_per_shot=16000, w_burst=2, w_reload=72, w_dps=400)
    # components: damage +9.1%, reload -11.1%, burst unanimous at 2 (a DIRECT stat)
    g = dps_guard(mam, dict(w_damage=34915, w_burst=2, w_reload=64), dps_target=695)
    assert abs(g["burst_delay_per_shot"] - 8) < 1e-9, g
    assert abs(g["composed_dps"] - 485) < 1, g["composed_dps"]
    assert abs(g["projected_ratio"] - 1.7375) < 0.01, g["projected_ratio"]
    assert g["verdict"] == "disagrees", g          # ~1.43x apart, the documented gap
    assert abs(1 / g["disagreement"] - 1.43) < 0.02, g["disagreement"]

    # ⛔ A BURST CHANGE ALONE *IS* A LARGE CHANGE, and this expectation was REVERSED on
    # 2026-09-12 when the maintainer ruled the one universal formula. The earlier version of this
    # test asserted the opposite — "a burst change alone must not look extreme" — because under
    # the old burst-total convention `Burst` only lengthened the CYCLE and never multiplied the
    # damage. Under `damage_per_shot * burst / cycle` it does both, and the engine agrees: the
    # MLRS fires 6 rockets of 8,000 over 136 ticks (352.9/tick), and at Burst 2 it fires 2 of
    # them over 116 (137.9/tick). Firing a third as many rockets really is a 61% cut, and a guard
    # that called it "ok" was hiding the largest change in the row.
    mlrs = dict(w_damage=48000, w_damage_per_shot=8000, w_burst=6, w_reload=111,
                w_dps=352.94117647058823)
    m = dps_guard(mlrs, dict(w_damage=16000, w_burst=2, w_reload=111), dps_target=None)
    assert abs(m["burst_delay_per_shot"] - 5) < 1e-6, m
    assert abs(m["composed_dps"] - 137.93) < 0.05, m["composed_dps"]
    assert m["verdict"] == "extreme", m          # 0.39x — correctly loud

    # a component set that agrees with the aggregate passes
    ok = dps_guard(mam, dict(w_damage=32000 * 1.7, w_reload=72), 680)
    assert ok["verdict"] == "ok", ok

    # a genuine 2.5x move through the components alone is flagged
    ex = dps_guard(mam, dict(w_damage=32000 * 2.5, w_reload=72), None)
    assert ex["verdict"] == "extreme", ex

    # a missing component is the CURRENT value, never zero
    same = dps_guard(mam, dict(w_damage=None, w_burst=None, w_reload=None), None)
    assert same["composed_ratio"] == 1.0, same
    return ("reference_targets R1 guard self-test: PASS "
            "(one formula, per shot; mammoth 1.43x gap; MLRS burst cut correctly loud)")


def add_cost_distribution(dist, rows):
    """Fold a `cost` distribution into `dist` in place.

    ⛔ `reference_distribution.ALL_STATS` is CHASSIS + WEAPON + ARMOR and deliberately has no
    `cost` — the module is the CHASSIS layer and never priced anything. Asking it for a cost
    target therefore returns nothing, silently, for every actor: an empty column that reads as
    "no reference data" when the data is right there in every row. Price is a first-class
    reference stat here, so the aggregate is built the same way for the same populations.
    """
    by_source = collections.defaultdict(list)
    for r in rows:
        by_source[r["source"]].append(r)
    for source, items in by_source.items():
        pops = {"overall": [r for r in items if r["type"] in rd.COMBAT_TYPES]}
        for t in rd.POPULATIONS:
            pops[t] = [r for r in items if r["type"] == t]
        for pop, members in pops.items():
            agg = rd.aggregates([m.get("cost") for m in members
                                 if m.get("cost") and rd.eligible(m, "cost")])
            if agg:
                dist.setdefault(source, {}).setdefault(pop, {})["cost"] = agg


def peer_index(peers):
    idx = collections.defaultdict(list)
    for p in peers:
        idx[(p["source"], (p.get("name") or "").strip())].append(p)
    return idx


def attach(assignment, idx):
    """{actor: [peer row, ...]} — the assignment stores a NAME; recover the row it meant.

    ⚠ Two rows in one source can share a name (a variant), so the hp/cost the assignment
    recorded disambiguates; a name-only hit is the fallback rather than a dropped pair.
    """
    out = {}
    for actor, srcs in assignment.items():
        rows = []
        for src, rec in srcs.items():
            hits = idx.get((src, (rec.get("name") or "").strip()))
            if not hits:
                continue
            # The ID is the only reliable key — see the note in assign_references. hp/cost is the
            # fallback for assignments written before the id was recorded.
            best = None
            if rec.get("id"):
                best = next((h for h in hits if h.get("id") == rec["id"]), None)
            if best is None:
                best = next((h for h in hits if h.get("hp") == rec.get("hp")
                             and h.get("cost") == rec.get("cost")), hits[0])
            rows.append(best)
        if rows:
            out[actor] = rows
    return out


# ⭐ FAMILY MEMBERS THAT DO NOT SHARE THE ID STEM (maintainer, 2026-09-07). The family rule finds
# `4TNK.ATOMIC` and `4TNK.ERAD` from `4TNK` because Combined Arms suffixes the variant onto the
# base id. It cannot find the Apocalypse or the Overlord, which are the SAME tier of Soviet super-
# heavy under their own names, and the maintainer wants them counted with the rest. Named rows
# only — this is a list of units, not a pattern anyone can widen by accident.
FAMILY_EXTRA = {
    ("ra1_soviets_siegemammothtank", "Combined Arms"): ("APOC", "OVLD"),
    # GDI's super-heavy tier is split across two chassis names: the Mammoth line and the Titan
    # walkers. Both are 110,000 HP / 2,000cr in Combined Arms and both belong with the Mk III.
    # ⚠ `allows("td_gdi", TITN)` currently returns FALSE — CA's broad faction tagging denies GDI
    # its own walker — so these rows are unreachable through routing and can only arrive here.
    # That is a symptom, not a fix: EMBER owns the CA over-tagging, and when it is corrected these
    # two entries should be re-checked to see whether the family rule finds them unaided.
    ("td_gdi_mammothtankmkiii", "Combined Arms"): ("TITN", "TITN.RAIL"),
}


def expand_families(attached, peers):
    """Replace each assigned row with its whole variant family from that source."""
    by_source = collections.defaultdict(list)
    for p in peers:
        by_source[p["source"]].append(p)
    out = {}
    for actor, rows in attached.items():
        faction = fr.faction_of(actor)
        grown, seen = [], set()
        for r in rows:
            for f in family_rows(r, by_source, faction):
                key = (f["source"], f.get("id"), f.get("name"))
                if key in seen:
                    continue
                seen.add(key)
                grown.append(f)
        for (a_id, src), ids in FAMILY_EXTRA.items():
            if a_id != actor:
                continue
            for extra in by_source.get(src, ()):
                if (extra.get("id") or "").upper() not in ids:
                    continue
                key = (extra["source"], extra.get("id"), extra.get("name"))
                if key not in seen:
                    seen.add(key)
                    grown.append(extra)
        out[actor] = grown
    return out


def family_rows(assigned, peers_by_source, faction):
    """Every VARIANT of the assigned reference, from that same source — one voice between them.

    ⛔ MAINTAINER 2026-09-07: *"if more than one variant exists just use all of them as reference
    since they would otherwise not be mapped... but weight it still only the mean from CA as one
    voice compared to our existing Cameo one."*

    Combined Arms routes FOUR mammoths to GDI — `HTNK`, `HTNK.Hover`, `HTNK.Ion`, `HTNK.Drone` —
    and clause 2 lets an actor take only one per source, so three of them describe nothing and a
    Cameo add-on above the Mammoth has almost no evidence to sit on. Taking all four and averaging
    them inside the source keeps R4 intact: Combined Arms still casts ONE vote, it is just a better
    informed one.

    The grouping signal is the mod's own naming, not a similarity guess: these mods suffix a
    variant onto the base actor id after a dot, so `HTNK.Ion` belongs to `HTNK`. A row is admitted
    only if routing already allows this faction to see it.
    """
    base = (assigned.get("id") or "").split(".")[0]
    if not base:
        return [assigned]
    out = [r for r in peers_by_source.get(assigned["source"], ())
           if (r.get("id") or "").split(".")[0] == base and fr.allows(faction, r)]
    # ⚠ DTA ships AI duplicates of its own units (`AIHTNK`, `AIHTNK2`) with identical stats.
    # They are not variants and must not weight the source's mean toward one design twice.
    seen, uniq = set(), []
    for r in out:
        key = (r.get("name"), r.get("hp"), r.get("cost"), r.get("w_damage"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    return uniq or [assigned]


FROZEN_CAMEO_SHA256 = '726ada6afec708f8c6e9798ecbfb2758c842195f66755c2d5e683432c4a86f95'


class FrozenCameoDistribution(dict):
    """Projection ruler and self-votes captured together; never live feedback."""
    def __init__(self, distribution, rows):
        super().__init__(distribution)
        self.cameo_votes = {row['id']: row for row in rows}


# ⛔ `_withhold_unproven_frozen_weapon_model` WAS HERE AND IS DELETED. MEASURED 2026-09-13.
#
# PR #369 stamped `weapon_model_eligible: False` on EVERY row of the frozen Cameo snapshot — both
# the ordinary and the hero context — and `target_for` then refuses every `WEAPON_STATS` projection
# whose Cameo row is ineligible. Since every actor's `cameo_row` comes from that snapshot, the
# stamp is universal. Rebuilt the map on the merge to measure it rather than argue about it:
#
#     live weapon targets ("would change")   266 -> 0
#     WITHHELD                                38 -> 354
#     "No usable source projection"          437 -> 910
#     EXTREME / DISAGREES                  68/42 -> 0/0
#
# ⚠ AND IT LOOKS GREEN, which is the dangerous part: the report still builds, and the headline
# counts (73 originals, 116 expanded, 305 references) are IDENTICAL, because references and chassis
# stats are untouched. Only the weapon numbers the map exists to show are gone — and the verifier
# columns fall silent too, so the guard rails report no problems by having nothing left to guard.
#
# This is the SECOND time this exact shape has arrived: `41d0dad57` withheld on the premise that
# "the source corpus currently lacks that compatible evidence" and printed WITHHELD on every row of
# the verifier column. Both changes had a genuinely better half, and both were reconciled, not
# reverted — #369's `dps_guard` fail-closed on an unrecoverable burst delay is KEPT below.
#
# ⭐ THE INTENT IS RIGHT AND THE INSTRUMENT IS WRONG. What #369 wanted to withhold is "uncaptured
# armament structure" — a cannon+missile tank whose single projected number mixes two weapons,
# which the maintainer raised the same day: *"Those two weapons are so different they should not be
# mixed ... this should be true for any dual or multi weapon units."* That is a real defect, it
# affects the multi-armament actors ONLY, and the fix the maintainer asked for is to MAP THEM PER
# WEAPON — not to blank every single-weapon unit alongside them. A blanket stamp cannot express
# "this actor's armaments were not separated"; per-armament pairing can, and that is the live task.


def cameo_context():
    import hashlib
    path = ROOT / 'docs/reference/cameo_baselines/pre_reference_20260910.json'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_CAMEO_SHA256:
        raise ValueError('permanent Cameo reference snapshot changed')
    document = json.loads(raw)
    if document.get('schema') != 1:
        raise ValueError('unsupported Cameo reference snapshot')
    # ⛔ NORMALISED TO PER SHOT AFTER the hash check, never before. The pin guarantees the FILE
    # is unchanged; the formula needs the ROWS in the one convention the whole project uses, or
    # every damage target comes back in burst-total units and the map draws an arrow between two
    # different quantities. The bytes are untouched and still hash.
    # The snapshot already stores the burst TOTAL, which IS the referenced coordinate, so it is
    # normalised only to attach the derived per-shot figure. See `reference_distribution.to_per_cycle`.
    rows = _recover_weapon_model_eligibility(rd.to_per_cycle(document['rows']))
    distribution = rd.build_distributions(rows)
    add_cost_distribution(distribution, rows)
    return FrozenCameoDistribution(distribution['Cameo'], rows)


def _recover_weapon_model_eligibility(rows):
    """Carry each frozen row's MULTI-ARMAMENT verdict over from the live ledger, by id.

    ⛔ WITHOUT THIS THE FROZEN POPULATION SILENTLY BYPASSES THE MULTI-ARMAMENT GUARD (Astra,
    PR #372). `armament_profile` sets `weapon_model_eligible` from `len(live) == 1`, so an actor
    whose cannon and missile would be averaged into one number abstains — but the pinned snapshot
    predates the flag and carries it on **none** of its 893 rows. Every check reads
    `... is False`, so "absent" meant "eligible", and all 893 were projected as if single-weapon.

    ⭐ IT IS FULLY RECOVERABLE, which is why this is a recovery and not a disclaimer: measured
    2026-09-13, **893 of 893** frozen ids have a live counterpart — 796 eligible, 97 genuinely
    multi-armament. Nothing has to be marked provisional; the verdict simply has to be fetched.

    ⚠ AFTER THE SHA256 CHECK, NEVER BEFORE — the same rule `to_per_cycle` follows. The pin
    guarantees the FILE is unchanged; this attaches a derived judgement to the in-memory rows and
    touches no bytes. A row with no live counterpart keeps no flag and stays eligible, which is the
    pre-existing behaviour rather than a new silent withholding.
    """
    try:
        live = {r["id"]: r for r in rd.cameo_rows()}
    except Exception:                      # a broken ledger must not take the frozen pin with it
        return rows
    out = []
    for row in rows:
        counterpart = live.get(row.get("id"))
        if counterpart is not None and "weapon_model_eligible" in counterpart:
            row = dict(row, weapon_model_eligible=counterpart["weapon_model_eligible"])
        out.append(row)
    return out


FROZEN_HERO_SHA256 = '101a934792713dd6ccf5fbeb99629db0379af7b1f9a51d52d02a010795e5365c'


def hero_cameo_context():
    """Separate hero population recovered from the same immutable ledger inputs."""
    import hashlib
    path = ROOT / 'docs/reference/cameo_baselines/pre_reference_heroes_20260910.json'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_HERO_SHA256:
        raise ValueError('permanent hero reference snapshot changed')
    doc = json.loads(raw)
    if doc['parent_snapshot_sha256'] != FROZEN_CAMEO_SHA256:
        raise ValueError('hero reference does not share the frozen baseline')
    rows = _recover_weapon_model_eligibility(rd.to_per_cycle(doc['rows']))
    dist = rd.build_distributions(rows)
    add_cost_distribution(dist, rows)
    return FrozenCameoDistribution(dist['Cameo'], rows)


def _direct_target(rows, vote_row, stat):
    """(peers_only, with_cameo, n_sources) for a DISCRETE count -- see DIRECT_STATS.

    No distribution, no projection: one vote per source (median of that source's eligible
    rows), then the median of the source votes. Eligibility is the SAME `rd.eligible` gate the
    projected path uses, so an upgraded variant or an evidence-withheld row abstains here too.

    `with_cameo` deliberately does NOT fold Cameo's own value in. On a continuous stat the
    self-vote damps a projection; on a count it would just drag a unanimous source answer
    toward the status quo and hide the very disagreement this stat is shown to reveal.
    """
    per = collections.defaultdict(list)
    for r in rows:
        x = r.get(stat)
        if not x or x <= 0 or not rd.eligible(r, stat):
            continue
        per[r["source"]].append(float(x))
    if not per:
        return None, None, 0
    votes = [statistics.median(v) for v in per.values()]
    value = statistics.median(votes)
    return value, value, len(per)


def target_for(rows, cameo_row, stat, dist, cdist):
    """(peers_only, with_cameo, n_sources) on one stat, or (None, None, 0).

    ⭐ POOLED PER SOURCE FIRST. Every source casts exactly ONE vote however many of its rows are
    in play, so a mod that happens to ship four variants of a unit cannot outvote one that ships
    a single unit. Without this, expanding to variant families would quietly re-weight R4.

    ⛔ AND EVERY VOTE IS GATED BY `rd.eligible` (review, 2026-09-09). The old test was only
    `if not x or x <= 0` — true for a withheld w_dps row's raw `w_range`/`w_damage`, which then
    voted against the other rows' aggregates even though the weapon's DPS fold never became a
    usable estimate. `rd.eligible` is the SAME gate `build_distributions` applies, so a row
    that abstains from a distribution cannot re-enter through `target_for`: for `w_dps` AND
    every stat that REQUIRES w_dps (`w_range`/`w_damage`/`w_burst`/`w_reload`, and the
    `dps_vs_*`), an evidence-withheld row contributes no coordinate, no peer vote and no
    source count. The optional Cameo self-vote is gated the same way, so an ineligible Cameo
    stat cannot outvote anything either. hp/speed/cost have their own eligibility and are
    unaffected. `peers_only` keeps its meaning: the peers' coordinates alone.
    """
    frozen = getattr(cdist, 'cameo_votes', None)
    vote_row = frozen.get(cameo_row.get('id')) if frozen is not None else cameo_row
    projection_row = vote_row if vote_row is not None else cameo_row
    if stat in LAW_GOVERNED_STATS:
        return None, None, 0
    if stat in rd.WEAPON_STATS and (
            cameo_row.get("weapon_model_eligible") is False
            or vote_row is None
            or vote_row.get("weapon_model_eligible") is False):
        return None, None, 0
    if stat in DIRECT_STATS:
        return _direct_target(rows, vote_row, stat)
    per_source = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        x = r.get(stat)
        if not x or x <= 0:
            continue
        if not rd.eligible(r, stat):
            continue
        for pop in ("overall", r["type"]):
            agg = dist.get(r["source"], {}).get(pop, {}).get(stat)
            for k, v in rd.coordinates(float(x), agg).items():
                per_source[r["source"]][(pop, k)].append(v)
    pooled, used = collections.defaultdict(list), set()
    for source, coords in per_source.items():
        used.add(source)
        for key, vals in coords.items():
            # p_rng is a bounded position and averages arithmetically; the rest are ratios.
            pooled[key].append(statistics.fmean(vals) if key[1] == "p_rng" else rd.gm(vals))
    if not pooled:
        return None, None, 0
    # p_rng is a bounded [0,1] position and can legitimately be 0, where a geometric mean is
    # undefined; every other coordinate is a ratio and pools geometrically.
    synth = {pk: (statistics.fmean(v) if pk[1] == "p_rng" else rd.gm(v)) for pk, v in pooled.items()}
    cands = []
    for pop in ("overall", projection_row["type"]):
        coord = {k: v for (p_, k), v in synth.items() if p_ == pop}
        cands += list(rd.project(coord, cdist.get(pop, {}).get(stat)).values())
    cands = [c for c in cands if c and c > 0]
    if not cands:
        return None, None, 0
    peers_only = rd.gm(cands)
    now = vote_row.get(stat) if vote_row is not None else None
    now = now if (now and now > 0 and rd.eligible(vote_row, stat)) else None
    with_cameo = rd.gm([peers_only] * len(used) + [now]) if now else peers_only
    return peers_only, with_cameo, len(used)


def armament_target(votes, dist, cdist, cameo_type, stat="w_damage", cameo_vote=None):
    """One component target for ONE armament, from only the peer WEAPONS paired to it.

    ⭐ THIS IS `target_for` WITH THE FOLD TAKEN OUT, and deliberately not a second model. Same
    coordinates, same per-source pooling, same projection onto the same frozen ruler — the only
    difference is WHAT gets projected: the damage of the peer weapon that was paired to this
    armament, instead of the actor's single folded `w_damage`.

    ⛔ IT EXISTS BECAUSE THE FOLD HAD NO HONEST ANSWER FOR A TWO-WEAPON UNIT. PR #372 stamped
    `weapon_model_eligible: False` on every multi-armament actor and `target_for` then refused the
    projection, which was the right refusal — averaging a 120mm cannon with an anti-air missile
    produces a number describing neither gun. But it left 38 actors in the map with a blank damage
    cell, including the two the maintainer went looking for:

        "td gdi battle tank and mammoth tank are now withheld"  (maintainer, 2026-09-13)

    37 of those 38 already had the evidence to answer properly — 83 armament-to-weapon pairs in
    `armament_pairing.json`, built from the maintainer's own ruling that a reference which does not
    carry a weapon in that role does not vote on it. The Mammoth has six exact pairs across three
    sources, cannon to cannon and missile to missile. Nothing consumed them until now.

    `votes` is [(peer_row, component_value)], at most one entry per source, already restricted to
    the weapons paired to this one armament. Continuous components use the same within-source
    coordinate projection as `target_for`. Burst is a count and keeps `_direct_target`'s law:
    median within each source, then median across source votes, with no coordinate projection.

    `cameo_vote` is the immutable Cameo self-vote for an unambiguous one-armament baseline. It is
    folded in once after the peer sources, matching R4's equal source weights. Multi-armament
    callers must omit it: their frozen actor-level weapon row is exactly the fold this function
    exists to avoid.

    ⚠ THE RULER STAYS THE ACTOR-LEVEL ONE. `cdist` is a distribution of whole actors' weapon
    damage, and an armament is projected against it as if it were a unit's gun. That is the
    approximation this function makes and it is worth stating plainly: it is right for the common
    case where one armament carries most of an actor's output, and it is generous to a small
    secondary weapon. It is still strictly better than the fold, which compared a cannon against a
    missile's reference. A per-ARMAMENT ruler is the honest end state and needs the peer corpora
    re-expressed per weapon first; that is not this change.

    Returns (target, sources_used) — (None, 0) when no paired weapon can be normalised, which is
    an abstention and must be rendered as one, never as a zero.
    """
    if stat in DIRECT_STATS:
        per_source = collections.defaultdict(list)
        for row, x in votes:
            if row and x and x > 0:
                per_source[row["source"]].append(float(x))
        if not per_source:
            return None, 0
        source_votes = [statistics.median(values) for values in per_source.values()]
        return statistics.median(source_votes), len(per_source)

    per_source = collections.defaultdict(lambda: collections.defaultdict(list))
    for row, x in votes:
        if not x or x <= 0 or not row:
            continue
        for pop in ("overall", row.get("type")):
            agg = dist.get(row.get("source"), {}).get(pop, {}).get(stat)
            for k, v in rd.coordinates(float(x), agg).items():
                per_source[row["source"]][(pop, k)].append(v)
    if not per_source:
        return None, 0
    pooled, used = collections.defaultdict(list), set()
    for source, coords in per_source.items():
        used.add(source)
        for key, vals in coords.items():
            pooled[key].append(statistics.fmean(vals) if key[1] == "p_rng" else rd.gm(vals))
    synth = {pk: (statistics.fmean(v) if pk[1] == "p_rng" else rd.gm(v))
             for pk, v in pooled.items()}
    cands = []
    for pop in ("overall", cameo_type):
        coord = {k: v for (p_, k), v in synth.items() if p_ == pop}
        cands += list(rd.project(coord, cdist.get(pop, {}).get(stat)).values())
    cands = [c for c in cands if c and c > 0]
    if not cands:
        return None, 0
    peers_only = rd.gm(cands)
    with_cameo = (rd.gm([peers_only] * len(used) + [float(cameo_vote)])
                   if cameo_vote is not None and cameo_vote > 0 else peers_only)
    return with_cameo, len(used)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--faction", nargs="+", required=True)
    ap.add_argument("--md", help="write the table to this path")
    args = ap.parse_args()

    peers = rd.peer_rows()
    cameo = rd.cameo_rows()
    dist = rd.build_distributions(peers)
    add_cost_distribution(dist, peers)
    cdist = cameo_context()
    assignment = json.loads(ASSIGN.read_text(encoding="utf-8"))["assignment"]
    attached = expand_families(attach(assignment, peer_index(peers)), peers)
    crows = {c["id"]: c for c in cameo}

    out = ["# Reference targets — R4 synthesis (references + Cameo, one vote each)", ""]
    for fac in args.faction:
        members = sorted(a for a in crows if a.startswith(fac + "_"))
        out += [f"## {fac} — {len(members)} actors", "",
                "| actor | src | hp now | hp -> | speed now | speed -> | range now | range -> "
                "| dps now | dps -> | cost now | cost -> |",
                "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
        for a in members:
            rows = attached.get(a)
            c = crows[a]
            if not rows:
                out.append(f"| `{a}` | **0** | " + " | ".join(
                    [f"{c.get(s) or 0:,.0f}" + " | —" for s in STATS]) + " |")
                continue
            cells, nsrc = [], 0
            for s in STATS:
                _, t, n = target_for(rows, c, s, dist, cdist)
                nsrc = max(nsrc, n)
                now = c.get(s)
                cells.append(f"{now:,.0f}" if now else "—")
                cells.append(f"**{t:,.0f}**" if t else "—")
            out.append(f"| `{a}` | {nsrc} | " + " | ".join(cells) + " |")
        out.append("")

    text = "\n".join(out)
    if args.md:
        p = ROOT / args.md
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text.rstrip() + "\n", encoding="utf-8")
        print(f"wrote {args.md}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
