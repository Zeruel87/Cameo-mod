# BALANCE PROGRAM — the execution plan (rev. 2026-08-28)

**This file is the SINGLE SOURCE OF TRUTH for what is done, what is next, and who owns
what.** It survives compaction, agent handover and session death. Every other document
(ROADMAP, EFFECTIVE_DAMAGE, PHYSICAL_STATE_SYSTEM, the AI handoffs) links *here* for
status rather than keeping its own copy.

---

## 0. HOW TO USE THIS FILE (read first, every session, any agent)

1. **Don't trust the status column — verify it.** Every work item carries a `VERIFY`
   command that answers "is this actually done?" in one line. Run it. If it disagrees
   with the status, **the command wins** — fix the status in the same commit.
2. **Take the topmost item whose `needs:` are all ✅ and whose `owner:` is free.**
3. **Do not start an item whose files another agent holds.** Ownership is per FILE SET
   (§2), not per person — check `git log --oneline -3 <file>` and the file mtime first.
4. **Every item is finished the same way**: its `DONE WHEN` list, then the universal
   gate in §3, then update this file's status line **in the same commit** as the work.
5. **Never renumber the items.** W-ids are permanent references used by commits,
   memory files and letters. Add W13, W14 … ; mark dead ones `✖ DROPPED` with a reason.

**Status vocabulary:** `✅ DONE` · `🔵 IN PROGRESS (agent, date)` · `⬜ READY` (deps met)
· `⛔ BLOCKED (on Wx / on maintainer)` · `✖ DROPPED`.

---

## 0a. ⛔ ORDER OF OPERATIONS — WEAPON STRUCTURE BEFORE PRICING (ruling 2026-08-17)

**Maintainer:** *"shouldn't we first finish the 3 way split like documented before we start
applying the balance formula to our actors? It would be double work splitting the multi
warheads later on. If we split it now applying the balance formula will be easy."*

**Correct, and measured.** A price is a function of `K`, and `K` is built from the weapon's
warhead set and their `Versus` profiles. Both are still scheduled to change across most of the
roster, so pricing first means pricing inputs we are about to replace:

| what is still in flux | measured evidence |
|---|---|
| W24 — directly fired weapons with **more than one** damage main | **184** under the raw unified predicate; 2026-09-07 survey (234 including indirectly reached weapons; no reviewed exceptions subtracted) |
| armament slots whose `K` moves when those collapse | **1 547** (2026-08-17 snapshot) |
| legacy template direct inheritors (W23) | **1596** on 2026-09-07 (`audit_unconverted_templates`); historical family reach was **665 of 1622 = 41.0%** on 2026-08-17, not a current measurement |

Changing the warhead structure can change both delivered damage and **`K`** — `K`
is share-weighted over each warhead's armor profile, so picking ONE family changes
the profile and therefore the price. Use the current conversion policy in DESIGN
§11b.1; do not infer behaviour preservation merely from a raw damage sum.
Retrofitting a legacy template onto a family changes pricing inputs again.

⚠ **The anchor table already said so.** `class_anchors.json` → `mbt.provisional`: *"DPS restat
DEFERRED to the cannon/weapon rebuild."* The decision to wait was written into the data before
the question was asked.

**The order:**

1. **W24** — one damage warhead per weapon (DESIGN §11b). 184 directly fired weapons remain non-compliant; 234 remain when indirect weapon-graph reachability is included (2026-09-07 raw survey).
2. **W23** — the 25-template legacy retrofit. ⭐ **W24 DISSOLVES W23's BLOCKER.** That blocker
   is "33 weapons inherit several legacy templates mapping into the SAME family, so the rename
   merges two warheads and the smaller damage vanishes". After W24 each weapon carries ONE
   damage warhead, so there is nothing left to merge — the collisions were this debt made
   visible, not a conversion bug. **The owed ruling ("should one weapon carry three warheads of
   the same family at all?") is already answered by §11b: no.**
3. **A5** — retire the remaining inline-`Versus` weapons onto templates.
4. **THEN** class anchors → `fit_class` per class → maintainer sign-off (W11) → targets written
   into the ledger → `apply_balance --confirm` → boot gate.

**Still safe BEFORE the split:** `fit_class` as a DIAGNOSTIC — it writes a validation report,
and its anchor write is merge-safe since `f1c89db9f`. Reading where costs stand today costs
nothing and informs the anchor choice. What must wait is WRITING targets and applying them.

---

## 1. THE BOARD

| id | work item | status | owner | needs |
|---|---|---|---|---|
| **W1** | K coefficient + target model (measured Versus weights, capped density) | ✅ DONE `f8421d345` | Claude | — |
| **W2** | `^LightFlameWeapon` → 3-way split + new `^Warhead_Inferno_*` family | 🔵 **IN PROGRESS (Devin, 2026-08-21); HeatRayBeam1-4 3-way split done; 28 matches remain** | Devin | — |
| **W3** | Ledger split: raw stays, derived moves to `docs/balance/derived/` | ✅ DONE | Claude | W1 |
| **W4** | Retire weapon-class K; charge-up becomes an ACTOR property | ✅ DONE | Claude | W1 |
| **W5** | Missing metrics: overkill/TTK, range advantage, ValidTargets, MinRange, AttackDelay | ✅ DONE | Claude | W1 |
| **W6** | C# `ModifiesCombatProportionalToPhysicalState` (+ pitch/glow hooks) | ✅ DONE `fc45a9632` | Claude | — |
| **W7** | Sonic → `Resonance` meter (no new C# needed) | ⬜ READY | either | — |
| **W8** | Gatling ladder → `SpinUp` meter | ✅ DONE `c0d6abf70` — all 43 actors, `GattlingSpeed` = 0 | Claude | W6 ✅ |
| **W9** | `^Poisonable` → `Poison` meter (gas-cloud dose-response) | ⬜ READY | either | — |
| **W10** | `^Blindable` → `Blind` meter | ⬜ READY (unblocked by W6) | either | W6 ✅ |
| **W11** | Wire K into `fit_class.py` behind a flag; fit one class both ways and compare | ✅ BUILT, sign-off owed (+2 pipeline bugs fixed: 43% of the roster priced at zero DPS) | Claude | W3 ✅, W4 ✅, W5 ✅ |
| **W12** | Superweapon balancing as a SEPARATE track (not unit-priced) | ⬜ READY | maintainer-led | — |
| **W13** | Warhead system rebuild from the 3150-profile reference corpus | 🔵 steps 1-4a DONE — **the measured profiles are LIVE** on all 10 sourced families (+ 8 blends); 4b = the 10 INVENTED families | Claude | W1, W5 |
| **W14** | ~~Renormalise `avg_versus`~~ — ✖ DROPPED, the multi-role premium is intended; folded into W13 rule 8b | ✖ DROPPED | — | — |
| **W15** | `%`-twin fix + `reference_hp` → 200 000 — **PREREQUISITE for W17** | ✅ DONE | Claude | — |
| **W16** | Charge-up discount PROPORTIONAL to real charge share (supersedes W4's flat 0.75×) | ✅ DONE | Claude | W4 ✅ |
| **W17** | ~~Remove the 2000-damage grid~~ (done as a 100 grid in W15); retire FirepowerMultiplier as a fine-tuning knob | 🔵 TOOLING DONE `451e10a63`; **content half NOW UNBLOCKED** | Claude | W15 ✅ |
| **W18** | Roll the 0.01% basis-point unit out into yaml (`PercentageDenominator: 10000`, `pct_damage = damage // 100`, ×5 the Versus values — all three together) | ✅ **DONE 2026-08-22.** Step 4 first: 2113 twins migrated `HealthPercentageDamage` → `AreaDamagePercentage` (the stock type has no `Falloff`, so 2059 authored curves were being discarded — not a behaviour-preserving drop-in as this row assumed). Then the unit: generator emits Damage×20 + Versus×5 + `PercentageDenominator: 10000`, and 1444 LOCAL overrides restated ×20 across 37 live files. Verified: effective %-damage changed on **0 of 4757** percentage warheads. ⚠ 1549 overrides deliberately left in whole percent — they resolve to LEGACY hand-written templates that never got the denominator; which overrides move depends on the denominator they RESOLVE to, not on where the line sits. | Claude | W15 ✅ |
| **W19** | Collapse the 195 `SpreadDamage` ExtraDamage chips into the main warhead (KEEP the 34 sniper `OpenToppedDamage`) | ⬜ READY (set B free) | Claude | W13 |
| **W20** | Multi-armor combination rule (engine MULTIPLIES → squares the profile); mechanism + switch | ✅ DONE (`Average` is live, maintainer set) | Claude | — |
| **W21** | Layered health Shield → Integrity → Armor → Health, layer-aware armor (solves W20 structurally) | ✅ BUILT + LIVE `ab467fe52` | Claude | — |
| **W22** | Roster census: liveness classifier + per-credit weighting (552/1977 armored actors are not buildable) | ⬜ PROPOSED | — | — |
| **W23** | Retrofit the 45 legacy templates into the `^Warhead_*` family system | 🔵 MACHINERY DONE + verified; content ⬜ READY — **the 33-collision blocker is DISSOLVED** (§0a + DESIGN §11b: one damage warhead per weapon, so there is nothing left to merge). Sequenced AFTER W24. | Claude | W13 |
| **W24** | Collapse every weapon to ONE damage warhead (3-way split, damage half) — 57.2% of fired weapons carry 2+, worst case 15 | ✅ ninth cluster (GoliathRockets_AA/WraithRockets_AA/SunDogRockets/MissileTurret/ScoutRockets_AA/HeavyOrdosCombatTankRockets) reparented to ^Warhead_MissileAA_Heavy (Goliath/Wraith/Scout/MissileTurret) and ^Warhead_MissileAP_Heavy (SunDog) + ^Projectile_Missile_Heavy_D2K + ^Effect_MissileHE_Heavy_D2K (one main + percentage twin); removed ^D2KRocket full-stack inherit and created ContentPacks/D2k/Shared/yaml/weapons.yaml with D2K-specific missile/rocket projectile and effect templates; removed ^Chaingun/^FlakWeapon/^LightMissile/^MediumMissile inherits and their warheads; preserved per-shot totals (30000/10000/10000/20000/10000/10000) and percentage twins (15/5/5/10/5/5); preserved local projectile overrides (Speed, Inaccuracy, launch angles, contrail colors) and restored flak-bullet contrail visual fields (ContrailZOffset/ContrailStartColor/ContrailEndColor/ContrailStartWidth/ContrailEndWidth) as local overrides because ^D2KRocket's ^Projectile_Missile_Heavy drops them; added local Warhead@EffectWater (small_splash) because the ^Effect_MissileAP_Heavy family does not define one; children resolve cleanly; review_resolve_diff clean; find_empty_warhead 0, find_orphan_old_keys 0, audit_warhead_split baseline 958→952, audit_physical_state_warheads PASS, audit_balance_drift clean, boot-gated; then ^D2K_Cannon repointed to ^Projectile_Shell_Medium_D2K + ^Effect_CannonHE_Medium_D2K in ContentPacks/D2k/Shared/yaml/weapons.yaml (preserving d2k_120mm, d2k_small_napalm, 8000 main + percentage twin, Sand/Rock smudge, 1000 concrete), boot-gated; then ^D2KRocket and ^D2KMissile moved into ContentPacks/D2k/Shared/yaml/weapons.yaml as AP 3-way split intermediates (^Warhead_MissileAP_Heavy + ^Projectile_Missile_Heavy_D2K[_Rocket] + ^Effect_MissileAP_Heavy_D2K[_Rocket]) so all D2K rocket/missile users resolve without empty warheads, boot-gated; then Debris repointed to ^Projectile_Grenade_Light_D2K_Debris + ^Effect_Demolition_Light_D2K (preserving shrapnel bounce, d2k_tiny_explosion, Scorch smudge, 300 concrete), boot-gated; then D2K_155mm family repointed to ^Projectile_Grenade_Light_D2K_155mm + ^Effect_Demolition_Heavy_D2K_155mm (preserving d2k_155mm, d2k_med_explosion, multi-warhead structure, MORTAR1.WAV), boot-gated; then Dune_SiegeMortar repointed to ^Projectile_Shell_Light_D2K_Mortar + ^Effect_CannonAP_Light_D2K_Mortar (preserving d2k_155mm / effect palette, d2k_large_explosion, four-warhead structure), boot-gated; then D2K_Rocket and Fremen_RPG repointed to D2K Shared blast effect layers (^Effect_MissileAP_Heavy_D2K_Rocket_Blast / ^Effect_MissileAP_Heavy_D2K_Missile_Blast) preserving d2k_rocket_explosion and per-weapon concrete, boot-gated; then oRocket repointed to ^Effect_MissileAP_Heavy_D2K_Rocket_Blast preserving SpreadDamage warhead and 625 concrete, boot-gated; then D2K_155mm2 repointed to ^Projectile_Grenade_Light_D2K_155mm + ^Effect_Demolition_Heavy_D2K_155mm2 preserving multi-warhead grenade/flame/shrapnel/bomb stack, d2k_155mm image, d2k_large_explosion, boot-gated; seventh cluster (TSChemJuggerboat90mm/TSChemVanMissile/TSChemMLRSMissile/TSChemBazooka/TSTibBazooka/TSChemApacheMissile/TSChemCobraMissile) reparented to chemical cannon/missile families with PhysicalStates moved into ^Warhead_Chem*/^Warhead_ChemCannon*/^Warhead_ChemMissile* templates; added global ^Projectile_ArtilleryShell_Medium and ^Projectile_ArtilleryRocket_Medium, consolidated the redundant ContentPacks/RedAlert2/Shared copy into the global template, and switched Future_MultiMissile_Frag to the artillery-rocket family; audit_physical_state_warheads updated to resolve PhysicalStates maps as well as direct PhysicalStateName/PhysicalStateScale; eighth cluster (227mm/GDIRigMissilePod/MammothTusk) reparented to ^Warhead_MissileHE_Medium/^Warhead_MissileHE_Heavy with ^Projectile_Missile_Medium/^Projectile_Missile_Heavy and ^Effect_MissileHE_Medium/^Effect_MissileHE_Heavy; preserved resolved per-shot totals 8000/32000/24000, local projectile overrides (Speed, Inaccuracy, launch angles), impact/water effects, ImpactActors, and the legacy flak-bullet contrail colors (ContrailStartColor/ContrailEndColor restored on the three non-AMT projectiles); children 227mmAMT, GDIRigMissilePodAMT, MammothTuskTargetingComputer resolve cleanly; review_resolve_diff clean; find_empty_warhead 0, audit_warhead_split broadcast baseline lowered 965→958, audit_balance_drift clean, boot-gated; then ^ORocket/^OMissile and children (oBazooka/oRocket/oTowerMissile/omtank_pri/oDeviatorMissile) converted to 3-way split with D2K Shared ^Warhead_MissileAP_Heavy_D2K_ORocket, ^Projectile_Missile_Heavy_D2K_ORocket/^Projectile_Missile_Heavy_D2K_OMissile, ^Effect_MissileAP_Heavy_D2K_ORocket/^Effect_MissileAP_Heavy_D2K_OMissile in ContentPacks/D2k/Shared/yaml/weapons.yaml; preserved legacy SpreadDamage, Versus, falloff, projectile fields, d2k_tiny/small/deviator explosions, concrete 240/720/625/900/1000, smudge invalid targets; review_resolve_diff OK; find_empty_warhead 0, find_orphan_old_keys 0, audit_warhead_split 952, boot-gated; then OrniBomb and OrniBombC converted to 3-way split using D2K Shared ^Projectile_GravityBomb_D2K, ^Warhead_Demolition_Heavy_D2K_Orni, and ^Effect_Demolition_Heavy_D2K_Orni; preserved 7500 SpreadDamage, d2k_bombs GravityBomb, Sand/Rock smudge, d2k_large_explosion, and 7500 concrete; OrniBombC inherits OrniBomb with Range 2500 (its original Range 3333 was mis-indented and ignored by the resolver); review_resolve_diff OK; find_empty_warhead 0, find_orphan_old_keys 0, audit_warhead_split 952, boot-gated; then HammerheadArtillery (Consortium) collapsed Demolition_Light+HeavyBomb into ^Warhead_Demolition_Heavy and CannonHE_Medium into ^Warhead_CannonHE_Medium (per-shot total 33333/33 preserved, Bullet/120MM blue-contrail projectile and steel_blueexp/makoexplose effects retained), audit_warhead_split baseline lowered 950->946, boot-gated; then NuclearMaverick (RedAlert/Soviets) converted from ^NuclearWarhead to ^Warhead_Nuclear_Super + ^Effect_Nuclear_Super with ^Warhead_MissileHE_Heavy retained; per-shot totals 40000 flat + 20% preserved; nuke half now AreaDamage 10-tick shockwave (Damage 2000/MaxRadius 9000) and percentage (Damage 1/Spread 500/MaxRadius 4500); old SpreadDamage/HealthPercentageDamage/FireDeath shape preserved via local overrides; Concrete/ShieldHit resolved to MissileHE effect values; audit_warhead_split baseline 946->945, find_empty_warhead 0, find_orphan_old_keys 0, audit_balance_drift clean, boot-gated; then ThermobaricNuclearMaverick (RedAlert/Soviets) repointed from the broken duplicate Inherits@2: ^NuclearWarhead + ^Warhead_Flame_Heavy stack to a clean 3-way split with ^Warhead_MissileHE_Heavy, ^Warhead_Nuclear_Super, ^Warhead_Flame_Heavy, ^Effect_Flame_Heavy, ^Effect_Nuclear_Super (flame effects first, nuclear effects second); fixed duplicate Inherits@2 so both flame and nuclear warheads actually apply; per-shot totals 42000 flat + 21% preserved via Nuclear_Super main Damage 1400 * 10 Ticks (MaxRadius 9000) and percentage Damage 1 * 7 Ticks (Spread 500, MaxRadius 4500); old SpreadDamage FireDeath/Incendiary shape and AffectsParent: false preserved; audit_warhead_split baseline 945->944, find_empty_warhead 0, find_orphan_old_keys 0, audit_balance_drift clean, boot-gated; then MonsterTank120mm (RedAlert/Soviets) repointed ^NuclearWarhead to ^Warhead_Nuclear_Super + ^Effect_Nuclear_Super, kept ^Warhead_CannonHE_Heavy and ^Effect_CannonHE_Heavy, with flame-thermobaric child MonsterTank120mmThermobaric inheriting the same nuclear/cannon split plus its own ^Warhead_Flame_Heavy/^Projectile_Flame_Heavy/^Effect_Flame_Heavy; main totals preserved (CannonHE_Heavy 40000 flat/20%, Nuclear_Super 4000*10=40000 flat and 2*10=20% percentage, AffectsParent: true, ValidRelationships: Enemy, FireDeath/Incendiary); old Report: nukemisl.aud retained; fixed order so ^Effect_CannonHE_Heavy is first and ^Effect_Nuclear_Super second, preserving Cannon craters and nuke Smudge1/2/3/Concrete/ShieldHit; audit_warhead_split baseline 944->942, find_empty_warhead 0, find_orphan_old_keys 0, audit_balance_drift clean, boot-gated; then TorpTubeThermobaric (RedAlert/Shared) repointed ^NuclearWarhead to ^Warhead_Nuclear_Super + ^Effect_Nuclear_Super, kept ^HeavyMissile as the unresolved old half, preserved torpedo projectile/v2/bubbles/150 speed and report torpedo1.aud, nuclear totals preserved (1600*10=16000 flat, 1*8=8% percentage, MaxRadius 9000/4500, Spread 1000/500, FireDeath/Incendiary, AffectsParent true, ValidRelationships Enemy, TargetActorCenter false), removed unwanted Glow, effect order keeps HeavyMissile ShieldHit 10/Concrete 200 with local nuke_small/kaboom22/ImpactActors true; audit_warhead_split baseline 942->941, find_empty_warhead 0, find_orphan_old_keys 0, audit_balance_drift clean, boot-gated; then JapanesePlasmaBomb (RedAlert/Japan) reparented ^HeavyBomb to ^Warhead_Demolition_Heavy + ^Effect_Demolition_Heavy while preserving chemical and flame 3-way split, kept per-shot totals (10000 flat + 5% percentage), matched old HeavyBomb falloff shape by setting MaxRadius 3200/1600 on the 6-step Demolition_Heavy family, restored poof primary explosion via local Warhead@Effect1 override, preserved blueartexp/blue_building_napalm effects and hakureiring bullet projectile with blue_smokey trail, review_resolve_diff OK, audit_warhead_split count 941, audit_balance_drift clean, phase_b_survey single-with-new count down to 1, boot-gated; then TorpTubeThermobaric (RedAlert/Shared) finished reparenting the remaining ^HeavyMissile to ^Warhead_MissileAP_Heavy + ^Projectile_Missile_Heavy + ^Effect_MissileAP_Heavy, keeping ^Warhead_Nuclear_Super + ^Effect_Nuclear_Super; missile half kept per-shot totals (16000 flat + 8% percentage) using family MaxRadius 4000/2000, valid targets Water/Underwater/Bridge/Structure, ValidRelationships Enemy, bespoke torpedo projectile preserved with -Projectile:, local Warhead@ShieldHit Duration 10 and -Warhead@Glow: kept, nuke_small/kaboom22.aud effect preserved, review_resolve_diff OK, audit_warhead_split count 941, audit_balance_drift clean, phase_b_survey single-with-new count 0 (all finish candidates done), boot-gated; then SCUDNUKE/SCUDNUKEThermobaric (RedAlert/Soviets) collapsed 15 stacked old full-stack inherits (HeavyMissile/MediumMissile/LightMissile/HeavyBomb/ShrapnelWeapon/Grenade/HeavyChemicalWeapon/MediumChemicalWeapon/LightChemicalWeapon/HeavyFlameWeapon/MediumFlameWeapon/LightFlameWeapon/TankDestroyerCannon/FlakWeapon/NuclearWarhead) into ^Warhead_Nuclear_Super + ^Effect_Nuclear_Super; per-shot totals 20000 flat + 10% preserved via Nuclear_Super main Damage 20000 (10-tick AreaDamage, MaxRadius 9000, Spread 1000) and percentage Damage 10 (10-tick AreaDamagePercentage, Spread 500, MaxRadius 4500); ValidRelationships Enemy, AffectsParent true, FireDeath/Incendiary, TargetActorCenter true inherited from family; V2 Bullet projectile retained (Image V2, Speed 240, Inaccuracy 240, LaunchAngle 80, smokey trail, contrail colors); local kaboom22.aud impact sound kept; SCUDNUKEThermobaric child still overrides with its own contrail width/length; review_resolve_diff flags expected (15 duplicate 20000 warheads collapsed to 1 + effect stack simplified to nuke_explosion), find_empty_warhead 0, find_orphan_old_keys 0 real, audit_warhead_split broadcast baseline 941->939, audit_balance_drift clean, phase_b_survey mixed 282 in 210 groups, boot-gated; then A2 W24 5-pack (NuclearMaverick -> ^Warhead_MissileHE_Heavy, ThermobaricNuclearMaverick -> ^Warhead_MissileThermobaric_Heavy, MonsterTank120mm -> ^Warhead_CannonNuke_Heavy, TorpTubeThermobaric -> ^Warhead_MissileNuke_Heavy, MonsterTank120mmThermobaric -> ^Warhead_CannonFire_Heavy) preserving per-shot totals; SCUDNUKE/SCUDNUKEThermobaric left on ^Warhead_Nuclear_Super pending maintainer call; audit_upgrade_regression + review_batch_diff blast-shape reporting added; boot-gated; then A6 batch (105mmThermobaric -> ^Warhead_CannonFire_Medium 12000 + napalm, HammerTankCannon and KotinCannon -> ^Warhead_CannonHE_Heavy 12000 each, Kotin retains radiation) preserves per-shot totals and effects; `multi_main_fired_weapons` 908→905, `audit_warhead_split` baseline 924→921; `review_resolve_diff` clean, `find_empty_warhead` 0, `find_orphan_old_keys` 0, `audit_doc_claims` 19 green, `extract_stats` redalert_soviets re-extracted, boot-gated | Claude | — |
| **W25** | Versus mean-normalisation to 100 + class tilt + Shield rebuild + the ARMOR-PLATING LAYER | ✅ S1–S4 SHIPPED 2026-08-16/17 (`78568a36d`..`99deed28d`). **E1 + E4 FIXED** (`30ead6d4b`, `761e79ed9`). ⛔ **S5 is NOT "run `--confirm`" — see the correction below: `--confirm` is a NO-OP until targets are written into the ledger, and that needs W11's sign-off.** | Claude | — |

| **W26** | **Retire `DamageMultiplier` (R1) — case by case, 369 live declarations** | 🔵 STARTED 2026-08-17: the shield 150% is DELETED. Inventory + rules below. | Claude | — |
| **W27** | Move inline Warhead@Effect* nodes into ^Effect_* templates (superweapons exempt) | 🔵 GUARD LANDED: `tools/audit/audit_inline_effects.py` now reports 665 concrete weapons with 815 inline effect nodes; superweapon auto-exemption removes 37 weapons/44 nodes. Next: adopt existing `^Effect_*` families and create missing families where none exists. Boot-gate per batch. | Devin | W24 ✅ |

**Order of work — §0a is binding and supersedes any per-item ordering below:**

    W24  (one damage warhead per weapon)
     └─> W23  (retrofit the legacy templates; W24 dissolves its blocker)
          └─> A5  (retire the remaining inline-`Versus` weapons onto templates)
               └─> class anchors → fit_class per class → W11 sign-off
                    → targets into the ledger → apply_balance --confirm → boot gate

The meter items (W7, W9, W10) and W12 are INDEPENDENT of that chain and may run in
parallel — they touch different files (§2). The older "W2 ∥ W3 → W4 → …" sequence predates
§0a and is retired: W2–W6 and W15/W16 are done, and pricing is explicitly gated behind the
weapon rebuild.

---

## 1a. W26 — RETIRING `DamageMultiplier`, CASE BY CASE

**Honest status first:** R1 (§W21, below) has said *"`DamageMultiplier` is abolished"* since
2026-08-12, but **it had no board item and no inventory**, so nothing executed it and it was
carried in conversation only. That is exactly how a ruling rots. This is the item.

**Maintainer 2026-08-17:** *"we want to remove all the damage multipliers and only keep those
that are absolutely necessary where we don't have a real answer yet. But mark them still for
later to replace them with a new mechanic. However some multipliers are still intended
especially those with status effects so yeah... we need to remove them on a case by case
basis."*

**354 live declarations** (683 in the tree; 314 sit in DEAD files such as `rules/wh40k.yaml`
and `rules/wz2100.yaml`, which `mod.yaml` does not load — do not "fix" those, delete the files).
Was 369 before the shield-150% deletion below. ⚠ **This count is registered in
`docs/audit/doc_claims.yaml` and re-measured by `audit_doc_claims.py`** — it went stale within
the same session it was written, and the audit caught it, which is precisely why the registry
exists. Update both together.

| category | count | median | disposition |
|---|--:|--:|---|
| UPGRADE-granted | 128 | 80 | → **convert to armor AMOUNT** (R1: a 15% reduction becomes +15% of HP as armor). Price into the upgrade (E5). |
| other condition | 113 | 80 | ⬜ **needs sub-classification** — the biggest unknown, do this before touching them |
| UNCONDITIONAL | 100 | 80 | → **fold into HP.** Pure baseline armor; an unconditional `Modifier: 80` is exactly `HP x 1.25` |
| PHYSICAL STATE / stance | 12 | 75 | **KEEP** — deployed/crouched/garrisoned is a genuine rate change |
| TEMPORARY ability | 10 | 80 | **KEEP** — Iron Curtain, chrono, invulnerability |
| VETERANCY / rank | 5 | 75 | → **grant HP instead** (see the correction below) |

**Two "no-brainer" sweeps — ⛔ ONE OF THEM WAS WRONG, and it nearly shipped:**

* ~~**20 declarations are `Modifier: 100`** — literal no-ops. Delete.~~
  ⚠⚠ **FALSE, measured 2026-08-17. Only ONE of the 20 is a no-op.** A `Modifier: 100` on a CHILD
  is not a no-op — it **CANCELS an inherited value**:

  | | | |
  |---|--:|---|
  | `^ScoutInfantryTemplate` declares | **50** | scouts take HALF damage — 2× effective HP |
  | actors that CANCEL it with a local `Modifier: 100` | 19 | the migrated ones — **deleting these restores the 50% reduction** |
  | actors that still RESOLVE to 50 | **16** | ⚠ un-migrated: double durability, unpriced |
  | `^CloseCombatInfantryTemplate` declares | 100 | the only genuine no-op (4 actors, nothing overrides it) |

  I wrote the deletion sweep, and the assertion in it (*"each node is exactly two lines"*) is what
  caught the error — it hit `Modifier: 50` on the template and stopped. **The scan was asking the
  wrong question**: it checked whether any DESCENDANT overrode the key, when the danger was an
  ANCESTOR declaring it. ⭐ **A no-op test must be RESOLVED, never read off the source node.**
  Claim `unmigrated_scout_damage_multiplier` now measures the 16 every audit run.

  Consequence for W26: these 19 can only be deleted **together with** the template's `50`, and
  only after the remaining 16 scouts get the 2×-health bake through the pipeline — i.e. it is a
  balance change needing a maintainer order, not a cleanup. FORMULA_V2's claim that the bake
  *"replaced"* the reduction was true for 19 of 35.
* 6 are `Modifier: 0` (true invulnerability) and 1 is `1000`; leave those, they are deliberate.

### THE PRINCIPLE (use this to decide any case not listed)

**`DamageMultiplier` is the right primitive for a RATE; a pool/bar is the right primitive for
an AMOUNT.** So:
* an **unconditional rate reduction** is indistinguishable from more HP → fold it into HP;
* a **conditional rate change** (stance, status, temporary power) stays a multiplier;
* an **amount** of extra durability becomes a pool (shield / armor plating).

⚠⚠ **CORRECTION — veterancy.** I recommended *keeping* the veterancy multipliers on the
rate-vs-amount argument, and the maintainer accepted that. **R1 had already ruled the other
way and R1 is right:** veterancy *"stops granting damage multipliers and grants HP instead —
currently veterancy gives NO HP at all, only invisible multipliers. **HP is visible in the unit
stat widget; a multiplier is not.**"* That legibility argument beats mine, and it does **not**
create the extra health bar the maintainer was worried about — it raises HP on the bar that is
already there. 5 declarations, so the job is small; the re-pricing is the real cost.

### ✅ DONE — the shield 150% penalty (2026-08-17)

`DamageMultiplier@shielded: Modifier: 150` in `defaults.yaml` (one block, inherited by all 56
always-on-shield actors). Deleted, because it **duplicated and fought** what it stood for:
`Armor@shielded` already routes hits through the `Shield` Versus row, whose entire design is
that energy weapons hurt shields (Tesla 369) and kinetics do not (Melee ~76). A FLAT 1.5x
scaled both ends equally, adding no counter-play — an unmanaged extension of the Shield ladder
living OUTSIDE its designed `[100,400]` window (1.5x would put Tesla at 553). It also hid the
pool's worth: a shield point read 0.540 HP from the ladder but was really 0.360.

⚠ **This is a BUFF and is not yet paid for.** A shield point went 0.360 → 0.540 HP, so the 56
actors' effective HP rose from +38.6% to +57.8% over raw. `audit_survivability_pricing.py` has
the per-actor numbers; the cost correction belongs in the same pass that prices the shields.

⚠ **`Modifier` is `[FieldLoader.Require]`.** Two actors (`steelconsortium_stalker`,
`steelconsortium_whiterabbit`) re-declared `DamageMultiplier@shielded` only to widen the
condition, inheriting the parent's `Modifier`. Deleting the parent alone would have crashed the
boot with a missing-required-field error — the same bug class as the empty-warhead crash, where
removing a template node orphans bare child overrides. **Always scan for dependents that
inherit a required field before deleting a template block.**

### ⬜ PROPOSED — halve unarmed-building HP, give them a shield (maintainer 2026-08-17)

*"for non defense buildings (which are not priced from the balance formula) you need to half
their HP and give them 200% shield from their HP so the effective health is about the same
right?"*

**The identity is right, and there is an EXACT figure.** Measured:

| pool, as % of the HALVED HP | resulting effective HP |
|--:|--:|
| 150% | 0.902× (−9.8%) |
| **186.8%** | **1.000× (0.0%)** |
| 200% | 1.035× (+3.5%) |

⭐ **The break-even pool is `100 / shield_hp_factor` = the MEAN VERSUS VS SHIELD itself
(186.8%).** Not a coincidence: converting HP into an equal-value shield means undoing exactly
the average penalty the Shield row applies. So **186.8% is the derived, self-updating number**
and 200% overshoots by 3.5%. Write it as a formula, never as a literal.

⚠⚠ **BUT THE IDENTITY HIDES THE REAL CONSEQUENCE — this is the largest single lever on weapon
pricing in the project.** Unarmed buildings hold **more HP than the entire unit roster**:

| group | actors | total HP |
|---|--:|--:|
| armed buildings (defenses, formula-priced) | 107 | 18 161 500 |
| **unarmed buildings (the target)** | **1 016** | **238 205 500** |
| everything else (units) | — | 129 248 940 |

The `Shield` row's share of all roster raw damage is an INPUT to `target_model.weighted_versus`
→ `K` → every weapon's price. Converting the unarmed buildings moves it:

```
Shield row share TODAY : 1.432%
Shield row share AFTER : ~27.5%     = a 19.2x increase in the Shield column's weight
```

Energy families (Tesla `Shield: 369`) would gain across the board; kinetic families (Melee ~76)
would lose. **So a change that is neutral for the buildings is emphatically NOT neutral for
weapons** — it would make "anti-shield" a mainstream weapon property instead of a 1.4% niche,
and every base assault becomes a shield fight.

**Two rulings owed before this can be built:**
1. **Is the 19× shift intended?** It is defensible — the Shield row is currently near-decorative
   and this gives it real meaning — but it is a deliberate rebalance of every weapon, not a
   side effect to absorb quietly.
2. **Do building shields REGENERATE?** `^ShieldedShieldable` carries `DamageRegenDelay: 125`.
   If regen is on, half of every building's effective HP comes back between raids — a large
   buff to turtling that the effective-HP identity does not show, and the reason harassment
   strategies would weaken. HP does not regenerate; a shield does. **This is the difference the
   arithmetic cannot see.**

⚠ Sequencing: do this BEFORE weapon pricing (§0a), never after — it moves K for the whole roster.

---

## 1b. W24 DIAGNOSIS (2026-08-17) — it is an INHERITANCE PILEUP, not a family choice

Measured before touching anything, and the finding changes the plan.

### What the 934 actually are

| shape | count | note |
|---|--:|---|
| **inheritance PILEUP** — ≥3 legacy templates inherited, no `^Warhead_*` family | **201** | the sum is an artifact |
| carries a `^Warhead_*` family inherit | 339 | real multi-warhead designs |
| 1–2 legacy inherits, no family | 116 | mostly the same disease, milder |
|| other (no legacy / no family, still multi-main) | 278 | mixed new-family or local warheads |

`wc2dragonFireVisible` — a dragon's fire breath — inherits **fifteen** legacy weapon templates:

```
^LightFlameWeapon  ^LightChemicalWeapon  ^MediumFlameWeapon  ^MediumChemicalWeapon
^HeavyFlameWeapon  ^HeavyChemicalWeapon  ^TankDestroyerCannon  ^MediumCannon
^HeavyCannon  ^Grenade  ^ShrapnelWeapon  ^HeavyBomb  ^MediumMissile  ^Chaingun  ^FlakWeapon
```

A dragon does not fire a tank-destroyer cannon or drop a heavy bomb. Each template contributes a
damage warhead, so this is accumulated copy-paste, not design. The templates most often pulled in
this way: `^ShrapnelWeapon` (100 weapons), `^Grenade` (96), `^FlakWeapon` (91), `^MediumMissile`
(85). **This is the same debt as W23/A5** — 45 legacy templates with 1193 inheritors — showing up
from the other end.

### ⚠ The finding that changes the collapse rule: 90% are BROADCAST

**576 of the 934 (61.7%) have EVERY main at the identical damage.** The worst pileups are all one
value repeated:

| weapon | mains | each | sum |
|---|--:|--:|--:|
| `SCUDNUKE` | 15 | 20 000 | 300 000 |
| `wc2cannontowerFire` | 15 | 4 000 | 60 000 |
| `wc2dragonFireVisible` | 15 | 2 000 | 30 000 |
| `SiegeTankSiegeCannon` | 14 | 10 000 | 140 000 |

That is the **broadcast fingerprint** `audit_warhead_split` was written to catch: one design
number written onto every warhead, multiplying real damage by the warhead count. **So the SUM is
frequently not a design value** — the dragon's 30 000 exists only because someone pasted 15
inherits.

⚠ **Which makes DESIGN §11b's "collapsing preserves the SUM" ambiguous here.** Preserving 30 000
locks the accident in as intent; collapsing to 2 000 is a 15× nerf.

**Historical recommendation — SUPERSEDED by DESIGN §11b.1 (2026-09-06).**
The following former argument to preserve the SUM and let pricing fix magnitude
is retained as history, not an operational instruction. In particular, preserving
a raw sum does not establish behaviour neutrality across different profiles,
targets, delays or area shapes. Current conversions follow §11b.1 and require a
reviewed payload comparison where the simple duplicated-main case does not apply.

**Former recommendation: preserve the SUM anyway.** Not
because 30 000 is right, but because:
* it keeps W24 a **behaviour-neutral refactor**, which is the only version that can be VERIFIED —
  `dump_resolved`/`review_resolve_diff` must diff empty, and a boot gate then means something;
* changing magnitudes inside a structural sweep is a hand-edited balance number (CLAUDE.md rule
  3) across ~874 weapons at once, with no way to tell a correct collapse from a wrong one;
* the whole point of §0a's ordering is that **pricing comes after structure**. The pricing pass
  will move these a long way, and that is where a 15× correction belongs — traceably, through the
  ledger.

Expect, and do not be alarmed by, large `Damage` moves for these weapons when pricing runs.

### ⚠ The guard's FAIL condition is narrower than the fingerprint it describes

`audit_warhead_split` FAIL 1 requires *"≥2 MAIN warheads **AND ≥1 side warhead** where every
warhead has the identical damage"*. The side-warhead requirement is why it reports **4** while the
fingerprint is present on **950**; its informational list adds 242 more but only at ≥8000 damage
per main. The type filter is fine (it counts `AreaDamage` as well as `SpreadDamage`, line 53).
**Widen FAIL 1 to "all mains identical" and drop the side-warhead precondition** — otherwise the
guard cannot see the thing W24 is cleaning up.

### Flame vs Inferno — KEEP BOTH, and the dragon is Flame

*"Maybe Flame or Inferno? … I'm not even sure we need to have both flame and inferno warheads at
the same time since they are basically the same right?"*

**They are not the same, and the data says so clearly:**

| | Flame | Inferno |
|---|---|---|
| ladder | **SHARP**: `None 200 … Concrete 92`, span ~2.2× | **FLAT**: `Scout 121 … Helicopter 76`, span ~1.6× |
| role | anti-infantry / anti-wood specialist | generalist — hurts everything about equally |
| `Shield` | 187–203 | **263** (couples more; it is part-energy) |
| `PHYSICS_RANK` | 0.50 (thermal) | 0.64 (blended) — vs Prism 0.76 |

Inferno's identity is not "fancier Flame": the family spec is `("Prism", "Temperature", +100, L3)`
— **a prism chassis that burns**, i.e. a HEAT RAY (`HeatRayBeam1/2`), which is why it inherits
Prism's flat ladder. Flame is fuel combustion. Merging them would delete the only *generalist*
thermal option and hand every heat weapon the anti-infantry spike.

**A dragon's fire breath is fuel combustion with an anti-infantry bite → `Flame`.**

### ✅ CONTRADICTION FOUND while checking this — FIXED (`e7fa2d57b`)

Two tables in `gen_weapon_template.py` described the same physics and disagreed about Inferno:

```
PHYSICS_RANK["Inferno"] = 0.64      # "blended energy — part field-coupling, part thermal"
COMPOSITION["Inferno"]  = {"thermo": 1.00}    # ...100% thermal, 0% energy
```

`COMPOSITION` drives the plating columns, so Inferno shipped **byte-identical to Flame** and a
REFLECTOR plating did nothing special against a focused-energy heat ray.

⚠ **The first fix — deriving the share from the rank table — was itself wrong and has been
retired.** It over-reached: the two tables answer different questions (how much a FORCE FIELD
absorbs vs what reaches MATTER), and `Railgun` is the standing disproof that they are one axis
(rank 0.78, a nearly pure kinetic slug). A derivation like that has to be overruled the moment a
ruling touches either table — which is exactly what happened when the maintainer ruled Inferno
*"mostly thermal"* while its rank puts it above the midpoint.

**Shipped instead:** `COMPOSITION["Inferno"] = {"thermo": 0.60, "energy": 0.40}` (the ruling), and
the anti-drift job moved to `rank_composition_conflicts()`, which constrains no share — a family
the shield table calls field-coupling must have SOME energy, one it calls thermal/kinetic must
have none. ⭐ Writing that guard immediately found the SAME drift a second time in **`Cryo`**
(rank 0.66, a prism chassis, still `thermo 1.00`).

Result: `Inferno` HAZMAT **49** / REFLECTOR **75** — reduced by both, far more by HAZMAT, which is
what the maintainer asked for. Full reasoning: `docs/design/ARMOR_LAYERS.md`.

⚠ Keep the general lesson: this was a **code-vs-code** contradiction, which `audit_doc_claims`
cannot catch. Two tables describing one reality need a guard of their own, and a guard that
DERIVES one from the other is too strong — it forbids a legitimate ruling.

### ⛔ THE PROCEDURE — resolve and INLINE first, remove inherits second, clean up third

**Maintainer 2026-08-17:** *"first you need to resolve all the inherits for the projectile and the
effects for each weapon before you remove any inherits. So those 15 inherits you saw earlier, they
all contributed something right? Inherit them one by one in order and resolve that, then remove
the inherits and then try to clean the massive field list up for what's important."*

**Correct, and the collapse planner alone is nowhere near sufficient** — it only chooses the
DAMAGE family. Measured on `wc2dragonFireVisible`: its local definition has 63 top-level nodes and
the full resolve has 69, of which **23 exist ONLY in the inherits**:

| what the inherits alone provide | nodes |
|---|--:|
| ground decals — `LeaveSmudge` (`Smudge`, `RA2Scorch`, `DuneRock`, `DuneSand`, `RA2Crater`, `Smudge1`, `Smudge2`, `Smudge2RA2`) | 8 |
| impact effects — `CreateEffect` (`ShieldHitEffect`, `EffectWater`, `EffectAir`) + `GlowImpact` | 4 |
| **`ApplyPhysicalState`** — the Temperature meters (Light/Medium/Heavy Flame + FriendlyFire twins) | 6 |
| `SpawnActor` `GroundFire` (burning ground), `GrantExternalCondition` `ShieldHit`, `DamagesConcrete` | 3 |
| `InvalidTargets: wall`, `TargetActorCenter: true` | 2 |

and the `Projectile` node goes from **2 local fields to 25 resolved** (`Inaccuracy: 250`,
`Shadow: true`, +21 more). **Deleting the inherits without inlining first would silently strip
every impact effect, every decal, the physical-state application, the ground fire, the glow, and
23 of 25 projectile fields** — a weapon that still lints, still boots, and looks visually broken
only in play.

⚠ It also already declares all ~41 warhead nodes locally as bare type re-declarations
(`Warhead@LightFlameWeapon: SpreadDamage`, …), inheriting their FIELDS. Removing the parents
orphans those into abstract/missing-required-field warheads — the empty-warhead boot-crash class.
⚠ And it is still `SpreadDamage` / `HealthPercentageDamage` with explicit `FriendlyFire` twins:
**never converted by the AreaDamage sweep.** So W24 on these weapons is also an A5 conversion.

**The order, per weapon:**

1. **RESOLVE** with `rs.resolve_weapon()` — it already implements the MiniYaml semantics
   (each parent spliced AT its `Inherits` line, document order, **last node wins**, so among 15
   inherits the later override the earlier and the weapon's own fields beat all of them).
2. **INLINE** the whole resolved node as a self-contained definition.
3. **REMOVE** the inherits.
4. **COLLAPSE** the damage mains to the one family (`plan_warhead_collapse.py`).
5. **CLEAN UP — this is where the real value is.** The dragon carries **8 ground decals** because
   it inherited eight games' worth; after collapsing to `Flame` it needs ONE smudge, ONE impact
   effect, ONE `ApplyPhysicalState` (Temperature). Same for the 6 physical-state nodes, which
   exist once per inherited flame tier.
6. **VERIFY** with `dump_resolved` / `review_resolve_diff` — the diff must show ONLY the intended
   collapse — then boot-gate the batch.

⚠ Step 5 cannot be automated safely: choosing which of eight decals a Warcraft dragon should
leave is a design call. Steps 1–3 are mechanical and verifiable; steps 4–5 need the review table.

### What is still judgment, and what is not

The family choice is NOT "which of 15 legacy templates wins" — it is **"what is this weapon?"**,
which its name, projectile and report answer directly (a dragon breathing fire → `Flame`). That
makes it reviewable at a glance rather than a research task per weapon, so the next step is a PLAN
tool that proposes one family per weapon with that evidence attached, for maintainer review before
any yaml moves.

---

## 1c. ⛔ W24 BRANCH REVIEW (2026-08-19) — what the `d2k_projectile_effect_split` batch got wrong

> _Branch renamed 2026-08-22 to `weapon_structure_and_warhead_fold`. The D2K projectile/effect
> split it was named for merged as PR #133 on 2026-08-20; the branch then went on to carry W18
> basis points, the AreaDamage fold, the physics blast shapes and the hitscan projectiles, so
> the name described 18 of its eventual 75 commits. The old name is kept in this heading
> because it is what the reviewed batch was called._

39 commits reviewed by resolving all 2325 weapons in an `origin/master` worktree and diffing the
invariants. **The tree boots, the `tools/tests` suite passes, `find_empty_warhead` is 0 and all doc claims are
green** — the batch is not broken. But four defect classes came out of it, three now fixed
(`47a66b6c2`) and one that needs new templates before it can be.

### ✅ FIXED — the sum was dropped on the nuclear batch

The last six commits scaled the surviving `Nuclear_Super` main to **10% of its sibling** instead of
preserving the pileup's total, so 7 weapons lost 30–93% of their damage (`SCUDNUKE` 300000 → 20000).
`WEAPON_3WAY_SPLIT.md` is explicit that the retrofit "PRESERVES the weapon's existing on-grid value
verbatim; it invents NO numbers". Restored — every value is the sibling main's own, all on the
2000-grid. The earlier D2K batch had done this correctly (`GoliathRockets_AA`: 5×6000 → one 30000),
so this was a mid-batch policy change, not a misunderstanding.

### ✅ FIXED — two silent behaviour regressions the damage diff surfaced

`SCUDNUKE` gained air-targeting (`^Warhead_Nuclear_Super` carries `ValidTargets: Ground, Water, Air`);
`HeavyOrdosCombatTankRockets` went **silent** (base resolved `Report: ROCKET1.WAV` through
`^D2KRocket`; none of the three new layers carry one).

### ✅ FIXED — one dead template

`^Effect_MissileHE_Heavy_D2K_Rocket`: created in this batch, inherited by ZERO weapons, and carrying
four `-Warhead@` removals (dead D4 crash-class node).

### ⬜ OPEN — the real defect: legacy templates were CONVERTED, never COLLAPSED

This is the one the maintainer caught by reading names: *"TS70mmChem is obviously a chemical cannon
from the name alone."* Each conversion was a faithful one-for-one swap of a legacy template for its
modern equivalent — and left the weapon with **two or three damage mains**, because the blend family
it actually needs either was not reached for or does not exist:

| weapon | mains after the batch | what it should be |
|---|---|---|
| `TS70mmChem` | `CannonHE_Medium` + `Chemical_Light` | **`^Warhead_CannonChem_Light`** — already exists, already used 6× **in the same file** |
| `TSScoopDualChem` | `CannonHE_Medium` + `Chemical_Medium` | **`^Warhead_CannonChem_Medium`** — exists |
| `JapanesePlasmaBomb` | `Chemical_Heavy` + `Flame_Heavy` + `Demolition_Heavy` | **`^Warhead_Plasma_Heavy`** — exists |
| `NuclearMaverick` | `MissileHE_Heavy` + `Nuclear_Super` | `^Warhead_MissileHE_Heavy` (see ruling 2) |
| `ThermobaricNuclearMaverick` | `MissileHE_Heavy` + `Nuclear_Super` + `Flame_Heavy` | `^Warhead_MissileThermobaric_Heavy` — **NEW** |
| `MonsterTank120mm` | `CannonHE_Heavy` + `Nuclear_Super` | `^Warhead_CannonNuke_Heavy` — **NEW** |
| `TorpTubeThermobaric` | `Nuclear_Super` + `MissileAP_Heavy` | `^Warhead_MissileNuke_*` — **NEW** |
| `D2K_Rocket_Trooper*` | three `MissileAP` levels at once | one level |
| `D2K_Rocket_Trooper2` | `Demolition_Light` + `Railgun_Heavy` + `CannonHE_Medium` | a rocket trooper firing a railgun and a cannon |

⚠ **`CannonHE_Medium` on the two TS chem weapons is PRE-EXISTING debt, not this batch's doing** —
the diff only converted `^LightChemicalWeapon` → `^Warhead_Chemical_Light`. The outcome is still
wrong, but the fix is a collapse, not a revert.

### ⚠ CONSEQUENCE OF THE FIX — the broadcast ratchet is RED at 944 vs baseline 939, and that is CORRECT

Restoring the seven totals made each weapon's mains EQUAL again, which is the guard's
"every MAIN identical" fingerprint. Exactly five weapons re-entered the count:
`NuclearMaverick` (20000+20000), `MonsterTank120mm` (40000+40000), `TorpTubeThermobaric`
(16000+16000), and the two 3-main thermobarics (14000x3, 40000x3).

⛔ **The baseline 939 was partly earned by the defect, not by collapses.** `4185340e5` lowered
`BROADCAST_BASELINE` 941 → 939 in the same commit that scaled the nuclear mains to 10% — and
under-damaging a weapon drops it out of the broadcast count just as effectively as collapsing it.
Two of those two points were bought with the bug. **Do NOT raise the baseline back to 944** (the
ratchet may only fall); the sanctioned fix is the guard's own second option — *collapse the weapon
to one main warhead* — which is exactly A2 below. The red clears when A2 lands, and it should stay
red until then, because it is now telling the truth about five weapons that really are broadcasts.

### ⬜ OPEN — template proliferation

The batch created **40 new templates, 27 of which serve exactly ONE weapon**
(`^Projectile_Grenade_Light_D2K_155mm`, `^Warhead_CannonHE_Heavy_D2K_DevBullet`, …). A template used
by one weapon is that weapon's own body relocated — it bloats the library and shares nothing. Two are
**warhead** templates, which carry `Versus`: that is the 2494-profile sprawl returning through the
back door, against the "Versus lives ONLY in `^Warhead_*` templates, a different profile means a
different template" law. Collapse them back into the shared layer or inline them on the weapon.

### 📋 MAINTAINER RULINGS 2026-08-19

1. **Blend families are DELIVERY-FIRST — `<Delivery><Payload>` — everywhere, one convention.**
   ⚠ An earlier draft of this section recommended element-first "to match the existing templates".
   That was measured on half the library and is **wrong**: the split is exactly **5 v 5**
   — delivery-first `CannonAP` `CannonHE` `MissileAA` `MissileAP` `MissileHE` against element-first
   `CannonChem` `MissileChem` `CannonFire` `MissileFire` `PhotonCannon`. Neither was "the existing
   convention", so the tie is broken on principle, and the maintainer's reading is the right one:
   delivery is the macro-type the **weapon ordering law** already sorts by, and it scales as one
   block — `Missile{AP,HE,AA,Chem,Fire,Nuke,Quantum,Tesla,Thermobaric}`.

   | rename (12 templates, **5 files** touch them) | new |
   |---|---|
   | `^Warhead_ChemCannon_*` | `^Warhead_CannonChem_*` |
   | `^Warhead_ChemMissile_*` | `^Warhead_MissileChem_*` |
   | `^Warhead_FireCannon_*` | `^Warhead_CannonFire_*` |
   | `^Warhead_FireMissile_*` | `^Warhead_MissileFire_*` |

   **NEW families** (L/M/H each, via `gen_weapon_template.py` — never hand-typed, per the ordering
   law): **`MissileNuke`, `CannonNuke`, `MissileQuantum`, `MissileTesla`, `MissileThermobaric`**.
   `MissileQuantum` is for Steel Consortium's upgraded quantum weapons; `MissileTesla` for the RA1
   Soviet tesla-missile upgrades. **`PhotonCannon` is EXEMPT** — it is a proper noun (the Protoss
   building's actual weapon), not a `<Element><Delivery>` blend.

2. **Weapon names follow the UPGRADE GATE**, because that is what the player reads in the UI —
   and where the gate itself is misnamed, the GATE is renamed too.
   `NuclearMaverick`/`ThermobaricNuclearMaverick` both belong to **one** actor,
   `ra1_soviets_su57attackbomber`. The upgrade trait `^HighExplosiveRocketsUpgradeRA1` becomes
   **`^ThermobaricRocketsUpgradeRA1`** (condition `..._upgrade_highexplosiverockets` →
   `..._upgrade_thermobaricrockets`), so the pair reads straight through:

   | | weapon | family |
   |---|---|---|
   | base | `Su57Maverick` | `^Warhead_MissileHE_Heavy` |
   | upgrade | `Su57MaverickThermobaric` | `^Warhead_MissileThermobaric_Heavy` |

   `MonsterTank120mmThermobaric` is gated on `doctrine_inferno` → `MonsterTank120mmInferno`.
   The weapon-pair rename law applies: renaming a base renames its variants.
   ⚠ **OPEN:** this drops the `Nuclear_Super` component from the Su-57 entirely (an HE→thermobaric
   missile, no nuke). Total damage is preserved either way — 40000 goes onto the single main — but
   whether an Su-57 should carry a nuclear payload at all is a design call still to confirm.

### ⛔ THE GUARD GAP — why none of this was caught

`audit_warhead_split` counts broadcasts, `find_empty_warhead` catches NREs, the boot gate proves it
loads, `doc_claims` pins totals. **Nothing checks that a weapon's family matches its identity, that a
collapse preserved the total, or that a new template has more than one user.** All three are
mechanical and belong in the audit suite BEFORE the next batch — see the plan below.

---

## 1d. PLAN — finishing the pipeline, in dependency order (2026-08-19)

⛔ **§0a still governs: weapon STRUCTURE before pricing.** Phase A is not optional preamble; every
delivery and price number measured before it lands is measuring the wrong object
(`meters_filling_before_death` claimed 534/549 and is really 146/562 for exactly this reason).

### Phase A — finish W24 (blocks everything downstream)

| # | work | gate |
|---|---|---|
| A0 | **Three new guards first**: family-vs-name mismatch, collapse-preserves-total, template-with-one-user. Cheap, and they make the rest self-checking. | tests green |
| A1a | Rename the 4 element-first blends to delivery-first (12 templates, 6 files) | ✅ DONE — CannonFire/MissileFire/CannonChem/MissileChem live, safe_rename.py preserves case, splice_templates.py runs full generator and preserves CRLF, verify_generator_sync drift 0, extract_stats --check clean |
| A1b | Generate MissileNuke / CannonNuke / MissileQuantum / MissileTesla / MissileThermobaric (L/M/H) via gen_weapon_template.py | ✅ DONE — 15 new ^Warhead_* blocks live, verify_generator_sync drift 0, extract_stats regenerated, boot-gated |
| A2 | Collapse the 7 nuclear weapons onto A1b's families — ONE main each, total preserved | ✅ DONE — `NuclearMaverick`→`MissileHE_Heavy` 40000, `ThermobaricNuclearMaverick`→`MissileThermobaric_Heavy` 42000, `MonsterTank120mm`→`CannonNuke_Heavy` 80000, `TorpTubeThermobaric`→`MissileNuke_Heavy` 32000, `MonsterTank120mmThermobaric`→`CannonFire_Heavy` 120000; SCUDNUKE/…Thermobaric stay on `^Warhead_Nuclear_Super` (already single-main, and genuinely Super-tier — moving to Heavy would be a class demotion). `review_batch_diff` main damage preserved on all 2325 weapons; `find_empty_warhead` 0, `verify_generator_sync` 0, `audit_warhead_split` 939 vs baseline 939, boot-gated. ⚠ Blast shape flattened on all five (`Ticks: 10` → family 6-step falloff): `AreaDamageWarhead.cs:282` splits Damage ACROSS ticks, so the SUM is safe, but the expanding shockwave is gone — restore it in the FAMILY via the generator if nuclear weapons should keep it, never per-weapon. |
| A3 | Fix the three misclassifications onto templates that already exist (`CannonChem` ×2, `Plasma` ×1) | ✅ DONE — `TS70mmChem` → `^Warhead_CannonChem_Light` at 6000, `TSScoopDualChem` → `^Warhead_CannonChem_Medium` at 30000, and `JapanesePlasmaBomb` → `^Warhead_Plasma_Heavy` at 30000. Main totals and weapon operation are preserved; standard family armour/blast profiles are accepted classification consequences. Upgrade audit records Ratty 0.75× Wood, Scooper 0.80× Wood, and Japanese bomber 0.96× Wood. Static audit-gated; in-game review deferred by maintainer request. |
| A4 | Rename `^HighExplosiveRocketsUpgradeRA1` → `^ThermobaricRocketsUpgradeRA1` + its condition, then the Su-57 and MonsterTank weapon pairs per ruling 2 | ✅ DONE — renamed the upgrade, condition, icon, UI text, Su-57 weapons, and Monster Tank inferno weapon across active YAML, Fluent, AI, sequences, and the survival-map script. `safe_rename.py` changed 89 references in 12 text files plus the icon; no old identifiers or dangling inheritance targets remain. Weapon values are unchanged. Static audit-gated; in-game review deferred by maintainer request. |
| A5 | Collapse the 27 single-user templates | ✅ DONE for the active W24-created set — the refreshed upstream-based census found 14 live one-user W24 wrappers rather than the older estimate of 27. All 14 are removed across three isolated batches: five small projectile/effect wrappers, five Rocket Trooper projectiles, then the Tower Missile and `mtank_pri2` projectile/effect pairs. Every sole consumer is exactly equal after full inheritance resolution. Static audit-gated; in-game review deferred by maintainer request. |
| A6 | Continue the burn-down | 🟢 BELOW-300 MILESTONE REACHED ON PR #320 — the long-lived branch combines the reviewed role cohorts with the Cameo percentage-runtime repair. Folded percentage hits execute exactly once for positional and direct-Actor impacts, and wide intermediates eliminate the old multiplication wraparound. `review_batch_diff.py` checks all 155 active/design health values and fingerprints armor profiles, targeting, relationships, projectiles, effects, physical state, non-damage warheads, and percentage output. Closure isolation detaches descendants before shared parents change. Three rule-driven tranches consolidate 226 reachable definitions (75 energy/ordnance plus 151 blast/legacy-energy definitions). The final 151-definition comparison preserves every flat total and non-damage payload; percentage arithmetic differs by at most one HP from integer rounding. The refreshed survey now reports 287 reachable stacked weapons: 212 are exact reviewed composites pinned to their complete resolved behavior and referrers, while 75 remain genuine armor, geometry, targeting, state, or progression decisions. Across the active ruleset there are 387 raw stacks, including 100 currently unreached definitions. The all-ruleset unreviewed ratchet is 175 and the reachable unreviewed queue is 75. Pricing has not started. |

#### A6 design gate — authorized batch and exact remaining cohort (2026-08-31)

Three independent reviews established the original 29-definition boundary. The maintainer then
authorized its lowest-dependency 11-definition bundle. A critical upgrade review held back the
Allied Tank Destroyer, leaving 10 authorized definitions applied across 12 resolved stacks: the two
Naxis corrosion descendants inherit their parent redesign even though they were not separate rows
in the original 29. Every converted weapon keeps its nominal flat total, target/relationship
contract, projectile, effect, cadence and auxiliary payload. Armor effectiveness, collateral
geometry and application count change intentionally; folded percentage rounding differs by at most
1 HP at a small exact set of low health values.

**Applied authorized batch — 10 weapon definitions, 12 resolved stacks.**

| weapon definitions | faction / active users | selected single family | intentional gameplay consequence |
|---|---|---|---|
| `ASDFKamikazeExplosion` | Asian Alliance Kamikaze and Airstrike Kamikaze | `Demolition_Heavy` | Concentrated, structure-biased suicide blast replaces the mixed demolition/concussion field. |
| `TSBusMortar` | Forgotten Thumper Bus | `Concussion_Medium` | Broad fragment field replaces the mixed structure/fragment profile. |
| `ConscriptMolotov` | Soviet Molotov Conscript; live `ConscriptMolotovExplode` death child | `Flame_Light` with state scale 50 | Preserves the current Temperature delivery while moving all damage onto Flame armor/geometry; the demolition field's farther outer reach disappears. The death child must retain its current route. |
| `tkm_trooper_gp25` | TKM Trooper GP-25/M203 upgrade | `Demolition_Light` with local Temperature scale 50 | Normal explosive-grenade damage identity while retaining Temperature; state delivery moves to the farther-reaching, steeper Demolition falloff. |
| `NaxiAntiTankCannon`, `NaxiAntiTankCannon_elite`, `NaxiHetzerDestroyer`, `NaxiHetzerDestroyer_elite` | Naxis Anti-Tank Cannon/Old Tank and Hetzer | `CannonAP_Light` | Matches the anti-vehicle/tank-destroyer role; removes HE splash. Corrosion descendants must retain their current resolved routes. |
| `AsianHowitzerCannon`, `AsianHowitzerCannon_elite` | Asian Alliance Howitzer | `CannonHE_Heavy` | Commits the artillery cannon to the wider Heavy HE profile instead of its current Medium/Heavy blend. |

**Closure isolation and artillery follow-up — 4 more consolidated definitions.**

| weapon definitions | isolation boundary | selected role / result |
|---|---|---|
| `AsianHowitzerSplash` | Kirov now triggers the exact legacy alias `RA2KirovHowitzerSplash` | Asian inferno splash becomes pure `Concussion_Medium`; Kirov remains byte-equivalent. |
| `TS155mm`, `TSAux155mm` | `TS155mm_bluenuke` now inherits the exact abstract legacy payload instead of the ordinary cannon | Standard and auxiliary Nod artillery become pure `Concussion_Medium`; blue-nuke remains unchanged. |
| `TSInfantryMortar` | `TSInfantryMortarChem` now inherits the exact abstract legacy payload | Ordinary Forgotten mortar becomes pure `Concussion_Medium`; the three-main chemical upgrade remains unchanged. |
| `GrenadeRA` | Ordinary, death and thermobaric routes now share an abstract legacy payload rather than inheriting through the ordinary weapon | No grenade gameplay change yet; the ordinary grenade can now be redesigned without leaking into its death/thermobaric descendants. |

The Kirov alias adds one concrete definition, so four resolved consolidations reduce the reachable
stacked backlog by three. The whole-tree report pins the added alias, exact descendant hashes,
three low-health +1 folded-percentage rounding cases, and the intentional Kirov trigger-name swap.

**Held back after critical review — 1 weapon definition.**

| weapon | reason |
|---|---|
| `AlliedTankDestroyerCannon` | Pure `CannonAP_Light` would deepen the paid `AlliedTankDestroyerCannonCryo` replacement's existing losses against Superheavy, Heavy and Concrete from roughly 0.91/0.92/0.93× to 0.75/0.87/0.83×. The base remains unchanged until the Cryo progression is designed with it. |

**Ready for a role decision after isolation — 1 weapon definition.**

| weapon | remaining decision |
|---|---|
| `GrenadeRA` | Choose ordinary explosive `Demolition_Light` or retain the current Flame identity. Its death and thermobaric routes are now independently pinned and cannot inherit the decision accidentally. |

**Approved anti-armor defense — 1 weapon definition.**

| weapon | faction / active user | approved contract |
|---|---|---|
| `tkmturretcannon` | TKM Tank Turret Bunker | The stationary defense now uses one 16,000-damage `CannonAP_Light` main, prioritizes vehicles, and presents the standard anti-tank-defense description. Its armor curve favors vehicles while retaining 74% damage against unarmored infantry. The fold keeps the old broad 300-range delivery geometry; the derived moving-target reliability is 0.8276 and effective DPS is 569.35, comparable to the TD/RA gun-turret role rather than the unintended 83.60-DPS narrow-geometry result rejected in review. It can therefore repel an isolated infantry unit without becoming an anti-infantry defense. Its structure performance is not a role constraint. |

**Approved air-first support vehicle — 3 weapon definitions and one paid-upgrade route.**

| unit | approved contract |
|---|---|
| Forgotten M113 ADATS | The long-range Air-only route now uses one 8,000-damage `Flak_Medium` main; the shorter ground route uses one 8,000-damage `MissileHE_Light` main against Ground/Water. The actor already prioritizes Air and advertises strength against aircraft and light vehicles. Purchasing Chemical Weapons now replaces both base armaments with the existing 12,000-damage `TSChemAdatsMissile` and `TSChemAdatsMissileAA` definitions instead of selecting the unchanged base weapons. The upgrade raises modeled ground and anti-air output by roughly 58% and 50%, respectively. The authored chemical ground route retains its corrosion state, cloud, positional delivery and three percentage companions; the chemical AA route retains its chemical trail and stronger Flak damage but intentionally has no Corrosion state. |

**Preserve the current hybrid — 6 weapon definitions.** The available actor descriptions do not
support choosing either half as the sole role.

| weapon | faction / active users | why it stays hybrid |
|---|---|---|
| `TSBoatcannon` | Forgotten Cannon Tug | The old Concussion proposal produces a large vehicle gain and structure loss. Demolition is closer to its current 2,000 Concussion + 16,000 Demolition weighting, but a pure profile is still an unrequested re-role. |
| `SheridanCannon` | Allied Sheridan Assault Tank | Its explicit general-purpose infantry/vehicle role is represented by the AP+HE blend. |
| `HammerTankCannon` | Soviet Hammer Tank | A main battle-tank progression should not silently become pure HE; its thermobaric descendant also inherits the parent route. |
| `KotinCannon` | Soviet Kotin Nuclear Tank | Same progression problem as Hammer, plus a nuclear-shell upgrade and thermobaric descendant. |
| `TigerCannon` | Allied Tiger Heavy Tank and Cyber Tank | One shared weapon serves two armored-combat units; pure HE is not corroborated for both. |
| `Type97Cannon` | Japan Chi-Ha Heavy Tank | No active description supports an HE-only heavy-tank role. |

**Isolate or reconstruct the closure first — 6 weapon definitions.** These parents are shared by
other factions, delivery modes or excluded upgrade descendants. Editing only the named root would
quietly change weapons outside this cohort.

| weapon definitions | active users / inherited closure | prerequisite decision |
|---|---|---|
| `RA2Terrorist` | Latin Terrorist/bomb cars, RA2 civilian bomb cars, CABAL Enlighted, Eden Starflare Lynx/Tiger; `GLDemolitionExplode`, two GL Terrorist routes, two GL Bomb Truck routes and global `GLBarrelExplode` descendants | Define the shared demolition contract and explicitly preserve or redesign every descendant, including the global structure/barrel death route. |
| `SCScourgeDroneExplosion`, `ScourgeDroneExplosion`, `SCScourgeExplosion`, `ScourgeExplosion` | Scourge Drone and Zerg Scourge attack/death payloads | Define one AA-suicide contract and protect the paired attack/death behavior; generic Demolition is not enough. |
| `TSBomb` | GDI Orca Bomber and Strike Orca | Preserve its Ground/Ship damage targeting and separate water-impact effect routing before selecting a generic bomb family. |

`tools/tests/test_authorized_role_profile_consolidation.py` pins the exact 12 resolved changes,
low-HP percentage deltas, nominal state-scale compensation, the accepted GP-25 Temperature
armor matrix, and the unchanged Molotov death payload. GP-25's effective meter is intentionally
reprofiled with the selected Demolition armor and falloff; it is not claimed as state-neutral.
`tools/tests/test_closure_isolation_consolidation.py` pins the first isolation batch and its exact
whole-tree comparison. `tools/tests/test_tkm_tank_turret_role.py` pins the approved anti-armor
profile, vehicle priority, tooltip, unchanged ordinary TKM Bunker role, and exact whole-tree
comparison. `tools/tests/test_adats_air_first_role.py` pins the ADATS ground/air profiles, Air
priority, chemical-upgrade replacements, monotonic paid progression, and exact whole-tree
comparison. `tools/tests/test_deferred_weapon_redesign_boundary.py` pins the remaining
14-definition boundary, ordered main-profile fingerprint, descendant closure and 11-direct/3-indirect
reachability split.
Until a remaining gameplay consequence is authorized, that cohort's current main-damage contract
stays unchanged. Pricing remains after W24/W23/A5 as required by §0a.

### Phase B — the physical-state half (parallel to A, different file set)

| # | work | note |
|---|---|---|
| B1 | `^Corrodible` coverage — ~100 vehicles + 42 aircraft | Zerg BOTH; Protoss/Terran vehicles+aircraft corrodible; Terran infantry poisonable; Protoss infantry neither. **Run `audit_duplicate_inherits` — adding a parent to a base template is the D1 crash route.** |
| B2 | **W9 Poison meter** — the infantry half | Corrosion is 0% infantry / 0% buildings BY DESIGN, so chemical prices are low because half their victims have no meter |
| B3 | Devin's 43 legacy Cryo `apply` → `scaled` conversions | ⛔ **AFTER** each weapon is split — converting a multi-main weapon moves it from the exempt class into the broken one |
| B4 | Requantify delivery with **relaxation** (~642 meter/shot at `ReloadDelay 60`) | one term at a time, on a corrected base |

### Phase C — pricing (ONLY after A and B)

| # | work | state |
|---|---|---|
| C1 | **W11 class-anchor sign-off — 27/27 unsigned** | ⛔ **hard blocker: no price is final until this lands** |
| C2 | W23 — rule on the 33 weapons that collide inside one family; delete the 6 obsolete templates that still bias every census | needs one ruling |
| C3 | W15 (%-twin + `reference_hp` 200000) → unblocks W17 | ready |
| C4 | W16 charge-up · W18 basis points · W19 `ExtraDamage` chips | ready |
| C5 | W13 warhead rebuild from the reference corpus | ready |
| C6 | W12 superweapons as a separate track | maintainer-led |

### Phase D — remaining meters (needs C# first)

W6 (`ModifiesCombatProportionalToPhysicalState`) → then W8 SpinUp, W10 Blind, W7 Sonic/Resonance.
⚠ `engine/` is a build output — ship these as an `OpenRA.Mods.Cameo` **shadow** if the type allows it.

### Housekeeping (not blocking, but it is the tree everyone shares)

~90 untracked files in `scratchpad/` (not gitignored), 5 stale worktrees under `%TEMP%`, local
`master` diverged (ahead 1 / behind 2), and 15 commits on this branch not pushed to its own remote.

---

## 2. FILE OWNERSHIP — how two agents work at once without collisions

One owner per FILE SET at a time. These sets are disjoint by construction:

| set | files | items |
|---|---|---|
| **A — pipeline tools** | `tools/balance/*.py`, `docs/balance/**` | W3, W4, W5, W11 |
| **B — weapon content** | `mods/cameo/weapons/**`, `mods/cameo/ContentPacks/**/weapons.yaml` | W2 |
| **C — engine C#** | `OpenRA.Mods.Cameo/**`, `engine/**` | W6 |
| **D — actor defaults** | `mods/cameo/rules/defaults.yaml` | W7, W8, W9, W10 |

⚠ **Set D is a single file — serialise W7/W8/W9/W10, never run two at once.**

⚠ **SET B'S LOCK IS RELEASED (maintainer, 2026-08-15): "you can release his lock since
Devin will not come back anytime soon".** Devin's W2 stopped on 2026-08-13 with 30 live
weapons still inheriting `^LightFlameWeapon`. Claude owns set B from now on, which
unblocks **W13 step 4, W17's content half, W18, W19 and W7** in one stroke — those were
the only things waiting on it. Finish W2's remaining 30 weapons as part of W13 step 4
rather than as a separate item; they need the same regeneration anyway.

---

## 3. THE UNIVERSAL GATE (every item, no exceptions)

```sh
python -m unittest discover -s tools/tests -t tools/tests   # all green
python tools/audit/find_empty_warhead.py                    # 0
python tools/balance/verify_generator_sync.py               # drift = 0
bash tools/audit/run_all.sh                                 # bash ONLY — PowerShell writes UTF-16
python tools/balance/extract_stats.py --check               # 0 drifted
```
then the **boot gate** (CLAUDE.md rule 1 — absolute):
1. snapshot `%APPDATA%/OpenRA/Logs/exception-*.log` count **before** launching (baseline 169);
2. rebuild first if `OpenRA.Mods.Cameo/` or `engine/` changed:
   `DOTNET_ROLL_FORWARD=LatestMajor dotnet build -c Release --nologo -p:TargetPlatform=win-x64`;
3. `launch-game.cmd`, then **grep** `perf.log` for `MenuPostProcessEffect.PostWorldLoaded`
   (never read the last line — map loading trails after it) and confirm the file's mtime
   is **after** the cutoff, so it is this run and not a stale marker;
4. 0 new `exception-*.log`; `Stop-Process -Name OpenRA -Force`;
5. **scoped `git add <files>` only** — never `-A` / `.` / `--all`;
6. update this file's status row **in the same commit**.

Commit trailer = the ACTUAL agent (CLAUDE.md rule 10). Never sign as another agent.

---

## 4. THE WORK ITEMS

### W1 — K coefficient + target model ✅ DONE (`f8421d345`)

`effective_dps = Damage_total × (burst / eff_reload) × FirepowerMultiplier × K`, with
`K = Σ_warheads share_w × versus_w × (reliability_w + secondary_w)`.

The scalable part of K (flat + chip + folded `PercentageScale`) is independent of the
Damage magnitude, so pricing inverts exactly:
`Damage_required = (target_per_shot − pct_absolute_context) / k_flat_context`, snapped to
the grid. ⚠ **Never invert `k` / `k_context`** — standalone percentage warheads are
ADDITIVE, and folded basis-point rounding is a current-shot residual. Those two make the
measurement move with Damage. Folded percentage damage itself is scalable and never a
floor (E4, corrected 2026-08-25; guard `audit_k_linearity.py`). Spec: `EFFECTIVE_DAMAGE.md`.

**VERIFY:** `python tools/balance/weapon_efficiency.py --families` prints 20 rows.

---

### W2 — `^LightFlameWeapon` → 3-way split + `^Warhead_Inferno_*` 🔵 IN PROGRESS (Devin, 2026-08-21) · owner **Devin**

**Why:** `^LightFlameWeapon` sets `Spread: 500` **and** `Range: 500`. A single-value
`Range` makes `effectiveRange` length 1, so `GetDamageFalloff`'s loop never runs and it
returns 0 — **77 live weapons deal zero flame damage** and always have. The fix is not
deleting the line; it is finishing the 3-way split (one warhead + one projectile + one
effect inherit), which removes the dead template entirely.

**Maintainer's warhead order (2026-08-11) — granted, this mapping:**

| weapons | → warhead |
|---|---|
| `HonestJohn`, `FireRockets*` | `^Warhead_MissileFire_Heavy` |
| `SiegeMortar*`, **V2 rocket** | `^Warhead_Thermobaric_Heavy` |
| `VenomLaser`, `NodTurretLaser` | `^Warhead_Laser_Medium` |
| `LaserBuggy2`, laser rifle infantry | `^Warhead_Laser_Light` |
| `HeatRayBeam1/2/3/4` | `^Warhead_Inferno_Heavy` (new) ✅ 3-way split |
| `25mmWaveforce`, `TankBusterBeamCannonCharged` | **ASK the maintainer** |

**New family** — three lines in `tools/balance/gen_weapon_template.py`:
```python
INHERIT_FAMILIES = {
    "Cryo":    ("Prism", "Temperature", -100, L3),   # existing
    "Inferno": ("Prism", "Temperature", +100, L3),   # NEW — prism chassis that burns
}
```
Named `Inferno`, not `HeatRay`: the family is the ELEMENT, not the delivery, so
non-beam flame weapons can use it later (same reason `Cryo` keeps its name).

**DONE WHEN**
- [x] `Inferno` in the generator; `splice_templates.py inferno`; generator drift 0.
- [x] Every weapon in the explicit mapping table above inherits exactly ONE `^Warhead_*`,
      ONE `^Projectile_*`, ONE `^Effect_*`.
- [ ] `^LightFlameWeapon` has zero remaining inheritors, then is deleted
      (28 matches remain, almost all multi-family mixed weapons or human-live/ASK files).
  - `HeatRayBeam1/2/3/4` now fully 3-way split with `^Warhead_Inferno_Heavy` + `^Projectile_Inferno_Heavy_HeatRayBeam` + `^Effect_Inferno_Heavy`; resolver diff identical; boot-gated.
- [x] `tools/audit/review_resolve_diff.py` run before/after on a sample of ≥10 of the
      77 — the ONLY expected change is that flame damage now lands (verified on 10).
- [x] `find_empty_warhead.py` = 0.
- [ ] Balance pass queued (77 weapons gaining real damage is a live balance change).

**VERIFY:** `grep -rc "\^LightFlameWeapon" mods/cameo --include=*.yaml` → 0

---

### W3 — Ledger split ✅ DONE · owner Claude · needs W1

`BALANCE_PIPELINE.md` §2 says the ledger is RAW STATS ONLY. Five derived fields sat in
it, and correcting the scatter model rewrote **4136 ledger lines with `mods/`
untouched** — model noise inside the artifact whose job is proving yaml ↔ ledger
equality.

**Shipped:** one `extract_stats.py` run writes two trees off the same resolve, so they
cannot desync.

| tree | a diff means |
|---|---|
| `docs/balance/<faction>.json` — raw only | **the game changed** |
| `docs/balance/derived/<faction>.json` — `k`, `avg_versus`, `effective_per_shot`, `eff_reload`, `effective_dps`, `effective_damage`, `damage_total`, `footprint`, `reliability`, `sigma` | **the model changed** |
| `docs/balance/derived/_model.json` — every constant they depend on | the model was **retuned** |

- [x] the five `effective_*` fields are gone from `docs/balance/*.json` — the split
      commit is **12 130 deletions, 0 additions**, every removed line one of the five
      names, so provably not one raw stat moved;
- [x] `docs/balance/derived/*.json`, 32 sidecars + `_model.json`; rows carry only
      `slot` + `weapon` as join keys, never a duplicated raw stat;
- [x] `audit_balance_drift` reads the raw tree **by construction** —
      `build_ledgers()` returns raw and `build_both()` is the two-tree entry point, so
      it cannot start diffing model output by accident;
- [x] `extract_stats.py --check` verifies both trees and labels findings
      `DRIFT (raw)` vs `DRIFT (model)`;
- [x] `BALANCE_PIPELINE.md` §2's ⚠ block replaced with the settled rule;
- [x] `tools/tests/test_ledger_split.py` (9 tests) pins it — the guard trips on 310
      rows of the pre-split ledgers, so it fails when it should.

⚠ **Correction to this item's original DONE list:** it required "the workbook builder
reads derived from the new path". That premise was wrong — `build_workbook.py` and
`import_workbook.py` never read the five fields even while they sat in the ledger
(`grep -n effective tools/balance/build_workbook.py` → one comment). Nothing consumes
the derived tree today; giving it its first consumer is **W11**, not W3. No consumer was
invented just to satisfy a checkbox.

Also folded in (both measured, neither changes a number): `target_model` now resolves
the roster **once** instead of twice and reuses the caller's `Ruleset` via
`use_ruleset()` — cold census 15.3s → 6.8s, full extraction of *both* trees 18s. The
armor census is byte-identical afterwards (Wood 563 … Fighter 20, reference HP 74 000).

**VERIFY:** `grep -l effective_damage docs/balance/*.json | wc -l` → 0
and `ls docs/balance/derived/*.json | wc -l` → 33

---

### W4 — Retire weapon-class K; charge-up moves to the ACTOR ✅ DONE · owner Claude · needs W1

**Maintainer ruling 2026-08-11:** chips now count in the metric, so their structural
"payment" must come off or they are double-charged. Concretely:
- `WeaponClass` / K as a per-weapon-type multiplier is **retired** — the metric measures
  what the weapon does, so the tier weight is no longer needed to stand in for it.
- **Charge-up is an ACTOR property, not a weapon one.** The actors carrying
  `AttackCharged` / `AttackTurretedCharged` / `AttackFrontalCharged` take a **0.75×**
  multiplier (a charge delay is a large real nerf), handled exactly like the documented
  Obelisk of Light case: the delay inflates the effective reload AND lowers the price.

**DONE WHEN**
- [x] `formula.dps()` no longer takes `weapon_class`; **all six** call sites updated —
      `fit_class`, `check_band`, `propose_rebalance`, `propose_class_rebalance`,
      `update_ranges`, and the workbook's **Excel DPS cell** (`build_workbook` dropped
      `*WeapClass`). The sheet is a second implementation of the same math and
      `formula.py`'s docstring promises the two agree — leaving the factor in Excel
      would have made the workbook and the module disagree silently;
- [x] `fit_class.py` reads the charge trait off the ACTOR and applies 0.75×, via the new
      `price_unit()` (extracted so the rule is testable rather than inline in `main`);
- [x] `docs/design/FORMULA_V2.md` + `ARMOR_SYSTEM` updated to state the retirement;
- [x] `tools/tests/test_formula_charge.py` (10 tests) pins the fixture
      "charged actor prices 0.75× an identical uncharged one", plus the Tesla exclusion
      and the positional-argument shift.

⚠ **Two findings that changed the shape of this item:**

1. **The ruling's own example was not covered by the ruling's own trait list.** It names
   `AttackCharged` / `AttackTurretedCharged` / `AttackFrontalCharged` and cites the
   Obelisk of Light as the model case — but the Obelisk uses **`AttackCharges`**, a
   different trait, so the three named traits would have left the cited precedent at
   full price. `AttackCharges` is therefore in `formula.CHARGE_UP_TRAITS` (4 Obelisks).
   Live counts: `AttackFrontalCharged` 5 · `AttackCharges` 4 · `AttackTurretedCharged` 2.
2. **`AttackTesla` (3 actors) is recorded but NOT discounted.** The Tesla Coil is already
   priced as a special case (ReloadDelay 100 + InitialChargeDelay 25, MaxCharges 3, its
   own K), so the generic 0.75× on top would compensate the same nerf twice — leaving a
   charging unit over-paid and cost-efficient rather than balanced. It sits in
   `CHARGE_UP_EXCLUDED_TRAITS` and **needs a maintainer ruling** before it joins.

Also resolved: `FORMULA_V2` §3b planned to compensate this same nerf as a **−0.25
negative special**. Both firing would pay for one weakness twice — and since a price cut
is a BUFF in value terms (cheaper = better per credit), the result would be a charging
unit that is over-compensated and cost-efficient, not balanced. §3b now records that the
charge half is implemented as the actor price multiplier and the special-K route must
not also fire. (The frontal-facing
−0.25 half is untouched and still future scope.)

**VERIFY:** `python -c "import sys;sys.path.insert(0,'tools/balance');import inspect,formula;print('weapon_class' in inspect.signature(formula.dps).parameters)"` → `False`
(the old `grep … | wc -l → 0` cannot pass: the docstrings that EXPLAIN the retirement
must name the retired thing. Test the signature, not the prose.)

---

### W5 — The five missing metrics ✅ DONE · owner Claude · needs W1

All approved by the maintainer 2026-08-11. Each is a named, individually-inspectable
factor in `weapon_efficiency.py` — never one blended fudge, so a price that moved can be
traced to the ONE factor that moved it. Spec + shapes: `EFFECTIVE_DAMAGE.md` §3.0.

| # | factor | shape | it bites |
|---|---|---|---|
| 1 | **overkill / TTK** | `HP / (ceil(HP/dmg) × dmg)` — waste is only the LAST shot | 200k on 50k → **0.25** |
| 2 | **range advantage** | `1 + 0.25 × (range/median − 1)`, bounded `[0.75, 1.50]` | long artillery **1.33** |
| 3 | **`ValidTargets`** | `0.5 + 0.5 × engagement share` | ground-only **0.95**, AA-only **0.55** |
| 4 | **`MinRange`** | `1 − (MinRange/Range)²` — the annulus, so area not radius | 2800/11000 → **0.96** |
| 5 | **`AttackDelay`** | ✖ **does not exist** — see below | — |

**The split that makes this safe:** factors 2–4 do NOT depend on `Damage`, so they fold
into the new **`k_flat_context`** and the pricing inversion stays closed-form. **Overkill
does** depend on Damage, so it is reported BESIDE K and never inside it — folding it in
would turn the inversion into a fixed-point iteration. `test_weapon_context.py` pins that
distinction explicitly. ⚠ Standalone percentage warheads are additive and live in
`pct_absolute_context`; folded `AreaDamage.PercentageScale` follows the main Damage and
lives in `k_flat_context`. The first E4 implementation recognized only specially named
standalone twins and no folded hits; the type-based model corrected that on 2026-08-25.

⚠ **Item 5 was based on a field that isn't there.** `AttackDelay` appears **0 times** in
the tree. Charge-up is an ACTOR trait (`AttackCharged`, `AttackCharges`, `AttackTesla`, …)
and W4 already implemented it there as the 0.75× price multiplier — which is the right
layer, since one weapon serves many actors. Nothing to add at the weapon level; no
placeholder was invented to fill the row.

**DONE WHEN**
- [x] each factor is a separate column in the derived output — `factor_targets`,
      `factor_range`, `factor_deadzone`, `overkill`, plus `k_context`;
- [x] each has a test — `tools/tests/test_weapon_context.py`, 21 tests;
- [x] `EFFECTIVE_DAMAGE.md` §3.0 documents them, moved out of "deliberately not included".

**VERIFY:** `python tools/balance/weapon_efficiency.py --families` shows
`targets · range · deadzone · overkill · K ctx`.

---

### W6 — C# `ModifiesCombatProportionalToPhysicalState` ✅ DONE (`fc45a9632`) · owner Claude

The framework's missing half: every existing proportional trait only makes things
*worse* (`SlowsProportionalToPhysicalState`, `DamageMultiplierProportionalToPhysicalState`).
A spin-**up** needs a signed one.

**Shape** — mirror `SlowsProportionalToPhysicalState`:
```
PhysicalStateName: SpinUp
ReloadDelayFrom/To: 100 / 60      # any subset of the four
RangeFrom/To:       100 / 122
SpeedFrom/To:       100 / 122
FirepowerFrom/To:   100 / 100
```
Maintainer picked **option C**: fold the readability hooks INTO this trait rather than
bolting on separate ones — an audio **pitch** scale (`PitchFrom/To`) driven by the same
meter, and a glow/overlay hook reusing the existing weapon-glow effects.

**DONE WHEN** built, `dotnet build -c Release -p:TargetPlatform=win-x64` clean, deployed
to `engine/bin`, and a CONCRETE actor instantiates it (an abstract-only template proves
nothing).

**VERIFY:** boot with a gatling actor present, no `Cannot locate type` in the log.

---

### W7 — Sonic → `Resonance` meter ⬜ READY · owner either

Needs **no new C#** — `DamageMultiplierProportionalToPhysicalState` and
`SlowsProportionalToPhysicalState` already exist.

```yaml
^Warhead_Sonic_<Level>:
    Warhead@Sonic_<Level>: AreaDamage
        PhysicalStates:
            Resonance: 100        # replaces the whole _Debuff GrantExternalCondition
```

**The design rule that keeps it distinct from Corrosion** (maintainer-approved):

| | Corrosion | **Resonance** |
|---|---|---|
| role | attrition — kills on its own | **force multiplier — kills nothing** |
| damage | DoT | **none, ever** |
| decay | slow, lingers | **fast, dies with the beam** |
| identity | poison you flee | a spotlight your team shoots into |

Sonic becomes the only debuff that deals no damage of its own: worthless solo, doubles
the army's output in a group. Emit via the generator's `FAMILY_PHYSICAL_STATE`, not by
hand. Retire `^SonicDebuff` + the `_Debuff` warheads once the meter is live.

**DONE WHEN** meter defined on defaults; generator emits it; `_Debuff` warheads and
`^SonicDebuff` removed; the predator/waveforce/IonPulse hand-grants re-pointed or
removed. Expect a balance pass: one hit no longer gives the full debuff.

**VERIFY:** `grep -rc "SonicDebuff" mods/cameo --include=*.yaml` → 0

---

### W8 — Gatling ladder → `SpinUp` meter ✅ DONE (`c0d6abf70`) — all 43 actors, `GattlingSpeed` = 0 · needs W6 ✅

**47 actors** × 20–30 multiplier traits ≈ **1340 trait objects**, roughly **40% of all
3197 multiplier instances in the mod**, in ten visible 5% steps. A meter replaces them
with 3–4, continuously.

⚠ **CORRECTED 2026-08-15 — this item's own end-points were wrong, and building from
them would have inverted a stat on all 47 actors.** The line below used to read
"`1.02¹⁰ = 1.219` range/**speed** … max → 60% reload / 122% range / **122% speed**".
Verified against `defaults.yaml`: **all 30 `SpeedMultiplier` entries in
`^GatlingSpeedUpUnitBehavior` are `95`, not `102`.** A spinning-up gatling unit gets
**SLOWER**, not faster — which is the better design anyway (you root yourself to gain
fire rate), and it is what the mod has always shipped. The spec had silently copied the
range direction onto speed.

Current ladder resolves to `0.95¹⁰ = 0.599` reload (fire rate ×1.67),
`1.02¹⁰ = 1.219` range, and `0.95¹⁰ = 0.599` speed — those are the **end-points** the
meter must reproduce (0 → 100%, max → **60% reload · 122% range · 60% speed**). The
turret template has no speed term at all; only the unit one does. Elite variant fills faster
(`RequiredShotsPerInstance: 1,1,1…` vs `1,2,3…`, `RevokeDelay` 15 vs 30) → same meter,
higher fill rate.

**DONE WHEN** `^GatlingSpeedUpTurretBehavior` / `…UnitBehavior` / `…SpecialUnitBehavior`
are meter-based, all 47 actors verified in `review_resolve_diff`, end-points match.

**VERIFY:** `grep -c "GattlingSpeed" mods/cameo/rules/defaults.yaml` → 0

---

### W9 — `^Poisonable` → `Poison` meter ⬜ READY · owner either

A Corrosion clone with a different victim class: **corrosion eats vehicles, poison hurts
infantry, flame does both** — a clean three-way split of the DoT space.

Maintainer's design: the Yuri Virus (and friends) spawn a **gas cloud**; the cloud does
very little direct damage but **fills the Poison meter for as long as a unit stands in
it**, and the DoT scales off the meter. Dose-response — one dart ≠ a lingering cloud.
`ChangesHealthProportionalToPhysicalState` already exists, so no new C#.

**DONE WHEN** meter on defaults, cloud weapons feed it via `PhysicalStates`, the old
binary `poisoned` condition is retired, infantry-only gating verified.

**VERIFY:** `grep -rc "Condition: poisoned" mods/cameo --include=*.yaml` → 0

---

### W10 — `^Blindable` → `Blind` meter ⬜ READY (unblocked — W6 ✅) · owner either

Today: binary, range/vision/detection → 20%. A cliff. Maintainer's spec:
- scale range **100% → 20%** proportionally with the meter (20% at full blind);
- **at FULL blind only**: disable the weapon entirely, show the `blinded_icon`
  decoration, and apply the `blinded` **Targetable** type so blinding units retarget
  instead of wasting shots on an already-blind target.

Needs W6 for the proportional range scaling; the full-blind cliff stays a
`GrantConditionOnPhysicalState` at max.

**VERIFY:** `grep -c "RequiresCondition: blinded" mods/cameo/rules/defaults.yaml` → only
the max-meter uses remain.

---

### W11 — Wire K into `fit_class.py` ✅ BUILT · ⬜ awaiting maintainer sign-off

W3/W4/W5 were all ✅ long before anyone re-read this line — the ⛔ was stale, which is
why this sat "blocked" while its dependencies were done.

**Built:** `--use-k` prices on the K-adjusted `effective_dps` from the derived sidecar
(accuracy, spread, falloff, range, dead zone, reachable targets) instead of raw
damage/reload; `--compare-k` prices the class BOTH ways and writes the evidence report.
K is read from the sidecar, never recomputed, so there is one definition of it. The
anchor is re-fitted in whichever mode is running — pricing members on K against an
anchor fitted on raw DPS would compare two scales and make every delta meaningless.
`--compare-k` deliberately writes **no candidate anchor**: it is a report, not a fit.

**⚠ TWO PIPELINE BUGS FOUND BY ACTUALLY RUNNING IT** — both pre-existing, both far more
consequential than the flag:

1. **43% of the roster was invisible to pricing.** `unit_inputs` skipped every armament
   carrying any `requires` at all. But `!rank-elite` is the BASE weapon, not an
   upgrade gate — as is `!forgotten_upgrade_chemicalweapons`, and so on. **371 of 863
   actors with priced armaments came out at zero DPS** and dropped out of class fits
   entirely, `tiger.nax` — the recorded `mbt` anchor — among them, which is why fitting
   `mbt` failed outright. Replaced with `formula.condition_holds_by_default()`: evaluate
   the condition with every named condition FALSE, i.e. *the weapon the unit fires as
   built*. Coverage **57% → 96%**; the 37 still at zero genuinely have no as-built weapon
   (transport- and deploy-gated). 18 unit tests, and it fails CLOSED on an expression it
   cannot parse — a wrong price looks authoritative, a missing one does not.
2. **The class-member scan never ran.** The anchor was unioned into `actors_filter`, and
   a non-empty filter switches off the `design.class_anchor == cls` branch — so every
   run collected exactly ONE unit (the anchor) and wrote a one-row validation table for
   the whole class. The anchor now passes through `always=` instead.

**First result — `docs/balance/derived/k_comparison_mbt.md`, 40 units:**
median price shift **+1.2%** (range −50% … +43%), but it moves prices AWAY from current
cost for **30/40** units. Individual movements are large and plausible in direction
(`protoss_dragoon` −51%, `tkm_trenchtank` +43%). Sanity check passed: the raw anchor
reproduces the documented Tiger identity exactly, O0 = P0 = Q0 = cost0 = 800.

**⚠ That result does NOT justify flipping the pipeline yet**, and the honest reading is
that it cannot on its own: current costs are themselves unbalanced — that is why this
program exists — so "moves away from current cost" is not automatically evidence
against K. What would settle it is running `--compare-k` on a class whose costs the
maintainer already considers CORRECT, and checking whether K pulls those towards or
away from them.

**VERIFY:** `python tools/balance/fit_class.py --class mbt --anchor tiger.nax --compare-k`
→ report in `docs/balance/derived/`, `class_anchors.json` untouched. Sign-off still owed
in `anchor_decisions_log.md` before `--use-k` becomes the default.

---

### W12 — Superweapons as a separate track ⬜ READY · maintainer-led

Maintainer 2026-08-11: superweapons are **not tied to a unit** and are not priced by the
unit formula — the blob cap in W1 exists partly because a superweapon footprint would
otherwise claim 50 kills. They need their own process (charge time, one-per-base,
counterplay), tracked separately from class anchors.

---

### W13 — Warhead system rebuild from the reference corpus 🔵 steps 1–4a DONE (measured profiles LIVE on all 10 sourced families + 8 blends) · owner Claude

Reference data: `docs/reference/versus_raw.json` — **2494 warhead profiles, 14 sources**,
built by `tools/reference/extract_versus.py` (+ `extract_mix_ini.py` for Mental Omega).

**Measured findings that drive the rules below** (all reproducible from that file):

| finding | number |
|---|---|
| field median profile span | **85** raw · **100** counting damage warheads only (Cameo: Light 90 · Medium 75 · Heavy 60 · Super 45) |
| field distribution | ⚠ **CORRECTED 2026-08-15 — see the box below.** Raw: 65% sharp · 7% moderate · 27% flat. **Damage warheads only: 84% sharp · 9% moderate · 7% flat** |
| Mental Omega alone | median span **95**, 34% flat — a BARBELL: many hard counters AND many all-rounders, few in between |
| archetypes occupied | Cameo **14** · field **28** |
| Cameo's most common archetype | `BLD>INF>VEH FLAT HE` at **17.8%**, vs **0.4%** in the field |
| multi-warhead flattening | 1 warhead → median span **75**; 2+ warheads → **58**. Worst cases lose ~250 span (`VonSniperLockdown` 7 warheads: 290 → 30) |
| live weapons with 2+ warheads | **1335 of 1972 (68%)** — the size of the migration |

**THE RULES (maintainer, 2026-08-11):**

1. **Exactly ONE damage warhead per weapon.** This is the balance mechanism, not
   housekeeping: mixing warheads averages their profiles and destroys the counter. The
   flattest weapons in the game today are the mixed ones, not the designed ones.
2. **Archetype = macro order × sharp/flat × HE/AP direction × air position.** Aim to
   occupy the field's ~28 rather than today's 14.
3. ⚠ **REVISED 2026-08-15 — the field is far sharper than this rule assumed.**
   The original rule read *"most warheads SHARP; **~20% intentionally FLAT**, the field's
   own ratio"*. That 20% was an artifact of counting warheads that carry **no damage at
   all**: 182 corpus rows are ALL-ZERO and 186 more peak at ≤5 — death animations
   (`AvatarDeathWH`), dummies (`BioDummyWH`), repair guns, de-evolution and EMP-only
   effects. A zero profile has span 0, so every one of them was filed as a "flat
   all-rounder". They are plumbing, not design.
   Excluding them (`cluster_versus.py`, `DAMAGE_FLOOR`), the real field ratio is
   **84% sharp · 9% moderate · 7% flat** — flat is roughly **a third** as common as the
   rule assumed. So: keep flat as a deliberate, RARE identity (Sonic, Magic, Tesla) at
   under 10% of families, and make everything else genuinely sharp. MO still proves both
   extremes can coexist without a mushy middle.
4. **CLUSTER the reference values, never average them.** Averaging all 2057 three-class
   profiles yields span **24** against a field median of 87 — it collapses exactly the
   rock-paper-scissors the corpus was gathered to produce. Take the median WITHIN each
   archetype cluster.
5. **Wild values allowed** — no fixed step law. Sources run to span 295 (`LaserTur`:
   infantry 320, heavy 25). Cameo's step law caps at 90.
6. **The ordering law still governs** (best→worst by macro priority + sub-ladder). It is
   what keeps "wild" coherent rather than random.
7. **Thematic fit per family**: flame = `INF>BLD>VEH · SHARP · HE`, missiles = the
   air-capable counterpart of cannons, etc.
8. ⚠ **EVERY warhead damages EVERY armor type — never zero** (maintainer ruling). A
   landed helicopter is a legitimate target for a flame tank. "Cannot fight air" is
   expressed by putting the aircraft armors at the END of the ordering (low, non-zero),
   NOT by omitting them.
   **Cameo's four dedicated aircraft armors are a deliberate improvement over the source
   mods, not a divergence to fix.** Those engines share one armor type between aircraft
   and tanks, so they simply cannot express "devastating vs aircraft, mediocre vs tanks,
   still good vs infantry" — the flak-cannon profile. An earlier draft of this item
   listed Cameo's 100%-air-coverage as a gap; that was wrong.
9. ✅ **Prerequisite — the `%`-twin. SATISFIED by W15.** The twin used to be
   `per // DAMAGE_STEP` (integer division), so every percentage warhead silently became 0
   below one grid step — hard immunity by rounding. `formula.percentage_twin` now rounds
   half-up and never falls below 1. The grid moved only after that landed.
10. ✖ **VOID — `FirepowerMultiplier` does NOT survive.** This rule was written before the
    maintainer's 2026-08-11 ruling that **no weapon is shared**, which removed its entire
    premise ("one weapon serves many actors"). The knob is retired; see **W17**.

**PROGRESS (2026-08-15) — step 1 of W13 is DONE: the corpus is clustered.**
`tools/reference/cluster_versus.py` → `docs/reference/WARHEAD_REFERENCE.md`. It places
**1876 damage profiles into 85 archetypes** (Cameo occupies 14) keyed on
`macro order x sharp/flat x HE/AP`, and reports the **median profile WITHIN each cluster**,
never a global average (rule 4). The biggest occupied archetypes, with the number of
independent mods backing each:

| archetype | n | sources | median span | INF | VEH | BLD |
|---|--:|--:|--:|--:|--:|--:|
| `INF>VEH>BLD sharp HE` | 345 | 14 | 100 | 100 | 47 | 23 |
| `INF>BLD>VEH sharp HE` | 250 | 14 | 100 | 100 | 47 | 63 |
| `VEH>BLD>INF sharp AP` | 114 | 13 | 90 | 25 | 92 | 63 |
| `VEH>INF>BLD sharp HE` | 82 | 10 | 110 | 60 | 115 | 24 |
| `BLD>INF>VEH sharp HE` | 71 | 10 | 150 | 110 | 77 | 197 |

⚠ **The AIR axis is NOT measurable from this corpus and must not be faked.** Only **37 of
1876** profiles define any aircraft armor at all: the source engines share one armor type
between aircraft and ground vehicles. That is precisely why Cameo's four dedicated aircraft
armors are an improvement (rule 8) — and it means each archetype's air POSITION is a
maintainer design decision, with the corpus contributing nothing. The tool says so in its
own output rather than emitting an invented number.

**STEP 4a — SHIPPED. The measured profiles are live in `weapons.yaml`.**

The even ramp is gone from every family the corpus can speak for. `table()` in
`gen_weapon_template.py` survives only as the fallback for the families Cameo invented.

| piece | where |
|---|---|
| frozen data | `docs/reference/family_profiles.json` — 10 families x 3 levels, `blend` aggregation, provenance (`n`, `mods`, `origin`) per cell |
| exporter | `propose_family_profiles.py --json` |
| consumer | `gen_weapon_template.reference_main()` — order still from `build_order()` |
| impact report | `tools/balance/report_versus_change.py <rev>` |

**Why the data is FROZEN into a committed JSON rather than derived at generation time:**
`survey_platforms.py` traces the source mods' INI files out of `~/Downloads`. Nobody else
has those, so a generator that imported the derivation would only run on one machine.

**Measured result:** 51 warhead tables changed. Profile SPAN (the counter-play) went from a
uniform 60/75/90 to **72–268**. Mean lethality moved **1.25x** on average (0.79x–2.04x), and
across 2436 live armaments K moved **median 1.07x, mean 1.16x** (0.88x–1.98x). 36% of
armaments did not move at all — those are the ~878 legacy nodes still declaring inline
`Versus` on `SpreadDamage` (item A5), which the templates do not reach.

⚠ **That K shift is not yet paid for.** `Damage` still has its old values, so a family whose
mean rose 1.4x currently deals 1.4x.

⛔⭐ **AND `apply_balance --confirm` IS NOT THE CORRECTION — MEASURED 2026-08-17.** Dry-run on
four factions (`starcraft_protoss`, `redalert2_soviets`, `tiberiansun_gdi`, `warcraft2_orcs`):

```
DRY RUN: 0 values would change (0 inherited stats skipped).
```

`apply_balance` writes **LEDGER → yaml**, and the ledger is a faithful EXTRACT of yaml, so
there is nothing in it to apply. `--confirm` today is a **no-op on every faction**, and it has
been described as "the pending final step, blocked on E1/E4" across several handoffs. That
description was wrong in a way no audit could catch, because the tool exits 0 either way.

**The missing step is UPSTREAM of the apply.** The pipeline is
`extract_stats` → **DECIDE TARGETS** → ledger → `apply_balance --confirm`, and the middle box
has never been filled in for the roster. Filling it means:

1. Choose the scope (one class, or one faction) — the ledger is per-faction, the anchors per class.
2. Generate targets: `fit_class.py` (class-formula price vs actual cost) and/or
   `propose_class_rebalance.py`, or `build_workbook.py` → edit the unlocked cells →
   `import_workbook.py`.
3. ⛔ **Get the maintainer's sign-off, which W11 already owes:** *which class has costs they
   consider CORRECT.* Every price is relative to that anchor, so nothing downstream can be
   right until it exists — this is the true head of the queue, not the apply.
4. THEN `apply_balance --faction X --confirm`, re-extract, audits, boot gate, commit yaml +
   ledger together.

⚠ Because the twin is now known to impose a **DPS floor** (E4), step 2 must respect it: 52
weapons cannot be priced below 25% of current output by lowering flat `Damage`, so a target
under `dps_floor` needs the TWIN shrunk instead. `required_damage()` returns `None` there
rather than a plausible wrong number.

**Two rules were CORRECTED by running this** (both now in DESIGN.md):
- **§12.0b Heroic/Airborne divide by the profile's PEAK, not by 100.** The two stopped being
  the same thing when normalisation moved to the median. Dividing by 100 with a parent at 137
  AMPLIFIES: `Bullet_Light` gave `Plate 137 · Scout 106 · Heroic 145` — heroes softer than
  either half, the exact inversion §12.0b exists to prevent. **36 of 60** derived cells.
- **§12.0 rule 1 said "peak is 100"** and the tooling had already moved to the median. Doc
  fixed to match the artifact.

**THE VERSUS WINDOW (maintainer, 2026-08-15) — adopted, DESIGN.md §12.0 rule 4.**
*"the maximum versus value is 200 and the minimum versus value is 10 so the normalized
spread is 100-5 which is 20x"* — yes, and the ratio is unchanged by it: the old peak-100
law's most extreme spread was 100-against-5, also **20:1**. The window fixes the SCALE that
the move to median normalisation had left open-ended (the ceiling was a loose guard at 300).

Implemented as `NORMALISE_CEILING = 200` + `ABSOLUTE_FLOOR = 10`, with `enforce_distinct` /
`distinct_ints` gaining a BOTTOM-UP repair pass — the descent that separates ties could push
the tail through the floor (`MissileAA_Heavy` had shipped a derived `Heroic` on 9).

| after the window | |
|---|---|
| cells outside `[10, 200]` | **0** (was 18 over 200, 1 under 10) |
| widest span | **11.7x** (`MissileAA_Medium`) |
| median span | **4.8x** |
| lethality change vs the pre-window commit | 0.96x mean (0.84–1.04) |

**THE TARGET BAND `2x · 4x · 8x` (maintainer, 2026-08-15) — maximum legal spread != target.**
*"if you do something automatically it should stay in the reference field's interval … only if
something is specifically designed otherwise should it be allowed."* The window says what MAY
ship; this says what ships by DEFAULT.

⚠ **Measured on INDIVIDUAL warheads, not aggregated families — the distinction is the whole
point.** My first answer quoted 1.3x–7.2x, which is the per-family AGGREGATE and an artifact:
averaging across mods that disagree about a family's direction CANCELS the disagreement.
Re-measured over **2402 individual reference warheads** with a real damage profile:

| | measured | adopted |
|---|--:|--:|
| flattest (p25) | 1.9x | **2x** |
| centre (median) | 4.0x | **4x** |
| sharpest (p75) | 7.5x | **8x** |
| p90 | 15x | — |
| **20:1 (the window)** | **field p94** | legal max |

The field's own distribution, snapped to a DOUBLING ladder. It continues 2 · 4 · 8 · 16 and
the legal maximum sits just past 16 — the window is *one doubling beyond the sharpest default*.
That the 20:1 window independently lands at the field's 94th percentile is a good sign: it is
the extreme that genuinely exists and is genuinely rare.

**Mechanism (`aggregate_archetype.py`):** `fit_ratio` is a **no-op inside the band** — most
families ship the measured shape verbatim. Outside it, the correction is a POWER LAW about the
profile's geometric mean (`v' = G * (v/G) ** alpha`), not an affine rescale onto a floor:
scale-free, order-preserving, and it holds the geometric mean — the right centre for a set of
MULTIPLIERS. An affine squeeze onto a floor drags the mean down and would silently make every
stretched family cheaper through K. `fit_window` then slides it into `[10, 200]`
MULTIPLICATIVELY, so the ratio just set is not quietly changed.

**This ANSWERS the level-vs-family floor question by dissolving it.** The floor is no longer a
dial at all: spread comes from the corpus and level comes from the window, so `LEVEL_FLOOR`
only survives for the families Cameo INVENTED. Deliberate departures live in
`SPECIALIST_RATIOS`, **empty by design** — candidate #1 is `CannonAP`, the clean example of why
the table must exist: DESIGN §12.0 names it the 20:1 archetype while the corpus measures it at
**1.8x–2.6x**, because the source engines write AP as ~100 against everything armoured and
averaging leaves it flat. The field cannot supply a distinction it never drew.

**Result: 37 of 37 measured-family templates inside 2x–8x** (median 3.0x, range 2.0–6.4x), 0
cells outside `[10, 200]`. The band is waived for the DERIVED armors only (they are products,
the sources contain no derived armor, and clamping would break §12.0b).

**Two bugs this flushed out**, both silent fall-throughs to the even ramp:
- `^Warhead_Cryo_*` / `^Warhead_Inferno_*` looked their profile up under their OWN name. They
  are now BLEND_FAMILIES (Cryo = Laser×Prism, Inferno = Flame×Prism) with their own averaged
  Versus and their own PHYSICS_RANK/COMPOSITION values, so the `profile_family=parent` fix was
  replaced by promoting them to proper blends.
- `^Warhead_Tesla_Super` had no measured tier (the export only walked Light/Medium/Heavy) and
  kept the even ramp at 1.8x while every other Tesla level was rebuilt. The export now walks
  the levels the GENERATOR emits; `Tesla/Super` measures n=29 / 7 mods.

**Two things deliberately NOT done here:**
- **`Airborne` is computed but NOT emitted.** Its column would make 17 armors share the
  %-twin's 16-wide window, where "no two identical" can only ever be the even ramp. Opening
  that window is **W18**, and W18 must land as ONE change (denominator + x5 values) or every
  %-twin deals a fifth or five times. `Airborne` ships with W18. ⚠ Also: `Jumpjet` is already
  a **TerrainType** (`mods/cameo/bits/d2k/arrakis.yaml`) — a reason to keep `Airborne`.
- **`--spread-flat-blocks` left OFF.** 24 of 30 family-levels have a macro block the corpus
  left flatter than 20 points (worst: `CannonAP` vehicles spanning 7–8 across five rungs).
  Widening them is DESIGN, not measurement, and it can push a block past its macro neighbour
  and break the ordering law — so it stays a per-family maintainer call.

**STEP 4b — SHIPPED. The invented families are designed, and the even ramp is GONE.**

Seven sloped ladders had no cross-mod equivalent: `Flak`, `Chemical`, `Melee`, `Arrow`,
`Demolition`, `Concussion`, `Railgun`. (`Magic` = PCT mode, `Sonic` = FLAT mode and `Nuclear`
= `HAND_TUNED` are designed by other means and stay deliberate 1.0x/1.8x exceptions.)

| piece | where |
|---|---|
| designer + reasoning | `tools/balance/design_invented_profiles.py` |
| design sheet | `docs/design/INVENTED_WARHEAD_FAMILIES.md` |
| data | `docs/design/invented_family_profiles.json` (**separate from `docs/reference/`** so measured and designed provenance can never be confused; measured WINS if the corpus ever covers a family) |

**Invented is not arbitrary — only two numbers per family are a choice, and both are
constrained.** SHARPNESS sits in the measured `2x/4x/8x` band, placed so the seven have their
OWN median on the field's centre (4x) and none exceeds what the MEASURED families reached
(6.2x) — the families we invented cannot be quietly sharper than the ones we measured. CLIFF
POSITION is **derived, not picked**: `rungs / 16`, the share of the order the weapon genuinely
threatens (a fist works on unarmoured infantry = 2 rungs). Only `width` — how BINARY the weapon
is — is left as feel. ORDER is `build_order()` as always.

**The measurement that justifies the whole item.** Step regularity across 1350 reference
profiles with 6+ armors, as the CV of consecutive gaps (`0.00` = a perfectly even ramp):

| p10 | p25 | median | p75 | p90 | CV < 0.30 | CV > 1.00 |
|--:|--:|--:|--:|--:|--:|--:|
| 0.78 | 0.97 | **1.25** | 1.58 | 2.06 | **0%** | 73% |

**Not one profile in 1350 is even-stepped.** The ramp these families shipped scored 0.00 — the
single shape no mod produces at any tier. Now: **median CV 0.99, and 0 templates left on a ramp.**

**Result across ALL 88 templates: 0 cells outside `[10, 200]`, 80 of 81 band-governed templates
inside 2x–8x** (median 3.2x, range 2.0–6.2x).

**Three bugs this pass flushed out:**
- ⚠ **The design ratio and the SHIPPED ratio are different quantities.** `enforce_distinct` has
  to MANUFACTURE separation wherever a tail is packed, and a sharp early cliff packs it hard:
  at a nominal 6.0x, ten of `Melee`'s sixteen values sat within 2 points of the bottom, so the
  gap-2 rule pushed the floor from 40 to 21 and shipped **9.4x** — outside the band, from a
  design that claimed to be inside it. The nominal is now SOLVED by bisection against what
  survives the no-ties rule, and the JSON records `sharpness_intended` AND `sharpness_shipped`.
- ⚠ **`Shield` breached the window.** Its rule puts it one floor ABOVE the profile's best
  target, and the best target may already be at the ceiling — 28 cells over 200. Fixed by
  scaling the whole row set down together; clamping `Shield` alone would tie it with the top
  armor, and a shield no softer than the toughest thing the weapon can hit is not a shield.
- An earlier draft placed cliffs by eye and produced an arrow dealing **190 against Plate** —
  95% of its peak against the armour it is least able to defeat.

**BLENDS ARE REPAIRED (maintainer, 2026-08-15: re-sharpen to 2.0x, "without clamping of
course").** A blend is the per-armor AVERAGE of its parents, and averaging did two things that
had to be undone. `finish_blend()` now does both:

1. **It computed the derived armors instead of DERIVING them.** §12.0b says
   `Heroic = Plate x Scout / peak` **of the profile it belongs to**, and the average of the
   parents' Heroic is not the product of the blend's own Plate and Scout
   (`avg(ab/p) != avg(a)avg(b)/avg(p)`). **5 of 21 blend levels were off**, `CannonFire_Light`
   by 12 points. Exactly the `/100`-divisor failure again: **a derived value must be derived
   LAST, from the finished profile.** All 22 now match the rule to within rounding.
2. **It flattened** — the same cancellation that makes a per-family aggregate mush.
   `MissileChem_Heavy` fell to 1.8x. Re-sharpened with the same POWER LAW the reference side
   uses (`v' = G * (v/G) ** alpha` about the geometric mean), **never by clamping**: clamping
   moves two cells and deforms the shape, the power law moves every cell proportionally and
   preserves both the ordering and the geometric centre. It now ships at exactly **2.0x**.

**Result: 0 templates outside 2x–8x, 0 cells outside `[10, 200]`, across all 88.**

⚠ **CORRECTION — my "Chemical reads backwards" note was WRONG, and the docs already said so.**
`Chemical` is **CORROSION, not gas**: `PHYSICAL_STATE_SYSTEM.md` maps Chemical to the
**Corrosion** meter at +100 ("pure corrosion") and W9 states "**corrosion eats vehicles**"
(poison is the separate infantry clone); `SPREAD_FALLOFF_PLAN.md` describes Chemical as a green
blast and explicitly **"NOT the gas cloud"**. So `dir="heavy"` — best against armoured infantry
and heavy vehicles — is correct and deliberate: acid eats armour. The anti-infantry gas is a
DIFFERENT family, `Toxic`.

✅ **TOXIC IS BUILT (maintainer order 2026-08-15: "build the toxic weapon now to the new
system and use all the gas clouds we have as reference").**

A THIRD provenance, alongside measured-from-corpus and designed: **measured from Cameo's own
content.** The mod already ships **28 gas/toxin weapons** with explicit `Versus` (the GLA toxin
line, the anthrax clouds and their Blue/Purple/Large tiers, Yuri's chaos gas, RA2's cloud pair,
the Forgotten's smoke). Normalising each to its own peak and taking the per-armor median is the
same method the reference corpus uses, applied to our own library — so `Toxic` is MEASURED,
just not from someone else's mod. Labelled `measured:cameo_gas_clouds`, never `designed`.

What the 28 say: `INF > BLD > VEH > AIR`, anti-LIGHT, spread **2.75x** — already inside the
2x-8x band with no correction, which quietly validates both the band and the library.

- **New `Trace` tier, WC 0.5** (`WEAPON_TYPE_SYSTEM.md`'s spec for Toxic: a lingering field a
  delivery weapon leaves behind, not an armament). ⚠ **It MUST stay LAST in `LEVELS`** —
  `li = list(LEVELS).index(level)` indexes the `spreads`/`falloffs` TUPLES positionally, so
  inserting a level anywhere else silently shifts every other family's spread by one slot.
  `at()` now tolerates a short tuple instead of raising `IndexError`.
- Levels `Trace / Light / Medium` deliberately **share one shape**. Unlike the corpus families
  these are not different PLATFORMS, they are the same gas at different intensities, so the
  magnitude differs (spread 700/900/1100, WC 0.5/0.75/1.0) and the armour shape should not.
- `InvalidTargets: wall, Mine, ToxinImmune` carries the "no-op vs robotic" half of the spec.
  That is a TARGETING rule — W13 rule 8 forbids expressing immunity as a zero multiplier.

**The legacy retirement, done at the TEMPLATE level** (one edit fixing all inheritors):
`^ToxicWeapon` was a textbook pre-split weapon — main + separate `*FriendlyFire` twin +
`HealthPercentageDamage` %-twin, all on the same 17-to-1 ladder (the %-twin SHAPE, on a main
warhead), `Falloff: 111, 33, 11, 3` that never reaches 0, and a building sub-ladder inverted
(`Wood 12 > Concrete 11 > Steel 10`). It is now a thin child of `^Warhead_Toxic_Light` keeping
only its own delivery. 10 warhead keys renamed, **5 retired FF twins deleted**, 4 inline
`Versus` ladders dropped (Versus lives only in templates).

⚠ **The new profile is 6.26x stronger on average than the legacy ladder**, so a naive repoint
would have made every gas cloud six times as lethal. `Damage` is rescaled to preserve DPS:
**1111 -> 177**, and the Blue/Purple upgrade tiers to **197 / 213** so their 1.00 / 1.11 / 1.20
ladder survives. Deliberately NOT snapped to the 100 grid: snapping puts all three on 200 and
collapses three distinct upgrade tiers into one. ⚠ Their bespoke `Versus` ladders (18-to-2,
19-to-3) are gone by law, so the tiers lose roughly 9% and 18% of their old edge — recorded
rather than compensated.

⚠ **A mistake worth keeping:** the first rescale used `text.replace(old, new, 1)`, which hit
the FIRST `Damage: 200` in the file — an unrelated `Warhead@Concrete: DamagesConcrete`. Caught
by reading the diff, reverted, redone scoped to the `^ToxicWeapon` block. This is exactly the
blind-substitution class `LESSONS_LEARNED.md` warns about, and it is invisible to every gate:
it lints, it boots, and it silently nerfs another weapon by 12%.

**AND THE SURVEY THAT FOUND THE REST** (maintainer: *"can you try to find more weapons like
that that were not converted yet?"*) — `tools/audit/audit_unconverted_templates.py`, report at
`docs/audit/latest/unconverted_templates.md`. A template declaring its own `Versus` while
inheriting no `^Warhead_*` parent has not been converted, and is simultaneously a live
violation of "Versus lives ONLY in `^Warhead_*` templates".

**45 unconverted templates, 1124 direct inheritors.** Biggest: `^ShrapnelWeapon` (88) →
Concussion · `^Grenade` (84) → Demolition/Concussion · `^FlakWeapon` (78) → Flak ·
`^MediumChemicalWeapon` (70) · `^MediumMissile` (67) · `^TankDestroyerCannon` (66) → CannonAP ·
`^MediumFlameWeapon` (64) · `^Chaingun` (59) → Bullet. Every target family already EXISTS, so these are retrofits, not
design. `^SniperWeapon` / `^HealingWeapon` / `^RepairWeapon` stay out by design.

---

**ORIGINAL GAP NOTE (now resolved by the above): `Toxic` was never rebuilt.** `^ToxicWeapon` is still a legacy
template with **6 live inheritors** (RA2 Shared, TS Forgotten, the dead central copies) and is
**absent from `gen_weapon_template.WEAPONS`** — so the genuine anti-infantry gas family has no
`^Warhead_Toxic_*`, no ordering law, and whatever inline `Versus` it always had.
`WEAPON_TYPE_SYSTEM.md` specifies it as WC **0.5** sub-light anti-infantry, no-op vs robotic.
Adding it is a new family (a level below Light), so it needs a maintainer ruling on where 0.5
sits in the level ladder.

**VERIFY:** `python tools/reference/extract_versus.py --summary` → 16 sources, 3150 rows;
`python tools/balance/verify_generator_sync.py` → drift = 0;
`python tools/balance/report_versus_change.py <rev>` → the profile diff.

---

### W14 — ✖ DROPPED as specified; folded into W13 rule 8b

**Original claim (mine, wrong):** ground-only weapons are double-charged because the
aircraft armors are averaged into `avg_versus` AND discounted again by `targets_factor`,
so `avg_versus` should be renormalised over reachable armors only.

**Maintainer's objection (2026-08-11, correct):** that is the INTENDED mechanism. Low air
multipliers *should* pull `avg_versus` down and make a ground-only unit cheaper than a
multi-role one. Renormalising would delete the multi-role premium — which is exactly the
thing we want the pricing to express.

**Measured, which settles it:**

| | n | mean K | mean air-Versus | targets_factor |
|---|---|---|---|---|
| AA-capable | 868 | 0.790 | 51.9 | 1.000 |
| ground-only | 1104 | 0.955 | 43.4 | 0.890 |

The Versus route contributes **~1%** (8.5 points of air-Versus at air's 10% engagement
weight); `targets_factor` contributes **-11%**. The overlap is a rounding error, so there
is no double-count worth fixing — and renormalising would have removed the good mechanism
to chase a negligible one.

**The real finding, now W13 rule 8b:** ground-only weapons average **43.4%** against
aircraft, i.e. the ordering law is NOT yet pushing air to the bottom for them. The
maintainer's natural-pricing mechanism cannot bite until W13 sets air values properly per
archetype — last in the order, genuinely low, never zero. Re-check the interaction with
`targets_factor` AFTER that, not before.

(Note also that K is dominated by splash footprint, not Versus: the ground-only
population scores HIGHER K than the AA-capable one because it is full of artillery.)

---

### W15 — `%`-twin fix + `reference_hp` 200 000 ✅ DONE · unblocked W17

Two maintainer rulings, both about how percentage damage is valued.

**1. The `%`-twin cannot survive an off-grid Damage value.**
`formula.distribute_damage` computes it as `per // DAMAGE_STEP` — integer division:

| Damage | twin | effect |
|---|---|---|
| 2000 | 1 | fine |
| 1999 | **0** | the %-warhead silently does NOTHING — hard immunity by rounding |
| 3500 | 1 | same as 2000 — the twin stops tracking damage |

So freeing the grid (W17) before fixing this silently zeroes every percentage warhead
under 2000 damage. Fix the derivation first (float, or a scale that is continuous in
Damage), then remove the grid.

**2. `reference_hp` is a DESIGN constant of 200 000, not a measured median.**
Maintainer 2026-08-11: percentage damage must be priced as if fired at an average
BASELINE actor, and 200 000 HP is the right middle — high-tech tanks, dreadnoughts and
epics all sit well above it, everything else below.

`target_model.reference_hp()` currently MEASURES 74 000 (engagement-weighted median of
the live roster). Overriding it to 200 000 makes every %-twin worth ~2.7x more in K, so
this is a real model change: expect the family table to move and say so in the commit.
Keep the measured value available as a diagnostic — the gap between "what the roster
actually is" (74 000) and "what we price against" (200 000) is itself information.

**DONE WHEN** the twin is continuous in Damage; `reference_hp` is the design constant
with the measured one still reportable; the family-table shift is recorded in §5.

**✅ SUPERSEDED BY THE FOLDED RUNTIME MODEL** — the temporary
`formula.percentage_twin()` solution removed the zero-damage cliff, but still left two
authored warheads that could drift. The completed family path now keeps one
`AreaDamage` warhead and derives its percentage hit through `PercentageScale` plus a
basis-point `PercentageDenominator`. This folded hit scales to zero with flat Damage.
Standalone `AreaDamagePercentage` and `HealthPercentageDamage` warheads remain valid
only for bespoke additive effects and are modeled as an absolute DPS floor.

`target_model.REFERENCE_HP = 200_000` is now a plain constant; the measured figure moved
to `measured_reference_hp()` and is still printed by the family table, the
`target_model` report and the derived ledger (`reference_hp_measured`). A test asserts
the measured value stays BELOW the constant — if the roster ever catches up, the constant
has stopped being the middle it was chosen to be and wants a re-ruling.

**3. ✅ THE BASIS-POINT REGRID (maintainer order 2026-08-11/12).**
*"Flat damage steps of 100 and percentage is always 0.01% for each 100 flat damage since
that seems very easy to remember. Now we can increase all the versus values for the
percentage warhead to 5x … 20 to 100 … steps of 5."*

**The law, in one sentence: 100 flat damage == 0.01% of max health.** So the twin is
literally `Damage / 100` and one step of either grid is one step of the other — it cannot
drift from the weapon it belongs to.

| | before | after |
|---|---|---|
| flat damage grid | 2000 | **100** (20x finer) |
| percentage twin unit | whole percent (1%) | **basis point (0.01%)** |
| base ratio | 1% per 2000 damage | **1% per 10000 damage** (5x weaker) |
| percentage-warhead Versus | 1..17, steps of 1 | **multiples of 5 in [5, 100]** (5x larger) |

The 5x weaker base and the 5x larger Versus **cancel exactly**, so total percentage damage
is unchanged: `16000 damage → 160bp (1.60%) × Versus 85` is the same as
`16000 → 8% × Versus 17`. What is bought is resolution *in both dimensions at once* — the
twin now separates every flat step, and Versus moves in clean 5s away from the cramped
1..17 band where a single integer step was a 100% jump at the bottom.

⚠ **THE TWO HALVES ARE ONE CHANGE.** `DAMAGE_PER_PERCENT` (2000 → 10000) without the
Versus x5 makes every percentage twin deal **a fifth** of its damage; the Versus x5 without
the ratio makes it deal **five times**. Never land one alone — see W18.

- C#: `AreaDamagePercentageWarhead.PercentageDenominator` — a DENOMINATOR, not a
  multiplier (it sits beside `IntegrityScale`/`PhysicalStateScale`, which scale UP;
  the `[Desc]` says so explicitly). `100` = whole percent = the engine convention and
  the **default, so no existing weapon changes behaviour**; `10000` = basis points.
  Validated at load through a new `AreaDamageWarhead.ValidateFields()` hook —
  implementing `IRulesetLoaded<WeaponInfo>` in the subclass instead would REPLACE the
  base's explicit implementation, leaving `effectiveRange` unbuilt and every ring empty.
- Tools: `formula.DAMAGE_STEP = 100`, `DAMAGE_PER_PERCENT = 10000`,
  `BASIS_POINT_DENOMINATOR = 10000`, `PERCENTAGE_VERSUS_STEP = 5`;
  `percentage_twin(per, denominator)` takes the unit from the node, `twin_denominator()`
  reads it from the ledger record, and `extract_stats` records
  `percentage_denominator` **only when the node states it**, so ledgers of weapons still
  on the default diff empty.

⚠ **The unit is threaded, never assumed** — writing whole percent into a basis-point node
(or the reverse) is a silent 100x error in a number nobody re-reads.

**Which 17-step Versus window?** The maintainer picked **20..100**. Recorded, with one
caveat for W13 to settle: 20..100 has a best/worst ratio of **5:1**, where the exact x5
rebase (5..85) keeps today's **17:1**. A 5:1 profile is a GENERALIST — the direction W13
is explicitly moving away from (field median span 87; "each warhead more specialized").
**Recommendation: make the STEP the law (multiples of 5) and the WINDOW a per-family
choice** — 5..85 for the sharp families, 20..100 for the intentional generalists (Magic,
Sonic, Tesla, which the maintainer has already named as such). Both windows are equally
clean to remember; only the sharpness differs.

⚠ **The yaml rollout is NOT in this commit — see W18.** The mechanism is live and inert:
nothing writes `PercentageDenominator: 10000` yet, so every weapon still behaves exactly
as before. **Re-verified 2026-08-16**: `grep -rn PercentageDenominator mods/` is still
empty, so every `_Percentage` twin is on the default whole-percent unit and the ×5 Versus
band has NOT landed. The board row above and this note both used to say `1000` / ×10,
which contradicted the spec in W18 and the C# `[Desc]`; the unit is `10000` (basis points,
0.01% steps) and the Versus factor is ×5.

---

### W16 — Charge-up proportional to real charge share ✅ DONE · supersedes W4's flat rate

W4 applied a flat **0.75x** to every charging actor. Measured, that is too blunt:

| actor | trait | charge | reload | share of cycle |
|---|---|---|---|---|
| Obelisk of Light (TD/TS) | `AttackCharges` | ChargeLevel **50** | — | the heavy case the ruling was written for |
| RA1 Tesla Coil | `AttackTesla` | InitialChargeDelay **25** | 100 | **20%** |
| AsianAlliance railtower | `AttackTesla` | **12** | 120 | **9%** |
| **RA2 Tesla Coil** | `AttackTesla` | **22 (engine default)** | 75 | **23%** |

Maintainer ruling 2026-08-11: *"AttackTesla doesn't have the long charge time of the
Obelisk … it's very fast, so this needs to be taken into account."* ⚠ CORRECTION 2026-08-11: an earlier draft read the RA2 Tesla Coil as having NO charge
delay. Wrong — `InitialChargeDelay` is simply not written on the actor, so it takes the
ENGINE DEFAULT of 22 (`AttackTesla.cs:31`). An absent key means default, never zero.
Re-measured, the RA2 Tesla Coil has the HIGHEST charge share of the Tesla group (23%),
not the lowest. The ruling stands and is now better supported: Tesla charges are real
but SHORT relative to the Obelisk's 50, so they earn a smaller discount, not none.

⭐ **THE ANCHOR IS A LAW, NOT A BUILDING** (maintainer 2026-08-15, "some nice ratio …
might be more consistent"):

> **A unit whose charge is 50% of its reload earns the full 0.75× discount.**
> Reload 100, charge 50. As a share of the whole cycle that is `0.5 / 1.5` = **1/3**.

`formula.CHARGE_ANCHOR_SHARE = 1/3`. The Obelisk sits at 50/(50+96) = 34.2%, just above
the line, so it still anchors at 0.75 and **nothing moved**: measured across the 11
chargers with a real share, spread 0.198 against the old accidental anchor's 0.199.

⚠ **A 25%-of-reload anchor (share 20%) was measured and REJECTED** — it puts **7 of 11**
chargers on the 0.75 floor instead of 5, erasing most of the differentiation this item
exists to create. Clean is good; clean and flat is not.

Optional tidy-up, NOT done (it is a weapon balance number and belongs in the pipeline):
`td_nod_obeliskoflight`'s weapon reload 96 → 100 would make the anchor unit sit exactly
ON the law at 33.3% instead of clamping from just above it.

**Model:** `charge_share = charge / (charge + reload)`, discount scaled so the anchor
share earns the documented 0.75x and a zero-charge actor gets exactly 1.0, clamped to
[0.75, 1.0]. This also RESOLVES the open Tesla question: `AttackTesla` can now join
`CHARGE_UP_TRAITS` safely, because the model gives each actor the discount its real
charge burden earns instead of a binary in/out. Retire `CHARGE_UP_EXCLUDED_TRAITS`.

**VERIFY:** Obelisk == 0.75 (anchor); railtower (9%) closest to 1.0; RA2 Tesla (23%) and
RA1 Tesla (20%) in between. Read charge values from the RESOLVED actor INCLUDING engine
defaults — `InitialChargeDelay` defaults to 22.

**✅ DONE. Measured across all 14 charging actors in the tree:**

| actor | trait | ticks | cycle | share | multiplier |
|---|---|---|---|---|---|
| `td_nod_obeliskoflight` | AttackCharges | 50 | 96 | 34.2% | **0.750** (anchor) |
| `ra2_soviets_teslacoil` | AttackTesla | **20** | 75 | 21.1% | 0.846 |
| `ra1_soviets_teslacoil` | AttackTesla | 25 | **106** | 19.1% | 0.861 |
| `wc2_*_siegeengine` | AttackFrontalCharged | 20 | 100 | 16.7% | 0.878 |
| `asianalliance_railtower` | AttackTesla | 12 | **160** | 7.0% | **0.949** |

`ts_nod_obeliskoflight` (45.5%) clamps to 0.75, proving the clamp.

⭐ **`AttackTesla` OVERRIDES THE WEAPON'S RELOAD** (maintainer 2026-08-15): *"if you have
the AttackTesla trait, ReloadDelay is taken from that instead of from the weapon, and the
reload delay from the weapon counts as the burst delay in the formula."* The coil winds up
once, fires `MaxCharges` zaps, and the WEAPON's reload is the gap between them — the burst
law verbatim, `eff_reload = trait ReloadDelay + weapon reload × (MaxCharges − 1)`:
RA1 = 100 + 3×2 = **106**, railtower = 120 + **10**×4 = **160**, RA2 = **75** (one charge).

⚠ **`ChargeDelay` is NOT the gap.** An earlier draft used it and was right twice by
coincidence — it defaults to 3, and both Tesla Coils happen to carry weapons that also
reload in 3. The AA railtower's weapon reloads in **10**, and only the railtower exposed
the error (132 against the correct 160). Two agreeing data points proved nothing.

⭐⭐ **THE REAL PRIZE: an 11.8× DPS OVERSTATEMENT.** Because a Tesla Coil's weapon reloads
every 3 ticks, `unit_inputs` was pricing the coil as firing 20 times a second when it
fires 3 zaps per 106 ticks. DPS drives the price, so every `AttackTesla` actor was priced
off a number ~12× too large. `formula.charge_attack_cycle` now returns the cycle and
shots-per-cycle for any trait that overrides the weapon, and `fit_class` prices on that.

⭐ **This FLIPS the Tesla ordering, and the flip is the point.** RA1 charges LONGER (25 vs
20) yet ends up with the SMALLER share (19.1% vs 21.1%), because its three zaps stretch
the cycle while the single-charge RA2 coil stays at 75. **Charge share is a ratio, not a
duration** — a fact no flat rate and no charge-time-only reading could ever express.

Charge times are now a DECISION rather than a leftover: RA1 stays 25 and the RA2 coil
writes `InitialChargeDelay: 20` explicitly instead of inheriting the engine's 22. `CHARGE_UP_EXCLUDED_TRAITS` is retired to an empty set and `AttackTesla`
joins `CHARGE_UP_TRAITS`, as the item asked.

⚠ **The cycle for `AttackTesla` is its OWN `ReloadDelay`, never the weapon's.** A Tesla
Coil's armaments reload every 3 ticks (`ChargeDelay`), so using the weapon would read as a
~90% charge share and hand it the full discount for nothing. The `ChargeLevel` family has
no reload of its own and falls back to the LONGEST base-weapon reload — longest, because a
charge gates the heavy shot, and the Terran siege tank's fast 37-tick secondary next to its
sieged 148 would otherwise fake a huge share.

⚠ **An actor whose charge cannot be measured keeps the flat 0.75, not 1.0** (2 of the 14:
`ra1_allies_mobileradarjammer`, `terran_siegetank` — both have only condition-gated weapons,
so there is no base reload to measure against). It charges; we just cannot see by how much,
and pricing it as if it did not charge is the larger error — a price cut is a BUFF in value
terms, so over-paying is not the safe default.

⚠ **SEPARATE DEFECT FOUND AND GUARDED: a `--faction` extract silently staled 30 derived
files.** `extract_stats --faction X` rewrites the GLOBAL `derived/_model.json` (its armor
census and weights are measured across the whole roster) but regenerates only X's sidecar —
so every other faction's `avg_versus`, `k` and `effective_dps` keep being computed against
the old model. Nothing caught it: `audit_balance_drift` compares raw yaml to the RAW ledger
and never looks at derived. Fixed here by a full re-extract (verified idempotent: a second
run changes nothing), and `extract_stats` now prints a loud warning after any filtered run.

---

### W17 — Retire FirepowerMultiplier 🔵 TOOLING DONE (2026-08-15) · content half ⛔ set B

⚠ **Partly superseded by W15's regrid.** The maintainer chose a **grid "for sanity"** (100,
`formula.DAMAGE_STEP`), not free-valued Damage, so "remove the grid" is now "the grid is 100
and the %-twin tracks it exactly". What remains of W17 is the SECOND half: retiring
`FirepowerMultiplier` as a fine-tuning knob, which the finer grid makes possible.

⚠ My earlier objection — "keep FP because one weapon serves many actors" — is **VOID**.
Maintainer 2026-08-11: **no weapon is shared; every vehicle has its own unique weapon
defined.** So FP has no remaining pricing role at all. (This also voids **W13 rule 10**,
written before that ruling.)

**MEASURED before changing anything** (`plan_firepower_retirement.py`, the whole roster):
1322 main warheads across **152 actors** carry an unconditional FP. Folding the multiplier
into `Damage` and snapping back to the grid leaves **1144 exact**, **1214 within 1%**, and
**108 needing a damage decision**. The residual is not the argument for retirement on its
own — the argument is that the 1% band is the step the retired knob itself moved in.

⚠ **The 108 are not trims.** They cluster on actors whose FP is a SCALE, not a fine-tune:
`futuretech_cryocopter` 0.12, `protoss_voidray` 0.09, `ra1_soviets_ak47conscript` 0.14,
`ra2_soviets_conscript` 0.19. A multiplier that far from 1.0 means the actor is firing
another unit's weapon at a fraction of its written damage; the grid cannot express the
result, so those need a real damage decision rather than a fold.

**TOOLING HALF — DONE (set A):**
- [x] `propose_class_rebalance.decompose_dps` solves on `formula.DAMAGE_STEP` and returns a
      multiplier of **1.0**, always. It also stopped using the stale hard-coded 2000 grid.
- [x] The two `over_priced` dead-ends no longer emit `2000, 0.05`. The floor is
      deliberately identical: one step at fp=1 is the same 100 effective damage.
- [x] `unique_dmg_per_shot` nudges **Damage in grid steps** instead of walking FP in 1% steps.
- [x] `apply_balance` cannot WRITE the knob: `firepower_multiplier` moved from
      `UNIT_FIELDS` to `RETIRED_UNIT_FIELDS`, a ledger/yaml disagreement is REPORTED, and
      the `set_field` branch that could MINT a missing `FirepowerMultiplier:` block is gone.
- [x] The report flags `fp-debt` and orders **"DELETE the unconditional
      FirepowerMultiplier"** — prescribed Damage is solved at fp=1, so a surviving trait
      would scale it a second time. (The old code overwrote the trait, so this instruction
      is new and load-bearing.)
- [x] `tools/tests/test_firepower_retired.py` — 12 tests pinning both halves.
- [x] `extract_stats` still READS FP and `fit_class` still prices with it. It must: 152
      actors still carry one, and un-pricing them would misprice the roster.

**CONTENT HALF — set B is free, but ⛔ the fold AS SPECIFIED IS UNSAFE. Two blockers found
2026-08-15 by checking the spec against the engine and the ledger before executing it.**

**BLOCKER 1 — the fold is incomplete. `FirepowerMultiplier` scales EVERY warhead, not just
mains.** `Armament` builds `DamageModifiers` ONCE and passes it to every warhead:
`DamageWarhead.cs:93`, `AreaDamagePercentageWarhead.cs:53` and
`HealthPercentageDamageWarhead.cs:24` all apply it, and `ApplyPhysicalStateWarhead.cs:49`
applies it to the METER amount as well. The worklist's `is_main()` excludes
`percentage` / `extradamage` / `friendlyfire`, so folding only mains leaves **1610 twin and
chip warheads across 375 weapons** silently scaled by `1/FP` — an actor at FP 0.5 would have
its %-twin and chip DOUBLE. The fold must cover every damaging warhead on the weapon plus any
`ApplyPhysicalState` amount.

**BLOCKER 2 — "no weapon is shared" is FALSE.** The ruling that voided the original objection
is the premise the fold rests on, and the ledger disagrees: **109 weapons are fired by actors
carrying DIFFERENT FirepowerMultipliers.** `BigFlamer` is fired by `futuretech_salamanderifv`
(1.5), `ra1_soviets_gorynychtank` (1) and five `ra2_allies_ifv` variants (1); `ChainGun` by
`ra1_soviets_hindattackhelicopter` (0.5) and `ra1_soviets_kamovattackhelicopter` (0.25).
Folding an FP into such a weapon's `Damage` is correct for ONE user and wrong for every other.
Most are the deliberate IFV/carrier weapon-BORROWING pattern that `audit_weapon_uniqueness`
class W3 says must never be split.

**So W17's content half needs a decision before any yaml moves:** for a borrowed weapon, either
the borrowing actor gets its own copy of the weapon (the uniqueness rule's normal answer, but
it multiplies the IFV's weapon list), or those 109 keep their multiplier as a documented
exception. Folding them mechanically would corrupt every other user of the weapon.

Once decided: write `Damage x FP` on **every damaging warhead** (not just mains), then DELETE
the trait; boot-gate per batch. Conditional (upgrade) FP traits are design and are NOT touched.

Versus values keep integer steps of 1 and the ordering law, but the floor may sit
anywhere without tier restriction (W13 rule 5).

**VERIFY:** `python tools/balance/plan_firepower_retirement.py` → 0 actors, once done.

---

### W18 — Roll the basis-point unit out into yaml ⬜ READY (unblocked)

W15 shipped the MECHANISM; this ships the CONTENT. It *was* blocked purely by file
ownership — every file involved is set B (`mods/cameo/weapons/**`,
`ContentPacks/**/weapons.yaml`), which Devin held while W2 ran. **Devin's set-B lock has
since been released**, so the ownership block is gone; the header said BLOCKED long after
that stopped being true.

Maintainer asked 2026-08-16 whether the ×5 had already landed. **It has not** — verified,
not assumed: `grep -rn PercentageDenominator mods/` returns nothing, so every `_Percentage`
twin still reads `Damage` as whole percent. The C# knob is live and inert, exactly as W15
left it.

Measured scope (2026-08-11, `Warhead@*Percentage` nodes carrying an explicit `Damage`):

| warhead type | explicit Damage | inherits Damage | can go per-mille? |
|---|---|---|---|
| `HealthPercentageDamage` (stock) | **2611** | 135 | ✗ — no such field; must migrate type first |
| `AreaDamagePercentage` (Cameo) | **182** | 1 | ✓ |

**Order of operations** (each step boot-gated; the whole thing is behaviour-preserving):
1. `gen_weapon_template.py` emits `PercentageDenominator: 10000` on every `_Percentage`
   twin, `pct_damage = damage // 100` (2000 damage = `20` = 0.20%), **and the x5 Versus
   band in multiples of 5** — all three together, never separately.
2. Regenerate the shared templates; `verify_generator_sync.py` drift back to its
   expected value. ⚠ This rewrites `mods/cameo/weapons/weapons.yaml` — **set B**.
3. Restate every explicit twin `Damage` on a node that just gained the finer unit
   (old whole-percent `N` → `N × 20` basis points, since the base ratio also fell 5x).
   A unit change, NOT a balance change: assert the resolved percentage damage is
   identical before/after with `tools/audit/review_resolve_diff.py`.
4. Migrate the 2611 stock `HealthPercentageDamage` nodes to `AreaDamagePercentage`
   (already documented as a behaviour-preserving drop-in) and restate them too.

⚠ **A node on the stock warhead CANNOT hold the new ratio** — whole percent rounds 1.60%
to 2%, a 25% error. Until step 4 lands, those 2611 nodes keep the old ratio and the old
Versus; the two systems must not be mixed inside one template.

⚠ **Deleting or retyping a `Warhead@` on a template orphans child BARE overrides → an
abstract warhead → NRE at `CreateBasic` with no weapon name in the stack.** Run
`python tools/audit/find_empty_warhead.py` (expect 0) after EVERY batch, not at the end.

**VERIFY:** `grep -rc "PercentageDenominator" mods/cameo` > 0 and
`python tools/balance/extract_stats.py --check` = 0 drifted.

---

### W19 — Collapse the `ExtraDamage` chips into the main warhead ⬜ READY (design), ⛔ content BLOCKED on set B

Maintainer 2026-08-11: *"extra damage warheads are no longer needed — after our new
balance formula that can take into account everything from the projectile like spread and
speed, we can collapse it into the main damage warhead (and later change it based on the
data-mining synthesis)."*

The reasoning holds and is reinforced by the corpus: the chip is a SECOND warhead, and
2+ warhead weapons measure a median span of 58 against 75 for single-warhead ones — chips
flatten exactly the rock-paper-scissors W13 is being built to sharpen. K now measures
footprint, reliability and profile directly, so the chip no longer pays for anything the
model cannot see.

Measured scope (229 nodes, 33 files) — and it does **not** collapse uniformly:

| chip type | nodes | families | verdict |
|---|---|---|---|
| `SpreadDamage` | **195** | Tesla 184 · Laser 5 · Railgun 1 · Magic 1 | ✓ COLLAPSE — a damage bonus with a bespoke Versus |
| `OpenToppedDamage` | **34** | Sniper only (`Sniper_Light_ExtraDamage` 26, `SniperWeaponExtraDamage` 8) | ✗ **KEEP** |

⚠ **The 34 sniper chips are not damage chips at all.** `OpenToppedDamage` is the MECHANIC
by which a sniper hits passengers inside an open-topped transport. Folding it into the main
warhead does not "merge damage", it deletes the ability — the sniper stops being able to
shoot a garrison. Collapse the 195 `SpreadDamage` chips; leave the sniper's alone.

The 195 carry bespoke per-family Versus (`CHIPS` / `CHIP_FLOOR` in
`gen_weapon_template.py`: Tesla = anti-armored-infantry + anti-shield, floors Laser 9 /
Railgun 10 / Tesla 10). Collapsing therefore means the MAIN warhead's profile must absorb
that role — which is W13's job, not a mechanical merge. **Sequence W19 after W13** so the
chip's identity is folded into a profile that was designed with it in mind, rather than
dropped and re-invented.

Damage bookkeeping: the chip is 50% of main and EXCLUDED from the damage total
(`spread_damage_sum`), so a naive delete is a real nerf and a naive merge (`main += chip`)
is a real buff. The collapse is behaviour-preserving only against the RESOLVED effective
damage — verify with `tools/audit/review_resolve_diff.py`, as in the 3-way split.

**DONE WHEN** the 195 `SpreadDamage` chips are gone, the sniper's 34 `OpenToppedDamage`
warheads remain, `find_empty_warhead.py` = 0, and the generator no longer emits `CHIPS`.

---

### W20 — Multi-armor combination rule ✅ DONE (`Average` is live)

Maintainer 2026-08-12: dual-armor units (FutureTech droids, Schwarzer Mond noids, CABAL
cyborgs) *"can feel unfair — certain weapons seem to do nothing against it while other
weapons seem too powerful."*

**The cause is multiplication, and it is ENGINE behaviour, not a Cameo choice.**
`DamageWarhead.DamageVersus` (engine `DamageWarhead.cs:88`) ends in
`Util.ApplyPercentageModifiers(100, armor)` over EVERY enabled `Armor` trait — a product.
So a second armor does not average the weapon's profile, it **squares** it: a weapon with a
17:1 spread becomes ~289:1 against a dual-armor unit. 40% × 30% = 12%, while 90% × 80% =
72% — a 6:1 gap between "bad" and "good" weapons where a single-armor unit shows ~2-3:1.
A flat 200% multiplier cannot fix this: it shifts the whole curve, and the problem is the
curve's SHAPE.

**Measured (2026-08-12): 36 actors declare more than one `Armor`, and they are three
different things wearing one mechanic —**

| group | actors | pattern | compensation |
|---|---|---|---|
| FutureTech droids | 4 | `Plate+Heavy`, `Plate+Medium`, `Flak+Light`, `None+Scout` | **`Modifier: 200`** |
| **CABAL cyborgs** | **12** | `Plate+Medium`, `Flak+Light`, `Heroic+Superheavy`, … | **NONE** |
| shields / stealth suits / upgrades | ~20 | a CONDITIONAL `Armor@Shield` layered on the body | various (50–150) |

⚠ **The compensation is applied inconsistently.** The FutureTech droids carry the 200%;
the CABAL cyborgs — the same design, named in the same breath by the maintainer — carry
**nothing**, so they are silently far tougher than their FutureTech counterparts. That
inconsistency is a likely part of what "feels unfair", independent of the combination rule.

⚠ **The ~20 shield/upgrade actors are NOT the same problem.** A conditional `Armor@Shield`
layered over the body is the layered system (W21) done crudely, and any global change to
the combination rule hits Protoss plasma shields, D2K/Ixian personal shields, Yuri stealth
suits and Steel Consortium at the same time. **Do not treat "36 dual-armor actors" as one
population.**

**Mechanism:** `AreaDamageWarhead.MultiArmorCombination` — `Average` (**the default since
2026-08-15**) · `Multiply` (the engine's rule) · `Lowest` · `Highest`. Single-armor actors
are unaffected by construction: any rule over one value returns that value, which is also
why a SHIELDED unit is untouched — its body armor is gated off while the shield holds.

**Maintainer order 2026-08-15, closing R5:** *"armored means armor plating + health armor
types are averaged"* — so `Average` is now the DEFAULT rather than an opt-in field, and no
weapon yaml has to declare it. `Average` keeps the weapon's designed profile intact (35%
rather than 12% for a 40/30 weapon), so no weapon is ever useless or oppressive.

**Landed together with the flip** (they are one change and cannot be split):
- the 7 `DamageMultiplier … Modifier: 200` squaring compensations are DELETED — 4 FutureTech
  droids, 2 Yuri slave miners, `^FlyingInfantryTemplate`. Averaged armor plus a 2x damage
  multiplier would have made those units paper.
- the 12 CABAL cyborgs needed no edit: they never had the compensation, so averaging simply
  removes the over-toughness they had been carrying silently.

⚠ **Only warheads routing through `AreaDamage` obey this.** 878 legacy warhead nodes still
declare inline `Versus` on `SpreadDamage` and keep MULTIPLYING until they are retired onto
`^Warhead_*` templates (item A5). Until then a dual-armor unit is tougher against legacy
weapons than against templated ones — a bounded inconsistency that A5 closes, and the
reason the universal alternative (moving the combination into the engine's `DamageWarhead`
base, submodule + mirror workflow) stays on the table.

**VERIFY:** `grep -n "MultiArmorCombination" OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs`
shows `= ArmorCombination.Average`, and
`grep -rn "DamageMultiplier@\(Concrete\|Scout\|Heavy\|Medium\|Light\|FlyingInfantry\):" mods/cameo`
is empty.

---

### W21 — Layered health: Shield → Integrity → Armor → Health ✅ BUILT + LIVE (2026-08-15)

⚠ **The "needs C#" status below is STALE — the C# exists and is in the game.**
`OpenRA.Mods.Cameo/Traits/` holds `Integrity.cs`, `ArmorPlating.cs` and `GrantsShield.cs`;
the stack is wired in yaml (`Shielded` 22 files, `Integrity` 6, `ChangesShield` 6,
`ArmorPlating` 2) and boot-gated across `0556f8fc9` → `4cdf8b2a8` → `ab467fe52`. The
rulings (R1–R14), the ONE-POOL/ONE-BAR law and the two-intercepting-layers hazard live in
`docs/design/ARMOR_LAYERS.md`.

⚠ **The bug class this shipped with, because boot gates cannot catch it:** two layers that
both intercept a hit each return damage modifier 1 and then each charge their own pool, so
the modifiers MULTIPLY — 1% x 1% made a shielded+plated unit effectively immortal in play,
with a clean boot. Guard: only the TOP surviving layer may absorb (`ShieldHolds`).

The original design notes follow.

**Design reference (as written 2026-08-12, before the build):**

Maintainer 2026-08-12: three bars, *"only the highest layer active determines the armor"* —
shield weak to Tesla/Storm/EMP/Quantum/Laser, armor weak to AP (CannonAP/MissileAP/Railgun),
health weak to flame/explosive. Reference: **Crystallized Nexus**
(`~/Downloads/crystallized-nexus-main`, GPLv3 — same licence as Cameo, so a port is fine
**with attribution**).

**What CN actually has** (`.modsdk/OpenRA.Mods.CN/Traits/Player/SecondaryHealth.cs`, 232
lines; `CNHealth.cs`, 293 lines):

- ✅ **Already N-layer, not 2** — `CNHealth` collects `TraitsImplementing<SecondaryHealth>()`
  into an array and walks it, so Shield → Armor → Health works structurally today.
- ✅ Per layer: `MaxHP`/`InitialHP`, `RegenerateRate` (**0 = ablative armor, >0 =
  regenerating shield** — exactly the Armor/Shield distinction), `RegenerateDelay`/
  `Interval`, `BypassDamageTypes`, `PierceDamageTypes` + `PiercePercentage`,
  `RepairDamageTypes`, `FullCondition`/`EmptyCondition`, depleted/recharged sounds,
  `BarColor`, and its own `ISelectionBarAboveHealth`.
- ❌ **`SecondaryHealth.ArmorType` is a DEAD FIELD.** Nothing outside `SecondaryHealth.cs`
  reads it (verified by grep across the whole CN assembly). CN gives layered HP POOLS, but
  Versus is still resolved against the actor's single `Armor` trait before the layer ever
  sees the damage. **The one feature we want is the one CN does not implement.**

**…and we do not need their C# for it.** `Armor` is a `ConditionalTrait` and `DamageVersus`
filters on `!a.IsTraitDisabled`. So **three `Armor` traits gated on the layers'
`FullCondition`/`EmptyCondition` give layer-aware armor with ZERO new C#** — and because
exactly one is enabled at a time, **W20's multiplication problem disappears structurally**.
That is the whole design, and the maintainer's instinct that the layers solve the dual-armor
problem is correct.

**The real cost** is the damage routing: intercepting damage before `Health` requires
replacing or subclassing the stock `Health` trait — CN wrote a 293-line `CNHealth` for
exactly this, and that is the invasive part, not the layers.

**Also worth lifting from CN** (relevant to the physical-state program's art phase):
`DamageSmoke`, `CharredPalette`, `BloomGlowEffect`, `VoxelDynamics` (spring-based impact
tilt, firing recoil, roll on turns), `PeriodicSpriteEffect`.

**DONE WHEN** a unit can carry Shield/Armor/Health with per-layer bars, the active layer
alone decides the Versus lookup, and a dual-armor cyborg needs no `DamageMultiplier` crutch.

#### W21 — verified ground truth (2026-08-12), correcting three assumptions

⚠ **`Integrity` is NOT the shield.** It is Cameo's own **electronics** pool
(`AffectedByDamageTypes: Tesla`, `ActiveCondition: electronics`, sits beside the EMP bar,
drained by a warhead's `IntegrityScale`). The shield is **`Shielded`**, from
`engine/OpenRA.Mods.AS/Traits/Shielded.cs` — 23 files use it vs 9 for Integrity. Every
`[Desc]` in `Integrity.cs` had been copied verbatim from `Shielded.cs` and called it a
shield; corrected 2026-08-12. ⚠ `Shielded` lives in the **engine submodule**, so extending
it needs the mirror workflow — prefer a Cameo-side layer trait.

**The stack forks below the shield** (maintainer 2026-08-12): *"Integrity should only be
protected by shields but not by armor, so once there are no shields left the unit starts
taking integrity damage."*

```
        Shield  (Shielded — absorbs EVERYTHING, incl. electrical)
           |
    +------+------+
    |             |
  Armor        Integrity        (parallel, selected by damage type:
 (physical)   (electrical)       armor never protects electronics)
    |             |
    +------+------+
           |
        Health
```

**Measured, and each contradicts a stated assumption:**

1. **The regen rule is real but has DRIFTED.** `defaults.yaml` carries only a flat
   `Step: 10` fallback; the real rule is hand-set per actor. Of 846 actors with a Step:
   **508 = HP/2500, 232 = HP/1000, 106 (12.5%) OFF-RULE** — including an undocumented
   third divisor `HP/1250` (chronotank, japan_chihaheavytank, apparition.ixian) and
   `HP/10000` on the carryalls. This is the case for moving regen INTO the trait.
   Note the defaults already slow infantry down via `Delay: 2` / `DamageCooldown: 20`
   against vehicles' `1` / `10`.
2. **"Versus vs shields is always >100%" is true for mains, false for twins.**
   Main warheads: n=185, median 110, **129 (70%) above 100**, range 9–400.
   `%`-twins: n=89, median **25**, only **4 (4%)** above 100.
   ⚠ The W15 Versus x5 rebase silently FLIPS this — a twin at 25 becomes 125, turning
   every percentage warhead from shield-resistant to shield-punishing. Decide it
   deliberately.
3. **The 150% multiplier is the REVERSE of what was remembered.**
   `DamageMultiplier@shieldpermanent: Modifier: 150` is gated on `shieldpermanent`,
   granted by `ixian_upgrade_personalshield` / `japan_upgrade_stealthsuitintegration` /
   `ordos_upgrade_shields` — the unit's OWN permanent shield. So **permanently**-shielded
   units take 150% damage and externally-shielded ones take normal, not the other way
   round. The plan (drop the multiplier, halve externally-granted capacity so 1 shield HP
   always means one thing) still stands — it just corrects the opposite asymmetry.

**⚠ The 50% armor cap does NOT contain the problem it was chosen for.** Effective HP from a
layer is `pool × (1 / versus)`. Armor at 50% of HP using a VEHICLE armor type, hit by an
anti-infantry weapon at 20% vs Medium, absorbs `50k / 0.20 = 250k` — **2.5x the unit's
whole health bar, from a "50%" layer** — and ~8x at a 17:1 profile. Pool size is additive,
the armor multiplier is multiplicative, so no flat percentage can cap it. **The cap must
scale with the spread** (e.g. `pool = HP × k / spread`), or the armor layer's Versus band
must be narrowed (e.g. 60–140) while body armor keeps the full 20–100.

**A property worth keeping deliberately:** shield 200% pool at 2x rate and armor 50% pool
at 0.5x rate both refill in EXACTLY the same time as health (2500 ticks in the worked
example) — pool and rate cancel. So "shields regenerate twice as fast" changes nothing in
relative terms; only the ramp-up delays (25 / 125 / 250) differentiate the layers. In
sustained fire the ABSOLUTE rate is what matters, and the shield soaks 4x the armor's
per-tick — likely more attrition dominance than intended.

**Suggested single ramp formula** for all three layers (one implementation, no per-unit
tuning): `rate = base × min(1, ticks_since_damage / ramp)`, ramp = 25 / 125 / 250.

#### W21 — MAINTAINER RULINGS 2026-08-12 (the full decision set)

⚠ **Layer order CORRECTED.** An earlier note in this file drew Integrity as a parallel
branch. The ruling is **sequential**:

```
Shield  →  Integrity  →  Armor  →  Health
```
- **Shield** absorbs EVERYTHING — physical damage, physical-state meters, DoT, and
  electrical. Nothing gets past an intact shield.
- **Integrity** (electronics) sits BETWEEN shield and armor: once the shield is gone,
  electrical damage starts eating it. Type-filtered, so non-electrical damage skips it.
- **Armor** protects the HEALTH POOL ONLY — it stops nothing else.
- **Health** decides life and death; every actor has one.

**R1 — 1 HP is 1 HP, always.** THE unifying law. The same armor type must always take the
same damage from the same hit, so **`DamageMultiplier` is abolished**:
- damage-reduction upgrades convert to **flat % of HP granted as additional ARMOR,
  additive** (15% reduction, i.e. `Modifier: 85`, becomes +15% of HP as armor);
- **no class-level `DamageMultiplier` on unit templates**;
- veterancy stops granting damage multipliers and **grants HP instead** — currently
  veterancy gives NO HP at all, only invisible multipliers. HP is visible in the unit stat
  widget; a multiplier is not. ⚠ This removes an invisible stat from the whole game and is
  a large re-pricing job — route it through the pipeline.
- **The ONE possible surviving use** (undecided): Superheavy + armor plating, which has no
  higher rung to promote into (see R5).

**R2 — Shields are 200% of HP** *because* the W15 Versus x5 rebase flips `%`-twins from
shield-resistant (median 25) to shield-punishing (~125). The bigger pool is the deliberate
compensation, not a coincidence. Shields regenerate fastest; armor slowest.

**R3 — Damage cascades.** Excess damage always flows into the next layer in the same shot,
exactly as `Shielded` behaves today. (So `BlockExcessDamage` stays `false`.)

**R4 — A `%`-warhead computes against the ACTIVE layer**, not max health — it is damaging
whatever the outer layer currently is.

**R5 — The armor layer's armor TYPE.** ✅ **LIVE since 2026-08-15** (W20 default = `Average`).
The three states, in the maintainer's words: *"shielded means only shield armor is active,
armored means armor plating + health armor types are averaged and health means only health
armor is active."* So the plating armor is gated on the plating's `FullCondition` and the
BODY armor stays enabled underneath it; only the SHIELD gates the body armor off.
- **Infantry: AVERAGE the body armor and the plating armor** (this is W20's `Average` mode,
  and it is what stops an anti-infantry weapon being useless against a plated cyborg —
  *"infantry with armor platings will still feel distinct from actual tanks"*).
- **Vehicles: the plating promotes one rung** — Scout→Light, Light→Medium, Medium→Heavy,
  Heavy→Superheavy. Superheavy has no rung above it (open).
- Per-class Health+Armor type COMBOS to be designed: `None+Scout`, `Flak+Light/Medium`,
  `Plate+Heavy/Superheavy`, etc.
- ✅ **SETTLED 2026-08-15 — average both, everywhere.** The maintainer's rule is stated for
  the ARMORED state as such, not for infantry only, and the mechanism is a warhead-wide
  default rather than a per-actor switch, so vehicles average too. This costs nothing: the
  promoted type is an ADJACENT rung, so averaging a tank barely moves it, while the same
  rule matters a lot for infantry, aircraft, ships and defences.

**R6 — Pool sizes.** Armor = 50% of HP **for units that start with an armor bar or get a
full bar from an upgrade**. Other upgrades granting armor stack ADDITIVELY on top.

**R7 — One ramp formula for all layers** (adopted):
`rate = base × min(1, ticks_since_damage / ramp)`, ramp = **25 health / 125 armor /
250 shield** (health doubles to 50 for infantry). Regen moves INTO the Health/Armor/Shield
traits — no more per-actor `Step`. (See the drift evidence above: 12.5% of 846 actors are
already off-rule.)

**R8 — Armor regenerates in combat, slowly** — no repair facility required, because not
every faction has one. Armor at **half** the earlier proposal, shield at **twice** it.
⚠ Exact numbers still to pin: the earlier worked example (100k HP → 40 HP/tick, 200k shield
→ 80/tick, 50k armor → 20/tick) made all three refill in the SAME time, which erases the
distinction. With R8's re-scaling they no longer do — confirm the final triple.

**R9 — Shield-break stun: ADOPTED, 25 ticks (1 second).** Accepted *because* shields now
stop physical-state meters and DoT as well, which is enormous. ⚠ Maintainer's own caveat,
recorded on purpose: a big AoE breaking every shield at once and stunning a whole army is
potentially miserable to play against — treat the 25 ticks as a starting value and be
willing to cut it.

**R10 — Repair vs heal split.** Repair restores **armor plates** (and vehicle health);
medics restore **infantry health only**. Neither restores shields — shields self-regenerate.

**R11 — Splash hits the top layer only** (current behaviour, kept). **Future idea, not
decided:** layer-PENETRATING weapons — railgun punches through armor straight to health,
sonic ignores shields. Note the data already leans this way: mean Versus vs Shield is
Sonic **55** and Railgun **75**, i.e. both are already poor against shields, so "ignore the
shield instead" is a thematic upgrade rather than a new axis.

**R12 — Who gets armor.** Cyborgs / droids / noids START with a bar; **any** unit can gain
one from an external effect or upgrade.

**R13 — UI.** Three bars: health green/yellow/red, shield purple, armor yellow-orange.
Gradients on shield/armor are OPTIONAL and off by default (colour overload risk). Build a
**combined segmented bar as a separate trait**, switchable from the game's visual settings
(3 bars ↔ 1 segmented bar). **All three bars are always visible to everyone**, and
**"Show Status Bars on Damage" must default to always-on** in the display settings.

**R14 — Tesla is the shield-killer** (verified: mean Versus vs Shield 228.8, the highest of
any family, next is Nuclear 155 and Storm 147.5). So the "shields hard-counter electrical"
worry is answered by design: you break the shield with the same weapon family you then use
on the electronics.

#### ⚠ The Heroic armor conflict is STRUCTURAL, not a data bug

Maintainer: *"Heroic is designed as the heaviest infantry armor, but this causes it to take
more damage from armor-piercing weapons meant to be anti-tank — suddenly they are really
good at fighting a commando. Heroic should always be the BEST armor."*

**Measured: of 186 main warheads carrying a full infantry ladder, 52 (28%) give Heroic a
HIGHER multiplier than some lighter infantry armor** — `^TeslaWeapon` None 125 / Flak 150 /
Plate 175 / **Heroic 200**, `^RailgunWeapon` 68/72/76/**80**, `^LaserWeapon` 44/56/72/**88**.
(A few of the 52 are `^HealingWeapon` / `^RepairWeapon`, where a higher number is a bigger
heal and therefore correct.)

**This is the ordering law working exactly as written** (macro-type priority x LIGHT/HEAVY,
AP -> heavy). Heroic is being asked to be two incompatible things at once: the heaviest rung
of the LIGHT→HEAVY infantry ladder, and "the best armour in the game". Under any law where
AP scales up with weight, those contradict. Three ways out:

- **(a) Take Heroic out of the ladder** — make it a QUALITY tier that sits at or near the
  best multiplier for every family. Clean semantics, but it is an exception to the ordering
  law, and the law is the thing keeping 2494 profiles coherent.
- **(b) Keep it in the ladder** and accept that a heavily armoured commando is precisely
  what an AP round is for. Costs nothing, and is defensible thematically.
- **(c) ★ Give commandos an ARMOR LAYER instead of a special armor type.** Their toughness
  comes from the extra bar (W21), not from bending the ladder — the ordering law stays
  intact and Heroic can retire to being just "heavy infantry". **This is the recommended
  option: W21 dissolves the problem instead of trading one exception for another.**

#### R1 addendum — "HP multiplier, not armor multiplier" (maintainer 2026-08-12)

Clarification: veterancy and upgrades should **raise the unit's maximum health dynamically**
rather than reduce incoming damage.

⚠ **VERIFIED BLOCKER: max health is IMMUTABLE in this engine.**
`engine/OpenRA.Mods.Common/Traits/Health.cs:81` declares `public int MaxHP { get; }` — a
get-only property assigned once in the constructor (`:69`). **No trait in
`OpenRA.Mods.Common`, `OpenRA.Mods.AS` or `OpenRA.Mods.Cameo` modifies it**; the only other
file that mentions max health, `AS/ActorStatValues.cs`, merely READS it for the stat widget.

So this is not a yaml swap. It needs `Health.cs` — a **core engine trait in the submodule**
(mirror workflow required) — made mutable, plus a ruling on what happens to CURRENT HP when
the maximum changes mid-life (scale proportionally, or keep absolute and heal the gap?).
`MaxHP` also feeds damage states, selection bars, husks, repair and AI evaluation, so
making it dynamic is invasive well beyond veterancy.

**✅ DECIDED 2026-08-12: veterancy and upgrades grant an ARMOR POOL, not max HP.** Max HP
stays immutable; no `Health.cs` change; the engine submodule is not touched.

**★ THE ALTERNATIVE, now the decision — grant an ARMOR POOL instead of raising max HP.** It is the
rule R1 already mandates for upgrades ("damage reduction becomes flat % of HP as additive
armor"), simply applied to veterancy as well:
- **zero engine change** — the layer trait is Cameo-side by design;
- **visible**, which was the whole point of dropping invisible multipliers — it shows as a
  bar, and `ActorStatValues` can total the layers for the stat widget;
- **additive and stackable**, so veterancy, upgrades and external effects compose without
  a special case;
- **one mechanism** for every "this unit is tougher now" effect in the game.

⚠ Either way, note the consequence under R4 (a `%`-warhead hits the ACTIVE layer): a bigger
pool means a percentage warhead removes proportionally more absolute HP, so **percentage
weapons give veterans NO protection at all** — they scale straight through. That makes
`%`-damage the natural anti-veteran counter. Decide whether that is a feature (it is a
clean rock-paper-scissors answer to deathballs of veterans) or needs a cap.

#### How a layer intercepts damage — the pattern, and the bug NOT to copy

`Shielded` never touches `Health.cs`. It absorbs damage with a two-step trick
(`engine/OpenRA.Mods.AS/Traits/Shielded.cs:138,197`):

1. `IDamageModifier.GetDamageModifier` returns **1** while the shield is up, so the engine
   scales the incoming hit to 1%. It returns 1 rather than 0 because a hit reduced to
   nothing would fire no damage event, and step 2 would never run.
2. `INotifyDamage.Damaged` then reconstructs the original (`e.Damage.Value / 0.01`),
   subtracts it from the shield pool, **heals back** the 1% that leaked to health
   (`InflictDamage` with negative damage), and cascades any excess to health — which is
   exactly R3's behaviour, already implemented.

**This is the pattern the armor layer should follow** (it needs no engine change and
composes with the shield automatically), **but not the arithmetic.**

⚠ **The 1%-round-trip loses damage, always downward.** `Util.ApplyPercentageModifiers` is
integer maths, so a hit of 5032 becomes `5032 × 1 / 100 = 50`, and 50 / 0.01 = **5000** —
the shield is charged 5000 for a 5032 hit. The residue is silently forgiven, up to 99 per
hit, which is a small systematic buff to every shield in the game.
⚠ **Below 100 damage it is total**: `99 × 1 / 100 = 0`, so a sub-100 hit costs the shield
nothing at all. Cameo's main damage sits in the thousands and lands on the 100 grid, so
mains are near-exact — but **Versus and Falloff scale damage before this point**, and DoT
ticks, physical-state chip damage and `%`-twin damage are all small. Those are precisely
the effects R9 just made shields responsible for absorbing.

**For the armor layer: carry the full-precision value yourself** instead of round-tripping
through a percentage — e.g. modifier 1 for the event, but subtract the pre-scaled damage
captured from `e.Damage`, or track the residue and carry it into the next hit. Worth fixing
in `Shielded` too, but that file is in the ENGINE SUBMODULE (mirror workflow), so the clean
path is a Cameo-side layer trait that both the armor bar and a future shield replacement
can share.

#### Still open

- The exact regen triple after R8's rescaling (R8).
- **The ledger has no concept of a layer.** `extract_stats` records one `#Armor.Type` per
  actor, so a plated walker is booked as its BODY armor (`Plate`) and the model prices it as
  plain infantry — the plating bar and the averaged type are invisible to pricing. Wiring
  the first three walkers moved the global armor census by one actor (`Plate` 89→90,
  `Superheavy` 94→93) and rippled every K in that faction by <0.01%, which is harmless now
  and will not be once plating is widespread. Decide before the rollout whether the ledger
  books the bare type, the plated type, or the average.
- Superheavy + plating: the one place a multiplier might survive (R1/R5). ⚠ Note that
  averaging (R5, now live) makes this LESS urgent, not more: a Superheavy body averaged
  with a Superheavy plating is still Superheavy, so the unit simply gains the bar without
  gaining a type — which may be answer enough.
- Which layer-penetrating weapons exist, if any (R11).
- Whether an EXTERNALLY granted shield protects electronics, or only a unit's own.

---

## 5. WHAT THE MODEL SAYS TODAY (the W1 baseline, for regression comparison)

All families at Heavy, 20 000 damage, abstract templates (so `reliability` = 1.00 —
the accuracy axis only differentiates on a concrete weapon with a projectile):

`Storm 2.43 · Flame 2.07 · Plasma 2.03 · Concussion 2.01 · Thermobaric 2.00 ·
Chemical 1.99 · Demolition 1.97 · Quantum 1.86 · Flak 1.84 · CannonHE 1.79 ·
CannonAP 1.76 · Sonic 1.63 · MissileHE 1.57 · MissileAP 1.52 · Magic 0.99 ·
Prism 0.84 · Bullet 0.81 · Tesla 0.81 · Railgun 0.75 · Laser 0.56`

Constants: `reference HP 74,000` (measured median) · `A_BLOB 9 cell²` · `A_SELF 1 cell²`
· `BLOB_UPTIME 0.30` · density INF 2.0 / VEH 0.33 / BLD 0.25 / AIR 0.20 · engagement
INF 35% / VEH 40% / BLD 15% / AIR 10%.

**If a change moves these numbers, that is the signal to explain in the commit message.**
W3, W4 and W5 all left this list **byte-identical** — verified after each.

**W15 is the first item that MOVED it, on purpose** (`reference HP 74,000 → 200,000`):

`Storm 2.94 · Flame 2.21 · Plasma 2.16 · Concussion 2.15 · Thermobaric 2.14 ·
Chemical 2.13 · Demolition 2.11 · Quantum 1.99 · Flak 1.96 · CannonHE 1.92 ·
CannonAP 1.89 · Sonic 1.70 · MissileHE 1.69 · MissileAP 1.64 · Magic 1.36 ·
Prism 0.96 · Bullet 0.92 · Tesla 0.89 · Railgun 0.83 · Laser 0.63`

`k_context`: `Storm 2.69 · Flame 2.02 · Plasma 1.98 · Concussion 1.96 · Thermobaric 1.96
· Chemical 1.95 · Demolition 1.93 · Flak 1.89 · Quantum 1.82 · CannonHE 1.76 ·
CannonAP 1.73 · MissileHE 1.63 · MissileAP 1.58 · Sonic 1.56 · Magic 1.24 ·
Bullet 0.89 · Prism 0.87 · Tesla 0.81 · Railgun 0.76 · Laser 0.61`

> **Historical model snapshot.** These values predate the 2026-08-25 type-based percentage
> repair, which found folded hits plus standalone nodes whose tags did not end `_Percentage`.
> Use the regenerated family table and derived sidecars for current comparisons.

Every family rose in that snapshot, because every family carries percentage damage and it was priced
against 2.7x more HP. What matters is that they rose UNEQUALLY, in proportion to how much
of the family's output is percentage damage:

| family | K before | K after | change | why |
|---|---|---|---|---|
| Magic | 0.99 | **1.36** | **+37%** | the %-equalizer family — mostly percentage damage by design |
| Storm | 2.43 | 2.94 | +21% | biggest footprint, so its %-twin catches the most targets |
| Prism · Bullet · Tesla · Laser | 0.81–0.84 | 0.89–0.96 | +13% | single-target: the twin is all they gain |
| Sonic | 1.63 | 1.70 | **+4%** | flat anti-low-HP by design — least %-exposed |

**Bare-K order is unchanged; `k_context` order changed once — MissileAP overtakes Sonic**
(1.58 vs 1.56). Both are the intended direction: Sonic is the deliberately flat family, so
raising the value of percentage damage should move it DOWN a generalist ladder, and the AA
capability that `targets_factor` rewards now decides a tie the %-shift created.

⚠ Magic's +37% is the number to watch when W13 restates the families: Magic was already the
%-based counter to high-HP targets, and it just got substantially better at its own job.

**W5 added a second baseline, `k_context`** (K × targets × range × deadzone):

`Storm 2.23 · Flame 1.89 · Plasma 1.86 · Concussion 1.84 · Thermobaric 1.83 ·
Chemical 1.82 · Demolition 1.81 · Flak 1.77 · Quantum 1.70 · CannonHE 1.64 ·
CannonAP 1.61 · MissileHE 1.51 · Sonic 1.49 · MissileAP 1.46 · Magic 0.91 ·
Bullet 0.78 · Prism 0.76 · Tesla 0.74 · Railgun 0.69 · Laser 0.54`

The ORDER changes against bare K, which is the point: **Flak overtakes Quantum** and
**MissileHE overtakes Sonic** because they can hit air and the others cannot. Under bare
K an AA-capable and a ground-only weapon were indistinguishable.

Constants added by W5: `TARGETS_FLOOR 0.5` · `RANGE_WEIGHT 0.25` ·
`RANGE_BOUNDS (0.75, 1.50)` · `DEADZONE_WEIGHT 1.0` · median weapon range **6000**
(measured over 2364 weapons that declare a Range).

---

## 5b. TOOLING AVAILABLE TO AGENTS (2026-08-11)

- **`gh` CLI 2.97.0 is installed** at `C:\Program Files\GitHub CLI\gh.exe`. It is NOT on
  the default PATH for a fresh shell — prepend it:
  `export PATH="$PATH:/c/Program Files/GitHub CLI"`. Use it for PR review comments, CI
  status and opening PRs instead of hand-rolling `curl` against the REST API.
  ✅ **Authenticated 2026-08-11** as `AedisToru`, scopes `gist, read:org, repo, workflow`;
  the repo resolves to `Zeruel87/Cameo-mod @ master`. `gh run list`, `gh pr view
  --comments` and `gh api` all work without further setup.
- **`openpyxl` 3.1.5** is present on the maintainer's Windows box, so `audit_balance_sheet`
  produces a real report here. It was MISSING on the Linux box that ran PR #251, which is
  why that PR committed `balance_sheet.md` as the 46-byte string "openpyxl not installed".
  **Any agent running the suite on Linux must `pip install openpyxl` first** or it will
  silently commit a degraded report.
- **`.github/dependabot.yml`** keeps the SHA-pinned actions fresh (weekly, grouped into
  one PR). Version updates only activate once it is on the default branch of the hosted
  repo — it does nothing while unpushed.

## 6. LINKS

`EFFECTIVE_DAMAGE.md` (the metric) · `BALANCE_PIPELINE.md` (the loop) ·
`FORMULA_V2.md` (the laws) · `PHYSICAL_STATE_SYSTEM.md` (meters) ·
`SPREAD_FALLOFF_PLAN.md` (falloff shapes) · `WEAPON_3WAY_SPLIT.md` (the split) ·
`ROADMAP.md` (everything else) · `AI_HANDOFF_2026-08-05.md` (agent letters)

---

---

# 7. THE PHASE MAP (A→G) — the strategic sequence

_Merged 2026-08-23 from `BALANCE_PROGRAM_PLAN.md`, unedited below this line. It lived as a separate
file for two weeks and spent that time disagreeing with §0a and §1 about status and order._

⚠ **§0a above is BINDING and supersedes any ordering here.** §0a is the newer ruling
(2026-08-17) and it is measured; this phase map is the strategic frame it sits inside. Where
the two disagree on ORDER, §0a wins. Where either disagrees with the tree on STATUS, the
**artifact** wins — verify, then fix both.

⚠ **This section carries 20 `memory <name>` citations.** They point at a private, per-agent
memory store no other reader can open. Provenance only, never authority: promote anything
binding into `DESIGN.md`, and pin any number in `docs/audit/doc_claims.yaml`.

The single source of truth for **what order** to build the balance pipeline and **everything it
needs** to be complete. Written 2026-08-04. This does not replace the detailed docs — it **threads
them** into one sequence so we never lose the order. Each phase links the doc that owns the detail.

> **Authority note (rev. 2026-08-23) — three files, three jobs, no overlap:**
>
> | file | owns |
> |---|---|
> | **this file** | the strategic **phase sequence** (what order, A→G) |
> | [`BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md) | **status, ownership, acceptance criteria** — the W1–W26 board, the file-set map (§2), the binding order of operations (§0a) |
> | [`ROADMAP.md`](ROADMAP.md) | the **live granular queue** — individual tasks + commit hashes; crashes jump it |
>
> ⚠ **Where §0a of `BALANCE_PROGRAM_PLAN.md` and the phase order below disagree, §0a wins** — it is
> the newer ruling (2026-08-17) and it is measured. When any of the three disagree on *status*, the
> **artifact** wins: verify, then fix all of them.
>
> This doc supersedes the older `MEGAPLAN.md`, archived at
> [`../history/MEGAPLAN_2026-08-08.md`](../history/MEGAPLAN_2026-08-08.md).
> [`../history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md`](../history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md)
> is historical — its warhead conversion is complete (see §1).
>
> ⚠ **This file carries 20 `memory <name>` citations.** They point at a private, per-agent memory
> store that no other reader — maintainer, co-maintainer or another agent — can open. Treat every
> one as **provenance, never authority**. If a memory carries a binding rule, promote it into
> `DESIGN.md`; if it carries a number, pin it in `docs/audit/doc_claims.yaml`.
>
> Companion docs (do NOT duplicate — this indexes them): `BALANCE_PIPELINE.md` (the sanctioned
> loop), `FORMULA_V2.md` (the laws), `BALANCE_SYNTHESIS.md` (synthesis laws), `ARMOR_SYSTEM.md` +
> `WEAPON_TYPE_SYSTEM.md` + `WEAPON_3WAY_SPLIT.md` (weapon/armor grammar), `SPREAD_FALLOFF_PLAN.md`
> (per-type spread/falloff profiles), `AREADAMAGE_WARHEAD.md` (warhead design + energy chips),
> `ORIGINAL_UNIT_STATS.md` + `ORIGINAL_UNITS_RAW.md` + `PROJECTILE_AND_EFFECT_LAYER.md` +
> `FACTION_IDENTITY.md` (reference material), `class_anchors.json` + `anchor_decisions_log.md` +
> `vehicle_class_decisions.md` (anchors), `discrepancies.md` (Phase-3 triage).

---

### 0. The mental model — 3 layers feeding one formula, applied through anchors

```
 LAYER 1  ORIGINAL_UNIT_STATS.md   cross-game reference library (whole C&C series + SC2 all
          (+ ORIGINAL_UNITS_RAW)   branches + WC3 + Cosmonarchy + Dune/Outpost2). [STAT] vs
                                    [IDENTITY] tagging, per-game normalization.
    +
 LAYER 2  extracted MODS           MO / CnCR / RV (RA2), SP / CnCR (TS), DTA / CA (TD+RA1).
                                    "how a good mod already tuned this unit."
    +
 LAYER 3  old Cameo + synthesis    the mod's own history + faction identity choices.
    |
    v  synthesize (well-reasoned, per-unit unique) + the FORMULA
 CLASS ANCHORS  (class_anchors.json)  per-class baseline: HP/Cost, DPS/Cost, A/B, tier, K.
    |
    v  members spread by formula(baseline weights) + synthesis, NEVER equal to the anchor
 PER-UNIT STATS  ->  ledger (docs/balance/*.json)  ->  yaml  (via apply_balance)
```

**Two laws that govern everything (never violate):**
- **Never hand-edit a balance number in yaml.** Everything flows ledger/workbook -> `apply_balance`.
  `audit_balance_drift` fails red when yaml and the committed ledger disagree.
- **Anchors are BASELINE comparisons, NOT per-unit targets.** HP/Cost, DPS/Cost, A/B aggregates
  describe the class; members are UNIQUE, spread by the formula + synthesis.

---

### 1. Where we are (VERIFIED 2026-08-08 — supersedes the 2026-08-04 snapshot)

**Phase A (weapon/warhead foundation) — the bulk of the STRUCTURE is done; tuning + collapse remain:**
- **Warheads: DONE.** Universal `AreaDamage` conversion complete — every live weapon main is
  `AreaDamage` + baked 50/50 FF (`Ally, Neutral, Enemy`); `_FriendlyFire` twins retired; Nuclear
  superweapon hand-tuned; `AreaDamagePercentage` for %HP. C# built + boot-proven.
- **A1 generator reconcile: ✅ DONE.** `gen_weapon_template.py` emits AreaDamage + baked FF +
  `^Warhead_<Family>_<Level>` + `_Percentage`; guard `verify_generator_sync.py` (run_all.sh `gen_sync`)
  reports **drift = 0** → regenerate is a verified no-op.
- **A2 cannon templates: ✅ BUILT.** `^Warhead_CannonAP_{L/M/H}` + `^Warhead_CannonHE_{L/M/H}` exist
  (weapons.yaml ~3429–3720), on the two-level ordering law. Repointing weapons onto them proceeds via
  the Phase-B collapse.
- **A3 projectile/effect libraries: ✅ BUILT.** `^Projectile_<Family>_<Level>` + `^Effect_<Family>_<Level>`
  (`gen_effects.py`); weapons inherit them via the 3-way split.
- **A4 weapon tuning — PARTLY done:** energy `_ExtraDamage` chips reworked (paid-for law) + thin energy
  spread ✅ (`b068a94f6`); MissileAA spread reduction ✅. **OPEN:** per-type spread/falloff profiles
  (DESIGNED in `SPREAD_FALLOFF_PLAN.md`, not yet applied — awaiting authoring-model pick), projectile-
  speed / tank-shell rules (documented, not applied), Railgun charge-delay downside, the spread-pricing
  formula term.
- **Weapon 3-way split: Phase A DONE** (0 single-inherit weapons remain). **Phase B (mixed-family
  collapse) IN PROGRESS** — Sniper family (21 weapons ✅ `fa1016d21`), Chemical 2-family group
  (5 weapons ✅ `ac17eb827`); **~350+ mixed weapons in ~250 groups remain** (maintainer-directed,
  dominant-damage heuristic in `docs/audit/latest/phase_b_survey.md`). This IS Phase A5 (retiring the
  deprecated inline old-family damage keys) — same effort, one queue.
- Guards green: `find_empty_warhead.py = 0`, `find_orphan_old_keys{,_multi}.py = 0 real`.

**Phase B (reference material):**
- **B2 extract CnCR + RV: ✅ DONE** (325 + 208 units in `ORIGINAL_UNITS_RAW.md`; sources in
  `~/Downloads`). All Layer-2 mods extracted (DTA/CA/SP/MO/CnCR/RV); only Dune/Outpost2 stubs pending.
  Remaining reference work = R4 synthesis into per-class targets (B1/B3).

**Phase C (anchors):**
- **Vehicle 13-class anchors LOCKED** (`class_anchors.json` + `anchor_decisions_log.md` "★ LOCKED
  2026-08-01"); templates built + armor normalized per-class. RESTAT of baselines+members pending
  (needs weapon DPS/range stable from A4).
- Infantry-class proposals drafted (`docs/balance/proposal_*_infantry.md`); 4 new templates +
  `^AntiTankAntiAir` split + scout-verifier tier fix pending, then lock.
- Defense + aircraft anchors: not started.

**Phases D–G:** `FORMULA_V2` has open terms (spread-pricing, AA/AoE pricing, per-class defense/infantry
baselines). Ledgers exist (`docs/balance/*.json`, 28 factions) but many predate current laws. Workbooks
exist (`cameo_armor_system.xlsx` legacy reference plus the active
`cameo_balance_by_faction.xlsx` / `cameo_balance_by_type.xlsx` workbenches). Per-faction
synthesize→apply (F) not started. Phase-3 discrepancy triage open (`docs/balance/discrepancies.md`).

---

### 2. PHASE A — finish the WEAPON / WARHEAD foundation (unblocks DPS + range for everything)

*Balance cannot be finalized until every weapon's effective DPS + range is stable, because pricing
is driven by EFFECTIVE DPS = raw × ∏ firepower knobs.*
⚠ **`FirepowerMultiplier` is LIVE AS A READ, RETIRED AS A WRITE** (verified in the code
2026-08-23). Pricing must keep reading it — `formula.py` is literally
`return base * firepower_multiplier`, `extract_stats.py` pulls one unconditional,
locally-defined multiplier per actor, and 152 actors carry one. But nothing may ADD a new
one: W26/R1 is retiring that class of knob. Saying only "live" invites a new one; saying
only "retired" makes the pricing look broken.

- **A1. Generator reconcile (AreaDamage drift) — TOP PRIORITY.** `gen_weapon_template.py` still
  emits `SpreadDamage` + old naming; the 54-template flip was a one-shot script. Update the
  generator to emit `AreaDamage` + `ValidRelationships: Ally, Neutral, Enemy` + `FriendlyFireDamage/
  Spread 50`, drop the FF twin, `^Warhead_{tag}`/`Warhead@{tag}_Percentage` naming. Then
  `regenerate + diff` the 54 non-Nuclear templates == file (no-op). **Until then DO NOT regenerate**
  (would revert). (`../history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md` §3c)
- **A2. Cannon/weapon rebuild** — `CannonAP_{L/M/H}` (anti-heavy) + `CannonHE_{L/M/H}` (anti-veh);
  current cannons -> CannonHE, TankDestroyerCannon -> CannonAP_Light. Built by `gen_weapon_template.py`
  via the two-level ordering law (macro priority × light/heavy). (
  `cameo-weapon-ordering-law`; docs `ARMOR_SYSTEM.md` §PROFILE, `WEAPON_TYPE_SYSTEM.md`)
- **A3. Projectile + effect template libraries** — `^Projectile<Family>_<Level>` + `^Effect<...>`
  (3-way split, `WEAPON_3WAY_SPLIT.md`, `PROJECTILE_AND_EFFECT_LAYER.md`). Retrofit weapons inherit
  them. Custom effects = RGBA PngSheet, pair every effect with a sound.
- **A4. Weapon tuning laws** (all in `AREADAMAGE_WARHEAD.md` §3–§5):
  - Energy `_ExtraDamage` chips repurposed with LOCKED ladders (Laser=anti-inf, Railgun=anti-building
    +superheavy Concrete 200>Steel 175>Wood 150 / Shield 10, Tesla=anti-inf+shield keep, Prism/Magic
    =none); thin energy main Spread ~800->150.
  - MissileAA spread reduction (never applied).
  - Projectile-speed / tank-shell rules (regular tank speed=maxRange/10 CannonHE 2×spread; TD +
    cannon-turret speed=maxRange/5 CannonAP small spread; hybrid 50/50 speed=maxRange/10×1.5).
  - Overall spread reduction + a **spread-pricing term** in the formula (diminishing returns,
    expected-targets-hit, capped by the single-target case).
- **A5. Retire deprecated inline damage keys** — 297 live weapons still on inline `Warhead@1Dam`
  etc.; convert to template inherits (DESIGN §870).

**Guard for A:** `audit_warhead_split`, `audit_template_conformance`, `find_empty_warhead.py`
(now blocking in `run_all.sh`), + BOOT GATE. Versus lives ONLY in `^Warhead_*` templates.

---

### 3. PHASE B — REFERENCE MATERIAL (the deep research; feeds every anchor)

*The 3-layer framework.*

- **B1. Layer 1 completeness — `ORIGINAL_UNIT_STATS.md`.** The cross-game library. Ensure every
  Cameo unit has its original-source row(s), `[STAT]` (raw numbers) vs `[IDENTITY]` (role/flavor)
  tagged, per-game normalized to Cameo's scale. Faction identity sources: Japan = RA3 Empire + WW2 +
  Touhou; AsianAlliance = Generals China. (⚠ RA2 unitstatistics "health" is a 1–5 rating, NOT raw HP.)
- **B2. Layer 2 — extract the remaining reference MODS + normalize.** DONE: DTA, CA, SP, MO.
  **PENDING: CnCR, RV.** Extract their unit stats, normalize, fold into the per-unit reference rows.
. Also `RESEARCH_NOTES.md` (SP done).
- **B3. Layer 3 — synthesis inputs.** Old Cameo values + `FACTION_IDENTITY.md` + rock-paper-scissors
  mandate. This is the "well-reasoned" judgment layer that combines B1+B2 into an intended role.

---

### 4. PHASE C — ANCHORS (per-class baselines, the synthesis output)

*Class anchor = the baseline a class's members are spread around by the formula. Aggregate targets
only (HP/Cost, DPS/Cost, A/B), NOT per-unit.*

- **C1. Vehicle anchors — LOCKED (13 classes).** `class_anchors.json` + `anchor_decisions_log.md`
  ("★ LOCKED 2026-08-01"): epic-top, ≤2.0× A+B spread, HP 10k-steps, DPS/Cost 0.5–1.5. RESUME =
  restat the 13 baselines + members once A2/A4 land (DPS/range stable). `vehicle_class_decisions.md`,
  `vehicle_class_review.md`, `membership_review.md`, `proposal_vehicle_defense_anchors.md`.
- **C2. Infantry class anchors — draft -> lock.** 12 proposals exist (`proposal_*_infantry.md`:
  scout, closecombat, grenadier, mortar, melee, archer, heavy, flying, rocket_trooper, heavy_sniper,
  pure_sniper, special_forces). NEED: 4 new templates (heavy sniper / rocket trooper / archer /
  support), `^AntiTankAntiAir` split, fix scout verifier tier (forgotten_mutantsoldier is T3 not T1).
. Lock into `class_anchors.json`.
- **C3. Defense + aircraft anchors.** Per-class baselines for defenses + aircraft (memory
  `cameo-formula-future-tasks`). AA class-gating (only some classes get AA).

**Anchor law:** baseline + its verifier must share the same
TechTier M-bucket AND K, or the 2.5× identity breaks (T1=T2=M1.0, T3=0.75, T4/5=0.5; tier from
tech-building prereqs only; gatling K1.25; charge-up K adjust).

---

### 5. PHASE D — the FORMULA (FORMULA_V2 completeness)

*Read `FORMULA_V2.md` FIRST: O=P=Q=cost baselines, 2×/2×/250%
verifiers, stat bands, conversion checklist.*

- **D1. Complete the missing terms**: per-class baselines
  (defenses + infantry), AA pricing, AoE pricing, per-ability specials, the **spread-pricing term**
  (from A4). Bake OUT per-actor multipliers, keep only global 50%+150% (BALANCE_SYNTHESIS law).
- **D2. Verifier laws** — tier+K match (C3), FirepowerMultiplier in effective DPS (unconditional one
  per actor; deploy/undeploy units priced as separate actors —).
- Code home: `tools/balance/formula.py` (+ `extract_stats.py` provenance).

---

### 6. PHASE E — the EXCEL / WORKBOOK pipeline

*Pipeline law: set a price in the raw ledger or an unlocked cell of an active generated
workbench, import it, then let guarded tooling update yaml; never scale costs directly in yaml.
Regenerate both active workbenches after the ledger changes. The legacy workbook is not a
required parallel write.*

- **E1. Legacy reference** `cameo_armor_system.xlsx` remains the design-judgment reference until the
  Phase-3 discrepancy triage completes (`discrepancies.md`).
- **E2. The active workbenches** — `tools/balance/build_workbook.py` generates the tracked
  `cameo_balance_by_faction.xlsx` / `cameo_balance_by_type.xlsx`; edit the UNLOCKED input cells
  and read one back with `import_workbook.py --workbook faction|type`.
  `cameo_balance_v2.xlsx` is the frozen pre-split prototype. Excel is OPTIONAL — you can edit the
  ledger JSON directly instead.

---

### 7. PHASE F — SYNTHESIZE + APPLY (per faction/class, the actual rebalance)

*The sanctioned loop (`BALANCE_PIPELINE.md`), repeated per faction/class:*

1. `python tools/balance/extract_stats.py` — refresh the ledger from yaml (raw stats + provenance).
2. **Synthesize members** from the anchor (Phase C) + reference (Phase B) via the formula (Phase D):
   each member UNIQUE, spread by formula(baseline weights) + `BALANCE_SYNTHESIS.md` (tighten spread
   0.4–3.5× rifle, strict class↔weapon binding, rock-paper-scissors). Write into the LEDGER (or the
   workbook, Phase E). `propose_class_rebalance.py` / `propose_rebalance.py` assist.
3. `python tools/balance/fit_class.py` — fit members to the anchor (applies FP-mult, skips
   conditional arms). Then `apply_balance.py --faction X --confirm` (dry-run WITHOUT `--confirm`).
   **`--confirm` requires an explicit maintainer order.**
4. Re-run `extract_stats.py`, run `tools/audit/run_all.sh` + **BOOT GATE**, commit yaml + ledger
   TOGETHER.

Do this class-by-class / faction-by-faction. Recommended order: get ONE class end-to-end (e.g. the
13 vehicle classes, since they're locked) as the reference implementation, then infantry, defenses,
aircraft, then per-faction sweeps.

---

### 8. PHASE G — DISCREPANCY TRIAGE + CLEANUP (runs alongside)

- **Phase-3 discrepancy triage** — `docs/balance/discrepancies.md`: reconcile the legacy
  `cameo_armor_system.xlsx` vs the new laws; retire the legacy sheet when clean.
- **YAML cleanup** — `MEGAPLAN_YAML_CLEANUP.md`, `weapons_cleanup_plan.md`: dead weapon files
  (redalert2.yaml etc.) deletion, actor-inheritance -> `^Templates` review (deferred, grandfathered
  —), closed-file-set discipline.
- **ContentPack migration** (the mission end-goal) — split remaining monoliths, per-faction ai.yaml,
  move assets in (`docs/MIGRATION.md`). Balance-independent;
  can run in parallel.

---

### 9. THE CANONICAL ORDER (one sequence — do not reorder A before B where noted)

```
A1 generator reconcile (unblocks safe regen)          <- DO FIRST (warhead work in flight)
A2 cannon/weapon rebuild (CannonAP/HE ×L/M/H)         <- unblocks DPS/range
A3 projectile + effect templates
A4 weapon tuning laws (energy chips, spreads, speeds, spread-pricing)
A5 retire inline damage keys
        |  (weapons stable -> DPS/range stable)
B1 ORIGINAL_UNIT_STATS completeness                    <- reference, can parallel A
B2 extract CnCR + RV, normalize
B3 synthesis inputs (faction identity)
        |
D1/D2 finish FORMULA_V2 terms (spread-pricing needs A4)
        |
C1 vehicle anchors restat (locked; needs A2/A4)
C2 infantry anchors (4 new templates, lock proposals)
C3 defense + aircraft anchors
        |
E build/refresh workbooks (or edit ledgers directly)
        |
F  per class/faction: extract -> synthesize members -> fit_class -> apply_balance --confirm
   -> audit + BOOT + commit   (repeat for all 28 factions / all classes)
        |
G  discrepancy triage + yaml/ContentPack cleanup  (parallel throughout)
```

---

### 10. GUARDRAILS (invariants that must ALWAYS hold — the pipeline is not "done" until all green)

- **BOOT GATE before every commit** — the only thing that
  catches junk trait nodes.
- **`tools/audit/run_all.sh` green** — incl. `audit_balance_drift` (yaml==ledger), `audit_warhead_split`,
  `audit_template_conformance`, `find_empty_warhead.py` (blocking), `audit_stat_formulas`.
- **Never hand-edit balance numbers** (pipeline only). **Never change a warhead/Burst/BurstDelays
  without explicit permission**.
- **Versus ONLY in `^Warhead_*` templates**.
- **Scoped `git add`, never `-A`** (maintainer WIP). **Reports via bash `run_all.sh` only** (PowerShell
  `>` = UTF-16 hazard). **Underscore-only naming** (no hyphens).
- **The DLL loads from `engine/bin`** (rebuild after C# changes; copy to the tracked `mods/cameo`
  copy for release —).

---

### 11. "DONE" definition (the finish line)

The balance pipeline is complete when: every weapon uses templated AreaDamage + templated Versus with
stable effective DPS (Phase A); every unit has reference rows from all 3 layers (Phase B); every class
has a locked anchor (Phase C); FORMULA_V2 has no missing terms (Phase D); every faction's ledger is
formula-derived, workbook-consistent, and applied to yaml (Phase F); `run_all.sh` is fully green and
the game boots (Phase G + guardrails). At that point a single `extract_stats -> fit_class ->
apply_balance` round-trip is a no-op diff — the definition of a converged pipeline.

---

### 12. Open-items checklist (verified 2026-08-08; tick as completed)

- [x] A1 generator reconcile (AreaDamage, drift=0)  · [x] A2 cannon templates built  · [x] A3 projectile/effect libs
- [x] A4 energy chips (paid-for) · [x] A4 MissileAA spread reduction
- [ ] A4 per-type spread/falloff profiles (DESIGNED in SPREAD_FALLOFF_PLAN.md; pick authoring model → generate → boot)
- [ ] A4 projectile-speed / tank-shell rules applied (AP `range/5`, HE `range/10` 2× spread, artillery slow lob)
- [ ] A4 Railgun charge-delay downside (= 50% ReloadDelay, armament-level)  · [ ] A4 spread-pricing formula term
- [ ] A5 / Phase B: collapse the ~350+ remaining mixed-family weapons (dominant-damage; retires inline old keys)
- [ ] B1 ORIGINAL_UNIT_STATS complete  · [x] B2 extract CnCR + RV (done)  · [ ] B3 faction-identity synthesis
- [ ] D1 FORMULA_V2 missing terms (spread-pricing, AA/AoE, per-class defense/infantry baselines)  · [ ] D2 verifier laws wired into extract/fit
- [ ] C1 vehicle anchors restat  · [ ] C2 infantry anchors (4 templates + lock)  · [ ] C3 defense/aircraft anchors
- [ ] E workbooks refreshed (or ledger-direct)
- [ ] F per-class/faction synthesize -> fit -> apply -> audit -> boot -> commit (×all)
- [ ] G discrepancy triage clean · legacy xlsx retired · yaml/ContentPack cleanup
- [ ] Guardrails: run_all.sh fully green + round-trip no-op

---

## W23 — Retrofit the 45 legacy templates into the `^Warhead_*` family system 🔵 MACHINERY DONE, content BLOCKED on one ruling

**Why.** DESIGN.md §12 is explicit that **`Versus` lives ONLY in `^Warhead_*` templates**. 47
templates still declare their own and **1196 weapons inherit them**, so every one is both a
migration target and a live rule violation — and their ladders pollute the Versus census that
W1's K coefficient, `armor_exposure.py` and the family surveys are all built on.

### Tooling (committed, verified)

| tool | what it answers |
|---|---|
| `tools/audit/audit_unconverted_templates.py` | which templates are still outside the system (45 / 1196) |
| `tools/balance/measure_retrofit_gap.py` | how far each legacy ladder sits from its target family, and **which** family by rank correlation |
| `tools/balance/retrofit_legacy_template.py` | **quarantined**: retired separate-percentage-twin writer; always refuses until redesigned for folded percentage |
| `tools/balance/verify_retrofit.py` | proves resolved behaviour survived (mean output held, no orphans, no geometry drift) |
| `tools/balance/remove_dead_weapons.py` | deletes loaded-but-unused definitions that bias the census |

**Measured:** 25 templates convertible, **median gap 1.279x** — so a naive repoint would have made
~1300 weapons a third more lethal. Full table: `docs/audit/latest/retrofit_gap.json`.

**Data-driven decisions the correlation check made** (shape, not name):
- all three missile templates are **AP**, not HE (corr 0.77 vs 0.30);
- `^Grenade` -> `Demolition_Light`, not Concussion (0.94 vs 0.79).

### Excluded by design — need a maintainer ruling, not a script

| template | why |
|---|---|
| `^MagicWeapon` | target `^Warhead_Magic_Heavy` is **FLAT 32 vs every armor** (the %-equalizer); the legacy is a 140->40 ladder, so converting DELETES its armor discrimination |
| `^NuclearWarhead` | family is hand-tuned to **BLD > VEH > AIR > INF**; the legacy ladder is anti-heavy, so a repoint re-roles the weapon |
| `^LightFlameWeapon` | **W2 owns it** — the maintainer split it across FOUR families per weapon, and its `Range: 500` P1 bug is still open |

### ✅ THE FORMER BLOCKER — 33 weapons collide inside one family (DISSOLVED)

> **Resolved by §0a + DESIGN §11b.** The design question below ("should a weapon carry three
> separate cannon warheads of the same family at all?") is already answered: **no** — §11b makes
> ONE damage warhead per weapon binding, and W24 executes it. Once a weapon carries a single
> damage main there is nothing for the rename to merge, so the collisions were this debt made
> VISIBLE, not a conversion bug. The consequence is ORDERING, not a block: **run W24 first, then
> this batch.** The analysis below is kept as the evidence for that ruling.

582 of 615 affected weapons convert with their mean output **exactly preserved**. The other 33
inherit **several legacy templates that map into the SAME family**, so after the rename MiniYaml
merges two independent warheads into one node and the smaller one's damage disappears:

- `GladiusCannon` inherits `^MediumCannon` + `^HeavyCannon` + `^TankDestroyerCannon` **and**
  already carries `CannonHE_Medium`/`CannonHE_Heavy`/`CannonAP_Light` — it lost **30 000** damage.
- `AsianSniperAP` had `Warhead@SmallArms: 6000` *and* `Warhead@Bullet_Light: 16000` as separate
  SUM-law sources; the rename collapsed them.

A SUM-law compensation pass (write the total into the weapon's own block) recovers most of it —
`GladiusCannon` from -30% to -6% — but cannot close it, because each template converts in its own
pass and the collisions compound. **The real question is a design one: should a weapon carry three
separate cannon warheads of the same family at all?** Under the one-weapon-one-warhead intent it
should be ONE warhead at the summed damage; that is a maintainer call.

**NEXT:** finish W24 for the affected weapons (which removes the collisions), then run the
batch (25 templates, ~2839 keys, one boot gate). No further ruling is owed.

### Also found — obsolete definitions that bias the census

`^AACannon`, `^RAHeavyMG`, `^RALightMG`, `^Artillery`, `^TSRailgun`, `^TSArtilleryWeapon` are
**loaded by the live ruleset, inherited by nothing and fired by nothing**, yet each still
contributes a `Versus` ladder to every census. Their only referrers sit in commented-out files.
Maintainer, 2026-08-16: *"obsolete things should be removed entirely so they don't affect our
unit / weapon balance."* Deletion is ready (`remove_dead_weapons.py`) and needs a boot gate.
⚠ The `--survey` mode deliberately SKIPS unused `^Warhead_*`/`^Effect_*`/`^Projectile_*` — the
generator ships that matrix on purpose and `verify_generator_sync.py` requires it.


---

## W24 / W25 — see `ARMOR_LAYERS.md` and DESIGN.md §11b

**W24 (one warhead per weapon)** is now a written binding rule — DESIGN.md **§11b**. Among
directly fired weapons, **243** carry 2 or more damage
warheads, worst case **6**. Including indirect weapon-graph reachability gives **299**. This is the debt the W23 retrofit exposed, and it must be paid before the retrofit
content ships, because same-family collisions are a symptom of it rather than a bug in the
conversion. This paragraph's counts and examples are historical. The former blanket
SUM instruction is superseded by DESIGN §11b.1; use its current value policy and
review non-identical or staged payloads rather than assuming equivalence. Where no
family fits, propose a NEW family rather than forcing a bad one (maintainer,
2026-08-16). Two historically identified examples:
`Waveforce` (Plasma × Quantum) for the Japanese energy rifles, and `Plasma` for
`GladiusCannon`, which inherits `PhotonCannon`.

**W25 (normalisation + Shield)** — full analysis in
[`ARMOR_LAYERS.md`](ARMOR_LAYERS.md). Headline: the
anti-shield identity is INVERTED (Melee 200, Tesla 151), because `Shield = top + floor` was
written for peak-100 profiles and W13 renormalised to median-100. The corpus **cannot**
arbitrate it — `shield` appears in **13 of 3150** profiles, from **1 of 16** mods — so the
ladder must come from design intent plus the structural `CEILING + floor` rule, not from a
3-way average over data that does not exist. Four decisions are owed: the Shield range,
whether Nuclear is an exception to "Super is a generalist", Option A/B/C, and whether
`Shield` should remain a `Versus` row at all now that W21 made shields a real health layer.
