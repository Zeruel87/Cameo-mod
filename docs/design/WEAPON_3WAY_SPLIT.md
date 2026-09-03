# WEAPON 3-WAY SPLIT — warhead / projectile / effect layers (2026-08-02)

> ⚠ **SUPERSEDED (W15/W17, 2026-08-15).** The grid is now `formula.DAMAGE_STEP` = **100**, the `%`-twin comes from `formula.percentage_twin()` (not `damage // 2000`), and `FirepowerMultiplier` is retired as a fine-tuning knob — `apply_balance` cannot write it and `decompose_dps` always solves at `fp = 1.0`. Read every "multiple of 2000" mention below as history.
> The split itself is unaffected — it preserves `Damage` verbatim either way.

_The repoint architecture. Maintainer decision 2026-08-02: "do the full split
now." Supersedes the naive "reparent onto warhead-only templates" plan (which
would orphan 392/437 override keys + strip FX). Companion to
`WEAPON_TYPE_SYSTEM.md` (warhead layer) + `ARMOR_SYSTEM.md` (Versus law)._

## The model — up to 4 inherits per weapon

The **2-inherit cap is on WARHEADS**, not total inherits. A weapon composes ONE
of each layer (warhead may be 1–2):

```
SomeWeapon:
    Inherits@wh:   ^Bullet_Light      # 1–2 WARHEAD templates (Versus + damage + % + FF twin)
    Inherits@proj: ^ProjectileBullet_Light   # 1 PROJECTILE template
    Inherits@fx:   ^EffectBullet_Light        # 1 EFFECT template (impact FX + shield + smudge/specials)
    ReloadDelay: 20                     # per-weapon: cadence
    Range: 4608                          # per-weapon: range (beautiful ranges preserved)
    Report: gun8.aud                     # per-weapon: sound
    Warhead@Bullet_Light:                # main-damage override — ON THE 2000-GRID, all mains identical
        Damage: 4000                     # multiple of 2000; twins auto (FF 50%, % = 1-per-2000)
```

**DAMAGE LAW (DESIGN.md §nice-number, do NOT violate):** main `Damage` is ALWAYS a
**multiple of 2000** (`total ÷ N`, all N mains identical), **never off-grid, never
hand-nudged**. Effective damage is fine-tuned ONLY by a single **unconditional
`FirepowerMultiplier` named after the actor, on the unit itself** — never by editing
`Damage`. The retrofit is therefore **purely structural**: it renames the damage key
and PRESERVES the weapon's existing on-grid value verbatim; it invents NO numbers. The
2000-grid re-quantise + per-actor FirepowerMultiplier are the **restat's** job (the
balance pipeline: `extract_stats` → workbook → `apply_balance --confirm`).

- **Layer 1 WARHEAD** = the 99-template library (`gen_weapon_template.py`, committed
  `fa0947ae5`/`956cf1ecb`) — pure Versus/damage/%/FF, FX/projectile-agnostic by design.
  FF twin (AoE) done; ExtraDamage twin (energy) handled per-weapon in the energy retrofit.
- **Layer 2 PROJECTILE** = the `Projectile:` block only.
- **Layer 3 EFFECT** = all the non-damage warheads: CreateEffect impact visuals
  (@Effect/@EffectAir/@EffectWater), @ShieldHit + @ShieldHitEffect, LeaveSmudge craters,
  and specials (@EMPUnit, @GroundFire, @ApplyPhysicalState, @DamagesConcrete).

Why: the OLD central templates (^SmallArms/^Grenade/…) are FULL-STACK and weapons hook
their warheads BY THE OLD KEY NAME + rely on their bundled FX, so a bare reparent breaks
them. The split lets a weapon pick its damage identity independently of look/delivery.

## Layer 2 — PROJECTILE templates

> **Naming resolved 2026-08-02:** the shipped prefix is `^Projectile_*` (not the early `^Proj*`
> proposal below). Derived from the 30 old templates' `Projectile:` blocks
> (catalog 2026-08-02; current `weapons.yaml` has 30 `^Projectile_*` + 48 `^Effect_*` + 99 `^Warhead_*`).

| Proposed | Projectile | Signature | From (old templates) |
|---|---|---|---|
| **^ProjBullet** | Bullet | 50CAL, contrail, Speed 2000–4000 | SmallArms, Chaingun |
| **^ProjFlak** | Bullet | 50CAL, contrail, Speed 7500–10000 (fast AA) | HeavyAAWeapon, FlakWeapon |
| **^ProjShell** | Bullet | 120MM, Speed 500, Shadow, arc; Inaccuracy L/M/H = 150/300/450 | TD/Medium/HeavyCannon |
| **^ProjGrenade** | Bullet | Speed 150, LaunchAngle 66, BOMB, Inaccuracy 400 | Grenade |
| **^ProjMissile** | Missile | DRAGON/MISSILE, homing; turn-rate L/M/H = 40/30/20 | Light/Medium/HeavyMissile |
| **^ProjArrow** | Missile | Inaccuracy 0, turn 40, PointDefenseTypes=Missile | ArrowWeapon |
| **^ProjSpray** | Bullet | Speed 3000–3500, short range (flame/chem) | Flame×3, Chemical×3 |
| **^ProjLaser** | LaserZap | Width 100, HitAnim laserfire | LaserWeapon |
| **^ProjLightning** | LightningZap | electric arc | Tesla, TeslaCharged |
| **^ProjRailgun** | Railgun | helix beam | RailgunWeapon |
| **^ProjMelee** | InstantHit | — | SwordWeapon |
| **^ProjToxic** | InstantExplode | AffectsParent | ToxicWeapon |
| **^ProjMagic** | Missile | tailsman image, TrailImage | MagicWeapon |
| **^ProjBomb** | (gravity / none) | dropped, no own projectile | Shrapnel, HeavyBomb, Nuclear |
| **^ProjHealBeam** | LaserZap | SecondaryBeam, heal color | HealingWeapon, RepairWeapon |

**Open granularity choice:** L/M/H variants (Shell Inaccuracy, Missile turn-rate, Bullet
speed) as SEPARATE templates (`^ProjShellL/M/H`) vs ONE base + per-weapon override. Leaning
base + per-weapon override (fewer templates; the varying field is a single line).

## Layer 3 — EFFECT templates (proposed `^Fx*`)

Each bundles impact FX + the near-universal shield/concrete core + family smudge/specials, so
ONE `Inherits@fx:` gives a weapon its whole look. Distinct FX key-sets from the catalog:
`(Effect,ShieldHitEffect)`×9, `(Effect,EffectAir,EffectWater,ShieldHitEffect)`×5, etc.

| Proposed | Impact FX | Smudge | Specials (folded in) | From |
|---|---|---|---|---|
| **^FxBullet** | Effect + EffectWater | — | ShieldHit, Concrete | SmallArms, Chaingun, Flak, AA |
| **^FxCannon** | Effect + EffectAir + EffectWater | crater ×4 | ShieldHit, Concrete | Cannons |
| **^FxMissile** | Effect + EffectAir | crater | ShieldHit, Concrete | Missiles, Arrow |
| **^FxExplosion** | Effect + EffectWater | crater | ShieldHit, Concrete | Grenade, Shrapnel, HeavyBomb |
| **^FxFlame** | Effect | scorch | ShieldHit, **GroundFire, PhysicalState** | Flame×3 |
| **^FxChem** | Effect | — | ShieldHit, Concrete | Chemical×3 |
| **^FxLaser** | Effect + EffectAir | scorch | ShieldHit, Concrete | Laser |
| **^FxTesla** | ShieldHitEffect only | — | ShieldHit, **EMP** | Tesla×2 |
| **^FxRailgun** | Effect | — | ShieldHit, Concrete | Railgun |
| **^FxNuclear** | Effect + ShieldHitEffectNuclear | crater ×3 | ShieldHit, Concrete | Nuclear |
| **^FxMelee** | Effect | — | ShieldHit | Sword |
| **^FxMagic** | Effect | smudge | ShieldHit | Magic |

The **ExtraDamage** twin (Laser/Railgun/Tesla/Magic/Sniper — an OpenToppedDamage/SpreadDamage
+vs-shield chip) is a WARHEAD-layer concern (goes in the warhead template), NOT effect.

## Build plan (incremental, each boot-gated)

1. **[additive, 0-usage]** Generate the `^Projectile_*` + `^Effect_*` libraries into weapons.yaml above the
   divider (same low-risk pattern as the warhead splice). Boot-gate + commit. Nothing inherits
   them yet → no behavior change.
2. **[warhead layer]** Extend `gen_weapon_template.py`: FF twin for AoE families, ExtraDamage
   twin for energy families. Re-splice the warhead library. Boot-gate.
3. **[retrofit — the big batch]** Family-by-family, convert weapons from the old full-stack
   inherit to the 3-inherit model (`Inherits@wh`/`Inherits@proj`/`Inherits@fx`), rewriting
   `Warhead@<Old>` override keys to the new warhead key. Single-inherit mechanical families are
   done (`retrofit_weapon_family.py` reports 0 remaining); the rest is **285 mixed weapons in
   212 groups** (see `phase_b_survey.py`) collapsed to ≤2 warheads by dominant-damage choice.
   Resolver-diff + boot-gate per group.
4. **[cleanup]** Delete the 30 orphaned old templates; drop their `weapon_classes.yaml` rows.

## The 2-warhead cap + its EXCEPTION allow-list (maintainer 2026-08-02)

The kill-mixing pass reduces every weapon to **≤2 warhead inherits** — EXCEPT a
maintainer-curated allow-list of units kept multi-warhead for uniqueness. Retrofit
must NOT strip these. Known so far (more to be defined; confirm each before keeping):
- **Dune combat tanks** — Ixian combat tank / Koda tank / Ordos combat tank / **any D2k
  combat tank** = **3 cannon warheads** (Cannon Light + Medium + Heavy), their signature
  (vs the single Medium cannon of other medium tanks).
- **D2K Rocket Trooper family** (`D2K_Rocket_Trooper`, `D2K_Rocket_Trooper1`,
  `D2K_Rocket_Trooper2`, `D2K_Rocket_Trooper_AA`, `D2K_Rocket_Trooper_AGOnly`) —
  the resolved damage identity requires **three warhead layers** (Light/Medium/Heavy
  missile AP for the base and AA variants; Demolition + Railgun + Cannon for the
  Ixian/Ordos demolition variants). The 3-way split keeps these separate `Inherits@wh`
  entries; new per-weapon `^Projectile_*_D2K_Rocket_Trooper*` and
  `^Effect_MissileAP_Heavy_D2K_Rocket_Trooper` templates preserve the d2k_RPG
  projectile and Dune smudge/effect behaviour.
- **Ixian D2K missile weapons** (`D2K_TowerMissile`, `mtank_pri2`) — collapsed to a
  single `^D2KMissile` warhead identity with `Damage` overrides for the missile main
  and percentage twin; only the D2K-specific `^Projectile_Missile_Heavy_D2K_TowerMissile`,
  `^Projectile_Missile_Heavy_D2K_mtank_pri2`, `^Effect_MissileAP_Heavy_D2K_TowerMissile`,
  and `^Effect_MissileAP_Heavy_D2K_mtank_pri2` templates remain as custom projectile/
  effect layers.
- **Terran Siege Tank** (`SiegeTankSiegeCannon`) + **Warcraft Siege Engine**
  (`SiegeEngineCannon`) = keep ALL AoE warheads + others combined = a unique shared explosion.

Everything else: the 2-cap is strict. Build a concrete allow-list (unit/weapon ids) before
the kill-mixing pass. See.

## Retrofit specifics + weapon assignments (maintainer 2026-08-02)

- **Intermediate templates.** Some weapons inherit a per-faction INTERMEDIATE
  (`^RA2Chaingun` → `^Chaingun`, `^RA2SmallArms` → `^SmallArms`), not the base directly.
  The retrofit must repoint these intermediates too (or the concrete weapons under them),
  so the whole chain lands on the new families.
- **Bullet_Heavy → the Pulverizer mecha** (Asian Alliance). Today `AsianPulverizerGatling`
  / `AsianPulverizerMechaGatling` stitch `^HeavyCannon + ^SmallArms + ^RA2Chaingun`
  (+ Chem + Missile) — a MIXED weapon → **Phase B**. Collapse it to the clean heavy-bullet
  identity `^Bullet_Heavy` (a heavy gatling). Bullet_Heavy has no old-template source, so
  the Pulverizer is its intended first home.
- **Energy families** (Laser/Railgun/Tesla/Magic) = **small spread → single target**, and
  their upside is the **ExtraDamage chip vs shields** (50% of main, excluded from total).
  Large-AoE weapons have big spread and NO such chip — that is the intended trade.

## SPREAD REBALANCE — a future balance task (maintainer 2026-08-02, reason later)

Spreads are currently placeholders (generator: 400/600/800/1000 by level). New law to work
out later: **every weapon's spread must be UNIQUE, but balanced so `Damage × Spread ≈ constant`**
(an inverse trade — high-damage = tight spread, low-damage = wide spread). A weapon with a
**small spread MUST carry a unique extra effect** to justify it (energy's +vs-shield chip is
the model; a plain small-spread weapon is under-powered). Do NOT hand-tune spreads yet — this
is a dedicated pass folded into the restat. Tracked in ROADMAP.

## Naming — RESOLVED (maintainer 2026-08-02)

Layers are `^Projectile<Family>_<Level>` and `^Effect<Family>_<Level>` (spelled out, separate
L/M/H templates, zero per-weapon overrides). Both libraries are BUILT + committed (`0a6649039`).

---

# ═══ CONVERSION RUNBOOK — convert ALL weapons to the 3-inherit model ═══
_(maintainer-requested full plan, 2026-08-02. The other agent is halted; this is the single
authoritative path. One canonical retrofit tool; one family per commit; every step boot-gated.)_

## The invariants (never violated — these are what the v1 blind script broke)
1. **Structural only.** A retrofit renames inherits + warhead keys; it PRESERVES every existing
   on-grid `Damage` verbatim and invents no numbers. (2000-grid + FirepowerMultiplier = the restat.)
2. **≤2 warhead inherits** per weapon (the cap is on warheads). Direct-fire = 1; energy/upgrade = 2;
   the **exception allow-list** (Dune 3-cannon combat tanks; Terran Siege Tank + WC Siege Engine)
   is the ONLY place >2 is allowed.
3. **Exactly one** `@proj` and one `@fx` per weapon (except bombs = no `@proj`). >1 = the v1 bug.
4. **Single-inherit first; mixed weapons are Phase B** (per-weapon collapse, maintainer-directed).
5. Resolver-diff (structural) + audits + **boot-gate** + scoped commit **per family**.

## The master triple-map (old template → warhead / projectile / effect)
| Old | Warhead | Projectile | Effect | Notes |
|---|---|---|---|---|
| SmallArms | Bullet_Light | ProjectileBullet_Light | EffectBullet_Light | ✅ v3 |
| Chaingun | Bullet_Medium | ProjectileBullet_Medium | EffectBullet_Medium | ✅ v3 |
| TankDestroyerCannon | CannonAP_Light | ProjectileShell_Light | EffectCannon_Light | |
| MediumCannon | CannonHE_Medium | ProjectileShell_Medium | EffectCannon_Medium | |
| HeavyCannon | CannonHE_Heavy | ProjectileShell_Heavy | EffectCannon_Heavy | |
| LightMissile | MissileAP_Light | ProjectileMissile_Light | EffectMissile_Light | |
| MediumMissile | MissileAP_Medium | ProjectileMissile_Medium | EffectMissile_Medium | |
| HeavyMissile | MissileAP_Heavy | ProjectileMissile_Heavy | EffectMissile_Heavy | |
| FlakWeapon | Flak_Medium | ProjectileFlak_Medium | EffectFlak_Medium | |
| HeavyAAWeapon | MissileAA_Heavy | ProjectileFlak_Heavy | EffectFlak_Heavy | |
| LightFlameWeapon | Flame_Light | ProjectileFlame_Light | EffectFlame_Light | AoE (FF twin) |
| MediumFlameWeapon | Flame_Medium | ProjectileFlame_Medium | EffectFlame_Medium | AoE |
| HeavyFlameWeapon | Flame_Heavy | ProjectileFlame_Heavy | EffectFlame_Heavy | AoE |
| LightChemicalWeapon | Chemical_Light | ProjectileChem_Light | EffectChem_Light | AoE |
| MediumChemicalWeapon | Chemical_Medium | ProjectileChem_Medium | EffectChem_Medium | AoE |
| HeavyChemicalWeapon | Chemical_Heavy | ProjectileChem_Heavy | EffectChem_Heavy | AoE |
| Grenade | Demolition_Light | ProjectileGrenade_Light | EffectExplosion_Light | AoE |
| ShrapnelWeapon | Concussion_Medium | *(none — inline/lobbed)* | EffectExplosion_Medium | AoE, no proj |
| HeavyBomb | Demolition_Heavy | *(none — dropped)* | EffectExplosion_Heavy | AoE, no proj |
| NuclearWarhead | Nuclear_Super | *(none — dropped)* | EffectNuclear_Super | AoE, no proj |
| SwordWeapon | Melee_Medium | ProjectileMelee_Medium | EffectMelee_Medium | AoE |
| ArrowWeapon | Arrow_Light | ProjectileArrow_Light | EffectArrow_Light | |
| MagicWeapon | Magic_Heavy | ProjectileMagic_Heavy | EffectMagic_Heavy | %-equalizer |
| LaserWeapon | Laser_Heavy | ProjectileLaser_Heavy | EffectLaser_Heavy | **+ ExtraDamage** |
| RailgunWeapon | Railgun_Heavy | ProjectileRailgun_Heavy | EffectRailgun_Heavy | **+ ExtraDamage** |
| TeslaWeapon | Tesla_Heavy | ProjectileLightning_Heavy | EffectTesla_Heavy | **+ ExtraDamage + EMP** |
| TeslaChargedWeapon | TeslaCharged_Super | ProjectileLightning_Super | EffectTesla_Super | **+ ExtraDamage + EMP** |
| SniperWeapon / HealingWeapon / RepairWeapon | — STAY (special, not converted) | | | |
| ~~ToxicWeapon~~ | ✅ **CONVERTED 2026-08-15** — no longer stays. Maintainer ordered it built into the family system; it is now a thin child of `^Warhead_Toxic_Light` keeping only its own delivery (`ReloadDelay: 1`, `Spread: 333`, `AffectsParent`, `InstantExplode`). | | | |

**Intermediate templates** (a faction sub-template that inherits a base + overrides only
projectile/effect, never the warhead — e.g. `^RA2SmallArms`, `^RA2Chaingun`, `^RA2MG`, `^TSMG`,
`^SteelChaingun`, `^RA2FlakWeapon`): convert the intermediate itself to `@wh` (the base's new
warhead) + `@proj`/`@fx` = the STANDARD family layer, and fold its bespoke projectile/effect
overrides into the intermediate body (they merge by key). v3 already did this for the RA2 bullet
pair. Every concrete weapon under the intermediate then inherits it unchanged — no per-weapon edit.

## PHASE 0 — establish a clean, verified baseline  ← DO FIRST
- The v3 bullet retrofit sits UNCOMMITTED (130 weapons/templates, 0 conflicts, dual-inherit skipped).
- **Verify it as if it were mine:** resolver-diff a sample (structural only — same resolved damage);
  run audits (warhead_split, template_conformance, yaml_lint, weapon_uniqueness); **boot-gate**;
  spot-check every category (single SA, single CG, RA2 intermediate, a skipped dual/mixed weapon).
- If clean → **commit it** as "retrofit: Bullet family (SmallArms/Chaingun)". If any defect → fix or
  discard (my `stash@{0}` holds the v1; the v3 tooling is `tools/archive/retrofit_v3.py` — ⚠ **not in the tree**; the surviving canonical tool is `tools/balance/retrofit_weapon_family.py`).
- **Adopt ONE canonical retrofit tool** (`tools/balance/retrofit_weapon_family.py`, authored/owned by
  me) driven by the triple-map above + the categorizer, so every remaining family is done identically.

## PHASE 1 — finish the layer libraries (prerequisites for later families)
- **Energy ExtraDamage:** add the bespoke `Warhead@<fam>ExtraDamage` (+ `@EMPUnit` for Tesla) — kept
  per-weapon/per-family (Tesla = +vs-Shield/heavy, Laser = anti-shield-only). These are NOT uniform;
  extract verbatim into the Laser/Railgun/Tesla effect templates or a `^*ExtraDamage` warhead mixin.
- **New-level proj/fx with no old source** (Bullet_Heavy, CannonAP_Medium/Heavy, MissileHE*, Prism*,
  Sonic*): generate their projectile/effect by cloning the nearest family sibling; only needed once a
  real weapon targets that level (e.g. Bullet_Heavy for the Pulverizer in Phase B).

## PHASE 2 — single-inherit retrofit, FAMILY BY FAMILY (one commit each, boot-gated)
Order (safest/most-numerous first), ~437 weapons total:
1. ✅ Bullet (SmallArms 40 + Chaingun 26) — v3, Phase 0.
2. Cannon (TankDestroyer 6 → AP, MediumCannon 28 + HeavyCannon 13 → HE).
3. Missile (Light 12 + Medium 17 + Heavy 16 → AP) + Flak (11) + HeavyAA (2 → MissileAA).
4. Flame (L12/M20/H4) + Chemical (L5/M10/H7).  [AoE — FF twins]
5. Explosions: Grenade 13 → Demolition_Light, Shrapnel 12 → Concussion_Medium, HeavyBomb 16 →
   Demolition_Heavy (no `@proj`).
6. Melee (Sword 32) + Arrow (5) + Magic (3).
7. Energy (Laser 34, Railgun 17, Tesla 50, TeslaCharged 20) — needs Phase-1 ExtraDamage.
8. Nuclear (6, no `@proj`).
Per family: `retrofit_weapon_family.py --family X` (dry-run) → review → apply → resolver-diff →
audits → boot-gate → `git add <changed weapons.yaml> && commit "retrofit: <family>"`.

## PHASE 3 — mixed-weapon collapse (Phase B, ~609 weapons, maintainer-directed)
Each mixed weapon → ONE (or exception ≤2) warhead identity. NOT mechanical — a design call per weapon.
- Categorize by dominant role (the biggest-damage / defining warhead) → propose one family → you sign
  off in batches. Rewrite to the single-family 3-inherit form.
- **Exception allow-list kept:** Dune combat tanks = Cannon L+M+H (3); Terran Siege Tank
  (`SiegeTankSiegeCannon`) + WC Siege Engine (`SiegeEngineCannon`) = combined AoE; **Pulverizer**
  gatling → `Bullet_Medium`, **Pulverizer Mecha** → `Bullet_Heavy`.

## PHASE 4 — cleanup
When `grep -c 'Inherits.*\^<Old>'` = 0 for a family's old template, DELETE that `^Old:` block from
`weapons/weapons.yaml` + its `weapon_classes.yaml` row. Resolver-diff empty + boot-gate. Batch at the
end so partial retrofits keep booting.

## PHASE 5 — spread rebalance + DPS/range restat (the balance pipeline, now UNBLOCKED)
- **Spread rebalance:** `Damage × Spread ≈ constant`, unique per weapon, small-spread ⇒ unique effect.
- **Vehicle DPS/range restat:** now every unit is on its correct weapon family, so the deferred DPS
  half of the 2026-08-01 anchor table can be applied — `extract_stats` → `fit_class` → workbook →
  `apply_balance --confirm` (maintainer order) → boot. Unblocks ROADMAP #1.

## Guard rails (post-incident)
Single canonical tool; one family per commit (small, boot-gated, revertible); damage-preservation is
an invariant checked by resolver-diff; **each agent in its own git worktree/branch** (the durable fix
for the collision). Memory: `cameo-multi-agent-repo`, `cameo-weapon-structure-rules`.

---

# ═══ PROGRESS + RESUME (2026-08-03) ═══

**Done (each boot-gated + committed):** Bullet family (`126f44e87`), Report→projectile
(`3c7dd7477`), Cannon family + tool hardening (`bfc349bb7`). Tool = `retrofit_weapon_family.py`
(canonical). It now handles: intermediate closure (skip base+intermediate mixes), skipped-block
`-Warhead@<Old>` repair (converted-intermediate children like `DevBullet`→`^D2K_Cannon`),
ORDER-INDEPENDENT mixed-detection (closure seeded with NEW warheads so A+B mixes stay Phase B),
BOM-safe, Report in the PROJECTILE layer, damage always preserved.

D2K heavy missile/rocket HE 3-way split: created `ContentPacks/D2k/Shared/yaml/weapons.yaml`
with the per-game `^Projectile_Missile_Heavy_D2K` and `^Effect_MissileHE_Heavy_D2K` layers,
reparented the six D2K rocket cluster weapons to `^Warhead_MissileHE_Heavy`, and boot-gated;
followed by `^D2K_Cannon` repointed to the per-game `^Projectile_Shell_Medium_D2K` and
`^Effect_CannonHE_Medium_D2K` layers (preserving the d2k_120mm and d2k_small_napalm visuals);
then `^D2KRocket` and `^D2KMissile` migrated into the same D2K Shared pack as AP 3-way
split intermediates using `^Effect_MissileAP_Heavy_D2K` / `^Effect_MissileAP_Heavy_D2K_Rocket`;
finally the D2K `Debris` family moved its shrapnel bounce and demolition-effect overrides
into `^Projectile_Grenade_Light_D2K_Debris` and `^Effect_Demolition_Light_D2K`;
then the D2K 155mm family (D2K_155mm, D2K_155mm_turret, D2K_155mm3) moved its shared
`d2k_155mm` projectile and `d2k_med_explosion` effect into
`^Projectile_Grenade_Light_D2K_155mm` and `^Effect_Demolition_Heavy_D2K_155mm`;
then Dune_SiegeMortar moved its `d2k_155mm` Bullet and `d2k_large_explosion`
into `^Projectile_Shell_Light_D2K_Mortar` and `^Effect_CannonAP_Light_D2K_Mortar`;
then `D2K_Rocket` and `Fremen_RPG` moved their `d2k_rocket_explosion` effect
into `^Effect_MissileAP_Heavy_D2K_Rocket_Blast` and
`^Effect_MissileAP_Heavy_D2K_Missile_Blast` while keeping their custom
concrete and warhead stacks; then `oRocket` moved its `d2k_rocket_explosion`
effect into `^Effect_MissileAP_Heavy_D2K_Rocket_Blast`;
then `D2K_155mm2` moved its `d2k_155mm` grenade projectile and
`d2k_large_explosion` effect into `^Projectile_Grenade_Light_D2K_155mm`
and `^Effect_Demolition_Heavy_D2K_155mm2`;
then the legacy `^ORocket`/`^OMissile` intermediates and their children
(`oBazooka`, `oRocket`, `oTowerMissile`, `omtank_pri`, `oDeviatorMissile`)
were converted to 3-way split using new D2K Shared
`^Warhead_MissileAP_Heavy_D2K_ORocket`, `^Projectile_Missile_Heavy_D2K_ORocket`,
`^Projectile_Missile_Heavy_D2K_OMissile`, `^Effect_MissileAP_Heavy_D2K_ORocket`,
and `^Effect_MissileAP_Heavy_D2K_OMissile`, preserving the old `SpreadDamage`
warhead, projectile fields, effect stacks, concrete values, and smudge behaviour.

then `OrniBomb` and `OrniBombC` converted to 3-way split using D2K Shared `^Projectile_GravityBomb_D2K`, `^Warhead_Demolition_Heavy_D2K_Orni`, and `^Effect_Demolition_Heavy_D2K_Orni` (preserving the 7500 SpreadDamage warhead, d2k_bombs GravityBomb, Sand/Rock smudge, d2k_large_explosion, and 7500 concrete);
then `HeatRayBeam1/2/3/4` were fully 3-way split with `^Warhead_Inferno_Heavy` + `^Projectile_Inferno_Heavy_HeatRayBeam` + `^Effect_Inferno_Heavy` (per-weapon RadBeam projectile, small_napalm effect override preserved); resolver diff identical; boot-gated;
**RESUME — Phase 2 complete; Phase B mixed-weapon collapse remaining** (one commit each, maintainer-directed dominant-family choice):
`LightMissile,MediumMissile,HeavyMissile` + `FlakWeapon,HeavyAAWeapon` + `LightFlameWeapon,MediumFlameWeapon,HeavyFlameWeapon`
+ `LightChemicalWeapon,MediumChemicalWeapon,HeavyChemicalWeapon` + `Grenade,ShrapnelWeapon,HeavyBomb` +
`SwordWeapon,ArrowWeapon,MagicWeapon` + `NuclearWarhead` are now down to **zero single-inherit candidates**;
`retrofit_weapon_family.py` reports 285 mixed (Phase B) weapons in 212 groups. Use
`tools/audit/phase_b_survey.py` for the live work-list; the next group is at the top of
`docs/audit/latest/phase_b_survey.md`.

**ENERGY LAST** (Laser/Railgun/Tesla/TeslaCharged — BLOCKED on the ExtraDamage decision below).
Standard self-check after each: 0 orphaned old keys, 0 layer conflicts, 0 Damage changes, boots.

## OPEN DESIGN #1 — ExtraDamage rework (maintainer wants suggestions first)
ExtraDamage = the compensation energy weapons get for their very small spread (~100, single-target)
vs AoE weapons' large spread (multi-target). The current old-template values are ad-hoc (Tesla Shield
300/heavy-favoring; Laser Shield 100/else-1). Needs a principled scaling. **My 3 options:**
1. **Fixed-fraction + anti-shield concentration** — ExtraDamage = 50% of main (the DESIGN twin law),
   Versus concentrated on Shield. Simple; role = anti-shield; not tied to spread math.
2. **Spread-deficit scaling (most principled)** — reference spread = 400 ("1.0 area"); area ≈ (spread/400)²
   capped; ExtraDamage% = (1 − area) × K, concentrated on shields. A 100-spread weapon (~0.06 area) gets
   ~0.94K extra; a 400-spread gets ~0. Total effective output becomes spread-independent → "makes sense".
3. **Tiered (pragmatic)** — 3 spread bands → full / half / no ExtraDamage; concentrate on shields.
**Recommendation:** principle of #2, delivered via #3's tiers now (exact per-weapon spread formula is
the later rebalance). Energy weapons → tight spread (~100) + defined anti-shield ExtraDamage.

## OPEN DESIGN #2 — storage/loading architecture (maintainer, confirmed understanding)
- **Warheads = central/universal** (artwork-independent). Stay in `weapons/weapons.yaml`. ✓ where they are.
- **Projectiles + effects = per-game.** The GENERIC/classic ones (from the old central templates =
  TD+RA1 shared artwork: bullets, cannon shells, missiles+trails) stay in a **GLOBAL shared** location =
  they double as the **FALLBACK** effect/projectile for any faction without its own art yet. (So my
  current central `^Projectile*`/`^Effect*` library is CORRECT as the global fallback.)
- **Per-game overrides** (RA2 has its own piff/explosion; TS has unique effects, not wired yet) →
  that game's `Shared/yaml/`, loaded by the dynamic faction loader only when a faction of that game plays.
- **Faction-UNIQUE** projectile/effect → that faction's yaml (loaded only with that faction).
- Goal: load only what a lobby needs. **DEEP RESEARCH TODO:** map unit → weapon → projectile/trail/
  impact/sound (from the extracted OpenRA repo) to drive the relocation, and split the RA2-style
  intermediates into RA2-shared projectile+effect (warhead stays central).

## OPEN DESIGN #3 — full spread + falloff rebalance (LATER, maintainer)
`Damage × Spread ≈ constant`, unique spreads, small-spread ⇒ unique effect, + falloff-damage pass.
Deferred to after the retrofit; folds into the vehicle DPS restat (Phase 5).
