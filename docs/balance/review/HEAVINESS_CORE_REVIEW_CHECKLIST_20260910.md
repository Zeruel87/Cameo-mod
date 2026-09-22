# Continuous heaviness core acceptance checks

## Final shared-mode tests — 10 September, 05:02 Jakarta

Full Python suite: **1453 tests, 14 failures, 8 errors, 45 skips**, with exactly
the same 22 failure/error signatures as the prior core baseline. Peak sampled
system RAM 82.53%; guard not triggered. The 20 new audit fixtures also pass:
11 independent K-inventory cases and 9 percentage-runtime reporting cases.

The final audit corrections separate legacy integer wrapping from intentional
shared scaling, keep all five authored shared profiles visible, and identify
runtime-zero values even when their continuous estimate is positive. Independent
K coverage retains positive continuous coefficients for fitting but expects no
percentage coefficient at h=0. It is analytical coverage, not a nonzero-hit count.
Invalid configurations are validated before non-positive damage filtering.
Independent review found no remaining draft-publication blocker.

The fresh 90-second shared-mode menu check passed without new exception logs,
with measured menu-load proof and peak RAM 74.81%. Production C#/YAML has not
changed since the 173-test build and nine-lane game probe below. Audit changes
do not require another game launch. Complete canonical audit results are
recorded with the draft PR; inherited repository failures remain visible.

Canonical `run_all.sh` completed with the same nine failing categories as the
core baseline: inherits, upgrades, basebuilder_crates, buildable_order, packs,
split_definitions, nuclear_flash_bindings, doc_claims and doc_health. No empty
reports remain. K-linearity and percentage-runtime gates pass; raw shared
inventory is five profiles including three runtime-zero profiles. Legacy Int32
overflow cases remain eight, separate from intentional shared scaling. Generator
sync verifies 146 retained templates with zero drift. Family/base compatibility
Shield duplicates remain visible rather than hidden from the raw census.

## Shared-mode checkpoint — 10 September, 04:11 Jakarta

Aedis approved the shared-profile interpretation at03:17. It is now implemented
for the five CannonAP pilots, with explicit SharedVersus mode and Scale2000.
Legacy consumers remain unchanged. Independent review found no remaining blocker
in the inspected production paths after adding undefined-mode, load-time overflow
and nonnegative-input checks. Python conservatively rejects a leading-plus numeric
mode token accepted by .NET; authored pilots use the named mode, not that syntax.

The isolated ./make all succeeded with0warnings/0errors; the fresh game DLL's
unique validation marker was verified. Parent reran the actual C# project:
173passed. The nine-lane actual game probe matched all expected totals exactly
for legacy controls, shared Medium and shared Shield armor at h0/1/2; peak RAM
76.39%, process closed. See the map README for measured values and boundaries.
This does not certify shield-pool behavior, splash distributions or match balance.

The parent-controlled memory-guarded full Python suite completed1433tests:
14failures,8errors,45skips. Failure/error signatures exactly match the core
baseline; peak RAM82.87%, guard not triggered. All33ledgers/derived sidecars were
regenerated and report zero drift. The complete audit/menu checkpoints follow.

Whole-PR comparison against upstream50b7d001 resolves2896existing definitions:
exactly six concrete weapons changed, with one new base and none removed. The
six are the five pilots below plus the earlier AlliedTankDestroyerCannon AP-role
correction. Its raw damage remains24000, but removing HE changes armor response
and outer radius900->80. The centered equal-armor percentage aggregate changes
378->306 after weighting the doubled AP Damage, not378->153; this is diagnostic,
not a matchup estimate. Eight focused AP-role tests pass. Earlier endpoint-only
results below remain historical rather than evidence for the later shared mode.

## Later checkpoint — 10 September, 03:25 Jakarta

Actual C# tests pass137, including the generated CannonAP fixture. The five-weapon
pilot comparison resolves2897weapons: exactly RA2sabot, RA2sabot_elite, TS90mm,
TS90mmDep and corrino_buggy_gun changed; all other existing resolved weapons match
the captured prepilot tree. A new base is present. This is a scope-preservation
comparison, not proof that the intentional armor-profile changes are equivalent.

The six-lane actual game probe matches every modeled Medium-target direct-hit
total; its README records measured values and the failed setup attempts. Peak RAM
was69.26%, and the owned game process is closed. No matchup/balance certification.

Independent review tightened the comparison's missing-base/main guards and damage
allowlist, strict audit Heaviness parsing, and Shield identity independent of shape
parsing. Raw base/Medium compatibility and existing legacy duplicates stay visible.
Reports distinguish authored/idealized calculations from runtime proof.

The first full activated-pilot suite ran1415tests with16failures,8errors,45skips.
Two newly exposed assertions assumed the preactivation corpus: no Heaviness anywhere
and unchanged global pricing census. They were replaced with an exact six-node
activation inventory and a separately isolated legacy-content golden. No live
census was filtered. A real stale-cache issue in target_model.use_ruleset was also
fixed: Shield mean/share caches now clear with the injected ruleset. Focused42tests
pass, including cache switching; a final full rerun is in progress.

The rerun finished1416tests:14failures,8errors,45skips. Failure/error signatures
match the previous core baseline exactly; sampled RAM peak77.18%. The complete
audit rerun retains the same nine blocking categories as baseline (inherits,
upgrades, basebuilder_crates, buildable_order, packs, split_definitions,
nuclear_flash_bindings, doc_claims, doc_health). Percentage-runtime dispatch
reports zero structural findings. This is not a fully green repository suite.

Aedis subsequently proposed a different shared-percentage table rule. Further
endpoint-based pilot expansion is paused; see HEAVINESS_SHARED_PROFILE_PROPOSAL_20260910.md.
The results above do not validate that unimplemented proposal.

This checklist records independent review of the opt-in implementation contract.
It is not evidence that the implementation has passed.

## Validation checkpoint — 10 September, 02:04 Jakarta

The isolated build succeeds; actual C# project tests pass (130), with 157 focused
Python tests passing. Independent review caught a disabled explicit-Range regression
missed by the first tests: omitted and -1 had been compared only to each other.
The helper now returns authored lengths when disabled, and both cases are tested
against the authored coordinates directly. Active scaling rejects both Int32 bounds.
The full Python run initially exposed ten outdated untyped test-fixture errors;
the fixture now declares its warhead type, with no weakened geometry assertions.
Full-suite rerun and activation checks remain pending. These results do not prove
every possible profile or gameplay matchup equivalent.

The generator preview is limited to CannonAP. Other families require preservation
of physical-state, integrity and extra-damage payloads before enabling that path.
The Shield/coexistence question was confirmed by Aedis at 02:10; implementation
itself was authorized at 00:40. New bases must be unique, and compatibility
duplicates remain visible. No existing level templates have been removed.

A fresh 90-second isolated menu boot at 02:05 completed without exception logs,
with peak sampled memory 73.47%. This is launch proof, not matchup validation.
The subsequent full Python core run completed 1377 tests: 14 failures, 8 errors,
45 skips, matching the 22 remaining upstream failure/error signatures. The initial
ten geometry fixture errors are gone. Sampled memory peaked at 84.92%.

## Acceptance checks

- Run shared field validation in the base rules-loaded path, not solely a virtual
  hook that AreaDamagePercentage overrides without calling base.
- Reject PercentageVersusLight/Heavy on AreaDamagePercentage until its separate
  primary-percentage semantics are deliberately supported. Those fields otherwise
  silently affect only a folded hit that the subclass forbids.
- Preserve the authored `MaxRadius > 0` shockwave branch decision. A tiny positive
  radius can round to zero after scaling; that must not switch to static-cloud mode.
- Scale every coordinate once before tick interpolation. Test single-entry Range,
  duplicate/equal distances after integer truncation, tiny radii and expanding rings.
- Interpolate percentage tables piecewise L/M/H with an explicit ties-to-even
  integer rounding contract before the bell. Validate endpoint values and key sets.
- Keep authored MiniYAML immutable. An effective-profile adapter must not transform
  already transformed data, including fallback from percentage to flat Versus.
- Execute actual C# helpers in differential tests, not a second Python equation
  presented as runtime proof. Compare h=-1/0/500/1000/1500/2000, absent/present anchors,
  asymmetric/flat profiles, derived armor, geometry and subclass validation.
- Verify the active resolved inventory has no explicit Heaviness=0 before treating
  the sentinel change as non-live. Never remove templates while consumers remain.
- Old percentage anchors are preserved before the new bell, not necessarily every
  final armor coefficient. Arithmetic normalization is not price invariance.

The independent build tree is a copy, not a junction. Do not change engine pins or
write through another worktree's engine. Parent controls build and publication.
