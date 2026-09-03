# Effective damage — the area-integrated weapon metric (spec, rev. 2026-08-11)

Tool: `tools/balance/effective_damage.py` (read-only) · written into every ledger by
`tools/balance/extract_stats.py` · tests in `tools/tests/test_effective_damage.py`.

> ⚠ **Two different things in this repo are called "effective damage".** See §1
> before using either. This document is about the **area-integrated metric**.

---

## 0. Why it exists

Raw `Damage` is not comparable across weapon types. A railgun that puts 20 000 into
one hitbox and a nuke that puts 20 000 into a 4-cell blast have the same number and
wildly different battlefield value. Before this metric the pipeline priced on
`Σ Damage / reload`, which meant:

- **AoE was free.** Spread and Falloff cost nothing, so wide warheads were underpriced
  and single-target energy weapons were overpriced.
- **Accuracy was free.** A slow, inaccurate mortar and a hitscan laser of equal `Damage`
  priced identically, though the mortar frequently misses a moving target.
- **The 3-axis Spread/Falloff work had no price signal.** `SPREAD_FALLOFF_PLAN.md`
  makes the falloff SHAPE a design axis; nothing turned that shape into a number.

The metric folds all three — **how much**, **over what area**, **how often it lands** —
into one comparable scalar, so the class anchors can be fitted across weapon families
instead of within them.

## 1. ⚠ The name collision — read this first

| | **A. "effective damage per shot"** | **B. `effective_damage` (this doc)** |
|---|---|---|
| Defined in | `LESSONS_LEARNED.md` §Uniqueness | `tools/balance/effective_damage.py` |
| Formula | `Σ(main warhead Damage) × FirepowerMultiplier` | `Σ base × (reliability + SWARM_W × footprint)` |
| ExtraDamage chips | **excluded** (paid for by K / charge delay) | **included** |
| FirepowerMultiplier | **applied** | **not applied** (actor-level, not weapon-level) |
| Used for | uniqueness rule #3 (5 stats per class) | ranking / pricing input (**not yet wired**) |

They are **not interchangeable**. A ledger row's `effective_damage` must never be fed to
the uniqueness audit, and the uniqueness stat must never be called `effective_damage` in
code. When in doubt, say "uniqueness damage" for A and "area-integrated damage" for B.

## 2. The formula

```
effective = projectile_impacts × Σ over (main + every *_ExtraDamage)
            base × ( reliability + SWARM_W × footprint )

  footprint   = 2π ∫ (F(r)/100) · r dr / 1024²                     [cell²]
  reliability = E[ F(miss distance) ] over the engine's scatter     [0 … 1]
  σ           = Inaccuracy + LEAD × TARGET_SPEED × Range / min(Speed, SPEED_CAP)
  area defaults: Spread 43 ; Falloff "100, 37, 14, 5, 0"
```

Constants (all at the top of the tool, all tunable):

| constant | value | meaning |
|---|---|---|
| `SWARM_W` | 0.25 | **target density, in units per cell²** — see §2.3 |
| `LEAD` | 0.20 | the engine leads/tracks, so real miss ≈ 20 % of raw displacement |
| `TARGET_SPEED` | 100 | a typical dodging vehicle, WDist/tick |
| `SPEED_CAP` | 10000 | ≥ this a projectile is "basically instant" (~10 cells/tick) |
| `DEFAULT_AREA_SPREAD` | 43 | runtime default when an area warhead omits Spread |
| `DEFAULT_AREA_FALLOFF` | 100, 37, 14, 5, 0 | runtime default when an area warhead omits Falloff |
| `POINT_TARGET_RADIUS` | 100 | synthetic radius used only for point-target reliability |

### 2.1 footprint — "how much ground does this cover"

`F(r)` is the piecewise-linear falloff curve the engine actually evaluates. Integrating
`F(r)·r dr` in polar coordinates gives the **damage-weighted area**: a disc that takes
full damage everywhere contributes its whole area, a cone that decays to zero
contributes less than its outer circle. Dividing by `1024²` puts it in **cells²**, the
unit a designer can picture.

Sanity check (pinned by a test): `Falloff: 100, 100` over `0…1024` gives exactly π cell²
— the area of a 1-cell-radius circle.

### 2.2 reliability — "does it land on the guy you aimed at"

The probability-weighted falloff value at the impact point, for a **single point
target**. `σ` has two terms:

- **`Inaccuracy`** — the weapon's own scatter, straight from the projectile.
- **travel drift** `LEAD × TARGET_SPEED × Range / Speed` — a slow projectile at long
  range gives the target time to walk out of the blast. Dimensionally: (WDist/tick) ×
  WDist / (WDist/tick) = WDist. ✔

MiniYAML does not materialize C# defaults. An ordinary `Bullet` with no authored
`Speed` therefore uses the runtime default 17 rather than becoming an instant hit.
`ScaledBullet` likewise starts from 17/0 and applies its range-percentage speed and
inaccuracy derivation before this calculation.

Missiles use the runtime default speed of 384. An always-locking missile uses
`LockOnInaccuracy` when it is non-negative, matching the value selected by the engine
before the offset is calculated. A lock probability from 0 through 98 mixes tracked and
untracked trajectories, so that row is explicitly provisional rather than assigned a
guessed average.

**Instant does not mean perfectly accurate.** `InstantHit`, the fake-bullet hitscan,
and `Railgun` have no travel drift but retain authored `Inaccuracy`; their positional
impacts still sample the warhead falloff. `TargetActorCenter` hitscans bypass scatter on
an ordinary valid actor target, while a tracking `LaserZap` replaces its initially
scattered point with the live target position. Support-power instant explosions use the
authored center falloff rather than an automatic 1.0. Projectiles with no known scalar
speed keep authored scatter, add no guessed travel drift, and are marked provisional
when their trajectory is known to need a richer model.

**The scatter distribution matches the engine, not a convenient approximation.**
`Bullet.cs` does `target += WVec.FromPDF(rng, 2) * maxInaccuracy / 1024`, and
`WVec.FromPDF(r, 2)` draws **each axis** as the sum of two uniforms — a *triangular*
density on `[-σ, σ]`. Hits therefore cluster near the aim point:

| model | mean miss radius | P(miss < σ/4) |
|---|---|---|
| engine (2-axis triangular) | **0.52 σ** | **15.7 %** |
| uniform disc (the old approximation) | 0.67 σ | 6.2 % |

The tool integrates against the real density. Using a uniform disc — as the first
revision did — throws ~28 % of hits too far out and **systematically under-values
inaccurate and slow weapons**. Fixing this moved 1 950 of 2 024 ledger rows up, median
**+4.9 %**, max **+167.8 %**.

### 2.3 `SWARM_W` — what the 0.25 actually means

`reliability` is a probability and `footprint` is an area, so adding them looks
dimensionally wrong. It is not, once `SWARM_W` is read as its true meaning:

```
effective / base  =  P(hit the primary target)  +  E[number of SECONDARY targets caught]
                  =  reliability                +  density × footprint
```

`SWARM_W` is a **target density in units per cell²**. `0.25` = one unit per 4 cell² = a
unit every 2×2 cells, i.e. a moderately packed formation. That is the knob to turn if
AoE feels over- or under-valued, and it has a physical meaning you can argue about:

- raise it toward `0.5` if you want blob-clearing weapons to price higher;
- lower it toward `0.1` to model spread-out armies where splash rarely multi-hits.

## 3. What the per-shot metric keeps separate

| input | treatment | consequence |
|---|---|---|
| `ReloadDelay`, `Burst`, `BurstDelays` | cadence is separate from the per-shot result | `effective_dps = effective_per_shot × burst / eff_reload`; every burst gap is counted and a missing delay uses the engine default of 5 |
| `FirepowerMultiplier` | actor-level, and one weapon serves many actors | multiply at the actor, as `fit_class.py` already does |
| `WeaponClass` (0.75/1.0/1.25/1.5) | **RETIRED from pricing entirely (W4)** | `formula.dps()` no longer takes it; K measures weapon quality directly |
| `Versus` / armor profile | resolved from each live warhead | folded into K as `avg_versus`, weighted by the measured armor census |
| percentage damage | discovered by runtime warhead type, not tag suffix | folded damage joins the scalable coefficient; standalone damage becomes an additive reference-HP floor |
| projectile-internal impacts | `AreaBeam` and `LaserZap` apply every warhead at their damage intervals; `LightningZap` applies them during its damage-active ticks | count those applications before ordinary Burst/reload cadence |
| `*FriendlyFire` twins | baked own-side splash, never a benefit | correctly ignored |

### 3.0 The context factors (W5, 2026-08-11) — no longer excluded

`ValidTargets` and `MinRange` used to sit in the table above. They are now measured,
each as a **separate named factor** rather than one blended fudge, so a price that
moved can be traced to the single factor that moved it:

| factor | models | shape | example |
|---|---|---|---|
| `targets` | `ValidTargets` — a weapon that cannot hit air fights less of the game | `FLOOR + (1-FLOOR) x engagement share`, `TARGETS_FLOOR = 0.5` | ground-only **0.95**, AA-only **0.55** |
| `range` | outranging is worth more than DPS | `1 + 0.25 x (range/median - 1)`, bounded `[0.75, 1.50]` | median range 1.00, long artillery **1.33** |
| `deadzone` | a `MinRange` hole costs the annulus you cannot cover | `1 - (MinRange/Range)²` (area, not radius) | MinRange 2800 / range 11000 → **0.96** |
| `overkill` | DPS ignores waste — a 200k burst on a 50k target throws away 75% | `HP / (ceil(HP/dmg) x dmg)` — waste is only the LAST shot | 200k on 50k → **0.25** |

**The split that matters.** `targets`, `range` and `deadzone` do **not** depend on
`Damage`, so they fold into **`k_flat_context`** and the pricing inversion stays closed-form:

```
Damage_required = (target_per_shot - pct_absolute_context) / k_flat_context
```

**`overkill` does** depend on Damage — it compares per-shot damage against target HP.
Folding it into K would turn that exact inversion into a fixed-point iteration, so it is
reported **beside** K and never inside it. `tools/tests/test_weapon_context.py` pins
this distinction; if you ever fold `overkill` in, the inversion must become iterative.

⚠ **Percentage damage has two runtime shapes, and only one is additive** (E4, corrected
2026-08-25). A standalone `AreaDamagePercentage` / `HealthPercentageDamage` warhead is a
share of the TARGET's max HP independent of the weapon's flat `Damage`; it belongs in
`pct_absolute_context` and creates a real floor. The `PercentageScale` fields folded into
an `AreaDamage` warhead derive a second hit from that SAME warhead's `Damage`; they reach
zero with it and therefore belong in `k_flat_context` when the current runtime invokes
them. The engine rounds the folded hit to basis-point units using unchecked Int32
arithmetic. The difference between the continuous coefficient and current runtime output
is published separately as `folded_rounding_context` and recomputed after snapping a
proposed Damage value. Overflow can make this residual large and non-linear; those rows
are marked provisional. `k` and `k_context` remain measurement forms and must not be
inverted. Guard: `tools/audit/audit_k_linearity.py`.

The current direct-Actor `AreaDamageWarhead` path invokes its flat `InflictDamage` method
but skips the folded `PercentageScale` second hit. The model mirrors that shipped behavior:
direct hits keep flat and standalone percentage applications, but do not price a folded
application that the game never executes. This is recorded as a separate runtime repair
candidate, not silently assumed by the balance pipeline.

`Ticks` and expanding `MinRadius`/`MaxRadius` are also evaluated one application at a
time. Each tick gets its own integer damage share and current ring radius; applying the
final falloff curve once to the whole attack overprices expanding shockwaves.

Direct-Actor geometry means the warhead's `Spread`, `Falloff`, and `Ticks` are bypassed;
for the current folded-percentage omission see above. It does not mean that a projectile
only invokes the warhead once. `AreaBeam` calls the active warhead path repeatedly while
the target remains on the beam. A stationary target exposed
for the whole uninterrupted beam receives `Duration / DamageInterval` impacts on
average. The exact count is the adjacent floor or ceiling when those fields do not
divide evenly, because it depends on travel-tick phase; moving, blocking, stopping, and
hit-shape width can shorten or extend the live exposure. A tracking beam refreshes its
line from the selected actor before searching the line, so initial scatter and travel
drift do not reduce that actor's ordinary direct hit. An untracked beam keeps the moving
projectile reliability approximation. The active percentage-bearing beams divide their
cadence evenly, making the published per-target full-exposure factors exact; their extra
line catches remain provisional.

`LightningZap` has a different repeated-hit rule. It invokes the warheads once per
damage-active tick, exactly `max(min(DamageDuration, Duration), 0)` times. This multiplier
is modeled directly, including zero-duration and clipped-duration cases.

`LaserZap` and `LaserZapCA` impact at tick zero and then every `DamageInterval` while
`ticks < DamageDuration` and the projectile remains alive. Their exact ordinary count is
modeled, including non-positive intervals (which impact every eligible tick). A `HitAnim`
can keep the projectile alive beyond `Duration`; if its authored damage window extends
into that unknown animation lifetime, the row is marked provisional rather than guessing
the sequence length.

Likewise, `TargetActorCenter` hitscans use the direct path only for an ordinary valid,
unblocked actor target. If the target becomes invalid, or a blockable shot meets a
blocker, the engine converts the impact to a position and warhead area geometry applies.
The pricing model describes the ordinary successful target hit.

Multi-actor line projectiles are only partly modeled today. `AreaBeam`, line-damaging
railguns, and shaped `LinearPulse` projectiles use the correct direct warhead invocation,
and AreaBeam's per-target cadence is counted, but their beam/line/cone secondary catches
and projectile-level falloff are not yet priced. Such derived rows carry a
machine-readable `model_limitations` entry and `model_status: provisional` so consumers
cannot mistake the number for complete projectile output.

`SpriteAthenaLaser` is also explicit rather than silently wrong. It invokes its
warheads repeatedly while moving, so derived rows report a max-range
`nominal_projectile_impacts` count and carry cadence/geometry limitations. The total
corridor count is not multiplied into one target's K; when the authored interval makes
the count exactly zero, the damage multiplier is zero because no warhead is invoked.
Ballistic `GravityBomb` and `NukeLaunch` rows likewise carry a motion limitation instead
of pretending that an omitted scalar Speed makes them instant. Their projectile classes
do not own scalar `Speed` or `Inaccuracy` fields, so foreign keys left by inheritance are
ignored just as the runtime ignores them.

`TARGETS_FLOOR` exists because AA units are separately class-anchored: a raw
engagement share would price an AA-only weapon at 0.10 and penalise those units twice.
An exotic `ValidTargets` set with no `Ground`/`Air` token (`Infantry, Monster`) scores
1.0 — declining to judge beats guessing "hits nothing".

**`AttackDelay` — the fifth item — does not exist.** W5 listed it, but the field appears
**0 times** in the tree: charge-up is an ACTOR trait (`AttackCharged`, `AttackCharges`,
`AttackTesla`, …), and W4 implemented it there as a 0.75x price multiplier. Nothing to
add at the weapon level.

### 3.1 ⚠ The ExtraDamage contradiction (needs a maintainer ruling)

`formula.spread_damage_sum()` **excludes** `*_ExtraDamage` chips — DESIGN law:
"`*ExtraDamage` is ALWAYS excluded from the damage calculation", because the chip is
*paid for* by a structural handicap (Tesla's `K = 1.25`, Railgun's charge delay).

`effective_damage` **includes** them.

Both positions are defensible — a chip is real damage the enemy takes, so an
"effective damage" comparison that omits it is lying; but pricing it twice (once in the
chip, once in the handicap) double-charges the weapon. **They cannot both be right when
this column is wired into pricing.** Decide before that happens, and record it here.

## 4. Engine fidelity: the single-`Range` footgun

`AreaDamageWarhead` and upstream `SpreadDamageWarhead` both do:

```csharp
if (Range != null) effectiveRange = Range;                  // NO expansion
else effectiveRange = [i * Spread for i in Falloff];
...
int GetDamageFalloff(int distance) {
    var inner = effectiveRange[0].Length;
    for (var i = 1; i < effectiveRange.Length; i++) { ... }  // never runs when Length == 1
    return 0;
}
```

A `Range:` with a **single** value and a multi-step `Falloff` therefore makes the warhead
deal **zero damage at every distance**. The load-time validation accepts it (`Range.Length
== 1` is legal), so it fails silently.

The metric now mirrors this exactly rather than inventing a per-step grid. **See
`ROADMAP.md` for the live weapons currently hit by this.**

## 5. Status — where the numbers live, and what still reads them

`extract_stats.py` writes them to **`docs/balance/derived/<faction>.json`**, never to
the raw ledger (W3, 2026-08-11). One row per armament, joined back to the raw ledger by
`slot` + `weapon`:

| field | metric | meaning |
|---|---|---|
| `effective_damage` | area-integrated | per-shot damage integrated over the blast, after scatter |
| `damage_total` | — | Σ flat main Damage (the input the two metrics share) |
| `footprint` | area-integrated | damage-weighted area in cell² |
| `reliability` | area-integrated | P-weighted falloff at the impact point |
| `sigma` | area-integrated | scatter σ in WDist |
| `k` | **pricing (W1)** | the dimensionless coefficient — see below |
| `k_context` | **pricing (W5)** | measured `k × targets × range × deadzone`; not the invertible shape coefficient |
| `k_flat` / `k_flat_context` | **pricing (E4)** | scalable flat + chip + folded-percentage coefficient, before/after context factors |
| `pct_absolute` / `pct_absolute_context` | **pricing (E4)** | standalone percentage damage at the reference HP; the true additive floor |
| `folded_rounding` / `folded_rounding_context` | diagnostic (E4) | current runtime residual from basis-point rounding or Int32 wrap; absent when exact |
| `avg_versus` | pricing | prevalence-weighted mean Versus over the FLAT warheads |
| `factor_targets` / `factor_range` / `factor_deadzone` | pricing (W5) | the three context factors, individually inspectable (§3.0) |
| `overkill` | diagnostic (W5) | Damage-DEPENDENT, so reported beside K, never inside it |
| `projectile_impact_multiplier` | cadence | internal warhead applications per weapon fire; present when not 1 (for example an `AreaBeam` or `LightningZap`) |
| `nominal_projectile_impacts` | cadence diagnostic | max-range total corridor impacts for `SpriteAthenaLaser`; not folded into one-target K |
| `model_limitations` / `model_status` | diagnostic | explicit unsupported projectile contributions, such as line geometry, ballistic trajectories, or probabilistic missile lock-on; affected rows are provisional |
| `effective_per_shot` | pricing | `damage_total × k_flat_context + pct_absolute_context + folded_rounding_context` |
| `eff_reload` | pricing | reload plus every burst gap; missing `BurstDelays` uses the engine default 5 |
| `effective_dps` | pricing | `effective_per_shot × burst / eff_reload` |
| `dps_floor` | pricing (E4) | standalone `pct_absolute_context × burst / eff_reload`; folded damage is excluded |

Two metrics sit side by side on purpose — §1 warns they are not interchangeable, so
they keep distinct names instead of being blended into one number.

`effective_dps` is the **weapon's** number. `FirepowerMultiplier` is an actor property
and is deliberately not baked in; the caller applies it.

When `damage_total` is zero, a measured ratio such as `k` has no denominator and is
therefore undefined. The derived row keeps the standalone percentage floor, but leaves
the contaminated ratio fields empty instead of inventing a coefficient from division by
one.

`docs/balance/derived/_model.json` records the constants every one of these depends on
(`SWARM_W`, `LEAD`, `TARGET_SPEED`, the runtime area defaults,
`POINT_TARGET_RADIUS`, `A_BLOB`, `A_SELF`, `BLOB_UPTIME`, `DENSITY`, `ENGAGEMENT`,
`reference_hp`, the armor census). A retune therefore shows up
as a short readable diff at the top of the tree, not only as thousands of shifted
decimals underneath it.

`fit_class.py --use-k` reads `effective_dps`, and `--compare-k` produces a side-by-side
raw-versus-effective report without writing an anchor candidate. The default fit,
`apply_balance.py`, the proposal tools, and the workbook remain on the raw-stat path.
K-adjusted pricing is therefore available for review, but is not the default pipeline
until the maintainer signs off on the comparison.

### 5.1 The "RAW STATS ONLY" ledger law — restored

`BALANCE_PIPELINE.md` §2 is explicit: *"No DPS, no combined Damage, no
effective-anything in the JSON. Every number appears exactly as the yaml states it."*
For a few days it was broken: `c9a09dc91` wrote five derived fields into every ledger
row.

That was not pedantry. A derived field moves when the **model** changes, not when the
game does: fixing the scatter model on 2026-08-11 rewrote **4 136 ledger lines with zero
`mods/` changes**. The ledger's purpose is to prove yaml ↔ ledger equality
(`audit_balance_drift`), and mixing model noise into it made "did a real stat move?"
unanswerable by diff.

The split restores it, and the restoration is pinned rather than trusted:

- `extract_stats.build_ledgers()` returns the **raw** docs by construction, so the drift
  audit cannot start diffing model output by accident;
- `extract_stats.py --check` verifies both trees and labels each finding `DRIFT (raw)`
  ("the game changed") or `DRIFT (model)` ("a tool changed");
- `tools/tests/test_ledger_split.py` fails if any committed raw ledger regrows a model
  field — under the pre-split ledgers that guard trips on 310 rows.

The split commit itself is the proof of purity: **12 130 deletions, 0 additions**, every
removed line one of the five field names.

## 6. Roadmap for the metric

> **Status and ownership for every item below live in
> [`BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md) (W1–W12), not here.** W1 (the K
> coefficient, prevalence-weighted Versus and the capped density model) is **done** —
> `tools/balance/target_model.py` + `tools/balance/weapon_efficiency.py`. The list below
> is the original reasoning; the plan file is what to execute.

**The K coefficient (W1, done).** Because `effective` is linear in `base`, a weapon's
whole geometry collapses into one dimensionless number:

```
effective_per_shot = Damage_total × k_flat_context
                     + pct_absolute_context + folded_rounding_context
effective_dps = effective_per_shot × burst / eff_reload × FirepowerMultiplier
```

The scalable part of K never depends on the Damage magnitude, so pricing inverts exactly and
the grid is never violated — `Damage_required = (target_per_shot − pct_absolute_context) /
k_flat_context`, snapped to the grid. A workbook value of 2351.85 therefore never goes into
yaml: the designer sets geometry for feel, K measures it, the pipeline solves for Damage,
then recomputes the folded basis-point rounding at the snapped value.

⚠ A **standalone** percentage warhead is additive, so the model is affine and that term is
a true DPS floor: a weapon still delivers `pct_absolute_context` at `Damage: 0`. A target
below it is unreachable; `weapon_efficiency.required_damage()` returns `None` rather than a
wrong positive number, and `dps_floor` is published per weapon in the derived ledger. Folded
`PercentageScale` damage is different: it scales with the main Damage, lives in `k_flat`,
and contributes no floor. `audit_k_linearity.py` publishes the live counts for both shapes.

**Secondary targets (W1, done).** `secondary = ρ_class × BLOB_UPTIME × (min(footprint,
A_BLOB) − A_SELF)`. `ρ` is per macro class (INF 2.0 / VEH 0.33 / BLD 0.25 / AIR 0.20 units
per cell²) so anti-infantry splash legitimately catches more bodies; `A_BLOB = 9 cell²`
caps a superweapon-sized blast from claiming 50 kills; `A_SELF = 1 cell²` stops the aimed
target being counted twice. `BLOB_UPTIME = 0.30` is the fraction of shots that actually
land in a crowd — without it every splash family scored ~5× every single-target family.
Completed foundations: the ledger publishes a full-cycle rate, armor prevalence weights
the Versus profile, and `fit_class.py` can compare the raw and K-adjusted paths without
changing the default.

1. **Decide §3.1** (chips in or out) before making K-adjusted pricing the default.
2. **Calibrate `SWARM_W` from the game**, not from taste: measure the mean number of
   actors inside a 1-cell² disc in real engagements and set the density from that.
3. **Model `TARGET_SPEED` per victim class** rather than one global 100 — a Harvester and
   a scout bike do not dodge alike; the drift term is linear in it.
4. **Review the existing `--compare-k` reports class by class**, then switch the default
   only after the resulting prices receive maintainer and multiplayer sign-off.

## 7. Reading the numbers

```sh
python tools/balance/effective_damage.py --top 40      # ranked table
python tools/balance/effective_damage.py NAME [NAME…]  # specific weapons
```

Diagnostics per row: `base` (raw sum), `reliab` (0…1), `footprint` (cell²), `sigma`
(WDist). Useful shapes:

- `reliab` far below 1 on a weapon that should be accurate → check `Inaccuracy` / `Speed`.
- `effective` well below `base` → the warhead is barely landing, or it is a **dead**
  warhead (§4).
- `footprint` ≈ 0 on something that should splash → `Spread` or `Falloff` is wrong.

Related: [`BALANCE_PIPELINE.md`](BALANCE_PIPELINE.md) · [`FORMULA_V2.md`](FORMULA_V2.md) ·
[`SPREAD_FALLOFF_PLAN.md`](SPREAD_FALLOFF_PLAN.md) · [`WEAPON_3WAY_SPLIT.md`](WEAPON_3WAY_SPLIT.md)
