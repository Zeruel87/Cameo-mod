# Overnight draft integration review

This is a local integration checkpoint, not a merged PR or gameplay-balance approval.

## Frozen batch closed — 10 September, 12:18 Jakarta

Current source inputs supersede the historical snapshots below:

| Draft | Source commit | Closing change |
|---|---|---|
| PR339 | d0c0be8848289e27c854fae1f5aae0e8df4011f2 | Four-actor CA initial-state declaration inventory; missing Contents link |
| PR340 | 6278225df00c0aa0356961036c44670847321027 | Final30 RA1 and16 TD identity-only weapons, exact references and tests |
| PR341 | 5a931844a3c6184fbfdd9f50fc8724b37543c5e0 | Citation-only correction; previously verified heaviness pilot unchanged |

All three are published OPEN/DRAFT. This combined checkout remains local and
unpublished. No master push, PR merge, protected PR edit, engine pin change or
OpenCode invocation was made. Scope is frozen; no additional cohort is active.

### Final evidence

- R18 isolated full discovery:1,962 tests,12 failures,8 errors,64 skips. All20
  failure/error identities are exactly R17's baseline.1,965 discovered identities
  are accounted for, including3 methods under the pre-existing optional-DTA class
  skip; no missing/extra tests. Peak total system RAM66.90%, no95% guard stop.
  This is not an all-green suite or a claim of monolithic-equivalent execution.
- The16 TD identities preserve all2,910 source/2,911 combined weapon payloads.
  Full-field ledger comparisons are identity-only; all33 ledgers match live rules.
  Earlier30-name preservation and R16 evidence are in the linked cohort reports.
- Frozen final menu boot started12:07:22 Jakarta and completed90 seconds:
  fresh MenuPostProcessEffect.PostWorldLoaded, no new exceptions, peak RAM66.85%,
  owned process closed. No rebuild or matchup validation. The verified DLL remains
  SHA-256 79FB7B6826E2A1F118883F1EDDA1CE0418446ED49561B5E2B521F89013B301A1.
- The citation-only generator docstring was synchronized AFTER R18.41 focused
  generator/fixture/citation tests then passed;146 templates regenerate with zero
  drift. The combined documentation-health audit now passes. R18 is not presented
  as having executed the later docstring.
- Final targeted combined runtime/shape/uniqueness/suffix/split/K-linearity and
  balance audits pass. Release drift remains FAIL: D1=115,D2=59,D3=17,D4=406/335,
  D5=34. Source339 and340 full canonical runs retain eight existing gated failure
  categories each; see their reports. No audit thresholds or original fixtures
  were relaxed. Source340 C1 remains20. Independent final review found no remaining
  publication blocker for this batch, not a whole-project balance endorsement.

Renames do not fix historical damage outliers: Recon still33000 versus release
32000, RAVulcan and both Officer weapons still16000 versus4000. Missing old-name
matches remain raw debt; accepted status is not automatically transferred.

### What remains, without opening more work

1. **Actual balance implementation:** the next recommended bounded candidate is
   the already-assessed Forgotten CannonAP cohort, not another naming session.
   Its alternate weapons and material Wood/Heroic/percentage changes need targeted
   matchup review before activation. The current five-weapon live pilot is not a
   complete roster rebalance. See FORGOTTEN_CANNONAP_NEXT_COHORT_20260910.md.
2. **Source-dependent state evidence:** factory/max certification still needs
   exact source-engine provenance and a defined owner/prerequisite/upgrade/rank
   scenario. The CA pilot records declarations only. Spice Wars source is missing;
   RA3/Emperor coverage is not final-retail semantic certification.
3. **Subjective naval roles:** do not apply submarine references to surface boats,
   equate carriers with launcher DPS, or steal the RA1 Cruiser reference without
   a reviewed assignment decision. See TD_NAVAL_REFERENCE_REVIEW_20260910.md.
4. **Deferred implementation:** broader ownership/W24 migration remains unfinished,
   not falsely declared source-blocked. It is outside this frozen closing batch.
   Fingerprinted target proposals must be regenerated/reviewed before later use;
   no new prices or stat targets have been applied here.

Blackrobe's latest cadence is roughly2hours between routine Aedis updates.
The12:08 update was delivered; closing publication news is recorded for the next
appropriate update, not sent immediately. New-work intake after06:00 remains closed.

## Historical checkpoints

## Exact inputs

- PR341: `4b4b354f4914305e6a248ce15f83a233970ee400` (integration HEAD).
- PR339: `0a0b7f3d4dc8c1c1090e05d962c24b1a93bb3c76` (pending merge parent).
- PR340: `45444296545d0a4e1aaa994e8d3086e5b6b0cfec` (reviewed binary Git patch;
  source/test/map changes applied, generated outputs regenerated rather than patched).

The newer CA structured-corpus follow-up is not included in this first snapshot.
The engine directory is a read-only-use junction to PR341's verified engine/build.
No build is run through that junction. The main checkout and protected PRs are untouched.

## Findings and repairs

The initial combined run executed 1,867 Python tests: 16 failures, 9 errors and 64 skips;
peak sampled system memory was 78.40%, with no guard stop. This is not a green suite.
Compared with the final PR341 run, three additional cases appeared:

1. The CannonAP byte-identity test compared against moving Git HEAD. After publication,
   HEAD already contained the appended base, making its expected tail comparison invalid.
   The test now executes both tools and both profile JSON inputs from immutable upstream
   `50b7d001be845e0ac5a0812d2591e154148c94dc`. All 22 module tests pass. This is test-only;
   the generator, weapons and runtime are unchanged. Independent review found no blocker.
   Git history must contain that baseline revision; missing history fails explicitly.
2. Generated reference assignments retained old Soviet actor identities, breaking the
   paired-identity check and changing the selected MBT speed pool. Regenerating the
   assignments restores both tests without weakening their assertions. Assignment scores
   and membership changes remain visible; this is not a pure string replacement.

The existing stale firepower-input report was also regenerated. Its 770 changed-entry
count remains unchanged. The targeted report, identity, speed-grid and actor/map naming
checks pass together: 42 tests. A corrected full rerun is still required.

## Other checks

- 33 balance ledgers: zero drift.
- Canonical audits completed with eight failing categories: inherits, basebuilder_crates,
  buildable_order, packs, split_definitions, release_drift, doc_claims and doc_health.
  No empty Markdown report was generated. Failures are retained, not suppressed.
- Combined menu boot started 05:50:29 Jakarta and completed the 90-second observation:
  fresh menu-load evidence, no new exception logs, sampled memory peak 87.66%.
  The test process was closed. This proves loading only, not matchup balance.
- Corrected full rerun: 1,867 tests, 13 failures, 8 errors, 64 skips; sampled
  memory peak 77.25%, no guard stop. Failure signatures are the final PR341 baseline
  minus the now-repaired stale firepower report test, with no additional failures.
  Known baseline failures remain unresolved and visible; this is not a green suite.

No PR merge is authorized by this report. Naval source-role holds and factory-ready /
maximum-upgrade evidence remain distinct work items; no price or live unit-stat fitting
has been applied by the reference collection work.

## Subsequent 13-weapon name follow-up

The reviewed BTR80/Flak Truck/Monster Tank identity patch applied cleanly. A fresh
90-second combined menu boot started 06:29:54 Jakarta and passed: no exceptions,
fresh menu-load proof, peak memory 79.62%, process closed. All 13 resolved weapon
payloads are unchanged. The earlier 1,867-test result predates this additional patch;
a final combined source snapshot and full rerun remain pending.

## Latest source snapshot (06:50 Jakarta)

The integration index now additionally contains PR339 through `09ffb2108975bbd48e1d201158c9053b0b653874`
(including structured CA input and raw production declarations), PR340 through
`905e9befc698f522f6268d6aa7e6a2c4ef9d1d58` for source/tests, and the PR341
`0dba5542ff8068179066321ab1aa633a1a4cf82b` frozen-baseline test fix. The pending
merge parent/HEAD above remain the historical starting points, not these complete inputs.

Applying the new JSONL together with its new `.gitattributes` produced CRLF bytes in
this already-populated integration checkout. The strict reader correctly rejected the
SHA mismatch. A byte-normalized comparison proved line endings were the only difference;
the exact published source bytes were copied back and restaged. No hash expectation was
relaxed. Fresh assignment generation succeeds: 694 actors in scope, 362 assigned, 216
with at least two references; 68 chassis-only and 199 formula-only. These are diagnostic
assignments, not approved live stat changes. Firepower report remains 770 changed entries.

The two source PRs separately match their baseline failure signatures: PR339 1,710 tests,
14 failures, 8 errors, 64 skips; PR340 1,341 tests, 14 failures, 8 errors, 45 skips.
Combined canonical audits retain the same eight failing categories, with no empty
final reports. The full R3 suite completed: 1,892 tests, 13 failures, 8 errors and
64 skips; exact prior integration signatures, peak memory 78.38%, no guard stop.

## Final identical-definition cleanup validation

The two identical OrniBombC/OrniGunC Ordos declarations were removed in the PR341
follow-up and applied here. Both weapons still resolve from Atreides. All 2,900
combined resolved weapons compare identical before/after removal. Three focused
regressions pass. The targeted split-definition audit now passes: S2 4→2, S1 22,
unchanged ratchets 2/56. The earlier canonical report set predates this line-only
cleanup; the split-definition report was regenerated afterward.

Final full R4 suite: **1,895 tests, 13 failures, 8 errors, 64 skips**, exact same
failure/error signatures as R3. Peak memory **80.97%**, no guard stop. No new game
run or engine build was necessary for an exactly unchanged resolved weapon set.
The full suite is not green; the remaining baseline failures are not waived.

This final source cleanup is published in PR341 as `7823fb3e0`.
PR339 remains `09ffb2108`; PR340 remains `905e9befc`. All three are open drafts.
This local integration checkpoint is not pushed and does not merge any GitHub PR.

## Yak ownership checkpoint (08:33 Jakarta)

PR340 source/tests now match published `b45546fe165af74a21dec55685ed0cf8cdb47179`.
PR339 remains `09ffb2108` and PR341 `7823fb3e0`. Five aircraft own ten independent
guns in place of four shared names. Complete2,900→2,908 weapon comparison preserves
every retained and renamed concrete payload; only two abstract helpers additionally
appear. Raw and derived Soviet ledger values remain unchanged after identity and
direct-ancestry normalization. No extractor/class-policy change is included.

Seven focused regressions pass. Final R7 suite:1,902 tests,12 failures,8 errors,
64 skips; exact R6/R5 signatures, one stale inventory failure removed versus R4.
Peak RAM83.72%, no guard stop. All33 ledgers have zero drift. Final targeted
percentage-runtime, K-linearity, suffix, split, shape and balance-drift audits pass;
release-drift remains failing with raw D4=347 and unchanged335 threshold.

The07:45 90-second menu boot passed before final payload-preserving factoring,
not afterward. Independent review cleared the final compatibility-helper naming
and verified no hidden class change. Five additional informational missing-direct-
warhead-template entries are disclosed, not excused. The full suite is not green.
This remains local integration only, not a GitHub merge or master push.

## Tiger ownership checkpoint (08:54 Jakarta)

PR340 source/tests now include `d598557f93f6e9585d40789778153c00113040a5`.
The complete 2,908→2,911 combined weapon comparison passes; only the four expected
owner identities and one effect helper replace two shared names. Five new focused
tests pass. Final R8: 1,907 tests, 12 failures, 8 errors, 64 skips, exact R7
signatures; peak RAM85.88%. Both source/integration have33 zero-drift ledgers.
The08:49:30 90-second boot passed with no new exceptions, fresh menu proof and
peak RAM70.59%; this covers final Yak and Tiger changes, no rebuild or matchup test.
Targeted runtime/shape/split checks pass. Release D4 remains failing at348/335.
Local effect debt falls694→693; other shape buckets and stacked counts stay fixed.
Both follow-ups are independently reviewed, still draft and unmerged.

## Fourteen-name Allied checkpoint (09:18 Jakarta)

PR340 source/tests/map now include `243c95cd8a8694002860715ac4699f00dd3b4365`.
All 2,911 combined weapon payloads remain exact after the fourteen identities are
reversed. Eighteen Armament values, one muzzle-smoke binding and Survival's one
map-local pistol reference migrate. Six new tests and four projectile-speed tests
pass; archive member data, order and metadata are pinned. All ledger fields are
unchanged except identity strings, and both 33-ledger checks have zero drift.

Final R9: 1,913 tests, 12 failures, 8 errors, 64 skips; exact R8 signatures.
Peak RAM86.41%, no guard stop. Targeted runtime/shape/split checks pass; release
D4 remains failing at355/335, with all structural counts and D1/D2/D3 unchanged.
No additional game run is claimed after this identity-only batch. The Gunboat
geometry/heaviness hold is retained under its new cannon name, not marked resolved.

## Eleven-name checkpoint (09:51 Jakarta)

PR340 now includes `17022b1d5b73841df40daa5f6a2ef8c0d5170ce8`.
Eleven names and twelve Armament values migrate, with all 2,911 combined weapon
payloads and all numerical ledger fields preserved. The old Soviet SAM actor
regression now recognizes only the exact reviewed Nike identity substitution;
negative cases and the full weapon fixture keep gameplay changes detectable.

R11:1,919 tests,12 failures,8 errors,64 skips, exact R9 baseline signatures;
peak86.56%, no memory guard stop. Runtime/shape/split checks pass; release D4
remains failing at363/335, with other damage and structural counts unchanged.
Both33-ledger checks have zero drift. No post-batch game test is claimed.
PR340 remains draft and unmerged; this combined checkpoint is local only.

## Guarded five-name checkpoint (10:25 Jakarta)

PR340 source `8850c3f12a0ebebcfa9ab07b8e64048a799e3a20` is integrated locally.
All2,911 combined weapon payloads remain identical after5 identity reversals;
all ledger fields stay identical except names. 46 focused tests and independent
review passed. Historical converter evidence, exact armor-value guards and the
unrelated Hellfire support-power name are preserved.

R12 was guard-stopped at90.04%, incomplete. Isolated R13 ran1,929 tests with
12 failures,8 errors,64 skips, exact prior signatures,53.75%peak. All1,932
discovered identities are accounted for:three methods belong to the explicit
pre-existing optional-DTA class skip. The original runner's terminal count
assertion was a bookkeeping error; the retained log and independent ID check
document it. Do not call this all-green or monolithic-equivalent.

Targeted runtime/shape/split checks pass; releaseD4 stays failing367/335.
Both33-ledger checks have zero drift. No additional game proof is claimed.
Future memory stop guards are95% per Blackrobe. This remains local-only integration.
