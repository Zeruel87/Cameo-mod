# Folded percentage runtime audit

- Reachable direct-hit weapons activated: **195**
- Folded direct-hit applications activated: **198**
- Direct weapons also carrying standalone percentage hits: **7**
- Direct weapons whose folded hit feeds physical state: **7**
- Direct weapons whose folded hit feeds integrity: **5**
- Legacy Int32 overflow applications repaired: **8**
- Authored shared-mode (SharedVersus) applications: **23** (of which zero-unit: **19** — visibly listed, not counted as percentage hits)
- Non-default direct relationship sets: **0**
- Dispatch structural findings: **0**

## Repaired overflow cases

A repair is ONLY a legacy Int32 wrap independent of SharedVersus. The `runtime units` column shows the value actually applied today; for shared-mode rows it already carries the approved h/2 design scale (Scale itself moved 10000 -> 2000), so that column alone is NOT the before-migration value.

| weapon | warhead | legacy Int32 units | wide legacy units | runtime units |
|---|---|---:|---:|---:|
| `DalekCannon` | `Railgun_HeavyFlatCompatibility` | -6474 | 15000 | 15000 |
| `DalekCannon_elite` | `Railgun_HeavyFlatCompatibility` | 8525 | 30000 | 30000 |
| `ExecutionerSword` | `Melee_Medium` | 8525 | 30000 | 30000 |
| `Hakureiring2` | `Magic_Heavy` | -9474 | 12000 | 12000 |
| `OIHakureiring2` | `Magic_Heavy` | -9474 | 12000 | 12000 |
| `TSLocustBombChem` | `Chemical_Heavy` | -7974 | 13500 | 13500 |
| `d2kStormLasher` | `Storm_Heavy` | -6474 | 15000 | 15000 |
| `sandmarinemortar` | `Demolition_HeavyFlatCompatibility` | -9474 | 12000 | 12000 |

## Shared-mode inventory

Every authored reachable SharedVersus AreaDamage application, including zero-unit profiles. Zero-unit rows are authored configurations with no effective percentage hit, NOT activated percentage hits.

| weapon | warhead | h | Damage | Scale | shared runtime units |
|---|---|---:|---:|---:|---:|
| `120mm_cobra` | `CannonAP` | 0 | 120000 | 2000 | 0 |
| `120mm_cobra_deploy` | `CannonAP` | 0 | 120000 | 2000 | 0 |
| `120mm_python` | `CannonAP` | 0 | 120000 | 2000 | 0 |
| `120mm_python_deploy` | `CannonAP` | 0 | 120000 | 2000 | 0 |
| `AlliedTankDestroyerCannon` | `CannonAP` | 0 | 24000 | 2000 | 0 |
| `NaxiAntiTankCannon` | `CannonAP` | 0 | 28000 | 2000 | 0 |
| `NaxiAntiTankCannon_elite` | `CannonAP` | 0 | 28000 | 2000 | 0 |
| `NaxiHetzerDestroyer` | `CannonAP` | 0 | 40000 | 2000 | 0 |
| `NaxiHetzerDestroyer_elite` | `CannonAP` | 0 | 40000 | 2000 | 0 |
| `RA2120xmm` | `CannonAP` | 0 | 12000 | 2000 | 0 |
| `RA2120xmm_elite` | `CannonAP` | 0 | 12000 | 2000 | 0 |
| `RA2sabot` | `CannonAP` | 0 | 80000 | 2000 | 0 |
| `RA2sabot_elite` | `CannonAP` | 0 | 160000 | 2000 | 0 |
| `SkyHawkCannon` | `CannonAP` | 0 | 16000 | 2000 | 0 |
| `TS90mm` | `CannonAP` | 1000 | 6000 | 2000 | 30 |
| `TS90mmDep` | `CannonAP` | 1000 | 6000 | 2000 | 30 |
| `TSHighVelocity` | `CannonAP` | 0 | 30000 | 2000 | 0 |
| `TSHighVelocity2` | `CannonAP` | 0 | 40000 | 2000 | 0 |
| `TSHighVelocityTur` | `CannonAP` | 0 | 48000 | 2000 | 0 |
| `TSLaser90mm` | `CannonAP` | 1000 | 12000 | 2000 | 60 |
| `TSLaser90mmDep` | `CannonAP` | 1000 | 12000 | 2000 | 60 |
| `corrino_buggy_gun` | `CannonAP` | 0 | 3000 | 2000 | 0 |
| `ra1_allies_gunboat_cannon` | `CannonAP` | 0 | 30000 | 2000 | 0 |

## Zero-unit shared applications

- `120mm_cobra`:`CannonAP` (h=0, Damage=120000, Scale=2000) — shared units 0
- `120mm_cobra_deploy`:`CannonAP` (h=0, Damage=120000, Scale=2000) — shared units 0
- `120mm_python`:`CannonAP` (h=0, Damage=120000, Scale=2000) — shared units 0
- `120mm_python_deploy`:`CannonAP` (h=0, Damage=120000, Scale=2000) — shared units 0
- `AlliedTankDestroyerCannon`:`CannonAP` (h=0, Damage=24000, Scale=2000) — shared units 0
- `NaxiAntiTankCannon`:`CannonAP` (h=0, Damage=28000, Scale=2000) — shared units 0
- `NaxiAntiTankCannon_elite`:`CannonAP` (h=0, Damage=28000, Scale=2000) — shared units 0
- `NaxiHetzerDestroyer`:`CannonAP` (h=0, Damage=40000, Scale=2000) — shared units 0
- `NaxiHetzerDestroyer_elite`:`CannonAP` (h=0, Damage=40000, Scale=2000) — shared units 0
- `RA2120xmm`:`CannonAP` (h=0, Damage=12000, Scale=2000) — shared units 0
- `RA2120xmm_elite`:`CannonAP` (h=0, Damage=12000, Scale=2000) — shared units 0
- `RA2sabot`:`CannonAP` (h=0, Damage=80000, Scale=2000) — shared units 0
- `RA2sabot_elite`:`CannonAP` (h=0, Damage=160000, Scale=2000) — shared units 0
- `SkyHawkCannon`:`CannonAP` (h=0, Damage=16000, Scale=2000) — shared units 0
- `TSHighVelocity`:`CannonAP` (h=0, Damage=30000, Scale=2000) — shared units 0
- `TSHighVelocity2`:`CannonAP` (h=0, Damage=40000, Scale=2000) — shared units 0
- `TSHighVelocityTur`:`CannonAP` (h=0, Damage=48000, Scale=2000) — shared units 0
- `corrino_buggy_gun`:`CannonAP` (h=0, Damage=3000, Scale=2000) — shared units 0
- `ra1_allies_gunboat_cannon`:`CannonAP` (h=0, Damage=30000, Scale=2000) — shared units 0

## Direct-hit mixed effects

- Standalone plus folded: `RA2HeavyMirageGun`, `RA2HeavyMirageGun_elite`, `RA2MirageGun`, `RA2MirageGun_elite`, `SteelMegaSword_elite`, `Tentacle`, `WaveTurretImpact`
- Physical state: `NaxDieGlocke`, `ra1_allies_alliedaagun_flak_cryo`, `ra1_allies_blackhawk_chaingun_cryo`, `ra1_allies_machinegunner_machinegun_cryo`, `ra1_allies_ranger_machinegun_cryo`, `ra1_allies_sheridanassaulttank_chaingun_cryo`, `wc2deathknightDeathAndDecay_Hit`
- Integrity: `PsiStorm`, `RA2DiskDrain`, `TSSonicZapWeapon`, `WaveArtilleryImpact`, `WaveTurretImpact`

_PASS — the active rules contain no invalid or double-percentage shapes._
