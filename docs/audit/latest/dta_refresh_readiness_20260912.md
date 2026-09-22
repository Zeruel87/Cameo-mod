# DTA refresh readiness — 12 September 2026

## Corrected extraction and corpus refresh

The new archive is now admitted through the extractor’s safe single-source path:

- archive SHA-256: `76765cb3fdb96ab9470abad45e828c8502701b463ba2b8bb2acb403f442a3ec4`
- `Rules.ini`: `786f0ae5babce2e9052c6a484f31c62663bf5150d0e652a3fe2efa75a5a126c9`
- `Enhance.ini`: `d836d5a9f9ac227e6b56262e96e9f665e58af10099b63712ec210ee25176edde`
- DTA Classic: **863 rows**
- DTA Enhanced: **863 rows**

The extractor now reads Vinifera’s `$Inherits=` key, resolves inheritance within
each file before applying overlay precedence, and refuses cyclic chains. The
Enhanced file reverses the Classic `ARTY`/`RAARTY` relationship; resolving after
the merge would manufacture cycles and discard fields. Named partial exports also
refuse unreadable, malformed or source-incomplete existing output unless
`--force-partial` is explicit.

The corpus refresh replaced only the 1,726 DTA rows. All 10,144 non-DTA lines
remain byte-identical. Current-branch weapon-channel corrections were preserved;
the refresh contributes the source-owned inheritance and balance deltas: the flak
rework, minigunner-family range `2.5 -> 2.67`, pillbox warhead changes,
`special_heavy` armor, and the inherited ownership/prerequisite/buildability
values present in the new archive. The corpus now hashes to
`c1883cb04d2b42b370aa1dba3bdd12c080d909c61a3d3adf92156f5f931ed92a`.

The range, cycle and reviewed weapon-selection receipts were re-fingerprinted
against the new DTA rows. Only the five declared `2.67` range entries changed;
no profiled cycle timing changed. Historical armor/payload receipts that still
name the earlier archive remain historical and are not silently re-admitted as
new-source runtime proof.

The derived `faction_profiles.json` was regenerated from the refreshed corpus:
96 faction profiles across nine sources. It is a diagnostic summary only; it
does not alter the reference assignment or any gameplay value.

The corpus-wide derived `armor_normalized.json` was regenerated as well; its
nine source sections now match the current corpus. The TS adapter
continues to admit only the shared `none`/`wood`/`concrete`/`light`/`heavy`
vocabulary; `medium`, `special_heavy`, `rocket` and naval-specific tags remain
explicitly unmapped rather than being assigned a ladder by assumption.

## Static map refresh

The four-faction map was regenerated from the current-base corpus and selector:

```text
python tools/balance/build_reference_report.py --faction td_gdi td_nod ra1_allies ra1_soviets --out <external-output>
```

The published HTML still contains **66 originals, 82 expanded, 270 references
and 23 formula-priced rows**. Its DTA values now reflect the corrected archive,
including `td_gdi_minigunner`’s updated nominal range and the corrected flak
channels. This is a static review artifact; it does not apply prices, votes or
gameplay changes.

## Validation

- `python -m unittest tools.tests.test_ini_weapon_evidence -v`: **51/51**.
- DTA corpus, range, cycle, consumer, selection and map contracts: **52/52**
  (one external-before-corpus test remains intentionally skipped without its
  report-time input).
- Japan-pilot provenance closure after the derived-artifact refresh: **77/77**.
- The extractor’s direct archive run produced 863/863 rows for both labels.

The current-base-compatible corpus and map are safe to review and publish. DTA
runtime/client-version applicability, secondary payload timing and the separate
OpenRA peer artifact remain unverified; PR #349’s master-based generated peer
document was not imported wholesale because its removals and evidence changes do
not satisfy this branch’s base-corpus contract.
