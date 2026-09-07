# audit_release_drift - measured against the build players played


baseline: **playtest-20260709** (`8c238ffc3`), 1912 weapons · 1577 shared with the tree · **1384 unchanged**

| code | check | count | ratchet |  |
|---|---|---|---|---|
| D1 | INFLATED - deals more than it shipped | 131 | 133 | PASS |
| D2 | WEAKENED - deals less than it shipped | 62 | 62 | PASS |
| D3 | EXTREME - 3x or worse, either way | 27 | 27 | PASS |
| D4 | UNMATCHED - in the release, gone under that name | 335 | 335 | PASS |
| D5 | ACCEPTED value edit (informational) | 42 | 43 | PASS |


## D3 EXTREME - 27 weapon(s) a player will feel

| weapon | shipped | now | x | mains |
|---|---|---|---|---|
| AsianTSIonCannon | 30000 | 230000 | 7.67 | 3 -> 4 |
| TSDevoutChainguns | 3200 | 24000 | 7.50 | 2 -> 1 |
| TSIonCannon | 38000 | 238000 | 6.26 | 3 -> 4 |
| MadcapGun | 6000 | 36000 | 6.00 | 3 -> 1 |
| MarineMG | 6000 | 36000 | 6.00 | 3 -> 1 |
| NaxiAlienPistol | 4000 | 24000 | 6.00 | 2 -> 1 |
| DragunovSniper | 40000 | 200000 | 5.00 | 5 -> 1 |
| KamovTeslaArcFragment2 | 8000 | 40000 | 5.00 | 2 -> 1 |
| YakTeslaArcFragment2 | 4000 | 20000 | 5.00 | 2 -> 1 |
| BlackHandLaser | 30000 | 144000 | 4.80 | 1 -> 2 |
| OfficerMachineGun | 4000 | 16000 | 4.00 | 2 -> 1 |
| RA2GattlingInf | 4000 | 16000 | 4.00 | 2 -> 1 |
| RAVulcan | 4000 | 16000 | 4.00 | 2 -> 1 |
| TS30mm | 4000 | 16000 | 4.00 | 2 -> 1 |
| TSSergGun | 4000 | 16000 | 4.00 | 2 -> 1 |
| elitecadregun | 4000 | 16000 | 4.00 | 2 -> 1 |
| KamovTeslaArcFragment1 | 16000 | 48000 | 3.00 | 2 -> 1 |
| MissileAttackRobotGun | 8000 | 24000 | 3.00 | 2 -> 1 |
| TS30mmRail | 6000 | 18000 | 3.00 | 3 -> 1 |
| YakTeslaArcFragment1 | 8000 | 24000 | 3.00 | 2 -> 1 |
| D2K_Rocket_Trooper_AGOnly | 30000 | 10000 | 0.33 | 3 -> 1 |
| RA2ThunderboltMissile | 12000 | 4000 | 0.33 | 6 -> 1 |
| RA2ThunderboltMissile_elite | 12000 | 4000 | 0.33 | 6 -> 1 |
| d2k_grenade | 30000 | 10000 | 0.33 | 3 -> 1 |
| RA2MultiThunderboltMissile | 16000 | 4000 | 0.25 | 8 -> 1 |
| RA2MultiThunderboltMissile_elite | 16000 | 4000 | 0.25 | 8 -> 1 |
| wc2ogremageRunes_Hit | 101250 | 11250 | 0.11 | 10 -> 1 |



_within ratchet_ — but every row above is still a weapon that does not deal what it shipped.

