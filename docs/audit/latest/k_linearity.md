# audit_k_linearity — the flat K must not move when Damage moves

Analysed **2039** concrete weapons.

## L0 — every positive offensive runtime percentage application is modeled

_clean_ — modeled 2184 folded and 2288 standalone applications.

## L1 — `k_flat` is invariant under a change of flat Damage

_clean_ — `k_flat` held to within 1e-09 across 3 scalings of every weapon.

## L2 — the scalable/absolute split decomposes the published `k`

`k == k_flat + (pct_absolute + folded_rounding) / damage_total`. The standalone term is a floor; the folded term is the current runtime quantisation residual.

_clean_ — the identity holds for every analysed weapon; 11 percentage-only weapon(s) correctly have no flat-Damage denominator.

## L3 — weapons with a standalone percentage DPS floor

651 weapon(s) carry a standalone percentage hit; **153** have a floor at or above 25% of output.

A price target below the floor is UNREACHABLE by lowering flat Damage — `required_damage()` returns None rather than a wrong positive number. To price these lower, the standalone percentage hit has to shrink.

| weapon | floor as share of output |
|---|--:|
| `DTMutate` | 100.0% |
| `MADTankThump` | 100.0% |
| `TSShadowTeamBomb` | 100.0% |
| `RA2Mutate` | 100.0% |
| `C4` | 100.0% |
| `WormSwallow` | 100.0% |
| `d2k_chaos_lightning` | 100.0% |
| `D2KGomJabbar` | 100.0% |
| `d2k_aircraft_eater` | 100.0% |
| `TSTacticalMissile` | 100.0% |
| `TSTacticalChemMissile` | 100.0% |
| `BlackEagleThunderboltMissiles_elite` | 97.7% |
| `BlackEagleThunderboltMissiles` | 97.6% |
| `TSTacticalMissileDamage` | 95.3% |
| `TSTacticalChemMissileDamage` | 95.3% |
| `RA2APCRocket_AA_elite` | 93.4% |
| `MigMissiles_elite` | 93.2% |
| `MigMissiles_fire_elite` | 93.2% |
| `MigMissiles_tesla_elite` | 93.2% |
| `RA2APCRocket_AA` | 93.2% |
| `MigMissiles` | 92.9% |
| `MigMissiles_fire` | 92.9% |
| `MigMissiles_tesla` | 92.9% |
| `RA2APCRocket_elite` | 92.6% |
| `RA2APCRocket` | 92.4% |
| `PhobosLaser` | 86.9% |
| `TSHSeekerBomb` | 85.7% |
| `LunarNaxiDroneMissile` | 85.3% |
| `SCTyrAA` | 84.1% |
| `D2K_RocketsCymek` | 84.1% |

_... and 123 more._

## L4 — folded runtime quantisation residual

382 weapon(s) have a non-zero current folded runtime residual.
This residual is included in measured output but excluded from `k_flat` and `dps_floor`; recompute it after snapping a proposed Damage value.

| weapon | context-adjusted residual per shot |
|---|--:|
| `FutureMechPlasma_elite` | +1.9195 |
| `ThermobaricMaverick` | +1.9116 |
| `FutureMechPlasma` | +1.8494 |
| `BTRTeslaMachineGun` | +1.7781 |
| `BTRTeslaMachineGunArc` | +1.7781 |
| `edenMobileDefenceLaser` | +1.7721 |
| `AsianChemicalBombs` | +1.7040 |
| `d2kChainGun_upgrade` | +1.6687 |
| `NapalmA10Carrier` | +1.6493 |
| `TSLasergun` | +1.5857 |
| `TSLaserHarpyClaw` | +1.5849 |
| `TSLaserHarpyAOEClaw` | +1.5849 |
| `JHighVWaveforce` | +1.5743 |
| `BTRTeslaMachineGunArcFragment1` | +1.5713 |
| `NambuMGWaveforce` | +1.5681 |
| `LMG_ordos_upgrade` | +1.5489 |
| `light_inf_lmg_ordos_upgrade` | +1.5388 |
| `CabalOverkillDroneLaser` | +1.5246 |
| `d2kCarryallChainGun_upgrade` | +1.5180 |
| `12MissilesSpawnerScud` | -1.5170 |
| `JapanSpeedBoatGunWaveforce` | +1.4667 |
| `RA2120xmm_elite` | +1.4649 |
| `RA2120xmm_fire_elite` | +1.4649 |
| `RA2120xmm_tesla_elite` | +1.4649 |
| `tkmbunkmg` | +1.4463 |
| `RA2120xmm` | +1.4429 |
| `RA2120xmm_fire` | +1.4429 |
| `RA2120xmm_tesla` | +1.4429 |
| `AsianGrenade_elite` | +1.4078 |
| `RA2NarcoAKM_elite` | +1.4068 |
