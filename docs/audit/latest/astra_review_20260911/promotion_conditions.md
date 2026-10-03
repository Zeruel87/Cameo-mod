# Promotion and upgrade interaction inventory

**REVIEW ONLY.** This receipt inventories condition sources and stat hooks for the current promotion cohort. It does not certify a factory-ready state, remove `^PromotionUnitBuff`, change prices or claim upgrade balance.

## Summary

- Promotion units: **47**; direct `^PromotionUnitBuff`: **40**; without the direct inherit: **7**.
- Promotion prerequisite hooks: **2**; current-faction upgrade/doctrine hooks: **197**.
- Conditional stat traits: **6399**; upgrade/doctrine-conditioned traits: **510**; traits with at least one unresolved identifier: **208**.
- Individually unresolved identifier occurrences: **232** across **16** names. Numeric comparison literals are excluded.
- Conditions are wiring evidence only. Prerequisite upgrades, ranks, external/runtime states and unknown sources remain separate; mixed expressions retain every unresolved identifier.

## Per-unit inventory

| faction | actor | direct buff | promotion hooks | upgrade hooks | upgrade-conditioned stat traits | traits with unknown identifiers | unknown identifiers |
|---|---|:---:|---:|---:|---:|---:|---:|
| `ra1_allies` | `ra1_allies_alliedtankdestroyer` | yes | 0 | 4 | 11 | 6 | 7 |
| `ra1_allies` | `ra1_allies_alliedtigerheavytank` | yes | 0 | 4 | 11 | 6 | 7 |
| `ra1_allies` | `ra1_allies_bastionartillerybunker` | no | 0 | 5 | 13 | 0 | 0 |
| `ra1_allies` | `ra1_allies_camopillbox` | no | 0 | 4 | 12 | 0 | 0 |
| `ra1_allies` | `ra1_allies_chronotank` | yes | 0 | 5 | 12 | 6 | 7 |
| `ra1_allies` | `ra1_allies_gapgenerator` | no | 0 | 1 | 1 | 1 | 1 |
| `ra1_allies` | `ra1_allies_machinegunner` | yes | 0 | 4 | 13 | 5 | 5 |
| `ra1_allies` | `ra1_allies_mobilegapgenerator` | no | 0 | 1 | 0 | 7 | 8 |
| `ra1_allies` | `ra1_allies_mobileradarjammer` | no | 0 | 1 | 0 | 7 | 8 |
| `ra1_allies` | `ra1_allies_phasetransport` | yes | 0 | 5 | 12 | 6 | 7 |
| `ra1_allies` | `ra1_allies_rapierjumpjet` | yes | 0 | 5 | 20 | 4 | 4 |
| `ra1_allies` | `ra1_allies_reconranger` | yes | 0 | 4 | 12 | 3 | 4 |
| `ra1_allies` | `ra1_allies_reinforcementpad` | no | 0 | 1 | 1 | 0 | 0 |
| `ra1_allies` | `ra1_allies_sheridanassaulttank` | yes | 0 | 5 | 12 | 6 | 7 |
| `ra1_soviets` | `ra1_soviets_cyberdog` | yes | 0 | 6 | 7 | 8 | 8 |
| `ra1_soviets` | `ra1_soviets_gatlingtank` | yes | 0 | 8 | 7 | 12 | 13 |
| `ra1_soviets` | `ra1_soviets_monstertank` | yes | 0 | 12 | 11 | 3 | 4 |
| `ra1_soviets` | `ra1_soviets_mortarsoldier` | yes | 1 | 4 | 5 | 5 | 5 |
| `ra1_soviets` | `ra1_soviets_supersonicnuclearbomber` | yes | 0 | 4 | 7 | 4 | 4 |
| `ra1_soviets` | `ra1_soviets_volkov` | yes | 1 | 7 | 5 | 5 | 5 |
| `td_gdi` | `td_gdi_assaultapc` | yes | 0 | 4 | 11 | 3 | 4 |
| `td_gdi` | `td_gdi_defenserig` | yes | 0 | 6 | 15 | 5 | 6 |
| `td_gdi` | `td_gdi_empgrenadier` | yes | 0 | 2 | 8 | 5 | 5 |
| `td_gdi` | `td_gdi_exosuit` | yes | 0 | 4 | 12 | 3 | 4 |
| `td_gdi` | `td_gdi_firehawk` | yes | 0 | 5 | 10 | 4 | 4 |
| `td_gdi` | `td_gdi_havoc` | yes | 0 | 4 | 11 | 5 | 5 |
| `td_gdi` | `td_gdi_heavysniper` | yes | 0 | 3 | 9 | 5 | 5 |
| `td_gdi` | `td_gdi_humveemkii` | yes | 0 | 5 | 13 | 3 | 4 |
| `td_gdi` | `td_gdi_mammothtankmkiii` | yes | 0 | 5 | 14 | 3 | 4 |
| `td_gdi` | `td_gdi_officer` | yes | 0 | 3 | 9 | 13 | 13 |
| `td_gdi` | `td_gdi_predatortank` | yes | 0 | 5 | 12 | 3 | 4 |
| `td_gdi` | `td_gdi_shotgunner` | yes | 0 | 3 | 9 | 5 | 5 |
| `td_gdi` | `td_gdi_sonicmissilesoldier` | yes | 0 | 3 | 10 | 5 | 5 |
| `td_nod` | `td_nod_blackhandflamer` | yes | 0 | 5 | 17 | 5 | 5 |
| `td_nod` | `td_nod_buggymkii` | yes | 0 | 4 | 10 | 3 | 4 |
| `td_nod` | `td_nod_chemicalattackbike` | yes | 0 | 4 | 12 | 3 | 4 |
| `td_nod` | `td_nod_chemicalrocketsoldier` | yes | 0 | 5 | 17 | 5 | 5 |
| `td_nod` | `td_nod_chemicalssmlauncher` | yes | 0 | 2 | 5 | 3 | 4 |
| `td_nod` | `td_nod_chemicalstealthtank` | yes | 0 | 3 | 12 | 3 | 4 |
| `td_nod` | `td_nod_flametankmkii` | yes | 0 | 3 | 12 | 3 | 4 |
| `td_nod` | `td_nod_lasercommando` | yes | 0 | 5 | 20 | 5 | 5 |
| `td_nod` | `td_nod_lasertrooper` | yes | 0 | 5 | 20 | 5 | 5 |
| `td_nod` | `td_nod_lighttankmkii` | yes | 0 | 5 | 17 | 3 | 4 |
| `td_nod` | `td_nod_specterartillery` | yes | 0 | 4 | 13 | 3 | 4 |
| `td_nod` | `td_nod_stealthharvester` | no | 0 | 2 | 10 | 4 | 5 |
| `td_nod` | `td_nod_stealthsoldier` | yes | 0 | 4 | 15 | 5 | 5 |
| `td_nod` | `td_nod_venom` | yes | 0 | 4 | 15 | 2 | 2 |

## Guardrails

- This inventory does not prove that a condition is active in a particular match; it reports authored wiring and condition references.
- Unknown identifiers are unresolved evidence items, not implementation blockers or proof of broken gameplay.
- Promotion-unit direct-buff counts are separate from the nine non-promotion direct inherits recorded by the discount receipt.
- Upgrade valuation, status uptime, and runtime interactions remain deferred until the base/factory-ready candidate is stable.
