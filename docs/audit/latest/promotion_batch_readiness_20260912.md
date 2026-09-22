# Promotion batch readiness — 12 September 2026

This is a fail-closed readiness check for the approved **1,500 virtual
credits per authored promotion tier** pilot. It does not remove inherits,
change costs, alter prerequisites or change runtime behavior.

## Result

**BLOCKED — 0 of 40 promotion-token consumers have a final GP-04 disposition.**

The 40-actor removal set is mechanically the set with both a direct
`Inherits@PromotionUnitBuff: ^PromotionUnitBuff` and one current-faction
promotion prerequisite. Their current proposal dispositions are:

| Disposition | Actors | Why the atomic batch cannot use it yet |
|---|---:|---|
| `SCALAR_REFERENCE_COVERAGE_REQUIRED` | 25 | Source coverage is not complete for the pricing decision. |
| `LIMITED_UNIT_SEPARATE_REVIEW` | 7 | The unit needs a separate limited-unit decision. |
| `CARGO_AWAITS_FINAL_PASSENGER_PRICES` | 4 | Promotion and cargo pricing must use the final passenger prices. |
| `AIR_OR_NAVAL_CLASS_DESIGN_REQUIRED` | 3 | The class model is still unresolved. |
| `SUPPORT_PRICE_EXEMPT` | 1 | Support pricing is a separate exception. |

The nine direct-buff actors without a promotion prerequisite remain protected
from removal. The seven promotion-token consumers without a direct buff remain
outside the removal set. The exact names and atomic write boundary are recorded
in [PROMOTION_CARGO_BATCH_20260911.md](../../balance/PROMOTION_CARGO_BATCH_20260911.md).

## Safe next step

1. Resolve the GP-04 disposition for every affected promotion unit and any
   dependent passenger price.
2. Re-run this readiness check and require all 40 rows to carry an approved
   final price/disposition before preparing a content diff.
3. Apply inherit removal and pricing-input changes in one guarded batch, with
   a before/after check that the nine protected non-promotion inherits are
   unchanged and no promotion consumer is partially modified.
4. Keep the resulting batch separate from the clean master playtest baseline
   until Blackrobe reviews and authorizes the exact runtime candidate.

The pricing helper is already non-live and fail-closed: it adds
`1500 * promotion_tier` once to the pricing-only chain while preserving the
actual chain cost and the `C <= B` plateau. The helper's focused checks pass;
this report is the missing content-readiness gate, not an approval to apply it.

Input evidence:

- `docs/balance/PROMOTION_CARGO_BATCH_20260911.md`
  SHA-256 `c1ff762c69684cb136fa51f2dea818b957c6f4615244cbe2429882e7eff5bf62`
- `docs/audit/latest/astra_review_20260911/candidate_proposals.json`
  SHA-256 `17130024e8b175a34599f7ba28a445f06b1f00dd6b944a737b37c5bd06124744`

No YAML, cost, prerequisite, runtime, build, launch or merge action occurred.
