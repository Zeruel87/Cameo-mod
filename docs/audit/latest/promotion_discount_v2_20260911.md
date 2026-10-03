# Promotion-unit discount proposal

**REVIEW ONLY.** This receipt models virtual prerequisite costs for promotion-unlocked units. It does not remove `^PromotionUnitBuff`, change costs, edit YAML or claim playtest results.

## Recommendation

- First bounded candidate: **1500 virtual credits per promotion tier**.
- Upper sensitivity case: **2000 virtual credits per promotion tier**.
- Formula-only equivalent discount for the active priced subset of `^PromotionUnitBuff`: **11.4%**.
- Promotion units evaluated: **47** across the four current factions.
- Direct `^PromotionUnitBuff` inherits in those factions: **49** actors (**40** promotion units and **9** non-promotion actors).
- Complete active include graph: **251** direct inherits; **207** are on promotion-token units and **44** are not.

The 1500-per-tier value is the accepted pilot direction. The formula response to the currently active PromotionUnitBuff traits is reported as context, not as the selection rationale; the rational curve can leave some early units on its C <= B plateau, so a virtual cost is not a guaranteed nonzero discount.

## Candidate summary

| candidate | rows | mean relative discount | median | range | plateau rows |
|---|---:|---:|---:|---:|---:|
| `fixed_5000` | 47 | 24.6% | 23.0% | 5.7%–36.4% | 0 |
| `per_tier_1000` | 47 | 13.1% | 15.5% | 0.0%–21.8% | 8 |
| `per_tier_1500` | 47 | 18.5% | 21.6% | 0.0%–29.5% | 7 |
| `per_tier_2000` | 47 | 23.6% | 26.9% | 0.0%–35.8% | 5 |

## Per-unit evidence

| faction | actor | promotion tier | C | f(C) | 1500×tier discount | 2000×tier discount |
|---|---|---:|---:|---:|---:|---:|
| ra1_allies | `ra1_allies_alliedtankdestroyer` | 3 | 13000 | 0.7021 | 27.7% | 33.8% |
| ra1_allies | `ra1_allies_alliedtigerheavytank` | 2 | 10500 | 0.8919 | 24.5% | 30.2% |
| ra1_allies | `ra1_allies_bastionartillerybunker` | 3 | 5000 | 1.0000 | 0.0% | 15.4% |
| ra1_allies | `ra1_allies_camopillbox` | 1 | 5000 | 1.0000 | 0.0% | 0.0% |
| ra1_allies | `ra1_allies_chronotank` | 4 | 18000 | 0.4925 | 26.4% | 32.3% |
| ra1_allies | `ra1_allies_gapgenerator` | 4 | 16000 | 0.5593 | 28.9% | 35.2% |
| ra1_allies | `ra1_allies_machinegunner` | 1 | 6500 | 1.0000 | 0.0% | 0.0% |
| ra1_allies | `ra1_allies_mobilegapgenerator` | 4 | 18000 | 0.4925 | 26.4% | 32.3% |
| ra1_allies | `ra1_allies_mobileradarjammer` | 4 | 18000 | 0.4925 | 26.4% | 32.3% |
| ra1_allies | `ra1_allies_phasetransport` | 2 | 18000 | 0.4925 | 15.2% | 19.3% |
| ra1_allies | `ra1_allies_rapierjumpjet` | 3 | 17500 | 0.5077 | 21.7% | 27.0% |
| ra1_allies | `ra1_allies_reconranger` | 1 | 10500 | 0.8919 | 14.0% | 17.8% |
| ra1_allies | `ra1_allies_reinforcementpad` | 4 | 16000 | 0.5593 | 28.9% | 35.2% |
| ra1_allies | `ra1_allies_sheridanassaulttank` | 2 | 10500 | 0.8919 | 24.5% | 30.2% |
| ra1_soviets | `ra1_soviets_cyberdog` | 3 | 6500 | 1.0000 | 15.4% | 26.7% |
| ra1_soviets | `ra1_soviets_gatlingtank` | 1 | 10500 | 0.8919 | 14.0% | 17.8% |
| ra1_soviets | `ra1_soviets_monstertank` | 4 | 18000 | 0.4925 | 26.4% | 32.3% |
| ra1_soviets | `ra1_soviets_mortarsoldier` | 2 | 12000 | 0.7674 | 21.8% | 27.1% |
| ra1_soviets | `ra1_soviets_supersonicnuclearbomber` | 4 | 17500 | 0.5077 | 27.0% | 33.0% |
| ra1_soviets | `ra1_soviets_volkov` | 4 | 17000 | 0.5238 | 27.6% | 33.7% |
| td_gdi | `td_gdi_assaultapc` | 4 | 23000 | 0.3793 | 21.6% | 26.9% |
| td_gdi | `td_gdi_defenserig` | 4 | 23000 | 0.3793 | 21.6% | 26.9% |
| td_gdi | `td_gdi_empgrenadier` | 1 | 6500 | 1.0000 | 0.0% | 0.0% |
| td_gdi | `td_gdi_exosuit` | 3 | 23000 | 0.3793 | 17.1% | 21.6% |
| td_gdi | `td_gdi_firehawk` | 4 | 22500 | 0.3882 | 22.0% | 27.4% |
| td_gdi | `td_gdi_havoc` | 3 | 22000 | 0.3976 | 17.8% | 22.4% |
| td_gdi | `td_gdi_heavysniper` | 3 | 12000 | 0.7674 | 29.5% | 35.8% |
| td_gdi | `td_gdi_humveemkii` | 1 | 10500 | 0.8919 | 14.0% | 17.8% |
| td_gdi | `td_gdi_mammothtankmkiii` | 3 | 23000 | 0.3793 | 17.1% | 21.6% |
| td_gdi | `td_gdi_officer` | 2 | 12000 | 0.7674 | 21.8% | 27.1% |
| td_gdi | `td_gdi_predatortank` | 2 | 10500 | 0.8919 | 24.5% | 30.2% |
| td_gdi | `td_gdi_shotgunner` | 1 | 6500 | 1.0000 | 0.0% | 0.0% |
| td_gdi | `td_gdi_sonicmissilesoldier` | 2 | 6500 | 1.0000 | 0.0% | 10.8% |
| td_nod | `td_nod_blackhandflamer` | 1 | 12000 | 0.7674 | 12.2% | 15.7% |
| td_nod | `td_nod_buggymkii` | 1 | 10000 | 0.9429 | 14.6% | 18.6% |
| td_nod | `td_nod_chemicalattackbike` | 2 | 10000 | 0.9429 | 25.5% | 31.4% |
| td_nod | `td_nod_chemicalrocketsoldier` | 1 | 6500 | 1.0000 | 0.0% | 0.0% |
| td_nod | `td_nod_chemicalssmlauncher` | 4 | 27500 | 0.3143 | 18.6% | 23.4% |
| td_nod | `td_nod_chemicalstealthtank` | 3 | 22500 | 0.3882 | 17.5% | 22.0% |
| td_nod | `td_nod_flametankmkii` | 3 | 12500 | 0.7333 | 28.6% | 34.8% |
| td_nod | `td_nod_lasercommando` | 4 | 27000 | 0.3204 | 18.9% | 23.7% |
| td_nod | `td_nod_lasertrooper` | 4 | 27000 | 0.3204 | 18.9% | 23.7% |
| td_nod | `td_nod_lighttankmkii` | 2 | 10000 | 0.9429 | 25.5% | 31.4% |
| td_nod | `td_nod_specterartillery` | 3 | 12500 | 0.7333 | 28.6% | 34.8% |
| td_nod | `td_nod_stealthharvester` | 2 | 10000 | 0.9429 | 25.5% | 31.4% |
| td_nod | `td_nod_stealthsoldier` | 2 | 22000 | 0.3976 | 12.6% | 16.2% |
| td_nod | `td_nod_venom` | 4 | 27500 | 0.3143 | 18.6% | 23.4% |

## Guardrails

- This is a proposal for the next playtest, not permission to remove promotion inherits or rewrite costs.
- The rational tier curve has a C <= B plateau; virtual credits below that boundary produce no discount. Do not force a discount by changing B or S.
- Promotion superiority, prerequisite-column tier correctness, upgrade interactions and the Sunday no-upgrade scope remain separate checks.
- Seven promotion-gated units in this scan have no direct `^PromotionUnitBuff` inherit; do not treat every promotion unit as a removal target. The nine non-promotion direct inherits need a separate disposition.
- Active vision, detection and inaccuracy modifiers are disclosed in the JSON profile but are not assigned a value by the current price formula.
