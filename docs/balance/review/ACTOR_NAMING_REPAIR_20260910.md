# Soviet, dog and TD naval naming repair

## Scope and player impact

This is the bounded naming migration requested by Aedis on 10 September at
03:03–03:22 Jakarta, based on upstream `50b7d001`. It is not a whole-roster
rename, a balance pass, or skirmish-AI development.

- Restore 31 Soviet roots plus the Mammoth color-picker variant, and rename
  the two RA2 dogs: 34 identities. The three dogs end in `_dog`.
- Rename eight TD naval actors to the `td_gdi_` / `td_nod_` scheme.
- Split concrete `DogJaw` into abstract `^DogJaw` and three actor-owned `_bite`
  weapons. All resolved payloads remain identical; no arbitrary stat differences.
- Update actor references, conditions, prerequisites, translations, map placements
  and scripts, AI lists, current tooling and generated ledgers. Dormant files with
  references are updated too; this is not claimed to be active-files-only.

No cost, HP, speed, damage, reload or weapon-range rebalance is intended. Actor IDs
are a compatibility boundary: external maps and old replays naming the old IDs
may require migration. This PR does not promise backward-compatible aliases.

## Root cause and asset preservation

The earlier tooltip-derived generator combined the faction `soviets` with the
adjective `Soviet`, duplicating it in actor IDs. The generator already strips that
adjective; this repairs the remaining definitions and references. The old
`actor_dog.name` Fluent key is valid in the active localization file, not missing.
The three dog `GenericName` literals are corrected to `Attack Dog`.

Actor IDs and sprite namespaces are distinct. Existing sequence and asset names
are preserved, including explicit old-ID `RenderSprites.Image` bindings and the
miner's `ImageByFullness`. No sprite files or sequence keys are renamed.

## Evidence

- Required captured resolved fixtures verify all 42 renamed identities. Asset
  fields are not normalized as actor IDs; unknown scalar fields stay unchanged.
  Collision checks and negative image-substitution tests guard false equivalence.
- 33 focused naming, dog-ownership and shellmap-reference tests passed.
- Complete weapon comparison: 2896 before / 2899 after; only `DogJaw` removed,
  abstract base plus three bites added, every other resolved weapon unchanged.
  All four new definitions resolve exactly to the original `DogJaw` payload.
- Seven edited map archives retain member order, metadata and unrelated bytes;
  coordinated Soviet/naval substitutions are combined in the shared lake map.
- All 33 ledgers and derived sidecars regenerated; recheck reports zero drift.
  The first full run exposed three stale-ledger failures; regeneration cleared
  all three without weakening their assertions. Remaining baseline failures are
  reported separately in the final validation checkpoint.
- 90-second menu boot passed at 04:45 Jakarta with no new exception logs and
  fresh `MenuPostProcessEffect.PostWorldLoaded` evidence. Peak sampled system RAM
  81.64%; owned game process closed. Existing engine build used read-only through
  the worktree junction; no build or engine mutation performed here.

Boot proof does not replace map-reference validation or prove every map playable.
Independent review challenged typed references, asset preservation, collision
handling and regression coverage; identified issues were corrected.

## Remaining work

Final full Python run: 1337 tests, 14 failures, 8 errors, 45 skips. All 22
failure/error signatures match the earlier upstream/core baseline; peak sampled
system RAM 80.94%, safety guard not triggered. This is not an all-green suite.

The release-drift audit intentionally remains red at D4: 336 unmatched old names
versus the lower-only ratchet of 335. The additional name is `DogJaw`, whose three
replacement payloads were compared exactly above. The raw count and ratchet are
not concealed or raised. A future rename-aware release comparison should retain
both provenance and raw unmatched counts; this draft does not claim that gate
passes merely because the rename is intentional.

Canonical `run_all.sh` completed with eight failing categories: inherits,
basebuilder_crates, buildable_order, packs, split_definitions, release_drift,
doc_claims and doc_health. The release-drift addition is explained above;
upgrade and nuclear-flash reference gates now pass. Map audit: 363 maps,
184162 placements, zero dangling actors and zero unreadable archives. Percentage
runtime, K-linearity, generator sync, weapon_shape, three_way_split and naming
ratchets pass. `split_definitions` remains a separate failing gate.

Whole-roster actor/weapon ownership migration and broader W24 changes remain
separate. Naval IDs now carry canonical faction prefixes; downstream reference
routing and CA/DTA naval assignments remain to be validated. Generated
diagnostics are evidence, not approval to apply balance targets.

Implementation: OpenCode GLM 5.3 Flash. Planning, review corrections and
independent review: Codex. Draft publication authorized by Blackrobe; no merge.
