# RA1, Tiberian Dawn, and Dune Infantry Formula Audit

> ⛔ **ARCHIVED 2026-08-23.** A one-off dated audit, not live evidence. Current audit output is
> regenerated into `docs/audit/latest/` by `bash tools/audit/run_all.sh`.

Date: 2026-08-02
Scope: every active, buildable combat infantry actor belonging to RA1, Tiberian Dawn, or Dune 2000 / Dune Universe. The audit snapshot predates the Stealth Soldier correction recorded below.

## Result

At audit time, the Tiberian Dawn Nod **Stealth Soldier was severely overpowered**. Its weapon package was worth approximately **4,136 credits** under Formula V2 while the unit cost **753**, giving it about **5.5 times** the formula value paid for it.

This was not a subtle HP or range discrepancy. `BHRedDarts` applied five main offensive warheads at 22,000 damage each, for **110,000 damage per projectile**, then fired a four-projectile burst. After its 90-tick reload, 5-tick burst delay, and 93% actor firepower multiplier, the weapon produced about **3,897 effective DPS**. The Special Forces anchor is 240 DPS.

## Implemented correction — 2026-08-03

The Stealth Soldier now preserves its 753 cost, 25,000 HP, 72 speed, 6,480 range, four-shot burst, cloak, EMP effect, and promotion role while correcting the damage package:

- Each of the five main offensive warheads: 22,000 → 4,000 damage.
- Tesla extra-damage and shrapnel friendly-fire twins: 22,000 → 2,000 damage.
- Each percentage twin: 1% → 2%, matching the Formula-V2 distribution law for a 4,000-damage main warhead.
- Actor firepower multiplier: 93% → 81%.

The new main damage total is **20,000 per projectile**. Effective DPS is **617.14**, and the Formula-V2 price is approximately **755.25 credits** versus the pinned 753-credit cost (about **+0.3%**). This is a formula correction; controlled in-game burst and time-to-kill testing remains required.

The imbalance was introduced by commit `04de392b31` on 2026-07-22. That commit assigned 22,000 damage to each main warhead, set the actor firepower multiplier to 93%, and changed the cost to 753. The existing `proposal_special_forces_infantry.md` already records the Stealth Soldier as a major formula mismatch; it was documented but not normalized.

## Formula used

For each priced primary armament:

```text
effective reload = ReloadDelay + BurstDelays × (Burst - 1)
effective DPS = SUM(main offensive SpreadDamage warheads)
                × Burst / effective reload
                × WeaponClass
                × FirepowerMultiplier
```

Formula price then uses the actor's assigned class anchor:

```text
h = HP / anchor HP
s = Speed / anchor Speed
r = Range / anchor Range × Special K
d = effective DPS / anchor DPS

O = (h + s + r + d) × anchor cost / 4 × tech tier
P = (h×s + r×d) × anchor cost / 2 × tech tier
Q = h×s×r×d × anchor cost × tech tier
price = (O + P + Q) / 3
```

Twin `ExtraDamage`, `FriendlyFire`, and `Percentage` warheads are excluded from the damage sum, as required by Formula V2.

Interpretation used below:

- **Severely hot:** formula price is at least 2× listed cost.
- **Hot:** formula price is at least 25% above listed cost.
- **Near:** formula price is within ±25% of cost.
- **Cold:** formula price is at least 25% below listed cost.
- Commando, support, and several provisional infantry classes are not fully signed off; their results are diagnostic rather than automatic balance instructions.

## Tiberian Dawn

### GDI

| Actor | Class | Cost | Effective DPS | Formula price | Ratio | Finding |
|---|---|---:|---:|---:|---:|---|
| `td_gdi_minigunner` | Scout | 100 | 24 | 93 | 0.93× | Near |
| `td_gdi_grenadier` | Grenadier | 200 | 381 | 490 | 2.45× | **Severely hot** |
| `td_gdi_empgrenadier` | Grenadier | 500 | 735 | 2,266 | 4.53× | **Severely hot** |
| `td_gdi_rocketsoldier` | Rocket Trooper | 200 | 214 | 276 | 1.38× | Hot |
| `td_gdi_shotgunner` | Close Combat | 200 | 250 | 200 | 1.00× | Exact anchor |
| `td_gdi_sonicmissilesoldier` | Heavy Infantry | 400 | 425 | 465 | 1.16× | Near |
| `td_gdi_heavysniper` | Pure Sniper | 700 | 400 | 737 | 1.05× | Near |
| `td_gdi_officer` | Special Forces | 1,532 | 1,890 | 2,021 | 1.32× | Hot |
| `td_gdi_commando` | Commando | 3,000 | 1,200 | 3,019 | 1.01× | Near anchor |
| `td_gdi_havoc` | Commando | 4,000 | extractor reads 0 | 992 | 0.25× | **Extraction/armament-pricing problem; do not balance from this row** |

### Nod

| Actor | Class | Cost | Effective DPS | Formula price | Ratio | Finding |
|---|---|---:|---:|---:|---:|---|
| `td_nod_minigunner` | Scout | 100 | 31 | 95 | 0.95× | Near |
| `td_nod_rocketsoldier` | Rocket Trooper | 200 | 214 | 276 | 1.38× | Hot |
| `td_nod_chemicalrocketsoldier` | Rocket Trooper | 400 | 556 | 895 | 2.24× | **Severely hot** |
| `td_nod_flamethrower` | Melee | 200 | 250 | 215 | 1.08× | Near |
| `td_nod_chemicalwarrior` | Melee | 500 | 750 | 734 | 1.47× | Hot |
| `td_nod_blackhandflamer` | Heavy Infantry | 600 | 364 | 545 | 0.91× | Near |
| `td_nod_lasertrooper` | Special Forces | 750 | 3,110 | 2,018 | 2.69× | **Severely hot** |
| `td_nod_stealthsoldier` | Special Forces | 753 | 3,897 | 4,136 | 5.49× | **Worst credible combat outlier** |
| `td_nod_commando` | Commando | 3,000 | 1,200 | 3,019 | 1.01× | Near |
| `td_nod_lasercommando` | Commando | 5,000 | 125 | 1,149 | 0.23× | Cold on extracted primary DPS; abilities dominate and require manual review |

### TD support infantry

`E6` / Engineer is assigned to the ability-priced Support class and is not meaningfully evaluated by combat DPS.

## Red Alert 1

### Allies

| Actor | Class | Cost | Effective DPS | Formula price | Ratio | Finding |
|---|---|---:|---:|---:|---:|---|
| `ra1_allies_rifleinfantry` | Scout | 100 | 36 | 92 | 0.92× | Near |
| `ra1_allies_alliedrocketsoldier` | Rocket Trooper | 300 | 350 | 438 | 1.46× | Hot |
| `ra1_allies_alliedsniper` | Pure Sniper | 500 | 225 | 279 | 0.56× | Cold |
| `ra1_allies_machinegunner` | Special Forces | 557 | 1,085 | 741 | 1.33× | Hot |
| `ra1_allies_tanya` | Commando | 3,000 | 1,667 | 2,515 | 0.84× | Near; C4 and hero utility are not fully represented |

Mechanic, Medic, and Spy use ability-priced Support classification and are excluded from combat-price conclusions.

### Soviets

| Actor | Class | Cost | Effective DPS | Formula price | Ratio | Finding |
|---|---|---:|---:|---:|---:|---|
| `ra1_soviets_rifleinfantry` | Scout | 100 | 32 | 92 | 0.92× | Near |
| `ra1_soviets_ak47conscript` | Scout | 200 | 98 | 256 | 1.28× | Hot |
| `ra1_soviets_grenadier` | Grenadier | 200 | 350 | 440 | 2.20× | **Severely hot** |
| `ra1_soviets_molotovconscript` | Grenadier verifier | 200 | 280 | 489 | 2.45× | **Verifier identity is broken under its live K/stats** |
| `ra1_soviets_rocketsoldier` | Rocket Trooper | 300 | 350 | 438 | 1.46× | Hot |
| `ra1_soviets_firerocketsoldier` | Rocket Trooper | 400 | 528 | 686 | 1.72× | Hot |
| `ra1_soviets_flamethrower` | Heavy Infantry | 200 | 333 | 309 | 1.55× | Hot |
| `ra1_soviets_shocktrooper` | Heavy Infantry | 600 | 500 | 360 | 0.60× | Cold |
| `ra1_soviets_zapper` | Heavy Infantry | 1,200 | 1,000 | 580 | 0.48× | Cold; intended verifier relationship is not satisfied |
| `ra1_soviets_attackdog` | Melee | 200 | extractor reads 0 | 71 | 0.35× | Dog-jaw damage is not captured by the current priced-warhead extractor |
| `ra1_soviets_cyberdog` | Melee | 1,000 | extractor reads 0 | 204 | 0.20× | Same extraction limitation; manual combat test required |
| `ra1_soviets_commissar` | Pure Sniper | 700 | 375 | 657 | 0.94× | Near |
| `ra1_soviets_dragunovantimaterialsniper` | Heavy Sniper | 422 | 5,150 | 2,158 | 5.11× | **Severely hot** |
| `ra1_soviets_mortarsoldier` | Mortar | 500 | 256 | 293 | 0.59× | Cold |
| `ra1_soviets_volkov` | Commando | 10,000 | 3,250 | 9,803 | 0.98× | Near |

Engineer is ability-priced Support and is excluded from combat-price conclusions.

### Japan

| Actor | Class | Cost | Effective DPS | Formula price | Ratio | Finding |
|---|---|---:|---:|---:|---:|---|
| `japan_imperialscoutsman` | Special Forces | 200 | 240 | 200 | 1.00× | Exact anchor |
| `japan_japaneseflamethrower` | Heavy Infantry | 200 | 459 | 276 | 1.38× | Hot |
| `japan_tankbuster` | Heavy Infantry | 400 | 281 | 450 | 1.12× | Near |
| `japan_samurai` | Melee | 300 | 375 | 328 | 1.09× | Near |
| `japan_archermaiden` | Archer | 500 | 300 | 687 | 1.37× | Hot |
| `japan_rocketangel` | Flying Infantry | 900 | 630 | 405 | 0.45× | Cold; flying-infantry formula is explicitly provisional |
| `japan_exorcist` | Commando | 3,000 | 1,200 | 2,123 | 0.71× | Cold; activated ability value is only approximated by K |

## Dune 2000 / Dune Universe

Atreides currently has no infantry actors. Harkonnen uses the shared `light_inf`, `trooper`, and Engineer actors.

### Shared / Harkonnen

| Actor | Class | Cost | Effective DPS | Formula price | Ratio | Finding |
|---|---|---:|---:|---:|---:|---|
| `light_inf` | Scout | 150 | 68 | 168 | 1.12× | Near |
| `trooper` | Rocket Trooper | 300 | 328 | 411 | 1.37× | Hot |

Engineer is ability-priced Support.

### Ixian

| Actor | Class | Cost | Effective DPS | Formula price | Ratio | Finding |
|---|---|---:|---:|---:|---:|---|
| `ixian_lightinfantry` | Scout | 150 | 85 | 170 | 1.13× | Near |
| `ixian_rockettrooper` | Rocket Trooper | 300 | 328 | 411 | 1.37× | Hot |
| `ixian_twinrockettrooper` | Rocket Trooper | 600 | 328 | 678 | 1.13× | Near; same extracted DPS as the cheaper single trooper, with extra value coming from HP/range |
| `heavy_inf.ixian` | Melee | 400 | 406 | 533 | 1.33× | Hot |
| `ixian_shockinfantry` | Heavy Infantry | 500 | 500 | 483 | 0.97× | Near |
| `ixian_storminfantry` | Heavy Infantry | 800 | 409 | 506 | 0.63× | Cold |

### Ordos

| Actor | Class | Cost | Effective DPS | Formula price | Ratio | Finding |
|---|---|---:|---:|---:|---:|---|
| `ordos_lightinfantry` | Scout | 120 | 50 | 120 | 1.00× | Exact |
| `ordos_rockettrooper` | Rocket Trooper | 300 | 328 | 411 | 1.37× | Hot |
| `ordos_antiairtrooper` | Rocket Trooper | 450 | 350 | 652 | 1.45× | Hot |
| `ordos_chemicaltrooper` | Heavy Infantry | 400 | 300 | 347 | 0.87× | Near |
| `ordos_contaminator` | Melee | 500 | 375 | 692 | 1.38× | Hot |
| `ordos_mortartrooper` | Mortar | 600 | 500 | 413 | 0.69× | Cold |
| `ordos_facedancer` | Commando | 5,000 | 2,000 | 3,985 | 0.80× | Near; infiltration utility is only approximated |

`ordos_leech` is stored in the infantry ledger but classified as `ScoutVehicle`; it has no infantry Formula-V2 class assignment and was not forced into an infantry formula.

## Priority findings

1. **Stealth Soldier was the first repair target and was corrected on 2026-08-03.** Its cloak and EMP remain represented by `K = 1.5`; its pinned cost and role were preserved.
2. **TD Nod Laser Trooper is also severely hot.** Its 3,110 effective DPS produces a formula price around 2,018 versus cost 750. It should be reviewed alongside the Stealth Soldier because both are Nod Special Forces and both appear affected by the same multi-warhead-era tuning.
3. **Several other credible combat outliers exist:** TD GDI EMP Grenadier, RA1 Soviet Dragunov Anti-Material Sniper, TD GDI Grenadier, RA1 Soviet Grenadier, and TD Nod Chemical Rocket Soldier.
4. **Some apparent cold units are extractor limitations or ability-heavy units.** Havoc, dogs, Laser Commando, support units, and some commandos must not be mechanically restatted from the zero/low extracted DPS rows.
5. **The broad infantry rebalance remains unfinished.** Existing per-class proposal documents already record many of these mismatches. A green YAML-to-ledger drift audit only proves that the ledger matches live YAML; it does not prove that live values match the Formula-V2 target proposals.

## Recommended correction order

1. Run controlled in-game burst and time-to-kill tests for the corrected `td_nod_stealthsoldier`; Formula V2 is a pricing model, not runtime proof.
2. Recalculate `td_nod_lasertrooper` inside the Special Forces class while preserving its role and pinned cost unless a cost change is explicitly approved.
3. Re-run the Special Forces proposal and its baseline/verifier identity checks.
4. Audit the other severe hot rows by class, starting with Grenadier and Heavy Sniper.

## Expanded vehicle and aircraft scan

The follow-up scan covered active RA1, TD, and Dune buildable vehicles and aircraft. Vehicle results use implemented Formula-V2 anchors where the actor has a credible class mapping. Aircraft are compared only by extracted damage profile because `class_anchors.json` currently has no Fighter, Bomber, Helicopter, or general Aircraft formula.

### Second damage outlier: Ixian Ix Missile Tank

`ixian_ixmissiletank` is the strongest credible non-infantry damage-profile outlier:

| Field | Live value |
|---|---:|
| Cost | 2,250 |
| HP | 50,000 |
| Speed | 50 |
| Range | 10,052 |
| Main warheads | Grenade 8,000 + Medium Flame 8,000 + Heavy Missile 8,000 |
| Total damage per shot | 24,000 |
| Weapon `ReloadDelay` | 5 ticks |
| Short-window DPS | 4,800 |
| Ammo | 10 shots |
| Ammo reload | 1 shot every 25 ticks, reset on fire |

Its extracted DPS-per-credit is about **5.97× the median of the currently tagged Fire Support vehicles** in these factions. The `FireSupport` classification is intentional: the `^MissileVehicleTemplate` inheritance describes its implementation and weapon behavior, but does not change its intended balance role.

As a Fire Support unit, its short-window 4,800 DPS must be evaluated together with its unusually slow, fragile chassis and its magazine cycle. The unresolved problem is that Formula V2 prices continuous DPS but does not currently price `AmmoPool` burst damage followed by `ReloadAmmoPool` downtime. The unit can release **240,000 main-warhead damage in its initial ten-shot magazine** before armor modifiers. That burst is the actual balance concern.

### Other raw damage flags

- `ra1_soviets_su57attackbomber`: approximately 5,628 extracted attack DPS and 3.44× the Bomber group median damage-per-credit. This is not a formula verdict because bomber sortie, ammo, rearm, speed, and exposure time are not modeled yet.
- `ordos_airmine`: approximately 2,500 extracted DPS at cost 500, or 9.17× the Bomber group median damage-per-credit. It is a mine/special actor rather than a normal bomber and needs role-specific testing.
- `ra1_allies_reconranger`: approximately 521 DPS at cost 500, or 3.39× the Support Vehicle group median damage-per-credit. No Support Vehicle anchor exists, so this is a comparison flag only.

### Recommendations from the expanded scan

1. **Keep the Fire Support classification:** treat the Ix Missile Tank's rapid missile magazine as its intended battlefield role, not as a classification error.
2. **Add ammo-cycle pricing:** Formula V2 should expose initial-magazine damage, burst duration, empty-magazine downtime, and long-run sustained DPS. Do not disguise magazine behavior as a normal continuous `ReloadDelay` weapon.
3. **Preserve the Ix Missile Tank's rapid-salvo identity:** if runtime testing confirms excessive burst, keep the 5-tick launch cadence and reduce magazine size or per-shot total damage. Increasing ordinary `ReloadDelay` would erase its distinctive weapon feel.
4. **Test two windows:** measure damage over the first 50 ticks and over a long interval that includes a full empty-and-reload cycle. Compare it with similarly priced Fire Support units against infantry, vehicles, tanks, buildings, and air.
5. **Do not mechanically retune aircraft yet:** first establish Fighter, Bomber, and Helicopter anchors that account for ammo, rearm, sortie time, and survivability. Until then, the Su-57 and Ordos Air Mine are high-priority test cases, not formula-approved changes.
