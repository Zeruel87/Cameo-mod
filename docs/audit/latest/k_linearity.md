# audit_k_linearity — the flat K must not move when Damage moves

Analysed **2191** concrete weapons.

## L0 — every positive offensive runtime percentage application is modeled

_clean_ — modeled 1607 folded and 2529 standalone applications.

## L1 — `k_flat` is invariant under a change of flat Damage

_clean_ — `k_flat` held to within 1e-09 across 3 scalings of every weapon.

## L2 — the scalable/absolute split decomposes the published `k`

`k == k_flat + (pct_absolute + folded_rounding) / damage_total`. The standalone term is a floor; the folded term is the current runtime quantisation residual.

_clean_ — the identity holds for every analysed weapon; 11 percentage-only weapon(s) correctly have no flat-Damage denominator.

## L3 — weapons with a standalone percentage DPS floor

706 weapon(s) carry a standalone percentage hit; **185** have a floor at or above 25% of output.

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
| `BlackEagleThunderboltMissiles` | 97.7% |
| `TSTacticalMissileDamage` | 95.3% |
| `TSTacticalChemMissileDamage` | 95.3% |
| `NaxiMissileUboat` | 93.3% |
| `BlackEagleMissiles` | 93.1% |
| `BlackEagleMissiles_elite` | 93.1% |
| `RocketAngelRockets` | 88.7% |
| `PhobosLaser` | 87.2% |
| `TSHSeekerBomb` | 85.7% |
| `LunarNaxiDroneMissile` | 85.3% |
| `HarrierMissiles_elite` | 84.0% |
| `BallistaSingleShotAirEnergized_AA` | 83.7% |
| `SCTyrAA` | 83.1% |
| `D2K_RocketsCymek` | 83.0% |
| `120mm_python_deploy` | 83.0% |
| `BallistaMultiShotEnergized` | 82.4% |
| `120mm_cobra_deploy` | 82.0% |
| `BallistaTowerMultiShotEnergized` | 81.8% |

_... and 155 more._

## L4 — folded runtime quantisation residual

635 weapon(s) have a non-zero current folded runtime residual.
This residual is included in measured output but excluded from `k_flat` and `dps_floor`; recompute it after snapping a proposed Damage value.

| weapon | context-adjusted residual per shot |
|---|--:|
| `AsianTurretPlasma` | +2.4157 |
| `AsianTwinPlasma_elite` | +2.1578 |
| `AsianTwinPlasma` | +2.0748 |
| `Tentacle` | +2.0190 |
| `ra1_soviets_migattackbomber_thermobaricmaverick` | +1.9411 |
| `FutureMechPlasma_elite` | +1.9392 |
| `AsianSinglePlasma_elite` | +1.9091 |
| `FutureMechPlasma` | +1.8669 |
| `AsianSinglePlasma` | +1.8624 |
| `ra1_soviets_btr80_machinegun_tesla` | +1.7793 |
| `ra1_soviets_btr80_machinegun_tesla_arc` | +1.7793 |
| `Napalm` | +1.7554 |
| `CabalMantisGun` | +1.7163 |
| `RA2LasherLaser` | +1.7151 |
| `AsianChemicalBombs` | +1.6999 |
| `ra1_allies_alliedgunturret_cannon` | +1.6910 |
| `NapalmA10Carrier` | +1.6654 |
| `TSTurretLaser` | +1.6573 |
| `TSCABALPlasmaFire` | +1.6573 |
| `d2kChainGun_upgrade` | +1.6536 |
| `edenMobileDefenceLaser` | -1.6514 |
| `schwarzermond_lunarsoldier_rifle_yellow` | +1.6407 |
| `schwarzermond_lunarsoldier_rifle_amplified` | +1.6407 |
| `TSLaserTurretLaser` | +1.6245 |
| `schwarzermond_lunarsoldier_rifle_yellow_elite` | +1.6058 |
| `schwarzermond_lunarsoldier_rifle_amplified_elite` | +1.6058 |
| `TSScoopDualTur` | +1.5973 |
| `JHighVWaveforce` | +1.5823 |
| `NambuMGWaveforce` | +1.5737 |
| `TSLaserHarpyClaw` | +1.5687 |
