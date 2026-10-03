# Reference-target delta — baseline 50b7 vs candidate 50b7 (read-only, 2026-09-10)

**Historical pre-corpus-refresh snapshot.** The later DTA-only evidence refresh changes
reference inputs and requires its own target-impact comparison. The 4384 legacy-only
label count below is not the current corpus status after that refresh.

**No balance change.** This doc compares two measurement runs; nothing in yaml, ledgers,
corpus, tests or tools was altered by it. Both trees sit at the same commit
`50b7d001b` ("TS Civilian Buildings and Tilesets for Urban Temperate").

## What was compared

| tree | path | delta vs HEAD |
|---|---|---|
| baseline | `../japan-pilot-baseline-86b41c` | input code/data unchanged at `50b7d001b`; generated audit outputs are present |
| candidate | this worktree | `reference_distribution.py` + `reference_targets.py` (the consumer evidence gate + `rd.eligible` gate in `target_for`) and its own regenerated `reference_assignment.json` (Katyusha override, below); `assign_references.py` is another worker's live WIP and was NOT imported |

Method: one fresh subprocess per tree, isolated `sys.path` (no cross-import), each passing the
production path `peer_rows → distributions → attach/expand_families → target_for` over
`td_gdi`, `td_nod`, `ra1_allies`, `ra1_soviets`, `japan`. 178 assignment rows compared
per tree (same set on both sides), 5 stats each. All numbers are `target_for` outputs
(`with_cameo` and per-stat source count `n`).

## Legacy evidence labels — not hidden

Candidate peer corpus: **4384 rows, all `legacy-unassessed`** — the committed
`ini_corpus.json` predates the extractor's verdicts; absent status is legacy, numbers kept
for compatibility, certified nothing. The baseline run has no evidence labelling at all. No
row in either run carries `nominal_direct`/`incomplete` yet, so every gate decision below is
made on plain w_dps usability, not on the new verdicts.

## Numerical delta — scoped to the four classic factions + Japan

### `w_range` — 13 actors changed by the eligible gate

| actor | src (w_range) | target |
|---|---|---|
| `ra1_allies_mechanic` | 3 → **0** | 3336.16 → none |
| `ra1_allies_medic` | 3 → **0** | 4132.78 → none |
| `ra1_allies_rifleinfantry` | 3 → 2 | 3088.06 → 4486.44 |
| `ra1_soviets_rifleinfantry` | 3 → 2 | 2964.00 → 4247.74 |
| `ra1_allies_alliedchinooktransport` | 1 → **0** | 3910.30 → none |
| `ra1_soviets_hiptransport` | 1 → **0** | 3910.30 → none |
| `td_gdi_chinooktransport` | 1 → **0** | 3910.30 → none |
| `td_nod_chinooktransport` | 1 → **0** | 3910.30 → none |
| `ra1_soviets_nukedemotruck` | 2 → **0** | 1800.38 → none |
| `japan_japaneseflamethrower` | 1 → **0** | 4784.61 → none |
| `td_gdi_minigunner` | 3 → 2 | 2720.09 → 3912.32 |
| `td_nod_minigunner` | 3 → 2 | 2602.64 → 3688.72 |
| `td_gdi_archerartillery` | 2 → 1 | 15858.41 → 12588.35 |

Examples of what the gate removed: DTA `MECH` carries `w_dps = -8.325` (negative, unusable —
never a DPS estimate), CA/OpenRA-RA `TRAN` carry `w_dps = None` while declaring `range`. Those
rows used to vote their range against other rows' aggregates; now they abstain, exactly like
`build_distributions` already abstained them. 8 actors lose a range target they never had an
honest vote for; 4 retarget upward (fewer low-quality votes pull the pooled coordinate), and
`archerartillery` retargets down.

### Not changed by the gate

`hp`, `speed`, `w_dps`, `cost`: **zero** actors changed other than the row below. Chassis and
price targets are untouched by the gate.

### The intended Katyusha mapping — NOT gate-caused

`ra1_soviets_v1rockettruck` is the only assignment change: the added override
`ra1_soviets_v1rockettruck → Combined Arms KATY` (the V1 Rocket Truck's intended reference,
per the Katyusha-identity work) takes it from **0 attached references to 1 source**. That
single new row produces with-Cameo targets (`hp` 31007.1, `speed` 77.9,
`w_range` 9609.7, `w_dps` 482.7). These are diagnostic projections, not applied stats.
The Katyusha line is mapping-driven, not gate-driven, and its `KATY` row is fully
w_dps-eligible (`w_dps = 62`).

## Uncertainty / notes

* Same-base full runs at `50b7d001b`: baseline 1306 tests, 16 failures, 8 errors,
  45 skipped; candidate 1609 tests, 16 failures, 8 errors, 63 skipped. All 24 failure/error
  signatures match exactly. The two additional signatures versus the earlier `86b41c007`
  baseline (ADATS/TKM) therefore reproduce without this batch's changes.
* `target_for` per-stat source counts as reported here are the counts of sources with at
  least one voting perimeter (`used`); no ship-side change follows from these numbers.
* One re-run would be expected to reproduce exactly: both collectors are pure reads over
  committed inputs plus documented deltas.
