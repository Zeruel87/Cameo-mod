# audit_display_text — internal ids leaked into UI prose

Active findings: **48**; dormant findings: **0**; technical references: **2**; comments for inspection: **0**


## D1 — active display text containing actor ids (48) — BLOCKING

| location | field | internal id | value |
|---|---|---|---|
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:5 | Name | scrin_extractor | scrin_extractor |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:13 | Name | scrin_portal | scrin_portal |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:21 | Name | scrin_warp_gate | scrin_warp_gate |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:29 | Name | scrin_gravity_stabilizer | scrin_gravity_stabilizer |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:37 | Name | scrin_nerve_center | scrin_nerve_center |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:45 | Name | scrin_stasis_chamber | scrin_stasis_chamber |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:53 | Name | scrin_technology_assembler | scrin_technology_assembler |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:61 | Name | scrin_signal_transmitter | scrin_signal_transmitter |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:69 | Name | scrin_buzzer_hive | scrin_buzzer_hive |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:77 | Name | scrin_photon_cannon | scrin_photon_cannon |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:85 | Name | scrin_plasma_missile_battery | scrin_plasma_missile_battery |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:93 | Name | scrin_growth_accelerator | scrin_growth_accelerator |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:101 | Name | scrin_growth_stimulator | scrin_growth_stimulator |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:109 | Name | scrin_storm_column | scrin_storm_column |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:117 | Name | scrin_rift_generator | scrin_rift_generator |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:125 | Name | scrin_lightning_spike | scrin_lightning_spike |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:133 | Name | scrin_tiberium_hive | scrin_tiberium_hive |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:141 | Name | scrin_warp_chasm | scrin_warp_chasm |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:149 | Name | scrin_foundry | scrin_foundry |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:157 | Name | scrin_outpost | scrin_outpost |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:165 | Name | scrin_control_node | scrin_control_node |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:173 | Name | scrin_phase_generator | scrin_phase_generator |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:181 | Name | scrin_lifeform_recycling_plant | scrin_lifeform_recycling_plant |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/buildup-palettes.yaml:189 | Name | scrin_terraforming_nexus | scrin_terraforming_nexus |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:39 | Name | scrin_reactor | scrin_reactor |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:47 | Name | scrin_fusion_reactor | scrin_fusion_reactor |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:64 | Name | scrin_disintegrator | scrin_disintegrator |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:73 | Name | scrin_assimilator | scrin_assimilator |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:82 | Name | scrin_shock_trooper | scrin_shock_trooper |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:91 | Name | scrin_shock_trooper_blink_pack | scrin_shock_trooper_blink_pack |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:100 | Name | scrin_ravager | scrin_ravager |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:109 | Name | scrin_mastermind | scrin_mastermind |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:118 | Name | scrin_prodigy | scrin_prodigy |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:127 | Name | scrin_explorer | scrin_explorer |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:136 | Name | scrin_harvester | scrin_harvester |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:145 | Name | scrin_seeker | scrin_seeker |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:154 | Name | scrin_devourer_tank | scrin_devourer_tank |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:163 | Name | scrin_repair_drone | scrin_repair_drone |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:172 | Name | scrin_gun_walker | scrin_gun_walker |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:181 | Name | scrin_shard_walker | scrin_shard_walker |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:190 | Name | scrin_corrupter | scrin_corrupter |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:199 | Name | scrin_annihilator_tripod | scrin_annihilator_tripod |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:208 | Name | scrin_reaper_tripod | scrin_reaper_tripod |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:217 | Name | scrin_stormrider | scrin_stormrider |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:226 | Name | scrin_devastator_warship | scrin_devastator_warship |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:235 | Name | scrin_planetary_assault_carrier | scrin_planetary_assault_carrier |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:244 | Name | scrin_invader_fighter | scrin_invader_fighter |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/palettes.yaml:253 | Name | scrin_mothership | scrin_mothership |


## D2 — dormant display text containing actor ids (0)

_none found_


## D0 — technical references in display-named fields (2) — INFORMATIONAL

| location | field | internal id | value |
|---|---|---|---|
| mods/cameo/ContentPacks/D2k/Ixian/yaml/upgrades.yaml:124 | Description | ixian_ixresearchcenter | upgrade_d2k_advanced_ixian_technology.description, ~ixian_ixresearchcenter |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/upgrades.yaml:171 | Description | ordos_ixresearchcenter | Grants cloaking capabilities to advanced Ordos aircraft., ~ordos_ixresearchcenter |

