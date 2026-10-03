# Yak combat-weapon ownership split

Identity/ownership cleanup, not balance tuning. Four shared weapon definitions become
ten independent owner-prefixed definitions for Yak Scout Plane, Tesla Yak, Nuclear
Yak, Su-57 Attack Bomber and Armored Yak. All twenty resolved Armament references
are updated, including paired guns and condition-gated incendiary replacements.
The armored definitions directly retain their cadence/range overrides rather than
inheriting another actor's weapon. All generic family/projectile/effect bases remain.

Before snapshot: PR340 `905e9befc698f522f6268d6aa7e6a2c4ef9d1d58`.
All 2,907 post-split resolved weapons compared with 2,899 before: four old IDs removed,
ten new owned IDs and two abstract helpers added; every unchanged ID has identical payload, and every new concrete definition
exactly matches its old weapon. Destination IDs were absent before the split. All
five complete actor payloads match after reversing only the twenty Weapon values.
No costs, HP, stats, damage, spread, percentage/state bindings or firing operation changed.

Regression tests cover active non-Armament reference scanning and
rejecting other actors borrowing the new IDs. All 363 bundled map archives plus
loose YAML/Lua files contain zero old weapon tokens. No map or asset edit was needed.
Independent review found no blocker in the scope or actual change.

The named-family converter now recognizes five independent incendiary roots, reusing
the original guarded hashes. Its current member count is 27 instead of 24; historical
comparison files/hashes remain unchanged. Historical set comparisons normalize only
this explicit identity split. The existing unrelated HindMissilesThermobaric historical
hash failure remains visible, not repaired or excused by this work.

## Inventory attribution

The committed structure inventory was stale before this batch. Regeneration reports
231 raw stacked weapons: 122 direct, 47 indirect, 62 unreached; 169 reachable and
334 reachable excess mains. A source reconstruction at the pre-split commit yields
exactly those same stack/excess counts. This batch changes only concrete definitions
and main-instance counts by +6, reflecting ownership duplication. It did not remove
any stacked damage. Reviewed exception partitions stay zero; raw counts remain visible.

Shared PDLaserBike is deliberately untouched: both consumers use it in point-defense
support slots, which the approved policy allows to remain shared. It is not silently
removed from existing raw weapon-uniqueness counts. The ordinary roster summary also
omitted Tesla Yak/Su-57 from its Yak rows through its carrier-style classification;
the full resolved-owner scan, not that summary, established this migration's scope.

All seven focused tests pass, including independent coverage of each new converter
hash guard. Raw same-faction sharing findings fall 39→37; cross-faction 37 and
carrier-only 95 are unchanged. Release D4 rises 343→347 for the four replaced IDs;
its threshold remains 335 and the gate remains failing. D1/D2/D3 are unchanged.

Derived Soviet ledger values are identical after reversing weapon IDs. The primary
ledger additionally changes the armored pair's source-ancestry labels from the old
concrete parents to their directly inherited generic templates; numeric values do
not change. These provenance changes are kept rather than falsifying the old ancestry.

Two abstract helpers factor the incendiary compatibility warhead and projectile
composition. Each of the ten concrete guns now has three direct parents. Complete
resolved payload comparisons and ordered converter guards verify that cancellation
and override order preserve behavior. Weapon-shape W1 falls 574 to 573 and W2 falls
205 to 200 against the pre-batch source, with unchanged ratchets. The intermediate
unfactored split raised W1 to 578 and failed; that version was not published.

The wrapper uses the existing `^Compatibility_*` convention, not a new warhead
class. Naming it `^Warhead_*` incorrectly added a third diagnostic class vote;
prepublication ledger review caught that. No extractor or class-policy change is
included. The original0.875 class is regression-tested. Both ledgers match before
after normalizing only weapon identities and direct ancestry labels.
The informational missing-direct-`^Warhead_*` count increases by five; this remains
visible and is not a claim that these compatibility weapons are fully canonical.

Combined R6 validation before the compatibility-prefix correction: 1,901 tests,
12 failures, 8 errors, 64 skips. The exact
failure/error signatures match intermediate R5; versus prior R4, the stale inventory
failure is resolved and none is added. Peak system RAM84.05%; no guard stop.
All 2,900 original combined weapon payloads are preserved under the same identity
mapping (2,908 final entries, including the two helpers). All 33 ledgers have zero drift.
The final compatibility-prefix R7 rerun completed: 1,902 tests, 12 failures,
8 errors, 64 skips, exact R6 signatures. Peak RAM83.72%, no guard stop.
Seven focused ownership/class regressions pass. Independent review cleared the
final correction and verified the extractor has no substantive diff.
The suite is not all-green.

The combined 90-second menu boot at07:45 passed with fresh menu-load evidence,
no new exception logs and peak RAM67.79%. This boot preceded the final exactly
payload-preserving template factoring; no post-factoring game run is claimed.

Canonical PR340 audits retain eight existing failing categories: inherits,
basebuilder_crates, buildable_order, packs, split_definitions, release_drift,
doc_claims and doc_health. Raw release D4 remains347 against335. This batch does
not merge any PR or complete the whole-roster migration.

Later integration evidence: the08:49:30 menu boot recorded in
[the Tiger follow-up](TIGER_WEAPON_OWNERSHIP_20260910.md) also covers the final
Yak compatibility composition and passed for90 seconds with no new exceptions.
