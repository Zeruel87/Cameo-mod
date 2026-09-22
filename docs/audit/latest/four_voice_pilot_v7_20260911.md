# Explicit four-voice pilot gate

**Review-only.** The manifest supplies every record index and group key.
DTA base-channel admission is explicit and raw status remains visible.
No source join, normalization writeback or gameplay value is produced.

## Summary

- Groups: **21**; assembly resolved: **21**; channel aggregation resolved: **21**; gate resolved: **21**; gate unresolved: **0**.
- Scenario policies:
  - **infantry** (`AEDIS_INFANTRY_NONE_LIGHT_TO_NONE_FLAK_PLATE`): None direct; Light maps to Plate; Flak is the equal midpoint between None and Light.
  - **vehicle** (`AEDIS_VEHICLE_LIGHT_HEAVY_LADDER`): Light and Heavy direct; Medium is the equal midpoint; Scout is one equal step below Light; Superheavy is one equal step above Heavy.
- Voice policy: one Current Cameo row plus exactly three distinct reference voices at equal 0.25 weight.

| comparison | status | voices | reasons |
|---|---|---|---|
| ra1/allies/alliedgunturret/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/allies/gunboat/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/allies/alliedmediumtank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/soviets/heavytank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/soviets/mammothtank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/soviets/teslacoil/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| td/gdi/battletank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/gdi/mammothtank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/gdi/orca/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/nod/lighttank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/nod/obeliskoflight/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/nod/stealthtank/vehicle/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| ra1/allies/rifleinfantry/infantry/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/allies/ranger/infantry/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/soviets/rifleinfantry/infantry/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/soviets/grenadier/infantry/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| ra1/soviets/shocktrooper/infantry/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Red Alert | — |
| td/gdi/minigunner/infantry/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/gdi/grenadier/infantry/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/nod/minigunner/infantry/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |
| td/nod/chemicalwarrior/infantry/base | RESOLVED | Current Cameo, Combined Arms, DTA Enhanced, OpenRA Tiberian Dawn | — |

Resolved means are diagnostic only; target eligibility, cadence, secondary payloads, runtime applicability and gameplay review remain separate.
