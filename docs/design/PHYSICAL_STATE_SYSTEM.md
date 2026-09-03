# Physical-State System — damage-scaled status meters (design spec, rev. 2026-08-09)

Status: **The framework + the entire Temperature axis ALREADY EXIST and are wired.** This rev
corrects the first draft, which wrongly implied a from-scratch C# build. The real remaining work is
small (one C# field + yaml config). Verify against the code before building — "don't trust, verify".

Companion: `AREADAMAGE_WARHEAD.md`, `SPREAD_FALLOFF_PLAN.md`;.

---

## ⛔⭐ THE METERS WERE NOT THE SAME SHAPE — three defects, all fixed 2026-08-18

**Maintainer:** *"Cryo seems as strong as Fire IF it is able to completely freeze a unit BEFORE it
dies ... they can reach their full effect before a unit dies at around 25% HP left"* and, on being
shown the asymmetry, *"Temperature has negative values while corrosion doesn't. The absolute
maximum and minimum values are the same! cryo = -20k heat = 20k and corrosion 20k!"* — i.e. the
three axes are ONE system and must behave alike. They did not. Model + guards:
**`tools/balance/physical_state_price.py`**, `tools/tests/test_physical_state_price.py`.

### D1 — the same `Scale` filled heat TWICE as fast as corrosion

`PhysicalState.ApplyChange` health-scales every incoming change through `ScaleChangeToHealth`:

```csharp
range = Info.MaxValue - Info.MinValue;                    // Created()
return (int)((long)amount * range / health.MaxHP);        // ScaleChangeToHealth()
```

The divisor is the meter's **own range** — ⚠ NOT the 10000 that `PhysicalStateInfo`'s
`[Desc]` still advertises (*"divided by HP/10000"*), which is exactly what the first derivation
trusted. `Temperature` is signed (−20000…20000) so its range is 40000; `Corrosion` shipped
`MinValue: 0`, range 20000 — **so one number meant two different fill rates.** The fill DISTANCE
was always the same 20000; only the divisor differed, which makes it an artifact, not a design.

**Fixed:** `Corrosion MinValue: 0 → -20000`. Both meters now:

```
damage-scaled   ratio = MaxValue × 100 / (Scale × range)   =  50 / Scale
discrete apply  ratio = MaxValue × damage / (Amount × range)
```

⭐ In the damage-scaled form the target's **MaxHP and the weapon's damage BOTH cancel** — the race
is a property of the constant alone, which is why one constant moves every weapon at once.
ℹ Negative corrosion is unreachable (nothing feeds it, `RelaxedValue: 0`), and the bar is
unaffected: `PhysicalStateBar` with `ShowAbsoluteValues: false` measures deviation from relaxed.

### D2 — corrosion did nothing at all below HALF the meter

`Corroding` was gated at `LowerValue: 10000` of 20000 while `Overheating` opens at `200` — a **50×
difference in the opening gate between two axes of the same system.** A corrosion weapon that
49%-filled the meter had delivered literally nothing.
**Fixed:** `Corroding LowerValue: 10000 → 200`, and `CorrosionDeadzone` mirrored to `-200…200`.

### D3 — every DoT opened at HALF strength

`ChangesHealthProportionalToPhysicalState` normalises over the **full signed range**
(`(v − MinValue) / range`) and has no `UseDeviationFromRelaxed` option. On a signed meter that puts
`DamageAtMinimum: 0` at the *midpoint*, so the burn opened at **75 of 150 per tick** the instant
`Overheating` was granted — a target one point past the deadzone burned at half maximum.
**Fixed** in yaml alone: `DamageAtMinimum: -DamageAtMaximum` puts the zero back at a relaxed meter
(heat −150, corrosion −180, corrosion/hazmat −90). Now `damage = DamageAtMaximum × fill`, exactly.

### What is true after the fixes

Full strength is now **`METER_FULL = 100`** — ONE knob in `gen_weapon_template.py`, with every
family and blend expressed as a fraction of it (`_m(0.75)`, `_m(0.35)`, …) instead of 13
hand-divided numbers. At 100 the race is **ratio 0.500 on both meters**: full effect with half the
target's life still ahead of it, comfortably inside the 0.75 bar.

| mechanism | bindings | reach full effect before 25% HP |
|---|--:|--:|
| damage-scaled (heat + corrosion) | 527 | **111** |
| discrete apply (cryo) | 22 | 7 |
| **total** | **549** | **118 (21.5%)** |

⛔ **`meters_filling_before_death` = 118 of 549 — NOT the 534 (97.3%) this section claimed until
2026-08-19.** The correction is one term, and it is W24's term. Everything above assumes the
damage that FILLS the meter is the damage that KILLS the target. It is not: a damage-scaled
binding fills from the ONE warhead carrying `PhysicalStateName`, while the target dies to every
main warhead the weapon fires.

    ratio = 50 / Scale / fed_share            fed_share = fed damage / total main damage

Only **41 of 427** damage-scaled metered weapons have `fed_share == 1`. The median is **0.398**,
so the typical metered weapon fills ~2.5× slower than modelled and misses the 0.75 bar outright.
The worst are 12-main EMP weapons at **4%** (`eden_EMP`, `edenTiger_EMP`, `plymouth_EMP`, …).

⚠ **How this was found, and why nothing here found it.** The maintainer playtested a Chemical
Stealth Tank against a harvester and the corrosion bar never filled. The weapon fires Shrapnel
5500 + Missile 9000 + Chemical 9000 vs Heavy: it kills on **27175**/shot and fills on **10350**
(38%). Every guard in this tree passed — `doc_claims` counted bindings, the unit tests pinned the
arithmetic, the boot gate proved it loads. None of them asked whether the two damage figures were
the same damage. That gap is structural: a census of *what exists* cannot see a defect in *how the
parts relate*.

⛔ **This is why `BALANCE_PROGRAM_PLAN` §0a puts weapon STRUCTURE before pricing** — restated by
the maintainer 2026-08-19: *"that's exactly why I said you should finish the 3 way weapon split
first!"* Pricing a weapon whose structure is wrong measures the wrong object. The burn-down is
pinned as `w24_multi_main_fed` (380, ratchet-down-only).

⚠ **RELAXATION is still excluded** and moves this number down further: `RelaxationDelay 25` +
`RelaxationLinear 5` + `RelaxationScaled 50` bleeds ~642 meter/shot at `ReloadDelay 60` (23% of
the gain in the Stealth Tank case), and it bites hardest on SLOW, LOW-damage weapons against
ARMOURED targets — precisely where chemical weapons are supposed to work. Add it AFTER W24: it is
a second term on the same corrected base, and stacking two corrections at once is how the first
census ended up three times revised.

⚠⚠ **Why 300 became 100.** The 100 → 300 change (`354ed5ad3`) was calibrated against the wrong
formula: `Scale: 100` had ratio **0.50** all along and always cleared the bar, and the Corrosion
"failure" that appeared to justify 300 was D1's artifact. 300 was a 3× faster fill than anything
needed, and the 1.25× ceiling cannot charge for it. Maintainer 2026-08-18: *"test it in game first
for 100"* — so 100 is shipped for playtest, propagated to all 694 live bindings.

### The effect curve — now one curve for all three axes

Derived from the consumer traits on `^CryoFreezable` / `^Corrodible`, never assumed:

| axis | consumers | gate | share of the axis at 5% / 25% / 50% / 75% / 100% fill |
|---|--:|--:|---|
| heat | 1 (DoT) | 1% | 0.05 · 0.25 · 0.50 · 0.75 · 1.00 |
| cryo | 2 (slow, damage amp) | 1% | 0.05 · 0.25 · 0.50 · 0.75 · 1.00 |
| corrosion | 4 (DoT ×2, slow, damage amp) | 1% | 0.05 · 0.25 · 0.50 · 0.75 · 1.00 |

ℹ A consumer that needs a **completely full** meter (`superhot`, `CorrosionMax`) is excluded from
the average: it is a bonus on top of full delivery, not half of the axis. `superhot` is 1% of max
HP per 25 ticks against `Overheating`'s 150 per tick — letting it halve every partial score would
be a rounding error deciding the shape of the curve.

### ⭐ EXPOSURE — the term the price model never had

A meter the target does not carry delivers **nothing**, and this is now the *only* thing separating
the axes:

| meter | actors | share of the 1609 priced (Health + Valued) actors |
|---|--:|--:|
| `Temperature` | 1592 | **98.6%** |
| `Corrosion` | 724 | **45.0%** |

A corrosion weapon does nothing at all to 51.3% of the roster. Claim: `corrosion_meter_actors`.

### E2 pricing — the rule as built

```
weight     = clamp01( exposure × delivery(ratio, curve) / delivery(0.75, curve) )
multiplier = 1 + 0.25 × weight
```

`delivery` is the mean effect share over the target's remaining life. The reference is a weapon
that exactly meets the maintainer's bar on a fully-exposed meter, so **meeting the bar pays exactly
1.25×** and filling faster is never charged more than the ruling allows. Over 549 bindings:
**328 pay the full 1.25×, 221 partially, 0 nothing**; per actor **+21.9%** across 337 actors.
Wired into the ledger by `01f1820b8` (`derived.physical_state_multiplier`).

| axis | mechanism | bindings | median ratio | median × |
|---|---|--:|--:|--:|
| heat | scaled | 321 | 0.500 | **1.250** |
| corrosion | scaled | 206 | 0.500 | **1.135** |
| cryo | apply | 22 | 0.519 | **1.250** |

⚠ Corrosion caps at 1.135 with an identical meter and an identical fill rate — **exposure alone**
holds it there. That is what separates Flame from Chemical now.

ℹ Relaxation between shots is deliberately **outside** the priced ratio: `RelaxationDelay: 25`
means a weapon reloading faster than 25 ticks loses nothing, and the linear term would reintroduce
a MaxHP dependence that destroys the cancellation above. It costs a slow artillery piece ~36% of a
shot's gain and a normal gun ~5%.

### E2 pricing — pipeline wiring

The delivery-weighted multiplier is now wired into `tools/balance/fit_class.py`:

* `tools/balance/extract_stats.py` computes the per-actor `physical_state_weight`,
  `physical_state_multiplier`, and `physical_state_weapon` via
  `physical_state_price.actor_multipliers()` and stores them in the derived sidecar
  (`docs/balance/derived/*.json`), so they cannot desync from the raw ledger.
* `fit_class.price_unit()` applies `formula.physical_state_price_multiplier(weight)`
  on top of the charge-up discount. A unit with full delivery (e.g. `td_nod_flametank`)
  prices at the full 1.25× ceiling; a unit with partial delivery or no physical-state
  weapon prices at the corresponding lower multiplier or 1.0.

## 0. WHAT ALREADY EXISTS (verified 2026-08-09)

**Engine traits** (`engine/OpenRA.Mods.Common/Traits/`): `PhysicalState`, `PhysicalStateBar`,
`PhysicalStateAura`, `DamageMultiplierProportionalToPhysicalState`, `SlowsProportionalToPhysicalState`,
`ChangesHealthProportionalToPhysicalState`, `ChangesHealthProportionalToPhysicalState`,
`GrantConditionOnPhysicalState`, `ChangeOwnerOnPhysicalState`, `ProvidesShieldFromPhysicalState`,
`PhysicalStateShieldManager`; Warhead `ApplyPhysicalStateWarhead`. Cameo adds `ChangesPhysicalState`,
`WithPhysicalStateColoredOverlay`. **This is a full, generic meter framework — no new trait C# needed
to add more axes.**

**The `Temperature` axis is FULLY BUILT** (`mods/cameo/rules/defaults.yaml`, on the infantry/vehicle
defaults). Verbatim behaviour — do NOT redesign it, only extend/tune:
- `PhysicalState@Temperature`: `MaxValue 20000 / MinValue -20000 / RelaxedValue 0`,
  **`RelativeToHealth: true`** (HP-scaled — big units need more), **`RelaxationLinear 5 + RelaxationScaled 50`
  + `RelaxationDelay 25`** (cools/warms back to 0 after 25 ticks), `ApplyDamageModifiers: true`.
- **Bar** `PhysicalStateBar@TemperatureBar`: 🔴 `FF0000` hot / 🔵 `0080FF` cold / grey neutral.
- **Hot side:** `GrantConditionOnPhysicalState@Overheating` (Temp **200→20000**) → `ChangesHealthProportionalTo…@Overheating`
  flat **150/tick FireDeath** (the damage burst); `@superhot` (Temp **==20000**, max) → **% damage** (the
  "keep heating → it pops" tier). Both already scale off the meter; the killing damage is credited to the
  attacker via the warhead's `firedBy` (verify XP attribution when wiring).
- **Cold side:** `@FrostSlowdown` (SlowsProportional) ramps Speed/Turn/Turret→0 and Reload→1 (freezes solid);
  `@CryoFreeze` (Temp **-200→-20000**) → **DamageMultiplier 100→200%** (takes up to 2× while frozen = the
  "shatter"); `@superfreeze` (Temp **==-20000**, max) → `frostspark` overlay (+ the aircraft-instakill hook —
  verify the 10× aircraft / 200% ground split when wiring); blue `WithPhysicalStateColoredOverlay@CryoFreeze`.
- **`EnemyProximity`** is a SECOND, non-HP axis (`PhysicalStateAura`) driving Tesla-discharge armor — proof
  the framework already carries multiple axes and that "scales with HP or not" is per-axis (`RelativeToHealth`).

**So for Temperature there is essentially nothing to build** — the meter, HP-scaling, decay, two hot
thresholds (burst→pop), two cold thresholds (freeze→shatter/superfreeze), bar and overlays all exist.

## 1. The ONE genuine C# gap — damage-scaled application

`ApplyPhysicalStateWarhead` applies a **fixed `Amount`** (× firepower modifiers), NOT the damage value —
so today you hand-tune `Amount` per weapon (e.g. Cryocopter `Amount: -16000`). The maintainer wants the
state to **scale with the weapon's actual damage**. The clean fix (small, additive):

Add to `OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs` (+ its `AreaDamagePercentage` subclass):
```
PhysicalStateName: Temperature    # default "" = off
PhysicalStateScale: -100          # state added = effective damage × Scale/100 (signed)
```
On impact, after computing per-target damage (post-falloff, post-Versus/armor) and calling
`InflictDamage`, also call the target's `PhysicalState.ApplyChange(damage × Scale/100, firedBy, applyMods)`.
- **On main + `_Percentage` warheads only, never `_ExtraDamage`** → chip auto-excluded; %-twin also feeds
  the meter (both maintainer rules satisfied by placement).
- Armor + falloff scale for free (it's a fraction of the computed damage). For attacker-firepower /
  target-damage mods, reuse `ApplyDamageModifiers`/`args.DamageModifiers` exactly as `ApplyPhysicalStateWarhead`
  does. Verify the hook against that warhead's `DoImpact` so behaviour matches the existing fixed-Amount path.

That single field removes the need for separate per-weapon `ApplyPhysicalState` warheads and makes heat/
cold/corrosion auto-scale with damage. **Everything else below is YAML config of existing traits.**

## 2. Corrosion axis — CONVERT the existing binary `corroded` into a meter (verified 2026-08-09)

⚠ Corrosion is NOT greenfield: it already exists as a **binary `corroded` condition** (`defaults.yaml`
~5495–5516) applied on/off by the Schwarzer Mond rockets — `DamageMultiplier@corroded 125`,
`SpeedMultiplier@corroded 75`, `WithColoredOverlay@corroded 44FF4444` (green), `Targetable@corroded`.
So BUILD 1 is a CONVERSION, reusing the existing gameplay mechanics:
1. Add `PhysicalState@Corrosion` meter (0–20000, `RelativeToHealth`, decay) on `^CryoFreezable` (the
   shared Temperature home) + wherever else Temperature lives.
2. Replace the fixed `@corroded` traits with **scaled** ones from 50%→100% (`ChangesHealthProportionalToPhysicalState`
   DoT ~180 + a `@…Hazmat` half via `hazmatsuits`; `SlowsProportionalToPhysicalState` `OnlyPositiveValues`
   to ~60%; `DamageMultiplierProportionalToPhysicalState` to +150%).
3. Keep the meter art: `WithPhysicalStateColoredOverlay@Corrosion` green tint 200→20000; leave the
   `CorrosionMax` condition visual-empty.
4. Migrate the Schwarzer Mond weapons from granting the binary `corroded` to feeding the Corrosion meter
   (via the new `PhysicalStateScale`, or an `ApplyPhysicalState` warhead). Keep the old binary path until
   migrated so nothing breaks mid-way.
Boot-gate after each step. (The section below is the original greenfield sketch, superseded by this.)

### (superseded greenfield sketch)

Add a `PhysicalState@Corrosion` block to the same defaults (unipolar): `MinValue 0 / MaxValue 20000 /
RelaxedValue 0`, `RelativeToHealth: true`, relaxation like Temperature. Bar 🟢 green (`PositiveColor 00C000`).
Reactions via the SAME proportional traits, gated on threshold conditions from `GrantConditionOnPhysicalState`:
- from 50%→100% ramp (maintainer 2026-08-09 — DoT + slow + vuln, the rounded "acid melts you"):
  `ChangesHealthProportionalToPhysicalState` DoT up to **~180/tick, short/sharp**;
  `SlowsProportionalToPhysicalState` down to **~60% speed**;
  `DamageMultiplierProportionalToPhysicalState` up to **+150% damage taken**.
- This IS the Schwarzer Mond "corruption" effect (Korruptes Biest / Rocket Soldier) turned into a meter.
- **Hazmat/reactive-armor reduction (maintainer 2026-08-09):** mirror the existing Temperature pattern —
  `@Overheating` (DoT 100–150) has a reduced `@OverheatingHazmat` variant (DoT 25) gated on `hazmatsuits`.
  Add the same for Corrosion: a `@CorrosionHazmat` variant at **half** the DoT gated on `hazmatsuits`,
  and/or a corrosion-resistant armor type that halves it — exactly as hazmat/reactive armor halves heat.
Then wire Chemical/Plasma to it via §1's field.

## 3. Family wiring (via §1 field, on main + _Percentage)

| Family | State | Scale% | Notes |
|---|---|--:|---|
| Flame (L/M/H) | Temperature | **+100** | + GroundFire linger |
| Laser (Heavy) | Temperature | **+75** | overheat→pop; main-damage only (chip excluded by placement) |
| **Prism (L/M/H)** | – | – | anti-LIGHT scatter beam, Versus LOCKED (`Scout 100 › None 94 › … › Superheavy 34`), ground-only, thin spread, no chip. **NO cryo by default** — Prism Tank / Athena Cannon are pure prism. |
| **Inferno (L/M/H)** — NEW | Temperature | **+100** | **Flame×Prism** heatray blend, ground-only, thin spread, FireDeath; mostly thermal with some field coupling, so both HAZMAT and REFLECTOR reduce it. |
| **Cryo (L/M/H)** — NEW | Temperature | **−100** | **Laser×Prism** coldray blend, air-capable, thin spread; coherent energy delivery with freeze-kinetic, so the damage profile is anti-heavy-ish and REFLECTOR helps more than HAZMAT. Reuses the existing cold/freeze/shatter side. |
| Chemical (L/M/H) | Corrosion | **+100** | pure corrosion |
| **Plasma (L/M/H)** — NEW | Temperature **+50** & Corrosion **+50** | | flagship Flame×Chem blend Versus |
| Tesla | (EMP, separate) | – | keeps existing EMP |
| Bullet/Cannon/Missile/Flak/Arrow/Demolition/Sonic/Prism/Magic/Melee | – | – | clean unless a §4 effect added |

## 3b. Effect UPGRADES (cryo etc.) = DUAL warhead (maintainer 2026-08-09)

When an upgrade adds an effect to an EXISTING weapon (e.g. RA1 Allied cryo projectiles upgrading the
demo artillery), replace the old manual `ApplyPhysicalState` rings with the **dual model**: the upgrade
swaps the armament (the JHind/waveforce `RequiresCondition` pattern) to a variant weapon that keeps the
original warhead **and adds the real Cryo warhead** — both at ~50% damage:
```
DemoArtilleryCryo:
    Inherits: DemoArtillery              # keeps Warhead@Demolition_Heavy (its Versus)
    Inherits@cryo: ^Warhead_Cryo_Heavy   # adds the Cryo warhead (Laser×Prism anti-heavy/air Versus + Temperature -100)
    Warhead@Demolition_Heavy: { Damage: <50%>, PhysicalStateName: Temperature, PhysicalStateScale: -100 }
    Warhead@Cryo_Heavy:       { Damage: <50%> }   # freeze via the family's baked -100
```
Rationale (maintainer): the point is NOT just to freeze — it's to **change the damage profile** so the
upgraded weapon feels unique (demo blast + cryo's Laser×Prism anti-heavy/air Versus + freeze). The added
Cryo warhead's Versus is the real value (temperature alone would be redundant). Both warheads carry the
−100 scaling so the whole weapon freezes. → this makes the **Cryo family a prerequisite** (BUILD 2b).

⚠ **Combined weapons stack it further (maintainer 2026-08-09):** artillery is being reworked to
**CannonHE + Demolition** (the slow big-blast combo), so a cryo upgrade makes Cryo the **THIRD** warhead
(CannonHE + Demolition + Cryo). This exceeds the usual 2-warhead cap but is a justified exception (a
combined artillery weapon + an upgrade) — the allow-list case in.

**Damage model (maintainer 2026-08-09) — symmetric warheads + a FirepowerMultiplier penalty:**
keep all members at the SAME damage (e.g. each 2000) and pay for the freeze by REDUCING net output.
Worked example (artillery): base CannonHE 2000 + Demolition 2000 = **4000**. Add Cryo 2000 → symmetric
**6000 raw** (+50%). Put **`FirepowerMultiplier: 50`** on the cryo-upgraded actor → 6000 × 0.5 = **3000
effective = 75%** of the original 4000. So the cryo upgrade *lowers* damage to 75% — fair, because the
freeze is very strong (immobilise + the cold-side +incoming-damage). Freeze buys the −25% damage.
General rule: N symmetric members × D, then `FirepowerMultiplier` set so the effective total lands where
the freeze/effect is priced (here 75%).

**⚠ PIPELINE INVARIANT (maintainer 2026-08-09): a cryo weapon ALWAYS deals 75% of the damage the SAME
weapon would deal without cryo.** Take the pipeline-balanced value X, then set a `FirepowerMultiplier`
so the cryo weapon's EFFECTIVE damage = 0.75·X — the fixed "cryo tax" that pays for the freeze
(immobilise + cold-side +incoming-damage). The FP *value* is computed from the raw: with a symmetric
added cryo warhead the raw is 1.5·X, so FP = 0.75/1.5 = **50%**; a cryo weapon with no added warhead
would use FP **75%**. This is a balance-pipeline rule to ENFORCE automatically (a cryo tag → the pipeline
applies the 0.75× effective tax), so it can never be forgotten. TODO: wire the cryo tax into
`extract_stats`/`fit_class`/`apply_balance`.

## 4. Other effects — what exists vs what's new
- **Suppression:** partial already (infantry go prone for less damage). A Concussion suppression METER
  (−firepower/pin) would be a new Corrosion-style axis (yaml) — decide if worth it over existing prone.
- **Radiation:** already exists as flavor on some weapons (RA2 Soviets). Keep as-is / extend per faction.
- **Armor Breach (Sunder)** — AP/Railgun: a NEW physical-state axis (yaml, mirror Temperature) with
  `DamageMultiplierProportionalToPhysicalState` so stacked kinetic hits make the target take more. **No new
  C#.** High value — makes tank-destroyers "soften" targets → combined-arms incentive (maintainer likes this).
- **Hex** — Magic: −firepower / −accuracy (inaccuracy) / disable specials, as a granted condition (yaml).
  Maintainer likes it; tune the magnitude (~ −50% firepower or heavy inaccuracy).
- **Knockback** — Demolition: **NO engine support found** → needs a NEW C# warhead (push actors from
  impact center). Feasible but a real addition; maintainer said "do it if possible" → build a
  `PushWarhead` in `OpenRA.Mods.Cameo/Warheads/`.

## 4b. Visuals — every axis needs its OWN artwork (maintainer 2026-08-09)

Each state needs (a) a **level-scaling coloured overlay** (`WithPhysicalStateColoredOverlay`, already
used for Temperature's blue cold side) AND (b) **threshold artwork** at the extreme
(`WithIdleOverlay`, like `@frostspark` on `superfreeze`). Not just a tint.

| Axis | Scaling overlay | Threshold artwork | Asset status |
|---|---|---|---|
| Temperature hot | 🔴 red (bar exists) | overheat glow at max | red overlay exists; max-heat art TBD |
| Temperature cold | 🔵 blue (`@CryoFreeze` overlay) | ❄ `frostspark` at `superfreeze` | **exists** |
| **Corrosion** | 🟢 **green tint**, ever-increasing 200→20000 (`WithPhysicalStateColoredOverlay`, colour only) | the **existing pulsating corrosion effect**, played ONLY at 100% (20000) | **mostly EXISTS** — pulse effect exists; green tint is just the colour trait |
| **Sonic** | 🔵 **looped, transparently-shifting blue** overlay (the sonic-mark visual) | — (on-hit, short duration) | **NEW art needed** — a looped shifting-blue overlay. PLACEHOLDER live now: `^SonicDebuff` uses a flat `WithColoredOverlay@SONICDEBUFF` (`0088FF40`, Multiply) — swap it for the looped overlay when the art lands. The commented-out `WithDecoration@SONICDEBUFF` in `^SonicDebuff` still points at the existing `2100commandodebuff` icon. |
| **Armor Breach** | very light **grey** scaling overlay | **breach icon** at 100% — a bullet punching through armor plating (when they take 200%) | **NEW art needed** — the breach icon; overlay is just grey colour |

**New sprite art to create** (RGBA PngSheet per pair every new
effect with a sound): the **looped shifting-blue Sonic** overlay, and the **armor-breach breach-icon**
(bullet-through-plating) for the 100% state. Corrosion's pulse already exists (play it at max) and its
green tint is just a colour trait. The traits (`WithPhysicalStateColoredOverlay` / `WithIdleOverlay`)
reference an image+sequence, so the yaml wires with placeholders and the art drops in later.

## 5. Build STATUS + RESUME TRACKER (updated 2026-08-11 — ⭐ RESUME HERE after /compact)

> ⭐ **The physical-state work is now items W6–W10 in
> [`BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md)**, which holds their status,
> ownership and acceptance criteria. Read §0 of that file first. Summary of the newly
> approved conversions (maintainer 2026-08-11):
>
> - **W6** — new C# `ModifiesCombatProportionalToPhysicalState` (signed from→to for
>   reload/range/speed/firepower, **with audio-pitch and glow hooks folded in**). This is
>   the framework's missing half: every existing proportional trait only makes things
>   worse, so a spin-**up** is impossible without it. Blocks W8 and W10.
> - **W7** — **Sonic → `Resonance` meter**, no new C# needed. The rule that keeps it
>   distinct from Corrosion: Resonance **deals no damage at all, ever** (pure force
>   multiplier, fast decay) while Corrosion is attrition (DoT, slow decay). Sonic becomes
>   the only debuff that kills nothing and doubles the army's output.
> - **W8** — gatling ladder → `SpinUp` meter. **47 actors × 20–30 multiplier traits ≈ 1340
>   objects, ~40% of all 3197 multiplier instances in the mod**, in ten 5% steps.
>   End-points to reproduce: `0.95¹⁰ = 0.599` reload, `1.02¹⁰ = 1.219` range/speed.
> - **W9** — **Poison meter**: a Corrosion clone for infantry (corrosion eats vehicles,
>   poison hurts infantry, flame does both). Gas clouds fill the meter by dwell time and
>   the DoT scales off it — dose-response, no new C#.
> - **W10** — **Blind meter**: range scales 100%→20% proportionally; at FULL blind only,
>   the weapon is disabled, the icon shows, and the `blinded` Targetable applies so
>   blinders retarget.
>
> **Keep binary:** `^Berserkable` (chaos gas) — it flips a *mode* (who you obey), not a
> magnitude. Rule of thumb: meter a *magnitude*, keep a *mode* binary.

**DONE (committed work was boot-gated unless noted):**
- ✅ C# damage-scaled `PhysicalStateName`/`PhysicalStateScale` on `AreaDamage` + `_Percentage` — `406261128`
- ✅ C# MULTI-state `PhysicalStates` dict (one warhead → many meters) — `2e6d6968a`
- ✅ Corrosion meter axis on `^Corrodible` (green tint 200→20000, DoT+slow+vuln 50→100%, hazmat-half,
  no cap visual) — additive, INERT until fed — `ecf616978`
- ✅ Family wiring LIVE: Flame +100 / Laser +75 / Chemical +100 (generator `FAMILY_PHYSICAL_STATE`) — `51148be5b`
- ✅ Cryo family = `^Warhead_Cryo_*` inherits `^Warhead_Prism_*` + Temperature −100 (generator
  `INHERIT_FAMILIES`) — `f97a3b77c`
- ✅ Plasma family = avg(Flame,Chemical) Versus + Temperature 50 + Corrosion 50 (generator `BLEND_FAMILIES`
  + `versus_override`/`physical_states`) — `2e6d6968a`. Inert until a weapon adopts `^Warhead_Plasma_*`.
- ✅ Flame/Chemical `_Percentage` twins use `AreaDamagePercentage` and feed the matching meter.
- ✅ Legacy `^*FlameWeapon`/`^*ChemicalWeapon` templates and all concrete overrides converted to
  damage-scaled `PhysicalStateName`/`PhysicalStateScale` on `AreaDamage`/`AreaDamagePercentage`;
  fixed `ApplyPhysicalState` duplicates and separate FriendlyFire twins removed. `audit_physical_state_warheads`
  PASS, boot-gated (2026-08-18). 43 non-family (mostly cryo) `ApplyPhysicalState` warheads remain.
- ✅ **BUILD 3 — Sonic mark** — global rename `CommandoDebuff → SonicDebuff` (29 lines / 8 yaml files:
  `^SonicDebuff` in defaults.yaml + the condition, `Warhead@` keys and both `Inherits@`; the
  `2100commandodebuff` **asset**, its sequences and its palette keep their own names) + the mark BAKED
  into all three `^Warhead_Sonic_*` levels by the generator (`FAMILY_CONDITION` → a
  `Warhead@<tag>_Debuff: GrantExternalCondition`, both numbers DERIVED: `Duration = 2 × ReloadDelay` = 50
  ticks, `Range = 2 × Spread` = 800/1200/1600 = the half-damage radius). Zero damage → price-neutral,
  drift stays 0. The predator laser / waveforce / IonPulse keep their own hand-tuned grants, now of the
  renamed condition. `5a14355e6`
- ✅ **Magnetism meter on `^Magnefreezable`** (2026-08-22) — the third live axis. The magnetic grip
  used to be an `ExternalCondition` counted in STACKS (`RA2Magnet` is `Burst 100 / BurstDelays 1`, so
  one volley grants 100 tokens over 99 ticks) read by ten `SpeedMultiplier` + ten `WithColoredOverlay`
  traits on 10-point windows. ⛔ **All nine interior boundaries overlapped** — `Magnet <= 20` and
  `Magnet >= 20` both hold at exactly 20 — so two multipliers MULTIPLIED at every step the burst swept
  through: 90%×80% = **72%** at 20, 60%×50% = **30%** at 50. The ramp was non-monotonic at every
  boundary, on all **739** actors that inherit the template (via `^Vehicle`, `^RANeutralPlane`,
  `^ShootableMissile`), on every volley. 20 traits → 5; the overlap is structurally impossible now
  because `SlowsProportionalToPhysicalState` interpolates. Meter `0..20000`, `RelativeToHealth: false`
  (the old stack counted SHOTS, not damage), `Amount: 200` × `Burst: 100` = a full lock per volley,
  and the CONSUMED `magnetfreeze` condition is re-granted by `GrantConditionOnPhysicalState` at a full
  bar. Price-neutral: both carriers (`yuri_magnetron`, `asianalliance_hyperionprojector`) already pay
  1.183× for the heat binding on `^RA2LaserWeapon`, and `actor_multipliers` takes the max, not the sum.
- (Temperature axis + framework were ALREADY built — see §0.)
- ✅ **Upgraded-weapon IntegrityScale bump + missing chip `DamageTypes: Tesla`** (Devin, 2026-08-10,
  `145c6861c`, PR `fix/tesla-integrity-upgrade-drain`) — fixed two bugs that kept RA1 Tesla Doctrine /
  RA2 Tesla Overload upgrades draining integrity at the same ratio as their un-upgraded base weapon.
  Full root-cause + fix write-up, plus a reply-letter with suggestions for the still-queued flat-EMP
  cleanup, lives in `docs/design/EMP_INTEGRITY_SYSTEM.md` §3c and §6 — read those before touching the
  flat-EMP sweep (§4 there) or the Quantum Tesla-typing decision (§2 there).

**TODO — resume queue (in order):**
1. **ADOPT the Sonic family** (needs a maintainer warhead order — rule 4): nothing inherits
   `^Warhead_Sonic_*` yet, so the baked mark is inert. Candidates are the TS GDI sonic weapons
   (`TSSonicZapWeapon`/`…Sonic` = the Disruptor, currently Tesla+Magic; `TSVulcanGunSonic`,
   `TSAssaultCannonSonic`, `TSHellfireSonic`, `TSBombSonic`, `TSGrenadeSonic` = sonic UPGRADE variants
   still on the legacy `^SmallArms`/`^Chaingun`/`^TeslaWeapon`/`^MagicWeapon` inline templates) and RA2
   `SonicZap`. Same shape as the cryo retrofit (§3b): the upgrade ADDS `^Warhead_Sonic_*` as a second
   warhead rather than replacing the base one — never drop a damage TYPE.
2. **BUILD 4 — new axes:** Armor Breach (new PhysicalState axis on defaults, mirror Temperature +
   `DamageMultiplierProportional`, AP/Railgun feed it; grey overlay + breach-icon @100%); Hex (Magic →
   −firepower/inaccuracy condition); Knockback = new C# `PushWarhead` in `OpenRA.Mods.Cameo/Warheads/`.
3. **PIPELINE — cryo 75% tax:** wire the "cryo weapon = 0.75× effective damage" invariant (§3b) into
   `extract_stats`/`fit_class`/`apply_balance` (a cryo tag → auto FirepowerMultiplier).
4. **RETROFIT cryo-upgrade weapons** (RA1 Allies etc.): armament-swap to a variant that adds `^Warhead_Cryo_*`
   (dual/triple, §3b) + the FP tax; replace the old manual `ApplyPhysicalState` rings.
5. **MIGRATE** the Schwarzer Mond binary `corroded` → the Corrosion meter (Chemical/Plasma weapons feed
   it via the wired templates). Verify overheat/corrosion DoT credits `firedBy` for XP
   (`ChangesHealthProportionalToPhysicalState`).
6. **ART** (artist): looped shifting-blue Sonic overlay + armor-breach breach-icon (PngSheet, §4b).
7. Then the broader roadmap: faction damage-type binding, temporal signatures, spread/falloff per-type
   curves, Railgun charge-delay, resume Phase B mixed-weapon collapse (~350, behavior-preserving).

**Guardrails to keep:** boot-gate every commit (kill lingering OpenRA before a C# rebuild — it locks
`engine/bin`); `verify_generator_sync` drift stays **0** (regenerated `^Warhead_Sniper_Light` now matches the
generator); scoped `git add`; family PhysicalState goes on the main and percentage warheads (chip excluded).

## 6. Decisions (maintainer 2026-08-09) + what's still open
DECIDED:
1. **Corrosion peak** = DoT + slow + vuln (values in §2). Hazmat halves the DoT.
2. **Cryo = a thin child of Prism** — `^Warhead_Cryo_*` inherits `^Warhead_Prism_*` and only adds Temperature −100; base Prism (Prism Tank / Athena Cannon) stays freeze-free. Prism anti-LIGHT Versus already locked.
3. **New axes to build:** Armor Breach + Hex + Knockback (new C# `PushWarhead`) + the base wiring (Corrosion/Prism-cryo/Plasma/Sonic).
4. **Sonic** = global `CommandoDebuff → SonicDebuff`, baked into `^Warhead_Sonic_*` (predator laser + waveforce keep applying it). **BUILT `5a14355e6`** — the family templates now grant the mark themselves; the three hand-tuned grants (GDI predator laser 22/222, Japan waveforce 222/666 + 150/1500, RA2 `IonPulseDischarge`'s 4 expanding rings) were only renamed, not folded, because converting their warheads is a separate permission-gated change.
5. **Every axis needs its own art** (§4b) — green pulsating corrosion overlay + armor-breach breach-icon are NEW assets.

6. **Plasma Versus** = the **per-armor blend (average) of the Flame and Chemical ladders** (maintainer:
   "as close as possible to the flame + chemical combo"). The generator computes it from the two
   families — no hand-authoring. Plasma then applies +50% heat & +50% corrosion (§3). RESOLVED.

STILL OPEN:
- **XP/kill attribution** of overheat/corrosion DoT — verify `ChangesHealthProportionalToPhysicalState`
  credits the original attacker (`firedBy`), not the trait/self, so flame/acid kills grant XP. (Build.)
- **Sonic + armor-breach art** (§4b) — new PngSheet assets (artist); yaml wires with placeholders.
- **MagicDeath death type** (2026-08-10) — Magic weapons currently use `ElectricityDeath` as a placeholder.
  A dedicated `MagicDeath` death type should be added: wire it to the existing `gendeath.shp` mutation
  animation (Yuri Genetic Mutator's `mutate` explosion sequence) via a new `MagicDeathEffect` weapon
  (like `MutateEffect` but WITHOUT the `SpawnActor` warhead — pure visual only). Implementation:
  (1) add `MagicDeath: 8` to `^TDRAInfantry` `WithDeathAnimation.DeathTypes` in `defaults.yaml`,
  (2) add `FireWarheadsOnDeath@MagicDeath` on `^Infantry` pointing to `MagicDeathEffect`,
  (3) create `MagicDeathEffect` weapon (`Explosions: mutate`, `ExplosionPalette: playerra2`, no SpawnActor),
  (4) replace `ElectricityDeath` with `MagicDeath` on all `^Warhead_Magic_*` and `^Warhead_Storm_*` templates.
  The `gendeath.shp` animation already exists in `mods/cameo/bits/ra2/` and is already registered as the
  `mutate` sequence in `sequences/misc.yaml`. Note: `PsychicDeath` (sequence 5) is reserved for Yuri
  mind-control weapons and should NOT be reused for generic magic.
