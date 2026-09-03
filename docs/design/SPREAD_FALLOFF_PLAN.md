# Spread + Damage-Falloff balancing plan (draft 2026-08-08)

Purpose: a principled, per-(damage-type × class) scheme for `Spread` and `Falloff`, accounting for
projectile speed and air-capability. Draft for review — numbers are a starting proposal derived from
the method; the METHOD is the point.

> **✅ AUTHORING MODEL DECIDED (maintainer, 2026-08-08): FULL per-type physics curves.** Every damage
> TYPE gets its OWN unique, physics-derived falloff curve — **§8 is the authoritative per-type spec**
> (convex ~1/r for HE, very-convex for demolition, broad long-tail for concussion, concave zone for
> flame, even wave for sonic, pinpoint `100,0` for kinetic/beam, expanding rings for nuclear). The
> simpler alternatives kept below for reference only and NOT adopted: the single-knob `100,0`
> everywhere (§1a) and the 3-shape menu {Linear/Punchy/Flat} (§1a table). Implementation: per-family
> `spreads`/`falloffs` overrides in `gen_weapon_template.py` → `splice_templates.py` → boot-gate.

> **✅ BUILT 2026-08-22.** §8 is live: `PHYSICS_SHAPES` in `gen_weapon_template.py` holds the
> per-type radius + curve, `LEVEL_RADIUS_SCALE` scales the radius by level without touching the
> shape, and `blend_shape()` crosses a blend family's shape from its parents' (geometric mean of
> the radii, arithmetic mean of the curves) exactly as `blend_versus` already crossed their armor
> profiles. Measured effect: **10 distinct falloff curves → 24**, and the flat tier where 23
> different Heavy families all sat at Spread 800 / radius 4000 / `100,50,25,10,5,0` — Melee,
> Arrow, PhotonCannon, Sonic, Flame, CannonNuke alike — is gone. `review_batch_diff`: main damage
> preserved on all 2325 weapons, blast shape changed on 1467.
>
> **UNIQUENESS PASS 2026-08-22** (maintainer: *"every family needs to be unique as fuck"*). The
> first pass was not enough: **13 families were still pairwise IDENTICAL** in radius and curve,
> because every pinpoint weapon had collapsed onto `100, 0` at one of a handful of radii. The
> kinetic/beam tier is now a ladder of real lateral energy spread — Sniper 40, Laser 48,
> MissileAP 64 (a shaped-charge jet is narrow and deep), Railgun 72, Arrow 88, Magic 96,
> Bullet 100, CannonAP 120, Melee 0 — and three families earn their own curve because they have a
> genuine secondary spread: Tesla `100, 55, 0` (the arc jumps to nearby conductors), Prism
> `100, 40, 0` (refraction halo), MissileAA `100, 70, 30, 0` (a proximity fuze never touches the
> target). **Flak** becomes airburst shrapnel, `100, 58, 32, 16, 6, 0` at radius 550 — a sharp
> drop off the detonation point and a long fragment tail, distinct from Concussion, which is the
> same physics at ground level and twice the size.
>
> ⚠ **`ENERGY_THIN_SPREAD` was silently overriding the physics table** for Tesla, Laser, Railgun,
> Prism, Inferno and Cryo, pinning all six to a flat `Spread 100` at every level — which is
> exactly what made Laser collide with Railgun and with Bullet. It is now only a fallback for a
> family with no physics shape.
>
> Guarded by **`tools/audit/audit_family_uniqueness.py`** (in `run_all.sh`), which reads the
> RESOLVED templates so hand edits are caught too: 126 family/level templates, no two sharing
> both a radius and a curve.
>
> ### Hitscan for the fast bullets, travel time for the shells
>
> Maintainer 2026-08-22: *"bullets should have that instant hit with tracer thingy from Shattered
> Paradise ... but only for the fastest bullets like the machine guns, gatlings, flak, sniper etc
> and not tank shells or artillery shells because those should have a travel time and inaccuracy
> while those fast bullets should only have a minimum inaccuracy that is equal to their spread."*
>
> | template | projectile | inaccuracy |
> |---|---|---|
> | `^Projectile_Bullet_{Light,Medium,Heavy}` | `InstantHitWithFakeBullets` | = Spread (67/100/133) |
> | `^Projectile_Sniper_Light` | `InstantHitWithFakeBullets` | = Spread (40) |
> | `^Projectile_Flak_{Light,Medium,Heavy}` | `InstantHitWithFakeBullets` | = Spread (73/110/146) |
> | `^Projectile_Melee_{Light,Medium,Heavy}` | `InstantHit` (nothing drawn) | n/a |
> | `^Projectile_Shell*`, `^Projectile_Artillery*`, missiles, grenades | unchanged, they fly | 1% of Range |
>
> `InstantHitWithFakeBullets` is ported from Shattered Paradise: the warhead lands on the firing
> tick and N **fake** bullets fly out afterwards carrying the sprite, trail and full contrail, so
> the existing visuals are kept. ⚠ `FakeBulletNumber` defaults to **0**, which draws nothing.
> Sniper and Flak were already at `Speed: 10000` — the `SPEED_CAP` the pricing model calls
> "basically instant" — so hitscan makes honest what those numbers already pretended.

## 1. The engine mechanic (verified in `OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs`)

- `Spread` (WDist) = the distance **between** falloff steps.
- `Falloff = [f0, f1, … f(N-1)]` → range points `effectiveRange[i] = i × Spread` (line 90), i.e.
  `0, S, 2S, … (N-1)S`.
- Damage% at distance `d` = **linear interpolation** between the two bracketing falloff values
  (`GetDamageFalloff` → `int2.Lerp`). Beyond the last point `(N-1)·S`, damage = **0** (line 178).
- **Max damage radius = (N-1) × Spread.** Each extra Falloff value adds ONE Spread to the radius.
- Center (`d=0`) always gets `f0` (normally 100) × the warhead's `Versus`/`Damage`.

Example — `Spread 200, Falloff 100, 50, 25`: 100% at 0 → 75% at 100 → 50% at 200 → 37.5% at 300 →
25% at 400 → **0 past 400**. Radius = 2×200 = 400.

## 1a. "Just a max radius, linear center→edge?" — yes, and it needs NO C# change

The single-knob idea (author a `MaxRadius`; interpolate 100%→0% from center to it) is already a
special case of the current mechanic: **`Spread: <radius>`, `Falloff: 100, 0`**. Range points become
`[0, radius]`; `GetDamageFalloff` lerps `100→0`; damage is a clean linear cone, 0 at the edge. Both
`AreaDamageWarhead` and its subclass `AreaDamagePercentageWarhead` support it unchanged. (A cosmetic
`Radius:` field could be added as sugar for `Spread + Falloff 100,0`, but it's optional — same behavior.)

**What you GAIN:** one intuitive knob (radius); trivial to balance — the area-integrated damage of a
linear cone is exactly `πR²/3` (a lone target still takes 100% at center).

**What you LOSE: the falloff SHAPE.** Pure-linear can only vary *radius*, not *concentration*. Radius
alone still separates precision (small) from swarm (large) — that covers most cases. But two roles
collapse together:
- "**big radius, punchy center**" (Demolition — a hard blast that fades fast), and
- "**big radius, flat zone**" (Flame/Chemical — stays lethal across the whole area)

become the *same curve* at the same radius; you could only tell them apart by DoT + Damage. If that
distinction matters to you (it's the thing that makes a flame *zone* feel different from a demo
*blast*), keep a **tiny shape menu** instead of pure-linear — still no C# change, just which Falloff
array the generator emits:

| shape | Falloff | feel |
|---|---|---|
| Linear | `100, 0` | neutral cone (the default) |
| Punchy | `100, 40, 0` | concentrated center, fast fade (demolition, precision) |
| Flat | `100, 80, 55, 30, 0` | lethal zone across the radius (flame, chemical, sonic swarm) |

**Recommendation:** adopt **radius as the primary knob** for everything (supersedes the ad-hoc
5-step falloffs), with just those **three shapes** as the secondary role selector. Simplest possible
authoring that still lets flame/demo feel distinct. If you truly want ONE knob only, use `100, 0`
everywhere and differentiate flame/demo purely by DoT + radius + Damage.

## 1b. Shape vs radius — how the falloff values map to a curve

Because damage interpolates **linearly between the points**, the *spacing* of the values IS the curve:

- **Evenly-spaced values = a straight LINE.** `100, 0` and `100, 80, 60, 40, 20, 0` are the same
  SHAPE (a linear cone); they differ only in RADIUS (`1·Spread` vs `5·Spread`). Same cone either way
  if `Spread = radius/(N-1)`. Extra evenly-spaced points buy only finer radius granularity.
- **Front-loaded values = CONVEX (concentrated).** `100, 50, 25, 0` = punchy core + moderate tail.
  `100, 50, 25, 12, 6, 3, 1, 0` (halving) = sharp core + long thin tail. True `1/r²` = `100, 25, 11,
  6, 4, 3` (= 100/n²) — real blast overpressure / radiation intensity. This is the "explosion" curve.
- **Back-loaded values = CONCAVE (sustained then cliff).** `100, 95, 85, 65, 40, 0` stays lethal
  across most of the radius then drops — a "zone" (fire, gas).

**Two orthogonal knobs: RADIUS = (N-1)·Spread, and SHAPE = convex/linear/concave spacing.** Any shape
at any radius. This is what makes per-weapon *physical* profiles possible.

## 2. Why spread must be traded steeply against damage

The area a shot covers grows with the **square** of the radius: `area ∝ ((N-1)·S)²`. The total
"AoE output" (area-integrated damage) therefore scales ≈ `S² × falloff-shape-weight`. So spread is a
*quadratically* powerful stat — doubling it quadruples the ground covered.

Two calibration laws follow:
- **Single-target value = center damage only** = `Damage × Versus/100`. Spread does nothing to a lone
  target. So anti-armor/precision weapons want **small spread + high Damage**.
- **Swarm value ∝ Damage × area**. To stop AoE weapons from being strictly better, hold
  **`Damage × Spread ≈ constant`** (the maintainer's inverse-trade law) — a *linear* trade that
  deliberately UNDER-credits spread vs its quadratic power, so effective enemy density (never a full
  field) closes the gap. **Corollary: keep spreads bounded** — a runaway spread is worth far more than
  the linear rule charges.

## 3. Design in terms of RADIUS, then back out Spread

Pick the **target radius** (intuitive) and the **falloff shape** (role); then `Spread = radius / (N-1)`.

**Falloff shapes (the curve = the role):**

| shape | Falloff | pts | radius | use |
|---|---|--:|--:|---|
| **Sharp** (concentrated) | `100, 40, 10` | 3 | 2·S | precision / anti-armor / giant-killer |
| **Standard** | `100, 55, 25, 8` | 4 | 3·S | small splash (bullets, light missiles) |
| **Broad** (anti-swarm) | `100, 72, 48, 28, 12` | 5 | 4·S | swarm-clear (CannonHE, Concussion, Sonic) |
| **Lingering** (area-denial) | `100, 85, 70, 55, 40` | 5 | 4·S | fire / chemical (flat + DoT/GroundFire) |
| **Concentrated-Large** | `100, 55, 15` | 3 | 2·S | demolition (one big blast, not a wide fade) |
| **Expanding** | 10-ring, hand-tuned | 10 | huge | Nuclear (already built) |

**Base target radius by AoE role (Medium tier), in map cells (1 cell = 1024):**
Pinpoint ≈ 0.4 cell (400) · Small ≈ 0.7 (700) · Medium ≈ 1.3 (1300) · Large ≈ 2.1 (2200).

## 4. Modifiers (multiply the target radius; Damage then moves inversely per §2)

| modifier | ×radius | rationale |
|---|--:|---|
| **Air-capable** (Bullet, Flak, Missile-*, Laser, Arrow) | **×0.6** | it also hits air — pay for that flexibility with less ground splash |
| **Ground-only** (Cannon, Flame, Chem, Demo, Concussion, Sonic, Magic, Prism, Railgun, Tesla, Melee) | **×1.25** | compensation for no air |
| projectile **instant** (energy beams) | ×0.7 | perfectly reliable, never dodged |
| projectile **fast** (bullets, flak) | ×1.0 | — |
| projectile **medium** (shells, missiles) | ×1.15 | — |
| projectile **slow arc/lob** (artillery, grenade, demo) | ×1.35 | telegraphed & dodgeable → paid back in radius + Damage |

## 5. Per-type proposal (Medium tier; L = ×0.8, H = ×1.25 on the radius)

| type | role | air | speed | shape | radius (M) | **Spread (M)** | notes |
|---|---|:--:|---|---|--:|--:|---|
| CannonAP | pinpoint | – | fast (`range/5`) | Sharp | 500 | **250** | tank-killer; high Damage; fastest shell |
| **CannonHE** | medium | – | med (`range/10`, ½ AP) | Broad | 1600 | **400** | the swarm-clearer (ground bonus); ≈2× AP spread |
| MissileAP | pinpoint | ✓ | med | Sharp | 240 | **120** | anti-armor, hits air |
| **MissileHE** | small | ✓ | med | Standard | 420 | **140** | << CannonHE (air penalty) |
| MissileAA | pinpoint | ✓ | med | Sharp | 300 | **100–200** | dedicated AA (already decided) |
| Bullet | small | ✓ | fast | Standard | 420 | **140** | anti-inf |
| Flak | small | ✓ | fast | Broad | 420 | **105** | flak burst, anti-air+light |
| Arrow | small | ✓ | fast | Standard | 420 | **140** | |
| Laser / Prism / Railgun / Tesla | pinpoint | mix | instant | Sharp | 200–400 | **100** | energy — thin; chip/utility pays (done) |
| TeslaCharged | pinpoint | – | instant | Sharp | 800 | **200** | super tier (done) |
| **Flame** | medium | – | med | Lingering | 1600 | **400** | + GroundFire; area-denial |
| **Chemical** | medium | – | med | Lingering | 1600 | **400** | + cloud/DoT; area-denial |
| **Concussion** | medium | – | med | Broad | 1600 | **400** | frag; anti-inf swarm |
| **Demolition** | large | – | slow | Concentrated-Large | 2200 | **1100** | one big blast (few steps); anti-bldg+inf |
| **Sonic** | medium | – | fast | Broad | 1400 | **350** | anti-swarm flat (wants width) |
| **Magic** | pinpoint | – | med | Sharp | 500 | **250** | giant-killer → single-target |
| Melee | point | – | – | 1-step | ~100 | **50** | |
| **Nuclear** | super | – | – | Expanding | — | (hand-tuned) | 10-ring, done |

## 6. The families you flagged (fire / chem / demolition / concussion / nuclear)

- **Flame & Chemical = area-DENIAL**, not burst: a **Lingering** falloff (stays ~70-85% across the
  radius) + their existing DoT (`GroundFire` / chem cloud). Medium radius, ground-only bonus. They
  should feel like a *zone* you can't stand in, not a single big hit.
- **Concussion (shrapnel) = anti-infantry swarm**: **Broad** falloff, medium-large radius — frag
  spreads wide and thin. Low per-target Damage, wide area (per §2 trade).
- **Demolition = one concentrated blast**: large radius but a **Concentrated-Large** (few-step) shape
  so the damage is punchy near the center and gone quickly, not a soft 4-ring fade. Slow lob → paid
  back in radius + Damage. Anti-building + anti-infantry.
- **Nuclear = expanding rings** (already hand-tuned in `^Warhead_Nuclear_Super`): leave as-is.

## 7. Open questions before implementing
1. **Level scaling of radius** — proposal is ×0.8 / ×1.0 / ×1.25 (L/M/H). Or keep radius by ROLE and
   let per-unit Damage carry the class? (Simpler, but a heavy artillery then has the same blast as a light.)
2. **Exact falloff arrays** — the shapes in §3 are starting curves; the anti-swarm "Broad" tail
   (28,12) and the "Lingering" flatness are tunable.
3. **Damage×Spread≈const enforcement** — should the pipeline auto-derive per-unit Damage from the
   assigned Spread, or stay a manual guardrail?
4. Implementation is generator-driven (`gen_weapon_template.py` per-family `spreads`/`falloffs`
   overrides + `splice_templates.py`), then boot-gate — same path as the energy chips.

## 8. Master per-type profiles — the 3-axis synthesis (gameplay × physics × uniqueness)

**Method:** the real-world SPATIAL behaviour of each weapon picks its SHAPE (§1b); gameplay
(projectile speed, air-capability) picks the RADIUS and, inversely, the Damage (§2); uniqueness is
the check that no two profiles coincide. Falloff arrays below are illustrative curves of the named
shape — RADIUS = (N-1)×Spread, and per-unit Damage moves inversely to Spread. This table is the
authoritative per-type spec and supersedes the starter numbers in §5.

| type | real-world behaviour | shape | Falloff (illustrative) | radius (M) | projectile | air | what makes it unique |
|---|---|---|---|--:|---|:--:|---|
| Bullet | point impact | pinpoint | `100, 0` | ~100 | fast | ✓ | rapid single-target |
| **CannonAP** | kinetic penetrator, focused | pinpoint | `100, 0` | ~120 | **fastest (`range/5`)** | – | tank-destroyer — anti-armor punch, **no splash**, hyper-velocity shell |
| **CannonHE** | HE shell overpressure (~1/r) | **convex** | `100, 50, 20, 0` | ~900 | **fast (`range/10`, ½ AP)** | – | **REGULAR TANK gun** — direct-fire shell + wide swarm blast (**≈2× AP spread**, >> MissileHE). Slower shells = ARTILLERY (CannonHE+Demolition/Concussion, slowest lob) |
| MissileAP | shaped-charge jet | pinpoint | `100, 0` | ~100 | med | ✓ | focused anti-armor, hits air |
| **MissileHE** | small HE warhead blast | convex, small | `100, 45, 15, 0` | ~450 | med | ✓ | modest blast, hits air — **<< CannonHE** |
| MissileAA | proximity airburst | pinpoint | `100, 0` | ~150 | fast | ✓ | dedicated AA |
| Flak | airburst fragmentation | convex, small | `100, 55, 25, 8, 0` | ~500 | fast | ✓ | anti-air + light flak cloud |
| **Demolition** | concentrated charge (~1/r²/1/r³) | **very convex** | `100, 45, 18, 6, 0` | ~1400 | **slow lob** | – | devastating center, **fast fade**; anti-bldg+inf |
| **Concussion** | fragments fly outward, spread | **broad, long tail** | `100, 72, 50, 32, 18, 8, 0` | ~2100 | med | – | **widest thin frag field**, anti-inf swarm |
| **Flame** | fire covers zone + lingers | **concave** + DoT | `100, 90, 78, 60, 0` | ~1200 | med | – | **sustained lethal zone** (GroundFire) |
| **Chemical** | short toxic **BLAST** (green — a recolored flame, ~22 ticks) | concave zone + brief DoT | `100, 88, 72, 50, 0` | ~1100 | med | – | green flame-like burst (≈ Flame recolored) — **NOT the gas cloud**; differs from Flame by armor profile + toxic DoT |
| **Toxic** | drifting gas **CLOUD** (spawned, looping, long-lived) | persistent field | n/a — spawned `AnthraxCloud*` via `SpawnSmokeParticle` | wide, lingers | slow drift | – | **the real gas** — long-lived diffusing cloud; THIS is what "lingers/expands", already done via spawned particles |
| **Sonic** | sound pressure wave (~1/r) | **near-linear even** | `100, 75, 50, 25, 0` | ~1600 | fast | – | even wave, **anti-swarm flat** damage |
| Laser | focused directed energy | pinpoint | `100, 0` | ~80 | **instant** | ✓ | precise beam, hits air |
| Prism | beam + refraction scatter | pinpoint, small | `100, 0` | ~150 | instant | – | scatter beam + utility |
| Railgun | hypervelocity penetrator | pinpoint | `100, 0` | ~80 | instant | – | instant kinetic, no splash (+ charge delay) |
| Tesla | electric arc / chain | pinpoint, small | `100, 0` | ~120 | instant | – | arc + EMP |
| Magic | non-physical %HP | pinpoint | `100, 0` | ~120 | med | – | giant-killer (%HP), no splash |
| Arrow | point impact | pinpoint | `100, 0` | ~100 | med | ✓ | single-target, hits air |
| Melee | adjacent contact | point | `100` | ~0 | melee | – | adjacent only |
| **Nuclear** | fireball + blast + radiation | **expanding rings** | 10-ring (hand-tuned) | huge | slow | ✓ | expanding shockwave superweapon |

### How the three axes resolve per family
- **Gameplay (the tank vs tank-destroyer SPEED/SPREAD law — verified in
  `AREADAMAGE_WARHEAD_REBALANCE.md §5` + `FORMULA_V2.md:64`):** projectile speed is set from range, and
  the two tank guns are NOT equally fast:
  - **CannonAP** (tank destroyer / gun turret) — speed = **`maxRange / 5`** (the FASTEST shell),
    **pinpoint** spread, high single-target Damage. Hyper-velocity flat-trajectory penetrator.
  - **CannonHE** (the REGULAR TANK) — speed = **`maxRange / 10`** (HALF of AP's speed, still a fast
    direct-fire gun), and **≈ 2× the spread of the AP** — a bursting HE shell that clears swarms.
  - **Hybrid** (50% CannonAP + 50% CannonHE) — speed = **`maxRange / 10 × 1.5`** (between the two).
  - **Artillery** = **CannonHE + Demolition/Concussion** — the SLOWEST projectile of all (a lobbed arc),
    the WIDEST spread. This is where the slow, telegraphed, huge-blast shell lives; rocket-artillery is
    MissileHE + Demolition/Concussion. So the full ladder is
    **speed: AP (/5) > HE (/10) > artillery (slow lob)** and **spread: AP (small) < HE (2× AP) < artillery (widest)**.
  Air-capable weapons (Missile/Flak/Laser/Bullet/Arrow) pay for hitting air with **smaller radius +
  lower Damage** than their ground-only counterparts; slow projectiles are repaid with **bigger radius
  + higher Damage** (they can be dodged/outrun). This is the `Damage × Spread ≈ const` trade (§2).
- **Physics (the shape):** kinetic rounds (AP/Railgun/Bullet) = pinpoint; HE overpressure = convex,
  falling ~1/r to 1/r²; a concentrated demolition charge = *very* convex (1/r³-ish, punchy center);
  fragmentation throws frags OUTWARD = broad with a long tail; fire = a concave sustained zone with a
  hard edge + burn DoT; gas = a Gaussian diffusing cloud (widest) + DoT; sound = an even ~1/r wave;
  a nuke = an expanding multi-zone shockwave.
- **Uniqueness (the check):** the eight AoE families are pairwise distinct on
  `shape × radius × DoT × projectile-speed` — convex-medium-slow (CannonHE) ≠ convex-small-air
  (MissileHE) ≠ very-convex-punchy (Demolition) ≠ broad-widest (Concussion) ≠ concave-DoT (Flame) ≠
  diffuse-widest-DoT (Chemical) ≠ even-wave (Sonic) ≠ expanding (Nuclear). The pinpoint families are
  distinguished by projectile speed (instant/fast/med), air-capability, their `Versus` profile, and
  damage TYPE (Magic = %HP, Tesla = +EMP, Railgun = +charge/chip). No two weapons feel the same.

## 9. Temporal modes — which weapons EXPAND or LINGER (not just instant)

The AreaDamage warhead has three temporal modes (verified in `AreaDamageWarhead.cs`, fields
`Ticks` / `TickDelay` / `MinRadius` / `MaxRadius` / `TickDamage`):
1. **Instant** (`Ticks: 1`) — one hit = SpreadDamage. Default; correct for anything that resolves in
   milliseconds.
2. **Static DoT cloud** (`Ticks > 1`, `MaxRadius: 0`) — repeats every `TickDelay`, full falloff radius
   each tick; a damage field lingering in place.
3. **Expanding shockwave** (`Ticks > 1`, `MaxRadius > 0`) — the damaged radius grows
   `MinRadius → MaxRadius` across the ticks (per-ring `TickDamage` weights); a wave propagating outward.

**Physics test — expand only if it propagates slowly enough to read across a tick:**

| weapon | propagation | verdict |
|---|---|---|
| **Nuclear** | shockwave expands over seconds | **EXPAND** ✓ (done) |
| **Toxic (gas cloud)** | gas diffuses + lingers over seconds | already a **spawned looping cloud** (`SpawnSmokeParticle` → `AnthraxCloud*`) — that IS the linger; no AreaDamage ticks needed |
| **Chemical (blast)** | short green burst (~22t, recolored flame) | **INSTANT** — it's an explosion, not the cloud |
| **Flame** | fire spreads over seconds + burns | **LINGER** (GroundFire) ✓; optional small initial expand |
| **Sonic** | sound wave ~343 m/s (real delay over a big radius) | optional **mild expand** (thematic, low priority) |
| Demolition | blast wave ~km/s = instant at tick resolution | **INSTANT** (expand = pure visual flavor, not physics) |
| Concussion | fragments ~1 km/s = instant | **INSTANT** |
| CannonHE / MissileHE / AP / Bullet / Laser / Railgun / Tesla / Flak / Arrow / Magic | instant | **INSTANT** |

**Recommendation:**
- **Net: the AreaDamage EXPAND mode is essentially Nuclear-only.** The real lingering/diffusing gas is
  the **Toxic** family, already implemented as a spawned looping `AnthraxCloud*` field — it doesn't
  need AreaDamage ticks. **Chemical** is a short green blast (instant). So don't add expand to Chemical.
- **Flame → keep the lingering `GroundFire`** for its DoT; optionally a small 2–3 tick expand for the
  initial fire spread.
- **Sonic → optional mild expand** (a visible ripple) — flavor only, low priority.
- **Demolition / Concussion / all blasts / kinetic / beams → INSTANT.** A real explosion, frag burst,
  or beam is faster than a game tick; "expanding" them is a visual gimmick, not physics, and costs
  per-weapon complexity + per-shot work for no gameplay gain. A *dramatic* big-demo expand is a
  deliberate VISUAL choice if you want it — flag it as such, don't dress it as physics.

**Caveats:** (a) the warhead does expand OR a static cloud, not both — persistent linger for gas/fire
is best left to the spawned cloud/`GroundFire` actor while the warhead does the initial (expanding)
burst; (b) multi-tick warheads cost more per shot — reserve them for the few weapons where the effect
actually reads on screen; (c) `TickDamage`/`TickDelay`/`MinRadius`/`MaxRadius` are tuned per weapon
(like the hand-tuned `^Warhead_Nuclear_Super`).
