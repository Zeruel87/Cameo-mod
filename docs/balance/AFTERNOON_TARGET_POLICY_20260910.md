# Target-domain and upgrade corrections — 10 September 2026

The candidate makes damage eligibility follow the intended weapon domain. Ground-only weapons must not damage airborne actors; air-only weapons must not damage ground actors. Dual-target weapons retain both domains without accidental ground-only damage contributions.

## Gameplay changes

- Future Tank main/percentage damage, EMP and shield-hit condition exclude Air. Groundfire spawned by the weapon is a decoration/lifetime actor with no damage traits.
- Asian Gun Boat flak admits Air for its full 8000 nominal flat damage and inherited percentage routes, previously split 2000 air / 8000 ground. Normal and elite share the correction.
- Asian Gun Boat uses a distinct AntiAirShip template with a 150% actor-wide range multiplier and air target priority. This increases the range of all its armaments, including cannon/depth charges. Existing Scout Ship armor/firepower/support traits are retained. Its balance anchor is still uncertified; no prices are applied.
- 119 directly bound ground/water-only leaf weapons receive 664 explicit Air exclusions across damage/status routes. No weapon descendants exist for the selected definitions. All existing exclusions and numerical fields are preserved.
- 61 directly bound Air-only leaf weapons have 177 inherited damage/percentage/integrity target filters set to Air. Existing exclusions and numerical fields are preserved. Ground-only inherited contributions now reach eligible air targets, so this can increase AA damage.
- 65 homogeneous parent families cover 134 definitions with 309 resolved target-field changes. Another 26 mixed-domain parent families cover 116 definitions with 131 resolved target-field changes; explicit descendant overrides preserve mixed-domain consumers without any resolved changes. These cohort counts overlap and must not be added as unique weapon totals.
- 227mm, RocketsRA and MammothTusk damage families change from MissileHE to MissileAP. Effects and firing operation remain. Their 12 affected definitions preserve nominal flat damage; the Air-only D2K_Annihilator_AA exception instead uses MissileAA_Heavy at 28500 damage. Family armor response and blast geometry intentionally change.
- Sonic replacement damage is 45000 for TSGrenadeSonic, 42000 for TSHellfireSonic and 41000 for TSZoneHellfireSonic. These round up the static no-regression thresholds to the next 1000. Minimum centered DPS gains over the base across the existing tested armor set are 0.9615%, 2.1622% and 1.5766%. The Sonic status remains separate; no upgrade pricing changed.

## Evidence and limits

The active-manifest target regression covers all directly bound simple single-domain weapons, plus exact Future Tank, gunboat, missile and AA child contracts. The grouped target/source-key/upgrade run passes 25 tests. Resolved before/after comparisons show target-only edits in the domain cohorts and preserved missile nominal totals, targeting and firing operation. A full 33-faction extraction was staged after the leaf corrections and all 67 raw/derived outputs reconciled; nine files changed. Later parent corrections affect target fields which the extractor does not read.

Historical conversion tests retain their original fingerprints. A test-only, exact field-delta fixture restores reviewed pre-policy target fields and rejects unrecorded changes. The corrective eight-module run passes 55 tests; the final history guard module passes six tests. This does not certify the complete suite.

The ledgers do not record most warhead target filters. Their equality is not evidence of correct target eligibility; the dedicated resolved-rule check supplies that evidence. No runtime battle validation, universal collateral proof, full-suite green result or merge readiness is claimed. Custom target categories, secondary routes and map-local overrides still need separate coverage. Status utility and upgrade pricing are separate follow-ups. Aedis's 17:16 request adds four delivery-specific Sonic combinations; the generic Sonic damage correction above predates that request and does not complete it.

## Sonic family milestone, 17:58 WIB

Delivery-specific BulletSonic, MissileSonic, CannonSonic and BlastSonic now replace generic Sonic in eight weapons. BlastSonic is Demolition x Concussion x Sonic; CryoBlast was renamed BlastCryo without numeric changes. The earlier generic-profile figures above describe the first checkpoint, now superseded by these family curves. Existing raw damage, firing fields and debuff settings are preserved; armor response and blast geometry change deliberately. See `DELIVERY_ELEMENT_COVERAGE_20260910.md` for mappings, scope and derived-model effects. Current target/source-key/upgrade checks pass 26 tests; focused generator checks pass four. Historical conversion corrections pass their scoped reruns, without rewriting original fingerprints or relaxing production converters. All 67 extracted outputs are reconciled. No runtime battle proof or full-suite green claim is made.
