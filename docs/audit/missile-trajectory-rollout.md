# Broader missile trajectory correction

Extend the visually approved Patriot approach to conventional ground-to-air and air-to-ground missiles. This is a data-only guidance adjustment, not a new ballistic projectile model. It changes simulated flight and may trade damage efficiency for appearance; the maintainer accepted that tradeoff for this direction. Representative Nod SAM, Ixian Air Drone and Patriot comparisons were visually approved.

## Scope and selection

Active mod.yaml includes and resolved actor armaments identify the firing domain. Ordinary missile artwork and weapon roles select the initial cohort; arrows, spells, plasma/railgun projectiles, torpedoes, air mines and kamikaze effects remain outside it. High-cruise profiles (over 1024 world units), steep launches (minimum angle 192 or above), and specially low/high turn rates are preserved. The already approved Patriot Thunderbolt 40 override is unchanged.

Reduce vertical turning only where nominal maximum range exceeds the current launch-speed terminal-guidance threshold. The threshold is `3 * (MaximumLaunchSpeed * 6400 / (157 * VerticalRateOfTurn.Facing))`, with integer arithmetic and the normal Speed fallback. New rates roughly halve facing-unit turning, rounded upward with a floor of 12 angle units. This starts the terminal approach earlier while retaining horizontal steering, speed, homing delay and cruise altitude. The threshold is a selection diagnostic, not a guarantee for upgraded ranges or every target motion.

For weapons used only by aircraft, a positive minimum launch angle is lowered to -128 so a ground target can be aimed at downward immediately. Maximum launch angles remain intact. The Ixian Air Drone changes minimum launch angle 64 to -128 and vertical turning 20 to 12. Its inherited ground-launch tilt previously forced an initial upward pitch despite the target being below the drone. Shared ground/air weapons do not receive the downward-launch adjustment.

Some ground-to-air weapons also attack ground targets; their shared projectile changes both uses. Dedicated air-to-air siblings, artillery, fragments and other unselected descendants have explicit preservation overrides where required. Generic templates are not edited.

## Validation

- 2,896 complete resolved weapon definitions compared.
- Exactly 203 weapons change, and only the declared vertical-turn/minimum-launch-angle fields.
- 22 inheritance guards preserve existing descendant behavior.
- Damage, speed, horizontal turning, reload, burst, target eligibility, effects and audio are unchanged.
- Independent complete-field comparison passed; the engine loaded the full modified default rules successfully using `--faction-report`.
- The automatic comparison map now includes Nod SAM and Ixian Air Drone A/B passes before the existing Patriot passes. Lua syntax and engine resolution of the Ixian test actor passed. These checks do not establish in-game visual quality or hit-rate parity.
- The maintainer visually approved the automatic Nod SAM, Ixian Air Drone and Patriot A/B comparisons. This is representative visual coverage, not an in-game check of all 203 weapons or measured hit-rate parity.
- See `missile-trajectory-rollout.json` for the exhaustive per-weapon field changes and preservation guards.
