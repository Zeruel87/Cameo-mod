# Cameo AI Architecture Review — Current Master `192ed5701`, 2026-10-02

**Reviewed repository:** `cameo-mod/Cameo-mod`  
**Reviewed master:** `192ed5701f2bbb16b976e41fbd9d840df1c2de2e`  
**Included merges:** #773, #774, #776 and the earlier 2026-10-02 coalition/formation consolidation  
**Post-review master note:** `6490e520f03d` landed afterwards and changes only `DEVELOPMENT_LOG.md`; runtime/code findings remain based on `192ed5701`.  
**Purpose:** independent architecture review after the evening merge, with emphasis on ownership, lifecycle, A/B correctness, team coordination and the boundary to cross-AI SCG/Dispatch interoperability.

## Executive summary

The evening merge is a net architectural improvement. Cameo is increasingly converging on the right structural rule for a large modular RTS AI:

> **One authority per decision; providers/advisors may influence it, but existing owners emit the orders.**

That rule is now visible across formation, placement, army-first policy, scale targets, parallel production, field economy and build-order adaptation. The new FE/BO work also adds something Cameo badly needs at this stage: measurement before tuning. Placement/build-order logs and expansion telemetry make future changes much easier to evaluate from evidence rather than spectator impression.

The current tree nevertheless has several concrete integration issues worth fixing before more switches are armed:

1. **The committed architecture audit/module-map evidence is stale** relative to current master.
2. **`increment_switches.yaml` still contains obsolete switch targets** from before the one-owner consolidation.
3. **TC-3 still assumes more temporal coherence than the current staggered broadcast system guarantees.**
4. **Team broadcasts still lack one central liveness/freshness rule.**
5. **Coalition rescue can assign the same responder to multiple simultaneous requests.**
6. **BO-1's `out_earned` reaction is player-count dependent** because it sums every living enemy economy but compares the sum with one bot's economy.
7. **The build-order report and tuner use different objective functions**, so the human-facing report can disagree with the optimization gate.
8. **The tuner calls the experiments paired/mirrored but analyzes pooled independent means and then selects among multiple candidate arms**, which weakens the statistical gate.

None of these requires replacing the architecture. They are boundary/lifecycle/lab-contract problems around an otherwise healthier core.

The SCG/Dispatch proposal should remain separate from Cameo TC-3. TC-3 is useful rich same-family coordination. SCG is a tiny neutral relay boundary between *different* AI implementations and must not become another brain.

---

## 1. Current architecture at `192ed5701`

A useful compressed map is:

```text
OBSERVE
  BotSituation / FogMemory / TacticalMap / Threat / Influence / telemetry
        |
        v
SYNTHESIZE
  MasterAi / UtilityAxes / Director / TeamBroadcast / CoalitionFold
        |
        v
PLAN / ADVISE
  ExpansionPlanner / DefenseCoverage / Siege / Formation / ScaleTargets /
  BuildOrderKnobs / Spacing / StealthDoctrine / ProductionWidth
        |
        v
ARBITRATE
  BaseBuilder / UnitBuilder / SquadManager / leases / action budget
        |
        v
EXECUTE
  squad states / engineer / repair / harvest / deploy / transport etc.
        |
        v
VERIFY / LEARN OFFLINE
  mission outcomes / placement log / expansion log / reports / A-B / tuner
```

The important property is not the number of modules. It is that the new modules are mostly **providers of bounded inputs** rather than second order issuers.

Examples:

- `SpacingAdvisorBotModule` -> `IBotPlacementAdvisor`; queue manager still places buildings.
- `AssaultFormationBotModule` -> `IBotAssaultFormation`; squad state still moves the squad.
- `ScaleTargetsBotModule` -> `IBotScaleTargets`; existing builders decide what to queue.
- `ParallelProductionBotModule` -> `IBotProductionWidth`; `UnitBuilderBotModuleCA` still owns production orders.
- `BuildOrderKnobsBotModule` -> `IBotBuildOrderKnobs`; base-builder logic still owns structure choice and timing.
- `CoalitionFold` -> `IBotCoalition`; existing Master/Squad/Expansion owners consume the directive.

That is the correct general direction.

---

## 2. What the evening merge improved

### 2.1 One-owner consolidation is now visible in real code

The 12.7a/12.20 consolidation is exactly the right kind of cleanup. Previously overlapping mechanisms for assault deployment, spacing and army-first policy are being collapsed into one owner/seam instead of stacked as independent brains.

The unified concave/objective deployment state is especially healthy architecturally: geometry/configuration may come from a provider, but squad states remain the only movement authority.

### 2.2 Field economy separates *measurement*, *policy* and *execution*

FE-0 adds behavior-neutral logging. FE-1 is behind `AJ_field_coverage`. The planner publishes refinery-law/claim information and the existing base builder consumes it. This preserves the execution owner instead of introducing a second refinery builder.

The one-refinery-per-anchor model is also much more directly tied to the actual resource geography than the old yard-count ceiling.

### 2.3 BO-1 is a provider, not another base builder

`BuildOrderKnobsBotModule` publishes eight bounded multipliers and an opening through `IBotBuildOrderKnobs`. It does not place buildings itself.

That is the right boundary. It makes it possible to tune *how and when* the existing owner builds without duplicating the owner.

### 2.4 The new logs create a real experimental surface

`cameo-ai-placements.jsonl`, the expansion snapshot block, `build_order_report.py`, `expansion_report.py` and the knob tuner are a major process improvement.

The architecture is now mature enough that the next regressions are likely to be interaction regressions. Instrumentation is therefore as important as another behavior module.

---

# 3. Immediate integration findings

## P0 — 3.1 The generated architecture evidence is stale

`AI_ARCHITECTURE.md` says the generated module map is authoritative, but the committed generated files do not describe current master:

- `docs/design/AI_ARCH_COVERAGE.md` last changed at `2fbd9a811fef` (10:21 UTC).
- `docs/design/AI_MODULE_MAP.md` last changed at `85c95b257683` (06:39 UTC).
- current master is `192ed5701` after the evening coalition/FE/BO merges.

The current human-authored architecture says **68 distinct trait types / 93 Player instances**, while the generated evidence predates several of those types and seams.

This matters because the generated files are supposed to detect exactly the kind of integration drift described below.

**Recommendation:** regenerate on current master and make stale generated architecture evidence a merge failure whenever the AI surface changes.

Suggested gate:

```text
python tools/ai/ai_module_map.py --check
python tools/ai/ai_arch_audit.py --check
```

Do this on the merged commit, not only on an earlier branch baseline.

---

## P0 — 3.2 `increment_switches.yaml` still contains obsolete pre-consolidation targets

The one-owner merge documents that the old BaseBuilder fields were removed:

```text
MinBuildingGapCells
MinBuildingGapDefensesCells
MinArmyUnitsBeforeBuildings
ArmyFirstMinCash
```

Current source confirms those fields are no longer on `BaseBuilderBotModuleCA` / its queue-manager Info surface.

However current `tools/ai/increment_switches.yaml` still contains the old groups:

```yaml
AD_army_first:
  BaseBuilderBotModuleCA:
    MinArmyUnitsBeforeBuildings: 14
    ArmyFirstMinCash: 1500

AE_spread_assault:
  BaseBuilderBotModuleCA:
    MinBuildingGapCells: 2
```

The *new* owners already have their proper groups (`AD_spaced_base_placement`, `AE_army_first`, etc.), so these are stale leftovers.

`apply_increment_switches.py` is intentionally a mechanical editor: it will insert a requested field under a matching trait even when that field no longer exists in C#. The `wiring` audit reported in PR #776 does not validate this class of switch field. `ai_arch_audit.py` R2 is the audit intended to validate it, but the committed architecture audit predates the merge.

**Risk:** a later `--groups all` or direct arm of these stale groups can generate an invalid experiment worktree or an experiment that no longer means what its label says.

**Recommendation:** delete the obsolete groups/targets, regenerate `AI_ARCH_COVERAGE.md`, and explicitly run R2 on `192ed5701` before the next increment batch.

This is the highest-confidence concrete merge-cleanup finding in this review.

---

# 4. TC-3 / same-family coalition findings

## P1 — 4.1 “Identical CoalitionDirective” is still not guaranteed by the runtime cadence

`CoalitionFold` is deterministic **for one identical set of broadcasts**. The tests establish that correctly.

Runtime publication is staggered:

```csharp
nextSnapshotTick = Math.Abs(player.ClientIndex * 37) % Math.Max(1, info.SnapshotInterval);
```

Each bot then publishes its fresh own `TeamBroadcast` and immediately folds it with whatever ally broadcasts currently exist.

Therefore one member can fold:

```text
A generation 20
B generation 19
C generation 20
```

while another folds a few ticks later:

```text
A generation 20
B generation 20
C generation 20
```

A deterministic function over different inputs does not guarantee an identical result.

This affects `MainTarget`, `Phase` and rescue elections when the TC-3 switches are armed.

Two valid designs exist:

**Strict common directive:** introduce a team epoch/double buffer and consume only a completed previous generation.

**Eventual consistency:** keep the simple staggered board, but document that directives may transiently differ and make all consumers tolerant of that.

Current docs/tests describe the first invariant while runtime behaves closer to the second.

---

## P1 — 4.2 TeamBroadcast has a timestamp but no central liveness contract

`TeamBroadcast` carries `SnapshotTick`, but `TeamBlackboard.CollectBroadcasts` primarily filters by bot/alliance and returns the latest enabled provider value.

It does not centrally require:

```text
publisher alive
SnapshotTick > 0
now - SnapshotTick <= max_age
```

OpenRA retains `Player`/`PlayerActor` after defeat, so a last broadcast can remain readable after the participant is no longer active.

Possible effects when team switches are armed:

- stale Climax affects sync attacks;
- stale defence request remains eligible;
- stale expansion claim makes a live ally yield;
- stale target vote remains in a coalition fold;
- stale sector identity remains in the fold.

**Recommendation:** one central validity function before *any* team aggregation, e.g.:

```text
ValidTeamBroadcast(p, b, now) =
  p.WinState == Undefined
  && b.SnapshotTick > 0
  && now - b.SnapshotTick <= TeamBroadcastMaxAge
```

Do not make every consumer solve freshness separately.

---

## P1 — 4.3 Coalition rescue can assign one responder to multiple simultaneous requests

`CoalitionFold.Compute` builds `freePool` once, selects the nearest responder for each requester, but does not consume the selected responder.

With two simultaneous defend requests, the same nearby army can therefore be elected for both.

If “nearest free ally” is the intended semantic, the basic rule should be:

```text
one participant -> at most one rescue assignment per fold
```

Remove the selected responder from the pool after assignment. If multi-rescue is later desirable, model explicit capacity rather than accidental reuse.

---

## P1 — 4.4 `ClientIndex` should not be the universal coalition participant identity

TC-2/TC-3 use `ClientIndex` for precedence, rescue identity and sector anchors.

That works for ordinary lobby bots, but OpenRA map-side bots can inherit the host/admin client index. Multiple map-side participants can therefore share it.

For generalized coalition identity, use a stable match-local player identity (`Player.InternalName` / slot key / explicit participant id). Keep `ClientIndex` only where lobby ordering itself is the intended rule.

This matters even more if Cameo later exposes an SCG adapter to Fransbot, stock AI or map-side bots.

---

# 5. FE-1 / field economy review

## 5.1 The ownership boundary is good

FE-1 does **not** introduce a second refinery/base builder. `ExpansionPlannerBotModule` publishes the active refinery law/anchor claim and `BaseBuilderBotModuleCA` remains the decision/order owner.

That is architecturally clean.

## 5.2 Failure lifecycle is bounded

The new anchor path includes `AnchorStuckReplans` and parking, and in-flight MCV sites are removed when the actor is gone/deployed/dead. Those are good lifecycle details and avoid the infinite retry class found in earlier Fransbot/Cameo reviews.

## 5.3 The aggressive MCV values are correctly treated as experiment values

`AJ_field_coverage` raises inflight MCV count, lowers reserve and raises target floor. The docs explicitly label these as unmeasured starting values for A/B rather than architecture truths. That is correct.

No architecture objection here: measure them with FE-0 before promoting them to defaults.

---

# 6. BO-1 / build-order lab findings

## P1 — 6.1 `out_earned` is player-count dependent in team/FFA games

`BuildOrderKnobsBotModule.ReactInputs` sums economy proxy across **every living enemy**:

```text
enemyEconomy += enemy.Harvesters + enemy.Refineries * 2
```

but compares that sum with **this one bot's** own economy:

```text
OwnHarvesters + ownRefineries * 2
```

`Evaluate` then triggers `OutEarned` when the summed enemy value exceeds own economy by `ReactOutEarnPct`.

In a roughly even 2v2, two comparable enemies naturally sum to about 2x one bot. In 6v6 the effect is much stronger. The reaction can therefore become almost a proxy for “there are multiple enemies”, not “this bot is economically behind”.

This is especially important because Cameo now has explicit multi-team harnesses.

**Recommendation:** normalize by population before applying the threshold. Two reasonable semantics:

```text
average observed enemy economy per living enemy
vs
own economy
```

or, if the intended question is coalition economy:

```text
observed enemy-team total
vs
allied-team total
```

The first is simpler and keeps BO-1 local. Do not use SCG for this; it is internal Cameo reasoning.

---

## P1 — 6.2 Human report and tuner optimize different score functions

`tools/ai/build_order_report.py` defines:

```text
speed weight = 0.5
reference = 30 game minutes
score = win + margin + speed
```

`tools/ai/tune_build_order.py` defines:

```text
speed weight = 0.25
reference = 54,000 ticks (~36 min at the assumed timestep)
score = win + margin + speed
```

The tuner also uses raw ticks, while the report converts ticks through the match timestep.

This creates a lab-contract problem: a developer can inspect `build_order_report.py` and see arm A score higher while the tuner is applying a materially different objective to decide whether arm A is accepted.

**Recommendation:** define the objective exactly once in shared tooling (`ai_log_common.py` or a dedicated score helper) and have both report and tuner import it.

One objective should mean one formula, one time unit and one set of constants.

---

## P2 — 6.3 The statistical gate is safer than blind tuning, but not yet truly paired

The tuner documentation calls the experiments paired/mirrored. The acceptance calculation is currently a Welch-style independent-means statistic:

```text
(mean_arm - mean_base) / sqrt(var_arm/n_arm + var_base/n_base)
```

and then the best significant candidate is selected among the measured arms.

Two issues follow:

1. mirrored map/seed/side pairs are not used as **paired differences**, so much of the controlled experimental structure is discarded;
2. repeatedly testing multiple knob/direction candidates and taking the best `z >= 1.96` inflates false-positive risk relative to one pre-specified comparison.

This is not a reason to remove the tuner. The current ≥20/arm threshold and one-coordinate-at-a-time update are much better than unguarded self-tuning.

**Recommendation for the next lab iteration:** match arm/base games by map/seed/side and test the distribution of paired score deltas. Add either a confirmation batch/holdout before `--write`, or a multiple-comparison correction when several candidates are evaluated from the same baseline.

---

## P2 — 6.4 Opening learning is confounded by knob experiments

Opening posteriors are updated from the same scored matches used for knob experiments. Therefore an opening win/loss can be credited while tempo/greed/production/etc. are deliberately perturbed.

That learns “opening performance averaged over whatever knob experiments happened to run”, not the isolated opening effect.

This may be acceptable if intentional, but it should be explicit. If the goal is a clean opening bandit, update opening posteriors from baseline/current-best knob matches only, or include the knob regime in the opening context.

---

# 7. Mission/lifecycle finding still open

The earlier mission-card boundary remains important: every committed attempt should reach exactly one terminal state, including match teardown.

If the current mission archive still permits open attempts at game end, close them with a bounded terminal record such as:

```text
RELEASED reason=match_end
```

A match ending is not automatically mission success or failure, but it must close the attempt lifecycle before the archive becomes learning evidence.

---

# 8. MasterAi: keep one owner, continue extracting pure components

`MasterAiBotModule` now implements/coordinates a very broad strategic surface: target selection, missions/outcomes, fog information, threat routing, prediction, memory, utility axes, Director, TeamBroadcast and coalition publication.

Do **not** split this into competing strategic brains.

Continue extracting pure internals behind one owner, conceptually:

```text
MasterAiBotModule
  -> SituationBuilder
  -> TargetEvaluator
  -> MissionLifecycle
  -> Utility/Director state
  -> TeamPublisher
  -> CoalitionFold adapter
```

The external authority remains one; the implementation becomes easier to audit and test.

---

# 9. SCG / Dispatch boundary after the new merge

The new FE/BO systems make the separation even clearer.

Cameo has rich internal state that **must stay private to Cameo**:

```text
Director phase/tension
Utility axes
CoalitionDirective
ScaleTargets
BuildOrderKnobs / opening / reactions
field coverage / refinery law
army centroid
internal sector anchors
```

None of that belongs in the common SCG protocol merely because it exists.

The neutral cross-AI boundary should expose only coalition-relevant intent/lifecycle, e.g.:

```text
INTENT      ATTACK / EXPAND / SECURE / DEFEND ...
COMMITMENT  same, now actually committed
REQUEST     capability/support request
RESPONSE    ACCEPT / DECLINE / PARTIAL / UNSUPPORTED
RELEASE     commitment/request no longer active
```

Cameo-to-Cameo can continue to use TC-3. Fransbot-to-Fransbot can use richer Fransbot communication. Stock AI may participate only through a coarse adapter.

**SCG remains a relay, not a coalition strategist.**

---

# 10. Recommended order of work

1. **Remove stale switch groups/fields from `increment_switches.yaml`.**
2. **Regenerate `AI_MODULE_MAP.md` and `AI_ARCH_COVERAGE.md` on `192ed5701`; run `ai_arch_audit.py --check`.**
3. **Unify BO report/tuner scoring into one shared function.**
4. **Normalize BO `out_earned` for multi-player/team games.**
5. **Define TC-3 consistency model: common epoch or documented eventual consistency.**
6. **Centralize TeamBroadcast liveness and alive filtering.**
7. **Make rescue capacity explicit; one responder per request by default.**
8. **Move generalized coalition identity away from `ClientIndex`.**
9. **Then run AJ/AK A/B experiments; do not tune unmeasured knobs before the lab contract is coherent.**
10. **Keep SCG/Dispatch outside TC-3 as a neutral adapter boundary.**

---

# 11. Overall assessment

Cameo is now much less a pile of AI modules and much more a layered system with explicit ownership and measurement. The evening merge strengthens that trend.

The highest-value fixes are no longer “invent more behavior”. They are **make the experiment switch surface trustworthy, make distributed team state explicit about time/liveness, and make the optimization objective singular and reproducible**.

The architecture can then support both rich Cameo-specific coordination and a separate minimal cross-AI SCG/Dispatch standard without adding another brain.

> **Keep internal intelligence rich. Keep ownership singular. Keep experiments reproducible. Keep cross-AI communication simple.**
