# Four equal voices: defense armor-shape comparison

- Each of the four sources has25% weight. Current Cameo is read live, not the frozen self-vote snapshot.
- These are the MAIN-channel None/Heavy and Wood/Heavy ratios discussed in the original message; extra/split channels do not get additional votes.
- Normalize each source to its own Heavy coefficient before averaging. Raw percentage scales differ between games; averaging raw multipliers would mix scale and shape.
- Arithmetic mean=(a+b+c+d)/4. Geometric mean=(a*b*c*d)^(1/4); it treats reciprocal ratio changes symmetrically and is less pulled by the10x/11.25x values.
- The candidate coefficient columns keep current Cameo Heavy fixed and rescale only the shown axes; they are unrounded review examples, not a complete profile or approved gameplay patch.
- DTA medium is not silently mapped to Light. Missing DTA Concrete and other unmatched armor axes are not replaced with defaults or reweighted three-source votes.
- DTA preprocessing and source conditions remain limitations. CA Flame Tower second channel adds no None/Heavy/Wood damage, so it does not change these ratios.

| Main channel | Cameo ratio | CA | DTA | OpenRA | Arithmetic | Geometric |
|---|---:|---:|---:|---:|---:|---:|
| ra1_soviets_flametower | 2.941176 | 11.250000 | 3.600000 | 3.600000 | 5.347794 | 4.550610 |
| ra1_soviets_teslacoil | 0.666667 | 10.000000 | 1.000000 | 10.000000 | 5.416667 | 2.857440 |
| td_nod_obeliskoflight | 0.564516 | 2.475248 | 1.000000 | 1.000000 | 1.259941 | 1.087236 |

## Example coefficients with current Heavy unchanged

| Actor | Heavy fixed | None arithmetic | None geometric | Wood arithmetic | Wood geometric |
|---|---:|---:|---:|---:|---:|
| ra1_soviets_flametower | 68.000 | 363.650 | 309.442 | 202.500 | 196.608 |
| ra1_soviets_teslacoil | 135.000 | 731.250 | 385.754 | 94.750 | 92.317 |
| td_nod_obeliskoflight | 124.000 | 156.233 | 134.817 | 83.666 | 80.729 |
