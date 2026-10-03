# Classic-four harvester durability batch — aggregate milestone, 2026-09-18

This is the harvester slice in the aggregate classic-four harvester/pipeline/
support/transport milestone that supersedes #404–#406 as one reviewable head.
It is the economy-unit slice the 2026-09-15 accepted batch explicitly held back
("this batch does not invent replacements for ... economy units"). It applies the
2026-09-16 reference-map targets for the classic four's harvesters, which restores
harvester survivability after the multiplier retirement (W17/W26) while the
warhead rework is still pending. No weapon, warhead, `Burst` or `BurstDelays`
field is touched.

## Evidence

`docs/audit/latest/Cameo-reference-map-original-four-20260916.html` (the newest
published reference map; its superseded 20260911 checkpoint in
`docs/balance/checkpoints/` carries the same rows within float noise). Harvester
weapon estimates are withheld by every source (0/3, 0/1, 0/2 model DPS
eligibility), so the batch is chassis-only, matching the 2026-09-07 ruling that
economy units extract HP and Speed only. Armor had no reference projection and
stays on each template (`Heavy`/`Heavy`/`Heavy`/`Medium`/`Medium`).

## Applied values (unsnapped target -> applied grid)

| Actor | HP | Speed | Self-heal Step | Repair HpPerStep | Cost | Sources |
|---|---:|---:|---:|---:|---:|---|
| td_gdi_tiberiumharvester | 239,813 -> **240,000** | 60 -> **69** | 60 -> **96** | 7,500 -> **12,000** | 1,000 -> **1,670** | 3/3 |
| td_nod_tiberiumharvester | 239,813 -> **240,000** | 60 -> **69** | 60 -> **96** | 7,500 -> **12,000** | 1,000 -> **1,670** | 3/3 |
| td_nod_stealthharvester | 175,085 -> **175,000** | 75 -> **77** | 50 -> **70** | 6,250 -> **8,750** | 1,000 -> **1,520** | 1/1 |
| ra1_allies_alliedoretruck | 209,944 -> **210,000** | 90 -> **81** | 40 -> **84** | 5,000 -> **10,500** | 1,000 -> **1,560** | 2/2 |
| ra1_soviets_oretruck | 209,944 -> **210,000** | 90 -> **81** | 40 -> **84** | 5,000 -> **10,500** | 1,000 -> **1,560** | 2/2 |

Grids per the accepted-batch rule: HP on the 1,000 grid, Speed integer, cost on
the 10-credit grid. Heal and repair steps scale with the same HP ratio so
time-to-full, repair time-to-full and the F1/F2 identities
(`HpPerStep == HP/20`, `Step == HP/2500`) are preserved exactly. TurnSpeed
follows the F8 law (`round(Speed/5)`): the TD pair moves 12 -> **14**, the RA1
pair 18 -> **16**, the stealth harvester stays **15**.

`ra1_soviets_heavyindustrialminer` had no reference projection (0/0 sources) and
keeps its authored values, which already override the ore-truck block it
inherits from.

## Application mechanics

* The shared templates `^TDHARV` (TiberianDawn Shared) and `^RAHARV` (RedAlert
  Japan templates) also feed four Tiberian Sun harvesters and japan's ore truck;
  to leave those untouched, the batch materializes per-actor child blocks in the
  five classic-four actors, the same override shape
  `td_nod_stealthharvester` and `ra1_soviets_heavyindustrialminer` already use.
* `tools/balance/apply_harvester_durability.py` performs the edit (idempotent,
  with complete resolved old/target preflight, per-file atomic replacement,
  rollback, and optimistic byte guards; exclusive writer ownership remains
  required). It remains a separate materializer because `apply_balance` refuses
  inherited-src edits; #405 now carries named self-heal and repair fields
  through the ledger.
* Ordering-sensitive: inserted children land at the END of each actor block. A
  block's own children placed BEFORE `Inherits:` lose same-key merges to the
  template (observed on this batch during the first run; resolved values and
  the test now guard both).

## Derived sidecars

A full re-extract ran: 34 raw ledgers + 34 derived sidecars. Unrelated
factions' sidecars wobble at the float rounding level for context-pool reasons
documented by the 2026-09-15 batch; `tools/balance/check_determinism.py`
reproduces all 69 refreshed artifacts byte-identically across two runs.

## Tests

- `tools/tests/test_accepted_classic_four_harvester_batch.py` — chassis and
  price contract for the five actors, plus a non-interference test pinning
  `^TDHARV`-derived TS harvesters, japan's ore truck and
  `heavyindustrialminer` to their unchanged resolved values.
- All four accepted-batch test files still pass (24 tests total, OK).
- `audit_stat_formulas.py` gains NO new harvester findings (F1/F2 exact, F8
  exact after the TurnSpeed move; remaining F-sections are pre-existing).

## Playtest focus

- Rocket soldier / harvester economics: a GDI or Nod rocket soldier hitting a
  240,000-HP harvester should feel like harassment, not a kill race at any
  engagement range.
- The RA1 ore truck trades durability for speed (90 -> 81): check whether
  Soviet ore deliveries read as brisk but catchable.
- Harvester cost walked 1,000 -> 1,670 (TD) / 1,520 (stealth) / 1,560 (RA1):
  the economy price ladder should never leave the classic four unable to open.
