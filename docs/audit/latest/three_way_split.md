# audit_three_way_split — 1072 weapons with MORE THAN ONE main warhead

_The `intentional_composites` exemption was DELETED 2026-09-06 (DESIGN §11b.1). Nothing is subtracted — every stack is debt._

    979  correct — exactly one main warhead
    316  none — utility / effect-only weapons
   1072  RAW STACKS — structural inventory
   1072  STACKS — all debt under §11b.1

  mains  weapons
      2    155
      3    307
      4    213
      5    146
      6     59
      7     86
      8     28
      9     27
     10     15
     11     17
     12      7
     13      1
     14      1
     15      7
     18      2
     19      1

498 distinct stacked combinations; the 20 most common:

| count | combination |
|---|---|
| 74 | Bullet_Light + Bullet_Medium + Bullet_MediumFlatCompatibility |
| 17 | 1Dam + MissileAP_Heavy |
| 13 | Chaingun + LaserWeapon + Laser_Heavy + MediumMissile + SmallArms |
| 12 | FlakWeapon + HeavyAAWeapon + HeavyBomb + MissileAP_Medium |
| 10 | MissileAP_Light + Tesla_Heavy + Tesla_HeavyFlatCompatibility |
| 10 | 1Dam + CannonHE_Medium |
| 10 | Chaingun + Concussion_Medium + FlakWeapon + Grenade + HeavyBomb + MediumMissile + ShrapnelWeapon |
| 8 | Bullet_Medium + Flak_Medium + Flak_MediumFlatCompatibility |
| 8 | CannonAP_Light + CannonHE_Medium |
| 8 | Bullet_Medium + Bullet_MediumFlatCompatibility + CannonHE_Heavy |
| 8 | Chaingun + Flak_Medium + LightMissile + TankDestroyerCannon |
| 8 | MissileHE_Heavy + MissileHE_LightFlatCompatibility |
| 8 | Bullet_Light + Bullet_MediumFlatCompatibility + CannonHE_Heavy + MissileAP_Medium |
| 8 | LaserWeapon + PreservedFlat_LaserWeapon + PreservedFlat_RailgunWeapon + PreservedFlat_TeslaWeapon + RailgunWeapon + TeslaWeapon + Tesla_HeavyFlatCompatibility |
| 8 | TemperatureCompatibility + Tesla_Super |
| 7 | 10Dam_areanuke3 + 11Dam_areanuke3 + 1Dam_impact + 4Dam_areanuke1 + 7Dam_areanuke2 + 8Dam_areanuke2 + Damage |
| 7 | CannonHE_Medium + Chaingun + Grenade + ShotgunChaingun + ShotgunGrenadeEnemy + ShotgunShrapnelEnemy + ShotgunSmallArms + ShotgunTankDestroyer + ShrapnelWeapon + SmallArms + TankDestroyerCannon |
| 7 | Chaingun + Flak_Medium + Flak_MediumFlatCompatibility + Grenade + HeavyMissile + NaxFlakGroundWater |
| 6 | Concussion_Heavy + Grenade + HeavyCannon + ShrapnelWeapon |
| 6 | Concussion_Medium + Demolition_Heavy |

FAIL raw 1072/329; (cross-check audit_weapon_shape W5)
**A weapon just gained a second main warhead.** Split it into the 3 layers instead of raising RAW_SPLIT_BASELINE.
