# Buggy Mk II and Humvee Mk II reference review

## Conclusion

The HP reversal is in a proposed reference projection, not the current Cameo stats.
Combined Arms has an unused upgraded Nod buggy reference. Adding it improves coverage
but does not itself restore the intended GDI-heavier/Nod-faster relationship. The pair
needs explicit role/tier review before any fitted values are applied.

This is a read-only comparison. No reference assignment, actor stat or weapon has been
changed for this pair. The DTA source version remains unverified pending Aedis's files.

## Current values and projection

Measured from Cameo base `86b41c007`, whose relevant combat files are unchanged by
upstream `50b7d001b`. Projection uses the existing `reference_targets.target_for` and
the committed corpus; it is not a new balance formula.

| measure | GDI Humvee Mk II | Nod Buggy Mk II |
|---|---:|---:|
| current HP | 37,500 | 25,000 |
| current speed | 115 | 120 |
| current price | 600 | 500 |
| assigned reference | CA HMMV.TOW | DTA Enhanced RAIDER |
| proposed HP, reference plus current Cameo vote | 40,603.737 | 66,136.878 |
| reference voices | 1 | 1 |

Adding CA `RBUG` to the Nod comparison, without modifying the assignment, yields a
two-reference HP projection of **58,147.699**, speed **125.109**, price **741.320**.
This does not eliminate the HP inversion. These remain unrounded, unapproved projections,
not grid-fitted or gameplay-validated proposals.

## What the references actually represent

- DTA Enhanced `RAIDER` is a Nod Heavy Raider: HP 4,800, speed 9, cost 800,
  TechLevel 7, prerequisites `AFLD,BIOE`. Its base `BGGY` has HP 1,200, speed 11,
  cost 300. This is a fourfold HP upgrade with lower speed, not merely an extra gun.
- DTA `JEEPPTNK` is a Rocket Hum-vee record, but is marked `TechLevel=-1` and
  `buildable=false`. Its existence does not establish an ordinary player-buildable
  GDI counterpart. No automatic inclusion is justified from the stored row.
- CA `RBUG` exists in the committed peer corpus and is not assigned to another
  Cameo actor. Current CA source confirms that it inherits `BGGY`, gains Heavy armor,
  uses `RaiderBuggyLaser` and is gated by the Raider upgrade/Zeal Covenant.
- CA `HMMV.TOW` inherits the ordinary Hum-Vee's Light armor and machine gun, and adds
  a secondary TOW missile with a one-round ammunition pool and separate reload.
  Both CA upgraded vehicles have speed 126; HP is 13,250 for RBUG and 15,000 for HMMV.TOW.

The CA definitions were resolved through `miniyaml.Ruleset` using their active manifest
at [revision ab9e477c3db818e91946d4cfdc86e71012966141](https://github.com/Inq8/CAmod/blob/ab9e477c3db818e91946d4cfdc86e71012966141/mods/ca/rules/vehicles.yaml).
The stored CA corpus does not record its original checkout revision, so this source
check establishes current role mechanics, not exact provenance for every archived field.

## Recommendations

1. Treat RBUG as a candidate upgraded-raider analogue, not a direct identity match.
   Retain the DTA Heavy Raider evidence and its distinct armor/tier/upgrade context.
2. Compare faction identity across explicitly comparable role/tier pairs. Use the
   proposed GDI-heavier/Nod-faster relationship as a visible review condition for this
   pair, not a claim that every GDI unit must out-health every Nod unit.
3. Keep source-relative targets separate from Cameo-fitted proposals. Any adjustment
   to preserve intended faction identity must explain its reason and magnitude.
4. Do not fill a missing reference slot with an unrelated unit just to reach a count.
   Source disagreement and non-buildable alternatives stay visible.
5. Review armor and weapon operation before interpreting raw HP or DPS as power.
   CA's stored HMMV.TOW summary carries one weapon statistic set; its source has gun
   plus missile. A one-weapon summary does not establish complete unit damage.

The wider lesson is not that the geometric mean is unusable: it is that the quality
and comparability of its inputs are design decisions the mean cannot repair.
