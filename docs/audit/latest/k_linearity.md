# audit_k_linearity — the flat K must not move when Damage moves

Analysed **2061** concrete weapons.

## L0 — every positive offensive runtime percentage application is modeled

_clean_ — modeled 1689 folded and 2441 standalone applications.

## L1 — `k_flat` is invariant under a change of flat Damage

_clean_ — `k_flat` held to within 1e-09 across 3 scalings of every weapon.

## L2 — the scalable/absolute split decomposes the published `k`

`k == k_flat + (pct_absolute + folded_rounding) / damage_total`. The standalone term is a floor; the folded term is the current runtime quantisation residual.

_clean_ — the identity holds for every analysed weapon; 11 percentage-only weapon(s) correctly have no flat-Damage denominator.

## L3 — weapons with a standalone percentage DPS floor

681 weapon(s) carry a standalone percentage hit; **185** have a floor at or above 25% of output.

A price target below the floor is UNREACHABLE by lowering flat Damage — `required_damage()` returns None rather than a wrong positive number. To price these lower, the standalone percentage hit has to shrink.

| weapon | floor as share of output |
|---|--:|
| `DTMutate` | 100.0% |
| `MADTankThump` | 100.0% |
| `TSShadowTeamBomb` | 100.0% |
| `RA2Mutate` | 100.0% |
| `WormSwallow` | 100.0% |
| `D2KGomJabbar` | 100.0% |
| `d2k_aircraft_eater` | 100.0% |
| `C4` | 100.0% |
| `d2k_chaos_lightning` | 100.0% |
| `TSTacticalMissile` | 100.0% |
| `TSTacticalChemMissile` | 100.0% |
| `BlackEagleThunderboltMissiles_elite` | 97.7% |
| `BlackEagleThunderboltMissiles` | 97.6% |
| `TSTacticalMissileDamage` | 95.3% |
| `TSTacticalChemMissileDamage` | 95.3% |
| `RA2APCRocket_AA_elite` | 93.4% |
| `NaxiMissileUboat` | 93.2% |
| `MigMissiles_elite` | 93.2% |
| `MigMissiles_fire_elite` | 93.2% |
| `MigMissiles_tesla_elite` | 93.2% |
| `RA2APCRocket_AA` | 93.2% |
| `BlackEagleMissiles` | 93.0% |
| `BlackEagleMissiles_elite` | 93.0% |
| `MigMissiles` | 92.9% |
| `MigMissiles_fire` | 92.9% |
| `MigMissiles_tesla` | 92.9% |
| `RA2APCRocket_elite` | 92.6% |
| `RA2APCRocket` | 92.4% |
| `PhobosLaser` | 86.9% |
| `TSHSeekerBomb` | 85.7% |

_... and 155 more._

## L4 — folded runtime quantisation residual

561 weapon(s) have a non-zero current folded runtime residual.
This residual is included in measured output but excluded from `k_flat` and `dps_floor`; recompute it after snapping a proposed Damage value.

| weapon | context-adjusted residual per shot |
|---|--:|
| `AsianTurretPlasma` | +2.3819 |
| `AsianTwinPlasma_elite` | +2.1341 |
| `AsianTwinPlasma` | +2.0538 |
| `Tentacle` | +1.9921 |
| `FutureMechPlasma_elite` | +1.9192 |
| `ThermobaricMaverick` | +1.9088 |
| `AsianSinglePlasma_elite` | +1.8929 |
| `FutureMechPlasma` | +1.8492 |
| `AsianSinglePlasma` | +1.8477 |
| `YakTeslaGun` | +1.8392 |
| `YakTeslaGunArc` | +1.8392 |
| `KamovTesla` | +1.8031 |
| `KamovTeslaArc` | +1.8031 |
| `BTRTeslaMachineGun` | +1.7787 |
| `BTRTeslaMachineGunArc` | +1.7787 |
| `edenMobileDefenceLaser` | +1.7736 |
| `Napalm` | +1.7341 |
| `CabalMantisGun` | +1.7321 |
| `RA2LasherLaser` | +1.7309 |
| `AsianChemicalBombs` | +1.7046 |
| `TSTurretLaser` | +1.6734 |
| `TSCABALPlasmaFire` | +1.6734 |
| `d2kChainGun_upgrade` | +1.6701 |
| `RATurretGun` | +1.6673 |
| `schwarzermond_lunarsoldier_rifle_yellow` | +1.6574 |
| `schwarzermond_lunarsoldier_rifle_amplified` | +1.6574 |
| `NapalmA10Carrier` | +1.6474 |
| `TSLaserTurretLaser` | +1.6396 |
| `Lunar_YellowUbermenschLaser_elite` | +1.6270 |
| `Lunar_AmplifiedUbermenschLaser_elite` | +1.6270 |
