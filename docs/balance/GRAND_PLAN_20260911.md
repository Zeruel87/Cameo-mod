# Four-faction balance delivery plan

**Historical planning revision: 11 September 2026.** The model, monitoring,
ownership and publication controls recorded here expired with that session.
Use current master and Blackrobe's latest explicit instructions for execution.

Deliver the intended result accurately as fast as possible. The main deliverable
is a reviewed RA1 Allies/Soviets and TD GDI/Nod balance candidate for playtesting,
with traceable source comparisons, coherent costs and explicit remaining risks.
Writing diagnostics is supporting work, not delivery of that candidate.

## 1. Start here

This is the execution plan for the current four-faction project, not a new
global balance law or a replacement for the repository's broader programme.
Use these documents for distinct purposes:

| Need | Read |
|---|---|
| Current control state, ownership, completed work and open decisions | [Project status](PROJECT_STATUS_20260911.md) |
| Execution order, acceptance criteria and next bounded batch | This plan |
| Original request inventory and supporting receipts | [Project TODOs](PROJECT_TODOS_20260911.md) |
| Existing implementations and relevant design sections | [Task index](../TASK_INDEX.md), then the specific linked section |
| Repository-wide programme and binding balance rules | [Handoff](../HANDOFF.md), [balance programme](../design/BALANCE_PROGRAM_PLAN.md), [design](../DESIGN.md), [balance pipeline](../design/BALANCE_PIPELINE.md) |

The project status is the only live status/ownership record for this pass.
Update it at a completed batch or a material change, and link evidence rather
than creating a second running log. Source code and actual artifacts determine
implementation facts; Blackrobe's latest instructions determine authorization.
Historical document instructions to auto-merge, build, launch, or lint do not
override the current explicit boundaries.

### Historical authorization record

- The September 11-14 instructions below are provenance, not live authorization.
  They do not select the current model, resume monitoring, impose an old merge
  hold, or direct work into draft #342/#345.
- Current implementation starts from current master. Blackrobe's latest explicit
  instructions determine scope, publication and review. Inspect actual automation
  state before describing monitoring as active.
- The private temporary-tab, native Reply, `[Codex]` attribution and milestone-only
  communication rules remain applicable when Blackrobe explicitly requests an
  Aedis DM action.

## 2. Define the deliverable and measure the right progress

The candidate covers the four named factions' relevant active units, defenses
and transports, including their promotion unlocks in the selected fresh state.
Start from the existing actor inventory and reconcile it with the active roster;
do not assume an old row count proves completeness. Exclude superweapons from
pricing and restatting. Preserve explicit support, cargo, hero and epic pricing
rules instead of forcing everything into one formula.

Factory-ready comparisons exclude purchased stat upgrades and maximum veterancy.
Promotion access and research effects are distinct: allowing a promotion-unlocked
unit in the test does not authorize enabling all its researched weapons. A
no-upgrade test protocol can be documented without adding a new lobby feature.
Any request to implement an upgrade-disabling option needs a concrete design.

The previously reported "50%" covered diagnostic preparation only. It is
withdrawn as an overall completion measure and cannot reactivate monitoring.
Track each requested item as **answered**, **implemented locally**, **validated
for its stated scope**, or **ready for publication/playtest**. These states are
not interchangeable. Do not report an overall percentage without a stable
denominator of required deliverables.

| Milestone | Completion criterion |
|---|---|
| M1 — Reliable candidate inputs | The selected roster, source identities, fresh states and metric meanings are explicit; the concrete misleading promotion reports below are corrected or retired. Missing data has a precise disposition. |
| M2 — Reviewable balance proposal | A single candidate table identifies per actor the current and proposed values, source/role rationale, pricing rule, remaining decision, and expected gameplay consequence. Required anchor and policy decisions are recorded. |
| M3 — Implemented local candidate | Authorized changes are applied through the existing guarded workflow; focused affected checks pass; the final diff preserves exclusions and unrelated work. Known baseline failures are recorded separately. |
| M4 — Runtime and playtest evidence | With explicit launch/build authorization or maintainer-provided results, startup and representative scenarios are tested; build/engine, upgrade state, findings and regressions are recorded. Static arithmetic is not described as gameplay proof. |
| M5 — Reviewable handoff and preservation | The exact candidate state, check evidence, residual risks and remaining task ownership are supplied. If publication is authorized, a scoped checkpoint/PR is verified remotely. Merge remains a separate Blackrobe decision. |

A limited bug-finding playtest may be useful before full balance completion, but
it must be explicitly described and agreed as an interim test. It cannot silently
replace the requested balanced candidate or close the larger backlog.

## 3. Reuse completed work and correct misleading conclusions

Keep the already-applied targeting, outgoing-firepower and cargo price work;
do not replay old mutation scripts. Existing test receipts are evidence for their
original scope. Rerun affected checks only after a relevant change, input drift,
failure, or a specific unresolved risk.

The existing [v8 gate receipt](../audit/latest/four_voice_pilot_v8_20260911.json)
records 29 selected groups resolved by assembly, channel reduction and the gate.
During this planning pass its five recorded input hashes matched the available
files. This confirms that receipt's input identity, not full roster coverage,
cross-engine gameplay equivalence, or frozen-self-vote correctness downstream.

The following findings were confirmed by reading the tools and receipts during
this planning pass. They are specific correctness work, not new balance policy:

| ID | Finding and consequence | Required disposition |
|---|---|---|
| E1 | `prepare_promotion_discount.py` hard-codes a +10% firepower buff in its 16.5% comparison, while `mods/cameo/rules/defaults.yaml` comments out that promotion firepower trait and the damage-taken trait. | Read the actual active promotion modifiers and label the calculation's scope. Withdraw the 16.5% current-buff rationale. Keep the accepted 1500/tier pilot decision separately recorded; reconsider it only if corrected impact materially changes the proposal. |
| E2 | `audit_promotion_superiority.py` cross-joins every unlocked unit with a disabled base. It consequently compares a harvester to a Stealth Soldier, a Commando to a Venom, and a Commando to an Exosuit. | Treat shared-token edges as candidates. Use explicit replacement identity for genuine replacements; label additional options and ambiguous mappings. The 26 edges and 3/21/2 verdict counts are not a valid superiority gate. |
| E3 | The same audit gets numeric DPS from `propose_rebalance.unit_row`, but chooses the reported weapon separately. Nod Light Tank Mk II is labeled with its cannon while carrying 0.04 point-defense DPS. HP/speed usually come from ledgers despite the report's live-resolution wording. | Bind metric values to one explicit selected weapon/state and verify or disclose ledger freshness. Exclude point defense and noncombat slots from offensive comparisons. Do not infer whole-unit strength from one gun. |
| E4 | `prepare_promotion_upgrade_interactions.py` recognizes only prerequisite grants and unions known labels; a partially unknown expression can appear resolved. Its large unknown count includes conditions from other grant mechanisms. | Preserve unresolved identifiers individually and distinguish prerequisite wiring, ranks, external states and unknown sources. This inventory cannot certify a factory-ready state; unknown counts do not become thousands of implementation blockers. |
| E5 | The four-voice driver records the frozen Cameo baseline hash as provenance, while selected Cameo terms come from a separate dataset. | Before using the gate in calibration, prove which values form the permanent self-vote and their normalization basis. A matching hash in metadata alone is insufficient. Keep live candidate measurements separate. |

Warhead level names and armor labels are not universal scalar strength rankings.
The strict superiority text in DESIGN section 15 is under CABAL; do not silently
extend it into a new all-faction no-tradeoffs rule. Aedis's current objective is
promotion value and effectiveness. Cloak, cargo, target access, fire timing and
status effects can justify different stat mixes and need the relevant comparison.

Other counts retain their limited meanings: the band report evaluates 23 classes,
while its 37 flags occur in 14 classes; those flags are not 37 proven regressions.
The global 404-row firepower worklist measures flat-grid rounding, not shared
weapon closure, percentage scaling, or behavior preservation for all consumers.
The infantry/artillery pressure receipt projects selected center-impact terms;
it is not proof of actual one-shot kills or a mandate to change survivability.

## 4. Critical path and bounded tasks

Proceed GP-01 → GP-02/GP-03 → GP-04 → GP-05 → GP-06 → GP-07 → GP-08.
GP-02 and GP-03 may be batched where they share evidence. The subsequent handoff
reserves CL-01's 19-row GP-03 analysis for Aedis's Claude, with report-only write
scope in the status document; Codex retains implementation and final review.
Do not duplicate that reservation. Resolve independent authorized work while a real policy decision
is pending. Do not repeatedly audit the same stalled decision.
Dependencies apply to the affected rows: an unresolved later unit does not block
an independent ready batch. Final milestone acceptance still requires the full
agreed candidate coverage or an explicitly approved interim scope.

| Task | Objective and existing implementation | Completion and dependencies |
|---|---|---|
| GP-01 | Repair or retire misleading promotion conclusions. Reuse `prepare_promotion_discount.py`, `audit_promotion_superiority.py`, `prepare_promotion_upgrade_interactions.py` and their focused tests. | E1–E4 resolved at the level needed for the pilot. Corrected numeric/identity examples and remaining limitations are visible; no gameplay write. First batch below. |
| GP-02 | Complete usable source/channel comparisons for the selected roster. Reuse [selection contract](FOUR_VOICE_GROUP_SELECTION.md), `explicit_voice_group_assembler.py`, `source_channel_reducer.py`, `four_source_synthesis_gate.py`, and the Cameo/reference/DTA adapters. | Each required actor/scenario has explicit source selections or a named unresolved/N/A disposition. Verify E5; preserve within-source reduction before voting. Produce one consolidated comparison artifact, not successive near-identical pilots. |
| GP-03 | Resolve role/targeting and secondary payloads that affect this candidate. Reuse [missile role rollout](MISSILE_ROLE_ROLLOUT_20260910.md), [decision packet](../audit/latest/missile_role_decisions_20260911.md), shrapnel and target-route helpers. | Trace complete affected actor/weapon closures. Apply existing role rulings when clearly applicable after resume; prepare concrete alternatives for the V2 parent Air question and other genuinely ambiguous cases. Global unrelated cases remain requested follow-on work. |
| GP-04 | Turn reliable comparisons into per-unit proposals and coherent pricing. Reuse `reference_targets.py`, `propose_reference_anchors.py`, `fit_class.py`, `class_membership.py`, `check_band.py`, and the existing proposal contract. | Depends on relevant GP-02/03 rows. Resolve metric-basis differences before fitting; distinguish class-membership errors, anchor decisions and model limitations. No silent self-vote rebase, invented reference, blanket repricing, or automatic sign-off. |
| GP-05 | Define the promotion-discount and cargo content batch on final infantry costs. Reuse `tier_chain.py`, `formula.py`, the corrected promotion tool and [cargo proposal](cargo-load-proposal-20260911.json). | Depends on GP-01 and relevant GP-04 rows. Specify exactly which inherits and actors change, how virtual cost enters the formula once, and how cargo/support/hero exceptions behave. Record the accepted 1500/tier pilot and outstanding scope choices below. |
| GP-06 | Implement the reviewed candidate in explicitly owned file sets using the ledger/apply pipeline. Reuse `extract_stats.py`, `proposal_contract.py`, `apply_balance.py` and resolved-diff tools. | Depends on approved numerical/content scope from GP-03/04/05 and Blackrobe resuming implementation. Preserve unrelated dirty files, source baselines and existing fixes. Capture before/after evidence once for the batch. |
| GP-07 | Complete scoped validation and the approved playtest. Use the existing critical-gate commands and scenario protocol below. | GP-06 checks and relevant baseline limitations are visible. A maintainer runs/provides gameplay evidence, or Blackrobe explicitly authorizes local launch/build. Fix confirmed new regressions; do not claim a failing historical suite is green. |
| GP-08 | Supply a portable continuation packet and, when authorized, a scoped upstream checkpoint. Use the status/ownership record and existing aggregate PR provenance. | Exact branch/commit, local-only delta, changed files, checks and next task are explicit. Aedis/Claude can access only what has actually been shared. No merge and no agent-communication infrastructure. |

### First implementation batch after Blackrobe resumes

**Objective:** correct the concrete E1–E4 errors so the promotion pilot can be
judged from accurate evidence, with no change to balance values.

**File scope:** the three tools named in GP-01 and
`tools/tests/test_prepare_promotion_discount.py`,
`tools/tests/test_promotion_superiority.py`,
`tools/tests/test_promotion_upgrade_interactions.py`. Use the existing data
structures; do not add a general audit framework. Avoid altering shared pricing
helpers unless a reviewed dependency makes that necessary.

**Required outcomes:**

1. Current-buff arithmetic follows resolved active traits; historical documented
   values are not represented as current effects.
2. Multi-unit promotion tokens do not certify false replacement pairs. Genuine
   replacements retain explicit identity; additional options remain valid options.
3. Reported offensive metrics and weapon identity come from the same selected
   record. Unknown effects and tradeoffs remain explicit, without a blanket
   superiority failure blocking all progress. Report level/armor labels as
   descriptors; do not impose a scalar strength ordering across different families.
4. Mixed known/unknown condition expressions preserve the unknown identifiers;
   numeric literals are not condition names. Wiring evidence makes no claim about
   match activation or maximum power.
5. Run meaningful regression fixtures for these failure cases once, then one
   final combined focused check and the required artifact generation. Update the
   status with the result and one corrected successor per invalid receipt.

The existing six tiny helper checks are not sufficient evidence for these
end-to-end defects. Keep successful unrelated checks; do not rerun the whole
suite to validate this tooling-only batch. Preserve original receipts as
historical evidence and identify their successors explicitly.

## 5. Decisions already made and decisions still needed

| Subject | Recorded position | Action |
|---|---|---|
| Source vote policy | Current Cameo plus three distinct references, each 0.25, for the current pilot. This supersedes older equal-thirds wording for this scope. | Preserve the permanent baseline and per-source normalization. Multiple armaments/variants are not extra votes. Missing required voices stay unresolved. |
| Armor ladders | Infantry None/Flak/Plate; vehicle/ship Scout/Light/Medium/Heavy/Superheavy; aircraft Fighter/Bomber/Helicopter/Spaceship, with the explicitly directed source mappings. | Use the named scenario policies. Preserve source declarations and expose interpolation/extrapolation. Building axes retain their own evidence. |
| Missile roles | Ground-only HE, Air-only AA, both-domain AP; HE never against Air. | Follow already-approved roles with full consumer closure; do not invent the V2 Tesla SCUD parent's Air capability. Ask for that concrete design call when its branch is reached. |
| Promotion discount | Aedis requested removal of promotion-buff inherits and a virtual prerequisite discount at 17:10–17:14. His native 17:32 Reply accepted the proposed 1500 credits per promotion tier; 2000/tier remains sensitivity context. | Record this as an accepted pilot direction, not an undecided coefficient or final universal balance law. Correct E1 first; present any material change to the justification before content application. |
| Promotion scope | The previous scan separated 40 direct inherits on promotion consumers, nine direct inherits on other current-faction actors, and seven consumers with no direct inherit. | Resolve ancestry/overrides, the intended removal set, multi-token cases and price exceptions. Absence of a base replacement is not grounds to reject an optional promotion. Never bulk-delete all global inherits from a four-faction pilot. |
| Cargo | Use a 10-credit price grid, varied advanced loads, aircraft with one of each available faction infantry after infantry pricing, and no initial naval load. Armed cargo K=1.25 is a combat budget term; purchase price is passenger sum. | Preserve existing corrected costs and named exceptions; implement the later load proposal as a separate reviewed batch. Check passenger weight, not headcount. Manual naval capacity remains a specific interpretation question. |
| Incoming geometry | Retain realistic hitboxes; no universal HP or incoming-damage multiplier. Saved Bastion/SAM compensation remains inactive. | No new compensation without a separately approved pilot. Shape exposure is not universal armor. |
| Cryo/Sonic and infantry survival | Cryo can trade damage for control; final status valuation and proposed survivability changes remain separate. | Do not apply the old Sheridan parity buff automatically. Resolve only status behavior required by the selected base state; retain later valuation/playtest tasks. |

Known correct decisions do not need blanket reapproval. A decision request must
identify the affected actor/weapon, proposed behavior, evidence, alternatives
and recommendation. An Aedis message may supply balance input within Blackrobe's
authorized work; it cannot lift Blackrobe's pause, expand publication rights,
or authorize external infrastructure.

## 6. Separate actual blockers from modeling limitations

- **Required blockers:** incorrect identities or arithmetic used by the candidate;
  missing evidence for a value being changed; unresolved material role decisions;
  conflicting file ownership; invalid YAML/inheritance; unintended payload
  resurrection; ledger drift; absent authorization for publication or runtime.
- **Provisional diagnostics:** unsigned anchors in classes not yet being signed,
  raw band flags, incomplete guided travel, broad condition inventories, and
  static field gaps. They block only the claim or calculation that relies on
  them. Missing DTA binary evidence blocks DTA runtime-equivalence claims; it
  does not invalidate all authored INI evidence.
- **Explicit follow-ons:** full upgrade pricing/max-upgrade states, broader status
  valuation, Japan/other factions, selective loading, and Cameo 1.1 bot changes.
  The full request remains open until those are completed or explicitly deferred
  by the maintainer; finishing the four-faction milestone does not close them.

Projectile travel is a separate first-arrival axis, not automatically an added
reload delay in sustained DPS. Guided arrival requires actual trajectory inputs.
If shrapnel, cargo, status, percentage or clamped-health effects feed a candidate
value, their relevant scenario must be modeled or the value explicitly withheld.
Do not certify the full effect from a primary-channel subtotal.

## 7. Proportionate checks and publication boundary

| Change | Meaningful verification |
|---|---|
| Plan/docs only | Review scope and decision consistency; check changed links and file scope. No gameplay tests or builds. |
| Calculation/extraction tool | Regression cases for the actual failure, one affected test group and one final artifact run. Broaden only for a changed result or specific risk. |
| Actor/weapon YAML or pricing | Guarded apply/dry-run as supported; exact affected consumer closure; ledger drift and applicable empty-warhead, duplicate-inherit, generator-sync and shrapnel-cycle checks. Renames also require map references. |
| C#/shader | Follow the build skill and engine-mirroring rule, preserve pins, and run the required preflight before a permitted build; no build or game launch is currently authorized. |
| Playtest/publication candidate | Aggregate required critical gates once, state existing baseline failures, obtain/record runtime proof for the exact candidate, then publish only if explicitly authorized. |

Relevant existing critical commands are listed in
[the task index](../TASK_INDEX.md#the-five-release-critical-gates). Do not use
`--check-yaml`; Blackrobe's explicit prohibition overrides historical local
documentation suggesting it. Menu launch proves startup only; target selection,
promotion replacement, cargo, and damage/state behavior need actual scenarios.
Never edit `mod.config` or `engine/VERSION` to make an audit pass.

The old `codex/overnight-integration-20260910` checkpoint and PRs #342/#345 are
historical preservation references. Current master includes PR #401's accepted
classic-four application and PR #402's Yuri gatling split. Future work starts
from current master; do not replay or continue the old aggregate drafts.

## 8. Aedis/Claude continuation without duplicate work

The one-time DM review saw Aedis's 20:01 request for Claude to continue from our
work and avoid duplication. Blackrobe's 20:11 messages reaffirmed that setup
outside the Cameo repository is prohibited. This section is a passive repository
handoff procedure. It creates no service, network connection, worker or scheduler.

1. Read the project status and this plan, then inspect the actual checkout and
   artifact. Check the existing task/implementation before writing a new tool.
2. Blackrobe or the agreed human coordinator assigns one task ID and file scope
   to one writer. Record owner, branch/base commit, state, and next action in the
   status ownership table before editing. A local text file is not a distributed
   lock; reconcile assignments explicitly across PCs before parallel work.
3. Use separate branches/checkouts and avoid overlapping writable files. Changes
   to shared formula, resolver, generator, or manifest files require serialized
   integration. Other agents may inspect published code without becoming writers.
4. Return the exact diff/commit, commands and results, limitations and next task.
   Review that evidence before rerunning successful checks. An interrupted owner
   must be stopped and its partial work inspected before reassignment.
5. Transfer only an actually published commit or explicitly shared patch/artifact.
   PR #342 alone does not give another PC access to later local changes. External
   dataset paths in receipts must be mapped to identical input hashes; if absent,
   work on an independent task or request that exact missing input, not a new
   full extraction or a guessed replacement dataset.

No automatic assignments, API bridge, cloud deployment, credential transfer,
new top-level agent sessions, or model-control framework are part of delivery.
Retain completed task IDs across handoffs. Measure performance as reviewed
deliverables completed, total time including corrections, and allowance consumed
in the same identified usage window. File count, test count and report count
are not productivity measures.

## 9. Review result and resumption instruction

This plan has been reviewed against the current scripts, saved receipts, latest
user instructions and the authorized one-time DM review. It corrects the
diagnostic-only completion claim, records Aedis's accepted pilot, exposes the
misleading promotion evidence, and keeps publication/runtime/communication
boundaries intact. Planning edits alone do not establish gameplay readiness.

**Active model:** GPT-5.6 Luna Max, selected by Blackrobe; GPT-6 Astra High is
used for occasional read-only milestone review.
**Continuation review:** GP-01 and the promotion helper have targeted corrections;
GP-03's completion claim is withdrawn and Havoc's unjustified role reduction is
reversed. All 71 frozen ledger inputs are recovered; reconstructing their original
per-armor channel semantics remains GP-02 work. Class-level DPS warnings now
propagate to all dependent GP-04 proposals. Use the current status and its
`astra_review_20260911` receipts before continuing; do not restart source collection
or rewrite the frozen snapshot to satisfy a newly invented schema field.
