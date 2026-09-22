# Explicit four-voice pilot gate

**Review-only.** The manifest supplies every record index and group key.
DTA base-channel admission is explicit and raw status remains visible.
No source join, normalization writeback or gameplay value is produced.

## Summary

- Groups: **29**; assembly resolved: **0**; channel aggregation resolved: **29**; gate resolved: **0**; gate unresolved: **29**.
- Permanent Current Cameo self-vote binding: **UNRESOLVED** (baseline_missing_current_cameo_channel_vote_contract).
- Scenario policies:
  - **aircraft** (`AEDIS_AIRCRAFT_LIGHT_HEAVY_LADDER`): Light maps to Fighter and Heavy maps to Spaceship; Bomber and Helicopter are equal linear steps between them.
  - **infantry** (`AEDIS_INFANTRY_NONE_LIGHT_TO_NONE_FLAK_PLATE`): None direct; Light maps to Plate; Flak is the equal midpoint between None and Light.
  - **vehicle** (`AEDIS_VEHICLE_LIGHT_HEAVY_LADDER`): Light and Heavy direct; Medium is the equal midpoint; Scout is one equal step below Light; Superheavy is one equal step above Heavy.
- Voice policy: one Current Cameo row plus exactly three distinct reference voices at equal 0.25 weight.

| comparison | status | voices | reasons |
|---|---|---|---|
| ra1/allies/alliedgunturret/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/allies/gunboat/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/allies/alliedmediumtank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/soviets/heavytank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/soviets/mammothtank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/soviets/teslacoil/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/gdi/battletank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/gdi/mammothtank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/gdi/orca/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/nod/lighttank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/nod/obeliskoflight/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/nod/stealthtank/vehicle/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/allies/rifleinfantry/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/allies/ranger/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/soviets/rifleinfantry/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/soviets/grenadier/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/soviets/shocktrooper/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/gdi/minigunner/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/gdi/grenadier/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/nod/minigunner/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/nod/chemicalwarrior/infantry/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/allies/alliedaagun/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/allies/alliedrocketsoldier/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/allies/longbow/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/soviets/rocketsoldier/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| ra1/soviets/samsite/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/gdi/rocketsoldier/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/nod/rocketsoldier/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |
| td/nod/samsite/aircraft/base | UNRESOLVED | — | current_cameo_self_vote_unbound:baseline_missing_current_cameo_channel_vote_contract |

Resolved means are diagnostic only; target eligibility, cadence, secondary payloads, runtime applicability and gameplay review remain separate.
