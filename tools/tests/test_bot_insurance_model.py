"""THE C# CANNOT BE COMPILED HERE, SO THE STATE MACHINE IS PINNED IN PYTHON INSTEAD.

⛔ WHAT THIS FILE IS DEFENDING. `OpenRA.Mods.Cameo/Traits/DynamicBotInsurance.cs` replaces a
ten-rung yaml ladder with one trait holding a small state machine: a threshold that rises, freezes,
and re-arms, with a delay derived from a rolling average. A cloud container has no `engine/` and no
dotnet (CLAUDE.md rule 7), so that C# is unverified AS CODE until someone builds it. The state
machine, though, is exactly the part with non-obvious failure modes -- it can oscillate, stick at
zero, pay a rich player, or never fire at all -- and all of that IS verifiable here.

`tools/balance/bot_insurance_model.py` mirrors `Tick` line for line. These tests pin the behaviour
that mirror must have. ⚠ The two files must change together; `test_the_model_matches_the_csharp_defaults`
is the guard that notices when they do not, by parsing the field defaults straight out of the .cs.
"""

from __future__ import annotations

import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import bot_insurance_model as m  # noqa: E402

CS = ROOT / "OpenRA.Mods.Cameo" / "Traits" / "DynamicBotInsurance.cs"


def csharp_source() -> str:
    """The committed trait and the model must change together."""
    assert CS.exists(), f"{CS} is missing"
    return CS.read_text(encoding="utf-8")


# ------------------------------------------------------- drift guard (the important one)

def _csharp_defaults() -> dict[str, int]:
    src = csharp_source()
    return {n: int(v) for n, v in
            re.findall(r"public readonly int (\w+) = (-?\d+);", src)}


def _csharp_bool_defaults() -> dict[str, bool]:
    src = csharp_source()
    return {n: v == "true" for n, v in
            re.findall(r"public readonly bool (\w+) = (true|false);", src)}


def test_the_model_matches_the_csharp_defaults():
    """If this fails, the model and the trait have drifted and every test below is fiction."""
    cs = _csharp_defaults()
    assert cs["AverageWindow"] == m.AVERAGE_WINDOW
    assert cs["MaxThreshold"] == m.MAX_THRESHOLD
    assert cs["MinThreshold"] == m.MIN_THRESHOLD
    assert (cs["MinThresholdRatePerTick"], cs["MaxThresholdRatePerTick"]) == (m.MIN_RATE, m.MAX_RATE)
    assert (cs["MinDelayDivisor"], cs["MaxDelayDivisor"]) == (m.MIN_DIVISOR, m.MAX_DIVISOR)
    assert (cs["MinDelayTicks"], cs["MaxDelayTicks"]) == (m.MIN_DELAY, m.MAX_DELAY)
    assert (cs["MinCashPerTick"], cs["MaxCashPerTick"]) == (m.MIN_CASH, m.MAX_CASH)
    assert (cs["MinPurifierModifier"], cs["MaxPurifierModifier"]) == (m.MIN_PURIFIER, m.MAX_PURIFIER)
    # the net-worth layer
    assert cs["ArmyValueWeight"] == m.ARMY_VALUE_WEIGHT
    assert cs["MinSelfRatio"] == m.MIN_SELF_RATIO
    assert (cs["ParRatioMin"], cs["ParRatioMax"]) == (m.PAR_RATIO_MIN, m.PAR_RATIO_MAX)
    assert cs["MinWorthFactor"] == m.MIN_WORTH_FACTOR
    assert cs["ParShapeStep"] == m.PAR_SHAPE_STEP
    assert cs["ParBaseWorth"] == m.PAR_BASE_WORTH
    assert cs["ParAsymptotePerRank"] == m.PAR_ASYMPTOTE_PER_RANK
    assert (cs["ParMidpointEasiest"], cs["ParMidpointHardest"]) == (
        m.PAR_MIDPOINT_EASIEST, m.PAR_MIDPOINT_HARDEST)
    assert _csharp_bool_defaults()["UseParCurve"] is m.USE_PAR_CURVE


def test_the_unmeasured_par_curve_is_disabled_by_default():
    assert m.Insurance("medium").use_par_curve is False


def test_the_par_curve_table_matches_the_csharp_default():
    """The shape is a yaml-tunable ARRAY; model and trait must ship the same one."""
    src = csharp_source()
    block = re.search(r"public readonly int\[\] ParShape =\s*\{([^}]*)\}", src)
    assert block, "the ParShape field moved or changed shape"
    assert [int(v) for v in re.findall(r"-?\d+", block.group(1))] == m.PAR_SHAPE


def test_the_csharp_uses_no_floating_point_in_the_curve():
    """⛔ Desync guard. Math.Exp/Sqrt are not bit-identical across platforms; this feeds [Sync]."""
    # ⚠ Strip comments AND [Desc] string literals first. The trait EXPLAINS why Math.Exp is
    # banned, in both a comment and a Desc line, and a naive substring search flags its own
    # documentation — a guard that fails on the thing it is documenting gets switched off.
    def is_prose(line: str) -> bool:
        s = line.strip()
        return s.startswith(("//", "///", "*", "/*", '"', "[Desc("))

    code = "\n".join(line for line in csharp_source().splitlines() if not is_prose(line))
    for banned in ("Math.Exp", "Math.Sqrt", "Math.Pow", "double ", "float "):
        assert banned not in code, f"{banned} in a synced code path — a desync waiting to happen"
    assert "IntSqrt" in code


def test_the_csharp_difficulty_list_matches_the_model():
    src = csharp_source()
    block = re.search(r"public readonly string\[\] Difficulties =\s*\{(.*?)\};", src, re.S)
    assert block, "the Difficulties field moved or changed shape"
    assert re.findall(r'"(\w+)"', block.group(1)) == m.DIFFICULTIES


def test_the_bar_tracks_both_ways_and_the_csharp_says_so():
    """The bar is a slew-limited tracker. Both earlier designs were rejected; keep it deliberate."""
    src = csharp_source()
    assert "Math.Clamp(target - threshold, -ratePerTick, ratePerTick)" in src
    assert "IT IS NOT A ONE-WAY RAMP AND NOT A FALLING BAR" in src
    assert "liquidity < threshold" in src, "the trigger must be STRICT"


def test_the_csharp_uses_total_liquid_funds_and_bounds_every_payout():
    """Stored resources are spendable, and purifier bursts cannot jump over the cap."""
    src = csharp_source()
    assert "var liquidity = playerResources.GetCashAndResources();" in src
    assert "Record(liquidity);" in src
    assert "if (ShouldStartDelay(liquidity, threshold))" in src
    assert "if (ShouldStopPaying(liquidity, info.MaxThreshold))" in src
    assert "DepthPermille(liquidity)" in src
    assert "CashPayout(accumulator, cashPerTick, depth, liquidity, info.MaxThreshold)" in src
    assert "PurifierPayout(amtAwaitingPurification, purifierModifier" in src


def test_the_csharp_banks_purifier_deliveries_only_while_paying_and_hashes_hidden_state():
    """The model cannot exercise engine callbacks, so pin their state boundaries in source."""
    src = csharp_source()
    assert "rank >= 0 && phase == Phase.Paying" in src
    assert "[VerifySync]\n\t\tint stateHash;" in src
    for state in ("historyIndex", "historyCount", "historySum", "historyHash", "worthFactor", "(int)phase"):
        assert state in src


# ------------------------------------------------------- rank scaling

def test_rank_endpoints_are_exactly_the_configured_min_and_max():
    n = len(m.DIFFICULTIES)
    assert m.by_rank(1, 10, 0, n) == 1
    assert m.by_rank(1, 10, n - 1, n) == 10
    assert m.by_rank(10, 100, 0, n) == 10
    assert m.by_rank(10, 100, n - 1, n) == 100


def test_the_maintainers_worked_example():
    """"if the average was like 1500 in the last minute then make it 150 ticks" -- easiest."""
    ins = m.Insurance("easiest")
    for _ in range(m.AVERAGE_WINDOW):
        ins.history.append(1500)
    assert ins.average == 1500
    assert ins.average // ins.delay_divisor == 150


def test_the_hardest_difficulty_waits_ten_times_less_than_the_easiest():
    easiest, hardest = m.Insurance("easiest"), m.Insurance("cameogod")
    assert hardest.delay_divisor == 10 * easiest.delay_divisor
    assert hardest.rate_per_tick == 10 * easiest.rate_per_tick
    assert hardest.cash_per_tick == 10 * easiest.cash_per_tick


# ------------------------------------------------------- who is insured at all

@pytest.mark.parametrize("who", ["campaign", "", "human", "nonsense"])
def test_a_player_outside_the_difficulty_list_is_never_insured(who):
    ins = m.Insurance(who)
    assert ins.rank == -1
    assert sum(ins.tick(0) for _ in range(5000)) == 0, (
        "a non-bot owner must never receive a credit -- one rung is one oil derrick, and the "
        "human derrick cap is 3")


@pytest.mark.parametrize("difficulty", m.DIFFICULTIES)
def test_a_rich_bot_is_never_insured(difficulty):
    r = m.simulate(difficulty, cash=m.MAX_THRESHOLD + 5000, ticks=5000)
    assert r["first_payout_tick"] is None and r["total_paid"] == 0


@pytest.mark.parametrize("difficulty", m.DIFFICULTIES)
def test_a_bankrupt_bot_is_always_rescued(difficulty):
    """The whole purpose: a bot at zero must never be left stuck at zero."""
    r = m.simulate(difficulty, cash=0, ticks=5000)
    assert r["first_payout_tick"] is not None
    assert r["first_payout_tick"] <= m.MIN_DELAY + 5
    assert r["total_paid"] > 0


# ------------------------------------------------------- the laws

def test_harder_bots_are_rescued_sooner_after_a_crash():
    """The property the original falling-bar spec did NOT have.

    Measured on a CRASH -- a healthy average, then cash collapses -- because that is what
    insurance is for. A bot merely HOLDING a small stable pile is deliberately not insured
    (see test_a_stable_bot_is_not_subsidised), so it is the wrong scenario to measure speed on.
    """
    firsts = []
    for d in m.DIFFICULTIES:
        ins = m.Insurance(d)
        for _ in range(m.AVERAGE_WINDOW * 2):
            ins.tick(8000)
        firsts.append(next((t for t in range(20000) if ins.tick(500)), None))

    assert all(f is not None for f in firsts), firsts
    assert firsts == sorted(firsts, reverse=True), firsts
    assert firsts[0] >= 8 * firsts[-1], (
        f"easiest {firsts[0]} vs hardest {firsts[-1]} — the difficulty spread has collapsed")


@pytest.mark.parametrize("cash", [2000, 5000, 9000, 9999, 12000])
def test_a_stable_bot_is_not_subsidised(cash):
    """⛔ The reason the trigger is `<` and not `<=`.

    With `<=` the bar converges to the average, the average converges to a stable cash pile, and
    every bot under the cap eventually insures itself — turning an emergency measure into baseline
    income, which is the snowball this rewrite exists to remove.
    """
    ins = m.Insurance("cameogod")
    assert not any(ins.tick(cash) for _ in range(10000))


def test_a_bot_below_the_poverty_line_IS_subsidised_even_when_stable():
    """The other side of the same law: MinThreshold is an absolute floor, not a relative one."""
    ins = m.Insurance("medium")
    assert any(ins.tick(m.MIN_THRESHOLD - 500) for _ in range(10000))


def test_a_near_cap_bot_with_low_worth_factor_recovers_and_rearms():
    """A one-credit gap must not strand Paying after worth scaling truncates depth."""
    ins = m.Insurance("cameogod", use_par_curve=False)
    ins.peak_worth = m.MAX_THRESHOLD
    ins.phase = "paying"
    cash = m.MAX_THRESHOLD - 1

    for _ in range(500):
        cash += ins.tick(cash)
        if ins.phase == "arming":
            break

    assert cash == m.MAX_THRESHOLD
    assert ins.phase == "arming"


@pytest.mark.parametrize("difficulty", ["easiest", "medium", "cameogod"])
def test_a_zero_floor_strands_a_bankrupt_bot(difficulty):
    """⛔ Why MinThreshold must be > 0 — the answer to "0 for the lowest boundary?".

    The bar tracks the rolling average. A bot stuck at zero drives its own average to zero, so
    with a floor of 0 the bar follows it to 0 and `cash < 0` can never be satisfied. The bot is
    stranded permanently, in the exact situation the trait exists to prevent.
    """
    stranded = m.Insurance(difficulty, min_threshold=0)
    assert not any(stranded.tick(0) for _ in range(20000)), "a zero floor must strand — it does not"

    rescued = m.Insurance(difficulty, min_threshold=m.MIN_THRESHOLD)
    assert any(rescued.tick(0) for _ in range(20000))


def test_raising_the_cap_subsidises_bots_that_are_not_in_trouble():
    """Why the ceiling is 10000 and not "10k or higher" — the measured cost of raising it.

    The case is a WEALTHY bot dipping, not a stable one: a bot running a 25000 economy that falls
    to 18000. At cap 10000 the bar is pinned at 10000 and it is correctly left alone — 18000 is
    not distress. At cap 20000 the bar follows the average up and insures it, which is a subsidy
    to the richest player on the map.
    """
    def dips_to(cap, rich, now):
        ins = m.Insurance("medium", max_threshold=cap)
        # ⚠ Prime long enough for the bar to actually CONVERGE on the cap. At 4/tick it needs
        # 5000 ticks to climb to 20000; a shorter prime measures the ramp, not the cap.
        for _ in range(6000):
            ins.tick(rich)
        return any(ins.tick(now) for _ in range(8000))

    for crash_to in (12000, 15000, 18000):
        assert not dips_to(m.MAX_THRESHOLD, 25000, crash_to), (
            f"{crash_to} must not be insured at cap {m.MAX_THRESHOLD}")
        assert dips_to(20000, 25000, crash_to), (
            f"at cap 20000 a bot with {crash_to} credits IS insured — a subsidy, not insurance")


def test_a_payout_never_exceeds_the_gap_to_the_cap():
    """Self-limiting by construction: difficulty buys SPEED, not a bigger total."""
    for d in m.DIFFICULTIES:
        r = m.simulate(d, cash=0, ticks=40000)
        assert r["total_paid"] <= m.MAX_THRESHOLD + 50, (d, r)


def test_no_credit_is_ever_granted_at_or_above_the_start_threshold():
    ins = m.Insurance("cameogod")
    for _ in range(5000):
        assert ins.tick(m.MAX_THRESHOLD) == 0


def test_paying_does_not_oscillate():
    """Exiting at the frozen bar instead of StartThreshold makes a payout oscillator. It must not."""
    ins = m.Insurance("medium")
    cash, transitions, last = 1500, 0, ins.phase
    for _ in range(20000):
        cash += ins.tick(max(0, cash))
        if ins.phase != last:
            transitions += 1
            last = ins.phase
    assert transitions < 30, f"{transitions} phase flips is churn, not a state machine"


def test_recovering_during_the_delay_cancels_the_payout():
    # A CRASH, not a stable small pile: a stable bot is deliberately never insured, so it would
    # never reach the delay to have it cancelled.
    ins = m.Insurance("cameogod")
    for _ in range(m.AVERAGE_WINDOW):
        ins.tick(8000)
    for _ in range(200):
        ins.tick(500)
    assert ins.phase in ("delaying", "paying")

    # One tick above the frozen bar is enough to cancel. The bar is then UNFROZEN, not reset:
    # it resumes tracking the average, which is the whole point of making it a tracker.
    before = ins.threshold
    assert ins.tick(m.MAX_THRESHOLD + 1) == 0
    assert ins.phase == "arming"
    for _ in range(50):
        ins.tick(m.MAX_THRESHOLD + 1)
    assert ins.threshold != before, "the bar stayed frozen after the cancel — it must resume tracking"
    assert ins.threshold <= m.MAX_THRESHOLD


# ------------------------------------------------------- the purifier half

def test_the_purifier_bonus_is_paid_only_while_paying_and_scales_with_difficulty():
    for difficulty, want in (("easiest", 5), ("cameogod", 50)):
        ins = m.Insurance(difficulty)
        ins.banked = 1000
        assert ins.tick(m.MAX_THRESHOLD + 1) == 0, "banked but rich -- must pay nothing"
        assert ins.banked == 1000, "the bank must not be spent while not paying"

        # At zero cash depth is 1000 permille, so the payout is the difficulty's PEAK rate and the
        # purifier bonus is its full percentage.
        ins = m.Insurance(difficulty)
        while ins.phase != "paying":
            ins.tick(0)
        ins.accumulator = 0
        ins.banked = 1000
        granted = ins.tick(0)
        assert granted == ins.cash_per_tick + 1000 * want // 100
        assert ins.banked == 0


def test_purifier_deliveries_before_distress_are_never_banked_or_released():
    """A rich bot must not cash out a lifetime of harvests at the first rescue tick."""
    ins = m.Insurance("cameogod")
    for _ in range(10):
        ins.resource_accepted(10000)
    assert ins.banked == 0

    while ins.phase != "paying":
        ins.tick(0)
    ins.accumulator = 0
    granted = ins.tick(0)
    assert granted == ins.cash_per_tick
    assert ins.banked == 0


def test_purifier_and_trickle_cannot_cross_the_liquid_funds_cap():
    ins = m.Insurance("cameogod")
    ins.phase = "paying"
    ins.banked = 100000
    granted = ins.tick(m.MAX_THRESHOLD - 100)
    assert granted == 100


def test_stored_resources_are_liquid_and_never_trigger_or_receive_insurance():
    ins = m.Insurance("cameogod")
    for _ in range(5000):
        assert ins.tick(0, m.MAX_THRESHOLD) == 0
    assert ins.phase == "arming"


# ------------------------------------------------------- proportional payout (the granularity)

def _pay_rate(difficulty: str, cash: int, ticks: int = 2000) -> float:
    """Credits per tick the PAYING phase grants at a given cash level.

    ⚠ The phase is forced, deliberately. You cannot measure this by holding cash steady and
    waiting: the bar converges on a stable pile and `cash < threshold` then never fires, which is
    the strict-`<` law working (see test_a_stable_bot_is_not_subsidised). Isolating the payout law
    from the arming law is the only way to measure the payout curve at a chosen depth.
    """
    ins = m.Insurance(difficulty)
    ins.phase = "paying"
    ins.accumulator = 0
    return sum(ins.tick(cash, has_statistics=False) for _ in range(ticks)) / ticks


def test_the_payout_reproduces_the_old_stacked_ladder():
    """⭐ The granularity the ten-rung ladder had, restored continuously.

    The old rungs sat at 1000..10000 and STACKED, so a `cameogod` bot drew one credit/tick per
    rung it was below. Depth-scaling reproduces that curve and then fills in between the rungs.
    """
    for cash in (9000, 7500, 5000, 2500, 1000, 0):
        old_rungs = sum(1 for r in range(1, 11) if cash < r * 1000)
        assert abs(_pay_rate("cameogod", cash) - old_rungs) <= 0.75, cash


def test_the_payout_rises_monotonically_as_a_bot_gets_poorer():
    """The point of the rewrite: NOT binary. Every difficulty must ramp, not switch on."""
    for d in ("easiest", "medium", "cameogod"):
        rates = [_pay_rate(d, c) for c in (9000, 7000, 5000, 3000, 1000, 0)]
        assert rates == sorted(rates), (d, rates)
        assert rates[0] < rates[-1], f"{d} pays a flat rate — the granularity is gone"


def test_a_fractional_rate_is_actually_paid_and_not_truncated_away():
    """Milli-credit accumulation. A naive integer divide pays ZERO for every low difficulty."""
    rate = _pay_rate("easiest", m.MAX_THRESHOLD // 2)
    assert 0.4 <= rate <= 0.6, f"expected ~0.5 credits/tick, got {rate}"


def test_the_peak_rate_is_reached_only_at_zero_cash():
    for d in m.DIFFICULTIES:
        ins = m.Insurance(d)
        assert abs(_pay_rate(d, 0) - ins.cash_per_tick) < 0.05
        assert _pay_rate(d, m.MAX_THRESHOLD - 1) < 0.05


# ------------------------------------------------------- the net-worth layer

def _crashed(difficulty="medium", assets=0, army=0, par=True, ticks=3000, has_statistics=True):
    """Healthy cash average, then cash collapses to zero while the owner keeps `assets`."""
    ins = m.Insurance(difficulty, use_par_curve=par)
    for _ in range(m.AVERAGE_WINDOW):
        ins.tick(8000, 0, assets, army, has_statistics)
    paid = sum(ins.tick(0, 0, assets, army, has_statistics) for _ in range(ticks))
    return ins, paid


def test_the_mid_push_false_positive_is_fixed():
    """⭐ The bug this layer exists for.

    A bot at zero cash holding a large army and base is NOT bankrupt — it is spending correctly
    and its harvesters will refill it. It must be helped far less than one that has been wiped out.
    """
    rich, rich_paid = _crashed(assets=60000, army=30000)
    poor, poor_paid = _crashed(assets=500, army=0)
    assert rich.last_worth_factor < poor.last_worth_factor
    assert rich_paid < poor_paid / 2, (rich_paid, poor_paid)


def test_a_wealthy_bot_still_gets_the_floor_and_never_nothing():
    """Assets a bot cannot sell do not rebuild a base, so the factor floors rather than hitting 0."""
    rich, rich_paid = _crashed(assets=500000, army=200000)
    assert rich.last_worth_factor == m.MIN_WORTH_FACTOR
    assert rich_paid > 0


def test_the_worth_factor_is_monotonic_in_wealth():
    factors = [_crashed(assets=a)[0].last_worth_factor
               for a in (500, 3000, 10000, 30000, 100000)]
    assert factors == sorted(factors, reverse=True), factors


def test_without_playerstatistics_it_degrades_to_the_cash_only_behaviour():
    """Absence degrades, never breaks — the AI_ARCHITECTURE section 10 invariant."""
    with_stats, _ = _crashed(assets=20000)
    without, _ = _crashed(assets=0, army=0, par=False, has_statistics=False)
    assert without.last_worth_factor == 1000
    assert with_stats.last_worth_factor < 1000


def test_zero_valued_statistics_are_not_treated_as_missing():
    """C# tests `stats != null`; zero-valued fields are still a real statistics trait."""
    with_stats, _ = _crashed(assets=0, army=0, par=False, has_statistics=True)
    without_stats, _ = _crashed(assets=0, army=0, par=False, has_statistics=False)
    assert with_stats.last_worth_factor < without_stats.last_worth_factor


def test_the_self_comparison_never_reads_another_player():
    """⛔ The fog ruling, asserted on the interface: tick() takes only the OWNER's numbers."""
    import inspect
    params = list(inspect.signature(m.Insurance.tick).parameters)
    assert params == ["self", "cash", "resources", "assets", "army", "has_statistics"], params
    src = pathlib.Path(m.__file__).read_text(encoding="utf-8")
    for banned in ("opponent", "enemy", "other_player", "world.Players"):
        assert banned not in src.lower(), f"{banned} — the peer signal must stay self-referential"


# ------------------------------------------------------- the par curve

def test_the_par_curve_starts_at_the_opening_bank_and_saturates():
    for rank in range(len(m.DIFFICULTIES)):
        assert m.par_worth(rank, 0) == m.PAR_BASE_WORTH
        top = m.PAR_BASE_WORTH + m.PAR_ASYMPTOTE_PER_RANK * (rank + 1)
        assert m.par_worth(rank, 10 ** 6) == top


def test_the_par_curve_is_monotonic_in_time_and_difficulty():
    for rank in range(len(m.DIFFICULTIES)):
        vals = [m.par_worth(rank, t) for t in range(0, 60000, 2000)]
        assert vals == sorted(vals), rank
    for t in (7500, 15000, 30000):
        vals = [m.par_worth(r, t) for r in range(len(m.DIFFICULTIES))]
        assert vals == sorted(vals), (t, vals)


def test_the_integer_table_tracks_the_continuous_logistic_it_was_sampled_from():
    """⚠ Sampling costs accuracy. Bounded, and bounded well inside the noise of three invented
    magnitudes — but asserted, so a future edit to ParShape cannot quietly break the shape."""
    sys.path.insert(0, str(ROOT / "tools" / "balance"))
    import bot_difficulty_curve as c
    worst = 0.0
    for rank, d in enumerate(m.DIFFICULTIES):
        for minutes in (5, 10, 15, 20, 30):
            approx = m.par_worth(rank, minutes * m.TICKS_PER_MINUTE)
            exact = c.logistic(d, minutes)
            worst = max(worst, abs(approx - exact) / max(exact, 1))
    assert worst < 0.05, f"table diverges {worst:.1%} from its own logistic"


def test_the_par_ratio_is_clamped_so_a_bad_curve_cannot_dominate():
    """The magnitudes are invented; the clamp is what makes shipping them safe."""
    ins = m.Insurance("medium")
    ins.peak_worth = 100000
    ins.ticks = 20 * m.TICKS_PER_MINUTE
    hopeless = ins.worth_factor_permille(1)
    ins.peak_worth = 100000
    absurd = ins.worth_factor_permille(10 ** 9)
    assert hopeless <= 1000 and absurd >= m.MIN_WORTH_FACTOR
    assert m.PAR_RATIO_MIN < 1000 < m.PAR_RATIO_MAX
