# Delivery-identity weapon profile consolidation

This follow-up begins from merged PR #292 and consolidates **31 concrete weapon
definitions** across nine complete inheritance roots.  The broad resolved
multi-main count falls from **847 to 829**; the equal-damage broadcast count
falls from **470 to 440**.  The smaller broad reduction is expected because
upgraded and resonance descendants still carry a separate, intentional main.

The selected profile follows the weapon's existing delivery and role:

- D2K heavy machine guns and raider guns use `Bullet_Medium`; light infantry
  keeps `Bullet_Light`.
- the Soviet BTR Tesla closure uses `Tesla_Heavy`, matching its lightning
  projectile and Tesla effects;
- Japanese hovercraft flak uses `Flak_Medium`;
- the Consortium Barracuda's ground chaingun uses `Bullet_Medium`, while its
  separately routed anti-air branch uses `Flak_Medium`.

The Barracuda split was corrected after independent adversarial review.  Its
ground and air branches intentionally do not share one profile.

## Preserved behavior

The whole-tree comparison reports no weapon additions or removals and preserves
nominal main damage, cadence, weapon-level targets, relationships, projectiles,
effects, reports, non-damage warheads, and physical-state behavior.  Twenty-nine
definitions gain exactly one HP of percentage damage on a 160-HP target because
one folded application replaces two separately rounded applications.  No larger
difference occurs across the 155 active and design health values.

## Rejected candidates

The pass leaves split air/ground machine guns, the D2K shotgun inheritance
branch, anti-tank cannon profile conflicts, torpedoes with different target masks,
and artillery closures with chemical or nuclear descendants unchanged. Pricing
and the later percentage-damage runtime activation were outside this earlier batch.
