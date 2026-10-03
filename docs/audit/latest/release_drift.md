# audit_release_drift - measured against the build players played


baseline: **playtest-20260709** (`8c238ffc3`), 1912 weapons · 1344 shared with the tree · **1151 unchanged**

| code | check | count | ratchet |  |
|---|---|---|---|---|
| D1 | INFLATED - deals more than it shipped | 137 | 133 | FAIL |
| D2 | WEAKENED - deals less than it shipped | 56 | 62 | PASS |
| D3 | EXTREME - 3x or worse, either way | 17 | 27 | PASS |
| D4 | UNMATCHED - in the release, gone under that name | 568 | 335 | FAIL |
| D5 | ACCEPTED value edit (informational) | 29 | 43 | PASS |


## D3 EXTREME - 17 weapon(s) a player will feel

| weapon | shipped | now | x | mains |
|---|---|---|---|---|
| NaxiAlienPistol | 4000 | 32000 | 8.00 | 2 -> 1 |
| AsianTSIonCannon | 30000 | 230000 | 7.67 | 3 -> 4 |
| TSIonCannon | 38000 | 254000 | 6.68 | 3 -> 4 |
| MadcapGun | 6000 | 36000 | 6.00 | 3 -> 1 |
| MarineMG | 6000 | 36000 | 6.00 | 3 -> 1 |
| DragunovSniper | 40000 | 200000 | 5.00 | 5 -> 1 |
| Pistol | 100 | 500 | 5.00 | 1 -> 1 |
| RA2GattlingInf | 4000 | 16000 | 4.00 | 2 -> 1 |
| elitecadregun | 4000 | 16000 | 4.00 | 2 -> 1 |
| MissileAttackRobotGun | 8000 | 24000 | 3.00 | 2 -> 1 |
| RA2ThunderboltMissile | 12000 | 4000 | 0.33 | 6 -> 1 |
| RA2ThunderboltMissile_elite | 12000 | 4000 | 0.33 | 6 -> 1 |
| RA2MultiThunderboltMissile | 16000 | 4000 | 0.25 | 8 -> 1 |
| RA2MultiThunderboltMissile_elite | 16000 | 4000 | 0.25 | 8 -> 1 |
| ArmoredCarMG | 16000 | 1600 | 0.10 | 8 -> 1 |
| ArmoredCarMGAAWaveforce | 19000 | 1900 | 0.10 | 10 -> 1 |
| ArmoredCarMGWaveforce | 19000 | 1900 | 0.10 | 10 -> 1 |



## Supplemental reviewed rename lineage — not the raw gate

Only the 194 pinned ownership renames are followed. Wrapper branches, unreviewed aliases and deleted identities are not inferred. Current damage is compared against the original released identity; matching an alias never exempts its damage drift.

| measure | lineage view |
|---|---|
| matched | 1499 |
| unmatched | 413 |
| inflated | 162 |
| weakened | 83 |
| extreme | 22 |
| accepted | 30 |


Recovered **155** release identities hidden by name-only matching. Raw D4 and all ratchets above remain unchanged.


## Resurfaced value differences — current values, not waived drift

| released identity | current identity | shipped | now | x | mains | status |
|---|---|---|---|---|---|---|
| 105mmThermobaric | ra1_soviets_heavytank_105mmthermobaric | 12000 | 22690 | 1.89 | 2 -> 1 | inflated |
| 120mmDual | td_gdi_mammothtank_120mmdual | 8000 | 13892 | 1.74 | 1 -> 1 | inflated |
| 120mmDualHV | td_gdi_mammothtank_120mmdualhv | 16000 | 27784 | 1.74 | 1 -> 1 | inflated |
| 120mmHV | td_gdi_battletank_120mmhv | 16000 | 29696 | 1.86 | 1 -> 1 | inflated |
| 227mmAMT | td_gdi_mlrs_227mmamt | 8000 | 14736 | 1.84 | 4 -> 1 | inflated |
| 70mm | td_nod_lighttank_70mm | 6000 | 14679 | 2.45 | 1 -> 1 | inflated |
| ArtilleryShellUpgrade | td_nod_artillery_artilleryshellupgrade | 36000 | 81296 | 2.26 | 6 -> 1 | inflated |
| BHRedDarts | td_nod_stealthsoldier_bhreddarts | 10000 | 17820 | 1.78 | 5 -> 1 | inflated |
| BlackHandLaser | td_nod_lasertrooper_blackhandlaser | 30000 | 33048 | 1.10 | 1 -> 1 | inflated |
| BoxerCannonAG | td_gdi_boxer_boxercannonag | 12000 | 6000 | 0.50 | 6 -> 1 | weakened |
| ChemRocketsExplosion | td_nod_chemicalrocketsoldier_chemrocketsexplosion | 18000 | 12000 | 0.67 | 3 -> 1 | weakened |
| FireballLauncherBuggy | td_nod_buggy_fireballlauncherbuggy | 2000 | 1948 | 0.97 | 1 -> 1 | weakened |
| FireballLauncherBuggy2 | td_nod_buggymkii_fireballlauncherbuggy2 | 6000 | 3000 | 0.50 | 3 -> 1 | weakened |
| GrenadeThermobaric | ra1_soviets_grenadier_grenadethermobaric | 16000 | 13577 | 0.85 | 4 -> 1 | weakened |
| GrenadeThermobaricExplode | ra1_soviets_grenadier_grenadethermobaricexplode | 8000 | 16000 | 2.00 | 4 -> 1 | inflated |
| HighV | td_gdi_guardtower_highv | 4000 | 2000 | 0.50 | 2 -> 1 | weakened |
| HindMissilesNuclear | ra1_soviets_hindattackhelicopter_hindmissilesnuclear | 8000 | 4000 | 0.50 | 4 -> 1 | weakened |
| HindMissilesThermobaric | ra1_soviets_hindattackhelicopter_hindmissilesthermobaric | 10000 | 5000 | 0.50 | 5 -> 1 | weakened |
| KamovMissilesTesla | ra1_soviets_kamovattackhelicopter_kamovmissilestesla | 10000 | 2750 | 0.28 | 5 -> 1 | weakened |
| KamovTesla | ra1_soviets_kamovattackhelicopter_kamovtesla | 32000 | 8000 | 0.25 | 2 -> 1 | weakened |
| KamovTeslaArc | ra1_soviets_kamovattackhelicopter_kamovteslaarc | 32000 | 8000 | 0.25 | 2 -> 1 | weakened |
| KamovTeslaArcFragment1 | ra1_soviets_kamovattackhelicopter_kamovteslaarcfragment1 | 16000 | 12000 | 0.75 | 2 -> 1 | weakened |
| KamovTeslaArcFragment2 | ra1_soviets_kamovattackhelicopter_kamovteslaarcfragment2 | 8000 | 10000 | 1.25 | 2 -> 1 | inflated |
| LTNKMissiles | td_nod_lighttank_ltnkmissiles | 6000 | 14679 | 2.45 | 1 -> 1 | inflated |
| LaserBuggy2 | td_nod_buggymkii_laserbuggy2 | 6000 | 3000 | 0.50 | 3 -> 1 | weakened |
| M1A1MachineGun | td_gdi_battletank_m1a1machinegun | 2000 | 3712 | 1.86 | 1 -> 1 | inflated |
| M1A1Missiles | td_gdi_battletank_m1a1missiles | 8000 | 14848 | 1.86 | 1 -> 1 | inflated |
| M1A1MissilesAMT | td_gdi_battletank_m1a1missilesamt | 8000 | 14848 | 1.86 | 1 -> 1 | inflated |
| MachineGunBuggy2 | td_nod_buggymkii_machinegunbuggy2 | 6000 | 3000 | 0.50 | 3 -> 1 | weakened |
| MammothMissiles | td_gdi_mammothtank_mammothmissiles | 8000 | 13892 | 1.74 | 1 -> 1 | inflated |
| MammothMissilesAMT | td_gdi_mammothtank_mammothmissilesamt | 8000 | 13892 | 1.74 | 1 -> 1 | inflated |
| MissileSoldierWeapon | td_gdi_sonicmissilesoldier_missilesoldierweapon | 50000 | 51000 | 1.02 | 5 -> 1 | inflated |
| NodCommandoLaser | td_nod_lasercommando_nodcommandolaser | 12000 | 2000 | 0.17 | 1 -> 1 | accepted exact value |
| PortaTeslaFragment | ra1_soviets_shocktrooper_portateslafragment | 10000 | 4551 | 0.46 | 1 -> 1 | weakened |
| RocketsHumvee2 | td_gdi_humveemkii_rocketshumvee2 | 16000 | 8000 | 0.50 | 1 -> 1 | weakened |
| RocketsHumvee2AMT | td_gdi_humveemkii_rocketshumvee2amt | 32000 | 16000 | 0.50 | 2 -> 1 | weakened |
| RocketsRACryo | ra1_allies_alliedrocketsoldier_rocketsracryo | 20000 | 11500 | 0.57 | 2 -> 1 | weakened |
| SCUDTesla | ra1_soviets_v2rocketlauncher_scudtesla | 90000 | 171493 | 1.91 | 3 -> 1 | inflated |
| SCUDThermobaric | ra1_soviets_v2rocketlauncher_scudthermobaric | 120000 | 195991 | 1.63 | 3 -> 1 | inflated |
| SiegeMortar | ra1_soviets_mortarsoldier_siegemortar_ExplicitDamage3of4 | 32000 | 24000 | 0.75 | 4 -> 1 | weakened |
| SiegeMortarThermobaric | ra1_soviets_mortarsoldier_siegemortarthermobaric_ExplicitDamage3of4 | 24000 | 18000 | 0.75 | 6 -> 1 | weakened |
| StealthTankMissiles | td_nod_stealthtank_stealthtankmissiles | 12000 | 22230 | 1.85 | 1 -> 1 | inflated |
| StealthTankMissilesBlackMarket | td_nod_stealthtank_stealthtankmissilesblackmarket | 12000 | 22230 | 1.85 | 1 -> 1 | inflated |
| TowerMissile | td_gdi_advancedguardtower_towermissile | 14000 | 16000 | 1.14 | 7 -> 1 | inflated |
| TowerMissileAMT | td_gdi_advancedguardtower_towermissileamt | 14000 | 16000 | 1.14 | 7 -> 1 | inflated |
| TurretGun | td_nod_gunturret_turretgun | 24000 | 19000 | 0.79 | 4 -> 1 | weakened |
| TurretGunBlackMarket | td_nod_gunturret_turretgunblackmarket | 36000 | 31000 | 0.86 | 6 -> 1 | weakened |
| VolkovMagneticWeaponIncendiaryNuclearShells | ra1_soviets_volkov_volkovmagneticweaponincendiarynuclearshells | 200000 | 180000 | 0.90 | 5 -> 1 | weakened |
| YakNuclearBomb | ra1_soviets_nuclearyak_yaknuclearbomb | 200000 | 100000 | 0.50 | 4 -> 1 | weakened |
| YakTeslaArcFragment1 | ra1_soviets_teslayak_yakteslaarcfragment1 | 8000 | 6000 | 0.75 | 2 -> 1 | weakened |
| YakTeslaArcFragment2 | ra1_soviets_teslayak_yakteslaarcfragment2 | 4000 | 5000 | 1.25 | 2 -> 1 | inflated |
| YakTeslaGun | ra1_soviets_teslayak_yakteslagun | 16000 | 4000 | 0.25 | 2 -> 1 | weakened |
| YakTeslaGunArc | ra1_soviets_teslayak_yakteslagunarc | 16000 | 4000 | 0.25 | 2 -> 1 | weakened |


**FAIL: D1, D4 above ratchet.** A rise means a weapon moved FURTHER from the shipped build, or that the gate went BLIND to more of them. Lower a baseline as the repair lands; never raise one.

