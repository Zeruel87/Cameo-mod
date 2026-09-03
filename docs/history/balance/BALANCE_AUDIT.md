> ⚠ **ARCHIVED — provenance, not current truth.**
>
> Deleted by the 83→43 documentation compaction (`20f15194`) and restored here on
> 2026-08-28 after a mechanical re-check found it was **not regenerable**, unlike the
> thirteen `proposal_*.md` reports deleted alongside it. Its generator, `tools/balance/_balance_audit_report.py`, raised `ModuleNotFoundError: No module named 'scout_rebalance_proposal_final'` — a module removed long ago. The script was dead, nothing ran it, and it was **deleted on 2026-08-28**. Recover it with `git show 6e0a273b:tools/balance/_balance_audit_report.py` if the methodology is ever wanted back.
>
> Its numbers are a snapshot of a **pre-W24 tree**: the weapon rebuild has moved damage
> structure since, so read it for method and for what was measured at the time, never as
> a current statement about the roster.

# Infantry Rebalance Delta Audit

This audit lists every unit whose formula price does not match its target cost
within +/- 1 credit.  The range solver is used to identify whether the mismatch
can be fixed by a simple range adjustment or whether the cost/stat/tech combination
is inconsistent with the class band.

## scout

- Total units: 17
- Units with |Δ| > 1: 13

| actor | HP | spd | current rng | cost | formula price | Δ | required rng | in band | min price in band | max price in band | recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `asianalliance_asianmilitia` | 24000 | 53 | 5500 | 110 | 64 | -46 | 1710.9 | False | 127 | 132 | cost too high for band; lower cost to ~132 or raise hp/dps |
| `ixian_lightinfantry` | 32000 | 56 | 4580 | 150 | 157 | +7 | 667.0 | False | 222 | 236 | cost too high for band; lower cost to ~236 or raise hp/dps |
| `ordos_lightinfantry` | 28000 | 62 | 5490 | 120 | 105 | -15 | -1481.2 | False | 175 | 183 | cost too high for band; lower cost to ~183 or raise hp/dps |
| `latinsyndicate_latinmilitia` | 25000 | 51 | 4570 | 250 | 253 | +3 | 5173.5 | False | 258 | 284 | cost too low for band; raise cost to ~258 or lower hp/dps |
| `naxis_naxiriflerecruit` | 21000 | 48 | 4560 | 75 | 98 | +23 | -1562.2 | False | 140 | 149 | cost too high for band; lower cost to ~149 or raise hp/dps |
| `ra1_soviets_ak47conscript` | 44000 | 71 | 4540 | 200 | 649 | +449 | -461.7 | False | 647 | 722 | cost too high for band; lower cost to ~722 or raise hp/dps |
| `ra2_allies_gi` | 50000 | 50 | 4520 | 200 | 472 | +272 | -52.9 | False | 491 | 544 | cost too high for band; lower cost to ~544 or raise hp/dps |
| `forgotten_mutant` | 45000 | 65 | 4590 | 160 | 248 | +88 | -2025.9 | False | 342 | 366 | cost too high for band; lower cost to ~366 or raise hp/dps |
| `ra2_soviets_conscript` | 26000 | 58 | 4510 | 100 | 223 | +123 | -1192.5 | False | 253 | 276 | cost too high for band; lower cost to ~276 or raise hp/dps |
| `tkm_trooper` | 33000 | 59 | 4500 | 360 | 358 | -2 | 5148.7 | False | 374 | 412 | cost too low for band; raise cost to ~374 or lower hp/dps |
| `td_gdi_minigunner` | 31000 | 63 | 5480 | 100 | 67 | -33 | -11720.1 | False | 163 | 166 | cost too high for band; lower cost to ~166 or raise hp/dps |
| `ra1_allies_rifleinfantry` | 27000 | 55 | 4550 | 100 | 116 | +16 | -1806.7 | False | 177 | 187 | cost too high for band; lower cost to ~187 or raise hp/dps |
| `ra1_soviets_rifleinfantry` | 34000 | 54 | 4530 | 100 | 151 | +51 | -3063.4 | False | 221 | 235 | cost too high for band; lower cost to ~235 or raise hp/dps |

## closecombat

- Total units: 4
- Units with |Δ| > 1: 0

No delta issues.

## special_forces

- Total units: 19
- Units with |Δ| > 1: 0

No delta issues.
