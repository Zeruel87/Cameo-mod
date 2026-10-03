# Weapon follow-up review, 2026-09-05

Base: upstream master `4deaee086`, seven commits after PR #320. The existing
`codex/weapon-balance-followup` branch was fast-forwarded with its three local
documentation/test edits preserved. No gameplay redesign is included.

## Corrections to the earlier discussion

- `review_batch_diff.py` already compares resolved `Versus`, `PercentageVersus`,
  percentage applications, targeting, projectiles and both physical-state binding
  forms. Armor-profile changes fail its comparison. The earlier claim that this
  tool ignores armor was wrong; the older `review_resolve_diff.py` is narrower.
- The pricing implementation is not wholly blind to firepower. `fit_class.py`
  applies the extracted local unconditional multiplier. Extraction does not model
  every inherited unconditional multiplier, and physical-state pricing selects the
  strongest binding rather than summing all delivery. These need separate pricing
  investigation; they do not authorize repricing actors in this follow-up.
- A shared armor table alone does not establish an exact fold: targeting,
  relationships, geometry, state, rounding and delivery must also agree.
- The previous Marine comparison omitted its permanent 31% burst compensator.
  Corrected flat damage ratios depend on armor: roughly 1.9x against Flak is not
  a claim that Hydra is 2x Marine against all targets or in actual combat.

## Work retained and continued

Sol's held-weapon fingerprints and actor Armament fingerprints strengthen the
review boundary. They do not pin all replacement weapon bodies or intermediate
delivery weapon bodies. Hydra retains four 18,000 mains and its existing actor
stats. Its regression now explicitly acknowledges both existing Corrosion routes.

The physical-state audit now enumerates both enabled runtime routes, reports
duplicate bindings and computes their combined nominal scale. It preserves each
application in diagnostics because runtime rounding and state clamping happen
separately. Zero bindings are inactive. The current content produces 216 findings;
these are exposed as FAIL, with no exception list or silently increased threshold.
Gameplay correction requires deciding the intended state delivery for each family,
especially unequal-scale cases; mechanically deleting either route is not justified.

Upstream changed ArcherArtilleryShell targeting/projectile fields and the Ordos
autogunturret's projectile streak fields. Their generated fingerprints are refreshed
to the merged upstream definitions, not used to authorize additional changes.
Raw/derived ledger and survey refreshes record upstream's other weapon/actor changes.

Hydra's gameplay redesign is not implemented. Pricing, actor costs and game launch
remain outside this local tooling change. Blackrobe subsequently authorized the
offline experiment and a draft tooling/evidence PR, not a gameplay release or merge.
The state audit is deliberately failing
until its content findings have a reviewed resolution.

## Developer-chat clarification supplied by Blackrobe

Aedis describes a cross-game reference model: normalize unit statistics within
classes and whole games using several summary statistics, then synthesize reference
factors with a geometric mean. This is a proposed design target, not proof that an
existing Cameo weapon can be folded without changing behavior. The supplied chat
does not specify the ten factors or their weights sufficiently to validate the model.

His chemical-bullet proposal combines bullet and chemical armor profiles.
The generator actually starts by averaging the parent Versus rows, then applies
its profile rules; the chat's multiplication wording is not the literal algorithm.
That defines a new counter profile; it is not generally equivalent to the weighted
sum delivered by Hydra's four current mains. Even where a flat armor table agrees,
percentage damage, physical-state delivery and firing behavior need separate checks.
The proposal can be considered as an intentional redesign, but this chat alone is
not authorization or evidence to implement it. The current no-change boundary holds.

PR #321 is still open at e42eb9914972346f77a931385da62d741f22ae35.
Its file set overlaps this refresh in four raw/derived ledger files; these should be
regenerated after any eventual integration. No PR changes or merge were performed.

## BulletChem: useful concept, unsuitable unchanged patch

The fetched PR #325 head e42eb991 contains the actual proposal in
`docs/patches/01_bulletchem_hydraspit.patch`, not active gameplay YAML. No patch was
applied. It adds a generated BulletChem family, puts Hydra's entire 72,000 raw
damage on it, and folds percentage damage into that main.

This is a useful third option between retaining four profiles forever and forcing
Hydra into pure Chemical. It makes a corrosive projectile role explicit and retains
the travelling spore rather than adopting the hitscan Bullet projectile. But its
unmodified magnitude is not suitable as a neutral cleanup or a damage reduction.

Nominal flat damage (Versus only, before actor multipliers, falloff, target defenses,
rounding, and percentage damage), independently checked against current resolved
Hydra and the staged template:

| Armor | Current four mains | Proposed 72,000 BulletChem | Ratio |
|---|---:|---:|---:|
| None | 51,480 | 137,520 | 2.67 |
| Flak | 51,480 | 111,600 | 2.17 |
| Heavy | 41,760 | 65,520 | 1.57 |
| Fighter | 39,600 | 67,680 | 1.71 |

No single raw damage value preserves these matchups: matching Flak needs roughly
33,213, while matching Fighter needs roughly 42,128. This is evidence for selecting
an explicit role, not a recommendation to use either number. At the Flak anchor,
Fighter damage would fall about 21%; a generic damage reduction does not automatically
meet the requested infantry-and-air role.

The staged notes report a nominal None percentage coefficient increase from 0.45%
to 4.32% of max HP. Their suggested PercentageScale 1042 is at most a None anchor;
the changed armor tables and integer rounding prevent exact universal equivalence.
Corrosion also needs a separate budget: current singular and mapped applications
both execute, while the new family has one 20% mapped route on a much larger hit.
The notes' single corrosion ratio is not sufficient across armor, HP and distance.
Their claim that DamagesConcrete 100 is new is stale: current resolved Hydra already
has Warhead@Concrete with Damage 100.

### Proposed sequence, not an approved gameplay edit

1. Keep current Hydra as the control. Preserve cost, HP, movement speed, range,
   reload, projectile travel and visuals throughout this weapon-only evaluation.
2. Build an offline BulletChem candidate worksheet from the staged family. Compare
   infantry, armor and air separately, with representative real actors, HP and
   distance; show flat damage, percentage damage and corrosion independently.
3. Select the intended role and acceptable matchup tradeoffs before selecting raw
   damage. Do not use 72,000 merely because it is the old sum or use a global armor
   average as a substitute for those decisions. Keep percentage/state calibration
   separate from the flat-damage choice.
4. If approved, implement a scoped candidate with resolved-inheritance regression
   tests. Audit all other generated families: adding this family re-ranks derived
   armor rows, so the staged patch has effects beyond Hydra. Preserve reviewed
   exceptions in raw inventories and replace Hydra's guard only with explicit approval.
5. Run small sequential test modules under a memory limit, then seek explicit
   permission for gameplay testing. No game launch or publication is implied.

The full discovery run reported 727 tests, 11 skipped and three upstream-staleness
failures before its process was stopped following Blackrobe's RAM warning. This is
not an all-green full-suite result. Follow-up validation uses focused modules;
do not rerun unchanged discovery until its memory retention is addressed.

Independent review found no blocking tooling issues. Its BulletChem challenge also
identified existing Shield rows changing by three in the patch, beyond the README's
description of +/-1 derived armor changes. Regenerated reviewed fingerprints record
those changes; they do not prove neutrality.

Earlier focused validation: 32 tests covering the three stale-upstream failures passed
sequentially, plus eight new state-binding tests passed. PR #320's historical
comparison artifact remains unchanged, with its provenance tested separately from
the refreshed upstream snapshot. All 32 balance ledgers match live rules; canonical
extraction, structure inventory, decision bundle, percentage-runtime and diff checks
pass. The full resolved comparison against an exported HEAD checks 2,349 weapons
with no changes. The physical-state audit honestly remains FAIL with 216 findings.
The decision queue remains 14 reachable holds and 100 unreached stacked definitions.

## Subsequent bounded validation and publication scope

The completed isolated-module run supersedes the earlier failing discovery result:
78/78 modules completed, 748 tests run, 737 passed, 11 skipped, zero failed modules.
Each module ran in a fresh sequential process. The sampled largest process tree was
1366.2 MB and sampled whole-PC memory peaked at 49.1%, below the 88% guard threshold
and Blackrobe's 90% ceiling. See `docs/audit/latest/bounded_test_run.json` for per-module
results. This is not a claim that unchanged one-process discovery is memory-safe.

The new [recommendation](HYDRALISK_RECOMMENDATION.md) and
[ordered-impact experiment](HYDRALISK_IMPACT_LAB.md) supersede the nominal screen as
the richer, still offline, assessment. Independent review approved this tooling/evidence
scope. Blackrobe authorized a draft PR; no gameplay, price, cost, engine or asset edits
are included, and no game launch or merge was performed.
