# WEAPON TYPE SYSTEM — deep-research proposal (2026-08-01)

> **STATUS: PROPOSAL.** Decisions made (Q1–Q4): unified `^<Family>_<Level>` naming;
> missiles get full L/M/H per profile; add Sonic + Heavy-anti-inf; build the library
> first. **The armor orders were REBUILT (2026-08-01) under the two-level ordering
> law (`ARMOR_SYSTEM.md` "PROFILE construction") after grounding them in the actual
> existing tables** — see §12 for the final matrix, which SUPERSEDES the earlier
> single-order sketch in §3/§10. Builds on `ARMOR_SYSTEM.md` + `BALANCE_SYNTHESIS.md`
> §13. Awaiting maintainer sign-off on the §12 matrix before splicing into weapons.yaml.

---

## 1. The grammar (recap) — every weapon = PROFILE × LEVEL

Two orthogonal axes fully determine a damage weapon (`ARMOR_SYSTEM.md`):

- **PROFILE (role)** = the **armor ORDER** — which of the 17 armor types sits at 100 and
  the descending sequence after it. This is the weapon's *identity* (what it's good vs).
  Six standard orders: **anti-infantry · universal · HE/anti-vehicle · AP/anti-heavy ·
  anti-structure · AA**.
- **LEVEL (power)** = the **STEP** by which effectiveness falls down the ladder, which
  also fixes the pipeline **WeaponClass (K)** and the Shield value:

  | Level | Step | Falloff | Shield | **WC/K** | Character |
  |---|---|---|---|---|---|
  | **Light**  | 6 | 100→10 | 110 | **0.75** | steep = hard specialist (cheap) |
  | **Medium** | 5 | 100→25 | 125 | **1.00** | middle |
  | **Heavy**  | 4 | 100→40 | 140 | **1.25** | flat = relatively universal (expensive) |
  | *(Super)*  | 3 | 100→55 | 155 | **1.50** | superweapon/charged band |

`tools/balance/gen_weapon_template.py` generates the whole 17-row Versus table (+ paired
HealthPercentageDamage chip) from `(order, step)` — **nothing is hand-typed**, so every
template is law-conformant by construction. Today it only knows the two explosion orders;
adding a family = adding its 16-entry order array.

**So the whole library is a matrix: pick a PROFILE (order), emit its Light/Medium/Heavy
trio** — unless the family is tier-locked (§4).

---

## 2. Current inventory (the `weapon_classes.yaml` sidecar) mapped to the grammar

| Family (profile) | Light | Medium | Heavy | Super | State |
|---|---|---|---|---|---|
| Anti-infantry (SA order) | `^SmallArms` .75 | `^Chaingun` 1.0 | — | — | needs Heavy |
| Sniper (inf-only) | `^SniperWeapon` .75 | — | — | — | specialist |
| AA / Flak | — | `^FlakWeapon` 1.0 | `^HeavyAAWeapon` 1.25 | — | needs Light; profile split (§7) |
| Missile | `^LightMissile` .75 | `^MediumMissile` 1.0 | `^HeavyMissile` 1.25 | — | **level-only, no profile** → split (§3) |
| Cannon | `^TankDestroyerCannon` .75 | `^MediumCannon` 1.0 | `^HeavyCannon` 1.25 | — | **one axis; split AP/HE** (§3) |
| Laser | — | — | `^LaserWeapon` 1.25 | — | needs Light/Medium |
| Railgun | — | — | `^RailgunWeapon` 1.25 | — | AP energy, late |
| Tesla | — | — | `^TeslaWeapon` 1.25 | `^TeslaChargedWeapon` 1.5 | **tier-locked (correct)** |
| Flame | `^LightFlameWeapon` .75 | `^MediumFlameWeapon` 1.0 | `^HeavyFlameWeapon` 1.25 | — | **COMPLETE** |
| Chemical | `^LightChemicalWeapon` .75 | `^MediumChemicalWeapon` 1.0 | `^HeavyChemicalWeapon` 1.25 | — | **COMPLETE** (+`^ToxicWeapon` .5) |
| Explosive (OLD) | `^Grenade` .75 | `^ShrapnelWeapon` 1.0 | `^HeavyBomb` 1.25 | — | **retire** → Concussion/Demolition (§6) |
| Melee | — | `^SwordWeapon` 1.0 | — | — | scale L/M/H |
| Arrow | `^ArrowWeapon` .75 | — | — | — | scale L/M/H |
| Magic | — | — | `^MagicWeapon` 1.25 | — | fantasy, optional scale |
| Nuclear | — | — | — | `^NuclearWarhead` 1.25 | superweapon |
| Support (non-damage) | — | — | — | — | `^HealingWeapon` 1.5, `^RepairWeapon` 1.5 |

Two families already scale cleanly (**Flame, Chemical**) — they are the model for everything else.

---

## 3. The RPS backbone — must exist at all three levels (§13.1)

The three-way counter that the whole balance overhaul rests on. Each MUST be a full L/M/H family:

- **Anti-Infantry (SA order)** — beats infantry, pings off armor.
  `^SmallArms`(L) + `^Chaingun`(M) + **NEW Heavy** (`^HeavyMachinegun`/autocannon-vs-inf).
  Binds: rifle/scout, closecombat, light & scout vehicles, gatlings.
- **CannonAP (AP order, inverted: Superheavy/Heavy at 100)** — kills armor, wastes on infantry.
  Rename `^TankDestroyerCannon` → **`CannonAP_Light`**; **NEW** `CannonAP_Medium`, `CannonAP_Heavy`.
  Binds: MBT, tank_destroyer, high-tech/mammoth, heavy_sniper.
- **CannonHE (HE order)** — infantry + light vehicles + structures, bounces off heavy armor.
  Rename `^MediumCannon` → **`CannonHE_Medium`**, `^HeavyCannon` → **`CannonHE_Heavy`**; **NEW** `CannonHE_Light`.
  Binds: artillery, grenade/splash cannons.

**Missiles split the same way (maintainer order):** the current level-only
`^LightMissile/^MediumMissile/^HeavyMissile` become **profile** families:

- **MissileAP** — anti-armor rocket (AP order). Binds: rocket_trooper, missile tanks.
- **MissileHE** — general/splash rocket (HE order). Binds: missile_vehicle (dual-purpose, §7), MLRS.
- **MissileAA** — dedicated anti-air SAM (AA order). Binds: dedicated AA vehicles/turrets.

→ **Q2:** do MissileAP/HE/AA each get the full L/M/H trio (9 templates), or one tier each
(3)? Recommendation: full trio for AP + HE (light MANPAD → heavy anti-tank missile), and
L/M/H for AA too (light gatling-SAM → heavy long-range SAM). The generator makes the extra
tiers nearly free.

---

## 4. Tier-gating — which families are NOT L/M/H

Some weapons are inherently late-game and only make sense at the top step (maintainer's
"Tesla is always late game"):

- **Tesla** — Heavy (`^TeslaWeapon`) + `^TeslaChargedWeapon` (super). **No Light/Medium.** ✅ already correct.
- **Railgun** — Heavy only (late-game AP energy). Optionally a Medium if a mid railgun exists.
- **Nuclear** — super tier only.
- **Laser** — the exception the maintainer named: lasers **do** span the tree (early laser
  infantry → heavy prism), so `Laser_Light/Medium/Heavy`. Rename `^LaserWeapon` → `Laser_Heavy`.

Specials that stay fixed (role, not a scaling family): **Sniper** (inf-only, huge/shot),
**Toxic** (sub-light 0.5 chemical, no-op vs robotic), **Magic**, **Healing/Repair** (support).

---

## 5. Fantasy + melee families (maintainer order)

- **Melee** — `^SwordWeapon` → **`Melee_Medium`**; **NEW** `Melee_Light`, `Melee_Heavy`.
  Profile = anti-infantry (melee shreds infantry, weak vs armor). Binds: melee class
  (footman = Light, knight/ogre = Medium/Heavy — ties into the dual-armor item, §9b).
- **Arrow** — `^ArrowWeapon` → **`Arrow_Light`**; **NEW** `Arrow_Medium`, `Arrow_Heavy`.
  Profile = anti-infantry **+ ValidTargets:air** (archer class hits air). Binds: archer.

---

## 6. Explosions — the split is DONE at the template level, migration is NOT

`ARMOR_SYSTEM.md` §"two explosion families" already collapsed Grenade/Shrapnel/HeavyBomb
into **two profiles**, and the six templates already exist in `weapons.yaml`:

- **Demolition** (anti-structure, soft-priority): `^LightDemolition` (= old `^Grenade`),
  `^MediumDemolition` (new), `^HeavyDemolition` (= old `^HeavyBomb`, byte-identical).
- **Concussion** (universal gentle slope): `^LightConcussion`, `^MediumConcussion` (= old
  `^ShrapnelWeapon`), `^HeavyConcussion`.

**But the migration never started:** the new templates have **0 inherit sites**, while the
old ones still carry **470** (`^Grenade` 169, `^ShrapnelWeapon` 175, `^HeavyBomb` 126). So
"the old templates still exist" because nobody repointed the weapons yet. The mapping is
already specified (`ARMOR_SYSTEM.md` §migration):

`^Grenade → ^LightDemolition · ^ShrapnelWeapon → ^MediumConcussion · ^HeavyBomb → ^HeavyDemolition`
(mixed-warhead weapons keep their other components; pair-rename law; resolver-diff empty; boot-gate).

→ **Q7:** go-ahead for the scripted 470-site migration + deletion of the three old templates?
This is a self-contained batch (no pricing dependency) and can run any time.

---

## 7. AA — reconciling the two docs (targeting gate vs AA order)

`ARMOR_SYSTEM.md` lists an **AA order** (Fighter/Bomber/Spaceship/Helicopter at 100).
`BALANCE_SYNTHESIS.md` §13.2 says **"AA is a targeting gate, not a versus profile"** (reuse a
ground warhead + `ValidTargets:air`). Both are right for different cases — proposed rule:

- **Dedicated AA** (only hits air: flak cannon, SAM turret, dedicated AA vehicle) → use the
  **AA order** (aircraft at 100, ground ≈ 0). The versus table itself enforces "great vs air,
  useless vs ground" = the AA class's built-in weakness. → `Flak_{L/M/H}` + `MissileAA_{L/M/H}`.
- **Dual-purpose** (hits ground AND air with one weapon: `missile_vehicle`, rocket troopers,
  light-vehicle autocannons) → keep the **ground profile** (HE/SA/AP) and add
  `ValidTargets:air` on the armament (the gate). Priced once, no air bonus (per the class law).

→ **Q3:** confirm both mechanisms coexist (dedicated-AA = AA order; dual-purpose = ground
profile + ValidTargets:air). This also lets `audit_aa_gating.py` (§14 of SYNTHESIS) enforce
who may carry an air-targeting armament.

---

## 8. Candidate NEW profiles (my "what else")

- **Sonic / Wave** (Japan waveforce line) — §13.2 lists it (broad, ignores some armor). No
  template today; the units exist. Candidate `Sonic_{L/M/H}` (general anti-armor, ignores a
  couple armor tiers) to formalize the wave weapons instead of ad-hoc versus.
- **Heavy anti-infantry** — the SA family's missing top tier (see §3); needed for late
  gatlings / heavy MG vehicles.
- **Radiation** (Desolator: anti-inf + anti-light, per §13.2) — probably a **Chemical**
  variant rather than its own family; low priority.

→ **Q4:** add Sonic? add the Heavy anti-inf tier? (Recommend yes to both.)

---

## 9. Naming convention — the one real inconsistency

Existing single-profile families are **LEVEL-first** (`^LightFlameWeapon`, `^MediumMissile`,
`^LightDemolition`), but the maintainer's new names are **FAMILY-first**
(`CannonAP_Light`, `MissileAA_Heavy`) — which is unavoidable for multi-profile families
(you can't cleanly write "LightCannonAP"). To avoid two conventions:

→ **Q1:** adopt a **unified `^<Family>_<Level>`** scheme (underscore separator, family-first,
per the no-hyphen naming law): `Flame_Light`, `Chemical_Heavy`, `CannonAP_Light`,
`MissileAA_Heavy`, `Demolition_Light`, `Melee_Heavy`, `Arrow_Light`, `Laser_Light`. This
renames the existing level-first families (mechanical, pair-rename law + resolver-diff), but
gives ONE rule. **Alternative:** keep level-first for single-profile families, family-first
only for the split ones (Cannon/Missile). Recommendation: **unified family-first** — worth the
one-time rename for a self-describing library.

---

## 10. Armor follow-ups from the last message

### 10a. Deploy/undeploy armor swap
**Rule (maintainer):** a unit that switches modes swaps armor too — **vehicle armor
(Medium/Heavy) undeployed, building armor (Steel/Concrete) deployed.**
Reference implementation already in the tree — `terran_siegetank`:

```
Armor:            # undeployed
    Type: Heavy
    RequiresCondition: !shielded && undeployed
Armor@deployed:   # deployed = building armor
    Type: Steel
    RequiresCondition: !shielded && !undeployed
```

- **TS Nod Tick Tank (`ts_nod_ticktank`) — checked: it deploys (swaps weapons + turret) but
  does NOT swap armor.** So per the rule it's a candidate: Heavy undeployed → Steel deployed.
- The other conditional-armor actors kept in the normalization pass (`terran_matador`,
  `td_gdi_defenserig`, `cabal_ravager`) + the D2k Ordos deploy units + RA Soviet V2 etc. all
  need the same audit.
- Proposal: enumerate every mode-switching deployable (the deploy-condition scan already
  found the candidates), add `Armor@deployed: <building>` gated on `deployed` and gate the
  base Armor on `!deployed`. Boot-gated batch.

→ **Q5:** which building armor for deployed mode — **Steel** for everything (matches siege
tank), or **Concrete for basic / Steel for advanced**? And confirm the scope = all
mode-switching deployables.

### 10b. Dual armor for WC2 knights + SM Noids
**Intent (maintainer):** give the WC2 heavy melee line and the SM Noids the "in-between"
dual armor that FutureTech/CABAL robots have — **one infantry armor + one vehicle armor** —
so they're harder to hard-counter with pure anti-infantry. This also **resolves the
`wc2_humans_paladin` line_breaker mis-tag**: instead of borrowing `^LineBreakerTemplate`
just to get vehicle armor, they carry dual armor directly and go back to being
infantry/melee-classed.

⚠ **The "×200% on the secondary" half of this recipe is DEAD** (W20/W21 R5, 2026-08-15).
Two armors now **AVERAGE** (`AreaDamageWarhead.MultiArmorCombination: Average`) instead of
multiplying, so the compensation multiplier has no job and all 7 instances were deleted.
Copy the trait set WITHOUT a `DamageMultiplier`.

- **Live pattern** (`schwarzermond_noidmgarmor`, `_noidharvester`, `_engineeringarmor`):
  `Armor: Plate` always on, `Armor@Plating: <vehicle type>` gated on `plating_up`, and an
  `ArmorPlating` trait granting `FullCondition: plating_up`. The vehicle armor is thus tied
  to a visible bar — strip the bar and the unit is plain infantry again.
- Older static pattern, no bar — `^TSCyborgDualArmorHeavy` (CABAL): `Armor: Heavy` +
  `Armor@Secondary: Shield`, both unconditional.
- Target units (confirmed present): `wc2_humans_knight`, `wc2_humans_paladin`,
  `wc2_orcs_ogre`, `wc2_orcs_ogremage` — the SM Noids are DONE.

→ **Q6 (partly answered):** the SM Noids shipped as **Plate + Superheavy** (MG walker) and
**Plate + Heavy** (harvester, engineering walker). Confirm the WC2 melee pair, and whether
they get the static dual armor or the `ArmorPlating` bar.

---

## 11. Open decisions (the maintainer's calls)

| # | Decision | Recommendation |
|---|---|---|
| **Q1** | Naming: unified `Family_Level` vs keep level-first for singles | **unified family-first** |
| **Q2** | Missile tiers: AP/HE/AA × L/M/H (9) or 3 total | **full L/M/H each** |
| **Q3** | AA: dedicated = AA order, dual-purpose = ValidTargets:air gate | **confirm both** |
| **Q4** | Add Sonic profile? Add Heavy anti-inf tier? | **yes to both** |
| **Q5** | Deploy swap: Steel always vs Concrete-basic/Steel-advanced; scope | **Steel always, all deployables** |
| **Q6** | Dual armor pair (Plate+Medium/Heavy) + 200% for WC2/Noids | **Plate + Heavy** |
| **Q7** | Explosion migration (470 sites) + delete old templates — go? | **go (self-contained)** |
| **Q8** | **Sequence** of the work | see below |

**Proposed sequence (Q8):**
1. **Naming + library build** — lock Q1, extend `gen_weapon_template.py` with every profile's
   order array, generate the full L/M/H matrix (Cannon AP/HE, Missile AP/HE/AA, Melee, Arrow,
   Laser, Heavy-anti-inf, Sonic), add `weapon_classes.yaml` entries. Boot-gated.
2. **Explosion migration** (Q7) — scripted 470-site repoint + delete old templates. Boot-gated.
3. **Repoint real weapons onto the new families** per the §13.3 binding matrix (the big batch),
   resolver-diffed, boot-gated — this is what finally unblocks the **DPS restat + pricing**.
4. **Deploy armor swap** (Q5) + **dual armor** (Q6) — independent armor batches, any time.
5. Then the vehicle **DPS/range restat → fit_class → apply_balance** (needs #1–#3 done, since
   DPS is confounded until each unit is on its correct weapon type).

---

## 12. FINAL weapon-type matrix (two-level ordering law, 2026-08-01)

Built from the law in `ARMOR_SYSTEM.md` "PROFILE construction": each type = a
macro-type PRIORITY (Infantry/Vehicle/Building/Aircraft, `+` = combined/interleaved)
× a LIGHT/HEAVY direction, over the fixed sub-ladders. One order per type; L/M/H
share it. Generated + validated by `gen_weapon_template.py` (`--orders` / `--list`).

| Weapon type | Macro priority (best→worst) | Dir | Air? | Levels | Supersedes |
|---|---|:--:|:--:|---|---|
| **Bullet** | INF > (VEH+AIR+BLD) | light | ✓ | L/M/H | SmallArms, Chaingun |
| **CannonAP** | VEH > BLD > INF > AIR | heavy | — | L/M/H | TankDestroyerCannon |
| **CannonHE** | (VEH+BLD) > INF > AIR | light | — | L/M/H | MediumCannon, HeavyCannon |
| **MissileAP** | VEH > AIR > BLD > INF | heavy | ✓ | L/M/H | (LightMissile family) |
| **MissileHE** | (VEH+BLD) > AIR > INF | light | ✓ | L/M/H | — |
| **MissileAA** | AIR > VEH > BLD > INF | heavy | ✓ | L/M/H | HeavyAAWeapon |
| **Flak** | AIR > INF > VEH > BLD | light | ✓ | L/M/H | FlakWeapon |
| **Laser** | (VEH+INF+AIR+BLD) all-4 | heavy | ✓ | L/M/H | LaserWeapon |
| **Prism** | (VEH+INF+BLD) all-ground | light | — | L/M/H | *(new — Laser mirrored, ground-only)* |
| **Flame** | (INF+BLD) > VEH > AIR | light | — | L/M/H | Light/Medium/HeavyFlameWeapon |
| **Chemical** | (INF+VEH) > BLD > AIR | heavy | — | L/M/H | Light/Medium/HeavyChemicalWeapon |
| **Melee** | INF > VEH > BLD > AIR | light | — | L/M/H | SwordWeapon |
| **Arrow** | INF > AIR > VEH > BLD | light | ✓ | L/M/H | ArrowWeapon |
| **Magic** | %-EQUALIZER (ignores armor) | pct | — | L/M/H | MagicWeapon *(giant-killer, §13.3)* |
| **Demolition** | BLD > INF > VEH > AIR | light | — | L/M/H | Grenade, HeavyBomb |
| **Concussion** | (INF+VEH+BLD) > AIR | light | — | L/M/H | ShrapnelWeapon |
| **Sonic** | FLAT — ignores armor | flat | — | L/M/H | *(new; all armors = 45/55/65)* |
| **Railgun** | VEH > INF > BLD > AIR | heavy | — | Heavy only | RailgunWeapon |
| **Tesla** | (INF+VEH) > BLD > AIR | heavy | — | Heavy only | TeslaWeapon *(+vs Shield)* |
| **TeslaCharged** | (INF+VEH) > BLD > AIR | heavy | — | **Super** only | TeslaChargedWeapon *(WC 1.5)* |
| **Nuclear** | **BLD > VEH > AIR > INF** | heavy | ✓ | **Super** only | NuclearWarhead *(WC 1.5)* |

**Resolved (maintainer 2026-08-02):**
- **Laser** = equally good vs ALL 4 types, anti-**HEAVY** (starts Superheavy).
- **Prism** = the mirror (anti-**LIGHT**, starts Scout) as a NEW family — so late-game
  prism tanks don't make AP tank-destroyers obsolete (Prism is anti-light, AP anti-heavy).
- **Demolition** = Buildings first, infantry second (true anti-structure).
- **Interleave** = longest sub-ladder leads (vehicle's 5 entries start, then 4, then 3).

**Resolved (maintainer 2026-08-02, cont.):**
- **Prism** cannot target air → air at the floor, ground-only ValidTargets. (Its
  ground profile equals Concussion's; fine — they differ in WC/projectile/effects.)
- **Sonic** = FLAT / "ignores armor": every armor takes the same per-level value
  (`FLAT_VALUES` = 45 / 55 / 65, tunable) — a pure generalist, no gradient, no macro
  preference. Distinct from Laser (which is sloped + macro-universal).

**Still open (minor):**
- Sonic's flat values (45/55/65) are a first guess — tune in-game.
- **Toxic** (WC 0.5 sub-light anti-inf) and **Sniper** (infantry-only, huge/shot) stay
  as fixed specials, not L/M/H families.

---

## 13. The 4-DIMENSIONAL differentiation model + the flat/% axis (2026-08-02)

The Versus matrix (§12) is only ONE of four axes that make a weapon unique. "Same
profile" ≠ "same weapon" — there are only ~9 sensible armor profiles, so families
SHARE profiles and differentiate on the other three axes.

**The four axes:**
1. **Versus PROFILE** — macro-priority × light/heavy direction (§12). *What it's good against.*
2. **LEVEL / steepness** — Light/Medium/Heavy/**Super** = step 6/5/4/**3** = WC 0.75/1.0/1.25/**1.5**. *Specialist ↔ generalist.*
3. **DELIVERY** — cannon shell / homing missile (shoot-down-able, hits air) / bullet / melee /
   hitscan beam / AoE splash. *How it plays* — not visible in the Versus matrix at all.
4. **flat/% RATIO + special effect** — see §13.2–13.3. *Anti-small ↔ anti-big, plus EMP/DoT/etc.*

### 13.1 The Super tier (step 3)
The L/M/H triple extends UP to **Super = step 3** (main 100→55, %-window top 30,
**WC 1.5**) for the superweapon band: **Nuclear** and **charged Tesla**. Shield is generated
by the separate physics-ranked 100–400 law. Super is flatter than Heavy
(never below 55%) and one WC notch above Heavy. (`LEVELS`/`WC` in `gen_weapon_template.py`.)

### 13.2 The percentage warhead — CORRECTED mechanic
Generated families now carry one `AreaDamage` warhead with two linked parts: flat `Damage` /
`Versus`, plus a folded max-health contribution controlled by `PercentageScale` /
`PercentageVersus`. **The earlier separate `HealthPercentageDamage` twin and its whole-percent
rounding law are retired for these families.**

- At the standard `PercentageScale: 10000`, every 2000 flat `Damage` derives 1.00% of max
  health before `PercentageVersus`. Changing the main Damage therefore scales both parts.
- `PercentageVersus` supplies the same armor order in the 16/20/25/30 window (floor top−15).
  Runtime rounds the derived basis points and final HP damage; a low result may truncate to zero,
  but this is not a designed hard-immunity rule.
- A bespoke standalone `AreaDamagePercentage` / `HealthPercentageDamage` does not follow main
  Damage and creates a true output floor. The affine pricing model reports that floor separately.
- Because the folded profile peaks on the weapon's best target, anti-tank families earn a larger
  high-HP contribution while anti-infantry families remain flat-dominant.

### 13.3 The flat/% ratio = the ORTHOGONAL axis (anti-small ↔ anti-big)
Independent of the armor profile: **flat-dominant = anti-LOW-HP; %-dominant = anti-HIGH-HP.** This
is a whole second design dimension the profile doesn't touch. The two pure extremes (both *ignore
armor* — uniform vs every armor):
- **Sonic** = FLAT uniform (45/55/65 vs all) → the anti-**low-HP** equalizer (fixed damage vs anything).
- **Magic** = **%-EQUALIZER**: tiny flat plus a large uniform folded **% of max HP** contribution,
  ground-only → the anti-**high-HP** giant-killer (melts expensive/high-HP units, useless vs
  cheap swarms). *The mirror of Sonic on the HP axis.*
- **General guidance:** tie a weapon's flat/% ratio to its target's typical HP — anti-infantry =
  flat-heavy (infantry HP is low, % rounds to ~0 anyway); anti-heavy/AP = %-heavier (only the %
  meaningfully dents a 500k-HP tank). Much of this is automatic via §13.2; Magic is the deliberate
  extreme.

### 13.4 AoE FRIENDLY-FIRE rule (GENERAL — applies to every splash weapon)
Every **AoE** `AreaDamage` weapon deals **reduced friendly fire: HALF radius + HALF damage**
to friendlies through its baked `FriendlyFireSpread` / `FriendlyFireDamage` fields. Applies to
Chemical, Demolition, Concussion, Nuclear, artillery HE, and any splash weapon — **remember this
when repointing.** (Single-target/hitscan weapons — bullets, cannon direct, Prism beam,
tesla, railgun — have no friendly-fire twin.)

### 13.5 Differentiating the overlap clusters (the payoff of §13.1–13.4)

| Cluster (shared Versus profile) | How each is made UNIQUE |
|---|---|
| **Prism ≡ Concussion** (universal, light, ground) | **Concussion** = explosion **AoE**, flat-dominant, reduced FF → shreds **swarms**. **Prism** = hitscan **beam**, single-target, **%-leaning** → melts **big single** targets. (flat/% axis + delivery) |
| **Chemical** (inf+veh heavy) | **AoE gas** — large spread, reduced FF (½r/½dmg); optional lingering DoT. Anti-crowd. |
| **Tesla** (inf+veh heavy) | **Bonus vs Shield** (elevated Shield value) + EMP/disable. Heavy tier. |
| **TeslaCharged** (inf+veh heavy) | **Super tier** (step 3, WC 1.5) + a BIGGER Shield bonus. The charged upgrade. |
| **Nuclear** | **RE-PROFILED** to **Building › Vehicle › Air › Infantry (heavy)** — levels structures + heavy units + air, weak vs infantry. **Super tier**, hits air, (radiation lingering). No longer overlaps Chemical/Tesla. |
| **Magic** | **Escaped the profile entirely** → the §13.3 %-equalizer (giant-killer). |
| **CannonAP / MissileAP / Railgun** (veh-heavy core) | Delivery + 2nd-priority: Cannon = ground shell (air floor); Missile = homing, hits air; Railgun = hitscan, infantry-2nd, Heavy-only. |
| **CannonHE ≈ MissileHE** | Cannon = ground shell; Missile = homing + hits air. |
| **Bullet / Melee / Arrow** (anti-inf light) | Bullet = ranged + reaches air; Melee = no range, no air; Arrow = arc + air-2nd. |

**Verdict: no new PROFILES needed** — the macro×direction space is covered; adding more would
manufacture overlaps. Uniqueness now comes from axes 2–4, which the above locks in.

**Open tuning knobs (decide in-game, not blocking the splice):**
- Sonic flat values (45/55/65), Magic % values (4/6/9), the Super %-window (top 30).
- Whether Nuclear/Chemical get lingering-DoT warheads (radiation/gas).
- The %-window magnitudes globally (they set how hard the natural immunity / anti-turtle is).
