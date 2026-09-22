# audit_k_linearity — the flat K must not move when Damage moves

Analysed **2128** concrete weapons.

## L0 — every positive offensive runtime percentage application is modeled

_clean_ — modeled 1690 folded and 2483 standalone applications.

## L1 — `k_flat` is invariant under a change of flat Damage

_clean_ — `k_flat` held to within 1e-09 across 3 scalings of every weapon.

## L2 — the scalable/absolute split decomposes the published `k`

`k == k_flat + (pct_absolute + folded_rounding) / damage_total`. The standalone term is a floor; the folded term is the current runtime quantisation residual.

_clean_ — the identity holds for every analysed weapon; 11 percentage-only weapon(s) correctly have no flat-Damage denominator.

## L3 — weapons with a standalone percentage DPS floor

692 weapon(s) carry a standalone percentage hit; **188** have a floor at or above 25% of output.

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
| `PhobosLaser` | 87.0% |
| `TSHSeekerBomb` | 85.7% |

_... and 158 more._

## L4 — folded runtime quantisation residual

575 weapon(s) have a non-zero current folded runtime residual.
This residual is included in measured output but excluded from `k_flat` and `dps_floor`; recompute it after snapping a proposed Damage value.

| weapon | context-adjusted residual per shot |
|---|--:|
| `AsianTurretPlasma` | +2.3815 |
| `AsianTwinPlasma_elite` | +2.1338 |
| `AsianTwinPlasma` | +2.0535 |
| `Tentacle` | +1.9922 |
| `FutureMechPlasma_elite` | +1.9190 |
| `ra1_soviets_migattackbomber_thermobaricmaverick` | +1.9091 |
| `AsianSinglePlasma_elite` | +1.8926 |
| `FutureMechPlasma` | +1.8489 |
| `AsianSinglePlasma` | +1.8474 |
| `ra1_soviets_teslayak_yakteslagun` | +1.8383 |
| `ra1_soviets_teslayak_yakteslagunarc` | +1.8383 |
| `ra1_soviets_kamovattackhelicopter_kamovtesla` | +1.8022 |
| `ra1_soviets_kamovattackhelicopter_kamovteslaarc` | +1.8022 |
| `ra1_soviets_btr80_machinegun_tesla` | +1.7778 |
| `ra1_soviets_btr80_machinegun_tesla_arc` | +1.7778 |
| `edenMobileDefenceLaser` | +1.7712 |
| `Napalm` | +1.7344 |
| `CabalMantisGun` | +1.7297 |
| `RA2LasherLaser` | +1.7285 |
| `AsianChemicalBombs` | +1.7038 |
| `TSTurretLaser` | +1.6711 |
| `TSCABALPlasmaFire` | +1.6711 |
| `d2kChainGun_upgrade` | +1.6678 |
| `ra1_allies_alliedgunturret_cannon` | +1.6677 |
| `schwarzermond_lunarsoldier_rifle_yellow` | +1.6551 |
| `schwarzermond_lunarsoldier_rifle_amplified` | +1.6551 |
| `NapalmA10Carrier` | +1.6477 |
| `TSLaserTurretLaser` | +1.6373 |
| `Lunar_YellowUbermenschLaser_elite` | +1.6248 |
| `Lunar_AmplifiedUbermenschLaser_elite` | +1.6248 |
