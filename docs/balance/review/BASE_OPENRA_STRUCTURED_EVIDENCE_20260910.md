# Base OpenRA structured evidence migration

## Reopened technical follow-up result

The combined affected run covered55 modules/612 tests:4 failures,5 errors,
zero skips,57.68% peak RAM. Six failure/error signatures came from three exact
ownership intersections in historical test helpers. After those fixes, all25
tests in the four affected modules pass. The three genuine Sonic paid-upgrade
damage failures remain; no synthetic green full-suite result is claimed.

All17 stale historical/readiness/exclusion failure identities are addressed.
Combined33 ledgers have zero drift, all22 registry claims match the completed
measurements after prose co-update, and doc-health passes. Raw missile/release
gates remain unchanged and failing. Independent scoped review found no remaining
implementation issue. This technical follow-up changes no live YAML or prices.
Earlier full-suite receipts below remain historical. Keep drafts; HOLD merges.

## Final integration receipt — 10 September 2026

This receipt supersedes source-stage pending notes below; the source-specific
measurements remain separate from this combined result. The full combined run
executed2,033 tests:20 failures,8 errors,64 skips. All2,036 discovered identities
were accounted for, including3 class-skipped methods. The20 prior R18 failure/error
identities remained. Eight new historical-test compatibility failures were then
corrected, and all25 affected tests passed. The original full result remains red;
no second full run or synthetic green result is claimed.

The combined candidate has2,969 resolved weapons and33 zero-drift ledgers.
Independent final review passed86 focused tests and approved scoped draft
publication, with HOLD for merges. Peak full-suite RAM57.40%; no95% guard stop.
The new raw missile-role gate (R3=52/47,R4=55/50) and worsened release-name coverage
(D4=562/335) remain explicit. Five previous documentation claim mismatches remain
after the two new factual counters were co-updated; combined doc_health passes.
Source/state/role decisions listed below are not declared complete by publication.

This completes raw structured transport for four existing reference populations,
not factory-ready/max-upgrade certification or applied game balance. No source
executable, game configuration, price, anchor or handwritten assignment was changed.
Other OpenRA peers remain unmigrated; this is not whole-Doc5 completion.

## Source and population comparison

All four exports read clean OpenRA commit
`bbd36d9e6a2d7f0d3b24f102858af6dc8caf8a78` (24 July 2026), following each selected
mod's active manifest. The source and engine source code are in the same pinned
repository; no separate SDK engine pin was declared. This identifies source code,
not a tested binary or certification of runtime applicability. The older Markdown
records checkout paths but no revision; no claim is made that this reconstructs
its original checkout. Every actually read source input was hashed before/after.

| Existing source | All rows before â†’ after | Armed incomplete rows | Unchanged source inputs |
|---|---:|---:|---:|
| OpenRA Tiberian Dawn | 48 â†’ 48 | 25 | 77 |
| OpenRA Red Alert | 88 â†’ 88 | 40 | 102 |
| OpenRA Tiberian Sun | 74 â†’ 70 | 30 | 50 |
| OpenRA Dune 2000 | 56 â†’ 50 | 27 | 63 |

Counts compare actual consumer rows, including the separate hero lane, not old
Markdown section headlines. Every retained row has exactly the same HP, cost,
speed and normalized type. No actors were added. Nine removed definitions resolve
`Buildable/Prerequisites: ~disabled` in this source; one does not exist:

- TS: GACNST, GASAND and ORCATRAN are disabled; GAFSDF is absent.
- D2k: conyard.atreides, conyard.harkonnen, conyard.ordos, fremen, nsfremen and
  saboteur are disabled. This does not mean they cannot occur through other game
  mechanisms; it means they fail the extractor's existing purchase-population rule.

The new JSONL files retain all resolved armaments, their raw gates/modifiers and
production declarations. All 122 armed records remain incomplete; neither first-slot
rates nor a sum of mutually exclusive weapons becomes certified DPS. The 134 unarmed
rows have no weapon metrics. The compatibility consumer labels their absent weapon
status legacy-unassessed; this does not conceal an armed legacy estimate.

## Consumer impact and validation

The explicit index replaces each old Markdown slice instead of adding a second copy.
All other source rows compare exactly. Ordinary rows decrease from 4,379 to 4,369;
incomplete evidence increases from 310 to 428, legacy-unassessed decreases from
4,023 to 3,895, and nominal-direct stays 46. The extra 118 incomplete ordinary
rows plus four armed hero rows have their weapon votes withheld. Their chassis
values remain available. Generated reference assignments and targets can change
from this population/evidence correction and must be regenerated and reviewed;
old input-fingerprinted proposals are not valid for the new index.

Four new installed-corpus regressions check exact source identity/input counts,
all retained chassis values, the exact ten removals, unchanged other-source rows,
no double counting, and ordinary/hero weapon withholding. The 51-test focused
corpus/consumer/DTA group passes with one optional external-baseline class skipped.
That skip is not a claim of new real-source DTA validation. The initial test-only
assumption that unarmed exports have a `weapon_evidence` key was corrected to honor
the existing absent-field contract. No extractor behavior changed.

Final combined audits/full-suite validation are performed by the integration task;
they are not claimed complete by this source report. No game run is needed for this
metadata/consumer change.

## Bounded rank-state evaluation

`tools/reference/extract_peer_rank_states.py` now evaluates the rank axis from the
same clean co-pinned source, rather than leaving every rank expression raw. Its
separate `base_rank_bbd36d9e.json` snapshot is deliberately not selected by the
consumer index and cannot supply a DPS vote. The exporter hashes 304 source files,
including the twelve inspected engine files for experience, condition counts,
conditional grants/traits, expressions, armaments/ammo and firepower/reload/range modifiers. Source
revision, dirty state, input inventory and hashes are checked across the read.

| Mod | Rank axis evaluated | Production-rank scenario required | No single rank track |
|---|---:|---:|---:|
| TD | 20 | 0 | 28 |
| RA | 17 | 22 | 49 |
| TS | 17 | 7 | 46 |
| D2k | 26 | 0 | 24 |

The 80 evaluated rows have separate unranked and maximum-rank views. Conditions
are cumulative token counts, not booleans: TD E1 has three `rank-veteran` tokens
at maximum, which enables `rank-elite`. Its older 125% rank modifiers are disabled;
only its 150% elite modifier applies. The result is not 125% Ã— 125% Ã— 150%.
No combined modifier product or whole-unit DPS is calculated, avoiding premature
claims about integer rounding, ammo, target armor or additional damage channels.

Only single-token/count comparisons and negation of a known token are evaluated; unsupported expressions and
non-rank conditions remain unknown. Permanent/history-dependent grants, ambiguous
rank providers and production-level overrides are refused. The 29 production-rank
rows need explicit player-prerequisite context; their initial rank is not guessed.
The 147 rows without one rank track are not incorrectly certified as fully
unmodified. Even evaluated rows retain both whole-unit certification flags as
`none`. The scenario excludes inherited experience/external rank grants and does
not assert purchase availability, complete upgrade compatibility or reachability
of maximum rank in a particular match.

Seventeen focused rank tests pass, covering token counts, exclusive rank modifiers,
unknown conditions, invalid tracks, permanent/duplicate/external grants, source
pin/dirty refusals, armament gates/range, creation ammo and the installed snapshot. The additional 146-test reference
target/assignment/Japan/holdout/export group passes. No game or full-suite rerun
was used for these focused checks.

The same projection now records individual armament activation gates and range
modifiers, including actors without a rank track. Across 155 armaments, 126 gates
are unconditionally open. The pinned AmmoPool creation rule proves the named
condition count starts at configured InitialAmmo or defaults to full Ammo; this
resolves 13 additional initial gates (139 known open, 16 still unknown). Explicit
zero initial ammo is retained, above-maximum/negative values follow the inspected
engine's full-pool fallback, and other providers of the same condition refuse the
count. Ammo at maximum rank remains unknown because it depends on combat history.
These are trait gates, not a claim that a weapon can hit a target immediately:
attack-trait state, facing, target validity and cadence still matter. Remaining
gate declarations include rank alternatives, deployment, reload-route conditions,
three tower upgrades and submergence; none is defaulted false.

The requested broader factory/max comparison still needs source/scenario policy
for non-rank states. For example, TD E1's hospital and biolab effects depend on
player prerequisites and terrain. "No purchased upgrades" alone does not specify
those conditions or combat history. The supported rank, initial-ammo and raw
activation-gate contract is complete; it does not turn those missing assumptions
into a falsely certified whole-unit reference.

## Remaining reference work â€” do not mark complete

### Explicit non-rank scenario continuation

The continuation adds `tools/reference/peer_state_scenarios.py`, a separate
settled-state evaluator for `GrantConditionOnPrerequisite`,
`GrantConditionOnTerrain` and non-permanent derived `GrantCondition` chains.
It inspects/hashes the co-pinned prerequisite manager and TechTree as well as
both condition traits. Inputs are explicit resolved player prerequisite keys
and effective in-map terrain after the terrain trait has ticked. Omitted axes
remain unknown; an explicitly empty prerequisite list is distinct from omission.
This is a projection given those inputs, not proof that the owner can acquire
them, reach that terrain, or purchase the actor. Empty prerequisite declarations
do not register with the source manager and grant zero tokens.

Supported conjunctions/disjunctions preserve source precedence. Unknown terms,
unsupported expressions, other/duplicate providers, permanent grants and cyclic
dependencies remain withheld. A supported rank-axis view may be selected, but
creation ammo is not carried into this settled view. No modifier product or DPS
is calculated and scenario outputs are never summed.

The separate, non-indexed `base_scenarios_bbd36d9e.json` contains 15 reproducible
views supplied by `tools/tests/fixtures/base_peer_scenarios.json`. The first four
cross explicit no-prerequisites/`bio` with Clear/Tiberium for unranked TD E1:
only `bio` + Tiberium activates `hazmatsuits`, and unspecified damage remains unknown.
Two further E1 hospital scenarios distinguish Heavy from Undamaged. Both whole-unit
certification flags remain `none`; these are diagnostic scenarios, not chosen
factory/max policy. All 315 hashed inputs, including 23 engine files, were unchanged.

| Existing axis | Implemented explicit input | Exact boundary retained |
|---|---|---|
| Damage/hospital | One current source DamageState; duplicate known damage grants sum token counts | Permanent damage grants require prior damage history |
| Deployment | Exact trait key mapped to completed Deployed or Undeployed | In-progress animation/order states are refused; no claim that terrain, facing or pause permits deployment |
| Tower upgrades | Exact Pluggable socket mapped to one accepted active plug or explicit empty | Four TS GACTWR views enable zero or exactly one of three weapons; acquisition requirements are separate |
| Submergence | Post-CenterPositionChanged event below transition threshold on subterranean layer, or above threshold off-layer | Layer alone, equality, and mixed layer/depth combinations retain history and are refused |
| Attack/reload route | Explicit fresh actor with no attacks | TD APC's two reload gates are open; subsequent cooldown/shot/target history is not guessed |
| Rank combination | Optional already-supported rank axis; no fresh-ammo carryover | Earned maximum rank cannot be combined with fresh-no-attacks; production-rank holds persist |

The submergence boundary follows the inspected source's strict comparisons, not
an assumed layer flag. The deploy projection uses completed token endpoints;
source transition state labels are not treated as sufficient token proof. The
plug projection follows EnablePlug's revoke-old/grant-new behavior and rejects
multiple selected upgrades in one socket. Dot-containing tower conditions are
supported by the separate bounded expression parser. Unsupported or ambiguous
providers remain visible in each row's holds.

Reproduction reads the clean pinned source and compares full JSON objects for
both installed snapshots: the original 304-input rank snapshot and the new
315-input scenario snapshot reproduce exactly. CLI reproduction of the latter:

```text
python tools/reference/peer_state_scenarios.py --source C:/Users/Blackrobe/repo/OpenRA-upstream --scenarios tools/tests/fixtures/base_peer_scenarios.json --output <new-external-json-path>
```

Focused validation: the initial peer group passed 95 tests; after expanding the
scenario endpoints, the affected rank/scenario group passed all 31 tests (17 rank,
14 scenario). Base-corpus tests passed 4/4; the reference-target/assignment/holdout/
Japan/DTA group passed 144 tests with one optional external-baseline skip. Source
`extract_stats.py --check` checked all 33 ledgers with zero drift; no ledger rewrite
was needed. `git diff --check` passed. No source full suite, game or build was run.
The integration task owns final combined audit/full-suite evidence.

### Source-specific diagnostic regeneration

The source339 checkout also regenerated the retained diagnostic assignment,
distribution/signature and synthesis outputs. These had stale data from earlier
source batches as well as the new base corpus; the entire delta is **not**
attributed to the base migration. The commands, in this exact source checkout:

```text
python tools/balance/assign_references.py --write
python tools/balance/reference_distribution.py
python tools/balance/assign_references.py --review scout
python tools/balance/build_reference_report.py --faction td_gdi td_nod ra1_allies ra1_soviets --out reference-continuation-source339.html
```

Tracked outputs are `docs/balance/derived/reference_assignment.json`,
`reference_distributions.json`, `reference_signatures.json`,
`docs/balance/REFERENCE_SYNTHESIS_REPORT.md` and `docs/balance/review/scout_references.md`.
The HTML is local diagnostic evidence, not publication payload. No combined
checkout output was copied into this source branch. The HTML reports 66 originals,
74 expansions, 261 references and three originals under three sources.

Against source339 HEAD, assignments change from 356 to 360 actors and 904 to 913
source slots; 145 actors have changed entries. The chassis-only list is unchanged.
Distribution/signature changes also include older CA/DTA and other source updates
and stale Cameo diagnostic inputs. These are regenerated proposals, not manual
assignment approval or applied price/HP/gameplay changes; the 33 numeric ledgers
still have zero drift.

Regeneration exposed two review-writer defects: explicit overrides/id promotions
can lack numerical match scores, and global overrides can survive a class-filtered
assignment call. Missing scores now display an em dash; class summaries count only
the members actually displayed. The resulting scout sheet has 33 members and nine
assigned members, all nine with at least two name-backed references. Neither fix
changes matching rules or stored assignments. The post-regeneration assignment/
target/holdout group passes 53 tests; the focused missing-score/outside-class
override regression passes after both report-only fixes.

At the earlier publication checkpoint, the affected source documentation audits were run against the regenerated
diagnostics. `audit_doc_health.py` exits 0: 293 documents, zero findings in D1–D8.
`audit_doc_claims.py` exits 1: 22 claims and five mismatches, with exactly the same
IDs and measured values as the previously tracked source audit:
`multi_main_fired_weapons` 184→122; `meters_filling_before_death` 269→282;
`w24_multi_main_fed` 429→425; `physical_state_fired_weapons` 534→531;
`unconverted_template_inheritors` 1596→1592. Those pre-existing numeric-policy
discrepancies were not rewritten. No new report-integrity finding was identified.
Raw stdout and empty stderr are retained locally as
`reference-continuation-doc-claims.md` / `.err` and
`reference-continuation-doc-health.md` / `.err`; they are source339 evidence,
not a claim that the full audit suite passes.

Remaining certification inputs are concrete: owner-resolved prerequisite keys,
production level, selected compatible socket/deployment state, effective terrain,
damage state and (for arbitrary historical states) prior grants/attacks/targets,
reload ticks and movement/depth events. No accepted factory/max scenario supplies
these choices. The safe alternative implemented here is separate explicit endpoint
projections; it does not approve any endpoint as the reference policy. Reconstructing
unknown histories or choosing all upgrades together would invent unavailable facts.
This is not an assertion that finite event histories cannot be evaluated. They
could support a further source-specific replay evaluator once an actual requested
history and observation point are supplied. No such history is supplied by the
existing factory/max request; inventing one would choose the reference scenario.
The listed compatible non-rank endpoints have executable input handling and
focused validation, rather than being deferred solely because a scenario decision
is missing. A general event-history simulator is not delivered or claimed complete.

- **Factory/max-state evaluation:** raw declarations and strict transport are done
  for the selected sources. The explicit endpoint evaluator above is implemented for
  prerequisite/terrain/derived grants, damage, deployment, tower selections,
  submergence and fresh attack/reload conditions. This closes the enumerated
  compatible non-rank endpoint engineering from the handoff. Certification remains
  pending the chosen factory/max scenario; arbitrary transitions and permanent
  grants are not reconstructed from an unspecified history. The rank-axis
  evaluator retains its documented production-level holds and does not certify
  a complete factory state. Base OpenRA's source and inspected engine semantics
  are co-pinned and were used for the completed endpoint implementation. CA's
  historical engine revision and exact player scenario still need confirmation;
  its moving branch name alone cannot certify a historical state. Do not assume
  every condition false or every factory-created actor unranked.
- **Naval assignments:** eligibility/collision/role review is done in the integration
  report `TD_NAVAL_REFERENCE_REVIEW_20260910.md`. Surface missile boats versus
  ballistic submarines, hovercraft versus transport submarines, carrier launchers
  versus their aircraft, and reuse of CA CA already assigned to the Allied Cruiser
  remain explicit role/evidence holds. Automatic proposals are not approval.
- **RA3, Emperor and OpenDUNE:** pinned raw extraction is complete as documented in
  [the collection guide](REFERENCE_COLLECTION_GUIDE_20260909.md). Final-retail
  applicability and unsupported weapon semantics are not certified. The Emperor
  example Rules.txt version is not proof of a retail patch; RA3 fragment/dependency
  diagnostics are not complete combat values; OpenDUNE static tables are not proof
  of per-scenario availability. Do not fabricate missing values.
- **Spice Wars:** no versioned primary full-stat dataset is available from the
  checked local library/official release sources. Patch deltas cannot reconstruct
  the base roster. Needs version-identified source files; no purchase/install is
  authorized by this extraction task.
- **Joint stats/price fit:** stays unapplied until source eligibility, class/role
  assignments and complete weapon operation are settled. Missing inputs are not
  zeros, and a small formula delta is not a gameplay-balance verdict.

The final status is completed raw collection and validated, bounded endpoint
engineering, with whole-unit certification and the listed source/role decisions
still pending. The report does not certify arbitrary historical states, all
upgrades, retail applicability, naval assignments or a joint stat/price fit.

## Reopened technical corrections — source339 after `8b4f9d465`

The anchor-membership failure represented an unlanded role, not a reason to change
live gameplay. GDI APC still inherits SupportVehicle and belongs to `support`;
the ruled `armed_troop_transport` class has no members. Its anchor entry now records
that pending membership explicitly, without changing any anchor spec or price.
Readiness exports actual/declared class, member count, pending/mismatch/missing
status and `membership_ready`. The pending APC remains false. Tests check that
exact declaration, zero current transport members, no sign-off, and failure to
clear any undeclared mismatch or missing actor. Other anchors still must match.

The T17 test wrongly required today's ChemRockets to retain an old three-main
weapon structure. A synthetic three-part example now checks the exact numerator
and denominator exclusions, while a separate live assertion pins the approved
single 36000 Chemical main. This investigation exposed a real denominator bug:
`DamagesConcrete: 100` was being counted as target HP damage, and percentage
exclusion depended on the arbitrary instance tag instead of runtime type.

Both `weapon_bindings` and `damage_split` now share the same flat-health predicate:
positive AreaDamage, SpreadDamage or TargetDamage, excluding ally-only twins.
Concrete-slab, integrity, open-topped, percentage and unknown damage types cannot
be summed into this denominator. Tests include renamed percentage types,
misleading flat-warhead names and nonhealth types. ChemRockets' nominal health
split is consequently 36000/36000, rather than 36100/36000. No live YAML, engine,
actor HP, cost or selected reference assignment was changed by these corrections.

A same-source before/after comparison finds 1301 fired weapons with changed
nominal flat totals. The binding inventory remains 643 rows; 282→301 qualify for
the full-effect diagnostic and partial-fed nominal debt changes 425→290. This is
a tooling measurement correction, not 135 newly converted weapons or gameplay
proof. Source claim snapshots and every listed claim document are co-updated;
historical numbers remain explicitly historical. No audit tolerance was raised.
The exact source values are 122 directly fired stacked-main weapons, 301 qualifying
bindings, 290 partial-fed weapons, 531 physical-state fired weapons, and 1592
legacy direct inheritors. Other source/integration combinations must remeasure.

The grouped anchor-readiness, physical-state and anchor-merge validation passes
47 tests. Full source ledger regeneration and its check pass for all 33 ledgers,
covering `extract_stats`' consumption of `actor_multipliers`. No raw faction ledger
or global `_model.json` content changes. Twenty-seven derived sidecars change:
207 physical-state multipliers, 208 weights and ten selected diagnostic weapon IDs.
The largest multiplier movement is `cobra.steel`, 1.2601→1.3705; this changes the
tool's estimate, not the unit's current price. Whole-unit reference certification and the existing source/scenario
holds are not cleared by these tooling and documentation repairs.
The final affected source audits both pass: doc-claims exits 0 with all 22 claims
matching, and doc-health exits 0 with zero structural findings. These replace the
earlier five-mismatch source checkpoint above; no full audit suite was rerun.
