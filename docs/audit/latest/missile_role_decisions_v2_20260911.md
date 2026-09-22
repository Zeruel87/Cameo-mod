# Missile role decision packet

**Review-only.** This packet groups the raw role audit by concrete weapon
and makes the next decision lane explicit. It does not select a family,
change a target mask, or authorize YAML/runtime work.

## Summary

- Unique strict weapons: **27** (raw R1-R4 rows: **31**; R3/R4 duplicates are merged).
- Custom selectors: **27**; explicit policy questions: **3**.

| decision lane | count | meaning |
|---|---:|---|
| DUAL_DOMAIN_ABSOLUTE_RULE | 4 | Both-domain route; MissileHE-against-Air also violates the explicit never rule. Review the complete consumer closure before choosing AP. |
| DUAL_DOMAIN_ROLE_REVIEW | 0 | Both-domain route with HE/AA family mismatch. A role choice changes armor and delivery behavior for every consumer. |
| SINGLE_DOMAIN_ROLE_REVIEW | 23 | Literal ground-only or air-only route, but a family correction still changes armor response and projectile delivery. |

## Strict cases

| priority | weapon | audit codes | role | family | expected | consumers | source |
|---|---|---|---|---|---|---:|---|
| critical | `CabalAscendedRockets` | R3, R4 | both | MissileHE | MissileAP | 2 | `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml:2292` |
| critical | `JimRaynorMachineGun` | R3, R4 | both | MissileHE | MissileAP | 3 | `mods/cameo/ContentPacks/StarCraft/Terran/yaml/weapons.yaml:32` |
| critical | `WaveforceCannon` | R3, R4 | both | MissileHE | MissileAP | 1 | `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml:1914` |
| critical | `WaveforceCannonChargedLaser` | R3, R4 | both | MissileHE | MissileAP | 2 | `mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml:875` |
| normal | `BallistaSingleShotAirEnergized` | R2 | air | MissileAP | MissileAA | 1 | `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml:582` |
| normal | `ConsortiumMissileSystem` | R2 | air | MissileAP | MissileAA | 1 | `mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml:141` |
| normal | `ConsortiumMissileSystem_EMP` | R2 | air | MissileAP | MissileAA | 1 | `mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/weapons.yaml:188` |
| normal | `D2K_Rocket_AA` | R2 | air | MissileAP | MissileAA | 1 | `mods/cameo/weapons/d2k.yaml:314` |
| normal | `DredMissile` | R1 | ground | MissileAP | MissileHE | 1 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2873` |
| high | `LatinAADefenderCannon` | R2 | air | MissileAP | MissileAA | 2 | `mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml:1735` |
| high | `RA2SCUD` | R1 | ground | MissileAP | MissileHE | 4 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2740` |
| normal | `RA2SCUDELITE` | R1 | ground | MissileAP | MissileHE | 1 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2843` |
| high | `RA2SCUD_fire` | R1 | ground | MissileAP | MissileHE | 2 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2827` |
| high | `RA2SCUD_rad` | R1 | ground | MissileAP | MissileHE | 2 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2777` |
| high | `RA2SCUD_tesla` | R1 | ground | MissileAP | MissileHE | 2 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2835` |
| normal | `Rocket_stealth_AA` | R2 | air | MissileAP | MissileAA | 0 | `mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml:2496` |
| high | `SandmarineTuskFire` | R1 | ground | MissileAP | MissileHE | 4 | `mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml:932` |
| high | `SandmarineTuskTwin` | R1 | ground | MissileAP | MissileHE | 4 | `mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml:883` |
| high | `V3Explode` | R1 | ground | MissileAP | MissileHE | 9 | `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml:2861` |
| normal | `d2k_APC_AA` | R2 | air | MissileAP | MissileAA | 0 | `mods/cameo/weapons/d2k.yaml:531` |
| normal | `d2k_APCo_AA` | R2 | air | MissileAP | MissileAA | 0 | `mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml:2528` |
| normal | `d2k_tyrant` | R1 | ground | MissileAP | MissileHE | 0 | `mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml:2457` |
| normal | `oBazooka` | R1 | ground | MissileAP | MissileHE | 0 | `mods/cameo/weapons/d2k.yaml:1936` |
| normal | `oDeviatorMissile` | R1 | ground | MissileAP | MissileHE | 0 | `mods/cameo/weapons/d2k.yaml:1991` |
| normal | `oRocket` | R1 | ground | MissileAP | MissileHE | 0 | `mods/cameo/weapons/d2k.yaml:1939` |
| high | `tkmfirerockets` | R1 | ground | MissileAP | MissileHE | 3 | `mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml:139` |
| normal | `tkmkatyushalalauncherrocketsfire` | R1 | ground | MissileAP | MissileHE | 1 | `mods/cameo/ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml:797` |

Every row retains inheritance, field provenance and consumer route details in the JSON receipt. A consumer count of zero means no resolved actor `Weapon:` route was found; it is not proof that the definition is unreachable.

## Decision order

1. Clear the dual-domain MissileHE/Air absolute-rule rows first.
2. Review dual-domain and multi-consumer closures as complete weapon/actor groups.
3. Review single-domain rows only after confirming the intended armor and delivery change.
4. Handle custom selectors and the V2 Tesla SCUD parent as separate recipient/runtime policy lanes.

## Custom selector lanes

| bucket | selectors | consumer routes |
|---|---:|---:|
| custom-vocabulary | 2 | 2 |
| recipient-type-selector | 15 | 17 |
| water-or-underwater | 10 | 13 |

Custom recipient vocabularies, naval selectors and invalid-tag combinations need recipient/runtime evidence; they do not enter the three-domain conversion rule automatically.

## Explicit policy questions

| subject | weapon | selector | consumers | status |
|---|---|---|---:|---|
| V2 Tesla SCUD parent Air role | `ra1_soviets_v2rocketlauncher_scudtesla` | `Ground, Water` | 2 | POLICY_REVIEW_REQUIRED |
| V2 Tesla SCUD parent Air role | `ra1_soviets_v2rocketlauncher_scudteslafragment1` | `Ground, Water` | 0 | POLICY_REVIEW_REQUIRED |
| V2 Tesla SCUD parent Air role | `ra1_soviets_v2rocketlauncher_scudteslafragment2` | `Ground, Water` | 0 | POLICY_REVIEW_REQUIRED |

## Guardrails

- This packet is review-only; it selects no canonical family.
- Do not infer combat activation from a Weapon consumer route alone.
- Do not change ValidTargets, InvalidTargets, damage, projectile, or Versus values from this receipt.
- Existing design holds and preserve candidates remain maintainer decisions; this packet does not override them.

Source receipt: `C:/Users/Blackrobe/repo/Cameo-mod-worktrees/overnight-integration-20260910/docs/audit/latest/missile_role_triage_v2_20260911.json`.
