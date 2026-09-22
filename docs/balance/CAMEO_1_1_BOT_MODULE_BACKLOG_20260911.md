# Cameo 1.1 bot-module backlog

This backlog records the 11 September Astor discussion that Aedis supplied in
`message.txt`. It is planning input, not an implementation or a claim that
the Command & Conquer mod discussed there matches Cameo's engine. Astor's
statement that the mob system now runs well is an unverified external claim;
it needs source review and profiling before any reuse decision.

## What the discussion suggests

- Build armies as role-aware squads and wait for a usable wave instead of
  committing isolated units.
- Put high-health units forward, keep fragile long-range units behind them,
  and use explicit formations.
- Give squads target priorities and coordinate artillery fire with a delayed
  assault window.
- Add air response squads for enemy artillery and increase later Steamroller
  wave sizes within a bounded rule.
- Treat infantry's late-game artillery problem as a separate gameplay design
  question. Terrain cover, structure-attack cover suppression, armor layers,
  secondary HP, piercing and slow regeneration are possible ideas, but none is
  a default Cameo change.
- Keep deterministic class/weapon conventions and hybrid payloads as model
  inputs; do not assume that a reference mod's mob implementation can be
  transplanted without profiling.

## Recommended staged plan

| stage | module | objective | size | acceptance evidence |
|---|---|---|---|---|
| 0 | telemetry and fixtures | Log deterministic seeds, composition, wave timing, target choice, losses and outcome by matchup; build fixed bot scenarios. | Small | Repeatable logs and a before/after comparison without changing bot behavior. |
| 1 | squad roles and formation | Partition available units into assault, screen, support and air-response roles; place durable units ahead of fragile ranged units with an explicit fallback when a role is absent. | Medium | Fixed scenarios show stable role assignment and formation positions; no new omniscience. |
| 2 | target priorities | Give each squad an ordered target policy (artillery, anti-air, production, frontline, or fallback) and expose the selected target in logs. | Medium | Target choice follows the policy under a fixed enemy layout and remains deterministic. |
| 3 | fire-support coordination | Schedule artillery attacks and assault release after a bounded delay or impact signal; cancel or retarget safely when the target disappears. | Medium | A fixture demonstrates artillery-first then assault timing without blocking ordinary attacks. |
| 4 | wave adaptation | Increase Steamroller wave size only under a bounded stockpile/production rule; avoid unbounded queues and preserve recovery after losses. | Medium | Wave sizes, queue pressure and recovery are visible in logs across early and late scenarios. |
| 5 | air response | Dispatch air squads to counter enemy artillery when the bot has an available and legal response; otherwise retain the ground plan. | Medium | Artillery pressure changes air-response decisions in a fixture without granting map-wide vision. |
| 6 | fairness ladder | Keep existing bot advantages initially, then A/B reduce one advantage at a time (vision, production speed, cost, passive income) after the deterministic modules have parity evidence. | Large | Each reduction has a measured win-rate/quality envelope and a reversible configuration boundary. |
| 7 | mob-system research | Profile current Cameo squad/mob alternatives and compare against the claimed CN implementation; do not port a mob system from screenshots or chat claims. | Large | CPU, memory, pathing and per-unit decision costs are measured on representative maps before a design choice. |

## Design boundaries

- This is a Cameo 1.1 backlog. It does not change the current 1.0 rebalance,
  the 29-group armor receipt, or any YAML, bot module, engine or runtime file.
- Machine learning is optional future research, not a dependency for stages
  0–5. Deterministic rules and logs should establish whether a module helps
  before any learning system is considered.
- Removing every bot advantage is not the first step. A staged fairness ladder
  preserves a playable AI while each advantage is measured and reduced only
  after the corresponding module is strong enough.
- Infantry survivability ideas belong in a separate balance/playtest packet.
  Cover must account for terrain and structure-attack context; regeneration,
  secondary HP, piercing and armor bypass must be measured against artillery
  rather than added as a blanket late-game buff.
- The backlog records concepts from the supplied conversation. It does not
  establish code ownership, compatibility, licenses, or runtime performance
  for Astor's or another mod's implementation.

## Current disposition

The backlog is captured for later review. The next actionable Cameo 1.1
research step is stage 0: inventory existing bot hooks and add deterministic
fixture/logging boundaries. Implementation waits until the current 1.0
rebalance candidate and Sunday playtest are stable, as Aedis requested.
