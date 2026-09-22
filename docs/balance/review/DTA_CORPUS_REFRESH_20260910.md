# DTA corpus refresh — before/after data + consumer + target impact (2026-09-10)

**No live unit stats changed.** The parent session re-extracted the two DTA sources and
merged the refresh into the WORKING-TREE `docs/reference/ini_corpus.json` (the parent's
fresh merge — **currently uncommitted**; this report pins it by hash, it does not claim it
has been committed or shipped). No yaml, ledger or anchor was touched, so nothing on the
playtest side changes; what changed here is ANALYTICAL — which reference rows get to be
called a DPS estimate at all — and that is measured below. Nothing was modified by the
measurement itself — no code, no corpus, no assignment file, no audits. The assignment is
FIXED: no regeneration, both sides read the same working-tree
`docs/balance/derived/reference_assignment.json`.

## Provenance by hash (verified here, not trusted)

| object | sha256 |
|---|---|
| external before-corpus (`ini_corpus.before.jsonl`) | `204391b21a95b3c5…` |
| working-tree `docs/reference/ini_corpus.json` (parent's fresh merge, uncommitted at report time) | `b8fec564b958a2d2…` |
| parent's `ini_corpus.updated.jsonl` | `b8fec…` — **byte-identical to the working-tree file** |
| exact received DTA rules texts, verified row-by-row | `Rules.ini` = `6329487eecaa12fb…` (Classic rows' `source_sha256`); `Enhance.ini` = `40a8a48a14239d43…` (Enhanced rows' `overlay_sha256`) |

* Total rows unchanged: **11,870**; DTA Classic 863 + DTA Enhanced 863 = **1,726** replaced.
* **All 10,144 non-DTA lines byte-identical** between before and after — compared as RAW
  byte lines (`splitlines(keepends=True)`), order, duplicates and line endings intact.
  (The earlier "10,141" figure was a keyed (source, id)-dict count that silently collapsed
  3 duplicate identities the OLD corpus already carried — `Red Resurrection NAINDP`,
  `Red Resurrection NAFLAKAI1`, `RA2 Reborn NAPSYA`; they are carried through, never
  merged. Unique ids: 10,141 of the 10,144 lines — same on both sides.)
* Every DTA row carries `source_runtime_version_status` = `unverified`,
  `engine_profile_applicability` = `unverified`, `profile_selection` = `user_declared`,
  `overlay_precedence` = `none` (Classic) / `overlay_over_rules` (Enhanced). **No
  `verified`/`ready`/`factory` token appears in any provenance or verdict field** — this
  report pins data, not runtime applicability.

## The 127 counter — definition and recount

**127 = rows of ONE DTA source whose BEFORE row carried a positive numeric `w_dps` (the old
corpus was presenting it as an authoritative rate) and whose AFTER row withholds it
(`w_evidence: incomplete` or `w_dps_usable` not True).** Recounted independently here:
127 (DTA Classic) + 127 (DTA Enhanced) = **254 rows** — matches the parent's final number;
the preliminary 132 is superseded. The consumer carries such a number POSITIVELY on
`w_dps_raw` and withholds the vote; raws are never read as zeros (some are legitimately
negative healing channels).

## Primary identities and slots (data contract)

10 primary identities per source were corrected (old auto-promotions reversed):
`AIMTNK`, `AISCRINTNK`, `AIXO`, `BRIG`, `EKRACARR`, `MTNK`, `MWAVEMSAM`, `SCRINTNK`,
`SP941`, `XO`. The original primary keeps `w_*` with its own evidence; the secondary is
whole under `w2_*` with its own verdict (`XO`: `w2_weapon = XOMachineGun`,
`w2_evidence = nominal_direct`); `w_from_secondary`-style promotion no longer happens
unbidden. XO contracts verified in both sources against the exact received texts:
`weapon = XORail`, `w_railgun = True`, `w_ambient_damage = 150`,
`w_evidence = incomplete` (`exotic_channels`), **no `w_dps`**; no elite claims, no
"factory ready" claims — none exist in the data.

## Limitation on the withheld raws (recorded, not hidden)

Of the 127 previously-positive rows per DTA source, **117** keep a NONZERO direct-channel
diagnostic on the new `w_dps` (the consumer then carries it as `w_dps_raw`) — but the 10
identity-corrected rows CANNOT preserve one: their old positive primary was replaced by a
primary whose direct channel reads the engine default (0), so no `w_dps_raw` exists for
them. The historical positive rate of those 10 rows survives only in the BEFORE table, and
in the new data only as the `w2_*` slot record (10 of 10 in each source), which never
votes. The raw NEW damage channels (`w_railgun`, `w_ambient_damage`, particles) are kept
in every case; what is not recoverable is the OLD primary-number-as-authoritative-rate —
by design.

## Consumer impact (the withholds actually withhold)

Distribution lane = the lineage representative only (`DTA Enhanced`; DTA Classic is a
lineage member and AI-only variants are filtered, both pre-existing rules):

| population | rows | withheld (`w_dps` → `w_dps_raw`) | notes |
|---|--:|--:|---|
| ordinary lane, DTA (in 4,384 peers) | 156 | **37** | 32 positive + 5 negative raws, all verbatim-copied, all `dps_vs_*` = None |
| AI-only lane (excluded from distribution lane) | — | **29 withheld, out of every vote** | |
| build-limit lane (`peer_hero_rows`) | — | **5** | hp/cost intact, `dps_vs_*` = None |
| evidence counts (all 4,384 peers) | 4,384 | `incomplete` 41 · `nominal_direct` 46 · `legacy-unassessed` 4,297 | honest mix, exposed by `evidence_counts` |

`nominal_direct` rows keep the DECLARED contract (`w_dps` numeric + `w_dps_usable: True`,
`w_dps_usable` absent/None on everything else) — that is a direct-channel rate, never a
complete weapon total, and no number in this report should be read otherwise.

## Target impact — 178 assignments × 5 stats (old corpus -> new, same consumer, same assignment)

* **hp / speed / cost: unchanged on all 178.** Fully.
* **`w_range` and `w_dps`: 63 actors changed each** (per-stat):
  * **2 actors lost their weapon targets entirely** — their only range/DPS vote was DTA-only
    and is now withheld: `ra1_allies_alliedheavyaatank` (5138.6 / 394.1 → none),
    `td_nod_buggymkii` (4963.0 / 325.6 → none);
  * 61 re-targeted both stats from the DTA distribution shift. Largest moves:
    `ra1_soviets_teslacoil` `w_dps` 5833.7 → 10280.5 (+76%),
    `ra1_soviets_missilesubmarine` 290.2 → 194.6 (−33%),
    `td_gdi_mlrs` 366.4 → 247.1 (−33%),
    `ra1_soviets_v2rocketlauncher` 313.4 → 213.0 (−32%),
    `ra1_soviets_yakscoutplane` 2195.5 → 1630.9 (−26%);
    largest `w_range` moves are ±13% (`td_nod_samsite` −12.6%,
    `ra1_soviets_migattackbomber` +10.5%);
  * Japan is untouched (no DTA reference reaches it); the other four classic factions carry
    the whole impact.
* All values are `target_for` measurements under the current consumer policy — measurement
  only; no ledger, yaml or anchor was produced, and none may be inferred from this file.

## Tests

New `tools/tests/test_dta_corpus_evidence.py` — **17 tests total: 14 pass unconditionally**
(corpus shape, provenance, identities, consumer withholding, `evidence_counts`), and
**+3 baseline-gated byte/counter tests pass when `REFERENCE_DTA_BEFORE_CORPUS` is set**
(17/17 measured and green with the pinned baseline path; the optional group first
VALIDATES the baseline sha256 `204391…` and refuses the file on mismatch — then compares
non-DTA content as raw byte lines: **10,144 lines, order + duplicates + endings intact**,
unique ids 10,141 with the 3 duplicate identities enumerated). Bounded and read-only: the
working-tree corpus + the existing loaders are read, never written; the suite does not
depend on the document store; closed file handles throughout (`with … read_bytes`).
