# audit_upstream_adoption — upstream mod types Cameo already has, and what is new

Cameo resolves **1103** yaml-visible type names across 7 assemblies.

| mod | types | already in Cameo | same mechanic, other name | candidates | of the candidates |
|---|--:|--:|--:|--:|---|
| Romanov's Vengeance | 26 | 11 | 8 | 7 | 6 used in its own yaml |
| Shattered Paradise | 46 | 7 | 7 | 32 | 31 used in its own yaml |
| Crystallized Nexus | 107 | 5 | 2 | 100 | 90 used in its own yaml |
| Combined Arms | 348 | 182 | 35 | 131 | 119 used in its own yaml |
| Generals Alpha | 23 | 2 | 1 | 20 | 20 used in its own yaml |

## Romanov's Vengeance — `OpenRA.Mods.RA2`

⛔ **Already implemented here under another name — read before porting:**

A `[Desc]` match is EVIDENCE, not proof, and it misleads in both directions. `LeaveSmudgeSP` repeats Common `LeaveSmudge`'s description word for word and is a genuine SUPERSET of it — smudge levels, ring size, a max level, and its own `SmudgeLayerSP`. Read both implementations before concluding either way.

| upstream type | Cameo already has | evidence |
|---|---|---|
| `AffectedByTemporal` | `Warpable (OpenRA.Mods.CA)` | read both, same mechanic |
| `AttackInfectRV` | `AttackInfect, AttackLeap, AttackInfectCA` | identical `[Desc]` text |
| `BallisticMissileOld` | `BallisticMissileCA, MissileBase` | identical `[Desc]` text |
| `InfectableRV` | `Infectable, InfectableCA` | identical `[Desc]` text |
| `MissileSpawnerOldMaster` | `MissileSpawnerMaster, MissileSpawnerMasterCA` | identical `[Desc]` text |
| `MissileSpawnerOldSlave` | `MissileSpawnerSlave` | read both, same mechanic |
| `Temporal` | `WarpDamage (OpenRA.Mods.CA)` | read both, same mechanic |
| `WithIdleRepairOverlay` | `WithRepairOverlay` | identical `[Desc]` text |

**6 of 7** candidates are used by the mod's own rules (the rest are dead code there too, and are not worth porting first).

| type | file | uses in its yaml |
|---|---|--:|
| `CaptureSound` | `Traits/Sound/CaptureSound.cs` | 3 |
| `WithSupportPowerChargedOverlay` | `Traits/Render/WithSupportPowerChargedOverlay.cs` | 3 |
| `ColorAlphaFlashPaletteEffect` | `PaletteEffects/ColorAlphaFlashPaletteEffect.cs` | 1 |
| `GrantConditionOnOwnerLost` | `Traits/Conditions/GrantConditionOnOwnerLost.cs` | 1 |
| `SpawnBuildingOrWeapon` | `Warheads/SpawnBuildingOrWeaponWarhead.cs` | 1 |
| `WithAcceptDeliveredCashSound` | `Traits/WithAcceptDeliveredCashSound.cs` | 1 |
| `LegacySpread` | `Warheads/LegacySpreadWarhead.cs` | 0 |

## Shattered Paradise — `OpenRA.Mods.Sp`

⛔ **Already implemented here under another name — read before porting:**

A `[Desc]` match is EVIDENCE, not proof, and it misleads in both directions. `LeaveSmudgeSP` repeats Common `LeaveSmudge`'s description word for word and is a genuine SUPERSET of it — smudge levels, ring size, a max level, and its own `SmudgeLayerSP`. Read both implementations before concluding either way.

| upstream type | Cameo already has | evidence |
|---|---|---|
| `GradientColorsPalette` | `FixedColorPalette, PlayerColorPalette` | identical `[Desc]` text |
| `HarvesterBotModuleSP` | `HarvesterBotModule, HarvesterBotModuleCA` | identical `[Desc]` text |
| `LeaveSmudgeSP` | `LeaveSmudge` | identical `[Desc]` text |
| `McvManagerSPBotModule` | `McvManagerASBotModule` | identical `[Desc]` text |
| `MinelayerBotModuleSP` | `MinelayerBotModule` | identical `[Desc]` text |
| `WithProductionDoorOverlaySP` | `WithProductionDoorOverlay, WithProductionDoorOverlayCA` | identical `[Desc]` text |
| `WithRandomIdleOverlay` | `WithIdleOverlay` | identical `[Desc]` text |

**31 of 32** candidates are used by the mod's own rules (the rest are dead code there too, and are not worth porting first).

| type | file | uses in its yaml |
|---|---|--:|
| `ExplodesAlsoTransported` | `Traits/ExplodesAlsoTransported.cs` | 112 |
| `LoadPaletteWithLightModifiedAndRBGSwapped` | `Traits/Palettes/LoadPaletteWithLightModifiedAndRBGSwapped.cs` | 66 |
| `ProjetcileHusk` | `Projectiles/ProjetcileHusk.cs` | 56 |
| `SpawnHuskEffectOnDeath` | `Traits/SpawnHuskEffectOnDeath.cs` | 47 |
| `SpawnSparks` | `Traits/SpawnSparks.cs` | 28 |
| `SpreadDamageWithCondition` | `Warheads/SpreadDamageWithConditionWarhead.cs` | 24 |
| `VoiceAnnouncementOnProductionExit` | `Traits/Sound/VoiceAnnouncementOnProductionExit.cs` | 8 |
| `WithSupportPowerActivationExplodeWeapon` | `Traits/WithSupportPowerActivationExplodeWeapon.cs` | 6 |
| `WithDisposedAnimation` | `Traits/Render/WithDisposedAnimation.cs` | 5 |
| `ForceFireAtLocation` | `Traits/ForceFireAtLocation.cs` | 4 |
| `ScrinEssenceHit` | `Warheads/ScrinEssenceHitWarhead.cs` | 4 |
| `WithMakeExplodeWeapon` | `Traits/WithMakeExplodeWeapon.cs` | 4 |
| `AddCashCheater` | `Traits/AddCashCheater.cs` | 3 |
| `AreaBeamSP` | `Projectiles/AreaBeamSP.cs` | 3 |
| `CashCheater` | `Traits/Player/CashCheater.cs` | 3 |
| `DamageOnCreation` | `Traits/DamageOnCreation.cs` | 3 |
| `FirestromSP` | `Traits/FirestromSP.cs` | 3 |
| `AutoDemolisher` | `Traits/AutoDemolisher.cs` | 2 |
| `WeaponWeather` | `Traits/World/WeaponWeather.cs` | 2 |
| `ArmamentsChargeBar` | `Traits/ArmamentsChargeBar.cs` | 1 |
| `ChangeSharedPassengerHealth` | `Traits/Player/ChangeSharedPassengerHealth.cs` | 1 |
| `CloudSpawner` | `Traits/World/CloudSpawner.cs` | 1 |
| `GrantConditionOnExploredMap` | `Traits/GrantConditionOnExploredMap.cs` | 1 |
| `GrantConditionOnShortGame` | `Traits/GrantConditionOnShortGame.cs` | 1 |
| `MadTankSP` | `Traits/MadTankSP.cs` | 1 |
| `PaletteFromPaletteWithLightModifiedAndRBGSwapped` | `Traits/Palettes/PaletteFromPaletteWithLightModifiedAndRBGSwapped.cs` | 1 |
| `RevealsShroudToParentOwner` | `Traits/RevealsShroudToParentOwner.cs` | 1 |
| `SmudgeLayerSP` | `Traits/World/SmudgeLayerSP.cs` | 1 |
| `SpawnActorsOnCorpseInRadius` | `Traits/SpawnActorsOnCorpseInRadius.cs` | 1 |
| `SpawnCorpseOnDeath` | `Traits/SpawnCorpseOnDeath.cs` | 1 |
| `UnpackBaseBotModule` | `Traits/BotModules/UnpackBaseBotModule.cs` | 1 |
| `HasCondition` | `Traits/DebugHack/HasCondition.cs` | 0 |

## Crystallized Nexus — `.modsdk/OpenRA.Mods.CN`

⛔ **Already implemented here under another name — read before porting:**

A `[Desc]` match is EVIDENCE, not proof, and it misleads in both directions. `LeaveSmudgeSP` repeats Common `LeaveSmudge`'s description word for word and is a genuine SUPERSET of it — smudge levels, ring size, a max level, and its own `SmudgeLayerSP`. Read both implementations before concluding either way.

| upstream type | Cameo already has | evidence |
|---|---|---|
| `CNBaseBuilderBotModule` | `BaseBuilderBotModule, BaseBuilderBotModuleCA` | identical `[Desc]` text |
| `CNMcvExpansionManagerBotModule` | `McvExpansionManagerBotModule` | identical `[Desc]` text |

**90 of 100** candidates are used by the mod's own rules (the rest are dead code there too, and are not worth porting first).

| type | file | uses in its yaml |
|---|---|--:|
| `CNHealth` | `Traits/Player/CNHealth.cs` | 223 |
| `BotCapabilities` | `Traits/BotCapabilities.cs` | 94 |
| `SecondaryHealth` | `Traits/Player/SecondaryHealth.cs` | 26 |
| `CNWithVoxelBody` | `Traits/Render/CNWithVoxelBody.cs` | 16 |
| `TerrainTileOverlay` | `Traits/World/TerrainTileOverlay.cs` | 16 |
| `SparkBurst` | `Warheads/SparkBurstWarhead.cs` | 15 |
| `CNWithVoxelTurret` | `Traits/Render/CNWithVoxelTurret.cs` | 11 |
| `CNWithVoxelBarrel` | `Traits/Render/CNWithVoxelBarrel.cs` | 10 |
| `VoxelDynamics` | `Traits/Render/VoxelDynamics.cs` | 9 |
| `CNBotProfileBotModule` | `Traits/BotModules/CNBotProfileBotModule.cs` | 7 |
| `ExplodeResource` | `Warheads/ExplodeResourceWarhead.cs` | 6 |
| `ProjectileHusk` | `Projectiles/ProjectileHusk.cs` | 6 |
| `CNSquadManagerBotModule` | `Traits/BotModules/Squads/CNSquadManagerBotModule.cs` | 5 |
| `WithWaterReflection` | `Traits/Render/WithWaterReflection.cs` | 5 |
| `CNAircraftFallsToEarth` | `Traits/Air/CNAircraftFallsToEarth.cs` | 4 |
| `CNLaserZap` | `Projectiles/CNLaserZap.cs` | 4 |
| `DamageSmoke` | `Traits/Render/DamageSmoke.cs` | 4 |
| `SpawnActorOnDamage` | `Traits/SpawnActorOnDamage.cs` | 4 |
| `TerrainDeformation` | `Warheads/TerrainDeformationWarhead.cs` | 4 |
| `CNHarvester` | `Traits/CNHarvester.cs` | 3 |
| `CNUnitBuilderBotModule` | `Traits/BotModules/CNUnitBuilderBotModule.cs` | 3 |
| `CNWithVoxelUnloadBody` | `Traits/Render/CNWithVoxelUnloadBody.cs` | 3 |
| `CharredPalette` | `Traits/Render/CharredPalette.cs` | 3 |
| `HuskFacing` | `Traits/HuskFacing.cs` | 3 |
| `PeriodicSpriteEffect` | `Traits/Render/PeriodicSpriteEffect.cs` | 3 |
| `VoxelDebrisOnDeath` | `Traits/VoxelDebrisOnDeath.cs` | 3 |
| `VoxelShadowSmoothing` | `Traits/Render/VoxelShadowSmoothing.cs` | 3 |
| `CNDestroyableCliff` | `Traits/CNDestroyableCliff.cs` | 2 |
| `CallProtectorsOnDamage` | `Traits/CallProtectorsOnDamage.cs` | 2 |
| `FormationMove` | `Traits/Player/FormationMove.cs` | 2 |
| `HeightAdvantageBonus` | `Traits/HeightAdvantageBonus.cs` | 2 |
| `IonStormDamage` | `Traits/World/IonStormDamage.cs` | 2 |
| `KeepNearActors` | `Traits/KeepNearActors.cs` | 2 |
| `RandomMapAmbientSound` | `Traits/World/RandomMapAmbientSound.cs` | 2 |
| `RandomTransformsNearResources` | `Traits/RandomTransformsNearResources.cs` | 2 |
| `RestoresInfantrySquads` | `Traits/RestoresInfantrySquads.cs` | 2 |
| `SpawnActorOnTimer` | `Traits/SpawnActorOnTimer.cs` | 2 |
| `AnnounceOnCondition` | `Traits/AnnounceOnCondition.cs` | 1 |
| `AtmosphericGradingRenderer` | `Traits/World/AtmosphericGradingRenderer.cs` | 1 |
| `BloomGlowEffect` | `Traits/World/BloomGlowEffect.cs` | 1 |
| `BotPlayerNames` | `Traits/Player/BotPlayerNames.cs` | 1 |
| `CNBaseOverlay` | `Traits/CNBaseOverlay.cs` | 1 |
| `CNBridgeRepairBotModule` | `Traits/BotModules/CNBridgeRepairBotModule.cs` | 1 |
| `CNCliffDemolitionBotModule` | `Traits/BotModules/CNCliffDemolitionBotModule.cs` | 1 |
| `CNCombatSignalReporter` | `Traits/CNCombatSignalReporter.cs` | 1 |
| `CNDestroyableCliffLayer` | `Traits/World/CNDestroyableCliffLayer.cs` | 1 |
| `CNDynamicMusicController` | `Traits/World/CNDynamicMusicController.cs` | 1 |
| `CNGarrisonBotModule` | `Traits/BotModules/CNGarrisonBotModule.cs` | 1 |
| `CNHandicapDamageMultiplier` | `Traits/Player/CNHandicapDamageMultiplier.cs` | 1 |
| `CNHandicapFirepowerMultiplier` | `Traits/Player/CNHandicapFirepowerMultiplier.cs` | 1 |
| `CNHandicapIncomeMultiplier` | `Traits/Player/CNHandicapIncomeMultiplier.cs` | 1 |
| `CNHandicapProductionTimeMultiplier` | `Traits/Player/CNHandicapProductionTimeMultiplier.cs` | 1 |
| `CNHarvesterBotModule` | `Traits/BotModules/CNHarvesterBotModule.cs` | 1 |
| `CNLeavesPitOnDeath` | `Traits/CNLeavesPitOnDeath.cs` | 1 |
| `CNOffsetSpriteSequenceShadow` | `Traits/Render/CNOffsetSpriteSequenceShadow.cs` | 1 |
| `CNProductionQueueFromSelection` | `Traits/Player/CNProductionQueueFromSelection.cs` | 1 |
| `CNRegionManagerBotModule` | `Traits/BotModules/CNRegionManagerBotModule.cs` | 1 |
| `CNRepairManagerBotModule` | `Traits/BotModules/CNRepairManagerBotModule.cs` | 1 |
| `CNResourceMapBotModule` | `Traits/BotModules/CNResourceMapBotModule.cs` | 1 |
| `CNTacticalMapBotModule` | `Traits/BotModules/CNTacticalMapBotModule.cs` | 1 |
| `CNTacticalMapOverlay` | `Traits/CNTacticalMapOverlay.cs` | 1 |
| `CNVeinholeAssaultBotModule` | `Traits/BotModules/CNVeinholeAssaultBotModule.cs` | 1 |
| `CNWindSway` | `Traits/Render/CNWindSway.cs` | 1 |
| `CNWithVoxelWalkerBody` | `Traits/Render/CNWithVoxelWalkerBody.cs` | 1 |
| `CombatAnalysisBotModule` | `Traits/BotModules/CombatAnalysisBotModule.cs` | 1 |
| `CombatChatter` | `Traits/CombatChatter.cs` | 1 |
| `DayNightCycle` | `Traits/World/DayNightCycle.cs` | 1 |
| `DeployBotModule` | `Traits/BotModules/DeployBotModule.cs` | 1 |
| `ExploresMapOnOwnerChange` | `Traits/ExploresMapOnOwnerChange.cs` | 1 |
| `FaceTurretOnOrder` | `Traits/FaceTurretOnOrder.cs` | 1 |
| `FadeOut` | `Traits/FadeOut.cs` | 1 |
| `ForestCoverSource` | `Traits/World/ForestCoverSystem.cs` | 1 |
| `ForestCoverSystem` | `Traits/World/ForestCoverSystem.cs` | 1 |
| `MobSquadSelectionDecoration` | `Traits/MobSpawner/MobSquadSelectionDecoration.cs` | 1 |
| `PlacesPavement` | `Traits/Player/PlacesPavement.cs` | 1 |
| `PlayerDefeatedAnnouncer` | `Traits/Player/PlayerDefeatedAnnouncer.cs` | 1 |
| `RandomTransformsNearResourcesManager` | `Traits/RandomTransformsNearResources.cs` | 1 |
| `RepairableInBarracks` | `Traits/RepairableInBarracks.cs` | 1 |
| `Scatterer` | `Traits/Scatterer.cs` | 1 |
| `SubgroupIcon` | `Traits/Player/SubgroupIcon.cs` | 1 |
| `TerrainDeformationOptions` | `Warheads/TerrainDeformationWarhead.cs` | 1 |
| `TerrainTileAmbientSound` | `Traits/World/TerrainTileAmbientSound.cs` | 1 |
| `TiberiumGlowRenderer` | `Traits/World/TiberiumGlowRenderer.cs` | 1 |
| `WaterOverlayRenderer` | `Traits/World/WaterOverlayRenderer.cs` | 1 |
| `WaterReflectionRenderer` | `Traits/World/WaterReflectionRenderer.cs` | 1 |
| `WaterSparkleRenderer` | `Traits/World/WaterSparkleRenderer.cs` | 1 |
| `WeatherController` | `Traits/World/WeatherController.cs` | 1 |
| `WeatherProfile` | `Traits/World/WeatherProfile.cs` | 1 |
| `WeatherTintEffect` | `Traits/World/WeatherTintEffect.cs` | 1 |
| `WorldCloudShadow` | `Traits/World/WorldCloudShadow.cs` | 1 |
| `AlphaGradientPalette` | `Traits/Render/AlphaGradientPalette.cs` | 0 |
| `CNSlot` | `Traits/BotModules/Squads/CNSquadManagerBotModule.cs` | 0 |
| `CNSquadNeedRule` | `Traits/BotModules/Squads/CNSquadManagerBotModule.cs` | 0 |
| `CNSteeredMobile` | `Traits/Movement/CNSteeredMobile.cs` | 0 |
| `CNTeamTemplate` | `Traits/BotModules/Squads/CNSquadManagerBotModule.cs` | 0 |
| `CloudShadowRenderer` | `Traits/World/CloudShadowRenderer.cs` | 0 |
| `CloudSpawner` | `Traits/World/CloudSpawner.cs` | 0 |
| `ResourceAnimationOverlay` | `Traits/World/ResourceAnimationOverlay.cs` | 0 |
| `TerrainAnimationOverlay` | `Traits/World/TerrainAnimationOverlay.cs` | 0 |
| `WaterEffectReflectionRenderer` | `Traits/World/WaterEffectReflectionRenderer.cs` | 0 |

## Combined Arms — `OpenRA.Mods.CA`

⛔ **Already implemented here under another name — read before porting:**

A `[Desc]` match is EVIDENCE, not proof, and it misleads in both directions. `LeaveSmudgeSP` repeats Common `LeaveSmudge`'s description word for word and is a genuine SUPERSET of it — smudge levels, ring size, a max level, and its own `SmudgeLayerSP`. Read both implementations before concluding either way.

| upstream type | Cameo already has | evidence |
|---|---|---|
| `AutoGuard` | `GuardsSelection` | identical `[Desc]` text |
| `ClassicProductionQueueCA` | `BulkProductionQueue, ClassicParallelProductionQueue, ClassicProductionQueue` | identical `[Desc]` text |
| `EjectOnTransform` | `EjectOnDeath` | identical `[Desc]` text |
| `FireClusterCA` | `FireCluster` | identical `[Desc]` text |
| `FreeActorCA` | `FreeActor, FreeActorWithCondition` | identical `[Desc]` text |
| `FrozenUnderFogUpdatedByGpsRadar` | `FrozenUnderFogUpdatedByGpsAS, FrozenUnderFogUpdatedByGps` | identical `[Desc]` text |
| `GivesBountyCA` | `GivesBounty` | identical `[Desc]` text |
| `GivesCashOnCaptureCA` | `GivesCashOnCapture` | identical `[Desc]` text |
| `GrantConditionOnDamageStateCA` | `GrantConditionOnDamageState, AnnounceOnDamageState` | identical `[Desc]` text |
| `GrantConditionOnDeployTurreted` | `GrantConditionOnDeploy, HeliGrantConditionOnDeploy` | identical `[Desc]` text |
| `GrantConditionOnLobbyOption` | `GrantConditionOnFogEnabled` | identical `[Desc]` text |
| `GrantExternalConditionCA` | `GrantExternalCondition` | identical `[Desc]` text |
| `GrantPrerequisiteChargeDrainPowerCA` | `GrantPrerequisiteChargeDrainPower` | identical `[Desc]` text |
| `HealthPercentageSpreadDamage` | `SpreadDamage` | identical `[Desc]` text |
| `Infiltrate` | `Dummy` | identical `[Desc]` text |
| `PeriodicExplosionOnSlaves` | `PeriodicExplosion` | identical `[Desc]` text |
| `ProduceActorPowerCA` | `ProduceActorPower, PeriodicProducer, PeriodicProducerCA` | identical `[Desc]` text |
| `ProximityExternalConditionCA` | `ProximityExternalCondition` | identical `[Desc]` text |
| `RailgunCA` | `Railgun` | identical `[Desc]` text |
| `RenderLine` | `WithDisguiseTargetPalette` | identical `[Desc]` text |
| `SeedsResourceCA` | `SeedsResource` | identical `[Desc]` text |
| `SpawnActorOnDeathCA` | `SpawnActorOnDeath, SpawnRandomActorOnDeath` | identical `[Desc]` text |
| `SpawnActorPowerCA` | `SpawnActorPower` | identical `[Desc]` text |
| `SpawnActorsOnSellCA` | `SpawnActorsOnSell` | identical `[Desc]` text |
| `SpawnRandomActor` | `SpawnActor` | identical `[Desc]` text |
| `SpawnerMasterBase` | `BaseSpawnerMaster, CarrierMaster, MobSpawnerMaster` | identical `[Desc]` text |
| `SpawnerSlaveBase` | `BaseSpawnerSlave` | identical `[Desc]` text |
| `StoresPlayerResourcesCA` | `StoresPlayerResources` | identical `[Desc]` text |
| `TargetSpecificOrderVoice` | `ValidFactions` | identical `[Desc]` text |
| `UnitConverter` | `ReflectsDamage` | identical `[Desc]` text |
| `WaitsForTurretAlignmentOnUndeploy` | `WithDisguiseTargetPalette` | identical `[Desc]` text |
| `WarpPercentDamage` | `WarpDamage` | identical `[Desc]` text |
| `WithEnterExitWorldOverlay` | `WithMakeOverlay` | identical `[Desc]` text |
| `WithReloadBar` | `WithDisguiseTargetPalette` | identical `[Desc]` text |
| `WithUnitConverterCountDecoration` | `WithTextDecoration` | identical `[Desc]` text |

**119 of 131** candidates are used by the mod's own rules (the rest are dead code there too, and are not worth porting first).

| type | file | uses in its yaml |
|---|---|--:|
| `EncyclopediaExtras` | `Traits/EncyclopediaExtras.cs` | 364 |
| `MissileCA` | `Projectiles/MissileCA.cs` | 103 |
| `LobbyMissionInfo` | `Traits/World/LobbyMissionInfo.cs` | 58 |
| `Upgradeable` | `Traits/Upgradeable.cs` | 48 |
| `AirstrikePowerCA` | `Traits/SupportPowers/AirstrikePowerCA.cs` | 39 |
| `InfiltrateToCreateProxyActor` | `Traits/Infiltration/InfiltrateToCreateProxyActor.cs` | 35 |
| `ParatroopersPowerCA` | `Traits/SupportPowers/ParatroopersPowerCA.cs` | 26 |
| `DummyConditionConsumer` | `Traits/Conditions/DummyConditionConsumer.cs` | 23 |
| `GpsRadarDot` | `Traits/GPSRadarDot.cs` | 21 |
| `ImmobileMultiCell` | `Traits/ImmobileMultiCell.cs` | 21 |
| `GivesExperienceCA` | `Traits/GivesExperienceCA.cs` | 18 |
| `Upgrade` | `Traits/Player/UpgradesManager.cs` | 17 |
| `RangedGpsRadarProvider` | `Traits/RangedGpsRadarProvider.cs` | 16 |
| `SoundOnDamageTransitionCA` | `Traits/Sound/SoundOnDamageTransitionCA.cs` | 16 |
| `SpawnActorOnMindControlled` | `Traits/SpawnActorOnMindControlled.cs` | 14 |
| `WithEjectedCasings` | `Traits/WithEjectedCasings.cs` | 12 |
| `TurretedFloating` | `Traits/TurretedFloating.cs` | 11 |
| `BulletCA` | `Projectiles/BulletCA.cs` | 10 |
| `CargoBlocked` | `Traits/CargoBlocked.cs` | 10 |
| `Convertible` | `Traits/Convertible.cs` | 10 |
| `DummyConditionGranter` | `Traits/Conditions/DummyConditionGranter.cs` | 10 |
| `GrantConditionIfOwnerIsNeutral` | `Traits/Conditions/GrantConditionIfOwnerIsNeutral.cs` | 10 |
| `SpawnActorAbility` | `Traits/SpawnActorAbility.cs` | 9 |
| `UpdatesSupportPowerTimer` | `Traits/UpdatesSupportPowerTimer.cs` | 9 |
| `WithPreviewDecoration` | `Traits/Render/WithPreviewDecoration.cs` | 9 |
| `WithRadiatingCircle` | `Traits/Render/WithRadiatingCircle.cs` | 9 |
| `CreateProxyActorForAllies` | `Traits/CreateProxyActorForAllies.cs` | 8 |
| `FlatHealthDamageMultiplier` | `Traits/Multipliers/FlatHealthDamageMultiplier.cs` | 8 |
| `GrantConditionToAttached` | `Traits/Conditions/GrantConditionToAttached.cs` | 7 |
| `ArmamentBurstCounter` | `Traits/ArmamentBurstCounter.cs` | 6 |
| `AttackOrderPowerCA` | `Traits/SupportPowers/AttackOrderPowerCA.cs` | 6 |
| `DummyGpsPower` | `Traits/SupportPowers/DummyGpsPower.cs` | 6 |
| `AreaBeamCA` | `Projectiles/AreaBeamCA.cs` | 5 |
| `ReclaimsExperience` | `Traits/ReclaimsExperience.cs` | 5 |
| `TargetedLeapAbility` | `Traits/TargetedLeapAbility.cs` | 5 |
| `CargoCloner` | `Traits/CargoCloner.cs` | 4 |
| `DamagedByTerrainCA` | `Traits/DamagedByTerrainCA.cs` | 4 |
| `GrantConditionOnResupply` | `Traits/Conditions/GrantConditionOnResupply.cs` | 4 |
| `GrantConditionOnResupplying` | `Traits/Conditions/GrantConditionOnResupplying.cs` | 4 |
| `TimedConditionBarCA` | `Traits/Render/TimedConditionBarCA.cs` | 4 |
| `ValueScalingFirepowerMultiplier` | `Traits/Multipliers/ValueScalingFirepowerMultiplier.cs` | 4 |
| `WithFlashEffect` | `Traits/Render/WithFlashEffect.cs` | 4 |
| `AutoDeployer` | `Traits/AutoDeployer.cs` | 3 |
| `ChronoshiftPowerCA` | `Traits/SupportPowers/ChronoshiftPowerCA.cs` | 3 |
| `ClassicAirstrikePower` | `Traits/SupportPowers/ClassicAirstrikePower.cs` | 3 |
| `CrateCA` | `Traits/CrateCA.cs` | 3 |
| `EncyclopediaColorPalette` | `Traits/Palettes/EncyclopediaColorPalette.cs` | 3 |
| `InterceptorPower` | `Traits/SupportPowers/InterceptorPower.cs` | 3 |
| `LaysMinefield` | `Traits/LaysMinefield.cs` | 3 |
| `MeteorPower` | `Traits/SupportPowers/MeteorPower.cs` | 3 |
| `OverlayColorPickerPalette` | `Traits/Palettes/OverlayColorPickerPalette.cs` | 3 |
| `ParachuteCargoOnCondition` | `Traits/Conditions/ParachuteCargoOnCondition.cs` | 3 |
| `ProvidesPrerequisitesOnCount` | `Traits/Player/ProvidesPrerequisitesOnCount.cs` | 3 |
| `ProvidesPrerequisitesOnTimeline` | `Traits/Player/ProvidesPrerequisitesOnTimeline.cs` | 3 |
| `RevealActorsPower` | `Traits/SupportPowers/RevealActorsPower.cs` | 3 |
| `SendCashPower` | `Traits/SupportPowers/SendCashPower.cs` | 3 |
| `WithColoredOverlayCA` | `Traits/Modifiers/WithColoredOverlayCA.cs` | 3 |
| `WithLinkedRangeCirclePreview` | `Traits/Render/WithLinkedRangeCirclePreview.cs` | 3 |
| `AirReinforcementsPower` | `Traits/SupportPowers/AirReinforcementsPower.cs` | 2 |
| `AttachActor` | `Warheads/AttachActorWarhead.cs` | 2 |
| `DropPodsPowerCA` | `Traits/SupportPowers/DropPodsPowerCA.cs` | 2 |
| `GivesPlayerExperienceOnCapture` | `Traits/GivesPlayerExperienceOnCapture.cs` | 2 |
| `GpsRadarProvider` | `Traits/SupportPowers/GpsRadarProvider.cs` | 2 |
| `IgnoreOutOfRangeAttackOrders` | `Traits/Attack/IgnoreOutOfRangeAttackOrders.cs` | 2 |
| `ImmobilePositionable` | `Traits/ImmobilePositionable.cs` | 2 |
| `InfiltrateForTimedCondition` | `Traits/Infiltration/InfiltrateForTimedCondition.cs` | 2 |
| `LinkedProducerSource` | `Traits/LinkedProducerSource.cs` | 2 |
| `MissileStrikePower` | `Traits/SupportPowers/MissileStrikePower.cs` | 2 |
| `ProjectileHusk` | `Projectiles/ProjectileHusk.cs` | 2 |
| `ProvidesUpgrade` | `Traits/ProvidesUpgrade.cs` | 2 |
| `ReturnsToBaseOnAmmoDepleted` | `Traits/ReturnsToBaseOnAmmoDepleted.cs` | 2 |
| `SeedsResourceMultiplier` | `Traits/Multipliers/SeedsResourceMultiplier.cs` | 2 |
| `SpawnMultiWeaponImpact` | `Warheads/SpawnMultiWeaponImpactWarhead.cs` | 2 |
| `SpeedCapSpeedMultiplier` | `Traits/Multipliers/SpeedCapSpeedMultiplier.cs` | 2 |
| `TriggersProductionDoorOverlay` | `Traits/Render/TriggersProductionDoorOverlay.cs` | 2 |
| `WeatherPaletteEffect` | `Traits/PaletteEffects/WeatherPaletteEffect.cs` | 2 |
| `WithDockingAnimationCA` | `Traits/Render/WithDockingAnimationCA.cs` | 2 |
| `AddsToReclaimableValue` | `Traits/AddsToReclaimableValue.cs` | 1 |
| `AdvancesTimeline` | `Traits/AdvancesTimeline.cs` | 1 |
| `AllyProxyFromSelection` | `Traits/World/AllyProxyFromSelection.cs` | 1 |
| `AutoDeployManager` | `Traits/Player/AutoDeployManager.cs` | 1 |
| `CampaignProgressTracker` | `Traits/Player/CampaignProgressTracker.cs` | 1 |
| `CancelActivityOnPickup` | `Traits/CancelActivityOnPickup.cs` | 1 |
| `CashHackPower` | `Traits/SupportPowers/CashHackPower.cs` | 1 |
| `ConvertsResources` | `Traits/ConvertsResources.cs` | 1 |
| `CreateFacingEffect` | `Warheads/CreateFacingEffectWarhead.cs` | 1 |
| `FallsDownAndTransforms` | `Traits/Air/FallsDownAndTransforms.cs` | 1 |
| `GpsRadarWatcher` | `Traits/GpsRadarWatcher.cs` | 1 |
| `GrantConditionOnPlayerFunds` | `Traits/Conditions/GrantConditionOnPlayerFunds.cs` | 1 |
| `GrantTimedConditionOnPointDefenseHit` | `Traits/Conditions/GrantTimedConditionOnPointDefenseHit.cs` | 1 |
| `HealthCapDamageMultiplier` | `Traits/Multipliers/HealthCapDamageMultiplier.cs` | 1 |
| `InfiltratePower` | `Traits/SupportPowers/InfiltratePower.cs` | 1 |
| `InheritsExperienceLevelOfMaster` | `Traits/InheritsExperienceLevelOfMaster.cs` | 1 |
| `Interceptor` | `Traits/Air/Interceptor.cs` | 1 |
| `LinkedProducerTarget` | `Traits/LinkedProducerTarget.cs` | 1 |
| `NotificationManager` | `Traits/Player/NotificationManager.cs` | 1 |
| `NotificationOnDamage` | `Traits/NotificationOnDamage.cs` | 1 |
| `PassengerBlocked` | `Traits/PassengerBlocked.cs` | 1 |
| `PlayerBountyPool` | `Traits/Player/PlayerBountyPool.cs` | 1 |
| `PlayerConnectionStatus` | `Traits/Player/PlayerConnectionStatus.cs` | 1 |
| `PlayerExperienceLevels` | `Traits/Player/PlayerExperienceLevels.cs` | 1 |
| `PopController` | `Traits/Player/PopController.cs` | 1 |
| `ProvidesPrerequisiteIfAlliesExist` | `Traits/Player/ProvidesPrerequisiteIfAlliesExist.cs` | 1 |
| `ReclaimableExperiencePool` | `Traits/Player/ReclaimableExperiencePool.cs` | 1 |
| `ReclaimableValueProducer` | `Traits/Player/ReclaimableValueProducer.cs` | 1 |
| `ScriptTriggersCA` | `Scripting/ScriptTriggersCA.cs` | 1 |
| `SquadPathOverlay` | `Traits/SquadPathOverlay.cs` | 1 |
| `StackableSupportPowerManager` | `Traits/Player/StackableSupportPowerManager.cs` | 1 |
| `SupportPowerInstanceManager` | `Traits/Player/SupportPowerInstanceManager.cs` | 1 |
| `TargetedDiveAbility` | `Traits/TargetedDiveAbility.cs` | 1 |
| `TeslaZapCA` | `Projectiles/TeslaZapCA.cs` | 1 |
| `TransferResourcesOnTransform` | `Traits/TransferResourcesOnTransform.cs` | 1 |
| `UndeployOnStop` | `Traits/UndeployOnStop.cs` | 1 |
| `UpgradesManager` | `Traits/Player/UpgradesManager.cs` | 1 |
| `WarheadDebugOverlayCA` | `Traits/WarheadDebugOverlayCA.cs` | 1 |
| `WithDistortionHalo` | `Traits/Render/WithDistortionHalo.cs` | 1 |
| `WithHarvestAnimationCA` | `Traits/Render/WithHarvestAnimationCA.cs` | 1 |
| `WithPrismLinkVisualization` | `Traits/Render/WithPrismLinkVisualization.cs` | 1 |
| `WithSpawnedActorIdentifier` | `Traits/Render/WithSpawnedActorIdentifier.cs` | 1 |
| `CreateDistortionHalo` | `Warheads/CreateDistortionHaloWarhead.cs` | 0 |
| `GrantConditionToSpawnerSlaves` | `Traits/Conditions/GrantConditionToSpawnerSlaves.cs` | 0 |
| `GrantConditionWhileProducing` | `Traits/Conditions/GrantConditionWhileProducing.cs` | 0 |
| `InitiallyHunts` | `Traits/InitiallyHunts.cs` | 0 |
| `LobbyMission` | `Traits/World/LobbyMissionInfo.cs` | 0 |
| `RearmsToUpgrade` | `Traits/RearmsToUpgrade.cs` | 0 |
| `RemoveOnPowerActivation` | `Traits/SupportPowers/RemoveOnPowerActivation.cs` | 0 |
| `ScatterOnExitCargo` | `Traits/ScatterOnExitCargo.cs` | 0 |
| `SpawnHuskEffectOnDeath` | `Traits/SpawnHuskEffectOnDeath.cs` | 0 |
| `SquadRoute` | `Traits/BotModules/Squads/States/GroundStatesCA.cs` | 0 |
| `StackableDirectionalSupportPower` | `Traits/SupportPowers/StackableDirectionalSupportPower.cs` | 0 |
| `TargetedMovementAbility` | `Traits/TargetedMovementAbility.cs` | 0 |

## Generals Alpha — `OpenRA.Mods.GenSDK`

⛔ **Already implemented here under another name — read before porting:**

A `[Desc]` match is EVIDENCE, not proof, and it misleads in both directions. `LeaveSmudgeSP` repeats Common `LeaveSmudge`'s description word for word and is a genuine SUPERSET of it — smudge levels, ring size, a max level, and its own `SmudgeLayerSP`. Read both implementations before concluding either way.

| upstream type | Cameo already has | evidence |
|---|---|---|
| `EmitInfantryOnDeath` | `SpawnActorsOnSell` | identical `[Desc]` text |

**20 of 20** candidates are used by the mod's own rules (the rest are dead code there too, and are not worth porting first).

| type | file | uses in its yaml |
|---|---|--:|
| `LaysMinefield` | `Traits/LaysMinefield.cs` | 20 |
| `SupplyDock` | `Traits/Supply/SupplyDock.cs` | 19 |
| `ConditionIconOverlay` | `Traits/Render/ConditionIconOverlay.cs` | 15 |
| `SupplyCenter` | `Traits/Supply/SupplyCenter.cs` | 5 |
| `WithTerrainDependantSpriteBody` | `Traits/Render/WithTerrainDependantSpriteBody.cs` | 5 |
| `PilotChamber` | `Traits/PilotChamber.cs` | 4 |
| `WithSupplyCollectorPipsDecoration` | `Traits/Render/WithSupplyCollectorPipsDecoration.cs` | 4 |
| `CashHack` | `Warheads/CashHackWarhead.cs` | 3 |
| `InitialBaseAndWorkerBotModule` | `Traits/BotModules/InitialBaseAndWorkerBotModule.cs` | 3 |
| `RadarIcon` | `Traits/Radar/RadarIcon.cs` | 3 |
| `SupplyCollector` | `Traits/Supply/SupplyCollector.cs` | 3 |
| `CashHackPower` | `Traits/SupportPowers/CashHackPower.cs` | 1 |
| `FakePower` | `Traits/SupportPowers/FakePower.cs` | 1 |
| `GeneralCollectorBotModule` | `Traits/BotModules/GeneralCollectorBotModule.cs` | 1 |
| `GrantConditionWhileCollectingSupplies` | `Traits/Supply/GrantConditionWhileCollectingSupplies.cs` | 1 |
| `GrantExternalConditionToAssignedCollectors` | `Traits/Supply/GrantExternalConditionToAssignedCollectors.cs` | 1 |
| `ResupplyDock` | `Traits/Supply/ResupplyDock.cs` | 1 |
| `WithSupplyCollectionOverlay` | `Traits/Render/WithSupplyCollectionOverlay.cs` | 1 |
| `WithSupplyDeliveryAnimation` | `Traits/Render/WithSupplyDeliveryAnimation.cs` | 1 |
| `WithSupplyDeliveryOverlay` | `Traits/Render/WithSupplyDeliveryOverlay.cs` | 1 |

_Informational: adopting upstream code is a maintainer decision, never a gate._
