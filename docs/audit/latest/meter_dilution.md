# audit_meter_dilution — 32 actors fire a state weapon alongside unconditional non-state weapons

| actor | guns | with state | state guns' share | dilution |
|---|--:|--:|--:|--:|
| `japan_exorcistoitank` | 5 | 3 | 6.2% | **16.12x** |
| `cabal_hunterdronecarrier` | 3 | 1 | 10.4% | **9.60x** |
| `japan_japanesespeedboat` | 2 | 1 | 10.5% | **9.56x** |
| `cabal_manticore` | 2 | 1 | 18.7% | **5.35x** |
| `cabal_manticore_backup` | 2 | 1 | 18.7% | **5.35x** |
| `forgotten_cannonboat` | 2 | 1 | 29.5% | **3.39x** |
| `forgotten_juggerboat` | 3 | 1 | 30.1% | **3.33x** |
| `A10Carrier` | 3 | 1 | 30.5% | **3.28x** |
| `td_nod_buggy` | 2 | 1 | 33.3% | **3.00x** |
| `cabal_hunterkillermk1` | 2 | 1 | 41.0% | **2.44x** |
| `schwarzermond_drone` | 2 | 1 | 41.6% | **2.40x** |
| `japan_tankbuster` | 2 | 1 | 49.9% | **2.00x** |
| `A10` | 2 | 1 | 49.9% | **2.00x** |
| `terran_warhound` | 2 | 1 | 50.1% | **2.00x** |
| `kami_chemical.asian` | 2 | 1 | 50.8% | **1.97x** |
| `cabal_lazerboat` | 3 | 2 | 56.5% | **1.77x** |
| `cabal_hunterkillermk1_elite` | 2 | 1 | 56.8% | **1.76x** |
| `forgotten_scarabapc` | 2 | 1 | 60.0% | **1.67x** |
| `tkm_iroquois` | 2 | 1 | 60.4% | **1.65x** |
| `forgotten_experimentalmammothtank` | 2 | 1 | 60.9% | **1.64x** |
| `terran_sundog` | 2 | 1 | 61.3% | **1.63x** |
| `terran_wraith` | 2 | 1 | 61.3% | **1.63x** |
| `naxis_nokana` | 3 | 2 | 62.2% | **1.61x** |
| `japan_ballistatower` | 4 | 3 | 63.3% | **1.58x** |
| `td_gdi_firehawk` | 2 | 1 | 66.5% | **1.50x** |
| `protoss_idol` | 3 | 2 | 68.6% | **1.46x** |
| `wc2_humans_archmage` | 3 | 2 | 72.0% | **1.39x** |
| `wc2_humans_mage` | 3 | 2 | 72.0% | **1.39x** |
| `td_nod_buggymkii` | 9 | 7 | 78.2% | **1.28x** |
| `tkm_trooper` | 2 | 1 | 85.7% | **1.17x** |

_(2 more — pass `--all`)_

## distribution

- 1.0-1.5x: **7**
- 1.5-2.0x: **12**
- 2.0-3.0x: **4**
- 3.0x+: **9**

## condition-gated actors the model cannot judge — 190

Every armament is gated, so no two can be shown to fire together. This is the IFV
shape, DEFERRED by maintainer ruling; it needs a variant-aware model, not a count.

WARN 32 diluted actors (ratchet 32)
Lower `DILUTION_BASELINE` as carriers are reworked; never raise it.
