# Bounded proposals with retained firepower

This is an opt-in, JSON-only calculation, not a class rebalance or an applicable
patch. It never writes YAML, actor costs, anchors or gameplay data. The old class
proposal and range write-back guards remain closed.

## What it does

Given one actor and an explicit **nominal flat damage per simulation tick** target,
the tool calculates a single raw `Damage` on the existing 100 grid. It retains all
firepower modifiers unless the caller explicitly names one local knob to retire.
This target is not per-second DPS, armor-adjusted damage, combat efficiency, or a
price-derived recommendation. No target is inferred from the balance formula.

The calculation uses exact rational arithmetic:

`nominal rate = Damage × retained firepower × Burst / full burst-cycle ticks`

It compares the neighboring grid points, reports the forward result and residual,
and picks the smaller damage on exact ties. Targets below the grid floor are flagged,
not silently declared satisfied. Invalid/nonpositive targets, zero modifiers and
raw Int32-limit overflow are rejected. These bounds do not prove that every armor
multiplier or target-specific runtime intermediate will remain in range.

## Safety boundary

- Exactly one actual, unconditional primary armament, including unpaid/alternate
  slots in the count. No charge/reload/ammunition mechanism outside the small model.
- The primary must be selected by a supported own-actor attack. `AttackMove` and
  `AttackWander` provide orders, not weapon selection. Omitted `Armaments` means
  `primary, secondary`; an explicit empty list stays empty and names are case-sensitive.
  Both armament and selected attack must be enabled/unpaused in a conservative
  zero-condition snapshot. Single-token conditions are supported; compound expressions
  remain unknown and block. This is not a resolver for actual spawn-time conditions.
- Exactly one flat main with no extra damage chips, percentage damage, state or
  integrity feedback, delayed ticks, spawning or unrecognized gameplay effects.
  Known cosmetic effects remain unchanged. Projectile delivery is allowlisted;
  repeated/bouncing variants are rejected.
- The source weapon is conservatively checked against other resolved actors and
  raw weapon references, including non-armament delivery and inheritance. Shared
  references block the proposal pending a separate clone review. This base-YAML
  scan does **not** prove absence of map overrides or script-constructed references.
- Retirement requires an exact, locally authored, unconditional, unscoped plain
  or actor-specific `FirepowerMultiplier` key. Global/class keys are not eligible.
  The prospective actor is re-resolved after removing the local block; an inherited
  same-slot modifier resurfacing is a rejection, not a silent subtraction.
- Structural comparisons require the prospective actor to differ only by that
  exact retirement, and the prospective weapon only by the selected `Damage`.
  Input trees remain unchanged; before/after fingerprints are included.

Conditional bonuses are outside the nominal calculation, not deleted. Armor,
falloff, accuracy, target defenses, player modifiers, per-hit integer rounding,
ammo uptime and actual kill times are not claimed to be simulated.

## Live coverage: deliberately narrow

The [generated census](../audit/latest/retained_firepower_survey.json) checks 1,000
ledger-listed armed actors against active base YAML. Five pass the structural
screen; four of those have shared/reference concerns. **One passes both screens:**
`ra1_allies_raspy`, using `SilencedPPK`. The other 999 stay blocked.

The reason counts record each actor's first rejection, not every independent
problem on that actor. No holds or reviewed exceptions are removed from the wider
weapon inventories. Hydra remains blocked. Its current upstream BulletChem profile
is preserved; the old four-profile experiments are now explicitly historical.
See the [upstream integration report](PR328_UPSTREAM_INTEGRATION.md) for provenance
and current validation failures.

The supported live example retains all modifiers. Safe local-knob retirement is
covered with synthetic resolved-inheritance tests, not presented as a proven
live-roster retirement candidate. This narrow result is not evidence to remove
guards or claim the whole roster can now be restated.

## Example and reproduction

Using the bounded Python wrapper from the isolated worktree:

```powershell
.\tools\run-bounded-python.ps1 -PythonArguments @('tools/balance/propose_retained_firepower.py', '--actor', 'ra1_allies_raspy', '--target-damage-per-tick', '1815/16') -MaxMemoryMB 2048 -MaxSystemMemoryPercent 84 -TimeoutSeconds 120
```

This no-change check returns the existing 15,000 raw Damage, retained factor
121/200 (0.605), and exactly 1815/16 damage per tick with zero nominal residual.
It is a mathematical preservation check, not a recommendation to rebalance the Spy.

`--retire-trait FirepowerMultiplier` is optional and must refer to an eligible
local knob on the selected actor. Omission retains everything. Blocked cases return
JSON with a reason and nonzero exit status; there is no `--confirm` or apply mode.

Run `tools/balance/retained_firepower_survey.py` to check census freshness;
`--write` updates only its diagnostic JSON. Use the same memory/deadline guard.

## Next boundary

The [armament-mode survey](../audit/latest/armament_mode_survey.json) separates
identical primary/garrison weapon pairs from other multiple-armament arrangements.
It resolves inherited slots, records each slot's unconditional firepower factor,
known own/passenger attack selectors, activation uncertainty, conditional modifier
names and the first weapon-only blocker. It does not sum slots or create proposals.

`AttackBase` selects the actor's own armaments by `Armament.Name`.
`AttackGarrisoned` and `AttackOpenTopped` instead borrow passenger armament objects;
the passenger's firepower remains relevant. A host can select both names, and host
conditions, fire ports and passenger compatibility remain runtime constraints.
Consequently, a `primary`/`garrisoned` pair is a topology observation, not proof of
mutual exclusivity, simultaneous damage, or a universal garrison combat mode.

Other base-YAML references are indexed once for the pair cohort. Only the pair's
two exact `Weapon` fields are excluded from its other-reference count; same-actor
delivery references, other actors and raw weapon inheritance remain visible.
Maps/scripts still require separate review. A weapon-only screen pass would not
establish actor/proposal eligibility or authorize modifier retirement.

Run `tools/balance/armament_mode_survey.py` to check freshness; `--write` updates
diagnostic JSON only. The multi-armament proposal guard remains closed. Any useful
future expansion needs a supported damage model, explicit mode-preservation policy
and sharing review, not a blanket relaxation of slot counting.

## Historical validation before upstream integration (2026-09-05)

- Full suite: 82 isolated modules, **802 passed**, zero skipped or failed; includes
  21 new proposal tests. Sampled process-tree peak 1,379.7 MB; PC peak 46.5%.
- Live CLI no-change Spy result agrees exactly; Hydra returns a blocked result.
  Actor-specific/local retirement, inherited override resurfacing, scoped/conditional
  preservation, shared/delivery references, burst gaps, engine-default reload (one
  tick), rounding, low targets, overflow and mutation-free rejection are tested.
- All 32 ledgers remain zero-drift. Generator, percentage-runtime, structure/decision
  and all three diagnostic-report freshness checks pass. Gameplay and old generator
  guards are unchanged; diff whitespace checks pass.
- Known failures remain visible: 216 physical-state findings and 192 provisional
  band flags. They are not suppressed or treated as balance targets.
- Independent review approved the corrected implementation and scope; its final
  full-suite condition is now satisfied. No game launch, write-back or merge.
