# R13 missing-template reconciliation

**Read-only current-tree measurement. No YAML or generator output is changed.**

The current tree has three unmatched compatibility template definitions, sixteen direct template-weapon relationships, and fourteen distinct weapons. This reconciles the current count but does not prove what the historical wording meant. None of the three definitions is a standard family-level generator target.

Missing definitions: **3**; direct relationships: **16** across **14** distinct weapons; field/type-identical legacy payload already exists for **2**; standard family-level generator targets: **0**.

| compatibility template | direct relationships | renamed inner key | field/type-identical legacy provider | classification |
|---|---:|---|---|---|
| `^Compatibility_Laser_ExtraDamage` | 9 | `Warhead@LaserExtraDamage` | `^LaserWeapon` (identical) | `exact_auxiliary_payload_without_standalone_template` |
| `^Compatibility_Railgun_ExtraDamage` | 6 | `Warhead@RailgunExtraDamage` | `^RailgunWeapon` (identical) | `exact_auxiliary_payload_without_standalone_template` |
| `^Compatibility_TankBusterBeam_UnscopedFlat` | 1 | `Warhead@TankBusterBeamUnscoped` | none | `special_payload_without_standalone_template` |

## Direct users

### `^Compatibility_Laser_ExtraDamage`

- `DreadshroudSpore` — `mods/cameo/ContentPacks/StarCraft/Zerg/yaml/weapons.yaml`
- `HMG_Duelist_upgrade` — `mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml`
- `PhobosLaser` — `mods/cameo/ContentPacks/StarCraft/Terran/yaml/weapons.yaml`
- `ShtoraLaser` — `mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml`
- `SteelFighterRailgun` — `mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml`
- `TSCABALEnlightedLaser` — `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml`
- `TSCABALObeliskLaserFire` — `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml`
- `TSProton` — `mods/cameo/ContentPacks/TiberianSun/Nod/yaml/weapons.yaml`
- `wc2highArrowFire` — `mods/cameo/weapons/warcraft2.yaml`

### `^Compatibility_Railgun_ExtraDamage`

- `IxRailgunDroneBullet` — `mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml`
- `KodiakCannon` — `mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml`
- `PhobosLaser` — `mods/cameo/ContentPacks/StarCraft/Terran/yaml/weapons.yaml`
- `TS30mmRail` — `mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml`
- `TankBusterBeamCannon` — `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml`
- `wc2_dwarf_Rifle` — `mods/cameo/ContentPacks/Warcraft2/Humans/yaml/weapons.yaml`

### `^Compatibility_TankBusterBeam_UnscopedFlat`

- `TankBusterBeamCannon` — `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml`

## Decision boundary

Do not ask `gen_weapon_template.py` to emit sixteen family/level templates. The two extra-damage cases are exact auxiliary payloads embedded in legacy templates, and the TankBuster case is a one-user special slice. R13 must be composed with R12's per-user closure so the new standalone names do not preserve or create a second warhead inherit. Any writer still needs resolved field/order comparison and a cohort boot gate.
