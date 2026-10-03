# Hydralisk: recommendation after the BulletChem experiment

Implementation follow-up: the [two-stage pilot](HYDRALISK_TWO_STAGE_PILOT.md) is
now built and exhaustively screened. It preserves the chemical sequence but fails
target-mask and radial-damage preservation. It is deliberately inactive; no live
collapse is recommended. A custom composite runtime would be disproportionate.

## Decision

Keep current Hydralisk gameplay in this PR. Accept Aedis's **corrosive projectile
role** as a useful design idea, but do not accept the staged 72,000-damage collapse
as a safe implementation of it. No examined single-main candidate preserves the
current combination of infantry, air, state delivery and splash behavior.

If reducing the number of damage mains is still desirable, investigate the
two-stage option first: retain the chemical pre-hit and experimentally combine
the nonchemical flat profiles. It is a better experimental starting point than a
one-hit replacement, not an approved implementation. The current four-profile
exception remains valid until those differences have an explicit decision.

## What changed our understanding

The initial armor worksheet was useful screening, but not a runtime verdict.
The ordered-impact experiment adds several effects that a raw-total comparison
cannot capture:

- **Posture:** Nod Minigunners go prone after the first component. Later components
  are reduced; putting everything in the first hit bypasses that reduction.
- **State availability:** Nod Minigunners and Marines have no Corrosion meter.
  Nominal Corrosion output is not received state on those actors.
- **Feedback:** on actors with a meter, the chemical hit changes vulnerability
  before later components. Both currently authored Corrosion bindings execute,
  and the second binding can observe the first binding's changes.
- **Geometry:** restoring the damage at distance zero does not restore the spatial
  response. Current damage is distributed across different radii and falloff curves.

This is why a new armor table alone is insufficient, even when its intended role
is a better fit. It does not show that reference-based balance is inherently flawed;
it shows that translating a role into runtime behavior needs more than a raw sum.

## Candidate results

These are **potential single-impact damage ratios**, not actual HP lost, DPS,
kill times or playtesting. The model holds victims alive while all components
execute, uses base unshielded/unupgraded actors and allows within-impact posture
and Corrosion feedback. It excludes tick-based DoT, relaxation, healing, projectile
accuracy, hitshape discovery, alliances and upgrade states.

| Experiment | Nod minigunner | Marine | Hydralisk | Medium tank | Wraith | Battlecruiser |
|---|---:|---:|---:|---:|---:|---:|
| Aedis staged 72,000 | 3.32x | 2.20x | 1.84x | 1.35x | 0.94x | 1.02x |
| BulletChem 33,000 | 1.51x | 1.00x | 0.82x | 0.60x | 0.42x | 0.41x |
| 33,000 with flat air rows restored | 1.51x | 1.00x | 0.82x | 0.60x | 0.90x | 0.97x |
| Two-stage close-impact control | ~1.00x | ~1.00x | ~1.00x | ~1.00x | ~1.00x | ~1.00x |

The air-restored candidate deliberately uses custom experimental rows, not a new
canonical family. Keeping the old four percentage hits on that candidate also
does not restore the damage sequence or the flat-derived state budget.

The two-stage control differs by only 2-3 engine health units at the center for
these seven tested targets (the detailed report also includes Siege Tank).
That is not general equivalence. Against Marine armor its potential damage at
distance 110 rises from 27,445 to 30,280 (about 10%); at 350 it rises about 14%.
It also changes targeting and death-type behavior. Do not apply that control as-is.

## Proposed next gameplay decision, grouped for review

1. **Role:** preserve the current mixed infantry/air role, or intentionally shift it?
   If shifting, define acceptable changes separately for unarmored/prone infantry,
   Flak infantry, Helicopter/Spaceship aircraft and tanks. One global average is not
   a substitute for those decisions.
2. **Delivery:** allow an explicit two-stage corrosive projectile, or require one
   main and accept changed posture/state sequencing? A descriptive weapon type does
   not have to imply one runtime damage instruction.
3. **Secondary effects:** choose Corrosion and percentage behavior independently
   from flat damage. Do not change current duplicate state delivery globally as a
   side effect of this unit experiment.

Until those decisions are made, keep cost, HP, speed, range, reload and the
travelling-spore projectile unchanged. No game launch is authorized. A later
gameplay pilot must retain raw inventory visibility, compare target eligibility
and all distance/armor cases, and audit any collateral generator changes.

## Reproduce without the earlier memory spike

From the percentage-balance-tooling worktree in PowerShell 7:

```powershell
.\tools\run-bounded-python.ps1 -PythonArguments @('tools/balance/hydra_impact_lab.py', '--write') -MaxMemoryMB 512 -TimeoutSeconds 60
.\tools\run-bounded-tests.ps1 -MaxMemoryMB 2048 -MaxSystemMemoryPercent 88 -ModuleTimeoutSeconds 180 -TotalTimeoutSeconds 1200
```

The guard samples private memory across discovered process descendants and enforces
a deadline while output streams drain. It also stops at 88% sampled PC memory use,
leaving margin below Blackrobe's 90% ceiling. It is not an OS allocation sandbox: ancestry
sampling can miss extremely short-lived intermediary processes. The test runner
uses fresh sequential processes so ruleset caches do not accumulate across modules.

Detailed evidence: [ordered-impact report](HYDRALISK_IMPACT_LAB.md),
[machine-readable traces](../audit/latest/hydralisk_impact_lab.json),
[earlier nominal screen](HYDRALISK_CANDIDATE_SCREEN.md).
