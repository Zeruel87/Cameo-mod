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
using OpenRA.Mods.Common;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Single Fransbot owner for static defensive structures, defensive walls and the Defense production queue items it starts.")]
	public class FransDefenseCommanderBotModuleInfo : ConditionalTraitInfo
	{
		[ActorReference]
		public readonly FrozenSet<string> ConstructionYardTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("All armed static defense actors this commander may produce and place.")]
		public readonly FrozenSet<string> DefenseTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Ground-oriented armed defenses preferred for a General DEFEND incident caused by a ground threat.")]
		public readonly FrozenSet<string> GroundDefenseTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Anti-air defenses preferred for a General DEFEND incident caused by an aircraft threat.")]
		public readonly FrozenSet<string> AntiAirDefenseTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Buildable RA wall actors owned exclusively by DefenseCommander.")]
		public readonly FrozenSet<string> WallTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Visible enemy actor types treated as air threats when selecting a DEFEND response.")]
		public readonly FrozenSet<string> AirThreatTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Friendly structures that walls must not crowd. This protects factories, refineries, naval access and other traffic-sensitive buildings.")]
		public readonly FrozenSet<string> WallKeepClearBuildingTypes =
			FrozenSet<string>.Empty;

		[Desc("RA production queue categories exclusively used by this commander for static defense/wall items. Covers US/UK spellings and per-faction defense queues (e.g. RADefence) so the list survives mods that split queues per faction.")]
		public readonly FrozenSet<string> DefenseQueueCategories = new HashSet<string> { "Defense", "Defence", "RADefence" }.ToFrozenSet();

		[Desc("World ticks between commander ownership/intent scans.")]
		public readonly int ScanInterval = 25;


		[Desc("Short safety cadence for General DEFEND / direct-emergency construction. It bypasses routine scarcity/cooldown but never becomes per-tick order spam.")]
		public readonly int PriorityDefenseCooldownTicks = 100;

		[Desc("World ticks after the latest direct attack on an owned building during which that local front may keep requesting new static defense even if General has no published DEFEND representative. Repeated attack callbacks refresh the window; once it expires no new static defense is requested for that front.")]
		public readonly int DirectAttackFrontHoldTicks = 300;

		[Desc("Maximum number of armed defenses around each selected permanent FACT.")]
		public readonly int DefenseLimitPerAnchor = 12;

		[Desc("Routine peacetime armed-defense floor around each selected permanent FACT once the scripted opening is complete. HardBot raids arrive before the first General DEFEND incident matures; this floor guarantees a minimum standing screen without waiting for a raid.")]
		public readonly int PeacetimeDefensePerAnchorTarget = 3;

		[Desc("World tick after which the peacetime defense floor may start even before the scripted opening completes. Early raids can land before OpeningComplete on fast-paced maps; int.MaxValue disables the early start (upstream behavior).")]
		public readonly int PeacetimeDefenseEarliestTick = int.MaxValue;

		[Desc("Maximum distance in cells from a General SECURE point to its physically established FACT for SECURE foothold defense placement.")]
		public readonly int SecureDefenseAnchorMaximumDistance = 18;

		[Desc("Number of physical armed static defenses required around a SECURE FACT before the foothold may complete. starts SECURE defenses only after a real autonomous-expansion FACT exists.")]
		public readonly int SecureFootholdRequiredDefenseCount = 2;

		[Desc("Maximum time a completed owned Defense-queue item may wait for a legal placement before it is cancelled.")]
		public readonly int PlacementTimeoutTicks = 500;

		[Desc("World ticks between expensive static-defense placement searches while an owned item is complete.")]
		public readonly int PlacementSearchIntervalTicks = 100;

		[Desc("Minimum placement radius around the selected FACT.")]
		public readonly int PlacementMinRadius = 4;

		[Desc("Maximum placement radius around the selected FACT.")]
		public readonly int PlacementMaxRadius = 14;

		[Desc("Preferred empty-cell gap around armed defenses. If impossible, the most open legal site is used.")]
		public readonly int MinimumDefenseSpacingCells = 2;

		[Desc("Percent weight toward the fair StrategicMap forward anchor when placing routine defenses.")]
		public readonly int ForwardPlacementWeightPercent = 100;

		[Desc("Unified RiskModel tolerance for armed static-defense placement.")]
		public readonly FransRiskTolerance DefensePlacementRiskTolerance = FransRiskTolerance.Aggressive;

		[Desc("Allow General ground DEFEND incidents to request a short wall barrier after the first armed response has been started.")]
		public readonly bool EnableWallBarriers = true;

		[Desc("Maximum wall segments planned for one General ground DEFEND incident.")]
		public readonly int WallSegmentsPerIncident = 4;

		[Desc("How long legitimate last-seen General DEFEND direction may keep its short wall plan after the active mission disappears.")]
		public readonly int WallPlanHoldTicks = 1000;

		[Desc("Minimum world ticks between wall geometry planning attempts.")]
		public readonly int WallPlanningIntervalTicks = 100;

		[Desc("Preferred barrier distance from the defending FACT toward the General DEFEND incident.")]
		public readonly int WallBarrierRadius = 8;

		[Desc("Half-width of the candidate wall line. Combined with WallGapHalfWidth it creates a short barrier with a deliberate central opening.")]
		public readonly int WallHalfSpan = 3;

		[Desc("Offsets with absolute value <= this are left open so friendly units retain a passage through the wall line.")]
		public readonly int WallGapHalfWidth = 1;

		[Desc("Small local correction radius if the exact planned wall cell is illegal. The line is never expanded into an unbounded placement search.")]
		public readonly int WallSearchJitterRadius = 1;

		[Desc("Walls are rejected within this radius of traffic-sensitive owned buildings.")]
		public readonly int WallKeepClearRadius = 3;

		[Desc("Unified RiskModel tolerance for wall placement.")]
		public readonly FransRiskTolerance WallPlacementRiskTolerance = FransRiskTolerance.Aggressive;

		[Desc("If General changes the visible representative inside this radius, keep the same defense/wall incident instead of resetting construction intent.")]
		public readonly int GeneralIncidentRetargetRadius = 8;

		[Desc("Maximum distance from a retained DEFEND/emergency front to a permanent FACT that may receive the completed static defense. Prevents a vanished forward site from silently redirecting the item to an unrelated rear base.")]
		public readonly int DefendSiteAnchorMaximumDistance = 18;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (DefenseQueueCategories.Count == 0)
				throw new YamlException("FransDefenseCommander requires at least one defense type and one Defense queue category.");
			if (ScanInterval <= 0 || PriorityDefenseCooldownTicks < 0 || DirectAttackFrontHoldTicks < 0 ||
				PlacementTimeoutTicks <= 0 || PlacementSearchIntervalTicks <= 0 || DefenseLimitPerAnchor < 0 || SecureDefenseAnchorMaximumDistance <= 0 ||
				SecureFootholdRequiredDefenseCount <= 0 || SecureFootholdRequiredDefenseCount > DefenseLimitPerAnchor)
				throw new YamlException("FransDefenseCommander timing/limit values are invalid.");
			if (PlacementMinRadius < 0 || PlacementMaxRadius < PlacementMinRadius || MinimumDefenseSpacingCells < 0)
				throw new YamlException("FransDefenseCommander placement radii/spacing are invalid.");
			if (ForwardPlacementWeightPercent < 0 || ForwardPlacementWeightPercent > 100)
				throw new YamlException($"{nameof(ForwardPlacementWeightPercent)} must be between 0 and 100.");
			if (WallSegmentsPerIncident < 0 || WallPlanHoldTicks < 0 || WallPlanningIntervalTicks <= 0 || WallBarrierRadius < 0 ||
				WallHalfSpan < 0 || WallGapHalfWidth < 0 || WallGapHalfWidth > WallHalfSpan || WallSearchJitterRadius < 0 || WallKeepClearRadius < 0 ||
				GeneralIncidentRetargetRadius < 0 || DefendSiteAnchorMaximumDistance <= 0)
				throw new YamlException("FransDefenseCommander wall/incident values are invalid.");
		}

		public override object Create(ActorInitializer init) => new FransDefenseCommanderBotModule(init.Self, this);
	}

	public class FransDefenseCommanderBotModule : ConditionalTrait<FransDefenseCommanderBotModuleInfo>, IBotTick, IBotRespondToAttack
	{
		readonly World world;
		readonly Player player;
		readonly Actor playerActor;

		IFransExpansionStateService expansionStateService;
		IFransRiskModelService riskModelService;
		IFransBaseBuilderService baseBuilderService;
		IFransGeneralService generalService;
		IFransCommanderCoreService groundCommanderService;
		PowerManager playerPower;

		int scanTicks;
		int lastDefenseEmergencyTick = int.MinValue;
		CPos? emergencyCenter;
		string emergencyThreatType;
		int lastDefenseQueuedTick = int.MinValue;
		int nextGateLogTick;

		uint generalIncidentActorId;
		uint generalIncidentMissionId;
		CPos? generalIncidentCenter;
		string generalIncidentThreatType;
		bool generalIncidentIsAir;
		bool generalIncidentArmedStarted;
		int wallPlanUntilTick;
		int wallPlanNextIndex;
		int nextWallPlanningTick;

		string pendingDefenseType;
		uint pendingQueueActorId;
		int pendingStartedTick;
		bool pendingSeenInQueue;
		bool pendingCancelIssued;
		int pendingPlacementIssuedTick = -1;
		int pendingNextPlacementSearchTick;
		bool pendingIsWall;
		bool pendingIsStrategicStructure;
		CPos? pendingWallCell;
		uint pendingSecureTargetId;
		CPos? pendingFrontCenter;
		CPos? pendingOriginCenter;
		uint pendingIncidentMissionId;
		string lastSiteStartSuppressionSignature;

		public FransDefenseCommanderBotModule(Actor self, FransDefenseCommanderBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			playerActor = self;
		}

		protected override void Created(Actor self)
		{
			expansionStateService = playerActor.TraitsImplementing<IFransExpansionStateService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransDefenseCommander requires FransMcvExpansionManagerBotModule.");
			riskModelService = playerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransDefenseCommander requires FransRiskModelBotModule.");
			baseBuilderService = playerActor.TraitsImplementing<IFransBaseBuilderService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransDefenseCommander requires FransBaseBuilderBotModule.");
			generalService = playerActor.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransDefenseCommander requires FransGeneralBotModule.");
			groundCommanderService = playerActor.TraitsImplementing<IFransCommanderCoreService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransDefenseCommander requires FransGroundCommanderBotModule.");
			playerPower = playerActor.TraitOrDefault<PowerManager>();
		}

		protected override void TraitEnabled(Actor self)
		{
			// deterministic per-module/player startup phase; cadence remains unchanged.
			scanTicks = (int)((self.ActorID + 14u) % (uint)Info.ScanInterval) + 1;
			lastDefenseEmergencyTick = int.MinValue;
			emergencyCenter = null;
			emergencyThreatType = null;
			if (pendingDefenseType == null)
				lastDefenseQueuedTick = int.MinValue;
			nextGateLogTick = 0;
			ClearGeneralIncident();
			if (pendingDefenseType == null)
				ClearPendingDefense();
			FransBotLog.BotDebug(world,
				"{0}: FransDefenseCommander GROUND EGRESS-AWARE PLACEMENT active: multi-foothold/committed-MSLO and active-front defense remain unchanged, but armed defenses, strategic Defense-queue structures and walls may not occupy Ground Commander's live large-army staging/egress reservation.",
				player);
		}

		protected override void TraitDisabled(Actor self)
		{
			ClearGeneralIncident();
			// No IBot/order context exists at this callback. Retain exact pending ownership
			// so a later re-enable resumes it instead of orphaning native queue work.
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (self == null || !self.Info.HasTraitInfo<BuildingInfo>() ||
				e.Attacker == null || e.Attacker.Disposed ||
				e.Attacker.Owner.RelationshipWith(self.Owner) != PlayerRelationship.Enemy ||
				!e.Attacker.Info.HasTraitInfo<ITargetableInfo>())
				return;

			// An attack on our building is legitimate information, but a hidden attacker must
			// not leak its live type or position. Fall back to the victim's own cell and a
			// generic threat so the defense response stays fog-honest (same convention as
			// FransMinelayerBotModule.RespondToAttack).
			var attackerVisible = e.Attacker.CanBeViewedByPlayer(player);
			lastDefenseEmergencyTick = world.WorldTick;
			emergencyThreatType = attackerVisible ? e.Attacker.Info.Name : null;
			emergencyCenter = attackerVisible && e.Attacker.IsInWorld && !e.Attacker.IsDead && e.Attacker.OccupiesSpace != null
				? e.Attacker.Location
				: self.Location;
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransDefenseCommander.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;

			var hasGeneralDefend = TryGetHighestGeneralDefend(out var generalMission);
			if (hasGeneralDefend)
				RefreshGeneralIncident(generalMission);
			else if (pendingDefenseType == null)
				ClearExpiredGeneralIncident();

			var emergency = lastDefenseEmergencyTick != int.MinValue &&
				world.WorldTick - lastDefenseEmergencyTick <= Info.DirectAttackFrontHoldTicks;

			// HARD OPENING LOCK: static defense, SECURE fortification, walls and strategic
			// Defense-queue spending are forbidden until the first PIONEER MCV physically
			// exists. The sole exception is a real attack callback against an owned building.
			// Merely seeing an enemy or receiving a General DEFEND mission is not enough.
			// Exact native work already owned below is managed to a real terminal; it is not a new start.
			if (baseBuilderService.OpeningLocked && !emergency && pendingDefenseType == null)
			{
				ClearGeneralIncident();
				return;
			}

			var conyards = OwnedBuildings(Info.ConstructionYardTypes).OrderBy(a => a.ActorID).ToArray();
			var defenses = OwnedBuildings(Info.DefenseTypes).ToArray();
			var secureMaxSq = Info.SecureDefenseAnchorMaximumDistance * Info.SecureDefenseAnchorMaximumDistance;

			// General may hold several pending footholds. Work on the oldest pending
			// point that already has a physical FACT; a no-FACT pending point must never block
			// fortification of another military win that autonomous MCV expansion has reached.
			var hasSecurePoint = false;
			var secureTargetId = 0u;
			var secureCenter = default(CPos);
			Actor securePhysicalAnchor = null;
			foreach (var foothold in generalService.PendingSecureFootholds)
			{
				if (!generalService.IsSecureFootholdDevelopmentReady(foothold.TargetActorId))
					continue;
				var candidateAnchor = conyards
					.Where(a => (a.Location - foothold.Cell).LengthSquared <= secureMaxSq)
					.OrderBy(a => (a.Location - foothold.Cell).LengthSquared).ThenBy(a => a.ActorID)
					.FirstOrDefault();
				if (candidateAnchor == null)
					continue;
				hasSecurePoint = true;
				secureTargetId = foothold.TargetActorId;
				secureCenter = foothold.Cell;
				securePhysicalAnchor = candidateAnchor;
				break;
			}

			var useSecurePriority = securePhysicalAnchor != null && !hasGeneralDefend && !emergency;
			var priorityCenter = hasGeneralDefend ? generalIncidentCenter : emergency ? emergencyCenter : useSecurePriority ? secureCenter : null;
			Actor frontAnchor = null;
			if ((hasGeneralDefend || emergency) && priorityCenter.HasValue)
				TrySelectRelevantFrontAnchor(conyards, priorityCenter.Value, out frontAnchor);
			var anchor = hasGeneralDefend || emergency
				? frontAnchor
				: SelectDefenseAnchor(conyards, defenses, priorityCenter, useSecurePriority);

			if (pendingDefenseType != null)
			{
				var pendingPurposeValid = true;
				if (pendingIncidentMissionId != 0)
				{
					if (generalService.TryGetDefendIncident(pendingIncidentMissionId, out var currentIncident))
					{
						if (!pendingFrontCenter.HasValue || pendingFrontCenter.Value != currentIncident.LastVisibleTargetCell)
						{
							FransBotLog.BotDebug(world,
								"{0}: [DEFENSE SITE] structure={1} incident={2} origin={3} currentThreat={4} action=Reevaluate.",
								player, pendingDefenseType, pendingIncidentMissionId, pendingOriginCenter, currentIncident.LastVisibleTargetCell);
							pendingFrontCenter = currentIncident.LastVisibleTargetCell;
						}
					}
					else
						pendingPurposeValid = false;
				}
				else if (pendingFrontCenter.HasValue)
				{
					// Emergency freshness gates new work only. Once the exact queue item has
					// started, keep owning it at that front while its relevant FACT survives.
					if (!emergency && hasGeneralDefend &&
						(pendingFrontCenter.Value - generalMission.LastVisibleTargetCell).LengthSquared <=
						Info.GeneralIncidentRetargetRadius * Info.GeneralIncidentRetargetRadius)
					{
						pendingIncidentMissionId = generalMission.MissionId;
						pendingFrontCenter = generalMission.LastVisibleTargetCell;
						pendingPurposeValid = true;
						FransBotLog.BotDebug(world,
							"{0}: [DEFENSE SITE] structure={1} incident={2} origin={3} currentThreat={4} action=Reevaluate reason=direct front joined authoritative General incident.",
							player, pendingDefenseType, pendingIncidentMissionId, pendingOriginCenter, pendingFrontCenter);
					}
				}

				// A pending SECURE item stays bound to its exact foothold even when another pending
				// point becomes the current fortification candidate.
				Actor pendingSecureAnchor = null;
				CPos? pendingSecureCenter = null;
				if (pendingSecureTargetId != 0 &&
					generalService.TryGetSecureDefensePoint(pendingSecureTargetId, out var exactSecureCenter, out _))
				{
					pendingSecureCenter = exactSecureCenter;
					pendingSecureAnchor = conyards
						.Where(a => (a.Location - exactSecureCenter).LengthSquared <= secureMaxSq)
						.OrderBy(a => (a.Location - exactSecureCenter).LengthSquared).ThenBy(a => a.ActorID)
						.FirstOrDefault();
				}

				Actor pendingFrontAnchor = null;
				if (pendingFrontCenter.HasValue)
					TrySelectRelevantFrontAnchor(conyards, pendingFrontCenter.Value, out pendingFrontAnchor);
				var pendingAnchor = pendingSecureTargetId != 0 ? pendingSecureAnchor :
					pendingIsStrategicStructure ? SelectStrategicAnchor(conyards) :
					pendingFrontCenter.HasValue ? pendingFrontAnchor : anchor;
				if (pendingFrontCenter.HasValue && pendingAnchor == null)
					pendingPurposeValid = false;
				var pendingPriorityCenter = pendingSecureTargetId != 0 ? pendingSecureCenter :
					pendingIsStrategicStructure ? null : pendingFrontCenter ?? priorityCenter;
				ManagePendingDefense(bot, pendingAnchor, pendingPriorityCenter, hasGeneralDefend || emergency, pendingPurposeValid);
				return;
			}

			// DefenseCommander, not McvExpansion, owns the final physical SECURE
			// handoff. General contributes only the military territory point. A normal
			// autonomous expansion FACT must already exist before any foothold construction begins.
			if (hasSecurePoint && securePhysicalAnchor != null)
			{
				var secureDefenseCount = CountStructuresNear(defenses, securePhysicalAnchor.Location, Info.PlacementMaxRadius);
				if (secureDefenseCount >= Info.SecureFootholdRequiredDefenseCount &&
					baseBuilderService.TryGetSecureFootholdProduction(securePhysicalAnchor.Location, out var secureProduction))
				{
					var footholdReason = $"autonomous FACT + {Info.SecureFootholdRequiredDefenseCount} armed defenses + local {secureProduction.Info.Name} physically established";
					var completedNow = generalService.CompleteSecureFoothold(secureTargetId, securePhysicalAnchor.Location, footholdReason);
					if (completedNow)
						FransBotLog.BotDebug(world,
							"{0}: DefenseCommander completes SECURE foothold {1} at physical FACT {2}: {3}. Completion is edge-triggered and will not repeat while General holds the established anchor.",
							player, secureTargetId, securePhysicalAnchor, footholdReason);
					// Preserve the completed-foothold hold behavior even after General has
					// consumed the one-shot transition. Only the diagnostic is edge-triggered.
					return;
				}
			}

			if (anchor == null || Info.DefenseLimitPerAnchor == 0)
			{
				if ((hasGeneralDefend || emergency) && Info.DefenseLimitPerAnchor > 0)
					LogDefenseSiteSuppressStart(hasGeneralDefend ? generalIncidentMissionId : 0, priorityCenter, "NoRelevantAnchor");
				return;
			}

			// A strategic General DEFEND mission owns active-front static-defense spending.
			// First start an armed response toward the observed pressure. If it is a ground
			// incident, then spend subsequent free Defense-queue opportunities on the bounded
			// wall plan before another armed response.
			if (hasGeneralDefend)
			{
				if (!generalIncidentArmedStarted && CanStartDefense(out _) &&
					CountStructuresNear(defenses, anchor.Location, Info.PlacementMaxRadius) < Info.DefenseLimitPerAnchor &&
					TryStartDefense(bot, defenses, anchor, generalIncidentThreatType, frontCenter: generalIncidentCenter, incidentMissionId: generalIncidentMissionId))
				{
					generalIncidentArmedStarted = true;
					return;
				}

				if (!generalIncidentIsAir && WallPlanActive && TryStartWall(bot, anchor, generalIncidentCenter.Value))
					return;

				if (CanStartDefense(out _) &&
					CountStructuresNear(defenses, anchor.Location, Info.PlacementMaxRadius) < Info.DefenseLimitPerAnchor)
					TryStartDefense(bot, defenses, anchor, generalIncidentThreatType, frontCenter: generalIncidentCenter, incidentMissionId: generalIncidentMissionId);
				return;
			}


			if (hasSecurePoint && !emergency)
			{
				var secureAnchor = securePhysicalAnchor;
				var secureDefenseCount = secureAnchor == null ? 0 : CountStructuresNear(defenses, secureAnchor.Location, Info.PlacementMaxRadius);
				if (secureAnchor != null && secureDefenseCount < Info.SecureFootholdRequiredDefenseCount &&
					CanStartDefense(out _) &&
					secureDefenseCount < Info.DefenseLimitPerAnchor &&
					TryStartDefense(bot, defenses, secureAnchor, "secure-ground", secureTargetId))
				{
					FransBotLog.BotDebug(world,
						"{0}: DefenseCommander starts SECURE defense {1}/{2} for target {3} at {4} from physical FACT {5}; SECURE foothold waits for two physical armed defenses.",
						player, secureDefenseCount + 1, Info.SecureFootholdRequiredDefenseCount, secureTargetId, secureCenter, secureAnchor);
					return;
				}
			}

			// BaseBuilder owns the strategic decision to progress from physical ATEK/STEK to MSLO,
			// but MSLO itself belongs to the RA Defense queue. Keep one physical queue owner here:
			// urgent DEFEND/emergency and the two mandatory SECURE defenses outrank this request;
			// otherwise MSLO remains the only peacetime Defense-queue growth request.
			if (!emergency && CanStartDefense(out _) && TryStartStrategicDefenseQueueRequest(bot, conyards))
				return;

			if (!emergency)
			{
				// Routine peacetime floor: grow toward a small standing screen at the least-defended
				// permanent FACT so the first HardBot raid does not meet an empty perimeter. Uses the
				// same anchor/limit/cooldown path as incident defense; a direct building attack that has
				// not produced a General DEFEND representative may still drive this local front while
				// fresh attack callbacks keep the hold window alive, so the floor only runs when no
				// emergency window is active.
				if ((!baseBuilderService.OpeningComplete && world.WorldTick < Info.PeacetimeDefenseEarliestTick) ||
					anchor == null || Info.PeacetimeDefensePerAnchorTarget <= 0 ||
					!CanStartDefense(out _) ||
					CountStructuresNear(defenses, anchor.Location, Info.PlacementMaxRadius) >= Math.Min(Info.PeacetimeDefensePerAnchorTarget, Info.DefenseLimitPerAnchor))
					return;

				TryStartDefense(bot, defenses, anchor, "peacetime-floor");
				return;
			}

			if (!CanStartDefense(out var reason))
			{
				LogGate(reason);
				return;
			}

			if (CountStructuresNear(defenses, anchor.Location, Info.PlacementMaxRadius) >= Info.DefenseLimitPerAnchor)
				return;

			TryStartDefense(bot, defenses, anchor, emergencyThreatType, frontCenter: emergencyCenter);
		}

		bool TryGetHighestGeneralDefend(out FransMission mission)
		{
			generalService.EnsureCurrentMissions();
			foreach (var candidate in generalService.CurrentMissions)
				if (candidate.Type == FransMissionType.Defend)
				{
					mission = candidate;
					return true;
				}

			mission = default;
			return false;
		}

		void RefreshGeneralIncident(FransMission mission)
		{
			var newIncident = generalIncidentMissionId == 0 || generalIncidentMissionId != mission.MissionId;

			if (newIncident)
			{
				generalIncidentArmedStarted = false;
				wallPlanNextIndex = 0;
				nextWallPlanningTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: DefenseCommander accepts General DEFEND priority {1} at {2} against {3} {4}; armed defense will take the next free owned Defense-queue opportunity and ground pressure may seed a short wall barrier.",
					player, mission.StrategicPriority, mission.LastVisibleTargetCell, mission.TargetActorType, mission.TargetActorId);
			}

			generalIncidentActorId = mission.TargetActorId;
			generalIncidentMissionId = mission.MissionId;
			generalIncidentCenter = mission.LastVisibleTargetCell;
			generalIncidentThreatType = mission.TargetActorType;
			generalIncidentIsAir = Info.AirThreatTypes.Contains(mission.TargetActorType);
			if (Info.EnableWallBarriers && !generalIncidentIsAir && Info.WallSegmentsPerIncident > 0)
				wallPlanUntilTick = Math.Max(wallPlanUntilTick, world.WorldTick + Info.WallPlanHoldTicks);
			else if (newIncident)
				wallPlanUntilTick = 0;
		}

		void ClearExpiredGeneralIncident()
		{
			generalIncidentActorId = 0;
			generalIncidentMissionId = 0;
			generalIncidentCenter = null;
			generalIncidentThreatType = null;
			generalIncidentIsAir = false;
			generalIncidentArmedStarted = false;
			wallPlanUntilTick = 0;
			wallPlanNextIndex = 0;
			nextWallPlanningTick = 0;
		}

		void ClearGeneralIncident() => ClearExpiredGeneralIncident();

		int AvailableWallOffsetCount => Math.Max(0, (Info.WallHalfSpan - Info.WallGapHalfWidth) * 2);

		bool WallPlanActive => Info.EnableWallBarriers && Info.WallSegmentsPerIncident > 0 &&
			generalIncidentCenter.HasValue && wallPlanNextIndex < Math.Min(Info.WallSegmentsPerIncident, AvailableWallOffsetCount) &&
			world.WorldTick <= wallPlanUntilTick;

		bool CanStartDefense(out string reason)
		{
			reason = null;
			if (lastDefenseQueuedTick != int.MinValue &&
				world.WorldTick - lastDefenseQueuedTick < Info.PriorityDefenseCooldownTicks)
			{
				reason = $"active-front defense cooldown {world.WorldTick - lastDefenseQueuedTick}/{Info.PriorityDefenseCooldownTicks} WT";
				return false;
			}

			return true;
		}

		void LogGate(string reason)
		{
			if (string.IsNullOrEmpty(reason) || world.WorldTick < nextGateLogTick)
				return;
			nextGateLogTick = world.WorldTick + 500;
			FransBotLog.BotDebug(world,
				"{0}: DefenseCommander holds active-front static defense: {1}.", player, reason);
		}

		Actor SelectDefenseAnchor(Actor[] conyards, Actor[] defenses, CPos? priorityCenter, bool includeAllConyardsForPriority = false)
		{
			if (conyards.Length == 0)
				return null;

			var permanentCount = Math.Min(conyards.Length, Math.Max(1, expansionStateService.DesiredPermanentConstructionYards));
			var candidates = includeAllConyardsForPriority ? conyards.AsEnumerable() : conyards.Take(permanentCount);
			if (priorityCenter.HasValue)
				return candidates.OrderBy(a => (a.Location - priorityCenter.Value).LengthSquared).ThenBy(a => a.ActorID).FirstOrDefault();

			return candidates
				.OrderBy(a => CountStructuresNear(defenses, a.Location, Info.PlacementMaxRadius))
				.ThenBy(a => riskModelService.EvaluateImmediateRisk(a, a.Location, FransRiskRole.BuildingPlacement, Info.DefensePlacementRiskTolerance).Score)
				.ThenBy(a => a.ActorID)
				.FirstOrDefault();
		}

		bool TrySelectRelevantFrontAnchor(Actor[] conyards, CPos frontCenter, out Actor anchor)
		{
			var maximumDistanceSquared = Info.DefendSiteAnchorMaximumDistance * Info.DefendSiteAnchorMaximumDistance;
			anchor = conyards
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.Owner == player &&
					(a.Location - frontCenter).LengthSquared <= maximumDistanceSquared)
				.OrderBy(a => (a.Location - frontCenter).LengthSquared)
				.ThenBy(a => a.ActorID)
				.FirstOrDefault();

			// A front that has lost its local FACT can still be anchored by the owned
			// building it is actually attacking, as long as the fallback anchor is also
			// within DefendSiteAnchorMaximumDistance of the front — the redirect-guard
			// semantics are preserved and the defense lands on the attacked site.
			if (anchor == null)
				anchor = world.ActorsHavingTrait<Building>()
					.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player &&
						(a.Location - frontCenter).LengthSquared <= maximumDistanceSquared)
					.OrderBy(a => (a.Location - frontCenter).LengthSquared)
					.ThenBy(a => a.ActorID)
					.FirstOrDefault();
			return anchor != null;
		}

		void LogDefenseSiteSuppressStart(uint incidentMissionId, CPos? frontCenter, string reason)
		{
			var signature = $"{incidentMissionId}|{frontCenter}|{reason}";
			if (signature == lastSiteStartSuppressionSignature)
				return;
			lastSiteStartSuppressionSignature = signature;
			FransBotLog.BotDebug(world,
				"{0}: [DEFENSE SITE] incident={1} currentThreat={2} action=SuppressStart reason={3}.",
				player, incidentMissionId, frontCenter, reason);
		}

		Actor SelectStrategicAnchor(Actor[] conyards) => conyards
			.OrderBy(a => (a.Location - baseBuilderService.StrategicBaseCenter).LengthSquared)
			.ThenBy(a => a.ActorID)
			.FirstOrDefault();

		bool TryStartStrategicDefenseQueueRequest(IBot bot, Actor[] conyards)
		{
			if (conyards.Length == 0 || !baseBuilderService.TryGetStrategicDefenseQueueRequest(out var actorType) ||
				string.IsNullOrWhiteSpace(actorType) || !HasSufficientPowerFor(actorType))
				return false;

			var queues = DefenseQueues()
				.Where(q => q.Enabled && !q.AllQueued().Any())
				.OrderBy(q => q.Actor.ActorID);
			foreach (var queue in queues)
			{
				if (!queue.BuildableItems().Any(i => i.Name == actorType))
					continue;

				BeginPending(queue, actorType, false, null, isStrategicStructure: true);
				lastDefenseQueuedTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: DefenseCommander accepts BaseBuilder strategic Defense-queue request and starts {1} on queue actor {2} at WT {3}; queue ownership remains single-writer.",
					player, actorType, queue.Actor.ActorID, world.WorldTick);
				bot.QueueOrder(Order.StartProduction(queue.Actor, actorType, 1));
				return true;
			}

			return false;
		}

		bool HasSufficientPowerFor(string actorType)
		{
			if (playerPower == null || !world.Map.Rules.Actors.TryGetValue(actorType, out var actorInfo))
				return true;
			var power = actorInfo.TraitInfos<PowerInfo>().Where(i => i.EnabledByDefault).Sum(i => i.Amount);
			return playerPower.ExcessPower + power >= 0;
		}

		bool TryStartDefense(IBot bot, Actor[] defenses, Actor siteAnchor, string threatType, uint secureTargetId = 0, CPos? frontCenter = null, uint incidentMissionId = 0)
		{
			if (siteAnchor == null || !siteAnchor.IsInWorld || siteAnchor.IsDead || siteAnchor.Owner != player)
			{
				if (frontCenter.HasValue)
					LogDefenseSiteSuppressStart(incidentMissionId, frontCenter, "NoRelevantAnchor");
				return false;
			}

			var queues = DefenseQueues()
				.Where(q => q.Enabled)
				.OrderBy(q => q.Actor.ActorID)
				.ToArray();

			foreach (var queue in queues)
			{
				if (queue.AllQueued().Any())
					continue;

				var all = queue.BuildableItems()
					.Select(i => i.Name)
					.Where(Info.DefenseTypes.Contains)
					.Distinct()
					.ToArray();
				if (all.Length == 0)
					continue;

				var preferredSet = threatType != null && Info.AirThreatTypes.Contains(threatType)
					? Info.AntiAirDefenseTypes
					: threatType != null ? Info.GroundDefenseTypes : Info.DefenseTypes;
				var preferred = all.Where(preferredSet.Contains).ToArray();
				var pool = preferred.Length > 0 ? preferred : all;
				var buildable = pool
					.OrderBy(type => defenses.Count(a => a.Info.Name == type))
					.ThenBy(type => type)
					.FirstOrDefault();
				if (buildable == null)
					continue;
				if (!FindDefenseLocation(siteAnchor, buildable, frontCenter).HasValue)
				{
					if (frontCenter.HasValue)
						LogDefenseSiteSuppressStart(incidentMissionId, frontCenter, "NoLegalPlacementAtRelevantAnchor");
					continue;
				}

				BeginPending(queue, buildable, false, null, secureTargetId, frontCenter: frontCenter,
					incidentMissionId: incidentMissionId, siteAnchor: siteAnchor);
				lastDefenseQueuedTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: DefenseCommander owns free Defense queue actor {1} and starts {2} at WT {3}{4}.",
					player, queue.Actor.ActorID, buildable, world.WorldTick,
					threatType != null ? $" for General/emergency threat {threatType}" : string.Empty);
				bot.QueueOrder(Order.StartProduction(queue.Actor, buildable, 1));
				return true;
			}

			return false;
		}

		bool TryStartWall(IBot bot, Actor anchor, CPos threatCenter)
		{
			if (!WallPlanActive || world.WorldTick < nextWallPlanningTick)
				return false;
			if (lastDefenseQueuedTick != int.MinValue &&
				world.WorldTick - lastDefenseQueuedTick < Info.PriorityDefenseCooldownTicks)
				return false;

			nextWallPlanningTick = world.WorldTick + Info.WallPlanningIntervalTicks;
			var queues = DefenseQueues()
				.Where(q => q.Enabled)
				.OrderBy(q => q.Actor.ActorID)
				.ToArray();

			foreach (var queue in queues)
			{
				if (queue.AllQueued().Any())
					continue;

				var wallType = queue.BuildableItems()
					.Where(i => Info.WallTypes.Contains(i.Name))
					.OrderByDescending(i => i.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0)
					.ThenBy(i => i.Name)
					.Select(i => i.Name)
					.FirstOrDefault();
				if (wallType == null)
					continue;

				if (!TryFindNextWallLocation(anchor, threatCenter, wallType, wallPlanNextIndex, out var location, out var selectedIndex))
				{
					wallPlanNextIndex = Math.Min(Info.WallSegmentsPerIncident, AvailableWallOffsetCount);
					FransBotLog.BotDebug(world,
						"{0}: DefenseCommander drops the remaining wall plan near {1}: no short legal barrier cell exists without blocking protected base traffic or the active MCV right-of-way.",
						player, threatCenter);
					return false;
				}

				wallPlanNextIndex = selectedIndex + 1;
				BeginPending(queue, wallType, true, location, frontCenter: threatCenter,
					incidentMissionId: generalIncidentMissionId, siteAnchor: anchor);
				lastDefenseQueuedTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: DefenseCommander starts wall {1} for General ground DEFEND at {2}; planned segment {3}/{4} is {5}, with the central passage kept open.",
					player, wallType, threatCenter, wallPlanNextIndex,
					Math.Min(Info.WallSegmentsPerIncident, AvailableWallOffsetCount), location);
				bot.QueueOrder(Order.StartProduction(queue.Actor, wallType, 1));
				return true;
			}

			return false;
		}

		void BeginPending(ProductionQueue queue, string type, bool isWall, CPos? wallCell, uint secureTargetId = 0,
			bool isStrategicStructure = false, CPos? frontCenter = null, uint incidentMissionId = 0, Actor siteAnchor = null)
		{
			pendingDefenseType = type;
			pendingQueueActorId = queue.Actor.ActorID;
			pendingStartedTick = world.WorldTick;
			pendingSeenInQueue = false;
			pendingCancelIssued = false;
			pendingPlacementIssuedTick = -1;
			pendingNextPlacementSearchTick = world.WorldTick;
			pendingIsWall = isWall;
			pendingIsStrategicStructure = isStrategicStructure;
			pendingWallCell = wallCell;
			pendingSecureTargetId = secureTargetId;
			pendingFrontCenter = frontCenter;
			pendingOriginCenter = frontCenter;
			pendingIncidentMissionId = incidentMissionId;
			lastSiteStartSuppressionSignature = null;
			if (frontCenter.HasValue)
				FransBotLog.BotDebug(world,
					"{0}: [DEFENSE SITE] structure={1} incident={2} origin={3} currentThreat={3} anchor={4}/{5} action=StartProduction queue={6}.",
					player, type, incidentMissionId, frontCenter.Value, siteAnchor?.ActorID ?? 0, siteAnchor?.Location, queue.Actor.ActorID);
		}

		void ManagePendingDefense(IBot bot, Actor anchor, CPos? priorityCenter, bool urgentPreemption = false, bool purposeValid = true)
		{
			var queue = DefenseQueues()
				.Where(q => q.Enabled && q.Actor.ActorID == pendingQueueActorId)
				.FirstOrDefault();
			if (queue == null)
			{
				ClearPendingDefense();
				return;
			}

			var pending = queue.AllQueued().FirstOrDefault(item => item.Item == pendingDefenseType);
			if (pending != null)
				pendingSeenInQueue = true;

			if (pending == null)
			{
				if (!pendingSeenInQueue && world.WorldTick - pendingStartedTick < Math.Max(50, Info.ScanInterval * 2))
					return;
				ClearPendingDefense();
				return;
			}

			if (!purposeValid && !pendingCancelIssued)
			{
				FransBotLog.BotDebug(world,
					"{0}: [DEFENSE SITE] structure={1} incident={2} origin={3} currentThreat={4} action=Release reason=no active incident or relevant live FACT remains.",
					player, pendingDefenseType, pendingIncidentMissionId, pendingOriginCenter, pendingFrontCenter);
				CancelPending(bot, queue, "originating defensive purpose no longer has an active incident/front and relevant permanent FACT");
				return;
			}

			// General DEFEND/direct emergency may preempt SECURE foothold preparation, but a strategic
			// MSLO/Defense-queue structure that has already started is committed to completion. Repeated
			// attack fronts must not burn cash in an endless cancel/restart loop; DEFEND takes the queue
			// before MSLO starts or immediately after the committed item resolves.
			if (urgentPreemption && pendingSecureTargetId != 0 && !pendingCancelIssued)
			{
				CancelPending(bot, queue, "General DEFEND/emergency preempts SECURE foothold defense");
				return;
			}

			if (pendingCancelIssued || !pending.Done)
				return;

			if (anchor == null)
			{
				// physical-FACT contract: SECURE never owns a travelling MCV and never
				// holds a completed defense item waiting for one. If the FACT that justified this
				// production disappears, release the exact owned queue item instead of redirecting it.
				CancelPending(bot, queue, pendingSecureTargetId != 0
					? "SECURE physical FACT anchor disappeared before defense placement"
						: "no relevant live FACT anchor exists");
				return;
			}

			if (pendingPlacementIssuedTick >= 0 && world.WorldTick - pendingPlacementIssuedTick < 75)
				return;

			if (world.WorldTick < pendingNextPlacementSearchTick)
				return;
			pendingNextPlacementSearchTick = world.WorldTick + Info.PlacementSearchIntervalTicks;

			var location = pendingIsWall
				? FindPendingWallLocation(anchor, pendingDefenseType, pendingWallCell)
				: pendingIsStrategicStructure
					? FindStrategicStructureLocation(anchor, pendingDefenseType)
					: FindDefenseLocation(anchor, pendingDefenseType, priorityCenter);
			if (location.HasValue)
			{
				pendingPlacementIssuedTick = world.WorldTick;
				if (pendingIsWall)
					FransBotLog.BotDebug(world,
						"{0}: DefenseCommander places owned wall {1} at {2} at WT {3}.",
						player, pendingDefenseType, location.Value, world.WorldTick);
				else if (pendingIsStrategicStructure)
					FransBotLog.BotDebug(world,
						"{0}: DefenseCommander places strategic Defense-queue structure {1} at rear-base cell {2} around FACT {4} at WT {3}.",
						player, pendingDefenseType, location.Value, world.WorldTick, anchor);
				else
					FransBotLog.BotDebug(world,
						"{0}: [DEFENSE SITE] structure={1} incident={2} origin={3} currentThreat={4} anchor={5}/{6} action=PlacementIssued cell={7} WT={8}.",
						player, pendingDefenseType, pendingIncidentMissionId, pendingOriginCenter, pendingFrontCenter,
						anchor.ActorID, anchor.Location, location.Value, world.WorldTick);
				bot.QueueOrder(new Order("PlaceBuilding", playerActor, Target.FromCell(world, location.Value), false)
				{
					TargetString = pendingDefenseType,
					ExtraLocation = CPos.Zero,
					ExtraData = queue.Actor.ActorID,
					SuppressVisualFeedback = true
				});
				return;
			}

			if (world.WorldTick - pendingStartedTick >= Info.PlacementTimeoutTicks)
				CancelPending(bot, queue, $"no legal unified-risk placement for {Info.PlacementTimeoutTicks} WT");
		}

		void CancelPending(IBot bot, ProductionQueue queue, string reason)
		{
			if (pendingCancelIssued)
				return;
			pendingCancelIssued = true;
			FransBotLog.BotDebug(world,
				"{0}: DefenseCommander cancels only its owned {1}: {2}.", player, pendingDefenseType, reason);
			bot.QueueOrder(Order.CancelProduction(queue.Actor, pendingDefenseType, 1));
		}

		void ClearPendingDefense()
		{
			pendingDefenseType = null;
			pendingQueueActorId = 0;
			pendingStartedTick = 0;
			pendingSeenInQueue = false;
			pendingCancelIssued = false;
			pendingPlacementIssuedTick = -1;
			pendingNextPlacementSearchTick = 0;
			pendingIsWall = false;
			pendingIsStrategicStructure = false;
			pendingWallCell = null;
			pendingSecureTargetId = 0;
			pendingFrontCenter = null;
			pendingOriginCenter = null;
			pendingIncidentMissionId = 0;
		}

		bool IntersectsGroundStagingReservation(CPos cell, BuildingInfo buildingInfo) =>
			buildingInfo != null && groundCommanderService != null &&
			groundCommanderService.IntersectsGroundStagingReservation(cell, buildingInfo.Dimensions.X, buildingInfo.Dimensions.Y);

		CPos? FindDefenseLocation(Actor anchor, string defenseType, CPos? priorityCenter)
		{
			if (!world.Map.Rules.Actors.TryGetValue(defenseType, out var actorInfo))
				return null;
			var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return null;

			var target = priorityCenter ?? baseBuilderService.StrategicForwardTarget ?? anchor.Location;
			var weight = priorityCenter.HasValue ? 100 : Info.ForwardPlacementWeightPercent;
			CPos? bestFallback = null;
			var bestClearance = -1;

			foreach (var cell in world.Map.FindTilesInAnnulus(anchor.Location, Info.PlacementMinRadius, Info.PlacementMaxRadius)
				.OrderBy(c => (long)(100 - weight) * (c - anchor.Location).LengthSquared + (long)weight * (c - target).LengthSquared)
				.ThenBy(c => (c - anchor.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y))
			{
				if (IntersectsGroundStagingReservation(cell, buildingInfo) ||
					!world.CanPlaceBuilding(cell, actorInfo, buildingInfo, null) ||
					!buildingInfo.IsCloseEnoughToBase(world, player, actorInfo, null, cell))
					continue;
				if (riskModelService.EvaluateStrategicCell(cell, FransRiskRole.BuildingPlacement, Info.DefensePlacementRiskTolerance).IsCritical)
					continue;

				var clearance = StructureClearance(cell, buildingInfo);
				if (clearance >= Info.MinimumDefenseSpacingCells)
					return cell;
				if (clearance > bestClearance)
				{
					bestClearance = clearance;
					bestFallback = cell;
				}
			}

			if (bestFallback.HasValue)
				FransBotLog.BotDebug(world,
					"{0}: DefenseCommander spacing fallback for {1}: preferred {2} empty cells, best legal clearance {3}; using {4}.",
					player, defenseType, Info.MinimumDefenseSpacingCells, bestClearance, bestFallback.Value);
			return bestFallback;
		}

		CPos? FindStrategicStructureLocation(Actor anchor, string actorType)
		{
			if (anchor == null || !world.Map.Rules.Actors.TryGetValue(actorType, out var actorInfo))
				return null;
			var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return null;

			var forward = baseBuilderService.StrategicForwardTarget;
			CPos? bestFallback = null;
			var bestClearance = -1;
			var cells = world.Map.FindTilesInAnnulus(anchor.Location, Info.PlacementMinRadius, Info.PlacementMaxRadius)
				.Where(world.Map.Contains);
			if (forward.HasValue)
				cells = cells.OrderByDescending(c => (c - forward.Value).LengthSquared)
					.ThenBy(c => (c - anchor.Location).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y);
			else
				cells = cells.OrderBy(c => (c - anchor.Location).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y);

			foreach (var cell in cells)
			{
				if (IntersectsGroundStagingReservation(cell, buildingInfo) ||
					!world.CanPlaceBuilding(cell, actorInfo, buildingInfo, null) ||
					!buildingInfo.IsCloseEnoughToBase(world, player, actorInfo, null, cell))
					continue;
				if (riskModelService.EvaluateStrategicCell(cell, FransRiskRole.BuildingPlacement, FransRiskTolerance.Cautious).IsCritical)
					continue;

				var clearance = StructureClearance(cell, buildingInfo);
				if (clearance >= Info.MinimumDefenseSpacingCells)
					return cell;
				if (clearance > bestClearance)
				{
					bestClearance = clearance;
					bestFallback = cell;
				}
			}

			return bestFallback;
		}

		CPos? FindPendingWallLocation(Actor anchor, string wallType, CPos? preferred)
		{
			if (!world.Map.Rules.Actors.TryGetValue(wallType, out var actorInfo))
				return null;
			var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null || !preferred.HasValue)
				return null;

			foreach (var cell in JitterCells(preferred.Value))
				if (IsLegalWallCell(anchor, cell, actorInfo, buildingInfo))
					return cell;
			return null;
		}

		bool TryFindNextWallLocation(Actor anchor, CPos threatCenter, string wallType, int startIndex, out CPos location, out int selectedIndex)
		{
			location = default;
			selectedIndex = -1;
			if (!world.Map.Rules.Actors.TryGetValue(wallType, out var actorInfo))
				return false;
			var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return false;

			var maxIndex = Math.Min(Info.WallSegmentsPerIncident, AvailableWallOffsetCount);
			var dx = threatCenter.X - anchor.Location.X;
			var dy = threatCenter.Y - anchor.Location.Y;
			var dominantX = Math.Abs(dx) >= Math.Abs(dy);
			var dominantDistance = Math.Max(Math.Abs(dx), Math.Abs(dy));
			var forward = Math.Min(Info.WallBarrierRadius, Math.Max(2, dominantDistance / 2));
			var sign = dominantX ? Math.Sign(dx) : Math.Sign(dy);
			if (sign == 0)
				sign = 1;
			var barrierCenter = dominantX
				? new CPos(anchor.Location.X + sign * forward, anchor.Location.Y)
				: new CPos(anchor.Location.X, anchor.Location.Y + sign * forward);

			for (var i = Math.Max(0, startIndex); i < maxIndex; i++)
			{
				var offset = WallOffsetAt(i);
				var intended = dominantX
					? new CPos(barrierCenter.X, barrierCenter.Y + offset)
					: new CPos(barrierCenter.X + offset, barrierCenter.Y);
				foreach (var cell in JitterCells(intended))
					if (IsLegalWallCell(anchor, cell, actorInfo, buildingInfo))
					{
						location = cell;
						selectedIndex = i;
						return true;
					}
			}

			return false;
		}

		int WallOffsetAt(int index)
		{
			// Deterministic far-to-near pairs around the deliberate center gap:
			// -3,+3,-2,+2 for the default half-span 3 / gap 1. No per-scan array allocation.
			var distance = Info.WallHalfSpan - index / 2;
			return index % 2 == 0 ? -distance : distance;
		}

		CPos[] JitterCells(CPos intended)
		{
			var r = Info.WallSearchJitterRadius;
			return Enumerable.Range(-r, r * 2 + 1)
				.SelectMany(x => Enumerable.Range(-r, r * 2 + 1).Select(y => new CPos(intended.X + x, intended.Y + y)))
				.Where(c => world.Map.Contains(c))
				.OrderBy(c => Math.Abs(c.X - intended.X) + Math.Abs(c.Y - intended.Y))
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.ToArray();
		}

		bool IsLegalWallCell(Actor anchor, CPos cell, ActorInfo actorInfo, BuildingInfo buildingInfo)
		{
			if (IntersectsGroundStagingReservation(cell, buildingInfo) ||
				!world.CanPlaceBuilding(cell, actorInfo, buildingInfo, null) ||
				!buildingInfo.IsCloseEnoughToBase(world, player, actorInfo, null, cell))
				return false;
			if (riskModelService.EvaluateStrategicCell(cell, FransRiskRole.BuildingPlacement, Info.WallPlacementRiskTolerance).IsCritical)
				return false;

			if (expansionStateService.TryGetMcvDeployRightOfWay(out var mcvCenter, out var mcvRadius))
			{
				var keep = mcvRadius + 1;
				if ((cell - mcvCenter).LengthSquared <= keep * keep)
					return false;
			}

			var keepClearSquared = Info.WallKeepClearRadius * Info.WallKeepClearRadius;
			foreach (var building in world.ActorsHavingTrait<Building>())
				if (building.IsInWorld && !building.IsDead && building.Owner == player &&
					Info.WallKeepClearBuildingTypes.Contains(building.Info.Name) &&
					(cell - building.Location).LengthSquared <= keepClearSquared)
					return false;

			return true;
		}

		int StructureClearance(CPos cell, BuildingInfo candidateInfo)
		{
			var candidateMinX = cell.X;
			var candidateMinY = cell.Y;
			var candidateMaxX = cell.X + candidateInfo.Dimensions.X - 1;
			var candidateMaxY = cell.Y + candidateInfo.Dimensions.Y - 1;
			var minimum = int.MaxValue;

			foreach (var existing in world.ActorsHavingTrait<Building>())
			{
				if (!existing.IsInWorld || existing.IsDead || existing.Owner != player)
					continue;
				var info = existing.Info.TraitInfoOrDefault<BuildingInfo>();
				if (info == null)
					continue;
				var exMinX = existing.Location.X;
				var exMinY = existing.Location.Y;
				var exMaxX = exMinX + info.Dimensions.X - 1;
				var exMaxY = exMinY + info.Dimensions.Y - 1;
				var gapX = candidateMaxX < exMinX ? exMinX - candidateMaxX - 1 : exMaxX < candidateMinX ? candidateMinX - exMaxX - 1 : 0;
				var gapY = candidateMaxY < exMinY ? exMinY - candidateMaxY - 1 : exMaxY < candidateMinY ? candidateMinY - exMaxY - 1 : 0;
				minimum = Math.Min(minimum, Math.Max(gapX, gapY));
				if (minimum == 0)
					break;
			}

			return minimum == int.MaxValue ? Info.MinimumDefenseSpacingCells : minimum;
		}

		System.Collections.Generic.IEnumerable<Actor> OwnedBuildings(FrozenSet<string> types) =>
			world.ActorsHavingTrait<Building>().Where(a =>
				a.IsInWorld && !a.IsDead && a.Owner == player && types.Contains(a.Info.Name));

		System.Collections.Generic.IEnumerable<ProductionQueue> DefenseQueues()
		{
			var byCategory = AIUtils.FindQueuesByCategory(player);
			return Info.DefenseQueueCategories.SelectMany(c => byCategory[c]);
		}

		static int CountStructuresNear(Actor[] defenses, CPos center, int radius)
		{
			var radiusSquared = radius * radius;
			return defenses.Count(a => (a.Location - center).LengthSquared <= radiusSquared);
		}
	}
}
