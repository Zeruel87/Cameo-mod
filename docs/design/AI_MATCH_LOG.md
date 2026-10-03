# AI match log — record schema v2

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
  "schema": 2,
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
    "home": "42,17",
    "outcome": "won",
    "personality": "rush",
    "personality_switches": 0,
    "personality_timeline": [ { "tick": 0, "personality": "rush" } ],
    "composition": "tdgdi_armorpush",
    "composition_switches": 0,
    "composition_timeline": [ { "tick": 9000, "composition": "tdgdi_armorpush" } ],
    "episode_timeline": [ { "tick": 0, "personality": "rush", "composition": "", "kills_cost": 0, "deaths_cost": 0 },
                          { "tick": 9000, "personality": "rush", "composition": "tdgdi_armorpush", "kills_cost": 1500, "deaths_cost": 800 } ]
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
    "resources_spent": 0,
    "stats_timeline_fields": "tick,earned,spent,army_value,assets_value,kills_cost,deaths_cost,banked,idle_queues",
    "stats_timeline": [ [750, 1200, 1000, 800, 5000, 0, 0, 200, 1], [1500, 2600, 2500, 1900, 7000, 300, 110, 100, 0] ]
  },
  "opponents": [
    { "name": "Multi1", "is_bot": true, "bot_type": "hard", "faction": "td_nod",
      "team": 2, "handicap": 0, "outcome": "lost" }
  ],
  "allies": []
}
```

## Field rules

- `home` — `player.HomeLocation` as `"x,y"`. `spawn` is the LOBBY's spawn choice and is `0`
  for every map-side player, which is how the A/B harness seats both duelists — so in a
  harness run `spawn` is constant and says nothing about side. Key side analysis on `home`.
- `stats_timeline` — one row per `AiMatchLogWriter.SampleIntervalTicks` (default 750) world
  ticks, columns named by `stats_timeline_fields`; cumulative except `army_value`,
  `assets_value`, `banked` (cash + stored resources) and `idle_queues` (player-level production
  queues that could build something but have nothing queued — the discipline metric of
  AI_DEEP_RESEARCH §13 item 1). Sampled on TICKS, not on `PlayerStatistics`' own graph cadence, which follows
  game time (every 3000 ticks at the harness's maximum speed). Optional: records written
  before it existed have no timeline.

`schema` is `2` for records carrying the composition/episode fields; older
schema-1 records in the same file remain valid and the aggregator pools both
(they simply contribute no composition/episode rows).

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
- `composition` — `UnitCompositionsBotModule` composition `Id` active at the END
  of the match; `""` for the baseline build order. Composition transitions are
  observed via `UnitBuilderBotModuleCA.ActiveCompositionChanged`, a read-only
  event added for exactly this purpose — the recorder never steers selection.
- `composition_timeline` — every composition selection/revert, oldest first;
  `""` marks a revert to baseline. Same 64-entry keep-first-32/last-32 cap, and
  `composition_switches` stays the uncapped total.
- `episode_timeline` — schema 2's attribution primitive: one entry whenever the
  personality OR the active composition changes, carrying `kills_cost` /
  `deaths_cost` snapshotted from `PlayerStatistics` at that tick. Each entry
  opens an episode; the aggregator diffs consecutive snapshots (the last entry
  diffs against match-end `stats`) to get per-episode value destroyed vs lost —
  the §6.1 `outcome` unit of learning. Damage before the first boundary is
  unattributed. Cap: 128 entries (keep first 64 / last 64).
- `stats` — from `PlayerStatistics` on that player, plus `PlayerResources`
  (`Earned`/`Spent`) for `resources_earned`/`resources_spent`; `0` when the
  trait is absent.
- `arsenal` — the player's `BotArsenalLedger` (AI_ARCHITECTURE.md §12.3, CA-1): one object per own
  actor type, ordered by `killed_value` — `created`, `lost`, `lost_value`, `killed_value` (value of
  enemy actors this type destroyed) and `killed_by_victim` (that value split by victim type). Booked
  by Cameo's `UpdatesPlayerStatistics` shadow (Info subclasses the engine's, trait wraps it), so
  every actor carrying that trait counts; pre-placed and starting units count as `created`.
  Empty when the ledger trait is absent.
- `opponents` / `allies` — every eligible player other than the subject, split
  by the **stance masks** (`p.AlliedPlayersMask.Overlaps(subject.PlayerMask)`),
  NOT by `player.IsAlliedWith`. The masks are assigned once by
  `CreateMapPlayers.SetupPlayerMasks` from `PlayerReference.Allies`/`Enemies`
  and lobby teams, and never mutate — so they still describe the matchup after
  the match resolves. `Player.Spectating` is `spectating || WinState !=
  Undefined` on non-mission maps (`Player.cs`), and `RelationshipWith`
  short-circuits `other.Spectating` to Ally for combatant evaluators — the log
  is built only after players resolve, so `IsAlliedWith` at write time reports
  every decided player as an ally of every combatant. Eligible means
  `!NonCombatant && (Playable || IsBot)`, where `NonCombatant` is taken from
  **both** the runtime flag and the declared `PlayerReference.NonCombatant` —
  a lobby-occupied slot ignores the runtime flag (`Player` ctor client branch),
  so map-declared inert slots (the `ai_duel_gate` referee) must be read off the
  reference or they leak into `opponents` and silently turn every record
  non-1v1. `IsBot` admits map-side bots: `Playable` is true only for lobby
  clients, but a headless `Launch.Map` match's duelists are map players
  (`Playable: False` + `Bot:`) that are nonetheless each other's real
  opponents.
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

## Situation snapshot log (schema 2)

Phase 2 adds a second record type to the same record-only logging boundary.
`MasterAiBotModule` publishes an unsynced, host-local snapshot and does not
queue orders, grant conditions, mutate synced state, or read either log back.
The snapshot carries the currently published mission intent (`mission`, or `null`) in addition
to the existing fields. Schema-1 records remain valid. Mission records contain `type`,
`priority`, and `region_index`; only `raid` and `defend` are produced in phase 7a.

The situation writer emits one line per snapshot rebuild per bot player. For
matches exceeding 2000 rebuilds, the buffer retains the first 1000 and most
recent 1000 lines and silently drops the middle. Field order is stable and all
numeric values are integers:

```json
{"schema":2,"kind":"situation","record_id":"<game_uid>|<player>|<tick>","game_uid":"","map_uid":"...","player":"Multi0","faction":"td_gdi","bot_type":"medium","tick":1500,"urgency":"normal","personality_current":"rush","personality_candidate":"steamroller","main_target":"Multi1","main_target_score":730,"mission":{"type":"raid","priority":65,"region_index":18},"hints":{"defence_fraction":35,"expansion_appetite":20},"demand":{"anti_air":10,"anti_armour":40,"anti_infantry":25,"detector":0,"artillery":60},"own":{"army_value":5400,"defence_value":1200,"buildings":14,"harvesters":4,"kills_cost_window":900,"deaths_cost_window":1500},"enemies":[{"name":"Multi1","faction":"td_nod","alive":true,"army_value":8100,"infantry_value":2000,"vehicle_value":5000,"air_value":1100,"naval_value":0,"defence_count":7,"defence_value":3500,"tech_buildings":4,"production_buildings":3,"buildings":9,"expansion_clusters":2,"harvesters":5,"refineries":2,"pressure_value":800,"stealth_share":10,"nearest_cells":42,"last_seen_tick":1500,"score":730}]}
```

`urgency` is `normal`, `pressured`, or `emergency`; `main_target` is empty
when there is no candidate. Enemy records are sorted by ordinal player name.
Candidate personality and target values are observations only. The phase-2
target score deliberately has no pairwise-damage (`w_hurt`) term because no
usable attribution hook exists; that term is phase-4 work.

`own.losses_by_role` / `own.away_losses_by_role` (objects, keys sorted) are the
CUMULATIVE cost of units lost, by the role the unit held at the last role pass
(`AssignRolesInterval`): a squad type (`rush` = the main attack force, `protection`,
`guerrilla`, `harass`, `artillery`, `support`, `air`, `naval`) or `idle` (at the base,
in no squad). `away_` is the part lost farther than `MaxBaseRadius` from the base
centre. Units in no squad and not idle (harvesters, MCVs) are not counted, so the
difference to `PlayerStatistics.DeathsCost` is buildings plus those. Summed over
every squad manager, including disabled personalities' (a disabled manager forgets
its snapshot, so a unit is never booked twice).

`own.combat_ratio_pct` / `own.combat_ratio_defended_pct` (record-only, phase CP of
`AI_DEEP_RESEARCH.md` §2.3): the Lanchester square-law ratio ×100 of the own combat units against
the enemy combat units this bot REMEMBERS (fog memory; mobile contacts expire), and against those
plus remembered enemy defences. Damage per tick uses each weapon's main warhead, burst cycle and
Versus against the target's armour, spread over the enemy by HP share. Above 100 the own side is
predicted to win; capped at 10000 (an enemy with nothing remembered that can shoot back). No
decision reads it yet — it is being validated against the decisive fights (`tools/ai/fight_report.py`).

## Batch harvest (Stage D)

**Maintainer test mandate (2026-09-28):** every bot A/B test runs on the real
tournament map — `mods/cameo/maps/ai_duel_nuclear_winter/` (a byte-faithful
extract of `_ra_a-nuclear-winter.oramap` whose two `Playable` slots become
map-side `BotA`/`BotB` players on the real mpspawn cells Actor705/Actor971) —
at the fixture's locked `insane` gamespeed. No hand-made duel fixtures: earlier
synthetic maps misled testing (disconnected pockets, painted-ore-only fields).
The acceptance match-up is the asymmetric one — `fransbot` (fog-honest: the
Cameo x RV x CA x CN x Fransbot composite) must beat `classic` (the pre-wave
stack with `RevealsMap` omniscience, `bot_ai.classic` / `classicbot` condition).
Default invocation:
`python tools/ai/run_ai_match_batch.py --factions ra1_soviets --bot-a fransbot --bot-b classic --repeats N`
(the harness template already defaults to the Nuclear Winter fixture).


`tools/ai/run_ai_match_batch.py` multiplies the log's value: it generates a
variant of the duel map per matchup inside the
batch's isolated `Engine.SupportDir` user-map cache (`maps/cameo/{DEV_VERSION}`)
— since 2026-09-28 the default source is `_ra_a-nuclear-winter.oramap` (see
the A/B acceptance protocol below; `--map` still accepts the legacy
`ai_duel_gate_20260928/` template dir),
launches `OpenRA.exe` with `Launch.Map` + `Launch.Benchmark`, and slices the
appended `cameo-ai-matches.jsonl` per run by byte offset. The duelists are
map-side bots (`Playable: False` + `Bot:`) — the only bot path under a Local
server — so `SpawnStartingUnits` cannot serve them; the harness resolves each
faction's `StartingUnits` group from the mod yaml and writes it into the
variant's `Actors:` section at that bot's `HomeLocation`. The template's
terrain is a real melee map (Desert Rats donor) with both `HomeLocation`s on
its two real `mpspawn` cells — a hand-made fixture once put one duelist on a
disconnected pocket, and the bot sat inert all match. Match end is
`ConquestVictoryConditions` (map restores `MustBeDestroyed` on the base unit
templates — Cameo strips it) or the locked `TimeLimitManager`; timeout ranks
`Playable` players only, so a stalemated duel records both bots `lost` — an
honest draw. The referee slot exists only to satisfy the local server's
non-empty-slots start rule; it is `NonCombatant` by map declaration, gets no
starting units, and is invisible to the records.

Operational semantics measured live (2026-09-28; speed raised 2026-09-29): the fixture locks
`gamespeed: maximum` via `MapOptions` — the maintainer's convention for bot
matches so batches iterate quickly. `TimeLimitManager` scales the minute cap
by `ticksPerSecond` (60,000 ticks per minute at maximum), so the duel fixtures offer
`TimeLimitOptions` 0/1/2/3/4/6/9, tick for tick the insane-era 0/10/20/30/40/60/90, and default to 3
(180,000 ticks): the **engine** ends a stalemate at that depth and records it (both sides `lost`: a timed-out stalemate has no
winner; proven live 2026-09-29, two `veryeasy` mirrors ended at 60,001 ticks under `--time-limit 1`), where a
30-minute cap (1.8M ticks) left the harness to kill it with no record. Achieved speed stays whatever
the box sustains; timeouts are therefore bounded
by a `debug.log` stall detector (a live match writes every few seconds) plus a
speed-aware wall backstop, never a tight fixed timeout. Game speed shortens
elimination matches only — drop `timelimit` when a quick pipeline check needs
a fast draw. An `exit=1` with zero
records and no exception is an external `TerminateProcess` — the engine only
returns 0/-1 — so the harness retries a no-records attempt once and appends
one durable line per attempt to `batch_results.jsonl`. Ally/opponent in the
records comes from the static stance masks, not `IsAlliedWith`: on
non-mission maps every decided player reports `Spectating`, which
short-circuits `RelationshipWith` to Ally for both losers. Generated variants
carry a unique comment salt because `Map.ComputeUID` hashes bytes and
identical copies merge into one `MapCache` preview.

## The A/B acceptance protocol (maintainer ruling 2026-09-28)

All bot-vs-bot testing runs on the shipped tournament duel map **"A Nuclear
Winter"** (`mods/cameo/maps/_ra_a-nuclear-winter.oramap`) — real melee terrain,
two `mpspawn` cells, `Categories: Tournament`. Generated shell fixtures are no
longer the test surface for bot comparisons.

The matchup axis is the franken-bot vs the classic bot:

- **Side A — the candidate stack**: the fog-honest merged stack, no global
  map vision — scouts, fog memory, region intel, nothing omniscient.
  Concretely that is the `hard` type (the `genericbot` modules = the
  Cameo × RV × CA × CN merge) — while `fransbot` is the Frans-module
  **donor** stack, kept as a separate lobby-hidden type so its modules can
  be A/B-tested in isolation before joining `hard` (maintainer 2026-09-28:
  "its modules join the Frankenstein stack one at a time"). `fransbot`
  does NOT receive the `genericbot` condition — the two stacks are
  disjoint. Both pairings against `classic` are informative; the named
  acceptance candidate is whichever stack carries the merged modules
  (today: `hard`).
- **Side B — `classic`**: the old `ModularBot` type — `classicbot` module
  gate plus the shared `hardbot` difficulty tier, and deliberate
  omniscience via `RevealsMap@classic` (self+allies shroud/fog reveal).

Acceptance criterion: **the candidate must win the series from both
spawns** — run `--repeats 4 --swap-bots` minimum (repeat parity alternates
which bot occupies which `mpspawn`). `gamespeed` stays locked at `maximum`
(the maintainer's "maximum game speed" for bot matches, taken literally
2026-09-29 — series before then ran at `insane` and are not win-rate
comparable: OrderLatency also shifts 7 -> 10). A timed-out match
records both sides `lost`, never a fabricated winner.

> ⚠ Validity note (2026-09-28, #611): before `IsEligible` admitted
> `Playable || IsBot`, the `genericbot` master AI saw **no enemy** in
> harness matches (both duelists are `Playable: False` map-side bots) —
> every `hard`-side result predating #611 measures a blind master AI and
> is not a baseline. Fransbot-side records are unaffected: the Frans stack
> never consumed MasterAi.

Under the hood the harness extracts the `.oramap` into a variant dir, adds
the `Referee` seat for the local client, converts `Multi0`/`Multi1` into
map-side bots (`Playable: False` + `Bot:` + `HomeLocation` from the map's
`mpspawn` actors), injects each faction's `StartingUnits` group at the spawn
cell, and layers the duel-gate `rules.yaml` (maximum speed, locked time cap,
restored `MustBeDestroyed`). The packaged map is never modified.

Baseline measured 2026-09-28: `hard` beat `fransbot` on the first clean
match — the franken-bot is not there yet; iterate until it takes the series.
While iterating, prefer the smallest honest lever (targeting, scouting,
economy pacing) over anything resembling a cheat — the acceptance is
"fight smart, not hard".

### Series log (A Nuclear Winter, td_gdi mirror, `--swap-bots`; maximum from 2026-09-29, insane before)

| series | axis | tree | result | notes |
|---|---|---|---|---|
| nw-ab-4 | fransbot vs hard | pre-ResourceMap fix | fransbot 0-4 | `army_value: 0` every match, 0 enemy buildings killed — donor stack tabled by a master-AI-blind `hard` |
| nw-ab-5 | fransbot vs hard | post-ResourceMap (#607) | fransbot 0-2 | expansion live (LandOre/BuildingRefinery commit + retry), first building kill, longest survival ~22k ticks; RAIDs get `bids 0` — recon never reaches the enemy base so no fresh visible targets exist |
| nw-ab-6 | fransbot vs classic | post-#607 | fransbot 0-2 | vs true omniscient `classic`: 0:16 and 0:18 buildings, army$ 0 both — donor stack alone cannot fight the reference |
| nw-ab-7 | hard vs classic | post-#611 | running | first VALID `hard` baseline — pre-#611 hard-side numbers were a blind master AI |
| nw-hard2 | hard vs classic (ra1_soviets mirror) | W1-armed hard (genericbot && hardbot) | hard 1-1 | first post-W1 lane; m1 loss 48067t (units 427:474, assets 65k:184k), m2 WIN 33447t (buildings 54:7, assets 301k:50k); m3/m4 died inside a mid-edit yaml window — invalid |
| nw-hard3 | hard vs classic (ra1_soviets mirror) | W1-armed hard | hard 1-3 | m1 loss 21831t (bld 2:35, rush→turtle latch), m2 loss 35790t (bld 9:53), m3 WIN 26664t (bld 45:4, army 97k:0), m4 loss 25005t (army 0:131k). Pooled ra1_soviets W1: hard 2-4. Wins dominant, losses die early — turtle-latch under continuous threat is the repeated signature |
| nw-classic6 | fransbot vs classic (donor smoke) | 6-capacity ground + probes | fransbot 0-1 | 14410t, bld 2:23; structural proof only: ground1-6 all register + missions distribute in parallel (52 RECON, 15 DEFEND) |
| nw-hard4 | hard vs classic (ra1_soviets mirror) | W2-armed hard (CommandBid+CommanderCore+General publish-only) | hard 1-1, 2 invalid | m1 loss (turtle), m2 WIN; m3/m4 died at ruleset load inside the mid-merge yaml window (17:50Z) — recorded invalid, not signal. Publish-only W2 shows no regression |
| nw-donor-v12931 | fransbot vs classic (donor smoke) | NOVA merge + V1.29.31 re-vendor | fransbot 0-1 | 16102t clean exit: probes fire (publish->bid->dispatch->retreat-on-damage), V1.29.31 MCV/transport ticking, remembered-structure SECURE doctrine live; donor-only diagnostic, not acceptance |
| nw-hard5 | hard vs classic (td_gdi mirror) | W2 on rebased tree (dc438d55e) | hard 1-0 decided, 1 invalid | m2 died at ruleset load in the yaml-before-DLL window (SiegeEvaluatorInfo) — documented as sequencing failure, not code failure |
| nw-hard6 | hard vs classic (td_gdi mirror) | post-#623 rebase + CA-2a telemetry + CA-2b plumbing (OFF) | running | m1 hard WIN 46628t (bld 64:9, decisive +53k, turtle/emergency, 4-5 sq); m2 hard LOSS 74472t (bld 25:82, decisive -64k @60-62k, turtle/emergency, only 2 sq/14k army vs 61k — all losses 0% away); squads=0 heartbeat ~24k WT in m2 → traced to FransCommanderCore AttackAnything draining idle pool below CreateAttackForce thresholds (starvation, no floor; see FINDINGS_2026-09-29_dawn_squad_starvation); m1 attempt-1 + m2 attempt-1 invalid (external kills / stale-Cameo DLL window) |

⚠ nw-ab-4/5 `hard`-side numbers predate #611 (`IsEligible` saw no enemies) —
they read as "hard's squad machinery carries it anyway", not as a fair test.

### Fog-honest capability gaps closed 2026-09-28 (donor stack)

- `ResourceMapBotModule@fransbot` instance (#607) — expansion was inert.
- `ScoutBotModule` multi-instance resolution (#607).
- Strategic-map probe actors (#614) — passability layers inert without them.
- Support-power `Decisions` table ported verbatim (#615) — fransbot had zero
  orders vs the genericbot stack's 210.
- Remaining unset fields swept module-by-module; the benign 0/null defaults
  and the real gaps are filed in `docs/HANDOFF.md` (2026-09-28 EMBER block).
| ca2b-ctrl/ca2b-cand | hard vs classic (td_gdi mirror) | F1 base + CA-2b BehaviourEnabled off/on | running | 8 matches/arm, both orientations, CAMEO_BOT_DEBUG=1; F1 validated: squads=2 by WT9k (was 0-for-74k pre-F1); candidate serving stand-off/commit/retreat orders; flag: remembered defence v=0 projection |
| ca2b-ctrl-max/-cand-max (v1, killed) | hard vs classic (td_gdi mirror) | 372b67825 + BehaviourEnabled off/on, maximum | partial | drivers killed by session restart @11:52; ctrl m1 **hard WON** 15289t (K/D 2.44; decisive +30.8k @10.5-12k; turtle/emergency, raid; bld 31:0), cand m1 never completed (killed mid-flight, no record); v1 ctrl verdict distribution @~WT35k: retreat(predicted-loss) 204, commit 75, free-advance 13, commit-no-defences 11, stand-off 1 — squads form (F1), advisor reads real walls |
| ca2b2-ctrl/ca2b2-cand (v2) | hard vs classic (td_gdi mirror) | 0365e4e9e (+phantom-retry) + BehaviourEnabled off/on, maximum | running | 8 matches/arm, swap orientations, CAMEO_BOT_DEBUG=1; phantom ok+0-retry adopted (NOVA 922b9ba23) |
| ca2b2+ca2b3 (pooled, FINAL) | hard vs classic (td_gdi+td_nod matrix) | pre-#660 lane base (372b67825 lineage) + BehaviourEnabled off/on, maximum, phantom-retry | **ctrl hard 10-7 (58%, Wilson 36-78%) / cand hard 6-11 (35%, Wilson 17-59%)** | n=17/arm across 2 identical-base runs; mirror-faction cells ctrl 8-4 vs cand 4-8 (pooled recount); the loss pattern is faction pairing, not spawn — hard-as-td_gdi went 0-6 vs classic td_nod pooled while hard-as-td_nod went 4-0 vs classic td_gdi, so 'who sits on the strong pairing' drove the mirror-adjacent cells. ca2b3 ran every hard match from home '11,45' (no position swap; coordinator recount on #670 — `player.home`, not `spawn`, is the side key) so the A/B is still fair between arms but silent about spawns; the earlier 'spawn' label was wrong. Verdict telemetry: ctrl computed 220 retreat/29 stand-off/35 commit unserved; cand served verdicts dissolve squads at first retreat -> only 29 retreat/4 stand-off/102 commit recorded and matches end 23% faster (28.8k vs 37.4k ticks). **FLAG VERDICT: BehaviourEnabled LOSES the A/B — stays off.** The advisor reads losing fights correctly but stand-off/retreat cycles cede initiative to the omniscient snowball; §12.6's artillery-first precondition is unmet (army mix: 77% infantry / 5% heavy / 4% artillery) |
| w3ab-ctrl/w3ab-cand (FINAL) | hard vs classic (td_gdi+td_nod matrix) | 66f098f3b + W3 economy swap (cand: 4 CA producers off / 5 Frans producers on), maximum, swap-bots | **cand hard 0-24 (0%) / ctrl hard 9-6 (60% of 15)** | 24-match design per arm (8/8 g/n mirrors + 4/4 cross); cand completed all 24 — lost EVERY match, including all 16 mirror-cell games. Forensics: production starvation, not tactics — FransMcvExpansion never tasks an MCV (`task=0/None, stage=Idle, mcv=0` heartbeat all game), queues idle (idle_queues 3+ from mid-game), deaths_cost ~4-5x kills_cost, army_value 0 at end. ctrl driver died at 15/24 (host restart); n-mirror backfill in flight (matrix 8/8/4/3 -> full). Tally method: filter `player.bot_type=='hard'` — each match writes a row per side, counting both forces a fake 1:1. **F1 VERDICT: FAIL — Frans producer stack stays donor-only; CA economy producers remain armed on `hard`; dawn-w3 arm set never merges.** The §19.1 shared `BotDifficultyLadder` (CA, #672) survives as infrastructure for future controlled ramps. |
| inc3ab-{ctrl,base,all} (FINAL, 2026-10-01) | hard vs classic, td_gdi + td_nod MIRRORS ×8 swapped, A Nuclear Winter, --render fast | ctrl `bea5573a2` / base `dfef889b6` / all = base + 53 switch changes (groups A+B+C) | **ctrl 12-4 (75%, 51-90) · base 9-7 (56%, 33-77) · all 13-3 (81%, 57-93)**; mean length 31,562 / 32,777 / 26,770 t; double-owned units 216 / 0 / 0; order gate base would-refuse 264 crossed 119, all refused 325 crossed 13. **VERDICT: `all` does not lose (leads, wins faster) → groups A+B+C shipped as defaults** (minus the engt-transport re-arm, §19.8; C on every tier, §19.1). `base` alone trails: the machinery pays off with its switches. |

## Engagement log (schema `engagement/1`, EL-0, AI_ARCHITECTURE 12.30)

File `Logs/cameo-ai-engagements.jsonl`, written by `AiEngagementLogWriter` (World actor) from `EngagementLogBotModule`
(Player actor, runs for genericbot AND classic, no `RequiresCondition`). Same writer rules as above: host only, non-replay,
append-only, flushed at game over. Record-only: no orders, no conditions. Every value is an integer; `*_milli` are thousandths.
Two record kinds share the file, told apart by `record`.

**Common ids (both kinds):** `schema`, `record` (`engagement` | `posture`), `game_uid`, `record_id`, `map_uid`, `player`,
`bot_type`, `faction`, `personality` (current).

**`engagement` (one line per closed fight):** `engagement_id`, `start_tick`, `end_tick`, `duration_ticks`, `close_reason`
(`quiet` | `side_gone` | `match_end`), `centroid` ("x,y" cell), `kind` (`defend` | `attack` | `field`), `skirmish` (below 300 value
traded or fewer than 2 deaths; still written).
* `context`: `dist_own_base`, `dist_enemy_base` (cells, -1 unknown), `director_phase`, `director_tension`, `urgency`.
* `seen` (what the bot knew): `predicted_method`, then `start` and `end`, each with `tick`, `own_committed_value`,
  `own_committed_units`, `own_defence_value`, `own_artillery_value`, `enemy_unit_value`, `enemy_units`, `enemy_defence_value`,
  `enemy_defence_count`, `enemy_artillery_value`, `predicted_ratio_milli`, `predicted_own_surviving_permille`,
  `predicted_enemy_surviving_permille`. Visible or frozen enemies only.
* `response` (defend only): `first_own_hurt_tick`, `first_own_mobile_dealt_tick`, `response_ticks` (-1 none), `army_dist_at_start_cells`.
* `tactics`: `approach_angle_deg` (-1 unknown), `approach_units`, `artillery_first`, `defence_killed_before_direct_entry`,
  `into_defences_value`, `suicide_index_milli` (into_defences / max(1, enemy defence value destroyed)), `defence_points`,
  `own_hurt_events`, `own_dealt_events`.
* `outcome`: `own_lost_value`, `own_lost_unit_value`, `own_lost_units`, `own_lost_building_value`, `own_buildings_lost`,
  `enemy_killed_value`, `enemy_killed_unit_value`, `enemy_killed_units`, `enemy_killed_defence_value`, `enemy_killed_defences`,
  `enemy_killed_building_value`, `enemy_buildings_killed`, `enemy_killed_harvester_value`, `enemy_harvesters_killed`,
  `own_lost_by_role` (object role -> value).
* `truth` (OFFLINE ONLY, unfogged, DESIGN 19.13): `start` and `end` with `tick`, `enemy_unit_value`, `enemy_units`,
  `enemy_defence_value`, `enemy_defence_count`; `enemy_loss_value`. Never an input to any decision.
* `score`: `trade_milli` = 1000 (killed - lost) / max(1, killed + lost); `predicted_trade_milli`; `vs_prediction_milli` = trade -
  predicted; `own_building_loss_milli`, `enemy_building_loss_milli` (value-weighted, 2/3 HP fraction lost + 1/3 on death);
  `objective_milli` (defend: 1000 - 2 x own loss; attack: 2 x enemy loss - 1000; field: 0); `total_milli` = (500 trade + 250
  vs_prediction + 250 objective) / 1000 clamped to +-1000. Mirror: `ai_log_common.engagement_score`.

**`posture` (every 250 ticks):** `tick`, `army_centroid`, `army_units`, `army_value`, `dist_own_base`,
`dist_building_under_attack` (last 500 ticks, -1 none), `dispersion_cells`, `dist_seen_enemy_army`, `idle_share_milli`,
`staging_cell` and `army_to_staging_cells` (AI_ARCHITECTURE 12.29 via `IBotArmyStaging`; null when no provider or plan).

Report: `python tools/ai/engagement_report.py <dirs...> [--json]`.
