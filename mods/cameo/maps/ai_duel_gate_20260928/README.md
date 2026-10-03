# AI Duel Gate

Headless 1v1 bot duel for `tools/ai/run_ai_match_batch.py` (Stage D of the
AI architecture — the data tap that feeds `aggregate_ai_matches.py`).

## Map

Terrain donor: **Desert Rats** (Madness, `mods/cameo/maps/desert-rats-cnc.oramap`,
also `engine/mods/cnc/maps/desert-rats-cnc`) — 72x72 DESERT melee map whose
two real `mpspawn` cells (22,16 and 49,55) are an exact 180-degree mirror.
`map.bin`/`map.png` are donor-verbatim; real terrain means real base
geometry, resources, and pathing — no synthetic fixture bias.

Do not substitute a hand-made map without checking connectivity first: the
earlier donor (`ai_duel` gate map) had BotB's corner on a concrete pocket
fully ringed by water — the bot owned units but could never path or deploy
(`McvExpansionManager` rescans every index, hits `PathFinder.NoPath`, and
retries forever; worth and liquidity stay frozen at spawn values).

## Shape (all verified against the engine)

- `Referee` — `Playable`+`Required` slot the local client occupies (a local
  server refuses to start with every slot empty). `NonCombatant: True` is the
  *map-declared* intent the match writer honors via `PlayerReference`
  (lobby-occupied slots ignore `Player.NonCombatant`), and
  `StartingUnitsClass: empty` gives it zero actors so conquest fails it on the
  first tick — decided early, never blocks `CheckIfGameIsOver`.
- `BotA`/`BotB` — `Playable: False` slots, i.e. **map-side players**
  (`client == null`): the only headless bot path, since `slot_bot` orders are
  sent by lobby UI / `SkirmishLogic` which do not exist on a `Launch.Map`
  Local server. The `Player` ctor honors `Bot:` (IsBot + bot activation on
  the host), `NonCombatant`, `Enemies:` and `HomeLocation` on that path, and
  the match writer's eligibility admits `IsBot` players as opponents — each
  duelist is the other's only `opponents` entry, aggregator-clean 1v1. The
  `Enemies:` declarations are what put them there: the writer reads the
  `SetupPlayerMasks` stance masks, which survive match resolution — decided
  players report `Spectating` on `Visibility: Lobby` maps, so
  `IsAlliedWith` at write time would report losers as allies instead.
- Starting forces: `SpawnStartingUnits` is `Playable`-gated, so the harness
  resolves each faction's `StartingUnits` group (`light`, else `none`) from
  the mod yaml and pre-places the actors in `Actors:` — same units a skirmish
  would grant, fixed per-side at `HomeLocation` (this map's real mpspawns).
  Support actors are placed at distance >=4 so the MCV deploy footprint stays
  clear.
- Match end: `MustBeDestroyed` restored on `^Building`/`^Vehicle`/
  `^Infantry`/`^Defense` (this mod strips it, so conquest can't see
  eliminations otherwise) → `ConquestVictoryConditions` ends on elimination;
  locked `TimeLimitManager` caps the game — its `NotifyTimerExpired` only
  ranks `Playable` players, so a timed-out duel records both bots `lost`
  (honest draw; it still exits via `CheckIfGameIsOver`).
- Speed: `MapOptions.GameSpeed: maximum` + `GameSpeedDropdownLocked` — a locked
  lobby option makes the local server's hard-coded `option gamespeed default`
  order a no-op (`LobbyCommands` rejects locked options), so fixtures always
  run at max CPU-bound rate. Bot tests SHOULD run at high game speed: iterations are short
  and comparable. The minute cap spans 60,000 ticks per minute at maximum
  (`TimeLimit *= 60 * ticksPerSecond`), so `TimeLimitOptions: 0, 1, 2, 3, 4, 6, 9`
  equal the insane-era 0/10/20/30/40/60/90 caps tick for tick; the default 3 is
  180,000 ticks — compare records only within one speed.

## Variant generation

`run_ai_match_batch.py` copies this dir into
`<SupportDir>/maps/cameo/{DEV_VERSION}/<variant>/`, patches the `Bot:`/`Faction:`
lines inside each `PlayerReference@Bot*` block, replaces the
`AI_DUEL_BOT_UNITS` sentinel in `Actors:` with the resolved starting forces,
patches `TimeLimitDefault`, and launches `OpenRA.exe` with `Launch.Map` +
`Launch.Benchmark` (exits on `GameOver`). Records append to
`<SupportDir>/Logs/cameo-ai-matches.jsonl`.
