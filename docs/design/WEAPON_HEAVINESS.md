# Weapon heaviness — the continuous scale and the research behind it

Two documents until 2026-08-23: the research that established heaviness is a CONTINUUM rather
than three tiers, and the design that turned it into a usable scale. They share every premise,
so they are one file.

Related law: `DESIGN.md` §12.0 (the profile shape law) and §12.0a (platform, not just family).

---

## The research

_Merged 2026-08-23 from `docs/design/HEAVINESS_RESEARCH.md`, unedited below this line._

> # ⛔⛔ CORRECTION 2026-08-22 — THE VERSUS NUMBERS BELOW ARE WRONG
>
> **Every Versus figure in this document was measured with a broken parser** and must not be
> acted on. The parser never CLOSED the `Versus:` block, so the `PercentageVersus:` rows that the
> AreaDamage fold added inside the same warhead node silently OVERWROTE the real profile. What
> was measured throughout was the percentage twin's 1..16 RANK ladder, not the armor profile.
>
> ```
> Warhead@Bullet_Light: AreaDamage
>     Versus:            None: 200 ... Spaceship 53, Superheavy 48   <- the REAL profile
>     PercentageVersus:  None: 16  ... Spaceship  2, Superheavy  1   <- what was read
> ```
>
> **Re-measured correctly (close the block when indentation returns to its level):**
>
> | claim in this document | truth |
> |---|---|
> | 0 of 125 profiles obey the MEAN-100 law | **123 of 125 obey it** (the 2 are `Nuclear_Super` and `Sniper_Light`, both `HAND_TUNED`) |
> | every family violates the 2x-8x spread band | **37 of 42 are IN the band**; median spread **4.17x** against a target of 4x |
> | spreads run 12x-100x | min 1.00x, p25 2.61x, median 4.17x, p75 4.97x, max 10.00x |
> | the level applies an additive `+4 / +5` offset | that was the twin's rank ladder stepping 1/5/10 |
> | 26 of 42 families invert under a tier-only bell | unverified — measured on the wrong data |
> | a Heavy weapon self-prices at ~2x a Light one | unverified — measured on the wrong data |
>
> **The real outliers are three families:** `CannonAP` 1.81x and `Cryo` 1.97x (too flat), `Sniper`
> 10.00x (too sharp). `Magic` and `Sonic` at 1.00x are FLAT BY DESIGN — `mean_normalise`
> special-cases them ("ignores armor").
>
> **And the substance of this document is already LAW and already LIVE.** See `DESIGN.md`
> **§12.0h THE MEAN-100 LAW** (2026-08-16, binding: *"all warheads average all versus values at
> 100"*, so `K` is SHAPE-ONLY and `Damage` is the sole magnitude knob) and **§12.0d THE CLASS
> TILT** (each LEVEL tilts toward one end of every armor ladder — Light toward the lightest rung,
> Heavy toward the heaviest). §12.0d is the bell curve, and it already solves the inversion
> problem properly: *"the tilt MUST NEVER reorder a ladder ... it can never invert"* — it is
> applied to the VALUES and each armor is then given back the RANK it held. Both are implemented
> in `gen_weapon_template.py` (`class_tilt` line 927, `mean_normalise` line 980) and live.
>
> **What is genuinely still open** is only this: make the tilt CONTINUOUS (driven by `h` from
> `tier_chain`) instead of four discrete levels, and collapse the level templates to one per
> family plus a per-weapon `h`.

**Status:** research findings. No yaml, no C#, no balance numbers changed.
**Date:** 2026-08-22
**Absorbed 2026-08-23:** `CONTINUOUS_WEAPON_HEAVINESS.md` is merged into this file (see the end).

Answers four maintainer questions: does heaviness feed the PRICE, does a late-game unit keep its
anti-light identity, what deterministic rule governs SECONDARY weapons, and what must not be
broken when families are collapsed.

---

### 1. Does `h` raise the unit's price? — ⛔ **REVERSED 2026-08-23: NO, and deliberately so**

> **Maintainer ruling, 2026-08-23** (the choice §9.3 asked for): *heaviness is free; price via
> Damage.* Renormalising to a constant weighted mean makes `K` invariant in `h`, so heaviness has
> **no** price effect. That is the intended separation:
>
>     Versus  = WHAT the weapon is good against   (RPS shape; heaviness lives here)
>     Damage  = HOW strong the weapon is          (magnitude; the balance pipeline lives here)
>
> A late-game weapon costs more because its `Damage` is higher, not because its profile is shaped
> differently. **The section below is the superseded analysis** — it is correct about the additive
> model it was measuring, and that model is no longer the design. Kept for provenance.


`tools/balance/weapon_efficiency.py` line 8:

```
K = SUM over warheads   share_w x versus_w x ( reliability_w + secondary_w )

  versus_w = Versus averaged over armors, WEIGHTED by how common each armor
             actually is (target_model.armor_weights)
```

and `extract_stats.py`:

```
effective_per_shot = damage_total x k_flat_context
                     + pct_absolute_context + folded_rounding_context
effective_dps = effective_per_shot x burst / eff_reload
```

Price is driven by effective DPS. So **raising Versus raises `versus_w` → raises K → raises
`effective_dps` → raises the price**, with no additional plumbing.

Measured, with the additive offset and real armor weights:

| family | h=0 | h=1 | h=2 | price pressure at h=2 |
|---|--:|--:|--:|--:|
| Laser | 0.075 | 0.115 | 0.165 | **+120%** |
| MissileAP | 0.090 | 0.130 | 0.180 | **+100%** |
| Flame | 0.099 | 0.139 | 0.189 | **+91%** |

A Heavy weapon costs roughly **twice** a Light one, purely through measured effectiveness.

#### 1.1 It cannot double-charge — the old knob was already removed

`formula.py:82`:

> **`weapon_class` was REMOVED here on 2026-08-11 (W4).** It was a tier weight standing in for
> "how good is this weapon type", back when nothing measured that. The K coefficient now measures
> it directly from the weapon's own geometry, so keeping the tier weight as well would charge a
> weapon twice for the same property.

Continuous heaviness works **through** K, exactly where the discrete tier weight was deliberately
taken out. The two designs are already compatible; nothing needs adding to the price formula.

---

### 2. ⛔ Can a Tier-4 unit stay anti-light? — **NOT under the additive offset**

**This corrects an earlier claim that "family character survives".** It survives in ORDERING but
not in MAGNITUDE. A uniform additive offset raises every armor entry equally, so the RATIO between
a family's best and worst target collapses as `h` rises:

| family | h=0 | h=1 | h=2 |
|---|--:|--:|--:|
| MissileAP (best/worst) | **16.00x** | 4.00x | **2.50x** |
| Laser | 5.33x | 2.86x | 2.08x |
| Flame | 3.20x | 2.22x | 1.79x |
| CannonHE | 1.75x | 1.50x | 1.35x |

`MissileAP` goes from savagely anti-heavy to nearly generic.

⚠ **This is not caused by the continuous model — today's discrete ladder is already additive**, so
current Heavy weapons are ALREADY less differentiated than current Light ones. The continuous
model only makes an existing defect visible and smooth.

#### 2.1 The fix: multiplicative, not additive

```
ADDITIVE        Versus(armor, h) = base(armor) + offset(h)     ratios COLLAPSE
MULTIPLICATIVE  Versus(armor, h) = base(armor) x (1 + 0.5h)    ratios PRESERVED EXACTLY
```

Multiplicative keeps a Tier-4 Venom exactly as anti-light as a Tier-1 one, just stronger overall.
It also produces the same ~2x K at h=2 (K is linear in Versus), so **the pricing behaviour of
§1 is unchanged**.

| | additive | multiplicative |
|---|---|---|
| reproduces today's templates | **yes, exactly** | no |
| preserves RPS at high tier | **no** | **yes** |
| effect on price | 2x at h=2 | 2x at h=2 |
| is it a balance change | none | **yes — every Medium/Heavy weapon moves** |

⚠ **This is the decision that matters.** Additive is a pure refactor; multiplicative is the
correct design but restates every non-Light weapon and must go through the balance pipeline.

---

### 3. Secondary weapons — a deterministic rule

#### 3.1 The population

| | actors |
|---|--:|
| with 2+ classifiable weapons | 320 |
| ...all weapons at the SAME level (a unit-derived `h` just works) | **270 (84%)** |
| ...MIXED levels, needing a per-weapon rule | **50 (16%)** |

Mixed combinations: `Medium+Heavy` 22, `Light+Medium` 13, `Light+Medium+Heavy` 7, `Heavy+Super` 5,
`Light+Heavy` 3.

The mixed cases are **not random — they track the armament's ROLE**, which is already encoded in
the armament key:

```
td_gdi_minigunner     PRIMARY=Bullet_Light,  Upgrade=Bullet_Medium
td_gdi_humvee         Armament=Bullet_Light, Upgrade=Bullet_Medium
A10Carrier            GUNS=Bullet_Medium,    AA=MissileAP_Heavy
ra1_allies_destroyer  Armament=MissileAP_Heavy, DC1/DC2=Demolition_Light
```

#### 3.2 The shared-weapon problem

522 of 1524 weapons are carried by 2+ units. Most are tier-consistent (p50 spread **0.00**,
p75 **0.12**) — but **96 weapons span >= 1.0 in `h`** across their carriers:

```
8Inch          h 0.00 (ra1_allies_cruiser)   ->  2.00 (ts_nod_cruiser)      15 carriers
Grenade        h 0.00 (td_gdi_grenadier)     ->  2.00 (ra2_allies_ifv_chrono) 9 carriers
BigFlamer      h 0.00 (ra2_allies_ifv_mg)    ->  2.00 (ra2_allies_ifv_chrono) 9 carriers
```

A warhead field is per-WEAPON, so one weapon can only have one `h`. Per-carrier heaviness is not
expressible without cloning the weapon per tier — which is the template explosion again.

#### 3.3 Proposed rule — deterministic, no manual tagging for 96% of cases

```
h(weapon) = clamp( 5 x (1 - f(C_min)), 0, 2 )

  C_min = the SMALLEST prerequisite chain cost among all units that field this weapon
          as a PRIMARY armament; if it is never primary, over all carriers.

  An explicit `Heaviness:` on the weapon overrides, and always wins.
```

**Why minimum, and why it is principled rather than arbitrary:** a weapon's heaviness is *the
earliest tech at which it can be fielded*. If `8Inch` is available on a T1 cruiser, it is a T1 gun,
and the T3 cruiser is simply fielding a T1 gun — it should pay T1 price for it and be differentiated
by hull, armor and its OTHER weapons. This also solves the coaxial-MG case for free: a machine gun
shared with a T1 scout is never primary on the tank, so it takes the low `h` and stays a genuine
anti-light counter, exactly as intended.

**Determinism:** the rule is a pure function of (roster, prerequisite graph, explicit overrides).
It contains no averaging, no sampling and no dependence on evaluation order, so repeated pipeline
runs cannot drift.

**Cost:** the ~50 mixed actors and 96 wide-span weapons should be reviewed once; anything the rule
gets wrong gets an explicit `Heaviness:` and is then frozen and auditable.

---

### 4. Family identity — what must NOT be lost when collapsing

The maintainer flagged that Laser is anti-heavy and the anti-light beam should be Prism, with
Inferno = Prism x Flame. **The data confirms all three.** Profiles at the Heavy rung:

| family | None | Light | Medium | Heavy | Superheavy | character |
|---|--:|--:|--:|--:|--:|---|
| Laser | 12 | 13 | 17 | 21 | 25 | **ANTI-HEAVY** |
| Railgun | 17 | 22 | 23 | 24 | 25 | ANTI-HEAVY |
| Tesla | 18 | 19 | 21 | 23 | 25 | ANTI-HEAVY |
| **Prism** | **24** | 22 | 19 | 16 | **14** | **ANTI-INFANTRY** |
| **Inferno** | **24** | 19 | 17 | 15 | **14** | ANTI-INFANTRY |
| Flame | 25 | 17 | 16 | 15 | 14 | ANTI-INFANTRY |

`Inferno` sits **between** `Prism` (24, 22, 19, 16, 14) and `Flame` (25, 17, 16, 15, 14) at every
armor class — numerically consistent with `Inferno = Prism x Flame`. The taxonomy is already right
and must be preserved through any collapse.

#### 4.1 ⚠ Two RPS-dead families found while checking

| family | None | Light | Medium | Heavy | Superheavy |
|---|--:|--:|--:|--:|--:|
| **Sonic** | 10 | 10 | 10 | 10 | 10 |
| **Magic** | 50 | 50 | 50 | 50 | 50 |

Both are **completely flat** — no rock-paper-scissors at all, at any level. Multiplicative scaling
cannot help them (`flat x k` is still flat). They need real profiles authored, and that is a
separate design task from heaviness.

---

### 5. What this changes in the build order

`CONTINUOUS_WEAPON_HEAVINESS.md` §7 stands, with two insertions:

1. Fix the 9 broken level ladders (unchanged blocker).
2. **NEW — rule additive vs multiplicative (§2).** This decides whether the rollout is a refactor
   or a balance restat, so it must be settled before any C# is written.
3. **NEW — author profiles for `Sonic` and `Magic` (§4.1).**
4. Add `Heaviness` to `AreaDamageWarhead`, inert at 0.
5. Verify the transform reproduces all 126 existing templates.
6. Collapse to one template per family; set `h` by the §3.3 rule.
7. Re-point the 102 mix weapons; lower the ratchets.

---

### 6. Provenance

Every figure measured on the resolved ruleset (`tools/audit/miniyaml.Ruleset`) or read from
`tools/balance/weapon_efficiency.py` / `formula.py` / `docs/balance/derived/*.json`, on 2026-08-22.

⚠ The "family character survives" claim in the first heaviness discussion was WRONG (§2) — it
checked ordering and not magnitude. Confirm differentiation with a best/worst RATIO, never by
eyeballing whether the biggest number is still biggest.

---

## The continuous scale

_Merged 2026-08-23 from `docs/design/CONTINUOUS_WEAPON_HEAVINESS.md`, unedited below this line._

> # ⛔⛔ CORRECTION 2026-08-22 — THE VERSUS NUMBERS BELOW ARE WRONG
>
> **Every Versus figure in this document was measured with a broken parser** and must not be
> acted on. The parser never CLOSED the `Versus:` block, so the `PercentageVersus:` rows that the
> AreaDamage fold added inside the same warhead node silently OVERWROTE the real profile. What
> was measured throughout was the percentage twin's 1..16 RANK ladder, not the armor profile.
>
> ```
> Warhead@Bullet_Light: AreaDamage
>     Versus:            None: 200 ... Spaceship 53, Superheavy 48   <- the REAL profile
>     PercentageVersus:  None: 16  ... Spaceship  2, Superheavy  1   <- what was read
> ```
>
> **Re-measured correctly (close the block when indentation returns to its level):**
>
> | claim in this document | truth |
> |---|---|
> | 0 of 125 profiles obey the MEAN-100 law | **123 of 125 obey it** (the 2 are `Nuclear_Super` and `Sniper_Light`, both `HAND_TUNED`) |
> | every family violates the 2x-8x spread band | **37 of 42 are IN the band**; median spread **4.17x** against a target of 4x |
> | spreads run 12x-100x | min 1.00x, p25 2.61x, median 4.17x, p75 4.97x, max 10.00x |
> | the level applies an additive `+4 / +5` offset | that was the twin's rank ladder stepping 1/5/10 |
> | 26 of 42 families invert under a tier-only bell | unverified — measured on the wrong data |
> | a Heavy weapon self-prices at ~2x a Light one | unverified — measured on the wrong data |
>
> **The real outliers are three families:** `CannonAP` 1.81x and `Cryo` 1.97x (too flat), `Sniper`
> 10.00x (too sharp). `Magic` and `Sonic` at 1.00x are FLAT BY DESIGN — `mean_normalise`
> special-cases them ("ignores armor").
>
> **And the substance of this document is already LAW and already LIVE.** See `DESIGN.md`
> **§12.0h THE MEAN-100 LAW** (2026-08-16, binding: *"all warheads average all versus values at
> 100"*, so `K` is SHAPE-ONLY and `Damage` is the sole magnitude knob) and **§12.0d THE CLASS
> TILT** (each LEVEL tilts toward one end of every armor ladder — Light toward the lightest rung,
> Heavy toward the heaviest). §12.0d is the bell curve, and it already solves the inversion
> problem properly: *"the tilt MUST NEVER reorder a ladder ... it can never invert"* — it is
> applied to the VALUES and each armor is then given back the RANK it held. Both are implemented
> in `gen_weapon_template.py` (`class_tilt` line 927, `mean_normalise` line 980) and live.
>
> **What is genuinely still open** is only this: make the tilt CONTINUOUS (driven by `h` from
> `tier_chain`) instead of four discrete levels, and collapse the level templates to one per
> family plus a per-weapon `h`.

**Status:** design proposal, measured but not implemented. No yaml or C# changed yet.
**⭐ READ §9 FIRST — the BELL CURVE model supersedes the additive offset of §2.**
**Date:** 2026-08-22
**Supersedes the plan to generate intermediate level templates** (`LightMedium`, `MediumHeavy`, …).

---

### 1. The problem this solves

Two standing laws collide:

- **The 3-way split** (`WEAPON_3WAY_SPLIT.md`): a weapon is ONE warhead + ONE projectile + ONE effect.
- **The Tier↔WeaponClass law** (`weapon_classes.yaml` header):
  a unit sitting *between* tech tiers carries **two adjacent-level warheads** —
  `Bullet_Light + Bullet_Medium`.

A between-tier unit cannot satisfy both. 102 weapons are in that state today.

⚠ **The mix is not merely inelegant — it does not deliver what it promises.** Two warheads'
damage is **added**, not interpolated. Measured against the median single-warhead damage of the
same family:

| | weapons |
|---|--:|
| mix lands **between** its two levels (as intended) | 55 |
| mix **exceeds the higher level outright** | 33 |
| below the lower level | 3 |
| no comparable baseline | 11 |

Totals range **0.27× to 6.00×** the higher level. A third of "between-tier" units are simply
*stronger than the tier above them* — the opposite of the intent.

#### 1.1 Why generating intermediate templates is the wrong fix

The obvious repair — generate `^Warhead_Bullet_LightMedium` — multiplies badly:

| | today | + intermediate rungs | + planned crossover families |
|---|--:|--:|--:|
| families | 40 | 40 | ~100 |
| rungs each | 3–4 | 6 | 6 |
| **templates** | **126** | **240** | **~600** |

Every new crossover family (`MissileTesla`, `MissileHE`, `BulletThermobaric`, …) multiplies by
the rung count. ~600 near-identical hand-maintainable Versus tables is not a system.

---

### 2. The key measurement: a "level" is already a pure transform

The level does **not** encode an independent armor profile. It applies a **uniform additive
offset** to the Versus table, and a **fixed ratio** to Spread. Measured across all 40
`^Warhead_<Family>_<Level>` templates in `mods/cameo/weapons/weapons.yaml`.

#### 2.1 Versus — additive offset

```
Bullet          Light  Medium  Heavy      step L->M   step M->H
  Superheavy        1       5     10          +4          +5
  Heavy             3       7     12          +4          +5
  Concrete          4       8     13          +4          +5
  None             16      20     25          +4          +5
  Shield           17      25     35          +8         +10     (2x)
  ARMOR            70      70     70           0           0     (plating: never shifts)
  BLAST            69      69     69           0           0
  COMPOSITE        43      43     43           0           0
```

Generalised:

```
Versus(armor, h) = base(armor) + offset(h)

  offset:   0 at Light,  +4 at Medium,  +9 at Heavy   (cumulative)
  plating (ARMOR/BLAST/COMPOSITE/HAZMAT/REFLECTOR):  always 0
  Shield:   2x the offset
```

**Conformance: 39 of 40 families.** `CannonChem` and `MissileChem` follow the pattern exactly
plus ONE extra family-specific entry (`+13`/`+17`). Only **`Storm`** is genuinely irregular —
every entry carries its own delta — and it is already a hand-tuned special case in the generator.

#### 2.2 Spread — fixed ratio

Across the 35 families with three measurable rungs, the ratio
`(Spread_Medium / Spread_Light, Spread_Heavy / Spread_Light)` is:

| ratio | families |
|---|--:|
| (1.50, 2.00) | 22 |
| (1.51, 2.00) | 4 |
| (1.49, 1.98) / (1.51, 2.02) / (1.50, 2.01) / … | 9 (rounding) |

So `Spread(h) = Spread_base × (1 + 0.5·h)` with `h = 0, 1, 2` for Light/Medium/Heavy. Clean and
continuous.

#### 2.3 Damage — currently carries no level signal at all

Every one of the 40 templates declares the same `Damage: 2000`. That is a **convention**, not a
bug: the template holds the SHAPE, the weapon holds the MAGNITUDE via the WeaponClass scalar.
See §5 — the effective ladder is broken and must be fixed before any of this lands.

---

### 3. The proposal

**One warhead template per family. One continuous `Heaviness` scalar per weapon.**

```
templates:  40 today, ~100 once the crossover families exist — and it NEVER multiplies
```

`h` is continuous, so any blend is expressible — 1/3 Light + 2/3 Medium, or anything else — which
is what the level ladder was reaching for and could never do.

#### 3.1 Where h comes from — it is already computed

`tools/balance/tier_chain.py` already exists and is validated:

- `TierChain.chain_cost(actor)` → `C`, total cost of the unique building prerequisite chain.
- `tier_multiplier(C) = 1 / (1 + (C - B) / S)`, `B = 9500` (T1 median chain), `S = 8250`
  (T4 median − B), clamped `[0, 1]`.
- `extract_stats.py` **already stores `tier_chain_cost` and `tier_multiplier` for every buildable
  actor** in `docs/balance/derived/*.json`, and `effective_tier()` preserves manual
  `design.tech_tier` overrides.

Verified examples from `tier_chain_validation.md`: `td_nod_lasertrooper` → C = $27,000,
f = 0.3204; `wc2_orcs_deathknight` → C = $15,000.

⚠ **Direction:** `f(C)` *falls* as tech deepens (it is a cost discount). Heaviness must *rise*.
So `h` is derived from `1 − f(C)`, not `f(C)`.

Fitting the three known rungs (`f ≈ 1.00 / 0.80 / 0.60` → `offset 0 / 4 / 9`):

```
offset(C) ≈ 22 × (1 − f(C))        -> 0.0, 4.4, 8.8      (needs proper calibration, §6)
```

This makes weapon heaviness and tier pricing read off the *same* number, so they cannot drift.

#### 3.2 Where h is applied — C#, not generated yaml

Generating the resolved table per weapon would write 2325 × 24 Versus entries into yaml and
defeat the entire purpose. Instead `AreaDamageWarhead` gains a `Heaviness` int applied at Versus
lookup and Spread computation.

**Precedent:** the AreaDamage fold already added `PercentageScale` as exactly this kind of
per-weapon integer interpreted by Cameo-owned C#. No engine change is needed — `AreaDamageWarhead`
lives in `OpenRA.Mods.Cameo`.

#### 3.3 What this buys

- **One warhead per weapon** → the 3-way split holds with no permanent audit carve-out.
- The tier law's intent is preserved and, for the first time, actually delivered.
- The **33 overshooting weapons are fixed by construction** — interpolation cannot exceed its
  endpoints, whereas addition always could.
- Rock-paper-scissors across the tech tree becomes continuous rather than snapping between three
  buckets: a T1 weapon's small offset meets T1 armor low on the same ladder.
- ~600 future templates collapse to ~100.

---

### 4. What must NOT be lost

- `Storm` is genuinely irregular and needs an explicit exception or a hand-authored table.
- `CannonChem` / `MissileChem` need their one extra entry preserved.
- The **plating** entries (ARMOR, BLAST, COMPOSITE, HAZMAT, REFLECTOR) must keep offset 0 — they
  are layer-selected, not level-scaled.
- `Shield` keeps its 2× offset.
- Per-weapon `Versus` overrides remain **forbidden** outside `^Warhead_*` templates (standing rule).

---

### 5. ~~⛔ BLOCKER — the ladder must be fixed first~~ — ✅ RETIRED 2026-08-23, NOT a blocker

⛔ **This section is superseded and kept only for provenance.** The maintainer ruled on 2026-08-23
that the level is a TILT (§12.0d), not a damage ladder, and that no law ever required a family's
effective damage to rise with its level. `audit_level_ladder.py` is deleted; the replacement is
`audit_heaviness_bell.py`, which checks what the bell actually needs. See §9.6, and DESIGN §12.0i.

The decisive fact this section missed: **145 of the `^Warhead_*` templates carry only a placeholder
`Damage: 2000`** — the template holds the SHAPE, the weapon holds the MAGNITUDE — so collapsing the
levels never touches a damage number and the ladder cannot block the collapse. The measurement
below is real; the conclusion drawn from it was not.

`audit_level_ladder.py` measured the EFFECTIVE ladder — median damage of the real weapons on each
rung:

| verdict | families |
|---|---|
| rise correctly | CannonHE, Flame, Laser, MissileChem, MissileHE |
| **FLAT** | Bullet, Demolition, MissileFire |
| **INVERTED** | Chemical, Flak, Inferno, MissileAP, Tesla, Thermobaric |

```
MissileAP   Light 20000 (n=23) -> Medium 12000 (n=26) -> Heavy 11000 (n=32)   falls throughout
Tesla       Heavy 12000 (n=47) -> Super  6500 (n=20)                          Super is half
Flak        Light 32000 (n=2)  -> Medium  8000 (n=15)                         quarter
```

Interpolating between two **equal** endpoints yields nothing — every intermediate rung would be
identical to its neighbours. Interpolating between two **inverted** endpoints yields nonsense — a
T1.5 unit would land *above* the T2 unit, faithfully and invisibly encoding the bug.

⚠ Restating a rung is a **balance change**: it goes through the pipeline (`extract_stats` →
ledger → `apply_balance --confirm`) and `--confirm` needs a maintainer order. Never hand-edit.

---

### 6. Open questions for the maintainer

1. **Super is inconsistent.** `Tesla` Heavy→Super is `+5` (the same step as Medium→Heavy) but
   `Magic` Heavy→Super is `+15`. Which is right? The answer sets the top of the `h` scale.
2. **Calibration of `offset(h)`.** `22 × (1 − f(C))` fits the three known rungs to ±0.4, but it is
   a back-of-envelope fit, not a derivation.
3. **Should Spread scale from the same `h`?** The measured `1 : 1.5 : 2` ramp says yes, but that
   couples blast radius to tech tier — a deliberate design choice, not an obvious one.
4. **Is `HeavySuper` needed?** `Tesla_Heavy + Tesla_Super` exists as a mix today. Under the
   continuous model the question dissolves, but the affected weapon still needs a value.
5. **Does `h` come from the unit, or stay per-weapon?** A unit with two weapons might want
   different heaviness on each (a T3 tank's coaxial MG is not a T3 weapon).

---

### 7. Build order

1. **Fix the 9 broken ladders** — balance pipeline, maintainer `--confirm`. Blocks everything.
2. Settle §6.1 and §6.2 (Super, calibration).
3. **Add `Heaviness` to `AreaDamageWarhead`**, inert by default (`0` = today's behaviour), rebuild,
   boot-gate. Ship the mechanism before using it — same as the AreaDamage fold.
4. Verify the transform reproduces all 126 existing templates exactly, family by family.
5. Collapse the level templates to one per family; set per-weapon `Heaviness` from
   `tier_multiplier`.
6. Re-point the 102 mix weapons; lower the `three_way_split` and `tier_weapon_class` ratchets.

---

### 8. Provenance

Every number here was measured on the resolved ruleset via `tools/audit/miniyaml.Ruleset`, not
read from a summary. Guards added while investigating:

- `tools/audit/audit_tier_weapon_class.py` — TYPES × LEVELS budget, ratchet 218.
- ~~`tools/audit/audit_level_ladder.py` — effective ladder monotonicity, ratchet 9~~ —
  RETIRED 2026-08-23, replaced by `tools/audit/audit_heaviness_bell.py` (0 inversions,
  0 mean drift, 2 flat families at ratchet 2).

⚠ Three earlier versions of these audits measured the WRONG SURFACE — source instead of resolved,
override instead of addition, template placeholder instead of effective value — and each produced
a confident, wrong number (393 violations; 40 broken ladders; 79 weapons queued for a "repair"
that would have erased their tier identity). Assert against the resolved node, always.

---

### 9. ⭐ SUPERSEDING MODEL — the BELL CURVE (maintainer, 2026-08-22)

**This replaces the additive offset of §2.** Maintainer proposal: instead of raising every Versus
entry, place the armor classes on a light->heavy axis and multiply the profile by a bell curve
whose peak moves with heaviness, then RENORMALISE so the profile keeps a constant mean.

    curve(x) = LO + (1 - LO) * exp( -(x - mu)^2 / (2*sigma^2) )
    Versus(armor, h) = base(armor) * curve( x(armor), mu(h) )   then renormalised

Heaviness then **redistributes** what a weapon is good against instead of inflating everything.
That is strictly better than the additive model, which flattened rock-paper-scissors as tier rose
(§2): MissileAP fell from 16.0x to 2.5x differentiation.

#### 9.1 Verified: the mean really is invariant

Renormalising to a constant **weighted** mean holds exactly. Measured across CannonAP, MissileAP,
Laser, Tesla, Flame, Prism, CannonHE, Sonic, Magic: weighted mean identical at h=0, 1 and 2
(`1.00x` at every step).

#### 9.2 ⛔ CRITICAL FLAW IN THE LITERAL PROPOSAL — the peak must be anchored to the FAMILY

If `mu` is a function of tier ALONE (h=0 peaks at the lightest armor, h=2 at the heaviest), then a
low-tier armor-piercing weapon peaks at LIGHT armor. Measured on the real profiles:

    CannonAP  at h=0 ->  best target = Light   (Light 16.1 vs Superheavy 10.9)
    MissileAP at h=0 ->  best target = Light   (Light 16.4 vs Superheavy 11.1)

That is precisely what the maintainer said must NOT happen: *"even the lightest CannonAP weapon is
still much better against heavy than light."*

**Cause:** the bell's swing (2x at LO=0.5) is larger than most families' own gradient across the
ladder. MissileAP runs Light 13 -> Superheavy 16, a gradient of only **1.23x**; a 2x bell trivially
overpowers it. Families whose own gradient EXCEEDS the swing survive — `Laser` (5.33x), `Flame`
(3.20x), `Prism` (3.00x), `Inferno` (3.00x) all keep their orientation.

**Measured inversion counts, 42 families with a full ladder:**

| model | swing | inverts |
|---|--:|--:|
| tier-only peak (as proposed) | 2.00x | **26 of 42** |
| tier-only peak | 1.25x | 10 of 42 |
| **family-anchored, shift +-0.25** | 2.00x | 9 of 42 |
| **family-anchored, shift +-0.25** | **1.25x** | **6 of 42** |
| family-anchored, shift +-0.30 | 1.18x | 7 of 42 |

**FIX:** anchor the peak to the family's own centre of mass and let heaviness only SHIFT it:

    mu(family, h) = centre_of_mass(base_profile) + SHIFT * (h - 1)     SHIFT ~ 0.25
    LO = 0.80                                                          swing ~ 1.25x

The family decides WHERE it is strong; heaviness nudges it heavier or lighter. This is exactly the
maintainer's stated intent: *"a heavy AP weapon is even stronger against heavy and worse against
light"* while a light one stays anti-heavy.

⛔ **SUPERSEDED 2026-08-24 — the constants in that table are RETIRED. `SHIFT` no longer exists,
`LO` is 0.667 and the peak is `mu = (h + centre_of_mass) / 2`.** See DESIGN §12.0i, which is
binding, and §9.5b below. Two things were wrong with the measurement above: the whole "inverts"
column was taken **before §12.0d's rank restore was implemented in the audit** — with the restore
in place a pure tier-anchored peak inverts **nothing**, so the row that rejects it (26 of 42) does
not stand — and `LO = 0.80` was calibrated against a peak that moved only 0.25, which under the
ruled blend leaves the continuous model much gentler than the discrete tilt already shipping.

The maintainer's restatement below still holds in full — it is the DESIGN intent, and the ruled
model implements it:

> *"the weapon family should be the most important and the heaviness level should only nudge it a
> little … a low level CannonAP will lean stronger towards lighter armor types but still deal more
> damage to heavy armor, the difference just is not too much, while the heavy CannonAP will deal
> much more to heavy … Flame weapons will be the opposite: a light flame weapon deals extremely
> high damage to light and very low to heavy, a heavy flame weapon slightly less to light and a
> little more to heavy — but still more to light, because that's their identity."*

Those two examples are the two halves of §12.0d's sentence: the shift **sharpens** where it agrees
with the family's centre of mass (CannonAP, already heavy-ward) and **flattens** where it disagrees
(Flame, light-ward), and the rank restore means it can never flip Flame into an anti-heavy weapon.

The residual 6 inversions are the FLAT families (`Sonic` 1.00x, `Magic` 1.00x, `Cryo` 1.25x,
`Railgun` 1.47x, `Waveforce` 1.44x, `Storm` 1.49x) which have almost no gradient to preserve. They
are fixed by §9.4, not by tuning the bell.

⭐ **RE-MEASURED 2026-08-23 at the ruled constants — the result is better than this predicted**
(`python tools/audit/audit_heaviness_bell.py`, which simulates the bell before it exists so §9.6
step 6 has its test waiting):

| | measured |
|---|--:|
| families with a full profile | **48** |
| flat, no gradient for the bell to preserve | **2** — only `Sonic` and `Magic` |
| weighted-mean drift at h = 0, 1, 2 | **0** (renormalisation holds exactly, confirming §9.1) |
| ladder directions the bell would flip | **2** |

`Cryo`, `Railgun`, `Waveforce` and `Storm` have been given real gradients since this was written —
`fit_band_floor` in `gen_weapon_template.py`, 2026-08-22 — so the "residual 6" is down to 2.

⛔ **RETRACTED 2026-08-24 — there are no remaining flips, and the "gap in §9.4" does not exist.**
An earlier revision of this section recorded `BulletThermobaric` BLD and `CannonFire` AIR as
permanent exceptions caused by near-flat 1.13x sub-ladders that no 1.25x swing could preserve, and
called for authoring new gradients under hard rule 4. That was an artifact of the audit **skipping
§12.0d's rank restore**.

§12.0d applies the tilt to the VALUES and then gives each armor back the RANK it held. Restore that
step and the count is **zero** — not just for those two endpoints but for the full internal ordering
of every ladder. Measured across 48 families:

| | ladder orderings changed |
|---|--:|
| bell WITHOUT the rank restore | **127** (60 family/ladder pairs) |
| bell WITH the rank restore | **0** |

So the spread band needs no widening, no warhead needs authoring for this, and the endpoint-only
check that produced the two "known inversions" was also blind to 125 further reorderings.

#### 9.3 ⚠ TRADE-OFF — a constant mean means heaviness NO LONGER RAISES THE PRICE

`HEAVINESS_RESEARCH.md` §1 established that K = SUM(share x versus x ...) reads the weighted mean
Versus, so under the ADDITIVE model a Heavy weapon priced ~2x a Light one automatically.

**Renormalising to a constant mean removes that entirely.** K becomes invariant in h, so heaviness
has NO price effect at all.

That is arguably correct and cleaner — it separates the two concerns:

    Versus  = WHAT the weapon is good against   (RPS shape; heaviness lives here)
    Damage  = HOW strong the weapon is          (magnitude; the balance pipeline lives here)

but it is a real reversal of the earlier answer and the maintainer must choose knowingly. If
late-game weapons should still cost more *because they are late-game*, that must now come from
Damage or from the tier term in pricing, not from Versus.

✅ **RULED 2026-08-23 — heaviness is free of price; magnitude comes from `Damage`.** §1 above is
struck accordingly. No tier term is added to the pricing formula: a heavier weapon is priced
through its `Damage`, exactly like every other magnitude change, and `K` stays invariant in `h`.

#### 9.4 The spread law — 2x to 8x, target 4x

Maintainer ruling: the ratio between a family's highest and lowest Versus must sit in **[2x, 8x]**
with a target of **4x**. Measured today, over the full armor table, **every family violates it**:

| family | spread | |
|---|--:|---|
| Chemical, Flame, Inferno, Tesla | 100.00x | TOO WIDE |
| Laser | 75.00x | TOO WIDE |
| BulletFire, CannonFire | 50.00x | TOO WIDE |
| Bullet, CannonAP, CannonHE, MissileAP, Prism, ... | 17.00x | TOO WIDE |
| MissileTesla | 12.50x | TOO WIDE |

and on the vehicle ladder alone several are far too NARROW (`Sonic` 1.00x, `Magic` 1.00x, `Cryo`
1.25x, `Railgun` 1.47x). Bringing every family into the band is a prerequisite for the bell,
because a family with no gradient cannot survive any modulation.

#### 9.5 ✅ RULED 2026-08-23, REVISED 2026-08-24 — the axis is per-ladder rung position

⛔ **The three-bucket answer below is SUPERSEDED.** It ties armors that are not equally heavy, and
tied coordinates move together under the bell, so heaviness could not tell them apart at all.

> Maintainer, 2026-08-24: *"both bomber and helicopter armor type are considered medium but from the
> two helicopter is the heavier one. Helicopter is actually in between medium and heavy while bomber
> is between light and medium. Same with the scout to light and the heavy to superheavy."*

**Ruled: `x(armor)` is the armor's rung index inside its OWN ladder, normalised to 0..2.** The
ordering is already canonical in `gen_weapon_template.LADDERS` (lightest → heaviest), so nothing new
is invented:

| ladder | coordinates |
|---|---|
| VEH | `Scout` 0.0 · `Light` 0.5 · `Medium` 1.0 · `Heavy` 1.5 · `Superheavy` 2.0 |
| AIR | `Fighter` 0.0 · `Bomber` 0.67 · `Helicopter` 1.33 · `Spaceship` 2.0 |
| INF | `None` 0.0 · `Flak` 1.0 · `Plate` 2.0 |
| BLD | `Wood` 0.0 · `Steel` 1.0 · `Concrete` 2.0 |

⛔ **SUPERSEDED 2026-08-24 by §9.5b — this per-ladder form gave four armors x=0.0, three x=1.0 and
four x=2.0.** The maintainer's requirement is one unique value per armor: *"I want a continuous
value for all of them and all of them should have their own unique value and not two sharing the
same."* Kept here because the Bomber/Helicopter measurement below is what proved a FINE axis
necessary in the first place, and that conclusion carried straight into the global one.

**What it buys, measured on `CannonAP`'s AIR rows, h=0 → h=2:**

| | Bomber | Helicopter |
|---|--:|--:|
| three buckets | 80.35 → 79.49 (**−0.86**) | 82.46 → 81.58 (**−0.88**) |
| per-ladder | 79.71 → 76.61 (**−3.10**) | 80.09 → 81.88 (**+1.79**) |

Under the buckets both move identically — the bell is blind to the distinction. Under the fine axis
they move in OPPOSITE directions, which is the design. And it cost nothing: across 48 families both
axes give the same 2 inversions, the same 2 flat families and zero mean drift.

##### ⭐ 9.5b THE RULED AXIS — one global 13-slot scale (maintainer 2026-08-24)

> *"scout -> none -> fighter -> light -> wood -> bomber -> medium = flak = steel -> helicopter ->
> concrete -> heavy -> spaceship -> plate -> superheavy … symmetrical armor types that are always
> evenly distributed from 0 to 2.0, and the 3 medium / flak / steel armor types in the middle with
> exactly 1.0."*

13 evenly spaced slots, step 1/6, and **every ladder is centred exactly on 1.000** — the property
that makes `h=1` mean "medium" in all four domains at once. The full table, the deliberate
three-way tie at 1.0 (worth ≤0.89% on any row, because those three armors sit in three different
ladders and the rank restore is per-ladder), and the ladder-width design claim are in
**DESIGN §12.0i**, which is binding. Do not restate the numbers here.

⚠ **The axis cannot be measured out of the corpus, and two attempts to do so both failed for
structural reasons.** Recorded so nobody tries a third time:

* the cross-ladder OFFSETS are provably not identifiable. Fit `log V = family + macro(family,
  ladder) + lean·heaviness(armor)`: the `macro` term is the confound (`Bullet` favours infantry
  whatever its heaviness) and removing it makes each ladder's residual mean exactly zero by
  construction. Raw PC1 without that removal is 56% ladder-membership — half macro-type, not
  heaviness.
* the within-ladder SPACING that survives correlates **0.979** with mean `build_order` rank. The
  profiles are GENERATED, so "measuring" them re-reads `gen_weapon_template`'s interleave rule
  rather than confirming it.

What the corpus CAN confirm, and does: with macro-type removed, one axis explains **92.3%** of the
residual and all four ladders come out monotone lightest→heaviest independently. The ORDER is real.
The numbers are a ruling.

The superseded reasoning, kept for provenance:

##### ~~9.5a the armor x-axis is §12.0d's three buckets~~

The bell needs an x-coordinate per armor class, and `None/Light/Medium/Heavy/Superheavy` is not one
axis once `Helicopter`, `Heroic`, `Scout`, `Shield`, `Wood`, `Steel`, `Plate` and `Concrete` are
included. **Ruled: reuse the three tilt buckets DESIGN §12.0d already defines**, as x = 0, 1, 2:

| x | bucket | armors |
|--:|---|---|
| 0 | light | `None` `Wood` `Scout` `Light` `Fighter` |
| 1 | middle | `Flak` `Steel` `Medium` `Bomber` `Helicopter` |
| 2 | heavy | `Plate` `Concrete` `Heavy` `Superheavy` `Spaceship` |

Zero new rulings, and guaranteed consistent with the tilt law already shipped and already verified
(`audit_versus_profile`: *"every family keeps one direction within every ladder, at every level"*).

⚠ **Consequences to implement against, not to be surprised by.** Armors TIE at a coordinate:
`Scout` = `Light` = 0 and `Heavy` = `Superheavy` = 2, so the bell cannot separate them. It does not
need to — it only shifts a centre of mass, the family's own base profile still differentiates those
rungs, and §12.0d restores each armor's rank afterwards. `Shield` is excluded (§12.0c: its own
compressed ladder, not a normal armor), as are the five ALL-CAPS platings (§12.0e) and `Heroic`
(§12.0b: a derived cell, recomputed rather than tilted).

#### 9.6 Build order — ⭐ steps 1-4 are DONE; the bell is unblocked (2026-08-23)

| # | step | state |
|--:|---|---|
| 1 | Fix the 9 broken level ladders | ✅ **retired, not fixed** — see below |
| 2 | Every family into the 2x-8x spread band (§9.4) | ✅ **already done 2026-08-22** |
| 3 | Rule the armor x-axis (§9.5) | ✅ ruled 2026-08-24 — one global 13-slot scale, §9.5b |
| 4 | Rule §9.3: does heaviness affect price? | ✅ ruled — no, price via `Damage` |
| 4b | Rule `mu`, `LO`, `sigma` | ✅ ruled 2026-08-24 — blend, 0.667, 0.75 |
| 5 | Implement the bell in `gen_weapon_template`, then `AreaDamageWarhead` | ✅ `gen_weapon_template` bell implemented (OFF by default); ✅ `AreaDamageWarhead` C# transform wired (inert at Heaviness 0); Spread scales linearly 2/3→1→4/3 for h∈[0,2]; Trace/Super outside ruled range |
| 6 | Verify no family inverts; verify the weighted mean is invariant | ✅ `audit_heaviness_bell` |
| 7 | Collapse to one template per family; set `h` by the §3.3 rule | |

**Step 1 was never a real blocker.** The ladder audit measured the *effective damage* of the
weapons on each rung, but 145 of the `^Warhead_*` templates carry only a placeholder `Damage: 2000`
— the template holds the SHAPE and the weapon holds the MAGNITUDE. Collapsing Light/Medium/Heavy
into one template plus a continuous `h` therefore never touches a damage number, and a family's
damage ladder is orthogonal to the bell. The maintainer ruled the monotonic check retired on
2026-08-23; nothing in §12.0d or §12.0h ever required it.

**Step 2 was already finished and the document had not noticed.** `SPREAD_OFFENDERS_BASELINE = 0`
in `audit_versus_profile.py`, cleared by `fit_band_floor` in `gen_weapon_template.py` on
2026-08-22: **46 families in band**, with only `Sonic` and `Magic` excluded as flat by design.

So the next action is step 5 — implementation — with every parameter now fixed:

    x(armor)      = the global 13-slot scale, §9.5b / DESIGN §12.0i
    mu(family, h) = ( h + centre_of_mass(base_profile) ) / 2
    LO            = 0.667                      (swing 1.50x = 1/TILT_RATIO)
    sigma         = 0.75
    Versus(a, h)  = base(a) * curve(x(a), mu)  then renormalised, then RANK-RESTORED per ladder

⚠ **"Inert at h=1" is a DEPLOYMENT property and it needs proving on the right comparison.** Under
the retired family-anchored peak it was unachievable — the bell reshaped all 48 families at h=1,
worst row 13.5%. Under the ruled model h=1 peaks at the middle rung of every ladder, i.e. exactly
§12.0d's Medium tilt, so the test is: regenerate the templates through the bell at h ∈ {0, 1, 2}
and diff against today's Light / Medium / Heavy yaml. ⛔ Do NOT compare the bell against the
shipped TEMPLATES directly — the level also changes the body's `step` and `floor`, so even the
shipped `class_tilt` scores **+18.7% worse than doing nothing** on that comparison. Compare tilt to
tilt, on the same base.
