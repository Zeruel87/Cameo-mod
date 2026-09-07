# audit_outliers — systemic numeric drift (B9)

(trait,field) distributions sampled: **18** — robust outliers (top 25 per field): **165**, selection bounds > 5120: **0**


## Hard screen — Selectable bounds above the 5x5-cell maximum

_none found_


## Robust outliers per (trait, field), |z| > 8

| trait.field | actor | value | median | robust z |
|---|---|---|---|---|
| Aircraft.CruiseAltitude | TSDPOD | 16384 | 2160 | 24.0 |
| Aircraft.CruiseAltitude | INVISIBLEPLANE | 9000 | 2160 | 11.5 |
| Aircraft.TurnSpeed | japan_rocketangel_husk | 160 | 20 | 18.9 |
| Aircraft.TurnSpeed | ra2rock.husk | 160 | 20 | 18.9 |
| Aircraft.TurnSpeed | yrlunr.husk | 160 | 20 | 18.9 |
| Aircraft.TurnSpeed | litt_husk.nax | 160 | 20 | 18.9 |
| Aircraft.TurnSpeed | cabal_overkillgunship_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | cabal_hunterdronecarrier_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | cabal_hunterdrone_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | cabal_hunterkillermk1_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | cabal_cyborgassassin_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | ts_nod_bansheefighter_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | ts_nod_harpy_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | ts_gdi_carryall | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | ts_gdi_orcafighter_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | ts_gdi_carryall_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | ts_gdi_strike_orca_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | forgotten_carryall | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | forgotten_cobracopter_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | forgotten_apache_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | forgotten_wasp_husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | RA2FALC.Husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | ra2beag.Husk | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | phoenix_husk.asian | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | harbinger_husk.asian | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | twister_husk.steel | 80 | 20 | 8.1 |
| Aircraft.TurnSpeed | tkmdrone | 80 | 20 | 8.1 |
| ChangesHealth.PercentageStep | wc2_orcs_deathknight | 83 | 1 | 55.3 |
| ChangesHealth.Step | terran_marine | -2000 | 20 | 68.1 |
| ChangesHealth.Step | terran_madcap | -2000 | 20 | 68.1 |
| ChangesHealth.Step | terran_firebat | -2000 | 20 | 68.1 |
| ChangesHealth.Step | terran_harakan | -2000 | 20 | 68.1 |
| ChangesHealth.Step | terran_marauder | -2000 | 20 | 68.1 |
| ChangesHealth.Step | terran_jimraynor | -2000 | 20 | 68.1 |
| ChangesHealth.Step | japan_shogunexecutioner | 1200 | 20 | 39.8 |
| ChangesHealth.Step | cabal_berserker | 800 | 20 | 26.3 |
| ChangesHealth.Step | cabal_coredefender | 800 | 20 | 26.3 |
| ChangesHealth.Step | naxis_ratte | 800 | 20 | 26.3 |
| ChangesHealth.Step | steelconsortium_empressstation | 600 | 20 | 19.6 |
| ChangesHealth.Step | ts_gdi_mammothmkii | 480 | 20 | 15.5 |
| ChangesHealth.Step | ra1_soviets_volkov | 400 | 20 | 12.8 |
| ChangesHealth.Step | ra1_soviets_monstertank | 400 | 20 | 12.8 |
| ChangesHealth.Step | cabal_avatar_backup | 400 | 20 | 12.8 |
| ChangesHealth.Step | cabal_cyborgcommandov2 | 400 | 20 | 12.8 |
| ChangesHealth.Step | cabal_constructionyard | 400 | 20 | 12.8 |
| ChangesHealth.Step | cabal_avatar | 400 | 20 | 12.8 |
| ChangesHealth.Step | forgotten_experimentalmammothtank | 400 | 20 | 12.8 |
| ChangesHealth.Step | terran_phobos | 400 | 20 | 12.8 |
| ChangesHealth.Step | ts_gdi_kodiakcommandship | 360 | 20 | 11.5 |
| ChangesHealth.Step | futuretech_cryolegionnaire | 360 | 20 | 11.5 |
| ChangesHealth.Step | latinsyndicate_tortugatank | 350 | 20 | 11.1 |
| ChangesHealth.Step | ts_gdi_mammothprototype | 320 | 20 | 10.1 |
| ChangesHealth.Step | ra2_soviets_kirovairship | 320 | 20 | 10.1 |
| Health.HP | schwarzermond_dieglocke | 3750000 | 60000 | 62.2 |
| Health.HP | japan_shogunexecutioner | 3000000 | 60000 | 49.6 |
| Health.HP | cabal_avatar_backup | 2500000 | 60000 | 41.1 |
| Health.HP | cabal_coredefender | 2000000 | 60000 | 32.7 |
| Health.HP | naxis_ratte | 2000000 | 60000 | 32.7 |
| Health.HP | steelconsortium_empressstation | 1500000 | 60000 | 24.3 |
| Health.HP | schwarzermond_spacezeppelin | 1350000 | 60000 | 21.8 |
| Health.HP | naxis_transportzeppelin | 1250000 | 60000 | 20.1 |
| Health.HP | ts_gdi_mammothmkii | 1200000 | 60000 | 19.2 |
| Health.HP | td_gdi_constructionyard | 1000000 | 60000 | 15.9 |
| Health.HP | td_gdi_advancedcommunicationscenter | 1000000 | 60000 | 15.9 |
| Health.HP | td_nod_constructionyard | 1000000 | 60000 | 15.9 |
| Health.HP | td_nod_templeofnod | 1000000 | 60000 | 15.9 |
| Health.HP | japan_japaneseconstructionyard | 1000000 | 60000 | 15.9 |
| Health.HP | japan_japaneseshrine | 1000000 | 60000 | 15.9 |
| Health.HP | ra1_soviets_sovietconstructionyard | 1000000 | 60000 | 15.9 |
| Health.HP | ra1_soviets_sovietmissilesilo | 1000000 | 60000 | 15.9 |
| Health.HP | ra1_soviets_ironcurtain | 1000000 | 60000 | 15.9 |
| Health.HP | ra1_soviets_monstertank | 1000000 | 60000 | 15.9 |
| Health.HP | ra1_allies_alliedconstructionyard | 1000000 | 60000 | 15.9 |
| Health.HP | ra1_allies_chronosphere | 1000000 | 60000 | 15.9 |
| Health.HP | TSGTCNST | 1000000 | 60000 | 15.9 |
| Health.HP | cabal_core | 1000000 | 60000 | 15.9 |
| Health.HP | cabal_constructionyard | 1000000 | 60000 | 15.9 |
| Health.HP | cabal_avatar | 1000000 | 60000 | 15.9 |
| Mobile.TurnSpeed | hole_small.nax2 | 255 | 20 | 22.6 |
| Mobile.TurnSpeed | hole.nax2 | 255 | 20 | 22.6 |
| Mobile.TurnSpeed | SCSPIDERMINE | 200 | 20 | 17.3 |
| Power.Amount | asianalliance_tankreactor | 2700 | -40 | 61.6 |
| Power.Amount | wc2_humans_sunwell | 2500 | -40 | 57.1 |
| Power.Amount | ra2_soviets_nuclearreactor | 2000 | -40 | 45.9 |
| Power.Amount | zerg_overmind | 2000 | -40 | 45.9 |
| Power.Amount | steelconsortium_bfg10000 | -1000 | -40 | 21.6 |
| Power.Amount | TECHBCANNON2 | -1000 | -40 | 21.6 |
| Power.Amount | steelconsortium_geothermalreactor | 750 | -40 | 17.8 |
| Power.Amount | futuretech_hypercore | 750 | -40 | 17.8 |
| Power.Amount | latinsyndicate_powerstation | 500 | -40 | 12.1 |
| Power.Amount | C2KNUKE | 500 | -40 | 12.1 |
| Power.Amount | protoss_starshipsovereign | -500 | -40 | 10.3 |
| Power.Amount | terran_phobos | -500 | -40 | 10.3 |
| Power.Amount | yuri_bioreactor | 400 | -40 | 9.9 |
| Power.Amount | ts_nod_advancedpowerplant | 360 | -40 | 9.0 |
| Repairable.HpPerStep | japan_shogunexecutioner | 150000 | 4250 | 43.7 |
| Repairable.HpPerStep | naxis_ratte | 100000 | 4250 | 28.7 |
| Repairable.HpPerStep | ts_gdi_mammothmkii | 60000 | 4250 | 16.7 |
| Repairable.HpPerStep | ra1_soviets_monstertank | 50000 | 4250 | 13.7 |
| Repairable.HpPerStep | forgotten_experimentalmammothtank | 50000 | 4250 | 13.7 |
| Repairable.HpPerStep | terran_phobos | 50000 | 4250 | 13.7 |
| Repairable.HpPerStep | ts_gdi_kodiakcommandship | 45000 | 4250 | 12.2 |
| Repairable.HpPerStep | latinsyndicate_tortugatank | 43750 | 4250 | 11.8 |
| Repairable.HpPerStep | ts_gdi_mammothprototype | 40000 | 4250 | 10.7 |
| Repairable.HpPerStep | japan_exorcistoitank | 37500 | 4250 | 10.0 |
| Repairable.HpPerStep | protoss_starshipsovereign | 37500 | 4250 | 10.0 |
| Repairable.HpPerStep | japan_oitank | 32500 | 4250 | 8.5 |
| Repairable.HpPerStep | forgotten_nomadbarracks | 32500 | 4250 | 8.5 |
| Repairable.HpPerStep | futuretech_futuretank | 32500 | 4250 | 8.5 |
| Repairable.HpPerStep | ra1_soviets_siegemammothtank | 31250 | 4250 | 8.1 |
| Repairable.HpPerStep | harkonnen_devastatormech | 31250 | 4250 | 8.1 |
| RevealsShroud.Range | steelconsortium_bfg10000 | 25000 | 2048 | 20.2 |
| RevealsShroud.Range | tkm_radartruck | 21500 | 2048 | 17.1 |
| RevealsShroud.Range | ixian_ixprojector | 20000 | 2048 | 15.8 |
| RevealsShroud.Range | wc2_orc_eye_of_kilrogg | 15360 | 2048 | 11.7 |
| RevealsShroud.Range | MISS | 15360 | 2048 | 11.7 |
| RevealsShroud.Range | RAMISS | 15360 | 2048 | 11.7 |
| RevealsShroud.Range | latinsyndicate_smlturret | 15000 | 2048 | 11.4 |
| RevealsShroud.Range | latinsyndicate_latinaadefender | 15000 | 2048 | 11.4 |
| RevealsShroud.Range | ra2_allies_patriotmissilesystem | 14150 | 2048 | 10.6 |
| RevealsShroud.Range | asianalliance_pulsar | 14000 | 2048 | 10.5 |
| RevealsShroud.Range | asianalliance_plasmacannon | 14000 | 2048 | 10.5 |
| RevealsShroud.Range | asianalliance_spitfire | 14000 | 2048 | 10.5 |
| RevealsShroud.Range | td_gdi_skyshield | 13800 | 2048 | 10.3 |
| RevealsShroud.Range | ts_nod_samsite | 13176 | 2048 | 9.8 |
| RevealsShroud.Range | ra2_soviets_flakcannon | 12936 | 2048 | 9.6 |
| RevealsShroud.Range | ra1_soviets_sovietsamsite | 12790 | 2048 | 9.4 |
| RevealsShroud.Range | td_nod_samsite | 12588 | 2048 | 9.3 |
| RevealsShroud.Range | ts_gdi_samtower | 12440 | 2048 | 9.1 |
| RevealsShroud.Range | cabal_hunterdronecarrier | 12345 | 2048 | 9.0 |
| RevealsShroud.Range | cabal_mothership | 12345 | 2048 | 9.0 |
| RevealsShroud.Range | ts_gdi_kodiakcommandship | 12345 | 2048 | 9.0 |
| RevealsShroud.Range | ra2_soviets_kirovairship | 12345 | 2048 | 9.0 |
| RevealsShroud.Range | yuri_floatingdisk | 12345 | 2048 | 9.0 |
| RevealsShroud.Range | steelconsortium_empressstation | 12345 | 2048 | 9.0 |
| RevealsShroud.Range | steelconsortium_cloudbreaker | 12345 | 2048 | 9.0 |
| Selectable.Bounds | ra1_allies_reinforcementpad | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2ctind01 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2ctmiam06 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2ctmiam07 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2ctmsc10 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctwash04 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctwash08 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctwash11 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctwash17 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctpars02 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctpars08 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctpars09 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctpars10 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctpars12 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctpars13 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctpars14 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctrus03 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctrus04 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctrus05 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctrus06 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | ra2_ctsanf05 | 5120 | 1024 | 10.8 |
| Selectable.Bounds | futuretech_constructionyard | 5120 | 1024 | 10.8 |
| Selectable.Bounds | futuretech_launchpad | 5120 | 1024 | 10.8 |
| Selectable.Bounds | C2KNUKE | 5120 | 1024 | 10.8 |
| Selectable.Bounds | td_nod_airstrip | 4096 | 1024 | 8.1 |
| Valued.Cost | cabal_coredefender | 15000 | 1500 | 9.1 |
| Valued.Cost | schwarzermond_dieglocke | 15000 | 1500 | 9.1 |
| Valued.Cost | wc2_orcs_orcgoldmine_bot | 15000 | 1500 | 9.1 |
| Valued.Cost | wc2_humans_humangoldmine_bot | 15000 | 1500 | 9.1 |


_Outliers are leads, not verdicts: epic units are legitimately extreme. Scan for CLUSTERS of similar z-scores — those are unit systems using a stale scale convention._

