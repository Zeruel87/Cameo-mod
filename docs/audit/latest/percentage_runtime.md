# Folded percentage runtime audit

- Reachable direct-hit weapons activated: **186**
- Folded direct-hit applications activated: **296**
- Direct weapons also carrying standalone percentage hits: **7**
- Direct weapons whose folded hit feeds physical state: **7**
- Direct weapons whose folded hit feeds integrity: **5**
- Legacy Int32 overflow applications repaired: **7**
- Non-default direct relationship sets: **0**
- Dispatch structural findings: **0**

## Repaired overflow cases

| weapon | warhead | legacy units | repaired units |
|---|---|---:|---:|
| `DalekCannon` | `Railgun_HeavyFlatCompatibility` | -6474 | 15000 |
| `DalekCannon_elite` | `Railgun_HeavyFlatCompatibility` | 8525 | 30000 |
| `ExecutionerSword` | `Melee_Medium` | 8525 | 30000 |
| `Hakureiring2` | `Magic_Heavy` | -9474 | 12000 |
| `OIHakureiring2` | `Magic_Heavy` | -9474 | 12000 |
| `d2kStormLasher` | `Storm_Heavy` | -6474 | 15000 |
| `sandmarinemortar` | `Demolition_HeavyFlatCompatibility` | -9474 | 12000 |

## Direct-hit mixed effects

- Standalone plus folded: `RA2HeavyMirageGun`, `RA2HeavyMirageGun_elite`, `RA2MirageGun`, `RA2MirageGun_elite`, `SteelMegaSword_elite`, `Tentacle`, `WaveTurretImpact`
- Physical state: `ChainGunMH60Cryo`, `M60mgCryo`, `NaxDieGlocke`, `RAVulcanCryo`, `SheridanVulcanCryo`, `wc2deathknightDeathAndDecay_Hit`, `zsu_23Cryo`
- Integrity: `PsiStorm`, `RA2DiskDrain`, `TSSonicZapWeapon`, `WaveArtilleryImpact`, `WaveTurretImpact`

_PASS — the active rules contain no invalid or double-percentage shapes._
