# Weapon suffix audit (DESIGN.md §1)

X1 elite weapons not ending _elite: **2** (+25 exempt shared-rung weapons, Ruling 2)
X2 EMP weapons not ending _EMP: **0**
X3 AA weapons not ending _AA: **1**
X4 deprecated E suffix (informational): **0**
X5 suffix ordering violations: **0**

## X1 — Elite weapons not following _elite convention
| File | Line | Actor | Trait | Weapon |
|---|---|---|---|---|
| ContentPacks/RedAlert2/Shared/yaml/misc.yaml | 2291 | ra2_c_ifv | Armament@eliteAA | RA2GattlingMG2_AA |
| rules/redalert2.yaml | 2594 | ra2_c_ifv | Armament@eliteAA | RA2GattlingMG2_AA |

## X3 — AA-only weapons not following _AA convention
| File | Line | Weapon | ValidTargets |
|---|---|---|---|
| ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml | 1675 | ConsortiumMissileSystem | Air |

