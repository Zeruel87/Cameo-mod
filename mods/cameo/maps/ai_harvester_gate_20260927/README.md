# AI harvester gate

Two `hard` bots, each starting with a construction yard, two power buildings, a
refinery, a vehicle factory and 10000 credits:

* **TkmBot** (`tkm`): its refinery is in `RefineryTypes`, and its harvester only
  reaches `HarvesterTypes` through the harvester role (AI_ARCHITECTURE.md §2.8).
* **AtreidesBot** (`atreides`, Dune 2000): its refinery and yard only reach
  `RefineryTypes` / `ConstructionYardTypes` through the refinery and conyard roles.
  Without them `BaseBuilderBotModuleCA` keeps unit production paused, and the bot
  owns only what the script gave it: 5 buildings + 2 free harvesters = 7 actors.

A refinery gives harvesters away (`FreeActor`: TKM 1, Atreides 2 with the carryall
delivery), and the base builder adds refineries, so the raw count proves nothing.
Each sample (ticks 1500, 3000, 4500, 6000) reports `extra = harvesters - free x
refineries` (the harvesters a bot actually built) and `actors` (everything it owns).

`far` counts the bot's harvesters more than 25 cells from its base. A harvester drafted into an attack
squad shows up here: Atreides without the squad exclusion had 4 of 4 far by tick 6000, and 0 in 4 of 4
runs with it. It's a diagnostic, not a floor: TKM reaches 1–3 far by tick 6000 while harvesting fields
near its extra refineries, although its harvester was always excluded.

The map runs at game speed `insane`, locked, with `-AdaptiveGameSpeed:`. Otherwise it silently runs at
Normal (LESSONS_LEARNED 2026-09-27): ~125 s instead of ~300 s.

Run `python tools/tests/ai_harvester_gate.py [--min TkmBot=3] [--min-actors AtreidesBot=15]`.
It asserts exit code 0 and no new `exception-*.log`, then reads the samples from
`lua.log`. Runs vary. 2026-09-27: TKM built +1/+1 without the harvester role and +5/+6 with it.
`extra` is too noisy for Atreides (0 or +2 between runs), so its floor is `--min-actors`.
