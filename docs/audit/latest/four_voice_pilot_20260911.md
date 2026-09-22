# Explicit four-voice pilot gate

**Review-only.** The manifest supplies every record index and group key.
DTA base-channel admission is explicit and raw status remains visible.
No source join, normalization writeback or gameplay value is produced.

## Summary

- Groups: **12**; assembly resolved: **12**; gate resolved: **7**; gate unresolved: **5**.
- Scenario policy: vehicle Light/Heavy direct, Medium midpoint, Scout and Superheavy one-step extrapolation.
- Voice policy: one Current Cameo row plus exactly three distinct reference voices at equal 0.25 weight.

| comparison | status | voices | reasons |
|---|---|---|---|
| ra1/allies/alliedapc/vehicle/base | UNRESOLVED | — | axes:Combined Arms:mapped_axis_negative:Superheavy; axes:OpenRA Red Alert:mapped_axis_negative:Superheavy |
| ra1/allies/alliedartillery/vehicle/base | UNRESOLVED | — | axes:Combined Arms:mapped_axis_negative:Superheavy; axes:OpenRA Red Alert:mapped_axis_negative:Superheavy |
| ra1/allies/alliedmediumtank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/soviets/heavytank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/soviets/mammothtank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/soviets/teslacoil/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| td/gdi/battletank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/gdi/grenadier/vehicle/base | UNRESOLVED | — | axes:Combined Arms:mapped_axis_negative:Superheavy; axes:DTA Enhanced:mapped_axis_negative:Superheavy; axes:OpenRA Tiberian Dawn:mapped_axis_negative:Superheavy |
| td/gdi/mlrs/vehicle/base | UNRESOLVED | — | axes:Combined Arms:mapped_axis_negative:Superheavy; axes:DTA Enhanced:mapped_axis_negative:Superheavy; axes:OpenRA Tiberian Dawn:mapped_axis_negative:Superheavy |
| td/nod/lighttank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/nod/obeliskoflight/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/nod/reconbike/vehicle/base | UNRESOLVED | — | axes:Combined Arms:mapped_axis_negative:Scout |

Resolved means are diagnostic only; target eligibility, cadence, secondary payloads, runtime applicability and gameplay review remain separate.
