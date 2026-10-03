# Missile role and class triage

This is a read-only review receipt. Strict findings are policy lanes;
they do not authorize a family, target-mask, damage or Versus edit.

## Current counts

| code | review lane | count |
|---|---|---:|
| R1 | ground-only route flying MissileAA/AP | 15 |
| R2 | air-only route flying MissileHE/AP | 8 |
| R3 | dual-domain route flying MissileHE/AA | 4 |
| R4 | MissileHE reachable against Air | 4 |
| custom | recipient or non-domain selector | 27 |

Scanned **378** concrete weapons; **280** recognized role/family pairs conform. The receipt also records **3** explicit policy question(s).

## R1 strict findings

| weapon | role | flies | expected | consumers | resolved family source |
|---|---|---|---|---:|---|
| `DredMissile` | ground | MissileAP | MissileHE | 1 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2770` |
| `RA2SCUD` | ground | MissileAP | MissileHE | 4 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2770` |
| `RA2SCUDELITE` | ground | MissileAP | MissileHE | 1 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2770` |
| `RA2SCUD_fire` | ground | MissileAP | MissileHE | 2 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2770` |
| `RA2SCUD_rad` | ground | MissileAP | MissileHE | 2 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2811` |
| `RA2SCUD_tesla` | ground | MissileAP | MissileHE | 2 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2770` |
| `SandmarineTuskFire` | ground | MissileAP | MissileHE | 4 | `mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml:956` |
| `SandmarineTuskTwin` | ground | MissileAP | MissileHE | 4 | `mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml:918` |
| `V3Explode` | ground | MissileAP | MissileHE | 9 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2869` |
| `d2k_tyrant` | ground | MissileAP | MissileHE | 0 | `mods/cameo/weapons/weapons.yaml:4615` |
| `oBazooka` | ground | MissileAP | MissileHE | 0 | `mods/cameo/ContentPacks/D2k/Shared/yaml/weapons.yaml:228` |
| `oDeviatorMissile` | ground | MissileAP | MissileHE | 0 | `mods/cameo/weapons/d2k.yaml:2003` |
| `oRocket` | ground | MissileAP | MissileHE | 0 | `mods/cameo/weapons/d2k.yaml:1946` |
| `tkmfirerockets` | ground | MissileAP | MissileHE | 3 | `mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml:147` |
| `tkmkatyushalalauncherrocketsfire` | ground | MissileAP | MissileHE | 1 | `mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml:824` |

Each row retains its valid/invalid target fields, inheritance chain and consumer routes in the JSON receipt.

## R2 strict findings

| weapon | role | flies | expected | consumers | resolved family source |
|---|---|---|---|---:|---|
| `BallistaSingleShotAirEnergized` | air | MissileAP | MissileAA | 1 | `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml:598` |
| `ConsortiumMissileSystem` | air | MissileAP | MissileAA | 1 | `mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml:176` |
| `ConsortiumMissileSystem_EMP` | air | MissileAP | MissileAA | 1 | `mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml:206` |
| `D2K_Rocket_AA` | air | MissileAP | MissileAA | 1 | `mods/cameo/weapons/d2k.yaml:335` |
| `LatinAADefenderCannon` | air | MissileAP | MissileAA | 2 | `mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml:1764` |
| `Rocket_stealth_AA` | air | MissileAP | MissileAA | 0 | `mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml:2515` |
| `d2k_APC_AA` | air | MissileAP | MissileAA | 0 | `mods/cameo/weapons/d2k.yaml:535` |
| `d2k_APCo_AA` | air | MissileAP | MissileAA | 0 | `mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml:2515` |

Each row retains its valid/invalid target fields, inheritance chain and consumer routes in the JSON receipt.

## R3 strict findings

| weapon | role | flies | expected | consumers | resolved family source |
|---|---|---|---|---:|---|
| `CabalAscendedRockets` | both | MissileHE | MissileAP | 2 | `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml:2343`, `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml:2346` |
| `JimRaynorMachineGun` | both | MissileHE | MissileAP | 3 | `mods/cameo/ContentPacks/StarCraft/Terran/yaml/weapons.yaml:54` |
| `WaveforceCannon` | both | MissileHE | MissileAP | 1 | `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml:1937` |
| `WaveforceCannonChargedLaser` | both | MissileHE | MissileAP | 2 | `mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml:898` |

Each row retains its valid/invalid target fields, inheritance chain and consumer routes in the JSON receipt.

## R4 strict findings

| weapon | role | flies | expected | consumers | resolved family source |
|---|---|---|---|---:|---|
| `CabalAscendedRockets` | both | MissileHE | MissileAP | 2 | `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml:2343`, `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml:2346` |
| `JimRaynorMachineGun` | both | MissileHE | MissileAP | 3 | `mods/cameo/ContentPacks/StarCraft/Terran/yaml/weapons.yaml:54` |
| `WaveforceCannon` | both | MissileHE | MissileAP | 1 | `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml:1937` |
| `WaveforceCannonChargedLaser` | both | MissileHE | MissileAP | 2 | `mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml:898` |

Each row retains its valid/invalid target fields, inheritance chain and consumer routes in the JSON receipt.

## Custom selectors

| weapon | selector | bucket | consumers |
|---|---|---|---:|
| `AsianSmallTorpedo` | `Water, Underwater, Bridge` | water-or-underwater | 2 |
| `CycloneRocketsLockOn` | `lockon` | recipient-type-selector | 1 |
| `Fremen_RPG` | `Air, Vehicle, Structure / invalid Infantry` | recipient-type-selector | 1 |
| `FutureMicrotorpedos` | `Water, Underwater, Bridge` | water-or-underwater | 2 |
| `MammothTusk` | `Ground, Water, Infantry, Monster, Air` | recipient-type-selector | 1 |
| `MammothTuskTesla` | `Ground, Water, Infantry, Monster, Air / invalid wall` | recipient-type-selector | 0 |
| `MammothTuskTeslaInfantryFragment1` | `Ground, Water, Infantry, Monster, Air / invalid wall` | recipient-type-selector | 0 |
| `MammothTuskTeslaInfantryFragment1_ExplicitDamage21of20` | `Ground, Water, Infantry, Monster, Air / invalid wall` | recipient-type-selector | 0 |
| `MammothTuskTeslaInfantryFragment2` | `Ground, Water, Infantry, Monster, Air / invalid wall` | recipient-type-selector | 0 |
| `NaxShoeRocket` | `Ground, Water, Ship, Submarine` | custom-vocabulary | 1 |
| `NaxTorpTube` | `Water, Underwater, Bridge` | water-or-underwater | 0 |
| `RA2AkulaRockets` | `Ground, Water, Ship, Submarine` | custom-vocabulary | 1 |
| `RA2FreedomRocket` | `Ground, Water, Air, Garrisoned` | recipient-type-selector | 2 |
| `RA2FreedomRocket_elite` | `Ground, Water, Air, Garrisoned` | recipient-type-selector | 2 |
| `RA2TorpTube` | `Water, Underwater, Bridge` | water-or-underwater | 2 |
| `RA2TorpTube_elite` | `Water, Underwater, Bridge` | water-or-underwater | 2 |
| `RA2Virusgun3` | `Ground, Ship, Garrisoned` | recipient-type-selector | 2 |
| `RA2Virusgun_elite` | `Ground, Ship, Garrisoned` | recipient-type-selector | 2 |
| `YRBoomerTorpedo` | `Water, Underwater, Bridge` | water-or-underwater | 1 |
| `ra1_soviets_mammothtank_mammothtusk` | `Ground, Water, Infantry, Monster, Air` | recipient-type-selector | 2 |
| `ra1_soviets_mammothtank_mammothtusktesla` | `Ground, Water, Infantry, Monster, Air / invalid wall` | recipient-type-selector | 2 |
| `ra1_soviets_monstertank_missile_tesla` | `Ground, Water, Infantry, Monster, Air / invalid wall` | recipient-type-selector | 1 |
| `ra1_soviets_siegemammothtank_mammothtusk2` | `Ground, Water, Infantry, Monster, Air / invalid wall` | recipient-type-selector | 1 |
| `ra1_soviets_submarine_torpedo` | `Water, Underwater, Bridge` | water-or-underwater | 1 |
| `ra1_soviets_submarine_torpedo_thermobaric` | `Water, Underwater, Bridge` | water-or-underwater | 1 |
| `td_nod_attacksubmarine_nodtorptube` | `Water, Underwater, Bridge` | water-or-underwater | 1 |
| `td_nod_attacksubmarine_nodtorptubeblackmarket` | `Water, Underwater, Bridge` | water-or-underwater | 1 |

Custom selectors need recipient-type or runtime evidence; they are not silently classified as ground, air or dual.

## Explicit policy questions

| subject | weapon | resolved selector | status |
|---|---|---|---|
| V2 Tesla SCUD parent Air role | `ra1_soviets_v2rocketlauncher_scudtesla` | `Ground, Water` | POLICY_REVIEW_REQUIRED |
| V2 Tesla SCUD parent Air role | `ra1_soviets_v2rocketlauncher_scudteslafragment1` | `Ground, Water` | POLICY_REVIEW_REQUIRED |
| V2 Tesla SCUD parent Air role | `ra1_soviets_v2rocketlauncher_scudteslafragment2` | `Ground, Water` | POLICY_REVIEW_REQUIRED |

The V2 Tesla SCUD row preserves the SCUD inheritance and Air exclusions so a parent-role decision can be made explicitly.

## Limits

- A consumer route is reachability evidence, not proof of active combat activation.
- Custom recipient tags, spawned actors, map-local weapons and runtime target filters remain unresolved.
- The receipt proposes no family, ValidTargets, InvalidTargets, damage, projectile or Versus edit.

JSON receipt: `docs/audit/latest/missile_role_triage_20260911.json`.
