# The projectile and effect layers — templates, sourcing, and per-game bases

The two lower layers of the weapon 3-way split, in one file. The warhead layer is
[`WEAPON_3WAY_SPLIT.md`](WEAPON_3WAY_SPLIT.md) + [`WEAPON_TYPE_SYSTEM.md`](WEAPON_TYPE_SYSTEM.md);
this covers what a `^Projectile_*` / `^Effect_*` template should contain, where the per-game
art and sound come from, and which game-specific base templates exist.

⚠ **Every weapon needs its OWN explicit `Report:`.** A silently-inherited fallback sound is a
real bug class here — `RA2PatriotThunderboltMissile` never had one and inherited a classic-CnC
fallback for its entire existence, while its sibling on the same launcher had the right RA2
sound the whole time.

---

## What belongs in a projectile template, and what should be DERIVED

_Merged 2026-08-23 from `docs/design/PROJECTILE_TEMPLATES.md`, unedited below this line._

**Maintainer 2026-08-17**, on finding that the three cannon projectile templates are the same
sprite: *"for cannons there is really only one cannon projectile so does it really make sense to
have light, medium and heavy cannons for the projectiles?"* … *"The sound should be always part
of the inlined weapon and not of the template anymore!"* … *"I want to see if we can bake the
inaccuracy and the speed already in the C# classes so we can just use that as a default."*

---

### 1. The measurement that started it

```
^Projectile_Shell_Light    Image: 120MM  Speed: 500  Inaccuracy: 150  Report: cannon1.aud
^Projectile_Shell_Medium   Image: 120MM  Speed: 500  Inaccuracy: 300  Report: tnkfire6.aud
^Projectile_Shell_Heavy    Image: 120MM  Speed: 500  Inaccuracy: 450  Report: tnkfire6.aud
```

Identical sprite, identical speed, identical shadow. The three-level split carries **one real
axis (`Inaccuracy`)** and a half-axis (two sounds across three levels). Missiles genuinely differ
— `^Projectile_Missile_*` and the TS set use different sprites — so the split earns its keep
there and does not here.

### 2. THE LAW — a projectile template describes the PROJECTILE

> A `^Projectile_*` template encodes what the projectile **is**: sprite (`Image`, `Sequences`),
> flight (`Speed`, `Shadow`, contrails, `HorizontalRateOfTurn`), and nothing else.
> **Sound belongs to the weapon. Balance numbers are DERIVED from the weapon's `Range`.**

Consequences:
* `^Projectile_Shell_{Light,Medium,Heavy}` collapse to **one** `^Projectile_Shell`.
* `Report:` moves out of every projectile template and onto each weapon inline — the maintainer's
  order, and it also unblocks the effect/sound pairing work, since a sound can then be chosen per
  weapon instead of inherited from a shared flight template.

### 3. Inaccuracy — the engine already scales it; the VALUE should be derived

⚠ **A distinction that is easy to miss.** `BulletInfo.InaccuracyType` defaults to
**`Maximum`**, documented as *"scale from 0 to max with range"*. So the current templates
**already scale inaccuracy with the shot's distance** — a Shell fired at half range is already
half as inaccurate. The three options:

| `InaccuracyType` | behaviour | fits |
|---|---|---|
| `Maximum` *(default)* | scales 0 → the stated value as the shot approaches max range | cannons |
| `PerCellIncrement` | grows from 0 by a fixed amount per cell, unbounded | artillery, artillery rockets |
| `Absolute` | the stated value regardless of distance | special cases only |

What is missing is not the scaling but **the stated value**, which is hand-written per template.
The maintainer's rule makes it derived:

```
Inaccuracy = InaccuracyPercentage% of the weapon's Range      (cannons: 1%)
Speed      = ProjectileSpeedPercentage% of the weapon's Range  (cannons: 10%, artillery: 2%)
```

⚠ **CORRECTION (measured 2026-08-17).** This document said *"the existing Shell templates are
`Speed: 500`, so 10% is already the de-facto convention and baking it in changes nothing."* That
was arithmetic on one hypothetical 5000-range cannon, not a measurement. Across the **145 weapons**
that actually inherit a `^Projectile_Shell_*` template:

| | today | derived at 10% of Range |
|---|---|---|
| Speed | flat **500** for all 145 | **300 … 1400** — `0.60×` to `2.80×`, and exactly ONE weapon lands on 500 |
| Inaccuracy | 150 / 300 / 450 by template | **30 … 140** — `3.2×` to `11.8×` tighter |

So deriving Speed is a real change: most cannons get a *faster* shell (the bulk land 540–700) and
the longest-ranged get 2.8×. Deriving Inaccuracy is a large accuracy buff, and E6 prices
inaccuracy at zero, so it would be free until E6 lands. Both go through the pipeline.

> ### ⛔ IT WAS NEVER RUNNING — fixed 2026-08-22
>
> `ScaledBullet` has carried `InaccuracyPercentage: 1` and `ProjectileSpeedPercentage: 10` on
> `^Projectile_Shell` for weeks, and **neither ever reached a single weapon.** The reason is in
> `ScaledBullet.cs`'s own comment: it derives a value **only when the field is still at
> `BulletInfo`'s default**, because FieldLoader cannot report which keys the yaml actually
> contained — so *an explicit yaml value always wins*. `^Projectile_Shell` also wrote
> `Speed: 500`, and `^Projectile_Shell_{Light,Medium,Heavy}` each wrote
> `Inaccuracy: 150/300/450`. Every one of those literals switched the derivation back off, for
> all **145** shell weapons.
>
> The literals are deleted. `Inaccuracy = 1% of Range` and `Speed = 10% of Range` now actually
> reach the engine, which is what the maintainer asked for again on 2026-08-22: *"for tank shells
> those should scale their inaccuracy with their maximum range."*
>
> **The general lesson:** a "derive it unless overridden" default is invisible when something
> upstream always overrides it. Assert the derived value on a real weapon, never just that the
> percentage field is present.

⭐ **The measurement also settles the collapse question.** The Light/Medium/Heavy assignment does
not correlate with range at all — `120mm_cobra` sits on `Shell_Light` at Range 7640 while `105mm`
sits on `Shell_Medium` at 5469. The three templates differ ONLY in a hand-written `Inaccuracy`, and
once that number is derived from each weapon's own Range there is nothing left to distinguish them
(same `Image`, same speed rule, same shadow) except two sounds that are moving onto the weapons
anyway. **The three-way split is not carrying an axis; the data says collapse it.**

⚠ **Inaccuracy is NOT already at 1%.** Current Shell values on a 5000-range cannon are
150 / 300 / 450 = **3% / 6% / 9%**. Adopting 1% makes cannons **3–9× more accurate** — a real
balance change, not a refactor, and it should go through the pipeline rather than ride along with
a cleanup. It also interacts with **E6** (inaccuracy is priced at zero today), so making cannons
accurate for free would be a silent buff until E6 lands.

#### The per-family table (proposed)

| family | `InaccuracyType` | inaccuracy | rationale |
|---|---|---|---|
| Cannon (direct fire) | `Maximum` | 1% of Range | aimed weapon; error grows with distance |
| Artillery shell | `PerCellIncrement` | per-cell | indirect fire; error compounds, unbounded |
| Artillery rocket (e.g. `latinsyndicate_burrito`, MissileHE) | `PerCellIncrement` | per-cell, **larger than a shell** | unguided rocket, worse dispersion than a rifled barrel |
| MissileAP / MissileAA | `Absolute` | **0** | guided; accuracy is the point. Spread lives in the WARHEAD, not here |

**Shell vs rocket** — the maintainer asked whether there should be a difference. There should, and
the physical reason gives the direction: a shell leaves a rifled barrel with a predictable
ballistic arc, while an unguided rocket accumulates error the whole time its motor burns. So both
are `PerCellIncrement`, and the **rocket's per-cell increment is larger**. Speed differs the same
way: a rocket accelerates, so its `ProjectileSpeedPercentage` is lower than a shell's off the
line.

### 4. ✅ IMPLEMENTED — `ScaledBullet`, and it is NOT a shadow

Shipped as `OpenRA.Mods.Cameo/Projectiles/ScaledBullet.cs`. Three findings changed the plan this
document originally set out:

* ⭐ **No shadow, and no 367-line copy.** `Ruleset.cs:70` calls `RulesetLoaded` on the projectile
  info with the firing `WeaponInfo` — so `ScaledBulletInfo : BulletInfo, IRulesetLoaded<WeaponInfo>`
  reads `Range` at LOAD time and derives both values once, inheriting every existing field
  (`Image`, `Sequences`, `Shadow`, `TrailImage`, `InaccuracyType`, …) for free.
* **Deliberately a NEW type rather than a `Bullet` shadow.** This document warned that shadowing
  `Bullet` silently changes every weapon that says `Projectile: Bullet` — the most-used projectile
  in the mod. A separate name means a template opts in and nothing else moves.
* The derived values are written through the same reflection FieldLoader itself uses on
  `public readonly` fields, which is why no engine change is needed.

```
InaccuracyPercentage: 1        # of the weapon's Range; 0 disables
ProjectileSpeedPercentage: 10  # of the weapon's Range, in WDist/tick; 0 disables
```

⚠ **An explicit `Inaccuracy` / `Speed` in yaml still WINS**, so this is a default, never a
constraint. "Explicit" is detected as *differs from `BulletInfo`'s own default*, because
FieldLoader does not report which keys the yaml contained — so a weapon that deliberately writes
`Inaccuracy: 0` or `Speed: 17` **and** sets a percentage gets the derived value instead. Set the
percentage to 0 there.

The three Shell templates now say `Projectile: ScaledBullet` and carry both percentages **with
their explicit `Speed` / `Inaccuracy` kept**, so behaviour today is byte-identical and the boot
proves the type and its Cameo-only fields load (an unknown field throws at load). Deleting the
explicit lines is what activates the rules — and that is the balance change measured above.

### 5. The original plan — a mod-side shadow (superseded by §4)

`ProjectileArgs` carries the firing `WeaponInfo`, so the projectile can read `Range` at creation
and compute both defaults. That means a Cameo-side `Bullet` (and `Missile`) with two new fields:

```
InaccuracyPercentage    : int  (0 = disabled, use the explicit Inaccuracy)
ProjectileSpeedPercentage: int  (0 = disabled, use the explicit Speed)
```

An explicit `Inaccuracy` / `Speed` in yaml always wins, so this is a DEFAULT and never a
constraint — which is what makes it safe to roll out family by family.

⚠ **`Bullet` is the most-used projectile in the mod, so shadowing it is wide-reaching.**
`ObjectCreator.FindType` takes the first assembly in `mod.yaml`'s list (AS, CA, **Cameo**, Cnc,
D2k, Common), so an `OpenRA.Mods.Cameo.Bullet` silently replaces the Common one for **every**
weapon that says `Projectile: Bullet`. Prove the shadow is live before trusting it: give the
Cameo Info a field the engine's lacks and boot with that field set — `--docs` lists both types
and proves nothing (LESSONS_LEARNED).

### 5. Order of work

1. **Sound out of templates** (mechanical, no balance effect) — move every `Report:` from
   `^Projectile_*` onto the weapons that inherit it. Needs a sweep tool: a weapon that inherits
   two templates must end up with exactly the sound it resolves to today.
2. **Collapse `^Projectile_Shell_*` → `^Projectile_Shell`**, moving `Inaccuracy` to the weapons so
   resolved behaviour is preserved verbatim.
3. **Then** the C# defaults, family by family, starting with cannons.
4. **Separately, through the pipeline:** the 3% → 1% inaccuracy decision, which is balance.

### 6. ✅ IMPLEMENTED — dedicated artillery projectile families

Global `^Projectile_ArtilleryShell_Medium` and `^Projectile_ArtilleryRocket_Medium` now live in
`mods/cameo/weapons/weapons.yaml`. The rocket family was previously duplicated in
`mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml`; that copy was removed so the global
family is the single source of truth. `RA2RTruckRocket`, `TSChemVanMissile`, `TSChemMLRSMissile`,
and `Future_MultiMissile_Frag` all inherit the rocket family and keep their weapon-local
`Speed` / `Inaccuracy` / `LaunchAngle` / `Arm` overrides. The shell family is used by
`TSChemJuggerboat90mm`. Both families keep `Blockable: false` and `Shadow: true` by default.

---

## Per-game projectile and effect sourcing (RA2, TS)

_Merged 2026-08-23 from `docs/design/PROJECTILE_EFFECT_SOURCING.md`, unedited below this line._

Deep-research findings for the per-game projectile/effect layer of the weapon
3-way split (companion to `WEAPON_3WAY_SPLIT.md` + `GAME_SPECIFIC_WEAPON_BASES.md`).
Goal: build the `^Projectile_<fam>_<game>` and `^Effect_<fam>_<game>` template
libraries that dissolved weapons (`^RA2SmallArms` → atomic inherits) point at, and
identify missing RA2/TS art to replicate.

Sources studied (read-only reference mods, NOT dependencies):
- **RV** = `Romanovs-Vengeance-master/mods/rv/weapons/` — `defaults.yaml`, `missiles.yaml`,
  `bullets.yaml`, `explosions.yaml`, `flaks.yaml`, `mgs.yaml`, `gatling.yaml`.
- **SP** = `Shattered-Paradise-SDK-bleed/mods/sp/weapons/` — `weapondefaults.yaml`,
  `effectdefaults.yaml`, `explosionweapons.yaml`.

> **Headline finding:** SP already ships the exact 3-layer split cameo is building —
> separate `^RifleDamage` (warhead) / `^RifleWeapon` (projectile) / `^Small_Bang`
> (effect) template families. It is direct proof the architecture is sound; we can
> lift SP's effect library almost verbatim for TS.

---

### PART 1 — RA2 projectiles (from RV `defaults.yaml` + `missiles.yaml` + `bullets.yaml`)

RV routes every weapon through a tiny set of projectile bases. These map 1:1 to the
per-game templates cameo needs:

| Proposed cameo template | RV base | Projectile | Image | Signature traits |
|---|---|---|---|---|
| `^Projectile_Bullet_RA2` | `^MG` | `InstantHit` | — | hitscan, `Blockable: true` (no flight art — matches earlier finding) |
| `^Projectile_Shell_RA2` | `^LargeBullet` | `BulletAS` | `120mm` | `Speed 40c0`, `LaunchAngle 62`, `Shadow`, `Palette: ra` — the flat tank shell |
| `^Projectile_Missile_RA2` | `^Missile` | `Missile` | `DRAGON` | homing, `ContrailLength 8` / `ContrailStartWidth 38`, `ContrailEndColorUsePlayerColor: true`, `CruiseAltitude 4352`, turn-rate 220 |
| `^Projectile_Flak_RA2` | `^Flak` | `BulletAS` | `120mm` | `LaunchAngle 128`, arc; AA variant `^AAFlak` uses `InstantHit` |
| **`^Projectile_BallisticMissile_RA2`** (NEW, you requested) | `APTusk` / `V3StormStrike` | `BulletAS` | `radiationmissile` / `DRAGON` | `LaunchAngle 62`, `TrailImage: smokeyv3`, `Sequences: down`, arcing — V3 rocket / Dreadnought / Boomer sub |

#### The contrail-color convention (variant encoding) — this is the key generalization
RV keeps ONE projectile per family and expresses the *variant* purely through
`ContrailStartColor`. Adopt this verbatim:

| Colour | Meaning | Seen on |
|---|---|---|
| `D8D8FF` | standard (light blue-white) | default missiles (HoverMissile, MissileLauncher) |
| `FFFFFF` | pure white | artillery shells (Grand Cannon, Howitzer, mortars) |
| `00b6ff` | **Boosted** (cyan) | `*Boosted` variants |
| `EA0000` | **Elite** (red) | `*E` variants |
| `FF8888` | Boosted+Elite (pink) | `*BoostedE` |
| `A8FFA8` | virus/toxin (green) | Mosquito |
| `FFA8FF` | chaos (magenta) | Chaos rocket |
| player-colour END | team identity | `ContrailEndColorUsePlayerColor` on all missiles |

So the "RA2 missile with classic white contrail + launch angle" you described =
`^Projectile_Missile_RA2` with `ContrailStartColor: D8D8FF` (or `FFFFFF`) + `MinimumLaunchAngle
/ MaximumLaunchAngle: 255` (vertical VLS). Light and Medium share this projectile and
differ only by contrail colour / speed; **Heavy/ballistic** (V3, Dreadnought, Boomer)
gets the separate `^Projectile_BallisticMissile_RA2` with the `smokeyv3` trail, exactly
as you called out.

#### Launch-angle convention
- `255` (min=max) → vertical VLS launch, then homing → all standard missiles.
- `62` → flat direct-fire → tank shells (`^LargeBullet`).
- `120`–`196` → arcing → mortars, artillery, grenades.

---

### PART 2 — RA2 effects (from RV `defaults.yaml` + `explosions.yaml`)

RV's impacts are a **named size-ladder** of explosion sprites on a few palettes:

| Family ladder | sprites (small → large) |
|---|---|
| bang | `small_bang` · `medium_bang` · `large_bang` |
| collision | `small_clsn` · `medium_clsn` · `verylarge_clsn` |
| burn | `small_brnl` · `medium_brnl` · `large_brnl` |
| twilight/tumult | `large_twlt` · `large_tumu` |
| grey | `small_grey_explosion` · `medium_grey_explosion` |
| flak | `flak_puff` (ground) · `flak_puff_AA` (air) |
| specials | `terrorist_explosion`, `demotruck_explosion`, `nuke_explosion`/`nuke_ball`, `tesla_explosion`, `ivan_explosion`, `chaosgas50p`, `apoc_explosion`, `elite_explosion` |

Palettes: `ra` (unit), `tseffect`, `effect`, `player` (team-tinted), `effect50alpha`.
Water impacts always pair a `*_watersplash` (`small`/`large`/`huge`) CreateEffect.

Proposed per-family RA2 effect templates (impact + water + smudge, from the RV bases):

| cameo template | content (RV origin) |
|---|---|
| `^Effect_Bullet_RA2` | `ra2_piff` / `piffpiff` ground puff (already inline in `^RA2SmallArms` today) |
| `^Effect_Shell_RA2` | `medium_explosion` + `MediumCrater` smudge (`^LargeBullet`/`GrandCannonWeapon`) |
| `^Effect_Missile_RA2` | `small_grey_explosion` + `small_watersplash` + `SmallCrater` (`^Missile`/`HoverMissile`) |
| `^Effect_Flak_RA2` | `flak_puff` ground / `flak_puff_AA` air (`^Flak`/`^AAFlak`) |
| `^Effect_BallisticMissile_RA2` | `terrorist_explosion` + `MediumCrater, MediumScorch` (`V3StormStrike`) |
| `^Effect_Nuke_RA2` / `^Effect_Tesla_RA2` / `^Effect_Toxin_RA2` | the named specials above |

---

### PART 3 — TS projectiles & effects (from SP — near drop-in)

SP is TS-era and already 3-way-split. Lift it almost directly.

#### TS projectiles (SP `weapondefaults.yaml`)
| cameo template | SP base | Projectile | Signature |
|---|---|---|---|
| `^Projectile_Bullet_TS` | `^RifleWeapon` / `^VulcanWeapon` | `InstantHitWithFakeBullets` | fake tracer bullets, contrail `FFFF00→FFAA00` (yellow) |
| `^Projectile_Shell_TS` | `^ArmorPierceAmmoWeapon` | `BulletAS` | `Image: cannonball`, `TrailImage: cannonsmokecircle`, contrail `BBC366→FF3311` |
| `^Projectile_Missile_TS` | `^RocketWeapon` | `MissileTA` | `Image: DRAGON`, `Sequences: idle2`, `TrailImage: small_smoke_trail`, `JetImage: explosion` (rocket flame), player palette, `CruiseAltitude 6000`, VLS angle 255 |

#### TS effects (SP `effectdefaults.yaml`) — the whole named library is reusable
`^Piffs`/`^PiffsCyan` (bullet), `^Tiny_Explo`, `^Small_Clsn`/`^Mediuml_Clsn`/`^Large_Clsn`,
`^Small_Brnl`/`^Medium_Brnl`, `^Small_Bang`/`^Medium_Bang`, `^GreyExplo`,
`^Large_Explosion`, `^Small_Twlt`/`^Mediumtwlt`/`^Large_twlt`, `^FlameScorch`/`^FlameScorchBlue`,
`^Scrin_Pulse`/`^Scrin_Explo`, `^GreenPlasmaExplosion`, `^MeleeClaw`, `^Shrapnel`.
Palette: `gensmkexploj` (the TS smoke/explosion palette); water pairs `*_watersplash`
on `terrain`; every effect leaves a `LeaveSmudgeSP` crater/scorch.

Proposed mapping:
| cameo template | SP origin |
|---|---|
| `^Effect_Bullet_TS` | `^Piffs` (+`^PiffsCyan` for energy) |
| `^Effect_Shell_TS` | `^Small_Clsn` / `^Mediuml_Clsn` |
| `^Effect_Explosion_TS` | `^Small_Bang` / `^Medium_Bang` / `^Large_Explosion` |
| `^Effect_Flame_TS` | `^FlameScorch` (+`^FlameScorchBlue`) |
| `^Effect_Laser_TS` / `^Effect_Tesla_TS` | `^LightningDefault` / `^GreenPlasmaExplosion` |

> ⚠ **Armour-taxonomy caveat.** SP uses the TS armour set (`Infantry/Building/Light/
> Heavy/Defense/Aircraft/Concrete`); RV uses the RA2 set (`None/Flak/Plate/Light/Medium/
> Heavy/Wood/Steel/Concrete/Drone/Rocket`). Cameo has its OWN armour ladder — so we lift
> **projectile + effect (art only)** from these mods and keep cameo's central warheads /
> Versus tables. Never copy their `Warhead@…Dam` Versus blocks.

---

### PART 4 — Missing RA2/TS art to replicate & open items

**What cameo already has:** central `^Projectile_Missile_*` on classic `DRAGON` + `smokey`
trail; generic classic impacts (`piff`, `water_piff`). Bullets are hitscan (fine).

**What RV/SP add that cameo's RA2/TS weapons still lack (candidate imports):**
1. **Contrail-colour variants** (`D8D8FF`/`EA0000`/`00b6ff`…) — behaviour-only, no new
   sprites; apply on the new `^Projectile_*_RA2` templates.
2. **Ballistic-missile trail** `smokeyv3` + `radiationmissile` image (V3/Dreadnought/Boomer).
3. **RA2 shell** `120mm`/`160mm`/`cannonball` images + `cannonsmokecircle` trail.
4. **TS rocket** `JetImage: explosion` flame + `small_smoke_trail`.
5. **Named effect ladders** (`*_bang`/`*_clsn`/`*_brnl`/`flak_puff`) + palettes
   `ra`/`tseffect`/`gensmkexploj`.

Each candidate needs an **asset check** (does the `.shp`/palette already ship in cameo,
or must it be imported from RV/SP `artsrc`?) before implementation — that asset audit is
the next concrete step and is NOT yet done here.

**Open naming decision (from `GAME_SPECIFIC_WEAPON_BASES.md` §5.2):** game suffix casing
& order — `^Projectile_Missile_RA2` (recommended: central `…_<Level>`-style grammar, game
as most-specific suffix, `RA2` all-caps to match `^RA2…` bases and the `RedAlert2` folder).

**Sequencing:** RA2 first (largest, most inlined), then TS. Build order per game:
projectile templates → effect templates → dissolve the game bundles (`^RA2SmallArms` …)
onto the atomic `@wh`(central) + `@proj`(game) + `@fx`(game) inherits.

---

### PART 5 — cameo's CURRENT state (PRESERVE — do not regress)

Cameo already does a lot of this well; the task is to STRUCTURE it, not replace it.

#### 5.1 The CABAL faction template — the per-faction exemplar
`ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml` already ships `^CabalMissile`:
```
^CabalMissile:                       # inherited @5 (last) by every CABAL missile
	Projectile: Missile
		MinimumLaunchAngle: 255 / MaximumLaunchAngle: 255   # TS-vertical (SP's 90°)
		HorizontalRateOfTurn/VerticalRateOfTurn: 80         # tuned not to overshoot
		CruiseAltitude: 6000
		TrailImage: cabal_rockettrail                       # CABAL blue = faction identity
	Warhead@Effect: CreateEffect
		Explosions: cabal_missileexplosion                  # CABAL impact
```
This is a **per-faction projectile+effect template** (no warhead) — the exact thing to
generalize. Note it **combines** the projectile and effect layers in ONE template
(inherited last so its projectile wins), rather than splitting `@proj` + `@fx`.

#### 5.2 Current inline per-weapon art (looks good — keep it)
RA2 weapons already carry per-weapon `ContrailStartColor` (BB8866, 88BB66, E60000,
EEEE00, 00EE00, 88FF44 …), `LaunchAngle` / `MinimumLaunchAngle`, trail images, and
impact overrides — e.g. the deployed Guardian GI (`RA2GIRocketsG`, `MinimumLaunchAngle:
200`) and its elite (`red_dragon` + `red_smokey` + `ContrailStartColor: E60000`). The
maintainer confirms the white contrails + launch angles look good. **Any restructure
must reproduce these values, not flatten them.**

#### 5.3 The intended THREE-tier hierarchy (per maintainer)
| Tier | Who uses it | Example |
|---|---|---|
| **Central** (global fallback) | factions with no own art yet | classic `piff`, `DRAGON`+`smokey` |
| **Per-game original** | ORIGINAL RA2 / TS factions (Allies, Soviets, GDI, Nod) | RA2-authentic look (RV-sourced), TS-authentic (SP-sourced) |
| **Per-faction unique** | custom / crossover factions | `^CabalMissile` blue trail; Yuri green; Naxis; etc. |

So each faction can have its own projectile + effect artwork (like CABAL), while the
original TS/RA2 factions deliberately fall back to the original-game look.

#### 5.4 Structural comparison (what to adopt)
| Approach | Structure | Trade-off |
|---|---|---|
| **cameo current** | per-weapon inline contrail/launch/effect | explicit, works, looks good; but art scattered, not DRY, not relocatable |
| **RV** | one shared `^Missile`/`^LargeBullet` base + per-weapon `ContrailStartColor` variant | DRY; variant via colour only; one base per family |
| **SP** | fully split `^RifleDamage`/`^RifleWeapon`/`^Small_Bang` | the pure 3-way ideal; many named templates |
| **CABAL (cameo)** | per-faction combined proj+fx template, inherited last | faction identity in one place; but merges `@proj`+`@fx` |

---

### PART 6 — DECISIONS (maintainer, 2026-08-03) + launch-angle finding

**Locked invariant.** Every weapon inherits **exactly ONE `@proj` + exactly ONE
`@fx`**, plus its warhead(s) mixed under the TYPES×LEVELS budget (1/2/4, see
`cameo-tier-weaponclass-law`). No weapon carries two projectile or two effect inherits.

**Granularity — SPLIT everything.** Projectile and effect are always separate templates
(`^Projectile_<fam>_<scope>` + `^Effect_<fam>_<scope>`), never combined. `^CabalMissile`
(the proj+fx bundle) is therefore **split** into `^Projectile_Missile_Cabal` +
`^Effect_Missile_Cabal`.

**Three-tier scope.**
- **Central** = global classic fallback (factions with no own art).
- **Per-game shared** = ORIGINAL factions of a game share it. Confirmed: **TS GDI + Nod
  share the same original TS art** → one `_TS` set; likewise RA2 Allies + Soviets → `_RA2`.
- **Per-faction unique** = crossover / custom factions get their OWN art. Confirmed
  unique: **Forgotten, CABAL** (and similar). CABAL blue trail stays, just split.

**Minimize inlining.** The template is the default; a weapon overrides it only when
*absolutely necessary*. The current good inline art (Guardian GI launch, elite red
trails, contrail colours) is preserved by folding the common case into templates and
leaving only true exceptions inline. **Move cameo's projectiles/effects closer to RV/SP.**

**Launch-angle investigation (answered).** RA2 sets a launch angle at 108 sites with no
dominant value (0,5,25,30,45,50,60,64,66,70,75,83,96,100,111,120,125,128,180,200,222,255…).
It CANNOT be one global value — but it clusters into **launch STYLES = projectile
subtypes**:
| Style | angle band | subtype template | examples |
|---|---|---|---|
| Vertical VLS homing | ~200–255 (min=max) | `^Projectile_Missile_<scope>` | Guardian GI (200), most homing SAMs |
| Ballistic arc | ~111–128 | `^Projectile_BallisticMissile_<scope>` | V3, Dreadnought, Boomer, artillery |
| Direct / low | ~0–75 | direct variant or inline override | flat-fire rockets |
So launch angle **moves into the projectile template per launch-style**, with a canonical
angle each; only genuine oddballs override. Guardian GI's 200 = the Vertical-VLS default.

**Sequence unchanged:** RA2 first, then TS; projectile templates → effect templates →
dissolve game bundles onto `@wh`(central) + `@proj` + `@fx`. Mechanical Phase-2 family
retrofits continue in parallel (they don't touch this layer).

---

## Game-specific weapon base templates

_Merged 2026-08-23 from `docs/design/GAME_SPECIFIC_WEAPON_BASES.md`, unedited below this line._

Research findings — companion to `WEAPON_3WAY_SPLIT.md` and the storage-architecture
question (per-game Shared projectiles/effects). Triggered by the `^TSDefaultMissile`
smell: *"It should only be the projectile, and a special explosion should be its own
effect inherit."* Correct — this doc catalogs every such base and how it decomposes.

Data source: accurate per-`^template` parse of the per-game weapon files
(`mods/cameo/weapons/{tiberiansun,redalert2,redalert2mod,d2k,tiberiandawn}.yaml`).
Central library + the 26 old full-stack templates live in `weapons.yaml` and are
covered by the main runbook; this doc is only about the **per-game intermediates**
that sit between the central templates and the concrete unit weapons.

---

### The 5 categories

| Category | Meaning | Roster |
|---|---|---|
| **ALREADY-3WAY** | Inherits central `@wh + @proj + @fx`, then adds a game-specific impact effect. The intended shape — except the game effect is *inlined* (see §3). | RA2: `^RA2SmallArms` `^RA2Chaingun` `^RA2FlakWeapon` `^RA2LightMissile` `^RA2MediumMissile` `^RA2HeavyMissile` `^RA2TankDestroyerCannon` `^RA2MediumCannon` `^RA2HeavyCannon`; TS: `^TSMG`; D2k: `^D2K_Cannon` `^D2KRocket` `^OCannon` |
| **PROJECTILE-base** | Has its own `Projectile:` art (game/faction sprite + trail) and often its own impact; carries **no** central warhead. This *is* the per-game projectile/effect layer — just not yet named/structured as `^Projectile_*` / `^Effect_*`. | TS: `^TSCannon` `^TSCannonEffect` `^TSLaserEffect` `^TSSonicGrenade` `^TSArtilleryWeapon` `^TSHealWeapon`; RA2: `^RA2MG`; RA2mod: `^SteelSmallArms` `^SteelChaingun` `^SteelLightMissile` `^SteelMediumMissile` `^SteelHeavyMissile` `^SteelMediumCannon` `^SteelHeavyCannon` `^LunarNaxGreenLasers` `^LunarNaxisUpgradedCannons`; D2k: `^HeavyMachineGunProjectile` `^D2KMissile` `^ORocket` `^OMissile` `^OMG`; TD: `^AMTProjectile` `^HVProjectile` |
| **single-old-WH** | Thin wrapper: inherits ONE central old template + a game effect. **Auto-converts** when that family runs in Phase 2 — no special handling. | RA2: `^RA2Grenade` `^RA2TeslaWeapon` `^RA2LaserWeapon` `^RA2RailgunWeapon`; TS: `^TSIonBeam`; RA2mod: `^AsianIonBeam` |
| **DUAL/STACK-WH** | Legacy hack: inherits **two** warhead bases to blend two armor-vs curves. Needs a maintainer-directed collapse to a single warhead (Phase 3). | TS: **`^TSDefaultMissile`** (the only true one left) |
| **other** | Effect/damage fragments (radiation, elite muzzle FX, energy blast) with no clean single warhead. | TS: `^TSEnergyBlast`; RA2: `^RA2EliteEffects` `^RA2RadShell`; RA2mod: `^NaxOxidationShells` |

Takeaway: after accurate parsing, the per-game base landscape is **healthy**. There is
only **one** real dual-warhead-stack base (`^TSDefaultMissile`); the rest are either
already-split, thin wrappers that convert automatically, or genuine per-game
projectile/effect art that the storage architecture already wants to relocate.

---

### §1 — Case study: `^TSDefaultMissile` (the trigger)

```
^TSDefaultMissile:
	Inherits: ^MediumMissile          # warhead base #1
	Inherits: ^LightMissile           # warhead base #2   <-- the smell
	ReloadDelay: 50
	Range: 6643
	Report: missile6.aud              # firing sound -> PROJECTILE layer
	Warhead@MediumMissile: SpreadDamage   { Damage: 10000 }
	Warhead@MediumMissilePercentage: HealthPercentageDamage { Damage: 5 }
	Warhead@LightMissile: SpreadDamage    { Damage: 10000 }
	Warhead@LightMissilePercentage: HealthPercentageDamage { Damage: 5 }
```

What it actually is: **not** a projectile and **not** an effect — it is a *dual-warhead
tuning wrapper*. It carries no `Projectile:` block and no `CreateEffect` of its own; it
inherits missile delivery + explosion from the central `^MediumMissile`/`^LightMissile`,
then stacks two SpreadDamage warheads (10000 each) so every hit applies **both** the
Medium and the Light armor-vs table at once — a legacy approximation of a specific curve.

Used by 5 weapons; each **overrides the projectile art per unit** (`Image: tsnodmmsil`,
`TrailImage: black_smokey`, …), so TS missiles are unit-specific art, not one shared sprite.

**Decomposition (target shape):**
- `@wh:` — resolve **per user by unit tier**, NOT one global warhead (maintainer,
  2026-08-03). Per the Tier↔WeaponClass law (
  `weapon_classes.yaml` header): T1→`^Warhead_MissileAP_Light`, T2→`_Medium`,
  T3+→`_Heavy`; a **between-tier** unit keeps *both* adjacent levels (the Medium+Light
  stack is a legitimate between-T1/T2 weapon, not merely a hack). Warhead budget =
  TYPES×LEVELS (≤2, or 4 only for a between-tier lore hybrid). Warhead changes still
  need sign-off per `cameo-warhead-change-permission`.
- `@proj: ^Projectile_Missile_<lvl>` carrying `Report: missile6.aud`; each unit keeps its
  own `Image`/`TrailImage` override (or gets a faction projectile). Lives in **TS Shared**.
- `@fx:` central `^Effect_Missile_<lvl>` unless the unit has a special explosion, in which
  case its own `^Effect_Missile_TS…` (see §3).

Until the maintainer picks the collapse profile, `^TSDefaultMissile` correctly stays a
Phase-B **mixed** template: the retrofit tool leaves it and its children untouched (this
is what the resolution-based repair now guarantees — its children keep their
`-Warhead@MediumMissile` removals instead of orphaning).

---

### §2 — The `single-old-WH` wrappers convert for free

`^RA2Grenade`, `^RA2TeslaWeapon`, `^RA2LaserWeapon`, `^RA2RailgunWeapon`, `^TSIonBeam`,
`^AsianIonBeam` each inherit exactly one central old template. They are **single-inherit**,
so `retrofit_weapon_family.py --old <family>` converts them automatically when that family
runs (Grenade → Phase-2 explosions; Tesla/Laser/Railgun → the Energy pass). No manual work;
they only look untouched today because those families haven't run yet.

---

### §3 — The inlined-effect pattern (ALREADY-3WAY bases)

The RA2 bases do the right thing structurally but inline the game explosion instead of
naming it:

```
^RA2SmallArms:
	Inherits@fx: ^Effect_Bullet_Light     # central: Warhead@Effect = piff
	Warhead@Effect: CreateEffect          # OVERRIDE same key -> ra2_piff (clean, not doubled)
		Explosions: ra2_piff
	Warhead@EffectAir: CreateEffect        # NEW key -> adds an air variant
		Explosions: ra2_piff
```

The override is **clean** (same `Warhead@Effect` key → replaces `piff` with `ra2_piff`;
verified — no double impact). But it means the RA2 look is buried inside a warhead override
rather than being a reusable, relocatable template.

**Recommendation (storage architecture):** extract each game explosion into its own
`^Effect_<family>_<game>` template in that game's `Shared/` folder, and have the base
inherit it:

```
^RA2SmallArms:
	Inherits@wh: ^Warhead_Bullet_Light
	Inherits@proj: ^Projectile_Bullet_Light
	Inherits@fx: ^Effect_Bullet_RA2       # <- RA2 Shared, replaces the inline override
```

Minor latent bug noted for later: `^RA2SmallArms`'s `Warhead@Effect` keeps the parent's
`ValidTargets: Ground, Ship, Air` while also adding `Warhead@EffectAir` → air targets get
`ra2_piff` twice. Fold the fix into the extraction (give `Warhead@Effect` ground-only
targeting).

---

### §4 — Storage placement

| Layer | Central (global fallback) | Per-game Shared | Per-faction |
|---|---|---|---|
| **Warhead** | ✅ all `^Warhead_*` (artwork-independent) | — | — |
| **Projectile** | generic classic art (TD/RA1 `piff`, `120mm`, `DRAGON`) as fallback | TS/RA2/D2k/SC shared missile & shell sprites + trails (`^Projectile_Missile_TS`, …) | only if a single unit's projectile is unique |
| **Effect** | generic classic impacts as fallback | game explosions (`^Effect_Bullet_RA2`, `^Effect_Missile_TS`, …) — extracted from the inline overrides in §3 | only if unique to one unit |

The **PROJECTILE-base** roster in the table above is the raw material for the per-game
Shared layer: those templates already hold the game art; the work is to rename/relocate
them to the `^Projectile_*` / `^Effect_*` grammar and move the assets into the game's
`Shared/` pack so the dynamic loader pulls them only when a faction of that game is active.

---

### §5 — Maintainer decisions required

1. **`^TSDefaultMissile` collapse** — ✅ RESOLVED (2026-08-03): **per-user by unit tier**
   under the Tier↔WeaponClass law (§1). Applied unit-by-unit in Phase 3.
2. **Per-game effect extraction** — approve extracting inline game explosions (§3) into
   `^Effect_<family>_<game>` templates in each game's `Shared/` folder. Naming: confirm
   the game-suffix casing (`^Effect_Bullet_RA2` matching the existing `^RA2…` base prefix
   vs `_Ra2`) and whether the game variant carries a level (`^Effect_Bullet_Light_RA2`).
   *(Explanation in progress with the maintainer.)*
3. **PROJECTILE-base relocation order** — ✅ RESOLVED (2026-08-03): **RA2 first** (largest,
   most inlined).

None of these block the remaining Phase-2 family retrofits (Flame/Chem/Explosions/Melee/
Arrow/Magic/Nuclear): those convert single-inherit blocks and correctly leave every base
in this doc as Phase B until the decisions above are made.
