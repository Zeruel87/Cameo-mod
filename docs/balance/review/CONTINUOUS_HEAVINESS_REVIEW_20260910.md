# Continuous weapon heaviness: design and implementation review

## Assessment

Scope: this is the review of upstream `50b7d001b`, not a status report for the
separate continuous-heaviness implementation branch. Aedis explicitly confirmed
at 01:19 that actual roster-weighted Versus, percentage damage and splash must
enter pricing; the former unweighted-total argument does not imply constant price.

One family profile plus a continuous heaviness parameter is a coherent replacement
for repeated Light/Medium/Heavy templates. It separates weapon identity from a coarse
level label and can avoid adding two damage profiles merely to represent an intermediate
level. However, the present implementation is not a complete implementation of the
requested design, and its audit does not establish the claimed price invariance.

The review originally paused W24 conversion drafts pending design clarification.
Aedis subsequently requested implementation and activation at 00:40, then confirmed
continuous interpolation at 00:51. The next step is a tested runtime/tool contract
and scoped activation, not immediate global template deletion. Existing percentage
endpoints are provisional initial anchors, as acknowledged at 00:59; no new numeric
endpoint values were selected. This report itself does not apply gameplay changes.

## Current evidence and scope

This review uses upstream `50b7d001be845e0ac5a0812d2591e154148c94dc`, refreshed on
10 September 2026. The active resolved Cameo weapon inventory contains **zero explicitly
configured Heaviness nodes**. The C# mechanism exists but is inactive for current authored
weapons; the generator selects the old discrete tilt unless `CAMEO_HEAVINESS_BELL=1`.
These are deployment facts, not evidence that the new design is invalid.^1

The binding specification is DESIGN §12.0i and the later rulings in WEAPON_HEAVINESS §9.
The latter document also retains extensive superseded measurements, including a broken
Versus parser, additive offsets and older axis proposals. Those passages are historical
evidence, not competing active requirements. Its final build-order prose still says
implementation is next even though the preceding table records an implemented, inactive
C# mechanism; that status wording needs reconciliation.^2

Aedis's 10 September request additionally calls for percentage magnitude and splash to
grow with heaviness, while the armor profile shifts toward heavier targets. This review
treats that as current implementation direction and identifies older statements that
need reconciliation. The 00:49 acknowledgement records the working pricing interpretation:
no separate surcharge, but actual resulting damage and geometry enter the normal formula.

## Findings

### 1. Constant arithmetic mean does not prove constant price

The C# transform normalizes `tiltable.Values.Average()` against the transformed values'
arithmetic average. The generator likewise uses `statistics.fmean`. The audit compares
`statistics.mean` before and after but labels the result **weighted-mean drift**. None
of these checks uses the actual target-population weights used by effectiveness pricing.^3

A permutation preserves an unweighted multiset average. It does not generally preserve
a weighted average when the weights remain attached to armor identities. For example,
values 50 and 150 have mean 100; with target weights 90% and 10%, their expected value
is 60. Exchanging their positions preserves mean 100 but changes the weighted result to
140. Thus the specification's claim that rank restoration preserves the weighted mean
requires qualification even before geometry and percentage damage are considered.

An independent read-only calculation with the existing Python bell produced these
Heavy-armor coefficients on the same input profile:

| family | h=0 | h=1 | h=2 |
|---|--:|--:|--:|
| CannonAP | 124.219 | 133.775 | 148.079 |
| Bullet | 58.351 | 66.432 | 72.701 |
| Flame | 58.468 | 66.039 | 65.656 |

These are profile-transform examples, not measured in-game DPS or final generated
templates. A target population concentrated on Heavy armor plainly does not see
invariant damage. The Flame example also shows that a heavyward tendency does not
guarantee every individual armor coefficient increases monotonically.

**Recommendation:** interpret “free of price” as **no additional heaviness surcharge**,
not an invariant final price. Retain a stable, documented profile-normalization basis,
then extend and verify the existing effectiveness/pricing path to account for the actual
resulting damage, percentage channel and geometry. Current runtime-bell parity is not
implemented. Joint fitting may adjust stats and cost afterward. Do not compensate with
a second tier multiplier for effects already measured by the formula. Aedis was asked
to confirm this distinction at 00:19.

### 2. Percentage redistribution is not percentage growth

The runtime transforms and renormalizes the percentage armor table separately. It does
not add an overall growth function to `PercentageScale` as h increases. By contrast,
today's discrete generator supplies different percentage bands for different levels:
ordinary sloped profiles use top values 16, 20 and 25 for Light, Medium and Heavy.
Sonic and Magic have their own authored level tables.^4

Collapsing those tables into one base plus a bell therefore loses an independent
magnitude relationship unless it is explicitly represented. A scalar ratio alone cannot
exactly reproduce all of the old additive band shifts: a low-ranked cell and a high-ranked
cell do not grow by the same proportion. This is a design choice, not a reason to retain
all historical tables forever.

**Decision required:** define the percentage-growth function and endpoints independently
from the armor tilt. Specify whether preserving selected old endpoint outputs or adopting
a new consistent curve takes precedence. Test it on both low-HP and high-HP targets;
a percentage increase changes those matchups differently.

### 3. Splash growth is a real power change

The runtime computes spread scale `(h + 2) / 3`: a Medium-sized base theoretically becomes
2/3 radius at h=0 and 4/3 at h=2. Doubling radius quadruples the area of a circular footprint;
that is not a claim of exactly four times damage in a match, because unit density, target
size, falloff and scatter matter. It does establish that constant center-hit flat damage
does not establish constant effectiveness.^5

Explicit warhead `Range` arrays remain authored rather than scaling with effectiveSpread.
Expanding effects can instead take their outer radius from MinRadius/MaxRadius. Consequently,
the current spread multiplier is not a universal radius multiplier for every AreaDamage
configuration. Those shapes require an explicit policy and regression coverage before
claiming uniform continuous scaling.

**Recommendation:** preserve delivery/effects independently; enumerate which damage-shape
fields scale. Keep point-like and special shockwave cases visible. Price the measured
resulting footprint instead of assuming the shape change is free.

### 4. The active light endpoint is currently unrepresentable

`Heaviness=0` means disabled and takes the authored profile/spread unchanged. But the
mathematical h=0 endpoint should apply the bell and the 2/3 spread factor. A small positive
value uses that transform, so zero is not continuous with its positive neighborhood.
The current field description acknowledges zero as disabled; this is a migration contract
gap, not a hidden live regression.^5

**Recommendation:** give disabled/unset state a distinct representation from active h=0,
and validate the supported range. Preserve old weapons when the field is omitted. Decide
Trace and Super separately; the existing documentation already says they are outside the
implemented Light/Medium/Heavy range. Do not invent their endpoints during a bulk migration.

### 5. “Heavyward” and “never flatter” need precise meanings

The current binding rule preserves each family's armor ordering through rank restoration.
For an anti-light family, transferring relative effectiveness toward heavy armor while
remaining anti-light necessarily reduces some light/heavy ratios: that is flattening in
that limited sense. It is not the same as making every family a generic equal-damage weapon.
For an already anti-heavy family, the same tendency can sharpen its specialization.^2

**Recommendation:** preserve family role and bounded differentiation, not a blanket
“never flatter” condition. Check ratios and representative counters, not merely whether
the largest coefficient remains largest. State whether monotonic movement is required
for each individual armor coefficient or only the overall tendency. Rank-restored bell
examples show that these are different promises.

### 6. Runtime and balance tools must share the same effective profile

The runtime applies the bell inside AreaDamage rules loading. The current effectiveness
tools read authored resolved YAML and do not apply that runtime transform. That is harmless
while no live weapon enables it, but enabling h without updating the pricing/evidence path
would make tools evaluate a different profile and geometry from the game.^1,3

The generator's optional bell is not a substitute for that runtime parity. Baking a bell
into a base template and applying the runtime bell again would compound the transform.
Choose one untilted family base and one transformation point; do not silently double-apply
the tilt. Exact equivalence to all old level templates is not promised by the current bell,
because old levels also change other profile-generation inputs.^2

## Recommended sequence

1. Resolve pricing meaning, percentage growth, active-zero semantics and the intended
   differentiation guarantee. Record the current decisions above historical prose.
2. Specify one stable base-profile representation and shared effective-profile calculation
   for runtime and tools. Keep existing weapons inert by default during implementation.
3. Add differential tests for all h endpoints, intermediate points, flat/special families,
   explicit radii, rounding, percentage damage and rank restoration. Include weighted
   matchup effectiveness as a measurement, not a false invariant.
4. Pilot a few contrasting families with explicit before/after damage matrices and a small
   runtime test. Only then remove obsolete level templates and expand W24 migration.

This retains the useful simplification without claiming that a structural collapse alone
preserves balance. Existing W24 decisions should be reconsidered under the agreed base/h
contract before publication; no template deletion is justified merely by this review.

## Sources

1. Active `mods/cameo/mod.yaml` inheritance inventory at `50b7d001b`;
   `tools/balance/gen_weapon_template.py`, `USE_BELL`; resolved inventory read on 10 September.
2. [DESIGN §12.0i](../../DESIGN.md), and
   [Weapon heaviness §9](../../design/WEAPON_HEAVINESS.md), including supersession notes.
3. `OpenRA.Mods.Cameo/Warheads/HeavinessBell.cs`, `Transform`;
   `tools/balance/gen_weapon_template.py`, `heaviness_bell`;
   `tools/audit/audit_heaviness_bell.py`, `belled` and `main`;
   `tools/balance/weapon_efficiency.py`.
4. `tools/balance/gen_weapon_template.py`, `LEVELS`, `FLAT_PCT`, `MAGIC_PCT`,
   and standard-family percentage-table generation.
5. `OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs`, rules loading, `effectiveRange`,
   shockwave outer-radius selection and percentage-radius gating.
