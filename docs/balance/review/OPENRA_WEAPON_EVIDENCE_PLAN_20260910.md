# OpenRA peer weapon evidence — repair plan and source review

The findings below began as a read-only plan. Bounded P0 implementation now retains
resolved armament evidence and withholds unsupported numeric summaries; ordinary and
hero Doc5 consumers now honor emitted evidence columns. Legacy corpus rows remain
unassessed for unmigrated sources. Full factory-ready/max-upgrade state evaluation remains
pending. The CA structured transport is published in draft PR339; the bounded
initial-state metadata follow-up below has completed source and combined validation.
Source checkouts were read only; no source game ran.

The subsequent [base-OpenRA migration](BASE_OPENRA_STRUCTURED_EVIDENCE_20260910.md)
also selects the four existing TD/RA/TS/D2k slices. References below to CA-only
selection and earlier population counts describe the earlier checkpoints, not the
current index. State certification remains pending for every selected source.

### CA structured consumer migration (P3, published draft)

`docs/reference/peer_corpus/index.json` explicitly selects the pinned CA JSONL payload.
That source replaces, rather than supplements, the CA Doc5 slice in ordinary/hero
distribution, chassis synthesis and peer cost-grid readers. Other sources remain on
Doc5. Unlisted files are inert; malformed selected evidence raises an error without
falling back to stale Markdown. Pilot/anchor fingerprints include the index, selected
payload and loader. JSONL bytes are preserved by Git because the index hashes them.

The payload contains 377 source rows, retaining nested evidence: 288 armed rows remain
incomplete and have no certified DPS; 89 rows have no weapon evidence. Population filters
yield 341 ordinary and 25 hero-lane CA rows, with the remaining 11 excluded by existing
AI-only filters. This is an evidence-input change, not a live unit-stat or price change.
No factory-ready or maximum-upgrade state has been certified by this transport work.
The old CA table remains historical/display material; do not use its first-slot DPS
as a certified unit-level value. Other source migrations require explicit review.

Validation: 1,706 tests ran, with 14 failures, 8 errors and 64 skips; failure signatures
match the recorded baseline, with no new failures. The raw ordinary evidence inventory
is now 310 incomplete, 46 nominal-direct and 4,023 legacy-unassessed rows (4,379 total).
CA contributes 269 incomplete ordinary rows; non-CA counts remain unchanged. Tests
assert these findings instead of hiding CA under the old legacy count. Independent
review found no remaining transport blocker. The full suite is not green and this
is not a merge or gameplay-balance recommendation.

### Production-state declaration inventory (P2 groundwork)

The structured export now retains selected production prerequisites, initial-level/experience
traits, recognized condition grants and raw `ReplacedInQueue`/`Upgradeable` declarations. Nested
fields and ordering survive. 57 of 377 CA records declare routes. Missing targets are
reported as missing definitions rather than discarded; existing targets are not labeled
reachable. HMMV declares queue replacement and an upgrade route to HMMV.TOW; inheritance
removals correctly leave neither route on HMMV.TOW itself. The two references are not
two additional simultaneous weapons or proof of a complete maximum-upgrade path.

All previous 377 rows' non-provenance fields are unchanged by this addition. Factory-ready
and maximum-upgrade certification remain `none`, including actors with no declared routes.
Condition values, player prerequisites, rank and compatible upgrade combinations still
need source-specific evaluation. No numerical source or live game stat was changed.
Differently named/custom state providers are not exhaustively inventoried by this step.

### Explicit evidence export implemented (10 September)

`extract_peer_units.py --mod ca --root <checkout> --json <external.jsonl>
--expect-commit <40-hex-HEAD>` now retains every nested weapon/armament record in
an external JSONL artifact. It does not rewrite Doc5 or feed the new file into
balance targets automatically. Exactly one source mod is required. Non-finite
JSON and conflicting output files are refused; source/output junction escapes
are checked on resolved paths.

The metadata records source HEAD/dirty state, the declared engine pin (unverified),
48 source-input hashes in the current CA export, and a documented finite local
dependency fingerprint. Source files and the engine pin are checked before/after
extraction. Local tool hashes are a snapshot, not a toolchain-stability guarantee.
Git diagnostic paths are not exported. Neither factory-ready nor maximum-upgrade
states are certified. The exact CA checkout still returns 377 units, including
288 armed rows that remain conservatively incomplete.

Independent review passed 16 export tests after correcting resolved-source
containment, engine-pin provenance and Git-error redaction. The parent reran
62 combined export, weapon-evidence, consumer and pinned DTA tests successfully.
No source executable, corpus rewrite or live unit-stat change was involved.

## Current CA source validation

At `ab9e477c3db818e91946d4cfdc86e71012966141`, active manifest extraction returns
377 rows: 288 armed and 89 unarmed. The former Doc5 headline of 382 differs by exactly
AFAC, FACT, SFAC, TRUK and TRUK.DROP: all still exist but resolve `~disabled` prerequisites
and are excluded by the current availability filter. No actor was deleted by this repair.

All 288 armed rows initially remain incomplete under the conservative evidence gate.
This is not 288 broken weapons or zero damage. Overlapping reasons include 190 multi-slot
actors, 147 conditional armaments, 42 bound ammo pools, 36 unknown bindings and 15 unresolved
burst cadences. A review also identified false warning reasons from incoming DamageMultiplier
and ordinary AttackMove; those are being corrected separately from genuine state ambiguity.

HMMV.TOW now retains M60mgTD plus TOW and its secondary-bound Ammo=1 / reload Delay=200
evidence. XO retains XOCoilGun and XOLaser. E1 retains its AI commandeer helper, M1Carbine
and M1CarbineBATF. The old E1 summary's range 1024 / reload 5 describes the first AI helper,
not its combat rifle. HP/cost/speed spot checks for HMMV, HMMV.TOW, XO and E1 match Doc5.
No declaration-order replacement is automatically certified as the factory-ready weapon.

## 1. Verified findings

### Source-specific state semantics inspected on 10 September

The CA checkout is sparse: absence of `OpenRA.Mods.CA` on disk is not absence from
the pinned Git tree. Reading that tree without changing the checkout verified
[`Upgradeable`](https://github.com/Inq8/CAmod/blob/ab9e477c3db818e91946d4cfdc86e71012966141/OpenRA.Mods.CA/Traits/Upgradeable.cs)
and [`ReloadAmmoPoolCA`](https://github.com/Inq8/CAmod/blob/ab9e477c3db818e91946d4cfdc86e71012966141/OpenRA.Mods.CA/Traits/ReloadAmmoPoolCA.cs).
The former requires an unlocked upgrade, an enabled trait and an explicit upgrade
order; its target actor is not an additional simultaneously firing unit. The latter
uses the named pool, conditional pause/disable state, reload modifiers and tick timing.
`Delay` alone therefore does not certify the actor's effective sustained DPS.

The declared engine branch `ca-engine/1.09` resolved during this inspection to
`ce20e97bbe43812ee9c7a8ad9d716d2bcaf99419`. This is a captured candidate revision,
not proof of the engine binary originally paired with CA's July source commit.
At that revision, [`AmmoPool`](https://github.com/Inq8/OpenRA/blob/ce20e97bbe43812ee9c7a8ad9d716d2bcaf99419/OpenRA.Mods.Common/Traits/AmmoPool.cs)
defaults to a full pool and grants its ammo condition on creation; therefore setting
all named conditions false would incorrectly suppress HMMV.TOW's loaded missile.
[`ProducibleWithLevel`](https://github.com/Inq8/OpenRA/blob/ce20e97bbe43812ee9c7a8ad9d716d2bcaf99419/OpenRA.Mods.Common/Traits/ProducibleWithLevel.cs)
can grant levels on creation when player prerequisites are met. Factory-created is
not automatically unranked. The requested no-purchased-upgrades/no-elite baseline
must explicitly identify player prerequisite state, not infer it from actor age.
No source executable was run and no complete state/DPS certification is claimed.

**F1 — `weapon_stats` keeps only the first Armament.** `tools/reference/extract_peer_units.py:97`
collects every `Armament@*` weapon but resolves and reports `weapons[0]` only — declaration
order, with no priority, condition, ammo or upgrade awareness. Every multi-armament Doc5 row
carries one weapon's numbers presented as the unit's damage summary.

**F2 — the concrete casualty is CA `HMMV.TOW`.** External [CA checkout](https://github.com/Inq8/CAmod)
(HEAD `ab9e477c3db818e91946d4cfdc86e71012966141`, 2026-07-30, clean tree; matches
`UPSTREAM_MODS.md` "ca-engine/1.09", `Inq8/OpenRA`), `mods/ca/rules/vehicles.yaml:3224-3345`:

* `HMMV` builds with `Prerequisites: ~vehicles.hmmv, ~!tow.upgrade` — **base purchase definition**,
  one unconditional `Armament:` (M60mgTD), cost 400, speed 144; `ReplacedInQueue: hmmv.tow`.
* `HMMV.TOW` (`Inherits: HMMV`) requires `~tow.upgrade`, cost 575, speed 126, adds
  `Armament@SECONDARY` (Weapon: TOW, `PauseOnCondition: !ammo`), `AmmoPool` (Armaments:
  secondary, Ammo: 1, `AmmoCondition: ammo`), `ReloadAmmoPoolCA` (Delay: 200), and cancels
  `-ReplacedInQueue` / `-Upgradeable@TOW` — an **upgrade-gated queue-replacement variant**,
  mutually exclusive with the base state, not an additive upgrade.
* Doc5 (`docs/design/ORIGINAL_UNITS_PEER_OPENRA.md:303-304`) shows BOTH rows with identical
  M60 numbers — F1 hiding the TOW slot and the ammo-gated cadence entirely.
  `BUGGY_HUMVEE_REFERENCE_REVIEW_20260909.md` recommendation 5 already flagged this.

**F3 — Doc5's MD tables are a lossy transport.** `reference_distribution.py` parses
the markdown into ordinary and hero rows. Other paths consume, maintain or fingerprint
the document; `propose_anchor_spec.py` and `build_japan_pilot.py` fingerprint it rather
than independently parsing all its weapon columns. History: cost and faction were each
extracted and then silently dropped on read; `vsINF` case mismatch zeroed armor columns;
`peer_rows` drops any row whose cell count differs from the header (line 609). Any metadata
that does not fit today's columns vanishes exactly this way.

**F4 — Doc5 is hash-pinned.** Anchor dossiers (`docs/balance/anchors/*.md`) pin its SHA-256
(`d37db59f…`) and `build_japan_pilot.py` fingerprints it; `BLACKROBE_ASTRA_ORDERS_2026-09-07.md`
line 1563 forbids full-file regeneration — CA-section changes go through
`splice_peer_section.py`. Changed inputs invalidate earlier evidence: regenerate and
review affected diagnostics, rather than mechanically updating a signed evidence hash.

**F5 — explicit source routing is needed.** `PEERS["ca"]["root"]` candidates
(`extract_peer_units.py:219-220`) do not include this independently acquired checkout, and the
stored corpus records no checkout revision at all.

## 2. The smallest fail-closed repair (prioritized)

**P0 — evidence-honest weapon extraction.** Extend `weapon_stats` (or emit alongside it) so
that per actor it emits ONE row PER RESOLVED ARMAMENT SLOT, using the INI extractor's
vocabulary (`extract_ini_units.py` `weapon_of`/`relabel_weapon`): `w_evidence`,
`w_evidence_reason`, `w_dps_usable`, plus slot twins `w2_*` / `wdummy_*`. The base numeric
summary (`w_dps`) is emitted ONLY when proven: exactly one resolved Armament, no
`PauseOnCondition`/`RequiresCondition` on it, no AmmoPool binding, weapon resolves through
`miniyaml.Ruleset.resolve_weapon`, all main warheads carry positive conventional `Damage`.
That state is labelled `nominal_direct` (the declared Damage/ROF contract, never "complete").
Everything else is `incomplete` with a reason; its raw direct estimate moves to `w_dps_raw`
and votes nowhere. Existing Doc5 numbers are never re-labelled as certified: absent evidence
stays `legacy-unassessed` (consumer `apply_weapon_evidence`, `reference_distribution.py:428`).

**P1 — retain cadence and gating evidence RAW, never folded silently.** Per slot, carry:
slot name, weapon id, `PauseOnCondition`, `RequiresCondition`, AmmoPool binding
(`Armaments`, `Ammo`, `AmmoCondition`), `ReloadAmmoPoolCA` delay, raw `ReloadDelay` /
`Burst` / `BurstDelays` / `Range` / `MinRange`, per-warhead `Damage`, and target-side
evidence (AutoTarget stance, warhead `Versus` presence). Ammo-pooled cadence (TOW:
ammo 1 + pool reload 200) must never be expressed as a plain ReloadDelay cycle.

**P2 — base and maximum-upgrade as SEPARATE views, never summed.**
* Base view = factory-ready, established from source-specific activation evidence.
  A token spelling such as `~<x>.upgrade` is not a general proof of upgrade state across
  mods. Preserve prerequisites and modifiers raw; unknown activation must remain unknown.
  The verified HMMV/TOW pair illustrates a source-specific case, not a universal parser rule.
  Distinguish the prerequisites needed to purchase a build variant from optional upgrades
  applied after it is produced: the TOW missile is intrinsic to HMMV.TOW's own definition.
  Its upgrade-gated availability does not, by itself, prove that it must be excluded as a
  counterpart to a separately buildable Cameo Mk II unit. That is a role/variant decision.
* Max-upgrade view = per base actor, LIST its mutually exclusive achieved states (the
  queue-replacement pair: `ReplacedInQueue` on the base, cancelled on the variant), each
  state its own row with its own evidence and gating provenance. No cross-state addition,
  no blended "upgraded DPS" — the views are separate columns of evidence, not a simulator.

**P3 — transport that cannot drop metadata.** Follow the INI family's precedent
(`docs/reference/ini_corpus.json`): the extractor writes a JSONL peer weapon corpus under
`docs/reference/` as the machine source of truth, and Doc5 becomes display-only output
regenerated per-section via `splice_peer_section.py`. Consumers migrate to the JSONL reader
(`peer_rows` shape already matches); until each migrates, keep the MD columns the consumer
reads strictly in sync and treat any header/column mismatch as an error, not a skip.
This is the reader-path fix for F3; no MD column gymnastics.

**P4 — provenance routing.** Add an explicit, recorded source identity for peer extraction,
mirroring `extract_ra3_units.py --expect-commit`: explicit `--root` (or a candidate entry)
for the CA checkout plus HEAD `ab9e477…`, dirty state and input hashes recorded in the
corpus. Keep `ENGINE_VERSION="ca-engine/1.09"` (mod.config) as part of the identity. Raw
sources stay outside the repo (R9); the checkout is never executed. Any Doc5 CA-section
rewrite invalidates earlier source-pinned diagnostics and needs explicit evidence review
(F4). A `TASK_INDEX.md` row for this task is added when implementation lands.

## Production-declaration follow-up validation

The selected raw production/upgrade declarations are retained for all 377 CA rows;
57 rows declare routes. Existing numeric fields are unchanged. Factory-ready and
maximum-upgrade certification remain `none`: this is evidence preservation, not a
completed condition evaluator. Source-specific providers outside the selected trait
inventory still require review.

37 focused tests pass. Full suite: 1,710 tests, 14 failures, 8 errors and 64 skips,
with the exact existing baseline signatures; sampled memory peak 80.26%, no guard
stop. Canonical audits retain nine failing categories: inherits, upgrades,
basebuilder_crates, buildable_order, packs, split_definitions, nuclear_flash_bindings,
doc_claims and doc_health. No empty final Markdown reports. No live YAML or C# change.

### Four-actor initial-state inventory (10 September follow-up)

The explicit CA pilot is HARV, LST, HMMV and HMMV.TOW. It records authored
top-level condition/prerequisite uses and raw modifier-bearing traits, without
evaluating them. Collection is heuristic and intentionally not exhaustive; custom
providers and world/player state may be missing. Exact source actor IDs are
asserted in the installed-corpus test so an upstream rename cannot silently
remove the selected evidence unnoticed.

| Actor | Condition-use occurrences | Prerequisite-use occurrences | Modifier-trait occurrences |
|---|---:|---:|---:|
| HARV | 184 | 22 | 88 |
| LST | 209 | 28 | 108 |
| HMMV | 230 | 29 | 112 |
| HMMV.TOW | 229 | 29 | 112 |

These are declarations, not unique conditions or confirmed factory-state
blockers. Even unarmed HARV retains damage modifiers and external dependencies.
No absent condition is assumed false, no modifiers are multiplied together, and
the queue/upgrade alternatives remain separate. Both certification flags stay
`none`, including empty inventories.

The clean pinned CA revision and all48 source input hashes are unchanged. All377
pre-existing row payloads compare exactly after excluding only the four new
review objects and updated exporter provenance. The regenerated6,802,090-byte
payload SHA-256 is
`e80f02b6ae603adfb5c3015045f94011a4af77ac4336f34bb35e153c30f1956f`.
41 focused exporter/consumer tests pass; independent review found no blocker.
Standalone isolated full suite:1,714 run,14 failures,8 errors,64 skips, exact22
prior failure/error identities; peak57.78%, no95% guard stop. Independent ID
accounting covers1,717 discovered identities, including3 methods under the
pre-existing optional-DTA class skip; none missing/extra.
Combined R17:1,957 run,12 failures,8 errors,64 skips, exact20 prior identities,
with all1,960 discovered identities accounted for. This is not an all-green suite.
Canonical source audits retain their prior failures, except documentation health
now passes after restoring one missing Contents link in LESSONS_LEARNED.md.
That index-only repair does not change the engine-update policy it links to.
Remaining8 gates:inherits,upgrades,basebuilder_crates,buildable_order,packs,
split_definitions,nuclear_flash_bindings,doc_claims. No thresholds changed.
33 ledgers have zero drift; no new game test was needed for metadata/index changes.

This completes a collection prerequisite, not P2 certification. The latter
requires a defined owner/faction, prerequisites/purchased upgrades, production
level and a verified exact source-engine revision. No live YAML/C# or numerical
reference-stat change is included.

## 3. Non-goals

No general upgrade simulator or new armor taxonomy in this bounded extractor repair;
no rebalance, assignment changes or retroactive certification of the committed corpus.
Heaviness C# work is a separate worktree/task, not part of this extractor change.

## 4. Open items for the implementing session

* Whether HMMV.TOW belongs in the base population at all once labelled (it is a distinct
  Buildable actor; routing rules R13/R15 and the population rule decide, not this note).
* `weapon_stats`' damage fold sums all warheads of the picked weapon — keep per-warhead
  rows in the corpus so that fold stays inspectable.
* Label `Combined Arms` (no parentheses — `main()` guard) must not change, or every
  de-dup/route that names the source breaks.
