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
using System.Linq;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public readonly record struct FransKnownAntiAirGeometryZone(uint ActorId, CPos Center);

	/// <summary>
	/// Exact identity of one ordered known-AA geometry snapshot. Signature is diagnostic/hash
	/// acceleration only; equality always compares the radius and every authoritative zone.
	/// </summary>
	public sealed class FransKnownAntiAirGeometryIdentity : IEquatable<FransKnownAntiAirGeometryIdentity>
	{
		readonly FransKnownAntiAirGeometryZone[] zones;
		readonly int hashCode;

		public int Signature { get; }
		public int SafetyRadius { get; }
		public int ZoneCount => zones.Length;
		public FransKnownAntiAirGeometryZone ZoneAt(int index) => zones[index];

		public FransKnownAntiAirGeometryIdentity(int safetyRadius, IReadOnlyList<FransKnownAntiAirGeometryZone> zones)
		{
			if (safetyRadius <= 0)
				throw new ArgumentOutOfRangeException(nameof(safetyRadius));

			SafetyRadius = safetyRadius;
			this.zones = zones?.ToArray() ?? Array.Empty<FransKnownAntiAirGeometryZone>();
			unchecked
			{
				var signature = 17;
				var hash = safetyRadius;
				foreach (var zone in this.zones)
				{
					signature = signature * 31 + (int)zone.ActorId;
					signature = signature * 31 + zone.Center.X;
					signature = signature * 31 + zone.Center.Y;
					hash = hash * 31 + zone.GetHashCode();
				}

				Signature = signature;
				hashCode = hash;
			}
		}

		public bool Equals(FransKnownAntiAirGeometryIdentity other)
		{
			if (ReferenceEquals(this, other))
				return true;
			if (other == null || SafetyRadius != other.SafetyRadius || zones.Length != other.zones.Length)
				return false;
			for (var i = 0; i < zones.Length; i++)
				if (zones[i] != other.zones[i])
					return false;
			return true;
		}

		public override bool Equals(object obj) => Equals(obj as FransKnownAntiAirGeometryIdentity);
		public override int GetHashCode() => hashCode;
	}

	public enum FransAirKnownAntiAirGeometryOutcome
	{
		OutsideMap,
		TargetInsideKnownAa,
		Direct,
		NoGraphRoute,
		BrokenPredecessor,
		GraphRoute
	}

	public readonly record struct FransAirKnownAntiAirGeometryRoute(
		bool Feasible,
		FransAirKnownAntiAirGeometryOutcome Outcome,
		CPos[] Waypoints);

	/// <summary>
	/// Shared bounded cache for pure known-AA geometry. One exact AA snapshot is retained at a
	/// time; dynamic RiskModel revisions are deliberately outside this cache.
	/// </summary>
	internal sealed class FransAirKnownAntiAirGeometryRouteCache
	{
		readonly record struct RouteKey(CPos StartCell, CPos TargetCell);
		readonly Dictionary<RouteKey, FransAirKnownAntiAirGeometryRoute> routes = [];
		readonly int maximumEntries;
		FransKnownAntiAirGeometryIdentity currentIdentity;

		public int Count => routes.Count;

		public FransAirKnownAntiAirGeometryRouteCache(int maximumEntries)
		{
			if (maximumEntries <= 0)
				throw new ArgumentOutOfRangeException(nameof(maximumEntries));
			this.maximumEntries = maximumEntries;
		}

		void EnsureIdentity(FransKnownAntiAirGeometryIdentity identity)
		{
			if (identity == null)
				throw new ArgumentNullException(nameof(identity));
			if (currentIdentity != null && currentIdentity.Equals(identity))
				return;
			routes.Clear();
			currentIdentity = identity;
		}

		static FransAirKnownAntiAirGeometryRoute Copy(FransAirKnownAntiAirGeometryRoute route) =>
			new(route.Feasible, route.Outcome, route.Waypoints?.ToArray() ?? Array.Empty<CPos>());

		public bool TryGet(FransKnownAntiAirGeometryIdentity identity, CPos startCell, CPos targetCell,
			out FransAirKnownAntiAirGeometryRoute route)
		{
			EnsureIdentity(identity);
			if (!routes.TryGetValue(new RouteKey(startCell, targetCell), out var stored))
			{
				route = default;
				return false;
			}

			route = Copy(stored);
			return true;
		}

		public void Store(FransKnownAntiAirGeometryIdentity identity, CPos startCell, CPos targetCell,
			FransAirKnownAntiAirGeometryRoute route)
		{
			EnsureIdentity(identity);
			var key = new RouteKey(startCell, targetCell);
			if (routes.Count >= maximumEntries && !routes.ContainsKey(key))
				routes.Clear();
			routes[key] = Copy(route);
		}

		public void Clear()
		{
			routes.Clear();
			currentIdentity = null;
		}
	}

	public readonly record struct FransAirBidRouteMetrics(
		bool Feasible,
		bool IsCritical,
		int PeakRisk,
		int EstimatedEtaTicks,
		int TravelCells);

	public readonly record struct FransAirRaidBidTemplate(
		bool Feasible,
		uint SubjectActorId,
		uint[] CommittedActorIds,
		int TotalCost,
		int RouteRisk,
		int TravelCost,
		int ForceCost,
		int EstimatedEtaTicks,
		int OfferedContribution,
		int RequiredContribution);

	public readonly record struct FransDefendResponseScore(
		int Utility,
		int StrengthScore,
		int UrgencyScore,
		int AssetRiskScore,
		int ResponseTimeCost,
		int OpportunityCost);

	/// <summary>
	/// Shared Commander evaluation primitives. General publishes fair raw missions/site intel; every combat
	/// Commander runs the same AVAILABLE -> CAPABILITY -> ETA -> RISK -> FORCE SIZING -> BID pipeline.
	/// Role-specific target rules remain in the Commander, but availability, ETA, actor value, RECON
	/// eligibility and conventional RAID contribution are evaluated here.
	/// </summary>
	public interface IFransCommanderCoreService
	{
		string PersonalityProfile { get; }
		int ReconWaypointBatchSize { get; }
		int RaidLostTargetReconTicks { get; }
		int ReconRetreatHealthPercent { get; }
		int GetCommanderFactorPercent(FransCommanderKind commander);
		bool IsActorAvailableForBidder(FransCommanderKind commander, string bidderKey, Actor actor);
		bool IsActorAvailableForMissionBid(FransCommanderKind commander, string bidderKey, Actor actor);
		bool IsExpectedRaidContact(FransActiveMission mission, Actor actor);
		int GetActorValue(Actor actor);
		int EstimateMoveEtaTicks(Actor subject, CPos targetCell);
		int EstimateReconEtaTicks(Actor subject, CPos targetCell);
		int PriceBid(FransCommanderKind commander, int routeRisk, int estimatedEtaTicks, int forceValue);
		int GetMissionRequiredContribution(FransCommanderKind commander, FransMission mission);
		int GetDefendRequiredUnitCount(FransMission mission);
		FransDefendResponseScore ScoreDefendResponse(FransMission mission, int offeredContribution,
			int requiredContribution, int estimatedEtaTicks, int forceValue);
		int GetReconVisionCells(Actor subject);
		bool IsReconCandidateOperational(Actor subject);
		int GetReconOpportunityCostPercent(Actor subject);
		int PriceReconBid(FransCommanderKind commander, Actor subject, int estimatedEtaTicks);
		bool IsRaidEtaEligible(int estimatedEtaTicks);
		int EstimateRaidContribution(FransCommanderKind commander, Actor attacker, Actor visibleTarget);
		int GetRaidRequiredContribution(FransCommanderKind commander, int observedHp);
		bool TryGetGroundDemandPoint(out CPos objective, out FransCommanderOrder order, out int startedWorldTick);
		IReadOnlyList<CPos> GetGroundRegroupPoints();
		bool IsGroundCombatUnitOwned(Actor actor);
		bool IsGroundVehicleCombatUnitOwned(Actor actor);
		IReadOnlyList<Actor> GetSharedGroundCombatRoster();
		bool TryGetSharedGroundCombatActor(uint actorId, out Actor actor);
		bool TryGetSharedAirKnownAntiAirGeometryRoute(CPos startCell, CPos targetCell,
			FransKnownAntiAirGeometryIdentity geometryIdentity, out FransAirKnownAntiAirGeometryRoute route);
		void StoreSharedAirKnownAntiAirGeometryRoute(CPos startCell, CPos targetCell,
			FransKnownAntiAirGeometryIdentity geometryIdentity, FransAirKnownAntiAirGeometryRoute route);
		bool TryGetSharedAirBidRouteMetrics(uint actorId, CPos actorCell, CPos targetCell,
			FransKnownAntiAirGeometryIdentity geometryIdentity, int riskRevision, out FransAirBidRouteMetrics metrics);
		void StoreSharedAirBidRouteMetrics(uint actorId, CPos actorCell, CPos targetCell,
			FransKnownAntiAirGeometryIdentity geometryIdentity, int riskRevision, FransAirBidRouteMetrics metrics);
		bool TryGetSharedAirRaidBidTemplate(uint targetActorId, CPos targetCell, int requiredContribution,
			FransKnownAntiAirGeometryIdentity geometryIdentity, int riskRevision, int candidateSignature, out FransAirRaidBidTemplate template);
		void StoreSharedAirRaidBidTemplate(uint targetActorId, CPos targetCell, int requiredContribution,
			FransKnownAntiAirGeometryIdentity geometryIdentity, int riskRevision, int candidateSignature, FransAirRaidBidTemplate template);
		bool IntersectsGroundStagingReservation(CPos topLeft, int width, int height);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Shared Fransbot Commander evaluation core. Provides common availability, ETA, actor-value, RECON and conventional RAID calculations; all Commander factors are neutral by default.")]
	public class FransCommanderCoreBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Stable personality profile id. only exposes the seam; 'balanced' preserves current behavior. Future personality presets should tune existing Commander/economy parameters through this profile instead of duplicating tactical logic.")]
		public readonly string PersonalityProfile = "balanced";

		[Desc("Weight applied to route peak risk while pricing ordinary Commander bids.")]
		public readonly int RouteRiskWeight = 3;

		[Desc("Cost added per estimated world tick while pricing ordinary Commander bids.")]
		public readonly int EtaCostPerTick = 1;

		[Desc("Committed force value is divided by this amount while pricing ordinary Commander bids.")]
		public readonly int ForceValueDivisor = 100;

		[Desc("Ground/Sea conventional RAID target HP margin used for force sizing.")]
		public readonly int RaidDamageMarginPercent = 110;

		[Desc("Air precision RAID HP margin for building targets. Mobile targets keep exact observed HP so one correctly sized full sortie is not inflated unnecessarily.")]
		public readonly int AirRaidBuildingDamageMarginPercent = 125;


		[Desc("Maximum estimated movement ETA for a conventional Ground/Air/Sea RAID contribution.")]
		public readonly int RaidMaximumStrikeEtaTicks = 500;

		[Desc("World ticks a committed RAID Commander performs short local plain-Move RECON around LastVisibleTargetCell after the exact target disappears before returning to its anchor.")]
		public readonly int RaidLostTargetReconTicks = 400;

		[Desc("Number of plain Move waypoints queued at once for persistent RECON probing.")]
		public readonly int ReconWaypointBatchSize = 8;

		[Desc("A RECON actor retreats when current HP falls below this percentage of MaxHP.")]
		public readonly int ReconRetreatHealthPercent = 95;

		[Desc("Default personality opportunity-cost multiplier for technically capable RECON actors. 100 preserves the normal ETA/value/vision price.")]
		public readonly int ReconDefaultOpportunityCostPercent = 100;

		[Desc("Optional personality actor-type overrides for RECON opportunity cost, expressed as percentages. High values make rare/specialist actors unattractive without changing role legality.")]
		public readonly FrozenDictionary<string, int> ReconActorOpportunityCostPercent =
			new Dictionary<string, int>().ToFrozenDictionary();

		[Desc("Ground bid factor. 100 is neutral x1.")]
		public readonly int GroundFactorPercent = 100;

		[Desc("Air bid factor. 100 is neutral x1.")]
		public readonly int AirFactorPercent = 100;

		[Desc("Sea bid factor. 100 is neutral x1.")]
		public readonly int SeaFactorPercent = 100;

		[Desc("SpecOps bid factor. 100 is neutral x1.")]
		public readonly int SpecOpsFactorPercent = 100;

		[Desc("World ticks between checks that apply native AttackAnything as the default stance to own movable AutoTarget units that are not currently committed to a Frans MISSION.")]
		public readonly int DefaultAttackAnythingScanInterval = 25;

		[Desc("Required DEFEND unit-count margin as a percentage of freshly observed hostile mobile combat units.")]
		public readonly int DefendRequiredStrengthMarginPercent = 300;

		[Desc("Utility weight for percentage fulfillment of the configured DEFEND strength requirement.")]
		public readonly int DefendStrengthWeight = 20;

		[Desc("Utility cost per estimated world tick before a DEFEND package can arrive.")]
		public readonly int DefendResponseTimeWeight = 5;

		[Desc("Utility weight for General DEFEND urgency above the defended asset's base strategic value.")]
		public readonly int DefendUrgencyWeight = 1;

		[Desc("Utility weight for General's strategic value of the friendly asset at risk.")]
		public readonly int DefendThreatenedAssetValueWeight = 1;

		[Desc("Utility weight for visible hostile combat pressure, normalized by ForceValueDivisor.")]
		public readonly int DefendThreatPressureWeight = 1;

		[Desc("Utility weight for committed combat value, normalized by ForceValueDivisor.")]
		public readonly int DefendCombatValueWeight = 1;

		[Desc("Opportunity cost charged for committed combat value, normalized by ForceValueDivisor.")]
		public readonly int DefendOpportunityCostWeight = 1;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (string.IsNullOrWhiteSpace(PersonalityProfile) || RouteRiskWeight <= 0 || EtaCostPerTick <= 0 || ForceValueDivisor <= 0 ||
				RaidDamageMarginPercent < 100 || AirRaidBuildingDamageMarginPercent < 100 || RaidMaximumStrikeEtaTicks <= 0 || RaidLostTargetReconTicks <= 0 ||
				ReconWaypointBatchSize <= 0 || ReconRetreatHealthPercent <= 0 || ReconRetreatHealthPercent > 100 ||
				ReconDefaultOpportunityCostPercent <= 0 || ReconActorOpportunityCostPercent.Any(p => string.IsNullOrWhiteSpace(p.Key) || p.Value <= 0) ||
				GroundFactorPercent <= 0 || AirFactorPercent <= 0 || SeaFactorPercent <= 0 || SpecOpsFactorPercent <= 0 || DefaultAttackAnythingScanInterval < 25 ||
				DefendRequiredStrengthMarginPercent < 100 || DefendStrengthWeight < 0 || DefendResponseTimeWeight < 0 || DefendUrgencyWeight < 0 ||
				DefendThreatenedAssetValueWeight < 0 || DefendThreatPressureWeight < 0 || DefendCombatValueWeight < 0 || DefendOpportunityCostWeight < 0)
				throw new YamlException("FransCommanderCore pricing, RAID, RECON, Commander factor or default-stance values are invalid.");
		}

		public override object Create(ActorInitializer init) { return new FransCommanderCoreBotModule(init.Self, this); }
	}

	public class FransCommanderCoreBotModule : ConditionalTrait<FransCommanderCoreBotModuleInfo>, IBotTick, IFransCommanderCoreService
	{
		readonly World world;
		readonly Player player;
		IFransCommandBidService commandBidService;
		IFransCombatIntelService combatIntelService;
		readonly HashSet<uint> defaultAttackAnythingActors = [];
		readonly Dictionary<string, bool> sharedGroundActorTypeCache = new(StringComparer.Ordinal);
		Actor[] sharedGroundCombatRoster = Array.Empty<Actor>();
		Dictionary<uint, Actor> sharedGroundCombatById = [];
		int sharedGroundCombatSnapshotTick = -1;
		readonly record struct AirBidRouteCacheKey(uint ActorId, CPos ActorCell, CPos TargetCell, FransKnownAntiAirGeometryIdentity GeometryIdentity, int RiskRevision);
		readonly record struct AirRaidBidCacheKey(uint TargetActorId, CPos TargetCell, int RequiredContribution, FransKnownAntiAirGeometryIdentity GeometryIdentity, int RiskRevision, int CandidateSignature);
		readonly Dictionary<AirBidRouteCacheKey, FransAirBidRouteMetrics> sharedAirBidRouteMetrics = [];
		readonly Dictionary<AirRaidBidCacheKey, FransAirRaidBidTemplate> sharedAirRaidBidTemplates = [];
		readonly FransAirKnownAntiAirGeometryRouteCache sharedAirKnownAntiAirGeometryRoutes = new(4096);
		int sharedAirBidRouteRiskRevision = -1;
		const int SharedAirBidRouteMaximumEntries = 4096;
		const int SharedAirRaidBidMaximumEntries = 512;
		readonly HashSet<uint> missionOwnedLastScan = [];
		int defaultAttackAnythingScanTicks;

		public FransCommanderCoreBotModule(Actor self, FransCommanderCoreBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;
			commandBidService = self.Owner.PlayerActor.TraitsImplementing<IFransCommandBidService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransCommanderCore requires FransCommandBidBotModule.");
			combatIntelService = self.Owner.PlayerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransCommanderCore requires FransCombatIntelBotModule for the shared Ground roster snapshot.");
			FransBotLog.BotDebug(world,
				"{0}: CommanderCore personality profile '{1}' active. RECON opportunity cost defaults to {2}% with actor overrides [{3}]; capability remains legality-only.",
				player, Info.PersonalityProfile, Info.ReconDefaultOpportunityCostPercent,
				string.Join(",", Info.ReconActorOpportunityCostPercent.OrderBy(p => p.Key, StringComparer.OrdinalIgnoreCase).Select(p => $"{p.Key}={p.Value}%")));
		}

		protected override void TraitEnabled(Actor self)
		{
			defaultAttackAnythingActors.Clear();
			missionOwnedLastScan.Clear();
			sharedGroundCombatRoster = Array.Empty<Actor>();
			sharedGroundCombatById = [];
			sharedGroundCombatSnapshotTick = -1;
			sharedAirBidRouteMetrics.Clear();
			sharedAirRaidBidTemplates.Clear();
			sharedAirKnownAntiAirGeometryRoutes.Clear();
			sharedAirBidRouteRiskRevision = -1;
			defaultAttackAnythingScanTicks = 1;
			FransBotLog.BotDebug(world,
				"{0}: CommanderCore default stance: movable own units with native AutoTarget use AttackAnything whenever they are outside a Frans MISSION; mission ownership is never preempted by this stance policy.",
				player);
		}

		protected override void TraitDisabled(Actor self)
		{
			defaultAttackAnythingActors.Clear();
			missionOwnedLastScan.Clear();
			sharedGroundCombatRoster = Array.Empty<Actor>();
			sharedGroundCombatById = [];
			sharedGroundCombatSnapshotTick = -1;
			sharedAirBidRouteMetrics.Clear();
			sharedAirRaidBidTemplates.Clear();
			sharedAirKnownAntiAirGeometryRoutes.Clear();
			sharedAirBidRouteRiskRevision = -1;
		}

		bool IsSharedGroundCombatActorType(ActorInfo actorInfo)
		{
			if (actorInfo == null || string.IsNullOrEmpty(actorInfo.Name))
				return false;
			if (sharedGroundActorTypeCache.TryGetValue(actorInfo.Name, out var cached))
				return cached;

			// ActorInfo and its trait declarations are immutable for the loaded ruleset. Cache only
			// this static classification; ownership, life-state, position and reservations remain live.
			var managed = actorInfo.HasTraitInfo<AttackBaseInfo>() && actorInfo.HasTraitInfo<MobileInfo>() &&
				!actorInfo.HasTraitInfo<AircraftInfo>();
			sharedGroundActorTypeCache[actorInfo.Name] = managed;
			return managed;
		}

		void EnsureSharedGroundCombatRoster()
		{
			combatIntelService.EnsureCurrentSnapshot();
			if (sharedGroundCombatSnapshotTick == combatIntelService.SnapshotWorldTick)
				return;

			using (FransBotLog.Profile(world, player, "Ground.SharedRosterBuild"))
			{
				var roster = new List<Actor>();
				var byId = new Dictionary<uint, Actor>();
				foreach (var actor in combatIntelService.OwnedActors)
				{
					if (actor == null || !actor.IsInWorld || actor.IsDead || actor.Owner != player || actor.OccupiesSpace == null ||
						!IsSharedGroundCombatActorType(actor.Info))
						continue;

					roster.Add(actor);
					byId[actor.ActorID] = actor;
				}

				roster.Sort((a, b) => a.ActorID.CompareTo(b.ActorID));
				sharedGroundCombatRoster = roster.ToArray();
				sharedGroundCombatById = byId;
			}
			sharedGroundCombatSnapshotTick = combatIntelService.SnapshotWorldTick;
		}

		public IReadOnlyList<Actor> GetSharedGroundCombatRoster()
		{
			EnsureSharedGroundCombatRoster();
			return sharedGroundCombatRoster;
		}

		public bool TryGetSharedGroundCombatActor(uint actorId, out Actor actor)
		{
			EnsureSharedGroundCombatRoster();
			return sharedGroundCombatById.TryGetValue(actorId, out actor);
		}

		void EnsureSharedAirBidRouteRevision(int riskRevision)
		{
			if (sharedAirBidRouteRiskRevision == riskRevision)
				return;
			sharedAirBidRouteMetrics.Clear();
			sharedAirRaidBidTemplates.Clear();
			sharedAirBidRouteRiskRevision = riskRevision;
		}

		public bool TryGetSharedAirKnownAntiAirGeometryRoute(CPos startCell, CPos targetCell,
			FransKnownAntiAirGeometryIdentity geometryIdentity, out FransAirKnownAntiAirGeometryRoute route)
		{
			return sharedAirKnownAntiAirGeometryRoutes.TryGet(geometryIdentity, startCell, targetCell, out route);
		}

		public void StoreSharedAirKnownAntiAirGeometryRoute(CPos startCell, CPos targetCell,
			FransKnownAntiAirGeometryIdentity geometryIdentity, FransAirKnownAntiAirGeometryRoute route)
		{
			sharedAirKnownAntiAirGeometryRoutes.Store(geometryIdentity, startCell, targetCell, route);
		}

		public bool TryGetSharedAirBidRouteMetrics(uint actorId, CPos actorCell, CPos targetCell,
			FransKnownAntiAirGeometryIdentity geometryIdentity, int riskRevision, out FransAirBidRouteMetrics metrics)
		{
			EnsureSharedAirBidRouteRevision(riskRevision);
			return sharedAirBidRouteMetrics.TryGetValue(
				new AirBidRouteCacheKey(actorId, actorCell, targetCell, geometryIdentity, riskRevision), out metrics);
		}

		public void StoreSharedAirBidRouteMetrics(uint actorId, CPos actorCell, CPos targetCell,
			FransKnownAntiAirGeometryIdentity geometryIdentity, int riskRevision, FransAirBidRouteMetrics metrics)
		{
			EnsureSharedAirBidRouteRevision(riskRevision);
			if (sharedAirBidRouteMetrics.Count >= SharedAirBidRouteMaximumEntries)
				sharedAirBidRouteMetrics.Clear();
			sharedAirBidRouteMetrics[new AirBidRouteCacheKey(actorId, actorCell, targetCell, geometryIdentity, riskRevision)] = metrics;
		}

		public bool TryGetSharedAirRaidBidTemplate(uint targetActorId, CPos targetCell, int requiredContribution,
			FransKnownAntiAirGeometryIdentity geometryIdentity, int riskRevision, int candidateSignature, out FransAirRaidBidTemplate template)
		{
			EnsureSharedAirBidRouteRevision(riskRevision);
			return sharedAirRaidBidTemplates.TryGetValue(
				new AirRaidBidCacheKey(targetActorId, targetCell, requiredContribution, geometryIdentity, riskRevision, candidateSignature), out template);
		}

		public void StoreSharedAirRaidBidTemplate(uint targetActorId, CPos targetCell, int requiredContribution,
			FransKnownAntiAirGeometryIdentity geometryIdentity, int riskRevision, int candidateSignature, FransAirRaidBidTemplate template)
		{
			EnsureSharedAirBidRouteRevision(riskRevision);
			if (sharedAirRaidBidTemplates.Count >= SharedAirRaidBidMaximumEntries)
				sharedAirRaidBidTemplates.Clear();
			sharedAirRaidBidTemplates[new AirRaidBidCacheKey(targetActorId, targetCell, requiredContribution, geometryIdentity, riskRevision, candidateSignature)] = template;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (player.WinState != WinState.Undefined || --defaultAttackAnythingScanTicks > 0)
				return;

			// A CA squad manager owns stance doctrine on the Frankenstein stack:
			// sallying the whole idle pool at contacts starves CreateAttackForce
			// thresholds indefinitely (DAWN nw-hard6 m2: zero squads in 74k ticks).
			// Donor bots have no SquadManagerBotModuleCA and keep this posture.
			if (player.PlayerActor.TraitsImplementing<OpenRA.Mods.CA.Traits.SquadManagerBotModuleCA>().Any(t => !t.IsTraitDisabled))
			{
				// One-shot revert: units already forced into AttackAnything before the
				// squad manager latched (first scan runs at WT1) mass-defend instead.
				// Only ids this module stanced are in the set; squad-assigned stances
				// are never touched.
				if (defaultAttackAnythingActors.Count > 0)
				{
					foreach (var pair in world.ActorsWithTrait<AutoTarget>())
					{
						var actor = pair.Actor;
						if (actor == null || !actor.IsInWorld || actor.IsDead || actor.Owner != player
							|| !defaultAttackAnythingActors.Contains(actor.ActorID)
							|| pair.Trait.Stance != UnitStance.AttackAnything)
							continue;

						bot.QueueOrder(new Order("SetUnitStance", actor, false) { ExtraData = (uint)UnitStance.Defend });
					}

					defaultAttackAnythingActors.Clear();
					missionOwnedLastScan.Clear();
				}

				return;
			}

			defaultAttackAnythingScanTicks = Info.DefaultAttackAnythingScanInterval;
			var live = new HashSet<uint>();
			foreach (var pair in world.ActorsWithTrait<AutoTarget>()
				.Where(x => x.Actor != null && x.Actor.IsInWorld && !x.Actor.IsDead && x.Actor.Owner == player)
				.Where(x => x.Actor.TraitOrDefault<Mobile>() != null || x.Actor.TraitOrDefault<Aircraft>() != null)
				.OrderBy(x => x.Actor.ActorID))
			{
				var actor = pair.Actor;
				var id = actor.ActorID;
				live.Add(id);
				var inMission = commandBidService != null && commandBidService.TryGetActorActiveMission(id, out _);
				var wasMissionOwned = missionOwnedLastScan.Contains(id);
				if (inMission)
				{
					missionOwnedLastScan.Add(id);
					continue;
				}

				missionOwnedLastScan.Remove(id);
				if (!defaultAttackAnythingActors.Add(id) && !wasMissionOwned)
					continue;

				if (pair.Trait.Stance != UnitStance.AttackAnything)
					bot.QueueOrder(new Order("SetUnitStance", actor, false) { ExtraData = (uint)UnitStance.AttackAnything });
			}

			defaultAttackAnythingActors.RemoveWhere(id => !live.Contains(id));
			missionOwnedLastScan.RemoveWhere(id => !live.Contains(id));
		}

		public string PersonalityProfile => Info.PersonalityProfile;
		public int ReconWaypointBatchSize => Info.ReconWaypointBatchSize;
		public int RaidLostTargetReconTicks => Info.RaidLostTargetReconTicks;
		public int ReconRetreatHealthPercent => Info.ReconRetreatHealthPercent;

		public int GetCommanderFactorPercent(FransCommanderKind commander) => commander switch
		{
			FransCommanderKind.Ground => Info.GroundFactorPercent,
			FransCommanderKind.Air => Info.AirFactorPercent,
			FransCommanderKind.Sea => Info.SeaFactorPercent,
			FransCommanderKind.SpecOps => Info.SpecOpsFactorPercent,
			_ => 100
		};

		int ApplyCommanderFactor(FransCommanderKind commander, long value)
		{
			if (value <= 0)
				return 0;
			var factor = GetCommanderFactorPercent(commander);
			return (int)Math.Clamp((value * factor + 99) / 100, 1L, int.MaxValue);
		}

		public bool IsActorAvailableForBidder(FransCommanderKind commander, string bidderKey, Actor actor)
		{
			return actor != null && actor.IsInWorld && !actor.IsDead && actor.Owner == player &&
				!string.IsNullOrEmpty(bidderKey) &&
				(commandBidService == null || !commandBidService.IsActorUnavailableForBidder(commander, bidderKey, actor.ActorID));
		}

		public bool IsActorAvailableForMissionBid(FransCommanderKind commander, string bidderKey, Actor actor)
		{
			return actor != null && actor.IsInWorld && !actor.IsDead && actor.Owner == player &&
				!string.IsNullOrEmpty(bidderKey) &&
				(commandBidService == null || !commandBidService.IsActorUnavailableForMissionBid(commander, bidderKey, actor.ActorID));
		}

		public bool IsExpectedRaidContact(FransActiveMission mission, Actor actor)
		{
			if (actor == null || actor.ActorID == 0)
				return false;
			if (actor.ActorID == mission.TargetActorId)
				return true;
			return (mission.SiteIntel.Actors ?? Array.Empty<FransSiteIntelActor>()).Any(a => a.ActorId == actor.ActorID);
		}

		public int GetActorValue(Actor actor)
		{
			return actor == null ? 0 : Math.Max(1, actor.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1);
		}

		public int EstimateReconEtaTicks(Actor subject, CPos targetCell) => EstimateMoveEtaTicks(subject, targetCell);

		public int EstimateMoveEtaTicks(Actor subject, CPos targetCell)
		{
			if (subject == null || !subject.IsInWorld || subject.IsDead || !world.Map.Contains(targetCell))
				return int.MaxValue;

			var destination = world.Map.CenterOfCell(targetCell);
			var mobile = subject.TraitOrDefault<Mobile>();
			if (mobile != null)
			{
				if (mobile.IsTraitDisabled || mobile.IsTraitPaused)
					return int.MaxValue;
				var eta = mobile.EstimatedMoveDuration(subject, subject.CenterPosition, destination);
				return eta > 0 ? eta : 1;
			}

			var aircraft = subject.TraitOrDefault<Aircraft>();
			if (aircraft != null)
			{
				if (aircraft.IsTraitDisabled || aircraft.IsTraitPaused)
					return int.MaxValue;
				var eta = aircraft.EstimatedMoveDuration(subject, subject.CenterPosition, destination);
				return eta > 0 ? eta : 1;
			}

			return int.MaxValue;
		}

		public int PriceBid(FransCommanderKind commander, int routeRisk, int estimatedEtaTicks, int forceValue)
		{
			if (estimatedEtaTicks <= 0 || estimatedEtaTicks == int.MaxValue)
				return int.MaxValue;
			var price = (long)Math.Max(0, routeRisk) * Info.RouteRiskWeight +
				(long)estimatedEtaTicks * Info.EtaCostPerTick +
				Math.Max(0, forceValue) / Info.ForceValueDivisor;
			return ApplyCommanderFactor(commander, price);
		}

		public int GetMissionRequiredContribution(FransCommanderKind commander, FransMission mission)
		{
			if (mission.Type == FransMissionType.Recon)
				return 1;

			if (mission.Type == FransMissionType.Raid)
			{
				var snapshot = mission.SiteIntel.Actors?.FirstOrDefault(a => a.ActorId == mission.TargetActorId) ?? default;
				var observedHp = snapshot.ObservedHp;
				// A remembered STATIONARY building may carry no fresh HP observation. Its public
				// ruleset HP is legitimate intel — the mod rules are not hidden state — so the
				// strike sizes against the undamaged value instead of refusing to bid.
				if (observedHp <= 0 && mission.IsRememberedIntel && mission.IsBuilding &&
					world.Map.Rules.Actors.TryGetValue(mission.TargetActorType, out var rememberedType))
					observedHp = rememberedType.TraitInfos<HealthInfo>().Select(h => h.HP).DefaultIfEmpty(0).Max();
				var raidRequired = GetRaidRequiredContribution(commander, observedHp);
				if (raidRequired == int.MaxValue)
					return raidRequired;

				// aircraft now complete their full native sortie. Buildings can survive or
				// repair through exact-HP estimates, so
				// Air alone receives a 125% building margin. Mobile precision targets remain exact HP.
				if (commander == FransCommanderKind.Air && mission.IsBuilding)
					return (int)Math.Clamp(((long)observedHp * Info.AirRaidBuildingDamageMarginPercent + 99) / 100, 1L, int.MaxValue);

				return raidRequired;
			}

			var observed = mission.SiteIntel.Actors ?? Array.Empty<FransSiteIntelActor>();
			var enemyCombat = observed
				.Where(a => a.Owner != null && PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(a.Owner)) && a.IsCombatActor)
				.ToArray();
			long required = enemyCombat.Sum(a => (long)Math.Max(0, a.ObservedValue));
			// Ground evaluates massed infantry symmetrically. A lone infantry actor keeps
			// raw observed value; from two infantry upward the infantry subtotal receives the same
			// 130% squad-value multiplier used for friendly Ground tactical groups. Other unit types
			// retain raw observed value and other Commanders remain unchanged.
			if (commander == FransCommanderKind.Ground)
			{
				var infantry = enemyCombat.Where(a => IsGroundInfantryActorType(a.ActorType)).ToArray();
				if (infantry.Length >= 2)
				{
					var infantryRaw = infantry.Sum(a => (long)Math.Max(0, a.ObservedValue));
					required = required - infantryRaw + infantryRaw * 130 / 100;
				}
			}
			return (int)Math.Clamp(Math.Max(1L, required), 1L, int.MaxValue);
		}

		// Cameo port: upstream listed RA infantry ids; classify by traits instead.
		bool IsGroundInfantryActorType(string actorType) =>
			actorType != null && world.Map.Rules.Actors.TryGetValue(actorType, out var info)
				&& FransActorClass.IsInfantry(info);

		public int GetDefendRequiredUnitCount(FransMission mission)
		{
			if (mission.Type != FransMissionType.Defend)
				return 1;

			var observed = mission.SiteIntel.Actors ?? Array.Empty<FransSiteIntelActor>();
			var seenEnemyCombatUnits = observed.Count(a =>
				a.Owner != null &&
				PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(a.Owner)) &&
				!a.IsBuilding &&
				a.IsCombatActor);
			return (int)Math.Clamp(Math.Max(1L,
				((long)seenEnemyCombatUnits * Info.DefendRequiredStrengthMarginPercent + 99L) / 100L), 1L, int.MaxValue);
		}

		public FransDefendResponseScore ScoreDefendResponse(FransMission mission, int offeredContribution,
			int requiredContribution, int estimatedEtaTicks, int forceValue)
		{
			if (mission.Type != FransMissionType.Defend || requiredContribution <= 0 || estimatedEtaTicks < 0 || estimatedEtaTicks == int.MaxValue)
				return default;

			var fulfillmentPercent = (int)Math.Clamp((long)Math.Max(0, offeredContribution) * 100L / requiredContribution, 0L, 100L);
			var normalizedForce = Math.Max(0, forceValue) / Info.ForceValueDivisor;
			var normalizedThreat = Math.Max(0, mission.DefendThreatValue) / Info.ForceValueDivisor;
			var incidentUrgency = Math.Max(0, mission.StrategicPriority - Math.Max(0, mission.DefendedAssetValue));
			var strengthScore = (long)fulfillmentPercent * Info.DefendStrengthWeight +
				(long)normalizedForce * Info.DefendCombatValueWeight;
			var urgencyScore = (long)incidentUrgency * Info.DefendUrgencyWeight +
				(long)normalizedThreat * Info.DefendThreatPressureWeight;
			var assetRiskScore = (long)Math.Max(0, mission.DefendedAssetValue) * Info.DefendThreatenedAssetValueWeight;
			var responseTimeCost = (long)estimatedEtaTicks * Info.DefendResponseTimeWeight;
			var opportunityCost = (long)normalizedForce * Info.DefendOpportunityCostWeight;
			var utility = strengthScore + urgencyScore + assetRiskScore - responseTimeCost - opportunityCost;
			return new FransDefendResponseScore(
				(int)Math.Clamp(utility, int.MinValue, int.MaxValue),
				(int)Math.Clamp(strengthScore, 0L, int.MaxValue),
				(int)Math.Clamp(urgencyScore, 0L, int.MaxValue),
				(int)Math.Clamp(assetRiskScore, 0L, int.MaxValue),
				(int)Math.Clamp(responseTimeCost, 0L, int.MaxValue),
				(int)Math.Clamp(opportunityCost, 0L, int.MaxValue));
		}

		public int GetReconVisionCells(Actor subject)
		{
			if (subject == null || !subject.IsInWorld || subject.IsDead)
				return 0;

			var range = subject.TraitsImplementing<RevealsShroud>()
				.Where(r => !r.IsTraitDisabled)
				.Select(r => r.Range.Length)
				.DefaultIfEmpty(0)
				.Max();
			if (range <= 0)
				return 0;

			var cellLength = Math.Max(1, WDist.FromCells(1).Length);
			return Math.Max(1, (range + cellLength - 1) / cellLength);
		}

		public bool IsReconCandidateOperational(Actor subject)
		{
			if (subject == null || !subject.IsInWorld || subject.IsDead || subject.Owner != player)
				return false;

			var health = subject.TraitOrDefault<Health>();
			if (health != null && health.MaxHP > 0 &&
				(long)health.HP * 100 < (long)health.MaxHP * Info.ReconRetreatHealthPercent)
				return false;

			var mobile = subject.TraitOrDefault<Mobile>();
			var aircraft = subject.TraitOrDefault<Aircraft>();
			if (mobile != null)
			{
				if (mobile.IsTraitDisabled || mobile.IsTraitPaused)
					return false;
			}
			else if (aircraft != null)
			{
				if (aircraft.IsTraitDisabled || aircraft.IsTraitPaused)
					return false;
			}
			else
				return false;

			return GetReconVisionCells(subject) > 0;
		}

		public int GetReconOpportunityCostPercent(Actor subject)
		{
			if (subject != null && Info.ReconActorOpportunityCostPercent.TryGetValue(subject.Info.Name, out var configured))
				return configured;
			return Info.ReconDefaultOpportunityCostPercent;
		}

		public int PriceReconBid(FransCommanderKind commander, Actor subject, int estimatedEtaTicks)
		{
			if (subject == null || estimatedEtaTicks <= 0 || estimatedEtaTicks == int.MaxValue)
				return int.MaxValue;
			var vision = GetReconVisionCells(subject);
			if (vision <= 0)
				return int.MaxValue;
			var basePrice = (long)estimatedEtaTicks * GetActorValue(subject) / vision;
			var price = (basePrice * GetReconOpportunityCostPercent(subject) + 99L) / 100L;
			return ApplyCommanderFactor(commander, Math.Max(1L, price));
		}

		public bool IsRaidEtaEligible(int estimatedEtaTicks)
		{
			return estimatedEtaTicks > 0 && estimatedEtaTicks != int.MaxValue && estimatedEtaTicks <= Info.RaidMaximumStrikeEtaTicks;
		}

		public int GetRaidRequiredContribution(FransCommanderKind commander, int observedHp)
		{
			if (observedHp <= 0)
				return int.MaxValue;
			if (commander == FransCommanderKind.SpecOps)
				return 1;
			if (commander == FransCommanderKind.Air)
				return observedHp;
			return (int)Math.Clamp(((long)observedHp * Info.RaidDamageMarginPercent + 99) / 100, 1L, int.MaxValue);
		}

		public int EstimateRaidContribution(FransCommanderKind commander, Actor attacker, Actor visibleTarget)
		{
			if (commander == FransCommanderKind.SpecOps)
				return 1;
			return commander == FransCommanderKind.Air
				? EstimateAirRaidSortieDamage(attacker, visibleTarget)
				: EstimateRaidFirstStrikeDamage(attacker, visibleTarget);
		}

		int EstimateRaidFirstStrikeDamage(Actor attacker, Actor target)
		{
			if (attacker == null || target == null || !attacker.IsInWorld || attacker.IsDead ||
				!target.IsInWorld || target.IsDead || !target.CanBeViewedByPlayer(player))
				return 0;

			var attackTarget = Target.FromActor(target);
			long total = 0;
			foreach (var attack in attacker.TraitsImplementing<AttackBase>())
			{
				if (attack.IsTraitDisabled || attack.IsTraitPaused || !attack.HasAnyValidWeapons(attackTarget))
					continue;
				foreach (var armament in attack.Armaments)
				{
					var firepower = attacker.TraitsImplementing<IFirepowerModifier>().Select(m => m.GetFirepowerModifier(armament.Info.Name)).ToArray();
					if (armament.IsTraitDisabled || armament.IsTraitPaused || !armament.Weapon.IsValidAgainst(attackTarget, world, attacker))
						continue;
					long shotDamage = 0;
					foreach (var warhead in armament.Weapon.Warheads.OfType<DamageWarhead>())
					{
						if (!warhead.IsValidAgainst(target, attacker) || warhead.Damage <= 0)
							continue;
						var armorModifier = 100;
						if (warhead.Versus.Count > 0)
						{
							var armor = target.TraitsImplementing<Armor>()
								.Where(a => !a.IsTraitDisabled && a.Info.Type != null && warhead.Versus.ContainsKey(a.Info.Type))
								.Select(a => warhead.Versus[a.Info.Type]);
							armorModifier = Util.ApplyPercentageModifiers(100, armor);
						}
						shotDamage += Math.Max(0, Util.ApplyPercentageModifiers(warhead.Damage, firepower.Append(armorModifier)));
					}
					total += shotDamage * Math.Max(1, armament.Weapon.Burst);
				}
			}
			return (int)Math.Clamp(total, 0L, int.MaxValue);
		}

		int EstimateAirRaidSortieDamage(Actor attacker, Actor target)
		{
			if (attacker == null || target == null || !attacker.IsInWorld || attacker.IsDead ||
				!target.IsInWorld || target.IsDead || !target.CanBeViewedByPlayer(player))
				return 0;

			var attackTarget = Target.FromActor(target);
			var ammoPools = attacker.TraitsImplementing<AmmoPool>().ToArray();
			var bestDamageByPool = new Dictionary<AmmoPool, long>();
			long unpooledDamage = 0;

			foreach (var attack in attacker.TraitsImplementing<AttackBase>())
			{
				if (attack.IsTraitDisabled || attack.IsTraitPaused || !attack.HasAnyValidWeapons(attackTarget))
					continue;
				foreach (var armament in attack.Armaments)
				{
					var firepower = attacker.TraitsImplementing<IFirepowerModifier>().Select(m => m.GetFirepowerModifier(armament.Info.Name)).ToArray();
					if (armament.IsTraitDisabled || armament.IsTraitPaused || !armament.Weapon.IsValidAgainst(attackTarget, world, attacker))
						continue;
					long shotDamage = 0;
					foreach (var warhead in armament.Weapon.Warheads.OfType<DamageWarhead>())
					{
						if (!warhead.IsValidAgainst(target, attacker) || warhead.Damage <= 0)
							continue;
						var armorModifier = 100;
						if (warhead.Versus.Count > 0)
						{
							var armor = target.TraitsImplementing<Armor>()
								.Where(a => !a.IsTraitDisabled && a.Info.Type != null && warhead.Versus.ContainsKey(a.Info.Type))
								.Select(a => warhead.Versus[a.Info.Type]);
							armorModifier = Util.ApplyPercentageModifiers(100, armor);
						}
						shotDamage += Math.Max(0, Util.ApplyPercentageModifiers(warhead.Damage, firepower.Append(armorModifier)));
					}
					if (shotDamage <= 0)
						continue;
					var pool = ammoPools.FirstOrDefault(p => p.Info.Armaments.Contains(armament.Info.Name));
					if (pool == null)
					{
						unpooledDamage += shotDamage * Math.Max(1, armament.Weapon.Burst);
						continue;
					}
					var shotsAvailable = pool.CurrentAmmoCount / Math.Max(1, armament.Info.AmmoUsage);
					var contribution = shotDamage * Math.Max(0, shotsAvailable);
					if (!bestDamageByPool.TryGetValue(pool, out var previous) || contribution > previous)
						bestDamageByPool[pool] = contribution;
				}
			}

			var total = unpooledDamage + bestDamageByPool.Values.Aggregate(0L, (sum, d) => sum + d);
			return (int)Math.Clamp(total, 0L, int.MaxValue);
		}


		IFransGroundCommanderService[] GroundServices() => player.PlayerActor
			.TraitsImplementing<IFransGroundCommanderService>().ToArray();

		public bool TryGetGroundDemandPoint(out CPos objective, out FransCommanderOrder order, out int startedWorldTick)
		{
			var candidates = GroundServices()
				.Select(s => s.TryGetGroundDemandPoint(out var p, out var o, out var t)
					? (Valid: true, Point: p, Order: o, Started: t)
					: (Valid: false, Point: default(CPos), Order: FransCommanderOrder.Move, Started: -1))
				.Where(x => x.Valid)
				.OrderByDescending(x => x.Order == FransCommanderOrder.Retreat)
				.ThenByDescending(x => x.Order == FransCommanderOrder.Defend)
				.ThenByDescending(x => x.Started)
				.ToArray();
			if (candidates.Length == 0)
			{
				objective = default;
				order = FransCommanderOrder.Move;
				startedWorldTick = -1;
				return false;
			}
			objective = candidates[0].Point;
			order = candidates[0].Order;
			startedWorldTick = candidates[0].Started;
			return true;
		}

		public IReadOnlyList<CPos> GetGroundRegroupPoints() => GroundServices()
			.SelectMany(s => s.GetGroundRegroupPoints() ?? Array.Empty<CPos>())
			.Distinct().OrderBy(c => c.X).ThenBy(c => c.Y).ToArray();

		public bool IsGroundCombatUnitOwned(Actor actor) => actor != null && GroundServices().Any(s => s.IsGroundCombatUnitOwned(actor));

		public bool IsGroundVehicleCombatUnitOwned(Actor actor) =>
			actor != null && GroundServices().Any(s => s.IsGroundVehicleCombatUnitOwned(actor));

		public bool IntersectsGroundStagingReservation(CPos topLeft, int width, int height) =>
			GroundServices().Any(s => s.IntersectsGroundStagingReservation(topLeft, width, height));
	}
}
