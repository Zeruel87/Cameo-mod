# Eleven further owner-prefixed weapon names

Sheridan cannon/missile and Rapier bomb/AA pairs, Commissar pistol, Cyberdog bite
and Soviet SAM missile receive their existing owners' prefixes. Exactly eleven
headers and twelve Armament values change. Weapon bodies and templates do not.
AA suffixes remain at the end; Nike's existing damage/air-only test retains all
assertions and changes only its two current weapon-name lookups.

Source baseline: `243c95cd8a8694002860715ac4699f00dd3b4365`.
All 2,910 source weapon payloads compare exact after reversing the eleven names.
Five complete actor hashes and ordered weapon hashes are pinned. Five new tests
pass, together with six existing projectile-role tests. Original numerical class
values and Cyberdog's unknown class are preserved; no guessed value is supplied.
All bundled map YAML/Lua has no old-name tokens, and no map edit is required.

Independent review found no blocker in actual scope, coverage or role boundaries.
Mixed-profile holds are preserved, not resolved by naming. Historical fixtures
and converters are untouched. The generic token guard is deliberately confined
to this collision-free cohort; it must not be applied blindly to Hellfire, whose
name also identifies an unrelated support-power order.

All 33 ledgers have zero drift. Full primary and derived ledger comparisons
preserve every field after reversing only the weapon identities. Canonical audits
retain the same eight baseline failing categories; structural counts are unchanged.
Raw release D4 rises 355 to 363 against the unchanged 335 threshold; D1/D2/D3
are unchanged. Naming does not erase these raw unmatched-release findings.

The first combined run (R10) ran 1,918 tests with 13 failures, 8 errors and 64
skips, at 88.77% peak RAM without a guard stop. Its sole additional failure was
the old Soviet actor baseline still expecting SAM's exact Weapon value Nike.
The test now permits only that actor/path/before/after identity change, with
negative cases rejecting other changes. Frozen historical fixtures stay intact;
the separate full weapon-payload fixture still checks gameplay. Twelve focused
Soviet identity tests pass and independent review found no blocker.

The corrected R11 ran 1,919 tests with 12 failures, 8 errors and 64 skips:
exact R9 baseline failure signatures, not an all-green suite. Peak RAM86.56%,
no guard stop. No post-batch game run is claimed.
