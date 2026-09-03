# audit_meter_dilution — 32 actors fire a state weapon alongside unconditional non-state weapons

| actor | guns | with state | state guns' share | dilution |
|---|--:|--:|--:|--:|
| `japan_exorcistoitank` | 5 | 3 | 6.2% | **16.12x** |
| `cabal_hunterdronecarrier` | 3 | 1 | 10.4% | **9.60x** |
| `cabal_manticore` | 2 | 1 | 18.7% | **5.35x** |
| `cabal_manticore_backup` | 2 | 1 | 18.7% | **5.35x** |
| `forgotten_cannonboat` | 2 | 1 | 29.5% | **3.39x** |
| `protoss_idol` | 3 | 1 | 29.7% | **3.37x** |
| `forgotten_juggerboat` | 3 | 1 | 30.1% | **3.33x** |
| `A10Carrier` | 3 | 1 | 30.5% | **3.28x** |
| `td_nod_buggy` | 2 | 1 | 33.3% | **3.00x** |
| `japan_tankbuster` | 2 | 1 | 49.9% | **2.00x** |
| `A10` | 2 | 1 | 49.9% | **2.00x** |
| `terran_warhound` | 2 | 1 | 50.1% | **2.00x** |
| `kami_chemical.asian` | 2 | 1 | 50.8% | **1.97x** |
| `cabal_lazerboat` | 3 | 2 | 56.5% | **1.77x** |
| `forgotten_scarabapc` | 2 | 1 | 60.0% | **1.67x** |
| `forgotten_experimentalmammothtank` | 2 | 1 | 60.9% | **1.64x** |
| `terran_sundog` | 2 | 1 | 61.3% | **1.63x** |
| `terran_wraith` | 2 | 1 | 61.3% | **1.63x** |
| `naxis_nokana` | 3 | 2 | 62.2% | **1.61x** |
| `cruiser_f.steel` | 2 | 1 | 63.3% | **1.58x** |
| `japan_ballistatower` | 4 | 3 | 63.3% | **1.58x** |
| `td_gdi_firehawk` | 2 | 1 | 66.5% | **1.50x** |
| `ordos_banshee` | 2 | 1 | 68.2% | **1.47x** |
| `ordos_laboratorycrawler` | 2 | 1 | 68.2% | **1.47x** |
| `wc2_humans_archmage` | 3 | 2 | 72.0% | **1.39x** |
| `wc2_humans_mage` | 3 | 2 | 72.0% | **1.39x** |
| `td_nod_buggymkii` | 9 | 7 | 78.2% | **1.28x** |
| `tkm_trooper` | 2 | 1 | 85.7% | **1.17x** |
| `ts_gdi_kodiakcommandship` | 2 | 1 | 87.3% | **1.15x** |
| `nodlasercorvette` | 2 | 1 | 92.2% | **1.08x** |

_(2 more — pass `--all`)_

## distribution

- 1.0-1.5x: **10**
- 1.5-2.0x: **11**
- 2.0-3.0x: **2**
- 3.0x+: **9**

## condition-gated actors the model cannot judge — 175

Every armament is gated, so no two can be shown to fire together. This is the IFV
shape, DEFERRED by maintainer ruling; it needs a variant-aware model, not a count.

WARN 32 diluted actors (ratchet 32)
Lower `DILUTION_BASELINE` as carriers are reworked; never raise it.
