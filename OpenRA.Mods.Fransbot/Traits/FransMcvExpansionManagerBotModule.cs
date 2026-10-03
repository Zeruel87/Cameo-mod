#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Pathfinder;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public interface IFransAmphibiousExpansionService
	{
		// Broader production-arbitration signal. This becomes true during SEA SUPPLY PRE-COMMIT
		// as soon as PIONEER has proved a concrete same-region LST requirement, before a SeaOre
		// ExpansionTask formally owns the MCV. Capture/GroundTransfer must yield new LST production
		// during this window so the reserved strategic pool slot cannot be stolen.
		bool HasStrategicLandingCraftProductionDemand { get; }
		bool IsLandingCraftPendingForExpansion(Actor craft);
	}

	/// <summary>
	/// Read-only expansion ownership signal for other planners that share production
	/// queues. It exposes state, not strategy: consumers may yield while the MCV
	/// operation owns expansion progression without inspecting its internal stage.
	/// </summary>
	public interface IFransExpansionStateService
	{
		int DesiredPermanentConstructionYards { get; }
		bool CanAcquireConstructionYardSlot { get; }
		bool FirstExpansionRefinerySuspendedForInfrastructure { get; }
		bool MissionCriticalNavalAccessRequired { get; }
		bool NavalCapabilityDemandActive { get; }
		bool NavalProductionOpportunityAvailable { get; }
		bool FirstExpansionRefineryPrebuildAllowed { get; }
		int ProtectedFirstExpansionRefineryRemainingCost { get; }
		bool CriticalMcvProductionDemandActive { get; }
		bool PioneerAirScoutDemandActive { get; }
		IReadOnlyList<CPos> SecureRequiredExpansionObjectives { get; }
		IReadOnlyList<CPos> ReconRequiredExpansionObjectives { get; }
		bool TryGetPioneerReconObjectiveNear(CPos referenceCell, out CPos objectiveCell);
		bool TryGetActiveExpansionReservation(out CPos objective, out CPos deployCell, out uint mcvActorId, out int reservationTick);
		bool TryGetMcvDeployRightOfWay(out CPos center, out int radius);
		bool TryGetNavalProductionLocation(string actorType, out CPos location);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Manages the autonomous Fransbots MCV expansion chain. General SECURE never owns MCV movement; routine land/sea expansion, Cargo-aware capacity, local-safe retreat and physical FACT handoff remain here.")]
	public class FransMcvExpansionManagerBotModuleInfo : ConditionalTraitInfo,
		Requires<ResourceMapBotModuleInfo>, NotBefore<ResourceMapBotModuleInfo>
	{
		[ActorReference]
		[Desc("Actor types that are considered MCVs.")]
		public readonly FrozenSet<string> McvTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Actor types that are considered construction yards.")]
		public readonly FrozenSet<string> ConstructionYardTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Actor types that can produce MCVs.")]
		public readonly FrozenSet<string> McvFactoryTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Landing craft types that may carry an expansion MCV over water.")]
		public readonly FrozenSet<string> LandingCraftTypes = FrozenSet<string>.Empty;

		[Desc("Production queue category used to request landing craft.")]
		public readonly string LandingCraftQueueCategory = "Ship";

		[ActorReference]
		[Desc("Faction-specific naval production structures that can build a requested landing craft.")]
		public readonly FrozenSet<string> LandingCraftProducerTypes = FrozenSet<string>.Empty;

		[Desc("Maximum distance in cells from owned buildable-area providers when placing a naval production structure.",
			"This should match the maximum adjacency of the configured naval structures.")]
		public readonly int LandingCraftProducerSearchRadius = 8;

		[Desc("World ticks a positive or negative shoreline-producer placement result is cached before a full BuildingInfluence/CanPlaceBuilding rescan. This prevents landlocked sea-wait states from repeatedly performing the same expensive placement search.")]
		public readonly int LandingCraftProducerPlacementScanInterval = 1000;

		[Desc("World ticks allowed after placing a completed SPEN/SYRD before the placement must be physically confirmed. Unconfirmed READY naval producers are retried and eventually cancelled so the shared Building queue cannot deadlock.")]
		public readonly int LandingCraftProducerPlacementConfirmTimeoutTicks = 500;

		[Desc("Maximum unconfirmed placement retries for one completed SPEN/SYRD before that stale queue item is cancelled and naval support replans.")]
		public readonly int LandingCraftProducerPlacementMaximumRetries = 4;

		[Desc("Allow proactive first naval-production bootstrap only when Explore Map resource topology proves that at least one known mine/gmine expansion objective is on a different ground landmass from the main FACT and has nearby sea access. Water percentage alone never creates naval demand.")]
		public readonly bool EnableTopologyProvenEarlyNavalBootstrap = true;

		[ActorReference]
		[Desc("Structures that must be physical before proactive water-map naval bootstrap may begin. AirAI uses FIX so the deterministic opening WEAP -> FIX sequence remains intact; Navy then gains priority before secondary WEAP growth.")]
		public readonly FrozenSet<string> EarlyNavalOpeningCompletionTypes = FrozenSet<string>.Empty;

		[Desc("Maximum distance in cells from a temporary coastal staging FACT to a native-passable LST handoff. Used only when an LST is required but no SPEN/SYRD can be placed from the current base footprint.")]
		public readonly int CoastalStagingShoreRadius = 10;

		[Desc("Maximum number of nearest coastal FACT candidates that receive expensive RiskModel/BuildingInfluence/path evaluation when creating temporary naval staging. A cheap mobility shortlist is evaluated first.")]
		public readonly int CoastalStagingMaximumCandidates = 24;

		[Desc("World ticks a temporary coastal staging FACT may remain with no naval-producer queue progress before it repacks and retries another coast. Queued/current Building work counts as progress, so the watchdog only breaks a genuine no-placement deadlock.")]
		public readonly int CoastalStagingNavalProducerTimeoutTicks = 2000;

		[Desc("Maximum failed coastal-staging FACT attempts for one support episode before the MCV releases naval bootstrap, returns to ordinary PIONEER duty, and waits for the normal expansion-area cooldown before another try.")]
		public readonly int CoastalStagingMaximumFailedAttempts = 4;

		[Desc("Minimum world ticks a suspended first-expansion PROC reservation stays yielded after naval infrastructure takes the shared Building queue. This bridges order-processing latency so a cancelled READY PROC cannot be immediately re-reserved before SPEN/SYRD production becomes visible.")]
		public readonly int FirstExpansionRefineryInfrastructureSuspensionGraceTicks = 250;

		[ActorReference]
		[Desc("Static resource-creator actors that are legitimate expansion objectives from match start when Explore Map is enabled. Only their map-start type/location is remembered; hidden dynamic ownership is never queried.")]
		public readonly FrozenSet<string> ExploredMapResourceObjectiveTypes = FrozenSet<string>.Empty;

		[Desc("Resource fields within this many cells of a map-start Explore-Map mine/gmine count as the same legitimate resource objective. If no ore cells exist yet, the static mine/gmine location itself may seed an expansion objective.")]
		public readonly int ExploredMapResourceObjectiveRadius = 12;

		[Desc("Minimum combined cash and resources before requesting an LST for an identified sea expansion.")]
		public readonly int MinimumCashForSeaTransport = 2000;
		[Desc("Ticks between expensive amphibious planning passes.")]
		public readonly int SeaPlanningInterval = 250;

		[Desc("World ticks between unified RiskModel route rechecks while an LST carries an expansion MCV.")]
		public readonly int SeaRouteRiskRecheckInterval = 125;

		[Desc("Ticks between repeated external requests for a landing craft.")]
		public readonly int SeaTransportRequestCooldown = 750;

		[Desc("Maximum time a committed MCV sea expansion may remain in WaitingForSeaTransport without a physical LST or a real queued LST build. At expiry feasibility is rechecked; an impossible/stalled ferry objective is released for normal replanning.")]
		public readonly int SeaTransportFeasibilityWatchdogTicks = 1500;

		[Desc("Absolute maximum WaitingForSeaTransport time for one committed sea objective. Correct-region queued production may satisfy the shorter feasibility watchdog, but it can never keep an MCV pinned indefinitely. 0 disables the absolute cap.")]
		public readonly int SeaTransportAbsoluteWaitWatchdogTicks = 4500;

		[Desc("Maximum number of otherwise-unreachable ore fields examined by amphibious planning.")]
		public readonly int MaximumSeaOreFieldCandidates = 3;

		[Desc("bounded sea planner: maximum expensive ore candidates processed in one simulation pass. Remaining candidates continue on later passes without changing target ranking.")]
		public readonly int RoutineSeaOreCandidatesPerPlanningPass = 1;

		[Desc("Within one routine SeaOre candidate, maximum ranked landing handoffs whose exit/path proof may be advanced in one simulation pass. This splits a single expensive candidate across ticks instead of allowing one target to spend the full landing search budget at once.")]
		public readonly int RoutineSeaOreLandingBeachesPerPlanningPass = 1;

		[Desc("Maximum truly expensive MCV exit-to-deploy path proofs advanced in one routine SeaOre planning pass. Empty/blocked handoffs may be skipped cheaply, but native pathfinding is explicitly time-sliced.")]
		public readonly int RoutineSeaOreExitPathProofsPerPlanningPass = 1;

		[Desc("Maximum native MCV pickup path proofs advanced in one sea-proof pass. Each proof may target all legal land cells in one StrategicMap handoff, so adjacent-cell alternatives remain exact without an unbounded per-tick loop.")]
		public readonly int SeaPickupPathProofsPerPlanningPass = 1;

		[Desc("Ticks between passes while a committed ferry-corridor recovery is active. Recovery is incremental but must advance faster than the ordinary sea-planning cooldown so its finite proof budget can terminate before the absolute watchdog.")]
		public readonly int CommittedSeaCorridorRecoveryInterval = 25;

		[Desc("Maximum bounded proof passes for one committed ferry-corridor recovery. The runtime limit is reduced further when the remaining absolute-watchdog lifetime cannot accommodate this many passes.")]
		public readonly int CommittedSeaCorridorRecoveryMaximumPasses = 64;

		[Desc("World ticks to reuse a completed routine sea-target search while the MCV has not materially moved. Keeps repeated no-result checks cheap without making stale results persistent.")]
		public readonly int RoutineSeaOreSearchCacheDuration = 750;

		[Desc("Short retry memory for a future FACT->PROC placement proof that currently has no legal refinery footprint. This is intentionally shorter than a real failed refinery-site cooldown because mobile blockers/world state may change before the MCV commits.")]
		public readonly int FutureRefineryProofRetryDelay = 250;

		[Desc("Maximum MCV movement in cells before an in-progress/completed bounded routine sea-target search is discarded and rebuilt.")]
		public readonly int RoutineSeaOreSearchMovementTolerance = 6;

		[Desc("Maximum number of nearest shoreline candidates examined by routine map-wide MCV ferry pickup planning. keeps this deliberately small because a ferry geometry plan is cached and reused instead of repeatedly searching the shoreline for each LST.")]
		public readonly int MaximumRoutinePickupBeachCandidates = 16;

		[Desc("Maximum number of native-passable landing handoffs examined near each sea-expansion ore field.")]
		public readonly int MaximumLandingBeachCandidates = 10;

		[Desc("Maximum distance in cells from an unreachable ore field to search for a native-passable landing handoff.")]
		public readonly int SeaLandingSearchRadius = 30;

		[Desc("Radius used to prefer sea-expansion ore fields and landing handoffs near an already established friendly ground squad. This is a preference, never a hard requirement.")]
		public readonly int SeaLandingProtectionRadius = 24;

		[Desc("Ticks between native EnterTransport retries while an MCV and its reserved LST are already at the pickup rendezvous. Mirrors the proven E6 transport flow instead of manually mutating Cargo.")]
		public readonly int SeaBoardingRetryInterval = 75;

		[Desc("Maximum world ticks a native MCV Cargo handoff may make no physical progress before bounded pickup/unload recovery is attempted.")]
		public readonly int SeaBoardingNoProgressTimeout = 250;

		[Desc("Maximum bounded recovery attempts for each native MCV Cargo handoff side. Pickup exhaustion releases pre-load ownership; destination unload exhaustion starts loaded return/preservation.")]
		public readonly int SeaBoardingMaximumRecoveryAttempts = 3;

		[Desc("Maximum bounded land-side pickup-cell replacements attempted for one reserved LST after the MCV exhausts the normal no-cell-progress retries. Recovery stays on the same shoreline pair and crossing corridor.")]
		public readonly int SeaPickupApproachMaximumRecoveryAttempts = 2;

		[Desc("Ticks to wait before retrying an Unload order if the previous unload activity ended but the MCV remains cargo.")]
		public readonly int SeaUnloadRetryInterval = 75;


		[ActorReference]
		[Desc("Refinery types that must be built at each ore expansion before the Construction Yard may repack.")]
		public readonly FrozenSet<string> ExpansionRefineryTypes = FrozenSet<string>.Empty;

		[Desc("Production queue category used for expansion refinery construction.")]
		public readonly string BuildingQueueCategory = "Building";

		[Desc("Only request an expansion MCV when combined cash and resources are at least this high.")]
		public readonly int MinimumCashForExpansionMcv = 100;

		[Desc("Hard cap for total Construction Yard capacity slots. Every live FACT, live MCV and pending/queued MCV consumes one slot. Sustained true Surplus may unlock capacity gradually up to this long-run maximum. A FACT<->MCV transform keeps the same slot.")]
		public readonly int MaximumConstructionYardSlots = 8;

		[Desc("Before Surplus pressure, cap total FACT + MCV + pending MCV capacity at this many slots. The normal early posture is one permanent main FACT plus one persistent PIONEER slot that is mobile whenever it is not physically deploying/finishing an outpost.")]
		public readonly int PreSurplusMaximumConstructionYardSlots = 2;

		[Desc("Before Surplus pressure, keep only this many Construction Yards permanently deployed. Additional early capacity belongs to the PIONEER role and repacks immediately after completing its local PROC unless a protected/permanent handoff is legitimate.")]
		public readonly int PreSurplusPermanentConstructionYards = 1;

		[Desc("How many Construction Yards should normally remain permanently deployed after Surplus pressure is reached. Remaining slot(s) stay as reserve/active MCV capacity.")]
		public readonly int DesiredPermanentConstructionYards = 2;

		[Desc("Hard maximum permanent FACT count. MaximumConstructionYardSlots should normally equal this value plus one roaming MCV/temporary FACT slot.")]
		public readonly int MaximumPermanentConstructionYards = 3;

		[Desc("Minimum current owned Ground Commander combat value required before true Surplus may grow permanent FACT/MCV capacity above the normal early main-FACT + one-roaming-slot posture. Set 0 to disable the army-pressure gate.")]
		public readonly int MinimumGroundCombatValueForAdditionalMcv = 10000;
		[Desc("If true, a damaged/critically exposed roaming MCV drops its expansion target and enters the single RETREAT state. RETREAT uses plain Move only toward a reachable destination that is spatially safer, non-critical and clear of visible weapon pressure.")]
		public readonly bool EnableMcvRetreat = true;

		[Desc("Minimum RecentDamageRiskScore required before a DEPLOYED expansion FACT may repack and flee on damage alone. Unlike a mobile MCV, a deployed conyard cannot quickly escape and repacking aborts the in-flight ore refinery claim, so light harassment below this risk is tanked rather than triggering a repack cycle. Set 0 to restore upstream behavior (any recent damage repacks).")]
		public readonly int ExpansionConyardRetreatRecentDamageRisk = 0;

		[Desc("Base radius scale used when generating ranked MCV RETREAT arrival candidates around the selected safe anchor. Completion still requires the MCV to physically reach its selected arrival cell.")]
		public readonly int McvRetreatArrivalRadius = 8;

		[Desc("Minimum cells a RETREAT destination must be from the MCV current cell so a fresh damage-triggered retreat cannot instantly complete without actually escaping.")]
		public readonly int McvRetreatMinimumEscapeCells = 4;

		[Desc("Radius around a Ground Commander regroup anchor searched for a legal MCV arrival cell. The anchor itself remains the strategic retreat point.")]
		public readonly int McvRetreatAnchorSearchRadius = 8;

		[Desc("Maximum number of best safety-ranked arrival cells that receive expensive native pathfinding per MCV RETREAT anchor/local-safe search pass. This is a performance bound; safety filtering still happens before pathfinding.")]
		public readonly int McvRetreatMaximumPathCandidatesPerAnchor = 6;

		[Desc("World ticks between cheap MCV RETREAT progress checks. This never reissues a Move while the MCV is making progress.")]
		public readonly int McvRetreatRecheckInterval = 25;

		[Desc("World ticks without changing cell before RETREAT may recalculate and issue one fresh plain Move toward the safest currently reachable validated retreat destination.")]
		public readonly int McvRetreatStallTimeout = 125;

		[Desc("Maximum number of own-control StrategicMap sectors considered when rebuilding a destroyed main Construction Yard. Recovery uses fair own-control plus unified RiskModel risk, never a hidden start location.")]
		public readonly int EmergencyMainBaseRecoverySectorCandidates = 12;

		[Desc("Cells around each safe own-control sector center searched for a legal emergency FACT deployment position.")]
		public readonly int EmergencyMainBaseRecoverySearchRadius = 10;

		[Desc("World ticks between emergency main-base recovery route/deploy progress checks.")]
		public readonly int EmergencyMainBaseRecoveryRecheckInterval = 125;

		[Desc("World ticks allowed after emergency DeployTransform before the recovery planner retries another safe cell instead of silently falling back to the old in-place deployment behavior.")]
		public readonly int EmergencyMainBaseRecoveryDeployTimeout = 200;

		[Desc("World ticks a protected first-expansion PROC may remain owned after its committed MCV objective disappears. This short grace prevents queue thrash, then stale reservation/prebuild ownership is cancelled until a new expansion objective commits.")]
		public readonly int FirstExpansionRefineryObjectiveGraceTicks = 500;

		[Desc("World ticks allowed after issuing PlaceBuilding for the protected first-expansion PROC before the placement is considered unconfirmed and retried. This prevents a rejected native placement order from leaving the READY refinery and Building queue owned forever.")]
		public readonly int FirstExpansionRefineryPlacementConfirmTimeoutTicks = 500;

		[Desc("Ticks between expansion-state evaluations.")]
		public readonly int ScanInterval = 25;
		[Desc("Ticks between attempts to request a replacement expansion MCV.")]
		public readonly int BuildMcvInterval = 100;

		[Desc("Minimum ticks between expensive full-path checks while an expansion MCV is already moving.")]
		public readonly int RouteRecheckInterval = 125;

		[Desc("World ticks an MCV may remain on the same map cell while a native Move is still active before one bounded movement retry is issued. This catches traffic/path stalls without rebuilding paths every bot tick.")]
		public readonly int MovingMcvStallTimeoutTicks = 375;

		[Desc("Maximum same-target movement-stall retries before the current ore objective is released and normal replanning selects another legal objective.")]
		public readonly int MovingMcvStallMaximumRetries = 2;


		[Desc("Maximum distance in cells between two allied MCV resource objectives for them to count as the same soft expansion reservation. Earlier reservation wins; same-tick ties use PlayerActor ID.")]
		public readonly int AlliedMcvReservationObjectiveRadius = 6;

		[Desc("Maximum distance in cells between two allied planned FACT deploy cells for them to count as a conflicting soft expansion reservation even if their resource-center cells differ.")]
		public readonly int AlliedMcvReservationDeployRadius = 10;

		[Desc("World ticks to wait after issuing DeployTransform before treating a still-live MCV as a failed/stalled deployment and retrying instead of waiting forever.")]
		public readonly int ExpansionDeployConfirmTimeoutTicks = 150;

		[Desc("Maximum DeployTransform retries at the validated deploy cell before the ore field is rejected and the MCV selects another expansion site.")]
		public readonly int ExpansionDeployMaximumRetries = 2;

		[Desc("Radius in cells around the MCV deploy cell used for bounded friendly-blocker clearance before FACT deployment.")]
		public readonly int ExpansionDeployClearanceRadius = 6;

		[Desc("Exclusive right-of-way radius around an approaching MCV deploy cell. Ground Commander and producer rally placement keep ordinary combat units outside this area while the MCV is close enough to deploy, preventing friendly-unit pileups from recreating the cleared FACT footprint.")]
		public readonly int McvDeployRightOfWayRadius = 8;

		[Desc("Distance in cells from the planned deploy cell at which the MCV right-of-way zone becomes active. It should be larger than the protected radius so units start clearing before the MCV reaches the exact FACT cell.")]
		public readonly int McvDeployRightOfWayActivationRadius = 14;

		[Desc("World ticks between re-issued blocker-clear orders while an arrived MCV is waiting for its FACT footprint to become free.")]
		public readonly int ExpansionDeployClearanceOrderInterval = 100;

		[Desc("World ticks allowed for one MCV deploy-clearance attempt before trying another legal deploy cell in the same ore field or abandoning the field.")]
		public readonly int ExpansionDeployClearanceTimeoutTicks = 500;

		[Desc("Maximum same-field deploy-cell clearance retries/replans before the ore field is temporarily rejected. This prevents friendly-blocker order loops from stalling expansion forever.")]
		public readonly int ExpansionDeployClearanceMaximumReplans = 2;

		[Desc("World ticks to wait after asking an expansion FACT to repack before retrying. Prevents WaitingForMcv from stalling forever.")]
		public readonly int ExpansionRepackConfirmTimeoutTicks = 150;

		[Desc("Maximum repack retries before a stubborn expansion FACT is left deployed as a useful permanent Construction Yard and the expansion chain continues with a reserve/new MCV.")]
		public readonly int ExpansionRepackMaximumRetries = 2;


		[Desc("Maximum number of nearest plausible ore fields that receive expensive safe-path evaluation.")]
		public readonly int MaximumOreFieldPathCandidates = 6;

		[Desc("Maximum accepted risk-aware MCV route length as a percentage of the geometric minimum step distance. Excessive safe detours are rejected so PIONEER tries the next-nearest ore instead of crossing half the map around one threat.")]
		public readonly int MaximumMcvRouteDetourPercent = 175;

		[Desc("Extra route-length slack in cells allowed on top of MaximumMcvRouteDetourPercent for local terrain/building geometry.")]
		public readonly int MaximumMcvRouteDetourSlackCells = 8;

		[Desc("Preferred straight-line distance in cells for a normal local expansion hop.")]
		public readonly int MaximumExpansionHopDistance = 35;

		[Desc("Maximum distance for the map-wide land fallback after no local field is usable. Zero means unlimited.")]
		public readonly int FallbackMaximumExpansionHopDistance = 0;

		[Desc("Maximum number of distant land fields that receive expensive safe-path evaluation after the local search fails.")]
		public readonly int FallbackMaximumOreFieldPathCandidates = 24;

		[ActorReference]
		[Desc("Existing economic-service structures that mark nearby ore fields as already covered. A FACT alone is physical presence/attraction, not proof that the local ore already has a refinery.")]
		public readonly FrozenSet<string> ExistingBaseCoverageTypes = FrozenSet<string>.Empty;

		[Desc("Ore fields within this many cells of a configured ExistingBaseCoverageTypes structure are treated as already economically covered.")]
		public readonly int ExistingBaseCoverageRadius = 16;

		[Desc("Minimum number of resource cells required for an ore field to be considered.")]
		public readonly int MinimumResourceCells = 4;

		[Desc("Minimum MCV deployment distance from the resource center.")]
		public readonly int ResourceDeployMinRadius = 4;

		[Desc("Maximum MCV deployment distance from the resource center.")]
		public readonly int ResourceDeployMaxRadius = 10;

		[Desc("Minimum placement radius for the expansion refinery around the temporary construction yard.")]
		public readonly int ExpansionStructureMinRadius = 2;

		[Desc("Maximum placement radius for the expansion refinery around the temporary construction yard.")]
		public readonly int ExpansionStructureMaxRadius = 6;

		[Desc("An ore field is considered serviced when a refinery exists within this radius.")]
		public readonly int ServicedFieldRadius = 12;




		[Desc("How many ticks a normally failed ore field is ignored before it may be tried again.")]
		public readonly int FailedFieldRetryDelay = 1500;

		[Desc("World ticks a MineCluster area is excluded after an expansion MCV retreats from it or is lost while pursuing it.")]
		public readonly int ExpansionTargetFailureCooldownTicks = 3000;

		[Desc("Radius around a failed MCV expansion objective treated as the same recently proven-dangerous area.")]
		public readonly int ExpansionTargetFailureRadius = 12;

		[Desc("Minimum world ticks after a full land expansion search returns no usable target before another expensive ore/deploy/path search may run.")]
		public readonly int NoLandExpansionReplanInterval = 500;

		[Desc("World ticks between full routine land/deploy/path rescans while the nearest PIONEER objective is already waiting for exact RECON. The exact objective stays fixed; this only prevents identical native path proofs from repeating every 25 WT while intelligence has not arrived.")]
		public readonly int PioneerReconHoldReplanInterval = 250;

		[Desc("Maximum world ticks the pre-commit PIONEER PRIMARY may remain blocked by RECON or SECURE work before it is abandoned and the prepared ALTERNATE is promoted. This prevents one frontier from pinning the roaming MCV indefinitely.")]
		public readonly int PioneerObjectiveMaximumHoldTicks = 3000;

		[Desc("World ticks an abandoned PIONEER objective is excluded before it may be considered again. The cooldown is local and does not create a General SECURE priority bonus.")]
		public readonly int PioneerObjectiveAbandonCooldownTicks = 6000;

		[Desc("Persistent enemy-structure exposure score at or above which an ore area is treated as an enemy stronghold rather than an expansion-unblock SECURE objective. Such areas are skipped/backed off instead of asking Ground to conquer a fortified base for the MCV.")]
		public readonly int PioneerHostileCoreStructureScore = 260;

		[Desc("World ticks an ore area is ignored after a deployed expansion FACT fails the configured refinery-placement limit. Static placement geometry should not be re-tested quickly.")]
		public readonly int FailedRefinerySiteRetryDelay = 6000;

		[Desc("Radius in cells around a refinery-placement failure that is treated as the same unusable expansion site during its cooldown.")]
		public readonly int FailedRefinerySiteRadius = 8;

		[Desc("Weight applied only when choosing among temporary coastal-staging FACT cells. Routine PIONEER ore objectives are nearest-first and use RiskModel only as a veto.")]
		public readonly int CoastalStagingRiskWeight = 4;

		[Desc("Role-specific RiskModel incident score remembered after an expansion FACT is forced to flee.")]
		public readonly int DangerousExpansionIncidentRisk = 220;

		[Desc("Radius in cells around a failed dangerous expansion remembered by RiskModel.")]
		public readonly int DangerousExpansionIncidentRadius = 18;

		[Desc("World ticks that a dangerous expansion front remains in RiskModel memory.")]
		public readonly int DangerousExpansionIncidentDuration = 8000;

		[Desc("Maximum failed placement attempts before the temporary expansion is abandoned.")]
		public readonly int MaximumPlacementFailures = 4;

		[Desc("Condition granted to the player while the temporary expansion conyard owns the building queue.")]
		public readonly string BaseBuilderLockCondition = "frans-expansion-lock";

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (ScanInterval < 25)
				throw new YamlException($"{nameof(ScanInterval)} must be at least 25 WT.");


			if (BuildMcvInterval <= 0)
				throw new YamlException($"{nameof(BuildMcvInterval)} must be greater than zero.");

			if (RouteRecheckInterval < 25)
				throw new YamlException($"{nameof(RouteRecheckInterval)} must be at least 25 WT.");
			// Cameo port: EarlyNavalOpeningCompletionTypes ships empty until per-faction
			// ContentPack wiring fills it; empty leaves naval opening detection inactive.
			if (MovingMcvStallTimeoutTicks < RouteRecheckInterval || MovingMcvStallMaximumRetries < 0)
				throw new YamlException("Moving MCV stall-watchdog settings are invalid.");
			if (AlliedMcvReservationObjectiveRadius < 0 || AlliedMcvReservationDeployRadius < 0)
				throw new YamlException($"{nameof(AlliedMcvReservationObjectiveRadius)} and {nameof(AlliedMcvReservationDeployRadius)} must be non-negative.");

			if (LandingCraftProducerPlacementScanInterval <= 0 || LandingCraftProducerPlacementConfirmTimeoutTicks < ScanInterval ||
				LandingCraftProducerPlacementMaximumRetries <= 0 || CoastalStagingShoreRadius <= 0 ||
				CoastalStagingMaximumCandidates <= 0 || CoastalStagingNavalProducerTimeoutTicks <= 0 ||
				CoastalStagingMaximumFailedAttempts <= 0 || FirstExpansionRefineryInfrastructureSuspensionGraceTicks < 0 ||
				ExploredMapResourceObjectiveRadius <= 0 ||
				MaximumMcvRouteDetourPercent < 100 || MaximumMcvRouteDetourSlackCells < 0)
				throw new YamlException("Explore-map resource / coastal-staging settings are invalid.");

			if (ExpansionDeployConfirmTimeoutTicks <= 0 || ExpansionDeployMaximumRetries < 0 ||
				ExpansionDeployClearanceRadius <= 0 || McvDeployRightOfWayRadius < ExpansionDeployClearanceRadius ||
				McvDeployRightOfWayActivationRadius <= McvDeployRightOfWayRadius || ExpansionDeployClearanceOrderInterval <= 0 ||
				ExpansionDeployClearanceTimeoutTicks <= 0 || ExpansionDeployClearanceMaximumReplans < 0 ||
				ExpansionRepackConfirmTimeoutTicks <= 0 || ExpansionRepackMaximumRetries < 0)
				throw new YamlException("Expansion deploy/clearance/repack watchdog settings are invalid.");


			if (MaximumOreFieldPathCandidates <= 0)
				throw new YamlException($"{nameof(MaximumOreFieldPathCandidates)} must be greater than zero.");

			if (MaximumExpansionHopDistance <= 0)
				throw new YamlException($"{nameof(MaximumExpansionHopDistance)} must be greater than zero.");

			if (FallbackMaximumExpansionHopDistance < 0 || FallbackMaximumOreFieldPathCandidates <= 0)
				throw new YamlException("Expansion land-fallback settings are invalid.");

			if (ExistingBaseCoverageRadius <= 0)
				throw new YamlException($"{nameof(ExistingBaseCoverageRadius)} must be greater than zero.");

			if (MinimumCashForExpansionMcv < 0 || MaximumConstructionYardSlots <= 0 || PreSurplusMaximumConstructionYardSlots <= 0 ||
				PreSurplusMaximumConstructionYardSlots > MaximumConstructionYardSlots || PreSurplusPermanentConstructionYards <= 0 ||
				PreSurplusPermanentConstructionYards > PreSurplusMaximumConstructionYardSlots || DesiredPermanentConstructionYards <= 0 ||
				MaximumPermanentConstructionYards <= 0 || MaximumPermanentConstructionYards >= MaximumConstructionYardSlots ||
				DesiredPermanentConstructionYards > MaximumPermanentConstructionYards || PreSurplusPermanentConstructionYards > DesiredPermanentConstructionYards ||
				MinimumGroundCombatValueForAdditionalMcv < 0 ||
				McvRetreatArrivalRadius <= 0 || McvRetreatMinimumEscapeCells <= 0 || McvRetreatAnchorSearchRadius < McvRetreatArrivalRadius ||
				McvRetreatMaximumPathCandidatesPerAnchor <= 0 ||
				McvRetreatRecheckInterval < 25 || McvRetreatStallTimeout < McvRetreatRecheckInterval ||
				EmergencyMainBaseRecoverySectorCandidates <= 0 || EmergencyMainBaseRecoverySearchRadius <= 0 ||
				EmergencyMainBaseRecoveryRecheckInterval < 25 || EmergencyMainBaseRecoveryDeployTimeout < 25)
				throw new YamlException("Expansion MCV economy/reserve/parking/growth/RETREAT/recovery settings are invalid; recurring Fransbot work may not run below 25 WT.");

			if (MinimumResourceCells <= 0)
				throw new YamlException($"{nameof(MinimumResourceCells)} must be greater than zero.");

			if (ResourceDeployMinRadius < 0 || ResourceDeployMaxRadius < ResourceDeployMinRadius)
				throw new YamlException($"{nameof(ResourceDeployMaxRadius)} must be at least {nameof(ResourceDeployMinRadius)}.");

			if (ExpansionStructureMinRadius < 0 || ExpansionStructureMaxRadius < ExpansionStructureMinRadius)
				throw new YamlException($"{nameof(ExpansionStructureMaxRadius)} must be at least {nameof(ExpansionStructureMinRadius)}.");

			if (ServicedFieldRadius <= 0)
				throw new YamlException("Expansion safety and service radii must be valid positive values.");

			if (FailedFieldRetryDelay < 0 || ExpansionTargetFailureCooldownTicks <= 0 || ExpansionTargetFailureRadius <= 0 || NoLandExpansionReplanInterval < 25 || PioneerReconHoldReplanInterval < 25 ||
				PioneerObjectiveMaximumHoldTicks < PioneerReconHoldReplanInterval || PioneerObjectiveAbandonCooldownTicks <= 0 || PioneerHostileCoreStructureScore <= 0 ||
				FailedRefinerySiteRetryDelay <= 0 || FailedRefinerySiteRadius <= 0 ||
				MaximumPlacementFailures <= 0 || CoastalStagingRiskWeight < 0 ||
				DangerousExpansionIncidentRisk < 0 || DangerousExpansionIncidentRadius <= 0 || DangerousExpansionIncidentDuration <= 0)
				throw new YamlException("Expansion retry/risk-memory settings must be valid; no-target replanning may not run below 25 WT.");

			if (string.IsNullOrWhiteSpace(LandingCraftQueueCategory))
				throw new YamlException("Amphibious expansion requires a queue category.");

			if (LandingCraftProducerSearchRadius <= 0)
				throw new YamlException($"{nameof(LandingCraftProducerSearchRadius)} must be greater than zero.");

			if (MinimumCashForSeaTransport < 0 || SeaPlanningInterval <= 0 || SeaRouteRiskRecheckInterval <= 0 || SeaTransportRequestCooldown < 0 ||
				SeaTransportFeasibilityWatchdogTicks < SeaPlanningInterval ||
				(SeaTransportAbsoluteWaitWatchdogTicks > 0 && SeaTransportAbsoluteWaitWatchdogTicks < SeaTransportFeasibilityWatchdogTicks) ||
				FirstExpansionRefineryObjectiveGraceTicks < ScanInterval ||
				FirstExpansionRefineryPlacementConfirmTimeoutTicks < ScanInterval ||
				SeaBoardingRetryInterval <= 0 || SeaBoardingNoProgressTimeout <= 0 || SeaBoardingMaximumRecoveryAttempts < 0 ||
				SeaPickupApproachMaximumRecoveryAttempts < 0)
				throw new YamlException("Sea expansion economy/timing settings are invalid.");

			if (MaximumSeaOreFieldCandidates <= 0 || MaximumRoutinePickupBeachCandidates <= 0 || MaximumLandingBeachCandidates <= 0 ||
				RoutineSeaOreCandidatesPerPlanningPass <= 0 || RoutineSeaOreLandingBeachesPerPlanningPass <= 0 ||
				RoutineSeaOreExitPathProofsPerPlanningPass <= 0 || SeaPickupPathProofsPerPlanningPass <= 0 ||
				CommittedSeaCorridorRecoveryInterval < ScanInterval || CommittedSeaCorridorRecoveryInterval > SeaPlanningInterval ||
				CommittedSeaCorridorRecoveryMaximumPasses <= 0 || RoutineSeaOreSearchCacheDuration < 25 ||
				RoutineSeaOreSearchMovementTolerance < 0 || FutureRefineryProofRetryDelay < ScanInterval)
				throw new YamlException("Sea expansion candidate/proof limits must be greater than zero, committed corridor recovery cadence must stay between one scan and the ordinary sea-planning interval, future refinery proof retry must be at least one scan, and the bounded sea-search cache may not be shorter than 25 WT.");

			if (SeaLandingSearchRadius <= 0 || SeaLandingProtectionRadius <= 0 ||
				SeaBoardingRetryInterval <= 0 || SeaUnloadRetryInterval <= 0)
				throw new YamlException("Sea expansion radii/retry settings must be greater than zero.");

			if (string.IsNullOrWhiteSpace(BaseBuilderLockCondition))
				throw new YamlException($"{nameof(BaseBuilderLockCondition)} must not be empty.");
		}

		public override object Create(ActorInitializer init) { return new FransMcvExpansionManagerBotModule(init.Self, this); }
	}

	public class FransMcvExpansionManagerBotModule : ConditionalTrait<FransMcvExpansionManagerBotModuleInfo>,
		IBotEnabled, IBotTick, IBotBaseExpansion, INotifyActorDisposing, IFransAmphibiousExpansionService, IFransExpansionStateService
	{
		enum ExpansionStage
		{
			Idle,
			MovingToOre,
			ClearingLandDeployArea,
			WaitingForConyard,
			BuildingRefinery,
			HoldingCompletedOutpost,
			WaitingForMcv,
			WaitingForSeaTransport,
			MovingToSeaPickup,
			SeaLoading,
			SeaTransporting,
			SeaUnloading,
			SeaCargoPreserved,
			Retreat,
			EmergencyMainBaseRecovery
		}

		enum SeaUnloadRecoveryPhase
		{
			NativeUnload,
			AwaitingStop,
			MovingToHandoff,
			PreservedCargo
		}

		// Ground-Commander style ownership. One object owns every piece of mutable
		// state that defines *which* expansion is currently being executed. Planner memory
		// (scouted/failed/SECURE-required ore) deliberately remains outside the task because
		// it survives aborts and feeds the next plan. Execution watchdogs remain local fields
		// because they are implementation details, not strategic ownership.
		enum ExpansionTaskMode
		{
			None,
			LandOre,
			SeaOre,
			CoastalStaging,
			EmergencyRecovery
		}

		enum PioneerObjectiveExecutionKind
		{
			None,
			Land,
			Sea
		}

		enum PioneerExecutionProofPhase
		{
			LandRoute,
			LandRefinery,
			SeaPrecheck,
			SeaLanding,
			SeaRefinery
		}

		enum PioneerLandRouteFailureKind
		{
			None,
			StableTopology,
			NoLegalDeployCell,
			CautiousRiskRejectedAllLegalCandidates,
			MissingPathFinder,
			NativePathNotFound,
			ReturnedPathCriticalRisk,
			RouteDetour
		}

		sealed class PioneerLandRouteAttemptEvidence
		{
			public CPos[] SafeDeployCells = [];
			public CPos[] ReturnedPath = [];
			public bool NativePathSearchAttempted;
			public bool ReturnedPathRejectedForRisk;
		}

		sealed class PioneerExecutionProofWork
		{
			public uint McvActorId;
			public CPos McvCell;
			public int RiskRevision;
			public int TerrainKnowledgeVersion;
			public PioneerExecutionProofPhase Phase;
			public CPos LandDeployCell;
			public CPos[] LandRoutePath = [];
			public bool LandRouteRejected;
			public bool LandRouteFailureTerrainStable;
			public PioneerLandRouteFailureKind LandRouteFailureKind;
			public bool LandRouteFailureRiskSensitive;
			public int LandRouteRejectedRiskRevision = -1;
			public CPos[] LandRouteLegalDeployCells = [];
			public CPos[] LandRouteSafeDeployCells = [];
			public CPos[] LandRouteReturnedPath = [];
			public CPos[] LandRouteRiskCostCells = [];
			public int[] LandRouteRiskCosts = [];
			public CPos[] LandRouteBlockedCells = [];
			public bool LandRouteRiskEvidenceChanged;
			public bool LandRouteDynamicEvidenceChanged;
			public bool LandRefineryRejected;
			public bool LandRefineryFailureRiskSensitive;
			public int LandRefineryRejectedRiskRevision = -1;
			public string[] LandRefineryLegalTypes = [];
			public CPos[] LandRefineryLegalCells = [];
			public bool LandRefineryRiskEvidenceChanged;
			public bool LandRefineryDynamicEvidenceChanged;
			public int PickupNavalRegion = -1;
			public CPos PickupMcvCell;
			public CPos PickupCraftCell;
			public CPos[] PickupMcvPath = [];
			public CPos SeaLandingCraftCell;
			public CPos SeaLandingExitCell;
			public CPos SeaDeployCell;
			public CPos[] SeaLandingPath = [];
			public RoutineSeaOreSearchState SeaLandingSearch;
			public string SeaRefineryType;
			public CPos SeaRefineryCell;
		}

		readonly record struct SeaTopologyFailureKey(CPos Objective, int PickupNavalRegion, int TerrainKnowledgeVersion);
		readonly record struct SeaLandingProofFailureKey(CPos Objective, int PickupNavalRegion, int TerrainKnowledgeVersion);
		readonly record struct LandingExitProof(bool Success, CPos DeployCell, int PathLength, CPos[] Path);
		readonly record struct PendingMoveOrder(CPos Destination, bool Queued);
		readonly record struct PioneerExecutionProofCacheEntry(uint McvActorId, CPos McvCell, int RiskRevision,
			int TerrainKnowledgeVersion, int Tick, PioneerObjectiveExecutionKind Kind);

		enum CoastalStagingRepackOutcome
		{
			None,
			RetryPlacementRejected,
			RetryProducerTimeout,
			Success
		}

		sealed class ExpansionTask
		{
			public int Id;
			public ExpansionTaskMode Mode;
			public ExpansionStage Stage = ExpansionStage.Idle;
			public CPos? ResourceCenter;
			public CPos? DeployCell;
			public int ReservationStartedTick = -1;
			public bool PostSeaUnloadDeployCommitted;
			public Actor LandingCraft;
			public Actor LandingCraftReservationOwner;
			public Actor PendingLandingCraftReservation;
			public CPos? SeaPickupMcvCell;
			public CPos? SeaPickupCraftCell;
			public CPos? SeaLandingCraftCell;
			public bool CoastalReturnToSea;
			public CoastalStagingRepackOutcome CoastalRepackOutcome;
			public CPos? DeferredRoutineFerryObjective;
			public int DeferredRoutineFerryReservationStartedTick = -1;

		}

		readonly record struct OreChoice(CPos ResourceCenter, CPos DeployCell, int PathLength, int RiskScore);
		readonly record struct OreFieldCandidate(CPos ResourceCenter, long DistanceSquared);
		readonly record struct SeaTargetChoice(CPos ResourceCenter, CPos DeployCell, CPos LandingCraftCell, long DistanceSquared);
		readonly record struct SeaPlan(CPos ResourceCenter, CPos DeployCell,
			CPos PickupMcvCell, CPos PickupCraftCell, CPos LandingCraftCell,
			int MvcLandPathLength, int SeaPathLength);

		sealed class LandingCraftEligibilityDiagnostic
		{
			public readonly Actor Craft;
			public string Origin;
			public string Claim = "NotEvaluated";
			public string Cargo = "NotEvaluated";
			public string Mobile = "NotEvaluated";
			public string Region = "NotEvaluated";
			public string PickupEnter = "NotEvaluated";
			public string PickupStay = "NotEvaluated";
			public string PickupPath = "NotEvaluated";
			public string CrossingPath = "NotEvaluated";
			public string Result = "NotEvaluated";

			public LandingCraftEligibilityDiagnostic(Actor craft, string origin)
			{
				Craft = craft;
				Origin = origin;
			}

			public override string ToString() =>
				$"{Craft.ActorID}/{Craft.Info.Name}:origin={Origin},claim={Claim},cargo={Cargo},mobile={Mobile},region={Region},pickupEnter={PickupEnter},pickupStay={PickupStay},pickupPath={PickupPath},crossingPath={CrossingPath},result={Result}";
		}

		sealed class NativeDeployProofKey : IEquatable<NativeDeployProofKey>
		{
			public readonly uint McvActorId;
			public readonly CPos Source;
			public readonly CPos[] OrderedTargets;
			readonly int hashCode;

			public NativeDeployProofKey(uint mcvActorId, CPos source, IReadOnlyList<CPos> orderedTargets)
			{
				McvActorId = mcvActorId;
				Source = source;
				OrderedTargets = orderedTargets?.ToArray();
				unchecked
				{
					var hash = ((int)mcvActorId * 397) ^ source.GetHashCode();
					if (OrderedTargets == null)
						hash = hash * 397 - 1;
					else
						foreach (var target in OrderedTargets)
							hash = hash * 397 ^ target.GetHashCode();
					hashCode = hash;
				}
			}

			public bool Equals(NativeDeployProofKey other)
			{
				if (other == null || McvActorId != other.McvActorId || Source != other.Source)
					return false;
				if (OrderedTargets == null || other.OrderedTargets == null)
					return OrderedTargets == other.OrderedTargets;
				if (OrderedTargets.Length != other.OrderedTargets.Length)
					return false;

				for (var i = 0; i < OrderedTargets.Length; i++)
					if (OrderedTargets[i] != other.OrderedTargets[i])
						return false;
				return true;
			}

			public override bool Equals(object obj) => Equals(obj as NativeDeployProofKey);
			public override int GetHashCode() => hashCode;
		}

		sealed class RoutineLandCandidatePerf
		{
			public readonly int Ordinal;
			public readonly string Classification;
			public readonly CPos Objective;
			public int DeployTargetCount;
			public bool TopologyNegative;
			public bool CooldownBeforePath;
			public bool NativeSearchExecuted;
			public long NativePathCostCallbacks;
			public double NativeElapsedMs;
			public bool NativeSearchSkippedByUnionCertificate;
			public string UnionCertificateMismatch = "None";
			public string Result = "Pending";
			public bool FinalWinner;

			public RoutineLandCandidatePerf(int ordinal, string classification, CPos objective)
			{
				Ordinal = ordinal;
				Classification = classification;
				Objective = objective;
			}

			public string Format() =>
				$"#{Ordinal}/{Classification}/objective={Objective}/targets={DeployTargetCount}/" +
				$"topologyNegative={TopologyNegative}/cooldownBeforePath={CooldownBeforePath}/" +
				$"nativeSearch={NativeSearchExecuted}/callbacks={NativePathCostCallbacks}/nativeMs={NativeElapsedMs:0.00}/" +
				$"unionCertifiedSkip={NativeSearchSkippedByUnionCertificate}/unionMismatch={UnionCertificateMismatch}/" +
				$"result={Result}/winner={FinalWinner}";
		}

		readonly record struct RoutineLandPlannedCandidate(OreFieldCandidate Candidate, string Classification);

		sealed class RoutineLandNegativeUnionScanState
		{
			public readonly CPos Source;
			public readonly RoutineLandPlannedCandidate[] PlannedCandidates;
			public readonly RoutineLandNegativeUnionScan Coordinator;
			public readonly McvObjectiveScanPerf Perf;

			public RoutineLandNegativeUnionScanState(Actor mcv, Mobile mobile, CPos source,
				int worldTick, int riskRevision, int terrainKnowledgeVersion,
				RoutineLandPlannedCandidate[] plannedCandidates, McvObjectiveScanPerf perf)
			{
				Source = source;
				PlannedCandidates = plannedCandidates;
				Perf = perf;
				Coordinator = new RoutineLandNegativeUnionScan(new RoutineLandNegativeUnionContract(
					mcv, mcv.ActorID, mcv.Owner, mobile, mobile.Locomotor, source, worldTick,
					riskRevision, terrainKnowledgeVersion, true));
			}
		}

		sealed class McvObjectiveScanPerf
		{
			const int MaximumRoutineLandCandidateEvidence = 16;
			readonly List<RoutineLandCandidatePerf> routineLandCandidateEvidence = [];

			public readonly string Kind;
			public readonly McvObjectivePerfPass Pass;
			public int ResourceNodesEnumerated;
			public int CandidateNodesRetained;
			public int NodesEvaluated;
			public long DeployCellsEnumerated;
			public long DeployCellsRiskRejected;
			public long DeployCellsLegalityRejected;
			public long DeployCandidatesGenerated;
			public int LogicalNativeProofRequests;
			public int PhysicalNativePathSearches;
			public long NativeTargetCells;
			public long NativePathCostCallbackCalls;
			public long RiskPathCostCalls;
			public long PostPathRiskChecks;
			public double NativePathSearchElapsedMs;
			public double MaxNativePathSearchElapsedMs;
			public long MaxNativePathSearchCallbackCalls;
			public int MaxNativeTargetCells;
			public int LastNativeTargetCount;
			public int LastNativeTargetHash;
			public int FirstSuccessfulNativeProofIndex;
			public int LastSuccessfulNativeProofIndex;
			public int AcceptedNativeProofIndex;
			public long TopologyTargetQueries;
			public int TopologyNegativeCandidates;
			public int NativeSearchesSkippedByTopologyNegative;
			public int CandidatesRejectedByPrePathRefineryCooldown;
			public int NativeSearchesSkippedByCooldownBeforePath;
			public int RoutineLandOrdinaryNativeEmptyResults;
			public int RoutineLandOrdinaryNativeSearches;
			public long RoutineLandOrdinaryPathCostCallbacks;
			public int RoutineLandUnionPreparationAttempts;
			public double RoutineLandUnionPreparationElapsedMs;
			public long RoutineLandUnionPreparationAllocatedBytes;
			public string RoutineLandUnionActivationReason = "NativeEmptyThresholdNotReached";
			public int RoutineLandUnionEligibleObjectives;
			public int RoutineLandUnionTargetCells;
			public int RoutineLandUnionTargetHash;
			public int RoutineLandUnionNativeSearches;
			public long RoutineLandUnionPathCostCallbacks;
			public double RoutineLandUnionElapsedMs;
			public string RoutineLandUnionOutcome = "NotAttempted";
			public string RoutineLandUnionFallbackReason = "None";
			public int RoutineLandNativeSearchesSkippedByUnionCertificate;
			public int RoutineLandUnionCertificateMismatches;
			public int RoutineLandCandidateEvidenceOmitted;
			public CPos? AcceptedObjective;
			public CPos? AcceptedDeployCell;
			public bool Pending;
			public double ElapsedMs;

			public McvObjectiveScanPerf(string kind, McvObjectivePerfPass pass)
			{
				Kind = kind;
				Pass = pass;
			}

			public RoutineLandCandidatePerf BeginRoutineLandCandidate(CPos objective, string classification)
			{
				var evidence = new RoutineLandCandidatePerf(NodesEvaluated, classification, objective);
				if (routineLandCandidateEvidence.Count < MaximumRoutineLandCandidateEvidence)
					routineLandCandidateEvidence.Add(evidence);
				else
					RoutineLandCandidateEvidenceOmitted++;
				return evidence;
			}

			public string FormatRoutineLandCandidateEvidence()
			{
				var formatted = string.Join(" | ", routineLandCandidateEvidence.Select(candidate => candidate.Format()));
				return RoutineLandCandidateEvidenceOmitted > 0
					? $"{formatted} | omitted={RoutineLandCandidateEvidenceOmitted}"
					: formatted;
			}

			public string Format()
			{
				var routineLandGuards = Kind == "Land"
					? $",topologyQueries={TopologyTargetQueries},topologyNegative={TopologyNegativeCandidates}," +
						$"nativeSkippedTopology={NativeSearchesSkippedByTopologyNegative}," +
						$"cooldownBeforePath={CandidatesRejectedByPrePathRefineryCooldown}," +
						$"nativeSkippedCooldown={NativeSearchesSkippedByCooldownBeforePath}," +
						$"ordinaryNativeEmpty={RoutineLandOrdinaryNativeEmptyResults}," +
						$"ordinaryNativeSearches={RoutineLandOrdinaryNativeSearches}," +
						$"ordinaryCallbacks={RoutineLandOrdinaryPathCostCallbacks}," +
						$"unionPrepAttempts={RoutineLandUnionPreparationAttempts}," +
						$"unionPrepMs={RoutineLandUnionPreparationElapsedMs:0.00}," +
						$"unionPrepAllocBytes={RoutineLandUnionPreparationAllocatedBytes}," +
						$"unionActivation={RoutineLandUnionActivationReason}," +
						$"unionEligibleObjectives={RoutineLandUnionEligibleObjectives}," +
						$"unionTargets={RoutineLandUnionTargetCells},unionHash={RoutineLandUnionTargetHash}," +
						$"unionSearches={RoutineLandUnionNativeSearches},unionCallbacks={RoutineLandUnionPathCostCallbacks}," +
						$"unionMs={RoutineLandUnionElapsedMs:0.00},unionOutcome={RoutineLandUnionOutcome}," +
						$"unionFallback={RoutineLandUnionFallbackReason}," +
						$"nativeSkippedUnionCertificate={RoutineLandNativeSearchesSkippedByUnionCertificate}," +
						$"unionCertificateMismatches={RoutineLandUnionCertificateMismatches}"
					: string.Empty;
				return $"{Kind}:resourceNodes={ResourceNodesEnumerated},candidateNodes={CandidateNodesRetained}," +
					$"nodesEvaluated={NodesEvaluated},deployCellsEnumerated={DeployCellsEnumerated}," +
					$"deployRiskRejected={DeployCellsRiskRejected},deployLegalityRejected={DeployCellsLegalityRejected}," +
					$"deployCandidates={DeployCandidatesGenerated},logicalNativeProofs={LogicalNativeProofRequests}," +
					$"physicalNativeSearches={PhysicalNativePathSearches},nativeTargetCells={NativeTargetCells}," +
					$"pathCostCallbacks={NativePathCostCallbackCalls}," +
					$"riskPathCostCalls={RiskPathCostCalls}," +
					$"postPathRiskChecks={PostPathRiskChecks},nativeMs={NativePathSearchElapsedMs:0.00}," +
					$"maxNativeMs={MaxNativePathSearchElapsedMs:0.00},maxNativeTargets={MaxNativeTargetCells}," +
					$"maxNativeCallbacks={MaxNativePathSearchCallbackCalls}," +
					$"firstNativeSuccess={FirstSuccessfulNativeProofIndex},acceptedProof={AcceptedNativeProofIndex}," +
					$"acceptedNode={(AcceptedObjective.HasValue ? AcceptedObjective.Value.ToString() : "none")}," +
					$"acceptedDeploy={(AcceptedDeployCell.HasValue ? AcceptedDeployCell.Value.ToString() : "none")}," +
					$"result={(Pending ? "pending" : AcceptedObjective.HasValue ? "success" : "failure")},elapsedMs={ElapsedMs:0.00}" +
					routineLandGuards;
			}
		}

		sealed class McvObjectivePerfPass
		{
			readonly Dictionary<NativeDeployProofKey, string> exactProofKinds = [];
			readonly Dictionary<CPos, CPos> resolvedDeployObjectives = [];

			public readonly McvObjectiveScanPerf Sea;
			public readonly McvObjectiveScanPerf Land;
			public int DuplicateExactProofs;
			public int CrossSeaLandExactDuplicates;
			public int DuplicateResolvedDeployCells;

			public int UniqueExactProofs => exactProofKinds.Count;

			public McvObjectivePerfPass()
			{
				Sea = new McvObjectiveScanPerf("Sea", this);
				Land = new McvObjectiveScanPerf("Land", this);
			}

			public void RecordPhysicalProof(McvObjectiveScanPerf scan, Actor mcv, CPos source, IReadOnlyList<CPos> orderedTargets)
			{
				var key = new NativeDeployProofKey(mcv.ActorID, source, orderedTargets);
				if (exactProofKinds.TryGetValue(key, out var firstKind))
				{
					DuplicateExactProofs++;
					if (firstKind != scan.Kind)
						CrossSeaLandExactDuplicates++;
					return;
				}

				exactProofKinds.Add(key, scan.Kind);
			}

			public void RecordResolvedDeployCell(CPos? objective, CPos deployCell)
			{
				if (!objective.HasValue)
					return;
				if (resolvedDeployObjectives.TryGetValue(deployCell, out var firstObjective))
				{
					if (firstObjective != objective.Value)
						DuplicateResolvedDeployCells++;
					return;
				}

				resolvedDeployObjectives.Add(deployCell, objective.Value);
			}
		}

		sealed class PioneerPhysicalProofPerf
		{
			public string Caller;
			public bool CachePresent;
			public bool CacheHit;
			public string CacheMissReason;
			public int CacheAge = -1;
			public uint CachedMcvActorId;
			public CPos CachedMcvCell;
			public int CachedRiskRevision = -1;
			public int CachedTerrainKnowledgeVersion = -1;
			public PioneerObjectiveExecutionKind CachedKind;
			public bool WorkPresent;
			public bool WorkRecreated;
			public string WorkResetReason;
			public int WorkRiskRevision = -1;
			public bool WorkRiskRevisionChanged;
			public string RiskValidity = "Current";
			public string RetainedSeaProofState = "NotChecked";
			public string RetainedSeaProofTrigger = "None";
			public string RetainedSeaProofFailure = "None";
			public int RetainedSeaProofPathCells;
			public bool RetainedSeaProofAvoidedPickupSearch;
			public bool FullPioneerRecomputationFollowed;
			public double RetainedSeaProofElapsedMs;
			public bool PhaseDeferred;
			public PioneerExecutionProofPhase? PreviousPhase;
			public McvObjectiveScanPerf LandRoutePerf;
			public McvObjectiveScanPerf SeaLandingPerf;
			public int PhasesThisTick;
			public double PhaseElapsedMs;
			public int SeaPickupCursor;
			public int SeaPickupCandidates;
			public int SeaPickupNativeSearchesThisPass;
			public int SeaPickupTargetCellsThisPass;
			public long SeaPickupPathCostCallbacksThisPass;
			public double SeaPickupNativeElapsedMsThisPass;
			public int SeaPickupNativeSearchesTotal;
			public long Started;
		}

		sealed class McvRecoveryPerf
		{
			public string Trigger;
			public bool RecheckGateBypassed;
			public int RecheckDueIn;
			public string AnchorSource;
			public int AnchorCenters;
			public int DistinctAnchorCenters;
			public long DeployCellsEnumerated;
			public long DeployCellsOutsideMap;
			public long DeployCellsMobilityRejected;
			public long BuildingPlacementChecks;
			public long DeployCellsPlacementRejected;
			public long DeployCellRiskChecks;
			public long DeployCellsRiskRejected;
			public int DeployCandidatesGenerated;
			public int DuplicateDeployCandidates;
			public int RankedDeployCandidates;
			public int LogicalNativeProofRequests;
			public int PhysicalNativePathSearches;
			public long NativeTargetCells;
			public long NativePathCostCallbackCalls;
			public long RiskPathCostCalls;
			public double NativePathSearchElapsedMs;
			public double MaxNativePathSearchElapsedMs;
			public long MaxNativePathSearchCallbackCalls;
			public int NativePathFailures;
			public int RouteRiskChecks;
			public int RouteRiskRejects;
		}

		sealed class RoutineSeaLandingProofState
		{
			public CPos ResourceCenter;
			public int PickupNavalRegion;
			public int RiskRevision;
			public CPos[] DeployCandidates = [];
			public CPos[] RankedBeaches = [];
			public int NextBeachIndex;
			public CPos? ActiveBeach;
			public CPos[] ActiveExitCells = [];
			public int NextExitIndex;
			public readonly Dictionary<CPos, LandingExitProof> ExitPathProofs = [];
		}

		sealed class RoutineSeaPickupProofState
		{
			public readonly uint McvActorId;
			public readonly CPos McvCell;
			public readonly int RiskRevision;
			public readonly int TerrainKnowledgeVersion;
			public readonly CPos? PreferredMcvCell;
			public readonly CPos? PreferredCraftCell;
			public readonly CPos[] RankedBeaches;
			public readonly int StartedTick;
			public bool PreferredAttempted;
			public int NextBeachIndex;
			public int NativeSearches;
			public long NativeTargetCells;
			public long NativePathCostCallbacks;
			public double NativeElapsedMs;
			public int LastPassNativeSearches;
			public int LastPassTargetCells;
			public long LastPassPathCostCallbacks;
			public double LastPassElapsedMs;
			public bool Success;
			public CPos ResultMcvCell;
			public CPos ResultCraftCell;
			public CPos[] ResultPath = [];
			public bool Complete;

			public RoutineSeaPickupProofState(uint mcvActorId, CPos mcvCell, int riskRevision, int terrainKnowledgeVersion,
				CPos? preferredMcvCell, CPos? preferredCraftCell, CPos[] rankedBeaches, int startedTick)
			{
				McvActorId = mcvActorId;
				McvCell = mcvCell;
				RiskRevision = riskRevision;
				TerrainKnowledgeVersion = terrainKnowledgeVersion;
				PreferredMcvCell = preferredMcvCell;
				PreferredCraftCell = preferredCraftCell;
				RankedBeaches = rankedBeaches;
				StartedTick = startedTick;
			}
		}

		sealed class RoutineSeaOreSearchState
		{
			public readonly uint McvActorId;
			public readonly CPos McvCell;
			public readonly int TerrainKnowledgeVersion;
			public readonly bool AllowMapWideFallback;
			public readonly OreFieldCandidate[] Candidates;
			public bool PickupProven;
			public int NextCandidateIndex;
			public RoutineSeaLandingProofState LandingProof;
			public bool Complete;
			public SeaTargetChoice? Result;
			public CPos SuccessfulLandingExitCell;
			public CPos[] SuccessfulLandingPath = [];
			public int CompletedRiskRevision = -1;
			public int CompletedTick = -1;

			public RoutineSeaOreSearchState(uint mcvActorId, CPos mcvCell, int terrainKnowledgeVersion,
				bool allowMapWideFallback, OreFieldCandidate[] candidates)
			{
				McvActorId = mcvActorId;
				McvCell = mcvCell;
				TerrainKnowledgeVersion = terrainKnowledgeVersion;
				AllowMapWideFallback = allowMapWideFallback;
				Candidates = candidates;
			}
		}

		sealed class CommittedSeaCorridorRecoveryState
		{
			public readonly int TaskId;
			public readonly uint McvActorId;
			public CPos McvCell;
			public readonly CPos Objective;
			public readonly CPos OriginalPickupMcvCell;
			public readonly CPos OriginalPickupCraftCell;
			public readonly CPos OriginalLandingCraftCell;
			public readonly CPos OriginalDeployCell;
			public readonly CPos[] RankedAlternativePickupBeaches;
			public int NextPickupBeachIndex;
			public bool HasPickupCandidate;
			public bool UsesOriginalPickup;
			public CPos PickupMcvCell;
			public CPos PickupCraftCell;
			public CPos[] PickupMcvPath = [];
			public int PickupNavalRegion = -1;
			public int EvidenceRiskRevision = -1;
			public RoutineSeaOreSearchState LandingSearch;
			public CPos? ProposedLandingCraftCell;
			public CPos? ProposedLandingExitCell;
			public CPos? ProposedDeployCell;
			public CPos[] ProposedLandingPath = [];
			public int TestedCorridors;
			public readonly int StartedTick;
			public readonly int DeadlineTick;
			public readonly int MaximumPasses;
			public int PassesCompleted;
			public int NextAdvanceTick;
			public bool PausedForOriginalEligibility;
			public int SourceRebases;

			public CommittedSeaCorridorRecoveryState(int taskId, uint mcvActorId, CPos mcvCell, CPos objective,
				CPos originalPickupMcvCell, CPos originalPickupCraftCell, CPos originalLandingCraftCell,
				CPos originalDeployCell, CPos[] rankedAlternativePickupBeaches,
				int startedTick, int deadlineTick, int maximumPasses, int nextAdvanceTick)
			{
				TaskId = taskId;
				McvActorId = mcvActorId;
				McvCell = mcvCell;
				Objective = objective;
				OriginalPickupMcvCell = originalPickupMcvCell;
				OriginalPickupCraftCell = originalPickupCraftCell;
				OriginalLandingCraftCell = originalLandingCraftCell;
				OriginalDeployCell = originalDeployCell;
				RankedAlternativePickupBeaches = rankedAlternativePickupBeaches;
				StartedTick = startedTick;
				DeadlineTick = deadlineTick;
				MaximumPasses = maximumPasses;
				NextAdvanceTick = nextAdvanceTick;
			}
		}

		readonly World world;
		FransQueueDomains queueDomains;
		FransQueueDomains QueueDomains => queueDomains ??= FransQueueDomains.For(world.Map.Rules);

		// The configured landing-craft queue name plus every naval-domain queue alias the
		// ruleset declares — resolves in classic ("Ship") and hybrid ("RANaval") modes.
		FrozenSet<string> ShipQueueNames() =>
			QueueDomains.Naval.Union(new[] { Info.LandingCraftQueueCategory })
				.ToFrozenSet(StringComparer.OrdinalIgnoreCase);
		readonly Player player;
		readonly Actor playerActor;
		readonly ActorIndex.OwnerAndNamesAndTrait<TransformsInfo> mcvs;
		readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> constructionYards;
		readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> mcvFactories;
		readonly HashSet<Actor> pendingStopOrders = [];
		readonly Dictionary<Actor, PendingMoveOrder> pendingMoveOrders = [];
		readonly Dictionary<(uint ActorId, CPos Candidate), string> mcvTargetDebugStates = [];

		IBot orderBot;
		string lastMcvIdentityDebugState;
		string lastMcvExpansionDebugState;
		string lastMcvWaitingDebugState;
		string lastMcvDeployDebugState;
		string lastMcvTransportDemandDebugState;
		string lastCommittedSeaExecutionDiagnosticSignature;
		string lastCommittedSeaCorridorRecoveryDiagnosticSignature;
		string lastSeaSupplyDiagnosticSignature;
		string lastLandingCraftPlanDiagnostic;
		string lastRegionalLandingCraftOrderDiagnostic;
		string lastRegionalLandingCraftOrderSignature;
		CPos? lastRegionalLandingCraftOrderObjective;
		int? lastRegionalLandingCraftOrderRegion;
		IBotRequestUnitProduction[] requestUnitProduction;
		IFransCaptureTransportService transportService;
		IFransBaseBuilderService openingBuildOrderService;
		IFransStrategicMapService strategicMapService;
		IFransCommanderCoreService groundCommanderService;
		IFransGeneralService generalService;
		IFransCommandBidService commandBidService;
		IFransCombatIntelService combatIntelService;
		IFransRiskModelService riskModelService;
		IFransEconomicSaturationService economicStateService;
		IFransCaptureSecurityService[] captureSecurityServices;
		IFransGroundUnitReservationService groundUnitReservationService;
		ResourceMapBotModule resourceMapModule;
		PlayerResources playerResources;
		Shroud shroud;

		Actor mainConyard;
		Actor activeMcv;
		CPos? activeMcvLastKnownCell;
		int activeMcvLastSeenTick = -1;
		Actor activeConyard;
		bool mainBaseEverEstablished;
		bool initialBootstrapDeployIssued;
		Actor emergencyRecoveryMcv;
		CPos? emergencyRecoveryDeployCell;
		int emergencyRecoveryNextCheckTick;
		int emergencyRecoveryDeployIssuedTick = -1;
		CPos? emergencyRecoveryMoveLastProgressCell;
		int emergencyRecoveryMoveLastProgressTick = -1;
		bool mcvRetreatAfterRepackPending;
		CPos? mcvRetreatAnchor;
		CPos? mcvRetreatDestination;
		string mcvRetreatAnchorKind;
		CPos? mcvRetreatLastProgressCell;
		int mcvRetreatLastProgressTick = -1;
		int mcvRetreatNextCheckTick;
		int mcvRetreatPathCandidateOffset;
		const int McvRetreatRankedCandidatePool = 24;
		bool pendingMcvSlotReservation;
		int pendingMcvSlotReservationLiveCount;
		int surplusUnlockedPermanentConstructionYards;
		int highestPhysicalConstructionYardCapacity;
		bool pioneerClaimingComplete;
		uint acknowledgedRetreatDamageActorId;
		int acknowledgedRetreatDamageHp = -1;
		ExpansionTask expansionTask = new();
		int nextExpansionTaskId = 1;

		// ExpansionTask field aliases keep execution code compact while all strategic ownership
		// lives in one task object. Native-order/path/risk execution remains unchanged.
		Actor activeLandingCraft { get => expansionTask.LandingCraft; set => expansionTask.LandingCraft = value; }
		Actor activeLandingCraftReservationOwner { get => expansionTask.LandingCraftReservationOwner; set => expansionTask.LandingCraftReservationOwner = value; }
		Actor pendingMcvLandingCraftReservation { get => expansionTask.PendingLandingCraftReservation; set => expansionTask.PendingLandingCraftReservation = value; }
		CPos? targetResourceCenter { get => expansionTask.ResourceCenter; set => expansionTask.ResourceCenter = value; }
		CPos? targetDeployCell { get => expansionTask.DeployCell; set => expansionTask.DeployCell = value; }
		int targetReservationStartedTick { get => expansionTask.ReservationStartedTick; set => expansionTask.ReservationStartedTick = value; }
		bool postSeaUnloadDeployCommitted { get => expansionTask.PostSeaUnloadDeployCommitted; set => expansionTask.PostSeaUnloadDeployCommitted = value; }
		CPos? lastTransformCell;
		CPos? seaPickupMcvCell { get => expansionTask.SeaPickupMcvCell; set => expansionTask.SeaPickupMcvCell = value; }
		CPos? seaPickupCraftCell { get => expansionTask.SeaPickupCraftCell; set => expansionTask.SeaPickupCraftCell = value; }
		CPos? seaLandingCraftCell { get => expansionTask.SeaLandingCraftCell; set => expansionTask.SeaLandingCraftCell = value; }
		ExpansionStage stage { get => expansionTask.Stage; set => expansionTask.Stage = value; }
		// One-shot reservation for the first expansion refinery (refinery #3 total in the fast-expansion opening).
		// It is produced while the first expansion MCV travels, but BaseBuilder remains enabled.
		// The normal expansion lock is granted only when the FACT exists and placement
		// is actually about to happen, preserving firstExpansionSeen semantics.
		bool firstExpansionRefineryReservationActive;
		bool firstExpansionRefineryReservationCompleted;
		int firstExpansionRefineryInfrastructureSuspensionStartedTick = -1;
		Actor firstExpansionRefineryQueueActor;
		string firstExpansionRefineryReservedType;
		readonly HashSet<Actor> firstExpansionRefineryExistingActors = [];
		CPos? firstExpansionRefineryPlacementCell;
		bool firstExpansionRefineryPlacementIssued;
		int firstExpansionRefineryPlacementIssuedTick = -1;
		readonly List<CPos> exploredMapResourceObjectiveCells = [];
		bool exploredMapResourceObjectivesSeeded;
		bool coastalStagingForSeaExpansion
		{
			get => expansionTask.Mode == ExpansionTaskMode.CoastalStaging;
			set
			{
				if (value)
					expansionTask.Mode = ExpansionTaskMode.CoastalStaging;
				else if (expansionTask.Mode == ExpansionTaskMode.CoastalStaging)
					expansionTask.Mode = ExpansionTaskMode.None;
			}
		}
		bool coastalStagingReturnToSea { get => expansionTask.CoastalReturnToSea; set => expansionTask.CoastalReturnToSea = value; }
		CoastalStagingRepackOutcome coastalStagingRepackOutcome { get => expansionTask.CoastalRepackOutcome; set => expansionTask.CoastalRepackOutcome = value; }
		CPos? deferredRoutineFerryObjective { get => expansionTask.DeferredRoutineFerryObjective; set => expansionTask.DeferredRoutineFerryObjective = value; }
		int deferredRoutineFerryReservationStartedTick { get => expansionTask.DeferredRoutineFerryReservationStartedTick; set => expansionTask.DeferredRoutineFerryReservationStartedTick = value; }
		bool firstExpansionRefinerySuspendedForInfrastructure;
		bool firstExpansionRefineryRetryHold;
		int firstExpansionRefineryNoObjectiveSinceTick = -1;
		int nextCoastalStagingSearchTick;
		int coastalStagingNavalNoProgressSinceTick = -1;
		int coastalStagingFailedAttempts;
		int? coastalStagingRequiredNavalRegion;
		bool coastalStagingPreservedCommittedSeaTask;
		int? preCommitStrategicLandingCraftRegion;
		CPos? preCommitStrategicLandingCraftObjective;
		int preCommitStrategicLandingCraftDemandUntilTick = -1;
		readonly Dictionary<string, CPos?> cachedLandingCraftProducerLocations = [];
		readonly Dictionary<string, int> cachedLandingCraftProducerLocationUntilTicks = [];
		readonly Dictionary<string, int> cachedLandingCraftProducerBuildAreaRevisions = [];
		string landingCraftProducerPlacementItem;
		uint landingCraftProducerPlacementQueueActorId;
		int landingCraftProducerPlacementIssuedTick = -1;
		int landingCraftProducerPlacementRetries;
		int cachedLandingCraftBuildAreaRevisionTick = -1;
		int cachedLandingCraftBuildAreaRevision;
		CPos[] cachedRoutinePickupHandoffCells;
		int cachedRoutinePickupHandoffTerrainVersion = -1;
		CPos? preferredRoutinePickupMcvCell;
		CPos? preferredRoutinePickupCraftCell;
		// BOUNDED SEA ORE PLANNER NATIVE LST EXECUTION: geometry is planned once, then plain native Move/EnterTransport/Unload
		// owns execution. Progress watchdogs reissue only the current leg after a real stall;
		// no full pickup/landing replanning occurs while either actor is making cell progress.
		CPos? seaPickupMcvLastProgressCell;
		int seaPickupMcvLastProgressTick = -1;
		int seaPickupMcvStallRetries;
		readonly HashSet<CPos> seaPickupApproachRejectedCells = [];
		int seaPickupApproachRecoveryAttempts;
		CPos? seaPickupCraftLastProgressCell;
		int seaPickupCraftLastProgressTick = -1;
		int seaPickupCraftStallRetries;
		CPos? seaTransportLastProgressCell;
		int seaTransportLastProgressTick = -1;
		int seaTransportStallRetries;
		CPos? seaBoardingLastProgressCell;
		int seaBoardingLastProgressTick = -1;
		int seaBoardingRecoveryAttempts;
		SeaUnloadRecoveryPhase seaUnloadRecoveryPhase;
		CPos? seaUnloadOriginalLandingCraftCell;
		CPos? seaUnloadExpectedExitCell;
		int seaUnloadAttemptStartedTick = -1;
		int seaUnloadRecoveryAttempts;
		bool seaUnloadReturningToSource;
		readonly HashSet<(CPos GroundCell, CPos NavalCell)> seaUnloadMoveRejectedHandoffs = [];
		int nextSeaCargoPreservedRecheckTick;
		int seaLastRiskRevision = -1;
		int seaLastTransportLossExclusionRevision = -1;
		int seaTransportLossBlockedRevision = -1;
		int seaProductionLossBlockedRevision = -1;
		int seaTransportWaitStartedTick = -1;
		int seaExactPathFailureStartedTick = -1;
		bool lastLandingCraftPlanHadPickupFailure;
		bool lastLandingCraftPlanHadCrossingFailure;
		CommittedSeaCorridorRecoveryState committedSeaCorridorRecovery;
		RoutineSeaOreSearchState routineSeaOreSearch;
		RoutineSeaOreSearchState committedSeaGeometrySearch;
		RoutineSeaPickupProofState routineSeaPickupProof;
		int nextMcvObjectivePerfLogTick;
		int nextMcvRecoverySuccessPerfLogTick;
		int nextMcvRecoveryFailurePerfLogTick;
		int nextMcvRecoveryMovePerfLogTick;
		readonly HashSet<SeaTopologyFailureKey> seaTopologyFailures = [];
		readonly Dictionary<SeaLandingProofFailureKey, int> seaLandingProofFailuresUntil = [];
		int seaTopologyFailureTerrainVersion = -1;

		readonly Dictionary<CPos, int> failedFieldsUntil = [];
		readonly Dictionary<CPos, int> failedExpansionAreasUntil = [];
		// PIONEER candidate enumeration is RECON-silent. Exact ore cells legitimately seen by
		// any scout are remembered as fair expansion intel, so one failed ore can fall through
		// immediately to the next already-scouted objective instead of forcing the MCV home.
		readonly HashSet<CPos> scoutedExpansionAreas = [];
		readonly HashSet<CPos> secureRequiredExpansionAreas = [];
		readonly HashSet<CPos> reconRequiredExpansionAreas = [];
		readonly Dictionary<CPos, int> pioneerDomainClearRecheckWorldTick = [];
		CPos? activePioneerObjective;
		int activePioneerObjectiveStartedTick = -1;
		CPos? alternatePioneerObjective;
		int alternatePioneerObjectiveStartedTick = -1;
		readonly Dictionary<CPos, PioneerExecutionProofCacheEntry> pioneerExecutionProofCache = [];
		readonly Dictionary<CPos, PioneerExecutionProofWork> pioneerExecutionProofWork = [];
		readonly Dictionary<CPos, PioneerExecutionProofWork> pioneerCompletedSeaProofs = [];
		int pioneerProofPhaseWorldTick = -1;
		int pioneerProofPhasesThisTick;
		readonly Dictionary<CPos, int> futureRefineryProofFailuresUntil = [];
		bool pioneerSuccessorPrequeueActive;
		int pioneerSuccessorPrequeueBaselineLiveMcvCount;
		int pioneerSuccessorPrequeueRequestedTick = -1;
		readonly Dictionary<CPos, int> failedRefinerySitesUntil = [];
		Actor routineExpansionStructureQueueActor;
		string routineExpansionStructureType;
		bool routineExpansionStructurePlacementIssued;
		int routineExpansionStructureOwnershipStartedTick = -1;
		int routineExpansionStructurePlacementIssuedTick = -1;
		// Dedupe only: this signature is written by logging calls and never read by queue decisions.
		string lastBuildingQueueHandoffDiagnostic;
		const int RoutineExpansionStructureOwnershipTimeoutTicks = 150;
		bool refineryPlacementRecoveryPending;
		CPos? refineryPlacementFailedSite;
		int nextRouteRecheckTick;
		CPos? movingMcvLastProgressCell;
		int movingMcvLastProgressTick = -1;
		int movingMcvStallRetries;
		int conyardTransformIssuedTick = -1;
		int conyardTransformRetries;
		int deployClearanceStartedTick = -1;
		int nextDeployClearanceOrderTick;
		int deployClearanceReplans;
		int repackTransformIssuedTick = -1;
		int repackTransformRetries;


		int nextNoOreStatusLogTick;
		int nextSeaPlanningTick;
		int nextSeaTransportRequestTick;
		int nextNavalCapabilityRetryTick;
		bool navalCapabilityDemandLatched;
		bool earlyNavalTopologyEvaluated;
		bool earlyNavalTopologyRequired;
		CPos? earlyNavalTopologyObjective;
		int earlyNavalTopologySourceLandmass = -1;
		int earlyNavalTopologyTargetLandmass = -1;
		int nextSeaRouteRiskRecheckTick;
		int nextSeaUnloadRetryTick;
		int nextLandExpansionPlanningTick;
		int scanTicks;
		int buildMcvTicks;
		int nextMcvPressureGateLogTick;
		int placementFailures;
		int nextSeaBoardingRetryTick;
		int baseBuilderLockToken = Actor.InvalidConditionToken;

		public FransMcvExpansionManagerBotModule(Actor self, FransMcvExpansionManagerBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			playerActor = self;

			if (world.Type == WorldType.Editor)
				return;

			mcvs = new ActorIndex.OwnerAndNamesAndTrait<TransformsInfo>(world, Info.McvTypes, player);
			constructionYards = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, Info.ConstructionYardTypes, player);
			mcvFactories = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, Info.McvFactoryTypes, player);
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			requestUnitProduction = self.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
			transportService = self.TraitsImplementing<IFransCaptureTransportService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires FransTransportCommanderBotModule.");
			openingBuildOrderService = self.TraitsImplementing<IFransBaseBuilderService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires FransBaseBuilderBotModule.");
			strategicMapService = self.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires FransStrategicMapBotModule.");
			groundCommanderService = self.TraitsImplementing<IFransCommanderCoreService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires Ground Commander service.");
			generalService = self.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires FransGeneralBotModule for read-only SECURE anchor coordination.");
			commandBidService = self.TraitsImplementing<IFransCommandBidService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires FransCommandBidBotModule for DEFEND-pressure coordination.");
			combatIntelService = self.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires FransCombatIntelBotModule.");
			riskModelService = self.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires FransRiskModelBotModule.");
			economicStateService = self.TraitsImplementing<IFransEconomicSaturationService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires FransEconomicSaturationBotModule.");
			captureSecurityServices = self.TraitsImplementing<IFransCaptureSecurityService>().ToArray();
			groundUnitReservationService = self.TraitsImplementing<IFransGroundUnitReservationService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMcvExpansionManagerBotModule requires FransGroundCommanderBotModule ground-unit reservation service.");
			playerResources = self.Trait<PlayerResources>();
			shroud = self.TraitOrDefault<Shroud>();
		}

		void IBotEnabled.BotEnabled(IBot bot)
		{
			orderBot = bot;
		}

		bool IsValidOrderSubject(Actor actor)
		{
			return actor != null && !actor.Disposed && actor.IsInWorld && !actor.IsDead && actor.Owner == player;
		}

		void QueueStopOrder(IBot bot, Actor actor)
		{
			if (!IsValidOrderSubject(actor))
				return;

			var sink = bot ?? orderBot;
			if (sink != null)
			{
				pendingStopOrders.Remove(actor);
				pendingMoveOrders.Remove(actor);
				sink.QueueOrder(new Order("Stop", actor, false));
				return;
			}

			pendingMoveOrders.Remove(actor);
			pendingStopOrders.Add(actor);
		}

		void QueueMoveOrder(IBot bot, Actor actor, CPos destination, bool queued = false)
		{
			if (!IsValidOrderSubject(actor) || !world.Map.Contains(destination) || actor.TraitOrDefault<Mobile>() == null)
			{
				if (actor != null && Info.McvTypes.Contains(actor.Info.Name))
					LogMcvWaitingState(actor, "MoveOrderRejectedInvalidActorOrDestination");
				return;
			}

			var sink = bot ?? orderBot;
			if (sink != null)
			{
				pendingStopOrders.Remove(actor);
				pendingMoveOrders.Remove(actor);
				sink.QueueOrder(new Order("Move", actor, Target.FromCell(world, destination), queued));
				return;
			}

			pendingStopOrders.Remove(actor);
			pendingMoveOrders[actor] = new PendingMoveOrder(destination, queued);
		}

		void FlushPendingSynchronizedActions(IBot bot)
		{
			if (bot == null || pendingStopOrders.Count == 0 && pendingMoveOrders.Count == 0)
				return;

			var actors = pendingStopOrders
				.Concat(pendingMoveOrders.Keys)
				.Distinct()
				.OrderBy(actor => actor.ActorID)
				.ToArray();

			foreach (var actor in actors)
			{
				if (!IsValidOrderSubject(actor))
					continue;

				if (pendingStopOrders.Contains(actor))
					bot.QueueOrder(new Order("Stop", actor, false));
				else if (pendingMoveOrders.TryGetValue(actor, out var move) && world.Map.Contains(move.Destination) &&
					actor.TraitOrDefault<Mobile>() != null)
					bot.QueueOrder(new Order("Move", actor, Target.FromCell(world, move.Destination), move.Queued));
			}

			pendingStopOrders.Clear();
			pendingMoveOrders.Clear();
		}

		void LogMcvIdentity(Actor mcv)
		{
			if (mcv == null)
				return;

			var signature = $"{mcv.ActorID}|{stage}|{expansionTask.Id}|{expansionTask.Mode}";
			if (lastMcvIdentityDebugState == signature)
				return;

			lastMcvIdentityDebugState = signature;
			FransBotLog.BotDebug(world,
				"[MCV DEBUG] Tick={0} Player={1} PlayerActorID={2} ActorID={3} State={4}/{5} Pos={6}",
				world.WorldTick, player, player.PlayerActor.ActorID, mcv.ActorID, stage, expansionTask.Mode, mcv.Location);
			LogMcvExpansionState(mcv, "Evaluate", "StateChanged");
		}

		void LogMcvExpansionState(Actor mcv, string action, string reason)
		{
			var actorId = mcv?.ActorID ?? 0u;
			var objective = targetResourceCenter.HasValue ? targetResourceCenter.Value.ToString() : "None";
			var deploy = targetDeployCell.HasValue ? targetDeployCell.Value.ToString() : "None";
			var mission = expansionTask.Id > 0 ? $"Task#{expansionTask.Id}/{expansionTask.Mode}" : "None";
			var reservation = targetReservationStartedTick >= 0 ? $"WT{targetReservationStartedTick}" : "None";
			var signature = $"{actorId}|{mission}|{stage}|{objective}|{deploy}|{reservation}|{action}|{reason}";
			if (lastMcvExpansionDebugState == signature)
				return;

			lastMcvExpansionDebugState = signature;
			FransBotLog.BotDebug(world,
				"[MCV EXPANSION] Tick={0} Player={1} PlayerActorID={2} ActorID={3} HasMission={4} Mission={5} State={6} Reservation={7} Objective={8} Target={9} Action={10} Reason={11}",
				world.WorldTick, player, player.PlayerActor.ActorID, actorId == 0u ? "None" : actorId.ToString(),
				expansionTask.Id > 0, mission, stage, reservation, objective, deploy, action, reason);
		}

		void LogMcvWaitingState(Actor mcv, string reason)
		{
			var actorId = mcv?.ActorID ?? 0u;
			var signature = $"{actorId}|{stage}|{expansionTask.Id}|{reason}";
			if (lastMcvWaitingDebugState == signature)
				return;

			lastMcvWaitingDebugState = signature;
			LogMcvExpansionState(mcv, "Waiting", reason);
			FransBotLog.BotDebug(world,
				"[MCV WAITING] Tick={0} Player={1} PlayerActorID={2} ActorID={3} State={4}/{5} Reason={6}",
				world.WorldTick, player, player.PlayerActor.ActorID, actorId == 0u ? "None" : actorId.ToString(),
				stage, expansionTask.Mode, reason);
		}

		void LogMcvTransportDemandState(int liveUsableLst, int queuedValidLst, int requestedLst,
			int sharedPool, int sharedPoolCap, int? navalRegion, string action, string reason)
		{
			if (stage != ExpansionStage.WaitingForSeaTransport || expansionTask.Mode != ExpansionTaskMode.SeaOre)
				return;

			var mcvId = activeMcv?.ActorID ?? 0u;
			var objective = targetResourceCenter.HasValue ? targetResourceCenter.Value.ToString() : "None";
			var region = navalRegion.HasValue ? navalRegion.Value.ToString() : "Unknown";
			var productionRequest = queuedValidLst > 0 || requestedLst > 0 ? "active" : "inactive";
			var signature = $"{expansionTask.Id}|{mcvId}|{objective}|{stage}|{liveUsableLst}|{queuedValidLst}|{requestedLst}|" +
				$"{sharedPool}|{sharedPoolCap}|{region}|{productionRequest}|{action}|{reason}";
			if (lastMcvTransportDemandDebugState == signature)
				return;

			lastMcvTransportDemandDebugState = signature;
			FransBotLog.BotDebug(world,
				"[MCV TRANSPORT DEMAND] Tick={0} Player={1} task={2} mcv={3} objective={4} stage={5} liveUsableLst={6} queuedValidLst={7} requestedLst={8} productionRequest={9} sharedPool={10}/{11} navalRegion={12} reason={13} action={14}",
				world.WorldTick, player, expansionTask.Id, mcvId, objective, stage, liveUsableLst,
				queuedValidLst, requestedLst, productionRequest, sharedPool, sharedPoolCap, region, reason, action);
		}

		void LogCommittedSeaExecutionDiagnostic(string outcome, Actor craft, string reason)
		{
			if ((stage != ExpansionStage.WaitingForSeaTransport && stage != ExpansionStage.MovingToSeaPickup) ||
				expansionTask.Mode != ExpansionTaskMode.SeaOre)
				return;

			var mcvId = activeMcv?.ActorID ?? 0u;
			var craftId = craft?.ActorID ?? 0u;
			var objective = targetResourceCenter.HasValue ? targetResourceCenter.Value.ToString() : "None";
			var pickupMcv = preferredRoutinePickupMcvCell.HasValue ? preferredRoutinePickupMcvCell.Value.ToString() : "None";
			var pickupCraft = preferredRoutinePickupCraftCell.HasValue ? preferredRoutinePickupCraftCell.Value.ToString() : "None";
			var landing = seaLandingCraftCell.HasValue ? seaLandingCraftCell.Value.ToString() : "None";
			var claimable = craft != null && transportService.CanStrategicExpansionClaimTransport(craft);
			var ownedByTask = craft != null && activeLandingCraft == craft &&
				activeLandingCraftReservationOwner == activeMcv;
			var waited = seaTransportWaitStartedTick < 0 ? 0 : world.WorldTick - seaTransportWaitStartedTick;
			var eligibility = lastLandingCraftPlanDiagnostic ?? "NotEvaluated";
			var signature = $"{expansionTask.Id}|{mcvId}|{objective}|{pickupMcv}|{pickupCraft}|{landing}|" +
				$"{outcome}|{craftId}|{claimable}|{ownedByTask}|{reason}|{eligibility}";
			if (signature == lastCommittedSeaExecutionDiagnosticSignature)
				return;

			lastCommittedSeaExecutionDiagnosticSignature = signature;
			FransBotLog.BotDebug(world,
				"{0}: [E25 POST-COMMIT FERRY] task={1} mcv={2} objective={3} stage={4} waitedWT={5} " +
				"pickupMcv={6} pickupCraft={7} landing={8} selectedLst={9} claimableNow={10} ownedByTask={11} outcome={12} reason={13}; eligibility={14}.",
				player, expansionTask.Id, mcvId, objective, stage, waited, pickupMcv, pickupCraft, landing,
				craftId == 0u ? "None" : craftId.ToString(), claimable, ownedByTask, outcome, reason ?? "None", eligibility);
		}

		void LogCommittedSeaCorridorRecovery(string outcome, CommittedSeaCorridorRecoveryState recovery,
			CPos? replacementPickupMcv, CPos? replacementPickupCraft, CPos? replacementLanding,
			CPos? replacementDeploy, string reason, string eligibility = null)
		{
			if (recovery == null)
				return;

			var replacement = replacementPickupMcv.HasValue && replacementPickupCraft.HasValue &&
				replacementLanding.HasValue && replacementDeploy.HasValue
				? $"pickupMcv={replacementPickupMcv.Value},pickupCraft={replacementPickupCraft.Value},landing={replacementLanding.Value},deploy={replacementDeploy.Value}"
				: "None";
			var lifetime = world.WorldTick - recovery.StartedTick;
			var remaining = recovery.DeadlineTick == int.MaxValue ? int.MaxValue : recovery.DeadlineTick - world.WorldTick;
			var progressBucket = recovery.PassesCompleted / 8;
			var signature = $"{recovery.TaskId}|{recovery.StartedTick}|{recovery.Objective}|" +
				$"{outcome}|{replacement}|{reason}|{eligibility}|paused={recovery.PausedForOriginalEligibility}|" +
				$"progressBucket={progressBucket}|tested={recovery.TestedCorridors}";
			if (signature == lastCommittedSeaCorridorRecoveryDiagnosticSignature)
				return;

			lastCommittedSeaCorridorRecoveryDiagnosticSignature = signature;
			FransBotLog.BotDebug(world,
				"{0}: [E25 FERRY CORRIDOR RECOVERY] task={1} generation={1}:{19} mcv={2} sourceMcv={20} sourceRebases={21} objective={3} outcome={4} " +
				"original=pickupMcv={5},pickupCraft={6},landing={7},deploy={8} replacement={9} testedCorridors={10} " +
				"passes={11}/{12} pickupCursor={13}/{14} lifetimeWT={15} deadlineRemainingWT={16} reason={17}; eligibility={18}.",
				player, recovery.TaskId, recovery.McvActorId, recovery.Objective, outcome,
				recovery.OriginalPickupMcvCell, recovery.OriginalPickupCraftCell,
				recovery.OriginalLandingCraftCell, recovery.OriginalDeployCell, replacement,
				recovery.TestedCorridors, recovery.PassesCompleted, recovery.MaximumPasses,
				recovery.NextPickupBeachIndex, recovery.RankedAlternativePickupBeaches.Length,
				lifetime, remaining == int.MaxValue ? "Unlimited" : remaining.ToString(),
				reason ?? "None", eligibility ?? "NotEvaluated", recovery.StartedTick, recovery.McvCell,
				recovery.SourceRebases);
		}

		void LogMcvTarget(Actor mcv, CPos candidate, bool valid, string reason,
			CPos? deployCell = null, int? score = null, int? pathLength = null)
		{
			if (mcv == null)
				return;

			var signature = $"{valid}|{reason}|{(deployCell.HasValue ? deployCell.Value.ToString() : "None")}";
			var key = (mcv.ActorID, candidate);
			if (mcvTargetDebugStates.TryGetValue(key, out var previous) && previous == signature)
				return;

			mcvTargetDebugStates[key] = signature;
			FransBotLog.BotDebug(world,
				"[MCV TARGET] Tick={0} Player={1} PlayerActorID={2} ActorID={3} Node={4} Deploy={5} Score={6} PathLength={7} Valid={8} Reason={9}",
				world.WorldTick, player, player.PlayerActor.ActorID, mcv.ActorID, candidate,
				deployCell.HasValue ? deployCell.Value.ToString() : "None", score.HasValue ? score.Value.ToString() : "n/a",
				pathLength.HasValue ? pathLength.Value.ToString() : "n/a", valid, reason);
		}

		void LogMcvMoveOrder(Actor mcv, CPos destination, int waypointCount, string reason)
		{
			if (mcv == null)
				return;

			lastMcvWaitingDebugState = null;
			FransBotLog.BotDebug(world,
				"[MCV ORDER] Tick={0} Player={1} PlayerActorID={2} ActorID={3} Order=QueueMoveOrder Destination={4} Waypoints={5} State={6}/{7} Reason={8}",
				world.WorldTick, player, player.PlayerActor.ActorID, mcv.ActorID, destination,
				waypointCount, stage, expansionTask.Mode, reason);
		}

		void LogMcvDeployment(Actor mcv, bool issued, string reason)
		{
			if (mcv == null)
				return;

			var signature = $"{mcv.ActorID}|{mcv.Location}|{mcv.IsIdle}|{issued}|{reason}";
			if (lastMcvDeployDebugState == signature)
				return;

			lastMcvDeployDebugState = signature;
			FransBotLog.BotDebug(world,
				"[MCV DEPLOY] Tick={0} Player={1} PlayerActorID={2} ActorID={3} Pos={4} Idle={5} DeployTransformIssued={6} State={7}/{8} Reason={9}",
				world.WorldTick, player, player.PlayerActor.ActorID, mcv.ActorID, mcv.Location, mcv.IsIdle,
				issued, stage, expansionTask.Mode, reason);
		}

		bool BeginExpansionTask(ExpansionTaskMode mode, CPos? objective, CPos? deployCell,
			ExpansionStage initialStage, int reservationTick, string reason)
		{
			// Ground-Commander rule: never overwrite live mission ownership. Every replacement
			// must pass through Abort/Release first, which releases PROC/LST/queue ownership too.
			if (expansionTask.Id > 0)
			{
				FransBotLog.BotDebug(world,
					"{0}: EXPANSION TASK COMMIT REFUSED for mode={1} objective={2}; task #{3}/{4} still owns objective {5}. Caller must Abort/Release first.",
					player, mode, objective.HasValue ? objective.Value.ToString() : "none", expansionTask.Id, expansionTask.Mode,
					expansionTask.ResourceCenter.HasValue ? expansionTask.ResourceCenter.Value.ToString() : "none");
				return false;
			}

			expansionTask = new ExpansionTask
			{
				Id = nextExpansionTaskId++,
				Mode = mode,
				Stage = initialStage,
				ResourceCenter = objective,
				DeployCell = deployCell,
				ReservationStartedTick = reservationTick
			};

			if ((mode == ExpansionTaskMode.LandOre || mode == ExpansionTaskMode.SeaOre) &&
				objective.HasValue && IsTrackedPioneerObjective(objective.Value))
				CompleteActivePioneerObjective($"ExpansionTask #{expansionTask.Id} committed {mode}");

			ResetTaskExecutionProgress();
			seaTransportWaitStartedTick = initialStage == ExpansionStage.WaitingForSeaTransport ? world.WorldTick : -1;
			FransBotLog.BotDebug(world,
				"{0}: EXPANSION TASK #{1} COMMIT mode={2} objective={3} deploy={4} stage={5}; {6}",
				player, expansionTask.Id, mode, objective.HasValue ? objective.Value.ToString() : "none",
				deployCell.HasValue ? deployCell.Value.ToString() : "none", initialStage, reason);
			if ((mode == ExpansionTaskMode.LandOre || mode == ExpansionTaskMode.SeaOre) && objective.HasValue)
				FransBotLog.BotDebug(world,
					"[PIONEER CLAIM] Tick={0} Player={1} Task={2} MCV={3} Objective={4} Action=CommitKnownOre Reason={5}",
					world.WorldTick, player, expansionTask.Id, activeMcv?.ActorID.ToString() ?? "none", objective.Value,
					reason ?? "known ore passed current route and tactical-risk validation");
			return true;
		}

		void ChangeExpansionTaskMode(ExpansionTaskMode mode, string reason)
		{
			if (expansionTask.Mode == mode)
				return;

			var previous = expansionTask.Mode;
			expansionTask.Mode = mode;
			if (expansionTask.Id > 0)
				FransBotLog.BotDebug(world,
					"{0}: EXPANSION TASK #{1} mode {2} -> {3}: {4}.", player, expansionTask.Id, previous, mode, reason);
		}

		void ReturnExpansionTaskToIdle(string reason)
		{
			var completedTaskId = expansionTask.Id;
			var completedMode = expansionTask.Mode;
			var completedObjective = expansionTask.ResourceCenter;

			ReleaseBaseBuilderLock();
			ReleaseActiveLandingCraftReservation();
			activeLandingCraft = null;
			pendingMcvLandingCraftReservation = null;
			coastalStagingReturnToSea = false;
			coastalStagingRepackOutcome = CoastalStagingRepackOutcome.None;
			coastalStagingForSeaExpansion = false;
			coastalStagingFailedAttempts = 0;
			coastalStagingRequiredNavalRegion = null;
			coastalStagingPreservedCommittedSeaTask = false;
			deferredRoutineFerryObjective = null;
			deferredRoutineFerryReservationStartedTick = -1;
			ClearTarget();
			stage = ExpansionStage.Idle;
			expansionTask.Mode = ExpansionTaskMode.None;
			expansionTask.Id = 0;
			seaTransportWaitStartedTick = -1;
			seaProductionLossBlockedRevision = -1;

			if (completedTaskId > 0)
				FransBotLog.BotDebug(world,
					"{0}: EXPANSION TASK #{1} RELEASE mode={2} objective={3}: {4}. Planner may immediately choose the next ore.",
					player, completedTaskId, completedMode,
					completedObjective.HasValue ? completedObjective.Value.ToString() : "none", reason);
		}

		void AbortExpansionTaskToIdle(IBot bot, string reason, CPos? failedSite = null)
		{
			var ownedSite = failedSite ?? targetResourceCenter ?? targetDeployCell;
			CancelOwnedRoutineExpansionStructureIfQueued(bot, reason);
			AbortFirstExpansionRefineryAttempt(bot, reason, ownedSite);
			ReturnExpansionTaskToIdle(reason);
			nextLandExpansionPlanningTick = world.WorldTick;
		}

		bool CommitLandOreTask(IBot bot, Actor mcv, Mobile mobile, OreChoice choice, string reason)
		{
			if (!BeginExpansionTask(ExpansionTaskMode.LandOre, choice.ResourceCenter, choice.DeployCell,
				ExpansionStage.MovingToOre, world.WorldTick, reason))
				return false;
			nextRouteRecheckTick = world.WorldTick + Info.RouteRecheckInterval;
			if (TryYieldToEarlierAlliedMcvReservation(bot))
				return false;

			QueueRiskAwareMove(mcv, mobile, choice.DeployCell);
			return true;
		}

		bool HasCommittedSeaExpansionDemand =>
			(expansionTask.Mode == ExpansionTaskMode.SeaOre && targetResourceCenter.HasValue &&
				(stage == ExpansionStage.WaitingForSeaTransport || stage == ExpansionStage.MovingToSeaPickup ||
				 stage == ExpansionStage.SeaLoading || stage == ExpansionStage.SeaTransporting ||
				 stage == ExpansionStage.SeaUnloading || stage == ExpansionStage.SeaCargoPreserved)) ||
			deferredRoutineFerryObjective.HasValue;

		bool HasLiveLandingCraftExecutionDemand =>
			activeLandingCraft == null &&
			(IsLiveOwnedLandingCraft(pendingMcvLandingCraftReservation) ||
			 (HasCommittedSeaExpansionDemand && coastalStagingForSeaExpansion && activeConyard != null &&
				activeConyard.IsInWorld && !activeConyard.IsDead && activeConyard.Owner == player) ||
			 ((stage == ExpansionStage.WaitingForSeaTransport) && IsLiveOwnedMcv(activeMcv)));

		bool HasActivePreCommitLandingCraftDemand =>
			preCommitStrategicLandingCraftRegion.HasValue && preCommitStrategicLandingCraftObjective.HasValue &&
			(activePioneerObjective == preCommitStrategicLandingCraftObjective ||
			 alternatePioneerObjective == preCommitStrategicLandingCraftObjective ||
			 world.WorldTick <= preCommitStrategicLandingCraftDemandUntilTick);

		void MarkPreCommitLandingCraftDemand(int navalRegion, CPos objective)
		{
			preCommitStrategicLandingCraftRegion = navalRegion;
			preCommitStrategicLandingCraftObjective = objective;
			// REGION-LOCKED RELEASE ARBITRATION: the short timestamp is now only a handoff grace
			// after objective bookkeeping changes. While this exact PIONEER objective remains
			// PRIMARY/ALTERNATE, strategic production demand stays live until same-region supply
			// appears or the objective is explicitly abandoned. This reserves the next freed
			// slot of the global three-LST pool for the required naval region.
			preCommitStrategicLandingCraftDemandUntilTick = world.WorldTick + Math.Max(500, Info.SeaPlanningInterval * 4);
		}

		void ClearPreCommitLandingCraftDemand()
		{
			preCommitStrategicLandingCraftRegion = null;
			preCommitStrategicLandingCraftObjective = null;
			preCommitStrategicLandingCraftDemandUntilTick = -1;
			lastSeaSupplyDiagnosticSignature = null;
			lastRegionalLandingCraftOrderDiagnostic = null;
			lastRegionalLandingCraftOrderSignature = null;
			lastRegionalLandingCraftOrderObjective = null;
			lastRegionalLandingCraftOrderRegion = null;
		}


		bool IFransAmphibiousExpansionService.HasStrategicLandingCraftProductionDemand =>
			HasLiveLandingCraftExecutionDemand || HasActivePreCommitLandingCraftDemand;

		bool IFransAmphibiousExpansionService.IsLandingCraftPendingForExpansion(Actor craft)
		{
			if (!IsLiveOwnedLandingCraft(craft) || !transportService.CanStrategicExpansionClaimTransport(craft))
				return false;

			// Actual LST ownership is centralized in FransTransportCommander via
			// TryReserveExternalTransport(). This service exposes only the short pre-commit
			// intent window, so Capture/GroundTransfer cannot steal the exact craft while an
			// MCV/FACT transition is still preparing the reservation.
			if (craft == pendingMcvLandingCraftReservation && IsLiveOwnedLandingCraft(pendingMcvLandingCraftReservation))
				return true;

			if (HasCommittedSeaExpansionDemand && coastalStagingForSeaExpansion && activeConyard != null && activeConyard.IsInWorld &&
				!activeConyard.IsDead && activeConyard.Owner == player)
				return FindAvailableLandingCraft(activeConyard) == craft;

			if (stage != ExpansionStage.WaitingForSeaTransport || !IsLiveOwnedMcv(activeMcv))
				return false;

			return FindAvailableLandingCraft(activeMcv) == craft;
		}

		protected override void TraitEnabled(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			if (surplusUnlockedPermanentConstructionYards <= 0)
				surplusUnlockedPermanentConstructionYards = Info.PreSurplusPermanentConstructionYards;
			pioneerClaimingComplete = false;

			FransBotLog.BotDebug(world,
				"{0}: FransMcvExpansion TOPOLOGY-PROVEN EARLY NAVY active: water percentage never creates naval demand. Explore Map resource topology may bootstrap one early Ship queue only when a known sea-accessible ore objective is on a different ground landmass from the main FACT. PIONEER successor, FACT->PROC proof, actionable regional LST supply, bounded CoastalStaging and SeaOre scan budgets remain active. Completed sea search cache {1} WT; RETREAT pathfinding remains batched to {2} candidate(s)/pass.",
				player, Info.RoutineSeaOreSearchCacheDuration, Info.McvRetreatMaximumPathCandidatesPerAnchor);

			scanTicks = world.LocalRandom.Next(1, Info.ScanInterval + 1);
			buildMcvTicks = world.LocalRandom.Next(1, Info.BuildMcvInterval + 1);
			nextSeaPlanningTick = world.WorldTick + world.LocalRandom.Next(1, Info.SeaPlanningInterval + 1);
		}

		protected override void TraitDisabled(Actor self)
		{
			ReturnExpansionTaskToIdle("MCV expansion trait disabled");
			ClearRoutineExpansionStructureOwnership();
			scoutedExpansionAreas.Clear();
			reconRequiredExpansionAreas.Clear();
			secureRequiredExpansionAreas.Clear();
			activePioneerObjective = null;
			activePioneerObjectiveStartedTick = -1;
			alternatePioneerObjective = null;
			alternatePioneerObjectiveStartedTick = -1;
			pioneerExecutionProofCache.Clear();
			pioneerExecutionProofWork.Clear();
			pioneerCompletedSeaProofs.Clear();
			futureRefineryProofFailuresUntil.Clear();
			pioneerSuccessorPrequeueActive = false;
			pioneerSuccessorPrequeueRequestedTick = -1;
			pioneerClaimingComplete = false;
			firstExpansionRefineryReservationActive = false;
			earlyNavalTopologyEvaluated = false;
			earlyNavalTopologyRequired = false;
			earlyNavalTopologyObjective = null;
			earlyNavalTopologySourceLandmass = -1;
			earlyNavalTopologyTargetLandmass = -1;
			firstExpansionRefinerySuspendedForInfrastructure = false;
			firstExpansionRefineryInfrastructureSuspensionStartedTick = -1;
			firstExpansionRefineryQueueActor = null;
			firstExpansionRefineryReservedType = null;
			firstExpansionRefineryExistingActors.Clear();
			ResetFirstExpansionRefineryPlacementAttempt();
			ResetLandingCraftProducerPlacementWatchdog();
			coastalStagingFailedAttempts = 0;
			coastalStagingRequiredNavalRegion = null;
			coastalStagingPreservedCommittedSeaTask = false;
			preCommitStrategicLandingCraftRegion = null;
			preCommitStrategicLandingCraftObjective = null;
			preCommitStrategicLandingCraftDemandUntilTick = -1;
			seaTopologyFailures.Clear();
			seaLandingProofFailuresUntil.Clear();
			seaTopologyFailureTerrainVersion = -1;
			pendingStopOrders.Clear();
			pendingMoveOrders.Clear();
			mcvTargetDebugStates.Clear();
			lastMcvIdentityDebugState = null;
			lastMcvExpansionDebugState = null;
			lastMcvWaitingDebugState = null;
			lastMcvDeployDebugState = null;
			lastMcvTransportDemandDebugState = null;
			lastBuildingQueueHandoffDiagnostic = null;
			routineSeaOreSearch = null;
			committedSeaGeometrySearch = null;
			routineSeaPickupProof = null;
			committedSeaCorridorRecovery = null;
		}



		int IFransExpansionStateService.DesiredPermanentConstructionYards => CurrentPermanentFactFloor();
		bool IFransExpansionStateService.CanAcquireConstructionYardSlot => CountConstructionYardSlots() < CurrentConstructionYardSlotCeiling();
		bool IFransExpansionStateService.FirstExpansionRefinerySuspendedForInfrastructure => firstExpansionRefinerySuspendedForInfrastructure;
		bool IFransExpansionStateService.MissionCriticalNavalAccessRequired =>
			!HasUsableLandingCraftProducerForCurrentDemand() &&
			((((stage == ExpansionStage.WaitingForSeaTransport) &&
				IsLiveOwnedMcv(activeMcv) && FindAvailableLandingCraft(activeMcv) == null) ||
			 (coastalStagingForSeaExpansion && activeConyard != null && activeConyard.IsInWorld &&
				!activeConyard.IsDead && activeConyard.Owner == player && FindAvailableLandingCraft(activeConyard) == null)) ||
			 (navalCapabilityDemandLatched && CanPlaceAnyLandingCraftProducerFromCurrentBase()));
		bool IFransExpansionStateService.NavalCapabilityDemandActive =>
			navalCapabilityDemandLatched && !HasOwnedLandingCraftProducer();
		bool IFransExpansionStateService.NavalProductionOpportunityAvailable =>
			!HasOwnedLandingCraftProducer() && CanPlaceAnyLandingCraftProducerFromCurrentBase();
		bool IFransExpansionStateService.TryGetNavalProductionLocation(string actorType, out CPos location)
		{
			location = default;
			if (string.IsNullOrEmpty(actorType) || !Info.LandingCraftProducerTypes.Contains(actorType))
				return false;

			var hasRequiredRegion = TryGetRequiredLandingCraftProductionRegion(out var requiredNavalRegion);
			var resolved = FindLandingCraftProducerLocation(actorType,
				hasRequiredRegion ? requiredNavalRegion : null);
			if (!resolved.HasValue)
				return false;

			location = resolved.Value;
			return true;
		}
		bool IFransExpansionStateService.FirstExpansionRefineryPrebuildAllowed =>
			!firstExpansionRefineryRetryHold && !firstExpansionRefineryReservationCompleted &&
			!firstExpansionRefinerySuspendedForInfrastructure &&
			openingBuildOrderService?.OpeningMcvCompleted == true;

		int IFransExpansionStateService.ProtectedFirstExpansionRefineryRemainingCost
		{
			get
			{
				// An aborted first-expansion attempt deliberately enters retry-hold until a new
				// MCV objective is committed. During that idle interval there is no queue owner
				// and therefore no cash reservation to protect. This prevents a stale 1400-credit
				// reserve from surviving after the expansion task itself has been released.
				if (firstExpansionRefineryReservationCompleted || firstExpansionRefinerySuspendedForInfrastructure ||
					openingBuildOrderService?.OpeningMcvCompleted != true ||
					(firstExpansionRefineryRetryHold && !HasCommittedFirstExpansionRefineryRetryObjective()) ||
					(firstExpansionRefineryReservationActive && !HasCommittedFirstExpansionRefineryRetryObjective() &&
					 firstExpansionRefineryNoObjectiveSinceTick >= 0 &&
					 world.WorldTick - firstExpansionRefineryNoObjectiveSinceTick >= Info.FirstExpansionRefineryObjectiveGraceTicks))
					return 0;

				var refineryType = FirstExpansionRefineryType();
				if (refineryType == null)
					return 0;

				var queue = FindReservedFirstExpansionRefineryQueue(refineryType);
				if (queue == null)
					return 0;

				var item = queue.AllQueued().FirstOrDefault(i => i.Item == refineryType);
				if (item != null)
					return Math.Max(0, item.RemainingCost);

				if (!world.Map.Rules.Actors.TryGetValue(refineryType, out var actorInfo))
					return 0;

				return Math.Max(0, queue.GetProductionCost(actorInfo));
			}
		}

		bool IFransExpansionStateService.CriticalMcvProductionDemandActive => pendingMcvSlotReservation;
		bool IFransExpansionStateService.PioneerAirScoutDemandActive => NeedsPioneerAirScoutDemand();
		IReadOnlyList<CPos> IFransExpansionStateService.SecureRequiredExpansionObjectives
		{
			get
			{
				// Only PRIMARY PIONEER may create expansion-unblock SECURE pressure. The alternate
				// target is scouting insurance only until it is explicitly promoted.
				if (!activePioneerObjective.HasValue || IsExpansionGroundSecured(activePioneerObjective.Value) || !HasSecureRequirementNear(activePioneerObjective.Value))
					return Array.Empty<CPos>();
				return new[] { activePioneerObjective.Value };
			}
		}
		IReadOnlyList<CPos> IFransExpansionStateService.ReconRequiredExpansionObjectives
		{
			get
			{
				var objectives = new List<CPos>(2);
				foreach (var objective in TrackedPioneerObjectives())
					if (!IsExpansionGroundSecured(objective) && HasReconRequirementNear(objective) && !HasSecureRequirementNear(objective))
						objectives.Add(objective);

				return objectives.Count == 0 ? Array.Empty<CPos>() : objectives.ToArray();
			}
		}
		bool IFransExpansionStateService.TryGetPioneerReconObjectiveNear(CPos referenceCell, out CPos objectiveCell)
		{
			// PRIMARY and ALTERNATE may both publish exact-cell RECON. Existing persistent RECON
			// redirects to the nearest matching PIONEER objective, while SECURE remains PRIMARY-only.
			objectiveCell = default;
			var radius = Math.Max(Info.ExpansionTargetFailureRadius * 2, Info.ExpansionTargetFailureRadius + 1);
			var radiusSquared = radius * radius;
			var match = TrackedPioneerObjectives()
				.Where(objective => HasReconRequirementNear(objective) && !HasSecureRequirementNear(objective) &&
					!IsExpansionGroundSecured(objective) && (objective - referenceCell).LengthSquared <= radiusSquared)
				.OrderBy(objective => (objective - referenceCell).LengthSquared)
				.ThenBy(objective => objective.X)
				.ThenBy(objective => objective.Y)
				.Select(objective => (CPos?)objective)
				.FirstOrDefault();
			if (!match.HasValue)
				return false;

			objectiveCell = match.Value;
			return true;
		}
		bool IFransExpansionStateService.TryGetActiveExpansionReservation(out CPos objective, out CPos deployCell, out uint mcvActorId, out int reservationTick)
		{
			objective = default;
			deployCell = default;
			mcvActorId = 0;
			reservationTick = -1;
			if (!targetResourceCenter.HasValue || !targetDeployCell.HasValue || targetReservationStartedTick < 0 || !IsLiveOwnedMcv(activeMcv))
				return false;

			objective = targetResourceCenter.Value;
			deployCell = targetDeployCell.Value;
			mcvActorId = activeMcv.ActorID;
			reservationTick = targetReservationStartedTick;
			return true;
		}

		bool IFransExpansionStateService.TryGetMcvDeployRightOfWay(out CPos center, out int radius)
		{
			center = default;
			radius = 0;
			if (!targetDeployCell.HasValue || !IsLiveOwnedMcv(activeMcv) ||
				(stage != ExpansionStage.MovingToOre && stage != ExpansionStage.ClearingLandDeployArea))
				return false;

			var activationSq = Info.McvDeployRightOfWayActivationRadius * Info.McvDeployRightOfWayActivationRadius;
			if ((activeMcv.Location - targetDeployCell.Value).LengthSquared > activationSq)
				return false;

			center = targetDeployCell.Value;
			radius = Info.McvDeployRightOfWayRadius;
			return true;
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransMcvExpansionManager.BotTick");
			FransBotLog.PerfWorldHeartbeat(world);
			if ((world.WorldTick % 25) == (int)(player.PlayerActor.ActorID % 25u))
				FransBotLog.SetPerfContext(world, $"MCV:{player.PlayerActor.ActorID}",
					$"{player}:task={expansionTask.Id}/{expansionTask.Mode},stage={stage},mcv={(activeMcv == null ? 0u : activeMcv.ActorID)},lst={(activeLandingCraft == null ? 0u : activeLandingCraft.ActorID)},target={(targetResourceCenter.HasValue ? targetResourceCenter.Value.ToString() : "-")}");
			if (world.Type == WorldType.Editor || player.WinState != WinState.Undefined)
				return;

			FlushPendingSynchronizedActions(bot);
			if (baseBuilderLockToken != Actor.InvalidConditionToken)
				openingBuildOrderService.DrainExistingProductionForExpansionLock(bot);

			RememberActiveMcvPosition();
			UpdatePhysicalConstructionYardHighWaterMark();
			RefreshPioneerSuccessorPrequeue(bot);

			if (resourceMapModule == null)
			{
				resourceMapModule = playerActor.TraitsImplementing<ResourceMapBotModule>()
					.FirstOrDefault(t => t.IsTraitEnabled());

				if (resourceMapModule == null)
					return;
			}

			SeedExploredMapResourceObjectives();

			UpdateSurplusConstructionYardGrowth();
			EvaluateTopologyProvenEarlyNavalRequirement();
			if (!openingBuildOrderService.OpeningLocked && earlyNavalTopologyRequired && !navalCapabilityDemandLatched && !HasOwnedLandingCraftProducer() &&
				world.ActorsHavingTrait<Building>().Any(a => a.IsInWorld && !a.IsDead && a.Owner == player && Info.McvFactoryTypes.Contains(a.Info.Name)) &&
				world.ActorsHavingTrait<Building>().Any(a => a.IsInWorld && !a.IsDead && a.Owner == player && Info.EarlyNavalOpeningCompletionTypes.Contains(a.Info.Name)))
				LatchNavalCapabilityDemand($"Explore Map topology proves ore {earlyNavalTopologyObjective} is sea-required from ground landmass {earlyNavalTopologySourceLandmass} to {earlyNavalTopologyTargetLandmass}; establish one Ship queue before secondary WEAP growth");
			MaintainLatchedNavalCapability(bot);

			if (--buildMcvTicks <= 0)
			{
				buildMcvTicks = Info.BuildMcvInterval;
				RequestExpansionMcv(bot);
			}

			if (--scanTicks > 0)
				return;

			scanTicks = Info.ScanInterval;
			CleanupFailedFields();
			RefreshPioneerScoutClearance();

			if (!EnsureMainBase(bot))
				return;

			RefreshFirstExpansionRefineryMilestone(bot);

			// The shared Building queue may stay yielded only while a real naval-support owner
			// still exists. This is stronger than the old stage==Idle heuristic: current-base
			// SPEN/SYRD production can legitimately run while ExpansionTask is Idle, whereas an
			// abandoned support path must never strand the first PROC reservation indefinitely.
			if (firstExpansionRefinerySuspendedForInfrastructure && !ShouldKeepFirstExpansionRefineryInfrastructureSuspended())
				ResumeFirstExpansionRefineryAfterInfrastructure("no live coastal/SeaOre task or queued naval producer still owns the shared Building queue");

			// RETREAT has exclusive MCV movement ownership. Ground Commander only exposes
			// rendezvous points; this module remains the sole actor/order owner of the MCV.
			if (stage == ExpansionStage.Retreat)
			{
				ManageMcvRetreat(bot);
				return;
			}


			// Keep the one-shot first-expansion refinery prebuild alive during amphibious transit too.
			// The only exception is the explicit naval-support suspension while naval access is being created.
			if (activeConyard == null)
				ManageFirstExpansionRefineryPrebuild(bot);

			switch (stage)
			{
				case ExpansionStage.WaitingForSeaTransport:
				case ExpansionStage.MovingToSeaPickup:
				case ExpansionStage.SeaLoading:
				case ExpansionStage.SeaTransporting:
				case ExpansionStage.SeaUnloading:
				case ExpansionStage.SeaCargoPreserved:
					ManageSeaExpansion(bot);
					return;

				case ExpansionStage.WaitingForConyard:
					FindExpansionConyard(bot);
					if (stage == ExpansionStage.WaitingForConyard)
						return;
					break;

				case ExpansionStage.WaitingForMcv:
					FindMcvAfterUndeploy(bot);
					// Ordinary repacks return to Idle and may continue expansion immediately.
					// RETREAT after a critical FACT repack is exclusive ownership: never fall through
					// into normal ore-field planning on the same world tick.
					if (stage != ExpansionStage.Idle)
						return;
					break;
			}

			// NAVAL SUPPORT conyard-loss self-heal. WaitingForMcv is handled by the transform
			// watchdog above, so reaching this point with a missing/foreign staging FACT
			// means the temporary base was genuinely lost. Release only staging ownership
			// and reopen the first PROC; never leave the Building queue permanently yielded.
			if (coastalStagingForSeaExpansion && activeConyard != null &&
				(!activeConyard.IsInWorld || activeConyard.IsDead || activeConyard.Owner != player))
			{
				FransBotLog.BotDebug(world,
					"{0}: NAVAL SUPPORT coastal staging FACT was lost before naval access completed; releasing staging ownership and resuming the first-expansion PROC reservation.",
					player);
				ResumeFirstExpansionRefineryAfterInfrastructure("the temporary coastal staging FACT was lost");
				CancelOwnedRoutineExpansionStructureIfQueued(bot, "coastal staging FACT loss");
				activeConyard = null;
				coastalStagingNavalNoProgressSinceTick = -1;
				ReturnExpansionTaskToIdle("temporary coastal staging FACT was lost");
			}

			// A routine expansion FACT may be destroyed between scans. Before PROC completion this
			// is an expansion failure; after completion/Holding it is only loss of the retained
			// Construction Yard bonus because the ore node is already physically serviced.
			if (!coastalStagingForSeaExpansion && activeConyard != null &&
				(!activeConyard.IsInWorld || activeConyard.IsDead || activeConyard.Owner != player))
			{
				var lostField = targetResourceCenter;
				var completedHoldLost = stage == ExpansionStage.HoldingCompletedOutpost;
				if (!completedHoldLost && lostField.HasValue)
					MarkExpansionAreaFailed(lostField.Value, "routine expansion FACT destroyed before outpost completion");
				CancelOwnedRoutineExpansionStructureIfQueued(bot, "routine expansion FACT loss");
				AbortFirstExpansionRefineryAttempt(bot, "routine expansion FACT loss", lostField);
				FransBotLog.BotDebug(world,
					completedHoldLost
						? "{0}: held completed expansion FACT was destroyed near serviced ore {1}; the PROC remains economy ownership, no false failed-ore memory is created, and normal planning reopens."
						: "{0}: routine expansion FACT was lost before the outpost completed near {1}; exact Building-queue ownership is released and the area enters normal retry protection.",
					player, lostField.HasValue ? lostField.Value.ToString() : "unknown target");
				activeConyard = null;
				ReturnExpansionTaskToIdle(completedHoldLost
					? "held completed expansion FACT was lost after its ore node was already serviced"
					: "routine expansion FACT was lost before outpost completion");
			}


			if (activeConyard != null && activeConyard.IsInWorld && !activeConyard.IsDead)
			{
				ManageExpansionConyard(bot);
				return;
			}

			// CLAIM -> SETTLE is terminal while the settled permanent capacity survives.
			// A later physical-capacity loss may reopen replacement demand in RequestExpansionMcv.
			if (pioneerClaimingComplete)
			{
				LogMcvWaitingState(null, "PioneerClaimPhaseSettled");
				return;
			}

			// Once fair intel proves Dominance, finish any already-active outpost but do not start another
			// economic expansion while the match should be closed. Existing roaming MCV capacity is kept
			// intact and resumes normal expansion if Dominance later ends.

			if (activeMcv == null || !activeMcv.IsInWorld || activeMcv.IsDead)
			{
				if (activeMcv != null)
					HandleUnexpectedActiveMcvLoss(bot, "normal land expansion");

				activeMcv = FindAvailableExpansionMcv();
				RememberActiveMcvPosition();
			}

			if (activeMcv == null)
			{
				stage = ExpansionStage.Idle;
				LogMcvWaitingState(null, "NoAvailableExpansionMcv");
				return;
			}

			ManageExpansionMcv(bot);
		}


		bool EnsureMainBase(IBot bot)
		{
			if (mainConyard != null && mainConyard.IsInWorld && !mainConyard.IsDead)
			{
				mainBaseEverEstablished = true;
				if (stage == ExpansionStage.EmergencyMainBaseRecovery)
					FinishEmergencyMainBaseRecovery(mainConyard);
				return true;
			}

			var conyards = constructionYards.Actors
				.Where(a => a.IsInWorld && !a.IsDead && a != activeConyard)
				.OrderBy(a => a.ActorID)
				.ToArray();

			if (conyards.Length > 0)
			{
				mainConyard = conyards[0];
				mainBaseEverEstablished = true;
				initialBootstrapDeployIssued = false;
				if (stage == ExpansionStage.EmergencyMainBaseRecovery)
					FinishEmergencyMainBaseRecovery(mainConyard);
				return true;
			}

			// If the original main base was destroyed while a temporary expansion conyard
			// survives, preserve that conyard as the new main base instead of packing it up.
			if (activeConyard != null && activeConyard.IsInWorld && !activeConyard.IsDead)
			{
				mainConyard = activeConyard;
				mainBaseEverEstablished = true;
				ResumeFirstExpansionRefineryAfterInfrastructure("the temporary expansion FACT became the surviving main base, so naval-support staging ownership ended");
				coastalStagingForSeaExpansion = false;
				coastalStagingReturnToSea = false;
				activeConyard = null;
				activeMcv = null;
				ReturnExpansionTaskToIdle("temporary expansion FACT became the surviving main base");
				FinishEmergencyMainBaseRecovery(mainConyard);
				return true;
			}

			// Initial bootstrap is intentionally a one-time exception. Before the first FACT has
			// ever existed the starting MCV may deploy in place. Once a FACT has existed, this
			// branch can never run again: all later recovery is StrategicMap + RiskModel driven.
			if (!mainBaseEverEstablished)
				return ManageInitialMainBaseBootstrap(bot);

			return ManageEmergencyMainBaseRecovery(bot);
		}

		bool ManageInitialMainBaseBootstrap(IBot bot)
		{
			var initialMcv = mcvs.Actors
				.Where(a => a.IsInWorld && !a.IsDead && a.IsIdle)
				.OrderBy(a => a.ActorID)
				.FirstOrDefault();

			if (initialMcv == null)
				return false;

			LogMcvIdentity(initialMcv);
			var transformsInfo = initialMcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null)
			{
				LogMcvWaitingState(initialMcv, "InitialBootstrapMissingTransformsTrait");
				return false;
			}

			var actorInfo = world.Map.Rules.Actors[transformsInfo.IntoActor];
			var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null ||
				!world.CanPlaceBuilding(initialMcv.Location + transformsInfo.Offset, actorInfo, buildingInfo, initialMcv))
			{
				LogMcvDeployment(initialMcv, false, "InitialBootstrapFootprintBlocked");
				return false;
			}

			if (!initialBootstrapDeployIssued)
			{
				initialBootstrapDeployIssued = true;
				FransBotLog.BotDebug(world, "{0}: one-time InitialBootstrap deploys starting MCV {1} in place as the permanent main base.", player, initialMcv);
				LogMcvDeployment(initialMcv, true, "InitialBootstrapDeploy");
				bot.QueueOrder(new Order("DeployTransform", initialMcv, true));
			}
			return false;
		}

		bool ManageEmergencyMainBaseRecovery(IBot bot)
		{
			if (stage != ExpansionStage.EmergencyMainBaseRecovery || emergencyRecoveryMcv == null ||
				!emergencyRecoveryMcv.IsInWorld || emergencyRecoveryMcv.IsDead)
			{
				if (!BeginEmergencyMainBaseRecovery(bot))
					return false;
			}

			var mcv = emergencyRecoveryMcv;
			LogMcvIdentity(mcv);
			var mobile = mcv.TraitOrDefault<Mobile>();
			var transformsInfo = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (mobile == null || transformsInfo == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
			{
				TrackEmergencyRecoveryMoveState(mcv, mobile, emergencyRecoveryDeployCell,
					"NoOperationalMobileOrTransform");
				LogMcvWaitingState(mcv, "EmergencyRecoveryNoOperationalMobileOrTransform");
				return false;
			}

			var intoActor = world.Map.Rules.Actors[transformsInfo.IntoActor];
			var buildingInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
			{
				TrackEmergencyRecoveryMoveState(mcv, mobile, emergencyRecoveryDeployCell,
					"MissingRecoveryBuildingInfo");
				return false;
			}

			if (!emergencyRecoveryDeployCell.HasValue ||
				world.WorldTick >= emergencyRecoveryNextCheckTick && !IsEmergencyRecoveryCellStillValid(mcv, mobile, transformsInfo, intoActor, buildingInfo, emergencyRecoveryDeployCell.Value))
			{
				var searchTrigger = emergencyRecoveryDeployCell.HasValue ? "AssignedCellInvalid" : "NoAssignedDeployCell";
				if (!TryFindEmergencyMainBaseRecoveryCell(mcv, mobile, transformsInfo, intoActor, buildingInfo,
					searchTrigger, out var recoveryCell, out var routeRisk))
				{
					emergencyRecoveryDeployCell = null;
					emergencyRecoveryNextCheckTick = world.WorldTick + Info.EmergencyMainBaseRecoveryRecheckInterval;
					emergencyRecoveryMoveLastProgressCell = null;
					emergencyRecoveryMoveLastProgressTick = -1;
					LogMcvWaitingState(mcv, "EmergencyRecoveryNoValidDeployCell");
					return false;
				}

				emergencyRecoveryDeployCell = recoveryCell;
				emergencyRecoveryNextCheckTick = world.WorldTick + Info.EmergencyMainBaseRecoveryRecheckInterval;
				emergencyRecoveryDeployIssuedTick = -1;
				ResetEmergencyRecoveryMoveDiagnostics(mobile);
				FransBotLog.BotDebug(world,
					"{0}: EmergencyMainBaseRecovery assigns MCV {1} to safe own-control cell {2}; unified route peak {3}/{4}. Expansion ownership is suspended until a replacement FACT exists.",
					player, mcv, recoveryCell, routeRisk.PeakScore, routeRisk.CriticalThreshold);
				QueueEmergencyRecoveryMove(mcv, mobile, recoveryCell);
			}

			var target = emergencyRecoveryDeployCell.Value;
			if (mobile.ToCell != target)
			{
				TrackEmergencyRecoveryMoveState(mcv, mobile, target, "TravelingOffTarget");
				if (mcv.IsIdle && world.WorldTick >= emergencyRecoveryNextCheckTick)
				{
					emergencyRecoveryNextCheckTick = world.WorldTick + Info.EmergencyMainBaseRecoveryRecheckInterval;
					QueueEmergencyRecoveryMove(mcv, mobile, target);
				}
				else if (mcv.IsIdle)
					LogMcvWaitingState(mcv, $"EmergencyRecoveryMoveRetryCooldownUntilWT{emergencyRecoveryNextCheckTick}");
				return false;
			}

			var risk = riskModelService.EvaluateCell(mcv, target, FransRiskRole.Mcv, FransRiskTolerance.Cautious);
			if (risk.IsCritical || !world.CanPlaceBuilding(target + transformsInfo.Offset, intoActor, buildingInfo, mcv))
			{
				LogMcvDeployment(mcv, false, risk.IsCritical ? "EmergencyRecoveryCriticalRisk" : "EmergencyRecoveryFootprintBlocked");
				emergencyRecoveryDeployCell = null;
				emergencyRecoveryNextCheckTick = world.WorldTick;
				emergencyRecoveryMoveLastProgressCell = null;
				emergencyRecoveryMoveLastProgressTick = -1;
				return false;
			}

			if (emergencyRecoveryDeployIssuedTick < 0)
			{
				emergencyRecoveryDeployIssuedTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: EmergencyMainBaseRecovery deploys MCV {1} at {2}; risk {3}/{4}. This is a recovery decision, not the one-time initial bootstrap.",
					player, mcv, target, risk.Score, risk.CriticalThreshold);
				LogMcvDeployment(mcv, true, "EmergencyRecoveryDeploy");
				bot.QueueOrder(new Order("DeployTransform", mcv, true));
				return false;
			}

			if (world.WorldTick - emergencyRecoveryDeployIssuedTick >= Info.EmergencyMainBaseRecoveryDeployTimeout)
			{
				FransBotLog.BotDebug(world,
					"{0}: EmergencyMainBaseRecovery deploy watchdog expired at {1}; selecting another safe own-control cell instead of issuing repeated in-place deploy orders.",
					player, target);
				emergencyRecoveryDeployCell = null;
				emergencyRecoveryDeployIssuedTick = -1;
				emergencyRecoveryNextCheckTick = world.WorldTick;
				emergencyRecoveryMoveLastProgressCell = null;
				emergencyRecoveryMoveLastProgressTick = -1;
			}
			return false;
		}

		bool BeginEmergencyMainBaseRecovery(IBot bot)
		{
			var candidate = mcvs.Actors
				.Where(a => a.IsInWorld && !a.IsDead)
				.OrderBy(a => a == activeMcv ? 1 : 0)
				.ThenBy(a => a.IsIdle ? 0 : 1)
				.ThenBy(a => a.ActorID)
				.FirstOrDefault();

			if (candidate == null)
				return false;

			// Explicit ownership transfer: emergency main-base recovery preempts the *whole*
			// expansion task, not merely whichever MCV happened to be selected for recovery.
			// This prevents a second idle MCV from becoming recovery owner while stale PROC/LST
			// ownership from the old ore task survives in parallel.
			if (expansionTask.Id > 0 && expansionTask.Mode != ExpansionTaskMode.EmergencyRecovery)
			{
				QueueStopOrder(bot, activeMcv);
				AbortExpansionTaskToIdle(bot, "emergency main-base recovery preempted the active expansion");
				activeMcv = null;
			}

			QueueStopOrder(bot, candidate);
			emergencyRecoveryMcv = candidate;
			emergencyRecoveryDeployCell = null;
			emergencyRecoveryDeployIssuedTick = -1;
			emergencyRecoveryNextCheckTick = world.WorldTick;
			emergencyRecoveryMoveLastProgressCell = null;
			emergencyRecoveryMoveLastProgressTick = -1;
			nextMcvRecoveryMovePerfLogTick = world.WorldTick;
			if (!BeginExpansionTask(ExpansionTaskMode.EmergencyRecovery, null, null,
				ExpansionStage.EmergencyMainBaseRecovery, world.WorldTick,
				"all permanent construction yards are gone; recovery temporarily owns one MCV"))
				return false;
			FransBotLog.BotDebug(world,
				"{0}: all Construction Yards are gone; EmergencyMainBaseRecovery takes explicit ownership of MCV {1}. No deploy-in-place fallback is permitted after the first base has existed.",
				player, candidate);
			return true;
		}

		bool TryFindEmergencyMainBaseRecoveryCell(Actor mcv, Mobile mobile, TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, string trigger,
			out CPos deployCell, out FransRouteRiskAssessment routeRisk)
		{
			var started = Stopwatch.GetTimestamp();
			var perf = new McvRecoveryPerf
			{
				Trigger = trigger,
				RecheckGateBypassed = !emergencyRecoveryDeployCell.HasValue && world.WorldTick < emergencyRecoveryNextCheckTick,
				RecheckDueIn = Math.Max(0, emergencyRecoveryNextCheckTick - world.WorldTick)
			};
			deployCell = default;
			routeRisk = default;
			if (mobile.PathFinder is not PathFinder pathFinder)
			{
				LogMcvRecoveryPerf(mcv, mobile, perf, "MissingPathfinder", null, started);
				return false;
			}

			var sectorById = strategicMapService.Sectors.ToDictionary(s => s.Id);
			var centers = strategicMapService.SectorMetrics
				.Where(m => m.OwnControlScore > 0 && m.OwnControlScore >= m.EnemyControlScore && !m.IsFrontlineSector)
				.OrderBy(m => m.ThreatScore)
				.ThenBy(m => m.EnemyControlScore)
				.ThenByDescending(m => m.OwnControlScore)
				.Take(Info.EmergencyMainBaseRecoverySectorCandidates)
				.Select(m => sectorById.TryGetValue(m.SectorId, out var sector) ? sector.McvCenter ?? sector.GroundCenter ?? (CPos?)sector.Center : null)
				.Where(c => c.HasValue)
				.Select(c => c.Value)
				.ToList();

			// If sector control is temporarily unavailable, own surviving structures are still fair
			// anchors. They do not reveal hidden enemy information and keep recovery possible.
			perf.AnchorSource = centers.Count == 0 ? "OwnedBuildings" : "StrategicSectors";
			if (centers.Count == 0)
			{
				combatIntelService.EnsureCurrentSnapshot();
				centers.AddRange(combatIntelService.OwnedActors
					.Where(a => a.Info.HasTraitInfo<BuildingInfo>())
					.OrderBy(a => a.ActorID)
					.Select(a => a.Location)
					.Take(Info.EmergencyMainBaseRecoverySectorCandidates));
			}
			perf.AnchorCenters = centers.Count;
			var distinctCenters = centers.Distinct().ToArray();
			perf.DistinctAnchorCenters = distinctCenters.Length;

			var candidates = new List<(CPos Cell, int Risk, int Distance)>();
			foreach (var center in distinctCenters)
			{
				var local = new[] { center }.Concat(world.Map.FindTilesInAnnulus(center, 1, Info.EmergencyMainBaseRecoverySearchRadius));
				foreach (var cell in local)
				{
					perf.DeployCellsEnumerated++;
					if (!world.Map.Contains(cell))
					{
						perf.DeployCellsOutsideMap++;
						continue;
					}
					if (!mobile.CanEnterCell(cell, check: BlockedByActor.Immovable))
					{
						perf.DeployCellsMobilityRejected++;
						continue;
					}
					if (!mobile.CanStayInCell(cell))
					{
						perf.DeployCellsMobilityRejected++;
						continue;
					}

					perf.BuildingPlacementChecks++;
					if (!world.CanPlaceBuilding(cell + transformsInfo.Offset, intoActor, buildingInfo, mcv))
					{
						perf.DeployCellsPlacementRejected++;
						continue;
					}

					perf.DeployCellRiskChecks++;
					var risk = riskModelService.EvaluateCell(mcv, cell, FransRiskRole.Mcv, FransRiskTolerance.Cautious);
					if (risk.IsCritical)
					{
						perf.DeployCellsRiskRejected++;
						continue;
					}
					candidates.Add((cell, risk.Score, (cell - mobile.ToCell).LengthSquared));
				}
			}

			perf.DeployCandidatesGenerated = candidates.Count;
			var distinctCandidates = candidates.Distinct().ToArray();
			perf.DuplicateDeployCandidates = candidates.Count - distinctCandidates.Length;
			var rankedCandidates = distinctCandidates.OrderBy(c => c.Risk).ThenBy(c => c.Distance).Take(64).ToArray();
			perf.RankedDeployCandidates = rankedCandidates.Length;
			foreach (var candidate in rankedCandidates)
			{
				long pathCostCallbacks = 0;
				long riskPathCostCalls = 0;
				int CustomCost(CPos cell)
				{
					pathCostCallbacks++;
					if (cell == mobile.ToCell)
						return 0;

					riskPathCostCalls++;
					return riskModelService.GetPathCost(mcv, cell, FransRiskRole.Mcv, FransRiskTolerance.Cautious);
				}

				perf.LogicalNativeProofRequests++;
				var pathSearchStarted = Stopwatch.GetTimestamp();
				var path = pathFinder.FindPathToTargetCell(mcv, [mobile.ToCell], candidate.Cell, BlockedByActor.Immovable, CustomCost, laneBias: false);
				var pathSearchElapsedMs = ElapsedMilliseconds(pathSearchStarted);
				perf.PhysicalNativePathSearches++;
				perf.NativeTargetCells++;
				perf.NativePathCostCallbackCalls += pathCostCallbacks;
				perf.RiskPathCostCalls += riskPathCostCalls;
				perf.NativePathSearchElapsedMs += pathSearchElapsedMs;
				if (pathSearchElapsedMs > perf.MaxNativePathSearchElapsedMs)
				{
					perf.MaxNativePathSearchElapsedMs = pathSearchElapsedMs;
					perf.MaxNativePathSearchCallbackCalls = pathCostCallbacks;
				}
				if (path == null || path.Count == 0)
				{
					perf.NativePathFailures++;
					continue;
				}

				perf.RouteRiskChecks++;
				var assessed = riskModelService.EvaluateRoute(mcv, path, FransRiskRole.Mcv, FransRiskTolerance.Cautious);
				if (assessed.IsCritical)
				{
					perf.RouteRiskRejects++;
					continue;
				}
				deployCell = candidate.Cell;
				routeRisk = assessed;
				LogMcvRecoveryPerf(mcv, mobile, perf, "Success", deployCell, started);
				return true;
			}

			LogMcvRecoveryPerf(mcv, mobile, perf, "NoValidDeployCell", null, started);
			return false;
		}

		bool IsEmergencyRecoveryCellStillValid(Actor mcv, Mobile mobile, TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, CPos cell)
		{
			if (!world.Map.Contains(cell) || !mobile.CanEnterCell(cell, check: BlockedByActor.Immovable) || !mobile.CanStayInCell(cell) ||
				!world.CanPlaceBuilding(cell + transformsInfo.Offset, intoActor, buildingInfo, mcv))
				return false;
			if (riskModelService.EvaluateCell(mcv, cell, FransRiskRole.Mcv, FransRiskTolerance.Cautious).IsCritical)
				return false;
			return TryFindRiskAwarePathToCell(mcv, mobile, cell, out var path) &&
				!riskModelService.EvaluateRoute(mcv, path, FransRiskRole.Mcv, FransRiskTolerance.Cautious).IsCritical;
		}

		void QueueEmergencyRecoveryMove(Actor mcv, Mobile mobile, CPos destination)
		{
			if (mobile.PathFinder is not PathFinder pathFinder || !world.Map.Contains(destination))
			{
				LogMcvWaitingState(mcv, "EmergencyRecoveryMoveOrderMissingPathfinderOrDestination");
				return;
			}

			int CustomCost(CPos cell) => cell == mobile.ToCell ? 0 : riskModelService.GetPathCost(mcv, cell, FransRiskRole.Mcv, FransRiskTolerance.Cautious);
			var initialPath = pathFinder.FindPathToTargetCell(mcv, [mobile.ToCell], destination,
				BlockedByActor.Immovable, CustomCost, laneBias: false);
			if (initialPath == null || initialPath.Count == 0)
			{
				LogMcvWaitingState(mcv, "EmergencyRecoveryMoveOrderNoPath");
				return;
			}

			// PathFinder returns target-to-source. Preserve the validated recovery corridor with a
			// bounded packet of native Move orders instead of installing a synchronized activity.
			var orderedPath = initialPath
				.AsEnumerable()
				.Reverse()
				.Where(cell => cell != mobile.ToCell)
				.ToArray();
			if (orderedPath.Length == 0)
			{
				LogMcvMoveOrder(mcv, destination, 1, "EmergencyRecovery");
				QueueMoveOrder(null, mcv, destination);
				return;
			}

			const int MaximumMoveWaypoints = 4;
			var waypointCount = Math.Min(MaximumMoveWaypoints, orderedPath.Length);
			LogMcvMoveOrder(mcv, destination, waypointCount, "EmergencyRecovery");
			var queued = false;
			for (var i = 1; i <= waypointCount; i++)
			{
				var index = (int)((long)i * orderedPath.Length / waypointCount) - 1;
				QueueMoveOrder(null, mcv, orderedPath[index], queued);
				queued = true;
			}
		}

		void FinishEmergencyMainBaseRecovery(Actor recoveredConyard)
		{
			if (stage != ExpansionStage.EmergencyMainBaseRecovery)
				return;
			FransBotLog.BotDebug(world,
				"{0}: EmergencyMainBaseRecovery complete: FACT {1} is established at {2}; normal expansion planning may resume with fresh ownership.",
				player, recoveredConyard, recoveredConyard.Location);
			emergencyRecoveryMcv = null;
			emergencyRecoveryDeployCell = null;
			emergencyRecoveryDeployIssuedTick = -1;
			emergencyRecoveryNextCheckTick = 0;
			emergencyRecoveryMoveLastProgressCell = null;
			emergencyRecoveryMoveLastProgressTick = -1;
			nextMcvRecoveryMovePerfLogTick = 0;
			ReturnExpansionTaskToIdle("emergency main-base FACT is physical");
		}

		Actor FindAvailableExpansionMcv()
		{
			return mcvs.Actors
				.Where(a => a.IsInWorld && !a.IsDead)
				.OrderBy(a => a.ActorID)
				.FirstOrDefault();
		}

		void UpdateSurplusConstructionYardGrowth()
		{
			if (surplusUnlockedPermanentConstructionYards <= 0)
				surplusUnlockedPermanentConstructionYards = Info.PreSurplusPermanentConstructionYards;

			// there is no special Radar/post-opening MCV #3 milestone. The normal early
			// posture is one permanent main FACT plus one roaming expansion slot. NEW permanent
			// capacity grows only under true Surplus and the shared Ground-force maturity gate.
			if (!economicStateService.IsSurplus || surplusUnlockedPermanentConstructionYards >= Info.MaximumPermanentConstructionYards)
				return;

			var groundCombatValue = CurrentGroundCombatValue();
			if (Info.MinimumGroundCombatValueForAdditionalMcv > 0 &&
				groundCombatValue < Info.MinimumGroundCombatValueForAdditionalMcv)
			{
				LogMcvPressureGate(
					$"true Surplus permanent FACT growth waits for Ground army {groundCombatValue}/{Info.MinimumGroundCombatValueForAdditionalMcv} combat value");
				return;
			}

			// One permanent target at a time. The next target unlocks only after the currently
			// unlocked FACT count physically exists. A temporary NAVAL SUPPORT coastal FACT is the
			// roaming slot deployed for access, not proof of a new permanent economic FACT.
			var liveConyards = LivePermanentEligibleConstructionYardCount();
			if (liveConyards < surplusUnlockedPermanentConstructionYards)
				return;

			surplusUnlockedPermanentConstructionYards = Math.Min(
				Info.MaximumPermanentConstructionYards,
				surplusUnlockedPermanentConstructionYards + 1);
			FransBotLog.BotDebug(world,
				"{0}: MCV pressure gate unlocks permanent Construction Yard target {1}/{2}: true Surplus and Ground combat value {3} satisfy expansion pressure; the next target still waits for this FACT count to be physically achieved.",
				player, surplusUnlockedPermanentConstructionYards, Info.MaximumPermanentConstructionYards, groundCombatValue);
		}


		int PhysicalConstructionYardSlotCount() => LiveConstructionYardCount() + LiveMcvCount();

		void UpdatePhysicalConstructionYardHighWaterMark()
		{
			// High-water records only economically UNLOCKED physical capacity. may temporarily
			// carry one extra roaming MCV above the current slot ceiling after a protected SECURE FACT
			// handoff. That role-replacement exemption must never ratchet replacement capacity upward or
			// recreate the old early-MCV-3 bug. When Surplus later raises the real ceiling, the same
			// physical actor count becomes ordinary achieved capacity and high-water advances naturally.
			var achieved = Math.Min(CurrentConstructionYardSlotCeiling(), PhysicalConstructionYardSlotCount());
			if (achieved <= highestPhysicalConstructionYardCapacity)
				return;

			highestPhysicalConstructionYardCapacity = achieved;
			FransBotLog.BotDebug(world,
				"{0}: Construction Yard physical-capacity high-water is now {1}. Later losses below this achieved FACT+MCV capacity are replacement demand and bypass economic growth gates.",
				player, highestPhysicalConstructionYardCapacity);
		}

		int LivePermanentEligibleConstructionYardCount()
		{
			var count = LiveConstructionYardCount();
			if (coastalStagingForSeaExpansion && activeConyard != null && activeConyard.IsInWorld &&
				!activeConyard.IsDead && activeConyard.Owner == player)
				count--;

			return Math.Max(0, count);
		}

		int CurrentGroundCombatValue()
		{
			if (combatIntelService == null || groundCommanderService == null)
				return 0;

			return combatIntelService.OwnedActors
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && groundCommanderService.IsGroundCombatUnitOwned(a))
				.Sum(a => Math.Max(1, a.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1));
		}

		void LogMcvPressureGate(string reason)
		{
			if (world.WorldTick < nextMcvPressureGateLogTick)
				return;

			nextMcvPressureGateLogTick = world.WorldTick + 500;
			FransBotLog.BotDebug(world, "{0}: MCV pressure gate holds expansion capacity: {1}.", player, reason);
		}

		int CurrentDesiredPermanentConstructionYards()
		{
			// True Surplus + Ground-force maturity unlocks this value one physical FACT at a time.
			// Prosperous/SurplusPressure alone no longer creates an early extra MCV slot.
			var unlocked = Math.Max(Info.PreSurplusPermanentConstructionYards, surplusUnlockedPermanentConstructionYards);
			return Math.Min(Info.MaximumPermanentConstructionYards, unlocked);
		}

		int CurrentPermanentFactFloor()
		{
			// A SECURE FACT is protected from reserve repacking, but it is NOT an economic-growth
			// milestone and must never unlock MCV #3 by itself. Before true Surplus + Ground-force
			// maturity, the economic slot budget therefore remains main FACT + one roaming slot.
			// handles loss of the roaming ROLE separately: one protected handoff may receive
			// a temporary replacement MCV above this ceiling, without changing this permanent target.
			return CurrentDesiredPermanentConstructionYards();
		}

		int CurrentConstructionYardSlotCeiling()
		{
			var permanentTarget = CurrentPermanentFactFloor();

			// Normal early posture: one permanent main FACT + one roaming FACT/MCV slot.
			// There is deliberately no Radar-based third slot. As true Surplus unlocks additional
			// permanent FACT targets, keep at most one extra roaming slot while below the hard cap.
			if (permanentTarget <= Info.PreSurplusPermanentConstructionYards)
				return Info.PreSurplusMaximumConstructionYardSlots;

			return Math.Min(
				Info.MaximumConstructionYardSlots,
				Math.Max(Info.PreSurplusMaximumConstructionYardSlots, permanentTarget + 1));
		}

		bool HasProtectedSecureAnchorConyard()
		{
			return generalService != null && constructionYards.Actors.Any(a => a.IsInWorld && !a.IsDead && a.Owner == player &&
				a != mainConyard && generalService.IsSecureAnchor(a.Location));
		}

		bool HasRoamingMcvRoleReplacementDemand()
		{
			RefreshPendingMcvSlotReservation();
			if (stage != ExpansionStage.Idle || activeMcv != null || activeConyard != null ||
				LiveMcvCount() != 0 || QueuedMcvCount() != 0 || pendingMcvSlotReservation)
				return false;

			// Exactly one protected handoff may consume the roaming role above the current economic
			// ceiling. Requiring equality prevents repeated SECURE handoffs from stacking unlimited
			// out-of-budget FACTs: once the exception exists, physical slots are already ceiling+1 and
			// no second role replacement is possible until genuine growth raises the ceiling.
			return CountConstructionYardSlots() == CurrentConstructionYardSlotCeiling() && HasProtectedSecureAnchorConyard();
		}

		void RefreshPioneerSuccessorPrequeue(IBot bot)
		{
			if (!pioneerSuccessorPrequeueActive)
				return;

			RefreshPendingMcvSlotReservation();
			if (LiveMcvCount() > pioneerSuccessorPrequeueBaselineLiveMcvCount)
			{
				FransBotLog.BotDebug(world,
					"{0}: PIONEER SUCCESSOR prequeue is fulfilled by a new physical MCV. The handoff gap is closed without changing the unlocked FACT+MCV slot ceiling.",
					player);
				pioneerSuccessorPrequeueActive = false;
				pioneerSuccessorPrequeueRequestedTick = -1;
				return;
			}

			if (world.WorldTick - pioneerSuccessorPrequeueRequestedTick < 1000)
				return;

			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			var stillRequested = unitBuilder != null &&
				Info.McvTypes.Any(t => unitBuilder.RequestedProductionCount(bot, t) > 0);
			if (!stillRequested && QueuedMcvCount() == 0 && !pendingMcvSlotReservation)
			{
				FransBotLog.BotDebug(world,
					"{0}: PIONEER SUCCESSOR prequeue reservation expired without a live/requested/queued MCV; the gate reopens for a later outpost.",
					player);
				pioneerSuccessorPrequeueActive = false;
				pioneerSuccessorPrequeueRequestedTick = -1;
			}
		}

		bool TryPrequeuePioneerSuccessorMcv(IBot bot, string reason)
		{
			if (pioneerSuccessorPrequeueActive || activeConyard == null || !activeConyard.IsInWorld ||
				activeConyard.IsDead || activeConyard.Owner != player || !targetResourceCenter.HasValue ||
				playerResources == null || Info.McvTypes.Count == 0)
				return false;
			if (!FindNextExpansionObjectiveHint(activeConyard).HasValue)
				return false;

			var permanentTarget = CurrentPermanentFactFloor();
			var permanentEligibleFacts = LivePermanentEligibleConstructionYardCount();
			var slots = CountConstructionYardSlots();
			var ceiling = CurrentConstructionYardSlotCeiling();
			if (permanentEligibleFacts > permanentTarget || slots >= ceiling || slots >= Info.MaximumConstructionYardSlots)
				return false;

			if (playerResources.GetCashAndResources() < Info.MinimumCashForExpansionMcv ||
				AIUtils.CountActorByCommonName(mcvFactories) <= 0)
				return false;

			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return false;

			var mcvType = PickBuildableMcvType();
			if (mcvType == null)
				return false;
			RefreshPendingMcvSlotReservation();
			if (McvAlreadyQueued() || unitBuilder.RequestedProductionCount(bot, mcvType) > 0 ||
				mcvs.Actors.Any(a => a.IsInWorld && !a.IsDead && a.Owner == player && a != activeMcv))
				return false;

			var beforeRequested = unitBuilder.RequestedProductionCount(bot, mcvType);
			var beforeLiveMcvs = LiveMcvCount();
			unitBuilder.RequestUnitProduction(bot, mcvType);
			var accepted = unitBuilder.RequestedProductionCount(bot, mcvType) > beforeRequested ||
				McvAlreadyQueued() || LiveMcvCount() > beforeLiveMcvs;
			if (!accepted)
				return false;

			pendingMcvSlotReservation = !McvAlreadyQueued() && LiveMcvCount() == beforeLiveMcvs;
			pendingMcvSlotReservationLiveCount = beforeLiveMcvs;
			pioneerSuccessorPrequeueActive = true;
			pioneerSuccessorPrequeueBaselineLiveMcvCount = beforeLiveMcvs;
			pioneerSuccessorPrequeueRequestedTick = world.WorldTick;
			FransBotLog.BotDebug(world,
				"{0}: PIONEER SUCCESSOR PREQUEUE accepted while outpost ore {1} still builds its PROC: permanent FACT capacity {2}/{3}, total unlocked slots {4}/{5}. The successor is a real produced MCV inside existing capacity, not an extra growth slot. Trigger: {6}.",
				player, targetResourceCenter.Value, permanentEligibleFacts, permanentTarget, slots, ceiling,
				reason ?? "permanent handoff is already predictable");
			return true;
		}

		bool RequestExpansionMcv(IBot bot)
		{
			// Replacement of physically achieved capacity is allowed even while the opening planner
			// would normally suppress NEW expansion-MCV growth. Losing an established MCV slot must
			// not make the bot wait for the opening phase to advance before restoring it.
			var replacementDemandAtEntry = highestPhysicalConstructionYardCapacity > 0 &&
				CountConstructionYardSlots() < Math.Min(Info.MaximumConstructionYardSlots, highestPhysicalConstructionYardCapacity);
			if (pioneerClaimingComplete && !replacementDemandAtEntry)
				return false;
			if (pioneerClaimingComplete)
			{
				pioneerClaimingComplete = false;
				FransBotLog.BotDebug(world,
					"{0}: PIONEER CLAIM phase reopens only to restore previously achieved physical FACT/MCV capacity after a loss.",
					player);
			}
			var roamingRoleReplacementDemandAtEntry = HasRoamingMcvRoleReplacementDemand();
			if (roamingRoleReplacementDemandAtEntry && commandBidService != null && commandBidService.IsDefendPressureActive())
			{
				LogMcvPressureGate("roaming-role replacement MCV waits while DEFEND pressure is active");
				return false;
			}
			if (!replacementDemandAtEntry && !roamingRoleReplacementDemandAtEntry && openingBuildOrderService != null && !openingBuildOrderService.AllowExpansionMcvProduction)
				return false;

			if (mainConyard == null || !mainConyard.IsInWorld || mainConyard.IsDead || playerResources == null)
				return false;

			var cash = playerResources.GetCashAndResources();
			if (cash < Info.MinimumCashForExpansionMcv || AIUtils.CountActorByCommonName(mcvFactories) <= 0)
				return false;

			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			if (unitBuilder == null || Info.McvTypes.Count == 0)
				return false;

			var mcvType = PickBuildableMcvType();
			if (mcvType == null)
				return false;
			RefreshPendingMcvSlotReservation();
			var alreadyQueued = McvAlreadyQueued();
			var alreadyRequested = unitBuilder.RequestedProductionCount(bot, mcvType) > 0;
			if (alreadyRequested && !alreadyQueued)
			{
				pendingMcvSlotReservation = true;
				pendingMcvSlotReservationLiveCount = LiveMcvCount();
			}

			var liveMcvs = LiveMcvCount();
			var liveConyards = LiveConstructionYardCount();
			var slots = CountConstructionYardSlots();
			var replacementTarget = Math.Min(Info.MaximumConstructionYardSlots, highestPhysicalConstructionYardCapacity);
			var replacementDeficit = replacementTarget > 0 && slots < replacementTarget;

			// Economic slot posture: main FACT + one roaming expansion FACT/MCV is the
			// complete early economy. NEW capacity above that is unlocked only by true Surplus
			// plus Ground-force maturity. Replacement of already achieved physical capacity is separate.
			var currentSlotCeiling = CurrentConstructionYardSlotCeiling();
			var currentPermanentTarget = CurrentPermanentFactFloor();

			// FACT + MCV + queued/requested MCV are one shared capacity budget. The configured hard
			// ceiling is unlocked one permanent target step at a time. If all currently unlocked slots are deployed FACTs,
			// turn the newest non-main FACT back into the reserve MCV instead of producing one.
			if (slots >= Info.MaximumConstructionYardSlots)
			{
				if (liveMcvs == 0 && !alreadyQueued && !alreadyRequested)
					TryRepackNewestReserveConyard(bot, "the hard Construction Yard slot cap is full and the expansion chain needs a mobile reserve");
				return false;
			}

			if (!replacementDeficit && slots >= currentSlotCeiling)
			{
				// First recover an ordinary non-main/non-SECURE FACT into the roaming role. Only when
				// that is impossible because the consumed slot is a protected SECURE anchor may 				// create one role-replacement MCV above the economic ceiling. Equality is essential:
				// ceiling+1 means the one exemption already exists and must not stack.
				if (liveMcvs == 0 && !alreadyQueued && !alreadyRequested)
				{
					if (liveConyards > currentPermanentTarget &&
						TryRepackNewestReserveConyard(bot, "the current economic slot ceiling is full and one ordinary FACT can restore the roaming expansion role"))
						return false;
					if (!roamingRoleReplacementDemandAtEntry || slots != currentSlotCeiling)
						return false;
				}
				else
					return false;
			}

			var expansionBusy = activeMcv != null || activeConyard != null ||
				stage == ExpansionStage.WaitingForConyard || stage == ExpansionStage.WaitingForMcv ||
				stage == ExpansionStage.WaitingForSeaTransport || stage == ExpansionStage.MovingToSeaPickup ||
				stage == ExpansionStage.SeaLoading || stage == ExpansionStage.SeaTransporting ||
				stage == ExpansionStage.SeaUnloading || stage == ExpansionStage.SeaCargoPreserved ||
				stage == ExpansionStage.Retreat;

			// Never produce an additional growth MCV while the current roaming expansion is
			// still being established. Finish the current FACT/outpost first, then reconsider.
			if (!replacementDeficit && slots >= Info.PreSurplusMaximumConstructionYardSlots && expansionBusy)
				return false;

			var spareOwned = mcvs.Actors.Count(a => a.IsInWorld && !a.IsDead && a.Owner == player && a != activeMcv);
			if ((!replacementDeficit && !roamingRoleReplacementDemandAtEntry && spareOwned > 0) || alreadyQueued || alreadyRequested)
				return false;

			// Growth waits for the current economic posture. Replacement does not: once the bot has
			// physically achieved N FACT+MCV slots, losing one is restoration of proven capacity, not
			// a request to unlock slot N again.
			if (!replacementDeficit && !roamingRoleReplacementDemandAtEntry && expansionBusy && liveConyards < currentPermanentTarget)
				return false;

			FransBotLog.BotDebug(world,
				replacementDeficit
					? "{0}: requesting REPLACEMENT MCV to restore achieved physical FACT+MCV capacity {1}; current live/queued/reserved slots {2}, live physical {3}. Prosperous/Surplus/army growth gates are bypassed because this is restoration, not growth."
					: roamingRoleReplacementDemandAtEntry
						? "{0}: requesting ROAMING-ROLE replacement MCV after protected SECURE FACT handoff: economic slots remain {2}/{4}, permanent FACT target {6}, hard max {5}. This one-slot role exemption does NOT raise physical-capacity high-water and therefore cannot unlock early MCV #3."
						: "{0}: requesting one MCV inside current Construction Yard slot budget {2}/{4} (hard max {5}); current permanent FACT target {6}.",
				player, replacementTarget, slots, PhysicalConstructionYardSlotCount(), currentSlotCeiling, Info.MaximumConstructionYardSlots, currentPermanentTarget);
			var beforeRequested = unitBuilder.RequestedProductionCount(bot, mcvType);
			var beforeLiveMcvs = LiveMcvCount();
			unitBuilder.RequestUnitProduction(bot, mcvType);
			var accepted = unitBuilder.RequestedProductionCount(bot, mcvType) > beforeRequested || McvAlreadyQueued() || LiveMcvCount() > beforeLiveMcvs;
			if (accepted)
			{
				pendingMcvSlotReservation = !McvAlreadyQueued() && LiveMcvCount() == beforeLiveMcvs;
				pendingMcvSlotReservationLiveCount = beforeLiveMcvs;
			}

			return accepted;
		}

		IEnumerable<Actor> LiveOwnedMcvs()
		{
			// ActorIndex only contains actors that are currently in World. Native Cargo passengers
			// are temporarily removed from World, so capacity accounting must also walk live owned
			// Cargo manifests. One ActorID is yielded once even if an engine/index transition makes
			// the same MCV visible through both sources for a frame.
			var seen = new HashSet<uint>();
			foreach (var mcv in mcvs.Actors)
				if (IsLiveOwnedMcv(mcv) && seen.Add(mcv.ActorID))
					yield return mcv;

			foreach (var transport in world.ActorsHavingTrait<Cargo>())
			{
				if (transport == null || !transport.IsInWorld || transport.IsDead || transport.Owner != player)
					continue;

				var cargo = transport.TraitOrDefault<Cargo>();
				if (cargo == null || cargo.IsTraitDisabled)
					continue;

				foreach (var passenger in cargo.Passengers)
					if (passenger != null && !passenger.IsDead && passenger.Owner == player &&
						Info.McvTypes.Contains(passenger.Info.Name) && IsLiveOwnedMcv(passenger) && seen.Add(passenger.ActorID))
						yield return passenger;
			}
		}

		// Picks the first configured MCV type an owned, enabled queue can actually produce.
		// A bare alphabetical pick selects a foreign faction's MCV whenever McvTypes spans the
		// whole roster (e.g. asianalliance_* for a Soviet bot), and that request never materializes.
		string PickBuildableMcvType()
		{
			var queues = AIUtils.FindQueuesByCategory(player)
				.SelectMany(g => g)
				.Where(q => q.Enabled)
				.ToArray();
			return Info.McvTypes.OrderBy(x => x)
				.FirstOrDefault(t => world.Map.Rules.Actors.ContainsKey(t) &&
					queues.Any(q => q.BuildableItems().Any(i => i.Name == t)));
		}

		int LiveMcvCount() => LiveOwnedMcvs().Count();

		int LiveConstructionYardCount() => constructionYards.Actors.Count(a => a.IsInWorld && !a.IsDead && a.Owner == player);

		int QueuedMcvCount()
		{
			// Count both producer-attached queues and the player-actor fallback queues.
			// Distinct prevents the same queue from consuming two strict Construction Yard slots.
			var queues = mcvFactories.Actors
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player)
				.SelectMany(a => a.TraitsImplementing<ProductionQueue>())
				.Concat(playerActor.TraitsImplementing<ProductionQueue>())
				.Where(q => q.Enabled)
				.Distinct();

			return queues.Sum(q => q.AllQueued().Count(item => Info.McvTypes.Contains(item.Item)));
		}

		void RefreshPendingMcvSlotReservation()
		{
			if (!pendingMcvSlotReservation)
				return;

			if (QueuedMcvCount() > 0 || LiveMcvCount() > pendingMcvSlotReservationLiveCount)
				pendingMcvSlotReservation = false;
		}

		int CountConstructionYardSlots()
		{
			RefreshPendingMcvSlotReservation();
			return LiveConstructionYardCount() + LiveMcvCount() + QueuedMcvCount() + (pendingMcvSlotReservation ? 1 : 0);
		}

		bool TryRepackNewestReserveConyard(IBot bot, string reason)
		{
			if (stage != ExpansionStage.Idle || activeMcv != null || activeConyard != null ||
				LiveConstructionYardCount() <= CurrentPermanentFactFloor())
				return false;

			var candidate = constructionYards.Actors
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && a != mainConyard)
				.Where(a => generalService == null || !generalService.IsSecureAnchor(a.Location))
				.OrderByDescending(a => a.ActorID)
				.FirstOrDefault();
			if (candidate == null)
				return false;

			mcvRetreatAfterRepackPending = false;
			activeConyard = candidate;
			lastTransformCell = candidate.Location;
			stage = ExpansionStage.WaitingForMcv;
			repackTransformIssuedTick = world.WorldTick;
			repackTransformRetries = 0;
			FransBotLog.BotDebug(world,
				"{0}: newest non-main non-SECURE Construction Yard {1} repacks as the reserve MCV because {2}. Protected SECURE anchors are never consumed; strict slot budget remains {3}/{4}.",
				player, candidate, reason, CountConstructionYardSlots(), Info.MaximumConstructionYardSlots);
			bot.QueueOrder(new Order("DeployTransform", candidate, true));
			return true;
		}

		bool McvAlreadyQueued() => QueuedMcvCount() > 0;

		static double ElapsedMilliseconds(long started) =>
			(Stopwatch.GetTimestamp() - started) * 1000.0 / Stopwatch.Frequency;

		static int OrderedCellHash(IReadOnlyList<CPos> cells)
		{
			if (cells == null || cells.Count == 0)
				return 0;

			unchecked
			{
				var hash = 17;
				for (var i = 0; i < cells.Count; i++)
					hash = hash * 31 + cells[i].Bits;
				return hash;
			}
		}

		void LogMcvObjectivePerf(Actor mcv, Mobile mobile, McvObjectivePerfPass perf, bool landScanRan)
		{
			if (mcv == null || mobile == null || perf == null)
				return;

			var elapsedMs = perf.Sea.ElapsedMs + perf.Land.ElapsedMs;
			var physicalSearches = perf.Sea.PhysicalNativePathSearches + perf.Land.PhysicalNativePathSearches;
			if ((physicalSearches == 0 && elapsedMs < 10.0) || world.WorldTick < nextMcvObjectivePerfLogTick)
				return;

			nextMcvObjectivePerfLogTick = world.WorldTick + 250;
			try
			{
				var routineLandCandidateEvidence = landScanRan && perf.Land.ElapsedMs >= 10.0
					? $" landCandidateEvidence=[{perf.Land.FormatRoutineLandCandidateEvidence()}]"
					: string.Empty;
				OpenRA.Log.Write("debug",
					$"[MCV OBJECTIVE PERF][WT {world.WorldTick}] mcv={mcv.ActorID}/{mcv.Info.Name}/{mobile.ToCell} " +
					$"task={expansionTask.Id}/{expansionTask.Mode} stage={stage} scans={(landScanRan ? "Sea+Land" : "Sea")} " +
					$"mapCells={world.Map.AllCells.Count()} [{perf.Sea.Format()}] " +
					$"[{perf.Land.Format()}] uniqueExactProofs={perf.UniqueExactProofs} " +
					$"duplicateExactProofs={perf.DuplicateExactProofs} " +
					$"crossSeaLandExactDuplicates={perf.CrossSeaLandExactDuplicates} " +
					$"duplicateResolvedDeployCells={perf.DuplicateResolvedDeployCells} elapsedMs={elapsedMs:0.00}" +
					routineLandCandidateEvidence);
			}
			catch
			{
				// Aggregate diagnostics must never affect expansion selection or MCV ownership.
			}
		}

		void LogMcvRecoveryPerf(Actor mcv, Mobile mobile, McvRecoveryPerf perf,
			string result, CPos? selectedDeployCell, long started)
		{
			if (mcv == null || mobile == null || perf == null)
				return;

			var elapsedMs = ElapsedMilliseconds(started);
			var success = result == "Success";
			var nextLogTick = success ? nextMcvRecoverySuccessPerfLogTick : nextMcvRecoveryFailurePerfLogTick;
			if ((perf.PhysicalNativePathSearches == 0 && elapsedMs < 10.0) || world.WorldTick < nextLogTick)
				return;

			if (success)
				nextMcvRecoverySuccessPerfLogTick = world.WorldTick + 250;
			else
				nextMcvRecoveryFailurePerfLogTick = world.WorldTick + 250;
			try
			{
				OpenRA.Log.Write("debug",
					$"[MCV RECOVERY PERF][WT {world.WorldTick}] mcv={mcv.ActorID}/{mcv.Info.Name}/{mobile.ToCell} " +
					$"task={expansionTask.Id}/{expansionTask.Mode} stage={stage} trigger={perf.Trigger} " +
					$"recheckGateBypassed={perf.RecheckGateBypassed} recheckDueIn={perf.RecheckDueIn} " +
					$"anchorSource={perf.AnchorSource ?? "None"} anchorCenters={perf.AnchorCenters} " +
					$"distinctAnchorCenters={perf.DistinctAnchorCenters} resourceNodes=0 candidateObjectives=0 " +
					$"deployCellsEnumerated={perf.DeployCellsEnumerated} outsideMap={perf.DeployCellsOutsideMap} " +
					$"mobilityRejected={perf.DeployCellsMobilityRejected} placementChecks={perf.BuildingPlacementChecks} " +
					$"placementRejected={perf.DeployCellsPlacementRejected} " +
					$"deployLegalityRejects={perf.DeployCellsOutsideMap + perf.DeployCellsMobilityRejected + perf.DeployCellsPlacementRejected} " +
					$"deployRiskChecks={perf.DeployCellRiskChecks} " +
					$"deployRiskRejected={perf.DeployCellsRiskRejected} deployCandidates={perf.DeployCandidatesGenerated} " +
					$"duplicateDeployCandidates={perf.DuplicateDeployCandidates} rankedDeployCandidates={perf.RankedDeployCandidates} " +
					$"logicalNativeProofs={perf.LogicalNativeProofRequests} physicalNativeSearches={perf.PhysicalNativePathSearches} " +
					$"nativeTargetCells={perf.NativeTargetCells} pathCostCallbacks={perf.NativePathCostCallbackCalls} " +
					$"riskPathCostCalls={perf.RiskPathCostCalls} preparedPathCost=False topologyRejects=0 " +
					$"strategicMapRouteProofs=0 cacheHits=0 " +
					$"nativePathFailures={perf.NativePathFailures} nativeMs={perf.NativePathSearchElapsedMs:0.00} " +
					$"maxNativeMs={perf.MaxNativePathSearchElapsedMs:0.00} maxNativeCallbacks={perf.MaxNativePathSearchCallbackCalls} " +
					$"routeRiskChecks={perf.RouteRiskChecks} routeRiskRejects={perf.RouteRiskRejects} shorelineCandidates=0 " +
					$"selectedDeploy={(selectedDeployCell.HasValue ? selectedDeployCell.Value.ToString() : "none")} " +
					$"result={result} elapsedMs={elapsedMs:0.00}");
			}
			catch
			{
				// Aggregate diagnostics must never affect recovery selection or MCV ownership.
			}
		}

		void ResetEmergencyRecoveryMoveDiagnostics(Mobile mobile)
		{
			emergencyRecoveryMoveLastProgressCell = mobile?.ToCell;
			emergencyRecoveryMoveLastProgressTick = world.WorldTick;
			nextMcvRecoveryMovePerfLogTick = world.WorldTick + Math.Max(25, Info.MovingMcvStallTimeoutTicks);
		}

		void TrackEmergencyRecoveryMoveState(Actor mcv, Mobile mobile, CPos? target, string state)
		{
			if (mcv == null)
				return;

			var currentCell = mobile?.ToCell ?? mcv.Location;
			if (!emergencyRecoveryMoveLastProgressCell.HasValue ||
				emergencyRecoveryMoveLastProgressCell.Value != currentCell)
			{
				emergencyRecoveryMoveLastProgressCell = currentCell;
				emergencyRecoveryMoveLastProgressTick = world.WorldTick;
				return;
			}

			if (emergencyRecoveryMoveLastProgressTick < 0)
				emergencyRecoveryMoveLastProgressTick = world.WorldTick;
			var noProgressTicks = world.WorldTick - emergencyRecoveryMoveLastProgressTick;
			var operational = mobile != null && !mobile.IsTraitDisabled && !mobile.IsTraitPaused;
			var offTarget = target.HasValue && currentCell != target.Value;
			if (operational && (!offTarget || noProgressTicks < Info.MovingMcvStallTimeoutTicks))
				return;
			if (world.WorldTick < nextMcvRecoveryMovePerfLogTick)
				return;

			nextMcvRecoveryMovePerfLogTick = world.WorldTick + 250;
			try
			{
				var activity = mcv.CurrentActivity;
				var activityLabel = activity == null
					? "None"
					: string.Join("/", activity.DebugLabelComponents());
				var queuedMoveActivities = activity?.ActivitiesImplementing<Move>().Count() ?? 0;
				OpenRA.Log.Write("debug",
					$"[MCV RECOVERY MOVE][WT {world.WorldTick}] mcv={mcv.ActorID}/{mcv.Info.Name}/{currentCell} " +
					$"task={expansionTask.Id}/{expansionTask.Mode} stage={stage} state={state} " +
					$"target={(target.HasValue ? target.Value.ToString() : "none")} " +
					$"distanceSquared={(target.HasValue ? (target.Value - currentCell).LengthSquared : -1)} " +
					$"idle={mcv.IsIdle} mobilePresent={mobile != null} " +
					$"mobileDisabled={mobile?.IsTraitDisabled ?? false} mobilePaused={mobile?.IsTraitPaused ?? false} " +
					$"activity={activityLabel} queuedMoveActivities={queuedMoveActivities} " +
					$"lastProgressCell={emergencyRecoveryMoveLastProgressCell} " +
					$"lastProgressTick={emergencyRecoveryMoveLastProgressTick} noProgressWT={noProgressTicks} " +
					$"nextRecoveryCheck={emergencyRecoveryNextCheckTick} " +
					$"recheckDueIn={Math.Max(0, emergencyRecoveryNextCheckTick - world.WorldTick)} " +
					$"deployIssuedTick={emergencyRecoveryDeployIssuedTick}");
			}
			catch
			{
				// Liveness diagnostics must never affect recovery movement or ownership.
			}
		}

		void ManageExpansionMcv(IBot bot)
		{
			LogMcvIdentity(activeMcv);
			var mobile = activeMcv.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
			{
				LogMcvWaitingState(activeMcv, "NoOperationalMobileTrait");
				return;
			}

			// A rejected coastal staging FACT remains the same NAVAL SUPPORT task. Never let the
			// no-target branch fall back to ordinary ore planning while naval access is still absent.
			if (coastalStagingForSeaExpansion && !HasUsableLandingCraftProducerForCurrentDemand() &&
				(!targetDeployCell.HasValue || !targetResourceCenter.HasValue))
			{
				if (world.WorldTick >= nextCoastalStagingSearchTick)
					TryRetargetFailedCoastalStaging(bot, activeMcv, mobile);
				if (!targetDeployCell.HasValue || !targetResourceCenter.HasValue)
					LogMcvWaitingState(activeMcv, "CoastalStagingAwaitingValidRetarget");
				return;
			}

			// While the naval-support MCV is physically moving to its coastal staging cell,
			// opportunistically start SPEN/SYRD from the existing base if that shoreline
			// is already legal. The MCV still deploys as requested, but naval construction
			// need not wait for its travel time. Placement scans stay cached/throttled.
			if (HasCommittedSeaExpansionDemand && coastalStagingForSeaExpansion && world.WorldTick >= nextSeaPlanningTick)
			{
				nextSeaPlanningTick = world.WorldTick + Info.SeaPlanningInterval;
				RequestLandingCraft(bot);
			}

			// Poll immediate risk every normal 25-WT expansion scan. This primes the shared
			// recent-damage observation before the first hit and gives an active MCV a fast
			// interrupt instead of waiting for the old 125-WT route recheck cadence.
			if (Info.EnableMcvRetreat &&
				(stage == ExpansionStage.MovingToOre || stage == ExpansionStage.ClearingLandDeployArea) &&
				TryStartMcvRetreat(bot, activeMcv, mobile))
				return;

			if (!targetDeployCell.HasValue || !targetResourceCenter.HasValue)
			{
				if (firstExpansionRefineryReservationCompleted &&
					earlyNavalTopologyRequired && navalCapabilityDemandLatched && !HasOwnedLandingCraftProducer() &&
					!CanPlaceAnyLandingCraftProducerFromCurrentBase() && world.WorldTick >= nextSeaPlanningTick)
				{
					nextSeaPlanningTick = world.WorldTick + Info.SeaPlanningInterval;
					if (TryBeginCoastalStaging(bot, activeMcv, mobile))
					{
						FransBotLog.BotDebug(world,
							"{0}: TOPOLOGY-PROVEN EARLY NAVY coastal bootstrap pre-empts another routine ore hop: Explore Map proves a sea-required ore objective but no current FACT can place SPEN/SYRD; roaming MCV {1} creates shoreline build radius first.",
							player, activeMcv);
						return;
					}
				}


				if (world.WorldTick < nextLandExpansionPlanningTick &&
					TryContinuePendingPioneerPhysicalProof(activeMcv))
					return;

				if (world.WorldTick < nextLandExpansionPlanningTick)
				{
					LogMcvWaitingState(activeMcv, $"ExpansionPlanningCooldownUntilWT{nextLandExpansionPlanningTick}");
					return;
				}

				if (activePioneerObjective.HasValue)
				{
					EnsureAlternatePioneerObjective(activeMcv);
					var pioneer = activePioneerObjective.Value;
					if (RequiresPioneerReconBeforeCommit(pioneer))
					{
						if (!activePioneerObjective.HasValue || activePioneerObjective.Value != pioneer)
						{
							nextLandExpansionPlanningTick = world.WorldTick;
							return;
						}

						// Re-evaluating the permission gate above clears stale routine RECON state
						// when a legally known ore objective is tactically Safe. Only current
						// Uncertain/Contested exposure may keep this hold alive.
						// If the backup has already been legitimately scout-cleared and is not
						// contested/hostile, use it now instead of burning the full PRIMARY hold.
						if (TryPromoteReadyAlternatePioneerObjective(activeMcv))
						{
							nextLandExpansionPlanningTick = world.WorldTick;
						}
						else if (activePioneerObjectiveStartedTick >= 0 &&
							world.WorldTick - activePioneerObjectiveStartedTick >= Info.PioneerObjectiveMaximumHoldTicks)
						{
							AbandonActivePioneerObjective($"pre-commit RECON/SECURE hold exceeded {Info.PioneerObjectiveMaximumHoldTicks} WT", activeMcv);
							nextLandExpansionPlanningTick = world.WorldTick;
							return;
						}
						else
						{
							nextLandExpansionPlanningTick = world.WorldTick + Info.PioneerReconHoldReplanInterval;
							LogMcvWaitingState(activeMcv, "PioneerObjectiveWaitingForReconOrSecure");
							return;
						}
					}
				}

				// advance only a bounded amount of expensive sea-target work per
				// simulation pass. Do not prematurely commit a land target while the same
				// objective-ordering sea scan is still in progress.
				var objectivePerf = new McvObjectivePerfPass();
				SeaTargetChoice? seaChoice;
				bool seaSearchPending;
				var seaStarted = Stopwatch.GetTimestamp();
				using (FransBotLog.Profile(world, player, "MCV.RoutineSeaObjectiveScan"))
					seaChoice = FindNearestRoutineSeaOreField(activeMcv, mobile, out seaSearchPending,
						perf: objectivePerf.Sea);
				objectivePerf.Sea.ElapsedMs = ElapsedMilliseconds(seaStarted);
				objectivePerf.Sea.Pending = seaSearchPending;
				if (seaChoice.HasValue)
				{
					objectivePerf.Sea.AcceptedObjective = seaChoice.Value.ResourceCenter;
					objectivePerf.Sea.AcceptedDeployCell = seaChoice.Value.DeployCell;
				}
				if (seaSearchPending)
				{
					LogMcvObjectivePerf(activeMcv, mobile, objectivePerf, landScanRan: false);
					nextLandExpansionPlanningTick = world.WorldTick + 25;
					LogMcvWaitingState(activeMcv, "BoundedSeaTargetSearchInProgress");
					return;
				}

				OreChoice? choice;
				var landStarted = Stopwatch.GetTimestamp();
				using (FransBotLog.Profile(world, player, "MCV.RoutineLandObjectiveScan"))
					choice = FindNearestSafeOreField(activeMcv, mobile, logChoice: false, perf: objectivePerf.Land);
				objectivePerf.Land.ElapsedMs = ElapsedMilliseconds(landStarted);
				if (choice.HasValue)
				{
					objectivePerf.Land.AcceptedObjective = choice.Value.ResourceCenter;
					objectivePerf.Land.AcceptedDeployCell = choice.Value.DeployCell;
				}
				LogMcvObjectivePerf(activeMcv, mobile, objectivePerf, landScanRan: true);

				// NEAREST-FIRST PIONEER: land and sea candidates share one simple doctrine.
				// Pick the nearest physically viable objective first. If that exact objective is still
				// unknown, request RECON for it instead of jumping across the map to a farther known
				// ore. RiskModel remains a veto/safe-route layer, not a strategic target-ranking bonus.
				bool preferSea;
				using (FransBotLog.Profile(world, player, "MCV.RoutineObjectiveArbitration"))
					preferSea = seaChoice.HasValue &&
						(!choice.HasValue || ShouldPreferRoutineSeaTarget(activeMcv, choice.Value, seaChoice.Value));
				if (preferSea)
				{
					SetActivePioneerObjective(seaChoice.Value.ResourceCenter, "nearest-first planner selected this other-landmass ore");
					EnsureAlternatePioneerObjective(activeMcv);
					if (RequiresPioneerReconBeforeCommit(seaChoice.Value.ResourceCenter))
					{
						nextLandExpansionPlanningTick = world.WorldTick + Info.PioneerReconHoldReplanInterval;
						LogMcvWaitingState(activeMcv, "SeaTargetWaitingForRecon");
						return;
					}

					nextSeaPlanningTick = world.WorldTick + Info.SeaPlanningInterval;
					if (TryBeginSeaExpansion(bot, activeMcv, mobile, seaChoice.Value))
					{
						FransBotLog.BotDebug(world,
							"{0}: ROUTINE EXPANSION PARITY selects sea ore {1} for MCV {2}: {3}. Ordinary Growing/expansion therefore uses an LST as the movement mechanism instead of treating the other landmass as a separate strategic mode.",
							player, seaChoice.Value.ResourceCenter, activeMcv,
							choice.HasValue ? "it outranks the best safe land objective in the shared ore ordering" : "no safe land objective exists");
						return;
					}
				}

				if (!choice.HasValue && !seaChoice.HasValue && activePioneerObjective.HasValue)
				{
					AbandonActivePioneerObjective("selected ore no longer has an executable land or sea expansion route", activeMcv);
					nextLandExpansionPlanningTick = world.WorldTick;
					return;
				}

				if (!choice.HasValue)
				{
					nextLandExpansionPlanningTick = world.WorldTick + Info.NoLandExpansionReplanInterval;
					LogMcvWaitingState(activeMcv, "NoValidLandOrSeaExpansionTarget");
					FransBotLog.BotDebug(world,
						"{0}: routine expansion found no safe land objective and no executable sea objective for MCV {1}; next full replan is WT {2}.",
						player, activeMcv, nextLandExpansionPlanningTick);
					return;
				}

				SetActivePioneerObjective(choice.Value.ResourceCenter, "nearest-first planner selected this land ore");
				EnsureAlternatePioneerObjective(activeMcv);
				if (RequiresPioneerReconBeforeCommit(choice.Value.ResourceCenter))
				{
					nextLandExpansionPlanningTick = world.WorldTick + Info.PioneerReconHoldReplanInterval;
					LogMcvWaitingState(activeMcv, "LandTargetWaitingForRecon");
					return;
				}

				if (!CommitLandOreTask(bot, activeMcv, mobile, choice.Value,
					"nearest-first planner selected the closest viable land ore"))
				{
					LogMcvWaitingState(activeMcv, "LandExpansionTaskCommitRefused");
					return;
				}
				var expansionPermission = IsExpansionGroundSecured(targetResourceCenter.Value)
					? "GROUND-SECURED"
					: HasPioneerScoutClearance(targetResourceCenter.Value)
						? "TACTICALLY SCOUT-CLEARED"
						: "KNOWN-ORE CLAIM";
				FransBotLog.BotDebug(world,
					"{0}: NEAREST-FIRST PIONEER selects land ore {1} for MCV {2}, deploy {3}; permission {4}. RiskModel accepted the route as non-critical and within the bounded detour limit; farther objectives receive no strategic score bonus.",
					player, targetResourceCenter.Value, activeMcv, targetDeployCell.Value, expansionPermission);
				return;
			}


			if (stage == ExpansionStage.ClearingLandDeployArea)
			{
				ManageLandDeployClearance(bot, activeMcv, mobile);
				return;
			}

			if (!activeMcv.IsIdle)
			{
				if (world.WorldTick < nextRouteRecheckTick)
					return;

				nextRouteRecheckTick = world.WorldTick + Info.RouteRecheckInterval;
				if (TryYieldToEarlierAlliedMcvReservation(bot))
					return;
				if (TryReplanPermanentlyBlockedDeployTarget(bot, activeMcv, mobile))
					return;

				if (!movingMcvLastProgressCell.HasValue || movingMcvLastProgressCell.Value != mobile.ToCell)
				{
					movingMcvLastProgressCell = mobile.ToCell;
					movingMcvLastProgressTick = world.WorldTick;
					movingMcvStallRetries = 0;
				}
				else if (movingMcvLastProgressTick >= 0 && world.WorldTick - movingMcvLastProgressTick >= Info.MovingMcvStallTimeoutTicks)
				{
					if (movingMcvStallRetries < Info.MovingMcvStallMaximumRetries)
					{
						movingMcvStallRetries++;
						movingMcvLastProgressTick = world.WorldTick;
						FransBotLog.BotDebug(world,
							"{0}: MCV MOVE WATCHDOG: {1} made no cell progress at {2} for {3} WT while native Move remained active; bounded retry {4}/{5} toward {6}.",
							player, activeMcv, mobile.ToCell, Info.MovingMcvStallTimeoutTicks, movingMcvStallRetries, Info.MovingMcvStallMaximumRetries, targetDeployCell.Value);
						QueueRiskAwareMove(activeMcv, mobile, targetDeployCell.Value);
						return;
					}

					var stalledField = targetResourceCenter.Value;
					FransBotLog.BotDebug(world,
						"{0}: MCV MOVE WATCHDOG releases stalled objective {1}: {2} remained at {3} through {4} bounded retries. The field receives normal retry cooldown and the roaming MCV replans instead of deadlocking.",
						player, stalledField, activeMcv, mobile.ToCell, Info.MovingMcvStallMaximumRetries);
					QueueStopOrder(bot, activeMcv);
					failedFieldsUntil[stalledField] = world.WorldTick + Info.FailedFieldRetryDelay;
					AbortExpansionTaskToIdle(bot, "land MCV no-progress watchdog rejected the current ore objective", stalledField);
					nextLandExpansionPlanningTick = world.WorldTick;
					return;
				}

				var targetRisk = GetMcvRisk(activeMcv, targetDeployCell.Value, CurrentMcvRiskTolerance);
				if (targetRisk.IsCritical)
				{
					// Only a critical destination invalidates an MCV that is still making progress.
					// Static/remembered critical danger gets a normal failed-field cooldown; a transient
					// mobile contact is allowed to be reconsidered after it moves away.
					if (targetRisk.StaticThreatCount > 0 || targetRisk.StrategicRiskScore >= 60)
					{
						MarkCurrentFieldFailed();
						var dangerousObjective = targetResourceCenter ?? targetDeployCell.Value;
						MarkExpansionAreaRequiresSecure(dangerousObjective, "critical known destination danger discovered during pioneer travel");
						RememberDangerousExpansionArea(dangerousObjective);
					}
					FransBotLog.BotDebug(world, "{0}: RiskModel aborts MCV destination {1}: risk {2} >= critical {3} (visible {4}, strategic {5}, static threats {6}).",
						player, targetDeployCell.Value, targetRisk.Score, targetRisk.CriticalThreshold,
						targetRisk.VisibleRiskScore, targetRisk.StrategicRiskScore, targetRisk.StaticThreatCount);
					QueueStopOrder(bot, activeMcv);
					AbortExpansionTaskToIdle(bot, "critical destination validation rejected the current expansion objective", targetResourceCenter ?? targetDeployCell.Value);
					nextLandExpansionPlanningTick = world.WorldTick;
				}

				return;
			}

			var idleTargetRisk = GetMcvRisk(activeMcv, targetDeployCell.Value, CurrentMcvRiskTolerance);
			if (idleTargetRisk.IsCritical)
			{
				if (idleTargetRisk.StaticThreatCount > 0 || idleTargetRisk.StrategicRiskScore >= 60)
				{
					MarkCurrentFieldFailed();
					var dangerousObjective = targetResourceCenter ?? targetDeployCell.Value;
					MarkExpansionAreaRequiresSecure(dangerousObjective, "critical known destination danger discovered before deployment");
					RememberDangerousExpansionArea(dangerousObjective);
				}
				AbortExpansionTaskToIdle(bot, "idle destination risk rejected the current expansion objective", targetResourceCenter ?? targetDeployCell.Value);
				nextLandExpansionPlanningTick = world.WorldTick;
				return;
			}

			if (mobile.ToCell != targetDeployCell.Value)
			{
				// Native Move may terminate before reaching the target (traffic/path failure). Treat
				// this as the same bounded no-progress condition as an active-but-stalled Move.
				// A real cell change resets the watchdog; an unchanged idle MCV never receives an
				// unbounded 125-WT order loop again.
				if (!movingMcvLastProgressCell.HasValue || movingMcvLastProgressCell.Value != mobile.ToCell)
				{
					movingMcvLastProgressCell = mobile.ToCell;
					movingMcvLastProgressTick = world.WorldTick;
					movingMcvStallRetries = 0;
				}

				if (world.WorldTick < nextRouteRecheckTick)
					return;

				nextRouteRecheckTick = world.WorldTick + Info.RouteRecheckInterval;
				if (TryYieldToEarlierAlliedMcvReservation(bot))
					return;
				if (TryReplanPermanentlyBlockedDeployTarget(bot, activeMcv, mobile))
					return;

				if (movingMcvLastProgressTick >= 0 && world.WorldTick - movingMcvLastProgressTick < Info.MovingMcvStallTimeoutTicks)
					return;

				if (movingMcvStallRetries < Info.MovingMcvStallMaximumRetries)
				{
					movingMcvStallRetries++;
					movingMcvLastProgressTick = world.WorldTick;
					FransBotLog.BotDebug(world,
						"{0}: MCV MOVE WATCHDOG: native Move ended before destination and {1} remained at {2}; bounded idle retry {3}/{4} toward {5}.",
						player, activeMcv, mobile.ToCell, movingMcvStallRetries, Info.MovingMcvStallMaximumRetries, targetDeployCell.Value);
					QueueRiskAwareMove(activeMcv, mobile, targetDeployCell.Value);
					return;
				}

				var stalledField = targetResourceCenter.Value;
				FransBotLog.BotDebug(world,
					"{0}: MCV MOVE WATCHDOG releases idle stalled objective {1}: {2} remained at {3} through {4} bounded retries. Normal target selection resumes.",
					player, stalledField, activeMcv, mobile.ToCell, Info.MovingMcvStallMaximumRetries);
				QueueStopOrder(bot, activeMcv);
				failedFieldsUntil[stalledField] = world.WorldTick + Info.FailedFieldRetryDelay;
				AbortExpansionTaskToIdle(bot, "moving MCV no-progress watchdog exhausted retries for the current ore", stalledField);
				nextLandExpansionPlanningTick = world.WorldTick;
				return;
			}


			if (!CanDeployAt(activeMcv, targetDeployCell.Value))
			{
				LogMcvDeployment(activeMcv, false, "DeploymentFootprintBlocked");
				LogMcvWaitingState(activeMcv, "DeploymentFootprintClearance");
				BeginLandDeployClearance(bot, activeMcv, mobile, "friendly mobile blockers still occupy the FACT footprint");
				return;
			}

			// tempo rule: FACT deployment is never held hostage by the prebuilt first PROC.
			// If the reserved refinery is still building, deploy now and let the established FACT wait
			// for/receive that exact queue item. This removes multi-thousand-WT folded-MCV idle stalls.
			if (firstExpansionRefineryReservationActive && !firstExpansionRefinerySuspendedForInfrastructure && !IsFirstExpansionRefineryReadyToPlace() &&
				world.WorldTick >= nextNoOreStatusLogTick)
			{
				nextNoOreStatusLogTick = world.WorldTick + 250;
				FransBotLog.BotDebug(world,
					"{0}: first expansion MCV {1} reached deploy cell {2} before reserved PROC finished; deploys FACT immediately and lets the refinery finish behind established build radius.",
					player, activeMcv, targetDeployCell.Value);
			}

			lastTransformCell = activeMcv.Location;
			postSeaUnloadDeployCommitted = false;
			stage = ExpansionStage.WaitingForConyard;
			conyardTransformIssuedTick = world.WorldTick;
			conyardTransformRetries = 0;
			FransBotLog.BotDebug(world,
				coastalStagingForSeaExpansion
					? "{0}: NAVAL SUPPORT MCV {1} reached coastal staging cell {3}; deploying temporary FACT now so naval production can start. Deploy-confirm watchdog armed for {4} WT."
					: "{0}: expansion MCV {1} reached safe ore field {2}; deploying at {3}. Deploy-confirm watchdog armed for {4} WT.",
				player, activeMcv, targetResourceCenter.Value, targetDeployCell.Value, Info.ExpansionDeployConfirmTimeoutTicks);
			LogMcvDeployment(activeMcv, true, "InitialExpansionDeploy");
			bot.QueueOrder(new Order("DeployTransform", activeMcv, true));
		}

		bool TryStartMcvRetreat(IBot bot, Actor mcv, Mobile mobile)
		{
			RefreshAcknowledgedRetreatDamageBaseline(mcv);
			var immediate = riskModelService.EvaluateImmediateRisk(mcv, mcv.Location, FransRiskRole.Mcv, FransRiskTolerance.Cautious);
			var newRecentDamage = IsUnacknowledgedRecentDamage(mcv, immediate);
			var acknowledgedDamageRisk = immediate.RecentlyDamaged && !newRecentDamage ? immediate.RecentDamageRiskScore : 0;
			var effectiveScore = Math.Max(0, immediate.Score - acknowledgedDamageRisk);
			string reason = null;
			if (newRecentDamage)
				reason = $"new recent damage at {mcv.Location} ({immediate.Score}/{immediate.CriticalThreshold})";
			else if (effectiveScore >= immediate.CriticalThreshold)
				reason = $"critical current risk at {mcv.Location} ({effectiveScore}/{immediate.CriticalThreshold}, acknowledged old-damage contribution {acknowledgedDamageRisk})";
			else if (postSeaUnloadDeployCommitted)
			{
				// A successfully unloaded Pioneer MCV has already paid the strategic cost of the ferry.
				// Remembered/static pressure just above Preferred must not make it abandon the validated
				// deploy cell before FACT exists. During this short commitment window only a direct
				// visible weapon threat, genuinely new damage or Critical risk may trigger RETREAT.
				if (immediate.VisibleThreatCount > 0)
					reason = $"direct visible weapon threat during post-landing deploy commitment at {mcv.Location} ({effectiveScore}/{immediate.CriticalThreshold})";
			}
			else if (effectiveScore > immediate.PreferredThreshold && (immediate.VisibleThreatCount > 0 || immediate.RememberedStaticRiskScore > 0))
				reason = $"known weapon pressure at {mcv.Location} ({effectiveScore}/{immediate.PreferredThreshold}, acknowledged old-damage contribution {acknowledgedDamageRisk})";

			if (reason == null)
				return false;

			var failedObjective = targetResourceCenter ?? targetDeployCell;
			QueueStopOrder(bot, mcv);
			MarkCurrentFieldFailed();
			if (failedObjective.HasValue)
				MarkExpansionAreaFailed(failedObjective.Value, "MCV RETREAT");
			RememberDangerousExpansionArea(mcv.Location);
			AbortFirstExpansionRefineryAttempt(bot, "MCV RETREAT", failedObjective);
			ResumeFirstExpansionRefineryAfterInfrastructure("MCV RETREAT released the temporary naval-infrastructure suspension before the first ore expansion completed");
			ReturnExpansionTaskToIdle($"MCV RETREAT aborted the current expansion: {reason}");
			BeginMcvRetreat(mcv, mobile, reason);
			return true;
		}

		void RefreshAcknowledgedRetreatDamageBaseline(Actor mcv)
		{
			if (mcv == null || acknowledgedRetreatDamageActorId != mcv.ActorID)
				return;

			var health = mcv.TraitOrDefault<Health>();
			if (health != null && health.HP > acknowledgedRetreatDamageHp)
				acknowledgedRetreatDamageHp = health.HP;
		}

		bool IsUnacknowledgedRecentDamage(Actor mcv, FransRiskAssessment immediate)
		{
			if (!immediate.RecentlyDamaged)
				return false;

			var health = mcv?.TraitOrDefault<Health>();
			if (health == null)
				return true;

			if (acknowledgedRetreatDamageActorId != mcv.ActorID)
				return true;

			return health.HP < acknowledgedRetreatDamageHp;
		}

		void AcknowledgeRetreatDamageIncident(Actor mcv)
		{
			var health = mcv?.TraitOrDefault<Health>();
			if (mcv == null || health == null)
			{
				acknowledgedRetreatDamageActorId = 0;
				acknowledgedRetreatDamageHp = -1;
				return;
			}

			acknowledgedRetreatDamageActorId = mcv.ActorID;
			acknowledgedRetreatDamageHp = health.HP;
		}

		bool IsMcvRetreatSafetyImprovement(Actor mcv, CPos candidate, out FransRiskAssessment candidateRisk)
		{
			candidateRisk = GetMcvRisk(mcv, candidate, FransRiskTolerance.Cautious);
			if ((candidate - mcv.Location).LengthSquared < Info.McvRetreatMinimumEscapeCells * Info.McvRetreatMinimumEscapeCells)
				return false;
			if (candidateRisk.IsCritical || candidateRisk.VisibleThreatCount > 0)
				return false;

			var currentRisk = GetMcvRisk(mcv, mcv.Location, FransRiskTolerance.Cautious);
			var needsStrictImprovement = currentRisk.IsCritical || currentRisk.VisibleThreatCount > 0;
			return needsStrictImprovement ? candidateRisk.Score < currentRisk.Score : candidateRisk.Score <= currentRisk.Score;
		}

		void BeginMcvRetreat(Actor mcv, Mobile mobile, string reason)
		{
			stage = ExpansionStage.Retreat;
			mcvRetreatAnchor = null;
			mcvRetreatDestination = null;
			mcvRetreatLastProgressCell = mcv.Location;
			mcvRetreatLastProgressTick = world.WorldTick;
			mcvRetreatNextCheckTick = world.WorldTick + Info.McvRetreatRecheckInterval;
			mcvRetreatPathCandidateOffset = 0;

			FransBotLog.BotDebug(world,
				"{0}: MCV {1} MOVE/DEPLOY -> RETREAT at {2}: {3}. Expansion ownership is released; RETREAT only accepts a reachable arrival cell at least the minimum escape distance away with zero visible weapon threats, non-critical risk and a spatial safety improvement.",
				player, mcv, mcv.Location, reason);

			if (!TryAssignMcvRetreatDestination(mcv, mobile, out var anchor, out var destination, out var anchorKind))
			{
				AdvanceMcvRetreatPathCandidateBatch();
				mcvRetreatNextCheckTick = world.WorldTick + Info.McvRetreatStallTimeout;
				FransBotLog.BotDebug(world,
					"{0}: MCV {1} RETREAT has no reachable regroup/base/local-safe destination; it keeps exclusive ownership and retries after {2} WT.",
					player, mcv, Info.McvRetreatStallTimeout);
				return;
			}

			mcvRetreatAnchor = anchor;
			mcvRetreatDestination = destination;
			mcvRetreatAnchorKind = anchorKind;
			QueuePlainMcvRetreatMove(mcv, destination);
			FransBotLog.BotDebug(world,
				"{0}: MCV {1} RETREAT selects safest reachable {2} anchor {3}; one plain Move is issued toward validated safe arrival cell {4}. Candidate safety is ranked before path length.",
				player, mcv, anchorKind, anchor, destination);
		}

		void ManageMcvRetreat(IBot bot)
		{
			if (!IsLiveOwnedMcv(activeMcv))
			{
				HandleUnexpectedActiveMcvLoss(bot, "RETREAT");
				return;
			}

			var mcv = activeMcv;
			var mobile = mcv.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
				return;

			if (mcvRetreatLastProgressCell != mcv.Location)
			{
				mcvRetreatLastProgressCell = mcv.Location;
				mcvRetreatLastProgressTick = world.WorldTick;
			}

			if (world.WorldTick < mcvRetreatNextCheckTick)
				return;
			mcvRetreatNextCheckTick = world.WorldTick + Info.McvRetreatRecheckInterval;

			if (mcvRetreatDestination.HasValue)
			{
				var spatialRisk = GetMcvRisk(mcv, mcv.Location, FransRiskTolerance.Cautious);
				var arrivalRadius = 2;
				var atArrival = (mcv.Location - mcvRetreatDestination.Value).LengthSquared <= arrivalRadius * arrivalRadius;
				var actuallySafe = !spatialRisk.IsCritical && spatialRisk.VisibleThreatCount == 0;
				if (atArrival && actuallySafe)
				{
					AcknowledgeRetreatDamageIncident(mcv);
					FransBotLog.BotDebug(world,
						"{0}: MCV {1} RETREAT complete at {2}; it physically reached safe arrival cell {3} near {4} anchor {5}. Spatial risk is {6}/{7} with zero visible weapon threats. Only now is the triggering damage incident acknowledged.",
						player, mcv, mcv.Location, mcvRetreatDestination.Value, mcvRetreatAnchorKind ?? "retreat", mcvRetreatAnchor ?? mcvRetreatDestination.Value, spatialRisk.Score, spatialRisk.CriticalThreshold);
					ResetMcvRetreat();
					stage = ExpansionStage.Idle;
					return;
				}

				if (atArrival && !actuallySafe)
				{
					FransBotLog.BotDebug(world,
						"{0}: MCV {1} reaches RETREAT arrival cell {2} but remains unsafe (risk {3}/{4}, visible threats {5}); RETREAT stays active and immediately searches for a safer destination.",
						player, mcv, mcv.Location, spatialRisk.Score, spatialRisk.CriticalThreshold, spatialRisk.VisibleThreatCount);
					mcvRetreatDestination = null;
				}
			}

			var stalled = mcvRetreatLastProgressTick >= 0 &&
				world.WorldTick - mcvRetreatLastProgressTick >= Info.McvRetreatStallTimeout;
			if (mcvRetreatDestination.HasValue && !stalled)
				return;

			if (!TryAssignMcvRetreatDestination(mcv, mobile, out var anchor, out var destination, out var anchorKind))
			{
				AdvanceMcvRetreatPathCandidateBatch();
				mcvRetreatNextCheckTick = world.WorldTick + Info.McvRetreatStallTimeout;
				return;
			}

			mcvRetreatAnchor = anchor;
			mcvRetreatDestination = destination;
			mcvRetreatAnchorKind = anchorKind;
			mcvRetreatLastProgressCell = mcv.Location;
			mcvRetreatLastProgressTick = world.WorldTick;
			QueuePlainMcvRetreatMove(mcv, destination);
			FransBotLog.BotDebug(world,
				stalled
					? "{0}: MCV {1} RETREAT stalled for {2} WT; one fresh plain Move is issued toward nearest {3} regroup anchor {4} via {5}."
					: "{0}: MCV {1} RETREAT acquires nearest {3} regroup anchor {4} via {5}.",
				player, mcv, Info.McvRetreatStallTimeout, anchorKind, anchor, destination);
		}

		bool TryAssignMcvRetreatDestination(Actor mcv, Mobile mobile, out CPos anchor, out CPos destination, out string anchorKind)
		{
			anchor = default;
			destination = default;
			anchorKind = "Ground";
			var choices = new List<(CPos Anchor, CPos Destination, int RiskScore, int PathLength, int AnchorDistance)>();
			var regroupPoints = groundCommanderService != null ? groundCommanderService.GetGroundRegroupPoints() : Array.Empty<CPos>();

			foreach (var point in regroupPoints)
				if (TryFindPlainMcvRetreatArrival(mcv, mobile, point, out var arrival, out var pathLength, out var riskScore))
					choices.Add((point, arrival, riskScore, pathLength, (point - mcv.Location).LengthSquared));

			if (choices.Count > 0)
			{
				var best = choices.OrderBy(x => x.RiskScore).ThenBy(x => x.PathLength).ThenBy(x => x.AnchorDistance).ThenBy(x => x.Anchor.X).ThenBy(x => x.Anchor.Y).First();
				anchor = best.Anchor;
				destination = best.Destination;
				return true;
			}

			var factChoices = new List<(CPos Anchor, CPos Destination, int RiskScore, int PathLength)>();
			foreach (var fact in constructionYards.Actors.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player))
				if (TryFindPlainMcvRetreatArrival(mcv, mobile, fact.Location, out var arrival, out var pathLength, out var riskScore))
					factChoices.Add((fact.Location, arrival, riskScore, pathLength));

			if (factChoices.Count > 0)
			{
				var bestFact = factChoices.OrderBy(x => x.RiskScore).ThenBy(x => x.PathLength).ThenBy(x => (x.Anchor - mcv.Location).LengthSquared).First();
				anchor = bestFact.Anchor;
				destination = bestFact.Destination;
				anchorKind = "FACT fallback";
				return true;
			}

			var fallback = openingBuildOrderService.StrategicBaseCenter;
			if (TryFindPlainMcvRetreatArrival(mcv, mobile, fallback, out destination, out _, out _))
			{
				anchor = fallback;
				anchorKind = "main-base fallback";
				return true;
			}

			// A freshly landed MCV may be on a landmass with no safe/reachable Ground regroup point,
			// FACT or path to the main base. Fall back to a reachable local cell that is both
			// non-critical and a real spatial safety improvement.
			if (!TryFindLocalSafeMcvRetreatDestination(mcv, mobile, out destination, out var localRisk))
				return false;

			anchor = destination;
			anchorKind = $"local-safe risk {localRisk}";
			return true;
		}

		bool TryFindLocalSafeMcvRetreatDestination(Actor mcv, Mobile mobile, out CPos destination, out int riskScore)
		{
			destination = default;
			riskScore = int.MaxValue;
			if (mobile.PathFinder is not PathFinder pathFinder)
				return false;

			var minRadius = Math.Max(4, Info.McvRetreatArrivalRadius / 2);
			var maxRadius = Math.Max(minRadius, Info.McvRetreatAnchorSearchRadius * 2);
			var candidates = world.Map.FindTilesInAnnulus(mobile.ToCell, minRadius, maxRadius)
				.Where(world.Map.Contains)
				.Where(cell => mobile.CanEnterCell(cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(cell))
				.Select(cell =>
				{
					var safe = IsMcvRetreatSafetyImprovement(mcv, cell, out var risk);
					return (Cell: cell, Safe: safe, Risk: risk);
				})
				.Where(x => x.Safe)
				.OrderBy(x => x.Risk.Score)
				.ThenByDescending(x => (x.Cell - mobile.ToCell).LengthSquared)
				.ThenBy(x => x.Cell.X)
				.ThenBy(x => x.Cell.Y)
				.Take(McvRetreatRankedCandidatePool)
				.Skip(mcvRetreatPathCandidateOffset)
				.Take(Info.McvRetreatMaximumPathCandidatesPerAnchor);

			var bestPathLength = int.MaxValue;
			foreach (var candidate in candidates)
			{
				if (!TryFindPlainMcvRetreatPath(mcv, mobile, pathFinder, candidate.Cell, out var path))
					continue;

				if (candidate.Risk.Score > riskScore ||
					(candidate.Risk.Score == riskScore && path.Count >= bestPathLength))
					continue;

				destination = candidate.Cell;
				riskScore = candidate.Risk.Score;
				bestPathLength = path.Count;
			}

			return bestPathLength != int.MaxValue;
		}

		bool TryFindPlainMcvRetreatArrival(Actor mcv, Mobile mobile, CPos anchor, out CPos destination, out int pathLength, out int riskScore)
		{
			destination = default;
			pathLength = int.MaxValue;
			riskScore = int.MaxValue;
			if (mobile.PathFinder is not PathFinder pathFinder)
				return false;

			var candidates = new[] { anchor }
				.Concat(world.Map.FindTilesInAnnulus(anchor, 1, Info.McvRetreatAnchorSearchRadius))
				.Where(world.Map.Contains)
				.Where(cell => mobile.CanEnterCell(cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(cell))
				.Select(cell =>
				{
					var safe = IsMcvRetreatSafetyImprovement(mcv, cell, out var risk);
					return (Cell: cell, Safe: safe, Risk: risk);
				})
				.Where(x => x.Safe)
				.OrderBy(x => x.Risk.Score)
				.ThenBy(x => (x.Cell - anchor).LengthSquared)
				.ThenBy(x => (x.Cell - mcv.Location).LengthSquared)
				.Take(McvRetreatRankedCandidatePool)
				.Skip(mcvRetreatPathCandidateOffset)
				.Take(Info.McvRetreatMaximumPathCandidatesPerAnchor);

			foreach (var candidate in candidates)
			{
				if (!TryFindPlainMcvRetreatPath(mcv, mobile, pathFinder, candidate.Cell, out var path))
					continue;

				if (candidate.Risk.Score > riskScore || (candidate.Risk.Score == riskScore && path.Count >= pathLength))
					continue;

				destination = candidate.Cell;
				pathLength = path.Count;
				riskScore = candidate.Risk.Score;
			}

			return pathLength != int.MaxValue;
		}

		void AdvanceMcvRetreatPathCandidateBatch()
		{
			var step = Math.Max(1, Info.McvRetreatMaximumPathCandidatesPerAnchor);
			mcvRetreatPathCandidateOffset = (mcvRetreatPathCandidateOffset + step) % McvRetreatRankedCandidatePool;
		}

		static bool TryFindPlainMcvRetreatPath(Actor mcv, Mobile mobile, PathFinder pathFinder, CPos destination, out List<CPos> path)
		{
			if (mobile.ToCell == destination)
			{
				path = new List<CPos> { destination };
				return true;
			}

			path = pathFinder.FindPathToTargetCell(mcv, [mobile.ToCell], destination,
				BlockedByActor.Immovable, laneBias: false);
			return path != null && path.Count > 0;
		}

		void QueuePlainMcvRetreatMove(Actor mcv, CPos destination)
		{
			LogMcvMoveOrder(mcv, destination, 1, "Retreat");
			QueueMoveOrder(null, mcv, destination);
		}

		void ResetMcvRetreat()
		{
			mcvRetreatAnchor = null;
			mcvRetreatDestination = null;
			mcvRetreatAnchorKind = null;
			mcvRetreatLastProgressCell = null;
			mcvRetreatLastProgressTick = -1;
			mcvRetreatNextCheckTick = 0;
			mcvRetreatPathCandidateOffset = 0;
		}

		void BeginLandDeployClearance(IBot bot, Actor mcv, Mobile mobile, string reason)
		{
			if (!targetDeployCell.HasValue || !targetResourceCenter.HasValue)
				return;

			if (deployClearanceStartedTick < 0)
			{
				deployClearanceStartedTick = world.WorldTick;
				nextDeployClearanceOrderTick = 0;
				stage = ExpansionStage.ClearingLandDeployArea;
				FransBotLog.BotDebug(world,
					"{0}: expansion MCV {1} begins bounded deploy-area clearance at {2}: {3}. Friendly blocker orders are de-duplicated and the field cannot stall indefinitely.",
					player, mcv, targetDeployCell.Value, reason);
			}

			ManageLandDeployClearance(bot, mcv, mobile);
		}

		void ManageLandDeployClearance(IBot bot, Actor mcv, Mobile mobile)
		{
			if (!targetDeployCell.HasValue || !targetResourceCenter.HasValue || !IsLiveOwnedMcv(mcv))
			{
				ResetDeployClearanceState();
				AbortExpansionTaskToIdle(bot, "deploy-clearance ownership disappeared before a FACT could be committed");
				return;
			}

			var deployCell = targetDeployCell.Value;
			if (mobile.ToCell != deployCell)
			{
				ResetDeployClearanceState(resetReplans: false);
				stage = ExpansionStage.MovingToOre;
				QueueRiskAwareMove(mcv, mobile, deployCell);
				return;
			}

			var canDeploy = CanDeployAt(mcv, deployCell);
			if (canDeploy)
			{
				FransBotLog.BotDebug(world,
					"{0}: deploy-area clearance confirmed for MCV {1} at {2}; friendly mobile blockers are physically clear. FACT deployment may proceed.",
					player, mcv, deployCell);
				ResetDeployClearanceState(resetReplans: false);
				stage = ExpansionStage.MovingToOre;
				return;
			}

			if (world.WorldTick >= nextDeployClearanceOrderTick)
			{
				nextDeployClearanceOrderTick = world.WorldTick + Info.ExpansionDeployClearanceOrderInterval;
				MoveFriendlyDeploymentBlockers(bot, mcv, deployCell);
			}

			if (deployClearanceStartedTick < 0 ||
				world.WorldTick - deployClearanceStartedTick < Info.ExpansionDeployClearanceTimeoutTicks)
				return;

			if (deployClearanceReplans < Info.ExpansionDeployClearanceMaximumReplans)
			{
				deployClearanceReplans++;
					var transformsInfo = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
				var intoActor = transformsInfo != null ? world.Map.Rules.Actors[transformsInfo.IntoActor] : null;
				var buildingInfo = intoActor?.TraitInfoOrDefault<BuildingInfo>();
				if (transformsInfo != null && intoActor != null && buildingInfo != null &&
					TryFindSafeDeployPath(mcv, mobile, targetResourceCenter.Value, transformsInfo, intoActor, buildingInfo,
						out var revisedDeploy, out _) && revisedDeploy != deployCell)
				{
					targetDeployCell = revisedDeploy;
					FransBotLog.BotDebug(world,
						"{0}: deploy-area clearance timeout at {1}; same ore field {2} has alternate legal deploy {3}. MCV {4} repositions instead of repeating blocker orders ({5}/{6}).",
						player, deployCell, targetResourceCenter.Value, revisedDeploy, mcv, deployClearanceReplans, Info.ExpansionDeployClearanceMaximumReplans);
					ResetDeployClearanceState(resetReplans: false);
					stage = ExpansionStage.MovingToOre;
					QueueRiskAwareMove(mcv, mobile, revisedDeploy);
					return;
				}

				deployClearanceStartedTick = world.WorldTick;
				nextDeployClearanceOrderTick = 0;
				FransBotLog.BotDebug(world,
					"{0}: deploy-area clearance at {1} is still blocked after {2} WT and no alternate cell is currently legal; bounded retry {3}/{4} begins without repeating unbounded blocker orders.",
					player, deployCell, Info.ExpansionDeployClearanceTimeoutTicks, deployClearanceReplans, Info.ExpansionDeployClearanceMaximumReplans);
				return;
			}

			FransBotLog.BotDebug(world,
				"{0}: deploy-area clearance exhausted at ore field {1}; MCV {2} refuses an infinite friendly-blocker loop and will choose another field.",
				player, targetResourceCenter.Value, mcv);
			MarkCurrentFieldFailed();
			ResetDeployClearanceState();
			AbortExpansionTaskToIdle(bot, "deploy-clearance recovery abandoned the current expansion target");
		}

		void ResetDeployClearanceState(bool resetReplans = true)
		{
			deployClearanceStartedTick = -1;
			nextDeployClearanceOrderTick = 0;
			if (resetReplans)
				deployClearanceReplans = 0;
		}


		bool TryGetExpansionObjectiveGroundLandmass(CPos objective, out int landmassId)
		{
			landmassId = -1;
			if (strategicMapService == null || !world.Map.Contains(objective))
				return false;

			if (strategicMapService.TryGetGroundLandmassId(objective, out landmassId))
				return true;

			var searchRadius = Math.Max(2, Info.ExploredMapResourceObjectiveRadius);
			foreach (var cell in world.Map.FindTilesInCircle(objective, searchRadius)
				.Where(world.Map.Contains)
				.OrderBy(c => (c - objective).LengthSquared)
				.ThenBy(c => c.X)
				.ThenBy(c => c.Y))
			{
				if (strategicMapService.TryGetGroundLandmassId(cell, out landmassId))
					return true;
			}

			landmassId = -1;
			return false;
		}

		void EvaluateTopologyProvenEarlyNavalRequirement()
		{
			if (earlyNavalTopologyEvaluated)
				return;

			if (!Info.EnableTopologyProvenEarlyNavalBootstrap)
			{
				earlyNavalTopologyEvaluated = true;
				FransBotLog.BotDebug(world,
					"{0}: EARLY NAVY TOPOLOGY PROOF disabled by configuration; ore economy keeps priority until a real SeaOre/transport demand appears.",
					player);
				return;
			}

			if (strategicMapService == null || !strategicMapService.ExploreMapEnabled || !exploredMapResourceObjectivesSeeded)
			{
				if (strategicMapService != null && !strategicMapService.ExploreMapEnabled)
				{
					earlyNavalTopologyEvaluated = true;
					FransBotLog.BotDebug(world,
						"{0}: EARLY NAVY TOPOLOGY PROOF has no Explore Map resource knowledge; proactive naval bootstrap stays off and only real SeaOre/transport demand may latch naval capability.",
						player);
				}
				return;
			}

			var source = mainConyard != null && mainConyard.IsInWorld && !mainConyard.IsDead && mainConyard.Owner == player
				? mainConyard
				: constructionYards.Actors
					.Where(a => a.IsInWorld && !a.IsDead)
					.OrderBy(a => a.ActorID)
					.FirstOrDefault();
			if (source == null || !strategicMapService.TryGetGroundLandmassId(source.Location, out var sourceLandmass))
				return;

			earlyNavalTopologyEvaluated = true;
			earlyNavalTopologyRequired = false;
			earlyNavalTopologyObjective = null;
			earlyNavalTopologySourceLandmass = sourceLandmass;
			earlyNavalTopologyTargetLandmass = -1;

			var remote = exploredMapResourceObjectiveCells
				.Where(world.Map.Contains)
				.Select(center =>
				{
					var known = TryGetExpansionObjectiveGroundLandmass(center, out var targetLandmass);
					return (Center: center, Known: known, TargetLandmass: targetLandmass);
				})
				.Where(x => x.Known && x.TargetLandmass != sourceLandmass && HasNearbyShore(x.Center, Info.SeaLandingSearchRadius))
				.OrderBy(x => (x.Center - source.Location).LengthSquared)
				.ThenBy(x => x.Center.X)
				.ThenBy(x => x.Center.Y)
				.FirstOrDefault();

			if (remote.Known)
			{
				earlyNavalTopologyRequired = true;
				earlyNavalTopologyObjective = remote.Center;
				earlyNavalTopologyTargetLandmass = remote.TargetLandmass;
				FransBotLog.BotDebug(world,
					"{0}: EARLY NAVY TOPOLOGY PROOF requires naval capability: Explore Map ore {1} is on ground landmass {2}, main FACT {3} is on landmass {4}, and the ore has nearby sea access. Water percentage is ignored.",
					player, remote.Center, remote.TargetLandmass, source, sourceLandmass);
			}
			else
			{
				FransBotLog.BotDebug(world,
					"{0}: EARLY NAVY TOPOLOGY PROOF finds no known sea-required ore objective among {1} Explore Map mine/gmine targets from main landmass {2}. Proactive SYRD/SPEN stays off; ore PROC growth keeps priority until real naval demand appears.",
					player, exploredMapResourceObjectiveCells.Count, sourceLandmass);
			}
		}

		void SeedExploredMapResourceObjectives()
		{
			if (exploredMapResourceObjectivesSeeded)
				return;

			exploredMapResourceObjectivesSeeded = true;
			exploredMapResourceObjectiveCells.Clear();
			if (strategicMapService == null || !strategicMapService.ExploreMapEnabled)
				return;

			foreach (var actor in world.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null)
				.Where(a => Info.ExploredMapResourceObjectiveTypes.Contains(a.Info.Name))
				.OrderBy(a => a.ActorID))
				exploredMapResourceObjectiveCells.Add(actor.Location);

			if (exploredMapResourceObjectiveCells.Count > 0)
				FransBotLog.BotDebug(world,
					"{0}: Explore Map static resource knowledge seeds {1} mine/gmine expansion objective(s); MCV planning may target their map-start coordinates even before a current ore patch is large enough for ResourceMap indexing.",
					player, exploredMapResourceObjectiveCells.Count);
		}

		IEnumerable<CPos> EnumerateExpansionObjectiveCenters()
		{
			var seen = new List<CPos>();
			for (var i = 0; i < resourceMapModule.GetIndicesLength(); i++)
			{
				var indice = resourceMapModule.GetIndice(i);
				if (indice.ResourceCellsCount < Info.MinimumResourceCells)
					continue;

				var center = indice.ResourceCellsCenter;
				if (!world.Map.Contains(center))
					continue;

				seen.Add(center);
				yield return center;
			}

			if (exploredMapResourceObjectiveCells.Count == 0)
				yield break;

			var radiusSquared = Info.ExploredMapResourceObjectiveRadius * Info.ExploredMapResourceObjectiveRadius;
			foreach (var center in exploredMapResourceObjectiveCells.OrderBy(c => c.X).ThenBy(c => c.Y))
			{
				if (!world.Map.Contains(center) || seen.Any(c => (c - center).LengthSquared <= radiusSquared))
					continue;

				seen.Add(center);
				yield return center;
			}
		}

		OreChoice? FindNearestSafeOreField(Actor mcv, Mobile mobile,
			CPos? excludedResourceCenter = null, CPos? secondExcludedResourceCenter = null, bool logChoice = true,
			CPos? minimumSeparationFrom = null, int minimumSeparationCells = 0, bool allowMapWideFallback = true,
			McvObjectiveScanPerf perf = null)
		{
			var transformsInfo = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null)
				return null;

			var intoActor = world.Map.Rules.Actors[transformsInfo.IntoActor];
			var buildingInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return null;

			var serviceTypes = Info.ExpansionRefineryTypes;
			var ownServiceStructures = world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && serviceTypes.Contains(a.Info.Name))
				.ToArray();

			var ownCoverageStructures = world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player &&
					Info.ExistingBaseCoverageTypes.Contains(a.Info.Name))
				.ToArray();

			var maximumHopDistanceSquared = Info.MaximumExpansionHopDistance * Info.MaximumExpansionHopDistance;
			var fallbackDistanceSquared = Info.FallbackMaximumExpansionHopDistance > 0
				? (long)Info.FallbackMaximumExpansionHopDistance * Info.FallbackMaximumExpansionHopDistance
				: long.MaxValue;

			combatIntelService.EnsureCurrentSnapshot();
			var candidates = new List<OreFieldCandidate>();
			foreach (var resourceCenter in EnumerateExpansionObjectiveCenters())
			{
				if (perf != null)
					perf.ResourceNodesEnumerated++;
				if (activePioneerObjective.HasValue && resourceCenter != activePioneerObjective.Value)
					continue;
				if (!world.Map.Contains(resourceCenter) || IsFieldTemporarilyFailed(resourceCenter) || IsExpansionCandidateBlockedBeforeSelection(resourceCenter))
					continue;
				if ((excludedResourceCenter.HasValue && resourceCenter == excludedResourceCenter.Value) ||
					(secondExcludedResourceCenter.HasValue && resourceCenter == secondExcludedResourceCenter.Value))
					continue;

				if (minimumSeparationFrom.HasValue && minimumSeparationCells > 0 &&
					(resourceCenter - minimumSeparationFrom.Value).LengthSquared < minimumSeparationCells * minimumSeparationCells)
					continue;

				if (IsFieldServiced(resourceCenter, ownServiceStructures, ownCoverageStructures) ||
					IsMcvCriticalRisk(mcv, resourceCenter, CurrentMcvRiskTolerance))
					continue;

				var distanceSquared = (resourceCenter - mcv.Location).LengthSquared;
				if (distanceSquared > fallbackDistanceSquared)
					continue;

				candidates.Add(new OreFieldCandidate(resourceCenter, distanceSquared));
			}
			if (perf != null)
				perf.CandidateNodesRetained = candidates.Count;

			// PIONEER target choice is intentionally simple. Nearest objective wins;
			// RiskModel/path legality may veto it, but known/secured/explored status never grants
			// a score bonus that can pull the MCV past a nearer ore. Unknown nearest objectives
			// return normally so RequiresPioneerReconBeforeCommit() can hold exactly that target.
			IOrderedEnumerable<OreFieldCandidate> OrderOreCandidates(IEnumerable<OreFieldCandidate> source) => source
				.OrderBy(c => c.DistanceSquared)
				.ThenBy(c => c.ResourceCenter.X)
				.ThenBy(c => c.ResourceCenter.Y);

			var localCandidates = OrderOreCandidates(candidates
				.Where(c => c.DistanceSquared <= maximumHopDistanceSquared))
				.Take(Info.MaximumOreFieldPathCandidates).ToArray();
			var fallbackCandidates = allowMapWideFallback
				? OrderOreCandidates(candidates.Where(c => c.DistanceSquared > maximumHopDistanceSquared))
					.Take(Info.FallbackMaximumOreFieldPathCandidates).ToArray()
				: [];
			var plannedCandidates = localCandidates.Select(candidate => new RoutineLandPlannedCandidate(candidate, "local"))
				.Concat(fallbackCandidates.Select(candidate => new RoutineLandPlannedCandidate(candidate, "fallback")))
				.ToArray();
			var routineLandUnion = new RoutineLandNegativeUnionScanState(mcv, mobile, mobile.ToCell,
				world.WorldTick, riskModelService?.RiskRevision ?? -1,
				strategicMapService?.TerrainKnowledgeVersion ?? -1, plannedCandidates, perf);

			var local = EvaluateOreCandidates(mcv, mobile, transformsInfo, intoActor, buildingInfo,
				localCandidates, "local", 0, routineLandUnion, perf);
			if (local.HasValue)
			{
				if (logChoice)
					FransBotLog.BotDebug(world,
						"{0}: NEAREST-FIRST local ore for {1} is {2}, path length {3}, destination risk {4}; scout/SECURE permission is checked only after this nearest target is chosen.",
						player, mcv, local.Value.ResourceCenter, local.Value.PathLength, local.Value.RiskScore);
				return local;
			}

			if (allowMapWideFallback)
			{
				var distant = EvaluateOreCandidates(mcv, mobile, transformsInfo, intoActor, buildingInfo,
					fallbackCandidates, "fallback", localCandidates.Length, routineLandUnion, perf);
				if (distant.HasValue)
				{
					if (logChoice)
						FransBotLog.BotDebug(world,
							"{0}: no viable local ore within {1} cells; NEAREST-FIRST fallback for {2} is {3}, path length {4}, destination risk {5}.",
							player, Info.MaximumExpansionHopDistance, mcv, distant.Value.ResourceCenter, distant.Value.PathLength, distant.Value.RiskScore);
					return distant;
				}
			}

			if (logChoice && world.WorldTick >= nextNoOreStatusLogTick)
			{
				nextNoOreStatusLogTick = world.WorldTick + 500;
				FransBotLog.BotDebug(world,
					"{0}: expansion MCV {1} found no safe reachable uncovered ore field by land; amphibious planning may be required.",
					player, mcv);
			}

			return null;
		}


		SeaTargetChoice? FindNearestRoutineSeaOreField(Actor mcv, Mobile mobile, bool allowMapWideFallback = true)
		{
			return FindNearestRoutineSeaOreField(mcv, mobile, out _, allowMapWideFallback);
		}

		SeaTargetChoice? FindNearestRoutineSeaOreField(Actor mcv, Mobile mobile, out bool searchPending,
			bool allowMapWideFallback = true, McvObjectiveScanPerf perf = null)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "MCV.FindSeaOre");
			searchPending = false;
			if (mcv == null || mobile == null || mcv.Disposed || !mcv.IsInWorld || mcv.IsDead)
			{
				routineSeaOreSearch = null;
				return null;
			}

			var transformsInfo = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null ||
				!world.Map.Rules.Actors.TryGetValue(transformsInfo.IntoActor, out var intoActor))
				return null;

			var buildingInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return null;

			var movementToleranceSquared = Info.RoutineSeaOreSearchMovementTolerance * Info.RoutineSeaOreSearchMovementTolerance;
			var riskRevision = riskModelService?.RiskRevision ?? -1;
			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			var stateMatches = routineSeaOreSearch != null && routineSeaOreSearch.McvActorId == mcv.ActorID &&
				routineSeaOreSearch.TerrainKnowledgeVersion == terrainVersion &&
				routineSeaOreSearch.AllowMapWideFallback == allowMapWideFallback &&
				(mcv.Location - routineSeaOreSearch.McvCell).LengthSquared <= movementToleranceSquared;

			if (stateMatches && routineSeaOreSearch.Complete &&
				world.WorldTick - routineSeaOreSearch.CompletedTick < Info.RoutineSeaOreSearchCacheDuration)
			{
				var completed = routineSeaOreSearch.Result;
				if (!completed.HasValue && routineSeaOreSearch.CompletedRiskRevision == riskRevision)
					return null;
				if (!completed.HasValue)
				{
					routineSeaOreSearch = null;
					stateMatches = false;
				}
				else
				{
					var pickup = routineSeaPickupProof;
					var evidenceCurrent = pickup?.Success == true &&
						pickup.McvActorId == mcv.ActorID && pickup.McvCell == mobile.ToCell &&
						IsPioneerPathEvidenceCurrent(mcv, mobile, pickup.McvCell, pickup.McvCell,
							pickup.ResultMcvCell, pickup.ResultPath) &&
						routineSeaOreSearch.SuccessfulLandingPath.Length > 0 &&
						IsPioneerPathEvidenceCurrent(mcv, mobile, routineSeaOreSearch.McvCell,
							routineSeaOreSearch.SuccessfulLandingExitCell, completed.Value.DeployCell,
							routineSeaOreSearch.SuccessfulLandingPath) &&
						TryProveFutureExpansionRefineryPlacement(mcv, completed.Value.DeployCell, out _, out _);
					if (evidenceCurrent)
						return completed;

					routineSeaOreSearch = null;
					stateMatches = false;
				}
			}

			if (!stateMatches || routineSeaOreSearch.Complete)
			{
				Actor[] ownServiceStructures;
				Actor[] ownCoverageStructures;
				OreFieldCandidate[] orderedCandidates;
				using (FransBotLog.Profile(world, player, "MCV.SeaOreCandidateSnapshot"))
				{
					ownServiceStructures = world.ActorsHavingTrait<Building>()
						.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player &&
							Info.ExpansionRefineryTypes.Contains(a.Info.Name))
						.ToArray();
					ownCoverageStructures = world.ActorsHavingTrait<Building>()
						.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player &&
							Info.ExistingBaseCoverageTypes.Contains(a.Info.Name))
						.ToArray();

					var maximumHopDistanceSquared = (long)Info.MaximumExpansionHopDistance * Info.MaximumExpansionHopDistance;
					var fallbackDistanceSquared = Info.FallbackMaximumExpansionHopDistance > 0
						? (long)Info.FallbackMaximumExpansionHopDistance * Info.FallbackMaximumExpansionHopDistance
						: long.MaxValue;

					combatIntelService.EnsureCurrentSnapshot();
					var candidates = new List<OreFieldCandidate>();
					foreach (var center in EnumerateExpansionObjectiveCenters())
					{
						if (perf != null)
							perf.ResourceNodesEnumerated++;
						if (activePioneerObjective.HasValue && center != activePioneerObjective.Value)
							continue;
						if (!world.Map.Contains(center) || IsFieldTemporarilyFailed(center) || IsExpansionCandidateBlockedBeforeSelection(center) ||
							IsFieldServiced(center, ownServiceStructures, ownCoverageStructures) ||
							IsMcvCriticalRisk(mcv, center, CurrentMcvRiskTolerance) ||
							!HasNearbyShore(center, Info.SeaLandingSearchRadius))
							continue;

						var distanceSquared = (center - mcv.Location).LengthSquared;
						if (distanceSquared > fallbackDistanceSquared)
							continue;
						candidates.Add(new OreFieldCandidate(center, distanceSquared));
					}

					// Match land PIONEER semantics: an executable objective anywhere in the normal
					// candidate horizon outranks an unknown objective that merely needs RECON.
					// Keep the same bounded candidate budget as before (local + optional fallback).
					var candidateBudget = Info.MaximumSeaOreFieldCandidates * (allowMapWideFallback ? 2 : 1);
					orderedCandidates = candidates
						.Where(c => allowMapWideFallback || c.DistanceSquared <= maximumHopDistanceSquared)
						.OrderBy(c => c.DistanceSquared > maximumHopDistanceSquared)
						.ThenBy(c => c.DistanceSquared)
						.ThenBy(c => c.ResourceCenter.X)
						.ThenBy(c => c.ResourceCenter.Y)
						.Take(candidateBudget)
						.ToArray();
					if (perf != null)
						perf.CandidateNodesRetained = orderedCandidates.Length;
				}

				if (orderedCandidates.Length == 0)
				{
						routineSeaOreSearch = new RoutineSeaOreSearchState(mcv.ActorID, mcv.Location,
							strategicMapService?.TerrainKnowledgeVersion ?? -1, allowMapWideFallback, []);
						routineSeaOreSearch.Complete = true;
						routineSeaOreSearch.CompletedRiskRevision = riskRevision;
						routineSeaOreSearch.CompletedTick = world.WorldTick;
					return null;
				}

				routineSeaOreSearch = new RoutineSeaOreSearchState(mcv.ActorID, mcv.Location,
					terrainVersion, allowMapWideFallback, orderedCandidates);
			}
			if (perf != null && routineSeaOreSearch != null && perf.CandidateNodesRetained == 0)
				perf.CandidateNodesRetained = routineSeaOreSearch.Candidates.Length;

			// Reuse the retained positive pickup path after cheap exact evidence validation.
			// Risk/terrain/source changes reset only this pickup proof, while an unchanged path
			// avoids repeating native A* during the incremental landing search.
			{
				bool pickupFound;
				bool pickupSearchExhausted;
				using (FransBotLog.Profile(world, player, "MCV.SeaOrePickupProof"))
					pickupFound = TryAdvanceReachableRoutineSeaPickupProof(mcv, mobile,
						out _, out _, out _, out pickupSearchExhausted, perf);
				if (!pickupFound || !TryGetPreferredRoutinePickupNavalRegion(out _))
				{
					routineSeaOreSearch.PickupProven = false;
					if (!pickupSearchExhausted)
					{
						searchPending = true;
						return null;
					}

					routineSeaOreSearch.Complete = true;
					routineSeaOreSearch.CompletedRiskRevision = riskRevision;
					routineSeaOreSearch.CompletedTick = world.WorldTick;
					return null;
				}

				routineSeaOreSearch.PickupProven = true;
			}

			Actor[] landingProtectors;
			using (FransBotLog.Profile(world, player, "MCV.SeaOreProtectorSnapshot"))
				landingProtectors = GetOwnedSeaLandingProtectors();
			var budget = Math.Max(1, Info.RoutineSeaOreCandidatesPerPlanningPass);
			for (var processed = 0; processed < budget && routineSeaOreSearch.NextCandidateIndex < routineSeaOreSearch.Candidates.Length; processed++)
			{
				var candidate = routineSeaOreSearch.Candidates[routineSeaOreSearch.NextCandidateIndex];
				if (perf != null)
					perf.NodesEvaluated++;

				var mutableCandidateRejected = false;
				using (FransBotLog.Profile(world, player, "MCV.SeaOreMutableCandidateGates"))
					mutableCandidateRejected = IsFieldTemporarilyFailed(candidate.ResourceCenter) ||
						IsExpansionCandidateBlockedBeforeSelection(candidate.ResourceCenter) ||
						IsMcvCriticalRisk(mcv, candidate.ResourceCenter, CurrentMcvRiskTolerance);
				if (mutableCandidateRejected)
				{
					LogMcvTarget(mcv, candidate.ResourceCenter, false, "SeaCandidateMutableGateRejected");
					routineSeaOreSearch.LandingProof = null;
					routineSeaOreSearch.NextCandidateIndex++;
					continue;
				}

				var activeLandingProof = routineSeaOreSearch.LandingProof;
				var continuingLandingProof = activeLandingProof != null &&
					activeLandingProof.ResourceCenter == candidate.ResourceCenter;
				if (!continuingLandingProof)
				{
					using (FransBotLog.Profile(world, player, "MCV.SeaOreLandProof"))
						if (TryFindSafeDeployPath(mcv, mobile, candidate.ResourceCenter,
							transformsInfo, intoActor, buildingInfo, out var landDeploy, out var landPathLength,
							perf, candidate.ResourceCenter) &&
							IsMcvRouteDetourAcceptable(mobile.ToCell, landDeploy, landPathLength))
						{
							LogMcvTarget(mcv, candidate.ResourceCenter, false, "LandRouteAlreadyExecutable", landDeploy, pathLength: landPathLength);
							routineSeaOreSearch.LandingProof = null;
							routineSeaOreSearch.NextCandidateIndex++;
							continue;
						}
				}

				var pickupNavalRegion = continuingLandingProof
					? activeLandingProof.PickupNavalRegion
					: -1;
				if (!continuingLandingProof && !TryGetPreferredRoutinePickupNavalRegion(out pickupNavalRegion))
				{
					LogMcvTarget(mcv, candidate.ResourceCenter, false, "NoReachablePickupNavalRegion");
					routineSeaOreSearch.LandingProof = null;
					routineSeaOreSearch.NextCandidateIndex++;
					continue;
				}
				if (IsSeaTopologyFailureCached(candidate.ResourceCenter, pickupNavalRegion) ||
					IsSeaLandingProofFailureCached(candidate.ResourceCenter, pickupNavalRegion))
				{
					LogMcvTarget(mcv, candidate.ResourceCenter, false, "CachedSeaTopologyOrLandingFailure");
					routineSeaOreSearch.LandingProof = null;
					routineSeaOreSearch.NextCandidateIndex++;
					continue;
				}
				if (!HasKnownLandingShoreInNavalRegion(candidate.ResourceCenter, pickupNavalRegion))
				{
					RememberSeaTopologyFailure(candidate.ResourceCenter, pickupNavalRegion,
						"no native-passable landing handoff belongs to the MCV pickup naval region");
					LogMcvTarget(mcv, candidate.ResourceCenter, false, "NoLandingShoreInPickupNavalRegion");
					routineSeaOreSearch.LandingProof = null;
					routineSeaOreSearch.NextCandidateIndex++;
					continue;
				}

				using (FransBotLog.Profile(world, player, "MCV.SeaOreLandingProof"))
				{
					if (TryAdvanceRoutineSeaLandingProof(routineSeaOreSearch, mcv, mobile, candidate.ResourceCenter,
						transformsInfo, intoActor, buildingInfo, pickupNavalRegion, landingProtectors,
						out var landingCraftCell, out var deployCell, out var exhausted,
						out var landingExitCell, out var landingPath, perf))
					{
						if (IsFutureRefineryProofCooling(candidate.ResourceCenter))
						{
							LogMcvTarget(mcv, candidate.ResourceCenter, false, "SeaFutureRefineryProofCooldown", deployCell);
							routineSeaOreSearch.LandingProof = null;
							routineSeaOreSearch.NextCandidateIndex++;
							continue;
						}
						if (!TryProveFutureExpansionRefineryPlacement(mcv, deployCell, out _, out _))
						{
							RememberFutureRefineryProofFailure(candidate.ResourceCenter);
							LogMcvTarget(mcv, candidate.ResourceCenter, false, "SeaNoFutureRefineryPlacement", deployCell);
							routineSeaOreSearch.LandingProof = null;
							routineSeaOreSearch.NextCandidateIndex++;
							continue;
						}

						routineSeaOreSearch.Result = new SeaTargetChoice(candidate.ResourceCenter, deployCell, landingCraftCell, candidate.DistanceSquared);
						routineSeaOreSearch.SuccessfulLandingExitCell = landingExitCell;
						routineSeaOreSearch.SuccessfulLandingPath = landingPath;
						if (perf != null)
							perf.AcceptedNativeProofIndex = perf.LastSuccessfulNativeProofIndex;
						routineSeaOreSearch.Complete = true;
						routineSeaOreSearch.CompletedRiskRevision = riskRevision;
						routineSeaOreSearch.CompletedTick = world.WorldTick;
						LogMcvTarget(mcv, candidate.ResourceCenter, true, "AcceptedSeaTarget", deployCell);
						return routineSeaOreSearch.Result;
					}

					if (!exhausted)
					{
						searchPending = true;
						return null;
					}

					RememberSeaLandingProofFailure(candidate.ResourceCenter, pickupNavalRegion);
					LogMcvTarget(mcv, candidate.ResourceCenter, false, "SeaLandingProofExhausted");
					routineSeaOreSearch.LandingProof = null;
					routineSeaOreSearch.NextCandidateIndex++;
				}
			}

			if (routineSeaOreSearch.NextCandidateIndex >= routineSeaOreSearch.Candidates.Length)
			{
				routineSeaOreSearch.Complete = true;
				routineSeaOreSearch.CompletedRiskRevision = riskRevision;
				routineSeaOreSearch.CompletedTick = world.WorldTick;
				return null;
			}

			searchPending = true;
			return null;
		}

		bool TryAdvanceRoutineSeaLandingProof(RoutineSeaOreSearchState search, Actor mcv, Mobile mcvMobile, CPos resourceCenter,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo, int pickupNavalRegion,
			IReadOnlyCollection<Actor> landingProtectors, out CPos landingCraftCell, out CPos deployCell, out bool exhausted,
			McvObjectiveScanPerf perf = null, IReadOnlyCollection<CPos> excludedLandingCraftCells = null)
		{
			return TryAdvanceRoutineSeaLandingProof(search, mcv, mcvMobile, resourceCenter,
				transformsInfo, intoActor, buildingInfo, pickupNavalRegion, landingProtectors,
				out landingCraftCell, out deployCell, out exhausted, out _, out _, perf, excludedLandingCraftCells);
		}

		bool TryAdvanceRoutineSeaLandingProof(RoutineSeaOreSearchState search, Actor mcv, Mobile mcvMobile, CPos resourceCenter,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo, int pickupNavalRegion,
			IReadOnlyCollection<Actor> landingProtectors, out CPos landingCraftCell, out CPos deployCell, out bool exhausted,
			out CPos provenExitCell, out CPos[] provenLandPath,
			McvObjectiveScanPerf perf = null, IReadOnlyCollection<CPos> excludedLandingCraftCells = null)
		{
			landingCraftCell = default;
			deployCell = default;
			exhausted = false;
			provenExitCell = default;
			provenLandPath = [];

			var currentRiskRevision = riskModelService?.RiskRevision ?? -1;
			var proof = search?.LandingProof;
			if (proof == null || proof.ResourceCenter != resourceCenter || proof.PickupNavalRegion != pickupNavalRegion ||
				proof.RiskRevision != currentRiskRevision)
			{
				CPos[] deployCandidates;
				using (FransBotLog.Profile(world, player, "MCV.SeaOreDeployCandidates"))
					deployCandidates = GetSafeDeployCandidates(mcv, mcvMobile, resourceCenter, transformsInfo, intoActor, buildingInfo, perf);
				if (deployCandidates.Length == 0)
				{
					exhausted = true;
					return false;
				}

				Dictionary<(int X, int Y), List<Actor>> protectorBuckets;
				using (FransBotLog.Profile(world, player, "MCV.SeaOreProtectorBuckets"))
					protectorBuckets = BuildSeaLandingProtectorBuckets(landingProtectors);
				CPos[] rankedBeaches;
				using (FransBotLog.Profile(world, player, "MCV.SeaOreHandoffRanking"))
					rankedBeaches = AmphibiousHandoffCellsNear(resourceCenter, Info.SeaLandingSearchRadius)
						.Where(c => IsCellInNavalRegion(c, pickupNavalRegion))
						.Where(c => excludedLandingCraftCells == null || !excludedLandingCraftCells.Contains(c))
						.OrderByDescending(c => CountSeaLandingProtectorsNear(c, landingProtectors, protectorBuckets))
						.ThenBy(c => (c - resourceCenter).LengthSquared)
						.Take(Info.MaximumLandingBeachCandidates)
						.ToArray();
				if (rankedBeaches.Length == 0)
				{
					exhausted = true;
					return false;
				}

				proof = new RoutineSeaLandingProofState
				{
					ResourceCenter = resourceCenter,
					PickupNavalRegion = pickupNavalRegion,
					RiskRevision = currentRiskRevision,
					DeployCandidates = deployCandidates,
					RankedBeaches = rankedBeaches,
					NextBeachIndex = 0
				};
				search.LandingProof = proof;
			}

			var beachBudget = Math.Max(1, Info.RoutineSeaOreLandingBeachesPerPlanningPass);
			var exitProofBudget = Math.Max(1, Info.RoutineSeaOreExitPathProofsPerPlanningPass);
			var beachesAdvanced = 0;
			var expensiveProofs = 0;

			while (expensiveProofs < exitProofBudget)
			{
				if (!proof.ActiveBeach.HasValue)
				{
					if (beachesAdvanced >= beachBudget || proof.NextBeachIndex >= proof.RankedBeaches.Length)
						break;

					var beach = proof.RankedBeaches[proof.NextBeachIndex++];
					beachesAdvanced++;
					proof.ActiveBeach = beach;
					using (FransBotLog.Profile(world, player, "MCV.SeaOreExitCellEnumeration"))
						proof.ActiveExitCells = PassengerAdjacentCells(beach)
							.Where(c => strategicMapService.IsAmphibiousHandoff(c, beach))
							.Where(c => mcvMobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mcvMobile.CanStayInCell(c))
							.OrderBy(c => (c - resourceCenter).LengthSquared)
							.ToArray();
					proof.NextExitIndex = 0;
				}

				if (proof.NextExitIndex >= proof.ActiveExitCells.Length)
				{
					proof.ActiveBeach = null;
					proof.ActiveExitCells = [];
					proof.NextExitIndex = 0;
					continue;
				}

				var exitCell = proof.ActiveExitCells[proof.NextExitIndex++];
				if (!proof.ExitPathProofs.TryGetValue(exitCell, out var exitProof))
				{
					bool success;
					CPos provenDeployCell;
					int provenLandPathLength;
					CPos[] path;
					using (FransBotLog.Profile(world, player, "MCV.SeaOreExitPathProof"))
						success = TryFindSafeDeployPathFromCellUsingCandidates(mcv, mcvMobile, exitCell,
							proof.DeployCandidates, out provenDeployCell, out provenLandPathLength, out path, perf, resourceCenter);
					exitProof = new LandingExitProof(success, provenDeployCell, provenLandPathLength, path);
					proof.ExitPathProofs.Add(exitCell, exitProof);
					expensiveProofs++;
				}

				if (!exitProof.Success)
					continue;

				landingCraftCell = proof.ActiveBeach.Value;
				deployCell = exitProof.DeployCell;
				provenExitCell = exitCell;
				provenLandPath = exitProof.Path;
				return true;
			}

			exhausted = proof.NextBeachIndex >= proof.RankedBeaches.Length &&
				(!proof.ActiveBeach.HasValue || proof.NextExitIndex >= proof.ActiveExitCells.Length);
			return false;
		}

		bool ShouldPreferRoutineSeaTarget(Actor mcv, OreChoice landChoice, SeaTargetChoice seaChoice)
		{
			// transport method does not change strategic objective ranking. The nearest
			// physically viable ore wins; land/sea only decides how the same PIONEER role gets there.
			var landDistanceSquared = (landChoice.ResourceCenter - mcv.Location).LengthSquared;
			if (seaChoice.DistanceSquared != landDistanceSquared)
				return seaChoice.DistanceSquared < landDistanceSquared;

			if (seaChoice.ResourceCenter.X != landChoice.ResourceCenter.X)
				return seaChoice.ResourceCenter.X < landChoice.ResourceCenter.X;
			return seaChoice.ResourceCenter.Y < landChoice.ResourceCenter.Y;
		}

		IReadOnlyList<CPos> RoutinePickupHandoffCells()
		{
			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			if (cachedRoutinePickupHandoffCells != null &&
				cachedRoutinePickupHandoffTerrainVersion == terrainVersion)
				return cachedRoutinePickupHandoffCells;

			// StrategicMap owns the fair-known native locomotor handoff graph. Cache only
			// its current version; progressive exploration may legitimately add cells.
			cachedRoutinePickupHandoffCells = strategicMapService?.AmphibiousHandoffs
				.Select(access => access.NavalCell)
				.Distinct()
				.OrderBy(c => c.X)
				.ThenBy(c => c.Y)
				.ToArray() ?? [];
			cachedRoutinePickupHandoffTerrainVersion = terrainVersion;
			FransBotLog.BotDebug(world,
				"{0}: ROUTINE FERRY native-passable handoff cache rebuilt for terrain version {1}: {2} LST-side cell(s). Replans reuse StrategicMap topology without scanning terrain labels.",
				player, terrainVersion, cachedRoutinePickupHandoffCells.Length);
			return cachedRoutinePickupHandoffCells;
		}

		CPos[] RankRoutinePickupHandoffs(CPos origin, CPos? excluded = null, int? maximum = null)
		{
			var limit = Math.Max(1, maximum ?? Info.MaximumRoutinePickupBeachCandidates);
			var ranked = new List<CPos>(limit);
			foreach (var cell in RoutinePickupHandoffCells())
			{
				if (excluded.HasValue && cell == excluded.Value)
					continue;

				var insertAt = 0;
				while (insertAt < ranked.Count)
				{
					var existing = ranked[insertAt];
					var distanceOrder = (cell - origin).LengthSquared.CompareTo((existing - origin).LengthSquared);
					if (distanceOrder < 0 || (distanceOrder == 0 &&
						(cell.X < existing.X || (cell.X == existing.X && cell.Y < existing.Y))))
						break;
					insertAt++;
				}

				if (insertAt >= limit)
					continue;
				ranked.Insert(insertAt, cell);
				if (ranked.Count > limit)
					ranked.RemoveAt(limit);
			}

			return ranked.ToArray();
		}

		bool TryUsePreferredRoutinePickup(Actor mcv, Mobile mcvMobile, Actor craft, Mobile craftMobile,
			out CPos mcvCell, out CPos craftCell)
		{
			return TryUsePreferredRoutinePickup(mcv, mcvMobile, craft, craftMobile,
				out mcvCell, out craftCell, out _);
		}

		bool TryUsePreferredRoutinePickup(Actor mcv, Mobile mcvMobile, Actor craft, Mobile craftMobile,
			out CPos mcvCell, out CPos craftCell, out CPos[] mcvPath)
		{
			mcvCell = default;
			craftCell = default;
			mcvPath = [];
			if (!preferredRoutinePickupMcvCell.HasValue || !preferredRoutinePickupCraftCell.HasValue)
				return false;

			var landCell = preferredRoutinePickupMcvCell.Value;
			var beach = preferredRoutinePickupCraftCell.Value;
			if (!world.Map.Contains(landCell) || !world.Map.Contains(beach) ||
				strategicMapService == null || !strategicMapService.IsAmphibiousHandoff(landCell, beach) ||
				!mcvMobile.CanEnterCell(landCell, check: BlockedByActor.Immovable) || !mcvMobile.CanStayInCell(landCell) ||
				!HasRiskAwarePathBetweenCells(mcv, mcvMobile, mcvMobile.ToCell, landCell, out _, out mcvPath))
				return false;

			if (craft != null)
			{
				if (craftMobile == null || !craftMobile.CanEnterCell(beach, check: BlockedByActor.Immovable) ||
					!craftMobile.CanStayInCell(beach) ||
					!TryFindNavalTransportPath(craft, craftMobile, craftMobile.ToCell, beach, out _, out _))
					return false;
			}

			mcvCell = landCell;
			craftCell = beach;
			return true;
		}

		bool TryFindRiskAwarePathToAnyCell(Actor actor, Mobile mobile, CPos source, CPos[] targets,
			out CPos target, out CPos[] provenPath, out bool nativeSearchExecuted,
			RoutineSeaPickupProofState pickupProof = null, McvObjectiveScanPerf perf = null)
		{
			target = default;
			provenPath = [];
			nativeSearchExecuted = false;
			if (actor == null || mobile == null || targets == null || targets.Length == 0)
				return false;

			if (targets.Contains(source))
			{
				target = source;
				provenPath = [source];
				return true;
			}
			if (mobile.PathFinder is not PathFinder pathFinder)
				return false;

			var started = Stopwatch.GetTimestamp();
			RoutineLandNativePathResult nativeResult;
			using (FransBotLog.Profile(world, player, "MCV.SeaPickupNativePath"))
				nativeResult = RoutineLandNativePathInvoker.FindPathToTargetCells(
					actor, pathFinder, source, targets,
					search => riskModelService.ExecuteWithPreparedPathCost(actor,
						FransRiskRole.Mcv, CurrentMcvRiskTolerance, search));
			var elapsedMs = ElapsedMilliseconds(started);
			nativeSearchExecuted = true;
			if (pickupProof != null)
			{
				pickupProof.NativeSearches++;
				pickupProof.NativeTargetCells += targets.Length;
				pickupProof.NativePathCostCallbacks += nativeResult.PathCostCallbacks;
				pickupProof.NativeElapsedMs += elapsedMs;
				pickupProof.LastPassNativeSearches++;
				pickupProof.LastPassTargetCells += targets.Length;
				pickupProof.LastPassPathCostCallbacks += nativeResult.PathCostCallbacks;
				pickupProof.LastPassElapsedMs += elapsedMs;
			}
			if (perf != null)
			{
				perf.LogicalNativeProofRequests++;
				perf.PhysicalNativePathSearches++;
				perf.NativeTargetCells += targets.Length;
				perf.NativePathCostCallbackCalls += nativeResult.PathCostCallbacks;
				perf.RiskPathCostCalls += nativeResult.RiskPathCostCalls;
				perf.NativePathSearchElapsedMs += elapsedMs;
				if (elapsedMs > perf.MaxNativePathSearchElapsedMs)
				{
					perf.MaxNativePathSearchElapsedMs = elapsedMs;
					perf.MaxNativeTargetCells = targets.Length;
					perf.MaxNativePathSearchCallbackCalls = nativeResult.PathCostCallbacks;
				}
				perf.Pass.RecordPhysicalProof(perf, actor, source, targets);
			}

			var path = nativeResult.Path;
			if (path == null || path.Count == 0 || !targets.Contains(path[0]))
				return false;
			for (var p = 0; p < path.Count - 1; p++)
			{
				if (perf != null)
					perf.PostPathRiskChecks++;
				if (IsMcvCriticalRisk(actor, path[p], CurrentMcvRiskTolerance))
					return false;
			}

			target = path[0];
			provenPath = path.ToArray();
			return true;
		}

		bool TryAdvanceReachableRoutineSeaPickupProof(Actor mcv, Mobile mcvMobile,
			out CPos mcvCell, out CPos craftCell, out CPos[] mcvPath, out bool exhausted,
			McvObjectiveScanPerf perf = null)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "MCV.SeaPickupSearch");
			mcvCell = default;
			craftCell = default;
			mcvPath = [];
			exhausted = false;
			if (mcv == null || mcvMobile == null)
			{
				exhausted = true;
				return false;
			}

			var riskRevision = riskModelService?.RiskRevision ?? -1;
			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			var stateMatches = routineSeaPickupProof != null && routineSeaPickupProof.McvActorId == mcv.ActorID &&
				routineSeaPickupProof.RiskRevision == riskRevision &&
				routineSeaPickupProof.TerrainKnowledgeVersion == terrainVersion &&
				mcvMobile.ToCell == routineSeaPickupProof.McvCell;
			if (!stateMatches)
				routineSeaPickupProof = new RoutineSeaPickupProofState(mcv.ActorID, mcvMobile.ToCell,
					riskRevision, terrainVersion, preferredRoutinePickupMcvCell, preferredRoutinePickupCraftCell,
					RankRoutinePickupHandoffs(mcvMobile.ToCell), world.WorldTick);

			var proof = routineSeaPickupProof;
			proof.LastPassNativeSearches = 0;
			proof.LastPassTargetCells = 0;
			proof.LastPassPathCostCallbacks = 0;
			proof.LastPassElapsedMs = 0;
			if (proof.Success)
			{
				var resultStillCurrent = world.Map.Contains(proof.ResultCraftCell) &&
					strategicMapService != null &&
					strategicMapService.IsAmphibiousHandoff(proof.ResultMcvCell, proof.ResultCraftCell) &&
					strategicMapService.TryGetNavalRegionId(proof.ResultCraftCell, out _) &&
					IsPioneerPathEvidenceCurrent(mcv, mcvMobile, proof.McvCell, proof.McvCell,
						proof.ResultMcvCell, proof.ResultPath);
				if (resultStillCurrent)
				{
					mcvCell = proof.ResultMcvCell;
					craftCell = proof.ResultCraftCell;
					mcvPath = proof.ResultPath;
					return true;
				}

				proof.Success = false;
				proof.ResultPath = [];
			}
			if (proof.Complete)
			{
				exhausted = true;
				return false;
			}

			var nativeBudget = Math.Max(1, Info.SeaPickupPathProofsPerPlanningPass);
			var nativeSearches = 0;
			while (nativeSearches < nativeBudget)
			{
				CPos beach;
				CPos[] targets;
				if (!proof.PreferredAttempted)
				{
					proof.PreferredAttempted = true;
					if (!proof.PreferredMcvCell.HasValue || !proof.PreferredCraftCell.HasValue)
						continue;
					beach = proof.PreferredCraftCell.Value;
					var preferred = proof.PreferredMcvCell.Value;
					if (!world.Map.Contains(preferred) || !world.Map.Contains(beach) || strategicMapService == null ||
						!strategicMapService.IsAmphibiousHandoff(preferred, beach) ||
						!strategicMapService.TryGetNavalRegionId(beach, out _) ||
						!mcvMobile.CanEnterCell(preferred, check: BlockedByActor.Immovable) || !mcvMobile.CanStayInCell(preferred))
						continue;
					targets = [preferred];
				}
				else
				{
					if (proof.NextBeachIndex >= proof.RankedBeaches.Length)
					{
						proof.Complete = true;
						exhausted = true;
						return false;
					}

					beach = proof.RankedBeaches[proof.NextBeachIndex++];
					if (strategicMapService == null || !strategicMapService.TryGetNavalRegionId(beach, out _))
						continue;
					targets = PassengerAdjacentCells(beach)
						.Where(cell => strategicMapService.IsAmphibiousHandoff(cell, beach))
						.Where(cell => mcvMobile.CanEnterCell(cell, check: BlockedByActor.Immovable) && mcvMobile.CanStayInCell(cell))
						.OrderBy(cell => (cell - mcvMobile.ToCell).LengthSquared)
						.ThenBy(cell => cell.X)
						.ThenBy(cell => cell.Y)
						.ToArray();
					if (targets.Length == 0)
						continue;
				}

				var found = TryFindRiskAwarePathToAnyCell(mcv, mcvMobile, mcvMobile.ToCell, targets,
					out var provenPickup, out var path, out var nativeSearchExecuted, proof, perf);
				if (nativeSearchExecuted)
					nativeSearches++;
				if (!found)
					continue;

				preferredRoutinePickupMcvCell = provenPickup;
				preferredRoutinePickupCraftCell = beach;
				proof.Success = true;
				proof.ResultMcvCell = provenPickup;
				proof.ResultCraftCell = beach;
				proof.ResultPath = path;
				mcvCell = provenPickup;
				craftCell = beach;
				mcvPath = path;
				return true;
			}

			return false;
		}


		bool IsCellInNavalRegion(CPos cell, int navalRegion)
		{
			return strategicMapService != null && world.Map.Contains(cell) &&
				strategicMapService.TryGetNavalRegionId(cell, out var region) && region == navalRegion;
		}

		bool HasKnownLandingShoreInNavalRegion(CPos resourceCenter, int navalRegion)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "MCV.SeaOreRegionalTopologyGate");
			return AmphibiousHandoffCellsNear(resourceCenter, Info.SeaLandingSearchRadius)
				.Any(cell => IsCellInNavalRegion(cell, navalRegion));
		}

		bool TryGetPreferredRoutinePickupNavalRegion(out int navalRegion)
		{
			navalRegion = -1;
			return preferredRoutinePickupCraftCell.HasValue && strategicMapService != null &&
				strategicMapService.TryGetNavalRegionId(preferredRoutinePickupCraftCell.Value, out navalRegion);
		}

		bool TryGetRequiredLandingCraftProductionRegion(out int navalRegion)
		{
			navalRegion = -1;
			if (coastalStagingForSeaExpansion && coastalStagingRequiredNavalRegion.HasValue)
			{
				navalRegion = coastalStagingRequiredNavalRegion.Value;
				return true;
			}

			return HasCommittedSeaExpansionDemand && TryGetPreferredRoutinePickupNavalRegion(out navalRegion);
		}

		bool IsLandingCraftInNavalRegion(Actor craft, int navalRegion)
		{
			if (!IsLiveOwnedLandingCraft(craft) || strategicMapService == null)
				return false;
			var mobile = craft.TraitOrDefault<Mobile>();
			var cell = mobile?.ToCell ?? craft.Location;
			return strategicMapService.TryGetNavalRegionId(cell, out var region) && region == navalRegion;
		}

		void RefreshSeaTopologyFailureCacheVersion()
		{
			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			if (seaTopologyFailureTerrainVersion == terrainVersion)
				return;

			seaTopologyFailures.Clear();
			seaLandingProofFailuresUntil.Clear();
			seaTopologyFailureTerrainVersion = terrainVersion;
		}

		bool IsSeaTopologyFailureCached(CPos objective, int pickupNavalRegion)
		{
			RefreshSeaTopologyFailureCacheVersion();
			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			return terrainVersion >= 0 &&
				seaTopologyFailures.Contains(new SeaTopologyFailureKey(objective, pickupNavalRegion, terrainVersion));
		}

		void RememberSeaTopologyFailure(CPos objective, int pickupNavalRegion, string reason)
		{
			RefreshSeaTopologyFailureCacheVersion();
			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			if (terrainVersion < 0)
				return;

			var key = new SeaTopologyFailureKey(objective, pickupNavalRegion, terrainVersion);
			if (!seaTopologyFailures.Add(key))
				return;

			FransBotLog.BotDebug(world,
				"{0}: MCV REGIONAL SEA topology-negative cache latches ore {1} from pickup naval region {2} for TerrainKnowledgeVersion {3}: {4}. The same source sea will not recommit this impossible ferry until terrain knowledge changes.",
				player, objective, pickupNavalRegion, terrainVersion, reason ?? "no same-region landing shoreline exists");
		}


		bool IsSeaLandingProofFailureCached(CPos objective, int pickupNavalRegion)
		{
			RefreshSeaTopologyFailureCacheVersion();
			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			if (terrainVersion < 0)
				return false;
			var key = new SeaLandingProofFailureKey(objective, pickupNavalRegion, terrainVersion);
			return seaLandingProofFailuresUntil.TryGetValue(key, out var until) && world.WorldTick < until;
		}

		void RememberSeaLandingProofFailure(CPos objective, int pickupNavalRegion)
		{
			RefreshSeaTopologyFailureCacheVersion();
			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			if (terrainVersion < 0)
				return;
			var key = new SeaLandingProofFailureKey(objective, pickupNavalRegion, terrainVersion);
			var until = world.WorldTick + Math.Max(Info.ScanInterval, Info.FutureRefineryProofRetryDelay);
			if (seaLandingProofFailuresUntil.TryGetValue(key, out var existing) && existing >= until)
				return;
			seaLandingProofFailuresUntil[key] = until;
			FransBotLog.BotDebug(world,
				"{0}: SEA LANDING short negative-cache records ore {1} from pickup naval region {2} until WT {3}. The fully ranked handoff/exit proof was exhausted, so subsequent planner passes skip it briefly instead of repeating the same A* burst.",
				player, objective, pickupNavalRegion, until);
		}

		bool IsFutureRefineryProofCooling(CPos objective)
		{
			var radiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			return futureRefineryProofFailuresUntil.Any(kv => world.WorldTick < kv.Value &&
				(kv.Key - objective).LengthSquared <= radiusSquared);
		}

		void RememberFutureRefineryProofFailure(CPos objective)
		{
			var until = world.WorldTick + Info.FutureRefineryProofRetryDelay;
			if (futureRefineryProofFailuresUntil.TryGetValue(objective, out var existing) && existing >= until)
				return;

			futureRefineryProofFailuresUntil[objective] = until;
			FransBotLog.BotDebug(world,
				"{0}: OUTPOST PROC PRE-PROOF rejects ore {1} for {2} WT: the future FACT deploy solution currently exposes no legal non-Critical refinery footprint within expansion radius. PIONEER does not commit and may reconsider after blockers/world state change.",
				player, objective, Info.FutureRefineryProofRetryDelay);
		}

		bool TryProveFutureExpansionRefineryPlacement(Actor mcv, CPos deployCell, out string refineryType, out CPos refineryCell)
		{
			return TryProveFutureExpansionRefineryPlacement(mcv, deployCell, out refineryType, out refineryCell,
				out _);
		}

		bool TryProveFutureExpansionRefineryPlacement(Actor mcv, CPos deployCell, out string refineryType,
			out CPos refineryCell, out bool failureRiskSensitive)
		{
			refineryType = null;
			refineryCell = default;
			failureRiskSensitive = false;
			foreach (var candidate in EnumerateFutureExpansionRefineryFootprints(mcv, deployCell))
			{
				if (!world.CanPlaceBuilding(candidate.Cell, candidate.ActorInfo, candidate.BuildingInfo, null))
					continue;
				failureRiskSensitive = true;
				if (riskModelService.EvaluateStrategicCell(candidate.Cell, FransRiskRole.BuildingPlacement,
					CurrentMcvRiskTolerance).IsCritical)
					continue;

				refineryType = candidate.Type;
				refineryCell = candidate.Cell;
				return true;
			}

			return false;
		}

		IEnumerable<(string Type, CPos Cell, ActorInfo ActorInfo, BuildingInfo BuildingInfo)>
			EnumerateFutureExpansionRefineryFootprints(Actor mcv, CPos deployCell)
		{
			var transformsInfo = mcv?.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null)
				yield break;

			var futureFactCell = deployCell + transformsInfo.Offset;
			foreach (var type in Info.ExpansionRefineryTypes.OrderBy(x => x))
			{
				if (!world.Map.Rules.Actors.TryGetValue(type, out var actorInfo))
					continue;
				var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
				if (buildingInfo == null)
					continue;

				foreach (var cell in world.Map.FindTilesInAnnulus(futureFactCell,
					Info.ExpansionStructureMinRadius, Info.ExpansionStructureMaxRadius)
					.Where(world.Map.Contains)
					.OrderBy(c => (c - futureFactCell).LengthSquared)
					.ThenBy(c => c.X)
					.ThenBy(c => c.Y))
					yield return (type, cell, actorInfo, buildingInfo);
			}
		}

		void TryPrepareRoutineLandNegativeUnion(Actor mcv, Mobile mobile,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			int firstPlannedIndex, RoutineLandNegativeUnionScanState state)
		{
			if (state == null || state.Coordinator.PreparationAttempted)
				return;
			var remainingCandidateUpperBound = state.PlannedCandidates.Length - firstPlannedIndex;
			if (state.Coordinator.OrdinaryNativeEmptyResults < RoutineLandNegativeUnionPolicy.ActivationNativeEmptyResults)
				return;
			if (!RoutineLandNegativeUnionPolicy.ShouldAttemptPreparation(
				state.Coordinator.OrdinaryNativeEmptyResults, remainingCandidateUpperBound,
				state.Coordinator.PreparationAttempted))
			{
				if (state.Perf != null)
				{
					state.Perf.RoutineLandUnionActivationReason = "InsufficientRemainingCandidateUpperBound";
					state.Perf.RoutineLandUnionFallbackReason = "InsufficientRemainingCandidateUpperBound";
				}
				return;
			}
			var perf = state.Perf;
			var preparationStarted = Stopwatch.GetTimestamp();
			var preparationAllocatedBytes = GC.GetAllocatedBytesForCurrentThread();

			var pathFinder = mobile.PathFinder as PathFinder;

			var eligible = new List<RoutineLandNegativeUnionObjective>();
			for (var i = firstPlannedIndex; i < state.PlannedCandidates.Length; i++)
			{
				var objective = state.PlannedCandidates[i].Candidate.ResourceCenter;
				if (IsFutureRefineryProofCooling(objective))
					continue;

				var targets = GetSafeDeployCandidates(mcv, mobile, objective,
					transformsInfo, intoActor, buildingInfo);
				if (!RoutineLandNegativeUnionPolicy.SupportsTargets(targets))
					continue;
				if (pathFinder == null || !targets.Any(target => pathFinder.PathMightExistForLocomotorBlockedByImmovable(
					mobile.Locomotor, state.Source, target)))
					continue;

				eligible.Add(new RoutineLandNegativeUnionObjective(objective, targets));
			}

			var nativeElapsedMs = 0d;
			long nativeAllocatedBytes = 0;
			var result = state.Coordinator.TryPrepare(
				remainingCandidateUpperBound,
				world.Map.Grid.MaximumTerrainHeight <= 0,
				() => CurrentRoutineLandNegativeUnionContract(mcv, mobile),
				eligible,
				unionTargets =>
				{
					if (pathFinder == null)
						return default;

					var started = Stopwatch.GetTimestamp();
					var allocatedBytes = GC.GetAllocatedBytesForCurrentThread();
					RoutineLandNativePathResult nativeResult;
					using (FransBotLog.Profile(world, player, "MCV.RoutineLandNegativeUnion"))
						nativeResult = RoutineLandNativePathInvoker.FindPathToTargetCells(
							mcv, pathFinder, state.Source, unionTargets,
							search => riskModelService.ExecuteWithPreparedPathCost(mcv,
								FransRiskRole.Mcv, CurrentMcvRiskTolerance, search));
					nativeElapsedMs = ElapsedMilliseconds(started);
					nativeAllocatedBytes = GC.GetAllocatedBytesForCurrentThread() - allocatedBytes;
					return nativeResult;
				});

			if (result.Outcome == RoutineLandNegativeUnionPreparationOutcome.NotAttempted)
			{
				if (perf != null && result.FallbackReason != null)
				{
					perf.RoutineLandUnionActivationReason = result.FallbackReason;
					perf.RoutineLandUnionFallbackReason = result.FallbackReason;
				}
				return;
			}

			if (perf != null)
			{
				perf.RoutineLandUnionPreparationAttempts++;
				perf.RoutineLandUnionActivationReason = result.ActivationReason;
				perf.RoutineLandUnionPreparationElapsedMs +=
					Math.Max(0d, ElapsedMilliseconds(preparationStarted) - nativeElapsedMs);
				perf.RoutineLandUnionPreparationAllocatedBytes +=
					Math.Max(0L, GC.GetAllocatedBytesForCurrentThread() - preparationAllocatedBytes - nativeAllocatedBytes);
				perf.RoutineLandUnionEligibleObjectives = result.EligibleObjectives;
				perf.RoutineLandUnionTargetCells = result.UnionTargets.Length;
				perf.RoutineLandUnionTargetHash = OrderedCellHash(result.UnionTargets);
				perf.RoutineLandUnionOutcome = result.Outcome.ToString();
				perf.RoutineLandUnionFallbackReason = result.FallbackReason ?? "None";
				if (result.NativeCallExecuted)
				{
					perf.RoutineLandUnionNativeSearches++;
					perf.RoutineLandUnionPathCostCallbacks += result.NativeResult.PathCostCallbacks;
					perf.RoutineLandUnionElapsedMs += nativeElapsedMs;
					perf.PhysicalNativePathSearches++;
					perf.NativeTargetCells += result.UnionTargets.Length;
					perf.NativePathCostCallbackCalls += result.NativeResult.PathCostCallbacks;
					perf.RiskPathCostCalls += result.NativeResult.RiskPathCostCalls;
					perf.NativePathSearchElapsedMs += nativeElapsedMs;
					if (nativeElapsedMs > perf.MaxNativePathSearchElapsedMs)
					{
						perf.MaxNativePathSearchElapsedMs = nativeElapsedMs;
						perf.MaxNativeTargetCells = result.UnionTargets.Length;
						perf.MaxNativePathSearchCallbackCalls = result.NativeResult.PathCostCallbacks;
					}
				}
			}
		}

		RoutineLandNegativeUnionContract CurrentRoutineLandNegativeUnionContract(Actor mcv, Mobile mobile)
		{
			return new RoutineLandNegativeUnionContract(
				mcv, mcv.ActorID, mcv.Owner, mobile, mobile.Locomotor, mobile.ToCell, world.WorldTick,
				riskModelService?.RiskRevision ?? -1, strategicMapService?.TerrainKnowledgeVersion ?? -1,
				!mcv.Disposed && mcv.IsInWorld && !mcv.IsDead);
		}

		OreChoice? EvaluateOreCandidates(Actor mcv, Mobile mobile,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			IReadOnlyList<OreFieldCandidate> candidates, string classification, int plannedOffset,
			RoutineLandNegativeUnionScanState routineLandUnion,
			McvObjectiveScanPerf perf = null)
		{
			for (var candidateIndex = 0; candidateIndex < candidates.Count; candidateIndex++)
			{
				var candidate = candidates[candidateIndex];
				RoutineLandCandidatePerf candidatePerf = null;
				if (perf != null)
				{
					perf.NodesEvaluated++;
					candidatePerf = perf.BeginRoutineLandCandidate(candidate.ResourceCenter, classification);
				}

				TryPrepareRoutineLandNegativeUnion(mcv, mobile, transformsInfo, intoActor, buildingInfo,
					plannedOffset + candidateIndex, routineLandUnion);

				var deployCandidates = GetSafeDeployCandidates(mcv, mobile, candidate.ResourceCenter,
					transformsInfo, intoActor, buildingInfo, perf);
				if (candidatePerf != null)
					candidatePerf.DeployTargetCount = deployCandidates.Length;
				if (!TryFindSafeDeployPathFromCellUsingCandidates(mcv, mobile, mobile.ToCell, deployCandidates,
					out var deployCell, out var pathLength, out _, null, perf, candidate.ResourceCenter,
					routineLandPrePathGuards: true, routineLandCandidate: candidatePerf,
					routineLandUnion: routineLandUnion))
				{
					var reason = candidatePerf?.CooldownBeforePath == true
						? "FutureRefineryProofCooldown"
						: candidatePerf?.TopologyNegative == true
							? "TopologyNegativeNoSafeDeployPath"
							: candidatePerf?.NativeSearchSkippedByUnionCertificate == true
								? "CertifiedNativeNoPath"
							: "NoSafeDeployPath";
					if (candidatePerf != null)
						candidatePerf.Result = reason;
					LogMcvTarget(mcv, candidate.ResourceCenter, false, reason);
					continue;
				}

				if (!IsMcvRouteDetourAcceptable(mobile.ToCell, deployCell, pathLength))
				{
					if (candidatePerf != null)
						candidatePerf.Result = "RouteDetourExceeded";
					LogMcvTarget(mcv, candidate.ResourceCenter, false, "RouteDetourExceeded", deployCell, pathLength: pathLength);
					continue;
				}

				if (IsFutureRefineryProofCooling(candidate.ResourceCenter))
				{
					if (candidatePerf != null)
						candidatePerf.Result = "FutureRefineryProofCooldownAfterPath";
					LogMcvTarget(mcv, candidate.ResourceCenter, false, "FutureRefineryProofCooldown", deployCell, pathLength: pathLength);
					continue;
				}
				if (!TryProveFutureExpansionRefineryPlacement(mcv, deployCell, out _, out _))
				{
					RememberFutureRefineryProofFailure(candidate.ResourceCenter);
					if (candidatePerf != null)
						candidatePerf.Result = "NoFutureRefineryPlacement";
					LogMcvTarget(mcv, candidate.ResourceCenter, false, "NoFutureRefineryPlacement", deployCell, pathLength: pathLength);
					continue;
				}

				var risk = GetMcvRisk(mcv, deployCell, CurrentMcvRiskTolerance);
				if (risk.IsCritical)
				{
					if (candidatePerf != null)
						candidatePerf.Result = "CriticalDeployRisk";
					LogMcvTarget(mcv, candidate.ResourceCenter, false, "CriticalDeployRisk", deployCell, risk.Score, pathLength);
					continue;
				}

				// Input is already ordered nearest-first. The first non-critical, reasonably direct
				// route wins: risk is a veto, never a score that can promote a farther ore.
				if (perf != null)
					perf.AcceptedNativeProofIndex = perf.LastSuccessfulNativeProofIndex;
				if (candidatePerf != null)
				{
					candidatePerf.Result = "Accepted";
					candidatePerf.FinalWinner = true;
				}
				LogMcvTarget(mcv, candidate.ResourceCenter, true, "AcceptedLandTarget", deployCell, risk.Score, pathLength);
				return new OreChoice(candidate.ResourceCenter, deployCell, pathLength, risk.Score);
			}

			return null;
		}

		bool IsMcvRouteDetourAcceptable(CPos source, CPos destination, int pathLength)
		{
			return pathLength <= MaximumMcvRouteSteps(source, destination);
		}

		long MaximumMcvRouteSteps(CPos source, CPos destination)
		{
			var minimumSteps = Math.Max(Math.Abs(destination.X - source.X), Math.Abs(destination.Y - source.Y));
			if (minimumSteps <= 0)
				return long.MaxValue;

			var percentLimit = (long)minimumSteps * Info.MaximumMcvRouteDetourPercent / 100;
			return Math.Max(minimumSteps + Info.MaximumMcvRouteDetourSlackCells, percentLimit);
		}

		bool TryFindSafeDeployPath(Actor mcv, Mobile mobile, CPos resourceCenter,
			TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, out CPos deployCell, out int pathLength,
			McvObjectiveScanPerf perf = null, CPos? objective = null)
		{
			return TryFindSafeDeployPath(mcv, mobile, resourceCenter, transformsInfo, intoActor, buildingInfo,
				out deployCell, out pathLength, out _, perf, objective);
		}

		bool TryFindSafeDeployPath(Actor mcv, Mobile mobile, CPos resourceCenter,
			TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, out CPos deployCell, out int pathLength,
			out CPos[] provenPath, McvObjectiveScanPerf perf = null, CPos? objective = null)
		{
			return TryFindSafeDeployPath(mcv, mobile, resourceCenter, transformsInfo, intoActor, buildingInfo,
				out deployCell, out pathLength, out provenPath, null, perf, objective);
		}

		bool TryFindSafeDeployPath(Actor mcv, Mobile mobile, CPos resourceCenter,
			TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, out CPos deployCell, out int pathLength,
			out CPos[] provenPath, PioneerLandRouteAttemptEvidence evidence,
			McvObjectiveScanPerf perf = null, CPos? objective = null)
		{
			return TryFindSafeDeployPathFromCell(mcv, mobile, mobile.ToCell, resourceCenter,
				transformsInfo, intoActor, buildingInfo, out deployCell, out pathLength, out provenPath,
				evidence, perf, objective);
		}

		CPos[] GetSafeDeployCandidates(Actor mcv, Mobile mobile, CPos resourceCenter,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			McvObjectiveScanPerf perf = null)
		{
			var candidates = new List<CPos>();
			foreach (var cell in EnumerateExpansionDeployCells(resourceCenter))
			{
				if (perf != null)
					perf.DeployCellsEnumerated++;
				if (!world.Map.Contains(cell))
					continue;
				if (IsMcvCriticalRisk(mcv, cell, CurrentMcvRiskTolerance))
				{
					if (perf != null)
						perf.DeployCellsRiskRejected++;
					continue;
				}
				if (!IsExpansionDeployCellLegal(mcv, mobile, cell, transformsInfo, intoActor, buildingInfo))
				{
					if (perf != null)
						perf.DeployCellsLegalityRejected++;
					continue;
				}

				candidates.Add(cell);
			}

			if (perf != null)
				perf.DeployCandidatesGenerated += candidates.Count;
			return candidates.ToArray();
		}

		IEnumerable<CPos> EnumerateExpansionDeployCells(CPos resourceCenter)
		{
			return world.Map.FindTilesInAnnulus(resourceCenter,
				Info.ResourceDeployMinRadius, Info.ResourceDeployMaxRadius);
		}

		bool IsExpansionDeployCellLegal(Actor mcv, Mobile mobile, CPos cell,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo)
		{
			return mobile.CanEnterCell(cell, check: BlockedByActor.Immovable) &&
				mobile.CanStayInCell(cell) &&
				world.CanPlaceBuilding(cell + transformsInfo.Offset, intoActor, buildingInfo, mcv);
		}

		bool TryFindSafeDeployPathFromCell(Actor mcv, Mobile mobile, CPos sourceCell, CPos resourceCenter,
			TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, out CPos deployCell, out int pathLength,
			McvObjectiveScanPerf perf = null, CPos? objective = null)
		{
			return TryFindSafeDeployPathFromCell(mcv, mobile, sourceCell, resourceCenter,
				transformsInfo, intoActor, buildingInfo, out deployCell, out pathLength, out _, perf, objective);
		}

		bool TryFindSafeDeployPathFromCell(Actor mcv, Mobile mobile, CPos sourceCell, CPos resourceCenter,
			TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, out CPos deployCell, out int pathLength,
			out CPos[] provenPath, McvObjectiveScanPerf perf = null, CPos? objective = null)
		{
			return TryFindSafeDeployPathFromCell(mcv, mobile, sourceCell, resourceCenter,
				transformsInfo, intoActor, buildingInfo, out deployCell, out pathLength, out provenPath,
				null, perf, objective);
		}

		bool TryFindSafeDeployPathFromCell(Actor mcv, Mobile mobile, CPos sourceCell, CPos resourceCenter,
			TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, out CPos deployCell, out int pathLength,
			out CPos[] provenPath, PioneerLandRouteAttemptEvidence evidence,
			McvObjectiveScanPerf perf = null, CPos? objective = null)
		{
			var candidates = GetSafeDeployCandidates(mcv, mobile, resourceCenter, transformsInfo, intoActor, buildingInfo, perf);
			if (evidence != null)
				evidence.SafeDeployCells = candidates.OrderBy(cell => cell.Bits).ToArray();
			return TryFindSafeDeployPathFromCellUsingCandidates(mcv, mobile, sourceCell, candidates,
				out deployCell, out pathLength, out provenPath, evidence, perf, objective);
		}

		bool TryFindSafeDeployPathFromCellUsingCandidates(Actor mcv, Mobile mobile, CPos sourceCell,
			CPos[] candidates, out CPos deployCell, out int pathLength,
			McvObjectiveScanPerf perf = null, CPos? objective = null)
		{
			return TryFindSafeDeployPathFromCellUsingCandidates(mcv, mobile, sourceCell, candidates,
				out deployCell, out pathLength, out _, perf, objective);
		}

		bool TryFindSafeDeployPathFromCellUsingCandidates(Actor mcv, Mobile mobile, CPos sourceCell,
			CPos[] candidates, out CPos deployCell, out int pathLength, out CPos[] provenPath,
			McvObjectiveScanPerf perf = null, CPos? objective = null)
		{
			return TryFindSafeDeployPathFromCellUsingCandidates(mcv, mobile, sourceCell, candidates,
				out deployCell, out pathLength, out provenPath, null, perf, objective);
		}

		bool TryFindSafeDeployPathFromCellUsingCandidates(Actor mcv, Mobile mobile, CPos sourceCell,
			CPos[] candidates, out CPos deployCell, out int pathLength, out CPos[] provenPath,
			PioneerLandRouteAttemptEvidence evidence,
			McvObjectiveScanPerf perf = null, CPos? objective = null,
			bool routineLandPrePathGuards = false, RoutineLandCandidatePerf routineLandCandidate = null,
			RoutineLandNegativeUnionScanState routineLandUnion = null)
		{
			deployCell = default;
			pathLength = int.MaxValue;
			provenPath = [];
			var logicalProofIndex = 0;
			if (perf != null)
			{
				logicalProofIndex = ++perf.LogicalNativeProofRequests;
				perf.LastNativeTargetCount = candidates?.Length ?? 0;
				perf.LastNativeTargetHash = OrderedCellHash(candidates);
			}

			if (candidates == null || candidates.Length == 0 || mobile.PathFinder is not PathFinder pathFinder)
				return false;

			if (routineLandPrePathGuards && objective.HasValue && IsFutureRefineryProofCooling(objective.Value))
			{
				if (perf != null)
				{
					perf.CandidatesRejectedByPrePathRefineryCooldown++;
					perf.NativeSearchesSkippedByCooldownBeforePath++;
				}
				if (routineLandCandidate != null)
					routineLandCandidate.CooldownBeforePath = true;
				return false;
			}

			if (routineLandPrePathGuards)
			{
				// OpenRA guarantees only the negative result. Any topology-maybe target must still use
				// the unchanged risk-aware native multi-target search below.
				var pathMightExist = candidates.Any(target =>
				{
					if (perf != null)
						perf.TopologyTargetQueries++;
					return pathFinder.PathMightExistForLocomotorBlockedByImmovable(
						mobile.Locomotor, sourceCell, target);
				});
				if (!pathMightExist)
				{
					if (perf != null)
					{
						perf.TopologyNegativeCandidates++;
						perf.NativeSearchesSkippedByTopologyNegative++;
					}
					if (routineLandCandidate != null)
						routineLandCandidate.TopologyNegative = true;
					return false;
				}
			}

			if (routineLandPrePathGuards && routineLandUnion != null && objective.HasValue &&
				routineLandUnion.Coordinator.HasCertificate(objective.Value))
			{
				if (!routineLandUnion.Coordinator.TryUseCertificate(objective.Value, candidates,
					CurrentRoutineLandNegativeUnionContract(mcv, mobile), out var mismatch))
				{
					if (perf != null)
						perf.RoutineLandUnionCertificateMismatches++;
					if (routineLandCandidate != null)
						routineLandCandidate.UnionCertificateMismatch = mismatch;
				}
				else
				{
					if (perf != null)
						perf.RoutineLandNativeSearchesSkippedByUnionCertificate++;
					if (routineLandCandidate != null)
						routineLandCandidate.NativeSearchSkippedByUnionCertificate = true;
					return false;
				}
			}

			if (evidence != null)
				evidence.NativePathSearchAttempted = true;
			if (routineLandCandidate != null)
				routineLandCandidate.NativeSearchExecuted = true;
			var pathSearchStarted = Stopwatch.GetTimestamp();
			RoutineLandNativePathResult nativeResult;
			using (FransBotLog.Profile(world, player, "MCV.NativeDeployPath"))
				nativeResult = RoutineLandNativePathInvoker.FindPathToTargetCells(
					mcv, pathFinder, sourceCell, candidates,
					search => riskModelService.ExecuteWithPreparedPathCost(mcv,
						FransRiskRole.Mcv, CurrentMcvRiskTolerance, search));
			var path = nativeResult.Path;
			var pathSearchElapsedMs = ElapsedMilliseconds(pathSearchStarted);
			if (routineLandCandidate != null)
			{
				routineLandCandidate.NativePathCostCallbacks = nativeResult.PathCostCallbacks;
				routineLandCandidate.NativeElapsedMs = pathSearchElapsedMs;
			}
			if (perf != null)
			{
				perf.PhysicalNativePathSearches++;
				if (routineLandUnion != null)
				{
					perf.RoutineLandOrdinaryNativeSearches++;
					perf.RoutineLandOrdinaryPathCostCallbacks += nativeResult.PathCostCallbacks;
				}
				perf.NativeTargetCells += candidates.Length;
				perf.NativePathCostCallbackCalls += nativeResult.PathCostCallbacks;
				perf.RiskPathCostCalls += nativeResult.RiskPathCostCalls;
				perf.NativePathSearchElapsedMs += pathSearchElapsedMs;
				if (pathSearchElapsedMs > perf.MaxNativePathSearchElapsedMs)
				{
					perf.MaxNativePathSearchElapsedMs = pathSearchElapsedMs;
					perf.MaxNativeTargetCells = candidates.Length;
					perf.MaxNativePathSearchCallbackCalls = nativeResult.PathCostCallbacks;
				}
				perf.Pass.RecordPhysicalProof(perf, mcv, sourceCell, candidates);
			}

			if (path == null)
				return false;

			if (path.Count == 0)
			{
				if (routineLandUnion != null)
				{
					routineLandUnion.Coordinator.RecordOrdinaryNativeResult(nativeResult);
					if (perf != null)
						perf.RoutineLandOrdinaryNativeEmptyResults++;
				}
				return false;
			}

			provenPath = path.ToArray();
			if (evidence != null)
				evidence.ReturnedPath = provenPath;

			for (var p = 0; p < path.Count - 1; p++)
			{
				if (perf != null)
					perf.PostPathRiskChecks++;
				if (IsMcvCriticalRisk(mcv, path[p], CurrentMcvRiskTolerance))
				{
					if (evidence != null)
						evidence.ReturnedPathRejectedForRisk = true;
					return false;
				}
			}

			deployCell = path[0];
			pathLength = path.Count;
			if (perf != null)
			{
				if (perf.FirstSuccessfulNativeProofIndex == 0)
					perf.FirstSuccessfulNativeProofIndex = logicalProofIndex;
				perf.LastSuccessfulNativeProofIndex = logicalProofIndex;
				perf.Pass.RecordResolvedDeployCell(objective, deployCell);
			}
			return true;
		}



		bool TryProveSeaSupplyBeforeCommit(Actor mcv, Mobile mobile, SeaTargetChoice target, out string proof, out int pickupRegion)
		{
			proof = null;
			pickupRegion = -1;
			seaLandingCraftCell = target.LandingCraftCell;

			// A physical free LST is the strongest proof because the exact pickup + crossing
			// geometry is validated against that actor before the ore mission owns the MCV.
			if (TryFindAvailableLandingCraftForObjective(mcv, mobile, target.ResourceCenter, out _, out _))
			{
				proof = "usable physical LST already passes the exact pickup/crossing proof";
				return true;
			}

			if (!TryPrepareCachedSeaGeometryForObjective(mcv, mobile, target.ResourceCenter) ||
				!preferredRoutinePickupCraftCell.HasValue || !seaLandingCraftCell.HasValue ||
				!strategicMapService.TryGetNavalRegionId(preferredRoutinePickupCraftCell.Value, out pickupRegion) ||
				!strategicMapService.TryGetNavalRegionId(seaLandingCraftCell.Value, out var landingRegion) || pickupRegion != landingRegion)
			{
				proof = "pickup/landing naval-region geometry cannot be proven";
				pickupRegion = -1;
				return false;
			}

			// SUPPLY and POSSIBILITY are deliberately separate. A physical producer or a hypothetical
			// staging site is infrastructure potential, not a SeaOre execution guarantee. The
			// strategic ore may commit only after a producer-bound queue visibly owns a same-region
			// LST item (or a physical exact-route LST already exists above). A classic/shared Ship
			// queue remains region-unbound until OpenRA selects the delivery producer.
			if (HasQueuedLandingCraftProduction(pickupRegion))
			{
				proof = $"producer-bound queued LST exists in naval region {pickupRegion}";
				return true;
			}

			if (HasRegionalLandingCraftQueueSupplyCapability(pickupRegion))
			{
				proof = $"an eligible producer exists in naval region {pickupRegion}, but no physical or producer-bound LST reservation is visible yet";
				return false;
			}

			if (CanPlaceAnyLandingCraftProducerFromCurrentBase(pickupRegion))
			{
				proof = $"current build radius can create the required naval producer in region {pickupRegion}, but SeaOre must wait for actionable LST supply";
				return false;
			}

			proof = $"no actionable LST reservation exists yet in naval region {pickupRegion}; current-base producer placement is unavailable, so bounded coastal FACT->SPEN/SYRD support must be proved before any SeaOre commit";
			return false;
		}

		bool TryBeginSeaExpansion(IBot bot, Actor mcv, Mobile mcvMobile, SeaTargetChoice? preferredTarget = null)
		{
			var target = preferredTarget ?? FindNearestRoutineSeaOreField(mcv, mcvMobile);
			if (!target.HasValue)
				return false;

			if (!TryProveSeaSupplyBeforeCommit(mcv, mcvMobile, target.Value, out var seaSupplyProof, out var pickupRegion))
			{
				if (pickupRegion >= 0)
				{
					MarkPreCommitLandingCraftDemand(pickupRegion, target.Value.ResourceCenter);
					LatchNavalCapabilityDemand("PIONEER found an other-landmass ore whose ferry geometry is valid, but actionable same-region LST supply must exist before SeaOre commit");

					if (HasRegionalLandingCraftQueueSupplyCapability(pickupRegion))
					{
						TryQueueRegionalLandingCraftSupply(bot, pickupRegion, out var queueState);
						LogSeaSupplyPreCommitDiagnostic(bot, mcv, target.Value.ResourceCenter,
							pickupRegion, "Blocked", seaSupplyProof, queueState);
						ClearTarget();
						nextSeaPlanningTick = world.WorldTick + Math.Min(Info.SeaPlanningInterval, 100);
						FransBotLog.BotDebug(world,
							"{0}: SEA SUPPLY PRE-COMMIT holds ore {1} outside ExpansionTask: {2}; {3}. PIONEER remains strategically uncommitted until the queued LST is visible.",
							player, target.Value.ResourceCenter, seaSupplyProof, queueState);
						return false;
					}

					if (CanPlaceAnyLandingCraftProducerFromCurrentBase(pickupRegion))
					{
						if (firstExpansionRefineryReservationActive && !firstExpansionRefineryReservationCompleted)
							SuspendFirstExpansionRefineryForInfrastructure(bot, "the nearest PIONEER objective requires a same-region naval producer before any SeaOre commit");

						var queuesByCategory = AIUtils.FindQueuesByCategory(player);
						var shipQueues = ShipQueueNames().SelectMany(name => queuesByCategory[name])
							.Where(q => q.Enabled)
							.Distinct()
							.ToArray();
						EnsureLandingCraftProducer(bot, queuesByCategory, shipQueues, pickupRegion);
						ClearTarget();
						nextSeaPlanningTick = world.WorldTick + Info.SeaPlanningInterval;
						FransBotLog.BotDebug(world,
							"{0}: SEA SUPPLY PRE-COMMIT defers ore {1}: {2}. Current-base SPEN/SYRD support is being created in naval region {3}; no SeaOre task owns the MCV yet.",
							player, target.Value.ResourceCenter, seaSupplyProof, pickupRegion);
						return false;
					}

					if (TryBeginCoastalStaging(bot, mcv, mcvMobile,
						requiredNavalRegion: pickupRegion, supportObjective: target.Value.ResourceCenter))
					{
						FransBotLog.BotDebug(world,
							"{0}: SEA SUPPLY PRE-COMMIT routes PIONEER MCV {1} into bounded CoastalStaging support for candidate ore {2}/naval region {3}. The ore itself remains uncommitted until a physical or genuinely queued LST exists.",
							player, mcv, target.Value.ResourceCenter, pickupRegion);
						return true;
					}
				}

				ClearPreCommitLandingCraftDemand();
				MarkExpansionAreaCooldown(target.Value.ResourceCenter, Info.FailedFieldRetryDelay,
					"Sea supply feasibility had no actionable LST reservation or complete infrastructure support path");
				FransBotLog.BotDebug(world,
					"{0}: SEA SUPPLY FEASIBILITY rejects ore area {1} BEFORE MCV COMMIT: {2}. Nearby MineCluster coordinates share the cooldown instead of immediately becoming a nominally new target.",
					player, target.Value.ResourceCenter, seaSupplyProof);
				ClearTarget();
				return false;
			}

			LogResolvedSeaSupplyPreCommitDiagnosticIfObserved(bot, mcv, target.Value.ResourceCenter,
				pickupRegion, seaSupplyProof);
			ClearPreCommitLandingCraftDemand();
			LatchNavalCapabilityDemand("routine MCV expansion selected an otherwise-unreachable ore field with proven regional LST supply path: " + seaSupplyProof);
			// Target first, transport second. The ExpansionTask owns this objective exactly once;
			// transport is merely an execution dependency and can no longer become an independent
			// hidden mission state. This mirrors Ground Commander mission ownership.
			if (!BeginExpansionTask(ExpansionTaskMode.SeaOre, target.Value.ResourceCenter, target.Value.DeployCell,
				ExpansionStage.WaitingForSeaTransport, world.WorldTick,
				"planner selected an executable other-landmass ore; transport is demand-only execution"))
				return false;
			seaLandingCraftCell = target.Value.LandingCraftCell;

			if (!TryFindAvailableLandingCraftForObjective(mcv, mcvMobile, target.Value.ResourceCenter, out var craft, out var plan))
			{
				var hasRequiredRegion = TryGetRequiredLandingCraftProductionRegion(out var requiredNavalRegion);
				var hasUsableProducer = hasRequiredRegion
					? HasOwnedLandingCraftProducer(requiredNavalRegion)
					: HasOwnedLandingCraftProducer();
				if (firstExpansionRefineryReservationActive && !firstExpansionRefineryReservationCompleted &&
					!hasUsableProducer)
				{
					if (TryBeginCoastalStaging(bot, mcv, mcvMobile,
						requiredNavalRegion: hasRequiredRegion ? requiredNavalRegion : null))
						return true;

					SuspendFirstExpansionRefineryForInfrastructure(bot, "the first routine expansion selected a nearby ore objective on another landmass and requires same-region naval access");
				}

				if (TryYieldToEarlierAlliedMcvReservation(bot))
					return true;
				RequestLandingCraft(bot);
				FransBotLog.BotDebug(world,
					"{0}: routine expansion MCV {1} COMMITs other-landmass ore {2}, provisional landing {3}, deploy {4}; target stays fixed while it waits for a usable LST, matching the E6 transport mission contract.",
					player, mcv, target.Value.ResourceCenter, target.Value.LandingCraftCell, target.Value.DeployCell);
				return true;
			}

			// Routine expansion has one MCV safety policy on land and water. General SECURE no longer
			// owns any MCV beachhead/escort state; the LST is only a movement mechanism.
			return BeginMcvSeaCrossing(bot, mcv, mcvMobile, craft, plan,
				"routine landmass-neutral expansion; LST is only the movement mechanism, not a separate assault mode");
		}

		void ManageSeaExpansion(IBot bot)
		{
			switch (stage)
			{
				case ExpansionStage.WaitingForSeaTransport:
					ManageWaitingForSeaTransport(bot);
					return;

				case ExpansionStage.MovingToSeaPickup:
					ManageSeaPickup(bot);
					return;

				case ExpansionStage.SeaLoading:
					ManageSeaLoading(bot);
					return;

				case ExpansionStage.SeaTransporting:
					ManageSeaTransport(bot);
					return;

				case ExpansionStage.SeaUnloading:
					ManageSeaUnload(bot);
					return;

				case ExpansionStage.SeaCargoPreserved:
					ManagePreservedSeaCargo(bot);
					return;
			}
		}

		void ManageWaitingForSeaTransport(IBot bot)
		{
			LogMcvIdentity(activeMcv);
			if (!IsLiveOwnedMcv(activeMcv))
			{
				activeMcv = null;
				AbortExpansionTaskToIdle(bot, "sea expansion lost its MCV while waiting for demand-driven transport");
				nextLandExpansionPlanningTick = world.WorldTick;
				return;
			}
			var mobile = activeMcv.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
			{
				LogMcvWaitingState(activeMcv, "WaitingForFerryNoOperationalMobileTrait");
				return;
			}

			// a routine ferry behaves like the proven E6 transport state machine. The mission
			// owns one passenger + one objective until completion or real invalidation; it never re-ranks
			// into another ore field while waiting for a transport.
			if (expansionTask.Mode != ExpansionTaskMode.SeaOre || !targetResourceCenter.HasValue ||
				!IsCommittedRoutineFerryObjectiveStillValid(targetResourceCenter.Value))
			{
				AbortExpansionTaskToIdle(bot, "committed sea ore became invalid/serviced; planner must choose the next objective");
				nextLandExpansionPlanningTick = world.WorldTick;
				return;
			}

			if (TryCommittedRoutineObjectiveAsLandMove(activeMcv, mobile, targetResourceCenter.Value, out var landDeploy))
			{
				// Transport method may change if the SAME objective becomes land-reachable (e.g. bridge
				// state changed), but the objective itself remains committed.
				ResumeFirstExpansionRefineryAfterInfrastructure("the same committed routine objective became land-reachable");
				ResetSeaMission(clearTarget: false);
				ChangeExpansionTaskMode(ExpansionTaskMode.LandOre, "the same committed ore became land-reachable; only the transport method changed");
				targetDeployCell = landDeploy;
				stage = ExpansionStage.MovingToOre;
				nextRouteRecheckTick = world.WorldTick + Info.RouteRecheckInterval;
				QueueRiskAwareMove(activeMcv, mobile, landDeploy);
				return;
			}

			if (TryYieldToEarlierAlliedMcvReservation(bot))
				return;

			var ordinaryCorridorCheckDue = world.WorldTick >= nextSeaPlanningTick;
			// Bounded recovery advances independently between ordinary original-corridor checks.
			// When both clocks are due, give the original corridor its scheduled chance first and
			// defer alternate recovery to the next scan so one pass never pays both exact-LST batches.
			if (committedSeaCorridorRecovery != null && !ordinaryCorridorCheckDue)
			{
				if (committedSeaCorridorRecovery.PausedForOriginalEligibility)
				{
					LogMcvWaitingState(activeMcv, "WaitingForOriginalFerryEligibilityBeforeRecoveryResumes");
					return;
				}
				if (TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, committedSeaCorridorRecovery))
					return;
				if (world.WorldTick < committedSeaCorridorRecovery.NextAdvanceTick)
				{
					LogMcvWaitingState(activeMcv,
						$"WaitingForBoundedFerryRecoveryPassAtWT{committedSeaCorridorRecovery.NextAdvanceTick}");
					return;
				}

				var recoveryTerminal = TryAdvanceCommittedSeaCorridorRecovery(bot, activeMcv, mobile,
					targetResourceCenter.Value);
				if (!recoveryTerminal && committedSeaCorridorRecovery != null)
					RequestLandingCraft(bot);
				return;
			}

			if (!ordinaryCorridorCheckDue)
			{
				LogMcvWaitingState(activeMcv, $"WaitingForFerryPlanningCooldownUntilWT{nextSeaPlanningTick}");
				return;
			}
			nextSeaPlanningTick = world.WorldTick + Info.SeaPlanningInterval;

			if (!TryFindAvailableLandingCraftForObjective(activeMcv, mobile, targetResourceCenter.Value, out var craft, out var plan))
			{
				if (seaTransportWaitStartedTick < 0)
					seaTransportWaitStartedTick = world.WorldTick;
				var exactPathFailure = lastLandingCraftPlanHadPickupFailure || lastLandingCraftPlanHadCrossingFailure;
				if (exactPathFailure)
				{
					if (seaExactPathFailureStartedTick < 0)
						seaExactPathFailureStartedTick = world.WorldTick;
					ResumeCommittedSeaCorridorRecoveryAfterExactFailure();
				}
				else
				{
					// Supply absence, reservation pressure and wrong-region craft are not corridor
					// failures. Pause an already-active proof rather than silently replacing its
					// owner, lifetime and finite budget when exact eligibility becomes observable again.
					seaExactPathFailureStartedTick = -1;
					PauseCommittedSeaCorridorRecoveryForOriginalEligibility();
				}
				LogCommittedSeaExecutionDiagnostic("WaitingNoExecutableLst", null,
					"physical supply, claimability and exact cached pickup/crossing eligibility are reported separately");

				var hasRequiredRegion = TryGetRequiredLandingCraftProductionRegion(out var requiredNavalRegion);
				var hasUsableProducer = hasRequiredRegion
					? HasOwnedLandingCraftProducer(requiredNavalRegion)
					: HasOwnedLandingCraftProducer();
				var canPlaceUsableProducer = hasRequiredRegion
					? CanPlaceAnyLandingCraftProducerFromCurrentBase(requiredNavalRegion)
					: CanPlaceAnyLandingCraftProducerFromCurrentBase();

				if (firstExpansionRefineryReservationActive && !firstExpansionRefineryReservationCompleted && !hasUsableProducer)
				{
					if (TryBeginCoastalStaging(bot, activeMcv, mobile,
						requiredNavalRegion: hasRequiredRegion ? requiredNavalRegion : null))
						return;

					SuspendFirstExpansionRefineryForInfrastructure(bot, "the first routine expansion is committed to another-landmass ore while no usable same-region LST exists");
				}
				else if (!hasUsableProducer && !canPlaceUsableProducer &&
					TryBeginCoastalStaging(bot, activeMcv, mobile, requiredNavalRegion: hasRequiredRegion ? requiredNavalRegion : null))
					return;

				var waited = world.WorldTick - seaTransportWaitStartedTick;
				if (committedSeaCorridorRecovery == null && exactPathFailure && seaExactPathFailureStartedTick >= 0 &&
					world.WorldTick - seaExactPathFailureStartedTick >= Info.SeaTransportFeasibilityWatchdogTicks &&
					TryStartCommittedSeaCorridorRecovery(activeMcv, mobile, targetResourceCenter.Value))
				{
					if (TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, committedSeaCorridorRecovery))
						return;
					RequestLandingCraft(bot);
					LogMcvWaitingState(activeMcv, "WaitingForBoundedFerryCorridorRecovery");
					return;
				}

				if (Info.SeaTransportAbsoluteWaitWatchdogTicks > 0 && waited >= Info.SeaTransportAbsoluteWaitWatchdogTicks)
				{
					var oldObjective = targetResourceCenter.Value;
					MarkExpansionAreaCooldown(oldObjective, Info.FailedFieldRetryDelay,
						"absolute WaitingForSeaTransport timeout");
					FransBotLog.BotDebug(world,
						"{0}: MCV WaitingForSeaTransport ABSOLUTE watchdog releases committed ore area {1} after {2} WT. Wrong-region LSTs/queues cannot keep strategic expansion pinned indefinitely; nearby MineCluster coordinates share the retry cooldown.",
						player, oldObjective, waited);
					AbortExpansionTaskToIdle(bot, "absolute WaitingForSeaTransport timeout", oldObjective);
					nextSeaPlanningTick = world.WorldTick + Info.SeaPlanningInterval;
					return;
				}

				var queuedLandingCraft = HasQueuedLandingCraftProduction(hasRequiredRegion ? requiredNavalRegion : null);
				if (!queuedLandingCraft && waited >= Info.SeaTransportFeasibilityWatchdogTicks &&
					!HasFeasibleUnbuiltSeaTransportProspect(activeMcv, mobile, targetResourceCenter.Value, out var infeasibleReason))
				{
					var oldObjective = targetResourceCenter.Value;
					MarkExpansionAreaCooldown(oldObjective, Info.FailedFieldRetryDelay,
						$"WaitingForSeaTransport feasibility watchdog: {infeasibleReason}");
					FransBotLog.BotDebug(world,
						"{0}: MCV WaitingForSeaTransport watchdog releases committed ore area {1} after {2} WT without a physical or genuinely queued SAME-REGION LST: {3}. Nearby MineClusters share the cooldown, preventing one-cell target bounce.",
						player, oldObjective, Info.SeaTransportFeasibilityWatchdogTicks, infeasibleReason);
					AbortExpansionTaskToIdle(bot, $"WaitingForSeaTransport watchdog: {infeasibleReason}", oldObjective);
					nextSeaPlanningTick = world.WorldTick + Info.SeaPlanningInterval;
					return;
				}

				RequestLandingCraft(bot);
				LogMcvWaitingState(activeMcv, hasRequiredRegion
					? $"WaitingForFerryInNavalRegion{requiredNavalRegion}"
					: "WaitingForFerry");
				return;
			}

			ResumeFirstExpansionRefineryAfterInfrastructure("a usable physical LST is available for the committed routine other-landmass objective");
			// Exact eligibility has recovered even if the subsequent ownership transfer is rejected.
			// Keep reservation pressure separate from a future continuous path-failure episode.
			committedSeaCorridorRecovery = null;
			seaExactPathFailureStartedTick = -1;
			lastCommittedSeaCorridorRecoveryDiagnosticSignature = null;
			if (!BeginMcvSeaCrossing(bot, activeMcv, mobile, craft, plan,
				"committed routine ferry objective; E6-style mission ownership with no mid-wait retargeting"))
			{
				LogCommittedSeaExecutionDiagnostic("ClaimRejected", craft,
					"the exact cached plan passed, but TransportCommander did not transfer reservation ownership");
				return;
			}

			LogCommittedSeaExecutionDiagnostic("ClaimedAndPickupStarted", craft,
				"TransportCommander reservation succeeded and native pickup moves were issued");
		}

		bool IsCommittedRoutineFerryObjectiveStillValid(CPos objective)
		{
			if (!world.Map.Contains(objective) || IsFieldTemporarilyFailed(objective))
				return false;
			if (TryGetPreferredRoutinePickupNavalRegion(out var pickupNavalRegion) &&
				IsSeaTopologyFailureCached(objective, pickupNavalRegion))
				return false;

			var ownServiceStructures = world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && Info.ExpansionRefineryTypes.Contains(a.Info.Name))
				.ToArray();
			var ownCoverageStructures = world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && Info.ExistingBaseCoverageTypes.Contains(a.Info.Name))
				.ToArray();
			return !IsFieldServiced(objective, ownServiceStructures, ownCoverageStructures);
		}

		bool TryCommittedRoutineObjectiveAsLandMove(Actor mcv, Mobile mobile, CPos objective, out CPos deployCell)
		{
			deployCell = default;
			var transformsInfo = mcv?.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null || !world.Map.Rules.Actors.TryGetValue(transformsInfo.IntoActor, out var intoActor))
				return false;
			var buildingInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			return buildingInfo != null && TryFindSafeDeployPath(mcv, mobile, objective, transformsInfo, intoActor, buildingInfo, out deployCell, out _);
		}

		bool TryFindAvailableLandingCraftForObjective(Actor mcv, Mobile mcvMobile, CPos objective, out Actor craft, out SeaPlan plan)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "MCV.LandingCraftPlan");
			craft = null;
			plan = default;
			lastLandingCraftPlanHadPickupFailure = false;
			lastLandingCraftPlanHadCrossingFailure = false;
			if (!IsLiveOwnedMcv(mcv) || mcvMobile == null)
			{
				lastLandingCraftPlanDiagnostic = "preconditions=Failed,geometry=NotEvaluated,topology=NotEvaluated,crafts=[none]";
				return false;
			}

			// SIMPLE FERRY: build the expensive MCV pickup + destination geometry once
			// for the committed ore objective. Waiting for a physical LST must not repeat the
			// full shoreline/deploy search for every free craft on every planning pass.
			if (!TryPrepareCachedSeaGeometryForObjective(mcv, mcvMobile, objective))
			{
				lastLandingCraftPlanDiagnostic = "preconditions=Passed,geometry=Failed,topology=NotEvaluated,crafts=[none]";
				return false;
			}

			var found = TryFindAvailableLandingCraftForGeometry(mcv, objective,
				preferredRoutinePickupMcvCell.Value, preferredRoutinePickupCraftCell.Value,
				seaLandingCraftCell.Value, targetDeployCell.Value, out craft, out plan,
				out lastLandingCraftPlanHadPickupFailure, out lastLandingCraftPlanHadCrossingFailure,
				out var diagnostic);
			lastLandingCraftPlanDiagnostic = diagnostic;
			return found;
		}

		bool TryFindAvailableLandingCraftForGeometry(Actor mcv, CPos objective,
			CPos pickupMcvCell, CPos pickupCraftCell, CPos landingCraftCell, CPos deployCell,
			out Actor craft, out SeaPlan plan, out bool hadPickupFailure, out bool hadCrossingFailure,
			out string diagnosticText)
		{
			craft = null;
			plan = default;
			hadPickupFailure = false;
			hadCrossingFailure = false;
			diagnosticText = null;

			// StrategicMap naval components are a cheap topology proof. If the cached pickup and
			// landing are not in the same known water component, never pay native A* for any LST.
			if (strategicMapService == null)
			{
				diagnosticText = "preconditions=Passed,geometry=Passed,topology=Failed(NoStrategicMapService),crafts=[none]";
				return false;
			}
			if (!strategicMapService.TryGetNavalRegionId(pickupCraftCell, out var ferryRegion))
			{
				diagnosticText = "preconditions=Passed,geometry=Passed,topology=Failed(PickupRegionUnknown),crafts=[none]";
				return false;
			}
			if (!strategicMapService.TryGetNavalRegionId(landingCraftCell, out var landingRegion))
			{
				diagnosticText = $"preconditions=Passed,geometry=Passed,topology=Failed(LandingRegionUnknown,pickupRegion={ferryRegion}),crafts=[none]";
				return false;
			}
			if (ferryRegion != landingRegion)
			{
				diagnosticText = $"preconditions=Passed,geometry=Passed,topology=Failed(RegionMismatch:{ferryRegion}!={landingRegion}),crafts=[none]";
				return false;
			}

			var diagnostics = new Dictionary<Actor, LandingCraftEligibilityDiagnostic>();
			LandingCraftEligibilityDiagnostic GetDiagnostic(Actor candidate, string origin)
			{
				if (!diagnostics.TryGetValue(candidate, out var diagnostic))
				{
					diagnostic = new LandingCraftEligibilityDiagnostic(candidate, origin);
					diagnostics.Add(candidate, diagnostic);
				}
				else if (!diagnostic.Origin.Contains(origin))
					diagnostic.Origin += "+" + origin;

				return diagnostic;
			}

			string CompleteDiagnostic()
			{
				var craftDetails = diagnostics.Count == 0
					? "none"
					: string.Join(";", diagnostics.Values.OrderBy(diagnostic => diagnostic.Craft.ActorID));
				return $"preconditions=Passed,geometry=Passed(pickupMcv={pickupMcvCell},pickupCraft={pickupCraftCell},landing={landingCraftCell},deploy={deployCell}),topology=Passed(region={ferryRegion}),crafts=[{craftDetails}]";
			}

			var candidates = new List<Actor>();
			if (IsLiveOwnedLandingCraft(pendingMcvLandingCraftReservation))
			{
				var pendingDiagnostic = GetDiagnostic(pendingMcvLandingCraftReservation, "PendingReservation");
				var claimable = transportService.CanStrategicExpansionClaimTransport(pendingMcvLandingCraftReservation);
				pendingDiagnostic.Claim = claimable ? "Passed" : "Failed";
				if (claimable)
					candidates.Add(pendingMcvLandingCraftReservation);
				else
					pendingDiagnostic.Result = "Rejected";
			}

			combatIntelService.EnsureCurrentSnapshot();
			var ownedCandidates = new List<Actor>();
			foreach (var ownedCraft in combatIntelService.OwnedActors.Where(IsLiveOwnedLandingCraft))
			{
				var diagnostic = GetDiagnostic(ownedCraft, "OwnedSnapshot");
				var claimable = transportService.CanStrategicExpansionClaimTransport(ownedCraft);
				diagnostic.Claim = claimable ? "Passed" : "Failed";
				if (!claimable)
				{
					diagnostic.Result = "Rejected";
					continue;
				}

				var ownedCargo = ownedCraft.TraitOrDefault<Cargo>();
				var cargoEligible = ownedCargo != null && !ownedCargo.IsTraitDisabled && ownedCargo.IsEmpty();
				diagnostic.Cargo = cargoEligible ? "Passed(Empty)" : ownedCargo == null
					? "Failed(Missing)"
					: ownedCargo.IsTraitDisabled ? "Failed(Disabled)" : "Failed(Loaded)";
				if (cargoEligible)
					ownedCandidates.Add(ownedCraft);
				else
					diagnostic.Result = "Rejected";
			}

			candidates.AddRange(ownedCandidates
				.OrderBy(a => (a.Location - mcv.Location).LengthSquared)
				.ThenBy(a => a.ActorID));

			// Only naval connectivity depends on which physical LST is selected. The MCV-side
			// pickup, landing handoff and FACT deploy cell are already cached above. This reduces
			// each candidate from a complete amphibious replan to two bounded naval path proofs.
			foreach (var candidate in candidates.Distinct()
				.Take(Math.Max(1, transportService?.MaximumLandingCraftPool ?? 1)))
			{
				var diagnostic = GetDiagnostic(candidate, "Candidate");
				var cargo = candidate.TraitOrDefault<Cargo>();
				var craftMobile = candidate.TraitOrDefault<Mobile>();
				if (cargo == null)
				{
					diagnostic.Cargo = "Failed(Missing)";
					diagnostic.Result = "Rejected";
					continue;
				}
				if (cargo.IsTraitDisabled)
				{
					diagnostic.Cargo = "Failed(Disabled)";
					diagnostic.Result = "Rejected";
					continue;
				}
				if (!cargo.IsEmpty())
				{
					diagnostic.Cargo = "Failed(Loaded)";
					diagnostic.Result = "Rejected";
					continue;
				}
				diagnostic.Cargo = "Passed(Empty)";
				if (craftMobile == null)
				{
					diagnostic.Mobile = "Failed(Missing)";
					diagnostic.Result = "Rejected";
					continue;
				}
				if (craftMobile.IsTraitDisabled)
				{
					diagnostic.Mobile = "Failed(Disabled)";
					diagnostic.Result = "Rejected";
					continue;
				}
				if (craftMobile.IsTraitPaused)
				{
					diagnostic.Mobile = "Failed(Paused)";
					diagnostic.Result = "Rejected";
					continue;
				}
				diagnostic.Mobile = "Passed";
				if (!strategicMapService.TryGetNavalRegionId(craftMobile.ToCell, out var candidateRegion))
				{
					diagnostic.Region = "Failed(Unknown)";
					diagnostic.Result = "Rejected";
					continue;
				}
				if (candidateRegion != ferryRegion)
				{
					diagnostic.Region = $"Failed(Mismatch:{candidateRegion}!={ferryRegion})";
					diagnostic.Result = "Rejected";
					continue;
				}
				diagnostic.Region = $"Passed({candidateRegion})";

				var canEnterPickup = craftMobile.CanEnterCell(pickupCraftCell, check: BlockedByActor.Immovable);
				diagnostic.PickupEnter = canEnterPickup ? "Passed" : "Failed";
				if (!canEnterPickup)
				{
					hadPickupFailure = true;
					diagnostic.Result = "Rejected";
					continue;
				}
				var canStayAtPickup = craftMobile.CanStayInCell(pickupCraftCell);
				diagnostic.PickupStay = canStayAtPickup ? "Passed" : "Failed";
				if (!canStayAtPickup)
				{
					hadPickupFailure = true;
					diagnostic.Result = "Rejected";
					continue;
				}
				var hasPickupPath = TryFindNavalTransportPath(candidate, craftMobile, craftMobile.ToCell,
					pickupCraftCell, out var pickupSeaPathLength, out _, out var pickupPathFailure);
				diagnostic.PickupPath = hasPickupPath ? "Passed" : $"Failed({pickupPathFailure})";
				if (!hasPickupPath)
				{
					hadPickupFailure = true;
					diagnostic.Result = "Rejected";
					continue;
				}

				var hasCrossingPath = TryFindNavalTransportPath(candidate, craftMobile, pickupCraftCell,
					landingCraftCell, out var crossingSeaPathLength, out _, out var crossingPathFailure);
				diagnostic.CrossingPath = hasCrossingPath ? "Passed" : $"Failed({crossingPathFailure})";
				if (!hasCrossingPath)
				{
					hadCrossingFailure = true;
					diagnostic.Result = "Rejected";
					continue;
				}

				diagnostic.Result = "Selected";
				craft = candidate;
				plan = new SeaPlan(objective, deployCell, pickupMcvCell, pickupCraftCell, landingCraftCell,
					0, pickupSeaPathLength + crossingSeaPathLength);
				diagnosticText = CompleteDiagnostic();
				return true;
			}

			diagnosticText = CompleteDiagnostic();
			return false;
		}

		void SetCommittedSeaRecoveryPickup(CommittedSeaCorridorRecoveryState recovery,
			CPos pickupMcvCell, CPos pickupCraftCell, CPos[] pickupMcvPath,
			int pickupNavalRegion, bool usesOriginalPickup)
		{
			recovery.HasPickupCandidate = true;
			recovery.UsesOriginalPickup = usesOriginalPickup;
			recovery.PickupMcvCell = pickupMcvCell;
			recovery.PickupCraftCell = pickupCraftCell;
			recovery.PickupMcvPath = pickupMcvPath ?? [];
			recovery.PickupNavalRegion = pickupNavalRegion;
			recovery.EvidenceRiskRevision = riskModelService?.RiskRevision ?? -1;
			recovery.LandingSearch = new RoutineSeaOreSearchState(recovery.McvActorId, recovery.McvCell,
				strategicMapService?.TerrainKnowledgeVersion ?? -1, allowMapWideFallback: false,
				[new OreFieldCandidate(recovery.Objective, (recovery.Objective - recovery.McvCell).LengthSquared)]);
			recovery.ProposedLandingCraftCell = null;
			recovery.ProposedLandingExitCell = null;
			recovery.ProposedDeployCell = null;
			recovery.ProposedLandingPath = [];
		}

		void ClearCommittedSeaRecoveryPickup(CommittedSeaCorridorRecoveryState recovery)
		{
			recovery.HasPickupCandidate = false;
			recovery.UsesOriginalPickup = false;
			recovery.PickupNavalRegion = -1;
			recovery.EvidenceRiskRevision = -1;
			recovery.PickupMcvPath = [];
			recovery.LandingSearch = null;
			recovery.ProposedLandingCraftCell = null;
			recovery.ProposedLandingExitCell = null;
			recovery.ProposedDeployCell = null;
			recovery.ProposedLandingPath = [];
		}

		void PauseCommittedSeaCorridorRecoveryForOriginalEligibility()
		{
			var recovery = committedSeaCorridorRecovery;
			if (recovery == null || recovery.PausedForOriginalEligibility)
				return;

			recovery.PausedForOriginalEligibility = true;
			LogCommittedSeaCorridorRecovery("PausedForOriginalEligibility", recovery,
				null, null, null, null,
				"the ordinary corridor check had no exact pickup/crossing path result; the same recovery generation retains its lifetime, pass count and cursors until exact eligibility is observable",
				lastLandingCraftPlanDiagnostic);
		}

		void ResumeCommittedSeaCorridorRecoveryAfterExactFailure()
		{
			var recovery = committedSeaCorridorRecovery;
			if (recovery == null || !recovery.PausedForOriginalEligibility)
				return;

			recovery.PausedForOriginalEligibility = false;
			recovery.NextAdvanceTick = world.WorldTick +
				Math.Max(Info.ScanInterval, Info.CommittedSeaCorridorRecoveryInterval);
			LogCommittedSeaCorridorRecovery("ResumedExactPathFailure", recovery,
				null, null, null, null,
				"exact pickup/crossing failure is observable again; the retained recovery generation resumes without a new lifetime or pass budget",
				lastLandingCraftPlanDiagnostic);
		}

		void RejectCommittedSeaRecoveryLanding(CommittedSeaCorridorRecoveryState recovery)
		{
			recovery.ProposedLandingCraftCell = null;
			recovery.ProposedLandingExitCell = null;
			recovery.ProposedDeployCell = null;
			recovery.ProposedLandingPath = [];
			var proof = recovery.LandingSearch?.LandingProof;
			if (proof == null)
				return;

			// Crossing eligibility depends on the LST-side handoff cell, not which adjacent exit/deploy
			// pair happened to prove first. Once that handoff fails every physical LST, continue at
			// the next ranked handoff instead of spending more native path work on the same crossing.
			proof.ActiveBeach = null;
			proof.ActiveExitCells = [];
			proof.NextExitIndex = 0;
		}

		bool TryStartCommittedSeaCorridorRecovery(Actor mcv, Mobile mobile, CPos objective)
		{
			if (committedSeaCorridorRecovery != null)
				return false;

			if (!preferredRoutinePickupMcvCell.HasValue || !preferredRoutinePickupCraftCell.HasValue ||
				!seaLandingCraftCell.HasValue || !targetDeployCell.HasValue)
				return false;

			var originalPickupMcv = preferredRoutinePickupMcvCell.Value;
			var originalPickupCraft = preferredRoutinePickupCraftCell.Value;
			var originalLanding = seaLandingCraftCell.Value;
			var originalDeploy = targetDeployCell.Value;
			var alternativePickupBeaches = RankRoutinePickupHandoffs(mobile.ToCell, originalPickupCraft);
			var recoveryInterval = Math.Max(Info.ScanInterval, Info.CommittedSeaCorridorRecoveryInterval);
			var deadlineTick = Info.SeaTransportAbsoluteWaitWatchdogTicks > 0 && seaTransportWaitStartedTick >= 0
				? seaTransportWaitStartedTick + Info.SeaTransportAbsoluteWaitWatchdogTicks - Math.Max(1, Info.ScanInterval)
				: int.MaxValue;
			var availablePasses = deadlineTick == int.MaxValue
				? Info.CommittedSeaCorridorRecoveryMaximumPasses
				: Math.Max(0, (deadlineTick - world.WorldTick) / recoveryInterval);
			var maximumPasses = Math.Min(Info.CommittedSeaCorridorRecoveryMaximumPasses, availablePasses);
			var recovery = new CommittedSeaCorridorRecoveryState(expansionTask.Id, mcv.ActorID, mobile.ToCell, objective,
				originalPickupMcv, originalPickupCraft, originalLanding, originalDeploy, alternativePickupBeaches,
				world.WorldTick, deadlineTick, maximumPasses, world.WorldTick + recoveryInterval);
			committedSeaCorridorRecovery = recovery;

			// A crossing-only failure can reuse the already-proven pickup and begin with alternate
			// landing handoffs. A pickup failure skips straight to the bounded alternate-pickup scan.
			if (lastLandingCraftPlanHadCrossingFailure &&
				strategicMapService.TryGetNavalRegionId(originalPickupCraft, out var originalPickupRegion) &&
				HasRiskAwarePathBetweenCells(mcv, mobile, mobile.ToCell, originalPickupMcv,
					out _, out var originalPickupPath))
				SetCommittedSeaRecoveryPickup(recovery, originalPickupMcv, originalPickupCraft, originalPickupPath,
					originalPickupRegion, usesOriginalPickup: true);

			LogCommittedSeaCorridorRecovery("StillTemporarilyBlocked", recovery, null, null, null, null,
				$"persistent exact-path failure reached {Info.SeaTransportFeasibilityWatchdogTicks} WT; " +
				"the original corridor remains active while bounded same-objective recovery starts");
			return true;
		}

		bool IsCommittedSeaCorridorRecoveryGenerationCurrent(CommittedSeaCorridorRecoveryState recovery,
			Actor mcv, CPos objective, out string transition)
		{
			transition = null;
			if (recovery.TaskId != expansionTask.Id)
				transition = $"task changed {recovery.TaskId}->{expansionTask.Id}";
			else if (recovery.McvActorId != mcv.ActorID)
				transition = $"MCV assignment changed {recovery.McvActorId}->{mcv.ActorID}";
			else if (recovery.Objective != objective)
				transition = $"objective changed {recovery.Objective}->{objective}";
			else if (!preferredRoutinePickupMcvCell.HasValue || !preferredRoutinePickupCraftCell.HasValue ||
				!seaLandingCraftCell.HasValue || !targetDeployCell.HasValue)
				transition = "the committed corridor identity is no longer complete";
			else if (recovery.OriginalPickupMcvCell != preferredRoutinePickupMcvCell.Value ||
				recovery.OriginalPickupCraftCell != preferredRoutinePickupCraftCell.Value ||
				recovery.OriginalLandingCraftCell != seaLandingCraftCell.Value ||
				recovery.OriginalDeployCell != targetDeployCell.Value)
				transition = $"corridor changed pickupMcv={recovery.OriginalPickupMcvCell}->{preferredRoutinePickupMcvCell.Value}," +
					$"pickupCraft={recovery.OriginalPickupCraftCell}->{preferredRoutinePickupCraftCell.Value}," +
					$"landing={recovery.OriginalLandingCraftCell}->{seaLandingCraftCell.Value}," +
					$"deploy={recovery.OriginalDeployCell}->{targetDeployCell.Value}";

			return transition == null;
		}

		void RebaseCommittedSeaCorridorRecoverySource(CommittedSeaCorridorRecoveryState recovery,
			CPos currentMcvCell)
		{
			if (recovery.McvCell == currentMcvCell)
				return;

			var previousMcvCell = recovery.McvCell;
			recovery.McvCell = currentMcvCell;
			recovery.SourceRebases++;
			ClearCommittedSeaRecoveryPickup(recovery);
			if (recovery.SourceRebases == 1 || recovery.SourceRebases % 8 == 0)
				LogCommittedSeaCorridorRecovery("SourceEvidenceRebased", recovery,
					null, null, null, null,
					$"MCV source cell changed {previousMcvCell}->{currentMcvCell} (cumulative rebases={recovery.SourceRebases}) while task, actor, objective and cached corridor identity were unchanged; source-dependent evidence was invalidated while lifetime, passes and cursors remained cumulative");
		}

		bool TryAdvanceCommittedSeaRecoveryPickup(Actor mcv, Mobile mobile,
			CommittedSeaCorridorRecoveryState recovery, out bool exhausted)
		{
			exhausted = false;
			var nativeSearches = 0;
			var proofBudget = Math.Max(1, Info.SeaPickupPathProofsPerPlanningPass);
			while (nativeSearches < proofBudget)
			{
				if (recovery.NextPickupBeachIndex >= recovery.RankedAlternativePickupBeaches.Length)
				{
					exhausted = true;
					return false;
				}

				var beach = recovery.RankedAlternativePickupBeaches[recovery.NextPickupBeachIndex++];
				if (!strategicMapService.TryGetNavalRegionId(beach, out var pickupRegion))
					continue;
				var targets = PassengerAdjacentCells(beach)
					.Where(cell => strategicMapService.IsAmphibiousHandoff(cell, beach))
					.Where(cell => mobile.CanEnterCell(cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(cell))
					.OrderBy(cell => (cell - mobile.ToCell).LengthSquared)
					.ThenBy(cell => cell.X)
					.ThenBy(cell => cell.Y)
					.ToArray();
				if (targets.Length == 0)
					continue;

				var found = TryFindRiskAwarePathToAnyCell(mcv, mobile, mobile.ToCell, targets,
					out var pickupMcvCell, out var pickupMcvPath, out var nativeSearchExecuted);
				if (nativeSearchExecuted)
					nativeSearches++;
				if (!found)
					continue;

				SetCommittedSeaRecoveryPickup(recovery, pickupMcvCell, beach, pickupMcvPath,
					pickupRegion, usesOriginalPickup: false);
				return true;
			}

			exhausted = recovery.NextPickupBeachIndex >= recovery.RankedAlternativePickupBeaches.Length;
			return false;
		}

		bool CompleteCommittedSeaCorridorRecoveryNoExecutable(IBot bot,
			CommittedSeaCorridorRecoveryState recovery, string reason)
		{
			MarkExpansionAreaCooldown(recovery.Objective, Info.FailedFieldRetryDelay,
				$"bounded committed ferry-corridor recovery: {reason}");
			LogCommittedSeaCorridorRecovery("NoExecutableCorridor", recovery, null, null, null, null, reason);
			AbortExpansionTaskToIdle(bot, $"bounded committed ferry-corridor recovery: {reason}", recovery.Objective);
			nextSeaPlanningTick = world.WorldTick + Info.SeaPlanningInterval;
			committedSeaCorridorRecovery = null;
			seaExactPathFailureStartedTick = -1;
			return true;
		}

		bool TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(IBot bot,
			CommittedSeaCorridorRecoveryState recovery)
		{
			if (recovery.PassesCompleted < recovery.MaximumPasses && world.WorldTick <= recovery.DeadlineTick)
				return false;

			var reason = world.WorldTick > recovery.DeadlineTick
				? "the recovery deadline was reached before the absolute watchdog"
				: $"the bounded {recovery.MaximumPasses}-pass recovery budget was exhausted before the absolute watchdog";
			return CompleteCommittedSeaCorridorRecoveryNoExecutable(bot, recovery, reason);
		}

		bool IsCommittedSeaRecoveryEvidenceCurrent(Actor mcv, Mobile mobile,
			CommittedSeaCorridorRecoveryState recovery, out string failure)
		{
			failure = null;
			if (!IsPioneerPathEvidenceCurrent(mcv, mobile, recovery.McvCell, recovery.McvCell,
				recovery.PickupMcvCell, recovery.PickupMcvPath, out failure))
			{
				failure = "Pickup" + failure;
				return false;
			}
			if (!recovery.ProposedLandingCraftCell.HasValue || !recovery.ProposedLandingExitCell.HasValue ||
				!recovery.ProposedDeployCell.HasValue || recovery.ProposedLandingPath.Length == 0)
			{
				failure = "LandingEvidenceMissing";
				return false;
			}

			var landing = recovery.ProposedLandingCraftCell.Value;
			var exit = recovery.ProposedLandingExitCell.Value;
			var deploy = recovery.ProposedDeployCell.Value;
			if (!world.Map.Contains(landing) || !world.Map.Contains(exit) || !world.Map.Contains(deploy))
				failure = "LandingOffMap";
			else if (strategicMapService == null || !strategicMapService.IsAmphibiousHandoff(exit, landing) ||
				!IsCellInNavalRegion(landing, recovery.PickupNavalRegion))
				failure = "LandingShoreOrRegion";
			else if (!mobile.CanEnterCell(exit, check: BlockedByActor.Immovable) || !mobile.CanStayInCell(exit))
				failure = "LandingExitBlocked";
			else if (!IsPioneerPathEvidenceCurrent(mcv, mobile, recovery.McvCell, exit,
				deploy, recovery.ProposedLandingPath, out failure))
				failure = "Landing" + failure;

			return failure == null;
		}

		bool TryAdvanceCommittedSeaCorridorRecovery(IBot bot, Actor mcv, Mobile mobile, CPos objective)
		{
			if (committedSeaCorridorRecovery == null)
			{
				if (!TryStartCommittedSeaCorridorRecovery(mcv, mobile, objective))
					return false;
			}
			else if (!IsCommittedSeaCorridorRecoveryGenerationCurrent(committedSeaCorridorRecovery,
				mcv, objective, out var generationTransition))
			{
				LogCommittedSeaCorridorRecovery("GenerationReplaced", committedSeaCorridorRecovery,
					null, null, null, null,
					$"a materially new recovery generation is required because {generationTransition}");
				committedSeaCorridorRecovery = null;
				lastCommittedSeaCorridorRecoveryDiagnosticSignature = null;
				if (!TryStartCommittedSeaCorridorRecovery(mcv, mobile, objective))
					return false;
			}

			var recovery = committedSeaCorridorRecovery;
			if (TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery))
				return true;
			RebaseCommittedSeaCorridorRecoverySource(recovery, mobile.ToCell);

			recovery.PassesCompleted++;
			recovery.NextAdvanceTick = world.WorldTick + Math.Max(Info.ScanInterval, Info.CommittedSeaCorridorRecoveryInterval);
			var currentRiskRevision = riskModelService?.RiskRevision ?? -1;
			var currentTerrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			if (recovery.HasPickupCandidate && (recovery.EvidenceRiskRevision != currentRiskRevision ||
				recovery.LandingSearch?.TerrainKnowledgeVersion != currentTerrainVersion))
			{
				// Invalidate only risk/terrain-dependent positive landing evidence. Keep the recovery
				// owner, deadline, pass count and pickup cursor so unrelated revisions cannot restart it.
				if (!IsPioneerPathEvidenceCurrent(mcv, mobile, recovery.McvCell, recovery.McvCell,
					recovery.PickupMcvCell, recovery.PickupMcvPath))
					ClearCommittedSeaRecoveryPickup(recovery);
				else
					SetCommittedSeaRecoveryPickup(recovery, recovery.PickupMcvCell, recovery.PickupCraftCell,
						recovery.PickupMcvPath, recovery.PickupNavalRegion, recovery.UsesOriginalPickup);
			}
			if (recovery.ProposedLandingCraftCell.HasValue && recovery.ProposedDeployCell.HasValue)
			{
				if (!IsCommittedSeaRecoveryEvidenceCurrent(mcv, mobile, recovery, out var staleEvidence))
				{
					LogCommittedSeaCorridorRecovery("StillTemporarilyBlocked", recovery,
						recovery.PickupMcvCell, recovery.PickupCraftCell,
						recovery.ProposedLandingCraftCell, recovery.ProposedDeployCell,
						$"replacement evidence changed before exact LST eligibility: {staleEvidence}");
					if (staleEvidence.StartsWith("Pickup", StringComparison.Ordinal))
						ClearCommittedSeaRecoveryPickup(recovery);
					else
						RejectCommittedSeaRecoveryLanding(recovery);
					return TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery);
				}
				if (!TryProveFutureExpansionRefineryPlacement(mcv, recovery.ProposedDeployCell.Value,
					out _, out _))
				{
					RejectCommittedSeaRecoveryLanding(recovery);
					return TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery);
				}

				var found = TryFindAvailableLandingCraftForGeometry(mcv, objective,
					recovery.PickupMcvCell, recovery.PickupCraftCell,
					recovery.ProposedLandingCraftCell.Value, recovery.ProposedDeployCell.Value,
					out var craft, out var plan, out var pickupFailure, out var crossingFailure,
					out var eligibility);
				recovery.TestedCorridors++;
				if (found)
				{
					if (!BeginMcvSeaCrossing(bot, mcv, mobile, craft, plan,
						"bounded post-commit recovery replaced a persistently non-executable cached ferry corridor"))
					{
						LogCommittedSeaCorridorRecovery("StillTemporarilyBlocked", recovery,
							recovery.PickupMcvCell, recovery.PickupCraftCell,
							recovery.ProposedLandingCraftCell, recovery.ProposedDeployCell,
							"replacement corridor is executable, but TransportCommander reservation was rejected",
							eligibility);
						return TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery);
					}

					lastLandingCraftPlanDiagnostic = eligibility;
					LogCommittedSeaCorridorRecovery("ReplannedExecutable", recovery,
						plan.PickupMcvCell, plan.PickupCraftCell, plan.LandingCraftCell, plan.DeployCell,
						"physical LST passed the bounded replacement pickup/crossing corridor", eligibility);
					LogCommittedSeaExecutionDiagnostic("ClaimedAndPickupStarted", craft,
						"bounded corridor recovery succeeded, TransportCommander reservation transferred, and native pickup moves were issued");
					committedSeaCorridorRecovery = null;
					seaExactPathFailureStartedTick = -1;
					return true;
				}

				LogCommittedSeaCorridorRecovery("StillTemporarilyBlocked", recovery,
					recovery.PickupMcvCell, recovery.PickupCraftCell,
					recovery.ProposedLandingCraftCell, recovery.ProposedDeployCell,
					"replacement geometry did not pass current physical-LST exact eligibility", eligibility);
				if (crossingFailure)
					RejectCommittedSeaRecoveryLanding(recovery);
				else if (pickupFailure)
					ClearCommittedSeaRecoveryPickup(recovery);
				return TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery);
			}

			if (!recovery.HasPickupCandidate)
			{
				if (TryAdvanceCommittedSeaRecoveryPickup(mcv, mobile, recovery, out var pickupSearchExhausted))
				{
					LogCommittedSeaCorridorRecovery("StillTemporarilyBlocked", recovery,
						recovery.PickupMcvCell, recovery.PickupCraftCell, null, null,
						"alternate pickup proved; landing/deploy proof is deferred to a later bounded planning pass");
					return TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery);
				}

				if (!pickupSearchExhausted)
					return TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery);

				return CompleteCommittedSeaCorridorRecoveryNoExecutable(bot, recovery,
					"the original corridor remained in exact-path failure and the bounded same-objective pickup alternatives were exhausted");
			}

			var transformsInfo = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null || !world.Map.Rules.Actors.TryGetValue(transformsInfo.IntoActor, out var intoActor) ||
				intoActor.TraitInfoOrDefault<BuildingInfo>() is not BuildingInfo buildingInfo)
				return CompleteCommittedSeaCorridorRecoveryNoExecutable(bot, recovery,
					"the committed MCV no longer has executable deploy metadata");

			var excludedLandings = recovery.UsesOriginalPickup
				? new[] { recovery.OriginalLandingCraftCell }
				: null;
			var landingProtectors = GetOwnedSeaLandingProtectors();
			if (TryAdvanceRoutineSeaLandingProof(recovery.LandingSearch, mcv, mobile, objective,
				transformsInfo, intoActor, buildingInfo, recovery.PickupNavalRegion, landingProtectors,
				out var landingCraftCell, out var deployCell, out var landingSearchExhausted,
				out var landingExitCell, out var landingPath,
				perf: null, excludedLandingCraftCells: excludedLandings))
			{
				if (!TryProveFutureExpansionRefineryPlacement(mcv, deployCell, out _, out _))
				{
					RejectCommittedSeaRecoveryLanding(recovery);
					return TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery);
				}

				recovery.ProposedLandingCraftCell = landingCraftCell;
				recovery.ProposedLandingExitCell = landingExitCell;
				recovery.ProposedDeployCell = deployCell;
				recovery.ProposedLandingPath = landingPath;
				LogCommittedSeaCorridorRecovery("StillTemporarilyBlocked", recovery,
					recovery.PickupMcvCell, recovery.PickupCraftCell, landingCraftCell, deployCell,
					"replacement geometry proof completed; physical-LST exact eligibility is deferred to the next planning pass");
				return TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery);
			}

			if (landingSearchExhausted)
			{
				LogCommittedSeaCorridorRecovery("StillTemporarilyBlocked", recovery,
					recovery.PickupMcvCell, recovery.PickupCraftCell, null, null,
					"landing alternatives for this pickup were exhausted; bounded recovery advances to another pickup");
				ClearCommittedSeaRecoveryPickup(recovery);
			}

			return TryCompleteCommittedSeaCorridorRecoveryIfBudgetExhausted(bot, recovery);
		}

		bool TryPrepareCachedSeaGeometryForObjective(Actor mcv, Mobile mcvMobile, CPos objective)
		{
			var cached = targetResourceCenter.HasValue && targetResourceCenter.Value == objective &&
				targetDeployCell.HasValue && seaLandingCraftCell.HasValue &&
				preferredRoutinePickupMcvCell.HasValue && preferredRoutinePickupCraftCell.HasValue;
			if (cached)
			{
				var landCell = preferredRoutinePickupMcvCell.Value;
				var beach = preferredRoutinePickupCraftCell.Value;
				var landing = seaLandingCraftCell.Value;
				var sameKnownNavalRegion = strategicMapService != null &&
					strategicMapService.TryGetNavalRegionId(beach, out var pickupRegion) &&
					strategicMapService.TryGetNavalRegionId(landing, out var landingRegion) &&
					pickupRegion == landingRegion && !IsSeaTopologyFailureCached(objective, pickupRegion);
				if (world.Map.Contains(landCell) && world.Map.Contains(beach) && strategicMapService != null &&
					strategicMapService.IsAmphibiousHandoff(landCell, beach) && sameKnownNavalRegion &&
					mcvMobile.CanEnterCell(landCell, check: BlockedByActor.Immovable) && mcvMobile.CanStayInCell(landCell))
					return true;
			}

			// Coastal staging/repack can deliberately preserve only the committed ore objective.
			// Recreate missing geometry once here, cache it, and reuse it until the mission is
			// completed or genuinely invalidated. The cheap pickup/naval-region proof comes first,
			// so disconnected seas never reach expensive landing/deploy ranking.
			if (!TryAdvanceReachableRoutineSeaPickupProof(mcv, mcvMobile,
				out _, out _, out _, out _) ||
				!TryGetPreferredRoutinePickupNavalRegion(out var pickupNavalRegion))
				return false;
			if (IsSeaTopologyFailureCached(objective, pickupNavalRegion))
				return false;
			if (!HasKnownLandingShoreInNavalRegion(objective, pickupNavalRegion))
			{
				RememberSeaTopologyFailure(objective, pickupNavalRegion,
					"committed objective has no native-passable landing handoff in the pickup naval region");
				return false;
			}

			var transformsInfo = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null || !world.Map.Rules.Actors.TryGetValue(transformsInfo.IntoActor, out var intoActor))
				return false;
			var buildingInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return false;

			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			var movementToleranceSquared = Info.RoutineSeaOreSearchMovementTolerance * Info.RoutineSeaOreSearchMovementTolerance;
			var landingStateMatches = committedSeaGeometrySearch != null &&
				committedSeaGeometrySearch.McvActorId == mcv.ActorID &&
				committedSeaGeometrySearch.TerrainKnowledgeVersion == terrainVersion &&
				(committedSeaGeometrySearch.McvCell - mcvMobile.ToCell).LengthSquared <= movementToleranceSquared &&
				committedSeaGeometrySearch.Candidates.Length == 1 &&
				committedSeaGeometrySearch.Candidates[0].ResourceCenter == objective;
			if (!landingStateMatches)
				committedSeaGeometrySearch = new RoutineSeaOreSearchState(mcv.ActorID, mcvMobile.ToCell,
					terrainVersion, allowMapWideFallback: false,
					[new OreFieldCandidate(objective, (objective - mcvMobile.ToCell).LengthSquared)])
				{
					PickupProven = true
				};

			var landingProtectors = GetOwnedSeaLandingProtectors();
			if (!TryAdvanceRoutineSeaLandingProof(committedSeaGeometrySearch, mcv, mcvMobile, objective,
				transformsInfo, intoActor, buildingInfo, pickupNavalRegion, landingProtectors,
				out var landingCraftCell, out var deployCell, out var landingSearchExhausted))
			{
				if (landingSearchExhausted)
					RememberSeaLandingProofFailure(objective, pickupNavalRegion);
				return false;
			}

			targetResourceCenter = objective;
			targetDeployCell = deployCell;
			seaLandingCraftCell = landingCraftCell;
			committedSeaGeometrySearch = null;
			FransBotLog.BotDebug(world,
				"{0}: SIMPLE FERRY caches one amphibious geometry plan for committed ore {1}: MCV pickup {2}, LST pickup {3}, landing {4}, deploy {5}. Free LST candidates now test naval connectivity only.",
				player, objective, preferredRoutinePickupMcvCell.Value, preferredRoutinePickupCraftCell.Value,
				landingCraftCell, deployCell);
			return true;
		}

		bool TryGetNavalRegionNearActor(Actor actor, out int navalRegion)
		{
			navalRegion = -1;
			if (actor == null || !actor.IsInWorld || actor.IsDead || actor.OccupiesSpace == null || strategicMapService == null)
				return false;

			var location = actor.Location;
			if (strategicMapService.TryGetNavalRegionId(location, out navalRegion))
				return true;

			foreach (var cell in world.Map.FindTilesInCircle(location, 3)
				.Where(world.Map.Contains)
				.OrderBy(c => (c - location).LengthSquared)
				.ThenBy(c => c.X)
				.ThenBy(c => c.Y))
				if (strategicMapService.TryGetNavalRegionId(cell, out navalRegion))
					return true;

			return false;
		}

		bool TryGetRegionBoundProductionQueueNavalRegion(ProductionQueue queue, string craftType,
			out int navalRegion, out Actor boundProducer)
		{
			navalRegion = -1;
			boundProducer = null;
			if (queue == null || !queue.Enabled || !world.Map.Rules.Actors.TryGetValue(craftType, out var actorInfo) ||
				actorInfo.TraitInfoOrDefault<BuildableInfo>() is not BuildableInfo buildable)
				return false;

			var productionType = buildable.BuildAtProductionType ?? queue.Info.Type;
			if (!queue.Actor.TraitsImplementing<Production>()
				.Any(production => production.Info.Produces.Contains(productionType)))
				return false;

			boundProducer = queue.Actor;
			return TryGetNavalRegionNearActor(boundProducer, out navalRegion);
		}

		Actor[] GetEligibleLandingCraftProducers(IEnumerable<ProductionQueue> shipQueues, string craftType,
			int requiredNavalRegion)
		{
			var queues = shipQueues.Where(queue => queue.Enabled &&
				queue.BuildableItems().Any(item => item.Name == craftType)).ToArray();
			var productionType = world.Map.Rules.Actors[craftType].TraitInfo<BuildableInfo>().BuildAtProductionType ??
				queues.Select(queue => queue.Info.Type).FirstOrDefault();
			var boundProducers = queues
				.Where(queue => TryGetRegionBoundProductionQueueNavalRegion(queue, craftType, out var region, out _) &&
					region == requiredNavalRegion)
				.Where(queue => queue.Actor.TraitsImplementing<Production>().Any(production =>
					!production.IsTraitDisabled && !production.IsTraitPaused && production.Info.Produces.Contains(productionType)))
				.Select(queue => queue.Actor);
			var sharedProductionTypes = queues
				.Where(queue => !TryGetRegionBoundProductionQueueNavalRegion(queue, craftType, out _, out _))
				.Select(queue => world.Map.Rules.Actors[craftType].TraitInfo<BuildableInfo>().BuildAtProductionType ?? queue.Info.Type)
				.ToHashSet();
			var sharedQueueProducers = world.ActorsWithTrait<Production>()
				.Where(pair => pair.Actor.Owner == player && pair.Actor.IsInWorld && !pair.Actor.IsDead &&
					!pair.Trait.IsTraitDisabled && !pair.Trait.IsTraitPaused &&
					pair.Trait.Info.Produces.Any(sharedProductionTypes.Contains) &&
					TryGetNavalRegionNearActor(pair.Actor, out var region) && region == requiredNavalRegion)
				.Select(pair => pair.Actor);
			return boundProducers.Concat(sharedQueueProducers)
				.Distinct()
				.OrderBy(actor => actor.ActorID)
				.ToArray();
		}

		bool TrySelectLandingCraftProductionQueue(IEnumerable<ProductionQueue> shipQueues, string craftType,
			int requiredNavalRegion, out ProductionQueue queue, out string producerBinding, out Actor[] producerCandidates)
		{
			var eligibleProducerCandidates = GetEligibleLandingCraftProducers(shipQueues, craftType, requiredNavalRegion);
			producerCandidates = eligibleProducerCandidates;
			queue = shipQueues
				.Where(q => TryGetRegionBoundProductionQueueNavalRegion(q, craftType, out var region, out _) &&
					region == requiredNavalRegion)
				.Where(q => eligibleProducerCandidates.Contains(q.Actor))
				.Where(q => q.BuildableItems().Any(item => item.Name == craftType))
				.OrderBy(q => q.AllQueued().Count())
				.ThenBy(q => q.Actor.ActorID)
				.FirstOrDefault();
			if (queue != null)
			{
				producerBinding = "RegionBound";
				return true;
			}

			queue = shipQueues
				.Where(q => !TryGetRegionBoundProductionQueueNavalRegion(q, craftType, out _, out _))
				.Where(q => q.BuildableItems().Any(item => item.Name == craftType))
				.OrderBy(q => q.AllQueued().Count())
				.ThenBy(q => q.Actor.ActorID)
				.FirstOrDefault();
			producerBinding = "UnboundUntilDelivery";
			return queue != null && eligibleProducerCandidates.Length > 0;
		}

		bool HasUsableLandingCraftProducerForCurrentDemand()
		{
			return TryGetRequiredLandingCraftProductionRegion(out var requiredNavalRegion)
				? HasOwnedLandingCraftProducer(requiredNavalRegion)
				: HasOwnedLandingCraftProducer();
		}

		bool HasOwnedLandingCraftProducer() => HasOwnedLandingCraftProducer(null);

		bool HasOwnedLandingCraftProducer(int? requiredNavalRegion) =>
			world.ActorsHavingTrait<Building>().Any(a => a.IsInWorld && !a.IsDead && a.Owner == player &&
				Info.LandingCraftProducerTypes.Contains(a.Info.Name) &&
				(!requiredNavalRegion.HasValue ||
				 (TryGetNavalRegionNearActor(a, out var region) && region == requiredNavalRegion.Value)));

		bool CanPlaceAnyLandingCraftProducerFromCurrentBase() => CanPlaceAnyLandingCraftProducerFromCurrentBase(null);

		bool CanPlaceAnyLandingCraftProducerFromCurrentBase(int? requiredNavalRegion)
		{
			var buildingQueues = AIUtils.FindQueuesByCategory(player)[Info.BuildingQueueCategory]
				.Where(q => q.Enabled)
				.ToArray();
			foreach (var type in Info.LandingCraftProducerTypes.OrderBy(x => x))
			{
				var buildableOrQueued = buildingQueues.Any(q =>
					q.BuildableItems().Any(item => item.Name == type) ||
					q.AllQueued().Any(item => item.Item == type));
				if (buildableOrQueued && FindLandingCraftProducerLocation(type, requiredNavalRegion).HasValue)
					return true;
			}

			return false;
		}

		bool TryBeginCoastalStaging(IBot bot, Actor mcv, Mobile mobile,
			int? requiredNavalRegion = null, CPos? supportObjective = null)
		{
			if (world.WorldTick < nextCoastalStagingSearchTick)
				return false;
			nextCoastalStagingSearchTick = world.WorldTick + Info.LandingCraftProducerPlacementScanInterval;

			var firstRefineryNeedsQueueYield = firstExpansionRefineryReservationActive && !firstExpansionRefineryReservationCompleted;
			bool foundCoastalStagingCell;
			CPos deployCell;
			using (FransBotLog.Profile(world, player, "MCV.CoastalStagingSearch"))
				foundCoastalStagingCell = TryFindCoastalStagingDeployCell(mcv, mobile, out deployCell, requiredNavalRegion);
			if (!foundCoastalStagingCell)
			{
				if (firstRefineryNeedsQueueYield)
					FransBotLog.BotDebug(world,
						"{0}: NAVAL SUPPORT coastal staging found no safe reachable FACT cell this pass; the first-expansion PROC keeps its queue until a concrete support route is selected. Another bounded coast search may occur after {1} WT.",
						player, Info.LandingCraftProducerPlacementScanInterval);
				return false;
			}

			if (firstRefineryNeedsQueueYield)
				SuspendFirstExpansionRefineryForInfrastructure(bot, "a safe reachable coastal staging FACT has been selected and naval infrastructure now needs the shared Building queue");

			// Coastal bootstrap temporarily needs targetResourceCenter/targetDeployCell for its own FACT.
			// Preserve a committed routine ferry's actual ore objective across that temporary transform,
			// then restore it when the coastal FACT repacks. E6 likewise never replaces the passenger's
			// mission target merely because transport infrastructure has to be acquired first.
			var preserveRoutineObjective = expansionTask.Mode == ExpansionTaskMode.SeaOre && targetResourceCenter.HasValue;
			var preservedRoutineObjective = preserveRoutineObjective ? targetResourceCenter : supportObjective;
			var preservedRoutineReservationTick = preserveRoutineObjective
				? targetReservationStartedTick
				: supportObjective.HasValue ? world.WorldTick : -1;
			coastalStagingPreservedCommittedSeaTask = preserveRoutineObjective;
			coastalStagingRequiredNavalRegion = requiredNavalRegion;
			if (!preserveRoutineObjective)
				coastalStagingFailedAttempts = 0;
			ResetSeaMission(clearTarget: true);
			if (preserveRoutineObjective)
			{
				// Same strategic expansion, different execution leg: keep the task id and preserve
				// the real ore objective while a temporary coastal FACT creates naval build radius.
				ChangeExpansionTaskMode(ExpansionTaskMode.CoastalStaging,
					"temporary coastal FACT is infrastructure for the already-selected sea ore");
				targetResourceCenter = deployCell;
				targetDeployCell = deployCell;
				targetReservationStartedTick = world.WorldTick;
				stage = ExpansionStage.MovingToOre;
				ResetTaskExecutionProgress();
			}
			else if (!BeginExpansionTask(ExpansionTaskMode.CoastalStaging, deployCell, deployCell,
				ExpansionStage.MovingToOre, world.WorldTick,
				"temporary coastal FACT is infrastructure-only naval bootstrap"))
				return false;
			deferredRoutineFerryObjective = preservedRoutineObjective;
			deferredRoutineFerryReservationStartedTick = preservedRoutineReservationTick;
			coastalStagingReturnToSea = false;
			coastalStagingRepackOutcome = CoastalStagingRepackOutcome.None;
			coastalStagingNavalNoProgressSinceTick = -1;
			FransBotLog.BotDebug(world,
				preserveRoutineObjective
					? "{0}: coastal support sends MCV {1} to temporary FACT {2}; an already-committed sea objective lost actionable naval infrastructure and keeps its strategic ownership during recovery."
					: supportObjective.HasValue
						? "{0}: coastal support sends PIONEER MCV {1} to temporary FACT {2}; candidate sea ore is NOT committed. This support task must prove/build SPEN/SYRD and LST supply first."
						: "{0}: proactive naval bootstrap sends PIONEER MCV {1} to temporary FACT {2}; this is infrastructure-only and bounded, not an ore expansion success.",
				player, mcv, deployCell);

			// Coastal staging is not an ore claim. The destination is already restricted to
			// known, reachable, non-critical terrain by TryFindCoastalStagingDeployCell.
			nextRouteRecheckTick = world.WorldTick + Info.RouteRecheckInterval;
			if (TryYieldToEarlierAlliedMcvReservation(bot))
				return false;
			QueueRiskAwareMove(mcv, mobile, deployCell);
			return true;
		}

		bool TryRetargetFailedCoastalStaging(IBot bot, Actor mcv, Mobile mobile)
		{
			var requiredNavalRegion = 0;
			var hasRequiredRegion = coastalStagingRequiredNavalRegion.HasValue;
			if (hasRequiredRegion)
				requiredNavalRegion = coastalStagingRequiredNavalRegion.Value;
			else
				hasRequiredRegion = TryGetPreferredRoutinePickupNavalRegion(out requiredNavalRegion);
			var hasUsableProducer = hasRequiredRegion
				? HasOwnedLandingCraftProducer(requiredNavalRegion)
				: HasOwnedLandingCraftProducer();
			if (!coastalStagingForSeaExpansion || mcv == null || mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused || hasUsableProducer)
				return false;

			if (!TryFindCoastalStagingDeployCell(mcv, mobile, out var deployCell,
				hasRequiredRegion ? requiredNavalRegion : null))
			{
				coastalStagingFailedAttempts++;
				if (coastalStagingFailedAttempts >= Info.CoastalStagingMaximumFailedAttempts)
				{
					var failedAttempts = coastalStagingFailedAttempts;
					var releasedObjective = deferredRoutineFerryObjective;
					if (releasedObjective.HasValue)
						MarkExpansionAreaCooldown(releasedObjective.Value, Info.ExpansionTargetFailureCooldownTicks,
							$"coastal support found no fully-proved FACT->SPEN/SYRD alternative for {failedAttempts} bounded retries");
					ReturnExpansionTaskToIdle(
						$"coastal support exhausted {failedAttempts}/{Info.CoastalStagingMaximumFailedAttempts} bounded placement proofs; PIONEER is released");
					nextCoastalStagingSearchTick = world.WorldTick + Info.ExpansionTargetFailureCooldownTicks;
					nextLandExpansionPlanningTick = world.WorldTick;
					if (releasedObjective.HasValue && activePioneerObjective.HasValue)
						AbandonActivePioneerObjective(
							"coastal support search exhausted bounded alternatives; same strategic area cools down", mcv);
					FransBotLog.BotDebug(world,
						"{0}: COASTAL SUPPORT SEARCH ABORTS after {1} bounded no-proof/rejected attempts. PIONEER MCV {2} returns to ordinary duty; candidate ore {3} no longer monopolizes the expansion role.",
						player, failedAttempts, mcv,
						releasedObjective.HasValue ? releasedObjective.Value.ToString() : "none");
					return false;
				}

				nextCoastalStagingSearchTick = world.WorldTick + Info.LandingCraftProducerPlacementScanInterval;
				FransBotLog.BotDebug(world,
					"{0}: coastal support retry found no alternative fully-proved FACT->SPEN/SYRD shoreline cell this pass ({1}/{2}). The bounded support episode retries after {3} WT instead of blocking PIONEER indefinitely.",
					player, coastalStagingFailedAttempts, Info.CoastalStagingMaximumFailedAttempts,
					Info.LandingCraftProducerPlacementScanInterval);
				return false;
			}

			targetResourceCenter = deployCell;
			targetDeployCell = deployCell;
			targetReservationStartedTick = world.WorldTick;
			stage = ExpansionStage.MovingToOre;
			coastalStagingNavalNoProgressSinceTick = -1;
			nextCoastalStagingSearchTick = world.WorldTick + Info.LandingCraftProducerPlacementScanInterval;
			ResetTaskExecutionProgress();
			nextRouteRecheckTick = world.WorldTick + Info.RouteRecheckInterval;
			QueueRiskAwareMove(mcv, mobile, deployCell);
			FransBotLog.BotDebug(world,
				"{0}: NAVAL SUPPORT coastal retry keeps EXPANSION TASK #{1} and retargets repacked MCV {2} to alternative staging FACT cell {3}. Failed staging is not treated as naval success and first-PROC suspension remains in force.",
				player, expansionTask.Id, mcv, deployCell);
			return true;
		}

		bool TryFindHypotheticalLandingCraftProducerFromStagingFact(CPos futureFactCell, int? requiredNavalRegion,
			out string producerType, out CPos producerCell)
		{
			producerType = null;
			producerCell = default;

			var buildingQueues = AIUtils.FindQueuesByCategory(player)[Info.BuildingQueueCategory]
				.Where(q => q.Enabled)
				.ToArray();
			foreach (var type in Info.LandingCraftProducerTypes.OrderBy(x => x))
			{
				var buildableOrQueued = buildingQueues.Any(q =>
					q.BuildableItems().Any(item => item.Name == type) ||
					q.AllQueued().Any(item => item.Item == type));
				if (!buildableOrQueued || !world.Map.Rules.Actors.TryGetValue(type, out var actorInfo))
					continue;

				var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
				if (buildingInfo == null)
					continue;

				foreach (var cell in world.Map.FindTilesInCircle(futureFactCell, Info.LandingCraftProducerSearchRadius)
					.Where(world.Map.Contains)
					.Where(c => (c - futureFactCell).LengthSquared > 1)
					.Where(c => !requiredNavalRegion.HasValue || PlacementTouchesNavalRegion(c, requiredNavalRegion.Value))
					.OrderBy(c => (c - futureFactCell).LengthSquared)
					.ThenBy(c => c.X)
					.ThenBy(c => c.Y))
				{
					if (!world.CanPlaceBuilding(cell, actorInfo, buildingInfo, null))
						continue;
					if (riskModelService.EvaluateStrategicCell(cell, FransRiskRole.BuildingPlacement, FransRiskTolerance.Cautious).IsCritical)
						continue;

					producerType = type;
					producerCell = cell;
					return true;
				}
			}

			return false;
		}

		bool TryFindCoastalStagingDeployCell(Actor mcv, Mobile mobile, out CPos deployCell, int? requiredNavalRegion = null)
		{
			deployCell = default;
			var transformsInfo = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null || !world.Map.Rules.Actors.TryGetValue(transformsInfo.IntoActor, out var intoActor))
				return false;
			var buildingInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return false;

			var cheapShortlistLimit = Math.Max(Info.CoastalStagingMaximumCandidates, Info.CoastalStagingMaximumCandidates * 4);
			// A staging FACT farther inland than the producer-placement scan can create a
			// false "coastal" success that still cannot reach water. Keep at least one
			// cell of margin for the water-side SPEN/SYRD footprint.
			var effectiveShoreRadius = Math.Min(Info.CoastalStagingShoreRadius,
				Math.Max(1, Info.LandingCraftProducerSearchRadius - 1));
			CPos[] candidateCells;
			using (FransBotLog.Profile(world, player, "MCV.CoastalStagingCandidateSnapshot"))
				candidateCells = RoutinePickupHandoffCells()
					.Where(c => !requiredNavalRegion.HasValue || IsCellInNavalRegion(c, requiredNavalRegion.Value))
					.Where(c => strategicMapService == null || strategicMapService.IsTerrainKnown(c))
					.SelectMany(beach => world.Map.FindTilesInCircle(beach, effectiveShoreRadius))
					.Where(world.Map.Contains)
					.Distinct()
					.Where(c => strategicMapService == null || strategicMapService.IsTerrainKnown(c))
					.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
					.Where(c => !IsFieldTemporarilyFailed(c))
					.OrderBy(c => (c - mcv.Location).LengthSquared)
					.ThenBy(c => c.X)
					.ThenBy(c => c.Y)
					.Take(cheapShortlistLimit)
					.Where(c => !IsMcvCriticalRisk(mcv, c, CurrentMcvRiskTolerance))
					.Where(c => world.CanPlaceBuilding(c + transformsInfo.Offset, intoActor, buildingInfo, mcv))
					.Take(Info.CoastalStagingMaximumCandidates)
					.ToArray();

			long bestScore = long.MaxValue;
			using (FransBotLog.Profile(world, player, "MCV.CoastalStagingCandidateEvaluation"))
			{
				foreach (var candidate in candidateCells)
				{
					var futureFactCell = candidate + transformsInfo.Offset;
					if (!TryFindHypotheticalLandingCraftProducerFromStagingFact(futureFactCell, requiredNavalRegion,
						out _, out _))
						continue;
					if (!TryFindRiskAwarePathToCell(mcv, mobile, candidate, out var path))
						continue;
					var routeRisk = riskModelService.EvaluateRoute(mcv, path, FransRiskRole.Mcv, CurrentMcvRiskTolerance);
					if (routeRisk.IsCritical)
						continue;

					var score = (long)path.Count * 10 + routeRisk.PeakScore * Info.CoastalStagingRiskWeight;
					if (score >= bestScore)
						continue;

					bestScore = score;
					deployCell = candidate;
				}
			}

			return bestScore != long.MaxValue;
		}

		void ApplySeaPlan(SeaPlan plan)
		{
			targetResourceCenter = plan.ResourceCenter;
			targetDeployCell = plan.DeployCell;
			targetReservationStartedTick = world.WorldTick;
			seaPickupMcvCell = plan.PickupMcvCell;
			seaPickupCraftCell = plan.PickupCraftCell;
			seaLandingCraftCell = plan.LandingCraftCell;
			nextSeaBoardingRetryTick = 0;
			nextSeaUnloadRetryTick = 0;
			nextSeaRouteRiskRecheckTick = 0;
			seaLastRiskRevision = riskModelService.RiskRevision;
			seaLastTransportLossExclusionRevision = generalService.TransportLossExclusionRevision;
			seaTransportLossBlockedRevision = -1;
		}

		void ResetSeaMoveProgress(Actor mcv, Mobile mcvMobile, Actor craft, Mobile craftMobile)
		{
			seaPickupMcvLastProgressCell = mcvMobile?.ToCell;
			seaPickupMcvLastProgressTick = world.WorldTick;
			seaPickupMcvStallRetries = 0;
			seaPickupApproachRejectedCells.Clear();
			seaPickupApproachRecoveryAttempts = 0;
			seaPickupCraftLastProgressCell = craftMobile?.ToCell;
			seaPickupCraftLastProgressTick = world.WorldTick;
			seaPickupCraftStallRetries = 0;
			seaTransportLastProgressCell = craftMobile?.ToCell;
			seaTransportLastProgressTick = world.WorldTick;
			seaTransportStallRetries = 0;
			ResetSeaUnloadRecovery();
		}

		void ResetSeaUnloadRecovery()
		{
			seaUnloadRecoveryPhase = SeaUnloadRecoveryPhase.NativeUnload;
			seaUnloadOriginalLandingCraftCell = null;
			seaUnloadExpectedExitCell = null;
			seaUnloadAttemptStartedTick = -1;
			seaUnloadRecoveryAttempts = 0;
			seaUnloadReturningToSource = false;
			seaUnloadMoveRejectedHandoffs.Clear();
			nextSeaUnloadRetryTick = 0;
			nextSeaCargoPreservedRecheckTick = 0;
		}

		static bool UpdateProgressCell(CPos current, ref CPos? lastCell, ref int lastProgressTick, int worldTick)
		{
			if (lastCell.HasValue && lastCell.Value == current)
				return false;
			lastCell = current;
			lastProgressTick = worldTick;
			return true;
		}

		bool BeginMcvSeaCrossing(IBot bot, Actor mcv, Mobile mcvMobile, Actor craft, SeaPlan plan, string reason)
		{
			var craftMobile = craft?.TraitOrDefault<Mobile>();
			if (craftMobile == null)
				return false;

			// The selected SeaPlan already proved both naval legs. Do not run the same A*
			// proof again here; reserve the craft and let native Move execute the cached leg.
			if (!transportService.TryReserveStrategicExpansionTransport(craft, mcv))
				return false;

			// The committed task leaves WaitingForSeaTransport only after the physical LST
			// reservation is authoritative. A failed handoff must not erase the absolute
			// watchdog clock and silently grant the same objective another full wait window.
			seaTransportWaitStartedTick = -1;
			if (pendingMcvLandingCraftReservation == craft)
				pendingMcvLandingCraftReservation = null;
			activeLandingCraft = craft;
			activeLandingCraftReservationOwner = mcv;
			ApplySeaPlan(plan);
			ResetSeaMoveProgress(mcv, mcvMobile, craft, craftMobile);
			stage = ExpansionStage.MovingToSeaPickup;
			nextSeaRouteRiskRecheckTick = world.WorldTick + Info.SeaRouteRiskRecheckInterval;
			QueueRiskAwareMove(mcv, mcvMobile, plan.PickupMcvCell);
			QueueNavalTransportPlainMove(craft, craftMobile, plan.PickupCraftCell, routeAlreadyValidated: true);
			FransBotLog.BotDebug(world, "{0}: SIMPLE FERRY starts cached plan for ore {1}. MCV pickup {2}, LST pickup {3}, landing {4}; plain native LST Move owns execution and full replanning is stall/invalidity-only. {5}.", player, plan.ResourceCenter, plan.PickupMcvCell, plan.PickupCraftCell, plan.LandingCraftCell, reason);
			return true;
		}

		void ManageSeaPickup(IBot bot)
		{
			if (!IsLiveOwnedMcv(activeMcv) || !IsLiveOwnedLandingCraft(activeLandingCraft) ||
				!seaPickupMcvCell.HasValue || !seaPickupCraftCell.HasValue)
			{
				AbortSeaMissionBeforeLoad(bot);
				return;
			}

			var mcvMobile = activeMcv.TraitOrDefault<Mobile>();
			var craftMobile = activeLandingCraft.TraitOrDefault<Mobile>();
			if (mcvMobile == null || craftMobile == null)
			{
				AbortSeaMissionBeforeLoad(bot);
				return;
			}

			if (UpdateProgressCell(mcvMobile.ToCell, ref seaPickupMcvLastProgressCell, ref seaPickupMcvLastProgressTick, world.WorldTick))
				seaPickupMcvStallRetries = 0;
			if (UpdateProgressCell(craftMobile.ToCell, ref seaPickupCraftLastProgressCell, ref seaPickupCraftLastProgressTick, world.WorldTick))
				seaPickupCraftStallRetries = 0;

			var mcvAtPickup = mcvMobile.ToCell == seaPickupMcvCell.Value;
			var craftAtPickup = craftMobile.ToCell == seaPickupCraftCell.Value;
			if (!mcvAtPickup && craftAtPickup && activeMcv.IsIdle && activeLandingCraft.IsIdle &&
				PassengerAdjacentCells(craftMobile.ToCell).Contains(mcvMobile.ToCell))
			{
				var plannedPickup = seaPickupMcvCell.Value;
				seaPickupMcvCell = mcvMobile.ToCell;
				mcvAtPickup = true;
				FransBotLog.BotDebug(world,
					"{0}: [E25 PICKUP APPROACH] task={1} mcv={2} lst={3} outcome=AdjacentHandoff current={4} oldPickupMcv={5} newPickupMcv={4} pickupCraft={6} landing={7} ferryRetained=True corridorRetained=True; native EnterTransport accepts any adjacent land cell, so the exact cached land cell is not required.",
					player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID, mcvMobile.ToCell,
					plannedPickup, seaPickupCraftCell.Value, seaLandingCraftCell?.ToString() ?? "None");
			}

			// plain native LST Move runs without Frans RiskModel A* while progress continues.
			// Reissue only the current cached leg after a real no-cell-progress stall. After the
			// normal retries, keep the reserved ferry/corridor and replace only the land-side
			// approach cell when one currently clear adjacent route exists.
			if (!mcvAtPickup && seaPickupMcvLastProgressTick >= 0 &&
				world.WorldTick - seaPickupMcvLastProgressTick >= Info.SeaPlanningInterval)
			{
				if (seaPickupMcvStallRetries >= Info.MovingMcvStallMaximumRetries)
				{
					var oldPickup = seaPickupMcvCell.Value;
					var originalPathStillValid = HasRiskAwarePathBetweenCells(activeMcv, mcvMobile,
						mcvMobile.ToCell, oldPickup, out var originalPathLength);
					seaPickupApproachRejectedCells.Add(oldPickup);
					if (seaPickupApproachRecoveryAttempts < Info.SeaPickupApproachMaximumRecoveryAttempts &&
						TryFindCurrentExecutableAlternateSeaPickup(activeMcv, mcvMobile, seaPickupCraftCell.Value,
							out var alternatePickup, out var alternatePath))
					{
						seaPickupApproachRecoveryAttempts++;
						seaPickupMcvCell = alternatePickup;
						QueueStopOrder(bot, activeMcv);
						QueueMcvMoveAlongProvenPath(activeMcv, mcvMobile, alternatePickup, alternatePath,
							"SeaPickupApproachRecovery");
						seaPickupMcvLastProgressCell = mcvMobile.ToCell;
						seaPickupMcvLastProgressTick = world.WorldTick;
						seaPickupMcvStallRetries = 0;
						FransBotLog.BotDebug(world,
							"{0}: [E25 PICKUP APPROACH] task={1} mcv={2} lst={3} outcome=PickupApproachReplanned current={4} oldPickupMcv={5} newPickupMcv={6} pickupCraft={7} landing={8} noCellProgressWT={9} oldFreshPath={10} oldPathCells={11} newPathCells={12} recovery={13}/{14} ferryRetained=True corridorRetained=True.",
							player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID, mcvMobile.ToCell,
							oldPickup, alternatePickup, seaPickupCraftCell.Value,
							seaLandingCraftCell?.ToString() ?? "None", Info.SeaPlanningInterval,
							originalPathStillValid, originalPathStillValid ? originalPathLength : 0,
							alternatePath.Length, seaPickupApproachRecoveryAttempts,
							Info.SeaPickupApproachMaximumRecoveryAttempts);
						return;
					}

					FransBotLog.BotDebug(world,
						"{0}: [E25 PICKUP APPROACH] task={1} mcv={2} lst={3} outcome=PickupApproachRecoveryExhausted current={4} pickupMcv={5} pickupCraft={6} landing={7} noCellProgressWT={8} retries={9} recovery={10}/{11} oldFreshPath={12} oldPathCells={13}; no currently clear task-scoped alternate beside the same ferry pickup exists. Action=release pre-load LST and reacquire transport for the SAME ExpansionTask/objective without poisoning the shoreline.",
						player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID, mcvMobile.ToCell,
						oldPickup, seaPickupCraftCell.Value, seaLandingCraftCell?.ToString() ?? "None",
						Info.SeaPlanningInterval, seaPickupMcvStallRetries, seaPickupApproachRecoveryAttempts,
						Info.SeaPickupApproachMaximumRecoveryAttempts, originalPathStillValid,
						originalPathStillValid ? originalPathLength : 0);
					QueueStopOrder(bot, activeMcv);
					QueueStopOrder(bot, activeLandingCraft);
					ResetSeaMission(clearTarget: false);
					stage = ExpansionStage.WaitingForSeaTransport;
					seaTransportWaitStartedTick = world.WorldTick;
					nextSeaPlanningTick = world.WorldTick + 25;
					return;
				}

				QueueStopOrder(bot, activeMcv);
				QueueRiskAwareMove(activeMcv, mcvMobile, seaPickupMcvCell.Value);
				seaPickupMcvStallRetries++;
				seaPickupMcvLastProgressTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: [E25 PICKUP APPROACH] task={1} mcv={2} lst={3} outcome=PickupPathRefreshed current={4} pickupMcv={5} pickupCraft={6} noCellProgressWT={7} retry={8}/{9}; same pickup retained for transient blockage.",
					player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID, mcvMobile.ToCell,
					seaPickupMcvCell.Value, seaPickupCraftCell.Value, Info.SeaPlanningInterval,
					seaPickupMcvStallRetries, Info.MovingMcvStallMaximumRetries);
			}

			if (!craftAtPickup && seaPickupCraftLastProgressTick >= 0 &&
				world.WorldTick - seaPickupCraftLastProgressTick >= Info.SeaPlanningInterval)
			{
				if (seaPickupCraftStallRetries >= Info.MovingMcvStallMaximumRetries)
				{
					if (!TryFindNavalTransportPath(activeLandingCraft, craftMobile, craftMobile.ToCell, seaPickupCraftCell.Value, out _, out _))
					{
						FransBotLog.BotDebug(world, "{0}: SIMPLE FERRY aborts cached pickup: LST {1} has no valid path to rendezvous {2} after {3} bounded stall retries.",
							player, activeLandingCraft, seaPickupCraftCell.Value, seaPickupCraftStallRetries);
						MarkCurrentFieldFailed();
						AbortSeaMissionBeforeLoad(bot);
						return;
					}
					seaPickupCraftStallRetries = 0;
				}

				QueueStopOrder(bot, activeLandingCraft);
				QueueNavalTransportPlainMove(activeLandingCraft, craftMobile, seaPickupCraftCell.Value,
					routeAlreadyValidated: true);
				seaPickupCraftStallRetries++;
				seaPickupCraftLastProgressTick = world.WorldTick;
				FransBotLog.BotDebug(world, "{0}: SIMPLE FERRY LST {1} stalled {2} WT en route to pickup; reissuing only the cached movement leg ({3}/{4}), no ferry replan.",
					player, activeLandingCraft, Info.SeaPlanningInterval, seaPickupCraftStallRetries, Info.MovingMcvStallMaximumRetries);
			}

			if (!mcvAtPickup || !craftAtPickup || !activeMcv.IsIdle || !activeLandingCraft.IsIdle)
				return;

			stage = ExpansionStage.SeaLoading;
			nextSeaBoardingRetryTick = 0;
			seaBoardingLastProgressCell = activeMcv.Location;
			seaBoardingLastProgressTick = world.WorldTick;
			seaBoardingRecoveryAttempts = 0;
			IssueNativeMcvBoarding(bot);
		}

		bool TryFindCurrentExecutableAlternateSeaPickup(Actor mcv, Mobile mobile, CPos craftCell,
			out CPos alternatePickup, out CPos[] provenPath)
		{
			alternatePickup = default;
			provenPath = [];
			if (!IsLiveOwnedMcv(mcv) || mobile == null || !world.Map.Contains(craftCell))
				return false;

			var candidates = PassengerAdjacentCells(craftCell)
				.Where(cell => strategicMapService.IsAmphibiousHandoff(cell, craftCell))
				.Where(cell => !seaPickupApproachRejectedCells.Contains(cell))
				.Where(mobile.CanStayInCell)
				.OrderBy(cell => (cell - mobile.ToCell).LengthSquared)
				.ThenBy(cell => cell.X)
				.ThenBy(cell => cell.Y)
				.ToArray();
			if (candidates.Contains(mobile.ToCell) &&
				mobile.CanEnterCell(mobile.ToCell, mcv, BlockedByActor.All))
			{
				alternatePickup = mobile.ToCell;
				provenPath = [mobile.ToCell];
				return true;
			}

			var currentlyEnterable = candidates
				.Where(cell => mobile.CanEnterCell(cell, mcv, BlockedByActor.All))
				.ToArray();
			if (currentlyEnterable.Length == 0 || mobile.PathFinder is not PathFinder pathFinder)
				return false;

			var path = riskModelService.ExecuteWithPreparedPathCost(mcv,
				FransRiskRole.Mcv, CurrentMcvRiskTolerance, preparedPathCost =>
				{
					int CustomCost(CPos cell) => cell == mobile.ToCell ? 0 : preparedPathCost(cell);

					return pathFinder.FindPathToTargetCells(mcv, mobile.ToCell, currentlyEnterable,
						BlockedByActor.All, CustomCost, laneBias: false);
				});

			if (path == null || path.Count == 0 || !currentlyEnterable.Contains(path[0]))
				return false;
			for (var p = 0; p < path.Count - 1; p++)
				if (IsMcvCriticalRisk(mcv, path[p], CurrentMcvRiskTolerance))
					return false;

			alternatePickup = path[0];
			provenPath = path.ToArray();
			return true;
		}

		void QueueMcvMoveAlongProvenPath(Actor mcv, Mobile mobile, CPos destination,
			IReadOnlyCollection<CPos> targetToSourcePath, string reason)
		{
			if (destination == mobile.ToCell)
				return;

			var orderedPath = targetToSourcePath
				.Reverse()
				.Where(cell => cell != mobile.ToCell)
				.ToArray();
			if (orderedPath.Length == 0)
			{
				LogMcvMoveOrder(mcv, destination, 1, reason);
				QueueMoveOrder(null, mcv, destination);
				return;
			}

			const int MaximumMoveWaypoints = 4;
			var waypointCount = Math.Min(MaximumMoveWaypoints, orderedPath.Length);
			LogMcvMoveOrder(mcv, destination, waypointCount, reason);
			var queued = false;
			for (var i = 1; i <= waypointCount; i++)
			{
				var index = (int)((long)i * orderedPath.Length / waypointCount) - 1;
				QueueMoveOrder(null, mcv, orderedPath[index], queued);
				queued = true;
			}
		}

		void IssueNativeMcvBoarding(IBot bot)
		{
			if (!IsLiveOwnedMcv(activeMcv) || !activeMcv.IsInWorld || !IsLiveOwnedLandingCraft(activeLandingCraft) ||
				world.WorldTick < nextSeaBoardingRetryTick)
				return;

			var cargo = activeLandingCraft.TraitOrDefault<Cargo>();
			var passenger = activeMcv.TraitOrDefault<Passenger>();
			if (cargo == null || passenger == null || cargo.IsTraitDisabled ||
				!cargo.Info.Types.Contains(passenger.Info.CargoType) || !cargo.CanLoad(activeMcv) || !cargo.IsEmpty())
				return;
			if (passenger.ReservedCargo != null || !activeMcv.IsIdle || !activeLandingCraft.IsIdle)
				return;

			nextSeaBoardingRetryTick = world.WorldTick + Info.SeaBoardingRetryInterval;
			if (!seaBoardingLastProgressCell.HasValue || seaBoardingLastProgressTick < 0)
			{
				seaBoardingLastProgressCell = activeMcv.Location;
				seaBoardingLastProgressTick = world.WorldTick;
			}
			FransBotLog.BotDebug(world,
				"{0}: expansion MCV {1} boards reserved LST {2} using native EnterTransport; no direct Cargo.Load/World.Remove mutation remains in FransMcvExpansion.",
				player, activeMcv, activeLandingCraft);
			bot.QueueOrder(new Order("EnterTransport", activeMcv, Target.FromActor(activeLandingCraft), false));
		}

		void ManageSeaLoading(IBot bot)
		{
			if (!IsLiveOwnedLandingCraft(activeLandingCraft) || activeMcv == null || activeMcv.IsDead)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			var cargo = activeLandingCraft.TraitOrDefault<Cargo>();
			var passenger = activeMcv.TraitOrDefault<Passenger>();
			var mcvMobile = activeMcv.TraitOrDefault<Mobile>();
			if (cargo == null || passenger == null || mcvMobile == null)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			// Same completion test used by the proven E6 transport path: native EnterTransport must
			// produce both Passenger.Transport and Cargo.Passengers before the LST may depart.
			if (!activeMcv.IsInWorld && passenger.Transport == activeLandingCraft &&
				cargo.Passengers.Contains(activeMcv))
			{
				var completedBoardingRecoveryAttempts = seaBoardingRecoveryAttempts;
				if (!seaLandingCraftCell.HasValue)
				{
					FailSeaMissionAfterLoad(bot);
					return;
				}

				stage = ExpansionStage.SeaTransporting;
				seaBoardingLastProgressCell = null;
				seaBoardingLastProgressTick = -1;
				seaBoardingRecoveryAttempts = 0;
				FransBotLog.BotDebug(world,
					"{0}: [MCV FERRY PICKUP] task={1} mcv={2} lst={3} outcome=NativeBoardingSuccess pickup={4}/{5} recovery={6}/{7} cargo={8}; exact Passenger.Transport and Cargo.Passengers agree, and the SAME ExpansionTask/corridor sails to landing {9} under committed Balanced tolerance.",
					player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
					seaPickupMcvCell?.ToString() ?? "None",
					seaPickupCraftCell?.ToString() ?? activeLandingCraft.Location.ToString(),
					completedBoardingRecoveryAttempts, Info.SeaBoardingMaximumRecoveryAttempts,
					cargo.PassengerCount, seaLandingCraftCell.Value);
				var craftMobile = activeLandingCraft.TraitOrDefault<Mobile>();
				if (craftMobile == null)
				{
					FailSeaMissionAfterLoad(bot);
					return;
				}

				seaTransportLastProgressCell = craftMobile.ToCell;
				seaTransportLastProgressTick = world.WorldTick;
				seaTransportStallRetries = 0;
				seaLastRiskRevision = riskModelService.RiskRevision;
				seaLastTransportLossExclusionRevision = generalService.TransportLossExclusionRevision;
				seaTransportLossBlockedRevision = -1;
				QueueNavalTransportPlainMove(activeLandingCraft, craftMobile, seaLandingCraftCell.Value, routeAlreadyValidated: true);
				nextSeaRouteRiskRecheckTick = world.WorldTick + Info.SeaRouteRiskRecheckInterval;
				return;
			}

			if (!activeMcv.IsInWorld)
				return;

			if (!seaBoardingLastProgressCell.HasValue || seaBoardingLastProgressCell.Value != activeMcv.Location)
			{
				seaBoardingLastProgressCell = activeMcv.Location;
				seaBoardingLastProgressTick = world.WorldTick;
			}

			var nativeBoardingOwnsMcv = passenger.ReservedCargo != null || !activeMcv.IsIdle;
			if (nativeBoardingOwnsMcv && seaBoardingLastProgressTick >= 0 &&
				world.WorldTick - seaBoardingLastProgressTick < Info.SeaBoardingNoProgressTimeout)
				return;

			if (seaBoardingLastProgressTick >= 0 &&
				world.WorldTick - seaBoardingLastProgressTick >= Info.SeaBoardingNoProgressTimeout)
			{
				QueueStopOrder(bot, activeMcv);
				seaBoardingRecoveryAttempts++;
				FransBotLog.BotDebug(world,
					"{0}: [MCV FERRY PICKUP] task={1} mcv={2} lst={3} outcome=BoardingNoProgress pickup={4}/{5} recovery={6}/{7} noProgressWT={8} reservedCargoCleared={9} ferryRetained={10} corridorRetained={10}; native EnterTransport remained active/retrying without physical cell or Cargo progress.",
					player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
					seaPickupMcvCell?.ToString() ?? mcvMobile.ToCell.ToString(),
					seaPickupCraftCell?.ToString() ?? activeLandingCraft.Location.ToString(),
					seaBoardingRecoveryAttempts, Info.SeaBoardingMaximumRecoveryAttempts,
					Info.SeaBoardingNoProgressTimeout,
					passenger.ReservedCargo == null,
					seaBoardingRecoveryAttempts <= Info.SeaBoardingMaximumRecoveryAttempts);
				if (seaBoardingRecoveryAttempts > Info.SeaBoardingMaximumRecoveryAttempts)
				{
					FransBotLog.BotDebug(world,
						"{0}: [MCV FERRY PICKUP] task={1} mcv={2} lst={3} outcome=BoardingRecoveryExhausted pickup={4}/{5} recovery={6}/{6}; native EnterTransport made no physical progress, so pre-load ownership is released and the SAME ExpansionTask/objective returns to transport acquisition.",
						player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
						seaPickupMcvCell?.ToString() ?? "None",
						seaPickupCraftCell?.ToString() ?? activeLandingCraft.Location.ToString(),
						Info.SeaBoardingMaximumRecoveryAttempts);
					ResetSeaMission(clearTarget: false);
					stage = ExpansionStage.WaitingForSeaTransport;
					seaTransportWaitStartedTick = world.WorldTick;
					nextSeaPlanningTick = world.WorldTick + 25;
					return;
				}

				if (TryShiftSeaPickupMcvCell(activeMcv, mcvMobile, out var alternatePickup))
				{
					var previousPickup = seaPickupMcvCell;
					seaPickupMcvCell = alternatePickup;
					seaBoardingLastProgressCell = activeMcv.Location;
					seaBoardingLastProgressTick = world.WorldTick;
					QueueRiskAwareMove(activeMcv, mcvMobile, alternatePickup);
					FransBotLog.BotDebug(world,
						"{0}: [MCV FERRY PICKUP] task={1} mcv={2} lst={3} outcome=AlternatePickupSelected oldPickup={4} newPickup={5} craftHandoff={6} noProgressWT={7} recovery={8}/{9} endpointBlockedBy=All ferryRetained=True corridorRetained=True; native EnterTransport will be retried after the currently-free endpoint is reached.",
						player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
						previousPickup?.ToString() ?? "None", alternatePickup,
						activeLandingCraft.Location, Info.SeaBoardingNoProgressTimeout,
						seaBoardingRecoveryAttempts, Info.SeaBoardingMaximumRecoveryAttempts);
					return;
				}

				seaBoardingLastProgressCell = activeMcv.Location;
				seaBoardingLastProgressTick = world.WorldTick;
				nextSeaBoardingRetryTick = 0;
			}

			// Once any recovery move reaches an adjacent pickup cell, native Cargo owns the final
			// handoff again. Do not require the original cached land cell forever.
			if (activeLandingCraft.IsIdle && activeMcv.IsIdle &&
				PassengerAdjacentCells(activeLandingCraft.Location).Contains(mcvMobile.ToCell))
			{
				seaPickupMcvCell = mcvMobile.ToCell;
				seaPickupCraftCell = activeLandingCraft.Location;
				IssueNativeMcvBoarding(bot);
			}
		}

		bool TryShiftSeaPickupMcvCell(Actor mcv, Mobile mobile, out CPos alternatePickup)
		{
			alternatePickup = default;
			if (!IsLiveOwnedMcv(mcv) || mobile == null || !IsLiveOwnedLandingCraft(activeLandingCraft))
				return false;

			var currentPickup = seaPickupMcvCell;
			foreach (var cell in PassengerAdjacentCells(activeLandingCraft.Location)
				.Where(c => !currentPickup.HasValue || c != currentPickup.Value)
				.Where(c => strategicMapService.IsAmphibiousHandoff(c, activeLandingCraft.Location))
				.Where(c => mobile.CanEnterCell(c, mcv, BlockedByActor.All) && mobile.CanStayInCell(c))
				.OrderBy(c => (c - mobile.ToCell).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y))
			{
				if (!HasRiskAwarePathBetweenCells(mcv, mobile, mobile.ToCell, cell, out _))
					continue;
				alternatePickup = cell;
				return true;
			}

			return false;
		}

		void ManageSeaTransport(IBot bot)
		{
			if (!IsLiveOwnedLandingCraft(activeLandingCraft) || activeMcv == null || activeMcv.IsDead)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			var cargo = activeLandingCraft.TraitOrDefault<Cargo>();
			var passenger = activeMcv.TraitOrDefault<Passenger>();
			var craftMobile = activeLandingCraft.TraitOrDefault<Mobile>();
			if (cargo == null || passenger == null || craftMobile == null ||
				passenger.Transport != activeLandingCraft || !cargo.Passengers.Contains(activeMcv) ||
				!seaLandingCraftCell.HasValue)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			if (UpdateProgressCell(craftMobile.ToCell, ref seaTransportLastProgressCell, ref seaTransportLastProgressTick, world.WorldTick))
				seaTransportStallRetries = 0;

			// LST-loss SECURE is a hard transport-only traffic block. Revalidate the cached
			// loaded-ferry leg only when the incident revision changes. If the remaining leg
			// intersects an unresolved loss zone, stop issuing movement until that incident is
			// cleared (which increments the revision again). Combat Commanders remain free to enter.
			if (seaLastTransportLossExclusionRevision != generalService.TransportLossExclusionRevision)
			{
				seaLastTransportLossExclusionRevision = generalService.TransportLossExclusionRevision;
				if (!IsTransportLossSafeNavalRoute(activeLandingCraft, craftMobile, craftMobile.ToCell, seaLandingCraftCell.Value))
				{
					seaTransportLossBlockedRevision = seaLastTransportLossExclusionRevision;
					QueueStopOrder(bot, activeLandingCraft);
					FransBotLog.BotDebug(world,
						"{0}: SIMPLE FERRY holds loaded LST {1}: active LST-loss SECURE revision {2} blocks the remaining route to {3}. No further crossing order is issued until a loss incident is cleared/changed.",
						player, activeLandingCraft, seaLastTransportLossExclusionRevision, seaLandingCraftCell.Value);
				}
				else
					seaTransportLossBlockedRevision = -1;
			}

			if (seaTransportLossBlockedRevision == generalService.TransportLossExclusionRevision)
				return;

			// Do not pay for a fresh A* route merely because the shared RiskModel snapshot tick
			// advanced. First use cheap endpoint checks. Only genuinely new CRITICAL pressure at
			// the LST or its landing handoff earns one full remaining-route proof/re-route.
			if (world.WorldTick >= nextSeaRouteRiskRecheckTick)
			{
				nextSeaRouteRiskRecheckTick = world.WorldTick + Info.SeaRouteRiskRecheckInterval;
				if (riskModelService.RiskRevision != seaLastRiskRevision)
				{
					seaLastRiskRevision = riskModelService.RiskRevision;
					var immediateRisk = riskModelService.EvaluateImmediateRisk(activeLandingCraft, craftMobile.ToCell,
						FransRiskRole.NavalTransport, FransRiskTolerance.Balanced);
					var landingRisk = riskModelService.EvaluateCell(activeLandingCraft, seaLandingCraftCell.Value,
						FransRiskRole.NavalTransport, FransRiskTolerance.Balanced);
					if (immediateRisk.IsCritical || landingRisk.IsCritical)
					{
						if (!TryFindNavalTransportPath(activeLandingCraft, craftMobile, craftMobile.ToCell, seaLandingCraftCell.Value, out _, out _, FransRiskTolerance.Balanced))
						{
							QueueStopOrder(bot, activeLandingCraft);
							seaTransportLastProgressTick = world.WorldTick;
							FransBotLog.BotDebug(world, "{0}: SIMPLE FERRY pauses loaded LST {1}: new CRITICAL risk at current/landing endpoint under RiskRevision {2}, and no safe remaining path exists. No repeated route search occurs while the plan is held.",
								player, activeLandingCraft, seaLastRiskRevision);
							return;
						}

						QueueStopOrder(bot, activeLandingCraft);
						QueueNavalTransportPlainMove(activeLandingCraft, craftMobile, seaLandingCraftCell.Value,
							routeAlreadyValidated: true);
						seaTransportLastProgressTick = world.WorldTick;
						seaTransportStallRetries = 0;
					}
				}
			}

			if (craftMobile.ToCell != seaLandingCraftCell.Value)
			{
				if (seaTransportLastProgressTick >= 0 &&
					world.WorldTick - seaTransportLastProgressTick >= Info.SeaPlanningInterval)
				{
					if (seaTransportStallRetries >= Info.MovingMcvStallMaximumRetries)
					{
						if (!TryFindNavalTransportPath(activeLandingCraft, craftMobile, craftMobile.ToCell, seaLandingCraftCell.Value, out _, out _, FransRiskTolerance.Balanced))
						{
							var immediate = riskModelService.EvaluateImmediateRisk(activeLandingCraft, craftMobile.ToCell,
								FransRiskRole.NavalTransport, FransRiskTolerance.Balanced);
							var landing = riskModelService.EvaluateCell(activeLandingCraft, seaLandingCraftCell.Value,
								FransRiskRole.NavalTransport, FransRiskTolerance.Balanced);
							if (!immediate.IsCritical && !landing.IsCritical)
							{
								QueueStopOrder(bot, activeLandingCraft);
								QueueNavalTransportPlainMove(activeLandingCraft, craftMobile, seaLandingCraftCell.Value, routeAlreadyValidated: true);
								seaTransportLastProgressTick = world.WorldTick;
								seaTransportStallRetries = 0;
								FransBotLog.BotDebug(world, "{0}: COMMITTED FERRY override keeps loaded LST {1} moving toward landing {2}: no Balanced non-critical proof was found, but both current and landing endpoints remain non-critical. Native Move is allowed to take the bounded risk instead of waiting indefinitely.",
									player, activeLandingCraft, seaLandingCraftCell.Value);
								return;
							}

							seaTransportLastProgressTick = world.WorldTick;
							FransBotLog.BotDebug(world, "{0}: SIMPLE FERRY loaded LST {1} remains held after {2} bounded stall retries because the current or landing endpoint is still CRITICAL under committed Balanced tolerance. Mission stays committed without repeated full replanning.",
								player, activeLandingCraft, seaTransportStallRetries, seaLandingCraftCell.Value);
							return;
						}
						seaTransportStallRetries = 0;
					}

					QueueStopOrder(bot, activeLandingCraft);
					QueueNavalTransportPlainMove(activeLandingCraft, craftMobile, seaLandingCraftCell.Value,
						routeAlreadyValidated: true);
					seaTransportStallRetries++;
					seaTransportLastProgressTick = world.WorldTick;
					FransBotLog.BotDebug(world, "{0}: SIMPLE FERRY loaded LST {1} made no cell progress for {2} WT; reissuing only the cached landing leg ({3}/{4}), no pickup/landing replan.",
						player, activeLandingCraft, Info.SeaPlanningInterval, seaTransportStallRetries, Info.MovingMcvStallMaximumRetries);
				}
				return;
			}

			if (!activeLandingCraft.IsIdle)
				return;

			if (!cargo.CanUnload())
				return;

			stage = ExpansionStage.SeaUnloading;
			ResetSeaUnloadRecovery();
			seaUnloadOriginalLandingCraftCell = seaLandingCraftCell;
			TryFindCurrentMcvUnloadExit(activeMcv, activeMcv.Trait<Mobile>(), activeLandingCraft,
				craftMobile, sourceSide: false, out seaUnloadExpectedExitCell);
			IssueNativeMcvUnload(bot, "InitialDestinationLanding");
		}

		void ManageSeaUnload(IBot bot)
		{
			if (!IsLiveOwnedLandingCraft(activeLandingCraft) || activeMcv == null || activeMcv.IsDead)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			var passenger = activeMcv.TraitOrDefault<Passenger>();
			var mcvMobile = activeMcv.TraitOrDefault<Mobile>();
			var cargo = activeLandingCraft.TraitOrDefault<Cargo>();
			var craftMobile = activeLandingCraft.TraitOrDefault<Mobile>();
			if (passenger == null || mcvMobile == null || cargo == null || craftMobile == null)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			// Cargo.Unload clears both ownership links before UnloadCargo adds the same actor
			// back to the world at frame end. The one-MCV ferry is physically complete only
			// after all three facts agree; activity state by itself is never progress.
			var passengerInCargo = cargo.Passengers.Contains(activeMcv);
			if (activeMcv.IsInWorld && passenger.Transport == null && !passengerInCargo)
			{
				if (seaUnloadReturningToSource)
					CompleteReturnedMcvUnload(bot);
				else
					ResumeLandExpansionAfterSeaUnload(bot);
				return;
			}

			if (passenger.Transport == null && !passengerInCargo)
				return;
			if (passenger.Transport != activeLandingCraft || !passengerInCargo)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			if (seaUnloadRecoveryPhase == SeaUnloadRecoveryPhase.PreservedCargo)
				return;

			if (seaUnloadRecoveryPhase == SeaUnloadRecoveryPhase.AwaitingStop)
			{
				if (!activeLandingCraft.IsIdle)
					return;

				if (seaUnloadRecoveryAttempts > Info.SeaBoardingMaximumRecoveryAttempts)
				{
					HandleSeaUnloadRecoveryExhausted(bot, mcvMobile, craftMobile);
					return;
				}

				if (TryFindCurrentExecutableSeaUnloadHandoff(activeMcv, mcvMobile,
					activeLandingCraft, craftMobile, seaUnloadReturningToSource,
					out var recoveryHandoff))
				{
					StartSeaUnloadHandoffRecovery(bot, craftMobile, recoveryHandoff);
					return;
				}

				// No endpoint is currently free. Keep the topology and objective intact,
				// consume only this bounded recovery window, and allow a transient blocker
				// to move before the next timeout.
				seaUnloadRecoveryPhase = SeaUnloadRecoveryPhase.NativeUnload;
				seaUnloadAttemptStartedTick = world.WorldTick;
				nextSeaUnloadRetryTick = world.WorldTick + Info.SeaUnloadRetryInterval;
				FransBotLog.BotDebug(world,
					"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=NoCurrentEndpoint side={4} original={5} current={6} recovery={7}/{8} cargo={9}; no canonical same-landmass/same-region handoff has both endpoints currently free. The SAME ExpansionTask/corridor remains eligible during this bounded wait.",
					player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
					seaUnloadReturningToSource ? "SourceReturn" : "Destination",
					seaUnloadOriginalLandingCraftCell?.ToString() ?? "None",
					seaLandingCraftCell?.ToString() ?? craftMobile.ToCell.ToString(),
					seaUnloadRecoveryAttempts, Info.SeaBoardingMaximumRecoveryAttempts,
					cargo.PassengerCount);
				return;
			}

			if (seaUnloadRecoveryPhase == SeaUnloadRecoveryPhase.MovingToHandoff)
			{
				if (!seaLandingCraftCell.HasValue)
				{
					EnterSeaCargoPreservation(bot, "alternate unload movement lost its canonical target handoff");
					return;
				}

				var transportLossChanged =
					seaLastTransportLossExclusionRevision != generalService.TransportLossExclusionRevision;
				var riskChanged = world.WorldTick >= nextSeaRouteRiskRecheckTick &&
					seaLastRiskRevision != riskModelService.RiskRevision;
				if (transportLossChanged || riskChanged)
				{
					seaLastTransportLossExclusionRevision = generalService.TransportLossExclusionRevision;
					seaLastRiskRevision = riskModelService.RiskRevision;
					nextSeaRouteRiskRecheckTick = world.WorldTick + Info.SeaRouteRiskRecheckInterval;
					if (!TryFindNavalTransportPath(activeLandingCraft, craftMobile, craftMobile.ToCell,
						seaLandingCraftCell.Value, out _, out _, out var recoveryFailure,
						FransRiskTolerance.Balanced))
					{
						if (seaUnloadExpectedExitCell.HasValue)
							seaUnloadMoveRejectedHandoffs.Add((seaUnloadExpectedExitCell.Value,
								seaLandingCraftCell.Value));
						seaUnloadRecoveryAttempts++;
						QueueStopOrder(bot, activeLandingCraft);
						seaUnloadRecoveryPhase = SeaUnloadRecoveryPhase.AwaitingStop;
						FransBotLog.BotDebug(world,
							"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=AlternateMoveInvalidated side={4} handoff={5}/{6} recovery={7}/{8} reason={9}; changed RiskModel/TransportLoss evidence stops the local move before another canonical endpoint is considered.",
							player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
							seaUnloadReturningToSource ? "SourceReturn" : "Destination",
							seaUnloadExpectedExitCell?.ToString() ?? "None",
							seaLandingCraftCell.Value, seaUnloadRecoveryAttempts,
							Info.SeaBoardingMaximumRecoveryAttempts,
							recoveryFailure ?? "ChangedRouteEvidence");
						return;
					}
				}

				if (UpdateProgressCell(craftMobile.ToCell, ref seaTransportLastProgressCell,
					ref seaTransportLastProgressTick, world.WorldTick))
					seaTransportStallRetries = 0;

				if (craftMobile.ToCell == seaLandingCraftCell.Value)
				{
					if (!activeLandingCraft.IsIdle)
						return;

					seaUnloadRecoveryPhase = SeaUnloadRecoveryPhase.NativeUnload;
					seaUnloadAttemptStartedTick = world.WorldTick;
					nextSeaUnloadRetryTick = world.WorldTick;
					if (TryFindCurrentMcvUnloadExit(activeMcv, mcvMobile, activeLandingCraft,
						craftMobile, seaUnloadReturningToSource, out var exitCell))
					{
						seaUnloadExpectedExitCell = exitCell;
						IssueNativeMcvUnload(bot, "RecoveredHandoffArrival");
					}
					else
						FransBotLog.BotDebug(world,
							"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=ArrivalEndpointNowBlocked side={4} handoff={5} expectedExit={6} recovery={7}/{8}; topology remains valid and the bounded watchdog waits for transient occupancy to clear.",
							player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
							seaUnloadReturningToSource ? "SourceReturn" : "Destination",
							seaLandingCraftCell.Value,
							seaUnloadExpectedExitCell?.ToString() ?? "None",
							seaUnloadRecoveryAttempts, Info.SeaBoardingMaximumRecoveryAttempts);
					return;
				}

				if (seaTransportLastProgressTick >= 0 &&
					world.WorldTick - seaTransportLastProgressTick >= Info.SeaPlanningInterval)
				{
					if (seaUnloadExpectedExitCell.HasValue)
						seaUnloadMoveRejectedHandoffs.Add((seaUnloadExpectedExitCell.Value,
							seaLandingCraftCell.Value));
					seaUnloadRecoveryAttempts++;
					QueueStopOrder(bot, activeLandingCraft);
					seaUnloadRecoveryPhase = SeaUnloadRecoveryPhase.AwaitingStop;
					FransBotLog.BotDebug(world,
						"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=AlternateMoveNoProgress side={4} handoff={5}/{6} noCellProgressWT={7} recovery={8}/{9} cargo={10}; native Stop precedes another bounded local handoff choice.",
						player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
						seaUnloadReturningToSource ? "SourceReturn" : "Destination",
						seaUnloadExpectedExitCell?.ToString() ?? "None", seaLandingCraftCell.Value,
						Info.SeaPlanningInterval, seaUnloadRecoveryAttempts,
						Info.SeaBoardingMaximumRecoveryAttempts, cargo.PassengerCount);
				}
				return;
			}

			// An idle activity is not required for liveness. If the previous native unload
			// ended, reissue only when the exact canonical MCV exit is currently available.
			// If UnloadCargo is still active, the physical timeout below remains authoritative.
			if (activeLandingCraft.IsIdle && world.WorldTick >= nextSeaUnloadRetryTick &&
				TryFindCurrentMcvUnloadExit(activeMcv, mcvMobile, activeLandingCraft,
					craftMobile, seaUnloadReturningToSource, out var currentExit))
			{
				seaUnloadExpectedExitCell = currentExit;
				IssueNativeMcvUnload(bot, "CurrentEndpointAvailable");
				return;
			}

			if (seaUnloadAttemptStartedTick < 0)
				seaUnloadAttemptStartedTick = world.WorldTick;
			if (world.WorldTick - seaUnloadAttemptStartedTick < Info.SeaBoardingNoProgressTimeout)
				return;

			seaUnloadRecoveryAttempts++;
			QueueStopOrder(bot, activeLandingCraft);
			seaUnloadRecoveryPhase = SeaUnloadRecoveryPhase.AwaitingStop;
			FransBotLog.BotDebug(world,
				"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=PhysicalNoProgress side={4} original={5} current={6} expectedExit={7} recovery={8}/{9} noProgressWT={10} cargo={11} passengerStillCargo={12} lstIdle={13}; active UnloadCargo is not progress, so native Stop opens bounded local recovery while retaining the SAME ExpansionTask/corridor.",
				player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
				seaUnloadReturningToSource ? "SourceReturn" : "Destination",
				seaUnloadOriginalLandingCraftCell?.ToString() ?? "None",
				seaLandingCraftCell?.ToString() ?? craftMobile.ToCell.ToString(),
				seaUnloadExpectedExitCell?.ToString() ?? "None",
				seaUnloadRecoveryAttempts, Info.SeaBoardingMaximumRecoveryAttempts,
				Info.SeaBoardingNoProgressTimeout, cargo.PassengerCount, passengerInCargo,
				activeLandingCraft.IsIdle);
		}

		void IssueNativeMcvUnload(IBot bot, string reason)
		{
			if (!IsLiveOwnedLandingCraft(activeLandingCraft) || activeMcv == null ||
				activeMcv.IsDead || activeMcv.IsInWorld)
				return;

			var passenger = activeMcv.TraitOrDefault<Passenger>();
			var cargo = activeLandingCraft.TraitOrDefault<Cargo>();
			if (passenger?.Transport != activeLandingCraft || cargo == null ||
				!cargo.Passengers.Contains(activeMcv))
				return;

			seaUnloadRecoveryPhase = SeaUnloadRecoveryPhase.NativeUnload;
			seaUnloadAttemptStartedTick = world.WorldTick;
			nextSeaUnloadRetryTick = world.WorldTick + Info.SeaUnloadRetryInterval;
			FransBotLog.BotDebug(world,
				"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=NativeUnloadIssued side={4} original={5} current={6} expectedExit={7} recovery={8}/{9} graceWT={10} cargo={11} reason={12}; SAME ExpansionTask/corridor retained.",
				player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
				seaUnloadReturningToSource ? "SourceReturn" : "Destination",
				seaUnloadOriginalLandingCraftCell?.ToString() ?? "None",
				seaLandingCraftCell?.ToString() ?? activeLandingCraft.Location.ToString(),
				seaUnloadExpectedExitCell?.ToString() ?? "BlockedOrNativeChoice",
				seaUnloadRecoveryAttempts, Info.SeaBoardingMaximumRecoveryAttempts,
				Info.SeaBoardingNoProgressTimeout, cargo.PassengerCount, reason);
			bot.QueueOrder(new Order("Unload", activeLandingCraft, false));
		}

		bool TryGetSeaUnloadRecoveryDomain(bool sourceSide, out int groundLandmass,
			out int navalRegion, out CPos anchorCraftCell)
		{
			groundLandmass = -1;
			navalRegion = -1;
			anchorCraftCell = default;
			var landCell = sourceSide ? seaPickupMcvCell : targetDeployCell;
			var craftCell = sourceSide ? seaPickupCraftCell : seaUnloadOriginalLandingCraftCell;
			if (!landCell.HasValue || !craftCell.HasValue ||
				!strategicMapService.TryGetGroundLandmassId(landCell.Value, out groundLandmass) ||
				!strategicMapService.TryGetNavalRegionId(craftCell.Value, out navalRegion))
				return false;

			anchorCraftCell = craftCell.Value;
			return true;
		}

		bool IsCurrentMcvUnloadEndpointUsable(Actor mcv, Mobile mcvMobile, Actor craft,
			Mobile craftMobile, FransGroundShoreAccess handoff)
		{
			if (!strategicMapService.IsAmphibiousHandoff(handoff.GroundCell, handoff.NavalCell) ||
				!mcvMobile.CanStayInCell(handoff.GroundCell) ||
				!mcvMobile.CanEnterCell(handoff.GroundCell, mcv, BlockedByActor.All) ||
				!craftMobile.CanStayInCell(handoff.NavalCell))
				return false;

			return handoff.NavalCell == craftMobile.ToCell ||
				craftMobile.CanEnterCell(handoff.NavalCell, craft, BlockedByActor.All);
		}

		bool TryFindCurrentMcvUnloadExit(Actor mcv, Mobile mcvMobile, Actor craft,
			Mobile craftMobile, bool sourceSide, out CPos? exitCell)
		{
			exitCell = null;
			if (!TryGetSeaUnloadRecoveryDomain(sourceSide, out var groundLandmass,
				out var navalRegion, out _))
				return false;

			foreach (var handoff in strategicMapService.GetGroundShoreAccess(groundLandmass)
				.Where(access => access.NavalRegionId == navalRegion &&
					access.NavalCell == craftMobile.ToCell)
				.OrderBy(access => access.GroundCell.X)
				.ThenBy(access => access.GroundCell.Y))
				if (IsCurrentMcvUnloadEndpointUsable(mcv, mcvMobile, craft, craftMobile, handoff))
				{
					exitCell = handoff.GroundCell;
					return true;
				}

			return false;
		}

		bool TryFindCurrentExecutableSeaUnloadHandoff(Actor mcv, Mobile mcvMobile,
			Actor craft, Mobile craftMobile, bool sourceSide, out FransGroundShoreAccess selected)
		{
			selected = default;
			if (!TryGetSeaUnloadRecoveryDomain(sourceSide, out var groundLandmass,
				out var navalRegion, out var anchorCraftCell))
				return false;

			var radiusSquared = Info.SeaLandingSearchRadius * Info.SeaLandingSearchRadius;
			var candidates = strategicMapService.GetGroundShoreAccess(groundLandmass)
				.Where(access => access.NavalRegionId == navalRegion &&
					(access.NavalCell - anchorCraftCell).LengthSquared <= radiusSquared &&
					!seaUnloadMoveRejectedHandoffs.Contains((access.GroundCell, access.NavalCell)) &&
					IsCurrentMcvUnloadEndpointUsable(mcv, mcvMobile, craft, craftMobile, access))
				.OrderBy(access => access.NavalCell == craftMobile.ToCell ? 0 : 1)
				.ThenBy(access => (access.NavalCell - anchorCraftCell).LengthSquared)
				.ThenBy(access => access.NavalCell.X)
				.ThenBy(access => access.NavalCell.Y)
				.ThenBy(access => access.GroundCell.X)
				.ThenBy(access => access.GroundCell.Y)
				.Take(Info.MaximumLandingBeachCandidates)
				.ToArray();

			foreach (var candidate in candidates)
			{
				if (!TryFindNavalTransportPath(craft, craftMobile, craftMobile.ToCell,
					candidate.NavalCell, out _, out _, FransRiskTolerance.Balanced))
					continue;

				selected = candidate;
				return true;
			}

			return false;
		}

		void StartSeaUnloadHandoffRecovery(IBot bot, Mobile craftMobile,
			FransGroundShoreAccess handoff)
		{
			var previous = seaLandingCraftCell;
			seaLandingCraftCell = handoff.NavalCell;
			seaUnloadExpectedExitCell = handoff.GroundCell;
			if (craftMobile.ToCell == handoff.NavalCell)
			{
				IssueNativeMcvUnload(bot, "CurrentHandoffRecovered");
				return;
			}

			seaUnloadRecoveryPhase = SeaUnloadRecoveryPhase.MovingToHandoff;
			seaTransportLastProgressCell = craftMobile.ToCell;
			seaTransportLastProgressTick = world.WorldTick;
			seaTransportStallRetries = 0;
			seaLastRiskRevision = riskModelService.RiskRevision;
			seaLastTransportLossExclusionRevision = generalService.TransportLossExclusionRevision;
			nextSeaRouteRiskRecheckTick = world.WorldTick + Info.SeaRouteRiskRecheckInterval;
			QueueNavalTransportPlainMove(activeLandingCraft, craftMobile, handoff.NavalCell,
				routeAlreadyValidated: true);
			FransBotLog.BotDebug(world,
				"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=AlternateHandoffSelected side={4} original={5} previous={6} alternate={7}/{8} recovery={9}/{10}; endpoint is currently free, StrategicMap-canonical, same landmass/naval region, and the Balanced TransportLoss-safe route is proven. Native Move then native Unload retain the SAME ExpansionTask/corridor.",
				player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
				seaUnloadReturningToSource ? "SourceReturn" : "Destination",
				seaUnloadOriginalLandingCraftCell?.ToString() ?? "None",
				previous?.ToString() ?? craftMobile.ToCell.ToString(),
				handoff.GroundCell, handoff.NavalCell, seaUnloadRecoveryAttempts,
				Info.SeaBoardingMaximumRecoveryAttempts);
		}

		void HandleSeaUnloadRecoveryExhausted(IBot bot, Mobile mcvMobile, Mobile craftMobile)
		{
			if (!seaUnloadReturningToSource &&
				TryFindCurrentExecutableSeaUnloadHandoff(activeMcv, mcvMobile,
					activeLandingCraft, craftMobile, sourceSide: true, out var sourceHandoff))
			{
				seaUnloadReturningToSource = true;
				seaUnloadRecoveryAttempts = 0;
				seaUnloadMoveRejectedHandoffs.Clear();
				FransBotLog.BotDebug(world,
					"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=DestinationRecoveryExhausted original={4} current={5} action=ReturnLoadedToSource sourceHandoff={6}/{7}; loaded MCV is preserved, the SAME ExpansionTask/corridor remains owned during return, and no strategic objective or shoreline is blacklisted.",
					player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
					seaUnloadOriginalLandingCraftCell?.ToString() ?? "None",
					seaLandingCraftCell?.ToString() ?? craftMobile.ToCell.ToString(),
					sourceHandoff.GroundCell, sourceHandoff.NavalCell);
				StartSeaUnloadHandoffRecovery(bot, craftMobile, sourceHandoff);
				return;
			}

			EnterSeaCargoPreservation(bot, seaUnloadReturningToSource
				? "source-side native unload recovery exhausted"
				: "destination unload recovery exhausted and no currently executable source return handoff exists");
		}

		void EnterSeaCargoPreservation(IBot bot, string reason)
		{
			QueueStopOrder(bot, activeLandingCraft);
			seaUnloadRecoveryPhase = SeaUnloadRecoveryPhase.PreservedCargo;
			seaUnloadMoveRejectedHandoffs.Clear();
			nextSeaCargoPreservedRecheckTick = world.WorldTick + Info.SeaPlanningInterval;
			stage = ExpansionStage.SeaCargoPreserved;
			FransBotLog.BotDebug(world,
				"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=SeaCargoPreserved original={4} current={5} recovery={6}/{7} cargo={8} reason=NoExecutableDestinationOrSourceHandoff detail={9} ownership=RetainedLoadedCargo action=QuiescentWait nextRecheckWT={10}; native Cargo and the SAME ExpansionTask/corridor/LST reservation remain owned until a canonical handoff reopens or the existing loss lifecycle applies.",
				player, expansionTask.Id, activeMcv?.ActorID ?? 0,
				activeLandingCraft?.ActorID ?? 0,
				seaUnloadOriginalLandingCraftCell?.ToString() ?? "None",
				seaLandingCraftCell?.ToString() ?? activeLandingCraft?.Location.ToString() ?? "None",
				seaUnloadRecoveryAttempts, Info.SeaBoardingMaximumRecoveryAttempts,
				activeLandingCraft?.TraitOrDefault<Cargo>()?.PassengerCount ?? 0, reason,
				nextSeaCargoPreservedRecheckTick);
		}

		void ManagePreservedSeaCargo(IBot bot)
		{
			if (!IsLiveOwnedLandingCraft(activeLandingCraft) || activeMcv == null || activeMcv.IsDead)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			var passenger = activeMcv.TraitOrDefault<Passenger>();
			var cargo = activeLandingCraft.TraitOrDefault<Cargo>();
			if (passenger == null || cargo == null)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			var passengerInCargo = cargo.Passengers.Contains(activeMcv);
			if (activeMcv.IsInWorld && passenger.Transport == null && !passengerInCargo)
			{
				if (seaUnloadReturningToSource)
					CompleteReturnedMcvUnload(bot);
				else
					ResumeLandExpansionAfterSeaUnload(bot);
				return;
			}

			// Cargo.Unload clears both ownership links before the actor returns to the world
			// at frame end. Preserve the same transient guard as ordinary SeaUnloading.
			if (passenger.Transport == null && !passengerInCargo)
				return;
			if (passenger.Transport != activeLandingCraft || !passengerInCargo)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			if (world.WorldTick < nextSeaCargoPreservedRecheckTick)
				return;

			nextSeaCargoPreservedRecheckTick = world.WorldTick + Info.SeaPlanningInterval;
			if (!activeLandingCraft.IsIdle)
			{
				// Preservation entry already issued Stop. Reassert it only on the bounded
				// preservation cadence if native activity has still not quiesced.
				QueueStopOrder(bot, activeLandingCraft);
				return;
			}

			var mcvMobile = activeMcv.TraitOrDefault<Mobile>();
			var craftMobile = activeLandingCraft.TraitOrDefault<Mobile>();
			if (mcvMobile == null || craftMobile == null)
			{
				FailSeaMissionAfterLoad(bot);
				return;
			}

			// A transient blocker or route condition must not become permanent task memory.
			// Re-open destination first, then the proven source-return domain, using the same
			// canonical/current-endpoint/RiskModel/TransportLoss checks as ordinary recovery.
			seaUnloadMoveRejectedHandoffs.Clear();
			if (TryFindCurrentExecutableSeaUnloadHandoff(activeMcv, mcvMobile,
				activeLandingCraft, craftMobile, sourceSide: false, out var destinationHandoff))
			{
				seaUnloadReturningToSource = false;
				seaUnloadRecoveryAttempts = 0;
				stage = ExpansionStage.SeaUnloading;
				FransBotLog.BotDebug(world,
					"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=PreservedCargoReopened side=Destination handoff={4}/{5} ownership=RetainedLoadedCargo action=ResumeBoundedRecovery; the SAME ExpansionTask/corridor remains owned and native Move/Unload resumes.",
					player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
					destinationHandoff.GroundCell, destinationHandoff.NavalCell);
				StartSeaUnloadHandoffRecovery(bot, craftMobile, destinationHandoff);
				return;
			}

			if (TryFindCurrentExecutableSeaUnloadHandoff(activeMcv, mcvMobile,
				activeLandingCraft, craftMobile, sourceSide: true, out var sourceHandoff))
			{
				seaUnloadReturningToSource = true;
				seaUnloadRecoveryAttempts = 0;
				stage = ExpansionStage.SeaUnloading;
				FransBotLog.BotDebug(world,
					"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=PreservedCargoReopened side=SourceReturn handoff={4}/{5} ownership=RetainedLoadedCargo action=ResumeBoundedRecovery; destination remains unavailable, so the SAME loaded ferry returns by native Move/Unload.",
					player, expansionTask.Id, activeMcv.ActorID, activeLandingCraft.ActorID,
					sourceHandoff.GroundCell, sourceHandoff.NavalCell);
				StartSeaUnloadHandoffRecovery(bot, craftMobile, sourceHandoff);
			}
		}

		void CompleteReturnedMcvUnload(IBot bot)
		{
			FransBotLog.BotDebug(world,
				"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=SourceReturnUnloadSuccess sourceHandoff={4}/{5}; exact MCV left native Cargo, LST ownership is released, and the ore objective returns to normal reconsideration without permanent blocker/shoreline failure memory.",
				player, expansionTask.Id, activeMcv?.ActorID ?? 0,
				activeLandingCraft?.ActorID ?? 0,
				seaUnloadExpectedExitCell?.ToString() ?? activeMcv?.Location.ToString() ?? "None",
				seaLandingCraftCell?.ToString() ?? activeLandingCraft?.Location.ToString() ?? "None");
			AbortExpansionTaskToIdle(bot,
				"destination unload recovery exhausted; loaded MCV returned and unloaded natively on the source landmass");
		}

		void ResumeLandExpansionAfterSeaUnload(IBot bot)
		{
			var mcv = activeMcv;
			var mobile = mcv?.TraitOrDefault<Mobile>();
			if (!IsLiveOwnedMcv(mcv) || mobile == null || !targetResourceCenter.HasValue)
			{
				MarkCurrentFieldFailed();
				AbortExpansionTaskToIdle(bot, "sea unload lost its live MCV/objective before land execution could resume");
				nextLandExpansionPlanningTick = world.WorldTick;
				return;
			}

			var transformsInfo = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null)
			{
				MarkCurrentFieldFailed();
				AbortExpansionTaskToIdle(bot, "sea unload MCV lacks a valid transform definition");
				nextLandExpansionPlanningTick = world.WorldTick;
				return;
			}

			var intoActor = world.Map.Rules.Actors[transformsInfo.IntoActor];
			var buildingInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null ||
				!TryFindSafeDeployPath(mcv, mobile, targetResourceCenter.Value,
					transformsInfo, intoActor, buildingInfo, out var deployCell, out _))
			{
				MarkCurrentFieldFailed();
				AbortExpansionTaskToIdle(bot, "sea unload found no safe deploy path for the committed ore");
				nextLandExpansionPlanningTick = world.WorldTick;
				return;
			}

			targetDeployCell = deployCell;
			postSeaUnloadDeployCommitted = true;
			FransBotLog.BotDebug(world,
				"{0}: [MCV FERRY UNLOAD] task={1} mcv={2} lst={3} outcome=DestinationUnloadSuccess original={4} current={5} recovery={6}/{7}; exact actor is back in world, Passenger.Transport is null, Cargo no longer contains it, and normal LST release resumes.",
				player, expansionTask.Id, mcv.ActorID, activeLandingCraft?.ActorID ?? 0,
				seaUnloadOriginalLandingCraftCell?.ToString() ?? "None",
				seaLandingCraftCell?.ToString() ?? "None",
				seaUnloadRecoveryAttempts, Info.SeaBoardingMaximumRecoveryAttempts);

			// The landing just proved a valid local MCV/LST shoreline rendezvous. Preserve
			// that exact handoff through FACT->PROC->MCV so a follow-on ferry from this
			// island never needs to rediscover the coast with another bounded shoreline/path search.
			if (seaLandingCraftCell.HasValue &&
				PassengerAdjacentCells(seaLandingCraftCell.Value).Contains(mobile.ToCell))
			{
				preferredRoutinePickupMcvCell = mobile.ToCell;
				preferredRoutinePickupCraftCell = seaLandingCraftCell.Value;
				FransBotLog.BotDebug(world,
					"{0}: ROUTINE FERRY remembers proven destination shoreline access {1}/{2} for the roaming chain after unload.",
					player, preferredRoutinePickupMcvCell.Value, preferredRoutinePickupCraftCell.Value);
			}

			ReleaseActiveLandingCraftReservation();
			activeLandingCraft = null;
			seaPickupMcvCell = null;
			seaPickupCraftCell = null;
			seaLandingCraftCell = null;
			nextSeaBoardingRetryTick = 0;
			ResetSeaUnloadRecovery();
			nextSeaRouteRiskRecheckTick = 0;
			seaPickupMcvLastProgressCell = null;
			seaPickupMcvLastProgressTick = -1;
			seaPickupMcvStallRetries = 0;
			seaPickupApproachRejectedCells.Clear();
			seaPickupApproachRecoveryAttempts = 0;
			seaPickupCraftLastProgressCell = null;
			seaPickupCraftLastProgressTick = -1;
			seaPickupCraftStallRetries = 0;
			seaTransportLastProgressCell = null;
			seaTransportLastProgressTick = -1;
			seaTransportStallRetries = 0;
			seaBoardingLastProgressCell = null;
			seaBoardingLastProgressTick = -1;
			seaBoardingRecoveryAttempts = 0;
			seaLastRiskRevision = -1;
			seaLastTransportLossExclusionRevision = -1;
			seaTransportLossBlockedRevision = -1;
			stage = ExpansionStage.MovingToOre;
			nextRouteRecheckTick = world.WorldTick + Info.RouteRecheckInterval;

			FransBotLog.BotDebug(world, "{0}: MCV {1} unloaded successfully on the new land mass; POST-LANDING DEPLOY COMMITMENT is active toward ore {2}. Remembered/preferred-only pressure cannot abort before FACT; new damage, direct visible weapon threat or Critical risk still can.",
				player, mcv, targetResourceCenter.Value);
			QueueRiskAwareMove(mcv, mobile, deployCell);
		}



		bool TryFindLandingSideForMcv(Actor mcv, Mobile mcvMobile, CPos resourceCenter,
			TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, Actor craft, CPos? seaSourceCell, int? requiredNavalRegion,
			IReadOnlyCollection<Actor> landingProtectors, out CPos landingCraftCell, out CPos deployCell, out int landPathLength, out int seaPathLength)
		{
			return TryFindLandingSideForMcvWithEvidence(mcv, mcvMobile, resourceCenter, transformsInfo,
				intoActor, buildingInfo, craft, seaSourceCell, requiredNavalRegion, landingProtectors,
				out landingCraftCell, out deployCell, out landPathLength, out seaPathLength, out _, out _);
		}

		bool TryFindLandingSideForMcvWithEvidence(Actor mcv, Mobile mcvMobile, CPos resourceCenter,
			TransformsInfo transformsInfo,
			ActorInfo intoActor, BuildingInfo buildingInfo, Actor craft, CPos? seaSourceCell, int? requiredNavalRegion,
			IReadOnlyCollection<Actor> landingProtectors, out CPos landingCraftCell, out CPos deployCell,
			out int landPathLength, out int seaPathLength, out CPos provenExitCell, out CPos[] landPath)
		{
			landingCraftCell = default;
			deployCell = default;
			landPathLength = int.MaxValue;
			seaPathLength = int.MaxValue;
			provenExitCell = default;
			landPath = [];

			var craftMobile = craft?.TraitOrDefault<Mobile>();

			// REGIONAL SEA EXECUTABILITY: reject a target before any expensive deploy/path ranking
			// unless at least one known native-passable handoff belongs to the exact pickup naval region.
			// This is topology only: no hidden actors, risk or ownership is inspected.
			if (requiredNavalRegion.HasValue &&
				!HasKnownLandingShoreInNavalRegion(resourceCenter, requiredNavalRegion.Value))
				return false;

			// PERFORMANCE-ONLY: every exit cell in this proof tests the same deploy candidate set.
			// Build it once for this exact world state, then memoize identical exit-cell path proofs
			// within this call. Handoff/exit ordering and all path/risk semantics remain unchanged.
			CPos[] deployCandidates;
			using (FransBotLog.Profile(world, player, "MCV.SeaOreDeployCandidates"))
				deployCandidates = GetSafeDeployCandidates(mcv, mcvMobile, resourceCenter, transformsInfo, intoActor, buildingInfo);
			if (deployCandidates.Length == 0)
				return false;

			var exitPathProofs = new Dictionary<CPos, (bool Success, CPos DeployCell, int PathLength)>();
			Dictionary<(int X, int Y), List<Actor>> protectorBuckets;
			using (FransBotLog.Profile(world, player, "MCV.SeaOreProtectorBuckets"))
				protectorBuckets = BuildSeaLandingProtectorBuckets(landingProtectors);

			CPos[] rankedBeaches;
			using (FransBotLog.Profile(world, player, "MCV.SeaOreHandoffRanking"))
				rankedBeaches = AmphibiousHandoffCellsNear(resourceCenter, Info.SeaLandingSearchRadius)
					.Where(c => !requiredNavalRegion.HasValue || IsCellInNavalRegion(c, requiredNavalRegion.Value))
					.OrderByDescending(c => CountSeaLandingProtectorsNear(c, landingProtectors, protectorBuckets))
					.ThenBy(c => (c - resourceCenter).LengthSquared)
					.Take(Info.MaximumLandingBeachCandidates)
					.ToArray();

			foreach (var beach in rankedBeaches)
			{
				if (craftMobile != null)
				{
					var navalProofOk = false;
					using (FransBotLog.Profile(world, player, "MCV.SeaOreHandoffNavalProof"))
						navalProofOk = craftMobile.CanEnterCell(beach, check: BlockedByActor.Immovable) &&
							craftMobile.CanStayInCell(beach) && seaSourceCell.HasValue &&
							TryFindNavalTransportPath(craft, craftMobile, seaSourceCell.Value, beach, out seaPathLength, out _);
					if (!navalProofOk)
						continue;
				}

				CPos[] exitCells;
				using (FransBotLog.Profile(world, player, "MCV.SeaOreExitCellEnumeration"))
					exitCells = PassengerAdjacentCells(beach)
						.Where(c => strategicMapService.IsAmphibiousHandoff(c, beach))
						.Where(c => mcvMobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mcvMobile.CanStayInCell(c))
						.OrderBy(c => (c - resourceCenter).LengthSquared)
						.ToArray();

				foreach (var exitCell in exitCells)
				{
					if (!exitPathProofs.TryGetValue(exitCell, out var proof))
					{
						bool success;
						CPos provenDeployCell;
						int provenLandPathLength;
						CPos[] provenPath;
						using (FransBotLog.Profile(world, player, "MCV.SeaOreExitPathProof"))
							success = TryFindSafeDeployPathFromCellUsingCandidates(mcv, mcvMobile, exitCell, deployCandidates,
								out provenDeployCell, out provenLandPathLength, out provenPath);
						proof = (success, provenDeployCell, provenLandPathLength);
						exitPathProofs.Add(exitCell, proof);
						if (success)
							landPath = provenPath;
					}

					if (!proof.Success)
						continue;

					deployCell = proof.DeployCell;
					landPathLength = proof.PathLength;
					landingCraftCell = beach;
					provenExitCell = exitCell;
					return true;
				}
			}

			return false;
		}

		Actor[] GetOwnedSeaLandingProtectors()
		{
			combatIntelService.EnsureCurrentSnapshot();
			return combatIntelService.OwnedActors
				.Where(a =>
					a.Info.HasTraitInfo<AttackBaseInfo>() && a.TraitOrDefault<Mobile>() != null &&
					a.TraitOrDefault<Passenger>() != null && !Info.McvTypes.Contains(a.Info.Name) &&
					!Info.LandingCraftTypes.Contains(a.Info.Name))
				.ToArray();
		}

		Dictionary<(int X, int Y), List<Actor>> BuildSeaLandingProtectorBuckets(IReadOnlyCollection<Actor> protectors)
		{
			var buckets = new Dictionary<(int X, int Y), List<Actor>>();
			if (protectors == null || protectors.Count == 0)
				return buckets;

			var bucketSize = Math.Max(1, Info.SeaLandingProtectionRadius);
			foreach (var actor in protectors)
			{
				if (actor == null || !actor.IsInWorld || actor.IsDead)
					continue;
				var key = (actor.Location.X / bucketSize, actor.Location.Y / bucketSize);
				if (!buckets.TryGetValue(key, out var bucket))
					buckets[key] = bucket = [];
				bucket.Add(actor);
			}
			return buckets;
		}

		int CountSeaLandingProtectorsNear(CPos cell, IReadOnlyCollection<Actor> protectors,
			Dictionary<(int X, int Y), List<Actor>> buckets)
		{
			if (protectors == null || protectors.Count == 0 || buckets == null || buckets.Count == 0)
				return 0;

			var radius = Math.Max(1, Info.SeaLandingProtectionRadius);
			var radiusSquared = radius * radius;
			var bucketX = cell.X / radius;
			var bucketY = cell.Y / radius;
			var count = 0;
			for (var x = bucketX - 1; x <= bucketX + 1; x++)
				for (var y = bucketY - 1; y <= bucketY + 1; y++)
				{
					if (!buckets.TryGetValue((x, y), out var bucket))
						continue;
					foreach (var actor in bucket)
						if ((actor.Location - cell).LengthSquared <= radiusSquared &&
							strategicMapService.TryGetStrategicSectorRoute(
								actor.Location, cell, FransStrategicMovementLayer.Ground, FransStrategicRoutePolicy.Fast, out _))
							count++;
				}
			return count;
		}


		bool CanDisplaceOrdinaryFriendlyBlocker(Actor actor)
		{
			if (actor == null || !actor.IsInWorld || actor.IsDead || actor.Owner != player || !actor.IsIdle ||
				actor == activeMcv ||
				actor.TraitOrDefault<Mobile>() == null || !actor.TraitsImplementing<AttackBase>().Any(a => !a.IsTraitDisabled && !a.IsTraitPaused) ||
				actor.TraitOrDefault<Harvester>() != null || actor.TraitOrDefault<Minelayer>() != null ||
				actor.Info.TraitInfos<CargoInfo>().Any() || actor.Info.TraitInfos<CapturesInfo>().Any() ||
				actor.Info.TraitInfos<TransformsInfo>().Any() || actor.TraitOrDefault<Aircraft>() != null)
				return false;

			if (groundUnitReservationService != null && groundUnitReservationService.IsGroundUnitReserved(actor))
				return false;
			if (captureSecurityServices != null && captureSecurityServices.Any(service => service.IsCaptureMissionActor(actor)))
				return false;
			if (transportService != null && transportService.IsTransportReserved(actor))
				return false;

			return true;
		}

		bool QueueOrdinaryBlockerRiskAwareMove(Actor actor, CPos destination)
		{
			var mobile = actor?.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused ||
				mobile.PathFinder is not PathFinder pathFinder)
				return false;

			int CustomCost(CPos cell) => cell == mobile.ToCell ? 0 :
				riskModelService.GetPathCost(actor, cell, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
			var initialPath = pathFinder.FindPathToTargetCell(actor, [mobile.ToCell], destination,
				BlockedByActor.Immovable, CustomCost, laneBias: false);
			if (initialPath == null || initialPath.Count == 0 ||
				riskModelService.EvaluateRoute(actor, initialPath, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced).IsCritical)
				return false;

			// PathFinder returns target-to-source. Preserve the validated blocker-clearance
			// route with a bounded packet of native Move orders.
			var orderedPath = initialPath
				.AsEnumerable()
				.Reverse()
				.Where(cell => cell != mobile.ToCell)
				.ToArray();
			if (orderedPath.Length == 0)
			{
				QueueMoveOrder(null, actor, destination);
				return true;
			}

			const int MaximumMoveWaypoints = 4;
			var waypointCount = Math.Min(MaximumMoveWaypoints, orderedPath.Length);
			var queued = false;
			for (var i = 1; i <= waypointCount; i++)
			{
				var index = (int)((long)i * orderedPath.Length / waypointCount) - 1;
				QueueMoveOrder(null, actor, orderedPath[index], queued);
				queued = true;
			}

			return true;
		}

		int MoveFriendlyDeploymentBlockers(IBot bot, Actor mcv, CPos deployCell)
		{
			var radius = Math.Max(4, Info.ExpansionDeployClearanceRadius);
			var radiusSquared = radius * radius;
			var moved = 0;
			combatIntelService.EnsureCurrentSnapshot();
			var blockers = combatIntelService.OwnedActors
				.Where(CanDisplaceOrdinaryFriendlyBlocker)
				.Where(a => a != mcv && (a.Location - deployCell).LengthSquared <= radiusSquared)
				.OrderBy(a => (a.Location - deployCell).LengthSquared)
				.ThenBy(a => a.ActorID)
				.Take(12)
				.ToArray();

			foreach (var blocker in blockers)
			{
				var mobile = blocker.TraitOrDefault<Mobile>();
				if (mobile == null)
					continue;

				var candidates = world.Map.FindTilesInAnnulus(deployCell, radius + 2, radius + 8)
					.Where(world.Map.Contains)
					.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
					.Select(c => (Cell: c, Risk: riskModelService.EvaluateCell(blocker, c, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced)))
					.Where(x => !x.Risk.IsCritical)
					.OrderBy(x => x.Risk.Score)
					.ThenByDescending(x => (x.Cell - deployCell).LengthSquared)
					.ThenBy(x => (x.Cell - blocker.Location).LengthSquared)
					.ThenBy(x => x.Cell.X)
					.ThenBy(x => x.Cell.Y)
					.ToArray();
				if (candidates.Length == 0)
					continue;

				if (QueueOrdinaryBlockerRiskAwareMove(blocker, candidates[0].Cell))
					moved++;
			}

			return moved;
		}

		bool TryClearFriendlyDeploymentBlockers(IBot bot, Actor mcv, CPos deployCell)
		{
			var moved = MoveFriendlyDeploymentBlockers(bot, mcv, deployCell);
			if (moved > 0)
				FransBotLog.BotDebug(world,
					"{0}: deploy-confirm watchdog moved {1} ordinary friendly blocker(s) away from {2}; scoutless MCV deployment keeps blocker handling bounded.",
					player, moved, deployCell);
			return moved > 0;
		}


		IEnumerable<CPos> PassengerAdjacentCells(CPos craftCell)
		{
			return Util.AdjacentCells(world, Target.FromCell(world, craftCell))
				.Where(c => c != craftCell && world.Map.Contains(c));
		}

		IEnumerable<CPos> AmphibiousHandoffCellsNear(CPos center, int radius)
		{
			if (strategicMapService == null || radius <= 0)
				return Enumerable.Empty<CPos>();

			var nearby = world.Map.FindTilesInAnnulus(center, 1, radius).ToHashSet();
			return strategicMapService.AmphibiousHandoffs
				.Select(access => access.NavalCell)
				.Distinct()
				.Where(nearby.Contains);
		}

		bool HasNearbyShore(CPos center, int radius)
		{
			return AmphibiousHandoffCellsNear(center, radius).Any();
		}

		bool IsTransportLossSafeNavalRoute(Actor actor, Mobile mobile, CPos source, CPos destination)
		{
			if (actor == null || mobile == null || mobile.PathFinder is not PathFinder pathFinder)
				return false;

			int NoExtraCost(CPos cell) => 0;
			var path = pathFinder.FindPathToTargetCell(actor, [source], destination,
				BlockedByActor.Immovable, NoExtraCost, laneBias: false);
			return path != null && path.Count > 0 && generalService.IsTransportLossRouteAllowed(path);
		}

		bool TryFindNavalTransportPath(Actor actor, Mobile mobile, CPos source, CPos destination,
			out int pathLength, out FransRouteRiskAssessment routeRisk, FransRiskTolerance tolerance = FransRiskTolerance.Cautious)
		{
			return TryFindNavalTransportPath(actor, mobile, source, destination,
				out pathLength, out routeRisk, out _, tolerance);
		}

		bool TryFindNavalTransportPath(Actor actor, Mobile mobile, CPos source, CPos destination,
			out int pathLength, out FransRouteRiskAssessment routeRisk, out string failure,
			FransRiskTolerance tolerance = FransRiskTolerance.Cautious)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "MCV.NavalPath");
			pathLength = int.MaxValue;
			routeRisk = default;
			failure = null;
			if (source == destination)
			{
				pathLength = 0;
				routeRisk = riskModelService.EvaluateDirectRoute(actor, source, destination, FransRiskRole.NavalTransport, tolerance);
				if (routeRisk.IsCritical)
				{
					failure = "CriticalRisk";
					return false;
				}
				return true;
			}

			if (mobile.PathFinder is not PathFinder pathFinder)
			{
				failure = "MissingPathFinder";
				return false;
			}

			int CustomCost(CPos cell) =>
				cell == source ? 0 : riskModelService.GetPathCost(actor, cell, FransRiskRole.NavalTransport, tolerance);
			var path = pathFinder.FindPathToTargetCell(actor, [source], destination,
				BlockedByActor.Immovable, CustomCost, laneBias: false);
			if (path == null || path.Count == 0)
			{
				failure = "NativePathNotFound";
				return false;
			}
			if (!generalService.IsTransportLossRouteAllowed(path))
			{
				failure = "TransportLossExclusion";
				if (generalService.TryGetTransportLossRouteBlocker(path, out var blocker))
					failure += $";[TRANSPORT-LOSS BLOCKER] incident={blocker.IncidentId},incidentCell={blocker.IncidentCell}," +
						$"latestLossCell={blocker.LatestLossCell},blockingRouteCell={blocker.BlockingRouteCell}," +
						$"radius={blocker.ExclusionRadius},state={blocker.LifecycleState},owner={blocker.Owner},route={source}->{destination}";
				return false;
			}

			routeRisk = riskModelService.EvaluateRoute(actor, path, FransRiskRole.NavalTransport, tolerance);
			if (routeRisk.IsCritical)
			{
				failure = "CriticalRisk";
				return false;
			}

			pathLength = path.Count;
			return true;
		}

		bool QueueNavalTransportPlainMove(Actor actor, Mobile mobile, CPos destination, bool routeAlreadyValidated = false)
		{
			FransRouteRiskAssessment routeRisk = default;
			if (!routeAlreadyValidated &&
				!TryFindNavalTransportPath(actor, mobile, mobile.ToCell, destination, out _, out routeRisk))
				return false;

			// RiskModel decides whether the strategic naval leg may start.
			// Once accepted, native OpenRA Move owns all cell-by-cell path execution.
			// Do not inject Frans GetPathCost into Move's dynamic path callback: that caused
			// repeated expensive A* work while an LST was already making normal progress.
			QueueMoveOrder(null, actor, destination);

			if (!routeAlreadyValidated && !routeRisk.IsPreferred)
				FransBotLog.BotDebug(world, "{0}: unified RiskModel accepts elevated but non-critical LST corridor for {1}: peak risk {2}/{3} near {4}; native Move owns execution.",
					player, actor, routeRisk.PeakScore, routeRisk.CriticalThreshold, routeRisk.PeakCell);
			return true;
		}

		bool HasRiskAwarePathBetweenCells(Actor actor, Mobile mobile, CPos source, CPos destination,
			out int pathLength)
		{
			return HasRiskAwarePathBetweenCells(actor, mobile, source, destination, out pathLength, out _);
		}

		bool HasRiskAwarePathBetweenCells(Actor actor, Mobile mobile, CPos source, CPos destination,
			out int pathLength, out CPos[] provenPath)
		{
			pathLength = int.MaxValue;
			provenPath = [];
			if (source == destination)
			{
				pathLength = 0;
				provenPath = [source];
				return true;
			}

			if (mobile.PathFinder is not PathFinder pathFinder)
				return false;

			var path = riskModelService.ExecuteWithPreparedPathCost(actor,
				FransRiskRole.Mcv, CurrentMcvRiskTolerance, preparedPathCost =>
				{
					int CustomCost(CPos cell) =>
						cell == source ? 0 : preparedPathCost(cell);

					return pathFinder.FindPathToTargetCell(actor, [source], destination,
						BlockedByActor.Immovable, CustomCost, laneBias: false);
				});

			if (path == null || path.Count == 0)
				return false;

			for (var p = 0; p < path.Count - 1; p++)
				if (IsMcvCriticalRisk(actor, path[p], CurrentMcvRiskTolerance))
					return false;

			pathLength = path.Count;
			provenPath = path.ToArray();
			return true;
		}

		Actor FindAvailableLandingCraft(Actor mcv)
		{
			if (pendingMcvLandingCraftReservation != null && !IsLiveOwnedLandingCraft(pendingMcvLandingCraftReservation))
				pendingMcvLandingCraftReservation = null;

			var requiresRegion = TryGetRequiredLandingCraftProductionRegion(out var requiredNavalRegion);
			if (IsLiveOwnedLandingCraft(pendingMcvLandingCraftReservation) &&
				transportService.CanStrategicExpansionClaimTransport(pendingMcvLandingCraftReservation) &&
				(!requiresRegion || IsLandingCraftInNavalRegion(pendingMcvLandingCraftReservation, requiredNavalRegion)))
			{
				var pinnedCargo = pendingMcvLandingCraftReservation.TraitOrDefault<Cargo>();
				if (pinnedCargo != null && !pinnedCargo.IsTraitDisabled && pinnedCargo.IsEmpty())
					return pendingMcvLandingCraftReservation;
			}

			// This scan only runs during the throttled sea-planning pass. Avoid maintaining
			// another always-live ActorIndex for a unit type that is rarely needed. A committed
			// ferry only sees physical LSTs in its source/ferry naval region; wrong-sea craft are
			// strategically unavailable and therefore cannot suppress local LST production.
			combatIntelService.EnsureCurrentSnapshot();
			return combatIntelService.OwnedActors
				.Where(IsLiveOwnedLandingCraft)
				.Where(a => !requiresRegion || IsLandingCraftInNavalRegion(a, requiredNavalRegion))
				.Where(a => transportService.CanStrategicExpansionClaimTransport(a))
				.Where(a =>
				{
					var cargo = a.TraitOrDefault<Cargo>();
					return cargo != null && !cargo.IsTraitDisabled && cargo.IsEmpty();
				})
				.OrderBy(a => (a.Location - mcv.Location).LengthSquared)
				.ThenBy(a => a.ActorID)
				.FirstOrDefault();
		}
		void LatchNavalCapabilityDemand(string reason)
		{
			if (HasOwnedLandingCraftProducer())
			{
				navalCapabilityDemandLatched = false;
				return;
			}

			if (navalCapabilityDemandLatched)
				return;
			navalCapabilityDemandLatched = true;
			nextNavalCapabilityRetryTick = world.WorldTick;
			FransBotLog.BotDebug(world,
				"{0}: NAVAL CAPABILITY demand latched: {1}. This strategic prerequisite survives a later temporary land-route fallback and closes only when physical SPEN/SYRD exists.",
				player, reason ?? "sea access proved useful");
		}

		void MaintainLatchedNavalCapability(IBot bot)
		{
			// HARD OPENING LOCK: no proactive SPEN/SYRD may consume the Building queue
			// before the first PIONEER MCV is physically complete. A previously restored
			// latch may survive, but it cannot execute until the opening milestone opens.
			if (openingBuildOrderService.OpeningLocked)
				return;

			if (!navalCapabilityDemandLatched)
				return;
			if (HasOwnedLandingCraftProducer())
			{
				navalCapabilityDemandLatched = false;
				ReleaseBaseBuilderLock();
				FransBotLog.BotDebug(world,
					"{0}: NAVAL CAPABILITY latch satisfied by physical SPEN/SYRD; ordinary Ship composition owns combat-ship production and LST remains demand-only.",
					player);
				return;
			}

			if (world.WorldTick < nextNavalCapabilityRetryTick)
				return;
			nextNavalCapabilityRetryTick = world.WorldTick + Info.SeaPlanningInterval;

			// A landlocked current base cannot consume the shared Building queue for an impossible
			// SPEN/SYRD. After a previously physical yard is lost, do not leave the restored naval
			// capability latch passive forever: an otherwise-idle physical MCV may prove and execute
			// the existing coastal-staging plan, then repack after the replacement yard is physical.
			if (!CanPlaceAnyLandingCraftProducerFromCurrentBase())
			{
				if (expansionTask.Id == 0)
				{
					var rebuildMcv = IsLiveOwnedMcv(activeMcv) ? activeMcv : FindAvailableExpansionMcv();
					var rebuildMobile = rebuildMcv?.TraitOrDefault<Mobile>();
					if (rebuildMcv != null && rebuildMobile != null && !rebuildMobile.IsTraitDisabled && !rebuildMobile.IsTraitPaused &&
						TryBeginCoastalStaging(bot, rebuildMcv, rebuildMobile))
					{
						activeMcv = rebuildMcv;
						FransBotLog.BotDebug(world,
							"{0}: NAVAL CAPABILITY rebuild after yard loss starts proactive coastal staging with MCV {1}; the latch remains active until a physical SPEN/SYRD is restored.",
							player, rebuildMcv);
						return;
					}
				}
				return;
			}

			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var shipQueues = ShipQueueNames().SelectMany(name => queuesByCategory[name])
				.Where(q => q.Enabled)
				.Distinct()
				.ToArray();
			EnsureLandingCraftProducer(bot, queuesByCategory, shipQueues);
		}

		void RequestLandingCraft(IBot bot, int desiredTotal = 1)
		{
			if (playerResources == null)
			{
				ReleaseBaseBuilderLock();
				return;
			}

			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
			{
				ReleaseBaseBuilderLock();
				return;
			}

			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var shipQueueNames = ShipQueueNames();
			var shipQueues = shipQueueNames.SelectMany(name => queuesByCategory[name])
				.Where(q => q.Enabled)
				.Distinct()
				.ToArray();

			string craftType = null;
			foreach (var type in Info.LandingCraftTypes.OrderBy(x => x))
				if (world.Map.Rules.Actors.TryGetValue(type, out var actorInfo) &&
					actorInfo.TraitInfoOrDefault<BuildableInfo>() is BuildableInfo buildable &&
					buildable.Queue.Any(shipQueueNames.Contains) &&
					shipQueues.Any(q => q.BuildableItems().Any(i => i.Name == type)))
				{
					craftType = type;
					break;
				}

			if (craftType == null)
			{
				ReleaseBaseBuilderLock();
				return;
			}

			var sharedLandingCraftPool = transportService?.CountLandingCraftPool(bot) ?? 0;
			var sharedLandingCraftCap = transportService?.MaximumLandingCraftPool ?? int.MaxValue;
			var missionCriticalSeaWait = stage == ExpansionStage.WaitingForSeaTransport ||
				(coastalStagingForSeaExpansion && HasCommittedSeaExpansionDemand);
			var requiredNavalRegion = 0;
			var hasRequiredRegion = missionCriticalSeaWait &&
				TryGetRequiredLandingCraftProductionRegion(out requiredNavalRegion);

			combatIntelService.EnsureCurrentSnapshot();
			var ownedCount = missionCriticalSeaWait
				? combatIntelService.OwnedActors.Count(a => IsLiveOwnedLandingCraft(a) &&
					(!hasRequiredRegion || IsLandingCraftInNavalRegion(a, requiredNavalRegion)) &&
					transportService.CanStrategicExpansionClaimTransport(a) &&
					(a.TraitOrDefault<Cargo>() is Cargo cargo && !cargo.IsTraitDisabled && cargo.IsEmpty()))
				: combatIntelService.OwnedActors.Count(IsLiveOwnedLandingCraft);
			var queuedCount = CountQueuedLandingCraftProduction(hasRequiredRegion ? requiredNavalRegion : null);
			var unboundSharedQueuedCount = hasRequiredRegion ? CountUnboundSharedLandingCraftProduction() : 0;
			var allRequestedCount = Info.LandingCraftTypes.Sum(type => unitBuilder.RequestedProductionCount(bot, type));
			var requestedCount = hasRequiredRegion ? 0 : allRequestedCount;
			if (sharedLandingCraftPool >= sharedLandingCraftCap)
			{
				LogMcvTransportDemandState(ownedCount, queuedCount, allRequestedCount,
					sharedLandingCraftPool, sharedLandingCraftCap,
					hasRequiredRegion ? requiredNavalRegion : null, "DemandHeld", "SharedPoolCap");
				if (world.WorldTick >= nextSeaTransportRequestTick)
				{
					nextSeaTransportRequestTick = world.WorldTick + Info.SeaTransportRequestCooldown;
					FransBotLog.BotDebug(world,
						"{0}: PIONEER LST demand waits at shared physical+queued+requested pool cap {1}/{2}. Strategic expansion keeps priority for any reusable empty capture LST, but does not grow the global landing-craft fleet beyond the release cap.",
						player, sharedLandingCraftPool, sharedLandingCraftCap);
				}
				ReleaseBaseBuilderLock();
				return;
			}
			if (ownedCount + queuedCount + requestedCount >= Math.Max(1, desiredTotal))
			{
				LogMcvTransportDemandState(ownedCount, queuedCount, allRequestedCount,
					sharedLandingCraftPool, sharedLandingCraftCap,
					hasRequiredRegion ? requiredNavalRegion : null, "WaitingValidQueue",
					ownedCount > 0 ? "LiveUsableLstAvailable" : queuedCount > 0 ? "ValidQueuePresent" : "GenericRequestPresent");
				ReleaseBaseBuilderLock();
				return;
			}
			if (hasRequiredRegion && unboundSharedQueuedCount > 0)
			{
				LogMcvTransportDemandState(ownedCount, queuedCount, allRequestedCount,
					sharedLandingCraftPool, sharedLandingCraftCap, requiredNavalRegion,
					"WaitingValidQueue", $"UnboundSharedQueued{unboundSharedQueuedCount}AwaitingPhysicalRegion");
				ReleaseBaseBuilderLock();
				return;
			}

			var hasBudget = playerResources.GetCashAndResources() >= Info.MinimumCashForSeaTransport;
			if (!missionCriticalSeaWait && !hasBudget &&
				unitBuilder.RequestedProductionCount(bot, craftType) <= 0 &&
				baseBuilderLockToken == Actor.InvalidConditionToken)
				return;

			EnsureLandingCraftProducer(bot, queuesByCategory, shipQueues,
				hasRequiredRegion ? requiredNavalRegion : null);

			if (missionCriticalSeaWait && IsCommittedSeaProductionCorridorLossBlocked())
			{
				LogMcvTransportDemandState(ownedCount, queuedCount, allRequestedCount,
					sharedLandingCraftPool, sharedLandingCraftCap,
					hasRequiredRegion ? requiredNavalRegion : null, "DemandHeld", "TransportLossCorridorBlocked");
				nextSeaTransportRequestTick = world.WorldTick + Info.SeaTransportRequestCooldown;
				if (seaProductionLossBlockedRevision != generalService.TransportLossExclusionRevision)
				{
					seaProductionLossBlockedRevision = generalService.TransportLossExclusionRevision;
					FransBotLog.BotDebug(world,
						"{0}: MCV ferry suppresses fresh {1} production because the committed pickup -> landing corridor intersects an active LST-loss SECURE exclusion. Existing SECURE work must clear the incident before demand-production resumes.",
						player, craftType);
				}
				return;
			}
			seaProductionLossBlockedRevision = -1;

			// Mission-critical ferry execution is regional, but production still obeys the shared
			// global LST pool cap above. A dedicated producer-owned queue can guarantee its region;
			// RA's player-owned classic Ship queue cannot, so its item remains unbound until delivery.
			if (missionCriticalSeaWait && hasRequiredRegion)
			{
				if (world.WorldTick < nextSeaTransportRequestTick)
				{
					LogMcvTransportDemandState(ownedCount, queuedCount, allRequestedCount,
						sharedLandingCraftPool, sharedLandingCraftCap, requiredNavalRegion,
						"DemandHeld", $"ProductionCooldownUntilWT{nextSeaTransportRequestTick}");
					return;
				}

				if (!TrySelectLandingCraftProductionQueue(shipQueues, craftType, requiredNavalRegion,
					out var selectedQueue, out var producerBinding, out var producerCandidates))
				{
					LogMcvTransportDemandState(ownedCount, queuedCount, allRequestedCount,
						sharedLandingCraftPool, sharedLandingCraftCap, requiredNavalRegion,
						"DemandHeld", "NoEnabledRegionalProducerCanBuildLst");
					return;
				}

				nextSeaTransportRequestTick = world.WorldTick + Info.SeaTransportRequestCooldown;
				LogMcvTransportDemandState(ownedCount, queuedCount, allRequestedCount,
					sharedLandingCraftPool, sharedLandingCraftCap, requiredNavalRegion,
					"DemandReasserted", $"ProductionRequested{producerBinding}QueueActor{selectedQueue.Actor.ActorID}");
				FransBotLog.BotDebug(world,
					"{0}: MCV REGIONAL LST SUPPLY queues demand-only {1} through queue actor {2} for pickup naval region {3}; producerBinding={4}, candidateProducerActors={5}. The shared global LST pool cap remains authoritative.",
					player, craftType, selectedQueue.Actor, requiredNavalRegion, producerBinding,
					producerCandidates.Length == 0 ? "none" : string.Join(",", producerCandidates.Select(a => a.ActorID)));
				bot.QueueOrder(Order.StartProduction(selectedQueue.Actor, craftType, 1));
				return;
			}

			var requestPending = unitBuilder.RequestedProductionCount(bot, craftType) > 0;
			if (requestPending || (!hasBudget && !missionCriticalSeaWait) || world.WorldTick < nextSeaTransportRequestTick)
			{
				LogMcvTransportDemandState(ownedCount, queuedCount, allRequestedCount,
					sharedLandingCraftPool, sharedLandingCraftCap,
					hasRequiredRegion ? requiredNavalRegion : null, "DemandHeld",
					requestPending ? "GenericRequestPresent" : !hasBudget ? "InsufficientBudget" : $"ProductionCooldownUntilWT{nextSeaTransportRequestTick}");
				return;
			}

			nextSeaTransportRequestTick = world.WorldTick + Info.SeaTransportRequestCooldown;
			LogMcvTransportDemandState(ownedCount, queuedCount, allRequestedCount,
				sharedLandingCraftPool, sharedLandingCraftCap,
				hasRequiredRegion ? requiredNavalRegion : null, "DemandReasserted", "GenericUnitBuilderRequest");
			FransBotLog.BotDebug(world,
				"{0}: retaining generic demand-only landing craft request {1} until a Ship producer can satisfy non-regional naval demand.",
				player, craftType);
			unitBuilder.RequestUnitProduction(bot, craftType);
		}

		bool IsCommittedSeaProductionCorridorLossBlocked()
		{
			if (stage != ExpansionStage.WaitingForSeaTransport || !IsLiveOwnedMcv(activeMcv) ||
				!targetResourceCenter.HasValue)
				return false;

			var mobile = activeMcv.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused ||
				!TryPrepareCachedSeaGeometryForObjective(activeMcv, mobile, targetResourceCenter.Value) ||
				!preferredRoutinePickupCraftCell.HasValue || !seaLandingCraftCell.HasValue)
				return false;

			return !generalService.IsTransportLossCorridorAllowed(preferredRoutinePickupCraftCell.Value, seaLandingCraftCell.Value);
		}

		int CountQueuedLandingCraftProduction(int? requiredNavalRegion = null)
		{
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var queues = queuesByCategory[Info.LandingCraftQueueCategory].Where(q => q.Enabled).ToArray();
			if (!requiredNavalRegion.HasValue)
				return queues.Sum(q => q.AllQueued().Count(item => Info.LandingCraftTypes.Contains(item.Item)));

			return queues.Sum(q => q.AllQueued().Count(item => Info.LandingCraftTypes.Contains(item.Item) &&
				TryGetRegionBoundProductionQueueNavalRegion(q, item.Item, out var region, out _) &&
				region == requiredNavalRegion.Value));
		}

		int CountUnboundSharedLandingCraftProduction()
		{
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			return queuesByCategory[Info.LandingCraftQueueCategory]
				.Where(q => q.Enabled)
				.Sum(q => q.AllQueued().Count(item => Info.LandingCraftTypes.Contains(item.Item) &&
					!TryGetRegionBoundProductionQueueNavalRegion(q, item.Item, out _, out _)));
		}

		bool HasQueuedLandingCraftProduction(int? requiredNavalRegion = null) =>
			CountQueuedLandingCraftProduction(requiredNavalRegion) > 0;

		bool HasRegionalLandingCraftQueueSupplyCapability(int requiredNavalRegion)
		{
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var shipQueues = queuesByCategory[Info.LandingCraftQueueCategory].Where(q => q.Enabled).ToArray();
			return Info.LandingCraftTypes.Any(craftType =>
				shipQueues.Any(q => q.BuildableItems().Any(item => item.Name == craftType)) &&
				(shipQueues.Any(q => TryGetRegionBoundProductionQueueNavalRegion(q, craftType, out var region, out _) &&
					region == requiredNavalRegion) ||
				 GetEligibleLandingCraftProducers(shipQueues, craftType, requiredNavalRegion).Length > 0));
		}

		void LogResolvedSeaSupplyPreCommitDiagnosticIfObserved(IBot bot, Actor mcv, CPos objective,
			int provenPickupRegion, string supplyProof)
		{
			if (lastSeaSupplyDiagnosticSignature == null ||
				preCommitStrategicLandingCraftObjective != objective ||
				!preCommitStrategicLandingCraftRegion.HasValue)
				return;

			var resolvedByNativeQueue = provenPickupRegion >= 0;
			var requiredNavalRegion = resolvedByNativeQueue
				? provenPickupRegion
				: preCommitStrategicLandingCraftRegion.Value;
			var resolution = resolvedByNativeQueue
				? "ResolvedByObservedRegionBoundNativeQueue"
				: "ResolvedByPhysicalLandingCraft";
			var queueState = resolvedByNativeQueue
				? "no StartProduction order issued; ordinary proof accepted an observed producer-bound native queue item"
				: "no StartProduction order issued; ordinary proof selected a physical LST";
			LogSeaSupplyPreCommitDiagnostic(bot, mcv, objective, requiredNavalRegion,
				resolution, supplyProof, queueState);
		}

		void LogSeaSupplyPreCommitDiagnostic(IBot bot, Actor mcv, CPos objective, int requiredNavalRegion,
			string outcome, string supplyProof, string queueState)
		{
			var pool = transportService?.GetLandingCraftPoolDiagnostic(bot) ??
				new FransLandingCraftPoolDiagnostic(0, 0, 0, 0, "service-unavailable", "service-unavailable", "service-unavailable");
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var regionalQueueDetails = queuesByCategory[Info.LandingCraftQueueCategory]
				.Where(queue => queue.Enabled)
				.Select(queue =>
				{
					var queuedItems = queue.AllQueued()
						.Where(item => Info.LandingCraftTypes.Contains(item.Item))
						.Select(item => item.Item)
						.OrderBy(item => item)
						.ToArray();
					var regionBoundQueued = queue.AllQueued()
						.Where(item => Info.LandingCraftTypes.Contains(item.Item) &&
							TryGetRegionBoundProductionQueueNavalRegion(queue, item.Item, out _, out _))
						.Select(item => item.Item)
						.OrderBy(item => item)
						.ToArray();
					var unboundQueued = queue.AllQueued()
						.Where(item => Info.LandingCraftTypes.Contains(item.Item) &&
							!TryGetRegionBoundProductionQueueNavalRegion(queue, item.Item, out _, out _))
						.Select(item => item.Item)
						.OrderBy(item => item)
						.ToArray();
					var buildable = queue.BuildableItems()
						.Where(item => Info.LandingCraftTypes.Contains(item.Name))
						.Select(item => item.Name)
						.OrderBy(item => item)
						.ToArray();
					var desiredRegionProducers = buildable
						.SelectMany(type => GetEligibleLandingCraftProducers(
							queuesByCategory[Info.LandingCraftQueueCategory].Where(q => q.Enabled), type, requiredNavalRegion))
						.Distinct().OrderBy(actor => actor.ActorID).ToArray();
					return $"queueActor={queue.Actor.ActorID}/{queue.Actor.Info.Name}," +
						$"producerBinding={(unboundQueued.Length > 0 ? "UnboundUntilDelivery" : regionBoundQueued.Length > 0 ? "RegionBound" : "NotQueued")}," +
						$"desiredRegionProducerActors={(desiredRegionProducers.Length == 0 ? "none" : string.Join(",", desiredRegionProducers.Select(a => a.ActorID)))}," +
						$"nativeQueued={(queuedItems.Length == 0 ? "none" : string.Join(",", queuedItems))}," +
						$"regionBoundQueued={(regionBoundQueued.Length == 0 ? "none" : string.Join(",", regionBoundQueued))}," +
						$"unboundSharedQueued={(unboundQueued.Length == 0 ? "none" : string.Join(",", unboundQueued))}," +
						$"buildable={(buildable.Length == 0 ? "none" : string.Join(",", buildable))}";
				})
				.OrderBy(detail => detail)
				.ToArray();
			var queueDetails = regionalQueueDetails.Length == 0 ? "none" : string.Join(";", regionalQueueDetails);
			var hasMatchingIssuedOrder = lastRegionalLandingCraftOrderObjective == objective &&
				lastRegionalLandingCraftOrderRegion == requiredNavalRegion;
			var issuedOrder = hasMatchingIssuedOrder
					? lastRegionalLandingCraftOrderDiagnostic
					: "none";
			var issuedOrderSignature = hasMatchingIssuedOrder
				? lastRegionalLandingCraftOrderSignature
				: "none";
			var planDetails = lastLandingCraftPlanDiagnostic ?? "NotEvaluated";
			var signature = $"outcome={outcome}|objective={objective}|region={requiredNavalRegion}|" +
				$"task={expansionTask.Id}/{expansionTask.Mode}/{stage}|{pool.Signature}|eligibility={planDetails}|" +
				$"queues={queueDetails}|queueState={queueState}|issuedOrderState={issuedOrderSignature}";
			if (signature == lastSeaSupplyDiagnosticSignature)
				return;

			lastSeaSupplyDiagnosticSignature = signature;
			FransBotLog.BotDebug(world,
				"{0}: [E25-SUPPLY DIAGNOSTIC] outcome={7} for MCV {1}/ore {2}/required naval region {3}: ExpansionTask={4}/{5}/{6}; proof={8}; {9}; eligibility={10}; queues=[{11}]; queue action={12}; last StartProduction intent={13}.",
				player, mcv.ActorID, objective, requiredNavalRegion, expansionTask.Id, expansionTask.Mode, stage,
				outcome, supplyProof, pool.Details, planDetails, queueDetails, queueState, issuedOrder);
		}

		bool TryQueueRegionalLandingCraftSupply(IBot bot, int requiredNavalRegion, out string state)
		{
			state = null;
			var sharedLandingCraftPool = transportService?.CountLandingCraftPool(bot) ?? 0;
			var sharedLandingCraftCap = transportService?.MaximumLandingCraftPool ?? int.MaxValue;
			if (sharedLandingCraftPool >= sharedLandingCraftCap)
			{
				state = $"shared LST pool is already at cap {sharedLandingCraftPool}/{sharedLandingCraftCap}; PIONEER waits for reusable capacity instead of creating LST #{sharedLandingCraftPool + 1}";
				return false;
			}

			if (HasQueuedLandingCraftProduction(requiredNavalRegion))
			{
				state = $"producer-bound LST is already queued in naval region {requiredNavalRegion}";
				return true;
			}
			var unboundSharedQueued = CountUnboundSharedLandingCraftProduction();
			if (unboundSharedQueued > 0)
			{
				state = $"unboundSharedQueued={unboundSharedQueued}; waiting for physical delivery before assigning regional identity";
				return false;
			}

			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var shipQueues = queuesByCategory[Info.LandingCraftQueueCategory].Where(q => q.Enabled).ToArray();
			ProductionQueue queue = null;
			Actor[] producerCandidates = Array.Empty<Actor>();
			string producerBinding = null;
			var craftType = Info.LandingCraftTypes.OrderBy(x => x).FirstOrDefault(type =>
				TrySelectLandingCraftProductionQueue(shipQueues, type, requiredNavalRegion,
					out queue, out producerBinding, out producerCandidates));
			if (craftType == null || queue == null)
			{
				state = $"no enabled Ship queue has an eligible LST producer in naval region {requiredNavalRegion}";
				return false;
			}

			nextSeaTransportRequestTick = world.WorldTick + Info.SeaTransportRequestCooldown;
			lastRegionalLandingCraftOrderObjective = preCommitStrategicLandingCraftObjective;
			lastRegionalLandingCraftOrderRegion = requiredNavalRegion;
			lastRegionalLandingCraftOrderSignature =
				$"type={craftType},queueActor={queue.Actor.ActorID}/{queue.Actor.Info.Name}," +
				$"producerBinding={producerBinding},candidateProducerActors=" +
				$"{(producerCandidates.Length == 0 ? "none" : string.Join(",", producerCandidates.Select(a => a.ActorID)))}," +
				$"desiredRegion={requiredNavalRegion},actualProduction=NotObserved";
			lastRegionalLandingCraftOrderDiagnostic =
				$"issuedWT={world.WorldTick},{lastRegionalLandingCraftOrderSignature}";
			FransBotLog.BotDebug(world,
				"{0}: PIONEER SEA SUPPLY requests {1} through queue actor {2} for naval region {3}; producerBinding={4}, candidateProducerActors={5}. The ore remains uncommitted until physical or producer-bound regional supply is visible.",
				player, craftType, queue.Actor, requiredNavalRegion, producerBinding,
				producerCandidates.Length == 0 ? "none" : string.Join(",", producerCandidates.Select(a => a.ActorID)));
			bot.QueueOrder(Order.StartProduction(queue.Actor, craftType, 1));
			state = $"submitted {craftType} through queue actor {queue.Actor}; producerBinding={producerBinding},desiredRegion={requiredNavalRegion}";
			return false;
		}

		bool HasFeasibleUnbuiltSeaTransportProspect(Actor mcv, Mobile mobile, CPos objective, out string reason)
		{
			reason = null;
			if (!TryPrepareCachedSeaGeometryForObjective(mcv, mobile, objective) ||
				!preferredRoutinePickupCraftCell.HasValue || !seaLandingCraftCell.HasValue)
			{
				reason = "cached pickup/landing geometry cannot be proven";
				return false;
			}

			if (!strategicMapService.TryGetNavalRegionId(preferredRoutinePickupCraftCell.Value, out var pickupRegion) ||
				!strategicMapService.TryGetNavalRegionId(seaLandingCraftCell.Value, out var landingRegion) || pickupRegion != landingRegion)
			{
				if (pickupRegion >= 0)
					RememberSeaTopologyFailure(objective, pickupRegion,
						"committed pickup and landing no longer share one known naval region");
				reason = "pickup and landing no longer share a known naval region";
				return false;
			}

			if (!generalService.IsTransportLossCorridorAllowed(preferredRoutinePickupCraftCell.Value, seaLandingCraftCell.Value))
			{
				reason = "active LST-loss SECURE blocks the committed ferry corridor";
				return false;
			}

			if (HasQueuedLandingCraftProduction(pickupRegion) ||
				HasRegionalLandingCraftQueueSupplyCapability(pickupRegion) ||
				CanPlaceAnyLandingCraftProducerFromCurrentBase(pickupRegion))
				return true;

			reason = $"no queued LST, actionable regional Ship queue, or currently placeable LST producer exists in pickup naval region {pickupRegion}";
			return false;
		}

		void ResetLandingCraftProducerPlacementWatchdog()
		{
			landingCraftProducerPlacementItem = null;
			landingCraftProducerPlacementQueueActorId = 0;
			landingCraftProducerPlacementIssuedTick = -1;
			landingCraftProducerPlacementRetries = 0;
		}

		bool EnsureLandingCraftProducer(IBot bot, ILookup<string, ProductionQueue> queuesByCategory,
			IReadOnlyCollection<ProductionQueue> shipQueues, int? requiredNavalRegion = null)
		{
			var hasUsableShipQueue = !requiredNavalRegion.HasValue
				? shipQueues.Count > 0
				: HasRegionalLandingCraftQueueSupplyCapability(requiredNavalRegion.Value);
			if (hasUsableShipQueue || HasOwnedLandingCraftProducer(requiredNavalRegion))
			{
				ResetLandingCraftProducerPlacementWatchdog();
				ReleaseBaseBuilderLock();
				return true;
			}

			var buildingQueues = queuesByCategory[Info.BuildingQueueCategory]
				.Where(q => q.Enabled)
				.OrderBy(q => q.Actor.ActorID)
				.ToArray();

			// If either this module or BaseBuilder has already queued a naval producer,
			// take ownership of that one item and place it at the closest legal shoreline.
			foreach (var queue in buildingQueues)
			{
				var current = queue.AllQueued().FirstOrDefault();
				if (current == null || !Info.LandingCraftProducerTypes.Contains(current.Item))
					continue;

				var location = FindLandingCraftProducerLocation(current.Item, requiredNavalRegion);
				if (requiredNavalRegion.HasValue && !location.HasValue)
				{
					// This queued producer cannot ever serve the committed ferry region from the current
					// buildable area, so it must not reset NAVAL SUPPORT progress merely by existing.
					ReleaseBaseBuilderLock();
					continue;
				}

				GrantBaseBuilderLock();
				if (!current.Done)
				{
					ResetLandingCraftProducerPlacementWatchdog();
					return true;
				}

				if (!location.HasValue)
				{
					if (requiredNavalRegion.HasValue)
					{
						// A naval producer queued for another sea is not progress for this ferry, but it is
						// also not ours to destroy. Leave the shared Building queue intact and let the
						// regional coastal-staging/watchdog logic decide the strategic fallback.
						ReleaseBaseBuilderLock();
						continue;
					}

					// This exact completed naval item cannot be placed from the current buildable area.
					// Cancel it so it cannot hostage Building production; the bounded coastal watchdog
					// will repack/retry another staging cell if no real producer progress follows.
					bot.QueueOrder(Order.CancelProduction(queue.Actor, current.Item, 1));
					ResetLandingCraftProducerPlacementWatchdog();
					ReleaseBaseBuilderLock();
					FransBotLog.BotDebug(world, "{0}: NAVAL SUPPORT completed naval producer {1} has no legal shoreline placement from the current buildable area; cancelling that exact queue item and counting this pass as no progress.",
						player, current.Item);
					return false;
				}

				var samePlacement = landingCraftProducerPlacementItem == current.Item &&
					landingCraftProducerPlacementQueueActorId == queue.Actor.ActorID && landingCraftProducerPlacementIssuedTick >= 0;
				if (samePlacement && world.WorldTick - landingCraftProducerPlacementIssuedTick < Info.LandingCraftProducerPlacementConfirmTimeoutTicks)
					return true;

				if (samePlacement)
				{
					landingCraftProducerPlacementRetries++;
					if (landingCraftProducerPlacementRetries >= Info.LandingCraftProducerPlacementMaximumRetries)
					{
						FransBotLog.BotDebug(world,
							"{0}: completed naval producer {1} on Building queue {2} failed physical placement confirmation {3} time(s); cancelling the stale READY item so naval support can replan instead of deadlocking the shared queue.",
							player, current.Item, queue.Actor.ActorID, landingCraftProducerPlacementRetries);
						bot.QueueOrder(Order.CancelProduction(queue.Actor, current.Item, 1));
						ResetLandingCraftProducerPlacementWatchdog();
						InvalidateLandingCraftProducerLocationCache();
						ReleaseBaseBuilderLock();
						return false;
					}
				}
				else
					landingCraftProducerPlacementRetries = 0;

				landingCraftProducerPlacementItem = current.Item;
				landingCraftProducerPlacementQueueActorId = queue.Actor.ActorID;
				landingCraftProducerPlacementIssuedTick = world.WorldTick;
				FransBotLog.BotDebug(world, "{0}: placing requested naval producer {1} at {2} for naval capability; placement watchdog retry {3}/{4}.",
					player, current.Item, location.Value, landingCraftProducerPlacementRetries, Info.LandingCraftProducerPlacementMaximumRetries);
				bot.QueueOrder(new Order("PlaceBuilding", playerActor, Target.FromCell(world, location.Value), false)
				{
					TargetString = current.Item,
					ExtraLocation = CPos.Zero,
					ExtraData = queue.Actor.ActorID,
					SuppressVisualFeedback = true
				});
				return true;
			}

			// Leave unrelated shared-queue work alone. Once the queue is free, select
			// the faction-specific producer that is currently buildable.
			var freeQueue = buildingQueues.FirstOrDefault(q => !q.AllQueued().Any());
			if (freeQueue == null)
			{
				// Unrelated Building work is not NAVAL SUPPORT progress. Returning false lets the
				// existing bounded watchdog detect a real bootstrap stall instead of being reset forever.
				ReleaseBaseBuilderLock();
				return false;
			}

			var producerType = Info.LandingCraftProducerTypes
				.OrderBy(type => type)
				.FirstOrDefault(type => freeQueue.BuildableItems().Any(item => item.Name == type) &&
					FindLandingCraftProducerLocation(type, requiredNavalRegion).HasValue);

			if (producerType == null)
			{
				ReleaseBaseBuilderLock();
				return false;
			}

			GrantBaseBuilderLock();
			ResetLandingCraftProducerPlacementWatchdog();
			FransBotLog.BotDebug(world, "{0}: naval capability demand requires faction naval structure {1}; producing it before any demand-only LST can be built.",
				player, producerType);
			bot.QueueOrder(Order.StartProduction(freeQueue.Actor, producerType, 1));
			return true;
		}

		void InvalidateLandingCraftProducerLocationCache()
		{
			cachedLandingCraftProducerLocations.Clear();
			cachedLandingCraftProducerLocationUntilTicks.Clear();
			cachedLandingCraftProducerBuildAreaRevisions.Clear();
			cachedLandingCraftBuildAreaRevisionTick = -1;
		}

		int ComputeLandingCraftProducerBuildAreaRevision()
		{
			if (cachedLandingCraftBuildAreaRevisionTick == world.WorldTick)
				return cachedLandingCraftBuildAreaRevision;

			unchecked
			{
				var revision = 17;
				foreach (var actor in world.ActorsHavingTrait<GivesBuildableArea>()
					.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player)
					.OrderBy(a => a.ActorID))
				{
					revision = revision * 31 + (int)actor.ActorID;
					revision = revision * 31 + actor.Location.X;
					revision = revision * 31 + actor.Location.Y;
				}
				cachedLandingCraftBuildAreaRevision = revision;
				cachedLandingCraftBuildAreaRevisionTick = world.WorldTick;
				return revision;
			}
		}

		bool PlacementTouchesNavalRegion(CPos cell, int navalRegion)
		{
			if (IsCellInNavalRegion(cell, navalRegion))
				return true;

			return world.Map.FindTilesInCircle(cell, 3)
				.Where(world.Map.Contains)
				.Any(c => IsCellInNavalRegion(c, navalRegion));
		}

		CPos? FindLandingCraftProducerLocation(string producerType) =>
			FindLandingCraftProducerLocation(producerType, null);

		CPos? FindLandingCraftProducerLocation(string producerType, int? requiredNavalRegion)
		{
			if (!world.Map.Rules.Actors.TryGetValue(producerType, out var actorInfo))
				return null;

			var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return null;

			var cacheKey = requiredNavalRegion.HasValue
				? $"{producerType}|R{requiredNavalRegion.Value}"
				: $"{producerType}|ANY";
			var buildAreaRevision = ComputeLandingCraftProducerBuildAreaRevision();
			if (cachedLandingCraftProducerLocationUntilTicks.TryGetValue(cacheKey, out var cacheUntil) &&
				world.WorldTick < cacheUntil &&
				cachedLandingCraftProducerBuildAreaRevisions.TryGetValue(cacheKey, out var cachedRevision) && cachedRevision == buildAreaRevision &&
				cachedLandingCraftProducerLocations.TryGetValue(cacheKey, out var cachedLocation))
			{
				if (!cachedLocation.HasValue)
					return null;

				var cached = cachedLocation.Value;
				if (world.Map.Contains(cached) &&
					(!requiredNavalRegion.HasValue || PlacementTouchesNavalRegion(cached, requiredNavalRegion.Value)) &&
					world.CanPlaceBuilding(cached, actorInfo, buildingInfo, null) &&
					buildingInfo.IsCloseEnoughToBase(world, player, actorInfo, null, cached) &&
					!riskModelService.EvaluateStrategicCell(cached, FransRiskRole.BuildingPlacement, FransRiskTolerance.Cautious).IsCritical)
					return cached;
			}

			var origin = activeMcv?.Location ?? activeConyard?.Location ?? mainConyard?.Location ?? CPos.Zero;
			CPos? result = null;
			var candidates = world.ActorsHavingTrait<GivesBuildableArea>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player)
				.SelectMany(a => world.Map.FindTilesInCircle(a.Location, Info.LandingCraftProducerSearchRadius))
				.Where(cell => world.Map.Contains(cell))
				.Distinct()
				.Where(cell => !requiredNavalRegion.HasValue || PlacementTouchesNavalRegion(cell, requiredNavalRegion.Value))
				.OrderBy(cell => (cell - origin).LengthSquared)
				.ThenBy(cell => cell.X)
				.ThenBy(cell => cell.Y);

			foreach (var cell in candidates)
				if (world.CanPlaceBuilding(cell, actorInfo, buildingInfo, null) &&
					buildingInfo.IsCloseEnoughToBase(world, player, actorInfo, null, cell) &&
					!riskModelService.EvaluateStrategicCell(cell, FransRiskRole.BuildingPlacement, FransRiskTolerance.Cautious).IsCritical)
				{
					result = cell;
					break;
				}

			cachedLandingCraftProducerLocations[cacheKey] = result;
			cachedLandingCraftProducerBuildAreaRevisions[cacheKey] = buildAreaRevision;
			cachedLandingCraftProducerLocationUntilTicks[cacheKey] =
				world.WorldTick + Info.LandingCraftProducerPlacementScanInterval;
			return result;
		}

		bool IsLiveOwnedMcv(Actor actor)
		{
			if (actor == null || actor.IsDead || actor.Owner != player)
				return false;
			if (actor.IsInWorld)
				return true;

			// Canonical MCV liveness: a passenger inside a live owned transport is still physical
			// construction-yard capacity. Mirror FransTransportCommander's E6 loaded test instead of
			// treating !IsInWorld as death/replacement demand.
			var passenger = actor.TraitOrDefault<Passenger>();
			var transport = passenger?.Transport;
			if (transport == null || !transport.IsInWorld || transport.IsDead || transport.Owner != player)
				return false;
			var cargo = transport.TraitOrDefault<Cargo>();
			return cargo != null && !cargo.IsTraitDisabled && cargo.Passengers.Contains(actor);
		}

		bool IsLiveOwnedLandingCraft(Actor actor)
		{
			return actor != null && actor.IsInWorld && !actor.IsDead && actor.Owner == player &&
				Info.LandingCraftTypes.Contains(actor.Info.Name);
		}

		void AbortSeaMissionBeforeLoad(IBot bot)
		{
			if (activeMcv != null && activeMcv.IsInWorld)
				QueueStopOrder(bot, activeMcv);

			if (activeLandingCraft != null && activeLandingCraft.IsInWorld && !activeLandingCraft.IsDead)
				QueueStopOrder(bot, activeLandingCraft);

			AbortExpansionTaskToIdle(bot, "sea mission aborted before MCV loading completed");
			nextLandExpansionPlanningTick = world.WorldTick;
		}

		void FailSeaMissionAfterLoad(IBot bot)
		{
			// If the LST is lost while carrying the MCV, stock Cargo semantics kill the
			// passenger (EjectOnDeath is false for RA LST). Do not invent an actor here: the
			// replacement-capacity loop restores the proven slot through normal production.
			var craftId = activeLandingCraft?.ActorID ?? 0;
			var mcvId = activeMcv?.ActorID ?? 0;
			var failedObjective = targetResourceCenter;
			var objective = failedObjective.HasValue ? failedObjective.Value.ToString() : "none";
			if (failedObjective.HasValue)
				MarkExpansionAreaFailed(failedObjective.Value, $"loaded MCV transport LST {craftId} was lost during the committed sea corridor");
			FransBotLog.BotDebug(world,
				"{0}: SEA TRANSPORT LOST after MCV loading: LST {1}, cargo MCV {2}, objective {3}. This objective is now SECURE REQUIRED + failure cooldown, so a replacement MCV will not repeat the same fatal ferry until Ground CLEAR reopens the area.",
				player, craftId, mcvId, objective);
			activeMcv = null;
			AbortExpansionTaskToIdle(bot, "loaded MCV transport was lost during the committed sea corridor", failedObjective);
		}

		void ReleaseActiveLandingCraftReservation()
		{
			if (activeLandingCraft != null && activeLandingCraftReservationOwner != null)
				transportService.ReleaseExternalTransport(activeLandingCraft, activeLandingCraftReservationOwner);
			activeLandingCraftReservationOwner = null;
		}

		void ResetSeaMission(bool clearTarget)
		{
			ReleaseBaseBuilderLock();
			ReleaseActiveLandingCraftReservation();
			activeLandingCraft = null;
			pendingMcvLandingCraftReservation = null;

			if (clearTarget)
			{
				ClearTarget();
				return;
			}

			// Keep the strategic ore/deploy reservation, but reset every execution watchdog
			// and cached ferry leg before the same ExpansionTask changes transport method.
			seaPickupMcvCell = null;
			seaPickupCraftCell = null;
			seaLandingCraftCell = null;
			committedSeaGeometrySearch = null;
			ResetTaskExecutionProgress();
		}


		bool TryYieldToEarlierAlliedMcvReservation(IBot bot)
		{
			if (!IsLiveOwnedMcv(activeMcv) || !targetResourceCenter.HasValue || !targetDeployCell.HasValue || targetReservationStartedTick < 0)
				return false;

			var objectiveRadiusSq = Info.AlliedMcvReservationObjectiveRadius * Info.AlliedMcvReservationObjectiveRadius;
			var deployRadiusSq = Info.AlliedMcvReservationDeployRadius * Info.AlliedMcvReservationDeployRadius;
			var ownPlayerActorId = player.PlayerActor.ActorID;
			var alliedPlayerActors = world.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.Owner != player &&
					PlayerRelationship.Ally.HasRelationship(player.RelationshipWith(a.Owner)))
				.Select(a => a.Owner.PlayerActor)
				.Where(a => a != null)
				.Distinct()
				.OrderBy(a => a.ActorID)
				.ToArray();

			foreach (var allyPlayerActor in alliedPlayerActors)
			{
				var allyService = allyPlayerActor.TraitsImplementing<IFransExpansionStateService>().FirstOrDefault();
				if (allyService == null || !allyService.TryGetActiveExpansionReservation(out var allyObjective, out var allyDeploy, out var allyMcvActorId, out var allyReservationTick))
					continue;

				var sameObjective = Info.AlliedMcvReservationObjectiveRadius > 0 &&
					(allyObjective - targetResourceCenter.Value).LengthSquared <= objectiveRadiusSq;
				var overlappingDeploy = Info.AlliedMcvReservationDeployRadius > 0 &&
					(allyDeploy - targetDeployCell.Value).LengthSquared <= deployRadiusSq;
				if (!sameObjective && !overlappingDeploy)
					continue;

				var allyWins = allyReservationTick < targetReservationStartedTick ||
					(allyReservationTick == targetReservationStartedTick && allyPlayerActor.ActorID < ownPlayerActorId);
				if (!allyWins)
					continue;

				var oldObjective = targetResourceCenter.Value;
				var oldDeploy = targetDeployCell.Value;
				QueueStopOrder(bot, activeMcv);
				FransBotLog.BotDebug(world,
					"{0}: ALLIED MCV RESERVATION YIELD: MCV {1} releases objective {2}/deploy {3}; allied PlayerActor {4} MCV {5} reserved conflicting objective {6}/deploy {7} earlier at WT {8} (ours WT {9}). Earlier reservation wins; same-WT ties use PlayerActor ID, so allied MCVs cannot deadlock on one FACT footprint.",
					player, activeMcv, oldObjective, oldDeploy, allyPlayerActor.ActorID, allyMcvActorId, allyObjective, allyDeploy, allyReservationTick, targetReservationStartedTick);

				failedFieldsUntil[oldObjective] = world.WorldTick + Info.FailedFieldRetryDelay;
				AbortExpansionTaskToIdle(bot, "earlier allied MCV owns the conflicting ore/deploy reservation", oldObjective);
				nextLandExpansionPlanningTick = world.WorldTick;

				return true;
			}

			return false;
		}

		bool TryReplanPermanentlyBlockedDeployTarget(IBot bot, Actor mcv, Mobile mobile)
		{
			if (!targetDeployCell.HasValue || !targetResourceCenter.HasValue || CanDeployAt(mcv, targetDeployCell.Value) ||
				!TryGetKnownPermanentDeployBuildingBlocker(mcv, targetDeployCell.Value, out var blocker))
				return false;

			var transforms = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transforms == null || !world.Map.Rules.Actors.TryGetValue(transforms.IntoActor, out var intoActor))
				return false;
			var building = intoActor.TraitInfoOrDefault<BuildingInfo>();
			if (building == null)
				return false;

			var oldDeploy = targetDeployCell.Value;
			if (TryFindSafeDeployPath(mcv, mobile, targetResourceCenter.Value, transforms, intoActor, building, out var alternate, out _) &&
				alternate != oldDeploy)
			{
				targetDeployCell = alternate;
				deployClearanceStartedTick = -1;
				deployClearanceReplans = 0;
				FransBotLog.BotDebug(world,
					"{0}: MCV stale-deploy revalidation: validated FACT cell {1} became permanently occupied by known {2} {3}:{4}; replanning the same objective {5} to legal deploy {6} instead of routing forever into the building.",
					player, oldDeploy, blocker.Owner == player ? "own" : "allied/visible", blocker.Info.Name, blocker.ActorID, targetResourceCenter.Value, alternate);
				QueueRiskAwareMove(mcv, mobile, alternate);
				return true;
			}

			FransBotLog.BotDebug(world,
				"{0}: MCV stale-deploy revalidation rejects objective {1}: FACT cell {2} is permanently occupied by known {3}:{4} and no alternate legal deploy remains.",
				player, targetResourceCenter.Value, oldDeploy, blocker.Info.Name, blocker.ActorID);
			QueueStopOrder(bot, mcv);
			MarkCurrentFieldFailed();
			AbortExpansionTaskToIdle(bot, "known permanent building blocker left no legal deploy cell for this ore");
			nextLandExpansionPlanningTick = world.WorldTick;
			return true;
		}

		bool TryGetKnownPermanentDeployBuildingBlocker(Actor mcv, CPos deployCell, out Actor blocker)
		{
			blocker = null;
			var transforms = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transforms == null || !world.Map.Rules.Actors.TryGetValue(transforms.IntoActor, out var intoActor))
				return false;
			var targetInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			if (targetInfo == null)
				return false;

			var targetOrigin = deployCell + transforms.Offset;
			var targetMaxX = targetOrigin.X + targetInfo.Dimensions.X - 1;
			var targetMaxY = targetOrigin.Y + targetInfo.Dimensions.Y - 1;
			foreach (var actor in world.ActorsHavingTrait<Building>().Where(a => a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null).OrderBy(a => a.ActorID))
			{
				var friendly = actor.Owner == player || PlayerRelationship.Ally.HasRelationship(player.RelationshipWith(actor.Owner));
				if (!friendly && !actor.CanBeViewedByPlayer(player))
					continue;
				var info = actor.Info.TraitInfoOrDefault<BuildingInfo>();
				if (info == null)
					continue;
				var actorMaxX = actor.Location.X + info.Dimensions.X - 1;
				var actorMaxY = actor.Location.Y + info.Dimensions.Y - 1;
				if (targetOrigin.X <= actorMaxX && targetMaxX >= actor.Location.X &&
					targetOrigin.Y <= actorMaxY && targetMaxY >= actor.Location.Y)
				{
					blocker = actor;
					return true;
				}
			}

			return false;
		}

		bool CanDeployAt(Actor mcv, CPos cell)
		{
			var transformsInfo = mcv.Info.TraitInfoOrDefault<TransformsInfo>();
			if (transformsInfo == null)
				return false;

			var intoActor = world.Map.Rules.Actors[transformsInfo.IntoActor];
			var buildingInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			return buildingInfo != null &&
				world.CanPlaceBuilding(cell + transformsInfo.Offset, intoActor, buildingInfo, mcv);
		}

		string FirstExpansionRefineryType() => firstExpansionRefineryReservedType ?? Info.ExpansionRefineryTypes
			.Where(world.Map.Rules.Actors.ContainsKey)
			.OrderBy(t => t)
			.FirstOrDefault();

		void ResetFirstExpansionRefineryPlacementAttempt()
		{
			firstExpansionRefineryPlacementIssued = false;
			firstExpansionRefineryPlacementIssuedTick = -1;
			firstExpansionRefineryPlacementCell = null;
		}

		bool IsFirstExpansionRefineryReadyToPlace()
		{
			var refineryType = FirstExpansionRefineryType();
			if (refineryType == null)
				return false;

			var queue = FindReservedFirstExpansionRefineryQueue(refineryType);
			var current = queue?.AllQueued().FirstOrDefault();
			return current != null && current.Item == refineryType && current.Done;
		}

		ProductionQueue FindReservedFirstExpansionRefineryQueue(string refineryType)
		{
			if (firstExpansionRefineryQueueActor != null && firstExpansionRefineryQueueActor.IsInWorld && !firstExpansionRefineryQueueActor.IsDead)
			{
				var queuesByCategory = AIUtils.FindQueuesByCategory(player);
				var reserved = queuesByCategory[Info.BuildingQueueCategory]
					.Where(q => q.Enabled && q.Actor == firstExpansionRefineryQueueActor &&
						q.BuildableItems().Any(item => item.Name == refineryType))
					.OrderBy(q => q.Actor.ActorID)
					.FirstOrDefault();
				if (reserved != null)
					return reserved;
			}

			return FindQueueFor(refineryType, Info.BuildingQueueCategory);
		}

		void RefreshFirstExpansionRefineryMilestone(IBot bot)
		{
			if (firstExpansionRefineryReservationCompleted || mainConyard == null ||
				firstExpansionRefinerySuspendedForInfrastructure || coastalStagingForSeaExpansion ||
				expansionTask.Mode == ExpansionTaskMode.CoastalStaging)
				return;

			var refineryType = FirstExpansionRefineryType();
			if (refineryType == null)
				return;

			var radiusSq = Info.ExpansionStructureMaxRadius * Info.ExpansionStructureMaxRadius;
			var expansionFacts = constructionYards.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.Owner == player && a != mainConyard)
				.OrderBy(a => a.ActorID)
				.ToArray();
			if (expansionFacts.Length == 0)
				return;

			var refineries = world.ActorsHavingTrait<Building>()
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.Owner == player && a.Info.Name == refineryType)
				.OrderBy(a => a.ActorID)
				.ToArray();

			Actor milestoneFact = null;
			Actor milestoneRefinery = null;
			foreach (var fact in expansionFacts)
			{
				var refinery = refineries
					.Where(a => (a.Location - fact.Location).LengthSquared <= radiusSq)
					.OrderBy(a => (a.Location - fact.Location).LengthSquared)
					.ThenBy(a => a.ActorID)
					.FirstOrDefault();
				if (refinery == null)
					continue;
				milestoneFact = fact;
				milestoneRefinery = refinery;
				break;
			}

			if (milestoneRefinery == null)
				return;

			// Historical milestone: once any real post-opening expansion FACT has physically
			// hosted a refinery, the one-shot first-expansion reserve is permanently satisfied.
			// This survives later FACT repacks, task=None/Idle and queue cancellation/rebuilds.
			var queue = FindReservedFirstExpansionRefineryQueue(refineryType);
			var reserved = queue?.AllQueued().FirstOrDefault(item => item.Item == refineryType);
			if (firstExpansionRefineryReservationActive && queue != null && reserved != null)
				bot.QueueOrder(Order.CancelProduction(queue.Actor, refineryType, 1));

			firstExpansionRefineryReservationActive = false;
			firstExpansionRefineryReservationCompleted = true;
			firstExpansionRefinerySuspendedForInfrastructure = false;
			firstExpansionRefineryInfrastructureSuspensionStartedTick = -1;
			firstExpansionRefineryRetryHold = false;
			firstExpansionRefineryNoObjectiveSinceTick = -1;
			firstExpansionRefineryQueueActor = null;
			firstExpansionRefineryReservedType = null;
			firstExpansionRefineryExistingActors.Clear();
			ResetFirstExpansionRefineryPlacementAttempt();
			ReleaseBaseBuilderLock();

			FransBotLog.BotDebug(world,
				"{0}: FIRST EXPANSION historical milestone is permanently satisfied: physical expansion FACT {1} at {2} has refinery {3} at {4}. The protected first-expansion PROC reserve can never reappear even if this FACT later repacks or the expansion task returns to Idle.",
				player, milestoneFact.ActorID, milestoneFact.Location, milestoneRefinery.ActorID, milestoneRefinery.Location);
		}

		void BeginFirstExpansionRefineryReservation(ProductionQueue queue, string refineryType)
		{
			if (firstExpansionRefineryReservationActive)
				return;

			firstExpansionRefineryReservationActive = true;
			firstExpansionRefineryQueueActor = queue.Actor;
			firstExpansionRefineryReservedType = refineryType;
			firstExpansionRefineryPlacementCell = null;
			firstExpansionRefineryPlacementIssued = false;
			firstExpansionRefineryNoObjectiveSinceTick = HasCommittedFirstExpansionRefineryRetryObjective() ? -1 : world.WorldTick;
			firstExpansionRefineryExistingActors.Clear();
			foreach (var actor in world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && a.Info.Name == refineryType))
				firstExpansionRefineryExistingActors.Add(actor);
		}

		bool HasQueuedLandingCraftProducerForCurrentDemand()
		{
			var hasRequiredRegion = TryGetRequiredLandingCraftProductionRegion(out var requiredNavalRegion);
			var queues = AIUtils.FindQueuesByCategory(player)[Info.BuildingQueueCategory]
				.Where(q => q.Enabled)
				.OrderBy(q => q.Actor.ActorID);
			foreach (var queue in queues)
			{
				var current = queue.AllQueued().FirstOrDefault();
				if (current == null || !Info.LandingCraftProducerTypes.Contains(current.Item))
					continue;

				if (!hasRequiredRegion || FindLandingCraftProducerLocation(current.Item, requiredNavalRegion).HasValue)
					return true;
			}

			return false;
		}

		bool ShouldKeepFirstExpansionRefineryInfrastructureSuspended()
		{
			if (!firstExpansionRefinerySuspendedForInfrastructure || firstExpansionRefineryReservationCompleted)
				return false;

			if (firstExpansionRefineryInfrastructureSuspensionStartedTick >= 0 &&
				world.WorldTick - firstExpansionRefineryInfrastructureSuspensionStartedTick < Info.FirstExpansionRefineryInfrastructureSuspensionGraceTicks)
				return true;

			if (coastalStagingForSeaExpansion || expansionTask.Mode == ExpansionTaskMode.CoastalStaging)
				return true;

			if (expansionTask.Mode == ExpansionTaskMode.SeaOre && stage != ExpansionStage.Idle && stage != ExpansionStage.Retreat)
				return true;

			var hasRequiredRegion = TryGetRequiredLandingCraftProductionRegion(out var requiredNavalRegion);
			if (hasRequiredRegion
				? HasOwnedLandingCraftProducer(requiredNavalRegion)
				: HasOwnedLandingCraftProducer())
				return false;

			return HasQueuedLandingCraftProducerForCurrentDemand();
		}

		void SuspendFirstExpansionRefineryForInfrastructure(IBot bot, string reason)
		{
			if (firstExpansionRefineryReservationCompleted || firstExpansionRefinerySuspendedForInfrastructure)
				return;

			var refineryType = FirstExpansionRefineryType();
			var queue = refineryType == null ? null : FindReservedFirstExpansionRefineryQueue(refineryType);
			var reserved = queue?.AllQueued().FirstOrDefault(item => item.Item == refineryType);
			var cancelled = queue != null && reserved != null;
			if (cancelled)
				bot.QueueOrder(Order.CancelProduction(queue.Actor, refineryType, 1));

			// Keep the strategic one-shot requirement, but relinquish all concrete Building-queue
			// ownership while naval infrastructure is being created. Resume reacquires a fresh
			// queue snapshot; no READY PROC can therefore hostage SPEN/SYRD production.
			firstExpansionRefineryReservationActive = false;
			firstExpansionRefinerySuspendedForInfrastructure = true;
			firstExpansionRefineryInfrastructureSuspensionStartedTick = world.WorldTick;
			firstExpansionRefineryRetryHold = false;
			firstExpansionRefineryNoObjectiveSinceTick = -1;
			firstExpansionRefineryQueueActor = null;
			firstExpansionRefineryReservedType = null;
			firstExpansionRefineryExistingActors.Clear();
			ResetFirstExpansionRefineryPlacementAttempt();
			ReleaseBaseBuilderLock();

			FransBotLog.BotDebug(world,
				"{0}: FIRST EXPANSION PROC SUSPENDED FOR NAVAL INFRASTRUCTURE: {1}. Exact reserved PROC queue item {2}; shared Building queue is released until SPEN/SYRD support either becomes real or is abandoned.",
				player, reason, cancelled ? "cancelled" : "was not present");
		}

		void AbortFirstExpansionRefineryAttempt(IBot bot, string reason, CPos? failedSite = null)
		{
			if (firstExpansionRefineryReservationCompleted)
				return;

			// Idempotent: multiple loss/abort paths may observe the same failed attempt on adjacent scans.
			if (firstExpansionRefineryRetryHold && !firstExpansionRefineryReservationActive &&
				!firstExpansionRefinerySuspendedForInfrastructure && firstExpansionRefineryQueueActor == null &&
				!firstExpansionRefineryPlacementIssued)
				return;

			var refineryType = FirstExpansionRefineryType();
			if (refineryType != null)
			{
				var placed = FindPhysicallyPlacedReservedFirstExpansionRefinery(refineryType);
				if (placed != null)
				{
					CompleteFirstExpansionRefineryReservation(placed);
					return;
				}
			}

			ProductionQueue queue = null;
			if (refineryType != null && firstExpansionRefineryQueueActor != null &&
				firstExpansionRefineryQueueActor.IsInWorld && !firstExpansionRefineryQueueActor.IsDead)
			{
				var queuesByCategory = AIUtils.FindQueuesByCategory(player);
				queue = queuesByCategory[Info.BuildingQueueCategory]
					.Where(q => q.Enabled && q.Actor == firstExpansionRefineryQueueActor &&
						q.BuildableItems().Any(item => item.Name == refineryType))
					.OrderBy(q => q.Actor.ActorID)
					.FirstOrDefault();
			}

			var reserved = queue?.AllQueued().FirstOrDefault(item => item.Item == refineryType);
			var cancellationQueued = queue != null && reserved != null;
			if (cancellationQueued)
				bot.QueueOrder(Order.CancelProduction(queue.Actor, refineryType, 1));

			firstExpansionRefineryReservationActive = false;
			firstExpansionRefinerySuspendedForInfrastructure = false;
			firstExpansionRefineryInfrastructureSuspensionStartedTick = -1;
			firstExpansionRefineryQueueActor = null;
			firstExpansionRefineryReservedType = null;
			firstExpansionRefineryExistingActors.Clear();
			ResetFirstExpansionRefineryPlacementAttempt();
			firstExpansionRefineryRetryHold = true;
			firstExpansionRefineryNoObjectiveSinceTick = -1;
			ReleaseBaseBuilderLock();

			FransBotLog.BotDebug(world,
				"{0}: first-expansion PROC attempt ABORTED with expansion lifetime after {1} at {2}; exact reserved Building-queue item {3}. Retry-hold remains until a new MCV expansion objective is committed.",
				player, reason, failedSite.HasValue ? failedSite.Value.ToString() : "unknown site",
				cancellationQueued ? "cancelled" : "was already absent");
		}

		void ResumeFirstExpansionRefineryAfterInfrastructure(string reason)
		{
			if (!firstExpansionRefinerySuspendedForInfrastructure)
				return;

			firstExpansionRefinerySuspendedForInfrastructure = false;
			firstExpansionRefineryInfrastructureSuspensionStartedTick = -1;
			firstExpansionRefineryReservationActive = false;
			firstExpansionRefineryQueueActor = null;
			firstExpansionRefineryReservedType = null;
			firstExpansionRefineryExistingActors.Clear();
			ResetFirstExpansionRefineryPlacementAttempt();
			ReleaseBaseBuilderLock();
			FransBotLog.BotDebug(world,
				"{0}: FIRST EXPANSION PROC RESUMED AFTER NAVAL INFRASTRUCTURE: {1}. The next prebuild pass reacquires a fresh Building queue and the refinery is still satisfied only beside a real ore-expansion FACT.",
				player, reason);
		}

		Actor FindPhysicallyPlacedReservedFirstExpansionRefinery(string refineryType)
		{
			if (activeConyard == null || !activeConyard.IsInWorld || activeConyard.IsDead)
				return null;

			var maxRadiusSquared = Info.ExpansionStructureMaxRadius * Info.ExpansionStructureMaxRadius;
			return world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && a.Info.Name == refineryType &&
					!firstExpansionRefineryExistingActors.Contains(a) &&
					(a.Location - activeConyard.Location).LengthSquared <= maxRadiusSquared)
				.OrderBy(a => firstExpansionRefineryPlacementCell.HasValue
					? (a.Location - firstExpansionRefineryPlacementCell.Value).LengthSquared
					: (a.Location - activeConyard.Location).LengthSquared)
				.ThenBy(a => a.ActorID)
				.FirstOrDefault();
		}

		void CompleteFirstExpansionRefineryReservation(Actor placed)
		{
			firstExpansionRefineryReservationActive = false;
			firstExpansionRefineryReservationCompleted = true;
			firstExpansionRefinerySuspendedForInfrastructure = false;
			firstExpansionRefineryInfrastructureSuspensionStartedTick = -1;
			firstExpansionRefineryRetryHold = false;
			firstExpansionRefineryNoObjectiveSinceTick = -1;
			ResetFirstExpansionRefineryPlacementAttempt();
			GrantBaseBuilderLock();
			FransBotLog.BotDebug(world,
				"{0}: reserved first-expansion PROC actor {1} is physically established beside the first expansion FACT; exact reservation completed without accepting an older nearby refinery.",
				player, placed);
		}

		bool ManageReservedFirstExpansionRefinery(IBot bot, string refineryType)
		{
			if (firstExpansionRefinerySuspendedForInfrastructure)
			{
				ReleaseBaseBuilderLock();
				return false;
			}

			var placed = FindPhysicallyPlacedReservedFirstExpansionRefinery(refineryType);
			if (placed != null)
			{
				CompleteFirstExpansionRefineryReservation(placed);
				return true;
			}

			GrantBaseBuilderLock();
			if (firstExpansionRefineryPlacementIssued)
			{
				if (firstExpansionRefineryPlacementIssuedTick >= 0 &&
					world.WorldTick - firstExpansionRefineryPlacementIssuedTick < Info.FirstExpansionRefineryPlacementConfirmTimeoutTicks)
					return false;

				placementFailures++;
				FransBotLog.BotDebug(world,
					"{0}: protected first-expansion PROC placement at {1} was not physically confirmed within {2} WT; clearing the stale placement latch and retrying from current BuildingInfluence instead of leaving the READY queue item deadlocked.",
					player, firstExpansionRefineryPlacementCell.HasValue ? firstExpansionRefineryPlacementCell.Value.ToString() : "unknown",
					Info.FirstExpansionRefineryPlacementConfirmTimeoutTicks);
				ResetFirstExpansionRefineryPlacementAttempt();
				if (placementFailures >= Info.MaximumPlacementFailures)
				{
					AbortTemporaryExpansion(bot, refineryPlacementFailure: true);
					return false;
				}
			}

			var queue = FindReservedFirstExpansionRefineryQueue(refineryType);
			if (queue == null)
				return false;

			firstExpansionRefineryQueueActor = queue.Actor;
			var current = queue.AllQueued().FirstOrDefault();
			if (current == null)
			{
				FransBotLog.BotDebug(world,
					"{0}: reserved first-expansion PROC queue item disappeared before expansion placement; rebuilding the same one-shot refinery in the reserved Building queue.",
					player);
				bot.QueueOrder(Order.StartProduction(queue.Actor, refineryType, 1));
				return false;
			}

			if (current.Item != refineryType || !current.Done)
				return false;

			var location = FindExpansionStructureLocation(refineryType, Info.ExpansionStructureMinRadius, Info.ExpansionStructureMaxRadius);
			if (!location.HasValue)
			{
				if (TryClearFriendlyConstructionBlockers(bot, activeConyard.Location, Info.ExpansionStructureMaxRadius))
				{
					placementFailures = 0;
					return false;
				}

				if (++placementFailures >= Info.MaximumPlacementFailures)
					AbortTemporaryExpansion(bot, refineryPlacementFailure: true);
				return false;
			}

			firstExpansionRefineryPlacementIssued = true;
			firstExpansionRefineryPlacementIssuedTick = world.WorldTick;
			firstExpansionRefineryPlacementCell = location.Value;
			FransBotLog.BotDebug(world,
				"{0}: placing the exact reserved first-expansion PROC at {1} beside first expansion FACT {2}; older nearby refineries are ignored for reservation completion.",
				player, location.Value, activeConyard);
			bot.QueueOrder(new Order("PlaceBuilding", playerActor, Target.FromCell(world, location.Value), false)
			{
				TargetString = refineryType,
				ExtraLocation = CPos.Zero,
				ExtraData = queue.Actor.ActorID,
				SuppressVisualFeedback = true
			});
			return false;
		}

		bool HasCommittedFirstExpansionRefineryRetryObjective() =>
			IsLiveOwnedMcv(activeMcv) &&
			targetResourceCenter.HasValue && stage != ExpansionStage.Idle && stage != ExpansionStage.WaitingForMcv &&
			stage != ExpansionStage.Retreat && stage != ExpansionStage.EmergencyMainBaseRecovery;

		void ManageFirstExpansionRefineryPrebuild(IBot bot)
		{
			if (firstExpansionRefineryReservationCompleted || firstExpansionRefinerySuspendedForInfrastructure)
				return;

			if (firstExpansionRefineryReservationActive)
			{
				if (HasCommittedFirstExpansionRefineryRetryObjective())
					firstExpansionRefineryNoObjectiveSinceTick = -1;
				else
				{
					if (firstExpansionRefineryNoObjectiveSinceTick < 0)
						firstExpansionRefineryNoObjectiveSinceTick = world.WorldTick;
					if (world.WorldTick - firstExpansionRefineryNoObjectiveSinceTick >= Info.FirstExpansionRefineryObjectiveGraceTicks)
					{
						AbortFirstExpansionRefineryAttempt(bot,
							$"no committed MCV expansion objective remained for {Info.FirstExpansionRefineryObjectiveGraceTicks} WT");
						return;
					}
				}
			}

			if (firstExpansionRefineryRetryHold)
			{
				if (!HasCommittedFirstExpansionRefineryRetryObjective())
					return;

				firstExpansionRefineryRetryHold = false;
				FransBotLog.BotDebug(world,
					"{0}: first-expansion PROC retry-hold released for committed MCV {1} objective {2}; Building-queue prebuild may resume for this new attempt.",
					player, activeMcv, targetResourceCenter.Value);
			}

			// Once reservation starts, keep following that exact Building queue. reserves
			// immediately after the first opening MCV becomes physical, before any optional post-opening
			// Building work. The completed PROC may wait in the queue until the real expansion FACT exists.
			if (!firstExpansionRefineryReservationActive &&
				!openingBuildOrderService.ReadyForFirstExpansionRefineryPrebuild)
				return;

			var refineryType = FirstExpansionRefineryType();
			if (refineryType == null)
				return;

			var queue = firstExpansionRefineryReservationActive
				? FindReservedFirstExpansionRefineryQueue(refineryType)
				: FindQueueFor(refineryType, Info.BuildingQueueCategory);
			if (queue == null)
				return;

			var current = queue.AllQueued().FirstOrDefault();
			if (current != null && current.Item != refineryType)
				return;

			if (!firstExpansionRefineryReservationActive)
				BeginFirstExpansionRefineryReservation(queue, refineryType);

			if (current == null)
			{
				FransBotLog.BotDebug(world,
					"{0}: reserves first expansion refinery {1} immediately after the opening MCV becomes physical; this is the first normal post-MCV Building item and may remain completed in the shared queue until the expansion FACT can place it.",
					player, refineryType);
				bot.QueueOrder(Order.StartProduction(queue.Actor, refineryType, 1));
			}
		}

		void FindExpansionConyard(IBot bot)
		{
			if (!lastTransformCell.HasValue)
				return;

			var maxDistanceSquared = 4 * 4;
			var conyard = constructionYards.Actors
				.Where(a => a.IsInWorld && !a.IsDead && a != mainConyard)
				.Where(a => (a.Location - lastTransformCell.Value).LengthSquared <= maxDistanceSquared)
				.OrderBy(a => (a.Location - lastTransformCell.Value).LengthSquared)
				.ThenByDescending(a => a.ActorID)
				.FirstOrDefault();

			if (conyard == null)
			{
				// Deploy-confirm watchdog. A native DeployTransform order can be
				// rejected after our pre-check because the footprint changes before the order
				// executes. Previously WaitingForConyard then had no timeout and the MCV could
				// remain parked forever.
				if (conyardTransformIssuedTick < 0 ||
					world.WorldTick - conyardTransformIssuedTick < Info.ExpansionDeployConfirmTimeoutTicks)
					return;

				if (!IsLiveOwnedMcv(activeMcv))
				{
					FransBotLog.BotDebug(world,
						"{0}: expansion deploy-confirm watchdog found neither the original MCV nor a new FACT after {1} WT; clearing the stale expansion state so another MCV/field can continue the chain.",
						player, Info.ExpansionDeployConfirmTimeoutTicks);
					activeMcv = null;
					LogMcvWaitingState(null, "DeployConfirmationLostOriginalMcv");
					AbortExpansionTaskToIdle(bot, "deploy-confirm watchdog found neither the committed MCV nor a resulting FACT");
					nextLandExpansionPlanningTick = world.WorldTick;
					return;
				}

				var mobile = activeMcv.TraitOrDefault<Mobile>();
				if (mobile != null && !mobile.IsTraitDisabled && !mobile.IsTraitPaused &&
					conyardTransformRetries < Info.ExpansionDeployMaximumRetries)
				{
					if (CanDeployAt(activeMcv, activeMcv.Location))
					{
						// Native deployment must begin from synchronized idle state. Stop any
						// remaining activity through the order system, then retry on a later tick.
						if (!activeMcv.IsIdle)
						{
							LogMcvDeployment(activeMcv, false, "DeployRetryStopIssuedWaitingForIdle");
							LogMcvWaitingState(activeMcv, "WaitingForIdleBeforeDeployRetry");
							QueueStopOrder(bot, activeMcv);
							return;
						}

						conyardTransformRetries++;
						conyardTransformIssuedTick = world.WorldTick;
						lastTransformCell = activeMcv.Location;
						FransBotLog.BotDebug(world,
							"{0}: expansion deploy-confirm watchdog found MCV {1} still mobile after {2} WT; retrying DeployTransform at {3} ({4}/{5}).",
							player, activeMcv, Info.ExpansionDeployConfirmTimeoutTicks, activeMcv.Location,
							conyardTransformRetries, Info.ExpansionDeployMaximumRetries);
						LogMcvDeployment(activeMcv, true, $"DeployConfirmRetry{conyardTransformRetries}");
						bot.QueueOrder(new Order("DeployTransform", activeMcv, true));
						return;
					}

					if (TryClearFriendlyDeploymentBlockers(bot, activeMcv, activeMcv.Location))
					{
						conyardTransformRetries++;
						conyardTransformIssuedTick = world.WorldTick;
						FransBotLog.BotDebug(world,
							"{0}: expansion deploy-confirm watchdog found a newly blocked FACT footprint at {1}; clearing friendly blockers before retry cycle {2}/{3}.",
							player, activeMcv.Location, conyardTransformRetries, Info.ExpansionDeployMaximumRetries);
						LogMcvDeployment(activeMcv, false, $"DeployRetryFootprintBlocked{conyardTransformRetries}");
						return;
					}
				}

				var failedCell = targetResourceCenter ?? lastTransformCell.Value;
				FransBotLog.BotDebug(world,
					"{0}: expansion deploy-confirm watchdog gives up on ore field {1}: MCV {2} remained undeployed after {3} retry attempt(s). Rejecting this field and immediately selecting another expansion.",
					player, failedCell, activeMcv, conyardTransformRetries);
				LogMcvDeployment(activeMcv, false, "DeployConfirmRetriesExhausted");
				MarkCurrentFieldFailed();
				QueueStopOrder(bot, activeMcv);
				AbortExpansionTaskToIdle(bot, "MCV deploy-confirm abort after bounded transform retries", failedCell);
				return;
			}

			conyardTransformIssuedTick = -1;
			conyardTransformRetries = 0;
			activeConyard = conyard;
			activeMcv = null;
			nextCoastalStagingSearchTick = 0;
			InvalidateLandingCraftProducerLocationCache();
			if (!coastalStagingForSeaExpansion)
				ResumeFirstExpansionRefineryAfterInfrastructure("the real first ore-expansion FACT is physically established");

			// Every autonomous ore outpost follows the same FACT -> PROC chain. If this FACT later
			// proves to be inside a militarily secured area, completion performs a read-only handoff
			// to BaseBuilder/DefenseCommander instead of giving General any MCV ownership.
			stage = ExpansionStage.BuildingRefinery;
			placementFailures = 0;
			if (coastalStagingForSeaExpansion)
			{
				coastalStagingNavalNoProgressSinceTick = world.WorldTick;
				GrantBaseBuilderLock();
			}
			else
			{
				// CLAIM owns the shared Building queue boundary until its physical PROC exists.
				// This prevents BaseBuilder from turning a temporary ore claim into a normal
				// permanent base package before the repack/settle decision is made.
				GrantBaseBuilderLock();
			}

			FransBotLog.BotDebug(world,
				coastalStagingForSeaExpansion
					? "{0}: coastal staging FACT {1} established at {2}; it will hold this shoreline build radius until SPEN/SYRD and an LST exist, then repack and resume the blocked sea expansion."
					: "{0}: expansion conyard {1} established at ore field {2}; waiting for its turn on the shared Building queue.",
				player, activeConyard, targetResourceCenter);
		}

		void ManageExpansionConyard(IBot bot)
		{
			var conyardTolerance = CurrentMcvRiskTolerance;
			var conyardRisk = riskModelService.EvaluateImmediateRisk(
				activeConyard, activeConyard.Location, FransRiskRole.Mcv, conyardTolerance);
			var retreatFromConyard = conyardRisk.IsCritical ||
				(Info.EnableMcvRetreat && conyardRisk.RecentlyDamaged &&
				conyardRisk.RecentDamageRiskScore >= Info.ExpansionConyardRetreatRecentDamageRisk);
			if (retreatFromConyard)
			{
				var incidentCenter = targetResourceCenter ?? activeConyard.Location;
				RememberDangerousExpansionArea(incidentCenter);
				FransBotLog.BotDebug(world,
					"{0}: expansion FACT {1} enters the simple MCV RETREAT path after {2} at {3} (risk {4}/{5}, recent-damage risk {6}); repacking first, then the resulting MCV will plain-Move to the nearest Ground regroup point.",
					player, activeConyard, conyardRisk.RecentlyDamaged ? "recent damage" : "critical risk", activeConyard.Location, conyardRisk.Score, conyardRisk.CriticalThreshold, conyardRisk.RecentDamageRiskScore);
				AbortTemporaryExpansion(bot, retreatAfterRepack: true);
				return;
			}

			if (!conyardRisk.IsPreferred && world.WorldTick >= nextNoOreStatusLogTick)
			{
				nextNoOreStatusLogTick = world.WorldTick + 500;
				FransBotLog.BotDebug(world,
					"{0}: RiskModel keeps expansion FACT {1} despite elevated non-critical risk {2}/{3}; tolerance {4}, static threats {5}, recent-damage risk {6}.",
					player, activeConyard, conyardRisk.Score, conyardRisk.CriticalThreshold, conyardTolerance, conyardRisk.StaticThreatCount, conyardRisk.RecentDamageRiskScore);
			}

			if (coastalStagingForSeaExpansion)
			{
				ManageCoastalStagingConyard(bot);
				return;
			}

			if (stage == ExpansionStage.HoldingCompletedOutpost)
			{
				ManageCompletedOutpostHold(bot);
				return;
			}

			// An ordinary temporary CLAIM permits only its required PROC before the
			// repack/settle decision. BaseBuilder resumes after that decision.
			GrantBaseBuilderLock();

			var refineryType = FindUsableExpansionType(Info.ExpansionRefineryTypes, Info.BuildingQueueCategory, Info.ExpansionStructureMaxRadius);
			if (refineryType == null)
				return;

			// The first-expansion PROC is an exact one-shot reserved queue item.
			// The reservation follows the exact queue item and confirms a NEW refinery actor;
			// an older PROC that merely happens to sit within the expansion radius can never satisfy it.
			if (firstExpansionRefineryReservationActive)
			{
				stage = ExpansionStage.BuildingRefinery;
				if (!ManageReservedFirstExpansionRefinery(bot, refineryType))
					return;
			}

			if (!HasStructureNear(refineryType, activeConyard.Location, Info.ExpansionStructureMaxRadius))
			{
				stage = ExpansionStage.BuildingRefinery;
				EnsureStructure(bot, refineryType, Info.BuildingQueueCategory,
					Info.ExpansionStructureMinRadius, Info.ExpansionStructureMaxRadius);
				return;
			}

			CompleteExpansionOutpost(bot, refineryType);
		}

		void ManageCoastalStagingConyard(IBot bot)
		{
			var requiredNavalRegion = 0;
			var hasRequiredRegion = coastalStagingRequiredNavalRegion.HasValue;
			if (hasRequiredRegion)
				requiredNavalRegion = coastalStagingRequiredNavalRegion.Value;
			else if (deferredRoutineFerryObjective.HasValue)
				hasRequiredRegion = TryGetPreferredRoutinePickupNavalRegion(out requiredNavalRegion);
			// The same exact naval-producer resolver is the sole authority for both BaseBuilder
			// and NAVAL SUPPORT. A committed ferry requires the producer to launch into its pickup
			// naval region; a producer on another disconnected sea is not naval progress.
			if (!(hasRequiredRegion
				? CanPlaceAnyLandingCraftProducerFromCurrentBase(requiredNavalRegion)
				: CanPlaceAnyLandingCraftProducerFromCurrentBase()))
			{
				MarkCurrentFieldFailed();
				lastTransformCell = activeConyard.Location;
				coastalStagingReturnToSea = true;
				coastalStagingRepackOutcome = CoastalStagingRepackOutcome.RetryPlacementRejected;
				stage = ExpansionStage.WaitingForMcv;
				repackTransformIssuedTick = world.WorldTick;
				repackTransformRetries = 0;
				nextCoastalStagingSearchTick = world.WorldTick;
				coastalStagingNavalNoProgressSinceTick = -1;
				ReleaseBaseBuilderLock();
				FransBotLog.BotDebug(world,
					"{0}: NAVAL SUPPORT coastal staging FACT {1} at {2} is rejected immediately: unified SPEN/SYRD resolver finds no legal naval-production footprint from the current buildable area. Repacking now instead of entering the producer/cancel watchdog loop.",
					player, activeConyard, activeConyard.Location);
				bot.QueueOrder(new Order("DeployTransform", activeConyard, true));
				return;
			}

			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var shipQueues = ShipQueueNames().SelectMany(name => queuesByCategory[name])
				.Where(q => q.Enabled)
				.Distinct()
				.ToArray();
			var producerProgress = EnsureLandingCraftProducer(bot, queuesByCategory, shipQueues,
				hasRequiredRegion ? requiredNavalRegion : null);
			if (!(hasRequiredRegion ? HasOwnedLandingCraftProducer(requiredNavalRegion) : HasOwnedLandingCraftProducer()))
			{
				if (producerProgress)
					coastalStagingNavalNoProgressSinceTick = world.WorldTick;
				else
				{
					if (coastalStagingNavalNoProgressSinceTick < 0)
						coastalStagingNavalNoProgressSinceTick = world.WorldTick;

					if (world.WorldTick - coastalStagingNavalNoProgressSinceTick >= Info.CoastalStagingNavalProducerTimeoutTicks)
					{
						// The FACT is physically coastal but still cannot queue/place SPEN/SYRD.
						// Repack this same slot, temporarily blacklist the failed staging cell, and
						// retry elsewhere. Keep first-PROC suspension active: restoring it here would
						// recreate the original queue dependency before naval access exists.
						MarkCurrentFieldFailed();
						lastTransformCell = activeConyard.Location;
						coastalStagingReturnToSea = true;
						coastalStagingRepackOutcome = CoastalStagingRepackOutcome.RetryProducerTimeout;
						stage = ExpansionStage.WaitingForMcv;
						repackTransformIssuedTick = world.WorldTick;
						repackTransformRetries = 0;
						nextCoastalStagingSearchTick = world.WorldTick;
						coastalStagingNavalNoProgressSinceTick = -1;
						ReleaseBaseBuilderLock();
						FransBotLog.BotDebug(world,
							"{0}: NAVAL SUPPORT coastal staging watchdog: FACT {1} had no SPEN/SYRD queue/placement progress for {2} WT. Repacking this failed staging cell and retrying another coast without resuming the blocked first-expansion PROC.",
							player, activeConyard, Info.CoastalStagingNavalProducerTimeoutTicks);
						bot.QueueOrder(new Order("DeployTransform", activeConyard, true));
					}
				}

				return;
			}

			coastalStagingNavalNoProgressSinceTick = -1;
			// Once SPEN/SYRD physically exists the Building queue is no longer a naval
			// prerequisite. Proactive naval bootstrap ends here: with no committed ore ferry
			// objective there is no LST demand, so repack immediately and resume normal expansion.
			ReleaseBaseBuilderLock();
			if (!deferredRoutineFerryObjective.HasValue)
			{
				pendingMcvLandingCraftReservation = null;
				ResumeFirstExpansionRefineryAfterInfrastructure("SPEN/SYRD now exists; proactive naval bootstrap is complete without creating an unneeded LST");
				lastTransformCell = activeConyard.Location;
				coastalStagingReturnToSea = true;
				coastalStagingRepackOutcome = CoastalStagingRepackOutcome.Success;
				stage = ExpansionStage.WaitingForMcv;
				repackTransformIssuedTick = world.WorldTick;
				repackTransformRetries = 0;
				FransBotLog.BotDebug(world,
					"{0}: COASTAL SUPPORT COMPLETE: proactive staging has a physical SPEN/SYRD and no committed ore ferry. No LST is requested; FACT {1} repacks and normal ore selection resumes.",
					player, activeConyard);
				bot.QueueOrder(new Order("DeployTransform", activeConyard, true));
				return;
			}

			RequestLandingCraft(bot);

			if (!coastalStagingPreservedCommittedSeaTask)
			{
				// PRE-COMMIT support owns no ore mission. Once the correct-region producer is physical,
				// its Ship queue can carry the LST reservation while the temporary FACT immediately
				// returns to PIONEER form. Do not hold the only MCV role waiting for the craft to finish.
				pendingMcvLandingCraftReservation = null;
				ResumeFirstExpansionRefineryAfterInfrastructure("same-region SPEN/SYRD is physical; pre-commit support may release PIONEER while the LST queue matures");
				lastTransformCell = activeConyard.Location;
				coastalStagingReturnToSea = true;
				coastalStagingRepackOutcome = CoastalStagingRepackOutcome.Success;
				stage = ExpansionStage.WaitingForMcv;
				repackTransformIssuedTick = world.WorldTick;
				repackTransformRetries = 0;
				ReleaseBaseBuilderLock();
				FransBotLog.BotDebug(world,
					"{0}: COASTAL SUPPORT COMPLETE: same-region SPEN/SYRD is physical before SeaOre commit. FACT {1} repacks immediately to restore PIONEER; any same-region LST queue continues independently and the ore will be re-proved after transform.",
					player, activeConyard);
				bot.QueueOrder(new Order("DeployTransform", activeConyard, true));
				return;
			}

			var craft = FindAvailableLandingCraft(activeConyard);
			if (craft == null)
				return;

			// Recovery of an ALREADY-COMMITTED SeaOre keeps the old stronger contract: pin a
			// physical free LST across FACT->MCV so that existing strategic ownership can resume.
			pendingMcvLandingCraftReservation = craft;
			ResumeFirstExpansionRefineryAfterInfrastructure("SPEN/SYRD and a physical demand-driven LST now exist; committed sea recovery can resume");
			lastTransformCell = activeConyard.Location;
			coastalStagingReturnToSea = true;
			coastalStagingRepackOutcome = CoastalStagingRepackOutcome.Success;
			stage = ExpansionStage.WaitingForMcv;
			repackTransformIssuedTick = world.WorldTick;
			repackTransformRetries = 0;
			ReleaseBaseBuilderLock();
			FransBotLog.BotDebug(world,
				"{0}: coastal recovery succeeded for an already-committed ore ferry: naval producer and demand-driven LST {1} exist. That exact LST is pinned across FACT->MCV transform; FACT {2} repacks now.",
				player, craft, activeConyard);
			bot.QueueOrder(new Order("DeployTransform", activeConyard, true));
		}



		bool TryGetPendingSecureFootholdForFact(Actor fact, out uint secureTargetId, out CPos securePoint)
		{
			secureTargetId = 0;
			securePoint = default;
			if (fact == null || !fact.IsInWorld || fact.IsDead || fact.Owner != player || generalService == null)
				return false;

			var sameEconomicAreaRadiusSquared = Info.ExistingBaseCoverageRadius * Info.ExistingBaseCoverageRadius;
			foreach (var foothold in generalService.PendingSecureFootholds
				.OrderBy(f => (fact.Location - f.Cell).LengthSquared)
				.ThenBy(f => f.ControlObservedWorldTick).ThenBy(f => f.TargetActorId))
			{
				if ((fact.Location - foothold.Cell).LengthSquared > sameEconomicAreaRadiusSquared)
					continue;
				secureTargetId = foothold.TargetActorId;
				securePoint = foothold.Cell;
				return true;
			}

			return false;
		}

		void CompleteExpansionOutpost(IBot bot, string refineryType)
		{
			mcvRetreatAfterRepackPending = false;
			ClearRoutineExpansionStructureOwnership();
			GrantBaseBuilderLock();
			var refineryRadiusSquared = Info.ExpansionStructureMaxRadius * Info.ExpansionStructureMaxRadius;
			var claimedRefinery = world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && a.Info.Name == refineryType &&
					(a.Location - activeConyard.Location).LengthSquared <= refineryRadiusSquared)
				.OrderBy(a => (a.Location - activeConyard.Location).LengthSquared)
				.ThenBy(a => a.ActorID)
				.FirstOrDefault();
			FransBotLog.BotDebug(world,
				"[PIONEER CLAIM] Tick={0} Player={1} Task={2} FACT={3} PROC={4} Objective={5} Action=ClaimConfirmed",
				world.WorldTick, player, expansionTask.Id, activeConyard.ActorID,
				claimedRefinery?.ActorID.ToString() ?? refineryType,
				targetResourceCenter.HasValue ? targetResourceCenter.Value.ToString() : "none");

			if (expansionTask.Mode == ExpansionTaskMode.SeaOre)
			{
				FransBotLog.BotDebug(world,
					"{0}: committed routine ferry objective {1} is COMPLETE: FACT + {2} are physical. Transport demand is finished; the same task remains owner only through FACT repack/handoff.",
					player, targetResourceCenter, refineryType);
			}

			// SECURE decoupling: General never sends this MCV here. If ordinary
			// autonomous expansion independently selected the same resource area that Ground
			// already secured, leave the completed FACT in place as a strategic anchor. The
			// MCV manager releases ownership immediately; DefenseCommander/BaseBuilder finish
			// the foothold and RequestExpansionMcv keeps the independent expansion chain alive.
			if (TryGetPendingSecureFootholdForFact(activeConyard, out var secureTargetId, out var securePoint))
			{
				// One protected SECURE handoff may consume the currently unlocked roaming slot and then
				// receive one role-replacement MCV. If physical FACT+MCV is already above the economic
				// ceiling, that exemption is already in use: repack this FACT normally instead of stacking
				// another protected out-of-budget anchor. Genuine Surplus growth later raises the ceiling
				// and naturally permits another handoff.
				if (PhysicalConstructionYardSlotCount() <= CurrentConstructionYardSlotCeiling())
				{
					var established = activeConyard;
					FransBotLog.BotDebug(world,
						"{0}: AUTONOMOUS EXPANSION HANDOFF: routine ore objective {1} independently reached militarily secured MineCluster {2} at {3}. FACT {4} + {5} remain physical as one protected SECURE anchor. If this consumes the roaming role, may replace that role without changing economic capacity/high-water. General did not retarget this MCV.",
						player, targetResourceCenter, secureTargetId, securePoint, established, refineryType);
					activeConyard = null;
					activeMcv = null;
					ReturnExpansionTaskToIdle("completed autonomous outpost handed its FACT to the already-secured foothold");
					RequestExpansionMcv(bot);
					return;
				}

				FransBotLog.BotDebug(world,
					"{0}: autonomous SECURE handoff at MineCluster {1} is deferred because physical FACT+MCV capacity {2} already exceeds current economic ceiling {3}; the existing roaming-role exemption is in use. FACT {4} repacks normally and keeps expansion mobile until genuine capacity growth absorbs that exemption.",
					player, secureTargetId, PhysicalConstructionYardSlotCount(), CurrentConstructionYardSlotCeiling(), activeConyard);
			}

			// PERSISTENT PIONEER ROLE: an ordinary completed ore FACT must not strand the
			// only roaming expansion role while RECON/SECURE prepares the next objective.
			// If current economic growth can legitimately absorb this FACT as permanent capacity,
			// hand it off and request the normal roaming slot. Otherwise repack immediately:
			// the physical MCV may wait mobile while fair intel develops.
			ReleaseActiveLandingCraftReservation();
			activeLandingCraft = null;
			pendingMcvLandingCraftReservation = null;

			var nextClaimObjective = FindNextExpansionObjectiveHint(activeConyard);
			if (!nextClaimObjective.HasValue)
			{
				var settledFact = activeConyard;
				var settledObjective = targetResourceCenter;
				pioneerClaimingComplete = true;
				activeConyard = null;
				activeMcv = null;
				ReturnExpansionTaskToIdle("no further acceptable PIONEER ore objective remains; completed FACT becomes a permanent settlement");
				FransBotLog.BotDebug(world,
					"[PIONEER SETTLE] Tick={0} Player={1} FACT={2} Objective={3} Reason=NoFurtherClaims Action=RemainPermanent",
					world.WorldTick, player, settledFact.ActorID,
					settledObjective.HasValue ? settledObjective.Value.ToString() : settledFact.Location.ToString());
				return;
			}

			var permanentTarget = CurrentPermanentFactFloor();
			var permanentEligibleFacts = LivePermanentEligibleConstructionYardCount();
			if (permanentEligibleFacts <= permanentTarget)
			{
				var established = activeConyard;
				var completedObjective = targetResourceCenter;
				activeConyard = null;
				activeMcv = null;
				ReturnExpansionTaskToIdle("completed ore FACT is absorbed into currently unlocked permanent capacity; restore one physical PIONEER MCV");
				RequestExpansionMcv(bot);
				FransBotLog.BotDebug(world,
					pioneerSuccessorPrequeueActive
						? "{0}: PERSISTENT PIONEER HANDOFF: completed ore {1} keeps FACT {2} because permanent capacity {3}/{4} can absorb it. Its real successor MCV was already prequeued while the PROC built, so handoff does not wait to begin replacement production."
						: "{0}: PERSISTENT PIONEER HANDOFF: completed ore {1} keeps FACT {2} because permanent capacity {3}/{4} can absorb it. ExpansionManager immediately pushes a replacement PIONEER MCV inside the normal slot budget.",
					player, completedObjective, established, permanentEligibleFacts, permanentTarget);
				return;
			}

			lastTransformCell = activeConyard.Location;
			stage = ExpansionStage.WaitingForMcv;
			repackTransformIssuedTick = world.WorldTick;
			repackTransformRetries = 0;
			FransBotLog.BotDebug(world,
				"[PIONEER CLAIM] Tick={0} Player={1} FACT={2} Action=RepackForNextClaim NextObjective={3}; completed ore {4} has physical {5}, but FACT capacity {6} exceeds permanent target {7}.",
				world.WorldTick, player, activeConyard.ActorID, nextClaimObjective.Value,
				targetResourceCenter, refineryType, permanentEligibleFacts, permanentTarget);
			bot.QueueOrder(new Order("DeployTransform", activeConyard, true));
		}

		void ManageCompletedOutpostHold(IBot bot)
		{
			if (world.WorldTick < nextLandExpansionPlanningTick)
				return;

			if (activePioneerObjective.HasValue)
			{
				EnsureAlternatePioneerObjective(activeConyard);
				var pioneer = activePioneerObjective.Value;
				if (!IsExpansionGroundSecured(pioneer) && (HasReconRequirementNear(pioneer) || HasSecureRequirementNear(pioneer)))
				{
					if (!TryPromoteReadyAlternatePioneerObjective(activeConyard) &&
						activePioneerObjectiveStartedTick >= 0 &&
						world.WorldTick - activePioneerObjectiveStartedTick >= Info.PioneerObjectiveMaximumHoldTicks)
						AbandonActivePioneerObjective($"completed-outpost PRIMARY hold exceeded {Info.PioneerObjectiveMaximumHoldTicks} WT", activeConyard);
				}
			}

			var nextObjective = FindNextExpansionObjectiveHint(activeConyard);
			if (!nextObjective.HasValue && activePioneerObjective.HasValue)
				AbandonActivePioneerObjective("completed-outpost planner can no longer execute the selected ore", activeConyard);

			if (!nextObjective.HasValue || !IsPioneerObjectiveIntelReady(nextObjective.Value))
			{
				// nearest-first hold: do not repack just because a farther scout-cleared
				// objective exists. The closest viable ore owns the next step. If it is unknown, keep
				// the FACT deployed for Construction Yard capacity and ask RECON for exactly that ore.
				if (nextObjective.HasValue)
				{
					SetActivePioneerObjective(nextObjective.Value, "completed outpost selected the nearest next ore");
					EnsureAlternatePioneerObjective(activeConyard);
					RequiresPioneerReconBeforeCommit(nextObjective.Value);
				}

				nextLandExpansionPlanningTick = world.WorldTick + Info.NoLandExpansionReplanInterval;
				if (world.WorldTick >= nextNoOreStatusLogTick)
				{
					nextNoOreStatusLogTick = world.WorldTick + Info.NoLandExpansionReplanInterval;
					FransBotLog.BotDebug(world,
						"{0}: completed expansion FACT {1} remains deployed at {2}; nearest next ore {3}. {4} Recheck WT {5}.",
						player, activeConyard, activeConyard.Location,
						nextObjective.HasValue ? nextObjective.Value.ToString() : "none",
						nextObjective.HasValue ? "Exact PIONEER RECON remains focused there before any farther objective may win." : "No viable uncovered ore exists.",
						nextLandExpansionPlanningTick);
				}
				return;
			}

			lastTransformCell = activeConyard.Location;
			stage = ExpansionStage.WaitingForMcv;
			repackTransformIssuedTick = world.WorldTick;
			repackTransformRetries = 0;
			FransBotLog.BotDebug(world,
				"{0}: completed expansion FACT {1} now has a NEW executable ore objective at {2}; only now does it repack into the roaming MCV. Exact land/sea route selection follows after transform.",
				player, activeConyard, nextObjective.Value);
			bot.QueueOrder(new Order("DeployTransform", activeConyard, true));
		}

		CPos? FindNextExpansionObjectiveHint(Actor heldFact)
		{
			if (heldFact == null || !heldFact.IsInWorld || heldFact.IsDead || heldFact.Owner != player)
				return null;

			var serviceTypes = Info.ExpansionRefineryTypes;
			var ownServiceStructures = world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && serviceTypes.Contains(a.Info.Name))
				.ToArray();

			var ownCoverageStructures = world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player &&
					Info.ExistingBaseCoverageTypes.Contains(a.Info.Name))
				.ToArray();

			var fallbackDistanceSquared = Info.FallbackMaximumExpansionHopDistance > 0
				? (long)Info.FallbackMaximumExpansionHopDistance * Info.FallbackMaximumExpansionHopDistance
				: long.MaxValue;

			combatIntelService.EnsureCurrentSnapshot();
			var currentObjectiveRadiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			return EnumerateExpansionObjectiveCenters()
				.Where(c => !activePioneerObjective.HasValue || c == activePioneerObjective.Value)
				.Where(c => world.Map.Contains(c))
				.Where(c => !targetResourceCenter.HasValue ||
					(c - targetResourceCenter.Value).LengthSquared > currentObjectiveRadiusSquared)
				.Where(c => !IsFieldTemporarilyFailed(c) && !IsExpansionCandidateBlockedBeforeSelection(c))
				.Where(c => !IsFieldServiced(c, ownServiceStructures, ownCoverageStructures))
				.Where(c => (c - heldFact.Location).LengthSquared <= fallbackDistanceSquared)
				.Where(c => !IsMcvCriticalRisk(heldFact, c, CurrentMcvRiskTolerance))
				.Select(c => new OreFieldCandidate(c, (c - heldFact.Location).LengthSquared))
				.OrderBy(c => c.DistanceSquared)
				.ThenBy(c => c.ResourceCenter.X)
				.ThenBy(c => c.ResourceCenter.Y)
				.Select(c => (CPos?)c.ResourceCenter)
				.FirstOrDefault();
		}

		string FindUsableExpansionType(FrozenSet<string> types, string queueCategory, int detectionRadius)
		{
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var queues = queuesByCategory[queueCategory].ToArray();

			foreach (var type in types.OrderBy(t => t))
			{
				if (!world.Map.Rules.Actors.ContainsKey(type))
					continue;

				if (HasStructureNear(type, activeConyard?.Location ?? CPos.Zero, detectionRadius))
					return type;

				if (queues.Any(q => q.Enabled && q.BuildableItems().Any(item => item.Name == type)))
					return type;
			}

			return null;
		}

		void LogBuildingQueueHandoffTransition(string eventName, ProductionQueue queue, string requestedType, string reason)
		{
			var items = queue?.AllQueued().ToArray() ?? [];
			var current = items.FirstOrDefault();
			var nativeItems = items.Length == 0 ? "NONE" : string.Join(">", items.Select(item => item.Item));
			var headSignature = current == null ? "NONE" : $"{current.Item}:{current.Started}:{current.Done}:{current.Paused}";
			var queueActorId = queue?.Actor.ActorID ?? 0;
			var ownerActorId = routineExpansionStructureQueueActor?.ActorID ?? 0;
			var ownerType = routineExpansionStructureType ?? "NONE";
			var signature = $"{eventName}|{queueActorId}|{requestedType}|{nativeItems}|{headSignature}|{ownerActorId}|{ownerType}|{routineExpansionStructurePlacementIssued}|{reason}";
			if (lastBuildingQueueHandoffDiagnostic == signature)
				return;

			lastBuildingQueueHandoffDiagnostic = signature;
			var head = current == null ? "NONE" :
				$"{current.Item}[Started={current.Started},Done={current.Done},Paused={current.Paused},RemainingCost={current.RemainingCost},RemainingTime={current.RemainingTime},RemainingTimeActual={current.RemainingTimeActual}]";
			FransBotLog.BotDebug(world,
				"[BUILDING QUEUE HANDOFF] Tick={0} Player={1} Module=MCVExpansion Stage={2} Event={3} Requested={4} QueueActor={5} NativeItems={6} Head={7} RoutineOwner={8}@{9} OwnershipStartTick={10} PlacementIssued={11} PlacementIssuedTick={12} Reason={13} Cash={14}",
				world.WorldTick, player, stage, eventName, requestedType, queueActorId, nativeItems, head, ownerType, ownerActorId,
				routineExpansionStructureOwnershipStartedTick, routineExpansionStructurePlacementIssued,
				routineExpansionStructurePlacementIssuedTick, reason, playerResources?.GetCashAndResources() ?? 0);
		}

		void BeginRoutineExpansionStructureOwnership(ProductionQueue queue, string buildingType)
		{
			routineExpansionStructureQueueActor = queue?.Actor;
			routineExpansionStructureType = buildingType;
			routineExpansionStructurePlacementIssued = false;
			routineExpansionStructureOwnershipStartedTick = world.WorldTick;
			routineExpansionStructurePlacementIssuedTick = -1;
		}

		void ClearRoutineExpansionStructureOwnership()
		{
			routineExpansionStructureQueueActor = null;
			routineExpansionStructureType = null;
			routineExpansionStructurePlacementIssued = false;
			routineExpansionStructureOwnershipStartedTick = -1;
			routineExpansionStructurePlacementIssuedTick = -1;
		}

		bool CancelOwnedRoutineExpansionStructureIfQueued(IBot bot, string reason)
		{
			if (bot == null || routineExpansionStructureQueueActor == null || string.IsNullOrEmpty(routineExpansionStructureType))
			{
				ClearRoutineExpansionStructureOwnership();
				return false;
			}

			var queueActor = routineExpansionStructureQueueActor;
			var buildingType = routineExpansionStructureType;
			ProductionQueue queue = null;
			if (queueActor.IsInWorld && !queueActor.IsDead && queueActor.Owner == player)
			{
				var queuesByCategory = AIUtils.FindQueuesByCategory(player);
				queue = queuesByCategory[Info.BuildingQueueCategory]
					.Where(q => q.Enabled && q.Actor == queueActor)
					.OrderBy(q => q.Actor.ActorID)
					.FirstOrDefault();
			}

			var ownedItem = queue?.AllQueued().FirstOrDefault(item => item.Item == buildingType);
			var cancelled = queue != null && ownedItem != null;
			if (cancelled)
			{
				LogBuildingQueueHandoffTransition("CancellationIssued", queue, buildingType, reason);
				bot.QueueOrder(Order.CancelProduction(queue.Actor, buildingType, 1));
			}

			FransBotLog.BotDebug(world,
				"{0}: routine expansion releases exact Building-queue ownership for {1} on actor {2} after {3}; owned item {4}. No unrelated queue item is touched.",
				player, buildingType, queueActor.ActorID, reason, cancelled ? "cancelled" : "already absent");
			ClearRoutineExpansionStructureOwnership();
			return cancelled;
		}

		void EnsureStructure(IBot bot, string buildingType, string queueCategory, int minRadius, int maxRadius)
		{
			var queue = FindQueueFor(buildingType, queueCategory);
			if (queue == null)
			{
				// CLAIM is deliberately PROC-only. Keep BaseBuilder paused while the
				// required refinery queue/prerequisites are temporarily unavailable.
				GrantBaseBuilderLock();
				return;
			}

			var current = queue.AllQueued().FirstOrDefault();
			var ownsQueue = routineExpansionStructureQueueActor == queue.Actor && routineExpansionStructureType == buildingType;
			if (openingBuildOrderService.HasExpansionLockDrainOwnership(queue.Actor))
			{
				if (ownsQueue)
				{
					LogBuildingQueueHandoffTransition("RoutineOwnershipClearedForBaseBuilderDrain", queue, buildingType,
						"PreLockBaseBuilderDrainOwnerIsAuthoritative");
					ClearRoutineExpansionStructureOwnership();
				}

				LogBuildingQueueHandoffTransition("WaitBaseBuilderDrainOwner", queue, buildingType,
					current == null ? "PendingPreLockBaseBuilderStartProduction" : $"NativePreLockBaseBuilderItem={current.Item}");
				GrantBaseBuilderLock();
				return;
			}

			// Production/placement orders are asynchronous. While this exact queue actor/type is ours,
			// an empty queue for a bounded interval means "order in flight" or "placement consumed" --
			// never start a duplicate PROC on the next scan. A successfully placed structure is detected
			// by ManageExpansionConyard before this method is called and clears ownership there.
			if (current == null && ownsQueue)
			{
				LogBuildingQueueHandoffTransition("QueueObservedEmpty", queue, buildingType,
					routineExpansionStructurePlacementIssued ? "OwnedPlacementOrderMayHaveConsumedNativeItem" : "OwnedStartProductionIntentInFlightOrNativeItemAbsent");
				GrantBaseBuilderLock();
				var since = routineExpansionStructurePlacementIssued
					? routineExpansionStructurePlacementIssuedTick
					: routineExpansionStructureOwnershipStartedTick;
				if (since >= 0 && world.WorldTick - since < RoutineExpansionStructureOwnershipTimeoutTicks)
					return;

				FransBotLog.BotDebug(world,
					"{0}: routine expansion exact queue ownership for {1} on actor {2} saw no owned queue item/physical structure for {3} WT; releasing stale item ownership while the PROC-only CLAIM lock remains active for a clean retry.",
					player, buildingType, queue.Actor.ActorID, RoutineExpansionStructureOwnershipTimeoutTicks);
				LogBuildingQueueHandoffTransition("RoutineOwnershipReleasedAbsent", queue, buildingType,
					"OwnedNativeItemOrPhysicalStructureAbsentAtOwnershipTimeout");
				ClearRoutineExpansionStructureOwnership();
				GrantBaseBuilderLock();
				return;
			}

			// Respect the currently active item in the selected player production queue. If our exact
			// item disappeared/replaced, drop stale ownership before yielding to unrelated work.
			if (current != null && current.Item != buildingType)
			{
				if (ownsQueue)
				{
					LogBuildingQueueHandoffTransition("RoutineOwnershipClearedOtherNativeHead", queue, buildingType,
						$"NativeHead={current.Item}");
					ClearRoutineExpansionStructureOwnership();
				}
				LogBuildingQueueHandoffTransition("WaitOtherNativeHead", queue, buildingType, $"NativeHead={current.Item}");
				GrantBaseBuilderLock();
				return;
			}

			if (current == null)
			{
				// The selected queue is free. Record the exact actor before issuing production:
				// only this item may later be cancelled if the outpost disappears before placement.
				LogBuildingQueueHandoffTransition("QueueObservedEmpty", queue, buildingType, "NoNativeProductionItems");
				GrantBaseBuilderLock();
				placementFailures = 0;
				BeginRoutineExpansionStructureOwnership(queue, buildingType);
				LogBuildingQueueHandoffTransition("RoutineOwnershipRecorded", queue, buildingType,
					"ExactQueueActorAndRequestedTypeRecordedBeforeStartProduction");
				FransBotLog.BotDebug(world, "{0}: shared Building queue is free; expansion outpost is producing required structure {1} with exact queue ownership on actor {2}.",
					player, buildingType, queue.Actor.ActorID);
				LogBuildingQueueHandoffTransition("StartProductionIntentBuffered", queue, buildingType,
					"PioneerRoutineExpansionStructure");
				bot.QueueOrder(Order.StartProduction(queue.Actor, buildingType, 1));
				return;
			}

			// Never claim a same-type item that another planner already started. Exact ownership
			// exists only when this module recorded the queue actor at StartProduction time.
			var ownsCurrent = ownsQueue;
			if (!ownsCurrent)
			{
				LogBuildingQueueHandoffTransition("WaitUnownedSameType", queue, buildingType,
					"NativeHeadMatchesRequestedTypeButRoutineOwnerDoesNot");
				GrantBaseBuilderLock();
				return;
			}

			LogBuildingQueueHandoffTransition("OwnedRequestNative", queue, buildingType,
				current.Done ? "OwnedNativeItemReadyToPlace" : "OwnedNativeItemBuilding");
			GrantBaseBuilderLock();

			if (Info.ExpansionRefineryTypes.Contains(buildingType))
				TryPrequeuePioneerSuccessorMcv(bot, "the exact outpost refinery is already owned/in production and this FACT fits the unlocked permanent target");

			if (!current.Done)
				return;

			var effectiveMaxRadius = maxRadius;

			var location = FindExpansionStructureLocation(buildingType, minRadius, effectiveMaxRadius);
			if (!location.HasValue)
			{
				// A successful amphibious landing can leave infantry/tanks packed around the FACT.
				// Before treating that as a failed expansion, push only friendly mobile blockers outward
				// and retry on the next scan. They remain close enough to defend the beachhead.
				if (TryClearFriendlyConstructionBlockers(bot, activeConyard.Location, effectiveMaxRadius))
				{
					placementFailures = 0;
					return;
				}

				if (++placementFailures >= Info.MaximumPlacementFailures)
					AbortTemporaryExpansion(bot, refineryPlacementFailure: true);
				return;
			}

			placementFailures = 0;
			FransBotLog.BotDebug(world, "{0}: placing expansion structure {1} at {2} from the shared Building queue; exact queue ownership remains latched until physical placement/abort confirmation.",
				player, buildingType, location.Value);
			routineExpansionStructurePlacementIssued = true;
			routineExpansionStructurePlacementIssuedTick = world.WorldTick;
			LogBuildingQueueHandoffTransition("PlacementIssued", queue, buildingType, $"Location={location.Value}");
			bot.QueueOrder(new Order("PlaceBuilding", playerActor, Target.FromCell(world, location.Value), false)
			{
				TargetString = buildingType,
				ExtraLocation = CPos.Zero,
				ExtraData = queue.Actor.ActorID,
				SuppressVisualFeedback = true
			});
		}

		ProductionQueue FindQueueFor(string buildingType, string queueCategory)
		{
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			return queuesByCategory[queueCategory]
				.Where(q => q.Enabled && q.BuildableItems().Any(item => item.Name == buildingType))
				.OrderBy(q => q.Actor.ActorID)
				.FirstOrDefault();
		}

		CPos? FindExpansionStructureLocation(string buildingType, int minRadius, int maxRadius)
		{
			if (activeConyard == null || !world.Map.Rules.Actors.ContainsKey(buildingType))
				return null;

			var actorInfo = world.Map.Rules.Actors[buildingType];
			var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return null;

			var tolerance = CurrentMcvRiskTolerance;
			var cells = world.Map.FindTilesInAnnulus(activeConyard.Location, minRadius, maxRadius)
				.Where(cell => world.CanPlaceBuilding(cell, actorInfo, buildingInfo, null))
				.Where(cell => buildingInfo.IsCloseEnoughToBase(world, player, actorInfo, null, cell))
				.Select(cell => (Cell: cell, Risk: riskModelService.EvaluateCell(activeConyard, cell,
					FransRiskRole.BuildingPlacement, tolerance)))
				.Where(candidate => !candidate.Risk.IsCritical)
				.OrderBy(candidate => candidate.Risk.Score)
				.ThenBy(candidate => (candidate.Cell - activeConyard.Location).LengthSquared);

			foreach (var candidate in cells)
				return candidate.Cell;

			return null;
		}

		bool TryClearFriendlyConstructionBlockers(IBot bot, CPos center, int constructionRadius)
		{
			var innerRadius = Math.Max(3, Math.Min(constructionRadius, 8));
			var innerSquared = innerRadius * innerRadius;
			combatIntelService.EnsureCurrentSnapshot();
			var blockers = combatIntelService.OwnedActors
				.Where(CanDisplaceOrdinaryFriendlyBlocker)
				.Where(a => a != activeMcv && (a.Location - center).LengthSquared <= innerSquared)
				.OrderBy(a => (a.Location - center).LengthSquared)
				.ThenBy(a => a.ActorID)
				.Take(10)
				.ToArray();

			if (blockers.Length == 0)
				return false;

			var moved = 0;
			foreach (var actor in blockers)
			{
				var mobile = actor.TraitOrDefault<Mobile>();
				if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
					continue;

				var candidates = world.Map.FindTilesInAnnulus(center, innerRadius + 2, innerRadius + 6)
					.Where(c => world.Map.Contains(c) && mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
					.Select(c => (Cell: c, Risk: riskModelService.EvaluateCell(actor, c, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced)))
					.Where(x => !x.Risk.IsCritical)
					.OrderBy(x => x.Risk.Score)
					.ThenBy(x => (x.Cell - actor.Location).LengthSquared)
					.ThenBy(x => x.Cell.X).ThenBy(x => x.Cell.Y);
				var destination = candidates.Select(x => (CPos?)x.Cell).FirstOrDefault();
				if (!destination.HasValue)
					continue;

				if (QueueOrdinaryBlockerRiskAwareMove(actor, destination.Value))
					moved++;
			}

			if (moved > 0)
				FransBotLog.BotDebug(world, "{0}: moved {1} friendly mobile blocker(s) out of the expansion construction ring around {2}; retaining them on the beachhead perimeter and retrying placement.", player, moved, center);

			return moved > 0;
		}

		bool HasStructureNear(string type, CPos center, int radius)
		{
			var radiusSquared = radius * radius;
			return world.ActorsHavingTrait<Building>()
				.Any(a => a.IsInWorld && !a.IsDead && a.Owner == player &&
					a.Info.Name == type && (a.Location - center).LengthSquared <= radiusSquared);
		}

		bool IsFieldServiced(CPos resourceCenter, IReadOnlyCollection<Actor> ownServiceStructures,
			IReadOnlyCollection<Actor> ownCoverageStructures)
		{
			var coverageRadiusSquared = Info.ExistingBaseCoverageRadius * Info.ExistingBaseCoverageRadius;
			foreach (var actor in ownCoverageStructures)
				if ((actor.Location - resourceCenter).LengthSquared <= coverageRadiusSquared)
					return true;

			var radiusSquared = Info.ServicedFieldRadius * Info.ServicedFieldRadius;
			return ownServiceStructures.Any(actor =>
				Info.ExpansionRefineryTypes.Contains(actor.Info.Name) &&
				(actor.Location - resourceCenter).LengthSquared <= radiusSquared);
		}

		void AbortTemporaryExpansion(IBot bot, bool retreatAfterRepack = false, bool refineryPlacementFailure = false)
		{
			CancelOwnedRoutineExpansionStructureIfQueued(bot, refineryPlacementFailure ? "refinery placement failure" : "temporary expansion abort");
			AbortFirstExpansionRefineryAttempt(bot,
				refineryPlacementFailure ? "refinery placement failure" : retreatAfterRepack ? "FACT RETREAT/repack" : "temporary expansion abort",
				targetResourceCenter);
			mcvRetreatAfterRepackPending = retreatAfterRepack;
			refineryPlacementRecoveryPending = refineryPlacementFailure;
			refineryPlacementFailedSite = refineryPlacementFailure ? targetResourceCenter : null;
			ResumeFirstExpansionRefineryAfterInfrastructure("the temporary naval-infrastructure suspension was released before the first ore expansion completed");
			coastalStagingForSeaExpansion = false;
			coastalStagingReturnToSea = false;
			coastalStagingRepackOutcome = CoastalStagingRepackOutcome.None;
			if (refineryPlacementFailure)
				MarkCurrentRefinerySiteFailed();
			else
				MarkCurrentFieldFailed();
			ReleaseBaseBuilderLock();

			if (activeConyard != null && activeConyard.IsInWorld && !activeConyard.IsDead)
			{
				lastTransformCell = activeConyard.Location;
				stage = ExpansionStage.WaitingForMcv;
				repackTransformIssuedTick = world.WorldTick;
				repackTransformRetries = 0;
				FransBotLog.BotDebug(world,
					"{0}: expansion FACT {1} is abandoning the outpost; repack-confirm watchdog armed for {2} WT.",
					player, activeConyard, Info.ExpansionRepackConfirmTimeoutTicks);
				bot.QueueOrder(new Order("DeployTransform", activeConyard, true));
				return;
			}

			mcvRetreatAfterRepackPending = false;
			refineryPlacementRecoveryPending = false;
			refineryPlacementFailedSite = null;
			activeConyard = null;
			activeMcv = null;
			ResumeFirstExpansionRefineryAfterInfrastructure("the temporary naval-infrastructure suspension was released before the first ore expansion completed");
			ReturnExpansionTaskToIdle("temporary expansion abort finished without a physical FACT/MCV to repack");
		}

		void FindMcvAfterUndeploy(IBot bot)
		{
			if (!lastTransformCell.HasValue)
				return;

			var maxDistanceSquared = 4 * 4;
			var mcv = mcvs.Actors
				.Where(a => a.IsInWorld && !a.IsDead)
				.Where(a => (a.Location - lastTransformCell.Value).LengthSquared <= maxDistanceSquared)
				.OrderBy(a => (a.Location - lastTransformCell.Value).LengthSquared)
				.ThenByDescending(a => a.ActorID)
				.FirstOrDefault();

			if (mcv != null)
			{
				var recoverFromRefineryPlacement = refineryPlacementRecoveryPending;
				var failedRefinerySite = refineryPlacementFailedSite;
				refineryPlacementRecoveryPending = false;
				refineryPlacementFailedSite = null;
				activeMcv = mcv;
				activeConyard = null;
				repackTransformIssuedTick = -1;
				repackTransformRetries = 0;
				ClearTarget();
				ReleaseBaseBuilderLock();

				if (coastalStagingReturnToSea)
				{
					var coastalOutcome = coastalStagingRepackOutcome;
					var deferredObjective = deferredRoutineFerryObjective;
					var preservedCommittedSeaTask = coastalStagingPreservedCommittedSeaTask;
					coastalStagingReturnToSea = false;
					coastalStagingRepackOutcome = CoastalStagingRepackOutcome.None;
					coastalStagingNavalNoProgressSinceTick = -1;

					if (coastalOutcome != CoastalStagingRepackOutcome.Success && !HasUsableLandingCraftProducerForCurrentDemand())
					{
						coastalStagingFailedAttempts++;
						if (coastalStagingFailedAttempts >= Info.CoastalStagingMaximumFailedAttempts)
						{
							var failedAttempts = coastalStagingFailedAttempts;
							if (deferredObjective.HasValue)
								MarkExpansionAreaCooldown(deferredObjective.Value, Info.ExpansionTargetFailureCooldownTicks,
									$"coastal support exhausted {failedAttempts} physically rejected FACT attempts");

							var releasedObjective = deferredObjective;
							ReturnExpansionTaskToIdle(
								$"bounded coastal support exhausted {failedAttempts}/{Info.CoastalStagingMaximumFailedAttempts} failed FACT attempts; PIONEER is released");
							nextCoastalStagingSearchTick = world.WorldTick + Info.ExpansionTargetFailureCooldownTicks;
							nextLandExpansionPlanningTick = world.WorldTick;
							if (releasedObjective.HasValue && activePioneerObjective.HasValue)
								AbandonActivePioneerObjective(
									"coastal support failed bounded proof; same strategic area cools down while PIONEER resumes ordinary duty", activeMcv);
							FransBotLog.BotDebug(world,
								"{0}: COASTAL SUPPORT ABORTS after {1} failed physical staging FACTs. PIONEER MCV {2} is released for ordinary expansion; candidate ore {3} shares strategic cooldown instead of keeping one MCV trapped in an infrastructure loop.",
								player, failedAttempts, activeMcv,
								releasedObjective.HasValue ? releasedObjective.Value.ToString() : "none");
							return;
						}

						// A failed support FACT is not naval success. Retry only within the bounded
						// support episode; after the configured cap the PIONEER role is released.
						coastalStagingForSeaExpansion = true;
						ChangeExpansionTaskMode(ExpansionTaskMode.CoastalStaging,
							$"failed coastal FACT repacked; bounded support retry {coastalStagingFailedAttempts + 1}/{Info.CoastalStagingMaximumFailedAttempts}");
						TryRetargetFailedCoastalStaging(bot, activeMcv, activeMcv.TraitOrDefault<Mobile>());
						return;
					}

					coastalStagingFailedAttempts = 0;
					coastalStagingForSeaExpansion = false;
					if (deferredObjective.HasValue)
					{
						if (preservedCommittedSeaTask)
						{
							targetResourceCenter = deferredObjective.Value;
							targetDeployCell = null;
							targetReservationStartedTick = deferredRoutineFerryReservationStartedTick >= 0
								? deferredRoutineFerryReservationStartedTick
								: world.WorldTick;
							coastalStagingRequiredNavalRegion = null;
							coastalStagingPreservedCommittedSeaTask = false;
							ChangeExpansionTaskMode(ExpansionTaskMode.SeaOre,
								"coastal naval recovery is ready; resume the already-committed ore objective");
							deferredRoutineFerryObjective = null;
							deferredRoutineFerryReservationStartedTick = -1;
							stage = ExpansionStage.WaitingForSeaTransport;
							seaTransportWaitStartedTick = world.WorldTick;
							nextSeaPlanningTick = world.WorldTick;
							FransBotLog.BotDebug(world,
								"{0}: coastal support FACT repacked into {1}; restoring already-committed routine ferry objective {2}.",
								player, activeMcv, deferredObjective.Value);
						}
						else
						{
							var candidateObjective = deferredObjective.Value;
							ReturnExpansionTaskToIdle(
								"coastal infrastructure support succeeded before SeaOre commit; PIONEER must re-prove actionable LST supply before the ore may own the MCV");
							SetActivePioneerObjective(candidateObjective,
								"coastal support completed; retry the same nearest sea candidate now that naval infrastructure/LST supply exists");
							nextLandExpansionPlanningTick = world.WorldTick;
							nextSeaPlanningTick = world.WorldTick;
							FransBotLog.BotDebug(world,
								"{0}: COASTAL SUPPORT COMPLETE: FACT repacked into PIONEER MCV {1}; candidate ore {2} was never committed. Planner rechecks exact physical/queued LST supply now before any SeaOre ExpansionTask may start.",
								player, activeMcv, candidateObjective);
						}
					}
					else
					{
						ReturnExpansionTaskToIdle("proactive coastal naval bootstrap completed without a deferred ore objective");
						nextLandExpansionPlanningTick = world.WorldTick;
						FransBotLog.BotDebug(world,
							"{0}: coastal support FACT repacked into PIONEER MCV {1}; naval access now exists and ordinary expansion selection resumes.",
							player, activeMcv);
					}

					return;
				}

				if (mcvRetreatAfterRepackPending)
				{
					mcvRetreatAfterRepackPending = false;
					ReturnExpansionTaskToIdle("threatened expansion FACT finished repacking; ore task is aborted before survival RETREAT");
					var mobile = activeMcv.TraitOrDefault<Mobile>();
					if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
					{
						stage = ExpansionStage.Retreat;
						ResetMcvRetreat();
						return;
					}

					BeginMcvRetreat(activeMcv, mobile, "threatened expansion FACT repacked for survival");
					return;
				}

				if (recoverFromRefineryPlacement)
				{
					ReturnExpansionTaskToIdle("failed refinery site repacked; planner owns the next ore choice");
					var mobile = activeMcv.TraitOrDefault<Mobile>();
					if (mobile != null && !mobile.IsTraitDisabled && !mobile.IsTraitPaused)
					{
						// One bounded local-only pass: at most MaximumOreFieldPathCandidates within
						// MaximumExpansionHopDistance and necessarily land-reachable from this MCV.
						// No map-wide fallback is allowed here because a failed island FACT must not
						// fall back into the expensive global land loop before sea planning gets ownership.
						var localChoice = FindNearestSafeOreField(activeMcv, mobile,
							excludedResourceCenter: failedRefinerySite, logChoice: false, allowMapWideFallback: false);
						if (localChoice.HasValue && RequiresPioneerReconBeforeCommit(localChoice.Value.ResourceCenter))
						{
							nextLandExpansionPlanningTick = world.WorldTick + Info.PioneerReconHoldReplanInterval;
							stage = ExpansionStage.Idle;
							return;
						}

						if (localChoice.HasValue)
						{
							if (!CommitLandOreTask(bot, activeMcv, mobile, localChoice.Value,
								"refinery-placement recovery selected the next local executable ore"))
								return;
							FransBotLog.BotDebug(world,
								"{0}: refinery-placement recovery after failed site {1} found scout-cleared local land ore {2}, deploy {3}; repacked MCV {4} stays on this reachable landmass.",
								player, failedRefinerySite, targetResourceCenter.Value, targetDeployCell.Value, activeMcv);
							return;
						}

						nextLandExpansionPlanningTick = world.WorldTick + Info.NoLandExpansionReplanInterval;
						nextSeaPlanningTick = world.WorldTick;
						var recoverySeaTarget = FindNearestRoutineSeaOreField(activeMcv, mobile, out var recoverySeaPending);
						if (recoverySeaPending)
						{
							nextLandExpansionPlanningTick = world.WorldTick + 25;
							stage = ExpansionStage.Idle;
							return;
						}

						if (recoverySeaTarget.HasValue && RequiresPioneerReconBeforeCommit(recoverySeaTarget.Value.ResourceCenter))
						{
							nextLandExpansionPlanningTick = world.WorldTick + Info.PioneerReconHoldReplanInterval;
							stage = ExpansionStage.Idle;
							return;
						}

						if (recoverySeaTarget.HasValue && TryBeginSeaExpansion(bot, activeMcv, mobile, recoverySeaTarget.Value))
						{
							FransBotLog.BotDebug(world,
								"{0}: refinery-placement recovery found no bounded local site after {1}; repacked MCV {2} returns directly to sea/LST planning instead of a global land retry.",
								player, failedRefinerySite, activeMcv);
							return;
						}

						nextSeaPlanningTick = world.WorldTick + Info.SeaPlanningInterval;
						FransBotLog.BotDebug(world,
							"{0}: refinery-placement recovery found no bounded local or current sea target after {1}; MCV {2} waits until WT {3} before another full land plan; any never-observed chosen objective will go through RECON first.",
							player, failedRefinerySite, activeMcv, nextLandExpansionPlanningTick);
					}
					stage = ExpansionStage.Idle;
					return;
				}

				ReturnExpansionTaskToIdle("completed expansion FACT repacked; the physical PIONEER MCV role is restored");
				nextLandExpansionPlanningTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: completed expansion FACT has repacked into physical PIONEER MCV {1}; it may remain mobile while RECON/SECURE prepares the next objective instead of being trapped as an idle outpost.",
					player, activeMcv);
				return;
			}

			if (activeConyard == null || !activeConyard.IsInWorld || activeConyard.IsDead)
			{
				FransBotLog.BotDebug(world,
					"{0}: expansion repack state lost its FACT without producing a nearby MCV; clearing the stale state instead of waiting forever.", player);
				mcvRetreatAfterRepackPending = false;
				refineryPlacementRecoveryPending = false;
				refineryPlacementFailedSite = null;
				activeConyard = null;
				activeMcv = null;
				ResumeFirstExpansionRefineryAfterInfrastructure("the temporary naval-infrastructure suspension was released before the first ore expansion completed");
				repackTransformIssuedTick = -1;
				repackTransformRetries = 0;
				ReturnExpansionTaskToIdle("repack state lost its FACT without producing a nearby MCV");
				return;
			}

			if (repackTransformIssuedTick < 0)
				repackTransformIssuedTick = world.WorldTick;
			if (world.WorldTick - repackTransformIssuedTick < Info.ExpansionRepackConfirmTimeoutTicks)
				return;

			if (repackTransformRetries < Info.ExpansionRepackMaximumRetries)
			{
				repackTransformRetries++;
				repackTransformIssuedTick = world.WorldTick;
				QueueStopOrder(bot, activeConyard);
				FransBotLog.BotDebug(world,
					"{0}: expansion FACT {1} is still deployed after repack request; repack-confirm watchdog retry {2}/{3}.",
					player, activeConyard, repackTransformRetries, Info.ExpansionRepackMaximumRetries);
				bot.QueueOrder(new Order("DeployTransform", activeConyard, true));
				return;
			}

			// Do not deadlock the entire expansion manager on a FACT that refuses to transform.
			// Leaving it deployed is useful construction capacity; a reserve/new MCV can continue.
			var stubborn = activeConyard;
			FransBotLog.BotDebug(world,
				"{0}: expansion repack-confirm watchdog exhausted {1} retries for FACT {2}; leaving it deployed as useful construction capacity and releasing the expansion chain for a reserve/new MCV.",
				player, Info.ExpansionRepackMaximumRetries, stubborn);
			mcvRetreatAfterRepackPending = false;
			refineryPlacementRecoveryPending = false;
			refineryPlacementFailedSite = null;
			activeConyard = null;
			activeMcv = null;
			ResumeFirstExpansionRefineryAfterInfrastructure("the temporary naval-infrastructure suspension was released before the first ore expansion completed");
			repackTransformIssuedTick = -1;
			repackTransformRetries = 0;
			ReturnExpansionTaskToIdle("FACT repack watchdog exhausted retries; deployed FACT is released as permanent capacity");
		}


		void GrantBaseBuilderLock()
		{
			if (baseBuilderLockToken != Actor.InvalidConditionToken)
				return;

			// Snapshot ordinary BaseBuilder work before the condition disables its normal BotTick.
			// Only that pre-lock work may drain; the later PIONEER-owned PROC remains exclusively
			// owned and placed by this expansion manager.
			openingBuildOrderService.CaptureExistingProductionForExpansionLock();
			baseBuilderLockToken = playerActor.GrantCondition(Info.BaseBuilderLockCondition);
		}

		void ReleaseBaseBuilderLock()
		{
			if (baseBuilderLockToken == Actor.InvalidConditionToken)
				return;

			baseBuilderLockToken = playerActor.RevokeCondition(baseBuilderLockToken);
		}

		bool TryFindRiskAwarePathToCell(Actor mcv, Mobile mobile, CPos destination, out List<CPos> path)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "MCV.GroundPath");
			path = null;
			if (mobile.ToCell == destination)
			{
				path = new List<CPos> { destination };
				return true;
			}

			if (mobile.PathFinder is not PathFinder pathFinder)
				return false;

			int CustomCost(CPos cell) =>
				cell == mobile.ToCell ? 0 : GetMcvPathCost(mcv, cell, CurrentMcvRiskTolerance);

			path = pathFinder.FindPathToTargetCell(mcv, [mobile.ToCell], destination,
				BlockedByActor.Immovable, CustomCost, laneBias: false);

			return path != null && path.Count > 0;
		}

		void QueueRiskAwareMove(Actor mcv, Mobile mobile, CPos destination)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "MCV.QueueRiskAwareMove");
			if (mcv == activeMcv && targetDeployCell.HasValue && destination == targetDeployCell.Value &&
				(!movingMcvLastProgressCell.HasValue || movingMcvLastProgressCell.Value != mobile.ToCell))
			{
				movingMcvLastProgressCell = mobile.ToCell;
				movingMcvLastProgressTick = world.WorldTick;
				movingMcvStallRetries = 0;
			}

			var destinationRisk = GetMcvRisk(mcv, destination, CurrentMcvRiskTolerance);
			FransBotLog.BotDebug(world, "{0}: unified RiskModel routes expansion MCV {1} toward {2}; destination risk {3} (preferred <= {4}, critical {5}).",
				player, mcv, destination, destinationRisk.Score, destinationRisk.PreferredThreshold, destinationRisk.CriticalThreshold);
			if (!TryFindRiskAwarePathToCell(mcv, mobile, destination, out var initialPath))
			{
				LogMcvWaitingState(mcv, "RiskAwareMoveOrderNoExecutablePath");
				return;
			}

			// PathFinder returns target-to-source. Preserve the accepted risk-aware route with a
			// bounded native waypoint packet instead of installing a synchronized activity.
			var orderedPath = initialPath
				.AsEnumerable()
				.Reverse()
				.Where(cell => cell != mobile.ToCell)
				.ToArray();
			if (orderedPath.Length == 0)
			{
				LogMcvMoveOrder(mcv, destination, 1, "RiskAwareExpansion");
				QueueMoveOrder(null, mcv, destination);
				return;
			}

			const int MaximumMoveWaypoints = 4;
			var waypointCount = Math.Min(MaximumMoveWaypoints, orderedPath.Length);
			LogMcvMoveOrder(mcv, destination, waypointCount, "RiskAwareExpansion");
			var queued = false;
			for (var i = 1; i <= waypointCount; i++)
			{
				var index = (int)((long)i * orderedPath.Length / waypointCount) - 1;
				QueueMoveOrder(null, mcv, orderedPath[index], queued);
				queued = true;
			}
		}

		void RememberDangerousExpansionArea(CPos center)
		{
			riskModelService.ReportRiskIncident(FransRiskRole.Mcv, center,
				Info.DangerousExpansionIncidentRisk, Info.DangerousExpansionIncidentRadius, Info.DangerousExpansionIncidentDuration);
		}

		bool IsExactPioneerObjectiveVisible(CPos center)
		{
			return world.Map.Contains(center) && (shroud == null || shroud.Disabled || shroud.IsVisible(center));
		}

		bool HasPioneerScoutClearance(CPos center)
		{
			if (IsExactPioneerObjectiveVisible(center))
				return true;

			var radiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			return scoutedExpansionAreas.Any(scouted => (scouted - center).LengthSquared <= radiusSquared);
		}

		void RefreshPioneerScoutClearance()
		{
			foreach (var center in EnumerateExpansionObjectiveCenters())
			{
				if (!IsExactPioneerObjectiveVisible(center))
					continue;

				var hadReconHold = IsTrackedPioneerObjective(center) && HasReconRequirementNear(center);
				if (scoutedExpansionAreas.Add(center) && hadReconHold)
				{
					var role = alternatePioneerObjective.HasValue && center == alternatePioneerObjective.Value ? "ALTERNATE" : "PRIMARY";
					FransBotLog.BotDebug(world,
						"{0}: DUAL PIONEER {1} RECON CLEAR at ore {2}: a scout legitimately revealed the exact objective. This fair scout memory remains usable after fog returns unless local failure/SECURE state later blocks it.",
						player, role, center);
				}

				if (hadReconHold)
					ClearReconRequirementNear(center);
			}
		}

		bool IsPioneerObjectiveIntelReady(CPos center)
		{
			if (IsExpansionGroundSecured(center))
				return true;
			if (HasReconRequirementNear(center) || HasSecureRequirementNear(center))
				return false;

			// Static ore/geography knowledge is sufficient for a normal CLAIM when current fair
			// tactical exposure is Safe. Uncertain exposure still needs legitimate exact-cell
			// scout clearance; Contested or hostile-core exposure never becomes ready here.
			var exposure = riskModelService.EvaluateExpansionExposure(center);
			return !IsPioneerHostileCore(exposure) && exposure.Level != FransExpansionExposureLevel.Contested &&
				(exposure.Level == FransExpansionExposureLevel.Safe || HasPioneerScoutClearance(center));
		}

		FransRiskTolerance CurrentMcvRiskTolerance => FransRiskTolerance.Cautious;

		FransRiskAssessment GetMcvRisk(Actor subject, CPos cell, FransRiskTolerance tolerance)
		{
			return riskModelService.EvaluateCell(subject, cell, FransRiskRole.Mcv, tolerance);
		}

		bool IsMcvCriticalRisk(Actor subject, CPos cell, FransRiskTolerance tolerance)
		{
			return GetMcvRisk(subject, cell, tolerance).IsCritical;
		}

		int GetMcvPathCost(Actor subject, CPos cell, FransRiskTolerance tolerance)
		{
			return riskModelService.GetPathCost(subject, cell, FransRiskRole.Mcv, tolerance);
		}

		bool IsExpansionGroundSecured(CPos center) => generalService != null && generalService.IsSecureAnchor(center);

		IEnumerable<CPos> TrackedPioneerObjectives()
		{
			if (activePioneerObjective.HasValue)
				yield return activePioneerObjective.Value;
			if (alternatePioneerObjective.HasValue &&
				(!activePioneerObjective.HasValue || alternatePioneerObjective.Value != activePioneerObjective.Value))
				yield return alternatePioneerObjective.Value;
		}

		bool IsTrackedPioneerObjective(CPos center)
		{
			var radiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			return TrackedPioneerObjectives().Any(objective => (objective - center).LengthSquared <= radiusSquared);
		}

		bool HasReconRequirementNear(CPos center)
		{
			var radiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			return reconRequiredExpansionAreas.Any(objective => (objective - center).LengthSquared <= radiusSquared);
		}

		bool HasSecureRequirementNear(CPos center)
		{
			var radiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			return secureRequiredExpansionAreas.Any(objective => (objective - center).LengthSquared <= radiusSquared);
		}

		void ClearReconRequirementNear(CPos center)
		{
			var radiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			foreach (var objective in reconRequiredExpansionAreas
				.Where(objective => (objective - center).LengthSquared <= radiusSquared).ToArray())
				reconRequiredExpansionAreas.Remove(objective);
		}

		void ClearSecureRequirementNear(CPos center)
		{
			var radiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			foreach (var objective in secureRequiredExpansionAreas
				.Where(objective => (objective - center).LengthSquared <= radiusSquared).ToArray())
				secureRequiredExpansionAreas.Remove(objective);
		}

		void MarkPioneerReconRequirement(CPos center, string role, FransExpansionExposureAssessment exposure, string reason)
		{
			var radiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			if (reconRequiredExpansionAreas.Any(existing => (existing - center).LengthSquared <= radiusSquared))
				return;

			ClearSecureRequirementNear(center);
			reconRequiredExpansionAreas.Add(center);
			FransBotLog.BotDebug(world,
				"{0}: DUAL PIONEER {1} ore {2} RECON REQUIRED: {3}; score {4} (structures {5}, mobile {6}, control {7}, intel age {8}). PRIMARY and ALTERNATE may scout in parallel, but only PRIMARY may publish expansion-unblock SECURE.",
				player, role, center, reason ?? "territory uncertainty", exposure.Score, exposure.StructureScore,
				exposure.MobileScore, exposure.ControlScore, exposure.IntelAgeTicks);
		}

		void ClearPioneerObjectiveProofEvidence(CPos center)
		{
			pioneerExecutionProofWork.Remove(center);
			pioneerCompletedSeaProofs.Remove(center);
		}

		void SetActivePioneerObjective(CPos center, string reason)
		{
			if (activePioneerObjective.HasValue && activePioneerObjective.Value == center)
				return;

			if (alternatePioneerObjective.HasValue && alternatePioneerObjective.Value == center)
			{
				PromoteAlternatePioneerObjective(reason ?? "planner selected the prepared alternate", retainOldPrimaryAsAlternate: true);
				return;
			}

			if (activePioneerObjective.HasValue)
			{
				var previous = activePioneerObjective.Value;
				ClearReconRequirementNear(previous);
				ClearSecureRequirementNear(previous);
				ClearPioneerObjectiveProofEvidence(previous);
				FransBotLog.BotDebug(world,
					"{0}: DUAL PIONEER PRIMARY handoff {1} -> {2}; stale strategic state for the replaced PRIMARY is removed. {3}",
					player, previous, center, reason ?? "nearest viable objective changed");
			}
			else
				FransBotLog.BotDebug(world,
					"{0}: DUAL PIONEER PRIMARY selects ore {1}. A second ALTERNATE ore may be scout-validated in parallel, while SECURE remains PRIMARY-only. {2}",
					player, center, reason ?? "nearest viable objective");

			pioneerCompletedSeaProofs.Remove(center);
			activePioneerObjective = center;
			activePioneerObjectiveStartedTick = world.WorldTick;
		}

		void SetAlternatePioneerObjective(CPos center, string reason)
		{
			if (activePioneerObjective.HasValue && activePioneerObjective.Value == center)
				return;
			if (alternatePioneerObjective.HasValue && alternatePioneerObjective.Value == center)
				return;

			if (alternatePioneerObjective.HasValue)
			{
				var previous = alternatePioneerObjective.Value;
				ClearReconRequirementNear(previous);
				ClearSecureRequirementNear(previous);
				pioneerCompletedSeaProofs.Remove(previous);
			}

			pioneerCompletedSeaProofs.Remove(center);
			alternatePioneerObjective = center;
			alternatePioneerObjectiveStartedTick = world.WorldTick;
			ClearSecureRequirementNear(center);

			FransBotLog.BotDebug(world,
				"{0}: DUAL PIONEER ALTERNATE selects ore {1}; it may receive exact RECON now, but cannot create +5000 expansion SECURE pressure until promoted to PRIMARY. {2}",
				player, center, reason ?? "nearest backup objective");

			if (!IsExpansionGroundSecured(center) && !HasPioneerScoutClearance(center))
			{
				var exposure = riskModelService.EvaluateExpansionExposure(center);
				if (exposure.Level == FransExpansionExposureLevel.Uncertain && !IsPioneerHostileCore(exposure))
					MarkPioneerReconRequirement(center, "ALTERNATE", exposure,
						"known tactical exposure is uncertain; static ore knowledge alone is not treated as tactical clearance");
			}
		}

		void ClearAlternatePioneerObjective(string reason, bool markFailed)
		{
			if (!alternatePioneerObjective.HasValue)
				return;

			var cleared = alternatePioneerObjective.Value;
			ClearReconRequirementNear(cleared);
			ClearSecureRequirementNear(cleared);
			ClearPioneerObjectiveProofEvidence(cleared);
			if (markFailed)
			{
				var until = world.WorldTick + Info.PioneerObjectiveAbandonCooldownTicks;
				if (!failedExpansionAreasUntil.TryGetValue(cleared, out var existing) || existing < until)
					failedExpansionAreasUntil[cleared] = until;
			}

			alternatePioneerObjective = null;
			alternatePioneerObjectiveStartedTick = -1;
			FransBotLog.BotDebug(world,
				"{0}: DUAL PIONEER drops ALTERNATE ore {1}: {2}.",
				player, cleared, reason ?? "alternate no longer useful");
		}

		void PromoteAlternatePioneerObjective(string reason, bool retainOldPrimaryAsAlternate)
		{
			if (!alternatePioneerObjective.HasValue)
				return;

			var promoted = alternatePioneerObjective.Value;
			var previousPrimary = activePioneerObjective;
			var previousPrimaryStartedTick = activePioneerObjectiveStartedTick;

			alternatePioneerObjective = null;
			alternatePioneerObjectiveStartedTick = -1;
			activePioneerObjective = promoted;
			activePioneerObjectiveStartedTick = world.WorldTick;

			if (retainOldPrimaryAsAlternate && previousPrimary.HasValue && previousPrimary.Value != promoted &&
				!IsFieldTemporarilyFailed(previousPrimary.Value))
			{
				// ALTERNATE may carry RECON memory, but never hidden SECURE pressure.
				ClearSecureRequirementNear(previousPrimary.Value);
				alternatePioneerObjective = previousPrimary.Value;
				alternatePioneerObjectiveStartedTick = previousPrimaryStartedTick >= 0 ? previousPrimaryStartedTick : world.WorldTick;
			}

			FransBotLog.BotDebug(world,
				"{0}: DUAL PIONEER promotes ALTERNATE ore {1} to PRIMARY{2}: {3}.",
				player, promoted,
				alternatePioneerObjective.HasValue ? $"; previous PRIMARY {alternatePioneerObjective.Value} remains as the backup" : "",
				reason ?? "alternate became the better executable choice");
		}

		bool IsPioneerPathEvidenceCurrent(Actor source, Mobile mobile, CPos currentMcvCell,
			CPos pathSourceCell, CPos destination, IReadOnlyList<CPos> path)
		{
			return IsPioneerPathEvidenceCurrent(source, mobile, currentMcvCell,
				pathSourceCell, destination, path, out _);
		}

		bool IsPioneerPathEvidenceCurrent(Actor source, Mobile mobile, CPos currentMcvCell,
			CPos pathSourceCell, CPos destination, IReadOnlyList<CPos> path, out string failure)
		{
			failure = null;
			if (!IsLiveOwnedMcv(source) || mobile == null || mobile.ToCell != currentMcvCell)
			{
				failure = "ActorOrSource";
				return false;
			}
			if (path == null || path.Count == 0 || path[0] != destination ||
				path[path.Count - 1] != pathSourceCell)
			{
				failure = "PathEndpoints";
				return false;
			}

			if (pathSourceCell == destination)
				return true;

			// Match the native proof's post-path contract: the returned path is destination-
			// first and its final entry is the source side. Recheck every traversed cell against
			// current immovable blockers and current Cautious critical risk.
			for (var p = 0; p < path.Count - 1; p++)
			{
				if (!world.Map.Contains(path[p]))
				{
					failure = $"PathOffMap@{path[p]}";
					return false;
				}
				if (!mobile.CanEnterCell(path[p], check: BlockedByActor.Immovable))
				{
					failure = $"PathBlockedImmovable@{path[p]}";
					return false;
				}
				if (IsMcvCriticalRisk(source, path[p], CurrentMcvRiskTolerance))
				{
					failure = $"PathCriticalRisk@{path[p]}";
					return false;
				}
			}

			return true;
		}

		bool IsPioneerLandRouteEvidenceCurrent(Actor source, Mobile mobile, CPos center,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			PioneerExecutionProofWork work)
		{
			var distanceSquared = (work.LandDeployCell - center).LengthSquared;
			return work.LandRoutePath.Length > 0 && world.Map.Contains(work.LandDeployCell) &&
				distanceSquared >= Info.ResourceDeployMinRadius * Info.ResourceDeployMinRadius &&
				distanceSquared <= Info.ResourceDeployMaxRadius * Info.ResourceDeployMaxRadius &&
				!IsMcvCriticalRisk(source, work.LandDeployCell, CurrentMcvRiskTolerance) &&
				mobile.CanEnterCell(work.LandDeployCell, check: BlockedByActor.Immovable) &&
				mobile.CanStayInCell(work.LandDeployCell) &&
				world.CanPlaceBuilding(work.LandDeployCell + transformsInfo.Offset, intoActor, buildingInfo, source) &&
				IsPioneerPathEvidenceCurrent(source, mobile, work.McvCell, work.McvCell,
					work.LandDeployCell, work.LandRoutePath) &&
				IsMcvRouteDetourAcceptable(work.McvCell, work.LandDeployCell, work.LandRoutePath.Length);
		}

		bool IsPioneerSeaPickupEvidenceCurrent(Actor source, Mobile mobile, PioneerExecutionProofWork work)
		{
			return IsPioneerSeaPickupEvidenceCurrent(source, mobile, work, out _);
		}

		bool IsPioneerSeaPickupEvidenceCurrent(Actor source, Mobile mobile, PioneerExecutionProofWork work,
			out string failure)
		{
			failure = null;
			if (work.PickupNavalRegion < 0 || work.PickupMcvPath.Length == 0)
				failure = "PickupEvidenceMissing";
			else if (!world.Map.Contains(work.PickupMcvCell) || !world.Map.Contains(work.PickupCraftCell))
				failure = "PickupOffMap";
			else if (strategicMapService == null ||
				!strategicMapService.IsAmphibiousHandoff(work.PickupMcvCell, work.PickupCraftCell))
				failure = "PickupShoreline";
			else if (!IsCellInNavalRegion(work.PickupCraftCell, work.PickupNavalRegion))
				failure = "PickupNavalRegion";
			else if (!mobile.CanEnterCell(work.PickupMcvCell, check: BlockedByActor.Immovable))
				failure = "PickupBlockedImmovable";
			else if (!mobile.CanStayInCell(work.PickupMcvCell))
				failure = "PickupCannotStay";
			else if (!IsPioneerPathEvidenceCurrent(source, mobile, work.McvCell, work.McvCell,
				work.PickupMcvCell, work.PickupMcvPath, out failure))
				failure = "Pickup" + failure;

			return failure == null;
		}

		bool IsPioneerSeaLandingEvidenceCurrent(Actor source, Mobile mobile, CPos center,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			PioneerExecutionProofWork work)
		{
			return IsPioneerSeaLandingEvidenceCurrent(source, mobile, center,
				transformsInfo, intoActor, buildingInfo, work, out _);
		}

		bool IsPioneerSeaLandingEvidenceCurrent(Actor source, Mobile mobile, CPos center,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			PioneerExecutionProofWork work, out string failure)
		{
			failure = null;
			var distanceSquared = (work.SeaDeployCell - center).LengthSquared;
			if (work.SeaLandingPath.Length == 0)
				failure = "LandingEvidenceMissing";
			else if (!world.Map.Contains(work.SeaLandingCraftCell) ||
				!world.Map.Contains(work.SeaLandingExitCell) || !world.Map.Contains(work.SeaDeployCell))
				failure = "LandingOffMap";
			else if (strategicMapService == null ||
				!strategicMapService.IsAmphibiousHandoff(work.SeaLandingExitCell, work.SeaLandingCraftCell))
				failure = "LandingShoreline";
			else if (!IsCellInNavalRegion(work.SeaLandingCraftCell, work.PickupNavalRegion))
				failure = "LandingNavalRegion";
			else if (!mobile.CanEnterCell(work.SeaLandingExitCell, check: BlockedByActor.Immovable))
				failure = "LandingExitBlockedImmovable";
			else if (!mobile.CanStayInCell(work.SeaLandingExitCell))
				failure = "LandingExitCannotStay";
			else if (distanceSquared < Info.ResourceDeployMinRadius * Info.ResourceDeployMinRadius ||
				distanceSquared > Info.ResourceDeployMaxRadius * Info.ResourceDeployMaxRadius)
				failure = "LandingDeployRange";
			else if (IsMcvCriticalRisk(source, work.SeaDeployCell, CurrentMcvRiskTolerance))
				failure = "LandingDeployCriticalRisk";
			else if (!mobile.CanEnterCell(work.SeaDeployCell, check: BlockedByActor.Immovable))
				failure = "LandingDeployBlockedImmovable";
			else if (!mobile.CanStayInCell(work.SeaDeployCell))
				failure = "LandingDeployCannotStay";
			else if (!world.CanPlaceBuilding(work.SeaDeployCell + transformsInfo.Offset, intoActor, buildingInfo, source))
				failure = "LandingFactPlacement";
			else if (!IsPioneerPathEvidenceCurrent(source, mobile, work.McvCell, work.SeaLandingExitCell,
				work.SeaDeployCell, work.SeaLandingPath, out failure))
				failure = "Landing" + failure;

			return failure == null;
		}

		bool IsPioneerSeaRefineryEvidenceCurrent(Actor source, CPos center,
			PioneerExecutionProofWork work, out string failure)
		{
			failure = null;
			if (IsFutureRefineryProofCooling(center))
				failure = "RefineryProofCooling";
			else if (string.IsNullOrEmpty(work.SeaRefineryType) || !world.Map.Contains(work.SeaRefineryCell) ||
				!Info.ExpansionRefineryTypes.Contains(work.SeaRefineryType) ||
				!world.Map.Rules.Actors.TryGetValue(work.SeaRefineryType, out var refineryInfo))
				failure = "RefineryEvidenceMissing";
			else if (refineryInfo.TraitInfoOrDefault<BuildingInfo>() is not BuildingInfo refineryBuildingInfo)
				failure = "RefineryBuildingInfo";
			else if (!EnumerateFutureExpansionRefineryFootprints(source, work.SeaDeployCell)
				.Any(candidate => candidate.Type == work.SeaRefineryType && candidate.Cell == work.SeaRefineryCell))
				failure = "RefineryFootprintIdentity";
			else if (!world.CanPlaceBuilding(work.SeaRefineryCell, refineryInfo, refineryBuildingInfo, null))
				failure = "RefineryPlacement";
			else if (riskModelService.EvaluateStrategicCell(work.SeaRefineryCell,
				FransRiskRole.BuildingPlacement, CurrentMcvRiskTolerance).IsCritical)
				failure = "RefineryCriticalRisk";

			return failure == null;
		}

		bool IsTerrainStableLandRouteFailure(CPos source, CPos objective)
		{
			return strategicMapService != null &&
				strategicMapService.TryGetGroundLandmassId(source, out var sourceLandmass) &&
				strategicMapService.TryGetGroundLandmassId(objective, out var targetLandmass) &&
				sourceLandmass != targetLandmass;
		}

		CPos[] GetPioneerLandRouteLegalDeployCells(Actor source, Mobile mobile, CPos center,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo)
		{
			return EnumerateExpansionDeployCells(center)
				.Where(world.Map.Contains)
				.Where(cell => IsExpansionDeployCellLegal(source, mobile, cell,
					transformsInfo, intoActor, buildingInfo))
				.OrderBy(cell => cell.Bits)
				.ToArray();
		}

		CPos[] GetPioneerLandRouteSafeDeployCells(Actor source, IReadOnlyList<CPos> legalDeployCells)
		{
			return legalDeployCells
				.Where(cell => !IsMcvCriticalRisk(source, cell, CurrentMcvRiskTolerance))
				.OrderBy(cell => cell.Bits)
				.ToArray();
		}

		bool CanCellAffectAcceptableLandRoute(CPos source, CPos cell, IReadOnlyList<CPos> destinations)
		{
			var sourceSteps = Math.Max(Math.Abs(cell.X - source.X), Math.Abs(cell.Y - source.Y));
			foreach (var destination in destinations)
			{
				var destinationSteps = Math.Max(Math.Abs(destination.X - cell.X), Math.Abs(destination.Y - cell.Y));
				if ((long)sourceSteps + destinationSteps <= MaximumMcvRouteSteps(source, destination))
					return true;
			}

			return false;
		}

		CPos[] GetPioneerLandRouteRelevantBlockedCells(Actor source, Mobile mobile,
			CPos routeSource, IReadOnlyList<CPos> safeDeployCells)
		{
			if (safeDeployCells == null || safeDeployCells.Count == 0)
				return [];

			// BlockedByActor.Immovable pathfinding can change without RiskRevision. Snapshot
			// only blocked cells that can lie on a route within the existing detour limit to
			// one of the exact risk-allowed targets. A cell outside this bounded union cannot
			// become part of an acceptable route if its blocker changes.
			return world.ActorMap.AllActors()
				.Where(actor => actor != null && !actor.Disposed && actor.IsInWorld && !actor.IsDead &&
					actor != source && actor.OccupiesSpace != null)
				.SelectMany(actor => actor.OccupiesSpace.OccupiedCells().Select(occupied => occupied.Cell))
				.Where(world.Map.Contains)
				.Distinct()
				.Where(mobile.CanExistInCell)
				.Where(cell => !mobile.CanEnterCell(cell, source, BlockedByActor.Immovable))
				.Where(cell => CanCellAffectAcceptableLandRoute(routeSource, cell, safeDeployCells))
				.OrderBy(cell => cell.Bits)
				.ToArray();
		}

		void GetPioneerLandRouteRiskCostEvidence(Actor source, Mobile mobile, CPos routeSource,
			IReadOnlyList<CPos> safeDeployCells, out CPos[] riskCostCells, out int[] riskCosts)
		{
			// Native-null and detour outcomes depend on risk-shaped A* costs, including a
			// shortcut that the previous search did not expand. Cover every terrain-passable
			// cell that can geometrically belong to a route accepted by the existing detour
			// bound. Risk changes outside this bounded union cannot make land feasible.
			var cells = world.Map.AllCells
				.Where(cell => cell != routeSource && mobile.CanExistInCell(cell))
				.Where(cell => mobile.CanEnterCell(cell, source, BlockedByActor.Immovable))
				.Where(cell => CanCellAffectAcceptableLandRoute(routeSource, cell, safeDeployCells))
				.OrderBy(cell => cell.Bits)
				.ToArray();
			riskCostCells = cells;
			riskCosts = riskModelService.ExecuteWithPreparedPathCost(source,
				FransRiskRole.Mcv, CurrentMcvRiskTolerance, preparedPathCost =>
					cells.Select(preparedPathCost).ToArray());
		}

		bool IsPioneerLandRouteRiskCostEvidenceCurrent(Actor source, PioneerExecutionProofWork work)
		{
			if (work.LandRouteRiskCostCells.Length != work.LandRouteRiskCosts.Length)
				return false;

			return riskModelService.ExecuteWithPreparedPathCost(source,
				FransRiskRole.Mcv, CurrentMcvRiskTolerance, preparedPathCost =>
				{
					for (var i = 0; i < work.LandRouteRiskCostCells.Length; i++)
						if (preparedPathCost(work.LandRouteRiskCostCells[i]) != work.LandRouteRiskCosts[i])
							return false;

					return true;
				});
		}

		bool IsPioneerReturnedPathDynamicallyCurrent(Mobile mobile, IReadOnlyList<CPos> path)
		{
			if (path == null || path.Count == 0)
				return false;

			for (var p = 0; p < path.Count - 1; p++)
				if (!world.Map.Contains(path[p]) ||
					!mobile.CanEnterCell(path[p], check: BlockedByActor.Immovable))
					return false;

			return true;
		}

		void ClearPioneerLandRouteEvidence(PioneerExecutionProofWork work)
		{
			work.LandDeployCell = default;
			work.LandRoutePath = [];
			work.LandRouteRejected = false;
			work.LandRouteFailureTerrainStable = false;
			work.LandRouteFailureKind = PioneerLandRouteFailureKind.None;
			work.LandRouteFailureRiskSensitive = false;
			work.LandRouteRejectedRiskRevision = -1;
			work.LandRouteLegalDeployCells = [];
			work.LandRouteSafeDeployCells = [];
			work.LandRouteReturnedPath = [];
			work.LandRouteRiskCostCells = [];
			work.LandRouteRiskCosts = [];
			work.LandRouteBlockedCells = [];
			work.LandRouteRiskEvidenceChanged = false;
			work.LandRouteDynamicEvidenceChanged = false;
			work.LandRefineryRejected = false;
			work.LandRefineryFailureRiskSensitive = false;
			work.LandRefineryRejectedRiskRevision = -1;
			work.LandRefineryLegalTypes = [];
			work.LandRefineryLegalCells = [];
			work.LandRefineryRiskEvidenceChanged = false;
			work.LandRefineryDynamicEvidenceChanged = false;
		}

		void ClearPioneerSeaPickupEvidence(PioneerExecutionProofWork work)
		{
			work.PickupNavalRegion = -1;
			work.PickupMcvCell = default;
			work.PickupCraftCell = default;
			work.PickupMcvPath = [];
			work.SeaLandingSearch = null;
			work.SeaLandingCraftCell = default;
			work.SeaLandingExitCell = default;
			work.SeaDeployCell = default;
			work.SeaLandingPath = [];
			work.SeaRefineryType = null;
			work.SeaRefineryCell = default;
		}

		void ClearPioneerSeaLandingEvidence(PioneerExecutionProofWork work)
		{
			work.SeaLandingSearch = null;
			work.SeaLandingCraftCell = default;
			work.SeaLandingExitCell = default;
			work.SeaDeployCell = default;
			work.SeaLandingPath = [];
			work.SeaRefineryType = null;
			work.SeaRefineryCell = default;
		}

		void EvaluatePioneerLandRouteNegativeEvidence(Actor source, Mobile mobile, CPos center,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			PioneerExecutionProofWork work, out bool riskEvidenceChanged, out bool dynamicEvidenceChanged)
		{
			riskEvidenceChanged = false;
			dynamicEvidenceChanged = false;
			var legalDeployCells = GetPioneerLandRouteLegalDeployCells(source, mobile, center,
				transformsInfo, intoActor, buildingInfo);

			switch (work.LandRouteFailureKind)
			{
				case PioneerLandRouteFailureKind.NoLegalDeployCell:
					dynamicEvidenceChanged = legalDeployCells.Length != 0;
					return;

				case PioneerLandRouteFailureKind.CautiousRiskRejectedAllLegalCandidates:
					dynamicEvidenceChanged = !work.LandRouteLegalDeployCells.SequenceEqual(legalDeployCells);
					if (!dynamicEvidenceChanged)
						riskEvidenceChanged = GetPioneerLandRouteSafeDeployCells(source, legalDeployCells).Length != 0;
					return;

				case PioneerLandRouteFailureKind.MissingPathFinder:
					dynamicEvidenceChanged = mobile.PathFinder is PathFinder;
					return;

				case PioneerLandRouteFailureKind.NativePathNotFound:
				case PioneerLandRouteFailureKind.ReturnedPathCriticalRisk:
				case PioneerLandRouteFailureKind.RouteDetour:
					dynamicEvidenceChanged = !work.LandRouteLegalDeployCells.SequenceEqual(legalDeployCells);
					var safeDeployCells = GetPioneerLandRouteSafeDeployCells(source, legalDeployCells);
					riskEvidenceChanged = !work.LandRouteSafeDeployCells.SequenceEqual(safeDeployCells);
					if (dynamicEvidenceChanged || riskEvidenceChanged)
						return;

					if (work.LandRouteFailureKind == PioneerLandRouteFailureKind.ReturnedPathCriticalRisk)
					{
						dynamicEvidenceChanged = !IsPioneerReturnedPathDynamicallyCurrent(mobile,
							work.LandRouteReturnedPath);
						riskEvidenceChanged = !work.LandRouteReturnedPath
							.Take(Math.Max(0, work.LandRouteReturnedPath.Length - 1))
							.Any(cell => IsMcvCriticalRisk(source, cell, CurrentMcvRiskTolerance));
						if (dynamicEvidenceChanged || riskEvidenceChanged)
							return;
					}

					var blockedCells = GetPioneerLandRouteRelevantBlockedCells(source, mobile,
						work.McvCell, safeDeployCells);
					dynamicEvidenceChanged = !work.LandRouteBlockedCells.SequenceEqual(blockedCells);
					riskEvidenceChanged = !IsPioneerLandRouteRiskCostEvidenceCurrent(source, work);
					return;
			}

			riskEvidenceChanged = true;
			dynamicEvidenceChanged = true;
		}

		bool EnsurePioneerLandRejectionCurrent(Actor source, Mobile mobile, CPos center,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			PioneerExecutionProofWork work, int currentRiskRevision, bool requireRiskCurrent,
			List<string> validity)
		{
			if (work.LandRouteFailureTerrainStable)
			{
				validity.Add("RetainedStableTopologyLandRouteFailure");
				if (work.LandRouteRejectedRiskRevision != currentRiskRevision)
					validity.Add("GlobalRiskRevisionChangedButRelevantLandEvidenceStillValid");
				if (requireRiskCurrent)
					validity.Add("TerminalLandNegativeRetained");
				return true;
			}

			if (work.LandRefineryRejected)
			{
				if (!IsPioneerLandRouteEvidenceCurrent(source, mobile, center,
					transformsInfo, intoActor, buildingInfo, work))
				{
					ClearPioneerLandRouteEvidence(work);
					ClearPioneerSeaPickupEvidence(work);
					work.Phase = PioneerExecutionProofPhase.LandRoute;
					validity.Add("RelevantLandDynamicEvidenceChanged");
					validity.Add("TerminalLandRouteRetryRequired");
					return false;
				}

				validity.Add("RevalidatedLandRoute");
				GetFutureExpansionRefineryLegalFootprints(source, work.LandDeployCell,
					out var legalTypes, out var legalCells);
				work.LandRefineryDynamicEvidenceChanged =
					!work.LandRefineryLegalTypes.SequenceEqual(legalTypes) ||
					!work.LandRefineryLegalCells.SequenceEqual(legalCells);
				work.LandRefineryRiskEvidenceChanged = work.LandRefineryFailureRiskSensitive &&
					!work.LandRefineryDynamicEvidenceChanged &&
					legalCells.Any(cell => !riskModelService.EvaluateStrategicCell(cell,
						FransRiskRole.BuildingPlacement, CurrentMcvRiskTolerance).IsCritical);

				if (work.LandRefineryDynamicEvidenceChanged)
					validity.Add("RelevantLandDynamicEvidenceChanged");
				if (work.LandRefineryRiskEvidenceChanged)
					validity.Add("RelevantLandRiskEvidenceChanged");

				if (work.LandRefineryDynamicEvidenceChanged || work.LandRefineryRiskEvidenceChanged)
				{
					if (!requireRiskCurrent)
						return true;

					ClearPioneerSeaPickupEvidence(work);
					work.Phase = PioneerExecutionProofPhase.LandRefinery;
					validity.Add("TerminalLandRefineryRetryRequired");
					return false;
				}

				if (work.LandRefineryRejectedRiskRevision != currentRiskRevision)
					validity.Add("GlobalRiskRevisionChangedButRelevantLandEvidenceStillValid");
				validity.Add(work.LandRefineryFailureRiskSensitive
					? "RetainedRiskSensitiveLandRefineryFailureByCurrentEvidence"
					: "RevalidatedPlacementOnlyLandRefineryFailure");
				if (requireRiskCurrent)
					validity.Add("TerminalLandNegativeRetained");
				return true;
			}

			if (work.LandRouteRejected)
			{
				EvaluatePioneerLandRouteNegativeEvidence(source, mobile, center,
					transformsInfo, intoActor, buildingInfo, work,
					out var riskEvidenceChanged, out var dynamicEvidenceChanged);
				work.LandRouteRiskEvidenceChanged = riskEvidenceChanged;
				work.LandRouteDynamicEvidenceChanged = dynamicEvidenceChanged;
				if (riskEvidenceChanged)
					validity.Add("RelevantLandRiskEvidenceChanged");
				if (dynamicEvidenceChanged)
					validity.Add("RelevantLandDynamicEvidenceChanged");

				if (riskEvidenceChanged || dynamicEvidenceChanged)
				{
					if (!requireRiskCurrent)
						return true;

					ClearPioneerLandRouteEvidence(work);
					ClearPioneerSeaPickupEvidence(work);
					work.Phase = PioneerExecutionProofPhase.LandRoute;
					validity.Add("TerminalLandRouteRetryRequired");
					return false;
				}

				if (work.LandRouteRejectedRiskRevision != currentRiskRevision)
					validity.Add("GlobalRiskRevisionChangedButRelevantLandEvidenceStillValid");
				validity.Add(work.LandRouteFailureRiskSensitive
					? "RetainedRiskSensitiveLandRouteNegativeByCurrentEvidence"
					: "RetainedRevisionIndependentLandRouteNegative");
				if (requireRiskCurrent)
					validity.Add("TerminalLandNegativeRetained");
				return true;
			}

			ClearPioneerLandRouteEvidence(work);
			ClearPioneerSeaPickupEvidence(work);
			work.Phase = PioneerExecutionProofPhase.LandRoute;
			validity.Add("InvalidatedUnclassifiedLandFailure");
			validity.Add("TerminalLandRouteRetryRequired");
			return false;
		}

		static PioneerExecutionProofPhase? GetPioneerLandRejectionRetryPhaseForTerminalResult(
			PioneerExecutionProofWork work)
		{
			if (work.LandRouteFailureTerrainStable)
				return null;
			if (work.LandRouteRejected)
				return work.LandRouteDynamicEvidenceChanged || work.LandRouteRiskEvidenceChanged
					? PioneerExecutionProofPhase.LandRoute
					: null;
			if (work.LandRefineryRejected)
				return work.LandRefineryDynamicEvidenceChanged || work.LandRefineryRiskEvidenceChanged
					? PioneerExecutionProofPhase.LandRefinery
					: null;
			return PioneerExecutionProofPhase.LandRoute;
		}

		void GetFutureExpansionRefineryLegalFootprints(Actor mcv, CPos deployCell,
			out string[] refineryTypes, out CPos[] refineryCells)
		{
			var types = new List<string>();
			var cells = new List<CPos>();
			foreach (var candidate in EnumerateFutureExpansionRefineryFootprints(mcv, deployCell))
			{
				if (!world.CanPlaceBuilding(candidate.Cell, candidate.ActorInfo, candidate.BuildingInfo, null))
					continue;

				types.Add(candidate.Type);
				cells.Add(candidate.Cell);
			}

			refineryTypes = types.ToArray();
			refineryCells = cells.ToArray();
		}

		void PreparePioneerProofPhaseForCurrentRisk(Actor source, Mobile mobile, CPos center,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			PioneerExecutionProofWork work, int riskRevision, PioneerPhysicalProofPerf perf)
		{
			var riskRevisionChanged = work.RiskRevision != riskRevision;
			perf.WorkRiskRevisionChanged = riskRevisionChanged;
			var validity = new List<string>
			{
				riskRevisionChanged ? "RiskRevisionChanged" : "CurrentRevision"
			};
			switch (work.Phase)
			{
				case PioneerExecutionProofPhase.LandRoute:
					validity.Add(riskRevisionChanged ? "RestartCurrentLandRoute" : "CurrentLandRoutePhase");
					break;

				case PioneerExecutionProofPhase.LandRefinery:
					if (IsPioneerLandRouteEvidenceCurrent(source, mobile, center,
						transformsInfo, intoActor, buildingInfo, work))
						validity.Add("RevalidatedLandRoute");
					else
					{
						ClearPioneerLandRouteEvidence(work);
						ClearPioneerSeaPickupEvidence(work);
						work.Phase = PioneerExecutionProofPhase.LandRoute;
						validity.Add("InvalidatedLandRoute");
					}
					break;

				case PioneerExecutionProofPhase.SeaPrecheck:
					if (EnsurePioneerLandRejectionCurrent(source, mobile, center,
						transformsInfo, intoActor, buildingInfo, work, riskRevision,
						requireRiskCurrent: false, validity) &&
						(work.LandRouteFailureTerrainStable || work.LandRouteRejected))
						validity.Add("PermittedSeaPrecheckAfterValidLandRouteNegative");
					break;

				case PioneerExecutionProofPhase.SeaLanding:
					if (!EnsurePioneerLandRejectionCurrent(source, mobile, center,
						transformsInfo, intoActor, buildingInfo, work, riskRevision,
						requireRiskCurrent: false, validity))
						break;
					if (IsPioneerSeaPickupEvidenceCurrent(source, mobile, work))
						validity.Add("RevalidatedSeaPickup");
					else
					{
						ClearPioneerSeaPickupEvidence(work);
						work.Phase = PioneerExecutionProofPhase.SeaPrecheck;
						validity.Add("InvalidatedSeaPickup");
					}
					break;

				case PioneerExecutionProofPhase.SeaRefinery:
					if (!EnsurePioneerLandRejectionCurrent(source, mobile, center,
						transformsInfo, intoActor, buildingInfo, work, riskRevision,
						requireRiskCurrent: true, validity))
						break;
					if (!IsPioneerSeaPickupEvidenceCurrent(source, mobile, work))
					{
						ClearPioneerSeaPickupEvidence(work);
						work.Phase = PioneerExecutionProofPhase.SeaPrecheck;
						validity.Add("InvalidatedSeaPickup");
						break;
					}

					validity.Add("RevalidatedSeaPickup");
					if (IsPioneerSeaLandingEvidenceCurrent(source, mobile, center,
						transformsInfo, intoActor, buildingInfo, work))
						validity.Add("RevalidatedSeaLanding");
					else
					{
						ClearPioneerSeaLandingEvidence(work);
						work.Phase = PioneerExecutionProofPhase.SeaLanding;
						validity.Add("InvalidatedSeaLanding");
					}
					break;
			}

			work.RiskRevision = riskRevision;
			perf.RiskValidity = string.Join("+", validity);
		}

		static bool HasCompletePioneerSeaProofEvidence(PioneerExecutionProofWork work)
		{
			return work != null && work.Phase == PioneerExecutionProofPhase.SeaRefinery &&
				(work.LandRouteFailureTerrainStable || work.LandRouteRejected || work.LandRefineryRejected) &&
				work.PickupNavalRegion >= 0 && work.PickupMcvPath.Length > 0 &&
				work.SeaLandingPath.Length > 0 && !string.IsNullOrEmpty(work.SeaRefineryType);
		}

		bool TryRevalidateCompletedPioneerSeaProof(Actor source, Mobile mobile, CPos center,
			TransformsInfo transformsInfo, ActorInfo intoActor, BuildingInfo buildingInfo,
			PioneerExecutionProofWork work, int riskRevision, out string failure, out string validity)
		{
			failure = null;
			var validityParts = new List<string> { "RetainedTerminalSeaProof", "ExactValidation" };
			if (!EnsurePioneerLandRejectionCurrent(source, mobile, center,
				transformsInfo, intoActor, buildingInfo, work, riskRevision,
				requireRiskCurrent: true, validityParts))
				failure = "LandNegativeInvalid";
			else if (!HasNearbyShore(center, Info.SeaLandingSearchRadius) ||
				IsSeaTopologyFailureCached(center, work.PickupNavalRegion))
				failure = "PickupOrLandingTopologyInvalid";
			else if (!IsPioneerSeaPickupEvidenceCurrent(source, mobile, work, out var pickupFailure))
				failure = pickupFailure;
			else if (!IsPioneerSeaLandingEvidenceCurrent(source, mobile, center,
				transformsInfo, intoActor, buildingInfo, work, out var landingFailure))
				failure = landingFailure;
			else if (!IsPioneerSeaRefineryEvidenceCurrent(source, center, work, out var refineryFailure))
				failure = refineryFailure;

			if (failure != null)
				validityParts.Add("RetainedTerminalSeaProofInvalid");
			else
			{
				validityParts.Add("RevalidatedSeaPickup");
				validityParts.Add("RevalidatedSeaLanding");
				validityParts.Add("RevalidatedSeaRefinery");
				work.RiskRevision = riskRevision;
			}

			validity = string.Join("+", validityParts);
			return failure == null;
		}

		static string PioneerProofIdentityMismatchReasons(uint previousActorId, CPos previousCell,
			int previousRiskRevision, int previousTerrainVersion, uint actorId, CPos cell,
			int riskRevision, int terrainVersion)
		{
			var reasons = new List<string>();
			if (previousActorId != actorId)
				reasons.Add("McvActorId");
			if (previousCell != cell)
				reasons.Add("McvCell");
			if (previousRiskRevision != riskRevision)
				reasons.Add("RiskRevision");
			if (previousTerrainVersion != terrainVersion)
				reasons.Add("TerrainKnowledgeVersion");
			return reasons.Count == 0 ? "None" : string.Join("+", reasons);
		}

		static string PioneerProofLifecycleMismatchReasons(uint previousActorId, CPos previousCell,
			int previousTerrainVersion, uint actorId, CPos cell, int terrainVersion)
		{
			var reasons = new List<string>();
			if (previousActorId != actorId)
				reasons.Add("McvActorId");
			if (previousCell != cell)
				reasons.Add("McvCell");
			if (previousTerrainVersion != terrainVersion)
				reasons.Add("TerrainKnowledgeVersion");
			return reasons.Count == 0 ? "None" : string.Join("+", reasons);
		}

		int RecordPioneerProofPhaseForCurrentTick()
		{
			if (pioneerProofPhaseWorldTick != world.WorldTick)
			{
				pioneerProofPhaseWorldTick = world.WorldTick;
				pioneerProofPhasesThisTick = 0;
			}

			return ++pioneerProofPhasesThisTick;
		}

		void LogPioneerPhysicalProofPerf(Actor source, Mobile mobile, CPos center,
			int riskRevision, int terrainVersion, PioneerPhysicalProofPerf perf,
			PioneerExecutionProofPhase phase, PioneerExecutionProofPhase? nextPhase,
			PioneerObjectiveExecutionKind result, bool pending)
		{
			if (source == null || mobile == null || perf == null)
				return;

			try
			{
				var objectiveRole = activePioneerObjective.HasValue && activePioneerObjective.Value == center
					? "PRIMARY"
					: alternatePioneerObjective.HasValue && alternatePioneerObjective.Value == center
						? "ALTERNATE"
						: "TRANSIENT";
				var cacheState = perf.CacheHit ? "Hit" : perf.CachePresent ? "Miss" : "Absent";
				var workState = perf.WorkRecreated
					? perf.WorkPresent ? "Recreated" : "Created"
					: perf.WorkPresent ? "Reused" : "NotChecked";
				var land = perf.LandRoutePerf;
				var seaLanding = perf.SeaLandingPerf;
				var targetCount = land?.LastNativeTargetCount ?? 0;
				var targetHash = targetCount > 0 ? $"{land.LastNativeTargetHash:X8}" : "none";
				OpenRA.Log.Write("debug",
					$"[MCV PIONEER PROOF][WT {world.WorldTick}] caller={perf.Caller} " +
					$"mcv={source.ActorID}/{source.Info.Name}/{mobile.ToCell} " +
					$"primary={(activePioneerObjective.HasValue ? activePioneerObjective.Value.ToString() : "none")} " +
					$"alternate={(alternatePioneerObjective.HasValue ? alternatePioneerObjective.Value.ToString() : "none")} " +
					$"objective={center} role={objectiveRole} " +
					$"cache={cacheState} cacheMiss={perf.CacheMissReason ?? "None"} cacheAge={perf.CacheAge} " +
					$"cachedMcv={perf.CachedMcvActorId}/{perf.CachedMcvCell} " +
					$"cachedRiskRevision={perf.CachedRiskRevision} cachedTerrainVersion={perf.CachedTerrainKnowledgeVersion} " +
					$"cachedKind={perf.CachedKind} work={workState} workReset={perf.WorkResetReason ?? "None"} " +
					$"workRiskRevision={perf.WorkRiskRevision} workRiskChanged={perf.WorkRiskRevisionChanged} " +
					$"retainedSeaProof={perf.RetainedSeaProofState} retainedTrigger={perf.RetainedSeaProofTrigger} " +
					$"retainedFailure={perf.RetainedSeaProofFailure} retainedPathCells={perf.RetainedSeaProofPathCells} " +
					$"retainedMs={perf.RetainedSeaProofElapsedMs:0.00} avoidedPickupSearch={perf.RetainedSeaProofAvoidedPickupSearch} " +
					$"fullRecompute={perf.FullPioneerRecomputationFollowed} " +
					$"riskValidity={perf.RiskValidity} deferred={perf.PhaseDeferred} " +
					$"previousPhase={(perf.PreviousPhase.HasValue ? perf.PreviousPhase.Value.ToString() : "none")} " +
					$"phase={phase} nextPhase={(nextPhase.HasValue ? nextPhase.Value.ToString() : "none")} " +
					$"riskRevision={riskRevision} terrainVersion={terrainVersion} " +
					$"deployTargets={targetCount} orderedTargetHash={targetHash} " +
					$"blocker=Immovable tolerance={CurrentMcvRiskTolerance} laneBias=False " +
					$"physicalNativeSearches={land?.PhysicalNativePathSearches ?? 0} " +
					$"nativeMs={(land?.NativePathSearchElapsedMs ?? 0):0.00} " +
					$"pathCostCallbacks={land?.NativePathCostCallbackCalls ?? 0} " +
					$"seaPickupCursor={perf.SeaPickupCursor}/{perf.SeaPickupCandidates} " +
					$"seaPickupNativeSearches={perf.SeaPickupNativeSearchesThisPass} " +
					$"seaPickupTargets={perf.SeaPickupTargetCellsThisPass} " +
					$"seaPickupCallbacks={perf.SeaPickupPathCostCallbacksThisPass} " +
					$"seaPickupNativeMs={perf.SeaPickupNativeElapsedMsThisPass:0.00} " +
					$"seaPickupNativeSearchesTotal={perf.SeaPickupNativeSearchesTotal} " +
					$"seaLandingNativeSearches={seaLanding?.PhysicalNativePathSearches ?? 0} " +
					$"seaLandingTargets={seaLanding?.NativeTargetCells ?? 0} " +
					$"seaLandingCallbacks={seaLanding?.NativePathCostCallbackCalls ?? 0} " +
					$"seaLandingNativeMs={(seaLanding?.NativePathSearchElapsedMs ?? 0):0.00} " +
					$"phasesThisTick={perf.PhasesThisTick} phaseMs={perf.PhaseElapsedMs:0.00} " +
					$"result={(perf.PhaseDeferred ? "Deferred" : pending ? "Pending" : result.ToString())} elapsedMs={ElapsedMilliseconds(perf.Started):0.00}");
			}
			catch
			{
				// Proof diagnostics must never influence objective selection or PIONEER ownership.
			}
		}

		bool TryGetPioneerObjectivePhysicalExecution(Actor source, CPos center, string caller,
			out PioneerObjectiveExecutionKind executionKind, out bool pending)
		{
			executionKind = PioneerObjectiveExecutionKind.None;
			pending = false;
			if (!IsLiveOwnedMcv(source))
				return false;

			var mobile = source.TraitOrDefault<Mobile>();
			var transformsInfo = source.Info.TraitInfoOrDefault<TransformsInfo>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused || transformsInfo == null ||
				!world.Map.Rules.Actors.TryGetValue(transformsInfo.IntoActor, out var intoActor))
				return false;

			var buildingInfo = intoActor.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return false;

			var riskRevision = riskModelService?.RiskRevision ?? -1;
			var terrainVersion = strategicMapService?.TerrainKnowledgeVersion ?? -1;
			var proofLifetime = Math.Max(25, Info.PioneerReconHoldReplanInterval);
			var perf = new PioneerPhysicalProofPerf
			{
				Caller = caller,
				Started = Stopwatch.GetTimestamp()
			};
			if (pioneerExecutionProofCache.TryGetValue(center, out var cachedProof))
			{
				perf.CachePresent = true;
				perf.CacheAge = world.WorldTick - cachedProof.Tick;
				perf.CachedMcvActorId = cachedProof.McvActorId;
				perf.CachedMcvCell = cachedProof.McvCell;
				perf.CachedRiskRevision = cachedProof.RiskRevision;
				perf.CachedTerrainKnowledgeVersion = cachedProof.TerrainKnowledgeVersion;
				perf.CachedKind = cachedProof.Kind;
				var identityMiss = PioneerProofIdentityMismatchReasons(cachedProof.McvActorId, cachedProof.McvCell,
					cachedProof.RiskRevision, cachedProof.TerrainKnowledgeVersion,
					source.ActorID, mobile.ToCell, riskRevision, terrainVersion);
				var ageMiss = perf.CacheAge >= proofLifetime;
				perf.CacheHit = identityMiss == "None" && !ageMiss;
				perf.CacheMissReason = perf.CacheHit
					? "None"
					: identityMiss == "None"
						? "Age"
						: ageMiss ? identityMiss + "+Age" : identityMiss;
				if (perf.CacheHit)
				{
					executionKind = cachedProof.Kind;
					if (executionKind == PioneerObjectiveExecutionKind.Sea)
					{
						perf.RetainedSeaProofState = "CacheHitNoRevalidation";
						perf.RetainedSeaProofAvoidedPickupSearch = true;
						LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
							perf, PioneerExecutionProofPhase.SeaRefinery, null, executionKind, pending: false);
					}
					return executionKind != PioneerObjectiveExecutionKind.None;
				}

				var lifecycleMiss = PioneerProofLifecycleMismatchReasons(cachedProof.McvActorId,
					cachedProof.McvCell, cachedProof.TerrainKnowledgeVersion,
					source.ActorID, mobile.ToCell, terrainVersion);
				var riskMiss = cachedProof.RiskRevision != riskRevision;
				if (cachedProof.Kind == PioneerObjectiveExecutionKind.Sea)
				{
					perf.RetainedSeaProofTrigger = riskMiss && ageMiss
						? "RiskRevision+Age"
						: riskMiss ? "RiskRevision" : ageMiss ? "Age" : "Identity";
					if (lifecycleMiss == "None" && (riskMiss || ageMiss))
					{
						if (!pioneerCompletedSeaProofs.TryGetValue(center, out var completedSeaProof))
						{
							perf.RetainedSeaProofState = "Unavailable";
							perf.RetainedSeaProofFailure = "NoRetainedEvidence";
						}
						else if (PioneerProofLifecycleMismatchReasons(completedSeaProof.McvActorId,
							completedSeaProof.McvCell, completedSeaProof.TerrainKnowledgeVersion,
							source.ActorID, mobile.ToCell, terrainVersion) != "None")
						{
							perf.RetainedSeaProofState = "Insufficient";
							perf.RetainedSeaProofFailure = "RetainedIdentityMismatch";
						}
						else if (!HasCompletePioneerSeaProofEvidence(completedSeaProof))
						{
							perf.RetainedSeaProofState = "Insufficient";
							perf.RetainedSeaProofFailure = "IncompleteRetainedEvidence";
						}
						else
						{
							perf.RetainedSeaProofPathCells = completedSeaProof.PickupMcvPath.Length +
								completedSeaProof.SeaLandingPath.Length;
							var retainedStarted = Stopwatch.GetTimestamp();
							bool retainedValid;
							string retainedFailure;
							string retainedValidity;
							using (FransBotLog.Profile(world, player, "MCV.PioneerRetainedSeaProofRevalidation"))
								retainedValid = TryRevalidateCompletedPioneerSeaProof(source, mobile, center,
									transformsInfo, intoActor, buildingInfo, completedSeaProof, riskRevision,
									out retainedFailure, out retainedValidity);
							perf.RetainedSeaProofElapsedMs = ElapsedMilliseconds(retainedStarted);
							perf.RiskValidity = retainedValidity;
							if (retainedValid)
							{
								perf.RetainedSeaProofState = "ExactValidationSuccess";
								perf.RetainedSeaProofAvoidedPickupSearch = true;
								pioneerExecutionProofCache[center] = new PioneerExecutionProofCacheEntry(
									source.ActorID, mobile.ToCell, riskRevision, terrainVersion,
									world.WorldTick, PioneerObjectiveExecutionKind.Sea);
								executionKind = PioneerObjectiveExecutionKind.Sea;
								LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
									perf, PioneerExecutionProofPhase.SeaRefinery, null, executionKind, pending: false);
								return true;
							}

							perf.RetainedSeaProofState = "ExactValidationFailure";
							perf.RetainedSeaProofFailure = retainedFailure ?? "Unknown";
						}
					}
					else
					{
						perf.RetainedSeaProofState = "Unavailable";
						perf.RetainedSeaProofFailure = lifecycleMiss;
					}

					pioneerCompletedSeaProofs.Remove(center);
					perf.FullPioneerRecomputationFollowed = true;
				}
			}
			else
			{
				perf.CacheMissReason = "Absent";
				pioneerCompletedSeaProofs.Remove(center);
			}

			perf.WorkPresent = pioneerExecutionProofWork.TryGetValue(center, out var work);
			if (perf.WorkPresent)
			{
				perf.PreviousPhase = work.Phase;
				perf.WorkRiskRevision = work.RiskRevision;
				perf.WorkRiskRevisionChanged = work.RiskRevision != riskRevision;
				perf.WorkResetReason = PioneerProofLifecycleMismatchReasons(work.McvActorId, work.McvCell,
					work.TerrainKnowledgeVersion, source.ActorID, mobile.ToCell, terrainVersion);
			}
			else
				perf.WorkResetReason = "Absent";

			if (!perf.WorkPresent || perf.WorkResetReason != "None")
			{
				perf.WorkRecreated = true;
				work = new PioneerExecutionProofWork
				{
					McvActorId = source.ActorID,
					McvCell = mobile.ToCell,
					RiskRevision = riskRevision,
					TerrainKnowledgeVersion = terrainVersion,
					Phase = PioneerExecutionProofPhase.LandRoute
				};
				pioneerExecutionProofWork[center] = work;
			}
			else
				perf.RiskValidity = perf.WorkRiskRevisionChanged ? "RetainedPendingValidation" : "Current";

			// Module-wide structural guard: a cache hit may still be consumed immediately, but
			// no caller may execute a second physical-proof phase in the same world tick.
			if (pioneerProofPhaseWorldTick == world.WorldTick && pioneerProofPhasesThisTick > 0)
			{
				perf.PhasesThisTick = pioneerProofPhasesThisTick;
				perf.PhaseDeferred = true;
				perf.RiskValidity = perf.WorkRiskRevisionChanged ? "DeferredPendingRiskValidation" : "DeferredCurrent";
				pending = true;
				LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
					perf, work.Phase, work.Phase, PioneerObjectiveExecutionKind.None, pending: true);
				return false;
			}

			PreparePioneerProofPhaseForCurrentRisk(source, mobile, center, transformsInfo,
				intoActor, buildingInfo, work, riskRevision, perf);

			perf.PhasesThisTick = RecordPioneerProofPhaseForCurrentTick();

			// RELEASE PERFORMANCE: advance exactly one expensive physical-proof phase per call.
			// The old synchronous chain could combine land pathfinding, refinery placement, sea
			// topology, landing-side search and a second refinery proof into one 100+ ms tick.
			// Each phase preserves the same exact predicates and final result; callers treat
			// pending work as neither success nor failure and retry on the normal planning cadence.
			using (FransBotLog.Profile(world, player, "MCV.PioneerExactPhysicalProof"))
			{
				switch (work.Phase)
				{
					case PioneerExecutionProofPhase.LandRoute:
						using (FransBotLog.Profile(world, player, "MCV.PioneerProof.LandRoute"))
						{
							var proofPass = new McvObjectivePerfPass();
							var landPerf = proofPass.Land;
							perf.LandRoutePerf = landPerf;
							var phaseStarted = Stopwatch.GetTimestamp();
							var attemptEvidence = new PioneerLandRouteAttemptEvidence();
							var landPathFound = TryFindSafeDeployPath(source, mobile, center,
								transformsInfo, intoActor, buildingInfo, out var landDeployCell,
								out var landPathLength, out var landRoutePath, attemptEvidence, landPerf, center);
							var landRouteDetourAccepted = landPathFound &&
								IsMcvRouteDetourAcceptable(mobile.ToCell, landDeployCell, landPathLength);
							if (landRouteDetourAccepted)
							{
								ClearPioneerLandRouteEvidence(work);
								ClearPioneerSeaPickupEvidence(work);
								work.LandDeployCell = landDeployCell;
								work.LandRoutePath = landRoutePath;
								work.Phase = PioneerExecutionProofPhase.LandRefinery;
							}
							else
							{
								ClearPioneerLandRouteEvidence(work);
								ClearPioneerSeaPickupEvidence(work);
								work.LandRouteRejected = true;
								work.LandRouteFailureTerrainStable = IsTerrainStableLandRouteFailure(work.McvCell, center);
								work.LandRouteRejectedRiskRevision = riskRevision;
								if (work.LandRouteFailureTerrainStable)
								{
									work.LandRouteFailureKind = PioneerLandRouteFailureKind.StableTopology;
									perf.RiskValidity += "+RecordedStableTopologyLandRouteFailure";
								}
								else
								{
									work.LandRouteLegalDeployCells = GetPioneerLandRouteLegalDeployCells(source, mobile,
										center, transformsInfo, intoActor, buildingInfo);
									work.LandRouteSafeDeployCells = attemptEvidence.SafeDeployCells;
									work.LandRouteReturnedPath = attemptEvidence.ReturnedPath;
									if (work.LandRouteLegalDeployCells.Length == 0)
									{
										work.LandRouteFailureKind = PioneerLandRouteFailureKind.NoLegalDeployCell;
										perf.RiskValidity += "+RecordedNoLegalDeployCellLandRouteFailure";
									}
									else if (attemptEvidence.SafeDeployCells.Length == 0)
									{
										work.LandRouteFailureKind = PioneerLandRouteFailureKind.CautiousRiskRejectedAllLegalCandidates;
										perf.RiskValidity += "+RecordedCautiousRiskLandRouteFailure";
									}
									else if (!attemptEvidence.NativePathSearchAttempted)
									{
										work.LandRouteFailureKind = PioneerLandRouteFailureKind.MissingPathFinder;
										perf.RiskValidity += "+RecordedMissingPathFinderLandRouteFailure";
									}
									else if (attemptEvidence.ReturnedPathRejectedForRisk)
									{
										work.LandRouteFailureKind = PioneerLandRouteFailureKind.ReturnedPathCriticalRisk;
										perf.RiskValidity += "+RecordedReturnedPathCriticalRiskLandRouteFailure";
									}
									else if (!landPathFound)
									{
										work.LandRouteFailureKind = PioneerLandRouteFailureKind.NativePathNotFound;
										perf.RiskValidity += "+RecordedNativePathNullLandRouteFailure";
									}
									else
									{
										work.LandRouteFailureKind = PioneerLandRouteFailureKind.RouteDetour;
										perf.RiskValidity += "+RecordedRouteDetourLandRouteFailure";
									}

									work.LandRouteFailureRiskSensitive =
										work.LandRouteFailureKind == PioneerLandRouteFailureKind.CautiousRiskRejectedAllLegalCandidates ||
										work.LandRouteFailureKind == PioneerLandRouteFailureKind.NativePathNotFound ||
										work.LandRouteFailureKind == PioneerLandRouteFailureKind.ReturnedPathCriticalRisk ||
										work.LandRouteFailureKind == PioneerLandRouteFailureKind.RouteDetour;
									if (work.LandRouteFailureKind == PioneerLandRouteFailureKind.NativePathNotFound ||
										work.LandRouteFailureKind == PioneerLandRouteFailureKind.ReturnedPathCriticalRisk ||
										work.LandRouteFailureKind == PioneerLandRouteFailureKind.RouteDetour)
									{
										work.LandRouteBlockedCells = GetPioneerLandRouteRelevantBlockedCells(source, mobile,
											work.McvCell, work.LandRouteSafeDeployCells);
										GetPioneerLandRouteRiskCostEvidence(source, mobile, work.McvCell,
											work.LandRouteSafeDeployCells, out work.LandRouteRiskCostCells,
											out work.LandRouteRiskCosts);
									}
								}
								work.Phase = PioneerExecutionProofPhase.SeaPrecheck;
							}
							landPerf.ElapsedMs = ElapsedMilliseconds(phaseStarted);
							perf.PhaseElapsedMs = landPerf.ElapsedMs;
						}
						pending = true;
						LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
							perf, PioneerExecutionProofPhase.LandRoute, work.Phase,
							PioneerObjectiveExecutionKind.None, pending: true);
						return false;

					case PioneerExecutionProofPhase.LandRefinery:
						var landRefineryStarted = Stopwatch.GetTimestamp();
						using (FransBotLog.Profile(world, player, "MCV.PioneerProof.LandRefinery"))
						{
							var refineryCooling = IsFutureRefineryProofCooling(center);
							var failureRiskSensitive = false;
							var refineryProven = !refineryCooling &&
								TryProveFutureExpansionRefineryPlacement(source, work.LandDeployCell,
									out _, out _, out failureRiskSensitive);
							if (refineryProven)
							{
								pioneerExecutionProofCache[center] = new PioneerExecutionProofCacheEntry(source.ActorID, mobile.ToCell, riskRevision, terrainVersion, world.WorldTick, PioneerObjectiveExecutionKind.Land);
								pioneerCompletedSeaProofs.Remove(center);
								pioneerExecutionProofWork.Remove(center);
								executionKind = PioneerObjectiveExecutionKind.Land;
								perf.PhaseElapsedMs = ElapsedMilliseconds(landRefineryStarted);
								LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
									perf, PioneerExecutionProofPhase.LandRefinery, null, executionKind, pending: false);
								return true;
							}
							work.LandRefineryRejected = true;
							work.LandRefineryFailureRiskSensitive = !refineryCooling && failureRiskSensitive;
							work.LandRefineryRejectedRiskRevision = riskRevision;
							GetFutureExpansionRefineryLegalFootprints(source, work.LandDeployCell,
								out work.LandRefineryLegalTypes, out work.LandRefineryLegalCells);
							ClearPioneerSeaPickupEvidence(work);
							work.Phase = PioneerExecutionProofPhase.SeaPrecheck;
						}
						perf.PhaseElapsedMs = ElapsedMilliseconds(landRefineryStarted);
						pending = true;
						LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
							perf, PioneerExecutionProofPhase.LandRefinery, work.Phase,
							PioneerObjectiveExecutionKind.None, pending: true);
						return false;

					case PioneerExecutionProofPhase.SeaPrecheck:
						var seaPrecheckStarted = Stopwatch.GetTimestamp();
						using (FransBotLog.Profile(world, player, "MCV.PioneerProof.SeaPrecheck"))
						{
							var pickupFound = TryAdvanceReachableRoutineSeaPickupProof(source, mobile,
								out var pickupMcvCell, out var pickupCraftCell, out var pickupMcvPath,
								out var pickupSearchExhausted);
							var pickupPerf = routineSeaPickupProof;
							if (pickupPerf != null)
							{
								perf.SeaPickupCursor = pickupPerf.NextBeachIndex;
								perf.SeaPickupCandidates = pickupPerf.RankedBeaches.Length;
								perf.SeaPickupNativeSearchesThisPass = pickupPerf.LastPassNativeSearches;
								perf.SeaPickupTargetCellsThisPass = pickupPerf.LastPassTargetCells;
								perf.SeaPickupPathCostCallbacksThisPass = pickupPerf.LastPassPathCostCallbacks;
								perf.SeaPickupNativeElapsedMsThisPass = pickupPerf.LastPassElapsedMs;
								perf.SeaPickupNativeSearchesTotal = pickupPerf.NativeSearches;
							}
							if (!pickupFound && !pickupSearchExhausted)
							{
								perf.PhaseElapsedMs = ElapsedMilliseconds(seaPrecheckStarted);
								pending = true;
								LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
									perf, PioneerExecutionProofPhase.SeaPrecheck, work.Phase,
									PioneerObjectiveExecutionKind.None, pending: true);
								return false;
							}

							if (!pickupFound ||
								strategicMapService == null ||
								!strategicMapService.TryGetNavalRegionId(pickupCraftCell, out var pickupNavalRegion) ||
								!HasNearbyShore(center, Info.SeaLandingSearchRadius) ||
								IsSeaTopologyFailureCached(center, pickupNavalRegion))
							{
								var retryPhase = GetPioneerLandRejectionRetryPhaseForTerminalResult(work);
								if (retryPhase.HasValue)
								{
									work.Phase = retryPhase.Value;
									perf.RiskValidity += retryPhase.Value == PioneerExecutionProofPhase.LandRoute
										? "+TerminalLandRouteRetryRequired+DeferredTerminalNoneForLandRouteRetry"
										: "+DeferredTerminalNoneForLandRefineryRetry";
									perf.PhaseElapsedMs = ElapsedMilliseconds(seaPrecheckStarted);
									pending = true;
									LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
										perf, PioneerExecutionProofPhase.SeaPrecheck, work.Phase,
										PioneerObjectiveExecutionKind.None, pending: true);
									return false;
								}
								perf.RiskValidity += "+TerminalLandNegativeRetained";

								pioneerExecutionProofCache[center] = new PioneerExecutionProofCacheEntry(source.ActorID, mobile.ToCell, riskRevision, terrainVersion, world.WorldTick, PioneerObjectiveExecutionKind.None);
								pioneerCompletedSeaProofs.Remove(center);
								pioneerExecutionProofWork.Remove(center);
								perf.PhaseElapsedMs = ElapsedMilliseconds(seaPrecheckStarted);
								LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
									perf, PioneerExecutionProofPhase.SeaPrecheck, null,
									PioneerObjectiveExecutionKind.None, pending: false);
								return false;
							}

							if (!HasKnownLandingShoreInNavalRegion(center, pickupNavalRegion))
							{
								RememberSeaTopologyFailure(center, pickupNavalRegion,
									"PIONEER target has shoreline, but none belongs to the MCV pickup naval region");
								var retryPhase = GetPioneerLandRejectionRetryPhaseForTerminalResult(work);
								if (retryPhase.HasValue)
								{
									work.Phase = retryPhase.Value;
									perf.RiskValidity += retryPhase.Value == PioneerExecutionProofPhase.LandRoute
										? "+TerminalLandRouteRetryRequired+DeferredTerminalNoneForLandRouteRetry"
										: "+DeferredTerminalNoneForLandRefineryRetry";
									perf.PhaseElapsedMs = ElapsedMilliseconds(seaPrecheckStarted);
									pending = true;
									LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
										perf, PioneerExecutionProofPhase.SeaPrecheck, work.Phase,
										PioneerObjectiveExecutionKind.None, pending: true);
									return false;
								}
								perf.RiskValidity += "+TerminalLandNegativeRetained";

								pioneerExecutionProofCache[center] = new PioneerExecutionProofCacheEntry(source.ActorID, mobile.ToCell, riskRevision, terrainVersion, world.WorldTick, PioneerObjectiveExecutionKind.None);
								pioneerCompletedSeaProofs.Remove(center);
								pioneerExecutionProofWork.Remove(center);
								perf.PhaseElapsedMs = ElapsedMilliseconds(seaPrecheckStarted);
								LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
									perf, PioneerExecutionProofPhase.SeaPrecheck, null,
									PioneerObjectiveExecutionKind.None, pending: false);
								return false;
							}

							work.PickupNavalRegion = pickupNavalRegion;
							work.PickupMcvCell = pickupMcvCell;
							work.PickupCraftCell = pickupCraftCell;
							work.PickupMcvPath = pickupMcvPath;
							ClearPioneerSeaLandingEvidence(work);
							work.SeaLandingSearch = new RoutineSeaOreSearchState(source.ActorID, mobile.ToCell,
								terrainVersion, allowMapWideFallback: false,
								[new OreFieldCandidate(center, (center - mobile.ToCell).LengthSquared)])
							{
								PickupProven = true
							};
							work.Phase = PioneerExecutionProofPhase.SeaLanding;
						}
						perf.PhaseElapsedMs = ElapsedMilliseconds(seaPrecheckStarted);
						pending = true;
						LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
							perf, PioneerExecutionProofPhase.SeaPrecheck, work.Phase,
							PioneerObjectiveExecutionKind.None, pending: true);
						return false;

					case PioneerExecutionProofPhase.SeaLanding:
						var seaLandingStarted = Stopwatch.GetTimestamp();
						using (FransBotLog.Profile(world, player, "MCV.PioneerProof.SeaLanding"))
						{
							work.SeaLandingSearch ??= new RoutineSeaOreSearchState(source.ActorID, mobile.ToCell,
								terrainVersion, allowMapWideFallback: false,
								[new OreFieldCandidate(center, (center - mobile.ToCell).LengthSquared)])
							{
								PickupProven = true
							};
							var landingProtectors = GetOwnedSeaLandingProtectors();
							var seaLandingPass = new McvObjectivePerfPass();
							perf.SeaLandingPerf = seaLandingPass.Sea;
							var landingFound = TryAdvanceRoutineSeaLandingProof(work.SeaLandingSearch,
								source, mobile, center, transformsInfo, intoActor, buildingInfo,
								work.PickupNavalRegion, landingProtectors,
								out var seaLandingCraftCell, out var seaDeployCell, out var seaLandingSearchExhausted,
								out var seaLandingExitCell, out var seaLandingPath, perf.SeaLandingPerf);
							if (!landingFound && !seaLandingSearchExhausted)
							{
								perf.PhaseElapsedMs = ElapsedMilliseconds(seaLandingStarted);
								pending = true;
								LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
									perf, PioneerExecutionProofPhase.SeaLanding, work.Phase,
									PioneerObjectiveExecutionKind.None, pending: true);
								return false;
							}

							if (!landingFound)
							{
								var retryPhase = GetPioneerLandRejectionRetryPhaseForTerminalResult(work);
								if (retryPhase.HasValue)
								{
									work.Phase = retryPhase.Value;
									perf.RiskValidity += retryPhase.Value == PioneerExecutionProofPhase.LandRoute
										? "+TerminalLandRouteRetryRequired+DeferredTerminalNoneForLandRouteRetry"
										: "+DeferredTerminalNoneForLandRefineryRetry";
									perf.PhaseElapsedMs = ElapsedMilliseconds(seaLandingStarted);
									pending = true;
									LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
										perf, PioneerExecutionProofPhase.SeaLanding, work.Phase,
										PioneerObjectiveExecutionKind.None, pending: true);
									return false;
								}
								perf.RiskValidity += "+TerminalLandNegativeRetained";

								pioneerExecutionProofCache[center] = new PioneerExecutionProofCacheEntry(source.ActorID, mobile.ToCell, riskRevision, terrainVersion, world.WorldTick, PioneerObjectiveExecutionKind.None);
								pioneerCompletedSeaProofs.Remove(center);
								pioneerExecutionProofWork.Remove(center);
								perf.PhaseElapsedMs = ElapsedMilliseconds(seaLandingStarted);
								LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
									perf, PioneerExecutionProofPhase.SeaLanding, null,
									PioneerObjectiveExecutionKind.None, pending: false);
								return false;
							}
							work.SeaLandingCraftCell = seaLandingCraftCell;
							work.SeaLandingExitCell = seaLandingExitCell;
							work.SeaDeployCell = seaDeployCell;
							work.SeaLandingPath = seaLandingPath;
							work.Phase = PioneerExecutionProofPhase.SeaRefinery;
						}
						perf.PhaseElapsedMs = ElapsedMilliseconds(seaLandingStarted);
						pending = true;
						LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
							perf, PioneerExecutionProofPhase.SeaLanding, work.Phase,
							PioneerObjectiveExecutionKind.None, pending: true);
						return false;

					case PioneerExecutionProofPhase.SeaRefinery:
						var seaRefineryStarted = Stopwatch.GetTimestamp();
						using (FransBotLog.Profile(world, player, "MCV.PioneerProof.SeaRefinery"))
						{
							string seaRefineryType = null;
							var seaRefineryCell = default(CPos);
							var kind = !IsFutureRefineryProofCooling(center) &&
								TryProveFutureExpansionRefineryPlacement(source, work.SeaDeployCell,
									out seaRefineryType, out seaRefineryCell)
								? PioneerObjectiveExecutionKind.Sea
								: PioneerObjectiveExecutionKind.None;
							pioneerExecutionProofCache[center] = new PioneerExecutionProofCacheEntry(source.ActorID, mobile.ToCell, riskRevision, terrainVersion, world.WorldTick, kind);
							if (kind == PioneerObjectiveExecutionKind.Sea)
							{
								work.SeaRefineryType = seaRefineryType;
								work.SeaRefineryCell = seaRefineryCell;
								pioneerCompletedSeaProofs[center] = work;
							}
							else
								pioneerCompletedSeaProofs.Remove(center);
							pioneerExecutionProofWork.Remove(center);
							executionKind = kind;
							perf.PhaseElapsedMs = ElapsedMilliseconds(seaRefineryStarted);
							LogPioneerPhysicalProofPerf(source, mobile, center, riskRevision, terrainVersion,
								perf, PioneerExecutionProofPhase.SeaRefinery, null, executionKind, pending: false);
							return kind != PioneerObjectiveExecutionKind.None;
						}
				}
			}

			return false;
		}

		bool TryContinuePendingPioneerPhysicalProof(Actor executionSource)
		{
			if (!activePioneerObjective.HasValue || !alternatePioneerObjective.HasValue ||
				!IsLiveOwnedMcv(executionSource))
				return false;

			var primary = activePioneerObjective.Value;
			var alternate = alternatePioneerObjective.Value;
			if (!pioneerExecutionProofWork.TryGetValue(alternate, out var work))
				return false;

			var mobile = executionSource.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused ||
				work.McvActorId != executionSource.ActorID || work.McvCell != mobile.ToCell)
			{
				ClearPioneerObjectiveProofEvidence(alternate);
				return false;
			}

			// Re-run the authoritative permission gate before bypassing the long planning
			// cooldown. If PRIMARY became ready, reopen normal planning immediately. If the
			// gate changed objective ownership, end this pass because abandonment may itself
			// have consumed the single permitted physical-proof phase.
			if (!RequiresPioneerReconBeforeCommit(primary))
			{
				nextLandExpansionPlanningTick = world.WorldTick;
				return false;
			}

			if (!activePioneerObjective.HasValue || activePioneerObjective.Value != primary ||
				!alternatePioneerObjective.HasValue || alternatePioneerObjective.Value != alternate)
			{
				nextLandExpansionPlanningTick = world.WorldTick;
				return true;
			}

			// A tactical-state change ends this continuation. Normal long-cadence planning
			// remains responsible for reconsidering an objective that later becomes ready.
			if (HasReconRequirementNear(alternate) || HasSecureRequirementNear(alternate) ||
				!IsPioneerObjectiveIntelReady(alternate))
			{
				ClearPioneerObjectiveProofEvidence(alternate);
				return false;
			}

			if (TryPromoteReadyAlternatePioneerObjective(executionSource, "PendingProofContinuation"))
			{
				// Promotion is immediate, but this pass has already consumed its one physical-
				// proof phase. Reopen planning for the next module scan and exit this pass.
				nextLandExpansionPlanningTick = world.WorldTick;
				return true;
			}

			return true;
		}

		bool TryPromoteReadyAlternatePioneerObjective(Actor executionSource,
			string physicalProofCaller = "ReadyAlternatePromotion")
		{
			if (!alternatePioneerObjective.HasValue)
				return false;

			var alternate = alternatePioneerObjective.Value;
			if (HasReconRequirementNear(alternate) || HasSecureRequirementNear(alternate) ||
				!IsPioneerObjectiveIntelReady(alternate))
				return false;

			if (!IsExpansionGroundSecured(alternate))
			{
				var exposure = riskModelService.EvaluateExpansionExposure(alternate);
				if (IsPioneerHostileCore(exposure))
				{
					ClearAlternatePioneerObjective(
						$"scout revealed hostile core structure exposure {exposure.StructureScore} >= {Info.PioneerHostileCoreStructureScore}",
						markFailed: true);
					return false;
				}

				// A contested ALTERNATE is useful insurance, but it must not steal PRIMARY status
				// merely to publish a second strategic invasion. It can become PRIMARY on timeout/
				// abandonment, at which point normal SECURE permission is evaluated.
				if (exposure.Level == FransExpansionExposureLevel.Contested)
					return false;
			}

			// Intel readiness and physical executability are deliberately separate. A scout-cleared
			// backup is never promoted until the current physical MCV can actually reach/deploy there;
			// this prevents promote -> route-fail -> abandon loops.
			// A deployed FACT cannot prove an MCV path yet, so completed-outpost holding simply
			// keeps the prepared alternate until a physical roaming MCV exists.
			if (!IsLiveOwnedMcv(executionSource))
				return false;

			if (!TryGetPioneerObjectivePhysicalExecution(executionSource, alternate, physicalProofCaller,
				out var executionKind, out var proofPending))
			{
				if (proofPending)
					return false;
				ClearAlternatePioneerObjective(
					"scout-cleared backup has no currently executable bounded land/sea MCV route", markFailed: true);
				return false;
			}

			PromoteAlternatePioneerObjective(
				$"ALTERNATE is scout-cleared and physically executable by {executionKind} while PRIMARY is still waiting",
				retainOldPrimaryAsAlternate: true);
			return true;
		}

		CPos? FindAlternatePioneerObjectiveHint(Actor source, CPos primary)
		{
			if (source == null || source.Disposed || !source.IsInWorld || source.IsDead || source.Owner != player)
				return null;

			var ownServiceStructures = world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && Info.ExpansionRefineryTypes.Contains(a.Info.Name))
				.ToArray();
			var ownCoverageStructures = world.ActorsHavingTrait<Building>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && Info.ExistingBaseCoverageTypes.Contains(a.Info.Name))
				.ToArray();
			var fallbackDistanceSquared = Info.FallbackMaximumExpansionHopDistance > 0
				? (long)Info.FallbackMaximumExpansionHopDistance * Info.FallbackMaximumExpansionHopDistance
				: long.MaxValue;

			combatIntelService.EnsureCurrentSnapshot();
			var distinctRadiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			return EnumerateExpansionObjectiveCenters()
				.Where(center => world.Map.Contains(center) && (center - primary).LengthSquared > distinctRadiusSquared)
				.Where(center => !IsFieldTemporarilyFailed(center) && !IsExpansionCandidateBlockedBeforeSelection(center))
				.Where(center => !IsFieldServiced(center, ownServiceStructures, ownCoverageStructures))
				.Where(center => !IsMcvCriticalRisk(source, center, CurrentMcvRiskTolerance))
				.Where(center => (center - source.Location).LengthSquared <= fallbackDistanceSquared)
				.Where(center =>
				{
					if (strategicMapService == null ||
						!strategicMapService.TryGetGroundLandmassId(source.Location, out var sourceLandmass) ||
						!strategicMapService.TryGetGroundLandmassId(center, out var targetLandmass) ||
						sourceLandmass == targetLandmass)
						return true;
					return HasNearbyShore(center, Info.SeaLandingSearchRadius);
				})
				.Select(center => new OreFieldCandidate(center, (center - source.Location).LengthSquared))
				.OrderBy(candidate => candidate.DistanceSquared)
				.ThenBy(candidate => candidate.ResourceCenter.X)
				.ThenBy(candidate => candidate.ResourceCenter.Y)
				.Select(candidate => (CPos?)candidate.ResourceCenter)
				.FirstOrDefault();
		}

		void EnsureAlternatePioneerObjective(Actor source)
		{
			if (!activePioneerObjective.HasValue || alternatePioneerObjective.HasValue)
				return;

			var alternate = FindAlternatePioneerObjectiveHint(source, activePioneerObjective.Value);
			if (alternate.HasValue)
				SetAlternatePioneerObjective(alternate.Value, "nearest plausible backup to the current PRIMARY");
		}

		void CompleteActivePioneerObjective(string reason)
		{
			if (!activePioneerObjective.HasValue && !alternatePioneerObjective.HasValue)
				return;

			var completed = activePioneerObjective;
			foreach (var objective in TrackedPioneerObjectives().ToArray())
			{
				ClearReconRequirementNear(objective);
				ClearSecureRequirementNear(objective);
				ClearPioneerObjectiveProofEvidence(objective);
			}

			activePioneerObjective = null;
			activePioneerObjectiveStartedTick = -1;
			alternatePioneerObjective = null;
			alternatePioneerObjectiveStartedTick = -1;
			FransBotLog.BotDebug(world,
				"{0}: DUAL PIONEER pre-commit pair releases ownership after PRIMARY {1}: {2}.",
				player, completed.HasValue ? completed.Value.ToString() : "none", reason ?? "objective committed or completed");
		}

		void AbandonActivePioneerObjective(string reason, Actor executionSource = null)
		{
			if (!activePioneerObjective.HasValue)
				return;

			var abandoned = activePioneerObjective.Value;
			ClearReconRequirementNear(abandoned);
			ClearSecureRequirementNear(abandoned);
			ClearPioneerObjectiveProofEvidence(abandoned);
			var until = world.WorldTick + Info.PioneerObjectiveAbandonCooldownTicks;
			if (!failedExpansionAreasUntil.TryGetValue(abandoned, out var existing) || existing < until)
				failedExpansionAreasUntil[abandoned] = until;

			var promoted = alternatePioneerObjective;
			var preservePendingAlternate = false;
			if (promoted.HasValue && IsLiveOwnedMcv(executionSource) &&
				!HasReconRequirementNear(promoted.Value) && !HasSecureRequirementNear(promoted.Value) &&
				IsPioneerObjectiveIntelReady(promoted.Value) &&
				!TryGetPioneerObjectivePhysicalExecution(executionSource, promoted.Value, "PrimaryAbandonment",
					out _, out var proofPending))
			{
				if (proofPending)
				{
					preservePendingAlternate = true;
					promoted = null;
				}
				else
				{
					var rejected = promoted.Value;
					ClearReconRequirementNear(rejected);
					ClearSecureRequirementNear(rejected);
					var rejectedUntil = world.WorldTick + Info.PioneerObjectiveAbandonCooldownTicks;
					if (!failedExpansionAreasUntil.TryGetValue(rejected, out var rejectedExisting) || rejectedExisting < rejectedUntil)
						failedExpansionAreasUntil[rejected] = rejectedUntil;
					FransBotLog.BotDebug(world,
						"{0}: DUAL PIONEER refuses to promote scout-cleared ALTERNATE ore {1}: exact bounded land/sea MCV execution proof failed. Backup cools down through WT {2} instead of becoming another immediate PRIMARY route-fail.",
						player, rejected, rejectedUntil);
					promoted = null;
				}
			}

			var pendingAlternate = preservePendingAlternate ? alternatePioneerObjective : null;
			alternatePioneerObjective = null;
			alternatePioneerObjectiveStartedTick = -1;
			activePioneerObjective = promoted;
			activePioneerObjectiveStartedTick = promoted.HasValue ? world.WorldTick : -1;
			if (!promoted.HasValue && pendingAlternate.HasValue)
			{
				alternatePioneerObjective = pendingAlternate;
				alternatePioneerObjectiveStartedTick = world.WorldTick;
			}

			FransBotLog.BotDebug(world,
				promoted.HasValue
					? "{0}: DUAL PIONEER ABANDONS PRIMARY ore {1} through WT {2}: {3}. Prepared ALTERNATE {4} is promoted immediately; no stale SECURE bonus survives."
					: "{0}: DUAL PIONEER ABANDONS PRIMARY ore {1} through WT {2}: {3}. No physically-approved prepared alternate remains; planner may select a fresh pair immediately.",
				player, abandoned, until, reason ?? "objective no longer suitable for expansion",
				promoted.HasValue ? promoted.Value.ToString() : "");
		}

		bool IsPioneerHostileCore(FransExpansionExposureAssessment exposure) =>
			exposure.StructureScore >= Info.PioneerHostileCoreStructureScore;

		bool NeedsPioneerAirScoutDemand()
		{
			var source = IsLiveOwnedMcv(activeMcv)
				? activeMcv
				: activeConyard != null && activeConyard.IsInWorld && !activeConyard.IsDead && activeConyard.Owner == player
					? activeConyard
					: null;
			if (source == null)
				return false;

			foreach (var objective in TrackedPioneerObjectives())
			{
				if (!HasReconRequirementNear(objective) || HasSecureRequirementNear(objective) || IsExpansionGroundSecured(objective))
					continue;
				if (strategicMapService.TryGetGroundLandmassId(source.Location, out var sourceLandmass) &&
					strategicMapService.TryGetGroundLandmassId(objective, out var targetLandmass) &&
					sourceLandmass != targetLandmass)
					return true;
			}

			return false;
		}

		void MarkExpansionAreaRequiresRecon(CPos center, FransExpansionExposureAssessment exposure, string reason = null)
		{
			if (!IsTrackedPioneerObjective(center))
				SetActivePioneerObjective(center, "exact-cell validation is required before commit");

			var role = alternatePioneerObjective.HasValue && alternatePioneerObjective.Value == center ? "ALTERNATE" : "PRIMARY";
			MarkPioneerReconRequirement(center, role, exposure, reason);
		}

		bool TryAcceptPioneerDomainClearAfterExposureRecheck(CPos center)
		{
			if (generalService == null)
				return false;

			var notBefore = activePioneerObjectiveStartedTick >= 0 ? activePioneerObjectiveStartedTick : 0;
			if (!generalService.TryGetRecentDomainSecureClearNear(center, Info.ExpansionTargetFailureRadius, notBefore,
				out var commander, out var clearWorldTick))
				return false;

			if (pioneerDomainClearRecheckWorldTick.TryGetValue(center, out var processedTick) && processedTick >= clearWorldTick)
				return false;
			pioneerDomainClearRecheckWorldTick[center] = clearWorldTick;

			// Air/Sea CLEAR is not a territorial Ground Anchor. It is permission to spend one
			// fresh fair-intel exposure check on the exact PIONEER objective. Only a genuinely
			// non-contested result removes SECURE_REQUIRED.
			var exposure = riskModelService.EvaluateExpansionExposure(center);
			if (IsPioneerHostileCore(exposure))
			{
				AbandonActivePioneerObjective($"{commander} domain CLEAR was followed by a fresh hostile-core exposure {exposure.StructureScore}/{exposure.Score}", activeMcv);
				return false;
			}

			if (exposure.Level == FransExpansionExposureLevel.Contested)
			{
				FransBotLog.BotDebug(world,
					"{0}: DUAL PIONEER PRIMARY ore {1} keeps SECURE REQUIRED after {2} domain CLEAR WT {3}: fresh fair-intel exposure is still contested, score {4} (structures {5}, mobile {6}, control {7}).",
					player, center, commander, clearWorldTick, exposure.Score, exposure.StructureScore, exposure.MobileScore, exposure.ControlScore);
				return false;
			}

			ClearSecureRequirementNear(center);
			ClearReconRequirementNear(center);
			scoutedExpansionAreas.Add(center);
			FransBotLog.BotDebug(world,
				"{0}: DUAL PIONEER PRIMARY ore {1} accepts {2} domain CLEAR WT {3} after fresh fair-intel exposure recheck: area is no longer contested (score {4}). SECURE_REQUIRED closes without inventing a Ground Anchor; exact MCV feasibility must still pass normally.",
				player, center, commander, clearWorldTick, exposure.Score);
			return true;
		}

		bool RequiresPioneerReconBeforeCommit(CPos center)
		{
			if (!activePioneerObjective.HasValue || activePioneerObjective.Value != center)
				SetActivePioneerObjective(center, "planner reached the pre-commit permission gate");

			if (IsExpansionGroundSecured(center))
			{
				ClearReconRequirementNear(center);
				ClearSecureRequirementNear(center);
				return false;
			}

			if (HasSecureRequirementNear(center))
			{
				if (TryAcceptPioneerDomainClearAfterExposureRecheck(center))
					return false;
				return true;
			}

			var exposure = riskModelService.EvaluateExpansionExposure(center);

			// Known hostile-core memory is already a real tactical reason to reject this
			// objective. It does not need a redundant exact-cell scout before acting on fair intel.
			if (IsPioneerHostileCore(exposure))
			{
				AbandonActivePioneerObjective($"known hostile core structure exposure {exposure.StructureScore} >= {Info.PioneerHostileCoreStructureScore} (total {exposure.Score})", activeMcv);
				return true;
			}

			if (exposure.Level == FransExpansionExposureLevel.Contested)
			{
				ClearReconRequirementNear(center);
				MarkExpansionAreaRequiresSecure(center,
					$"known frontier exposure is contested but is not a hostile core: score {exposure.Score} (structures {exposure.StructureScore}, mobile {exposure.MobileScore}, control {exposure.ControlScore})");
				return true;
			}

			if (exposure.Level == FransExpansionExposureLevel.Uncertain && !HasPioneerScoutClearance(center))
			{
				MarkExpansionAreaRequiresRecon(center, exposure,
					"known tactical exposure is uncertain; static ore knowledge alone is not treated as tactical clearance");
				return true;
			}

			// Safe legally-known ore is ordinary economic CLAIM material. Exact visibility is
			// not a prerequisite because static map/resource knowledge is not enemy intelligence.
			ClearReconRequirementNear(center);
			ClearSecureRequirementNear(center);
			return false;
		}

		bool IsExpansionCandidateBlockedBeforeSelection(CPos center)
		{
			// Candidate enumeration is strictly non-mutating. Historical/fortified areas are
			// skipped, but only PRIMARY PIONEER may later create SECURE strategic work.
			if (IsExpansionGroundSecured(center))
				return false;

			var exposure = riskModelService.EvaluateExpansionExposure(center);
			return IsPioneerHostileCore(exposure);
		}

		void MarkExpansionAreaRequiresSecure(CPos center, string reason)
		{
			if (!activePioneerObjective.HasValue || activePioneerObjective.Value != center)
				SetActivePioneerObjective(center, "selected frontier requires Ground territorial clearance");

			ClearReconRequirementNear(center);
			foreach (var stale in secureRequiredExpansionAreas.Where(objective => objective != center).ToArray())
				secureRequiredExpansionAreas.Remove(stale);
			if (!secureRequiredExpansionAreas.Add(center))
				return;

			FransBotLog.BotDebug(world,
				"{0}: DUAL PIONEER PRIMARY ore {1} SECURE REQUIRED after {2}. This remains the ONLY expansion-unblock SECURE objective; ALTERNATE may scout but cannot publish a second +5000 invasion.",
				player, center, reason);
		}

		bool IsFieldTemporarilyFailed(CPos center)
		{
			if (failedFieldsUntil.TryGetValue(center, out var until) && world.WorldTick < until)
				return true;

			var expansionRadiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			if (failedExpansionAreasUntil.Any(kv => world.WorldTick < kv.Value &&
				(kv.Key - center).LengthSquared <= expansionRadiusSquared))
				return true;

			var refineryRadiusSquared = Info.FailedRefinerySiteRadius * Info.FailedRefinerySiteRadius;
			if (failedRefinerySitesUntil.Any(kv => world.WorldTick < kv.Value &&
				(kv.Key - center).LengthSquared <= refineryRadiusSquared))
				return true;

			var proofRadiusSquared = Info.ExpansionTargetFailureRadius * Info.ExpansionTargetFailureRadius;
			return futureRefineryProofFailuresUntil.Any(kv => world.WorldTick < kv.Value &&
				(kv.Key - center).LengthSquared <= proofRadiusSquared);
		}

		void MarkExpansionAreaFailed(CPos center, string reason)
		{
			MarkExpansionAreaRequiresSecure(center, reason);
			var until = world.WorldTick + Info.ExpansionTargetFailureCooldownTicks;
			if (!failedExpansionAreasUntil.TryGetValue(center, out var existing) || existing < until)
				failedExpansionAreasUntil[center] = until;
			FransBotLog.BotDebug(world,
				"{0}: expansion objective area {1} enters {2}-cell failure cooldown until WT {3} after {4}; nearby MineClusters are temporarily excluded from MCV target selection.",
				player, center, Info.ExpansionTargetFailureRadius, until, reason);
		}

		void MarkExpansionAreaCooldown(CPos center, int delay, string reason)
		{
			if (delay <= 0)
				return;

			var until = world.WorldTick + delay;
			if (!failedExpansionAreasUntil.TryGetValue(center, out var existing) || existing < until)
				failedExpansionAreasUntil[center] = until;
			FransBotLog.BotDebug(world,
				"{0}: PIONEER objective area {1} enters strategic {2}-cell cooldown until WT {3} after {4}. Nearby MineCluster coordinates share the same retry memory, so one physical field cannot bypass the watchdog by shifting one cell.",
				player, center, Info.ExpansionTargetFailureRadius, until, reason);
		}

		void MarkCurrentFieldFailed()
		{
			if (targetResourceCenter.HasValue)
				failedFieldsUntil[targetResourceCenter.Value] = world.WorldTick + Info.FailedFieldRetryDelay;
		}

		void MarkCurrentRefinerySiteFailed()
		{
			if (!targetResourceCenter.HasValue)
				return;

			var center = targetResourceCenter.Value;
			var until = world.WorldTick + Info.FailedRefinerySiteRetryDelay;
			if (!failedRefinerySitesUntil.TryGetValue(center, out var existing) || existing < until)
				failedRefinerySitesUntil[center] = until;

			FransBotLog.BotDebug(world,
				"{0}: refinery placement exhausted {1} attempts at ore site {2}; blacklisting the surrounding {3}-cell area until WT {4} before repack/local recovery.",
				player, Info.MaximumPlacementFailures, center, Info.FailedRefinerySiteRadius, until);
		}

		void CleanupFailedFields()
		{
			foreach (var center in failedFieldsUntil
				.Where(kv => world.WorldTick >= kv.Value)
				.Select(kv => kv.Key)
				.ToArray())
				failedFieldsUntil.Remove(center);

			foreach (var center in failedExpansionAreasUntil
				.Where(kv => world.WorldTick >= kv.Value)
				.Select(kv => kv.Key)
				.ToArray())
				failedExpansionAreasUntil.Remove(center);

			foreach (var center in failedRefinerySitesUntil
				.Where(kv => world.WorldTick >= kv.Value)
				.Select(kv => kv.Key)
				.ToArray())
				failedRefinerySitesUntil.Remove(center);

			foreach (var center in futureRefineryProofFailuresUntil
				.Where(kv => world.WorldTick >= kv.Value)
				.Select(kv => kv.Key)
				.ToArray())
				futureRefineryProofFailuresUntil.Remove(center);

			foreach (var key in seaLandingProofFailuresUntil
				.Where(kv => world.WorldTick >= kv.Value)
				.Select(kv => kv.Key)
				.ToArray())
				seaLandingProofFailuresUntil.Remove(key);
		}


		void RememberActiveMcvPosition()
		{
			if (activeMcv == null || !activeMcv.IsInWorld || activeMcv.IsDead || activeMcv.Owner != player)
				return;

			activeMcvLastKnownCell = activeMcv.Location;
			activeMcvLastSeenTick = world.WorldTick;
		}

		void HandleUnexpectedActiveMcvLoss(IBot bot, string context)
		{
			nextCoastalStagingSearchTick = 0;
			coastalStagingNavalNoProgressSinceTick = -1;
			ResumeFirstExpansionRefineryAfterInfrastructure("the temporary naval-infrastructure suspension was released before the first ore expansion completed");
			coastalStagingForSeaExpansion = false;
			coastalStagingReturnToSea = false;
			coastalStagingRepackOutcome = CoastalStagingRepackOutcome.None;
			var lost = activeMcv;
			var lostStage = stage;
			var lostField = targetResourceCenter;
			var lostDeploy = targetDeployCell;
			var lostCell = activeMcvLastKnownCell;
			var lostSeenTick = activeMcvLastSeenTick;

			FransBotLog.BotDebug(world,
				"{0}: ACTIVE MCV LOSS detected for {1} during {2}; stage {3}, last known cell {4} at WT {5}, target field {6}, deploy {7}. Clearing actor-owned expansion state before any reserve MCV may be adopted.",
				player, lost, context, lostStage, lostCell, lostSeenTick, lostField, lostDeploy);
			if (lostField.HasValue)
				MarkExpansionAreaFailed(lostField.Value, $"active MCV loss during {context}");

			// A replacement MCV must never inherit the dead actor's target, transform watchdog,
			// retreat state, route timers, refinery-recovery state, LST ownership or queue ownership.
			CancelOwnedRoutineExpansionStructureIfQueued(bot, $"active MCV loss during {context}");
			AbortFirstExpansionRefineryAttempt(bot, $"active MCV loss during {context}", lostField ?? lostDeploy);
			ResetMcvRetreat();
			mcvRetreatAfterRepackPending = false;
			refineryPlacementRecoveryPending = false;
			refineryPlacementFailedSite = null;
			activeMcv = null;
			ReturnExpansionTaskToIdle($"active MCV loss during {context}");
			activeMcvLastKnownCell = null;
			activeMcvLastSeenTick = -1;
		}

		void ResetTaskExecutionProgress()
		{
			lastCommittedSeaExecutionDiagnosticSignature = null;
			lastCommittedSeaCorridorRecoveryDiagnosticSignature = null;
			seaExactPathFailureStartedTick = -1;
			lastLandingCraftPlanHadPickupFailure = false;
			lastLandingCraftPlanHadCrossingFailure = false;
			committedSeaCorridorRecovery = null;
			lastTransformCell = null;
			conyardTransformIssuedTick = -1;
			conyardTransformRetries = 0;
			ResetDeployClearanceState();
			repackTransformIssuedTick = -1;
			repackTransformRetries = 0;
			placementFailures = 0;
			nextRouteRecheckTick = 0;
			movingMcvLastProgressCell = null;
			movingMcvLastProgressTick = -1;
			movingMcvStallRetries = 0;
			nextSeaBoardingRetryTick = 0;
			ResetSeaUnloadRecovery();
			nextSeaRouteRiskRecheckTick = 0;
			seaPickupMcvLastProgressCell = null;
			seaPickupMcvLastProgressTick = -1;
			seaPickupMcvStallRetries = 0;
			seaPickupApproachRejectedCells.Clear();
			seaPickupApproachRecoveryAttempts = 0;
			seaPickupCraftLastProgressCell = null;
			seaPickupCraftLastProgressTick = -1;
			seaPickupCraftStallRetries = 0;
			seaTransportLastProgressCell = null;
			seaTransportLastProgressTick = -1;
			seaTransportStallRetries = 0;
			seaLastRiskRevision = -1;
			seaLastTransportLossExclusionRevision = -1;
			seaTransportLossBlockedRevision = -1;
		}

		void ClearTarget()
		{
			targetResourceCenter = null;
			targetDeployCell = null;
			targetReservationStartedTick = -1;
			postSeaUnloadDeployCommitted = false;
			if (!coastalStagingForSeaExpansion && !coastalStagingReturnToSea)
			{
				deferredRoutineFerryObjective = null;
				deferredRoutineFerryReservationStartedTick = -1;
			}
			seaPickupMcvCell = null;
			seaPickupCraftCell = null;
			seaLandingCraftCell = null;
			committedSeaGeometrySearch = null;
			ResetTaskExecutionProgress();
		}

		// BaseBuilder may still send expansion nudges when it places production/tech buildings.
		// Frans expansion is intentionally deterministic, so those nudges are ignored.
		void IBotBaseExpansion.UpdateExpansionParams(IBot bot, bool fallback, bool undeployEvenNoBase, Actor mustUndeploy)
		{
		}

		// Cameo engine patch: BaseBuilderCA clears its RelocationHoldConyard once no
		// expansion module reports it pending. Fransbot manages its conyard lifecycle
		// itself (activeConyard + GrantBaseBuilderLock) and never asks BaseBuilder to
		// hold one, so nothing is pending through this interface.
		bool IBotBaseExpansion.IsConyardRelocationPending(Actor conyard)
		{
			return false;
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			ReleaseBaseBuilderLock();
			mcvs?.Dispose();
			constructionYards?.Dispose();
			mcvFactories?.Dispose();
		}
	}
}
