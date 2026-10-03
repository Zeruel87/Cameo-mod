# audit_meter_dilution — 34 actors fire a state weapon alongside unconditional non-state weapons

| actor | guns | with state | state guns' share | dilution |
|---|--:|--:|--:|--:|
| `japan_exorcistoitank` | 5 | 3 | 5.8% | **17.25x** |
| `japan_japanesespeedboat` | 2 | 1 | 10.4% | **9.57x** |
| `cabal_hunterdronecarrier` | 3 | 1 | 10.7% | **9.33x** |
| `cabal_manticore` | 2 | 1 | 18.6% | **5.36x** |
| `cabal_manticore_backup` | 2 | 1 | 18.6% | **5.36x** |
| `forgotten_cannonboat` | 2 | 1 | 29.4% | **3.40x** |
| `forgotten_juggerboat` | 3 | 1 | 30.0% | **3.33x** |
| `A10Carrier` | 3 | 1 | 30.8% | **3.25x** |
| `td_nod_buggy` | 2 | 1 | 33.3% | **3.00x** |
| `cabal_hunterkillermk1` | 2 | 1 | 40.9% | **2.45x** |
| `schwarzermond_drone` | 2 | 1 | 41.7% | **2.40x** |
| `A10` | 2 | 1 | 50.0% | **2.00x** |
| `asianalliance_kami_chemical` | 2 | 1 | 50.0% | **2.00x** |
| `japan_tankbuster` | 2 | 1 | 50.0% | **2.00x** |
| `terran_warhound` | 2 | 1 | 50.0% | **2.00x** |
| `cabal_lazerboat` | 3 | 2 | 56.5% | **1.77x** |
| `cabal_hunterkillermk1_elite` | 2 | 1 | 56.8% | **1.76x** |
| `forgotten_scarabapc` | 2 | 1 | 60.0% | **1.67x** |
| `tkm_iroquois` | 2 | 1 | 60.0% | **1.67x** |
| `forgotten_experimentalmammothtank` | 2 | 1 | 60.9% | **1.64x** |
| `japan_ballistatower` | 4 | 3 | 61.4% | **1.63x** |
| `naxis_nokana` | 3 | 2 | 62.3% | **1.61x** |
| `terran_sundog` | 2 | 1 | 63.0% | **1.59x** |
| `terran_wraith` | 2 | 1 | 63.0% | **1.59x** |
| `protoss_corsair` | 2 | 1 | 65.2% | **1.53x** |
| `td_gdi_firehawk` | 2 | 1 | 66.7% | **1.50x** |
| `protoss_idol` | 3 | 2 | 68.2% | **1.47x** |
| `wc2_humans_archmage` | 3 | 2 | 75.0% | **1.33x** |
| `wc2_humans_mage` | 3 | 2 | 75.0% | **1.33x** |
| `td_nod_buggymkii` | 9 | 7 | 78.3% | **1.28x** |

_(4 more — pass `--all`)_

## distribution

- 1.0-1.5x: **8**
- 1.5-2.0x: **11**
- 2.0-3.0x: **6**
- 3.0x+: **9**

## condition-gated actors the model cannot judge — 193

Every armament is gated, so no two can be shown to fire together. This is the IFV
shape, DEFERRED by maintainer ruling; it needs a variant-aware model, not a count.

FAIL 34 diluted actors (ratchet 32)
**A state carrier gained a non-feeding gun.** The fix is to make every weapon on a state unit feed the same meter, not to raise the ratchet.
