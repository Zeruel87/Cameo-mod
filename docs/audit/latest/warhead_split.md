# Warhead-split guard (multi-warhead over-damage)


## FAIL 1 — broadcast fingerprint / every MAIN identical (67 vs baseline 72)

_at or below baseline_ — pre-existing **W24** debt (67 weapons), not a regression. The ratchet catches new broadcasts without blocking every commit on the existing pile. **Lower `BROADCAST_BASELINE` as W24 collapses weapons; never raise it.**

| weapon | mains | per_warhead | total |
|---|---|---|---|
| 12MissilesSpawnerScud | 4 | 24000 | 96000 |
| AlliedTankDestroyerCannon | 2 | 12000 | 24000 |
| AphidCryo_AA | 2 | 8000 | 16000 |
| Aphid_AA | 2 | 8000 | 16000 |
| AsianChaosMine | 2 | 125000 | 250000 |
| AsianPhoenixRocket | 3 | 20000 | 60000 |
| AsianPhoenixRocket_elite | 3 | 20000 | 60000 |
| CommandoRocketLauncher | 2 | 40000 | 80000 |
| CycloneRockets | 2 | 4000 | 8000 |
| CycloneRocketsLockOn | 2 | 4000 | 8000 |
| D2K_Rocket_Trooper2 | 3 | 8000 | 24000 |
| D2K_Rocket_Trooper_AA | 3 | 10000 | 30000 |
| D2K_Rocket_Trooper_AGOnly | 3 | 10000 | 30000 |
| GoliathMG | 3 | 2000 | 6000 |
| HMGo_upgrade | 3 | 2000 | 6000 |
| HellfireCryo | 2 | 8000 | 16000 |
| IdolCannon | 8 | 10000 | 80000 |
| JimRaynorMachineGun | 2 | 2000 | 4000 |
| KodiakCannonSonic | 2 | 22000 | 44000 |
| MagicOrb | 2 | 12000 | 24000 |
| MagicOrb2 | 2 | 4000 | 8000 |
| MissileAttackRobotGun | 2 | 24000 | 48000 |
| MissileAttackRobotGun_elite | 2 | 24000 | 48000 |
| NaxiMP40 | 3 | 2000 | 6000 |
| NaxiMP40_elite | 3 | 2000 | 6000 |
| NodTorpTube | 2 | 8000 | 16000 |
| NodTorpTubeBlackMarket | 2 | 8000 | 16000 |
| OIBigPlasmaCannon | 3 | 8000 | 24000 |
| RA2Comet | 3 | 20000 | 60000 |
| RA2Comet_elite | 3 | 20000 | 60000 |
| RA2DiskDrain | 2 | 2000 | 4000 |
| RA2KirovBomb_nuclear | 2 | 80000 | 160000 |
| RA2KirovBomb_nuclear_elite | 2 | 100000 | 200000 |
| RA2KirovBomb_rad | 2 | 48000 | 96000 |
| RA2KirovBomb_tesla | 2 | 80000 | 160000 |
| RA2Robotmm | 3 | 8000 | 24000 |
| RA2Robotmm_elite | 3 | 8000 | 24000 |
| SCUD | 2 | 60000 | 120000 |
| SCUDIrak | 2 | 60000 | 120000 |
| SamuraiBladeCharged | 4 | 10000 | 40000 |


_... and 27 more._


## Review — exact gameplay restorations (0)

_none found_


## Review — routing-revealed composites (0)

Exact-fingerprint exceptions for pre-existing composites whose dead legacy slots previously masked them from the ratchet. Any main-key or damage change removes the exception and is checked normally.

_none found_


## FAIL 2 — FriendlyFire louder than the shot (0)

None. ✅


## Review — high uniform stacks (informational, 14)

Allowed, but 8000+ per-warhead x N is a big total — confirm it is intended (not flattening residue).

| weapon | mains | per_warhead | total |
|---|---|---|---|
| 12MissilesSpawnerScud | 4 | 24000 | 96000 |
| AsianPhoenixRocket | 3 | 20000 | 60000 |
| AsianPhoenixRocket_elite | 3 | 20000 | 60000 |
| D2K_Rocket_Trooper2 | 3 | 8000 | 24000 |
| D2K_Rocket_Trooper_AA | 3 | 10000 | 30000 |
| D2K_Rocket_Trooper_AGOnly | 3 | 10000 | 30000 |
| IdolCannon | 8 | 10000 | 80000 |
| OIBigPlasmaCannon | 3 | 8000 | 24000 |
| RA2Comet | 3 | 20000 | 60000 |
| RA2Comet_elite | 3 | 20000 | 60000 |
| RA2Robotmm | 3 | 8000 | 24000 |
| RA2Robotmm_elite | 3 | 8000 | 24000 |
| SamuraiBladeCharged | 4 | 10000 | 40000 |
| YakTeslaBomb | 8 | 40000 | 320000 |

