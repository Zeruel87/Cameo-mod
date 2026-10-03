# Sonic/Cryo and status route inventory

**Read-only active-ruleset receipt.** This inventory records declared emitters,
actor receivers and condition consumers. It does not infer hit probability,
uptime, eligibility, resistance, damage value or pricing.

## Coverage

- Active concrete weapons checked by the companion physical-state audit: **2,448**.
- Declared condition/status names with an active direct-armament emitter: **26**.
- Physical-state templates checked: **6** (Flame and Chemical, three tiers each).
- Physical-state audit: **PASS**; no active weapon combines a damage-scaled meter
  with a fixed `ApplyPhysicalState` route for the same meter.

## SonicDebuff

`SonicDebuff` has **12** direct-armament emitters and **1,545** resolved actor
traits consuming the condition. Consumer trait types are `DamageMultiplier`,
`SpeedMultiplier` and `WithColoredOverlay`.

Emitters:

`Future_MBT_DebuffLaser`, `Future_MBT_DebuffLaser_elite`, `KodiakCannonSonic`,
`td_gdi_predatortank_gdipredatorbluelaser`, `TSAssaultCannonSonic`,
`TSAssaultCannonTalSonic`, `TSBombSonic`, `TSGrenadeSonic`, `TSHellfireSonic`,
`TSSonicZapWeaponSonic`, `TSVulcanGunSonic`, `TSZoneHellfireSonic`.

The inventory confirms the Sonic delivery routes and their declared condition
consumers; it does not turn a slow or damage multiplier into a scalar DPS vote.

## CryoFreeze

`CryoFreeze` has one direct-armament emitter, `HueyCryoMissiles`, bound to
`tkm_iroquois` `Armament@PRIMARYNATO` under
`tkm_upgrade_cryorocketsupgrade`. Its declaration is:

| field | value |
|---|---|
| `Duration` | `125` |
| `Range` | `1250` |
| `ValidTargets` | `Ground, Water, Air` |
| `ValidRelationships` | `Enemy, Neutral, Ally` |

No concrete `ExternalCondition` receiver declares `CryoFreeze` directly, but
the condition token is consumed by `CryoFogEmitter`,
`DamageMultiplierProportionalToPhysicalState`, `SmokeParticleEmitter` and
`WithIdleOverlay` traits. This is a condition-token route, not evidence that
the emitter reaches every target or that the proportional multiplier is always
active.

## Corrosion cross-check

`corroded` has **11** direct-armament emitters, **817** resolved actor receivers
and `ChangesHealth`, `DamageMultiplier`, `SpeedMultiplier`, `Targetable` and
`WithColoredOverlay` consumers. It remains a separate status lane from Sonic
and Cryo valuation.

## Limits

The JSON receipt retains all 26 status rows, full emitter/receiver fields,
`RequiresCondition` expressions and direct bindings. Receiver presence does not
prove target-mask or relationship eligibility. Script grants, spawned actors,
secondary routes, source caps, resistances, duration refresh and runtime
activation remain outside this static inventory. No status cost, upgrade price,
armor value or gameplay change is proposed.

JSON receipt: `docs/audit/latest/status_effect_inventory_20260911.json`.
