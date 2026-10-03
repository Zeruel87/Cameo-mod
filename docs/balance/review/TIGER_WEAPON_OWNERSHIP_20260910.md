# Tiger and Cybertank weapon ownership

Two shared cannon IDs become four independent owner-prefixed definitions for
Allied Tiger Heavy Tank and Cybertank. Only four Armament weapon values change.
Normal and mutually exclusive Cryo upgrade operation are preserved, including
damage 16,000, reload 60, range 5,915, projectile speed 591 and both diagnostic classes 1.25.

Before source: PR340 `b45546fe165af74a21dec55685ed0cf8cdb47179`.
The full 2,907→2,910 source weapon comparison preserves all retained payloads and
each renamed concrete payload. Only one new abstract effect helper is added.
It factors the existing impact-effect override, avoiding duplicated local-effect
debt. Both complete actor payloads match after reversing exactly four identities.
Ordered payload hashes also match, including warhead execution order.

Five focused regressions cover these contracts, all active executable references,
other resolved owners, all bundled map YAML/Lua and exact diagnostic class values.
All ledger values match the baseline after normalizing weapon names and direct
ancestry labels; only Allied and shared-Red-Alert primary/derived files differ.
No costs, actor stats, firing behavior, class policy or reference assignments change.

Independent review found no blocker and requested the explicit numerical class
guard, which is included. Historical consolidation/retired boundary fixtures remain
unchanged: this is identity isolation, not a new role/profile decision.
Final combined R8: 1,907 tests, 12 failures, 8 errors, 64 skips, exact R7
failure/error signatures. Peak system RAM 85.88%, no guard stop; not all-green.
The 90-second menu smoke check started 08:49:30 and passed with fresh menu-load
evidence, no new exceptions and peak RAM 70.59%. This covers final Yak and Tiger
identity changes on the verified PR341 binary, without rebuilding. It is startup/
menu evidence, not matchup or numerical balance validation.

Raw stacked weapons remain 231, reachable 169 and reachable excess 334. Concrete
weapons and main instances each rise by two. The shape audit W6 falls694→693;
all other shape buckets and informational missing-template counts are unchanged.
The roster-uniqueness audit remains 37/37/95: its filtering does not make this
owner isolation a numerical improvement in that report. Release D4 rises 347→348
against unchanged 335; D1/D2/D3 are unchanged. No ratchet or exception changed.
Canonical audits retain the same eight existing failure categories: inherits,
basebuilder_crates, buildable_order, packs, split_definitions, release_drift,
doc_claims and doc_health. Final source and integration checks each report
33 ledgers with zero drift. Diff checks pass. This remains a draft follow-up,
not a merge or a claim that the entire roster migration is complete.
