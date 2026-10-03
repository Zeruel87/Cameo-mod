# AI Duel — A Nuclear Winter

Headless 1v1 bot duel for `tools/ai/run_ai_match_batch.py` (the default
template since 2026-09-28). Terrain donor: **A Nuclear Winter**
(Lucian/AedisToru, `mods/cameo/maps/_ra_a-nuclear-winter.oramap`) — a real
102x72 RA_SNOW map in the **Tournament** category, i.e. a real competitive
duel map: real base geometry, resources, cliffs and the map's own Creeps
hostile to both sides. `map.bin`/`map.png` are donor-verbatim.

Maintainer order (2026-09-28): **all** bot-vs-bot testing runs here — real
map, real spawns, locked `gamespeed: maximum`. No synthetic fixtures. The old
flat `ai_duel_gate_20260928` stays available via `--template` for harness
debugging only.

## The A/B contract

Side A is the current stack ("Frankenstein": genericbot — Cameo + CA + CN
modules, `UseFoggedObservation: true`, fog-honest). Side B is the `classic`
bot type: the pre-Cognition-wave module set re-gated `genericbot ||
classicbot`, the pre-wave `SquadManagerBotModuleCA@generic` config as
`@classic`, the shared `hardbot` tier, and `RevealsMap` on its PlayerActor —
the mandated omniscience handicap. Acceptance for the new stack: beat
classic without map vision. See `docs/HANDOFF.md` 2026-09-28.

## Shape (same engine-verified pattern as ai_duel_gate_20260928)

- `Referee` — `Playable`+`Required` slot for the local client
  (`StartingUnitsClass: empty`; declared `NonCombatant` so it is excluded
  from match records and conquest fails it on tick 1).
- `BotA`/`BotB` — `Playable: False` map-side players (`client == null`
  path), homes = this map's two real mpspawn cells (11,45 / 90,24), hostile
  to each other and to `Creeps`. `Bot:`/`Faction:` are sentinel values the
  harness patches per matchup; starting forces are written into `Actors:` at
  the `AI_DUEL_BOT_UNITS` marker.
- `rules.yaml` — shared duel lock: `-AdaptiveGameSpeed`, `gamespeed: maximum`
  locked, `TimeLimitManager` stalemate cap, `MustBeDestroyed` restored on the
  base classes so elimination is real.

## Caveats measured here

- Sustained sim rate is ~25 tps (vs ~100 on the flat fixture): module-timing
  lines in `debug.log` can be 60-120s apart — the harness `--stall-timeout`
  default was raised to 400s accordingly.
- `render_side_actors` places support units on a fixed +-4 ring around the
  home cell; Nuclear Winter's spawn pockets are open, but if a support unit
  is ever missing in a variant, check the ring cells against `map.png`.
