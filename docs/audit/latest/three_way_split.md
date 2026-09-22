# audit_three_way_split — 230 weapons with MORE THAN ONE main warhead

_The `intentional_composites` exemption was DELETED 2026-09-06 (DESIGN §11b.1). Nothing is subtracted — every stack is debt._

   1887  correct — exactly one main warhead
    317  none — utility / effect-only weapons
    230  RAW STACKS — structural inventory
    230  STACKS — all debt under §11b.1

  mains  weapons
      2    122
      3     65
      4     21
      5     10
      6      3
      7      8
      8      1

131 distinct stacked combinations; the 20 most common:

| count | combination |
|---|---|
| 8 | 1Dam + MissileAP_Heavy |
| 8 | TemperatureCompatibility + Tesla_Super |
| 7 | 10Dam_areanuke3 + 11Dam_areanuke3 + 1Dam_impact + 4Dam_areanuke1 + 7Dam_areanuke2 + 8Dam_areanuke2 + Damage |
| 7 | CannonHE_Medium + ShotgunChaingun + ShotgunShrapnelEnemy + ShotgunSmallArms + ShotgunTankDestroyer |
| 6 | Nuclear_Super + Tesla_Super |
| 5 | Demolition_Light + MissileAP_Heavy + RA2SCUDMissileAP_Heavy_NoWall |
| 5 | 1Dam + Concussion_Medium + Demolition_Heavy |
| 4 | 1Dam + Flame_Heavy + MissileHE_Heavy |
| 4 | 1Dam + Bullet_Light |
| 4 | Flame_Heavy + MissileHE_Heavy |
| 3 | 1Dam + Flame_Medium |
| 3 | 1Dam + Demolition_Heavy + Flame_Heavy |
| 3 | IonCannon + Tesla_Super |
| 3 | Magic_Heavy + Tesla_Heavy |
| 3 | Bullet_Medium + Concussion_Medium + Demolition_Light |
| 3 | Laser_Heavy + Railgun_Heavy + Tesla_Heavy |
| 3 | Quantum_HeavyFlatCompatibility + Tesla_Heavy |
| 3 | CannonHE_Heavy + Railgun_HeavyFlatCompatibility + Tesla_Heavy |
| 2 | Flak_Medium + Flak_MediumFlatCompatibility |
| 2 | Bullet_Medium + Railgun_Heavy |

WARN raw 230/322; (cross-check audit_weapon_shape W5)
Lower `RAW_SPLIT_BASELINE` as weapons are collapsed; never raise it. W5 also resolves inheritance, but includes zero/healing/ally-only flat nodes and has narrower type/name rules. Use audit_weapon_shape.py --compare-split for the exact set difference; neither count is subtracted or reclassified.
