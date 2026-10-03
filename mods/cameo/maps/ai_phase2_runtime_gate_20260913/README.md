# AI phase 2 runtime gate

This map starts one fixed `hard` bot and one human enemy with a construction
yard each. The fixed bot form matches Cameo campaign maps and activates the
normal modular-bot player construction path. At tick 900, Lua writes
`AI_PHASE2_GATE_COMPLETED`.

Run `python tools\tests\ai_bot_player_gate.py` to launch this map with
`Launch.Map` and `Launch.Benchmark`, then read back the appended
`cameo-ai-situations.jsonl` records. The gate requires repeated `HardBot`
situation snapshots with a real decision, target, personality, and unsaturated
target score before the failed objective ends the world and benchmark exit.
Map-declared bots are included in the match and situation logs even though they
do not occupy playable lobby slots, so campaign and other map-declared bots also
produce records. Each record carries `map_uid` and `bot_type` for offline
filtering.
