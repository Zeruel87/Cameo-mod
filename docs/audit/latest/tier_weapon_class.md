# audit_tier_weapon_class — 13 of 1330 classifiable weapons break the TYPES x LEVELS budget

Historical budget diagnostic only; DESIGN section11b.1 one-main law takes precedence.

Historical budget shapes (not one-main compliance):
   1302  1 type, 1 level - squarely in tier
      9  2 types, 1 level - lore hybrid
      3  1 type, 2 ADJACENT levels - between-tier mix
      3  2 types, 2 adjacent levels - hybrid AND between-tier (budget 4)

    934  weapons unclassified — at least one main lacks a recognized Family_Level; this is not a balance or structural pass
     25  continuous-profile weapons — discrete tier unclassified; runtime heaviness is checked separately
  Continuous identities: 120mm_cobra, 120mm_cobra_deploy, 120mm_python, 120mm_python_deploy, AlliedTankDestroyerCannon, NaxiAntiTankCannon, NaxiAntiTankCannonCorrosion, NaxiAntiTankCannon_elite, NaxiHetzerDestroyer, NaxiHetzerDestroyerCorrosion, NaxiHetzerDestroyer_elite, RA2120xmm, RA2120xmm_elite, RA2sabot, RA2sabot_elite, SkyHawkCannon, TS90mm, TS90mmDep, TSHighVelocity, TSHighVelocity2, TSHighVelocityTur, TSLaser90mm, TSLaser90mmDep, corrino_buggy_gun, ra1_allies_gunboat_cannon

VIOLATIONS by shape:
     11  3 LEVELS
      2  3 TYPES

| weapon | problem | main warheads |
|---|---|---|
| 12MissilesSpawnerScud | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Demolition_Heavy, Demolition_Light, Flame_Medium, MissileAP_Heavy |
| D2K_SiegeQuad | 3 LEVELS (Heavy+Light+Medium) - max is 2 | CannonHE_Medium, Concussion_Medium, Demolition_Heavy, Demolition_Light |
| Lunar_AmplifiedBeetleLaser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| Lunar_AmplifiedTank2Laser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| Lunar_YellowBeetleLaser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| Lunar_YellowTank2Laser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| NaxiBeetleLaser_AA_elite | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| NaxiMP40 | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Medium, CannonHE_Heavy, Concussion_Light |
| NaxiMP40_elite | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Medium, CannonHE_Heavy, Concussion_Light |
| NaxiTank2Laser_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, Laser_Heavy |
| PositronBounce1 | 3 TYPES (CannonAP, CannonHE, Quantum) - max is 2 | CannonAP_Light, CannonHE_Medium, Quantum_Medium |
| PositronBounce2 | 3 TYPES (CannonAP, CannonHE, Quantum) - max is 2 | CannonAP_Light, CannonHE_Medium, Quantum_Medium |
| td_nod_buggymkii_machinegunbuggy2_AA | 3 LEVELS (Heavy+Light+Medium) - max is 2 | Bullet_Light, Bullet_Medium, CannonHE_Heavy |

WARN 13 budget violations (ratchet 48)
Lower `TIER_BASELINE` as weapons are brought onto the law; never raise it.
