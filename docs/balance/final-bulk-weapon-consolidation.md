# Final bulk weapon consolidation

This batch is the large closing pass requested after PR #291.  It combines two
independently guarded cohorts and lowers the broad resolved multi-main backlog
from **923 to 847**.  The reduction is 76 rather than the 97 changed definitions
because some weapons still retain other legitimate or unresolved main slices.

## Percentage-inert compatibility folds

Thirty-five source definitions affect 58 resolved variants.  Their retired-root
compatibility slice has the same armor table, blast geometry, damage types,
targeting, relationships, and physical-state binding as the already selected
canonical main.  Only flat damage and the percentage scale differ.  The two flat
slices become one canonical main, while a recalculated scale preserves the old
runtime percentage units.

This cohort preserves nominal damage and all behavior measured by the whole-tree
comparison.  The comparison reports the structural change from two identical
blast entries to one, but the radius, falloff, damage sum, targets, relationships,
physical state, and percentage result remain the same.

## Reviewed canonical-profile folds

Twenty-seven roots cover 39 concrete definitions.  Each complete inheritance
closure passed all of these screens:

- one destination tier already matches both projectile and effect identity;
- every main has the same target and relationship contract;
- the weapon name and role do not contradict the destination;
- nominal flat damage is carried into the selected profile;
- the merged percentage result differs by no more than one HP at every active
  authored health value and never relies on unsafe overflow.

This cohort deliberately adopts the selected canonical armor and blast profile.
Thirty-two definitions gain one HP of percentage damage on some 160-HP targets
because the runtime rounds one folded application instead of several.  Cadence,
weapon-level targeting, projectiles, effects, reports, and non-damage warheads do
not change.

## Rejected hazards

The automated pass rejects rather than guesses when it finds:

- split ground/air routing, including the FLAK-23 AA child;
- physical-state or friendly-fire changes, including BC Yamato, the Latin
  militia Molotov, and several temperature-bearing hybrids;
- percentage quantisation or inherited percentage drift, including the elite
  Freedom Rocket and RA2 radioactive 120 mm descendants;
- semantic conflicts such as an AA Thunderbolt resolving toward high-explosive
  missiles, a mortar resolving toward a cannon profile, and unresolved
  Quantum/railgun identities.

Pricing and the later percentage-damage runtime activation were outside this
earlier batch.
