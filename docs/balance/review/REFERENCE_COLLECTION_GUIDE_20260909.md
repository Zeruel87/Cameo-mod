# Reference collection and pilot diagnostics

## Scope

These tools collect inspectable reference evidence and test the translation method.
They do not apply balance, certify source-game fidelity, or sign off class anchors.
Keep original game/source files outside the repository. Use a fresh external output
directory for changed results; differing existing artifacts are not overwritten.

| source | inspected source identity | collection result | remaining limitation |
|---|---|---|---|
| RA3 | EA CnC Modding Support, `3aad8e412961ab543192ae70f8503dc8e178e095` | 75 roster records: 63 static candidates, 12 manual-review records; 452 other objects itemized separately | unsupported fragments/merges and dependency warnings remain; not verified final retail patch |
| Dune II | OpenDUNE `9781a1c2fd14dfa09611d3502456d7918d862e96` | 27 unit-table records and 6 house records | reconstructed 1.07 static tables, not a retail executable or scenario-availability proof |
| Emperor | archived Rules.txt, SHA-256 `a1de5044aebc837d439892a081674ceb919007b87887abdf999cf099ff5f692d` | 99 records; 52 static buildable candidates; weapon dependencies retained separately | example/hierarchy archive, file Version=1.23 is not a verified retail patch |
| DTA | Aedis archive received 10 September 00:46; hashes in DTA research report | Rules/Enhance extraction and corpus refresh completed; omitted X-O rail channel retained and unsupported votes withheld | selected mode and engine version unverified; no complete X-O DPS claim |
| Spice Wars | no versioned primary dataset acquired | pending | do not substitute an unsourced community table or another Dune game |

Counts above are collection records, not unique eligible combat units. For example,
OpenDUNE includes projectile, superweapon and wildlife entries. All new RA3/Dune
collection outputs withhold automatic balance eligibility. MCVs and harvesters are
manual-review only; their presence is never permission to fit them with combat units.

### Spice Wars acquisition check (10 September)

The official [game site](https://dunespicewars.com/) and publisher/developer
[Steam announcement stream](https://steamcommunity.com/app/1605220/announcements/)
provide release context, including a patch announcement dated 9 July 2025, but this
check did not acquire a versioned full unit-stat dataset. Patch deltas alone cannot
reconstruct the complete base roster. The configured local Steam library did not list
Spice Wars (app 1605220). No game was purchased, installed, downloaded or executed.
Community tables/mod packs remain discovery leads, not certified retail evidence.
This source remains a named input hold; obtaining version-identified original data is
required before extracting or fitting its numerical stats.

## Source acquisition

- [EA CnC Modding Support](https://github.com/electronicarts/CnC_Modding_Support):
  inspect the `Red Alert 3/Xml` and `Red Alert 3/Schemas` directories at the stated
  revision, with the repository's license and additional terms. Do not execute it.
- [OpenDUNE](https://github.com/OpenDUNE/OpenDUNE): inspect the stated revision's
  `src/table/unitinfo.c`, `src/table/houseinfo.c`, `src/unit.h`, `src/house.h` and
  `src/structure.h`. Retain its GPL licensing/provenance separately from retail data.
- [Dune2k Emperor modifications archive](https://dune2k.com/Duniverse/Games/Emperor/Downloads/Modifications),
  [Rules.txt download](https://dune2k.com/Download/15): verify the exact SHA-256 above.
  A different file or a modified unlock-rules example is a different reference.

The extractors do not download source files or run source code. Provide paths explicitly.
Git HEAD, dirty state and input hashes are evidence; HEAD alone does not identify locally
modified contents. Unresolved values stay unresolved rather than being evaluated as code.

## Commands

Run from the Cameo repository root, substituting external source/output paths:

```text
python tools/reference/extract_ra3_units.py --source-root <EA-checkout> --output <external-output>/ra3.json --expect-commit 3aad8e412961ab543192ae70f8503dc8e178e095
python tools/reference/extract_opendune_units.py --source <OpenDUNE-checkout> --out <external-output>/opendune.json
python tools/reference/extract_emperor_units.py --source <external-source>/Rules.txt --out <external-output>/emperor.json
python tools/balance/build_japan_pilot.py --out <external-output>/japan
python tools/balance/build_japan_pilot.py --baseline <external-output>/japan/japan_reference_pilot.json --out <another-external-output>/japan
python tools/balance/validate_reference_holdout.py --max-actors 20 --out <external-output>/holdout
```

The Japan `--baseline` option pins input fingerprints and refuses mismatches. It is
**not an archived copy of every input**, nor does it evaluate a changed candidate against
an immutable stored calibration. Preserve the source checkout/export separately. A new
source revision or changed calibration requires a new explicitly identified pilot run.

`--pending` can supply a read-only pending-class overlay. Without it, pending membership
is `NOT_CHECKED`, not “no pending changes.” No command above writes unit-stat targets to
ledgers or YAML, and none invokes a game build or launch.

## Reading the results

### Raw collection

RA3 follows the selected active XML include graph. It retains source paths, inheritance,
conditions, unresolved includes and raw expressions instead of pretending to implement the
entire SAGE engine. Per-field presence does not imply resolved semantics. Automatic balance
eligibility remains false even for ordinary-looking units.

OpenDUNE's bounded parser reads initializer and enum data without executing C or Python
expressions. An unknown explicit enum value invalidates following implicit values until a
known explicit reset. This prevents plausible but fabricated successor values.

Emperor preserves repeated fields and veterancy boundaries. Repeated values across separate
levels are distinct from conflicting values in one context. The inspected file contains
130 contextual repetitions, 2 conflicting-key findings, 15 dangling declarations and 15
unresolved references. These are 162 reported occurrences, not 162 broken units. The two
pre-level conflicts are ATKindjal's StormDamage and IXInfiltrator's ExplosionType. Neither
should be silently certified as an intended gameplay value.

### INI damage evidence

The updated extractor keeps primary and secondary identities. A missing/zero direct damage
value does not prove a dummy weapon; unknown primary damage is not automatically replaced
by a clean-looking secondary estimate. Known effect-driven channels, unsupported bursts and
unresolved dependencies produce incomplete evidence. A plain supported single-shot estimate
is labeled `nominal_direct`, not complete real-time unit DPS.

Both ordinary and hero consumers preserve evidence and withhold explicitly incomplete
weapon metrics. Chassis/cost data remain available. Target projection follows the same
eligibility rule as population construction, including eligibility of Cameo's own vote.
The DTA Classic/Enhanced corpus slices now carry exact Rules/overlay hashes and explicit
evidence from the received archive. Source runtime semantics remain unverified. Other
corpus sources retain legacy-unassessed compatibility numbers, not retrospective validation.

See [the DTA research report](DTA_INI_EXTRACTOR_RESEARCH_20260909.md) for the reproduced
X-O arithmetic, engine-version caveats and actor-by-actor review requirements.

### Japan and withheld-reference diagnostics

The Japan report separates source-only projections, Cameo-inclusive R4 targets and
unapproved same-class sensitivity. Source disagreement and match provenance are visible.
A class-wide ratio preserves existing within-class imbalances; it is not a redesign.

The holdout tool hides a reference's truth from its predictors and calibration, then
compares the prediction with the hidden value and a simple type-median baseline. It
tests HP, speed and cost only. It does not test unit counters, weapon damage, class fitting
or runtime behavior. Read sample coverage, exclusions and evidence levels before interpreting
the error summary. No arbitrary pass threshold turns this report into balance approval.

## Verification and next gates

Run the relevant synthetic test modules under `tools/tests/`. Real Dune integration tests
are opt-in with `CAMEO_REFERENCE_RAW_SOURCES` pointing to the external source collection;
skipped source tests must not be reported as real-source validation.

Before publication, compare the full test suite and audits with the same upstream base,
review changed numerical targets and generated files, and independently challenge the
source/consumer boundary. A menu boot validates loading only. W24 structure, complete weapon
operation, class membership/tier, armor and intended faction-role relationships must be
settled before recommending applied damage/stat changes.
