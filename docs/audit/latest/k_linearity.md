# audit_k_linearity — the flat K must not move when Damage moves

Analysed **2062** concrete weapons.

## L0 — every positive offensive runtime percentage application is modeled

_clean_ — modeled 2815 folded and 2538 standalone applications.

## L1 — `k_flat` is invariant under a change of flat Damage

_clean_ — `k_flat` held to within 1e-09 across 3 scalings of every weapon.

## L2 — the scalable/absolute split decomposes the published `k`

`k == k_flat + (pct_absolute + folded_rounding) / damage_total`. The standalone term is a floor; the folded term is the current runtime quantisation residual.

_clean_ — the identity holds for every analysed weapon; 11 percentage-only weapon(s) correctly have no flat-Damage denominator.

## L3 — weapons with a standalone percentage DPS floor

686 weapon(s) carry a standalone percentage hit; **91** have a floor at or above 25% of output.

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
| `TSTacticalMissileDamage` | 95.3% |
| `TSTacticalChemMissileDamage` | 95.3% |
| `TSHSeekerBomb` | 85.7% |
| `SteelTwisterMissiles_elite` | 81.2% |
| `Spit` | 78.8% |
| `SteelTwisterMissiles` | 78.4% |
| `PlasBullet` | 74.0% |
| `bowFire_AA` | 72.7% |
| `bowFire` | 72.7% |
| `wc_tower_fire` | 72.3% |
| `Spit_AA` | 69.1% |
| `LatinBuggyRocket_elite` | 67.6% |
| `wc2lightshipFire` | 67.0% |
| `wc2submarineFire` | 66.7% |
| `wc2tornadoTest` | 66.7% |
| `wc2daemonFire` | 66.7% |
| `wc2heavyshipFire` | 66.5% |
| `d2k_quake_thump` | 65.8% |
| `d2k_quake_boom` | 65.8% |

_... and 61 more._

## L4 — folded runtime quantisation residual

569 weapon(s) have a non-zero current folded runtime residual.
This residual is included in measured output but excluded from `k_flat` and `dps_floor`; recompute it after snapping a proposed Damage value.

| weapon | context-adjusted residual per shot |
|---|--:|
| `light_inf_lmg_ordos_upgrade` | +2.4263 |
| `AsianTurretPlasma` | +2.3815 |
| `AsianTwinPlasma_elite` | +2.1338 |
| `AsianTwinPlasma` | +2.0534 |
| `Tentacle` | +1.9923 |
| `RA2CosmonautLaser` | +1.9278 |
| `FutureMechPlasma_elite` | +1.9189 |
| `ThermobaricMaverick` | +1.9092 |
| `AsianSinglePlasma_elite` | +1.8926 |
| `CannonAttackRobotGun_elite` | +1.8830 |
| `CannonAttackRobotGun` | +1.8781 |
| `JHighVWaveforce` | +1.8624 |
| `FutureMechPlasma` | +1.8489 |
| `AsianSinglePlasma` | +1.8474 |
| `YakTeslaGun` | +1.8388 |
| `YakTeslaGunArc` | +1.8388 |
| `KamovTesla` | +1.8026 |
| `KamovTeslaArc` | +1.8026 |
| `BTRTeslaMachineGun` | +1.7782 |
| `BTRTeslaMachineGunArc` | +1.7782 |
| `JapanSpeedBoatGunWaveforce` | +1.7730 |
| `edenMobileDefenceLaser` | +1.7730 |
| `Napalm` | +1.7342 |
| `CabalMantisGun` | +1.7314 |
| `RA2LasherLaser` | +1.7303 |
| `AsianChemicalBombs` | +1.7042 |
| `TSTurretLaser` | +1.6728 |
| `TSCABALPlasmaFire` | +1.6728 |
| `d2kChainGun_upgrade` | +1.6695 |
| `RATurretGun` | +1.6680 |
