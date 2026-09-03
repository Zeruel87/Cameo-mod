# Warhead-split guard (multi-warhead over-damage)


## FAIL 1 — broadcast fingerprint / every MAIN identical (135 vs baseline 135)

_at or below baseline_ — pre-existing **W24** debt (135 weapons), not a regression. The ratchet catches new broadcasts without blocking every commit on the existing pile. **Lower `BROADCAST_BASELINE` as W24 collapses weapons; never raise it.**

| weapon | mains | per_warhead | total |
|---|---|---|---|
| 110mm_Gun | 3 | 10000 | 30000 |
| 12MissilesSpawnerScud | 4 | 24000 | 96000 |
| AlliedTankDestroyerCannon | 2 | 12000 | 24000 |
| AphidCryo_AA | 2 | 8000 | 16000 |
| Aphid_AA | 2 | 8000 | 16000 |
| AsianChaosMine | 2 | 125000 | 250000 |
| AsianPhoenixRocket | 3 | 20000 | 60000 |
| AsianPhoenixRocket_elite | 3 | 20000 | 60000 |
| BikeRockets | 2 | 8000 | 16000 |
| CabalHeavyReaperMissiles | 4 | 12000 | 48000 |
| CabalReaperMissiles | 4 | 8000 | 32000 |
| CommandoM16 | 2 | 4000 | 8000 |
| CommandoSniper | 2 | 20000 | 40000 |
| D2K_Rocket_Trooper1 | 3 | 8000 | 24000 |
| D2K_Rocket_Trooper2 | 3 | 8000 | 24000 |
| D2K_Rocket_Trooper_AA | 3 | 10000 | 30000 |
| D2K_Rocket_Trooper_AGOnly | 3 | 10000 | 30000 |
| D2K_SiegeQuad | 4 | 12000 | 48000 |
| DredMissile | 3 | 30000 | 90000 |
| DuelistTankCannon | 6 | 14000 | 84000 |
| GlaveCanon | 2 | 8000 | 16000 |
| GoliathMG | 3 | 2000 | 6000 |
| GradRockets | 2 | 8000 | 16000 |
| GrenadeRA | 2 | 8000 | 16000 |
| HMG | 3 | 2000 | 6000 |
| HMG_fremen | 3 | 2000 | 6000 |
| HMGh | 3 | 2000 | 6000 |
| HMGo_upgrade | 3 | 2000 | 6000 |
| HammerTankCannon | 2 | 6000 | 12000 |
| HammerTankCannonThermobaric | 4 | 4000 | 16000 |
| HeavyIxianCombatTankCannon | 3 | 6000 | 18000 |
| HellfireCryo | 2 | 8000 | 16000 |
| IdolCannon | 4 | 10000 | 40000 |
| IxianCombatTankCannon | 3 | 4000 | 12000 |
| JapanesePlasmaBomb | 3 | 10000 | 30000 |
| JimRaynorMachineGun | 2 | 2000 | 4000 |
| KodiakCannonSonic | 2 | 22000 | 44000 |
| KotinCannon | 2 | 6000 | 12000 |
| KotinCannonThermobaric | 4 | 4000 | 16000 |
| LMG | 2 | 2000 | 4000 |


_... and 95 more._


## Review — routing-revealed composites (0)

Exact-fingerprint exceptions for pre-existing composites whose dead legacy slots previously masked them from the ratchet. Any main-key or damage change removes the exception and is checked normally.

_none found_


## FAIL 2 — FriendlyFire louder than the shot (0)

None. ✅


## Review — high uniform stacks (informational, 35)

Allowed, but 8000+ per-warhead x N is a big total — confirm it is intended (not flattening residue).

| weapon | mains | per_warhead | total |
|---|---|---|---|
| 110mm_Gun | 3 | 10000 | 30000 |
| 12MissilesSpawnerScud | 4 | 24000 | 96000 |
| AsianPhoenixRocket | 3 | 20000 | 60000 |
| AsianPhoenixRocket_elite | 3 | 20000 | 60000 |
| CabalHeavyReaperMissiles | 4 | 12000 | 48000 |
| CabalReaperMissiles | 4 | 8000 | 32000 |
| D2K_Rocket_Trooper1 | 3 | 8000 | 24000 |
| D2K_Rocket_Trooper2 | 3 | 8000 | 24000 |
| D2K_Rocket_Trooper_AA | 3 | 10000 | 30000 |
| D2K_Rocket_Trooper_AGOnly | 3 | 10000 | 30000 |
| D2K_SiegeQuad | 4 | 12000 | 48000 |
| DredMissile | 3 | 30000 | 90000 |
| DuelistTankCannon | 6 | 14000 | 84000 |
| IdolCannon | 4 | 10000 | 40000 |
| JapanesePlasmaBomb | 3 | 10000 | 30000 |
| LatinBuggyRocket | 4 | 10000 | 40000 |
| LatinBuggyRocket_elite | 4 | 10000 | 40000 |
| Lunar_GreenGrilleArty | 4 | 16000 | 64000 |
| Lunar_GreenGrilleArty_elite | 4 | 16000 | 64000 |
| NaxGrilleArty | 3 | 16000 | 48000 |
| NaxGrilleArty_elite | 3 | 16000 | 48000 |
| OIBigPlasmaCannon | 3 | 8000 | 24000 |
| RA160mmE_rad_elite | 4 | 36000 | 144000 |
| RA2Comet | 3 | 20000 | 60000 |
| RA2Comet_elite | 3 | 20000 | 60000 |
| RA2Robotmm | 3 | 8000 | 24000 |
| RA2Robotmm_elite | 3 | 8000 | 24000 |
| RA2SCUD | 3 | 30000 | 90000 |
| RA2SCUDELITE | 4 | 30000 | 120000 |
| RA2SCUD_fire | 3 | 30000 | 90000 |
| RA2SCUD_tesla | 3 | 30000 | 90000 |
| SiegeTankCannon | 3 | 10000 | 30000 |
| V3Explode | 3 | 10000 | 30000 |
| YakTeslaBomb | 4 | 40000 | 160000 |
| d2k_grenade | 3 | 10000 | 30000 |

