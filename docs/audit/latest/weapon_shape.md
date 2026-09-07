# Weapon shape ΓÇö the ONE-WARHEAD / THREE-INHERIT law

**Maintainer ruling, 2026-09-06.** Every concrete weapon ends with exactly three inherits ΓÇö `^Warhead_*`, `^Projectile_*`, `^Effect_*` ΓÇö one main warhead, and no effect warheads of its own. Mechanic warheads (`FireShrapnel`, `GrantExternalCondition`) and the `*Percentage` / `*FriendlyFire` / `*ExtraDamage` halves of one main are NOT violations.

Γ¢ö This **repeals the exemption** in `tools/audit/intentional_composites.py`. Its 224 entries are no longer 'reviewed, keep' ΓÇö they are the worklist. The registry data stays useful: it says which mains someone chose on purpose.

concrete weapons with inherits: **2061**

| check | what | count | ratchet |
|---|---|--:|--:|
| W1 | more than 3 inherits | **576** | 576 |
| W2 | two or more `^Warhead_*` inherits | **210** | 210 |
| W3 | two or more `^Projectile_*` inherits | **12** | 12 |
| W4 | two or more `^Effect_*` inherits | **51** | 51 |
| W5 | more than one resolved MAIN warhead | **389** | 389 |
| W6 | effect warheads declared LOCALLY | **694** | 694 |

| I7 informational ΓÇö missing template | weapons |
|---|--:|
| no `^Effect_*` inherit | 1244 |
| no `^Projectile_*` inherit | 1362 |
| no `^Warhead_*` inherit | 1156 |

_I7 is a REVIEW QUEUE, not a defect count ΓÇö an instant or utility weapon may legitimately have no projectile. Do not ratchet it without a per-weapon pass._


## W1 ΓÇö more than 3 inherits (576 vs ratchet 576)

| weapon | inherits | first four |
|---|---|---|
| `105mmThermobaric` | 5 | `^Compatibility_Flame_MediumFlat` ┬╖ `^Warhead_Flame_Medium` ┬╖ `^Projectile_Flame_Medium` ┬╖ `^Effect_Flame_Medium` |
| `110mm_Gun` | 8 | `^Compatibility_CannonAP_LightFlat` ┬╖ `^Warhead_CannonHE_Heavy` ┬╖ `^Projectile_Shell_Heavy` ┬╖ `^Effect_CannonHE_Heavy` |
| `120mmDualHV` | 4 | `^Warhead_CannonHE_Heavy` ┬╖ `^Projectile_Shell_Heavy` ┬╖ `^Effect_CannonHE_Heavy` ┬╖ `^HVProjectile` |
| `120mmHV` | 4 | `^Warhead_CannonHE_Medium` ┬╖ `^Projectile_Shell_Medium` ┬╖ `^Effect_CannonHE_Medium` ┬╖ `^HVProjectile` |
| `120mm_cobra` | 7 | `^Compatibility_CannonAP_LightFlat` ┬╖ `^Warhead_Demolition_Light` ┬╖ `^Warhead_Concussion_Medium` ┬╖ `^Warhead_CannonAP_Light` |
| `120mm_td` | 5 | `^Compatibility_CannonHE_MediumFlat` ┬╖ `^MediumChemicalWeapon` ┬╖ `^LightChemicalWeapon` ┬╖ `^D2K_Cannon` |
| `12MissilesSpawnerScud` | 7 | `^Warhead_Demolition_Heavy` ┬╖ `^Warhead_Flame_Medium` ┬╖ `^Projectile_Flame_Medium` ┬╖ `^Effect_Flame_Medium` |
| `155mm` | 4 | `^Warhead_Concussion_Heavy` ┬╖ `^HeavyCannon` ┬╖ `^ShrapnelWeapon` ┬╖ `^Grenade` |
| `25mm` | 9 | `^Compatibility_CannonHE_MediumFlat` ┬╖ `^Warhead_CannonHE_Medium` ┬╖ `^Projectile_Shell_Medium` ┬╖ `^Effect_CannonHE_Medium` |
| `8Inch` | 4 | `^Compatibility_Demolition_HeavyFlat` ┬╖ `^Warhead_Demolition_Heavy` ┬╖ `^Projectile_Grenade_Light` ┬╖ `^Effect_Demolition_Light` |
| `APCGun` | 5 | `^Compatibility_Flak_MediumFlat` ┬╖ `^Warhead_Bullet_Medium` ┬╖ `^Warhead_Flak_Medium` ┬╖ `^Projectile_Flak_Medium` |
| `APCGunAllies` | 5 | `^Compatibility_Flak_MediumFlat` ┬╖ `^Warhead_Bullet_Medium` ┬╖ `^Warhead_Flak_Medium` ┬╖ `^Projectile_Flak_Medium` |
| `APTusk` | 5 | `^Warhead_MissileAP_Heavy` ┬╖ `^TankDestroyerCannon` ┬╖ `^Grenade` ┬╖ `^FlakWeapon` |
| `ASDFGun2` | 4 | `^Warhead_Railgun_Heavy` ┬╖ `^Projectile_Railgun_Heavy` ┬╖ `^Effect_Railgun_Heavy` ┬╖ `ASDFGun` |
| `ASDFKamikazeExplosion` | 4 | `^Warhead_Demolition_Heavy` ┬╖ `^Warhead_Concussion_Medium` ┬╖ `^Effect_Concussion_Medium` ┬╖ `^Projectile_Grenade_Light` |
| `AlliedTankDestroyerCannon` | 4 | `^Warhead_CannonHE_Medium` ┬╖ `^Warhead_CannonAP_Light` ┬╖ `^Projectile_Shell_Light` ┬╖ `^Effect_CannonAP_Light` |
| `AphidCryo_AA` | 4 | `^Warhead_CryoBlast_Medium` ┬╖ `^Warhead_MissileCryo_Heavy` ┬╖ `^Projectile_Missile_Heavy` ┬╖ `^Effect_Cryo` |
| `Aphid_AA` | 4 | `^Warhead_Concussion_Medium` ┬╖ `^Warhead_MissileHE_Heavy` ┬╖ `^Projectile_Missile_Heavy` ┬╖ `^Effect_MissileHE_Heavy` |
| `ArcherArtilleryShell` | 6 | `^Warhead_Concussion_Heavy` ┬╖ `^MediumCannon` ┬╖ `^HeavyCannon` ┬╖ `^MediumFlameWeapon` |
| `ArmoredCarMG` | 9 | `^Warhead_Bullet_Medium` ┬╖ `^ArrowWeapon` ┬╖ `^TankDestroyerCannon` ┬╖ `^SmallArms` |
| `ArtilleryShell` | 5 | `^Compatibility_Concussion_MediumFlat` ┬╖ `^Warhead_Demolition_Light` ┬╖ `^Warhead_Concussion_Medium` ┬╖ `^Projectile_Grenade_Light` |
| `ArtilleryShellUpgrade` | 7 | `^Warhead_Concussion_Heavy` ┬╖ `^Grenade` ┬╖ `^ShrapnelWeapon` ┬╖ `^MediumChemicalWeapon` |
| `AsianChaosMine` | 5 | `AsianChaosTurret` ┬╖ `AsianTankMine` ┬╖ `^Warhead_Chemical_Heavy` ┬╖ `^Projectile_Chem_Heavy` |
| `AsianChemical` | 7 | `^Compatibility_Chemical_MediumFlat` ┬╖ `^LightChemicalWeapon` ┬╖ `^MediumChemicalWeapon` ┬╖ `^HeavyChemicalWeapon` |
| `AsianGrenade` | 4 | `^Compatibility_Concussion_MediumFlat` ┬╖ `^Warhead_Concussion_Medium` ┬╖ `^Effect_Concussion_Medium` ┬╖ `^RA2MediumCannon` |
| `AsianHarbingerPlasma` | 13 | `^Compatibility_Plasma_MediumFlat` ┬╖ `^Warhead_Plasma_Medium` ┬╖ `^Warhead_CannonHE_Medium` ┬╖ `^Projectile_Shell_Medium` |
| `AsianLynxTankCannon` | 7 | `^Compatibility_CannonHE_MediumFlat` ┬╖ `^Grenade` ┬╖ `^ShrapnelWeapon` ┬╖ `^LightFlameWeapon` |
| `AsianMLRS` | 5 | `^Compatibility_MissileAA_MediumFlat` ┬╖ `^HeavyMissile` ┬╖ `^FlakWeapon` ┬╖ `^RA2Grenade` |
| `AsianMaidenBow` | 4 | `^Compatibility_Arrow_LightFlat` ┬╖ `AsianPhotonCannon` ┬╖ `^Grenade` ┬╖ `^ArrowWeapon` |
| `AsianNinjaStar` | 4 | `^Warhead_Melee_Medium` ┬╖ `^Projectile_InstantHit` ┬╖ `^Effect_Melee_Medium` ┬╖ `^Effect_Bullet_Medium_RA2` |
| `AsianPelicanMissile` | 7 | `^Compatibility_MissileAP_HeavyFlat` ┬╖ `^Warhead_Concussion_Light` ┬╖ `^Warhead_MissileAP_Heavy` ┬╖ `^Projectile_Missile_Heavy` |
| `AsianPhoenixRocket` | 6 | `^Warhead_Flame_Medium` ┬╖ `^Warhead_Demolition_Light` ┬╖ `^Projectile_Flame_Medium` ┬╖ `^Effect_Flame_Medium` |
| `AsianPhotonCannon` | 5 | `^Compatibility_Plasma_HeavyFlat` ┬╖ `^MediumMissile` ┬╖ `^FlakWeapon` ┬╖ `^TeslaWeapon` |
| `AsianPulverizerGatling` | 6 | `^Compatibility_Bullet_MediumFlat` ┬╖ `^Warhead_Bullet_Light` ┬╖ `^Warhead_CannonHE_Heavy` ┬╖ `^Projectile_Shell_Heavy` |
| `AsianRailTank` | 4 | `^Warhead_Railgun_Heavy` ┬╖ `^Projectile_Railgun_Heavy` ┬╖ `^Effect_Railgun_Heavy` ┬╖ `^Effect_Clsn_Medium_RA2` |
| `AsianRailgun` | 4 | `^Warhead_Railgun_Heavy` ┬╖ `^Projectile_Railgun_Heavy` ┬╖ `^Effect_Railgun_Heavy` ┬╖ `^Effect_Explosion_Medium_RA2` |
| `AsianSinglePlasma` | 12 | `^Compatibility_Plasma_HeavyFlat` ┬╖ `^Warhead_CannonHE_Medium` ┬╖ `^Projectile_Shell_Medium` ┬╖ `^Effect_CannonHE_Medium` |
| `AsianSmallTorpedo` | 4 | `^Compatibility_MissileAP_HeavyFlat` ┬╖ `^RA2Grenade` ┬╖ `^RA2HeavyMissile` ┬╖ `^Effect_Watersplash_Large_RA2` |
| `AsianSniper` | 8 | `^Warhead_Bullet_Heavy` ┬╖ `^Projectile_Shell_Heavy` ┬╖ `^Effect_CannonHE_Heavy` ┬╖ `^MediumMissile` |
| `AsianSniperLockdown` | 4 | `^Warhead_Tesla_Super` ┬╖ `^Projectile_Lightning_Super` ┬╖ `^Effect_Tesla_Super` ┬╖ `AsianSniperAP` |


_... and 536 more._


## W2 ΓÇö two or more `^Warhead_*` inherits (210 vs ratchet 210)

| weapon | warhead templates |
|---|---|
| `110mm_Gun` | `^Warhead_CannonHE_Heavy` ┬╖ `^Warhead_CannonAP_Light` |
| `120mm_cobra` | `^Warhead_Demolition_Light` ┬╖ `^Warhead_Concussion_Medium` ┬╖ `^Warhead_CannonAP_Light` |
| `12MissilesSpawnerScud` | `^Warhead_Demolition_Heavy` ┬╖ `^Warhead_Flame_Medium` |
| `APCGun` | `^Warhead_Bullet_Medium` ┬╖ `^Warhead_Flak_Medium` |
| `APCGunAllies` | `^Warhead_Bullet_Medium` ┬╖ `^Warhead_Flak_Medium` |
| `ASDFKamikazeExplosion` | `^Warhead_Demolition_Heavy` ┬╖ `^Warhead_Concussion_Medium` |
| `AlliedTankDestroyerCannon` | `^Warhead_CannonHE_Medium` ┬╖ `^Warhead_CannonAP_Light` |
| `AphidCryo_AA` | `^Warhead_CryoBlast_Medium` ┬╖ `^Warhead_MissileCryo_Heavy` |
| `Aphid_AA` | `^Warhead_Concussion_Medium` ┬╖ `^Warhead_MissileHE_Heavy` |
| `ArtilleryShell` | `^Warhead_Demolition_Light` ┬╖ `^Warhead_Concussion_Medium` |
| `AsianHarbingerPlasma` | `^Warhead_Plasma_Medium` ┬╖ `^Warhead_CannonHE_Medium` |
| `AsianPelicanMissile` | `^Warhead_Concussion_Light` ┬╖ `^Warhead_MissileAP_Heavy` |
| `AsianPhoenixRocket` | `^Warhead_Flame_Medium` ┬╖ `^Warhead_Demolition_Light` |
| `AsianPulverizerGatling` | `^Warhead_Bullet_Light` ┬╖ `^Warhead_CannonHE_Heavy` |
| `BTRMachineGun` | `^Warhead_Bullet_Light` ┬╖ `^Warhead_Bullet_Medium` |
| `BTRTeslaMachineGun` | `^Warhead_MissileAP_Light` ┬╖ `^Warhead_Tesla_Heavy` |
| `BigShieeTusk` | `^Warhead_MissileHE_Heavy` ┬╖ `^Warhead_Concussion_Medium` |
| `BlackEagleMissiles` | `^Warhead_Demolition_Light` ┬╖ `^Warhead_Demolition_Heavy` |
| `CHGuardRifle` | `^Warhead_Bullet_Light` ┬╖ `^Warhead_Bullet_Medium` |
| `CabalCyborgChaingun` | `^Warhead_Bullet_Light` ┬╖ `^Warhead_Bullet_Medium` |
| `CabalHeavyReaperMissiles` | `^Warhead_MissileHE_Medium` ┬╖ `^Warhead_MissileHE_Heavy` ┬╖ `^Warhead_Demolition_Light` ┬╖ `^Warhead_Concussion_Medium` |
| `CabalHeavyReaperMissiles_AA` | `^Warhead_MissileHE_Medium` ┬╖ `^Warhead_MissileHE_Heavy` ┬╖ `^Warhead_Demolition_Light` ┬╖ `^Warhead_Concussion_Medium` |
| `CabalLegionGun` | `^Warhead_Bullet_Light` ┬╖ `^Warhead_Laser_Heavy` |
| `CabalMagicNuke` | `^Warhead_Tesla_Heavy` ┬╖ `^Warhead_Tesla_Super` |
| `CabalMantisGun` | `^Warhead_Bullet_Light` ┬╖ `^Warhead_Laser_Heavy` |
| `CabalOverkillDroneLaser` | `^Warhead_Bullet_Light` ┬╖ `^Warhead_Laser_Heavy` |
| `CabalReaperMissiles` | `^Warhead_MissileHE_Light` ┬╖ `^Warhead_MissileHE_Medium` ┬╖ `^Warhead_Demolition_Light` ┬╖ `^Warhead_Concussion_Medium` |
| `CabalReaperMissiles_AA` | `^Warhead_MissileHE_Light` ┬╖ `^Warhead_MissileHE_Medium` ┬╖ `^Warhead_Demolition_Light` ┬╖ `^Warhead_Concussion_Medium` |
| `CabalRocketCyborgRockets` | `^Warhead_MissileHE_Light` ┬╖ `^Warhead_MissileHE_Medium` |
| `CabalRocketCyborgRocketsUpgraded` | `^Warhead_MissileHE_Light` ┬╖ `^Warhead_MissileHE_Medium` |
| `ConscriptMolotov` | `^Warhead_Demolition_Light` ┬╖ `^Warhead_Flame_Light` |
| `CorsairFlash` | `^Warhead_Flak_Medium` ┬╖ `^Warhead_Demolition_Light` |
| `D2K_155mm3` | `^Warhead_Demolition_Light` ┬╖ `^Warhead_Demolition_Heavy` ┬╖ `^Warhead_Concussion_Medium` |
| `D2K_155mm_turret` | `^Warhead_Demolition_Light` ┬╖ `^Warhead_Demolition_Heavy` ┬╖ `^Warhead_Concussion_Medium` |
| `D2K_APC_Rocket` | `^Warhead_MissileAP_Light` ┬╖ `^Warhead_MissileAP_Medium` |
| `D2K_Rocket_Trooper` | `^Warhead_MissileAP_Light` ┬╖ `^Warhead_MissileAP_Medium` ┬╖ `^Warhead_MissileAP_Heavy` |
| `D2K_Rocket_Trooper1` | `^Warhead_Flak_Medium` ┬╖ `^Warhead_MissileAP_Light` ┬╖ `^Warhead_MissileAP_Heavy` |
| `D2K_Rocket_Trooper2` | `^Warhead_Demolition_Light` ┬╖ `^Warhead_Railgun_Heavy` ┬╖ `^Warhead_CannonHE_Medium` |
| `DalekCannon` | `^Warhead_Tesla_Heavy` ┬╖ `^Warhead_Laser_Heavy` |
| `Dune_SiegeMortar` | `^Warhead_Demolition_Light` ┬╖ `^Warhead_Concussion_Medium` ┬╖ `^Warhead_CannonAP_Light` |


_... and 170 more._


## W3 ΓÇö two or more `^Projectile_*` inherits (12 vs ratchet 12)

| weapon | projectile templates |
|---|---|
| `110mm_Gun` | `^Projectile_Shell_Heavy` ┬╖ `^Projectile_Shell_Light` |
| `Flamethrower` | `^Projectile_Flame_Light` ┬╖ `^Projectile_Flame_Light` |
| `HeavyIxianCombatTankCannon` | `^Projectile_Shell_Heavy` ┬╖ `^Projectile_Shell_Light` |
| `IxianCombatTankCannon` | `^Projectile_Shell_Heavy` ┬╖ `^Projectile_Shell_Light` |
| `LatinMonkeyGrenade1` | `^Projectile_Grenade_Light` ┬╖ `^Projectile_Shell_Heavy` |
| `RashidanGun_upgrade` | `^Projectile_Shell_Heavy` ┬╖ `^Projectile_Missile_Heavy` |
| `ReaperGrenade` | `^Projectile_Grenade_Light` ┬╖ `^Projectile_Shell_Heavy` |
| `TS70mmTur` | `^Projectile_Shell_Medium` ┬╖ `^Projectile_Shell_Light` |
| `YakovlevCannon` | `^Projectile_Shell_Heavy` ┬╖ `^Projectile_Shell_Light` |
| `YakovlevCannon_elite` | `^Projectile_Shell_Heavy` ┬╖ `^Projectile_Shell_Light` |
| `ra120mm2Thermobaric` | `^Projectile_Shell_Heavy` ┬╖ `^Projectile_Flame_Heavy` |
| `ra120mmThermobaric` | `^Projectile_Shell_Heavy` ┬╖ `^Projectile_Flame_Heavy` |


## W4 ΓÇö two or more `^Effect_*` inherits (51 vs ratchet 51)

| weapon | effect templates |
|---|---|
| `110mm_Gun` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_CannonAP_Light` |
| `12MissilesSpawnerScud` | `^Effect_Flame_Medium` ┬╖ `^Effect_Demolition_Heavy` |
| `AsianHarbingerPlasma` | `^Effect_CannonHE_Medium` ┬╖ `^Effect_Apoc_Explosion_RA2` |
| `AsianNinjaStar` | `^Effect_Melee_Medium` ┬╖ `^Effect_Bullet_Medium_RA2` |
| `AsianPelicanMissile` | `^Effect_MissileAP_Heavy` ┬╖ `^Effect_Grey_Explosion_Small_RA2` |
| `AsianPhoenixRocket` | `^Effect_Flame_Medium` ┬╖ `^Effect_Explosion_Large_RA2` |
| `AsianRailTank` | `^Effect_Railgun_Heavy` ┬╖ `^Effect_Clsn_Medium_RA2` |
| `AsianRailgun` | `^Effect_Railgun_Heavy` ┬╖ `^Effect_Explosion_Medium_RA2` |
| `AsianSinglePlasma` | `^Effect_CannonHE_Medium` ┬╖ `^Effect_Apoc_Explosion_RA2` |
| `AsianSubmarineBomb` | `^Effect_Demolition_Heavy` ┬╖ `^Effect_Twlt_Large_RA2` |
| `Flamethrower` | `^Effect_Flame_Light` ┬╖ `^Effect_Flame_Light` |
| `HeavyIxianCombatTankCannon` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_CannonAP_Light` |
| `IxianCombatTankCannon` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_CannonAP_Light` |
| `JapanesePlasmaBomb` | `^Effect_Flame_Heavy` ┬╖ `^Effect_Demolition_Heavy` |
| `KotinCannonNuclearShell` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Nuclear_Super` |
| `LatinMonkeyGrenade1` | `^Effect_Concussion_Medium` ┬╖ `^Effect_CannonHE_Heavy` |
| `LunarNaxiJadgDestroyer` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Concussion_Medium` |
| `MissileAttackRobotGun` | `^Effect_MissileAP_Medium` ┬╖ `^Effect_Grey_Explosion_Small_RA2` |
| `MonsterTank120mm` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Nuclear_Super` |
| `MonsterTank120mmInferno` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Flame_Heavy` |
| `NaxBrummbarArty` | `^Effect_Concussion_Medium` ┬╖ `^Effect_CannonHE_Heavy` |
| `NaxGrilleArty` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Concussion_Medium` |
| `NaxiCowDrop` | `^Effect_Demolition_Heavy` ┬╖ `^Effect_Clsn_Medium_RA2` |
| `NaxiJadgDestroyer` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Concussion_Medium` |
| `OrionRailgun` | `^Effect_Railgun_Heavy` ┬╖ `^Effect_Explosion_Large_RA2` |
| `RA2FreedomAK47` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Bullet_Light_RA2` |
| `RA2GrandCannonWeapon` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Clsn_Medium_RA2` |
| `RA2MortarBike` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Explosion_Large_RA2` |
| `RashidanGun_upgrade` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_MissileHE_Heavy` |
| `ReaperGrenade` | `^Effect_Concussion_Medium` ┬╖ `^Effect_CannonHE_Heavy` |
| `SCUDTesla` | `^Effect_Tesla_Heavy` ┬╖ `^Effect_Kirov_Tesla_RA2` |
| `TS120mmx` | `^Effect_CannonHE_Medium` ┬╖ `^Effect_Concussion_Medium` |
| `TS70mmTur` | `^Effect_CannonHE_Medium` ┬╖ `^Effect_CannonAP_Light` |
| `TSGrenade` | `^Effect_CannonHE_Medium` ┬╖ `^Effect_Concussion_Medium` |
| `TSScoopDualTur` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Concussion_Medium` |
| `TorpTubeThermobaric` | `^Effect_Nuclear_Super` ┬╖ `^Effect_MissileAP_Heavy` |
| `YakovlevCannon` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_CannonAP_Light` |
| `YakovlevCannon_elite` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_CannonAP_Light` |
| `bigshieemortar` | `^Effect_Flame_Medium` ┬╖ `^Effect_Explosion_Large_RA2` |
| `ra120mm2Thermobaric` | `^Effect_CannonHE_Heavy` ┬╖ `^Effect_Flame_Heavy` |


_... and 11 more._


## W5 ΓÇö more than one resolved MAIN warhead (389 vs ratchet 389)

| weapon | mains | which |
|---|---|---|
| `12MissilesSpawnerScud` | 4 | `Demolition_Heavy` ┬╖ `Demolition_Light` ┬╖ `Flame_Medium` ┬╖ `MissileAP_Heavy` |
| `25mmWaveforce` | 2 | `CannonHE_Medium` ┬╖ `Railgun_Heavy` |
| `AAGunBoatFlak` | 3 | `Bullet_Light` ┬╖ `Flak_Medium` ┬╖ `Flak_MediumFlatCompatibility` |
| `AAGunBoatFlak_elite` | 3 | `Bullet_Light` ┬╖ `Flak_Medium` ┬╖ `Flak_MediumFlatCompatibility` |
| `ATMine` | 2 | `ATMineDemolition_Light` ┬╖ `Demolition_Light` |
| `AlliedTankDestroyerCannon` | 2 | `CannonAP_Light` ┬╖ `CannonHE_Medium` |
| `AphidCryo_AA` | 2 | `CryoBlast_Medium` ┬╖ `MissileCryo_Heavy` |
| `Aphid_AA` | 2 | `Concussion_Medium` ┬╖ `MissileHE_Heavy` |
| `ArcherArtilleryShell` | 2 | `CollapseTargetCompatibility1` ┬╖ `Concussion_Heavy` |
| `ArmoredCarMGAAWaveforce` | 5 | `Bullet_Light` ┬╖ `Bullet_Medium` ┬╖ `CannonAP_Light` ┬╖ `CannonHE_Medium` |
| `ArmoredCarMGWaveforce` | 2 | `Bullet_Medium` ┬╖ `Railgun_Heavy` |
| `ArmoredCarMG_AA` | 4 | `Bullet_Light` ┬╖ `Bullet_Medium` ┬╖ `CannonAP_Light` ┬╖ `CannonHE_Medium` |
| `ArtilleryShellUpgrade` | 2 | `CollapseTargetCompatibility1` ┬╖ `Concussion_Heavy` |
| `AsianChaosMine` | 2 | `CannonAP_Light` ┬╖ `Chemical_Heavy` |
| `AsianPhoenixRocket` | 3 | `Demolition_Light` ┬╖ `Flame_Medium` ┬╖ `MissileAP_Heavy` |
| `AsianPhoenixRocket_elite` | 3 | `Demolition_Light` ┬╖ `Flame_Medium` ┬╖ `MissileAP_Heavy` |
| `AsianSniper` | 3 | `Bullet_Heavy` ┬╖ `SniperChaingun` ┬╖ `SniperSmallArms` |
| `AsianSniperAP` | 4 | `Bullet_Heavy` ┬╖ `Bullet_Medium` ┬╖ `SniperChaingun` ┬╖ `SniperSmallArms` |
| `AsianSniperLockdown` | 6 | `Bullet_Heavy` ┬╖ `Bullet_Medium` ┬╖ `SniperChaingun` ┬╖ `SniperFlak` |
| `AsianTSIonCannon` | 4 | `IonCannon` ┬╖ `TeslaChargedWeapon` ┬╖ `TeslaWeapon` ┬╖ `Tesla_Super` |
| `Atomic` | 2 | `Nuclear_Super` ┬╖ `Tesla_Super` |
| `AtreusMG` | 2 | `Bullet_Medium` ┬╖ `CannonHE_Heavy` |
| `BCLaser` | 2 | `CannonHE_Heavy` ┬╖ `Laser_HeavyFlatCompatibility` |
| `BCYamatoCannon` | 2 | `CannonHE_Heavy` ┬╖ `Plasma_HeavyFlatCompatibility` |
| `BallistaMultiShot` | 2 | `Arrow_Medium` ┬╖ `CollapseTargetCompatibility1` |
| `BallistaSingleShotAirEnergized` | 4 | `Arrow_Light` ┬╖ `Arrow_LightFlatCompatibility` ┬╖ `CannonHE_Medium` ┬╖ `MissileAP_Light` |
| `BallistaTowerMultiShot` | 2 | `Arrow_Medium` ┬╖ `CollapseTargetCompatibility1` |
| `BarrelExplode` | 2 | `1Dam` ┬╖ `Demolition_Light` |
| `BikeRockets` | 2 | `CollapseTargetCompatibility1` ┬╖ `MissileAP_Medium` |
| `BlackHandLaser` | 2 | `LaserHeavyGroundRemainder` ┬╖ `Laser_Heavy` |
| `BoxerCannon_AA` | 4 | `Bullet_Light` ┬╖ `Bullet_Medium` ┬╖ `CannonHE_Medium` ┬╖ `Flak_MediumFlatCompatibility` |
| `BroodweaverLeech` | 2 | `ExtraHealing` ┬╖ `HealingWeapon` |
| `CHFlameBlue` | 2 | `1Dam` ┬╖ `Flame_Medium` |
| `CabalAscendedRockets` | 2 | `MissileHE_Heavy` ┬╖ `MissileHE_HeavyGroundBonus` |
| `CabalEngineerRepairBeam` | 2 | `ExtraRepair` ┬╖ `RepairWeapon` |
| `CabalMagicNuke` | 8 | `10Dam_areanuke3` ┬╖ `11Dam_areanuke3` ┬╖ `1Dam_impact` ┬╖ `4Dam_areanuke1` |
| `ChemRockets` | 2 | `ChemRocketCompatibility` ┬╖ `Chemical_Light` |
| `ChemRocketsExplosion` | 2 | `ChemRocketCompatibility` ┬╖ `Chemical_Light` |
| `ChemTibAtomic` | 2 | `Nuclear_Super` ┬╖ `Tesla_Super` |
| `Combat_Tank_F_Sound` | 2 | `1Dam` ┬╖ `2Dam` |


_... and 349 more._


## W6 ΓÇö effect warheads declared LOCALLY (694 vs ratchet 694)

| weapon | nodes | first three |
|---|---|---|
| `105mm` | 1 | `Warhead@Effect: CreateEffect` |
| `105mmThermobaric` | 1 | `Warhead@Effect: CreateEffect` |
| `120mm` | 1 | `Warhead@Effect: CreateEffect` |
| `120mmHV` | 1 | `Warhead@Effect: CreateEffect` |
| `12MissilesSpawnerScud` | 1 | `Warhead@Effect: CreateEffect` |
| `155mm` | 1 | `Warhead@Effect: CreateEffect` |
| `155mmCryo` | 1 | `Warhead@Effect: CreateEffect` |
| `2100Tanktrap` | 1 | `Warhead@Smu: LeaveSmudge` |
| `227mm` | 2 | `Warhead@Effect: CreateEffect` ┬╖ `Warhead@EffectWater: CreateEffect` |
| `25mm` | 2 | `Warhead@Effect: CreateEffect` ┬╖ `Warhead@EffectAir: CreateEffect` |
| `70mm` | 1 | `Warhead@Effect: CreateEffect` |
| `90mm` | 1 | `Warhead@Effect: CreateEffect` |
| `A10CarrierMissiles_AA` | 1 | `Warhead@EffectAir: CreateEffect` |
| `AAGunBoatFlak` | 1 | `Warhead@EffectAir: CreateEffect` |
| `ASDFKamikazeExplosion` | 1 | `Warhead@Effect: CreateEffect` |
| `ATMine` | 3 | `Warhead@Effect: CreateEffect` ┬╖ `Warhead@Smudge: LeaveSmudge` ┬╖ `Warhead@Concrete: DamagesConcrete` |
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
| `AsianMaidenBow` | 2 | `Warhead@Effect: CreateEffect` ┬╖ `Warhead@EffectAir: CreateEffect` |
| `AsianOilBombFragments` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianPhotonCannon` | 2 | `Warhead@Effect: CreateEffect` ┬╖ `Warhead@Smudge: LeaveSmudge` |
| `AsianSmallOilBomb` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSmallTorpedo` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSniper` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSniperAP` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianSubmarineBomb` | 1 | `Warhead@Effect: CreateEffect` |
| `AsianTSIonCannon` | 2 | `Warhead@3Smu_area: LeaveSmudge` ┬╖ `Warhead@Effect: CreateEffect` |
| `AsianTurretPlasma` | 1 | `Warhead@Effect: CreateEffect` |
| `AthenaLaser` | 9 | `Warhead@Effect: CreateEffect` ┬╖ `Warhead@Effect2: CreateEffect` ┬╖ `Warhead@Effect3: CreateEffect` |
| `AtreusMG` | 1 | `Warhead@Effect: CreateEffect` |
| `BCYamatoCannon` | 1 | `Warhead@Effect: CreateEffect` |
| `BHBombs` | 1 | `Warhead@3Eff: CreateEffect` |


_... and 654 more._


_all buckets at or below their ratchets_ ΓÇö this is the pre-existing conversion backlog. **Lower each baseline as you convert; never raise one.**
