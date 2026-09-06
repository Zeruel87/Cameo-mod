# Hydralisk ordered-impact laboratory

Offline experiment only; no candidate is applied to gameplay.
Source baseline: 4deaee086. Staged BulletChem rows: PR325 e42eb991.

## Scenario and limits

One enemy positional impact at a stated distance from the target hitshape edge.
Actors start unupgraded, unshielded, standing, with zero Corrosion; external conditions
start at zero, while the Corroding condition follows its authored meter thresholds.
Hydra outgoing modifiers: 50, 110, 110, 99%.
Includes selected actor incoming modifiers, ordered TakeCover activation, individual
state bindings, health-relative state scaling, clamping and immediate Corrosion vulnerability.
**Victims are held alive for the whole impact**: results are potential damage, not
actual HP removed, kills, DPS or time-to-kill. No tick effects, DoT, relaxation, shields,
world hitshape discovery, target eligibility or projectile interception is simulated.
This is a source-derived Python projection, not engine execution or playtest evidence.

## Close-impact potential damage

| Target | Current | Staged 72000 | Scaled 33000 | Air-restored 33000 | Percentage control | Two-stage control |
|---|---:|---:|---:|---:|---:|---:|
| td_nod_minigunner | 33738 | 111980 (3.32x) | 51037 (1.51x) | 51037 (1.51x) | 51041 (1.51x) | 33741 (1.00x) |
| terran_marine | 41645 | 91787 (2.20x) | 41506 (1.00x) | 41506 (1.00x) | 41501 (1.00x) | 41648 (1.00x) |
| zerg_hydralisk | 51080 | 93928 (1.84x) | 41677 (0.82x) | 41677 (0.82x) | 41672 (0.82x) | 51083 (1.00x) |
| ra1_allies_alliedmediumtank | 45433 | 61494 (1.35x) | 27213 (0.60x) | 27213 (0.60x) | 27280 (0.60x) | 45436 (1.00x) |
| terran_siegetank | 42364 | 63016 (1.49x) | 27362 (0.65x) | 27362 (0.65x) | 27470 (0.65x) | 42366 (1.00x) |
| terran_wraith | 31941 | 29924 (0.94x) | 13489 (0.42x) | 28701 (0.90x) | 28772 (0.90x) | 31943 (1.00x) |
| terran_battlecruiser | 29943 | 30605 (1.02x) | 12424 (0.41x) | 28971 (0.97x) | 29767 (0.99x) | 29946 (1.00x) |

## Corrosion meter after the complete potential impact

Meter units are not HP damage. No meter means no received Corrosion; cap is 20000.
Held-alive assumption still applies, including to low-HP targets.

| Target | Current | Staged | Scaled | Air-restored | Percentage control | Two-stage |
|---|---:|---:|---:|---:|---:|---:|
| td_nod_minigunner | no meter | no meter | no meter | no meter | no meter | no meter |
| terran_marine | no meter | no meter | no meter | no meter | no meter | no meter |
| zerg_hydralisk | 12747 | 9391 | 4166 | 4166 | 4223 | 12747 |
| ra1_allies_alliedmediumtank | 13587 | 5464 | 2415 | 2415 | 2497 | 13587 |
| terran_siegetank | 7966 | 3357 | 1458 | 1458 | 1538 | 7966 |
| terran_wraith | 4977 | 4784 | 2157 | 4589 | 4597 | 4977 |
| terran_battlecruiser | 668 | 487 | 196 | 461 | 480 | 668 |

## Distance sensitivity: potential damage, not crowd effectiveness

| Target / distance | Current | Air-restored | Two-stage control |
|---|---:|---:|---:|
| terran_marine / 0 | 41645 | 41506 | 41648 |
| terran_marine / 55 | 34393 | 34034 | 35953 |
| terran_marine / 110 | 27445 | 25318 | 30280 |
| terran_marine / 220 | 19135 | 0 | 19841 |
| terran_marine / 350 | 12124 | 0 | 13812 |
| ra1_allies_alliedmediumtank / 0 | 45433 | 27213 | 45436 |
| ra1_allies_alliedmediumtank / 55 | 38799 | 22312 | 39165 |
| ra1_allies_alliedmediumtank / 110 | 32187 | 16596 | 32838 |
| ra1_allies_alliedmediumtank / 220 | 21866 | 0 | 21608 |
| ra1_allies_alliedmediumtank / 350 | 14627 | 0 | 15027 |
| terran_wraith / 0 | 31941 | 28701 | 31943 |
| terran_wraith / 55 | 26391 | 23533 | 26636 |
| terran_wraith / 110 | 21160 | 17505 | 21597 |
| terran_wraith / 220 | 12994 | 0 | 12224 |
| terran_wraith / 350 | 7218 | 0 | 7562 |

## What the controls mean

- Scaled 33000 uses the staged shape, 20% Corrosion and PercentageScale 2098.
- Air-restored changes only four nominal flat air rows (120/117/113/107). It is
  a bespoke role experiment, not a generated canonical family or exact preservation.
- Percentage control restores the four original percentage nodes. It demonstrates
  why percentage payload choice is separate from flat damage; geometry/order still differ.
- Two-stage control retains the original chemical flat pre-hit and four percentage hits,
  combining the other three flat profiles. This is a close-impact diagnostic only:
  it borrows missile geometry and changes targeting/death-type behavior. Not a safe patch.
- Every new single-main candidate loses parts of the current distributed splash.

The JSON companion contains individual applications, defense modifiers and meter changes.
No candidate is approved; do not regenerate weapon families or remove Hydra guards based on this report.
