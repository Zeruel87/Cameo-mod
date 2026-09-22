# Armor projection: first worked source example

Worked source-data example, not a four-source proposal or whole-unit DPS. One CA FireballLauncher center impact on an eligible enemy surface target; no external modifiers/prone, no radius averaging. Two flat channels combined once before mapping. Linear equal class spacing is an explicit diagnostic assumption.

CA Flame Tower has two30000-damage channels. The main channel is0% against Light and8% againstHeavy; the second is50% againstLight and0% againstHeavy. Combining channels givesLight15000 andHeavy2400. Treating the first channel alone would incorrectly predict zero Light damage.

| Cameo armor position | Interpolated nominal damage |
|---|---:|
| scout | 15000 |
| light | 11850 |
| medium | 8700 |
| heavy | 5550 |
| superheavy | 2400 |

## Next implementation steps

- Current Cameo folded percentage response needs explicit target HP and full PercentageVersus maps.
- DTA selected warhead trace lacks weapon Damage and unresolved BaseSection processing.
- Apply reviewed source state, cadence, burst and secondary routing before claiming whole-unit outcomes.
- Only after all four curves have comparable bases should equal25% source means be computed. No missing source becomes a three-source average.
- Per-warhead family proposals must reconcile multiple actor results without assigning extra votes per channel.

## Current Cameo Flame Tower HP-dependent main hit

Main folded AreaDamage only; nominal center hit at unit modifiers and eligible target, no prone/status or engine integer truncation. Demonstrates HP dependence, not normalized source comparison.

| Armor | Flat | Max-HP coefficient | HP50000 | HP100000 |
|---|---:|---:|---:|---:|
| none | 36000 | 0.018 | 36900 | 37800 |
| scout | 16380 | 0.0117 | 16965 | 17550 |
| light | 16200 | 0.0108 | 16740 | 17280 |
| medium | 15660 | 0.0099 | 16155 | 16650 |
| heavy | 12240 | 0.009 | 12690 | 13140 |
| superheavy | 10260 | 0.0081 | 10665 | 11070 |
