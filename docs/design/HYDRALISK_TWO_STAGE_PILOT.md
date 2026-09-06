# Two-stage Hydralisk implementation pilot

**Implemented as an inactive standalone MiniYAML weapon; not safe to activate.**
The live Hydra, all stats, manifests, ledgers and reviewed exception remain unchanged.

## Implementation

- Preserve the resolved chemical main, all four percentage hits and their order.
- Keep the original missile flat-hit slot, increase it to 54000 and replace its
  armor table with the exact damage-weighted center table of the three nonchemical hits.
- Remove only the SmallArms and Arrow flat nodes. Preserve firing/projectile/effect fields.
- Fit one piecewise falloff using a rounded continuous minimax midpoint at each
  original radius knot. Integer damage rounding and between-knot behavior mean
  this is not a claim of optimality for the complete runtime grid.

Range: `0, 70, 100, 140, 200, 210, 280, 300, 350, 400, 420, 600, 800`
Falloff: `100, 72, 61, 50, 34, 33, 24, 21, 15, 10, 6, 2, 0`

## Flat-payload preservation checks

Every integer distance 0–800 is checked for every authored class armor row.
Only the three nonchemical flat hits are compared here, before actor modifiers.
Tag combinations are synthetic routing probes, not claims that every actor/armor
combination exists in the live roster.
Ordinary targets and the two exclusion tags are kept separate. No tolerance is
silently treated as approval; changed cases remain failures of exact preservation.

| Target flags | Cases | Changed | Worst absolute delta | Worst error / original center damage |
|---|---:|---:|---:|---:|
| ordinary | 13617 | 13489 | -2674 | 9.8% |
| BulletImmune | 13617 | 13499 | +19800 | 128.0% |
| wall | 13617 | 13560 | +19998 | 87.1% |
| BulletImmune, wall | 13617 | 13560 | +39600 | 1460.0% |

## Why one flat hit cannot preserve the old behavior

The old nonchemical payload has three different target masks: missile excludes neither
tag, SmallArms excludes BulletImmune, and Arrow excludes wall. The pilot inherits the
broad missile mask. That restores excluded damage; using the union instead would remove
legitimate damage from other components. One common mask cannot represent both cases.

At distance 350, None retains 5616/38880 of its center damage;
Heavy retains 4816/25920. These ratios differ.
A single armor table multiplied by a common falloff cannot reproduce both radial responses.
Per-hit rounding adds further differences; it does not explain away this mismatch.

The merged hit also uses the missile damage types. That does not preserve the separate
BulletDeath contributions. Friendly-fire/target-discovery behavior is not modeled by
the numeric grid and has not been declared equivalent.

## Ordered actor projections

The seven-actor lab holds targets alive and models one enemy impact, including TakeCover
and Corrosion feedback. Values are potential damage, not HP lost or playtest results.

| Actor | Center before → after | Distance 110 before → after | Distance 350 before → after |
|---|---|---|---|
| td_nod_minigunner | 33738 → 33741 | 22476 → 23010 | 10126 → 10259 |
| terran_marine | 41645 → 41648 | 27445 → 28202 | 12124 → 12328 |
| zerg_hydralisk | 51080 → 51083 | 32242 → 33210 | 12975 → 13219 |
| ra1_allies_alliedmediumtank | 45433 → 45436 | 32187 → 30719 | 14627 → 13619 |
| terran_siegetank | 42364 → 42366 | 30355 → 29033 | 14239 → 13307 |
| terran_wraith | 31941 → 31943 | 21160 → 19600 | 7218 → 6172 |
| terran_battlecruiser | 29943 → 29946 | 20674 → 18740 | 7668 → 6409 |

## Disposition

Do not activate this pilot. The two-stage approach preserves the chemical sequence
and improves center behavior, but fitting the splash curve does not solve the target-mask
or armor-distance incompatibility. Exact preservation requires retaining the separate
nonchemical applications, or a new composite runtime implementation. The latter is
disproportionate for this one weapon and is not part of this task.

Current Hydra stays on four profiles. A deliberate redesign remains possible, but its
changed immunity, splash and death-type behavior is a gameplay choice, not a cleanup.

Reproduce with `tools/run-bounded-python.ps1 -PythonArguments @('tools/balance/hydra_two_stage_pilot.py', '--check')`.
The pilot is in `tools/balance/pilots/hydra_two_stage.yaml`, outside all active includes.
No game launch is required for these static checks.
