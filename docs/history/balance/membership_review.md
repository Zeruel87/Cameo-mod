# Infantry membership review (auto-classified 2026-07-22)

> ⛔ **ARCHIVED 2026-08-23 — not current.** Moved out of the live documentation set: it is either machine-generated (regenerate it rather than reading this copy) or the programme it belonged to is finished or dormant. Kept for provenance. Start at [`docs/HANDOFF.md`](../../HANDOFF.md).

Membership = the `^…InfantryTemplate` each unit inherits (design.subtype), with explicit `design.class_anchor` overrides for pollutants. Review the overrides + ambiguous; then per-class conversion follows.

## Per-class counts

- **scout**: 28
- **closecombat**: 4
- **special_forces**: 19
- **melee**: 41
- **grenadier**: 11
- **heavy_infantry**: 38
- **pure_sniper**: 18
- **heavy_sniper**: 2
- **rocket_trooper**: 32
- **support**: 35
- **commando**: 27
- **flying_infantry**: 8
- **None**: 12


## scout  (28)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `naxis_coneheadsknights` | redalert2mod_naxis | 1000 | 667 | ScoutInfantry |  |
| `conehead2.nax` | redalert2mod_naxis | 500 | 240 | ScoutInfantry |  |
| `tkm_marine` | redalert2mod_tkm | 300 | 375 | ScoutInfantry |  |
| `zerg_spithid` | starcraft_zerg | 300 | 300 | ScoutInfantry |  |
| `forgotten_mutantsoldier` | tiberiansun_forgotten | 250 | 120 | ScoutInfantry | **scout** |
| `forgotten_mutantsoldier_sp` | tiberiansun_forgotten | 250 | 120 | ScoutInfantry |  |
| `ra1_soviets_ak47conscript` | redalert_soviets | 200 | 700 | ScoutInfantry |  |
| `ra2_allies_gi` | redalert2_allies | 200 | 237 | ScoutInfantry |  |
| `forgotten_mutant` | tiberiansun_forgotten | 160 | 167 | ScoutInfantry |  |
| `forgotten_mutant_sp` | tiberiansun_forgotten | 160 | 167 | ScoutInfantry |  |
| `forgotten_mutant_wild` | tiberiansun_forgotten | 160 | 167 | ScoutInfantry |  |
| `ixian_lightinfantry` | d2k_ixian | 150 | 175 | ScoutInfantry |  |
| `light_inf` | shared_d2k | 150 | 175 | ScoutInfantry |  |
| `latinsyndicate_latinmilitia` | redalert2mod_syndicate | 130 | 150 | ScoutInfantry |  |
| `ordos_lightinfantry` | d2k_ordos | 120 | 175 | ScoutInfantry |  |
| `tkm_rifleman` | redalert2mod_tkm | 120 | 60 | ScoutInfantry |  |
| `ts_gdi_lightinfantry` | tiberiansun_gdi | 120 | 125 | ScoutInfantry |  |
| `ts_nod_lightinfantry` | tiberiansun_nod | 120 | 125 | ScoutInfantry |  |
| `asianalliance_asianmilitia` | redalert2mod_asianalliance | 110 | 90 | ScoutInfantry |  |
| `E1` | tiberiandawn_gdi | 100 | 102 | ScoutInfantry |  |
| `naxis_naxiriflesoldier` | redalert2mod_naxis | 100 | 60 | ScoutInfantry |  |
| `ra1_allies_rifleinfantry` | shared_redalert | 100 | 78 | ScoutInfantry | **scout** |
| `ra1_soviets_rifleinfantry` | redalert_soviets | 100 | 75 | ScoutInfantry | **scout** |
| `ra2_soviets_conscript` | redalert2_soviets | 100 | 83 | ScoutInfantry |  |
| `td_gdi_minigunner` | tiberiandawn_gdi | 100 | 102 | ScoutInfantry | **scout** |
| `td_nod_minigunner` | tiberiandawn_nod | 100 | 107 | ScoutInfantry | **scout** |
| `undead.nax` | redalert2mod_naxis | 100 | 60 | ScoutInfantry |  |
| `naxis_naxiriflerecruit` | redalert2mod_naxis | 75 | 60 | ScoutInfantry |  |

## closecombat  (4)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `asianalliance_fanatic` | redalert2mod_asianalliance | 500 | 500 | CloseCombatInfantry | **closecombat** |
| `naxis_sssoldier` | redalert2mod_naxis | 240 | 292 | CloseCombatInfantry | **closecombat** |
| `td_gdi_shotgunner` | tiberiandawn_gdi | 200 | 250 | CloseCombatInfantry | **closecombat** |
| `alien.nax` | redalert2mod_naxis | 110 | 561 | CloseCombatInfantry | **closecombat** |

## special_forces  (19)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `zerg_hydralisk` | starcraft_zerg | 3314 | 3600 | AntiTankAntiAirInfantry | **special_forces** |
| `terran_specter` | starcraft_terran | 1744 | 606 | SniperInfantry | **special_forces** |
| `td_gdi_officer` | tiberiandawn_gdi | 1532 | 1750 | HeavyInfantry | **special_forces** |
| `cabal_eliminator800` | tiberiansun_cabal | 1450 | 800 | HeavyInfantry | **special_forces** |
| `ts_gdi_falconenforcer` | tiberiansun_gdi | 1322 | 1600 | AntiTankAntiAirInfantry | **special_forces** |
| `terran_ghost` | starcraft_terran | 1176 | 455 | SniperInfantry | **special_forces** |
| `ra2_allies_seal` | redalert2_allies | 1162 | 632 | MeleeInfantry | **special_forces** |
| `forgotten_mutantsergeant` | tiberiansun_forgotten | 1154 | 1750 | HeavyInfantry | **special_forces** |
| `terran_madcap` | starcraft_terran | 1003 | 1440 | AntiTankAntiAirInfantry | **special_forces** |
| `td_nod_stealthsoldier` | tiberiandawn_nod | 753 | 4190 | HeavyInfantry | **special_forces** |
| `td_nod_lasertrooper` | tiberiandawn_nod | 750 | 2880 | SpecialForcesInfantry | **special_forces** |
| `terran_marine` | starcraft_terran | 689 | 3600 | AntiTankAntiAirInfantry | **special_forces** |
| `ra1_allies_machinegunner` | redalert_allies | 557 | 1167 | HeavyInfantry | **special_forces** |
| `schwarzermond_lunarsoldier` | redalert2mod_schwarzermond | 500 | 480 | SpecialForcesInfantry | **special_forces** |
| `ts_nod_elitecadre` | tiberiansun_nod | 435 | 1167 | AntiTankAntiAirInfantry | **special_forces** |
| `yuri_gatlingtrooper` | redalert2_yuri | 431 | 933 | AntiTankAntiAirInfantry | **special_forces** |
| `ra2_soviets_flaktrooper` | redalert2_soviets | 416 | 941 | AntiTankAntiAirInfantry | **special_forces** |
| `japan_imperialscoutsman` | redalert_japan | 200 | 240 | SpecialForcesInfantry | **special_forces** |
| `tkm_trooper` | redalert2mod_tkm | 200 | 286 | SpecialForcesInfantry |  |

## melee  (41)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `futuretech_blackwidow` | redalert2mod_futuretech | 1200 | 789 | MeleeInfantry |  |
| `protoss_amaranth` | starcraft_protoss | 1200 | 1125 | MeleeInfantry |  |
| `wc2_orcs_warcraft3grunt` | warcraft2_orcs | 1100 | 1000 | MeleeInfantry |  |
| `ra1_soviets_cyberdog` | redalert_soviets | 1000 | 0 | Dog | **melee** |
| `tkm_spetsnaz` | redalert2mod_tkm | 900 | 417 | MeleeInfantry |  |
| `ts_nod_shadowteam` | tiberiansun_nod | 900 | 700 | MeleeInfantry |  |
| `wc2_humans_warcraft3footman` | warcraft2_humans | 900 | 900 | MeleeInfantry |  |
| `forgotten_runnershotgal` | tiberiansun_forgotten | 750 | 712 | MeleeInfantry |  |
| `forgotten_chemsprayinfantry` | tiberiansun_forgotten | 700 | 1018 | MeleeInfantry |  |
| `protoss_legionnaire` | starcraft_protoss | 700 | 923 | MeleeInfantry |  |
| `terran_harakan` | starcraft_terran | 700 | 0 | MeleeInfantry |  |
| `ts_gdi_riottrooper` | tiberiansun_gdi | 700 | 496 | MeleeInfantry |  |
| `protoss_darktemplar` | starcraft_protoss | 600 | 600 | MeleeInfantry |  |
| `wc2_orcs_grunt` | warcraft2_orcs | 600 | 667 | MeleeInfantry |  |
| `forgotten_visceroid` | tiberiansun_forgotten | 500 | 700 | MeleeInfantry |  |
| `forgotten_zombiemutant` | tiberiansun_forgotten | 500 | 600 | MeleeInfantry |  |
| `frank.nax` | redalert2mod_naxis | 500 | 405 | MeleeInfantry |  |
| `ordos_contaminator` | d2k_ordos | 500 | 375 | MeleeInfantry |  |
| `td_nod_chemicalwarrior` | tiberiandawn_nod | 500 | 750 | MeleeInfantry |  |
| `terran_firebat` | starcraft_terran | 500 | 0 | MeleeInfantry |  |
| `tkm_thermonaut` | redalert2mod_tkm | 500 | 464 | MeleeInfantry |  |
| `ts_nod_chameleonspy` | tiberiansun_nod | 500 | 721 | MeleeInfantry |  |
| `wc2_humans_footman` | warcraft2_humans | 500 | 600 | MeleeInfantry |  |
| `heavy_inf.ixian` | d2k_ixian | 400 | 406 | MeleeInfantry |  |
| `yuri_brute` | redalert2_yuri | 400 | 405 | MeleeInfantry |  |
| `zerg_infestedterranbomber` | starcraft_zerg | 400 | 0 | MeleeInfantry |  |
| `asianalliance_japanesesamurai` | redalert2mod_asianalliance | 350 | 0 | MeleeInfantry |  |
| `asianalliance_alligator` | redalert2mod_asianalliance | 300 | 308 | MeleeInfantry |  |
| `futuretech_enforcer` | redalert2mod_futuretech | 300 | 285 | MeleeInfantry |  |
| `japan_samurai` | redalert_japan | 300 | 375 | MeleeInfantry |  |
| `protoss_zealot` | starcraft_protoss | 300 | 333 | MeleeInfantry |  |
| `wc2_humans_militiapeasant` | warcraft2_humans | 300 | 600 | MeleeInfantry |  |
| `zerg_talon` | starcraft_zerg | 300 | 300 | MeleeInfantry |  |
| `naxis_slave` | redalert2mod_naxis | 250 | 50 | MeleeInfantry |  |
| `tkmworker` | redalert2mod_tkm | 250 | 50 | MeleeInfantry |  |
| `latinsyndicate_terrorist` | redalert2mod_syndicate | 200 | 0 | MeleeInfantry |  |
| `ra1_soviets_attackdog` | redalert_soviets | 200 | 0 | Dog | **melee** |
| `ra2_allies_attackdog` | redalert2_allies | 200 | 0 | Dog | **melee** |
| `ra2_soviets_attackdog` | redalert2_soviets | 200 | 0 | Dog | **melee** |
| `td_nod_flamethrower` | tiberiandawn_nod | 200 | 250 | MeleeInfantry |  |
| `zerg_zergling` | starcraft_zerg | 200 | 136 | MeleeInfantry |  |

## grenadier  (11)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `wc2_humans_mortarteam` | warcraft2_humans | 800 | 400 | MortarInfantry |  |
| `steelconsortium_hoverboardgrenadier` | redalert2mod_consortium | 650 | 340 | GrenadierInfantry |  |
| `ordos_mortartrooper` | d2k_ordos | 600 | 500 | MortarInfantry |  |
| `forgotten_mutantmortarman` | tiberiansun_forgotten | 500 | 409 | MortarInfantry |  |
| `ra1_soviets_mortarsoldier` | redalert_soviets | 500 | 341 | MortarInfantry |  |
| `td_gdi_empgrenadier` | tiberiandawn_gdi | 500 | 613 | GrenadierInfantry |  |
| `latinsyndicate_grenademonkey` | redalert2mod_syndicate | 400 | 542 | GrenadierInfantry |  |
| `ts_gdi_discthrower` | tiberiansun_gdi | 300 | 480 | GrenadierInfantry |  |
| `ra1_soviets_grenadier` | redalert_soviets | 200 | 350 | GrenadierInfantry |  |
| `ra1_soviets_molotovconscript` | shared_redalert | 200 | 280 | GrenadierInfantry |  |
| `td_gdi_grenadier` | tiberiandawn_gdi | 200 | 381 | GrenadierInfantry |  |

## heavy_infantry  (38)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `cabal_cyborgcommandov2` | tiberiansun_cabal | 10000 | 1806 | HeavyInfantry |  |
| `cabal_cyborgcommando` | tiberiansun_cabal | 5000 | 1806 | HeavyInfantry |  |
| `forgotten_viniferafiend` | tiberiansun_forgotten | 2000 | 1688 | HeavyInfantry |  |
| `cabal_enlighted` | tiberiansun_cabal | 1600 | 11200 | HeavyInfantry |  |
| `ts_gdi_zonetrooper` | tiberiansun_gdi | 1500 | 833 | HeavyInfantry |  |
| `cabal_devout` | tiberiansun_cabal | 1400 | 875 | HeavyInfantry |  |
| `ra1_soviets_zapper` | redalert_soviets | 1200 | 1000 | HeavyInfantry |  |
| `steelconsortium_quantummissiletrooper` | redalert2mod_consortium | 1150 | 667 | HeavyInfantry |  |
| `forgotten_tiberianfiend` | tiberiansun_forgotten | 1000 | 788 | HeavyInfantry |  |
| `forgotten_tiberianfiend_wild` | tiberiansun_forgotten | 1000 | 788 | HeavyInfantry |  |
| `terran_marauder` | starcraft_terran | 1000 | 0 | HeavyInfantry |  |
| `ts_nod_toxintrooper` | tiberiansun_nod | 850 | 600 | HeavyInfantry |  |
| `ixian_storminfantry` | d2k_ixian | 800 | 409 | HeavyInfantry |  |
| `cabal_dissolver` | tiberiansun_cabal | 725 | 750 | HeavyInfantry |  |
| `ra2_soviets_desolator` | redalert2_soviets | 700 | 667 | HeavyInfantry |  |
| `schwarzermond_ubermensch` | redalert2mod_schwarzermond | 700 | 485 | HeavyInfantry |  |
| `protoss_adept` | starcraft_protoss | 650 | 450 | HeavyInfantry |  |
| `tkm_juggernaut` | redalert2mod_tkm | 650 | 500 | HeavyInfantry |  |
| `naxis_naximachinegunners` | redalert2mod_naxis | 600 | 0 | HeavyInfantry |  |
| `naxis_panzerschreck` | redalert2mod_naxis | 600 | 426 | HeavyInfantry |  |
| `ra1_soviets_shocktrooper` | redalert_soviets | 600 | 500 | HeavyInfantry |  |
| `td_nod_blackhandflamer` | tiberiandawn_nod | 600 | 364 | HeavyInfantry |  |
| `wc2_humans_dwarvenrifleman` | warcraft2_humans | 600 | 450 | HeavyInfantry |  |
| `asianalliance_plasmatrooper` | redalert2mod_asianalliance | 500 | 471 | HeavyInfantry |  |
| `cabal_cyborginfantry` | tiberiansun_cabal | 500 | 292 | HeavyInfantry |  |
| `ixian_shockinfantry` | d2k_ixian | 500 | 500 | HeavyInfantry |  |
| `latinsyndicate_latinflametrooper` | redalert2mod_syndicate | 500 | 429 | HeavyInfantry |  |
| `ra2_soviets_teslatrooper` | redalert2_soviets | 500 | 240 | HeavyInfantry |  |
| `schwarzermond_noidmgarmor` | redalert2mod_schwarzermond | 500 | 417 | HeavyInfantry |  |
| `asianalliance_asianflametrooper` | redalert2mod_asianalliance | 400 | 340 | HeavyInfantry |  |
| `japan_tankbuster` | redalert_japan | 400 | 281 | HeavyInfantry |  |
| `naxis_panzerfausttrooper` | redalert2mod_naxis | 400 | 293 | HeavyInfantry |  |
| `ordos_chemicaltrooper` | d2k_ordos | 400 | 300 | HeavyInfantry |  |
| `td_gdi_sonicmissilesoldier` | tiberiandawn_gdi | 400 | 425 | HeavyInfantry |  |
| `yuri_biotrooper` | redalert2_yuri | 400 | 343 | HeavyInfantry |  |
| `naxis_naxiflamer` | redalert2mod_naxis | 225 | 136 | HeavyInfantry |  |
| `japan_japaneseflamethrower` | redalert_japan | 200 | 459 | HeavyInfantry |  |
| `ra1_soviets_flamethrower` | redalert_soviets | 200 | 333 | HeavyInfantry |  |

## pure_sniper  (18)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `wc2_humans_archmage` | warcraft2_humans | 1000 | 200 | SniperInfantry |  |
| `wc2_humans_highelfpriest` | warcraft2_humans | 1000 | 200 | SniperInfantry |  |
| `wc2_humans_highelfsorceress` | warcraft2_humans | 1000 | 200 | SniperInfantry |  |
| `wc2_humans_mage` | warcraft2_humans | 1000 | 200 | SniperInfantry |  |
| `wc2_orcs_deathknight` | warcraft2_orcs | 1000 | 450 | SniperInfantry |  |
| `ra2_allies_sniper` | redalert2_allies | 800 | 611 | SniperInfantry |  |
| `asianalliance_shinobi` | redalert2mod_asianalliance | 750 | 600 | SniperInfantry |  |
| `ra1_soviets_commissar` | redalert_soviets | 700 | 375 | SniperInfantry |  |
| `td_gdi_heavysniper` | tiberiandawn_gdi | 700 | 400 | SniperInfantry |  |
| `forgotten_mutantsniper` | tiberiansun_forgotten | 650 | 300 | SniperInfantry |  |
| `forgotten_mutantsniper_r4` | tiberiansun_forgotten | 650 | 300 | SniperInfantry |  |
| `forgotten_mutantsniper_sp` | tiberiansun_forgotten | 650 | 300 | SniperInfantry |  |
| `terran_reaper` | starcraft_terran | 600 | 136 | SniperInfantry |  |
| `tkm_sniper` | redalert2mod_tkm | 600 | 600 | SniperInfantry |  |
| `japan_archermaiden` | redalert_japan | 500 | 300 | SniperInfantry |  |
| `ra1_allies_alliedsniper` | redalert_allies | 500 | 225 | SniperInfantry |  |
| `asianalliance_asdf` | redalert2mod_asianalliance | 357 | 525 | SniperInfantry |  |
| `naxis_naximercenarysniper` | redalert2mod_naxis | 250 | 150 | SniperInfantry |  |

## heavy_sniper  (2)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `yuri_virus` | redalert2_yuri | 700 | 324 | SniperInfantry | **heavy_sniper** |
| `ra1_soviets_dragunovantimaterialsniper` | redalert_soviets | 422 | 5000 | AntiTankAntiAirInfantry | **heavy_sniper** |

## rocket_trooper  (32)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `wc2_humans_highelvenarcher` | warcraft2_humans | 1100 | 1102 | AntiTankAntiAirInfantry |  |
| `wc2_orcs_kodobeast` | warcraft2_orcs | 1000 | 632 | AntiTankAntiAirInfantry |  |
| `wc2_orcs_trollheadhunter` | warcraft2_orcs | 1000 | 964 | AntiTankAntiAirInfantry |  |
| `cabal_ascended` | tiberiansun_cabal | 900 | 1112 | AntiTankAntiAirInfantry |  |
| `cabal_rocketcyborg` | tiberiansun_cabal | 650 | 463 | AntiTankAntiAirInfantry |  |
| `ixian_twinrockettrooper` | d2k_ixian | 600 | 328 | AntiTankAntiAirInfantry |  |
| `wc2_humans_elvenarcher` | warcraft2_humans | 600 | 960 | AntiTankAntiAirInfantry |  |
| `wc2_humans_elvenranger` | warcraft2_humans | 600 | 960 | AntiTankAntiAirInfantry |  |
| `wc2_orcs_trollaxethrower` | warcraft2_orcs | 500 | 632 | AntiTankAntiAirInfantry |  |
| `wc2_orcs_trollberserker` | warcraft2_orcs | 500 | 632 | AntiTankAntiAirInfantry |  |
| `asianalliance_veteranarcher` | redalert2mod_asianalliance | 450 | 529 | AntiTankAntiAirInfantry |  |
| `ordos_antiairtrooper` | d2k_ordos | 450 | 350 | AntiTankAntiAirInfantry |  |
| `futuretech_javelinsoldier` | redalert2mod_futuretech | 400 | 375 | AntiTankAntiAirInfantry |  |
| `ra1_soviets_firerocketsoldier` | redalert_soviets | 400 | 528 | AntiTankAntiAirInfantry |  |
| `ra2_allies_guardiangi` | redalert2_allies | 400 | 438 | AntiTankAntiAirInfantry |  |
| `td_nod_chemicalrocketsoldier` | tiberiandawn_nod | 400 | 556 | AntiTankAntiAirInfantry |  |
| `schwarzermond_lunarrocket` | redalert2mod_schwarzermond | 350 | 260 | AntiTankAntiAirInfantry |  |
| `asianalliance_asiantankkiller` | redalert2mod_asianalliance | 300 | 340 | AntiTankAntiAirInfantry |  |
| `forgotten_rocketinfantry` | tiberiansun_forgotten | 300 | 346 | AntiTankAntiAirInfantry |  |
| `ixian_rockettrooper` | d2k_ixian | 300 | 328 | AntiTankAntiAirInfantry |  |
| `ordos_rockettrooper` | d2k_ordos | 300 | 328 | AntiTankAntiAirInfantry |  |
| `ra1_allies_alliedrocketsoldier` | shared_redalert | 300 | 350 | AntiTankAntiAirInfantry |  |
| `ra1_soviets_rocketsoldier` | redalert_soviets | 300 | 350 | AntiTankAntiAirInfantry |  |
| `trooper` | shared_d2k | 300 | 328 | AntiTankAntiAirInfantry |  |
| `ts_nod_rocketinfantry` | tiberiansun_nod | 300 | 346 | AntiTankAntiAirInfantry |  |
| `latinsyndicate_latintankkiller` | redalert2mod_syndicate | 270 | 295 | AntiTankAntiAirInfantry |  |
| `E3` | tiberiandawn_gdi | 200 | 214 | AntiTankAntiAirInfantry |  |
| `td_gdi_rocketsoldier` | tiberiandawn_gdi | 200 | 214 | AntiTankAntiAirInfantry |  |
| `td_nod_rocketsoldier` | tiberiandawn_nod | 200 | 214 | AntiTankAntiAirInfantry |  |
| `tkm_rocketeer` | redalert2mod_tkm | 200 | 211 | AntiTankAntiAirInfantry |  |
| `yuri_initiate` | redalert2_yuri | 200 | 489 | AntiTankAntiAirInfantry |  |
| `steelconsortium_clonetrooper` | redalert2mod_consortium | 143 | 240 | AntiTankAntiAirInfantry |  |

## support  (35)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `ra2_allies_chronolegionnaire` | redalert2_allies | 1500 | 0 | HeavyInfantry | **support** |
| `zerg_defiler` | starcraft_zerg | 1400 | 214 | ScoutInfantry | **support** |
| `cabal_hackercyborg` | tiberiansun_cabal | 1250 | 0 | HeavyInfantry | **support** |
| `futuretech_spyfutu` | redalert2mod_futuretech | 1000 | 0 | ScoutInfantry | **support** |
| `cabal_engineer` | tiberiansun_cabal | 800 | 0 | Mechanic | **support** |
| `protoss_hightemplar` | starcraft_protoss | 800 | 0 | AntiTankAntiAirInfantry | **support** |
| `latinsyndicate_narco` | redalert2mod_syndicate | 756 | 0 | SniperInfantry | **support** |
| `forgotten_mutanthijacker` | tiberiansun_forgotten | 750 | 0 | HeroInfantry | **support** |
| `forgotten_engineer` | tiberiansun_forgotten | 600 | 600 | SniperInfantry | **support** |
| `ra2_soviets_crazyivan` | redalert2_soviets | 600 | 0 | MeleeInfantry | **support** |
| `terran_medic` | starcraft_terran | 600 | 0 | Medic | **support** |
| `ts_gdi_engineer` | tiberiansun_gdi | 600 | 600 | SniperInfantry | **support** |
| `ts_nod_engineer` | tiberiansun_nod | 600 | 600 | SniperInfantry | **support** |
| `E6` | shared_tiberiandawn | 500 | 0 | Infantry | **support** |
| `asianalliance_engineer` | redalert2mod_asianalliance | 500 | 0 | Infantry | **support** |
| `engineer` | shared_d2k | 500 | 0 | Infantry | **support** |
| `futuretech_engineer` | redalert2mod_futuretech | 500 | 0 | Infantry | **support** |
| `latinsyndicate_engineer` | redalert2mod_syndicate | 500 | 0 | Infantry | **support** |
| `naxis_slaveoverseer` | redalert2mod_naxis | 500 | 60 | ScoutInfantry | **support** |
| `ra1_allies_mechanic` | redalert_allies | 500 | -536 | Mechanic | **support** |
| `ra1_allies_medic` | redalert_allies | 500 | -60 | Medic | **support** |
| `ra1_allies_raspy` | redalert_allies | 500 | 141 | ScoutInfantry | **support** |
| `ra1_engineer` | shared_redalert | 500 | 0 | Infantry | **support** |
| `ra1_scientist` | shared_redalert | 500 | 0 | Infantry | **support** |
| `ra2_allies_engineer` | redalert2_allies | 500 | 0 | Infantry | **support** |
| `ra2_allies_ra2spy` | redalert2_allies | 500 | 0 | ScoutInfantry | **support** |
| `ra2_soviets_engineer` | redalert2_soviets | 500 | 0 | Infantry | **support** |
| `steelconsortium_engineer` | redalert2mod_consortium | 500 | 0 | Infantry | **support** |
| `tkm_engineer` | redalert2mod_tkm | 500 | 0 | Infantry | **support** |
| `ts_gdi_medic` | tiberiansun_gdi | 500 | -60 | Medic | **support** |
| `yuri_clone` | redalert2_yuri | 500 | 0 | ScoutInfantry | **support** |
| `yuri_engineer` | redalert2_yuri | 500 | 0 | Infantry | **support** |
| `naxis_portableflak` | redalert2mod_naxis | 400 | 0 | AntiTankAntiAirInfantry | **support** |
| `ordos_saboteur` | d2k_ordos | 300 | 0 | Infantry | **support** |
| `ra1_einstein` | shared_redalert | 10 | 0 | Infantry | **support** |

## commando  (27)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `ra1_soviets_volkov` | redalert_soviets | 10000 | 4333 | HeroInfantry |  |
| `ordos_facedancer` | d2k_ordos | 5000 | 2000 | HeroInfantry |  |
| `td_nod_lasercommando` | tiberiandawn_nod | 5000 | 1500 | HeroInfantry |  |
| `ts_gdi_railguncommando` | tiberiansun_gdi | 5000 | 2500 | HeroInfantry |  |
| `forgotten_ghoststalker` | tiberiansun_forgotten | 4000 | 600 | HeroInfantry |  |
| `forgotten_ghoststalker_r4` | tiberiansun_forgotten | 4000 | 600 | HeroInfantry |  |
| `forgotten_ghoststalker_sp` | tiberiansun_forgotten | 4000 | 600 | HeroInfantry |  |
| `protoss_patriarch` | starcraft_protoss | 4000 | 333 | HeroInfantry |  |
| `protoss_zeratul` | starcraft_protoss | 4000 | 2000 | HeroInfantry |  |
| `td_gdi_havoc` | tiberiandawn_gdi | 4000 | 0 | HeroInfantry |  |
| `terran_jimraynor` | starcraft_terran | 4000 | 1250 | HeroInfantry |  |
| `yuri_yurix` | redalert2_yuri | 4000 | 0 | HeroInfantry |  |
| `zerg_kerrigan` | starcraft_zerg | 4000 | 1500 | HeroInfantry |  |
| `futuretech_cryolegionnaire` | redalert2mod_futuretech | 3500 | 367 | HeroInfantry |  |
| `tkmvan` | redalert2mod_tkm | 3500 | 2000 | HeroInfantry |  |
| `asianalliance_asiancommando` | redalert2mod_asianalliance | 3000 | 1200 | HeroInfantry |  |
| `japan_exorcist` | redalert_japan | 3000 | 1200 | HeroInfantry |  |
| `latinsyndicate_freedomfighter` | redalert2mod_syndicate | 3000 | 1800 | HeroInfantry |  |
| `ra1_allies_tanya` | redalert_allies | 3000 | 1666 | HeroInfantry |  |
| `ra2_allies_tanyaii` | redalert2_allies | 3000 | 1400 | HeroInfantry |  |
| `ra2_soviets_boris` | redalert2_soviets | 3000 | 1167 | HeroInfantry |  |
| `schwarzermond_parzival` | redalert2mod_schwarzermond | 3000 | 1000 | HeroInfantry |  |
| `steelconsortium_steelrunner` | redalert2mod_consortium | 3000 | 2167 | HeroInfantry |  |
| `td_gdi_commando` | tiberiandawn_gdi | 3000 | 1200 | HeroInfantry |  |
| `td_nod_commando` | tiberiandawn_nod | 3000 | 1200 | HeroInfantry |  |
| `tkm_von` | redalert2mod_tkm | 3000 | 1200 | HeroInfantry |  |
| `ts_nod_shotguncommando` | tiberiansun_nod | 3000 | 2280 | HeroInfantry |  |

## flying_infantry  (8)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `naxis_skymage` | redalert2mod_naxis | 1200 | 1109 | FlyingInfantry |  |
| `yuri_cosmonaut` | redalert2_yuri | 1100 | 1045 | FlyingInfantry |  |
| `japan_rocketangel` | redalert_japan | 900 | 1260 | FlyingInfantry |  |
| `ts_nod_shadowteam_air` | tiberiansun_nod | 900 | 0 | FlyingInfantry |  |
| `zerg_swarmling` | starcraft_zerg | 800 | 206 | FlyingInfantry |  |
| `ts_gdi_jumpjetinfantry` | tiberiansun_gdi | 700 | 320 | FlyingInfantry |  |
| `ra2_allies_rocketeer` | redalert2_allies | 600 | 500 | FlyingInfantry |  |
| `zerg_shriek` | starcraft_zerg | 500 | 273 | FlyingInfantry |  |

## None  (12)

| actor | faction | cost | dps | subtype | override |
|---|---|--:|--:|---|---|
| `ordos_leech` | d2k_ordos | 1100 | 0 | ScoutVehicle |  |
| `futuretech_repairdroid` | redalert2mod_futuretech | 800 | -763 | SupportVehicle |  |
| `schwarzermond_engineeringarmor` | redalert2mod_schwarzermond | 800 | -763 | SupportVehicle |  |
| `futuretech_missiledroid` | redalert2mod_futuretech | 700 | 600 | FireSupport |  |
| `naxis_antitankcannon` | redalert2mod_naxis | 600 | 373 | FireSupport |  |
| `fremen_creep` | shared_d2k | 500 | 175 | Infantry |  |
| `schwarzermond_noidharvester` | redalert2mod_schwarzermond | 500 | 417 | Harvester |  |
| `naxis_bmwbike` | redalert2mod_naxis | 450 | 0 | ScoutVehicle |  |
| `futuretech_scoutdroid` | redalert2mod_futuretech | 200 | 304 | ScoutVehicle |  |
| `ra1_agentdelphi` | shared_redalert | 10 | 11 | Infantry |  |
| `ra1_general` | shared_redalert | 10 | 11 | Infantry |  |
| `ra1_technician` | shared_redalert | 10 | 11 | Infantry |  |