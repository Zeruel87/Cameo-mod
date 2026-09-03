# Weapon suffix audit (DESIGN.md §1)

X1 elite weapons not ending _elite: **25**
X2 EMP weapons not ending _EMP: **10**
X3 AA weapons not ending _AA: **8**
X4 deprecated E suffix (informational): **2**
X5 suffix ordering violations: **0**

## X1 — Elite weapons not following _elite convention
| File | Line | Actor | Trait | Weapon |
|---|---|---|---|---|
| ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 2284 | ra2_c_ifv | Armament@elite | RA2GattlingMG2 |
| ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 2302 | ra2_c_ifv | Armament@eliteAA | RA2GattlingMG2_AA |
| ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 2362 | ra2_c_hum | Armament@elite | RA2GattlingMG2 |
| ContentPacks/RedAlert2Mod/AsianAlliance/yaml/infantry.yaml | 244 | asianalliance_asianflametrooper | Armament@ELITE | AsianFlamerTurret |
| ContentPacks/RedAlert2Mod/AsianAlliance/yaml/naval.yaml | 196 | gunb.asian | Armament@AntiSubElite | DepthCharge |
| ContentPacks/RedAlert2Mod/AsianAlliance/yaml/vehicles.yaml | 850 | asianalliance_railguntank | Armament@ELITE | AsianRailTank2 |
| ContentPacks/RedAlert2Mod/AsianAlliance/yaml/vehicles.yaml | 893 | asianalliance_heavyrailguntank | Armament@ELITE | AsianRailTank3 |
| ContentPacks/RedAlert2Mod/Consortium/yaml/vehicles.yaml | 1208 | steelconsortium_megalodon | Armament@ELITE | SteelMegaSword_EMP |
| ContentPacks/RedAlert2Mod/FutureTech/yaml/vehicles.yaml | 484 | futuretech_phalanxwip | Armament@PRIMARYELITE | RA2RTruckRocket |
| ContentPacks/RedAlert2Mod/Naxis/yaml/infantry.yaml | 1086 | conehead2.nax | Armament@ELITE | RA2PortaTesla |
| ContentPacks/RedAlert2Mod/Naxis/yaml/infantry.yaml | 1096 | conehead2.nax | Armament@GARRISONEDELITE | RA2PortaTesla |
| ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/aircraft.yaml | 176 | schwarzermond_spacezeppelin | Armament@eliteUP | Lunar_YellowBeetleLaser |
| ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/aircraft.yaml | 190 | schwarzermond_spacezeppelin | Armament@eliteAA_UP | Lunar_YellowBeetleLaser_AA |
| ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/aircraft.yaml | 204 | schwarzermond_spacezeppelin | Armament@eliteAMP | Lunar_AmplifiedBeetleLaser |
| ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/aircraft.yaml | 218 | schwarzermond_spacezeppelin | Armament@eliteAA_AMP | Lunar_AmplifiedBeetleLaser_AA |
| ContentPacks/RedAlert2Mod/Syndicate/yaml/infantry.yaml | 169 | latinsyndicate_grenademonkey | Armament@ELITE | LatinMonkeyGrenade3 |
| ContentPacks/RedAlert2Mod/Syndicate/yaml/infantry.yaml | 181 | latinsyndicate_grenademonkey | Armament@GARRISONEDELITE | LatinMonkeyGrenade3 |
| ContentPacks/RedAlert2Mod/Syndicate/yaml/naval.yaml | 175 | rammax.latin | Armament@ELITE | Rammax_Sabot |
| ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 978 | latinsyndicate_missiletruck | Armament@PRIMARYELITE | RA2RTruckRocket |
| ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 1049 | latinsyndicate_burrito | Armament@PRIMARYELITE | RA2RBurritoRocket |
| ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml | 1118 | latinsyndicate_lars | Armament@PRIMARYELITE | RA2LarsRocket |
| ContentPacks/TiberianSun/Nod/yaml/naval.yaml | 193 | ts_nod_rayboat | Armament@ELITE | TSStankTibTusk |
| rules/redalert2.yaml | 2590 | ra2_c_ifv | Armament@elite | RA2GattlingMG2 |
| rules/redalert2.yaml | 2608 | ra2_c_ifv | Armament@eliteAA | RA2GattlingMG2_AA |
| rules/redalert2.yaml | 2668 | ra2_c_hum | Armament@elite | RA2GattlingMG2 |

## X2 — EMP weapons not following _EMP convention
| File | Line | Weapon |
|---|---|---|
| ContentPacks/TiberianDawn/GDI/yaml/weapons.yaml | 723 | EMPGrenade |
| ContentPacks/TiberianDawn/GDI/yaml/weapons.yaml | 819 | EMPGrenadeExplode |
| weapons/darkreign.yaml | 1324 | DR_EMP_Device |
| weapons/generals.yaml | 1592 | USA_EMP_PatriotMissAG |
| weapons/generals.yaml | 1617 | USA_EMP_PatriotMissAA |
| weapons/outpost2.yaml | 308 | eden_EMP_GP |
| weapons/outpost2.yaml | 765 | plymouth_EMP_Tiger |
| weapons/shockwave.yaml | 1196 | SUSA_EMP_MissileDefenderAG |
| weapons/shockwave.yaml | 1205 | SUSA_EMP_MissileDefenderStructure |
| weapons/shockwave.yaml | 1224 | SUSA_EMP_MissileDefenderGarrisoned |

## X3 — AA-only weapons not following _AA convention
| File | Line | Weapon | ValidTargets |
|---|---|---|---|
| ContentPacks/RedAlert/Japan/yaml/weapons.yaml | 358 | BallistaSingleShotAir | Air |
| ContentPacks/RedAlert/Japan/yaml/weapons.yaml | 366 | BallistaSingleShotAirEnergized | Air |
| ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml | 977 | LaserBuggy2_AAInferno | Air |
| ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml | 983 | LaserBuggy2_AABurning | Air |
| ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 920 | CabalLaserBoatLaserAA | Air |
| ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1245 | CabalManticoreMissilesAA | Air |
| ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 568 | TSMammothTusk2 | Air |
| weapons/darkreign.yaml | 404 | DRBionWeaponAA | Air |

## X4 — Weapons with deprecated E suffix (informational)
| File | Line | Weapon |
|---|---|---|
| weapons/shockwave.yaml | 78 | SUSABurtonSniperHE |
| weapons/shockwave.yaml | 232 | SUSAMLRSHE |

