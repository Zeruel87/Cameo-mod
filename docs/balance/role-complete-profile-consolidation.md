# Role-complete weapon profile consolidation

This follow-up begins from merged PR #293 and finishes **20 concrete weapon
definitions** across seven complete inheritance roots. The broad resolved
multi-main count falls from **829 to 810**, the fired count falls from **614 to
599**, and the equal-damage broadcast count falls from **440 to 432**.

The selected profile follows the authored delivery and unit role:

- Mirage and Heavy Mirage weapons use `CannonAP_Light` and restore the authored
  `FireDeath` tag to the full hit;
- Psychic Jab uses `CannonHE_Medium` and restores its authored `FireDeath` and
  `Incendiary` tags to the full hit;
- the Ixian air drone and Ordos air mine use `MissileAP_Heavy` for their missile
  payload (the air mine keeps its distinct air-only `1Dam` warhead);
- the Naxis Maus and Ratte superheavy cannons use `CannonHE_Heavy` geometry;
- the Steel Consortium Manta uses `Bullet_Medium` on its ground route and
  `Flak_Medium` on its separately routed anti-air route, including resonance
  bounces.

The whole-tree comparison reports no weapon additions or removals and preserves
nominal main damage, cadence, weapon-level targets, relationships, projectiles,
effects, reports, non-damage warheads, and physical-state behavior. The Manta's
four separately rounded percentage applications become one: on the two smallest
design health values (160 and 250 HP), this changes 4 to 6 HP and 8 to 10 HP;
all other 153 audited health values match. This bounded difference is accepted
for the clean ground/air role split.

Pricing and the later percentage-damage runtime activation were outside this
earlier batch.
