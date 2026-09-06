# Remaining reachable weapon decisions

This report compresses the honest unreviewed backlog into inheritance
families. It is a review queue, not conversion authority. Reviewed exact
composites remain in the raw structural count but are excluded here.
Three independent reviews found no mechanically exact fold in this
remaining set; each row requires an armor, geometry, targeting, state,
or progression decision before its live behavior can be changed.
The player-facing recommendation for every family is maintained in
`docs/design/WEAPON_REDESIGN_RECOMMENDATIONS.md`.

- Raw reachable stacked definitions: **240**
- Exact reviewed composites: **226**
- Unreviewed reachable definitions: **14**
- Unreviewed inheritance families: **12**

The buckets describe why automatic consolidation is unsafe. They do not
decide the eventual damage family.
A bold family label is an unreviewed planning root; only the definitions
listed after the colon remain open decisions.

| decision bucket | families | definitions |
|---|---:|---:|
| target and state routing | 0 | 0 |
| target routing | 0 | 0 |
| state delivery | 2 | 2 |
| legacy compatibility | 0 | 0 |
| numbered warhead key | 0 | 0 |
| no special mechanical signal | 10 | 12 |

## Target And State Routing (0 families)


## Target Routing (0 families)


## State Delivery (2 families)

- **`TSSonicZapWeapon`** (1; state or integrity): `TSSonicZapWeapon`
  - active users: TiberianSun / GDI: Disruptor (`ts_gdi_disruptor`)
  - mains `Magic_Heavy + Tesla_Heavy`: `TSSonicZapWeapon`
- **`Type97PlasmaCannon`** (1; state or integrity): `Type97PlasmaCannon`
  - active users: RedAlert / Japan: Chi-Ha Heavy Tank (`japan_chihaheavytank`)
  - mains `CannonHE_Heavy + Railgun_Heavy + Tesla_Heavy`: `Type97PlasmaCannon`

## Legacy Compatibility (0 families)


## Numbered Warhead Key (0 families)


## No Special Mechanical Signal (10 families)

- **`TSTacticalMissileDamage`** (2; none detected): `TSTacticalChemMissileDamage`, `TSTacticalMissileDamage`
  - active users: shared rules: Casino Crate (`casinocrate`); TiberianSun / Nod: Missile Silo (`ts_nod_missilesilo`)
  - transitive delivery: `TSTacticalChemMissile`, `TSTacticalMissile`
  - mains `LightMissile + MediumMissile`: `TSTacticalChemMissileDamage`, `TSTacticalMissileDamage`
- **`d2k_air_drone_guns`** (2; none detected): `d2k_air_drone_guns`, `d2k_air_drone_guns_upgrade`
  - active users: D2k / Ixian: Ixian Air Drone (`ixian_airdrone`)
  - mains `Bullet_Light + Bullet_Medium + CannonHE_Heavy + MissileAP_Heavy`: `d2k_air_drone_guns_upgrade`
  - mains `Bullet_Light + Bullet_Medium + MissileAP_Heavy`: `d2k_air_drone_guns`
- **`AlliedTankDestroyerCannon`** (1; none detected): `AlliedTankDestroyerCannon`
  - active users: RedAlert / Allies: Allied Tank Destroyer (`ra1_allies_alliedtankdestroyer`)
  - mains `CannonAP_Light + CannonHE_Medium`: `AlliedTankDestroyerCannon`
- **`Aphid_AA`** (1; none detected): `Aphid_AA`
  - active users: RedAlert / Allies: Rapier Jumpjet (`ra1_allies_rapierjumpjet`)
  - mains `Concussion_Medium + MissileHE_Heavy`: `Aphid_AA`
- **`JimRaynorMachineGun`** (1; none detected): `JimRaynorMachineGun`
  - active users: StarCraft / Terran: Jim Raynor (`terran_jimraynor`); StarCraft / Terran: Pythean (`terran_pythean`)
  - mains `CannonHE_Heavy + MissileHE_Heavy`: `JimRaynorMachineGun`
- **`SheridanCannon`** (1; none detected): `SheridanCannon`
  - active users: RedAlert / Allies: Sheridan Assault Tank (`ra1_allies_sheridanassaulttank`)
  - mains `CannonAP_Light + CannonHE_Medium`: `SheridanCannon`
- **`SheridanMissiles`** (1; none detected): `SheridanMissiles`
  - active users: RedAlert / Allies: Sheridan Assault Tank (`ra1_allies_sheridanassaulttank`)
  - mains `MissileHE_Light + MissileHE_Medium`: `SheridanMissiles`
- **`TSBoatcannon`** (1; none detected): `TSBoatcannon`
  - active users: TiberianSun / Forgotten: Cannon Tug (`forgotten_cannonboat`)
  - mains `Concussion_Medium + Demolition_Heavy`: `TSBoatcannon`
- **`TigerCannon`** (1; none detected): `TigerCannon`
  - active users: RedAlert / Shared: Allied Cyber Tank (`ra1_allies_alliedcybertank`); RedAlert / Allies: Allied Tiger Heavy Tank (`ra1_allies_alliedtigerheavytank`)
  - mains `CannonHE_Heavy + CannonHE_Medium`: `TigerCannon`
- **`Type97Cannon`** (1; none detected): `Type97Cannon`
  - active users: RedAlert / Japan: Chi-Ha Heavy Tank (`japan_chihaheavytank`)
  - mains `CannonHE_Heavy + CannonHE_Medium`: `Type97Cannon`

## Maintainer decision shape

For each family, the eventual question is: which authored main defines the unit's role, and may its armor, splash, target route, and state delivery be applied to the full nominal damage? Paid replacements and mixed target routes must be reviewed as complete closures.
