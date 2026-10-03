# IFV-aware owner names and preserved Yak bombs

Baseline game configuration: `ec2631b9ba75d8ed4cb8cceb9a583bb493e8fb46`
(the local25-name checkpoint, not yet published). Five weapon headers and seven
concrete Armament references are renamed. The eighth changed reference is the
explicit `^IFVConditions/Armament@hmg/Weapon` binding.

The four owners are Machine Gunner, Allied Gun Turret, Scout Yak and Tesla Yak.
All seven concrete IFV descendants still override hmg with RA2CRM60H; complete
resolved snapshots prove them unchanged. The abstract IFV node is also pinned,
reversing only its one weapon identity. No IFV behavior is redesigned.

All five complete ordered weapon payloads, original classes, four owning actors,
seven IFVs and active/map references are tested. Tesla Yak's bomb remains in
EXACT_PRESERVE and outside canonical-role mappings. Current converter keys and
historical membership adapters migrate names only; two historical JSONs retain
their original bytes. Earlier Yak snapshots use exact bomb-slot adapters with
negative cases rather than refreshed hashes.

The duplicated map scan and concrete-consumer checks are now shared helpers.
Six synthetic tests cover valid similar names, archived YAML/Lua and loose
references, empty inputs, rejection before oversized-member decompression, foreign
consumers and stale abstract bindings. The map check remains a token scan, not a
general Lua reference parser. C1 returns to20; its existing threshold10 is unchanged.

All2,910 source and2,911 combined weapon payloads compare exact after reversing
the five names.30 focused IFV/Yak/converter tests and20 map/previous-cohort tests
pass. Independent actual-diff review found no blocker. No numerical or role change.

Isolated full-discovery R15 completed1,952 tests:12 failures,8 errors,64 skips,
the exact20 failure/error identities from R14. Peak system RAM56.71%, no guard stop.
Independent discovery accounting finds1,955 identities, including3 under the
pre-existing optional-DTA class skip, with none missing/extra. The full suite is
not green. Final R16 after the shared consumer-helper refactor completed1,953
tests with the same12 failures,8 errors and64 skips; peak52.37%, no guard stop.
All1,956 discovered identities are accounted for, including the3 class-skipped
methods; none missing/extra. All20 failure/error identities match R15 exactly.

Canonical source audits completed with the same8 gated failures: inherits,
basebuilder_crates, buildable_order, packs, split_definitions, release_drift,
doc_claims and doc_health. Targeted helper advisory reports were then refreshed.
All33 ledgers match live rules. Percentage-runtime reports0 dispatch findings.
No audit threshold or historical fixture was relaxed.

The combined339/340/341 configuration passed one90-second menu boot started
2026-09-10 11:20:06 Jakarta: fresh menu-load proof, no new exception logs, peak
system RAM65.36%, process closed. The existing verified DLL was not rebuilt.
This covers final30 naming changes, not combat matchups or whole-roster balance.

## Release comparison continuity (flat damage only)

Raw D4 rises388 to392 against unchanged335. Raw D1 falls117 to116 and D3 falls19
to18 only because RAVulcan moved to an unmatched name. Its existing4x flat-damage
outlier is NOT fixed. These are explicit reviewed identities, not inferred aliases:

| Previous identity | Current identity | Release flat | Current flat |
|---|---|---:|---:|
| RAVulcan | ra1_allies_machinegunner_machinegun | 4000 | 16000 |
| RAVulcanCryo | ra1_allies_machinegunner_machinegun_cryo | unavailable | 16000 |
| RATurretGun | ra1_allies_alliedgunturret_cannon | 20000 | 20000 |
| YakNapalm | ra1_soviets_yakscoutplane_napalm_bomb | 40000 | 40000 |
| YakTeslaBomb | ra1_soviets_teslayak_tesla_bomb | 160000 | 160000 |

Measured with the existing release audit's snapshot metric against
playtest-20260709. No missing source is zero-filled, no accepted-value status is
transferred, and no raw audit count is altered. A general identity-continuity
appendix remains a separate validation improvement, not a publication dependency.
PR340 remains draft; no merge or master push is authorized.
