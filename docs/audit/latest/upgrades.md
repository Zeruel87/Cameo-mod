# audit_upgrades — inverted / dead upgrade effects (B3)

Upgrade items found: **626** — inverted-direction traits: **0**, exact deferred traits: **1**, dead upgrades: **10**, dead wiring tokens: **20**, without intent entries: **1**


## Inverted-direction stat traits gated on upgrade conditions

_none found_


## Exact deferred inverted traits (pricing-linked review boundary)

| upgrade | affected actor | trait | value | beneficial means | note |
|---|---|---|---|---|---|
| steelconsortium_upgrade_pulseweapons | steelconsortium_clonetrooper | FirepowerMultiplier@steelconsortium_upgrade_pulseweapons | 91 | >=100 = not weaker | declared drawback? |


## Dead upgrades (granted tokens nobody consumes)

| upgrade | extra tokens | file |
|---|---|---|
| atreides_upgrade_conyard | (own name only) | mods/cameo/ContentPacks/D2k/Atreides/yaml/upgrades.yaml |
| atreides_upgrade_radar | (own name only) | mods/cameo/ContentPacks/D2k/Atreides/yaml/upgrades.yaml |
| corrino_upgrade_barracks | (own name only) | mods/cameo/ContentPacks/D2k/Corrino/yaml/upgrades.yaml |
| corrino_upgrade_conyard | (own name only) | mods/cameo/ContentPacks/D2k/Corrino/yaml/upgrades.yaml |
| corrino_upgrade_radar | (own name only) | mods/cameo/ContentPacks/D2k/Corrino/yaml/upgrades.yaml |
| harkonnen_upgrade_barracks | (own name only) | mods/cameo/ContentPacks/D2k/Harkonnen/yaml/upgrades.yaml |
| harkonnen_upgrade_conyard | (own name only) | mods/cameo/ContentPacks/D2k/Harkonnen/yaml/upgrades.yaml |
| harkonnen_upgrade_heavy | (own name only) | mods/cameo/ContentPacks/D2k/Harkonnen/yaml/upgrades.yaml |
| harkonnen_upgrade_light | (own name only) | mods/cameo/ContentPacks/D2k/Harkonnen/yaml/upgrades.yaml |
| harkonnen_upgrade_radar | (own name only) | mods/cameo/ContentPacks/D2k/Harkonnen/yaml/upgrades.yaml |


## Dead wiring (GrantConditionOnPrerequisite tokens granted by nothing)

| token | #consumer traits | sample consumers |
|---|---|---|
| base-reveal | 1735 | a10, a10carrier, asianalliance_advancedcommunicationcenter, asianalliance_airforcecommand |
| classicproductionqueues | 173 | asianalliance_airforcecommand, asianalliance_barracks, asianalliance_cgyard, asianalliance_constructionyard |
| derricklimit_is_0 | 1 | player |
| derricklimit_is_3 | 1 | player |
| derricklimit_is_infinite | 1 | player |
| hybridproductionqueues | 173 | asianalliance_airforcecommand, asianalliance_barracks, asianalliance_cgyard, asianalliance_constructionyard |
| littlebuilderenable | 173 | asianalliance_airforcecommand, asianalliance_barracks, asianalliance_cgyard, asianalliance_constructionyard |
| palace_emperor | 27 | atreides_engineer, atreides_fremen, atreides_lightinfantry, atreides_rockettrooper |
| scaledprices | 114 | asianalliance_airforcecommand, asianalliance_barracks, asianalliance_cgyard, asianalliance_warfactory |
| scaledproductionqueues | 114 | asianalliance_airforcecommand, asianalliance_barracks, asianalliance_cgyard, asianalliance_warfactory |
| stardecoration | 2 | corrino_barracks, corrino_lightfactory |
| upemptesla | 3 | ra2_soviets_teslatrooper, ra2shk.bot, ra2shkhero |
| upra2deso | 358 | asianalliance_alligator, asianalliance_asdf, asianalliance_commando, asianalliance_engineer |
| upsubliminal | 1205 | a10, a10carrier, asianalliance_alligator, asianalliance_asdf |
| upsubliminal2 | 1205 | a10, a10carrier, asianalliance_alligator, asianalliance_asdf |
| usabombardament | 1205 | a10, a10carrier, asianalliance_alligator, asianalliance_asdf |
| usaholdtheline | 1205 | a10, a10carrier, asianalliance_alligator, asianalliance_asdf |
| usasearchndestroy | 1205 | a10, a10carrier, asianalliance_alligator, asianalliance_asdf |
| usaupcounter | 2 | ra1_allies_chinooktransport, ra1_soviets_hiptransport |
| usaupsupplylines | 34 | asianalliance_militaryacademy, cabal_core, d2k_spicesifter, forgotten_tiberiumspike |


## Upgrades without an upgrades_intent.yaml entry

scrin_upgrade_fusion_reactor

