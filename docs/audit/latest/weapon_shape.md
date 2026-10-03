# Weapon shape — the ONE-WARHEAD / THREE-INHERIT law

**Maintainer ruling, 2026-09-06.** Every concrete weapon ends with exactly three inherits — `^Warhead_*`, `^Projectile_*`, `^Effect_*` — one main warhead, and no effect warheads of its own. Mechanic warheads (`FireShrapnel`, `GrantExternalCondition`) and the `*Percentage` / `*FriendlyFire` / `*ExtraDamage` halves of one main are NOT violations.

⛔ This **repeals the exemption** in `tools/audit/intentional_composites.py`. Its 224 entries are no longer 'reviewed, keep' — they are the worklist. The registry data stays useful: it says which mains someone chose on purpose.

concrete weapons with inherits: **2168**

W5 counts structural flat-damage nodes, including zero/healing/ally-only nodes; the split audit counts positive non-companion damage. Both resolve the full concrete weapon corpus. Use `--compare-split` for exact differences.

| check | what | count | ratchet |
|---|---|--:|--:|
| W1 | more than 3 inherits | **343** (15.83% of 2168) | 15.98% |
| W2 | two or more `^Warhead_*` inherits | **84** ⛔ | 83 |
| W3 | two or more `^Projectile_*` inherits | **29** | 29 |
| W4 | two or more `^Effect_*` inherits | **167** ⛔ | 166 |
| W5 | more than one resolved MAIN warhead | **154** ⛔ | 153 |
| W6 | effect warheads declared LOCALLY | **401** ⛔ | 394 |
| W7 | inherits from ANOTHER WEAPON, not a template | **420** ⛔ | 403 |
| W8 | inherits a `^Template` that is not one of the three kinds | **313** ⛔ | 305 |

| I7 informational — missing template | weapons |
|---|--:|
| no `^Effect_*` inherit | 471 |
| no `^Projectile_*` inherit | 937 |
| no `^Warhead_*` inherit | 602 |

_I7 is a REVIEW QUEUE, not a defect count — an instant or utility weapon may legitimately have no projectile. Do not ratchet it without a per-weapon pass._


## W7 — inherits from ANOTHER WEAPON, not a template (420 vs ratchet 403)

| weapon | weapon-parents | first four |
|---|---|---|
| `155mmCryo` | 1 | `155mm` |
| `25mmWaveforce` | 1 | `25mm` |
| `AAGunBoatFlak_elite` | 1 | `AAGunBoatFlak` |
| `ASDFGun2` | 1 | `ASDFGun` |
| `ArbiterCannon` | 1 | `PhotonCannon` |
| `ArmoredCarMGAAWaveforce` | 1 | `ArmoredCarMG_AA` |
| `ArmoredCarMGWaveforce` | 1 | `ArmoredCarMG` |
| `ArmoredCarMG_AA` | 1 | `ArmoredCarMG` |
| `ArtilleryExplode` | 1 | `155mm` |
| `AsianChaosMine` | 1 | `AsianTankMine` |
| `AsianChemical_elite` | 1 | `AsianChemical` |
| `AsianGrenade_elite` | 1 | `AsianGrenade` |
| `AsianLynxMG_elite` | 1 | `AsianLynxMG` |
| `AsianLynxTankCannon_elite` | 1 | `AsianLynxTankCannon` |
| `AsianPelicanMG_elite` | 1 | `AsianPelicanMG` |
| `AsianPelicanMissile_elite` | 1 | `AsianPelicanMissile` |
| `AsianPhoenixRocket_elite` | 1 | `AsianPhoenixRocket` |
| `AsianPhotonCannon_EMP` | 1 | `AsianPhotonCannon` |
| `AsianPulverizerMechaGatling` | 1 | `AsianPulverizerGatling` |
| `AsianPunisherAG_EMP` | 1 | `AsianPunisherAG` |
| `AsianQuasarAG` | 1 | `AsianPhotonCannon` |
| `AsianQuasarAG_EMP` | 1 | `AsianQuasarAG` |
| `AsianQuasarBoatAG` | 1 | `AsianPhotonCannon` |
| `AsianQuasarBoatAG_EMP` | 1 | `AsianQuasarBoatAG` |
| `AsianQuasarBoat_AA` | 1 | `AsianPhotonCannon` |
| `AsianQuasarBoat_EMP_AA` | 1 | `AsianQuasarBoat_AA` |
| `AsianQuasar_AA` | 1 | `AsianPhotonCannon` |
| `AsianQuasar_EMP_AA` | 1 | `AsianQuasar_AA` |
| `AsianSniperAP` | 1 | `AsianSniper` |
| `AsianSniperLockdown` | 1 | `AsianSniperAP` |
| `AsianSpitfireRockets` | 1 | `AsianMLRS` |
| `AsianTSIonCannon` | 1 | `IonCannon` |
| `AsianTwinPlasma_elite` | 1 | `AsianTwinPlasma` |
| `BCYamatoCannon` | 1 | `BCLaser` |
| `BallistaSingleShotAirEnergized_AA` | 1 | `JapanMaidenBowEnergized` |
| `BallistaTowerMultiShot` | 1 | `BallistaMultiShot` |
| `BallistaTowerMultiShotEnergized` | 1 | `BallistaMultiShotEnergized` |
| `BlackEagleMissiles_elite` | 1 | `BlackEagleMissiles` |
| `BlackEagleThunderboltMissiles_elite` | 1 | `BlackEagleThunderboltMissiles` |
| `ChemTibAtomic` | 1 | `Atomic` |


_... and 380 more._


## W8 — inherits a `^Template` that is not one of the three kinds (313 vs ratchet 305)

| weapon | legacy templates | first four |
|---|---|---|
| `AnthraxCloud` | 1 | `^ToxicWeapon` |
| `AsianPhotonCannon` | 1 | `^TeslaWeapon` |
| `AthenaLaser` | 2 | `^TeslaWeapon` · `^LaserWeapon` |
| `Atomic` | 1 | `^AtomicCore` |
| `AtreusMG` | 4 | `^Grenade` · `^MediumMissile` · `^FlakWeapon` · `^SCRA2Chaingun` |
| `BCLaser` | 4 | `^NuclearWarhead` · `^RailgunWeapon` · `^HeavyBomb` · `^LaserWeapon` |
| `BHBombs` | 1 | `^FlameWeapon` |
| `BallistaMultiShotEnergized` | 1 | `^TeslaWeapon` |
| `BehemothShoot` | 6 | `^LightFlameWeapon` · `^MediumChemicalWeapon` · `^HeavyMissile` · `^Grenade` |
| `BigChemSpray` | 1 | `^FlameWeapon` |
| `BoatMissile` | 1 | `^MissileWeapon` |
| `BroodweaverLeech` | 1 | `^HealingWeapon` |
| `BuildingExplode` | 1 | `^DamagingExplosionHE` |
| `CabalArtilleryWalkerShellUpgraded` | 2 | `^TeslaChargedWeapon` · `^RailgunWeapon` |
| `CabalAscendedRockets` | 1 | `^CabalMissileMedium` |
| `CabalBeholderLaser` | 3 | `^TeslaWeapon` · `^RailgunWeapon` · `^LaserWeapon` |
| `CabalCommandoPlasma` | 3 | `^HeavyCannon` · `^MediumFlameWeapon` · `^MediumChemicalWeapon` |
| `CabalCommandoPlasmaMk2` | 3 | `^HeavyCannon` · `^MediumFlameWeapon` · `^MediumChemicalWeapon` |
| `CabalCommandoPlasmaMk2Neutron` | 5 | `^HeavyCannon` · `^MediumFlameWeapon` · `^TeslaWeapon` · `^MagicWeapon` |
| `CabalCommandoPlasmaNeutron` | 5 | `^HeavyCannon` · `^MediumFlameWeapon` · `^TeslaWeapon` · `^MagicWeapon` |
| `CabalEngineerRepairBeam` | 1 | `^RepairWeapon` |
| `CabalHunterKillerLasers` | 1 | `^LaserWeapon` |
| `CabalHunterKillerLasers_elite` | 2 | `^LaserWeapon` · `^RailgunWeapon` |
| `CabalManticoreMissiles_AA` | 1 | `^CabalManticoreMissiles` |
| `CabalMothershipRockets` | 4 | `^TeslaWeapon` · `^HeavyMissile` · `^MediumFlameWeapon` · `^Grenade` |
| `CabalSubmarinePlasma` | 3 | `^HeavyCannon` · `^MediumFlameWeapon` · `^MediumChemicalWeapon` |
| `Claw` | 1 | `^DinoWeapon` |
| `ConsortiumMissileSystem` | 1 | `^TeslaWeapon` |
| `CryoLegionnaireAttack` | 2 | `^TeslaWeapon` · `^LaserWeapon` |
| `D2KRepair` | 1 | `^HealingWeapon` |
| `D2KUnitExplodeLarge` | 1 | `^DamagingExplosionHE` |
| `D2KUnitExplodeMed` | 1 | `^DamagingExplosion` |
| `D2KUnitExplodeSmall` | 1 | `^Explosion` |
| `D2K_155mm` | 1 | `^D2K155mmLegacy` |
| `D2K_155mm2` | 3 | `^MediumFlameWeapon` · `^ShrapnelWeapon` · `^HeavyBomb` |
| `D2K_SiegeQuad` | 1 | `^D2K155mmLegacy` |
| `D2K_TowerMissile` | 1 | `^D2KMissile` |
| `D2kBuildingExplode` | 1 | `^DamagingExplosionHE` |
| `DRPlasmaTankWeapon` | 1 | `^DRPlasmaWeapon` |
| `DefuseKit` | 2 | `^RemovesIvanBombs` · `^RemovesTerrorDrone` |


_... and 273 more._


## W1 — more than 3 inherits (343 vs ratchet 576)

| weapon | inherits | first four |
|---|---|---|
| `110mm_Gun` | 5 | `^Warhead_CannonAP_Light_Flat` · `^Projectile_Shell_Heavy` · `^Effect_CannonAP_Light` · `^Projectile_Shell_Medium_D2K` |
| `120mm_cobra` | 5 | `^Warhead_CannonAP` · `^Projectile_Shell_Light` · `^Effect_CannonAP_Light` · `^Projectile_Shell_Medium_D2K` |
| `120mm_td` | 4 | `^Warhead_CannonHE_Medium` · `^Projectile_Shell_Medium_D2K` · `^Effect_CannonHE_Medium_D2K` · `^d2k_ordos_120mm_td` |
| `25mmWaveforce` | 4 | `^Warhead_Railgun_Heavy` · `^Projectile_Railgun_Heavy` · `^Effect_Railgun_Heavy` · `25mm` |
| `AAGunBoatFlak` | 5 | `^Warhead_Flak_Medium` · `^Projectile_Flak_Medium` · `^Effect_Flak_Puff_RA2` · `^Effect_Watersplash_Small_RA2` |
| `ASDFGun2` | 4 | `^Warhead_Railgun_Heavy` · `^Projectile_Railgun_Heavy` · `^Effect_Railgun_Heavy` · `ASDFGun` |
| `ArmoredCarMGAAWaveforce` | 4 | `^Warhead_Railgun_Heavy` · `^Projectile_Railgun_Heavy` · `^Effect_AlliedTigerCannon` · `ArmoredCarMG_AA` |
| `ArmoredCarMGWaveforce` | 4 | `^Warhead_Railgun_Heavy` · `^Projectile_Railgun_Heavy` · `^Effect_AlliedTigerCannon` · `ArmoredCarMG` |
| `ArtilleryShell` | 5 | `^Warhead_Concussion_Medium_Flat` · `^Warhead_Demolition_Light` · `^Warhead_Concussion_Medium` · `^Projectile_Grenade_Light` |
| `AsianChaosMine` | 4 | `AsianTankMine` · `^Warhead_Chemical_Heavy` · `^Projectile_Chem_Heavy` · `^Effect_Chem_Heavy` |
| `AsianLynxTankCannon` | 4 | `^Warhead_CannonHE_Medium` · `^Projectile_Shell_Medium` · `^Effect_AlliedTigerCannon` · `^Effect_Flame_Heavy` |
| `AsianSinglePlasma` | 4 | `^Warhead_CannonHE_Heavy` · `^Projectile_Shell_Heavy` · `^Effect_Apoc_AP_RA2` · `^Effect_Flame_Heavy` |
| `AsianSinglePlasma_elite` | 4 | `^Warhead_CannonHE_Heavy` · `^Projectile_Shell_Heavy` · `^Effect_Apoc_AP_RA2` · `^Effect_Flame_Heavy` |
| `AsianSniperLockdown` | 4 | `^Warhead_Tesla_Super` · `^Projectile_Lightning_Super` · `^Effect_Tesla_Super` · `AsianSniperAP` |
| `AsianTurretPlasma` | 5 | `^Warhead_CannonHE_Heavy` · `^Projectile_Shell_Heavy` · `^Effect_Apoc_AP_RA2` · `^Effect_Flame_Heavy` |
| `AsianTwinPlasma` | 4 | `^Warhead_CannonHE_Heavy` · `^Projectile_Shell_Heavy` · `^Effect_Apoc_AP_RA2` · `^Effect_Flame_Heavy` |
| `AtreusMG` | 8 | `^Warhead_CannonHE_Heavy` · `^Projectile_Shell_Heavy` · `^Effect_CannonHE_Heavy` · `^Grenade` |
| `BCLaser` | 8 | `^Warhead_Laser_Heavy_Flat` · `^Warhead_CannonHE_Heavy` · `^Projectile_Shell_Heavy` · `^Effect_CannonHE_Heavy` |
| `BallistaSingleShotAirEnergized_AA` | 4 | `^Warhead_MissileAP_Light` · `^Projectile_Missile_Light` · `^Effect_MissileAP_Light` · `JapanMaidenBowEnergized` |
| `BehemothShoot` | 8 | `^Warhead_MissileHE_Heavy` · `^LightFlameWeapon` · `^MediumChemicalWeapon` · `^HeavyMissile` |
| `BuggyPlasmaGrenade` | 4 | `^Warhead_Plasma_Light` · `^Warhead_Demolition_Light` · `^Projectile_Grenade_Light` · `^Effect_Demolition_Light` |
| `CabalArtilleryWalkerShellUpgraded` | 4 | `^Warhead_CannonHE_Heavy_Flat` · `^TeslaChargedWeapon` · `^RailgunWeapon` · `^ts_cabal_cabalartillerywalkershellupgraded` |
| `CabalBeholderLaser` | 5 | `^Warhead_Laser_Heavy_Flat` · `^TeslaWeapon` · `^RailgunWeapon` · `^LaserWeapon` |
| `CabalCommandoPlasma` | 5 | `^Warhead_Plasma_Heavy` · `^HeavyCannon` · `^MediumFlameWeapon` · `^MediumChemicalWeapon` |
| `CabalCommandoPlasmaMk2` | 5 | `^Warhead_Plasma_Heavy` · `^HeavyCannon` · `^MediumFlameWeapon` · `^MediumChemicalWeapon` |
| `CabalCommandoPlasmaMk2Neutron` | 7 | `^Warhead_Plasma_Heavy_Flat` · `^HeavyCannon` · `^MediumFlameWeapon` · `^TeslaWeapon` |
| `CabalCommandoPlasmaNeutron` | 7 | `^Warhead_Plasma_Heavy_Flat` · `^HeavyCannon` · `^MediumFlameWeapon` · `^TeslaWeapon` |
| `CabalHunterKillerLasers_elite` | 4 | `^Warhead_Laser_Heavy` · `^LaserWeapon` · `^RailgunWeapon` · `^ts_cabal_cabalhunterkillerlasers_elite` |
| `CabalLegionGun` | 4 | `^Warhead_Laser_Heavy_Flat` · `^Warhead_Laser_Heavy` · `^Projectile_Bullet_Light` · `^ts_cabal_set8` |
| `CabalMagicNuke` | 4 | `^Warhead_Tesla_Heavy` · `^Warhead_Tesla_Super` · `^Projectile_Lightning_Super` · `^ts_cabal_cabalmagicnuke` |
| `CabalMantisGun` | 4 | `^Warhead_Laser_Heavy_Flat` · `^Warhead_Laser_Heavy` · `^Projectile_Bullet_Light` · `^ts_cabal_set8` |
| `CabalMothershipRockets` | 6 | `^Warhead_MissileTesla_Heavy` · `^TeslaWeapon` · `^HeavyMissile` · `^MediumFlameWeapon` |
| `CabalOverkillDroneLaser` | 4 | `^Warhead_Laser_Heavy_Flat` · `^Warhead_Laser_Heavy` · `^Projectile_Bullet_Light` · `^ts_cabal_cabaloverkilldronelaser` |
| `CabalSubmarinePlasma` | 5 | `^Warhead_Plasma_Heavy` · `^HeavyCannon` · `^MediumFlameWeapon` · `^MediumChemicalWeapon` |
| `ConsortiumMissileSystem` | 4 | `^TeslaWeapon` · `^Warhead_MissileAP_Medium` · `^Projectile_Missile_Medium` · `^Effect_Clsn_Medium_RA2` |
| `CorruptorSpore` | 4 | `^Warhead_Chemical_Medium` · `^Projectile_Chem_Medium` · `^Effect_Chem_Medium` · `^sc_zerg_corruptorspore` |
| `CorsairFlash` | 4 | `^Warhead_Flak_Medium_Flat` · `^Projectile_Flak_Medium` · `^Effect_Flak_Medium` · `^sc_protoss_corsairflash` |
| `Corsair_EMP` | 4 | `^Warhead_Tesla_Super` · `^Projectile_Lightning_Super` · `^Effect_Tesla_Super` · `^sc_protoss_corsair_emp` |
| `D2K_155mm2` | 6 | `^Warhead_CannonHE_Heavy` · `^MediumFlameWeapon` · `^ShrapnelWeapon` · `^HeavyBomb` |
| `D2K_155mm_turret` | 5 | `^Warhead_CannonHE_Medium_Flat` · `^Projectile_Grenade_Light_D2K_155mm` · `^Projectile_Shell_Medium_D2K` · `^Effect_CannonHE_Medium_D2K` |


_... and 303 more._


## W2 — two or more `^Warhead_*` inherits (84 vs ratchet 83)

| weapon | warhead templates |
|---|---|
| `AAGunBoatFlak` | `^Warhead_Flak_Medium` · `^Warhead_Flak_Medium_Flat` |
| `ArtilleryShell` | `^Warhead_Concussion_Medium_Flat` · `^Warhead_Demolition_Light` · `^Warhead_Concussion_Medium` |
| `BCLaser` | `^Warhead_Laser_Heavy_Flat` · `^Warhead_CannonHE_Heavy` |
| `BuggyPlasmaGrenade` | `^Warhead_Plasma_Light` · `^Warhead_Demolition_Light` |
| `CabalLegionGun` | `^Warhead_Laser_Heavy_Flat` · `^Warhead_Laser_Heavy` |
| `CabalMagicNuke` | `^Warhead_Tesla_Heavy` · `^Warhead_Tesla_Super` |
| `CabalMantisGun` | `^Warhead_Laser_Heavy_Flat` · `^Warhead_Laser_Heavy` |
| `CabalOverkillDroneLaser` | `^Warhead_Laser_Heavy_Flat` · `^Warhead_Laser_Heavy` |
| `D2K_Rocket_AA` | `^Warhead_MissileAP_Heavy` · `^Warhead_MissileHE_Heavy` |
| `D2K_Rocket_Trooper2` | `^Warhead_Railgun_Heavy` · `^Warhead_MissileHE_Heavy` |
| `DeathHandCluster` | `^Warhead_Flame_Light` · `^Warhead_Demolition_Light` |
| `Debris2` | `^Warhead_Demolition_Light_Flat` · `^Warhead_Flame_Light` |
| `DeviatorMissile` | `^Warhead_CannonHE_Heavy` · `^Warhead_MissileAP_Heavy` |
| `ExplosiveDebris` | `^Warhead_Flame_Light` · `^Warhead_Demolition_Light` |
| `Flamethrower` | `^Warhead_Flame_Light` · `^Warhead_Flame_Light` |
| `GlaveCanon` | `^Warhead_Railgun_Heavy_Flat` · `^Warhead_Railgun_Heavy` |
| `HMGo_upgrade` | `^Warhead_Laser_Heavy` · `^Warhead_Bullet_Medium` |
| `IonCannon` | `^Warhead_Tesla_Heavy` · `^Warhead_Tesla_Super` |
| `IxRailgunDroneBullet` | `^Warhead_Railgun_Heavy_Flat` · `^Warhead_Railgun_Heavy` |
| `JapanMaidenBowEnergized` | `^Warhead_Arrow_Light_Flat` · `^Warhead_Arrow_Light` |
| `LMG_ordos_upgrade` | `^Warhead_Laser_Heavy_Flat` · `^Warhead_Laser_Heavy` |
| `MigMissiles_rad` | `^Warhead_Chemical_Medium` · `^Warhead_MissileAP_Medium_GroundShip` |
| `NambuMGWaveforce` | `^Warhead_Railgun_Heavy` · `^Warhead_Bullet_Light` |
| `NaxQuadCannon_AA` | `^Warhead_Flak_Medium_Flat` · `^Warhead_Flak_Medium` |
| `NaxiMP40Laser` | `^Warhead_Bullet_Medium` · `^Warhead_Laser_Heavy` |
| `ObeliskLaserFragment` | `^Warhead_Laser_Heavy_Flat` · `^Warhead_Bullet_Medium` · `^Warhead_Laser_Heavy` |
| `PhobosLaser` | `^Warhead_Laser_Heavy_Flat` · `^Warhead_Laser_Heavy` |
| `PulseMissile` | `^Warhead_Tesla_Heavy` · `^Warhead_Tesla_Super` |
| `RA160mmE_elite` | `^Warhead_Demolition_Light` · `^Warhead_Concussion_Medium_Flat` |
| `RA160mmE_fire_elite` | `^Warhead_CannonFire_Heavy_Flat` · `^Warhead_Demolition_Light` |
| `RA160mmE_tesla_elite` | `^Warhead_Tesla_Heavy_Flat` · `^Warhead_Demolition_Light` |
| `RA2120mm_rad` | `^Warhead_Chemical_Medium` · `^Warhead_CannonHE_Medium` |
| `RA2HoverMissile_AA` | `^Warhead_MissileAA_Light_Flat` · `^Warhead_MissileAP_Light` |
| `RA2MultiHoverMissile_AA` | `^Warhead_MissileAA_Light_Flat` · `^Warhead_MissileHE_Light_Flat` |
| `RA2SCUD_rad` | `^Warhead_MissileChem_Heavy` · `^Warhead_MissileAP_Heavy` |
| `RA2Virusgun2` | `^Warhead_Toxic_Medium` · `^Warhead_Toxic_Light` |
| `RashidanGun_upgrade` | `^Warhead_Bullet_Medium_Flat` · `^Warhead_CannonHE_Heavy` |
| `SCScourgeDroneExplosion` | `^Warhead_Demolition_Heavy_Flat` · `^Warhead_Demolition_Heavy` · `^Warhead_Concussion_Medium` |
| `SkyHawkArrowsEnergized` | `^Warhead_Arrow_Medium` · `^Warhead_Arrow_Light` |
| `SkyHawkChainGunWaveforce` | `^Warhead_Railgun_Heavy` · `^Warhead_Bullet_Medium` |


_... and 44 more._


## W3 — two or more `^Projectile_*` inherits (29 vs ratchet 29)

| weapon | projectile templates |
|---|---|
| `110mm_Gun` | `^Projectile_Shell_Heavy` · `^Projectile_Shell_Medium_D2K` |
| `120mm_cobra` | `^Projectile_Shell_Light` · `^Projectile_Shell_Medium_D2K` |
| `D2K_155mm_turret` | `^Projectile_Grenade_Light_D2K_155mm` · `^Projectile_Shell_Medium_D2K` |
| `D2K_APC_Rocket` | `^Projectile_Missile_Medium` · `^Projectile_Missile_Heavy_D2K_Rocket` |
| `DeathHandCluster` | `^Projectile_Flame_Light` · `^Projectile_Grenade_Light_D2K_Debris` |
| `Debris2` | `^Projectile_Flame_Light` · `^Projectile_Grenade_Light_D2K_Debris` |
| `DeviatorMissile` | `^Projectile_Shell_Heavy` · `^Projectile_Missile_Heavy_D2K` |
| `DuelistTankCannon` | `^Projectile_Shell_Heavy` · `^Projectile_Shell_Medium_D2K` |
| `Dune_SiegeMortar` | `^Projectile_Shell_Light` · `^Projectile_Shell_Medium_D2K` |
| `ExplosiveDebris` | `^Projectile_Flame_Light` · `^Projectile_Grenade_Light_D2K_Debris` |
| `Flamethrower` | `^Projectile_Flame_Light` · `^Projectile_Flame_Light` |
| `HeavyIxianCombatTankCannon` | `^Projectile_Shell_Heavy` · `^Projectile_Shell_Medium_D2K` |
| `IxianCombatTankCannon` | `^Projectile_Shell_Heavy` · `^Projectile_Shell_Medium_D2K` |
| `MigMissiles_rad` | `^Projectile_Chem_Medium` · `^Projectile_Missile_Medium` |
| `NambuMGWaveforce` | `^Projectile_Railgun_Heavy` · `^Projectile_Bullet_Light` |
| `NaxiMP40Laser` | `^Projectile_Bullet_Medium` · `^Projectile_Laser_Heavy` |
| `RA2120mm_rad` | `^Projectile_Chem_Medium` · `^Projectile_Shell_Medium` |
| `ReaperGrenade` | `^Projectile_Grenade_Light` · `^Projectile_Shell_Heavy` |
| `SkyHawkChainGunWaveforce` | `^Projectile_Railgun_Heavy` · `^Projectile_Bullet_Medium` |
| `SteelMantaHunterCannons_AA` | `^Projectile_Missile_Medium` · `^Projectile_Bullet_Medium` |
| `TanyaBomb` | `^Projectile_Grenade_Light` · `^Projectile_Shell_Heavy` |
| `ZeroFighterChainGunWaveforce` | `^Projectile_Railgun_Heavy` · `^Projectile_Bullet_Medium` |
| `autogun_tank` | `^Projectile_Shell_Heavy` · `^Projectile_Missile_Heavy_D2K` |
| `d2k_air_drone_guns` | `^Projectile_Missile_Heavy_D2K` · `^Projectile_Bullet_Medium` |
| `facedancer_grenade` | `^Projectile_Shell_Heavy` · `^Projectile_Missile_Heavy_D2K` |
| `oDeathHandCluster` | `^Projectile_Flame_Light` · `^Projectile_Grenade_Light_D2K_Debris` |
| `ra1_soviets_hammertank_cannon_thermobaric` | `^Projectile_Flame_Medium` · `^Projectile_Shell_Heavy` |
| `ra1_soviets_volkov_volkovmagneticweaponincendiary` | `^Projectile_Flame_Medium` · `^Projectile_Shell_Heavy` |
| `schwarzermond_lunarsoldier_rifle` | `^Projectile_Bullet_Light` · `^Projectile_Laser_Heavy` |


## W4 — two or more `^Effect_*` inherits (167 vs ratchet 166)

| weapon | effect templates |
|---|---|
| `110mm_Gun` | `^Effect_CannonAP_Light` · `^Effect_CannonHE_Medium_D2K` |
| `120mm_cobra` | `^Effect_CannonAP_Light` · `^Effect_CannonHE_Medium_D2K` |
| `120mm_td` | `^Effect_CannonHE_Medium_D2K` · `^d2k_ordos_120mm_td` |
| `AAGunBoatFlak` | `^Effect_Flak_Puff_RA2` · `^Effect_Watersplash_Small_RA2` |
| `AsianLynxTankCannon` | `^Effect_AlliedTigerCannon` · `^Effect_Flame_Heavy` |
| `AsianSinglePlasma` | `^Effect_Apoc_AP_RA2` · `^Effect_Flame_Heavy` |
| `AsianSinglePlasma_elite` | `^Effect_Apoc_AP_RA2` · `^Effect_Flame_Heavy` |
| `AsianTurretPlasma` | `^Effect_Apoc_AP_RA2` · `^Effect_Flame_Heavy` · `^Effect_Twlt_Large_RA2` |
| `AsianTwinPlasma` | `^Effect_Apoc_AP_RA2` · `^Effect_Flame_Heavy` |
| `AsianTwinPlasma_elite` | `^Effect_Apoc_AP_RA2` · `^Effect_Flame_Heavy` |
| `AtreusMG` | `^Effect_CannonHE_Heavy` · `^sc_protoss_atreusmg` |
| `CorruptorSpore` | `^Effect_Chem_Medium` · `^sc_zerg_corruptorspore` |
| `CorsairFlash` | `^Effect_Flak_Medium` · `^sc_protoss_corsairflash` |
| `Corsair_EMP` | `^Effect_Tesla_Super` · `^sc_protoss_corsair_emp` |
| `D2K_155mm_turret` | `^Effect_CannonHE_Medium_D2K` · `^d2k_ordos_d2k_155mm_turret` |
| `D2K_APC_Rocket` | `^Effect_MissileAP_Medium` · `^Effect_MissileAP_Heavy_D2K_Rocket` |
| `D2K_APC_Rocket_AA` | `^d2k_ordos_d2k_apc_rocket_aa` · `^d2k_ordos_d2k_apc_rocket_aa_1` · `^d2k_ordos_d2k_apc_rocket_aa_2` |
| `D2K_Rocket` | `^Effect_MissileAP_Heavy_D2K_Rocket` · `^d2k_d2k_d2k_rocket` |
| `DeathHandCluster` | `^Effect_Flame_Light` · `^Effect_Demolition_Light_D2K` · `^d2k_d2k_set3` |
| `Debris2` | `^Effect_Flame_Light` · `^Effect_Demolition_Light_D2K` |
| `DefilerPlague` | `^Effect_Chem_Heavy` · `^sc_zerg_defilerplague` |
| `DeviatorMissile` | `^Effect_MissileAP_Heavy_D2K` · `^d2k_ordos_deviatormissile_2` |
| `DeviatorMissile_Artillery` | `^d2k_ordos_deviatormissile_artillery` · `^d2k_ordos_deviatormissile_artillery_1` · `^d2k_ordos_deviatormissile_artillery_2` · `^d2k_ordos_deviatormissile_artillery_3` |
| `DredMissile` | `^Effect_Clsn_Large_RA2` · `^Effect_Watersplash_Large_RA2` |
| `DroneAttack` | `^Effect_Melee_Medium` · `^sc_zerg_droneattack` |
| `DuelistTankCannon` | `^Effect_CannonHE_Medium_D2K` · `^d2k_ixian_duelisttankcannon` |
| `Dune_SiegeMortar` | `^Effect_CannonAP_Light` · `^Effect_CannonHE_Medium_D2K` |
| `EpigraphMG` | `^Effect_CannonHE_Heavy` · `^sc_protoss_epigraphmg` |
| `ExplosiveDebris` | `^Effect_Flame_Light` · `^Effect_Demolition_Light_D2K` · `^d2k_harkonnen_explosivedebris` |
| `Flamethrower` | `^Effect_Flame_Light` · `^Effect_Flame_Light` |
| `Fremen_RPG` | `^Effect_MissileAP_Heavy_D2K` · `^d2k_shared_fremen_rpg` |
| `GhostSniper` | `^Effect_CannonHE_Heavy` · `^sc_terran_ghostsniper` |
| `GladiusCannon` | `^sc_protoss_gladiuscannon` · `^sc_protoss_gladiuscannon_fx` |
| `GoliathMk2Rockets_AA` | `^Effect_MissileAP_Heavy_Rocket_SC` · `^sc_terran_goliathmk2rockets_aa` |
| `GoliathRockets_AA` | `^Effect_MissileHE_Heavy_SC` · `^sc_terran_goliathrockets_aa` |
| `GorekrakenClaw` | `^Effect_Melee_Medium` · `^sc_zerg_gorekrakenclaw` |
| `GoremawClaw` | `^Effect_Melee_Medium` · `^sc_zerg_goremawclaw` |
| `HMG_Duelist_upgrade` | `^d2k_ixian_hmg_duelist_upgrade_1` · `^d2k_ixian_hmg_duelist_upgrade_2` · `^d2k_ixian_hmg_duelist_upgrade` |
| `HMG_fremen` | `^d2k_shared_hmg_fremen` · `^d2k_shared_hmg_fremen_fx` |
| `HMGo_upgrade` | `^d2k_ordos_hmgo_upgrade` · `^d2k_ordos_hmgo_upgrade_fx` |


_... and 127 more._


## W5 — more than one resolved MAIN warhead (154 vs ratchet 153)

| weapon | mains | which |
|---|---|---|
| `12MissilesSpawnerScud` | 4 | `Demolition_Heavy` · `Demolition_Light` · `Flame_Medium` · `MissileAP_Heavy` |
| `AsianTSIonCannon` | 4 | `IonCannon` · `TeslaChargedWeapon` · `TeslaWeapon` · `Tesla_Super` |
| `Atomic` | 2 | `Nuclear_Super` · `Tesla_Super` |
| `BCLaser` | 2 | `CannonHE_Heavy` · `Laser_Heavy_Flat` |
| `CHFlameBlue` | 2 | `1Dam` · `Flame_Medium` |
| `CabalMagicNuke` | 8 | `10Dam_areanuke3` · `11Dam_areanuke3` · `1Dam_impact` · `4Dam_areanuke1` |
| `ChemTibAtomic` | 2 | `Nuclear_Super` · `Tesla_Super` |
| `Combat_Tank_F_Sound` | 2 | `1Dam` · `2Dam` |
| `CrateNuke` | 3 | `1Dam_impact` · `4Dam_areanuke1` · `TREEKILL` |
| `D2KRepair` | 2 | `1Dam` · `HealingWeapon` |
| `D2K_SiegeQuad` | 4 | `CannonHE_Medium` · `Concussion_Medium` · `Demolition_Heavy` · `Demolition_Light` |
| `DRPlasmaTankWeapon` | 2 | `1Dam` · `1DamBuildings` |
| `DTAtomic` | 2 | `Nuclear_Super` · `Tesla_Super` |
| `DeathHandCluster` | 3 | `1Dam` · `Demolition_Light` · `Flame_Light` |
| `DredMissile` | 3 | `Demolition_Light` · `MissileAP_Heavy` · `RA2SCUDMissileAP_Heavy_NoWall` |
| `ExecutionerDeath` | 7 | `10Dam_areanuke3` · `11Dam_areanuke3` · `1Dam_impact` · `4Dam_areanuke1` |
| `ExplosiveDebris` | 2 | `Demolition_Light` · `Flame_Light` |
| `FutureEnforcerShotgun` | 3 | `CannonHE_Medium` · `ShotgunGrenadeAlly` · `ShotgunShrapnelAlly` |
| `FutureEnforcerShotgunDeployed` | 3 | `CannonHE_Medium` · `ShotgunGrenadeAlly` · `ShotgunShrapnelAlly` |
| `FutureEnforcerShotgunDeployed_elite` | 3 | `CannonHE_Medium` · `ShotgunGrenadeAlly` · `ShotgunShrapnelAlly` |
| `FutureEnforcerShotgun_elite` | 3 | `CannonHE_Medium` · `ShotgunGrenadeAlly` · `ShotgunShrapnelAlly` |
| `Future_Cryocopter_Rocket` | 2 | `FutureCryocopterMissileAP_MediumFriendly` · `MissileAP_Medium_Flat` |
| `GLASCUD` | 2 | `1Dam` · `MissileHE_Heavy` |
| `GLASCUDPOWER` | 2 | `1Dam` · `MissileHE_Heavy` |
| `GLASCUDPOWER2` | 2 | `1Dam` · `MissileHE_Heavy` |
| `GLASCUDPOWER3` | 2 | `1Dam` · `MissileHE_Heavy` |
| `GLBarrelExplode` | 2 | `1Dam` · `Demolition_Heavy_Flat` |
| `GLBombTruckToxExplosive` | 3 | `1Dam` · `Concussion_Medium` · `Demolition_Heavy` |
| `GLBombTruckToxExplosive2` | 3 | `1Dam` · `Concussion_Medium` · `Demolition_Heavy` |
| `GLDemolitionExplode` | 3 | `1Dam` · `Concussion_Medium` · `Demolition_Heavy` |
| `GLRebelToxin` | 2 | `1Dam` · `Clear` |
| `GLRebelToxinGarrison` | 2 | `1Dam` · `Clear` |
| `GLTerroristExplosive` | 3 | `1Dam` · `Concussion_Medium` · `Demolition_Heavy` |
| `GLTerroristExplosive2` | 3 | `1Dam` · `Concussion_Medium` · `Demolition_Heavy` |
| `GLToxinBomb` | 3 | `1Dam` · `Demolition_Heavy` · `Flame_Heavy` |
| `GLToxinBombBlue` | 3 | `1Dam` · `Demolition_Heavy` · `Flame_Heavy` |
| `GLToxinBombPurple` | 3 | `1Dam` · `Demolition_Heavy` · `Flame_Heavy` |
| `GLToxinExplode` | 2 | `1Dam` · `Demolition_Light` |
| `GLToxinExplodeBlue` | 2 | `1Dam` · `Demolition_Light` |
| `GLTunnelWeap` | 2 | `1Dam` · `Bullet_Light` |


_... and 114 more._


## W6 — effect warheads declared LOCALLY (401 vs ratchet 394)

| weapon | nodes | first three |
|---|---|---|
| `120mm_cobra_deploy` | 8 | `Warhead@DuneRock: LeaveSmudge` · `Warhead@DuneSand: LeaveSmudge` · `Warhead@RA2Crater: LeaveSmudge` |
| `120mm_python` | 8 | `Warhead@DuneRock: LeaveSmudge` · `Warhead@DuneSand: LeaveSmudge` · `Warhead@RA2Crater: LeaveSmudge` |
| `120mm_python_deploy` | 8 | `Warhead@DuneRock: LeaveSmudge` · `Warhead@DuneSand: LeaveSmudge` · `Warhead@RA2Crater: LeaveSmudge` |
| `12MissilesSpawnerScud` | 6 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` · `Warhead@RA2Scorch: LeaveSmudge` |
| `155mm` | 10 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` · `Warhead@DuneRock: LeaveSmudge` |
| `155mmCryo` | 1 | `Warhead@Effect: CreateEffect` |
| `2100Tanktrap` | 1 | `Warhead@Smu: LeaveSmudge` |
| `25mm` | 3 | `Warhead@Effect: CreateEffect` · `Warhead@EffectAir: CreateEffect` · `Warhead@RA2Scorch: LeaveSmudge` |
| `ATMine` | 10 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` · `Warhead@Concrete: DamagesConcrete` |
| `ArmoredCarMG` | 10 | `Warhead@Effect: CreateEffect` · `Warhead@EffectAir: CreateEffect` · `Warhead@ShieldHitEffect: CreateEffect` |
| `ArtilleryExplode` | 1 | `Warhead@2Eff: CreateEffect` |
| `AsianChaosMine` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianChaosSuperweapon` | 1 | `Warhead@1: CreateEffect` |
| `AsianChaosTurret` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianChemical` | 5 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge1: LeaveSmudge` · `Warhead@RA2Crater: LeaveSmudge` |
| `AsianHarbingerPlasma` | 6 | `Warhead@Effect: CreateEffect` · `Warhead@RA2Scorch: LeaveSmudge` · `Warhead@Smudge: LeaveSmudge` |
| `AsianIonBeamMini` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianMaidenBow` | 9 | `Warhead@ShieldHitEffect: CreateEffect` · `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` |
| `AsianMaidenBow_elite` | 9 | `Warhead@ShieldHitEffect: CreateEffect` · `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` |
| `AsianOilBombFragments` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianPhoenixRocket` | 1 | `Warhead@RA2Scorch: LeaveSmudge` |
| `AsianPhotonCannon` | 8 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` · `Warhead@DuneRock: LeaveSmudge` |
| `AsianPunisherAG` | 9 | `Warhead@ShieldHitEffect: CreateEffect` · `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` |
| `AsianSmallTorpedo` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSniperAP` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSubmarineBomb` | 4 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` · `Warhead@DuneRock: LeaveSmudge` |
| `AsianTSIonCannon` | 2 | `Warhead@3Smu_area: LeaveSmudge` · `Warhead@Effect: CreateEffect` |
| `AsianTurretPlasma` | 1 | `Warhead@Effect: CreateEffect` |
| `AthenaLaser` | 13 | `Warhead@Effect: CreateEffect` · `Warhead@Effect2: CreateEffect` · `Warhead@Effect3: CreateEffect` |
| `BHBombs` | 1 | `Warhead@3Eff: CreateEffect` |
| `BallistaMultiShot` | 9 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` · `Warhead@DuneRock: LeaveSmudge` |
| `BallistaMultiShotEnergized` | 5 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` · `Warhead@RA2Scorch: LeaveSmudge` |
| `BarrelExplode` | 11 | `Warhead@2Eff: CreateEffect` · `Warhead@Smu: LeaveSmudge` · `Warhead@Glow: GlowImpact` |
| `BigChemSpray` | 1 | `Warhead@3Eff: CreateEffect` |
| `BlackEagleThunderboltMissiles` | 6 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge1: LeaveSmudge` · `Warhead@Smudge2: LeaveSmudge` |
| `BlackHoleSuck` | 1 | `Warhead@Effect: CreateEffect` |
| `BoatMissile` | 2 | `Warhead@3Eff: CreateEffect` · `Warhead@4EffAir: CreateEffect` |
| `BuggyPlasmaGrenade` | 7 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge1: LeaveSmudge` · `Warhead@RA2Crater: LeaveSmudge` |
| `BuildingExplode` | 2 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` |
| `C4` | 1 | `Warhead@2Eff: CreateEffect` |


_... and 361 more._


**FAIL — W2, W4, W5, W6, W7, W8 rose above baseline.** A weapon was given a second warhead, projectile or effect. The law allows exactly three inherits and one main.
