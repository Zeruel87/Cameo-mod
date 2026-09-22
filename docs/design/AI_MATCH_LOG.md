# AI match log — record schema v1

One JSON object per line (JSONL), **one line per bot player per finished match**.
Append-only. Never rewritten, never read back by the game.

File: `Platform.SupportDir` + `Logs/cameo-ai-matches.jsonl` (a single file across
matches and across releases; the batch harness may point elsewhere later via the
trait's `FileName` field).

Field order below is the required emission order (stable field order keeps diffs
and `sort`-based dedupe useful). All keys snake_case. All numbers integers.
Strings are the internal names, never the display/translated names.

```json
{
  "schema": 1,
  "record_id": "<game_uid>|<player_internal_name>",
  "recorded_utc": "2026-08-31T10:27:15.1234567Z",
  "mod_version": "<Game.ModData.Manifest.Metadata.Version>",
  "game_uid": "<world.LobbyInfo.GlobalSettings.GameUid, may be empty>",
  "map_uid": "<world.Map.Uid>",
  "map_title": "<world.Map.Title>",
  "duration_ticks": 12345,
  "timestep": 40,
  "player": {
    "name": "<player.InternalName>",
    "bot_type": "medium",
    "faction": "td_gdi",
    "team": 1,
    "handicap": 0,
    "spawn": 3,
    "outcome": "won",
    "personality": "rush",
    "personality_switches": 0,
    "personality_timeline": [ { "tick": 0, "personality": "rush" } ]
  },
  "stats": {
    "units_killed": 0,
    "units_lost": 0,
    "buildings_killed": 0,
    "buildings_lost": 0,
    "kills_cost": 0,
    "deaths_cost": 0,
    "army_value": 0,
    "assets_value": 0,
    "resources_earned": 0,
    "resources_spent": 0
  },
  "opponents": [
    { "name": "Multi1", "is_bot": true, "bot_type": "hard", "faction": "td_nod",
      "team": 2, "handicap": 0, "outcome": "lost" }
  ],
  "allies": []
}
```

## Field rules

- `record_id` — `game_uid + "|" + player.InternalName`. When `game_uid` is empty
  (skirmish without one), substitute a per-match `Guid.NewGuid().ToString("N")`
  generated ONCE per world by the world-level writer and shared by all lines of
  that match, so lines of one match always share a prefix.
- `outcome` — lowercase `won` / `lost` / `undecided`. `undecided` covers
  `WinState.Undefined` (game ended without a resolution, e.g. host quit).
  Emit the record anyway; the aggregator drops undecided rows.
- `personality` — the personality condition enabled at the END of the match,
  with the `personality-` prefix stripped (`personality-rush` -> `rush`).
  `""` if none was ever enabled (a non-personality bot).
- `personality_timeline` — every observed change, oldest first, including the
  initial grant; `tick` is `world.WorldTick` at the change. Cap the list at 64
  entries (drop the middle, keep first 32 and last 32) so a future oscillating
  manager cannot produce unbounded lines. `personality_switches` is the TOTAL
  number of changes observed after the first grant, uncapped, so a truncated
  timeline is still detectable.
- `stats` — from `PlayerStatistics` on that player, plus `PlayerResources`
  (`Earned`/`Spent`) for `resources_earned`/`resources_spent`; `0` when the
  trait is absent.
- `opponents` / `allies` — every non-neutral, non-spectating player other than
  the subject, split by `player.IsAlliedWith`. Same key order as shown.
- `handicap` and `bot_type` are recorded because they are the cheat axes: an
  aggregation that mixes handicaps or difficulty tiers is meaningless.
- Ordering: `opponents` and `allies` sorted by `name` ordinal, so two records of
  the same match are byte-comparable.

## Writer rules

Loaded saves are excluded for the entire world lifetime, using eligibility captured
at world load before replay-in clears the loading flag. This prevents resumed
matches from being recorded as fresh complete observations.

- Write ONLY for fresh worlds (`!IsLoadingGameSave` at world load),
  `world.Type == WorldType.Regular`, `!world.IsReplay`, and
  `Game.IsHost` (bots only tick on the host — `Player.cs:223` — so the host is
  the only process with authority, and this prevents every client in a
  multiplayer game appending a duplicate line).
- Write once per match, at the first of: `IGameOver.GameOver`, or all bot
  players resolved as polled by `ITick`. Guard with a `written` flag.
- Append under a cross-process named mutex derived from the canonical file path,
  exactly as `CameoCareerRepository` does (`SHA256` of the upper-cased full path
  on Windows), because the future AI-vs-AI harness runs many instances at once.
  Timeout 100 ms; on timeout retry on a later tick with the same backoff shape
  as `CameoCareerRecorder.TryPersist` (`1 << min(retry-1, 5)`, capped 30 ticks),
  and give up silently after 8 attempts — a missing log line must never affect
  a match.
- One `File.AppendAllText` of all lines for the match, each line terminated with
  `"\n"` (not `Environment.NewLine`), UTF-8 no BOM. Serialize by hand
  (`StringBuilder`) with `CultureInfo.InvariantCulture`; escape `\`, `"` and
  control characters in every string value. Do not add a JSON dependency.
- Never read the file, never let its contents influence the simulation, and
  never touch synced state. This is record-only.

## Emitter guard — hand-serialized JSON has a separator bug class

Serializing by hand means one forgotten comma makes every line unparseable, and
the aggregator can only report that as a skip — it cannot say *why*. The first
implementation shipped with exactly that: `AppendTimeline` wrote no leading
comma, so every line came out as

    ..."personality_switches":0"personality_timeline":[]...

`tools/tests/test_aggregate_ai_matches.py` could not see it, because its
fixtures are built with `json.dumps` — it tests the reader, never the writer.

Two rules follow, and both are load-bearing:

- **Every `Append*` helper writes its own leading separator**, governed by the
  same `first` flag — `AppendString`, `AppendNumber`, `AppendBoolean`,
  `AppendObjectPropertyStart`, `AppendTimeline` and `AppendRelationships` alike.
  `BuildLog` therefore contains no hand-written `,` at all. A new field cannot
  be added without its separator because there is nowhere to omit it from.
- **`OpenRA.Mods.Cameo.Test/AiMatchLogWriterTest.cs` runs that same call
  sequence and parses the result** with `JsonDocument`. It fails 2 of 3 against
  the original emitter. Extend it whenever `BuildLog` grows a field.

## Situation snapshot log (schema 1)

Phase 2 adds a second record type to the same record-only logging boundary.
`MasterAiBotModule` publishes an unsynced, host-local snapshot and does not
queue orders, grant conditions, mutate synced state, or read either log back.
The snapshot is intentionally **pre-fog**: it scans `world.Actors` without
shroud gating. Future fogged observation is a later phase.

The situation writer emits one line per snapshot rebuild per bot player. For
matches exceeding 2000 rebuilds, the buffer retains the first 1000 and most
recent 1000 lines and silently drops the middle. Field order is stable and all
numeric values are integers:

```json
{"schema":1,"kind":"situation","record_id":"<game_uid>|<player>|<tick>","game_uid":"","map_uid":"...","player":"Multi0","faction":"td_gdi","bot_type":"medium","tick":1500,"urgency":"normal","personality_current":"rush","personality_candidate":"steamroller","main_target":"Multi1","main_target_score":730,"hints":{"defence_fraction":35,"expansion_appetite":20},"demand":{"anti_air":10,"anti_armour":40,"anti_infantry":25,"detector":0,"artillery":60},"own":{"army_value":5400,"defence_value":1200,"buildings":14,"harvesters":4,"kills_cost_window":900,"deaths_cost_window":1500},"enemies":[{"name":"Multi1","faction":"td_nod","alive":true,"army_value":8100,"infantry_value":2000,"vehicle_value":5000,"air_value":1100,"naval_value":0,"defence_count":7,"defence_value":3500,"tech_buildings":4,"production_buildings":3,"buildings":9,"expansion_clusters":2,"harvesters":5,"refineries":2,"pressure_value":800,"stealth_share":10,"nearest_cells":42,"last_seen_tick":1500,"score":730}]}
```

`urgency` is `normal`, `pressured`, or `emergency`; `main_target` is empty
when there is no candidate. Enemy records are sorted by ordinal player name.
Candidate personality and target values are observations only. The phase-2
target score deliberately has no pairwise-damage (`w_hurt`) term because no
usable attribution hook exists; that term is phase-4 work.
