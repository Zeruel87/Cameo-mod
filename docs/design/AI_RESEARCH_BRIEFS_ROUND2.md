# AI research round two — differentiated briefs

Owner: `AI_ARCHITECTURE.md` §11. These are the five follow-up requests specified in
`BLACKROBE_ASTRA_BRIEF.md` H.3, not a new architecture or task queue. They have not
been sent to the external services, and no replies are claimed. Phase-one match
logging is implemented; adaptive decisions and episode attribution are not.

## Common response contract

Use the repository revision you inspected and cite exact sources. Separate an
observed implementation, measured result, inference and proposal. State units,
population, missing data and limitations. Do not invent Cameo thresholds, claim
PRs merged without checking, or re-adopt §11.2/§11.4 rejected claims. A useful
answer ends with a smallest falsifiable experiment, not another implementation
handoff. No answer grants permission to change gameplay or synced state.

## Perplexity — published evidence and transfer limits

Question: which published RTS results support comparing fixed versus adaptive
high-level policies with sparse, non-stationary observations, and what does not
transfer to a crossover mod with changing balance?

Already settled: §6.1 separates local reasoning and simulation; §11.3.5 requires
an offline fixed/dynamic comparison before bandits; §11.4 rejects ungrounded
strategy thresholds. Do not repeat the observer-graph answer from round one.

Evidence: primary papers with experimental setting, comparator, sample size,
uncertainty, compute budget and failure cases. Distinguish opponent modelling,
policy selection and direct tactical control. Identify human-versus-bot transfer
limitations separately from bot-versus-bot results.

Falsification: a recommendation fails if it depends on full-state observations,
frozen balance or training volume unavailable to Cameo without acknowledging it.
Propose an evaluation that could show no benefit over fixed personalities.

## Grok — narrowly scoped code archaeology

Question: in CA, AS, Mental Omega, Shattered Paradise and Generals Alpha, which
mechanisms actually coordinate competing production, squad and support-power
decisions, and what happens when the active personality changes?

Already settled: §1.6 verified CN's direct condition mutation and stale-profile
cache issue; it did not validate Cameo's order bridge. §11.2 rejects that inference.
Do not revisit the same CN constants or call a strategy label a coordinating API.

Evidence: repository/revision, relevant functions or configuration blocks, call
chain, ownership lifetime, refresh trigger and fallback. If a title's source is
not available, say so; engine differences are not interchangeable APIs.

Falsification: trace a personality switch or actor-order collision. A claimed
single owner is disproved by two enabled writers without a reservation mechanism.
Deliver an implementation comparison, not new Cameo code or fetched game assets.

## ChatGPT — small-sample decision mathematics

Question: what experiment and estimator can compare fixed personalities without
mistaking faction/map/team strength or unequal match coverage for policy quality?
What extra observations are essential before estimating counter-demand or episodes?

Already settled: §6.2a only records completed-world aggregate outcomes; it cannot
attribute damage pairwise or identify composition episodes. §11.3.1 bounds future
features; §11.3.5 requires comparison before a bandit. No fixed detection constants.

Evidence: explicit estimand, stratification/paired-seed design, treatment of
duplicates, censoring/abandonment, uncertainty and changing rulesets. Work a small
synthetic example, label it synthetic, and show sensitivity to a single outlier.

Falsification: the estimator should refuse or widen uncertainty when coverage is
insufficient or incompatible. Demonstrate a confounded example where pooled win
rates reverse the within-matchup conclusion. Do not produce deployment weights.

## Copilot — desync and lifecycle feasibility

Question: what is the minimal replay-safe implementation and test plan for the
future personality controller's token ownership, including the initial random
token, save/load and disabled-trait transitions?

Already settled: §1.1 local bot reasoning may only issue orders; §10.4 rejects
GrantConditionOnOrders as the controller because ordinary orders revoke it.
§11.2 rejects citing CN as proof of an order bridge. Phase one changes no behavior.

Evidence: pinned OpenRA call sites, interfaces, sync hashing and serialization
paths; an explicit lifecycle sequence and failure injection for duplicate, stale,
unauthorized and replayed requests. Include what must be identical across clients.

Falsification: one divergent token, missed save restoration, stale enabled-module
reference or direct synced mutation from an unsynced callback defeats the design.
Do not implement the controller until the initial-token ownership issue is closed.

## Gemini — ContentPack migration with observable equivalence

Question: how can the first faction-owned AI dictionary slice move into an active
ContentPack without changing effective precedence, selection order or references?

Already settled: §1.2 and §2 distinguish merging data from multi-instance traits;
§1.3 rejects duplicating singleton consumers; §1.4 already supplies condition-gated
prerequisites. Do not invent a new aggregator or assume the historical pack count.

Evidence: current manifest include order, one exact before/after merged example,
order-sensitive consumers and cross-pack references. Identify which equivalence
is required: key/value equality is not sequence equality. Use active includes only.

Falsification: a changed weighted/random choice ordering, duplicate singleton,
missing reference when a pack is absent, or different fallback blocks the pilot.
Deliver one reversible migration experiment and its checks, not a roster-wide sweep.

## Reconciliation ledger

All five lanes are **awaiting external responses**. When a reply arrives, add its
source/revision and outcome to `AI_ARCHITECTURE.md` §11: verified, rejected with
counter-evidence, or unresolved with a discriminating test. Keep conflicting
answers separate. Brief authorship is not a delivered research result, and no
weighted average of AI opinions substitutes for evidence.
