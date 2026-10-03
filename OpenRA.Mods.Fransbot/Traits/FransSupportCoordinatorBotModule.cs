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
using System.Linq;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public enum FransSupportOperationKind
	{
		None,
		NukeSecure,
		Paratroopers,
		IronCurtain,
		Chronoshift
	}

	public interface IFransSupportCoordinatorService
	{
		bool TryGetNukeExclusion(uint secureTargetActorId, out CPos center, out int radius);
		bool IsCellInsideActiveNukeExclusion(CPos cell);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Coordinates mission-aware Fransbot support operations. It never creates a new strategic mission type: support powers reserve/stage/release around General's existing DEFEND/SECURE/RAID missions.")]
	public class FransSupportCoordinatorBotModuleInfo : ConditionalTraitInfo, Requires<FransSupportPowerBotModuleInfo>
	{
		[Desc("World ticks between support-operation coordination passes.")]
		public readonly int ScanInterval = 10;

		[Desc("Support-power order used for mission-coordinated nuclear strikes.")]
		public readonly string NukeOrder = "NukePowerInfoOrder";

		[Desc("Support-power order used for mission-aware paratrooper insertion.")]
		public readonly string ParatrooperOrder = "SovietParatroopers";

		[Desc("Maximum distance in cells from a SECURE mission center where FAIR-INTEL NUKE may choose its strike cell.")]
		public readonly int NukeSecureLinkRadius = 18;

		[Desc("Friendly exclusion radius around a reserved nuclear strike cell. Ground SECURE stages outside this ring until the post-launch hold expires.")]
		public readonly int NukeExclusionRadius = 8;

		[Desc("Maximum world ticks a SECURE may stage waiting for its nuclear exclusion zone to clear before the support reservation is cancelled and normal SECURE resumes.")]
		public readonly int NukeStageTimeoutTicks = 750;

		[Desc("World ticks after issuing the nuclear launch order before the exclusion zone is released. This conservative safety window covers missile flight/detonation without assuming enemy casualties.")]
		public readonly int NukePostLaunchHoldTicks = 200;

		[Desc("Cells around a mission center searched for a non-critical, non-water paratrooper drop cell.")]
		public readonly int ParatrooperMissionSearchRadius = 6;

		[Desc("World ticks after a coordinated nuke release during which Paratroopers preferentially reinforce the same SECURE mission if ready.")]
		public readonly int NukeParatrooperFollowupWindowTicks = 500;

		[Desc("Minimum world ticks before repeating the expensive FAIR-INTEL nuclear target-planning scan after a ready missile found no launchable target. Active reserved NUKE->SECURE clearance checks still run at ScanInterval.")]
		public readonly int NukePlanningBackoffTicks = 125;

		public override object Create(ActorInitializer init) { return new FransSupportCoordinatorBotModule(init.Self, this); }

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (ScanInterval <= 0 || NukeSecureLinkRadius <= 0 || NukeExclusionRadius <= 0 ||
				NukeStageTimeoutTicks <= 0 || NukePostLaunchHoldTicks <= 0 || ParatrooperMissionSearchRadius < 0 ||
				NukeParatrooperFollowupWindowTicks < 0 || NukePlanningBackoffTicks <= 0 ||
				string.IsNullOrWhiteSpace(NukeOrder) || string.IsNullOrWhiteSpace(ParatrooperOrder))
				throw new YamlException("FransSupportCoordinator settings must use positive intervals/radii and non-empty support-power order names.");
		}
	}

	public class FransSupportCoordinatorBotModule : ConditionalTrait<FransSupportCoordinatorBotModuleInfo>,
		IBotTick, IFransSupportCoordinatorService
	{
		readonly World world;
		readonly Player player;
		IFransSupportPowerService supportPowerService;
		IFransGeneralService generalService;
		IFransCommandBidService commandBidService;
		IFransRiskModelService riskModelService;

		int scanTicks;
		int nextNukeRiskRefreshTick;
		int nextNukePlanningTick;
		bool nukeOperationActive;
		bool nukeLaunched;
		uint nukeSecureTargetId;
		CPos nukeStrikeCell;
		int nukeOperationStartedTick = -1;
		int nukeReleaseTick = -1;
		uint recentNukeSecureTargetId;
		int recentNukeFollowupUntilTick = -1;

		public FransSupportCoordinatorBotModule(Actor self, FransSupportCoordinatorBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			supportPowerService = self.Owner.PlayerActor.TraitsImplementing<IFransSupportPowerService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSupportCoordinator requires FransSupportPowerBotModule.");
			generalService = self.Owner.PlayerActor.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSupportCoordinator requires FransGeneralBotModule.");
			commandBidService = self.Owner.PlayerActor.TraitsImplementing<IFransCommandBidService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSupportCoordinator requires FransCommandBidBotModule.");
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSupportCoordinator requires FransRiskModelBotModule.");
		}

		protected override void TraitEnabled(Actor self)
		{
			scanTicks = 1 + (int)(self.ActorID % (uint)Math.Max(1, Info.ScanInterval));
			ClearNukeOperation();
			recentNukeSecureTargetId = 0;
			recentNukeFollowupUntilTick = -1;
			nextNukePlanningTick = 0;
			FransBotLog.BotDebug(world,
				"{0}: FransSupportCoordinator NUKE PLANNING BACKOFF enabled. Ready-but-unlaunchable FAIR-INTEL planning retries no faster than every {1} WT; an active reserved NUKE->SECURE still checks friendly clearance at the normal {2}-WT coordination cadence.",
				player, Info.NukePlanningBackoffTicks, Info.ScanInterval);
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var perf = FransBotLog.Profile(world, player, "FransSupportCoordinator.BotTick");
			if (player.WinState != WinState.Undefined || --scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;

			generalService.EnsureCurrentMissions();
			if (nukeOperationActive)
				ProcessNukeOperation(bot);

			if (!nukeOperationActive)
			{
				var nukeConsumedThisPass = false;
				var nukeReady = supportPowerService.IsPowerReady(Info.NukeOrder);
				if (nukeReady && world.WorldTick >= nextNukePlanningTick)
				{
					if (TryStartNukeSecureOperation())
					{
						nukeConsumedThisPass = true;
						ProcessNukeOperation(bot);
					}
					else if (TryLaunchStandaloneNuke(bot))
						nukeConsumedThisPass = true;
					else
						nextNukePlanningTick = world.WorldTick + Info.NukePlanningBackoffTicks;
				}

				if (!nukeOperationActive && !nukeConsumedThisPass)
					TryUseMissionAwareParatroopers(bot);
			}
		}

		bool TryStartNukeSecureOperation()
		{
			if (!supportPowerService.IsPowerReady(Info.NukeOrder))
				return false;

			foreach (var mission in generalService.CurrentMissions
				.Where(m => m.Type == FransMissionType.Secure)
				.OrderByDescending(m => m.StrategicPriority)
				.ThenBy(m => m.TargetActorId))
			{
				if (!commandBidService.TryGetActiveMissionForTarget(mission.TargetActorId, out var active) ||
					active.MissionType != FransMissionType.Secure || active.Commander != FransCommanderKind.Ground)
					continue;

				if (!supportPowerService.TryFindFairIntelNukeTarget(mission.LastVisibleTargetCell,
					Info.NukeSecureLinkRadius, out var strike, out var score))
					continue;

				if (HasFriendlyBuildingInside(strike, Info.NukeExclusionRadius))
					continue;

				nukeOperationActive = true;
				nukeLaunched = false;
				nukeSecureTargetId = mission.TargetActorId;
				nukeStrikeCell = strike;
				nukeOperationStartedTick = world.WorldTick;
				nukeReleaseTick = -1;
				FransBotLog.BotDebug(world,
					"{0}: SUPPORT OPERATION NUKE->SECURE reserves strike {1} for Ground SECURE {2} at {3}, fair-intel score {4}. Ground stages outside {5} cells; launch waits for friendly mobile clearance.",
					player, strike, mission.TargetActorId, mission.LastVisibleTargetCell, score, Info.NukeExclusionRadius);
				return true;
			}

			return false;
		}

		bool TryLaunchStandaloneNuke(IBot bot)
		{
			if (!supportPowerService.IsPowerReady(Info.NukeOrder) ||
				!supportPowerService.TryFindFairIntelNukeTarget(out var strike, out var score))
				return false;

			// SECURE-linked nuclear support remains preferred because Ground can actively stage out of
			// the exclusion zone. The fallback is intentionally opportunistic: it fires only when the
			// best fair-intel strike is already clear of every friendly/allied structure and mobile.
			if (HasFriendlyBuildingInside(strike, Info.NukeExclusionRadius) ||
				HasFriendlyMobileInside(strike, Info.NukeExclusionRadius))
				return false;

			if (!supportPowerService.TryFirePower(bot, Info.NukeOrder, strike))
				return false;

			FransBotLog.BotDebug(world,
				"{0}: SUPPORT OPERATION NUKE-STANDALONE launches at {1}, fair-intel score {2}. No suitable active Ground SECURE existed; friendly exclusion was already clear.",
				player, strike, score);
			return true;
		}

		void ProcessNukeOperation(IBot bot)
		{
			if (!nukeOperationActive)
				return;

			RefreshNukeRiskExclusion();

			if (nukeLaunched)
			{
				if (world.WorldTick < nukeReleaseTick)
					return;

				recentNukeSecureTargetId = nukeSecureTargetId;
				recentNukeFollowupUntilTick = world.WorldTick + Info.NukeParatrooperFollowupWindowTicks;
				FransBotLog.BotDebug(world,
					"{0}: SUPPORT OPERATION NUKE->SECURE releases exclusion at {1} for SECURE {2} after post-launch safety window. Ground may advance now; no enemy kill is assumed until fair intel observes it.",
					player, nukeStrikeCell, nukeSecureTargetId);
				ClearNukeOperation();
				TryUseMissionAwareParatroopers(bot);
				return;
			}

			if (!generalService.TryGetMission(nukeSecureTargetId, out var strategicMission) ||
				strategicMission.Type != FransMissionType.Secure ||
				!commandBidService.TryGetActiveMissionForTarget(nukeSecureTargetId, out var active) ||
				active.MissionType != FransMissionType.Secure || active.Commander != FransCommanderKind.Ground)
			{
				CancelNukeOperation("Ground SECURE ownership ended before launch");
				return;
			}

			if (world.WorldTick - nukeOperationStartedTick >= Info.NukeStageTimeoutTicks)
			{
				CancelNukeOperation("staging timeout");
				return;
			}

			if (!supportPowerService.IsPowerReady(Info.NukeOrder))
			{
				CancelNukeOperation("reserved Nuke is no longer launchable");
				return;
			}

			if (HasFriendlyBuildingInside(nukeStrikeCell, Info.NukeExclusionRadius))
			{
				CancelNukeOperation("friendly/allied building entered the blast exclusion zone");
				return;
			}

			if (HasFriendlyMobileInside(nukeStrikeCell, Info.NukeExclusionRadius))
				return;

			if (!supportPowerService.TryFirePower(bot, Info.NukeOrder, nukeStrikeCell))
				return;

			nukeLaunched = true;
			nukeReleaseTick = world.WorldTick + Info.NukePostLaunchHoldTicks;
			FransBotLog.BotDebug(world,
				"{0}: SUPPORT OPERATION NUKE->SECURE launches at {1} for SECURE {2}. Exclusion remains active through WT {3}; Ground attack releases only after that safety window.",
				player, nukeStrikeCell, nukeSecureTargetId, nukeReleaseTick);
		}

		void TryUseMissionAwareParatroopers(IBot bot)
		{
			if (!supportPowerService.IsPowerReady(Info.ParatrooperOrder) || nukeOperationActive)
				return;

			FransMission? chosen = null;
			if (recentNukeSecureTargetId != 0 && world.WorldTick <= recentNukeFollowupUntilTick &&
				generalService.TryGetMission(recentNukeSecureTargetId, out var recent) && recent.Type == FransMissionType.Secure)
				chosen = recent;

			if (!chosen.HasValue)
			{
				chosen = generalService.CurrentMissions
					.Where(m => m.Type != FransMissionType.Recon)
					.Where(IsMeaningfulParatrooperMission)
					.OrderBy(MissionSupportRank)
					.ThenByDescending(m => m.StrategicPriority)
					.ThenBy(m => m.TargetActorId)
					.Select(m => (FransMission?)m)
					.FirstOrDefault();
			}

			if (!chosen.HasValue)
				return;

			var mission = chosen.Value;
			if (!supportPowerService.TryFindSafeMissionDeliveryCell(Info.ParatrooperOrder,
				mission.LastVisibleTargetCell, Info.ParatrooperMissionSearchRadius, out var drop))
				return;

			if (IsCellInsideActiveNukeExclusion(drop) || !supportPowerService.TryFirePower(bot, Info.ParatrooperOrder, drop))
				return;

			var followup = mission.TargetActorId == recentNukeSecureTargetId && world.WorldTick <= recentNukeFollowupUntilTick;
			FransBotLog.BotDebug(world,
				"{0}: SUPPORT OPERATION PARATROOPERS fires at {1} for MISSION {2} target {3}{4}. Drop cell is mission-local, non-water and below critical Ground risk; landed infantry return to ordinary Ground ownership.",
				player, drop, mission.Type, mission.TargetActorId, followup ? " as NUKE follow-up" : "");
			if (followup)
			{
				recentNukeSecureTargetId = 0;
				recentNukeFollowupUntilTick = -1;
			}
		}

		bool IsMeaningfulParatrooperMission(FransMission mission)
		{
			if (mission.Type == FransMissionType.Defend)
				return true;
			return commandBidService.TryGetActiveMissionForTarget(mission.TargetActorId, out var active) &&
				active.MissionType == mission.Type;
		}

		static int MissionSupportRank(FransMission mission) => mission.Type switch
		{
			FransMissionType.Defend => 0,
			FransMissionType.Secure => 1,
			FransMissionType.Raid => 2,
			_ => 3
		};

		void RefreshNukeRiskExclusion()
		{
			if (!nukeOperationActive || world.WorldTick < nextNukeRiskRefreshTick)
				return;

			nextNukeRiskRefreshTick = world.WorldTick + 20;
			// A short-lived global FransRisk incident makes every risk-aware role route/target around
			// the reserved friendly blast zone. It is refreshed only while the operation is active,
			// so cancellation/release clears naturally within a few simulation ticks.
			riskModelService.ReportGlobalRiskIncident(nukeStrikeCell, 10000, Info.NukeExclusionRadius, 30);
		}

		bool HasFriendlyBuildingInside(CPos center, int radius)
		{
			var radiusSq = radius * radius;
			return world.ActorsHavingTrait<Building>().Any(a => IsFriendlyActor(a) &&
				(a.Location - center).LengthSquared <= radiusSq);
		}

		bool HasFriendlyMobileInside(CPos center, int radius)
		{
			var radiusSq = radius * radius;
			return world.Actors.Any(a => IsFriendlyActor(a) &&
				(a.Info.HasTraitInfo<MobileInfo>() || a.Info.HasTraitInfo<AircraftInfo>()) &&
				(a.Location - center).LengthSquared <= radiusSq);
		}

		bool IsFriendlyActor(Actor actor)
		{
			if (actor == null || actor.IsDead || !actor.IsInWorld || actor.Owner == null)
				return false;
			return actor.Owner == player || PlayerRelationship.Ally.HasRelationship(player.RelationshipWith(actor.Owner));
		}

		void CancelNukeOperation(string reason)
		{
			FransBotLog.BotDebug(world,
				"{0}: SUPPORT OPERATION NUKE->SECURE cancels strike {1} for SECURE {2}: {3}. Normal SECURE is released immediately; expensive target planning backs off before retry.",
				player, nukeStrikeCell, nukeSecureTargetId, reason);
			ClearNukeOperation();
			nextNukePlanningTick = world.WorldTick + Info.NukePlanningBackoffTicks;
		}

		void ClearNukeOperation()
		{
			nukeOperationActive = false;
			nukeLaunched = false;
			nukeSecureTargetId = 0;
			nukeStrikeCell = default;
			nukeOperationStartedTick = -1;
			nukeReleaseTick = -1;
			nextNukeRiskRefreshTick = 0;
		}

		bool IFransSupportCoordinatorService.TryGetNukeExclusion(uint secureTargetActorId, out CPos center, out int radius)
		{
			center = default;
			radius = 0;
			if (!nukeOperationActive || secureTargetActorId == 0 || secureTargetActorId != nukeSecureTargetId)
				return false;

			center = nukeStrikeCell;
			radius = Info.NukeExclusionRadius;
			return true;
		}

		public bool IsCellInsideActiveNukeExclusion(CPos cell)
		{
			if (!nukeOperationActive || !world.Map.Contains(cell))
				return false;
			var radiusSq = Info.NukeExclusionRadius * Info.NukeExclusionRadius;
			return (cell - nukeStrikeCell).LengthSquared <= radiusSq;
		}

		bool IFransSupportCoordinatorService.IsCellInsideActiveNukeExclusion(CPos cell) => IsCellInsideActiveNukeExclusion(cell);
	}
}
