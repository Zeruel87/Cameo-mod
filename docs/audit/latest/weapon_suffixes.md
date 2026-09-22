# Weapon suffix audit (DESIGN.md §1)

X1 elite weapons not ending _elite: **0** (+27 exempt shared-rung weapons, Ruling 2)
X2 EMP weapons not ending _EMP: **0**
X3 AA weapons not ending _AA: **10**
X4 deprecated E suffix (informational): **0**
X5 suffix ordering violations: **0**

## X3 — AA-only weapons not following _AA convention
| File | Line | Weapon | ValidTargets |
|---|---|---|---|
| ContentPacks/RedAlert/Japan/yaml/weapons.yaml | 551 | BallistaSingleShotAir | Air |
| ContentPacks/RedAlert/Japan/yaml/weapons.yaml | 559 | BallistaSingleShotAirEnergized | Air |
| ContentPacks/StarCraft/Terran/yaml/weapons.yaml | 1054 | GoliathMk2Rockets | Air |
| ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml | 1025 | td_nod_buggymkii_laserbuggy2_AAinferno | Air |
| ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml | 1031 | td_nod_buggymkii_laserbuggy2_AAburning | Air |
| ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1530 | CabalLaserBoatLaserAA | Air |
| ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1876 | CabalManticoreMissilesAA | Air |
| ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 632 | TSMammothTusk2 | Air |
| weapons/darkreign.yaml | 404 | DRBionWeaponAA | Air |
| weapons/tiberiansun.yaml | 1182 | TSChemAdatsMissileAA |  |

