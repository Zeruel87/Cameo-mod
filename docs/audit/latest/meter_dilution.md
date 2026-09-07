# audit_meter_dilution — 34 actors fire a state weapon alongside unconditional non-state weapons

| actor | guns | with state | state guns' share | dilution |
|---|--:|--:|--:|--:|
| `cabal_manticore` | 2 | 1 | 10.3% | **9.71x** |
| `cabal_manticore_backup` | 2 | 1 | 10.3% | **9.71x** |
| `cabal_hunterdronecarrier` | 3 | 1 | 10.4% | **9.60x** |
| `japan_exorcistoitank` | 5 | 3 | 10.7% | **9.33x** |
| `japan_japanesespeedboat` | 2 | 1 | 22.1% | **4.53x** |
| `cabal_hunterkillermk1` | 2 | 1 | 29.7% | **3.37x** |
| `forgotten_juggerboat` | 3 | 1 | 30.1% | **3.33x** |
| `forgotten_cannonboat` | 2 | 1 | 31.9% | **3.13x** |
| `japan_tankbuster` | 2 | 1 | 33.3% | **3.00x** |
| `td_nod_buggy` | 2 | 1 | 33.3% | **3.00x** |
| `cabal_hunterkillermk1_elite` | 2 | 1 | 43.7% | **2.29x** |
| `schwarzermond_drone` | 2 | 1 | 45.4% | **2.20x** |
| `A10Carrier` | 3 | 1 | 46.7% | **2.14x** |
| `kami_chemical.asian` | 2 | 1 | 50.4% | **1.98x** |
| `cabal_lazerboat` | 3 | 2 | 56.5% | **1.77x** |
| `terran_warhound` | 2 | 1 | 59.6% | **1.68x** |
| `forgotten_scarabapc` | 2 | 1 | 60.0% | **1.67x** |
| `terran_sundog` | 2 | 1 | 61.3% | **1.63x** |
| `terran_wraith` | 2 | 1 | 61.3% | **1.63x** |
| `forgotten_experimentalmammothtank` | 2 | 1 | 62.3% | **1.61x** |
| `A10` | 2 | 1 | 66.6% | **1.50x** |
| `wc2_humans_archmage` | 3 | 2 | 72.0% | **1.39x** |
| `wc2_humans_mage` | 3 | 2 | 72.0% | **1.39x** |
| `td_nod_buggymkii` | 9 | 7 | 73.2% | **1.37x** |
| `japan_ballistatower` | 4 | 3 | 74.7% | **1.34x** |
| `tkm_iroquois` | 2 | 1 | 75.1% | **1.33x** |
| `naxis_nokana` | 3 | 2 | 75.9% | **1.32x** |
| `protoss_idol` | 3 | 2 | 77.1% | **1.30x** |
| `td_gdi_firehawk` | 2 | 1 | 79.9% | **1.25x** |
| `tkm_trooper` | 2 | 1 | 87.5% | **1.14x** |

_(4 more — pass `--all`)_

## distribution

- 1.0-1.5x: **13**
- 1.5-2.0x: **8**
- 2.0-3.0x: **3**
- 3.0x+: **10**

## condition-gated actors the model cannot judge — 201

Every armament is gated, so no two can be shown to fire together. This is the IFV
shape, DEFERRED by maintainer ruling; it needs a variant-aware model, not a count.

FAIL 34 diluted actors (ratchet 32)
**A state carrier gained a non-feeding gun.** The fix is to make every weapon on a state unit feed the same meter, not to raise the ratchet.
