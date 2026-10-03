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
using OpenRA.Mods.Common.Pathfinder;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	/// <summary>
	/// Describes the mission/actor family asking for a risk estimate.  The protected
	/// Actor is still authoritative for weapon validity; the role only controls
	/// buffers and preferred/critical thresholds.
	/// </summary>
	public enum FransRiskRole
	{
		Mcv,
		Capturer,
		Aircraft,
		GroundCombat,
		Harvester,
		SupportVehicle,
		Minelayer,
		BuildingPlacement,
		AuxiliaryCombat,
		NavalTransport,
		NavalCombat
	}

	/// <summary>
	/// Mission tolerance is intentionally separate from actor type.  A cautious MCV
	/// expansion and a pre-supported beachhead MCV therefore use the same threat data
	/// but may make different decisions from it.
	/// </summary>
	public enum FransRiskTolerance
	{
		Cautious,
		Balanced,
		Aggressive,
		Assault
	}

	public enum FransExpansionExposureLevel
	{
		Safe,
		Uncertain,
		Contested
	}

	public readonly record struct FransExpansionExposureAssessment(
		FransExpansionExposureLevel Level,
		int Score,
		int StructureScore,
		int MobileScore,
		int ControlScore,
		int IntelAgeTicks);

	public readonly record struct FransRiskAssessment(
		int Score,
		int VisibleRiskScore,
		int StrategicRiskScore,
		int RememberedStaticRiskScore,
		int IncidentRiskScore,
		int RecentDamageRiskScore,
		bool RecentlyDamaged,
		int VisibleThreatCount,
		int StaticThreatCount,
		int PeakThreatScore,
		int PreferredThreshold,
		int CriticalThreshold)
	{
		public bool IsPreferred => Score <= PreferredThreshold;
		public bool IsCritical => Score >= CriticalThreshold;
	}

	public readonly record struct FransRouteRiskAssessment(
		int PeakScore,
		int AverageScore,
		long TotalScore,
		int CriticalCellCount,
		CPos PeakCell,
		int PreferredThreshold,
		int CriticalThreshold)
	{
		public bool IsCritical => CriticalCellCount > 0 || PeakScore >= CriticalThreshold;
		public bool IsPreferred => PeakScore <= PreferredThreshold;
	}

	/// <summary>
	/// Shared read-only tactical risk service.  It does not issue orders or choose
	/// missions.  Consumers decide their own tolerance and may use the returned path
	/// cost with OpenRA's native PathFinder.
	/// </summary>
	// Fransbot spatial-order contract:
	// Any Frans planner that selects a world-space destination or a route-capable combat target must
	// consult this shared service before issuing the order. Engine-native terminal actions whose
	// destination/corridor was already selected safely (CaptureActor, EnterTransport, Unload,
	// DeployTransform, Repair and ReturnToBase) are not separate threat planners and remain native.
	public interface IFransRiskModelService
	{
		FransRiskAssessment EvaluateCell(Actor subject, CPos cell, FransRiskRole role, FransRiskTolerance tolerance);
		FransRiskAssessment EvaluateImmediateRisk(Actor subject, CPos cell, FransRiskRole role, FransRiskTolerance tolerance);
		FransRiskAssessment EvaluateStrategicCell(CPos cell, FransRiskRole role, FransRiskTolerance tolerance);
		FransExpansionExposureAssessment EvaluateExpansionExposure(CPos cell);
		FransRouteRiskAssessment EvaluateRoute(Actor subject, IReadOnlyList<CPos> path, FransRiskRole role, FransRiskTolerance tolerance);
		FransRouteRiskAssessment EvaluateDirectRoute(Actor subject, CPos from, CPos to, FransRiskRole role, FransRiskTolerance tolerance);
		int GetPathCost(Actor subject, CPos cell, FransRiskRole role, FransRiskTolerance tolerance);
		T ExecuteWithPreparedPathCost<T>(Actor subject, FransRiskRole role, FransRiskTolerance tolerance,
			Func<Func<CPos, int>, T> synchronousSearch);
		void ReportRiskIncident(FransRiskRole role, CPos center, int riskScore, int radiusCells, int durationTicks);
		void ReportGlobalRiskIncident(CPos center, int riskScore, int radiusCells, int durationTicks);
		int SnapshotWorldTick { get; }
		int RiskRevision { get; }
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Shared Fransbot tactical risk layer. Passive service only: converts legitimate visible weapon threats, remembered observed static defenses, strategic-map pressure, reported mission incidents and recent damage into reusable role-aware cell/route risk scores.")]
	public class FransRiskModelBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Base risk added by each visible enemy actor that can actually damage the protected actor.")]
		public readonly int BaseVisibleThreatRisk = 25;

		[Desc("Enemy actor cost is divided by this value and added to its visible threat risk.")]
		public readonly int VisibleThreatValueDivisor = 5;

		[Desc("Maximum cost-derived risk added by one visible enemy actor before static-defense scaling.")]
		public readonly int MaximumVisibleThreatValueRisk = 300;

		[Desc("Aircraft-only risk multiplier for a valid anti-air weapon threat that is not listed as soft AA. 1000 = x10. Ground/MCV/harvester/etc. risk is unchanged.")]
		public readonly int AircraftHardAntiAirRiskPercent = 1000;

		[Desc("Aircraft-only risk multiplier for a valid anti-air weapon threat whose actor type is listed in AircraftSoftAntiAirThreatTypes. 300 = x3.")]
		public readonly int AircraftSoftAntiAirRiskPercent = 300;

		[ActorReference]
		[Desc("AA actor types treated as soft AA for Aircraft risk scaling. Every other actor whose enabled weapon can validly hit the protected aircraft uses AircraftHardAntiAirRiskPercent.")]
		public readonly FrozenSet<string> AircraftSoftAntiAirThreatTypes = FrozenSet<string>.Empty;

		[Desc("Risk multiplier for immobile/building weapon threats, as a percentage.")]
		public readonly int StaticDefenseRiskPercent = 140;

		[Desc("Percentage of full risk applied in the safety buffer immediately outside actual weapon range.")]
		public readonly int BufferRiskPercent = 45;

		[Desc("Percentage of StrategicMap sector threat added as coarse remembered/uncertain risk. Exact hidden actor positions are never queried.")]
		public readonly int StrategicThreatWeightPercent = 30;

		[Desc("Maximum coarse StrategicMap contribution to one cell risk assessment.")]
		public readonly int MaximumStrategicRisk = 120;

		[Desc("Radius in cells used by fair Enemy Territory Likelihood when deciding whether an ore objective is safe, uncertain or contested for MCV expansion.")]
		public readonly int ExpansionTerritoryRadius = 28;

		[Desc("Enemy Territory Likelihood score at/above which an expansion objective requires fresh RECON before an MCV may pioneer it.")]
		public readonly int ExpansionTerritoryUncertainScore = 70;

		[Desc("Enemy Territory Likelihood score at/above which an expansion objective is treated as contested and requires Ground SECURE before MCV entry.")]
		public readonly int ExpansionTerritoryContestedScore = 180;

		[Desc("Base likelihood contributions from remembered enemy construction, production, defense, economy, strategic and other buildings. Confidence and distance scale these scores.")]
		public readonly int ExpansionConstructionStructureScore = 170;
		public readonly int ExpansionProductionStructureScore = 150;
		public readonly int ExpansionDefenseStructureScore = 130;
		public readonly int ExpansionEconomyStructureScore = 90;
		public readonly int ExpansionStrategicStructureScore = 110;
		public readonly int ExpansionOtherStructureScore = 60;

		[Desc("Maximum Enemy Territory Likelihood contribution from remembered/visible mobile combat contacts near an expansion objective.")]
		public readonly int ExpansionMobileCombatMaximumScore = 140;

		[Desc("Percentage of StrategicMap enemy-control score added to Enemy Territory Likelihood, before the configured cap.")]
		public readonly int ExpansionEnemyControlWeightPercent = 50;

		[Desc("Maximum Enemy Territory Likelihood contribution from the coarse StrategicMap enemy-control score.")]
		public readonly int ExpansionEnemyControlMaximumScore = 120;

		[Desc("A sector observed within this many world ticks is considered fresh for Enemy Territory Likelihood diagnostics. Fresh observation can clear uncertainty when no enemy evidence remains, but never erases remembered persistent buildings.")]
		public readonly int ExpansionFreshIntelTicks = 750;

		[Desc("Percentage of cheap sector-based Enemy Territory Likelihood added to MCV path risk, so native pathfinding prefers routes away from likely enemy territory without scanning remembered actors per path cell.")]
		public readonly int McvEnemyTerritoryRiskPercent = 70;

		[Desc("Maximum cheap sector-based enemy-territory risk added to one MCV path cell.")]
		public readonly int MaximumMcvEnemyTerritoryRisk = 260;

		[Desc("Known-beach distance in cells that carries a soft exposure penalty for naval combat ships. Naval transports are deliberately excluded.")]
		public readonly int NavalCombatShoreExposureRadius = 5;

		[Desc("Maximum soft shore-exposure risk next to known beach terrain for naval combat ships. This is intentionally below the normal critical threshold by itself.")]
		public readonly int NavalCombatShoreExposureRisk = 140;

		[Desc("Minimum StrategicMap confidence for a legitimately observed remembered static defense to contribute an exact local risk circle.")]
		public readonly int RememberedStaticDefenseMinimumConfidencePercent = 35;

		[Desc("Percentage of the visible static-defense severity retained for a remembered static defense before confidence scaling.")]
		public readonly int RememberedStaticDefenseRiskPercent = 100;

		[Desc("Maximum remembered-static contribution to one cell risk assessment.")]
		public readonly int MaximumRememberedStaticRisk = 420;

		[Desc("Additional safety buffer in cells outside actual valid enemy weapon range for MCVs.")]
		public readonly int McvRangeBuffer = 2;
		[Desc("Additional safety buffer in cells outside actual valid enemy weapon range for engineers/thieves.")]
		public readonly int CapturerRangeBuffer = 1;
		[Desc("Additional safety buffer in cells outside actual valid anti-air weapon range.")]
		public readonly int AircraftRangeBuffer = 1;
		[Desc("Additional safety buffer for normal ground combat routing.")]
		public readonly int GroundCombatRangeBuffer = 1;
		[Desc("Additional safety buffer for harvesters.")]
		public readonly int HarvesterRangeBuffer = 2;
		[Desc("Additional safety buffer for supply/support vehicles.")]
		public readonly int SupportVehicleRangeBuffer = 2;
		[Desc("Additional safety buffer for minelayers.")]
		public readonly int MinelayerRangeBuffer = 2;
		[Desc("Additional safety buffer used while choosing new building placements.")]
		public readonly int BuildingPlacementRangeBuffer = 1;
		[Desc("Additional safety buffer for specialist auxiliary combat units.")]
		public readonly int AuxiliaryCombatRangeBuffer = 1;
		[Desc("Additional safety buffer for naval transports.")]
		public readonly int NavalTransportRangeBuffer = 2;
		[Desc("Additional safety buffer for naval combat task forces.")]
		public readonly int NavalCombatRangeBuffer = 1;

		[Desc("Preferred/critical base risk thresholds for an MCV mission before tolerance scaling.")]
		public readonly int McvPreferredRisk = 120;
		public readonly int McvCriticalRisk = 360;
		[Desc("Preferred/critical base risk thresholds for engineers and thieves.")]
		public readonly int CapturerPreferredRisk = 70;
		public readonly int CapturerCriticalRisk = 210;
		[Desc("Preferred/critical base risk thresholds for aircraft.")]
		public readonly int AircraftPreferredRisk = 110;
		public readonly int AircraftCriticalRisk = 330;
		[Desc("Preferred/critical base risk thresholds for ordinary ground combat units.")]
		public readonly int GroundCombatPreferredRisk = 180;
		public readonly int GroundCombatCriticalRisk = 500;
		[Desc("Preferred/critical base risk thresholds for harvesters.")]
		public readonly int HarvesterPreferredRisk = 90;
		public readonly int HarvesterCriticalRisk = 260;
		[Desc("Preferred/critical base risk thresholds for supply/support vehicles.")]
		public readonly int SupportVehiclePreferredRisk = 110;
		public readonly int SupportVehicleCriticalRisk = 300;
		[Desc("Preferred/critical base risk thresholds for minelayers.")]
		public readonly int MinelayerPreferredRisk = 140;
		public readonly int MinelayerCriticalRisk = 360;
		[Desc("Preferred/critical base risk thresholds used while choosing building placements.")]
		public readonly int BuildingPlacementPreferredRisk = 220;
		public readonly int BuildingPlacementCriticalRisk = 600;
		[Desc("Preferred/critical base risk thresholds for specialist auxiliary combat units.")]
		public readonly int AuxiliaryCombatPreferredRisk = 180;
		public readonly int AuxiliaryCombatCriticalRisk = 500;
		[Desc("Preferred/critical base risk thresholds for naval transports.")]
		public readonly int NavalTransportPreferredRisk = 110;
		public readonly int NavalTransportCriticalRisk = 330;
		[Desc("Preferred/critical base risk thresholds for naval combat task forces.")]
		public readonly int NavalCombatPreferredRisk = 200;
		public readonly int NavalCombatCriticalRisk = 560;

		[Desc("Cautious threshold multiplier percentage.")]
		public readonly int CautiousTolerancePercent = 80;
		[Desc("Balanced threshold multiplier percentage.")]
		public readonly int BalancedTolerancePercent = 100;
		[Desc("Aggressive threshold multiplier percentage.")]
		public readonly int AggressiveTolerancePercent = 135;
		[Desc("Assault threshold multiplier percentage.")]
		public readonly int AssaultTolerancePercent = 180;

		[Desc("Additional native pathfinding cost per point of non-critical risk.")]
		public readonly int PathCostPerRiskPoint = 40;

		[Desc("If true, a cell at/above the role's critical threshold is a hard no-go for native pathfinding. Non-critical risk remains a soft cost.")]
		public readonly bool HardBlockCriticalRisk = true;

		[Desc("Temporary immediate-risk bonus after the protected actor is observed losing HP. This affects immediate stay/flee decisions, never map-cell path cost.")]
		public readonly int RecentDamageRisk = 250;

		[Desc("World ticks to remember a recent HP loss for immediate-risk decisions.")]
		public readonly int RecentDamageMemoryTicks = 150;

		[Desc("Maximum number of reported role-specific danger incidents retained at once.")]
		public readonly int MaximumRiskIncidents = 64;


		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (BaseVisibleThreatRisk < 0 || VisibleThreatValueDivisor <= 0 || MaximumVisibleThreatValueRisk < 0 ||
				AircraftHardAntiAirRiskPercent <= 0 || AircraftSoftAntiAirRiskPercent <= 0)
				throw new YamlException("RiskModel visible-threat/aircraft-AA scoring values are invalid.");
			if (StaticDefenseRiskPercent <= 0 || BufferRiskPercent < 0 || StrategicThreatWeightPercent < 0 || MaximumStrategicRisk < 0 ||
				RememberedStaticDefenseMinimumConfidencePercent is < 0 or > 100 || RememberedStaticDefenseRiskPercent < 0 || MaximumRememberedStaticRisk < 0)
				throw new YamlException("RiskModel risk multipliers are invalid.");
			if (ExpansionTerritoryRadius <= 0 || ExpansionTerritoryUncertainScore < 0 || ExpansionTerritoryContestedScore <= ExpansionTerritoryUncertainScore ||
				ExpansionConstructionStructureScore < 0 || ExpansionProductionStructureScore < 0 || ExpansionDefenseStructureScore < 0 ||
				ExpansionEconomyStructureScore < 0 || ExpansionStrategicStructureScore < 0 || ExpansionOtherStructureScore < 0 ||
				ExpansionMobileCombatMaximumScore < 0 || ExpansionEnemyControlWeightPercent < 0 || ExpansionEnemyControlMaximumScore < 0 ||
				ExpansionFreshIntelTicks <= 0 || McvEnemyTerritoryRiskPercent < 0 || MaximumMcvEnemyTerritoryRisk < 0 ||
				NavalCombatShoreExposureRadius < 0 || NavalCombatShoreExposureRisk < 0)
				throw new YamlException("RiskModel enemy-territory/shore-exposure settings are invalid.");
			if (McvRangeBuffer < 0 || CapturerRangeBuffer < 0 || AircraftRangeBuffer < 0 || GroundCombatRangeBuffer < 0 ||
				HarvesterRangeBuffer < 0 || SupportVehicleRangeBuffer < 0 || MinelayerRangeBuffer < 0 || BuildingPlacementRangeBuffer < 0 || AuxiliaryCombatRangeBuffer < 0 ||
				NavalTransportRangeBuffer < 0 || NavalCombatRangeBuffer < 0)
				throw new YamlException("RiskModel range buffers cannot be negative.");
			if (McvPreferredRisk < 0 || McvCriticalRisk <= McvPreferredRisk ||
				CapturerPreferredRisk < 0 || CapturerCriticalRisk <= CapturerPreferredRisk ||
				AircraftPreferredRisk < 0 || AircraftCriticalRisk <= AircraftPreferredRisk ||
				GroundCombatPreferredRisk < 0 || GroundCombatCriticalRisk <= GroundCombatPreferredRisk ||
				HarvesterPreferredRisk < 0 || HarvesterCriticalRisk <= HarvesterPreferredRisk ||
				SupportVehiclePreferredRisk < 0 || SupportVehicleCriticalRisk <= SupportVehiclePreferredRisk ||
				MinelayerPreferredRisk < 0 || MinelayerCriticalRisk <= MinelayerPreferredRisk ||
				BuildingPlacementPreferredRisk < 0 || BuildingPlacementCriticalRisk <= BuildingPlacementPreferredRisk ||
				AuxiliaryCombatPreferredRisk < 0 || AuxiliaryCombatCriticalRisk <= AuxiliaryCombatPreferredRisk ||
				NavalTransportPreferredRisk < 0 || NavalTransportCriticalRisk <= NavalTransportPreferredRisk ||
				NavalCombatPreferredRisk < 0 || NavalCombatCriticalRisk <= NavalCombatPreferredRisk)
				throw new YamlException("RiskModel preferred/critical thresholds are invalid.");
			if (CautiousTolerancePercent <= 0 || BalancedTolerancePercent <= 0 || AggressiveTolerancePercent <= 0 || AssaultTolerancePercent <= 0)
				throw new YamlException("RiskModel tolerance percentages must be positive.");
			if (PathCostPerRiskPoint < 0)
				throw new YamlException($"{nameof(PathCostPerRiskPoint)} cannot be negative.");
			if (RecentDamageRisk < 0 || RecentDamageMemoryTicks <= 0)
				throw new YamlException("RiskModel recent-damage settings are invalid.");
			if (MaximumRiskIncidents <= 0)
				throw new YamlException($"{nameof(MaximumRiskIncidents)} must be greater than zero.");
		}

		public override object Create(ActorInitializer init) { return new FransRiskModelBotModule(init.Self, this); }
	}

	public class FransRiskModelBotModule : ConditionalTrait<FransRiskModelBotModuleInfo>, IFransRiskModelService
	{
		readonly record struct ThreatDescriptor(WPos Position, int WeaponRange, int Severity, bool IsStatic, string ActorType);
		readonly record struct RawRisk(int VisibleRisk, int StrategicRisk, int RememberedStaticRisk, int IncidentRisk, int VisibleThreats, int StaticThreats, int PeakThreat);
		readonly record struct CellCacheKey(string ActorType, FransRiskRole Role, CPos Cell);
		readonly record struct StrategicCellCacheKey(FransRiskRole Role, CPos Cell);
		readonly record struct RiskIncident(FransRiskRole Role, CPos Center, int RiskScore, int RadiusCells, int ExpiresWorldTick);


		sealed class DamageObservation
		{
			public int LastHp;
			public int MaxHp;
			public int LastObservedTick;
			public int RecentDamageUntil;
		}

		readonly World world;
		readonly Player player;
		readonly Actor playerActor;
		readonly Dictionary<string, ThreatDescriptor[]> threatCache = [];
		readonly Dictionary<CellCacheKey, RawRisk> cellCache = [];
		readonly Dictionary<StrategicCellCacheKey, RawRisk> strategicCellCache = [];
		readonly Dictionary<CPos, FransExpansionExposureAssessment> expansionExposureCache = [];
		readonly HashSet<uint> visibleEnemyActorIds = [];
		readonly Dictionary<uint, DamageObservation> damageObservations = [];
		readonly List<RiskIncident> riskIncidents = [];
		int nextDamageCleanupTick;
		int riskRevision;

		IFransCombatIntelService combatIntel;
		IFransStrategicMapService strategicMap;
		int cachedCombatSnapshot = int.MinValue;
		int cachedStrategicSnapshot = int.MinValue;

		public FransRiskModelBotModule(Actor self, FransRiskModelBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			playerActor = self;
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			combatIntel = playerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransRiskModelBotModule requires FransCombatIntelBotModule.");
			strategicMap = playerActor.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransRiskModelBotModule requires FransStrategicMapBotModule.");
		}

		protected override void TraitEnabled(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			FransBotLog.BotDebug(world,
				"{0}: FransRiskModel AIRCRAFT AA SCALING active: shared fair-information risk remains passive; valid hard-AA weapon threats are x{1}% and configured soft-AA [{2}] are x{3}% for FransRiskRole.Aircraft only. Other roles keep their existing severity.",
				player, Info.AircraftHardAntiAirRiskPercent / 100, string.Join(",", Info.AircraftSoftAntiAirThreatTypes.OrderBy(x => x)), Info.AircraftSoftAntiAirRiskPercent / 100);
			FransBotLog.BotDebug(world,
				"{0}: FransRiskModel ENEMY TERRITORY + SHORE EXPOSURE active: MCV expansion uses fair remembered structures/mobile contacts/StrategicMap control as Safe-Uncertain-Contested likelihood; MCV path cells use only cheap sector pressure, and NavalCombat receives a soft known-beach exposure cost inside {1} cells from StrategicMap's precomputed O(1) shore-distance cache. No hidden actors or per-cell remembered-actor scans are used by pathfinding.",
				player, Info.NavalCombatShoreExposureRadius);
		}

		public int SnapshotWorldTick => Math.Max(combatIntel?.SnapshotWorldTick ?? -1, strategicMap?.SnapshotWorldTick ?? -1);
		public int RiskRevision
		{
			get
			{
				RefreshCachesIfNeeded();
				return riskRevision;
			}
		}

		public FransRiskAssessment EvaluateCell(Actor subject, CPos cell, FransRiskRole role, FransRiskTolerance tolerance)
		{
			if (subject == null || subject.IsDead || !world.Map.Contains(cell))
				return BuildAssessment(default, role, tolerance, 0, false);

			RefreshCachesIfNeeded();
			return EvaluateCellPrepared(subject, cell, role, tolerance);
		}

		FransRiskAssessment EvaluateCellPrepared(Actor subject, CPos cell, FransRiskRole role, FransRiskTolerance tolerance)
		{
			if (subject == null || subject.IsDead || !world.Map.Contains(cell))
				return BuildAssessment(default, role, tolerance, 0, false);

			var key = new CellCacheKey(subject.Info.Name, role, cell);
			if (!cellCache.TryGetValue(key, out var raw))
			{
				raw = EvaluateRaw(subject, cell, role);
				cellCache[key] = raw;
			}

			return BuildAssessment(raw, role, tolerance, 0, false);
		}

		public FransRiskAssessment EvaluateImmediateRisk(Actor subject, CPos cell, FransRiskRole role, FransRiskTolerance tolerance)
		{
			if (subject == null || subject.IsDead || !world.Map.Contains(cell))
				return BuildAssessment(default, role, tolerance, 0, false);

			RefreshCachesIfNeeded();
			var key = new CellCacheKey(subject.Info.Name, role, cell);
			if (!cellCache.TryGetValue(key, out var raw))
			{
				raw = EvaluateRaw(subject, cell, role);
				cellCache[key] = raw;
			}

			var recentDamageRisk = GetRecentDamageRisk(subject, out var recentlyDamaged);
			return BuildAssessment(raw, role, tolerance, recentDamageRisk, recentlyDamaged);
		}

		public FransRiskAssessment EvaluateStrategicCell(CPos cell, FransRiskRole role, FransRiskTolerance tolerance)
		{
			if (!world.Map.Contains(cell))
				return BuildAssessment(default, role, tolerance, 0, false);

			RefreshCachesIfNeeded();
			var key = new StrategicCellCacheKey(role, cell);
			if (!strategicCellCache.TryGetValue(key, out var raw))
			{
				raw = EvaluateStrategicRaw(cell, role);
				strategicCellCache[key] = raw;
			}

			return BuildAssessment(raw, role, tolerance, 0, false);
		}

		public FransExpansionExposureAssessment EvaluateExpansionExposure(CPos cell)
		{
			if (!world.Map.Contains(cell))
				return new FransExpansionExposureAssessment(FransExpansionExposureLevel.Contested, int.MaxValue, 0, 0, 0, int.MaxValue);

			combatIntel?.EnsureCurrentSnapshot();
			RefreshCachesIfNeeded();
			if (expansionExposureCache.TryGetValue(cell, out var cached))
				return cached;

			var radius = Info.ExpansionTerritoryRadius;
			var radiusSq = radius * radius;
			var structureScore = 0;
			foreach (var memory in strategicMap?.KnownEnemyStructures ?? Array.Empty<FransKnownEnemyStructure>())
			{
				var distanceSq = (memory.LastKnownLocation - cell).LengthSquared;
				if (distanceSq > radiusSq || memory.ConfidencePercent <= 0)
					continue;

				var baseScore = memory.Category switch
				{
					FransKnownStructureCategory.Construction => Info.ExpansionConstructionStructureScore,
					FransKnownStructureCategory.Production => Info.ExpansionProductionStructureScore,
					FransKnownStructureCategory.Defense => Info.ExpansionDefenseStructureScore,
					FransKnownStructureCategory.Economy => Info.ExpansionEconomyStructureScore,
					FransKnownStructureCategory.Strategic => Info.ExpansionStrategicStructureScore,
					_ => Info.ExpansionOtherStructureScore
				};
				var distance = (int)Math.Sqrt(distanceSq);
				var distancePercent = Math.Max(15, (radius - Math.Min(radius, distance) + 1) * 100 / Math.Max(1, radius + 1));
				var contribution = (long)baseScore * memory.ConfidencePercent / 100 * distancePercent / 100;
				structureScore = (int)Math.Min(int.MaxValue, structureScore + Math.Max(1L, contribution));
			}

			var mobileScore = 0;
			if (combatIntel?.EnemyCombatContacts != null)
				foreach (var contact in combatIntel.EnemyCombatContacts)
				{
					if (contact.IsBuilding || contact.EstimatedValue <= 0 || (contact.LastSeenCell - cell).LengthSquared > radiusSq)
						continue;
					var contribution = Math.Clamp(contact.EstimatedValue / 20, 1, 50);
					mobileScore = Math.Min(Info.ExpansionMobileCombatMaximumScore, mobileScore + contribution);
					if (mobileScore >= Info.ExpansionMobileCombatMaximumScore)
						break;
				}

			var controlScore = 0;
			var intelAge = int.MaxValue;
			if (strategicMap != null)
			{
				if (strategicMap.TryGetSectorMetrics(cell, out var metrics) && metrics.EnemyControlScore > 0)
					controlScore = Math.Min(Info.ExpansionEnemyControlMaximumScore, metrics.EnemyControlScore * Info.ExpansionEnemyControlWeightPercent / 100);
				if (strategicMap.TryGetSector(cell, out var sector) && sector.LastObservedWorldTick >= 0)
					intelAge = Math.Max(0, world.WorldTick - sector.LastObservedWorldTick);
			}

			var score = (int)Math.Min(int.MaxValue, (long)structureScore + mobileScore + controlScore);
			var level = score >= Info.ExpansionTerritoryContestedScore
				? FransExpansionExposureLevel.Contested
				: score >= Info.ExpansionTerritoryUncertainScore
					? FransExpansionExposureLevel.Uncertain
					: FransExpansionExposureLevel.Safe;

			// Fresh direct observation with no persistent structure/mobile evidence is explicit evidence
			// that old coarse sector pressure should not keep a harmless ore site permanently uncertain.
			if (intelAge <= Info.ExpansionFreshIntelTicks && structureScore == 0 && mobileScore == 0 &&
				level == FransExpansionExposureLevel.Uncertain)
				level = FransExpansionExposureLevel.Safe;

			var result = new FransExpansionExposureAssessment(level, score, structureScore, mobileScore, controlScore, intelAge);
			expansionExposureCache[cell] = result;
			return result;
		}

		public FransRouteRiskAssessment EvaluateRoute(Actor subject, IReadOnlyList<CPos> path, FransRiskRole role, FransRiskTolerance tolerance)
		{
			GetThresholds(role, tolerance, out var preferred, out var critical);
			if (path == null || path.Count == 0)
				return new FransRouteRiskAssessment(0, 0, 0, 0, subject?.Location ?? CPos.Zero, preferred, critical);

			if (subject != null && !subject.IsDead && path.Any(world.Map.Contains))
				RefreshCachesIfNeeded();

			var peak = 0;
			var peakCell = path[0];
			long total = 0;
			var criticalCells = 0;
			foreach (var cell in path)
			{
				var risk = EvaluateCellPrepared(subject, cell, role, tolerance);
				total += risk.Score;
				if (risk.Score > peak)
				{
					peak = risk.Score;
					peakCell = cell;
				}

				if (risk.IsCritical)
					criticalCells++;
			}

			return new FransRouteRiskAssessment(peak, (int)(total / path.Count), total, criticalCells, peakCell, preferred, critical);
		}

		public FransRouteRiskAssessment EvaluateDirectRoute(Actor subject, CPos from, CPos to, FransRiskRole role, FransRiskTolerance tolerance)
		{
			var line = LineCells(from, to).Where(world.Map.Contains).ToArray();
			return EvaluateRoute(subject, line, role, tolerance);
		}

		public int GetPathCost(Actor subject, CPos cell, FransRiskRole role, FransRiskTolerance tolerance)
		{
			return ConvertToPathCost(EvaluateCell(subject, cell, role, tolerance));
		}

		public T ExecuteWithPreparedPathCost<T>(Actor subject, FransRiskRole role, FransRiskTolerance tolerance,
			Func<Func<CPos, int>, T> synchronousSearch)
		{
			if (synchronousSearch == null)
				throw new ArgumentNullException(nameof(synchronousSearch));

			// Native pathfinding is synchronous: refresh immediately before it starts, then
			// keep every callback on the same prepared snapshot/cache state for this call only.
			RefreshCachesIfNeeded();
			int PreparedPathCost(CPos cell) => ConvertToPathCost(EvaluateCellPrepared(subject, cell, role, tolerance));
			return synchronousSearch(PreparedPathCost);
		}

		int ConvertToPathCost(FransRiskAssessment risk)
		{
			if (Info.HardBlockCriticalRisk && risk.IsCritical)
				return PathGraph.PathCostForInvalidPath;

			if (risk.Score <= 0 || Info.PathCostPerRiskPoint == 0)
				return 0;

			var cost = (long)risk.Score * Info.PathCostPerRiskPoint;
			return (int)Math.Min(PathGraph.PathCostForInvalidPath - 1L, cost);
		}

		public void ReportRiskIncident(FransRiskRole role, CPos center, int riskScore, int radiusCells, int durationTicks)
		{
			if (!world.Map.Contains(center) || riskScore <= 0 || radiusCells <= 0 || durationTicks <= 0)
				return;

			CleanupRiskIncidents();
			riskIncidents.Add(new RiskIncident(role, center, riskScore, radiusCells, world.WorldTick + durationTicks));
			if (riskIncidents.Count > Info.MaximumRiskIncidents)
				riskIncidents.RemoveRange(0, riskIncidents.Count - Info.MaximumRiskIncidents);

			riskRevision++;
			cellCache.Clear();
			strategicCellCache.Clear();
			expansionExposureCache.Clear();
		}

		public void ReportGlobalRiskIncident(CPos center, int riskScore, int radiusCells, int durationTicks)
		{
			if (!world.Map.Contains(center) || riskScore <= 0 || radiusCells <= 0 || durationTicks <= 0)
				return;

			CleanupRiskIncidents();
			var expires = world.WorldTick + durationTicks;
			foreach (FransRiskRole role in Enum.GetValues(typeof(FransRiskRole)))
				riskIncidents.Add(new RiskIncident(role, center, riskScore, radiusCells, expires));

			if (riskIncidents.Count > Info.MaximumRiskIncidents)
				riskIncidents.RemoveRange(0, riskIncidents.Count - Info.MaximumRiskIncidents);

			riskRevision++;
			cellCache.Clear();
			strategicCellCache.Clear();
			expansionExposureCache.Clear();
		}


		void RefreshCachesIfNeeded()
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "Risk.RefreshCaches");
			var combatSnapshot = combatIntel?.SnapshotWorldTick ?? -1;
			var strategicSnapshot = strategicMap?.SnapshotWorldTick ?? -1;
			if (combatSnapshot == cachedCombatSnapshot && strategicSnapshot == cachedStrategicSnapshot)
				return;

			cachedCombatSnapshot = combatSnapshot;
			cachedStrategicSnapshot = strategicSnapshot;
			riskRevision++;
			threatCache.Clear();
			cellCache.Clear();
			strategicCellCache.Clear();
			expansionExposureCache.Clear();
			visibleEnemyActorIds.Clear();
			if (combatIntel?.VisibleEnemies != null)
				foreach (var enemy in combatIntel.VisibleEnemies)
					if (enemy != null && enemy.IsInWorld && !enemy.IsDead)
						visibleEnemyActorIds.Add(enemy.ActorID);
		}

		RawRisk EvaluateRaw(Actor subject, CPos cell, FransRiskRole role)
		{
			var visibleRisk = 0;
			var strategicRisk = 0;
			var rememberedStaticRisk = 0;
			var incidentRisk = 0;
			var visibleThreats = 0;
			var staticThreats = 0;
			var peakThreat = 0;
			var buffer = WDist.FromCells(BufferCells(role)).Length;
			var position = world.Map.CenterOfCell(cell);

			foreach (var threat in GetThreats(subject))
			{
				var distanceSquared = (threat.Position - position).HorizontalLengthSquared;
				var weaponRange = (long)threat.WeaponRange;
				var outerRange = weaponRange + buffer;
				if (distanceSquared > outerRange * outerRange)
					continue;

				var contribution = threat.Severity;
				if (distanceSquared > weaponRange * weaponRange)
					contribution = contribution * Info.BufferRiskPercent / 100;
				if (role == FransRiskRole.Aircraft)
					contribution = ScaleAircraftAntiAirRisk(contribution, threat.ActorType);

				if (contribution <= 0)
					continue;

				visibleRisk += contribution;
				visibleThreats++;
				if (threat.IsStatic)
					staticThreats++;
				peakThreat = Math.Max(peakThreat, contribution);
			}

			if (strategicMap != null && strategicMap.TryGetSectorMetrics(cell, out var metrics))
			{
				if (metrics.ThreatScore > 0)
					strategicRisk = Math.Min(Info.MaximumStrategicRisk, metrics.ThreatScore * Info.StrategicThreatWeightPercent / 100);

				if (role == FransRiskRole.Mcv && Info.McvEnemyTerritoryRiskPercent > 0 && Info.MaximumMcvEnemyTerritoryRisk > 0)
				{
					// Cheap sector-only pressure for pathfinding. Do not iterate remembered actors here:
					// native A* may ask for thousands of cell costs in one planning pass.
					var territoryBase = Math.Max(0, metrics.EnemyControlScore) +
						Math.Max(0, metrics.VisibleEnemyCombatUnitCount) * 20;
					var territoryRisk = Math.Min(Info.MaximumMcvEnemyTerritoryRisk, territoryBase * Info.McvEnemyTerritoryRiskPercent / 100);
					strategicRisk = (int)Math.Min(int.MaxValue, (long)strategicRisk + territoryRisk);
				}
			}

			if (role == FransRiskRole.NavalCombat && strategicMap != null && Info.NavalCombatShoreExposureRadius > 0 && Info.NavalCombatShoreExposureRisk > 0)
			{
				var beachDistance = strategicMap.GetKnownBeachDistance(cell, Info.NavalCombatShoreExposureRadius);
				if (beachDistance >= 0)
				{
					var shoreRisk = Info.NavalCombatShoreExposureRisk *
						(Info.NavalCombatShoreExposureRadius - Math.Min(beachDistance, Info.NavalCombatShoreExposureRadius) + 1) /
						(Info.NavalCombatShoreExposureRadius + 1);
					strategicRisk = (int)Math.Min(int.MaxValue, (long)strategicRisk + Math.Max(1, shoreRisk));
				}
			}

			rememberedStaticRisk = EvaluateRememberedStaticRisk(subject, cell, role);

			CleanupRiskIncidents();
			foreach (var incident in riskIncidents)
			{
				if (incident.Role != role)
					continue;

				var radiusSquared = incident.RadiusCells * incident.RadiusCells;
				if ((incident.Center - cell).LengthSquared <= radiusSquared)
					incidentRisk = Math.Max(incidentRisk, incident.RiskScore);
			}


			return new RawRisk(visibleRisk, strategicRisk, rememberedStaticRisk, incidentRisk, visibleThreats, staticThreats, peakThreat);
		}

		ThreatDescriptor[] GetThreats(Actor subject)
		{
			if (threatCache.TryGetValue(subject.Info.Name, out var cached))
				return cached;

			var threats = new List<ThreatDescriptor>();
			var enemies = combatIntel?.VisibleEnemies;
			if (enemies == null)
			{
				threatCache[subject.Info.Name] = [];
				return [];
			}

			var target = Target.FromActor(subject);
			foreach (var enemy in enemies)
			{
				if (enemy == null || !enemy.IsInWorld || enemy.IsDead || enemy.Owner == null ||
					!PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(enemy.Owner)))
					continue;

				var maxRange = 0;
				var hasValidWeapon = false;
				foreach (var attack in enemy.TraitsImplementing<AttackBase>())
				{
					if (attack.IsTraitDisabled || attack.IsTraitPaused)
						continue;

					foreach (var armament in attack.Armaments)
					{
						if (armament.IsTraitDisabled || armament.IsTraitPaused ||
							!armament.Weapon.IsValidAgainst(target, world, enemy))
							continue;

						hasValidWeapon = true;
						maxRange = Math.Max(maxRange, armament.MaxRange().Length);
					}
				}

				if (!hasValidWeapon || maxRange <= 0)
					continue;

				var actorCost = Math.Max(1, enemy.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1);
				var valueRisk = Math.Min(Info.MaximumVisibleThreatValueRisk, actorCost / Info.VisibleThreatValueDivisor);
				var severity = Info.BaseVisibleThreatRisk + valueRisk;
				var isStatic = enemy.Info.HasTraitInfo<BuildingInfo>();
				if (isStatic)
					severity = severity * Info.StaticDefenseRiskPercent / 100;

				threats.Add(new ThreatDescriptor(enemy.CenterPosition, maxRange, Math.Max(1, severity), isStatic, enemy.Info.Name));
			}

			cached = threats.ToArray();
			threatCache[subject.Info.Name] = cached;
			return cached;
		}

		RawRisk EvaluateStrategicRaw(CPos cell, FransRiskRole role)
		{
			var strategicRisk = 0;
			var rememberedStaticRisk = 0;
			var incidentRisk = 0;
			if (strategicMap != null && strategicMap.TryGetSectorMetrics(cell, out var metrics) && metrics.ThreatScore > 0)
				strategicRisk = Math.Min(Info.MaximumStrategicRisk, metrics.ThreatScore * Info.StrategicThreatWeightPercent / 100);

			if (role == FransRiskRole.NavalCombat && strategicMap != null && Info.NavalCombatShoreExposureRadius > 0 && Info.NavalCombatShoreExposureRisk > 0)
			{
				var beachDistance = strategicMap.GetKnownBeachDistance(cell, Info.NavalCombatShoreExposureRadius);
				if (beachDistance >= 0)
					strategicRisk += Math.Max(1, Info.NavalCombatShoreExposureRisk *
						(Info.NavalCombatShoreExposureRadius - Math.Min(beachDistance, Info.NavalCombatShoreExposureRadius) + 1) /
						(Info.NavalCombatShoreExposureRadius + 1));
			}

			rememberedStaticRisk = EvaluateRememberedStaticRisk(null, cell, role);
			CleanupRiskIncidents();
			foreach (var incident in riskIncidents)
				if (incident.Role == role && (incident.Center - cell).LengthSquared <= incident.RadiusCells * incident.RadiusCells)
					incidentRisk = Math.Max(incidentRisk, incident.RiskScore);

			return new RawRisk(0, strategicRisk, rememberedStaticRisk, incidentRisk, 0, 0, 0);
		}

		int EvaluateRememberedStaticRisk(Actor subject, CPos cell, FransRiskRole role)
		{
			if (strategicMap == null || Info.RememberedStaticDefenseRiskPercent <= 0 || Info.MaximumRememberedStaticRisk <= 0)
				return 0;

			var hasTargetTypes = subject != null;
			var targetTypes = hasTargetTypes ? subject.GetEnabledTargetTypes() : default;
			var cellLength = Math.Max(1, WDist.FromCells(1).Length);
			var bufferWorld = WDist.FromCells(BufferCells(role)).Length;
			var total = 0;
			foreach (var memory in strategicMap.KnownEnemyStructures)
			{
				// A currently visible defense is already represented by the exact live-weapon layer.
				// Never count the same actor again through StrategicMap memory.
				if (visibleEnemyActorIds.Contains(memory.ActorId) ||
					memory.Category != FransKnownStructureCategory.Defense ||
					memory.ConfidencePercent < Info.RememberedStaticDefenseMinimumConfidencePercent ||
					!world.Map.Rules.Actors.TryGetValue(memory.ActorType, out var actorInfo))
					continue;

				var maxRange = 0;
				var canThreatenRole = false;
				foreach (var armamentInfo in actorInfo.TraitInfos<ArmamentInfo>())
				{
					if (armamentInfo.WeaponInfo == null)
						continue;
					if (hasTargetTypes && !armamentInfo.WeaponInfo.IsValidTarget(targetTypes))
						continue;
					canThreatenRole = true;
					maxRange = Math.Max(maxRange, armamentInfo.ModifiedRange.Length);
				}

				if (!canThreatenRole || maxRange <= 0)
					continue;

				var radiusCells = Math.Max(1, (maxRange + bufferWorld + cellLength - 1) / cellLength);
				if ((memory.LastKnownLocation - cell).LengthSquared > radiusCells * radiusCells)
					continue;

				var actorCost = Math.Max(1, actorInfo.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1);
				var valueRisk = Math.Min(Info.MaximumVisibleThreatValueRisk, actorCost / Info.VisibleThreatValueDivisor);
				var severity = (Info.BaseVisibleThreatRisk + valueRisk) * Info.StaticDefenseRiskPercent / 100;
				severity = severity * Info.RememberedStaticDefenseRiskPercent / 100;
				// Confidence decays remembered severity, but never below the configured admission confidence.
				severity = severity * Math.Max(Info.RememberedStaticDefenseMinimumConfidencePercent, memory.ConfidencePercent) / 100;
				if (role == FransRiskRole.Aircraft)
					severity = ScaleAircraftAntiAirRisk(severity, memory.ActorType);
				total += Math.Max(1, severity);
				if (total >= Info.MaximumRememberedStaticRisk)
					return Info.MaximumRememberedStaticRisk;
			}

			return Math.Min(Info.MaximumRememberedStaticRisk, total);
		}


		int ScaleAircraftAntiAirRisk(int severity, string threatActorType)
		{
			if (severity <= 0)
				return 0;

			var percent = Info.AircraftSoftAntiAirThreatTypes.Contains(threatActorType)
				? Info.AircraftSoftAntiAirRiskPercent
				: Info.AircraftHardAntiAirRiskPercent;
			return (int)Math.Min(int.MaxValue, Math.Max(1L, (long)severity * percent / 100));
		}

		static IEnumerable<CPos> LineCells(CPos from, CPos to)
		{
			var x0 = from.X;
			var y0 = from.Y;
			var x1 = to.X;
			var y1 = to.Y;
			var dx = Math.Abs(x1 - x0);
			var sx = x0 < x1 ? 1 : -1;
			var dy = -Math.Abs(y1 - y0);
			var sy = y0 < y1 ? 1 : -1;
			var error = dx + dy;
			while (true)
			{
				yield return new CPos(x0, y0);
				if (x0 == x1 && y0 == y1)
					yield break;
				var e2 = 2 * error;
				if (e2 >= dy) { error += dy; x0 += sx; }
				if (e2 <= dx) { error += dx; y0 += sy; }
			}
		}

		void CleanupRiskIncidents()
		{
			var removed = false;
			if (riskIncidents.Count > 0)
				removed |= riskIncidents.RemoveAll(i => world.WorldTick >= i.ExpiresWorldTick) > 0;

			if (removed)
			{
				riskRevision++;
				cellCache.Clear();
				strategicCellCache.Clear();
				expansionExposureCache.Clear();
			}
		}

		int GetRecentDamageRisk(Actor subject, out bool recentlyDamaged)
		{
			recentlyDamaged = false;
			var health = subject.TraitOrDefault<Health>();
			if (health == null)
				return 0;

			if (world.WorldTick >= nextDamageCleanupTick)
			{
				nextDamageCleanupTick = world.WorldTick + Math.Max(1000, Info.RecentDamageMemoryTicks * 4);
				var expiry = world.WorldTick - Math.Max(1000, Info.RecentDamageMemoryTicks * 4);
				foreach (var actorId in damageObservations.Where(kv => kv.Value.LastObservedTick < expiry).Select(kv => kv.Key).ToArray())
					damageObservations.Remove(actorId);
			}

			if (!damageObservations.TryGetValue(subject.ActorID, out var observation) || observation.MaxHp != health.MaxHP)
			{
				observation = new DamageObservation
				{
					LastHp = health.HP,
					MaxHp = health.MaxHP,
					LastObservedTick = world.WorldTick,
					RecentDamageUntil = int.MinValue
				};
				damageObservations[subject.ActorID] = observation;
				return 0;
			}

			if (health.HP < observation.LastHp)
				observation.RecentDamageUntil = world.WorldTick + Info.RecentDamageMemoryTicks;

			observation.LastHp = health.HP;
			observation.MaxHp = health.MaxHP;
			observation.LastObservedTick = world.WorldTick;
			recentlyDamaged = world.WorldTick <= observation.RecentDamageUntil;
			return recentlyDamaged ? Info.RecentDamageRisk : 0;
		}

		FransRiskAssessment BuildAssessment(RawRisk raw, FransRiskRole role, FransRiskTolerance tolerance, int recentDamageRisk, bool recentlyDamaged)
		{
			GetThresholds(role, tolerance, out var preferred, out var critical);
			var total = raw.VisibleRisk + raw.StrategicRisk + raw.RememberedStaticRisk + raw.IncidentRisk + recentDamageRisk;
			return new FransRiskAssessment(total, raw.VisibleRisk, raw.StrategicRisk, raw.RememberedStaticRisk, raw.IncidentRisk, recentDamageRisk, recentlyDamaged,
				raw.VisibleThreats, raw.StaticThreats, raw.PeakThreat, preferred, critical);
		}

		void GetThresholds(FransRiskRole role, FransRiskTolerance tolerance, out int preferred, out int critical)
		{
			(preferred, critical) = role switch
			{
				FransRiskRole.Mcv => (Info.McvPreferredRisk, Info.McvCriticalRisk),
				FransRiskRole.Capturer => (Info.CapturerPreferredRisk, Info.CapturerCriticalRisk),
				FransRiskRole.Aircraft => (Info.AircraftPreferredRisk, Info.AircraftCriticalRisk),
				FransRiskRole.GroundCombat => (Info.GroundCombatPreferredRisk, Info.GroundCombatCriticalRisk),
				FransRiskRole.Harvester => (Info.HarvesterPreferredRisk, Info.HarvesterCriticalRisk),
				FransRiskRole.SupportVehicle => (Info.SupportVehiclePreferredRisk, Info.SupportVehicleCriticalRisk),
				FransRiskRole.Minelayer => (Info.MinelayerPreferredRisk, Info.MinelayerCriticalRisk),
				FransRiskRole.BuildingPlacement => (Info.BuildingPlacementPreferredRisk, Info.BuildingPlacementCriticalRisk),
				FransRiskRole.AuxiliaryCombat => (Info.AuxiliaryCombatPreferredRisk, Info.AuxiliaryCombatCriticalRisk),
				FransRiskRole.NavalTransport => (Info.NavalTransportPreferredRisk, Info.NavalTransportCriticalRisk),
				FransRiskRole.NavalCombat => (Info.NavalCombatPreferredRisk, Info.NavalCombatCriticalRisk),
				_ => (Info.GroundCombatPreferredRisk, Info.GroundCombatCriticalRisk)
			};

			var percent = tolerance switch
			{
				FransRiskTolerance.Cautious => Info.CautiousTolerancePercent,
				FransRiskTolerance.Balanced => Info.BalancedTolerancePercent,
				FransRiskTolerance.Aggressive => Info.AggressiveTolerancePercent,
				FransRiskTolerance.Assault => Info.AssaultTolerancePercent,
				_ => Info.BalancedTolerancePercent
			};

			preferred = Math.Max(1, preferred * percent / 100);
			critical = Math.Max(preferred + 1, critical * percent / 100);
		}

		int BufferCells(FransRiskRole role)
		{
			return role switch
			{
				FransRiskRole.Mcv => Info.McvRangeBuffer,
				FransRiskRole.Capturer => Info.CapturerRangeBuffer,
				FransRiskRole.Aircraft => Info.AircraftRangeBuffer,
				FransRiskRole.GroundCombat => Info.GroundCombatRangeBuffer,
				FransRiskRole.Harvester => Info.HarvesterRangeBuffer,
				FransRiskRole.SupportVehicle => Info.SupportVehicleRangeBuffer,
				FransRiskRole.Minelayer => Info.MinelayerRangeBuffer,
				FransRiskRole.BuildingPlacement => Info.BuildingPlacementRangeBuffer,
				FransRiskRole.AuxiliaryCombat => Info.AuxiliaryCombatRangeBuffer,
				FransRiskRole.NavalTransport => Info.NavalTransportRangeBuffer,
				FransRiskRole.NavalCombat => Info.NavalCombatRangeBuffer,
				_ => Info.GroundCombatRangeBuffer
			};
		}
	}
}
