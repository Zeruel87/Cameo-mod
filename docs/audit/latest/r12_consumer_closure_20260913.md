# R12 compatibility consumer closure

**Read-only. The simulation edits only an in-memory ruleset.**

The historical 369/139/214/16 figures count concrete weapon relationships only. Complete direct closure adds one template consumer, ^Warhead_IncendiaryYakComposition, which already inherits the matching twin. A uniform twin-before-payload chain position reorders warheads for 30 direct consumers that already inherit their twin; the exposed-user changes are the expected input to measured suppression. A separate pure-rename simulation removes the Compatibility names owned by this 36-template cohort with zero resolved field or order changes by keeping the two collision-prone extra-damage payloads distinct as _Auxiliary. This is the safest implementation candidate, but it needs a maintainer ruling because it deliberately does not add twin chaining.

## Inventory

- Compatibility templates: **36**
- Direct relationships: **370** = **369** concrete + **1** template
- Distinct concrete weapons: **361**
- Already inherits matching twin: **140**
- Exposed without matching twin: **214**
- Missing matching twin: **16**

The extra non-concrete edge is `^Warhead_IncendiaryYakComposition -> ^Compatibility_Flame_LightFlat`; the consumer also directly inherits `^Warhead_Flame_Light`.

## Literal chain simulation

The simulation makes every matched compatibility template inherit its twin before the local payload and removes one duplicate direct twin inherit from each already-twin consumer. It then compares every resolved concrete weapon, including descendants.

- Changed concrete weapons: **290**
- Warhead-order changes: **287** (101 pure reorders)
- Resolved field pairs gained/lost: **12117 / 8**
- Already-twin direct consumers changed: **30 / 139**; all **30** include a warhead-order change
- Exposed direct consumers changed: **113 / 213**; these are the inputs whose local suppressions must be measured

This is a blocking correctness result for a bulk writer, not evidence that the debt should remain. The writer must preserve each consumer's original parent ordering, measure exposed-user suppressions from resolved diffs, and verify the complete concrete descendant closure with both field and warhead-order comparisons.

The Python resolver is a planning gate. It does not certify engine duplicate-inheritance or removal legality; those remain separate blocking audits and one cohort boot after a candidate exists.

## Zero-behavior alternative

A pure rename of **36** template keys and **36** payload keys changes **0** resolved concrete weapons.

`LaserExtraDamageCompatibility` and `RailgunExtraDamageCompatibility` cannot collapse onto their existing unsuffixed keys: inherited payload/removal keys already use those names, and the direct unsuffixed proposal suppresses the renamed payload on fifteen resolved weapons. The exact rename therefore uses `LaserExtraDamage_Auxiliary` and `RailgunExtraDamage_Auxiliary`. This removes the deprecated word while preserving the two distinct payloads and their original firing positions.

This candidate resolves the maintainer's deprecated-name goal with no behavior change, but it does not implement the current R12 text's twin chaining. Do not write YAML until the maintainer confirms that name retirement, rather than twin chaining itself, is the binding outcome.

## Per-template direct relationships

| template | twin | relationships | concrete | template | already | exposed | missing |
|---|---|---:|---:|---:|---:|---:|---:|
| `^Compatibility_Arrow_LightFlat` | `^Warhead_Arrow_Light` | 3 | 3 | 0 | 1 | 2 | 0 |
| `^Compatibility_Bullet_LightFlat` | `^Warhead_Bullet_Light` | 2 | 2 | 0 | 0 | 2 | 0 |
| `^Compatibility_Bullet_MediumFlat` | `^Warhead_Bullet_Medium` | 78 | 78 | 0 | 25 | 53 | 0 |
| `^Compatibility_CannonAP_LightFlat` | `^Warhead_CannonAP_Light` | 9 | 9 | 0 | 5 | 4 | 0 |
| `^Compatibility_CannonFire_HeavyFlat` | `^Warhead_CannonFire_Heavy` | 2 | 2 | 0 | 0 | 2 | 0 |
| `^Compatibility_CannonHE_HeavyFlat` | `^Warhead_CannonHE_Heavy` | 22 | 22 | 0 | 12 | 10 | 0 |
| `^Compatibility_CannonHE_MediumFlat` | `^Warhead_CannonHE_Medium` | 16 | 16 | 0 | 6 | 10 | 0 |
| `^Compatibility_Chemical_LightFlat` | `^Warhead_Chemical_Light` | 3 | 3 | 0 | 1 | 2 | 0 |
| `^Compatibility_Chemical_MediumFlat` | `^Warhead_Chemical_Medium` | 5 | 5 | 0 | 3 | 2 | 0 |
| `^Compatibility_Concussion_MediumFlat` | `^Warhead_Concussion_Medium` | 11 | 11 | 0 | 7 | 4 | 0 |
| `^Compatibility_Cryo_MediumFlat` | `^Warhead_Cryo_Medium` | 2 | 2 | 0 | 0 | 2 | 0 |
| `^Compatibility_Demolition_HeavyFlat` | `^Warhead_Demolition_Heavy` | 12 | 12 | 0 | 8 | 4 | 0 |
| `^Compatibility_Demolition_LightFlat` | `^Warhead_Demolition_Light` | 4 | 4 | 0 | 2 | 2 | 0 |
| `^Compatibility_Flak_MediumFlat` | `^Warhead_Flak_Medium` | 24 | 24 | 0 | 11 | 13 | 0 |
| `^Compatibility_Flame_LightFlat` | `^Warhead_Flame_Light` | 8 | 7 | 1 | 6 | 2 | 0 |
| `^Compatibility_Flame_MediumFlat` | `^Warhead_Flame_Medium` | 2 | 2 | 0 | 1 | 1 | 0 |
| `^Compatibility_Laser_ExtraDamage` | `none` | 9 | 9 | 0 | 0 | 0 | 9 |
| `^Compatibility_Laser_HeavyFlat` | `^Warhead_Laser_Heavy` | 26 | 26 | 0 | 17 | 9 | 0 |
| `^Compatibility_Melee_HeavyFlat` | `^Warhead_Melee_Heavy` | 2 | 2 | 0 | 0 | 2 | 0 |
| `^Compatibility_MissileAA_HeavyFlat` | `^Warhead_MissileAA_Heavy` | 4 | 4 | 0 | 1 | 3 | 0 |
| `^Compatibility_MissileAA_LightFlat` | `^Warhead_MissileAA_Light` | 5 | 5 | 0 | 4 | 1 | 0 |
| `^Compatibility_MissileAA_MediumFlat` | `^Warhead_MissileAA_Medium` | 8 | 8 | 0 | 0 | 8 | 0 |
| `^Compatibility_MissileAP_HeavyFlat` | `^Warhead_MissileAP_Heavy` | 15 | 15 | 0 | 2 | 13 | 0 |
| `^Compatibility_MissileAP_LightFlat` | `^Warhead_MissileAP_Light` | 3 | 3 | 0 | 0 | 3 | 0 |
| `^Compatibility_MissileAP_MediumFlat` | `^Warhead_MissileAP_Medium` | 21 | 21 | 0 | 6 | 15 | 0 |
| `^Compatibility_MissileHE_HeavyFlat` | `^Warhead_MissileHE_Heavy` | 7 | 7 | 0 | 3 | 4 | 0 |
| `^Compatibility_MissileHE_LightFlat` | `^Warhead_MissileHE_Light` | 5 | 5 | 0 | 1 | 4 | 0 |
| `^Compatibility_MissileHE_MediumFlat` | `^Warhead_MissileHE_Medium` | 9 | 9 | 0 | 2 | 7 | 0 |
| `^Compatibility_Plasma_HeavyFlat` | `^Warhead_Plasma_Heavy` | 9 | 9 | 0 | 1 | 8 | 0 |
| `^Compatibility_Plasma_MediumFlat` | `^Warhead_Plasma_Medium` | 4 | 4 | 0 | 1 | 3 | 0 |
| `^Compatibility_Quantum_HeavyFlat` | `^Warhead_Quantum_Heavy` | 9 | 9 | 0 | 0 | 9 | 0 |
| `^Compatibility_Railgun_ExtraDamage` | `none` | 6 | 6 | 0 | 0 | 0 | 6 |
| `^Compatibility_Railgun_HeavyFlat` | `^Warhead_Railgun_Heavy` | 12 | 12 | 0 | 6 | 6 | 0 |
| `^Compatibility_TankBusterBeam_UnscopedFlat` | `none` | 1 | 1 | 0 | 0 | 0 | 1 |
| `^Compatibility_Tesla_HeavyFlat` | `^Warhead_Tesla_Heavy` | 9 | 9 | 0 | 7 | 2 | 0 |
| `^Compatibility_Thermobaric_HeavyFlat` | `^Warhead_Thermobaric_Heavy` | 3 | 3 | 0 | 1 | 2 | 0 |
