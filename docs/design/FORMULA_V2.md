# FORMULA V2 — the complete law book (as learned through 2026-07-19)

_Where this fits: [`BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md) is the phase sequence,
[`BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md) is the board and ownership, and
[`BALANCE_PIPELINE.md`](BALANCE_PIPELINE.md) is the machinery. (The old `MEGAPLAN.md`
index is archived at [`../history/MEGAPLAN_2026-08-08.md`](../history/MEGAPLAN_2026-08-08.md).)_

_The consolidated, binding reference for the per-class balance system.
Grew out of DESIGN §12 + the balance pipeline (BALANCE_PIPELINE.md) +
the scout-class conversions (docs/balance/formula_v2_classes.md holds the
class log). Update THIS file whenever a law is added or tuned._

## 1. The construction (why O = P = Q = cost always holds)

Each class formula normalizes every stat against the class BASELINE
unit (h₀ = HP, s₀ = Speed, r₀ = Range in wdist, d₀ = effective DPS,
C₀ = cost). With ratios h,s,r,d (and r carrying the Special factor K):

    O = (h + s + r + d) · C₀/4 · Tier
    P = (h·s + r·d)      · C₀/2 · Tier
    Q = (h·s·r·d)        · C₀   · Tier
    price = (O + P + Q) / 3

- At the baseline every ratio is 1 → **O = P = Q = price = C₀ exactly**
  (the maintainer's rule; must hold for EVERY baseline unit).
- The legacy Tiger global formula IS this construction with
  (100000, 100, 5000, 200, 800) plugged in — its "magic constants"
  (25000, 12.5e6, ×200) all derive from the anchor.
- **The King-Tiger identity**: at 2×HP + 2×damage, same range/speed →
  O = 1.5×, P = 2.0×, Q = 4.0×, price = 2.5×. ALWAYS, for any class.
- Price is LINEAR in each single stat → closed-form solvers (the
  workbook's Range-from-Cost column) survive every class variant.
- Code: `tools/balance/formula.py::class_baseline_estimators/price`.
  Registry: `docs/balance/class_anchors.json`.

## 2. Baselines & verifiers (fixed points at both envelope ends)

- Every class gets a **living baseline unit in game** (round stats,
  price = C₀ exactly) — the testable reference.
- Every class gets a **verification unit**: exactly 2×HP + 2×damage,
  same range/speed, 250% cost — price must compute 2.5×C₀ EXACTLY.
  It doubles as a formula tripwire (it caught a shadowed-override bug
  on day one).
- Established anchors:
  | class | baseline | stats | verifier |
  |---|---|---|---|
  | mbt | Naxis Tiger Tank | 100000/100/5000/10000@50 → 800 | King Tiger (2×/2× @ 2000) |
  | scout | naxis_naxiriflesoldier | 20000/60/5000/4000@50 SA → 100 | forgotten_mutantsoldier (40000/60/5000/8000@50 → 250.0000 exact) |
  | special forces | japan_imperialscoutsman | 15000/50/6000/6000@50 (SA+CG+Railgun-AP, air, bullet) → 200 | schwarzermond_lunarsoldier (T1, 30000/50/6000 SA+CG+Laser 12000@50 → 500.00 exact) |

  **Scout↔SF baseline transfer — DONE 2026-07-20** (`cb4e926a4` + build
  commit): japan_imperialscoutsman moved scout → special forces
  (15000/50/6000/200, air restored, bullet+railgun-AP weapon, precise
  small spread, `^SpecialForcesInfantryTemplate` via a clean `@Template`
  inherit swap — resolved Armor Flak confirms); naxis_naxiriflesoldier
  took over the scout anchor (exact 20000/60/5000/4000@50, ground-only).
  Both resolver-verified (100.00 / 200.00 exact).

## 3. Stat laws (all classes unless stated)

- **Price**: 10-credit steps; envelope **50%–250% of the class C₀**;
  classic C&C factions keep their ORIGINAL prices (memorability);
  custom factions (AsianAlliance, LatinSyndicate, …) may deviate.
- **Range**: ±10% of the class baseline (HARD band; scouts 4500–5500);
  low edge = cheapest units, high edge = priciest; **steps of 10**
  (tank shells use bullet speed = range/10; tank destroyers = 2× that).
- **Speed**: ±20% of baseline (provisional, maintainer will tune).
  Vehicles, aircraft, AND ships: **steps of 5** (turn rate = speed/5, so
  speed MUST be a multiple of 5). **Infantry: steps of 1** (free integer
  values — instant turn, no /5 constraint) — use the freedom for faction
  character.
- **HP**: infantry in 1000 steps; self-heal Step = HP/1000. (The
  2×-health bake replaced the ScoutInfantryBuff 50% damage reduction —
  ⚠ **for 19 of 35 scouts. Measured 2026-08-17: 16 still resolve to
  `DamageMultiplier@ScoutInfantryBuff: 50`**, i.e. double effective HP
  that the price does not see. `^ScoutInfantryTemplate` still carries the
  50; the migrated actors CANCEL it with a local `Modifier: 100`, which
  is why those overrides look like deletable no-ops and are not — see
  BALANCE_PROGRAM_PLAN §W26. Claim: `unmigrated_scout_damage_multiplier`.)
- **Damage**: steps of 100. Percentage companions use basis-point units so
  every 100 flat Damage tracks 0.01% max HP (1% per 10000); folded
  `PercentageScale` hits derive their amount from the same main Damage.
- **Burst is flavor, not power** (i.e. burst count is a presentation/
  weapon-feel constraint, not an independently priced bonus — the full burst
  and every inter-shot gap are already included in effective DPS): keep burst
  feel, then trim the main Damage on the 100 grid or adjust reload timing.
  Unconditional actor `FirepowerMultiplier` is retired as a tuning knob.
  Gatling/spinup units
  (soviet gatling tank, RA1 allied heavy AA tank) are special cases —
  handle individually.
- **Weapon-class bands by cost** (scout values; per-class analogues):
  ≤150% of C₀ → SmallArms only (WC 0.75); above → SmallArms+Chaingun
  (WC 0.875). The class's own DPS₀ already includes the baseline WC.
- **SoundVolume = 1/burst** (LAW): a BurstDelays-0 weapon firing N
  shots on one tick must set SoundVolume 1/N or it deafens.
  **BASE weapon only** (maintainer 2026-07-20): scale the volume once,
  on the base weapon; upgrade/elite/veteran variants that raise Burst
  (e.g. fanatic 10→13→16) do NOT re-scale — they inherit the base's
  SoundVolume and are simply allowed to get louder with more shots.
  A `SoundVolume:` override on a `_upgrade`/`_elite` variant is a bug.
- **Tech tier factor** multiplies O/P/Q: T1 = 1.0, T3 = 0.75
  (higher tech = cheaper per stat). From the deepest tech-building
  prerequisite. Closecombat verifier doubles DPS via 2x BURSTS.
- **Scout infantry never hit aircraft**: ValidTargets Ground, Water on
  every scout weapon INCLUDING upgrade variants; units use
  ^AutoTargetGroundAssaultMove (faction consistency program).

## 3b. Promotion/special-upgrade units (global)

- Units unlocked by promotion or special upgrades inherit `^PromotionUnitBuff`.
  That buff is an **external faction buff** and is ignored by the balance
  formula — base stats are priced, not the buffed state.
- Such a unit's tech tier is taken from the unit's own build prerequisite,
  **not** the upgrade's tier. T1 and T2 both use the same 1.0x tech-class
  multiplier, so an upgrade gated at radar tier does not change the unit's
  formula tier as long as the unit itself is buildable from a T1/T2 structure.

## 3c. The special-modifier system (K) — trait-derived, not guessed (maintainer 2026-07-20)

The Special factor **K** on the range ratio (§1) is **1 + Σ(special
weights)**, computed from the actor's TRAITS so K is never guessed.
Legacy column K (cameo_armor_system.xlsx) is reproduced EXACTLY by this
table. A "special" = value the base HP/speed/range/DPS pricing does NOT
already capture.

**Standard specials — +0.25 each:**

| special | detect by (yaml/engine) | example |
|---|---|---|
| Deploy / mode-switch to a 2nd weapon | `GrantConditionOnDeploy` + a deploy-gated Armament | G.I., Guardian G.I., Javelin |
| Demolition / C4 | a C4/GenericC4 demolition armament | Navy Seal, Tanya, Commando |
| Stealth / cloak | `Cloak` | Stealth Soldier |
| Status-effect warhead | EMP / tesla / fire / virus-toxin / radiation warhead (curated set) | EMP Grenadier, Tesla Trooper |
| Support-power / drone / kamikaze | a `SupportPower` trait or drone/kamikaze armament | ASDF, kamikaze |
| Caster ability | activated non-damage ability (heal/mind-control/polymorph) — MANUAL if AoE-DoT dominant | High Templar |
| Gatling spin-up / ramp | `^GatlingSpeedUpUnitBehavior` | Gatling Trooper, Eliminator 800 |
| Sniper instakill / lockdown | lockdown attach or instakill-vs-infantry weapon | Ghost, Allied Sniper |
| Point-defense | point-defense trait (intercepts incoming projectiles) | Laser Commando, TD Nod Light Tank Mk2 |
| Spawns an attacking sub-actor | `Warhead@…: SpawnActor` dropping an actor with its own weapon (black hole, mines, drone) | Parzival (BlackHoleMaker → hole_small.nax2) → K 1.25 |
| Friendly aura buff | a proximity buff aura (firepower/speed/armour to nearby allies) — often VERY strong, RE-TIER to Major+ | TD GDI Officer **propaganda** |
| Debuff warhead / designator | snare (slow), blind (vision/accuracy cut), or target-designator (marks for bonus damage) | zerg corruptor (snare), latin smoker tank (blind), GDI Predator (targeting laser) |

**Legacy single-value notes (do not overwrite):**
- `japan_exorcist` deploy-ability (spellcard) is kept at **K = 0.25**
  per the old spreadsheet. The in-game `DamageMultiplier@SpellCard` and
  `FirepowerMultiplier@SpellCard` are YAML balance values (currently 50)
  and are NOT this formula K.

**Heavy special — +1.0** (worth far more than a normal special):

| special | detect by | example |
|---|---|---|
| All-terrain movement (aircraft-like) | `Mobile: Locomotor: fakeaircraft` (ignores terrain) | Reaper → K 2.0 |

**MANUAL / algorithmic-pending** — NOT true "abilities" but pricing gaps
the current DPS math misprices; hand-price + flag, and FIX the math
(roadmap) rather than leave a permanent K kludge:

| gap | detect by | example |
|---|---|---|
| Multi-warhead stacking (DPS undercounted) | one weapon inherits several damage templates (`^Grenade+^Shrapnel+^HeavyBomb+^MediumMissile+^Chaingun+^FlakWeapon…`) so a shot applies many warheads; max-warhead DPS misses the SUM | **Patriarch** (K 2.0 was a kludge; real fix = sum the damage warheads in DPS, then K→1.0) — **DONE**: DPS/pricing use `formula.spread_damage_sum`; the workbook Damage cell is the per-shot TOTAL and `formula.distribute_damage` gives every main warhead the identical `total ÷ N` on the 100 grid (FF + ExtraDamage 50%; standalone Percentage companions track 0.01% per 100 flat Damage in their own denominator; folded percentage derives from the main; ExtraDamage excluded from the total), so the design number can't be broadcast onto every warhead. Guard: `audit_warhead_split`. See BALANCE_PIPELINE §3. |
| Probabilistic / bounce / AoE-DoT | <100%-hit split warheads, or damage-over-area-over-time from a caster/spawned actor | high templar psi-storm, spawned black-hole DoT |

**Validation (reproduces legacy K exactly):**
- Laser Commando = cloak + point-defense + C4 + gatling = 4×0.25 → **K 2.0** ✓
- Stealth Soldier = cloak + EMP warhead = 2×0.25 → **K 1.5** ✓
- Reaper = fakeaircraft locomotor = +1.0 → **K 2.0** ✓
- G.I. / Navy Seal / ASDF / High Templar / Gatling Trooper = 1 special → **K 1.25** ✓

**NOT a special:** hitting air with the PRIMARY weapon (Marine = K 1.0).
Only a SEPARATE weapon/mode or an ability counts — never the primary
weapon's target list. So a Special-Forces unit's air capability is
baseline, never charged.

Extractor auto-detects `Cloak` / `GrantConditionOnDeploy` / the gatling
trait / the `fakeaircraft` locomotor / `SpawnActor` warheads; the
status-warhead and caster sets are small curated lists; MANUAL rows are
flagged for hand-pricing (K stays 1.0 in the auto pass until set).

**COLLECT-ALL (task, do not skip):** the list above is SEEDED, not
complete — memory misses effects (propaganda aura, snare, blind, target
designator, point-defense were all missed on the first pass). A repo-wide
trait scan (aura/proximity-buff traits, condition-granting warheads,
support-power traits, debuff beams) must ENUMERATE every effect in the
game so none is missed, then each is slotted into a tier. This runs
alongside the extractor's K detection.

**Future direction (maintainer 2026-07-20) — per-ability values, shown
itemized (NOT one opaque number):** the uniform +0.25 above is an INTERIM
placeholder. The target is a UNIQUE power value PER ability (deploy ≠ C4
≠ stealth in real worth), each with its own flag/column, so the workbook
shows the special as an **itemized list** (a checkbox/collection per
ability) that SUMS to K — never a lone combined value whose origin can't
be traced, justified, or reviewed. The extractor therefore emits the
LIST of detected specials + each ability's value; the sheet totals them.
- **Negative specials exist** (subtract from K): a very long charge delay
  (Obelisk-of-Light style) = **−0.25**; frontal-facing (non-turreted)
  vehicle weapons = **−0.25** — a genuine disadvantage vs turreted units
  that move and fire at once.

  ⚠ **The charge-delay half is now IMPLEMENTED as an actor price multiplier,
  NOT as a negative special — do not apply both** (W4, 2026-08-11). Note the direction:
  the charge delay is the NERF, and the price cut is the COMPENSATION for it. Since a
  cheaper unit is better per credit, compensating twice does not "double-nerf" it — it
  leaves it **over-paid and cost-efficient**, which is the opposite of the intent. An actor
  carrying `AttackCharged` / `AttackTurretedCharged` / `AttackFrontalCharged` /
  `AttackCharges` prices at **0.75×** via `formula.charge_price_multiplier`,
  read from the ledger's `charge_up` field. It is a multiplier on the PRICE
  rather than −0.25 on the special K because `special` enters `estimators()`
  on the range term only, so it would neither be a clean 0.75× nor scale the
  HP/DPS terms the charge delay actually devalues. The frontal-facing half is
  still FUTURE / VEHICLE scope and unimplemented.
- **Scope order:** finish INFANTRY on the interim uniform weights first;
  the per-ability value table + negative specials land when we start
  VEHICLES (the program AFTER infantry).

## 3d. Rebalance uniqueness & preservation rules (2026-07-21)

These rules govern every class-wide stat pass. They live here, not in a
class-specific log, because they apply to all classes.

- **Uniqueness within a class** (EXACTLY these 5, checked against each other):
  no two units may share the same **HP**, **Speed**, **effective damage per
  shot** (= Σ of all offensive warhead `Damage` at the baseline actor state),
  **raw `ReloadDelay`** (NOT the burst-adjusted/effective reload), or **Range**.
  An inherited or conditional `FirepowerMultiplier` is gameplay state, not a
  uniqueness key or a fine-tuning knob; tune base output on the 100-Damage grid.
  #3 (effective damage per shot) and #4 (raw ReloadDelay)
  are checked SEPARATELY, so two units may share one if they differ on the other.
- **Baseline/verifier exception only**: the verification unit is exactly
  2× HP, 2× DPS, 2.5× cost, same Range and Speed as the baseline (§2). No other
  pair may share a stat.
- **Preserve relative differences**: do not clamp every unit to the same band
  edge. If a unit was the longest-ranged member, keep it the longest-ranged
  member after shrinking; shrink the whole class toward the allowed band
  proportionally, not uniformly.
- **Faction personality over formula equality**: similar factions stay close
  (e.g. RA1 Allies rifle vs RA1 Soviets rifle, TD GDI minigunner vs TD Nod
  minigunner) but every stat must differ by at least one step. Use lore/identity
  to choose which axis each faction emphasizes.
- **Original C&C prices are pinned**: TD, TS, RA1, and RA2 factions keep their
  original costs for memorability; only stats move. Custom/RA2-mod factions may
  adjust cost in 10-credit steps inside the class envelope.
- **Damage stays in 100 steps**: never write free-valued or unequal main
  warhead Damage; adjust effective DPS on that grid or with `ReloadDelay`.
- **Outlier flag rule**: if a unit's current stats place it so far outside the
  allowed band that fixing it would completely change its character, stop and
  ask the maintainer before editing.

## 4. Weapon & template laws

- **Weapon Versus tables**: built by the step law in ARMOR_SYSTEM.md —
  LEVEL = step 6/5/4 (light/medium/heavy, floor 10/25/40, Shield
  110/125/140), PROFILE = the armor order. Generate, never hand-type.
- **`*ExtraDamage` warheads: value = 50% of the main, EXCLUDED from the
  damage total** (maintainer 2026-07-27, supersedes the 2026-07-20
  "never scale" note). The `Warhead@…ExtraDamage` an energy template carries
  (Railgun/Laser/Tesla/…, Versus ~1 vs everything except Shield ~100) is the
  compensation for an energy weapon's smaller area-of-effect plus its
  shield/bonus chip. It is ALWAYS **50% of the main warhead damage** (Tesla
  main 2000 → ExtraDamage 1000), written by `formula.distribute_damage`, but
  the DPS/price **sum still skips any warhead whose key ends `ExtraDamage`**
  (`formula.spread_damage_sum`).
> ⚠ **WeaponClass NO LONGER PRICES ANYTHING (W4, 2026-08-11).** `formula.dps()`
> dropped its `weapon_class` argument, and the workbook's DPS cell dropped its
> `*WeapClass` factor to match. WC was a tier weight standing in for "how good is
> this weapon type" back when nothing measured that; the K coefficient
> (`weapon_efficiency.py`) now measures it from the weapon's own geometry, so
> keeping the weight too would charge a weapon twice for one property. The
> `design_weapon_class` field stays in the ledger and the workbook as design data —
> the warhead-triad meaning below is unchanged and still governs template design.
> Verify with `inspect.signature(formula.dps)`, not a grep: the docstrings that
> explain the retirement necessarily name the retired thing.

- **A "weapon class" (WC 1.0) = a light+medium+heavy warhead TRIAD**
  (maintainer 2026-07-20): one light + one medium + one heavy SpreadDamage
  warhead summed. Baseline japan = SmallArms + Chaingun + Railgun-AP; a
  member may re-theme the triad (CannonAP+Flak+Laser, SA+Chaingun+Laser…)
  and keep the same WC. `^TankDestroyerCannon` = the interim Light CannonAP
  until the weapon-template refactor renames it; `^HeavyCannon` is
  deprecated (too much spread — use a small-spread heavy like Railgun/Laser).

- **Dedicated weapons**: a converted unit never shares its weapon —
  check sharing repo-wide FIRST (`Weapon: <name>`); shared originals
  stay for their other users (brik.shp lesson, weapon edition).
- **Pair-rename law** ("remembered at all times"): renaming/dedicating
  a base weapon ALWAYS renames its upgrade variants with it — the
  family moves together, orphans are retired.
- **Templates are law**: conyards always use the ^Conyard template
  Power (100); icons set Offset: 0,0 whenever their image's Defaults
  defines a nonzero offset (`audit_template_conformance` enforces both).
- **Every unit is UNIQUE within its class** (maintainer 2026-07-19):
  no two units in a class share identical HP / speed / damage /
  reload — give each faction's member its own small deviations
  (per the faction-personality guide §5), pricing each via the
  formula. EXCEPTION: original C&C units keep their ORIGINAL price
  (stats still vary; the price is pinned). This kills clone rows
  like the three identical D2k light infantry (light_inf /
  ixian_lightinfantry / ordos_lightinfantry): Ordos = cheaper/
  faster/weaker, Ixian = pricier/slower/harder-hitting.
- **Descriptions carry NO `
`**: unit/weapon descriptions live in the
  fluent files (`fluent/**/en.ftl`) with REAL line breaks, never the
  `
` escape. New descriptions go straight to fluent.
- **Knob hierarchy** (^GlobalBuffs → class → subclass) stays as the
  live one-value tuning layer, pipeline-owned, with knob-aware pricing;
  formula-gap patches get baked away per class (BALANCE_PIPELINE §5b).

## 5. Faction personality (differentiation guide)

Same-class units vary SLIGHTLY per faction, staying near their old
feel: e.g. minigunners faster + shorter-ranged than rifle soldiers
(TD GDI 4600/63 disciplined, TD Nod 4500/66 light & fast) vs rifles
longer-ranged + slower (Allies 5400/57 accurate, Soviets 5100/54
tanky). Larger personalities for custom factions: Ordos = weak, cheap,
fast; Ixians = expensive, slow, high firepower/range/attack speed.

## 6. The conversion process (one unit at a time, learn each time)

1. Read the class conversion log (`docs/balance/formula_v2_<class>.md`)
   — accumulated lessons are BINDING.
2. Check weapon sharing → dedicate the weapon family (pair law).
3. Apply stat laws (bands, steps, bake, no-air for scouts).
4. Neutralize class knobs per-unit (Modifier: 100) until the whole
   class is converted, then delete knobs + overrides in one sweep.
5. Scale ChangesHealth — EXACT tag `ChangesHealth@SelfHealing` (a
   resolved infantry carries a dozen conditional heal traits).
6. Edit EXISTING stat lines; a block's later same-trait definition
   shadows anything inserted above it.
7. Verify price via resolver + formula BEFORE boot (target ±2%).
8. Ledger sync (`extract_stats.py`, design fields, `--check` green),
   boot gate, scoped commit, push, append the conversion-log entry.

## 6b. The infantry class ladder (target state, rev. 2026-07-19 late)

**CONTIGUOUS half-open range bands** (maintainer design): no unit can
ever fall between classes again — the band DEFINES membership.

| class | range band | anchor r₀ | baseline | status |
|---|---|---|---|---|
| melee | [1250, 2500) | 1750 | TBD | future anchor; range is SIZE-DERIVED (see below) |
| **closecombat** (shotgun/SMG) | **[2500, 4500)** | **3500** | td_gdi_shotgunner @ 200 | **LIVE** (baseline 200.00, verifier fanatic 500.00 exact, +naxis_sssoldier T3) |
| scout (rifles) | [4500, 5500] | 5000 | naxis_naxiriflesoldier @ 100 | LIVE (6 converted; baseline moved from japan 2026-07-20) |

- **Band width is a PER-CLASS property.** Scouts keep the tight ±10%
  (one weapon archetype: rifles). Melee and closecombat get WIDE
  contiguous bands because their ranges express different things:
- **Melee range IS priced — like every other class** (maintainer
  correction 2026-07-22; the earlier "fixed ratio 1 / not priced" claim
  was WRONG and unauthored). Reach still follows unit size (small:
  shriek 1150 / zergling 1350 / zealot 1335; medium: footman 1333 /
  knight 1420 / worker 1500; large: dogs 2000; huge melee VEHICLES like
  the Consortium Megalodon belong to a melee-vehicle class, not
  infantry). Size→reach convention: small 1250–1400, medium 1400–1700,
  large 1700–2500. Sub-1250 outliers (zombiemutant 1127) round UP to
  1250. The reasoning: bigger units are *balanced around* having more
  reach (grunt > footman), so range enters the formula normally — the
  spread is just small (1250–1750). Melee ANCHOR (2026-07-22):
  baseline `asianalliance_alligator` 27000/90/1400/DPS300 @ 280,
  verifier `yuri_brute` 54000/90/1400/DPS600 @ 700 (both scaled to a
  common speed 90; cost 280→700 keeps the WC/SC verifier a multiple of 20).
- **Closecombat range IS a balance lever** (2500 SMG spray → 4500
  long shotgun): it prices normally, and the wide band follows the
  price-gradient law — cheapest members at the low edge, priciest at
  the high edge (a cost axis, not free choice).
- Boundary rule: a weapon at exactly 2500 is closecombat; exactly
  4500 is scout (half-open bands).
| **special forces** (advanced; CAN hit air) | 5500–6500 (r₀ 6000) | 6000 | japan_imperialscoutsman @ 200 | **LIVE** (baseline 200.00; verifier + roster next) |
| grenadier | TBD | TBD | grenade/demolition infantry (td_gdi_empgrenadier) |
| heavy infantry | TBD (very high HP to survive heavy fire) | TBD | ixian_shockinfantry, tkm_juggernaut(?), forgotten fiends |
| sniper (PURE) | TBD (long) | TBD | targets ONLY infantry; big stat boost compensates the restriction; no air, no vehicles |
| heavy sniper | TBD (long) | TBD | all GROUND, NO air; loses to pure snipers as the trade (td_gdi_heavysniper, ra2_allies_sniper, tkm_sniper) |
| rocket trooper | TBD | TBD | dedicated rocket/AA-launcher infantry (NEW class, built after SF; quantummissiletrooper, all the _rocketsoldier/_tankkiller units) |
| archer | scales with range | TBD | projectile-arc infantry; uses the MISSILE projectile (tracks targets); **arrow speed = maxRange/10** (tank-bullet scaling; TD cannons use 2×); hits air (wc2 archers, japan/asian maidens) |
| support / special | n/a (ability-priced) | n/a | medics, mechanics, engineers, casters, spies, mind-control, hackers; price = baseline + Σ special-K (§3b). **HP is PER-UNIT** — weak support share ~5000, but strong casters (wc2 mage/deathknight, high templar) keep their high HP to fight |
| flying infantry | n/a (movement class) | n/a | over-terrain (cosmonaut, jumpjet, rocketeer, skymage, swarmling) |
| hero / commando | ~2000 attach/C4 | TBD | unique high-cost; multiple stacked specials (§3b); mostly left as-is |

- **A class is a PRICING ARCHETYPE, not a uniqueness key** (maintainer
  2026-07-20): a faction MAY field several units of the same class
  (Terran Marine AND Ghost are both special forces). The §4 uniqueness
  law keeps their stats distinct; the soft goal is roster VARIETY across
  classes, not one-template-per-unit-per-faction.
- **Air is the special-forces class trait**, baked into the baseline —
  hitting air is NEVER a per-unit special (§3b).

### Roster verdicts — air-capable infantry sweep (maintainer 2026-07-20)
- **→ special forces:** marine, ghost/specter, clone trooper, lunar
  soldier, tkm marine, elite cadre, scout-droid, madcap, navy seal
  (from sniper), stealth soldier, gatling trooper, eliminator 800, GDI
  officer, dragunov (anti-material), narco, mutant sergeant, coneheads
  knight, tiberian fiends (or heavy infantry), crazy ivan (bomb-attach).
- **→ scout (lose air):** conscript, asian militia, latin militia, tkm
  trooper, yuri initiate (gatling trooper is Yuri's SF), naxi
  slaveoverseer, zerg spithid, cabal devout, cabal cyborginfantry
  (so eliminator 800 owns CABAL's SF slot).
- **→ closecombat:** ixian rashinan → **rename ixian_rashidan** (+ its
  promotion), futuretech shotgundroid, futuretech enforcer (give it a
  shotgun burst; its AA is bot-only).
- **→ grenadier:** td_gdi_empgrenadier. **→ heavy infantry:**
  ixian_shockinfantry, tkm_juggernaut. **→ melee:** wc2 knight, wc2 ogre.
- **→ vehicle:** naxis_bmwbike (scout vehicle — not infantry), wc2
  kodobeast (support vehicle: change unit template + armor Medium only,
  keep other inherits).
- **→ flying infantry:** cosmonaut, jumpjet, rocketeer, skymage,
  swarmling. **→ archer class:** all the wc2/japan/asian archers.
  **→ support class:** casters (mages/deathknight/templar/defiler),
  medics, mechanics, engineers.
- **Left as-is:** heroes (≥3000), dedicated-AA specials (skymage,
  quantum missile trooper → rocket-trooper class), fremen_creep (not
  player-controlled), civilians delphi/general/technician (ground-only,
  unused).
- **Heavy-sniper override:** td_gdi_heavysniper is a HEAVY SNIPER (loses
  air), NOT special forces — the earlier SF call is superseded.

_Roadmap item (maintainer 2026-07-20):_ no-attack units (medics,
mechanics, engineers) use a `dummytargeting` weapon as a movement
stopgap so they don't rush in and die. Proper fix = kiting AI that keeps
distance and never advances into enemies — belongs on the long-term
roadmap, not shipped as dummytargeting forever.

## 6c. Vehicle classes (FUTURE — the program AFTER infantry)

Do NOT start until the infantry rebalance is complete; recorded here so
the scope is fixed. Each gets template → baseline → verifier like the
infantry classes.

| class | notes |
|---|---|
| MBT (main battle tank) | LIVE anchor: Naxis Tiger (§2) — the global reference |
| light tank | fast, cheap, low-armour raider/scout tank — NEW template |
| battlefortress | slow "bunker on tracks": high HP, troop-carry/garrison, short range — NEW template |
| anti-air vehicle | dedicated mobile AA (flak/missile) — NEW template |
| tank destroyer | AP glass-cannon vs heavy armour; frontal weapon (−0.25 special); range/speed on the 2×-bullet-speed convention — NEW template |

Vehicle-only specials attach here (§3b future scope): frontal-facing
(non-turreted) weapon = −0.25. Long charge delay is NO LONGER a special —
it became the actor-level 0.75× price multiplier in W4 (see §3b); applying
both would discount a charging unit twice.
The per-ability special-value table replaces the interim uniform weights
at the start of this program.

## 7. Open items

- Scout proposal (formula_v2_scout.md) awaits maintainer row verdicts;
  ranges clamp to the band at application.
- Speed ±20% band and other stat bands await maintainer tuning.
- Unconverted scout weapons (shared M16/M1Carbine users) get the
  no-air rule at their own conversion.
- Next classes: bomber (replace reload-250 convention), defense
  (replace speed-100), infantry sub-anchors, fighter port.
- MARS-type shrapnel-chain weapons need extractor coverage first.

### D2k light-infantry price ladder (maintainer 2026-07-20)
Same scout class, per-faction unique stats + price (light_inf_lmg
base; each differs in HP/speed/firepower):
- Ordos 120 (cheap/fast/weak: 28000/62/82%)
- Atreides 130 (FUTURE — between Ordos and the 150 tier)
- Harkonnen 140 (FUTURE)
- light_inf 150 (generic tanky: 40000/54/91%) · Ixian 150
  (elite/high-tech: 32000/56/113% — fragile, high firepower)
- Corrino Sardaukar — special, MORE expensive than all (FUTURE)
