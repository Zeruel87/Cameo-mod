# Class-anchor decisions log (maintainer-confirmed, one class at a time)

_Running record of the collaborative baseline+verifier definition (started 2026-07-25). Each class
is LOCKED here once the maintainer confirms; then `fit_class` + sign-off + `defaults.yaml` template
work follow. Fixed MBT anchor pivot: **Tiger `naxis_tiger` = 100000 HP / 100 spd / **5500 rng** / 10000
dmg @ 50 reload / cost0 800** (DPS 200). (Range bumped 5000→5500 on 2026-07-26 to complete the range
ladder — see the RANGE LADDER section.)_

---

# ★★★ FINAL LOCKED — VEHICLE LADDER + CLASSES (2026-07-28) ★★★
_This section SUPERSEDES all the iterative discussion below. A fresh session should read THIS as the
authoritative final state of the vehicle overhaul. Everything below the `═══` divider is iteration
history / per-class rationale (still valid as reasoning, but the numbers here are the final ones)._

## ★ LOCKED 2026-08-01 (maintainer-confirmed — THIS is the authoritative table; supersedes 2026-07-31 below)
Re-tuned 2026-08-01: **epic on top** (HP 4M / DPS 20k), **A+B spread capped at ≤2.0× (actual 1.92×)**,
**HP in clean 10k steps**, **DPS/Cost kept sane 0.5–1.5** (epic the sole 2.0 = 20k÷10k spec — the earlier
"unique ×0.05" experiment produced insane 3.4 values, reverted). All 5 base stats UNIQUE. Ordered by A+B ↓
(the maintainer's fixed order: epic, line_breaker, light_tank, mbt, high_tech, tank_destroyer, dreadnought,
scout, anti_air, artillery_tank, artillery, fire_support, missile_veh). Written to `class_anchors.json` spec.

| # | Class | Cost | HP | Spd | DPS | Range | HP/Cost | DPS/Cost | A=HP/C·Spd | B=DPS/C·Rng | A+B |
|--|--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | epic | 10000 | 4,000,000 | 60 | 20,000 | 8,500 | 400 | 2.00 | 24,000 | 17,000 | **41,000** |
| 2 | line_breaker | 1600 | 750,000 | 80 | 1,600 | 2,500 | 469 | 1.00 | 37,500 | 2,500 | 40,000 |
| 3 | light_tank | 400 | 100,000 | 125 | 200 | 5,000 | 250 | 0.50 | 31,250 | 2,500 | 33,750 |
| 4 | mbt | 800 | 240,000 | 95 | 600 | 5,500 | 300 | 0.75 | 28,500 | 4,125 | 32,625 |
| 5 | high_tech_tank | 2000 | 700,000 | 65 | 2,000 | 6,500 | 350 | 1.00 | 22,750 | 6,500 | 29,250 |
| 6 | tank_destroyer | 600 | 150,000 | 70 | 900 | 7,500 | 250 | 1.50 | 17,500 | 11,250 | 28,750 |
| 7 | dreadnought | 3000 | 1,150,000 | 50 | 3,750 | 7,000 | 383 | 1.25 | 19,167 | 8,750 | 27,917 |
| 8 | scout_vehicle | 300 | 30,000 | 200 | 450 | 4,500 | 100 | 1.50 | 20,000 | 6,750 | 26,750 |
| 9 | anti_air_vehicle | 1000 | 170,000 | 110 | 1,250 | 6,000 | 170 | 1.25 | 18,700 | 7,500 | 26,200 |
| 10 | artillery_tank | 700 | 140,000 | 85 | 525 | 12,000 | 200 | 0.75 | 17,000 | 9,000 | 26,000 |
| 11 | artillery | 500 | 60,000 | 75 | 500 | 15,000 | 120 | 1.00 | 9,000 | 15,000 | 24,000 |
| 12 | fire_support | 1400 | 120,000 | 90 | 2,100 | 10,000 | 86 | 1.50 | 7,714 | 15,000 | 22,714 |
| 13 | missile_vehicle | 1200 | 160,000 | 100 | 1,200 | 8,000 | 133 | 1.00 | 13,333 | 8,000 | 21,333 |

**⚠ DPS restat DEFERRED** to the cannon/weapon rebuild: current in-game
DPS is confounded by warhead-mixing + two calc bugs (fit_class skips FirepowerMultiplier; versus_shield
stale-preserved WC). HP/Speed/Cost/armor restat can proceed now. Armor targets (in class_anchors + templates):
missile Light, anti_air Medium, tank_destroyer Heavy, high_tech + dreadnought Superheavy (fix
`^HighTechTankTemplate` Medium→Superheavy + strip per-actor Armor overrides). Verifiers = 2×HP / 2×DPS /
2.5×cost of these baselines, matched tier+K.

═══════════════════════════════════════════════════════════════════════════════════════════════

## ⚠ REVISION 2026-07-31 (SUPERSEDED by the 2026-08-01 LOCKED table above)
The maintainer re-opened the ladder on 2026-07-31 with a batch of speed/ratio edits. **This table
SUPERSEDES the 2026-07-28 numbers below.** Costs unchanged. Ordered by composite Total = A+B (descending).

Edits applied (in order): MBT spd→95 (mid of LightTank 125 & HighTech 65), HP/Cost→300, DPS/Cost→0.75 ·
LightTank spd→125 · HighTech spd→65, HP/Cost→350, DPS/Cost→1.00 · Dreadnought DPS/Cost→1.25 ·
TankDestroyer DPS/Cost→1.50 · Artillery spd→75 · LineBreaker spd→80 · AntiAir spd→110 · MissileVehicle spd→100.

**⚠ interpretation flag:** "HP/Cost of the High Tech Tank to 1.0 and the dreadnought to 1.25 and Tank
Destroyer 1.5" was read as **DPS/Cost** (literal HP/Cost 1.0 is impossible, and a later message set HighTech
HP/Cost = 350). CONFIRM.

| # | Class | Cost | HP | Spd | DPS | Range | HP/Cost | DPS/Cost | A=HP/C·Spd | B=DPS/C·Rng | A+B |
|--|--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | LineBreaker | 1600 | 800,000 | 80 | 1,600 | 2,500 | 500 | 1.00 | 40,000 | 2,500 | **42,500** |
| 2 | LightTank | 400 | 100,000 | 125 | 200 | 5,000 | 250 | 0.50 | 31,250 | 2,500 | 33,750 |
| 3 | MBT | 800 | 240,000 | 95 | 600 | 5,500 | 300 | 0.75 | 28,500 | 4,125 | 32,625 |
| 4 | EpicVehicle | 10000 | 5,000,000 | 45 | 10,000 | 8,500 | 500 | 1.00 | 22,500 | 8,500 | 31,000 |
| 5 | HighTechTank | 2000 | 700,000 | 65 | 2,000 | 6,500 | 350 | 1.00 | 22,750 | 6,500 | 29,250 |
| 6 | Dreadnought | 3000 | 1,200,000 | 50 | 3,750 | 7,000 | 400 | 1.25 | 20,000 | 8,750 | 28,750 |
| 7 | Scout | 300 | 30,000 | 200 | 450 | 4,500 | 100 | 1.50 | 20,000 | 6,750 | 26,750 |
| 8 | ArtilleryTank | 700 | 140,000 | 85 | 525 | 12,000 | 200 | 0.75 | 17,000 | 9,000 | 26,000 |
| 9 | TankDestroyer | 600 | 150,000 | 55 | 900 | 7,500 | 250 | 1.50 | 13,750 | 11,250 | 25,000 |
| 10 | Artillery | 500 | 50,000 | 75 | 500 | 15,000 | 100 | 1.00 | 7,500 | 15,000 | 22,500 |
| 11 | FireSupport | 1400 | 105,000 | 90 | 2,100 | 10,000 | 75 | 1.50 | 6,750 | 15,000 | 21,750 |
| 12 | AntiAir | 1000 | 125,000 | 110 | 1,250 | 6,000 | 125 | 1.25 | 13,750 | 7,500 | 21,250 |
| 13 | MissileVehicle | 1200 | 120,000 | 100 | 1,200 | 8,000 | 100 | 1.00 | 10,000 | 8,000 | 18,000 |

All 5 base stats (HP/Spd/DPS/Range/Cost) remain UNIQUE per column ✓ (MBT HP 220k→240k).

**Baseline actor change (HighTechTank):** baseline RA1 Soviet Mammoth → **TD GDI Mammoth Tank**
(`td_gdi_mammothtank`); RA1 Soviet Mammoth (`ra1_soviets_mammothtank`) demoted to a **mid variant at
Spd 60 / Cost 2500** (more HP/Range/FP); **Siege Mammoth stays verifier**. ⚠ CONFIRM TD Mammoth (baseline)
and Siege Mammoth (RA1, verifier) share the same M-bucket + K or the 2.5× breaks —.

**Did it fix the earlier problems? — verdict:**
- ✅ FireSupport no longer efficiency-dominated by MissileVehicle (FS 21,750 > MV 18,000).
- ⚠ **LineBreaker re-introduced as top outlier**: spd 60→80 pushes A back to 40,000 → Total 42,500 (exactly
  what the earlier spd-60 drop had fixed). Only drawback = short 2,500 range. Accept as intentional slow
  super-juggernaut, OR pull speed to ~65–70.
- ⚠ **MissileVehicle is now the composite FLOOR** (18,000, below AntiAir & FireSupport) — pure flexer, no
  standout stat. Fine as identity but worth a small bump if it feels weak in play.

**latinsyndicate_burrito → Artillery** (maintainer 2026-07-31): long range but CANNOT hit air ⇒ Artillery, not MissileVehicle.

**⚠ PER-UNIT APPLICATION LAW (maintainer 2026-07-31 — do NOT misread the table):** the HP/Cost, DPS/Cost
and A/B aggregates exist ONLY to compare the 13 BASELINE actors against each other and set the class
center. They are **NOT per-unit targets** — members of a class must NOT all inherit the baseline's ratios;
the GOAL is **MORE uniqueness between units of a class**. Application model:
1. **2c sets ONLY the 13 baseline actors** (+ verifiers) to the exact table stats — the anchor per class.
2. The **balance FORMULA** takes its weights from that class baseline actor.
3. Each **member's stats** are then set by **SYNTHESIS** — an aggregate of **(a)** the OLD Cameo relative
   values, **(b)** every relative stat from the cross-game/mod data-mining, and **(c)** deep reasoning on
   where each unit sits relative to its class baseline. **RE-READ** the research before this pass:
   `docs/design/ORIGINAL_UNIT_STATS.md`, `docs/design/BALANCE_SYNTHESIS.md`, the extracted-mod ledgers,
   and memories +.
This is a **massive, compute-intensive pass** and is the real "apply the class" work — the per-member
spread, NOT a copy of the baseline ratios. `fit_class` then prices each synthesized member.

═══ (the 2026-07-28 table below is SUPERSEDED by the revision above; kept for baseline/verifier/armor refs) ═══

## The 13 vehicle classes — 2026-07-28 numbers (SUPERSEDED by REVISION above; armor/baseline/verifier cols still current)

| Class | HP | Spd | DPS | Range | Cost | HP/Cost | DPS/Cost | Armor | Baseline actor | Verifier (2×HP/2×DPS/2.5×cost, matched tier+K) |
|---|--:|--:|--:|--:|--:|--:|--:|---|---|---|
| Scout | 30,000 | 200 | 450 | 4,500 | 300 | 100 | 1.50 | Scout | `td_nod_buggy` | `terran_vulture` |
| LightTank | 100,000 | 120 | 200 | 5,000 | 400 | 250 | 0.50 | Medium | `ra1_allies_alliedlighttank` | `td_nod_lighttankmkii` |
| Artillery | 50,000 | 70 | 500 | 15,000 | 500 | 100 | 1.00 | Light | `ra1_allies_alliedartillery` | `naxis_brummbar` (T2, NOT V2 which is T3) |
| TankDestroyer | 150,000 | 55 | 600 | 7,500 | 600 | 250 | 1.00 | Heavy | `naxis_hetzer` | `ra2_allies_tankdestroyer` |
| ArtilleryTank | 140,000 | 85 | 525 | 12,000 | 700 | 200 | 0.75 | Medium | `ixian_ixcombatsiege` | `schwarzermond_lunargrille` |
| MBT | 220,000 | 100 | 480 | 5,500 | 800 | 275 | 0.60 | Heavy | `naxis_tiger` | `naxis_kingtigerheavytank` (T1/T1, K1.0, 800→2000 exact 2.5×) |
| AntiAir | 125,000 | 130 | 1,250 | 6,000 | 1,000 | 125 | 1.25 | Medium | `latinsyndicate_diablo` | `steelconsortium_barracuda` |
| **MissileVehicle** | 120,000 | 110 | 1,200 | 8,000 | 1,200 | 100 | 1.00 | Light | `ts_gdi_hovermlrs` | `terran_cyclone` (T1/1.0) |
| FireSupport | 105,000 | 90 | 2,100 | 10,000 | 1,400 | 75 | 1.50 | Light | `latinsyndicate_missiletruck` | **TBD at FS membership curation** (pure-ground T1/T2 K1.0; pool: forgotten_warriortank/protoss_reaver/eden_thorshammer) |
| LineBreaker | 800,000 | 60 | 1,600 | 2,500 | 1,600 | 500 | 1.00 | Superheavy | `td_nod_flametank` | `td_nod_flametankmkii` |
| HighTechTank | 600,000 | 80 | 1,500 | 6,500 | 2,000 | 300 | 0.75 | Superheavy | `ra1_soviets_mammothtank` | `ra1_soviets_siegemammothtank` |
| Dreadnought | 1,200,000 | 50 | 2,400 | 7,000 | 3,000 | 400 | 0.80 | Superheavy | `terran_warhound` | `ixian_neocymek` |
| **EpicVehicle** | 5,000,000 | 45 | 10,000 | 8,500 | 10,000 | 500 | 1.00 | Superheavy | `ra1_soviets_monstertank` | n/a (BuildLimit 1) |

**Verifier stats are DERIVED** from each baseline by 2×HP + 2×DPS + 2.5×cost, SAME speed/range, and MUST
match the baseline's **tier M-bucket AND K** (see the tier+K rule below). E.g. MBT verifier King Tiger =
440000 HP / 960 DPS / 2000 cost.

**Ladder derivation notes (final):**
- Speeds: LineBreaker↔HighTech SWAPPED (LineBreaker 80→**60** slow juggernaut; HighTech 60→**80**) — this
  cut LineBreaker's mobile-durability outlier. TankDestroyer 55, Dreadnought 50.
- FireSupport DPS **DOUBLED** 1050→2100 (DPS/Cost 1.5) so it's no longer efficiency-dominated by the
  MissileVehicle — now FS = fragile high-DPS long-range sniper, MV = balanced dual-purpose flexer.
- HP/Cost spine 250 (LightTank/TD/MBT-ish) → MBT 275 → HighTech 300 → Dreadnought 400 → LineBreaker 500.
- Ranges: HighTech/Dreadnought/TankDestroyer all +500 vs the old ladder (bands too); AntiAir stays 6000.
- Composite check columns: A = HP/Cost×Speed (mobile-durability), B = DPS/Cost×Range (ranged-poke),
  Total = A+B. Roster is role-clustered (brawlers high-A/low-B, artillery high-B/low-A). No remaining
  outliers after the LineBreaker slow-down + FS buff.

## MissileVehicle class (`^MissileVehicleTemplate`) — the vehicle analog of `^AdvancedAntiAirDefense`
- **Solves:** FireSupport was to lose AA (fragile+long-range+AA = too strong), but 6 factions had NO
  dedicated AA vehicle (ts_gdi, ixian, ordos, futuretech, terran, zerg) and relied on a dual-role unit.
- **Weapon rule (KEY):** MissileVehicle has **ONE weapon** hitting **both ground and air** (priced once
  as DPS; no air bonus). AntiAir keeps its **separate FREE air weapon** (+50% range→9000, +100% damage),
  priced only on the ground weapon. So AntiAir >> MV vs air; MV > AntiAir vs ground (range 8000 vs 6000);
  FireSupport = pure ground siege at 10000, no air. MV dominant in neither = flexible fragile all-rounder.
- **Baseline = Hover MLRS** (`ts_gdi_hovermlrs`, T2, single dual-purpose weapon, range 8159≈8000). NOT the
  TD GDI MLRS (which is the SAME KIND — its 227mm/227mmAMT are `!upgrade`/`upgrade` MUTUALLY EXCLUSIVE =
  effectively ONE weapon; it's also a MissileVehicle, not FireSupport).
- **Membership = the "missile-MLRS family":** long-range missile units that ALSO hit air. Includes
  ts_gdi_hovermlrs, td_gdi_mlrs, latinsyndicate_lars, asianalliance_type89mlrs, ixian_ixmissiletank +
  the AA-capable FireSupport pool + **Nod bikes** (td_nod_reconbike/chemicalattackbike, ts_nod_attackcycle
  — MOVE from AntiAir → MissileVehicle, kept very fast as members). **Curate from a COMPLETE air-capable
  scan** (my earlier scan only read `*weapon*.yaml` files — MISS: missiles.yaml/ballistics.yaml/
  tiberiandawn.yaml define weapons too; rescan ALL yaml for `ValidTargets: … Air`).

## Epic vehicles (`^EpicVehicleTemplate` + `^EpicAirUnitTemplate`) — RULES
- **Remove `DamageMultiplier@EpicBuff`** (defaults.yaml:1644 + :1934) — the last multiplier standing.
- **4× raw HP** replaces it (the general ×2 HP bake + ×2 for the removed epic damage-reduction).
- **Epic vehicle baseline = Monster Tank** (`ra1_soviets_monstertank`): HP 1,000,000×4 = **5,000,000**,
  spd 45, range **8,500**, cost 10,000, Superheavy. **DPS = 10,000 (DPS/Cost 1.0).**
- **Epic DPS calc:** its cannon (`MonsterTank120mm`, dmg 40k, burst 2, eff-reload 103+32=135) + AA tusk
  (`MonsterTankTusk`, dmg 20k, burst 4, eff-reload 125+9=134) both hit ground+air and have the SAME
  eff-reload → **DPS values ADD**. Current summed ≈ 1,190; buff both weapons ~8.4× (to 5,000 DPS each →
  10,000 total; cannon dmg → ~337,500, tusk → ~167,500) via the pipeline (`distribute_damage` snaps to
  the 2000-grid). Damage-VALUE change = allowed without permission.

## ★ FUNDAMENTAL VERIFIER RULE (I violated this — do NOT again): TIER **and** K must MATCH
Baseline+verifier must share the same **TechTier M-bucket AND K** or the 2.5× cost identity is wrong.
- **TechTier M** (DESIGN.md §"Tier counting for the M discount"; set ONLY by TECH-building prereqs —
  production buildings + refineries never count): no-tech = T1, radar/equiv = T2, tech-center = T3, beyond
  = T4/5. **T1 = T2 = M 1.0** (same bucket!) · T3 = 0.75 · T4/5 = 0.5. So a **T1 baseline + T2 verifier is
  FINE** (Artillery RA1-Allied-Artillery T2 / Brummbär T2 ✓; also T1/T2 mix ok), but a **T2 baseline + T3
  verifier is WRONG** (Hover MLRS T2 / Ixian Missile Tank T3 ✗; V2 rocket T3 ✗).
- **K** (special modifier): **gatling → K 1.25** (Asian MLRS, Latin LARS = gatling → invalid MV verifiers);
  flame/charge/cloak likewise must match. Tier detection = read Buildable Prerequisites for a tech building.
Also saved as memory.

## ★ NEXT MAJOR TASK (after compaction): NEW WEAPON CLASSES / TYPES
The rule **unit-class ↔ weapon-class are directly bound** (each unit class carries a specific weapon type)
needs MORE weapon templates to exist first. Maintainer will name the ones to create; **I ALSO propose my
own**. Initial suggestions to develop: **Light/Medium/Heavy Laser** (so beam units like the FS-verifier
candidates fit a class), Light/Medium/Heavy of each family (Cannon, Missile/Rocket, MG/Autocannon, Flame,
Plasma, Tesla, Gatling, Artillery-shell), + AA variants. Weapon class = derived from the main SpreadDamage
warhead's `Versus: Shield` (110/125/140 = 0.75/1.0/1.25; superheavy 155/170/185 = 1.5/1.75/2.0). Wire the
`weapon_classes.yaml` sidecar + `--check-weapon-classes` into `run_all.sh`, then the weapon-type↔unit-type
binding audit. **THEN** each vehicle class gets its bound weapon type(s).

### Weapon-class program — GUIDING RULES (maintainer, 2026-07-28)
- **STRICT ORDER:** finish the **vehicle unit templates FIRST** (MissileVehicle etc.), **THEN** build the
  new weapon templates. The maintainer will **name exactly** which weapon templates we need; I **also
  propose my own** (do not pre-build them before that conversation).
- **PURPOSE = kill warhead-mixing.** Today many weapons mix many warheads; the goal is **1–2 warheads max
  per weapon**, achieved by having a proper template per role so a weapon inherits ONE role instead of
  stitching several.
- **HARD LIMIT = 2 weapon-template inherits per weapon** (this is the *upgraded* variant's ceiling; a basic
  weapon = 1). See.
- **Special-unit exemption is NOT a blank cheque — it is TBD.** A special unit may exceed 2 **only when the
  extra mixing is genuinely justified** (a deliberate multi-role "for-fun" siege unit); an unjustified >2 is
  a cleanup target, NOT an exemption. The exact justification bar is **still to be determined** with the
  maintainer — do not assume the old siege-tank list is the final allow-list.

## ★ BUILD/IMPLEMENT ORDER (resume here after compaction)
1. **Record complete** (this section) — done.
2. **Build `^MissileVehicleTemplate`** in defaults.yaml (Light armor, single dual-purpose weapon behaviour,
   tooltip, build order) — boot-gated, same pattern as the 5 templates already built in commit `090d3d997`.
3. **Reassign the missile-MLRS family + Nod bikes → MissileVehicle** (scripted, collision-checked via the
   MiniYaml.cs:471 direct-sibling∩closure rule — see `scratchpad/collide.py` pattern); remove EpicBuff
   multiplier; boot-test → commit.
4. **NUMERIC PASS (needs maintainer `apply_balance --confirm` order):** set each baseline actor to the FINAL
   table above → `fit_class` scales every member 0.5–4.0× band, verifier at 2.5× → per-actor armor
   normalization (strip per-actor `Armor:Type` overrides so the class armor applies) → self-heal Step
   (scouts HP/1000, others HP/2500) → epic 4×HP + Monster-Tank DPS buff → re-extract → audits + BOOT GATE →
   commit yaml+ledger together.
5. **Weapon classes** (the next major task above).

**STRUCTURAL PASS ALREADY DONE + COMMITTED** `090d3d997` (5 vehicle templates, buffs stripped, 58
reassignments, boot-verified). Do NOT redo it.

═══════════════════════════════════════════════════════════════════════════════════════════════════

## ▶ STATUS / RESUME HERE (2026-07-26)

**Collaborative class-by-class anchor definition IN PROGRESS.** The maintainer names a class → I
propose baseline+verifier → they give exact numbers → LOCK here → later: create template (boot-gated)
+ `fit_class` + sign-off. **Every class needs a baseline AND a verifier** (verifier = 2×HP + 2×DPS +
2.5×cost, same speed/range → clean identity). Support is EXEMPT; cargo = Σ(passengers).

**LOCKED (cost0):** ScoutVehicle 300 · LightTank 400 · AntiAir 600 · TankDestroyer 600 · MBT 800
(Tiger pivot, signed) · FireSupport 1000 · ArtilleryTank 1200 (baseline; verifier pending) · LineBreaker
1200 · HighTechTank 2000 · Dreadnought 3000.
**➡ RESUME AFTER COMPACT — make ALL pending decisions, then FINISH ALL TEMPLATES.** Defenses = **7
templates** now (see "DEFENSE TEMPLATE ROSTER" below). Baselines locked: Basic 500, AntiAir 600, Advanced
1000 (idea B), Super (plasma, cost open). **Verifier convention = 2.5×HP + 2.5×DPS → 4.0×** (Basic
verifier = **Photon Cannon @2000**, AntiAir 2400).
**★ OPEN DECISIONS (all deferred to after compact):**
- (a) NAME the new hybrid template `^AdvancedAntiAirDefense?` (Ixian Missile Tower + Japan Ballista Tower,
  range 10000, T2). **This solves the Ixian AA gap** — missile tower stays here, NOT moved to Advanced T3.
- (b) NEW `^EarlyAdvancedDefenseTemplate` (Nod Laser Tower, Photon Cannon) — shares Basic's formula, T1/2
  exempt from the T3 rule.
- (c) Advanced verifier = Cabal Obelisk Prime? — its **charge K 0.75 vs baseline K 1.0** breaks the 4×
  identity — UNRESOLVED.
- (d) Super baseline 4000 (clean, epic ceiling — recommend) vs 2500 (overlaps).
- (e) Define **Bunker** (HP + cargo slots; Bastion K1.25).
- (f) ArtilleryTank verifier (lunar grille / Juggernaut MkII); Artillery verifier (V2); LineBreaker armor;
  `japan_armoredcar` Scout-vs-AntiAir; `asianalliance_pulverizer`→AntiAir.
- **THEN BUILD every template in `defaults.yaml` (boot-gated)** + apply the Nuclear Versus fix (step 3) +
  scout self-heal + Step=HP/1000 + per-class armor + power/cost + umlaut renames → `fit_class` → sign-off.
**★ BUG (NFWRambo, player-visible regression — investigate after compact, jumps the queue):** campaign
maps ("Special Delivery") vanished from the map editor + mission selector; triggered by adding factions to
`map.yaml`, or adding a `rules.yaml` + lua scripts. See `docs/design/ROADMAP.md`.
**Future audits:** projectile speed = range÷2 (V3-type missiles exempt); weapon-type↔unit-type binding.
Infantry anchors (14) already exist, need sign-off (commando needs a verifier). **After all anchors:**
create templates in defaults.yaml (boot-gated), run `fit_class`, wire `check_band` into `run_all.sh`.
**Upgrades LAST.** **Weapons.yaml below-divider cleanup = ON HOLD** (`weapons_cleanup_plan.md`, no
deletions). WeaponClass restored to `weapon_classes.yaml`.

## ★ DECISIONS 2026-07-27 (post-compact template lock — all confirmed)

**(a) `^AdvancedAntiAirDefense`** (NEW hybrid, range **10000**, **T2**, closes Ixian AA gap):
- **Baseline = Ixian Missile Turret** = **2×HP + 2×DPS of the TD GDI Advanced Guard Tower @ 2.5× price**
  (Guard Tower = 200k HP / DPS 1000 / cost 1200 → Missile Turret = **400k HP / DPS 2000 / cost 3000**,
  range 10000). **SINGLE weapon** vs both ground + air (simple).
- **Verifier = Japan Ballista Tower** — cheaper + weaker, **same 10000 range**, but **TWO weapons
  balanced SEPARATELY**, each keeping its behaviour: **artillery-burst anti-ground** + **single
  high-damage missile anti-air** (both range 10000).

**(c) AdvancedDefense verifier = Consortium Quantum Cannon** (`steelconsortium_quantumcannon`),
re-priced to **4000** (= 4.0× Advanced baseline 1000). **Dual `SteelQuantumTurretRail`** summed →
give it the consolidated **`FirepowerMultiplier@steelconsortium_quantumcannon: 50`** so 2 weapons ×0.5 =
net 1× (per the multiplier-consolidation rule). Replaces Cabal Obelisk Prime → **drops the charge-K
problem**. (Obelisk Prime shelved as Advanced verifier.)

**(d) SuperDefense — baseline 4000, NO verifier.** Instead **cluster all super defenses in a
2000–6000 cost band around 4000** (no 4× → no absurd 16k builds). **Hard ceiling = BFG-10000 @ 10000
cost, BuildLimit 1** — nothing in the game costs more.

**(e) Bunker** — `^BunkerTemplate`: **Concrete** armor, no inherent weapon (garrison shoots), Bastion
variant **K1.25**. **COST FORMULA = `HP/600 × slots`** (NOT the 3-input defense formula — bunkers have
no own DPS/range). Verified: Soviet battle bunker **80000 HP × 6 slots → 800 = its current price
EXACTLY**. Keep the iconic bunkers' HP+slots fixed, derive cost (Terran 240k/4 → 1600; battle bunker
unchanged at 800).

**(f) Standing vehicle items:**
- **ArtilleryTank verifier = Lunar Grille** ✓. **Juggernaut MkII = real Artillery** (turret only in
  theory; must DEPLOY → stationary → frontal artillery).
- **Artillery baseline = RA1 allies artillery** (`ra1_allies_alliedartillery`: **HP 20000 / spd 60 /
  range 15000 / DPS 375 / cost0 600**, Light armor, frontal). **Verifier = Naxis Brummbär** (T2,
  promotion-gated, no odd modifiers, **WC 1.0**). V2 nuclear launcher rejected (T3 + nuclear WC≠1).
  Artilleries compared at **WC 1.0**.
- **LineBreaker armor = Superheavy** ✓ (was TBD).
- **`japan_armoredcar` = AntiAir** (currently a SUPPORT vehicle with +50% range; **supports split into
  real supports (exempt) + AntiAir**). **`asianalliance_pulverizer` = AntiAir** ✓.

**★ AntiAir range REVISED: baseline 6000, band 5000–7000** (was 5000/4500–5500). **Range ⟂ HP
(inversely)**: fragile AA (the two Nod bikes) → longer range (→7000) to survive; tanky AA → shorter
(→5000). **AA weapon = ground +50% = 9000.**

**★ FULL ARMOR TABLE (confirm before build):**
| Vehicle class | Armor | | Defense template | Armor |
|---|---|---|---|---|
| ScoutVehicle | Scout | | BasicDefense | Concrete |
| LightTank | Medium | | EarlyAdvancedDefense | **Steel** |
| AntiAir | Medium | | AntiAirDefense | Concrete |
| MBT | Heavy | | AdvancedAntiAirDefense | Steel |
| TankDestroyer | Heavy | | AdvancedDefense | Steel |
| HighTechTank | Superheavy | | SuperDefense | Steel |
| Dreadnought | Superheavy | | Bunker | **Concrete** |
| FireSupport | Light | | | |
| Artillery | Light | | | |
| ArtilleryTank | Medium | | | |
| **LineBreaker** | **Superheavy** | | | |

## ★ VEHICLE BASELINE LADDER + LATE RULES (2026-07-27, pre-compact)

**FULL VEHICLE BASELINE LADDER** (HP bumps 2026-07-27 to enable removing template multipliers):

| Class | baseline actor | HP | spd | range | DPS | cost0 | armor |
|---|---|--:|--:|--:|--:|--:|---|
_FINAL numbers (maintainer 2026-07-27, second pass — HP + DPS bumped to bake out ALL buffs):_

| ScoutVehicle | `td_nod_buggy` | 40000 | 200 | 4500 | 450 | 300 | Scout |
| LightTank | `ra1_allies_alliedlighttank` | 100000 | 120 | 5000 | **200** | 400 | Medium |
| TankDestroyer | `naxis_hetzer` | 150000 | 60 | 7000 | **500** | 600 | Heavy |
| AntiAir | `latinsyndicate_diablo` | 80000 | 125 | 6000 | **800** | 600 | Medium |
| Artillery | `ra1_allies_alliedartillery` | 50000 | **70** | 15000 | **500** | 600 | Light |
| MBT | `naxis_tiger` | 200000 | 100 | 5500 | **400** | 800 | Heavy |
| FireSupport | `td_gdi_mlrs` | 75000 | **90** | 10000 | **600** | 1000 | Light |
| ArtilleryTank | `ixian_ixcombatsiege` | 125000 | 80 | 12000 | **160** | 1200 | Medium |
| LineBreaker | `td_nod_flametank` | 300000 | 80 | 2500 | **1000** | 1200 | Superheavy |
| HighTechTank | `ra1_soviets_mammothtank` | 500000 | 50 | 6000 | **1000** | 2000 | Superheavy |
| Dreadnought | `terran_warhound` | 600000 | 60 | 6500 | **1200** | 3000 | Superheavy |

**DPS DOUBLED from the first pass** for LightTank (100→200), TankDestroyer (250→500), MBT (200→400),
ArtilleryTank (80→160), HighTechTank (500→1000). AntiAir→800, LineBreaker→round 1000, Dreadnought→1200,
**Artillery→500, FireSupport→600**. Scout DPS unchanged (450).

**★ GOAL — REMOVE ALL BUFF MULTIPLIERS** (maintainer 2026-07-27, CONFIRMED): delete **every** template /
class buff layer — `^VehicleBuffs`, `^InfantryBuffs`, `^AircraftBuffs`, `^TankBuffs`, `^DefenseBuffs`,
`MainBattleTankBuff`, `HighTechTankBuff`, `SupportVehicleBuff`, `FireSupportBuff`, etc. (both the
`FirepowerMultiplier@*` and `DamageMultiplier@*`) — and **bake them into the baseline HP + damage** so
the baseline is WYSIWYG. The HP+DPS bumps in the FINAL table above ARE that bake. **ONLY the two global
buffs survive** (BALANCE_SYNTHESIS §7): the global **50% firepower reduction + 150% damage multiplier**
(150% on units+defenses only, buildings exempt). Each actor keeps at most ONE
`FirepowerMultiplier@<actor>` fine-tune knob. This is the core of the `fit_class` build pass.

**★ WEAPON STRUCTURE RULES (maintainer 2026-07-27):**
- **Max 2 inherited templates per weapon.** Basic units = **1** weapon-template inherit; upgraded /
  promotion units = up to **2** (where appropriate). Special fun units (siege tank, siege engine, a
  few others with many mixed warheads) are **EXEMPT** — regular units must obey.
- **Weapon-type ↔ unit-class binding** (goal): limit which unit class may carry which weapon type and
  vice versa — cleaner + consistent. Needs the weapon-type library + `weapon_classes.yaml` wired.
- **Twin law (locked):** FriendlyFire **and** ExtraDamage twins = **50%** of the main (ExtraDamage any
  type — SpreadDamage/OpenToppedDamage — and EXCLUDED from the damage total); Percentage = **1 per
  2000**; only **template-named** warheads may exist (`1Dam` retired). Code: `formula.distribute_damage`
  / `spread_damage_sum`; guard `audit_warhead_split`.

**★★ PERMISSION RULE (maintainer 2026-07-27 — ABSOLUTE):** NEVER change a weapon's **warhead**, its
**Burst**, or its **BurstDelays** without **explicit maintainer permission**. Other stats (HP, Damage
value, Range, Speed, Cost, ReloadDelay, FirepowerMultiplier) may be tuned more freely (especially once
the synthesized reference data lands). Warhead/burst/burst-delay = ASK FIRST, every time.

**★ REFERENCE DATA INCOMPLETE (2026-07-27):** the synthesized cross-mod reference stats (data-mining)
are **NOT finished** — several games still un-mined. Balance tuning that leans on the reference band
waits for it; structural/template work proceeds now.

**★ RECLASSIFICATION FLAGS — one-time check before the build** (current template ≠ new class; confirm
each is intentional). From the live membership snapshot:
- **→ new `^AntiAirVehicleTemplate`** (from Support/Scout): `latinsyndicate_diablo` (baseline!),
  `steelconsortium_barracuda` (verifier!), `ra1_allies_alliedheavyaatank`, `ra1_soviets_flaktruck`,
  `ra1_soviets_gatlingtank`, `ra2_soviets_flaktrack`, `tkm_flakbus`, `naxis_wirbelwind`,
  `yuri_gatlingtank`, `forgotten_m113adats`, `japan_armoredcar`, `asianalliance_pulverizer`,
  the two Nod bikes (`td_nod_reconbike`/`td_nod_chemicalattackbike` + TS `ts_nod_attackcycle`).
- **→ new `^LightTankTemplate`** (from MBT): `ra1_allies_alliedlighttank` (baseline!),
  `td_nod_lighttank`, `td_nod_lighttankmkii` (verifier!), `ordos_combattank`, + the LightTank member
  list. **Turreted tanks are ALWAYS Light/MBT/HighTech.**
- **→ `^TankDestroyerTemplate`** (from LineBreaker): `naxis_hetzer` (baseline!), `naxis_jagdpanzer`,
  `ordos_tankdestroyer`, `ra1_allies_alliedtankdestroyer`, `ra2_allies_tankdestroyer`.
- **→ `^DreadnoughtTemplate`** (from LineBreaker): `terran_warhound` (baseline!), `ixian_neocymek`
  (verifier!), `asianalliance_pulverizermecha`, `schwarzermond_neojagdpanzer`.
- **→ new `^ArtilleryTankTemplate`** (from FireSupport/Artillery, turreted): `ixian_ixcombatsiege`
  (baseline!), `schwarzermond_lunargrille` (verifier!), `asianalliance_howitzer`,
  `td_gdi_archerartillery`, `ts_gdi_juggernautmkii` (deploys → maybe real Artillery).
- **LineBreaker keeps** only flame/melee/very-short durable (flame tanks, Ogre/Knight/Ultralisk/Megalodon).
- **FireSupport keeps** long-range fragile (MLRS baseline, missile trucks); LOSES the AA + the siege/turret units.

## ★ DECISIONS 2026-07-27b (comparison-check resolutions — maintainer confirmed)

Ran the one-time old-vs-new class comparison (`scratchpad/class_compare.py`): **390 vehicle
actors, 56 reclassifications** (matching the locked lists). Discrepancies resolved:
- **`ra1_allies_sheridanassaulttank` → LightTank** ✓ (was missed by a garbled id in the member list;
  it IS a light tank). Currently `^MainBattleTankTemplate`.
- **`naxis_kbelwagen` → AntiAir** ✓ — its `NaxiWW2KübelwagenMachinegun` has `ValidTargets: …, Air`,
  so it CAN hit air; it also has `^CargoVehicle` → **armed AA transport → AntiAir template**, priced by
  the **cargo rule** (Σ passengers), NOT LightTank/Scout. **ALSO umlaut-rename `naxis_kbelwagen →
  naxis_kubelwagen`** (u, not dropped) — add to the umlaut rename batch with `naxis_brummbr→brummbar`.
- **`ra1_soviets_madtank` → Epic** (BuildLimit 1 → epic; drop the LineBreaker inherit, keep Epic).
- **`japan_exorcistoitank` → Epic** (BuildLimit 1 → epic; drop the HighTech inherit, keep Epic).
- **`terran_siegetank` → ArtilleryTank**; **`siege_tank` (Harkonnen/Shared) → Artillery**;
  **`missile_tank` → FireSupport**; **`ts_nod_ticktank` → MBT** (stays; tick tank not LightTank).
- **`yrsmin.empy` → REMOVE** (only 2 defs — `RedAlert2/Shared/…/misc.yaml` + `rules/redalert2.yaml`;
  zero references → delete both).
- Civilian/AI-only dupes (`ra2_c_abram`, `ra2_c_ifv`, `ra2_c_hum`, `ra2leopard`, `yrrobo`) = **EXCLUDE
  from the rebalance** (not buildable faction units), leave defined.

**★ REMOVE-ALL-MULTIPLIERS = ONE PASS (maintainer 2026-07-27b):** do NOT keep the multiplier layers in
place for a first pass — **strip every `DamageMultiplier@*Buff` / `FirepowerMultiplier@*Buff` NOW**
(keep only `^GlobalBuffs` FP50/DMG150 + self-heal + tech-upgrade inherits) and **find the new balance by
setting the baseline actors to the ladder and scaling each class from there** (`fit_class`). Temporary
imbalance during the pass is accepted.

**★ BASELINE RATIOS (WYSIWYG after buff removal — HP/Cost = effective-HP/credit):**
| Class | HP | DPS | Cost | HP/Cost | DPS/Cost |
|---|--:|--:|--:|--:|--:|
| Scout | 40000 | 450 | 300 | 133.3 | 1.500 |
| LightTank | 100000 | 200 | 400 | 250.0 | 0.500 |
| AntiAir | 80000 | 800 | 600 | 133.3 | 1.333 |
| TankDestroyer | 150000 | 500 | 600 | 250.0 | 0.833 |
| Artillery | 50000 | 500 | 600 | 83.3 | 0.833 |
| MBT | 200000 | 400 | 800 | 250.0 | 0.500 |
| FireSupport | 75000 | 600 | 1000 | 75.0 | 0.600 |
| ArtilleryTank | 125000 | 160 | 1200 | 104.2 | 0.133 |
| LineBreaker | 300000 | 1000 | 1200 | 250.0 | 0.833 |
| HighTechTank | 500000 | 1000 | 2000 | 250.0 | 0.500 |
| Dreadnought | 600000 | 1200 | 3000 | 200.0 | 0.400 |
Clean **250 HP/credit spine** across LightTank/TankDestroyer/MBT/LineBreaker/HighTech; fragile classes
lower (Artillery 83, FireSupport 75); Scout leads DPS/Cost (1.5). **ArtilleryTank DPS/Cost 0.133** is
the deliberate outlier (tanky long-range siege, not a damage dealer — flagged, standing unless changed).

**★ LADDER REVISION 2026-07-27c (maintainer, ratio-driven):**
- **LineBreaker: cost 1200 → 1000** (HP 300000 / DPS 1000) → **HP/Cost 300 (highest), DPS/Cost 1.0**. ✓ LOCKED
- **Artillery: cost 600 → 500** (HP 50000 / DPS 500) → **HP/Cost 100, DPS/Cost 1.0**. ✓ LOCKED
- **TankDestroyer: DPS 500 → 600** (HP 150000 / cost 600) → HP/Cost 250, **DPS/Cost 1.0**. ✓ LOCKED
- **Dreadnought = (A) LOCKED:** cost **3000** (apex) → **HP 900000 / DPS 1500** (HP/Cost 300, DPS/Cost 0.5).
- **ArtilleryTank = (B) LOCKED:** keep **HP 125000** → cost **700 / DPS 525** (HP/Cost ~178, DPS/Cost 0.75).
- **`asianalliance_viper` = Artillery LOCKED** (stays; frontal no-turret).

## ★ NEW CLASS — `^MissileVehicleTemplate` (2026-07-28) — flexible ground+air missile skirmisher

**Solves:** FireSupport was to lose AA (fragile-long-range + AA = too strong), but 6 factions have NO
dedicated AntiAir vehicle and rely on a dual-role FireSupport unit (ts_gdi hovermlrs, ixian, ordos,
futuretech, terran, zerg). Rather than strip their only AA, split the dual-role units into their own
class — the **vehicle analog of `^AdvancedAntiAirDefense`** (the defense-side hybrid). **Nothing gets its
AA stripped.**

**Position = EXACTLY between FireSupport and AntiAir** (maintainer 2026-07-28, ratio-defined):
| Class | HP | Spd | DPS | Range | Cost | Armor | HP/Cost | DPS/Cost |
|---|--:|--:|--:|--:|--:|---|--:|--:|
| FireSupport | 75000 | 90 | **750** | 10000 | 1000 | Light | 75 | 0.75 |
| **MissileVehicle** | **80000** | **110** | **800** | **8000** | **800** | **Light** | **100** | **1.00** |
| AntiAir | **75000** | **130** | **750** | 6000 | 600 | Medium | 125 | 1.25 |

- **MissileVehicle baseline = `td_gdi_mlrs`** (GDI Hover-style MLRS — the unit that prompted the split).
  Verifier (2×HP+2×DPS+2.5×cost): HP 155000 / DPS 1400 / cost 2000, same spd/rng — pick a verifier unit.
- **Weapon rule (KEY, maintainer 2026-07-28):** MissileVehicle has **ONE weapon** that hits **both ground
  and air** (priced once as its DPS; no air bonus → air = ground). AntiAir keeps its **separate FREE air
  weapon** (+50% range → 9000, +100% damage), priced only on the ground weapon (unchanged rule). So
  AntiAir >> MissileVehicle vs air; MissileVehicle > AntiAir vs ground (range 8000 vs 6000); FireSupport =
  pure ground siege at 10000, no air. MissileVehicle dominant in neither → the flexible fragile all-rounder.
- **Armor = Light** (fragility is the counterweight to flexibility; clear counter = fast closers).
- **Speed 110** baseline; **members keep own speed → Nod bikes stay very fast** (`td_nod_reconbike`,
  `td_nod_chemicalattackbike`, `ts_nod_attackcycle` MOVE from AntiAir → MissileVehicle, fast outliers).

**★ FireSupport + AntiAir stat changes (2026-07-28):**
- **FireSupport:** DPS 600 → **750** (only change). **Baseline switches GDI MLRS → Latin Syndicate
  Missile Truck** (`latinsyndicate_missiletruck`; already in-class, fits Latin's rocket identity).
  **RA1 V1 Rocket Truck STAYS Artillery** (indirect ballistic, 15000, frontal). **⏳ FireSupport needs a
  NEW verifier** (old baseline→MissileVehicle, old verifier→baseline).
- **AntiAir:** HP 80000 → **75000**, DPS 800 → **750**, Speed 125 → **130** (so MissileVehicle mid = 110).

**★ Membership curation PENDING** (from the 15 AA-capable FireSupport units + Nod bikes): clear missile
dual-role → MissileVehicle; false positives (e.g. `zerg_lurker` targeting-only) stay put; gatling/beam
units (futuretech_gunstrider, japan_waveforcetank) may be AntiAir instead. Propose + confirm before moving.

## ★ RANGE LADDER (maintainer 2026-07-26 — verified consistent, steps of 500)

| Class | baseline range | band (±500) |
|---|--:|--:|
| LightTank | 5000 | 4500–5500 |
| **MBT** | **5500** | 5000–6000 |
| HighTechTank | 6000 | 5500–6500 |
| Dreadnought | 6500 | 6000–7000 |
| TankDestroyer | 7000 | 6500–7500 |
| **FireSupport** | **10000** | **9000–11000** |
| **ArtilleryTank** | **12000** | **10000–14000** |

The **direct-fire gun ladder now ENDS at TankDestroyer 7000** (500-step, close brawler → long-range).
The **indirect long-range classes** sit above it with wider ±bands: **FireSupport 10000 (band
9000–11000)** — slow + very fragile, must outrange tanks; **ArtilleryTank 12000 (band 10000–14000)** —
tanky TURRETED artillery (Medium armor); **pure Artillery 15000 (band 13000–17000)** — FRONTAL-facing
(no turret), Light armor, fragile. Scout / AntiAir / LineBreaker
have their own ranges (Scout 4500 band 4000–5000; **AntiAir GND 5000 band 4500–5500**, AA weapon
+50% = 7500; LineBreaker short ~2500). **These ranges override the per-class range values below.**

## ★ ARMOR LADDER (maintainer 2026-07-26 — one armor type per class)

Each class carries a fixed armor type (lightest → heaviest: **Scout < Light < Medium < Heavy <
Superheavy**):

| Class | Armor |
|---|---|
| ScoutVehicle | **Scout** |
| LightTank | **Medium** *(revised from Light, 2026-07-26)* |
| AntiAir Vehicle | **Medium** |
| MBT | **Heavy** |
| TankDestroyer | **Heavy** |
| HighTechTank | **Superheavy** |
| Dreadnought | **Superheavy** |
| FireSupport | **Light** |
| Artillery | **Light** |
| ArtilleryTank | **Medium** (tanky turreted artillery) |
| LineBreaker | **TBD** — "very durable" → likely Heavy/Superheavy (confirm) |

*(Aircraft / naval / defenses get their own armor scheme later.)*

## ★ TWO NEW PRICING RULES (maintainer 2026-07-26)

1. **Flame units → special K 1.25.** Every flame weapon burns / deals damage-over-time, so ALL flame
   units carry a **1.25× special modifier** (new rule; wasn't applied before).
2. **WeaponClass is part of the DPS calc** (confirmed): `DPS = Damage × Burst / eff-reload ×
   WeaponClass`. e.g. **Medium Flame = 1.0, Heavy Flame = 1.25** — the heavier weapon class raises DPS
   directly, so the verifier reaches 2× DPS with a *higher weapon class + lower damage-per-shot*.

---

## ✅ LightTank (NEW) — LOCKED 2026-07-25

**Baseline actor:** `ra1_allies_alliedlighttank`, **restatted** to:
| HP | Speed | Range | Damage | Reload | **cost0** | DPS |
|--:|--:|--:|--:|--:|--:|--:|
| **40000** | **120** | **5000** | **4000** | **40** | **400** | 100 |

**Verifier:** **Nod Light Tank Mk II** (`td_nod_lighttankmkii`, the promotion unit) at **exactly 2.5×
cost = 1000¢**, restatted to **2× HP / 2× DPS** (80000 HP / 8000 dmg @ 40, same 120 spd / 5000 rng).
- **Move its point-defense laser to the Black-Market upgrade** (same pattern as the bikes) so it is
  no longer a base **special** modifier → keeps the verifier identity clean (K = 1.0).
- The **regular Nod Light Tank** (`td_nod_lighttank`) keeps its current price but is rebalanced to fit
  this band.

**Class rules:** all members → **Medium armor** (revised from Light on 2026-07-26 — see ARMOR LADDER);
rebalanced into the baseline→verifier band.

**★ REBALANCE METHOD (maintainer 2026-07-25, applies to ALL classes):** each member **keeps its
current Speed, Range, Cost, ReloadDelay, Burst, BurstDelays** where possible. Rebalance is done by
**(1) adjusting the main Damage first, then (2) fine-tuning with the unit's `FirepowerMultiplier`**
(+ HP to fit the band). Cost stays nostalgic (§20); the formula prices the kept cost from the tuned
stats.

**Members (maintainer-confirmed):** latinsyndicate_rushertank, yuri_lashertank, ra1_allies_sheridan
assaultta, schwarzermond lunar panzer, japan_shrineminitank, naxis_panzer (Naxis Panzer III — HP comes
DOWN into band), futuretech_robottank. **Tick Tank DROPPED** (slow/deploys — doesn't fit).

**Members (my additions — CONFIRMED, templates already exist in yaml per maintainer):**
`terran_vulture`, `asianalliance_viper`/`asianalliance_quasar`, `steelconsortium_manta`,
`ixian_shockraider`, `cabal_ravager`, `naxis_kbelwagen`, `japan_armoredcar`.
- **`latinsyndicate_diablo` → NOT LightTank.** It's Latin's main **anti-air** vehicle → **move from
  Support to the AntiAirTank template.** (flagged for the AntiAirTank class.)
- **`ordos_ordoscombattank` (Ordos Combat Tank) → ADD to LightTank** — the lightest of the three Dune
  house tanks (§17.4: Ordos 3.2× < Atreides 3.7× < Harkonnen 4.8×). Nudge its speed up toward the
  class if it feels too slow; otherwise keep.
- Scouts (ordos_raider, ts_gdi_pitbull, forgotten_raidercar, IFVs, futuretech_salamanderifv) =
  **already ScoutVehicle in the yaml** (confirmed) — not here.

**PREREQ note:** the class↔weapon binding rules (which unit class may pick which weapon class/type)
need the **new weapon types (§13 warhead library) implemented first**, and the restored
**`WeaponClass`** sidecar (`docs/balance/weapon_classes.yaml`) wired into the pipeline.

---

## ✅ HighTechTank — LOCKED 2026-07-25

**Baseline = RA1 Soviet Mammoth Tank** (`ra1_soviets_mammothtank`) — EXACT round numbers
(maintainer 2026-07-25):
| HP | Speed | Range | Dmg/shot | Burst | BurstDelay | **eff-reload** | **cost0** | DPS |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **400000** | **50** | **6000** | **20000** | **2** | 8 (keep) | **80** | **2000** | **500** |
- **eff-reload 80** for BOTH weapons, but they keep their different burst delays: **cannon bd 8 ⇒
  ReloadDelay 72** (72+8); **AA tusk bd 12 ⇒ ReloadDelay 68** (68+12). Total per burst = 40000.
  **Range 6000, band 5500–6500** (2026-07-26). (Verifier likewise: eff-reload 80 both, cannon RD 72 / AA RD 68.)

**Verifier = Siege Mammoth Tank** (`ra1_soviets_siegemammothtank`) — 2×HP / 2×DPS / 2.5×cost, SAME
speed+range:
| HP | Speed | Range | Dmg/shot | Burst | eff-reload | **cost0** | DPS |
|--:|--:|--:|--:|--:|--:|--:|--:|
| **800000** | **50** | **6000** | **40000** | **2** | **80** | **5000** | **1000** |
- ✓ identity verified: 2×HP + 2×DPS (same spd/rng) = **exactly 2.5× cost** under the class-baseline
  formula (o 1.5 / p 2 / q 4 → mean 2.5).

**⚠ Pricing-flag cleanup (both units):** all 10/8 armaments are `pricing=True` (base gun + Targeting-
Computer/Thermobaric/Tesla upgrade variants + the AA MammothTusk). Anchor DPS = **500** from the base
main gun. Upgrade variants are upgrade-gated (excluded). **★ AG/AA PAIR LAW (maintainer 2026-07-25):
a unit's anti-ground and anti-air base weapons must have the SAME EFFECTIVE reload delay** (so
identical DPS) **+ same Damage, Burst, WeaponClass — but their BurstDelays MAY differ** (ReloadDelay
compensates to keep eff-reload equal). **Counted as ONE for pricing — never summed** (can't fire on
the same target). Mammoth: cannon bd 8 → ReloadDelay 72; AA tusk bd 12 → ReloadDelay 68; **both
eff-reload 80** → both DPS 500, priced once (not 500+500).
**Other Soviet mammoth variants:** only these two exist in the RA1 Soviet roster; the per-armament
upgrade variants inherit the base damage (20000 baseline / 40000 verifier) + their upgrade modifiers.
- Ladder so far: LightTank 400 · MBT 800 · **HighTechTank 2000**. (Maintainer called 2000 "twice the
  MBT baseline" — vs the Tiger's cost0 800 that's 2.5×; confirm MBT stays 800 or bumps to 1000.)
- **Apocalypse** sits as a heavy *member*, not the baseline.
- **Turreted tanks are ALWAYS Light / MBT / HighTech** (maintainer rule).

## ✅ TankDestroyer — LOCKED 2026-07-25

**Role:** frontal-facing (no turret), long range, anti-tank. **Baseline = the cheapest/budget TD
(Hetzer); verifier = RA2 Tank Destroyer.**

| | Unit | HP | Speed | Range | Dmg | Burst | Reload | **cost0** | DPS |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| **Baseline** | `naxis_hetzer` | **75000** | 60 | 7000 | 20000 | 1 | 80 | **600** | 250 |
| **Verifier** | `ra2_allies_tankdestroyer` | **150000** | 60 | 7000 | 40000 | 1 | 80 | **1500** | 500 |

- Range band **6500–7500**. ✓ identity: 2×HP + 2×DPS, same spd/rng → 2.5× cost (600 → 1500).
- **Ladder now:** LightTank 400 · **TankDestroyer 600** · MBT 800 · HighTechTank 2000 (Hetzer is a
  budget unit, cheaper than the MBT — intended).
- **Other TDs in between** (600–1500): `ra1_allies_alliedtankdestroyer`, `naxis_jagdpanzer`.
- **Ordos Tank Destroyer = MORE expensive** — it's **cloaked** → carries a special modifier (K>1),
  so it prices above the plain band.
- **Neo Jagdpanzer → Dreadnought** (450k HP Superheavy — too tanky for a TD).

## Taxonomy clarifications (maintainer 2026-07-25)

- **LineBreaker** = **very short range + very durable** (flame tanks). The template's heavy
  damage-reduction + extra-firepower suits CLOSE range only.
- **FireSupport** = **weaker armor + longer range**; countered easily *because* fragile. **REMOVE
  anti-air from FireSupport** (e.g. GDI MLRS loses AA) for consistency.
- **ArtilleryTank** = between tank and artillery (e.g. **Ixian Combat Siege**; maybe Sturm Tiger —
  research later; so far Ixian Combat Siege is the only clear fit).

## ✅ NEW CLASS — **Dreadnought** (`^DreadnoughtTemplate`) — heavy, long-range, FRONTAL, TANKY

**Named by maintainer 2026-07-25.** Frontal-facing + long range + **tanky** — the tanky counterpart
to the fragile FireSupport. Currently mis-assigned to LineBreaker, whose damage-reduction + firepower
buff only works at *close* range; Dreadnought needs its OWN damage-reduction tuned for long range
(NOT the LineBreaker buff). Members (move off LineBreaker):
- `asianalliance_pulverizermecha` — 285000 HP, Superheavy, cost 3000
- `terran_warhound` — 300000 HP, Heavy, cost 4500
- `ixian_neocymek` — 300000 HP, Heavy, cost 4500

**TODO:** create `^DreadnoughtTemplate` in defaults.yaml (boot-gated); baseline/verifier pick later.

## HOLD

**Weapons.yaml below-divider cleanup = ON HOLD** (maintainer: "don't delete anything yet"). Plan
stays in `weapons_cleanup_plan.md`; no deletions/moves until greenlit.

---

## ✅ Dreadnought — LOCKED 2026-07-26 (Warhound baseline, no cloak)

**Baseline = Warhound** (`terran_warhound`) — the previous baseline stats, but KEEP the Warhound's own
weapons (adjust only their DAMAGE to hit the target DPS):
| HP | Speed | Range | cost0 |
|--:|--:|--:|--:|
| **300000** | **60** | **6500** (band 6000–7000) | **3000** |
- Weapons kept: **SCTyr** dual AG cannon (burst 2, bd 0, reload 44) + **SCTyrAA** burst-4 anti-
  everything rockets (burst 4, bd 2, reload 84). **Both hit ground → multi-weapon ground-sum**: anchor
  DPS = cannon DPS + rocket DPS (set via weapon damage). Keep bursts/burst-delays/reloads as-is.

**Verifier = Neo Cymek** (`ixian_neocymek`) — a Warhound carbon-copy (dual **railgun** StormGun +
burst-4 rockets; only the cannon→railgun differs), so "changing the weapon damage is the easiest
thing":
| HP | Speed | Range | cost0 |
|--:|--:|--:|--:|
| **600000** | **60** | **6500** | **7500** |
- 2× HP, **2× DPS** (adjust the weapon damage; keep its bursts/burst-delays/reloads), 2.5× cost, same
  speed/range → clean identity.

**Cloak/K = RESOLVED (2026-07-26): NO cloak on either.** Both Warhound baseline and Neo Cymek verifier
run at **K 1.0** (the cloak's only purpose — cancelling the Pulverizer's gatling K — is gone now that
the Warhound is the baseline). Clean 2×HP + 2×DPS + K 1.0 + same spd/rng → 2.5× cost = 7500 identity.

**Pulverizer Mecha** → scaled DOWN to a **member** at **cost 2500**, **range 6000** (CONFIRMED — the
minimum of the dreadnought band 6000–7000). Keeps its gatling (its own K 1.25 as a member, not the
anchor). **Other members:** Neo Jagdpanzer.

**Ladder:** LightTank 400 · TankDestroyer 600 · MBT 800 · HighTech 2000 · Pulverizer(member) 2500 ·
**Dreadnought baseline 3000.**

**★ MULTI-WEAPON GROUND-SUM RULE (maintainer 2026-07-25):** when a unit has multiple weapons that
can ALL hit the GROUND, **SUM their DPS** (they fire together on a ground target) — even if only one
of them also hits air. This is DISTINCT from the **AG/AA PAIR LAW** (an AG-only + an AA-only weapon =
alternatives, counted ONCE). Rule of thumb: **the ground is the reference — sum every weapon that
reaches a ground target.**

---

## ✅ LineBreaker — LOCKED 2026-07-26 (short range, very durable — flame + melee)

**Baseline = Nod Flame Tank** (`td_nod_flametank`):
| HP | Speed | Range | Dmg/shot | Burst | eff-reload | WeaponClass | special K | cost0 | DPS |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **200000** | **80** | **2500** | **20000** | **2** | **60** | **1.0** (Medium Flame) | **1.25** (flame) | **1200** | **666.7** |
- DPS = 20000 × 2 / 60 × **1.0** = 666.7. Flame → **special K 1.25** (burn/DoT, new rule).

**Verifier = Flame Tank Mk II** (`td_nod_flametankmkii`, the upgrade) — **Heavy Flame → WeaponClass
1.25**, which raises DPS directly, so the 2× DPS is reached with a *lower* damage-per-shot:
| HP | Speed | Range | Dmg/shot | Burst | eff-reload | WeaponClass | special K | cost0 | DPS |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **400000** | **80** | **2500** | **32000** | **2** | **60** | **1.25** (Heavy Flame) | **1.25** (flame) | **3000** | **1333.3** |
- DPS = 32000 × 2 / 60 × **1.25** = 1333.3 = 2× baseline. ✓ identity: 2×HP + 2×DPS + same K(1.25) +
  same spd/rng → 2.5× cost (1200 → 3000). (Damage-per-shot is 32000, NOT 40000, because the 1.25
  weapon-class already carries part of the DPS — as you flagged.)

**Members:** flame tanks (`td_nod_flametankmkii`, `forgotten_flametank`, `asianalliance_asianflametank`,
`japan_hovercraftflametank`) **+ melee / very-short-range durable**: WC2 **Ogre-Mage**, WC **Knight**,
**Zerg Ultralisk**, **Consortium Megalodon**. (Berserker / MAD Tank read as epic/suicide — flag if not.)
**Ladder (cost):** … LineBreaker baseline **1200** (short-range brawler class; its own range ~2500,
outside the gun range-ladder).

---

## ✅ ScoutVehicle — LOCKED 2026-07-26 (fastest, most fragile, cheapest; INFANTRY HP granularity)

**Baseline = Nod Buggy** (`td_nod_buggy`) — anchored on its REAL stats (not an invented DPS):
| HP | Speed | Range | DPS | cost0 | Armor |
|--:|--:|--:|--:|--:|--:|
| **20000** | **200** | **4500** | **450** | **300** | Scout |
- **DPS 450 = the buggy's ACTUAL main-gun DPS** (MachineGun: 4000 dmg × burst 3 / eff-reload 20 ×
  wc 0.75 = 450). The class self-anchors on the real baseline unit → the buggy keeps its weapon as-is,
  no nerf. *(The earlier "75" was a bogus cross-class ¾-of-LightTank guess — corrected 2026-07-26 per
  maintainer.)* HP 20000 = ½ the LightTank → fragile. Speed 200 = fastest class. Range **4500** =
  scout's own (**band 4000–5000**). cost0 **300** = nostalgic. NB the weapon is anti-infantry (SmallArms warhead) so this
  raw DPS is NOT cross-comparable with the tanks' anti-armor DPS — each class self-anchors.

**Verifier = Terran Vulture** (`terran_vulture`), restatted to the 2.5× identity point:
| HP | Speed | Range | DPS | cost0 |
|--:|--:|--:|--:|--:|
| **40000** | **200** | **4500** | **900** | **750** |
- 2×HP + 2×DPS + same spd/rng → exactly 2.5× cost (300 → 750). ✓ clean identity (o1.5 / p2 / q4 → 2.5).
- Restat: HP 75000→40000, cost 900→750, speed 125→**200**, range 4800→4500, weapon damage → **DPS 900**
  (2× the buggy). Ground-only (lays mines) → no AA question.

**★ INFANTRY HP GRANULARITY (maintainer 2026-07-26) — the scout class's special rule:**
Scouts use the **infantry HP granularity (steps of 1000)**, NOT the vehicle granularity (steps of
2500), so the 20000–30000 band holds **11 levels** (20k,21k,…,30k) instead of 5. Enforced by the
self-heal convention:
- **Engine mechanic:** self-heal Step is tied to max-HP. Vehicles use `ChangesHealth@SelfHealing.Step
  = HP/2500` (→ HP must be a multiple of 2500); infantry use **`Step = HP/1000`** (→ HP a multiple of
  1000). **Scouts switch to the infantry rule: `Step = HP/1000`** (verified: buggy 20000 → Step 20;
  Ixian/Ordos infantry actors already set Step = HP/1000).
- **Template change (to implement, boot-gated):** `^ScoutVehicleTemplate` currently inherits the
  VEHICLE self-heal from `^VehicleBuffs` (Step 10 / **Delay 1** / **DamageCooldown 10**). Override it to
  the INFANTRY timing from `^InfantryBuffs` (**Delay 2** / **DamageCooldown 20** / StartIfBelow 100),
  and set each scout actor's `ChangesHealth@SelfHealing.Step = HP/1000` (applied in the member
  rebalance, since HP must first be re-rounded to a multiple of 1000). **HARD RULE — do not forget.**
- `Repairable.HpPerStep = HP/20` stays (a multiple of 1000 is always a multiple of 20 → clean).

**Rebalance method (as always):** each member keeps its Speed/Range/Cost/Reload/Burst; tune main Damage
→ FirepowerMultiplier (+HP to band, now in 1000-steps).

**Membership (2026-07-26):** all currently-`^ScoutVehicleTemplate` actors STAY scouts (maintainer:
"currently scout ⇒ still scout unless I give another order") **EXCEPT the moves below.**
- **KEEP (rebalance into band):** `td_nod_buggy` (baseline), `ra1_allies_ranger`, `td_gdi_humvee`,
  `forgotten_raidercar`, `ts_nod_attackbuggy`, `futuretech_scoutdroid` (**bump speed** ~70→~180 — too
  slow for the fastest class), `japan_armoredcar`, `japan_scoutcar`, `tkm_technical`, `tkm_as42`,
  `ordos_leech`, `forgotten_bowler`, `forgotten_ruiner`, `protoss_positron`,
  `steelconsortium_whiterabbit`, `terran_vulture` (verifier).
- **`ordos_raider` = PREMIUM HEAVY SCOUT** (maintainer): keeps its 1200¢ / 60000 HP / K 1.25 — an
  intentional high outlier priced with the special modifier. Stays scout.
- **MOVED OUT → AntiAir Vehicle** (maintainer new order): `td_nod_reconbike`,
  `td_nod_chemicalattackbike` (TD bikes), `ts_nod_attackcycle` (TS bike). *(`naxis_bmwbike` = WW2 Naxis
  bike — FLAG: move too, or keep scout?)*
- **`ra2_soviets_terrordrone` = SPECIAL EXCEPTION** (maintainer): melee suicide/sabotage → EXEMPT.
- **`ra2_c_hum` = CIVILIAN** (`ra2_c_` prefix, only in garrison/spawn lists, 80000 HP is a civilian
  stat) → out of scope, not a buildable faction scout.

**★ Cross-note (infantry):** TD **rocket infantry → 300¢** (align with the other rocket-infantry
anchors; was 200) — matters for cargo/transport pricing (Σ passengers). Feeds the rocket-trooper
infantry anchor.

---

## ✅ FireSupport — LOCKED 2026-07-26 (fragile, LONGEST range 10000, NO anti-air)

**Role:** weak armor + the longest direct range — slow + fragile → it must OUTRANGE the tanks to
survive. **Range = 10000** (revised up from 7500; leaves the direct-fire gun ladder). **NO anti-air**
(strip it — e.g. GDI MLRS loses its AA).

| | Unit | HP | Speed | Range | DPS | cost0 |
|---|---|--:|--:|--:|--:|--:|
| **Baseline** | `td_gdi_mlrs` (GDI MLRS) | **25000** | **80** | **10000** | **400** | **1000** |
| **Verifier** | `latinsyndicate_missiletruck` | **50000** | 80 | 10000 | **800** | **2500** |

- ✓ identity: 2×HP + 2×DPS + same spd/rng → exactly 2.5× cost (1000 → 2500). (o1.5 / p2 / q4 → 2.5.)
- **Baseline (GDI MLRS):** iconic fragile rocket support. **AA stripped**; weapon buffed to **DPS 400**
  (from ~188); range 9920→10000; keeps HP 25000 / speed 80 / cost 1000.
- **Verifier (Latin Syndicate missile truck):** fits Latin's "best artillery / rocket-artillery"
  faction identity. Restat: HP 30000→50000, cost 1000→**2500** (premium tier), speed 75→80, range
  7777→10000, DPS →800. *(NB the 1000→2500 cost jump makes it a premium unit — flag if you want it
  kept cheaper and a different verifier named.)*
- **Ladder (cost):** … MBT 800 · **FireSupport 1000** · LineBreaker 1200 · HighTech 2000 · Dreadnought
  3000. Fragile long-range members to rebalance into band: prism tank, hover-MLRS, tank-killer,
  missile trucks, SSM launcher, Type-89 MLRS, etc.
- **Consequence:** FireSupport at 10000 now sits where Artillery / ArtilleryTank were "beyond 7500" —
  resolve the range overlap when we lock those (they must extend past 10000).

---

## ✅ AntiAir Vehicle (`^AntiAirVehicleTemplate`) — LOCKED 2026-07-26 (great vs air, HORRIBLE vs ground)

**Concept:** dedicated mobile anti-air — short range + Medium armor vs ground (bad on purpose), massive
range + firepower vs air (excellent). All members = **Medium armor**. Absorbs the planned AntiAirTank.

| | Unit | HP | Speed | Range(GND) | GND Dmg | Reload | DPS | cost0 |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| **Baseline** | `latinsyndicate_diablo` | **50000** | **125** | **5000** | **10000** | **15** | **667** | **600** |
| **Verifier** | `steelconsortium_barracuda` | **100000** | 125 | 5000 | 20000 | 15 | **1333** | **1500** |

- DPS = 10000 / 15 = 666.7 (burst 1, wc 1.0); verifier 2× via dmg 20000 / 15. ✓ identity 2×HP + 2×DPS +
  same spd/rng → exactly 2.5× cost (600 → 1500). **GND range band 4500–5500** (baseline 5000 ±500).
- **★ AA weapon = the ground weapon +50% RANGE / +100% DAMAGE** → Diablo AA: **range 7500, damage
  20000**. Priced ONLY on the GROUND weapon; the strong AA weapon is **FREE** (the class's whole appeal).
  **NO class K** — they are MEANT to be horrible vs ground (short 5000 range, Medium armor) and to shine
  vs air (7500 range, 2× damage). **Supersedes the old AG/AA pair law for this class.**
- **★ AA-primary members (bikes / Pitbull) — SPLIT rule:** their single dual-purpose missile is split
  into a **separate ground weapon** (priced, range in the 4500–5500 band) **and a separate AA weapon**
  (+50% range / +100% damage off it), applied as two armaments.

**Membership (drafted):**
- **All troop transports that have anti-air** (new rule; needs a Cargo+AA scan across the roster).
- **TD/TS bikes** moved from Scout: `td_nod_reconbike`, `td_nod_chemicalattackbike`,
  `ts_nod_attackcycle` (SPLIT their missile per the rule above). **`naxis_bmwbike` STAYS Scout** (its
  two weapons are ground-only WW2 MGs — no AA).
- **`latinsyndicate_diablo`** (baseline — Latin's main AA vehicle).
- **`ts_gdi_pitbull`** (missiles) → AntiAir (AA-primary, SPLIT rule).
- **Armed AA transports** (e.g. `ra2_soviets_flaktrack`, Cargo 5) → AntiAir template for armor + the
  derived AA weapon, but **priced by the cargo rule** (below), not the ground-weapon formula.
- **`japan_armoredcar`** (MG + AA MG, non-transport) — FLAG: stays Scout (maintainer "currently scout ⇒
  stays scout") or move to AntiAir? (has AA.)

### Findings (2026-07-26 roster scan)
- **`ra2_soviets_flaktrack` = TRANSPORT** (Cargo MaxWeight 5) + AA. Its AA range is already GND×1.5
  (5528→8292) → the +50%-range rule is native here. **Priced by the cargo rule** (Σ passengers), see
  the reconciliation below.
- **`latinsyndicate_diablo` = NON-transport**, clean GND cannon (dps 193, rng 7300) + AA cannon (rng
  10450 ≈ +43%). Latin's dedicated AA → strong **baseline candidate** (K 1.0). cost 1200.
- **`td_nod_reconbike` / `td_nod_chemicalattackbike` / `ts_nod_attackcycle` / `ts_gdi_pitbull` =
  AA-PRIMARY** — their only real weapon is AA missiles (+ a dmg-1 point-defense laser); **no distinct
  ground weapon.** ⇒ the "AA = +50%rng/+100%dmg OFF the ground weapon" rule has nothing to derive from.
  **RULING NEEDED:** (a) give them a ground weapon and derive AA from it, or (b) treat their
  anti-vehicle missile as the "ground" weapon and add a +50%/+100% AA variant?
- **`naxis_bmwbike` = GROUND-ONLY** (two WW2 MGs, no AA) → **STAYS Scout** (resolved, not AA).
- **`japan_armoredcar` = scout-with-AA** (MG + AA MG, non-transport). Maintainer rule "currently scout
  ⇒ stays scout" → keep Scout, but flag as an AA candidate.

### ★ CARGO × weapon pricing (CORRECTED by maintainer 2026-07-26)
For an armed transport the **price is FIXED = Σ(passenger costs at capacity)** — **NOT** ×1.25. The
**1.25× is the special modifier K applied INSIDE the balance formula**, which at that fixed price budgets
the unit **weaker combat stats**: `formula(stats) = Σ / 1.25`. So the transport pays full Σ for its
cargo utility and receives combat stats as if it cost Σ/1.25 (weaker at the same price). Unarmed
transport = Σ, no weapon (K n/a). Flak Track: price = Σ(5 passengers), stats solved with K 1.25; its
AntiAir membership only governs armor + the derived AA weapon.

**RESOLVED (all locked):** baseline Diablo @600 / verifier Barracuda @1500; AA = +50%rng/+100%dmg free,
NO class K (horrible-vs-ground / great-vs-air is the point); AA-primary units SPLIT their dual weapon;
cargo K as corrected above. **Only open flag:** `japan_armoredcar` placement (Scout vs AntiAir).

**★ Added member (maintainer 2026-07-26):** `asianalliance_pulverizer` (85000 HP, range 5517 → fits the
GND band 4500–5500) → **move to AntiAir Vehicle**, and **remove its "disabled when Pulverizer Mecha is
unlocked" prerequisite** (they're different units). *(NOT the `asianalliance_pulverizermecha`, which is
the Dreadnought member.)* Implement in the boot-gated pass.

---

## ✅ ArtilleryTank — LOCKED baseline 2026-07-26 (TANKY, TURRETED artillery — verifier pending)

**Definition (maintainer 2026-07-26):** the **tankiest artillery** — a unit with the **Artillery role +
a TURRET** (`AttackTurreted`), Medium armor, more durable than the frontal-facing (Light-armor) pure
Artillery. Range **12000 (band 10000–14000)**.

| | Unit | HP | Speed | Range | DPS | cost0 | Armor |
|---|---|--:|--:|--:|--:|--:|--:|
| **Baseline** | `ixian_ixcombatsiege` | **80000** | **80** | **12000** | **80** | **1200** | Medium |
| **Verifier** | *(pending — same-tier, see below)* | 160000 | 80 | 12000 | 160 | **3000** | Medium |

- Baseline = Ixian Combat Siege (Tier 2). Verifier target = 2×HP / 2×DPS / 2.5×cost, same spd/rng
  (160000 / DPS 160 / 3000). ✓ identity holds.
- **Verifier pick OPEN — tech-tier matched (maintainer wants baseline+verifier same tier):** Combat
  Siege is Tier 2; the only other Tier-2 turreted artillery is **`schwarzermond_lunargrille`** (the
  "lunar grille"). Also a natural premium option: **`ts_gdi_juggernautmkii`** (the Juggernaut Mk II
  upgrade — tier to confirm). **Name the verifier.**
- **`naxis_sturmtiger` = slow HEAVY member** of ArtilleryTank (250000 HP / range 14000 fits the band;
  keeps its speed 30 via the rebalance method — members keep their own speed). NOT the verifier (too
  slow to share the baseline's 80) and NOT Dreadnought (its 14000 range far exceeds Dreadnought's 6500).

**Membership = Artillery-template + `AttackTurreted` (roster scan 2026-07-26):** `ordos_cobratank`,
`ordos_pythontank`, `japan_waveforceartillery`, `ra1_soviets_grad`, `asianalliance_howitzer`,
`schwarzermond_lunargrille`, `schwarzermond_mars`, `td_gdi_archerartillery`, `forgotten_missilevan`,
`forgotten_mlrs`, `ts_gdi_juggernaut` (+`juggernautmkii`), `ts_nod_artillery` + the Combat Siege
baseline + Sturm Tiger. *(`ra2_tractor_driveby` = flag, likely a special/civilian driveby.)*
**Non-turreted artillery stays pure Artillery** (frontal, Light armor, range 15000).

---

## ✅ Artillery (pure) — LOCKED baseline 2026-07-26 (FRONTAL, fragile, Light armor, longest range)

**Definition:** frontal-facing (**NO turret**), **Light armor**, fragile, **range 15000 (band
13000–17000)** — the longest-range ground class. Distinct from the turreted, Medium-armor ArtilleryTank.

| | Unit | HP | Speed | Range | DPS | cost0 | Armor |
|---|---|--:|--:|--:|--:|--:|--:|
| **Baseline** | `ra1_allies_alliedartillery` | **20000** | **60** | **15000** | **300** | **600** | Light |
| **Verifier** | *(pending — V2 candidate)* | 40000 | 60 | 15000 | 600 | **1500** | Light |

- ✓ identity: 2×HP + 2×DPS + same spd/rng → exactly 2.5× cost (600 → 1500). DPS 300 (round, high
  per-shot / slow reload).
- **Verifier candidate = `ra1_soviets_v2rocketlauncher`** — restat to 40000 / DPS 600 / 1500, same
  60 spd / 15000 rng. **Confirm** (mind the tech-tier match — Allied Artillery is early T1).
- **Members = Artillery-template WITHOUT `AttackTurreted`** (frontal): `td_nod_artillery`,
  `naxis_grille`, **`naxis_brummbr`** (Brummbär — frontal casemate gun ⇒ pure Artillery, NOT
  ArtilleryTank; needs the umlaut rename), `naxis_donnerschlag`, `ra1_soviets_v1rockettruck` /
  `v2rocketlauncher` / `nuclearv2launcher`, `ra2_soviets_v3rocketlauncher`, `td_nod_specterartillery` /
  `chemicalssmlauncher`, `japan_ballista`, WC2 ballista/catapult/siege-engine, `ixian_ixmissiletank` /
  `ixsiegetank`, `steelconsortium_dagger` / `hammerheadartillerytank`, `ordos_deviatorartillery`,
  `latinsyndicate_burrito`, `futuretech_athenacannon`, `cabal_artilleryspider`, `asianalliance_viper`,
  `tkm_dronepodtruck` / `tornadoglauncher`.
- **Deploy siege tanks** (`terran_siegetank` 150k HP, `siege_tank`, `missile_tank`) = tanky DEPLOY
  specials → FLAG (their own handling, not fragile Light artillery).

---

## ★ FUTURE-AUDIT RULES (maintainer 2026-07-26 — record now, wire into `run_all.sh` later)

1. **Projectile speed = range ÷ 2** for every weapon (e.g. range 15000 → projectile speed 7500).
   **EXCEPTION:** interceptable / shoot-down-able missiles (e.g. the **V3**) keep their own (slower)
   speed so they *can* be shot down. → a **projectile-speed audit** will enforce this.
2. **Weapon type ↔ unit type binding:** each unit CLASS is bound to a weapon TYPE, and a unit's weapon
   must inherit the weapon type bound to its class — unit type and weapon type are always linked. → a
   **weapon-type-binding audit** will enforce this (depends on the WeaponClass sidecar + the §13
   warhead library being wired in).

---

## ★ DEFENSE PRICING FORMULA — 3-input (maintainer 2026-07-26) — implemented in `formula.py`

Static defenses have no speed → the 4-input v2 formula's speed term is meaningless (like "speed 100" as
a placeholder). **Defenses use a new 3-input formula** (HP, Range, DPS) built with the SAME
degree-1 / degree-2 / degree-3 logic, symmetric across all three inputs, so O = P = Q = cost0 at the
baseline:

    h = hp/hp0 ; r = (range/range0)*special ; d = dps/dps0
    O = (h + r + d)/3        * cost0   (degree 1 — mean of the singles)
    P = (h*r + h*d + r*d)/3  * cost0   (degree 2 — mean of the pairs)
    Q = (h * r * d)          * cost0   (degree 3 — the triple product)
    Cost = (O + P + Q)/3

`formula.py`: `class_baseline_estimators_3` / `class_baseline_price_3` /
`solve_class_baseline_range_3` (price stays LINEAR in range → closed-form solve). Verified numerically:
- baseline → O=P=Q=cost0, price=cost0 ✓
- **fully symmetric:** 2× any ONE input → **1.667×** cost (all three interchangeable — the "same logic").
- 2×HP + 2×DPS + same range → **2.778×** (vs the mobile 2.5×); 2× all three → **4.667×**.

**★ ONLY for defenses** (mobile classes keep the 4-input formula + 2.5× verifier). **OPEN — defense
verifier convention:** pick (a) 2×HP + 2×DPS + same range = 2.778×, (b) a 2×-all = 4.667× tripwire, or
(c) another.

## ★ REARMABLE AIRCRAFT — needs its OWN formula (maintainer 2026-07-26; when we reach aircraft)

Bombers / rearmable aircraft return to base to reload, so the weapon `ReloadDelay` (currently a
placeholder ~250 multiplier) does NOT reflect their real damage cadence — the same nonsense as
"speed 100" for defenses. **Effective DPS must be driven by the SORTIE cycle** (fly out → attack → fly
back → rearm), not the weapon reload. **TODO: derive an aircraft-specific formula when we lock the
aircraft classes** (applies to all return-to-base aircraft; loitering gunships/fighters may keep the
normal form — decide per subclass).

## ★ DEFENSE CLASS RULES (maintainer 2026-07-26)

**Formula:** the 3-input defense formula (HP, Range, DPS — above). **★ Verifier convention = 2.5×HP +
2.5×DPS + same range → exactly 4.0× cost** (maintainer 2026-07-26 — the ONLY "both-round" point of the
3-input formula: price = (2·2.5+1)²/9 = 36/9 = 4). Replaces the earlier 2.778×. More extreme band, but
clean. **Caveat:** 4× only makes sense where a class spans a real range (Basic/AntiAir/Advanced);
**SuperDefense is a narrow epic tier** (4000–5000), so 4× of 4000 = 16000 has no real unit → Super uses
NO 4× verifier (see its section).

**★ Defense HP granularity + regen (maintainer 2026-07-26):** defenses regenerate at a **FLAT 10 HP per
step** (NOT HP-scaled like units), so their self-heal is constant regardless of HP ⇒ **defense HP may be
in EITHER 1000 or 2500 steps** (both fine). No per-actor `Step = HP/n` for defenses.

**★ Defense ARMOR scheme (already in the templates, `defaults.yaml` 2005–2071):** BasicDefense =
**Concrete**, AntiAirDefense = **Concrete**, AdvancedDefense = **Steel**, SuperDefense = **Steel**,
Bunker = **Steel**. Build-time modifiers: Basic **100** (longest), Advanced/Bunker **75**, AntiAir/Super
**50** (quickest). *(Advanced/Super build-times may need to lengthen to match "plan-ahead" intent +
the new power/cost ratios — review in the implementation pass.)*

## ◧ DEFENSE TEMPLATE ROSTER — grew 5 → 7 (maintainer 2026-07-26; FINALIZE + BUILD after the compact)

**Common:** verifier convention **2.5×HP + 2.5×DPS + same range → 4× cost**; power/cost Basic&AntiAir /20,
Advanced /10, Super /5; armor Basic/AntiAir = Concrete, Advanced/Super/Bunker = Steel; regen flat 10/step.

1. **`^BasicDefenseTemplate`** — baseline GDI Guard Tower (100k/7000/DPS400/**500**). **Verifier = Protoss
   Photon Cannon @ 2000** (4× of 500 — maintainer: "we don't even need to change anything"). Concrete, T1.
2. **NEW `^EarlyAdvancedDefenseTemplate`** — early-game advanced defenses (**TD Nod Laser Tower, Protoss
   Photon Cannon**). **SHARES the BasicDefense formula + SAME weights**; the ONLY difference = it is an
   **EXCEPTION to the "must be Tier 3" rule → allowed on Tier 1/2** (and the defense audit must accept
   that). The Photon Cannon (2000) IS the shared Basic verifier point.
3. **`^AntiAirDefenseTemplate`** — pure AA. Flak Cannon (150k/12500/DPS1000/**600**) → Air Defender @ 2400.
   Range band 10000–15000. Concrete, quickest build.
4. **NEW hybrid `^AdvancedAntiAirDefenseTemplate`** (name TBD) — **between AntiAir and Advanced, range
   EXACTLY 10000** (where the AntiAir band 10000–15000 meets the Advanced band 8000–10000). For **advanced
   turrets that ALSO shoot air and are their faction's ONLY AA**: **Ixian Missile Tower**
   (`ixian_rocketturret`), **Japan Ballista Tower** (`japan_ballistatower`). **Allowed on Tier 2**, accepted
   by the defense audit. **★ SOLVES THE IXIAN AA GAP** — the Missile Tower stays AA-capable in THIS class;
   the earlier "move it to pure Advanced T3" plan is **DROPPED**.
5. **`^AdvancedDefenseTemplate`** — Advanced Guard Tower (200k/9000/DPS~800/**1000**), Steel, T3. **★
   VERIFIER STILL OPEN:** the **Cabal Obelisk Prime** is the strongest advanced defense (ideal verifier)
   BUT its **charge-delay K 0.75** mismatches the baseline's K 1.0, breaking the clean 4× identity.
   **Decide after compact** (accept K-shift / matched-K baseline / non-charge verifier).
6. **`^SuperDefenseTemplate`** — epic capstone = **2×2 footprint AND cost ≥ ~4000**. Plasma Cannon baseline.
   **★ OPEN: cost 4000 (clean boundary, epic ceiling, no 4× verifier — RECOMMEND) vs 2500 (overlaps).**
7. **`^BunkerTemplate`** — NOT YET DEFINED. Price = HP + cargo slots; Bastion (defense+bunker) = K1.25.

**★ DECISIONS PENDING AFTER COMPACT:** (4) name the hybrid template; (5) Advanced verifier + the Obelisk
Prime charge-K problem; (6) Super baseline 4000 vs 2500; (7) define Bunker; then **BUILD all defense
templates in defaults.yaml (boot-gated)**. Plus the standing vehicle verifiers (ArtilleryTank, Artillery).

**★ Power-to-Cost per defense TYPE** (was a uniform `cost/20`):
| Type | Power draw | Build-time modifier |
|---|---|---|
| BasicDefense | **cost / 20** | LONGEST (early-game — fine as is) |
| AntiAirDefense | **cost / 20** | QUICKEST (specialized, need it fast) |
| AdvancedDefense | **cost / 10** | long (the thing you plan in advance) |
| SuperDefense | **cost / 5** | long (scale accordingly) |
Build-time modifiers scale with the power/cost ratio.

**★ SuperDefense membership rule:** any defense with a **footprint bigger than 1×1 cell** (Building
`Dimensions` > `1,1`) — **EXCEPT anti-air turrets** — is a SuperDefense (verified: Grand Cannon =
`2,2`). PLUS **1×1 defenses that are extremely powerful** (large HP AND large cost) also qualify —
cross-reference the roster. Named members: `ra2_allies_grandcannon` + Latin **SML turret**, Asian
Alliance **plasma cannon**, Ixian **storm lasher**, … (full footprint scan when we lock SuperDefense).

**★ Bunker rules:**
- **Pure bunker** (holds cargo, no own weapon) → price scales with **HP + number of cargo slots** (the
  garrison capacity is the value).
- **Combined defense + bunker** (e.g. **RA1 Bastion** — own weapon AND holds cargo) → **special K =
  1.25** (same as armed vehicle transports — weaker stats at the same price).
- **Pillbox with a FIXED garrison** (an infantry unit permanently inside, whose weapon IS the pillbox's
  weapon) → priced as a **BasicDefense** on that garrisoned weapon's DPS (the garrison = the weapon).

---

## ✅ BasicDefense — LOCKED baseline 2026-07-26 (range band 6500–7500)

| | Unit | HP | Range | DPS | cost0 |
|---|---|--:|--:|--:|--:|
| **Baseline** | `td_gdi_guardtower` | **100000** | **7000** | **400** | **500** |
| **Verifier** | `japan_japanesemgnest` | **250000** | 7000 | **1000** | **2000** (4×) |

- All BasicDefenses **range 6500–7500** (7000 middle). Power draw = **cost / 20** (guardtower 500 →
  power 25), longest build-time modifier.
- Verifier = Japanese MG Nest restatted to **2.5×HP + 2.5×DPS + same range = 4× → 2000** (250000 HP /
  DPS 1000 / 7000). Current MG Nest = 110000 HP / dual MG (dmg 4000 ×5 / rd 25 bd 5) / cost 1000.
- Baseline guardtower restat: HP 60000→**100000**, range 6720→**7000**, weapon → **DPS 400**, keep
  cost 500.

---

## ✅ AntiAirDefense — LOCKED 2026-07-26 (pure AA, long range, Concrete armor, quickest build)

| | Unit | HP | Range | Dmg | Reload | DPS | cost0 |
|---|---|--:|--:|--:|--:|--:|--:|
| **Baseline** | `ra2_soviets_flakcannon` | **150000** | **12500** | **12000** | **12** | **1000** | **600** |
| **Verifier** | `latinsyndicate_latinaadefender` | **375000** | 12500 | 30000 | 12 | **2500** | **2400** |

- DPS = 12000 / 12 = **1000** (burst 1). **Range band 10000–15000** (12500 middle). Armor **Concrete**,
  power = cost/20, quickest build time. **Pure-AA priced directly on the AA weapon** (no ground-weapon
  split — confirmed).
- Verifier = Latin **Air Defender** (dual flak, naturally tankier) → **2.5×HP + 2.5×DPS + same range =
  4× → 2400** (375000 HP / DPS 2500 / 12500). ✓ 4× convention.
- HP 150000 / 375000 clean (flat-10 regen → any 1000/2500 step is fine).

---

## ⚠ WEAPON-CLASS EXTRACTION BUG (found 2026-07-26) — extractor ≠ authoritative

`extract_stats.py`'s `design_weapon_class` is WRONG — it averages a weapon's **versus-armor templates**
via a hard-coded `_WEAPON_CLASS_OVERRIDES` table, instead of reading the authoritative sidecar
`weapon_classes.yaml` for the weapon's **own class**. Two symptoms found:
- **Guard tower → 1.0833** = mean of its 6 recognized versus templates `[Grenade 1.0, Shrapnel 1.0,
  Flak 1.0, HeavyAA 1.25, HeavyMissile 1.25, MediumMissile 1.0]` = 6.5/6 = 13/12. (Should be its OWN
  class ≈ 1.0.) `^TankDestroyerCannon` → None (unrecognized).
- **Obelisk → 1.0** because the override table has **`LaserWeapon: 1.0`** — WRONG; sidecar + legacy
  Excel say **1.25**. Also **`ShrapnelWeapon` should be 1.25** (Heavy), table has 1.0.

**★ THE RULE IS AUTOMATIC (ARMOR_SYSTEM.md — canonical Versus law):** a weapon's class = read from its
main SpreadDamage warhead's **`Versus: Shield`** value — Light/Medium/Heavy = step 6/5/4 = Shield
**110 / 125 / 140 → 0.75 / 1.0 / 1.25** (+15 shield = +0.25; superheavy bands 155/170/185 → 1.5/1.75/2.0).
Multi-warhead weapons = arithmetic mean. So `^Grenade` (Light Demolition, Shield 110) = **0.75**,
`^ShrapnelWeapon` (Medium Concussion, Shield 125) = **1.0** — automatic, no hand list.

**✅ FIXED 2026-07-26:** `extract_stats.py` now derives `design_weapon_class` **automatically from the
Versus Shield** (`weapon_class_from_versus`, `source="versus_shield"`) — self-correcting from the yaml,
so a stale value can't recur. The `weapon_classes.yaml` sidecar is the **fallback** for weapons with no
Versus of their own; the stale hard-coded override table was deleted (it had LaserWeapon 1.0, Grenade
1.0 — both wrong; Shield-derived gives 1.25 / 0.75 correctly). **`^ShrapnelWeapon` reverted to 1.0**
(maintainer: shrapnel was right, GRENADE was the wrong one — now 0.75 via Shield). New gate
**`--check-weapon-classes`** fails on any template lacking BOTH a Versus Shield and a sidecar entry;
after the automatic law it's down from 48 → **10** (targeting-only `^AADeployTargeting`/`^DeployTargeting`
→ IGNORE set; abstract parents `^MissileWeapon`/`^MG`/`^LightMG`/`^AntiGroundMissile`; `^SnipeWeapon` →
0.75; `^D2K_Cannon`/`^DRPlasmaWeapon`/`^TSDefaultMissile`). Finish those 10, then wire into `run_all.sh`.
Ledgers pick up the corrected classes on the next sanctioned `extract_stats` run.

**★ Robustness upgrade (to build): classify by the Versus FLOOR/STEP, not just Shield** — the Shield can
be non-standard (Charged Tesla Shield = 200, an EMP bonus). The floor is the reliable signal:
`class = 0.75 + (floor − 10)/60` → floor 10/25/40/55 = 0.75/1.0/1.25/1.5. Cross-check floor vs Shield vs
the sidecar and **auto-update the sidecar** on mismatch (single always-accurate source).
**Off-ladder EXCEPTIONS (hard-set in the sidecar):** `^ToxicWeapon` = **0.5**; `^TeslaChargedWeapon` +
`^NuclearWarhead` = **1.5** (Superheavy, step 3). Sidecar: `^NuclearWarhead` 1.25 → **1.5**.

**★ NUCLEAR WARHEAD Versus fix — CONFIRMED 2026-07-26 (BOOT-GATED weapons.yaml edit, apply in the pass):**
`^NuclearWarhead` is currently a **Heavy** profile (step 4, 100→40, Shield 140 = class 1.25). Change to
**Superheavy (step 3)** to match its 1.5 class — KEEP the armor order, change the step 4→3:
- **Main warhead:** Superheavy 100, then −3 per row (Plate 97, Heavy 94, Flak 91, Medium 88, None 85,
  Light 82, Heroic 79, Scout 76, Steel 73, Concrete 70, Wood 67, Spaceship 64, Helicopter 61, Bomber 58,
  **Fighter 55** floor), **Shield 155** (standard top+floor; NOT the Tesla's 200 — nukes get no shield
  bonus). **HAZMAT 50 kept.**
- **% warhead:** superheavy window **30 → 15** (Superheavy 30 … Fighter 15, step 1), **Shield 45** (was
  the Heavy window 25→10 / Shield 35). Matches the Charged Tesla's % ladder (30→15).

## ✅ AdvancedDefense — LOCKED baseline 2026-07-26 (1×1, Steel armor, plan-ahead build)

| | Unit | HP | Range | DPS | cost0 |
|---|---|--:|--:|--:|--:|
| | Unit | HP | Range | DPS | cost0 |
|---|---|--:|--:|--:|--:|
| **Baseline** | `td_gdi_advancedguardtower` | 200000 | **9000** | **~800** | **1000** |
| **Verifier** | `ixian_rocketturret` (1×1) | 500000 | 9000 | 2000 | **4000** |

- **LOCKED idea B (maintainer 2026-07-26):** cost0 **1000**, **DPS trimmed 1250 → ~800** — a clean
  2×HP / 2×DPS / +range step over Basic (100k/400/500), fairly priced. Range band **8000–10000**, Steel
  armor, power = cost/10, heavy-missile-only (wc 1.25). Verifier = **Ixian rocket turret** at 2.5×HP +
  2.5×DPS + same range = **4× → 4000** (= the SuperDefense floor, a clean boundary).
- **Ixian rocket turret → Tier 3** (maintainer confirmed). Creates an **Ixian AA gap — STILL OPEN.**
  *(`d2k_airdefenseplatform` is NOT usable — it's the upcoming HARKONNEN faction's flying spaceship, not
  a turret. Reverted 2026-07-26.)* Full `d2k.yaml` scan: **no unused static AA turret exists** — every
  AA entry is already in the packs (rocket turret, ordos autogun) or is an aircraft. Dune's only AA
  defense was the Rocket Turret. **OPTIONS for the Ixian AA (maintainer to pick):**
  (1) **Ixian Railgun Drone** (`ixian_railgundrone`, exists, mobile AA, high-tech — their AA is mobile,
  not a turret); (2) give the **Ixian machine-gun / gun turret an AA mode** (compact, reuses a turret);
  (3) **keep a light Rocket Turret at T2** (Ixian AA) + the heavier Missile Tower at T3 (the verifier);
  (4) **new Ixian AA turret** (railgun/needle-flak, T2, ~800–1000 — fits their high-tech identity).

## ✅ SuperDefense — baseline 2026-07-26 (epic capstone, 2×2, Steel, power = cost/5)

**★ CLEAR Advanced-vs-Super distinction (footprint scan 2026-07-26):** footprint ALONE fails — the
obelisks are **2×2 but Advanced** (TD obelisk 1×1/1800, TS obelisk 2×2/2200, Cabal obelisk 2×2/2400,
Quantum Cannon 2×2/2000, Tesla/Prism 2000/2200). The true super defenses are **2×2 AND expensive**
(plasma 4000, grand cannon/SML/storm lasher 5000). So the rule is **SuperDefense = 2×2 footprint AND
cost ≥ ~4000** (the faction's capstone); everything cheaper = Advanced (any footprint). There's a clean
natural GAP between the obelisks (~2400) and the supers (~4000).

**Baseline = `asianalliance_plasmacannon`** (300000 HP, range 14000, 2×2, PlasmaWeapon 1.25, no charge).
Members (MOVE out of AdvancedDefense): `ra2_allies_grandcannon`, `ixian_stormlasher`,
`latinsyndicate_smlturret` (all 5000, 2×2).
**⚠ BASELINE-COST DECISION:** (a) keep plasma **@4000** → clean boundary (Advanced verifier 4000 = Super
floor 4000), Super = **epic ceiling, NO 4× verifier** (4× of 4000 = 16000 has no unit); OR (b) maintainer's
idea — plasma **@2500** → 4× verifier = **10000** (= BFG-10k price, but the BFG is epic/build-limit-1, its
OWN class → need a different 10000 unit), but 2500 **overlaps** the Advanced band (1000→4000). **Recommend
(a):** cleaner boundary, keeps idea B intact. `steelconsortium_bfg10000` stays its own epic class (BuildLimit 1).
`cabal_heavycabalobelisk` (2400, charge) is NOT Super (charge → Advanced/own handling).

**★ Tesla Coil EXEMPT from charge-up rule** (maintainer 2026-07-26): both RA1+RA2 tesla coils have a
QUICK charge (25) and are already strong → NO 0.75 discount, NO reload=2×charge; **K = 1.25 (EMP)**;
effective reload still 125 (RA1: ReloadDelay 100 + InitialChargeDelay 25). See.

---

## 🔤 NAMING FIX — dropped umlauts (maintainer 2026-07-26) — BOOT-GATED, via rename tool

Rule: umlauts transliterate to the base letter (ü→u, ö→o, ä→a, ß→ss). A roster scan (display-name
umlaut vs actor id) found **only two ids that DROPPED the umlaut instead of transliterating:**
- `naxis_brummbr` → **`naxis_brummbar`** (Brummbär)
- `naxis_kbelwagen` → **`naxis_kubelwagen`** (Kübelwagen)

`schwarzermond_ubermensch` (Übermensch) is already correct (Ü→u); `naxis_frank` is a codename (not
name-derived). **To fix via `tools/rename/safe_rename.py` + a `rename_map` (touches rules/sequences/weapons/
cameos/AI/fluent), then BOOT-GATE.** (Also the `naxis_frank` display name "Übermutant" shows a mojibake
`�` — check the source file encoding separately.)
