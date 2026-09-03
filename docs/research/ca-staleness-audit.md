# Combined Arms vendor staleness audit

Read-only comparison of Cameo's vendored `OpenRA.Mods.CA` source against the fetched `Inq8/CAmod` checkout.

## Compared revisions

- Upstream Combined Arms: `ab9e477c3db818e91946d4cfdc86e71012966141` (2026-07-30T10:43:27+08:00); Merge remote-tracking branch 'darkademic/dev'
- CA engine default branch (`prep-CA23`): `d3976b8b4b47859971ff61aca62f475f6d21cc1a` (2024-02-24T16:51:56+08:00); Add casing throwing for Armament (Dnqbob)
- Cameo reference only: `61c48022c616dcaad48a6e547e6c052e8e310ef6` (2026-08-20T13:09:04+02:00)

The Cameo and Cameo-engine repositories were not modified.

## Classification summary

| Classification | Count |
|---|---:|
| IDENTICAL | 41 |
| DIVERGED-UPSTREAM-NEWER | 3 |
| DIVERGED-LOCAL | 2 |
| DIVERGED-BOTH | 105 |
| LOCAL-ONLY | 30 |

Classification ignores line endings, whitespace-only changes, and copyright/license header differences. Directional labels use normalized line deltas: upstream-only changes indicate upstream content absent locally; local-only changes indicate Cameo content absent upstream.

## Per-file comparison

| Local file | Upstream counterpart | Match | Classification | Historical vendor match | Upstream commits after match |
|---|---|---|---|---|---:|
| `Activities/AttackCharged.cs` | `Activities/AttackCharged.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Activities/BallisticMissileCAFly.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Activities/CruiseMissileFly.cs` | `Activities/CruiseMissileFly.cs` | relative-path | **DIVERGED-BOTH** | `92c36baa143b` (2024-05-27) | 1 |
| `Activities/Dive.cs` | `Activities/Dive.cs` | relative-path | **DIVERGED-BOTH** | `a6f122fa2423` (2024-05-11) | 2 |
| `Activities/EnterAirstrikeMasterCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Activities/GuidedMissileFly.cs` | `Activities/GuidedMissileFly.cs` | relative-path | **DIVERGED-BOTH** | `a41ab548db80` (2024-05-07) | 2 |
| `Activities/HuntCA.cs` | `Activities/HuntCA.cs` | relative-path | **DIVERGED-BOTH** | `eb4f92cae626` (2025-10-06) | 1 |
| `Activities/InstantTransform.cs` | `Activities/InstantTransform.cs` | relative-path | **DIVERGED-BOTH** | not identified | 11 |
| `Activities/TeleportCA.cs` | `Activities/TeleportCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 14 |
| `AIUtils.cs` | `AIUtils.cs` | relative-path | **DIVERGED-BOTH** | not identified | 11 |
| `Effects/WarheadTrailProjectileEffectCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Graphics/MindControlArc.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Orders/ReleaseSlaveOrderTargeter.cs` | `Orders/ReleaseSlaveOrderTargeter.cs` | relative-path | **DIVERGED-BOTH** | not identified | 6 |
| `Projectiles/LaserZapCA.cs` | `Projectiles/LaserZapCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 6 |
| `Projectiles/LinearPulse.cs` | `Projectiles/LinearPulse.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Projectiles/NukeLaunchInfo.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Projectiles/PlasmaBeam.cs` | `Projectiles/PlasmaBeam.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Projectiles/SpriteAthenaLaser.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Projectiles/WarheadTrailProjectileCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Scripting/MadTankCAGlobal.cs` | `Scripting/MadTankCAGlobal.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Scripting/ReinforcementsCAGlobal.cs` | `Scripting/ReinforcementsCAGlobal.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Air/AttackAircraftCA.cs` | `Traits/Air/AttackAircraftCA.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/Air/DiveOnAttack.cs` | `Traits/Air/DiveOnAttack.cs` | relative-path | **DIVERGED-BOTH** | `a6f122fa2423` (2024-05-11) | 2 |
| `Traits/AirstrikeMasterCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/AirstrikeSlaveCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/Attachable.cs` | `Traits/Attachable.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/AttachableTo.cs` | `Traits/AttachableTo.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 9 |
| `Traits/AttachedAircraft.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/AttachOnCreation.cs` | `Traits/AttachOnCreation.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 2 |
| `Traits/AttachOnTransform.cs` | `Traits/AttachOnTransform.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 3 |
| `Traits/Attack/AttackBomberCA.cs` | `Traits/Air/AttackBomberCA.cs` | filename | **DIVERGED-BOTH** | not identified | 10 |
| `Traits/Attack/AttackFrontalCharged.cs` | `Traits/Attack/AttackFrontalCharged.cs` | relative-path | **DIVERGED-BOTH** | not identified | 12 |
| `Traits/Attack/AttackGarrisonedSP.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/Attack/AttackPrismSupported.cs` | `Traits/Attack/AttackPrismSupported.cs` | relative-path | **DIVERGED-BOTH** | not identified | 4 |
| `Traits/Attack/AttackTurretedCharged.cs` | `Traits/Attack/AttackTurretedCharged.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/BallisticMissileCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/BotModules/BaseBuilderBotModuleCA.cs` | `Traits/BotModules/BaseBuilderBotModuleCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/BotModules/BotLimits.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/BotModules/BotModuleLogic/BaseBuilderQueueManagerCA.cs` | `Traits/BotModules/BotModuleLogic/BaseBuilderQueueManagerCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/BotModules/BuildingRepairBotModuleCA.cs` | `Traits/BotModules/BuildingRepairBotModuleCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 7 |
| `Traits/BotModules/CaptureManagerBotModuleCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/BotModules/HarvesterBotModuleCA.cs` | `Traits/BotModules/HarvesterBotModuleCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/BotModules/LoadGarrisonerBotModuleCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/BotModules/MCVManagerBotModuleCA.cs` | `Traits/BotModules/MCVManagerBotModuleCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 7 |
| `Traits/BotModules/PowerDownBotModuleCA.cs` | `Traits/BotModules/PowerDownBotModuleCA.cs` | relative-path | **DIVERGED-UPSTREAM-NEWER** | not identified | 8 |
| `Traits/BotModules/SquadManagerBotModuleCA.cs` | `Traits/BotModules/SquadManagerBotModuleCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/BotModules/Squads/AttackOrFleeFuzzyCA.cs` | `Traits/BotModules/Squads/AttackOrFleeFuzzyCA.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/BotModules/Squads/SquadCA.cs` | `Traits/BotModules/Squads/SquadCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 17 |
| `Traits/BotModules/Squads/StateMachineCA.cs` | `Traits/BotModules/Squads/StateMachineCA.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/BotModules/Squads/States/AirStatesCA.cs` | `Traits/BotModules/Squads/States/AirStatesCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/BotModules/Squads/States/GroundStatesCA.cs` | `Traits/BotModules/Squads/States/GroundStatesCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/BotModules/Squads/States/NavyStatesCA.cs` | `Traits/BotModules/Squads/States/NavyStatesCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 19 |
| `Traits/BotModules/Squads/States/ProtectionStatesCA.cs` | `Traits/BotModules/Squads/States/ProtectionStatesCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 15 |
| `Traits/BotModules/Squads/States/StateBaseCA.cs` | `Traits/BotModules/Squads/States/StateBaseCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 16 |
| `Traits/BotModules/UnitBuilderBotModuleCA.cs` | `Traits/BotModules/UnitBuilderBotModuleCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/BotModules/UnitCompositionsBotModule.cs` | `Traits/BotModules/UnitCompositionsBotModule.cs` | relative-path | **DIVERGED-BOTH** | not identified | 4 |
| `Traits/CashHackable.cs` | `Traits/CashHackable.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/ChangesHealthVersus.cs` | `Traits/ChangesHealthVersus.cs` | relative-path | **DIVERGED-BOTH** | not identified | 2 |
| `Traits/ChargingSelfDestruct.cs` | `Traits/ChargingSelfDestruct.cs` | relative-path | **DIVERGED-BOTH** | not identified | 9 |
| `Traits/ChronoshiftableCA.cs` | `Traits/ChronoshiftableCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/Conditions/GrantChargingCondition.cs` | `Traits/Conditions/GrantChargingCondition.cs` | relative-path | **DIVERGED-BOTH** | not identified | 3 |
| `Traits/Conditions/GrantConditionOnAttackCA.cs` | `Traits/Conditions/GrantConditionOnAttackCA.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 2 |
| `Traits/Conditions/GrantConditionOnBotOwnerCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/Conditions/GrantConditionOnDamage.cs` | `Traits/Conditions/GrantConditionOnDamage.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Conditions/GrantConditionOnFogEnabled.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/Conditions/GrantConditionOnHealingReceived.cs` | `Traits/Conditions/GrantConditionOnHealingReceived.cs` | relative-path | **DIVERGED-LOCAL** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/Conditions/GrantConditionOnOrders.cs` | `Traits/Conditions/GrantConditionOnOrders.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 5 |
| `Traits/Conditions/GrantConditionOnPrerequisiteCA.cs` | `Traits/Conditions/GrantConditionOnPrerequisiteCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 4 |
| `Traits/Conditions/GrantDelayedCondition.cs` | `Traits/Conditions/GrantDelayedCondition.cs` | relative-path | **DIVERGED-BOTH** | not identified | 5 |
| `Traits/Conditions/GrantStackingCondition.cs` | `Traits/Conditions/GrantStackingCondition.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/Conditions/GrantThermalCondition.cs` | `Traits/Conditions/GrantThermalCondition.cs` | relative-path | **DIVERGED-BOTH** | not identified | 2 |
| `Traits/Conditions/GrantTimedConditionOnCargoAction.cs` | `Traits/Conditions/GrantTimedConditionOnCargoAction.cs` | relative-path | **DIVERGED-BOTH** | not identified | 5 |
| `Traits/Conditions/GrantTimedConditionOnCrushWarning.cs` | `Traits/Conditions/GrantTimedConditionOnCrushWarning.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Conditions/UnloadOnCondition.cs` | `Traits/Conditions/UnloadOnCondition.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 2 |
| `Traits/ConvertsDamageToHealth.cs` | `Traits/ConvertsDamageToHealth.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 2 |
| `Traits/CruiseMissile.cs` | `Traits/CruiseMissile.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/CustomRadarColor.cs` | `Traits/CustomRadarColor.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/DeployOnAttack.cs` | `Traits/DeployOnAttack.cs` | relative-path | **DIVERGED-UPSTREAM-NEWER** | not identified | 8 |
| `Traits/DetonateWeaponOnDeploy.cs` | `Traits/DetonateWeaponOnDeploy.cs` | relative-path | **DIVERGED-BOTH** | not identified | 6 |
| `Traits/DoesNotBlock.cs` | `Traits/DoesNotBlock.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/GivesExperienceToMaster.cs` | `Traits/GivesExperienceToMaster.cs` | relative-path | **DIVERGED-BOTH** | not identified | 8 |
| `Traits/GuardsSelection.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/GuidedMissile.cs` | `Traits/GuidedMissile.cs` | relative-path | **DIVERGED-BOTH** | `a41ab548db80` (2024-05-07) | 3 |
| `Traits/HarvesterBalancer.cs` | `Traits/HarvesterBalancer.cs` | relative-path | **DIVERGED-BOTH** | not identified | 9 |
| `Traits/IHasParallelQueueSlots.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/ImmobileWithFacing.cs` | `Traits/ImmobileWithFacing.cs` | relative-path | **DIVERGED-BOTH** | not identified | 4 |
| `Traits/Infiltration/InfiltrateForSupportPowerCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/Infiltration/InfiltrateToAttach.cs` | `Traits/Infiltration/InfiltrateToAttach.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 4 |
| `Traits/InstantTransforms.cs` | `Traits/InstantTransforms.cs` | relative-path | **DIVERGED-BOTH** | not identified | 3 |
| `Traits/KeepsDistance.cs` | `Traits/KeepsDistance.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 2 |
| `Traits/MadTankCA.cs` | `Traits/MadTankCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 17 |
| `Traits/MassEnterableCargo.cs` | `Traits/MassEnterableCargo.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/MassEntersCargo.cs` | `Traits/MassEntersCargo.cs` | relative-path | **DIVERGED-BOTH** | not identified | 5 |
| `Traits/MindControllable.cs` | `Traits/MindControllable.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/MindControllableProgressBar.cs` | `Traits/MindControllableProgressBar.cs` | relative-path | **DIVERGED-BOTH** | not identified | 3 |
| `Traits/MindController.cs` | `Traits/MindController.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/MindControllerCapacityModifier.cs` | `Traits/MindControllerCapacityModifier.cs` | relative-path | **DIVERGED-BOTH** | not identified | 3 |
| `Traits/MindControllerDelayModifier.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/Mirage.cs` | `Traits/Mirage.cs` | relative-path | **DIVERGED-BOTH** | not identified | 9 |
| `Traits/MissileBase.cs` | `Traits/MissileBase.cs` | relative-path | **DIVERGED-BOTH** | not identified | 12 |
| `Traits/MissileSpawnerMaster.cs` | `Traits/MissileSpawnerMaster.cs` | relative-path | **DIVERGED-BOTH** | not identified | 10 |
| `Traits/Modifiers/WithPalettedOverlay.cs` | `Traits/Modifiers/WithPalettedOverlay.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 5 |
| `Traits/Multipliers/DamageTypeDamageMultiplier.cs` | `Traits/Multipliers/DamageTypeDamageMultiplier.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Multipliers/DynamicSpeedMultiplier.cs` | `Traits/Multipliers/DynamicSpeedMultiplier.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Multipliers/LayeredDamageMultiplier.cs` | `Traits/Multipliers/LayeredDamageMultiplier.cs` | relative-path | **DIVERGED-BOTH** | not identified | 3 |
| `Traits/Multipliers/PortableChronoModifier.cs` | `Traits/Multipliers/PortableChronoModifier.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Multipliers/TimedDamageMultiplier.cs` | `Traits/Multipliers/TimedDamageMultiplier.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/PaletteEffects/CloakPaletteEffectCA.cs` | `Traits/PaletteEffects/CloakPaletteEffectCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 3 |
| `Traits/PaletteEffects/PulsingPaletteEffect.cs` | `Traits/PaletteEffects/PulsingPaletteEffect.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/PaletteEffects/WeatherColorEffect.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/Palettes/OverlayPlayerColorPalette.cs` | `Traits/Palettes/OverlayPlayerColorPalette.cs` | relative-path | **DIVERGED-BOTH** | not identified | 11 |
| `Traits/PeriodicProducerCA.cs` | `Traits/PeriodicProducerCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 7 |
| `Traits/Player/CapturedFactionsManager.cs` | `Traits/Player/CapturedFactionsManager.cs` | relative-path | **DIVERGED-UPSTREAM-NEWER** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/Player/GrantConditionOnPrerequisiteManagerCA.cs` | `Traits/Player/GrantConditionOnPrerequisiteManagerCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 5 |
| `Traits/Player/LobbyPrerequisiteDropdown.cs` | `Traits/Player/LobbyPrerequisiteDropdown.cs` | relative-path | **DIVERGED-LOCAL** | `c72dd9565c02` (2025-06-07) | 1 |
| `Traits/Player/ProvidesDelayedPrerequisite.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/Player/ProvidesPrerequisiteValidatedFaction.cs` | `Traits/Player/ProvidesPrerequisiteValidatedFaction.cs` | relative-path | **DIVERGED-BOTH** | not identified | 14 |
| `Traits/PopControlled.cs` | `Traits/PopControlled.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/PortableChronoCA.cs` | `Traits/PortableChronoCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/ProductionAirdropCA.cs` | `Traits/ProductionAirdropCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 11 |
| `Traits/ProductionParadropCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/ProductionQueueFromSelectionCA.cs` | `Traits/ProductionQueueFromSelectionCA.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 5 |
| `Traits/RecenterViewWithProductionTab.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/ReflectsDamage.cs` | `Traits/ReflectsDamage.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 2 |
| `Traits/ReloadAmmoPoolCA.cs` | `Traits/ReloadAmmoPoolCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 15 |
| `Traits/Render/LeavesTrailsCA.cs` | `Traits/Render/LeavesTrailsCA.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 2 |
| `Traits/Render/RenderShroudCircleCA.cs` | `Traits/Render/RenderShroudCircleCA.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 4 |
| `Traits/Render/WithActivateAnimation.cs` | `Traits/Render/WithActivateAnimation.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Render/WithCargoHatchAnimation.cs` | `Traits/Render/WithCargoHatchAnimation.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Render/WithChronoshiftChargePipsDecoration.cs` | `Traits/Render/WithChronoshiftChargePipsDecoration.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Render/WithChronosphereOverlay.cs` | `Traits/Render/WithChronosphereOverlay.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Render/WithColoredSelectionBox.cs` | `Traits/Render/WithColoredSelectionBox.cs` | relative-path | **DIVERGED-BOTH** | `7057e3569ec5` (2023-06-18) | 2 |
| `Traits/Render/WithDeliveryOverlay.cs` | `Traits/Render/WithDeliveryOverlay.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Render/WithDetectionCircle.cs` | `Traits/Render/WithDetectionCircle.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Render/WithDisguiseTargetPalette.cs` | `Traits/Render/WithDisguiseTargetPalette.cs` | relative-path | **DIVERGED-BOTH** | not identified | 1 |
| `Traits/Render/WithEnabledAnimation.cs` | `Traits/Render/WithEnabledAnimation.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/Render/WithHarvesterCapacityBar.cs` | `Traits/Render/WithHarvesterCapacityBar.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Render/WithMirageSpriteBody.cs` | `Traits/Render/WithMirageSpriteBody.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Render/WithMuzzleOverlayCA.cs` | `Traits/Render/WithMuzzleOverlayCA.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Render/WithNameTagDecorationCA.cs` | `Traits/Render/WithNameTagDecorationCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 6 |
| `Traits/Render/WithProductionDoorOverlayCA.cs` | `Traits/Render/WithProductionDoorOverlayCA.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 3 |
| `Traits/Render/WithRangeCircleCA.cs` | `Traits/Render/WithRangeCircleCA.cs` | relative-path | **DIVERGED-BOTH** | `51c1c2f633ee` (2024-05-30) | 1 |
| `Traits/Render/WithRestartableIdleOverlay.cs` | `Traits/Render/WithRestartableIdleOverlay.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/ResourcePurifierCA.cs` | `Traits/ResourcePurifierCA.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/RevealOnFireCA.cs` | `Traits/RevealOnFireCA.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Sound/AmbientSoundCA.cs` | `Traits/Sound/AmbientSoundCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 9 |
| `Traits/Sound/AnnounceOnCreation.cs` | `Traits/Sound/AnnounceOnCreation.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 2 |
| `Traits/Sound/AttackSoundsCA.cs` | `Traits/Sound/AttackSoundsCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 4 |
| `Traits/SpawnActorOnCapture.cs` | `Traits/SpawnActorOnCapture.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/SpawnActorOnSell.cs` | `Traits/SpawnActorOnSell.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/SpawnedExplodes.cs` | `Traits/SpawnedExplodes.cs` | relative-path | **DIVERGED-BOTH** | not identified | 11 |
| `Traits/SpawnRandomActorOnDeath.cs` | `Traits/SpawnRandomActorOnDeath.cs` | relative-path | **DIVERGED-BOTH** | not identified | 4 |
| `Traits/SupportPowers/DetonateWeaponPowerCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/SupportPowers/GrantExternalConditionPowerCA.cs` | `Traits/SupportPowers/GrantExternalConditionPowerCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Traits/SupportPowers/NukePowerCA.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/TargetedAttackAbility.cs` | `Traits/TargetedAttackAbility.cs` | relative-path | **DIVERGED-BOTH** | not identified | 12 |
| `Traits/TooltipExtras.cs` | `Traits/TooltipExtras.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/TracksCapturedFaction.cs` | `Traits/TracksCapturedFaction.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/TransferStanceToDeathActor.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Traits/TurnOnIdleCA.cs` | `Traits/TurnOnIdleCA.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Traits/ValidFactions.cs` | `Traits/ValidFactions.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Traits/Warpable.cs` | `Traits/Warpable.cs` | relative-path | **DIVERGED-BOTH** | not identified | 8 |
| `Traits/World/RevealedPlayersManager.cs` | `Traits/World/RevealedPlayersManager.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `TraitsInterfaces.cs` | `TraitsInterfaces.cs` | relative-path | **DIVERGED-BOTH** | not identified | 20 |
| `Warheads/ChronoFlashEffectWarhead.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Warheads/DummyWarhead.cs` | `Warheads/DummyWarhead.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Warheads/FireReverseRadiusWarhead.cs` | `—` | — | **LOCAL-ONLY** | not identified | 0 |
| `Warheads/WarpDamageWarhead.cs` | `Warheads/WarpDamageWarhead.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Widgets/ContainerWithTooltipWidget.cs` | `Widgets/ContainerWithTooltipWidget.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Widgets/ExternalLinkButtonWidget.cs` | `Widgets/ExternalLinkButtonWidget.cs` | relative-path | **DIVERGED-BOTH** | `990765108ba5` (2023-07-06) | 1 |
| `Widgets/ImageCAWidget.cs` | `Widgets/ImageCAWidget.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Widgets/Logic/AddFactionSuffixLogicCA.cs` | `Widgets/Logic/AddFactionSuffixLogicCA.cs` | relative-path | **DIVERGED-BOTH** | `59e4d0e55bee` (2023-05-27) | 1 |
| `Widgets/Logic/ExternalLinksLogic.cs` | `Widgets/Logic/ExternalLinksLogic.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Widgets/Logic/Ingame/ProductionTabsLogicCA.cs` | `Widgets/Logic/Ingame/ProductionTabsLogicCA.cs` | relative-path | **DIVERGED-BOTH** | not identified | 4 |
| `Widgets/Logic/Ingame/SpritePowerMeterLogic.cs` | `Widgets/Logic/Ingame/SpritePowerMeterLogic.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Widgets/Logic/LobbyOptionsLogicCA.cs` | `Widgets/Logic/Lobby/LobbyOptionsLogicCA.cs` | filename | **DIVERGED-BOTH** | not identified | 6 |
| `Widgets/Logic/SimpleTooltipWithDescLogic.cs` | `Widgets/Logic/SimpleTooltipWithDescLogic.cs` | relative-path | **DIVERGED-BOTH** | `5b4ed31d19cd` (2023-07-01) | 2 |
| `Widgets/Logic/TemplateMenuLogic.cs` | `Widgets/Logic/TemplateMenuLogic.cs` | relative-path | **IDENTICAL** | not identified | 0 |
| `Widgets/ProductionPaletteCAWidget.cs` | `Widgets/ProductionPaletteCAWidget.cs` | relative-path | **DIVERGED-BOTH** | `04ccb8abf61c` (2023-06-16) | 1 |
| `Widgets/ProductionTabsCAWidget.cs` | `Widgets/ProductionTabsCAWidget.cs` | relative-path | **DIVERGED-BOTH** | not identified | 16 |
| `Widgets/SpritePowerMeterWidget.cs` | `Widgets/SpritePowerMeterWidget.cs` | relative-path | **IDENTICAL** | not identified | 0 |

For each divergent file, the JSON records the normalized local/upstream line delta, historical match search, and the upstream commits after the matched vendor version. The detailed commit evidence follows.

## Upstream commits after the matched vendor version

### `Activities/CruiseMissileFly.cs`

Vendor content matches approximately `92c36baa143b9cd2db68f693edf2f182f61c48f0` (2024-05-27T17:59:40+01:00; Align V3/TH with trajectory a little better.).

- `dc80a83e24a168303ff6f9c621bb120a8d95ac38` (2025-06-26T16:43:23+01:00) — Speculative fix for cruise missile crash.

### `Activities/Dive.cs`

Vendor content matches approximately `a6f122fa24230a3010f3e9e60da7a31d343f47a1` (2024-05-11T14:23:33+01:00; Jackknife.).

- `0d12ac149fa8b293ef2bb81f3751344ad69cbe71` (2025-12-22T10:15:53Z) — Targeted dive ability for Shadow Team.
- `48a4ad59df7a6566ab948e3b317d575f78f1ef4a` (2025-12-22T10:15:53Z) — Targeted dive ability for Shadow Team.

### `Activities/GuidedMissileFly.cs`

Vendor content matches approximately `a41ab548db80b6e6f206d3072dbc03ee375ceb18` (2024-05-07T19:37:01+01:00; Patriot Strike.).

- `85f81032bef93d1fd026e20d298c26c10308f38f` (2024-12-17T12:31:00Z) — - Increased Grand Cannon damage vs heavy armor. Increased range by from 9 to 10. First shot is accurate. - Replaced Patriot Strike with Black Sky Strike. Hits up to 6 ground targets, prioritizing the most valuable. - Reduced Troop Crawler cost from 1600 to 1500. - Hoplite range reduced by 1. Added empowered shots which blind enemies (9s cooldown). - Increased Black Eagle splash damage. - Avatar shadow. - Stealth Harvester research icon. - Fix Teleport/Leap abilities being permanently disabled if unit is warped while recharging. - Fix Chrono Tank moving to destination if long distance teleport is temporarily interrupted by being warped.
- `49e916f2ae0269512abc289e6c09cae124f84cc6` (2024-11-06T11:16:47Z) — - Reduced Patriot missile damage & splash. Reduced distance to avoid slightly. - UI indicators for GDI strategy level and Nod building/harvester kills.

### `Activities/HuntCA.cs`

Vendor content matches approximately `eb4f92cae626a117d168fd18bb8b25eafd691cf4` (2025-10-06T08:17:56+01:00; - Mission fixes. - Fixed AttackCharged behaviour for AI units in hunt mode. - Reverted accidental change to laser weapons. - Fixed ruined Oil Derrick granting bonus on capture. - Reverted Avatar HP back to 78k HP. - Hacker no longer needs to deploy. - Fixed performance issues on Zenith.).

- `5188405e6744295b39ef22d8fa15a355a74a23d1` (2026-06-27T16:09:55+01:00) — - Prism Tank/Cannon will no longer undeploy if ordered to fire at a target out of range. - HuntCA supports multiple attack bases.

### `Activities/InstantTransform.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `0c542cc2e0dc2b1bc566283d6aaea65a3f8a6e8e` (2026-06-10T18:12:47Z) — - Prevent Nanite Repair from targeting attached Mini Drones. - Added missing Mobile Sensor discount for ARC. - Cap Ichor Spike to affecting 3 resource nodes. - AI uses IC on damaged units only. - SSM voice. - Speculative fix for failed Mini Drone detachment.
- `faf82cbf6b9958a7ef80abbc2bafc9bbf662ba0a` (2025-10-18T10:03:28+01:00) — - Fixed Engineer not defusing SEAL C4. - Fixed Tib Stealth not applying to attached Mini Drones. - Fixed Entrenchment prerequisite display in chapter 8 missions. - Speculative fix for Mini Drones not detaching properly if parent is killed. - Corrected fake War Factory selection bounds.
- `d57d9fe4bd13804522eb90f6995f2eae66ef504b` (2025-06-21T09:44:25+01:00) — - Make Tech Buildings hackable, chillable and affected by target painter & watcher parasite. - Fix Mini Drone not detaching when attached to an MCV which deploys. - Mini Drones can now survive their host being destroyed.
- `886c7f95c5c7aeefa550c912353a4ac9e3b1ad29` (2024-12-19T14:06:28Z) — Avenger & Ceramic Armor upgrades for Warthog on Bombardment & Hold the Line strategies respectively. Sidewinders for Seek & Destroy only.
- `1b92047181fbb6b9d90c984d60cdc78e09a0ac5f` (2024-05-19T18:32:16+01:00) — Misc: - Improved Pitbull missile sound. - Improved meteor impact. - Reduced Rift sprite size. - Custom paratroopers power for prerequisite based overrides. - Fix Chrono Harvester facing on teleporting to refinery. - Custom harvester docking animation trait so animation only plays for certain refinery types.
- `1b7e7ac7d256265fe32fcef3ab5cdb45a56b4eb9` (2024-05-17T20:17:17+01:00) — Transfer resources on Chrono Harvester upgrade.
- `d8160dc6364d0848a837d0d6e479850ced562973` (2024-02-03T17:58:52Z) — Overhauled mini drone attachment. Improvements to Upgradeable trait and Upgrade activity.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `5d53346543bc070694fdf9375dd98b228dc7edd7` (2023-04-02T15:43:22+01:00) — Unit upgrades system.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `3545e78cbac89a596abacdbaf5d07ee40feabc4c` (2021-03-08T02:28:30+10:00) — Add Ion Storm Upgrade

### `Activities/TeleportCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `7a4fbbd66d9f8a7952073b992188d0c7692cf76b` (2025-06-07T21:44:14+01:00) — Engine update fixes part 3.
- `7bb28bc17b4062d0b6d74ca86cd3481a843c0643` (2025-01-20T07:55:26Z) — Fixed queued Chrono Tank telports incorrectly calculating the pre-charge time.
- `627143ca994d3a6a067aef2d1581ef8c75cd6645` (2024-11-29T21:37:23Z) — Removed Temporal Flux range boost.
- `10108c11aa700d3a4abc0a99eb791a04f948ed05` (2024-11-18T22:27:22Z) — - Allow Chrono Tank to teleport 48 cells, but longer distances require scaling charge up time. Increased cost to 1500. - Cryostorm has EVA warning and takes 5 seconds to appear. - Removed X external link from menu screen. - Hornet/Invader tooltip clarification. - Mission 22 difficulty tweaks.
- `7d1a20ab9b7c5befacd3b5525fea075251e2c723` (2024-02-07T22:12:38Z) — Added Fleet Recall power on Scrin Signal Transmitter. Added target highlighting to Chronoshift. Minor yaml fixes.
- `30837752e6dd34adbab6dcc0c49b798e7ae29fc0` (2023-08-19T15:35:33+01:00) — Improved targeting for GrantExternalConditionPowerCA and ChronoshiftPowerCA.
- `d5807171441099eaac02314571ae099e85c28f70` (2023-08-13T21:46:53+01:00) — Balance/misc: - Increased Hum-Vee/Ranger/Buggy/BTR/Gun Walker/Guardian Drone/Mini Drone/APC/Raider APC damage vs light armor. - Increased Gun Walker HP from 30k to 33k. - Shard Walker no longer has heavy armor. HP increased to 40k. Reverted nerf vs light armor. - Increased Seeker HP from 22k to 23k. - Increased Lacerator vision by 1. - Increased Leecher HP from 28k to 30k. Increased damage vs light armor. - Increased Leecher orb HP from 30k to 35k. - Chrono Tank can now attack aircraft (relatively low damage). Added a 3 second cooldown between jumps with Temporal Flux. Can no longer crush infantry instantly by teleporting onto them. - Reduced Tripod & Reaper Tripod range very slightly. Reduced damage vs buildings and infantry. - Increased Disruptor damage vs buildings and light armor slightly. - Increased Sukhoi splash damage and missile speed slightly. - Mission 1 & 2 normal/easy difficulty tweaks.
- `090f33479b9816b2045d929a5b4d9914ac9ee6e7` (2023-08-05T12:01:44+01:00) — 2307 engine fixes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `af3b4af7aaf080c086210269fffffafed17a41a8` (2023-04-29T12:39:47+01:00) — Prevent teleporting infantry stacking on the same sub cell.
- `307a50b81e88aaeb38ca02354f4c119cc35221f1` (2023-03-26T10:26:18+01:00) — Temporal Flux allows Chrono Tank to teleport twice before recharging. Reduced Chrono Tank damage vs infantry and speed.
- `eed1e75fa0d574d8532d6a326cafcdfff8597ac7` (2022-01-31T22:55:56Z) — TurretedFloating fix. EMP missile fix. Minor adjustments to match engine classes. Removed ContrailCA, RevealsMapCA and RepairableNearCA as the engine versions seem to do everything we need now.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `949e78b505e8a986ab0a3ae9169d06c8e18d8b1c` (2021-07-31T18:56:47+10:00) — Add Temporal Flux Upgrade for Chrono Prison

### `AIUtils.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `9a68fea1584271fee9363ac6dc1b108cabc850f4` (2026-01-31T16:24:09Z) — Skirmish AI indirect routes of attack.
- `71754fc0647fde6b9559ae43fff8cb00ff392f76` (2026-01-01T11:45:03Z) — Fix AI aircraft limits.
- `53d7a35e577e0c783f7b583a9fdfb152336a3f56` (2026-01-01T11:45:03Z) — Fix AI aircraft limits.
- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `7a4fbbd66d9f8a7952073b992188d0c7692cf76b` (2025-06-07T21:44:14+01:00) — Engine update fixes part 3.
- `356e0301a50187da7c5b528674c2495b45fba2e7` (2025-06-07T20:57:22+01:00) — Engine update fixes part 2.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo

### `Orders/ReleaseSlaveOrderTargeter.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `8fdf6ea259630864cf89e8889806c05bbf71d2a9` (2023-04-15T21:03:03+01:00) — When a transport is mind controlled, normal command will release it, force command (alt) will enter it.
- `b94f5adc8f94f61315fa035a41bd9a1d2203c9d9` (2023-02-27T22:10:45Z) — Allow mind control slaves to be released manually.
- `73b8aa03def9dca2a004b64c4003bc7e6ecdb700` (2021-11-05T16:42:30Z) — Don't disable enter cursor for cyborg conversion when player has no credits as it makes it appear like it's not working.
- `fcd8830dc2bfe8f62cb74b34be4df3cc5d24b77f` (2021-03-12T00:26:34+10:00) — Move Unit Converter to Temple Prime
- `2ce889554ed91a9f7ae7b3466183a8ec9b0959c4` (2021-02-16T22:31:30+10:00) — Add UnitConverter

### `Projectiles/LaserZapCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `8c5efe4d366519099a39d14b998f0041823a1875` (2025-06-08T15:53:55+01:00) — Engine update part 10 (projectiles).
- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `7a4fbbd66d9f8a7952073b992188d0c7692cf76b` (2025-06-07T21:44:14+01:00) — Engine update fixes part 3.
- `d5af505685fb21f3c2bc7b14b1c18d9862b0b1a0` (2024-12-06T17:48:24Z) — - Added voice announcement for when Covenants become available. - Added tracers effects to Wolverine & updated firing sound. - Increased Chrono Tank rate of fire, damage vs light/buildings, range (+1) and turn speed. Reduced HP from 45k to 32k. - Increased JumpJet/Bombardier speed. - Ships targetable by Anathema. - Tripled PAC damage vs buildings. - Reduced duration of Cyborg Reaper snare from 8s to 6s. - Zone Defender shield stacks up to 6 times providing between 25% and 50% damage reduction. - Updated Stromberg maps.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `70fb0f23bad5a675db1c0657e94338ca666de57c` (2022-08-07T10:42:06+01:00) — Reworked some projectiles so beams don't render behind things incorrectly (no longer need to use huge ZOffsets).

### `Projectiles/LinearPulse.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `3aa1b02802361a481def572213e6bbbee9a95b46` (2026-06-06T22:01:14+01:00) — - Updated Obliterator/Cryo Trooper to use new LinearPulse. - Increased Cryo Trooper/Launcher damage vs buildings. - Fixed Mini Drone XP level inheritance crash.
- `eda277515d0cc89700dd95e52935b0427541bdc4` (2026-06-02T00:03:37+01:00) — Removed unused Cone impact type (can be achieved with Trapezoid). Corrected flamer friendly fire range.
- `e7ed9870206d448167845e4a6d6402edc9a0a384` (2026-01-11T19:06:46Z) — LinearPulse calculation tweaks (fixes Enforcer blasts at very close range).
- `e44e23848e5ebf1f3c800e9ad8baa368109f5782` (2025-11-26T18:00:53Z) — Mission updates.
- `b908cabe9abe14b19654e1fd13e9827f80747f7e` (2025-11-22T19:11:52Z) — - Fixed LinearPulse damage calculation. - Allow refund when upgrading to actors with lower cost.
- `972575f369b12426ffec086610cfbe2448cc4429` (2025-09-11T21:16:16+01:00) — - Updates to LinearPulse projectile. - Added BlindImmune target type. - Updated campaign progress tracker. - Fixed campaign tech building tooltips. - Make Tib Coalescence hit air in campaign. - Reduced Howitzer upgrade cost from 1000 to 750. - Reduced Bombardier speed from 118 to 100. Increased price from 525 to 550.
- `50cb55c803c53a8f024e917da4590e63c5c70162` (2025-08-31T09:44:36+01:00) — Updated LinearPulse to support multiple projectile animations.
- `bd52713dcbbb81725fb8ca2475cf27f9f26a2c71` (2025-08-30T13:19:39+01:00) — Mission updates.
- `d137d873636c9302b6da9f0bae7f7ef07e510bd1` (2025-08-30T08:11:12+01:00) — Add smudges and multi-falloff to LinearPulse.
- `2b18801d1d465d120aedd1eb840dd6ca0c541715` (2025-08-29T20:39:08+01:00) — - Add Blockable and MinimumFriendlyFireRange property to LinearPulse. - Increased Enforcer HP from 18k to 25k.
- `ebe536abadde2f62f1694a3dd2b822e57529dc58` (2025-08-29T17:53:29+01:00) — LinearPulse projectile improvements (remove unused warheads). Implement Enforcer shotgun conal spread.
- `751c5a49219e7a4847391bd6eb4140537a14b3b5` (2025-08-28T17:51:50+01:00) — LinearPulse projectile improvements.
- `8c5efe4d366519099a39d14b998f0041823a1875` (2025-06-08T15:53:55+01:00) — Engine update part 10 (projectiles).
- `46bfd4be75fdded4692a89125cfc6491b8ebd1d7` (2025-03-16T18:21:36Z) — - Reworked Obliterator. - Reduced Impaler speed from 72 to 60. - Increased Mutilator damage reduction after blink from 50% to 66%.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `74a3c2df1d5ee07158ce077ff932ae36be73f505` (2023-05-26T22:12:30+01:00) — Updated Disruptor projectile.
- `82477fc9b47e16c30e2fbbe6915d2d3d758a46d1` (2022-08-31T07:14:11Z) — Allow LinearPulse visual projectile speed to be different from the impact projectile speed to improve Flame Tank usability. Increase Flame Tank and Corrupter damage vs light armor.
- `fb83f0d39f147c2f9bf4b849a21735b96497bc9b` (2021-08-23T17:43:41+01:00) — LinearPulse changed to use ticks rather than distance for impact interval so impacts are synchronised with the projectile speed. Fixed projectile not terminating at max range. Removed wall crushing from Scrin hover units.
- `01776f9f7e993b76bc950a45f955b1ff6e5de987` (2021-07-26T19:35:21+01:00) — Fixed flames not appearing when firing at friendly units. Added dummy warhead to remove the need for spread damage warheads with zero damage. Added ForceGround to LinearPulse so flamers are accurate without needing a dummy weapon for the muzzle position.
- `af7c77d83041dbdb87d3f11f3de413ca0c6f781e` (2021-07-24T22:44:15+01:00) — Balancing. - Black Hand Trooper weapon rework to make it effective against moving targets. - Feeders now have a Leecher-like basic weapon so they aren't defenseless prior to reaching capacity. - Atomized debuff also slows rate of fire by 20%. - Increased Bike AA damage as Nod AA vehicles are very fragile and non-Marked Nod also lack any air-to-air until tier 3. - Reduced Leecher movement speed, HP and damage. Increased damage radius. Doubled self-healing ratio. Beams now only chain if primary target is infantry. - Raised AI likelihood of prioritising aircraft with their air-to-air units. - Increased IFV vision from 5 to 6 to match BTR, GunWalker etc.

### `Projectiles/PlasmaBeam.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `b0bab62993059552bdc66333781f3231c5101701` (2026-07-03T18:04:35+01:00) — Default glow colors of projectiles.
- `9956284764b30d5cec89a4b26b6ab055c973756a` (2026-06-05T21:43:13+01:00) — Fixed some glow colours.
- `13f2889253e967ef12ce5dfa770a88bacd28c9e1` (2026-06-05T21:32:51+08:00) — Add Glow Effect to CA Projectiles
- `8c5efe4d366519099a39d14b998f0041823a1875` (2025-06-08T15:53:55+01:00) — Engine update part 10 (projectiles).
- `7a4fbbd66d9f8a7952073b992188d0c7692cf76b` (2025-06-07T21:44:14+01:00) — Engine update fixes part 3.
- `ac131e9ebad3a81cde890aad0595a91a2dbccd12` (2024-09-14T16:30:27+01:00) — Balance/misc. - Guardian Drone does 3 shot burst. Increased reload time. Increased DPS slightly. - Atomizer now hits the target plus up to 3 additional nearby targets. Atomized debuff no longer does splash damage, but will do more damage over time. Will now stack infinitely (previously only stacked to 3). No longer targets aircraft. - After 30 seconds, watcher parasite will cause an icon to appear to the watched player. Icon appears immediately for watcher player. - Fixed JumpJet getting stuck attacking attack move target. - Reduced Venom damage vs heavy armor. Reduced upgraded Venom damage vs buildings/defenses. - Increased cyborg conversion time. - Fix Comanche getting stuck decloaked if interrupted when resupplying. - Reduced Apache rate of fire slightly. - Don't enable bot insurance until 2 minutes into the game.
- `6a63ce74c7416d34d13c0e6d54bcca68eb1fc2bd` (2024-03-01T16:52:22Z) — Updates. - Increase Floating Disc HP from 60k to 65k. Increase speed from 56 to 60. - Improved Guard Tower/Pillbox projectiles so they track the target. - Use "Unit Stolen" announcement if your unit is stolen. - Increased Jumpjet/Bombardier speed from 99 to 108. - Reverted SEAL RoF. Increased damage vs light to compensate. - Fixed Mastermind having idle animation while being warped. - Slight increase in resource regrowth rates. - Allied/GDI static AA require factory instead of radar.
- `bdcae0cbe5a69e480ba5656a1e2563831d27ce46` (2024-02-12T17:04:14Z) — Prevent Mothership being recalled while using main weapon. Interrupt plasma beam weapons on death. Default Nighthawk stance to Defend.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `70fb0f23bad5a675db1c0657e94338ca666de57c` (2022-08-07T10:42:06+01:00) — Reworked some projectiles so beams don't render behind things incorrectly (no longer need to use huge ZOffsets).
- `13705bacb9c84fb211e02629d777da4c95c72754` (2022-07-30T14:56:18+01:00) — Add Shard Walker to AI build list. Corrected Coalescence spelling in AI build list. Make AI target Leecher Orbs. Removed debugging. Code formatting.
- `44d2c1aa7db174d9741da1202ac3dae46276edbb` (2022-07-30T13:42:46+01:00) — Removed MothershipAttackBehaviour trait and associated hackiness; no longer needed with PlasmaBeam changes.
- `9ef01127cfa799643d6e1cc8dd52a31c33b55246` (2022-07-30T09:54:37+01:00) — Updated Devourer/Tripod/Mothership beams so they will always do a full swipe and not swap targets in the middle of one.
- `b0eb2555c766170c0575ecb6010c60a6c2808e3c` (2022-07-24T11:09:33+01:00) — Updated PlasmaBeam projectile so that sweeping beam mode is built in. Fixed Reaper Tripod not charging on resources.
- `15aa57e6bc4e76dfafdfdd78c3daf77e2998bdea` (2022-06-15T22:28:57+01:00) — Fixes after merge.
- `98681f3a1a42b41333f6f665d66224d6e1a602c4` (2022-06-10T16:21:08+01:00) — Misc. - Fixed being able to prevent Chronoshift return by spamming attack or attack move. - Don't play unit lost notification on Brute mutation. - Reduce gap cloud opacity a little. - Remove GuardsSelection from MGG. - Don't reset MGG stacks when switching targets. - Projectile improvements to PlasmaBeam and ElectricBolt.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `fd367c06fed72dfe32f89fdb587acb24125c12ad` (2021-07-07T10:07:23+01:00) — Fixed code styling.
- `aab81ead482c12b94dd35a439bec0e4eca320dc6` (2021-06-26T21:47:27+01:00) — Reduced Leecher beam intensity. Added workaround for PlasmaBeam alpha being higher at longer ranges. Added Atomized death voices.
- `304e81220dd5bfca1de0e8d6f5f3d1383c9cb1b5` (2021-06-19T12:30:30+01:00) — Despoiler-11. New Scrin subfaction with Leecher and Atomizer unique units.

### `Traits/Air/AttackAircraftCA.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `886c7f95c5c7aeefa550c912353a4ac9e3b1ad29` (2024-12-19T14:06:28Z) — Avenger & Ceramic Armor upgrades for Warthog on Bombardment & Hold the Line strategies respectively. Sidewinders for Seek & Destroy only.

### `Traits/Air/DiveOnAttack.cs`

Vendor content matches approximately `a6f122fa24230a3010f3e9e60da7a31d343f47a1` (2024-05-11T14:23:33+01:00; Jackknife.).

- `0d12ac149fa8b293ef2bb81f3751344ad69cbe71` (2025-12-22T10:15:53Z) — Targeted dive ability for Shadow Team.
- `48a4ad59df7a6566ab948e3b317d575f78f1ef4a` (2025-12-22T10:15:53Z) — Targeted dive ability for Shadow Team.

### `Traits/Attachable.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `d66d24aca2f651b9675bb7855a7ae3aace0cb520` (2026-07-03T22:27:20+01:00) — Warning fix.
- `c31ddb771659bb2e1ab93f1f91c7c38c6dcb40fd` (2026-06-27T14:47:17+01:00) — Improved responsiveness of Mini Drone attachment.
- `686aa05d2383f6056aae737f4c0c7ecd04f8426d` (2026-06-12T07:01:40Z) — Vulcan voice.
- `64a7ec1a1dea8c57492e45f55a6a0d983c5bd172` (2026-06-04T15:46:47Z) — - The full XP of any destroyed ARC drones will now be added to a singular reclaimable XP pool. On production of new drones, this XP will be drawn from up to veterancy level 2. - Mini Drones will transfer their XP to the parent unit on attaching. They will then inherit the veterancy level of the parent unit, and any damage dealt will be given to the parent unit. - Suppression Field can be applied as long as one valid unit is visible within the target circle (non-visible units within the circle will then be affected upon activation). - Made Templar laser with Quantum Capacitors more visually distinct. - Red skull icon for Assassins. - Fixed triple SSM with Black Napalm burst count. Adjusted reload to bring DPS into line. - Removed duplicate lasher warhead.
- `3f07398638ae11fdac95a91f2711647dda2d01f3` (2025-10-29T17:53:23Z) — - Mini Drones inherit cloak from parent. - Corrected TD Harvester palette. - Fixed Mini Drone attach sound.
- `bff362a26fc9cddf57334d3dad7194b2f7c5eeed` (2025-10-19T12:39:23+01:00) — Speculative fix for interrupted Chronoshift.
- `d57d9fe4bd13804522eb90f6995f2eae66ef504b` (2025-06-21T09:44:25+01:00) — - Make Tech Buildings hackable, chillable and affected by target painter & watcher parasite. - Fix Mini Drone not detaching when attached to an MCV which deploys. - Mini Drones can now survive their host being destroyed.
- `cdc66e8722aa6b9536d9888322ed638d44f388bd` (2025-03-15T16:17:04Z) — Voice line for mass cargo loading.
- `844302d1b0882922b573a4a26f28a6868386cfaa` (2025-03-15T11:06:38Z) — Fix mass load/attach desync.
- `4c2090b8927789083cc7aa94cf4cc9ca99856b5c` (2025-03-15T10:24:00Z) — Mass Mini Drone attachment.
- `42ab4fe6298bf42abf55bc23a0a8255ee9a57132` (2024-09-01T09:37:08+01:00) — Fix unattached Mini Drone cancelling activities after stopping aiming.
- `83e46fd8e510f63a9a6b779167caba5062a5d02d` (2024-05-19T14:10:54+01:00) — Reworked Attachable/AttachableTo traits. Allows multiple AttachableTo traits, each for a different type of attachable.
- `6a24353abae6acecb7a53296479cd4e9b235a7b0` (2024-02-13T19:13:44Z) — Updates. - Fix condition warheads not applying to large actors with multiple targetable locations. - Added IronCurtainImmune and ChronoshiftImmune to easily prevent decoys from being targeted by these. - Reduced Venom damage vs buildings (with upgrade no change).
- `d8160dc6364d0848a837d0d6e479850ced562973` (2024-02-03T17:58:52Z) — Overhauled mini drone attachment. Improvements to Upgradeable trait and Upgrade activity.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `6c6ac0b15598df5bd5def7c9de2a01eeb65a72e4` (2023-04-25T19:40:00+01:00) — Fixed attached Mini Drones fixating on targets after they go out of range.
- `df3e96a28249b17c5a5336a92a00e3ef0f1defe1` (2023-03-21T21:56:01Z) — Fix crash when attached actor is dead and parent is removed from world (but not killed).
- `861ae6033a1072512a8ede3b551729b085cfd66a` (2022-02-02T19:59:42Z) — Fixed Attachable actor causing pathfinding crash. Fixed MCV being unable to deploy with a Mini Drone attached. Fixed crates duplicating attached Mini Drone rather than the parent unit.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `bbb070560b11e5a83d3dd596c1eebac0215f6250` (2021-10-19T13:54:57+01:00) — Fixed attached Mini Drones blocking Carryall pick up and being left behind by water transports. Added Atomic/Lasher tanks to Mastermind Madness maps. Use gun turret for technician IFV since it's the same. YAML error fixes.

### `Traits/AttachableTo.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `0c542cc2e0dc2b1bc566283d6aaea65a3f8a6e8e` (2026-06-10T18:12:47Z) — - Prevent Nanite Repair from targeting attached Mini Drones. - Added missing Mobile Sensor discount for ARC. - Cap Ichor Spike to affecting 3 resource nodes. - AI uses IC on damaged units only. - SSM voice. - Speculative fix for failed Mini Drone detachment.
- `6eff906c5de3ebd82effddccd42f37721bba4ac5` (2026-05-30T18:13:47+01:00) — - Allow Burster to force fire ground. - Strafing Run targeting circle. - Fixed Interceptors camera duration. Show radius while interceptors are active. - Watcher parasites can attach to infantry. A watched unit can be struck again to refresh the parasite duration. - Additional Collector-73 bonus - Watcher attack applies suppression to multiple targets.
- `067a587d6deaf8f6be893185eecfbb6f9bfd948d` (2025-11-02T09:32:52Z) — Attachable crash fix.
- `3f07398638ae11fdac95a91f2711647dda2d01f3` (2025-10-29T17:53:23Z) — - Mini Drones inherit cloak from parent. - Corrected TD Harvester palette. - Fixed Mini Drone attach sound.
- `03324538cac3293579f7f400cec009163a3814d9` (2025-06-22T15:33:15+01:00) — Fix stuck Mini Drone after host is sold.
- `d248b730207afd2ac96559cda806fabdeb7f20ef` (2024-12-28T22:24:19Z) — - Increased Tank Destroyer range by 1. Reduced HP from 44k to 42k. - Fixed allied passenger ownership when chronoshifted transport is killed. - Conditional CloneProducer (for missions). - Show "watched" icon on units with a shadow beacon attached. - Attached Shadow Beacons and Watcher parasites detect cloak. - Minor campaign AI code fix. - Allow 10 hotkeys for support powers. - Reckoning tweaks.
- `83e46fd8e510f63a9a6b779167caba5062a5d02d` (2024-05-19T14:10:54+01:00) — Reworked Attachable/AttachableTo traits. Allows multiple AttachableTo traits, each for a different type of attachable.
- `ac3f7a7e89fc46ffb3cfc8206e00fc86bb8f744c` (2024-05-18T07:35:00+01:00) — Scrin allegiances, Eviscerator, Obliterator, Nullifier, Overlord's Wrath, Gateway & Watcher.
- `d8160dc6364d0848a837d0d6e479850ced562973` (2024-02-03T17:58:52Z) — Overhauled mini drone attachment. Improvements to Upgradeable trait and Upgrade activity.

### `Traits/AttachOnCreation.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `3f07398638ae11fdac95a91f2711647dda2d01f3` (2025-10-29T17:53:23Z) — - Mini Drones inherit cloak from parent. - Corrected TD Harvester palette. - Fixed Mini Drone attach sound.
- `83e46fd8e510f63a9a6b779167caba5062a5d02d` (2024-05-19T14:10:54+01:00) — Reworked Attachable/AttachableTo traits. Allows multiple AttachableTo traits, each for a different type of attachable.

### `Traits/AttachOnTransform.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `ea1b851088cb523c23c3f9b7b1f4d1c6b4d0a2a3` (2025-12-07T16:13:06Z) — Clean up trait lookups.
- `3f07398638ae11fdac95a91f2711647dda2d01f3` (2025-10-29T17:53:23Z) — - Mini Drones inherit cloak from parent. - Corrected TD Harvester palette. - Fixed Mini Drone attach sound.
- `371ca5d2b5223ca70107c3d11246ca1dd4a33ea9` (2023-07-24T20:11:32+01:00) — Fixed crash when deploying an MCV with Mini Drone attached.

### `Traits/Attack/AttackBomberCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `1ed842152534dbf84947813552da46bc82c5bdde` (2024-03-23T10:49:45Z) — Updates. - Increased V2 splash radius slightly. Reduced cost of V2 upgrade from 1000 to 500. - Raised Iron Curtained unit speed cap to 60 (Heavy Tank speed), or 112 for aircraft (Hind speed). - Increased power consumption of basic defenses from 10 to 15 (was previously reduced from 25). - Increased Battle Fortress HP from 120k to 130k HP. Range to 5.75 (to match Apoc, Tripod etc.). - Reduced Tesla Track HP from 22k to 20k. - Increased Floating Disc range by 1. - Increased Tank Destroyer range by 1. Reduced HP from 46k to 44k. - Reduced Tomahawk price from 2000 to 1850. - Reduced Hypercharge upgrade cost from 1000 to 750. - Changed Mobile Sensor to light armor. - Increased Aurora cost from 2200 to 2300. Reduced splash radius vs infantry. Damage reduction reduced from 20% to 10% when afternburner is active. Target must be enemy unit/building to activate afterburner. - Slightly increased Banshee splash damage. - Reduced X-O Powersuit range by 1. Increased turn rate by 33%. - Increased Desolator damage vs light. Slightly increased splash damage vs infantry. Reduced deploy time. - Atomized debuff slows target by 25%, up from 15%. - Reduced Pitbull cost from 1000 to 900. Increased missile speed. - Increased Peacemaker cost from 2400 to 2500. - 8x RAGL 15 1v1 maps. - 3x other 1v1 maps. - 37x new team game maps. - Fixed undeployable starting location on Basalt Badlands map. - Prevent wormholes being destroyed in certain campaign missions. - Exclude Supply Truck from Oil Refinery price reduction.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `b2286da8eabf18577b63bd049875d8fdd8cc153c` (2022-02-02T13:01:13Z) — Additional changes to bring customised traits in line with their base versions as far as possible. Added descriptions to these classes to explain the differences with base versions.
- `eed1e75fa0d574d8532d6a326cafcdfff8597ac7` (2022-01-31T22:55:56Z) — TurretedFloating fix. EMP missile fix. Minor adjustments to match engine classes. Removed ContrailCA, RevealsMapCA and RepairableNearCA as the engine versions seem to do everything we need now.
- `eaa4e5ce84b7ff5f761066587863a92d7d955016` (2021-10-13T16:45:17+10:00) — FacingTolerance fix for AttackBomberCA.
- `b091fb3552611a3738b61b1b3a4525de0d621d95` (2021-10-12T21:53:33+01:00) — FacingTolerance fix for AttackBomberCA.
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `0ec50396b6191e99f4ac3fdb2587cd6a7994e95d` (2020-01-21T07:38:02Z) — Engine Update
- `5f9bd7777761120640d00a05d147cd38b628379e` (2020-01-03T01:58:10Z) — Add Faction Support Powers +
- `6d0ff33bfd1edc9fe5bf3c43f319f8128e3612ee` (2019-12-14T19:14:58Z) — 0.60.1

### `Traits/Attack/AttackFrontalCharged.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `ea1b851088cb523c23c3f9b7b1f4d1c6b4d0a2a3` (2025-12-07T16:13:06Z) — Clean up trait lookups.
- `eb4f92cae626a117d168fd18bb8b25eafd691cf4` (2025-10-06T08:17:56+01:00) — - Mission fixes. - Fixed AttackCharged behaviour for AI units in hunt mode. - Reverted accidental change to laser weapons. - Fixed ruined Oil Derrick granting bonus on capture. - Reverted Avatar HP back to 78k HP. - Hacker no longer needs to deploy. - Fixed performance issues on Zenith.
- `d246d669c1ea45490c49bd7db0d2790fd8680f47` (2025-05-30T20:35:33+01:00) — - Zeus loses charge while turning. - Added concussion to Kamov missiles. - Campaign crash fix.
- `872777970a420acd026d8bde97e1a4103f1a4aa8` (2024-12-18T23:16:57Z) — Prevent Hoplite moving forward when toggling between weapons.
- `58ddacd4804cecd9b15747e1f9ace4eb25b5b06a` (2024-10-09T17:46:58+01:00) — - Added line damage back to Wolverine. Reverted XO damage changes. - Increased Overlord's Wrath damage. - Malefic tooltip/prerequisite corrections. - Reduced Ravager HP from 7k to 6k. Reduced damage & rate of fire slightly. - Watcher defaults to hold fire stance. - Reduced Eviscerator rate of fire and damage. Now affected by Resource Conversion upgrade. - Increased Mutilator HP. - Added small amount of splash to Impaler projectiles. - Stormcrawler clouds form immediately on dealing/taking damage with Ion Conduits upgrade. - Reduced Plasma Cannon damage vs heavy armor. - Increased Rad Trooper damage slightly. Increased HP from 7.5k to 8k. - Increased Desolator splash radius slightly. Increased HP from 17k to 18.5k. - Increased Zone Trooper rate of fire and damage. - Increased Zone Defender rate of fire. - Increased Tesla Trooper HP from 17k to 18k. - Reduced Cyborg HP from 21k to 20k. Increased cost from 250 to 275. - Increased Zone Trooper/Raider jump pack cooldown by 1s. - Reduced Acolyte HP from 10k to 9k. - Reduced Leecher damage vs buildings and light armor. - Added support for random charge times to AttackFrontalCharged.
- `7cb898702255d959241e9b7ef1cee3dfe0f15ad4` (2023-05-29T16:14:25+01:00) — Misc. - Stop ambient sounds after game ends. - Use charging attacks for EMP Missile and Firestorm Barrage so time to fire is consistent regardless of initial turret facing.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `6551c7469e6f7d5ad8685636ddf2901d5844fac0` (2023-05-27T16:09:55+01:00) — Balancing/misc. - Slightly reduced Ion Mammoth rate of fire and splash radius. - Soviet engineer voice. - Spectre charges to attack instead of using FireDelay (which was buggy). - Make Scrin units use Scrin voices when controlled by a human faction. - Yaml fix.
- `4f1cc919a626b5745077ddebce2363642f60eb27` (2023-04-05T21:57:04+01:00) — Fix issue with AttackFrontalCharged being enabled while already attacking. Yaml fix.
- `bfd28b851598b077e9c1ef85bdb37bfa5df1ba4d` (2023-04-05T21:18:56+01:00) — Balance. - Rebalanced Tesla Tank around a higher rate of fire and good damage vs heavy armor. - Increased Tesla Track base damage, reduced Tesla Arcing damage a little more. - Base Sniper no longer targets vehicles and must aim before firing. Increased range to 8.75. - Moved Raufoss upgrade to T3. Reduces range. - Reduced detonation and cooldown times of SEAL C4.
- `8eaeca5bae23ad1c85139258a14587ee7a891f16` (2022-12-08T07:20:31Z) — Allow Mechanics to be upgraded to Cyborg Mechanics in Temple Prime. Fixed upgraded Devastator attack move.
- `bd345564e961f1dcf76fac1ddb4428d49165d560` (2022-09-24T22:10:25+01:00) — Added AttackFrontalCharged trait for Devastator with Stellar Fusion Cannon upgrade.

### `Traits/Attack/AttackPrismSupported.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `1ed842152534dbf84947813552da46bc82c5bdde` (2024-03-23T10:49:45Z) — Updates. - Increased V2 splash radius slightly. Reduced cost of V2 upgrade from 1000 to 500. - Raised Iron Curtained unit speed cap to 60 (Heavy Tank speed), or 112 for aircraft (Hind speed). - Increased power consumption of basic defenses from 10 to 15 (was previously reduced from 25). - Increased Battle Fortress HP from 120k to 130k HP. Range to 5.75 (to match Apoc, Tripod etc.). - Reduced Tesla Track HP from 22k to 20k. - Increased Floating Disc range by 1. - Increased Tank Destroyer range by 1. Reduced HP from 46k to 44k. - Reduced Tomahawk price from 2000 to 1850. - Reduced Hypercharge upgrade cost from 1000 to 750. - Changed Mobile Sensor to light armor. - Increased Aurora cost from 2200 to 2300. Reduced splash radius vs infantry. Damage reduction reduced from 20% to 10% when afternburner is active. Target must be enemy unit/building to activate afterburner. - Slightly increased Banshee splash damage. - Reduced X-O Powersuit range by 1. Increased turn rate by 33%. - Increased Desolator damage vs light. Slightly increased splash damage vs infantry. Reduced deploy time. - Atomized debuff slows target by 25%, up from 15%. - Reduced Pitbull cost from 1000 to 900. Increased missile speed. - Increased Peacemaker cost from 2400 to 2500. - 8x RAGL 15 1v1 maps. - 3x other 1v1 maps. - 37x new team game maps. - Fixed undeployable starting location on Basalt Badlands map. - Prevent wormholes being destroyed in certain campaign missions. - Exclude Supply Truck from Oil Refinery price reduction.
- `a7c77671a3af802f6e492e0d198d7b1d8ceefa2b` (2023-08-05T23:17:09+01:00) — Updates/fixes for engine.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `e78069c0a146e057cadc6940f90c3024bcf95722` (2021-02-07T20:13:22+10:00) — Update AI + Add Prism Forwarding

### `Traits/BotModules/BaseBuilderBotModuleCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `356e0301a50187da7c5b528674c2495b45fba2e7` (2025-06-07T20:57:22+01:00) — Engine update fixes part 2.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `b51ea31657d53f6b6784940da06e9a649032ee43` (2023-02-25T12:17:58Z) — Fixed lower AI difficulties stopping all production. Improved low cash handling.
- `48662a1b87d47cf503897db1524ea68b226adb63` (2022-09-02T17:33:05+01:00) — AI improvements (MQ performance, prevents AI delaying production when repeatedly trying to produce units that are maxed out, added building intervals to space out the production of certain buildings).
- `bb6b87a63aca752376be0aa558c8883161216d80` (2022-08-27T17:31:29+01:00) — Remove AI MaxAirProduction (no longer needed with Helipad/Airfield merge).
- `dbe179cd638432320815f9e0517a98041d3137d8` (2022-08-19T20:18:32+01:00) — AI improvements for MQ to better enforce structure limits.
- `d3b7300ad198b7bce34b21cf407038f4dfff2e13` (2022-02-04T16:36:33Z) — Corrected StructureProductionActiveDelay default value in AI BaseBuilderBotModuleCA.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `c5e8947e96bfb6951420436201dca55af97886b5` (2022-01-17T15:10:47Z) — Make AI maximum refineries scale with number of construction yards (means AI is more likely to build a refinery at its expansions).
- `bdde57c086a5ff55e7006bfa6db2fc6b90d5ab2d` (2021-12-31T12:36:49Z) — Added random chance threshold to AI selling with a lower chance if building is within the main base. Tweak to AI repairing.
- `3ffec1ffc6a091cc3b402f82769d05f5d1c1ddef` (2021-12-14T17:43:05Z) — Refactored AI selling code.
- `2480147f086cf04ced3e3258f5d0f71458c4f057` (2021-12-14T23:25:57+10:00) — Allow AI to Sell buildings when
- `5cd360e6626a8ccd00ed180afedc9dcf2b2e1acb` (2021-12-02T03:36:23+10:00) — Tidy
- `8e2cd3d7217e05a742bae892af1d1e78b3195d18` (2021-12-02T00:52:06+10:00) — Allow AI to Sell structures
- `c27f4e185fecef6e85a3ec8feac00fef608c8d6c` (2021-02-04T22:17:48Z) — Trim trailing whitespace and fix line endings.
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `2944eeee20609651b8dba09d38017f4bb2ade3be` (2020-05-16T16:44:14+01:00) — Added max refineries and max harvesters bot settings to prevent Allies building double the number of other factions due to addition of Chrono Miner. Removed refinery limits and harvester limits/fractions as base builder and harvester modules take care of these. Added proc prerequisite to proc.chrono.
- `288aadcd79243285121cfbceb5bf4ed8efea7ea7` (2020-04-20T23:12:31+01:00) — AI difficulty tuning. Added Very Hard difficulty to make the gap between difficulties (particularly between Easy and Normal) less wide. Made the AI more likely to spread anti-air defenses around their base by dividing PlaceDefenseTowardsEnemyChance by 1.5 (anti-ground defenses are unaffected).
- `dd626aaaa854172427a94747fff871ca9d14a3dc` (2020-04-20T23:12:31+01:00) — AI difficulty tuning. Added Very Hard difficulty to make the gap between difficulties (particularly between Easy and Normal) less wide. Made the AI more likely to spread anti-air defenses around their base by dividing PlaceDefenseTowardsEnemyChance by 1.5 (anti-ground defenses are unaffected).

### `Traits/BotModules/BotModuleLogic/BaseBuilderQueueManagerCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `b51ea31657d53f6b6784940da06e9a649032ee43` (2023-02-25T12:17:58Z) — Fixed lower AI difficulties stopping all production. Improved low cash handling.
- `48662a1b87d47cf503897db1524ea68b226adb63` (2022-09-02T17:33:05+01:00) — AI improvements (MQ performance, prevents AI delaying production when repeatedly trying to produce units that are maxed out, added building intervals to space out the production of certain buildings).
- `af26aef9e2c030e8f797597bceaa117ade7eeb6e` (2022-09-02T16:39:34+01:00) — Crash fix.
- `bb6b87a63aca752376be0aa558c8883161216d80` (2022-08-27T17:31:29+01:00) — Remove AI MaxAirProduction (no longer needed with Helipad/Airfield merge).
- `dbe179cd638432320815f9e0517a98041d3137d8` (2022-08-19T20:18:32+01:00) — AI improvements for MQ to better enforce structure limits.
- `9199548ccb0f57318425e6d2489455f324157613` (2022-07-29T18:24:46+01:00) — Reduce Shard Walker upgrade cost to 750. Make Point Defense Shield charge time scaleable with damage. Fix potential crash if no UnitIntervals set.
- `2840f3b24800adc1551eb06154f01ef0e334b655` (2022-07-26T21:29:15+01:00) — Speculative fix for very rare crash caused by AI trying to add plug to a building at the moment it's destroyed.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `9cfce9297022419467fee71976aff77675c072dd` (2022-04-09T13:01:23+01:00) — Fixes for updates.
- `6b538078f2e77e1045b63b41e7f5467de6404f14` (2022-02-20T12:18:12+10:00) — Cleanup VS issues
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `956407be63a8d760ffa7020d34617ce7bf10ca2f` (2021-01-31T03:26:03+10:00) — Fix prereq's & allow AI to build plugs
- `2944eeee20609651b8dba09d38017f4bb2ade3be` (2020-05-16T16:44:14+01:00) — Added max refineries and max harvesters bot settings to prevent Allies building double the number of other factions due to addition of Chrono Miner. Removed refinery limits and harvester limits/fractions as base builder and harvester modules take care of these. Added proc prerequisite to proc.chrono.
- `288aadcd79243285121cfbceb5bf4ed8efea7ea7` (2020-04-20T23:12:31+01:00) — AI difficulty tuning. Added Very Hard difficulty to make the gap between difficulties (particularly between Easy and Normal) less wide. Made the AI more likely to spread anti-air defenses around their base by dividing PlaceDefenseTowardsEnemyChance by 1.5 (anti-ground defenses are unaffected).
- `dd626aaaa854172427a94747fff871ca9d14a3dc` (2020-04-20T23:12:31+01:00) — AI difficulty tuning. Added Very Hard difficulty to make the gap between difficulties (particularly between Easy and Normal) less wide. Made the AI more likely to spread anti-air defenses around their base by dividing PlaceDefenseTowardsEnemyChance by 1.5 (anti-ground defenses are unaffected).
- `5a8b1e934a0c1397f3f0b4bb1e88c51513643b74` (2020-03-16T08:16:20Z) — Fix AI production

### `Traits/BotModules/BuildingRepairBotModuleCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `cb00e65f786ed1c911437ff4c7ae63f2a4ef6529` (2026-07-26T19:56:19+01:00) — Fix AI not repairing buildings.
- `ea1b851088cb523c23c3f9b7b1f4d1c6b4d0a2a3` (2025-12-07T16:13:06Z) — Clean up trait lookups.
- `51e9df06b1734646d67c7d1baf4a421cc109dcb1` (2023-08-06T18:02:38+01:00) — Minor fixes.
- `45736b7a2ee7f515b156cbed6a0f18c399e71045` (2023-06-06T17:35:44+01:00) — Removed Enlightened EMP target circle and added some voice lines. Rare crash fix (fix from engine).
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `bdde57c086a5ff55e7006bfa6db2fc6b90d5ab2d` (2021-12-31T12:36:49Z) — Added random chance threshold to AI selling with a lower chance if building is within the main base. Tweak to AI repairing.
- `302c676f1f3aebb0cc1aa2e92e74877f6ef9f4ab` (2021-12-29T00:56:40+10:00) — Try get AI to repair more

### `Traits/BotModules/HarvesterBotModuleCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `1e72c67057d0efe246fcbe4a384217772f573345` (2022-11-27T12:41:35Z) — AI should not command harvesters that cannot be ordered (aligns with engine change).
- `cd345f6e95264832098d88c712f4d0a7e6cb25c7` (2022-08-13T10:19:59+01:00) — Restored changes for hierarchical pathfinder.
- `f84fc018a8050efcd413e3f59a842de9ab686e73` (2022-08-09T23:02:14+01:00) — Temporarily reverted changes for hierarchical pathfinder.
- `6491a1f0194822d8f39f2a0303edc348413f667a` (2022-08-06T12:28:49+01:00) — Engine update changes.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `60c7c5a5f6b62f038778e30006d008a05227c1ec` (2022-04-22T14:35:02+01:00) — Fixes after master merge.
- `11637502c3344da1167b94434a5727d4537aad7a` (2022-04-21T12:14:10+01:00) — Fixes for updates.
- `9cfce9297022419467fee71976aff77675c072dd` (2022-04-09T13:01:23+01:00) — Fixes for updates.
- `6b538078f2e77e1045b63b41e7f5467de6404f14` (2022-02-20T12:18:12+10:00) — Cleanup VS issues
- `eed1e75fa0d574d8532d6a326cafcdfff8597ac7` (2022-01-31T22:55:56Z) — TurretedFloating fix. EMP missile fix. Minor adjustments to match engine classes. Removed ContrailCA, RevealsMapCA and RepairableNearCA as the engine versions seem to do everything we need now.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `8914728193859ab20ab4ca30f117082c80433ed9` (2022-01-15T15:30:27Z) — AI - Added AI unit intervals to control how frequently certain units are built (e.g. MCVs, harvesters and commandos). - Unit limits/delays will now work correctly for externally requested units (MCVs and harvesters). - When looking for a new resource patch AI harvesters will now only scan the destination for enemies rather than the entire path.
- `1ab01efa5f850b8e64c7991b479e9054fa40afde` (2021-03-23T16:49:33+10:00) — Remove Possible Desync Sources
- `3545e78cbac89a596abacdbaf5d07ee40feabc4c` (2021-03-08T02:28:30+10:00) — Add Ion Storm Upgrade
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `10454de58eb1eb40be48bc41fe3560aa337311f8` (2020-08-28T21:05:21+01:00) — Restored a modified HarvesterBotModuleCA with less frequent checks for sufficient and idle harvesters.
- `2944eeee20609651b8dba09d38017f4bb2ade3be` (2020-05-16T16:44:14+01:00) — Added max refineries and max harvesters bot settings to prevent Allies building double the number of other factions due to addition of Chrono Miner. Removed refinery limits and harvester limits/fractions as base builder and harvester modules take care of these. Added proc prerequisite to proc.chrono.
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo

### `Traits/BotModules/MCVManagerBotModuleCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `356e0301a50187da7c5b528674c2495b45fba2e7` (2025-06-07T20:57:22+01:00) — Engine update fixes part 2.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `e68cdfeb45dfd01fd3e529923daeed488e12aa19` (2021-02-04T12:43:09+10:00) — Increase Bot MCV placement chance
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo

### `Traits/BotModules/PowerDownBotModuleCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `356e0301a50187da7c5b528674c2495b45fba2e7` (2025-06-07T20:57:22+01:00) — Engine update fixes part 2.
- `0dd06eed212fd88483fed8386f3f4c9b0195e708` (2023-08-20T08:28:07+08:00) — Fix dysfunction of PowerDownBotModuleCA on loading saved game
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `4b92156e3c5b9aae08b33f026ac33d4cc74f344d` (2021-02-14T21:49:51+08:00) — AI-cs-fix
- `b925cbe573e3f27be17912350ef7e591df403434` (2020-11-21T20:56:53+08:00) — AI Squad & PowerDown up2date fixes
- `a9494a8f59131bbae6a7babbe54004b57f75a842` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:
- `22d5e5e89f8b22091144088bc02a04b854ca7b5b` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:

### `Traits/BotModules/SquadManagerBotModuleCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `4e00d215b22f7b2cf61e88cbe14ef4f76425f1ed` (2026-02-09T21:27:45Z) — - Increased IFV HP from 30k to 32k. - Tiger Guard IFV prioritizes vehicle targets. - Increased Peacemaker damage vs defenses. - Clean up V3 upgrade remnants. - AI tweaks.
- `d3b5e8887532288d3ad4aa76a584490df8081d8c` (2026-02-08T21:18:06Z) — Compositions.
- `2bad89a779e49e6f984aa3b7b352ea210516b587` (2026-02-06T17:38:48Z) — Updated AI routing.
- `55e042954afbfb2e739fc2b8b8b3d22fc37bdcd8` (2026-02-03T16:41:51Z) — AI harasser squads.
- `9a68fea1584271fee9363ac6dc1b108cabc850f4` (2026-01-31T16:24:09Z) — Skirmish AI indirect routes of attack.
- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `356e0301a50187da7c5b528674c2495b45fba2e7` (2025-06-07T20:57:22+01:00) — Engine update fixes part 2.
- `162f00bb6cc9c064f9c45b95334213e58130fa2c` (2025-05-26T10:38:38+01:00) — Skirmish AI aircraft target based on armor type instead of target type.
- `8e9da5778cb92c42a7f1393eb30204fb8cc211da` (2024-01-17T18:17:30Z) — Adjusted AI initial squad targeting behaviour.
- `baca1fc0dbd60fb2abd5597f476eadff4111e777` (2023-06-04T20:23:41+01:00) — Added targeted weapon ability functionality. - Enlightened can target EMP ability. Reduced speed, damage, EMP duration and EMP area of effect. - Updated teleporting units so deploy command can be used on a group. - Code formatting fixes.
- `877332a4aab5fd9c1d7d5338184d6cb0f8477942` (2023-05-31T21:28:37+01:00) — Removed broken AI "rushing". Added a chance for AI squads to select high priority targets.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `bb5187da665f9179d7f475b39702ab11b75f706d` (2022-09-05T18:08:58+01:00) — Increased difficulty for hard mode of Crossrip. Prevent AI repeatedly ordering to defend on buildings taking damage.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `6b538078f2e77e1045b63b41e7f5467de6404f14` (2022-02-20T12:18:12+10:00) — Cleanup VS issues
- `16b6987bae21cd3e952e3364d1d91fa8f0ab3dce` (2022-02-06T12:10:36Z) — BulletCA/MissileCA fixes. Restored ProduceActorPowerCA crash fix. Removed some traits no longer used. Extra tweaks to bring things more into line with engine equivalents.
- `e9a52495d7dbdfaa3d2856abffd0e398224094ad` (2021-11-30T22:14:17+10:00) — Fix Error
- `1455d65c1f3aba5aba67059a581c870978f2a1d0` (2021-11-27T21:05:05Z) — Fixed random squad bonuses not applying due to recalculating every tick (so it would almost always settle for the lowest possible value). Adjusted squad sizes and bonuses to account for it working now correctly.
- `58aaaa0e4cbb60e49359f83ec1c723d6e66b188b` (2021-11-27T15:05:20Z) — AI bugfix (lower difficulties were looking at the Brutal config for deciding if it should wait for more aircraft to be built).
- `cf6265d13eb5399c499cec83329132522c1760ac` (2021-11-23T15:32:58Z) — Revert "AI air superiority improvements."

### `Traits/BotModules/Squads/SquadCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `2bad89a779e49e6f984aa3b7b352ea210516b587` (2026-02-06T17:38:48Z) — Updated AI routing.
- `55e042954afbfb2e739fc2b8b8b3d22fc37bdcd8` (2026-02-03T16:41:51Z) — AI harasser squads.
- `9a68fea1584271fee9363ac6dc1b108cabc850f4` (2026-01-31T16:24:09Z) — Skirmish AI indirect routes of attack.
- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `b2286da8eabf18577b63bd049875d8fdd8cc153c` (2022-02-02T13:01:13Z) — Additional changes to bring customised traits in line with their base versions as far as possible. Added descriptions to these classes to explain the differences with base versions.
- `cf6265d13eb5399c499cec83329132522c1760ac` (2021-11-23T15:32:58Z) — Revert "AI air superiority improvements."
- `a21ab12bbfa958076417594900a32ea15bfdd61c` (2021-11-23T15:32:58Z) — AI air superiority and squad management improvements.
- `1bd39937aae03f37066b2ea8e562463d6a473c65` (2021-11-23T15:32:58Z) — AI air superiority improvements.
- `7ca8ca473be53c4751b9ce41e58ee5ccb11f8211` (2021-04-08T00:29:40+10:00) — Change CA AI Back for further Development
- `e78069c0a146e057cadc6940f90c3024bcf95722` (2021-02-07T20:13:22+10:00) — Update AI + Add Prism Forwarding
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `38e5c357768b00a23b450f1031cf8be478138bf9` (2020-08-25T16:07:55+08:00) — Fix name space of ProtectionState
- `72b68f8da2677e0b88bbf21cc706a69116c32aba` (2020-04-29T17:04:35+01:00) — Add Siege Tank & Sukhoi
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo
- `e9a0a8fe87184a5a5a5aa743c650e12b631b32f3` (2020-01-23T06:39:55Z) — Clone Squad AI logic + AI Changes

### `Traits/BotModules/Squads/States/AirStatesCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `71754fc0647fde6b9559ae43fff8cb00ff392f76` (2026-01-01T11:45:03Z) — Fix AI aircraft limits.
- `53d7a35e577e0c783f7b583a9fdfb152336a3f56` (2026-01-01T11:45:03Z) — Fix AI aircraft limits.
- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `f9bb5de994ff74fb347acc45b4e93a7b0b81ea4b` (2025-06-08T12:49:39+01:00) — AI crash fix.
- `162f00bb6cc9c064f9c45b95334213e58130fa2c` (2025-05-26T10:38:38+01:00) — Skirmish AI aircraft target based on armor type instead of target type.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `8e4cdb783a81b63906327296645d1a2d025886ba` (2022-10-02T16:46:02+01:00) — Crossrip bugfix and increased Halo/landing craft HP. Reflected some minor engine changes in corresponding classes.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `58aaaa0e4cbb60e49359f83ec1c723d6e66b188b` (2021-11-27T15:05:20Z) — AI bugfix (lower difficulties were looking at the Brutal config for deciding if it should wait for more aircraft to be built).
- `cf6265d13eb5399c499cec83329132522c1760ac` (2021-11-23T15:32:58Z) — Revert "AI air superiority improvements."
- `a21ab12bbfa958076417594900a32ea15bfdd61c` (2021-11-23T15:32:58Z) — AI air superiority and squad management improvements.
- `1bd39937aae03f37066b2ea8e562463d6a473c65` (2021-11-23T15:32:58Z) — AI air superiority improvements.
- `c45c846ea6ce2b0dc3584739fb40e5804a81716c` (2021-08-14T16:51:55+01:00) — Fixed AI Mothership getting stuck idle. Added a MothershipAttackBehaviour trait so that motherships always fire for full duration of beam even if target dies. Reduced the duration of the beam. Allow target types to be defined for AI air squads (e.g. so motherships only attack structures). Removed AI mothership actor and weapons as no longer needed with these changes.
- `e3c18093924e7c7840b1a6842f4d693cde4e530a` (2021-05-20T19:05:33+01:00) — AI air squads composed of aircraft that can attack other aircraft have a 65% chance to prioritise the closest enemy aircraft. Restored code for making AI assign aircraft to squads of a single aircraft type. Fixed minor styling in Shielded trait.
- `7ca8ca473be53c4751b9ce41e58ee5ccb11f8211` (2021-04-08T00:29:40+10:00) — Change CA AI Back for further Development
- `4b92156e3c5b9aae08b33f026ac33d4cc74f344d` (2021-02-14T21:49:51+08:00) — AI-cs-fix
- `e78069c0a146e057cadc6940f90c3024bcf95722` (2021-02-07T20:13:22+10:00) — Update AI + Add Prism Forwarding
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `5a841f2ab5edba1616454fc84c3149d301c5698d` (2020-11-21T21:07:37+08:00) — AI SquadStates switching optimize
- `b925cbe573e3f27be17912350ef7e591df403434` (2020-11-21T20:56:53+08:00) — AI Squad & PowerDown up2date fixes

### `Traits/BotModules/Squads/States/GroundStatesCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `d3b5e8887532288d3ad4aa76a584490df8081d8c` (2026-02-08T21:18:06Z) — Compositions.
- `2bad89a779e49e6f984aa3b7b352ea210516b587` (2026-02-06T17:38:48Z) — Updated AI routing.
- `461dde736616df2cfa2dcb623e1b0e2aa036a0b4` (2026-02-04T20:24:41Z) — - V3 now Ukraine unique unit. - Siege Tank now replaces V2 for Ukraine. - Yaml fixes.
- `55e042954afbfb2e739fc2b8b8b3d22fc37bdcd8` (2026-02-03T16:41:51Z) — AI harasser squads.
- `9a68fea1584271fee9363ac6dc1b108cabc850f4` (2026-01-31T16:24:09Z) — Skirmish AI indirect routes of attack.
- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `29e2630eb969f547c2aaf987e273691dd7f300e7` (2023-12-22T17:17:27Z) — Minor misc updates. - AI should only check for high value targets from idle state. - Removed unnecessary "chem" locomotor. - Lua function naming. - Line endings.
- `baca1fc0dbd60fb2abd5597f476eadff4111e777` (2023-06-04T20:23:41+01:00) — Added targeted weapon ability functionality. - Enlightened can target EMP ability. Reduced speed, damage, EMP duration and EMP area of effect. - Updated teleporting units so deploy command can be used on a group. - Code formatting fixes.
- `877332a4aab5fd9c1d7d5338184d6cb0f8477942` (2023-05-31T21:28:37+01:00) — Removed broken AI "rushing". Added a chance for AI squads to select high priority targets.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `7ca8ca473be53c4751b9ce41e58ee5ccb11f8211` (2021-04-08T00:29:40+10:00) — Change CA AI Back for further Development
- `4b92156e3c5b9aae08b33f026ac33d4cc74f344d` (2021-02-14T21:49:51+08:00) — AI-cs-fix
- `e78069c0a146e057cadc6940f90c3024bcf95722` (2021-02-07T20:13:22+10:00) — Update AI + Add Prism Forwarding
- `ebe13613e07be31642b0f966a311aa220e893407` (2021-01-16T13:27:51+08:00) — Dismissed ground squad unit join idle unit
- `5a841f2ab5edba1616454fc84c3149d301c5698d` (2020-11-21T21:07:37+08:00) — AI SquadStates switching optimize
- `b925cbe573e3f27be17912350ef7e591df403434` (2020-11-21T20:56:53+08:00) — AI Squad & PowerDown up2date fixes
- `c0a623bddb1063bc9114f8b1c219d785a68e8884` (2020-10-22T15:49:50+10:00) — Revert Jump Jet to Aircraft
- `54326e736f896f1d588a6edae837c96a70121bf0` (2020-08-10T21:04:11+08:00) — Groundstate simplified
- `a9494a8f59131bbae6a7babbe54004b57f75a842` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:
- `22d5e5e89f8b22091144088bc02a04b854ca7b5b` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:

### `Traits/BotModules/Squads/States/NavyStatesCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `356e0301a50187da7c5b528674c2495b45fba2e7` (2025-06-07T20:57:22+01:00) — Engine update fixes part 2.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `cd345f6e95264832098d88c712f4d0a7e6cb25c7` (2022-08-13T10:19:59+01:00) — Restored changes for hierarchical pathfinder.
- `f84fc018a8050efcd413e3f59a842de9ab686e73` (2022-08-09T23:02:14+01:00) — Temporarily reverted changes for hierarchical pathfinder.
- `6491a1f0194822d8f39f2a0303edc348413f667a` (2022-08-06T12:28:49+01:00) — Engine update changes.
- `3a3d3248841606ff9ef8a88f80c5fb6fb249f77b` (2021-11-23T01:05:57+10:00) — Make Naval units squad by unit type
- `7ca8ca473be53c4751b9ce41e58ee5ccb11f8211` (2021-04-08T00:29:40+10:00) — Change CA AI Back for further Development
- `e78069c0a146e057cadc6940f90c3024bcf95722` (2021-02-07T20:13:22+10:00) — Update AI + Add Prism Forwarding
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `02327e6ec35581ead54d2cbbbc8d17b7d82f727a` (2021-01-16T14:03:36+08:00) — Upstream navy stuck check
- `da8406c4e875fcc023e8b443537cb9e0d68a2b93` (2021-01-16T13:46:32+08:00) — Navy squad won't be dismissed
- `5a841f2ab5edba1616454fc84c3149d301c5698d` (2020-11-21T21:07:37+08:00) — AI SquadStates switching optimize
- `b925cbe573e3f27be17912350ef7e591df403434` (2020-11-21T20:56:53+08:00) — AI Squad & PowerDown up2date fixes
- `a9494a8f59131bbae6a7babbe54004b57f75a842` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:
- `22d5e5e89f8b22091144088bc02a04b854ca7b5b` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:
- `72b68f8da2677e0b88bbf21cc706a69116c32aba` (2020-04-29T17:04:35+01:00) — Add Siege Tank & Sukhoi
- `e9a0a8fe87184a5a5a5aa743c650e12b631b32f3` (2020-01-23T06:39:55Z) — Clone Squad AI logic + AI Changes

### `Traits/BotModules/Squads/States/ProtectionStatesCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `9a68fea1584271fee9363ac6dc1b108cabc850f4` (2026-01-31T16:24:09Z) — Skirmish AI indirect routes of attack.
- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `7ca8ca473be53c4751b9ce41e58ee5ccb11f8211` (2021-04-08T00:29:40+10:00) — Change CA AI Back for further Development
- `4b92156e3c5b9aae08b33f026ac33d4cc74f344d` (2021-02-14T21:49:51+08:00) — AI-cs-fix
- `e78069c0a146e057cadc6940f90c3024bcf95722` (2021-02-07T20:13:22+10:00) — Update AI + Add Prism Forwarding
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `5a841f2ab5edba1616454fc84c3149d301c5698d` (2020-11-21T21:07:37+08:00) — AI SquadStates switching optimize
- `b925cbe573e3f27be17912350ef7e591df403434` (2020-11-21T20:56:53+08:00) — AI Squad & PowerDown up2date fixes
- `38e5c357768b00a23b450f1031cf8be478138bf9` (2020-08-25T16:07:55+08:00) — Fix name space of ProtectionState
- `a9494a8f59131bbae6a7babbe54004b57f75a842` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:
- `22d5e5e89f8b22091144088bc02a04b854ca7b5b` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:
- `72b68f8da2677e0b88bbf21cc706a69116c32aba` (2020-04-29T17:04:35+01:00) — Add Siege Tank & Sukhoi
- `ca6fbe5f05d3fd40ff449f3fba6ecfff8f09c43e` (2020-04-27T15:33:54+01:00) — Add Improved protective squads
- `e9a0a8fe87184a5a5a5aa743c650e12b631b32f3` (2020-01-23T06:39:55Z) — Clone Squad AI logic + AI Changes

### `Traits/BotModules/Squads/States/StateBaseCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `2bad89a779e49e6f984aa3b7b352ea210516b587` (2026-02-06T17:38:48Z) — Updated AI routing.
- `9a68fea1584271fee9363ac6dc1b108cabc850f4` (2026-01-31T16:24:09Z) — Skirmish AI indirect routes of attack.
- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `cf6265d13eb5399c499cec83329132522c1760ac` (2021-11-23T15:32:58Z) — Revert "AI air superiority improvements."
- `a21ab12bbfa958076417594900a32ea15bfdd61c` (2021-11-23T15:32:58Z) — AI air superiority and squad management improvements.
- `1bd39937aae03f37066b2ea8e562463d6a473c65` (2021-11-23T15:32:58Z) — AI air superiority improvements.
- `7ca8ca473be53c4751b9ce41e58ee5ccb11f8211` (2021-04-08T00:29:40+10:00) — Change CA AI Back for further Development
- `4b92156e3c5b9aae08b33f026ac33d4cc74f344d` (2021-02-14T21:49:51+08:00) — AI-cs-fix
- `e78069c0a146e057cadc6940f90c3024bcf95722` (2021-02-07T20:13:22+10:00) — Update AI + Add Prism Forwarding
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `b925cbe573e3f27be17912350ef7e591df403434` (2020-11-21T20:56:53+08:00) — AI Squad & PowerDown up2date fixes
- `a9494a8f59131bbae6a7babbe54004b57f75a842` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:
- `22d5e5e89f8b22091144088bc02a04b854ca7b5b` (2020-08-02T08:59:28+08:00) — Overall AI upgrade:
- `ca6fbe5f05d3fd40ff449f3fba6ecfff8f09c43e` (2020-04-27T15:33:54+01:00) — Add Improved protective squads
- `e9a0a8fe87184a5a5a5aa743c650e12b631b32f3` (2020-01-23T06:39:55Z) — Clone Squad AI logic + AI Changes

### `Traits/BotModules/UnitBuilderBotModuleCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `0a863cc8ee1f8ab4a2ae23d18847cef95f603196` (2026-04-23T20:42:51+01:00) — Fix bot crash (Naval AI).
- `1156c4eb355808599c05ca485a967d41e56e12d2` (2026-02-12T17:39:59Z) — AI tweaks.
- `4e00d215b22f7b2cf61e88cbe14ef4f76425f1ed` (2026-02-09T21:27:45Z) — - Increased IFV HP from 30k to 32k. - Tiger Guard IFV prioritizes vehicle targets. - Increased Peacemaker damage vs defenses. - Clean up V3 upgrade remnants. - AI tweaks.
- `d3b5e8887532288d3ad4aa76a584490df8081d8c` (2026-02-08T21:18:06Z) — Compositions.
- `cdafd6c2034ef326a063166e1b6d3341dfe2548c` (2026-01-09T07:12:23Z) — Remove bot debugging.
- `71754fc0647fde6b9559ae43fff8cb00ff392f76` (2026-01-01T11:45:03Z) — Fix AI aircraft limits.
- `53d7a35e577e0c783f7b583a9fdfb152336a3f56` (2026-01-01T11:45:03Z) — Fix AI aircraft limits.
- `b831676de3610212404aa9bf5e5656e24d630af7` (2025-08-10T16:03:40+01:00) — AI updates.
- `356e0301a50187da7c5b528674c2495b45fba2e7` (2025-06-07T20:57:22+01:00) — Engine update fixes part 2.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `b51ea31657d53f6b6784940da06e9a649032ee43` (2023-02-25T12:17:58Z) — Fixed lower AI difficulties stopping all production. Improved low cash handling.
- `48662a1b87d47cf503897db1524ea68b226adb63` (2022-09-02T17:33:05+01:00) — AI improvements (MQ performance, prevents AI delaying production when repeatedly trying to produce units that are maxed out, added building intervals to space out the production of certain buildings).
- `0f485b42e257fd345a648e9d5b7a7df05dc96bc1` (2022-08-16T18:03:35+01:00) — Multi-queue.
- `9199548ccb0f57318425e6d2489455f324157613` (2022-07-29T18:24:46+01:00) — Reduce Shard Walker upgrade cost to 750. Make Point Defense Shield charge time scaleable with damage. Fix potential crash if no UnitIntervals set.
- `8914728193859ab20ab4ca30f117082c80433ed9` (2022-01-15T15:30:27Z) — AI - Added AI unit intervals to control how frequently certain units are built (e.g. MCVs, harvesters and commandos). - Unit limits/delays will now work correctly for externally requested units (MCVs and harvesters). - When looking for a new resource patch AI harvesters will now only scan the destination for enemies rather than the entire path.
- `cf6265d13eb5399c499cec83329132522c1760ac` (2021-11-23T15:32:58Z) — Revert "AI air superiority improvements."
- `a21ab12bbfa958076417594900a32ea15bfdd61c` (2021-11-23T15:32:58Z) — AI air superiority and squad management improvements.
- `1bd39937aae03f37066b2ea8e562463d6a473c65` (2021-11-23T15:32:58Z) — AI air superiority improvements.
- `c27f4e185fecef6e85a3ec8feac00fef608c8d6c` (2021-02-04T22:17:48Z) — Trim trailing whitespace and fix line endings.
- `5a8b1e934a0c1397f3f0b4bb1e88c51513643b74` (2020-03-16T08:16:20Z) — Fix AI production

### `Traits/BotModules/UnitCompositionsBotModule.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `22508a52e3b17212ec7a903f7c60c76ca0347a39` (2026-02-20T07:15:55Z) — Mission crash fix caused by UnitCompositionsBotModule.
- `1156c4eb355808599c05ca485a967d41e56e12d2` (2026-02-12T17:39:59Z) — AI tweaks.
- `b4f1f7c3ad227b3cdf8c45471bdd9d8dba643d06` (2026-02-12T12:13:47Z) — Yaml fix.
- `d3b5e8887532288d3ad4aa76a584490df8081d8c` (2026-02-08T21:18:06Z) — Compositions.

### `Traits/ChangesHealthVersus.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `304e81220dd5bfca1de0e8d6f5f3d1383c9cb1b5` (2021-06-19T12:30:30+01:00) — Despoiler-11. New Scrin subfaction with Leecher and Atomizer unique units.

### `Traits/ChargingSelfDestruct.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `c72dd9565c02b5d75f1101cec9d671f6aa16a802` (2025-06-07T19:22:54+01:00) — Engine update fixes.
- `090f33479b9816b2045d929a5b4d9914ac9ee6e7` (2023-08-05T12:01:44+01:00) — 2307 engine fixes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `2e9dcc49f28d07e63463ac104a8afad6e92df6b7` (2020-03-16T06:51:43Z) — Fix GrantTimedConditionOnDeploy & EMP
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo
- `6d0ff33bfd1edc9fe5bf3c43f319f8128e3612ee` (2019-12-14T19:14:58Z) — 0.60.1

### `Traits/ChronoshiftableCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `ea1b851088cb523c23c3f9b7b1f4d1c6b4d0a2a3` (2025-12-07T16:13:06Z) — Clean up trait lookups.
- `bff362a26fc9cddf57334d3dad7194b2f7c5eeed` (2025-10-19T12:39:23+01:00) — Speculative fix for interrupted Chronoshift.
- `053891d201921a06b98120470005f8269198f77a` (2025-10-14T08:03:19+01:00) — - Fixed Dissection bombing runs continuing after secondary objective completed. - Oil Derrick just gives $125 per 15s with no bonus. - Reverted Venom random shot delay as it prevented returning to base when ammo depleted. - Added 5 second delay before initial Medic/Mechanic produced from Hospital/Machine Shop. - Speculative fix for failed Chronoshifting of enemy units.
- `d248b730207afd2ac96559cda806fabdeb7f20ef` (2024-12-28T22:24:19Z) — - Increased Tank Destroyer range by 1. Reduced HP from 44k to 42k. - Fixed allied passenger ownership when chronoshifted transport is killed. - Conditional CloneProducer (for missions). - Show "watched" icon on units with a shadow beacon attached. - Attached Shadow Beacons and Watcher parasites detect cloak. - Minor campaign AI code fix. - Allow 10 hotkeys for support powers. - Reckoning tweaks.
- `bbfbeb8c1aea5f8a7324e385803986e62f122b7e` (2024-05-27T09:26:25+01:00) — Allow missile strike power to use ballistic/cruise missiles. Prevent gateway being spawned on top of actors.
- `77e417706372379d81e1c7015b410b2ecfa25139` (2024-02-09T18:57:22Z) — Updates. - Increased Juggernaut cost from $1500 to $2000. Increased range, HP and damage. - Reduced PAC cost from $3000 to $2800. - Reduced damage radius from shot down missiles a little more. - Limited AI V3/TH at Hard difficulty and below. - Fixed rare crashing bug caused by missiles effectively diving underground.
- `cafc8fe9b2e7b464c53d13ae6ba134e13d8dde85` (2023-08-30T13:09:26+01:00) — Balance/misc: - Allow advanced cyborgs to be chronoshifted. - Cap health at 47k while chronoshifted. - Reduced Greater Coalescence cooldown from 4:30 to 4:00. - Fixed missing Soviet force shield. - Exclude husks from chronoshift targeting.
- `d9195fff74eb3aeccfa1324f95a6ac453055c103` (2023-08-28T17:24:02+01:00) — Added MaxEnemyUnits to Chronoshift. Added separate warp sequences for the power itself. Revert to killing passengers.
- `d5360301091213ba7dfe6d2fb41ae7495192dff1` (2023-08-21T23:13:45+01:00) — Misc - Reduced chronoshift duration for enemy units. - Restored return on death. - Cargo no longer killed on chronoshift, but can't be unloaded until returning. - Mission 2 crash fix. - Improved support power unit count. - Fixed Ion Conduits activating when Storm Column is powere down.
- `a0883e44e75e64dea8a6d90a24f502d47fc08892` (2023-08-19T21:02:51+01:00) — Fix Chronoshift desync.
- `442298d0bf8deeb79a0182ea5e3925e9ef1d19fb` (2023-08-19T15:32:34+01:00) — Added ChronoshiftPowerCA and renamed ChronoshiftableWithSpriteEffect to ChronoshiftableCA.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `8de9bd7c05701078e403ac15d831d9b3c8650bf2` (2022-11-23T16:44:19Z) — Fixed crash when chronoshifted unit is killed by a shootable missile.
- `15aa57e6bc4e76dfafdfdd78c3daf77e2998bdea` (2022-06-15T22:28:57+01:00) — Fixes after merge.
- `3e1ae6809de86ab2c80adae1ba536bfb6e625f96` (2022-06-11T07:10:22+01:00) — Fixed errors.
- `98681f3a1a42b41333f6f665d66224d6e1a602c4` (2022-06-10T16:21:08+01:00) — Misc. - Fixed being able to prevent Chronoshift return by spamming attack or attack move. - Don't play unit lost notification on Brute mutation. - Reduce gap cloud opacity a little. - Remove GuardsSelection from MGG. - Don't reset MGG stacks when switching targets. - Projectile improvements to PlasmaBeam and ElectricBolt.
- `3f9daada297e4a6532d75a368a4fb01e1eb974de` (2022-06-03T10:51:21+01:00) — Fix code style errors.
- `246a31fecedcb2fc8551002680e8fc88150850f6` (2022-06-03T10:12:03+01:00) — Only friendly units benefit from returning to avoid death when chronoshifted.
- `95c22844a1bf08fdd5324d8b6d205f3ac9831187` (2022-06-02T10:15:37+01:00) — Chronoshift/Fixes - Chronoshifted units will return to origin with 20% HP instead of being killed. - Added unit detection to Advanced Comms Center. - Fixed bug where RangedGpsProvider revealed units outside of range if created after the enemy created one first.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update

### `Traits/Conditions/GrantChargingCondition.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `6eddd5e7960766dea951673618f5edd275eb8584` (2021-10-29T21:36:02+01:00) — Traits for Orca Afterburner.
- `cb1b5ade2bf156e54623ef72be219edcdacdf2d2` (2021-10-27T19:50:02+01:00) — GrantDischargingCondition trait for Orca afterburner.

### `Traits/Conditions/GrantConditionOnAttackCA.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `1ed842152534dbf84947813552da46bc82c5bdde` (2024-03-23T10:49:45Z) — Updates. - Increased V2 splash radius slightly. Reduced cost of V2 upgrade from 1000 to 500. - Raised Iron Curtained unit speed cap to 60 (Heavy Tank speed), or 112 for aircraft (Hind speed). - Increased power consumption of basic defenses from 10 to 15 (was previously reduced from 25). - Increased Battle Fortress HP from 120k to 130k HP. Range to 5.75 (to match Apoc, Tripod etc.). - Reduced Tesla Track HP from 22k to 20k. - Increased Floating Disc range by 1. - Increased Tank Destroyer range by 1. Reduced HP from 46k to 44k. - Reduced Tomahawk price from 2000 to 1850. - Reduced Hypercharge upgrade cost from 1000 to 750. - Changed Mobile Sensor to light armor. - Increased Aurora cost from 2200 to 2300. Reduced splash radius vs infantry. Damage reduction reduced from 20% to 10% when afternburner is active. Target must be enemy unit/building to activate afterburner. - Slightly increased Banshee splash damage. - Reduced X-O Powersuit range by 1. Increased turn rate by 33%. - Increased Desolator damage vs light. Slightly increased splash damage vs infantry. Reduced deploy time. - Atomized debuff slows target by 25%, up from 15%. - Reduced Pitbull cost from 1000 to 900. Increased missile speed. - Increased Peacemaker cost from 2400 to 2500. - 8x RAGL 15 1v1 maps. - 3x other 1v1 maps. - 37x new team game maps. - Fixed undeployable starting location on Basalt Badlands map. - Prevent wormholes being destroyed in certain campaign missions. - Exclude Supply Truck from Oil Refinery price reduction.

### `Traits/Conditions/GrantConditionOnHealingReceived.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `856427308cf3f846691acab06f95886187f8e365` (2023-07-29T18:41:47+01:00) — Collector-73 reworks & misc changes. - Atomized debuff pulses AoE damage and slows movement speed, instead of being a single target DoT that also reduces firepower. No longer spreads. - Replaced Feeder Mutation power with Greater Coalescence. Spawns a larger controllable version of Leecher orb which heals allies and slows/drains enemies. - Feeder renamed to Burster and can be produced by all Scrin with Tech Center. No longer harvests to charge up. - Added spawn/death animation for Buzzer Swarm. - Added player coloured selection box to Buzzer Swarm, Leecher Orb. - Increased Nanite Repair tick rate slightly. - Fixed PeriodicExplosion initial delay. - Corrected ARC Recon Drone voice line.

### `Traits/Conditions/GrantConditionOnOrders.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `1bc8de13a2a1dc0d9cec673e25894d46b26866bf` (2025-05-10T09:10:47+01:00) — - Fixed upgrading existing units. - Fixed Subterranean APC armor type. - Increased Confessor range by 1. - Storm Spikes no longer count towards Nod Covenant acquisition. - Voidspikes will also convert Ore/Gems. - Tormentor fires 6 shots per pass instead of 4 (taking 2 passes to fully unload, down from 3). Increased damage per shot slightly. - Allied Development meter threshold bars won't use the lighter color until the exact percentage is reached. - Fixed Aurora gaining afterburner when attacking friendly targets. - Increaded Voidspike HP from 30k to 40k. Increased conversion rate. Reduced cooldown from 5:00 to 4:00. Starts fully charged. - Reduced development level times from 4/12/20 minutes to 4/10/16 minutes. Reverted Time Skip cost/cooldown to 1000/2s. - Reduced cost of coalition upgrades from 750 to 500. Reduced policy upgrades from 500 to 300.
- `fe6c95dcebc6813e74b78dc765d3b57e56d8e9c4` (2024-04-20T12:11:14+01:00) — Fix queued orders cancelling Aurora afterburner.
- `b111fea1c9d809d2e95fa81c818d5463911b2cda` (2024-04-01T07:32:54+01:00) — Aurora afterburner fix.
- `1ed842152534dbf84947813552da46bc82c5bdde` (2024-03-23T10:49:45Z) — Updates. - Increased V2 splash radius slightly. Reduced cost of V2 upgrade from 1000 to 500. - Raised Iron Curtained unit speed cap to 60 (Heavy Tank speed), or 112 for aircraft (Hind speed). - Increased power consumption of basic defenses from 10 to 15 (was previously reduced from 25). - Increased Battle Fortress HP from 120k to 130k HP. Range to 5.75 (to match Apoc, Tripod etc.). - Reduced Tesla Track HP from 22k to 20k. - Increased Floating Disc range by 1. - Increased Tank Destroyer range by 1. Reduced HP from 46k to 44k. - Reduced Tomahawk price from 2000 to 1850. - Reduced Hypercharge upgrade cost from 1000 to 750. - Changed Mobile Sensor to light armor. - Increased Aurora cost from 2200 to 2300. Reduced splash radius vs infantry. Damage reduction reduced from 20% to 10% when afternburner is active. Target must be enemy unit/building to activate afterburner. - Slightly increased Banshee splash damage. - Reduced X-O Powersuit range by 1. Increased turn rate by 33%. - Increased Desolator damage vs light. Slightly increased splash damage vs infantry. Reduced deploy time. - Atomized debuff slows target by 25%, up from 15%. - Reduced Pitbull cost from 1000 to 900. Increased missile speed. - Increased Peacemaker cost from 2400 to 2500. - 8x RAGL 15 1v1 maps. - 3x other 1v1 maps. - 37x new team game maps. - Fixed undeployable starting location on Basalt Badlands map. - Prevent wormholes being destroyed in certain campaign missions. - Exclude Supply Truck from Oil Refinery price reduction.
- `f55b2348f823788b207d93c88d4e6e7062a446f6` (2024-01-12T08:24:32Z) — Updates. - Added Hypercharge upgrade for Scrin Seeker & Lacerator. - Chem Warrior gains Tiberium Surge ability. - Yuri/Mastermind ability no longer kills slaves. Slaves are killed either manually by deploying them, or when exceeding capacity. - Minor mission 9 fix - prevent MAD Tank deploying when player does a sat hack on it. - Minor mission 15 fix - prevent player's units auto attacking disabled defenses. - Reduce Kirov separation distance to make them less prone to blocking each other from dropping bombs. - Improvements to targeted ability traits. - Battle Drone self-repairs to 50% instead of 100%.

### `Traits/Conditions/GrantConditionOnPrerequisiteCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `ae18b40e3a288c4ee65399b5f9f33e79c1c0719e` (2025-11-02T13:39:02Z) — Fixed Rebel MCV production while moving speed penalty.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `1d8e42c2e1bfd72e169d2f3fb4dd931cdadfc10e` (2022-05-04T00:43:12+01:00) — Fixed version of GrantConditionOnPrerequisiteCA (temporary until PR merged). Reverted SD cost. MCV can now be built without SD if player has no MCV or Construction Yard.

### `Traits/Conditions/GrantDelayedCondition.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `9695a2e51959415721b71b4a8d69a34aab6681ef` (2022-11-05T15:45:29Z) — Fixes/misc. - Fixed Mothership beams (was broken by added turret used for shields). - Increased Mothership main beam damage radius. - Fixed numerous hit shapes and selection decorations. - Ion Conduits now applies to Stormcrawlers. - Made Ion Conduit effect more consistent (each time the 3 clouds spawn, one is active, instead of a random 1/9 chance). Reduced damage to offset. - Increased Atomized debuff damage but reduced duration.
- `a138d418f57d1f6408ff9fa7df2650e2a7b84bf3` (2021-05-16T15:40:55+01:00) — Added a new trait for Scrin Shields so they operate like an independent health pool. Removed some unnecessary "using" directives.
- `cdbe778689a460ebc6be8abc1c8fb51a649c1e4e` (2021-03-24T18:11:02Z) — Various tweaks. - Use SpeedMultiplier for aircraft warping as this doesn't cause helicopters to land (though the issue of it not affecting idling aircraft remains). - Fixed Chrono Prison hitting multiple targets that overlap. - Slight increase to Battle Tank, Heavy Tank and BTR damage vs light armor. - Reduced Desolator direct damage vs heavy armor, added a small amount of splash to main weapon, increased prone movement speed, increased irradiated unit damage and area of effect, increased deployed radiation levels at outer edges slightly. - Reduced Stealth Generator invisibility damage. - Reverted Iron Curtain footprint. - Improvements to GrantDelayedCondition for possible future usage.
- `826c75a87c6a8cd8cd091b90a133f9a82742c57c` (2021-03-14T16:58:46Z) — Make initial capture of an oil derrick give 300 cash. Corrected derrick husk offset.

### `Traits/Conditions/GrantStackingCondition.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `3fe4defb1ca23bd2397cccc22a4b616884f4e8f3` (2024-10-06T13:28:32+01:00) — - Added Malefic allegiance (with Mutilator/Tormentor units and Anathema power). - Reduced delay between Guardian Drone burst shots. - Fixed support powers that spawn actors not spawning directly on top of other actors. - Corrected Bombardier damage. - Reverted Leecher damage buff. - Reduced Greater Coalescence healing of infantry & light armor.

### `Traits/Conditions/GrantThermalCondition.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `6eddd5e7960766dea951673618f5edd275eb8584` (2021-10-29T21:36:02+01:00) — Traits for Orca Afterburner.

### `Traits/Conditions/GrantTimedConditionOnCargoAction.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `adfec16772a69a3bb89f33c085e92daf88e8be01` (2021-12-14T22:07:25Z) — Make Stealth APC uncloak on passenger entering. Reduce Light Tank HP a little (41250 to 39000).
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `8b965617a68b975026e7c3de8a94d5de99552740` (2020-05-05T10:58:39+01:00) — Fix Bugs with 0.62

### `Traits/Conditions/UnloadOnCondition.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `0547d56347bde44330e45fe753f981ef7c31c047` (2024-12-04T12:16:59Z) — - Technology Hack power available to Legion only on radar. - Removed Overload power. - Reduced Mutilator HP from 15k to 13k. Increased cost from 475 to 500 (correction). - Reduced Ravager damage vs buildings. - Fixed Troop Crawler auto unloading when not owned by AI. - Increased Zone Trooper/Raider jump cooldown from 7s to 10s. - Reduced opacity of dog detection circle.
- `58ddacd4804cecd9b15747e1f9ace4eb25b5b06a` (2024-10-09T17:46:58+01:00) — - Added line damage back to Wolverine. Reverted XO damage changes. - Increased Overlord's Wrath damage. - Malefic tooltip/prerequisite corrections. - Reduced Ravager HP from 7k to 6k. Reduced damage & rate of fire slightly. - Watcher defaults to hold fire stance. - Reduced Eviscerator rate of fire and damage. Now affected by Resource Conversion upgrade. - Increased Mutilator HP. - Added small amount of splash to Impaler projectiles. - Stormcrawler clouds form immediately on dealing/taking damage with Ion Conduits upgrade. - Reduced Plasma Cannon damage vs heavy armor. - Increased Rad Trooper damage slightly. Increased HP from 7.5k to 8k. - Increased Desolator splash radius slightly. Increased HP from 17k to 18.5k. - Increased Zone Trooper rate of fire and damage. - Increased Zone Defender rate of fire. - Increased Tesla Trooper HP from 17k to 18k. - Reduced Cyborg HP from 21k to 20k. Increased cost from 250 to 275. - Increased Zone Trooper/Raider jump pack cooldown by 1s. - Reduced Acolyte HP from 10k to 9k. - Reduced Leecher damage vs buildings and light armor. - Added support for random charge times to AttackFrontalCharged.

### `Traits/ConvertsDamageToHealth.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `ea1b851088cb523c23c3f9b7b1f4d1c6b4d0a2a3` (2025-12-07T16:13:06Z) — Clean up trait lookups.
- `3001442006d88fc2d6eb95690d0c2f50298f28e8` (2024-07-18T21:17:22+01:00) — Balancing. - Reduced Orca Bomber HP from 38k to 32k. - Reduced Peacemaker HP from 40k to 36k. - Shadow Operatives throw Shadow Beacons rather than plant them, and have 2 instead of 1. Increased pistol rate of fire slightly. - Chaos cloud duration reduced from 12 seconds to 10 seconds. - Watcher parasite duration increased from 1:00 to 1:30. - Inferno Bomb charge time increased from 6:00 to 6:30. - Burster speed increased from 80 to 92. HP reduced from 7k to 5k. On exploding, will only do 25% damage to other Bursters. - Increased Obliterator rate of fire, reduced damage (overall DPS is increased). Increased turn rate slightly. - Leechers no longer heal via crushing husks. - Reduced Stormrider price from 1750 to 1650. - Increased Mobile EMP turn rate. Reduced shockwave delay from 2s to 1s. - Removed Apocalyptic Eradicator AA rockets. - Increased Nuke Cannon splash radius and damage vs infantry. - Pitbull no longer blinds shielded units. - Reduced Hacker range by 1. - Increased PAC damage. - Increased time before and between Gateway waves by 5s.

### `Traits/DeployOnAttack.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `af6387c37c5650f3a1fbc17daf2bb530e4a59043` (2026-07-19T13:21:49+01:00) — - Fixed Nuke Cannon bug allowing deployment on building bibs. - Allow Floating Disc ability to target buildings under fog.
- `8c373ad239d5440c92832021fbe6850b05293e07` (2024-12-18T15:34:39Z) — - Black Sky Strike fires 4 missiles, down from 6. Reduced base damage to 70k, added TankBuster modifier. - Corrected Black Sky announcement filenames. - Stealth Harvester upgrade moved to radar. Will upgrade existing harvesters. - Increase Mantis speed, reduce HP from 30k to 28k. - Fixed minor issue with Nuke Cannon auto deployment. - Tooltip corrections.
- `8f164718d8464105cfef345358fe80d489d86410` (2024-12-16T13:38:15Z) — Reduced Nuke Cannon cost to 2300. Improved deploy behaviour (will not undeploy when attacked moved with a group, will auto deploy once in range with an attack order).
- `f2e5f1acc53fdea8e50dd49e73e05ae4567a6273` (2024-08-11T23:05:55+01:00) — Shellmap improvements.
- `1238be5d9a307434f4716d5a879a4641848b4a1a` (2024-06-15T17:01:40+01:00) — Nuke Cannon AI deployment. Initial balancing. Yaml fixes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `62c50245a4b04c0fdfe9227c423d1c9c85c1b192` (2021-10-30T18:05:20+01:00) — Auto deploy MEMP on attacking.
- `11540d59960aa40cb45069d255c860866b0c4f19` (2021-09-15T23:33:58+01:00) — Added Hacker (working but not buildable, work in progress). Some minor code fixes. Updated Soviet faction descriptions to include unique Kirov bombs.

### `Traits/DetonateWeaponOnDeploy.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `090f33479b9816b2045d929a5b4d9914ac9ee6e7` (2023-08-05T12:01:44+01:00) — 2307 engine fixes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `9cfce9297022419467fee71976aff77675c072dd` (2022-04-09T13:01:23+01:00) — Fixes for updates.
- `1075fc1a1255b7414032cb62c57b5d90aef68d2b` (2021-06-17T19:01:19+01:00) — Simplified DetonateWeaponOnDeploy. Added charging bars for Mothership weapons.
- `ddede374d19be45470e568875f5fa0d2be7196b7` (2021-06-15T18:18:25+01:00) — Scrin Mothership beam adjustments. Minor fixes.
- `2b42f3d9cba2cfce1ce0fa2c202fd2db637cff2a` (2021-06-14T23:02:14+01:00) — Added Scrin Mothership.

### `Traits/GivesExperienceToMaster.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `48d91f464a0f67a3126bca45351327d592160384` (2026-06-05T16:31:48+01:00) — Attached Mini Drone XP fixes & Kirov tooltip correction.
- `64a7ec1a1dea8c57492e45f55a6a0d983c5bd172` (2026-06-04T15:46:47Z) — - The full XP of any destroyed ARC drones will now be added to a singular reclaimable XP pool. On production of new drones, this XP will be drawn from up to veterancy level 2. - Mini Drones will transfer their XP to the parent unit on attaching. They will then inherit the veterancy level of the parent unit, and any damage dealt will be given to the parent unit. - Suppression Field can be applied as long as one valid unit is visible within the target circle (non-visible units within the circle will then be affected upon activation). - Made Templar laser with Quantum Capacitors more visually distinct. - Red skull icon for Assassins. - Fixed triple SSM with Black Napalm burst count. Adjusted reload to bring DPS into line. - Removed duplicate lasher warhead.
- `51305a6639e4f586b49330866abdb9555e3062f2` (2025-05-13T18:20:07+01:00) — - Allow multiple types of mind control on a single unit. - Yuri/Mastermind/Hacker IFV reworked to allow control which passes to/from the passenger on exit/entry. - Re-remove Jackknife air to ground modifier.
- `ba62f9d0167fb6ac857a48b3129df7a27921e0a7` (2023-12-17T10:17:26Z) — Cruise missile.
- `975a855f527512cea690311244f091ea5cf46970` (2023-09-01T17:28:46+01:00) — Mastermind/Yuri gain XP for each unique unit mind controlled. PAC/Drone Carrier gain XP from fighters dealing damage.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `b4bafff1d819697d2da8d68d363142cbb2361e70` (2023-03-13T21:44:21Z) — Fix dead slave XP crash.
- `2416d8adc4f9974a011c3942d87041dbb195dd9b` (2023-02-12T18:37:39Z) — Chapter 4 missions. Chapters 1-3 clean up.

### `Traits/GuidedMissile.cs`

Vendor content matches approximately `a41ab548db80b6e6f206d3072dbc03ee375ceb18` (2024-05-07T19:37:01+01:00; Patriot Strike.).

- `49e916f2ae0269512abc289e6c09cae124f84cc6` (2024-11-06T11:16:47Z) — - Reduced Patriot missile damage & splash. Reduced distance to avoid slightly. - UI indicators for GDI strategy level and Nod building/harvester kills.
- `77b48a74ac9bb0a076409c31edda02a65522e027` (2024-07-07T20:53:49+01:00) — Remove debugging. Don't apply seek and destroy speed bonus to Aurora's while afterburner enabled.
- `3ebbdbe126ba9ed970061a0c9a999388bb2f20bf` (2024-07-05T19:06:32+01:00) — Balance/fixes: - Replaced XO machinegun with coilgun. Increased range from 5.75 to 7.5. Reduced HP from 32k to 25k. Reduced rate of fire slightly. - The distance at which Patriot missiles will lose tracking now scales with the speed of the target. - Increased volume of beacon sound. - Fixed Patriot Strike crash when target dies at the moment of being targeted. - Fixed PACs/Devastators being destroyed when a slave is freed directly beneath them.

### `Traits/HarvesterBalancer.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `c72dd9565c02b5d75f1101cec9d671f6aa16a802` (2025-06-07T19:22:54+01:00) — Engine update fixes.
- `d8f445aa97bd38b1f168de7cb39e786570200beb` (2025-05-06T08:12:12+01:00) — Scrin allegiance bonuses. - Loyalist: Resources near Colony Platforms regrow faster. - Rebel: Colony Ship can produces structures while moving. - Malefic: Colony Platforms are cloaked.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `d18f803b1e48583378314fc8b21eb3afbd988b34` (2021-02-11T16:27:03Z) — Corrected harvester balancer angles and added a time limit for harvesters produced from factory so they can't gain speed buff for an excessive amount of time prior to reaching resources or returning to refinery.
- `4034aa01386fb3978145e6729f306aaf891b7086` (2021-02-05T01:22:19+10:00) — Fix Bugs, Misc
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `9ec3d3a6350193bfd167882344e7c2623afd5ec9` (2020-12-13T21:05:28+10:00) — Fix Disruptor breaking with Seek & Destroy
- `e17a77923e289d3ff3b364d3b4292f58c2f75dd4` (2020-12-12T12:48:54Z) — Trait to give Harvesters travelling to/from resources from above the refinery a speed boost so income matches harvesters travelling to/from resources below the refinery.

### `Traits/ImmobileWithFacing.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `fd367c06fed72dfe32f89fdb587acb24125c12ad` (2021-07-07T10:07:23+01:00) — Fixed code styling.
- `32d48329428228b02bb93037ecffefb50242db58` (2021-07-06T13:19:21+01:00) — Shadow Team support power.

### `Traits/Infiltration/InfiltrateToAttach.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `3f07398638ae11fdac95a91f2711647dda2d01f3` (2025-10-29T17:53:23Z) — - Mini Drones inherit cloak from parent. - Corrected TD Harvester palette. - Fixed Mini Drone attach sound.
- `1d1f46592ea335f831fd665c10fbabe32659f32a` (2025-06-19T21:12:39+01:00) — Grant 15XP for Spy/Infiltrator infiltrations and for Thief captures.
- `83e46fd8e510f63a9a6b779167caba5062a5d02d` (2024-05-19T14:10:54+01:00) — Reworked Attachable/AttachableTo traits. Allows multiple AttachableTo traits, each for a different type of attachable.
- `d8160dc6364d0848a837d0d6e479850ced562973` (2024-02-03T17:58:52Z) — Overhauled mini drone attachment. Improvements to Upgradeable trait and Upgrade activity.

### `Traits/InstantTransforms.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `3545e78cbac89a596abacdbaf5d07ee40feabc4c` (2021-03-08T02:28:30+10:00) — Add Ion Storm Upgrade

### `Traits/KeepsDistance.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `c86ae8d1367622f7f8a3b3903e3d6c46173b8c50` (2026-05-31T09:16:57+01:00) — - Missile lock on based on burst count for (H)MLRS, AGT, Seeker, Intruder (odd numbered shots will lock on). - Slightly increased projectile speed of Intruder, Seeker, Marauder. - Subs default to return fire instead of hold fire. - Fixed KeepsDistance preventing move orders. - Renamed GuardsSelection to AutoGuard. Shorter radius to check for units to guard that are further away from the target. - Corrected Psychic IFV tooltip.
- `d70424ca1c631f802b337c091379c265b4b8cbde` (2026-05-30T15:40:34+01:00) — GuardsSelection responsiveness improvements.

### `Traits/MadTankCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `d17512aeeda64f8dc06ae3afee84f4d140cbce4d` (2025-10-09T07:01:25Z) — - Mission adjustments. - Simplified MAD Tank code (fixes reload time buffs). - Enmity fix.
- `1541f07d78db777ede815506b1dc1fe645beafd6` (2025-10-05T14:39:21+01:00) — MAD Tank bug fix.
- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `c72dd9565c02b5d75f1101cec9d671f6aa16a802` (2025-06-07T19:22:54+01:00) — Engine update fixes.
- `aa42f86614ae6f85c35a2a2668beda4ca378f409` (2025-05-25T17:21:05+01:00) — - Make Anathema affect MAD tank thump interval. - Improve Mothership crash explosion. - Increase Basilisk range from 5 to 8. - After 4 pulses Desolator eruption radius increases by 1 cell. - Fixed Decoy Projectors crash. - Fixed actor spawning abilities ordering by distance. - Fixed targeted weapon abilities no longer being targetable on ground. - Changed bulk transport loading cursor to yellow to make it easier to distinguish.
- `090f33479b9816b2045d929a5b4d9914ac9ee6e7` (2023-08-05T12:01:44+01:00) — 2307 engine fixes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `8dbdd537eb15a6b269db53aa3d7f344ba891f2ac` (2022-11-15T17:01:54Z) — Chapter II missions.
- `175ab7bf4b1bd828afdd9b2929373da7db62f48e` (2022-05-04T00:51:40+01:00) — Code style fix.
- `eb0761251efc7fafee2d5cf8ca75faca073c95e6` (2022-05-02T11:19:07+01:00) — Balance. - MCV no longer requires SD. Reduced SD cost to 600. - Normalised power consumption (150) and HP (100k) of tech centers and superweapons. - Increase Bombardier projectile speed, splash damage and damage vs infantry/buildings. - Increase Kirov bombs dropped before reloading (from 8 to 10). Increased damage from 12k to 13k. - Reverted Shadow Team cooldown to 4:30. - Moved Blink Packs upgrade to Nerve Center (increased upgrade time to 2:00). - Reduced Mobile Stealth Generator cloak radius by 1. - Reduced Devourer damage vs infantry a little more. - Corrected TOW missile range (didn't take into account S&D bonus). - Hind will now use rockets and gun against vehicles/structures, with damage more evenly spread between both. Lowered rocket reload time. - MAD Tank can be deployed when Iron Curtained. Will do 40% of normal damage while invulnerable.
- `e2f088e350e4e0b987418dcc1b69ebd6c3d799fb` (2022-03-25T13:43:10Z) — Fixes after rebasing.
- `49f96efdc321c4ca787c467506fd89b785b13d40` (2022-03-12T10:23:07Z) — Balancing/misc. - Increase Black Hand speed a little (keeping prone speed roughly the same). - Increase XO HP from 27.5k to 30k. - Frenzy causes affected units to take 10% more damage. - MAD Tank will detonate repeatedly when deployed, taking damage on each detonation. - Hide Comanche from enemies on radar (mostly thematic change). - Conditions cleanup.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `2e9dcc49f28d07e63463ac104a8afad6e92df6b7` (2020-03-16T06:51:43Z) — Fix GrantTimedConditionOnDeploy & EMP
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo
- `6d0ff33bfd1edc9fe5bf3c43f319f8128e3612ee` (2019-12-14T19:14:58Z) — 0.60.1

### `Traits/MassEntersCargo.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `71ca473402f729a81bf2773f44d84a971a03c4b0` (2026-05-30T12:28:23+01:00) — Improved responsiveness of mass transport loading.
- `cdc66e8722aa6b9536d9888322ed638d44f388bd` (2025-03-15T16:17:04Z) — Voice line for mass cargo loading.
- `844302d1b0882922b573a4a26f28a6868386cfaa` (2025-03-15T11:06:38Z) — Fix mass load/attach desync.
- `4c2090b8927789083cc7aa94cf4cc9ca99856b5c` (2025-03-15T10:24:00Z) — Mass Mini Drone attachment.
- `46fd04052082ccc56a3505eed790886344446da0` (2025-03-08T13:21:03Z) — Mass transport loading.

### `Traits/MindControllable.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `56c47711351328a83b2982cd3ae2af0f9d118c57` (2026-05-10T16:30:22+01:00) — Mind controlled MGG original owner defeated crash workaround fix.
- `c7882b36f9bc3f40ffc9d6c0b696eb5c96d15297` (2025-12-27T10:12:35Z) — Mind control trait improvements.
- `9701d121cb0731bb63c2b88207e522e303d3820f` (2025-12-27T10:12:35Z) — Mind control trait improvements.
- `ea1b851088cb523c23c3f9b7b1f4d1c6b4d0a2a3` (2025-12-07T16:13:06Z) — Clean up trait lookups.
- `9d611b686bde86c0dbb01aa03924fd7d6716fcf9` (2025-06-26T13:04:59+01:00) — Scale point defense laser in the same way as point defense shield.
- `236e4e0ffaae496b2b9c99d49a429c5b5d5ed601` (2025-05-15T17:35:19+01:00) — - Reduced speed of Tiger Guard IFV. - Fixed Hacker IFV permanently controlling targets. - Tooltip tweaks. - Removed debugging.
- `51305a6639e4f586b49330866abdb9555e3062f2` (2025-05-13T18:20:07+01:00) — - Allow multiple types of mind control on a single unit. - Yuri/Mastermind/Hacker IFV reworked to allow control which passes to/from the passenger on exit/entry. - Re-remove Jackknife air to ground modifier.
- `28747cc61f710e11dfa2112aff25483980b97f22` (2024-11-03T23:10:04Z) — - Implement stolen tech acquisition for Hackers/Assassins. - Hypercharge reduces DPS after wearing off instead of disabling weapons.
- `47c30b106559bd1b1f4821c054011fcffa3cf33e` (2024-11-03T09:52:44Z) — Nod branch groundwork.
- `08024f6b1f5c50de64e6272c714b081c738f6ad4` (2024-03-13T20:44:35Z) — Updates. - Loaded transports no longer immune to mind control. Loaded transports and harvesters take 4 seconds to mind control (Commando type passengers provide immunity). - Reduced Microwave Tank splash damage (removed vs infantry). Reduced speed. - Add minimum distance to airstrike powers to prevent instant damage near map edge. - Reduce cost of Prism Cannon upgrade to 750. - Adjusted Hospital locations on Lost in Space map. - Make dogs immune to mind control. - Limit Very Hard & Brutal AI to 4 V3s/Tomahawks. - Updated MindControllable trait to allow cargo to be ejected. - Use SD resupplying condition for unit sell. - Yaml fixes.
- `02bd389513ca42644765c933fb809bb6d6036e0f` (2024-03-10T22:38:15Z) — Updates. - Microwave Tank kills crews of vehicles below 75% HP (calculated after the damage from the MW zap itself). - Allow for cargo killing via mind control (not used currently). - Sniper pip color to green. - Subterranean Strike tooltip clarification. - X-O tooltip fix.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `7ac90648a03ba62b43c168239e29c3595af51584` (2021-11-22T10:05:32Z) — Fix hacked icon not being removed when an Engineer recaptures a hacked building.
- `729a3fb1937cb1078b651e7c3b9a2e6aa1612898` (2021-11-02T18:42:57+10:00) — Add MiniDrone Voice
- `5e7bd2dff1f868fc969320cd3d16c8d90862033c` (2021-10-31T23:21:24Z) — Fix mind control crash. Added USA airdropped units to faction tooltip & mention X-O has to be researched. corrected a typo.
- `d891bc3eb7cb6f2e6926f98c4063f3e8312dc33f` (2021-09-27T01:47:12+10:00) — Fix Formatting
- `828c964d0bccb067890d417b9486e913e743c072` (2021-09-26T13:15:17+01:00) — Prevent hack being instantly revoked (only seemed to affect actors created after the map loads). Removed "Select Target" voice on triggering Hacker Cell.
- `7ffd6726d4c2f2f78c80d427503274101521823a` (2021-09-25T23:03:23+01:00) — Hacker changes. - Spawn at base (renamed Hacker Cell). - Increase movement speed to 56. - Hack takes 4 seconds to wear off if Hacker dies. "Restoring" icon shown if this occurs. - Hacking power plants causes damage over time, "Overloading" icon shown. - Drone units are hackable. - Updated sounds.
- `488001a13887a50c6169917814092391489d56d0` (2021-09-24T16:33:58+01:00) — Misc tweaks/fixes. - Allow selling buildings with TNT attached. - Increased hospital/Medic IFV healing. - Give Medic IFV the Medic's heal weapon in addition to area passive healing. - Updated MindController/MindControllable traits to allow for a delay for effects to wear off and a sound on starting mind control process. - Corrected healing pip offset. - Fixed Venom and superweapons not damaging JumpJet troopers. - Fixed Rocket Solider weapon offsets (had issues when prone). - Fixed errors.

### `Traits/MindControllableProgressBar.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `d1fa7b5d472f33cf78974e0661ad2ae2c3729226` (2024-03-13T08:03:08Z) — Updates. - Updated MindController trait to allow TicksToControl to vary based on target type. - Reduced time taken for Hacker to hack drones. - Powered down defenses have reduced vision.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `11540d59960aa40cb45069d255c860866b0c4f19` (2021-09-15T23:33:58+01:00) — Added Hacker (working but not buildable, work in progress). Some minor code fixes. Updated Soviet faction descriptions to include unique Kirov bombs.

### `Traits/MindController.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `c7882b36f9bc3f40ffc9d6c0b696eb5c96d15297` (2025-12-27T10:12:35Z) — Mind control trait improvements.
- `9701d121cb0731bb63c2b88207e522e303d3820f` (2025-12-27T10:12:35Z) — Mind control trait improvements.
- `ea1b851088cb523c23c3f9b7b1f4d1c6b4d0a2a3` (2025-12-07T16:13:06Z) — Clean up trait lookups.
- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `cea756c8449898fb1574c7857b87f6b1ebdb7255` (2025-05-19T08:08:29+01:00) — - Fixed crash when manually releasing mind controlled slaves. - Added target painter ability to Pitbull. - Added minimum range to Aurora so it will circle back instead of missing. - Increased Killzone duration from 16s to 30s. - FlashTarget warhead. - WithFlashEffect trait. - Tooltip tweaks.
- `236e4e0ffaae496b2b9c99d49a429c5b5d5ed601` (2025-05-15T17:35:19+01:00) — - Reduced speed of Tiger Guard IFV. - Fixed Hacker IFV permanently controlling targets. - Tooltip tweaks. - Removed debugging.
- `51305a6639e4f586b49330866abdb9555e3062f2` (2025-05-13T18:20:07+01:00) — - Allow multiple types of mind control on a single unit. - Yuri/Mastermind/Hacker IFV reworked to allow control which passes to/from the passenger on exit/entry. - Re-remove Jackknife air to ground modifier.
- `b55ac4fc4e7142e1b60a5cf22c3b7d81b7be15d6` (2025-05-12T21:20:29+01:00) — - Hoplite, Tiger Guard, Eviscerator, Impaler, Stalker, Zone Trooper/Raider/Defender, Commissar, Shadow & Disintegrator IFV turrets. - Jackknife has TankBuster modifier & deals increased damage vs defenses. - Corrected Industrial Plant prerequisites. - Some code cleanup.
- `d8f445aa97bd38b1f168de7cb39e786570200beb` (2025-05-06T08:12:12+01:00) — Scrin allegiance bonuses. - Loyalist: Resources near Colony Platforms regrow faster. - Rebel: Colony Ship can produces structures while moving. - Malefic: Colony Platforms are cloaked.
- `28747cc61f710e11dfa2112aff25483980b97f22` (2024-11-03T23:10:04Z) — - Implement stolen tech acquisition for Hackers/Assassins. - Hypercharge reduces DPS after wearing off instead of disabling weapons.
- `47c30b106559bd1b1f4821c054011fcffa3cf33e` (2024-11-03T09:52:44Z) — Nod branch groundwork.
- `3d278d9f9e5eaa66ac2fbed0190f7030ca3ad90b` (2024-08-22T22:58:47+01:00) — Misc fixes/tweaks. - Disable GPS for AI in campaign. - Allow Guardian Drones and Mini Drones to be built in mission 23. - Fix queued hacking orders resetting the current hack. - Prevent Advanced Comms Center being built in mission 7. - Remove non-elite regen from Boris in mission 12. - Fix Nod Banshee/Harvester/MCV husk colour in campaign. - Prevent blocked Temple Prime exit from infinitely accumulating money. - Add short delay on deploying before Nuke Cannon fires to allow pre-targeting.
- `4d2947d9760b54a2a228a903cb98b7d85c810cd1` (2024-04-13T09:20:04+01:00) — Fix Hackers not undeploying if target dies or changes owner while hacking.
- `07d3bd224defb9c936c18834b35861799a434f8c` (2024-03-16T16:02:46Z) — Updated cursor for Mastermind building capture (enter cursor suggests Mastermind is consumed on capture).
- `16be4f6dbd0b4a784db4c1e889ce7338326919df` (2024-03-16T09:59:46Z) — Block loading into mind controlled transports. Show blocked cursor for enter/unload.
- `d1fa7b5d472f33cf78974e0661ad2ae2c3729226` (2024-03-13T08:03:08Z) — Updates. - Updated MindController trait to allow TicksToControl to vary based on target type. - Reduced time taken for Hacker to hack drones. - Powered down defenses have reduced vision.
- `9d07d181be591dacaf8c29b6885244d78d3e2ec7` (2024-03-10T19:58:10Z) — Updates. - Mind controllers detonate a specific weapon to kill slaves on release or controlling above capacity. - Static AA defenses no longer auto targeted in defensive stance. - Remove infantry prioritisation from JumpJet. - Yaml fixes for commando regen.
- `f55b2348f823788b207d93c88d4e6e7062a446f6` (2024-01-12T08:24:32Z) — Updates. - Added Hypercharge upgrade for Scrin Seeker & Lacerator. - Chem Warrior gains Tiberium Surge ability. - Yuri/Mastermind ability no longer kills slaves. Slaves are killed either manually by deploying them, or when exceeding capacity. - Minor mission 9 fix - prevent MAD Tank deploying when player does a sat hack on it. - Minor mission 15 fix - prevent player's units auto attacking disabled defenses. - Reduce Kirov separation distance to make them less prone to blocking each other from dropping bombs. - Improvements to targeted ability traits. - Battle Drone self-repairs to 50% instead of 100%.
- `975a855f527512cea690311244f091ea5cf46970` (2023-09-01T17:28:46+01:00) — Mastermind/Yuri gain XP for each unique unit mind controlled. PAC/Drone Carrier gain XP from fighters dealing damage.
- `090f33479b9816b2045d929a5b4d9914ac9ee6e7` (2023-08-05T12:01:44+01:00) — 2307 engine fixes.

### `Traits/MindControllerCapacityModifier.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `51305a6639e4f586b49330866abdb9555e3062f2` (2025-05-13T18:20:07+01:00) — - Allow multiple types of mind control on a single unit. - Yuri/Mastermind/Hacker IFV reworked to allow control which passes to/from the passenger on exit/entry. - Re-remove Jackknife air to ground modifier.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `2416d8adc4f9974a011c3942d87041dbb195dd9b` (2023-02-12T18:37:39Z) — Chapter 4 missions. Chapters 1-3 clean up.

### `Traits/Mirage.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `090f33479b9816b2045d929a5b4d9914ac9ee6e7` (2023-08-05T12:01:44+01:00) — 2307 engine fixes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `969d92290ae7ff8854c5ee38842ad19fecbdfe1f` (2022-01-01T00:12:39+10:00) — Happy lint
- `a1c12eca33b1402c79bf0d77f09127c4e780f9a9` (2021-12-31T13:32:14Z) — Fix Mirage Tank tooltip not showing owner.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `131a019eda3d97ed620e1db8d7eb35b3fce3d20b` (2020-05-01T08:30:11+01:00) — Add Mirage Disguise Logic

### `Traits/MissileBase.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `bbfbeb8c1aea5f8a7324e385803986e62f122b7e` (2024-05-27T09:26:25+01:00) — Allow missile strike power to use ballistic/cruise missiles. Prevent gateway being spawned on top of actors.
- `869fed49d61031c501fc8744c7bbe11c0f4e9369` (2024-05-08T18:04:43+01:00) — Allow missiles to have vision. Increase Atomizer projectile speed.
- `ba62f9d0167fb6ac857a48b3129df7a27921e0a7` (2023-12-17T10:17:26Z) — Cruise missile.
- `090f33479b9816b2045d929a5b4d9914ac9ee6e7` (2023-08-05T12:01:44+01:00) — 2307 engine fixes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `8b24281ae9582d580e52cad942c8ba4c9d233679` (2022-02-02T00:21:05Z) — Removed VisualMove from BallisticMissile.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `a512e365b2f4f17feb030f7697a8cdc80aca8710` (2021-01-05T00:13:45+10:00) — Fix Crashes
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo
- `6d0ff33bfd1edc9fe5bf3c43f319f8128e3612ee` (2019-12-14T19:14:58Z) — 0.60.1

### `Traits/MissileSpawnerMaster.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `54d51d0bc37a262c157803638da6d22bcb743c84` (2024-01-07T12:05:48Z) — Missile fix.
- `ba62f9d0167fb6ac857a48b3129df7a27921e0a7` (2023-12-17T10:17:26Z) — Cruise missile.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `a512e365b2f4f17feb030f7697a8cdc80aca8710` (2021-01-05T00:13:45+10:00) — Fix Crashes
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo
- `6d0ff33bfd1edc9fe5bf3c43f319f8128e3612ee` (2019-12-14T19:14:58Z) — 0.60.1

### `Traits/Modifiers/WithPalettedOverlay.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `65e2a2fb56c2a7f5a71bf2b4d420b73f9e24c3ef` (2025-12-27T10:12:40Z) — Encyclopedia effects fix.
- `20ccc922e88f2f811c09b99e61c7c5ecbd0127ce` (2025-12-27T10:12:40Z) — Encyclopedia effects fix.
- `21c6ed216b673f95f54b22851f7ac045bb007a85` (2025-12-02T08:17:24Z) — Encyclopedia updates.
- `164b07c96e53f72bb3dfa223f919d1077ee7a026` (2025-11-14T12:40:24Z) — - Voidspike ambient sound now audible through fog. Added sound effect when created. Reduced initial timer from 2 minutes to 30 seconds. Visual effect applied to resource spawners no longer visible through fog. - Reduced Chem Mortar damage vs cyborgs. All mortars now affected by flak vest mitigation. - Adjusted Crossrip/Schism ending phase scaling.
- `70e2c56ff1d332e41b75f4f05501298ffb7cba9b` (2023-12-29T09:42:51Z) — Buggy decoy upgrade.

### `Traits/Multipliers/LayeredDamageMultiplier.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `3f9daada297e4a6532d75a368a4fb01e1eb974de` (2022-06-03T10:51:21+01:00) — Fix code style errors.
- `092aa06dc5dee16aa3da0af57a9f49d723a0612a` (2022-05-29T11:40:14+01:00) — Flak Armor and Hardened Carapace upgrades. Provide 40% damage reduction against explosives. Cyborg Armor also provides 10% damage reduction against explosives.

### `Traits/Multipliers/TimedDamageMultiplier.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `9d611b686bde86c0dbb01aa03924fd7d6716fcf9` (2025-06-26T13:04:59+01:00) — Scale point defense laser in the same way as point defense shield.

### `Traits/PaletteEffects/CloakPaletteEffectCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `79d6ffa754e72f8419a64d5a8f55d47f60160756` (2023-05-21T15:23:15+01:00) — Updated cloak effect. Moved/renamed some palette related classes.
- `17cb9eb11022e798a2693054236a3c830f32861f` (2023-05-20T15:56:16+01:00) — Replace FlickeringPaletteEffect with PulsingPaletteEffect. Fixed version of CloakPaletteEffect.

### `Traits/PaletteEffects/PulsingPaletteEffect.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `ff2339acd15eada566cf857942d001435dc4b33f` (2026-01-17T10:30:05Z) — Fix encyclopedia preview positioning for different camera settings.

### `Traits/Palettes/OverlayPlayerColorPalette.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `1598a9cfb1034483521c0c2f31ef134658820811` (2026-01-19T07:40:17Z) — Lock player colors in co-op missions.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `79d6ffa754e72f8419a64d5a8f55d47f60160756` (2023-05-21T15:23:15+01:00) — Updated cloak effect. Moved/renamed some palette related classes.
- `9276ed8f20b8e119c3ed3b1bd045105a9f6fa98a` (2022-10-11T22:44:58+01:00) — Mission 5 - Machinations. Yaml fixes. Show mod specific authors file in the in-game credits panel.
- `1be3409112013a61069f9fa747a739fcdbed7723` (2022-09-22T21:43:49+01:00) — Campaign AI overhaul and mission improvements.
- `af7e185929f12a50c80a9e4ea0a2d531c2d50b1d` (2022-06-26T16:59:14+01:00) — Use OverlayPlayerColourPalette and OverlayColourPickerPalette for the time being to maintain colour accuracy/vibrancy. Improved variety of preset colours.
- `b5605e349bd5445e307e8c243c42f2914d50e596` (2022-02-20T14:20:49+10:00) — Restore PlayerColor
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo
- `6d0ff33bfd1edc9fe5bf3c43f319f8128e3612ee` (2019-12-14T19:14:58Z) — 0.60.1

### `Traits/PeriodicProducerCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `053891d201921a06b98120470005f8269198f77a` (2025-10-14T08:03:19+01:00) — - Fixed Dissection bombing runs continuing after secondary objective completed. - Oil Derrick just gives $125 per 15s with no bonus. - Reverted Venom random shot delay as it prevented returning to base when ammo depleted. - Added 5 second delay before initial Medic/Mechanic produced from Hospital/Machine Shop. - Speculative fix for failed Chronoshifting of enemy units.
- `f614cf5ad9c729024667a6611aa98c3e413ab367` (2024-01-30T19:25:16Z) — Updates. - Decoy Projectors creates 2 decoy Flame Tanks (or Heavy Flame Tanks) instead of a Buggy. - Added Peacemaker to AI. - Increased Engineer mine detection range. - Advanced Optics available on radar. Increased vision extension by 1. Increased price from 750 to 1000. - Made Commissar range indicator more visible. Increased range to 6c0. - Fixed Cyberdog not showing in MQ. Reduced delay between attacks. - Updated IFV mortar turret sprite. - Reduced Flame Tank splash damage.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `2cf3bb50ad5f0b7f9a18b7380ef5ff03ee5b0d13` (2021-12-21T11:36:19Z) — Hospital produces Medic/Rejuvenator every two minutes instead of allowing them to be built normally.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `29fcbf43aed5998edf9693aca7ab1f86f10be967` (2021-01-28T23:01:00+10:00) — WIP3

### `Traits/Player/CapturedFactionsManager.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `e540fbf64f247d75e980fc46a37638747a862fc1` (2025-07-11T07:17:02Z) — - Reworked CountManager and related traits. - Removed unused/redundant traits. - Yaml fixes.

### `Traits/Player/GrantConditionOnPrerequisiteManagerCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `e540fbf64f247d75e980fc46a37638747a862fc1` (2025-07-11T07:17:02Z) — - Reworked CountManager and related traits. - Removed unused/redundant traits. - Yaml fixes.
- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `1d8e42c2e1bfd72e169d2f3fb4dd931cdadfc10e` (2022-05-04T00:43:12+01:00) — Fixed version of GrantConditionOnPrerequisiteCA (temporary until PR merged). Reverted SD cost. MCV can now be built without SD if player has no MCV or Construction Yard.

### `Traits/Player/LobbyPrerequisiteDropdown.cs`

Vendor content matches approximately `c72dd9565c02b5d75f1101cec9d671f6aa16a802` (2025-06-07T19:22:54+01:00; Engine update fixes.).

- `e540fbf64f247d75e980fc46a37638747a862fc1` (2025-07-11T07:17:02Z) — - Reworked CountManager and related traits. - Removed unused/redundant traits. - Yaml fixes.

### `Traits/Player/ProvidesPrerequisiteValidatedFaction.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `50b01f307763b268cb24f8636664014a737c9b77` (2025-11-24T16:48:07Z) — - Increased Raider Buggy range by 1. - Speculative fix for Deliverance mission. - Removed debugging. - Fixed Artillery/Spectre not being slowed by crushing fences.
- `59408ff8c98f630471676e85dba804daae2a744d` (2025-11-23T14:07:20Z) — Send Cash power for team games and co-op (replaces Supply Truck).
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `49e99c0b78579799801c9aade998885fbb3d33cc` (2022-09-23T17:30:58+01:00) — Added some missing faction validation. Added captured faction manager so faction is always validated against ones the player has actually captured.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `6f8d9dc1d9965078de284d6cc08288bc275377f5` (2020-12-06T00:57:36+10:00) — Clear Errors
- `ccbc53430d59a270a96f4e665750bcdfe9c5659c` (2020-12-05T11:51:27Z) — Added traits to ensure production structures have valid factions. Removed unused prerequisites. Made radar structures equivalent for unit prerequisite purposes.
- `0fecfde59f51ba6a2eafad960bbacad4a64744a2` (2020-06-02T14:20:12+01:00) — Bug Fixes
- `a0568ea32942e3984511264cf775d0b13afc26fa` (2020-05-25T15:44:57+01:00) — Fix Broken MLRS 227mm
- `1e5d78a86c72a2a71c58143c2f843feb1e1b8428` (2020-05-23T19:06:52+01:00) — Pause timer instead of resetting it when trait is disabled by conditions.
- `a70a4b16c5defccfa0f4c160a0eac2b30d2a1b47` (2020-05-22T21:57:02+01:00) — Changed the default colour of the delayed prerequisite charging bar to grey.
- `09abeb2f196c0550404ac25b550c5da60f80331e` (2020-05-21T17:55:35+01:00) — Added ProvidesDelayedPrerequisite trait.

### `Traits/PopControlled.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `3a57a3aa1de8161e55d15575a116eb520ddce482` (2025-05-21T17:36:05+01:00) — - Increased Killzone duration from 30s to 1 min. Reduced cooldown from 4 min to 3 min. - Improved PopControlled trait so it can deal with actors created in the same tick. - Improved SpawnActorWarhead so it doesn't create then dispose an actor if it's not positionable.

### `Traits/PortableChronoCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `7bb28bc17b4062d0b6d74ca86cd3481a843c0643` (2025-01-20T07:55:26Z) — Fixed queued Chrono Tank telports incorrectly calculating the pre-charge time.
- `85f81032bef93d1fd026e20d298c26c10308f38f` (2024-12-17T12:31:00Z) — - Increased Grand Cannon damage vs heavy armor. Increased range by from 9 to 10. First shot is accurate. - Replaced Patriot Strike with Black Sky Strike. Hits up to 6 ground targets, prioritizing the most valuable. - Reduced Troop Crawler cost from 1600 to 1500. - Hoplite range reduced by 1. Added empowered shots which blind enemies (9s cooldown). - Increased Black Eagle splash damage. - Avatar shadow. - Stealth Harvester research icon. - Fix Teleport/Leap abilities being permanently disabled if unit is warped while recharging. - Fix Chrono Tank moving to destination if long distance teleport is temporarily interrupted by being warped.
- `10108c11aa700d3a4abc0a99eb791a04f948ed05` (2024-11-18T22:27:22Z) — - Allow Chrono Tank to teleport 48 cells, but longer distances require scaling charge up time. Increased cost to 1500. - Cryostorm has EVA warning and takes 5 seconds to appear. - Removed X external link from menu screen. - Hornet/Invader tooltip clarification. - Mission 22 difficulty tweaks.
- `f55b2348f823788b207d93c88d4e6e7062a446f6` (2024-01-12T08:24:32Z) — Updates. - Added Hypercharge upgrade for Scrin Seeker & Lacerator. - Chem Warrior gains Tiberium Surge ability. - Yuri/Mastermind ability no longer kills slaves. Slaves are killed either manually by deploying them, or when exceeding capacity. - Minor mission 9 fix - prevent MAD Tank deploying when player does a sat hack on it. - Minor mission 15 fix - prevent player's units auto attacking disabled defenses. - Reduce Kirov separation distance to make them less prone to blocking each other from dropping bombs. - Improvements to targeted ability traits. - Battle Drone self-repairs to 50% instead of 100%.
- `c3aca173ab31e4771f6d13671a864e2187cf03fa` (2023-12-25T11:53:28Z) — Smart cast targeted abilities by default with ctrl forcing all selected units to fire the ability.
- `d5807171441099eaac02314571ae099e85c28f70` (2023-08-13T21:46:53+01:00) — Balance/misc: - Increased Hum-Vee/Ranger/Buggy/BTR/Gun Walker/Guardian Drone/Mini Drone/APC/Raider APC damage vs light armor. - Increased Gun Walker HP from 30k to 33k. - Shard Walker no longer has heavy armor. HP increased to 40k. Reverted nerf vs light armor. - Increased Seeker HP from 22k to 23k. - Increased Lacerator vision by 1. - Increased Leecher HP from 28k to 30k. Increased damage vs light armor. - Increased Leecher orb HP from 30k to 35k. - Chrono Tank can now attack aircraft (relatively low damage). Added a 3 second cooldown between jumps with Temporal Flux. Can no longer crush infantry instantly by teleporting onto them. - Reduced Tripod & Reaper Tripod range very slightly. Reduced damage vs buildings and infantry. - Increased Disruptor damage vs buildings and light armor slightly. - Increased Sukhoi splash damage and missile speed slightly. - Mission 1 & 2 normal/easy difficulty tweaks.
- `a0c32612c76d44108819e0b8ad5b0d3cd34f75c2` (2023-07-07T07:01:29Z) — Fixed crash when Chrono Tank dies while giving the order to chronoshift. Minor Enlightened/Intruder damage nerfs. Minor Apoc range buff.
- `59526030e68facbe04ca70b8243a58105a8cb6e9` (2023-07-02T11:37:24+01:00) — TFCA improvements.
- `baca1fc0dbd60fb2abd5597f476eadff4111e777` (2023-06-04T20:23:41+01:00) — Added targeted weapon ability functionality. - Enlightened can target EMP ability. Reduced speed, damage, EMP duration and EMP area of effect. - Updated teleporting units so deploy command can be used on a group. - Code formatting fixes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `307a50b81e88aaeb38ca02354f4c119cc35221f1` (2023-03-26T10:26:18+01:00) — Temporal Flux allows Chrono Tank to teleport twice before recharging. Reduced Chrono Tank damage vs infantry and speed.
- `15aa57e6bc4e76dfafdfdd78c3daf77e2998bdea` (2022-06-15T22:28:57+01:00) — Fixes after merge.
- `a7d5debd6022537e7dfe4b67f7d343e3464daa7a` (2022-06-12T09:50:05+01:00) — Balance/misc: - Increase vision of Warthog and Stormrider by 1 to match other T2 planes. - Corrected Hardened Carapace cost to match Flak Armor. - Reduced Feeder Mutation cooldown from 4:30 to 4:00. - Temporal Flux upgrade also increases Chrono Tank teleport range and reduces its cooldown.
- `11637502c3344da1167b94434a5727d4537aad7a` (2022-04-21T12:14:10+01:00) — Fixes for updates.
- `9cfce9297022419467fee71976aff77675c072dd` (2022-04-09T13:01:23+01:00) — Fixes for updates.
- `b2286da8eabf18577b63bd049875d8fdd8cc153c` (2022-02-02T13:01:13Z) — Additional changes to bring customised traits in line with their base versions as far as possible. Added descriptions to these classes to explain the differences with base versions.
- `eed1e75fa0d574d8532d6a326cafcdfff8597ac7` (2022-01-31T22:55:56Z) — TurretedFloating fix. EMP missile fix. Minor adjustments to match engine classes. Removed ContrailCA, RevealsMapCA and RepairableNearCA as the engine versions seem to do everything we need now.
- `f682081761351b38db40be96569bc76f199a642e` (2021-07-31T14:04:15+01:00) — Hide Chrono Prison charge bar prior to Temporal Flux upgrade. Increase Hind/Apache price to 1400.
- `949e78b505e8a986ab0a3ae9169d06c8e18d8b1c` (2021-07-31T18:56:47+10:00) — Add Temporal Flux Upgrade for Chrono Prison

### `Traits/ProductionAirdropCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `bef2a576a460475375d9f663d19da9725891ea08` (2026-07-04T18:37:48+01:00) — - ProductionAirdropCA refactor. - Reaper snare fixes.
- `28861bb689bb64d2e888a213e11209bff0502ce6` (2025-12-19T14:41:40Z) — Co-op improvements.
- `3248b6e0591704103833d3103e9d7c99a681abd6` (2025-12-19T14:41:40Z) — Co-op improvements.
- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `b2286da8eabf18577b63bd049875d8fdd8cc153c` (2022-02-02T13:01:13Z) — Additional changes to bring customised traits in line with their base versions as far as possible. Added descriptions to these classes to explain the differences with base versions.
- `fe9acc0e0e3f6c1d17ea8ca44f7226e34b086f33` (2021-07-31T18:25:40+01:00) — Reworked airdrop production so that arrival delay is consistent across spawn points and map sizes, and so the plane comes from the map edge nearest to the airstrip rather than the edge nearest the player spawn point. First Airstrip costs 1800 so the delay isn't purely a disadvantage (earlier subsequent building, a little extra cash when you get a combat unit first).
- `be634b115c5367d76ed4e2c44cf90a3f6dbf94c5` (2021-02-08T01:22:30+10:00) — Fix Misc
- `54d6f045a6e8d637ef5bed18b6c889dbffd3e0c2` (2021-02-04T20:29:58+10:00) — Remove Errors
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `b2e2ae7b4926784fbf911aeb4e8f83a7a2494483` (2020-05-07T15:48:02+01:00) — Change ProductionAirdrop to closest Map edge

### `Traits/ProductionQueueFromSelectionCA.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `87e811d72352016e03c79f446c8a0dbf007bbdbf` (2025-12-12T07:40:19Z) — - More generic trait for conditions based on lobby options. - Queue selection from selecting allied production structures in co-op. - Mission prerequisite cleanup. - Campaign GPS timer correction (w/ no fog). - Increase Seeker speed from 113 to 126.
- `2f5458051fbf9a1afea9c165f4882f43b65297e9` (2025-10-18T13:32:08+01:00) — - Rebel Gateway can be linked to any number of production structures. Can now be linked either from the source or the gateway. Increased cooldown from 3:00 to 4:00. - Scrin basic infantry can benefit from Commissar buff (Warrior, Disintegrator, Assimilator, Rejuvenator, Artificer).
- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `50e719170d798e30488ff82ecce523af00a2daa5` (2025-05-04T20:57:16+01:00) — - Renamed Dragonguard to Tiger Guard. - Fixed Gateway crash when no production structures exist. - Replaced Defense -10% power consumption bonus with +15% power generation. - Corrected build radius increase bonus to be on Economy policy.
- `1277b816fc4fc6fc6fe995eb1c7971de581dca86` (2025-05-03T12:33:52+01:00) — - Make EMP Missile force shieldable. - Selecting Cloning Vat will select the queue of the linked production structure. - Gateway tooltip & reduced cooldown.

### `Traits/ReflectsDamage.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `481ff0a548ecb4ea5685bb5075c3b757565f6ca2` (2025-10-28T08:11:58Z) — - Flak Vest upgrade partially mitigates damage from Disruptor. - Voidspike reflected damage reduced by any damage reduction applied to the attacker. - Fix Nod Covenant tooltip going above level 3. - Increased initial charge time for Assassin Squad, Hacker Cell and Confessor Cabal from 1:00 to 2:30.
- `895e8ff555bd6e9363749da52776785ca01a15e3` (2025-05-28T17:37:59+01:00) — - Fixed Jackknife losing building target in fog when it comes into vision. - Increased Jackknife damage vs defenses. - Reduced Tormentor damage. Increased turn rate from 28 to 32. - Voidspike reflects 50% damage. - MAD Tank can't be mind controlled or driver killed after deploying. - Simplified driver kill yaml (use DriverKill immune instead of removing all the traits). - Increased AGT base damage. Reduced rate of fire. Increased projectile speed. - Increased Prism Tower damage vs heavy/light armor.

### `Traits/ReloadAmmoPoolCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `6ea045b2101d02e304e4514ad8fac2d490484215` (2025-12-17T16:44:15Z) — Reload bar for Nuke Cannon.
- `ce2648fd506dd0bfc3d86a22da451158b94cfa84` (2025-05-24T08:39:50+01:00) — ReloadAmmoPoolCA refactoring.
- `39136da9b5b959d2dadcaa181b4fa26a2752ded1` (2025-05-24T07:55:42+01:00) — - Obliterator charge drains gradually instead of immediately if targeting is interrupted. Added minimum range to prevent direction bug. - EMP Grenadiers don't get range bonus from Heroes of the Union. - Fixed Voidspike visual glitch if hit by weapons which flash the target. - Added Health to Mind Spark so its death animation plays.
- `70e2c56ff1d332e41b75f4f05501298ffb7cba9b` (2023-12-29T09:42:51Z) — Buggy decoy upgrade.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `307a50b81e88aaeb38ca02354f4c119cc35221f1` (2023-03-26T10:26:18+01:00) — Temporal Flux allows Chrono Tank to teleport twice before recharging. Reduced Chrono Tank damage vs infantry and speed.
- `33cb084797a6e878a3c80090995d89c2638e7e2a` (2022-05-15T21:19:53+01:00) — Allow GDI to apply Railgun Titan, Ion Mammoth, Hover Mammoth and Mammoth Drone upgrades to existing units via Repair Facility. Corrected Mini Drone weapons.
- `b2286da8eabf18577b63bd049875d8fdd8cc153c` (2022-02-02T13:01:13Z) — Additional changes to bring customised traits in line with their base versions as far as possible. Added descriptions to these classes to explain the differences with base versions.
- `2b42f3d9cba2cfce1ce0fa2c202fd2db637cff2a` (2021-06-14T23:02:14+01:00) — Added Scrin Mothership.
- `f70188931b21c947aecd5f88222e0518f6a6c734` (2021-04-18T22:38:14+01:00) — Tib Conversion upgrade for Scrin Devourer and Ruiner. Reaper Tripod altered to use the same mechanic.
- `866f3d9cea2cd775f8840e99aeda881e00ef080e` (2021-03-06T22:57:28Z) — Fixed bug with ReloadAmmoPoolCA where delay before beginning reload after firing wouldn't take effect if ammo was at zero. Reworked Stormrider so it doesn't have an awkward gap, and instead has greatly reduced damage with zero ammo until it recharges. Reduced Venom range. Reduced PAC damage vs infantry slightly.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `19d1962ccab1afa1216a7ea8170a4711f1b5ff7a` (2020-04-29T17:11:21+01:00) — Remove whitespace
- `a15f8dc91f0072fc184bb4dbe297e7c03592116c` (2020-04-24T21:14:05+01:00) — Kirov has increased HP but takes more damage when bombing. Can drop 8 bombs before a long reload.

### `Traits/Render/LeavesTrailsCA.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `77e417706372379d81e1c7015b410b2ecfa25139` (2024-02-09T18:57:22Z) — Updates. - Increased Juggernaut cost from $1500 to $2000. Increased range, HP and damage. - Reduced PAC cost from $3000 to $2800. - Reduced damage radius from shot down missiles a little more. - Limited AI V3/TH at Hard difficulty and below. - Fixed rare crashing bug caused by missiles effectively diving underground.

### `Traits/Render/RenderShroudCircleCA.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `51c1c2f633ee8b8d4255d19636250ff2b33e758a` (2024-05-30T07:07:32Z) — Reduce alpha of player coloured range circles.
- `3eca717f77aa4020f1063ce01d424bdd6f1079fa` (2024-05-04T12:23:35+01:00) — Updates. - Added Cryostorm. - Improved Cryo Trooper voice. - Added icons. - Use player colour for all range indicators where owner is significant. - Yaml fixes.
- `d5386f03fce8423fa7ae27e1212967e0d33b9d21` (2024-02-27T07:56:50Z) — Show range circle for enemy Veil of War. Fix cluster mines causing damage when defused.

### `Traits/Render/WithColoredSelectionBox.cs`

Vendor content matches approximately `7057e3569ec5f3178357e0948bde12fd311dd22b` (2023-06-18T12:48:44+01:00; Exception fix.).

- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `ca85940142debcef8cc5d11efa86eb8165850c2e` (2025-01-01T10:34:38Z) — - Player coloured selection box for mines. - Troop Crawler dummy weapon no longer targets vehicles. - Increase Hoplite blind duration by 1s. Increase radius vs infantry slightly. Reset weapon after not attacking for a few seconds. - Corrected Scrin unit palettes in campaign so they appear grey when built by Nod.

### `Traits/Render/WithDisguiseTargetPalette.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `e206b0dd8b5fb9af25d951cbf480b60305cbc492` (2023-12-28T16:46:26Z) — Allow spies to disguise as infantry with any palette. Added SEAL/Commissar icons when disguised.

### `Traits/Render/WithEnabledAnimation.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `2ed967e6ace90b214e478a52960343be84ee31ef` (2024-08-26T15:17:45+01:00) — Balance/misc. - Increase Nuke Cannon splash radius and damage vs heavy armor. - Improved Nuke Cannon deploy behaviour to allow pre-targeting. - Mission 22 improvements. - Removed base regen from Yuri/Mastermind in missions 15/20. - Terror Dogs take reduced damage from each other's explosions. - Tibcore upgrade applies to IFV/Reckoner. - Increased range of Laser IFV/Reckoner by 1. Increased damage. - Increased Disruptor damage vs defenses. - Increased Viper damage. - Increased Cyclops range by 1. - Increased Obliterator spread so damage applies more consistently. - Increased Firestorm Missile damage vs heavy armor. - Reduced gren/flamer Heroes damage reduction a little more. - Troop Crawler from 1.5k to 1.6k. - Tooltip corrections.

### `Traits/Render/WithNameTagDecorationCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `30837752e6dd34adbab6dcc0c49b798e7ae29fc0` (2023-08-19T15:35:33+01:00) — Improved targeting for GrantExternalConditionPowerCA and ChronoshiftPowerCA.
- `7057e3569ec5f3178357e0948bde12fd311dd22b` (2023-06-18T12:48:44+01:00) — Exception fix.
- `389eca585ce9c39b79a2839bb22a97aab4098a7c` (2023-06-17T13:29:28+01:00) — Updated WithNameTagDecorationCA and WithColoredSelectionBox to allow team colours. Fixed missing main menu tooltips.
- `051bd79448caebd670bb2c217b619f8d79250286` (2023-06-17T10:40:34+01:00) — WithNameTagDecorationCA to allow contrast colour to be specified. Add name tags to Mastermind Madness.
- `62ed059cfcb4b64f2f2d3a46a2af018a9434c7c1` (2023-05-29T11:46:02+01:00) — Show number of units queued for conversion in Temple Prime.

### `Traits/Render/WithProductionDoorOverlayCA.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `28861bb689bb64d2e888a213e11209bff0502ce6` (2025-12-19T14:41:40Z) — Co-op improvements.
- `3248b6e0591704103833d3103e9d7c99a681abd6` (2025-12-19T14:41:40Z) — Co-op improvements.
- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.

### `Traits/Render/WithRangeCircleCA.cs`

Vendor content matches approximately `51c1c2f633ee8b8d4255d19636250ff2b33e758a` (2024-05-30T07:07:32Z; Reduce alpha of player coloured range circles.).

- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.

### `Traits/ResourcePurifierCA.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.

### `Traits/Sound/AmbientSoundCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `7f041ae0789747d06b85afa0e17a89fe59b41164` (2024-08-23T12:39:57+01:00) — Stop looping ambient sounds when game is paused. Don't include Troop Crawler in statistics.
- `7cb898702255d959241e9b7ef1cee3dfe0f15ad4` (2023-05-29T16:14:25+01:00) — Misc. - Stop ambient sounds after game ends. - Use charging attacks for EMP Missile and Firestorm Barrage so time to fire is consistent regardless of initial turret facing.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `b2286da8eabf18577b63bd049875d8fdd8cc153c` (2022-02-02T13:01:13Z) — Additional changes to bring customised traits in line with their base versions as far as possible. Added descriptions to these classes to explain the differences with base versions.
- `eed1e75fa0d574d8532d6a326cafcdfff8597ac7` (2022-01-31T22:55:56Z) — TurretedFloating fix. EMP missile fix. Minor adjustments to match engine classes. Removed ContrailCA, RevealsMapCA and RepairableNearCA as the engine versions seem to do everything we need now.
- `7b1a09ba69dbff519dbe938474c6d1a81078b324` (2022-01-31T18:16:12Z) — C# fixes.
- `f1b9586e205899307b897d3bb0eed9f6003ddb8f` (2021-05-30T15:45:22+01:00) — Added "Purification Doctrine" upgrade for Black Hand on Tech Center. Upgrades Flame Tank to have a longer range, long duration spray, and replaces Flamethrower with Black Hand trooper that has stats similar to Chem Warrior, which it also replaces.
- `d744fc2c9da6588ee53c0e0fd2b0babb1bcd6fe1` (2021-04-01T22:34:06+10:00) — Silence Audio Under Fog/Shroud
- `a908c5f9379263565ab7913dd6a9025f686157bb` (2021-02-13T18:46:10+10:00) — Engine Update & Carry All Bug fix

### `Traits/Sound/AnnounceOnCreation.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `4fb632bd99bda3cdb055f270ce3f29fe13edca09` (2024-02-05T21:45:57Z) — Heavy Flame Tank voice. Hypercharge doesn't drain until firing. +0.5 Devourer/Darkener range. Yaml fixes/cleanup.
- `cf4d92bcef5a446f087c33c4b3ea5a0318702dee` (2024-02-05T16:56:16+08:00) — Add TITN VO

### `Traits/Sound/AttackSoundsCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `822283bad792bbafcd17460c3c2d82585fba5987` (2022-06-24T20:52:39+01:00) — Don't play attack sounds when trait is disabled.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `95a3c9a63527845185b6e032daac3124f6938114` (2022-06-20T23:59:08+01:00) — Make repair/heal sounds not audible through fog.

### `Traits/SpawnedExplodes.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `c72dd9565c02b5d75f1101cec9d671f6aa16a802` (2025-06-07T19:22:54+01:00) — Engine update fixes.
- `a41ab548db80b6e6f206d3072dbc03ee375ceb18` (2024-05-07T19:37:01+01:00) — Patriot Strike.
- `ba62f9d0167fb6ac857a48b3129df7a27921e0a7` (2023-12-17T10:17:26Z) — Cruise missile.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `88d529cd78d031c28d0c9a4e7ce8bad3c35353f2` (2022-06-23T17:22:29+01:00) — Use .Count/.Length where possible instead of .Count()/.Any().
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `7680a0c3ece4f9ed5972da9780ddd0ca6b44eb8f` (2020-05-01T05:33:14+01:00) — Allow V3 Vet Damage Bonus
- `ada5eba3f87c36e1a0ddd09ea589d59f22b6ecd7` (2020-05-01T05:18:28+01:00) — Fix V3 exploding twice when shot down
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo
- `6d0ff33bfd1edc9fe5bf3c43f319f8128e3612ee` (2019-12-14T19:14:58Z) — 0.60.1

### `Traits/SpawnRandomActorOnDeath.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `f7ad46bcbf919d006d6f17e697058da13fd94357` (2020-05-18T13:41:45+01:00) — +Add more Civilians (Make Spawns more like TD)

### `Traits/SupportPowers/GrantExternalConditionPowerCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `bacca5f24dc41d59b5d0ca2a4d05b23a4e1e79a2` (2026-06-04T23:51:56+01:00) — Warning fix.
- `64a7ec1a1dea8c57492e45f55a6a0d983c5bd172` (2026-06-04T15:46:47Z) — - The full XP of any destroyed ARC drones will now be added to a singular reclaimable XP pool. On production of new drones, this XP will be drawn from up to veterancy level 2. - Mini Drones will transfer their XP to the parent unit on attaching. They will then inherit the veterancy level of the parent unit, and any damage dealt will be given to the parent unit. - Suppression Field can be applied as long as one valid unit is visible within the target circle (non-visible units within the circle will then be affected upon activation). - Made Templar laser with Quantum Capacitors more visually distinct. - Red skull icon for Assassins. - Fixed triple SSM with Black Napalm burst count. Adjusted reload to bring DPS into line. - Removed duplicate lasher warhead.
- `ea1b851088cb523c23c3f9b7b1f4d1c6b4d0a2a3` (2025-12-07T16:13:06Z) — Clean up trait lookups.
- `adbcb988bed25b86495d51400057caa9c923c68b` (2025-06-08T11:24:46+01:00) — Engine update part 7.
- `c72dd9565c02b5d75f1101cec9d671f6aa16a802` (2025-06-07T19:22:54+01:00) — Engine update fixes.
- `ba78b89641ed9141051fb0814484b2e87f0609c0` (2025-06-07T13:53:20+01:00) — Prioritize atomic ammo by unit value.
- `0b33a9cc4267f8ad0a25aead50ec366adeb3fe0a` (2025-01-15T18:26:33Z) — Validate targets before activating grant condition powers.
- `a46a0318effb24c571e3dac724a2b98e61d9c107` (2024-06-23T08:57:28+01:00) — Misc updates. - Bombardier upgrade available regardless of strategy. - Removed Zone Raider/Zone Defender upgrades. Available with Seek & Destroy II and Hold the Line II respectively. - Zone Trooper available with Bombardment II. - Enforcer requires Allied HQ instead of Tech Center. - Reduced Coalition negotiation time from 2:30 to 2:00. - Allied HQ provides second level of optimized production in Multi-Queue Scaled mode. - Fixed Heroes of the Union. - Shock Troopers, Telsa Troopers, Rad Troopers and Desolators no longer receive inspiration buffs from Commissar/Overlord/Troop Crawler. - Pitbull rockets apply blind. Increased cost to 850. Reduced range to 6 (was increased from 5 to 7). - Increased Cryostorm cooldown from 5:00 to 5:30. - Reduced IFV and Missile IFV damage vs buildings and defenses.
- `dbd7d930d9f3b2657b9c3ba0a1dfe4289b96bf25` (2024-06-22T17:05:17+01:00) — Balancing. - Increase Obliterator projectile speed. - Reactive armor applies to BTRs. - Reduced XO damage vs infantry, increased vs light armor. - Reduced Wolverine damage vs heavy armor. - Increased Pitbull damage vs light armor. Reduced vs heavy armor. Increased range from 5 to 7. - Increased Basilisk speed from 68 to 100. - Heroes of the Union only applies to player's own units. - Increased Nullifier damage.
- `db539d3cd24bcc9c978ab5006807c39f4a1f6bc7` (2024-06-03T22:23:04+01:00) — Kill Zone & Heroes of the Union.
- `f780de413b847c2168b8fd7533ad76b081a425e8` (2024-05-25T13:04:55+01:00) — Zeus/Black Eagle voices. Allow for multiple prerequisite overrides for paratroopers and external condition powers.
- `6a24353abae6acecb7a53296479cd4e9b235a7b0` (2024-02-13T19:13:44Z) — Updates. - Fix condition warheads not applying to large actors with multiple targetable locations. - Added IronCurtainImmune and ChronoshiftImmune to easily prevent decoys from being targeted by these. - Reduced Venom damage vs buildings (with upgrade no change).
- `e7f96d3353ae13b4eb0591eccc0d52cf16856bbe` (2024-02-06T17:50:21Z) — Support power target highlighting. Allow for either circle or footprint mode.
- `0a6375ee0b08e0f2799aea3316880fd6704d8497` (2023-12-23T12:28:32Z) — Misc fixes/updates. - Added directional targeting to infiltration airstrike and corrected building damage. - IFV keeps distance in Medic/Spy modes. - Added minimum altitude to GrantExternalConditionPowerCA. - Prevent Soviets being resource capped in prologue 1.
- `a8c169035086fa8228e96babf74b2b60b80ecd89` (2023-08-25T15:24:56+01:00) — Desync fix. Move targeted unit count above cursor so not blocked by tooltips. Selected chronoshift targets are deselected when going out of leash range.
- `d5360301091213ba7dfe6d2fb41ae7495192dff1` (2023-08-21T23:13:45+01:00) — Misc - Reduced chronoshift duration for enemy units. - Restored return on death. - Cargo no longer killed on chronoshift, but can't be unloaded until returning. - Mission 2 crash fix. - Improved support power unit count. - Fixed Ion Conduits activating when Storm Column is powere down.
- `568a41e13d328975871e40041497ec0704339587` (2023-08-20T21:51:48+01:00) — Added target count for powers that affect a limited number of targets.
- `30837752e6dd34adbab6dcc0c49b798e7ae29fc0` (2023-08-19T15:35:33+01:00) — Improved targeting for GrantExternalConditionPowerCA and ChronoshiftPowerCA.
- `090f33479b9816b2045d929a5b4d9914ac9ee6e7` (2023-08-05T12:01:44+01:00) — 2307 engine fixes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.

### `Traits/TargetedAttackAbility.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `dde2a4a06630f0d9fdf171c1ba8a9c9ee32fc6c8` (2025-08-11T20:55:40+01:00) — - Updated targetable ability logic (multiple abilities per activation). - Mantis guards selection. - Fix Conduit crash. - Default dogs to Defend stance.
- `aa42f86614ae6f85c35a2a2668beda4ca378f409` (2025-05-25T17:21:05+01:00) — - Make Anathema affect MAD tank thump interval. - Improve Mothership crash explosion. - Increase Basilisk range from 5 to 8. - After 4 pulses Desolator eruption radius increases by 1 cell. - Fixed Decoy Projectors crash. - Fixed actor spawning abilities ordering by distance. - Fixed targeted weapon abilities no longer being targetable on ground. - Changed bulk transport loading cursor to yellow to make it easier to distinguish.
- `03be7c68b2773bcb20aefb45b078e3dfce969153` (2025-05-22T18:31:05+01:00) — - Mind Sparks and Decoy Projectors are now targeted abilities, where the target is where the sparks/decoys will move to after spawning. - Reduced Mind Spark suppression duration, rate of fire, and increased cooldown by 5s. Increase hitbox size for easier selection. - Pitbull target painter can target buildings under fog. - Heroes of the Union applies to Grenadiers and Flamethrowers.
- `cea756c8449898fb1574c7857b87f6b1ebdb7255` (2025-05-19T08:08:29+01:00) — - Fixed crash when manually releasing mind controlled slaves. - Added target painter ability to Pitbull. - Added minimum range to Aurora so it will circle back instead of missing. - Increased Killzone duration from 16s to 30s. - FlashTarget warhead. - WithFlashEffect trait. - Tooltip tweaks.
- `666603b8f6720d4c6c686bc4ca747de821d21f3a` (2025-05-18T08:31:47+01:00) — - Loyalist growth bonus applies to full build radius. - Enforcer deals damage in a line. - Enforcer IFV gains 50% damage reduction (up from 30%). Fires double shot. - Increased Hoplite IFV rate of fire, splash radius and damage. - Simplified Hoplite recharge yaml. - Floating Disc drain targeted via ability.
- `3f2d859369407a4253307f7ebca0407d6fa98491` (2025-02-05T13:05:43Z) — - Remove air damage from anti-ground missiles. - Fix stuck Halo on mission Domination. - Minor tooltip corrections. - Speculative Nuke Cannon fix. - TargetedAttackAbility for Jackknives. - Speculative post-game spawner slave crash.
- `f2b742c4f39bedf608ff79ef17d1547b3a89145c` (2024-06-24T13:21:59+01:00) — Balancing. - Increased Mammoth Tank and Tripod HP by ~5% (all variants). - Reduced Rhino Tank damage slightly. - Thrasher Tank not slowed by crushing and moves faster. - Reduced Shade EMP duration from 13s to 9s. Reduced area of effect slightly. - Partially reverted XO damage nerf vs infantry. - Reduced Apache/Yak damage vs buildings. - Increased TOW missile damage, increased reload time, added reload bar, new hit sound. - Increased RoF of Laser Battle Tank. - Added some flexibility to TargetedAttackAbility (unused atm). - Increased duration of Hum-Vee/Guardian Drone point defense shield from 3s to 4s. Increased damage reduction from -60% to -66%. Increased cooldown by 5s. - Reduced Desolator splash damage slightly. Reduced damage against light armored infantry.
- `f55b2348f823788b207d93c88d4e6e7062a446f6` (2024-01-12T08:24:32Z) — Updates. - Added Hypercharge upgrade for Scrin Seeker & Lacerator. - Chem Warrior gains Tiberium Surge ability. - Yuri/Mastermind ability no longer kills slaves. Slaves are killed either manually by deploying them, or when exceeding capacity. - Minor mission 9 fix - prevent MAD Tank deploying when player does a sat hack on it. - Minor mission 15 fix - prevent player's units auto attacking disabled defenses. - Reduce Kirov separation distance to make them less prone to blocking each other from dropping bombs. - Improvements to targeted ability traits. - Battle Drone self-repairs to 50% instead of 100%.
- `c3aca173ab31e4771f6d13671a864e2187cf03fa` (2023-12-25T11:53:28Z) — Smart cast targeted abilities by default with ctrl forcing all selected units to fire the ability.
- `a2d73108dd05a662d9b14a81aa772897ed9e4544` (2023-12-13T19:11:51Z) — Fix targeted ability crash when selected unit dies.
- `c138150a740bd08e3e141ababacc58c07740b89c` (2023-06-05T17:10:22+01:00) — Balance/misc. - Fix fake building selection tooltips. - Make fake Radar Dome and War Factory infiltratable by Infiltrators. - Add 5 second delay before fake building can be detonated. - Reduce Enlightened EMP duration vs defenses. - Changed voice line for Infiltrator infiltrating non power plants (was "new construction options" which may not be true).
- `baca1fc0dbd60fb2abd5597f476eadff4111e777` (2023-06-04T20:23:41+01:00) — Added targeted weapon ability functionality. - Enlightened can target EMP ability. Reduced speed, damage, EMP duration and EMP area of effect. - Updated teleporting units so deploy command can be used on a group. - Code formatting fixes.

### `Traits/TurnOnIdleCA.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `c58d8928c5262354470549bc11dc0fd8ce4d2952` (2026-05-31T18:49:27+01:00) — Replaced AttachedAircraft trait with ImmobilePositionable.

### `Traits/Warpable.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `8b82b7b09649df175e6a3385f395ac7da666a978` (2023-12-22T13:12:20Z) — Fixed empty warp damage bar appearing when units have very low health. Minor spelling/yaml corrections.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `6bae5962f68d7470b85c9ecb7a456369ca889f05` (2021-12-27T03:19:29+10:00) — Fix Error
- `f0b55cbbd99ecb94c7d338ab32fc3e7869e5b985` (2021-12-25T22:21:49Z) — Base warping progress bar on the currently required damage for warping rather than on the maximum value (for when ScaleWithCurrentHealthPercentage is true).
- `aa92622d4249e83e70ef15be848dd698abd7c36e` (2021-10-16T13:44:42+01:00) — Chrono Prison warp damage now wears off gradually rather than after a fixed 120 ticks (so the longer a unit has been warped the longer it will take to wear off).
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `db922b734bf05d6bea79251dc401168e0260b9ab` (2019-12-17T23:52:54Z) — Add Warpable & Point Defense

### `TraitsInterfaces.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `800fb119b4bafa092d5c9c0a2fb6903697e337f7` (2026-07-08T20:05:28+01:00) — Ion Cannon & Lightning Storm always strikes center with first shot.
- `21c6ed216b673f95f54b22851f7ac045bb007a85` (2025-12-02T08:17:24Z) — Encyclopedia updates.
- `3f07398638ae11fdac95a91f2711647dda2d01f3` (2025-10-29T17:53:23Z) — - Mini Drones inherit cloak from parent. - Corrected TD Harvester palette. - Fixed Mini Drone attach sound.
- `9d611b686bde86c0dbb01aa03924fd7d6716fcf9` (2025-06-26T13:04:59+01:00) — Scale point defense laser in the same way as point defense shield.
- `d8f445aa97bd38b1f168de7cb39e786570200beb` (2025-05-06T08:12:12+01:00) — Scrin allegiance bonuses. - Loyalist: Resources near Colony Platforms regrow faster. - Rebel: Colony Ship can produces structures while moving. - Malefic: Colony Platforms are cloaked.
- `49e916f2ae0269512abc289e6c09cae124f84cc6` (2024-11-06T11:16:47Z) — - Reduced Patriot missile damage & splash. Reduced distance to avoid slightly. - UI indicators for GDI strategy level and Nod building/harvester kills.
- `47c30b106559bd1b1f4821c054011fcffa3cf33e` (2024-11-03T09:52:44Z) — Nod branch groundwork.
- `71a7ca5f9df63bc1b5cdb663fd577c6aabbd4c19` (2024-10-17T18:25:32+01:00) — - Added random delay before firing for Shock Trooper, Tesla Trooper, Rad Trooper, Desolator, Acolyte, Templar, Sniper. Increased reload to counterbalance. - Reduce Darkener slow and turn rate. - Tripods regenerate on Tib/resources. - Updated Lightning Storm and Ion Cannon superweapons so damage is consistent. - Fixed Buzzer Swarm blinding aircraft.
- `2a0b78ccae31dfb5bd70eb24f9b1cd16c165a869` (2023-06-07T21:56:50+01:00) — Added trait so that selected Shadow Team units will remain selected after landing. Fixed some death sequence palettes.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `307a50b81e88aaeb38ca02354f4c119cc35221f1` (2023-03-26T10:26:18+01:00) — Temporal Flux allows Chrono Tank to teleport twice before recharging. Reduced Chrono Tank damage vs infantry and speed.
- `a7d5debd6022537e7dfe4b67f7d343e3464daa7a` (2022-06-12T09:50:05+01:00) — Balance/misc: - Increase vision of Warthog and Stormrider by 1 to match other T2 planes. - Corrected Hardened Carapace cost to match Flak Armor. - Reduced Feeder Mutation cooldown from 4:30 to 4:00. - Temporal Flux upgrade also increases Chrono Tank teleport range and reduces its cooldown.
- `a21ab12bbfa958076417594900a32ea15bfdd61c` (2021-11-23T15:32:58Z) — AI air superiority and squad management improvements.
- `2b42f3d9cba2cfce1ce0fa2c202fd2db637cff2a` (2021-06-14T23:02:14+01:00) — Added Scrin Mothership.
- `e78069c0a146e057cadc6940f90c3024bcf95722` (2021-02-07T20:13:22+10:00) — Update AI + Add Prism Forwarding
- `1c91214494f76b6731b0b8b9084e560ee1443969` (2021-02-04T21:27:12+10:00) — Prep mod for update
- `4b99d3040aa33f7f83c5c2ebae599904a1cc7299` (2021-01-03T22:43:29+10:00) — WIP playtest branch
- `0dc7cfc289e108babe6c8f46717469c68b7c9495` (2020-05-01T04:23:02+01:00) — Added RA2 Chronosphere effect
- `5117512b1cf87b7f72a53fa8c16ca29f5fb7a47d` (2020-03-16T06:35:28Z) — Engine Update + Cryo
- `5f9bd7777761120640d00a05d147cd38b628379e` (2020-01-03T01:58:10Z) — Add Faction Support Powers +

### `Widgets/ExternalLinkButtonWidget.cs`

Vendor content matches approximately `990765108ba57cafa3a8730a0fb9fc2ea2960342` (2023-07-06T07:18:43Z; Fixed main menu link button tooltip being shown on other menu buttons.).

- `30837752e6dd34adbab6dcc0c49b798e7ae29fc0` (2023-08-19T15:35:33+01:00) — Improved targeting for GrantExternalConditionPowerCA and ChronoshiftPowerCA.

### `Widgets/Logic/AddFactionSuffixLogicCA.cs`

Vendor content matches approximately `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00; Updated copyright notice. Removed unused imports. Namespace corrections.).

- `222a8ab45d4ed681437f38ed22b6573a8a1dcf6e` (2025-07-05T10:03:25+01:00) — Update UI classes to match engine changes.

### `Widgets/Logic/Ingame/ProductionTabsLogicCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `fefada4a24499fe9013eddfd35327e93394935af` (2025-07-26T21:29:29+01:00) — Fix production tabs crash.
- `ac3f7a7e89fc46ffb3cfc8206e00fc86bb8f744c` (2024-05-18T07:35:00+01:00) — Scrin allegiances, Eviscerator, Obliterator, Nullifier, Overlord's Wrath, Gateway & Watcher.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `0f485b42e257fd345a648e9d5b7a7df05dc96bc1` (2022-08-16T18:03:35+01:00) — Multi-queue.

### `Widgets/Logic/LobbyOptionsLogicCA.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `993a70c0f43bcd89a0a8f849463718b17e7ac8f4` (2026-06-12T22:53:30+01:00) — - Enlarged lobby panel so all options are visible. - Added blind pick lobby option.
- `35127f26c3d0d40cf59ea8acd206a89a06f94696` (2025-12-07T10:55:27Z) — Advanced Options section in lobby options (for co-op).
- `a7eb06585e18110c443b25fa9cd3d5dc14625bad` (2025-11-13T09:51:25Z) — Co-op mission updates.
- `c72dd9565c02b5d75f1101cec9d671f6aa16a802` (2025-06-07T19:22:54+01:00) — Engine update fixes.
- `21738535acf1db1d4d1ce8d83316bfeb59ff03f7` (2023-12-23T10:52:48Z) — Added reset lobby options button.
- `700c6d0d8f47b32338b8dfd32c037f959797c704` (2023-09-13T16:35:18+01:00) — Save/load lobby options.

### `Widgets/Logic/SimpleTooltipWithDescLogic.cs`

Vendor content matches approximately `5b4ed31d19cdfd87c7dbb09c0a0d7a00bdbd189b` (2023-07-01T18:15:20+01:00; Faction tooltips on scores panel. Reveal random factions when player selects one of their units/structures.).

- `bd93af528e4ca61c06470edae69d43d72506c1d2` (2025-06-09T18:14:44+01:00) — Engine update part 11.
- `525654b7690b229a623764960c91dd09002ba92b` (2025-06-23T19:08:42+01:00) — Fix disabled Allied influence indicator tooltip crash.

### `Widgets/ProductionPaletteCAWidget.cs`

Vendor content matches approximately `04ccb8abf61c90e0a344d7f0e4a3eb5660e26bb6` (2023-06-16T18:48:59+01:00; Code styling.).

- `30837752e6dd34adbab6dcc0c49b798e7ae29fc0` (2023-08-19T15:35:33+01:00) — Improved targeting for GrantExternalConditionPowerCA and ChronoshiftPowerCA.

### `Widgets/ProductionTabsCAWidget.cs`

No exact historical match was identified within the searched upstream history; the following are the most recent commits touching the counterpart.

- `06a4efa6331f99ae9dde396ae3e49a849d08f2f3` (2025-07-31T17:02:23+01:00) — Mission updates & bugfixes.
- `fefada4a24499fe9013eddfd35327e93394935af` (2025-07-26T21:29:29+01:00) — Fix production tabs crash.
- `5074360c99448015c89a6a4976cc73f3b5131ff8` (2025-07-25T17:01:32+01:00) — Mission fixes.
- `d8bd4601d4d3438c9c7dcc751f76c23be4f25bb0` (2025-07-16T16:53:33+01:00) — - Updated ScrollableLineGraphWidget. - Updated ProductionTabsCAWidget. - Reverted utility.cmd. - Added Thrasher Tank to Reactive Armor tooltip.
- `222a8ab45d4ed681437f38ed22b6573a8a1dcf6e` (2025-07-05T10:03:25+01:00) — Update UI classes to match engine changes.
- `23b3ecf7ff525bec11ad9b14ebe5a14e7b06abde` (2023-08-24T21:39:39+01:00) — Misc - Separate tab for dogs in MQ (Barracks no longer required). - Increased Mechanic salvage reward to $200.
- `a7c77671a3af802f6e492e0d198d7b1d8ceefa2b` (2023-08-05T23:17:09+01:00) — Updates/fixes for engine.
- `04ccb8abf61c90e0a344d7f0e4a3eb5660e26bb6` (2023-06-16T18:48:59+01:00) — Code styling.
- `cd810bf65697bb022fcaffaeb37b6af9af4e6cd4` (2023-06-16T07:01:36Z) — UI updates. - External links on main menu. - Button hover cursor. - Updated click sound. - Added pressed state to production queue buttons.
- `59e4d0e55beee0a9d0bddfcd222b46148359c3cf` (2023-05-27T20:52:25+01:00) — Updated copyright notice. Removed unused imports. Namespace corrections.
- `0fb7ab8c99f65c5b2f5a1f22a6cf755e3b7ad6c6` (2022-11-28T17:42:20Z) — Fix rare crash caused production palette trying to update as the game is aborted.
- `b630cdb7458f1b5a4d1be5fbb3bd2a8a3be4b0c0` (2022-09-04T14:16:18+01:00) — If queues exist, but no queue is selected when updating production tabs, select the first one.
- `7df8b306cde805009ffb52fe3ec28ab45ad17447` (2022-08-26T18:14:13+01:00) — Reduced Black Hand damage vs infantry and light armor. Clicking on a production structure that causes the queue to change will scroll to top.
- `de47f7aac6071ba7661e1461ac4eed67eaebc137` (2022-08-21T17:55:14+01:00) — Fixes to stop flooding of debug.log.
- `436706fefb5452c5c53b0b39471ba9040ef91c11` (2022-08-19T07:25:11Z) — Scroll to top of production palette on changing queues. Temple Prime only produces Cyborgs in single queue mode.
- `0f485b42e257fd345a648e9d5b7a7df05dc96bc1` (2022-08-16T18:03:35+01:00) — Multi-queue.

## Upstream CA files with no Cameo counterpart

Count: **320**.

- `Activities/Attach.cs` — `Attach`: (no class-level Desc)
- `Activities/AttackFrontalFollowActivity.cs` — `AttackFrontalFollowActivity`: (no class-level Desc)
- `Activities/BallisticMissileFly.cs` — `BallisticMissileFly`: (no class-level Desc)
- `Activities/ChronoResourceTeleport.cs` — `ChronoResourceTeleport`: (no class-level Desc)
- `Activities/ConvertActor.cs` — `ConvertActor`: (no class-level Desc)
- `Activities/DeployForGrantedConditionTurreted.cs` — `DeployForGrantedConditionTurreted`: (no class-level Desc); `DeployInner`: (no class-level Desc)
- `Activities/DiveApproach.cs` — `DiveApproach`: (no class-level Desc)
- `Activities/EnterAirstrikeMaster.cs` — `EnterAirstrikeMaster`: (no class-level Desc); `ReturnAirstrikeMaster`: (no class-level Desc)
- `Activities/EnterCarrierMaster.cs` — `EnterCarrierMaster`: (no class-level Desc)
- `Activities/EnterTeleportNetwork.cs` — `EnterTeleportNetwork`: (no class-level Desc)
- `Activities/FallDown.cs` — `FallDown`: (no class-level Desc)
- `Activities/MassRideTransport.cs` — `MassRideTransport`: (no class-level Desc)
- `Activities/ParadropCargo.cs` — `ParadropCargo`: (no class-level Desc)
- `Activities/ProductionAirdropDeliver.cs` — `ProductionAirdropDeliver`: (no class-level Desc)
- `Activities/SpawnActor.cs` — `SpawnActor`: (no class-level Desc)
- `Activities/TargetedLeap.cs` — `TargetedLeap`: (no class-level Desc)
- `Activities/Upgrade.cs` — `Upgrade`: Activity whereby an actor searches for a location it can upgrade, moves to that location, and receives the upgrade.
- `Effects/Countdown.cs` — `Countdown`: (no class-level Desc)
- `Effects/DistortionHaloEffect.cs` — `DistortionHaloAnimation`: (no class-level Desc); `DistortionHaloEffect`: (no class-level Desc)
- `Effects/FlashTargetCA.cs` — `FlashTargetCA`: (no class-level Desc)
- `Effects/GPSRadarDotEffect.cs` — `GpsRadarDotEffect`: (no class-level Desc); `DotState`: (no class-level Desc)
- `Effects/GpsSatelliteCA.cs` — `GpsSatelliteCA`: (no class-level Desc)
- `Effects/LinkedProducerIndicator.cs` — `LinkedProducerIndicator`: (no class-level Desc)
- `Effects/MultiWeaponImpactEffect.cs` — `MultiWeaponImpactEffect`: (no class-level Desc)
- `Effects/SatelliteLaunchCA.cs` — `SatelliteLaunchCA`: (no class-level Desc)
- `Effects/SmokeParticle.cs` — `SmokeParticle`: (no class-level Desc)
- `Graphics/ArcRenderable.cs` — (no class declaration found)
- `Graphics/CapsuleAnnotationRenderable.cs` — `CapsuleAnnotationRenderable`: (no class-level Desc)
- `Graphics/DistortionHaloRenderable.cs` — (no class declaration found)
- `Graphics/ElectricBoltRenderable.cs` — (no class declaration found)
- `Graphics/KKNDLaserRenderable.cs` — (no class declaration found)
- `Graphics/RadBeamRenderable.cs` — (no class declaration found)
- `Graphics/RailgunHelixRenderableCA.cs` — `RailgunHelixRenderableCA`: Exact copy of base version just replacing Railgun with RailgunCA.
- `Graphics/TeslaZapRenderableCA.cs` — `TeslaZapRenderableCA`: Exact copy of base version to get around protection level in TelsaZapCA.
- `Graphics/TintedCell.cs` — `TintedCell`: (no class-level Desc)
- `Graphics/UIModifyableSpriteRenderable.cs` — `UIModifyableSpriteRenderable`: (no class-level Desc)
- `LoadScreens/ImageLoadScreen.cs` — `ImageLoadScreen`: (no class-level Desc)
- `Orders/ConvertibleOrderTargeter.cs` — `ConvertibleOrderTargeter`: (no class-level Desc)
- `Orders/MassEnterCargoOrderTargeter.cs` — `MassEnterCargoOrderTargeter`: (no class-level Desc)
- `Orders/ShootableBallisticMissileMoveOrderTargeter.cs` — `ShootableBallisticMissileMoveOrderTargeter`: (no class-level Desc)
- `Orders/UpgradeOrderGenerator.cs` — `UpgradeOrderGenerator`: (no class-level Desc)
- `Projectiles/ArcLaserZap.cs` — `ArcLaserZap`: Not a sprite, but an engine effect.; `ArcLaserZap`: Brightness-only multiplier for the glow halo, independent of GlowScale (does not grow the radius).
- `Projectiles/AreaBeamCA.cs` — `AreaBeamCA`: (no class-level Desc); `AreaBeamCA`: Beam color is the player's color.
- `Projectiles/AthenaProjectile.cs` — `AthenaProjectile`: Dummy projectile exploding on/above the target actor/position after a specified delay.; `AthenaProjectile`: Delay between firing and exploding.
- `Projectiles/BulletCA.cs` — `BulletCA`: (no class-level Desc); `BulletCA`: If true, full passthroughs will travel parallel to the weapon muzzle offset.
- `Projectiles/ElectricBolt.cs` — `ElectricBolt`: Not a sprite, but an engine effect.; `ElectricBolt`: Brightness-only multiplier for the glow halo, independent of GlowScale (does not grow the radius).
- `Projectiles/InstantExplode.cs` — `InstantExplode`: (no class-level Desc); `InstantExplode`: (no class-level Desc)
- `Projectiles/KKNDLaser.cs` — `KKNDLaser`: A beautiful generated laser beam.; `KKNDLaser`: Brightness-only multiplier for the glow halo, independent of GlowScale (does not grow the radius).
- `Projectiles/MeteorStrike.cs` — `MeteorStrike`: (no class-level Desc)
- `Projectiles/MissileCA.cs` — `MissileCA`: (no class-level Desc); `MissileCA`: Ignore variable launch angle and speed when target is below this distance.
- `Projectiles/ProjectileHusk.cs` — `ProjectileHusk`: Projectile with customisable acceleration vector, recieve dead actor speed by using range modifier, used as aircraft husk.; `ProjectileHusk`: Use the Player Palette to render the trail sequence.
- `Projectiles/RadBeam.cs` — `RadBeam`: Not a sprite, but an engine effect.; `RadBeam`: Brightness-only multiplier for the glow halo, independent of GlowScale (does not grow the radius).
- `Projectiles/RailgunCA.cs` — `RailgunCA`: Laser effect with helix coiling around.; `RailgunCA`: Brightness-only multiplier for the glow halo, independent of GlowScale (does not grow the radius).
- `Projectiles/TeslaZapCA.cs` — `TeslaZapCA`: Copy of TeslaZap. CA version adds to ZOffset for targets below the source.; `TeslaZapCA`: Brightness-only multiplier for the glow halo, independent of GlowScale (does not grow the radius).
- `Scripting/ActorCAGlobal.cs` — `ActorCAGlobal`: (no class-level Desc)
- `Scripting/AirstrikeCAProperties.cs` — `AirstrikeCAProperties`: (no class-level Desc)
- `Scripting/BuildingProperties.cs` — `BuildingProperties`: (no class-level Desc)
- `Scripting/CombatCAProperties.cs` — `CombatCAProperties`: (no class-level Desc)
- `Scripting/MediaCAGlobal.cs` — `MediaCAGlobal`: PlaySound includes a volume modifier.
- `Scripting/PlayerCAProperties.cs` — `PlayerCAProperties`: (no class-level Desc)
- `Scripting/PortableChronoCAGlobal.cs` — `PortableChronoCAProperties`: (no class-level Desc)
- `Scripting/ScriptTriggersCA.cs` — `ScriptTriggersCA`: Allows map scripts to attach CA-specific triggers to this actor via the TriggerCA global.; `ScriptTriggersCA`: Allows map scripts to attach CA-specific triggers to this actor via the TriggerCA global.
- `Scripting/TargetableCAProperties.cs` — `TargetableCAProperties`: (no class-level Desc)
- `Scripting/TargetedLeapAbilityGlobal.cs` — `TargetableLeapAbilityProperties`: (no class-level Desc)
- `Scripting/TriggerCAGlobal.cs` — `TriggerCAGlobal`: (no class-level Desc)
- `Scripting/UtilsCAGlobal.cs` — `UtilsCAGlobal`: (no class-level Desc)
- `SpriteLoaders/R8Loader.cs` — `R8Loader`: (no class-level Desc); `R8Frame`: (no class-level Desc)
- `Traits/AddsToReclaimableValue.cs` — `AddsToReclaimableValue`: When killed, this actor adds value to the owner's reclaimable value pool.; `AddsToReclaimableValue`: DeathTypes for which value should be added. Use an empty list (the default) to allow all DeathTypes.
- `Traits/AdvancesTimeline.cs` — `AdvancesTimeline`: On creation, adds specified number of ticks to a specified `ProvidesPrerequisitesOnTimeline` trait.; `AdvancesTimeline`: Number of ticks to advance.
- `Traits/Air/FallsDownAndTransforms.cs` — `FallsDownAndTransforms`: Falls to the ground then transforms into a different actor.; `FallsDownAndTransforms`: Velocity (per tick) the actor moves forwards.
- `Traits/Air/Interceptor.cs` — `Interceptor`: (no class-level Desc); `Interceptor`: Used for actors spawned by InterceptorsPower.
- `Traits/AirstrikeMaster.cs` — `AirstrikeMaster`: This actor can send in other actors to deliver an airstrike.; `AirstrikeMaster`: The sound will be played when mark a target; `AirstrikeSlaveEntry`: The sound will be played when mark a target; `to`: The sound will be played when mark a target; `to`: (no class-level Desc)
- `Traits/AirstrikeSlave.cs` — `AirstrikeSlave`: Can be slaved to a spawner.; `AirstrikeSlave`: Can be slaved to a spawner.
- `Traits/ArmamentBurstCounter.cs` — `ArmamentBurstCounter`: Tracks 1-based shot indexes within a burst for a specific armament.; `ArmamentBurstCounter`: The armament name to track.
- `Traits/Attack/AttackFollowFrontal.cs` — `AttackFollowFrontal`: (no class-level Desc); `AttackFollowFrontal`: Actor will turn directly to target regardless the FacingTolerance to catch its target in full fire angle.
- `Traits/Attack/AttackOpenTopped.cs` — `AttackOpenTopped`: Implements the YR OpenTopped logic where transported actors used separate firing offsets, ignoring facing. Compatible with both `Cargo`/`Passengers` or `Garrionable`/`Garrisoners` logic.; `AttackOpenTopped`: Fire port offsets in local coordinates.
- `Traits/Attack/AttackPrism.cs` — `AttackPrism`: Implements the charge-then-burst attack logic specific to the RA tesla coil.; `AttackPrism`: Sound to play when actor charges.; `ChargeAttack`: Sound to play when actor charges.; `ChargeFire`: (no class-level Desc)
- `Traits/Attack/IgnoreOutOfRangeAttackOrders.cs` — `IgnoreOutOfRangeAttackOrders`: Intercepts regular attack orders against out-of-range actor targets and ignores them while enabled.; `IgnoreOutOfRangeAttackOrders`: If true, will ignore out of range attack orders that are forced by the player.; `IgnoreOutOfRangeAttackOrderTargeter`: (no class-level Desc)
- `Traits/AutoDeployer.cs` — `AutoDeployer`: Allow this actor to automatically issue deploy orders on selected events. Require the AutoDeployManager trait on the player actor.; `AutoDeployer`: Delay to wait for the actor to undeploy (if capable to) after a successful deploy.
- `Traits/AutoGuard.cs` — `AutoGuard`: Attach to support unit so that when ordered as part of a group with combat units it will guard those units.; `AutoGuard`: If guard targets are this much further from the target, don't guard them.
- `Traits/BallisticMissile.cs` — `BallisticMissile`: This unit, when ordered to move, will fly in ballistic path then will detonate itself upon reaching target.; `BallisticMissile`: This unit, when ordered to move, will fly in ballistic path then will detonate itself upon reaching target.
- `Traits/Berserkable.cs` — `Berserkable`: When enabled, the actor will randomly try to attack nearby other actors.; `Berserkable`: Maximum scan range. If zero, uses the maximum range of the unit's weapons and auto-target traits.
- `Traits/CancelActivityOnPickup.cs` — `CancelActivityOnPickup`: When picked up, cancels any activities.; `CancelActivityOnPickup`: When picked up, cancels any activities.
- `Traits/CargoBlocked.cs` — `CargoBlocked`: Attach to a transport to override the unload order.; `CargoBlocked`: Cursor to display when hovering over the transport.; `CargoBlockedOrderTargeter`: Cursor to display when hovering over the transport.
- `Traits/CargoCloner.cs` — `CargoCloner`: Continuously produces the passenger actor at no cost. Assumes only one passenger.; `CargoCloner`: Defines to which players the bar is to be shown.
- `Traits/CarrierMaster.cs` — `CarrierMaster`: This actor can spawn actors.; `CarrierMaster`: Conditions to grant when specified actors are contained inside the transport. A dictionary of [actor id]: [condition].; `CarrierSlaveEntry`: Conditions to grant when specified actors are contained inside the transport. A dictionary of [actor id]: [condition].; `to`: Conditions to grant when specified actors are contained inside the transport. A dictionary of [actor id]: [condition].; `to`: (no class-level Desc)
- `Traits/CarrierSlave.cs` — `CarrierSlave`: Can be slaved to a spawner.; `CarrierSlave`: Can be slaved to a spawner.
- `Traits/ChronoResourceDelivery.cs` — `ChronoResourceDelivery`: When returning to a refinery to deliver resources, this actor will teleport if possible.; `ChronoResourceDelivery`: Volume the WarpInSound and WarpOutSound played at.
- `Traits/Conditions/DummyConditionConsumer.cs` — `DummyConditionConsumer`: Just to prevent YAML errors when a condition isn't used (sometimes cleaner than removing a large number of traits/properties).; `DummyConditionConsumer`: Just to prevent YAML errors when a condition isn't used (sometimes cleaner than removing a large number of traits/properties).
- `Traits/Conditions/DummyConditionGranter.cs` — `DummyConditionGranter`: Just to prevent YAML errors when a condition is consumed but not granted (sometimes cleaner than removing a large number of traits/properties).; `DummyConditionGranter`: Just to prevent YAML errors when a condition is consumed but not granted (sometimes cleaner than removing a large number of traits/properties).
- `Traits/Conditions/GrantConditionIfOwnerIsNeutral.cs` — `GrantConditionIfOwnerIsNeutral`: Grants a condition if the owner is the Neutral player.; `GrantConditionIfOwnerIsNeutral`: The condition to grant.
- `Traits/Conditions/GrantConditionOnActivity.cs` — `GrantConditionOnActivity`: (no class-level Desc); `GrantConditionOnActivity`: Sound to play when Active.
- `Traits/Conditions/GrantConditionOnCapture.cs` — `GrantConditionOnCapture`: Grants a condition when this actor is captured.; `GrantConditionOnCapture`: Grant condition only if the capturer's CaptureTypes overlap with these types. Leave empty to allow all types.
- `Traits/Conditions/GrantConditionOnDamageStateCA.cs` — `GrantConditionOnDamageStateCA`: Applies a condition to the actor at specified damage states.; `GrantConditionOnDamageStateCA`: Is the condition irrevocable once it has been activated?
- `Traits/Conditions/GrantConditionOnDeployTurreted.cs` — `GrantConditionOnDeployTurreted`: Grants a condition when a deploy order is issued. Can be paused with the granted condition to disable undeploying.; `GrantConditionOnDeployTurreted`: Display order for the deployed checkbox in the map editor
- `Traits/Conditions/GrantConditionOnLobbyOption.cs` — `GrantConditionOnLobbyOption`: Grants a condition to the actor when created if fog is enabled.; `GrantConditionOnLobbyOption`: If not boolean, list of string values that enable the condition.
- `Traits/Conditions/GrantConditionOnPlayerFunds.cs` — `GrantConditionOnPlayerFunds`: Grants a condition to this actor when the player has stored funds (cash plus resources).; `GrantConditionOnPlayerFunds`: Enable condition when funds are greater than this.
- `Traits/Conditions/GrantConditionOnResupply.cs` — `GrantConditionOnResupply`: Grants a condition when being resupplied.; `GrantConditionOnResupply`: Order name that toggles the condition.
- `Traits/Conditions/GrantConditionOnResupplying.cs` — `GrantConditionOnResupplying`: Grants a condition when resupplying another actor.; `GrantConditionOnResupplying`: Condition to grant.
- `Traits/Conditions/GrantConditionToAttached.cs` — `GrantConditionToAttached`: Grants a condition to any attached actors.; `GrantConditionToAttached`: The condition to grant.
- `Traits/Conditions/GrantConditionToSpawnerSlaves.cs` — `GrantConditionToSpawnerSlaves`: Grants a condition to any attached actors.; `GrantConditionToSpawnerSlaves`: The condition to grant.
- `Traits/Conditions/GrantConditionWhileProducing.cs` — `GrantConditionWhileProducing`: Grants a condition while the actor is producing something.; `GrantConditionWhileProducing`: The condition to grant while producing.
- `Traits/Conditions/GrantExternalConditionToOwner.cs` — `GrantExternalConditionToOwner`: Grants an external condition to the owner player's actor.; `GrantExternalConditionToOwner`: Grants an external condition to the owner player's actor.
- `Traits/Conditions/GrantPeriodicCondition.cs` — `GrantPeriodicCondition`: Grants a condition periodically.; `GrantPeriodicCondition`: The range of time (in ticks) with the condition being enabled.
- `Traits/Conditions/GrantTimedCondition.cs` — `GrantTimedCondition`: Gives a condition to the actor for a limited time.; `GrantTimedCondition`: If true, condition will last for full duration once enabled, even if trait is subsequently disabled/paused.
- `Traits/Conditions/GrantTimedConditionOnDeploy.cs` — `GrantTimedConditionOnDeploy`: (no class-level Desc); `GrantTimedConditionOnDeploy`: If DischargeOnAttack is true, maximum ticks before the condition will begin to drain regardless.
- `Traits/Conditions/GrantTimedConditionOnPointDefenseHit.cs` — `GrantTimedConditionOnPointDefenseHit`: Gives a condition to the actor for a limited time when point defense destroys an incoming projectile.; `GrantTimedConditionOnPointDefenseHit`: The amount of damage required to add 1 tick of charging time.
- `Traits/Conditions/ParachuteCargoOnCondition.cs` — `ParachuteCargoOnCondition`: (no class-level Desc); `ParachuteCargoOnCondition`: Return to base when drop complete?
- `Traits/Conditions/ProximityExternalConditionCA.cs` — `ProximityExternalConditionCA`: Applies a condition to actors within a specified range.; `ProximityExternalConditionCA`: Recalculate target distances every tick. If false, only range entry/exit updates the target set.
- `Traits/Conditions/TransformOnCondition.cs` — `TransformOnCondition`: (no class-level Desc); `TransformOnCondition`: (no class-level Desc)
- `Traits/Convertible.cs` — `Convertible`: This Actor can be converted into another actor (or actors) through the UnitConverter trait.; `Convertible`: Voice used when ordering to enter.
- `Traits/ConvertsResources.cs` — `ConvertsResources`: Gradually converts resources within a given radius.; `ConvertsResources`: Gradually converts resources within a given radius.
- `Traits/CrateCA.cs` — `CrateCA`: Copy of base version with a crash fix for when location is set before crate is added to world.; `CrateCA`: Define actors that can collect crates by setting this into the Crushes field from the Mobile trait.
- `Traits/CreateProxyActorForAllies.cs` — `CreateProxyActorForAllies`: Creates a proxy actor on creation for each allied player.; `CreateProxyActorForAllies`: If true, only creates proxy when owner is a playable (human) player.
- `Traits/DamagedByTerrainCA.cs` — `DamagedByTerrainCA`: This actor receives damage on the specified terrain type.; `DamagedByTerrainCA`: Duration of the flash in ticks. 0 for disabled.
- `Traits/DamagedByTintedCells.cs` — `DamagedByTintedCells`: This actor receives damage when in TintedCell area.; `DamagedByTintedCells`: Duration of the flash in ticks. 0 for disabled.
- `Traits/DelayedWeaponAttachable.cs` — `DelayedWeaponAttachable`: This trait interacts with and provides a container for Attach/DetachDelayedWeaponWarheads.; `DelayedWeaponAttachable`: The condition to grant while any DelayedWeapon is attached.
- `Traits/DelayedWeaponDetector.cs` — `DelayedWeaponDetector`: This trait can reveal DelayedWeapon progressbars on DelayedWeaponAttachable traits.; `DelayedWeaponDetector`: Range of detection.
- `Traits/DelayedWeaponTrigger.cs` — `DelayedWeaponTrigger`: (no class-level Desc)
- `Traits/EjectOnTransform.cs` — `EjectOnTransform`: Eject a ground soldier or a paratrooper while in the air.; `EjectOnTransform`: Name of the unit to eject. This actor type needs to have the Parachutable trait defined.
- `Traits/EncyclopediaExtras.cs` — `EncyclopediaExtras`: To override encyclopedia preview.; `EncyclopediaExtras`: Group name for variant dropdown (e.g., 'Allies Infantry').
- `Traits/FreeActorCA.cs` — `FreeActorCA`: Player receives a unit for free once the building is placed. This also works for structures. If you want more than one unit to appear copy this section and assign IDs like FreeActor@2, ...; `FreeActorCA`: Display order for the free actor checkbox in the map editor
- `Traits/FrozenUnderFogUpdatedByGpsRadar.cs` — `FrozenUnderFogUpdatedByGpsRadar`: Updates frozen actors of actors that change owners, are sold or die whilst having an active GPS power.; `FrozenUnderFogUpdatedByGpsRadar`: Updates frozen actors of actors that change owners, are sold or die whilst having an active GPS power.; `Traits`: Updates frozen actors of actors that change owners, are sold or die whilst having an active GPS power.
- `Traits/GiveCashOnCaptureCA.cs` — `GivesCashOnCaptureCA`: Lets the actor grant cash when captured.; `GivesCashOnCaptureCA`: Value actor percentage (if actor is used for value).
- `Traits/GivesBountyCA.cs` — `GivesBountyCA`: When killed, this actor causes the attacking player to receive money.; `GivesBountyCA`: DeathTypes for which a bounty should be granted. Use an empty list (the default) to allow all DeathTypes.
- `Traits/GivesExperienceCA.cs` — `GivesExperienceCA`: This actor gives experience to a GainsExperience actor when they are killed or damaged.; `GivesExperienceCA`: If true, gives experience on damage, otherwise gives experience when killed.
- `Traits/GivesPlayerExperienceOnCapture.cs` — `GivesPlayerExperienceOnCapture`: Grants player XP to capturing player.; `GivesPlayerExperienceOnCapture`: Modifier for captures after the first capture.
- `Traits/GPSRadarDot.cs` — `GpsRadarDot`: Show an indicator revealing the actor underneath the fog when a GpsRadarProvider is activated.; `GpsRadarDot`: Sprite used for this actor.
- `Traits/GpsRadarWatcher.cs` — `GpsRadarWatcher`: Required for GPS Radar related logic to function. Attach this to the player actor.; `GpsRadarWatcher`: Required for GPS Radar related logic to function. Attach this to the player actor.
- `Traits/ImmobileMultiCell.cs` — `ImmobileMultiCell`: (no class-level Desc); `ImmobileMultiCell`: Shift center of the actor by this offset.
- `Traits/ImmobilePositionable.cs` — `ImmobilePositionable`: Provides a mutable position and facing for actors that are moved externally, such as attachments.; `ImmobilePositionable`: Speed at which the actor turns.
- `Traits/Infiltration/InfiltrateForTimedCondition.cs` — `InfiltrateForTimedCondition`: The actor gains a timed condition when infiltrated.; `InfiltrateForTimedCondition`: If true, will also grant the condition to all actors of the same type owned by the target player.
- `Traits/Infiltration/InfiltrateToCreateProxyActor.cs` — `InfiltrateToCreateProxyActor`: Replaces InfiltrateForSupportPower. Allows the spawned proxy actor to inherit the faction of the infiltrated actor, or to be owned by the target.; `InfiltrateToCreateProxyActor`: If true, the spawned actor is destroyed if the parent actor dies, is sold, or is captured.
- `Traits/InheritsExperienceLevelOfMaster.cs` — `InheritsExperienceLevelOfMaster`: Grants conditions based on the current level of this actor's first available master.; `InheritsExperienceLevelOfMaster`: Number of ticks between master level checks.
- `Traits/InitiallyHunts.cs` — `InitiallyHunts`: Hunts on creation.; `InitiallyHunts`: Hunts on creation.
- `Traits/LaysMinefield.cs` — `LaysMinefield`: This actor places mines around itself, and replenishes them after a while.; `LaysMinefield`: Ignore placement rules
- `Traits/LinkedProducerSource.cs` — `LinkedProducerSource`: A possible source for a LinkedProducerTarget.; `LinkedProducerSource`: Text notification to display when setting a new target.; `LinkedProducerSourceAddLinkOrderTargeter`: (no class-level Desc)
- `Traits/LinkedProducerTarget.cs` — `LinkedProducerTarget`: The target of a linked producer. Any units produced at the targeted source will be either cloned or redirect at the target.; `LinkedProducerTarget`: If true, skips anything currently being produced when link is established.; `LinkedProducerTargetAddLinkOrderTargeter`: (no class-level Desc)
- `Traits/MissileSpawnerSlave.cs` — `MissileSpawnerSlave`: This unit is "slaved" to a missile spawner master.; `MissileSpawnerSlave`: This unit is "slaved" to a missile spawner master.
- `Traits/Modifiers/WithColoredOverlayCA.cs` — `WithColoredOverlayCA`: Display a colored overlay when a timed condition is active. Supports preview rendering.; `WithColoredOverlayCA`: Whether to show this overlay in actor previews (encyclopedia, tooltips, etc).; `WithColoredOverlayPreviewModifier`: Whether to show this overlay in actor previews (encyclopedia, tooltips, etc).
- `Traits/Multipliers/FlatHealthDamageMultiplier.cs` — `FlatHealthDamageMultiplier`: Modifies the damage taken by the actor to emulate a specified amount of additional health.; `FlatHealthDamageMultiplier`: Extra health to emulate.
- `Traits/Multipliers/HealthCapDamageMultiplier.cs` — `HealthCapDamageMultiplier`: Modifies the damage taken by the actor to emulate specified maximum health.; `HealthCapDamageMultiplier`: Maximum health to emulate.
- `Traits/Multipliers/SeedsResourceMultiplier.cs` — `SeedsResourceMultiplier`: Modifies the interval between seeding resources.; `SeedsResourceMultiplier`: Percentage modifier to apply.
- `Traits/Multipliers/SpeedCapSpeedMultiplier.cs` — `SpeedCapSpeedMultiplier`: Modifies the speed of an actor to emulate specified maximum speed.; `SpeedCapSpeedMultiplier`: Maximum speed to emulate.
- `Traits/Multipliers/ValueScalingFirepowerMultiplier.cs` — `ValueScalingFirepowerMultiplier`: Modifies the firepower of a given actor according to its value.; `ValueScalingFirepowerMultiplier`: Firepower multiplier applied at the maximum value.
- `Traits/NotificationOnDamage.cs` — `NotificationOnDamage`: Plays an audio notification and shows a radar ping when actor is damaged.; `NotificationOnDamage`: Text notification to display.
- `Traits/PaletteEffects/WeatherPaletteEffect.cs` — `WeatherPaletteEffect`: Global palette effect with a fixed color.; `WeatherPaletteEffect`: Set this when using multiple independent flash effects.
- `Traits/Palettes/EncyclopediaColorPalette.cs` — `EncyclopediaColorPalette`: Create an encyclopedia preview palette that can be dynamically updated with arbitrary colors.; `EncyclopediaColorPalette`: Default color to use.
- `Traits/Palettes/OverlayColorPickerPalette.cs` — `OverlayColorPickerPalette`: Create a color picker palette from another palette, using the overlay blend mode which increases contrast.; `OverlayColorPickerPalette`: Lowers brightness range.
- `Traits/PassengerBlocked.cs` — `PassengerBlocked`: Attach to a transport to override the unload order.; `PassengerBlocked`: Cursor to display when hovering over the transport.; `PassengerBlockedOrderTargeter`: Cursor to display when hovering over the transport.
- `Traits/PeriodicExplosion.cs` — `PeriodicExplosion`: Explodes a weapon at the actor's position when enabled. Reload/BurstDelays are used as explosion intervals.; `PeriodicExplosion`: If true, will apply firepower/reload modifiers.
- `Traits/PeriodicExplosionOnSlaves.cs` — `PeriodicExplosionOnSlaves`: Explodes a weapon at the actor's position when enabled. Reload/BurstDelays are used as explosion intervals.; `PeriodicExplosionOnSlaves`: What happens to surviving slaves after the explosion?
- `Traits/Player/AutoDeployManager.cs` — `AutoDeployManager`: Allows the player to issue the orders the AutoDeployer traits trigger.; `AutoDeployManager`: Allows the player to issue the orders the AutoDeployer traits trigger.
- `Traits/Player/CampaignProgressTracker.cs` — `CampaignProgressTracker`: Stores campaign progress.; `CampaignProgressTracker`: Stores campaign progress.; `MissionVictoryResult`: (no class-level Desc)
- `Traits/Player/ClassicProductionQueueCA.cs` — `ClassicProductionQueueCA`: Attach this to the player actor (not a building!) to define a new shared build queue. Will only work together with the Production: trait on the actor that actually does the production. You will also want to add PrimaryBuildings: to let the user choose where new units should exit. CA version allows build speed reduction to take into account all buildings for a type if BuildAtProductionType is set, and allows excluding certain types from that calculation.; `ClassicProductionQueueCA`: If true, ignore BuildAtProductionType when calculating build duration, so all structures for this queue are counted.
- `Traits/Player/CountManager.cs` — `CountManager`: Allows arbitrary counts.; `CountManager`: Maximum count for specific count types.
- `Traits/Player/NotificationManager.cs` — `NotificationManager`: Tracks last notification times.; `NotificationManager`: Tracks last notification times.
- `Traits/Player/PlayerBountyPool.cs` — `PlayerBountyPool`: Tracks and provides access to player bounty pool.; `PlayerBountyPool`: Tracks and provides access to player bounty pool.
- `Traits/Player/PlayerConnectionStatus.cs` — `PlayerConnectionStatus`: Tracks player connection status.; `PlayerConnectionStatus`: Tracks player connection status.
- `Traits/Player/PlayerExperienceLevels.cs` — `PlayerExperienceLevels`: Tracks player experience and sets grants prerequisites based on it.; `PlayerExperienceLevels`: Actor to spawn when player levels up.
- `Traits/Player/PopController.cs` — `PopController`: Works with PopControlled trait on actors to cull excess instances.; `PopController`: Limits by type.
- `Traits/Player/ProductionTracker.cs` — `ProductionTracker`: Keeps track of player's initial build order and units produced for observer stats.; `ProductionTracker`: Maximum number of build order items to track.; `ProductionTrackerBuildOrderItem`: Maximum number of build order items to track.; `ProductionTrackerUnitValueItem`: Maximum number of build order items to track.
- `Traits/Player/ProvidesPrerequisiteIfAlliesExist.cs` — `ProvidesPrerequisiteIfAlliesExist`: Provides a prerequisite if one or more allies exist.; `ProvidesPrerequisiteIfAlliesExist`: Minimum number of allies required to provide the prerequisite.
- `Traits/Player/ProvidesPrerequisitesOnCount.cs` — `ProvidesPrerequisitesOnCount`: (no class-level Desc); `ProvidesPrerequisitesOnCount`: If true, adds the to the observer Upgrades tab.
- `Traits/Player/ProvidesPrerequisitesOnTimeline.cs` — `ProvidesPrerequisitesOnTimeline`: (no class-level Desc); `ProvidesPrerequisitesOnTimeline`: Sound notification to play when count is incremented.
- `Traits/Player/ReclaimableExperiencePool.cs` — `ReclaimableExperiencePool`: A pool of experience that can be added to and taken from.; `ReclaimableExperiencePool`: Percentage modifier to apply when adding XP to the pool.
- `Traits/Player/ReclaimableValueProducer.cs` — `ReclaimableValueProducer`: Produces actors when enough reclaimable value is accumulated for the specified type.; `ReclaimableValueProducer`: Production type to use
- `Traits/Player/StackableSupportPowerManager.cs` — `StackableSupportPowerManager`: Tracks independent stack cooldowns for stackable support powers.; `StackableSupportPowerDefinition`: Tracks independent stack cooldowns for stackable support powers.; `StackableSupportPowerStack`: Tracks independent stack cooldowns for stackable support powers.; `StackableSupportPowerState`: Tracks independent stack cooldowns for stackable support powers.; `StackableSupportPowerManager`: Tracks independent stack cooldowns for stackable support powers.
- `Traits/Player/SupportPowerInstanceManager.cs` — `SupportPowerInstanceManager`: For storing global support power properties e.g. to limit the number of times timers are modified.; `SupportPowerInstanceManager`: For storing global support power properties e.g. to limit the number of times timers are modified.
- `Traits/Player/TeleportNetworkManager.cs` — `TeleportNetworkManager`: This must be attached to player in order for TeleportNetwork to work.; `TeleportNetworkManager`: If true, on entering the network a random exit is used.
- `Traits/Player/UpgradesManager.cs` — `UpgradesManager`: Manages unit upgrades.; `UpgradesManager`: Manages unit upgrades.; `Upgrade`: (no class-level Desc)
- `Traits/PointDefense.cs` — `PointDefense`: This actor can destroy weaponry.; `PointDefense`: What diplomatic stances are affected.
- `Traits/ProvidesUpgrade.cs` — `ProvidesUpgrade`: Provides a prerequisite that is used for upgrades.; `ProvidesUpgrade`: Type.
- `Traits/RangedGpsRadarProvider.cs` — `RangedGpsRadarProvider`: This actor provides Radar GPS.; `RangedGpsRadarProvider`: The maximum vertical range above terrain to search for actors. Ignored if 0 (actors are selected regardless of vertical distance).
- `Traits/RearmsToUpgrade.cs` — `RearmsToUpgrade`: Use in conjunction with Rearmable and an AmmoPool with large reload delay. Replaces with specified unit after a delay (optionally if the unit is also undamaged).; `RearmsToUpgrade`: If true, the unit must be at full health before triggering the upgrade process.
- `Traits/ReclaimsExperience.cs` — `ReclaimsExperience`: When killed, gives to a reclaimable pool. When created takes from that pool.; `ReclaimsExperience`: When true, only adds to the pool on death, doesn't reclaim on creation.
- `Traits/Render/RenderLine.cs` — `RenderLine`: .; `RenderLine`: If true, fade in as well as out.
- `Traits/Render/TimedConditionBarCA.cs` — `TimedConditionBarCA`: Visualizes the remaining time for a condition. CA version is conditional and allows relationship to be specified.; `TimedConditionBarCA`: Relationships that can see the bar.
- `Traits/Render/TriggersProductionDoorOverlay.cs` — `TriggersProductionDoorOverlay`: Play production door animation on allied building when unit is produced.; `TriggersProductionDoorOverlay`: Play production door animation on allied building when unit is produced.
- `Traits/Render/WithDistortionHalo.cs` — `WithDistortionHalo`: Renders a distorted halo of animated arc segments around the actor.; `WithDistortionHalo`: When to show the halo. Valid values are `Always`, and `WhenSelected`
- `Traits/Render/WithDockingAnimationCA.cs` — `WithDockingAnimationCA`: (no class-level Desc); `WithDockingAnimationCA`: Valid refinery types at which to play the animation.
- `Traits/Render/WithEnterExitWorldOverlay.cs` — `WithEnterExitWorldOverlay`: Draws an overlay on top of a make animation.; `WithEnterExitWorldOverlay`: Custom palette is a player palette BaseName.
- `Traits/Render/WithFlashEffect.cs` — `WithFlashEffect`: Flashes the target at a set interval.; `WithFlashEffect`: Flash color.
- `Traits/Render/WithHarvestAnimationCA.cs` — `WithHarvestAnimationCA`: CA version fixes jerky turning caused by fewer harvest facings than normal facings.; `WithHarvestAnimationCA`: Which sprite body to play the animation on.
- `Traits/Render/WithLinkedRangeCirclePreview.cs` — `WithLinkedRangeCirclePreview`: Shows matching range circles from existing actors while placing a structure.; `WithLinkedRangeCirclePreview`: Type of linked range circle to render from existing actors.
- `Traits/Render/WithMindControlArc.cs` — `WithMindControlArc`: (no class-level Desc); `WithMindControlArc`: Brightness-only multiplier for the glow halo, independent of GlowScale (does not grow the radius).
- `Traits/Render/WithPreviewDecoration.cs` — `WithPreviewDecoration`: Displays a custom UI overlay relative to the actor's mouseover bounds. Also renders on actor previews.; `WithPreviewDecoration`: Displays a custom UI overlay relative to the actor's mouseover bounds. Also renders on actor previews.; `WithPreviewDecorationPreviewModifier`: Displays a custom UI overlay relative to the actor's mouseover bounds. Also renders on actor previews.
- `Traits/Render/WithPrismChargeAnimation.cs` — `WithPrismChargeAnimation`: This actor displays a charge-up animation before firing.; `WithPrismChargeAnimation`: Which sprite body to play the animation on.
- `Traits/Render/WithPrismLinkVisualization.cs` — `WithPrismLinkVisualization`: Renders selection boxes on Prism Towers within range.; `WithPrismLinkVisualization`: Range of the circle; `PrismLinkVisualizationRenderer`: (no class-level Desc)
- `Traits/Render/WithRadiatingCircle.cs` — `WithRadiatingCircle`: Radiating circle overlay with an optional outer circle.; `WithRadiatingCircle`: When to show the range circle. Valid values are `Always`, and `WhenSelected`
- `Traits/Render/WithSpawnedActorIdentifier.cs` — `WithSpawnedActorIdentifier`: Draws a marker around actors tracked by SpawnActorAbility while selected.; `WithSpawnedActorIdentifier`: The alpha value [from 0 to 255] used when UsePlayerColor is enabled.; `RectangleAnnotationRenderable`: (no class-level Desc)
- `Traits/Render/WithSpawnerMasterPipsDecoration.cs` — `WithSpawnerMasterPipsDecoration`: (no class-level Desc); `WithSpawnerMasterPipsDecoration`: Sequence used for lost spawnees.
- `Traits/Render/WithUnitConverterCountDecoration.cs` — `WithUnitConverterCountDecoration`: Displays a text overlay relative to the selection box.; `WithUnitConverterCountDecoration`: Use the player color of the current owner.
- `Traits/ReturnsToBaseOnAmmoDepleted.cs` — `ReturnsToBaseOnAmmoDepleted`: For aircraft with a Strafe AttackType, which don't return to base due to using an AttackMove.; `ReturnsToBaseOnAmmoDepleted`: Name(s) of AmmoPool(s) that are checked.
- `Traits/ScatterOnExitCargo.cs` — `ScatterOnExitCargo`: When exiting a transport the actor will scatter.; `ScatterOnExitCargo`: Only scatter if the cargo is dead.
- `Traits/SeedsResourceCA.cs` — `SeedsResourceCA`: Lets the actor spread resources around it in a circle.; `SeedsResourceCA`: Lets the actor spread resources around it in a circle.
- `Traits/Shielded.cs` — `Shielded`: Grants a shield with its own health pool. Main health pool is unaffected by damage until the shield is broken.; `Shielded`: Hides selection bar when shield is at max strength.
- `Traits/Sound/SoundOnDamageTransitionCA.cs` — `SoundOnDamageTransitionCA`: (no class-level Desc); `SoundOnDamageTransitionCA`: DamageType(s) that trigger the sounds. Leave empty to always trigger a sound.
- `Traits/Sound/WithCargoSounds.cs` — `WithCargoSounds`: (no class-level Desc); `WithCargoSounds`: Volume the EnterSounds and ExitSounds played at.
- `Traits/SpawnActorAbility.cs` — `SpawnActorAbility`: Actor can deploy to be able to target a location and spawn an actor there.; `SpawnActorAbility`: Avoid actors.; `SpawnActorAbilityOrderGenerator`: (no class-level Desc)
- `Traits/SpawnActorOnDeathCA.cs` — `SpawnActorOnDeathCA`: Spawn another actor immediately upon death. CA version can add spawned actor to selection and/or control group.; `SpawnActorOnDeathCA`: Should the spawned actor inhert experience from the killed actor.
- `Traits/SpawnActorOnMindControlled.cs` — `SpawnActorOnMindControlled`: Spawn another actor immediately upon being mind controlled.; `SpawnActorOnMindControlled`: Should an actor spawn after the player has been defeated (e.g. after surrendering)?
- `Traits/SpawnActorsOnSellCA.cs` — `SpawnActorsOnSellCA`: Spawn new actors when sold.; `SpawnActorsOnSellCA`: If true, the actors defined by GuaranteedActorTypes will not spawn if there isn't enough value.
- `Traits/SpawnerMasterBase.cs` — `SpawnerSlaveBaseEntry`: (no class-level Desc); `SpawnerMasterBase`: This actor can spawn actors.; `SpawnerMasterBase`: Spawn regen delay, in ticks
- `Traits/SpawnerSlaveBase.cs` — `SpawnerSlaveBase`: Can be slaved to a SpawnerMaster.; `SpawnerSlaveBase`: The condition to grant when the master trait is paused.
- `Traits/SpawnHuskEffectOnDeath.cs` — `SpawnHuskEffectOnDeath`: Spawn projectile as husk upon death.; `SpawnHuskEffectOnDeath`: Pass current actor speed as RangeModifier to husk weapon. Only supports aircraft for now.
- `Traits/SquadPathOverlay.cs` — `SquadPathOverlay`: Renders a debug overlay showing the pathfinding routes of AI squads. Attach this to the world actor.; `SquadPathOverlay`: Renders a debug overlay showing the pathfinding routes of AI squads. Attach this to the world actor.
- `Traits/StoresPlayerResourcesCA.cs` — `StoresPlayerResourcesCA`: Adds capacity to a player's harvested resource limit.; `StoresPlayerResourcesCA`: Adds capacity to a player's harvested resource limit.
- `Traits/SupportPowers/AirReinforcementsPower.cs` — `AirReinforcementsPower`: (no class-level Desc); `AirReinforcementsPower`: Weapon range offset to apply during the beacon clock calculation
- `Traits/SupportPowers/AirstrikePowerCA.cs` — `AirstrikePowerCA`: Copy of AirstrikePowerCA but has MinDistance instead of Cordon.; `AirstrikePowerCA`: Overrides UnitType based on prerequsites being met. If multiple are met, the first is used. Keys can either be a single prerequisite or be a key of PrerequisiteGroupings.
- `Traits/SupportPowers/AttackOrderPowerCA.cs` — `AttackOrderPowerCA`: Copy of AttackOrderPower but allows target radius indicator.; `AttackOrderPowerCA`: Amount of time after detonation to remove the camera.; `SelectAttackOrderPowerCATarget`: (no class-level Desc)
- `Traits/SupportPowers/CashHackPower.cs` — `CashHackPower`: (no class-level Desc); `CashHackPower`: Whether to show the cash tick indicators rising from the actor.; `SelectHackTarget`: (no class-level Desc)
- `Traits/SupportPowers/ChronoshiftPowerCA.cs` — `ChronoshiftPowerCA`: (no class-level Desc); `ChronoshiftPowerCA`: Target tint colour.; `SelectChronoshiftTarget`: (no class-level Desc); `SelectDestination`: (no class-level Desc)
- `Traits/SupportPowers/ClassicAirstrikePower.cs` — `ClassicAirstrikePowerSquadMember`: (no class-level Desc); `ClassicAirstrikePower`: (no class-level Desc); `ClassicAirstrikePower`: How long to allow idling in the circle phase between strikes.
- `Traits/SupportPowers/DetonateWeaponPower.cs` — `DetonateWeaponPower`: Support power for detonating a weapon at the target position.; `DetonateWeaponPower`: If true, target must be within build range of a base provider.; `SelectDetonateWeaponPowerTarget`: (no class-level Desc)
- `Traits/SupportPowers/DropPodsPowerCA.cs` — `DropPodsPowerCA`: (no class-level Desc); `DropPodsPowerCA`: Apply the weapon impact this many ticks into the effect
- `Traits/SupportPowers/DummyGpsPower.cs` — `DummyGpsPower`: (no class-level Desc); `DummyGpsPower`: The condition to apply. Must be included in the target actor's ExternalConditions list.
- `Traits/SupportPowers/GpsRadarProvider.cs` — `GpsRadarProvider`: This actor provides Radar GPS.; `GpsRadarProvider`: This actor provides Radar GPS.
- `Traits/SupportPowers/GrantPrerequisiteChargeDrainPowerCA.cs` — `GrantPrerequisiteChargeDrainPowerCA`: Grants a prerequisite while discharging at a configurable rate. CA version adds early deactivation penalty to prevent frequent toggling.; `GrantPrerequisiteChargeDrainPowerCA`: If deactivating the power prior to full discharge, discharge by this additional amount to prevent frequent activation/deactivation with no penalty.; `DischargeableSupportPowerInstance`: If deactivating the power prior to full discharge, discharge by this additional amount to prevent frequent activation/deactivation with no penalty.
- `Traits/SupportPowers/InfiltratePower.cs` — `InfiltratePower`: Acts like infiltrating a targeted structure.; `InfiltratePower`: Should visibility (Shroud, Fog, Cloak, etc) be considered when searching for targets?; `SelectInfiltrateTarget`: (no class-level Desc)
- `Traits/SupportPowers/InterceptorPower.cs` — `InterceptorPower`: (no class-level Desc); `InterceptorPower`: Weapon range offset to apply during the beacon clock calculation
- `Traits/SupportPowers/MeteorPower.cs` — `MeteorPower`: (no class-level Desc); `MeteorPower`: Render circles based on these distance ranges while targeting.; `SelectMeteorPowerTarget`: (no class-level Desc)
- `Traits/SupportPowers/MissileStrikePower.cs` — `MissileStrikePower`: (no class-level Desc); `MissileStrikePower`: Target selection radius.; `SelectMissileStrikeTarget`: (no class-level Desc)
- `Traits/SupportPowers/ParatroopersPowerCA.cs` — `ParatroopersPowerCA`: Support power that delivers paratroopers. CA version adds overrides based on prerequisites.; `ParatroopersPowerCA`: Overrides DropItems based on prerequsites being met. If multiple are met, the first is used. Keys can either be a single prerequisite or be a key of PrerequisiteGroupings.
- `Traits/SupportPowers/ProduceActorPowerCA.cs` — `PrimaryExts`: (no class-level Desc); `ProduceActorPowerCA`: Produces an actor without using the standard production queue. CA version allows actors to be produced immediately when charged. Also removes sorting of the producing actor as this can cause a crash when multiple exist.; `ProduceActorPowerCA`: If true, producer must be selected, otherwise chosen automatically.; `SelectProductionTarget`: (no class-level Desc)
- `Traits/SupportPowers/RecallPower.cs` — `RecallPower`: (no class-level Desc); `RecallPower`: Warp to sequence.; `SelectRecallTarget`: (no class-level Desc)
- `Traits/SupportPowers/RemoveOnPowerActivation.cs` — `RemoveOnPowerActivation`: Removes actors when support power is activated.; `RemoveOnPowerActivation`: Remove the actor triggering the support power on activation.
- `Traits/SupportPowers/RevealActorsPower.cs` — `RevealActorsPower`: Spawns camera actors at the location of specified actor types that stay for a limited amount of time.; `RevealActorsPower`: Amount of time to keep the actor alive in ticks. Value < 0 means this actor will not remove itself.
- `Traits/SupportPowers/SelectDirectionalTargetWithCircle.cs` — `SelectDirectionalTargetWithCircle`: (no class-level Desc)
- `Traits/SupportPowers/SendCashPower.cs` — `SendCashPower`: Transfers money to the owner of the targeted actor.; `SendCashPower`: Text notification to display when the player does not have any funds.; `SelectSendCashTarget`: (no class-level Desc)
- `Traits/SupportPowers/SpawnActorPowerCA.cs` — `SpawnActorPowerCA`: Spawns an actor that stays for a limited amount of time. CA version extends the base version, adding a target circle.; `SpawnActorPowerCA`: Beacon duration.; `SelectSpawnActorPowerCATarget`: (no class-level Desc)
- `Traits/SupportPowers/StackableDirectionalSupportPower.cs` — `StackableDirectionalSupportPower`: Paratroopers support power with independent cooldown stacks granted by other actors.; `StackableDirectionalSupportPower`: Number of stacks granted by this actor.
- `Traits/SupportPowers/StackableSupportPowerInstance.cs` — `StackableSupportPowerInstance`: (no class-level Desc)
- `Traits/SupportPowers/SupportPowerInstanceCA.cs` — `SupportPowerInstanceCA`: (no class-level Desc)
- `Traits/TargetedDiveAbility.cs` — `TargetedDiveAbility`: Allows unit to dive to a targeted location.; `TargetedDiveAbility`: Actor to transform into when the dive is complete.
- `Traits/TargetedLeapAbility.cs` — `TargetedLeapAbility`: Allows unit to leap to a targeted location.; `TargetedLeapAbility`: The condition to grant while leaping.
- `Traits/TargetedMovementAbility.cs` — `TargetedMovementAbility`: Allows unit to leap to a targeted location.; `TargetedMovementAbility`: Cursor to display when targeting a teleport location with modifier key held.; `TargetedMovementOrderTargeter`: (no class-level Desc); `TargetedMovementOrderGenerator`: (no class-level Desc)
- `Traits/TargetSpecificOrderVoice.cs` — `TargetSpecificOrderVoice`: Lists valid factions for ProvidesPrerequisiteValidatedFaction.; `TargetSpecificOrderVoice`: Voice line to use if no target type is matched.
- `Traits/TeleportNetwork.cs` — `TeleportNetworkExts`: (no class-level Desc); `TeleportNetwork`: This actor can teleport actors to another actor with the same trait.; `TeleportNetwork`: Time in ticks to wait for the teleporter to charge up.
- `Traits/TeleportNetworkPrimaryExit.cs` — `TeleportNetworkPrimaryExitExts`: (no class-level Desc); `TeleportNetworkPrimaryExit`: Used with TeleportNetwork trait for primary exit designation.; `TeleportNetworkPrimaryExit`: Cursor to display when setting primary exit.
- `Traits/TeleportNetworkTransportable.cs` — `TeleportNetworkTransportable`: Can move actors instantly to primary designated teleport network canal actor.; `TeleportNetworkTransportable`: Can move actors instantly to primary designated teleport network canal actor.; `TeleportNetworkTransportOrderTargeter`: (no class-level Desc)
- `Traits/TransferResourcesOnTransform.cs` — `TransferResourcesOnTransform`: (no class-level Desc); `TransferResourcesOnTransform`: (no class-level Desc)
- `Traits/TurretedFloating.cs` — `TurretedFloating`: Turret for where the unit is able to move instantly in any direction, to make the turret unaffected by changes in body facing.; `TurretedFloating`: Turret for where the unit is able to move instantly in any direction, to make the turret unaffected by changes in body facing.
- `Traits/UndeployOnStop.cs` — `UndeployOnStop`: (no class-level Desc); `UndeployOnStop`: (no class-level Desc)
- `Traits/UnitConverter.cs` — `UnitConverter`: Allow convertible units to enter and spawn a new actor or actors.; `UnitConverter`: Converting condition.; `UnitConverterQueueItem`: (no class-level Desc)
- `Traits/UpdatesBuildOrder.cs` — `UpdatesBuildOrder`: Added to build order when the actor is created.; `UpdatesBuildOrder`: If true, ignores the maximum.
- `Traits/UpdatesCount.cs` — `UpdatesCount`: Updates a counter when the actor is created/disposed or changes owner.; `UpdatesCount`: Relationships that a killing/capturing/damaging/infiltrating player must have to update the count. No effect on Owned.
- `Traits/UpdatesSupportPowerTimer.cs` — `UpdatesSupportPowerTimer`: When trait is enabled the named support power will have its timer updated.; `UpdatesSupportPowerTimer`: If set to true, the support power timer will be updated the first time it becomes available.  Otherwise it will be updated every time the trait is enabled.
- `Traits/UpdatesUnitsProduced.cs` — `UpdatesUnitsProduced`: Attach to producer actors. Updates units produced.; `UpdatesUnitsProduced`: Attach to producer actors. Updates units produced.
- `Traits/Upgradeable.cs` — `Upgradeable`: Lists actors this actor may be upgraded to.; `Upgradeable`: Cursor to display when unable to be upgraded near target actor.
- `Traits/WaitsForTurretAlignmentOnUndeploy.cs` — `WaitsForTurretAlignmentOnUndeploy`: .; `WaitsForTurretAlignmentOnUndeploy`: Condition to grant while aligning turrets.
- `Traits/WarheadDebugOverlayCA.cs` — `WarheadDebugOverlayCA`: Enhanced version of WarheadDebugOverlay that supports custom shapes. Attach this to the world actor.; `WarheadDebugOverlayCA`: Enhanced version of WarheadDebugOverlay that supports custom shapes. Attach this to the world actor.; `WHImpact`: Enhanced version of WarheadDebugOverlay that supports custom shapes. Attach this to the world actor.; `WHPoylineImpact`: Enhanced version of WarheadDebugOverlay that supports custom shapes. Attach this to the world actor.
- `Traits/WithEjectedCasings.cs` — `WithEjectedCasings`: Ejects casings when the actor fires weapons. Supports burst firing of casings over time using the casing weapon's Burst and BurstDelays properties, or the BurstOverride and BurstDelayOverride trait properties for custom control.; `WithEjectedCasings`: Override the casing weapon's burst delays. If empty, uses the weapon's own burst delays.
- `Traits/WithReloadBar.cs` — `WithReloadBar`: .; `WithReloadBar`: Armament to track reload of.
- `Traits/World/AllyProxyFromSelection.cs` — `AllyProxyFromSelection`: Automatically adds proxy actors to selection when their parent ally building is selected. This enables standard traits like RallyPoint on proxy actors to work when ally buildings are selected.; `AllyProxyFromSelection`: Automatically adds proxy actors to selection when their parent ally building is selected. This enables standard traits like RallyPoint on proxy actors to work when ally buildings are selected.
- `Traits/World/LobbyMissionInfo.cs` — `LobbyMissionInfo`: Displays additional info in the lobby chat after a map is selected. Requires LobbyMissionInfoLogic widget logic.; `LobbyMission`: Color of the info text in the lobby chat.
- `Traits/World/TintedCellsLayer.cs` — `TintedCellsLayer`: Has to be attached to world actor. ; `TintedCellsLayer`: How shall level decay, can be Linear or Logarithmic.
- `Warheads/AttachActorWarhead.cs` — `AttachActorWarhead`: This warhead can attach an actor to the target.
- `Warheads/AttachDelayedWeaponWarhead.cs` — `AttachDelayedWeaponWarhead`: This warhead can attach a DelayedWeapon to the target. Requires an appropriate type of DelayedWeaponAttachable trait to function properly.
- `Warheads/ChangeOwnerToNeutralWarhead.cs` — `ChangeOwnerToNeutralWarhead`: Changes targets to neutral.
- `Warheads/ChronoFlashEffectWarhead .cs` — `ChronoFlashEffectWarhead`: This warhead activates the global flash effect when detonated.
- `Warheads/CreateDistortionHaloWarhead.cs` — `CreateDistortionHaloWarhead`: Creates a temporary distorted halo of animated arc segments at the impact position. Purely visual, no damage.
- `Warheads/CreateFacingEffectWarhead.cs` — `CreateFacingEffectWarhead`: Spawn a sprite with sound. Identical to CreateEffectWarhead except it supports sprites with facings.
- `Warheads/CreateTintedCellsWarhead.cs` — `CreateTintedCellsWarhead`: (no class-level Desc)
- `Warheads/DetatchDelayedWeaponWarhead.cs` — `DetachDelayedWeaponWarhead`: This warhead can detach a DelayedWeapon from the target. Requires an appropriate type of DelayedWeaponAttachable trait to function properly.
- `Warheads/FireClusterCAWarhead.cs` — `FireClusterCAWarhead`: Fires weapons from the point of impact.
- `Warheads/FireFragmentWarhead.cs` — `FireFragmentWarhead`: Allows to fire a a weapon to a directly specified target position relative to the warhead explosion.
- `Warheads/FireRadiusWarhead.cs` — `FireRadiusWarhead`: Fires a defined amount of weapons with their maximum range in a wave pattern.
- `Warheads/FireShrapnelWarhead.cs` — `FireShrapnelWarhead`: (no class-level Desc)
- `Warheads/FlashTargetWarhead.cs` — `FlashTargetWarhead`: Flashes the target.
- `Warheads/GlowImpactWarhead.cs` — `GlowImpactWarhead`: Registers a screen-space glow flash at the impact position. Purely visual, no damage.
- `Warheads/GrantExternalConditionCAWarhead.cs` — `GrantExternalConditionCAWarhead`: Grant an external condition to hit actors.
- `Warheads/HealthPercentageSpreadDamageWarhead.cs` — `HealthPercentageSpreadDamageWarhead`: Apply damage in a specified range.
- `Warheads/HeatDistortionWarhead.cs` — `HeatDistortionWarhead`: Registers a screen-space heat-haze distortion at the impact position. Purely visual, no damage.
- `Warheads/InfiltrateWarhead.cs` — `InfiltrateWarhead`: Does nothing.
- `Warheads/RevealShroudWarhead.cs` — `RevealShroudWarhead`: (no class-level Desc)
- `Warheads/SendAirstrikeWarhead.cs` — `SendAirstrikeWarhead`: This warhead sends an airstrike.
- `Warheads/ShockwaveWarhead.cs` — `ShockwaveWarhead`: Registers a screen-space shockwave-lens distortion at the impact position. Purely visual, no damage.
- `Warheads/SpawnActorWarhead.cs` — `SpawnActorWarhead`: Spawn actors upon explosion. Don't use this with buildings.
- `Warheads/SpawnBuildingWarhead.cs` — `SpawnBuildingWarhead`: Spawn buildings upon explosion.
- `Warheads/SpawnMultiWeaponImpactWarhead.cs` — `SpawnMultiWeaponImpactWarhead`: (no class-level Desc)
- `Warheads/SpawnRandomActorWarhead.cs` — `SpawnRandomActorWarhead`: Spawn actors upon explosion. Don't use this with buildings.
- `Warheads/WarheadAS.cs` — `WarheadAS`: AS warhead extension class. These warheads check for the Air TargetType when detonated inair!
- `Warheads/WarpPercentDamageWarhead.cs` — `WarpPercentDamageWarhead`: Affects warp value on the actors with Warpable trait.
- `Widgets/ActorPreviewCAWidget.cs` — `ActorPreviewCAWidget`: (no class-level Desc)
- `Widgets/ColoredRectangleWidget.cs` — `ColoredRectangleWidget`: (no class-level Desc)
- `Widgets/CroppableImageWidget.cs` — `CroppableImageWidget`: (no class-level Desc)
- `Widgets/ImageWithAlphaWidget.cs` — `ImageWithAlphaWidget`: (no class-level Desc)
- `Widgets/LinkableLabelWidget.cs` — `LinkableLabelWidget`: (no class-level Desc)
- `Widgets/Logic/EncyclopediaLogicCA.cs` — `EncyclopediaLogicCA`: (no class-level Desc); `to`: (no class-level Desc); `FolderNode`: (no class-level Desc)
- `Widgets/Logic/Ingame/AlliedInfluenceIndicatorLogic.cs` — `AlliedInfluenceIndicatorLogic`: (no class-level Desc)
- `Widgets/Logic/Ingame/ArmyTooltipLogicCA.cs` — `ArmyTooltipLogicCA`: (no class-level Desc)
- `Widgets/Logic/Ingame/ArmyValueTooltipLogic.cs` — `ArmyValueTooltipLogic`: (no class-level Desc)
- `Widgets/Logic/Ingame/GameInfoLogicCA.cs` — `GameInfoLogicCA`: (no class-level Desc)
- `Widgets/Logic/Ingame/GameInfoStatsLogicCA.cs` — `GameInfoStatsLogicCA`: (no class-level Desc)
- `Widgets/Logic/Ingame/GDIStrategyIndicatorLogic.cs` — `GDIStrategyIndicatorLogic`: (no class-level Desc)
- `Widgets/Logic/Ingame/IngameMenuLogicCA.cs` — `IngameMenuLogicCA`: (no class-level Desc)
- `Widgets/Logic/Ingame/NextMissionInfoLogicCA.cs` — `NextMissionInfoLogicCA`: (no class-level Desc)
- `Widgets/Logic/Ingame/NodCovenantIndicatorLogic.cs` — `NodCovenantIndicatorLogic`: (no class-level Desc)
- `Widgets/Logic/Ingame/ObserverStatsLogicCA.cs` — `ObserverStatsLogicCA`: (no class-level Desc); `StatsDropDownOption`: (no class-level Desc)
- `Widgets/Logic/Ingame/PlayerExperienceLevelIndicatorLogic.cs` — `PlayerExperienceLevelIndicatorLogic`: (no class-level Desc)
- `Widgets/Logic/Ingame/ProductionTooltipLogicCA.cs` — `ProductionTooltipLogicCA`: (no class-level Desc)
- `Widgets/Logic/Ingame/ReplayControlBarLogicCA.cs` — `ReplayControlBarLogicCA`: (no class-level Desc)
- `Widgets/Logic/Ingame/ScrinAllegianceIndicatorLogic.cs` — `ScrinAllegianceIndicatorLogic`: (no class-level Desc)
- `Widgets/Logic/Ingame/SelectionTooltipLogic.cs` — `SelectionTooltipLogic`: (no class-level Desc)
- `Widgets/Logic/Ingame/SupportPowerBinLogicCA.cs` — `SupportPowerBinLogicCA`: (no class-level Desc)
- `Widgets/Logic/Ingame/SupportPowerTooltipLogicCA.cs` — `SupportPowerTooltipLogicCA`: (no class-level Desc)
- `Widgets/Logic/Ingame/UpgradeOrderButtonLogic.cs` — `UpgradeOrderButtonLogic`: (no class-level Desc)
- `Widgets/Logic/Lobby/LobbyMissionInfoLogic.cs` — `LobbyMissionInfoLogic`: (no class-level Desc)
- `Widgets/Logic/MainMenuLogicCA.cs` — `MainMenuLogicCA`: (no class-level Desc); `NewsItem`: (no class-level Desc)
- `Widgets/Logic/MenuNotificationsLogic.cs` — `MenuNotificationsLogic`: (no class-level Desc); `VersionCheck`: (no class-level Desc); `Release`: (no class-level Desc); `NotificationsData`: (no class-level Desc); `Notification`: (no class-level Desc)
- `Widgets/Logic/MissionBrowserLogicCA.cs` — `MissionBrowserLogicCA`: (no class-level Desc)
- `Widgets/ObserverArmyValuesWidget.cs` — `ObserverArmyValuesWidget`: (no class-level Desc); `ArmyValue`: (no class-level Desc)
- `Widgets/ObserverBuildOrderIconsWidget.cs` — `ObserverBuildOrderIconsWidget`: (no class-level Desc); `ArmyIcon`: (no class-level Desc)
- `Widgets/ObserverSupportPowerIconsCAWidget.cs` — `ObserverSupportPowerIconsCAWidget`: (no class-level Desc)
- `Widgets/ObserverUnitsProducedIconsWidget.cs` — `ObserverUnitsProducedIconsWidget`: (no class-level Desc); `UnitProduced`: (no class-level Desc); `ArmyIcon`: (no class-level Desc)
- `Widgets/ObserverUpgradeIconsWidget.cs` — `ObserverUpgradeIconsWidget`: (no class-level Desc); `ArmyIcon`: (no class-level Desc)
- `Widgets/ScrollableLineGraphWidget.cs` — `ScrollableLineGraphWidget`: (no class-level Desc); `ScrollableLineGraphSeries`: (no class-level Desc)
- `Widgets/SupportPowersScrollableWidget.cs` — `SupportPowersScrollableWidget`: (no class-level Desc)
- `Widgets/WidgetUtilsCA.cs` — `WidgetUtilsCA`: (no class-level Desc)

## Four priority modules

### `UnitCompositionsBotModule.cs`

- Local: `OpenRA.Mods.CA/Traits/BotModules/UnitCompositionsBotModule.cs`
- Upstream: `OpenRA.Mods.CA/Traits/BotModules/UnitCompositionsBotModule.cs`
- Status: **DIVERGED**
- Cameo consumers:
  - None outside the implementation file.
- Upstream consumers:
  - `mods/ca/rules/ai.yaml:2733` — `UnitCompositionsBotModule:`
  - `OpenRA.Mods.CA/Traits/BotModules/UnitBuilderBotModuleCA.cs:70` — `[Desc("If true, the bot will use compositions defined in the UnitCompositionsBotModule to determine what units to build.",`
  - `OpenRA.Mods.CA/Traits/BotModules/UnitBuilderBotModuleCA.cs:101` — `UnitCompositionsBotModule compositionsModule;`
  - `OpenRA.Mods.CA/Traits/BotModules/UnitBuilderBotModuleCA.cs:124` — `compositionsModule = Info.UseCompositions ? self.World.WorldActor.TraitOrDefault<UnitCompositionsBotModule>() : null;`

### `MCVManagerBotModuleCA.cs`

- Local: `OpenRA.Mods.CA/Traits/BotModules/MCVManagerBotModuleCA.cs`
- Upstream: `OpenRA.Mods.CA/Traits/BotModules/MCVManagerBotModuleCA.cs`
- Status: **DIVERGED**
- Cameo consumers:
  - None outside the implementation file.
- Upstream consumers:
  - `mods/ca/rules/ai.yaml:846` — `McvManagerBotModuleCA@brutal:`
  - `mods/ca/rules/ai.yaml:854` — `McvManagerBotModuleCA@upper:`
  - `mods/ca/rules/ai.yaml:862` — `McvManagerBotModuleCA@lower:`

### `PowerDownBotModuleCA.cs`

- Local: `OpenRA.Mods.CA/Traits/BotModules/PowerDownBotModuleCA.cs`
- Upstream: `OpenRA.Mods.CA/Traits/BotModules/PowerDownBotModuleCA.cs`
- Status: **DIVERGED**
- Cameo consumers:
  - None outside the implementation file.
- Upstream consumers:
  - `mods/ca/rules/ai.yaml:844` — `PowerDownBotModuleCA:`

### `PlugSpawnerBotModuleCA.cs`

- Local: `OpenRA.Mods.Cameo/Traits/BotModules/PlugSpawnerBotModuleCA.cs`
- Upstream: `no counterpart`
- Status: **LOCAL-ONLY**
- Cameo consumers:
  - None outside the implementation file.
- Upstream consumers:
  - None outside the implementation file.

### Priority conclusions

- `UnitCompositionsBotModule`: the local repository has no consumer outside its implementation; local `UnitBuilderBotModuleCA` does not mention it. Upstream `UnitBuilderBotModuleCA` reads it (`UnitCompositionsBotModule compositionsModule = ...`) and upstream `mods/ca/rules/ai.yaml` defines `UnitCompositionsBotModule` at line 2733. Finding (a) is **confirmed**.
- `McvManagerBotModuleCA`: Cameo's AI YAML uses the engine `McvExpansionManagerBotModule` at `mods/cameo/ai/ai.yaml:3141` and does not use the CA module. Upstream CA's own `mods/ca/rules/ai.yaml` uses `McvManagerBotModuleCA` at lines 846, 854, and 862; it does not use `McvExpansionManagerBotModule`. Finding (b) is **true for Cameo's local integration**, but upstream CA has not superseded the CA module with the engine module.
- `PowerDownBotModuleCA`: the source is divergent; the local YAML does not consume it, while upstream CA's AI YAML defines it at `mods/ca/rules/ai.yaml:844`.
- `PlugSpawnerBotModuleCA`: this is Cameo-only; no counterpart exists under upstream `OpenRA.Mods.CA`, and no upstream consumer was found.

## OpenRA.Mods.AS summary

No plausible upstream Attacque Superieure checkout was found in the provided clones; AS staleness could not be measured against upstream.
Cameo's vendored `engine/OpenRA.Mods.AS` contains 241 C# files; the checked CA engine contains 0 AS files.

## Vendor-point estimate

Exact historical matches were found for 39 divergent files. The median matched vendor date is approximately **2023-05-27**, versus upstream HEAD **2026-07-30**; this is roughly **38.1 months** of source drift. The JSON contains each file's exact matched commit and commit count. Because some files are local customizations and some never match an exact historical blob, treat the median as an estimate rather than a single repository-wide fork point.
