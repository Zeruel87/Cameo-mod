---
name: cluster-convert
description: "Convert a weapon cluster from old full-stack templates to the 3-way split"
argument-hint: "[family1+family2]"
triggers:
  - user
  - model
---

# Cluster-Convert — weapon 3-way split retrofit

This skill converts a group of weapons from old full-stack templates (`^SmallArms`,
`^Chaingun`, `^Grenade`, etc.) to the 3-way split model (`^Warhead_*` + `^Projectile_*`
+ `^Effect_*`).

## Pre-requisites (read before starting)

Load these docs into context first:
1. `docs/HANDOFF.md` -- current state, the priority queue, and the W24 cluster procedure
2. `docs/design/WEAPON_3WAY_SPLIT.md` -- the architecture
3. `docs/design/BALANCE_PROGRAM_PLAN.md` §1b -- the resolve-and-inline-FIRST procedure
4. `docs/LESSONS_LEARNED.md` -- the conversion traps (inherit position, removal markers,
   orphaned old keys, effect-warhead merges)

⚠ The two ARCHIVED handoffs this skill used to name
(`docs/history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md`,
`docs/history/handoffs/AI_HANDOFF_2026-08-05.md`) are provenance only. Their AreaDamage
conversion is COMPLETE and their "current state" is months stale -- read them for technique,
never for status.

Key rules:
- **Damage values are PRESERVED VERBATIM** -- never change a number
- **Main warhead type is `AreaDamage`** (or bare if inheriting `^Warhead_*`)
- **Never `SpreadDamage`** on new-family warheads (that's the old type)
- **2-warhead cap** on warheads (exceptions need maintainer sign-off)
- **Do NOT touch files the maintainer is editing** (check `docs/history/handoffs/AI_HANDOFF_2026-08-05.md` section 8)

## Conversion procedure

### 1. Identify the cluster
Run the phase_b_survey to find the next cluster:
```powershell
python tools/audit/phase_b_survey.py
```
Pick a cluster from the report (prefer larger groups for efficiency).

### 2. Determine the mapping
For each old template in the cluster, find the matching new family:
- `^SmallArms` -> `Bullet_Light`
- `^Chaingun` -> `Bullet_Medium`
- `^Grenade` -> `Demolition_Light`
- `^ShrapnelWeapon` -> `Concussion_Medium`
- `^HeavyBomb` -> `Demolition_Heavy`
- `^MediumCannon` -> `CannonHE_Medium`
- `^HeavyCannon` -> `CannonHE_Heavy`
- `^TankDestroyerCannon` -> `CannonAP_Light`
- `^LightMissile` -> `MissileAP_Light` or `MissileHE_Light`
- `^MediumMissile` -> `MissileAP_Medium` or `MissileHE_Medium`
- `^HeavyMissile` -> `MissileHE_Heavy` or `MissileAP_Heavy`
- `^FlakWeapon` -> `Flak_Medium`
- `^HeavyAAWeapon` -> `Flak_Heavy`
- `^LightFlameWeapon` -> `Flame_Light`
- `^MediumFlameWeapon` -> `Flame_Medium`
- `^HeavyFlameWeapon` -> `Flame_Heavy`
- `^LightChemicalWeapon` -> `Chemical_Light`
- `^MediumChemicalWeapon` -> `Chemical_Medium`
- `^HeavyChemicalWeapon` -> `Chemical_Heavy`
- `^LaserWeapon` -> `Laser_Heavy` (BLOCKED on ExtraDamage decision)
- `^RailgunWeapon` -> `Railgun_Heavy` (BLOCKED on ExtraDamage decision)
- `^TeslaWeapon` -> `Tesla_Heavy` (BLOCKED on ExtraDamage decision)
- `^SniperWeapon` -> `Sniper_Light`

### 3. Convert the weapons
For each weapon in the cluster:

**Replace old inherits:**
```yaml
# OLD:
SomeWeapon:
    Inherits: ^Grenade
    Inherits@2: ^HeavyMissile

# NEW:
SomeWeapon:
    Inherits@wh: ^Warhead_Demolition_Light
    Inherits@wh2: ^Warhead_MissileHE_Heavy
    Inherits@proj: ^Projectile_Missile_Heavy
    Inherits@fx: ^Effect_MissileHE_Heavy
```

**Rename warhead keys:**
```yaml
# OLD:
    Warhead@Grenade: SpreadDamage
        Damage: 4000
    Warhead@GrenadePercentage: HealthPercentageDamage
        Damage: 2

# NEW:
    Warhead@Demolition_Light:
        Damage: 4000
    Warhead@Demolition_Light_Percentage: HealthPercentageDamage
        Damage: 2
```

**Strip FriendlyFire twins** if the 50% ratio matches the baked FF in `^Warhead_*`.

**Keep addon inherits** (`^RA2Chaingun`, `^TSLaserEffect`, `^D2K_Cannon`, etc.)
after the new 3-way inherits so they continue to override projectile/effect.

**Preserve local overrides** (custom `Projectile:`, `Report:`, `Warhead@Effect`).

### 4. Post-conversion verification

Run ALL of these after every batch:

```powershell
# Empty warhead audit (must be 0)
python tools/audit/find_empty_warhead.py

# Orphaned old keys (must be 0 real)
python tools/audit/find_orphan_old_keys.py

# AreaDamage sweep (should report 0 candidates)
python tools/balance/sweep_areadamage.py

# Refresh ledgers
python tools/balance/extract_stats.py

# Boot-gate (invoke the boot-gate skill)
```

### 5. Handle children

After converting a parent weapon, grep all its children for OLD warhead keys:
```powershell
# Find children
Select-String -Path "mods\cameo\**\weapons.yaml" -Pattern "Inherits.*ConvertedParentName"
# Check each child for old keys like Warhead@OldKey
```
Rename any orphaned old keys in children to match the new convention.

### 6. Commit

Use scoped `git add`:
```powershell
git add <changed_files>
git commit -m "Phase B: collapse <Family1>+<Family2> group to <NewFamily>"
```
Never `git add -A` or `git add .`.
