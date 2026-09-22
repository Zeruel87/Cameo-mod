# AI phase 2 runtime gate

This map starts one fixed `hard` bot and one human enemy with a construction
yard each. The fixed bot form matches Cameo campaign maps and activates the
normal modular-bot player construction path. At tick 400, Lua writes
`AI_PHASE2_GATE_COMPLETED`.

The runtime pass requires the completion marker and no new exception log. It
proves successful world/player construction and 400 ticks with a configured
hard bot under the pinned engine. The focused `MasterAiBotModuleTest` cases
separately cover the unavailable-incumbent decision branch. `Launch.Map` uses a
local server, so it cannot populate a playable skirmish-bot slot; the runtime
snapshot assertion remains inferred from the normal modular-bot wiring rather
than read back through `AiSituationLogWriter`.
