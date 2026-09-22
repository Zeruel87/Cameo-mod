# Fourteen Allied weapon identities

Seven normal/Cryo pairs receive their existing global-roster owner's prefix:
Ranger machineguns, AA-gun flak, Blackhawk chainguns, Medium Tank cannons,
Tanya pistols, Gunboat cannons and Destroyer missiles. These are renames, not
copied weapons or changes to combat profiles.

Source baseline: `d598557f93f6e9585d40789778153c00113040a5`.
All 2,910 source weapon payloads compare exactly after reversing the fourteen
identities; no definition is added or removed beyond those replacements.
The seven complete actor payloads match after reversing eighteen Armament values
and one Medium Tank WithMuzzleSmoke/Weapons value. Normal/Cryo conditions,
garrison/secondary slots, projectile fields, damage and ordered warheads are intact.

These weapons have one owner each in the global roster, with one preserved
map-local borrower: Survival's C5 Armament references Tanya's pistol. Only that
one reference in rules.yaml changes. The archive regression pins every member's
data hash after that exact reverse substitution, plus member order, timestamps,
compression type, flags, attributes, comments and extra fields. All 363 bundled
archives and loose map YAML/Lua have no old-name tokens afterward.

Six new regressions cover these contracts and all original diagnostic class values.
The existing Colt45 projectile-speed test keys are renamed with their values
unchanged. No extractor, template body, price, actor stat or reference assignment
changes. No claim is made that a generic node scanner parses arbitrary script
expressions; the separate bundled-map token scan covers the identified map risk.
Independent review found no blocker in scope, implementation or these test boundaries.

Final combined R9: 1,913 tests, 12 failures, 8 errors, 64 skips; exact R8
failure/error signatures. Peak system RAM 86.41%, no guard stop. Six new tests
and four existing projectile-speed tests pass. The suite is not all-green.
All primary/derived ledger fields compare unchanged after weapon-name reversal.
All structural inventory counts and shape buckets remain unchanged. Release D4
rises 348→355 against unchanged 335; D1/D2/D3 remain fixed. No ratchet is relaxed.
Source and integration checks each report 33 ledgers with zero drift. Targeted
percentage-runtime, K-linearity, suffix, shape, split and balance-drift audits pass.
Canonical audits retain the eight baseline failure categories: inherits,
basebuilder_crates, buildable_order, packs, split_definitions, release_drift,
doc_claims and doc_health. Diff checks pass. The checked C# and Lua sources have
no remaining old-name tokens. No threshold or historical fixture is rewritten.
No additional game run is claimed for this identity-only batch.
