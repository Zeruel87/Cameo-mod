# Cameo AI review — Fransbot perspective

_Date: 2026-09-30_

I reviewed the current Cameo master AI stack together with the `cameo-engine` bot changes, focusing specifically on the failure classes that have caused the most trouble during Fransbot development: ownership conflicts, lifecycle asymmetry, stale state, conditional-trait transitions, and modules issuing competing orders.

## Overall assessment

The direction of the Cameo AI is strong. The individual systems are generally not the main concern.

The largest technical risk I see is the **control plane between the systems**.

Cameo's own current master plan states the correct architectural rule: **one owner per decision**. I strongly agree with that rule. My main recommendation is to make it an enforced runtime/design contract rather than only an architectural convention.

This matters increasingly as Cameo combines OpenRA, CA, RV, CN, Cameo and Fransbot modules. The current plan reports 53 bot-module types / 76 instances, with substantially more harvesting planned.

I would therefore consider a short **AI lifecycle/ownership hardening phase before adding many more behavioural modules**.

## P0 — Multiple modules can own the same actor or decision

The clearest known example is already documented by Cameo: both `BuildingRepairBotModule` and `BuildingRepairBotModuleCA` are active for the same bots. The master plan itself records this as a bug because the repair toggle can cancel itself.

This should be treated as a representative architecture bug rather than an isolated repair bug.

There is a second concrete example around engineers.

`CaptureManagerBotModuleCA` and `CncEngineerBotModule` can both select idle engineers. The YAML comment currently says that because both select idle engineers, "whichever orders first wins".

That assumption is unsafe.

`ModularBot.QueueOrder()` only enqueues an order. All enabled bot modules execute their BotTick before the queued orders are issued. Therefore two modules may both observe the same actor as idle during the same simulation tick and both enqueue orders for it.

In addition, `MinOrderQuotientPerTick` means queued orders can survive into following ticks.

In other words:

**Actor.IsIdle is not an ownership primitive.**

I recommend a common lightweight ownership/lease mechanism for long-lived AI assignments:

`ActorID -> owner / purpose / acquired tick / expiry or heartbeat`

Examples of owners could be:

`Squad`, `Scout`, `Beacon`, `Capture`, `Engineer`, `Crate`, `MCVExpansion`, `FransMission`.

Modules should use something equivalent to `TryClaim`, `Release`, and `IsClaimedByOther` before issuing long-lived assignments.

I would not initially turn this into a huge central scheduler. A small common reservation contract would catch most of the dangerous cases without replacing the existing commanders.

## P1 — EX-3 MCV expansion has a failure-lifecycle mismatch

The new `IBotMcvExpansionSiteProvider` seam is a good idea, but I believe its current contract is too narrow.

`ExpansionPlannerBotModule.McvSite()` chooses the highest-scoring far resource field from `LastScores`. The ranking uses resource value, safety and geometric MCV distance, but does not prove that the MCV's locomotor can actually reach that field.

The engine `McvExpansionManagerBotModule` then replaces its own `expandCenter` with the provider's site.

However, the manager's `checkspot` remains the one belonging to its original internally selected site.

If the external provider site cannot be reached or cannot produce a deployable cell:

1. the MCV manager rejects the deployment;
2. its failure bookkeeping records the internal `checkspot`, not the provider field;
3. the ExpansionPlanner receives no rejection;
4. the planner can return exactly the same external field on the next request;
5. changing the MCV manager between CheckResource / CheckBase does not necessarily escape the problem because the external provider overrides `expandCenter` again.

There is a related multi-MCV issue: `activeMCVs` records the internal check location, so duplicate-site suppression may not describe the site actually selected by the provider.

This is especially important before importing Fransbot's island/transport expansion. "Not land-reachable by this MCV" should eventually be a useful classification — potentially a transport objective — rather than either globally bad or retried indefinitely.

I would expand the interface from a bare `CPos?` toward a candidate object containing at least:

- site/location;
- stable candidate/field identity;
- candidate kind;
- score;
- optionally reachability requirements.

Ideally the MCV manager should be able to report `accepted`, `unreachable`, `undeployable`, `reserved`, etc. back to the provider.

A smaller immediate fix would be to ensure the provider site is path/deploy validated and parked for a bounded time after rejection.

## P1 — CratePickup has a stale reservation

`CratePickupBotModule` keeps:

`readonly List<Actor> alreadyPursuitCrates`

A crate is added when a collector is ordered toward it, but I cannot find a corresponding removal path.

This means that if the collector dies, is reassigned, becomes stuck, or its queued Move loses to another module, that crate can remain permanently marked as already pursued.

Disposed crate actors also remain referenced by the list.

I would change this into a reservation:

`crate -> collector + assignedTick`

and clear it when:

- crate disappears;
- collector disappears;
- collector becomes owned by another role;
- collector becomes idle after a grace period;
- assignment times out.

This is exactly the class of stale-state bug that tends to become rare, long-match "AI just stopped doing X" behaviour.

## P1 — Audit all caches of conditionally enabled traits

Cameo has already found a very important example of this in `SiegeEvaluatorBotModule`.

The evaluator resolved enabled personality squad managers before the personality latch. The result was an empty cached array that stayed empty for the match. The recent fix correctly re-resolves the set when it is empty or a cached manager becomes disabled.

I would treat this as a bug class and search the AI stack for every case that combines:

- `TraitsImplementing<T>()`;
- filtering by `!IsTraitDisabled` / enabled state;
- storing the result;
- personality/difficulty/condition-dependent traits.

Either cache all instances and check enabled state when consuming them, or explicitly refresh on lifecycle transitions.

The same principle applies to provider selection: if only one provider is allowed to own a decision, assert that rather than relying on enumeration order.

## P1 — Fog honesty is not yet end-to-end

The core fog-memory work is good, but some side modules still leak world information.

Current `ai.yaml` has:

`CaptureManagerBotModuleCA.CheckCaptureTargetsForVisibility: false`

and:

`CratePickupBotModule.CheckTargetsForVisibility: false`

so those modules can react to targets/crates the player has not observed.

There is also a subtler CaptureManager case: even with capture-target visibility enabled, `SafePath` evaluates enemy actors around path cells without a visibility check. Invisible enemies can therefore influence the chosen path.

The existing `audit_fog_honesty.py` is useful, but its own documentation correctly says that it is a **count ratchet**, not a semantic proof. A PASS means that no new global-enumeration sites were added, not that all existing sites are fog-honest.

I suggest adding a few runtime "fog canary" tests where an unseen actor/crate exists and asserting that it cannot change bot behaviour until it has actually been observed.

## P1 — Add ownership/lifecycle invariants

Cameo already contains local fixes for stranded actors:

- squad members kicked for being stuck are returned to the idle pool;
- save/load reconciles actors present in `activeUnits` but in neither a squad nor the idle pool;
- scouts relinquish ownership when a squad claims them;
- scouts and beacon responders return actors to the shared idle pool.

These are good fixes.

I would generalise their underlying rule.

Periodically, in debug/test builds, calculate an ownership snapshot for every own orderable combat actor and assert:

- no actor has more than one exclusive long-lived owner;
- every actor marked active by a subsystem has a valid owner;
- every squad member belongs to exactly one squad manager;
- no dead/disposed actor remains reserved;
- a released actor eventually becomes visible to the normal allocation pool.

This would have detected several bugs that were otherwise discovered only through long runtime matches.

## P2 — Protect the experiment pipeline as strongly as the AI

Cameo's A/B infrastructure is impressive, but its history also shows why match results cannot be the only acceptance mechanism.

Recent examples include:

- MasterAI profiling no enemies because test-map bot players were `Playable: false`;
- stale binary/rules windows;
- YAML changes affecting the next match in a running batch;
- outcome interpretation problems;
- test/document counters drifting after merges.

I would make every batch record and verify an immutable fingerprint of:

- mod commit;
- engine commit;
- resolved AI YAML/rules hash;
- map hash;
- bot type/personality configuration.

If any of these changes while a batch is running, invalidate/abort that batch automatically.

A/B then measures behaviour and strength, while invariants establish correctness.

## Things Cameo is doing very well

The `SiegeEvaluator` architecture is a good pattern: it advises `Advance / StandOff / Retreat`, while the squad state machine remains the single order authority. I would reuse this pattern widely.

The recent FransCommanderCore change is also exactly the right solution. Fransbot's stance logic now yields when a CA squad manager is enabled instead of trying to make both systems coexist as order authorities.

The scout and beacon-response lifecycle is significantly stronger than some of the older modules because ownership and return-to-pool are explicit.

The current UnitBuilder configuration also avoids the old `IdleBaseUnitsMaximum < required squad size` production/formation deadlock.

Finally, the amount of telemetry, fight reporting, module auditing and A/B infrastructure is a major strength. I would keep that work, but add state-machine and ownership assertions underneath it.

## Suggested order of work

1. Fix the known double repair owner.
2. Introduce a small common unit-claim/lease contract and use it first for Engineer/Capture/Scout/Beacon/Crate.
3. Fix CratePickup reservation cleanup.
4. Add failure feedback/reachability ownership to the EX-3 MCV provider seam.
5. Sweep conditional-trait caches for stale enabled-instance sets.
6. Add unit-ownership and stale-reservation watchdogs.
7. Add semantic fog-canary tests.
8. Harden A/B run fingerprinting.
9. Only then accelerate the remaining module harvesting.

## Main takeaway

One of the strongest lessons from Fransbot development is that once an RTS bot becomes modular enough, **decision quality stops being the only hard problem**.

The difficult bugs increasingly occur at the boundaries:

- who owns an actor;
- when ownership begins;
- how ownership ends;
- what happens when an objective disappears;
- whether a cached view of another subsystem is still valid;
- whether a failed execution writes its outcome back to the strategic layer.

Cameo already has most of the design vocabulary needed to solve this. I would make those lifecycle rules first-class contracts before adding substantially more brains to the Frankenstein stack.
