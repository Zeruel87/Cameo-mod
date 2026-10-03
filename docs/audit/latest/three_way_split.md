# audit_three_way_split — 88 weapons with MORE THAN ONE main warhead

_The `intentional_composites` exemption was DELETED 2026-09-06 (DESIGN §11b.1). Nothing is subtracted — every stack is debt._

   2092  correct — exactly one main warhead
    329  none — utility / effect-only weapons
     88  RAW STACKS — structural inventory
     88  STACKS — all debt under §11b.1

  mains  weapons
      2     47
      3     22
      4      7
      6      1
      7     10
      8      1

41 distinct stacked combinations; the 20 most common:

| count | combination |
|---|---|
| 9 | 10Dam_areanuke3 + 11Dam_areanuke3 + 1Dam_impact + 4Dam_areanuke1 + 7Dam_areanuke2 + 8Dam_areanuke2 + Damage |
| 6 | Nuclear_Super + Tesla_Super |
| 5 | Demolition_Light + MissileAP_Heavy + RA2SCUDMissileAP_Heavy_NoWall |
| 5 | 1Dam + Concussion_Medium + Demolition_Heavy |
| 5 | 1Dam + MissileAP_Heavy |
| 4 | 1Dam + MissileHE_Heavy |
| 4 | 1Dam + Bullet_Light |
| 3 | 1Dam + Flame_Medium |
| 3 | 1Dam + Demolition_Heavy + Flame_Heavy |
| 3 | IonCannon + Tesla_Super |
| 2 | IonCannon + TeslaChargedWeapon + TeslaWeapon + Tesla_Super |
| 2 | 1Dam + Demolition_Light + Flame_Light |
| 2 | 1Dam + Clear |
| 2 | 1Dam + Demolition_Light |
| 2 | Bullet_Medium + CannonHE_Heavy + Concussion_Light |
| 2 | CannonAP_Light + CannonHE_Medium + Quantum_Medium |
| 2 | 1Dam + 1Dam_impact |
| 2 | 1Dam + LightMissile + MediumMissile |
| 2 | LightMissile + MediumMissile |
| 2 | 1Dam + Laser_Heavy |

WARN raw 88/322; (cross-check audit_weapon_shape W5)
Lower `RAW_SPLIT_BASELINE` as weapons are collapsed; never raise it. W5 also resolves inheritance, but includes zero/healing/ally-only flat nodes and has narrower type/name rules. Use audit_weapon_shape.py --compare-split for the exact set difference; neither count is subtracted or reclassified.
