# Class moves — completing the 2026-07-21 template split, one class at a time

_Working document. One section per class, in the order they are done. Each section is a PROPOSAL
until the maintainer approves it; approved sections still need `apply_balance --confirm` where they
move a number, and a **boot gate** in every case (they edit `mods/**`)._

Governed by `BASELINE_ACTOR_REVIEW.md` (archived; content merged into this document). Enforced by
`tools/audit/audit_class_templates.py`.

---

## 0. ⭐ Why five templates are dead: a split that was designed and never applied

`^RocketTrooperInfantryTemplate` documents it in its own comment:

> *"Formula v2 ROCKET TROOPER class (design 2026-07-21): dedicated missile-based anti-vehicle /
> anti-air infantry. **Splits from the old AntiTankAntiAir template, which mixed bullet-based AA
> infantry into special forces.**"*

`^ArcherInfantryTemplate` carries the same 2026-07-21 stamp. So the five dead templates —
`^ArcherInfantryTemplate`, `^HeavySniperInfantryTemplate`, `^RocketTrooperInfantryTemplate`,
`^SupportInfantryTemplate`, `^SuperDefenseTemplate` — are not abandoned ideas. **They are the
unapplied half of a designed split.** The units they were meant to hold are still sitting in the
templates the split was supposed to empty.

⛔ **That is why `archer` and `heavy_sniper` are the only two classes whose member count went DOWN
against the ledger, and why both are SIGNED against a template with zero inheritors.**

---

## 1. `archer` — ⭐ PROPOSAL (revised: 8 members, not 4)

⛔ **My first roster was wrong and the maintainer corrected it twice.** I searched by NAME
(`archer|bow|arrow`) and found 4. The maintainer: *"The orc axe throwers and headhunter are the
equivalent to the elven archers so they must be in the same archer template."* Correct — and
enumerating the bucket structurally instead of by name found **8**, including
`wc2_humans_elvenranger`, which has neither "archer" nor "bow" nor "arrow" in its name.

⭐ **The reliable query is the template's own definition, not the unit's name.** All eight sit in
`^AntiTankAntiAirInfantryTemplate` firing `Missile`-projectile thrown/drawn weapons —
`wc2arrowFire`, `wc2axeFire`, `AsianMaidenBow`. That is exactly the population
`^ArcherInfantryTemplate` describes ("projectile-arc infantry using the MISSILE projectile … hits
air") and exactly what the 2026-07-21 split was meant to remove from AT/AA.

### The roster, and the repricing

Anchor = cheapest = **`asianalliance_veteranarcher` @ 450**.

| was | → new | ×cost0 | HP | actor | why it moves |
|--:|--:|--:|--:|---|---|
| 450 | **450** | 1.00 | 14,000 | `asianalliance_veteranarcher` | anchor |
| 500 | **500** | 1.11 | 20,000 | `japan_archermaiden` | lowest HP of the 500 group keeps the round number |
| 500 | **550** | 1.22 | 30,000 | `wc2_orcs_trollaxethrower` | collision |
| 500 | **600** | 1.33 | 30,000 | `wc2_orcs_trollberserker` | collision; the axethrower's upgrade form, so it prices above it |
| 600 | **650** | 1.44 | 25,000 | `wc2_humans_elvenarcher` | collision |
| 600 | **700** | 1.56 | 25,000 | `wc2_humans_elvenranger` | collision; the archer's upgrade form |
| 1,000 | **1,000** | 2.22 | 40,000 | `wc2_orcs_trollheadhunter` | unchanged |
| 1,100 | **1,100** | 2.44 | 35,000 | `wc2_humans_highelvenarcher` | unchanged |

| | measured | target |
|---|--:|--:|
| occupancy in the target band | **8 of 8 = 100%** | >= 80% |
| spread | **2.44x** | fits 2.50x |
| **sigma_log** | **0.296** | 0.3575 |
| unique prices, all multiples of 50 | ✅ | required |

⚠ **Four units need +50 or +100, and that is a balance number** — so it goes through
`apply_balance --confirm` on a maintainer order, not a hand edit (CLAUDE.md rule 3).

⚠ **The tie-break needs a ruling, because mine was luck.** `trollaxethrower`/`trollberserker` and
`elvenarcher`/`elvenranger` are stat-identical pairs (500/30,000 and 600/25,000). I broke the tie
alphabetically and it happened to put each upgrade form above its base. That is not a rule. The
principled tie-break is **the tech/upgrade relationship**, and it should be stated rather than
relied on by accident.

### Two units that look like archers and are not

* `ra1_allies_longbow` — an Apache gunship (`^HelicopterTemplate` ✅)
* `td_gdi_archerartillery` — the British Archer SPG (`^ArtilleryTankTemplate` ✅)

### ⛔ And one separate defect found on the way

`wc2_orcs_kodobeast` (1,000) throws the same `wc2axeFire` and sits in
`^AntiTankAntiAirInfantryTemplate` — but it inherits **`^WC2Vehicle`**. It is a **vehicle in an
infantry class template**, which is a different defect from the eight above and needs its own
ruling: a mounted axe-thrower is arguably a `scout_vehicle` or a `light_tank`, not an archer.
⚠ Its `Tooltip` also declares `Name:` twice (`Kodo Beast`, then `garrisoned`).

### ⛔ The bucket this comes out of needs a 3-way split, not a 1-way move

`^AntiTankAntiAirInfantryTemplate` holds **44** members and is the grab-bag the 2026-07-21 design
was written to break up. Measured by projectile:

| destination | n | examples |
|---|--:|---|
| **`^ArcherInfantryTemplate`** (this section) | 8 | thrown/drawn `Missile` weapons |
| **`^RocketTrooperInfantryTemplate`** — currently DEAD | ~20 | `td_gdi_rocketsoldier`, `ra1_allies_alliedrocketsoldier`, `ordos_rockettrooper`, `cabal_rocketcyborg` … all `Missile` rockets/bazookas |
| **stays, or goes elsewhere** | ~16 | `Bullet`/`InstantHit` AA — and several that are plainly misfiled: `terran_marine` (basic infantry), `zerg_hydralisk` (3,314), `protoss_hightemplar` (a PsiStorm caster), `ra1_soviets_dragunovantimaterialsniper` (a sniper) |

⭐ **That is the real shape of the job**: filling `^RocketTrooperInfantryTemplate` is the same task
as this one and roughly 20 units in size, and it empties most of the grab-bag at the same time.

### Open questions for this class

1. **Is `Armor: None` intended for archers?** `^ArcherInfantryTemplate` declares it; all eight ship
   as `Flak` today, so the template has never been tested against a real member.
2. **Do archers keep hitting air?** The template says *"Hits air"* — that is why they were in AT/AA.
3. **The tie-break rule** for stat-identical upgrade pairs (above).
4. **`wc2_orcs_kodobeast`** — which class does a mounted axe-thrower belong to?


---

## 2. The unclassified 91 — ✅ APPROVED 2026-09-02 (A3 + A4)

Every **buildable, mobile** actor carrying no full class template. 67 have nothing at all; 24 carry
only an epic add-on. Buildings are out of scope (§4.5 of `BASELINE_ACTOR_REVIEW.md`, archived), upgrades are
not units.

✅ **Maintainer approved 2.1, 2.2, 2.3 and 2.6 outright**, ruled that ground/naval transports get
their **own template**, and made three further rulings recorded below. Three units are deliberately
deferred to be handled one at a time.

**Three NEW templates come out of this pass** — `^TransportVehicleTemplate`,
`^SuicideVehicleTemplate` and `^CarrierDroneTemplate` (A6) — and one DEAD template,
`^SupportInfantryTemplate`, is filled by its obvious tenants.

### 2.1 ⭐ Engineers → `^SupportInfantryTemplate` *(fills a DEAD template)* — 11 units, high confidence

All share `DefuseKit, LeechDisinfect`:
`engineer` · `ra1_engineer` · `ra2_allies_engineer` · `ra2_soviets_engineer` ·
`asianalliance_engineer` · `futuretech_engineer` · `latinsyndicate_engineer` ·
`steelconsortium_engineer` · `tkm_engineer` · `yuri_engineer` · `E6` — all 500cr / 5,000 HP.

⭐ **And this reunites them with four engineers currently mis-filed in `^SniperInfantryTemplate`**
(`TSENGINEER`, `forgotten_engineer`, `ts_gdi_engineer`, `ts_nod_engineer` — found in §1). **15
engineers in one class**, and one of the five dead templates is filled by its obvious tenants.

### 2.2 ⭐ Support vehicles → `^SupportVehicleTemplate` — 6 units, high confidence

| unit | cost | role |
|---|--:|---|
| `ra1_allies_minelayer` | 800 | minelayer |
| `ts_nod_mobilerepairvehicle` | 1,000 | repair |
| `ts_gdi_mobilesensorarray` | 1,100 | detection |
| `ts_nod_mobilestealthgenerator` | 1,500 | cloak field |
| `ra1_allies_mobilegapgenerator` | 5,000 | shroud — ⚠ armed with `dummytargeting` (C2) |
| `ra1_allies_mobileradarjammer` | 5,000 | jammer |

### 2.3 ⭐ Air transports → `^UnarmedTransportHelicopterTemplate` — 7 units, high confidence

`forgotten_chinook` 700 · `forgotten_carryall` 750 · `ts_gdi_carryall` 750 · `carryall` 2,000 ·
`carryall.paradrop` 5,000 · `carryall.reinforce` 5,000 · `wc2_orc_eye_of_kilrogg` 2,000 (unarmed scout)

⚠ **Two ARMED carryalls do not belong here**: `ordos_advancedcarryall` (2,000) and
`carryall_reinforce.ordos` (5,000) carry `d2kCarryallChainGun` — an *armed* transport helicopter, so
`^HelicopterTemplate` instead.

### 2.4 ✅ Transports → **NEW `^TransportVehicleTemplate`** — 11 units, one class

**Ruled: one template for all 11.** Measured, they share an identical cargo contract
(`Infantry, Hacker, Fremen, Vehicle`) and span 500–1,200 — a **2.4x spread that already fits the
2.5x band**, anchored on the cheapest at 500. They differ only in *how* they cross water:

| locomotor | units |
|---|---|
| `lcraft` | `CNCRSS` 500 · `LST` 500 · `ra1_navaltransport` 500 |
| `hover` | `ra2lcrf` 750 · `ra2sapc` 750 · `yrhovr` 750 · `ts_gdi_hover` 1,200 · `ts_nod_hover` 1,200 · `cabal_lcraft` 1,200 |
| `naval` | `wc2_human_transport` 1,000 · `wc2_orc_transport` 1,000 |

⭐ **Locomotor is a movement detail, not a role.** All eleven do the same job.

### 2.4a ✅ Oil tankers → `^HarvesterTemplate` — and ⛔ a BROKEN MECHANIC recorded

`wc2_human_oil_tanker` and `wc2_orc_oil_tanker` (400cr, `naval`, **no cargo**) are not transports —
they are WC2 resource ships, found only because the locomotor check separated them from 2.4.

⛔ **Maintainer, recorded as a defect, not a classification problem:** *"the game mechanic is not
working correctly. What they should do is travel between the two naval buildings, load up in one and
move to the other. Currently we can't do that. Also we don't have oil patches in the water — so what
is the purpose?"*

So the class is `^HarvesterTemplate`, **but the unit currently has no working economy loop**: no
water oil patches to harvest from, and no building-to-building haul route. ⚠ **Pricing them before
that is settled prices a unit that does nothing.** Flagged for the balance pipeline as a
quarantine candidate (`docs/design/balance_exceptions.yaml`) until the mechanic works.

### 2.4b (superseded — see 2.4)

`CNCRSS` 500 · `LST` 500 · `ra1_navaltransport` 500 · `ra2lcrf` 750 · `ra2sapc` 750 · `yrhovr` 750 ·
`ts_gdi_hover` 1,200 · `ts_nod_hover` 1,200 · `cabal_lcraft` 1,200 ·
`wc2_human_transport` / `wc2_orc_transport` 1,000

⛔ **There is no ground- or naval-transport template.** `^SupportVehicleTemplate` would take them,
but a landing craft is not a support vehicle. This group needs a ruling: new template, or fold into
support?

### 2.5 ✅ Suicide units → **NEW `^SuicideVehicleTemplate`** — 5 units

`asianalliance_oiltruck` 1,000 · `latinsyndicate_demolitiontruck` 1,500 ·
`ra1_soviets_nukedemotruck` 1,500 · `latinsyndicate_nuketruck` 3,000 *(epic)* — all
`DemoTruckTargeting`.

**Ruled: their own template.** ⭐ The reasoning is a pricing one, and it is why a class exists at
all: a one-shot unit **cannot be priced on DPS**. Its damage is a single burst and its survivability
is irrelevant the moment it fires, so pricing it against sustained line-breakers reads as wildly
wrong in either direction. `ra1_soviets_madtank` joins them — it is a suicide-by-shockwave epic, and
it keeps its `^EpicVehicleTemplate` add-on.

### 2.6 The 24 epic-only → base class from role (A4)

Each keeps `^EpicVehicleTemplate` as the add-on and gains a base class. Proposed:

| base class | units |
|---|---|
| `^HighTechTankTemplate` | `forgotten_chemicalmammothtank`, `forgotten_experimentalmammothtank`, `ts_gdi_mammothprototype`, `ts_gdi_mammothmkii`, `ra1_soviets_monstertank`, `futuretech_futuretank`, `tkm_sandmarine`, `tkm_bigshiee`, `naxis_ratte`, `japan_exorcistoitank` |
| `^MainBattleTankTemplate` | `tkm_t30`, `schwarzermond_dalek`, `ra1_allies_chronotank`, `naxis_nokana` |
| `^ArtilleryTankTemplate` | `latinsyndicate_topolm`, `zerg_hermit` |
| `^LineBreakerTemplate` | `japan_shogunexecutioner`, `cabal_coredefender`, `protoss_idol` |
| `^SupportVehicleTemplate` | `ixian_ixprojector` (EMP), `td_gdi_defenserig`, `forgotten_nomadbarracks` |
| *(2.5 demolition)* | `latinsyndicate_nuketruck` |
| ⚠ unresolved | `ra1_soviets_madtank` — a suicide-by-shockwave epic; 2.5 or its own thing |

### 2.7 ⚠ Not units — propose A7 separation, not a class

| group | units | why |
|---|---|---|
| critters | `wc2_critter_boar`, `_helboar`, `_seal`, `_sheep`, `sc_zerg_larva` | ambient/critter fauna, 50–100cr, unarmed |
| markers | `eden_impulseitems`, `_2`, `_3` | **HP 1**, unarmed, 300–1,000cr — not units |
| mobile buildings | `japan_corepowerplant` · `corebarracks` · `coreservicedepot` · `coreairfield` · `corewarfactory` · `coreradar` · `corerefinery` · `coretechcenter` (8) | Japan's mobile-base system — buildings that move; pricing them as vehicles distorts any class |
| | `PLYMOUTH_CONVEC_STRUCTURE_FACTORY` 5,000 | same shape, Outpost-2 import |

### 2.8 ⚠ Still open — three DEFERRED by ruling, five proposed

✅ **Deferred, to be brought one at a time with full stats:** `RAPT`, `tsprobe`,
`wc2_neutral_daemon`. All three are roles the taxonomy genuinely lacks — a melee vehicle, an air
scout, an air attacker — and the maintainer chose to see them individually rather than force them
into a nearest neighbour.

⚠ **Five still carry only my proposed read and need a call:**

| unit | cost | evidence | my read |
|---|--:|---|---|
| `tsldrone` | 150 | `TSLimpetBomb_EMP`, 11,500 HP | limpet drone — `^ScoutVehicleTemplate`? |
| `tsprobe` | 600 | air, `TSHSeekerTargeting` | air scout — no air-scout class exists |
| `tsaegis` | 1,200 | `TSAegisMissile`, 80,000 HP | `^AntiAirVehicleTemplate` |
| `RAPT` | 1,000 | `claw`, 100,000 HP | a melee vehicle — no class fits |
| `devastator` | 3,000 | `DevBullet`, 550,000 HP | D2k Devastator → `^HighTechTankTemplate` |
| `ra1_soviets_gorynychtank` | 1,300 | `BigFlamer`, 150,000 HP | `^LineBreakerTemplate` (flame) |
| `wc2_neutral_daemon` | 2,000 | air, `wc2daemonFire` | air attacker → `^FighterTemplate`? |
| `ordos_saboteur` | 300 | `GenericC4` | 2.1 engineers, or its own saboteur role |

⚠ **`ra1_allies_chronotank` also appears in §1's multi-template list** — resolve there first.

### 2.9 ✅ The approved tally

| destination | n | status |
|---|--:|---|
| `^SupportInfantryTemplate` *(dead → filled)* | 11 + **4 rescued from `^SniperInfantryTemplate`** = **15** | ✅ approved |
| `^SupportVehicleTemplate` | 6 | ✅ approved |
| `^UnarmedTransportHelicopterTemplate` | 7 | ✅ approved |
| `^HelicopterTemplate` (the 2 ARMED carryalls) | 2 | ✅ approved |
| **NEW `^TransportVehicleTemplate`** | 11 | ✅ ruled |
| **NEW `^SuicideVehicleTemplate`** | 5 | ✅ ruled |
| `^HarvesterTemplate` (oil tankers) | 2 | ✅ ruled — ⛔ mechanic broken, quarantine first |
| the epic 24 → base class + add-on | 24 | ✅ approved |
| **A7 separation, not a class** | 17 | ⚠ proposed (5 critters, 3 `eden_impulseitems`, 9 mobile buildings) |
| deferred, one at a time | 3 | ✅ ruled |
| still needing a call | 5 | ⚠ open |

⚠ **Every line here is a yaml edit to `mods/**` — engine content.** Boot gate before commit
(CLAUDE.md rule 1). The three new templates must be written before the units can inherit them, and
`^SuicideVehicleTemplate` needs a pricing shape that is not DPS-based before its members can be
priced at all.

---

## 3. Conflict group 1 — `ScoutInfantry` (template) vs `support` (tag), 6 units

Worked one by one at the maintainer's instruction. ⚠ **First finding: most of what looked
distinctive was inherited noise.** `Captures`, `Cloak`, `MindControllableCA` and `Passenger` appear
on all six — and a control check shows `td_gdi_minigunner`, `ra1_allies_medic` and
`td_gdi_grenadier` carry exactly the same four. Only what is **absent** from ordinary infantry
discriminates.

**So the six are three different things, not one class:**

| | units | real discriminator |
|---|---|---|
| **spies** | `ra1_allies_raspy` 500 · `ra2_allies_ra2spy` 500 · `futuretech_spyfutu` 1,000 | `Disguise` **+** `Infiltrates` |
| **mind controller** | `yuri_clone` 500 | `MindControllerCA` + `ProximityCaptor` |
| **neither** | `naxis_slaveoverseer` 500 (whip + rifle) · `zerg_defiler` 1,400 (80,000 HP, `DefilerPlague`) | — |

### ⭐ Infiltrators are a candidate class: exactly 3 units, mod-wide

`Disguise + Infiltrates` matches **3 buildable units in the whole mod** — the three above, all
currently `^ScoutInfantryTemplate`, spanning 500–1,000 (a 2.0x spread that fits the band).
⚠ Three members is small but not unprecedented: `closecombat` has 4, `tank_destroyer` and
`dreadnought` have 5 each.

### ⛔ Mind control is a MECHANIC, not a class — measured, and it kills the obvious idea

`MindControllerCA` matches **7 buildable units spread across 6 different templates**:

| unit | cost | template |
|---|--:|---|
| `cabal_radar_cruiser` | 0 | `^ScoutShipTemplate` |
| `yuri_clone` | 500 | `^ScoutInfantryTemplate` |
| `cabal_hackercyborg` | 1,250 | `^HeavyInfantryTemplate` |
| `yuri_mastermind` | 1,500 | `^HighTechTankTemplate` |
| `yuri_psychictower` | 2,000 | `^AdvancedDefenseTemplate` |
| `yuri_yurix` | 4,000 | `^HeroInfantryTemplate` |
| `yuri_psychicdominator` | 10,000 | ⛔ none |

A ship, an infantryman, a cyborg, a tank, a **defence building**, a hero and a superweapon. ⭐ **A
"caster class" would put a building and a hero in the same price distribution** — so mind control is
correctly a mechanic that cuts across classes, exactly like `Cloak`. Not a classification axis.

⚠ It does surface one real defect on the way: **`yuri_psychicdominator` (10,000cr) has no class
template** — a superweapon, so probably an A7 separation rather than a class.

---

## 4. ⛔ THE MIRROR PROBLEM — measured, and it changes the uniqueness rule

**Maintainer, on the engineers:** *"those engineers are all mirrored units so of course it makes
sense to have the same price for those."* ✅ And on support: *"Support units are exempt from the
balance pipeline and will be deliberately hand tuned."*

The support exemption solves support. ⛔ **It does not solve the problem, because the problem is
roster-wide.**

### Measured across every COMBAT class

**178 of 312 combat units (57%) share a price with a classmate**, and the clearest cases are
unmistakable faction mirrors:

| class | members | share | the mirror |
|---|--:|--:|---|
| `scout` | 6 | 4 | `ra1_allies_rifleinfantry`, `ra1_soviets_rifleinfantry`, `td_gdi_minigunner`, `td_nod_minigunner` — **all 100cr** |
| `melee` | 4 | 3 | `ra1_soviets_attackdog`, `ra2_allies_attackdog`, `ra2_soviets_attackdog` — **all 200cr** |
| `mbt` | 42 | **35** | 4 at 800cr incl. `tiger.nax` (the anchor) |
| `scout_vehicle` | 28 | **23** | 8 at 500cr |
| `epic_vehicle` | 24 | 18 | 6 at 5,000cr |
| `high_tech_tank` | 26 | 16 | 4 at 1,600cr |

⛔ **Strict per-class uniqueness would reprice 178 combat units and break faction mirroring
everywhere** — the RA2 Allied attack dog would have to cost something different from the RA2 Soviet
attack dog, for no design reason. In a crossover mod whose factions deliberately mirror each other,
that is a visible fairness bug, not a rounding detail.

### ⭐ The resolution the maintainer's own reasoning implies

> **A MIRROR SET — the same role shipped once per faction — shares one price by design.
> Uniqueness applies BETWEEN roles, never within a mirror set.**

Operationally this is identical to **unique per (class x faction)**: no two units of the same class
in the SAME faction may share a price, and every class averages 1.0–2.1 members per faction, so it
is always satisfiable. ⚠ It needs no new concept and no per-unit annotation — the faction is already
known from the ContentPack.

⚠ **This does NOT weaken the rule where it matters.** Inside one faction, two units of the same
class still cannot share a price, which is the case a player actually compares side by side in the
build palette.

---

## 5. ⛔ CORRECTION — `FORMULA_V2.md` already rules all of this, and I re-derived it wrong

**Maintainer:** *"Can you read again the documentation about our planned unit classes? The special
forces infantry are the long range rifle guys that are able to attack air like the terran marine,
ghost, gdi officer, Nod stealth trooper."*

⛔ **All of it is already law in [`FORMULA_V2.md`](FORMULA_V2.md), which I had never opened**, and
27 per-class working logs sit in `docs/balance/formula_v2_*.md`. This is CLAUDE.md rule 8f exactly:
*"a design question that feels novel usually is not."*

### §6b — class membership is a RANGE BAND, and special forces is defined

> **CONTIGUOUS half-open range bands (maintainer design): no unit can ever fall between classes
> again — the band DEFINES membership.**

| class | range band | baseline |
|---|---|---|
| melee | [1250, 2500) | `asianalliance_alligator` @ 280 |
| closecombat | [2500, 4500) | `td_gdi_shotgunner` @ 200 |
| scout | [4500, 5500] | `naxis_naxiriflesoldier` @ 100 |
| **special forces (advanced; CAN hit air)** | **5500–6500 (r₀ 6000)** | **`japan_imperialscoutsman` @ 200 — LIVE** |

> **"Air is the special-forces class trait, baked into the baseline — hitting air is NEVER a
> per-unit special."**
> **Roster verdicts, air-capable infantry sweep (maintainer 2026-07-20): → special forces: marine,
> ghost/specter, clone trooper, lunar…"**

### ⛔ §3d already rules UNIQUENESS — and it is about STATS, not price

> **Uniqueness within a class** (EXACTLY these 5): no two units may share the same **HP**, **Speed**,
> **effective damage per shot**, **raw `ReloadDelay`**, or **Range**.
> **Original C&C prices are PINNED**: TD, TS, RA1 and RA2 factions keep their original costs for
> memorability; **only stats move**. Custom/RA2-mod factions may adjust cost in **10-credit steps**.
> **Faction personality over formula equality**: similar factions stay close (RA1 Allies rifle vs
> RA1 Soviets rifle, TD GDI vs TD Nod minigunner) but **every stat must differ by at least one step**.

⭐⭐ **This dissolves §4's mirror problem entirely, and it was law the whole time.** The 4 riflemen at
100cr and the 3 attack dogs at 200cr are **TD/RA1/RA2 originals — PINNED, and not allowed to move.**
Mirrors keep the SAME PRICE; it is their **STATS** that must differ by at least one step. That is
the exact opposite of the unique-price rule I spent this thread deriving.

⚠ **So §2.4's price grid needs re-basing against §3d before anything is applied:** price uniqueness
is not the law, stat uniqueness is; TD/TS/RA1/RA2 costs cannot move at all; and the 10-credit step
the maintainer named is already §3d's, for custom factions only.

### ✅ Conflict group 2 RESOLVED by the law — `HeavyInfantry` vs `special_forces` (5)

Measured against the band and the air rule. **The ledger tag was right in all five cases:**

| unit | range | in 5500–6500? | hits air? |
|---|--:|:-:|:-:|
| `td_gdi_officer` | 5,596 | ✅ | ✅ |
| `forgotten_mutantsergeant` | 5,611 | ✅ | ✅ |
| `cabal_eliminator800` | 5,857 | ✅ | ✅ |
| `td_nod_stealthsoldier` | 6,480 | ✅ | ✅ |
| `ra1_allies_machinegunner` | 6,500 | ✅ | ⛔ **no** |
| *(control)* `terran_marine` | 6,105 | ✅ | ✅ |

**All five move to `^SpecialForcesInfantryTemplate`** — the templates were wrong, the tags right.

### ⛔ Two defects the law exposes

1. **`ra1_allies_machinegunner` is in the band but cannot hit air.** §6b says air is the class trait,
   *"never a per-unit special"* — so either it gains air targeting or it is not special forces.
   ⚠ Needs a ruling; it is 6,500 range, exactly the band's top edge.
2. **`terran_ghost` (8,428) and `terran_specter` (7,922) are ABOVE the band**, yet the 2026-07-20
   roster verdict names ghost/specter as special forces. Two parts of the law disagree: either the
   verdict outranks the band, or their ranges must come down into it. ⚠ Ruling needed.

---

## 6. ⭐ The whole infantry roster, measured against §6b — 256 units, 29 out of band

**New tool: `tools/audit/audit_infantry_class_bands.py`** (advisory in `run_all.sh`). §5 checked
five units by hand. This is the same check over every buildable infantry unit in the mod, and it
turns "let's check everything one by one where there are still conflicts" into a list rather than
a search.

| class | band | members | in band | out of band |
|---|---|--:|--:|--:|
| melee (incl. `^DogTemplate`) | [1250, 2500) | 45 | 29 | **16** |
| closecombat | [2500, 4500) | 4 | 3 | **1** |
| scout | [4500, 5500) | 34 | 21 | **11** |
| special forces | [5500, 6500] | 3 | 2 | **1** |

Nine further infantry classes have a **TBD** band in §6b, so nothing in them can be out of band.
They are measured without a verdict in §6.4.

### 6.0 ⛔ The finding that was nearly invisible: the special-forces BASELINE has two classes

`japan_imperialscoutsman` is §6b's special-forces baseline (`@ 200 — LIVE`). It declares
`Inherits@Template: ^SpecialForcesInfantryTemplate` **and** reaches `^ScoutInfantryTemplate`
through `Inherits: ^RA1AlliesRifleInfantry`. Two classes means no single band to check, so the
first draft of the audit dropped it — silently. **The anchor of a class was invisible to the
audit of that class.** Six units are in this state:

| unit | class templates |
|---|---|
| `japan_imperialscoutsman` | `^ScoutInfantryTemplate` + `^SpecialForcesInfantryTemplate` |
| `cabal_cyborgcommando` | `^HeavyInfantryTemplate` + `^HeroInfantryTemplate` |
| `cabal_cyborgcommandov2` | `^HeavyInfantryTemplate` + `^HeroInfantryTemplate` |
| `forgotten_mutantsniper` | `^ScoutInfantryTemplate` + `^SniperInfantryTemplate` |
| `japan_archermaiden` | `^HeavyInfantryTemplate` + `^SniperInfantryTemplate` |
| `wc2_humans_militiapeasant` | `^HarvesterTemplate` + `^MeleeInfantryTemplate` |

⚠ `japan_archermaiden` is one of the eight §1 archers, so its fix is already proposed there
(`^ArcherInfantryTemplate`, dropping the other two). The other five need a ruling.

### 6.1 ⛔ Out of their own class's band — 29 units

The band **defines** membership, so each of these has exactly two legal fixes: **re-class the
unit**, or **move its range into its class's band**. The second is a priced change and must go
through `apply_balance`, so the cheap fix is almost always the first. My reading is in the last
column and is a PROPOSAL, not a decision.

**Melee holding units that are not melee (16).** Nine are flame/spray/shotgun troops sitting one
band too low — they are closecombat by range and by weapon type, which is exactly what
closecombat means (§6b: "shotgun/SMG", 2500 spray → 4500 long shotgun):

| unit | range | lands in | proposed |
|---|--:|---|---|
| `futuretech_blackwidow` | 9,000 | above | sniper family — not melee at any reading |
| `ts_nod_shadowteam` | 8,000 | above | sniper family |
| `ra2_allies_seal` | 6,386 | special forces | §6b verdict already says **navy seal → special forces (from sniper)** |
| `tkm_spetsnaz` | 5,750 | special forces | special forces (hits no air — see §6.3) |
| `terran_harakan` | 4,185 | closecombat | closecombat |
| `ts_gdi_riottrooper` | 4,002 | closecombat | closecombat |
| `heavy_inf.ixian` | 3,800 | closecombat | closecombat (hits air) |
| `td_nod_chemicalwarrior` | 3,414 | closecombat | closecombat |
| `terran_firebat` | 3,400 | closecombat | closecombat |
| `tkm_thermonaut` | 3,204 | closecombat | closecombat |
| `forgotten_chemsprayinfantry` | 3,183 | closecombat | closecombat |
| `forgotten_runnershotgal` | 3,112 | closecombat | closecombat |
| `futuretech_enforcer` | 3,000 | closecombat | §6b verdict already says **futuretech enforcer → closecombat** |
| `ra1_soviets_cyberdog` | 2,500 | closecombat | ⚠ a DOG at exactly 2500 — the boundary rule puts it in closecombat, but a dog that is not melee is a design question, not an arithmetic one |
| `SCBROODLING` | 1,200 | below | round UP to 1250 (§6b: "sub-1250 outliers round UP") |
| `forgotten_zombiemutant` | 1,127 | below | §6b names this exact unit as the round-up case |

**Scout holding units that are not scouts (11):**

| unit | range | lands in | proposed |
|---|--:|---|---|
| `zerg_defiler` | 9,000 | above | §6b verdict: **casters → support class** |
| `yuri_clone` | 7,000 | above | needs a ruling — no verdict covers it |
| `naxis_slaveoverseer` | 5,621 | special forces | ⚠ §6b verdict says **naxi slaveoverseer → scout (lose air)** — so the RANGE moves, not the class |
| `undead.nax` | 5,621 | special forces | same weapon as the above; also a naming-rule defect (`.` not `_`) |
| `ra1_allies_rifleinfantry` | 5,500 | ⚠ **the boundary** | see §6.2 |
| `TSE1` / `ts_gdi_lightinfantry` / `ts_nod_lightinfantry` | 4,062 | closecombat | ⚠ these are the TS riflemen — rifles are the SCOUT archetype, so the class is right and the RANGE is 438 short of the band |
| `zerg_spithid` | 3,855 | closecombat | §6b verdict says **zerg spithid → scout (lose air)** — again the range moves |
| `ra1_allies_raspy` | 2,560 | closecombat | needs a ruling |
| `naxis_coneheadsknights` | 1,555 | melee | ⚠ §6b verdict says **coneheads knight → special forces**, and it measures 1,555 — a 4,000-point gap. One of the two is wrong. |

**Closecombat (1):** `naxis_sssoldier` at exactly 4,500 lands in scout. §6b's closecombat line
explicitly names it as a T3 member of that class, so this is the boundary rule biting a unit the
law places by name — the range should come down one step, not the class change.

**Special forces (1):** `tkm_trooper` at 5,191 lands in scout — and §6b's verdict says
**"→ scout (lose air): … tkm trooper"**. A move that was ruled 2026-07-20 and never applied.

### 6.2 ⛔ §6b contradicts itself at exactly 5500, and one unit sits on it

§6b's table writes scout as the CLOSED interval **[4500, 5500]** and special forces as
**"5500–6500"**, so 5500 belongs to both. Its prose settles it the other way — *"Boundary rule: a
weapon at exactly 2500 is closecombat; exactly 4500 is scout (half-open bands)"* — so the audit
reads every band half-open and **`ra1_allies_rifleinfantry` @ 5,500 becomes special forces**.

That is almost certainly not intended: it is the RA1 Allied rifleman, the archetypal scout, and it
cannot hit air. ⚠ **Needs a ruling** — either §6b's table is corrected to `[4500, 5500)` and this
unit's range drops one step, or the boundary is closed at the top and the prose is corrected.
Whichever way, one of the two statements in §6b has to go.

### 6.3 ⚠ Air capability outside special forces — 19 units

§6b: *"Air is the special-forces class trait, baked into the baseline — hitting air is NEVER a
per-unit special."* Sixteen of the nineteen are scouts, and the 2026-07-20 sweep already ruled
"→ scout (lose air)" for several of them by name (`ra2_soviets_conscript`,
`asianalliance_asianmilitia`, `latinsyndicate_latinmilitia`, `naxis_slaveoverseer`,
`zerg_spithid`, `tkm_marine`):

`futuretech_enforcer` · `heavy_inf.ixian` · `ra2_soviets_crazyivan` (melee) —
`TSE1` · `asianalliance_asianmilitia` · `ixian_lightinfantry` · `latinsyndicate_latinmilitia` ·
`light_inf` · `naxis_slaveoverseer` · `ordos_lightinfantry` · `ra2_allies_gi` ·
`ra2_soviets_conscript` · `ra2e2.black` · `tkm_marine` · `ts_gdi_lightinfantry` ·
`ts_nod_lightinfantry` · `undead.nax` · `zerg_defiler` · `zerg_spithid` (scout)

⚠ The D2k light-infantry ladder (`light_inf`, `ordos_lightinfantry`, `ixian_lightinfantry`) is
named in §6b's own price ladder as scout class, and all three hit air. That is the largest block
here and it needs one ruling, not three.

⚠ `ra2_soviets_crazyivan` is melee-classed and air-capable; §6b's verdict says
**"crazy ivan (bomb-attach) → special forces"**. Its 2,000 range makes it melee by the band. Same
shape of conflict as `naxis_coneheadsknights`.

### 6.4 The unapplied split, in numbers — where the SF/rocket-trooper/archer intake is

The nine TBD classes, by where each member's range LANDS. This is §0's dead-template story as a
measurement: `^AntiTankAntiAirInfantryTemplate` and `^HeavyInfantryTemplate` are holding 43 units
that land in the special-forces band, while `^SpecialForcesInfantryTemplate` has **3 members**.

| class (template) | members | melee | closecombat | scout | special forces | above | below | no range |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `^AntiTankAntiAirInfantryTemplate` | 44 | 0 | 1 | 1 | **25** | 17 | 0 | 0 |
| `^HeavyInfantryTemplate` | 46 | 0 | 5 | 14 | **18** | 8 | 0 | 1 |
| `^HeroInfantryTemplate` | 29 | 5 | 1 | 2 | 4 | 16 | 0 | 1 |
| `^SniperInfantryTemplate` | 22 | 0 | 5 | 1 | 2 | 14 | 0 | 0 |
| `^FlyingInfantryTemplate` | 11 | 0 | 0 | 5 | 3 | 2 | 1 | 0 |
| `^GrenadierInfantryTemplate` | 7 | 0 | 0 | 0 | 7 | 0 | 0 | 0 |
| `^MortarInfantryTemplate` | 5 | 0 | 0 | 0 | 0 | 5 | 0 | 0 |
| `^MedicTemplate` | 3 | 0 | 0 | 0 | 1 | 2 | 0 | 0 |
| `^MechanicTemplate` | 3 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |

⚠ **This table does NOT say those 43 units are special forces.** The 17 `AntiTankAntiAir` units
ABOVE the band are the rocket-trooper/archer intake the 2026-07-21 split was designed for, and a
grenadier landing in the SF band means grenadier's own band, once ruled, will have to overlap
5500–6500 or those seven move. **The bands for the nine TBD classes are the blocking decision**,
and §6b's contiguity promise ("no unit can ever fall between classes again") cannot hold while
nine of thirteen classes have none.

### 6.5 What this sweep deliberately does NOT do

* It does not price anything. Every range change here is a balance number and belongs to
  `apply_balance --confirm` with a maintainer order.
* It does not touch yaml. This container has no `engine/` build, so no boot gate is possible;
  the template moves ship as a `docs/patches/` patch when they are approved (LESSONS_LEARNED,
  *"A boot-less environment can still land engine work"*).
* It does not judge the nine TBD classes. A band nobody has ruled is not a band this audit gets
  to invent.
