# Classic-four MCV/support durability batch — 2026-09-18

This is the support slice in the aggregate classic-four harvester/pipeline/
support/transport milestone. It applies the newest reference map's complete
chassis projections to four MCVs and two unarmed RA1 support vehicles. MCV
prices follow the reference map. The gap generator and radar jammer retain
their authored 5,000 costs: their reference rows are chassis-only, and their
strategic shroud/jamming/deflection abilities have no class or special input
that justifies a 1,640/1,710 replacement.

## Evidence and scope

Source: `docs/audit/latest/Cameo-reference-map-original-four-20260916.html`.
Every applied MCV row has complete HP, Speed and Cost evidence (2/2 or 3/3
sources). The two support rows have chassis evidence; their costs are held
because the map has no class or special ability input for repricing. No actor-
level weapon projection or weapon, warhead, `Burst` or `BurstDelays` field is
changed.

The shared `^MCV` template is not edited: it feeds MCVs across roughly twenty
other packs. The four classic MCVs receive materialized per-actor blocks at the
end of their actor nodes, after `Inherits:`, so the template's other users stay
unchanged. The two RA1 support vehicles already own their chassis blocks and
are patched in place.

## Applied values

| Actor | HP | Speed | TurnSpeed | Self-heal Step | HpPerStep | Cost |
|---|---:|---:|---:|---:|---:|---:|
| `td_gdi_mobileconstructionvehicle` | 300,000 -> **294,000** | 75 -> **65** | 15 -> **13** | 120 -> **118** | 15,000 -> **14,700** | 5,000 -> **4,920** |
| `td_nod_mobileconstructionvehicle` | 300,000 -> **294,000** | 75 -> **65** | 15 -> **13** | 120 -> **118** | 15,000 -> **14,700** | 5,000 -> **4,920** |
| `ra1_allies_alliedmobileconstructionvehicle` | 300,000 -> **253,000** | 75 -> **70** | 15 -> **14** | 120 -> **101** | 15,000 -> **12,650** | 5,000 -> **4,650** |
| `ra1_soviets_mobileconstructionvehicle` | 300,000 -> **253,000** | 75 -> **70** | 15 -> **14** | 120 -> **101** | 15,000 -> **12,650** | 5,000 -> **4,650** |
| `ra1_allies_mobilegapgenerator` | 25,000 -> **96,000** | 75 -> **76** | 30 -> **30** | 10 -> **38** | 1,250 -> **4,800** | **5,000 held** |
| `ra1_allies_mobileradarjammer` | 25,000 -> **72,000** | 100 -> **74** | 40 -> **30** | 10 -> **29** | 1,250 -> **3,600** | **5,000 held** |

HP uses the accepted 1,000 grid. `Repairable.HpPerStep` follows `HP / 20`
exactly; `ChangesHealth@SelfHealing.Step` is the nearest integer to
`HP / 2500`, matching the existing audit tolerance. Speed is the nearest
integer. Costs use the 10-credit grid with half-up handling at an exact
5-credit tie. A held support cost is excluded from this grid calculation.
TurnSpeed follows the resolved actor's existing formula: the MCVs follow
`round(Speed / 5)`; the two support actors' existing doubled turn lane follows
`2 * round(Speed / 5)`.

The doubled support lane is not inferred from the actor name: both actors
currently carry `AttackFrontal` support/dummy traits and no turret, which is
why the audit selects F10 rather than F8. Removing those traits later would be
a separate design change and would require revisiting their TurnSpeed values.

## Related aggregate transport slice

`td_gdi_chinooktransport`, `td_nod_chinooktransport`,
`ra1_allies_alliedchinooktransport` and `ra1_soviets_hiptransport` are applied
by the sibling transport slice in this aggregate. Their authored costs remain
the passenger sums; see
[`PLAYTEST_CLASSIC_FOUR_TRANSPORT_CHASSIS_20260918.md`](PLAYTEST_CLASSIC_FOUR_TRANSPORT_CHASSIS_20260918.md)
for the full-load, capacity, weight, and cost contract.

## Playtest focus

- Confirm MCV price reductions do not make early expansion strictly dominant.
- Confirm the TD and RA1 MCV speed reductions preserve deployment timing and
  do not make an MCV unable to escape harassment.
- Confirm the gap generator's large HP increase while retaining its 5,000 cost
  does not make mobile stealth support the default opening.
- Confirm the radar jammer's speed reduction is still usable while its larger
  health pool survives the approach to a frontline.

`mods/cameo/rules/camea.yaml` contains a commented-out MCV that inherits the TD
GDI MCV directly. It is inert in the current `mod.yaml` graph, but must be
reviewed before Camea is re-enabled because it would intentionally inherit the
TD-specific override. The inactive `mods/cameo/rules/tomorrow.yaml` also has
`mcv.answer` inheriting `^MCV` and an `mrj.answer` support actor; re-enable review
must resolve both actors before the shared template or classic MCV overrides are
changed.
