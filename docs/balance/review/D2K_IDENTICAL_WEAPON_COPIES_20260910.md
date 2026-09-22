# Dune identical weapon-definition cleanup

Removed only the redundant `OrniBombC` and `OrniGunC` blocks from the active Ordos
weapon file. Their identical definitions remain in Atreides beside their parents.
The manifest loads Ordos before Atreides. No weapon ID, actor reference, projectile,
damage, firing timing, target eligibility, effect or asset was removed or changed.

All 2,897 resolved weapons compare exactly with the pre-edit snapshot from
`0dba5542ff8068179066321ab1aa633a1a4cf82b`. Three new tests cover sole active
definition location, full resolved payload hashes, and explicit range/target/damage
fields. The retained OrniBombC range is2500; OrniGunC range6000, minimum1200, damage800.

Independent review supports this scoped cleanup. Split-definition S2 drops4→2;
S1 stays22. The existing thresholds56/2 are not raised. Flamethrower and ZClaw3 are
not identical duplicates and remain visible, untouched. This clears the S2 overrun,
not all duplicate-definition debt or W24 migration.

Final combined suite: 1,895 tests, 13 failures, 8 errors, 64 skips, exact preceding
integration signatures. Peak memory 80.97%, no guard stop. All 2,900 combined
resolved weapons are unchanged. Three focused tests pass; 33 ledgers have zero drift.
The separate PR341 canonical run retains eight failing categories, with no empty
reports. Its split-definition gate now passes. This is not a green full suite.

The removed text is recoverable in Git; the runtime weapons themselves still exist.
