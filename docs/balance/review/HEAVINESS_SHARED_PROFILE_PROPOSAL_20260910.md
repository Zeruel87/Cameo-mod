# Shared-profile proposal — 10 September, 03:20 Jakarta

Status: Aedis approved this interpretation at03:17 after proposing replacement of percentage endpoint tables with the same armor
profile used for flat damage, then scaling the percentage component by heaviness.
The existing five-weapon endpoint pilot is not expanded while this is assessed.
No shared-profile mode has been implemented or activated at this checkpoint.

## Current rule versus proposed rule

The C# folded conversion is `(Damage * PercentageScale + 100000) / 200000`
integer basis points. With the usual Scale 10000, Damage 100 gives 5 basis points,
or 0.05% max HP before armor. The engine supports 0.01% granularity; it does NOT
currently make every 100 damage equal 0.01% HP. Those are distinct statements.
Scale 2000 would give the requested 100 -> 0.01% conversion. This reduces the
baseline percentage component fivefold rather than merely increasing precision.
Existing overrides and disabled legacy warheads must retain their old semantics.
The 100 -> 0.01% ratio is BEFORE heaviness and armor. With h/2, h=1 halves
that to 0.005% before granularity rounding; h=2 reaches the full base coefficient.

## Measured starting point and analytical candidates

Six actual in-game shots verified the old endpoint implementation against an
unmodified Medium-armored 1,000,000-HP target. Each used Damage 2000. Values below
retain the flat profile; the two right columns are calculations, not game tests.

| h | Actual flat | Actual percentage | Actual total | Proposed total, Scale 2000 and h/2 | Proposed total, Scale 2000 and h |
|---|---:|---:|---:|---:|---:|
| 0 | 2720 | 1400 | 4120 | 2720 | 2720 |
| 1 | 2640 | 1800 | 4440 | 3960 | 5280 |
| 2 | 2760 | 2400 | 5160 | 5520 | 8280 |

The h/2 variant is the lower-impact starting candidate (also offered by Aedis at
03:08). It is not universally equivalent: h=0 intentionally loses percentage damage,
and other armor types/HP pools differ. Preserve Damage, cadence and delivery, report
full per-armor deltas, then let pricing read the actual effect; do not force K equal.

## Shield proposal and pending distinction

Aedis requested unique family Shield coefficients, scaling from 100% at h=0 to
200% at h=2. A common `1 + h/2` multiplier preserves uniqueness at the SAME h;
different h values can coincide, which is not global uniqueness across all weapons.
For CannonAP's base 144, the flat Shield coefficients would be 144/216/288.

At 03:09 Astra asked whether this scales the Shield armor coefficient while the
percentage component still vanishes at h=0, or whether Shield is an exception to
that zero-percentage endpoint. At03:17 Aedis confirmed the first interpretation:
the percentage component remains zero at h=0, while flat Shield damage has its floor.

## Safe implementation boundary

An explicit opt-in mode should retain old endpoint fields for unmigrated content,
reject mixed shared/endpoint configuration, apply the bell once, preserve the
disabled -1 contract, and use bounded integer rounding. New bases use the new
conversion deliberately; no silent global default replacement. Runtime and Python
models must share fixtures and actual C# tests. Keep raw compatibility duplicates
visible. The earlier endpoint tests and six-shot probe remain historical evidence,
not certification of this proposed mode.
