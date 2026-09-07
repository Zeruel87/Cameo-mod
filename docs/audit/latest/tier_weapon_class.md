# audit_tier_weapon_class — 35 of 866 classifiable weapons break the TYPES x LEVELS budget

LEGAL shapes:
    763  1 type, 1 level - squarely in tier
     38  2 types, 1 level - lore hybrid
     29  2 types, 2 adjacent levels - hybrid AND between-tier (budget 4)
      1  1 type, 2 ADJACENT levels - between-tier mix

   1288  weapons skipped — at least one LEGACY-named main warhead (no Family_Level), so the budget cannot be judged until they are 3-way split

VIOLATIONS by shape:
     17  3 LEVELS
     11  3 TYPES
      7  NON-ADJACENT levels

| weapon | problem | main warheads |
|---|---|---|
| 12MissilesSpawnerScud | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Demolition_Heavy, Demolition_Light, Flame_Medium, MissileAP_Heavy |
| AsianChaosMine | NON-ADJACENT levels (Heavy+Light) | CannonAP_Light, Chemical_Heavy |
| AsianPhoenixRocket | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Demolition_Light, Flame_Medium, MissileAP_Heavy |
| AsianPhoenixRocket_elite | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Demolition_Light, Flame_Medium, MissileAP_Heavy |
| D2K_Rocket_Trooper1 | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Flak_Medium, MissileAP_Heavy, MissileAP_Light |
| D2K_Rocket_Trooper2 | 3 LEVELS (Heavy+Light+Medium) - max is 2 | CannonHE_Medium, Demolition_Light, Railgun_Heavy |
| D2K_Rocket_Trooper_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Flak_Medium, MissileAP_Heavy, MissileAP_Light |
| D2K_Rocket_Trooper_AGOnly | 3 LEVELS (Heavy+Light+Medium) - max is 2 | CannonHE_Medium, Demolition_Light, Railgun_Heavy |
| D2K_SiegeQuad | 3 LEVELS (Heavy+Light+Medium) - max is 2 | CannonHE_Medium, Concussion_Medium, Demolition_Heavy, Demolition_Light |
| GoliathMG | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Medium, CannonHE_Heavy, Concussion_Light |
| HMGo_upgrade | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| HeavyIxianCombatTankCannon | 3 LEVELS (Heavy+Light+Medium) - max is 2 | CannonAP_Light, CannonHE_Heavy, CannonHE_Medium |
| IxianCombatTankCannon | 3 LEVELS (Heavy+Light+Medium) - max is 2 | CannonAP_Light, CannonHE_Heavy, CannonHE_Medium |
| NaxiMP40 | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Medium, CannonHE_Heavy, Concussion_Light |
| NaxiMP40_elite | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Medium, CannonHE_Heavy, Concussion_Light |
| NodTorpTube | NON-ADJACENT levels (Heavy+Light) | Concussion_Light, MissileHE_Heavy |
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
| TSLaserObeliskLaserFire | NON-ADJACENT levels (Heavy+Light) | CannonAP_Light, Laser_Heavy |
| TSObeliskLaserFire | NON-ADJACENT levels (Heavy+Light) | CannonAP_Light, Laser_Heavy |
| TorpTube | NON-ADJACENT levels (Heavy+Light) | Concussion_Light, MissileHE_Heavy |
| Type97PlasmaCannon | 3 TYPES (CannonHE, Railgun, Tesla) - max is 2 | CannonHE_Heavy, Railgun_Heavy, Tesla_Heavy |
| ViperMissilesFire | 3 TYPES (Concussion, Flame, MissileAP) - max is 2 | Concussion_Medium, Flame_Light, MissileAP_Light, MissileAP_Medium |
| d2k_air_drone_guns_upgrade | 3 TYPES (Bullet, CannonHE, MissileAP) - max is 2 | Bullet_Medium, CannonHE_Heavy, MissileAP_Heavy |
| ordos_autogunturret | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, CannonHE_Heavy |
| td_gdi_commando_sniper_elite | NON-ADJACENT levels (Heavy+Light) | Railgun_Heavy, Sniper_Light |
| tkmkatyushalalauncherrocketsfire | 3 TYPES (Concussion, Flame, MissileAP) - max is 2 | Concussion_Medium, Flame_Light, MissileAP_Light |

WARN 35 budget violations (ratchet 48)
Lower `TIER_BASELINE` as weapons are brought onto the law; never raise it.
