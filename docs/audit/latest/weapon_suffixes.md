# Weapon suffix audit (DESIGN.md §1)

X1 elite weapons not ending _elite: **0** (+27 exempt shared-rung weapons, Ruling 2)
X2 EMP weapons not ending _EMP: **0**
X3 AA weapons not ending _AA: **10**
X4 deprecated E suffix (informational): **0**
X5 suffix ordering violations: **0**

## X3 — AA-only weapons not following _AA convention
| File | Line | Weapon | ValidTargets |
|---|---|---|---|
| ContentPacks/RedAlert/Japan/yaml/weapons.yaml | 526 | BallistaSingleShotAir | Air |
| ContentPacks/RedAlert/Japan/yaml/weapons.yaml | 534 | BallistaSingleShotAirEnergized | Air |
| ContentPacks/StarCraft/Terran/yaml/weapons.yaml | 1036 | GoliathMk2Rockets | Air |
| ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml | 935 | LaserBuggy2_AAInferno | Air |
| ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml | 941 | LaserBuggy2_AABurning | Air |
| ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1460 | CabalLaserBoatLaserAA | Air |
| ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1791 | CabalManticoreMissilesAA | Air |
| ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 610 | TSMammothTusk2 | Air |
| weapons/darkreign.yaml | 404 | DRBionWeaponAA | Air |
| weapons/tiberiansun.yaml | 1169 | TSChemAdatsMissileAA |  |

