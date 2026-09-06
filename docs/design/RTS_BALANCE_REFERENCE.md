# RTS and multiplayer balance — a reference, not a law

⚠ **NON-BINDING.** Nothing here is a Cameo ruling. Where any of it meets
[`DESIGN.md`](../DESIGN.md), **DESIGN.md wins**; where it meets an owning document —
[`FORMULA_V2.md`](FORMULA_V2.md), [`ARMOR_SYSTEM.md`](ARMOR_SYSTEM.md),
[`FACTION_IDENTITY.md`](FACTION_IDENTITY.md),
[`BALANCE_SYNTHESIS.md`](BALANCE_SYNTHESIS.md) — that document wins.

⚠ **The sourcing is unverified from this repository.** This material arrived through an
outside review round that cited industry balance posts and academic papers. Those
citations could not be checked against anything in the tree, so they are not reproduced
as if they had been. What is kept is the *substance* — the questions worth asking and
the shapes worth measuring — because the substance stands on its own reasoning.

Read this when designing a metric, not when settling a number.

---

## Why keep it at all

The measured half of Cameo's balance programme is strong: Formula V2, class anchors, K,
effective damage, the armor ladders, MEAN-100. What it answers is *"is this unit priced
consistently with its stats?"*

That is necessary and not sufficient. A unit can be priced perfectly and still be
miserable to play against, and a faction can pass every numeric check and still have no
answer to a timing. The dimensions below are the ones a stat-consistency model cannot
see. None of them is scheduled work — the board's order stands, weapon structure before
pricing — but a metric designed without them tends to need rebuilding later.

---

## 1. What "balanced" is not

**Not equal.** The target is that many options stay viable at high skill with no single
strategy crowding out the rest. Cameo is a deliberately asymmetric crossover; flattening
factions toward identical mechanics would destroy the thing it exists for. A common
*measurement* framework, never a common mechanical identity.

**Not a 50% win rate.** A rate near the middle is weak evidence of health and a rate far
from it is a reason to look, not a verdict. Roughly 45–55% is commonly treated as "no
clear crisis" and something past 60/40 as "investigate" — but only once the rate is
conditioned (below), and never as a law to tune toward.

**Not the absence of strong units.** A strong unit with a legible, affordable, timely
answer is healthy. A fairly-priced unit whose range, mobility or timing denies any
response is not.

---

## 2. Counterplay, as something you can measure

[`BALANCE_SYNTHESIS.md`](BALANCE_SYNTHESIS.md) §10 already carries Cameo's
rock-paper-scissors counter mandate. What that section does not give is a way to *check*
a mechanic against it. The taxonomy below is the missing half.

For any offensive mechanic, ask which of these responses actually exist:

| axis | the question |
|---|---|
| hard counter | is there a unit whose job is beating this? |
| soft counter | does something trade acceptably without being the answer? |
| range | can it be outranged? |
| armor | does any armor or plating meaningfully blunt it? |
| mobility | can the target leave? |
| detection | does seeing it coming change the outcome? |
| terrain | does the map offer a position that defeats it? |
| timing | can it be pre-empted, or punished on cooldown? |
| economic | can it be answered by out-expanding rather than out-fighting? |
| micro | does skilled control change the result? |
| tech | is the answer gated behind a tier the threat arrives before? |

Three failure shapes are worth naming, because they need different fixes:

* **Counterless** — no axis has an answer. Usually a design problem, not a number.
* **Over-countered** — several cheap answers exist, so the unit is never built. Also a
  design problem, and the opposite one.
* **Too late to counter** — an answer exists but arrives after the threat has decided
  the game. This is the one a pricing model is *least* able to see, because on paper
  the counter exists.

---

## 3. Time-to-kill, decomposed

A single TTK number hides the thing that matters. Worth separating:

* **Burst TTK** — how fast can this be deleted in one commitment?
* **Sustained TTK** — over a full engagement, including reload downtime.
* **Setup TTK** — including deploy, spin-up, targeting delay, first-shot delay.
* **Squad TTK** — what a realistic group does, not a duel.

And the inputs that move them: first-shot delay, burst length, reload, accuracy, target
availability, overkill, armor interaction. Overkill in particular is invisible to DPS
and decides whether a high-damage weapon is efficient against small targets.

Survivability deserves the same treatment. HP is not durability: **effective survival
time** against representative threats folds in armor, shields, Integrity, healing,
repair, movement, range, stealth and retreat. Cameo has several health-like layers, so
the gap between "has the most HP" and "survives longest" is wider here than in most RTS.

⚠ Armor is non-linear. Ladder rungs and the plating layer create cliffs, and averaging
(not multiplication) is what the current system does — see DESIGN §12.0e. A model that
assumes smooth scaling will misprice exactly at the interesting boundaries.

---

## 4. Economy, which is barely modelled here

This is the largest genuine gap. Cameo spans source games with materially different
economic designs, so a single hard-coded model would be wrong for most factions. What a
future economy layer wants is a *profile* rather than an assumption:

```
EconomyProfile:
    resource_type          gather_rate         gather_method
    delivery_method        travel_dependency   storage_dependency
    worker_count           worker_cost         worker_vulnerability
    expansion_dependency   harassment_exposure automation_level
```

The archetypes worth supporting, because Cameo already contains most of them:

| archetype | shape |
|---|---|
| refinery | worker → node → refinery |
| supply network | worker → supply source, no return trip |
| territory | captured point yields income |
| passive | structure generates without workers |
| combat-generated | fighting produces resources |
| risk/reward | higher yield, higher exposure |
| hybrid | any combination of the above |

⭐ A Generals-style supply economy is a *candidate archetype*, not a port. The value is
in the profile being general enough to describe it alongside the refinery model, so
factions can differ economically without the balance layer needing a special case each
time.

**Tempo** is the measurable part and the part that catches things unit pricing misses:
time-to-first-expansion, time-to-tech-tier, time-to-army-threshold, income per minute,
production capacity per minute. A faction can be priced correctly per unit and still be
too strong because it reaches everything sooner.

---

## 5. Shape of a game, not just a fight

**Snowball slope.** An advantage should pay off — a game where leads mean nothing is
dull. The question is the *slope*: does a won engagement convert into map control, then
income, then production, then an unanswerable army? Measure amplification rather than
trying to eliminate it.

**Comeback room.** After losing an army, an expansion or a tech tier, does the loser
still have decisions? This is a property of the system, not of any unit.

**Failure severity.** What a mistake costs should scale with how avoidable it was. A
mechanic that is high-impact *and* low-effort deserves more scrutiny than one that is
high-impact and demanding — the second is skill expression, the first is a coin flip.
Worth tracking alongside power: micro burden, setup burden, positioning burden,
attention burden.

---

## 6. Coverage, reachability and role

**Role coverage.** Tag units by role — scout, raider, anti-infantry, anti-armour,
anti-air, siege, artillery, assault, defender, support, harvester, transport, detector,
builder — then build a role × tech-tier matrix per faction. Holes show up immediately,
and a hole is usually more interesting than a mispriced unit.

**Faction identity as a checkable claim.** [`FACTION_IDENTITY.md`](FACTION_IDENTITY.md)
declares each faction's bias. A roster can contradict its own declaration — a faction
described as fragile and high-tech while holding the best armour and range is a design
failure even at a 50% win rate. That contradiction is detectable.

**Reachability.** Separate from balance: can a unit, upgrade or power actually be
reached — by a human, *and* by the AI? Cameo has already been bitten here. A mechanic
gated behind a promotion no bot buys is not exercised by any automated test, and content
nobody can build is a coverage hole rather than a balanced design. Worth its own audit:
minimum prerequisite path, minimum cost, minimum time, and whether the AI's decision
logic can ever get there.

**Build orders.** The sequence is more informative than the units. Earliest tech,
earliest expansion, first army timing, first AA, first anti-armour, first detection,
first siege — that is where timing imbalance lives.

---

## 7. Things that need their own model

Ordinary class pricing does not describe these, and forcing them through it produces
confident nonsense:

* **Heroes** — build-limited, persistent, often carrying auras and veterancy.
* **Superweapons** — priced on map influence, warning time, counterplay window and
  economic opportunity cost, not on damage per credit.
* **Transports, harvesters, builders** — value is logistical.
* **Promotions and upgrade trees** — the unit of value is the *choice*, not the bonus.
  A promotion is balanced when several paths stay viable, not when each grants equal
  raw statistics.
* **Transforming units** — a state machine with transition cost, not two units.

This is the argument for an explicit exception registry: these should be *data* with a
recorded reason, not a special case buried in a script.

---

## 8. Data, when there is any

Cameo collects no telemetry today, and this section is a schema to grow into rather than
something to act on.

If it existed, the discipline matters more than the fields: **condition every statistic**
on skill band, matchup, faction, map, game duration and game state, and never act on a
sample too small to mean anything. Usage and presence often say more than win rate — a
unit built in almost every game at 51% is a stronger signal than a niche unit at 54%.
And a metagame moves: a strategy nobody has answered yet looks identical to a structural
imbalance for the first few weeks.

Simulation, if it ever comes, is worth staging: deterministic micro-scenarios first,
then repeated engagements, then build-order simulation. Each stage is evidence about the
model, not proof about the game.

---

## 9. How to use this without breaking the queue

Nothing here authorises work. The order in [`HANDOFF.md`](../HANDOFF.md) §3 stands:
weapon structure first, and no price is final while zero class anchors are signed off.

What this page is for is the moment *before* a metric gets built — so that when the
strategic layer is scheduled, it is designed against the questions that matter rather
than rediscovered one mispriced faction at a time. The evidence ladder in
[`BALANCE_PIPELINE_GAPS.md`](BALANCE_PIPELINE_GAPS.md) §4 applies to everything above.

⛔ **"None of it is measured yet" was true when this page was written and is NOT true now.**
That sentence stood here after four of these sections had partly landed, which is the exact
failure this repository keeps paying for — a summary outliving its artifact. Re-measured against
the tree 2026-08-30:

| § | dimension | what exists in the tree today | state |
|---|---|---|---|
| 1 | what "balanced" is not | no win-rate tuning (no telemetry to tune to); asymmetry protected by `FACTION_IDENTITY.md` | **aligned by default** |
| 2 | counterplay taxonomy | `docs/balance/counter_matrix.yaml` + `audit_counter_matrix.py`, which cite this page by name. But they implement RELATION TYPES (hard / soft / generalist / forbidden / neutral), a different cut from the 11 RESPONSE AXES here — only `armor` and `tech` appear in both, and `detection`, `terrain`, `timing`, `economic` appear in neither file | **partial** |
| 3 | TTK decomposition | `effective_damage.py` (falloff, area geometry, projectile impact), `audit_burst_delays.py`, and **overkill modelled explicitly** — `weapon_efficiency` reports it ALONGSIDE K rather than inside it, precisely because it moves with `Damage`. Burst / sustained / setup / squad are not four separate metrics, and there is no first-shot or spin-up term | **partial** |
| 3 | effective survival | `target_model.py` (armor census, armor weights, shield damage share, shield-HP factor), `audit_survivability_pricing.py`, `armor_exposure.py` — the layers are modelled as PRICING, not as survival TIME against representative threats. No healing, repair, stealth or retreat term | **partial** |
| 4 | economy + tempo | `HARVESTER_BALANCE.md`'s six-parameter income model, `harvester_income.py`, `harvester_table.py` — ONE archetype (refinery). No `EconomyProfile`, no archetype registry, and **zero** tempo metrics: `time_to_tech`, `first_expansion`, `army_timing`, income/minute all return no hits in `tools/` | **the largest gap, as predicted** |
| 5 | snowball / comeback / failure severity | nothing — no hits for any of it in `tools/` | **absent** |
| 6 | coverage / reachability / role | the 28 class anchors ARE a role taxonomy; `audit_upgrade_coverage.py` finds roster-wide holes; `audit_buildable_order.py` checks prerequisite and palette order; `audit_ai.py` checks AI WIRING. Missing: a role × tech-tier matrix per faction, faction identity as a CHECKABLE claim, build-order timings, and reachability by the AI's DECISION logic (wiring is not reachability) | **partial** |
| 7 | things needing their own model | ⭐ **the closest to done.** `docs/design/balance_exceptions.yaml` is exactly the "data with a recorded reason" this section asks for: every entry carries `in_formula`, `ruling` and `method`. Covers combat units, defenses, heroes (in formula, no separate track), superweapons (out, method TO BUILD), harvesters, weaponless support, props. Not covered: transports, builders, promotion/upgrade TREES, transforming units | **mostly landed** |
| 8 | telemetry | none, as this page says. Confirmed: no hits for `telemetry`, `win_rate` in `tools/` | **absent, by design** |

So the honest summary is **the fight is well modelled and the game is not**. Everything inside one
engagement — damage, armor, overkill, survivability layers, counter relations — has an owner and an
audit. Everything spanning a MATCH — economy shape, tempo, snowball, build-order timing, role
coverage per tier — has none. That is a coherent place to be given the board's order (weapon
structure before pricing), and it is the shape of the remaining work.
