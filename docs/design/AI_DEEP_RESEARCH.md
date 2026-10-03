# How to build the best RTS bot — research round 2, measured against the Frankenstein

_Written 2026-09-28 by Claude-Local on a maintainer order: "do a deep research on how to make the
best RTS game bot, use what we have written down from our last deep research but expand it with
new facts and new ideas, compare it to our current Frankenstein and how to improve it — make it
more interesting, coherent and heavily modified."_

**Where this sits.** Round 1 lives in [`AI_ARCHITECTURE.md`](AI_ARCHITECTURE.md) §8 (opponent
modelling, bandit strategy selection, learned switching, failure modes) and
[`AI_SYNTHESIS.md`](AI_SYNTHESIS.md) §5 (human-likeness). This round does **not** repeat them; it
adds what round 1 missed — how the strongest bots decide **when to fight**, how they **reason about
space**, how they **micro**, how they are **trained**, and how a bot is made **fun**. The binding
design stays in `AI_ARCHITECTURE.md` (§10.1 one owner per decision, §6.1 learning tiers, §12
combined arms); the merge plan in `AI_SYNTHESIS.md` §7. Where this document proposes a change to
either, it says so and names the section. Every outside claim carries its source; every Cameo
claim was measured on 2026-09-28.

---

## 0. TL;DR — the ten changes that matter most, ranked

| # | Change | Why (evidence) | Where it lands |
|---|---|---|---|
| 1 | **Predict every fight before taking it** (Lanchester model with learned per-type strengths, Versus-aware) and make it the single engage/retreat/commit authority | Our matches are decided by 1–2 fights traded ~2:1 (§1). Bots that decide attack/retreat by predicted outcome beat the AIIDE-2014 field more often (Stanescu et al.) | new **CP** phase; replaces the scalar `AttackRiskMargin`; feeds CA-2 siege |
| 2 | **Fight on a zone graph, not a grid**: terrain regions + chokepoints, zone-to-zone paths precomputed | BWEM/M28 practice; M28 cut path cost >99 % by precomputing zone paths; our `RegionMemory` is a square grid | **ZG** = CN `CNTacticalMap` port |
| 3 | **Influence-map layers** on that graph: enemy threat by weapon range, own strength, interest (value), plus working maps per decision | Mark's modular influence maps (Game AI Pro 2 ch. 30); the siege stand-off ring *is* the threat layer's edge | **IM**, owned with ZG |
| 4 | **One utility strategist** replaces five condition-gated squad managers: bipolar axes scored by response curves in yaml | IAUS (Mark/Lewis): data-driven, explainable, scales to many considerations; matches the maintainer's axis ruling | **UT**; supersedes the shelved threat branch |
| 5 | **Budgeted micro**: focus fire, kite with range advantage, pull damaged units, concave on engage | M28's micro is its main strength (its "Easy" variant is M28 with micro off); Lanchester's square law rewards concentration | **MI**, under the H1 action budget |
| 6 | **Learn the opponent across games** (nearest-neighbour over unit-mix snapshots) and pick openings per opponent | Steamhammer's opponent model; ZZZKBot's bandit (round 1) | **OM**; host-local (§6.1 allows it) |
| 7 | **Train against a league, not one reference bot** | AlphaStar: "playing to win is insufficient"; exploiters expose flaws. We A/B only vs `classic` | **LG** in the harness |
| 8 | **Difficulty = delays and self-preservation, never cheats** | Zero-K's AI rework: Normal/Hard are the top AI with construction delay and less self-preservation | amends DESIGN §19.1 scaling fields |
| 9 | **A Director for fun**: tension-curve pacing of attacks vs humans, honest (no resource rubber-banding) | Left 4 Dead's Director; Hunicke's DDA | **DI** — ruled: no cheats, on in the A/B (§8) |
| 10 | **LLM as an offline analyst, never in the loop** | LLM agents reach roughly average-player level in StarCraft II text play but are slow and non-deterministic; Fransbot's author already tunes from LLM-read logs | **LA** tooling on the match/situation logs (ruled: yes, §8) |

---

## 1. The Frankenstein, measured (the problems this must fix)

From the Nuclear Winter A/B (td_gdi mirror, maximum speed; #617 telemetry):

* **Master `hard` vs omniscient `classic` = 7–6 over 13 matches** — a coin flip.
* **Fights decide matches, economy follows.** In every decided match the winner out-earned the
  loser, but the `stats_timeline` shows the Frankenstein out-earning classic for 21,000 ticks in a
  match it then lost: it traded 1:2 from the first skirmish. Big fights around ticks
  12,000–16,500 are traded ~2:1 one way or the other.
* **Losses by role (round 4):** the largest category is **idle units at home** (38–108 k per
  match, 70–81 % inside the base) — `ProtectOwn` drafted only an empty squad and never
  disbanded it (fix `ReinforceProtection`, A/B round 5). Main-force (`rush`) and `guerrilla`
  losses are next, a third of them far from home.
* **Composition of the stack** (`AI_SYNTHESIS.md` §7): RV + CA merged, Cameo phases 1–6g, one CN
  module, **zero Fransbot modules** in `hard`.

So the bot's problem is not seeing or earning — it is **choosing and executing fights**. Items 1,
3, 5 of §0 attack exactly that; 2 is their foundation; 4 makes the whole thing coherent.

---

## 2. Deciding when to fight

### 2.1 What the strongest bots do

* **Combat simulators.** SparCraft (Churchill) and FAP (FastAPproximation) simulate an engagement
  to answer "should I attack or run away?"; FAP is far simpler — every unit moves toward or
  attacks the closest enemy — and much faster with many units, while SparCraft is better early
  ([satirist: FAP](http://satirist.org/ai/starcraft/blog/archives/334-a-first-look-at-the-FastAPproximation-combat-simulator.html),
  [satirist: comparing simulators](http://satirist.org/ai/starcraft/blog/archives/494-comparing-combat-simulators.html)).
  Steamhammer, one of the best-documented open bots, decides engagements by simulation.
* **Lanchester models with learned strengths.** Stanescu et al. predict battle outcomes with
  Lanchester attrition laws whose per-unit-type strengths are fitted by maximum likelihood from
  recorded battles; faster than simulation, and a bot using it to decide attack/retreat raised
  its win rate against the AIIDE-2014 bots
  ([AIIDE 2013](https://ojs.aaai.org/index.php/AIIDE/article/view/12683),
  [AIIDE 2015](https://cdn.aaai.org/ojs/12780/12780-52-16297-1-2-20201228.pdf),
  [Combat Models for RTS Games](https://arxiv.org/pdf/1605.05305)).
* **Lanchester's square law** is also the reason concentration wins: a force's strength grows with
  the *square* of its size under aimed fire, so two halves arriving apart lose to one whole.

### 2.2 What Cameo has, and the gap

`AttackRiskMargin` (6c) compares **raw cost** of the squad with remembered regional threat. That
ignores who beats whom (a tank army "outvalues" a cheaper rocket-infantry blob it loses to), range,
and concentration. Cameo holds something no StarCraft bot had: **the whole damage model as data**
— every warhead's Versus row (MEAN-100, DESIGN §12.0h), every weapon's DPS and range via the
balance pipeline (`tools/balance/`), and armour classes per actor.

### 2.3 Proposal **CP** — one engagement predictor, one authority

* `BotCombatPredictor` (Cameo, unsynced, pure function + cache): for two unit lists (own, and the
  fog-honest remembered enemy incl. static defences in range) compute effective strength
  `Σ (DPS × Versus-vs-target-armour mix × range factor) × Σ HP`, then a Lanchester-square outcome
  (winner, survivors' value, time). Versus and DPS come from rules at load time — the same
  derivation `AdaptiveCounterProduction` (#605) already does.
* **Learned strengths (self-learning):** the CA-1 ledger logs every engagement (units in,
  survivors out); the offline fitter (CA-1b) fits a per-type correction factor by maximum
  likelihood, exactly Stanescu's method, and commits it with the priors file (§6.1 tier 4).
* **Hysteresis:** engage at predicted advantage ≥ `EngageRatio`, disengage at ≤ `RetreatRatio`
  (`RetreatRatio < EngageRatio`), so squads do not dance at the boundary. Both are per-personality
  inputs moved by the Aggression axis; both scale on the DESIGN §19.1 line.
* **One authority:** CP answers three questions — *launch this attack?* (replaces the 6c scalar),
  *commit past the siege stand-off?* (CA-2 rule 4), *retreat now?* (wraps the fuzzy flee as its
  fallback). Squad states consult it; nothing else decides engagement.
* **⚠ Measured 2026-09-28 — the input is the weak part, not the formula.** Over every A/B
  match with both logs, the enemy army the Frankenstein **remembers** is a small fraction of the
  enemy's **actual** army (classic's own `stats_timeline`): median 0.01 before tick 6000, 0.08 at
  6–12k, 0.13 at 12–18k, 0.15–0.18 after (p25–p75 roughly half to one and a half times that). The
  memory is not forgetting (mobile contacts are kept 30,000 ticks); the bot never *sees* most of
  the army, because its scouts do not reach the enemy base (§9 item 12 of `AI_ARCHITECTURE.md`).
  In the first validation loss the prediction before the decisive fight was 5.6 in our favour
  against an enemy five times larger than remembered. So CP uses two inputs:
  * **local fights** — what is visible around the squad now (reliable);
  * **strategic commits** — `max(remembered enemy, own army)`: assume the enemy is at least as
    strong as we are unless proven otherwise (fog-honest; commit only when composition and
    Versus favour us), later ÷ a **learned visibility factor per game phase** fitted from exactly
    this measurement (CA-1b), and raised by better scouting (CA-6).
* **A/B metric:** trade ratio in the decisive fights (`stats_timeline` deaths/kills deltas around
  the largest loss window) and `rush`/`guerrilla` away-losses, not only win rate.

---

## 3. Reasoning about space

### 3.1 What the strongest bots do

* **Terrain analysis into areas and chokepoints.** BWEM computes areas, chokepoints and bases;
  paths are a precomputed list of chokepoints, ground distances O(1) from flood-filled grids,
  and blocked chokes are accounted for ([BWEM FAQ](https://bwem.sourceforge.net/faq.html),
  [satirist: terrain libraries](http://satirist.org/ai/starcraft/blog/archives/69-pathing-7-terrain-analysis-libraries.html)).
* **Zones around resources.** M28AI (Supreme Commander) divides the map into land zones around
  mass points, keeps a safety flag per zone, sends builders only along safe zone paths, and
  precomputes every zone-to-zone path at game start, cutting that processing time by more than
  99 % ([M28AI devlog](https://forum.faforever.com/topic/5331/m28ai-devlog-v121)).
* **Influence maps.** Mark's modular influence maps combine threat, proximity and interest
  layers through reusable templates and small "working maps" assembled around one agent for one
  decision ([Game AI Pro 2, ch. 30](https://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter30_Modular_Tactical_Influence_Maps.pdf)).
* **Potential fields** for reactive movement: Hagelbäck & Johansson's multi-agent potential-field
  bots won all three ORTS 2008 competitions they entered
  ([AIIDE 2008](https://ojs.aaai.org/index.php/AIIDE/article/view/12365)).

### 3.2 What Cameo has, and the gap

`RegionMemory` is a square grid (`CellSize`), values are overwritten on each sighting, the 6e
router runs A* over that grid for ground only, and CN's `CNTacticalMapBotModule` (3,055 lines:
regions, chokepoints and "doors" from the pathfinder graph, `AI_SYNTHESIS.md` §3c) is not ported.

### 3.3 Proposals **ZG** and **IM**

* **ZG — zone graph.** Port CN's topology as the region set (§2 rule 1 of `AI_SYNTHESIS.md`
  already prefers it); keep the grid as the fallback. Precompute zone-to-zone paths per locomotor
  class at map load (M28), cache per map hash. Chokepoints become first-class: staging points,
  defence placement, siege stand-offs and ambush sites.
* **IM — influence layers on zones** (one publisher: the master's snapshot, §10.3):
  `threat_ground`, `threat_air` (each = Σ remembered weapon DPS × Versus reach, spread over the
  weapon's range), `own_strength`, `interest` (value of economy/production/tech), `staleness`.
  Remembered values decay toward a per-zone **average**, which answers the maintainer's "where
  they usually are" (§12.3 of `AI_ARCHITECTURE.md`).
* Consumers, each already owned: siege stand-off = the zone boundary where `threat_ground` rises
  (CA-2); air strike routes = minimum `threat_air` path (CA-5); raid/guerrilla targets = high
  `interest` ÷ `threat` (§12.9); scouts = high `staleness × interest` (6b); expansion safety
  (M28's engineer rule).
* **Potential fields** for the last metres only (CA-4 formation and MI kiting), because OpenRA
  moves units by orders and its own pathfinder: fields choose *the target cell of the next
  order*, never per-tick steering.

---

## 4. Micro, under a hand budget

### 4.1 Evidence

M28AI's variants make the point: **M28Easy is M28 with micro disabled**
([ModDB listing](https://www.moddb.com/mods/m28ai)); micro is the difference between its tiers.
~~Round 1's AlphaStar lesson still applies: micro must spend a capped, burst-free action budget.~~
**Superseded 2026-09-28 (DESIGN.md §19.1):** Cameo's bots run with no APM cap — a capped budget
measurably weakened them (0–4), and the goal is strength. Micro spends what it needs.

### 4.2 Proposal **MI** (inside the CA squad states, consuming `IBotActionBudget`)

1. **Focus fire:** squads pick targets by `(own damage vs its armour) ÷ its remaining HP`,
   weighted by the target's own threat — kill what dies fastest and hurts most (square law).
2. **Kite** when own range exceeds the target's and own speed allows: attack, step back one
   order, repeat. Only units whose range advantage is ≥ 1 cell.
3. **Pull back damaged units** below an HP fraction to the repair/heal point (CN repair manager,
   Fransbot RETREAT) and return them — cheap preservation.
4. **Concave on engage:** the formation step before contact spreads the frontline across the
   approach instead of a column (CA-4 provides the positions).
5. Budget priority: expensive units first; micro is spent where the value at risk is highest.

Difficulty: micro intensity is a §19.1 field (Easiest none → CameoGod full), which is how M28's
tiers differ.

---

## 5. One coherent brain

### 5.1 Utility AI instead of thresholds and gates

IAUS: every action is scored by axes, each axis = one normalised input + a response curve + four
parameters; the product of the axes is the utility; data-driven and self-contained
([IAUS](https://www.gameai.com/iaus.php), [Utility system](https://en.wikipedia.org/wiki/Utility_system)).

**Proposal UT — the strategist becomes a utility system over the bipolar axes.**

* Today: 5 `SquadManagerBotModuleCA` instances switched by personality conditions, a latched
  Emergency, dozens of hand thresholds. The maintainer's ruling (bipolar axes Turtle↔Rush,
  TechRush↔Expansion, Steamroller↔Guerrilla, decaying to resting values) is exactly a utility
  design: each axis is a curve over inputs (threat, army ratio from **CP**, enemy expansions from
  **IM**, economy state).
* Outputs are **inputs to existing owners** (§10.1): squad size/count, attack interval, defence
  share, expansion appetite, tech priority, `EngageRatio`. **One** blended squad manager reads
  them (CA-3), replacing five instances — the Fransbot author's own stated pain point
  (`AI_FRANSBOT_RESEARCH.md` §3).
* Curves live in yaml (per personality = a starting point on the axes), are logged with their
  inputs on every decision (explainable: "attacked because army ratio 1.8 → curve 0.74"), and are
  the natural thing the offline fitter tunes.
* The shelved continuous-threat branch (lost 1–3) is one input of this, not a mode.

### 5.2 The target layering (amends `AI_SYNTHESIS.md` §2)

| Layer | Owns | Cameo owner today → target |
|---|---|---|
| L0 Sensors | what is seen | fog scans, `ScoutBotModule` (keep) |
| L1 World model | zones, influence layers, ledgers, opponent model | `BotSituation` + `RegionMemory` → **ZG + IM + CA-1 + OM** in the one snapshot |
| L2 Strategist | posture, main target, tension | master + 5 personalities → **UT** (+ **DI**) |
| L3 Operations | missions over zones (recon/raid/secure/defend/siege) | 7a missions → keep; Fransbot SECURE/CLEAR validation |
| L4 Tactics | engage/commit/retreat, siege, formation | fuzzy flee + 6c + 6f → **CP** + CA-2 + CA-4 |
| L5 Micro | focus, kite, pull back | none → **MI** |
| L6 Execution | pacing, attention, order drain | `HumanPace` + attention (keep) |
| Learning | in-match weights; offline priors; league; opponent profiles | logs + harness → CA-1b + **LG** + **OM** |

---

## 6. Learning that actually improves the bot

### 6.1 Across games, per opponent — **OM**

Steamhammer snapshots enemy unit mixes every 30 s, finds the nearest past game against the same
opponent by summed mix differences, and uses it to predict the enemy's plan and pick the opening;
it also distinguishes opponents that repeat a build from those that randomise
([satirist: Steamhammer's opponent model](http://satirist.org/ai/starcraft/blog/archives/362-Steamhammers-opponent-model.html),
Synnaeve & Bessière in round 1). **Cameo (ruling §8: one profile per enemy faction):** the situation log already takes fog-honest
enemy snapshots; **OM** keeps a profile per enemy faction — the last N games' snapshot
sequences, openings seen, which posture and which own roles traded well — as committed offline
priors plus a host-local layer that grows with every game played. At match start the
bot picks its starting axes by a bandit over that profile (round 1 §8.2). Allowed by §6.1: it
only steers unsynced bot reasoning on the host.

### 6.2 Train against a league — **LG**

AlphaStar trained main agents against a league of past selves plus **exploiters** whose only job
is to find the main agent's flaws: "playing to win is insufficient"
([DeepMind](https://deepmind.google/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/),
[Nature 2019](https://www.nature.com/articles/s41586-019-1724-z)). **Cameo:** every candidate
already plays `classic`; LG adds (a) the last three masters (no regression), (b) **scripted
exploiters** — pure rush, pure turtle, air-only, artillery-only, harass-only personalities pinned
to one pole — and (c) other maps and factions. A candidate lands on a *league score*, not on one
pairing. This is also the data volume the offline fitters need.

### 6.3 Deep RL: still not now

RAISocketAI was the first deep-RL agent to win the microRTS competition (after five scripted
winners), but needed iterative fine-tuning and **per-map transfer learning**
([arXiv:2402.08112](https://arxiv.org/abs/2402.08112)) — on a toy RTS. With 25 factions and a
moving balance, round 1's Stage E deferral stands.

> **Amended 2026-10-03 (DESIGN §19.13, research round 3: `AI_LEARNING_RESEARCH_2026-10-03.md`).** The verdict still
> holds for a whole-game policy, which is two to three orders of magnitude beyond one PC. It no longer holds for one
> narrow decision. A small engagement network (~5k weights, the Supreme Commander 2 platoon pattern) choosing assault /
> flank / siege-first / retreat per fight is adopted as tier 5, once ~50k engagements are logged.

### 6.4 LLMs: offline analyst — **LA**

TextStarCraft II agents with chain-of-summarization beat the level-5 built-in AI; human experts
put them near an average player ([NeurIPS 2024](https://arxiv.org/abs/2312.11865)). Too slow and
non-deterministic for a host-only bot loop, and a network call is forbidden by §6.1. But as an
**offline tool** over our JSONL logs (summarise each decisive fight, propose which curve or
threshold to move, human-reviewed, A/B-verified) it is cheap and the Fransbot author already
works this way. It never ships in the game.

---

## 7. Making it interesting, not only strong

* **Difficulty honestly (amend DESIGN §19.1):** Zero-K's rework made Normal and Hard "effectively
  Brutal but with a delay on all their construction and less self preservation for their units"
  ([ModDB news](https://www.moddb.com/games/zero-k/news/zero-k-latest-updates-ai-rework)). Cameo's
  continuous scale already delays attacks and paces orders; add **self-preservation** (CP
  `RetreatRatio`, MI pull-back) and **micro intensity** as scaled fields, and keep resource
  bonuses (`BotInsurance`) as the *only* cheat, clearly labelled.
* **A Director (DI):** Left 4 Dead's Director follows a tension curve and changes enemy numbers,
  placement and pacing from player stress ([L4D wiki](https://left4dead.fandom.com/wiki/The_Director));
  Hunicke's Hamlet adjusts when failure is predicted
  ([AAAI 2004 workshop](https://www.researchgate.net/publication/228889029_AI_for_dynamic_difficulty_adjustment_in_games)).
  For Cameo vs humans: build-up → pressure → climax → relief waves, modulating **attack timing
  and aggression only** — never income or unit stats. **On in the A/B** (ruling, §8).
* **Readable personalities:** each named personality gets a signature the player can learn and
  counter (the steamroller's one big push, the guerrilla's multi-front raids, the turtle's
  artillery creep) plus telegraphs before big attacks (a staging army that is visible), and
  optional chat lines at posture changes. Human-likeness (round 1 §5) plus readability is what
  makes losing to a bot feel fair.
* **Faction doctrine:** the arsenal tracker's roles let each faction's bot play to its identity
  (e.g. Nod stealth raids, Soviet armour pushes) by biasing its resting axes per faction in yaml —
  25 factions, 25 flavours, zero C#.

---

## 8. Maintainer rulings (2026-09-28) — binding in DESIGN.md §19.2

1. **DI Director: yes, no cheats, and part of the A/B.** Pacing and aggression only; it is **on**
   in the Nuclear Winter A/B (this replaces §7's "off in the A/B" proposal).
2. **OM: one profile per enemy faction**, remembering what was effective against it and
   countering it more automatically as games accumulate — committed offline priors, frozen in
   release and trained on dev builds only (amended 2026-09-29, DESIGN §19.2). No per-human-player data.
3. **LA offline LLM analyst: yes**, in `tools/` only, human-reviewed, A/B-verified.

---

## 9. Roadmap — new phases slotted into `AI_ARCHITECTURE.md` §12.10

Every phase: telemetry first, behaviour behind a yaml switch, A/B vs current master on A Nuclear
Winter (≥ 8 matches), and — once **LG** exists — a league score.

| Phase | What | Owner (proposed) | Depends on |
|---|---|---|---|
| **CP** | combat predictor + engage/retreat hysteresis; replaces the 6c scalar | Claude (with CA-1) | CA-1 roles |
| **ZG** | CN topology port, precomputed zone paths | NOVA (claim first) | — |
| **IM** | influence layers on zones, decay to averages | NOVA with ZG | ZG, CA-1 |
| **UT** | utility strategist over bipolar axes; one blended squad manager | NOVA (absorbs CA-3) | CP, IM |
| **MI** | budgeted micro: focus, kite, pull back, concave | EMBER (with CA-5) | CP, CA-4 |
| **OM** | per-enemy-faction profiles + bandit start | Claude (with CA-1b) | logs |
| **LG** | league harness: past masters + exploiter personalities + maps/factions | EMBER | — |
| **DI** | Director (pacing only, no cheats, on in the A/B) | NOVA (with UT) | UT |
| **LA** | offline analyst loop (§12) | Claude | logs |

Order of value: **CP → ZG/IM → MI → UT → LG/OM**, interleaved with CA-1…CA-6. CP comes first
because it attacks the measured failure (fights traded 2:1) with data Cameo already has.

---

## 10. Anti-patterns (things the research says not to do)

* **Two engagement authorities.** CP owns engage/retreat; the 6c gate and fuzzy flee become its
  inputs/fallback, never parallel voices (§10.1).
* **Tuning against one opponent.** Every A/B so far is vs `classic`; that overfits (§6.2).
* ~~**Micro without a budget.**~~ Superseded: no APM cap (DESIGN.md §19.1, 2026-09-28).
* **Per-tick field steering or pathfinding in bot code.** Precompute (M28), issue orders.
* **Neural nets or network calls in the game loop** (§6.1, §6.3–6.4).
* **Difficulty by stats.** Scale delays, self-preservation and micro; keep insurance as the one
  labelled cheat.

---

## 11. Team games: the Team Commander (maintainer, 2026-09-28)

> "Director sounds useful for team games where the bots can give attack and defend and expand
> orders to each other."

The Director (§7, DI) paces pressure against humans. Its team sibling, **TC — Team Commander**,
coordinates allied bots. It is cheap in OpenRA because **every bot of a match runs on the host**
(`AI_ARCHITECTURE.md` §1.1), so allied bots can share an unsynced team blackboard without any
network or sync work, and allies already share vision. Nothing here is a cheat: it is what a
human team does on voice chat.

* **Shared plan:** one team main target and a **synchronised attack time** — waves from two
  bots arrive together (Lanchester square law, §2.1) instead of one after another.
* **Defend requests:** a bot under attack posts a request; the ally whose army is nearest and
  not committed answers with a squad (CP decides whether the answer can win).
* **Expansion claims:** a bot reserves an expansion zone before its MCV moves, so allies never
  race each other for the same site; claims time out.
* **Role split:** allies bias their resting axes apart (one air/tech, one ground/rush) so the team
  covers the arsenal instead of mirroring.
* **Human allies:** allied beacons (phase 8, approved) become defend/attack requests on the
  same blackboard.
* **One owner:** a world-level `BotTeamCommander` (host-only, unsynced) owns the team plan; each
  bot's master reads it as an input (§10.1). Absent in 1v1: nothing changes.
* **A/B:** a 2v2 variant of the harness (Frankenstein pair vs `classic` pair); owner NOVA with DI.

---

## 12. The analyst without a local LLM: an agent

Ruling LA (DESIGN §19.2) allows an offline analyst; the maintainer has no local LLM yet, so the
analyst is **an agent**: Devin was proposed, but Devin Cloud is out of tokens until next week, so
**Claude** runs the loop now (`../Cameo-mod-fleet/ORDERS_2026-09-28_claude_devin_cloud_reassigned.md`). (Measured on the maintainer's machine: RTX 4060 with 8 GB VRAM —
Windows' WMI reports "4095 MB", a known 32-bit cap — 32 GB RAM, Ryzen 7 5700X: enough for a
quantised 7–8B model later, e.g. through Ollama or LM Studio, if ever wanted.)

The loop, every step reviewable:

1. **Run** a league batch (`tools/ai/run_ai_match_batch.py`, §6.2).
2. **Condense:** `python tools/ai/fight_report.py <batch dirs> --bot hard` — per match the
   decisive fight (largest net trade swing), what the bot believed before/after, and which roles
   took the losses. This is the analyst's input; it replaces reading raw JSONL.
3. **Hypothesise:** the analyst writes `FINDINGS_<date>_<agent>.md` in the fleet folder: the top 3
   recurring causes with the report lines that show them, and one candidate change each.
4. **Test:** each candidate on its own branch, behind a yaml switch, A/B vs master.
5. **Review:** a human (maintainer or Claude) merges only what won.

This is how today's two defects were found (idle units at home; `ProtectOwn` never grows), by
hand; the report makes the same read take seconds.

---

## 13. Beating the best human players — what else

Beyond §0's ten, the literature and our measurements point to what separates a bot that beats a
strong human from one that only beats bots. Each is **fair** (no cheats) and each is a candidate
for the league A/B.

1. **Superhuman discipline, not superhuman stats.** Humans float cash, idle factories, forget
   power and harvesters in fights; a bot must never. Add telemetry for idle-production ticks,
   banked cash and brown-out time, and drive them to zero at the top tiers.
2. **Pressure on several fronts at once.** A human's attention is one screen; a bot's is its
   action budget. At the top tiers run main army + harass + expansion snipe simultaneously (RV
   guerrilla, CA harasser, 6c/CP decide each), inside the H1 budget.
3. **Base trade and counter-attack.** When influence maps (IM) show the human army committed
   elsewhere, hit their base or expansion instead of racing home — or race home only when CP
   says the defence wins.
4. **Refuse the bait.** Humans pull bots into defences and chokes. CP + siege stand-off (CA-2)
   + remembered ambush zones (IM decay keeps "they killed us here") make the bot decline.
5. **Be unpredictable on purpose.** Draw openings, timings and attack paths from a distribution
   (round 1 §8.2, Tavares' safe exploitation); a human who learns the bot's one plan beats it.
6. **Hit windows, not timers.** Attack at our own power spikes (a tech/upgrade just completed,
   CA-1 ledger) and at the enemy's weak moments (just lost a fight, just expanded, superweapon on
   cooldown — support-power timers are public in OpenRA).
7. **Superweapons both ways.** Fire at the densest valuable cluster (army or production);
   disperse own army and harvesters when an enemy superweapon is due.
8. **Keep veterans alive.** MI pull-back weights veterancy; a promoted unit is worth more than
   its cost.
9. **Map control and vision.** Hold chokes and tech/oil structures with cheap watchers
   (ScoutBotModule posts), kill enemy scouts, deny information.
10. **Learn from our best humans.** Record human-vs-bot games in the same logs (the match writer
    logs bots today; add a record-only human row). The per-faction profile (OM) then learns from
    the strongest opponents too — still keyed by faction, no personal data (ruling §8).
11. **Measure it: ratings.** Keep an Elo/TrueSkill rating per bot version across the league and
    human games, so "beats our best players" is a number that moves, not a feeling.
12. **Robustness watchdogs.** Log and self-correct stuck units, an army idle for N ticks, a
    squad without a reachable target — the silent failures humans exploit.

Owners are assigned as each item becomes a phase; items 1, 10, 11 are telemetry and harness work
(Claude / EMBER), 2–4 are CP/IM consumers, 5–9 belong to UT, MI and CA-5.

### 13.1 Measured today: the base-defence fix alone is not enough

Round 5 (A Nuclear Winter, `ReinforceProtection` vs master, 4+4 matches, same session): the
candidate went **1–3**, master **2–2**. Idle-at-home losses fell (3–16 k vs 15–28 k) but
protection losses rose by the same amount (20–72 k vs 4–19 k), almost all **inside** the base:
the whole defence now fights, and still loses, because classic arrives with 43–96 k of army
against 3–10 k (`fight_report`). The fix stays shelved and is re-tested together with **CP**
(hold under own defences until the predicted trade favours us). It confirms §1: the lever is
fight selection and army size at the decisive moment, not who is drafted.

---

## 14. Predictive defence, the lure, and punishing an army that left home — phase **DF**

**Maintainer order (2026-09-28):** *"defense squads that react to any predicted incoming attack by
plotting enemy movements and extrapolation to predict where they might attack, so the defense
squad is already there. It should lure the enemies into the main defenses: counter-attack, then
quickly retreat into the defenses where they are safe. Guerrilla, recon and spec-ops squads can
be changed into defense squads if the threat level is high enough. But if the incoming attack is
too far away for those fast squads to react, they should pressure or sneak into the enemy base,
since the enemy army will be out — and this must be punished by the fast squads and maybe even
the main army."*

### 14.1 What exists and what is new

Today the base reacts *after* a hit: `ProtectOwn` fires when a building or harvester takes damage
(`ReinforceProtection`, shelved: it made the defence fight, but at the wrong place and time). Fog
memory keeps each remembered enemy's last cell and tick, not its movement. So DF adds:

1. **Group tracking (world model, record-only first).** Cluster visible enemy combat units by
   proximity each snapshot; per group keep centroid, value, and a velocity from its last two
   sightings (fog-honest: only while seen). Log groups in the situation record.
2. **Threat prediction.** Extrapolate each group's heading; the predicted target is the own asset
   cluster (base, expansion, harvesters, defences) in a cone around the heading with the highest
   value ÷ distance; ETA = path distance ÷ the group's slowest speed. Output per threat:
   `(target, ETA, predicted strength)` — the input NOVA's influence maps (IM) will later refine.
3. **Defence squad with a lure.** The Protection squad (and any converted fast squad) moves to a
   rally point *under own defences on the approach* before the ETA; when the enemy closes, it pokes
   (attacks the front), then falls back into defence range. Every decision is the combat predictor
   with **own defences counted on our side** — fight under the towers, never outside them unless CP
   says the open fight is won.
4. **Conversion by threat and reach.** When the continuous threat level (AI_ARCHITECTURE §4.6) is
   high: fast squads whose travel time ≤ ETA convert to defence for the duration; those that cannot
   make it go on offence instead.
5. **Punish.** With the tracked enemy army known to be far from its base, the enemy-base estimate
   *excludes* that army: raids/sneak attacks target the base (production, harvesters, tech); the
   main army joins when CP (own main army vs remembered base defences + what is left) predicts a
   win **and** our own base holds without it (CP of the defence under towers vs the incoming group).
   This is item 3 of §13 (base trade) made concrete.

### 14.2 Order and gates
Record-only group tracking + prediction first (validated against where attacks actually land,
`fight_report` decisive windows), then the defence rally/lure, then conversion + punish — each
behind a yaml switch, each A/B'd on A Nuclear Winter against master. Owner: **Claude** (it sits on
CP and the threat level); NOVA's IM/ZG layers improve the target prediction when they land.

