#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;
using CAAIUtils = OpenRA.Mods.CA.AIUtils;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[Desc("Phase EX-0 of the expansion planner (docs/design/AI_ARCHITECTURE.md §12.13): scores every resource field",
		"we hold no refinery at by value x safety / time-until-it-pays and keeps the best one as the target field.",
		"Telemetry only: nothing reads the target yet (EX-1 makes the base builder walk toward it).")]
	public class ExpansionPlannerBotModuleInfo : ConditionalTraitInfo, NotBefore<ResourceMapBotModuleInfo>
	{
		[Desc("Ticks between two re-plans.")]
		public readonly int ReplanTicks = 250;

		[Desc("How far (cells) one new building extends the base: the step of the building line toward a field.")]
		public readonly int LinkStepCells = 4;

		[Desc("How far (cells) from a building that gives buildable area a refinery can still be placed next to a field.",
			"A field closer than this needs no link buildings.")]
		public readonly int ReachCells = 6;

		[Desc("Radius (cells) around a field's resource centre in which our own combat units count as its guard.")]
		public readonly int GuardRadiusCells = 12;

		[Desc("Smoothing (ticks) added to the time-until-it-pays, so a field next to the yard does not divide by ~0.")]
		public readonly int TauTicks = 750;

		[Desc("Window (ticks) over which the income used to turn costs into time is measured.")]
		public readonly int IncomeWindowTicks = 1500;

		[Desc("EX-1: publish the target field to the base builder, whose BaseCrawl placements then walk toward it.",
			"False = telemetry only (EX-0).")]
		public readonly bool DriveBaseCrawl = false;

		[Desc("EX-2: while the target field is in reach and unclaimed, ask the base builder for a refinery there, beyond",
			"its fixed optimum (every field in reach gets one). Needs DriveBaseCrawl, which publishes the target.")]
		public readonly bool DriveRefineries = false;

		[Desc("EX-2: an own refinery this close (cells) to a field's resource centre claims it.")]
		public readonly int ClaimRadiusCells = 8;

		[Desc("EX-2: refineries built while a field stayed unclaimed before the field is parked (a placement that keeps",
			"missing it must not turn into a refinery loop).")]
		public readonly int MaxClaimAttempts = 2;

		[Desc("EX-2: ticks a parked field is left out of the candidates.")]
		public readonly int ParkTicks = 3000;

		[Desc("EX-3: tell McvExpansionManagerBotModule where an MCV should found its next base (it still decides when).")]
		public readonly bool DriveMcvSite = false;

		[Desc("EX-3: only fields at least this many link buildings away are MCV sites; nearer ones the building line reaches.")]
		public readonly int McvMinHops = 3;

		[Desc("EX-3: smoothing (cells) added to the MCV's distance to a site, so the nearest field does not divide by ~0.")]
		public readonly int McvTauCells = 10;

		[Desc("LC3 (AI_REVIEW_FRANSOTTO P1a): the same field handed out this many times in a row is parked for ParkTicks.",
			"The MCV module only asks again for an IDLE MCV, so a repeat means the last attempt there failed (no deploy",
			"cell, blocked, or rejected); the module records its own checkspot, not ours, so without this the field comes",
			"back forever. 0 disables.")]
		public readonly int McvMaxSiteHandouts = 3;

		[Desc("Greedy expansion: the planner requests construction-MCV production itself while a free field beyond the",
			"building line's reach (McvMinHops) exists, instead of waiting for the MCV module's high cash trigger.",
			"The engine module still decides where to send it (EX-3) and placement/dedup is unchanged.")]
		public readonly bool DriveMcvRequests = false;

		[Desc("Greedy expansion: request a construction MCV only while cash+resources stays above this reserve.",
			"Well below the MCV module's own cash trigger, so a second MCV comes early.")]
		public readonly int McvRequestReserve = 1500;

		[Desc("Greedy expansion: construction yards + construction MCVs + queued MCVs the driver aims for.",
			"The engine module's own count/cash gates still apply to its requests on top of this.")]
		public readonly int McvTargetCount = 3;

		[Desc("UT-4 (AI_ARCHITECTURE §12.13): the TechRush<->Expansion utility axis scales the appetite —",
			"an Expansion-leaning personality raises the effective McvTargetCount, a TechRush-leaning one",
			"lowers it. Needs DriveMcvRequests. genericbot-only module, so classic is unaffected.")]
		public readonly bool UseUtilityExpansionAppetite = false;

		[Desc("UT-4: at the full Expansion pole the effective McvTargetCount grows by this many.")]
		public readonly int ExpansionAxisBonusMcvs = 2;

		[Desc("UT-4: at the full TechRush pole the effective McvTargetCount shrinks by this many (floor 1).")]
		public readonly int TechRushAxisMinusMcvs = 1;

		[Desc("EX-4 (AI_ARCHITECTURE §12.19): the appetite tracks the map, not a flat cap — while any reachable far",
			"field stays free, the driver keeps up to CoverAllFieldsMaxInflight construction MCVs in the queue on top",
			"of however many yards/MCVs already exist, so expansion only stops when every field is claimed (or",
			"unreachable/parked). Difficulty still paces it through BotLimits production intervals and the cash",
			"reserve — speed changes, the ceiling does not. Needs DriveMcvRequests.")]
		public readonly bool CoverAllFields = false;

		[Desc("EX-4: queued construction MCVs the cover-the-map driver holds in flight at once. Bounds the",
			"commitment, not the map: finished MCVs leave the queue and a new one is requested while fields remain.")]
		public readonly int CoverAllFieldsMaxInflight = 2;

		[Desc("TC-2c (AI_ARCHITECTURE §12.17): yield a free field to an allied bot's published expansion claim",
			"when it outranks us (lower ClientIndex). Deterministic precedence, so contested fields converge",
			"instead of oscillating. Inert in 1v1 — no allied broadcasts exist.")]
		public readonly bool UseTeamExpansionClaims = false;

		[Desc("TC-2c: an allied claim this close (cells) to a field's resource centre contests it.")]
		public readonly int AllyClaimRadiusCells = 10;

		[Desc("TC-3 / BD (AI_ARCHITECTURE §12.18): score the Voronoi sector anchored at our own spawn",
			"first — a field belongs to the coalition sector anchor nearest it; foreign-sector fields keep",
			"CoalitionForeignSectorPercent of their score (reachable, deprioritized, never forbidden).",
			"Needs the master's UseCoalitionPlan publishing the anchors; inert in 1v1 (the only anchor",
			"is our own) and bit-identical when no provider publishes.")]
		public readonly bool UseCoalitionSectors = false;

		[Desc("TC-3 / BD: percent of its score a foreign-sector field keeps. 0 would still leave the",
			"argmax free to pick a foreign field when no own-sector field remains; higher values shrink",
			"the home bias.")]
		public readonly int CoalitionForeignSectorPercent = 35;

		[Desc("BEV (AI_MASTER_PLAN §3; DESIGN §19.4 keeps BevManagerBotModule unloaded because this owner covers it):",
			"a vehicle in the MCV module's McvTypes that is NOT a construction MCV and does not deploy into a refinery is",
			"a base-building vehicle (Japan's cores) and deploys next to the base, not at a far field. Construction MCVs",
			"(EX-3) and field refineries (Yuri's slave miner, Japan's core refinery) keep going to fields.")]
		public readonly bool BaseVehiclesAtBase = true;

		[Desc("FE-1 (AI_ARCHITECTURE §12.24, DESIGN §19.1b; switch group AJ_field_coverage): one refinery per ANCHOR (a resource",
			"spreader, or the centre of a field that has none), placed on the free cell nearest the anchor; a refinery is wanted",
			"only while an anchor in building reach is unserved and never beyond the anchor count (replacing the yard-based",
			"cap, OptimalRefineryCount and the scale-target refinery cap). The MCV site and the crawl target also score a",
			"separation factor (different directions) and a spread factor (unexplored ground). Needs DriveRefineries.")]
		public readonly bool FieldCoverage = false;

		[Desc("FE-1: a field with a spreader within this many cells of its resource centre is represented by the spreader;",
			"a field without one is its own anchor.")]
		public readonly int SpreaderFieldRadiusCells = 12;

		[Desc("FE-1: an own refinery within this many cells of an anchor serves it (0 = ClaimRadiusCells).")]
		public readonly int AnchorServeRadiusCells = 0;

		[Desc("FE-1: replans an anchor may stay wanted with no refinery gained before it is parked for ParkTicks",
			"(a claim whose placement keeps failing must not retry forever).")]
		public readonly int AnchorStuckReplans = 12;

		[Desc("FE-1: the factor a site/field keeps when its bearing from the main base lies within CrawlSeparationDegrees of",
			"the crawl target, an own yard or another in-flight MCV site (deprioritised, never forbidden).")]
		public readonly double MinSeparationFactor = 0.25;

		[Desc("FE-1: the bearing window (degrees) inside which two directions count as the same direction.")]
		public readonly int CrawlSeparationDegrees = 35;

		[Desc("FE-1: score x (1 + SpreadBonus x distance to our nearest building / map diagonal), for the MCV site and the crawl target.")]
		public readonly double SpreadBonus = 1.0;

		[Desc("FE-1: a building closer than this (cells) to the main base has no usable bearing and is ignored by the separation factor.")]
		public readonly int MinBearingDistanceCells = 6;

		[Desc("Building queues searched for the refinery and the cheapest link building. Empty = the enabled base",
			"builder's own BuildingQueues (Cameo's classic mode builds from the player-level RABuilding queue).")]
		public readonly HashSet<string> BuildingQueues = new();

		public override object Create(ActorInitializer init) { return new ExpansionPlannerBotModule(init.Self, this); }
	}

	public enum McvRole { Expansion, FieldRefinery, BaseBuilding }

	public class ExpansionPlannerBotModule : ConditionalTrait<ExpansionPlannerBotModuleInfo>, IBotTick, IBotExpansionTargetProvider,
		IBotMcvExpansionSiteProvider, IBotPositionsUpdated, IBotExpansionAssistProvider
	{
		public readonly struct FieldScore
		{
			public readonly int Index;
			public readonly CPos Center;
			public readonly int Value;
			public readonly int Hops;
			public readonly int PaybackTicks;
			public readonly int Threat;
			public readonly double Score;
			public readonly double Safety;

			public FieldScore(int index, CPos center, int value, int hops, int paybackTicks, int threat, double score, double safety = 1)
			{
				Safety = safety;
				Index = index;
				Center = center;
				Value = value;
				Hops = hops;
				PaybackTicks = paybackTicks;
				Threat = threat;
				Score = score;
			}
		}

		readonly World world;
		readonly OpenRA.Player player;
		readonly Dictionary<int, int> initialCells = new();
		readonly Dictionary<int, CPos> initialCenters = new();
		readonly Queue<(int Tick, int Earned)> income = new();

		ResourceMapBotModule resourceMap;
		PlayerResources resources;
		IBotRegionThreatProvider[] threatProviders;
		BaseBuilderBotModuleCA[] baseBuilders;
		int ticks;
		string lastIdleReason;
		readonly Dictionary<int, int> claimAttempts = new();
		readonly Dictionary<int, int> parkedUntil = new();

		// LC3: the field last handed to an MCV and how many times in a row; fields an MCV's locomotor cannot reach
		// (kept as their own class: a future transport objective, FB1).
		(int Field, int Count) mcvHandout = (-1, 0);
		readonly HashSet<int> landUnreachableLogged = new();
		IPathFinder pathFinder;
		Actor self;
		(int Field, int Refineries) wanting = (-1, 0);
		bool wantsRefinery;
		FieldScore? claimField;

		// FE-1 (§12.24): the anchors and the claim of the last re-plan, own-building cells for the spread factor, and the
		// MCV sites handed out whose MCV is still on the way (actor id -> site).
		List<CPos> anchors = new();
		int unservedInReach;
		CPos? anchorClaim;
		CPos? anchorClaimFieldCenter;
		(CPos? Anchor, int Replans, int Refineries) anchorStuck = (null, 0, 0);
		readonly Dictionary<CPos, int> anchorParkedUntil = new();
		readonly Dictionary<uint, CPos> inflightMcvSites = new();
		List<CPos> ownBuildingCells = new();
		List<CPos> ownYardCells = new();

		// BEV: the base centre the base builder publishes (the parent BevManagerBotModule used the same signal), and the
		// construction MCVs of every MCV module on this player (Info-level: fixed for the match, safe to cache).
		CPos? baseCenter;
		readonly HashSet<string> constructionMcvTypes;
		readonly HashSet<string> constructionYardTypes;
		readonly Dictionary<string, McvRole> mcvRoles = new();
		IBotRequestUnitProduction[] unitBuilders;
		IBotUtilityAxes[] utilityAxesProviders;
		IBotScaleTargets[] scaleTargetProviders;

		public ExpansionPlannerBotModule(Actor self, ExpansionPlannerBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			constructionMcvTypes = self.Info.TraitInfos<McvExpansionManagerBotModuleInfo>()
				.SelectMany(i => i.ConstructionMcvTypes).ToHashSet();
			constructionYardTypes = self.Info.TraitInfos<McvExpansionManagerBotModuleInfo>()
				.SelectMany(i => i.ConstructionYardTypes).ToHashSet();
		}

		void IBotPositionsUpdated.UpdatedBaseCenter(CPos newLocation) { baseCenter = newLocation; }

		void IBotPositionsUpdated.UpdatedDefenseCenter(CPos newLocation) { }

		/// <summary>BEV's rule, free of world state so it can be tested.</summary>
		public static McvRole ClassifyMcv(bool constructionMcv, bool deploysIntoRefinery) =>
			constructionMcv ? McvRole.Expansion : deploysIntoRefinery ? McvRole.FieldRefinery : McvRole.BaseBuilding;

		McvRole RoleOf(ActorInfo vehicle)
		{
			if (mcvRoles.TryGetValue(vehicle.Name, out var role))
				return role;

			var into = vehicle.TraitInfoOrDefault<TransformsInfo>()?.IntoActor;
			var intoInfo = into != null && world.Map.Rules.Actors.TryGetValue(into, out var ai) ? ai : null;
			role = ClassifyMcv(constructionMcvTypes.Contains(vehicle.Name), intoInfo?.HasTraitInfo<RefineryInfo>() ?? false);
			mcvRoles[vehicle.Name] = role;
			return role;
		}

		/// <summary>The best field of the last re-plan; null when there is none (EX-1 reads it).</summary>
		public FieldScore? Target { get; private set; }

		public IReadOnlyList<FieldScore> LastScores { get; private set; } = Array.Empty<FieldScore>();

		/// <summary>Telemetry only (12.24 FE-0): the last field handed to an MCV as its site. Never read by a decision.</summary>
		public CPos? LastMcvSite { get; private set; }

		CPos? IBotExpansionTargetProvider.ExpansionTarget => IsTraitDisabled || !Info.DriveBaseCrawl ? null : Target?.Center;

		bool IBotExpansionTargetProvider.WantsRefineryAtExpansionTarget => !IsTraitDisabled && Info.DriveRefineries && wantsRefinery;

		int IBotExpansionTargetProvider.ExpansionTargetClaimRadius => Info.ClaimRadiusCells;

		CPos? IBotExpansionTargetProvider.RefineryClaimTarget => IsTraitDisabled || !Info.DriveRefineries ? null
			: LawActive ? anchorClaim : claimField?.Center;

		bool LawActive => !IsTraitDisabled && Info.FieldCoverage && Info.DriveRefineries && anchors.Count > 0;

		bool IBotExpansionTargetProvider.RefineryLawActive => LawActive;

		int IBotExpansionTargetProvider.RefineryAnchorCount => LawActive ? anchors.Count : 0;

		int IBotExpansionTargetProvider.UnservedAnchorsInReach => LawActive ? unservedInReach : 0;

		CPos? IBotExpansionTargetProvider.RefineryClaimFieldCenter => LawActive ? anchorClaimFieldCenter : null;

		/// <summary>
		/// TC-3 (§12.18): the claim that wants a bodyguard — the current target field while its
		/// evaluated threat is non-trivial. Threat is the remembered-enemy sum the region threat
		/// providers publish at the field's centre (the same term Safety() folds into the score),
		/// so "contested" is the fog-honest memory, not a live peek. An uncontested target needs
		/// no escort and no target publishes nothing — null, never a behaviour change.
		/// </summary>
		WPos? IBotExpansionAssistProvider.ExpansionAssistTarget
		{
			get
			{
				if (IsTraitDisabled || !(Target is FieldScore target) || target.Threat <= 0)
					return null;

				return world.Map.CenterOfCell(target.Center);
			}
		}

		/// <summary>EX-2: a field counts as ours when an own refinery stands within the claim radius of its resource centre.</summary>
		public static bool Claimed(CPos center, IEnumerable<CPos> refineries, int claimRadiusCells)
		{
			return refineries.Any(r => (r - center).LengthSquared <= claimRadiusCells * claimRadiusCells);
		}

		/// <summary>
		/// EX-2 loop guard: while we want a refinery at `field`, every refinery we gain without the field turning ours is a
		/// missed claim. Returns the updated state and whether the field must now be parked.
		/// </summary>
		public static ((int Field, int Refineries) Wanting, int Attempts, bool Park) TrackClaim(
			(int Field, int Refineries) wanting, int field, int refineries, int attempts, int maxAttempts)
		{
			if (wanting.Field != field)
				return ((field, refineries), attempts, false);

			if (refineries > wanting.Refineries)
				attempts += refineries - wanting.Refineries;

			return ((field, refineries), attempts, attempts >= maxAttempts);
		}

		protected override void TraitEnabled(Actor self)
		{
			this.self = self;
			pathFinder = self.World.WorldActor.TraitOrDefault<IPathFinder>();
			resourceMap = self.TraitsImplementing<ResourceMapBotModule>().FirstOrDefault(t => t.IsTraitEnabled());
			resources = self.TraitOrDefault<PlayerResources>();
			threatProviders = self.TraitsImplementing<IBotRegionThreatProvider>().ToArray();
			baseBuilders = self.TraitsImplementing<BaseBuilderBotModuleCA>().ToArray();
			unitBuilders = self.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
			utilityAxesProviders = self.TraitsImplementing<IBotUtilityAxes>().ToArray();
			scaleTargetProviders = self.TraitsImplementing<IBotScaleTargets>().ToArray();
		}

		/// <summary>
		/// §12.13: score = V x S / (T + tau), S = 1 / (1 + threat / max(guard, 1)),
		/// T = cost / income + hops x link build time + refinery build time. Pure, for the tests.
		/// </summary>
		public static double Score(int value, int threat, int guard, int costCredits, double incomePerTick,
			int hops, int linkBuildTicks, int refineryBuildTicks, int tauTicks, out int paybackTicks)
		{
			// No income yet: every credit costs a tick, so fields still rank by cost, distance and value.
			var costTicks = incomePerTick > 0 ? costCredits / incomePerTick : costCredits;
			paybackTicks = (int)Math.Min(int.MaxValue, costTicks + (long)hops * linkBuildTicks + refineryBuildTicks);
			var safety = Safety(threat, guard);
			return value * safety / (paybackTicks + Math.Max(tauTicks, 1));
		}

		public static double Safety(int threat, int guard) => 1.0 / (1.0 + threat / (double)Math.Max(guard, 1));

		/// <summary>
		/// EX-3: the MCV site among the far fields (at least `minHops` links away): value x safety / (distance from the
		/// MCV + tau). Nearer fields are the building line's job (EX-1/EX-2). Null when no far field is free.
		/// </summary>
		public static FieldScore? McvSite(IEnumerable<FieldScore> fields, CPos mcv, int minHops, int tauCells,
			Func<FieldScore, bool> eligible = null, Func<FieldScore, double> weight = null)
		{
			FieldScore? best = null;
			var bestScore = double.MinValue;
			foreach (var f in fields)
			{
				if (f.Hops < minHops || (eligible != null && !eligible(f)))
					continue;

				var score = f.Value * f.Safety / ((f.Center - mcv).Length + Math.Max(tauCells, 1));

				// FE-1: separation x spread (null = master behaviour, bit-identical).
				if (weight != null)
					score *= weight(f);

				if (score > bestScore)
				{
					bestScore = score;
					best = f;
				}
			}

			return best;
		}

		// ---- FE-1 (§12.24): pure helpers, free of world state so they can be tested ----

		/// <summary>
		/// FE-1: the anchors - every resource spreader (deduplicated, input order), then the centre of every field with no
		/// spreader within `spreaderRadiusCells` of it. One refinery per anchor.
		/// </summary>
		public static List<CPos> BuildAnchors(IEnumerable<CPos> spreaders, IEnumerable<CPos> fieldCenters, int spreaderRadiusCells)
		{
			var result = new List<CPos>();
			foreach (var s in spreaders)
				if (!result.Contains(s))
					result.Add(s);

			var spreaderCount = result.Count;
			var r2 = (long)spreaderRadiusCells * spreaderRadiusCells;
			foreach (var f in fieldCenters)
			{
				var covered = false;
				for (var i = 0; i < spreaderCount && !covered; i++)
					covered = (result[i] - f).LengthSquared <= r2;

				if (!covered && !result.Contains(f))
					result.Add(f);
			}

			return result;
		}

		/// <summary>
		/// FE-1: which refinery serves which anchor - a result per anchor, the refinery index or -1. Greedy by ascending
		/// distance (ties by anchor then refinery index) within `serveRadiusCells`; every refinery serves at most one anchor
		/// and every anchor has at most one refinery, so two spreaders next to one refinery do not both count as served.
		/// </summary>
		public static int[] AssignRefineries(IReadOnlyList<CPos> anchorCells, IReadOnlyList<CPos> refineries, int serveRadiusCells)
		{
			var result = new int[anchorCells.Count];
			Array.Fill(result, -1);
			var r2 = (long)serveRadiusCells * serveRadiusCells;
			var pairs = new List<(long D, int A, int R)>();
			for (var a = 0; a < anchorCells.Count; a++)
				for (var r = 0; r < refineries.Count; r++)
				{
					var d = (anchorCells[a] - refineries[r]).LengthSquared;
					if (d <= r2)
						pairs.Add((d, a, r));
				}

			pairs.Sort((x, y) => x.D != y.D ? x.D.CompareTo(y.D) : x.A != y.A ? x.A.CompareTo(y.A) : x.R.CompareTo(y.R));
			var used = new bool[refineries.Count];
			foreach (var (_, a, r) in pairs)
			{
				if (result[a] >= 0 || used[r])
					continue;

				result[a] = r;
				used[r] = true;
			}

			return result;
		}

		/// <summary>
		/// FE-1 refinery-wanted rule: the anchor the next refinery claims, or -1. Wanted iff an anchor within `reachCells` of a
		/// building that gives buildable area is unserved (and not parked) AND the refinery count (placed + queued) is below
		/// the anchor count - never more refineries than anchors. Among the candidates the one nearest a building wins (ties:
		/// lowest index). `unservedInReach` counts all unserved in-reach anchors, parked or not.
		/// </summary>
		public static int WantedAnchor(IReadOnlyList<CPos> anchorCells, IReadOnlyList<CPos> refineries, IReadOnlyList<CPos> buildingCells,
			int serveRadiusCells, int reachCells, Func<int, bool> parked, int queuedRefineries, out int unservedInReach)
		{
			unservedInReach = 0;
			var assigned = AssignRefineries(anchorCells, refineries, serveRadiusCells);
			var best = -1;
			var bestDistance = int.MaxValue;
			for (var a = 0; a < anchorCells.Count; a++)
			{
				if (assigned[a] >= 0)
					continue;

				var distance = int.MaxValue;
				foreach (var b in buildingCells)
					distance = Math.Min(distance, (b - anchorCells[a]).Length);

				if (distance > reachCells)
					continue;

				unservedInReach++;
				if (parked != null && parked(a))
					continue;

				if (distance < bestDistance)
				{
					bestDistance = distance;
					best = a;
				}
			}

			return refineries.Count + queuedRefineries >= anchorCells.Count ? -1 : best;
		}

		/// <summary>FE-1: the bearing of `to` as seen from `from`, integer (WAngle.ArcTan).</summary>
		public static WAngle Bearing(CPos from, CPos to) => WAngle.ArcTan(to.Y - from.Y, to.X - from.X);

		/// <summary>FE-1: the smaller angle between two bearings, in WAngle units (0..512).</summary>
		public static int BearingDelta(WAngle a, WAngle b)
		{
			var d = Math.Abs(a.Angle - b.Angle) % 1024;
			return d > 512 ? 1024 - d : d;
		}

		/// <summary>
		/// FE-1: the separation factor of a site - `minFactor` when its bearing from `origin` (the main base) lies within
		/// `degrees` of the bearing of any `avoid` position (the crawl target, own yards, other in-flight MCV sites), else 1.
		/// A position closer than `minDistanceCells` to the origin has no usable bearing and is skipped.
		/// </summary>
		public static double SeparationFactor(CPos site, CPos origin, IEnumerable<CPos> avoid, int degrees, double minFactor, int minDistanceCells)
		{
			if ((site - origin).Length < 1)
				return 1;

			var siteBearing = Bearing(origin, site);
			var window = WAngle.FromDegrees(degrees).Angle;
			foreach (var other in avoid)
			{
				if ((other - origin).Length < Math.Max(minDistanceCells, 1))
					continue;

				if (BearingDelta(siteBearing, Bearing(origin, other)) <= window)
					return minFactor;
			}

			return 1;
		}

		/// <summary>FE-1: 1 + bonus x distance-to-our-nearest-building / map diagonal (unexplored ground wins ties).</summary>
		public static double SpreadFactor(int distanceToNearestBuildingCells, int mapDiagonalCells, double bonus)
		{
			return 1 + bonus * Math.Max(distanceToNearestBuildingCells, 0) / Math.Max(mapDiagonalCells, 1);
		}

		/// <summary>FE-1: is the field's centre within `radiusCells` of a site an MCV is already heading to?</summary>
		public static bool TakenByMcvSite(CPos center, IEnumerable<CPos> sites, int radiusCells)
		{
			return sites.Any(s => (s - center).LengthSquared <= (long)radiusCells * radiusCells);
		}

		/// <summary>
		/// EX-2c: the field the next refinery should claim — the best-scoring free field already in buildable
		/// reach (`scores` is score-sorted, parked and claimed fields never reach it). Any in-reach field
		/// qualifies, not only the crawl target: an outpost yard draws its refinery the moment it can place
		/// one. Pure, for the tests.
		/// </summary>
		public static FieldScore? BestClaimField(IReadOnlyList<FieldScore> scores)
		{
			for (var i = 0; i < scores.Count; i++)
				if (scores[i].Hops == 0)
					return scores[i];

			return null;
		}

		/// <summary>
		/// TC-2c: does an allied claim outrank ours on `field`? The lower ClientIndex wins — a stable,
		/// arbitrary precedence both bots compute identically, so a contested field converges instead of
		/// both allies yielding forever. Pure, for the tests.
		/// </summary>
		public static bool AllyClaimWins(WPos field, IEnumerable<(int ClientIndex, WPos Claim)> allyClaims,
			int myClientIndex, int radiusCells)
		{
			var radiusW = 1024L * radiusCells;
			foreach (var (index, claim) in allyClaims)
				if (index < myClientIndex && (field - claim).HorizontalLengthSquared <= radiusW * radiusW)
					return true;

			return false;
		}

		/// <summary>
		/// TC-3 / BD (§12.18): the Voronoi score percent — a field belongs to the coalition sector
		/// anchor nearest it (min HorizontalLengthSquared, the same horizontal measure AllyClaimWins
		/// uses, so terrain height cannot tilt a border). The anchor holding our own participant id
		/// keeps 100, a foreign anchor keeps `foreignPercent`; a distance tie goes to the ordinally
		/// smallest id so every member computes the identical partition. Pure, for the tests.
		/// </summary>
		public static int SectorScorePercent(WPos field, IReadOnlyDictionary<string, WPos> anchors,
			string myId, int foreignPercent)
		{
			if (anchors == null || anchors.Count == 0)
				return 100;

			string nearest = null;
			var best = long.MaxValue;
			foreach (var kv in anchors)
			{
				var d = (kv.Value - field).HorizontalLengthSquared;
				if (d < best || (d == best && string.CompareOrdinal(kv.Key, nearest) < 0))
				{
					best = d;
					nearest = kv.Key;
				}
			}

			return nearest == myId ? 100 : Math.Clamp(foreignPercent, 0, 100);
		}

		/// <summary>LC3: one more hand-out of `field`; returns the new streak and whether the field must now be parked.</summary>
		public static ((int Field, int Count) Streak, bool Park) TrackMcvHandout((int Field, int Count) streak, int field, int maxHandouts)
		{
			var count = streak.Field == field ? streak.Count + 1 : 1;
			if (maxHandouts > 0 && count > maxHandouts)
				return ((-1, 0), true);

			return ((field, count), false);
		}

		/// <summary>
		/// Greedy expansion: an extra construction MCV is worth its queue slot while a field beyond the building
		/// line's reach is free and we still hold the cash reserve. Pure, for the tests.
		/// </summary>
		public static bool ShouldRequestMcv(int cash, int reserve, bool farFieldFree, int activePlusQueued, int targetCount)
		{
			return farFieldFree && cash >= reserve && activePlusQueued < targetCount;
		}

		/// <summary>
		/// UT-4: the effective MCV appetite under the TechRush&lt;-&gt;Expansion axis — Expansion leans add up to
		/// +expansionBonus at the pole, TechRush leans subtract up to -techrushMinus (floor 1: never zero appetite).
		/// Neutral (50) returns the base count verbatim. Pure, for the tests.
		/// </summary>
		public static int EffectiveMcvTargetCount(int baseTarget, int axis, int expansionBonus, int techrushMinus)
		{
			if (axis > IBotUtilityAxes.Neutral)
				return baseTarget + (int)Math.Round((axis - IBotUtilityAxes.Neutral) / (double)IBotUtilityAxes.Neutral * expansionBonus);

			return Math.Max(1, baseTarget - (int)Math.Round((IBotUtilityAxes.Neutral - Math.Max(0, axis)) / (double)IBotUtilityAxes.Neutral * techrushMinus));
		}

		void RequestMcv(IBot bot)
		{
			if (unitBuilders == null || resources == null)
				return;

			// A construction MCV pays only if the building line cannot reach a free field soon.
			var farFieldFree = LastScores.Any(f => f.Hops >= Info.McvMinHops
				&& !(parkedUntil.TryGetValue(f.Index, out var until) && world.WorldTick < until));

			// Yards + construction MCVs in the field + MCVs already in a queue (factory-level and player-level).
			var active = world.Actors.Count(a => a.Owner == player && !a.IsDead
				&& (constructionMcvTypes.Contains(a.Info.Name) || constructionYardTypes.Contains(a.Info.Name)));
			var queued = world.ActorsWithTrait<ProductionQueue>()
				.Where(tp => tp.Actor.Owner == player && tp.Trait.Enabled)
				.SelectMany(tp => tp.Trait.AllQueued())
				.Concat(player.PlayerActor.TraitsImplementing<ProductionQueue>()
					.Where(t => t.Enabled)
					.SelectMany(t => t.AllQueued()))
				.Count(q => constructionMcvTypes.Contains(q.Item));

			// UT-4: the TechRush<->Expansion axis scales the appetite — Expansion personalities keep more
			// MCVs flowing, TechRush ones hold back (the engine's own gates still apply on top either way).
			// Scale targets (DESIGN 19.10): with an enabled provider the construction-yard target IS this count, and UT-4's
			// axis lean lives inside the provider (one multiplier, never two), so the planner applies neither fixed number.
			var targetCount = Info.McvTargetCount;
			if (scaleTargetProviders.TryTarget("conyard", out var scaledYards))
				targetCount = scaledYards;
			else if (Info.UseUtilityExpansionAppetite)
			{
				var axis = utilityAxesProviders?.FirstEnabledTraitOrDefault()?.UtilityTechRushExpansion ?? IBotUtilityAxes.Neutral;
				targetCount = EffectiveMcvTargetCount(Info.McvTargetCount, axis, Info.ExpansionAxisBonusMcvs, Info.TechRushAxisMinusMcvs);
			}

			// EX-4: cover the whole map. The flat McvTargetCount ceiling is what made the stack stop at one
			// expansion — active yards count against it, so three yards meant "never request again". With
			// CoverAllFields the target becomes "as many active construction assets as exist, plus a bounded
			// inflight pipeline whenever a reachable far field is still free". freeFarFields==0 keeps a one-MCV
			// replacement allowance so a lost yard can be refounded.
			if (Info.CoverAllFields)
			{
				var tick = world.WorldTick;
				var freeFarFields = LastScores.Count(f => f.Hops >= Info.McvMinHops
					&& !(parkedUntil.TryGetValue(f.Index, out var until) && tick < until));
				var inflightCap = Math.Min(Math.Max(freeFarFields, 1), Math.Max(1, Info.CoverAllFieldsMaxInflight));
				targetCount = Math.Max(targetCount, active + inflightCap);
			}

			if (!ShouldRequestMcv(resources.GetCashAndResources(), Info.McvRequestReserve, farFieldFree, active + queued, targetCount))
				return;

			var unitBuilder = unitBuilders.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return;

			var producible = world.ActorsWithTrait<ProductionQueue>()
				.Where(a => a.Actor.Owner == player && a.Trait.Enabled)
				.SelectMany(a => a.Trait.BuildableItems())
				.Select(i => i.Name)
				.Where(constructionMcvTypes.Contains)
				.Distinct()
				.ToArray();
			if (producible.Length == 0)
				return;

			var mcvType = producible.Random(world.LocalRandom);
			if (unitBuilder.RequestedProductionCount(bot, mcvType) > 0)
				return;

			unitBuilder.RequestUnitProduction(bot, mcvType);
			var line = $"AI ({player.ClientIndex}): greedy MCV request {mcvType}: {active} active yards/MCVs, {queued} queued, cash {resources.GetCashAndResources()}, at tick {world.WorldTick}";
			Log.Write("debug", line);
			AIUtils.BotDebug(line);
		}

		CPos? IBotMcvExpansionSiteProvider.McvExpansionSite(Actor mcv)
		{
			// A deploying yard relocation (no Mobile) keeps the MCV module's own choice.
			if (IsTraitDisabled || mcv == null || !mcv.Info.HasTraitInfo<MobileInfo>())
				return null;

			// BEV: a base-building vehicle deploys at home; the MCV module's deploy search takes the cells 2-20 around it.
			if (Info.BaseVehiclesAtBase && baseCenter.HasValue && RoleOf(mcv.Info) == McvRole.BaseBuilding)
			{
				Log.Write("debug", $"AI ({player.ClientIndex}): BEV {mcv.Info.Name} {mcv.ActorID} deploys at the base {baseCenter.Value} (not a construction MCV, not a refinery) at tick {world.WorldTick}");
				return baseCenter;
			}

			if (!Info.DriveMcvSite)
				return null;

			var tick = world.WorldTick;
			var locomotor = mcv.TraitOrDefault<Mobile>()?.Locomotor;
			bool Eligible(FieldScore f)
			{
				if (parkedUntil.TryGetValue(f.Index, out var until) && tick < until)
					return false;

				// LC3: never send an MCV to a field its locomotor cannot reach (the MCV module's deploy search would
				// reject it and record its own checkspot, not this field).
				if (pathFinder != null && locomotor != null
					&& !pathFinder.PathMightExistForLocomotorBlockedByImmovable(locomotor, mcv.Location, f.Center))
				{
					if (landUnreachableLogged.Add(f.Index))
						Log.Write("debug", $"AI ({player.ClientIndex}): LC3 field {f.Index} at {f.Center} is not reachable for {mcv.Info.Name} ({locomotor.Info.Name}) from {mcv.Location} at tick {tick}");

					return false;
				}

				return true;
			}

			// FE-1 (§12.24): MCV and crawl cover different ground. A site scores x SeparationFactor (its bearing from the main
			// base must differ from the crawl target's, any own yard's and any other in-flight MCV site's) x SpreadFactor
			// (far from everything we own). Null weight (switch off) = master behaviour.
			Func<FieldScore, double> weight = null;
			if (Info.FieldCoverage)
			{
				var origin = baseCenter ?? (ownYardCells.Count > 0 ? ownYardCells[0] : mcv.Location);
				var avoid = new List<CPos>(ownYardCells);
				if (Target is FieldScore crawl)
					avoid.Add(crawl.Center);

				foreach (var kv in inflightMcvSites)
					if (kv.Key != mcv.ActorID)
						avoid.Add(kv.Value);

				var diagonal = MapDiagonalCells();
				weight = f => SeparationFactor(f.Center, origin, avoid, Info.CrawlSeparationDegrees, Info.MinSeparationFactor, Info.MinBearingDistanceCells)
					* SpreadFactor(NearestOwnBuildingDistance(f.Center), diagonal, Info.SpreadBonus);
			}

			// At most one park per request: a parked field falls out and the next best is offered.
			for (var attempt = 0; attempt < 2; attempt++)
			{
				if (McvSite(LastScores, mcv.Location, Info.McvMinHops, Info.McvTauCells, Eligible, weight) is not FieldScore s)
					return null;

				(mcvHandout, var park) = TrackMcvHandout(mcvHandout, s.Index, Info.McvMaxSiteHandouts);
				if (park)
				{
					parkedUntil[s.Index] = tick + Info.ParkTicks;
					Log.Write("debug", $"AI ({player.ClientIndex}): LC3 parked field {s.Index} at {s.Center} for {Info.ParkTicks} ticks: handed to an idle MCV more than {Info.McvMaxSiteHandouts} times in a row, no yard founded, at tick {tick}");
					continue;
				}

				if (Info.FieldCoverage)
					inflightMcvSites[mcv.ActorID] = s.Center;

				Log.Write("debug", $"AI ({player.ClientIndex}): EX-3 MCV {mcv.Info.Name} at {mcv.Location} sent to field {s.Index} at {s.Center}: value {s.Value}, hops {s.Hops}, safety {s.Safety:F2}, hand-out {mcvHandout.Count} at tick {tick}");
				LastMcvSite = s.Center;
				return s.Center;
			}

			return null;
		}

		/// <summary>
		/// EX-2d: the centre to score/claim for a field — the live centre while resource cells exist;
		/// a depleted field's live centre collapses (the resource map recomputes it every scan and an
		/// empty field has none), so fall back to the remembered first-seen centre instead of aiming
		/// refineries at the map corner. Pure, for the tests.
		/// </summary>
		public static CPos EffectiveCenter(int liveCellCount, CPos liveCenter, CPos rememberedCenter)
		{
			return liveCellCount > 0 ? liveCenter : rememberedCenter;
		}

		/// <summary>Buildings needed to bring the base within reach of a field `distance` cells away.</summary>
		public static int Hops(int distanceCells, int reachCells, int stepCells)
		{
			var gap = distanceCells - reachCells;
			return gap <= 0 ? 0 : (gap + Math.Max(stepCells, 1) - 1) / Math.Max(stepCells, 1);
		}

		int MapDiagonalCells()
		{
			var size = world.Map.MapSize;
			return (int)Math.Sqrt((long)size.Width * size.Width + (long)size.Height * size.Height);
		}

		int NearestOwnBuildingDistance(CPos cell)
		{
			var best = int.MaxValue;
			foreach (var b in ownBuildingCells)
				best = Math.Min(best, (b - cell).Length);

			return best == int.MaxValue ? 0 : best;
		}

		void IBotTick.BotTick(IBot bot)
		{
			// LC4 (AI_REVIEW_FRANSOTTO P1c): TraitEnabled may run before the resource map's own condition is granted in
			// the same batch, so a null / disabled cache is re-resolved here instead of idling for the whole match.
			if (resourceMap == null || !resourceMap.IsTraitEnabled())
				resourceMap = self.TraitsImplementing<ResourceMapBotModule>().FirstOrDefault(t => t.IsTraitEnabled());

			if (resourceMap == null || resources == null)
			{
				if (++ticks % Info.ReplanTicks == 0)
					Idle(resourceMap == null ? "no enabled ResourceMapBotModule" : "no PlayerResources");
				return;
			}

			income.Enqueue((world.WorldTick, resources.Earned));
			while (income.Count > 1 && world.WorldTick - income.Peek().Tick > Info.IncomeWindowTicks)
				income.Dequeue();

			if (++ticks % Info.ReplanTicks != 0)
				return;

			Replan(bot);
		}

		void Replan(IBot bot)
		{
			var (refinery, link, queues) = CheapestBuildables();
			if (refinery.Info == null)
			{
				Target = null;
				LastScores = Array.Empty<FieldScore>();
				Idle($"no refinery buildable ({queues} building queue(s) searched)");
				return;
			}

			// One pass over OUR OWN actors (always visible to us: fog-honest): the cells of the buildings that extend the
			// base (GivesBuildableArea; a captured derrick or a garrisoned house does not), and guard units.
			var buildingCells = new List<CPos>();
			var refineryCells = new List<CPos>();
			var guards = new List<(CPos Cell, int Value)>();
			var allBuildingCells = new List<CPos>();
			var yardCells = new List<CPos>();
			foreach (var a in world.Actors)
			{
				if (a.Owner != player || a.IsDead || !a.IsInWorld)
					continue;

				// The Refinery trait, from rules (the by-name lists are filled by the role rollout, §2.8).
				if (a.Info.HasTraitInfo<RefineryInfo>())
					refineryCells.Add(a.Location);

				if (Info.FieldCoverage)
				{
					if (a.Info.HasTraitInfo<BuildingInfo>())
						allBuildingCells.Add(a.Location);

					if (constructionYardTypes.Contains(a.Info.Name))
						yardCells.Add(a.Location);
				}

				if (a.Info.HasTraitInfo<GivesBuildableAreaInfo>())
					buildingCells.Add(a.Location);
				else if (a.Info.HasTraitInfo<BuildingInfo>())
					continue;
				else if (a.Info.HasTraitInfo<AttackBaseInfo>() && !a.Info.HasTraitInfo<HarvesterInfo>())
					guards.Add((a.Location, a.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0));
			}

			if (buildingCells.Count == 0)
			{
				Idle("no own building gives buildable area");
				return;
			}

			if (Info.FieldCoverage)
			{
				ownBuildingCells = allBuildingCells;
				ownYardCells = yardCells;

				// An MCV that is gone (deployed into a yard, or dead) no longer holds its site.
				foreach (var id in inflightMcvSites.Keys.ToArray())
				{
					var heading = world.GetActorById(id);
					if (heading == null || heading.IsDead || !heading.IsInWorld || heading.Owner != player)
						inflightMcvSites.Remove(id);
				}
			}

			var diagonalCells = Info.FieldCoverage ? MapDiagonalCells() : 1;
			var first = income.Count > 0 ? income.Peek() : (Tick: world.WorldTick, Earned: resources.Earned);
			var span = Math.Max(1, world.WorldTick - first.Tick);
			var incomePerTick = (resources.Earned - first.Earned) / (double)span;
			var reach = Info.ReachCells;
			var scores = new List<FieldScore>();
			var fields = resourceMap.GetIndicesLength();
			var owned = 0;

			// TC-2c (§12.17): allied expansion claims off the team blackboard — only the ones that
			// outrank us (lower ClientIndex). No allies → empty → every field behaves as before.
			List<(int ClientIndex, WPos Claim)> allyClaims = null;
			if (Info.UseTeamExpansionClaims)
			{
				allyClaims = TeamBlackboard.CollectBroadcasts(player)
					.Where(b => b != null && b.ExpansionClaim != WPos.Zero)
					.Select(b => (b.ClientIndex, b.ExpansionClaim))
					.ToList();
			}

			// TC-3 / BD (§12.18): the coalition's Voronoi partition — every allied spawn anchor owns
			// the fields nearest it. Resolved once per re-plan; a missing provider or an empty anchor
			// map leaves every score untouched (1v1, flag off — bit-identical).
			IReadOnlyDictionary<string, WPos> sectorAnchors = null;
			if (Info.UseCoalitionSectors)
			{
				var anchors = player.PlayerActor.TraitsImplementing<IBotCoalition>()
					.FirstEnabledTraitOrDefault()?.Coalition?.SectorAnchors;
				if (anchors != null && anchors.Count > 0)
					sectorAnchors = anchors;
			}

			for (var i = 0; i < resourceMap.GetIndicesLength(); i++)
			{
				var field = resourceMap.GetIndice(i);
				if (field == null || (field.ResourceCellsCount <= 0 && !initialCells.ContainsKey(i)))
					continue;

				// Ruling (c): the field's size at match start is public map data. The first scan of a field
				// fixes its value; depletion under the fog is never read (EX-1 adds depletion that was seen).
				if (!initialCells.TryGetValue(i, out var value))
				{
					initialCells[i] = value = field.ResourceCellsCount;
					initialCenters[i] = field.ResourceCellsCenter;
				}

				// The centre drifts as the field depletes (the resource map recomputes it every scan), so a refinery near
				// either the current or the first-seen centre claims it; otherwise a claimed field could look free again.
				// EX-2d: fully depleted fields report a degenerate live centre — score/aim at the remembered
				// first-seen centre instead (the field regrows; its location does not move).
				var center = EffectiveCenter(field.ResourceCellsCount, field.ResourceCellsCenter, initialCenters[i]);
				var claimed = Claimed(center, refineryCells, Info.ClaimRadiusCells)
					|| Claimed(initialCenters[i], refineryCells, Info.ClaimRadiusCells);
				if (field.PlayerRefineryCount > 0 || claimed || value <= 0)
				{
					owned += value > 0 ? 1 : 0;
					continue;
				}

				if (parkedUntil.TryGetValue(i, out var until) && world.WorldTick < until)
					continue;

				// TC-2c: an outranking ally already aims at this field — yield instead of stacking.
				if (allyClaims != null && allyClaims.Count > 0
					&& AllyClaimWins(world.Map.CenterOfCell(center), allyClaims, player.ClientIndex, Info.AllyClaimRadiusCells))
					continue;

				var distance = buildingCells.Min(c => (c - center).Length);
				var hops = Hops(distance, reach, Info.LinkStepCells);
				var threat = threatProviders.Sum(p => p.RememberedEnemyThreatAt(center));
				var guardValue = guards.Where(g => (g.Cell - center).LengthSquared <= Info.GuardRadiusCells * Info.GuardRadiusCells)
					.Sum(g => g.Value);
				var cost = refinery.Cost + hops * link.Cost;
				var score = Score(value, threat, guardValue, cost, incomePerTick, hops, link.BuildTicks, refinery.BuildTicks,
					Info.TauTicks, out var payback);

				// TC-3 / BD: own-sector fields keep their full score, foreign-sector fields keep
				// CoalitionForeignSectorPercent of it — deprioritized, never forbidden: the argmax
				// still picks a foreign field when no own-sector field is left.
				if (sectorAnchors != null)
					score *= SectorScorePercent(world.Map.CenterOfCell(center), sectorAnchors,
						player.InternalName ?? "#" + player.ClientIndex, Info.CoalitionForeignSectorPercent) / 100.0;

				// FE-1: unexplored ground wins ties (spread), and the crawl prefers fields no MCV is already heading to.
				if (Info.FieldCoverage)
				{
					score *= SpreadFactor(allBuildingCells.Count > 0 ? allBuildingCells.Min(c => (c - center).Length) : distance, diagonalCells, Info.SpreadBonus);
					if (inflightMcvSites.Count > 0 && TakenByMcvSite(center, inflightMcvSites.Values, Info.ClaimRadiusCells))
						score *= Info.MinSeparationFactor;
				}

				scores.Add(new FieldScore(i, center, value, hops, payback, threat, score, Safety(threat, guardValue)));
			}

			scores.Sort((a, b) => b.Score.CompareTo(a.Score));
			LastScores = scores;
			var previous = Target?.Index;
			Target = scores.Count > 0 ? scores[0] : null;
			if (Target == null)
				Idle($"no free field ({fields} map indices, {initialCells.Count} with resources, {owned} already ours)");
			else
				lastIdleReason = null;

			// EX-2/EX-2c: want a refinery at the best free field already in reach — any in-reach field counts,
			// not only the crawl target, so an outpost yard claims its local field right away (EX-2c). Park a
			// field that keeps being missed.
			// FE-1 (§12.24): with the switch on, one refinery per anchor replaces this field-based claim.
			if (Info.FieldCoverage && Info.DriveRefineries)
				UpdateAnchorClaim(refineryCells, buildingCells);

			var lawClaims = LawActive;
			claimField = lawClaims ? null : BestClaimField(scores);
			if (!lawClaims)
				wantsRefinery = claimField.HasValue;

			if (lawClaims)
			{
				// The anchor claim (UpdateAnchorClaim) carries its own loop guard; TrackClaim is the field claim's.
			}
			else if (wantsRefinery && claimField is FieldScore want)
			{
				claimAttempts.TryGetValue(want.Index, out var attempts);
				var (state, now, park) = TrackClaim(wanting, want.Index, refineryCells.Count, attempts, Info.MaxClaimAttempts);
				wanting = state;
				claimAttempts[want.Index] = now;
				if (park)
				{
					parkedUntil[want.Index] = world.WorldTick + Info.ParkTicks;
					claimAttempts.Remove(want.Index);
					claimField = null;
					wantsRefinery = false;
					var parked = $"AI ({player.ClientIndex}): EX-2 parked field {want.Index} at {want.Center} for {Info.ParkTicks} ticks: {now} refinery(ies) built without claiming it, at tick {world.WorldTick}";
					Log.Write("debug", parked);
					AIUtils.BotDebug(parked);
				}
			}
			else
				wanting = (-1, refineryCells.Count);

			// Telemetry (EX-0): a debug.log line whenever the target field changes, so a batch shows where each bot
			// wanted to expand and why. BotDebug alone only reaches the in-game chat.
			if (Target is FieldScore t && t.Index != previous)
			{
				var line = string.Format("AI ({0}): EX-0 target field {1} at {2}: value {3}, hops {4}, payback {5} ticks, threat {6}, score {7:F4} ({8} fields) at tick {9}",
					player.ClientIndex, t.Index, t.Center, t.Value, t.Hops, t.PaybackTicks, t.Threat, t.Score, scores.Count, world.WorldTick);
				Log.Write("debug", line);
				AIUtils.BotDebug(line);
			}

			// Greedy expansion: ask for the next construction MCV right away; the engine module would wait for its
			// high cash trigger first. LastScores is this tick's fresh list, so a freed field is seen immediately.
			if (Info.DriveMcvRequests)
				RequestMcv(bot);
		}

		/// <summary>
		/// FE-1: rebuild the anchors (spreaders are public map data, like the spawn points; field centres are the first-seen
		/// ones) and pick the unserved anchor in reach the next refinery claims. A claim that keeps failing is parked.
		/// </summary>
		void UpdateAnchorClaim(List<CPos> refineryCells, List<CPos> buildingCells)
		{
			// Fog honesty: spreaders are neutral map actors placed by the map author - public map data like the spawn points
			// (DESIGN 19.1b), never an enemy's state. Manifested in tools/audit/fog_honesty_manifest.json.
			var spreaders = new List<CPos>();
			foreach (var tp in world.ActorsWithTrait<ISeedableResource>())
			{
				if (tp.Actor.IsDead || !tp.Actor.IsInWorld || (tp.Trait is IDisabledTrait d && d.IsTraitDisabled))
					continue;

				spreaders.Add(tp.Actor.Location);
			}

			var centers = new List<CPos>();
			foreach (var kv in initialCenters)
				if (initialCells.TryGetValue(kv.Key, out var cells) && cells > 0)
					centers.Add(kv.Value);

			anchors = BuildAnchors(spreaders, centers, Info.SpreaderFieldRadiusCells);
			anchorClaim = null;
			anchorClaimFieldCenter = null;
			wantsRefinery = false;
			unservedInReach = 0;
			if (anchors.Count == 0)
				return;

			var tick = world.WorldTick;
			var queued = 0;
			var builder = baseBuilders.FirstOrDefault(t => t.IsTraitEnabled());
			if (builder?.BuildingsBeingProduced != null)
				foreach (var r in builder.Info.RefineryTypes)
					if (builder.BuildingsBeingProduced.TryGetValue(r, out var n))
						queued += n;

			var serve = Info.AnchorServeRadiusCells > 0 ? Info.AnchorServeRadiusCells : Info.ClaimRadiusCells;
			var best = WantedAnchor(anchors, refineryCells, buildingCells, serve, Info.ReachCells,
				i => anchorParkedUntil.TryGetValue(anchors[i], out var until) && tick < until, queued, out unservedInReach);
			if (best < 0)
			{
				anchorStuck = (null, 0, refineryCells.Count);
				return;
			}

			var anchor = anchors[best];

			// Loop guard: the same anchor wanted replan after replan with no refinery gained and none in production.
			var replans = anchorStuck.Anchor == anchor && refineryCells.Count <= anchorStuck.Refineries && queued == 0 ? anchorStuck.Replans + 1 : 0;
			anchorStuck = (anchor, replans, refineryCells.Count);
			if (Info.AnchorStuckReplans > 0 && replans >= Info.AnchorStuckReplans)
			{
				anchorParkedUntil[anchor] = tick + Info.ParkTicks;
				anchorStuck = (null, 0, refineryCells.Count);
				var parked = $"AI ({player.ClientIndex}): FE-1 parked anchor {anchor} for {Info.ParkTicks} ticks: wanted {replans} re-plans with no refinery placed, at tick {tick}";
				Log.Write("debug", parked);
				AIUtils.BotDebug(parked);
				return;
			}

			anchorClaim = anchor;
			wantsRefinery = true;

			// Tie-break of the placement: the resource centre of the field nearest the anchor.
			var nearest = int.MaxValue;
			foreach (var c in centers)
			{
				var d = (c - anchor).LengthSquared;
				if (d < nearest)
				{
					nearest = d;
					anchorClaimFieldCenter = c;
				}
			}
		}

		void Idle(string reason)
		{
			if (reason == lastIdleReason)
				return;

			lastIdleReason = reason;
			var line = $"AI ({player.ClientIndex}): EX-0 no target at tick {world.WorldTick}: {reason}";
			Log.Write("debug", line);
			AIUtils.BotDebug(line);
		}

		((ActorInfo Info, int Cost, int BuildTicks) Refinery, (ActorInfo Info, int Cost, int BuildTicks) Link, int Queues) CheapestBuildables()
		{
			(ActorInfo Info, int Cost, int BuildTicks) refinery = default, link = default;
			var queues = 0;
			// Resolved per re-plan: the base builder's condition may switch on after ours.
			var types = Info.BuildingQueues.Count > 0 ? Info.BuildingQueues
				: baseBuilders.FirstOrDefault(t => t.IsTraitEnabled())?.Info.BuildingQueues ?? (IEnumerable<string>)new[] { "Building" };
			foreach (var queue in types.SelectMany(type => CAAIUtils.FindQueues(player, type)).Distinct())
			{
				queues++;
				foreach (var item in queue.BuildableItems())
				{
					var bi = item.TraitInfoOrDefault<BuildableInfo>();
					if (bi == null || !item.HasTraitInfo<BuildingInfo>())
						continue;

					var cost = item.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
					var entry = (item, cost, queue.GetBuildTime(item, bi));
					// The Refinery trait, from rules: the by-name lists were emptied by the role rollout (§2.8).
					if (item.HasTraitInfo<RefineryInfo>())
					{
						if (refinery.Info == null || cost < refinery.Cost)
							refinery = entry;
					}
					else if (cost > 0 && (link.Info == null || cost < link.Cost))
						link = entry;
				}
			}

			return (refinery, link, queues);
		}
	}
}
