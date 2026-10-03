# Promotion and upgrade interaction inventory

**REVIEW ONLY.** This receipt inventories resolved condition and stat hooks for the current promotion cohort. It does not remove `^PromotionUnitBuff`, change prices or claim upgrade balance.

## Summary

- Promotion units: **47**; direct `^PromotionUnitBuff`: **40**; without the direct inherit: **7**.
- Promotion prerequisite hooks: **2**; current-faction upgrade/doctrine hooks: **197**.
- Conditional stat traits: **6399**; upgrade/doctrine-conditioned traits: **510**; unresolved condition sources: **4437**.
- Conditions are listed as wiring evidence only. The fresh Sunday comparison keeps upgrade-conditioned effects out of the promotion superiority result.

## Per-unit inventory

| faction | actor | direct buff | promotion hooks | upgrade hooks | upgrade-conditioned stat traits | unresolved stat traits |
|---|---|:---:|---:|---:|---:|---:|
| `ra1_allies` | `ra1_allies_alliedtankdestroyer` | yes | 0 | 4 | 11 | 107 |
| `ra1_allies` | `ra1_allies_alliedtigerheavytank` | yes | 0 | 4 | 11 | 107 |
| `ra1_allies` | `ra1_allies_bastionartillerybunker` | no | 0 | 5 | 13 | 54 |
| `ra1_allies` | `ra1_allies_camopillbox` | no | 0 | 4 | 12 | 54 |
| `ra1_allies` | `ra1_allies_chronotank` | yes | 0 | 5 | 12 | 107 |
| `ra1_allies` | `ra1_allies_gapgenerator` | no | 0 | 1 | 1 | 54 |
| `ra1_allies` | `ra1_allies_machinegunner` | yes | 0 | 4 | 13 | 98 |
| `ra1_allies` | `ra1_allies_mobilegapgenerator` | no | 0 | 1 | 0 | 71 |
| `ra1_allies` | `ra1_allies_mobileradarjammer` | no | 0 | 1 | 0 | 71 |
| `ra1_allies` | `ra1_allies_phasetransport` | yes | 0 | 5 | 12 | 107 |
| `ra1_allies` | `ra1_allies_rapierjumpjet` | yes | 0 | 5 | 20 | 81 |
| `ra1_allies` | `ra1_allies_reconranger` | yes | 0 | 4 | 12 | 107 |
| `ra1_allies` | `ra1_allies_reinforcementpad` | no | 0 | 1 | 1 | 23 |
| `ra1_allies` | `ra1_allies_sheridanassaulttank` | yes | 0 | 5 | 12 | 107 |
| `ra1_soviets` | `ra1_soviets_cyberdog` | yes | 0 | 6 | 7 | 96 |
| `ra1_soviets` | `ra1_soviets_gatlingtank` | yes | 0 | 8 | 7 | 113 |
| `ra1_soviets` | `ra1_soviets_monstertank` | yes | 0 | 12 | 11 | 104 |
| `ra1_soviets` | `ra1_soviets_mortarsoldier` | yes | 1 | 4 | 5 | 98 |
| `ra1_soviets` | `ra1_soviets_supersonicnuclearbomber` | yes | 0 | 4 | 7 | 81 |
| `ra1_soviets` | `ra1_soviets_volkov` | yes | 1 | 7 | 5 | 98 |
| `td_gdi` | `td_gdi_assaultapc` | yes | 0 | 4 | 11 | 104 |
| `td_gdi` | `td_gdi_defenserig` | yes | 0 | 6 | 15 | 106 |
| `td_gdi` | `td_gdi_empgrenadier` | yes | 0 | 2 | 8 | 98 |
| `td_gdi` | `td_gdi_exosuit` | yes | 0 | 4 | 12 | 104 |
| `td_gdi` | `td_gdi_firehawk` | yes | 0 | 5 | 10 | 81 |
| `td_gdi` | `td_gdi_havoc` | yes | 0 | 4 | 11 | 98 |
| `td_gdi` | `td_gdi_heavysniper` | yes | 0 | 3 | 9 | 98 |
| `td_gdi` | `td_gdi_humveemkii` | yes | 0 | 5 | 13 | 104 |
| `td_gdi` | `td_gdi_mammothtankmkiii` | yes | 0 | 5 | 14 | 104 |
| `td_gdi` | `td_gdi_officer` | yes | 0 | 3 | 9 | 98 |
| `td_gdi` | `td_gdi_predatortank` | yes | 0 | 5 | 12 | 104 |
| `td_gdi` | `td_gdi_shotgunner` | yes | 0 | 3 | 9 | 98 |
| `td_gdi` | `td_gdi_sonicmissilesoldier` | yes | 0 | 3 | 10 | 98 |
| `td_nod` | `td_nod_blackhandflamer` | yes | 0 | 5 | 17 | 98 |
| `td_nod` | `td_nod_buggymkii` | yes | 0 | 4 | 10 | 104 |
| `td_nod` | `td_nod_chemicalattackbike` | yes | 0 | 4 | 12 | 104 |
| `td_nod` | `td_nod_chemicalrocketsoldier` | yes | 0 | 5 | 17 | 99 |
| `td_nod` | `td_nod_chemicalssmlauncher` | yes | 0 | 2 | 5 | 104 |
| `td_nod` | `td_nod_chemicalstealthtank` | yes | 0 | 3 | 12 | 104 |
| `td_nod` | `td_nod_flametankmkii` | yes | 0 | 3 | 12 | 104 |
| `td_nod` | `td_nod_lasercommando` | yes | 0 | 5 | 20 | 98 |
| `td_nod` | `td_nod_lasertrooper` | yes | 0 | 5 | 20 | 99 |
| `td_nod` | `td_nod_lighttankmkii` | yes | 0 | 5 | 17 | 104 |
| `td_nod` | `td_nod_specterartillery` | yes | 0 | 4 | 13 | 104 |
| `td_nod` | `td_nod_stealthharvester` | no | 0 | 2 | 10 | 105 |
| `td_nod` | `td_nod_stealthsoldier` | yes | 0 | 4 | 15 | 98 |
| `td_nod` | `td_nod_venom` | yes | 0 | 4 | 15 | 79 |

## Guardrails

- This inventory does not prove that a condition is active in a particular match; it reports authored prerequisite wiring and resolved trait references.
- Promotion-unit direct-buff counts are separate from the nine non-promotion direct inherits recorded by the discount receipt.
- Upgrade valuation, status uptime, and runtime interactions remain deferred until the base/factory-ready candidate is stable.
