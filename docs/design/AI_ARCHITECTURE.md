# Cameo AI architecture — bot modules, personalities, master module, learning

_Written 2026-08-31. Owner document for everything about how Cameo's bots decide what to do.
[`DESIGN.md`](../DESIGN.md) §19 and §20 keep the binding rules for the personality and composition
systems that already ship; this file is the forward design and the research behind it.
Task queue: [`ROADMAP.md`](ROADMAP.md) section "AI ARCHITECTURE"._

**Most of this document remains a design, not a shipped adaptive system.** Section 1 is verified
fact with source evidence. Sections 2–7 are proposals except the record-only implementation in
§6.2a, delivered on the follow-up branch for coordinator review. Section 8 is outside research. Section 9 records what is
still undecided. Section 10 is the module-by-module build plan and section 11 reconciles the
five-agent research round against sections 1–10. **Section 12 is the maintainer's combined-arms
order of 2026-09-28** (arsenal tracker with self-learning, role ratios, formation, siege, air
doctrine, scouting) mapped onto what ships, with phases CA-1…CA-6 and an owner for each.
Research round 2 — how the strongest RTS bots fight, reason about space, micro, learn and stay
fun, with the phases CP/ZG/IM/UT/MI/OM/LG it adds — is [`AI_DEEP_RESEARCH.md`](AI_DEEP_RESEARCH.md). The §6.2a match logger has runtime and replay
evidence in `docs/audit/ASTRA_REVIEW.md`; this does not validate the proposed decision system.

---

## 0. The goal, stated so it can be checked

A bot that beats a good human by deciding better, not by being given more. Two consequences that
shape every choice in this document:

1. **No economic or production cheats.** Cameo is already close to this. Difficulty is expressed
   purely as `BotLimits` — caps on production structures, refineries and harvesters, plus build
   delay/interval modifiers (`mods/cameo/ai/ai.yaml:37-142`). There is no cash bonus, no resource
   multiplier and no build-speed advantage for bots anywhere in the AI rules; `DefaultCash` is a
   global player setting (`mods/cameo/rules/player.yaml:75`). Difficulty currently *throttles the
   bot's own competence*, which is the honest form of it.
2. **The real cheat is information, and it is still there.** The squad manager scans
   `World.Actors` and filters visibility only through `IVisibilityModifier` — cloak and submersion
   — never through the player's shroud (`OpenRA.Mods.CA/Traits/BotModules/SquadManagerBotModuleCA.cs:226-253,331-345`).
   A bot therefore knows where every enemy unit and building is from tick zero, including inside
   unexplored map. Only the capture and crate modules expose a visibility option at all
   (`CaptureManagerBotModuleCA.cs:49`, `CratePickupBotModule.cs:41`). Any claim that a future
   Cameo bot "wins without cheating" is false until this is addressed, and the strategy-detection
   design in §3 is where it has to be addressed, because a detector that reads the true world
   state cannot be wrong and therefore cannot be beaten by deception.

The second point is the single most important finding in this document. It also makes the AI
*better* rather than worse to fix: an opponent model that can be wrong is what makes scouting,
feints and hidden tech meaningful, and it is what the whole opponent-modelling literature in §8
is about.

### 0a. The acceptance test (maintainer rulings, 2026-09-27)

> *"The new Frankenstein monster AI with no map wide vision [must be] able to beat our existing AI of
> the same difficulty level with map wide vision … every time with any faction. … At least as a
> first step it should win with the same faction on both sides. Later any match up."*

The program is done when this test passes. It is binding and still **unmeasured** (status below).

| | ruling |
|---|---|
| **Candidate** | the new bot (the CA × RV × CN × Fransbot merge), with **no map-wide vision**: every module reads the world only through what its player can see or remembers (§3.1). |
| **Opponent** | the existing bot **at the same difficulty**, **with** map-wide vision, i.e. today's omniscient squad targeting (§0 point 2). |
| **Pass** | the candidate wins **at least 16 of 20** matches, one match per map. |
| **Maps** | the **20 two-player maps in the `Tournament` category**, ordered by player count, then title. There are 21; **Twin Lakes CAMEO** is left out. |
| **Stage 1** | the same faction on both sides. |
| **Stage 2** | any match-up: every faction against every faction. |

The 20 maps (measured 2026-09-28 from each map's `Categories:`, `Title:` and `Playable: True`
count; file in brackets):

1. 16:9 (`16-9.oramap`) · 2. 420 blaze it (`420bzt`) · 3. A Nuclear Winter (`_ra_a-nuclear-winter`) ·
4. Alpine Assault (`AlpineAssault`) · 5. Bombshell Beach (`BombshellBeach`) · 6. Death Valley
(`DeathValley`) · 7. Frozen Rift CAMEO (`frozen_rift_cameo`) · 8. Model 200 (`model-200`) ·
9. Mountain Pass (`MountainPass`) · 10. Northern Lights CAMEO (`NL04`) · 11. Only Blood Is Accepted
(`Only_Blood_Is_Accepted_1v1_BI-4.4`) · 12. Pitfight (`_ra_pitfight`) · 13. Plan B (`plan-b`) ·
14. Proto Blood (`proto_map_blood`) · 15. Proto Desert Night (`proto_map_desert_night`) ·
16. Proto Mediterranean Conflict (`proto_map_mediterranean`) · 17. Proto Snow (`proto_map_snow`) ·
18. Satan's Clutch (`SatansClutch`) · 19. Snowy Woodlands (`SnowyWoodlands`) · 20. Ysmir (`_ra_ysmir`)

**Status 2026-09-28: the test cannot be run yet.** Two pieces are missing from master:
1. **A fog-honesty check.** Nothing verifies "no map-wide vision" across *all* modules;
   `MasterAiBotModule.UseFoggedObservation: true` (`mods/cameo/ai/ai.yaml`) covers only the modules
   that consume the fogged provider, and the squad manager still scans `World.Actors` (§0 point 2).
2. **A match runner** that plays one match per map and records the winner. DAWN's #578 branch has a
   Fransbot versus map; nothing on master plays the 20-map set.

Also, **the candidate must first be able to play every faction.** On 2026-09-28 an Atreides bot
starting from a bare construction yard still built nothing (the power, barracks and production lists
lack the D2k and Outpost2 ids; #588 and the next list-rollout roles fix this).

Speed for the runs: `GameSpeed: maximum` — the top ladder tier — with the dropdown locked
and adaptive speed off (see `LESSONS_LEARNED.md`); promoted from `insane` for unattended
tuning runs (maintainer order 2026-09-29).

---

## 1. Verified facts

Everything in this section was read out of the pinned tree or produced by running the engine's
own resolver. Raw artifacts: `C:\Users\Administrator\research\ai-yaml-experiment\`.

### 1.1 Bot logic is unsynced and may only act by issuing orders

`ModularBot` ticks its modules inside `Sync.RunUnsynced(...)` and states the contract directly:
"Bot logic is not allowed to affect world state, and can only act by issuing orders"
(`engine/OpenRA.Mods.Common/Traits/Player/ModularBot.cs:68-70,86-104`). Modules are activated only
for the client that owns the bot, and not at all in replays (`:66-79`).

Three consequences, all load-bearing:

* A bot module **may** hold arbitrary local state, read files, use `World.LocalRandom`, and write
  logs. None of it can desync, because none of it reaches the simulation except as orders.
* A bot module **may not** grant a condition, set a variable other traits read, or otherwise
  mutate synced state. This is why the personality switch in §4 must travel as an *order*.
* Bot modules exist as traits on every client but only tick on one, so any per-module counter will
  legitimately differ between clients. That is harmless, and it is also why such a counter must
  never feed a synced decision.

**Precedent for the order round-trip already exists in Cameo**, which removes the main risk from
§4: `PlugSpawnerBotModuleCA` queues `new Order("PlacePlugAI", player.PlayerActor, ...)` with a
`TargetString` payload from `IBotTick`, and resolves it in synced code via `IResolveOrder` on the
same trait (`OpenRA.Mods.Cameo/Traits/BotModules/PlugSpawnerBotModuleCA.cs:84-108`).
`ExternalBotOrdersManager` does the same for `IssueOrderToBot`
(`engine/OpenRA.Mods.AS/Traits/BotModules/ExternalBotOrdersManager.cs:120-149`).

### 1.2 How ContentPack ai.yaml actually merges — measured, not assumed

The user's premise was that per-pack bot modules "would be overwritten in the order they are
loaded". The mechanism is more specific than that, and the specifics decide the architecture.
Measured with `.\utility.cmd cameo --resolved-rules Player`, one case at a time, against a
1375-row baseline:

| # | Case | Result |
|---|---|---|
| 0 | Load order | **ContentPack rules resolve BEFORE the global `Rules:` block**, so every `ContentPacks/**/yaml/ai.yaml` is merged before `cameo|ai/ai.yaml` |
| 1 | Pack adds a *new* row to `UnitsToBuild` | **Unions.** 1375 → 1376 rows, new row present alongside all existing ones |
| 2 | Pack sets an *existing* `UnitsToBuild` row | Row keeps the global file's value (void as a measurement — the appended fragment landed at the wrong depth; the conclusion rests on case 3) |
| 3 | Pack sets a scalar the global file also sets (`SquadSize`) | **Global wins.** Resolved `SquadSize` is 3, not the pack's 77; no trace of 77 survives; every other field of the block is intact |
| 4 | Pack declares a *new* instance `SquadManagerBotModuleCA@gdi_test` | **Works.** Both `@rush` and `@gdi_test` resolve, no error or warning |
| 5 | Pack removes a trait the global file defines (`-SquadManagerBotModuleCA@rush`) | **Hard error:** `OpenRA.YamlException: ContentPacks|TiberianDawn/GDI/yaml/ai.yaml:56: There are no elements with key SquadManagerBotModuleCA@rush to remove` |

This matches `MiniYaml.MergePartial`, which recurses into duplicate keys and takes the override
(later) node's value at the leaves (`engine/OpenRA.Game/MiniYaml.cs`), and `FieldLoader`'s
dictionary parsing, which builds a field from whatever nested nodes survived the merge
(`engine/OpenRA.Game/FieldLoader.cs`).

**The rule, stated for implementers:**

> A ContentPack can **add** keys, rows and whole trait instances to a bot module. It can **never
> override** a key the global `ai/ai.yaml` already sets — the global file loads later and wins —
> and it can **never remove** one, which is a load-time crash rather than a silent no-op. Packs
> can, however, override and remove things declared by *earlier* packs, ordered by the `Include:`
> lines in `mod.yaml`.

So the user's instinct is right about the symptom and the fix is not "stop the overwriting": it is
that **the global file must stop declaring anything a pack is supposed to own.** Whatever key the
global file sets is permanently unownable by any pack. This is a subtractive job on
`mods/cameo/ai/ai.yaml`, not primarily an additive one on the 28 pack files.

Case 5 also kills the most obvious layering idiom: a pack cannot opt out of a global default.
Opt-out has to be expressed as a value a pack *adds* (a condition, a prerequisite token, a row
with weight 0 where the consumer treats 0 as "never"), never as a removal.

**Ordering caveat (measured 2026-09-05):** `MiniYaml.MergePartial`
(`engine/OpenRA.Game/MiniYaml.cs:590-643`) appends new dictionary keys in merge order — pack
rows first, then global rows. Moving an existing `UnitsToBuild` row from the global file to a
pack therefore relocates it to the top of the resolved dictionary: the `--resolved-rules` dump
cannot stay byte-identical, though the resolved content (keys + values, and the
`FrozenDictionary` the bot consumes) is identical. Any migration gate must compare *content*,
not dump bytes, or the rows must stay in the global file.

### 1.3 Multi-instance safety is per-consumer, and one consumer is a crash

Multiple same-type modules are fine *iff* every consumer enumerates them. The engine's own bot
modules already do this: `UnitBuilderBotModule`, `McvManagerBotModule`,
`McvExpansionManagerBotModule` and `HarvesterBotModule` all cache arrays of
`IBotRequestUnitProduction` / `IBotPositionsUpdated` / `IBotRequestPauseUnitProduction` via
`TraitsImplementing<T>()`.

The exception, verified: `UnitBuilderBotModuleCA` resolves compositions with
`self.World.WorldActor.TraitOrDefault<UnitCompositionsBotModule>()`
(`OpenRA.Mods.CA/Traits/BotModules/UnitBuilderBotModuleCA.cs:151`), and
`TraitDictionary.GetOrDefault` throws `Actor World has multiple traits of type ...` on the second
instance (`engine/OpenRA.Game/TraitDictionary.cs:178`). Because a disabled `ConditionalTrait`
still lives in the trait dictionary, condition-gating does not save it: five personality-gated
composition modules crash on the first bot tick regardless of which conditions are active.
Credit for this correction goes to the Claude review; my earlier "compositions are personality-
blind because the trait has no condition field" was wrong on the mechanism.

### 1.4 Personality-tagged compositions need no C# at all

Composition eligibility runs through the tech tree:
`techTree.HasPrerequisites(composition.Prerequisites)` (`UnitBuilderBotModuleCA.cs:581`),
`TechTree` gathers `ITechTreePrerequisite` from every actor the player owns including the Player
actor itself, and `ProvidesPrerequisiteInfo : ConditionalTraitInfo, ITechTreePrerequisiteInfo`
yields nothing while disabled (`engine/OpenRA.Mods.Common/Traits/Player/ProvidesPrerequisite.cs:20,61`).
Cameo already relies on exactly this pattern — `ProvidesPrerequisite@botplayer` with
`RequiresCondition: genericbot` gates every bot module in the file (`mods/cameo/ai/ai.yaml:176-178`).

So a condition-gated `ProvidesPrerequisite` per personality plus a token in a composition's
`Prerequisites` gives personality-specific compositions with one composition module, no
`TraitOrDefault` collision, and zero C#. `Prerequisites` is an AND-list, but OR is expressible the
way tech trees always express it: several condition-gated instances providing the same group token
(`personality_aggressive` from both the Rush and Steamroller conditions).

### 1.5 What the reference mods actually have — and the one correction that matters

I previously told the user that CN's personalities are "budget allocators, not switchers". That
was incomplete, and the missing half is the closest existing thing to what the user is asking for.
`CNBotProfileBotModule` (924 lines) has an **`Adaptive` profile** that re-scores and switches
profiles at runtime, with machinery Cameo should copy the shape of:

* candidate scoring per profile, with named weights (`AdaptiveFortificationRushPenalty`,
  `AdaptiveFortificationSteamrollerBonus`, `AdaptiveTechCashRichBonus`, …);
* **hysteresis** as an explicit score bonus for the incumbent (`AdaptiveProfileMomentumBonus`,
  default 0.75) plus a minimum hold time (`AdaptiveMinimumIntentHoldTicks`, 3000) and a
  re-evaluation cooldown (`AdaptiveSwitchCooldownTicks`, 1500);
* an **emergency override** that bypasses hysteresis on a danger spike
  (`AdaptiveEmergencyTurtleDangerThreshold`, checked every 25 ticks);
* earliest-tick and army-ratio gates so a profile cannot be picked before it makes sense
  (`AdaptiveSteamrollerEarliestTick`, `AdaptiveSteamrollerArmyRatio`);
* **team coordination** — a penalty per allied bot already running a profile
  (`TeamAdaptiveCoverageWeight`) so allies diversify;
* observer-only announcements of each switch (`AnnounceProfileToObservers`), the same information
  discipline Cameo adopted in §19.

Its own field documentation contains the lesson worth quoting: momentum must be small enough that
"the signal the profile exists for could never trigger the switch it was written for".

Equally important is what CN does **not** have, which is precisely the user's ask:

* **No per-enemy-player model.** Its fortification signal is a single aggregate,
  `squadManager.KnownEnemyDefenseCount` (`CNBotProfileBotModule.cs:571-572`), not a count per
  opponent. There is no notion of a main target: the string `TargetPlayer` does not occur.
* **No learning and no persistence.** Zero occurrences of `File.`, `Path.Combine`, `Json`, `Save`
  or `WinRate` in the file. Nothing survives the match.

No other reference mod is closer. So dynamic switching has a reference implementation to learn
from; **per-enemy targeting and cross-match learning have none, in any OpenRA mod** — that part is
new work, and §8 is where the outside prior art for it comes from.

"Copy the shape" above means the *numbers and the safeguards*. It does not mean the mechanism:
§1.6 is a second read of the same file, and it shows the mechanism is one Cameo may not use.

### 1.6 CN, read a second time: the numbers hold, the mechanism does not

Verified against the local clone at `crystallized-nexus@30cf70a66`, file
`.modsdk/OpenRA.Mods.CN/Traits/BotModules/CNBotProfileBotModule.cs` unless stated otherwise.

* **The adaptive constants are as quoted in §1.5**: `AdaptiveStaticExposureWeight` 0.25 (`:90`),
  `AdaptiveSwitchCooldownTicks` 1500 (`:96`), `AdaptiveEmergencyCheckInterval` 25 (`:110`),
  `AdaptiveMinimumIntentHoldTicks` 3000 (`:113`), `AdaptiveEmergencyTurtleDangerThreshold` 600
  (`:116`), `AdaptiveEnemyFortifiedDefenses` 6 (`:126`), `AdaptiveProfileMomentumBonus` 0.75
  (`:190`), `TeamAdaptiveCoverageWeight` 1.5 (`:194`).
* **CN switches profiles by granting the condition directly from the bot module.** `SwitchTo`
  revokes the old token and grants the new one on the player actor (`:882-887`); it is reached from
  `IBotTick.BotTick` (`:321`), i.e. from inside `Sync.RunUnsynced`. The initial profile is drawn
  with `world.LocalRandom` in the trait constructor and granted in `Created` (`:307`, `:317-318`,
  `:901-910`). Under §1.1 that is synced state being mutated from unsynced code, on one client, from
  a host-local random draw. I have not tested whether CN desyncs in practice — it may be effectively
  single-client in the modes people play — but the pattern is the one `ModularBot` explicitly
  forbids, so **it is not available to Cameo**. The order bridge in §4.2 and §10.4 is therefore not
  "validated by CN"; it is Cameo's own, and it exists precisely because CN's shortcut is closed to
  us. Two of the research replies asserted the opposite; see §11.2.
* **CN's fortification input is fog-honest contact memory, not omniscience.**
  `UpdateKnownEnemyDefenses` (`Squads/CNSquadManagerBotModule.cs:4101-4145`) records a defence only
  if `building.CanBeViewedByPlayer(Player)`, forgets a remembered cell only when
  `Player.Shroud.IsVisible(cell)` proves it empty, and otherwise keeps what was last seen under fog;
  damage taken also writes the attacker's cell into the same memory (`:975`). So the blanket claim
  that the family's bots are omniscient except for cloak — mine for Cameo in §0.2, and Grok's for the
  family — is true of *targeting* but false of CN's *strategy input*. This matters for sequencing:
  contact memory is the cheapest first step towards §0.2 and it has a working in-family reference,
  while a full shroud gate on squad targeting does not.
* **CN documents its own worst bug in-source, and Cameo would inherit it verbatim** (`:325-332`):
  because there is one squad manager, base builder and MCV manager *per profile*, each gated by a
  condition, a reference cached on the first tick points at an instance the module's own next
  decision disables — "the fortification input read zero for the rest of the match while the active
  squad manager knew of twenty-two enemy emplacements". Cameo's personality squad managers are
  per-personality instances too (§10.2), so any master-module reference to a personality-gated module
  must be re-resolved whenever the cached one is not enabled (`:333-351` is the fix), never cached
  once.

---

## 2. Splitting bot modules across ContentPacks

### 2.1 What "splittable" has to mean here

Cameo ships 28 `ContentPacks/**/yaml/ai.yaml` files, all effectively placeholders, while
`mods/cameo/ai/ai.yaml` holds ~6,440 lines of bot configuration for every faction at once,
including a single 1,375-row `UnitsToBuild` table. The goal is that a pack contributes its own AI
behaviour and can be enabled or disabled independently, with no cross-pack breakage and no
dependence on load order for correctness.

Given §1.2, five mechanisms are available. They are not exclusive; the recommendation uses three.

### 2.2 Option A — pack-owned rows in globally-declared dictionaries

The pack adds rows to a dictionary field the global file declares (`UnitsToBuild`, `UnitLimits`,
`BuildingFractions`, …). Measured to work (case 1).

* **Good:** zero C#, zero new concepts, works today, and it is the natural home for the faction
  data that makes up most of the bulk. Actor names are faction-prefixed, so rows are already
  effectively pack-scoped: a GDI bot never sees a Nod row.
* **Bad:** the global file must not already contain the row (case 3), so this only works after the
  rows are *moved out* of `ai/ai.yaml`. It cannot express per-pack *scalars* at all, because the
  global file's value always wins.
* **Verdict: adopt, for dictionary data only.** This is the mechanical bulk of the migration and
  the one part that is safely delegable.

### 2.3 Option B — pack-owned uniquely-named module instances

The pack declares `SquadManagerBotModuleCA@td_gdi` etc. Measured to work (case 4).

* **Good:** full per-pack control of every field, including scalars.
* **Bad:** it multiplies decision authorities. Two enabled squad managers both form squads from the
  same idle pool; two unit builders both queue production against the same cash. It also duplicates
  the enormous shared type lists per pack, and for the composition module it is a *crash* (§1.3).
* **Verdict: adopt only for modules that are genuinely per-scope specialists, and only when gated
  by a condition that guarantees at most one is enabled.** Never for the composition module.

### 2.4 Option C — prerequisite/condition-gated configuration

The pack contributes tokens and condition-gated traits rather than module configuration, and the
global module reacts (§1.4).

* **Good:** zero C#, no new authorities, and it composes — this is the mechanism that makes
  personality-specific compositions possible at all.
* **Bad:** expressiveness is limited to what a token can gate; AND-only semantics need group
  tokens for OR.
* **Verdict: adopt.** It is the right mechanism for eligibility and membership, not for numbers.

### 2.5 Option D — a fragment registry with an aggregator (needs C#)

Introduce a small multi-instance provider trait — say `BotDataFragment@<pack>` — that packs
declare freely, plus one aggregator that collects every instance with `TraitsImplementing<T>()`
and hands the merged result to the real modules. The engine's bot modules already use exactly this
discovery pattern (§1.3), so the idiom is native rather than invented.

* **Good:** removes load-order sensitivity entirely, makes "which pack contributed this" a
  first-class question (and therefore loggable and auditable), and gives packs scalar control
  through a merge policy the aggregator defines explicitly (max, sum, last, per-scope) instead of
  through whichever file happens to load last.
* **Bad:** new C#, and a merge policy is a new thing to get wrong.
* **Verdict: defer.** It is the right answer *if* option A's constraint (global file must not
  declare the key) proves too restrictive in practice. Do not build it speculatively.

### 2.6 Option E — a generated merged ai.yaml

Keep authoring per-pack and generate the global file with a tool at build time.

* **Good:** arbitrary merge semantics, no engine change.
* **Bad:** a generated 6,000-line file in the tree, a generator to maintain, and the thing the
  game loads stops being the thing a human edited. Cameo's audit tooling already treats the yaml
  as source of truth.
* **Verdict: reject** for runtime configuration.

### 2.7 Recommended target shape

```
mods/cameo/ai/ai.yaml            difficulties, ModularBot types, singleton authorities,
                                 module DECLARATIONS with shared non-faction defaults,
                                 and no faction rows and no pack-ownable scalars
ContentPacks/<pack>/yaml/ai.yaml UnitsToBuild / UnitLimits / BuildingFractions rows for that
                                 pack's actors, its compositions, its personality tokens,
                                 and any pack-scoped specialist module instances
```

Migration order, each step independently verifiable by diffing `--resolved-rules Player` against
the pre-migration dump — the resolved output must be **byte-identical** until behaviour is
deliberately changed:

1. Pick one pack (TD/GDI) and one dictionary (`UnitsToBuild`). Move only that pack's rows out of
   the global file into the pack file. Resolved dump must be unchanged.
2. Repeat per pack for that dictionary, then per dictionary. This is mechanical and delegable.
3. Move compositions and personality tokens to their packs (§1.4).
4. Only then consider option D, and only for a scalar that genuinely needs per-pack values.

**Trap to document loudly** (also going into `LESSONS_LEARNED.md`): moving a row out of the global
file is only safe if no *other* file still sets it, and a pack cannot remove a global default
without a load-time crash. The failure mode of a partial migration is silent — the global value
just keeps winning — which is why every step is gated on the resolved-rules diff rather than on
reading the yaml.

### 2.7a Status (2026-09-27, AI architect: Claude)

Measured on master `28cf7b404` with `tools/audit/miniyaml` (rule 8e): the central `ai.yaml` held
**7,151 actor-id references**. **2,680** are dictionary rows (12 fields, e.g. `UnitsToBuild` 1,436,
`BuildingFractions` 402, `BuildingLimits` 250). **4,471** are list entries (41 fields, e.g.
`GuerrillaTypes` 1,265, `ExcludeFromSquadsTypes` 510, `HighValueTargetTypes` 500). **0 of 28**
pack `ai.yaml` files held live config. They held a stale "cannot be split" note plus commented
copies of the rows, which is a second copy that drifts.

* **Dictionaries: built.** `tools/packs/split_ai_rows.py` moves every row whose key is an actor
  defined in exactly one pack into that pack's `yaml/ai.yaml`, under the same trait instance and
  field. It adds the `content.yaml` include when the pack had no ai file; 13 packs had none, and
  without the include their rows would silently vanish. **2,646 of the 2,680 rows are movable.**
  The rest are keyed by actors defined in no pack or in several. `tools/packs/compare_resolved.py`
  is the gate: it compares the engine's `--resolved-rules Player` before and after, as content.
  **Pilot measured: TD/GDI, 100 rows, 7,054 resolved keys before and after, 0 differences.** The
  all-pack apply is prepared but not committed: its engine verification is still pending.
* **Lists: not movable in yaml** (§2.8).

### 2.8 Lists: derive the membership, don't enumerate it

A pack cannot append to a list that another file sets. MiniYaml merges a scalar value by
override, and the central file loads last (§1.2). A list therefore cannot be split by moving
lines. As long as the central file names every faction's ids, two things break. A game that
doesn't load faction X still carries ids for X's actors: that is a lint error today and a
KeyNotFound the day loading becomes dynamic. And a pack author has to edit the central file to
add a unit, which is exactly the coupling ContentPacks exist to remove.

Three mechanisms were considered:

| | Mechanism | Pack edits | C# | Verdict |
|---|---|---|---|---|
| **A** | **Roles on the actor.** Each pack's unit yaml says what the unit *is for* (`BotRoles: Guerrilla, AntiAir`). Mechanical roles are **derived** from traits and need no yaml (Harvester → harvester, Aircraft → air unit, a naval locomotor → naval, Refinery, conyard, MCV, power, barracks). At rules load, one Cameo trait (`BotRoleSets`, `IRulesetLoaded`) adds each role's actors into the module lists that role feeds, through a role → (module, field) table. | on the pack's own actors only | one new trait; **zero edits to CA files** (Frankenstein and CA sync stay safe) | **RULED 2026-09-27 (maintainer): adopt** |
| B | Engine list-append syntax (`GuerrillaTypes+: …`) in cameo-engine's MiniYaml | 5× per personality instance, per pack | engine patch | rejected: duplicates every list ×5 and forks the yaml language |
| C | Every consumer reads `Info.X ∪ roles(X)` | on the pack's own actors | edits at every read site in ~15 CA files | rejected: conflicts with every CA sync |

Why A fits the rulings already made. The raid-unit ruling (2026-09-27: guerrilla = fast/light,
*generated from traits*) is a derived role. EMBER's 6g `BotTargetTags` already derives targeting
tags from rules. An unloaded pack contributes no actors, so it contributes no ids, and the lists
become plug and play automatically. Mechanism A **replaces** each target field's value once, at
rules load, with a new set of the field's own type (old ∪ role members), identically on every
client, so it is sync-safe. It follows `ScaledBullet`'s derive-at-load idiom. Replacing rather than
mutating is required: `BaseBuilderBotModuleCA`'s lists are already `FrozenSet` on master.

**Built: `BotRoleSets` (Player) + `BotRoles` (actor)**, in `OpenRA.Mods.Cameo/Traits/BotModules/BotRoleSets.cs`.
The yaml has `DeriveHas` / `DeriveNot` / `Exclude` / `Targets` per role, and only roles listed
under `Apply` change anything. `DeriveHasField` / `DeriveNotField` add **field predicates**:
`Trait.Field any v1|v2` (the field holds at least one listed value) or `Trait.Field only v1|v2`
(it holds values, and all of them are listed). They're read by reflection at rules load, and a
predicate that no trait can satisfy fails the load, so a typo can't silently match nothing. This
is the primitive DAWN's Fransbot field spec (Class B: `Mobile.Locomotor`, `Production.Produces`)
builds on. Every other role **reports** to `bot-roles.log`: its member count,
what it would add, and what is written but not in the role. `tools/ai/derive_roles_preview.py`
predicts the same numbers without booting a match: it re-implements `ResolveMembers` in
Python (trait base-class expansion from the C# sources, the `Weapons.ValidTargets` union over
`RequiresCondition`-enabled armaments via a full NoVariables boolean evaluator, C# field
defaults, explicit `BotRoles` members, and the fieldSeen typo check — an unresolvable
predicate field exits 1), and `--compare` diffs each role against its written `Targets`
lists — the review gate before anything joins `Apply`. **First report (2026-09-27, report-only):**

| Role → target | Written | Would add | Written, not derived |
|---|---|---|---|
| harvester → `HarvesterBotModuleCA` / `ResourceMapBotModule.HarvesterTypes` | 25 / 26 | 9: the D2k spice harvesters (atreides, harkonnen, corrino), Outpost 2 cargo trucks (Eden, Plymouth), `futuretech_prospectormk2`, `ra1_soviets_heavyindustrialminer`, `tkm_templateharvesterraname`, `wc2_humans_militiapeasant` | 0 / 1 (`naxis_slaveoverseer`) |
| refinery → 3 `RefineryTypes` fields | 28–32 | 10–14: the D2k refineries, the Outpost 2 smelters, the StarCraft resource depots (`protoss_nexus`, `terran_commandcenter`, `zerg_hatchery`: also yards), the Warcraft II oil refineries | 4 (`chsupply`, `glsupply`, `usasupply`, `refinery`) |
| mcv → `McvTypes` | 35 | 10: the D2k MCVs, Outpost 2 convecs, **and false hits**: `ra1_soviets_stalinfist`, `tkm_flakbus`, `tkm_trenchtank`, `tkm_trenchtruck`, `ts_nod_shadowteam` (they transform, but not into a yard) | 0 |
| conyard → `ConstructionYardTypes` | 28 | 5: the D2k yards, the Outpost 2 structure factories | 2 (`zerg_hive`, `zerg_lair`) |

Derivation only counts **producible** actors: `Buildable` **with a Queue**. Spawned slaves such as
`YRSLAV` and `tkmworker` carry a queueless `Buildable` for their tooltip. Their master miner drives
them, so they're no one's harvester. Without that rule the harvester role would have added both.

What an unlisted actor costs depends on the module. The lists are looked up **by name**
(`ActorIndex.OwnerAndNames…`), but not every use is by name:

* **Harvester:** `HarvesterBotModuleCA` sends *every* `Harvester`-trait actor out to harvest
  (`ActorsHavingTrait<Harvester>`), listed or not. The name list controls the **count**, **which
  harvester to build** (`GetBuildableInfoByCommonName`, a random pick among the buildable members)
  and the retreat-when-attacked response. A faction whose harvester isn't listed counts zero, and the
  module has nothing buildable to request. The same happens after a switch makes the listed type
  unbuildable: RA1's Industrial Efficiency doctrine replaces `ra1_soviets_oretruck` with the unlisted
  heavy industrial miner, and FutureTech's promotion does the same with `futuretech_prospectormk2`.
* **Refinery and conyard: the bot is inert.** `BaseBuilderBotModuleCA.PauseUnitProduction` is
  `!HasMinimalRefineryCount()` (BaseBuilderBotModuleCA.cs:395), a by-name count. A faction whose
  refinery isn't listed keeps **unit production paused for the whole game**, and a yard that isn't
  listed gives the base builder nothing to build from. That applies to **Atreides, Harkonnen,
  Corrino, Eden and Plymouth**. Measured on `ai_harvester_gate_20260927`: a hard Atreides bot with a
  yard, a refinery, a heavy factory and 10,000 credits spent **nothing in 6,000 ticks**. The
  refinery and conyard roles fix it (applied together; see the table below). The same by-name
  count had also left `HarvesterBotModuleCA` without `ordos_refineryordos` and
  `schwarzermond_orerefinery`, so those two bots aimed for a single harvester.
* **Refinery: which refinery gets built.** `BaseBuilderQueueManagerCA.GetProducibleBuilding`
  picks **at random** among the buildable `RefineryTypes`. A water-only refinery (the WC2 oil
  refineries) would be chosen about half the time on any map, so the role excludes it with
  `DeriveNotField: refinery: Building.TerrainTypes only Water`. `only`, not `any`:
  `steelconsortium_consortiumrefinery` can be placed on land *and* water, and it stays. Yards that
  are also resource depots (StarCraft Nexus, Command Center, Hatchery) are excluded with
  `DeriveNot: BaseBuilding`. They were never written as refineries, so nothing changes for them.

Each role is applied only after its additions are reviewed and a match with an affected faction
confirms it. False hits are best removed by a tighter **derivation rule** (the producible rule
above). `Exclude` names ids centrally, so it's a last resort. The "written, not derived" actors get a
`BotRoles` line in their own pack. Only then does the central list shrink.

Order: the derived roles first (they remove the most ids with no yaml at all), then `BotRoles` on
the judgment lists (`HighValueTargetTypes`, `BigAirThreats`, `ExcludeFromSquadsTypes`). A list is
then emptied in the central file. Progress metric: actor ids in the central `ai.yaml`, lower-only,
→ 0. It was **7,151** before the pack split. Measure it with `python tools/ai/count_central_ids.py`,
which counts only ids of loaded actors (a node key or a list entry): **4,530** on `e9d500212` (after
#574), **4,480** after the harvester role, and **4,092** after refinery + conyard and the squad exclusion.

**Applied roles** (each needs a match with an affected faction; refinery and conyard went in together,
because a bot with neither listed stays paused):

| Role | Applied | Central ids removed | Evidence |
|---|---|---|---|
| harvester | 2026-09-27 | 50: `HarvesterBotModuleCA.HarvesterTypes` emptied, and `ResourceMapBotModule.HarvesterTypes` reduced to `naxis_slaveoverseer` (a slave whip with no `Harvester` trait; kept so its behaviour doesn't change) | `ai_harvester_gate_20260927`, 4 paired runs to tick 6000: TKM (refinery listed, harvester not) **built +1, +1 without the role and +5, +6 with it**. Atreides built 0 either way: it needs refinery + conyard. `bot-roles.log`: `34 members, 0 written; ADDED 34` |
| refinery + conyard, and harvester → `SquadManagerBotModuleCA.ExcludeFromSquadsTypes` | 2026-09-27 | 388: `HarvesterBotModuleCA.RefineryTypes` emptied; the other two `RefineryTypes` keep only `wc2_humans_townhall`/`wc2_orcs_greathall` (refinery-yards); the 7 `ConstructionYardTypes` lists keep only `zerg_hive`/`zerg_lair` (and `td_gdi_defenserig` in `McvExpansionManagerBotModule`); 4 dead ids deleted (`chsupply`, `glsupply`, `usasupply`, `refinery`); 26 harvesters × 5 personalities out of `ExcludeFromSquadsTypes` | `ai_harvester_gate_20260927` to tick 6000: the Atreides bot owned **7 → 7** actors (inert) with the harvester role only and **11 → 22/24** with these roles, +2 harvesters built in both runs; its harvesters (`far`: more than 25 cells from base) were **4 of 4 far by tick 6000 without** the `ExcludeFromSquadsTypes` target, drafted into attack squads as the maintainer saw, and **0 in 4 of 4 runs with it**; the same gap already existed on master for `ra1_soviets_heavyindustrialminer`, `futuretech_prospectormk2` and `wc2_humans_militiapeasant`. `bot-roles.log`: 31 refinery and 31 conyard members |

**Interim repair (2026-09-28, EMBER, `devin/ember/ai-faction-wiring`):** the "would add" set was
a live bug — the five newest factions were inert because their ids were in no central list. The
ids were hand-appended (119 ids across 66 rows, all verified defined) until `Apply:` drains them;
`Apply` unions into set types so the enumeration dedupe-composes with the role mechanism. The
table's "written" column therefore now includes these ids — do not re-review them as pending
additions.

**Where the central ids are (measured 2026-09-29, master `f37342668`: 5,825).** The metric went
**up** from 4,092, and nothing caught it, because `count_central_ids.py` is in no gate: +670 from
#588's interim repair (4,601 after `06c74eff4` lowercased it), +580 from `1d754587f`
(`SquadManagerBotModuleCA@classic`) and +644 from `3fc9e7e5f` (`SquadManagerBotModuleCA@guerrilla`).
Every personality block carries its **own full copy** of the squad lists, so each new personality
adds ~600 ids. The seven `SquadManagerBotModuleCA` copies hold ~4,270 of the 5,746 list entries:
`GuerrillaTypes` 1,776 (254 × 7), `HighValueTargetTypes` 794, `ExcludeFromSquadsTypes` 745,
`BigAirThreats` 284, `AirUnitsTypes` 222, `NavalUnitsTypes` 215, `StaticAntiAirTypes` 177. A role
that targets a SquadManager field drains all seven copies at once, so the squad lists come first;
the base-builder lists (`PowerTypes` 33, `BarracksTypes` 30, `ProductionTypes` 88) are worth far
less. **Ratchet since 2026-09-29:** `tools/audit/audit_central_ids.py` (in `run_all.sh`) fails when
the count rises above its `CEILING` (4,289 after the guerrilla role); lower it in the commit that
lowers the count, never raise it.

### 2.8a The guerrilla role: generated onto the actors, because the band is per faction

**Ruled 2026-09-27:** guerrilla (raid) units are fast/light only, generated from traits, never
hand-typed (AI_SYNTHESIS.md §3.1). **Bands ruled 2026-09-29 (maintainer, from four measured
options):** a unit is a guerrilla when it is in the **fastest third** of its own faction's infantry
(or vehicles) **and** costs **at most that group's median**.

The band is relative to the *faction*, and the bot cannot see ContentPacks at rules load, so
`BotRoleSets` cannot compute it. `tools/ai/derive_guerrilla_roles.py` computes it offline (the
faction is the pack, `ContentPacks/<Theme>/<Faction>/`; an actor still in a central rules file is
`<file stem>/<id prefix>`, e.g. `outpost2/eden`) and writes `BotRoles: Roles: guerrilla` on the
actor **in its own file**. That keeps the id out of `ai.yaml` (plug and play) and the unit list
out of human hands. `tools/audit/audit_guerrilla_roles.py` (in `run_all.sh`) reruns it with
`--check` and fails on any drift.

The pool, per faction and per infantry/vehicle group: producible (a queue some trait `Produces` or
some `*ProductionQueue` declares: no factory makes the `Disabled` queue, and the Zerg queue
is a player queue), armed with a weapon that can hurt an enemy (`scrin_repair_drone`'s beam is
ally-only), ground-mobile (not `naval` or `subterranean`), not an engineer, saboteur or spy
(`Captures` with a `building` type, or `Infiltrates`: every infantryman also `Captures`
`ra2garrison`), and not from the artillery, artillery-tank or fire-support template (§12.4a).
**Result: 154 actors in 37 factions, 57 infantry and 97 vehicles, 1–8 per faction; 12 of them
live in central rules files (Outpost 2, TS, WC2).**

Two traps the generator handles, both caught while building it:
* **A tag leaks to children.** An actor that inherits another actor inherits its `BotRoles`:
  the Plymouth Lynx chassis is in the band and the heavier Tiger (`PLYMOUTH_TIGER_*`) that
  inherits it is not. The generator compares the **resolved** roles and writes `-BotRoles:` on
  such a child (10 today), so `--check` also catches a new child of a guerrilla.
* **A child `Roles:` replaces the parent's.** A new block repeats every role the actor keeps.

**Applied (branch `claude/role_guerrilla_apply`, lands after its Nuclear Winter A/B):** the
role targets the **six personality instances only**, `SquadManagerBotModuleCA@rush.GuerrillaTypes`
… `@guerrilla.GuerrillaTypes`. `Targets` gained the `TraitType@instance.Field` form for this, so
`@classic`, the A/B reference, keeps its written 254-id list and does not move. Their six written
lists are deleted: **5,825 → 4,289 central ids**. Behaviour changes: 254 raiders → 154, and the 51
aircraft leave the ground guerrilla squad. `bot-roles.log` shows `154 members, 0 written; ADDED 154`
on each of the six and no `@classic` line.

### 2.8b Generalising the whole file: tags on templates, numbers per building type (ruled 2026-09-29)

**Maintainer question:** can `ai.yaml` stop listing units and buildings everywhere, and instead fill
itself at runtime from tags on the templates, so that each faction's folder is complete on its own?
Yes. The file splits into four layers, and each one gets the same answer: the C# derives the value
at rules load from the actors that are loaded, and a pack writes only a deliberate exception.

1. **Lists** (§2.8, built): roles derived from traits or declared on templates and actors. A role
   fills every personality instance at once. That matters because MiniYaml has no inheritance for
   a trait node inside `Player`, so yaml alone cannot share one list between personalities.
2. **Per-building numbers** (new). Measured over the 34 packs' ~940 rows, by building type derived
   from traits:

   | field | uniform by type |
   |---|---|
   | `BuildingIntervals` | factory, refinery, barracks **100 %** (1500) |
   | `BuildingLimits` | refinery **100 %** (10), radar **100 %** (1), repair **100 %** (1); factory and barracks 77 % (10) |
   | `BuildingFractions` | radar and repair **100 %** (1), superweapon 83 % (1), refinery 82 % (15), barracks 74 % (15) |
   | `BuildingDelays` | repair **100 %** (4500), radar 86 % (3000) |

   **Ruled: defaults per building type, exceptions kept.** One line per type in the central file
   (e.g. `refinery: Fraction 15, Limit 10, Interval 1500`) fills every loaded building of that
   type. A pack row that equals its type default is deleted. A row that differs stays in its pack
   as an explicit override, and the list of overrides goes to the maintainer for review.
   ⚠ **Buildings with no row at all DO change** (and they need the A/B): the bot never plans
   them today. Measured: Scrin's `scrin_extractor`, `scrin_warp_gate` and `scrin_portal`
   (refinery, vehicle factory, barracks); Outpost 2's smelters, vehicle factories,
   consumer/arachnid factories, garages and spaceports; 8 naval yards (the base builder may place
   those through its water logic instead, so check that first).
   **Which type a building is: tag the templates** (the maintainer's suggestion), not trait
   heuristics, which mislabel e.g. `EDEN_RESIDENCE` as radar. Template coverage of producible
   buildings: `^RepairFacility` 18/18, `^IsWeaponFactory` 35/38, `^IsShipyard` 17/18, `^Refinery`
   33/34, `^IsAircraftFactory` 28/31, `^RadarBuilding` 18/20, `^PowerPlant` 30/34. There is **no
   barracks template** (0/35: a new `^IsBarracks` is needed), and `^Superweapon` is unreliable
   (14/35, and 20 non-superweapons inherit it), so that type stays trait-derived.
3. **Unit production weights** (`UnitsToBuild`, 1,421 rows; 67 % of them weight 1). **Ruled: derive
   them from stats, after CA-3.** The personality sets a role mix (§12.5); a unit's weight follows
   from its derived role and Versus profile. The hand rows stay until the derived mix wins an A/B.
   CA-3 is NOVA's; the roles come from this lane.
   **UW-1 implemented** (`nova/derived-unit-weights`): `UnitBuilderBotModuleCA.UseDerivedUnitWeights`
   (default **false**; switch group `I_derived_unit_weights`) derives the table as
   `max(1, round(share[r] x strength[u] / mean strength of the candidates sharing r))` where `r` is
   the unit's primary role (`IBotUnitRoles.PrimaryRoleOf`, combat taxonomy only), `share[r]` is the
   `RoleMix` value or `RoleMixRoleFloorPct`, and `strength[u]` is the best weapon's
   `DamagePerTick x mean(Versus)/100` floored at 1 (`BotUnitProfiles`, own-side stats only — no
   enemy enumerated). The yaml rows stay the membership gate and pass through verbatim for unroled
   units; an active composition still wins; flag off, absent mix or absent provider return the yaml
   dict byte-identical. Cached on the (mix, floorPct) reference so a personality switch rebuilds.
4. **Per-unit squad settings.** `AirSquadTargetTypes` is written 5 times in 17 packs, identically
   (32 aircraft, 0 differences). **The `@guerrilla` personality never got the rows**, so its air
   squads lack the setting for every one of them; `@classic` carries its own 28 rows in the central
   file. The value (Ground / Aircraft / Naval) follows from each aircraft's weapons, so it can be
   derived, which fixes the gap and removes the copies.

The end state for ContentPacks: a pack holds its actors, and their tags come from the templates; an
unloaded pack contributes nothing, and no faction needs its own `ai.yaml`.

### 2.9 The empty `ai.yaml`: the plan (maintainer goal 2026-09-29) — binding goal

**Goal.** The central `mods/cameo/ai/ai.yaml` keeps only module wiring, tuning numbers and
*type* tables, with **zero actor ids**. At rules load the bot fills every list and every
per-actor table from tags on the templates and actors that are actually loaded. A ContentPack's own
`ai.yaml` carries only that faction's genuine exceptions. The bot keeps **today's behaviour**,
except for deliberate, listed fixes (Outpost 2 and Scrin wiring, the guerrilla band). Unit production
learns across matches instead of using fixed numbers. **Standing rule:** never add an actor id to the
central file to fix something; add a role, a tag or a type row (TASK_INDEX already says so).

**Why the C# must do it.** Packs load first and the central file last, so a pack cannot append to a
central list or override a central scalar. MiniYaml also cannot share a trait node between the
personality blocks. §2.8 therefore fills the fields at rules load, the `ScaledBullet` derive-at-load
idiom: identical on every client, and sync-safe.

**The layers**

| layer | today | target |
|---|---|---|
| lists (harvester, guerrilla, AA, ships, …) | ids × 7 personality copies | roles from traits/templates, one role set fills all personalities (`BotRoleSets`, §2.8/§2.8a); `@instance` targets keep the A/B reference apart |
| per-building numbers (fractions, limits, delays, intervals) | ~940 pack rows | one row per **building type × game family**; pack rows only for real exceptions (§2.8b) |
| unit production weights (`UnitsToBuild`) | 1,421 static pack rows | derived and **learned** (below) |
| per-unit squad settings (`AirSquadTargetTypes`, …) | 5 copies per pack, missing for `@guerrilla` | derived from the unit's weapons |

**Building type.** A building's type is declared by a `BotRoles` tag on its template:
`^Refinery`, `^IsWeaponFactory`, `^IsAircraftFactory`, `^IsShipyard`, `^RadarBuilding`,
`^RepairFacility`, `^PowerPlant`, and a new `^IsBarracks` (none exists: 0/35). Without a template
tag, the type is derived from traits, and a building with several roles takes the **first** of
conyard > epic > airfield > navalyard > factory > barracks > refinery > power > radar > repair.
Measured: 82 producible buildings carry several roles, and the precedence settles almost all of
them. Every C&C yard is also power and radar → conyard; helipads, airfields and naval yards also
repair or rearm → their production role; the RA2 Air Force Command HQ (airfield + radar +
repair) → **airfield** (maintainer's example). **Exceptions ruled 2026-09-29:**
* StarCraft/Warcraft main halls (Nexus, Command Center, Hatchery, Town Hall, Great Hall) →
  **conyard only**, kept out of the refinery lists as today.
* WC2 Gnomish Inventor, Goblin Alchemist, Zerg Infested Command Center → **factory**.
* `scrin_warp_chasm` → its own **epic** type: it produces `ScrinAdvancedVehicle`,
  `ScrinWarpAircraft` and `ScrinCapitalAircraft` (the Hexapod). **One per player is a rule of the
  actor, not of the bot** (maintainer 2026-09-29): it had no build limit at all, and #636 gives it
  `Buildable.BuildLimit: 1`. The epic type's bot row therefore needs no limit of its own. Scrin's
  vehicle factory is the Warp Gate; its airfield is the Gravity Stabilizer.
* `futuretech_launchpad` → **airfield**. It produces only aircraft; an early scan matched the "ship"
  in `futuretech_harbingergunship`. Queue names must be compared whole, never as substrings.

**Game family.** C&C buildings are uniform (refinery limit 10 in 24/24 packs, radar 1 in 22/24,
conyard fraction 5 in 20/20). StarCraft and Warcraft II scale differently (supply buildings limit 50
against C&C's 1, refinery fractions 20–30 against 15), and Outpost 2 has **no rows at all**. The
type table therefore has one column per family: `cnc` (default), `starcraft`, `warcraft`, `outpost2`.
The family is a tag on the family's building base template: `^OP2Building` exists; StarCraft and
Warcraft II share no family template (measured), so each race's building base gets the tag.

**Units: learned, not listed.** A unit's production weight at match start is

    weight(u) = mix[personality][role(u)] / |loaded units of that faction in role(u)|
                × prior(own faction, enemy faction, u) × trade(u, this match)

(With several enemies or allies `prior` becomes General × Enemies × Allies, and a team-gap factor
joins it: §6.4a.)

* `role(u)` comes from §12.4 (frontline, anti-infantry, anti-armour, artillery, AA, air, scout, …).
* `mix` is one small table per personality, roles × shares, with **no unit ids**. That is how the
  personalities differ without copying a unit list. It starts calibrated from today's
  `UnitsToBuild` role shares, so the first derived weights reproduce today's production.
* `prior` is the cross-match memory ruled in DESIGN §19.2: the committed, offline-fitted
  `mods/cameo/ai/learned/arsenal_priors.yaml` (CA-1b fitter over the CA-1 ledgers). **Release
  builds only read it**, so every player meets the same bot; learning writes only on dev builds
  and harness training runs, and developers commit the result (DESIGN §19.2, amended 2026-09-29).
  It is read at match start only (§6.1), keyed by faction, never by player, and 1.0 where nothing
  is known. ⛔ It is applied inside the host's running bot, never written into rules at load:
  bots run only on the host (`Player.cs:223`), but rules load on every client.
* `trade` is the in-match trade ratio per role or type (§12.3), smoothed toward the prior.

Ruled 2026-09-29: the hand `UnitsToBuild` rows stay until the derived weights win a Nuclear Winter
A/B, after CA-3 (NOVA) supplies the role mix.

**The equivalence gate ("same functionality as now").** The Python resolver cannot see what the C#
fills at load, so phase P0 adds an engine-side dump: after rules load, every list and table field of
every bot module on `Player`, one line per field and instance. A diff tool compares two dumps.
Every phase must diff **empty** against the previous one, except its listed deliberate changes, and
must also pass the boot gate. A phase that changes behaviour needs the Nuclear Winter A/B.

**Phases**

| # | step | gate |
|---|---|---|
| P0 ✅ | **built 2026-09-29:** `BotModuleFieldDump` (opt-in, `CAMEO_DUMP_BOT_MODULES=1`, called at the end of `BotRoleSets` load) + `tools/ai/dump_bot_modules.py` (boots a worktree, isolated support dir, graceful close) + `tools/ai/diff_bot_modules.py` (`--allow` for a phase's declared changes) | dumped twice: 2,168 fields identical; negative control (`guerrilla` out of `Apply`) flags exactly 7 fields |
| P1 | fix `count_central_ids.py` case handling (ids are lowercased at load, so `eden_*`/`plymouth_*` are live, not dead); delete the truly dead ids (`asianalliance_asian*`, `d2k_*`, `ra1_allies_allied*`, …) | dump diff empty |
| P2 | building type and family tags on the templates, `^IsBarracks`, the exceptions above | dump diff empty (tags only) |
| P3 | type × family defaults fill the four building tables; pack rows equal to their default deleted, the others kept as exceptions; Outpost 2 and Scrin gain rows | dump diff = only the no-row buildings; A/B with an Outpost 2 and a Scrin bot |
| P4 | the remaining ~40 list fields → roles; the personality blocks keep only numbers | dump diff empty |
| P5 | `AirSquadTargetTypes` and other per-unit settings from weapons | dump diff = only `@guerrilla`'s missing rows |
| P6 | derived and learned unit weights (after CA-3) | A/B |
| P7 | the packs' `ai.yaml` keep only exceptions; the central id count reaches 0 | `audit_central_ids` CEILING 0 |

---

## 3. Reading the enemy: the observation model

The personality manager is only as good as its inputs, and the inputs are where the no-cheat goal
is won or lost (§0).

### 3.1 Fogged observation, deliberately

Every signal below must be computed from **what the bot is entitled to know**: actors currently
visible, plus a decaying memory of actors seen earlier. Concretely, gate scanning on
`player.Shroud.IsVisible`/`IsExplored` for the cell, keep a per-enemy `LastSeen` record with a
tick stamp, and let confidence decay with age rather than snapping to zero. This is a change of
*policy*, not of plumbing: the scan loops already exist, they simply don't filter on shroud today.

Two honest consequences to accept up front: a fogged bot will sometimes attack into a defence it
should have scouted, and it needs scouting to play well — which is why OpenHV's `ScoutBotModule`
stops being a nice-to-have and becomes a dependency of this design. Cameo has no scouting
behaviour at all today.

### 3.2 Per-enemy signals

For **each** enemy player, tracked independently (this is the part CN does not have):

| Signal | Derivation | Feeds |
|---|---|---|
| Static defence count / value | visible defensive buildings owned by that player | Steamroller, artillery demand |
| Army value and composition mix | visible combat units, by class (inf/veh/air/naval) | counter-composition, AA demand |
| Tech level | highest-tier visible production and tech buildings | Tech matching |
| Expansion count | distinct visible base clusters / refineries | Guerrilla |
| Economy proxy | visible harvester count × refinery count | boom detection |
| Aggression | our losses attributable to that player over a window | Turtle, target switching |
| Proximity / reachability | path distance from our base to their nearest cluster | target feasibility |
| Superweapon presence | visible superweapon structures | urgency override |
| Cloak/stealth reliance | share of seen units with stealth traits | detector demand |
| Confidence | age of the newest observation for that player | damping on everything above |

`PlayerStatistics` (`engine/OpenRA.Mods.Common/Traits/Player/PlayerStatistics.cs`) gives
`KillsCost`, `DeathsCost`, `ArmyValue`, `AssetsValue`, `Income` per player, which is useful for
end-of-match logging but is **aggregate, not pairwise** — it cannot say "player 3 is the one
killing my units". Pairwise attribution needs the master module to keep its own ledger, keyed by
attacker owner, which it may do freely under §1.1.

### 3.3 Derived global signals

Own army value vs summed visible enemy army value; own income trend; whether we are ahead or
behind on tech; whether any of our production is dead; map control proxy (owned/visible resource
patches). CN's danger score is the precedent for the shape.

---

## 4. The personality manager

### 4.1 What a personality is, extended

A personality is a condition that selects one of six `SquadManagerBotModuleCA` instances
(§19). The sixth — **Guerrilla**, the missing personality the user named — is now wired end
to end (2026-09-28, EMBER): `personality-guerrilla` joined the controller's default
`Conditions`, `SquadManagerBotModuleCA@guerrilla` fields the small-squad harassment tuning
(`JoinGuerrilla: 100`, `IndirectRouteChance: 60`, `StageBeforeAssault: false`, `PreferMainTarget:
false`, 700-tick attack cadence, `HarasserTypes` — the dormant CA HVT-strike list — finally
populated with the cross-faction elite/commando roster), and the observer notification exists. Its trigger was already in the master module:
`ExpansionClusters >= GuerrillaMinClusters` on the main target yields `guerrilla` — an enemy
spread across many expansion clusters gets its economy raided from several directions instead
of meeting one blob.

### 4.2 The switch mechanism, given §1.1

The manager cannot grant a condition. The round-trip, following the `PlacePlugAI` precedent
(§1.1):

```
master module (IBotTick, unsynced)      decides personality P for this player
        │  bot.QueueOrder(new Order("SetBotPersonality", player.PlayerActor, false)
        │                 { TargetString = P, SuppressVisualFeedback = true })
        ▼
BotPersonalityController (synced, on Player, IResolveOrder)
        grants the ExternalCondition token for P, revokes the previous one
        ▼
existing condition consumers: SquadManagerBotModuleCA@<P>, ProvidesPrerequisite@personality_<P>
        (→ personality-specific compositions, §1.4), ObserverConditionNotification@<P>
```

This keeps every existing consumer unchanged, keeps the synced state machine tiny and
deterministic, and makes each switch a replay-visible event. `BotPersonalityController` owns
the initial draw as well as later switches; when switching is disabled, the lower tiers preserve
the fixed random personality.

The observer notification in §19 fires per trait instance once, so it needs a small change to
announce repeat switches; live players must still see nothing.

### 4.3 Main target selection — the user's question

The master module owns it. Per enemy player, a target score from §3.2, roughly:

```
score(e) = w_reach · reachability(e)
         + w_weak  · (our army value / their visible army value)
         + w_hurt  · damage we have dealt to e / damage e has dealt to us
         + w_econ  · their economy share of the enemy team
         + w_kill  · closeness to elimination
         - w_def   · their fortification
         - w_ally  · number of our allies already committed to e
```

Re-evaluated on the same slow cadence as personality (not every tick), with the incumbent target
carrying a momentum bonus. The user's "check how well it is doing against that player" is the
`w_hurt` term, and it is what makes the target switch when a fight is going badly: a sustained
adverse trade ratio against the current target lowers its score until a softer teammate outranks
it. Explicit guards, all learned from CN's momentum documentation: a minimum hold time, a
mandatory re-target when the current target is eliminated or unreachable, and an override when a
different player is actively killing our base (you do not get to ignore who is hitting you).

Target and personality are **coupled but distinct**: the target answers "who", the personality
answers "how". The personality is chosen against the *selected target's* profile, damped by the
worst threat among the others — otherwise the bot turtles against a rusher it isn't fighting, or
steamrolls into a fortified target while a second player razes its base.

The `w_hurt` **producer** landed 2026-09-28: `CombatAnalysisBotModule` (Cameo, ported from CN
`30cf70a`) implements `IBotThreatAnalysis` — per-role threat weights fed by `IBotRespondToAttack`
with decay, plus a nemesis score per enemy player (the "damage e has dealt to us" side). The
dealt side landed the same day (EMBER): `INotifyAppliedDamage` fires on the *attacker's* player
actor (`Health.cs`), so `dealtScores` mirrors `nemesisScores` with the same per-player throttle,
weight, cap and decay. Consumed 2026-09-28 (EMBER): `WeightHurt` scores the **taken share**
`taken/(taken+dealt)` — the bounded form of the dealt/taken ratio — and a nemesis above
`NemesisOverrideWeight` force-retargets regardless of hold time — the 'do not ignore who is
hitting you' clause.

### 4.4 Transition table

The user's five cases, plus the ones the design needs to cover. "Signal" is per §3.2, evaluated
for the main target unless stated.

| Detected situation | Personality | Also |
|---|---|---|
| High static defence count / value | Steamroller | artillery/siege composition tokens; slow massed push |
| Aggressive expansion, many clusters | Guerrilla | many small squads, simultaneous raids on outlying clusters |
| Enemy rushing us (early aggression, our losses spiking) | Turtle | static defence fractions up, defensive squads near base |
| Few defences and small army | Rush | small squads from multiple directions |
| Enemy teching (tier climbing fast, low army) | Tech | match tech pace; keep enough army to punish |
| Air-heavy enemy | (keep) | AA demand up, `AirToAirUnits`/`StaticAntiAirTypes` priority |
| Naval-heavy on a water map | (keep) | naval squad share up |
| Mass infantry | (keep) | anti-infantry weighting |
| Mass armour | (keep) | anti-armour weighting |
| Stealth reliance | (keep) | detector demand |
| Economic boom, no army | Rush | punish now; the window closes |
| Superweapon under construction | Rush/Guerrilla | urgency override on hold time |
| We lost production structures | Turtle (as a candidate, never forced — DESIGN §19.11) | rebuild before committing |
| Two enemies focusing one ally | (keep) | target the aggressor, not the score leader |
| No contact / nothing known | Expansion | scout; take map while blind |
| No signal crosses a threshold (terminal fallback) | Turtle if Pressured, else Expansion | the candidate set always yields a posture; the incumbent is no longer a silent default |

**Measured defect, fixed 2026-09-28 (EMBER):** in nw-ab-7 both `hard` matches sat in `turtle`
for ~38k ticks while the candidate stayed `rush`. The latch was not a missing candidate — the
emergency checker had a single 600-loss threshold, so the loss window bounced across it every
25-tick check, each flicker flipped the candidate to `turtle` and back and reset the
sustained-candidate timer, so `rush` never accumulated its reaction delay. Two changes: an
off-threshold (`EmergencyLossClearThreshold = 300`, half the on-threshold) gives the emergency
state hysteresis, and `PersonalityCandidates` now always ends with a posture yield (Turtle under
pressure, Expansion when calm) so no profile can starve the switcher of a decision.

Note the "(keep)" rows: **most enemy facts should change composition and priorities, not
personality.** Personality is the coarse posture; a six-state machine cannot express "he went
air" and should not try. This split is deliberate and is the main structural opinion in this
document.

### 4.5 Switching policy

Copy CN's shape, with numbers as tunable fields, not constants: slow re-evaluation cadence
(~1500 ticks); a fast emergency check (~25 ticks) that raises urgency on a danger spike (it forced Turtle until DESIGN §19.11, 2026-10-03); a
minimum hold time (~3000 ticks); an incumbent momentum bonus small enough not to mask the signal
each personality exists for; earliest-tick and army-ratio gates so Steamroller cannot be chosen
before a mass exists; and a per-personality coverage penalty across allied bots so a team of bots
diversifies. Every switch is logged (§6) with the signal vector that caused it — without that,
the learning loop has nothing to learn from and the behaviour is unexplainable in a replay.

---

## 5. The master module

`MasterAiBotModule` — one instance per player, singleton by construction, `IBotTick`.

**It owns exactly three decisions:** main target, personality, and the published signal snapshot
(the user's "input matrix"). Everything else stays where it is. The failure mode to avoid is a
second production or squad authority (§2.3), and the existing modules are competent; what they
lack is a shared view of the enemy.

```
MasterAiBotModule
├── observes   fogged per-enemy signals (§3), own state, our pairwise damage ledger
├── decides    main target · personality · urgency
├── publishes  an immutable snapshot other modules may read
└── acts       only by queueing SetBotPersonality / target-hint orders (§4.2)

readers (unchanged authorities, now better informed)
├── SquadManagerBotModuleCA@<personality>   who to attack, how big a squad
├── BaseBuilderBotModuleCA                  defence fraction, expansion appetite
├── UnitBuilderBotModuleCA                  composition eligibility, AA/anti-armour demand
├── UnitCompositionsBotModule (world, singleton) via personality tokens (§1.4)
└── specialists (harvester, MCV, power, support powers, capture, repair, scout)
```

As of 2026-09-28 the published snapshot is still **telemetry-only**: `DefenceFractionHint` and
`ExpansionAppetiteHint` reach `cameo-ai-situations.jsonl` but no in-game reader exists — there is
no `IBotSituationProvider` interface and `BaseBuilderBotModuleCA` does not consult it. Wiring it
means a new CA-side interface plus defaults for the `classic` stack (which has no master module);
that is the next integration seam, deliberately left for coordination since it touches the
CA-sync-tracked builder.

Publication should be pull-based — readers ask the master for the current snapshot — so the master
never has to know who its readers are, and a missing master degrades to today's behaviour instead
of crashing. That is the difference between "the master coordinates" and "the master is a single
point of failure".

What the master must **not** do: pick individual unit targets, choose build items, move squads, or
duplicate any decision a specialist already owns.

---

## 6. Logging and learning

### 6.1 The boundary that keeps this safe

Four strictly separated tiers. Crossing them is the only way this feature can break the game:

| Tier | Determinism | Where |
|---|---|---|
| Synced simulation | must be identical on every client | personality condition state only |
| Live bot reasoning | host-local, unsynced, free (§1.1) | master module |
| Match log | write-only, no gameplay effect | disk, end of match + on events |
| Learned parameters | read at map load, then frozen for the match | a data file, treated as configuration |

The hard rule: **learned data may only be read when the match starts, and must be identical for
every client, or it must not touch synced state at all.** A weight table that only steers the
master's own unsynced scoring is safe on the host. Anything that changes what a *condition* does
must be part of the map/mod configuration, not a file one client happens to have. No inference at
runtime, no network calls, no adapting mid-match from a file that another client cannot see.

`Log.AddChannel(name, file, isTimestamped)` writes to `Platform.SupportDir + "Logs"`
(`engine/OpenRA.Game/Support/Log.cs:111,128`) and mods already add channels from traits
(`ScriptContext.cs:146`, `TraitDictionary.cs:62`). The shipped phase-one writer uses
an append-only file with host authority, mutex coordination and bounded retries;
its exact contract is in `AI_MATCH_LOG.md`.

### 6.2 Shipped record-only log schema (one JSON object per line)

Phase 1 ships one versioned JSONL object per bot player per finished match. The
authoritative field order and writer rules live in [`AI_MATCH_LOG.md`](AI_MATCH_LOG.md).
`AiMatchLogRecorder` observes personality transitions without changing them, and
`AiMatchLogWriter` appends the records only on the host in regular non-replay worlds.
The game never reads the file back. The offline
[`aggregate_ai_matches.py`](../../tools/ai/aggregate_ai_matches.py) tool consumes
schema version 1 records; later decision and episode records remain proposals.

Three proposed learning record types, not the shipped schema above:

* `match` — map, ruleset hash, player slots (faction, difficulty, bot type, human/bot), duration,
  outcome per player.
* `decision` — tick, player, chosen personality, chosen main target, urgency, the full signal
  vector per enemy, and *why* (winning score and margin). One per re-evaluation, not per tick.
* `outcome` — per player per personality-episode: ticks held, army value delta, resources spent,
  units/buildings killed and lost, attributed pairwise against the main target of that episode.
  Plus per composition: ticks active, cost committed, value destroyed vs value lost.

The unit of learning is the **episode** (a personality held against one target), not the match.
Match-level win/loss alone is far too sparse to attribute — a 40-minute game with six switches
gives one bit of signal against six decisions, which is the credit-assignment problem in §8.

### 6.2a Integration boundary and learning stages

PR #329 adopts the merged #331 writer rather than shipping its competing
`CameoMatchRecorder`. Older `Logs/cameo_matches/*.jsonl` experiments have a different
schema and must not be mixed with `Logs/cameo-ai-matches.jsonl`. The retained writer
captures bot rows when all bots resolve or GameOver occurs, not necessarily at
completion of the whole world. Replays, loaded saves and non-host clients are excluded.
Prior PR #329 runtime recording evidence exercised the retired writer, not this one.

The shipped schema does not carry source hashes, module IDs or lobby options;
matching mod-version strings do not prove identical balance inputs. Missing stats
are zero, and overlapping personalities are not separately marked ambiguous.
Timeline length and retries are bounded, but file size and record size are not.
These are explicit limitations, not grounds for introducing a second recorder.

**Phase 1 — record only (implemented).** Emit schema version 1 logs, change no behaviour, and
leave aggregation offline. The shipped recorder, writer, schema, and aggregator are the proof of
concept deliverable. Verify the schema survives real matches and that the numbers are attributable.

**Stage B — offline aggregation extensions.** The shipped aggregate tool handles
schema-v1 bot rows; future episode-aware extensions would produce, per
(faction × enemy faction × personality) and (composition × enemy faction), the episode counts,
mean value-trade ratio and win contribution. This is where "which composition does badly" gets
answered once episode attribution exists, with uncertainty and coverage reported before
any number informs a decision. First compare fixed versus dynamic policies offline (§11.3.5).

**Stage C — offline weight fitting, still no online learning.** Fit the §4 scores' weights, or
simply a prior over personality choice per matchup, and ship the result as a committed data file
reviewed like any balance change. Bandit-style selection (UCB1/Thompson over personalities per
matchup) is a candidate from §8.2, not a selected Cameo policy. It must first show a benefit
over the fixed-policy comparator on compatible Cameo data (§11.3.5).

**Stage D — AI-vs-AI batch harness.** Headless repeated matches across matchups, feeding stages
B–C. This is what makes the data volume possible; it should be a script and a map rotation, not
engine work. *Shipped:* `tools/ai/run_ai_match_batch.py`. **Since the 2026-09-28 maintainer
ruling the duel map is the shipped tournament map "A Nuclear Winter"
(`mods/cameo/maps/_ra_a-nuclear-winter.oramap`)** — the harness extracts the .oramap into a
variant dir, seats a `Referee`, and converts `Multi0`/`Multi1` into map-side bots bound to the
map's real `mpspawn` cells. The acceptance A/B is the Frankenstein bot at a tier (`hard`,
fog-honest, every merged module) vs the `classic` `ModularBot` type (omniscient, pre-merge
modules, same difficulty scaling) — **not** the `fransbot` type, which is a hidden donor
(maintainer ruling 2026-09-28) — both spawns (`--repeats 4 --swap-bots`), `gamespeed: maximum`
locked — see `docs/design/AI_MATCH_LOG.md` § "The A/B acceptance protocol". Legacy fixture:
`mods/cameo/maps/ai_duel_gate_20260928/` (Desert Rats donor terrain, two real mirrored mpspawns)
remains usable via `--map` —
the harness copies the template into an isolated `Engine.SupportDir` user-map cache per matchup
(faction × bot × time-limit patching + faction starting-unit actors written into `Actors:`),
launches `Launch.Map`+`Launch.Benchmark` (exits on `GameOver`), and slices the appended
`cameo-ai-matches.jsonl` per run. Constraints the map design had to satisfy, verified against
the engine: a `Local` server refuses to start with every slot empty, so the map keeps an inert
host-occupied `Referee` slot whose `PlayerReference.NonCombatant` keeps it out of every record's
`opponents`/`allies` (lobby clients ignore `Player.NonCombatant`); empty playable slots produce
no `Player` at all, so the duelists are `Playable: False` + `Bot:` map-side players (the writer
admits them via `IsBot`) with `SpawnStartingUnits` bypassed by preplaced actors; Cameo strips
`MustBeDestroyed` from most actors so the map re-adds it to the base templates for real
elimination, and `TimeLimitManager` (locked) is the guaranteed terminator — its timeout ranking
reads `Playable` only, so a drawn duel records both bots `lost`. **Run bot tests at high game
speed:** the fixture locks `gamespeed: maximum` (1 ms timestep — CPU-bound, ~25x default at
parity hardware) so decisive matches resolve as fast as the box can tick them — the minutes
cap then spans 40x the ticks (`TimeLimit *= 60 * ticksPerSecond`, `TimeLimitManager`), and
`AdaptiveGameSpeed` pacing slows the target rate under CPU contention rather than janking, so a
generous wall bound plus a debug.log stall detector (`run_ai_match_batch.py`) replaces a tight
match timeout. Match records are only comparable within one speed — a `10`-minute maximum match
contains 40x the simulated play of a default-speed one and 10x an insane-era one, so pooled
baselines do not carry across the 2026-09-29 speed change.

**2v2 team mode (TC-3, landed 2026-10-02, DAWN).** The same harness runs duos:
`--team-size 2` makes `--bot-a`/`--bot-b` comma-separated team lists (one name
duplicates across both slots) and defaults the map to the shipped doubles map
`mods/cameo/maps/_ra_doubles.oramap`, whose consecutive `Multi` pairs are the
teams (Multi0+Multi1 vs Multi2+Multi3 on its four mpspawns). Map-side stances
must be declared **symmetrically** — `CreateMapPlayers.SetupPlayerMasks`
resolves every ORDERED pair and same-Team clients fall to the allied default,
so each member append-merges its teammate into `Allies:` and BOTH enemy refs
into `Enemies:` (the map's `Creeps` hostility stays). A 2v2 match appends four
schema-2 records sharing one game_uid; the team verdict for aggregation is
"any member record `won`" — ConquestVictoryConditions beats a side only when
every non-ally is Lost, so a teammate eliminated early still records `lost`.
`run_league.py` takes `"team_size": 2` for homogeneous-duo league cells.

**Stage E — anything neural.** Explicitly deferred until factions and balance are finished, per
the user's own sequencing. Training against a moving balance target fits noise.

Recording and coverage diagnostics help debug the current bots while balance moves. Learned
weights remain §10.6 phase 7, after the earlier delivery phases; neither this section nor the
batch-harness proposal authorizes skipping the observe-only and behavior-review gates.

### 6.4 Learning every number between matches (maintainer rulings 2026-09-29)

**Ruled:** every bot number is learnable, and today's values are only the starting point. That
includes per-faction building timers and limits: identical templates, different play styles.

**The inventory (measured 2026-09-29):**
* 101 distinct numeric settings in 15 bot modules, 404 values over all instances;
* 2,612 per-actor numbers (building tables, unit weights);
* derived factors (combat-predictor strengths, unit priors).

A training match takes ~10 min on an idle machine, so a day gives ~100–150 matches. Tuning
3,000 numbers one by one on that is hopeless; every number therefore learns through the route that
fits how its truth can be observed.

| route | numbers | how it learns | data per match |
|---|---|---|---|
| **1. measured** | unit effectiveness per (unit, enemy faction) from the arsenal ledger (CA-1/CA-1b); combat-predictor strength per type (fitted to real fight outcomes); the enemy faction's usual composition and first-attack timing | statistics with evidence counts and shrinkage toward the parent level; every match counts, won or lost, both sides | hundreds of units, dozens of fights |
| **2. tuned** | building fractions, limits, delays and intervals; timers; squad sizes; attack and retreat thresholds; the personality's role mix | experiments: in training, the harness nudges values per match (paired ± steps, SPSA-style), compares scores, and moves toward the better side within bounds | one score per match |
| **3. chosen** | discrete options: which personality or opening against which enemy faction | a bandit (Thompson sampling) over the options per matchup | one outcome per match |

**Rulings on route 2:**
* **Granularity:** per own faction, falling back to its game family and then global while
  evidence is thin. Only the army mix and counter weights also split per enemy faction.
* **Knobs first, then raw:** about 8 knobs per faction scale their raw numbers together (tempo:
  delays and intervals; economy greed: refinery and harvester numbers; tech speed; defence share;
  army mix; aggression: attack and retreat thresholds; …). Once a knob settles, an individual number
  with strong evidence of its own gets its own learned value.
* **Score = win plus margin:** win or loss, plus how decisively, measured by army and building value
  traded over the whole match (the timeline and fight report exist, #617). Win/loss alone is too
  noisy; the 7–6 coin flip showed it.

**Hierarchy and bounds.** A learned value is a multiplier on its default:
`value = default × m(global) × m(family) × m(faction) [× m(matchup) for the mix]`. Each multiplier
shrinks toward 1 in proportion to its evidence, and a training round may move it at most ×0.5–×2.
Difficulty applies **on top**, so the DESIGN §19.1 equal-step line holds for every learned base.
Unit and building stats are never learned (that is balance), and nothing learned may cheat (§19.2).

**Where learned values live and apply.**
* The committed files live in `mods/cameo/ai/learned/`, one per route. Each entry carries its
  evidence count and the build it was trained on.
* Release builds only read them; only dev builds and harness training runs write (DESIGN §19.2).
* The modules read their numbers straight from the shared rules: 415 `Info.*` reads in
  BaseBuilder, its queue manager, SquadManager and UnitBuilder. One `Info` object serves every bot
  using that module, so a learned per-faction value cannot live there. **Mechanism:** when the
  host's bot is enabled, it gives each of its modules a private **copy** of that module's `Info`
  with the learned values applied. That is zero edits at the 415 read sites and no CA-sync conflict.
  It stays host-only, because the modules only run in the host's bot (`Player.cs:223`). Never apply
  learned values to rules at load: rules load on every client.

**When balance moves (maintainer question 2026-09-29).** The reference mapping and the balance
pipeline have not written their targets yet, so costs, HP, damage and Versus values will change a
lot, and a value learned now describes a game that will not exist ("training against a moving
balance target fits noise", Stage E above). The design therefore:
* **Fingerprints every learned entry** with the stats it was trained on: the unit's cost, HP,
  speed, armour and weapons, and a faction fingerprint for faction knobs. At match start, an entry
  whose fingerprint changed is discounted toward its default **per unit**, not globally, so a small
  patch invalidates only what it touched.
* **Route 1 re-learns fast:** effectiveness is value traded per value lost, so a cost change alone is
  largely absorbed, and every match brings hundreds of new points.
* **Knobs survive better than raw numbers:** they are multipliers on defaults that come from the
  templates. They are still discounted when their faction's fingerprint moves a lot.
* **Sequencing:** L0–L2 (machinery, no behaviour change) are built now. Serious training (L3+)
  starts after the balance freeze and is repeated once per release, whose learned files ship with it.
* **Guard:** an audit reports how much of the committed learned evidence the current rules have
  invalidated, so a big rebalance shows up as "retrain before release".

### 6.4a Combining the weights: general × enemies × allies (maintainer rulings 2026-09-29)

This generalises the single-enemy `prior(own faction, enemy faction, u)` of §2.9's production
weight to any number of enemies and allies; `mix` and the role split of §2.9 are unchanged.
Every learned value is a **multiplier that defaults to 1**, and the layers combine in log space,
where a geometric mean is a weighted average:

    prior(u)   = General(own faction, u) × Enemies(u) × Allies(u)
    weight(u)  = mix[personality][role(u)] / |role(u)| × prior(u) × Gap(u) × trade(u)      (§2.9)
    Enemies(u) = exp( Σ_e α_e · ln M(u | e) )        Σ α_e = 1
    Allies(u)  = exp( λ(n_allies) · Σ_a β_a · ln S(u | a) )        Σ β_a = 1

* **General**: one file per own faction, trained against everyone and **always active**. When a
  matchup has little data its `M` shrinks to 1, so the bot falls back to General automatically.
* **Enemies**: the per-enemy-faction counter multipliers `M(u | e)`, combined as a **weighted
  geometric mean**, so no single matchup can dominate a multi-faction game. **The share α of the
  main (hate) target combines all three proposals** (maintainer: "a combination of all of them"):
  1. a **floor** that keeps it dominant: `α_main ≥ max(1/2, 2/(n+1))`. That is 100 % with one
     enemy, the double vote at 67 % with two, and 50 % from three enemies up, so it is never
     diluted in a big game;
  2. the **rest**, `1 − α_main`, is split among the other enemies by
     `(1 − γ) · equal share + γ · threat share`. Threat is fog-honest: remembered enemy army
     value near our assets. A quiet enemy still counts, and the one attacking us counts more;
  3. **γ and the floor are learnable** (route 2, §6.4), so training finds how reactive to be.
* **Allies** (ruled: **learned + fill gaps**): the trained synergy multipliers `S(u | a)` per
  (own faction, ally faction) come from team-game training; that needs a 2v2 variant of the duel harness, built with
  **TC** (Team Commander, ROADMAP; `AI_DEEP_RESEARCH.md` §9).
  `β` splits equally among allies, and `λ` grows with the number of allies (the team's say in
  what we build grows with the team). With no allies `Allies(u) = 1`.
* **Gap** (the "fill gaps" half of the same ruling) is in-match, not learned from past games: a
  role (§12.4) the whole team, us included, lacks gets a boost, bounded like every other factor.
  Allied armies are visible, so this is not a cheat. With no allies it is 1.
* **trade**: the live in-match trade ratio per role or type (§12.3), as in §2.9.

Every factor is trained separately (routes 1–3, §6.4), bounded, fingerprinted against balance
changes, and applied only inside the host's bot. With no data at all the bot plays today's defaults.

**The training loop (dev only).**
1. **League batch:** past masters, `classic` and the exploiters (LG), several tournament maps,
   both spawns.
2. **Fitters:** route 1 is updated from the logs; route 2 is updated from the paired perturbations.
3. **A/B:** the candidate learned files are tested against the current files.
4. **Commit:** a PR with the evidence, if the candidate does not lose.

**Phases** (after the §2.9 groundwork; the §10.6 gates still apply):

| # | step | gate |
|---|---|---|
| L0 | the per-bot `Info` copy + a learned-file reader; empty files change nothing | the P0 dump is identical; a two-client desync test; boot |
| L1 | route 1: unit priors (CA-1b), combat-predictor strengths, enemy models | A/B |
| L2 | the score in the harness + the knob layer (defaults = 1) | the dump is identical with all knobs at 1 |
| L3 | route 2 training: paired perturbations per faction knob | A/B per committed file |
| L4 | route 3: personality and opening bandit per matchup | A/B |
| L5 | raw numbers with strong evidence leave their knob | A/B |

---

## 7. Dependencies and risks

**Dependencies.** Fogged observation (§3.1) needs a scouting module or the bot plays blind.
Personality-specific compositions (§1.4) need composition authoring per faction — that is balance
work, not a port. The pack split (§2) should land before per-pack AI behaviour is authored, or the
migration has to be redone.

**Risks.**

* *Silent migration failure* — the global file keeps winning after a partial move. Mitigated by
  gating every step on a byte-identical `--resolved-rules` diff.
* *Load-time crash from removal syntax* in a pack (case 5). Mitigated by the "add, never remove"
  rule.
* *Composition module crash* if anyone reaches for multi-instance gating (§1.3).
* *Thrashing* — a manager that switches too often is worse than a random one. Mitigated by CN's
  hysteresis shape, and observable because every switch is logged.
* *Overfitting to bot opponents* — self-play data teaches beating bots, which is not the goal.
  Human replays are the only corrective, and there is no pipeline for them today.
* *Fog makes bots weaker before it makes them better.* Expect a temporary strength regression when
  §3.1 lands, and hold it against the honest-play goal rather than against win rate.

---

## 8. Outside research: how RTS AI actually does this

Provenance is separated deliberately: the items below are published work, not Cameo facts, and
each is cited so the claim can be checked.

### 8.1 Opponent modelling and strategy prediction under fog

Synnaeve and Bessière's Bayesian models predict an opponent's opening and build/tech tree from
partial, noisy observations, with parameters learned from replays
([CIG 2011](https://doi.org/10.1109/cig.2011.6032018),
[AIIDE 2011](https://doi.org/10.1609/aiide.v7i1.12429)). The structural lesson for §3 is that a
build tree is hierarchical, so a single sighting raises the probability of everything it implies —
which is exactly how a fogged bot should reason from one scouted building, instead of the
all-or-nothing knowledge it has today. Their framing of it as *keyhole plan recognition* is also
the right framing for Cameo: the bot infers intent from what it happens to see, without
interrogating the opponent.

### 8.2 Strategy selection as a bandit — the cheap win

The strongest *scripted* Brood War bots learn between games rather than within them. ZZZKBot uses
"a multi armed bandit online learning algorithm for opening selection" and, from AIIDE 2017,
"uses the results from past games for an opponent to decide which strategy to try the next game
against that opponent" ([Liquipedia](https://liquipedia.net/starcraft/ZZZKBot)). That is precisely
the user's "learn which personality works against which faction and build order", implemented with
a handful of counters and no neural network — which motivates the bandit candidate in §6.3 stage C.

Tavares et al. treat strategy selection itself as a game, filling a payoff matrix from recorded
matches and showing it pays to *deviate* from Nash equilibrium to exploit a suboptimal opponent,
with safe-exploitation bounds to limit the downside
([AIIDE 2016](https://doi.org/10.1609/aiide.v12i1.12857)). Two consequences for §4: a
personality-vs-enemy-strategy payoff matrix is the natural learned artifact, and a bot that always
plays the "safe" counter is exploitable by a human who notices — some deliberate randomisation is
correct, not sloppy.

### 8.3 Learned high-level switching, and its cost

Gehring et al. cast high-level strategy selection in Brood War as reinforcement learning where an
action *is* a switch to a strategy, under partial observability, and report substantial win-rate
gains over a fixed-strategy baseline ([arXiv:1811.08568](https://www.alphaxiv.org/abs/1811.08568)).
This is close to the user's target and is the reason §6.3 stage E is not dismissed. But it is also
the reason it is last: it needed a research team, a mature bot to sit inside, and training volume
Cameo cannot produce until the balance stops moving. AlphaStar-class approaches are further still
outside reach and, more importantly, outside the point — a deterministic, auditable manager is
worth more to a mod that people have to debug and tune by hand.

### 8.4 What the literature says the failure modes are

Recurring across the above: **credit assignment** (which of many decisions caused the loss — §6.2's
episode records exist for this), **non-stationarity** (an opponent that adapts invalidates learned
weights, hence bandits with exploration rather than fixed tables), and **distribution shift**
(training against bots does not transfer to humans — §7's overfitting risk).

---

## 9. Open decisions

1. **Does fogged observation ship, and when?** It is the difference between "no cheats" being true
   and being a slogan, and it will make bots temporarily weaker. Maintainer's call.
2. **Is Guerrilla a sixth personality or a mode of Rush?** Sixth costs another squad-manager block
   and a token; a mode is cheaper but less legible in logs. Leaning sixth.
3. **How far does the pack split go?** Dictionary rows only (option A, no C#), or eventually the
   fragment registry (option D)?
4. **Where do learned weights live** — committed yaml reviewed as balance, or a support-dir data
   file? The synced/unsynced boundary in §6.1 permits either; reviewability argues for committed.
5. **Do we want a human-replay pipeline** at all, given §8.4's distribution-shift warning?
6. **Are the ten difficulty tiers all supposed to get the manager**, or is dynamic switching itself
   a high-difficulty feature? Making it difficulty-gated is a cheap, honest difficulty axis.
7. **How deep does the opponent model go in phase 2** — per-enemy strategy labels as §3 designs, or
   own-state plus a fortification scalar as CN actually ships (§1.6)? Kept open on purpose: the
   phase-2 logs are the evidence that settles it.
8. **Who owns contact memory** — one memory built by the master, or an extension of the squad
   manager's own scan, which is where CN keeps it? One authority per decision (§10.1) says pick one,
   and the master needs it per enemy player while the squad manager needs it per cell.
9. **How verbose is the decision trace** (§11.3.2) — always-on JSONL, or behind a debug flag? Eight
   bots re-deciding every 1500 ticks with a full candidate vector is small; the same trace on the
   emergency cadence is not.
10. **What may an emergency override change** — target and urgency only, or the personality too? CN
    switches the personality straight to Turtle on a danger spike (§1.6); the review reply argues an
    emergency should never rewrite the strategic posture. **RULED 2026-10-03 (DESIGN §19.11): target and
    urgency only.** An emergency never rewrites the personality, and it fires only on a net loss that is
    large relative to the bot's own army. Switch `AL_emergency_net_loss`.
11. **Do CN's hysteresis constants ship as Cameo's defaults**, or get re-fitted from phase-2 logs
    before phase 3 turns switching on? Leaning: ship CN's as the starting point, since they were
    tuned against a switching bot in this engine family, and re-fit after the first logged matches.
12. **How does a fog-honest offense get fresh target intel?** Measured 2026-09-28 (nw-ab-5/6,
    `FransGeneralBotModule` recon loop): ordinary RECON selects only the nearest *stale
    MineCluster* on a geographic fan from home — there is no candidate class for "the enemy's
    probable base". `FransMissionType` has no assault verb; `Raid` is the only offense, and
    `TryBuildGroundRaidBid` rejects remembered-intel targets (a deliberate fog-honesty rule —
    `FransRaidIntel` docs reserve remembered-building strikes for Sea). Result on A Nuclear
    Winter: recon fans stall on mineral waypoints short of the enemy base, every RAID publishes
    `bids 0`, zero enemy buildings die across six matches. The choices, in increasing size:
    a. **Spawn-directed recon** — `Map.ActorDefinitions` `mpspawn` cells are public map data
       (lobby-visible to every human). Add unscouted-spawn cells as a RECON candidate class
       alongside mine clusters (same cooldown/staleness machinery, higher priority for cells
       whose fan arm is unexplored). Fog-honest, minimal, and it is what every human does.
    b. **Bounded remembered-building raids for ground** — permit `IsRememberedIntel` targets
       when `IsBuilding` is true (buildings cannot move; last-seen cell stays valid), inside a
       freshness window. Extends the Sea-only rule by one axis.
    c. **A distinct assault/base-attack verb** — a heavier mission type with escort/consolidation
       semantics, versus teaching Raid to fill the gap.
    Leaning (a)+(b): they are orthogonal, both fog-honest, and together they close the
    "no fresh targets -> no bids -> no pressure" funnel without new verbs. (c) only if the
    combined change still cannot produce raid bids in measured matches.

---

## 10. The module plan: every module, what changes, and how they connect

§5 states the master module's role in the abstract. This section is the concrete build plan: what
each module that Cameo actually loads does today, what changes for it, and what it is allowed to
read. It exists so that implementation can start module by module without re-deriving the design,
and so that a reviewer can check any single module against it in isolation.

### 10.1 One authority per decision

The load-bearing rule, and the one most likely to be violated by accident:

> A decision has exactly one owner. The master module changes the *inputs* to a decision. It never
> makes a decision another module already owns.

Concretely: the master may raise the AA demand that `UnitBuilderBotModuleCA` reads, but it never
queues a production order itself; it may name the main target, but `SquadManagerBotModuleCA` still
picks which squad attacks what. Every past AI regression in this tree came from two writers of the
same state, and §1.3 shows the engine punishes duplicate authorities with a hard crash rather than
a subtle bug.

**One owner per ACTOR, too (LC1, 2026-09-30).** A module that sends a unit on a long-lived job claims it through
`IBotUnitLeases` (`OpenRA.Mods.CA/Traits/BotModules/IBotUnitLeases.cs`; the registry `BotUnitLeaseRegistry` loads for
`genericbot`) and skips units another module holds. `Actor.IsIdle` is never ownership: `ModularBot` runs every
module's `BotTick` before it issues any queued order, so two modules can both see one unit idle in the same tick
(the Fransbot author's review, P0). Holders either release, or renew every evaluation (a heartbeat) and let the
lease expire when they drop the unit — no release path can be forgotten. Resolve the service with
`BotUnitLeases.Of(player)` at every use; a null service means "no contract", the old behaviour (`classic`).

The second rule follows from it: **absence degrades, it never breaks.** Every reader treats a
missing master, a missing snapshot, or a stale snapshot as "carry on as today". That is what makes
this incrementally shippable — each phase in 10.6 is a complete, playable state.

### 10.2 What Cameo loads today

> **The authoritative list is generated:** [`AI_MODULE_MAP.md`](AI_MODULE_MAP.md), built by
> `python tools/ai/ai_module_map.py --write` from the resolved `Player`/`World` and the C#. On
> 2026-09-27 it lists **32 loaded bot types, 67 instances**, the interface provider → consumer
> graph, and four checks (consumer without provider, producer without consumer, unloaded code,
> shadowing). The table below is the annotated narrative; where they disagree, the map wins.
> Run `--check` before citing a count.

Verified on 2026-09-07 from the active `mods/cameo/mod.yaml` manifest and resolved
`Player` / `World`, against upstream base `291052380`. Scope here is the decision modules,
their explicit coordination adapter, and the three data/limit providers named below:
**68 distinct trait types, 93 Player instances plus one World instance** (2026-10-02e: BO-1 adds `BuildOrderKnobsBotModule` (genericbot, behind `build_order_knobs`), the §12.25 build-order knob provider, +1 type / +1 instance; 2026-10-02d: ST adds `ScaleTargetsBotModule` (genericbot, behind `scale_targets`), the §12.22 size-target provider, +1 type / +1 instance (#770 left it uncounted); 2026-10-02c: PP-1 adds `ParallelProductionBotModule` (genericbot, behind `parallel_production`), the settings-only IBotProductionWidth provider, and ATK-1 adds `AssaultFormationBotModule` (genericbot, behind `assault_fanout`), the settings-only provider of the unified CV/ATK-1 deploy state (§12.7a), and ST adds `ScaleTargetsBotModule` (genericbot, behind `scale_targets`, §12.22), +3 types / +3 instances; 2026-10-02b: SP-1/AF-1 add `SpacingAdvisorBotModule` + `ArmyFirstBotModule` (genericbot, behind `spaced_base`/`army_first`) and the `HarvesterBotModuleCA@generic`/@classic split adds one more instance, +3 types / +4 instances — the count also absorbs +2/+2 drift other merges left uncounted; 2026-10-02: CN3 adds `BridgeRepairBotModule` (genericbot, behind `cn3_bridge_repair`), the CN bridge-hut repair port claiming repairers per §19.6, +1 type / +1 instance — the count also absorbs a +1 drift RV2's `SupportPowerBotASModule@wc2` left uncounted; 2026-10-01: CN3 adds `DeployBotModule` (genericbot, behind `cn3_deploy`), the CN unified deploy-driving port, +1 type / +1 instance; CN2 adds `UnitRepairBotModule` (genericbot, behind `cn2_unit_repair`) and `GarrisonDefenseBotModule` (genericbot, behind `cn2_garrison_defense`), the crystallized-nexus repair-manager and threat-adaptive garrison ports claiming units per §19.6, +2 types / +2 instances; ZG adds `TacticalMapBotModule` (genericbot), +1 type / +1 instance; 2026-09-30: RV1 adds `BaseRepairBotModule`, the merged repair owner of DESIGN §19.3, and unloads the Common `BuildingRepairBotModule`, ±0; #656 adds `SiegeEvaluatorBotModule` (CA-2a siege telemetry) and splits the Fransbot `FransGroundCommanderBotModule` into six instances `@ground1`…`@ground6`, +1 type / +6 instances; 2026-09-29: `ExpansionPlannerBotModule`, EX-0 of §12.13, +1 type / +1 instance; 2026-09-28: #621 adds
`SquadManagerBotModuleCA@guerrilla`, the 69th instance; #607 adds `ResourceMapBotModule@fransbot` and `SquadManagerBotModuleCA@classic`, the 67th–68th instances; #578's Route-A Fransbot port adds 24 vendored `Frans*BotModule` types / 24 instances, the 28th–51st / 43rd–66th, which run only under the `fransbot` bot type; `BeaconResponderBotModule` (#580) is the 27th type / 42nd instance; `CncEngineerBotModule` (#562), `CombatAnalysisBotModule` (#564) and `HumanPaceBotModule` added the 24th–26th types / 39th–41st instances; `ScoutBotModule` was the 23rd/38th). Conditional instances
are loaded, not necessarily enabled simultaneously. This replaces the old unqualified
"20 loaded modules" claim. The scope does not count `ModularBot` dispatchers,
`GrantConditionOnBotOwner`, `BotInsurance`, generic condition/prerequisite traits, or observers;
it is not a claim that nothing else affects bots.

Sources: `mods/cameo/ai/ai.yaml`, active pack additions, and the `SupportPowerBotModule`
inherited through Player rules. C# implementations are under
`OpenRA.Mods.CA/Traits/BotModules/`, `engine/OpenRA.Mods.AS/Traits/BotModules/`,
`engine/OpenRA.Mods.Common/Traits/BotModules/`, with Cameo's
`Traits/BotModules/CratePickupBotModule.cs` and `Traits/BotGlobalUnitBudget.cs`.
Names below are actual resolved types; `PowerDownBotModule` resolves to AS
(`PowerDownBotManager.cs`), not the separately named CA implementation.

**Boundary legend:** **U** = local bot reasoning / callbacks; only queued orders may change
simulation. `ModularBot` wraps both `IBotTick` and `IBotRespondToAttack` in
`Sync.RunUnsynced`; it does not activate bots in replays. **R** = rule/state provider read by
local reasoning, not an autonomous order issuer. Provider trait existence on all peers does
not make a local cache safe for synced consumers. None of these rows reads the proposed
master snapshot today. "Hint" below is a future read-only integration, not shipped behavior.

| Actual type (loaded instances) | Decision / data ownership today | Current reads; future snapshot hint | Publishes / cadence / boundary |
|---|---|---|---|
| `SquadManagerBotModuleCA` (5 personalities) | squad assignment, combat posture and retreat | actors, attack events, base positions, limits; main target + urgency hint | orders, idle-unit and position callbacks; roles 25 ticks, attack-force 50/100/75/75/60 by current personality; U |
| `BaseBuilderBotModuleCA` (@generic) | structure choice, placement and construction priorities | queues, economy, terrain, limits, base/defence state; defence/expansion hints | build/placement/rally orders, production-pause query; queue-state delays and configured building intervals, not one universal period; U |
| `UnitBuilderBotModuleCA` (@generic) | unit production and composition selection | buildability, cash, idle units, requests, pause providers, composition table; counter-demand hint | production orders, requested-production count; feedback loop plus `UnitBuilderInterval`, per-unit delays and composition-selection gates; U |
| `UnitCompositionsBotModule` (World singleton) | composition definitions and lookup data | resolved rules and configured rows; no direct snapshot read planned | `Info.UnitCompositions`, prerequisite/queue/cost dictionaries at construction; R |
| `SupportPowerBotModule` (1) | Common decision-table power targeting | available powers, funds, configured decisions, target actors; target preference if integrated | power orders; each bot tick with per-power retry delays; U |
| `SupportPowerBotASModule` (1) | AS decision-table power targeting | same manager, AS decision rows and target evaluation; target preference if integrated | power orders; each bot tick with its own per-power retry delays; U |
| `SendUnitToAttackBotModule` (default, @chrono) | configured opportunistic attackers | eligible units/targets and attack desire; target preference | attack orders; `ScanTick` default 463; U |
| `HarvesterBotModuleCA` (1) | harvester task/threat handling | collectors, resources, threats and unit requests; economy-pressure hint later | harvesting/movement and production requests; idle scan configured 1000 ticks plus other source callbacks; U |
| `McvExpansionManagerBotModule` (1) | MCV deployment and expansion | mobile construction actors, resource map, base positions, unit builder; expansion hint | movement/deploy orders, production requests, position callbacks; new-MCV scan default 20, build check 101; U |
| `CaptureManagerBotModuleCA` (1) | capture assignment | eligible capturers/targets and visibility configuration; target preference | capture orders; minimum capture delay configured 125 ticks; U |
| `BuildingRepairBotModule` (0, unloaded since RV1) | Common building repair response | attacked actor, damage state, repair capability | repair orders on `IBotRespondToAttack`, including cooldown-gated all-building scan inside that callback; U |
| `BuildingRepairBotModuleCA` (1) | CA repair response path | attacked actor's repair trait, damage event and attacker relationship | conditional repair orders on `IBotRespondToAttack`; U |
| `PowerDownBotModule` (1) | power toggling | power totals and toggleable buildings; no new hint | PowerDown orders; interval default 150 ticks; U |
| `CratePickupBotModule` (1) | crate collector assignment | crate candidates, collectors and visibility setting; no new hint | movement orders; scan configured 300 ticks; U |
| `LoadGarrisonerBotModuleCA` (@Infantry) | passenger-to-garrison assignment | configured passengers, garrisons, capacity/proximity; posture hint only in a later phase | Stop/AttackMove/EnterGarrison orders; scan default 457 ticks; U |
| `LoadCargoBotModule` (@Infantry/@TankBunker/@Battery) | configured cargo loading | passengers, transport capacity and proximity; no phase-1 hint | cargo-related orders; scan default 317, Battery configured 799 ticks; U |
| `MinelayerBotModule` (1) | minefield assignment | minelayers, positions and attack events; posture hint later | mine-related orders; scan default 320 ticks and attack callbacks; U |
| `ExpansionPlannerBotModule` (genericbot) | EX-0 target field (§12.13): telemetry only, no orders | own actors, resource indices, base-builder queues, `IBotRegionThreatProvider`; nothing reads its target yet | `Target` / `LastScores` and a `debug.log` line on each target change; re-plan default 250 ticks; U |
| `ResourceMapBotModule` (1) | resource-index information | resource layer and nearby actors; no snapshot hint | index/threat query methods; `UpdateResourceMapInverval` default 67 ticks, randomized initialization; U provider |
| `ExternalBotOrdersManager` (1) | forwarding registered external requests | direct entries / `IssueOrderToBot` registrations and current issuer validity | queued orders each bot tick; local bridge, not a new strategy owner; U |
| `BotLimits` (10 difficulty instances) | configured cap/delay inputs | enabled difficulty condition; no master replacement | enabled `Info` queried by consumers; no independent tick; R |
| `BotGlobalUnitBudget` (1) | global-budget production pause input | living bots, owned mobile actors, exclusions and configured clamps | `IBotRequestPauseUnitProduction.PauseUnitProduction`, lazy recalculation at default 25-tick interval; R/local cache |

Intervals are simulation ticks, not milliseconds, and are gates rather than promises to emit
an order every interval. Startup randomization, disabled conditions, affordability, target
availability and existing queue backpressure still apply. These contracts do not alter any of
them or certify the separate economic-fairness claims elsewhere in this design.

### 10.2a Interaction and failure contracts

The following is the integration contract; absence of the future snapshot preserves current
decisions. A delayed rebuild must not trigger a compensating burst of production or orders.
Invalid/dead targets are revalidated by the decision owner; an unavailable hint is not permission
to mutate simulation directly. Existing overlap is recorded honestly below: the target design's
"one authority" rule is not proof that today's modules never compete.

**SquadManagerBotModuleCA.** Retains tactical ownership; the master may suggest a strategic
target but cannot commandeer squad members. Existing idle-unit notifications feed the unit
builder, and position updates coordinate bases. On future personality changes, re-resolve
enabled manager references rather than caching a disabled instance. No hint means current
targeting, including its existing visibility limitations, remains in force.

**BaseBuilderBotModuleCA.** Owns construction orders and placement attempts; production-pause
responses are advisory to the unit builder, whose existing opening-defence exception remains.
An unaffordable or unplaceable candidate stays subject to current retry/backoff limits.
Expansion appetite must not become an independent second building queue in the master.

**UnitBuilderBotModuleCA.** Owns fulfilling unit requests, not callers such as the harvester
or MCV manager. It checks non-base pause providers before its base-builder opening-defence
exception; a budget pause must not be bypassed by a future counter-demand hint. Missing
composition eligibility leaves existing selection behavior intact, not an invented fallback unit.

**UnitCompositionsBotModule.** Is data, not a second production agent. Consumers own selection
and prerequisite evaluation. Preserve the singleton: adding condition-gated duplicates breaks
single-trait lookup even when most copies are disabled (§1.3). Future personality influence
travels through properly supplied prerequisite tokens, not mutation of shared dictionaries.

**SupportPowerBotModule.** Owns its Common decision rows and queues, never directly executes,
power orders. Missing decision entries do not fire powers; no affordable target triggers the
existing decision-specific retry. Its co-presence with AS is real: future integration must
compare decision `OrderName` coverage before claiming exclusive power ownership.

**SupportPowerBotASModule.** Retains the AS targeting algorithm and separate retry dictionary.
A suggested main target cannot override power readiness, cost or target-validity checks.
There is no shared reservation protocol with Common today; any overlapping decision rows
require an explicit later ownership decision rather than silently disabling one module here.

**SendUnitToAttackBotModule.** The two instances retain their configured unit selections and
attack-desire accumulation. Missing suitable attackers/targets leaves them waiting. The master
does not issue substitute attack orders; avoiding overlap with squad ownership is an integration
acceptance test, not an already implemented reservation system.

**HarvesterBotModuleCA.** Keeps collector control and requests replacements through the unit
production interface. A future danger hint is additional input, not a command to abandon the
economy. Unavailable resources, actors or production capacity retain current retry behavior;
the master cannot create a collector or bypass the builder.

**McvExpansionManagerBotModule.** Uses ResourceMap's indices and requests production through
the builder; it owns deployment decisions. Missing viable expansion locations must not cause
another module to deploy the same MCV. Current `MoveConyardTick: 0` is preserved; a future
appetite hint does not implicitly enable that separate relocation behavior.

**CaptureManagerBotModuleCA.** Keeps capturer eligibility and capture-target checks. A stale
main target is discarded as a preference, not forced through capture restrictions. Easiest-bot
condition gating remains; waiting for the minimum delay cannot transfer ownership to the master.

**BuildingRepairBotModule** (unloaded since RV1; its sweep lives on in `BaseRepairBotModule`). Receives attack callbacks and inspects repair-capable actors
through the existing Common path. Its all-building scan is cooldown-gated inside the attack
callback, not independently scheduled; without callbacks there is no scan. Unsupported actors
produce no direct repair order; future hints must not create an unconditional expenditure loop.

**BuildingRepairBotModuleCA.** Is separately loaded, not an alias of Common. It looks up
`RepairableBuilding` on each attacked actor (the creation-time cache that left it inert was
fixed, as upstream CA did). Since RV1 (2026-09-30) it is `classic`'s only repair module (the Common
one is unloaded); `genericbot` runs the merged `BaseRepairBotModule` (DESIGN §19.3).

**PowerDownBotModule.** Reads the power manager and eligible buildings, then queues toggles.
It does not own construction of replacement generators. Insufficient toggleable capacity
remains a power-management limitation; future base-builder hints cannot justify direct power
or condition changes inside this local module.

**CratePickupBotModule.** Chooses a collector under existing distance/eligibility and visibility
settings and queues movement. No crate or collector yields no useful assignment; future squad
coordination must explicitly resolve competing actor orders rather than inventing an actor-lock
API absent from today's code.

**LoadGarrisonerBotModuleCA.** Chooses passengers and garrisons, with the existing capacity and
scan limits. Full/dead destinations require current eligibility checks; a future Turtle hint
must not bypass capacity or force the same infantry simultaneously into a squad and garrison.
Such arbitration is future work, not a shipped shared allocator.

**LoadCargoBotModule.** Keeps each instance's configured passenger/transport policy. A full or
missing transport does not authorize an unrelated module to spawn one. Preserve the three
instances and Battery cadence; cross-instance passenger contention must be tested if their
selection sets change.

**MinelayerBotModule.** Owns mine-placement assignments, using its current periodic and attack
inputs. No usable minelayer or site leaves no assignment. A posture hint may bias sites later,
but cannot grant mines or issue orders independently from this owner.

**ResourceMapBotModule.** Publishes local derived indices through query methods; it is not
the planned shared strategic snapshot. Consumers must tolerate stale information and recheck
actors/locations before orders. Its scan data must not feed a synced trait directly merely
because the source world is synced.

**ExternalBotOrdersManager.** Forwards valid registered requests rather than deciding global
strategy. Dead, out-of-world or no-longer-owned direct issuers are skipped, and direct entries
are cleared after processing. Preserve the source's distinction between direct entries and
`IssueOrderToBot` registrations; it is not a durable, acknowledged inter-module message bus.

**BotLimits.** Supplies enabled-instance policy to builders and squads; it neither publishes
a snapshot nor emits orders. Consumers must handle condition selection using their existing
refresh rules. The master must not silently replace difficulty limits while changing personality;
these are different axes.

**BotGlobalUnitBudget.** Is a query-driven pause provider, not an actor producer or remover.
Disabled/nonpositive budget returns no pause; otherwise existing clamps and exclusions apply.
Cached results may wait for the next configured recalculation; no other local module may
interpret that cache as synchronized world state or bypass it through a new production path.

**Loaded, observe-only:** `MasterAiBotModule` publishes the immutable local snapshot
at the §10.5 cadence (emergency ~25, rebuild ~150, decisions ~1500 ticks).
It has **no consumers and no hint reads**, and logs candidate personality and target values only.
Every difficulty issues `SetBotPersonality` after its sustained reaction delay; the synced
`BotPersonalityController` validates the order, ignores repeats, and owns the sole condition token.
`ScoutBotModule` remains a later owner of explicitly allocated scouting tasks after contact memory
and the visibility gate (§11.3), not a current capability. Reading an unsynced personality field
from simulation code is forbidden. `PersonalityReactionDelay` controls how long
a candidate must persist before switching; the ten difficulty tiers range from
7500 ticks on easiest to 750 on cameogod in 750-tick steps. The personality
hold is clamped to that reaction delay, so no tier reacts slower than its own
delay; a negative value preserves the fixed random personality fallback.

```text
Current synced world / rule data
    -> local modules + data providers (existing callbacks and queries)
    -> bot.QueueOrder -> synchronized order resolution -> world

Planned local Master snapshot --read-only hints--> existing decision owners
    |                                              -> same order boundary
    +-- SetBotPersonality order --> planned synced Controller --> condition
    +-- observation / decision records --> local diagnostics only
```

This specification changes documentation only. It adds no callbacks, shared snapshot consumers,
personality switching, scouting, fog restriction, priority arbitration or AI orders. In particular,
it does not re-adopt §11's rejected direct-condition mutation or multi-agent pipeline designs.

### 10.3 The snapshot: the one shared data structure

The user's "input matrix". One immutable object per player, rebuilt on the slow cadence, read by
everyone, written by nobody but the master.

```csharp
// unsynced, host-local, rebuilt on the slow cadence (10.5)
sealed class BotSituation
{
    int Tick;                                 // when this was built; readers check staleness
    Player MainTarget;                        // may be null: no contact yet
    string Personality;                       // what the master ASKED for, not what is granted
    Urgency Urgency;                          // Normal | Pressured | Emergency
    IReadOnlyDictionary<Player, EnemyProfile> Enemies;   // §3.2 signals, per enemy
    CounterDemand Demand;                     // AA, anti-armour, anti-infantry, detector, artillery: 0-100
    int DefenceFractionHint;                  // for the base builder
    int ExpansionAppetiteHint;                // for the MCV/expansion modules
}
```

Three properties are deliberate:

* **Pull-based.** Readers ask the master (`TraitOrDefault<MasterAiBotModule>()?.Situation`). The
  master does not know its readers, so a reader can be added without touching it, and a missing
  master is a `null` that every reader already has to handle.
* **Immutable and stamped.** Readers may cache it and compare `Tick`; nobody can mutate another
  module's view. This also makes the snapshot the natural log record (§6.2) — the thing we log is
  exactly the thing the bot decided on, so a replay explanation is never a reconstruction.
* **Hints, not commands.** `DefenceFractionHint` is an input the base builder may clamp or ignore
  by its own rules. That is what keeps 10.1 true.

`Personality` in the snapshot is the *request*. The authoritative state is the granted condition,
because that is what the five squad-manager instances key off. Readers that care about posture must
read the condition (as they do today), not this field; the field exists for logging and for the
one-tick window before the order resolves.

### 10.4 The one synced piece, and why an existing trait cannot do it

The switch has to cross from unsynced reasoning into synced state, and §1.1 allows exactly one
bridge: queue an order. `ExternalBotOrdersManager` (10.2) is the precedent for order plumbing, but
it runs the other way — synced traits register, the module queues. What we need is the
`PlacePlugAI` direction: module queues, synced trait resolves.

`GrantConditionOnOrders` (`OpenRA.Mods.CA/Traits/Conditions/GrantConditionOnOrders.cs`) looks like a
zero-C# answer and is not one. Its `ResolveOrder` revokes the condition on **any** order whose name
is not in its set (lines 44-47), and the Player actor resolves plenty of unrelated orders —
`PlaceBuilding` is a player-level trait (`engine/OpenRA.Mods.Common/Traits/Player/PlaceBuilding.cs:22`),
as are the production queues. The first building the bot places would clear its own personality.
Five instances would give correct mutual exclusion and still lose the state on the next placement.

So one small synced trait is unavoidable — the only new synced state in the whole design:

```
MasterAiBotModule (unsynced, IBotTick)
    bot.QueueOrder(new Order("SetBotPersonality", player.PlayerActor, false)
                   { TargetString = "guerrilla", SuppressVisualFeedback = true })
        |
BotPersonalityController (synced, on Player, IResolveOrder)   ~40 lines
    validates TargetString against its configured token map
    revokes the previous token, grants the new one, ignores a repeat of the current one
        |
existing consumers, unchanged:
    SquadManagerBotModuleCA@<personality>       (condition-gated instance selection)
    ProvidesPrerequisite@personality_<p>        -> personality-tagged compositions (§1.4)
    ObserverConditionNotification@<p>           (observer-only switch announcement)
```

The controller owns the initial draw as well as every later switch: deleting
`GrantRandomCondition@personality` prevents an unrecoverable first token from surviving a switch.
If switching is difficulty-gated off, the bot behaves exactly as it does today — a random fixed
personality — which is the degradation rule of 10.1 applied to the riskiest change here.

Two consequences to accept: every switch is a replay-visible order (good — it is auditable and it
is how the observer indicator learns about it), and the switch costs one order per change, so the
cadence limits in §4.5 are not just anti-thrash tuning, they are the cost control.

### 10.5 Cadence, and why the master is cheap

| Loop | Cadence | Work |
|---|---|---|
| Emergency check | ~25 ticks | danger delta only; can force Urgency=Emergency, never the personality (DESIGN §19.11) |
| Snapshot rebuild | ~150 ticks | per-enemy signal scan, counter demand, hints |
| Target + personality decision | ~1500 ticks | scoring, hysteresis, the order |
| Log flush | match end + on switch | append JSONL (§6) |

The expensive part is the actor scan in the snapshot rebuild, and it is the same scan the squad
manager already does every tick — so doing it once per 150 ticks in the master and letting readers
share the result is a net *saving* if the squad managers are later pointed at the shared result
instead of scanning independently. That consolidation is not phase 1, but the snapshot is shaped to
allow it.

### 10.5a The assign layer: missions

Phase 7a adds the first assign-layer contract without creating another unit owner.
`MasterAiBotModule` publishes fog-honest `Raid` and `Defend` intent through
`IBotMissionProvider`; `SquadManagerBotModuleCA` consumes the ordered missions only when it is
about to form a new attack force. The producer derives missions from `RegionMemory`, while the
consumer retains ownership of force formation, target validation, and orders.

The strategist publishes intent rather than commanding units because squad membership and
execution already belong to the squad manager. A mission may defer a force for a bounded defend
hold or focus a newly formed raid, but it never moves units between existing squads and never
assigns a unit itself. `Recon` remains with `ScoutBotModule` and `Secure` is deferred to a later
phase. The assign layer must never become a second owner of a unit.

The mission consumer revalidates each cycle: an exhausted Defend posture is skipped so a later affordable Raid remains eligible, and a cleared threat releases the hold immediately. Raid target lookup first uses visible actors; in fogged mode the consumer may use the existing remembered frozen-actor path. With `FoggedScans` disabled, the fallback can select unseen actors because it inherits the existing omniscient behavior of that mode rather than introducing a mission-layer cheat. The permanent `ai_raid_gate_20260928` fixture proves Raid publication and target-bearing assignment with reachable enemy economy under fog; it does not assert frozen assignment because that path is not reliably reproducible in the fixture.

### 10.6 Build order, each phase shippable on its own

1. **Match logging, record-only.** No behaviour change. Writes the match record (§6.2) including
   the fixed personality and the outcome. Value: the learning loop has data before any decision
   code exists, and the log schema gets exercised while it is still cheap to change.
2. **`MasterAiBotModule`, observe-only (implemented).** Builds and publishes the snapshot; decides
   nothing, and no module reads it yet. Logged per rebuild. This is intentionally pre-fog, and the
   score omits `w_hurt` until phase 4 adds pairwise attribution. The signal derivations can be
   validated against replays cheaply without touching gameplay.
3. **`BotPersonalityController` + dynamic switching (implemented).** The first behaviour change.
   Difficulty-gated so the lower tiers keep today's fixed personality.
   The guerrilla rule is currently a computed-but-unavailable candidate: it remains in the
   situation log's candidate field, while the active five-personality controller falls through
   to the next grantable rule.
4. **Main target selection (landed).** `SquadManagerBotModuleCA` consumes the
   master's target for proactive, unbounded picks only when `PreferMainTarget` is
   enabled; in-radius targeting is untouched, and empty preferred results fall
   back to the existing unrestricted selection.
5. **Counter demand and hints (implemented).** `MasterAiBotModule` issues the
   `SetBotCounterDemand` order; `BotCounterDemandController` owns the synced demand conditions;
   `ProvidesPrerequisite` maps those conditions to `demand.*` tokens, and composition
   `Prerequisites` consume them without new consumer-side C#. Signals use hysteresis, with
   per-tier sustained activation delays and immediate removal below the off threshold. Only a
   small set of pilot compositions ships initially.
6. **Fogged observation + `ScoutBotModule`.** Deliberately last among the behaviour changes,
   because it makes the bots temporarily weaker and it invalidates any tuning done against
   omniscient signals. This is the §9.1 decision; phases 1-5 are honest about being pre-fog.
   *Phase 6a (fogged observation + `RegionMemory` + `UseFoggedObservation`) landed 2026-09-27 —
   the master builds profiles from `BotFogMemory` instead of `World.Actors`; Phase 6b
   (`ScoutBotModule`: staleness x interest region targets, yaml-listed scout types, scout-loss
   danger marks now feed it) and 6c (the pre-commit risk
   gate: `IBotRegionThreatProvider` + `AttackRiskMargin` on `SquadManagerBotModuleCA`, gating the
   idle-squad commit only) and 6d (squad-side fogged scans: `IBotFoggedEnemyProvider` gates every
   `World.Actors` target scan to observed enemies, with `FrozenActorLayer` remembered buildings as
   fallback targets — remembered mobile units are re-observed by scouts instead of being chased at
   stale positions) all landed 2026-09-27, as did 6e (risk routing: a coarse A*
   over `RegionMemory` costed by remembered hostile value —
   `IBotRouteThreatRouter` on the master answers `RouteAroundThreat` with 1-4
   locomotor-checked waypoints; guerrillas keep their harass routes), all merged
   2026-09-27 — and 6f's first piece (artillery attach: `SquadCAType.Artillery`,
   rules-derived via max weapon range, hangs `ArtilleryHangBackCells` behind a
   parent assault squad and bombards only what the parent sees — no separate
   staging or support-follow yet) — phase 6 is done except 6f staging/support —
   `docs/design/AI_FRANSBOT_RESEARCH.md` §4.*
7. **Assign-layer missions (phase 7a, implemented).** The master publishes ordered, reserved
   `Raid` and `Defend` intent from fogged region memory; squad formation remains the execution
   owner's decision. `Recon` and `Secure` are deferred.
8. **Offline learning.** Aggregate logs, fit bandit priors per (faction, personality, enemy
   strategy), commit them as reviewed data (§6.1 tier 4). Nothing neural until balance is frozen.

Phases 1 and 2 are pure additions with no gameplay effect and can proceed while the balance
pipeline is still moving. Phase 3 is the first one that needs playtesting attention, and phase 6 is
the one that needs a tuning pass on everything before it.

### 10.7 Failure modes this shape is chosen to avoid

| Failure | Why it is avoided here |
|---|---|
| Duplicate authority (two writers of production or squads) | 10.1; enforced by the master owning no queues and no squads |
| Second instance of a `TraitOrDefault` consumer | §1.3; the master and the compositions module are singletons by declaration |
| Personality thrash | §4.5 sustained reaction delay + clamped hold + momentum; and every switch costs an order (10.4) |
| Desync from learning | §6.1 tiers; learned data is read at load or never touches synced state |
| Learned weights overfitted to bot-vs-bot play | §8.4 distribution shift; priors stay small and are reviewed as balance data |
| Losing today's behaviour on a bad phase | degradation rule in 10.1; set `PersonalityReactionDelay` negative to disable switching |
| Tuning invalidated by the fog switch | fog is phase 6, and phases 1-5 are labelled pre-fog rather than pretending otherwise |
| Stale reference to a personality-gated module after a switch | §1.6; CN shipped this bug and documented it — every such reference is re-resolved whenever the cached instance is not enabled |
| A borrowed detection threshold that never fires | §11.4; detection thresholds are fitted from phase-2 logs, only the hysteresis constants are imported |

---

## 11. Reconciliation of the five-agent research round

Five differentiated briefs went out (`AI-RESEARCH-BRIEFS.md`: literature, OpenRA archaeology,
decision maths, engine feasibility, yaml/migration). This section records what came back, what
survived checking, and what the answers changed in the design. The discipline is the one that made
the balance pipeline usable: **repository artifact > measured experiment > primary external source >
independent review > AI synthesis**. Where two replies disagree, the disagreement is kept as an open
decision in §9 rather than averaged into a compromise nobody verified.

### 11.1 What actually came back

| Brief | Delivered | Usable content |
|---|---|---|
| OpenRA archaeology (Grok) | **Yes**, with file paths and constants | CN's adaptive constants, the per-profile stale-cache trap, the "no in-family main-target focuser" gap, an anti-pattern list. Independently re-verified in §1.6 — the constants and the trap check out; two of its architectural conclusions did not (§11.2) |
| Decision maths | **Partly** — a design review, not the requested derivation | bounded/saturating features, personality/target decoupling, decision traces, confidence propagation (§11.3). No thresholds, no team-coverage shape |
| Engine feasibility | **No** — a restatement of the existing spec as a "handoff document" | nothing new; it also reported #324 as merged, which it is not |
| Literature | **No** — the reply in this round answered the observer-graph question instead | none for the AI briefs |
| Yaml / migration | **No** — a "synthesis matrix" asserting findings the other agents never produced (§11.2) | none admissible |

So one of five briefs is answered on its own terms. The literature, engine-feasibility and
yaml-migration questions are still open, and **§3's signal thresholds, §6.3's bandit sample sizes and
§2.7's migration steps still have no external evidence behind them**. That does not block phases 1-2
of §10.6, which deliberately need no thresholds: they log raw signals so the thresholds can be fitted
from Cameo's own matches instead of borrowed.

### 11.2 Claims rejected, with what falsifies them

Recorded because they were stated as settled fact, and two of them would have changed the design.

| Claim | Status |
|---|---|
| "The order-based `BotPersonalityController` is validated by CN's implementation" | **False.** CN grants the condition directly from the bot module and issues no order at all (§1.6). The bridge is Cameo's own invention, forced by §1.1 |
| "CN-style token lifecycle owned by one module is an acceptable alternative to the order bridge" | **Rejected**, same evidence. It is a §1.1 violation; that it apparently works in CN is not evidence that it is sound |
| "Misclassifying a Rush as a Turtle was proved fatal" | **Unsourced.** Plausible and probably directionally right, but no paper, no measurement. Not admitted to §1; if it holds, phase-1 logs will show it |
| "`S_def > 0.35` classifies heavy defences; `S_eco > 1.25` classifies aggressive expansion" | **Invented constants.** No derivation, no data. Thresholds come from phase-2 logs (§10.6) or not at all |
| "All five agents' research has been synthesised into the architecture" | **False**, per §11.1 |
| "PR #323 merged" / "PR #324 merged" | **False when asserted in round one.** Current check (2026-09-07): #324 merged on September 6 as `15a08466e`; #323 remains open/conflicting and its graph is adapted on the follow-up branch. Historical rejection is not current PR status |
| "Cameo bots are omniscient, and so is every bot in the family" | **Half true.** Correct for Cameo's squad targeting (§0.2), false for CN's strategy input (§1.6) |

### 11.3 Recommendations adopted, and what they amend

1. **Bounded, saturating features in the target score.** §4.3's weighted sum takes raw quantities,
   which lets one large economy or army number dominate every other term. Amended: every feature is
   normalised into `[0,1]` before weighting, using `x / (x + k)` for unbounded quantities (economy
   share, army value, damage) so that twice the value is not twice the attractiveness, with `k` per
   feature in the tuning block. Weights stay linear on top of bounded features.
2. **A decision trace on every strategic decision.** Not just the chosen personality and target, but
   the full candidate vector, the incumbent's momentum bonus, the winning margin and the gates that
   fired. This is what makes phase 2 of §10.6 worth shipping on its own: an observe-only master whose
   log says only "would pick Rush" cannot be debugged, while one that says "Rush 0.73, Tech 0.67,
   incumbent +0.15, margin +0.06, held by minimum-hold" can. Folded into §6.2 as the
   `decision` object; §9.9 covers how verbose it is allowed to be.
3. **Confidence travels with every signal.** "Saw two tanks" must not enter the transition table as
   "the enemy army is armour-heavy". Each per-enemy signal in §3.2 carries a confidence derived from
   observation age and coverage, and a switch below a confidence floor is not taken — it is logged as
   suppressed. This is also the mechanism that makes fog (§10.6 phase 6) a change of input rather
   than a rewrite of the decision layer.
4. **Contact memory is split out ahead of fog and scouting.** §10.6 phase 6 bundled the shroud gate
   with `ScoutBotModule`. Amended to three increments in order: (a) contact memory — remember what
   was seen and what shot us, forget it only when a visible cell disproves it, the CN shape in §1.6;
   (b) the shroud gate on the squad managers' actor scan, which is the actual §0.2 fix; (c)
   `ScoutBotModule`, which only has a job once (b) leaves gaps worth filling. Each is independently
   playable and (a) costs the bots nothing.
5. **Bandits come after an offline comparison, not as the cheap first win.** §6.3 frames bandit
   priors as the cheap first learning step. Amended: the cheap first step is an offline comparison of
   fixed vs dynamic personality on logged matches. A bandit that has not been shown to beat the fixed
   policy on Cameo's own data is not cheap, it is unfalsifiable.
6. **The master stays out of the economy.** Restating §10.1 because two replies drifted here: the
   harvester, MCV-expansion and base-builder modules keep their decisions; the master publishes
   economy and expansion pressure as hints and nothing else.
7. **No caching of personality-gated module references** (§1.6, last bullet). Any master-module
   reference to a per-personality module is re-resolved whenever the cached instance is not enabled.

### 11.4 Rejected as design changes

* **A five-module unsynced pipeline** (`FogPerceptionBotModule` → `OpponentModelBotModule` →
  `EnemyTargetingBotModule` → `PersonalityEvaluator` → controller). Four extra trait lifecycles,
  four more load-order and enable/disable interactions, for what are pure functions over one
  snapshot. §10.1's last rule stands: the master's stages are methods, not traits. The only new
  traits remain `MasterAiBotModule`, `BotPersonalityController` and eventually `ScoutBotModule`.
* **A richer snapshot up front** (snapshot age, per-enemy tech/air/armour shares, aggression score,
  economy pressure as separate fields). Every field needs a consumer in the same phase that adds it;
  otherwise it is unverified surface that the log makes look authoritative. The fields arrive with
  their readers.
* **A full enemy-strategy classifier in phase 2.** Phase 2 logs raw per-enemy signals only. Strategy
  labels are added once the logs show the signals actually separate the strategies — this is the
  disagreement between the archaeology reply (own-state and fortification only, as CN does) and the
  §3 design (a per-enemy classifier), and §9.7 keeps it open rather than resolving it by assertion.
* **Any fixed numeric threshold before phase-2 logs exist**, including the CN constants as Cameo
  defaults. CN's numbers are the starting point for *hysteresis* (they were tuned against a switching
  bot in the same engine family), not for *detection*.

---

## 12. Combined arms: the arsenal tracker, composition, formation, siege and air doctrine

**Maintainer order, 2026-09-28** (paraphrased; every clause below is binding):

> Add a unit/defence tracker that keeps count of every unit and defence built and where they
> usually are, and that is **self-learning**. The AI must use **everything in its arsenal, in the
> right ratio**; build squads of the right composition; move them **in formation** (tanky units in
> front, long-range artillery behind, infantry supporting the tanks, aircraft giving air support)
> while **fast scouts** roam to spot enemies and decide where to attack next. Build **quick air
> strike teams** that hit high-value targets along the route of **least remembered resistance**.
> **Most importantly, always move so as to minimise losses: no suicide runs into defences.** Stop
> just outside their range, take them down with artillery, and move in only when every defence in
> the area is destroyed or the army is strong enough to destroy them. Helicopters and spaceships
> give air support to the ground army; fighters pick off enemies that are out of position and join
> big battles; bombers take out high-value targets, sometimes defences and power plants.

Two standing laws shape every item. **§10.1: one owner per decision.** Each item below changes the
*inputs* of a decision an existing module owns; none adds a second producer, a second squad
manager, or a second target picker. **§6.1: learning tiers.** In-match learning is live bot
reasoning (host-local, unsynced, acts only through orders; §1.1) and is free. Cross-match learning
is a **committed data file read at match start and frozen**, fitted offline from harness runs
(§6.2a Stage C) and reviewed like a balance change. "Self-learning" means both: the bot adapts
inside a match, and the batch harness plus the fitter improve its priors between matches.

### 12.1 What already exists (do not rebuild it)

| Order clause | Shipped today | Where |
|---|---|---|
| Enemy memory, "where they are" | `BotFogMemory` + `RegionMemory`: remembered hostile value per region, fog-honest | `OpenRA.Mods.Cameo/Traits/BotModules/BotFogMemory.cs` (§6a) |
| Enemy composition | `IBotEnemyCompositionProvider` from fog memory; Versus-scored counters | `AdaptiveCounterProduction.cs` (#605) |
| Who hurts us | `CombatAnalysisBotModule`: per-role threat weights from damage events, nemesis | `OpenRA.Mods.Cameo/Traits/BotModules/CombatAnalysisBotModule.cs` |
| Compositions | personality-tagged compositions, zero C# (§1.4) | `UnitCompositionsBotModule.cs` |
| Artillery behind the assault | artillery squads attach to an assault and hang back (`ArtilleryMinRangeCells`, `ArtilleryHangBackCells`) | `SquadManagerBotModuleCA.cs` (6f, #554) |
| Support follows | `SquadCAType.Support` trails its parent (`SupportFollowRangeCells`) | same (6f) |
| Rally before assault | `StageBeforeAssault` / `StageAssemblePercent` / `StageTimeoutTicks` | `GroundUnitsStageStateCA` (6f) |
| No suicide (partial) | pre-commit gate `AttackRiskMargin`: squad value must beat remembered regional threat | `SquadManagerBotModuleCA.cs` (6c) |
| Avoid defences en route (ground) | `UseRiskRouting` → `IBotRouteThreatRouter` waypoints around remembered threat | `GroundStatesCA.cs:508`, `RegionRouter.cs` (6e) |
| Flee when losing | fuzzy attack-or-flee | `AttackOrFleeFuzzyCA.cs` |
| Scouts | `ScoutBotModule`: cheap fast units cycle the stalest regions | `ScoutBotModule.cs` (6b) |
| Target priorities | rules-derived tags `artillery`, `harvester`, `production`, `superweapon`; per-squad `*PriorityTags`; air hunts artillery | `BotTargetTags.cs` (6g) |
| Donor stack | `FransRiskModel` (role-aware cell/route risk), `FransGroundDefendForcePreservationGuard`, `FransCombatIntel` (last-seen force estimate), `FransAirCommander` | `OpenRA.Mods.Fransbot/Traits/` — merge one module at a time, A/B each (§0a) |

### 12.2 The gaps, precisely

1. **No arsenal ledger.** Nothing counts *per unit type* what was built, lost, or destroyed, on
   either side; `PlayerStatistics` only holds per-player totals. So the bot cannot learn "our
   type X trades well against this enemy", and cannot know "the enemy usually has N defences of
   range R at choke C".
2. **No ratio law.** Production follows demand counters and compositions, but nothing guarantees
   every role the faction owns is used, in a target mix.
3. **No formation.** Artillery and support trail; tanks, infantry, AA and air do not hold roles
   relative to one another, and a squad moves at each unit's own speed.
4. **Siege is missing.** The 6c gate says *whether* to attack, not *how*: there is no stand-off
   outside defence range, no "artillery first", no "commit when the area's defences are gone".
5. **No air doctrine.** Air squads are one type with one tag set; risk routing is ground-only
   (`GroundStatesCA` is its only consumer), so strike aircraft fly straight through remembered AA.

### 12.3 The arsenal tracker (phase CA-1) — the foundation for everything else

* **Own ledger, per unit type:** built, alive, lost (count and cost), value destroyed (cost of
  victims killed), per enemy faction. **Mechanism:** a Cameo shadow of
  `UpdatesPlayerStatistics` (engine `PlayerStatistics.cs:215`; carried by 1,243 actor nodes, so no
  yaml changes). Its `INotifyKilled.Killed(self, e)` already receives the attacker actor; the
  shadow keeps the engine behaviour verbatim and additionally books `victim cost` to
  `(attacker owner, attacker type)` and `victim type` to the victim owner's ledger. The ledger
  lives on a player-level `BotArsenalTracker` trait and is read only by bot code (never `[Sync]`).
  Prove the shadow with a Cameo-only field (CLAUDE.md rule 7).
* **Enemy ledger, fog-honest:** distinct enemy actors *seen* (dedupe by actor id), per rules-derived
  role (§12.4), with the region they were seen in; for defences also the **max weapon range**
  (read from rules once the type is known). Extends `RegionMemory`; never enumerates unseen
  actors (`audit_fog_honesty.py` ratchet).
* **Where they usually are:** per region, a decaying average of remembered enemy defence value and
  army value — a heat map the siege planner (§12.6) and air router (§12.8) read.
* **In-match learning:** for each own role, the trade ratio `value destroyed / value lost` against
  this enemy, smoothed (prior-weighted), becomes a production *weight input* to the existing owner
  (`UnitBuilderBotModuleCA` via the master's demand inputs — §10.1).
* **Cross-match learning:** the match record gains the per-type ledger; `tools/ai/` aggregates it
  per (own faction, enemy faction, role and type) across harness runs and writes
  `mods/cameo/ai/learned/arsenal_priors.yaml` — **committed, reviewed, read at match start**.
  Every harness batch is therefore a training run; nothing is learned from a file only one client has.
* **Record-only first:** CA-1 ships as telemetry (match and situation logs) with no behaviour
  change; the in-match weight is a separate, A/B-tested step.

### 12.4 Roles are derived from rules, never listed

Extend `BotTargetTags` into `BotUnitRoles` (same load-time derivation, no actor ids, 25 factions):
`frontline` (high HP × armour, short range), `skirmisher`, `anti_infantry` / `anti_armour` (from the
weapon's Versus profile, as `AdaptiveCounterProduction` scores it), `artillery` (existing tag),
`anti_air`, `scout` (fast, cheap, long vision), `support` (heal/repair), `transport`, and for air:
`gunship` (VTOL/hovering, ground weapons — helicopters and hovering spaceships), `fighter`
(air-to-air weapons), `bomber` (bomb/drop attacks or fixed-wing ground-only), `air_transport`.
New **target** tags: `power` (positive `Power`), `defence` (building with an armament), `tech`.

### 12.4a Squad membership rulings (maintainer, 2026-09-29)

1. **Artillery squads are the `^ArtilleryTemplate` and `^ArtilleryTankTemplate` units ONLY.**
   Both templates now declare `BotRoles: Roles: artillery` (`rules/defaults.yaml`; 50 actors
   resolve to it). This replaces the range rule the code uses today: `SquadManagerBotModuleCA
   .ArtilleryMinRangeCells` (10) splits *any* ground unit with a 10-cell weapon into an artillery
   squad, and `BotTargetTags` tags *any* 12-cell unit as artillery.
2. **Fire-support units form their own squads, with tanks, and protect the artillery.**
   `^FireSupportTemplate` declares `BotRoles: Roles: firesupport` (37 actors: e.g. the Tesla tank,
   the GDI exosuit). They are support, never assault or raid units.
3. **Ships are their own squads, never mixed into ground or air squads.** A ship is a `naval`
   locomotor (the `navalunit` role's rule; `hover` and `amphibius` units such as hovercraft move on
   land and stay ground units). Today `FindNewUnits` checks `GuerrillaTypes` before
   `NavalUnitsTypes` and sends anything unlisted to a ground squad, and #627 measured **19 naval
   units missing from `NavalUnitsTypes`**: those ships are drafted into ground squads now.
   Applying `navalunit` is the list fix; a guard that a naval unit can never enter a ground or air
   squad is the code fix.

None of the three is a guerrilla (§2.8a excludes them). **Open, C# in `SquadManagerBotModuleCA`:**
read the `artillery` role instead of the range rule, add the fire-support squad and its escort
of tanks, and the naval guard. Owners per §12.10: CA-3/CA-4 (NOVA) for the squad composition,
Claude for the roles and the `navalunit` application; Claude-Local (who integrated the DF code
below) reviews the C#.

**Interlocks with the defence code on master `297c626f4`** (all in `SquadManagerBotModuleCA`):
* **Naval check first.** `PrepositionDefenceTick` and `ProtectOwn` draft the idle pool (`AttackBase`,
  not Building/Harvester/Aircraft), so a ship missing from `NavalUnitsTypes` can be drafted into a
  *land* protection squad today. Put the naval branch **before** the guerrilla branch in
  `FindNewUnits` (guerrilla assignment goes through `OpenGuerrillaSquad`, which respects
  `MaxGuerrillaSquads` / `MaxGuerrillaSquadsLate`), so a ship never reaches the idle pool.
* **`ReleaseDefenders`** routes released defenders by `GuerrillaTypes` / `HarasserTypes`, else to the
  idle pool. The guerrilla role follows automatically once it has `Targets`; a fire-support squad
  type needs its own branch there, or released fire-support units fall back into the idle pool.
* **`FastSquadsReactToThreats`** moves only Guerrilla/Harass squads. Fire-support squads guard the
  artillery and are not fast squads, so they stay out of it.
* **Artillery by role** does not touch the combat predictor (`BotUnitProfiles` is independent of
  `ArtilleryMinRangeCells`).

### 12.5 Composition and ratios (phase CA-3)

* A **target mix by role** per personality (starting values in yaml; e.g. frontline 35 %,
  anti-infantry 20 %, artillery 15 %, anti-air 10 %, air 15 %, scout 5 %), shifted by the enemy
  ledger (counters) and by the learned trade ratios, with a **floor** so every role the faction
  can build is used. Production fills the largest *deficit* against the mix — through the existing
  builder, as a demand input.
* Squads are formed to the same mix (a main assault without frontline or AA waits for them,
  bounded by `StageTimeoutTicks`), and compositions (§1.4) remain the personality flavour.

*Landed (2026-10-01, NOVA, `nova/rolemix-mixes`):* the six genericbot personalities carry their
starting `RoleMix` rows in ai.yaml, gated by `SquadManagerBotModuleCAInfo.UseRoleMix` (default
false — a mix without the flag is inert data, and the deficit pick checks the flag, so writing
a mix can never silently arm behaviour; switch group `J_rolemix_production` arms the six
personality instances only — `SquadManagerBotModuleCA@classic` carries neither flag nor mix).
Starting shares: rush skirmisher/anti-infantry heavy, steamroller frontline+artillery, turtle
artillery+anti-air, expansion balanced + extra scouts, tech adds the air split, guerrilla
skirmisher+scout+gunship. Pairs with UW-1's derived weights (group `I_derived_unit_weights`),
which reads the same mixes through its own flag for the share×strength table.

### 12.6 Siege and force preservation (phase CA-2) — the maintainer's "most importantly"

The rule, in order of precedence:

1. **Never path through remembered defence coverage** (6e, now fed by §12.3 ranges).
2. **Stop at stand-off**: the assault halts at `max remembered defence range + margin` from the
   nearest remembered defence of the target area (margin per difficulty on the DESIGN.md §19.1 equal-step line).
3. **Artillery first**: the attached artillery squad (6f) engages the defences from outside their
   range; frontline screens the artillery; air (§12.8) may strike defences.
4. **Commit** only when (a) no remembered defence in the area survives (re-verified by sight), or
   (b) `effective squad value ≥ R × (remembered defence value + remembered army in the region)`,
   where "effective" is Versus-weighted (the 6c gate, generalised) and `R` is a per-personality
   input the Aggression axis moves.
5. **Retreat** before the trade turns (fuzzy flee exists); a failed siege writes the loss into the
   region memory so the next plan avoids it.

*Landed (2026-09-29, flag-gated):* `SiegeEvaluatorBotModule` computes the rules
2/4/5 verdict each `EvaluationInterval` for every Rush/Guerrilla/Harass squad
above a value floor — stand-off cell on the `maxRange + StandOffMarginCells`
line, `BotCombatPredictor.Predict` on the squad's own unit profiles vs the
remembered defences' observed types for the "effective" check (4b), commit at
`CommitRatioPercent` — and serves it through `IBotSiegeAdvisor` to the assault
states when `BehaviourEnabled` is on (the CA-2b A/B variable). Rule 5's
write-back landed as `IBotSiegeFailureMemory`: a retreat-verdict *transition*
records one failed siege against the nearest covering defence's
(owner, region) on `MasterAiBotModule` — `RegionMemory` is a per-publish
snapshot, so the durable count lives on the module and stamps onto each
snapshot's `Region.FailedSiegeCount/LastFailedSiegeTick`; with
`SiegeMemoryEnabled` the remembered failures inflate `obstacleValue`
(`SiegeFailureWeightPercent` per failure inside `SiegeFailureMemoryTicks`),
so the next plan reads the wall that beat it as heavier. Both flags default
false — each is its own isolated A/B variable.

Donor to evaluate first: `FransRiskModel` + `FransGroundDefendForcePreservationGuard`.

*Guard evaluation (2026-10-01, DAWN):* `FransGroundDefendForcePreservationGuard` (shipped in the
V1.29.48 revendor) gates a defend bid: commit ≥ trigger AND reserve below floor → shrink the package
to a reserve target, waived when the response is an emergency (utility ≥ 0 or sub-`LongEta` travel).
The genericbot equivalent lands at the two full-pool draft sites in `SquadManagerBotModuleCA`:
`ProtectOwn` (attack ping) and `PrepositionDefenceTick` (predicted threat / escort request), both of
which committed 100% of the idle pool. `UseDefendPreservation` keeps
`max(MinReserveUnits, pool × ReservePercent/100)` back once the pool reaches `TriggerUnits`; the
donor's emergency maps to "attacker / rally inside `MaxBaseRadius` of the base centre". Behind
`O_ca2_defend_reserve`, bit-identical off. `FransRiskModel` remains open (route-risk scoring is
ZG/IM-adjacent, not a defend-side gap).

### 12.7 Formation movement (phase CA-4)

Engine orders have no formation, so the bot moves a squad **in steps along its route** (orders
only, §1.1): per step the frontline goes first; infantry holds just behind/alongside the tanks;
anti-air sits inside the group; artillery hangs back (6f exists); support trails (6f exists);
gunships hover over the frontline centroid. The group advances at the **pace of its slowest
frontline unit** (units that run ahead wait at the step point). Fast scouts are never in the
formation — they run ahead on their own (6b).

### 12.7a Concave engagement (phase CV, maintainer order 2026-10-01)

> *Maintainer:* "units are not running into a fight in a straight line but engage in a perfect concave shape that
> allows them all to fire at the same time they arrive in range. The larger the army the wider the concave. Having
> the perfect formation before any fight is the key to win any engagement."

§12.7 governs the **march**; CV governs the **deployment** between contact and the first shot. Today a Rush squad
that meets the enemy goes straight from `GroundUnitsAttackMoveStateCA` to `GroundUnitsAttackState` and every member
attack-moves at one point: the column arrives one unit at a time and loses the first seconds of the fight piecemeal.
CV inserts one state, **`GroundUnitsConcaveStateCA`** (Rush squads only; armed only by the `AssaultFormationBotModule` provider, default off),
entered from `GroundUnitsAttackMoveStateCA` (§19.3 — squad states remain the sole order authority; orders only, §1.1).

**Geometry — a pure, deterministic planner `ConcaveEvalCA` (integer math, no RNG, unit-tested):**
1. **Anchor `A`**: the centroid of the *observed* enemy combat units in contact (only `IsPreferredObservedEnemyUnit`
   — fog-honest), else the squad target's position (a remembered/visible building or defence). Approach axis
   `d` = unit vector `A → frontline centroid`. **Enemy front depth** `F` = the largest projection of an observed enemy
   onto `d` (how far the enemy line already sits toward us); 0 for a lone target.
2. **Per-member radius** `rᵢ = F + MaxRangeᵢ + StageMarginCells` — every member stands the SAME distance
   (the margin) outside its OWN range, so long-range units naturally form outer ranks and everyone is the same
   step from firing. Weaponless members (and scouts) are not placed; they keep the plain order.
3. **Ranks**: members whose `rᵢ` lie within `RankBandCells` of each other share one arc (the band radius is
   the band's minimum `rᵢ`, so nobody in it stands inside its range).
4. **Width grows with the army**: a band of `n` members needs arc length `L = n × spacing` (spacing =
   `Spacing`, infantry half of it). The arc's angle is `θ = L / r`, centred on `d` — a bigger army
   is a wider, never a denser, concave. If `θ > ConcaveMaxArcDegrees`, spacing first compresses down to
   `MinSpacing`; members that still do not fit go to a second arc `RankGap` further out.
5. **Slot assignment without crossing**: sort the band's members by their current bearing around `A` and its
   slots by bearing, pair in order. Paths never cross, so wings fill from the side they already stand on.
6. **Terrain**: each slot snaps to the nearest cell within 2 cells that the member's locomotor can enter and reach
   (same domain). If fewer than `MinValidSlotPct` of the slots are valid (a choke, a cliff edge), CV aborts:
   the squad engages as today.

**Phases (`GroundUnitsConcaveStateCA`):**
* **Trigger** (in the attack-move state, BEFORE the existing `AttackScanRadius` switch to the attack state): the
  squad is Rush, an enabled provider arms it, it has ≥ `MinSquadSize` weaponed ground members, the provider's
  same-ground cooldown has run, and either an observed enemy combat
  unit is within `FanoutTriggerCells` of the frontline centroid, or the squad target is within that distance.
  Fog limits how early a contact is seen; a partial concave formed late still beats a column.
* **Form**: each placed member gets a `Move` (not `AttackMove` — nobody gets drawn into the fight early) to its slot.
  Orders are re-issued only to members that are idle and off their slot; every order spends one
  `IBotActionBudget` action (§19.1 — lower tiers form worse, on the same straight line); a denied member keeps its
  last order. The plan re-runs only if `A` moves more than 3 cells or an eligible member joins while forming (a late joiner gets a slot), at most once per 25 ticks.
* **Commit** when ANY of: ≥ `AssemblePercent` of the placed members are within 1.5 cells of their slot; the form
  timer reaches `StageDeadlineTicks`; a member took damage or an observed enemy is inside some member's own range
  (the enemy engaged us — never keep forming under fire).
* **Synchronised arrival**: on commit, each member's time to its own firing range is `tᵢ = margin_i / speedᵢ`
  (its real distance to range, over its locomotor speed); member `i`'s `AttackMove` toward `A` is issued
  `max(t) − tᵢ` ticks after the commit tick, so the slowest starts first and **all arrive in range together**.
  When the last delayed order is out, the state hands over to `GroundUnitsAttackState` (focus fire, kiting and
  pull-back take over, §MI).
* **Abort** to the attack-move state when the anchor is gone (no observed enemy and the target is invalid); after a
  commit or an abort the squad cannot re-enter CV against the same ground for `RefanoutCooldownTicks` (the provider's per-squad cooldown, restarted on arm, commit and abort).

Supersedes the ring slot on `devin/ember/mi-concave` (`a64a294ae`, not merged): fixed 30°-per-member angles under a
135° cap (an army past 5 units packs denser instead of wider), slots by ActorID (paths cross), no form or commit
phase (units still arrive one by one), no terrain check, and it would have changed group A's shipped default behaviour
without a new switch. Its integer mirroring trick (`WRot` conjugate for the negative wing) is reused.
Switch group **AG_assault_fanout** in `tools/ai/increment_switches.yaml` (the single switch); A/B in INC-4.

**Unified with ATK-1 (2026-10-02).** The two duplicate implementations (CV here, NOVA ATK-1 in the former §12.21) are
merged into this one (§19.3 one module per decision). *From CV:* all geometry (`ConcaveEvalCA` — range-matched radius,
rank bands, member-count arc width, bearing pairing, mirroring), the state machine (`GroundUnitsConcaveStateCA`:
form with `Move`, terrain snap, commit on formed/timeout/under fire, staggered commit) and its single entry hook in the
attack-move state. *From ATK-1:* the settings seam — `AssaultFormationBotModule` / `IBotAssaultFormation` /
`AssaultFormationSettings` are the ONLY home of the tunables (CV's 13 `Concave*` fields left `SquadManagerBotModuleCAInfo`)
and the provider's presence (`genericbot && assault_fanout`) is the ONLY switch, so classic has no provider and stays
bit-identical; the per-squad same-ground cooldown (`RecordFanout`, replaces `SquadCA.ConcaveCooldownUntilTick`); late-joiner
handling (roster change re-plans, rate-limited). *Dropped:* ATK-1's fixed-radius far-side ring (`FanoutRadiusCells`), its
map-bounds-only slot check, its Stage-state transition and band trigger (a staged squad reaches the concave through the
attack-move state). Field map: `MinSquadSize`=min units, `FanoutTriggerCells`=contact cells, `AssemblePercent`=formed %,
`StageDeadlineTicks`=form ticks, `SlotReachCells`=terrain-snap radius, `ArcDegrees`=arc cap, `RefanoutCooldownTicks`=cooldown;
plus `StageMarginCells`, `RankBandCells`, `Spacing`, `MinSpacing`, `RankGap`, `MinValidSlotPct`. `ai.yaml` writes this
section's values (min 4 / contact 16 / formed 80% / 150 ticks / arc cap 150°) — ATK-1's ring-tuned 12 / 60 / 500 / 180 were
measured on the old fixed ring and do not carry over (coordinator 2026-10-02); the next increment A/B measures the unified state.

**Objective shape (merged DAWN's assault fan, 2026-10-02).** The §12.20b assault fan was a second implementation of
"deploy before the first shot" inside `GroundUnitsAttackMoveStateCA` (§19.3: one module per decision). It is now the
second SHAPE of this state, chosen by the anchor: `GroundUnitsConcaveStateCA.ShouldEnter(owner, out shape)` returns
**Army** (observed armed enemies within `FanoutTriggerCells`; the range-matched concave above; gate = the
`IBotAssaultFormation` provider, `AG_assault_fanout`, off on master), **Objective** or none. *Objective* = no armed enemy
in contact (none in the attack scan either, `NearestEngagedEnemy` null), the squad target within
`AssaultEngageRadiusCells` (18) of the frontline centroid, `FormationMovement` on, siege advisors say Advance, squad off its
cooldown. Gate = today's fan gate (`FormationMovement` + Rush), so it stays LIVE exactly where the fan was (genericbot
personalities) and needs no provider; classic sets neither `FormationMovement` nor a provider, so it is unchanged. Settings
stay `AssaultFanRadiusCells` / `AssaultFanMinSlots` / `AssaultFanMaxSlots` / `AssaultEngageRadiusCells` /
`AssaultSyncHoldTicks` (same names and defaults). One planner: `ConcaveEvalCA.ProngCount` (members/2 clamped 3..8),
`ObjectiveProngs` (prongs on a 200-degree front around the objective, centred on objective -> centroid, wings mirrored with
the `WRot` conjugate, integer math) and `PlanObjective` (member -> prong by `ActorID % prongs`, as the fan did); the state
terrain-snaps each slot like the concave's (off-map prongs project onto the ring). Machinery shared with the army shape:
form (`AttackMove` to the prong, re-issued while idle, late joiners re-plan), commit on formed / hold expiry /
under fire (`NearestEngagedEnemy`), the pending-order commit, hand-over to `GroundUnitsAttackState`, and the same
orders-only micro-action spend. Differences: the commit is "formed" when every prong is within 6 cells of its slot or
`AssaultSyncHoldTicks` expired, the push is zero-delay (together, as the fan) - no stagger; the same-ground cooldown (750
ticks, the provider's `RefanoutCooldownTicks` default, same radius = `AssaultEngageRadiusCells`) is kept ON THE SQUAD
(`SquadCA.DeployCooldownCell/Tick`), not the provider: the objective shape runs with no provider, and a squad-scoped record
dies with its squad with nothing to prune. The attack-move state has ONE entry into the deploy state (after the contact-first
all-in) and no fan fields.

### 12.7b Contact-first all-in (maintainer 2026-10-02) — and the ONE "the fight is on" test

> *Maintainer, spectating a 6v6:* a large blob stood in formation while part of the force was already trading fire.

Formation (the march §12.7, the concave §12.7a incl. its objective shape = the former assault fan) is for BEFORE the first shot. When the fight is
on for ANY member, a Rush squad commits wholesale on the same tick (Lanchester: staging while the local fight runs feeds
the enemy one prong at a time). `GroundStatesCA.NearestEngagedEnemy` is the single definition, used by the attack-move
state's all-in, the concave's entry (declines) and the concave's commit (zero-delay under-fire commit):

* **the fight is on** = a visible enemy (`VisibleEnemiesNear`, fog-honest) and a squad member are within weapon range of
  each other — EITHER side's `MaxRange` — counted over every member, placed or not, or a member took damage (concave).
* Not "an enemy is visible within `AttackScanRadius`" (the first cut, `22f6e5ee9`): the concave stages just OUTSIDE
  weapon range on purpose, so a 12-cell sight test cancelled it before it could form (coordinator 2026-10-02).
* The all-in goes THROUGH `GroundUnitsAttackState` (target = the engaged enemy): it attack-moves every member on the same
  tick and keeps the shipped group-A micro (focus fire, kiting, pull-back). The first cut re-issued one grouped
  `AttackMove` from the attack-move state every tick and never left it, so those never ran for a Rush squad in contact.
* `SquadManagerBotModuleCA.ContactFirstAllIn` (default true) — `@classic` sets false: the A/B reference keeps the
  leader-scan engage.

### 12.8 Air doctrine (phase CA-5)

* **Gunships (helicopters, hovering spaceships): close air support** — attach to the main
  assault like support squads and engage what the frontline engages.
* **Fighters: air superiority and pick-off** — hunt enemy aircraft and **isolated** enemy units
  (far from their army and from remembered defences), and join big battles near the own army.
* **Bombers: strike teams** — 2–4 aircraft, targets by tag priority (`superweapon`, `tech`,
  `production`, `power`, `harvester`, `artillery`; `defence` when it opens a siege), routed over
  the **air-threat layer** (remembered anti-air coverage) with minimum exposure, regroup and
  return. This is risk routing for air — today's router is ground-only.
  *Landed first slice (2026-09-28):* the 6e router now picks its remembered-threat
  read by the leader's domain — airborne leaders pay `AntiAirValue`, ground
  leaders pay `ArmyValue+DefenceValue` — and `AirAttackStateCA` transits a fresh
  target through those waypoints (`Fly` chain + queued `Attack`, skipped by the
  per-tick re-issue so transit is not cancelled). The doctrine split (gunship CAS,
  fighter pick-off, bomber strike-team targets) still waits on CA-1 roles.

### 12.9 Scouting decides where to attack next

`ScoutBotModule` (6b) keeps running; add **spawn-directed recon** (§9 item 12 (a): `mpspawn` cells are
public map data) and feed each scout report into the main-target / region choice: attack the
most valuable region whose remembered defence the available force beats (§12.6 rule 4), not the
nearest one.

**Shipped shape (DAWN `devin/dawn/ca6-scout-target-intel`, switch `N_ca6_target_intel`).** The loop
closes in both directions on remembered intel only:

- *Target choice → scouting:* `ScoutBotModule.UseTargetIntelBias` adds `TargetIntelBonus` interest to
  regions remembered as the current `IBotMainTargetProvider.MainTarget`'s footprint, so scouts refresh
  the intel target choice and raid bidding consume instead of wandering stale regions uniformly.
- *Scouting → target choice:* `MasterAiBotModule.WeightIntelAge` subtracts a `Saturate(age,
  IntelStaleTicks)` term in `TargetScore`; a sighting's value decays toward the never-seen maximum as
  it ages, so freshly-scouted enemies win near-ties and a scout report measurably moves the target.
- *Beatability:* `WeakIncludesDefence` (earlier CA-6 seed, own A/B variable) folds remembered static
  defence into the `weak` term — the force-vs-defence check of §12.6 rule 4.
- The Fransbot donor side of §9 item 12 shipped with the V1.29.48 revendor: `FransGeneralBotModule`
  runs `mpspawn` recon probes off public map data and `FransGroundCommanderBotModule` bids bounded
  remembered-building raids (`GroundRememberedRaidMaximumAge`); the genericbot `EnemySpawnBonus`
  spawn-watch landed earlier. CA-6 adds no duplicate of either.

### 12.10 Order of work, owners, and the gate for each phase

Every phase: record-only telemetry first where it applies, then the behaviour behind a yaml
switch, then **an A/B on A Nuclear Winter against the current master** (≥ 8 matches, both spawns,
`--bot-a hard --bot-b classic --swap-bots`, compared with a master run in the same session). A
phase lands only if it does not lose to master; the standing target stays "beat `classic`".

| Phase | What | Owner | Depends on |
|---|---|---|---|
| **CA-1** | arsenal tracker: `BotUnitRoles`/new target tags, own ledger (stats shadow), enemy ledger with defence ranges and region heat map, match/situation log fields; then the in-match production weight | **Claude** | — |
| **CA-1b** | offline fitter: aggregate harness ledgers → `learned/arsenal_priors.yaml`; harness runs more matchups | **Claude** (was Devin Cloud, out of tokens 2026-09-28) | CA-1 log fields |
| **CA-2** | siege and force preservation (§12.6) incl. evaluating the Fransbot donor guard | **DAWN** | CA-1 defence ranges |
| **CA-3** | role mix production + squad composition (§12.5), personality starting mixes | **NOVA** | CA-1 roles |
| **CA-4** | formation movement (§12.7) | **NOVA** | CA-3 |
| **CA-5** | air doctrine: gunship CAS, fighter pick-off, bomber strike teams, air-threat routing (§12.8) | **EMBER** | CA-1 roles |
| **CA-6** | scouting → target choice (§12.9), with §9 item 12 (a)+(b) | **DAWN** (owns recon) | CA-1 heat map |
| **SG** | scout-rebuild rationing and garrisons as defences (§12.12) | **Claude** | — |
| **EX** | expansion planner: field score, placement, refinery per field, MCV hand-off, enemy creep (§12.13) | **Claude** | CA-1 (fog memory) |
| **PL** | personality leads (§12.14): telemetry, then each lead's budget lean | Claude / NOVA / DAWN per row | CA-1 |

CA-2 and CA-5 may start on the parts that do not need CA-1 (reading the existing
`RegionMemory`), and switch to the tracker's ranges when it lands.

Research round 2 ([`AI_DEEP_RESEARCH.md`](AI_DEEP_RESEARCH.md) §9) adds phases that interleave
with these: **CP** combat predictor (the single engage/commit/retreat authority; CA-2's commit
rule and the 6c gate become its inputs), **ZG/IM** zone graph + influence layers (the region set
and "where they usually are" — ZG-a topology, ZG-b fog-honest territory/ownership and ZG-c
zone-backed `RegionMemory`/`RegionRouter` behind `UseZoneTopology` have landed; the square grid
stays the fallback whenever no enabled, built `TacticalMapBotModule` exists; **IM-1** then laid
the layers on that index space — `BotInfluenceLayers` publishes `threat_ground`, `threat_air`,
`interest`, `own_strength` and `staleness` per region on the master snapshot behind
`UseInfluenceLayers`, remembered threat decaying toward a per-zone EMA as sightings go stale —
the spec's "where they usually are". IM-2 spreads each published threat across the region
boundary (`InfluenceSpreadPercent` of every neighbour, one hop — a remembered unit's reach
covers the ground past the gate it holds), and `RouteAroundThreat` now risks squads on the
blended+spread layer instead of the raw per-region memory. `ScoutBotModule` is the first
consumer; the siege stand-off edge (CA-2), air-threat routing (CA-5), raid/guerrilla
interest÷threat (§12.9) and expansion safety (EX) stay with their owners), **UT** utility
strategist (absorbs CA-3's blended squad manager),
**MI** budgeted micro (with CA-5), **OM** opponent model and **LG** league harness (with CA-1b).

### 12.11 What a spectator saw, measured (maintainer review of the #633 A/B, 2026-09-29)

The maintainer watched `hard` vs `classic` (td_gdi, A Nuclear Winter) and reported suicidal
infantry at garrisoned buildings, infantry blobs without tanks, Humvees instead of tanks, no
artillery, idle armies and a timid base. The arsenal ledger (§12.3) of the 8 master-half matches
plus 3 branch-half matches confirms each, per match:

| `hard` built | per match | the composition asks for (`UnitsToBuild`, td_gdi vehicles) |
|---|--:|---|
| Humvee Mk2 + Humvee | 59.4 + 13.0 | Humvee Mk2 weight 5 of 100 |
| battle tank, Predator, Mammoth (all marks) | 1.2 + 1.5 + 0.6 | 45 + 20 + 15 of 100 |
| MLRS + Archer artillery | 0.9 + 1.1 | 10 of 100 |
| minigunner, grenadier, rocket soldier | 184.5, 81.1, 81.5 | — |

Causes, each traced to code:
1. **Humvees are scout replacements that jump the queue.** `td_gdi_humvee`/`humveemkii` are
   `ScoutBotModule.ScoutUnitTypes`. Below `MaxScouts` (2) the scout module calls
   `RequestUnitProduction` on every scan (`ScanInterval` 50), and `UnitBuilderBotModuleCA` builds a
   requested unit at the start of every production cycle, **before the cash check and outside the
   queue rotation**. Scouts die at the enemy base (`EnemySpawnBonus` 20000), and a new Humvee can be
   drafted by `FindNewUnits` into a guerrilla squad before the scout module claims it (both types are
   in `GuerrillaTypes`). The count stays below 2, and the vehicle queue builds Humvees instead of the
   composition's tanks. Fix: §12.12 item 1.
2. **Garrisoned buildings count as free.** The civilian houses (`^CivBuilding` →
   `^GarrisonableBuilding`) carry `AttackOpenTopped` and `ChangeOwnerOnGarrisoner`. Once enemy
   infantry enter, `BotFogMemory.Classify` marks them `Defence`, but their `Value` is the house's
   `Valued.Cost`, and the houses have **none** (`v02`, `v03`: no `Valued`; a GDI guard tower: 500).
   The occupants are cargo, invisible to the memory. The 6c risk gate therefore sees a garrison as
   worth 0 and lets infantry walk in one by one. Fix: §12.12 item 2.
3. **No artillery first, no tanks in front:** not built yet (CA-2 siege, CA-4 formation, §12.6–12.7).
4. **Idle blobs:** `IdleBaseUnitsMaximum: 50` holds the army at base until squads form. The CA-2/CA-3
   owners take it with the commit rule.
5. **A timid base:** `BaseCrawl` takes every building under 1,000 cost (`BaseCrawlChance: 100` in
   `ai.yaml`; the C# default is 50), but aims it at a **random** resource cell within 50 cells, else at
   the enemy building nearest the defence centre, found by
   scanning `world.ActorsHavingTrait<Building>()`: omniscient. `ExpansionAppetiteHint` has no reader
   (§5). The engine `ResourceMapBotModule` also counts enemy units per field without fog. Fix: §12.13.

**Army-mix tracking (maintainer 2026-09-29):** *"add a unit tracking to see the army composition so
that you can easily notice … just Humvee and infantry spam instead of building a mix of all
available units."* `tools/ai/army_mix_report.py <support dirs>` reads the arsenal ledger of any
batch and prints, per bot type, the units built per match: shares by class (infantry, vehicle,
aircraft, ship; harvesters and MCVs apart as economy), the heavy and artillery share of the
vehicles, and the top types. Classes come from the resolved rules (`Aircraft`, the locomotor,
`Infantry` target type, `Armor.Type` Heavy/Superheavy, the `artillery` role). It **flags** one type
above 25 % of all units, heavy vehicles below 5 % of vehicles, and artillery below 5 % (each a
flag), and exits 1 when anything is flagged. On the master half above it flags all three for
`hard` (minigunner 34 %, heavy 4 %, artillery 1 %). Run it after every batch.

### 12.12 Scout rebuilds and garrisons (maintainer rulings 2026-09-29; owner Claude)

1. **A scout request is rationed.** `ScoutBotModule` requests a replacement at most once per
   `ScoutRebuildCooldownTicks` (`genericbot`: 3000; 0 = the old request-every-scan). So the
   requests can no longer take over the vehicle queue, whatever happens to the scouts.
2. **A garrisoned building is a defence, priced by its garrison.** An enemy-owned `Garrisonable`
   building (owned means occupied: `ChangeOwnerOnGarrisoner`) is valued at
   `Garrisonable.MaxWeight × GarrisonOccupantValue` when it has no `Valued` cost, and is a `Defence`
   like a tower. `genericbot`: 250, half the median cost (500) of the 323 buildable garrisoning
   infantry, because an observer cannot see how full the house is; 235 garrisonable buildings have
   no cost (capacity 1–40). So the 6c risk gate, the risk router (6e) and the siege planner (CA-2) all avoid
   it, stand off from it and shell it. Fog-honest: ownership is visible, and the value is a rules
   constant, never the real passenger list.

Both are behaviour changes, so each runs the §12.10 gate: a Nuclear Winter A/B (≥ 8 matches, both spawns).

### 12.13 The expansion planner (phase EX; maintainer rulings 2026-09-29; owner Claude)

> *"Always expand, always build more harvesters, always build more units, never be idle, always try
> to pressure and attack, always build towards the enemy and towards the resources. Always occupy all
> the resource fields … make a formula estimating where to place the next building so you can get
> the most money in the shortest amount of time … distance and value … and the less enemies the
> safer."*

**Rulings.** (a) Every resource field within building reach gets **one refinery**, protected by
towers. (b) The base builder never idles: **every building it places moves the base closer to the
next resource field**, and power plants make the line when nothing else is due. (c) **Fog:** where
the fields are and how rich they are at match start is public map data (like the spawn points).
Depletion, enemy refineries and enemy defences count only once seen, through `BotFogMemory` /
`RegionMemory`, never through `ResourceMapBotModule`'s omniscient enemy counts. (d) **Creeping toward
the enemy base** scales with difficulty (DESIGN §19.1) **and** aggressiveness (the personality's
Aggression axis).

**The score of a resource field `f`** (every constant is a yaml knob, learnable by route 2, §6.4):

    V_f    = value of f: its initial resource cells × value per cell, minus the depletion seen
    hops_f = ceil( max(0, d_f − R_reach) / R_link )   d_f: distance from our nearest building that gives buildable area
    C_f    = refinery cost + hops_f × link cost + towers_f × tower cost
    T_f    = C_f / income + hops_f × link build time + refinery build time   (seconds until it pays)
    S_f    = 1 / (1 + threat_f / max(own force near f, 1))   threat_f: remembered enemy value near f
    score_f = V_f × S_f / (T_f + τ₀)

Higher value ranks higher, a shorter distance ranks higher (fewer hops, so a smaller `T_f`), and
fewer remembered enemies rank safer. `τ₀` keeps a field next to the yard from dividing by nearly
zero. A field with a seen enemy refinery is not a candidate. It becomes a raid target for Rush and
Guerrilla (§12.14).

**Placement.** The planner keeps a target field `f*` (the best score, re-chosen every
`ExpansionReplanTicks`). The next non-refinery building goes on the valid cell that **minimises
the path distance to `f*`**, ties broken toward home, so the base walks toward the field one
building at a time. Once `f*` is in reach, its refinery goes on the free cell nearest the field's
resource centre on the home side, ahead of every other building; then `towers_f` towers, where
`towers_f` grows with `threat_f`, placed on the side of the highest remembered threat. When
`hops_f` exceeds `MaxLinkHops`, the MCV module is asked to found a yard at `f*` instead
(`McvExpansionManagerBotModule` owns the deployment, §10.1).

**The MCV goes to the best field, and never alone (maintainer 2026-09-29).** An MCV's site is
the field with the best `score_f`, where `d_f` is the MCV's own path distance and the link terms
become its travel time. Each factor comes from its own analytics: value from the map's resource
layer (public, ruling (c)), distance from the pathfinder, and safety from `RegionMemory`'s
remembered threat along the route **and** at the site (the 6e router's cost). Before the MCV
moves, the planner asks the squad manager for an **escort**, sized so its Versus-weighted strength
beats the route's remembered threat (the CP predictor's ratio). The escort travels with the MCV
and stays to guard the new yard until its first tower stands (`OutpostGuardTicks`). The request
goes through the squad manager's existing protection path (`ProtectOwn` / `PrepositionDefenceTick`,
§12.4a), never a second squad manager (§10.1). The hook in `SquadManagerBotModuleCA` is agreed
with its owner (NOVA, CA-3/CA-4).

**Creeping toward the enemy.** The enemy's probable base (a spawn, or seen buildings) is one more
candidate, with `score = CreepWeight × difficulty step × Aggression`. It wins only when no field
scores higher. Its towers go on the enemy-facing edge.

**EX-0 as built (2026-09-29).** `ExpansionPlannerBotModule` (genericbot) scores every field we hold no
refinery at, every `ReplanTicks` (250), and writes a `debug.log` line whenever the target changes
(`EX-0 target field …`) or it has none, with the reason (`EX-0 no target …`). Measured choices:
`V_f` is the field's resource-cell count at its first scan: a common factor leaves the ranking
unchanged, so no price per cell is invented. The refinery and the cheapest building (the link) are
whatever the base builder's own queues can build now, with their real cost and `GetBuildTime`.
Income is `PlayerResources.Earned` over `IncomeWindowTicks`. `d_f` is measured from buildings that give
buildable area only: a captured derrick or a garrisoned house does not extend the base, and the
first live run picked a field 35 cells away because of one. `R_reach` = `ReachCells` (6),
`R_link` = `LinkStepCells` (4). It is straight-line distance for now; path distance is an EX-1
refinement. Enemy threat comes only from `IBotRegionThreatProvider` (fog-honest), never from
`ResourceMapBotModule`'s own enemy counts. The one own-actors pass is manifested in
`fog_honesty_manifest.json`.

**EX-1 as built (2026-09-29).** A CA-side `IBotExpansionTargetProvider` (the pattern of
`IBotRegionThreatProvider`) lets `BaseBuilderBotModuleCA` ask for the target field without naming a
Cameo type. In the `BaseCrawl` case, which `ai.yaml` already takes for every building under 1,000
cost (`BaseCrawlChance: 100`), the builder first tries `findPos` toward that field: the placeable cell
nearest to it, within `BaseCrawlRadius`. It falls back to the old logic only when no cell fits. The
planner publishes the field only with `DriveBaseCrawl: true` (`genericbot`). `classic` shares
`BaseBuilderBotModuleCA@generic` but has no enabled planner, so it keeps today's placement and stays
the A/B reference. Each steered placement writes `EX-1 BaseCrawl <type> at <cell> toward field <cell>`
to `debug.log`. Live: `hard` put its second power plant at 12,36 toward field 16,36 (tick 1,554).
Refineries and defences still use their own placement; EX-2 adds refinery-per-field.

**EX-2 as built (2026-09-29).** While the target field is in reach (0 hops) and unclaimed, the planner
reports `WantsRefineryAtExpansionTarget`. `HasAdequateRefineryCount()` then answers "not adequate"
even above the fixed optimum (initial + additional + per base), which is ruling (a): every field in
reach gets a refinery. The refinery case places it with `findPos` toward the field, limited to
`ClaimRadiusCells` (8), so it lands where it claims the field; an MCV-requested refinery keeps
priority. "Claimed" is decided from rules: an own actor with the `Refinery` trait within the claim
radius (or the resource map's own count). **Loop guard:** every refinery gained while the same field
stays unclaimed is a missed claim, and after `MaxClaimAttempts` (2) the field is parked for
`ParkTicks` (3000) with a `debug.log` line (`EX-2 parked field …`). So a placement that keeps missing
cannot become a refinery loop. `DriveRefineries: true` (genericbot) needs `DriveBaseCrawl`, which
publishes the target. Live: the home field was claimed by tick 1,500, then the target moved to field
7 at 45,32 (7 hops), and the base built a line of power plants toward it (17,43 → 21,38 → 30,33 by
tick 4,034).

**EX-2 spread fix (2026-10-01).** The claim path above only fires while a field is wanted and in
reach; the fallback then sampled the resource cells *farthest from the newest own refinery inside the
same conyard annulus* — the far edge of the home field — so repeated refineries stacked on one field
(seen live: three on the home field). Two repairs, both keyed on a mounted `IBotExpansionTargetProvider`
(`BaseBuilderBotModuleCA.HasExpansionGuidance`, so classic — which shares the base builder — is
unchanged): (a) that fallback now first keeps only cells of fields no own refinery serves — a field is
served when a refinery stands within `RefineryUnservedRadiusCells` (10) of the index's resource centre
(`PreferUnservedResourceCells`, own-actor cells only, fog-honest) — spreading each new refinery onto a
new field; an all-served annulus keeps the old candidate set. A pure cell-to-refinery distance filter
was tried first and is wrong: a big field's far edge is still the same field. (b) `RequestLocation`
counts refineries already *requested* for an index toward `MaxRefineryPerIndice`, not only built ones,
so queued MCV requests can no longer stack on one index before `PlayerRefineryCount` catches up.
(c) The claim placement itself searched an annulus around the BASE centre bounded by
`MinBaseRadius`/`MaxBaseRadius` — a crawled-to field beyond `baseCenter + MaxBaseRadius + claimRadius`
had zero candidate cells, so the claim silently failed and the refinery fell back to home (seen live:
crawl reached the field, no refinery followed). The claim annulus now centres on the field with radius
`ExpansionTargetClaimRadius`, sorted toward the base so the refinery takes the home-facing edge.

**Greedy expansion (2026-10-01, same section family).** `DriveMcvRequests` lets the planner ask for a
construction MCV itself once per re-plan — while a free field at `McvMinHops` or farther exists, cash
stays above `McvRequestReserve` (1500), and owned yards + construction MCVs + queued MCVs stay under
`McvTargetCount` (3). The engine module alone only builds a second MCV above a 4000-cash trigger, so
without this the second expansion waits minutes; where the MCV goes is still EX-3's job, and its LC3
hand-out parking is untouched. `ShouldRequestMcv` is the pure gate; all inputs are own-side counts or
public map data, so fog-honest, and the flag lives only on the genericbot planner.

**UT-4 (switch group `U_ut4_expansion_appetite`, off until the increment A/B):** the
TechRush&harr;Expansion axis scales that appetite — `EffectiveMcvTargetCount` adds up to
`ExpansionAxisBonusMcvs` (2) at the Expansion pole and subtracts up to `TechRushAxisMinusMcvs` (1,
floor 1) at TechRush. Expansion personalities spread wider; TechRush ones hold the home front and
tech. Neutral axis = verbatim count.

**EX-2c (same section, 2026-10-01; not §12.13's reserved EX-4 "enemy creep").** The claim driver no
longer waits for the crawl target itself to be in reach: `BestClaimField` picks the best-scoring
free field whose hops are already 0 — any own buildable area counts, so a freshly deployed outpost
yard claims its local field the same replan instead of queueing behind the walk to a different
target. The provider publishes it as `RefineryClaimTarget` (the queue manager falls back to
`ExpansionTarget`); when the crawl target is in reach the pick is identical to EX-2's, and
parked/missed-claim bookkeeping is unchanged and still per-field.

**EX-2d (same section, 2026-10-02).** A fully depleted field's live `ResourceCellsCenter` collapses
to a degenerate cell (the resource map recomputes it every scan and an empty field has none), so a
depleted field could score or claim toward the map corner. `EffectiveCenter` falls back to the
remembered first-seen centre whenever the field reports no live cells — Tiberium regrows in place,
the field's location does not move. Armed-smoke finding: two depleted fields both surfaced at
`0,0` as expansion candidates.

**EX-3 as built (2026-09-29; maintainer ruling: a small engine hook).** `McvExpansionManagerBotModule` is
engine code, so the hook lives in the engine (`cameo-mod/OpenRA` `d5d8b2a685`, branch
`claude/mcv_expansion_site`, on top of the pin `042b2fa787`; pinned in `mod.config`). Right after
`GetExpansionCenter`, the module asks the player's `IBotMcvExpansionSiteProvider` traits for a site and
deploys toward the first non-null one. The engine still decides **when** to expand (its cash and
yard-count triggers); the planner decides **where**. The planner answers only for a mobile MCV (a yard
relocation keeps the engine's choice) and only among fields at least `McvMinHops` (3) links away, which
the building line would not reach soon. It ranks them by `V × S / (distance from the MCV + McvTauCells)`;
value, safety and distance each come from their own analytics, as ruled. Each site is logged
(`EX-3 MCV … sent to field …`). `genericbot` only (`DriveMcvSite: true`). **Still open:** the escort
and outpost guard, whose hook in `SquadManagerBotModuleCA` is proposed to its owner (NOVA), not built.

**Order of work** (each step: telemetry first, then behaviour behind a yaml switch, then the A/B):
EX-0 compute and log `score_f`, `f*` and the placement choice (no behaviour change); EX-1 replace
`BaseCrawl`'s random/omniscient target with `f*` and the distance-minimising placement; EX-2
refinery-per-field priority plus towers; EX-3 the MCV hand-off; EX-4 the enemy creep, scaled per
(d). The CA base builder is CA-sync-tracked: the planner lives in a Cameo module that the builder
consults (a pull interface, as §5 prescribes for the master's hints), so the CA file changes by a
small hook only.

### 12.14 Personality leads: one top priority each, measured against the enemy (maintainer ruling 2026-09-29)

DESIGN §19.1c gives every personality **one top priority, measured as a lead over the enemy**:
`lead = own metric / remembered enemy metric`. It is fog-honest: the enemy side comes only from
what was seen (§3). While the lead is below its target, the personality's budget leans toward the
lead's driver. The other priorities keep their floors, so no personality abandons the rest.

| personality | top priority | own metric | enemy metric (seen only) | driver it leans on | owner |
|---|---|---|---|---|---|
| Expansion | out-earn | income per minute | seen refineries × seen harvesters (the economy proxy, §3.2) | EX planner (§12.13), harvesters | Claude |
| Steamroller | out-produce | army value produced per minute | seen production buildings, seen army growth | unit builder budget, factories | NOVA (CA-3) |
| Guerrilla | out-scout, map control | regions seen within `StaleAfterTicks`, share held | regions with remembered enemy presence | scouts, guerrilla squads | DAWN (CA-6 recon) |
| Rush | pressure: attack early and often, kill the economy | attacks launched, enemy economy value destroyed | none: it is absolute (first-attack tick, attack frequency) | squad manager attack thresholds | NOVA / DAWN |
| Turtle | more defences | own defence value | remembered enemy defence value | base builder defence share | Claude (base builder) |
| Tech | tech up faster | research and upgrades done, tier reached | seen tech buildings and upgrades | research queue priority | Claude (base builder) |

Telemetry first, as for EX-0: every lead goes into the situation log, so the targets are tuned
from data rather than invented (§10.6).

**Telemetry (2026-09-29, NOVA):** the situation log now records the Steamroller and Rush lead
inputs, record-only — no decision reads them, and the enemy-side numbers stay fog-honest
(remembered sightings only). Feeds: Steamroller own = `production_per_game_min`, enemy =
`production_buildings` + `army_value_delta`; Rush = `attacks_launched`, `attacks_per_game_min`,
`first_attack_tick`, `econ_destroyed`.

- `own.production_window`, `own.production_per_game_min` — arsenal-ledger created-cost delta since
  the last snapshot, raw and per game minute.
- `own.econ_destroyed_window`, `own.econ_destroyed` — seen-cost of enemy harvester/refinery types
  this bot's units destroyed, window and cumulative.
- `own.attacks_launched`, `own.first_attack_tick`, `own.attacks_per_game_min` — cumulative
  Rush/Harass/Guerrilla/Air/Naval squads across all squad managers (counters persist while a
  personality is disabled, so switches don't erase history — same semantics as `losses_by_role`), the first launch's
  tick, and the per-minute rate.
- `enemies[].army_value_delta` — net seen army growth since the previous snapshot (can go negative).

**PL-1 (NOVA, branch nova/personality-leads):** the Steamroller and Rush leads are now
computed on every snapshot and published on the situation (`own.enemy_production_per_game_min`,
`own.steamroller_lead`, `own.rush_lead` in the situation log) — always-on telemetry; the new
`UsePersonalityLeads` flag (default **false**, increment-switch group `G_personality_leads`)
gates only the consumers. Enemy production is estimated fog-honestly as Σ positive
`army_value_delta` per game minute plus `PersonalityLeadEnemyProductionPerBuildingPerMin`
(200) per remembered production building; `steamroller_lead` is own/enemy — with nothing
remembered the denominator reads as at-target (1), not infinite. `rush_lead` is
`min(attacks_per_game_min / target, clamp(first_attack_target / first_attack_tick))`, 0
until the first launch, with a flat +0.25 attack-score credit once any enemy economy value
has been destroyed. Consumers reach the leads through `IBotPersonalityLeadProvider` (the
usual CA seam — Mods.CA does not reference Mods.Cameo): `PersonalityLeadLean(personality)`
returns the snapshot's multiplier, gated by flag, running-personality match and lead < 1.
Steamroller leans `UnitBuilderBotModuleCA`'s `ProductionMinCashRequirement` /
`MaximiseProductionCashRequirement` floors; Rush leans `SquadManagerBotModuleCA`'s
`minAttackForceDelayTicks` reset — each by up to `PersonalityLeadMaxLeanPercent` (50),
linear in the deficit.

**PL-2 (DAWN, 2026-10-01):** the Guerrilla lead gains its consumer legs — `PersonalityLeadLean`
now answers "guerrilla" from `Situation.GuerrillaLead`, and both drivers lean while it trails:
`ScoutBotModule` adds up to `GuerrillaLeadExtraScouts` (2) to its effective `MaxScouts`, linear
in the deficit (`EffectiveMaxScouts`), and `SquadManagerBotModuleCA` raises the `JoinGuerrilla`
roll toward 100 by the same deficit (`EffectiveJoinGuerrilla`) — a configured 0 stays 0, so
non-guerrilla personalities are never revived by the lean. Both loops are honest: scouts are the
lead's numerator driver directly, and raiders crossing the map are incidental scouts feeding the
same `regions_fresh`. Gated by the same `UsePersonalityLeads` (group `G_personality_leads`) —
flag-off leaves `MaxScouts` and `JoinGuerrilla` bit-identical, and a non-guerrilla personality
reads lean 1.0 via the seam's personality match. UT-2's axis keeps the guerrilla squad CAP; the
lead leans the FILL — different knobs, different signals, they compose without double-counting.
The Expansion/Turtle/Tech leads remain telemetry-only.
### 12.15 UT-1 — the utility axes, first slice (NOVA, 2026-10-01; AI_DEEP_RESEARCH.md §5.1)

The maintainer's axis ruling lands as `BotUtilityAxes`: three bipolar posture axes —
Turtle↔Rush, TechRush↔Expansion, Steamroller↔Guerrilla — each [0,100] with 100 the
second-named pole. Every snapshot, `MasterAiBotModule.Rebuild` folds the snapshot's own
fog-honest inputs into `target = rest[personality] + terms x UtilityInputWeightPercent`,
then EMA-steps the published axis toward it by `UtilityAxisDecayPercent` — quiet inputs
decay back to the resting value, and a personality switch moves the rest, not the axis.
Every raw input is squashed (`Saturate`/`HurtShare`) before its capped term, so no single
term dominates; the term units sit in `BotUtilityAxes.cs`.

- **Published, always on:** `BotSituation.UtilityTurtleRush`/`...TechRushExpansion`/
  `...SteamrollerGuerrilla`, plus `own.utility_turtlerush` etc. in the situation log —
  explainable against the same record's inputs (§5.1's "logged with their inputs").
- **Seam:** `IBotUtilityAxes` (OpenRA.Mods.CA) is implemented by the master; absent or
  disabled providers read neutral 50 — never a behaviour change.
- **First consumer, flag-gated:** `SquadManagerBotModuleCAInfo.UseUtilityAxes` (default
  false) scales the `minAttackForceDelayTicks` reset by TurtleRush — Rush 100 → x0.6,
  50 → x1.0, Turtle 0 → x1.5. Flag off is byte-identical; `@classic` never arms it.
- **Second consumer (UT-2):** under the same flag the time-ramped guerrilla-squad cap
  scales by SteamrollerGuerrilla — Guerrilla 100 → x1.5, 50 → x1.0, Steamroller 0 → x0.5.
- **Third consumer (UT-3, 'defence share'):** `SquadManagerBotModuleCAInfo.
  UseUtilityDefendReserve` (default false, own flag so group M keeps isolating the delay
  lean) scales the CA-2 defend reserve by TurtleRush — `DefendReserveAxisPercent` maps
  Turtle 0 → `DefendReserveTurtleFactorPercent` (x2.0), 50 → x1.0, Rush 100 →
  `DefendReserveRushFactorPercent` (x0.5), linear between. It only modulates a reserve
  `UseDefendPreservation` already keeps — emergency and small pools bypass it exactly as
  before; it never creates a reserve on its own. Switch group `Q_ut3_defend_share`
  (bare key + `@classic` skip; compose with O_ca2 to have a reserve to scale).
- **Arm:** switch group `M_utility_axes` (explicit `@`-keys on the six genericbot
  personality instances; K and L remain reserved for DAWN).
- Rest points per personality live on `MasterAiBotModule` in ai.yaml (`Utility*Rest`
  dicts, keyed `rush`/`turtle`/...; missing → 50).
### 12.16 DI-1 — the Director's tension wave, publish-only slice (NOVA, 2026-10-01; AI_DEEP_RESEARCH.md §7, DESIGN.md §19.2)

The Director ruling lands as `BotDirector`: an L4D-style pacing wave over the bot's own
tempo — **build-up → pressure → climax → relief** — computed once per situation snapshot
from fog-honest scalars only (own army value, launch deltas, the loss/kill sample
windows; nothing enumerates enemy actors). **Publish-only:** no consumer, no yaml flag —
flag-off and flag-on are identical because there is no flag. The ruling stands: pacing
and aggression telemetry only, never income, unit stats or vision.

- **Tension [0,100].** While the own army is massed (`OwnArmyValue ≥ DirectorArmyMassValue`,
  default 2500 — personality-agnostic, between `RushMaxEnemyArmyValue` and
  `SteamrollerMinArmyValue`), each snapshot adds `DirectorTensionRisePerSnapshot` (3) plus
  impatience: one point per `DirectorImpatienceTicksPerPoint` (1500) ticks since the last
  delivered attack — since game start while none was ever launched — capped at
  `DirectorImpatienceMaxPerSnapshot` (10) per snapshot so a never-attacking bot cannot
  jump thresholds in one step. A thin army sheds `DirectorTensionDecayPerSnapshot` (2)
  instead; impatience only feeds a massed army — there is nothing to be impatient *with*.
- **Phases.** `BuildUp` promotes to `Pressure` at `DirectorPressureThreshold` (60);
  `Pressure` crests into `Climax` at `DirectorClimaxThreshold` (85) or immediately on a
  launch (`attacksDelta > 0` — an attack out of BuildUp is just early, the spec's crest
  condition is Pressure-only). `Climax` relaxes into `Relief` once the post-attack kill
  window flattens — no launches and no fresh kill-sample delta for
  `DirectorReliefQuietTicks` (750, armed at Climax entry and refreshed by any fresh
  attack/kill) — or immediately on a heavy own-loss spike
  (`freshLossDelta ≥ DirectorLossSpikeValue`, 600 = `EmergencyLossThreshold`; the spike
  also breaks `Pressure`, the other armed wave). `Relief` resets tension to
  `DirectorReliefTension` (20) and re-arms to `BuildUp` at
  `DirectorReliefExitThreshold` (45).
- **Hysteresis everywhere a boundary could flutter:** `Pressure` relaxes only
  `DirectorHysteresis` (10) below its entry point, and `Relief`'s exit sits above its
  reset level — a tension value parked in a dead-band keeps its phase by history, which
  the tests prove by driving the same readings through both directions.
- **Published, always on:** `BotSituation.DirectorTension`/`.DirectorPhase`, the
  `IBotDirector` seam on the master module (CA-side; a disabled or never-snapshotted
  provider reads 0/`BuildUp`), and `own.director_tension` + `own.director_phase` in the
  situation log. State is deliberately NOT in `MasterAiBotSavedState` — a save/load
  restarts the wave at 0/`BuildUp`, which for record-only telemetry is the honest reset.
- **DI-2 — the phase-scaled launch bar (consumer slice).** `SquadManagerBotModuleCA`
  re-targets the dispatch bar every check: `desiredAttackForceValue`/`Size` are
  multiplied by a per-phase percent — `DirectorBuildUpForceScalePercent` (100, the
  baseline and also what a disabled/absent provider reads), `Pressure` (85),
  `Climax` (55 — the wave's release: launch on a smaller pool), `Relief` (150 —
  rebuild past the baseline before committing again). Scaling the *bar* rather
  than the stored desired force means a phase change mid-wait takes effect
  immediately — a loss spike into `Relief` raises the bar that same tick instead
  of next cycle. Zero stays zero, so `SquadValue 0` configs keep their trivially
  passing value check. The chosen surface deliberately avoids
  `minAttackForceDelayTicks`, which `UseUtilityAxes` and personality leads already
  multiply — no shared-knob ordering, no cross-switch interaction. Armed by
  `UseDirectorPacing` (switch group P), flag-off = scale 100 = bit-identical.
  A Director change is itself an A/B candidate that must beat master
  (DESIGN §19.2).
### 12.17 TC-1 — the team blackboard, publish-only slice (NOVA, 2026-10-02; AI_DEEP_RESEARCH.md §11)

The Team Commander ruling lands its foundation as `IBotTeamMember` +
`TeamBlackboard` (CA-side, next to `IBotDirector`): every allied bot publishes a
`TeamBroadcast` once per situation snapshot — refreshed at the same point where
`director.Observe` folds the pacing wave — and every bot can read the allies'
half of the board. It is cheap because **every bot of a match runs on the host**
(§1.1): allied bots read each other's PlayerActor traits directly, so the
blackboard is unsynced by design — no sync work, no network traffic. Fog-honest
by construction: only own-side scalars and ally-published data cross it; nothing
enumerates enemy actors.

- **What a broadcast carries.** `SnapshotTick`, `OwnArmyValue`, `UrgencyLevel`
  (0/1/2 = Normal/Pressured/Emergency — the Cameo `BotUrgency` ordinals carried
  as an int because CA cannot reference that enum), the DI-1 wave verbatim
  (`DirectorTension`, `DirectorPhase`), the committed `MainTarget`,
  `RequestsDefence` (urgency ≥ Pressured) and `DefendPosition` — the own base
  centre while under pressure (the `BaseBuilding` centroid the `NearestCells`
  scoring uses), `WPos.Zero` when help isn't needed or no base stands. A
  disabled or never-snapshotted provider publishes `TeamBroadcast.Empty` —
  never a behaviour change.
- **The summary.** `TeamBlackboard.Collect(me)` folds the broadcasts of every
  allied bot (`World.Players` filtered to `IsBot && IsAlliedWith` — the same
  seam `AlliedCommitments` already uses, one `FirstEnabledTraitOrDefault` read
  per ally) into a `TeamBlackboardSummary`: allied-bot count, summed army
  value, max tension, an any-Climax flag, the defend-request count and the
  largest same-`MainTarget` group (allies committed to the same enemy). The
  caller's own broadcast is NOT folded in — a bot reads its own scalars
  directly; the summary answers "what is the rest of the team doing".
- **Liveness, one rule for every consumer (2026-10-02, review finding 4.2):**
  `TeamBlackboard.ValidBroadcast(p, b, now)` is the central freshness contract
  `CollectBroadcasts` applies before any aggregation — the publisher's
  `WinState` is `Undefined` (OpenRA keeps `Player`/`PlayerActor` after defeat,
  so a dead ally's last broadcast would otherwise hold its expansion/capture
  claims and defend requests open forever), `SnapshotTick > 0`, and
  `now - SnapshotTick <= MaxBroadcastAgeTicks` (600 = four snapshot intervals).
  No consumer may invent its own freshness test.
- **Published, always on:** five `own.team_*` fields in the situation log —
  `team_allied_bots`, `team_army_value`, `team_max_tension`,
  `team_defend_requests`, `team_shared_target`. In 1v1, or on a team without an
  allied bot provider, every field reads 0 — absence is the honest answer, not
  an error.
- **Publish-only:** no consumer, no yaml flag — flag-off and flag-on are
  identical because there is no flag. TC-2's consumers are already named in
  §11, all deferred: synchronised attack windows, defend-request answering,
  expansion-claim deconfliction, role-split bias and human-ally beacons.
- **First consumer (TC-2a — synchronised attack windows):** `SquadManagerBotModuleCAInfo.
  UseTeamSyncAttacks` (default false) folds the allied blackboard's `AnyClimax` into the
  launch-bar scale — `TeamSyncForceScale` takes `min(ownPhaseScale,
  DirectorClimaxForceScalePercent)` while an ally's wave crests, so every team's bots
  release inside the same fleeting window. Runs standalone (pacing-off reads scale 100)
  or composed with DI-2; a 1v1 or absent ally provider yields `AnyClimax = false` —
  bit-identical. Switch group `R_tc2_sync_attacks`.
  Every Rush launch that commits without a taken provider card emits a
  `secure:<enemyPlayer>` attempt record (Committed at launch, Superseded by the next
  wave, Released when the squad stands down intact, Success/`done` the tick the named
  enemy's WinState decides, Failed only if the wave dies) — the massed assault
  predates the mission grammar,
  and without the record `team_coordination_report`'s `shared_push` sees only the
  rare economy-raid path. The record names the enemy the wave steers toward
  (the card it couldn't afford, else `EffectiveMainTarget`); classic has no mission
  providers and no main target, so it stays silent.
- **Second consumer (TC-2b — defend-request answering):** `UseTeamDefendAnswers` (default
  false) adds a third channel inside `PrepositionDefenceTick`, below own threat and own
  escort requests: `TeamBlackboard.TopDefendRequest` picks the most urgent broadcast
  (ties to the weakest ally), and the answer is synthesised as a `BotProtectionRequest`
  — rally, draft, AttackMove and rolling hold-expiry reuse the escort path verbatim.
  The ally's position sits outside our base radius, so the CA-2 reserve still keeps a
  floor at home, and `TeamDefendAnswerMinPoolUnits` (default 8) means a thin pool stays
  home entirely. `CollectBroadcasts` exposes the per-ally detail the summary drops.
  The answer emits `defend_answer:<requesterKey>:<rallyCell>` attempt records (Committed
  at the confirmed rally, Released on hold expiry/supersede, Failed if the squad dies —
  one open attempt per id, so the rolling hold refresh extends instead of spamming) so
  `team_coordination_report`'s `defend_missions` counts the answers this path makes —
  the protection channel predates the mission-card grammar and otherwise wrote nothing.
  Switch group `S_tc2_defend_answers`; inert in 1v1.
- **Third consumer (TC-2c — expansion-claim deconfliction):** the broadcast gains
  `ClientIndex` (the publisher's own index) and `ExpansionClaim` (the bot's planner
  target, `WPos.Zero` when none — own-side intent, publish-always, inert without a
  consumer). `ExpansionPlannerBotModuleInfo.UseTeamExpansionClaims` (default false)
  then makes the planner skip a free field an outranking ally already claims —
  `AllyClaimWins` gives the field to the lower `ClientIndex`, a stable precedence both
  bots compute identically, so a contested field converges instead of both allies
  yielding forever or two refineries landing on one patch. `AllyClaimRadiusCells`
  (10) is the contest distance. Switch group `V_tc2_expansion_claims`; inert in 1v1
  because no allied broadcasts exist. (An ally's *built* refinery is deliberately not
  enumerated — `world.Actors` is omniscient and fog forbids reading ally positions
  outside shared vision; the claim broadcast is the honest channel.)
- **Fourth consumer (TC-2d — role split):** `MasterAiBotModuleInfo.
  UseTeamRoleSplit` (default false) spreads the TechRush&harr;Expansion RESTING
  point across the allied bots by participant-key rank — `TeamRoleRank` counts
  allied `ParticipantKey`s ordinally below mine, `RoleSplitBias(rank, teamSize,
  shift)` spreads the endpoints to ±`TeamRoleSplitShift` (20), rank 0 taking the
  Expansion pole. The bias moves the effective rest itself, so the axis parks on
  it and decays back to it like an authored rest. Computed from static keys,
  never from the drifting axes — a mirrored `hard`/`hard` team converges to
  expander+techer by construction, no oscillation possible. No new broadcast
  field: `ParticipantId` arrived with the TC-3 identity fix (map-side bots
  share the host `ClientIndex`, review 4.4 — an index rank would collapse
  every map-side team to rank 0). Switch group `W_tc2_role_split`;
  inert in 1v1.
- **Fifth consumer (TC-2e — capture-claim arbitration):** the broadcast gains
  `CaptureClaims` (the union of every enabled `IBotCaptureClaimSource`'s live
  target cell centres — `EngineerBotModule`'s capture missions and
  `GarrisonContestBotModule`'s contest claims; own-side intent, publish-always).
  `TeamBlackboard.ClaimsAheadOf` folds the allied half into the position set of
  every outranking publisher (strictly lower `ParticipantKey`, the same
  InternalName identity the coalition fold uses — `ClientIndex` cannot order
  map-side bots), and each module's `UseTeamCaptureClaims` (default false)
  gates the stand-down: new claims on a claimed cell are skipped, in-flight
  ones are released (superseded). Switch group `BF_team_capture_claims`;
  inert in 1v1. See §12.26.
**Telemetry (2026-10-01, NOVA):** the §13.1 discipline counters are published on every
snapshot — `own.banked_cash` (`PlayerResources.Cash + Resources`), `own.brownout_ticks`
(per-tick `PowerManager.ExcessPower < 0`), `own.idle_production_ticks` (per-tick, one count
per enabled `ProductionQueue` sitting with no current item and nothing queued — each idle
factory counts separately) and `own.production_queues`. Own-side trait reads only —
record-only, publish-always, no consumer and no flag; the LA analyst reads them for §13.1's
drive-to-zero goal, and a save/load restarts the counters at 0 (honest reset, same as DI-1).

### 12.18 TC-3 — the coalition general: from blackboard to hivemind (EMBER design, 2026-10-02)

The maintainer's §11 ruling already fixes the shape: **a world-level `BotTeamCommander`
owns the team plan; each bot's master reads it as an input.** This section is the
implementation design for that ruling plus the 2026-10-02 maintainer request — merged
squads under one commander, nearest-army rescue, expansion assist, collective territory
coverage — and the RTS-teamwork literature it draws on.

**What the literature says (surveyed 2026-10-02).**

- *Lanchester's Square Law* (Zero-K Strategy Treatise): two pooled forces fight at the
  square of their combined numbers — the mathematical case for merging allied armies onto
  one target instead of each bot duelling its nearest enemy. The treatise's team rule is
  literal: "attack the one in front of the ally next to you" — concentration, not
  front-line mirroring. The anti-square corollary (chokes bound simultaneous engagement)
  is why waves converge *in time* rather than clump *in space*: a coalition push wants
  same-target arrivals in one window, not one blob walking a choke (§12.7 formations keep
  their own spacing).
- *Organisational paradigms in RTS* (AAMAS 2019, SC:BW): individual / swarm / market /
  hierarchical structures compared; hierarchical — subordinates executing a superior's
  plan — is the paradigm the maintainer's "coalition general" names. Our equivalent must
  not add a second order-issuer (§19.3): the general is publish-only, orders stay with the
  existing owners.
- *BiCNet* (UCL, SC combat) and *RoMIX* (role-factored MARL): coordination quality scales
  with bidirectional shared state and explicit role specialisation — the two things TC-1's
  blackboard and TC-2d's role split already provide.
- *Sector responsibility* (team-play doctrine across ZK/Bar-family multiplayer): teams
  divide the front into owned sectors so coverage has an owner and help travels to a
  neighbour, not across the map.

**The hivemind is a function, not a unit.** Every allied bot already reads every other
ally's broadcast off the same host-side blackboard (§12.17). Feeding the same input set
through a pure, order-deterministic fold — `CoalitionPlan(broadcasts ∪ own)` evaluated by
*every* member each snapshot — makes all members compute the *identical* team directive
without election, messaging, or a command unit that can die. Transient divergence inside
a tick is impossible to act on before the next snapshot re-converges (deterministic fold
ordered by `ClientIndex`). This is strictly stronger than leader election: a dead
"general" bot changes nothing; the function lives in every head.

- **`CoalitionDirective`** — the fold's output, four fields:
  - `MainTarget` — the enemy the team pushes: the `MainTarget` carried by the most
    allied broadcasts, ties to the target of the highest `DirectorTension` broadcaster,
    then lowest `ClientIndex` publisher. This *is* the merged-army commander: every
    member's `MasterAiBotModule` biases its target choice toward it (bounded like every
    axis factor, so a bot seconds from winning a different fight is not yanked off),
    and every member's `SquadManagerBotModuleCA` treats it as the preferred `SquadCA`
    goal. Squads do not literally merge across players — an ally's actors can never join
    my squad — but same-target + same-window convergence produces the one-army effect
    the maintainer describes, under one shared "commander" that is the fold itself.
  - `Phase` — `BuildUp` / `Push` / `Defend`, derived from `AnyClimax`, total army value
    vs. remembered enemy team value, and `DefendRequests > 0`. `Push` requires a
    `MainTarget`; `Defend` suppresses Push while any ally is at `UrgencyLevel` 2.
  - `RescueAssignments` — per defend-request, the elected responder: the allied bot
    whose broadcast carries the nearest `ArmyCentroid` (new broadcast field, below) to
    `DefendPosition`, skipping bots already committed to a Push they own. Every member
    computes the same election, so exactly one ally rallies — the nearest army rescues,
    by construction. Extends the TC-2b path (`TopDefendRequest` picks the request;
    the directive picks *who* goes). **Review fix 4.3 (2026-10-02):** an elected
    responder leaves the free pool for the rest of the fold — one participant answers
    at most one defend request per directive, so two simultaneous calls cannot claim
    the same army.
  - `Sectors` — the territory partition: a Voronoi assignment of regions (the CN4
    `IBotRegionRoles` zone set, §12.17-era topology) to allied bots by spawn distance —
    each bot owns the zones nearest its base centroid. `ExpansionPlannerBotModule`
    scores own-sector fields first (foreign fields reachable but deprioritised, never
    forbidden — a dead ally's sector re-folds to the survivors), and
    `DefenseCoveragePlanner` counts ally-covered fronts as covered for the team's map
    shape but keeps a handoff margin at sector borders.
- **New broadcast fields** (additive, `TeamBroadcast` ctor defaults keep old call sites):
  `ArmyCentroid` (WPos of own army centre — own-side, honest), `ExpansionAssist` (an
  `ExpansionClaim` the publisher wants escorted — a thin army claiming a contested field
  asks for a bodyguard; the directive routes the nearest free ally the same way rescue
  routes to `DefendPosition`).
- **One owner per decision, unchanged:** `CoalitionDirective` is a *publication* — every
  consumer reads it as demand bias. Squad orders stay in `SquadManagerBotModuleCA`,
  production in `UnitBuilderBotModuleCA`, expansion in `ExpansionPlannerBotModule`,
  defence in `PrepositionDefenceTick`. No new order issuer; the fold is pure and each
  side of a mismatch degrades to today's behaviour (`TeamBroadcast.Empty` → own-only
  plan = current TC-2 semantics).
- **Fog honesty:** the directive folds own-side scalars and ally-published positions only.
  `MainTarget` is a `Player`, not a location — no enemy enumeration crosses the wire.
  `ArmyCentroid`/`ExpansionClaim` are own-side. An ally's visible-enemy knowledge may be
  published only where shared vision already shows it to the team (OpenRA allied vision
  makes that the honest case).
- **Switch groups (shipped NOVA 2026-10-02, default-off):** `BB_tc3_coalition_plan`
  (`MasterAiBotModule.UseCoalitionPlan` — broadcast fields ArmyCentroid/ExpansionAssist/
  SpawnPoint + the `CoalitionFold.Compute` fold + `IBotCoalition` provider +
  `coalition_*` situation fields, publish-only), `BC_tc3_rescue_election`
  (`SquadManagerBotModuleCA.UseCoalitionRescue` — the elected responder answers, the
  unelected stand down; no provider/empty election = today's TopDefendRequest),
  `BD_tc3_sectors` (`ExpansionPlannerBotModule.UseCoalitionSectors` — Voronoi score
  bias, `CoalitionForeignSectorPercent` 35, foreign fields deprioritized never
  forbidden), `BE_tc3_main_target` (`MasterAiBotModule.UseCoalitionTargetBias` +
  `SquadManagerBotModuleCA.UseCoalitionTarget` — both read the directive as demand
  bias only). All inert in 1v1 and on mixed teams without allied providers — same
  degradation contract as TC-2. Seam: `IBotCoalition.cs` (fold + directive +
  `IBotExpansionAssistProvider`); the fold runs inside the master's snapshot and the
  target bias reads the *previous* snapshot's fold (publish→fold→consume ordering —
  the only honest order).
- **Team roles beyond TC-2d:** the role split currently spreads TechRush↔Expansion rests.
  With sectors live, the partition itself carries the spread (sector = expander frontier),
  and `RoleSplitBias` keeps the arsenal spread — the two compose instead of competing.
- **Acceptance criteria (6v6 evaluation, tools/ai):** measured off situation + mission
  records — (a) `team_shared_target` > 1 during at least one push window per team;
  (b) contested expansion claims resolved without two allied refineries within
  `AllyClaimRadiusCells`; (c) `DefendRequests` answered: a friendly squad enters the
  requester's `DefendPosition` region within the escort expiry; (d) climax-window
  convergence: ≥2 allies launch within ±`TeamSyncForceScale` window of the coalition
  `Push`; (e) team territory: union of held `IBotRegionRoles` regions vs. enemy team's —
  the union, not the overlap, is the metric (per-member coverage is already logged).
- **6v6 harness:** `run_ai_match_batch.py --team-size N` generalises the TC-3 duo wiring —
  Team A occupies `Multi0..Multi{N-1}`, Team B `Multi{N}..Multi{2N-1}`, reciprocal
  `Allies:` within teams and `Enemies:` across; needs a map with ≥2N `PlayerReference`s
  and ≥2N mpspawns (dusttown-battle-6v6, moldova-6v6 verified at 12). `run_league.py`
  takes `"team_size": N` the same way.

**Post-merge audit amendments (independent architecture review 2026-10-02, P1 items 4.1-4.4 — all shipped):**

- **Consistency model — stated honestly:** members publish on a *staggered* snapshot cadence
  (phase = `ClientIndex * 37 % SnapshotInterval`), so two members can fold different broadcast
  *generations* inside one interval. The contract is identical-output-for-identical-input plus
  convergence within `BroadcastMaxAgeTicks` — NOT a shared epoch. Every consumer treats the
  directive as a bias, so a transient mixed-generation fold is tolerated, never an order fight.
- **Freshness is central:** `TeamBlackboard.IsLive` — publisher `WinState == Undefined`,
  `SnapshotTick > 0`, age <= `BroadcastMaxAgeTicks` (500) — filters every aggregation in
  `CollectBroadcasts`, so a defeated ally's last broadcast stops electing responders, holding
  sectors and claiming fields. No consumer implements its own freshness.
- **Rescue capacity is explicit:** the elected responder leaves the free pool, so one participant
  answers at most one request per fold; extra requests stand down until the next snapshot refolds.
- **Identity is `ParticipantId`:** `Player.InternalName` carried on the broadcast; rescue
  elections, sector anchors, claim precedence (TC-2e) and the role-split rank (TC-2d)
  all key on it (`#ClientIndex` marks old-version publishers). `ClientIndex` remains
  only where *lobby ordering* is the rule — snapshot stagger phase and MainTarget
  vote tie-breaks.

### 12.19 GC-1 + EX-4 — garrison contest and cover-the-map expansion (EMBER, 2026-10-02)

Two maintainer-observed stack failures, one shared root cause class: behaviour that existed
only as *opportunistic local fallback* was invisible to the strategic layer, so the stack
never *aimed* at it.

**GC-1 — the garrison contest** (`GarrisonContestBotModule`, switch `AB_garrison_contest`,
`genericbot && garrison_contest`).

- *Why the old path lost:* `LoadGarrisonerBotModuleCA` drafts only `IsIdle` units and picks a
  map-random target — on the new stack squads absorb every infantryman first, so neutral
  garrisonables went unclaimed by default, and walkers it did send could be re-drafted
  mid-trip (no lease).
- *Contest pass:* every `ScanInterval` the module scores scouted neutral `Garrisonable`
  buildings (`Shroud.IsExplored` — fog-honest, scouting feeds the frontier), capacity-
  weighted nearest-first from the own-buildings centroid, bounded by `ContestRadiusCells`.
  Walkers are claimed under `BotLeasePurpose.Garrison` **before** orders go out, so a squad
  pass in the same tick cannot draft them (`ReconcileSquadLeases` hands them off cleanly).
  `MinimumSpareInfantry` keeps squad formation fed first; `MaxConcurrentClaims`/
  `MaxLeasedWalkers` bound the commitment. Orders are `AttackMove` to the cell + queued
  `EnterGarrison` — walkers fight through incidental contact instead of dying single-file.
- *Clear pass:* enemy occupation is fog-honestly detectable — `ChangeOwnerOnGarrisoner`
  flips the building's owner, and `BotFogMemory` already prices remembered garrisonables
  by capacity × occupant value (§12.12). The module implements `IBotMissionProvider` and
  publishes `Raid` missions at every enemy-owned or remembered-garrisonable defence cell
  (`raid:garrison_<x>_<y>:r<zone>` — per-building attempt lineage). Squads remain the sole
  execution authority: `BestAffordableMission` takes them like any raid, the trailing
  artillery squad + `IBotSiegeAdvisor` verdicts produce stand-off bombardment — artillery
  clears the garrison *before* infantry are committed, which is exactly the maintainer's
  ask. `RequiredValue` = remembered defence value × `ClearRaidForcePercent` gates the
  suicide case: an intact high-value garrison demands a squad big enough to survive it.
- *Denial* is emergent, not a third system: an enemy column moving at a garrison makes it
  flip enemy-owned → it becomes a published Raid target; once cleared it re-enters the
  contest candidate set. No "deny" type needed.
- *One-owner swap:* when armed, `LoadGarrisonerBotModuleCA@Infantry` is disarmed for
  genericbot (`classicbot || (genericbot && !garrison_contest)`) — the same yield pattern
  as `cn3_bridge_repair` (EngineerBotModule's RepairBridge job). Classic keeps the CA
  loader untouched, so the A/B control is preserved.
- *Terminal cards:* every contest claim ends in a DORMANT card line — `done` (walkers
  inside / building ours), `target_gone` (destroyed), `x_contest_lost` (flipped enemy),
  `lost_units` (walkers died in transit), `superseded` (TC-2e: an outranking ally's claim
  landed on the cell; the walkers are stood down — release + `Stop`, or the queued
  `EnterGarrison` would capture anyway), or `stuck` (`ClaimTimeoutTicks`, default 7500:
  no walker inside and the claim ran past the timeout — a wedged but living walker renews
  its lease forever, so without the timeout the claim never prunes). Raid cards that leave
  the scan without a reservation are shelved `target_gone`; reserved ones stay live under
  the executor. The archive therefore has a close-out for every card this module publishes.
- *Bleeding suppression:* a consecutive `lost_units`/`x_contest_lost`/`stuck` streak on the
  same building imposes an escalating re-contest backoff (`ContestRetryCooldownTicks`,
  default 2500, × streak — a stuck close counts because a wedged path is topological and
  the next walkers would re-wedge). A `done` clears the streak; `superseded` is neutral.
  Smoke evidence: one defended building ate `lost_units` 7× in ~5000 ticks before this gate
  existed — the suicidal re-claim loop the module was built to avoid.

**EX-4 — cover the whole map** (`ExpansionPlannerBotModule.CoverAllFields`, switch
`AC_cover_map_expansion`).

- *The ceiling found:* `RequestMcv`'s `McvTargetCount = 3` counts **yards + MCVs + queued**
  against the appetite — starter yard + one expansion + one in-flight MCV saturates it, so
  the greedy driver stopped requesting after the first field. `ParkTicks` also meant a
  transiently-uncalimable field fell out for 3000 ticks at a time.
- *The fix:* with `CoverAllFields` armed, `targetCount` becomes `max(McvTargetCount,
  active + min(max(freeFarFields, 1), CoverAllFieldsMaxInflight))` — i.e. a bounded
  in-flight pipeline (`CoverAllFieldsMaxInflight = 2` queued MCVs) that runs **whenever a
  reachable far field is still free**, regardless of how many bases already exist.
  `freeFarFields == 0` leaves a one-MCV replacement allowance so a lost yard can be
  refounded. Expansion stops exactly when the maintainer said it should: no unclaimed
  reachable field remains.
- *Difficulty scales pace, not the ceiling:* `BotLimits@<tier>.BuildingIntervalModifier`
  already throttles production speed per difficulty and `McvRequestReserve` paces the cash
  commitment — `CoverAllFields` removes only the count cap, so `easiest` covers the map
  slowly, `cameogod` fast, and both eventually cover it.
- *Composition:* teams get deconfliction for free — `UseTeamExpansionClaims` (TC-2c)
  arbitrates contested fields before `CoverAllFields` refills the pipeline, and the §12.18
  sector fold can bias scoring later without touching this gate.
- *Downstream growth:* `BuildingLimits` carries almost no production caps, so each new
  yard's local base builder fills factories/production/refineries (`RefineriesPerBase`,
  `MaxExtraRefineries` are per-base, not global) — bases grow as they land.

### 12.20b The 2026-10-02 maintainer review round — assault fan, base spacing, harvester caps, army-first (DAWN)

> **Merged 2026-10-02 (maintainer ruling, DESIGN 19.3 one module per decision).** The three DAWN knobs that duplicated
> EMBER's SP-1/HS-1/AF-1 now have ONE owner each; the BaseBuilder fields `MinBuildingGapCells`,
> `MinBuildingGapDefensesCells`, `MinArmyUnitsBeforeBuildings`, `ArmyFirstMinCash` and the groups `AD_army_first` and
> `AE_spread_assault` are gone. **Spacing:** `SpacingAdvisorBotModule` (genericbot only) owns the hard gap (2 / 1, LIVE;
> `findPos` asks `IBotPlacementAdvisor`, no advisor = no gap) and the switched re-ranking. **Harvester:**
> `HarvesterBotModuleCA.MaxHarvestersPerResourceIndice` (4, LIVE; 0 = unlimited) stays the core, the HS-1 cadence is the
> one switch `AF_harvester_spread`. **Army-first:** `ArmyFirstBotModule` owns both the DAWN army-count gate and the AF-1
> cash vote, behind the one switch `AE_army_first`. **classic opts out:** no advisor, `MaxHarvestersPerResourceIndice: 0`
> on `@classic`, no army-first (it behaves as before 10-02). Details below describe the original rules; the owners are above.

Four more maintainer-observed failures, all "the stack does the simple thing wrong"
class. Merged via `devin/dawn/ai-assault` (commit `2dfc153e6`, merge `ef010523b`).

**Assault fan** - merged on 2026-10-02 into the unified deploy state as its *objective shape*: see **§12.7a "Objective
shape (merged DAWN's assault fan)"**. `IssueAssaultFanOrders` and the fan fields are gone; the settings
(`AssaultFan*`, `AssaultEngageRadiusCells`, `AssaultSyncHoldTicks`) and the `FormationMovement` gate are unchanged.

**Building spacing** (`BaseBuilderQueueManagerCA.findPos`, `MinBuildingGapCells` = 2
default-on, `MinBuildingGapDefensesCells` = 1). The golden rule made mechanical: a
candidate cell is rejected if the new footprint comes within `gap` cells (Chebyshev)
of any own building's footprint. The buffer set is built once per `findPos` call from
the per-tick own-buildings cache; `AllowInvalidPlacement` actors exempt (same opt-out
`CanPlaceBuilding` uses); an exhausted annulus still returns null and the queue
retries — the rule never relaxes mid-call. Defenses get the tighter 1-cell gap so
turret/wall lines still form. Result: bases spread, lanes stay open for harvesters
and reinforcing units, and the pathfinder stops degrading under wall-to-wall clutter.

**Harvester field spread** (`HarvesterBotModuleCA`,
`MaxHarvestersPerResourceIndice` = 4 default-on). A resource-map indice at the cap is
*saturated*: `FindAndOrderLowEffectHarvesterOnResourceMap` never sends more harvesters
into it and actively pushes its surplus to the best lacking indice (receiving indice
headroom is clamped to `cap - current` so the rebalance cannot overshoot into a new
pile). `FindNextResource` filters saturated-indice cells when an unsaturated
alternative exists — no harvester ever strands idle.

**Army-first** (`MinArmyUnitsBeforeBuildings`, default 0 = off; `AD_army_first` sets
14 + `ArmyFirstMinCash` 1500). At `TickQueue`'s emission point: while owned
`AttackBase` units are below the threshold and cash exceeds the reserve, non-essential
build requests defer to next tick. Essential = construction yards, refineries, power,
and exactly one in-flight production building (the no-factory deadlock guard).

**Switch map for the round (post-consolidation):** `F_concave`/`AG_assault_fanout` (§12.7a),
`AB_garrison_contest` + `L_cn2_garrison_defense` (contest + man-own), `AC_cover_map_expansion`,
`AD_spaced_base_placement`, `AE_army_first`, `AF_harvester_spread` (the default-on trio's
switched parts), plus `X_cn3_bridge_repair` / `Y_cn3_stealth_squads` from the same day's
merges. (The pre-consolidation `AD_army_first`/`AE_spread_assault` groups were removed from
`increment_switches.yaml` — they wrote fields the merge deleted and would have contaminated
`@classic`'s harvester-cap opt-out via the unscoped `HarvesterBotModuleCA` match.)


### 12.20 SP-1 + AF-1 + HS-1 — spread bases, army-first cash, harvester redistribution (EMBER, 2026-10-02)

**Single owners (2026-10-02 merge with DAWN 12.20b).**
- *Spacing* — `SpacingAdvisorBotModule` loads on `genericbot` alone and always exposes the hard gap
  (`MinBuildingGapCells` 2, `MinBuildingGapDefensesCells` 1; `BuildingGapRule` is the pure check); the SP-1 re-ranking
  runs only when `RerankCandidates` is true (switch `AD_spaced_base_placement`, no longer a granted condition).
- *Harvester* — one mechanism in `HarvesterBotModuleCA`: the per-field cap (`HarvesterFieldCap`, 0 = unlimited) is live,
  `ScanForLowEffectHarvestersInterval` (HS-1 cadence) stays behind `AF_harvester_spread`; `@classic` sets the cap to 0.
- *Army-first* — `ArmyFirstBotModule` = AF-1 cash hysteresis OR DAWN army-count gate (`MinArmyUnitsBeforeBuildings` 0 off by
  default, 14 / `ArmyFirstMinCash` 1500 under `AE_army_first`). `IBotRequestPauseBuildingProduction.PausesBuilding(building,
  essential)`: the base builder classifies essentials (conyard, refinery, power, first factory), the module decides.
  Own units only (fog honest); `ArmyFirstEval` is the pure logic.

Three switch-gated patches for the maintainer's second failure report (the 6v6 review):
buildings packed wall-to-wall into a pathfinder jam, dozens of harvesters queueing on one
field, and building production out-spending the army.

**SP-1 — spaced placement** (`SpacingAdvisorBotModule`, `IBotPlacementAdvisor`, switch
`AD_spaced_base_placement`).

- *The packing found:* `BaseBuilderQueueManagerCA.findPos` returned the **first** valid
  cell in its shuffled annulus — nothing ever preferred an open cell over a cramped one,
  so buildings accreted edge-by-edge into a solid block.
- *The seam:* `IBotPlacementAdvisor.ChooseCell(building, candidates, stillPlaceable)`
  re-ranks a bounded prefix (`PlacementAdvisorCandidates = 24`) of cells that already
  passed `CanPlaceBuilding`/`IsCloseEnoughToBase` — the advisor can never pick a cell the
  caller would have rejected, and with no active advisor the placement scan is
  byte-identical to upstream. Mirrors the existing `IBotDefensePlacementAdvisor` pattern.
- *The advisor:* scores candidates by distance to the nearest own building footprint,
  capped at `DesiredGapCells + 1` (beyond the gap, more distance stops mattering so the
  frontier doesn't drift absurdly), plus a `OutwardLeanPercent` bias away from the base
  centroid. If nothing meets the gap it takes the widest cell left — spacing can never
  deadlock placement.

- *Refinery exemption (SP-1 fix, same day):* the advisor returns `null` for any
  `RefineryInfo` building — refinery placement stays owned by field proximity (EX-2
  claim annulus + resource fallback). The first cut re-ranked refinery candidates too,
  which pushed the refinery to the far edge of the claim annulus; the field then read
  *unserved* (a field counts as served only when a refinery stands within
  `servedRadiusCells` of its centre) and the builder stacked another refinery on the
  same field — "refineries far away, multiple per spreader" in one bug.
- *Resource frontage:* non-refinery candidates whose footprint plus a
  `ResourceFrontageCells` (1) ring touches a valuable resource cell are scored last —
  buildings may not park on the cells a refinery needs or clog the harvester approach
  lane. Valuable set comes from `ResourceMapBotModule` (any resource when absent);
  resource cells are never rejected outright, so a dense field map can't deadlock
  placement either.
- Defence cells keep DEF-3 coverage and are never re-ranked by this advisor.

**AF-1 — army-first cash** (`ArmyFirstBotModule`, `IBotRequestPauseBuildingProduction`,
switch `AE_army_first`).

- *The seam:* `IBotRequestPauseBuildingProduction` is the building-side mirror of the
  existing `IBotRequestPauseUnitProduction` OR-of-vetoes vote (§19.4 R4). The queue
  manager consults providers lazily inside `TickQueue` — any provider returning true
  holds new non-refinery buildings for the tick; refineries stay exempt exactly as in
  the low-cash gate.
- *The voter:* pauses while `CashAndResources < ArmyReserveLowCash` (2500), resumes at
  `ArmyReserveHighCash` (4000) — hysteresis so building production doesn't flicker. The
  vote releases entirely while no unit-producing structure exists: the first
  barracks/war factory (and rebuilding a wiped production chain) can never be starved
  by the guard that exists to feed them.

**HS-1 — harvester spread** (switch `AF_harvester_spread`).

- The CA module already redirects low-effect harvesters from over-served fields to
  starved ones by `ResourceCellsPerHarvester` deficit — the lever is cadence:
  `ScanForLowEffectHarvestersInterval = 433` ran the rebalance roughly once per 17 s,
  far behind harvester production. `HarvesterBotModuleCA` is split into
  `@generic`/`@classic` instances (identical fields today; `BotRoleSets` type-name
  targets match all instances) so the switch retunes genericbot only: interval 433→125.
- Production-side, `ResourceCellsPerHarvester` remains the spread definition; EX-4 keeps
  opening new fields so redistribution always has somewhere to send the surplus.

*Formation/multi-front* (convex spread, multi-angle waves) is **Claude's lane**
(`claude/cv_concave`, §12.7a) — EMBER deliberately does not touch squad formation code;
SP-1/AF-1 only make the base cheaper to path through and the army bigger to form up.

### 12.21 ATK-1 — the assault fan-out (NOVA, 2026-10-02; switch AG_assault_fanout)

Merged into the concave engagement: see **§12.7a "Unified with ATK-1"** — one implementation (CV geometry + state machine, ATK-1 provider seam and single switch).

### 12.22 Scale targets — the growth law (phase ST; DESIGN §19.10; maintainer order 2026-10-01; owner Claude)

**One module, one decision (§19.3):** `ScaleTargetsBotModule` (OpenRA.Mods.Cameo, player trait, `RequiresCondition:
genericbot`) decides HOW BIG the base and army should be. It publishes the answer through `IBotScaleTargets`
(`int Target(string category)`, `int ArmyValueTarget`, plus a snapshot for the situation log). It never builds and
never issues orders: the existing builders read it. A consumer with no provider (classic, or the switch off) keeps its
old limit, so master is unchanged until the A/B.

**Inputs.**
* Tier index from the active `BotLimits@<tier>` (via `BotLimitsResolver`, `Difficulties` list like `DynamicBotInsurance`).
* Game minutes from `WorldTick`.
* The active `personality-*` condition.
* `Seen_k` from `MasterAiBotModule`'s published `BotSituation`: `RegionMemory` per-enemy `ArmyValue/DefenceValue/EconomyValue`,
  `EverSeen`, `LastSeenTick`; `BotFogMemory` remembered actors (`Building` + rules-derived `BotTargetTags`) for counts
  per category; `IBotEnemyCompositionProvider` for army value.
* Own team size = alive players allied with the bot, including itself.

**Formula:** DESIGN §19.10, verbatim, in a pure static `ScaleTargetsEval`. It uses fixed-point integer math (×1000), never
floats, because bot decisions run in lockstep on every client. Unit-tested.

**Categories (first cut)** and their consumers:

| category | Seen_k | consumer (replaces) |
|---|---|---|
| `army` (value) | observed enemy army value | `SquadManagerBotModuleCA` desiredAttackForceValue (`SquadValue` + ramp), `MaxIdleUnits` |
| `harvester` | seen enemy harvesters | `HarvesterBotModuleCA` (`BotLimits.HarvesterLimit`); cap refineries × `HarvestersPerRefineryCap` |
| `refinery` | seen enemy refineries | `BaseBuilderBotModuleCA` (`RefineryLimit`); cap = resource fields in reach |
| `production` (per production type) | seen enemy production buildings | `BaseBuilderQueueManagerCA` (`ProductionTypeLimit`) |
| `conyard` | seen enemy construction yards | `MCVManagerBotModuleCA` (`ConstructionYardLimit`) |
| `tech` | seen enemy tech buildings | `BuildingLimits` entries of tech-tagged buildings |
| `superweapon` | seen enemy superweapons | `BuildingLimits` entries of superweapon-tagged buildings |
| `defence` (value) | remembered enemy army value | base builder defence share if a cap exists today; else telemetry only |
| `aircraft` | seen enemy aircraft (composition) | `UnitBuilderBotModuleCA.MaxAircraft` / `MaxAirSuperiority` |

**Yaml shape.** One instance, every number on the §19.1 line. Fractions are written in one form FieldLoader can read
(fixed-point ints ×100, or a decimal parsed to fixed point); the coder picks one and documents it.
* Per category: `Min/Max/RatioMin/RatioMax/Margin/Growth/Floor`.
* `PersonalityMultipliers`, keyed by personality condition → category → multiplier.
* `ScoutStaleTicks`, `RecomputeTicks`.

The §19.1 table numbers become the Min/Max. The other defaults are starting values for the A/B, not settled numbers:
* `Ratio 0.6 → 1.4`, so Hard (0.96) roughly matches the enemy.
* `Margin` 1.0 for the army, 0.5 for the base.
* `Growth` per hour 1.0 for the army, 0.5 for the base.
* Personality multipliers:
  * Steamroller: army and production 1.25.
  * Expansion: refinery, harvester, conyard and production 1.25.
  * Turtle: defence 1.4.
  * Tech: tech 1.5.
  * Rush: army 0.8.

**Audit.** `audit_ai_personalities.py` gains a check:
* every category writes all fields;
* Min ≤ Max;
* the tech line rounds down to 1 1 1 1 2 2 2 2 3 3;
* the minute-0, nothing-seen targets equal the old §19.1 table.

**Fits with what is already on master (2026-10-02 survey; §19.3, one owner per decision):**
* `ExpansionPlannerBotModule.McvTargetCount` (3) and UT-4's `UseUtilityExpansionAppetite` lean are the construction-yard
  size decision, so they move here. The planner reads `Target("conyard")`. UT-4's TechRush↔Expansion axis becomes the
  axis lean below, so it is no longer a second multiplier.
* **The utility axes refine personality.** When `UseUtilityAxes` is on, `P_k` = the personality table × the axis lean:
  * TurtleRush leans defence vs army;
  * TechRush↔Expansion leans tech vs refinery/harvester/conyard/production;
  * each by `±AxisLeanPct` at the axis ends.
  The discrete personality sets the starting point and the continuous axis tracks how the match develops. With the
  axes off, `P_k` = the table.
* `BotGlobalUnitBudget` is a **physical cap** (FPS across all bots), not a tier cap: the army count target never exceeds
  this bot's share of it.
* `ArmyFirstBotModule` (cash priority), the Director pacing (when to launch) and the personality leads (§12.14, budget
  lean while trailing) decide WHEN and WHERE the money goes, not HOW BIG. They stay separate. The leads read the same
  `Seen_k` numbers, which this module publishes on the situation snapshot so there is one estimate of the enemy.
* `DynamicBotInsurance` sizes its payout from `HarvesterLimit`. With the provider present it reads `Target("harvester")`.

**Switch:** group `ST_scale_targets` (master already uses `G_personality_leads`).

**Implemented (2026-10-02, branch `claude/scale_targets`, dormant until the switch arms it):**
* Files: `OpenRA.Mods.CA/Traits/BotModules/IBotScaleTargets.cs` (interface + `TryTarget/TryArmyValue/TryBuilding` helpers),
  `OpenRA.Mods.Cameo/Traits/BotModules/ScaleTargetsEval.cs` (pure, integer-only), `ScaleTargetsBotModule.cs` (provider,
  `ScaleTargetsSnapshot`), `OpenRA.Mods.Cameo.Test/ScaleTargetsEvalTest.cs`, `ai.yaml` (`ScaleTargetsBotModule` block +
  `GrantConditionOnBotOwner@scaletargets`), `increment_switches.yaml` (`ST_scale_targets`), audit in `audit_ai_personalities.py`
  (`scale_target_failures`). Situation log: optional `own.scale_targets` object (omitted while no provider runs).
* **Fixed point:** thousandths. `Min: 1000` = 1.0, `Max: 3250` = 3.25; `Floor` is in units; `Growth` is per game HOUR in thousandths.
* Spec decisions: (1) `IBotScaleTargets` also has `TryGetBuildingTarget(actorName)` (tech/superweapon category lookup for
  `BuildingLimits`, from `IBotUnitRoles` `tech` + `BotTargetTags.Superweapon`; only entries that exist in BuildingLimits are
  overridden, no new caps on unlisted buildings) and `TryGetArmyValueTarget(int baselineValue, ...)` takes the personality's
  SquadValue, because `own_army` is baseline x line. (2) Army `Min = Max = 1000`: the only difficulty scaling of the army is the
  enemy ratio line; minute 0 keeps today's SquadValue. The Director/team force scale, `ValueOnlyAttackLaunch` and `MaxIdleUnits`
  (scaled by target / SquadValue) apply on top; the random `SquadValueRandomBonus` and the 20-minute bonus ramp are replaced
  by `Growth`. (3) Axis leans are per category yaml fields `TurtleRushLean` / `TechRushExpansionLean` (signed percent at the
  pole): army +25 and defence -25 on Turtle-Rush; tech -25 and refinery/harvester/conyard/production +25 on TechRush-Expansion.
  (4) `production` seen = per enemy the count of its most numerous remembered production building type (the limit is per type),
  summed over enemies. (5) `u` = zone-cell-weighted share of regions with no enemy table entry fresher than `ScoutStaleTicks`
  (a lit empty region counts as fresh only while visible: `RegionMemory` is rebuilt per snapshot), own territory
  (`IBotZoneTopology.IsInTerritory`) excluded. (6) With a provider, `HarvesterBotModuleCA` ignores its fixed `MaxHarvesters` (24)
  as well as `HarvesterLimit`; `aircraft` also scales `MaxAirSuperiority` in the same proportion. (7) Aircraft physical cap =
  `BotGlobalUnitBudget.CurrentShare()` (new, same arithmetic as the pause); no planner exposes resource fields in reach, so
  refineries have no physical cap yet (the base builder's `RefineriesPerBase x yards + MaxExtraRefineries` ceiling still applies).
* Not wired: no `MCVManagerBotModuleCA` exists and nothing reads `BotLimits.ConstructionYardLimit` (the engine's
  `McvExpansionManagerBotModule` has its own `MinimumConstructionYardCount`); the conyard target drives
  `ExpansionPlannerBotModule` only, UT-4's axis lean is skipped when a provider is present. `DynamicBotInsurance` never read
  `HarvesterLimit` (a comment only), so it needs no change. `defence` is telemetry: the base builder has no numeric defence cap.
### 12.23 PP-1 — parallel production width (EMBER, 2026-10-02)

The maintainer's "use all production buildings" report: `UnitBuilderBotModuleCA.BuildUnit`
filled only the FIRST idle queue of a category per call — three war factories still
produced serially through whichever happened to be free, so parallel macro investment
never converted into throughput.

- *The seam:* `IBotProductionWidth.MaxQueuesPerCategory` — settings-only provider (same
  shape as `IBotAssaultFormation`): the unit builder resolves it lazily and fills up to
  N idle queues per call instead of one. No provider (classic mounts none) keeps the
  upstream single-queue fill byte-identical — the shared `UnitBuilderBotModuleCA@generic`
  instance never leaks the width to the A/B control, which a plain field-write switch
  would have done.
- *The provider:* `ParallelProductionBotModule` (`genericbot && parallel_production`,
  switch `AH_parallel_production`, width 4). Orders still come only from the unit
  builder — the provider is pure tunables.
- *Per-queue independence:* each filled queue picks its own unit via the normal
  chooser, so composition/RoleMix logic applies per facility rather than stamping one
  unit across all of them.

### 12.24 FE — field economy and coverage: refineries at the spreader, MCV and crawl apart, every field (maintainer 2026-10-02; owner Claude)

DESIGN §19.1b (field economy bullet). **Observed** by the maintainer: bots stack 2–3 refineries in the home base (more than
the fields there), then cannot build one at the field they crawl to. **Cause, code-verified:**
`BaseBuilderBotModuleCA.ShouldBuildRefinery…` caps refineries at `yards × RefineriesPerBase (2) + MaxExtraRefineries (1)`,
and `OptimalRefineryCount` wants `initial + additional + 2 per extra yard`. Both count construction yards, not fields. The
EX planner's crawl target (best field in reach) and its MCV site (best far field by value × safety / distance) are chosen
independently, so they often point the same way.

**FE-0 telemetry (always on, behaviour-neutral):**
* `cameo-ai-placements.jsonl`, one line per building a bot places: tick, player, actor, cell, reason (`crawl`,
  `refinery_claim`, `base`, `defence`, `other`). For refineries: the nearest anchor, its cell, and the distance in cells.
* An `expansion` object on each situation snapshot:
  * fields known / in reach / served / harvested;
  * anchors (spreaders + spreaderless fields) and refineries;
  * excess refineries (beyond one per anchor);
  * mean and max refinery→anchor distance;
  * construction yards and outposts;
  * the crawl target, the MCV site, and the angle between their bearings from the main base;
  * coverage: the share of map fields within reach of our buildings.
* `tools/ai/expansion_report.py <match dirs>`: per bot and per match, the numbers above over time (first refinery, fields
  harvested at minutes 5/10/20, peak, excess refineries, mean anchor distance, crawl/MCV angle distribution).

**Implemented (FE-0, 2026-10-02, worktree `claude/tel_2026_10_02`, not boot-gated):**
* `OpenRA.Mods.CA/Traits/BotModules/IBotPlacementObserver.cs` is the record-only hook. `BaseBuilderQueueManagerCA` records the queue tick per producer
  (`queuedAt`) and calls the observers when it issues the `PlaceBuilding` order. `reason` comes from the placement path it already took:
  `refinery_claim` (the EX-2 claim returned a cell, flag `refineryClaimed`), `crawl` (`BuildingType.BaseCrawl`), `defence` (`Defense` or an advised
  defence cell), `other` (a plug), else `base`. No decision reads any of it.
* `OpenRA.Mods.Cameo/Traits/AiPlacementLogWriter.cs` (world trait `AiPlacementLogWriter`, `world.yaml`) appends `cameo-ai-placements.jsonl` at game
  over. Line: `schema, kind:"placement", game_uid, record_id, map_uid, seed, player, faction, bot_type, personality, tick, queued_tick,
  placed_tick, actor, cell:"x,y", category, reason` and, for refineries, `anchor_kind` (`spreader` | `field`), `anchor_cell`, `anchor_dist` (cells).
  `category` = `ExpansionMath.Category` over `BotTargetTags` (conyard, refinery, superweapon, power, defence, production) then the `IBotUnitRoles`
  `tech` / `support` roles, else `other`; no actor id is typed.
* `OpenRA.Mods.Cameo/Traits/AiLogExpansion.cs`: `ExpansionTelemetry` (one per `MasterAiBotModule`, shared by the snapshots and the placement log) and the
  pure `ExpansionMath`. It reads the existing `ResourceMapBotModule` (it only remembers each field's first-seen centre) and
  `ExpansionPlannerBotModule.Target` / the new read-only `LastMcvSite`; spreaders = `ActorsWithTrait<ISeedableResource>` (public map data, the one
  enumeration site, manifested in `fog_honesty_manifest.json`). Anchors = spreaders, then fields with no spreader within 12 cells. A refinery serves its
  nearest anchor within 12 cells; excess = refineries beyond one per anchor plus the unassigned ones. In reach = field centre within the planner's
  `ReachCells` of a buildable-area building; served = own refinery within `ClaimRadiusCells`; harvested = own harvester on the field (resource map);
  coverage = (in reach or served) / known. Main base = the first yard seen; outposts = yards more than 20 cells from it; the angle is between the
  bearings (clockwise from north) of the crawl target and the MCV site from the centroid of own buildings within 20 cells of the main yard (-1 = n/a).
* Situation snapshot: top-level `expansion` object (`AiSituationLogWriter.AppendExpansion`): `fields_known, fields_in_reach, fields_served,
  fields_harvested, anchors_spreader, anchors_field, refineries, excess_refineries, unassigned_refineries, anchor_dist_mean, anchor_dist_max, conyards,
  outposts, crawl_target, mcv_site, crawl_mcv_angle, coverage_milli`.
* `tools/ai/expansion_report.py <match dirs> [--json]` (shared readers in `tools/ai/ai_log_common.py`); tests `tools/tests/test_expansion_and_build_order_reports.py`
  and `OpenRA.Mods.Cameo.Test/ExpansionTelemetryTest.cs`.

**FE-1 behaviour (one switch `AJ_field_coverage`, default off; classic unchanged):**
1. **Refinery law:** one refinery per anchor (see DESIGN). A refinery is wanted while an anchor in building reach is
   unserved, and only then. Under this switch it replaces the yard-based cap, `OptimalRefineryCount` and the §19.10
   refinery target. §19.1b binds every field to its refinery, so a tier line never caps it. The physical cap is the
   number of anchors.
2. **Placement:** the refinery claim takes the placeable cell nearest its anchor ("directly next to the spreader").
   Ties go to the cell closest to the field's resource cells.
3. **Directions:** the MCV site is scored by the existing value × safety / distance, × a separation factor. The factor
   falls to `MinSeparationFactor` when the site's bearing from the main base lies within `CrawlSeparationDegrees` of the
   crawl target's bearing or of any yard or in-flight MCV site. The crawl target, in turn, prefers fields not already
   taken by an MCV site.
4. **Spread:** both scores gain `× (1 + SpreadBonus × distance to our nearest building / map size)`, so unexplored
   ground wins ties.
5. **Aggression:** earlier and more MCVs, via the existing EX-4 knobs in the switch values. No new driver.

**Implemented (FE-1, 2026-10-02, switch `AJ_field_coverage`, default off; `ExpansionPlannerBotModule.FieldCoverage`):**
* Anchors = `ISeedableResource` actors (spreaders, public map data) plus first-seen centres of fields with no spreader within
  `SpreaderFieldRadiusCells` (12). `AssignRefineries` pairs each own refinery with at most one anchor within the serve radius
  (`AnchorServeRadiusCells`, 0 = `ClaimRadiusCells`); `WantedAnchor` wants a refinery iff an unserved, unparked anchor lies
  within `ReachCells` of a buildable-area building AND placed + queued refineries < anchors. A claim wanted for
  `AnchorStuckReplans` (12) re-plans with nothing placed or queued parks the anchor for `ParkTicks`.
* The planner publishes it through new default-false members of `IBotExpansionTargetProvider` (`RefineryLawActive`,
  `RefineryAnchorCount`, `UnservedAnchorsInReach`, `RefineryClaimFieldCenter`; `RefineryClaimTarget` becomes the anchor).
  `BaseBuilderBotModuleCA` reads only these: under the law `HasMaxRefineriesFor` ignores the yard cap, `RefineryLimit` and the
  scale-target refinery cap (the first `InititalMinimumRefineryCount` refineries still pass), `HasAdequateRefineryCount` uses the
  initial minimum instead of `OptimalRefineryCount`, and `ExpansionWantsRefinery` no longer needs a crawl target. No provider
  (classic) or switch off = every line is the old one.
* Placement: `findPos(anchorOrder: true)` sorts the claim annulus (radius `ExpansionTargetClaimRadius` around the anchor) by
  distance to the anchor, then to the field's resource centre, takes the first valid cell (the spacing advisor's re-rank is
  skipped; refineries were already exempt from the gap) and does not fall back to a home placement.
* Directions: `McvSite` takes an optional weight = `SeparationFactor` (x `MinSeparationFactor` 0.25 when the bearing from the main
  base is within `CrawlSeparationDegrees` 35 of the crawl target, an own yard or another in-flight MCV site; `WAngle.ArcTan`) x
  `SpreadFactor`. The crawl score takes the spread factor and x `MinSeparationFactor` for a field an in-flight MCV site holds.
* Spread: `1 + SpreadBonus (1.0) x distance to our nearest building / map diagonal`, for both scores.
* Aggression (switch values): `CoverAllFields` true, `CoverAllFieldsMaxInflight` 3 (was 2), `McvRequestReserve` 1000 (was 1500),
  `McvTargetCount` 4 (was 3). Unmeasured guesses: the FE-0 report (`expansion_report.py`) and the increment A/B decide them.
* Tests: `OpenRA.Mods.Cameo.Test/FieldCoverageTest.cs` (anchors, assignment, wanted rule incl. never more than anchors, separation,
  spread). Fog manifest: `ExpansionPlannerBotModule.cs` 4 -> 5 (neutral spreader scan).

### 12.25 BO — the building build-order lab: log, score, tune, personalise, learn, react (maintainer 2026-10-02; owner Claude)

> *Maintainer:* "log the build order, then try to switch it around until the result is optimal … for all the buildings
> for now (units later, after the rebalance) … the timer for each, the interval … always record the success: how fast did
> they win, destroyed-to-lost value … each personality its own little adjustments … keep some random elements … learn
> between matches and during the match … react to what the opponent does and change the build order mid-game."

It implements DESIGN §19.2's routes for buildings. Route 2 "tuned" covers building fractions, limits, delays, intervals
and timers. Route 3 "chosen" is the opening bandit. Everything follows §19.2's rules:
* bounded multipliers on the defaults, with difficulty (§19.1) on top;
* written only by dev/harness training runs, reviewed and committed;
* applied only inside the host's bot, never into rules;
* a match is scored as **win plus margin**.

Units are out of scope until the rebalance.

**BO-1 - Implemented (2026-10-02, branch `claude/bo1_2026_10_02`; switch `AK_build_order_knobs`, default off).**
* `IBotBuildOrderKnobs` (Mods.CA: `Enabled`, `KnobMilli(knob)`, `CategoryOf(actor)`, `OpeningWanted`, `NotifyQueued(actor)`) +
  `BuildOrderKnobsBotModule` (Mods.Cameo, `RequiresCondition: genericbot && build_order_knobs`, `GrantConditionOnBotOwner@buildorderknobs`
  `Bots: fransbot` = inert on master). The shared `BaseBuilderBotModuleCA` reads `BuildOrderKnobs` (first enabled provider, else null:
  classic and switch-off are bit-identical). Pure math, opening, react rules and the learned-file model are in `BuildOrderKnobsEval.cs`
  (unit-tested). All knobs are integer thousandths.
* **Knob -> consumer** (`BaseBuilderQueueManagerCA`; categories are rules-derived by the provider: the base builder's own type lists, then
  `BotTargetTags`, radar/repair traits and the `tech` role - no actor-id list):
  | knob | what it does |
  |---|---|
  | `tempo` | **speed** of the build clock: `BuildingDelays`, `BuildingIntervals` and the general build interval (`StructureProduction*Delay`) are divided by it, so 1150 = 15% faster |
  | `greed` | refinery-category fractions, refinery delay (divided), and `NewProductionCashThreshold` x greed (economy before more factories) |
  | `production` | fractions of barracks / factory / production buildings; `NewProductionCashThreshold` / production |
  | `tech` | fractions and delays (divided) of `tech` and `superweapon` buildings |
  | `defence` | fractions of defence / anti-air buildings |
  | `support` | fractions of radar / repair buildings |
  | `power_margin` | the power surplus target (`MinimumExcessPower` and its bonus, and the per-building power check) |
  | `expansion` | published only (`KnobMilli("expansion")`); the expansion planner reads it later - the base builder does not |
  Fractions compare as `count x 100 x 1000 > fraction x knob x buildings` (no rounding of small fractions).
* **Opening:** yaml `Openings` (`eco`, `barracks_first`, `fast_tech`, `defence_first`) = ordered categories (`production` = any production
  building). The base builder asks `OpeningWanted` AFTER the low-power and refinery priority overrides and before the cash-threshold
  production override, picks the highest-fraction buildable building of that category that respects `BuildingLimits`, the production limit
  and the power check (building power first when it would brown out), and calls `NotifyQueued` for every queued building so any path
  advances the step. Ends: completed, `OpeningMaxTicks`, a step stuck `OpeningStepTimeoutTicks` (skipped), or the react layer.
* **Value** = `Presets[personality]` x learned (`ai/learned/build_order_knobs.yaml`, only with `UseLearnedBuildOrder`; lookup per personality:
  faction, `family_<prefix before the first underscore>`, `any`, then `any__any`; missing = 1000) x jitter (one `LocalRandom` draw per knob,
  +-`JitterPct`, once per match), clamped to [`KnobMin`, `KnobMax`]. Presets: Rush tempo/production up, greed down; Turtle defence up;
  Tech tech up (and its delays shorter); Expansion greed + expansion up; Steamroller production up; Guerrilla production/support light.
  The opening is Thompson-sampled: score = preset weight x Beta(alpha, beta) of the matchup posterior (no posterior = Beta(1, 1)).
* **React** (every `ReactEvalTicks`, from the published `BotSituation`, fog memory only): air = summed seen enemy `AirValue`; rush =
  seen enemy value near our base before `ReactRushWindowTicks` (also invalidates the opening); turtle = seen defence value and share;
  out-earned = the 12.14 economy proxy (harvesters + 2 x refineries) vs ours. Each reaction has a target factor per knob (`ReactTargets`);
  the factor approaches it by `ReactStep` per evaluation, is bounded [`ReactMin`, `ReactMax`], and decays at `ReactDecayPerMinute` once
  no reaction holds.
* **Log:** `own.build_order` in the situation log (personality, faction, enemy faction, opening + end reason, `base_<knob>`/`now_<knob>`,
  reaction flags, events `tick:name+/-`).
* **Tuner:** `tools/ai/tune_build_order.py` (tests `tools/tests/test_tune_build_order.py`): score = win + margin + speed bonus; arms named
  `bo__<personality>__<faction>__base` / `__<knob>__up|dn100` (batch dir name minus `_N`); `--propose` writes the next one-knob pair as
  learned-file copies plus an `increment_switches`-style spec for `apply_increment_switches.py --spec`; `--write` accepts at most one
  arm per (personality, faction) with >= 20 matches per arm and Welch z >= 1.96, step +-10% clamped to a learned multiplier in
  [800, 1250], updates opening posteriors (matchups with >= 20 new matches, cap 200 then halve), each game used once. Not yet exercised:
  no match has run with the switch on; the presets, thresholds and openings are starting values for the A/B.

**BO-0 telemetry (always on, behaviour-neutral):**
* The placement log (§12.24) is the **build order**. Each line also carries the tick the item entered the queue and the
  tick it was placed, plus the building's category (`power`, `refinery`, `production`, `tech`, `defence`, `support`,
  `superweapon`, `conyard`, `other`) from rules-derived tags.
* `tools/ai/build_order_report.py <match dirs>`, per bot and match:
  * the ordered building list with times;
  * time to the first of each category;
  * the outcome: win, game length, `kills_cost` / `deaths_cost` (destroyed-to-lost), and **score = win + margin**.
    margin = (killed − lost) / (killed + lost), plus a speed bonus for a faster win.
  * Grouped by personality and by knob vector (BO-1).

**Implemented (BO-0, 2026-10-02, worktree `claude/tel_2026_10_02`):** the build order is the placement log above. `tools/ai/build_order_report.py <match dirs>
[--json]` prints per bot and match the ordered list (mm:ss, actor, category, reason), the time to the first of each category and the outcome from
`cameo-ai-matches.jsonl`. **Score** = `win + margin + speed`: `win` = 1 for outcome `won` else 0; `margin` = `(killed - lost) / (killed + lost)` over
`stats.kills_cost` / `stats.deaths_cost` (0 when both are 0); `speed` = `0.5 * max(0, (30 - length_min) / 30)` for a win only, `length_min` =
`duration_ticks * timestep / 60000`. Range -1 to 2.5; the constants are `SPEED_WEIGHT` / `SPEED_REF_MIN` in the tool. Aggregates by personality and by
knob vector (`player.knobs` / `knobs` of the match record once BO-1 writes it; `(none)` before).

**BO-1 knobs (switch `AK_build_order_knobs`, default off).** `BuildOrderKnobsBotModule` (genericbot) publishes about
8 bounded multipliers through `IBotBuildOrderKnobs`. The base builder reads them where it reads its raw numbers:
| knob | scales |
|---|---|
| `tempo` | building delays and intervals |
| `greed` | refinery and harvester priority |
| `production` | production-building fractions |
| `tech` | tech delays and fractions |
| `defence` | defence fractions |
| `power_margin` | the power surplus target |
| `expansion` | MCV appetite |
| `support` | radar, repair and other support fractions |

* **Opening** = an ordered list of the first N building categories, from a small named set per personality
  (e.g. `eco`, `barracks_first`, `fast_tech`, `defence_first`).
* **Values** = the personality preset × the learned multiplier (route 2) × a per-match random jitter (±`JitterPct`,
  from the host bot's random), clamped to [`KnobMin`, `KnobMax`]. Every personality feels different, and no two
  matches are identical.
* **Between matches (route 2):** `tools/ai/tune_build_order.py` runs paired mirror experiments. It nudges one knob
  ±δ against the current best, scores win + margin, and accepts significant improvements (coordinate descent). The
  result is written to `mods/cameo/ai/learned/build_order_knobs.yaml` (per personality × own faction, falling back to
  game family, then global).
* **Opening choice (route 3):** Thompson sampling over the openings per (personality, own faction, enemy faction),
  with posteriors in the same learned file.
* **During the match (react):** the knobs shift from what the bot SAW (fog-honest situation snapshot) and decay back
  over time:
  * enemy air seen → defence ↑ (AA share);
  * an early enemy army near the base (rush) → defence and production ↑, greed ↓;
  * enemy defence-heavy (turtle) → tech ↑, defence ↓;
  * enemy out-earning us → greed and expansion ↑.
  * It reuses the personality-lead deficits (§12.14) rather than computing a second enemy estimate.
  * The opening is abandoned when the plan is invalidated (the rush rule fires).
* **One owner per decision (§19.3):**
  * the knobs decide HOW and WHEN the base builder builds (order, timing, weights);
  * §19.10 scale targets decide HOW BIG;
  * the leads (§12.14) decide the BUDGET lean;
  * the knob module reads those, it does not redo them.

### 12.26 TC-2e — capture-claim arbitration (NOVA, 2026-10-02; switch BF_team_capture_claims)

The 6v6 smoke showed every allied bot independently publishing capture missions on the same neutral
targets — 49 contested claims, up to all six teammates committing one engineer to one building. TC-2c's
channel now covers actors: `IBotCaptureClaimSource` (OpenRA.Mods.CA) is implemented by
`EngineerBotModule` (in-flight `capture:` mission targets and the waiting escort plan — never repair or
bridge jobs) and `GarrisonContestBotModule` (live contest claims, one cell per claimed garrisonable).
`BotSituation` unions every enabled source's cell centres into `TeamBroadcast.CaptureClaims`
(publish-always, own-side only — a claim the bot itself already chose, so no enemy enumeration). The
consumer half reads `TeamBlackboard.ClaimsAheadOf(broadcasts, myParticipantKey)` — the position union of
every strictly-lower-`ParticipantKey` publisher — once per module pass behind `UseTeamCaptureClaims`
(default off on both): a new claim on a claimed cell is skipped, and an in-flight claim whose cell lost
arbitration stands down through the stale-claim/release path (`Released`/`superseded`, walkers and
engineers stopped so queued orders cannot complete the claim anyway). Deterministic — ordering is an
ordinal key compare only — and inert in 1v1, where no allied broadcasts exist. Classic is bit-identical:
its stack has no claim-source modules.

**BF-2 prefer-shard** (NOVA, 2026-10-03; same `BF_team_capture_claims` group, field
`PreferShardCaptureTargets` on both modules, default off). The armed 2v2 smoke showed the residual
class arbitration cannot reach: claims publish only on the snapshot cadence, so two allies can commit
the same capturable inside one interval — the blackboard can't arbitrate a claim that isn't published
yet (observed: same-cell commits 5 ticks apart). The fix is zero-communication pre-partitioning —
`TeamBlackboard.CaptureShard(cell, size)` = `(cell.X*31 + cell.Y) % size` and `ClaimRank` = the
caller's position in the ordinal-sorted union of own + allied participant keys — prepended as the
first ordering tier at every capture/contest pick site. The shard is a tier, not a wall: out-of-shard
targets stay eligible once the in-shard list is consumed (TargetFull/Dormant/escort exhaust it), so
coverage can't starve. In-shard ordering is unchanged, and `size <= 1` (1v1 or no live allies) makes
every tier 0 — bit-identical to off. The residual race shrinks to the genuinely unavoidable case (the
own-shard owner picks later), which the participant-key arbitration then resolves.
### 12.27 TC-2f — raid-mission steering: the wave commits anyway (EMBER's dead-end; switch BG_raid_mission_steering)

EMBER's GC-1 evidence exposed a structural dead-end in the assign layer: Raid cards publish but are
never taken. `BestAffordableMission` gates `RequiredValue <= idleForceValue` on the idle pool at
launch time, and a provider's `RequiredValue` is honestly sized for a *dedicated* force (GC-1 prices
remembered defence x `ClearRaidForcePercent`; the master's raids price region army + defence x
`RaidForceRatioPercent`). The launch bar itself is the formation threshold (`SquadValue`/
`MaxIdleUnits`), so a wave that already passed it routinely holds less than the card asks — the card
sits published forever, and the wave goes out cardless as a `secure:` push.

Steering (`SquadManagerBotModuleCAInfo.UseRaidMissionSteering`, default off) is the squad-layer fix.
When the Defend-hold loop resolves `mission == null` — nothing affordable won — a second selector,
`BestRaidForSteering(providers, cap)`, re-picks among `BotMissionType.Raid` cards alone under the
relaxed cap `max(idleForceValue x RaidMissionSteerOvercommitPercent / 100,
RaidMissionSteerMinValue)` (defaults 300/0 = up to 3x overcommit, ratio only). The pick is
deterministic — Priority desc, then RequiredValue asc, then publish order — and needs no exclusion
set: the only filter in the path is Defend-hold exhaustion, which can never match a Raid. A steered
Raid lands above the non-Defend clearing on purpose: it IS a real commit, so it releases the hold
machinery exactly like a won card, then flows through the unchanged Raid path — target resolution
(`FindClosestEnemy`, fogged `FindFrozenEnemyTarget`), `MissionTaken`, provider reservation, attempt
records. If no target resolves it still names `mission.TargetPlayer` in the `secure:` fallback, the
same "card it couldn't afford" semantics as before.

**Why overcommit is not feeding:** the launch gate already fired — the wave commits regardless, so
steering changes WHERE it goes, not WHETHER it goes. No extra units are drawn, no launch happens
earlier, and the card's `RequiredValue` keeps meaning "the dedicated-force price" for reservation
and scoring; the steer only grants the card's target to a wave that was leaving anyway.

**Rejected alternatives:** (a) lowering providers' `RequiredValue` — the number is the provider's
honest dedicated-force sizing and feeds reservations and the dormant shelf, cheapening it would lie;
(b) holding waves until the pool covers the card — re-opens the formation-starvation class and a
high-priced card still never fires; (c) a new assault verb — the grammar has the verb already, the
gap was affordability not vocabulary; (d) relaxing `BestAffordableMission` itself — it is public
static with other callers and its publish-order contract stays bit-identical, so the steer got its
own selector.

### 12.28 TC-3 assist election — the ExpansionAssist dead-end closed (switch BH_tc3_assist_election)

§12.18 published `TeamBroadcast.ExpansionAssist` — a contested expansion field's WPos
that wants a bodyguard — and never folded it: the rescue pass consumed `DefendPosition`
requests but assist requests published into a dead-end (the same class EMBER diagnosed
for Raid cards, §12.27 — a channel that publishes without a consumer). The fold's second
election pass closes it.

**The fold (`CoalitionFold.Compute`).** After the rescue pass, every broadcast carrying
a non-Zero `ExpansionAssist` is a requester (ordered by `ParticipantKey`); each elects
the nearest `ArmyCentroid` to the claim from the **same free pool the rescue pass left**,
with two additions to the rescue rules: (a) a requester cannot elect itself — assist
requesters were never excluded from the pool the way defend requesters are, so the
self-skip is this pass's own rule; (b) the shared-pool `Remove` holds across both
passes — one participant answers at most one request total per fold, whether rescue or
assist. Rescue strictly precedes assist: survival outranks economy, so a contested
claim waits for capacity a defence did not need. `CoalitionDirective` gains
`AssistAssignments` (`CoalitionAssistAssignment` mirrors `CoalitionRescueAssignment`:
RequesterClientIndex / AssistPosition / ResponderClientIndex / RequesterId /
ResponderId); `Empty` and 1v1 degrade to an empty list, and staleness stays outside the
fold — `CollectBroadcasts`' `IsLive` gate is the only freshness rule.

**The consumer (`SquadManagerBotModuleCA.UseCoalitionAssist`, default off).** The
ally-answer channel gains an assist match strictly below the defend match inside the
same protect-squad rally path: own threat and own escort outrank both, a defend answer
(own election pick or the `TopDefendRequest` fallback) claims the rally first, and only
an unanswered channel checks `directive.AssistAssignments` for our participant key. An
elected assist synthesises the same `BotProtectionRequest` the defend path builds —
rally at the claim's cell, `AttackMove`, the rolling `ProtectInterval * 10` hold — so
the escort releases within one interval once the requester's assist broadcast retracts
or goes stale. Election-only by construction: `ExpansionAssist` exists only through the
fold, so there is no pre-fold fallback to preserve. The same `TeamDefendAnswerMinPoolUnits`
floor applies — a thin home pool never escorts.

**Record grammar.** `assist_answer:<requesterParticipantKey>:<rallyCell>` (MissionType
`assist_answer`), written at the confirmed rally exactly like `defend_answer`; the
open-attempt id is tracked in `allyAssistOpen` separately from `allyDefendOpen` so a
defend↔assist switch supersedes the prior record under its own kind instead of
crossing grammars. `DEFEND_KINDS` in `tools/ai/team_coordination_report.py` counts
`assist_answer` with the defend kinds — an escort IS defence-shaped work.

**Rejected alternatives:** (a) routing the escort through a squad channel of its own —
the protect-squad rally/hold/draft machinery is the existing answer channel and a second
one would double the release triggers; (b) a separate responder pool for assist —
rescues and escorts draw on the same armies, so shared capacity is the honest model of
"one army, one job per snapshot"; (c) letting assist outrank a `TopDefendRequest`
fallback — survival outranks economy at both layers, fold and consumer alike.

### 12.29 AS — army staging: front with the defences, split by threatened side (maintainer 2026-10-03; owner Claude)

Binding text: DESIGN 19.12. A new unit used to wait at a random cell within 8 of its factory and a fled or idle squad walked to a
random own building; both are deep in the base, so the rim defences fought alone. Switch `AM_army_staging` (module
`ArmyStagingBotModule`, condition `armystaging`, `Bots:` empty by default = inert on master).

**Seam (who owns what).** `ArmyStagingBotModule` (Cameo) is a pure PLANNER behind `IBotArmyStaging` (OpenRA.Mods.CA, like
`IBotTeamMember`); it issues no order. `SquadManagerBotModuleCA` stays the one owner of the idle pool and of squads: `StageIdlePool`
(each `StagingInterval`) offers the pool (ground combat units, no unit leased by another module) to `AssignIdlePool`, gets a cell per unit
and queues ONE grouped AttackMove per cell, only for units farther than `StagingRadiusCells` that are idle or were sent elsewhere
(order gate and leases of DESIGN 19.6 unchanged). `BaseBuilderBotModuleCA.ChooseRallyLocationNear` uses `PrimaryStagingCell` (biggest
group) for producers whose units can walk there. `StateBaseCA.HomeLocation` (GoToRandomOwnBuilding, flee, idle return) sends a ground
squad to `StagingCellNear` its position; air and naval keep the random building. DF-2 stays one live-attack INPUT: the planner reads
`IBotThreatPredictionProvider` (ETA within `LiveAttackTicks`), and the squad manager no longer drafts the pool for a predicted threat
whose target lies inside the base (`Covers`); a forward threat and escort/ally requests keep their draft. No provider = old code paths.

**Data flow (every `PlanIntervalTicks`).** Own buildings give the centre (mean) and, per 45-degree sector (octant, 0 = east, clockwise,
integer tan 0.414 test), the ring = median radius of own ARMED buildings (else outermost building of the sector, else the same over the
whole base). Staging cell = `ring - StagingInsetCells` along the sector centre line, pulled back until on the map (passability is not
checked yet). Rim weight = learned + prior. Learned: `RespondToAttack` of an enemy ground attacker (aircraft ignored) on an own actor within
`BaseRadiusCells`; weight = attacker cost (damage if unpriced), once per attacker per `EventDedupeTicks`, into the attacker's sector, or into
the INSIDE weight when the attacker already stands within that sector's ring; linear decay with half-life `WeightHalfLifeTicks`. Prior
(`PriorWeightValue` shared): enemy spawn candidates (map `mpspawn` minus every start within `SpawnMatchCells` of an own or ALLIED home,
so a team game faces the enemy team) plus seen enemy defences (`IBotRememberedDefenceProvider`, fog memory); with neither, the map centre.
Active sectors hold >= `ActiveSectorSharePct` of the rim weight, at most `MaxDefenceGroups`, shares by weight. A group below
`MinGroupValue` of idle value merges into the nearest group (the bigger on a tie). Reserve = min(`ReserveMaxPct`, inside share); inside
share >= `CentreSwitchPct` puts the whole army in the centre. Live (an event within `LiveAttackTicks`): one live sector, every group and
the reserve converge on its point; several, each group holds its own sector and the reserve takes the largest live value; an inside
attack sends the reserve to the centre. The last live assignment is held until `ReturnAfterTicks` pass without one. Units are split by
value in ActorID order. All math is integer (`ArmyStagingEval`, pure, tested in `ArmyStagingEvalTest`).

**Constants (Info fields, genericbot).** StagingInsetCells 3, ActiveSectorSharePct 20, MaxDefenceGroups 3, MinGroupValue 1500,
ReserveMaxPct 35, CentreSwitchPct 60, LiveAttackTicks 150, ReturnAfterTicks 375, StagingInterval 50, StagingRadiusCells 5,
WeightHalfLifeTicks 3000, PlanIntervalTicks 25, PriorWeightValue 2000, EventDedupeTicks 150, BaseRadiusCells 30, SpawnMatchCells 8.
Starting values for the increment A/B, not settled numbers.

**What is logged.** Not wired into `BotSituation` (another branch edits it). The plan is on `IBotArmyStaging.Plan` for the situation
snapshot to add: tick, centre, `RimValue`/`PriorValue`/`InsideValue` per sector, `RingRadius`, `LiveValue`/`LiveInsideValue`, groups
(sector, share, cell, target sector), reserve (share, cell, target), `CentreMode`, `Live`.

**A/B metric** (mirror matches, one increment A/B): buildings lost per enemy attack, response time from the first attack event to the
first own unit engaging, and win rate. Compare the arm against the same increment without `AM_army_staging`.

### 12.30 EL — the engagement log: score every fight (maintainer 2026-10-03; owner Claude)

Binding ruling: DESIGN 19.13. EL-0 is record-only: `EngagementLogBotModule` (Player, no `RequiresCondition`, so genericbot, classic
and any bot are measured identically) issues no orders, grants no conditions and no other module reads its state. The writer is
`AiEngagementLogWriter` (World): host only, non-replay, append-only `cameo-ai-engagements.jsonl`, schema `engagement/1`
(fields: `AI_MATCH_LOG.md`).

**Hooks.** Own actor hurt by an enemy: `IBotRespondToAttack`. Own actor hurting an enemy (and enemy kills): `INotifyAppliedDamage`
(the hook `CombatAnalysisBotModule` already uses), and `AttackInfo.Attacker` (revealed on fire, DESIGN 19.5, fair) for the first mobile dealer.
No trait is added to any unit template.

**Segmentation** (`EngagementConstants`, pure `EngagementTracker`, unit-tested): events cluster in space and time. Join an open
engagement within 10 cells of its centroid (a unit's weapon reach plus a squad's spread). Close after 150 quiet ticks (6 s: longer than
a reload, shorter than a regroup), at match end, or when one side has nothing left in radius. Under 300 value traded or fewer than
2 deaths: `skirmish` (written, flagged, excluded by the report). Kind: defend = centroid within 20 cells of an own construction
yard; attack = within 20 cells of a SEEN enemy yard (fog memory); else field.

**Scores** (`EngagementScore`, mirrored in `ai_log_common.engagement_score`, same test vectors in both languages):
trade (zero-sum), vs_prediction (result minus the Lanchester-style `BotCombatPredictor` expectation: play quality, not army size),
objective (buildings 2/3 by HP fraction lost, 1/3 on death), total = 500/250/250 weighting in thousandths. Tactics: approach angle
against the own-base-to-enemy-defence line, `artillery_first`, `suicide_index`.

**Fog split.** `seen` uses visible or frozen enemies only (`CanBeViewedByPlayer`). `truth` is computed by ONE method,
`OmniscientTruthScan`, at engagement start and close only, used by the writer alone and never stored where a decision reads it
(manifest: `fog_honesty_manifest.json`, DESIGN 19.13 "truth block, logging only"). The other enumeration sites list own
actors only, or are fog-filtered.

**Perf budget.** O(own events) per tick. Once per 50 ticks: one pass over own armed actors (ring buffers, 5 samples). Once per 250
ticks: posture line, own-base refresh, one fog-filtered circle scan. Truth scan: twice per engagement. No per-tick world
enumeration. Estimated well under 0.1 ms per tick average.

**What reads this next.** EL-1 (in-match adaptation): a bounded rule reading the running `total_milli` of this match's closed
engagements (seen block only), reset every match, gains are tuned knobs (DESIGN 19.2). The tier-1 fitter: per weapon-delivery x
armour coefficients from `outcome` vs `seen.predicted_*` (truth for calibration only), and the response and suicide priors from
`response` and `tactics`. `tools/ai/engagement_report.py` is the human view of both.
