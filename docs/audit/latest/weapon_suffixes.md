# Weapon suffix audit (DESIGN.md §1)

X1 elite weapons not ending _elite: **0** (+27 exempt shared-rung weapons, Ruling 2)
X2 EMP weapons not ending _EMP: **10**
X3 AA weapons not ending _AA: **10**
X4 deprecated E suffix (informational): **2**
X5 suffix ordering violations: **0**

## X2 — EMP weapons not following _EMP convention
| File | Line | Weapon |
|---|---|---|
| ContentPacks/TiberianDawn/GDI/yaml/weapons.yaml | 884 | EMPGrenade |
| ContentPacks/TiberianDawn/GDI/yaml/weapons.yaml | 982 | EMPGrenadeExplode |
| weapons/darkreign.yaml | 1324 | DR_EMP_Device |
| weapons/generals.yaml | 1592 | USA_EMP_PatriotMissAG |
| weapons/generals.yaml | 1617 | USA_EMP_PatriotMissAA |
| weapons/outpost2.yaml | 382 | eden_EMP_GP |
| weapons/outpost2.yaml | 826 | plymouth_EMP_Tiger |
| weapons/shockwave.yaml | 1196 | SUSA_EMP_MissileDefenderAG |
| weapons/shockwave.yaml | 1205 | SUSA_EMP_MissileDefenderStructure |
| weapons/shockwave.yaml | 1224 | SUSA_EMP_MissileDefenderGarrisoned |

## X3 — AA-only weapons not following _AA convention
| File | Line | Weapon | ValidTargets |
|---|---|---|---|
| ContentPacks/RedAlert/Japan/yaml/weapons.yaml | 551 | BallistaSingleShotAir | Air |
| ContentPacks/RedAlert/Japan/yaml/weapons.yaml | 559 | BallistaSingleShotAirEnergized | Air |
| ContentPacks/StarCraft/Terran/yaml/weapons.yaml | 1108 | GoliathMk2Rockets | Air |
| ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml | 984 | LaserBuggy2_AAInferno | Air |
| ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml | 990 | LaserBuggy2_AABurning | Air |
| ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1529 | CabalLaserBoatLaserAA | Air |
| ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1875 | CabalManticoreMissilesAA | Air |
| ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 640 | TSMammothTusk2 | Air |
| weapons/darkreign.yaml | 404 | DRBionWeaponAA | Air |
| weapons/tiberiansun.yaml | 1169 | TSChemAdatsMissileAA |  |

## X4 — Weapons with deprecated E suffix (informational)
| File | Line | Weapon |
|---|---|---|
| weapons/shockwave.yaml | 78 | SUSABurtonSniperHE |
| weapons/shockwave.yaml | 232 | SUSAMLRSHE |

