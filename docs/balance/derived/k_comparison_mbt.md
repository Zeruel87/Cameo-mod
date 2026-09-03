# W11 — K comparison for class `mbt`

Anchor `tiger.nax`, cost0 800. Every member priced twice: on RAW
damage/reload, and on K-adjusted `effective_dps` from the derived sidecar
(accuracy, spread, falloff, range, dead zone, reachable targets).

The anchor is re-fitted in each mode, so each column is internally
consistent; only the SHAPE of the class changes between them.

| estimator | raw | K |
|---|---|---|
| O0 | 800.00 | 785.32 |
| P0 | 800.00 | 770.64 |
| Q0 | 800.00 | 741.28 |

| unit | cost | raw price | K price | raw Δ | K Δ | K vs raw |
|---|---|---|---|---|---|---|
| `tkm_trenchtank` | 2500 | 1494 | 2313 | -40% | -7% | +55% ❗ |
| `steelconsortium_quantumtank` | 1600 | 1294 | 805 | -19% | -50% | -38% ❗ |
| `steelconsortium_mako` | 900 | 974 | 610 | +8% | -32% | -37% ❗ |
| `ixian_mongoose` | 1300 | 1300 | 893 | +0% | -31% | -31% ❗ |
| `protoss_dragoon` | 1200 | 1150 | 793 | -4% | -34% | -31% ❗ |
| `td_gdi_predatortank` | 1250 | 1292 | 892 | +3% | -29% | -31% ❗ |
| `cabal_widow` | 3500 | 9052 | 11829 | +159% | +238% | +31% ❗ |
| `ordos_combatautoguntank` | 1500 | 892 | 624 | -41% | -58% | -30% ⚠ |
| `td_gdi_battletank` | 900 | 928 | 657 | +3% | -27% | -29% ⚠ |
| `ptnk.asian` | 2400 | 1842 | 2341 | -23% | -2% | +27% ⚠ |
| `ixian_heavykodatank` | 1100 | 1037 | 780 | -6% | -29% | -25% ⚠ |
| `ixian_kodatank` | 800 | 713 | 545 | -11% | -32% | -24% ⚠ |
| `oldqtnk.steel` | 2400 | 3180 | 2666 | +33% | +11% | -16% ⚠ |
| `latinsyndicate_smokertank` | 1800 | 1832 | 1580 | +2% | -12% | -14% ⚠ |
| `assault.nax` | 900 | 4036 | 4518 | +348% | +402% | +12% ⚠ |
| `schwarzermond_lunartiger` | 950 | 770 | 861 | -19% | -9% | +12% ⚠ |
| `combat_tank.atreides` | 600 | 836 | 763 | +39% | +27% | -9% |
| `ra1_soviets_hammertank` | 1500 | 1651 | 1791 | +10% | +19% | +9% |
| `ts_gdi_titanmkii` | 1600 | 1604 | 1728 | +0% | +8% | +8% |
| `tkm_t72m` | 900 | 989 | 1064 | +10% | +18% | +8% |
| `ra1_soviets_kotinnucleartank` | 1800 | 1809 | 1945 | +1% | +8% | +8% |
| `futuretech_guardiantank` | 850 | 734 | 785 | -14% | -8% | +7% |
| `ts_gdi_titan` | 950 | 954 | 1019 | +0% | +7% | +7% |
| `combat_tank.harkonnen` | 600 | 408 | 382 | -32% | -36% | -6% |
| `asianalliance_lynxtank` | 850 | 1033 | 972 | +22% | +14% | -6% |
| `ra1_allies_alliedcybertank` | 1300 | 1499 | 1583 | +15% | +22% | +6% |
| `ra1_allies_alliedtigerheavytank` | 1300 | 1499 | 1583 | +15% | +22% | +6% |
| `japan_chihaheavytank` | 1200 | 834 | 873 | -31% | -27% | +5% |
| `ordos_heavycombattank` | 950 | 950 | 911 | +0% | -4% | -4% |
| `cabal_tarantula` | 1000 | 1000 | 962 | -0% | -4% | -4% |
| `ra1_soviets_heavytank` | 1000 | 1183 | 1195 | +18% | +20% | +1% |
| `japan_igomediumtank` | 800 | 800 | 805 | -0% | +1% | +1% |
| `ra2_soviets_rhinoheavytank` | 850 | 926 | 931 | +9% | +10% | +1% |
| `ra1_allies_alliedmediumtank` | 700 | 875 | 879 | +25% | +26% | +0% |
| `tkm_technicaltank` | 700 | 631 | 634 | -10% | -9% | +0% |
| `tkm_abrams` | 1000 | 708 | 711 | -29% | -29% | +0% |
| `ra2_allies_grizzlytank` | 750 | 1004 | 1007 | +34% | +34% | +0% |
| `naxis_kingtigerheavytank` | 2000 | 2000 | 1998 | +0% | -0% | -0% |
| `forgotten_rattytank` | 600 | 636 | 636 | +6% | +6% | +0% |
| `tiger.nax` | 800 | 800 | 800 | +0% | +0% | +0% |

## What the switch would do

- **40 units** priced both ways.
- Median price shift: **+0.4%**; range **-37.8% … +54.8%**.
- Moves AWAY from the current cost for **29/40** units, towards it for **11**.

A K switch is worth taking when it moves prices TOWARDS current costs for
units the maintainer already considers correctly priced — that is evidence
the coefficient is capturing something real rather than adding noise.
It is not a target to optimise: a weapon that genuinely is inaccurate
SHOULD price below its raw damage.

