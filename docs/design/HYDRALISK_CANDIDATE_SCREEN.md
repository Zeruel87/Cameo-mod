# Hydralisk candidate screening

Source: upstream 4deaee086; candidate template from PR325 e42eb991 staged patch.
No candidate is applied. Cost, HP, speed, range, reload and projectile remain unchanged.

## Nominal per-shot budgets

Each cell is **flat / percentage / flat-derived Corrosion** in engine health units.
Uses real resolved HP and base Armor (not deployed/shielded variants). Excludes actor
firepower, target damage modifiers, targeting eligibility, state clamping/DoT and falloff.
Corrosion excludes percentage-derived feed, so is not total state delivery.
This isolates profile tradeoffs; it is not actual damage, DPS or shots-to-kill.

| Target | HP / armor | Current | Staged 72000 | Flak anchor 33000 | Fighter-row anchor 42000 |
|---|---|---|---|---|---|
| td_nod_minigunner | 30000 / None | 51480 / 135 / 25200 | 137520 / 1296 / 27504 | 63030 / 124 / 12606 | 80220 / 124 / 16044 |
| terran_marine | 41000 / Flak | 51480 / 183 / 29520 | 111600 / 1918 / 22320 | 51150 / 184 / 10230 | 65100 / 184 / 13020 |
| zerg_hydralisk | 80000 / Flak | 51480 / 360 / 29520 | 111600 / 3744 / 22320 | 51150 / 359 / 10230 | 65100 / 359 / 13020 |
| ra1_allies_alliedmediumtank | 90000 / Heavy | 41760 / 324 / 31680 | 65520 / 2592 / 13104 | 30030 / 249 / 6006 | 38220 / 249 / 7644 |
| terran_siegetank | 150000 / Heavy | 41760 / 540 / 31680 | 65520 / 4320 / 13104 | 30030 / 415 / 6006 | 38220 / 415 / 7644 |
| terran_wraith | 50000 / Helicopter | 37440 / 160 / 7920 | 38160 / 720 / 7632 | 17490 / 69 / 3498 | 22260 / 69 / 4452 |
| terran_battlecruiser | 500000 / Spaceship | 35280 / 1500 / 10080 | 32400 / 5400 / 6480 | 14850 / 519 / 2970 | 18900 / 519 / 3780 |
| Synthetic Fighter reference (not an actor) | 50000 / Fighter | 39600 / 170 / 3600 | 67680 / 1080 / 13536 | 31020 / 103 / 6204 | 39480 / 103 / 7896 |

The 33000 and 42000 values are rounded screening anchors, not recommendations.
Their PercentageScale values 2098 and 1648 approximately retain the current nominal
Flak percentage coefficient (0.45% max HP), instead of retaining the staged buff.
They do not preserve every armor row or small-HP rounding. Corrosion stays at the staged
20% only to expose its consequences; it has not been calibrated.

## Flat-only distance sensitivity

Flak damage at distance from the hit-shape edge, without actor modifiers. This is
one target at a chosen distance, not a crowd simulation or projectile hit probability.

Current nominal Flak damage is 51480; at distance zero it is 51332 because this
table includes the existing authored falloff (the chemical main starts at 99%).

| Distance (world units) | Current | 33000 | 42000 |
|---|---|---|---|
| 0 | 51332 | 51150 | 65100 |
| 55 | 42424 | 41943 | 53382 |
| 110 | 33867 | 31201 | 39711 |
| 220 | 23640 | 0 | 0 |
| 350 | 15000 | 0 | 0 |
| 700 | 118 | 0 | 0 |

## Screening conclusion

Neither candidate is ready to implement. 33000 roughly retains Flak flat damage but
raises None damage by 22%; 42000 roughly retains Fighter flat damage but still cuts
Helicopter and Spaceship flat damage by about 40-46%. Reducing raw damage alone
cannot preserve the existing mixed anti-air role. Percentage and Corrosion delivery
also change independently. Choose the desired armor response before tuning magnitude.

Next gate: choose acceptable infantry-versus-air tradeoffs, then model full
actor modifiers, percentage geometry and total state delivery before selecting a build.
No broad family regeneration, game launch or publication is authorized by this screen.
