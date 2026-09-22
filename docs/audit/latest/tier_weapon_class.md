# audit_tier_weapon_class — 34 of 1153 classifiable weapons break the TYPES x LEVELS budget

Historical budget diagnostic only; DESIGN section11b.1 one-main law takes precedence.

Historical budget shapes (not one-main compliance):
   1068  1 type, 1 level - squarely in tier
     32  2 types, 1 level - lore hybrid
     16  2 types, 2 adjacent levels - hybrid AND between-tier (budget 4)
      3  1 type, 2 ADJACENT levels - between-tier mix

   1042  weapons unclassified — at least one main lacks a recognized Family_Level; this is not a balance or structural pass
     25  continuous-profile weapons — discrete tier unclassified; runtime heaviness is checked separately
  Continuous identities: 120mm_cobra, 120mm_cobra_deploy, 120mm_python, 120mm_python_deploy, AlliedTankDestroyerCannon, NaxiAntiTankCannon, NaxiAntiTankCannonCorrosion, NaxiAntiTankCannon_elite, NaxiHetzerDestroyer, NaxiHetzerDestroyerCorrosion, NaxiHetzerDestroyer_elite, RA2120xmm, RA2120xmm_elite, RA2sabot, RA2sabot_elite, SkyHawkCannon, TS90mm, TS90mmDep, TSHighVelocity, TSHighVelocity2, TSHighVelocityTur, TSLaser90mm, TSLaser90mmDep, corrino_buggy_gun, ra1_allies_gunboat_cannon

VIOLATIONS by shape:
     19  3 LEVELS
     11  3 TYPES
      4  NON-ADJACENT levels

| weapon | problem | main warheads |
|---|---|---|
| 12MissilesSpawnerScud | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Demolition_Heavy, Demolition_Light, Flame_Medium, MissileAP_Heavy |
| ArmoredCarMGAAWaveforce | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, CannonAP_Light, CannonHE_Medium, Railgun_Heavy |
| ArmoredCarMG_AA | 3 TYPES (Bullet, CannonAP, CannonHE) - max is 2 | Bullet_Light, Bullet_Medium, CannonAP_Light, CannonHE_Medium |
| AsianChaosMine | NON-ADJACENT levels (Heavy+Light) | CannonAP_Light, Chemical_Heavy |
| AsianPhoenixRocket | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Demolition_Light, Flame_Medium, MissileAP_Heavy |
| AsianPhoenixRocket_elite | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Demolition_Light, Flame_Medium, MissileAP_Heavy |
| D2K_Rocket_Trooper1 | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Flak_Medium, MissileAP_Heavy, MissileAP_Light |
| D2K_Rocket_Trooper2 | 3 LEVELS (Heavy+Light+Medium) - max is 2 | CannonHE_Medium, Demolition_Light, Railgun_Heavy |
| D2K_SiegeQuad | 3 LEVELS (Heavy+Light+Medium) - max is 2 | CannonHE_Medium, Concussion_Medium, Demolition_Heavy, Demolition_Light |
| Lunar_AmplifiedBeetleLaser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| Lunar_AmplifiedTank2Laser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| Lunar_YellowBeetleLaser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| Lunar_YellowTank2Laser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| NaxiBeetleLaser_AA_elite | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| NaxiMP40 | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Medium, CannonHE_Heavy, Concussion_Light |
| NaxiMP40_elite | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Medium, CannonHE_Heavy, Concussion_Light |
| NaxiTank2Laser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| OIBigPlasmaCannon | 3 TYPES (CannonHE, Railgun, Tesla) - max is 2 | CannonHE_Heavy, Railgun_Heavy, Tesla_Heavy |
| RA2AsianShotgunFanatic1 | 3 TYPES (Bullet, Concussion, Demolition) - max is 2 | Bullet_Medium, Concussion_Medium, Demolition_Light |
| RA2AsianShotgunFanatic2 | 3 TYPES (Bullet, Concussion, Demolition) - max is 2 | Bullet_Medium, Concussion_Medium, Demolition_Light |
| RA2AsianShotgunFanatic3 | 3 TYPES (Bullet, Concussion, Demolition) - max is 2 | Bullet_Medium, Concussion_Medium, Demolition_Light |
| RA2Comet | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Demolition_Light, Flame_Medium, Laser_Heavy |
| RA2Comet_elite | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Demolition_Light, Flame_Medium, Laser_Heavy |
| RA2Robotmm | 3 TYPES (Laser, Railgun, Tesla) - max is 2 | Laser_Heavy, Railgun_Heavy, Tesla_Heavy |
| RA2RobotmmScatter_elite | 3 TYPES (Laser, Railgun, Tesla) - max is 2 | Laser_Heavy, Railgun_Heavy, Tesla_Heavy |
| RA2Robotmm_elite | 3 TYPES (Laser, Railgun, Tesla) - max is 2 | Laser_Heavy, Railgun_Heavy, Tesla_Heavy |
| SkyHawkPlasmaCannon | NON-ADJACENT levels (Heavy+Light) | CannonAP_Light, Tesla_Heavy |
| Type97PlasmaCannon | 3 TYPES (CannonHE, Railgun, Tesla) - max is 2 | CannonHE_Heavy, Railgun_Heavy, Tesla_Heavy |
| ViperMissilesFire | 3 TYPES (Concussion, Flame, MissileAP) - max is 2 | Concussion_Medium, Flame_Light, MissileAP_Light, MissileAP_Medium |
| ordos_autogunturret | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, CannonHE_Heavy |
| ra1_soviets_submarine_torpedo | NON-ADJACENT levels (Heavy+Light) | Concussion_Light, MissileHE_Heavy |
| td_nod_attacksubmarine_nodtorptube | NON-ADJACENT levels (Heavy+Light) | Concussion_Light, MissileHE_Heavy |
| td_nod_buggymkii_machinegunbuggy2_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, CannonHE_Heavy |
| tkmkatyushalalauncherrocketsfire | 3 TYPES (Concussion, Flame, MissileAP) - max is 2 | Concussion_Medium, Flame_Light, MissileAP_Light |

WARN 34 budget violations (ratchet 48)
Lower `TIER_BASELINE` as weapons are brought onto the law; never raise it.
