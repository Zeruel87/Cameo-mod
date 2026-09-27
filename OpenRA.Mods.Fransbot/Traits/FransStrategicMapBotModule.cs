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
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	/// <summary>
	/// Describes which information the strategic map is legitimately allowed to know.
	/// This is derived from OpenRA's live Shroud trait, not from a duplicated lobby setting.
	/// </summary>
	public enum FransStrategicKnowledgeMode
	{
		ProgressiveShroudWithFog,
		ProgressiveShroudWithoutFog,
		ExploredMapWithFog,
		FullVisibility
	}

	public enum FransStrategicMovementLayer
	{
		Ground,
		Mcv,
		Naval
	}

	public enum FransStrategicRoutePolicy
	{
		Fast,
		Safe,
		Assault
	}

	/// <summary>
	/// Natural strategic stabilization locations that a Commander may use as an ANCHOR POINT.
	/// StrategicMap only identifies candidates; General chooses one for each mission and RiskModel
	/// validates whether it is currently suitable for the requesting combat domain.
	/// </summary>
	public enum FransAnchorPointKind
	{
		FriendlyControl,
		Choke,
		Base,
		SecuredFoothold
	}

	public readonly record struct FransAnchorPointCandidate(
		CPos Cell,
		FransAnchorPointKind Kind,
		int StrategicScore);

	public enum FransKnownStructureCategory
	{
		Other,
		Construction,
		Economy,
		Production,
		Defense,
		Strategic
	}

	public enum FransStrategicObjectiveControl
	{
		Neutral,
		Own,
		Ally,
		Enemy
	}

	/// <summary>
	/// Immutable public snapshot of one coarse strategic map sector.
	/// This is deliberately a strategic abstraction, not a replacement for OpenRA pathfinding.
	/// </summary>
	public sealed class FransStrategicSector
	{
		public int Id { get; }
		public CPos Center { get; }
		public CPos? GroundCenter { get; }
		public CPos? McvCenter { get; }
		public CPos? NavalCenter { get; }

		public int TotalCellCount { get; }
		public int KnownCellCount { get; }
		public int GroundPassableCellCount { get; }
		public int McvPassableCellCount { get; }
		public int NavalPassableCellCount { get; }
		public int BeachCellCount { get; }

		public IReadOnlyList<int> GroundNeighbors { get; }
		public IReadOnlyList<int> McvNeighbors { get; }
		public IReadOnlyList<int> NavalNeighbors { get; }

		public bool IsGroundChokeCandidate { get; }
		public bool IsBeachheadCandidate { get; }

		public int LastObservedWorldTick { get; }
		public int LastExplorationChangeWorldTick { get; }

		public int KnownResourceCreatorCount { get; }
		public int KnownEnemyStructureCount { get; }
		public int OwnedStructureCount { get; }

		public FransStrategicSector(
			int id,
			CPos center,
			CPos? groundCenter,
			CPos? mcvCenter,
			CPos? navalCenter,
			int totalCellCount,
			int knownCellCount,
			int groundPassableCellCount,
			int mcvPassableCellCount,
			int navalPassableCellCount,
			int beachCellCount,
			int[] groundNeighbors,
			int[] mcvNeighbors,
			int[] navalNeighbors,
			bool isGroundChokeCandidate,
			bool isBeachheadCandidate,
			int lastObservedWorldTick,
			int lastExplorationChangeWorldTick,
			int knownResourceCreatorCount,
			int knownEnemyStructureCount,
			int ownedStructureCount)
		{
			Id = id;
			Center = center;
			GroundCenter = groundCenter;
			McvCenter = mcvCenter;
			NavalCenter = navalCenter;
			TotalCellCount = totalCellCount;
			KnownCellCount = knownCellCount;
			GroundPassableCellCount = groundPassableCellCount;
			McvPassableCellCount = mcvPassableCellCount;
			NavalPassableCellCount = navalPassableCellCount;
			BeachCellCount = beachCellCount;
			GroundNeighbors = groundNeighbors;
			McvNeighbors = mcvNeighbors;
			NavalNeighbors = navalNeighbors;
			IsGroundChokeCandidate = isGroundChokeCandidate;
			IsBeachheadCandidate = isBeachheadCandidate;
			LastObservedWorldTick = lastObservedWorldTick;
			LastExplorationChangeWorldTick = lastExplorationChangeWorldTick;
			KnownResourceCreatorCount = knownResourceCreatorCount;
			KnownEnemyStructureCount = knownEnemyStructureCount;
			OwnedStructureCount = ownedStructureCount;
		}
	}

	public readonly record struct FransKnownEnemyStructure(
		uint ActorId,
		string ActorType,
		Player Owner,
		CPos LastKnownLocation,
		int LastSeenWorldTick,
		int ConfidencePercent,
		FransKnownStructureCategory Category);

	public readonly record struct FransKnownResourceCreator(
		uint ActorId,
		string ActorType,
		CPos LastKnownLocation,
		int LastSeenWorldTick);

	/// <summary>
	/// Last legitimately observed state of a capturable/strategic objective. Ownership is
	/// remembered under fog exactly like enemy structures; hidden ownership changes are not read.
	/// </summary>
	public readonly record struct FransKnownStrategicObjective(
		uint ActorId,
		string ActorType,
		CPos LastKnownLocation,
		int LastSeenWorldTick,
		int ConfidencePercent,
		FransStrategicObjectiveControl Control,
		int StrategicValueScore);


	/// <summary>
	/// Dynamic strategic interpretation layered on top of the immutable terrain sector.
	/// Scores are intentionally coarse and relative: consumers should compare sectors,
	/// not treat these values as exact combat simulation.
	/// </summary>
	public readonly record struct FransStrategicSectorMetrics(
		int SectorId,
		int CentralityPercent,
		int ResourceValueScore,
		int StrategicObjectiveValueScore,
		int ThreatScore,
		int OwnControlScore,
		int EnemyControlScore,
		int VisibleEnemyCombatUnitCount,
		int OwnedRefineryCount,
		int OwnedMilitaryProductionCount,
		int OwnStrategicObjectiveCount,
		int AlliedStrategicObjectiveCount,
		int EnemyStrategicObjectiveCount,
		int NeutralStrategicObjectiveCount,
		int FrontlineScore,
		int LocalRefineryCount,
		int LocalMilitaryProductionCount,
		int LocalProductionPressurePercent,
		int GroundChokeScore,
		bool IsGroundArticulationPoint,
		bool IsHighValueResourceSector,
		bool IsContestedResourceSector,
		bool IsStrategicObjectiveSector,
		bool IsFrontlineSector,
		bool NeedsLocalProductionCapacity);

	/// <summary>
	/// Ranked general-purpose strategic sector for future Squad/BaseBuilder/MCV consumers.
	/// Enemy/neutral objectives, resources and frontlines can all contribute to the score.
	/// </summary>
	public readonly record struct FransStrategicPrioritySector(
		int SectorId,
		CPos Target,
		int TotalScore,
		int ResourceValueScore,
		int StrategicObjectiveValueScore,
		int FrontlineScore,
		int ThreatScore,
		int EnemyControlScore,
		int EnemyStrategicObjectiveCount,
		int NeutralStrategicObjectiveCount,
		bool IsHighValueResourceSector,
		bool IsStrategicObjectiveSector,
		bool IsFrontlineSector,
		CPos? SuggestedStagingPoint);

	/// <summary>
	/// Replay-derived capacity diagnostic. This does not build anything by itself.
	/// It lets economy/production consumers see when refinery growth has outrun the number
	/// of military producers capable of converting that income into units.
	/// </summary>
	public readonly record struct FransStrategicProductionPressure(
		int RefineryCount,
		int VehicleProducerCount,
		int InfantryProducerCount,
		int HelicopterProducerCount,
		int PlaneProducerCount,
		int NavalProducerCount,
		int TotalMilitaryProducerCount,
		int SuggestedMinimumMilitaryProducerCount,
		int ProducerDeficit,
		int PressurePercent,
		bool NeedsMoreProductionCapacity);

	/// <summary>
	/// Static/fair terrain topology handoff for amphibious Ground logistics.
	/// GroundCell and NavalCell are adjacent known passable cells; ids are rebuilt only when
	/// legitimate terrain knowledge changes, so consumers never need runtime pathfinding just
	/// to discover whether two land masses share a usable sea region.
	/// </summary>
	public readonly record struct FransGroundShoreAccess(
		int GroundLandmassId,
		int NavalRegionId,
		CPos GroundCell,
		CPos NavalCell);

	/// <summary>
	/// Read-only coordination surface for Frans modules.
	/// Adds shared objective/frontline/local-capacity context while remaining strictly read-only.
	/// </summary>
	public interface IFransStrategicMapService
	{
		FransStrategicKnowledgeMode KnowledgeMode { get; }
		bool ExploreMapEnabled { get; }
		bool FogEnabled { get; }

		IReadOnlyList<FransStrategicSector> Sectors { get; }
		IReadOnlyList<FransStrategicSectorMetrics> SectorMetrics { get; }
		IReadOnlyList<FransKnownEnemyStructure> KnownEnemyStructures { get; }

		int SnapshotWorldTick { get; }
		int TerrainKnowledgeVersion { get; }

		bool IsTerrainKnown(CPos cell);
		bool TryGetSector(CPos cell, out FransStrategicSector sector);
		bool TryGetSectorMetrics(CPos cell, out FransStrategicSectorMetrics metrics);


		IReadOnlyList<FransStrategicPrioritySector> GetStrategicPrioritySectors(int maximumCount);
		IReadOnlyList<FransAnchorPointCandidate> GetAnchorPointCandidates(FransStrategicMovementLayer movementLayer, int maximumCount);

		/// <summary>
		/// Returns a coarse sector route only. Consumers must still let OpenRA's native
		/// pathfinder validate and execute movement between the returned waypoints.
		/// </summary>
		bool TryGetStrategicSectorRoute(
			CPos from,
			CPos to,
			FransStrategicMovementLayer movementLayer,
			out IReadOnlyList<CPos> waypoints);

		bool TryGetStrategicSectorRoute(
			CPos from,
			CPos to,
			FransStrategicMovementLayer movementLayer,
			FransStrategicRoutePolicy routePolicy,
			out IReadOnlyList<CPos> waypoints);

		bool TryGetGroundLandmassId(CPos cell, out int landmassId);
		bool TryGetNavalRegionId(CPos cell, out int navalRegionId);
		int GetKnownBeachDistance(CPos cell, int maximumDistance);
		IReadOnlyList<FransGroundShoreAccess> GetGroundShoreAccess(int groundLandmassId);

	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Read-only strategic battlefield model for Fransbot. Adds objective memory, frontline scoring and local " +
		"economy-vs-production pressure alongside resource/route/expansion analysis and never issues orders.")]
	public class FransStrategicMapBotModuleInfo : ConditionalTraitInfo, Requires<ShroudInfo>
	{
		[Desc("Width/height of one coarse strategic sector in map cells.")]
		public readonly int SectorSize = 8;

		[Desc("World ticks between dynamic strategic/intel snapshot updates.")]
		public readonly int ScanInterval = 125;

		[Desc("If true, Explore Map means the complete static terrain graph is legitimate map-file knowledge from match start. This never reveals dynamic enemy actors/ownership.")]
		public readonly bool UseExploredMapStaticTerrainKnowledge = true;

		[Desc("World ticks between checks for newly explored terrain while shroud is active.")]
		public readonly int TerrainKnowledgeRefreshInterval = 500;

		[Desc("World ticks between optional BotDebug summary lines. Set 0 to disable summaries.")]
		public readonly int SummaryLogInterval = 1500;

		[Desc("Minimum known/passable cells before a sector participates in a movement graph.")]
		public readonly int MinimumPassableCellsPerSector = 4;

		[Desc("Minimum percentage of a sector that must be explored before it may be labelled a choke candidate.")]
		public readonly int MinimumKnowledgePercentForChoke = 60;

		[Desc("Maximum number of passable boundary-cell connections on the narrow side of a sector for it to be considered a choke candidate.")]
		public readonly int ChokeMaximumBoundaryWidth = 5;

		[Desc("Strategic value assigned to one known mine resource creator.")]
		public readonly int OreMineValue = 100;

		[Desc("Gem mine strategic value as a percentage of a normal mine.")]
		public readonly int GemMineValuePercent = 160;

		[Desc("Threat added by one currently visible non-building combat unit.")]
		public readonly int VisibleCombatUnitThreat = 12;

		[Desc("Percentage of a sector's raw threat that spills into each directly connected ground neighbor.")]
		public readonly int NeighborThreatSpillPercent = 40;

		[Desc("Threat score at which a known resource sector is considered contested rather than simply safe.")]
		public readonly int ContestedThreatThreshold = 35;

		[Desc("Static resource score at/above which a resource sector is always considered high value.")]
		public readonly int HighValueResourceScoreThreshold = 180;

		[Desc("Desired minimum number of military production buildings as a percentage of refinery count. This is advisory only.")]
		public readonly int DesiredMilitaryProducersPerRefineryPercent = 75;

		[Desc("Strategic value of a known Oil Derrick objective.")]
		public readonly int OilDerrickObjectiveValue = 140;

		[Desc("Strategic value of a known capturable Construction Yard objective.")]
		public readonly int ConstructionObjectiveValue = 220;

		[Desc("Strategic value of a known capturable refinery/economy objective.")]
		public readonly int EconomyObjectiveValue = 180;

		[Desc("Strategic value of other known capturable tech objectives.")]
		public readonly int TechObjectiveValue = 100;

		[Desc("Control influence contributed by an observed owned/enemy strategic objective.")]
		public readonly int ObjectiveControlScore = 24;

		[Desc("Local threat at/above which contact with own influence may be classified as a frontline.")]
		public readonly int FrontlineThreatThreshold = 25;

		[Desc("Advisory local military-producer target as a percentage of refineries in the sector plus its immediate ground neighbors.")]
		public readonly int DesiredLocalMilitaryProducersPerRefineryPercent = 50;

		[Desc("Threat penalty percentage used when ranking general strategic priority sectors.")]
		public readonly int StrategicPriorityThreatPenaltyPercent = 25;

		[Desc("Remembered enemy structure confidence while the contact is no older than one StrategicMap scan.")]
		public readonly int RememberedStructureCurrentConfidencePercent = 100;
		[Desc("Maximum age in world ticks for the recent remembered-structure confidence band.")]
		public readonly int RememberedStructureRecentAgeTicks = 500;
		[Desc("Confidence percentage for recent remembered structures.")]
		public readonly int RememberedStructureRecentConfidencePercent = 85;
		[Desc("Maximum age in world ticks for the medium remembered-structure confidence band.")]
		public readonly int RememberedStructureMediumAgeTicks = 2000;
		[Desc("Confidence percentage for medium-age remembered structures.")]
		public readonly int RememberedStructureMediumConfidencePercent = 65;
		[Desc("Maximum age in world ticks for the old remembered-structure confidence band.")]
		public readonly int RememberedStructureOldAgeTicks = 5000;
		[Desc("Confidence percentage for old remembered structures.")]
		public readonly int RememberedStructureOldConfidencePercent = 40;
		[Desc("Confidence percentage for remembered structures older than the configured old-age band.")]
		public readonly int RememberedStructureStaleConfidencePercent = 20;

		[Desc("Strategic threat weight contributed by a remembered enemy defense structure before confidence decay.")]
		public readonly int EnemyDefenseThreatWeight = 60;
		[Desc("Strategic threat weight contributed by a remembered enemy strategic/tech structure before confidence decay.")]
		public readonly int EnemyStrategicThreatWeight = 35;
		[Desc("Strategic threat weight contributed by a remembered enemy production structure before confidence decay.")]
		public readonly int EnemyProductionThreatWeight = 28;
		[Desc("Strategic threat weight contributed by a remembered enemy Construction Yard before confidence decay.")]
		public readonly int EnemyConstructionThreatWeight = 25;
		[Desc("Strategic threat weight contributed by a remembered enemy economy structure before confidence decay.")]
		public readonly int EnemyEconomyThreatWeight = 16;
		[Desc("Fallback strategic threat weight for an otherwise categorized remembered structure.")]
		public readonly int EnemyOtherThreatWeight = 10;

		[Desc("Enemy-control influence weight of a remembered Construction Yard before confidence decay.")]
		public readonly int EnemyConstructionControlWeight = 45;
		[Desc("Enemy-control influence weight of a remembered defense structure before confidence decay.")]
		public readonly int EnemyDefenseControlWeight = 35;
		[Desc("Enemy-control influence weight of a remembered production structure before confidence decay.")]
		public readonly int EnemyProductionControlWeight = 28;
		[Desc("Enemy-control influence weight of a remembered economy structure before confidence decay.")]
		public readonly int EnemyEconomyControlWeight = 24;
		[Desc("Enemy-control influence weight of a remembered strategic/tech structure before confidence decay.")]
		public readonly int EnemyStrategicControlWeight = 20;
		[Desc("Fallback enemy-control influence weight for other remembered structure categories.")]
		public readonly int EnemyOtherControlWeight = 10;

		[ActorReference]
		[Desc("Representative normal ground unit used to derive ground terrain passability from its Mobile locomotor rules, not runtime pathfinding.")]
		public readonly string GroundProbeActorType = null;

		[ActorReference]
		[Desc("Representative MCV used to derive MCV terrain passability.")]
		public readonly string McvProbeActorType = null;

		[ActorReference]
		[Desc("Representative naval/landing-craft unit used to derive water terrain passability.")]
		public readonly string NavalProbeActorType = null;

		[ActorReference]
		public readonly FrozenSet<string> ResourceCreatorTypes =
			FrozenSet<string>.Empty;

		[Desc("Terrain types treated as shoreline/beach markers.")]
		public readonly FrozenSet<string> BeachTerrainTypes =
			new[] { "Beach" }.ToFrozenSet();

		[ActorReference]
		[Desc("Capturable/strategic objectives remembered by the objective layer.")]
		public readonly FrozenSet<string> StrategicObjectiveTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> PrimaryBaseTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> RefineryTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> VehicleProductionTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> InfantryProductionTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> HelicopterProductionTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> PlaneProductionTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> NavalProductionTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> EnemyConstructionTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> EnemyEconomyTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> EnemyProductionTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> EnemyDefenseTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> EnemyStrategicTypes =
			FrozenSet<string>.Empty;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (SectorSize < 4)
				throw new YamlException($"{nameof(SectorSize)} must be at least 4.");

			if (ScanInterval <= 0 || TerrainKnowledgeRefreshInterval <= 0 || SummaryLogInterval < 0)
				throw new YamlException("Strategic map timing settings are invalid.");

			if (MinimumPassableCellsPerSector <= 0 ||
				MinimumKnowledgePercentForChoke <= 0 ||
				MinimumKnowledgePercentForChoke > 100 ||
				ChokeMaximumBoundaryWidth <= 0)
				throw new YamlException("Strategic map sector/choke settings are invalid.");

			if (OreMineValue <= 0 || GemMineValuePercent <= 0 ||
				VisibleCombatUnitThreat < 0 ||
				NeighborThreatSpillPercent < 0 || NeighborThreatSpillPercent > 100 ||
				ContestedThreatThreshold < 0 ||
				HighValueResourceScoreThreshold <= 0 ||
				DesiredMilitaryProducersPerRefineryPercent <= 0 ||
				OilDerrickObjectiveValue <= 0 || ConstructionObjectiveValue <= 0 ||
				EconomyObjectiveValue <= 0 || TechObjectiveValue <= 0 ||
				ObjectiveControlScore < 0 || FrontlineThreatThreshold < 0 ||
				DesiredLocalMilitaryProducersPerRefineryPercent <= 0 ||
				StrategicPriorityThreatPenaltyPercent < 0)
				throw new YamlException("Strategic map scoring settings are invalid.");

			if (RememberedStructureCurrentConfidencePercent < 0 || RememberedStructureCurrentConfidencePercent > 100 ||
				RememberedStructureRecentAgeTicks < ScanInterval || RememberedStructureMediumAgeTicks < RememberedStructureRecentAgeTicks ||
				RememberedStructureOldAgeTicks < RememberedStructureMediumAgeTicks || RememberedStructureRecentConfidencePercent < 0 ||
				RememberedStructureRecentConfidencePercent > 100 || RememberedStructureMediumConfidencePercent < 0 || RememberedStructureMediumConfidencePercent > 100 ||
				RememberedStructureOldConfidencePercent < 0 || RememberedStructureOldConfidencePercent > 100 || RememberedStructureStaleConfidencePercent < 0 || RememberedStructureStaleConfidencePercent > 100 ||
				EnemyDefenseThreatWeight < 0 || EnemyStrategicThreatWeight < 0 || EnemyProductionThreatWeight < 0 || EnemyConstructionThreatWeight < 0 || EnemyEconomyThreatWeight < 0 || EnemyOtherThreatWeight < 0 ||
				EnemyConstructionControlWeight < 0 || EnemyDefenseControlWeight < 0 || EnemyProductionControlWeight < 0 || EnemyEconomyControlWeight < 0 || EnemyStrategicControlWeight < 0 || EnemyOtherControlWeight < 0)
				throw new YamlException("Strategic map remembered-structure personality settings are invalid.");

			ValidateMobileProbe(rules, GroundProbeActorType, nameof(GroundProbeActorType));
			ValidateMobileProbe(rules, McvProbeActorType, nameof(McvProbeActorType));
			ValidateMobileProbe(rules, NavalProbeActorType, nameof(NavalProbeActorType));
		}

		static void ValidateMobileProbe(Ruleset rules, string actorType, string fieldName)
		{
			// Cameo port: probe actors are per-faction ContentPack actors and no
			// globally loaded actor is guaranteed, so a missing actor means the
			// passability layer stays inactive rather than failing the ruleset.
			if (string.IsNullOrWhiteSpace(actorType) ||
				!rules.Actors.TryGetValue(actorType, out var actorInfo))
				return;

			if (actorInfo.TraitInfoOrDefault<MobileInfo>() == null)
				throw new YamlException($"{fieldName} actor '{actorType}' must define Mobile.");
		}

		public override object Create(ActorInitializer init)
		{
			return new FransStrategicMapBotModule(init.Self, this);
		}
	}

	public class FransStrategicMapBotModule : ConditionalTrait<FransStrategicMapBotModuleInfo>,
		IBotTick, IFransStrategicMapService
	{
		static readonly CVec[] TransportTopologyCardinalOffsets =
		{
			new CVec(1, 0), new CVec(-1, 0), new CVec(0, 1), new CVec(0, -1)
		};
		sealed class SectorTerrainState
		{
			public int TotalCellCount;
			public int KnownCellCount;
			public int GroundPassableCellCount;
			public int McvPassableCellCount;
			public int NavalPassableCellCount;
			public int BeachCellCount;
			public int LastObservedWorldTick = -1;
			public int LastExplorationChangeWorldTick = -1;
			public CPos NominalCenter;
			public CPos? GroundCenter;
			public CPos? McvCenter;
			public CPos? NavalCenter;
			public readonly HashSet<int> GroundNeighbors = [];
			public readonly HashSet<int> McvNeighbors = [];
			public readonly HashSet<int> NavalNeighbors = [];
		}

		sealed class EnemyStructureMemory
		{
			public uint ActorId;
			public string ActorType;
			public Player Owner;
			public CPos LastKnownLocation;
			public int LastSeenWorldTick;
			public FransKnownStructureCategory Category;
		}

		sealed class ResourceMemory
		{
			public uint ActorId;
			public string ActorType;
			public CPos LastKnownLocation;
			public int LastSeenWorldTick;
		}

		sealed class StrategicObjectiveMemory
		{
			public uint ActorId;
			public string ActorType;
			public CPos LastKnownLocation;
			public int LastSeenWorldTick;
			public FransStrategicObjectiveControl Control;
		}

		readonly World world;
		readonly Player player;
		readonly Dictionary<uint, EnemyStructureMemory> enemyStructureMemory = [];
		readonly Dictionary<uint, ResourceMemory> resourceMemory = [];
		readonly Dictionary<uint, StrategicObjectiveMemory> strategicObjectiveMemory = [];

		readonly HashSet<CPos> analyzedKnownCells = [];
		readonly HashSet<CPos> knownGroundCells = [];
		readonly HashSet<CPos> knownMcvCells = [];
		readonly HashSet<CPos> knownNavalCells = [];
		readonly HashSet<CPos> knownBeachCells = [];
		readonly Dictionary<CPos, int> knownBeachDistanceByCell = [];
		const int KnownBeachDistanceCacheRadius = 12;
		readonly Dictionary<CPos, int> groundLandmassByCell = [];
		readonly Dictionary<CPos, int> navalRegionByCell = [];
		readonly Dictionary<int, FransGroundShoreAccess[]> groundShoreAccessByLandmass = [];

		readonly Dictionary<(int A, int B), int> groundBoundaryWidths = [];
		readonly HashSet<int> groundArticulationPoints = [];

		// Strategic route topology/costs are immutable inside one StrategicMap snapshot. Cache only
		// the sector-id path (not the exact destination cell), so every Commander asking the same
		// start-sector -> goal-sector question shares one Dijkstra result while still receiving its
		// own exact final target cell. Safe-route costs are threat/control dependent, therefore both
		// positive and negative entries are cleared whenever BuildPublicSnapshots refreshes metrics.
		readonly Dictionary<(int Start, int Goal, FransStrategicMovementLayer Layer, FransStrategicRoutePolicy Policy), int[]> strategicSectorRouteCache = [];
		readonly HashSet<(int Start, int Goal, FransStrategicMovementLayer Layer, FransStrategicRoutePolicy Policy)> strategicSectorRouteMissCache = [];

		Shroud shroud;
		IFransCombatIntelService combatIntel;

		LocomotorInfo groundLocomotorInfo;
		LocomotorInfo mcvLocomotorInfo;
		LocomotorInfo navalLocomotorInfo;

		CPos[] playableCells = [];
		List<CPos>[] sectorCells = [];
		SectorTerrainState[] sectorTerrain = [];
		FransStrategicSector[] sectors = [];
		FransStrategicSectorMetrics[] sectorMetrics = [];
		FransKnownEnemyStructure[] knownEnemyStructures = [];
		FransKnownResourceCreator[] knownResourceCreators = [];
		FransKnownStrategicObjective[] knownStrategicObjectives = [];
		FransStrategicProductionPressure productionPressure;
		CPos? primaryBaseCell;

		CPos mapCenter;
		int maximumCenterDistanceSquared;

		int sectorColumns;
		int sectorRows;
		int scanTicks;
		int nextTerrainKnowledgeRefreshTick;
		int nextSummaryLogTick;
		bool terrainInitialized;

		public FransStrategicMapBotModule(Actor self, FransStrategicMapBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		public FransStrategicKnowledgeMode KnowledgeMode
		{
			get
			{
				if (shroud == null || shroud.Disabled ||
					(shroud.ExploreMapEnabled && !shroud.FogEnabled))
					return FransStrategicKnowledgeMode.FullVisibility;

				if (shroud.ExploreMapEnabled)
					return FransStrategicKnowledgeMode.ExploredMapWithFog;

				return shroud.FogEnabled
					? FransStrategicKnowledgeMode.ProgressiveShroudWithFog
					: FransStrategicKnowledgeMode.ProgressiveShroudWithoutFog;
			}
		}

		public bool ExploreMapEnabled => shroud?.ExploreMapEnabled ?? true;
		public bool FogEnabled => shroud?.FogEnabled ?? false;
		public IReadOnlyList<FransStrategicSector> Sectors => sectors;
		public IReadOnlyList<FransStrategicSectorMetrics> SectorMetrics => sectorMetrics;
		public IReadOnlyList<FransKnownEnemyStructure> KnownEnemyStructures => knownEnemyStructures;
		public int SnapshotWorldTick { get; private set; } = -1;
		public int TerrainKnowledgeVersion { get; private set; }

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			shroud = self.Trait<Shroud>();
			combatIntel = self.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault() ??
				throw new InvalidOperationException("FransStrategicMap requires FransCombatIntelBotModule.");

			groundLocomotorInfo = GetProbeLocomotorInfo(Info.GroundProbeActorType);
			mcvLocomotorInfo = GetProbeLocomotorInfo(Info.McvProbeActorType);
			navalLocomotorInfo = GetProbeLocomotorInfo(Info.NavalProbeActorType);

			InitializeSectorGrid();
		}

		protected override void TraitEnabled(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			// Deterministic per-player phase spreading for future many-bot games.
			scanTicks = (int)self.ActorID % Info.ScanInterval + 1;
			nextTerrainKnowledgeRefreshTick = world.WorldTick;
			nextSummaryLogTick = world.WorldTick;
			terrainInitialized = false;
		}

		protected override void TraitDisabled(Actor self)
		{
			enemyStructureMemory.Clear();
			resourceMemory.Clear();
			strategicObjectiveMemory.Clear();
			analyzedKnownCells.Clear();
			knownGroundCells.Clear();
			knownMcvCells.Clear();
			knownNavalCells.Clear();
			knownBeachCells.Clear();
			knownBeachDistanceByCell.Clear();
			groundLandmassByCell.Clear();
			navalRegionByCell.Clear();
			groundShoreAccessByLandmass.Clear();
			groundBoundaryWidths.Clear();
			groundArticulationPoints.Clear();
			strategicSectorRouteCache.Clear();
			strategicSectorRouteMissCache.Clear();

			sectors = [];
			sectorMetrics = [];
			knownEnemyStructures = [];
			knownResourceCreators = [];
			knownStrategicObjectives = [];
			productionPressure = default;
			primaryBaseCell = null;
			SnapshotWorldTick = -1;
			TerrainKnowledgeVersion = 0;
			terrainInitialized = false;
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransStrategicMap.BotTick");
			if (world.Type == WorldType.Editor || player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;

			scanTicks = Info.ScanInterval;

			if (!terrainInitialized ||
				(!IsFullTerrainKnownFromSettings() &&
					world.WorldTick >= nextTerrainKnowledgeRefreshTick))
			{
				nextTerrainKnowledgeRefreshTick =
					world.WorldTick + Info.TerrainKnowledgeRefreshInterval;
				RefreshTerrainKnowledge();
			}

			UpdateObservationTimes();
			UpdateKnownIntel();
			BuildPublicSnapshots();
			// Safe/Assault route costs depend on the freshly rebuilt sector metrics. Any cached route
			// from the previous snapshot is now stale; clear once per strategic scan, not per caller.
			strategicSectorRouteCache.Clear();
			strategicSectorRouteMissCache.Clear();

			SnapshotWorldTick = world.WorldTick;

			if (Info.SummaryLogInterval > 0 && world.WorldTick >= nextSummaryLogTick)
			{
				nextSummaryLogTick = world.WorldTick + Info.SummaryLogInterval;
				LogSummary();
			}
		}

		LocomotorInfo GetProbeLocomotorInfo(string actorType)
		{
			if (string.IsNullOrWhiteSpace(actorType) ||
				!world.Map.Rules.Actors.TryGetValue(actorType, out var actorInfo))
				return null;

			return actorInfo.TraitInfoOrDefault<MobileInfo>()?.LocomotorInfo;
		}

		void InitializeSectorGrid()
		{
			playableCells = world.Map.AllCells
				.Where(world.Map.Contains)
				.ToArray();

			var bounds = world.Map.Bounds;

			mapCenter = new CPos(
				(bounds.Left + bounds.Right - 1) / 2,
				(bounds.Top + bounds.Bottom - 1) / 2);

			var cornerCells = new[]
			{
				new CPos(bounds.Left, bounds.Top),
				new CPos(bounds.Right - 1, bounds.Top),
				new CPos(bounds.Left, bounds.Bottom - 1),
				new CPos(bounds.Right - 1, bounds.Bottom - 1)
			};

			maximumCenterDistanceSquared = Math.Max(1,
				cornerCells.Max(c => (c - mapCenter).LengthSquared));

			sectorColumns = Math.Max(1,
				(bounds.Right - bounds.Left + Info.SectorSize - 1) / Info.SectorSize);
			sectorRows = Math.Max(1,
				(bounds.Bottom - bounds.Top + Info.SectorSize - 1) / Info.SectorSize);

			var sectorCount = sectorColumns * sectorRows;
			sectorCells = new List<CPos>[sectorCount];
			sectorTerrain = new SectorTerrainState[sectorCount];

			for (var i = 0; i < sectorCount; i++)
			{
				sectorCells[i] = [];
				sectorTerrain[i] = new SectorTerrainState();
			}

			foreach (var cell in playableCells)
			{
				var id = SectorIdForCell(cell);
				if (id >= 0)
					sectorCells[id].Add(cell);
			}

			for (var id = 0; id < sectorCount; id++)
			{
				var state = sectorTerrain[id];
				state.TotalCellCount = sectorCells[id].Count;

				var sx = id % sectorColumns;
				var sy = id / sectorColumns;
				var x = Math.Min(bounds.Right - 1,
					bounds.Left + sx * Info.SectorSize + Info.SectorSize / 2);
				var y = Math.Min(bounds.Bottom - 1,
					bounds.Top + sy * Info.SectorSize + Info.SectorSize / 2);
				var nominal = new CPos(x, y);

				state.NominalCenter = world.Map.Contains(nominal) || sectorCells[id].Count == 0
					? nominal
					: sectorCells[id][0];
			}
		}

		void RefreshTerrainKnowledge()
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "StrategicMap.RefreshTerrain");
			// Exploration is normally monotonic, so only newly explored cells need terrain
			// classification. Handle unusual ResetExploration/HideMap cases with a full rebuild.
			var mustRebuild = false;
			var discoveredNewCell = false;

			foreach (var cell in playableCells)
			{
				var known = IsTerrainKnown(cell);
				var analyzed = analyzedKnownCells.Contains(cell);

				if (!known && analyzed)
				{
					mustRebuild = true;
					break;
				}

				if (known && !analyzed)
					discoveredNewCell = true;
			}

			if (!terrainInitialized || mustRebuild)
			{
				ResetTerrainKnowledge();
				foreach (var cell in playableCells)
					if (IsTerrainKnown(cell))
						AnalyzeKnownCell(cell);

				terrainInitialized = true;
				RebuildMovementGraphs();
				TerrainKnowledgeVersion++;
				return;
			}

			if (!discoveredNewCell)
				return;

			foreach (var cell in playableCells)
				if (IsTerrainKnown(cell) && !analyzedKnownCells.Contains(cell))
					AnalyzeKnownCell(cell);

			RebuildMovementGraphs();
			TerrainKnowledgeVersion++;
		}

		void ResetTerrainKnowledge()
		{
			analyzedKnownCells.Clear();
			knownGroundCells.Clear();
			knownMcvCells.Clear();
			knownNavalCells.Clear();
			knownBeachCells.Clear();
			knownBeachDistanceByCell.Clear();
			groundBoundaryWidths.Clear();

			foreach (var state in sectorTerrain)
			{
				state.KnownCellCount = 0;
				state.GroundPassableCellCount = 0;
				state.McvPassableCellCount = 0;
				state.NavalPassableCellCount = 0;
				state.BeachCellCount = 0;
				state.GroundCenter = null;
				state.McvCenter = null;
				state.NavalCenter = null;
				state.GroundNeighbors.Clear();
				state.McvNeighbors.Clear();
				state.NavalNeighbors.Clear();
				state.LastExplorationChangeWorldTick = world.WorldTick;
			}
		}

		void AnalyzeKnownCell(CPos cell)
		{
			if (!analyzedKnownCells.Add(cell))
				return;

			var sectorId = SectorIdForCell(cell);
			if (sectorId < 0)
				return;

			var state = sectorTerrain[sectorId];
			state.KnownCellCount++;
			state.LastExplorationChangeWorldTick = world.WorldTick;

			var terrainType = world.Map.GetTerrainInfo(cell).Type;

			if (groundLocomotorInfo != null && groundLocomotorInfo.TerrainSpeeds.ContainsKey(terrainType))
			{
				state.GroundPassableCellCount++;
				knownGroundCells.Add(cell);
				state.GroundCenter = ChooseCloserCenter(
					state.GroundCenter, state.NominalCenter, cell);
			}

			if (mcvLocomotorInfo != null && mcvLocomotorInfo.TerrainSpeeds.ContainsKey(terrainType))
			{
				state.McvPassableCellCount++;
				knownMcvCells.Add(cell);
				state.McvCenter = ChooseCloserCenter(
					state.McvCenter, state.NominalCenter, cell);
			}

			if (navalLocomotorInfo != null && navalLocomotorInfo.TerrainSpeeds.ContainsKey(terrainType))
			{
				state.NavalPassableCellCount++;
				knownNavalCells.Add(cell);
				state.NavalCenter = ChooseCloserCenter(
					state.NavalCenter, state.NominalCenter, cell);
			}

			if (Info.BeachTerrainTypes.Contains(terrainType))
			{
				state.BeachCellCount++;
				if (knownBeachCells.Add(cell))
					CacheKnownBeachDistances(cell);
			}
		}

		static CPos? ChooseCloserCenter(CPos? current, CPos nominal, CPos candidate)
		{
			if (!current.HasValue)
				return candidate;

			return (candidate - nominal).LengthSquared <
				(current.Value - nominal).LengthSquared
					? candidate
					: current;
		}

		void RebuildMovementGraphs()
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "StrategicMap.RebuildMovementGraphs");
			groundBoundaryWidths.Clear();

			foreach (var state in sectorTerrain)
			{
				state.GroundNeighbors.Clear();
				state.McvNeighbors.Clear();
				state.NavalNeighbors.Clear();
			}

			BuildLayerConnections(
				knownGroundCells,
				state => state.GroundNeighbors,
				recordBoundaryWidth: true);

			BuildLayerConnections(
				knownMcvCells,
				state => state.McvNeighbors,
				recordBoundaryWidth: false);

			BuildLayerConnections(
				knownNavalCells,
				state => state.NavalNeighbors,
				recordBoundaryWidth: false);

			RebuildGroundArticulationPoints();
			RebuildTransportTopology();
		}

		void RebuildTransportTopology()
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "StrategicMap.RebuildTransportTopology");
			groundLandmassByCell.Clear();
			navalRegionByCell.Clear();
			groundShoreAccessByLandmass.Clear();

			BuildExactCellComponents(knownGroundCells, groundLandmassByCell);
			BuildExactCellComponents(knownNavalCells, navalRegionByCell);

			var mutable = new Dictionary<int, List<FransGroundShoreAccess>>();
			foreach (var navalCell in knownNavalCells
				.Where(c => Info.BeachTerrainTypes.Contains(world.Map.GetTerrainInfo(c).Type))
				.OrderBy(c => c.X).ThenBy(c => c.Y))
			{
				if (!navalRegionByCell.TryGetValue(navalCell, out var navalRegionId))
					continue;

				for (var dy = -1; dy <= 1; dy++)
				for (var dx = -1; dx <= 1; dx++)
				{
					if (dx == 0 && dy == 0)
						continue;

					var groundCell = navalCell + new CVec(dx, dy);
					if (!world.Map.Contains(groundCell) || !groundLandmassByCell.TryGetValue(groundCell, out var landmassId))
						continue;

					if (!mutable.TryGetValue(landmassId, out var list))
					{
						list = [];
						mutable[landmassId] = list;
					}

					list.Add(new FransGroundShoreAccess(landmassId, navalRegionId, groundCell, navalCell));
				}
			}

			foreach (var pair in mutable)
				groundShoreAccessByLandmass[pair.Key] = pair.Value
					.Distinct()
					.OrderBy(a => a.NavalRegionId)
					.ThenBy(a => a.NavalCell.X).ThenBy(a => a.NavalCell.Y)
					.ThenBy(a => a.GroundCell.X).ThenBy(a => a.GroundCell.Y)
					.ToArray();
		}

		void BuildExactCellComponents(HashSet<CPos> passableCells, Dictionary<CPos, int> componentByCell)
		{
			var nextId = 1;
			var queue = new Queue<CPos>();
			foreach (var start in passableCells.OrderBy(c => c.X).ThenBy(c => c.Y))
			{
				if (componentByCell.ContainsKey(start))
					continue;

				var componentId = nextId++;
				componentByCell[start] = componentId;
				queue.Enqueue(start);
				while (queue.Count > 0)
				{
					var current = queue.Dequeue();
					foreach (var offset in TransportTopologyCardinalOffsets)
					{
						var next = current + offset;
						if (!world.Map.Contains(next) || !passableCells.Contains(next) || componentByCell.ContainsKey(next))
							continue;

						if (world.Map.Grid.MaximumTerrainHeight > 0 &&
							Math.Abs(world.Map.Height[current] - world.Map.Height[next]) > 1)
							continue;

						componentByCell[next] = componentId;
						queue.Enqueue(next);
					}
				}
			}
		}

		void RebuildGroundArticulationPoints()
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "StrategicMap.RebuildArticulation");
			groundArticulationPoints.Clear();

			var count = sectorTerrain.Length;
			var discovery = new int[count];
			var low = new int[count];
			var parent = new int[count];
			var visited = new bool[count];
			Array.Fill(parent, -1);

			var time = 0;
			for (var id = 0; id < count; id++)
			{
				if (visited[id] ||
					sectorTerrain[id].GroundPassableCellCount < Info.MinimumPassableCellsPerSector)
					continue;

				GroundArticulationDfs(id, visited, discovery, low, parent, ref time);
			}
		}

		void GroundArticulationDfs(
			int current,
			bool[] visited,
			int[] discovery,
			int[] low,
			int[] parent,
			ref int time)
		{
			visited[current] = true;
			discovery[current] = low[current] = ++time;
			var children = 0;

			foreach (var next in sectorTerrain[current].GroundNeighbors)
			{
				if (sectorTerrain[next].GroundPassableCellCount <
					Info.MinimumPassableCellsPerSector)
					continue;

				if (!visited[next])
				{
					children++;
					parent[next] = current;

					GroundArticulationDfs(
						next, visited, discovery, low, parent, ref time);

					low[current] = Math.Min(low[current], low[next]);

					if (parent[current] == -1 && children > 1)
						groundArticulationPoints.Add(current);

					if (parent[current] != -1 &&
						low[next] >= discovery[current])
						groundArticulationPoints.Add(current);
				}
				else if (next != parent[current])
					low[current] = Math.Min(low[current], discovery[next]);
			}
		}

		void BuildLayerConnections(
			HashSet<CPos> passableCells,
			Func<SectorTerrainState, HashSet<int>> neighborSelector,
			bool recordBoundaryWidth)
		{
			foreach (var cell in passableCells)
			{
				CheckLayerConnection(
					cell,
					cell + new CVec(1, 0),
					passableCells,
					neighborSelector,
					recordBoundaryWidth);

				CheckLayerConnection(
					cell,
					cell + new CVec(0, 1),
					passableCells,
					neighborSelector,
					recordBoundaryWidth);
			}
		}

		void CheckLayerConnection(
			CPos a,
			CPos b,
			HashSet<CPos> passableCells,
			Func<SectorTerrainState, HashSet<int>> neighborSelector,
			bool recordBoundaryWidth)
		{
			if (!passableCells.Contains(b) || !world.Map.Contains(b))
				return;

			// Match the static height-discontinuity rule used by Locomotor:
			// adjacent cells whose height differs by more than one cannot connect.
			if (world.Map.Grid.MaximumTerrainHeight > 0 &&
				Math.Abs(world.Map.Height[a] - world.Map.Height[b]) > 1)
				return;

			var aId = SectorIdForCell(a);
			var bId = SectorIdForCell(b);
			if (aId < 0 || bId < 0 || aId == bId)
				return;

			neighborSelector(sectorTerrain[aId]).Add(bId);
			neighborSelector(sectorTerrain[bId]).Add(aId);

			if (!recordBoundaryWidth)
				return;

			var key = aId < bId ? (aId, bId) : (bId, aId);
			groundBoundaryWidths.TryGetValue(key, out var width);
			groundBoundaryWidths[key] = width + 1;
		}

		void UpdateObservationTimes()
		{
			if (!terrainInitialized)
				return;

			var fullVisibility = KnowledgeMode == FransStrategicKnowledgeMode.FullVisibility ||
				KnowledgeMode == FransStrategicKnowledgeMode.ProgressiveShroudWithoutFog;

			for (var id = 0; id < sectorTerrain.Length; id++)
			{
				var state = sectorTerrain[id];
				if (state.KnownCellCount == 0)
					continue;

				if (fullVisibility)
				{
					state.LastObservedWorldTick = world.WorldTick;
					continue;
				}

				foreach (var cell in sectorCells[id])
				{
					if (!IsTerrainKnown(cell))
						continue;

					if (!shroud.IsVisible(cell))
						continue;

					state.LastObservedWorldTick = world.WorldTick;
					break;
				}
			}
		}

		void UpdateKnownIntel()
		{
			combatIntel.EnsureCurrentSnapshot();
			var visibleActors = combatIntel.VisibleActors;
			var visibleEnemies = combatIntel.VisibleEnemies;

			var seenEnemyStructures = new HashSet<uint>();
			foreach (var actor in visibleEnemies)
			{
				if (actor.OccupiesSpace == null || actor.Info.TraitInfoOrDefault<BuildingInfo>() == null)
					continue;

				seenEnemyStructures.Add(actor.ActorID);
				enemyStructureMemory[actor.ActorID] = new EnemyStructureMemory
				{
					ActorId = actor.ActorID,
					ActorType = actor.Info.Name,
					Owner = actor.Owner,
					LastKnownLocation = actor.Location,
					LastSeenWorldTick = world.WorldTick,
					Category = ClassifyEnemyStructure(actor.Info.Name)
				};
			}

			// A human can discard remembered information after revisiting the location and
			// seeing that the building is gone. Never inspect a hidden Actor to make this decision.
			foreach (var memory in enemyStructureMemory.Values.ToArray())
			{
				if (seenEnemyStructures.Contains(memory.ActorId))
					continue;

				if (IsCellCurrentlyObserved(memory.LastKnownLocation))
					enemyStructureMemory.Remove(memory.ActorId);
			}

			var seenResources = new HashSet<uint>();
			foreach (var actor in visibleActors)
			{
				if (actor.OccupiesSpace == null ||
					!Info.ResourceCreatorTypes.Contains(actor.Info.Name))
					continue;

				seenResources.Add(actor.ActorID);
				resourceMemory[actor.ActorID] = new ResourceMemory
				{
					ActorId = actor.ActorID,
					ActorType = actor.Info.Name,
					LastKnownLocation = actor.Location,
					LastSeenWorldTick = world.WorldTick
				};
			}

			foreach (var memory in resourceMemory.Values.ToArray())
			{
				if (seenResources.Contains(memory.ActorId))
					continue;

				if (IsCellCurrentlyObserved(memory.LastKnownLocation))
					resourceMemory.Remove(memory.ActorId);
			}

			var seenObjectives = new HashSet<uint>();
			foreach (var actor in visibleActors)
			{
				if (actor.OccupiesSpace == null ||
					!Info.StrategicObjectiveTypes.Contains(actor.Info.Name))
					continue;

				seenObjectives.Add(actor.ActorID);
				strategicObjectiveMemory[actor.ActorID] = new StrategicObjectiveMemory
				{
					ActorId = actor.ActorID,
					ActorType = actor.Info.Name,
					LastKnownLocation = actor.Location,
					LastSeenWorldTick = world.WorldTick,
					Control = ObjectiveControlFor(actor)
				};
			}

			// If the location is observed again and the remembered actor is no longer there,
			// forget it. Hidden ownership/death is never queried.
			foreach (var memory in strategicObjectiveMemory.Values.ToArray())
			{
				if (seenObjectives.Contains(memory.ActorId))
					continue;

				if (IsCellCurrentlyObserved(memory.LastKnownLocation))
					strategicObjectiveMemory.Remove(memory.ActorId);
			}
		}

		void BuildPublicSnapshots()
		{
			var enemyCountBySector = new int[sectorTerrain.Length];
			var resourceCountBySector = new int[sectorTerrain.Length];
			var ownedStructureCountBySector = new int[sectorTerrain.Length];

			foreach (var memory in enemyStructureMemory.Values)
			{
				var id = SectorIdForCell(memory.LastKnownLocation);
				if (id >= 0)
					enemyCountBySector[id]++;
			}

			foreach (var memory in resourceMemory.Values)
			{
				var id = SectorIdForCell(memory.LastKnownLocation);
				if (id >= 0)
					resourceCountBySector[id]++;
			}

			combatIntel.EnsureCurrentSnapshot();
			var ownedActors = combatIntel.OwnedActors;

			foreach (var actor in ownedActors)
			{
				if (actor.OccupiesSpace == null || actor.Info.TraitInfoOrDefault<BuildingInfo>() == null)
					continue;

				var id = SectorIdForCell(actor.Location);
				if (id >= 0)
					ownedStructureCountBySector[id]++;
			}

			var publicSectors = new FransStrategicSector[sectorTerrain.Length];

			for (var id = 0; id < sectorTerrain.Length; id++)
			{
				var state = sectorTerrain[id];
				var knowledgePercent = state.TotalCellCount > 0
					? state.KnownCellCount * 100 / state.TotalCellCount
					: 0;

				var groundNeighbors = state.GroundNeighbors.OrderBy(n => n).ToArray();
				var mcvNeighbors = state.McvNeighbors.OrderBy(n => n).ToArray();
				var navalNeighbors = state.NavalNeighbors.OrderBy(n => n).ToArray();

				var choke = false;
				if (knowledgePercent >= Info.MinimumKnowledgePercentForChoke &&
					state.GroundPassableCellCount >= Info.MinimumPassableCellsPerSector &&
					groundNeighbors.Length == 2)
				{
					var narrowestBoundary = groundNeighbors
						.Select(n =>
						{
							var key = id < n ? (id, n) : (n, id);
							return groundBoundaryWidths.TryGetValue(key, out var width)
								? width
								: int.MaxValue;
						})
						.Min();

					choke = narrowestBoundary <= Info.ChokeMaximumBoundaryWidth;
				}

				var beachhead =
					state.BeachCellCount > 0 &&
					state.GroundPassableCellCount >= Info.MinimumPassableCellsPerSector &&
					state.NavalPassableCellCount > 0;

				var center =
					state.GroundCenter ??
					state.McvCenter ??
					state.NavalCenter ??
					state.NominalCenter;

				publicSectors[id] = new FransStrategicSector(
					id,
					center,
					state.GroundCenter,
					state.McvCenter,
					state.NavalCenter,
					state.TotalCellCount,
					state.KnownCellCount,
					state.GroundPassableCellCount,
					state.McvPassableCellCount,
					state.NavalPassableCellCount,
					state.BeachCellCount,
					groundNeighbors,
					mcvNeighbors,
					navalNeighbors,
					choke,
					beachhead,
					state.LastObservedWorldTick,
					state.LastExplorationChangeWorldTick,
					resourceCountBySector[id],
					enemyCountBySector[id],
					ownedStructureCountBySector[id]);
			}

			sectors = publicSectors;

			knownEnemyStructures = enemyStructureMemory.Values
				.OrderBy(m => m.ActorId)
				.Select(m => new FransKnownEnemyStructure(
					m.ActorId,
					m.ActorType,
					m.Owner,
					m.LastKnownLocation,
					m.LastSeenWorldTick,
					100,
					m.Category))
				.ToArray();

			knownResourceCreators = resourceMemory.Values
				.OrderBy(m => m.ActorId)
				.Select(m => new FransKnownResourceCreator(
					m.ActorId,
					m.ActorType,
					m.LastKnownLocation,
					m.LastSeenWorldTick))
				.ToArray();

			knownStrategicObjectives = strategicObjectiveMemory.Values
				.OrderBy(m => m.ActorId)
				.Select(m => new FransKnownStrategicObjective(
					m.ActorId,
					m.ActorType,
					m.LastKnownLocation,
					m.LastSeenWorldTick,
					ConfidenceForLastSeenTick(m.LastSeenWorldTick),
					m.Control,
					StrategicObjectiveValue(m.ActorType)))
				.ToArray();

			BuildStrategicMetrics(ownedActors);
		}

		void BuildStrategicMetrics(IReadOnlyList<Actor> ownedActors)
		{
			var sectorCount = sectors.Length;
			var resourceValue = new int[sectorCount];
			var strategicObjectiveValue = new int[sectorCount];
			var ownObjectives = new int[sectorCount];
			var alliedObjectives = new int[sectorCount];
			var enemyObjectives = new int[sectorCount];
			var neutralObjectives = new int[sectorCount];
			var rawThreat = new int[sectorCount];
			var threat = new int[sectorCount];
			var ownControl = new int[sectorCount];
			var enemyControl = new int[sectorCount];
			var visibleEnemyCombat = new int[sectorCount];
			var ownedRefineries = new int[sectorCount];
			var ownedMilitaryProduction = new int[sectorCount];

			foreach (var memory in resourceMemory.Values)
			{
				var id = SectorIdForCell(memory.LastKnownLocation);
				if (id < 0)
					continue;

				var value = Info.OreMineValue;
				if (memory.ActorType == "gmine")
					value = value * Info.GemMineValuePercent / 100;

				resourceValue[id] += value;
			}

			foreach (var memory in strategicObjectiveMemory.Values)
			{
				var id = SectorIdForCell(memory.LastKnownLocation);
				if (id < 0)
					continue;

				var confidence = ConfidenceForLastSeenTick(memory.LastSeenWorldTick);
				strategicObjectiveValue[id] += StrategicObjectiveValue(memory.ActorType) * confidence / 100;

				switch (memory.Control)
				{
					case FransStrategicObjectiveControl.Own:
						ownObjectives[id]++;
						ownControl[id] += Info.ObjectiveControlScore * confidence / 100;
						break;
					case FransStrategicObjectiveControl.Ally:
						alliedObjectives[id]++;
						ownControl[id] += Info.ObjectiveControlScore * confidence / 200;
						break;
					case FransStrategicObjectiveControl.Enemy:
						enemyObjectives[id]++;
						enemyControl[id] += Info.ObjectiveControlScore * confidence / 100;
						break;
					default:
						neutralObjectives[id]++;
						break;
				}
			}

			foreach (var memory in enemyStructureMemory.Values)
			{
				var id = SectorIdForCell(memory.LastKnownLocation);
				if (id < 0)
					continue;

				// Static enemy structures remain fully believed until direct observation of their
				// last-known cell proves them gone/changed. Only mobile/objective uncertainty decays.
				const int confidence = 100;
				var structureThreat = StructureThreatWeight(memory.Category) * confidence / 100;
				var structureControl = StructureControlWeight(memory.Category) * confidence / 100;

				rawThreat[id] += structureThreat;
				enemyControl[id] += structureControl;
			}

			combatIntel.EnsureCurrentSnapshot();
			var visibleEnemies = combatIntel.VisibleEnemies;
			foreach (var actor in visibleEnemies)
			{
				if (actor == null || !actor.IsInWorld || actor.IsDead ||
					actor.OccupiesSpace == null ||
					actor.Info.TraitInfoOrDefault<BuildingInfo>() != null ||
					actor.Info.TraitInfoOrDefault<AttackBaseInfo>() == null)
					continue;

				var id = SectorIdForCell(actor.Location);
				if (id < 0)
					continue;

				visibleEnemyCombat[id]++;
				rawThreat[id] += Info.VisibleCombatUnitThreat;
				enemyControl[id] += Math.Max(1, Info.VisibleCombatUnitThreat / 3);
			}

			var vehicleProducers = 0;
			var infantryProducers = 0;
			var helicopterProducers = 0;
			var planeProducers = 0;
			var navalProducers = 0;
			var refineryCount = 0;

			primaryBaseCell = null;
			var primaryBaseActorId = uint.MaxValue;

			foreach (var actor in ownedActors)
			{
				if (actor == null || !actor.IsInWorld || actor.IsDead ||
					actor.OccupiesSpace == null ||
					actor.Info.TraitInfoOrDefault<BuildingInfo>() == null)
					continue;

				var id = SectorIdForCell(actor.Location);
				if (id < 0)
					continue;

				var type = actor.Info.Name;

				if (Info.PrimaryBaseTypes.Contains(type))
				{
					ownControl[id] += 50;
					if (actor.ActorID < primaryBaseActorId)
					{
						primaryBaseActorId = actor.ActorID;
						primaryBaseCell = actor.Location;
					}
				}
				else if (Info.RefineryTypes.Contains(type))
				{
					refineryCount++;
					ownedRefineries[id]++;
					ownControl[id] += 30;
				}
				else if (Info.VehicleProductionTypes.Contains(type))
				{
					vehicleProducers++;
					ownedMilitaryProduction[id]++;
					ownControl[id] += 22;
				}
				else if (Info.InfantryProductionTypes.Contains(type))
				{
					infantryProducers++;
					ownedMilitaryProduction[id]++;
					ownControl[id] += 18;
				}
				else if (Info.HelicopterProductionTypes.Contains(type))
				{
					helicopterProducers++;
					ownedMilitaryProduction[id]++;
					ownControl[id] += 20;
				}
				else if (Info.PlaneProductionTypes.Contains(type))
				{
					planeProducers++;
					ownedMilitaryProduction[id]++;
					ownControl[id] += 20;
				}
				else if (Info.NavalProductionTypes.Contains(type))
				{
					navalProducers++;
					ownedMilitaryProduction[id]++;
					ownControl[id] += 18;
				}
				else
					ownControl[id] += 8;
			}

			// Threat is intentionally coarse. Known danger bleeds into adjacent ground
			// sectors so "the Tesla is one 8x8 bucket away" does not become a false safe edge.
			Array.Copy(rawThreat, threat, rawThreat.Length);
			if (Info.NeighborThreatSpillPercent > 0)
			{
				for (var id = 0; id < sectorCount; id++)
				{
					if (rawThreat[id] <= 0 || sectors[id] == null)
						continue;

					var spill = rawThreat[id] * Info.NeighborThreatSpillPercent / 100;
					foreach (var neighbor in sectors[id].GroundNeighbors)
						threat[neighbor] += spill;
				}
			}

			var metrics = new FransStrategicSectorMetrics[sectorCount];

			for (var id = 0; id < sectorCount; id++)
			{
				var sector = sectors[id];
				if (sector == null)
					continue;

				var centrality = CentralityPercent(sector.Center);

				var localSectorIds = sector.GroundNeighbors
					.Where(n => n >= 0 && n < sectorCount)
					.Append(id)
					.Distinct()
					.ToArray();

				var localRefineryCount = localSectorIds.Sum(n => ownedRefineries[n]);
				var localMilitaryProductionCount = localSectorIds.Sum(n => ownedMilitaryProduction[n]);
				var desiredLocalMilitaryProduction = localRefineryCount > 0
					? (localRefineryCount * Info.DesiredLocalMilitaryProducersPerRefineryPercent + 99) / 100
					: 0;
				var localProductionDeficit = Math.Max(0,
					desiredLocalMilitaryProduction - localMilitaryProductionCount);
				var localProductionPressurePercent = desiredLocalMilitaryProduction > 0
					? Math.Min(100, localProductionDeficit * 100 / desiredLocalMilitaryProduction)
					: 0;
				var needsLocalProductionCapacity =
					localRefineryCount >= 2 && localProductionDeficit > 0;

				var localOwnInfluence = localSectorIds.Sum(n => ownControl[n]);
				var localEnemyInfluence = localSectorIds.Sum(n => enemyControl[n]);
				var isFrontline =
					localOwnInfluence > 0 &&
					(localEnemyInfluence > 0 || threat[id] >= Info.FrontlineThreatThreshold);
				var frontlineScore = isFrontline
					? Math.Min(250,
						Math.Min(100, localOwnInfluence) +
						Math.Min(100, localEnemyInfluence) +
						threat[id] / 2)
					: 0;

				var highValue =
					resourceValue[id] >= Info.HighValueResourceScoreThreshold ||
					(resourceValue[id] > 0 && centrality >= 65);

				var contested =
					resourceValue[id] > 0 &&
					threat[id] >= Info.ContestedThreatThreshold;

				var narrowChokeScore = sector.IsGroundChokeCandidate ? 45 : 0;
				var articulationScore = groundArticulationPoints.Contains(id) ? 55 : 0;
				var strategicChokeBonus = Math.Min(20,
					centrality / 5 +
					Math.Min(10, resourceValue[id] / Math.Max(1, Info.OreMineValue)));

				var chokeScore =
					narrowChokeScore + articulationScore + strategicChokeBonus;

				metrics[id] = new FransStrategicSectorMetrics(
					id,
					centrality,
					resourceValue[id],
					strategicObjectiveValue[id],
					threat[id],
					ownControl[id],
					enemyControl[id],
					visibleEnemyCombat[id],
					ownedRefineries[id],
					ownedMilitaryProduction[id],
					ownObjectives[id],
					alliedObjectives[id],
					enemyObjectives[id],
					neutralObjectives[id],
					frontlineScore,
					localRefineryCount,
					localMilitaryProductionCount,
					localProductionPressurePercent,
					chokeScore,
					groundArticulationPoints.Contains(id),
					highValue,
					contested,
					strategicObjectiveValue[id] > 0,
					isFrontline,
					needsLocalProductionCapacity);
			}

			sectorMetrics = metrics;

			var totalMilitaryProducers =
				vehicleProducers +
				infantryProducers +
				helicopterProducers +
				planeProducers +
				navalProducers;

			var suggestedMinimum = refineryCount > 0
				? Math.Max(2,
					(refineryCount * Info.DesiredMilitaryProducersPerRefineryPercent + 99) / 100)
				: 0;

			var deficit = Math.Max(0, suggestedMinimum - totalMilitaryProducers);
			var pressurePercent = suggestedMinimum > 0
				? Math.Min(100, deficit * 100 / suggestedMinimum)
				: 0;

			productionPressure = new FransStrategicProductionPressure(
				refineryCount,
				vehicleProducers,
				infantryProducers,
				helicopterProducers,
				planeProducers,
				navalProducers,
				totalMilitaryProducers,
				suggestedMinimum,
				deficit,
				pressurePercent,
				refineryCount >= 6 && deficit > 0);
		}

		int StructureThreatWeight(FransKnownStructureCategory category)
		{
			return category switch
			{
				FransKnownStructureCategory.Defense => Info.EnemyDefenseThreatWeight,
				FransKnownStructureCategory.Strategic => Info.EnemyStrategicThreatWeight,
				FransKnownStructureCategory.Production => Info.EnemyProductionThreatWeight,
				FransKnownStructureCategory.Construction => Info.EnemyConstructionThreatWeight,
				FransKnownStructureCategory.Economy => Info.EnemyEconomyThreatWeight,
				_ => Info.EnemyOtherThreatWeight
			};
		}

		int StructureControlWeight(FransKnownStructureCategory category)
		{
			return category switch
			{
				FransKnownStructureCategory.Construction => Info.EnemyConstructionControlWeight,
				FransKnownStructureCategory.Defense => Info.EnemyDefenseControlWeight,
				FransKnownStructureCategory.Production => Info.EnemyProductionControlWeight,
				FransKnownStructureCategory.Economy => Info.EnemyEconomyControlWeight,
				FransKnownStructureCategory.Strategic => Info.EnemyStrategicControlWeight,
				_ => Info.EnemyOtherControlWeight
			};
		}

		int CentralityPercent(CPos cell)
		{
			var distanceSquared = (cell - mapCenter).LengthSquared;
			var normalized = Math.Sqrt(
				Math.Min(distanceSquared, maximumCenterDistanceSquared) /
				(double)maximumCenterDistanceSquared);

			return Math.Clamp(100 - (int)Math.Round(normalized * 100), 0, 100);
		}

		int ConfidenceForLastSeenTick(int lastSeenWorldTick)
		{
			var age = Math.Max(0, world.WorldTick - lastSeenWorldTick);
			if (age <= Info.ScanInterval)
				return Info.RememberedStructureCurrentConfidencePercent;
			if (age <= Info.RememberedStructureRecentAgeTicks)
				return Info.RememberedStructureRecentConfidencePercent;
			if (age <= Info.RememberedStructureMediumAgeTicks)
				return Info.RememberedStructureMediumConfidencePercent;
			if (age <= Info.RememberedStructureOldAgeTicks)
				return Info.RememberedStructureOldConfidencePercent;
			return Info.RememberedStructureStaleConfidencePercent;
		}

		FransKnownStructureCategory ClassifyEnemyStructure(string actorType)
		{
			if (Info.EnemyConstructionTypes.Contains(actorType))
				return FransKnownStructureCategory.Construction;
			if (Info.EnemyEconomyTypes.Contains(actorType))
				return FransKnownStructureCategory.Economy;
			if (Info.EnemyProductionTypes.Contains(actorType))
				return FransKnownStructureCategory.Production;
			if (Info.EnemyDefenseTypes.Contains(actorType))
				return FransKnownStructureCategory.Defense;
			if (Info.EnemyStrategicTypes.Contains(actorType))
				return FransKnownStructureCategory.Strategic;

			return FransKnownStructureCategory.Other;
		}

		FransStrategicObjectiveControl ObjectiveControlFor(Actor actor)
		{
			if (actor.Owner == player)
				return FransStrategicObjectiveControl.Own;

			if (actor.Owner == null)
				return FransStrategicObjectiveControl.Neutral;

			var relationship = player.RelationshipWith(actor.Owner);
			if (PlayerRelationship.Enemy.HasRelationship(relationship))
				return FransStrategicObjectiveControl.Enemy;
			if (PlayerRelationship.Ally.HasRelationship(relationship))
				return FransStrategicObjectiveControl.Ally;

			return FransStrategicObjectiveControl.Neutral;
		}

		int StrategicObjectiveValue(string actorType)
		{
			if (actorType == "oilb")
				return Info.OilDerrickObjectiveValue;
			if (Info.PrimaryBaseTypes.Contains(actorType))
				return Info.ConstructionObjectiveValue;
			if (Info.RefineryTypes.Contains(actorType))
				return Info.EconomyObjectiveValue;

			return Info.TechObjectiveValue;
		}

		bool IsFullTerrainKnownFromSettings()
		{
			return shroud == null || shroud.Disabled ||
				(Info.UseExploredMapStaticTerrainKnowledge && shroud.ExploreMapEnabled);
		}

		public bool IsTerrainKnown(CPos cell)
		{
			if (!world.Map.Contains(cell))
				return false;

			return shroud == null ||
				shroud.Disabled ||
				(Info.UseExploredMapStaticTerrainKnowledge && shroud.ExploreMapEnabled) ||
				shroud.IsExplored(cell);
		}

		bool IsCellCurrentlyObserved(CPos cell)
		{
			if (!IsTerrainKnown(cell))
				return false;

			if (KnowledgeMode == FransStrategicKnowledgeMode.FullVisibility ||
				KnowledgeMode == FransStrategicKnowledgeMode.ProgressiveShroudWithoutFog)
				return true;

			return shroud.IsVisible(cell);
		}

		int SectorIdForCell(CPos cell)
		{
			if (!world.Map.Contains(cell))
				return -1;

			var bounds = world.Map.Bounds;
			var sx = (cell.X - bounds.Left) / Info.SectorSize;
			var sy = (cell.Y - bounds.Top) / Info.SectorSize;

			if (sx < 0 || sy < 0 || sx >= sectorColumns || sy >= sectorRows)
				return -1;

			return sy * sectorColumns + sx;
		}

		public bool TryGetSector(CPos cell, out FransStrategicSector sector)
		{
			sector = null;
			var id = SectorIdForCell(cell);
			if (id < 0 || id >= sectors.Length)
				return false;

			sector = sectors[id];
			return sector != null && sector.KnownCellCount > 0;
		}

		public bool TryGetSectorMetrics(
			CPos cell,
			out FransStrategicSectorMetrics metrics)
		{
			metrics = default;
			var id = SectorIdForCell(cell);
			if (id < 0 || id >= sectorMetrics.Length ||
				id >= sectors.Length || sectors[id] == null)
				return false;

			metrics = sectorMetrics[id];
			return sectors[id].KnownCellCount > 0;
		}


		public bool TryGetGroundLandmassId(CPos cell, out int landmassId)
		{
			return groundLandmassByCell.TryGetValue(cell, out landmassId);
		}

		public bool TryGetNavalRegionId(CPos cell, out int navalRegionId)
		{
			return navalRegionByCell.TryGetValue(cell, out navalRegionId);
		}

		void CacheKnownBeachDistances(CPos beachCell)
		{
			// Terrain knowledge changes slowly, while RiskModel path-cost callbacks can execute
			// thousands of times in one native A* search. Pay the small radius walk once when a
			// beach cell becomes legitimately known, then keep every shore-distance query O(1).
			knownBeachDistanceByCell[beachCell] = 0;
			for (var radius = 1; radius <= KnownBeachDistanceCacheRadius; radius++)
				foreach (var candidate in world.Map.FindTilesInAnnulus(beachCell, radius, radius))
				{
					if (!world.Map.Contains(candidate))
						continue;
					if (!knownBeachDistanceByCell.TryGetValue(candidate, out var existing) || radius < existing)
						knownBeachDistanceByCell[candidate] = radius;
				}
		}

		public int GetKnownBeachDistance(CPos cell, int maximumDistance)
		{
			if (maximumDistance < 0 || !world.Map.Contains(cell) || knownBeachCells.Count == 0)
				return -1;
			if (!knownBeachDistanceByCell.TryGetValue(cell, out var distance) || distance > maximumDistance)
				return -1;
			return distance;
		}

		public IReadOnlyList<FransGroundShoreAccess> GetGroundShoreAccess(int groundLandmassId)
		{
			return groundShoreAccessByLandmass.TryGetValue(groundLandmassId, out var access)
				? access
				: Array.Empty<FransGroundShoreAccess>();
		}

		public IReadOnlyList<FransAnchorPointCandidate> GetAnchorPointCandidates(
			FransStrategicMovementLayer movementLayer,
			int maximumCount)
		{
			if (maximumCount <= 0 || sectorMetrics.Length != sectors.Length)
				return Array.Empty<FransAnchorPointCandidate>();

			var result = new List<FransAnchorPointCandidate>();
			for (var id = 0; id < sectors.Length; id++)
			{
				var sector = sectors[id];
				if (sector == null || sector.KnownCellCount == 0)
					continue;

				CPos? cell = movementLayer switch
				{
					FransStrategicMovementLayer.Naval => sector.NavalCenter,
					FransStrategicMovementLayer.Mcv => sector.McvCenter ?? sector.GroundCenter,
					_ => sector.GroundCenter
				};
				if (!cell.HasValue)
					continue;

				var metrics = sectorMetrics[id];
				if (metrics.OwnControlScore <= 0 || metrics.OwnControlScore < metrics.EnemyControlScore)
					continue;

				var hasBase = sector.OwnedStructureCount > 0 ||
					metrics.OwnedRefineryCount > 0 || metrics.OwnedMilitaryProductionCount > 0;
				var hasChoke = movementLayer != FransStrategicMovementLayer.Naval &&
					(metrics.GroundChokeScore > 0 || metrics.IsGroundArticulationPoint);

				var kind = hasBase
					? FransAnchorPointKind.Base
					: hasChoke ? FransAnchorPointKind.Choke : FransAnchorPointKind.FriendlyControl;

				var score =
					metrics.OwnControlScore * 4 +
					metrics.CentralityPercent +
					metrics.OwnedRefineryCount * 120 +
					metrics.OwnedMilitaryProductionCount * 150 +
					metrics.GroundChokeScore * 2 -
					metrics.EnemyControlScore * 4 -
					metrics.ThreatScore * 2;

				result.Add(new FransAnchorPointCandidate(cell.Value, kind, score));
			}

			return result
				.OrderByDescending(c => c.Kind)
				.ThenByDescending(c => c.StrategicScore)
				.ThenBy(c => c.Cell.X)
				.ThenBy(c => c.Cell.Y)
				.Take(maximumCount)
				.ToArray();
		}

		public IReadOnlyList<FransStrategicPrioritySector> GetStrategicPrioritySectors(int maximumCount)
		{
			if (maximumCount <= 0 || sectorMetrics.Length != sectors.Length)
				return Array.Empty<FransStrategicPrioritySector>();

			var result = new List<FransStrategicPrioritySector>();
			for (var id = 0; id < sectors.Length; id++)
			{
				var sector = sectors[id];
				var metrics = sectorMetrics[id];
				if (sector == null || sector.KnownCellCount == 0 || !sector.GroundCenter.HasValue)
					continue;

				var actionableObjectiveValue = strategicObjectiveMemory.Values
					.Where(m => SectorIdForCell(m.LastKnownLocation) == id &&
						(m.Control == FransStrategicObjectiveControl.Enemy ||
						 m.Control == FransStrategicObjectiveControl.Neutral))
					.Sum(m => StrategicObjectiveValue(m.ActorType) *
						ConfidenceForLastSeenTick(m.LastSeenWorldTick) / 100);

				if (metrics.ResourceValueScore <= 0 &&
					actionableObjectiveValue <= 0 &&
					!metrics.IsFrontlineSector &&
					metrics.EnemyControlScore <= 0)
					continue;

				var threatPenalty =
					metrics.ThreatScore * Info.StrategicPriorityThreatPenaltyPercent / 100;
				var controlObjectiveBonus =
					metrics.EnemyStrategicObjectiveCount * 60 +
					metrics.NeutralStrategicObjectiveCount * 35;
				var totalScore =
					metrics.ResourceValueScore +
					actionableObjectiveValue +
					metrics.FrontlineScore +
					metrics.EnemyControlScore * 2 +
					metrics.CentralityPercent / 2 +
					controlObjectiveBonus -
					threatPenalty;

				result.Add(new FransStrategicPrioritySector(
					id,
					sector.GroundCenter.Value,
					totalScore,
					metrics.ResourceValueScore,
					actionableObjectiveValue,
					metrics.FrontlineScore,
					metrics.ThreatScore,
					metrics.EnemyControlScore,
					metrics.EnemyStrategicObjectiveCount,
					metrics.NeutralStrategicObjectiveCount,
					metrics.IsHighValueResourceSector,
					metrics.IsStrategicObjectiveSector,
					metrics.IsFrontlineSector,
					FindSuggestedStagingPoint(id)));
			}

			return result
				.OrderByDescending(c => c.TotalScore)
				.ThenByDescending(c => c.EnemyStrategicObjectiveCount)
				.ThenByDescending(c => c.NeutralStrategicObjectiveCount)
				.ThenBy(c => c.ThreatScore)
				.ThenBy(c => c.SectorId)
				.Take(maximumCount)
				.ToArray();
		}

		CPos? FindSuggestedStagingPoint(int targetSectorId)
		{
			if (targetSectorId < 0 || targetSectorId >= sectors.Length)
				return null;

			var target = sectors[targetSectorId];
			if (target == null)
				return null;

			var candidateIds = target.GroundNeighbors
				.Where(id => id >= 0 && id < sectors.Length &&
					sectors[id] != null &&
					sectors[id].GroundCenter.HasValue)
				.ToArray();

			if (candidateIds.Length == 0)
				return target.GroundCenter;

			var best = candidateIds
				.OrderBy(id => sectorMetrics[id].ThreatScore)
				.ThenByDescending(id => sectorMetrics[id].OwnControlScore)
				.ThenByDescending(id => sectorMetrics[id].CentralityPercent)
				.ThenBy(id => id)
				.First();

			return sectors[best].GroundCenter;
		}

		public bool TryGetStrategicSectorRoute(
			CPos from,
			CPos to,
			FransStrategicMovementLayer movementLayer,
			out IReadOnlyList<CPos> waypoints)
		{
			return TryGetStrategicSectorRoute(
				from,
				to,
				movementLayer,
				FransStrategicRoutePolicy.Fast,
				out waypoints);
		}

		public bool TryGetStrategicSectorRoute(
			CPos from,
			CPos to,
			FransStrategicMovementLayer movementLayer,
			FransStrategicRoutePolicy routePolicy,
			out IReadOnlyList<CPos> waypoints)
		{
			waypoints = Array.Empty<CPos>();

			var start = SectorIdForCell(from);
			var goal = SectorIdForCell(to);
			if (start < 0 || goal < 0 ||
				start >= sectors.Length || goal >= sectors.Length ||
				sectors[start] == null || sectors[goal] == null)
				return false;

			if (!SectorSupportsLayer(sectors[start], movementLayer) ||
				!SectorSupportsLayer(sectors[goal], movementLayer))
				return false;

			if (start == goal)
			{
				waypoints = new[] { to };
				return true;
			}

			var cacheKey = (start, goal, movementLayer, routePolicy);
			if (strategicSectorRouteMissCache.Contains(cacheKey))
				return false;
			if (strategicSectorRouteCache.TryGetValue(cacheKey, out var cachedSectorRoute))
			{
				waypoints = BuildStrategicRouteWaypoints(cachedSectorRoute, movementLayer, to);
				return true;
			}

			using var routePerf = FransBotLog.Profile(world, player, "StrategicMap.RouteBuild");
			var distance = new int[sectors.Length];
			var previous = new int[sectors.Length];
			var visited = new bool[sectors.Length];
			Array.Fill(distance, int.MaxValue);
			Array.Fill(previous, -1);
			distance[start] = 0;

			for (var iteration = 0; iteration < sectors.Length; iteration++)
			{
				var current = -1;
				var currentDistance = int.MaxValue;

				for (var id = 0; id < sectors.Length; id++)
				{
					if (visited[id] || distance[id] >= currentDistance)
						continue;

					current = id;
					currentDistance = distance[id];
				}

				if (current < 0)
					break;

				if (current == goal)
					break;

				visited[current] = true;

				foreach (var next in NeighborsForLayer(sectors[current], movementLayer))
				{
					if (next < 0 || next >= sectors.Length ||
						visited[next] ||
						!SectorSupportsLayer(sectors[next], movementLayer))
						continue;

					var stepCost = StrategicRouteStepCost(next, routePolicy);
					if (currentDistance > int.MaxValue - stepCost)
						continue;

					var candidate = currentDistance + stepCost;
					if (candidate >= distance[next])
						continue;

					distance[next] = candidate;
					previous[next] = current;
				}
			}

			if (previous[goal] == -1)
			{
				strategicSectorRouteMissCache.Add(cacheKey);
				return false;
			}

			var sectorRoute = new List<int>();
			for (var current = goal; current != start; current = previous[current])
			{
				if (current < 0)
				{
					strategicSectorRouteMissCache.Add(cacheKey);
					return false;
				}

				sectorRoute.Add(current);
			}

			sectorRoute.Reverse();
			var frozenSectorRoute = sectorRoute.ToArray();
			strategicSectorRouteCache[cacheKey] = frozenSectorRoute;
			waypoints = BuildStrategicRouteWaypoints(frozenSectorRoute, movementLayer, to);
			return true;
		}

		IReadOnlyList<CPos> BuildStrategicRouteWaypoints(IReadOnlyList<int> sectorRoute, FransStrategicMovementLayer movementLayer, CPos to)
		{
			var result = new List<CPos>((sectorRoute?.Count ?? 0) + 1);
			if (sectorRoute != null)
				foreach (var id in sectorRoute)
				{
					if (id < 0 || id >= sectors.Length || sectors[id] == null)
						continue;
					var center = CenterForLayer(sectors[id], movementLayer);
					if (center.HasValue)
						result.Add(center.Value);
				}

			if (result.Count == 0 || result[^1] != to)
				result.Add(to);
			return result;
		}

		int StrategicRouteStepCost(
			int sectorId,
			FransStrategicRoutePolicy routePolicy)
		{
			if (sectorId < 0 || sectorId >= sectorMetrics.Length)
				return 100;

			var metrics = sectorMetrics[sectorId];
			var sector = sectors[sectorId];

			switch (routePolicy)
			{
				case FransStrategicRoutePolicy.Safe:
					return Math.Max(20,
						100 +
						metrics.ThreatScore * 3 +
						metrics.EnemyControlScore * 2 +
						metrics.FrontlineScore);

				case FransStrategicRoutePolicy.Assault:
					// Assault still sees danger, but will accept a longer-known contested
					// corridor when it leads through strategically valuable ground.
					var strategicDiscount =
						metrics.ResourceValueScore / 10 +
						metrics.StrategicObjectiveValueScore / 12 +
						metrics.FrontlineScore / 5 +
						metrics.CentralityPercent / 3;

					return Math.Max(20,
						100 +
						metrics.ThreatScore +
						metrics.EnemyControlScore -
						Math.Min(60, strategicDiscount));

				default:
					return 100;
			}
		}

		static bool SectorSupportsLayer(
			FransStrategicSector sector,
			FransStrategicMovementLayer layer)
		{
			return layer switch
			{
				FransStrategicMovementLayer.Ground =>
					sector.GroundPassableCellCount > 0,
				FransStrategicMovementLayer.Mcv =>
					sector.McvPassableCellCount > 0,
				FransStrategicMovementLayer.Naval =>
					sector.NavalPassableCellCount > 0,
				_ => false
			};
		}

		static IReadOnlyList<int> NeighborsForLayer(
			FransStrategicSector sector,
			FransStrategicMovementLayer layer)
		{
			return layer switch
			{
				FransStrategicMovementLayer.Ground => sector.GroundNeighbors,
				FransStrategicMovementLayer.Mcv => sector.McvNeighbors,
				FransStrategicMovementLayer.Naval => sector.NavalNeighbors,
				_ => Array.Empty<int>()
			};
		}

		static CPos? CenterForLayer(
			FransStrategicSector sector,
			FransStrategicMovementLayer layer)
		{
			return layer switch
			{
				FransStrategicMovementLayer.Ground => sector.GroundCenter,
				FransStrategicMovementLayer.Mcv => sector.McvCenter,
				FransStrategicMovementLayer.Naval => sector.NavalCenter,
				_ => null
			};
		}


		void LogSummary()
		{
			var knownSectors = sectors.Count(s => s != null && s.KnownCellCount > 0);
			var groundSectors = sectors.Count(s =>
				s != null && s.GroundPassableCellCount >= Info.MinimumPassableCellsPerSector);
			var mcvSectors = sectors.Count(s =>
				s != null && s.McvPassableCellCount >= Info.MinimumPassableCellsPerSector);
			var navalSectors = sectors.Count(s =>
				s != null && s.NavalPassableCellCount >= Info.MinimumPassableCellsPerSector);
			var chokes = sectorMetrics.Count(m => m.GroundChokeScore > 0);
			var articulationChokes = sectorMetrics.Count(m => m.IsGroundArticulationPoint);
			var beachheads = sectors.Count(s => s?.IsBeachheadCandidate == true);
			var contestedResources = sectorMetrics.Count(m => m.IsContestedResourceSector);
			var highValueResources = sectorMetrics.Count(m => m.IsHighValueResourceSector);
			var objectiveSectors = sectorMetrics.Count(m => m.IsStrategicObjectiveSector);
			var frontlineSectors = sectorMetrics.Count(m => m.IsFrontlineSector);
			var localProductionPressureSectors = sectorMetrics.Count(m => m.NeedsLocalProductionCapacity);

			AIUtils.BotDebug(
				"{0}: StrategicMap [{1}] terrain-v{2}: known {3}/{4}, ground {5}, MCV {6}, naval {7}, choke {8} ({9} articulation), beachheads {10}, high-value resource sectors {11}, contested resource sectors {12}, remembered enemy structures {13}, mine/gmine {14}.",
				player,
				KnowledgeMode,
				TerrainKnowledgeVersion,
				knownSectors,
				sectors.Length,
				groundSectors,
				mcvSectors,
				navalSectors,
				chokes,
				articulationChokes,
				beachheads,
				highValueResources,
				contestedResources,
				knownEnemyStructures.Length,
				knownResourceCreators.Length);

			AIUtils.BotDebug(
				"{0}: StrategicMap objective/frontline: remembered objectives {1} across {2} sectors, frontline sectors {3}, local production-pressure sectors {4}.",
				player,
				knownStrategicObjectives.Length,
				objectiveSectors,
				frontlineSectors,
				localProductionPressureSectors);

			AIUtils.BotDebug(
				"{0}: StrategicMap global production pressure: PROC {1}, producers total {2} (WEAP {3}, infantry {4}, HPAD {5}, AFLD {6}, naval {7}), suggested minimum {8}, deficit {9}, pressure {10}%, needs capacity {11}.",
				player,
				productionPressure.RefineryCount,
				productionPressure.TotalMilitaryProducerCount,
				productionPressure.VehicleProducerCount,
				productionPressure.InfantryProducerCount,
				productionPressure.HelicopterProducerCount,
				productionPressure.PlaneProducerCount,
				productionPressure.NavalProducerCount,
				productionPressure.SuggestedMinimumMilitaryProducerCount,
				productionPressure.ProducerDeficit,
				productionPressure.PressurePercent,
				productionPressure.NeedsMoreProductionCapacity);

			if (primaryBaseCell.HasValue)
			{
				foreach (var priority in GetStrategicPrioritySectors(3))
					AIUtils.BotDebug(
						"{0}: StrategicMap priority sector {1} at {2}: score {3}, resource {4}, objective {5}, frontline {6}, threat {7}, enemy-control {8}, enemy objectives {9}, neutral objectives {10}, staging {11}.",
						player,
						priority.SectorId,
						priority.Target,
						priority.TotalScore,
						priority.ResourceValueScore,
						priority.StrategicObjectiveValueScore,
						priority.FrontlineScore,
						priority.ThreatScore,
						priority.EnemyControlScore,
						priority.EnemyStrategicObjectiveCount,
						priority.NeutralStrategicObjectiveCount,
						priority.SuggestedStagingPoint.HasValue
							? priority.SuggestedStagingPoint.Value.ToString()
							: "none");
			}
		}

	}
}
