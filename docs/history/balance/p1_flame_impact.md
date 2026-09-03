# P1 flame/footgun impact measurement

> ⛔ **ARCHIVED 2026-08-23 — not current.** Moved out of the live documentation set: it is either machine-generated (regenerate it rather than reading this copy) or the programme it belonged to is finished or dormant. Kept for provenance. Start at [`docs/HANDOFF.md`](../../HANDOFF.md).

Concrete weapons with a single-value `Range:` on a flat-damage warhead: **49**

The fix is to delete the `Range:` line from the warhead so `Spread:` + `Falloff:` define the geometry. `effective_damage.py` is the same metric the balance pipeline uses (area-integrated per-shot).

| weapon | current eff | after-fix eff | absolute Δ | relative Δ | warhead | Damage | Spread | Range | Falloff |
|---|---:|---:|---:|---:|---|---|---|---|---|
| MonsterTankTuskTesla | 68772 | 97654 | 28882 | 0.42x | Warhead@LightFlameWeapon | 26750 | 500 | 500 | 111, 33, 11, 3 |
| facedancer_grenade | 250580 | 269211 | 18631 | 0.07x | Warhead@LightFlameWeapon | 20000 | 500 | 500 | 111, 33, 11, 3 |
| MammothTusk2 | 39956 | 57806 | 17850 | 0.45x | Warhead@LightFlameWeapon | 16000 | 500 | 500 | 111, 33, 11, 3 |
| MammothTusk2TargetingComputer | 39956 | 57806 | 17850 | 0.45x | Warhead@LightFlameWeapon | 16000 | 500 | 500 | 111, 33, 11, 3 |
| MonsterTankTuskThermobaric | 114949 | 129255 | 14306 | 0.12x | Warhead@LightFlameWeapon | 13250 | 500 | 500 | 111, 33, 11, 3 |
| SiegeTankSiegeCannon | 452898 | 465800 | 12902 | 0.03x | Warhead@LightFlameWeapon | 10000 | 500 | 500 | 111, 33, 11, 3 |
| SiegeEngineCannon | 452898 | 465800 | 12902 | 0.03x | Warhead@LightFlameWeapon | 10000 | 500 | 500 | 111, 33, 11, 3 |
| SCUDNUKE | 764587 | 777005 | 12419 | 0.02x | Warhead@LightFlameWeapon | 20000 | 500 | 500 | 111, 33, 11, 3 |
| SCUDNUKEThermobaric | 764587 | 777005 | 12419 | 0.02x | Warhead@LightFlameWeapon | 20000 | 500 | 500 | 111, 33, 11, 3 |
| GladiusCannon | 69955 | 79904 | 9949 | 0.14x | Warhead@LightFlameWeapon | 10000 | 500 | 500 | 111, 33, 11, 3 |
| MammothTuskTesla | 21361 | 30287 | 8926 | 0.42x | Warhead@LightFlameWeapon | 8000 | 500 | 500 | 111, 33, 11, 3 |
| MammothTuskTeslaTargetingComputer | 21361 | 30287 | 8926 | 0.42x | Warhead@LightFlameWeapon | 8000 | 500 | 500 | 111, 33, 11, 3 |
| BallistaTowerMultiShot | 14589 | 19417 | 4828 | 0.33x | Warhead@LightFlameWeapon | 10000 | 500 | 500 | 111, 33, 11, 3 |
| MammothTuskTeslaFragment1 | 11646 | 16434 | 4788 | 0.41x | Warhead@LightFlameWeapon | 4000 | 500 | 500 | 111, 33, 11, 3 |
| MammothTuskThermobaric | 35602 | 40065 | 4463 | 0.13x | Warhead@LightFlameWeapon | 4000 | 500 | 500 | 111, 33, 11, 3 |
| MammothTuskThermobaricTargetingComputer | 35602 | 40065 | 4463 | 0.13x | Warhead@LightFlameWeapon | 4000 | 500 | 500 | 111, 33, 11, 3 |
| BallistaMultiShot | 13439 | 17863 | 4423 | 0.33x | Warhead@LightFlameWeapon | 10000 | 500 | 500 | 111, 33, 11, 3 |
| wc2mageBlizzard_Projectile | 13283 | 17422 | 4139 | 0.31x | Warhead@LightFlameWeapon | 4000 | 500 | 500 | 111, 33, 11, 3 |
| HarrierMissiles | 26260 | 30137 | 3877 | 0.15x | Warhead@LightFlameWeapon | 4000 | 500 | 500 | 111, 33, 11, 3 |
| HarrierMissiles_elite | 25276 | 28844 | 3567 | 0.14x | Warhead@LightFlameWeapon | 4000 | 500 | 500 | 111, 33, 11, 3 |
| wc2cannontowerFire | 60952 | 64479 | 3527 | 0.06x | Warhead@LightFlameWeapon | 4000 | 500 | 500 | 111, 33, 11, 3 |
| RA2MortarBike | 50218 | 53495 | 3277 | 0.07x | Warhead@LightFlameWeapon | 6000 | 500 | 500 | 111, 33, 11, 3 |
| RA2MortarBike_elite | 49670 | 52853 | 3183 | 0.06x | Warhead@LightFlameWeapon | 6000 | 500 | 500 | 111, 33, 11, 3 |
| SCTyr | 17469 | 20460 | 2991 | 0.17x | Warhead@LightFlameWeapon | 4000 | 500 | 500 | 111, 33, 11, 3 |
| ShtoraLaser | 5645 | 8226 | 2580 | 0.46x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| 25mmWaveforce | 17923 | 20441 | 2518 | 0.14x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| MammothTuskTeslaFragment2 | 6122 | 8598 | 2475 | 0.40x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| RA2PsychicJab | 5337 | 7695 | 2358 | 0.44x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| RA2PsychicJab_elite | 5303 | 7653 | 2350 | 0.44x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| DreadshroudSpore | 9973 | 12253 | 2280 | 0.23x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| 25mm | 14643 | 16875 | 2232 | 0.15x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| AsianHarbingerPlasma | 25356 | 27539 | 2182 | 0.09x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| RA2LasherCannon | 14086 | 16076 | 1990 | 0.14x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| AsianLynxTankCannon | 14086 | 16075 | 1989 | 0.14x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| wc2dragonFireVisible | 32224 | 34197 | 1973 | 0.06x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| wc2dragonFireExplosion | 32224 | 34197 | 1973 | 0.06x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| BehemothShoot | 15998 | 17963 | 1965 | 0.12x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| AsianLynxTankCannon_elite | 13967 | 15899 | 1932 | 0.14x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| RA2LasherCannon_elite | 13965 | 15895 | 1931 | 0.14x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| MedicFlare | 522 | 2436 | 1914 | 3.67x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| AsianSinglePlasma | 25043 | 26820 | 1776 | 0.07x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| AsianTwinPlasma | 25043 | 26819 | 1776 | 0.07x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| AsianSinglePlasma_elite | 24916 | 26662 | 1745 | 0.07x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| AsianTwinPlasma_elite | 24897 | 26638 | 1741 | 0.07x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| AsianTurretPlasma | 24012 | 25571 | 1558 | 0.06x | Warhead@LightFlameWeapon | 2000 | 500 | 500 | 111, 33, 11, 3 |
| TSTurretLaserFire | 30760 | 32050 | 1290 | 0.04x | Warhead@LightFlameWeapon | 1000 | 500 | 500 | 111, 33, 11, 3 |
| HueyFireMissiles | 13780 | 14919 | 1139 | 0.08x | Warhead@LightFlameWeapon | 1000 | 500 | 500 | 111, 33, 11, 3 |
| NanoSmokeAG | 3636 | 4185 | 548 | 0.15x | Warhead@LightFlameWeapon | 3333 | 333 | 500 | 111, 33, 11, 3 |
| RA2Dronegas | 0 | 0 | 0 | 0.00x | Warhead@2 | 0 | - | 5000 | 100, 100 |

## Summary

- Total affected concrete weapons: 49
- Total current `effective_damage`: 3,815,331
- Total after-fix `effective_damage`: 4,085,037
- Total absolute increase: 269,706 (6.6% of after-fix total)

## Proposed balance pass — cap the relative gain of each affected weapon

For each weapon the broken warhead is currently contributing 0. After the fix it adds `delta`. `Damage` is linear in `effective_damage`, so the table below shows the `Damage` value for the broken warhead that would cap the total weapon gain at +10%, +25%, or +50% over its current `effective_damage`. Values already at or above current `Damage` mean no change is needed; lower values mean a per-weapon override (or template change) is required.

| weapon | source | current D | cap +10% | cap +25% | cap +50% | file |
|---|---|---:|---:|---:|---:|---|
| `MonsterTankTuskTesla` | override | 26750 | 6400 | 15900 | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `facedancer_grenade` | override | 20000 | no change | no change | no change | mods\cameo\ContentPacks\D2k\Ordos\yaml\weapons.yaml |
| `MammothTusk2` | override | 16000 | 3600 | 9000 | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `MammothTusk2TargetingComputer` | override | 16000 | 3600 | 9000 | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `MonsterTankTuskThermobaric` | override | 13250 | 10600 | no change | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `SiegeTankSiegeCannon` | override | 10000 | no change | no change | no change | mods\cameo\ContentPacks\StarCraft\Terran\yaml\weapons.yaml |
| `SiegeEngineCannon` | override | 10000 | no change | no change | no change | mods\cameo\weapons\warcraft2.yaml |
| `SCUDNUKE` | override | 20000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `SCUDNUKEThermobaric` | override | 20000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `GladiusCannon` | override | 10000 | 7000 | no change | no change | mods\cameo\ContentPacks\StarCraft\Protoss\yaml\weapons.yaml |
| `MammothTuskTesla` | override | 8000 | 1900 | 4800 | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `MammothTuskTeslaTargetingComputer` | override | 8000 | 1900 | 4800 | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `BallistaTowerMultiShot` | override | 10000 | 3000 | 7600 | no change | mods\cameo\ContentPacks\RedAlert\Japan\yaml\weapons.yaml |
| `MammothTuskTeslaFragment1` | override | 4000 | 1000 | 2400 | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `MammothTuskThermobaric` | override | 4000 | 3200 | no change | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `MammothTuskThermobaricTargetingComputer` | override | 4000 | 3200 | no change | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `BallistaMultiShot` | override | 10000 | 3000 | 7600 | no change | mods\cameo\ContentPacks\RedAlert\Japan\yaml\weapons.yaml |
| `wc2mageBlizzard_Projectile` | override | 4000 | 1300 | 3200 | no change | mods\cameo\weapons\warcraft2.yaml |
| `HarrierMissiles` | override | 4000 | 2700 | no change | no change | mods\cameo\ContentPacks\RedAlert2\Allies\yaml\weapons.yaml |
| `HarrierMissiles_elite` | override | 4000 | 2800 | no change | no change | mods\cameo\ContentPacks\RedAlert2\Allies\yaml\weapons.yaml |
| `wc2cannontowerFire` | override | 4000 | no change | no change | no change | mods\cameo\weapons\warcraft2.yaml |
| `RA2MortarBike` | override | 6000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\Syndicate\yaml\weapons.yaml |
| `RA2MortarBike_elite` | override | 6000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\Syndicate\yaml\weapons.yaml |
| `SCTyr` | override | 4000 | 2300 | no change | no change | mods\cameo\ContentPacks\StarCraft\Terran\yaml\weapons.yaml |
| `ShtoraLaser` | override | 2000 | 400 | 1100 | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `25mmWaveforce` | override | 2000 | 1400 | no change | no change | mods\cameo\ContentPacks\RedAlert\Shared\yaml\weapons.yaml |
| `MammothTuskTeslaFragment2` | override | 2000 | 500 | 1200 | no change | mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml |
| `RA2PsychicJab` | override | 2000 | 500 | 1100 | no change | mods\cameo\ContentPacks\RedAlert2\Yuri\yaml\weapons.yaml |
| `RA2PsychicJab_elite` | override | 2000 | 500 | 1100 | no change | mods\cameo\ContentPacks\RedAlert2\Yuri\yaml\weapons.yaml |
| `DreadshroudSpore` | override | 2000 | 900 | no change | no change | mods\cameo\ContentPacks\StarCraft\Zerg\yaml\weapons.yaml |
| `25mm` | override | 2000 | 1300 | no change | no change | mods\cameo\ContentPacks\RedAlert\Allies\yaml\weapons.yaml |
| `AsianHarbingerPlasma` | override | 2000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\AsianAlliance\yaml\weapons.yaml |
| `RA2LasherCannon` | override | 2000 | 1400 | no change | no change | mods\cameo\ContentPacks\RedAlert2\Yuri\yaml\weapons.yaml |
| `AsianLynxTankCannon` | override | 2000 | 1400 | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\AsianAlliance\yaml\weapons.yaml |
| `wc2dragonFireVisible` | override | 2000 | no change | no change | no change | mods\cameo\ContentPacks\Warcraft2\Orcs\yaml\weapons.yaml |
| `wc2dragonFireExplosion` | override | 2000 | no change | no change | no change | mods\cameo\ContentPacks\Warcraft2\Orcs\yaml\weapons.yaml |
| `BehemothShoot` | override | 2000 | 1600 | no change | no change | mods\cameo\ContentPacks\StarCraft\Zerg\yaml\weapons.yaml |
| `AsianLynxTankCannon_elite` | override | 2000 | 1400 | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\AsianAlliance\yaml\weapons.yaml |
| `RA2LasherCannon_elite` | override | 2000 | 1400 | no change | no change | mods\cameo\ContentPacks\RedAlert2\Yuri\yaml\weapons.yaml |
| `MedicFlare` | override | 2000 | 100 | 100 | 300 | mods\cameo\ContentPacks\StarCraft\Terran\yaml\weapons.yaml |
| `AsianSinglePlasma` | override | 2000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\AsianAlliance\yaml\weapons.yaml |
| `AsianTwinPlasma` | override | 2000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\AsianAlliance\yaml\weapons.yaml |
| `AsianSinglePlasma_elite` | override | 2000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\AsianAlliance\yaml\weapons.yaml |
| `AsianTwinPlasma_elite` | override | 2000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\AsianAlliance\yaml\weapons.yaml |
| `AsianTurretPlasma` | override | 2000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\AsianAlliance\yaml\weapons.yaml |
| `TSTurretLaserFire` | template | 1000 | no change | no change | no change | mods\cameo\weapons\weapons.yaml |
| `HueyFireMissiles` | template | 1000 | no change | no change | no change | mods\cameo\ContentPacks\RedAlert2Mod\TKM\yaml\weapons.yaml |
| `NanoSmokeAG` | override | 3333 | 2200 | no change | no change | mods\cameo\ContentPacks\RedAlert\Japan\yaml\weapons.yaml |

### Observations

- 30 of 48 weapons need a `Damage` nerf to stay within +10%.
- 14 need a nerf to stay within +25%.
- 1 need a nerf to stay within +50%.
- Most of the big outliers are **per-weapon overrides**, so changing only the `^LightFlameWeapon` template `Damage` (1000) will not touch them.

## Top 10 biggest absolute gains (watch for over-budget)

- `MonsterTankTuskTesla`: 68,772 -> 97,654 (+28,882, 0.42x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `facedancer_grenade`: 250,580 -> 269,211 (+18,631, 0.07x) in mods\cameo\ContentPacks\D2k\Ordos\yaml\weapons.yaml
- `MammothTusk2`: 39,956 -> 57,806 (+17,850, 0.45x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `MammothTusk2TargetingComputer`: 39,956 -> 57,806 (+17,850, 0.45x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `MonsterTankTuskThermobaric`: 114,949 -> 129,255 (+14,306, 0.12x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `SiegeTankSiegeCannon`: 452,898 -> 465,800 (+12,902, 0.03x) in mods\cameo\ContentPacks\StarCraft\Terran\yaml\weapons.yaml
- `SiegeEngineCannon`: 452,898 -> 465,800 (+12,902, 0.03x) in mods\cameo\weapons\warcraft2.yaml
- `SCUDNUKE`: 764,587 -> 777,005 (+12,419, 0.02x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `SCUDNUKEThermobaric`: 764,587 -> 777,005 (+12,419, 0.02x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `GladiusCannon`: 69,955 -> 79,904 (+9,949, 0.14x) in mods\cameo\ContentPacks\StarCraft\Protoss\yaml\weapons.yaml

## Top 10 biggest relative gains (likely under-priced today)

- `MedicFlare`: 522 -> 2,436 (3.67x) in mods\cameo\ContentPacks\StarCraft\Terran\yaml\weapons.yaml
- `ShtoraLaser`: 5,645 -> 8,226 (0.46x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `MammothTusk2`: 39,956 -> 57,806 (0.45x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `MammothTusk2TargetingComputer`: 39,956 -> 57,806 (0.45x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `RA2PsychicJab_elite`: 5,303 -> 7,653 (0.44x) in mods\cameo\ContentPacks\RedAlert2\Yuri\yaml\weapons.yaml
- `RA2PsychicJab`: 5,337 -> 7,695 (0.44x) in mods\cameo\ContentPacks\RedAlert2\Yuri\yaml\weapons.yaml
- `MonsterTankTuskTesla`: 68,772 -> 97,654 (0.42x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `MammothTuskTesla`: 21,361 -> 30,287 (0.42x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `MammothTuskTeslaTargetingComputer`: 21,361 -> 30,287 (0.42x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml
- `MammothTuskTeslaFragment1`: 11,646 -> 16,434 (0.41x) in mods\cameo\ContentPacks\RedAlert\Soviets\yaml\weapons.yaml

## What a balance pass needs

1. Choose the target `effective_damage` for each affected actor (usually the current total from all *other* warheads, or a re-derived price-aware target).
2. The broken warhead is currently contributing 0; after the fix it will contribute `after_eff - current_eff`.
3. To hold a weapon's power constant while enabling the warhead, reduce `Damage` in `^LightFlameWeapon` (or per-weapon overrides) so the warhead's new contribution matches the desired budget.
4. If the intent is to *buff* these weapons, accept the new numbers and re-run the full balance pipeline (`extract_stats` -> workbook -> `apply_balance --confirm`).
5. Run `review_resolve_diff.py` on the `^LightFlameWeapon` family after the yaml edit, then boot-gate.