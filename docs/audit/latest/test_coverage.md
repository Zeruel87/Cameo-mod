# audit_test_coverage — test floors and untested modules

| metric | meaning | value | floor/baseline |
|---|---|---|---|
| T1 | NUnit [Test] cases in OpenRA.Mods.Cameo.Test (5 file(s)) | 48 | >= 24 |
| T2 | `def test_*` in tools/tests (89 file(s)) | 887 | >= 177 |
| T3 | modules with no test mentioning them | 267 | <= 224 |


## How to run the real suites (periodic run must paste output here)

```
dotnet test OpenRA.Mods.Cameo.Test/OpenRA.Mods.Cameo.Test.csproj -c Release
python -m unittest discover -s tools/tests -t tools/tests
```


## T3 — untested modules (267)

| kind | file | type(s)/module |
|---|---|---|
| C# | OpenRA.Mods.Cameo/Activities/HeliDeployForGrantedCondition.cs | HeliDeployForGrantedCondition, HeliDeployInner |
| C# | OpenRA.Mods.Cameo/CyberintelThemes.cs | CyberintelThemes |
| C# | OpenRA.Mods.Cameo/Effects/TintedSpriteEffect.cs | TintedSpriteEffect |
| C# | OpenRA.Mods.Cameo/FileSystem/BagFile.cs | AudioBagLoader |
| C# | OpenRA.Mods.Cameo/Graphics/CameoSpriteSequence.cs | CameoSpriteSequenceLoader, CameoSpriteSequence |
| C# | OpenRA.Mods.Cameo/Graphics/LayeredSelectionBarsRenderable.cs | LayeredSelectionBarsRenderable |
| C# | OpenRA.Mods.Cameo/Graphics/LightningGeometry.cs | LightningGeometry |
| C# | OpenRA.Mods.Cameo/Graphics/LightningRenderable.cs | LightningRenderable |
| C# | OpenRA.Mods.Cameo/Graphics/UILineRenderable.cs | UILineAnnotationRenderable, UIRectangleAnnotationRenderable |
| C# | OpenRA.Mods.Cameo/LoadScreens/FitImageLoadScreen.cs | FitImageLoadScreen |
| C# | OpenRA.Mods.Cameo/Orders/CustomFormationsAttackMoveOrderGenerator.cs | CustomFormationsAttackMoveOrderGenerator |
| C# | OpenRA.Mods.Cameo/Orders/CustomFormationsOrderGeneratorBase.cs | UnitOrderResult, CustomFormationsOrderGeneratorBase, OrderGeneratorHelpers |
| C# | OpenRA.Mods.Cameo/Orders/CustomFormationsUnitOrderGenerator.cs | CustomFormationsUnitOrderGenerator |
| C# | OpenRA.Mods.Cameo/Projectiles/InstantHitWithFakeBullets.cs | InstantHitWithFakeBullets |
| C# | OpenRA.Mods.Cameo/Projectiles/LightningZap.cs | LightningZap |
| C# | OpenRA.Mods.Cameo/Rendering/ColorPickerColorShift.cs | ColorPickerColorShift |
| C# | OpenRA.Mods.Cameo/Rendering/PlayerColorShift.cs | PlayerColorShift |
| C# | OpenRA.Mods.Cameo/Traits/AdaptiveGameSpeed.cs | AdaptiveGameSpeed |
| C# | OpenRA.Mods.Cameo/Traits/AdaptiveGameSpeedHost.cs | AdaptiveGameSpeedHost |
| C# | OpenRA.Mods.Cameo/Traits/AdaptiveSpeedController.cs | AdaptiveSpeedController |
| C# | OpenRA.Mods.Cameo/Traits/AnnounceOnDamageState.cs | AnnounceOnDamageState |
| C# | OpenRA.Mods.Cameo/Traits/ArmorPlating.cs | ArmorPlating, ArmorPlatingInit |
| C# | OpenRA.Mods.Cameo/Traits/Attack/AttackInfectCA.cs | AttackInfectCA |
| C# | OpenRA.Mods.Cameo/Traits/BotGlobalUnitBudget.cs | BotGlobalUnitBudget |
| C# | OpenRA.Mods.Cameo/Traits/BotInsurance.cs | BotInsurance |
| C# | OpenRA.Mods.Cameo/Traits/BotModules/CratePickupBotModule.cs | CratePickupBotModule |
| C# | OpenRA.Mods.Cameo/Traits/BotModules/PlugSpawnerBotModuleCA.cs | PlugSpawnerBotModuleCA |
| C# | OpenRA.Mods.Cameo/Traits/CameoSettings.cs | CameoSettings |
| C# | OpenRA.Mods.Cameo/Traits/ChangesPhysicalState.cs | ChangesPhysicalState |
| C# | OpenRA.Mods.Cameo/Traits/Conditions/GrantConditionOnPower.cs | GrantConditionOnPower |
| C# | OpenRA.Mods.Cameo/Traits/Conditions/GrantExternalConditionToTransport.cs | GrantExternalConditionToTransport |
| C# | OpenRA.Mods.Cameo/Traits/Conditions/HeliGrantConditionOnDeploy.cs | HeliGrantConditionOnDeploy |
| C# | OpenRA.Mods.Cameo/Traits/CryoFogEmitter.cs | CryoFogEmitter |
| C# | OpenRA.Mods.Cameo/Traits/CryoFogLimiter.cs | CryoFogLimiter |
| C# | OpenRA.Mods.Cameo/Traits/DeployOnCondition.cs | DeployOnCondition |
| C# | OpenRA.Mods.Cameo/Traits/DeterministicCellOffset.cs | DeterministicCellOffset |
| C# | OpenRA.Mods.Cameo/Traits/DeterministicOffsetSmokeParticleEmitter.cs | DeterministicOffsetSmokeParticleEmitter |
| C# | OpenRA.Mods.Cameo/Traits/DroneSpawnerMasterCA.cs | DroneSpawnerMasterCA |
| C# | OpenRA.Mods.Cameo/Traits/ExplodesCA.cs | FireWarheadsOnDeathCA |
| C# | OpenRA.Mods.Cameo/Traits/FreeActorWithCondition.cs | FreeActorWithCondition, FreeActorInit, ParentActorInit |
| C# | OpenRA.Mods.Cameo/Traits/GrantConditionOnPlayerTotalCash.cs | GrantConditionOnPlayerTotalCash |
| C# | OpenRA.Mods.Cameo/Traits/GrantsShield.cs | GrantsShield |
| C# | OpenRA.Mods.Cameo/Traits/InfectableCA.cs | InfectorCA, InfectableCA |
| C# | OpenRA.Mods.Cameo/Traits/InfectableOld.cs | InfectableOld |
| C# | OpenRA.Mods.Cameo/Traits/InfectorOld.cs | InfectorOld |
| C# | OpenRA.Mods.Cameo/Traits/Integrity.cs | Integrity |
| C# | OpenRA.Mods.Cameo/Traits/LarvaConsumingProduction.cs | LarvaConsumingProduction |
| C# | OpenRA.Mods.Cameo/Traits/LarvaProductionQueue.cs | LarvaProductionQueue |
| C# | OpenRA.Mods.Cameo/Traits/Modifiers/WithPhysicalStateColoredOverlay.cs | WithPhysicalStateColoredOverlay |
| C# | OpenRA.Mods.Cameo/Traits/ModifiesCombatProportionalToPhysicalState.cs | ModifiesCombatProportionalToPhysicalState |
| C# | OpenRA.Mods.Cameo/Traits/NewConstructionOptionsNotification.cs | NewConstructionOptionsNotification, NewConstructionOptionsOnDeploy |
| C# | OpenRA.Mods.Cameo/Traits/OneActorPerCell.cs | OneActorPerCell |
| C# | OpenRA.Mods.Cameo/Traits/PaletteEffects/TAStealthTankCloakPaletteEffect.cs | TAStealthTankCloakPaletteEffect |
| C# | OpenRA.Mods.Cameo/Traits/Player/CountManager.cs | CountManager |
| C# | OpenRA.Mods.Cameo/Traits/Player/CriticalUnitAttackNotifier.cs | CriticalUnit, CriticalUnitAttackNotifier |
| C# | OpenRA.Mods.Cameo/Traits/Player/CustomFormationsModOptions.cs | CustomFormationsModOptions |
| C# | OpenRA.Mods.Cameo/Traits/Player/ObserverConditionNotification.cs | ObserverConditionNotification |
| C# | OpenRA.Mods.Cameo/Traits/Player/PlayerPromotions.cs | PlayerPromotions |
| C# | OpenRA.Mods.Cameo/Traits/Player/ProductionTracker.cs | ProductionTracker, ProductionTrackerBuildOrderItem, ProductionTrackerUnitValueItem |
| C# | OpenRA.Mods.Cameo/Traits/PlayerDisplayUpgrade.cs | PlayerDisplayUpgrade |
| C# | OpenRA.Mods.Cameo/Traits/ProductionIconHoverHeader.cs | ProductionIconHoverHeader |
| C# | OpenRA.Mods.Cameo/Traits/ProductionIconMutualExclusion.cs | ProductionIconMutualExclusion |
| C# | OpenRA.Mods.Cameo/Traits/PromotionPalette.cs | PromotionPalette |
| C# | OpenRA.Mods.Cameo/Traits/PromotionUpgrade.cs | PromotionUpgrade |
| C# | OpenRA.Mods.Cameo/Traits/ProvidesTeamProxyActor.cs | ProvidesTeamProxyActor |
| C# | OpenRA.Mods.Cameo/Traits/QuotaProductionManager.cs | QuotaProductionManager |
| C# | OpenRA.Mods.Cameo/Traits/Render/OverlayPlayerColorPalette.cs | OverlayPlayerColorPalette |
| C# | OpenRA.Mods.Cameo/Traits/Render/SelectionDecorations.cs | SelectionDecorations |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithAlpha.cs | WithAlpha |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithBuildingBibCA.cs | WithBuildingBibCA |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithCargoBuilding.cs | WithCargoBuilding |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithCreepOverlay.cs | CreepLayer, WithCreepOverlay |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithDeterministicOffsetIdleOverlay.cs | WithDeterministicOffsetIdleOverlay |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithLifetimeFade.cs | WithLifetimeFade |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithLoopedMakeAnimation.cs | WithLoopedMakeAnimation |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithMuzzleGlow.cs | WithMuzzleGlow |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithMuzzleSmoke.cs | WithMuzzleSmoke |
| C# | OpenRA.Mods.Cameo/Traits/Render/WithTurretSearchlight.cs | WithTurretSearchlight |
| C# | OpenRA.Mods.Cameo/Traits/ShadeMaster.cs | ShadeMaster |
| C# | OpenRA.Mods.Cameo/Traits/ShadeSlave.cs | ShadeSlave |
| C# | OpenRA.Mods.Cameo/Traits/SlaveMinerSpawnerMaster.cs | SlaveMinerSpawnerMaster |
| C# | OpenRA.Mods.Cameo/Traits/SlaveMinerSpawnerSlave.cs | SlaveMinerSpawnerSlave |
| C# | OpenRA.Mods.Cameo/Traits/SoundAnnouncement.cs | SoundAnnouncement |
| C# | OpenRA.Mods.Cameo/Traits/SpawnsActorsOnKill.cs | SpawnsActorsOnKill |
| C# | OpenRA.Mods.Cameo/Traits/StarportBatchProduction.cs | StarportBatchProductionQueue, StarportBatchAirdrop |
| C# | OpenRA.Mods.Cameo/Traits/SupportPowers/TransferCashSupportPower.cs | TransferCashSupportPower |
| C# | OpenRA.Mods.Cameo/Traits/TakeOffOnMake.cs | TakeOffOnMake |
| C# | OpenRA.Mods.Cameo/Traits/TerrainLightSourceCA.cs | TerrainLightSourceCA |
| C# | OpenRA.Mods.Cameo/Traits/UpdatesBuildOrder.cs | UpdatesBuildOrder |
| C# | OpenRA.Mods.Cameo/Traits/UpdatesCount.cs | UpdatesCount |
| C# | OpenRA.Mods.Cameo/Traits/UpdatesUnitsProduced.cs | UpdatesUnitsProduced |
| C# | OpenRA.Mods.Cameo/Traits/UsePointsOnProduction.cs | UsePointsOnProduction |
| C# | OpenRA.Mods.Cameo/Traits/World/AutoControlGroupsManager.cs | AutoControlGroupsManager |
| C# | OpenRA.Mods.Cameo/Traits/World/BackstabGameMode.cs | BackstabGameMode |
| C# | OpenRA.Mods.Cameo/Traits/World/ConditionalTintPostProcessEffect.cs | ConditionalTintPostProcessEffect |
| C# | OpenRA.Mods.Cameo/Traits/World/ConditionalWorldTint.cs | ConditionalWorldTint |
| C# | OpenRA.Mods.Cameo/Traits/World/HeatDistortionRenderer.cs | HeatDistortionRenderer |
| C# | OpenRA.Mods.Cameo/Traits/World/LobbySystemActorConditionDropdown.cs | LobbySystemActorConditionDropdown |
| C# | OpenRA.Mods.Cameo/Traits/World/NuclearFlashRenderer.cs | NuclearFlashRenderer |
| C# | OpenRA.Mods.Cameo/Traits/World/ResourceRegrowth.cs | ResourceRegrowth, LobbyScaledSeedsResource |
| C# | OpenRA.Mods.Cameo/Traits/World/ResourceSparkleEffect.cs | SparkleConfig, ResourceSparkleEffect |
| C# | OpenRA.Mods.Cameo/Traits/World/ShockwaveDistortionRenderer.cs | ShockwaveDistortionRenderer |
| C# | OpenRA.Mods.Cameo/Warheads/AffectsIntegrityWarhead.cs | AffectsIntegrityWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/AreaDamagePercentageWarhead.cs | AreaDamagePercentageWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/ChangeOwnerToNeutralWarhead.cs | ChangeOwnerToNeutralWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/GlowImpactWarhead.cs | GlowImpactWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/HeatDistortionWarhead.cs | HeatDistortionWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/HeavinessBell.cs | HeavinessBell |
| C# | OpenRA.Mods.Cameo/Warheads/MindControlWarhead.cs | MindControlWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/NuclearFlashEffectWarhead.cs | NuclearFlashEffectWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/ShockwaveWarhead.cs | ShockwaveWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/SpawnActorInAreaWarhead.cs | SpawnActorInAreaWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/SpawnActorOrWeaponWarhead.cs | SpawnActorOrWeaponWarhead |
| C# | OpenRA.Mods.Cameo/Warheads/StealResourceWarhead.cs | StealResourceWarhead |
| C# | OpenRA.Mods.Cameo/Widgets/AutoControlGroupsWidget.cs | AutoControlGroupsWidget |
| C# | OpenRA.Mods.Cameo/Widgets/ClickMaskWidget.cs | ClickMaskWidget |
| C# | OpenRA.Mods.Cameo/Widgets/CommanderTreeDismissWidget.cs | CommanderTreeDismissWidget |
| C# | OpenRA.Mods.Cameo/Widgets/CommanderTreeWidget.cs | CommanderTreeWidget |
| C# | OpenRA.Mods.Cameo/Widgets/CustomFormationsCommandBarLogic.cs | CustomFormationsCommandBarLogic |
| C# | OpenRA.Mods.Cameo/Widgets/DragHandleWidget.cs | DragHandleWidget |
| C# | OpenRA.Mods.Cameo/Widgets/IngamePromotionCounterWidget.cs | IngamePromotionCounterWidget |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/ActorIconTooltipCameoLogic.cs | ActorIconTooltipCameoLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/ArmyTooltipCameoLogic.cs | ArmyTooltipCameoLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/ArmyValueTooltipLogic.cs | ArmyValueTooltipLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/CameoDisplaySettingsLogic.cs | CameoDisplaySettingsLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/CameoGameplaySettingsLogic.cs | CameoGameplaySettingsLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/CameoMainMenuLogic.cs | CameoMainMenuLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/CameoObserverStatsLogic.cs | CameoObserverStatsLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/CommanderTreeWindowLogic.cs | CommanderTreeWindowLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/Ingame/PromotionTreeButtonLogic.cs | PromotionTreeButtonLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/IngameActorStatsLogicCameo.cs | IngameActorStatsLogicCameo |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/LobbyLogic.cs | LobbyLogic, LobbyFaction |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/ProductionTooltipCameoLogic.cs | ProductionTooltipCameoLogic |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/ReplayControlBarLogicCameo.cs | ReplayControlBarLogicCameo |
| C# | OpenRA.Mods.Cameo/Widgets/Logic/StarportBatchStatusLogic.cs | StarportBatchStatusLogic |
| C# | OpenRA.Mods.Cameo/Widgets/ObserverArmyValuesWidget.cs | ObserverArmyValuesWidget |
| C# | OpenRA.Mods.Cameo/Widgets/ObserverBuildOrderIconsWidget.cs | ObserverBuildOrderIconsWidget |
| C# | OpenRA.Mods.Cameo/Widgets/ObserverPromotionsIconsWidget.cs | ObserverPromotionsIconsWidget |
| C# | OpenRA.Mods.Cameo/Widgets/ObserverUnitsProducedIconsWidget.cs | ObserverUnitsProducedIconsWidget |
| C# | OpenRA.Mods.Cameo/Widgets/PlayerUpgradesIconsWidget.cs | PlayerUpgradesIconsWidget |
| C# | OpenRA.Mods.Cameo/Widgets/QuotaProductionPaletteWidget.cs | QuotaProductionPaletteWidget |
| C# | OpenRA.Mods.Cameo/Widgets/RoundedImageWidget.cs | RoundedImageWidget |
| C# | OpenRA.Mods.Cameo/Widgets/ScaledImageWidget.cs | ScaledImageWidget |
| C# | OpenRA.Mods.Cameo/Widgets/ScrollableLineGraphWidget.cs | ScrollableLineGraphWidget, ScrollableLineGraphSeries |
| python | tools/audit/audit_ai.py | audit_ai |
| python | tools/audit/audit_ai_personalities.py | audit_ai_personalities |
| python | tools/audit/audit_armament_naming.py | audit_armament_naming |
| python | tools/audit/audit_armor_upgrade_harm.py | audit_armor_upgrade_harm |
| python | tools/audit/audit_asset_files.py | audit_asset_files |
| python | tools/audit/audit_assets.py | audit_assets |
| python | tools/audit/audit_balance_drift.py | audit_balance_drift |
| python | tools/audit/audit_balance_sheet.py | audit_balance_sheet |
| python | tools/audit/audit_basebuilder_crates.py | audit_basebuilder_crates |
| python | tools/audit/audit_buildable_order.py | audit_buildable_order |
| python | tools/audit/audit_burst_delays.py | audit_burst_delays |
| python | tools/audit/audit_ca_drift.py | audit_ca_drift |
| python | tools/audit/audit_code_duplication.py | audit_code_duplication |
| python | tools/audit/audit_consistency_report.py | audit_consistency_report |
| python | tools/audit/audit_damage_grid.py | audit_damage_grid |
| python | tools/audit/audit_dead_warhead_fields.py | audit_dead_warhead_fields |
| python | tools/audit/audit_display_text.py | audit_display_text |
| python | tools/audit/audit_doc_claims.py | audit_doc_claims |
| python | tools/audit/audit_dune_rank_decoration.py | audit_dune_rank_decoration |
| python | tools/audit/audit_duplicate_inherits.py | audit_duplicate_inherits |
| python | tools/audit/audit_effect_warhead_names.py | audit_effect_warhead_names |
| python | tools/audit/audit_elite_gating.py | audit_elite_gating |
| python | tools/audit/audit_empty_warheads.py | audit_empty_warheads |
| python | tools/audit/audit_faction_leaks.py | audit_faction_leaks |
| python | tools/audit/audit_family_uniqueness.py | audit_family_uniqueness |
| python | tools/audit/audit_fluent.py | audit_fluent |
| python | tools/audit/audit_garrison_weapons.py | audit_garrison_weapons |
| python | tools/audit/audit_hex_shield_routing.py | audit_hex_shield_routing |
| python | tools/audit/audit_inherits.py | audit_inherits |
| python | tools/audit/audit_inline_effects.py | audit_inline_effects |
| python | tools/audit/audit_metadata.py | audit_metadata |
| python | tools/audit/audit_meter_dilution.py | audit_meter_dilution |
| python | tools/audit/audit_min_range.py | audit_min_range |
| python | tools/audit/audit_missing_elite.py | audit_missing_elite |
| python | tools/audit/audit_multiplier_modifiers.py | audit_multiplier_modifiers |
| python | tools/audit/audit_nuclear_flash_bindings.py | audit_nuclear_flash_bindings |
| python | tools/audit/audit_orphans.py | audit_orphans |
| python | tools/audit/audit_outliers.py | audit_outliers |
| python | tools/audit/audit_packs.py | audit_packs |
| python | tools/audit/audit_percentage_runtime.py | audit_percentage_runtime |
| python | tools/audit/audit_plating_exclusivity.py | audit_plating_exclusivity |
| python | tools/audit/audit_power_budget.py | audit_power_budget |
| python | tools/audit/audit_promotion_gating.py | audit_promotion_gating |
| python | tools/audit/audit_rank_decoration.py | audit_rank_decoration |
| python | tools/audit/audit_rename_safety.py | audit_rename_safety |
| python | tools/audit/audit_sequences.py | audit_sequences |
| python | tools/audit/audit_split_definitions.py | audit_split_definitions |
| python | tools/audit/audit_survivability_pricing.py | audit_survivability_pricing |
| python | tools/audit/audit_task_index.py | audit_task_index |
| python | tools/audit/audit_template_conformance.py | audit_template_conformance |
| python | tools/audit/audit_test_coverage.py | audit_test_coverage |
| python | tools/audit/audit_tier_weapon_class.py | audit_tier_weapon_class |
| python | tools/audit/audit_ts_death_palette.py | audit_ts_death_palette |
| python | tools/audit/audit_unconverted_templates.py | audit_unconverted_templates |
| python | tools/audit/audit_unique_traits.py | audit_unique_traits |
| python | tools/audit/audit_upgrade_coverage.py | audit_upgrade_coverage |
| python | tools/audit/audit_weapon_identity.py | audit_weapon_identity |
| python | tools/audit/audit_weapon_shape.py | audit_weapon_shape |
| python | tools/audit/audit_weapon_suffixes.py | audit_weapon_suffixes |
| python | tools/audit/audit_weapon_uniqueness.py | audit_weapon_uniqueness |
| python | tools/audit/check_effect_audio.py | check_effect_audio |
| python | tools/audit/dump_resolved.py | dump_resolved |
| python | tools/audit/effect_audit.py | effect_audit |
| python | tools/audit/environment.py | environment |
| python | tools/audit/find_empty_warhead.py | find_empty_warhead |
| python | tools/audit/find_mechanical_phase_a.py | find_mechanical_phase_a |
| python | tools/audit/find_orphan_old_keys.py | find_orphan_old_keys |
| python | tools/audit/find_orphan_old_keys_multi.py | find_orphan_old_keys_multi |
| python | tools/audit/gen_damage_matrix.py | gen_damage_matrix |
| python | tools/audit/gen_faction_matrix.py | gen_faction_matrix |
| python | tools/audit/gen_rename_maps.py | gen_rename_maps |
| python | tools/audit/phase_b_survey.py | phase_b_survey |
| python | tools/audit/propose_sonic_mapping.py | propose_sonic_mapping |
| python | tools/audit/review_resolve_diff.py | review_resolve_diff |
| python | tools/audit/summarize_role_comparison.py | summarize_role_comparison |
| python | tools/balance/_fix_min_range.py | _fix_min_range |
| python | tools/balance/_patch_ledgers_from_reports.py | _patch_ledgers_from_reports |
| python | tools/balance/_requantize_ledgers.py | _requantize_ledgers |
| python | tools/balance/_show_audit_summaries.py | _show_audit_summaries |
| python | tools/balance/_write_weapon_class.py | _write_weapon_class |
| python | tools/balance/armor_exposure.py | armor_exposure |
| python | tools/balance/audit_below_divider.py | audit_below_divider |
| python | tools/balance/compensate_retrofit.py | compensate_retrofit |
| python | tools/balance/consolidate_compatibility_profiles.py | consolidate_compatibility_profiles |
| python | tools/balance/consolidate_reviewed_weapon_roots.py | consolidate_reviewed_weapon_roots |
| python | tools/balance/convert_apply_to_scaled_v2.py | convert_apply_to_scaled_v2 |
| python | tools/balance/count_mixed.py | count_mixed |
| python | tools/balance/design_invented_profiles.py | design_invented_profiles |
| python | tools/balance/firepower_consumer_report.py | firepower_consumer_report |
| python | tools/balance/fix_orphan_old_keys.py | fix_orphan_old_keys |
| python | tools/balance/fix_orphan_old_keys_multi.py | fix_orphan_old_keys_multi |
| python | tools/balance/fix_stale_warhead_keys.py | fix_stale_warhead_keys |
| python | tools/balance/gen_derived_stats.py | gen_derived_stats |
| python | tools/balance/gen_effects.py | gen_effects |
| python | tools/balance/gen_projectiles.py | gen_projectiles |
| python | tools/balance/harvester_table.py | harvester_table |
| python | tools/balance/measure_retrofit_gap.py | measure_retrofit_gap |
| python | tools/balance/plan_firepower_retirement.py | plan_firepower_retirement |
| python | tools/balance/plan_warhead_collapse.py | plan_warhead_collapse |
| python | tools/balance/preview_bell.py | preview_bell |
| python | tools/balance/remove_dead_weapons.py | remove_dead_weapons |
| python | tools/balance/rename_3way_underscore.py | rename_3way_underscore |
| python | tools/balance/report_versus_change.py | report_versus_change |
| python | tools/balance/retained_firepower_survey.py | retained_firepower_survey |
| python | tools/balance/retrofit_legacy_template.py | retrofit_legacy_template |
| python | tools/balance/retrofit_weapon_family.py | retrofit_weapon_family |
| python | tools/balance/run_with_guard.py | run_with_guard |
| python | tools/balance/seed_design.py | seed_design |
| python | tools/balance/shield_uniqueness.py | shield_uniqueness |
| python | tools/balance/splice_templates.py | splice_templates |
| python | tools/balance/strip_orphan_report.py | strip_orphan_report |
| python | tools/balance/strip_weapon_versus.py | strip_weapon_versus |
| python | tools/balance/sweep_areadamage.py | sweep_areadamage |
| python | tools/balance/synthesize_reference.py | synthesize_reference |
| python | tools/balance/tier_chain.py | tier_chain |
| python | tools/balance/verify_generator_sync.py | verify_generator_sync |
| python | tools/balance/verify_retrofit.py | verify_retrofit |
| python | tools/packs/extract_shared.py | extract_shared |
| python | tools/packs/split_faction.py | split_faction |
| python | tools/rename/apply_ra1_legacy.py | apply_ra1_legacy |
| python | tools/rename/convert_maps.py | convert_maps |
| python | tools/rename/curate_map.py | curate_map |
| python | tools/rename/safe_rename.py | safe_rename |


## FAIL

- T3: 267 untested > baseline 224

