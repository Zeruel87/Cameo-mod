# AA naming migration - `_AG`/`_AA` twins, `_AGOnly`/`_AAOnly` disjoint pairs

Generated from the resolved ruleset. **NOT YET APPLIED** - executing it is a
`safe_rename.py` migration needing a boot gate and a quiet tree.

The suffix tells the balance formula which mechanism a weapon belongs to, so nothing has to
be inferred (DESIGN 3a.8, 3a.10):

| naming | meaning | the formula |
|---|---|---|
| `X_AG` + `X_AA` | ONE weapon split for reach | prices `X_AG`, **drops** `X_AA` |
| `X_AGOnly` + `X_AAOnly` | TWO independent weapons | prices **both**, never summed |
| no suffix | hits everything, or is the only weapon | priced normally |

**94 renames** - 74 twin, 16 disjoint, 4 dropped.

## Twin splits - the ground half gains `_AG`

| old | new | why |
|---|---|---|
| `ArmoredCarMG` | `ArmoredCarMG_AG` | ground half of the twin ArmoredCarMG_AA (same actor) |
| `AsianQuasarAG` | `AsianQuasar_AG` | AG spelling normalised on a proven twin |
| `AsianQuasarBoatAG` | `AsianQuasarBoat_AG` | AG spelling normalised on a proven twin |
| `CabalHeavyReaperMissiles` | `CabalHeavyReaperMissiles_AG` | ground half of the twin CabalHeavyReaperMissiles_AA (same actor) |
| `CabalReaperMissiles` | `CabalReaperMissiles_AG` | ground half of the twin CabalReaperMissiles_AA (same actor) |
| `DiabloCannon` | `DiabloCannon_AG` | ground half of the twin DiabloCannon_AA (same actor) |
| `DiabloCannon_elite` | `DiabloCannon_AG_elite` | state variant of the twin's ground half |
| `Lunar_AmplifiedBeetleLaser` | `Lunar_AmplifiedBeetleLaser_AG` | ground half of the twin Lunar_AmplifiedBeetleLaser_AA (same actor) |
| `Lunar_AmplifiedTank2Laser` | `Lunar_AmplifiedTank2Laser_AG` | ground half of the twin Lunar_AmplifiedTank2Laser_AA (same actor) |
| `Lunar_YellowBeetleLaser` | `Lunar_YellowBeetleLaser_AG` | ground half of the twin Lunar_YellowBeetleLaser_AA (same actor) |
| `Lunar_YellowTank2Laser` | `Lunar_YellowTank2Laser_AG` | ground half of the twin Lunar_YellowTank2Laser_AA (same actor) |
| `ManifoldMG` | `ManifoldMG_AG` | ground half of the twin ManifoldMG_AA (same actor) |
| `MigMissiles` | `MigMissiles_AG` | ground half of the twin MigMissiles_AA (same actor) |
| `MigMissiles_elite` | `MigMissiles_AG_elite` | state variant of the twin's ground half |
| `MigMissiles_fire` | `MigMissiles_AG_fire` | state variant of the twin's ground half |
| `MigMissiles_fire_elite` | `MigMissiles_AG_fire_elite` | state variant of the twin's ground half |
| `MigMissiles_rad` | `MigMissiles_AG_rad` | state variant of the twin's ground half |
| `MigMissiles_rad_elite` | `MigMissiles_AG_rad_elite` | state variant of the twin's ground half |
| `MigMissiles_tesla` | `MigMissiles_AG_tesla` | state variant of the twin's ground half |
| `MigMissiles_tesla_elite` | `MigMissiles_AG_tesla_elite` | state variant of the twin's ground half |
| `NaxQuadCannon` | `NaxQuadCannon_AG` | ground half of the twin NaxQuadCannon_AA (same actor) |
| `NaxQuadCannon_elite` | `NaxQuadCannon_AG_elite` | state variant of the twin's ground half |
| `NaxiTank2Laser` | `NaxiTank2Laser_AG` | ground half of the twin NaxiTank2Laser_AA (same actor) |
| `NaxiWW2Machinegun` | `NaxiWW2Machinegun_AG` | ground half of the twin NaxiWW2Machinegun_AA (same actor) |
| `NaxiWW2MachinegunSmall` | `NaxiWW2MachinegunSmall_AG` | ground half of the twin NaxiWW2MachinegunSmall_AA (same actor) |
| `NaxiWW2MachinegunTop` | `NaxiWW2MachinegunTop_AG` | ground half of the twin NaxiWW2MachinegunTop_AA (same actor) |
| `Naxis_Komet` | `Naxis_Komet_AG` | ground half of the twin Naxis_Komet_AA (same actor) |
| `RA2APCMachineGun` | `RA2APCMachineGun_AG` | ground half of the twin RA2APCMachineGun_AA (same actor) |
| `RA2APCMachineGun_elite` | `RA2APCMachineGun_AG_elite` | state variant of the twin's ground half |
| `RA2APCRocket` | `RA2APCRocket_AG` | ground half of the twin RA2APCRocket_AA (same actor) |
| `RA2APCRocket_elite` | `RA2APCRocket_AG_elite` | state variant of the twin's ground half |
| `RA2GattlingMG1` | `RA2GattlingMG1_AG` | ground half of the twin RA2GattlingMG1_AA (same actor) |
| `RA2GattlingMG2` | `RA2GattlingMG2_AG` | ground half of the twin RA2GattlingMG2_AA (same actor) |
| `RA2GattlingMG3` | `RA2GattlingMG3_AG` | ground half of the twin RA2GattlingMG3_AA (same actor) |
| `RA2HoverMissile` | `RA2HoverMissile_AG` | ground half of the twin RA2HoverMissile_AA (same actor) |
| `RA2HoverMissile_elite` | `RA2HoverMissile_AG_elite` | state variant of the twin's ground half |
| `RA2MedusaAG` | `RA2Medusa_AG` | AG spelling normalised on a proven twin |
| `RA2MultiHoverMissile` | `RA2MultiHoverMissile_AG` | ground half of the twin RA2MultiHoverMissile_AA (same actor) |
| `RA2MultiHoverMissile_elite` | `RA2MultiHoverMissile_AG_elite` | state variant of the twin's ground half |
| `RA2MultiThunderboltMissile` | `RA2MultiThunderboltMissile_AG` | ground half of the twin RA2MultiThunderboltMissile_AA (same actor) |
| `RA2MultiThunderboltMissile_elite` | `RA2MultiThunderboltMissile_AG_elite` | state variant of the twin's ground half |
| `RA2ThunderboltMissile` | `RA2ThunderboltMissile_AG` | ground half of the twin RA2ThunderboltMissile_AA (same actor) |
| `RA2ThunderboltMissile_elite` | `RA2ThunderboltMissile_AG_elite` | state variant of the twin's ground half |
| `SkyMageCannon` | `SkyMageCannon_AG` | ground half of the twin SkyMageCannon_AA (same actor) |
| `SkyMageCannon_elite` | `SkyMageCannon_AG_elite` | state variant of the twin's ground half |
| `SteelMantaAG` | `SteelManta_AG` | AG spelling normalised on a proven twin |
| `SteelMantaHunterCannons` | `SteelMantaHunterCannons_AG` | ground half of the twin SteelMantaHunterCannons_AA (same actor) |
| `TSAdatsMissile` | `TSAdatsMissile_AG` | ground half of the twin TSAdatsMissile_AA (same actor) |
| `YuriGatlingCannonMG1` | `YuriGatlingCannonMG1_AG` | ground half of the twin YuriGatlingCannonMG1_AA (same actor) |
| `YuriGatlingCannonMG2` | `YuriGatlingCannonMG2_AG` | ground half of the twin YuriGatlingCannonMG2_AA (same actor) |
| `YuriGatlingCannonMG3` | `YuriGatlingCannonMG3_AG` | ground half of the twin YuriGatlingCannonMG3_AA (same actor) |
| `d2k_basq` | `d2k_basq_AG` | ground half of the twin d2k_basq_AA (same actor) |
| `edenTiger_EMP` | `edenTiger_EMP_AG` | ground half of the twin edenTiger_EMP_AA (same actor) |
| `eden_EMP` | `eden_EMP_AG` | ground half of the twin eden_EMP_AA (same actor) |
| `ra1_allies_alliedapc_gun` | `ra1_allies_alliedapc_gun_AG` | ground half of the twin ra1_allies_alliedapc_gun_AA (same actor) |
| `ra1_allies_alliedheavyaatank_cannon` | `ra1_allies_alliedheavyaatank_cannon_AG` | ground half of the twin ra1_allies_alliedheavyaatank_cannon_AA (same actor) |
| `ra1_soviets_btr80_machinegun` | `ra1_soviets_btr80_machinegun_AG` | ground half of the twin ra1_soviets_btr80_machinegun_AA (same actor) |
| `ra1_soviets_btr80_machinegun_tesla` | `ra1_soviets_btr80_machinegun_tesla_AG` | ground half of the twin ra1_soviets_btr80_machinegun_tesla_AA (same actor) |
| `ra1_soviets_btr80_machinegun_tesla_arc` | `ra1_soviets_btr80_machinegun_tesla_arc_AG` | ground half of the twin ra1_soviets_btr80_machinegun_tesla_arc_AA (same actor) |
| `ra1_soviets_flaktruck_flak_cannon` | `ra1_soviets_flaktruck_flak_cannon_AG` | ground half of the twin ra1_soviets_flaktruck_flak_cannon_AA (same actor) |
| `ra1_soviets_gatlingtank_incendiaryragatlingtankcannon` | `ra1_soviets_gatlingtank_incendiaryragatlingtankcannon_AG` | ground half of the twin ra1_soviets_gatlingtank_incendiaryragatlingtankcannon_AA (same actor) |
| `ra1_soviets_gatlingtank_ragatlingtankcannon` | `ra1_soviets_gatlingtank_ragatlingtankcannon_AG` | ground half of the twin ra1_soviets_gatlingtank_ragatlingtankcannon_AA (same actor) |
| `ra1_soviets_gatlingtank_teslaragatlingtankcannon` | `ra1_soviets_gatlingtank_teslaragatlingtankcannon_AG` | ground half of the twin ra1_soviets_gatlingtank_teslaragatlingtankcannon_AA (same actor) |
| `ra1_soviets_gatlingtank_teslaragatlingtankcannonarc` | `ra1_soviets_gatlingtank_teslaragatlingtankcannonarc_AG` | ground half of the twin ra1_soviets_gatlingtank_teslaragatlingtankcannonarc_AA (same actor) |
| `td_gdi_apc_apcgun` | `td_gdi_apc_apcgun_AG` | ground half of the twin td_gdi_apc_apcgun_AA (same actor) |
| `td_gdi_assaultapc_machinegunhumvee2` | `td_gdi_assaultapc_machinegunhumvee2_AG` | ground half of the twin td_gdi_assaultapc_machinegunhumvee2_AA (same actor) |
| `td_gdi_assaultapc_machinegunhumvee2ap` | `td_gdi_assaultapc_machinegunhumvee2ap_AG` | ground half of the twin td_gdi_assaultapc_machinegunhumvee2ap_AA (same actor) |
| `td_gdi_boxer_boxercannonag` | `td_gdi_boxer_boxercannon_AG` | AG spelling normalised on a proven twin |
| `td_gdi_humveemkii_machinegunhumvee2` | `td_gdi_humveemkii_machinegunhumvee2_AG` | ground half of the twin td_gdi_humveemkii_machinegunhumvee2_AA (same actor) |
| `td_gdi_humveemkii_machinegunhumvee2ap` | `td_gdi_humveemkii_machinegunhumvee2ap_AG` | ground half of the twin td_gdi_humveemkii_machinegunhumvee2ap_AA (same actor) |
| `td_gdi_humveemkii_rocketshumvee2` | `td_gdi_humveemkii_rocketshumvee2_AG` | ground half of the twin td_gdi_humveemkii_rocketshumvee2_AA (same actor) |
| `td_gdi_humveemkii_rocketshumvee2amt` | `td_gdi_humveemkii_rocketshumvee2amt_AG` | ground half of the twin td_gdi_humveemkii_rocketshumvee2amt_AA (same actor) |
| `td_nod_buggymkii_laserbuggy2` | `td_nod_buggymkii_laserbuggy2_AG` | ground half of the twin td_nod_buggymkii_laserbuggy2_AA (same actor) |
| `td_nod_buggymkii_machinegunbuggy2` | `td_nod_buggymkii_machinegunbuggy2_AG` | ground half of the twin td_nod_buggymkii_machinegunbuggy2_AA (same actor) |

## Disjoint pairs - the air half gains `_AAOnly` (3a.10)

| old | new | why |
|---|---|---|
| `A10CarrierMissiles_AA` | `A10CarrierMissiles_AAOnly` | disjoint air weapon; never shares a target with NapalmA10Carrier, and does not match it on cadence or reach |
| `AsianQuasarBoat_AA` | `AsianQuasarBoat_AAOnly` | disjoint air weapon; never shares a target with AsianQuasarBoatAG, AsianQuasarBoatAG_EMP, and does not match it on cadence or reach |
| `AsianQuasarBoat_EMP_AA` | `AsianQuasarBoat_EMP_AAOnly` | disjoint air weapon; never shares a target with AsianQuasarBoatAG, AsianQuasarBoatAG_EMP, and does not match it on cadence or reach |
| `D2K_APC_Rocket_AA` | `D2K_APC_Rocket_AAOnly` | disjoint air weapon; never shares a target with Laboratory_Bioball, and does not match it on cadence or reach |
| `D2K_Rocket_Trooper_AA` | `D2K_Rocket_Trooper_AAOnly` | disjoint air weapon; never shares a target with D2K_Rocket_Trooper_AGOnly, and does not match it on cadence or reach |
| `DiabloCannonAAE_AA` | `DiabloCannonAAE_AAOnly` | disjoint air weapon; never shares a target with DiabloCannon, DiabloCannon_elite, and does not match it on cadence or reach |
| `GoliathRockets_AA` | `GoliathRockets_AAOnly` | disjoint air weapon; never shares a target with GoliathMG, and does not match it on cadence or reach |
| `RA2MammothTusk_AA` | `RA2MammothTusk_AAOnly` | disjoint air weapon; never shares a target with RA2120xmm, RA2120xmm_elite, and does not match it on cadence or reach |
| `ScoutRockets_AA` | `ScoutRockets_AAOnly` | disjoint air weapon; never shares a target with ScoutMG, and does not match it on cadence or reach |
| `SeaScorpion_AA` | `SeaScorpion_AAOnly` | disjoint air weapon; never shares a target with RA2FlakTrackGun, and does not match it on cadence or reach |
| `Spore_AA` | `Spore_AAOnly` | disjoint air weapon; never shares a target with Tentacle, and does not match it on cadence or reach |
| `SteelMantaHunterCannonsAAResonance_AA` | `SteelMantaHunterCannonsAAResonance_AAOnly` | disjoint air weapon; never shares a target with SteelMantaHunterCannons, SteelMantaHunterCannonsResonance, and does not match it on cadence or reach |
| `TSMammothTusk2II_AA` | `TSMammothTusk2II_AAOnly` | disjoint air weapon; never shares a target with TSMechMGII, TSMechRailgunII, and does not match it on cadence or reach |
| `WraithRockets_AA` | `WraithRockets_AAOnly` | disjoint air weapon; never shares a target with WraithLaser, and does not match it on cadence or reach |
| `aadeploytargeting_8c0_AA` | `aadeploytargeting_8c0_AAOnly` | disjoint air weapon; never shares a target with FutureEnforcerShotgun, FutureEnforcerShotgunDeployed, and does not match it on cadence or reach |
| `td_gdi_firehawk_firehawkmissiles_AA` | `td_gdi_firehawk_firehawkmissiles_AAOnly` | disjoint air weapon; never shares a target with td_gdi_firehawk_firehawkbomb, and does not match it on cadence or reach |

## Suffix dropped - it marked nothing

| old | new | why |
|---|---|---|
| `D2K_Rocket_AA` | `D2K_ADP_Rocket` | maintainer-named; the plain de-suffixed name is taken by another weapon |
| `ra1_allies_rapierjumpjet_missile_AA` | `ra1_allies_rapierjumpjet_missile` | it attacks air AND ground |
| `ra1_allies_rapierjumpjet_missile_cryo_AA` | `ra1_allies_rapierjumpjet_missile_cryo` | it attacks air AND ground |
| `ra1_soviets_samsite_missile_AA` | `ra1_soviets_samsite_missile` | it is the actor's only weapon |

## ⚠ Needs a human - the target name is already taken

| old | wanted | why |
|---|---|---|
| `AsianQuasarAG` | `AsianQuasar_EMP_AG` | already scheduled as AsianQuasar_AG - one weapon cannot take two names: ground half of the twin AsianQuasar_EMP_AA (matched on cadence + 1.5x reach, not on name) |
| `SteelMantaAG` | `SteelMantaAAResonance_AG` | already scheduled as SteelManta_AG - one weapon cannot take two names: ground half of the twin SteelMantaAAResonance_AA (matched on cadence + 1.5x reach, not on name) |
