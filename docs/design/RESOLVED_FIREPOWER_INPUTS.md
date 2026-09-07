# Class-fitting firepower input correction

Scope: offline pricing inputs. No actor costs, weapon damage, runtime code,
class anchors or live includes are changed. The inactive Hydra pilot stays inactive.

The old raw ledger field `firepower_multiplier` represents one local fine-tuning
knob. That field is still needed by legacy diagnostics/retirement tooling; it is
not a complete actor damage multiplier. Class fitting previously treated it as one.

Raw ledgers now also record `resolved_firepower_modifiers`: the inherited,
unconditional `FirepowerMultiplier` traits, with their integer percentages,
armament-name restrictions and local/inherited provenance. An empty list explicitly
means none; consumers must not fall back to the local knob in that case.

`fit_class.unit_inputs` multiplies the applicable percentages for each armament,
both for raw weapon DPS and the optional derived effective-DPS path. It does not
double-count the legacy field. Armament names are case-sensitive, default to
`primary` only when omitted, and retain explicitly empty names. Zero means zero,
not a missing value. Old ledger fixtures without the new field retain compatibility.

## Impact

The [generated comparison](../audit/latest/firepower_inputs.json) finds 770 changed
actor entries with usable class-fit inputs across the roster. These are input
corrections, not 770 balance defects or recommended price changes.

Examples of unconditional products:

| Actor | Old local multiplier | Resolved product |
|---|---:|---:|
| Hydralisk | 0.99 | 0.50 × 1.10 × 1.10 × 0.99 = 0.59895 |
| Marine | 0.31 | 0.50 × 1.10 × 1.10 × 0.31 = 0.18755 |

Both examples change by the same factor, 0.605. A common multiplier can cancel
when class members and their real anchor are normalized together. Do not interpret
the DPS-input ratio as a price ratio. No authoritative new prices are generated:
that requires selecting/refitting the intended class anchor and pricing mode.

## Deliberate limits

- This is the product of unconditional `FirepowerMultiplier` traits, not a combat
  simulator. Per-hit integer rounding can differ from multiplying floating DPS.
- Traits with `RequiresCondition` are excluded, including conditions that may hold
  at spawn. Veterancy, upgrades, player modifiers, health-dependent modifiers and
  other modifier trait types are not newly modeled here.
- The existing effective-damage/physical-state models and their limitations remain.
  Duplicate state delivery is not fixed or repriced by this change.
- The initial commit fixed `fit_class`; the consumer follow-up below migrates
  current-output measurement, not replacement-damage inversion. Different armament,
  charge-cycle, armor and pricing models still prevent universal price agreement.
- The local fine-tuning field remains unchanged. Neither the resolved list nor its
  product is introduced as a gameplay write-back knob.

## Reproduce

Run with `tools/run-bounded-python.ps1` and an appropriate memory/deadline guard:

```
tools/balance/extract_stats.py --check
tools/balance/firepower_input_report.py
-m unittest discover -s tools/tests -p test_resolved_firepower_inputs.py -q
```

The report command checks freshness by default; `--write` refreshes only its JSON.
Regression coverage includes inherited Hydra/Marine values, conditional exclusions,
armament scopes, zero values, legacy compatibility, and both raw/derived DPS paths.

## Initial-commit validation (2026-09-05)

- Full isolated suite: 80 modules, 767 tests run, 756 passed, 11 skipped; no failures.
  Includes nine new tests. Sampled process-tree peak 1,381.4 MB; PC peak 47.6%.
- All 32 ledgers pass fresh extraction checks. Removing only the new field from
  each refreshed ledger reproduces its prior contents; derived ledgers are unchanged.
- Generator sync (139 templates), percentage-runtime, structure/decision freshness,
  report freshness and diff whitespace checks pass.
- The decision audit initially hit a 1 GB process guard; rerunning under 2 GB passed.
  The existing physical-state audit still fails with 216 findings, unchanged.
- Independent review approved the scoped change after stronger exact-value and
  armament-name tests were added. No game launch or gameplay edits were needed.

## Consumer follow-up

The shared `firepower.py` helper now supplies class fitting, band checking, the
faction diagnostic report, range diagnostics and workbook weapon rows. Legacy
fractions remain fractions: 0.99 means 99%, not 0.99%. The workbook and range/faction
tools previously divided those values by 100 again. The faction report also read
template-name strings in `warheads` as damage records; it now uses `damage_warheads`
and the existing main-damage predicate (including AreaDamage, excluding chips).

Band/range/workbook totals exclude non-default conditional alternatives and unpaid
garrison rows. Alternate weapons remain visible in the workbook, but are not summed
into the base actor row. Resolved factors are locked per-weapon diagnostic cells,
not imported actor knobs. The workbook fingerprint includes the shared helper.

The [consumer census](../audit/latest/firepower_consumers.json) compares the first
PR328 commit's consumer implementation with this follow-up across 1,000 armed
ledger entries on the `56c14d9db` integration:

| Consumer | Changed entries | Baseline errors included in changes |
|---|---:|---:|
| Band DPS input | 799 | 0 |
| Faction primary-weapon DPS input | 905 | 836 |
| Range DPS input | 890 | 0 |
| Workbook weapon-row factors | 932 | 0 |

These counts include corrected condition selection and schema handling; they are
not all attributable to inherited firepower alone. Workbook counts concern factors,
not evaluated Excel prices. The faction report remains intentionally primary-only;
other consumers sum their selected priced armaments. Charge-cycle/model differences
remain outside this follow-up. No reference anchors or derived pricing data were
recalibrated, and no proposed cost was applied.

The band checker remains failing: 169 flags across 20 classes versus 131 on the
baseline, using the same unrecalibrated anchors. The report retains both exit codes
and counts. Do not treat those flags as proven unit defects or lower the thresholds
to make this measurement correction green.

### Explicit write boundaries

A separate [retained-firepower proposal lane](RETAINED_FIREPOWER_PROPOSALS.md) now
accepts explicit per-tick targets for a narrowly screened single-weapon actor.
It does not reopen either broad generator below or infer a balance target.

`propose_class_rebalance` still assumes prospective Damage at FP=1 and can prescribe
deleting a modifier. It now rejects selected modern resolved-modifier ledger entries,
including empty lists, before writing a proposal. It needs a separate design for
retaining inherited/scoped multipliers during inversion; current-output measurement
cannot be substituted for that design.

`update_ranges --confirm` similarly rejects selected modern entries before any
ledger is written, including across a multi-ledger run. Dry-run diagnostics remain
available. Applying one solved range to every priced alternate armament requires
an explicit policy; this follow-up does not silently authorize it. Legacy arithmetic
tests remain supported, but removing the new field is not a supported workaround.

The generated workbook binaries are not regenerated or represented as current by
this code-only follow-up. Workbook generation/import is tested in memory using the
bundled openpyxl dependency; no Excel recalculation or visual QA is claimed.

### Historical consumer-follow-up validation

Current upstream integration status and armament-mode findings are recorded in
[PR328_UPSTREAM_INTEGRATION.md](PR328_UPSTREAM_INTEGRATION.md). The green results
below predate that integration and do not supersede its current failures.

- Final-source suite: 81 isolated modules, **781 passed, zero skipped, zero failures**.
  The bundled Python runtime supplies openpyxl, so all workbook tests actually run.
  Includes 14 consumer regressions alongside the initial nine input regressions.
- Sampled full-suite process-tree peak: 1,364.1 MB; PC memory peak: 49.1%.
- 32 ledgers: zero drift. Generator, percentage-runtime, structure/decision checks,
  both impact-report freshness checks and diff whitespace checks pass.
- Band validation remains FAIL (192 flags, baseline 129); physical-state validation
  remains FAIL (216 existing findings). Neither is suppressed or treated as a
  mandate to change gameplay.
- Independent review approved the final guard/scope corrections, with its final
  condition satisfied by the successful final-source suite.
- No gameplay, raw/derived ledger, class-anchor, map or engine edits in this follow-up.
  No game launch, package installation or merge.
