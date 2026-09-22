"""Diagnostic coverage of already-eligible, successfully applied timed status grants.

Inputs are simulation ticks and successful grant intervals, not scheduled shots.
Eligibility, source caps and resistance must be resolved before using this helper.
It does not infer prices or turn slowing into an automatic damage multiplier.
"""
from collections import defaultdict
from fractions import Fraction


def coverage(sources, horizon_ticks):
    """Union coverage and overlap attribution for {source: [(start, end), ...]}.

    Intervals are half-open. Equal sharing splits each covered segment among its
    active sources and sums to union coverage. Leave-one-source-out marginal
    coverage is also reported; redundant sources can each have zero marginal value.
    Multiple overlapping grants from one source never count it twice.
    """
    if type(horizon_ticks) is not int or horizon_ticks <= 0:
        raise ValueError('horizon_ticks must be a positive integer')
    events = defaultdict(lambda: defaultdict(int))
    for source, intervals in sources.items():
        if not isinstance(source, str) or not source:
            raise ValueError('source identities must be nonempty strings')
        for start, end in intervals:
            if type(start) is not int or type(end) is not int or end <= start:
                raise ValueError('intervals must have integer start < end')
            left, right = max(start, 0), min(end, horizon_ticks)
            if left < right:
                events[left][source] += 1
                events[right][source] -= 1
    active = defaultdict(int)
    individual = dict.fromkeys(sources, 0)
    marginal = dict.fromkeys(sources, 0)
    shared = {source: Fraction(0) for source in sources}
    union = 0
    previous = 0
    for tick, deltas in sorted(events.items()):
        present = sorted(source for source, count in active.items() if count > 0)
        length = tick - previous
        if present:
            union += length
            for source in present:
                individual[source] += length
                shared[source] += Fraction(length, len(present))
            if len(present) == 1:
                marginal[present[0]] += length
        for source, count in deltas.items():
            active[source] += count
        previous = tick
    return dict(horizon_ticks=horizon_ticks, covered_ticks=union,
        uptime=union / horizon_ticks,
        duplicate_credit_ticks=sum(individual.values()) - union,
        individual_covered_ticks=individual,
        marginal_covered_ticks=marginal,
        equal_share_ticks={source: float(value) for source, value in shared.items()},
        assumption='intervals represent successful eligible grants after caps and resistance')


def successful_hit_intervals(hit_ticks, duration):
    if type(duration) is not int or duration <= 0:
        raise ValueError('positive finite duration required; permanent grants need explicit intervals')
    intervals = []
    for tick in hit_ticks:
        if type(tick) is not int:
            raise ValueError('hit ticks must be integers')
        intervals.append((tick, tick + duration))
    return intervals


def paired_damage_value(events, horizon_ticks, ticks_per_second):
    """Compare paired eligible hits using already-resolved health damage.

    Each (event_id, tick, baseline_damage, status_damage) must use the same
    attacker/target and pre-hit state in both counterfactual evaluations. Armor,
    shields, rounding and overkill policy are caller responsibilities. This is
    the direct incoming-damage channel only, not a full battle or price model.
    Damage may decrease; negative contribution is retained rather than clamped.
    """
    import math
    if type(horizon_ticks) is not int or horizon_ticks <= 0:
        raise ValueError('horizon_ticks must be a positive integer')
    if isinstance(ticks_per_second, bool) or not isinstance(ticks_per_second, (int, float)) or not math.isfinite(ticks_per_second) or ticks_per_second <= 0:
        raise ValueError('ticks_per_second must be positive and finite')
    seen = set()
    baseline, affected, deltas = [], [], []
    for event_id, tick, before, after in events:
        if not isinstance(event_id, str) or not event_id or event_id in seen:
            raise ValueError('paired event identities must be nonempty and unique')
        if type(tick) is not int or not 0 <= tick < horizon_ticks:
            raise ValueError('event tick must be inside the observation horizon')
        for value in (before, after):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('paired damage must be finite and nonnegative')
        seen.add(event_id)
        baseline.append(before)
        affected.append(after)
        deltas.append(after - before)
    total_before, total_after, added = map(math.fsum, (baseline, affected, deltas))
    seconds = horizon_ticks / ticks_per_second
    return dict(event_count=len(seen), baseline_damage=total_before,
                status_damage=total_after, added_damage=added,
                added_dps=added / seconds,
                relative_gain=added / total_before if total_before else None,
                channel='paired incoming health damage only; not a price or full battle result')
