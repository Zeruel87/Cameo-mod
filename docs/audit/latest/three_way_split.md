# audit_three_way_split — 322 weapons with MORE THAN ONE main warhead

_The `intentional_composites` exemption was DELETED 2026-09-06 (DESIGN §11b.1). Nothing is subtracted — every stack is debt._

   1728  correct — exactly one main warhead
    317  none — utility / effect-only weapons
    322  RAW STACKS — structural inventory
    322  STACKS — all debt under §11b.1

  mains  weapons
      2    197
      3     77
      4     23
      5     11
      6      5
      7      8
      8      1

173 distinct stacked combinations; the 20 most common:

| count | combination |
|---|---|
| 17 | 1Dam + MissileAP_Heavy |
| 9 | 1Dam + CannonHE_Medium |
| 8 | TemperatureCompatibility + Tesla_Super |
| 7 | 10Dam_areanuke3 + 11Dam_areanuke3 + 1Dam_impact + 4Dam_areanuke1 + 7Dam_areanuke2 + 8Dam_areanuke2 + Damage |
| 7 | CannonHE_Medium + ShotgunChaingun + ShotgunShrapnelEnemy + ShotgunSmallArms + ShotgunTankDestroyer |
| 6 | Bullet_Heavy + SniperChaingun + SniperSmallArms |
| 6 | Nuclear_Super + Tesla_Super |
| 6 | Quantum_HeavyFlatCompatibility + Tesla_Heavy |
| 5 | Demolition_Light + MissileAP_Heavy + RA2SCUDMissileAP_Heavy_NoWall |
| 5 | 1Dam + Concussion_Medium + Demolition_Heavy |
| 4 | Bullet_Heavy + Bullet_Medium + SniperChaingun + SniperFlak + SniperSmallArms + Tesla_Super |
| 4 | Bullet_Medium + CannonHE_Heavy |
| 4 | 1Dam + Flame_Heavy + MissileHE_Heavy |
| 4 | 1Dam + Bullet_Light |
| 4 | Magic_Heavy + Tesla_Heavy |
| 4 | Flame_Heavy + Tesla_Super |
| 3 | CollapseTargetCompatibility1 + Concussion_Heavy |
| 3 | CannonHE_Heavy + Plasma_HeavyFlatCompatibility |
| 3 | 1Dam + Flame_Medium |
| 3 | 1Dam + Demolition_Light |

WARN raw 322/322; (cross-check audit_weapon_shape W5)
Lower `RAW_SPLIT_BASELINE` as weapons are collapsed; never raise it. ⚠ Cross-check `audit_weapon_shape` W5, which measures the same population from the RESOLVED node rather than the source.
