# Weapon shape — the ONE-WARHEAD / THREE-INHERIT law

**Maintainer ruling, 2026-09-06.** Every concrete weapon ends with exactly three inherits — `^Warhead_*`, `^Projectile_*`, `^Effect_*` — one main warhead, and no effect warheads of its own. Mechanic warheads (`FireShrapnel`, `GrantExternalCondition`) and the `*Percentage` / `*FriendlyFire` / `*ExtraDamage` halves of one main are NOT violations.

⛔ This **repeals the exemption** in `tools/audit/intentional_composites.py`. Its 224 entries are no longer 'reviewed, keep' — they are the worklist. The registry data stays useful: it says which mains someone chose on purpose.

concrete weapons with inherits: **2031**

| check | what | count | ratchet |
|---|---|--:|--:|
| W1 | more than 3 inherits | **580** | 583 |
| W2 | two or more `^Warhead_*` inherits | **218** ⛔ | 213 |
| W3 | two or more `^Projectile_*` inherits | **18** | 21 |
| W4 | two or more `^Effect_*` inherits | **58** | 61 |
| W5 | more than one resolved MAIN warhead | **1105** ⛔ | 401 |
| W6 | effect warheads declared LOCALLY | **687** | 687 |

| I7 informational — missing template | weapons |
|---|--:|
| no `^Effect_*` inherit | 1230 |
| no `^Projectile_*` inherit | 1348 |
| no `^Warhead_*` inherit | 1142 |

_I7 is a REVIEW QUEUE, not a defect count — an instant or utility weapon may legitimately have no projectile. Do not ratchet it without a per-weapon pass._


## W1 — more than 3 inherits (580 vs ratchet 583)

| weapon | inherits | first four |
|---|---|---|
| `APCGun` | 5 | `^Compatibility_Flak_MediumFlat` · `^Warhead_Bullet_Medium` · `^Warhead_Flak_Medium` · `^Projectile_Flak_Medium` |
| `APCGunAllies` | 5 | `^Compatibility_Flak_MediumFlat` · `^Warhead_Bullet_Medium` · `^Warhead_Flak_Medium` · `^Projectile_Flak_Medium` |
| `APTusk` | 5 | `^Warhead_MissileAP_Heavy` · `^TankDestroyerCannon` · `^Grenade` · `^FlakWeapon` |
| `ASDFGun2` | 4 | `^Warhead_Railgun_Heavy` · `^Projectile_Railgun_Heavy` · `^Effect_Railgun_Heavy` · `ASDFGun` |
| `ASDFKamikazeExplosion` | 4 | `^Warhead_Demolition_Heavy` · `^Warhead_Concussion_Medium` · `^Effect_Concussion_Medium` · `^Projectile_Grenade_Light` |
| `AlliedTankDestroyerCannon` | 4 | `^Warhead_CannonHE_Medium` · `^Warhead_CannonAP_Light` · `^Projectile_Shell_Light` · `^Effect_CannonAP_Light` |
| `AphidCryo_AA` | 4 | `^Warhead_CryoBlast_Medium` · `^Warhead_MissileCryo_Heavy` · `^Projectile_Missile_Heavy` · `^Effect_Cryo` |
| `Aphid_AA` | 4 | `^Warhead_Concussion_Medium` · `^Warhead_MissileHE_Heavy` · `^Projectile_Missile_Heavy` · `^Effect_MissileHE_Heavy` |
| `ArcherArtilleryShell` | 6 | `^Warhead_Concussion_Heavy` · `^MediumCannon` · `^HeavyCannon` · `^MediumFlameWeapon` |
| `ArmoredCarMG` | 9 | `^Warhead_Bullet_Medium` · `^ArrowWeapon` · `^TankDestroyerCannon` · `^SmallArms` |
| `ArtilleryShell` | 5 | `^Compatibility_Concussion_MediumFlat` · `^Warhead_Demolition_Light` · `^Warhead_Concussion_Medium` · `^Projectile_Grenade_Light` |
| `ArtilleryShellUpgrade` | 7 | `^Warhead_Concussion_Heavy` · `^Grenade` · `^ShrapnelWeapon` · `^MediumChemicalWeapon` |
| `AsianChaosMine` | 5 | `AsianChaosTurret` · `AsianTankMine` · `^Warhead_Chemical_Heavy` · `^Projectile_Chem_Heavy` |
| `AsianChemical` | 7 | `^Compatibility_Chemical_MediumFlat` · `^LightChemicalWeapon` · `^MediumChemicalWeapon` · `^HeavyChemicalWeapon` |
| `AsianGrenade` | 4 | `^Compatibility_Concussion_MediumFlat` · `^Warhead_Concussion_Medium` · `^Effect_Concussion_Medium` · `^RA2MediumCannon` |
| `AsianHarbingerPlasma` | 13 | `^Compatibility_Plasma_MediumFlat` · `^Warhead_Plasma_Medium` · `^Warhead_CannonHE_Medium` · `^Projectile_Shell_Medium` |
| `AsianLynxTankCannon` | 7 | `^Compatibility_CannonHE_MediumFlat` · `^Grenade` · `^ShrapnelWeapon` · `^LightFlameWeapon` |
| `AsianMLRS` | 5 | `^Compatibility_MissileAA_MediumFlat` · `^HeavyMissile` · `^FlakWeapon` · `^RA2Grenade` |
| `AsianMaidenBow` | 4 | `^Compatibility_Arrow_LightFlat` · `AsianPhotonCannon` · `^Grenade` · `^ArrowWeapon` |
| `AsianNinjaStar` | 4 | `^Warhead_Melee_Medium` · `^Projectile_InstantHit` · `^Effect_Melee_Medium` · `^Effect_Bullet_Medium_RA2` |
| `AsianPelicanMissile` | 7 | `^Compatibility_MissileAP_HeavyFlat` · `^Warhead_Concussion_Light` · `^Warhead_MissileAP_Heavy` · `^Projectile_Missile_Heavy` |
| `AsianPhoenixRocket` | 6 | `^Warhead_Flame_Medium` · `^Warhead_Demolition_Light` · `^Projectile_Flame_Medium` · `^Effect_Flame_Medium` |
| `AsianPhotonCannon` | 5 | `^Compatibility_Plasma_HeavyFlat` · `^MediumMissile` · `^FlakWeapon` · `^TeslaWeapon` |
| `AsianPulverizerGatling` | 6 | `^Compatibility_Bullet_MediumFlat` · `^Warhead_Bullet_Light` · `^Warhead_CannonHE_Heavy` · `^Projectile_Shell_Heavy` |
| `AsianRailTank` | 4 | `^Warhead_Railgun_Heavy` · `^Projectile_Railgun_Heavy` · `^Effect_Railgun_Heavy` · `^Effect_Clsn_Medium_RA2` |
| `AsianRailgun` | 4 | `^Warhead_Railgun_Heavy` · `^Projectile_Railgun_Heavy` · `^Effect_Railgun_Heavy` · `^Effect_Explosion_Medium_RA2` |
| `AsianSinglePlasma` | 12 | `^Compatibility_Plasma_HeavyFlat` · `^Warhead_CannonHE_Medium` · `^Projectile_Shell_Medium` · `^Effect_CannonHE_Medium` |
| `AsianSmallTorpedo` | 4 | `^Compatibility_MissileAP_HeavyFlat` · `^RA2Grenade` · `^RA2HeavyMissile` · `^Effect_Watersplash_Large_RA2` |
| `AsianSniper` | 8 | `^Warhead_Bullet_Heavy` · `^Projectile_Shell_Heavy` · `^Effect_CannonHE_Heavy` · `^MediumMissile` |
| `AsianSniperLockdown` | 4 | `^Warhead_Tesla_Super` · `^Projectile_Lightning_Super` · `^Effect_Tesla_Super` · `AsianSniperAP` |
| `AsianSubmarineBomb` | 5 | `^Compatibility_Demolition_HeavyFlat` · `^Warhead_Demolition_Heavy` · `^Effect_Demolition_Heavy` · `^RA2Grenade` |
| `AthenaLaser` | 7 | `^Compatibility_Laser_HeavyFlat` · `^LightMissile` · `^SmallArms` · `^Chaingun` |
| `AtreusMG` | 8 | `^Compatibility_Bullet_MediumFlat` · `^Warhead_CannonHE_Heavy` · `^Projectile_Shell_Heavy` · `^Effect_CannonHE_Heavy` |
| `BCLaser` | 12 | `^Compatibility_Laser_HeavyFlat` · `^Warhead_CannonHE_Heavy` · `^Projectile_Shell_Heavy` · `^Effect_CannonHE_Heavy` |
| `BHRedDarts` | 6 | `^Warhead_Tesla_Super` · `^TeslaChargedWeapon` · `^TankDestroyerCannon` · `^Chaingun` |
| `BTRMachineGun` | 5 | `^Compatibility_Bullet_MediumFlat` · `^Warhead_Bullet_Light` · `^Warhead_Bullet_Medium` · `^Projectile_Bullet_Medium` |
| `BTRTeslaMachineGun` | 5 | `^Compatibility_Tesla_HeavyFlat` · `^Warhead_MissileAP_Light` · `^Warhead_Tesla_Heavy` · `^Projectile_Lightning_Heavy` |
| `BallistaMultiShot` | 5 | `^Warhead_Arrow_Medium` · `^Grenade` · `^LightFlameWeapon` · `^LightChemicalWeapon` |
| `BallistaMultiShotEnergized` | 5 | `^Compatibility_Arrow_MediumFlat` · `^TeslaWeapon` · `^MediumFlameWeapon` · `^MediumChemicalWeapon` |
| `BallistaSingleShotAirEnergized` | 4 | `^Warhead_MissileAP_Light` · `^Projectile_Missile_Light` · `^Effect_MissileAP_Light` · `JapanMaidenBowEnergized` |


_... and 540 more._


## W2 — two or more `^Warhead_*` inherits (218 vs ratchet 213)

| weapon | warhead templates |
|---|---|
| `APCGun` | `^Warhead_Bullet_Medium` · `^Warhead_Flak_Medium` |
| `APCGunAllies` | `^Warhead_Bullet_Medium` · `^Warhead_Flak_Medium` |
| `ASDFKamikazeExplosion` | `^Warhead_Demolition_Heavy` · `^Warhead_Concussion_Medium` |
| `AlliedTankDestroyerCannon` | `^Warhead_CannonHE_Medium` · `^Warhead_CannonAP_Light` |
| `AphidCryo_AA` | `^Warhead_CryoBlast_Medium` · `^Warhead_MissileCryo_Heavy` |
| `Aphid_AA` | `^Warhead_Concussion_Medium` · `^Warhead_MissileHE_Heavy` |
| `ArtilleryShell` | `^Warhead_Demolition_Light` · `^Warhead_Concussion_Medium` |
| `AsianHarbingerPlasma` | `^Warhead_Plasma_Medium` · `^Warhead_CannonHE_Medium` |
| `AsianPelicanMissile` | `^Warhead_Concussion_Light` · `^Warhead_MissileAP_Heavy` |
| `AsianPhoenixRocket` | `^Warhead_Flame_Medium` · `^Warhead_Demolition_Light` |
| `AsianPulverizerGatling` | `^Warhead_Bullet_Light` · `^Warhead_CannonHE_Heavy` |
| `BTRMachineGun` | `^Warhead_Bullet_Light` · `^Warhead_Bullet_Medium` |
| `BTRTeslaMachineGun` | `^Warhead_MissileAP_Light` · `^Warhead_Tesla_Heavy` |
| `BigShieeTusk` | `^Warhead_MissileHE_Heavy` · `^Warhead_Concussion_Medium` |
| `BlackEagleMissiles` | `^Warhead_Demolition_Light` · `^Warhead_Demolition_Heavy` |
| `CHGuardRifle` | `^Warhead_Bullet_Light` · `^Warhead_Bullet_Medium` |
| `CabalCyborgChaingun` | `^Warhead_Bullet_Light` · `^Warhead_Bullet_Medium` |
| `CabalHeavyReaperMissiles` | `^Warhead_MissileHE_Medium` · `^Warhead_MissileHE_Heavy` · `^Warhead_Demolition_Light` · `^Warhead_Concussion_Medium` |
| `CabalHeavyReaperMissiles_AA` | `^Warhead_MissileHE_Medium` · `^Warhead_MissileHE_Heavy` · `^Warhead_Demolition_Light` · `^Warhead_Concussion_Medium` |
| `CabalLegionGun` | `^Warhead_Bullet_Light` · `^Warhead_Laser_Heavy` |
| `CabalMagicNuke` | `^Warhead_Tesla_Heavy` · `^Warhead_Tesla_Super` |
| `CabalMantisGun` | `^Warhead_Bullet_Light` · `^Warhead_Laser_Heavy` |
| `CabalOverkillDroneLaser` | `^Warhead_Bullet_Light` · `^Warhead_Laser_Heavy` |
| `CabalReaperMissiles` | `^Warhead_MissileHE_Light` · `^Warhead_MissileHE_Medium` · `^Warhead_Demolition_Light` · `^Warhead_Concussion_Medium` |
| `CabalReaperMissiles_AA` | `^Warhead_MissileHE_Light` · `^Warhead_MissileHE_Medium` · `^Warhead_Demolition_Light` · `^Warhead_Concussion_Medium` |
| `CabalRocketCyborgRockets` | `^Warhead_MissileHE_Light` · `^Warhead_MissileHE_Medium` |
| `CabalRocketCyborgRocketsUpgraded` | `^Warhead_MissileHE_Light` · `^Warhead_MissileHE_Medium` |
| `ChronoTuskCryo` | `^Warhead_CannonHE_Medium` · `^Warhead_CannonHE_Medium` · `^Warhead_CannonCryo_Medium` |
| `ConscriptMolotov` | `^Warhead_Demolition_Light` · `^Warhead_Flame_Light` |
| `CorsairFlash` | `^Warhead_Flak_Medium` · `^Warhead_Demolition_Light` |
| `D2K_155mm3` | `^Warhead_Demolition_Light` · `^Warhead_Demolition_Heavy` · `^Warhead_Concussion_Medium` |
| `D2K_155mm_turret` | `^Warhead_Demolition_Light` · `^Warhead_Demolition_Heavy` · `^Warhead_Concussion_Medium` |
| `D2K_APC_Rocket` | `^Warhead_MissileAP_Light` · `^Warhead_MissileAP_Medium` |
| `D2K_Rocket_Trooper` | `^Warhead_MissileAP_Light` · `^Warhead_MissileAP_Medium` · `^Warhead_MissileAP_Heavy` |
| `D2K_Rocket_Trooper1` | `^Warhead_Flak_Medium` · `^Warhead_MissileAP_Light` · `^Warhead_MissileAP_Heavy` |
| `D2K_Rocket_Trooper2` | `^Warhead_Demolition_Light` · `^Warhead_Railgun_Heavy` · `^Warhead_CannonHE_Medium` |
| `D2K_Rocket_Trooper_AA` | `^Warhead_Flak_Medium` · `^Warhead_MissileAP_Light` · `^Warhead_MissileAP_Heavy` |
| `D2K_Rocket_Trooper_AGOnly` | `^Warhead_Demolition_Light` · `^Warhead_Railgun_Heavy` · `^Warhead_CannonHE_Medium` |
| `DalekCannon` | `^Warhead_Tesla_Heavy` · `^Warhead_Laser_Heavy` |
| `DepthChargeCryo` | `^Warhead_CryoBlast_Light` · `^Warhead_CannonAP_Light` · `^Warhead_CannonCryo_Light` · `^Warhead_Demolition_Heavy` · `^Warhead_CryoBlast_Heavy` |


_... and 178 more._


## W3 — two or more `^Projectile_*` inherits (18 vs ratchet 21)

| weapon | projectile templates |
|---|---|
| `ChronoTuskCryo` | `^Projectile_Shell_Medium` · `^Projectile_Shell_Medium` · `^Projectile_Shell_Medium` |
| `DepthChargeCryo` | `^Projectile_Grenade_Light` · `^Projectile_Shell_Light` · `^Projectile_Shell_Light` · `^Projectile_Grenade_Light` · `^Projectile_Grenade_Light` |
| `FlametankExplode` | `^Projectile_Flame_Medium` · `^Projectile_Missile_Medium` |
| `Flamethrower` | `^Projectile_Flame_Light` · `^Projectile_Flame_Light` |
| `HeavyIxianCombatTankCannon` | `^Projectile_Shell_Heavy` · `^Projectile_Shell_Light` |
| `HeavyOrdosCombatTankRockets` | `^Projectile_Missile_Heavy_D2K` · `^Projectile_Shell_Light` |
| `IxianCombatTankCannon` | `^Projectile_Shell_Heavy` · `^Projectile_Shell_Light` |
| `LatinMonkeyGrenade1` | `^Projectile_Grenade_Light` · `^Projectile_Shell_Heavy` |
| `M1A1MachineGun` | `^Projectile_Bullet_Medium` · `^Projectile_Shell_Heavy` · `^Projectile_Shell_Heavy` |
| `MachineGunAPH` | `^Projectile_Bullet_Medium` · `^Projectile_Shell_Medium` · `^Projectile_Shell_Medium` |
| `RashidanGun_upgrade` | `^Projectile_Shell_Heavy` · `^Projectile_Missile_Heavy` |
| `ReaperGrenade` | `^Projectile_Grenade_Light` · `^Projectile_Shell_Heavy` |
| `Su57MaverickThermobaric` | `^Projectile_Missile_Heavy` · `^Projectile_Shell_Medium` · `^Projectile_Flame_Medium` |
| `TS70mmTur` | `^Projectile_Shell_Medium` · `^Projectile_Shell_Light` |
| `YakovlevCannon` | `^Projectile_Shell_Heavy` · `^Projectile_Shell_Light` |
| `YakovlevCannon_elite` | `^Projectile_Shell_Heavy` · `^Projectile_Shell_Light` |
| `ra120mm2Thermobaric` | `^Projectile_Shell_Heavy` · `^Projectile_Flame_Heavy` |
| `ra120mmThermobaric` | `^Projectile_Shell_Heavy` · `^Projectile_Flame_Heavy` |


## W4 — two or more `^Effect_*` inherits (58 vs ratchet 61)

| weapon | effect templates |
|---|---|
| `AsianHarbingerPlasma` | `^Effect_CannonHE_Medium` · `^Effect_Apoc_Explosion_RA2` |
| `AsianNinjaStar` | `^Effect_Melee_Medium` · `^Effect_Bullet_Medium_RA2` |
| `AsianPelicanMissile` | `^Effect_MissileAP_Heavy` · `^Effect_Grey_Explosion_Small_RA2` |
| `AsianPhoenixRocket` | `^Effect_Flame_Medium` · `^Effect_Explosion_Large_RA2` |
| `AsianRailTank` | `^Effect_Railgun_Heavy` · `^Effect_Clsn_Medium_RA2` |
| `AsianRailgun` | `^Effect_Railgun_Heavy` · `^Effect_Explosion_Medium_RA2` |
| `AsianSinglePlasma` | `^Effect_CannonHE_Medium` · `^Effect_Apoc_Explosion_RA2` |
| `AsianSubmarineBomb` | `^Effect_Demolition_Heavy` · `^Effect_Twlt_Large_RA2` |
| `ChronoTuskCryo` | `^Effect_CannonHE_Medium` · `^Effect_CannonHE_Medium` · `^Effect_Cryo` |
| `DepthChargeCryo` | `^Effect_Cryo` · `^Effect_CannonAP_Light` · `^Effect_Cryo` · `^Effect_Demolition_Light` · `^Effect_Cryo` |
| `FlametankExplode` | `^Effect_Flame_Medium` · `^Effect_MissileHE_Medium` |
| `Flamethrower` | `^Effect_Flame_Light` · `^Effect_Flame_Light` |
| `HeavyIxianCombatTankCannon` | `^Effect_CannonHE_Heavy` · `^Effect_CannonAP_Light` |
| `HeavyOrdosCombatTankRockets` | `^Effect_MissileHE_Heavy_D2K` · `^Effect_CannonAP_Light` |
| `IxianCombatTankCannon` | `^Effect_CannonHE_Heavy` · `^Effect_CannonAP_Light` |
| `JapanesePlasmaBomb` | `^Effect_Flame_Heavy` · `^Effect_Demolition_Heavy` |
| `KotinCannonNuclearShell` | `^Effect_CannonHE_Heavy` · `^Effect_Nuclear_Super` |
| `LatinBuggyRocket_elite` | `^Effect_Flame_Medium` · `^Effect_Demolition_Heavy` |
| `LatinMonkeyGrenade1` | `^Effect_Concussion_Medium` · `^Effect_CannonHE_Heavy` |
| `LunarNaxiJadgDestroyer` | `^Effect_CannonHE_Heavy` · `^Effect_Concussion_Medium` |
| `M1A1MachineGun` | `^Effect_Bullet_Medium` · `^Effect_CannonHE_Heavy` · `^Effect_CannonHE_Heavy` |
| `MachineGunAPH` | `^Effect_Bullet_Medium` · `^Effect_CannonHE_Medium` · `^Effect_CannonHE_Medium` |
| `MissileAttackRobotGun` | `^Effect_MissileAP_Medium` · `^Effect_Grey_Explosion_Small_RA2` |
| `MonsterTank120mm` | `^Effect_CannonHE_Heavy` · `^Effect_Nuclear_Super` |
| `MonsterTank120mmInferno` | `^Effect_CannonHE_Heavy` · `^Effect_Flame_Heavy` |
| `NaxBrummbarArty` | `^Effect_Concussion_Medium` · `^Effect_CannonHE_Heavy` |
| `NaxGrilleArty` | `^Effect_CannonHE_Heavy` · `^Effect_Concussion_Medium` |
| `NaxiCowDrop` | `^Effect_Demolition_Heavy` · `^Effect_Clsn_Medium_RA2` |
| `NaxiJadgDestroyer` | `^Effect_CannonHE_Heavy` · `^Effect_Concussion_Medium` |
| `OrionRailgun` | `^Effect_Railgun_Heavy` · `^Effect_Explosion_Large_RA2` |
| `RA2120xmm` | `^Effect_CannonAP_Light` · `^Effect_Apoc_Explosion_RA2` |
| `RA2FreedomAK47` | `^Effect_CannonHE_Heavy` · `^Effect_Bullet_Light_RA2` |
| `RA2GrandCannonWeapon` | `^Effect_CannonHE_Heavy` · `^Effect_Clsn_Medium_RA2` |
| `RA2MortarBike` | `^Effect_CannonHE_Heavy` · `^Effect_Explosion_Large_RA2` |
| `RashidanGun_upgrade` | `^Effect_CannonHE_Heavy` · `^Effect_MissileHE_Heavy` |
| `ReaperGrenade` | `^Effect_Concussion_Medium` · `^Effect_CannonHE_Heavy` |
| `SCUDTesla` | `^Effect_Tesla_Heavy` · `^Effect_Kirov_Tesla_RA2` |
| `Su57MaverickThermobaric` | `^Effect_Flame_Heavy` · `^Effect_CannonHE_Medium` · `^Effect_Flame_Medium` |
| `TS120mmx` | `^Effect_CannonHE_Medium` · `^Effect_Concussion_Medium` |
| `TS70mmTur` | `^Effect_CannonHE_Medium` · `^Effect_CannonAP_Light` |


_... and 18 more._


## W5 — more than one resolved MAIN warhead (1105 vs ratchet 401)

| weapon | mains | which |
|---|---|---|
| `105mmThermobaric` | 3 | `CannonHE_Medium` · `Flame_Medium` · `Flame_MediumFlatCompatibility` |
| `110mm_Gun` | 4 | `CannonAP_Light` · `CannonAP_LightFlatCompatibility` · `CannonHE_Heavy` · `CannonHE_Medium` |
| `120mm_cobra` | 5 | `CannonAP_Light` · `CannonAP_LightFlatCompatibility` · `CannonHE_Medium` · `Concussion_Medium` |
| `120mm_cobra_deploy` | 5 | `CannonAP_Light` · `CannonAP_LightFlatCompatibility` · `CannonHE_Medium` · `Concussion_Medium` |
| `120mm_python` | 5 | `CannonAP_Light` · `CannonAP_LightFlatCompatibility` · `CannonHE_Medium` · `Concussion_Medium` |
| `120mm_python_deploy` | 5 | `CannonAP_Light` · `CannonAP_LightFlatCompatibility` · `CannonHE_Medium` · `Concussion_Medium` |
| `120mm_td` | 5 | `CannonHE_Medium` · `CannonHE_MediumFlatCompatibility` · `LightChemicalWeapon` · `MediumChemicalWeapon` |
| `12MissilesSpawnerScud` | 4 | `Demolition_Heavy` · `Demolition_Light` · `Flame_Medium` · `MissileAP_Heavy` |
| `155mm` | 4 | `Concussion_Heavy` · `Grenade` · `HeavyCannon` · `ShrapnelWeapon` |
| `155mmBastion` | 4 | `Concussion_Heavy` · `Grenade` · `HeavyCannon` · `ShrapnelWeapon` |
| `155mmBastionCryo` | 4 | `Concussion_Heavy` · `Grenade` · `HeavyCannon` · `ShrapnelWeapon` |
| `155mmCryo` | 4 | `Concussion_Heavy` · `Grenade` · `HeavyCannon` · `ShrapnelWeapon` |
| `25mm` | 7 | `CannonHE_Medium` · `CannonHE_MediumFlatCompatibility` · `Grenade` · `LightFlameWeapon` |
| `25mmWaveforce` | 8 | `CannonHE_Medium` · `CannonHE_MediumFlatCompatibility` · `Grenade` · `LightFlameWeapon` |
| `8Inch` | 3 | `Demolition_Heavy` · `Demolition_HeavyFlatCompatibility` · `Demolition_Light` |
| `AAGunBoatFlak` | 6 | `Bullet_Light` · `Chaingun` · `Flak_Medium` · `Flak_MediumFlatCompatibility` |
| `AAGunBoatFlak_elite` | 6 | `Bullet_Light` · `Chaingun` · `Flak_Medium` · `Flak_MediumFlatCompatibility` |
| `ACV_Machinegun` | 3 | `Bullet_Light` · `Bullet_Medium` · `Bullet_MediumFlatCompatibility` |
| `APCGun` | 3 | `Bullet_Medium` · `Flak_Medium` · `Flak_MediumFlatCompatibility` |
| `APCGunAllies` | 3 | `Bullet_Medium` · `Flak_Medium` · `Flak_MediumFlatCompatibility` |
| `APCGunAllies_AA` | 3 | `Bullet_Medium` · `Flak_Medium` · `Flak_MediumFlatCompatibility` |
| `APCGun_AA` | 3 | `Bullet_Medium` · `Flak_Medium` · `Flak_MediumFlatCompatibility` |
| `APTusk` | 5 | `FlakWeapon` · `Grenade` · `MediumMissile` · `MissileAP_Heavy` |
| `APTuskCryo` | 5 | `FlakWeapon` · `Grenade` · `MediumMissile` · `MissileAP_Heavy` |
| `ASDFGun` | 3 | `Bullet_Light` · `Bullet_Medium` · `Bullet_MediumFlatCompatibility` |
| `ASDFGun2` | 4 | `Bullet_Light` · `Bullet_Medium` · `Bullet_MediumFlatCompatibility` · `Railgun_Heavy` |
| `ASDFKamikazeExplosion` | 2 | `Concussion_Medium` · `Demolition_Heavy` |
| `ATMine` | 3 | `ATMineDemolition_Light` · `Demolition_Light` · `HeavyMissile` |
| `AlliedTankDestroyerCannon` | 2 | `CannonAP_Light` · `CannonHE_Medium` |
| `AphidCryo_AA` | 2 | `CryoBlast_Medium` · `MissileCryo_Heavy` |
| `Aphid_AA` | 2 | `Concussion_Medium` · `MissileHE_Heavy` |
| `ArbiterCannon` | 9 | `FlakWeapon` · `HeavyCannon` · `MediumCannon` · `Plasma_HeavyFlatCompatibility` |
| `ArcherArtilleryShell` | 7 | `CollapseTargetCompatibility1` · `Concussion_Heavy` · `HeavyBomb` · `HeavyCannon` |
| `ArmoredCarMG` | 9 | `ArrowWeapon` · `Bullet_Medium` · `Chaingun` · `FlakWeapon` |
| `ArmoredCarMGAAWaveforce` | 13 | `ArrowWeapon` · `Bullet_Light` · `Bullet_Medium` · `CannonAP_Light` |
| `ArmoredCarMGWaveforce` | 10 | `ArrowWeapon` · `Bullet_Medium` · `Chaingun` · `FlakWeapon` |
| `ArmoredCarMG_AA` | 12 | `ArrowWeapon` · `Bullet_Light` · `Bullet_Medium` · `CannonAP_Light` |
| `ArtilleryExplode` | 4 | `Concussion_Heavy` · `Grenade` · `HeavyCannon` · `ShrapnelWeapon` |
| `ArtilleryShellUpgrade` | 8 | `CollapseTargetCompatibility1` · `Concussion_Heavy` · `Grenade` · `HeavyBomb` |
| `AsianChaosMine` | 2 | `CannonAP_Light` · `Chemical_Heavy` |


_... and 1065 more._


## W6 — effect warheads declared LOCALLY (687 vs ratchet 687)

| weapon | nodes | first three |
|---|---|---|
| `A10CarrierMissiles_AA` | 1 | `Warhead@EffectAir: CreateEffect` |
| `AAGunBoatFlak` | 1 | `Warhead@EffectAir: CreateEffect` |
| `ASDFKamikazeExplosion` | 1 | `Warhead@Effect: CreateEffect` |
| `ATMine` | 3 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` · `Warhead@Concrete: DamagesConcrete` |
| `Aphid_AA` | 1 | `Warhead@EffectAir: CreateEffect` |
| `ArmoredCarMG` | 1 | `Warhead@Effect: CreateEffect` |
| `ArtilleryExplode` | 1 | `Warhead@2Eff: CreateEffect` |
| `ArtilleryShell` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianChaosSuperweapon` | 1 | `Warhead@1: CreateEffect` |
| `AsianChaosTurret` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianChemical` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianChemicalBombs` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianHarbingerPlasma` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianIonBeamMini` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianMaidenBow` | 2 | `Warhead@Effect: CreateEffect` · `Warhead@EffectAir: CreateEffect` |
| `AsianOilBombFragments` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianPhotonCannon` | 2 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge: LeaveSmudge` |
| `AsianSmallOilBomb` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSmallTorpedo` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSniper` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSniperAP` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSubmarineBomb` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianTSIonCannon` | 2 | `Warhead@3Smu_area: LeaveSmudge` · `Warhead@Effect: CreateEffect` |
| `AsianTurretPlasma` | 1 | `Warhead@Effect: CreateEffect` |
| `AthenaLaser` | 9 | `Warhead@Effect: CreateEffect` · `Warhead@Effect2: CreateEffect` · `Warhead@Effect3: CreateEffect` |
| `AtreusMG` | 1 | `Warhead@Effect: CreateEffect` |
| `BCYamatoCannon` | 1 | `Warhead@Effect: CreateEffect` |
| `BHBombs` | 1 | `Warhead@3Eff: CreateEffect` |
| `BHRedDarts` | 2 | `Warhead@Effect: CreateEffect` · `Warhead@EffectAir: CreateEffect` |
| `BallistaMultiShot` | 1 | `Warhead@Effect: CreateEffect` |
| `BallistaMultiShotEnergized` | 1 | `Warhead@Effect: CreateEffect` |
| `BarrelExplode` | 2 | `Warhead@2Eff: CreateEffect` · `Warhead@Smu: LeaveSmudge` |
| `BehemothShoot` | 3 | `Warhead@Effect: CreateEffect` · `Warhead@Effect2: CreateEffect` · `Warhead@EffectAir: CreateEffect` |
| `BigChemSpray` | 1 | `Warhead@3Eff: CreateEffect` |
| `BigFlamer` | 1 | `Warhead@Glow: GlowImpact` |
| `BigFlamer2` | 1 | `Warhead@Glow: GlowImpact` |
| `BlackEagleThunderboltMissiles` | 6 | `Warhead@Effect: CreateEffect` · `Warhead@Smudge1: LeaveSmudge` · `Warhead@Smudge2: LeaveSmudge` |
| `BlackHoleSuck` | 1 | `Warhead@Effect: CreateEffect` |
| `BoatMissile` | 2 | `Warhead@3Eff: CreateEffect` · `Warhead@4EffAir: CreateEffect` |
| `BuggyPlasmaGrenade` | 1 | `Warhead@Effect: CreateEffect` |


_... and 647 more._


**FAIL — W2, W5 rose above baseline.** A weapon was given a second warhead, projectile or effect. The law allows exactly three inherits and one main.
