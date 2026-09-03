# What the one-click balance pipeline still needs

_Companion to [`BALANCE_PIPELINE.md`](BALANCE_PIPELINE.md) (the machinery as it exists) and
[`BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md) (the W-board and its binding order)._

This page holds two things: the **gaps** between today's tooling and a single deterministic
command, and the **verified residue** of an outside review round — what it got right, what it
got wrong, and why.

---

## 0. The lesson that came out of the review round

In August 2026 five external AI systems were asked to review this repository and draft an
operating prompt for balance work. Their outputs contradicted each other on basic facts: one
declared the core balance documents nonexistent, another declared them present; several cited
paths that resolve to nothing.

Checked against the tree, the pattern is single and complete:

| what they cited | actual state |
|---|---|
| `MASTER_REPORT.md`, `audit/FINDINGS.md`, `BALANCE_MEGAPLAN.md`, `MEGAPLAN_YAML_CLEANUP.md`, `PROJECT_CONTEXT.md`, `AI_HANDOFF_2026-08-05.md`, `AREADAMAGE_HANDOFF.md` | **all seven removed or merged by `20f15194`** (the 83→43 compaction) |
| "the balance documents do not exist" | **all eleven exist** — pipeline, program plan, estimate, Formula V2, effective damage, both armor documents, faction identity, decisions, vision, class anchors |

Every reviewer was reading the same **pre-compaction snapshot**. Their disagreements were not
disagreements about the repository; they were disagreements about *when*.

⭐ **A review of a repository snapshot is a review of a date.** Before acting on any outside
report — human or machine — establish which commit it saw. A confident report about a file that
moved is indistinguishable from a report about a file that never existed, and both read as
authoritative. The cheap check is `git log --all -- <path>`: a path with commits behind it and
none at HEAD was *moved*, and the reviewer's substance may still be sound even though its
address is stale.

### 0b. The same lesson twice more: load state, then namespace

Two further disagreements ran on the same fault line, and neither was a disagreement about
the game.

**Load state.** The audits report four USA condition families as inert across ~1,042 actors;
the Generals branch reports them working end to end. Both are right, about different trees —
and the mechanism is worth reading in full, because it is four links long and only the last
two are on master:

```
usacommand  (rules/generals.yaml — NOT LOADED)
  produces a doctrine upgrade
    → GrantConditionOnProduction@1b/2s/3h   grants usabombardamentx / …x
      → ProvidesPrerequisite@1b/2s/3h       supplies prerequisite "usabombardament"
        → defaults.yaml:5009  GrantConditionOnPrerequisite  grants the condition
          → Firepower / ReloadDelay / Damage / Range / Speed multipliers fire
```

⚠ **This is a complete, correct mechanism, not rot.** An earlier draft of this section
called it dead wiring and named `ProvidesPrerequisite` as "the only provider" — that is link
three of four, and the word "dead" implies decay that is not there. Nothing is broken. The
front end simply lives in content `mod.yaml` does not load, so on master the conditions can
never be granted and the five multipliers are inert; enable Generals and the whole chain
works.

The ~1,042-actor scale is not a red flag either: the multipliers hang off
`^PropagandaEffectBuff`, which `^BasicUnit` inherits at `defaults.yaml:2418`, and nearly
every unit in the mod descends from `^BasicUnit`.

**Namespace.** The same four tokens then went missing entirely — searched for on master by
one party and found, searched for in a contributor's working archive and not found. Neither
search was wrong. That archive had renamed 874 actors plus every id that doubles as a string
match, so `usabombardament` had become `usa_doctrine_bombardmentbattleplan` locally and
nowhere else. Grepping master's names against a renamed tree returns nothing, and "not found"
reads exactly like "removed upstream".

⭐ **Three forms of one mistake, all of them "not found" mistaken for "not there".**
A finding is scoped to a commit, to a load state, *and* to a namespace. Before concluding
that something is absent, establish which tree, which loaded content, and which naming
generation the search ran against — and prefer tracing a mechanism end to end over inferring
its absence from a grep that returned nothing.

---

## 1. Claims checked against the artifact

Everything below was re-measured on the tree, not taken from the reports.

### Confirmed true

| claim | evidence |
|---|---|
| Generals / ShockWave / Elementals are dormant | all six rule/weapon files present on disk, every line commented out in `mod.yaml` |
| No Generals ContentPack on master | `ContentPacks/` holds Core, D2k, Outpost2, RedAlert, RedAlert2, RedAlert2Mod, Shared, StarCraft, TiberianDawn, TiberianSun, Warcraft2 — no Generals |
| `elementals.yaml` is nothing but Targetable immunity templates | 39 lines: five elemental target types plus `^FireImmune` / `^IceImmune` / `^ToxinImmune` / `^BulletImmune` |
| `glblackmarket` carries two `Inherits` keys in one node | `rules/generals.yaml` 2501–2504 |
| `USA_EMP_PatriotMiss*` weapon-suffix violations exist | 2 in `weapons/generals.yaml` |
| `SpawnActorOnDeath@Scraps` is absent from `^Vehicle` | the only surviving match is an unrelated `@ScrapsAvatar` in `tiberiaalliances.yaml` |
| `noid_resolved.json` and `scratchpad/` are tracked at root | both present |
| The pipeline has no single entry point | `tools/balance/` holds 50+ scripts and no orchestrator |

### Confirmed false, or misleading enough to be false

| claim | what the tree says |
|---|---|
| `rules/generals.yaml` is 3,410 lines | **14,398**. `shockwave.yaml` is 16,487. |
| The board runs W1–W24 (or W1–W26) | it runs to at least **W27**, which has a landed guard and an owner |
| Remaining effort ≈ 510 agent-hours | the estimate document says **≈455 h serial**, 80–135 sessions |
| "Never use `Targetable` — use armor types instead" | `Targetable` has **777 live uses** and is the ordinary OpenRA mechanism for target types. See §2. |
| The repository is `Zeruel87/Cameo-mod` | it is `cameo-mod/Cameo-mod` |

### True in intent, wrong in arithmetic

**The overlay armors.** The ruling that binary immunity is replaced by conditional resistance is
real and shipped: `Armor@HAZMAT` (hazmat suits and Soviet reactive armor, ~329 actors) and
`Armor@REFLECTOR` (Allied reflective plating, ~16 actors) are condition-gated overlays carried
*in addition* to an actor's real armor.

The "reduces incoming damage by 50%" figure describes the mechanic **as it behaved before W21**,
when armor types multiplied. They now **average**, and a row of 50 against a base of 100 yields
75 — a 25% cut, not 50%. Averaging also caps the mechanic: one overlay can never exceed roughly
45%, because reaching 50% would require a row of 0, which is immunity again.

The generator already solves for this. Rows are derived from the reduction they should produce
rather than written directly, against `OVERLAY_DEPTH = 0.45`. The 100 reference is not an
assumption — MEAN-100 pins every family's Versus mean to exactly 100.

⛔ **Do not "restore" 45 to 50.** The gap is the arithmetic change, not a regression, and 50 is
unreachable by construction. And omitting an overlay row is **not** the same as writing 100: an
absent row drops the overlay out of the average entirely, while 100 pulls the result toward 100.
Omission is the only way to say a weapon ignores the plating.

---

## 2. The Targetable ruling, stated at its real scope

The deprecation is narrow and it is worth stating precisely, because the broad version was
already circulating as "never use `Targetable`" and would have been destructive.

* **Deprecated:** the `elementals.yaml` pattern — a `Targetable` node whose only purpose is to
  grant total immunity to a damage family. Binary immunity invalidates army composition and
  removes counterplay. Do not re-enable it, extend it, or reintroduce the pattern elsewhere.
* **Untouched:** `Targetable` itself, as the engine's mechanism for declaring what a thing *is*
  for targeting purposes. 777 live uses depend on it.

The replacement for immunity is the conditional overlay armor described above, which produces
resistance with a ceiling rather than an on/off switch.

---

## 3. Verified gaps — what a single command still lacks

The pipeline's stages exist and are documented. What is missing is the wiring and the layers
above it.

| gap | why it matters |
|---|---|
| ~~**No orchestrator.**~~ **CLOSED** — `tools/balance/run_pipeline.py`. | It ran the documented order on its first real pass and immediately found what the gap predicted: 22 of 33 raw ledgers stale against yaml. See §3b. |
| **No exception registry.** | Heroes, superweapons, harvesters, transports and promotion-only actors have no declared escape from class pricing, so each pass re-litigates them. |
| **No constraint reporting.** | When a computed value exceeds what the engine can carry, nothing records *desired* alongside *implementable*. A silent clamp changes the model without saying so. |
| ~~**No determinism check.**~~ **CLOSED** — `tools/balance/check_determinism.py`. | Measured at `c653f160`: **65 artifacts byte-identical** across two hash seeds and two timezones. The property held; what changed is that it is now evidence rather than an assumption. See §3c. |
| **Strategic layer absent.** | Counterplay, role coverage, tech reachability and economic tempo are not modelled anywhere, so a unit can price correctly and still be unhealthy. |

### 3b. What the orchestrator found on its first run

`run_pipeline.py` executes steps 1, 3, 7 and 8 plus the structural gates, reports each
stage's real exit code, and stops at step 6. It cannot apply — no flag reaches
`--confirm`, because a gate a tool can open by itself is not a gate.

Its first real run came back **FAIL**, on the oldest known failure mode in this
programme:

| stage | result |
|---|--:|
| drift — yaml vs committed ledger | **FAIL**: 22 of 33 raw ledgers stale, 5 model |
| multiplier modifiers integer | PASS |
| generator reproduces every family | PASS — drift 0 across 139 templates |
| empty warhead types | PASS — 0 of 2839 |

`CLAUDE.md` already warns that `audit_balance_drift` "only helps if someone LOOKS", and
that it had gone red twice for exactly this reason. This is the third time. The last
commit to re-extract was #293; something after it moved yaml without re-running step 1.

⭐ The remedy is one command — `python tools/balance/extract_stats.py`, then commit the
ledgers with the yaml — and it belongs to whoever lands the next balance commit, not to
a drive-by. The weapon-consolidation work already re-extracts as part of its flow; a
single commit that skipped it left 22 ledgers stale. That is the argument for a runner
in the documented order rather than a discipline nobody can see failing.

The first three are mechanical and can be built without touching a balance number. The last two
are design work that must not run ahead of the W-board.

---

### 3c. Determinism, measured

`check_determinism.py` extracts twice in **separate processes** under different
`PYTHONHASHSEED` and `TZ`, builds the ledgers in memory, and compares every artifact
byte for byte. Separate processes are the design: inside one interpreter the hash seed
is fixed, so set and dict iteration order is stable by accident and an ordering leak
stays invisible. Nothing is written under `docs/balance/` — a tool that verifies the
ledgers must never be able to be the thing that moved them.

**Result at `c653f160`: 65 of 65 artifacts byte-identical.** Raw ledgers, derived
sidecars and the model constants all reproduce.

That is a good answer, and it is worth being precise about what it is worth. It shows
those two configurations agree. It is not a theorem: a different OS, Python version,
filesystem ordering or locale is a separate experiment, and nondeterminism that is
stable within a process but varies by machine is invisible to it.

⭐ **A checker that cannot fail is worse than no checker**, because it manufactures
confidence. This one was proven against an injected fault before being trusted — a list
built by iterating a set of eight strings, the exact bug class it claims to catch. It
named the artifact, the line and both values, gave the right diagnosis, and exited 1.
Do that to any gate before believing its green.

`serialize()` already writes `sort_keys=True`, so mapping order was never the risk.
Sorting keys does nothing for the order of a **list**, which is where a set leaks.

## 4. Design guidance worth keeping — non-binding

The review round produced RTS and live-service balance material that is genuinely useful as
*shape*. It is recorded as provenance only. Its citations were not verifiable from this
repository, and where any of it meets `DESIGN.md`, **DESIGN.md wins**.

📖 **The full treatment now lives in
[`RTS_BALANCE_REFERENCE.md`](RTS_BALANCE_REFERENCE.md)** — counterplay as a checkable
taxonomy, TTK decomposed, the economy profile and its archetypes, tempo, snowball slope,
role coverage, reachability, and what needs its own model instead of class pricing. The
first pass through this material compressed it to the six headlines below and lost the
structure; the reference page is where it was put back.

* **Balance is viability, not equality.** The target is that many options stay playable at high
  skill with no strategy crowding the rest out — not equal damage per credit, and not a 50%
  win rate as a law. Cameo is a deliberately asymmetric crossover; flattening factions toward
  identical mechanics would destroy the thing it exists for. A common *measurement* framework,
  never a common mechanical identity.
* **Counterplay is a first-class property.** A strong unit is not unhealthy if the answer is
  reliable and legible. A unit can be unhealthy at fair cost if its range, mobility or timing
  denies any response. Worth modelling explicitly: which counters exist, at which tech tier, and
  whether they arrive before the threat has already decided the game.
* **An evidence ladder.** Intuition → static calculation → resolved-ruleset analysis →
  simulation → AI games → human play → live telemetry. The value is in never presenting the
  cheap end as the expensive end, and in making **UNKNOWN** a legal answer instead of a
  manufactured verdict. This matches the repository's own "artifact wins" doctrine.
* **Win rate is one input.** Read it conditioned on skill, matchup, map, duration and sample
  size; usage and presence often say more than the rate. Do not build automatic balance changes
  on statistically meaningless samples, and separate a structural imbalance from a strategy the
  metagame has not answered yet.
* **Economy and tempo are under-modelled here.** Time-to-expansion, time-to-tech, income and
  production per minute catch factions that are correctly priced per unit and still too strong.
  Cameo spans several source games with genuinely different economic models, so any future work
  wants a generic economy profile rather than one hard-coded harvesting scheme.
* **Reachability deserves a check of its own.** Whether a unit, upgrade or power can actually be
  reached — by a human *and* by the AI — is separable from whether it is balanced. Dormant
  content that no one can build is a coverage hole, not a balanced design.

None of this is authorised work. It is a backlog to draw from once the weapon structure settles.

---

## 5. What not to adopt from the review round

* **A generic cost formula.** Suggestions to price units from a fresh damage/health expression
  would displace Formula V2, class anchors and K. The architecture already exists; extend it.
* **Bidirectional Excel authority.** The workbook is a workbench. It may be edited and imported,
  but it is never an independent source of truth alongside the ledgers.
* **Pricing before structure.** The board's order is binding for a measurable reason: weapon
  structure feeds K, K feeds price, and pricing an unstable K prices inputs that are about to
  change.
* **Blanket bans phrased from a narrow ruling.** See §2. A rule stated wider than the decision
  behind it destroys working content.

---

## 6. Where this leaves the queue

Nothing here changes the order in [`HANDOFF.md`](../HANDOFF.md) §3. The weapon rebuild still
comes first, and no price is final while zero class anchors are signed off. The mechanical gaps
in §3 are the parts of this page that can be built in parallel, because none of them writes a
balance number.
