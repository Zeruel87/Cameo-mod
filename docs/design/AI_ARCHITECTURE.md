# Cameo AI architecture — bot modules, personalities, master module, learning

_Written 2026-08-31. Owner document for everything about how Cameo's bots decide what to do.
[`DESIGN.md`](../DESIGN.md) §19 and §20 keep the binding rules for the personality and composition
systems that already ship; this file is the forward design and the research behind it.
Task queue: [`ROADMAP.md`](ROADMAP.md) section "AI ARCHITECTURE"._

**This document is a design, not a shipped system.** Section 1 is verified fact with file:line
evidence. Sections 2–7 are proposals. Section 8 is outside research. Section 9 records what is
still undecided. Nothing below section 1 has been observed running.

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

Today a personality is a condition that selects one of five `SquadManagerBotModuleCA` instances
(§19). The manager keeps that mechanism and adds the missing personality the user named:
**Guerrilla** — many small simultaneous raids against expansions, rather than one blob. Cameo's
squad manager already has the knobs (`JoinGuerrilla`, `MaxGuerrillaSize`, `GuerrillaTypes`), and
note `JoinGuerrilla` is inverted: a *higher* value means *less* harassment.

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
deterministic, and makes each switch a replay-visible event. `GrantRandomCondition@personality`
becomes the *initial* draw only, which also preserves current behaviour if the manager is absent
or disabled.

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
| We lost production structures | Turtle | rebuild before committing |
| Two enemies focusing one ally | (keep) | target the aggressor, not the score leader |
| No contact / nothing known | Expansion | scout; take map while blind |

Note the "(keep)" rows: **most enemy facts should change composition and priorities, not
personality.** Personality is the coarse posture; a five-state machine cannot express "he went
air" and should not try. This split is deliberate and is the main structural opinion in this
document.

### 4.5 Switching policy

Copy CN's shape, with numbers as tunable fields, not constants: slow re-evaluation cadence
(~1500 ticks); a fast emergency check (~25 ticks) that can force Turtle on a danger spike; a
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
(`ScriptContext.cs:146`, `TraitDictionary.cs:62`), so JSONL match logs need no new IO plumbing.

### 6.2 Log schema (one JSON object per line)

Three record types, deliberately flat so aggregation is trivial:

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

### 6.3 Learning, in the order it should be built

**Phase 1 — record only.** Emit the logs, change no behaviour. Verify the schema survives real
matches and that the numbers are attributable. This is the proof of concept the user asked for,
and it is the whole first deliverable.

**Phase 2 — offline aggregation.** A Python tool under `tools/` producing, per
(faction × enemy faction × personality) and (composition × enemy faction), the episode counts,
mean value-trade ratio and win contribution. This is where "which composition does badly" gets
answered, with a minimum sample threshold before any number is believed.

**Phase 3 — offline weight fitting, still no online learning.** Fit the §4 scores' weights, or
simply a prior over personality choice per matchup, and ship the result as a committed data file
reviewed like any balance change. Bandit-style selection (UCB1/Thompson over personalities per
matchup) is the right first algorithm — it is what the strongest scripted StarCraft bots use
(§8.2), it needs no neural network, and it is auditable.

**Phase 4 — AI-vs-AI batch harness.** Headless repeated matches across matchups, feeding phases
2–3. This is what makes the data volume possible; it should be a script and a map rotation, not
engine work.

**Phase 5 — anything neural.** Explicitly deferred until factions and balance are finished, per
the user's own sequencing. Training against a moving balance target fits noise.

An honest note on ordering: phases 1–2 are worth doing now because the logs also make the *current*
bots debuggable. Phases 3–4 only pay off once the game is balanced, for the same reason phase 5 is
deferred.

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
a handful of counters and no neural network — which is why §6.3 phase 3 is a bandit.

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
This is close to the user's target and is the reason §6.3 phase 5 is not dismissed. But it is also
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
