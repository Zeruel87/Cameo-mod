# AI review from the Fransbot author (2026-09-30): verified findings, response and plan

**Source:** an ordered review of the Cameo master AI stack and the `cameo-engine` bot changes by **Codex Astra from
Fransotto, the creator of Fransbot**, relayed by the maintainer on 2026-09-30 with the order to write it into the
documentation, act on it, reply, and fold it into the plan. Scope: ownership conflicts, lifecycle asymmetry, stale
state, conditional-trait transitions, modules issuing competing orders — the failure classes Fransbot development
hit most.

**Where it went:** every finding is in `AI_MASTER_PLAN.md` §3 under **"Lifecycle hardening (LC)"** with an id, an
owner and an estimate, and the plan's waves now put LC before further harvesting (the review's suggested order).
The review text itself is the author's own file, [`../FRANSBOT_AI_REVIEW_2026-09-30.md`](../FRANSBOT_AI_REVIEW_2026-09-30.md)
(cameo-mod#665, committed by fransotto) — the single copy; this document holds only our verification, reply and plan.

---

## 1. Verification against the code (master `1ee562ec4` + #664, 2026-09-30)

"Don't trust, verify": each claim was checked against the artifact before it was accepted.

| # | Finding | Verified | Evidence | Status / plan id |
|---|---|---|---|---|
| P0a | Double repair owner (`BuildingRepairBotModule` + `…CA`) | **yes** | both loaded for `genericbot \|\| classicbot`; `RepairBuilding` is a toggle (`RepairableBuilding.RepairBuilding` removes an existing repairer); `RepairActive` only updates in `Tick` | **fix built in #664 (RV1, draft, A/B pending)**: `BaseRepairBotModule` (merged, `Repairers.Contains` + in-flight window) for `genericbot`; classic runs only the CA copy; DESIGN §19.3 |
| P0b | `CaptureManagerBotModuleCA` and `CncEngineerBotModule` both select idle engineers | **yes** | both loaded for `genericbot && !easiestbot`; overlapping engineer lists; `ai.yaml` comment says *"whichever orders first wins — no double-assignment"*; `ModularBot.Tick` runs every module's `BotTick` **before** issuing queued orders and issues only `ceil(n / MinOrderQuotientPerTick)` per tick, so both can see the same engineer idle and both queue orders | **LC1** (lease contract) + **ENG** (merge the two, DESIGN §19.3) |
| P0 | `Actor.IsIdle` is not an ownership primitive | **yes** (follows from P0b) | same | **LC1** |
| P1a | EX-3: provider site vs the manager's own `checkspot` | **yes** | `McvExpansionManagerBotModule.ChooseMcvDeployLocation`: the provider replaces `expandCenter`, but `FindBadDeploySpot(bc.HasValue ? null : checkspot)` records the manager's internal spot; `activeMCVs[mcv] = checkloc` likewise; `ExpansionPlannerBotModule.McvSite` ranks by value × safety / straight-line distance with no locomotor check, and gets no rejection signal; `DriveMcvSite: true` is live on master | **LC3** (Cameo side now: path check + park after a timeout; engine feedback later) |
| P1b | `CratePickupBotModule.alreadyPursuitCrates` is never cleared | **yes** | `Add` at line 125, no `Remove` anywhere; disposed crates stay referenced | **LC2** |
| P1c | Conditionally enabled traits cached while disabled | **yes (class)** | `SiegeEvaluatorBotModule` fix present (re-resolves when empty or a cached manager is disabled) | **LC4** (sweep for the same pattern everywhere) |
| P1d | Fog honesty not end-to-end | **partly — two are ruled exceptions** | `CaptureManagerBotModuleCA.CheckCaptureTargetsForVisibility: false`, its `SafePath` scans enemies without a visibility check, `CratePickupBotModule.CheckTargetsForVisibility: false` — **all three are inside the maintainer's DESIGN §19.5 ruling** (the capture manager routes engineers around the army; a bot that lost its MCV finds a crate anywhere). `audit_fog_honesty` is a count ratchet, as stated | exceptions ruled; **LC6** adds semantic fog canaries for everything else; the audit now also counts `ActorsWithTrait` and fails on a visibility switch outside the two exceptions |
| P1e | Ownership/lifecycle invariants | adopted | the local fixes cited (stuck-kick return, save/load reconcile, scout relinquish, beacon return) exist | **LC5** (watchdog) |
| P2 | A/B runs need an immutable fingerprint | **yes** | league-3: the main-checkout auto-sync landed #656's yaml under pre-#656 DLLs, 15 matches died with `Cannot locate type` (EMBER, LESSONS_LEARNED 2026-09-30); the harness re-reads `ai.yaml` per match; one smoke match stalled with no cause recorded | **LC7** |
| + | *"Whether a failed execution writes its outcome back to the strategic layer"* — added in the author's committed text, not in the draft first relayed | adopted | EX-3 is the measured case (the MCV manager records its own `checkspot`); CA-2c siege failure memory is the working pattern | **LC8** |
| + | "SiegeEvaluator advises, the squad state machine orders" as the pattern | agreed | `SiegeEvaluatorBotModule` → `GroundUnitsAttackMoveStateCA` | used as the LC1 / ENG design pattern |

**Two further duplicates found while verifying** (DESIGN §19.3): `SupportPowerBotModule` + `SupportPowerBotASModule`
on every bot (**RV2**), and `BevManagerBotModule` vs `McvExpansionManagerBotModule`: every `McvTypes` vehicle — Japan's
nanocores included — goes through the expansion-site logic, which deploys away from existing yards, and since EX-3 to
a far field; BevManager's job is to deploy such base-building vehicles next to the base (**BEV**).

---

## 2. Reply to the reviewer

> Thank you — this is exactly the kind of review we needed, from the person who has already hit these bugs.
>
> **Everything you flagged checks out in the code**, and it is now in our plan (`AI_MASTER_PLAN.md` §3, the new
> "Lifecycle hardening" block), with your order of work adopted: hardening lands before we accelerate harvesting.
>
> * **Double repair owner:** fixed in #664, pending its A/B. The two modules are merged into one owner that reads
>   `RepairableBuilding.Repairers` instead of `RepairActive` and remembers orders still in flight, so it can never
>   send the toggle that switches a repair off. The maintainer also made "one module per decision" binding
>   (DESIGN §19.3): duplicates from any parent are merged, never run side by side, and a new audit fails when a
>   merged module's parent file changes, so upstream fixes get ported.
> * **Engineers / `IsIdle`:** agreed, it is a live duplicate and the yaml comment is wrong. We are building the lease
>   you describe (`ActorID → owner, purpose, acquired tick, expiry`; `TryClaim` / `Release` / `IsClaimedByOther`) as a
>   small common contract, first for engineers, capture, scouts, beacons and crates, and merging the two engineer
>   modules on top of it.
> * **EX-3:** confirmed exactly as you describe — the manager records its own `checkspot`, the planner never hears the
>   rejection, and the same unreachable field comes back. Immediate fix: the planner checks the MCV's locomotor path
>   and parks a field it keeps handing out without a yard appearing. Then the candidate object with
>   accepted / unreachable / undeployable / reserved feedback, through the engine hook. "Not land-reachable" will be
>   kept as its own class, for the transport expansion we still want to harvest from Fransbot.
> * **Crate reservation:** confirmed (never cleared); it becomes `crate → collector + tick` with the release rules you list.
> * **Conditional-trait caches:** sweeping for the SiegeEvaluator pattern across the stack.
> * **Fog:** two of your three examples are deliberate — the maintainer ruled the capture manager (routing engineers
>   around the army) and MCV-recovery crate pickup the only modules allowed to see through fog (DESIGN §19.5); the
>   `SafePath` scan belongs to the first. Everything else must be honest, and we agree a count ratchet is not proof:
>   we will add your fog canaries. (The ratchet also now counts `ActorsWithTrait`, which it had missed.)
> * **Ownership watchdog and A/B fingerprinting:** adopted as written. Today's session illustrated the second one: a
>   yaml edit landed while a batch was running from the same checkout.
>
> If Fransbot already has a lease/claim implementation or an ownership watchdog you are happy to share, we would
> rather harvest it than reinvent it (with the GPLv3 header and a "Ported from" line, as for the other modules).

---

## 3. The review text

The author's committed version lives at [`../FRANSBOT_AI_REVIEW_2026-09-30.md`](../FRANSBOT_AI_REVIEW_2026-09-30.md)
(cameo-mod#665). It differs from the draft first relayed on 2026-09-30 in two places: the heading "Things Cameo is
doing very well", and a "Main takeaway" section whose list of boundary bugs adds *"whether a failed execution
writes its outcome back to the strategic layer"* (→ LC8). Read that file for the review; do not copy it here again.

---

## 4. Second verification and follow-ups (2026-09-30, afternoon)

* **NOVA re-verified every claim independently** (17 rows, fleet note `VERIFY_2026-09-30_nova_fransotto_review_claims.md`,
  cross-checked by EMBER): all hold. Three findings the review did not list, each re-checked by the coordinator
  against the code:
  1. **28 `IgnoreVisibility: true` support-power decisions** in `ai.yaml`; `SupportPowerBotASModule.cs:138` accepts
     `IgnoreVisibility || CanBeViewedByPlayer`, so unseen enemies attract strikes. EMBER's LC6 ratchet now counts
     them (56 resolved nodes). → **RV2** scope: the merged owner targets seen or remembered actors for `genericbot`.
  2. **`ResourceMapBotModule.cs:186`** (engine) counts enemies per resource field through fog; the engine MCV manager
     scores expansion threat from those counts (our planner already uses remembered threat). → **LC9**.
  3. `CncEngineerBotModule` enables only bridge-hut repair in `ai.yaml`, so the live P0b race is capture vs bridge
     repair. → fixed by **ENG** (#673).
* **Maintainer ruling:** *"The engineer module can be omniscient as a whole."* (DESIGN §19.5; `EngineerBotModule`.)
* **Mission cards.** In conversation afterwards fransotto described Fransbot's move from bids to mission cards
  (`MatchId → MissionId → AttemptId`, dormant missions, feedback to the General, a local experience archive) and
  proposed sharing neutral infrastructure. Cameo's answer and the shared-format offer:
  [`AI_MISSION_CARDS.md`](AI_MISSION_CARDS.md) (plan rows MC1–MC3, on LC8).
