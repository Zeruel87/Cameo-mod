# audit_ca_unused: vendored C# Cameo never uses, and what CA uses it for

| kind | declared | unused in Cameo | of those, used by CA |
|---|--:|--:|--:|
| activity | 16 | 3 | 0 |
| logic | 19 | 19 | 0 |
| projectile | 9 | 0 | 0 |
| trait | 292 | 87 | 57 |
| warhead | 16 | 0 | 0 |
| widget | 21 | 6 | 5 |

## Unused here, USED by CA: the purpose to implement (most-used first)

- **ProvidesPrerequisiteValidatedFaction** (trait, `OpenRA.Mods.CA/Traits/Player/ProvidesPrerequisiteValidatedFaction.cs`): CA uses it 348x, e.g. `mods/ca/rules/custom/coop-rules.yaml`, `mods/ca/rules/misc.yaml`, `mods/ca/rules/powers.yaml`
- **PeriodicProducerCA** (trait, `OpenRA.Mods.CA/Traits/PeriodicProducerCA.cs`): CA uses it 50x, e.g. `mods/ca/maps/ca-testing-grounds/rules.yaml`, `mods/ca/maps/shellmap/rules.yaml`, `mods/ca/missions/main-campaign/ca07-conspiracy/conspiracy-rules.yaml`
- **SpawnRandomActorOnDeath** (trait, `OpenRA.Mods.CA/Traits/SpawnRandomActorOnDeath.cs`): CA uses it 45x, e.g. `mods/ca/maps/ca-composition-tester/rules.yaml`, `mods/ca/maps/tfca/tfca-rules-base.yaml`, `mods/ca/missions/main-campaign/ca01-crossrip/crossrip-rules.yaml`
- **WithPalettedOverlay** (trait, `OpenRA.Mods.CA/Traits/Modifiers/WithPalettedOverlay.cs`): CA uses it 32x, e.g. `mods/ca/missions/main-campaign/ca26-capitulation/capitulation-rules.yaml`, `mods/ca/rules/custom/mastermind-madness.yaml`, `mods/ca/rules/defaults.yaml`
- **DamageTypeDamageMultiplier** (trait, `OpenRA.Mods.CA/Traits/Multipliers/DamageTypeDamageMultiplier.cs`): CA uses it 27x, e.g. `mods/ca/missions/main-campaign/ca30-singularity/singularity-rules.yaml`, `mods/ca/missions/main-campaign/ca36-reckoning/reckoning-rules.yaml`, `mods/ca/missions/main-campaign/ca53-defiance/defiance-rules.yaml`
- **WithRestartableIdleOverlay** (trait, `OpenRA.Mods.CA/Traits/Render/WithRestartableIdleOverlay.cs`): CA uses it 23x, e.g. `mods/ca/missions/main-campaign/ca01-crossrip/crossrip-rules.yaml`, `mods/ca/missions/main-campaign/ca30-singularity/singularity-rules.yaml`, `mods/ca/missions/main-campaign/ca42-schism/schism-rules.yaml`
- **AnnounceOnCreation** (trait, `OpenRA.Mods.CA/Traits/Sound/AnnounceOnCreation.cs`): CA uses it 21x, e.g. `mods/ca/missions/main-campaign/ca09-salvation/salvation-rules.yaml`, `mods/ca/missions/main-campaign/ca27-emancipation/emancipation-rules.yaml`, `mods/ca/rules/scrin.yaml`
- **ChronoshiftableCA** (trait, `OpenRA.Mods.CA/Traits/ChronoshiftableCA.cs`): CA uses it 13x, e.g. `mods/ca/rules/defaults.yaml`, `mods/ca/rules/vehicles.yaml`
- **GrantConditionOnHealingReceived** (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantConditionOnHealingReceived.cs`): CA uses it 13x, e.g. `mods/ca/maps/tfca/tfca-rules-base.yaml`, `mods/ca/missions/main-campaign/ca53-defiance/defiance-rules.yaml`, `mods/ca/rules/defaults.yaml`
- **PulsingPaletteEffect** (trait, `OpenRA.Mods.CA/Traits/PaletteEffects/PulsingPaletteEffect.cs`): CA uses it 13x, e.g. `mods/ca/rules/palettes.yaml`
- **MindControllableProgressBar** (trait, `OpenRA.Mods.CA/Traits/MindControllableProgressBar.cs`): CA uses it 11x, e.g. `mods/ca/rules/defaults.yaml`, `mods/ca/rules/scrin.yaml`, `mods/ca/rules/structures.yaml`
- **TargetedAttackAbility** (trait, `OpenRA.Mods.CA/Traits/TargetedAttackAbility.cs`): CA uses it 9x, e.g. `mods/ca/maps/tfca/tfca-rules-base.yaml`, `mods/ca/rules/aircraft.yaml`, `mods/ca/rules/infantry.yaml`
- **ExternalLinkButton** (widget, `OpenRA.Mods.CA/Widgets/ExternalLinkButtonWidget.cs`): CA uses it 8x, e.g. `mods/ca/chrome/mainmenu.yaml`
- **GrantDelayedCondition** (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantDelayedCondition.cs`): CA uses it 8x, e.g. `mods/ca/maps/ca-composition-tester/rules.yaml`, `mods/ca/missions/main-campaign/ca14-treachery/treachery-rules.yaml`, `mods/ca/rules/civilian.yaml`
- **GrantStackingCondition** (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantStackingCondition.cs`): CA uses it 8x, e.g. `mods/ca/rules/defaults.yaml`, `mods/ca/rules/infantry.yaml`, `mods/ca/rules/scrin.yaml`
- **OverlayPlayerColorPalette** (trait, `OpenRA.Mods.CA/Traits/Palettes/OverlayPlayerColorPalette.cs`): CA uses it 8x, e.g. `mods/ca/rules/custom/two-tone-nod.yaml`, `mods/ca/rules/palettes.yaml`
- **OverlayPlayerColorPalette** (trait, `OpenRA.Mods.Cameo/Traits/Render/OverlayPlayerColorPalette.cs`): CA uses it 8x, e.g. `mods/ca/rules/custom/two-tone-nod.yaml`, `mods/ca/rules/palettes.yaml`
- **AttackSoundsCA** (trait, `OpenRA.Mods.CA/Traits/Sound/AttackSoundsCA.cs`): CA uses it 7x, e.g. `mods/ca/maps/tfca/tfca-rules-base.yaml`, `mods/ca/rules/infantry.yaml`, `mods/ca/rules/scrin.yaml`
- **TracksCapturedFaction** (trait, `OpenRA.Mods.CA/Traits/TracksCapturedFaction.cs`): CA uses it 7x, e.g. `mods/ca/rules/scrin.yaml`, `mods/ca/rules/structures.yaml`
- **AttachableTo** (trait, `OpenRA.Mods.CA/Traits/AttachableTo.cs`): CA uses it 6x, e.g. `mods/ca/rules/defaults.yaml`, `mods/ca/rules/ships.yaml`, `mods/ca/rules/vehicles.yaml`
- **Attachable** (trait, `OpenRA.Mods.CA/Traits/Attachable.cs`): CA uses it 5x, e.g. `mods/ca/missions/coop-campaign/ca27-emancipation-coop/emancipation-coop-rules.yaml`, `mods/ca/rules/misc.yaml`, `mods/ca/rules/vehicles.yaml`
- **ConvertsDamageToHealth** (trait, `OpenRA.Mods.CA/Traits/ConvertsDamageToHealth.cs`): CA uses it 5x, e.g. `mods/ca/rules/custom/scrinfestation-base.yaml`, `mods/ca/rules/scrin.yaml`
- **GrantChargingCondition** (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantChargingCondition.cs`): CA uses it 5x, e.g. `mods/ca/missions/coop-campaign/ca50-preservation-coop/preservation-coop-rules.yaml`, `mods/ca/missions/main-campaign/ca50-preservation/preservation-rules.yaml`, `mods/ca/rules/custom/campaign-rules.yaml`
- **LeavesTrailsCA** (trait, `OpenRA.Mods.CA/Traits/Render/LeavesTrailsCA.cs`): CA uses it 4x, e.g. `mods/ca/rules/ships.yaml`, `mods/ca/rules/vehicles.yaml`
- **UnloadOnCondition** (trait, `OpenRA.Mods.CA/Traits/Conditions/UnloadOnCondition.cs`): CA uses it 4x, e.g. `mods/ca/rules/defaults.yaml`, `mods/ca/rules/vehicles.yaml`
- **WithNameTagDecorationCA** (trait, `OpenRA.Mods.CA/Traits/Render/WithNameTagDecorationCA.cs`): CA uses it 4x, e.g. `mods/ca/maps/team-mastermind-madness/rules.yaml`, `mods/ca/maps/tfca/tfca-rules-base.yaml`, `mods/ca/rules/custom/mastermind-madness.yaml`
- **AttackAircraftCA** (trait, `OpenRA.Mods.CA/Traits/Air/AttackAircraftCA.cs`): CA uses it 3x, e.g. `mods/ca/rules/aircraft.yaml`
- **GrantConditionOnOrders** (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantConditionOnOrders.cs`): CA uses it 3x, e.g. `mods/ca/rules/aircraft.yaml`
- **PopControlled** (trait, `OpenRA.Mods.CA/Traits/PopControlled.cs`): CA uses it 3x, e.g. `mods/ca/maps/ca-testing-grounds/rules.yaml`, `mods/ca/rules/misc.yaml`
- **RenderShroudCircleCA** (trait, `OpenRA.Mods.CA/Traits/Render/RenderShroudCircleCA.cs`): CA uses it 3x, e.g. `mods/ca/maps/shellmap/rules.yaml`, `mods/ca/rules/misc.yaml`, `mods/ca/rules/vehicles.yaml`
- **SpawnActorOnCapture** (trait, `OpenRA.Mods.CA/Traits/SpawnActorOnCapture.cs`): CA uses it 3x, e.g. `mods/ca/rules/defaults.yaml`
- **TimedDamageMultiplier** (trait, `OpenRA.Mods.CA/Traits/Multipliers/TimedDamageMultiplier.cs`): CA uses it 3x, e.g. `mods/ca/rules/defaults.yaml`, `mods/ca/rules/vehicles.yaml`
- **CloakPaletteEffectCA** (trait, `OpenRA.Mods.CA/Traits/PaletteEffects/CloakPaletteEffectCA.cs`): CA uses it 2x, e.g. `mods/ca/rules/palettes.yaml`
- **ContainerWithTooltip** (widget, `OpenRA.Mods.CA/Widgets/ContainerWithTooltipWidget.cs`): CA uses it 2x, e.g. `mods/ca/chrome/ingame-infostats.yaml`, `mods/ca/chrome/ingame-player.yaml`
- **GrantConditionOnPrerequisiteCA** (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantConditionOnPrerequisiteCA.cs`): CA uses it 2x, e.g. `mods/ca/rules/defaults.yaml`
- **GrantThermalCondition** (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantThermalCondition.cs`): CA uses it 2x, e.g. `mods/ca/rules/aircraft.yaml`
- **ImageCA** (widget, `OpenRA.Mods.CA/Widgets/ImageCAWidget.cs`): CA uses it 2x, e.g. `mods/ca/chrome/mainmenu.yaml`
- **LinkedProducerSource** (trait, `OpenRA.Mods.CA/Traits/LinkedProducerSource.cs`): CA uses it 2x, e.g. `mods/ca/rules/defaults.yaml`
- **ResourcePurifierCA** (trait, `OpenRA.Mods.CA/Traits/ResourcePurifierCA.cs`): CA uses it 2x, e.g. `mods/ca/rules/structures.yaml`
- **WithCargoHatchAnimation** (trait, `OpenRA.Mods.CA/Traits/Render/WithCargoHatchAnimation.cs`): CA uses it 2x, e.g. `mods/ca/rules/aircraft.yaml`
- **WithProductionDoorOverlayCA** (trait, `OpenRA.Mods.CA/Traits/Render/WithProductionDoorOverlayCA.cs`): CA uses it 2x, e.g. `mods/ca/rules/structures.yaml`
- **CapturedFactionsManager** (trait, `OpenRA.Mods.CA/Traits/Player/CapturedFactionsManager.cs`): CA uses it 1x, e.g. `mods/ca/rules/player.yaml`
- **CustomRadarColor** (trait, `OpenRA.Mods.CA/Traits/CustomRadarColor.cs`): CA uses it 1x, e.g. `mods/ca/rules/defaults.yaml`
- **DoesNotBlock** (trait, `OpenRA.Mods.CA/Traits/DoesNotBlock.cs`): CA uses it 1x, e.g. `mods/ca/rules/aircraft.yaml`
- **GrantConditionOnPrerequisiteManagerCA** (trait, `OpenRA.Mods.CA/Traits/Player/GrantConditionOnPrerequisiteManagerCA.cs`): CA uses it 1x, e.g. `mods/ca/rules/player.yaml`
- **GrantTimedConditionOnCargoAction** (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantTimedConditionOnCargoAction.cs`): CA uses it 1x, e.g. `mods/ca/rules/vehicles.yaml`
- **GrantTimedConditionOnCrushWarning** (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantTimedConditionOnCrushWarning.cs`): CA uses it 1x, e.g. `mods/ca/rules/defaults.yaml`
- **GuidedMissile** (trait, `OpenRA.Mods.CA/Traits/GuidedMissile.cs`): CA uses it 1x, e.g. `mods/ca/rules/vehicles.yaml`
- **ImmobileWithFacing** (trait, `OpenRA.Mods.CA/Traits/ImmobileWithFacing.cs`): CA uses it 1x, e.g. `mods/ca/rules/infantry.yaml`
- **LinkedProducerTarget** (trait, `OpenRA.Mods.CA/Traits/LinkedProducerTarget.cs`): CA uses it 1x, e.g. `mods/ca/rules/scrin.yaml`
- **PopController** (trait, `OpenRA.Mods.CA/Traits/Player/PopController.cs`): CA uses it 1x, e.g. `mods/ca/rules/player.yaml`
- **PortableChronoModifier** (trait, `OpenRA.Mods.CA/Traits/Multipliers/PortableChronoModifier.cs`): CA uses it 1x, e.g. `mods/ca/rules/vehicles.yaml`
- **ProductionPaletteCA** (widget, `OpenRA.Mods.CA/Widgets/ProductionPaletteCAWidget.cs`): CA uses it 1x, e.g. `mods/ca/chrome/ingame-player.yaml`
- **ReflectsDamage** (trait, `OpenRA.Mods.CA/Traits/ReflectsDamage.cs`): CA uses it 1x, e.g. `mods/ca/rules/scrin.yaml`
- **RevealOnFireCA** (trait, `OpenRA.Mods.CA/Traits/RevealOnFireCA.cs`): CA uses it 1x, e.g. `mods/ca/rules/defaults.yaml`
- **SpawnActorOnSell** (trait, `OpenRA.Mods.CA/Traits/SpawnActorOnSell.cs`): CA uses it 1x, e.g. `mods/ca/rules/structures.yaml`
- **SpritePowerMeter** (widget, `OpenRA.Mods.CA/Widgets/SpritePowerMeterWidget.cs`): CA uses it 1x, e.g. `mods/ca/chrome/ingame-player.yaml`
- **TurnOnIdleCA** (trait, `OpenRA.Mods.CA/Traits/TurnOnIdleCA.cs`): CA uses it 1x, e.g. `mods/ca/rules/vehicles.yaml`
- **WithChronoshiftChargePipsDecoration** (trait, `OpenRA.Mods.CA/Traits/Render/WithChronoshiftChargePipsDecoration.cs`): CA uses it 1x, e.g. `mods/ca/rules/vehicles.yaml`
- **WithChronosphereOverlay** (trait, `OpenRA.Mods.CA/Traits/Render/WithChronosphereOverlay.cs`): CA uses it 1x, e.g. `mods/ca/rules/structures.yaml`
- **WithDetectionCircle** (trait, `OpenRA.Mods.CA/Traits/Render/WithDetectionCircle.cs`): CA uses it 1x, e.g. `mods/ca/rules/vehicles.yaml`
- **WithMuzzleOverlayCA** (trait, `OpenRA.Mods.CA/Traits/Render/WithMuzzleOverlayCA.cs`): CA uses it 1x, e.g. `mods/ca/rules/scrin.yaml`

## Unused here AND in CA (truly dead, or a Cameo-only file never wired)

- ActorIconTooltipCameo (logic, `OpenRA.Mods.Cameo/Widgets/Logic/ActorIconTooltipCameoLogic.cs`)
- ArmyTooltipCameo (logic, `OpenRA.Mods.Cameo/Widgets/Logic/ArmyTooltipCameoLogic.cs`)
- ArmyValueTooltip (logic, `OpenRA.Mods.Cameo/Widgets/Logic/ArmyValueTooltipLogic.cs`)
- AttachOnCreation (trait, `OpenRA.Mods.CA/Traits/AttachOnCreation.cs`)
- AttachOnTransform (trait, `OpenRA.Mods.CA/Traits/AttachOnTransform.cs`)
- AttachedAircraft (trait, `OpenRA.Mods.CA/Traits/AttachedAircraft.cs`)
- AttackGarrisonedSP (trait, `OpenRA.Mods.CA/Traits/Attack/AttackGarrisonedSP.cs`)
- CameoDisplaySettings (logic, `OpenRA.Mods.Cameo/Widgets/Logic/CameoDisplaySettingsLogic.cs`)
- CameoGameplaySettings (logic, `OpenRA.Mods.Cameo/Widgets/Logic/CameoGameplaySettingsLogic.cs`)
- CameoMainMenu (logic, `OpenRA.Mods.Cameo/Widgets/Logic/CameoMainMenuLogic.cs`)
- CameoObserverStats (logic, `OpenRA.Mods.Cameo/Widgets/Logic/CameoObserverStatsLogic.cs`)
- CameoRemasterDisplaySettings (logic, `OpenRA.Mods.Cameo/Widgets/Logic/CameoRemasterDisplaySettingsLogic.cs`)
- CameoRemasterTerrainTemplate (trait, `OpenRA.Mods.Cameo/Terrain/CameoRemasterTerrain.cs`)
- ChangesHealthVersus (trait, `OpenRA.Mods.CA/Traits/ChangesHealthVersus.cs`)
- ChargingSelfDestruct (trait, `OpenRA.Mods.CA/Traits/ChargingSelfDestruct.cs`)
- CommanderTreeWindow (logic, `OpenRA.Mods.Cameo/Widgets/Logic/CommanderTreeWindowLogic.cs`)
- ConditionalTintPostProcessEffect (trait, `OpenRA.Mods.Cameo/Traits/World/ConditionalTintPostProcessEffect.cs`)
- CustomFormationsCommandBar (logic, `OpenRA.Mods.Cameo/Widgets/CustomFormationsCommandBarLogic.cs`)
- DeployOnCondition (trait, `OpenRA.Mods.Cameo/Traits/DeployOnCondition.cs`)
- DetonateWeaponOnDeploy (trait, `OpenRA.Mods.CA/Traits/DetonateWeaponOnDeploy.cs`)
- EnterAirstrikeMasterCA (activity, `OpenRA.Mods.CA/Activities/EnterAirstrikeMasterCA.cs`)
- ExternalLinks (logic, `OpenRA.Mods.CA/Widgets/Logic/ExternalLinksLogic.cs`)
- FreeActorWithCondition (trait, `OpenRA.Mods.Cameo/Traits/FreeActorWithCondition.cs`)
- GrantConditionOnFogEnabled (trait, `OpenRA.Mods.CA/Traits/Conditions/GrantConditionOnFogEnabled.cs`)
- HeliDeployInner (activity, `OpenRA.Mods.Cameo/Activities/HeliDeployForGrantedCondition.cs`)
- InfiltrateForSupportPowerCA (trait, `OpenRA.Mods.CA/Traits/Infiltration/InfiltrateForSupportPowerCA.cs`)
- InfiltrateToAttach (trait, `OpenRA.Mods.CA/Traits/Infiltration/InfiltrateToAttach.cs`)
- InstantTransforms (trait, `OpenRA.Mods.CA/Traits/InstantTransforms.cs`)
- IssueOrderAfterTransform (activity, `OpenRA.Mods.CA/Activities/InstantTransform.cs`)
- LayeredDamageMultiplier (trait, `OpenRA.Mods.CA/Traits/Multipliers/LayeredDamageMultiplier.cs`)
- Lobby (logic, `OpenRA.Mods.Cameo/Widgets/Logic/LobbyLogic.cs`)
- Materialization (trait, `OpenRA.Mods.Cameo/Traits/Render/WithBuildingMaterialization.cs`)
- MissileBase (trait, `OpenRA.Mods.CA/Traits/MissileBase.cs`)
- ProductionTooltipCameo (logic, `OpenRA.Mods.Cameo/Widgets/Logic/ProductionTooltipCameoLogic.cs`)
- PromotionPalette (trait, `OpenRA.Mods.Cameo/Traits/PromotionPalette.cs`)
- PromotionTreeButton (logic, `OpenRA.Mods.Cameo/Widgets/Logic/Ingame/PromotionTreeButtonLogic.cs`)
- ProvidesDelayedPrerequisite (trait, `OpenRA.Mods.CA/Traits/Player/ProvidesDelayedPrerequisite.cs`)
- RevealedPlayersManager (trait, `OpenRA.Mods.CA/Traits/World/RevealedPlayersManager.cs`)
- ScaledBullet (trait, `OpenRA.Mods.Cameo/Projectiles/ScaledBullet.cs`)
- ScaledImage (widget, `OpenRA.Mods.Cameo/Widgets/ScaledImageWidget.cs`)
- ScaledSelfHeal (trait, `OpenRA.Mods.Cameo/Traits/ScaledSelfHeal.cs`)
- SimpleTooltipWithDesc (logic, `OpenRA.Mods.CA/Widgets/Logic/SimpleTooltipWithDescLogic.cs`)
- SpritePowerMeter (logic, `OpenRA.Mods.CA/Widgets/Logic/Ingame/SpritePowerMeterLogic.cs`)
- StarportBatchStatus (logic, `OpenRA.Mods.Cameo/Widgets/Logic/StarportBatchStatusLogic.cs`)
- StatisticsWindow (logic, `OpenRA.Mods.Cameo/Widgets/Logic/StatisticsWindowLogic.cs`)
- TemplateMenu (logic, `OpenRA.Mods.CA/Widgets/Logic/TemplateMenuLogic.cs`)
- TerrainLightSourceCA (trait, `OpenRA.Mods.Cameo/Traits/TerrainLightSourceCA.cs`)
- TransferCashSupportPower (trait, `OpenRA.Mods.Cameo/Traits/SupportPowers/TransferCashSupportPower.cs`)
- TransfersStanceToDeathActor (trait, `OpenRA.Mods.CA/Traits/TransferStanceToDeathActor.cs`)
- WithActivateAnimation (trait, `OpenRA.Mods.CA/Traits/Render/WithActivateAnimation.cs`)
- WithBuildingBibCA (trait, `OpenRA.Mods.Cameo/Traits/Render/WithBuildingBibCA.cs`)
- WithBuildingMaterialization (trait, `OpenRA.Mods.Cameo/Traits/Render/WithBuildingMaterialization.cs`)
- WithHarvesterCapacityBar (trait, `OpenRA.Mods.CA/Traits/Render/WithHarvesterCapacityBar.cs`)

_Informational: never fails. Which mechanics to wire is a maintainer decision (UPSTREAM_MODS.md §5). Unused ≠ dead: check the CA column before deleting anything._
