# PR #328: upstream integration and armament-mode boundary

## Current integration: retired exemptions (2026-09-06)

The current merge incorporates upstream `56c14d9db`. This section supersedes the
older snapshots below. Upstream deleted the intentional-composite exemption
registry under the one-warhead ruling. PR 328 therefore retires its live registry
drift command and that command's tests; it does not restore the deleted approval
mechanism. The last diagnostic is retained only as
[`pr328_composite_registry_drift_pre_retirement.json`](../history/audits/pr328_composite_registry_drift_pre_retirement.json).
Its counts are historical, not current findings or exemptions. The old live
command and its tests were removed; the archived evidence is recoverable in git.

The shared reachability survey also imported the removed validator, preventing
the percentage-runtime audit from starting. Its inventory now reports raw stacks
without exemptions. Legacy reviewed partition fields remain empty with an explicit
policy label; callers cannot supply a callback to restore exemptions. Raw counts,
reachability and lower-only ratchets are unchanged. Three synthetic regressions
cover direct/transitive/unreached counts and rejection of exemption injection.
The percentage-runtime audit now runs and passes (186 direct weapons, 296 folded
applications, zero dispatch-structure findings); 145-template generator sync passes.

The Hydra regression still verifies its complete historical four-profile fixture
and current BulletChem fields, but now checks the raw resolved main count directly
instead of importing the removed exemption machinery. Independent review identified
both compatibility issues and confirmed the nominal guard and armament-mode tests
pass. The completed paired test/audit comparison below supports a scoped merge;
it does not certify that upstream's entire balance pipeline is green.

All 33 raw and derived ledgers were regenerated from the integrated active content
(2,205 ledger actors). The merge retains upstream's centralized class-membership
import alongside the PR's per-armament firepower import. Gameplay files and engine
configuration remain identical to the integrated upstream revision.

Automated same-rules comparison loaded the exact upstream extractor from
`56c14d9db` and ran both versions against one integrated Ruleset. Across all 33
raw/derived ledger pairs, differences are exactly 1,000 new resolved-modifier
lists, two spawn-only eligibility flags and their four removed derived tier fields.
There are no other differences. Thus regenerated armor, damage, physical-state,
survivability and tier-model outputs are not silently changed by this PR.

### Final test comparison for this integration

Both runs used the bundled Python with openpyxl and the sequential bounded runner
(`-MaxMemoryMB 2048 -MaxSystemMemoryPercent 84 -TotalTimeoutSeconds 1800`).
The baseline was a clean detached checkout of `56c14d9db`, not a reconstruction
of its results from the PR's tests.

| Test tree | Modules completed | Tests run | Skipped | Failed modules |
|---|---:|---:|---:|---:|
| Upstream `56c14d9db` | 83 | 650 | 0 | 50 |
| Integrated PR 328 | 88 | 766 | 0 | 43 |

All 137 tests in the twelve PR-added/modified test modules pass. The current full
report is [`bounded_test_run.json`](../audit/latest/bounded_test_run.json).
No module newly fails. Seven baseline failures are repaired: assignment tests,
four Hydra modules, physical-state binding regression and scaled-bullet overrides.

**Method-level qualification:** fixing the survey import exposes twelve failing
methods that baseline could not execute: five in `authorized_remaining_profiles`,
four in `corroborated_role_profile_consolidation`, one in `reachable_stack_planner`
and two in `weapon_structure_inventory`. These modules were all import-blocked
upstream. The additional output exposes old profile/ratchet disagreements; it is
not a claim that no new failure messages appear. No other new failure identities
were found. The independent reviewer reproduced this comparison and conditionally
approved the scoped repair after completing the paired audit comparison.
No historical profile expectation or raw-stack ratchet was raised to pass.

### Final canonical audit comparison

Both `bash tools/audit/run_all.sh` runs completed with exit 1: integrated PR
716.6 seconds, clean upstream 721.0 seconds. Their sampled process-tree peaks
were 1,119.4 and 1,119.3 MB; peak PC memory was 55.0% for both, below the 84%
guard. These are completed red runs, not interrupted or globally passing runs.

The PR has no zero-byte Markdown reports. Upstream's percentage-runtime report
is empty with an import-error sidecar; the PR repairs that import and reports
zero dispatch findings. Ledger drift is repaired from 31 baseline ledgers to
zero. Raw stack findings remain fully visible. Document-health checks find no
issues in either tree. The six refreshed rename proposals are byte-identical
between both runs; no renames are applied. Other gameplay audit differences
were checked against the identical source and refreshed ledger inputs.

Independent review found two minor PR-added error-handling flags, now repaired:
explicit absolute-path provenance fallback and explicit encoding forwarding in
a test wrapper. Their 43 focused tests were rerun and pass; error-handling counts
now match upstream. The security audit deliberately retains one additional
`exec` finding: the historical consumer comparison executes trusted repository
modules at the fixed SHA `ffc753fb0a6430fa518869ba94027aef4cd8e7ba`, with module
names selected by a literal tuple. It does not accept a ref/source from the user.
This reviewed diagnostic boundary is documented, not hidden by an exemption.

The engine-freshness audit cannot measure the external engine clone in this
environment and explicitly says so; this is not a clean engine result. No engine
or live gameplay files differ from upstream, and no game was launched for this
tools/docs-only PR. Final ledger verification and all four PR report freshness
checks pass. The independent reviewer recommends the scoped merge, with existing
upstream failures retained as implementation follow-up rather than waived.

## Local follow-up: spawn-only roster classification (2026-09-06)

Fetched upstream `77beaef41`, 171 commits beyond this PR's integrated base.
Those commits are **not integrated** here. The snapshot and validation sections
below describe the PR worktree, not current upstream gameplay. Upstream's handoff
assigns the weapon codemod to Claude and composite-registry review to Nova/Ember;
this repair does not overlap those decisions or authorize merging PR 328.

The extractor lacked the actor-name parameter required by the existing
`test_assign_references.py` regressions and the self-prerequisite rule in
`REFERENCE_PIPELINE_HANDOFF.md` §10. It now excludes a positive exact self
prerequisite from offline roster eligibility while preserving negated self gates.
The actor key is passed by `extract_actor`, including for inherited Buildable
traits. This is the documented Cameo roster heuristic, not general prerequisite
reachability simulation. Costs, HP, weapons and runtime YAML are unchanged.

Both direct execution and unittest discovery now execute all 14 assignment tests;
the misplaced `unittest.main()` previously hid the last class during direct runs.
An independent reviewer ran the direct test file and found no blocking defect.

Comparison over 2,198 ledger rows changes only `forgotten_mutant_wild` and
`forgotten_tiberianfiend_wild` from buildable to non-buildable; all 100 exact
negated-self cases previously eligible remain eligible. Generator-produced diffs
contain exactly these two flags and removal of their four derived tier fields.
The global model fingerprint is unchanged. Full raw/derived ledger verification
passes for all 33 ledgers after the focused regeneration. Percentage-runtime and
145-template generator synchronization checks pass on this PR worktree.

This changes later pricing/reference populations intentionally; it does not apply
prices. The follow-up full suite completed **88/88 modules, 862 tests run, 15
skipped, 21 failed modules** in 481 seconds, recorded in
[`bounded_test_run.json`](../audit/latest/bounded_test_run.json). Compared with
the previous recorded run, there are no newly failing modules and the assignment
module is repaired. Remaining failures are not waived or automatically classified
as harmless. Structure and decision audits still fail on the invalid registry.

The default Python lacks openpyxl: four consumer tests and eleven workbook tests
were skipped in that run. Both modules were separately rerun with the bundled
Python: **16 consumer + 11 workbook tests pass, zero skips**. This supplemental
result does not turn the red full-suite report green. Sampled full-suite peak was
879.8 MB for its process tree and 50.5% PC memory, with an 84% PC guard. Diff checks
pass; no game was launched. Publication and latest-upstream integration remain
pending.

## Previous upstream integration snapshot

Integrated upstream `e06ed9907` (115 commits beyond the former base). This is a
tooling integration, not approval to merge PR #328 or change gameplay.

## What changed here

- The workbook and range-tool import conflicts combine upstream's centralized
  class membership with this PR's per-armament firepower handling. Both broad
  write guards remain closed. Workbook fingerprints include both helper modules.
- The JSON-only nominal proposal now requires an actual attack selecting the
  primary armament. Orders such as AttackMove do not qualify. Disabled, paused
  or unknown activation at the assumed zero-condition snapshot blocks a proposal.
  This is not a simulation of actual spawn-time conditions or combat readiness.
- The new armament-mode report resolves inherited slots and reports each mode's
  factor, attack selectors, activation uncertainty and other base-YAML references.
  It never sums primary/garrison slots, removes an armament, or proposes a price.
- All 33 raw and 33 derived ledgers were regenerated. A comparison with the exact
  upstream extractor, run against the same current YAML, produced identical raw
  data after removing only `resolved_firepower_modifiers`, and identical derived
  sidecars. Derived changes relative to committed upstream are regeneration drift,
  not a new pricing law or applied actor costs.

## Current roster result

The ledger-listed armed population is **1,000**, up from 950 on the previous base.
It is not an exhaustive inventory of every concrete actor or every map override.

| Actual armament topology | Actors |
|---|---:|
| Fewer than two slots | 338 |
| Same-weapon primary/garrison pair | 86 |
| Other repeated same-weapon slots | 23 |
| Other multiple weapons | 553 |

None of the 86 simple pairs pass the weapon-only model: 49 first stop at folded
percentage damage, 17 at standalone percentage damage, 8 at GlowImpact, 1 at state
feedback and 11 at projectile delivery. These are first blockers, not exhaustive
independent findings. **41 pairs also have other base-YAML references.**

There is therefore no evidence to relax the multi-armament proposal guard. Five
single-armament actors pass the structural screen; four have reference concerns.
The Spy remains the one unshared nominal candidate, not a rebalance recommendation.

## Hydra: current versus historical

Upstream `8748c68e4` replaced HydraSpit's four profiles with `BulletChem_Light`;
subsequent upstream generator work retains 18,000 Damage, PercentageScale 10,000,
ReloadDelay 15, Range 5979 and the Corrosion map binding at 20. This integration
preserves that upstream definition. It does not assert that the redesign preserves
the old weapon's damage, splash, state response or gameplay balance.

The old laboratory and two-stage pilot concern a different, historical weapon.
Their original JSON and report artifacts remain intact. Tests now explicitly use:

- A fully resolved weapon fixture captured from
  `819abe10d5858b810c6102a33eeebce42165f6cb`, canonical SHA-256
  `50c133e219282e45ffe130f8a657d61aba40e732aecd9953a19d9098680e4122`.
- The archived target/shooter scenario, canonical SHA-256
  `5591cd280cb6e097795a2bb6e1fccd9850e47b3245754b03fbd83b35b395d398`.

Historical evaluations require explicit complete inputs. Default execution against
today's weapon rejects the unsupported scenario before writing artifacts. Tests
retain the old arithmetic evidence separately from the current BulletChem contract.
No game launch or in-game validation is claimed.

## Validation boundary

Generator synchronization passes for 145 templates. Percentage-runtime checks pass.
The physical-state audit remains failing with 208 findings. The structure and
decision audits fail because upstream's reviewed-composite registry no longer
matches the resolved weapons. No stale digest or changed composite is automatically
re-approved here; the old structure/decision artifacts must not be read as current.

The [historical registry drift queue](../history/audits/pr328_composite_registry_drift_pre_retirement.json) retains
all **355 validator findings**. Its overlapping categories include 11 curated
main-name disagreements, 14 manifest main-name disagreements, 151 changed main
fingerprints despite unchanged names, and 5 reference/reachability disagreements.
These are review categories, not approval decisions. Its raw topology counts show
335 stacked concrete weapons: 242 reachable and 93 currently unreached. No
reviewed/unreviewed totals are claimed while the registry is invalid.

The now-retired `report_composite_registry_drift.py --write` command wrote only
diagnostic JSON. At this historical checkpoint, a fresh blocked report still
returned exit 1. It must not be resumed against the current, retired registry.

The previous integrated suite completed **88/88 modules, 859 tests run, zero skips,
22 failed modules** at PR head `9a47d4703`. The current report is superseded by the
local follow-up run described above. Setup errors
prevent some classes from running their test methods; this is not 859 passes.
Sampled full-suite process-tree peak was 831.6 MB and PC memory peak 44.9%, with an
84% guard. The new/migrated focused tests pass, but the overall suite remains red.
A prior green 802-test result applies to the old base, not this integration.

Baseline reproduction was selective, not a second full clean-checkout suite:
loading the exact `e06ed9907` registry implementation against byte-matching upstream
YAML/manifest/resolver inputs reproduced all 355 registry findings. Loading that
revision's extractor and assignment tests reproduced the three two-argument
`_is_balance_buildable` API errors. Other failed historical contracts remain
unresolved findings; they are not all declared harmless or upstream-proven here.

Historical next step (superseded by the registry retirement above): reconcile
changed composite decisions against their upstream commits and refresh the registry.
Do not perform that obsolete step or restore exemptions on current upstream.

The 11 curated main-name disagreements group into three concrete review batches:

- Seven Tesla-containing superweapon chains lose a separate `Tesla_Heavy` main:
  Atomic, NaxiV1Rocket, PulseMissile, RA2Atomic, RAAtomic, SteelIonCannonDamage and
  TDIonCannonDamage.
- Three Ixian cannon profiles lose a separate `CannonHE_Medium` main:
  DuelistTankCannon, HeavyIxianCombatTankCannon and IxianCombatTankCannon.
- JapanesePlasmaBomb replaces its Chemical/Demolition/Flame trio with Plasma.

These observations describe profile membership only, not damage preservation or
approval. The other fingerprint/reference findings still require review too.

## Priority finding: AtomicCore loses a delayed extra hit

Upstream [a92ae850f](https://github.com/cameo-mod/Cameo-mod/commit/a92ae850ff65b65cab015f99e2a5a0fc9e115910)
does more than collapse two same-family mains. Comparing its parent AtomicCore
definition with current upstream gives these explicit Tesla stages, all targeting
`Shielded`:

| Authored Delay | Before raw Damage | Current raw Damage |
|---|---:|---:|
| 0 | 100,000 | 200,000 |
| 2 (`Tesla_Super_ExtraDamage`) | 100,000 | 100,000 |
| 3 (`Tesla_Heavy`) | 100,000 | removed |
| 5 (`Tesla_Heavy_ExtraDamage`) | 100,000 | removed |
| Sum of these explicit Tesla stages | 400,000 | 300,000 |

Thus the explicit raw Tesla-stage budget falls 25%, and a delayed 100,000 main
contribution moves to the initial stage. **This is not a claim of a 25% reduction
in total nuclear damage or actual shield damage**: armor, percentage applications,
defenses, target eligibility and the other nuclear payload remain separate.

The engine's `WeaponInfo.Impact` dispatches all warheads and schedules positive
Delay values through `DelayedImpact`; `ExtraDamage` is not an engine exemption.
The structural main-count predicate deliberately excludes that companion name.
Preserving only the main-warhead total therefore does not establish preservation
of the complete delivered payload or timing.

Current resolved descendants Atomic, RAAtomic, RA2Atomic, NaxiV1Rocket, DTAtomic
and ChemTibAtomic all contain the remaining two Tesla stages. This is a concrete
reason to reconcile the review decisions, not merely refresh their fingerprints.
Whether the removed hit and altered timing were intended remains a maintainer
decision. No gameplay restoration is applied by this PR.
