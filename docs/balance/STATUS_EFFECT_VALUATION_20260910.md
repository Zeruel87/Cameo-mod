# Status-effect valuation: source inventory and overlap diagnostics

Direct damage and status utility remain separate. This work adds no formula coefficient, upgrade price, unit cost or HP change.

The active-manifest inventory finds 26 conditions emitted by directly bound weapons. `tools/audit/status_effect_inventory.py` records each resolved grant, its armament condition, concrete actor receivers and conditional consumer traits. A receiver count is a count of active definitions, not combat prevalence or guaranteed eligibility.

## Findings that affect valuation

- SonicDebuff has 12 emitting weapon definitions and 1543 concrete receiver definitions. Its direct combat consumers are incoming DamageMultiplier and SpeedMultiplier; the colored overlay is cosmetic. Existing generic Sonic and new delivery-specific Sonic coexist.
- Shieldhit has 1492 emitters but only an idle-overlay consumer in this inventory. Counting every condition grant as a damage bonus would price a cosmetic hit marker.
- HueyCryoMissiles still declares a CryoFreeze grant with no matching ExternalCondition receiver. The engine grant warhead only calls a matching ExternalCondition, so this explicit route cannot apply to the inventoried actors. The weapon already cools through Temperature scale -200, and the physical-state system grants CryoFreeze from that meter. Do not count the inert external grant as a second freezing benefit or add receivers that bypass the meter.
- LeechDisinfect grants LeechEggKill, but the active concrete inventory has neither a receiver nor LeechEggLaid/LeechEggKill target tags. The legacy receiver/target block is commented out. No active disinfection benefit is established by this route.
- Other conditions span healing, combat buffs, slowing, blindness, berserk behavior, power drains and disable effects. Their recipient gates, source caps and indirect conditional grants must be traced individually. The inventory does not assign one common multiplier to them.

`GrantExternalConditionWarhead.DoImpact` applies to the hit actor when the impact target is an actor; it searches the configured circle for a positional impact. Therefore a declared Range alone does not prove area-wide debuff coverage on every shot. Hit type and actual successful grants must feed any uptime estimate.

## Deterministic uptime examples

`tools/balance/status_uptime.py` accepts successful eligible grant intervals after source caps and resistance. It reports union coverage, individual coverage, the extra ticks that naive independent credit would double-count, leave-one-source-out marginal coverage and an explicit equal-share attribution. Repeated hits from one source do not stack its multiplier.

| Synthetic successful-hit scenario | Window | Covered fraction | Duplicate credit if sources are added independently |
| --- | ---: | ---: | ---: |
| One source, hits every 66 ticks, duration 50 | 200 ticks | 76% | 0 ticks |
| Two such sources staggered by 33 ticks | 200 ticks | 100% | 87 ticks |
| Two fast sources, 32-tick spacing, staggered by 16 | 200 ticks | 100% | 184 ticks |
| Four hits at 0/2/4/6, repeating every 72, duration 50 | 216 ticks | 77.78% | 0 ticks |

These are specified input scenarios, not measured hit schedules. The fast second source can add no new coverage despite having many successful hits. Equal sharing is an attribution convention, not a price formula.

For Sonic's incoming-damage modifier, a future scenario can multiply eligible baseline team damage during newly covered intervals by 0.5, with integer rounding and other active modifiers modeled separately. Slowing requires movement, pursuit, escape and exposure scenarios; a 25% speed reduction is not automatically a 25% damage or price increase. Permanent/unknown durations are rejected by the finite-duration helper unless the caller supplies an explicit observation interval.

Five focused overlap tests pass, covering redundant sources, repeated grants, partial overlap, unsupported durations and streamed hit logs. The hit-log helper consumes an iterator once, avoiding silent loss of all intervals during validation. Remaining work is recipient eligibility and cap semantics, additional status-specific value channels, and observed combat inputs. Upgrade pricing remains deferred.

Aedis's 18:52 clarification permits Cryo to trade direct damage for control, and requires this valuation before deciding final Sonic/Cryo damage tradeoffs. Do not apply the proposed Sheridan raw-damage parity buff or treat the earlier Sonic no-loss direction as an unconditional policy. A constant eligible baseline team DPS of 100 with Sonic coverage of 76% would gain 38 average DPS from its 1.5 incoming-damage multiplier alone; full coverage yields 50, regardless of how many overlapping sources sustain it. This is an illustrative scenario, not observed combat output, and excludes the separate value of slowing.
