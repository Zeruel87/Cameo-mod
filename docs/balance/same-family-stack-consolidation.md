# Same-family weapon-stack consolidation

This batch deliberately changes balance profiles. It is not a behavior-preserving
cleanup.

## Selected scope

- 54 machine-gun variants move from a Light + Medium bullet blend to the Medium
  bullet profile already used by their projectile and impact effect.
- `CycloneRockets` and `CycloneRocketsLockOn` move from a Light + Medium explosive
  missile blend to Light explosive missiles, matching their delivery/effect tier.
- `RA2Chemspray2` and `RA2Chemspray_elite` move from a Medium + Heavy chemical
  blend to Heavy chemical, matching their delivery/effect tier.

The result is 58 fewer multi-main concrete weapons: 981 becomes 923 in the broad
resolved-weapon survey.

## Deliberate gameplay changes

- Each weapon adopts the destination tier's armor table and blast geometry rather
  than averaging two tiers. Center damage can move by roughly 17 percent depending
  on armor. For example, `RAVulcan` changes from 21,440 to 18,720 against Scout and
  from 22,240 to 24,160 against Plate.
- The two folded percentage applications become one. Thirty-seven variants gain
  one HP of percentage damage against some active 160-HP and 250-HP targets because
  the runtime rounds once instead of twice. No accepted case differs by more than
  one HP.
- The chemical pair's corrosion follows its new Heavy damage/radius profile because
  physical-state application scales from post-armor damage.

## Preserved contracts

The full resolved-tree comparison confirms no weapon additions/removals and no
changes to nominal flat totals, cadence, weapon-level targeting, relationships,
projectiles, effects, firing reports, or non-damage warheads. Tests also pin every
selected destination armor/percentage table and blast profile.

## Deferred hazards

The batch rejects candidates whose merged percentage arithmetic exceeds the
checked result range or moves by more than one HP at any active health value. It also defers target-routing
conflicts such as `RA220mmrapid`, mixed-family descendants, rifle/shotgun role
ambiguities, and pricing. The later percentage-damage runtime activation was
deliberately handled as a separate change.
