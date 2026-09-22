# Guarded owner identities: Longbow, Sheridan chaingun and Grenadier

Baseline: `17022b1d5b73841df40daa5f6a2ef8c0d5170ce8`. Five weapon headers
and six Armament values change; no weapon body, damage, cadence, geometry,
targeting, price or actor-stat change. All 2,910 source and 2,911 combined
resolved weapon payloads compare exactly after reversing only these identities.

- Hellfire/Cryo become Longbow missile/Cryo.
- SheridanVulcan/Cryo become Sheridan chaingun/Cryo.
- GrenadeRA becomes Soviet Grenadier grenade. Thermobaric upgrade slots remain
  unchanged; GrenadeRAExplode is a separate weapon and is not renamed.

Three current converter selections follow the new IDs. Historical comparison
JSONs, their original hashes and the reviewed source-change guard stay intact.
The GrenadeRA historical test restores only the root identity in a deep copy
before the original 102-to-101 COMPOSITE adapter; a negative test rejects103.
The original source node is never changed by this historical reconstruction.

Complete actor snapshots from earlier cohorts remain frozen. Exact slot-specific
Sheridan and Grenadier identity adapters reconcile the later names without
allowing arbitrary armament or upgrade changes. Seven new tests pin full ordered
weapons, classes, all three actors, six references, map references, historical
JSON bytes and the unrelated OrderName `Hellfire Dreadnought Deep Strike`.
AI YAML and that support-power order are untouched.

All 46 focused tests pass; independent actual-diff review found no blocker.
All 33 ledgers have zero drift; every primary/derived field is unchanged after
reversing the five identities. Canonical audits retain eight existing gated
failure categories. Structural counts stay fixed; release D4 rises363 to367
against unchanged335, while D1/D2/D3 are unchanged. Tracked-file advisory scans
were refreshed after staging the new files and retain their existing findings.

Monolithic R12 was stopped at90.04% by the then-current90% memory guard near
the last Yak tests. It is incomplete and is not accepted as a full run.
R13 ran all144 modules in isolated subprocess groups:1,929 tests,12 failures,
8 errors,64 skips, exact R11 baseline failure signatures, peak53.75%, no guard
stop. This is isolated full-discovery validation, not proof of monolithic
cross-module state equivalence.

The original runner's final count check mistook three methods inside the
explicitly skipped OptionalBeforeCorpusTest class for missing executions.
That pre-existing class skip is present in R11 too. Independent identity
verification accounts for all1,932 discovered IDs:1,929 reported tests plus
those three class-skipped methods; no missing or extra IDs. The historical
R13 log and its bookkeeping assertion are retained. The external helper now
handles explicit class skips and reads terminal group summaries.

Blackrobe subsequently set future test/game memory stop guards to95%.
No new in-game test or complete whole-roster migration is claimed.
