# Warhead-split guard (multi-warhead over-damage)


## FAIL 1 — broadcast fingerprint / every MAIN identical (14 vs baseline 69)

_at or below baseline_ — pre-existing **W24** debt (14 weapons), not a regression. The ratchet catches new broadcasts without blocking every commit on the existing pile. **Lower `BROADCAST_BASELINE` as W24 collapses weapons; never raise it.**

| weapon | mains | per_warhead | total |
|---|---|---|---|
| 12MissilesSpawnerScud | 4 | 24000 | 96000 |
| DredMissile | 3 | 30000 | 90000 |
| IdolCannon | 4 | 10000 | 40000 |
| NaxiMP40 | 3 | 2000 | 6000 |
| NaxiMP40_elite | 3 | 2000 | 6000 |
| RA2SCUD | 3 | 30000 | 90000 |
| RA2SCUD_fire | 3 | 30000 | 90000 |
| RA2SCUD_tesla | 3 | 30000 | 90000 |
| TS155mm_bluenuke | 2 | 60000 | 120000 |
| TSTacticalChemMissileDamage | 2 | 10000 | 20000 |
| TSTacticalMissileDamage | 2 | 10000 | 20000 |
| TSVulcan | 2 | 2000 | 4000 |
| ThermobaricFlame | 2 | 2000 | 4000 |
| V3Explode | 3 | 10000 | 30000 |


## Review — exact gameplay restorations (0)

_none found_


## Review — routing-revealed composites (0)

Exact-fingerprint exceptions for pre-existing composites whose dead legacy slots previously masked them from the ratchet. Any main-key or damage change removes the exception and is checked normally.

_none found_


## FAIL 2 — FriendlyFire louder than the shot (0)

None. ✅


## Review — high uniform stacks (informational, 7)

Allowed, but 8000+ per-warhead x N is a big total — confirm it is intended (not flattening residue).

| weapon | mains | per_warhead | total |
|---|---|---|---|
| 12MissilesSpawnerScud | 4 | 24000 | 96000 |
| DredMissile | 3 | 30000 | 90000 |
| IdolCannon | 4 | 10000 | 40000 |
| RA2SCUD | 3 | 30000 | 90000 |
| RA2SCUD_fire | 3 | 30000 | 90000 |
| RA2SCUD_tesla | 3 | 30000 | 90000 |
| V3Explode | 3 | 10000 | 30000 |

