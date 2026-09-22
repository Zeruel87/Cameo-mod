# audit_release_drift - measured against the build players played


baseline: **playtest-20260709** (`8c238ffc3`), 1912 weapons · 1350 shared with the tree · **1193 unchanged**

| code | check | count | ratchet |  |
|---|---|---|---|---|
| D1 | INFLATED - deals more than it shipped | 103 | 133 | PASS |
| D2 | WEAKENED - deals less than it shipped | 54 | 62 | PASS |
| D3 | EXTREME - 3x or worse, either way | 13 | 27 | PASS |
| D4 | UNMATCHED - in the release, gone under that name | 562 | 335 | FAIL |
| D5 | ACCEPTED value edit (informational) | 33 | 43 | PASS |


## D3 EXTREME - 13 weapon(s) a player will feel

| weapon | shipped | now | x | mains |
|---|---|---|---|---|
| AsianTSIonCannon | 30000 | 230000 | 7.67 | 3 -> 4 |
| TSIonCannon | 38000 | 238000 | 6.26 | 3 -> 4 |
| MadcapGun | 6000 | 36000 | 6.00 | 3 -> 1 |
| MarineMG | 6000 | 36000 | 6.00 | 3 -> 1 |
| NaxiAlienPistol | 4000 | 24000 | 6.00 | 2 -> 1 |
| DragunovSniper | 40000 | 200000 | 5.00 | 5 -> 1 |
| RA2GattlingInf | 4000 | 16000 | 4.00 | 2 -> 1 |
| elitecadregun | 4000 | 16000 | 4.00 | 2 -> 1 |
| MissileAttackRobotGun | 8000 | 24000 | 3.00 | 2 -> 1 |
| RA2ThunderboltMissile | 12000 | 4000 | 0.33 | 6 -> 1 |
| RA2ThunderboltMissile_elite | 12000 | 4000 | 0.33 | 6 -> 1 |
| RA2MultiThunderboltMissile | 16000 | 4000 | 0.25 | 8 -> 1 |
| RA2MultiThunderboltMissile_elite | 16000 | 4000 | 0.25 | 8 -> 1 |



## Supplemental reviewed rename lineage — not the raw gate

Only the 194 pinned ownership renames are followed. Wrapper branches, unreviewed aliases and deleted identities are not inferred. Current damage is compared against the original released identity; matching an alias never exempts its damage drift.

| measure | lineage view |
|---|---|
| matched | 1506 |
| unmatched | 406 |
| inflated | 115 |
| weakened | 59 |
| extreme | 17 |
| accepted | 34 |


Recovered **156** release identities hidden by name-only matching. Raw D4 and all ratchets above remain unchanged.


## Resurfaced value differences — current values, not waived drift

| released identity | current identity | shipped | now | x | mains | status |
|---|---|---|---|---|---|---|
| BHRedDarts | td_nod_stealthsoldier_bhreddarts | 10000 | 22000 | 2.20 | 5 -> 1 | inflated |
| ChemRocketsExplosion | td_nod_chemicalrocketsoldier_chemrocketsexplosion | 18000 | 12000 | 0.67 | 3 -> 1 | weakened |
| GrenadeThermobaricExplode | ra1_soviets_grenadier_grenadethermobaricexplode | 8000 | 16000 | 2.00 | 4 -> 1 | inflated |
| HighV | td_gdi_guardtower_highv_base | 4000 | 2000 | 0.50 | 2 -> 1 | weakened |
| KamovMissilesTesla | ra1_soviets_kamovattackhelicopter_kamovmissilestesla | 10000 | 11000 | 1.10 | 5 -> 1 | inflated |
| KamovTeslaArcFragment1 | ra1_soviets_kamovattackhelicopter_kamovteslaarcfragment1 | 16000 | 48000 | 3.00 | 2 -> 1 | inflated |
| KamovTeslaArcFragment2 | ra1_soviets_kamovattackhelicopter_kamovteslaarcfragment2 | 8000 | 40000 | 5.00 | 2 -> 1 | inflated |
| MissileSoldierWeapon | td_gdi_sonicmissilesoldier_missilesoldierweapon | 50000 | 51000 | 1.02 | 5 -> 1 | inflated |
| NodCommandoLaser | td_nod_lasercommando_nodcommandolaser | 12000 | 2000 | 0.17 | 1 -> 1 | accepted exact value |
| SCUDTesla | ra1_soviets_v2rocketlauncher_scudtesla | 90000 | 210000 | 2.33 | 3 -> 5 | inflated |
| SCUDThermobaric | ra1_soviets_v2rocketlauncher_scudthermobaric | 120000 | 240000 | 2.00 | 3 -> 5 | inflated |
| TowerMissile | td_gdi_advancedguardtower_towermissile | 14000 | 16000 | 1.14 | 7 -> 1 | inflated |
| TowerMissileAMT | td_gdi_advancedguardtower_towermissileamt | 14000 | 16000 | 1.14 | 7 -> 1 | inflated |
| TurretGun | td_nod_gunturret_turretgun | 24000 | 19000 | 0.79 | 4 -> 1 | weakened |
| TurretGunBlackMarket | td_nod_gunturret_turretgunblackmarket | 36000 | 31000 | 0.86 | 6 -> 1 | weakened |
| VolkovMagneticWeaponIncendiaryNuclearShells | ra1_soviets_volkov_volkovmagneticweaponincendiarynuclearshells | 200000 | 180000 | 0.90 | 5 -> 4 | weakened |
| YakTeslaArcFragment1 | ra1_soviets_teslayak_yakteslaarcfragment1 | 8000 | 24000 | 3.00 | 2 -> 1 | inflated |
| YakTeslaArcFragment2 | ra1_soviets_teslayak_yakteslaarcfragment2 | 4000 | 20000 | 5.00 | 2 -> 1 | inflated |


**FAIL: D4 above ratchet.** A rise means a weapon moved FURTHER from the shipped build, or that the gate went BLIND to more of them. Lower a baseline as the repair lands; never raise one.

