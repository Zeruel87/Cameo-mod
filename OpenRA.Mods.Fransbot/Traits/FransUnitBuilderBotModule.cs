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
using System.Collections.Immutable;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public interface IFransOpeningUnitPlanService
	{
		bool OpeningVehicleEconomyReadyForMcv { get; }
		bool OpeningMcvProductionStarted { get; }
	}

	/// <summary>
	/// Explicit production mailbox owned by UnitBuilder and written only by SpecOps.
	/// Mailbox requests are checked at each free production queue before ordinary saturation.
	/// </summary>
	public interface IFransSpecOpsProductionMailbox
	{
		void RequestSpecOpsProduction(IBot bot, string requestedActor);
		int RequestedSpecOpsProductionCount(IBot bot, string requestedActor);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Controls Fransbots unit production. Infantry and vehicles prefer the functioning producer nearest the current Ground Commander objective, falling back to the stable front. RiskModel belongs to the produced unit's later MOVE, not producer selection. The deterministic opening may start its single manual HARV; all post-opening HARV demand and redistribution is owned by FransHarvesterBotModule.")]
	public class FransUnitBuilderBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Production queue categories used for producing units.")]
		public readonly ImmutableArray<string> UnitQueues = ["Vehicle", "Infantry", "Plane", "Ship", "Aircraft"];

		[Desc("Relative desired share of each unit type.")]
		public readonly FrozenDictionary<string, int> UnitsToBuild = FrozenDictionary<string, int>.Empty;

		[Desc("Maximum number of each unit type.")]
		public readonly FrozenDictionary<string, int> UnitLimits = FrozenDictionary<string, int>.Empty;

		[Desc("World tick before which each unit type should not be trained.")]
		public readonly FrozenDictionary<string, int> UnitDelays = FrozenDictionary<string, int>.Empty;

		[ActorReference]
		[Desc("Unit types that this Fransbot personality must never produce, including external production requests.")]
		public readonly FrozenSet<string> HardDisabledUnitTypes = FrozenSet<string>.Empty;

		[Desc("Only queue construction of a new unit when above this cash/resources requirement after the deterministic opening.")]
		public readonly int ProductionMinCashRequirement = 500;

		[Desc("Cash/resources requirement used throughout the deterministic opening until the first MCV has physically completed.")]
		public readonly int OpeningProductionMinCashRequirement = 1000;

		[Desc("Percent of mobile-combat production picks that may choose the best fog-honest counter to the observed enemy army (sourced from CombatIntel's seen/remembered contacts). 0 disables.")]
		public readonly int AdaptiveCounterWeight = 0;

		[Desc("Ticks between enemy-composition samples that feed adaptive counter-production.")]
		public readonly int AdaptiveCounterObservationInterval = 250;

		[ActorReference]
		[Desc("Unit types blocked until the first opening MCV has physically completed, not merely started production.")]
		public readonly FrozenSet<string> DelayUntilOpeningMcvCompletedUnitTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Demand-only capture specialists allowed through the hard opening lock. AirAI uses E6 so early Oil Derrick / civilian capture opportunities remain available without unlocking general SpecOps spending.")]
		public readonly FrozenSet<string> OpeningCaptureSpecialistTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Rifle infantry used by the deterministic Fransbot opening.")]
		public readonly FrozenSet<string> OpeningRifleTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Rocket infantry used by the deterministic Fransbot opening.")]
		public readonly FrozenSet<string> OpeningRocketTypes = FrozenSet<string>.Empty;

		[Desc("Preferred light map-control vehicle vehicle types for the Fransbot opening, tried in configured order.")]
		public readonly string[] OpeningLightVehicleTypes = [];

		[Desc("Minimum rifle orders to start before PROC #2 is complete.")]
		public readonly int OpeningRifleTargetBeforeSecondRefinery = 12;

		[Desc("Total rifle orders to start before the first opening MCV begins production.")]
		public readonly int OpeningRifleTarget = 15;

		[Desc("Rocket infantry orders started after PROC #2 and before the first opening MCV.")]
		public readonly int OpeningRocketTarget = 3;

		[Desc("Manually produced harvesters after the light map-control vehicle and before the opening MCV. Fast Expansion keeps this one standard opening HARV; after the opening MCV physically completes, FransHarvester owns all later HARV demand.")]
		public readonly int OpeningManualHarvesterTarget = 1;

		[ActorReference]
		[Desc("Vehicle factories eligible for tactical producer selection.")]
		public readonly FrozenSet<string> PreferredVehicleProducerTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Heavy vehicle types that remain blocked until the configured number of physically completed functioning vehicle factories exists.")]
		public readonly FrozenSet<string> MultiFactoryGatedVehicleTypes = FrozenSet<string>.Empty;

		[Desc("Number of completed functioning WEAP required before MultiFactoryGatedVehicleTypes may be produced.")]
		public readonly int MultiFactoryGatedVehicleMinimumProducerCount = 3;

		[ActorReference]
		[Desc("Infantry factories used by Fransbot.")]
		public readonly FrozenSet<string> PreferredInfantryProducerTypes = FrozenSet<string>.Empty;

		[Desc("If true, infantry production prefers the functioning BARR/TENT closest to the current Ground Commander objective, falling back to the stable strategic front.")]
		public readonly bool PreferStrategicInfantryProducer = true;

		[Desc("If true, vehicle production prefers the functioning WEAP closest to the current Ground Commander objective, falling back to the stable strategic front instead of the newest factory.")]
		public readonly bool PreferStrategicVehicleProducer = true;

		[ActorReference]
		[Desc("Externally requested unit types attempted before other pending special requests.")]
		public readonly FrozenSet<string> PriorityRequestedUnitTypes = FrozenSet<string>.Empty;

		[Desc("Fallback reserve for non-harvester strategic priority production when no exact native RemainingCost can be read. During the first opening MCV and first expansion PROC, instead protects the exact remaining production bill and permits only fully funded surplus Infantry/Vehicle spending.")]
		public readonly int CriticalPriorityProductionReserveCash = 3000;

		[Desc("Minimum world ticks between debug messages while critical priority-production reserve protection is holding new spending.")]
		public readonly int CriticalPriorityProductionLogInterval = 300;

		[ActorReference]
		[Desc("Harvester actor types used by the deterministic opening and accepted as external economy requests. Post-opening HARV demand is NOT calculated here.")]
		public readonly FrozenSet<string> HarvesterTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Refinery actor types used only by the deterministic opening to detect physical PROC #2.")]
		public readonly FrozenSet<string> ResourceControlStructureTypes = FrozenSet<string>.Empty;

		[Desc("Cash/resources threshold used while FransHarvester has submitted an explicit HARV production request.")]
		public readonly int HarvesterProductionMinCashRequirement = 100;

		[Desc("Cash/resources floor at which an explicit SpecOps mailbox request may use a free compatible queue even when ordinary military saturation is paused.")]
		public readonly int SpecOpsProductionMinCashRequirement = 100;

		[Desc("Cash/resources floor for one explicit PIONEER cross-landmass scout aircraft when the active expansion objective requires exact RECON and the AI owns/queues zero combat aircraft. Protected HARV/MCV/first-PROC reserves still outrank this demand.")]
		public readonly int PioneerAirScoutMinCashRequirement = 100;

		[Desc("Immediate cash/resources threshold below which ordinary Sea combat production is suspended first and currently queued ordinary Sea combat units are cancelled once on entry.")]
		public readonly int EconomicEmergencySeaSuspendCash = 500;

		[Desc("Lower emergency threshold below which ordinary Air combat production is also suspended and currently queued ordinary Air combat units are cancelled once on entry.")]
		public readonly int EconomicEmergencyAirSuspendCash = 250;

		[Desc("Cash/resources level required before ordinary Air production resumes after an economic emergency. Must exceed the Air suspend threshold.")]
		public readonly int EconomicEmergencyAirResumeCash = 1000;

		[Desc("Cash/resources level required before ordinary Sea production resumes after an economic emergency. This is deliberately above Air resume so Navy restarts last.")]
		public readonly int EconomicEmergencySeaResumeCash = 1500;

		[Desc("Minimum live + already queued ordinary combat aircraft retained/built while Air ordinary production is economically suspended. This preserves a small defensive Air reserve without reopening normal Air saturation.")]
		public readonly int EconomicEmergencyMinimumAirCombatReserve = 3;

		[Desc("Minimum world ticks between repeated economic-emergency hold diagnostics.")]
		public readonly int EconomicEmergencyLogInterval = 250;

		[Desc("Maximum combined aircraft using the same rearm-building family per physical rearm building. This replaces the old one-aircraft-of-each-type-per-building gate.")]
		public readonly int AirUnitsPerRearmBuilding = 4;

		[ActorReference]
		[Desc("Primary fixed-wing Air composition family. AirAI keeps this family at the configured weight relative to AirFixedWingSecondaryTypes whenever both are buildable.")]
		public readonly FrozenSet<string> AirFixedWingPrimaryTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Secondary fixed-wing Air composition family paired with AirFixedWingPrimaryTypes.")]
		public readonly FrozenSet<string> AirFixedWingSecondaryTypes = FrozenSet<string>.Empty;

		[Desc("Target production/composition weight for AirFixedWingPrimaryTypes.")]
		public readonly int AirFixedWingPrimaryWeight = 2;

		[Desc("Target production/composition weight for AirFixedWingSecondaryTypes.")]
		public readonly int AirFixedWingSecondaryWeight = 1;

		[ActorReference]
		[Desc("Primary rotary-wing Air composition family. AirAI keeps this family at the configured weight relative to AirRotaryWingSecondaryTypes whenever both are buildable.")]
		public readonly FrozenSet<string> AirRotaryWingPrimaryTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Secondary rotary-wing Air composition family paired with AirRotaryWingPrimaryTypes.")]
		public readonly FrozenSet<string> AirRotaryWingSecondaryTypes = FrozenSet<string>.Empty;

		[Desc("Target production/composition weight for AirRotaryWingPrimaryTypes.")]
		public readonly int AirRotaryWingPrimaryWeight = 2;

		[Desc("Target production/composition weight for AirRotaryWingSecondaryTypes.")]
		public readonly int AirRotaryWingSecondaryWeight = 1;

		[ActorReference]
		[Desc("Allied Sea combat composition family. When at least two are currently buildable, UnitBuilder balances the buildable members equally (1:1:1 with three, 1:1 with two).")]
		public readonly FrozenSet<string> AlliedSeaCombatTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Soviet Sea combat composition family. When both are currently buildable, UnitBuilder balances them equally 1:1.")]
		public readonly FrozenSet<string> SovietSeaCombatTypes = FrozenSet<string>.Empty;


		[ActorReference]
		[Desc("Advanced ordinary/random unit types withheld until the shared economy reaches Prosperous. Explicit emergency/strategic requests still bypass this ordinary-composition gate.")]
		public readonly FrozenSet<string> ProsperousUnitTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Ground vehicle artillery family used as one combined Commander-domain composition pool. ARTY and V2RL share one target rather than each demanding the full percentage.")]
		public readonly FrozenSet<string> GroundVehicleArtilleryTypes = FrozenSet<string>.Empty;

		[Desc("Desired combined percentage of live Ground combat vehicles that should be ARTY or V2RL. The denominator excludes infantry, aircraft, ships, MCV/HARV and specialist logistics.")]
		public readonly int GroundVehicleArtilleryShare = 33;

		[Desc("If true, every usable military production queue is kept non-empty after the deterministic opening whenever the normal production cash floor is met. Economic state changes composition and producer growth, not whether an existing queue is allowed to sit idle. Protected MCV/first-PROC RemainingCost reserves may temporarily pause or defer ordinary Ground spending so those economic-critical items cannot stall.")]
		public readonly bool KeepAllMilitaryQueuesFilled = true;

		[Desc("If true, positive UnitLimits are composition targets instead of production stops for ordinary combat units. UnitLimit 0 remains a hard disable. Demand-only logistics such as LST are not part of ordinary composition and therefore need no fixed UnitLimit cap.")]
		public readonly bool PositiveCombatUnitLimitsAreSoft = true;

		[ActorReference]
		[Desc("Minelayer unit types whose ordinary production is delayed until Fransbot has useful fair enemy-location intel.")]
		public readonly FrozenSet<string> IntelGatedMinelayerTypes = FrozenSet<string>.Empty;

		[Desc("Earliest world tick at which an intel-gated minelayer may be produced.")]
		public readonly int MinelayerEarliestProductionTick = 9000;

		[Desc("Minimum remembered/visible enemy combat contacts that make minelayer production useful. A sufficiently confident remembered enemy structure also satisfies the gate.")]
		public readonly int MinelayerMinimumEnemyCombatContacts = 3;

		[Desc("Minimum confidence percentage of one fair remembered enemy structure that may satisfy the minelayer intel gate.")]
		public readonly int MinelayerMinimumKnownStructureConfidencePercent = 35;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (UnitQueues.Length == 0 || OpeningLightVehicleTypes.Any(string.IsNullOrWhiteSpace))
				throw new YamlException("UnitBuilder needs at least one production queue.");
			if (ProductionMinCashRequirement < 0 || OpeningProductionMinCashRequirement < 0 || HarvesterProductionMinCashRequirement < 0 ||
				CriticalPriorityProductionReserveCash < 0 || CriticalPriorityProductionLogInterval <= 0 ||
				OpeningRifleTargetBeforeSecondRefinery < 0 || OpeningRifleTargetBeforeSecondRefinery > OpeningRifleTarget ||
				OpeningRifleTarget < 0 || OpeningRocketTarget < 0 || OpeningManualHarvesterTarget < 0 ||
				MultiFactoryGatedVehicleMinimumProducerCount <= 0)
				throw new YamlException("UnitBuilder opening/production thresholds are invalid.");
			if (AirUnitsPerRearmBuilding <= 0 || AirFixedWingPrimaryWeight <= 0 || AirFixedWingSecondaryWeight <= 0 ||
				AirRotaryWingPrimaryWeight <= 0 || AirRotaryWingSecondaryWeight <= 0 ||
				GroundVehicleArtilleryShare < 0 || GroundVehicleArtilleryShare > 100)
				throw new YamlException("UnitBuilder Air/Ground composition settings are invalid.");
			if (MinelayerEarliestProductionTick < 0 || MinelayerMinimumEnemyCombatContacts < 0 ||
				MinelayerMinimumKnownStructureConfidencePercent < 0 || MinelayerMinimumKnownStructureConfidencePercent > 100)
				throw new YamlException("UnitBuilder minelayer intel-gate settings are invalid.");
			if (SpecOpsProductionMinCashRequirement < 0 || PioneerAirScoutMinCashRequirement < 0 || EconomicEmergencySeaSuspendCash < 0 || EconomicEmergencyAirSuspendCash < 0 ||
				EconomicEmergencyAirSuspendCash > EconomicEmergencySeaSuspendCash ||
				EconomicEmergencyAirResumeCash <= EconomicEmergencyAirSuspendCash ||
				EconomicEmergencySeaResumeCash <= EconomicEmergencySeaSuspendCash ||
				EconomicEmergencySeaResumeCash < EconomicEmergencyAirResumeCash || EconomicEmergencyMinimumAirCombatReserve <= 0 || EconomicEmergencyLogInterval <= 0)
				throw new YamlException("UnitBuilder SpecOps/economic-emergency production thresholds are invalid.");
			if (AdaptiveCounterWeight < 0 || AdaptiveCounterWeight > 100 || AdaptiveCounterObservationInterval <= 0)
				throw new YamlException("UnitBuilder adaptive counter-production settings are invalid.");
		}

		public override object Create(ActorInitializer init) { return new FransUnitBuilderBotModule(init.Self, this); }
	}

	public class FransUnitBuilderBotModule : ConditionalTrait<FransUnitBuilderBotModuleInfo>,
		IBotTick, IBotRequestUnitProduction, IGameSaveTraitData, INotifyActorDisposing,
		IFransOpeningUnitPlanService, IFransSpecOpsProductionMailbox
	{
		public const int FeedbackTime = 30;

		readonly World world;
		readonly Player player;
		readonly List<string> queuedBuildRequests = [];
		readonly List<string> specOpsBuildRequests = [];
		readonly HashSet<(uint ActorId, string Item)> protectedProductionPauses = [];
		readonly ActorIndex.OwnerAndNames unitsToBuild;
		readonly ActorIndex.OwnerAndNames resourceControlStructures;

		IBotRequestPauseUnitProduction[] requestPause;
		AdaptiveCounterProduction counters;
		IBotEnemyCompositionProvider compositionProvider;
		IFransEconomicSaturationService economicSaturationService;
		IFransBaseBuilderService openingBuildOrderService;
		IFransCombatIntelService combatIntelService;
		IFransStrategicMapService strategicMapService;
		IFransExpansionStateService expansionStateService;
		IFransCommanderCoreService groundCommanderService;
		PlayerResources playerResources;

		int currentQueueIndex;
		FransQueueDomains queueDomains;
		FransQueueDomains QueueDomains => queueDomains ??= FransQueueDomains.For(world.Map.Rules);
		int ticks;
		int lastCriticalPriorityReserveLogTick = -1;
		int lastEconomicEmergencyLogTick = -1;
		bool seaProductionSuspendedForEconomy;
		bool airProductionSuspendedForEconomy;
		FransEconomicState previousEconomicState = FransEconomicState.Growing;

		int openingRiflesStarted;
		int openingRocketsStarted;
		int openingManualHarvestersStarted;
		bool openingLightVehicleSatisfied;
		bool openingMcvProductionStarted;

		public bool OpeningVehicleEconomyReadyForMcv =>
			openingLightVehicleSatisfied && openingManualHarvestersStarted >= Math.Max(0, Info.OpeningManualHarvesterTarget);
		public bool OpeningMcvProductionStarted => openingMcvProductionStarted;

		public FransUnitBuilderBotModule(Actor self, FransUnitBuilderBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			counters = new AdaptiveCounterProduction(world, player);
			unitsToBuild = new ActorIndex.OwnerAndNames(world, info.UnitsToBuild.Keys, player);
			resourceControlStructures = new ActorIndex.OwnerAndNames(world, info.ResourceControlStructureTypes, player);
		}

		protected override void Created(Actor self)
		{
			requestPause = self.Owner.PlayerActor.TraitsImplementing<IBotRequestPauseUnitProduction>().ToArray();
			economicSaturationService = self.Owner.PlayerActor.TraitsImplementing<IFransEconomicSaturationService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransUnitBuilderBotModule requires FransEconomicSaturationBotModule.");
			openingBuildOrderService = self.Owner.PlayerActor.TraitsImplementing<IFransBaseBuilderService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransUnitBuilderBotModule requires FransBaseBuilderBotModule.");
			combatIntelService = self.Owner.PlayerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransUnitBuilderBotModule requires FransCombatIntelBotModule.");
			strategicMapService = self.Owner.PlayerActor.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransUnitBuilderBotModule requires FransStrategicMapBotModule.");
			expansionStateService = self.Owner.PlayerActor.TraitsImplementing<IFransExpansionStateService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransUnitBuilderBotModule requires FransMcvExpansionManagerBotModule.");
			groundCommanderService = self.Owner.PlayerActor.TraitsImplementing<IFransCommanderCoreService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransUnitBuilderBotModule requires Ground Commander service.");
			playerResources = self.Owner.PlayerActor.Trait<PlayerResources>();
			compositionProvider = self.Owner.PlayerActor.TraitsImplementing<IBotEnemyCompositionProvider>().FirstOrDefault();
		}

		protected override void TraitEnabled(Actor self)
		{
			FransBotLog.BotDebug(world,
				"{0}: FransUnitBuilder EXACT ECONOMIC RESERVES + PIONEER AIR-SCOUT BOOTSTRAP active: SpecOps still gets first refusal between normal free queues; Sea suspends first below {8}, Air below {9}, with a {12}-aircraft emergency reserve. During opening MCV production, exact native RemainingCost is protected while fully funded surplus Infantry/E6 may continue; after physical MCV the first expansion PROC receives the same absolute reserve while surplus Infantry/Vehicle production may continue. Air resumes at {10}, Sea at {11}; Yak:MiG {4}:{5}, MH60:Longbow {6}:{7}; ARTY/V2RL target {1}% of live Ground combat vehicles. Fallback strategic reserve {2}, feedback {3} WT.",
				player, Info.GroundVehicleArtilleryShare, Info.CriticalPriorityProductionReserveCash, FeedbackTime,
				Info.AirFixedWingPrimaryWeight, Info.AirFixedWingSecondaryWeight,
				Info.AirRotaryWingPrimaryWeight, Info.AirRotaryWingSecondaryWeight,
				Info.EconomicEmergencySeaSuspendCash, Info.EconomicEmergencyAirSuspendCash,
				Info.EconomicEmergencyAirResumeCash, Info.EconomicEmergencySeaResumeCash,
				Info.EconomicEmergencyMinimumAirCombatReserve);
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransUnitBuilder.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (requestPause.Any(rp => rp.PauseUnitProduction))
				return;

			ticks++;
			if (ticks % FeedbackTime != 0)
				return;

			var economicState = economicSaturationService.State;
			UpdateEconomicStateTransition(economicState);

			counters.Observe(Info.AdaptiveCounterObservationInterval, compositionProvider);

			var hasHarvesterDebt = queuedBuildRequests.Any(Info.HarvesterTypes.Contains);

			// Preserve extra cash while the deterministic Fransbot opening is active.
			// keeps OpeningComplete false until the first MCV physically exists.
			var openingInProgress = !openingBuildOrderService.OpeningComplete;
			var minimumCash = hasHarvesterDebt
				? Info.HarvesterProductionMinCashRequirement
				: openingInProgress
					? Info.OpeningProductionMinCashRequirement
					: Info.ProductionMinCashRequirement;

			var cash = playerResources.GetCashAndResources();
			ILookup<string, ProductionQueue> queuesByCategory = AIUtils.FindQueuesByCategory(player);
			UpdateEconomicEmergencyProduction(bot, queuesByCategory, cash);

			// protected-production budget. The first MCV no longer freezes Infantry:
			// its exact native RemainingCost is ring-fenced, and Infantry may spend only the cash
			// that remains above that reserve. The Vehicle queue remains dedicated to the MCV.
			if (openingMcvProductionStarted && openingBuildOrderService.OpeningLocked)
			{
				var mcvReserve = OpeningMcvRemainingCost(queuesByCategory);
				if (mcvReserve <= 0)
					mcvReserve = Math.Max(0, Info.CriticalPriorityProductionReserveCash);

				RunProtectedGroundProduction(bot, queuesByCategory, cash, mcvReserve,
					allowInfantry: true, allowVehicle: false, openingInfantryPlan: true, openingCaptureOnly: true,
					reserveLabel: "OPENING MCV");
				return;
			}

			// The very first post-MCV Building item is the reserved expansion PROC. Its exact
			// RemainingCost gets the same hard guarantee: Infantry and Vehicles may keep producing,
			// but only from money that is provably surplus to the refinery's remaining bill.
			var firstExpansionProcReserve = expansionStateService?.ProtectedFirstExpansionRefineryRemainingCost ?? 0;
			if (openingBuildOrderService.OpeningMcvCompleted && firstExpansionProcReserve > 0)
			{
				RunProtectedGroundProduction(bot, queuesByCategory, cash, firstExpansionProcReserve,
					allowInfantry: true, allowVehicle: true, openingInfantryPlan: false, openingCaptureOnly: false,
					reserveLabel: "FIRST EXPANSION PROC");
				return;
			}

			ReleaseProtectedProductionPauses(bot, queuesByCategory);

			// SpecOps has an explicit mailbox instead of competing with ordinary composition. Even below
			// the normal military floor, one genuinely requested specialist may take a compatible free
			// queue at the small emergency floor. This never blocks HARV/MCV strategic debt.
			if (cash < minimumCash)
			{
				if (!hasHarvesterDebt && cash >= Info.SpecOpsProductionMinCashRequirement)
					TryBuildOneSpecOpsRequest(bot, queuesByCategory, openingCaptureOnly: openingInProgress);
				return;
			}

			// A pending strategic MCV request must get one chance to enter its native queue BEFORE
			// the cash-reserve gate is evaluated. put the reserve test first, which meant an
			// accepted MCV request below the reserve threshold could block the very request loop that
			// needed to start it. Once physically queued, the normal reserve gate protects its income.
			foreach (var criticalRequest in queuedBuildRequests
				.Where(IsCriticalPriorityUnit)
				.OrderBy(RequestPriority)
				.ToArray())
			{
				if (!TryBuildRequestedUnit(bot, criticalRequest, queuesByCategory))
					continue;

				queuedBuildRequests.Remove(criticalRequest);
				return;
			}

			// Reserve income as soon as ExpansionManager has an accepted outstanding MCV request,
			// or after a priority unit is physically queued. This remains one cheap state read + queue
			// scan every FeedbackTime (30 WT), never a per-tick world scan.
			if (ShouldProtectCriticalPriorityProduction(queuesByCategory, cash))
				return;

			// A physical PIONEER MCV on one landmass may need exact RECON on another before any
			// routine Air exists. Grant exactly one strategic scout demand after economic-critical
			// reserves, but before ordinary Air emergency suspension can keep Aircraft at zero.
			if (!hasHarvesterDebt && !openingInProgress && cash >= Info.PioneerAirScoutMinCashRequirement &&
				TryBuildPioneerAirScout(bot, queuesByCategory))
				return;

			// Economic Air suspension is allowed to preserve a tiny defensive reserve, but never at the
			// expense of HARV debt or a protected MCV/strategic priority build. Build at most one reserve
			// aircraft per feedback pass; normal Air saturation remains suspended until hysteresis clears.
			if (!hasHarvesterDebt && !openingInProgress && cash >= Info.ProductionMinCashRequirement &&
				TryBuildEconomicEmergencyAirReserve(bot, queuesByCategory))
				return;

			// Remaining external requests stay ahead of ordinary production. Critical requests were
			// already handled above so the reserve gate can never starve its own MCV start again.
			if (!openingInProgress)
			{
				foreach (var buildRequest in queuedBuildRequests
					.Where(r => !IsCriticalPriorityUnit(r))
					.OrderBy(RequestPriority)
					.ToArray())
				{
					if (TryBuildRequestedUnit(bot, buildRequest, queuesByCategory))
					{
						queuedBuildRequests.Remove(buildRequest);
						break;
					}
				}
			}

			if (cash >= Info.SpecOpsProductionMinCashRequirement)
				TryBuildOneSpecOpsRequest(bot, queuesByCategory, openingCaptureOnly: openingInProgress);

			// Explicit HARV/MCV/SpecOps-specialist requests may use their lower emergency cash floor. Post-opening HARV debt originates in FransHarvester;
			// UnitBuilder only executes it. Ordinary queue saturation still obeys the normal production floor. Once
			// that floor is available, even Struggling keeps usable military queues working;
			// the economy state is a spending/throughput diagnosis, not an idle-order.
			var ordinaryMinimumCash = openingInProgress
				? Info.OpeningProductionMinCashRequirement
				: Info.ProductionMinCashRequirement;
			if (cash < ordinaryMinimumCash)
				return;


			// During the Fransbot opening, ordinary weighted production is replaced
			// by a deterministic concurrent infantry + vehicle plan:
			// rifles -> 3 rockets after PROC #2, one light map-control vehicle, then one manual harvester.
			// External strategic requests were already processed above and remain one-order-only.
			if (openingInProgress)
			{
				BuildHumanDoubleRefOpeningPlan(bot, queuesByCategory);
				return;
			}

			// Production saturation is the default, not a Prosperous/Surplus perk.
			// Existing usable queues should not sit empty while the bank grows. Economic state
			// still controls advanced-unit availability and BaseBuilder producer growth.
			if (Info.KeepAllMilitaryQueuesFilled)
			{
				BuildAllFreeMilitaryProduction(bot, queuesByCategory,
					Info.PositiveCombatUnitLimitsAreSoft,
					openingBuildOrderService.PauseOrdinaryVehicleProduction,
					openingBuildOrderService.PauseOrdinaryInfantryProduction);
				return;
			}

			for (var i = 0; i < Info.UnitQueues.Length; i++)
			{
				if (++currentQueueIndex >= Info.UnitQueues.Length)
					currentQueueIndex = 0;

				var category = Info.UnitQueues[currentQueueIndex];
				if (openingBuildOrderService.PauseOrdinaryVehicleProduction && QueueDomains.Vehicle.Contains(category))
					continue;
				if (openingBuildOrderService.PauseOrdinaryInfantryProduction && QueueDomains.Infantry.Contains(category))
					continue;
				if (seaProductionSuspendedForEconomy && QueueDomains.Naval.Contains(category))
					continue;
				if (airProductionSuspendedForEconomy && QueueDomains.Air.Contains(category))
					continue;

				var queues = queuesByCategory[category].ToArray();
				if (queues.Length == 0)
					continue;

				BuildRandomUnit(bot, category, queues);
				break;
			}
		}

		int OpeningMcvRemainingCost(ILookup<string, ProductionQueue> queuesByCategory)
		{
			foreach (var category in Info.UnitQueues)
				foreach (var queue in queuesByCategory[category].Where(IsUsableQueue))
				{
					var item = queue.AllQueued().FirstOrDefault(i =>
						Info.PriorityRequestedUnitTypes.Contains(i.Item) && !Info.HarvesterTypes.Contains(i.Item));
					if (item != null)
						return Math.Max(0, item.RemainingCost);
				}

			return 0;
		}

		void QueueProductionPause(IBot bot, ProductionQueue queue, ProductionItem item, bool paused)
		{
			if (queue == null || item == null || item.Done)
				return;

			var key = (queue.Actor.ActorID, item.Item);
			if (paused)
			{
				if (item.Paused)
					return;
				protectedProductionPauses.Add(key);
			}
			else
			{
				if (!protectedProductionPauses.Remove(key) || !item.Paused)
					return;
			}

			bot.QueueOrder(new Order("PauseProduction", queue.Actor, false)
			{
				TargetString = item.Item,
				ExtraData = paused ? 1u : 0u
			});
		}

		void ReleaseProtectedProductionPauses(IBot bot, ILookup<string, ProductionQueue> queuesByCategory)
		{
			if (protectedProductionPauses.Count == 0)
				return;

			foreach (var category in Info.UnitQueues)
				foreach (var queue in queuesByCategory[category].Where(IsUsableQueue))
				{
					var item = queue.AllQueued().FirstOrDefault();
					if (item == null)
						continue;
					QueueProductionPause(bot, queue, item, paused: false);
				}

			// Actors/items that disappeared while paused need no resume order.
			protectedProductionPauses.RemoveWhere(key =>
			{
				var actor = world.GetActorById(key.ActorId);
				return actor == null || !actor.IsInWorld || actor.IsDead;
			});
		}

		void RunProtectedGroundProduction(IBot bot, ILookup<string, ProductionQueue> queuesByCategory,
			int cash, int protectedReserve, bool allowInfantry, bool allowVehicle,
			bool openingInfantryPlan, bool openingCaptureOnly, string reserveLabel)
		{
			var available = Math.Max(0, cash - Math.Max(0, protectedReserve));
			var allowedCategories = new List<string>();
			if (allowInfantry)
				allowedCategories.AddRange(QueueDomains.Infantry);
			if (allowVehicle)
				allowedCategories.AddRange(QueueDomains.Vehicle);

			// Existing current production may continue only when the bank already covers both
			// the protected priority item and the complete remaining bill for that queue item.
			// Otherwise native PauseProduction holds it without cancelling/refunding anything.
			foreach (var category in allowedCategories)
				foreach (var queue in queuesByCategory[category].Where(IsUsableQueue).OrderByDescending(q => q.Actor.ActorID))
				{
					var item = queue.AllQueued().FirstOrDefault();
					if (item == null || item.Done ||
						(Info.PriorityRequestedUnitTypes.Contains(item.Item) && !Info.HarvesterTypes.Contains(item.Item)))
						continue;

					var canFundToCompletion = item.RemainingCost <= available;
					QueueProductionPause(bot, queue, item, !canFundToCompletion);
					if (canFundToCompletion)
						available -= Math.Max(0, item.RemainingCost);
				}

			// During MCV production only Infantry may receive new work. Keep the deterministic
			// opening E1/E3 plan and the explicit early E6 capture exception, but make both pay
			// entirely from cash above the MCV reserve.
			if (openingInfantryPlan)
			{
				if (allowInfantry)
				{
					foreach (var category in QueueDomains.Infantry)
						if (TryBuildAffordableSpecOpsRequest(bot, queuesByCategory, category, ref available, openingCaptureOnly))
							break;
					BuildOpeningInfantryWithBudget(bot, queuesByCategory, ref available);
				}
			}
			else
			{
				foreach (var category in allowedCategories)
					foreach (var queue in queuesByCategory[category].Where(IsFreeUsableQueue).OrderByDescending(q => q.Actor.ActorID))
					{
						if (TryBuildAffordableSpecOpsRequestForQueue(bot, queue, ref available, openingCaptureOnly))
							continue;

						var unit = ChooseRandomUnitToBuild(queue);
						if (unit == null)
							continue;
						var cost = Math.Max(0, queue.GetProductionCost(unit));
						if (cost > available)
							continue;

						bot.QueueOrder(Order.StartProduction(queue.Actor, unit.Name, 1));
						counters.Record(unit);
						available -= cost;
						FransBotLog.BotDebug(world,
							"{0}: {1} reserve permits {2} {3} on {4}; protected remaining cost {5}, post-order free budget {6}.",
							player, reserveLabel, category, unit.Name, queue.Actor, protectedReserve, available);
					}
			}

			if (lastCriticalPriorityReserveLogTick < 0 ||
				world.WorldTick - lastCriticalPriorityReserveLogTick >= Math.Max(1, Info.CriticalPriorityProductionLogInterval))
			{
				lastCriticalPriorityReserveLogTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: {1} protected-production budget: cash/resources {2}, exact remaining reserve {3}, safely allocatable Ground budget {4}.",
					player, reserveLabel, cash, protectedReserve, Math.Max(0, cash - protectedReserve));
			}
		}

		void BuildOpeningInfantryWithBudget(IBot bot, ILookup<string, ProductionQueue> queuesByCategory, ref int available)
		{
			var refineryCount = resourceControlStructures.Actors.Count(a =>
				a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null);

			if (refineryCount < 2)
			{
				if (openingRiflesStarted < Math.Max(0, Info.OpeningRifleTargetBeforeSecondRefinery))
					TryStartOpeningUnitWithBudget(bot, Info.OpeningRifleTypes, queuesByCategory, ref available,
						"early Double Ref rifle map control");
				return;
			}

			if (openingRocketsStarted < Math.Max(0, Info.OpeningRocketTarget))
				TryStartOpeningUnitWithBudget(bot, Info.OpeningRocketTypes, queuesByCategory, ref available,
					"three Double Ref rocket soldiers after PROC #2");
			else if (openingRiflesStarted < Math.Max(0, Info.OpeningRifleTarget))
				TryStartOpeningUnitWithBudget(bot, Info.OpeningRifleTypes, queuesByCategory, ref available,
					"complete Double Ref rifle map-control group");
		}

		bool TryStartOpeningUnitWithBudget(IBot bot, IEnumerable<string> candidateTypes,
			ILookup<string, ProductionQueue> queuesByCategory, ref int available, string reason)
		{
			foreach (var name in candidateTypes)
			{
				if (!world.Map.Rules.Actors.TryGetValue(name, out var actorInfo))
					continue;
				var buildableInfo = actorInfo.TraitInfoOrDefault<BuildableInfo>();
				if (buildableInfo == null)
					continue;

				foreach (var category in buildableInfo.Queue.Where(q => QueueDomains.Infantry.Contains(q)))
				{
					var queues = queuesByCategory[category].ToArray();
					var selected = queues.Where(IsFreeUsableQueue).FirstOrDefault(q => QueueCanBuild(q, name));
					if (selected == null)
						continue;
					var cost = Math.Max(0, selected.GetProductionCost(actorInfo));
					if (cost > available)
						return false;

					bot.QueueOrder(Order.StartProduction(selected.Actor, name, 1));
					available -= cost;
					RecordOpeningProduction(name, openingPlanUnit: true);
					FransBotLog.BotDebug(world,
						"{0}: protected opening budget starts {1} from {2}: {3}; free budget after full-cost guarantee {4}.",
						player, name, selected.Actor, reason, available);
					return true;
				}
			}
			return false;
		}

		bool TryBuildAffordableSpecOpsRequest(IBot bot, ILookup<string, ProductionQueue> queuesByCategory,
			string category, ref int available, bool openingCaptureOnly)
		{
			foreach (var queue in queuesByCategory[category].Where(IsFreeUsableQueue).OrderByDescending(q => q.Actor.ActorID))
				if (TryBuildAffordableSpecOpsRequestForQueue(bot, queue, ref available, openingCaptureOnly))
					return true;
			return false;
		}

		bool TryBuildAffordableSpecOpsRequestForQueue(IBot bot, ProductionQueue queue,
			ref int available, bool openingCaptureOnly)
		{
			if (!IsFreeUsableQueue(queue) || specOpsBuildRequests.Count == 0)
				return false;

			foreach (var request in specOpsBuildRequests.ToArray())
			{
				if (openingCaptureOnly && !Info.OpeningCaptureSpecialistTypes.Contains(request))
					continue;
				if (IsUnitDelayed(request) || !QueueCanBuild(queue, request) ||
					!world.Map.Rules.Actors.TryGetValue(request, out var actorInfo))
					continue;

				var cost = Math.Max(0, queue.GetProductionCost(actorInfo));
				if (cost > available)
					continue;

				bot.QueueOrder(Order.StartProduction(queue.Actor, request, 1));
				available -= cost;
				specOpsBuildRequests.Remove(request);
				RecordOpeningProduction(request);
				FransBotLog.BotDebug(world,
					"{0}: protected reserve grants SpecOps {1} in queue {2}; free budget after full-cost guarantee {3}.",
					player, request, queue.Actor, available);
				return true;
			}

			return false;
		}

		void BuildHumanDoubleRefOpeningPlan(IBot bot, ILookup<string, ProductionQueue> queuesByCategory)
		{
			var refineryCount = resourceControlStructures.Actors.Count(a =>
				a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null);

			// Before PROC #2, build a real map-control rifle body instead of letting
			// SpecOps requests consume nearly the whole infantry queue.
			if (refineryCount < 2)
			{
				if (openingRiflesStarted < Math.Max(0, Info.OpeningRifleTargetBeforeSecondRefinery))
					TryStartOpeningUnit(bot, Info.OpeningRifleTypes, queuesByCategory, "early Double Ref rifle map control");
			}
			else
			{
				// The tutorial's anti-vehicle insurance: exactly three rocket soldiers
				// become available because the second refinery is physically complete.
				if (openingRocketsStarted < Math.Max(0, Info.OpeningRocketTarget))
					TryStartOpeningUnit(bot, Info.OpeningRocketTypes, queuesByCategory, "three Double Ref rocket soldiers after PROC #2");
				else if (openingRiflesStarted < Math.Max(0, Info.OpeningRifleTarget))
					TryStartOpeningUnit(bot, Info.OpeningRifleTypes, queuesByCategory, "complete Double Ref rifle map-control group");
			}

			combatIntelService.EnsureCurrentSnapshot();
			var hasWarFactory = combatIntelService.OwnedActors.Any(a => Info.PreferredVehicleProducerTypes.Contains(a.Info.Name));
			if (!hasWarFactory)
				return;

			// A capture APC or other already-started configured light vehicle also satisfies
			// the tutorial's one-light-vehicle step; do not buy a redundant second map-control vehicle.
			if (!openingLightVehicleSatisfied)
			{
				if (HasOwnedOrQueuedOpeningLightVehicle())
					openingLightVehicleSatisfied = true;
				else if (TryStartOpeningUnit(bot, Info.OpeningLightVehicleTypes, queuesByCategory, "one Double Ref light map-control vehicle"))
					return;
				else if (TryStartCheapestOpeningVehicle(bot, queuesByCategory))
					return;
				else if (!AnyOpeningCandidateBuildable(Info.OpeningLightVehicleTypes, queuesByCategory))
				{
					// Some faction rosters field no light map-control unit at all (e.g. heavy-armor
					// lineups). The flag gates the opening MCV and the manual harvester below, so an
					// impossible demand must satisfy the step rather than deadlock the whole opening.
					openingLightVehicleSatisfied = true;
					FransBotLog.BotDebug(world,
						"{0}: Fransbot opening skips the light map-control vehicle: no configured type is producible on any owned queue for this faction.",
						player);
				}
			}

			if (openingLightVehicleSatisfied &&
				openingManualHarvestersStarted < Math.Max(0, Info.OpeningManualHarvesterTarget) &&
				!TryStartOpeningUnit(bot, Info.HarvesterTypes, queuesByCategory, "Fast Expansion single pre-MCV ore truck") &&
				!AnyOpeningCandidateBuildable(Info.HarvesterTypes, queuesByCategory))
			{
				openingManualHarvestersStarted = Math.Max(0, Info.OpeningManualHarvesterTarget);
				FransBotLog.BotDebug(world,
					"{0}: Fransbot opening skips the manual pre-MCV harvester: no configured harvester type is producible on any owned queue for this faction.",
					player);
			}
		}

		bool HasOwnedOrQueuedOpeningLightVehicle()
		{
			if (Info.OpeningLightVehicleTypes.Length == 0)
				return true;

			combatIntelService.EnsureCurrentSnapshot();
			if (combatIntelService.OwnedActors.Any(a => Info.OpeningLightVehicleTypes.Contains(a.Info.Name)))
				return true;

			return combatIntelService.OwnedActors
				.SelectMany(a => a.TraitsImplementing<ProductionQueue>())
				.Where(q => q.Enabled)
				.Any(q => q.AllQueued().Any(item => Info.OpeningLightVehicleTypes.Contains(item.Item)));
		}

		bool TryStartOpeningUnit(IBot bot, IEnumerable<string> candidateTypes,
			ILookup<string, ProductionQueue> queuesByCategory, string reason)
		{
			foreach (var name in candidateTypes)
			{
				if (!world.Map.Rules.Actors.TryGetValue(name, out var actorInfo))
					continue;

				var buildableInfo = actorInfo.TraitInfoOrDefault<BuildableInfo>();
				if (buildableInfo == null)
					continue;

				foreach (var category in buildableInfo.Queue)
				{
					var queues = queuesByCategory[category].ToArray();
					if (queues.Length == 0)
						continue;

					var preferred = PreferredCompatibleProducer(category, queues, name);
					var selected = preferred != null
						? (!preferred.AllQueued().Any()
							? preferred
							: PreferredFreeCompatibleProducer(category, queues, name, preferred))
						: queues.Where(IsFreeUsableQueue).FirstOrDefault(q => QueueCanBuild(q, name));

					if (selected == null)
						continue;

					bot.QueueOrder(Order.StartProduction(selected.Actor, name, 1));
					RecordOpeningProduction(name, openingPlanUnit: true);
					FransBotLog.BotDebug(world,
						"{0}: Fransbot opening starts {1} from {2}: {3}.",
						player, name, selected.Actor, reason);
					return true;
				}
			}

			return false;
		}

		// Factions without a configured light map-control vehicle (e.g. heavy-armor rosters)
		// substitute the cheapest armed vehicle their queues can currently produce — the step
		// exists to field one mobile combat unit early, so a substitute beats an idle queue.
		bool TryStartCheapestOpeningVehicle(IBot bot, ILookup<string, ProductionQueue> queuesByCategory)
		{
			ProductionQueue bestQueue = null;
			ActorInfo bestUnit = null;
			var bestCost = int.MaxValue;
			foreach (var category in QueueDomains.Vehicle)
				foreach (var queue in queuesByCategory[category].Where(IsFreeUsableQueue))
					foreach (var unit in queue.BuildableItems())
					{
						if (!FransActorClass.IsGround(unit) || !FransActorClass.IsArmed(unit) ||
							FransActorClass.IsHarvester(unit) || FransActorClass.IsTransport(unit) ||
							FransActorClass.IsMcv(unit) ||
							Info.DelayUntilOpeningMcvCompletedUnitTypes.Contains(unit.Name) ||
							Info.HardDisabledUnitTypes.Contains(unit.Name))
							continue;
						var cost = Math.Max(0, queue.GetProductionCost(unit));
						if (cost < bestCost)
						{
							bestCost = cost;
							bestQueue = queue;
							bestUnit = unit;
						}
					}

			if (bestQueue == null)
				return false;

			bot.QueueOrder(Order.StartProduction(bestQueue.Actor, bestUnit.Name, 1));
			openingLightVehicleSatisfied = true;
			RecordOpeningProduction(bestUnit.Name);
			FransBotLog.BotDebug(world,
				"{0}: Fransbot opening substitutes {1} for the light map-control vehicle step on {2}: no configured light type is buildable for this faction.",
				player, bestUnit.Name, bestQueue.Actor);
			return true;
		}

		bool AnyOpeningCandidateBuildable(IEnumerable<string> candidateTypes,
			ILookup<string, ProductionQueue> queuesByCategory)
		{
			foreach (var name in candidateTypes)
			{
				if (!world.Map.Rules.Actors.TryGetValue(name, out var actorInfo))
					continue;
				var buildableInfo = actorInfo.TraitInfoOrDefault<BuildableInfo>();
				if (buildableInfo == null)
					continue;

				// QueueCanBuild is the same prereq-resolved test TryStartOpeningUnit needs —
				// Producible would be wrong here because it is a pure queue-type match that
				// also lists cross-faction units a queue can never actually produce.
				foreach (var category in buildableInfo.Queue)
					if (queuesByCategory[category].Any(q => IsUsableQueue(q) && QueueCanBuild(q, name)))
						return true;
			}

			return false;
		}

		void RecordOpeningProduction(string unitName, bool openingPlanUnit = false)
		{
			if (openingBuildOrderService.OpeningComplete)
				return;

			if (Info.OpeningRifleTypes.Contains(unitName))
				openingRiflesStarted++;
			if (Info.OpeningRocketTypes.Contains(unitName))
				openingRocketsStarted++;
			if (Info.OpeningLightVehicleTypes.Contains(unitName))
				openingLightVehicleSatisfied = true;
			if (openingPlanUnit && Info.HarvesterTypes.Contains(unitName))
				openingManualHarvestersStarted++;
		}

		void UpdateEconomicStateTransition(FransEconomicState state)
		{
			if (state == previousEconomicState)
				return;
			var previous = previousEconomicState;
			previousEconomicState = state;
			FransBotLog.BotDebug(world,
				"{0}: UnitBuilder economy {1} -> {2}; Ground E1 target is {3}% of live Ground combat units and ARTY/V2RL combined target remains {4}% of live Ground combat vehicles.",
				player, previous, state, GroundE1DesiredShare(), Info.GroundVehicleArtilleryShare);

			if (state == FransEconomicState.Surplus)
			{
				FransBotLog.BotDebug(world, "{0}: UnitBuilder enters Surplus: queues were already saturated; Surplus now means producer throughput is the bottleneck, so BaseBuilder/economy may grow capacity while production continues.", player);
			}
			else if (previous == FransEconomicState.Surplus)
			{
				FransBotLog.BotDebug(world, "{0}: UnitBuilder leaves Surplus for {1}; existing military queues remain saturated whenever the normal cash floor is met, while producer growth and composition follow the lower economy state.", player, state);
			}
		}

		void BuildAllFreeMilitaryProduction(IBot bot,
			ILookup<string, ProductionQueue> queuesByCategory, bool ignorePositiveUnitLimits,
			bool pauseOrdinaryVehicleProduction, bool pauseOrdinaryInfantryProduction)
		{
			// Build the owned-unit snapshot once for this whole throughput-probe pass instead of
			// rescanning ActorIndex separately for every individual production queue.
			var allUnits = unitsToBuild.Actors.Where(a => !a.IsDead).ToArray();

			foreach (var category in Info.UnitQueues)
			{
				if (pauseOrdinaryVehicleProduction && QueueDomains.Vehicle.Contains(category))
					continue;
				if (pauseOrdinaryInfantryProduction && QueueDomains.Infantry.Contains(category))
					continue;

				foreach (var queue in queuesByCategory[category]
					.Where(IsFreeUsableQueue)
					.OrderByDescending(q => q.Actor.ActorID))
				{
					// Mailbox check happens between every queue fill. A requested E6/Tanya/Mechanic/etc.
					// therefore gets first refusal on a compatible free queue instead of waiting behind
					// a full saturation pass. Incompatible requests never idle this queue.
					if (TryBuildSpecOpsRequestForQueue(bot, queue, openingCaptureOnly: false))
						continue;

					if (seaProductionSuspendedForEconomy && QueueDomains.Naval.Contains(category))
						continue;
					if (airProductionSuspendedForEconomy && QueueDomains.Air.Contains(category))
						continue;

					var unit = ChooseRandomUnitToBuild(queue, allUnits, ignorePositiveUnitLimits);
					if (unit == null)
						continue;

					bot.QueueOrder(Order.StartProduction(queue.Actor, unit.Name, 1));
					counters.Record(unit);
					var capMode = !ignorePositiveUnitLimits ? "hard" : "soft";
					FransBotLog.BotDebug(world, "{0}: Production saturation fills {1} queue {2} with {3}; positive unit caps are {4}.",
						player, category, queue.Actor, unit.Name, capMode);
				}
			}
		}

		void IFransSpecOpsProductionMailbox.RequestSpecOpsProduction(IBot bot, string requestedActor)
		{
			if (string.IsNullOrWhiteSpace(requestedActor) ||
				Info.HardDisabledUnitTypes.Contains(requestedActor) ||
				!world.Map.Rules.Actors.ContainsKey(requestedActor))
				return;

			// Keep a legitimate request even when its UnitDelay has not opened yet. The mailbox is
			// strategic demand memory: UnitBuilder will grant the first compatible queue after the
			// delay/tech gate opens instead of forcing SpecOps to rediscover the same opportunity.
			specOpsBuildRequests.Add(requestedActor);
			FransBotLog.BotDebug(world, "{0}: SPECOPS MAILBOX accepts production request for {1}; pending mailbox count for type is now {2}.",
				player, requestedActor, specOpsBuildRequests.Count(r => r == requestedActor));
		}

		int IFransSpecOpsProductionMailbox.RequestedSpecOpsProductionCount(IBot bot, string requestedActor) =>
			specOpsBuildRequests.Count(r => r == requestedActor);

		bool TryBuildOneSpecOpsRequest(IBot bot, ILookup<string, ProductionQueue> queuesByCategory, bool openingCaptureOnly = false)
		{
			foreach (var category in Info.UnitQueues)
				foreach (var queue in queuesByCategory[category].Where(IsFreeUsableQueue).OrderByDescending(q => q.Actor.ActorID))
					if (TryBuildSpecOpsRequestForQueue(bot, queue, openingCaptureOnly))
						return true;

			return false;
		}

		bool TryBuildSpecOpsRequestForQueue(IBot bot, ProductionQueue queue, bool openingCaptureOnly = false)
		{
			if (!IsFreeUsableQueue(queue) || specOpsBuildRequests.Count == 0)
				return false;

			foreach (var request in specOpsBuildRequests.ToArray())
			{
				if (openingCaptureOnly && !Info.OpeningCaptureSpecialistTypes.Contains(request))
					continue;

				if (IsUnitDelayed(request) || !QueueCanBuild(queue, request))
					continue;

				bot.QueueOrder(Order.StartProduction(queue.Actor, request, 1));
				specOpsBuildRequests.Remove(request);
				RecordOpeningProduction(request);
				FransBotLog.BotDebug(world,
					"{0}: UNITBUILDER SPECOPS SLOT granted: {1} starts in queue {2}; {3} mailbox request(s) remain.",
					player, request, queue.Actor, specOpsBuildRequests.Count);
				return true;
			}

			return false;
		}

		void UpdateEconomicEmergencyProduction(IBot bot, ILookup<string, ProductionQueue> queuesByCategory, int cash)
		{
			if (!seaProductionSuspendedForEconomy && cash < Info.EconomicEmergencySeaSuspendCash)
			{
				seaProductionSuspendedForEconomy = true;
				var cancelled = CancelQueuedOrdinaryDomainProduction(bot, queuesByCategory, QueueDomains.Naval.ToArray());
				FransBotLog.BotDebug(world,
					"{0}: ECONOMIC EMERGENCY: Sea ordinary production suspends FIRST at cash/resources {1} < {2}; cancelled {3} queued ordinary Sea combat unit(s). Demand-only transport requests are untouched.",
					player, cash, Info.EconomicEmergencySeaSuspendCash, cancelled);
			}

			if (!airProductionSuspendedForEconomy && cash < Info.EconomicEmergencyAirSuspendCash)
			{
				airProductionSuspendedForEconomy = true;
				var cancelled = CancelQueuedOrdinaryAirAboveReserve(bot, queuesByCategory);
				FransBotLog.BotDebug(world,
					"{0}: ECONOMIC EMERGENCY: Air ordinary production now also suspends at cash/resources {1} < {2}; cancelled {3} queued Air combat unit(s) above the defensive reserve of {4}. Ground/economy and explicit specialist debt remain active.",
					player, cash, Info.EconomicEmergencyAirSuspendCash, cancelled, Info.EconomicEmergencyMinimumAirCombatReserve);
			}

			if (airProductionSuspendedForEconomy && cash >= Info.EconomicEmergencyAirResumeCash)
			{
				airProductionSuspendedForEconomy = false;
				FransBotLog.BotDebug(world, "{0}: ECONOMIC RECOVERY: Air ordinary production resumes first at cash/resources {1} >= {2}.",
					player, cash, Info.EconomicEmergencyAirResumeCash);
			}

			if (seaProductionSuspendedForEconomy && cash >= Info.EconomicEmergencySeaResumeCash)
			{
				seaProductionSuspendedForEconomy = false;
				FransBotLog.BotDebug(world, "{0}: ECONOMIC RECOVERY: Sea ordinary production resumes last at cash/resources {1} >= {2}.",
					player, cash, Info.EconomicEmergencySeaResumeCash);
			}

			if ((seaProductionSuspendedForEconomy || airProductionSuspendedForEconomy) &&
				(lastEconomicEmergencyLogTick < 0 || world.WorldTick - lastEconomicEmergencyLogTick >= Info.EconomicEmergencyLogInterval))
			{
				lastEconomicEmergencyLogTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: ECONOMIC EMERGENCY HOLD: cash/resources {1}; Sea suspended={2}, Air suspended={3}. Defensive Air reserve {4}, Air resume {5}, Sea resume {6}.",
					player, cash, seaProductionSuspendedForEconomy, airProductionSuspendedForEconomy,
					Info.EconomicEmergencyMinimumAirCombatReserve, Info.EconomicEmergencyAirResumeCash, Info.EconomicEmergencySeaResumeCash);
			}
		}

		bool IsConfiguredAirCombatType(string actorType) => !string.IsNullOrEmpty(actorType) &&
			(Info.AirFixedWingPrimaryTypes.Contains(actorType) || Info.AirFixedWingSecondaryTypes.Contains(actorType) ||
			Info.AirRotaryWingPrimaryTypes.Contains(actorType) || Info.AirRotaryWingSecondaryTypes.Contains(actorType));

		int CountLiveAirCombatUnits()
		{
			combatIntelService.EnsureCurrentSnapshot();
			return combatIntelService.OwnedActors.Count(a => a != null && a.IsInWorld && !a.IsDead && IsConfiguredAirCombatType(a.Info.Name));
		}

		int CountQueuedAirCombatUnits(ILookup<string, ProductionQueue> queuesByCategory) =>
			QueueDomains.Air
				.SelectMany(category => queuesByCategory[category])
				.Where(IsUsableQueue)
				.SelectMany(queue => queue.AllQueued())
				.Count(item => IsConfiguredAirCombatType(item.Item));

		bool TryBuildPioneerAirScout(IBot bot, ILookup<string, ProductionQueue> queuesByCategory)
		{
			if (expansionStateService?.PioneerAirScoutDemandActive != true)
				return false;

			// This is a zero-Air bootstrap only. Once any combat aircraft exists or is queued,
			// normal Commander ownership decides whether it performs PIONEER RECON.
			var live = CountLiveAirCombatUnits();
			var queued = CountQueuedAirCombatUnits(queuesByCategory);
			if (live + queued > 0)
				return false;

			var preferredTypes = Info.AirFixedWingPrimaryTypes
				.Concat(Info.AirRotaryWingPrimaryTypes)
				.Concat(Info.AirFixedWingSecondaryTypes)
				.Concat(Info.AirRotaryWingSecondaryTypes)
				.Distinct()
				.ToArray();

			foreach (var actorType in preferredTypes)
				foreach (var category in QueueDomains.Air)
					foreach (var queue in queuesByCategory[category].Where(IsFreeUsableQueue).OrderByDescending(q => q.Actor.ActorID))
					{
						if (IsUnitDelayed(actorType) || !QueueCanBuild(queue, actorType) ||
							!world.Map.Rules.Actors.TryGetValue(actorType, out var actorInfo) || !HasAdequateAirUnitReloadBuildings(actorInfo))
							continue;

						bot.QueueOrder(Order.StartProduction(queue.Actor, actorType, 1));
						FransBotLog.BotDebug(world,
							"{0}: PIONEER AIR-SCOUT DEMAND starts one {1} in {2}: active expansion objective is on another Ground landmass, exact RECON is required, and live+queued combat Air was 0. Normal Air saturation remains unchanged.",
							player, actorType, queue.Actor);
						return true;
					}

			return false;
		}

		bool TryBuildEconomicEmergencyAirReserve(IBot bot, ILookup<string, ProductionQueue> queuesByCategory)
		{
			if (!airProductionSuspendedForEconomy)
				return false;

			var live = CountLiveAirCombatUnits();
			var queued = CountQueuedAirCombatUnits(queuesByCategory);
			if (live + queued >= Info.EconomicEmergencyMinimumAirCombatReserve)
				return false;

			var allUnits = unitsToBuild.Actors.Where(a => !a.IsDead).ToArray();
			foreach (var category in QueueDomains.Air)
				foreach (var queue in queuesByCategory[category].Where(IsFreeUsableQueue).OrderByDescending(q => q.Actor.ActorID))
				{
					var unit = ChooseRandomUnitToBuild(queue, allUnits, Info.PositiveCombatUnitLimitsAreSoft);
					if (unit == null || !IsConfiguredAirCombatType(unit.Name))
						continue;

					bot.QueueOrder(Order.StartProduction(queue.Actor, unit.Name, 1));
					counters.Record(unit);
					FransBotLog.BotDebug(world,
						"{0}: ECONOMIC DEFENSIVE AIR RESERVE: suspended Air domain starts {1} in {2}; live {3}, queued {4}, reserve target {5}.",
						player, unit.Name, queue.Actor, live, queued, Info.EconomicEmergencyMinimumAirCombatReserve);
					return true;
				}

			return false;
		}

		int CancelQueuedOrdinaryAirAboveReserve(IBot bot, ILookup<string, ProductionQueue> queuesByCategory)
		{
			var live = CountLiveAirCombatUnits();
			var preserveQueued = Math.Max(0, Info.EconomicEmergencyMinimumAirCombatReserve - live);
			var queued = QueueDomains.Air
				.SelectMany(category => queuesByCategory[category])
				.Where(IsUsableQueue)
				.OrderBy(q => q.Actor.ActorID)
				.SelectMany(queue => queue.AllQueued().Where(item => IsConfiguredAirCombatType(item.Item)).Select(item => (Queue: queue, Item: item)))
				.ToArray();

			var cancelled = 0;
			foreach (var entry in queued.Skip(preserveQueued))
			{
				bot.QueueOrder(Order.CancelProduction(entry.Queue.Actor, entry.Item.Item, 1));
				cancelled++;
			}
			return cancelled;
		}

		int CancelQueuedOrdinaryDomainProduction(IBot bot, ILookup<string, ProductionQueue> queuesByCategory, params string[] categories)
		{
			var cancelled = 0;
			foreach (var category in categories)
				foreach (var queue in queuesByCategory[category].Where(IsUsableQueue))
					foreach (var item in queue.AllQueued().ToArray())
					{
						// Only ordinary UnitBuilder composition is sacrificed. LST/TRAN and other
						// demand-only logistics are not UnitsToBuild entries and therefore survive.
						if (!Info.UnitsToBuild.TryGetValue(item.Item, out var ordinaryWeight) || ordinaryWeight <= 0)
							continue;

						bot.QueueOrder(Order.CancelProduction(queue.Actor, item.Item, 1));
						cancelled++;
					}

			return cancelled;
		}

		// Only true strategic vehicles may hold the critical reserve. Cheap infantry/engineers in
		// PriorityRequestedUnitTypes previously froze all spending behind the flat cash reserve for
		// their entire queue lifetime, which starved harvester and army growth into a stall.
		bool IsCriticalPriorityUnit(string unitName)
		{
			if (unitName == null || !Info.PriorityRequestedUnitTypes.Contains(unitName) || Info.HarvesterTypes.Contains(unitName))
				return false;
			return world.Map.Rules.Actors.TryGetValue(unitName, out var actorInfo) && FransActorClass.IsMcv(actorInfo);
		}

		bool HasCriticalPriorityProduction(ILookup<string, ProductionQueue> queuesByCategory)
		{
			foreach (var category in Info.UnitQueues)
				foreach (var queue in queuesByCategory[category])
					if (queue.Enabled && queue.AllQueued().Any(item => IsCriticalPriorityUnit(item.Item)))
						return true;
			return false;
		}

		bool ShouldProtectCriticalPriorityProduction(ILookup<string, ProductionQueue> queuesByCategory, int cash)
		{
			if (Info.CriticalPriorityProductionReserveCash <= 0 || cash >= Info.CriticalPriorityProductionReserveCash)
				return false;

			var pendingMcvRequest = expansionStateService?.CriticalMcvProductionDemandActive == true;
			var physicallyQueuedPriority = HasCriticalPriorityProduction(queuesByCategory);
			if (!pendingMcvRequest && !physicallyQueuedPriority)
				return false;

			if (lastCriticalPriorityReserveLogTick < 0 ||
				world.WorldTick - lastCriticalPriorityReserveLogTick >= Math.Max(1, Info.CriticalPriorityProductionLogInterval))
			{
				lastCriticalPriorityReserveLogTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: critical priority production reserve holds new UnitBuilder spending at cash/resources {1} < {2}; {3}, so existing/native MCV production receives income before new military saturation orders.",
					player, cash, Info.CriticalPriorityProductionReserveCash,
					pendingMcvRequest ? "ExpansionManager has an accepted MCV request waiting for its native queue" : "an MCV/priority strategic unit is physically queued");
			}
			return true;
		}

		int RequestPriority(string requestedActor)
		{
			// Expansion MCV is the highest Vehicle-queue obligation. The opening explicitly
			// requires MCV "as soon as possible" after FIX, and mine-economy catch-up must
			// never postpone the first real expansion.
			if (Info.PriorityRequestedUnitTypes.Contains(requestedActor) &&
				!Info.HarvesterTypes.Contains(requestedActor))
				return 0;

			// Mine economy is second: still important, but filled progressively so WEAP also
			// has room for combat vehicles between economy requests.
			if (Info.HarvesterTypes.Contains(requestedActor))
				return 1;

			return 2;
		}


		void IBotRequestUnitProduction.RequestUnitProduction(IBot bot, string requestedActor)
		{

			// External resource-economy requests remain valid in every economic state, including Surplus.
			// Post-opening HARV demand comes from FransHarvester; UnitBuilder only executes the request.

			// MCV/HARV are strategic single-debt requests. Never stack another copy while one
			// is already requested or physically present in an enabled production queue.
			if (Info.PriorityRequestedUnitTypes.Contains(requestedActor))
			{
				if (queuedBuildRequests.Contains(requestedActor))
					return;

				combatIntelService.EnsureCurrentSnapshot();
				var alreadyInProduction = combatIntelService.OwnedActors
					.SelectMany(a => a.TraitsImplementing<ProductionQueue>())
					.Any(q => q.Enabled && q.AllQueued().Any(item => item.Item == requestedActor));

				if (alreadyInProduction)
					return;
			}

			queuedBuildRequests.Add(requestedActor);
		}

		int IBotRequestUnitProduction.RequestedProductionCount(IBot bot, string requestedActor)
		{
			return queuedBuildRequests.Count(r => r == requestedActor);
		}

		void BuildRandomUnit(IBot bot, string category, ProductionQueue[] queues)
		{
			if (Info.UnitsToBuild.Count == 0)
				return;

			var preferred = PreferredCompatibleProducer(category, queues, null);
			if (preferred != null)
			{
				// Infantry and vehicles both use strategic geography when available.
				// Never stall production solely because the best-positioned producer is busy.
				var selected = !preferred.AllQueued().Any()
					? preferred
					: PreferredFreeCompatibleProducer(category, queues, null, preferred);

				if (selected != null)
				{
					var unit = ChooseRandomUnitToBuild(selected);
					if (unit != null)
					{
						bot.QueueOrder(Order.StartProduction(selected.Actor, unit.Name, 1));
						counters.Record(unit);
						FransBotLog.BotDebug(world, "{0}: {1} producer {2} is building {3}{4}.",
							player, category, selected.Actor, unit.Name,
							selected == preferred ? " from the preferred producer" : " using compatible-producer fallback");
						return;
					}
				}
			}

			// Non-ground categories, or ground categories with no configured preferred producer,
			// retain the stock-like first-free behavior.
			var queue = queues.FirstOrDefault(IsFreeUsableQueue);
			if (queue == null)
				return;

			var fallbackUnit = ChooseRandomUnitToBuild(queue);
			if (fallbackUnit == null)
				return;

			bot.QueueOrder(Order.StartProduction(queue.Actor, fallbackUnit.Name, 1));
			counters.Record(fallbackUnit);
		}

		bool TryBuildRequestedUnit(IBot bot, string name, ILookup<string, ProductionQueue> queuesByCategory)
		{
			// UnitDelays are absolute: they apply to externally requested production as
			// well as weighted/random production. Keep a delayed request queued until its
			// world-tick gate has opened instead of bypassing the configured delay.
			if (IsUnitDelayed(name))
				return false;

			if (!world.Map.Rules.Actors.TryGetValue(name, out var actorInfo))
				return true;

			var buildableInfo = actorInfo.TraitInfoOrDefault<BuildableInfo>();
			if (buildableInfo == null)
				return true;

			foreach (var category in buildableInfo.Queue)
			{
				var queues = queuesByCategory[category].ToArray();
				if (queues.Length == 0)
					continue;

				var preferred = PreferredCompatibleProducer(category, queues, name);
				if (preferred != null)
				{
					var selected = !preferred.AllQueued().Any()
						? preferred
						: PreferredFreeCompatibleProducer(category, queues, name, preferred);

					if (selected != null)
					{
						bot.QueueOrder(Order.StartProduction(selected.Actor, name, 1));
						RecordOpeningProduction(name);
						if (!openingBuildOrderService.OpeningComplete && Info.PriorityRequestedUnitTypes.Contains(name) && !Info.HarvesterTypes.Contains(name))
						{
							openingMcvProductionStarted = true;
							FransBotLog.BotDebug(world,
								"{0}: OPENING MCV PRODUCTION START accepted by UnitBuilder on producer {1} at WT {2}; exact RemainingCost protection remains active until the MCV is physically complete.",
								player, selected.Actor, world.WorldTick);
						}
						FransBotLog.BotDebug(world, "{0}: {1} producer {2} is building requested unit {3}{4} at world tick {5}.",
							player, category, selected.Actor, name,
							selected == preferred ? " from the preferred producer" : " using compatible-producer fallback",
							world.WorldTick);
						return true;
					}

					// All compatible ground producers are currently occupied: retain the request.
					return false;
				}

				var fallback = queues
					.Where(IsFreeUsableQueue)
					.FirstOrDefault(q => QueueCanBuild(q, name));

				if (fallback == null)
					continue;

				bot.QueueOrder(Order.StartProduction(fallback.Actor, name, 1));
				RecordOpeningProduction(name);
				if (!openingBuildOrderService.OpeningComplete && Info.PriorityRequestedUnitTypes.Contains(name) && !Info.HarvesterTypes.Contains(name))
				{
					openingMcvProductionStarted = true;
					FransBotLog.BotDebug(world,
						"{0}: OPENING MCV PRODUCTION START accepted by UnitBuilder on fallback producer {1} at WT {2}; exact RemainingCost protection remains active until the MCV is physically complete.",
						player, fallback.Actor, world.WorldTick);
				}
				FransBotLog.BotDebug(world, "{0}: fallback producer {1} is building requested unit {2} at world tick {3}.",
					player, fallback.Actor, name, world.WorldTick);
				return true;
			}

			// No compatible producer exists yet. Keep the request so a newly built producer
			// can satisfy it later.
			return false;
		}

		ProductionQueue PreferredCompatibleProducer(string category, IEnumerable<ProductionQueue> queues, string requestedUnit)
		{
			var producerTypes = QueueDomains.Vehicle.Contains(category) ? Info.PreferredVehicleProducerTypes
				: QueueDomains.Infantry.Contains(category) ? Info.PreferredInfantryProducerTypes
				: null;

			if (producerTypes == null || producerTypes.Count == 0)
				return null;

			var candidates = queues
				.Where(IsUsableQueue)
				.Where(q => producerTypes.Contains(q.Actor.Info.Name))
				.Where(q => requestedUnit == null || QueueCanBuild(q, requestedUnit));

			return OrderGroundProducersByPreference(category, candidates).FirstOrDefault();
		}

		ProductionQueue PreferredFreeCompatibleProducer(string category, IEnumerable<ProductionQueue> queues,
			string requestedUnit, ProductionQueue exclude)
		{
			var producerTypes = QueueDomains.Vehicle.Contains(category) ? Info.PreferredVehicleProducerTypes
				: QueueDomains.Infantry.Contains(category) ? Info.PreferredInfantryProducerTypes
				: null;

			if (producerTypes == null || producerTypes.Count == 0)
				return null;

			var candidates = queues
				.Where(q => q != exclude)
				.Where(IsFreeUsableQueue)
				.Where(q => producerTypes.Contains(q.Actor.Info.Name))
				.Where(q => requestedUnit == null || QueueCanBuild(q, requestedUnit));

			return OrderGroundProducersByPreference(category, candidates).FirstOrDefault();
		}

		IEnumerable<ProductionQueue> OrderGroundProducersByPreference(string category, IEnumerable<ProductionQueue> candidates)
		{
			var available = candidates.ToArray();
			var useCommanderDemand = (QueueDomains.Infantry.Contains(category) && Info.PreferStrategicInfantryProducer) ||
				(QueueDomains.Vehicle.Contains(category) && Info.PreferStrategicVehicleProducer);
			if (useCommanderDemand && TryGetGroundProductionDemandPoint(out var demand))
				return available
					.OrderBy(q => (q.Actor.Location - demand).LengthSquared)
					.ThenByDescending(q => q.Actor.ActorID);

			// Producer choice is logistics, not a second combat planner. With no commander demand,
			// keep the deterministic newest-first fallback. The produced unit's MOVE is where RiskModel applies.
			return available.OrderByDescending(q => q.Actor.ActorID);
		}

		bool TryGetGroundProductionDemandPoint(out CPos demand)
		{
			if (groundCommanderService != null &&
				groundCommanderService.TryGetGroundDemandPoint(out demand, out _, out _))
				return true;

			if (openingBuildOrderService.StrategicForwardTarget is CPos front)
			{
				demand = front;
				return true;
			}

			demand = default;
			return false;
		}

		static bool IsUsableQueue(ProductionQueue queue)
		{
			return queue.Enabled && queue.Actor.IsInWorld && !queue.Actor.IsDead;
		}

		static bool IsFreeUsableQueue(ProductionQueue queue)
		{
			return IsUsableQueue(queue) && !queue.AllQueued().Any();
		}

		static bool QueueCanBuild(ProductionQueue queue, string unitName)
		{
			return queue.BuildableItems().Any(item => item.Name == unitName);
		}

		ActorInfo ChooseRandomUnitToBuild(ProductionQueue queue)
		{
			return ChooseRandomUnitToBuild(queue,
				unitsToBuild.Actors.Where(a => !a.IsDead).ToArray(),
				ignorePositiveUnitLimits: false);
		}

		int GroundE1DesiredShare()
		{
			// E1 remains the Ground cost-efficiency backbone, but its explicit target
			// is now a percentage of the Ground Commander's own live combat pool only.
			// Struggling intentionally stays at the Growing target until separately tuned.
			return economicSaturationService.State switch
			{
				FransEconomicState.Prosperous => 45,
				FransEconomicState.Surplus => 35,
				_ => 55
			};
		}

		int CompositionPopulationForUnit(string unitName, Actor[] allUnits)
		{
			// Commander-domain composition uses Commander-owned classifiers rather than one global
			// unit denominator. E1 is measured against all live Ground combat units. ARTY/V2RL are
			// one combined pool measured only against live Ground combat vehicles. Air, Sea, infantry
			// and specialist/logistics actors therefore cannot dilute the artillery target.
			if (groundCommanderService != null)
			{
				if (Info.OpeningRifleTypes.Contains(unitName))
					return allUnits.Count(groundCommanderService.IsGroundCombatUnitOwned);

				if (Info.GroundVehicleArtilleryTypes.Contains(unitName))
					return allUnits.Count(groundCommanderService.IsGroundVehicleCombatUnitOwned);
			}

			return allUnits.Length;
		}

		int CompositionCountForUnit(string unitName, Actor[] allUnits)
		{
			if (Info.GroundVehicleArtilleryTypes.Contains(unitName))
				return allUnits.Count(a => Info.GroundVehicleArtilleryTypes.Contains(a.Info.Name));

			return allUnits.Count(a => a.Info.Name == unitName);
		}

		bool IsRatioCandidateEligible(ActorInfo unit, Actor[] allUnits, bool ignorePositiveUnitLimits)
		{
			if (unit == null || !Info.UnitsToBuild.ContainsKey(unit.Name) || IsUnitDelayed(unit.Name))
				return false;

			if (Info.ProsperousUnitTypes.Contains(unit.Name) && !economicSaturationService.IsProsperousOrBetter)
				return false;

			var unitCount = allUnits.Count(a => a.Info.Name == unit.Name);
			if (Info.UnitLimits != null && Info.UnitLimits.TryGetValue(unit.Name, out var count))
			{
				if (count == 0)
					return false;
				if (!ignorePositiveUnitLimits && unitCount >= count)
					return false;
			}

			return HasAdequateAirUnitReloadBuildings(unit);
		}

		ActorInfo ChooseWeightedPairRatioUnit(ActorInfo[] buildableThings, Actor[] allUnits,
			bool ignorePositiveUnitLimits, FrozenSet<string> primaryTypes, int primaryWeight,
			FrozenSet<string> secondaryTypes, int secondaryWeight)
		{
			if (primaryWeight <= 0 || secondaryWeight <= 0)
				return null;

			var primary = buildableThings
				.Where(a => primaryTypes.Contains(a.Name))
				.Where(a => IsRatioCandidateEligible(a, allUnits, ignorePositiveUnitLimits))
				.OrderBy(a => a.Name)
				.ToArray();
			var secondary = buildableThings
				.Where(a => secondaryTypes.Contains(a.Name))
				.Where(a => IsRatioCandidateEligible(a, allUnits, ignorePositiveUnitLimits))
				.OrderBy(a => a.Name)
				.ToArray();
			if (primary.Length == 0 || secondary.Length == 0)
				return null;

			var primaryCount = allUnits.Count(a => primaryTypes.Contains(a.Info.Name));
			var secondaryCount = allUnits.Count(a => secondaryTypes.Contains(a.Info.Name));
			var primaryProjectedError = Math.Abs((long)(primaryCount + 1) * secondaryWeight - (long)secondaryCount * primaryWeight);
			var secondaryProjectedError = Math.Abs((long)primaryCount * secondaryWeight - (long)(secondaryCount + 1) * primaryWeight);
			var selectedFamily = primaryProjectedError <= secondaryProjectedError ? primary : secondary;

			return selectedFamily
				.OrderBy(a => allUnits.Count(u => u.Info.Name == a.Name))
				.ThenBy(a => a.Name)
				.FirstOrDefault();
		}

		ActorInfo ChooseEqualRatioSeaUnit(ActorInfo[] buildableThings, Actor[] allUnits,
			bool ignorePositiveUnitLimits, FrozenSet<string> seaTypes)
		{
			var eligible = buildableThings
				.Where(a => seaTypes.Contains(a.Name))
				.Where(a => IsRatioCandidateEligible(a, allUnits, ignorePositiveUnitLimits))
				.OrderBy(a => a.Name)
				.ToArray();
			if (eligible.Length < 2)
				return null;

			return eligible
				.OrderBy(a => allUnits.Count(u => u.Info.Name == a.Name))
				.ThenBy(a => a.Name)
				.FirstOrDefault();
		}

		ActorInfo ChooseConfiguredDomainRatioUnit(ActorInfo[] buildableThings, Actor[] allUnits,
			bool ignorePositiveUnitLimits)
		{
			var ratio = ChooseWeightedPairRatioUnit(buildableThings, allUnits, ignorePositiveUnitLimits,
				Info.AirFixedWingPrimaryTypes, Info.AirFixedWingPrimaryWeight,
				Info.AirFixedWingSecondaryTypes, Info.AirFixedWingSecondaryWeight);
			if (ratio != null)
				return ratio;

			ratio = ChooseWeightedPairRatioUnit(buildableThings, allUnits, ignorePositiveUnitLimits,
				Info.AirRotaryWingPrimaryTypes, Info.AirRotaryWingPrimaryWeight,
				Info.AirRotaryWingSecondaryTypes, Info.AirRotaryWingSecondaryWeight);
			if (ratio != null)
				return ratio;

			ratio = ChooseEqualRatioSeaUnit(buildableThings, allUnits, ignorePositiveUnitLimits, Info.AlliedSeaCombatTypes);
			if (ratio != null)
				return ratio;

			return ChooseEqualRatioSeaUnit(buildableThings, allUnits, ignorePositiveUnitLimits, Info.SovietSeaCombatTypes);
		}

		ActorInfo ChooseRandomUnitToBuild(ProductionQueue queue, Actor[] allUnits,
			bool ignorePositiveUnitLimits)
		{
			var groundVehiclePopulation = groundCommanderService != null
				? allUnits.Count(groundCommanderService.IsGroundVehicleCombatUnitOwned)
				: 0;
			var groundArtilleryPopulation = allUnits.Count(a => Info.GroundVehicleArtilleryTypes.Contains(a.Info.Name));
			var artilleryUnderTarget = Info.GroundVehicleArtilleryTypes.Count > 0 &&
				(groundVehiclePopulation == 0 ||
				groundArtilleryPopulation * 100 < Info.GroundVehicleArtilleryShare * groundVehiclePopulation);

			// When Ground artillery is below its combined target, inspect ARTY/V2RL first so another
			// unrelated under-target vehicle cannot win merely because Shuffle happened to list it
			// first. Once the 33% pool is satisfied, ARTY/V2RL are held as queue-saturation fallback
			// rather than continuing to inflate beyond the requested combined vehicle share.
			var buildableThings = queue.BuildableItems().Shuffle(world.LocalRandom)
				.OrderByDescending(a => artilleryUnderTarget && Info.GroundVehicleArtilleryTypes.Contains(a.Name))
				.ToArray();
			if (buildableThings.Length == 0)
				return null;

			// Air and Sea composition use explicit Commander-domain pools before the
			// generic percentage chooser. This keeps Yak:MiG and MH60:Longbow near 2:1, and
			// balances buildable combat ships 1:1:1 or 1:1, without ever idling a usable queue
			// when one member is tech/economy/rearm gated.
			var domainRatioUnit = ChooseConfiguredDomainRatioUnit(buildableThings, allUnits, ignorePositiveUnitLimits);
			if (domainRatioUnit != null)
				return domainRatioUnit;

			var counterUnit = ChooseAdaptiveCounter(buildableThings, allUnits);
			if (counterUnit != null)
				return counterUnit;

			ActorInfo desiredUnit = null;
			ActorInfo artillerySaturationFallback = null;
			var desiredError = int.MaxValue;

			foreach (var unit in buildableThings)
			{
				if (Info.ProsperousUnitTypes.Contains(unit.Name) && !economicSaturationService.IsProsperousOrBetter)
					continue;
				if (!Info.UnitsToBuild.TryGetValue(unit.Name, out var share) || IsUnitDelayed(unit.Name))
					continue;

				if (Info.OpeningRifleTypes.Contains(unit.Name))
					share = GroundE1DesiredShare();
				else if (Info.GroundVehicleArtilleryTypes.Contains(unit.Name))
					share = Info.GroundVehicleArtilleryShare;

				var unitCount = allUnits.Count(a => a.Info.Name == unit.Name);
				if (Info.UnitLimits != null && Info.UnitLimits.TryGetValue(unit.Name, out var count))
				{
					// Zero is ALWAYS a hard disable (e.g. random harvesters/specials).
					if (count == 0)
						continue;

					// Positive limits are composition targets, not a reason to idle an otherwise
					// usable military queue. Zero remains a hard disable. Demand-only logistics
					// such as LST are outside ordinary composition and arrive only through requests.
					if (!ignorePositiveUnitLimits && unitCount >= count)
						continue;
				}

				if (Info.GroundVehicleArtilleryTypes.Contains(unit.Name) && !artilleryUnderTarget)
				{
					artillerySaturationFallback ??= unit;
					continue;
				}

				var compositionPopulation = CompositionPopulationForUnit(unit.Name, allUnits);
				var compositionCount = CompositionCountForUnit(unit.Name, allUnits);
				var error = compositionPopulation > 0 ? compositionCount * 100 / compositionPopulation - share : -1;
				if (error < 0)
					return HasAdequateAirUnitReloadBuildings(unit) ? unit : null;

				if (error < desiredError)
				{
					desiredError = error;
					desiredUnit = unit;
				}
			}

			if (desiredUnit != null && HasAdequateAirUnitReloadBuildings(desiredUnit))
				return desiredUnit;

			// Never violate queue saturation solely to preserve an exact composition percentage.
			// If ARTY/V2RL is the only legal ordinary choice left, keep the Vehicle queue working.
			return artillerySaturationFallback != null && HasAdequateAirUnitReloadBuildings(artillerySaturationFallback)
				? artillerySaturationFallback
				: null;
		}

		// #245/CA parity on the fog-honest feed: below the weight cap, pick the best counter
		// to the enemy army CombatIntel has SEEN among this queue's configured combat units.
		ActorInfo ChooseAdaptiveCounter(ActorInfo[] buildableThings, Actor[] allUnits)
		{
			counters.LastChoiceAdaptive = false;
			if (!AdaptiveCounterProduction.CounterPickAllowed(counters.AdaptiveSelections, counters.TotalSelections, Info.AdaptiveCounterWeight))
				return null;

			var owned = allUnits.Where(a => !a.IsDead).GroupBy(a => a.Info.Name).ToDictionary(g => g.Key, g => g.Count());
			var choice = counters.Choose(
				buildableThings.Where(a => AdaptiveCounterProduction.IsMobileCombat(a) && !IsUnitDelayed(a.Name) &&
					(Info.UnitsToBuild?.ContainsKey(a.Name) ?? false) && HasAdequateAirUnitReloadBuildings(a)),
				n => owned.GetValueOrDefault(n));
			counters.LastChoiceAdaptive = choice != null;
			return choice;
		}

		bool IsUnitDelayed(string unitName)
		{
			if (Info.HardDisabledUnitTypes.Contains(unitName))
				return true;

			// Absolute opening-completion gates apply to every production path, including
			// external requests. AirAI uses this for ftrk so opening cash is not spent on
			// early AA before the first expansion MCV physically exists. APC stays open.
			if (Info.DelayUntilOpeningMcvCompletedUnitTypes.Contains(unitName) &&
				!openingBuildOrderService.OpeningMcvCompleted)
				return true;

			// A minelayer is deliberately not an opening purchase. It becomes eligible only
			// after both a later world-tick gate and useful FAIR enemy-location information.
			// No hidden actor position is queried here: contacts come from CombatIntel and
			// static locations from StrategicMap's last legitimately observed memory.
			if (Info.IntelGatedMinelayerTypes.Contains(unitName) && !HasEnoughIntelForMinelayer())
				return true;

			if (Info.MultiFactoryGatedVehicleTypes.Contains(unitName))
			{
				combatIntelService.EnsureCurrentSnapshot();
				var completedFactories = combatIntelService.OwnedActors.Count(a => Info.PreferredVehicleProducerTypes.Contains(a.Info.Name));
				if (completedFactories < Math.Max(1, Info.MultiFactoryGatedVehicleMinimumProducerCount))
					return true;
			}

			return Info.UnitDelays != null &&
				Info.UnitDelays.TryGetValue(unitName, out var delay) &&
				delay > world.WorldTick;
		}

		bool HasEnoughIntelForMinelayer()
		{
			if (world.WorldTick < Info.MinelayerEarliestProductionTick)
				return false;

			// passive building memory exists to preserve fair strategic structure intel, not to
			// masquerade as three separate battlefield threats and unlock minelayers by count.
			var combatContacts = combatIntelService.EnemyCombatContacts.Count(c => !c.IsBuilding || c.IsDefensiveBuilding);
			if (combatContacts >= Info.MinelayerMinimumEnemyCombatContacts)
				return true;

			return strategicMapService.KnownEnemyStructures.Any(s =>
				s.ConfidencePercent >= Info.MinelayerMinimumKnownStructureConfidencePercent);
		}

		bool HasAdequateAirUnitReloadBuildings(ActorInfo actorInfo)
		{
			var aircraftInfo = actorInfo.TraitInfoOrDefault<AircraftInfo>();
			if (aircraftInfo == null)
				return true;

			var rearmableInfo = actorInfo.TraitInfoOrDefault<RearmableInfo>();
			if (rearmableInfo == null)
				return true;

			var rearmActors = rearmableInfo.RearmActors.ToHashSet();
			var countBuildings = rearmActors
				.Sum(b => AIUtils.CountActorsWithNameAndTrait<Building>(b, player));
			if (countBuildings <= 0)
				return false;

			// the old code counted only this exact aircraft type and allowed one of
			// EACH type per rearm building. One AFLD therefore meant one MiG + one Yak, while
			// YAML composition targets could never be reached. Treat the rearm family as one
			// shared physical capacity instead: all aircraft that use the same AF/HPAD family
			// consume the same pool. This grows naturally when BaseBuilder adds air producers.
			combatIntelService.EnsureCurrentSnapshot();
			var countOwnCompatibleAir = combatIntelService.OwnedActors.Count(a =>
			{
				if (a == null || !a.IsInWorld || a.IsDead || a.Info.TraitInfoOrDefault<AircraftInfo>() == null)
					return false;

				var ownRearm = a.Info.TraitInfoOrDefault<RearmableInfo>();
				return ownRearm != null && ownRearm.RearmActors.Any(rearmActors.Contains);
			});

			return countOwnCompatibleAir < countBuildings * Math.Max(1, Info.AirUnitsPerRearmBuilding);
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			return
			[
				new("QueuedBuildRequests", FieldSaver.FormatValue(queuedBuildRequests.ToArray())),
				new("SpecOpsBuildRequests", FieldSaver.FormatValue(specOpsBuildRequests.ToArray())),
				new("SeaProductionSuspendedForEconomy", FieldSaver.FormatValue(seaProductionSuspendedForEconomy)),
				new("AirProductionSuspendedForEconomy", FieldSaver.FormatValue(airProductionSuspendedForEconomy)),
				new("OpeningRiflesStarted", FieldSaver.FormatValue(openingRiflesStarted)),
				new("OpeningRocketsStarted", FieldSaver.FormatValue(openingRocketsStarted)),
				new("OpeningManualHarvestersStarted", FieldSaver.FormatValue(openingManualHarvestersStarted)),
				new("OpeningLightVehicleSatisfied", FieldSaver.FormatValue(openingLightVehicleSatisfied))
			];
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			var queuedBuildRequestsNode = data.NodeWithKeyOrDefault("QueuedBuildRequests");
			if (queuedBuildRequestsNode != null)
			{
				queuedBuildRequests.Clear();
				queuedBuildRequests.AddRange(
					FieldLoader.GetValue<ImmutableArray<string>>("QueuedBuildRequests", queuedBuildRequestsNode.Value.Value));
			}

			var specOpsBuildRequestsNode = data.NodeWithKeyOrDefault("SpecOpsBuildRequests");
			if (specOpsBuildRequestsNode != null)
			{
				specOpsBuildRequests.Clear();
				specOpsBuildRequests.AddRange(
					FieldLoader.GetValue<ImmutableArray<string>>("SpecOpsBuildRequests", specOpsBuildRequestsNode.Value.Value));
			}

			var seaSuspendedNode = data.NodeWithKeyOrDefault("SeaProductionSuspendedForEconomy");
			if (seaSuspendedNode != null)
				seaProductionSuspendedForEconomy = FieldLoader.GetValue<bool>("SeaProductionSuspendedForEconomy", seaSuspendedNode.Value.Value);

			var airSuspendedNode = data.NodeWithKeyOrDefault("AirProductionSuspendedForEconomy");
			if (airSuspendedNode != null)
				airProductionSuspendedForEconomy = FieldLoader.GetValue<bool>("AirProductionSuspendedForEconomy", airSuspendedNode.Value.Value);

			var openingRiflesNode = data.NodeWithKeyOrDefault("OpeningRiflesStarted");
			if (openingRiflesNode != null)
				openingRiflesStarted = FieldLoader.GetValue<int>("OpeningRiflesStarted", openingRiflesNode.Value.Value);
			var openingRocketsNode = data.NodeWithKeyOrDefault("OpeningRocketsStarted");
			if (openingRocketsNode != null)
				openingRocketsStarted = FieldLoader.GetValue<int>("OpeningRocketsStarted", openingRocketsNode.Value.Value);
			var openingHarvestersNode = data.NodeWithKeyOrDefault("OpeningManualHarvestersStarted");
			if (openingHarvestersNode != null)
				openingManualHarvestersStarted = FieldLoader.GetValue<int>("OpeningManualHarvestersStarted", openingHarvestersNode.Value.Value);
			var openingLightVehicleNode = data.NodeWithKeyOrDefault("OpeningLightVehicleSatisfied");
			if (openingLightVehicleNode != null)
				openingLightVehicleSatisfied = FieldLoader.GetValue<bool>("OpeningLightVehicleSatisfied", openingLightVehicleNode.Value.Value);
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			unitsToBuild.Dispose();
			resourceControlStructures.Dispose();
		}
	}
}
