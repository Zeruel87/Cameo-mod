# Classic-four transport chassis batch — aggregate milestone, 2026-09-18

This is the transport slice in the aggregate classic-four harvester/pipeline/
support/transport milestone that supersedes #404–#406 as one reviewable head.
It applies the chassis-only HP, Speed, and Aircraft.TurnSpeed projections from
the 20260916 reference map. Carrier Cost is deliberately unchanged: all four
authored `Cargo.InitialUnits` loads are valid full loads whose passenger sum
equals the current carrier cost, and the cargo pricing law owns that field.
This is the explicit cargo-law exemption from the ordinary 10-credit candidate
grid: a carrier cost is the integer sum of its passenger costs, even when that
sum is not itself a multiple of ten.

| Actor | HP | Speed | Aircraft TurnSpeed | Self-heal Step | HpPerStep | Cost |
|---|---:|---:|---:|---:|---:|---:|
| `td_gdi_chinooktransport` | 100,000 -> **82,000** | 150 -> **124** | 30 -> **25** | 40 -> **33** | 5,000 -> **4,100** | **4,120 held** |
| `td_nod_chinooktransport` | 100,000 -> **82,000** | 150 -> **124** | 30 -> **25** | 40 -> **33** | 5,000 -> **4,100** | **3,853 held** |
| `ra1_allies_alliedchinooktransport` | 125,000 -> **88,000** | 125 -> **120** | 25 -> **24** | 50 -> **35** | 6,250 -> **4,400** | **4,300 held** |
| `ra1_soviets_hiptransport` | 150,000 -> **104,000** | 100 -> **118** | 20 -> **24** | 60 -> **42** | 7,500 -> **5,200** | **2,760 held** |

HP uses the 1,000 grid. Speed and aircraft TurnSpeed follow the helicopter
F19 law (`round(Speed / 5)`); self-heal uses the nearest integer to HP/2500,
and repair uses HP/20. Every actor already owns its Aircraft, Health,
Repairable and SelfHealing blocks, so no shared transport template is edited.
`Aircraft.TurnSpeed` is also emitted as `turn_speed_air` in the raw ledger, so
drift checks cover the field instead of relying only on the resolved contract.

Cargo was inspected directly through `cargo_pricing.authored_load`: all four
loads are valid and filled to capacity, including the Nod Chinook's eight
authored passengers whose heavier passenger weights total 11. No Cargo,
InitialUnits, MaxWeight or passenger price changes are included.

The dated `band-scope-20260911.json` and checkpoint cargo reports are historical
diagnostics from before the accepted passenger-price batch; their old unresolved
rows are not current evidence. The current cargo state is the direct
`cargo_pricing.authored_load` result recorded above and is covered by the focused
contract in this batch.

## Playtest focus

- Check whether the lower transport HP makes infantry drops vulnerable without
  making transport production uneconomical; cost remains the passenger sum.
- Check the faster/slower reach changes at factory state and during unload.
- Treat any future transport cost change as a separate cargo-law decision with
  cross-carrier passenger-price impact.

## Verification

- Resolved transport contract: chassis, raw-ledger Aircraft.TurnSpeed, and
  full authored-load coverage for all four transports
- Cargo pricing: 8/8, 11/11, 10/10 and 8/8 full authored loads; costs equal
  passenger sums
- `audit_balance_drift`: clean, 34 ledgers
- `find_empty_warhead.py`: 0; `audit_stat_formulas.py`: no transport findings
- `check_determinism.py`: 69/69 byte-identical
- Boot gate: `MenuPostProcessEffect.PostWorldLoaded`, zero new exceptions
