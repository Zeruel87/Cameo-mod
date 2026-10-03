# Four-faction Sunday playtest handoff — 12 September 2026

This is the execution sheet for a maintainer-authorized Sunday runtime review.
It does not authorize a build, game launch, faction approval, balance writeback
or merge. The static candidate and review map remain the evidence baseline.

## Candidate state

- Scope: current Cameo plus TD GDI, TD Nod, RA1 Allies and RA1 Soviets references.
- Review branch: `codex/overnight-integration-20260910` on Blackrobe's fork.
- Published static checkpoint before this handoff: `6abbcd9f4` in draft PR #345.
- Review map: `docs/audit/latest/reference_map_clean_20260911.html`.
- The map reports source-local `damage/tick`; it is not a sustained gameplay DPS
  claim and contains no applied proposal values.
- The pending class map is review-only. It shows the approved `after` class
  column but does not change actor templates or live class membership.

## Authorization gate

Before any runtime action, Blackrobe must explicitly authorize the build/launch
and name the exact candidate commit or local diff to test. If that authorization
is absent, stop at the static checklist and record the missing authorization;
do not infer it from a Sunday request or from this document.

When authorized, record:

1. branch and full `HEAD` SHA;
2. engine pin and generated DLL/source state;
3. map, player count, difficulty, factions and starting credits;
4. whether upgrades, promotions and cargo changes are live in that build; and
5. the exact scenario result and any reproduction steps.

Use the repository preflight before an engine build. Do not use `--check-yaml`,
change `mod.config` or `engine/VERSION`, or describe a menu load as gameplay
proof. A maintainer may provide runtime evidence instead of a local launch.

## Minimal scenario order

Run only the scenarios needed for the candidate under review. Record `PASS`,
`FAIL`, or `UNTESTED` with the build identity.

### 1. Baseline control

- Start one unupgraded match for each selected faction pair.
- Check construction, production, movement and ordinary ground fire for one
  infantry, one main battle tank and one artillery or rocket unit.
- Check that no reference-map number is treated as an automatic balance target.

### 2. Target and payload closure

- Fire the PDLaser pair at a grounded and an airborne `^ShootableMissile` state;
  record whether the projectile is destroyed, not merely whether a warhead
  applies. Damage 1 versus 10,000 HP remains an unapproved balance decision.
- Use PointDefenseTesla as the control interception route; its existing damage
  and mask are evidence, not a requested PDLaser damage value.
- If the selected scenario reaches them, record flying-infantry target tags,
  the Stealth Tank `CHFlame` air route, and the V2 Tesla/SCUD parent role
  separately. Do not widen a shared warhead to clear a static warning.

### 3. Promotion and cargo observation

- Test only if the approved candidate actually contains the promotion/cargo
  batch. The 1500-credit-per-tier direction is a pilot input, not applied here.
- For a loaded transport, record passenger identities, total weight, purchase
  cost, capacity and firing behavior. Keep naval-empty and manual-loading rows
  as `NOT_APPLICABLE` unless the maintainer changes that policy.
- Do not mix an upgrade or promotion state into the unupgraded baseline result.

## Findings record

For every observation, retain the scenario, actor/weapon identity, state,
expected rule, observed result, reproduction steps and whether it is a new
regression. Static mismatches, unsupported payloads and policy decisions stay
separate from runtime findings. A failed historical suite is reported as a
baseline limitation, never as a green runtime result.

Startup evidence is now available in
[`master_boot_baseline_20260912.md`](master_boot_baseline_20260912.md): a clean
master worktree built and reached the menu with no new exception log. It is a
baseline receipt only; representative gameplay scenarios for the exact Sunday
candidate remain `UNTESTED`.

The runtime section remains open until a maintainer supplies or authorizes this
evidence. Until then, the next unblocked work is static candidate review and
decision preparation; Phase A faction approval, numerical pricing, YAML
writeback and merge remain separate decisions.
