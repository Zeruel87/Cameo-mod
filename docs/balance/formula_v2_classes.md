# Formula V2 — per-class working logs

The per-class validation runs and proposals behind [`../design/FORMULA_V2.md`](../design/FORMULA_V2.md),
which is the law. These are the WORKING RECORDS: what each class's anchor was, what the
formula priced its members at, and what was decided. They were four separate files until
2026-08-23.

⚠ **Numbers here are as-measured on the date of each section and are NOT re-measured by any
audit.** For a current price, re-run `tools/balance/fit_class.py` / `propose_class_rebalance.py`.
Signed-off class anchors today: **0** — see `docs/audit/doc_claims.yaml` (`signed_off_class_anchors`),
so nothing below is final.

Class anchors themselves live in [`anchor_decisions_log.md`](anchor_decisions_log.md) and
`class_anchors.json`.

---

## Scout infantry

_Merged 2026-08-23 from `docs/balance/formula_v2_scout.md`, unedited below this line._

Anchor spec: HP=20000, Speed=60, Range=5000, eff-DPS=60, Cost=100

| actor | faction | HP | spd | rng | cost | dmg | burst | rl | FP% | wc | eff DPS | formula price | Δ | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `naxis_naxiriflesoldier` | naxis | 29000 | 52 | 5495 | 100 | 6000 | 1 | 75 | 70 | 0.75 | 42.0 | 100 | +0 | anchor-ish baseline |
| `forgotten_mutantsoldier` | forgotten | 40000 | 59 | 5000 | 250 | 8000 | 1 | 50 | 100 | 0.75 | 120.0 | 247 | -3 | verifier |
| `asianalliance_asianmilitia` | asianalliance | 24000 | 57 | 4570 | 110 | 6000 | 1 | 50 | 70 | 0.75 | 63.0 | 106 | -4 |  |
| `ixian_lightinfantry` | ixian | 35000 | 55 | 4530 | 150 | 4000 | 1 | 20 | 54 | 0.75 | 81.0 | 154 | +4 |  |
| `ordos_lightinfantry` | ordos | 37000 | 51 | 4500 | 150 | 4000 | 1 | 20 | 55 | 0.75 | 82.5 | 153 | +3 |  |
| `light_inf` | d2k_shared | 36000 | 54 | 4510 | 150 | 4000 | 1 | 20 | 53 | 0.75 | 79.5 | 153 | +3 |  |
| `latinsyndicate_latinmilitia` | latinsyndicate | 25000 | 56 | 4520 | 160 | 2000 | 3 | 22 | 60 | 0.75 | 122.7 | 165 | +5 |  |
| `naxis_naxiriflerecruit` | naxis | 20000 | 53 | 5485 | 75 | 8000 | 1 | 100 | 81 | 0.75 | 48.6 | 87 | +12 |  |
| `ra1_soviets_ak47conscript` | ra1_soviets | 44000 | 71 | 4505 | 200 | 2000 | 3 | 11 | 20 | 0.875 | 95.5 | 241 | +41 |  |
| `ra2_allies_gi` | ra2_allies | 50000 | 48 | 4515 | 200 | 2000 | 3 | 15 | 33 | 0.875 | 115.5 | 229 | +29 |  |
| `ra2_soviets_conscript` | ra2_soviets | 26000 | 58 | 4525 | 100 | 2000 | 1 | 18 | 63 | 0.75 | 52.5 | 101 | +1 |  |
| `tkm_rifleman` | tkm | 32000 | 60 | 5500 | 120 | 6000 | 1 | 75 | 73 | 0.75 | 43.8 | 120 | -0 |  |
| `tkm_trooper` | tkm | 33000 | 61 | 5490 | 220 | 2000 | 5 | 31 | 40 | 0.875 | 112.9 | 225 | +5 |  |
| `td_gdi_minigunner` | td_gdi | 31000 | 63 | 4750 | 100 | 2000 | 4 | 50 | 30 | 0.75 | 36.0 | 102 | +2 |  |
| `td_nod_minigunner` | td_nod | 30000 | 66 | 4535 | 100 | 2000 | 4 | 50 | 27 | 0.75 | 32.4 | 96 | -4 |  |
| `ra1_allies_rifleinfantry` | ra1_allies | 28000 | 50 | 5250 | 100 | 2000 | 3 | 50 | 50 | 0.75 | 45.0 | 97 | -3 |  |
| `ra1_soviets_rifleinfantry` | ra1_soviets | 34000 | 49 | 4600 | 100 | 2000 | 3 | 50 | 55 | 0.75 | 49.5 | 106 | +6 |  |

### Uniqueness check

> **Note:** This check was run with the original 4-field uniqueness
> definition (HP, Speed, Range, effective DPS). The binding rule was
> later expanded to 5 fields in `FORMULA_V2.md` §3d (2026-07-21):
> HP, Speed, effective damage per shot, raw ReloadDelay, Range —
> checked separately. Re-run with the 5-field definition before
> applying.

- All uniqueness checks passed (HP, Speed, Range, effective DPS).

### Out-of-scope units (maintainer decisions applied)

- `forgotten_mutant` → reclassified to closecombat infantry (was range 3132).
- `schwarzermond_lunarsoldier` → already moved to special forces; excluded from this scout pass.
- `naxis_alien` → civilian variant spawned from asteroids/dead aircraft; set Cost to **1000** (stats unchanged).
- Spies, civilian Naxis variants, casters, and units priced outside the scout envelope remain for a future pass.
- Raw Damage values are kept in 2000-step increments; effective-DPS uniqueness is enforced via per-actor FirepowerMultiplier.

### Required YAML edits (per unit)

- `naxis_naxiriflesoldier`: HP 29000, Speed 52, Range 5495, weapon Damage 6000, ReloadDelay 75, Burst 1, FirepowerMultiplier@NAXISNAXIRIFLESOLDIER 70
- `forgotten_mutantsoldier`: HP 40000, Speed 59, Range 5000, weapon Damage 8000, ReloadDelay 50, Burst 1, FirepowerMultiplier@FORGOTTENMUTANTSOLDIER 100
- `asianalliance_asianmilitia`: HP 24000, Speed 57, Range 4570, weapon Damage 6000, ReloadDelay 50, Burst 1, FirepowerMultiplier@ASIANALLIANCEASIANMILITIA 70
- `ixian_lightinfantry`: HP 35000, Speed 55, Range 4530, weapon Damage 4000, ReloadDelay 20, Burst 1, FirepowerMultiplier@IXIANLIGHTINFANTRY 54
- `ordos_lightinfantry`: HP 37000, Speed 51, Range 4500, weapon Damage 4000, ReloadDelay 20, Burst 1, FirepowerMultiplier@ORDOSLIGHTINFANTRY 55
- `light_inf`: HP 36000, Speed 54, Range 4510, weapon Damage 4000, ReloadDelay 20, Burst 1, FirepowerMultiplier@LIGHTINF 53
- `latinsyndicate_latinmilitia`: HP 25000, Speed 56, Range 4520, weapon Damage 2000, ReloadDelay 22, Burst 3, FirepowerMultiplier@LATINSYNDICATELATINMILITIA 60
- `naxis_naxiriflerecruit`: HP 20000, Speed 53, Range 5485, weapon Damage 8000, ReloadDelay 100, Burst 1, FirepowerMultiplier@NAXISNAXIRIFLERECRUIT 81, formula price delta +12 (informational; cost pinned at 75)
- `ra1_soviets_ak47conscript`: HP 44000, Speed 71, Range 4505, weapon Damage 2000, ReloadDelay 11, Burst 3, FirepowerMultiplier@RA1SOVIETSAK47CONSCRIPT 20, formula price delta +41 (informational; cost pinned at 200)
- `ra2_allies_gi`: HP 50000, Speed 48, Range 4515, weapon Damage 2000, ReloadDelay 15, Burst 3, FirepowerMultiplier@RA2ALLIESGI 33, formula price delta +29 (informational; cost pinned at 200)
- `ra2_soviets_conscript`: HP 26000, Speed 58, Range 4525, weapon Damage 2000, ReloadDelay 18, Burst 1, FirepowerMultiplier@RA2SOVIETSCONSCRIPT 63
- `tkm_rifleman`: HP 32000, Speed 60, Range 5500, weapon Damage 6000, ReloadDelay 75, Burst 1, FirepowerMultiplier@TKMRIFLEMAN 73
- `tkm_trooper`: HP 33000, Speed 61, Range 5490, weapon Damage 2000, ReloadDelay 31, Burst 5, FirepowerMultiplier@TKMTROOPER 40
- `td_gdi_minigunner`: HP 31000, Speed 63, Range 4750, weapon Damage 2000, ReloadDelay 50, Burst 4, FirepowerMultiplier@TDGDIMINIGUNNER 30
- `td_nod_minigunner`: HP 30000, Speed 66, Range 4535, weapon Damage 2000, ReloadDelay 50, Burst 4, FirepowerMultiplier@TDNODMINIGUNNER 27
- `ra1_allies_rifleinfantry`: HP 28000, Speed 50, Range 5250, weapon Damage 2000, ReloadDelay 50, Burst 3, FirepowerMultiplier@RA1ALLIESRIFLEINFANTRY 50
- `ra1_soviets_rifleinfantry`: HP 34000, Speed 49, Range 4600, weapon Damage 2000, ReloadDelay 50, Burst 3, FirepowerMultiplier@RA1SOVIETSRIFLEINFANTRY 55, formula price delta +6 (informational; cost pinned at 100)

---

## Close-combat infantry

_Merged 2026-08-23 from `docs/balance/formula_v2_closecombat.md`, unedited below this line._

_The maintainer's question: units with less range than the scout band
allows need a new shotgunner/close-range class between melee and heavy
infantry. Problem analysis + solution proposal for review. Nothing
applied._

### 1. The problem, precisely

1. The scout range band (4500–5500) is correct for scouts — but it
   FORCED true close-range fighters upward (the forgotten_mutant went
   3132 → 4500 in proposal v2, a +44% reach buff that changes its
   combat identity from brawler to rifleman).
2. A ±10% band around any single anchor covers only ~20% of range
   space. The infantry ladder currently anchors melee (~1500–2000
   contact weapons) and scout (5000) — leaving everything between
   ~1700 and ~4400 classless. A survey of base-weapon ranges found
   **60 infantry units in that hole**.
3. Under the WRONG class anchor the formula misprices structurally:
   a low range ratio collapses Q, so the solver hands the unit huge
   DPS/HP for its cost — the class formula only works when the class
   is right.

### 2. What actually lives in the hole (survey 2026-07-19)

The 60 units cluster into archetypes — most belong to OTHER classes
and leave a clean shotgunner core behind:

| archetype | examples | verdict |
|---|---|---|
| Commando/hero (C4, attach kills, rng 2000) | Tanya(s), TD commandos, Havoc, SEALs, spetsnaz, shadow team, black widow, ghoststalker | hero/commando class (own anchor later) — NOT close-combat |
| Attack dogs | ra1/ra2 dogs, cyberdog | own mini-archetype (leap mechanic), later |
| Flame/chem | td_nod flamethrower 2085, chem warrior 3414, chemspray 3183, japan flamer 3603, firebat 3400, thermonaut 3204 | mostly ALREADY ^HeavyInfantryTemplate — stay heavy; maintainer may split a flame class later |
| Utility/economy | engineers (4303), crazyivan, saboteur, contaminator, leech, slaveoverseer, named civilians | support/special class (below) or their own thing |
| **THE SHOTGUN/SMG CORE** | **td_gdi_shotgunner 3125, ts_gdi_riottrooper 4002 (TSShotgun), futuretech_enforcer 3000 + shotgundroid 4110, forgotten_runnershotgal 3112 + mutant 3132 (dual pistols), naxis_sssoldier 4000 (MP40), fremen_creep 3072, heavy_inf.ixian 3800, ts_gdi/nod_lightinfantry 4062** | **the new class** |
| Casters | zerg_defiler, kerrigan, teslatrooper? | defiler → SNIPER transform (maintainer verdict); others case-by-case |

### 3. The proposed class: `closecombat` (shotgunners & SMGs)

**Ladder position** (maintainer: between melee and heavy):
melee (contact) < **closecombat 3150–3850** < scout 4500–5500;
tougher per cost than scouts (they must survive the approach), less
specialist than heavies.

**Anchor proposal (round numbers, O=P=Q=C₀ by construction):**

| | HP | Speed | Range | Damage | Reload | WC | eff DPS | Cost |
|---|---|---|---|---|---|---|---|---|
| baseline | 40000 | 55 | **3500** | 8000 | 50 | SA 0.75 | 120 | **200** |
| verifier (2×/2×) | 80000 | 55 | 3500 | 16000 | 50 | SA 0.75 | 240 | 500 |

- REV (maintainer 2026-07-19): band widened to the CONTIGUOUS
  [2500, 4500) — anchor stays 3500 (the exact center). No unit can
  fall between melee and scout anymore; within the class the price
  gradient binds (cheap → 2500 end, pricey → 4500 end). Original
  cluster needs almost no range moves at all now (shotgunner 3125,
  mutant 3132, shotgundroid 4110 all already inside).
- Vs the scout baseline: 2× HP and 2× DPS for 2× cost at −30% range
  and −5 speed — the archetype IS the formula trade.
- **Baseline unit pick: `td_gdi_shotgunner`** — THE archetypal
  shotgunner, already exactly cost 200 (classic-price law holds).
- Verifier pick: maintainer's call — `ts_nod_shotguncommando` is v
  wrong tier (3000); suggest converting `ts_gdi_riottrooper` (700)
  down to 500 as the verifier, or a Forgotten shotgun variant.
- Class rules inherit the law book (10-step ranges, damage 2000-steps,
  bands, envelope 100–500 = 50–250% of 200, no-air, ground autotarget,
  burst/pellets as flavor with unit-named FP-mult). Shotgun pellet
  spread stays a weapon-flavor property, not a formula input (like
  burst).

**Template mechanics:** new `^CloseCombatInfantryTemplate` in
defaults.yaml mirroring ^ScoutInfantryTemplate (armor class, its own
Buff knob pair for §5b live tuning, ^AutoTargetGroundAssaultMove
default); members migrate off ^ScoutInfantryTemplate /
^HeavyInfantryTemplate one at a time with the standard conversion
checklist (FORMULA_V2 §6).

### 4. The second new class from the maintainer's verdicts: `support`

Spies (raspy, ra2spy, spyfutu), Yuri mind-control units, CABAL
hackers — units whose value is an ABILITY, not DPS. New
`^SupportInfantryTemplate`; pricing needs an ability-value table
(infiltration, mind control, hack) because the combat formula has no
input for them — proposal: maintainer prices the ability tiers once
(like the old Special column, but per-ability), formula prices the
chassis (HP/speed), price = chassis + ability. To be designed with
the maintainer before any conversion.

### 5. Sequencing & open maintainer decisions

1. Finish the scout conversions (13 queued) — unchanged.
2. `closecombat`: approve anchor spec + baseline (td_gdi_shotgunner)
   + verifier pick + member list (§2 core).
3. `sniper`: transform zerg_defiler per verdict (stat proposal to
   follow once the sniper anchor exists — ^SniperInfantryTemplate
   already exists as a template).
4. `support`: ability-value table workshop with the maintainer.
5. Melee + heavy anchors: after closecombat lands, same survey method
   (melee r₀ ~1500 band 1350–1650; heavy needs its own survey — many
   flame units already live there).
6. Civilians (alien/undead/naxis_conehead2): parked undecided per the
   maintainer — they can slot into scout/closecombat/melee/heavy once
   the ladder is complete.

---

### CONVERSION LOG — closecombat class (LIVE 2026-07-19)

#### Anchor established (maintainer spec, boot-pending)

- **BASELINE `td_gdi_shotgunner`**: 50000 HP / 75 Speed / 3500 Range /
  cost 200. Weapon `td_gdi_shotgunner_shotgun`: SmallArms 2000 +
  Chaingun 2000 per shot (WC 0.875), **burst 5 / BurstDelays 0** (one
  shotgun blast), Inaccuracy 800 (= 4× the Chaingun's 200), ReloadDelay
  75, **SoundVolume 0.2** (= 1/burst so 5 simultaneous shots aren't
  deafening), no-air. Effective DPS = (2000+2000)·5/75·0.875 = 233.33.
  → **O = P = Q = price = 200.00 EXACT.**
- **VERIFIER `asianalliance_fanatic`**: 2× HP (100000) + 2× DPS via
  **DOUBLE BURSTS (burst 10, not double damage)** @ 250% cost = 500.
  SoundVolume 0.1. → O=300 P=400 Q=800 **price=500.00 EXACT** (identity
  holds — doubling bursts doubles DPS just like doubling damage).
  Upgrade/elite tiers dedicated (burst 13/16) per the pair law.
- **MEMBER `naxis_sssoldier`**: 60000 HP / 55 Speed / 4000 Range,
  SMG `naxis_sssoldier_smg` (SA+CG, burst 10, bd 0, no-air) + elite
  pair. **Tier 3 (academy) → tech_tier 0.75** → priced 243 → **cost
  240** (the tech discount: a T3 unit is cheaper per stat because the
  academy is the entry cost). Was 375/30000/MeleeTemplate.

#### Class laws (in addition to the universal ones)

- ALL closecombat weapons use **SmallArms + Chaingun** (WC 0.875);
  per-shot damage = the two warheads SUMMED (both equal), in 2000-steps;
  each carries its % warhead (1% per 2000).
- **BurstDelays 0** (rapid blast); **SoundVolume = 1/burst** (LAW — a
  simultaneous multi-shot burst must be volume-scaled or it deafens).
- **Tech tier factor**: T1 = 1.0, T3 = 0.75 (multiplies O/P/Q, so a
  higher-tech unit is cheaper per stat). Determined by the deepest
  tech-building prerequisite.
- `^CloseCombatInfantryTemplate` (Plate armor, ground-only autotarget,
  own neutral Buff knob pair) — the class is born normalized (no bake).

Lessons:
9. Verifier via 2× BURSTS instead of 2× damage gives the identical
   2.5× identity AND a cleaner weapon (same per-shot feel, faster
   cadence) — the maintainer's preferred pattern for burst weapons.
10. SoundVolume scales inversely with burst count (1/burst) — required
    whenever BurstDelays 0 fires many shots on one tick.
11. Tech tier belongs in the price: a T3 unit prices at 0.75× the T1
    formula, so it can carry stronger stats for the same cost.

---

## MBT (vehicles)

_Merged 2026-08-23 from `docs/balance/formula_v2_mbt.md`, unedited below this line._

anchor: `naxis_tiger` (cost0 800, O0 946.79, P0 1093.58, Q0 1387.16)

| unit | cost (actual) | class-formula price | delta |
|---|---|---|---|
| `asianalliance_lynxtank` | 850 | 761 | -11% ⚠ |
| `naxis_assault` | 900 | 4452 | +395% ❗ |
| `cabal_tarantula` | 1000 | 1065 | +7% |
| `cabal_widow` | 3500 | 8264 | +136% ❗ |
| `combat_tank.atreides` | 600 | 1018 | +70% ❗ |
| `combat_tank.harkonnen` | 600 | 476 | -21% ⚠ |
| `forgotten_rattytank` | 600 | 718 | +20% ⚠ |
| `futuretech_guardiantank` | 850 | 906 | +7% |
| `ixian_heavykodatank` | 1100 | 1411 | +28% ⚠ |
| `ixian_kodatank` | 800 | 952 | +19% ⚠ |
| `ixian_mongoose` | 1300 | 771 | -41% ❗ |
| `japan_chihaheavytank` | 1200 | 1077 | -10% ⚠ |
| `japan_igomediumtank` | 800 | 805 | +1% |
| `latinsyndicate_smokertank` | 1800 | 1958 | +9% |
| `naxis_kingtigerheavytank` | 2000 | 2021 | +1% |
| `oldqtnk.steel` | 2400 | 3109 | +30% ⚠ |
| `ordos_combatautoguntank` | 1500 | 916 | -39% ❗ |
| `ordos_heavycombattank` | 950 | 1063 | +12% ⚠ |
| `protoss_dragoon` | 1200 | 438 | -63% ❗ |
| `ptnk.asian` | 2400 | 3485 | +45% ❗ |
| `ra1_allies_alliedcybertank` | 1300 | 1381 | +6% |
| `ra1_allies_alliedmediumtank` | 700 | 698 | -0% |
| `ra1_allies_alliedtigerheavytank` | 1300 | 1381 | +6% |
| `ra1_soviets_hammertank` | 1500 | 2048 | +37% ❗ |
| `ra1_soviets_heavytank` | 1000 | 1287 | +29% ⚠ |
| `ra1_soviets_kotinnucleartank` | 1800 | 2396 | +33% ❗ |
| `ra2_allies_grizzlytank` | 750 | 1046 | +39% ❗ |
| `ra2_soviets_rhinoheavytank` | 850 | 989 | +16% ⚠ |
| `schwarzermond_lunartiger` | 950 | 914 | -4% |
| `steelconsortium_mako` | 900 | 861 | -4% |
| `steelconsortium_quantumtank` | 1600 | 1350 | -16% ⚠ |
| `td_gdi_battletank` | 900 | 911 | +1% |
| `td_gdi_predatortank` | 1250 | 1282 | +3% |
| `terran_matador` | 1700.0 | (no combat stats) | |
| `naxis_tiger` | 800 | 800 | +0% |
| `tkm_abrams` | 1000 | 1046 | +5% |
| `tkm_t72m` | 900 | 1287 | +43% ❗ |
| `tkm_technicaltank` | 700 | 715 | +2% |
| `tkm_trenchtank` | 2500 | 4264 | +71% ❗ |
| `ts_gdi_titan` | 950 | 1049 | +10% ⚠ |
| `ts_gdi_titanmkii` | 1600 | 1816 | +13% ⚠ |
| `ts_nod_ticktank` | 800.0 | (no combat stats) | |

---

## Line breaker (vehicles)

_Merged 2026-08-23 from `docs/balance/formula_v2_line_breaker.md`, unedited below this line._

anchor: `td_nod_flametank` (cost0 800, O0 1403.88, P0 1226.56, Q0 1450.49)

| unit | cost (actual) | class-formula price | delta |
|---|---|---|---|
| `asianalliance_asianflametank` | 1300 | 882 | -32% ❗ |
| `asianalliance_warturtle` | 5000 | 567 | -89% ❗ |
| `cabal_beholder` | 2500 | 856 | -66% ❗ |
| `cobra.steel` | 3600 | 2515 | -30% ❗ |
| `forgotten_closhtank` | 1000 | 1266 | +27% ⚠ |
| `forgotten_flametank` | 1300 | 1199 | -8% |
| `forgotten_thumperbus` | 5200 | 4937 | -5% |
| `futuretech_plasmastrider` | 2600 | 3035 | +17% ⚠ |
| `latinsyndicate_carteltruck` | 6000 | 2502 | -58% ❗ |
| `latinsyndicate_tortugatank` | 3000 | 1728 | -42% ❗ |
| `naxis_oldtank` | 2000 | 1094 | -45% ❗ |
| `ordos_heavyautoguntank` | 2800 | 1587 | -43% ❗ |
| `protoss_archon` | 5600 | 5415 | -3% |
| `ra2_allies_battlefortress` | 4000 | 1254 | -69% ❗ |
| `ra2_allies_battlefortress_chrono` | 4000 | 1254 | -69% ❗ |
| `ra2_allies_battlefortress_empty` | 4000 | 1254 | -69% ❗ |
| `steelconsortium_megalodon` | 4600 | 1581 | -66% ❗ |
| `steelconsortium_poseidontank` | 4000 | 1719 | -57% ❗ |
| `td_gdi_assaultapc` | 4500 | 1131 | -75% ❗ |
| `td_nod_flametank` | 800 | 1000 | +25% ⚠ |
| `td_nod_flametankmkii` | 1300 | 2466 | +90% ❗ |
| `tkm_battlebus` | 1250 | -442 | -135% ❗ |
| `ts_gdi_disruptor` | 2400 | 391 | -84% ❗ |
| `ts_gdi_mobileemp` | 1400 | 1207 | -14% ⚠ |
| `ts_nod_devilstongue` | 1150 | 1746 | +52% ❗ |
| `wc2_humans_demolitionsquad` | 800.0 | (no combat stats) | |
| `wc2_humans_paladin` | 1600.0 | (no combat stats) | |
| `wc2_humans_warcraft3knight` | 2200.0 | (no combat stats) | |
| `wc2_orcs_goblinsappers` | 800.0 | (no combat stats) | |
| `wc2_orcs_ogremage` | 1800.0 | (no combat stats) | |
