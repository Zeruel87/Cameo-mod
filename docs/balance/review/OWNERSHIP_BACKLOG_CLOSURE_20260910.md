# RA1 / Tiberian Dawn combat-weapon ownership closure

## Reopened technical follow-up result

The combined affected run covered55 modules/612 tests:4 failures,5 errors,
zero skips,57.68% peak RAM. Six failure/error signatures came from three exact
ownership intersections in historical test helpers. After those fixes, all25
tests in the four affected modules pass. The three genuine Sonic paid-upgrade
damage failures remain; no synthetic green full-suite result is claimed.

All17 stale historical/readiness/exclusion failure identities are addressed.
Combined33 ledgers have zero drift, all22 registry claims match the completed
measurements after prose co-update, and doc-health passes. Raw missile/release
gates remain unchanged and failing. Independent scoped review found no remaining
implementation issue. This technical follow-up changes no live YAML or prices.
Earlier full-suite receipts below remain historical. Keep drafts; HOLD merges.

## Final integration receipt — 10 September 2026

This receipt supersedes source-stage pending notes below; the source-specific
measurements remain separate from this combined result. The full combined run
executed2,033 tests:20 failures,8 errors,64 skips. All2,036 discovered identities
were accounted for, including3 class-skipped methods. The20 prior R18 failure/error
identities remained. Eight new historical-test compatibility failures were then
corrected, and all25 affected tests passed. The original full result remains red;
no second full run or synthetic green result is claimed.

The combined candidate has2,969 resolved weapons and33 zero-drift ledgers.
Independent final review passed86 focused tests and approved scoped draft
publication, with HOLD for merges. Peak full-suite RAM57.40%; no95% guard stop.
The new raw missile-role gate (R3=52/47,R4=55/50) and worsened release-name coverage
(D4=562/335) remain explicit. Five previous documentation claim mismatches remain
after the two new factual counters were co-updated; combined doc_health passes.
Source/state/role decisions listed below are not declared complete by publication.

Baseline: `6278225df00c0aa0356961036c44670847321027` (draft PR340).
Scope: the already assigned RA1 Allies/Soviets and TD GDI/Nod actors. This is
an identity migration, not another damage/profile rebalance, and not a claim
that every Cameo faction or the W24 gameplay backlog is complete.

## Completed implementation

- 194 existing weapon identities are renamed with their canonical owner prefix:
  50 closed direct definitions, 29 current-test lookup definitions, 24
  converter-facing definitions, and 91 complete inheritance/death/fragment links.
- 57 owner identities for shared combat weapons are transparent one-parent
  definitions. The original shared roots remain available to every unmodified
  outside/unreached consumer and to maps that override those roots.
- The refreshed scoped Armament scan has no remaining unowned combat identity,
  apart from the Allied Tank Destroyer pair owned by the separate PR341 work.
  The Mammoth color-picker deliberately inherits its canonical parent's five
  weapons; it does not need five extra display-only copies.
- Support/targeting, healing/repair, point-defense and superweapon helpers are
  deliberately not part of this combat identity pass. No AI, prices, actor
  health, weapon numbers, projectile parameters or engine files are edited.

All 2,910 pre-wrapper weapon payloads and all 4,132 actors compared exactly
after reversal of the 194 named identities. The additional 57 definitions bring
the resolved source weapon inventory to 2,967. Each wrapper's complete ordered
resolved payload and diagnostic weapon class/source match its retained parent.

## Consumer and engine checks

Ownership was checked through every resolved concrete actor trait, then through
weapon inheritance and nested weapon references, not just Armament declarations.
That caught two misleading single-Armament cases: `ArtilleryShell` has additional
MLRS, submarine, Naxis and CABAL death consumers; `ParaBombNuke` also serves the
Monster Tank's death explosion. Their attempted global names were reverted;
owner wrappers preserve those shared roots instead.

The actual Armament implementation obtains reload/firepower modifiers using the
unchanged `ArmamentInfo.Name`. Each armament's name, conditions, timing, ammo
and operation are preserved. `WithMuzzleSmoke` compares explicit weapon names,
so its three affected lists were migrated. The MAD Tank's `DetonationWeapon`
reference is also migrated without altering its payload.

The `E3` map-import compatibility alias inherits the GDI rocket soldier. Four
local Weapon overrides keep the alias on its original shared `Rockets` and
`RocketsAMT` definitions. Its complete resolved payload is pinned unchanged.
All other outside actors are checked without identity normalization. Bundled
maps retain the shared roots, while the 194 removed identities have no remaining
map references.

## Historical evidence remains historical

Current selectors/tests follow the new identities. Existing historical JSON
reports and their accepted-value fingerprints are not rewritten. Exact test-only
identity adapters compare current names against those frozen records. Original
converter hashes remain intact; a retained baseline failure is not called green.
External `aggregate_archetype.py` source selectors, synthetic parser fixtures,
the archived EMP rename script, and historical prose retain their own names.

Two frozen converter closure checks encounter the new `APCGun` and
`IncendiaryChainGun` wrappers. `owned_weapon_wrappers.py` recognizes only the
57 declared identities with exactly one unchanged `Inherits` child. A changed
parent, scalar override, nested override, root value or unlisted wrapper is not
recognized. Negative tests pin that fail-closed boundary. This helper is used
only by those frozen converter closure checks, never to reduce raw structure,
sharing, duplication or balance-audit counts.

## Validation and raw accounting

Source continuation regenerated all 33 raw ledgers and derived sidecars; the
subsequent full `extract_stats.py --check` passed with zero drift. Five pairs
changed: RA1 Allies/Soviets/Shared and TD GDI/Nod. An exact JSON comparison
against source HEAD reversed all 251 identities and found no numeric or derived
changes. The remaining 123 differences are provenance metadata: 42 `defined_in`
paths and 81 `versus_templates` lists/entries exposing the retained wrapper parent.

Fresh focused validation passed all 18 tests in the five new identity modules.
These check ordered payloads, complete actors, ownership, maps, classes and the
fail-closed wrapper boundary. A fresh four-module adapter rerun also passed
all 36 Allied/guarded/TD naval/Yak tests (peak RAM 55.65%); its complete evidence
is `ownership-continuation-adapters.log`. Source affected audits also passed: weapon
uniqueness, weapon shape, weapon suffixes, family uniqueness, percentage runtime,
effect/audio (24 source mappings and 15 concrete chains), and structure inventory
regeneration. Only these affected canonical reports were regenerated here.

The source structure inventory has 2,434 concrete weapons (57 more than its
previous report), 232 raw stacked weapons (previously 231), and 169 reachable
stacked weapons / 334 reachable excess mains (both unchanged). The additional
raw stack is retained wrapper debt; no exemption or threshold was changed.

External fresh evidence lives under the handoff evidence root's `validation/`:
`ownership-continuation-source.log`, `ownership-continuation-ledger-compare.log`,
and `ownership-continuation-audits-r2.log`. Peak total-system RAM was 51.54% for
ledger/tests and 49.49% for audits. The first audit logger hit a Windows console
encoding error; the UTF-8 rerun completed all seven commands successfully.

The earlier broad source sweep and its known failures remain historical evidence;
these focused passes do not certify a green full suite. The single final combined
suite/audit run is owned by the integration coordinator. No game was launched
for these identity-only changes, and no commits or pushes were made by this
continuation subtask.

The 57 extra concrete definitions remain visible in every raw count, including
any inherited stacked profiles and duplicate/shape debt. Thresholds and accepted
statuses are unchanged. Their ledger `versus_templates` metadata intentionally
names the retained shared parent, rather than copying its direct template list;
numeric and derived values must be compared independently of that disclosed
ancestry metadata. The final generated audits, not the pre-pass counts, are the
authoritative combined inventory.

Fixtures: `closed_remaining_names_20260910.json`,
`test_lookup_owned_names_20260910.json`, `converter_owned_names_20260910.json`,
`chained_owned_names_20260910.json`, and `shared_owner_wrappers_20260910.json`
under `tools/tests/fixtures/`. They enumerate every exact identity, original
payload/ordered hash, owner and relevant consumer contract.

## Remaining boundary

There is no next actionable combat-name batch inside these four assigned
factions. The separate PR341 gameplay/profile work, reference-source/role
decisions, and other factions are not marked completed by this report. Shared
roots and unknown/unreached descendants are retained intentionally; their
continued existence is not hidden from raw audit counts.

## Source release-drift gate after identity closure

The affected source-only `audit_release_drift.py` was regenerated after the
continuation checks. It exits **1**, with D4 still failing and materially worse:
562 unmatched release names against the unchanged 335 ratchet. This is a real
loss of same-name release-audit coverage, not a green gate or a damage repair.

| Gate | HEAD report | Current source | Change | Ratchet | Result |
|---|---:|---:|---:|---:|---|
| D1 inflated | 115 | 103 | -12 | 133 | PASS |
| D2 weakened | 59 | 54 | -5 | 62 | PASS |
| D3 extreme | 17 | 13 | -4 | 27 | PASS |
| D4 unmatched | 406 | 562 | +156 | 335 | FAIL |
| D5 accepted, informational | 34 | 33 | -1 | 43 | PASS |

Shared release-name coverage falls from 1,506 to 1,350 of the 1,912 release
weapons; reported unchanged names fall from 1,332 to 1,193. The decreases in
D1-D3/D5 do not establish improvements: removed identities disappear from those
same-name comparisons. In particular, the four renamed Kamov/Yak Tesla arc
fragments leave the displayed D3 list; their previously reported 3x/5x shipped
flat-damage debt is preserved by the exact payload fixtures, not repaired here.
No accepted-value fingerprint, numerical payload, release matching policy or
ratchet was changed. The earlier whole-payload and ledger comparisons establish
identity preservation separately; they do not restore this gate's lost coverage.

Evidence: `validation/ownership-continuation-release-drift.log` under the handoff
evidence root (child audit exit 1; peak total-system RAM 46.12%). This report
supersedes any inference that the seven earlier passing affected checks included
the release-drift gate. Final combined findings remain separately measured.

## New source missile-role gate failure

The source-only `audit_missile_role_family.py` exits **1**. This is a **new failing
gate introduced by the added concrete owner identities**, not baseline-only:
R1 stays 51/51 and R2 stays 33/33, but R3 rises 47 to 52 against ratchet 47,
and R4 rises 50 to 55 against ratchet 50. Missile-main concrete inventory rises
352 to 367; role-matching entries rise 184 to 191.

Exactly five added owner wrappers each add one R3 and one R4 finding:

| Added concrete identity | Retained parent |
|---|---|
| `ra1_allies_alliedrocketsoldier_rocketsra` | `RocketsRA` |
| `ra1_soviets_rocketsoldier_rocketsra` | `RocketsRA` |
| `ra1_soviets_mammothtank_mammothtusk` | `MammothTusk` |
| `ra1_soviets_missilesubmarine_227mm` | `227mm` |
| `td_gdi_mlrs_227mm` | `227mm` |

Every row resolves to its parent's exact payload and exact child execution order:
both ground/air targeting with a MissileHE main. The pre-existing whole-payload
fixtures and fresh wrapper comparison preserve the original mismatch. Therefore
the additional findings are raw cardinality growth from existing mismatches,
not five newly altered gameplay profiles. They remain real, visible gate debt.

There is no safe representation-only repair within this identity contract.
`MAMMOTHBUNKER` still directly binds `MammothTusk`; shared roots/descendants and
map override compatibility were deliberately retained. Even abstracting all three
parent identities would remove at most three findings while five new concrete
owner wrappers must remain visible, so that would not restore either ratchet.
Converting their families would change geometry/armor behavior and requires a
separate supported role decision; hiding wrappers or raising ratchets would
misrepresent this audit. Neither is performed here.

Evidence: `validation/ownership-continuation-missile.log` (audit exit 1; peak
RAM 48.02%) and `ownership-continuation-missile-wrappers.log` under the handoff
evidence root. The latter enumerates all five findings, parent consumers and
exact ordered-payload equality. These new failing R3/R4 gates supersede any
inference of a fully passing source audit set.

## Source documentation-claim refresh

After updating only `warhead_family_reach` and both listed documents, the fresh
source `audit_doc_claims.py` checks 22 claims: 17 match and five remain mismatched;
exit **1**. Family reach now matches **1454 / 1454**. The five remaining mismatch
identities already appeared in the previous source report, but their current
measurements are recorded here rather than copied from that older snapshot:

| Claim | Documented | Current source |
|---|---:|---:|
| `multi_main_fired_weapons` | 184 | 122 |
| `meters_filling_before_death` | 269 | 291 |
| `w24_multi_main_fed` | 429 | 426 |
| `physical_state_fired_weapons` | 534 | 542 |
| `unconverted_template_inheritors` | 1596 | 1592 |

Those registry values and predicates remain untouched. The report is not a
passing doc-claims gate. Evidence: `validation/ownership-continuation-doc-claims.log`
under the handoff root; peak total-system RAM 57.38%. No full suite was rerun.

Combined-candidate reconciliation: the converter/lookup complete-actor checks now
accept PR339's exact reviewed Katyusha Tooltip name only when the Combined Arms
override is exactly KATY, then restore the old name before original hash checks.
The full source-versus-combined Soviet vehicle file differs only at that Tooltip
name. No hashes or runtime values changed. Source rerun: both modules, six tests
passed; peak RAM 49.79%; evidence ownership-continuation-katyusha.log. Combined
modern-branch validation remains the integration coordinator's affected rerun.

## Reopened technical follow-up — rename visibility

The supplemental release view follows194 pinned reviewed renames and recovers156
historical identities. It compares their current values with their original released
identities and exposes differences rather than waiving them. Missing mappings,
conflicts and changed provenance fail visibly. The original raw counts and exit
gates are unchanged.

The missile report now also groups exact reviewed owner wrappers whose current
ordered payload equals their retained parent. All concrete members stay printed
and counted in the raw gate. The five wrappers account for the new raw R3/R4
count increase; equivalence does not establish that their inherited roles are correct.
Changing the gating policy or gameplay families remains unresolved.

Nine focused lineage/equivalence tests passed, including mutation, event order,
provenance and raw-failure-preservation checks. Both source audits were regenerated
and retain exit1. No runtime YAML, damage values, accepted-value pins or thresholds
changed in this technical follow-up.
