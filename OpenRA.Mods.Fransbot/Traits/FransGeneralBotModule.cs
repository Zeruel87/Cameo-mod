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
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public enum FransMissionType
	{
		Raid,
		Defend,
		Secure,
		Recon
	}

	public readonly record struct FransSiteIntelActor(
		uint ActorId,
		string ActorType,
		Player Owner,
		CPos Cell,
		bool IsBuilding,
		bool IsDefensiveBuilding,
		bool IsCombatActor,
		int ObservedHp,
		int ObservedValue);

	public readonly record struct FransSiteIntel(CPos Center, FransSiteIntelActor[] Actors);

	public readonly record struct FransMission(
		Actor Target,
		uint TargetActorId,
		string TargetActorType,
		Player TargetOwner,
		CPos LastVisibleTargetCell,
		bool IsRememberedIntel,
		bool IsBuilding,
		FransSiteIntel SiteIntel,
		FransMissionType Type,
		int StrategicPriority,
		int PublishedWorldTick,
		uint MissionId = 0,
		int DefendThreatValue = 0,
		int DefendedAssetValue = 0);

	public readonly record struct FransSecureFoothold(uint TargetActorId, CPos Cell, int ControlObservedWorldTick);

	public readonly record struct FransTransportLossBlockerDiagnostic(
		uint IncidentId,
		CPos IncidentCell,
		CPos LatestLossCell,
		CPos BlockingRouteCell,
		int ExclusionRadius,
		string LifecycleState,
		string Owner);

	/// <summary>
	/// Strategic mission board. Strategic ATTACK is retired. General publishes only DEFEND, SECURE, RECON and
	/// RAID. General publishes a MISSION plus raw SiteIntel and never decides Commander-specific risk/feasibility.
	/// RAID creation requires a currently visible target/site. Stationary building RAID opportunities may retain a bounded fair last-visible snapshot so Sea can bid a fresh remembered coastal target; mobile RAID targets never receive strike memory. A committed Commander locally searches the last-visible area if the target disappears.
	/// General never issues OpenRA unit orders itself.
	/// </summary>
	public interface IFransGeneralService
	{
		IReadOnlyList<FransMission> CurrentMissions { get; }
		void EnsureCurrentMissions();
		bool TryGetMission(Actor target, out FransMission mission);
		bool TryGetMission(uint targetActorId, out FransMission mission);
		bool TryRefreshAcceptedSecureMission(uint targetActorId, out FransMission mission);
		bool TryGetDefendIncident(uint missionId, out FransMission mission);
		bool IsDefenseTarget(Actor target);
		bool TrySelectAnchorPoint(FransCommanderKind commander, FransMissionType missionType, IReadOnlyCollection<uint> committedActorIds, Actor subject, CPos missionObjective, out CPos anchorPoint);
		bool TryGetLatestGroundAnchor(out CPos anchorPoint);
		void CompleteReconMission(uint reconTargetActorId, string reason);
		void ReportRaidRetreat(uint raidTargetActorId, string reason);
		void ReportSecureRetreat(uint secureTargetActorId, string reason);
		bool EstablishSecureAnchor(uint secureTargetActorId, CPos anchorCell, string reason);
		bool CompleteDomainSecureMission(uint secureTargetActorId, FransCommanderKind commander, CPos clearCell, string reason);
		bool TryGetDomainSecureClearWorldTick(uint secureTargetActorId, FransCommanderKind commander, out int clearWorldTick);
		bool TryGetRecentDomainSecureClearNear(CPos objectiveCell, int radius, int notBeforeWorldTick, out FransCommanderKind commander, out int clearWorldTick);
		void RequestSeaTransportBeachSecure(uint requestId, CPos beachCell, int validThroughWorldTick);
		void ReleaseSeaTransportBeachSecure(uint requestId);
		bool IsSeaTransportBeachSecureRequested(uint requestId);
		bool IsTransportLossSecure(uint targetActorId);
		int TransportLossExclusionRevision { get; }
		bool IsTransportLossRouteAllowed(IReadOnlyList<CPos> route);
		bool TryGetTransportLossRouteBlocker(IReadOnlyList<CPos> route, out FransTransportLossBlockerDiagnostic blocker);
		bool IsTransportLossCorridorAllowed(CPos from, CPos to);
		bool TryGetTransportLossCorridorBlocker(CPos from, CPos to, out FransTransportLossBlockerDiagnostic blocker);
		IReadOnlyList<FransSecureFoothold> PendingSecureFootholds { get; }
		bool IsSecureFootholdDevelopmentReady(uint secureTargetActorId);
		bool TryGetSecureDefensePoint(out uint secureTargetActorId, out CPos secureCell, out int strategicPriority);
		bool TryGetSecureDefensePoint(uint secureTargetActorId, out CPos secureCell, out int strategicPriority);
		bool IsSecureAnchor(CPos cell);
		bool CompleteSecureFoothold(uint secureTargetActorId, CPos establishedCell, string reason);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Fransbot General. Strategic ATTACK is disabled. Publishes DEFEND/SECURE/RECON/RAID MISSIONS with raw SiteIntel for Ground/Air/Sea/SpecOps. General chooses strategic mission type/target and intel freshness, but does not perform Commander-specific capability, ETA, risk or force feasibility. General never issues unit orders itself.")]
	public class FransGeneralBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("World ticks between ordinary strategic mission-board rebuilds. Qualifying attack callbacks invalidate the board immediately.")]
		public readonly int ScanInterval = 25;

		[Desc("World ticks between read-only long-game strategic assessment summaries. This diagnostic never creates missions, bids or orders.")]
		public readonly int StrategicAssessmentInterval = 1500;

		[Desc("Maximum enemy-economy intel age in world ticks still classified as Good by the read-only strategic assessment.")]
		public readonly int StrategicIntelGoodAgeTicks = 750;

		[Desc("Maximum enemy-economy intel age in world ticks classified as Aging. Older remembered economy intel is Poor.")]
		public readonly int StrategicIntelAgingAgeTicks = 2000;

		[Desc("Maximum distance in cells from an economy actor to any mine/gmine in a MineCluster when associating that actor with a productive ore/gem area.")]
		public readonly int StrategicMineEconomyLinkRadius = 20;

		[Desc("Low strategic priority of RECON. It is intentionally below DEFEND/SECURE/RAID and wins only when Commander capacity is otherwise free.")]
		public readonly int ReconStrategicPriority = 100;

		[Desc("Strategic priority used only for PIONEER exact-objective RECON validation. It outranks ordinary persistent RECON but remains below RAID/SECURE.")]
		public readonly int PioneerReconStrategicPriority = 200;

		[Desc("Extra globally reserved RECON capacity available only while an unrepresented PIONEER exact-objective validation is waiting. This prevents four persistent fan patrols from starving expansion reconnaissance.")]
		public readonly int MaximumPioneerReconValidationMissions = 1;

		[Desc("World ticks before a completed/failed MineCluster RECON target may be selected again.")]
		public readonly int ReconTargetCooldownTicks = 750;

		[Desc("Global maximum simultaneous RECON work, counting accepted persistent Commander RECON missions plus still-pending General RECON slots. Accepted RECON remains counted even after its old board slot is superseded/closed, preventing persistent scouts from accumulating above this limit.")]
		public readonly int MaximumActiveReconMissions = 4;

		[Desc("Number of geographic fan arms used by ordinary RECON selection around the home FACT/MCV. Special PIONEER/SECURE validation RECON still outranks the fan. Four gives a simple outward cross/fan without map-specific logic.")]
		public readonly int ReconFanArmCount = 4;

		[Desc("World ticks an active General RECON slot may remain without an active Commander MISSION before the slot is released to cooldown. The scout patrol itself remains persistent indefinitely while its MISSION is active; this only prevents dead/retreated/superseded scouts from pinning a strategic slot forever.")]
		public readonly int ReconInactiveMissionSlotReleaseTicks = 750;

		[Desc("World ticks a newly published RECON target without an active MISSION may remain with no Commander bid before General backs that target off. Existing active persistent RECON is never affected by this timer.")]
		public readonly int ReconNoBidBackoffTicks = 500;

		[Desc("If true, legitimate map-file spawn points (mpspawn actor cells) minus the own home spawn seed persistent enemy-base RECON probes. Without them a fog-honest bot can patrol ore forever and never discover the enemy base.")]
		public readonly bool EnemySpawnReconEnabled = true;

		[Desc("Cells around the own HomeLocation that suppress an enemy-spawn RECON probe, so the bot never scouts its own spawn.")]
		public readonly int EnemySpawnReconOwnHomeExclusionRadius = 10;

		[Desc("Maximum RECON board slots enemy-spawn probes may occupy at once; remaining slots stay reserved for MineCluster fan reconnaissance.")]
		public readonly int EnemySpawnReconMaxSlots = 2;

		[Desc("Cells around a spawn probe that count as observed while a scout is nearby or the cell itself is visible.")]
		public readonly int EnemySpawnReconObservationRadius = 5;

		[Desc("Cells around a spawn probe where a known enemy structure counts as the probe's intel already resolved.")]
		public readonly int EnemySpawnReconResolvedRadius = 12;

		[Desc("Strategic priority of precision RAID. RAID is opportunistic and remains below SECURE; once committed it is never recalled for DEFEND.")]
		public readonly int RaidStrategicPriority = 700;

		[Desc("Maximum simultaneous neutral precision RAID opportunities. General does not rank target types; Commanders rank the published opportunities independently.")]
		public readonly int MaximumActiveRaidMissions = 10;

		[Desc("Radius in cells around a RAID mission target included in the raw SiteIntel snapshot published with the MISSION. General does not interpret these actors as Commander-specific risk or feasibility.")]
		public readonly int RaidSiteIntelRadius = 10;

		[ActorReference]
		[Desc("Visible mobile actor types that General may expose as neutral RAID opportunities in addition to buildings. This is eligibility only; target priority belongs exclusively to Commanders.")]
		public readonly FrozenSet<string> RaidEligibleMobileTargetTypes = FrozenSet<string>.Empty;

		[Desc("Maximum age in world ticks for StrategicMap samples used by General to decide whether the currently visible RAID site is fresh enough to publish.")]
		public readonly int RaidIntelFreshTicks = 250;

		[Desc("Maximum world ticks a previously visible stationary BUILDING RAID may remain published from its frozen fair last-visible snapshot after vision is lost. Mobile RAID targets are never remembered. Sea may use this window for coastal pressure; Ground/Air/SpecOps keep their own visible-target bid rules.")]
		public readonly int RaidRememberedBuildingLifetimeTicks = 3000;

		[Desc("If true, General may open a remembered STATIONARY-building RAID straight from combat-intel memory when no live publish ever got a fresh-intel window: the building was seen once and cannot move, so its last-seen cell remains a fair strike objective until the snapshot expires. Required contribution falls back to the public ruleset max HP when no observed HP exists.")]
		public readonly bool RaidPublishRememberedBuildings = false;

		[Desc("Minimum fresh sample points among target center plus eight points around RaidSiteIntelRadius before General may open an ordinary RAID MISSION. This is an intel-quality publication gate, not a defense/risk feasibility test.")]
		public readonly int RaidMinimumFreshAreaSamples = 5;

		[Desc("Extra world ticks after the winning Commander's ETA before General rechecks the same RAID target. The active Commander owns execution; General never keeps stale target memory alive.")]
		public readonly int RaidPostEtaRecheckMarginTicks = 300;

		[Desc("World ticks a RAID target is suppressed after an explicit Commander RETREAT. Lost visibility or normal target disappearance does not apply this cooldown.")]
		public readonly int RaidRetreatCooldownTicks = 750;

		[Desc("World ticks a visible RAID opportunity with no winning Commander MISSION may occupy a General slot before it is briefly backed off for another target.")]
		public readonly int RaidNoBidBackoffTicks = 500;

		[Desc("RAID MISSION priority bonus for targets close to the next published SECURE point. This is a strategic softening bonus only; Commander target doctrine and feasibility still decide the winning bid.")]
		public readonly int RaidNextSecurePriorityBonus = 50;

		[Desc("Radius in cells around the next published SECURE point where RAID MISSIONs receive RaidNextSecurePriorityBonus.")]
		public readonly int RaidNextSecurePriorityRadius = 14;

		[Desc("Maximum temporary RAID strategic-value bonus for a hostile actor observed attacking an owned actor. The bonus decays to zero over RaidInterferenceMemoryTicks and is generic across target types.")]
		public readonly int RaidInterferencePriorityBonus;

		[Desc("World ticks over which an observed hostile attack remains operational-interference evidence for RAID scoring. Repeated observed attacks refresh this bounded memory.")]
		public readonly int RaidInterferenceMemoryTicks;

		[Desc("Strategic priority of SECURE. It is deliberate territorial work and outranks opportunistic RAID and RECON.")]
		public readonly int SecureStrategicPriority = 800;

		[Desc("Strategic priority of the Sea-only support SECURE temporarily opened around a GroundTransfer destination beach. This support mission never becomes a territorial Ground ANCHOR.")]
		public readonly int TransportBeachSecureStrategicPriority = 850;

		[ActorReference]
		[Desc("Owned naval transport actor types whose observed destruction opens an ordinary domain-neutral SECURE at the last known loss cell.")]
		public readonly FrozenSet<string> TransportLossActorTypes = FrozenSet<string>.Empty;

		[Desc("Nearby destroyed transports inside this radius merge into the same persistent LST-loss SECURE incident instead of publishing duplicate missions.")]
		public readonly int TransportLossSecureMergeRadius = 10;

		[Desc("Transport-only exclusion radius around every active LST-loss SECURE incident. New LST routes may not cross this area until Ground/Air/Sea reports CLEAR or an ownerless incident's latest loss evidence is continuously observed with no authoritative danger; combat units remain free to enter and clear it.")]
		public readonly int TransportLossRouteExclusionRadius = 10;

		[Desc("Repeated losses inside one ownerless merged LST-loss SECURE incident at/above this count escalate the incident into a strategic transport closure until the same SECURE is genuinely cleared or invalidated by continuous directly observed clear evidence.")]
		public readonly int TransportLossSevereLossCount = 4;

		[Desc("Transport-only exclusion radius used after TransportLossSevereLossCount is reached. This widens logistics avoidance for a proven kill-zone without changing combat Commander access or the SECURE mission itself.")]
		public readonly int TransportLossSevereRouteExclusionRadius = 18;

		[Desc("World ticks of continuous direct observation of an ownerless incident's latest loss cell with no nearby authoritative CombatIntel danger evidence required before General invalidates it. This never expires a Commander-owned, unobserved, or still-dangerous incident by age alone.")]
		public readonly int TransportLossObservedClearHoldTicks = 250;

		[Desc("Maximum simultaneous General SECURE opportunities. Each target has an independent no-bid/ETA/ANCHOR lifecycle and may be owned by a different Commander capacity.")]
		public readonly int MaximumActiveSecureMissions = 3;

		[Desc("Radius in cells used with fair CombatIntel when estimating remembered/visible combat force around every SECURE area, whether anchored by a MineCluster or an enemy Construction Yard.")]
		public readonly int SecureRiskAssessmentRadius = 18;

		[Desc("Minimum shared RiskModel score for an otherwise empty MineCluster to need SECURE. Visible/remembered enemy combat force can independently make the area risky.")]
		public readonly int SecureMinimumRiskScore = 25;








		[Desc("Strategic SECURE score contributed by each live mine/gmine node in a candidate MineCluster. A known enemy Construction Yard contributes exactly the same score.")]
		public readonly int SecureMineNodeScore = 800;

		[Desc("Maximum distance in cells from an ore/gem mine for a known enemy Construction Yard to merge into that MineCluster SECURE instead of creating a duplicate standalone SECURE.")]
		public readonly int SecureConstructionYardMergeRadius = 14;

		[Desc("Strategic SECURE score penalty per shared RiskModel point. Risk controls difficulty/required force and must never make a dangerous area more attractive merely because it is dangerous.")]
		public readonly int SecureRiskScorePenaltyWeight = 8;

		[Desc("Strategic SECURE score penalty per Manhattan cell from our current economic frontier/home anchor.")]
		public readonly int SecureDistanceScorePerCell = 10;

		[Desc("Strategic bonus for a SECURE candidate close to the current fair-intel Ground Forward Anchor. This favors contiguous frontier growth (for example Scandinavia -> Finland/Russia) without making distant objectives impossible.")]
		public readonly int SecureFrontierContinuityBonus = 2000;

		[Desc("Maximum Manhattan distance from the current Ground Forward Anchor for SecureFrontierContinuityBonus.")]
		public readonly int SecureFrontierContinuityRadius = 30;

		[Desc("Strategic score bonus for a SECURE candidate that overlaps an MCV expansion objective explicitly blocked behind SECURE REQUIRED. This is a handoff from Expansion to General, not hidden intel: the pioneer MCV earned this knowledge by observing danger.")]
		public readonly int ExpansionBlockedSecurePriorityBonus = 5000;

		[Desc("Maximum cell distance from an MCV SECURE REQUIRED expansion objective for a General SECURE candidate to count as the expansion-unblock mission.")]
		public readonly int ExpansionBlockedSecureRadius = 12;


		[Desc("World ticks before a RETREATed/physically completed SECURE MineCluster may be selected again.")]
		public readonly int SecureTargetCooldownTicks = 3000;

		[Desc("World ticks a newly published SECURE with no winning Commander MISSION may occupy one SECURE slot before General rotates that target to a short backoff.")]
		public readonly int SecureNoBidBackoffTicks = 1500;

		[ActorReference]
		[Desc("Allied structures that claim a nearby ore-mine for team-aware SECURE selection. General avoids opening/reopening military SECURE work inside an allied FACT/PROC economy area; autonomous MCV expansion remains a separate system.")]
		public readonly FrozenSet<string> SecureAlliedClaimStructureTypes = FrozenSet<string>.Empty;

		[Desc("Maximum distance in cells from an allied claim structure to an ore-mine before that individual mine is excluded from this bot's SECURE candidates.")]
		public readonly int SecureAlliedClaimRadius = 14;



		[Desc("World ticks DefenseCommander may continue treating an established SECURE point as priority territory after the FACT + support foothold handoff completes.")]
		public readonly int SecureDefenseHoldTicks = 1500;

		[Desc("World ticks a strategic defense incident remains active after the latest qualifying observed attack.")]
		public readonly int DefenseMemoryTicks = 300;

		[Desc("Minimum world ticks between full pressure/asset reassessments for repeated attacks by the same DEFEND representative. Faster callbacks only refresh the incident lease.")]
		public readonly int DefenseIncidentReassessmentInterval = 50;

		[Desc("Nearby qualifying attacks inside this radius merge into one strategic DEFEND incident instead of creating one mission per attacker.")]
		public readonly int DefenseIncidentMergeRadius = 8;

		[Desc("Radius used to judge whether attacks on ordinary forward combat units are part of a sufficiently large visible mobile enemy concentration.")]
		public readonly int DefenseClusterRadius = 8;

		[Desc("Minimum visible mobile combat threats inside DefenseClusterRadius before an attack on an ordinary combat unit can escalate into strategic DEFEND.")]
		public readonly int DefenseClusterMinimumMobileThreats = 4;

		[Desc("Minimum visible enemy combat value inside DefenseClusterRadius before an attack on an ordinary combat unit can escalate into strategic DEFEND.")]
		public readonly int DefenseClusterMinimumVisibleValue = 2500;

		[Desc("Base strategic priority of a DEFEND incident created only by a concentrated enemy attack on ordinary combat units. This remains below the global offense-preemption band even at maximum pressure; local Commanders still answer the DEFEND normally.")]
		public readonly int ClusterDefenseBasePriority = 550;

		[Desc("Maximum priority bonus added to DEFEND missions from visible local enemy combat pressure.")]
		public readonly int DefensePressurePriorityBonusMaximum = 100;

		[Desc("Visible local enemy combat value divided by this number becomes DEFEND pressure priority bonus, capped by DefensePressurePriorityBonusMaximum.")]
		public readonly int DefensePressureValuePerPriorityPoint = 40;

		[Desc("Additional DEFEND priority when the observed attack crosses the defended actor into a worse damage state. This is a coarse damage-pressure signal, not hidden DPS knowledge.")]
		public readonly int DefenseDamageStateTransitionPriorityBonus = 50;

		[ActorReference]
		[Desc("Owned support/capture actors whose observed attack may create strategic DEFEND even though they are not normal economy/production structures.")]
		public readonly FrozenSet<string> SupportAssetTypes = FrozenSet<string>.Empty;

		[Desc("Strategic DEFEND base priority for SupportAssetTypes.")]
		public readonly int SupportAssetDefensePriority = 500;

		[Desc("Strategic DEFEND base priority for other owned structures not covered by the explicit command/superweapon/economy/production/tech groups.")]
		public readonly int OtherOwnedStructureDefensePriority = 450;

		[ActorReference]
		[Desc("Actor types used to classify owned construction/control assets for DEFEND importance. These are not strategic attack targets.")]
		public readonly FrozenSet<string> CommandTargetTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Actor types used to classify owned superweapon assets for DEFEND importance.")]
		public readonly FrozenSet<string> SuperweaponTargetTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Actor types used to classify owned economy assets for DEFEND importance. RAID mission target eligibility is evaluated separately.")]
		public readonly FrozenSet<string> EconomyTargetTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Actor types used to classify owned production assets for DEFEND importance.")]
		public readonly FrozenSet<string> ProductionTargetTypes = FrozenSet<string>.Empty;


		[ActorReference]
		[Desc("Actor types used to classify owned technology assets for DEFEND importance.")]
		public readonly FrozenSet<string> TechTargetTypes = FrozenSet<string>.Empty;

		[Desc("DEFEND importance for owned Construction Yards and MCVs.")]
		public readonly int CommandTargetPriority = 900;

		[Desc("DEFEND importance for owned superweapon structures.")]
		public readonly int SuperweaponTargetPriority = 850;


		[Desc("DEFEND importance for owned harvesters/refineries.")]
		public readonly int EconomyTargetPriority = 650;

		[Desc("DEFEND importance for owned military production structures.")]
		public readonly int ProductionTargetPriority = 600;


		[Desc("DEFEND importance for owned technology structures.")]
		public readonly int TechTargetPriority = 500;


		[Desc("Maximum strategic missions published at once. Sized to expose 10 RAID + 3 SECURE + 4 globally bounded RECON + up to 2 DEFEND opportunities without one mission family crowding out another.")]
		public readonly int MaximumPublishedMissions = 24;

		[Desc("Maximum DEFEND incidents allowed on the published command board at once.")]
		public readonly int MaximumDefendMissions = 2;





		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (ScanInterval < 25 || StrategicAssessmentInterval <= 0 || StrategicIntelGoodAgeTicks < 0 ||
				StrategicIntelAgingAgeTicks < StrategicIntelGoodAgeTicks || StrategicMineEconomyLinkRadius <= 0 ||
				ReconStrategicPriority < 0 || PioneerReconStrategicPriority <= ReconStrategicPriority || PioneerReconStrategicPriority >= RaidStrategicPriority || MaximumPioneerReconValidationMissions <= 0 || ReconTargetCooldownTicks <= 0 || MaximumActiveReconMissions <= 0 || ReconFanArmCount <= 0 || ReconInactiveMissionSlotReleaseTicks <= 0 || ReconNoBidBackoffTicks <= 0 ||
				EnemySpawnReconOwnHomeExclusionRadius < 0 || EnemySpawnReconMaxSlots < 0 || EnemySpawnReconObservationRadius < 0 || EnemySpawnReconResolvedRadius < 0 ||
				RaidStrategicPriority <= ReconStrategicPriority || MaximumActiveRaidMissions <= 0 || RaidSiteIntelRadius <= 0 || RaidIntelFreshTicks <= 0 || RaidRememberedBuildingLifetimeTicks <= 0 || RaidMinimumFreshAreaSamples <= 0 || RaidMinimumFreshAreaSamples > 9 ||
				RaidPostEtaRecheckMarginTicks < 0 || RaidRetreatCooldownTicks <= 0 || RaidNoBidBackoffTicks <= 0 || RaidNextSecurePriorityBonus < 0 || RaidNextSecurePriorityRadius <= 0 || RaidInterferencePriorityBonus <= 0 || RaidInterferenceMemoryTicks <= 0 || (long)RaidStrategicPriority + RaidNextSecurePriorityBonus + RaidInterferencePriorityBonus >= SecureStrategicPriority || SecureStrategicPriority <= RaidStrategicPriority ||
				SecureFrontierContinuityBonus < 0 || SecureFrontierContinuityRadius <= 0 ||
				MaximumActiveSecureMissions <= 0 || SecureTargetCooldownTicks <= 0 || SecureNoBidBackoffTicks <= 0 || SecureAlliedClaimStructureTypes.Count == 0 || SecureAlliedClaimRadius <= 0 || SecureDefenseHoldTicks < 0 ||
				TransportBeachSecureStrategicPriority < 0 || TransportLossSecureMergeRadius <= 0 || TransportLossRouteExclusionRadius <= 0 || TransportLossSevereLossCount < 2 || TransportLossSevereRouteExclusionRadius < TransportLossRouteExclusionRadius || TransportLossObservedClearHoldTicks <= 0 ||
				SecureRiskAssessmentRadius <= 0 || SecureMinimumRiskScore < 0 ||
				SecureMineNodeScore < 0 || SecureConstructionYardMergeRadius <= 0 || SecureRiskScorePenaltyWeight < 0 || SecureDistanceScorePerCell < 0 || ExpansionBlockedSecurePriorityBonus < 0 || ExpansionBlockedSecureRadius <= 0 ||
				DefenseMemoryTicks <= 0 || DefenseIncidentReassessmentInterval <= 0 || DefenseIncidentMergeRadius < 0 || DefenseClusterRadius <= 0 ||
				DefenseClusterMinimumMobileThreats <= 0 || DefenseClusterMinimumVisibleValue < 0 || ClusterDefenseBasePriority < 0 ||
				DefensePressurePriorityBonusMaximum < 0 || DefensePressureValuePerPriorityPoint <= 0 || DefenseDamageStateTransitionPriorityBonus < 0 || SupportAssetDefensePriority < 0 ||
				OtherOwnedStructureDefensePriority < 0 || CommandTargetPriority < 0 || SuperweaponTargetPriority < 0 ||
				EconomyTargetPriority < 0 || ProductionTargetPriority < 0 || TechTargetPriority < 0 ||
				MaximumPublishedMissions <= 0 || MaximumDefendMissions < 0 || MaximumDefendMissions > MaximumPublishedMissions)
				throw new YamlException("FransGeneral DEFEND/SECURE/RECON/RAID priorities, freshness/timing and published-mission limits must be valid.");
		}

		public override object Create(ActorInitializer init) { return new FransGeneralBotModule(init.Self, this); }
	}

	public class FransGeneralBotModule : ConditionalTrait<FransGeneralBotModuleInfo>,
		IBotTick, IBotRespondToAttack, IFransGeneralService
	{
		sealed class TransportLossSecureIncident
		{
			public readonly CPos Cell;
			public readonly int OpenedWorldTick;
			public CPos LatestLossCell;
			public int LastLossWorldTick;
			public int LossCount;
			public uint LatestLostActorId;
			public int ObservedClearSinceWorldTick = -1;
			public int NextLifecycleDiagnosticWorldTick;

			public TransportLossSecureIncident(CPos cell, int worldTick, uint lostActorId, int diagnosticInterval)
			{
				Cell = cell;
				OpenedWorldTick = worldTick;
				LatestLossCell = cell;
				LastLossWorldTick = worldTick;
				LossCount = 1;
				LatestLostActorId = lostActorId;
				NextLifecycleDiagnosticWorldTick = worldTick + diagnosticInterval;
			}
		}

		readonly World world;
		readonly Player player;

		// DEFEND incidents keep a stable strategic MissionId even when the currently visible hostile
		// representative changes. ActorID remains tactical target data; MissionId is auction identity.
		readonly Dictionary<uint, int> defendTargetUntil = [];
		readonly Dictionary<uint, int> defendTargetPriority = [];
		// Strategic incident space is anchored where the local battle began. The current representative
		// remains tactical evidence and may move or be replaced without dragging this origin across the map.
		readonly Dictionary<uint, CPos> defendIncidentOrigins = [];
		readonly Dictionary<uint, uint> defendIncidentMissionIds = [];
		readonly Dictionary<uint, int> defendIncidentThreatValues = [];
		readonly Dictionary<uint, int> defendIncidentAssetValues = [];
		readonly Dictionary<uint, int> defendIncidentLastAssessmentTicks = [];
		uint nextDefenseIncidentSequence;
		readonly Dictionary<uint, FransMission> missionsByActorId = [];
		readonly List<FransMission> currentMissions = [];
		readonly Dictionary<uint, int> mineClusterLastObservedTick = [];
		readonly Dictionary<uint, int> reconTargetCooldownUntil = [];
		readonly Dictionary<uint, int> secureTargetCooldownUntil = [];
		readonly HashSet<uint> secureReconRequiredTargets = [];
		readonly HashSet<uint> expansionReconMissionTargets = [];
		// A cleared SECURE immediately becomes a strategic ANCHOR. PendingSecureFootholds is
		// retained only as the development queue for autonomous MCV/BaseBuilder/DefenseCommander.
		readonly Dictionary<uint, FransSecureFoothold> pendingSecureFootholds = [];
		readonly Dictionary<uint, CPos> establishedSecureAnchorPoints = [];
		readonly Dictionary<uint, int> secureAnchorEstablishedWorldTick = [];
		bool hasLatestGroundAnchor;
		uint latestGroundAnchorTargetId;
		CPos latestGroundAnchorPoint;
		int lastGroundForwardAnchorIntelSnapshotTick = -1;
		readonly HashSet<uint> completedSecureFootholds = [];
		readonly Dictionary<uint, int> establishedSecureDefenseHoldUntil = [];

		IFransCombatIntelService combatIntelService;
		IFransMineClusterService mineClusterService;
		IFransEconomicSaturationService economicSaturationService;
		IFransRiskModelService riskModelService;
		IFransStrategicMapService strategicMapService;
		IFransCommandBidService commandBidService;
		IFransOreEconomyService oreEconomyService;
		IFransGroundCommanderService groundCommanderService;
		IFransExpansionStateService expansionStateService;
		IFransBaseBuilderService baseBuilderService;
		Shroud shroud;
		readonly Dictionary<uint, CPos> activeReconTargets = [];
		readonly Dictionary<uint, int> activeReconWithoutMissionSinceTick = [];

		// Enemy-spawn probes live in the same RECON machinery but use a synthetic key space that can
		// never collide with a MineCluster key (and never hits the 0/MaxValue sentinels). Cells come
		// exclusively from the map-file mpspawn actors minus the own home spawn: the same public
		// spawn list every lobby player sees on the map preview, so no hidden state is read.
		const uint SpawnProbeKeyBase = 0xF0000000;
		readonly Dictionary<uint, CPos> spawnProbeTargets = [];
		readonly Dictionary<uint, int> spawnProbeLastObservedTick = [];
		bool spawnProbesSeeded;
		readonly Dictionary<uint, int> activeRaidTargets = [];
		readonly Dictionary<uint, FransMission> activeRaidSnapshots = [];
		readonly Dictionary<uint, int> raidTargetCooldownUntil = [];
		readonly Dictionary<uint, int> recentHostileActionWorldTick = [];
		readonly Dictionary<uint, CPos> activeSecureTargets = [];
		readonly HashSet<uint> pioneerExpansionPrioritySecureTargets = [];
		readonly Dictionary<uint, int> activeSecurePublishedWorldTick = [];
		readonly Dictionary<uint, (CPos Cell, int ValidThroughWorldTick)> seaTransportBeachSecureRequests = [];
		readonly Dictionary<uint, TransportLossSecureIncident> transportLossSecureIncidents = [];
		readonly Dictionary<uint, CPos> ownedTransportLastKnownCells = [];
		uint nextTransportLossSecureSequence;
		int transportLossExclusionRevision;
		// Air/Sea CLEAR is domain memory only. It suppresses that same domain from re-bidding
		// until fresh domain-relevant enemy intel appears, while Ground remains free to take SECURE.
		readonly Dictionary<(uint TargetActorId, FransCommanderKind Commander), int> domainSecureClearWorldTick = [];
		readonly Dictionary<(uint TargetActorId, FransCommanderKind Commander), CPos> domainSecureClearCells = [];
		// Standalone enemy Construction Yards use their real ActorID as the SECURE target key.
		// FACTs merged into a MineCluster keep the MineCluster key and never enter this set.
		readonly HashSet<uint> standaloneFactSecureTargets = [];
		public const string SeaTransportBeachSecureTargetType = "transportbeach";
		public const string TransportLossSecureTargetType = "lstloss";
		int scanTicks;
		int nextStrategicAssessmentTick;
		int lastPublishedWorldTick = -1;

		public FransGeneralBotModule(Actor self, FransGeneralBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;
			combatIntelService = self.Owner.PlayerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransGeneral requires FransCombatIntelBotModule.");
			mineClusterService = self.Owner.PlayerActor.TraitsImplementing<IFransMineClusterService>().FirstOrDefault();
			economicSaturationService = self.Owner.PlayerActor.TraitsImplementing<IFransEconomicSaturationService>().FirstOrDefault();
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransGeneral requires FransRiskModelBotModule for SECURE risk validation.");
			strategicMapService = self.Owner.PlayerActor.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransGeneral requires FransStrategicMapBotModule for ANCHOR POINT selection.");
			commandBidService = self.Owner.PlayerActor.TraitsImplementing<IFransCommandBidService>().FirstOrDefault();
			oreEconomyService = self.Owner.PlayerActor.TraitsImplementing<IFransOreEconomyService>().FirstOrDefault();
			groundCommanderService = self.Owner.PlayerActor.TraitsImplementing<IFransGroundCommanderService>().FirstOrDefault();
			expansionStateService = self.Owner.PlayerActor.TraitsImplementing<IFransExpansionStateService>().FirstOrDefault();
			baseBuilderService = self.Owner.PlayerActor.TraitsImplementing<IFransBaseBuilderService>().FirstOrDefault();
			shroud = self.Trait<Shroud>();
		}

		protected override void TraitEnabled(Actor self)
		{
			// Deterministic per-module/player startup phase; cadence remains unchanged.
			scanTicks = (int)((self.ActorID + 2u) % (uint)Info.ScanInterval) + 1;
			nextStrategicAssessmentTick = world.WorldTick + Info.StrategicAssessmentInterval +
				(int)((self.ActorID + 11u) % (uint)Info.ScanInterval);
			lastPublishedWorldTick = -1;
			activeReconTargets.Clear();
			activeReconWithoutMissionSinceTick.Clear();
			activeRaidTargets.Clear();
			activeRaidSnapshots.Clear();
			raidTargetCooldownUntil.Clear();
			recentHostileActionWorldTick.Clear();
			activeSecureTargets.Clear();
			activeSecurePublishedWorldTick.Clear();
			seaTransportBeachSecureRequests.Clear();
			transportLossSecureIncidents.Clear();
			ownedTransportLastKnownCells.Clear();
			nextTransportLossSecureSequence = 0;
			transportLossExclusionRevision = 0;
			domainSecureClearWorldTick.Clear();
			domainSecureClearCells.Clear();
			standaloneFactSecureTargets.Clear();
			mineClusterLastObservedTick.Clear();
			reconTargetCooldownUntil.Clear();
			secureTargetCooldownUntil.Clear();
			secureReconRequiredTargets.Clear();
			expansionReconMissionTargets.Clear();
			pendingSecureFootholds.Clear();
			establishedSecureAnchorPoints.Clear();
			secureAnchorEstablishedWorldTick.Clear();
			hasLatestGroundAnchor = false;
			latestGroundAnchorTargetId = 0;
			latestGroundAnchorPoint = default;
			lastGroundForwardAnchorIntelSnapshotTick = -1;
			completedSecureFootholds.Clear();
			establishedSecureDefenseHoldUntil.Clear();
			spawnProbeTargets.Clear();
			spawnProbeLastObservedTick.Clear();
			spawnProbesSeeded = false;
			ClearDefenseIncidents();
			missionsByActorId.Clear();
			currentMissions.Clear();
			FransBotLog.BotDebug(world,
				"{0}: FransGeneral FAN-RECON MISSION model active: up to {1} RECON, {2} RAID and {3} SECURE opportunities on a {4}-mission board. DEFEND incidents keep stable MissionId auction identity while the visible representative may change. SECURE strategic objects are ore/gem mines plus remembered enemy FACTs; Ground SECURE creates territorial anchors, Air/Sea keep domain CLEAR memory, and ExpansionManager consumes raw RECON/SECURE intel handoff without General computing MCV feasibility. RAID ETA recheck + RETREAT cooldown remain {5}/{6} WT margins; stationary building RAID snapshots may remain fair remembered opportunities for up to {7} WT after vision is lost, while mobile RAID targets remain visible-only.",
				player, Info.MaximumActiveReconMissions, Info.MaximumActiveRaidMissions, Info.MaximumActiveSecureMissions, Info.MaximumPublishedMissions,
				Info.RaidPostEtaRecheckMarginTicks, Info.RaidRetreatCooldownTicks, Info.RaidRememberedBuildingLifetimeTicks);
		}

		protected override void TraitDisabled(Actor self)
		{
			ClearDefenseIncidents();
			missionsByActorId.Clear();
			currentMissions.Clear();
			mineClusterLastObservedTick.Clear();
			reconTargetCooldownUntil.Clear();
			secureTargetCooldownUntil.Clear();
			secureReconRequiredTargets.Clear();
			expansionReconMissionTargets.Clear();
			establishedSecureAnchorPoints.Clear();
			secureAnchorEstablishedWorldTick.Clear();
			hasLatestGroundAnchor = false;
			latestGroundAnchorTargetId = 0;
			latestGroundAnchorPoint = default;
			lastGroundForwardAnchorIntelSnapshotTick = -1;
			completedSecureFootholds.Clear();
			activeReconTargets.Clear();
			activeReconWithoutMissionSinceTick.Clear();
			activeRaidTargets.Clear();
			activeRaidSnapshots.Clear();
			raidTargetCooldownUntil.Clear();
			recentHostileActionWorldTick.Clear();
			activeSecureTargets.Clear();
			activeSecurePublishedWorldTick.Clear();
			seaTransportBeachSecureRequests.Clear();
			transportLossSecureIncidents.Clear();
			ownedTransportLastKnownCells.Clear();
			nextTransportLossSecureSequence = 0;
			transportLossExclusionRevision = 0;
			domainSecureClearWorldTick.Clear();
			domainSecureClearCells.Clear();
			standaloneFactSecureTargets.Clear();
			pendingSecureFootholds.Clear();
			establishedSecureDefenseHoldUntil.Clear();
			nextStrategicAssessmentTick = 0;
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransGeneral.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;
			EnsureCurrentMissions();
			WriteStrategicAssessmentIfDue();
		}

		static bool IsNonCombatHusk(Actor actor) => actor?.Info != null &&
			(actor.Info.HasTraitInfo<HuskInfo>() || actor.Info.Name.EndsWith(".husk", StringComparison.OrdinalIgnoreCase));

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			var attacker = e.Attacker;
			if (self == null || self.Owner != player || IsNonCombatHusk(self) || attacker == null || IsNonCombatHusk(attacker) || !IsValidVisibleEnemy(attacker))
				return;

			RecordRaidInterference(attacker);

			// Hot-path debounce before any CombatIntel pressure scan. Once this same attacker has already
			// established a strategic incident in this local area, repeated bullet/burst callbacks only
			// refresh its memory. A materially relocated attack still falls through to full qualification.
			if (TryFastRefreshSameAttackerDefenseIncident(attacker))
				return;

			combatIntelService.EnsureCurrentSnapshot();

			var defendedAssetPriority = GetDefendedAssetPriority(self);
			var visiblePressure = GetVisibleEnemyPressure(self.Location, attacker.Owner, out var mobileThreats);
			var clusteredForwardAttack = defendedAssetPriority <= 0 &&
				mobileThreats >= Info.DefenseClusterMinimumMobileThreats &&
				visiblePressure >= Info.DefenseClusterMinimumVisibleValue;

			// Ordinary battlefield contact stays local: Ground/Air/Sea FIGHT already reacts immediately.
			// General only escalates attacks on strategic/support assets or a genuinely concentrated mobile enemy push.
			if (defendedAssetPriority <= 0 && !clusteredForwardAttack)
				return;

			var basePriority = defendedAssetPriority > 0 ? defendedAssetPriority : Info.ClusterDefenseBasePriority;
			var pressureBonus = Math.Min(Info.DefensePressurePriorityBonusMaximum,
				Math.Max(0, visiblePressure) / Info.DefensePressureValuePerPriorityPoint);
			var damageBonus = e.DamageState > e.PreviousDamageState ? Info.DefenseDamageStateTransitionPriorityBonus : 0;
			var defensePriority = basePriority + pressureBonus + damageBonus;
			var until = world.WorldTick + Info.DefenseMemoryTicks;

			// Fast-path the exact same attacker before any spatial merge lookup. This closes the same-WT
			// duplicate callback hole: the first damage callback creates the incident immediately, and every
			// later callback from that actor only refreshes its memory/priority. If the actor had temporarily
			// left vision, the retained incident is reactivated without allocating/publishing a second incident.
			if (TryRefreshSameAttackerDefenseIncident(attacker, until, defensePriority, visiblePressure, defendedAssetPriority))
				return;

			var existingIncidentId = FindNearbyDefenseIncidentRepresentativeId(attacker.Location);
			if (existingIncidentId.HasValue)
			{
				var existingId = existingIncidentId.Value;
				var existingRepresentative = world.GetActorById(existingId);
				// The remembered incident identity survives a dead/hidden/less-important representative.
				// A new visible attacker may become the tactical target without restarting the Broker auction.
				var replaceRepresentative = !IsValidVisibleEnemy(existingRepresentative) ||
					GetTargetValue(attacker) > GetTargetValue(existingRepresentative);
				if (replaceRepresentative)
				{
					var replacedPriority = defendTargetPriority.TryGetValue(existingId, out var p) ? p : defensePriority;
					var replacedThreatValue = defendIncidentThreatValues.TryGetValue(existingId, out var threat) ? threat : 0;
					var replacedAssetValue = defendIncidentAssetValues.TryGetValue(existingId, out var asset) ? asset : 0;
					var stableMissionId = EnsureDefenseIncidentMissionId(existingId);
					var incidentOrigin = defendIncidentOrigins.TryGetValue(existingId, out var origin)
						? origin
						: attacker.Location;
					var oldType = existingRepresentative?.Info?.Name ?? "lost";
					RemoveDefenseIncident(existingId);
					defendTargetUntil[attacker.ActorID] = until;
					defendTargetPriority[attacker.ActorID] = Math.Max(replacedPriority, defensePriority);
					defendIncidentOrigins[attacker.ActorID] = incidentOrigin;
					defendIncidentMissionIds[attacker.ActorID] = stableMissionId;
					defendIncidentThreatValues[attacker.ActorID] = Math.Max(replacedThreatValue, visiblePressure);
					defendIncidentAssetValues[attacker.ActorID] = Math.Max(replacedAssetValue, defendedAssetPriority);
					defendIncidentLastAssessmentTicks[attacker.ActorID] = world.WorldTick;
					lastPublishedWorldTick = -1;
					FransBotLog.BotDebug(world,
						"{0}: GENERAL merges local defense pressure and changes incident representative {1} {2} -> {3} {4} at {5}; stable DEFEND MissionId {6}, priority {7}, memory through WT {8}.",
						player, oldType, existingId, attacker.Info.Name, attacker.ActorID, attacker.Location, stableMissionId,
						defendTargetPriority[attacker.ActorID], until);
					return;
				}

				var mergedPriority = defendTargetPriority.TryGetValue(existingId, out var currentPriority) ? currentPriority : 0;
				defendTargetUntil[existingId] = Math.Max(defendTargetUntil[existingId], until);
				defendTargetPriority[existingId] = Math.Max(mergedPriority, defensePriority);
				defendIncidentThreatValues[existingId] = Math.Max(
					defendIncidentThreatValues.TryGetValue(existingId, out var existingThreat) ? existingThreat : 0,
					visiblePressure);
				defendIncidentAssetValues[existingId] = Math.Max(
					defendIncidentAssetValues.TryGetValue(existingId, out var existingAsset) ? existingAsset : 0,
					defendedAssetPriority);
				defendIncidentLastAssessmentTicks[existingId] = world.WorldTick;
				var representativePublished = missionsByActorId.TryGetValue(existingId, out var publishedMission) &&
					publishedMission.Type == FransMissionType.Defend;
				if (!representativePublished || defensePriority > mergedPriority)
					lastPublishedWorldTick = -1;
				return;
			}

			defendTargetUntil[attacker.ActorID] = until;
			defendTargetPriority[attacker.ActorID] = defensePriority;
			defendIncidentOrigins[attacker.ActorID] = attacker.Location;
			defendIncidentThreatValues[attacker.ActorID] = visiblePressure;
			defendIncidentAssetValues[attacker.ActorID] = defendedAssetPriority;
			defendIncidentLastAssessmentTicks[attacker.ActorID] = world.WorldTick;
			var defendMissionId = EnsureDefenseIncidentMissionId(attacker.ActorID);
			lastPublishedWorldTick = -1;
			var defendIntel = BuildSiteIntel(attacker.Location, Info.DefenseClusterRadius, Info.DefenseMemoryTicks, attacker);
			FransBotLog.BotDebug(world,
				"{0}: GENERAL publishes MISSION DEFEND at {1}, representative {2} {3}, stable MissionId {11}, priority {4}; raw SiteIntel [{5}]. Trigger: observed attack on owned {6} {7}; visible pressure {8} from {9} mobile threat(s), memory through WT {10}.",
				player, attacker.Location, attacker.Info.Name, attacker.ActorID, defensePriority, FormatSiteIntelForLog(defendIntel),
				self.Info.Name, self.ActorID, visiblePressure, mobileThreats, until, defendMissionId);
		}

		void RecordRaidInterference(Actor attacker)
		{
			var wasActive = recentHostileActionWorldTick.TryGetValue(attacker.ActorID, out var previousTick) &&
				world.WorldTick - previousTick < Info.RaidInterferenceMemoryTicks;
			recentHostileActionWorldTick[attacker.ActorID] = world.WorldTick;
			if (wasActive)
				return;
			lastPublishedWorldTick = -1;

			var interferenceValue = GetRaidInterferenceValue(attacker.ActorID);
			var finalUtility = GetRaidMissionPriority(attacker.ActorID, attacker.Location);
			FransBotLog.BotDebug(world,
				"{0}: [RAID INTERFERENCE] target={1}#{2} recentHostileAction=0/{3}WT interferenceValue={4} finalUtility={5}.",
				player, attacker.Info.Name, attacker.ActorID, Info.RaidInterferenceMemoryTicks, interferenceValue, finalUtility);
		}

		public IReadOnlyList<FransMission> CurrentMissions
		{
			get
			{
				EnsureCurrentMissions();
				return currentMissions;
			}
		}

		static int MissionTypeTieBreakRank(FransMissionType kind) => kind switch
		{
			FransMissionType.Defend => 4,
			FransMissionType.Secure => 3,
			FransMissionType.Raid => 2,
			FransMissionType.Recon => 1,
			_ => 0
		};

		static bool PreferPublishedMission(FransMission candidate, FransMission existing)
		{
			if (candidate.StrategicPriority != existing.StrategicPriority)
				return candidate.StrategicPriority > existing.StrategicPriority;

			var candidateRank = MissionTypeTieBreakRank(candidate.Type);
			var existingRank = MissionTypeTieBreakRank(existing.Type);
			if (candidateRank != existingRank)
				return candidateRank > existingRank;

			return candidate.PublishedWorldTick > existing.PublishedWorldTick;
		}

		void PublishUniqueMission(FransMission mission)
		{
			if (mission.TargetActorId == 0)
				return;

			var index = currentMissions.FindIndex(existing => existing.TargetActorId == mission.TargetActorId);
			if (index < 0)
			{
				currentMissions.Add(mission);
				missionsByActorId[mission.TargetActorId] = mission;
				return;
			}

			var existingMission = currentMissions[index];
			if (PreferPublishedMission(mission, existingMission))
			{
				currentMissions[index] = mission;
				missionsByActorId[mission.TargetActorId] = mission;
				FransBotLog.BotDebug(world,
					"{0}: GENERAL coalesces duplicate target id {1}: {2} priority {3} replaces {4} priority {5}.",
					player, mission.TargetActorId, mission.Type, mission.StrategicPriority, existingMission.Type, existingMission.StrategicPriority);
			}
			else
			{
				missionsByActorId[mission.TargetActorId] = existingMission;
				FransBotLog.BotDebug(world,
					"{0}: GENERAL suppresses duplicate target id {1}: keeps {2} priority {3} over {4} priority {5}.",
					player, mission.TargetActorId, existingMission.Type, existingMission.StrategicPriority, mission.Type, mission.StrategicPriority);
			}
		}

		public void EnsureCurrentMissions()
		{
			if (world.Type == WorldType.Editor || combatIntelService == null)
				return;
			if (lastPublishedWorldTick >= 0 && world.WorldTick - lastPublishedWorldTick < Info.ScanInterval)
				return;

			combatIntelService.EnsureCurrentSnapshot();
			CleanupDefenseIncidents();
			EnsureSpawnProbesSeeded();
			UpdateMineClusterObservationMemory();
			// foothold development is locally gated by a physical owned FACT at that SECURE anchor.
			// The old all-map ore-occupation gate is intentionally no longer part of mission publication.
			CleanupSeaTransportBeachSecureRequests();
			ObserveOwnedTransportLosses();
			UpdateTransportLossSecureIncidentValidity();

			missionsByActorId.Clear();
			currentMissions.Clear();

			// Strategic ATTACK is retired. Only currently visible representatives of live DEFEND incidents
			// are published from enemy actor contacts; invisible incident representatives remain debounce memory only.
			var defendMissions = 0;
			foreach (var target in combatIntelService.VisibleEnemies.Where(IsValidVisibleEnemy)
				.Where(IsDefenseTarget)
				.OrderByDescending(t => defendTargetPriority.TryGetValue(t.ActorID, out var p) ? p : 0)
				.ThenByDescending(GetTargetValue)
				.ThenBy(t => t.ActorID))
			{
				if (defendMissions >= Info.MaximumDefendMissions || currentMissions.Count >= Info.MaximumPublishedMissions)
					break;
				var priority = defendTargetPriority.TryGetValue(target.ActorID, out var p) ? p : 0;
				var siteIntel = BuildSiteIntel(target.Location, Info.DefenseClusterRadius, Info.DefenseMemoryTicks, target);
				var mission = new FransMission(target, target.ActorID, target.Info.Name, target.Owner, target.Location, false,
					target.Info.HasTraitInfo<BuildingInfo>(), siteIntel, FransMissionType.Defend, priority, world.WorldTick,
					EnsureDefenseIncidentMissionId(target.ActorID),
					defendIncidentThreatValues.TryGetValue(target.ActorID, out var threatValue) ? threatValue : 0,
					defendIncidentAssetValues.TryGetValue(target.ActorID, out var assetValue) ? assetValue : 0);
				PublishUniqueMission(mission);
				defendMissions++;
			}

			// LST-loss SECURE is a normal domain-neutral incident and is published before ordinary
			// territorial opportunities so a known transport kill-zone cannot be hidden by expansion work.
			AppendTransportLossSecureMissions();
			// SECURE is selected first so RAID publication in the same scan can soften the next SECURE point.
			AppendSecureMission();
			AppendSeaTransportBeachSecureMissions();
			AppendRaidMissions();
			AppendReconMission();
			lastPublishedWorldTick = world.WorldTick;
		}


		public void RequestSeaTransportBeachSecure(uint requestId, CPos beachCell, int validThroughWorldTick)
		{
			if (requestId == 0 || !world.Map.Contains(beachCell) || validThroughWorldTick <= world.WorldTick)
				return;

			var hadOld = seaTransportBeachSecureRequests.TryGetValue(requestId, out var old);
			var changed = !hadOld || old.Cell != beachCell;
			var lease = hadOld ? Math.Max(validThroughWorldTick, old.ValidThroughWorldTick) : validThroughWorldTick;
			seaTransportBeachSecureRequests[requestId] = (beachCell, lease);
			if (!changed)
				return;

			domainSecureClearWorldTick.Remove((requestId, FransCommanderKind.Sea));
			lastPublishedWorldTick = -1;
			FransBotLog.BotDebug(world,
				"{0}: GENERAL opens Sea-only transport-beach SECURE {1} at {2}. Sea may clear/support the destination independently; this is not a Ground territorial SECURE and creates no ANCHOR.",
				player, requestId, beachCell);
		}

		public void ReleaseSeaTransportBeachSecure(uint requestId)
		{
			if (requestId == 0 || !seaTransportBeachSecureRequests.Remove(requestId))
				return;
			domainSecureClearWorldTick.Remove((requestId, FransCommanderKind.Sea));
			lastPublishedWorldTick = -1;
			FransBotLog.BotDebug(world,
				"{0}: GENERAL closes Sea-only transport-beach SECURE {1}; the GroundTransfer landing wave no longer needs this naval support request.",
				player, requestId);
		}

		public bool IsSeaTransportBeachSecureRequested(uint requestId) =>
			requestId != 0 && seaTransportBeachSecureRequests.TryGetValue(requestId, out var request) && request.ValidThroughWorldTick >= world.WorldTick;

		public bool IsTransportLossSecure(uint targetActorId) =>
			targetActorId != 0 && transportLossSecureIncidents.ContainsKey(targetActorId);

		public int TransportLossExclusionRevision => transportLossExclusionRevision;

		int GetTransportLossExclusionRadius(int lossCount) =>
			lossCount >= Info.TransportLossSevereLossCount
				? Math.Max(Info.TransportLossRouteExclusionRadius, Info.TransportLossSevereRouteExclusionRadius)
				: Info.TransportLossRouteExclusionRadius;

		bool IsTransportLossExclusionCell(CPos cell)
		{
			if (!world.Map.Contains(cell) || transportLossSecureIncidents.Count == 0)
				return false;

			foreach (var incident in transportLossSecureIncidents.Values)
			{
				var radius = GetTransportLossExclusionRadius(incident.LossCount);
				if ((incident.Cell - cell).LengthSquared <= radius * radius)
					return true;
			}
			return false;
		}

		public bool IsTransportLossRouteAllowed(IReadOnlyList<CPos> route)
		{
			if (route == null || route.Count == 0 || transportLossSecureIncidents.Count == 0)
				return true;

			return !route.Any(IsTransportLossExclusionCell);
		}

		public bool TryGetTransportLossRouteBlocker(IReadOnlyList<CPos> route, out FransTransportLossBlockerDiagnostic blocker)
		{
			blocker = default;
			if (route == null || route.Count == 0 || transportLossSecureIncidents.Count == 0)
				return false;

			foreach (var cell in route)
			{
				if (!world.Map.Contains(cell))
					continue;
				foreach (var incident in transportLossSecureIncidents.OrderBy(kv => kv.Key))
				{
					var radius = GetTransportLossExclusionRadius(incident.Value.LossCount);
					if ((incident.Value.Cell - cell).LengthSquared > radius * radius)
						continue;

					var lifecycleState = GetTransportLossDiagnosticLifecycleState(incident.Key, incident.Value, out var owner);
					blocker = new FransTransportLossBlockerDiagnostic(
						incident.Key, incident.Value.Cell, incident.Value.LatestLossCell, cell,
						radius, lifecycleState, owner);
					return true;
				}
			}

			return false;
		}

		string GetTransportLossDiagnosticLifecycleState(uint incidentId, TransportLossSecureIncident incident, out string owner)
		{
			if (TryGetTransportLossSecureOwner(incidentId, out var active))
			{
				owner = $"{active.Commander}/{active.BidderKey}:startedWT={active.StartedWorldTick}";
				return "ActiveCommanderOwned";
			}

			owner = "None";
			if (incident.ObservedClearSinceWorldTick >= 0)
				return "ObservedClearPending";
			if (GetTransportLossDangerEvidenceCount(incident.LatestLossCell) > 0)
				return "ActiveDangerEvidence";
			return IsTransportLossCellCurrentlyObserved(incident.LatestLossCell)
				? "ActiveObservedNoDanger"
				: "ActiveUnobserved";
		}

		public bool IsTransportLossCorridorAllowed(CPos from, CPos to)
		{
			return !TryFindTransportLossCorridorIntersection(from, to, out _, out _, out _);
		}

		bool TryFindTransportLossCorridorIntersection(CPos from, CPos to, out uint incidentId,
			out TransportLossSecureIncident blockingIncident, out CPos blockingCell)
		{
			incidentId = 0;
			blockingIncident = null;
			blockingCell = default;
			if (!world.Map.Contains(from) || !world.Map.Contains(to) || transportLossSecureIncidents.Count == 0)
				return false;

			var dx = to.X - from.X;
			var dy = to.Y - from.Y;
			var segmentLengthSquared = (double)dx * dx + (double)dy * dy;
			foreach (var incident in transportLossSecureIncidents.OrderBy(kv => kv.Key))
			{
				var radius = Math.Max(1, GetTransportLossExclusionRadius(incident.Value.LossCount));
				var radiusSquared = (double)radius * radius;
				double distanceSquared;
				double nearestX;
				double nearestY;
				if (segmentLengthSquared <= 0)
				{
					nearestX = from.X;
					nearestY = from.Y;
					distanceSquared = (incident.Value.Cell - from).LengthSquared;
				}
				else
				{
					var px = incident.Value.Cell.X - from.X;
					var py = incident.Value.Cell.Y - from.Y;
					var t = Math.Clamp(((double)px * dx + (double)py * dy) / segmentLengthSquared, 0.0, 1.0);
					nearestX = from.X + t * dx;
					nearestY = from.Y + t * dy;
					var ex = incident.Value.Cell.X - nearestX;
					var ey = incident.Value.Cell.Y - nearestY;
					distanceSquared = ex * ex + ey * ey;
				}

				if (distanceSquared <= radiusSquared)
				{
					incidentId = incident.Key;
					blockingIncident = incident.Value;
					blockingCell = new CPos((int)Math.Round(nearestX), (int)Math.Round(nearestY));
					return true;
				}
			}

			return false;
		}

		public bool TryGetTransportLossCorridorBlocker(CPos from, CPos to,
			out FransTransportLossBlockerDiagnostic blocker)
		{
			blocker = default;
			if (!TryFindTransportLossCorridorIntersection(from, to, out var incidentId,
				out var incident, out var blockingCell))
				return false;

			var lifecycleState = GetTransportLossDiagnosticLifecycleState(incidentId, incident, out var owner);
			blocker = new FransTransportLossBlockerDiagnostic(
				incidentId, incident.Cell, incident.LatestLossCell, blockingCell,
				Math.Max(1, GetTransportLossExclusionRadius(incident.LossCount)), lifecycleState, owner);
			return true;
		}

		uint NextTransportLossSecureId()
		{
			do
			{
				nextTransportLossSecureSequence = (nextTransportLossSecureSequence + 1u) & 0x3FFFFFFFu;
				if (nextTransportLossSecureSequence == 0)
					nextTransportLossSecureSequence = 1;
			}
			while (transportLossSecureIncidents.ContainsKey(0x40000000u | nextTransportLossSecureSequence));

			return 0x40000000u | nextTransportLossSecureSequence;
		}

		void ObserveOwnedTransportLosses()
		{
			if (Info.TransportLossActorTypes.Count == 0)
				return;

			var current = combatIntelService.OwnedActors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.Owner == player && Info.TransportLossActorTypes.Contains(a.Info.Name))
				.OrderBy(a => a.ActorID)
				.ToArray();
			var currentIds = current.Select(a => a.ActorID).ToHashSet();

			foreach (var lost in ownedTransportLastKnownCells.Where(kv => !currentIds.Contains(kv.Key)).ToArray())
			{
				RegisterTransportLossSecure(lost.Key, lost.Value);
				ownedTransportLastKnownCells.Remove(lost.Key);
			}

			foreach (var transport in current)
				ownedTransportLastKnownCells[transport.ActorID] = transport.Location;
		}

		void RegisterTransportLossSecure(uint lostActorId, CPos lossCell)
		{
			if (lostActorId == 0 || !world.Map.Contains(lossCell))
				return;

			var mergeRadiusSq = Info.TransportLossSecureMergeRadius * Info.TransportLossSecureMergeRadius;
			var nearbyIncidents = transportLossSecureIncidents
				.Where(kv => (kv.Value.Cell - lossCell).LengthSquared <= mergeRadiusSq)
				.OrderBy(kv => (kv.Value.Cell - lossCell).LengthSquared)
				.ThenBy(kv => kv.Key)
				.ToArray();
			var existing = nearbyIncidents
				.Where(kv => !TryGetTransportLossSecureOwner(kv.Key, out _))
				.Select(kv => (Found: true, Id: kv.Key, Incident: kv.Value))
				.FirstOrDefault();

			if (existing.Found)
			{
				var previousEvidenceCell = existing.Incident.LatestLossCell;
				existing.Incident.LatestLossCell = lossCell;
				existing.Incident.LastLossWorldTick = world.WorldTick;
				existing.Incident.LossCount++;
				existing.Incident.LatestLostActorId = lostActorId;
				existing.Incident.ObservedClearSinceWorldTick = -1;
				existing.Incident.NextLifecycleDiagnosticWorldTick = world.WorldTick + Math.Max(Info.ScanInterval, Info.StrategicAssessmentInterval);
				transportLossExclusionRevision++;
				lastPublishedWorldTick = -1;
				LogTransportLossLifecycle(existing.Id, existing.Incident, "ActiveReinforced",
					$"new LST loss {lostActorId} at {lossCell} moves clear-evidence anchor from {previousEvidenceCell} and resets any pending observed-clear evidence",
					GetTransportLossDangerEvidenceCount(existing.Incident.LatestLossCell));
				if (existing.Incident.LossCount == Info.TransportLossSevereLossCount)
					FransBotLog.BotDebug(world,
						"{0}: LST-loss SECURE incident {1} escalates to STRATEGIC TRANSPORT CLOSURE after {2} losses. Logistics exclusion expands from {3} to {4} cells and remains closed until this exact incident is genuinely CLEAR; combat Commanders may still enter normally.",
						player, existing.Id, existing.Incident.LossCount, Info.TransportLossRouteExclusionRadius, GetTransportLossExclusionRadius(existing.Incident.LossCount));
				return;
			}

			var incidentId = NextTransportLossSecureId();
			var incident = new TransportLossSecureIncident(lossCell, world.WorldTick, lostActorId,
				Math.Max(Info.ScanInterval, Info.StrategicAssessmentInterval));
			var nearbyOwnedIncidentId = nearbyIncidents
				.Where(kv => TryGetTransportLossSecureOwner(kv.Key, out _))
				.Select(kv => kv.Key)
				.FirstOrDefault();
			transportLossSecureIncidents[incidentId] = incident;
			transportLossExclusionRevision++;
			lastPublishedWorldTick = -1;
			LogTransportLossLifecycle(incidentId, incident, "Active",
				nearbyOwnedIncidentId != 0
					? $"transport destruction opens a new generation because nearby incident {nearbyOwnedIncidentId} has an immutable accepted SECURE owner; Ground/Air/Sea bid normally"
					: "transport destruction opens domain-neutral SECURE; Ground/Air/Sea bid normally",
				GetTransportLossDangerEvidenceCount(lossCell));
		}

		bool IsTransportLossCellCurrentlyObserved(CPos cell) =>
			world.Map.Contains(cell) && (shroud == null || shroud.Disabled || shroud.IsVisible(cell));

		int GetTransportLossDangerEvidenceCount(CPos lossCell)
		{
			var radiusSquared = Info.SecureRiskAssessmentRadius * Info.SecureRiskAssessmentRadius;
			return combatIntelService.EnemyCombatContacts.Count(contact =>
				contact.EstimatedValue > 0 &&
				(contact.IsDefensiveBuilding || !contact.IsBuilding) &&
				(contact.LastSeenCell - lossCell).LengthSquared <= radiusSquared);
		}

		bool TryGetTransportLossSecureOwner(uint incidentId, out FransActiveMission mission)
		{
			mission = default;
			return commandBidService != null && commandBidService.TryGetActiveMissionForTarget(incidentId, out mission) &&
				mission.MissionType == FransMissionType.Secure;
		}

		string GetTransportLossSecureOwner(uint incidentId) =>
			TryGetTransportLossSecureOwner(incidentId, out var mission)
				? $"{mission.Commander}/{mission.BidderKey}:mission={mission.MissionId}:startedWT={mission.StartedWorldTick}"
				: "None";

		void LogTransportLossLifecycle(uint incidentId, TransportLossSecureIncident incident, string state,
			string reason, int dangerEvidenceCount, bool exclusionActive = true)
		{
			var clearHeldFor = incident.ObservedClearSinceWorldTick < 0
				? 0
				: Math.Max(0, world.WorldTick - incident.ObservedClearSinceWorldTick);
			FransBotLog.BotDebug(world,
				"{0}: [LST-LOSS LIFECYCLE] incident={1} mission={1} sourceActor={2} incidentCell={3} latestLossCell={4} ageWT={5} sinceLastLossWT={6} losses={7} state={8} exclusionActive={9} exclusionRadius={10} owner={11} observedClearWT={12}/{13} dangerEvidence={14} reason={15}.",
				player, incidentId, incident.LatestLostActorId, incident.Cell, incident.LatestLossCell,
				Math.Max(0, world.WorldTick - incident.OpenedWorldTick), Math.Max(0, world.WorldTick - incident.LastLossWorldTick),
				incident.LossCount, state, exclusionActive, GetTransportLossExclusionRadius(incident.LossCount),
				GetTransportLossSecureOwner(incidentId), clearHeldFor, Info.TransportLossObservedClearHoldTicks,
				dangerEvidenceCount, reason ?? "unspecified");
			incident.NextLifecycleDiagnosticWorldTick = world.WorldTick + Math.Max(Info.ScanInterval, Info.StrategicAssessmentInterval);
		}

		void UpdateTransportLossSecureIncidentValidity()
		{
			foreach (var pair in transportLossSecureIncidents.OrderBy(kv => kv.Key).ToArray())
			{
				var incidentId = pair.Key;
				var incident = pair.Value;
				var evidenceCell = incident.LatestLossCell;
				var observed = IsTransportLossCellCurrentlyObserved(evidenceCell);
				var dangerEvidenceCount = GetTransportLossDangerEvidenceCount(evidenceCell);
				if (TryGetTransportLossSecureOwner(incidentId, out var owner))
				{
					var reason = $"accepted {owner.Commander}/{owner.BidderKey} SECURE owns the next CLEAR or release/RETREAT transition; General observed-clear invalidation is ownerless-only";
					if (incident.ObservedClearSinceWorldTick >= 0)
					{
						incident.ObservedClearSinceWorldTick = -1;
						LogTransportLossLifecycle(incidentId, incident, "ActiveCommanderOwned",
							$"observed-clear evidence reset: {reason}", dangerEvidenceCount);
					}
					else if (world.WorldTick >= incident.NextLifecycleDiagnosticWorldTick)
						LogTransportLossLifecycle(incidentId, incident, "ActiveCommanderOwned", reason, dangerEvidenceCount);
					continue;
				}

				if (!observed || dangerEvidenceCount > 0)
				{
					var state = dangerEvidenceCount > 0 ? "ActiveDangerEvidence" : "ActiveUnobserved";
					var reason = !observed && dangerEvidenceCount > 0
						? "latest loss evidence cell is not currently visible and nearby CombatIntel danger evidence remains"
						: !observed
							? "latest loss evidence cell is not currently visible; failed/no-bid SECURE execution is not clear evidence"
							: "nearby authoritative CombatIntel danger evidence remains";
					if (incident.ObservedClearSinceWorldTick >= 0)
					{
						incident.ObservedClearSinceWorldTick = -1;
						LogTransportLossLifecycle(incidentId, incident, state, $"observed-clear evidence reset: {reason}", dangerEvidenceCount);
					}
					else if (world.WorldTick >= incident.NextLifecycleDiagnosticWorldTick)
						LogTransportLossLifecycle(incidentId, incident, state, reason, dangerEvidenceCount);
					continue;
				}

				if (incident.ObservedClearSinceWorldTick < 0)
				{
					incident.ObservedClearSinceWorldTick = world.WorldTick;
					LogTransportLossLifecycle(incidentId, incident, "ObservedClearPending",
						"latest loss evidence cell is directly visible, no Commander owns SECURE, and no nearby CombatIntel danger evidence remains; continuous clear-evidence hold begins",
						dangerEvidenceCount);
					continue;
				}

				if (world.WorldTick - incident.ObservedClearSinceWorldTick >= Info.TransportLossObservedClearHoldTicks)
				{
					CloseTransportLossSecureIncident(incidentId, null, evidenceCell, "InvalidatedObservedClear",
						"ownerless continuous direct observation of the latest loss evidence plus absence of nearby authoritative CombatIntel danger evidence invalidated the old loss obligation",
						dangerEvidenceCount);
					continue;
				}

				if (world.WorldTick >= incident.NextLifecycleDiagnosticWorldTick)
					LogTransportLossLifecycle(incidentId, incident, "ObservedClearPending",
						"continuous observed-clear evidence has not yet reached the configured hold", dangerEvidenceCount);
			}
		}

		bool CloseTransportLossSecureIncident(uint incidentId, FransCommanderKind? commander, CPos clearCell,
			string transition, string reason, int dangerEvidenceCount)
		{
			if (!transportLossSecureIncidents.Remove(incidentId, out var incident))
				return false;

			transportLossExclusionRevision++;
			activeSecureTargets.Remove(incidentId);
			activeSecurePublishedWorldTick.Remove(incidentId);
			secureTargetCooldownUntil.Remove(incidentId);
			domainSecureClearWorldTick.Remove((incidentId, FransCommanderKind.Air));
			domainSecureClearWorldTick.Remove((incidentId, FransCommanderKind.Sea));
			domainSecureClearCells.Remove((incidentId, FransCommanderKind.Air));
			domainSecureClearCells.Remove((incidentId, FransCommanderKind.Sea));
			lastPublishedWorldTick = -1;
			var authority = commander.HasValue ? $"{commander.Value}CommanderClear" : "GeneralObservedClearEvidence";
			LogTransportLossLifecycle(incidentId, incident, transition,
				$"authority={authority}; clearCell={clearCell}; {reason ?? "loss area clear"}; exclusion removed without Ground ANCHOR/foothold",
				dangerEvidenceCount, exclusionActive: false);
			return true;
		}

		void CleanupSeaTransportBeachSecureRequests()
		{
			foreach (var requestId in seaTransportBeachSecureRequests
				.Where(kv => kv.Value.ValidThroughWorldTick < world.WorldTick)
				.Select(kv => kv.Key).ToArray())
			{
				seaTransportBeachSecureRequests.Remove(requestId);
				domainSecureClearWorldTick.Remove((requestId, FransCommanderKind.Sea));
			}
		}

		void AppendTransportLossSecureMissions()
		{
			foreach (var incident in transportLossSecureIncidents.OrderByDescending(kv => kv.Value.LastLossWorldTick).ThenBy(kv => kv.Key))
			{
				if (currentMissions.Count >= Info.MaximumPublishedMissions)
					break;

				var siteIntel = BuildSiteIntel(incident.Value.LatestLossCell, Info.SecureRiskAssessmentRadius, Info.StrategicIntelAgingAgeTicks);
				PublishUniqueMission(new FransMission(null, incident.Key, TransportLossSecureTargetType, player,
					incident.Value.LatestLossCell, false, false, siteIntel, FransMissionType.Secure,
					Info.SecureStrategicPriority, world.WorldTick, incident.Key));
			}
		}

		void AppendSeaTransportBeachSecureMissions()
		{
			foreach (var request in seaTransportBeachSecureRequests.OrderBy(kv => kv.Key))
			{
				if (currentMissions.Count >= Info.MaximumPublishedMissions)
					break;
				var siteIntel = BuildSiteIntel(request.Value.Cell, Info.SecureRiskAssessmentRadius, Info.StrategicIntelAgingAgeTicks);
				PublishUniqueMission(new FransMission(null, request.Key, SeaTransportBeachSecureTargetType, player,
					request.Value.Cell, false, false, siteIntel, FransMissionType.Secure,
					Info.TransportBeachSecureStrategicPriority, world.WorldTick));
			}
		}

		FransSiteIntel BuildSiteIntel(CPos center, int radiusCells, int maximumContactAgeTicks, Actor visiblePrimary = null)
		{
			combatIntelService.EnsureCurrentSnapshot();
			var radiusSq = Math.Max(0, radiusCells) * Math.Max(0, radiusCells);
			var actors = new Dictionary<uint, FransSiteIntelActor>();

			foreach (var contact in combatIntelService.EnemyCombatContacts.OrderBy(c => c.ActorId))
			{
				if ((contact.LastSeenCell - center).LengthSquared > radiusSq ||
					(!contact.IsBuilding && world.WorldTick - contact.LastSeenWorldTick > maximumContactAgeTicks))
					continue;

				var live = world.GetActorById(contact.ActorId);
				var visible = live != null && IsValidVisibleEnemy(live);
				var hp = visible ? Math.Max(1, live.TraitOrDefault<Health>()?.HP ?? 1) : 0;
				var cell = visible ? live.Location : contact.LastSeenCell;
				actors[contact.ActorId] = new FransSiteIntelActor(
					contact.ActorId, contact.ActorType, contact.Owner, cell, contact.IsBuilding,
					contact.IsDefensiveBuilding, contact.IsDefensiveBuilding || !contact.IsBuilding,
					hp, Math.Max(0, contact.EstimatedValue));
			}

			if (visiblePrimary != null && IsValidVisibleEnemy(visiblePrimary))
			{
				var building = visiblePrimary.Info.HasTraitInfo<BuildingInfo>();
				var defensive = building && combatIntelService.IsCombatThreat(visiblePrimary);
				actors[visiblePrimary.ActorID] = new FransSiteIntelActor(
					visiblePrimary.ActorID, visiblePrimary.Info.Name, visiblePrimary.Owner, visiblePrimary.Location,
					building, defensive, combatIntelService.IsCombatThreat(visiblePrimary),
					Math.Max(1, visiblePrimary.TraitOrDefault<Health>()?.HP ?? 1), Math.Max(0, GetTargetValue(visiblePrimary)));
			}

			return new FransSiteIntel(center, actors.Values.OrderBy(a => a.ActorId).ToArray());
		}

		public bool TryGetLatestGroundAnchor(out CPos anchorPoint)
		{
			RefreshGroundForwardAnchor();
			if (hasLatestGroundAnchor)
			{
				anchorPoint = latestGroundAnchorPoint;
				return true;
			}

			anchorPoint = default;
			return false;
		}

		bool IsGroundForwardRelevantAnchor(CPos anchorPoint)
		{
			var radiusSquared = Info.SecureRiskAssessmentRadius * Info.SecureRiskAssessmentRadius;
			foreach (var contact in combatIntelService.EnemyCombatContacts)
			{
				if (contact.EstimatedValue <= 0 || (contact.LastSeenCell - anchorPoint).LengthSquared > radiusSquared)
					continue;

				// Territorial SECURE and forward army staging are deliberately separate. A remembered
				// enemy building is a legitimate front objective; mobile contacts count only when the
				// Ground Commander classifies their actor type as Ground combat. Air/Sea contacts never
				// drag the Ground army onto an otherwise empty island.
				if (contact.IsBuilding || (groundCommanderService != null && groundCommanderService.IsGroundCombatActorType(contact.ActorType)))
					return true;
			}

			return false;
		}

		void RefreshGroundForwardAnchor(bool force = false)
		{
			combatIntelService.EnsureCurrentSnapshot();
			if (!force && lastGroundForwardAnchorIntelSnapshotTick == combatIntelService.SnapshotWorldTick)
				return;
			lastGroundForwardAnchorIntelSnapshotTick = combatIntelService.SnapshotWorldTick;

			var previousHasAnchor = hasLatestGroundAnchor;
			var previousTargetId = latestGroundAnchorTargetId;
			var candidate = establishedSecureAnchorPoints
				.Where(kv => IsGroundForwardRelevantAnchor(kv.Value))
				.OrderByDescending(kv => secureAnchorEstablishedWorldTick.TryGetValue(kv.Key, out var tick) ? tick : -1)
				.ThenByDescending(kv => kv.Key)
				.Select(kv => (Found: true, TargetId: kv.Key, Point: kv.Value))
				.FirstOrDefault();

			if (candidate.Found)
			{
				hasLatestGroundAnchor = true;
				latestGroundAnchorTargetId = candidate.TargetId;
				latestGroundAnchorPoint = candidate.Point;
				if (!previousHasAnchor || previousTargetId != candidate.TargetId)
					FransBotLog.BotDebug(world,
						"{0}: Ground FORWARD ANCHOR selects territorial SECURE {1} at {2}; fair CombatIntel knows an enemy building or Ground-combat contact within {3} cells. Idle/rebuilt Ground may stage here while that front relevance remains.",
						player, candidate.TargetId, candidate.Point, Info.SecureRiskAssessmentRadius);
				return;
			}

			hasLatestGroundAnchor = false;
			latestGroundAnchorTargetId = 0;
			latestGroundAnchorPoint = default;
			if (previousHasAnchor)
				FransBotLog.BotDebug(world,
					"{0}: Ground FORWARD ANCHOR releases territorial SECURE {1}; no fair enemy-building/Ground-combat intel remains within {2} cells of any secured territory. Territorial SECURE/MCV permission remains intact, but idle Ground no longer masses there.",
					player, previousTargetId, Info.SecureRiskAssessmentRadius);
		}

		bool TryGetNextSecurePoint(out CPos securePoint)
		{
			foreach (var pair in activeSecureTargets
				.OrderBy(kv => activeSecurePublishedWorldTick.TryGetValue(kv.Key, out var tick) ? tick : int.MaxValue)
				.ThenBy(kv => kv.Key))
			{
				securePoint = pair.Value;
				return true;
			}

			securePoint = default;
			return false;
		}

		int GetRaidInterferenceValue(uint targetActorId)
		{
			if (!recentHostileActionWorldTick.TryGetValue(targetActorId, out var hostileActionTick))
				return 0;
			var age = Math.Max(0, world.WorldTick - hostileActionTick);
			if (age >= Info.RaidInterferenceMemoryTicks)
			{
				recentHostileActionWorldTick.Remove(targetActorId);
				return 0;
			}

			var remaining = Info.RaidInterferenceMemoryTicks - age;
			return (int)Math.Clamp(((long)Info.RaidInterferencePriorityBonus * remaining + Info.RaidInterferenceMemoryTicks - 1L) /
				Info.RaidInterferenceMemoryTicks, 0L, Info.RaidInterferencePriorityBonus);
		}

		int GetRaidMissionPriority(uint targetActorId, CPos targetCell)
		{
			var secureProximityValue = 0;
			if (TryGetNextSecurePoint(out var securePoint))
			{
				var radiusSq = Info.RaidNextSecurePriorityRadius * Info.RaidNextSecurePriorityRadius;
				if ((targetCell - securePoint).LengthSquared <= radiusSq)
					secureProximityValue = Info.RaidNextSecurePriorityBonus;
			}

			return Info.RaidStrategicPriority + secureProximityValue + GetRaidInterferenceValue(targetActorId);
		}

		void AppendRaidMissions()
		{
			if (Info.MaximumActiveRaidMissions <= 0)
				return;

			combatIntelService.EnsureCurrentSnapshot();
			foreach (var id in raidTargetCooldownUntil.Keys.Where(id => world.WorldTick >= raidTargetCooldownUntil[id]).ToArray())
				raidTargetCooldownUntil.Remove(id);
			foreach (var id in recentHostileActionWorldTick.Keys
				.Where(id => world.WorldTick - recentHostileActionWorldTick[id] >= Info.RaidInterferenceMemoryTicks).ToArray())
				recentHostileActionWorldTick.Remove(id);

			foreach (var id in activeRaidTargets.Keys.ToArray())
			{
				var target = world.GetActorById(id);
				FransActiveMission activeMission = default;
				var hasActiveCommander = commandBidService != null &&
					commandBidService.TryGetActiveMissionForTarget(id, out activeMission) &&
					activeMission.MissionType == FransMissionType.Raid;

				if (hasActiveCommander)
				{
					var recheckTick = activeMission.StartedWorldTick + Math.Max(0, activeMission.EstimatedEtaTicks) + Info.RaidPostEtaRecheckMarginTicks;
					if (world.WorldTick < recheckTick)
						continue;

					if (IsValidVisibleEnemy(target) && IsRaidCandidate(target, out _))
						continue;

					// Once ETA + strike margin has elapsed, release the General board reservation if the
					// target is no longer visible/eligible. The already-winning Commander owns its immutable
					// MISSION and performs bounded local RECON; the remembered-building publication window is
					// only for yet-unassigned Sea bids and is no longer needed after assignment.
					activeRaidTargets.Remove(id);
					activeRaidSnapshots.Remove(id);
					FransBotLog.BotDebug(world,
						"{0}: GENERAL releases RAID board target {1} after Commander ETA recheck WT {2}: target is no longer currently visible/eligible. The active Commander owns local lost-target RECON/return; General drops the board snapshot now.",
						player, id, recheckTick);
					continue;
				}

				if (!IsValidVisibleEnemy(target) || !IsRaidCandidate(target, out _))
				{
					if (activeRaidSnapshots.TryGetValue(id, out var remembered) && remembered.IsBuilding &&
						!shroud.IsVisible(remembered.LastVisibleTargetCell) &&
						world.WorldTick - remembered.PublishedWorldTick <= Info.RaidRememberedBuildingLifetimeTicks)
					{
						// Keep only the frozen fair snapshot. Hidden live actor state is never read.
						continue;
					}

					activeRaidTargets.Remove(id);
					activeRaidSnapshots.Remove(id);
					FransBotLog.BotDebug(world,
						"{0}: GENERAL releases unassigned RAID board target {1}: target is no longer visible/eligible and no fresh remembered stationary-building snapshot remains.",
						player, id);
					continue;
				}

				if (world.WorldTick - activeRaidTargets[id] > Info.RaidNoBidBackoffTicks)
				{
					activeRaidTargets.Remove(id);
					activeRaidSnapshots.Remove(id);
					raidTargetCooldownUntil[id] = world.WorldTick + Info.RaidNoBidBackoffTicks;
					FransBotLog.BotDebug(world,
						"{0}: GENERAL backs off visible RAID target {1} after {2} WT with no winning Commander MISSION; short publication backoff through WT {3}.",
						player, id, Info.RaidNoBidBackoffTicks, raidTargetCooldownUntil[id]);
				}
			}

			// During the deterministic opening the army stays home: publishing RAID missions
			// sends the only defenders across the map while the build chain is at its most
			// fragile. Local FIGHT authorization still runs, so the army defends reactively.
			var raidsSuppressedByOpening = baseBuilderService != null && !baseBuilderService.OpeningComplete;
			while (!raidsSuppressedByOpening && activeRaidTargets.Count < Info.MaximumActiveRaidMissions)
			{
				var chosen = combatIntelService.VisibleEnemies
					.Where(IsValidVisibleEnemy)
					.Where(t => !activeRaidTargets.ContainsKey(t.ActorID))
					.Where(t => commandBidService == null || !commandBidService.TryGetActiveMissionForTarget(t.ActorID, out var active) || active.MissionType != FransMissionType.Raid)
					.Where(t => !raidTargetCooldownUntil.TryGetValue(t.ActorID, out var until) || world.WorldTick >= until)
					.Select(t =>
					{
						var ok = IsRaidCandidate(t, out var freshSamples);
						var hp = t.TraitOrDefault<Health>()?.HP ?? int.MaxValue;
						var priority = GetRaidMissionPriority(t.ActorID, t.Location);
						return (Target: t, Ok: ok, FreshSamples: freshSamples, Hp: hp, Value: GetTargetValue(t), Priority: priority);
					})
					.Where(x => x.Ok)
					// Target TYPE ranking still belongs to Commanders. General moves RAID opportunities
					// forward only for strategic SECURE proximity and recent observed operational interference.
					.OrderByDescending(x => x.Priority)
					.ThenBy(x => x.Target.ActorID)
					.FirstOrDefault();

				if (chosen.Target == null)
					break;

				activeRaidTargets[chosen.Target.ActorID] = world.WorldTick;
				var rawIntel = BuildSiteIntel(chosen.Target.Location, Info.RaidSiteIntelRadius, Info.RaidIntelFreshTicks, chosen.Target);
				activeRaidSnapshots[chosen.Target.ActorID] = new FransMission(chosen.Target, chosen.Target.ActorID, chosen.Target.Info.Name, chosen.Target.Owner, chosen.Target.Location, false,
					chosen.Target.Info.HasTraitInfo<BuildingInfo>(), rawIntel, FransMissionType.Raid, GetRaidMissionPriority(chosen.Target.ActorID, chosen.Target.Location), world.WorldTick);
				FransBotLog.BotDebug(world,
					"{0}: GENERAL publishes MISSION RAID target {1} {2} at {3}: HP snapshot {4}, strategic value {5}, fresh site samples {6}/9, priority {7}; raw SiteIntel [{8}]. General utility may include SECURE proximity and decaying recent-hostile-action value; Commander doctrine still ranks target types.",
					player, chosen.Target.Info.Name, chosen.Target.ActorID, chosen.Target.Location, chosen.Hp, chosen.Value,
					chosen.FreshSamples, chosen.Priority, FormatSiteIntelForLog(rawIntel));
			}

			// Fog-honest remembered strikes: stationary buildings cannot move, so a building
			// observed once stays a fair RAID objective until its snapshot expires. This seeds
			// remembered missions for remembered contacts the live scan never got a fresh
			// visibility window to publish; the republish loop below then emits them while
			// the snapshot remains inside RaidRememberedBuildingLifetimeTicks.
			if (!raidsSuppressedByOpening && Info.RaidPublishRememberedBuildings &&
				activeRaidTargets.Count < Info.MaximumActiveRaidMissions)
			{
				foreach (var contact in combatIntelService.EnemyCombatContacts
					.Where(c => c.IsBuilding && !c.IsDefensiveBuilding && c.Owner != null &&
						PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)) &&
						world.WorldTick - c.LastSeenWorldTick <= Info.RaidRememberedBuildingLifetimeTicks &&
						world.WorldTick - c.LastSeenWorldTick >= 0)
					.OrderBy(c => c.ActorId))
				{
					if (activeRaidTargets.Count >= Info.MaximumActiveRaidMissions)
						break;
					if (activeRaidTargets.ContainsKey(contact.ActorId))
						continue;
					if (shroud.IsVisible(contact.LastSeenCell))
						continue; // live path owns visible targets
					if (raidTargetCooldownUntil.TryGetValue(contact.ActorId, out var rememberedUntil) &&
						world.WorldTick < rememberedUntil)
						continue;
					if (commandBidService != null &&
						commandBidService.TryGetActiveMissionForTarget(contact.ActorId, out var activeMission) &&
						activeMission.MissionType == FransMissionType.Raid)
						continue;

					var rememberedIntel = BuildSiteIntel(contact.LastSeenCell, Info.RaidSiteIntelRadius, Info.RaidIntelFreshTicks);
					activeRaidTargets[contact.ActorId] = world.WorldTick;
					activeRaidSnapshots[contact.ActorId] = new FransMission(null, contact.ActorId, contact.ActorType, contact.Owner,
						contact.LastSeenCell, true, true, rememberedIntel, FransMissionType.Raid,
						GetRaidMissionPriority(contact.ActorId, contact.LastSeenCell), world.WorldTick);
					FransBotLog.BotDebug(world,
						"{0}: GENERAL seeds REMEMBERED BUILDING RAID objective {1} {2} at remembered cell {3}: last seen {4} WT ago, republish loop will emit it within the {5} WT remembered lifetime.",
						player, contact.ActorType, contact.ActorId, contact.LastSeenCell,
						world.WorldTick - contact.LastSeenWorldTick, Info.RaidRememberedBuildingLifetimeTicks);
				}
			}

			foreach (var pair in activeRaidTargets.OrderBy(p => p.Key))
			{
				if (currentMissions.Count >= Info.MaximumPublishedMissions)
					break;
				if (commandBidService != null && commandBidService.TryGetActiveMissionForTarget(pair.Key, out var active) && active.MissionType == FransMissionType.Raid)
					continue;
				var target = world.GetActorById(pair.Key);
				if (IsValidVisibleEnemy(target) && IsRaidCandidate(target, out _))
				{
					var liveMission = new FransMission(target, target.ActorID, target.Info.Name, target.Owner, target.Location, false,
						target.Info.HasTraitInfo<BuildingInfo>(), BuildSiteIntel(target.Location, Info.RaidSiteIntelRadius, Info.RaidIntelFreshTicks, target),
						FransMissionType.Raid, GetRaidMissionPriority(target.ActorID, target.Location), world.WorldTick);
					activeRaidSnapshots[target.ActorID] = liveMission;
					PublishUniqueMission(liveMission);
					continue;
				}

				if (activeRaidSnapshots.TryGetValue(pair.Key, out var snapshot) && snapshot.IsBuilding &&
					!shroud.IsVisible(snapshot.LastVisibleTargetCell) &&
					world.WorldTick - snapshot.PublishedWorldTick <= Info.RaidRememberedBuildingLifetimeTicks)
				{
					var rememberedMission = snapshot with { Target = null, IsRememberedIntel = true };
					PublishUniqueMission(rememberedMission);
				}
			}
		}

		static string FormatSiteIntelForLog(FransSiteIntel intel)
		{
			var actors = intel.Actors ?? Array.Empty<FransSiteIntelActor>();
			if (actors.Length == 0)
				return "none";
			return string.Join(", ", actors
				.OrderBy(a => a.ActorId)
				.Take(12)
				.Select(a => $"{a.ActorType}#{a.ActorId}@{a.Cell}")) + (actors.Length > 12 ? $", +{actors.Length - 12} more" : string.Empty);
		}

		bool IsRaidCandidate(Actor target, out int freshSamples)
		{
			freshSamples = 0;
			if (!IsValidVisibleEnemy(target) || IsDefenseTarget(target) ||
				!(target.Info.HasTraitInfo<BuildingInfo>() || Info.RaidEligibleMobileTargetTypes.Contains(target.Info.Name)))
				return false;
			var health = target.TraitOrDefault<Health>();
			if (health == null || health.HP <= 0)
				return false;

			freshSamples = CountRaidFreshAreaSamples(target.Location);
			// General applies one neutral freshness gate to every RAID target. Target-type
			// prioritization belongs exclusively to the Commander bid layer.
			return freshSamples >= Info.RaidMinimumFreshAreaSamples;
		}

		int CountRaidFreshAreaSamples(CPos center)
		{
			if (shroud == null || shroud.Disabled)
				return 9;
			var r = Info.RaidSiteIntelRadius;
			var d = Math.Max(1, r * 3 / 4);
			var samples = new[]
			{
				center, new CPos(center.X + r, center.Y), new CPos(center.X - r, center.Y),
				new CPos(center.X, center.Y + r), new CPos(center.X, center.Y - r),
				new CPos(center.X + d, center.Y + d), new CPos(center.X + d, center.Y - d),
				new CPos(center.X - d, center.Y + d), new CPos(center.X - d, center.Y - d)
			};
			return samples.Count(c =>
			{
				if (!world.Map.Contains(c))
					return false;
				if (shroud.IsVisible(c))
					return true;
				return strategicMapService != null && strategicMapService.TryGetSector(c, out var sector) &&
					sector.LastObservedWorldTick >= 0 && world.WorldTick - sector.LastObservedWorldTick <= Info.RaidIntelFreshTicks;
			});
		}

		public void ReportRaidRetreat(uint raidTargetActorId, string reason)
		{
			if (raidTargetActorId == 0)
				return;
			activeRaidTargets.Remove(raidTargetActorId);
			activeRaidSnapshots.Remove(raidTargetActorId);
			raidTargetCooldownUntil[raidTargetActorId] = world.WorldTick + Info.RaidRetreatCooldownTicks;
			FransBotLog.BotDebug(world,
				"{0}: GENERAL receives RAID RETREAT for target {1}: {2}; retry cooldown through WT {3}. Lost visibility/normal target disappearance never uses this cooldown.",
				player, raidTargetActorId, reason ?? "Commander RETREAT", raidTargetCooldownUntil[raidTargetActorId]);
			lastPublishedWorldTick = -1;
		}

		void UpdateMineClusterObservationMemory()
		{
			if (mineClusterService == null)
				return;

			var liveKeys = new HashSet<uint>();
			foreach (var cluster in mineClusterService.VisibleClusters.Where(IsLiveMineCluster))
			{
				var key = GetMineClusterKey(cluster);
				if (key == uint.MaxValue)
					continue;
				liveKeys.Add(key);
				if (IsMineClusterCurrentlyObserved(cluster))
					mineClusterLastObservedTick[key] = world.WorldTick;
			}

			foreach (var stale in mineClusterLastObservedTick.Keys.Where(k => !liveKeys.Contains(k)).ToArray())
				mineClusterLastObservedTick.Remove(stale);
			foreach (var stale in reconTargetCooldownUntil.Keys.Where(k => IsSpawnProbeKey(k) ? world.WorldTick >= reconTargetCooldownUntil[k] : !liveKeys.Contains(k) || world.WorldTick >= reconTargetCooldownUntil[k]).ToArray())
				reconTargetCooldownUntil.Remove(stale);

			foreach (var stale in activeReconTargets.Keys.Where(k => !IsSpawnProbeKey(k) && !liveKeys.Contains(k)).ToArray())
			{
				activeReconTargets.Remove(stale);
				activeReconWithoutMissionSinceTick.Remove(stale);
				expansionReconMissionTargets.Remove(stale);
			}

			UpdateSpawnProbeObservationMemory();
		}

		static bool IsSpawnProbeKey(uint key) => key >= SpawnProbeKeyBase && key != uint.MaxValue;

		void EnsureSpawnProbesSeeded()
		{
			if (spawnProbesSeeded)
				return;
			spawnProbesSeeded = true;
			if (!Info.EnemySpawnReconEnabled)
				return;

			var home = player.HomeLocation;
			var exclusionSq = Info.EnemySpawnReconOwnHomeExclusionRadius * Info.EnemySpawnReconOwnHomeExclusionRadius;
			uint index = 0;
			foreach (var definition in world.Map.ActorDefinitions)
			{
				if (definition.Value.Value != "mpspawn")
					continue;
				var cell = new ActorReference(definition.Key, definition.Value).GetValue<LocationInit, CPos>();
				if (!world.Map.Contains(cell) || (cell - home).LengthSquared <= exclusionSq)
					continue;
				if (SpawnProbeKeyBase + index == uint.MaxValue)
					break;
				spawnProbeTargets[SpawnProbeKeyBase + index++] = cell;
			}

			if (spawnProbeTargets.Count > 0)
				FransBotLog.BotDebug(world,
					"{0}: GENERAL seeds {1} enemy-spawn RECON probe(s) from public map mpspawn data at [{2}]; own spawn {3} excluded. A fog-honest bot cannot find the enemy base from ore patrols alone.",
					player, spawnProbeTargets.Count, string.Join(", ", spawnProbeTargets.Values), home);
		}

		void UpdateSpawnProbeObservationMemory()
		{
			if (spawnProbeTargets.Count == 0)
				return;

			foreach (var pair in spawnProbeTargets)
			{
				var resolvedByIntel = IsSpawnProbeResolvedByIntel(pair.Value);
				if (IsSpawnProbeCurrentlyObserved(pair.Value) || resolvedByIntel)
					spawnProbeLastObservedTick[pair.Key] = world.WorldTick;

				// A spawn probe is a one-shot question ("is the enemy here?"), not a perpetual patrol:
				// once the cell area is actually seen, retire the mission so its Commander capacity frees
				// for combat work. The staleness gate republishes it later if intel ages out.
				if (activeReconTargets.ContainsKey(pair.Key) && IsSpawnProbeCurrentlyObserved(pair.Value))
					CompleteReconMission(pair.Key, "enemy spawn probe area observed; retiring one-shot probe");
				else if (activeReconTargets.ContainsKey(pair.Key) && resolvedByIntel)
					CompleteReconMission(pair.Key, "known enemy structures near spawn probe; retiring resolved probe");
			}
		}

		bool IsSpawnProbeCurrentlyObserved(CPos cell)
		{
			if (shroud == null || shroud.Disabled)
				return true;

			var radius = Info.EnemySpawnReconObservationRadius;
			for (var dy = -radius; dy <= radius; dy++)
				for (var dx = -radius; dx <= radius; dx++)
				{
					var check = new CPos(cell.X + dx, cell.Y + dy);
					if (world.Map.Contains(check) && shroud.IsVisible(check))
						return true;
				}

			return false;
		}

		bool IsSpawnProbeResolvedByIntel(CPos cell)
		{
			if (strategicMapService == null)
				return false;

			var radiusSq = (long)Info.EnemySpawnReconResolvedRadius * Info.EnemySpawnReconResolvedRadius;
			foreach (var structure in strategicMapService.KnownEnemyStructures)
				if ((structure.LastKnownLocation - cell).LengthSquared <= radiusSq)
					return true;

			return false;
		}

		bool IsMineClusterCurrentlyObserved(FransMineCluster cluster)
		{
			if (cluster == null)
				return false;
			if (shroud == null || shroud.Disabled)
				return true;
			return cluster.Mines.Any(m => m != null && m.IsInWorld && !m.IsDead &&
				world.Map.Contains(m.Location) && shroud.IsVisible(m.Location));
		}

		bool IsExpansionBlockedSecureCandidate(CPos cell, IReadOnlyList<CPos> blockedObjectives)
		{
			if (blockedObjectives == null || blockedObjectives.Count == 0)
				return false;

			var radiusSq = Info.ExpansionBlockedSecureRadius * Info.ExpansionBlockedSecureRadius;
			return blockedObjectives.Any(c => world.Map.Contains(c) && (c - cell).LengthSquared <= radiusSq);
		}

		CPos? FindExpansionBlockedObjectiveForCluster(FransMineCluster cluster, IReadOnlyList<CPos> blockedObjectives)
		{
			if (cluster == null || blockedObjectives == null || blockedObjectives.Count == 0)
				return null;

			var liveMines = cluster.Mines
				.Where(m => m != null && m.IsInWorld && !m.IsDead && world.Map.Contains(m.Location))
				.Select(m => m.Location)
				.ToArray();
			if (liveMines.Length == 0)
				return null;

			var radiusSq = Info.ExpansionBlockedSecureRadius * Info.ExpansionBlockedSecureRadius;
			return blockedObjectives
				.Where(c => world.Map.Contains(c) && liveMines.Any(m => (m - c).LengthSquared <= radiusSq))
				.OrderBy(c => (c - cluster.Center).LengthSquared)
				.ThenBy(c => c.Y).ThenBy(c => c.X)
				.Select(c => (CPos?)c)
				.FirstOrDefault();
		}

		void AppendSecureMission()
		{
			secureReconRequiredTargets.Clear();
			if (Info.MaximumActiveSecureMissions <= 0)
				return;

			combatIntelService.EnsureCurrentSnapshot();
			var clusters = mineClusterService != null
				? mineClusterService.VisibleClusters.Where(IsLiveMineCluster).ToArray()
				: Array.Empty<FransMineCluster>();
			var knownEnemyFacts = GetKnownEnemyConstructionYards();
			var expansionBlockedObjectives = expansionStateService != null
				? expansionStateService.SecureRequiredExpansionObjectives
				: Array.Empty<CPos>();
			if (clusters.Length == 0 && knownEnemyFacts.Length == 0)
				return;

			var byKey = clusters.ToDictionary(GetMineClusterKey);
			var knownFactsById = knownEnemyFacts.ToDictionary(f => f.ActorId);
			var factClusterAssignments = BuildConstructionYardClusterAssignments(knownEnemyFacts, clusters);
			var factsByCluster = factClusterAssignments
				.GroupBy(kv => kv.Value)
				.ToDictionary(g => g.Key, g => g.Select(kv => knownFactsById[kv.Key]).OrderBy(f => f.ActorId).ToArray());
			var useOreNodeOwnership = oreEconomyService != null && oreEconomyService.VisibleMineCount > 0;
			var unpairedOreMineLocations = useOreNodeOwnership ? oreEconomyService.UnpairedMineLocations.ToHashSet() : null;
			var alliedClaimStructures = GetAlliedSecureClaimStructures();
			RefreshPendingSecureFootholds(clusters, alliedClaimStructures);

			// Maintain every independent SECURE slot. MineCluster targets keep their resource key.
			// A standalone enemy FACT uses the FACT ActorID as a stable strategic territory key.
			foreach (var key in activeSecureTargets.Keys.OrderBy(k => k).ToArray())
			{
				var isMineCluster = byKey.TryGetValue(key, out var activeCluster);
				var isStandaloneFact = standaloneFactSecureTargets.Contains(key);
				if (!isMineCluster && !isStandaloneFact)
				{
					ReleaseActiveSecureToCooldown(key, "strategic SECURE target disappeared");
					continue;
				}

				if (pioneerExpansionPrioritySecureTargets.Contains(key))
				{
					var stillCurrentPioneerUnblock = isMineCluster
						? FindExpansionBlockedObjectiveForCluster(activeCluster, expansionBlockedObjectives).HasValue
						: IsExpansionBlockedSecureCandidate(activeSecureTargets[key], expansionBlockedObjectives);
					if (!stillCurrentPioneerUnblock)
					{
						if (commandBidService != null && commandBidService.TryGetActiveMissionForTarget(key, out var staleExpansionSecure) &&
							staleExpansionSecure.MissionType == FransMissionType.Secure)
							commandBidService.ReleaseMission(staleExpansionSecure.Commander, staleExpansionSecure.BidderKey,
								"PIONEER single-objective changed/abandoned; expansion-unblock SECURE ownership is no longer current");

						ReleaseActiveSecureToCooldown(key,
							"PIONEER single-objective changed/abandoned; stale expansion-unblock SECURE released", Info.SecureNoBidBackoffTicks);
						continue;
					}
				}

				FransActiveMission secureMission = default;
				var hasActiveCommander = commandBidService != null &&
					commandBidService.TryGetActiveMissionForTarget(key, out secureMission) &&
					secureMission.MissionType == FransMissionType.Secure;

				if (hasActiveCommander)
				{
					// CLEAR is Commander-domain work. Ground, Air and Sea each validate the area
					// with their own movement/attack capabilities and call EstablishSecureAnchor
					// themselves. General must never infer CLEAR from a generic visible-actor scan.
					activeSecureTargets[key] = secureMission.LastVisibleTargetCell;
					continue;
				}

				CPos objectiveCell;
				string targetType;
				Player targetOwner;
				if (isMineCluster)
				{
					var mergedFacts = factsByCluster.TryGetValue(key, out var foundFacts)
						? foundFacts
						: Array.Empty<FransCombatIntelContact>();
					var availableNodes = CountSecureAvailableOreMineNodes(activeCluster,
						useOreNodeOwnership ? unpairedOreMineLocations : null, alliedClaimStructures);
					if (availableNodes + mergedFacts.Length <= 0)
					{
						ReleaseActiveSecureToCooldown(key, "no available ore-mine nodes or remembered enemy Construction Yards remain in the strategic area");
						continue;
					}

					var blockedObjective = FindExpansionBlockedObjectiveForCluster(activeCluster, expansionBlockedObjectives);
					objectiveCell = mergedFacts.Length == 0 && blockedObjective.HasValue
						? blockedObjective.Value
						: SelectSecureObjectiveCell(activeCluster,
							useOreNodeOwnership ? unpairedOreMineLocations : null, alliedClaimStructures, mergedFacts);
					targetType = "minecluster";
					targetOwner = activeCluster.Representative.Owner;
				}
				else
				{
					if (!knownFactsById.TryGetValue(key, out var fact))
					{
						ReleaseActiveSecureToCooldown(key, "remembered enemy Construction Yard was directly disproved before any Commander accepted SECURE");
						standaloneFactSecureTargets.Remove(key);
						continue;
					}
					objectiveCell = fact.LastSeenCell;
					targetType = "fact";
					targetOwner = fact.Owner;
				}

				activeSecureTargets[key] = objectiveCell;
				if (!activeSecurePublishedWorldTick.TryGetValue(key, out var publishedTick))
				{
					publishedTick = world.WorldTick;
					activeSecurePublishedWorldTick[key] = publishedTick;
				}
				// Expansion-unblock SECURE is pinned while the SINGLE PIONEER objective still owns it.
				// Ordinary SECURE keeps the bounded no-bid backoff, but a PIONEER SECURE must not
				// churn off the broker board merely because no Commander could accept it inside one
				// short window. PIONEER itself owns the longer objective lifetime and releases this
				// pin when the objective changes/aborts.
				if (pioneerExpansionPrioritySecureTargets.Contains(key) ||
					world.WorldTick - publishedTick <= Info.SecureNoBidBackoffTicks)
					PublishSecureMission(key, targetType, targetOwner, objectiveCell);
				else
					ReleaseActiveSecureToCooldown(key, "no winning Commander MISSION inside SECURE no-bid window", Info.SecureNoBidBackoffTicks);
			}

			if (activeSecureTargets.Count >= Info.MaximumActiveSecureMissions && expansionStateService != null)
			{
				var blockedObjectives = expansionBlockedObjectives;
				var radiusSq = Info.ExpansionBlockedSecureRadius * Info.ExpansionBlockedSecureRadius;
				var blockedAlreadyRepresented = blockedObjectives.Any(blocked =>
					activeSecureTargets.Values.Any(active => (active - blocked).LengthSquared <= radiusSq));
				if (blockedObjectives.Count > 0 && !blockedAlreadyRepresented)
				{
					var replaceable = activeSecureTargets.Keys
						// A live PIONEER expansion-unblock SECURE is itself the thing this eviction
						// mechanism is trying to make room for. Never select it as the victim.
						.Where(key => !pioneerExpansionPrioritySecureTargets.Contains(key))
						.Where(key => commandBidService == null ||
							!commandBidService.TryGetActiveMissionForTarget(key, out var active) || active.MissionType != FransMissionType.Secure)
						.OrderBy(key => activeSecurePublishedWorldTick.TryGetValue(key, out var tick) ? tick : int.MaxValue)
						.ThenBy(key => key)
						.Select(key => (uint?)key)
						.FirstOrDefault();
					if (replaceable.HasValue)
					{
						FransBotLog.BotDebug(world,
							"{0}: GENERAL yields unowned SECURE slot {1} so pioneer-MCV SECURE REQUIRED expansion work can enter the {2}-slot board. Active Commander SECURE ownership is never preempted.",
							player, replaceable.Value, Info.MaximumActiveSecureMissions);
						ReleaseActiveSecureToCooldown(replaceable.Value, "yielded to SECURE REQUIRED expansion-unblock demand", Info.SecureNoBidBackoffTicks);
					}
				}
			}

			if (activeSecureTargets.Count >= Info.MaximumActiveSecureMissions)
				return;

			var friendlyRefineries = combatIntelService.OwnedActors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && FransActorClass.IsRefinery(a.Info)).ToArray();
			if (!TryGetOwnEconomicFrontier(out var ownFrontier, out _))
				ownFrontier = clusters.Length > 0
					? clusters.OrderBy(GetMineClusterKey).First().Center
					: knownEnemyFacts.OrderBy(f => f.ActorId).First().LastSeenCell;

			RefreshGroundForwardAnchor();
			var hasFrontierAnchor = hasLatestGroundAnchor;
			var frontierAnchor = latestGroundAnchorPoint;
			var ranked = new List<(FransMineCluster Cluster, FransCombatIntelContact Fact, bool StandaloneFact, uint Key, CPos Cell, int AvailableNodes, int ConstructionYards, bool ExpansionBlocked, bool FrontierContinuous, long Score)>();
			foreach (var cluster in clusters.OrderBy(GetMineClusterKey))
			{
				var key = GetMineClusterKey(cluster);
				if (key == uint.MaxValue || activeSecureTargets.ContainsKey(key) || pendingSecureFootholds.ContainsKey(key))
					continue;
				if (secureTargetCooldownUntil.TryGetValue(key, out var until) && world.WorldTick < until)
					continue;

				var mergedFacts = factsByCluster.TryGetValue(key, out var foundFacts)
					? foundFacts
					: Array.Empty<FransCombatIntelContact>();
				var availableNodes = CountSecureAvailableOreMineNodes(cluster,
					useOreNodeOwnership ? unpairedOreMineLocations : null, alliedClaimStructures);
				if (availableNodes + mergedFacts.Length <= 0)
					continue;
				if (mergedFacts.Length == 0 && !useOreNodeOwnership && friendlyRefineries.Any(a => IsEconomyActorNearCluster(a.Location, cluster)))
					continue;

				var blockedObjective = FindExpansionBlockedObjectiveForCluster(cluster, expansionBlockedObjectives);
				var objectiveCell = mergedFacts.Length == 0 && blockedObjective.HasValue
					? blockedObjective.Value
					: SelectSecureObjectiveCell(cluster,
						useOreNodeOwnership ? unpairedOreMineLocations : null, alliedClaimStructures, mergedFacts);
				var risk = riskModelService.EvaluateStrategicCell(objectiveCell, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
				var enemyForce = combatIntelService.EstimateEnemyCombatValueNear(
					objectiveCell, Info.SecureRiskAssessmentRadius, null, out _, out _);
				var freshIntel = mineClusterLastObservedTick.TryGetValue(key, out var observedTick) &&
					world.WorldTick - observedTick <= Info.StrategicIntelGoodAgeTicks;

				var expansionBlocked = blockedObjective.HasValue || IsExpansionBlockedSecureCandidate(objectiveCell, expansionBlockedObjectives);
				var apparentlyCalm = risk.Score < Info.SecureMinimumRiskScore && enemyForce <= 0;
				// A remembered FACT is itself persistent strategic structure intel, so it never needs
				// a separate stale-calm RECON gate merely to prove that the strategic object exists.
				// Likewise, a pioneer MCV's explicit SECURE REQUIRED mark is earned fair intel: forcing
				// another RECON before Ground SECURE would deadlock expansion behind its own safety gate.
				if (mergedFacts.Length == 0 && apparentlyCalm && !freshIntel && !expansionBlocked)
				{
					secureReconRequiredTargets.Add(key);
					continue;
				}

				var distance = Math.Abs(objectiveCell.X - ownFrontier.X) + Math.Abs(objectiveCell.Y - ownFrontier.Y);
				var strategicObjects = availableNodes + mergedFacts.Length;
				var frontierDistance = hasFrontierAnchor
					? Math.Abs(objectiveCell.X - frontierAnchor.X) + Math.Abs(objectiveCell.Y - frontierAnchor.Y)
					: int.MaxValue;
				var frontierContinuous = hasFrontierAnchor && frontierDistance <= Info.SecureFrontierContinuityRadius;
				var score = (long)strategicObjects * Info.SecureMineNodeScore -
					(long)Math.Max(0, risk.Score) * Info.SecureRiskScorePenaltyWeight -
					(long)distance * Info.SecureDistanceScorePerCell +
					(expansionBlocked ? Info.ExpansionBlockedSecurePriorityBonus : 0) +
					(frontierContinuous ? Info.SecureFrontierContinuityBonus : 0);
				ranked.Add((cluster, default, false, key, objectiveCell, availableNodes, mergedFacts.Length, expansionBlocked, frontierContinuous, score));
			}

			foreach (var fact in knownEnemyFacts.Where(f => !factClusterAssignments.ContainsKey(f.ActorId)).OrderBy(f => f.ActorId))
			{
				var key = fact.ActorId;
				if (key == 0 || activeSecureTargets.ContainsKey(key))
					continue;
				if (secureTargetCooldownUntil.TryGetValue(key, out var until) && world.WorldTick < until)
					continue;

				var objectiveCell = fact.LastSeenCell;
				var risk = riskModelService.EvaluateStrategicCell(objectiveCell, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
				var distance = Math.Abs(objectiveCell.X - ownFrontier.X) + Math.Abs(objectiveCell.Y - ownFrontier.Y);
				var expansionBlocked = IsExpansionBlockedSecureCandidate(objectiveCell, expansionBlockedObjectives);
				var frontierDistance = hasFrontierAnchor
					? Math.Abs(objectiveCell.X - frontierAnchor.X) + Math.Abs(objectiveCell.Y - frontierAnchor.Y)
					: int.MaxValue;
				var frontierContinuous = hasFrontierAnchor && frontierDistance <= Info.SecureFrontierContinuityRadius;
				var score = (long)Info.SecureMineNodeScore -
					(long)Math.Max(0, risk.Score) * Info.SecureRiskScorePenaltyWeight -
					(long)distance * Info.SecureDistanceScorePerCell +
					(expansionBlocked ? Info.ExpansionBlockedSecurePriorityBonus : 0) +
					(frontierContinuous ? Info.SecureFrontierContinuityBonus : 0);
				ranked.Add((null, fact, true, key, objectiveCell, 0, 1, expansionBlocked, frontierContinuous, score));
			}

			foreach (var candidate in ranked.OrderByDescending(x => x.Score).ThenBy(x => x.Key))
			{
				if (activeSecureTargets.Count >= Info.MaximumActiveSecureMissions)
					break;
				activeSecureTargets[candidate.Key] = candidate.Cell;
				activeSecurePublishedWorldTick[candidate.Key] = world.WorldTick;
				if (candidate.StandaloneFact)
					standaloneFactSecureTargets.Add(candidate.Key);
				if (activeReconTargets.ContainsKey(candidate.Key))
					CompleteReconMission(candidate.Key, "superseded by higher-priority SECURE");

				if (candidate.ExpansionBlocked)
				{
					pioneerExpansionPrioritySecureTargets.Add(candidate.Key);
					FransBotLog.BotDebug(world,
						"{0}: GENERAL prioritizes SECURE {1} at {2} with +{3} expansion-unblock bonus because the SINGLE active pioneer objective marked this area SECURE REQUIRED. If PIONEER abandons/switches that objective, this bonus-owned SECURE is released instead of continuing as a stale invasion.",
						player, candidate.Key, candidate.Cell, Info.ExpansionBlockedSecurePriorityBonus);
				}
				if (candidate.FrontierContinuous)
					FransBotLog.BotDebug(world,
						"{0}: GENERAL gives SECURE {1} at {2} +{3} FRONTIER CONTINUITY because it lies within {4} cells of current Ground Forward Anchor {5}. Contiguous front growth outranks a similarly valuable distant sector.",
						player, candidate.Key, candidate.Cell, Info.SecureFrontierContinuityBonus, Info.SecureFrontierContinuityRadius, frontierAnchor);

				var secureIntel = BuildSiteIntel(candidate.Cell, Info.SecureRiskAssessmentRadius, Info.StrategicIntelAgingAgeTicks);
				FransBotLog.BotDebug(world,
					candidate.StandaloneFact
						? "{0}: GENERAL publishes MISSION SECURE enemy FACT {1} at {2}, slot {3}/{4}: 1 Construction Yard = 1 ore-node strategic object, strategic score {7}; raw SiteIntel [{8}]."
						: "{0}: GENERAL publishes MISSION SECURE MineCluster {1} at {2}, slot {3}/{4}: {5} available ore node(s) + {6} enemy Construction Yard(s), strategic score {7}; raw SiteIntel [{8}]. FACT and ore each contribute the same base strategic value.",
					player, candidate.Key, candidate.Cell, activeSecureTargets.Count, Info.MaximumActiveSecureMissions,
					candidate.AvailableNodes, candidate.ConstructionYards, candidate.Score, FormatSiteIntelForLog(secureIntel));
				PublishSecureMission(candidate.Key, candidate.StandaloneFact ? "fact" : "minecluster",
					candidate.StandaloneFact ? candidate.Fact.Owner : candidate.Cluster.Representative.Owner, candidate.Cell);
			}
		}

		Actor[] GetAlliedSecureClaimStructures()
		{
			return world.ActorsHavingTrait<Building>()
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.Owner != player && a.OccupiesSpace != null &&
					Info.SecureAlliedClaimStructureTypes.Contains(a.Info.Name) &&
					PlayerRelationship.Ally.HasRelationship(player.RelationshipWith(a.Owner)))
				.OrderBy(a => a.ActorID)
				.ToArray();
		}

		bool IsOreMineClaimedByAlly(CPos mineCell, IReadOnlyCollection<Actor> alliedClaimStructures)
		{
			if (alliedClaimStructures == null || alliedClaimStructures.Count == 0)
				return false;
			var radiusSquared = Info.SecureAlliedClaimRadius * Info.SecureAlliedClaimRadius;
			return alliedClaimStructures.Any(a => (a.Location - mineCell).LengthSquared <= radiusSquared);
		}

		IEnumerable<CPos> SecureAvailableOreMineLocations(FransMineCluster cluster, HashSet<CPos> unpairedLocations,
			IReadOnlyCollection<Actor> alliedClaimStructures)
		{
			if (cluster == null)
				yield break;

			foreach (var mine in cluster.Mines.Where(m => m != null && m.IsInWorld && !m.IsDead)
				.OrderBy(m => m.Location.X).ThenBy(m => m.Location.Y))
			{
				if (unpairedLocations != null && !unpairedLocations.Contains(mine.Location))
					continue;
				if (IsOreMineClaimedByAlly(mine.Location, alliedClaimStructures))
					continue;
				yield return mine.Location;
			}
		}

		int CountSecureAvailableOreMineNodes(FransMineCluster cluster, HashSet<CPos> unpairedLocations,
			IReadOnlyCollection<Actor> alliedClaimStructures) =>
			SecureAvailableOreMineLocations(cluster, unpairedLocations, alliedClaimStructures).Count();

		CPos SelectSecureObjectiveCell(FransMineCluster cluster, HashSet<CPos> unpairedLocations,
			IReadOnlyCollection<Actor> alliedClaimStructures, IReadOnlyCollection<FransCombatIntelContact> mergedConstructionYards = null)
		{
			// If a known enemy FACT is part of this strategic area, center SECURE on the FACT.
			// The merge radius guarantees that at least one mine in the merged MineCluster is inside
			// the same local territorial fight, while centering on FACT prevents the strategic building
			// from surviving just outside Ground's clear radius.
			if (mergedConstructionYards != null && mergedConstructionYards.Count > 0)
				return mergedConstructionYards
					.OrderBy(f => (f.LastSeenCell - cluster.Center).LengthSquared)
					.ThenBy(f => f.ActorId)
					.First().LastSeenCell;

			return SecureAvailableOreMineLocations(cluster, unpairedLocations, alliedClaimStructures)
				.OrderBy(c => (c - cluster.Center).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.FirstOrDefault(cluster.Center);
		}

		FransCombatIntelContact[] GetKnownEnemyConstructionYards()
		{
			var rules = world.Map.Rules;
			return combatIntelService.EnemyCombatContacts
				.Where(c => c.ActorId != 0 && c.IsBuilding
					&& c.ActorType != null && rules.Actors.TryGetValue(c.ActorType, out var ai)
					&& FransActorClass.IsConyard(ai))
				.Where(c => c.Owner != null && PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)))
				.OrderBy(c => c.ActorId)
				.ToArray();
		}

		Dictionary<uint, uint> BuildConstructionYardClusterAssignments(
			IReadOnlyCollection<FransCombatIntelContact> constructionYards, IReadOnlyCollection<FransMineCluster> clusters)
		{
			var assignments = new Dictionary<uint, uint>();
			if (constructionYards == null || constructionYards.Count == 0 || clusters == null || clusters.Count == 0)
				return assignments;

			var mergeRadiusSq = Info.SecureConstructionYardMergeRadius * Info.SecureConstructionYardMergeRadius;
			foreach (var fact in constructionYards.OrderBy(f => f.ActorId))
			{
				var bestClusterKey = 0u;
				var bestDistanceSq = int.MaxValue;
				foreach (var cluster in clusters.OrderBy(GetMineClusterKey))
				{
					var key = GetMineClusterKey(cluster);
					if (key == uint.MaxValue)
						continue;
					var distanceSq = cluster.Mines
						.Where(m => m != null && m.IsInWorld && !m.IsDead)
						.Select(m => (m.Location - fact.LastSeenCell).LengthSquared)
						.DefaultIfEmpty(int.MaxValue)
						.Min();
					if (distanceSq > mergeRadiusSq || distanceSq > bestDistanceSq ||
						(distanceSq == bestDistanceSq && bestClusterKey != 0 && key >= bestClusterKey))
						continue;
					bestDistanceSq = distanceSq;
					bestClusterKey = key;
				}

				if (bestClusterKey != 0)
					assignments[fact.ActorId] = bestClusterKey;
			}

			return assignments;
		}

		void RefreshPendingSecureFootholds(FransMineCluster[] clusters, IReadOnlyCollection<Actor> alliedClaimStructures)
		{
			if (pendingSecureFootholds.Count == 0)
				return;

			foreach (var pending in pendingSecureFootholds.Values
				.OrderBy(f => f.ControlObservedWorldTick).ThenBy(f => f.TargetActorId).ToArray())
			{
				var cluster = clusters.FirstOrDefault(c => GetMineClusterKey(c) == pending.TargetActorId);
				if (cluster == null)
				{
					AbortSecureFoothold(pending.TargetActorId, "controlled MineCluster disappeared from the live resource map");
					continue;
				}

				// Preserve the team-aware rule: if an ally has established the local economy,
				// our pending foothold is redundant. Own PROC pairing is deliberately ignored here;
				// DefenseCommander/BaseBuilder still need the pending record until the physical foothold is complete.
				if (CountSecureAvailableOreMineNodes(cluster, null, alliedClaimStructures) <= 0)
				{
					AbortSecureFoothold(pending.TargetActorId,
						"all ore-mine nodes at the won objective are now claimed by an allied FACT/PROC");
					continue;
				}

				var secureStillOwned = commandBidService != null &&
					commandBidService.TryGetActiveMissionForTarget(pending.TargetActorId, out var activeSecureMission) &&
					activeSecureMission.MissionType == FransMissionType.Secure;
				if (!secureStillOwned && HasFreshVisibleEnemyRetakenSecurePoint(pending.Cell, out var enemyValue, out var enemyClaim))
					AbortSecureFoothold(pending.TargetActorId,
						enemyClaim
							? $"fresh visible enemy FACT/PROC has reclaimed the secured ore area at {pending.Cell}"
							: $"fresh visible enemy ground/static combat value {enemyValue} has returned to the secured area at {pending.Cell}",
						applyCooldown: false);
			}
		}

		bool HasFreshVisibleEnemyRetakenSecurePoint(CPos secureCell, out int visibleEnemyValue, out bool enemyEconomyClaim)
		{
			visibleEnemyValue = 0;
			enemyEconomyClaim = false;
			var threatRadiusSq = Info.SecureRiskAssessmentRadius * Info.SecureRiskAssessmentRadius;
			var claimRadiusSq = Info.SecureAlliedClaimRadius * Info.SecureAlliedClaimRadius;

			foreach (var enemy in combatIntelService.VisibleEnemies.Where(IsValidVisibleEnemy))
			{
				var distanceSq = (enemy.Location - secureCell).LengthSquared;
				if (distanceSq <= claimRadiusSq && Info.SecureAlliedClaimStructureTypes.Contains(enemy.Info.Name))
					enemyEconomyClaim = true;

				if (distanceSq > threatRadiusSq || !enemy.Info.HasTraitInfo<AttackBaseInfo>() ||
					enemy.TraitOrDefault<Aircraft>() != null)
					continue;

				visibleEnemyValue += GetTargetValue(enemy);
				if (visibleEnemyValue > 0)
					return true;
			}

			return enemyEconomyClaim;
		}

		void ReleaseActiveSecureToCooldown(uint secureTargetActorId, string reason, int cooldownTicks = -1)
		{
			if (secureTargetActorId == 0 || !activeSecureTargets.ContainsKey(secureTargetActorId))
				return;
			var appliedCooldown = cooldownTicks > 0 ? cooldownTicks : Info.SecureTargetCooldownTicks;
			secureTargetCooldownUntil[secureTargetActorId] = world.WorldTick + appliedCooldown;
			FransBotLog.BotDebug(world,
				"{0}: GENERAL releases MISSION SECURE {1} {2}: {3}; cooldown through WT {4}. {5}/{6} SECURE slot(s) remain active.",
				player, standaloneFactSecureTargets.Contains(secureTargetActorId) ? "enemy FACT" : "MineCluster", secureTargetActorId,
				reason ?? "released", secureTargetCooldownUntil[secureTargetActorId], Math.Max(0, activeSecureTargets.Count - 1), Info.MaximumActiveSecureMissions);
			activeSecureTargets.Remove(secureTargetActorId);
			activeSecurePublishedWorldTick.Remove(secureTargetActorId);
			pioneerExpansionPrioritySecureTargets.Remove(secureTargetActorId);
		}

		void PublishSecureMission(uint secureTargetActorId, string targetActorType, Player targetOwner, CPos secureCell)
		{
			if (secureTargetActorId == 0 || string.IsNullOrWhiteSpace(targetActorType) || currentMissions.Count >= Info.MaximumPublishedMissions)
				return;
			// SECURE targets territory, not the structure actor directly. TargetIsBuilding therefore stays false
			// even when a remembered enemy FACT supplies the strategic target key.
			var strategicPriority = pioneerExpansionPrioritySecureTargets.Contains(secureTargetActorId)
				? (int)Math.Min(int.MaxValue, (long)Info.SecureStrategicPriority + Info.ExpansionBlockedSecurePriorityBonus)
				: Info.SecureStrategicPriority;
			var secure = new FransMission(null, secureTargetActorId, targetActorType, targetOwner,
				secureCell, false, false, BuildSiteIntel(secureCell, Info.SecureRiskAssessmentRadius, Info.StrategicIntelAgingAgeTicks),
				FransMissionType.Secure, strategicPriority, world.WorldTick);
			PublishUniqueMission(secure);
		}

		int GlobalReconSlotCount()
		{
			if (commandBidService == null)
				return activeReconTargets.Count;

			var accepted = commandBidService.GetActiveReconMissionCount();
			var pendingOnly = activeReconTargets.Keys.Count(key => !commandBidService.HasActiveReconMission(key));
			return accepted + pendingOnly;
		}

		void AppendReconMission()
		{
			if (mineClusterService == null || Info.MaximumActiveReconMissions <= 0)
				return;

			combatIntelService.EnsureCurrentSnapshot();
			var clusters = mineClusterService.VisibleClusters.Where(IsLiveMineCluster).ToArray();
			var byKey = clusters.ToDictionary(GetMineClusterKey);
			var expansionReconObjectives = expansionStateService?.ReconRequiredExpansionObjectives ?? Array.Empty<CPos>();
			var expansionReconRequiredTargets = new HashSet<uint>();
			if (expansionReconObjectives.Count > 0)
				foreach (var cluster in clusters)
				{
					var objective = FindExpansionBlockedObjectiveForCluster(cluster, expansionReconObjectives);
					if (!objective.HasValue)
						continue;
					var key = GetMineClusterKey(cluster);
					if (key == uint.MaxValue)
						continue;
					expansionReconRequiredTargets.Add(key);
				}

			// If an ordinary persistent RECON already owns the MineCluster that PIONEER now
			// needs to validate, repurpose that strategic slot immediately. The Commander also
			// reads the ExpansionState service at execution time, so an already-accepted immutable
			// broker assignment redirects to the exact ore cell without waiting for death/rotation.
			foreach (var key in expansionReconRequiredTargets.OrderBy(k => k))
			{
				if (!byKey.TryGetValue(key, out var existingCluster) || !activeReconTargets.ContainsKey(key))
					continue;
				var exactObjective = FindExpansionBlockedObjectiveForCluster(existingCluster, expansionReconObjectives);
				if (!exactObjective.HasValue)
					continue;
				activeReconTargets[key] = exactObjective.Value;
				expansionReconMissionTargets.Add(key);
			}
			// Enemy-territory RECON is a one-shot validation gate, unlike ordinary persistent probing.
			// As soon as the MCV planner reevaluates the objective as Safe or escalates it to SECURE,
			// close only the RECON that was opened for that expansion objective.
			foreach (var key in expansionReconMissionTargets.Where(key => !expansionReconRequiredTargets.Contains(key)).ToArray())
			{
				CompleteReconMission(key, "PIONEER-MCV objective received fresh intel; expansion validation no longer requires RECON");
				expansionReconMissionTargets.Remove(key);
			}

			foreach (var stale in activeReconTargets.Keys.Where(k => !IsSpawnProbeKey(k) && !byKey.ContainsKey(k)).ToArray())
			{
				activeReconTargets.Remove(stale);
				activeReconWithoutMissionSinceTick.Remove(stale);
			}

			// persistence belongs to a scout with an active MISSION, not to an empty
			// General slot. A scout may probe forever, but once its CommandBid MISSION is
			// gone (death, RECON retreat, or higher-priority supersession), the empty slot gets
			// a bounded grace period and is then rotated to normal RECON cooldown.
			if (commandBidService != null)
			{
				foreach (var key in activeReconTargets.Keys.OrderBy(k => k).ToArray())
				{
					if (commandBidService.HasActiveReconMission(key))
					{
						activeReconWithoutMissionSinceTick.Remove(key);
						continue;
					}

					if (!activeReconWithoutMissionSinceTick.TryGetValue(key, out var since))
					{
						since = world.WorldTick;
						activeReconWithoutMissionSinceTick[key] = since;
					}

					var withoutMissionTicks = world.WorldTick - since;
					if (!commandBidService.HasReconBid(key) && withoutMissionTicks >= Info.ReconNoBidBackoffTicks)
					{
						activeReconTargets.Remove(key);
						activeReconWithoutMissionSinceTick.Remove(key);
						reconTargetCooldownUntil[key] = world.WorldTick + Info.ReconNoBidBackoffTicks;
						FransBotLog.BotDebug(world,
							"{0}: GENERAL backs off new RECON MineCluster {1}: no Commander bid for {2} WT; target may be reconsidered after WT {3}. Existing active persistent RECON patrols are untouched.",
							player, key, Info.ReconNoBidBackoffTicks, reconTargetCooldownUntil[key]);
						continue;
					}

					if (withoutMissionTicks >= Info.ReconInactiveMissionSlotReleaseTicks)
						CompleteReconMission(key, $"no active Commander RECON MISSION for {Info.ReconInactiveMissionSlotReleaseTicks} WT; rotating stale strategic slot");
				}
			}

			var staleBefore = world.WorldTick - Info.StrategicIntelGoodAgeTicks;

			// Enemy-spawn probes run before the MineCluster fan: finding the enemy base is the only
			// path that ever lets SECURE/RAID form against it, and the probe retires as soon as the
			// cell is observed or a known enemy structure already sits near it, freeing the slot again.
			var spawnProbeSlotsUsed = 0;
			foreach (var probe in spawnProbeTargets.OrderBy(p => p.Key))
			{
				var unrepresentedPioneerForProbes = expansionReconRequiredTargets.Any(key =>
					!activeReconTargets.ContainsKey(key) &&
					(commandBidService == null || !commandBidService.HasActiveReconMission(key)));
				var probeReconSlotLimit = Info.MaximumActiveReconMissions +
					(unrepresentedPioneerForProbes ? Info.MaximumPioneerReconValidationMissions : 0);
				if (GlobalReconSlotCount() >= probeReconSlotLimit || spawnProbeSlotsUsed >= Info.EnemySpawnReconMaxSlots)
					break;
				if (activeReconTargets.ContainsKey(probe.Key) ||
					(commandBidService != null && commandBidService.HasActiveReconMission(probe.Key)) ||
					activeSecureTargets.ContainsKey(probe.Key))
					continue;
				if (reconTargetCooldownUntil.TryGetValue(probe.Key, out var probeCooldownUntil) && world.WorldTick < probeCooldownUntil)
					continue;
				if (spawnProbeLastObservedTick.TryGetValue(probe.Key, out var probeObserved) && probeObserved >= staleBefore)
					continue;
				activeReconTargets[probe.Key] = probe.Value;
				activeReconWithoutMissionSinceTick[probe.Key] = world.WorldTick;
				spawnProbeSlotsUsed++;
				FransBotLog.BotDebug(world,
					"{0}: GENERAL publishes MISSION RECON EnemySpawnProbe {1} at {2}, probe slot {3}/{4}: map-file mpspawn candidate minus own spawn; retires on observation so SECURE/RAID can act on what the scout finds.",
					player, probe.Key, probe.Value, spawnProbeSlotsUsed, Info.EnemySpawnReconMaxSlots);
			}

			while (true)
			{
				var unrepresentedPioneerValidation = expansionReconRequiredTargets.Any(key =>
					!activeReconTargets.ContainsKey(key) &&
					(commandBidService == null || !commandBidService.HasActiveReconMission(key)));
				var reconSlotLimit = Info.MaximumActiveReconMissions +
					(unrepresentedPioneerValidation ? Info.MaximumPioneerReconValidationMissions : 0);
				if (GlobalReconSlotCount() >= reconSlotLimit)
					break;
				var eligible = clusters
					.Where(c =>
					{
						var key = GetMineClusterKey(c);
						var expansionValidation = expansionReconRequiredTargets.Contains(key);
						if (key == uint.MaxValue || activeSecureTargets.ContainsKey(key) || activeReconTargets.ContainsKey(key) ||
							(commandBidService != null && commandBidService.HasActiveReconMission(key)) ||
							(pendingSecureFootholds.ContainsKey(key) && !expansionValidation))
							return false;
						if (!expansionValidation && reconTargetCooldownUntil.TryGetValue(key, out var until) && world.WorldTick < until)
							return false;
						return expansionValidation || !mineClusterLastObservedTick.TryGetValue(key, out var observed) || observed < staleBefore;
					})
					.ToArray();
				if (eligible.Length == 0)
					break;

				// Explicit validation gates outrank ordinary persistent probing. MCV expansion validation is
				// one-shot and closes when the expansion planner sees fresh enough evidence to classify the
				// objective Safe or Contested; normal SECURE uncertainty remains independent.
				var expansionValidationRecon = eligible.Where(c => expansionReconRequiredTargets.Contains(GetMineClusterKey(c))).ToArray();
				var secureValidationRecon = eligible.Where(c => secureReconRequiredTargets.Contains(GetMineClusterKey(c)) &&
					!expansionReconRequiredTargets.Contains(GetMineClusterKey(c))).ToArray();
				var selectionPool = expansionValidationRecon.Length > 0 ? expansionValidationRecon :
					secureValidationRecon.Length > 0 ? secureValidationRecon : eligible;
				var reconForExpansionValidation = expansionValidationRecon.Length > 0;
				var reconForSecureValidation = !reconForExpansionValidation && secureValidationRecon.Length > 0;

				FransMineCluster chosen;
				CPos reconAnchor;
				string anchorKind;

				// Exact validation gates stay objective-driven. Ordinary RECON is different: it now
				// grows outward as a geographic fan from the home FACT/MCV. Each free slot prefers
				// the least-covered fan arm, then the nearest stale MineCluster in that arm. If a
				// scout later dies/preempts and the inner cluster is on cooldown, the refill naturally
				// advances farther outward in the same direction instead of jumping across the map.
				if (reconForExpansionValidation || reconForSecureValidation)
				{
					if (TryGetReconHomeAnchor(out reconAnchor))
					{
						chosen = OrderReconCandidates(selectionPool, c => (c.Center - reconAnchor).LengthSquared).FirstOrDefault();
						anchorKind = "exact validation from home";
					}
					else
					{
						chosen = OrderReconCandidates(selectionPool, _ => 0).FirstOrDefault();
						reconAnchor = chosen?.Center ?? default;
						anchorKind = "exact validation deterministic fallback";
					}
				}
				else if (TryGetReconHomeAnchor(out reconAnchor))
				{
					chosen = SelectOrdinaryFanReconCandidate(selectionPool, reconAnchor, out var fanArm);
					anchorKind = $"home-base FAN arm {fanArm + 1}/{Info.ReconFanArmCount}";
				}
				else
				{
					chosen = OrderReconCandidates(selectionPool, _ => 0).FirstOrDefault();
					reconAnchor = chosen?.Center ?? default;
					anchorKind = "home-base FAN deterministic fallback";
				}

				if (chosen == null)
					break;
				if (reconForExpansionValidation)
					anchorKind = "PIONEER-MCV exact-objective RECON gate; " + anchorKind;
				else if (reconForSecureValidation)
					anchorKind = "SECURE uncertainty gate; " + anchorKind;

				var key = GetMineClusterKey(chosen);
				var missionCell = reconForExpansionValidation
					? FindExpansionBlockedObjectiveForCluster(chosen, expansionReconObjectives) ?? chosen.Center
					: chosen.Center;
				var missionPriority = reconForExpansionValidation ? Info.PioneerReconStrategicPriority : Info.ReconStrategicPriority;
				if (reconForExpansionValidation)
					expansionReconMissionTargets.Add(key);
				activeReconTargets[key] = missionCell;
				activeReconWithoutMissionSinceTick[key] = world.WorldTick;
				var reconIntel = BuildSiteIntel(missionCell, Info.SecureRiskAssessmentRadius, Info.StrategicIntelAgingAgeTicks);
				FransBotLog.BotDebug(world,
					"{0}: GENERAL publishes MISSION RECON MineCluster {1} at {2}, slot {3}/{4}, priority {5}; raw SiteIntel [{6}]. Strategic anchor {7} at {8}. Commander chooses scout/capability/ETA/risk.",
					player, key, missionCell, GlobalReconSlotCount(), reconSlotLimit, missionPriority,
					FormatSiteIntelForLog(reconIntel), anchorKind, reconAnchor);
			}

			foreach (var pair in activeReconTargets.OrderBy(p => p.Key))
			{
				if (currentMissions.Count >= Info.MaximumPublishedMissions)
					break;
				if (spawnProbeTargets.TryGetValue(pair.Key, out var probeCell))
				{
					if (activeSecureTargets.ContainsKey(pair.Key) || pendingSecureFootholds.ContainsKey(pair.Key))
						continue;
					var probe = new FransMission(null, pair.Key, "enemyspawn", null,
						probeCell, false, false, BuildSiteIntel(probeCell, Info.SecureRiskAssessmentRadius, Info.StrategicIntelAgingAgeTicks),
						FransMissionType.Recon, Info.ReconStrategicPriority, world.WorldTick);
					PublishUniqueMission(probe);
					continue;
				}

				if (!byKey.TryGetValue(pair.Key, out var cluster) || activeSecureTargets.ContainsKey(pair.Key) ||
					pendingSecureFootholds.ContainsKey(pair.Key))
					continue;
				var pioneerValidation = expansionReconMissionTargets.Contains(pair.Key);
				var missionCell = pioneerValidation ? pair.Value : cluster.Center;
				var recon = new FransMission(null, pair.Key, "minecluster", cluster.Representative.Owner,
					missionCell, false, false, BuildSiteIntel(missionCell, Info.SecureRiskAssessmentRadius, Info.StrategicIntelAgingAgeTicks),
					FransMissionType.Recon, pioneerValidation ? Info.PioneerReconStrategicPriority : Info.ReconStrategicPriority, world.WorldTick);
				PublishUniqueMission(recon);
			}
		}

		IOrderedEnumerable<FransMineCluster> OrderReconCandidates(IEnumerable<FransMineCluster> candidates, Func<FransMineCluster, int> distanceSelector)
		{
			return candidates
				.OrderBy(distanceSelector)
				.ThenByDescending(c => c.MineCount)
				.ThenBy(c => mineClusterLastObservedTick.TryGetValue(GetMineClusterKey(c), out var observed) ? observed : int.MinValue)
				.ThenBy(GetMineClusterKey);
		}

		bool TryGetReconHomeAnchor(out CPos homeCell)
		{
			combatIntelService.EnsureCurrentSnapshot();
			var owned = combatIntelService.OwnedActors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null)
				.ToArray();

			var home = owned.Where(a => FransActorClass.IsConyard(a.Info)).OrderBy(a => a.ActorID).FirstOrDefault() ??
				owned.Where(a => FransActorClass.IsMcv(a.Info)).OrderBy(a => a.ActorID).FirstOrDefault();
			if (home == null)
			{
				homeCell = default;
				return false;
			}

			homeCell = home.Location;
			return true;
		}

		int GetReconFanArm(CPos home, CPos target)
		{
			var arms = Math.Max(1, Info.ReconFanArmCount);
			if (arms == 1)
				return 0;

			var dx = target.X - home.X;
			var dy = target.Y - home.Y;
			if (dx == 0 && dy == 0)
				return 0;

			var angle = Math.Atan2(dy, dx);
			if (angle < 0)
				angle += Math.PI * 2;
			var sector = (int)Math.Floor((angle + Math.PI / arms) / (Math.PI * 2) * arms) % arms;
			return sector;
		}

		FransMineCluster SelectOrdinaryFanReconCandidate(IEnumerable<FransMineCluster> candidates, CPos home, out int selectedArm)
		{
			selectedArm = 0;
			var candidateArray = candidates.ToArray();
			if (candidateArray.Length == 0)
				return null;

			var activePerArm = new int[Math.Max(1, Info.ReconFanArmCount)];
			foreach (var pair in activeReconTargets)
			{
				// PIONEER/SECURE validation slots are strategic exceptions, not fan coverage.
				if (expansionReconMissionTargets.Contains(pair.Key) || secureReconRequiredTargets.Contains(pair.Key))
					continue;
				activePerArm[GetReconFanArm(home, pair.Value)]++;
			}

			var availableArms = candidateArray
				.Select(c => GetReconFanArm(home, c.Center))
				.Distinct()
				.OrderBy(arm => activePerArm[arm])
				.ThenBy(arm => arm)
				.ToArray();
			if (availableArms.Length == 0)
				return null;

			var chosenArm = availableArms[0];
			selectedArm = chosenArm;
			return OrderReconCandidates(candidateArray.Where(c => GetReconFanArm(home, c.Center) == chosenArm),
				c => (c.Center - home).LengthSquared).FirstOrDefault();
		}

		bool TryGetOwnEconomicFrontier(out CPos frontierCell, out string anchorKind)
		{
			var owned = combatIntelService.OwnedActors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null)
				.ToArray();

			var home = owned
				.Where(a => FransActorClass.IsConyard(a.Info))
				.OrderBy(a => a.ActorID)
				.FirstOrDefault() ?? owned
				.Where(a => FransActorClass.IsMcv(a.Info))
				.OrderBy(a => a.ActorID)
				.FirstOrDefault();

			var stableEconomy = owned
				.Where(a => IsLiveOwnedEconomyActor(a, true))
				.ToArray();
			Actor[] mobileEconomy = stableEconomy.Length == 0
				? owned.Where(a => IsLiveOwnedEconomyActor(a, false)).ToArray()
				: [];
			var economy = stableEconomy.Length > 0 ? stableEconomy : mobileEconomy;

			if (economy.Length > 0)
			{
				if (home != null)
					frontierCell = economy
						.OrderByDescending(a => (a.Location - home.Location).LengthSquared)
						.ThenBy(a => a.ActorID)
						.First().Location;
				else
					frontierCell = economy.OrderBy(a => a.ActorID).First().Location;

				anchorKind = stableEconomy.Length > 0 ? "own outer refinery frontier" : "own harvester frontier";
				return true;
			}

			if (home != null)
			{
				frontierCell = home.Location;
				anchorKind = "home base before first refinery";
				return true;
			}

			frontierCell = default;
			anchorKind = "none";
			return false;
		}

		public void CompleteReconMission(uint reconTargetActorId, string reason)
		{
			if (reconTargetActorId == 0 || !activeReconTargets.TryGetValue(reconTargetActorId, out var reconCell))
				return;

			reconTargetCooldownUntil[reconTargetActorId] = world.WorldTick + Info.ReconTargetCooldownTicks;
			activeReconTargets.Remove(reconTargetActorId);
			activeReconWithoutMissionSinceTick.Remove(reconTargetActorId);
			FransBotLog.BotDebug(world,
				"{0}: GENERAL closes MISSION RECON MineCluster {1} at {2}: {3}. Target cooldown through WT {4}; global RECON occupancy remains {5}/{6} (accepted persistent missions still count after board-slot closure).",
				player, reconTargetActorId, reconCell, reason ?? "completed", reconTargetCooldownUntil[reconTargetActorId],
				GlobalReconSlotCount(), Info.MaximumActiveReconMissions);
			lastPublishedWorldTick = -1;
		}

		public bool EstablishSecureAnchor(uint secureTargetActorId, CPos anchorCell, string reason)
		{
			if (secureTargetActorId == 0 || transportLossSecureIncidents.ContainsKey(secureTargetActorId))
				return false;

			var standaloneFact = standaloneFactSecureTargets.Contains(secureTargetActorId);
			var firstEstablishment = standaloneFact
				? !establishedSecureAnchorPoints.ContainsKey(secureTargetActorId)
				: !pendingSecureFootholds.ContainsKey(secureTargetActorId) && !completedSecureFootholds.Contains(secureTargetActorId);
			establishedSecureAnchorPoints[secureTargetActorId] = anchorCell;
			if (firstEstablishment || !secureAnchorEstablishedWorldTick.ContainsKey(secureTargetActorId))
				secureAnchorEstablishedWorldTick[secureTargetActorId] = world.WorldTick;
			RefreshGroundForwardAnchor(force: true);
			// Only ore/MineCluster SECURE enters the autonomous foothold-development queue.
			// A standalone enemy FACT is territorial work only: CLEAR -> ANCHOR -> release.
			if (!standaloneFact && !completedSecureFootholds.Contains(secureTargetActorId))
				pendingSecureFootholds[secureTargetActorId] = new FransSecureFoothold(secureTargetActorId, anchorCell, world.WorldTick);
			activeSecureTargets.Remove(secureTargetActorId);
			activeSecurePublishedWorldTick.Remove(secureTargetActorId);
			secureTargetCooldownUntil.Remove(secureTargetActorId);
			domainSecureClearWorldTick.Remove((secureTargetActorId, FransCommanderKind.Air));
			domainSecureClearWorldTick.Remove((secureTargetActorId, FransCommanderKind.Sea));
			lastPublishedWorldTick = -1;

			if (firstEstablishment)
				FransBotLog.BotDebug(world,
					"{0}: GENERAL establishes TERRITORIAL SECURE ANCHOR {1} {2} at {3}: {4}. MCV/foothold permission is permanent until a real SECURE invalidation; Forward Anchor is separate and exists only while fair enemy-building/Ground-combat intel makes secured territory an active front; {5}.",
					player, standaloneFact ? "enemy FACT" : "MineCluster", secureTargetActorId, anchorCell,
					reason ?? "Commander reports initial area clear", standaloneFact ? "standalone FACT SECURE has no ore foothold-development queue" : "BaseBuilder develops the ore foothold independently");
			return true;
		}

		public bool CompleteDomainSecureMission(uint secureTargetActorId, FransCommanderKind commander, CPos clearCell, string reason)
		{
			if (secureTargetActorId == 0)
				return false;

			if (transportLossSecureIncidents.TryGetValue(secureTargetActorId, out var lossIncident))
				return CloseTransportLossSecureIncident(secureTargetActorId, commander, clearCell, "ResolvedCommanderClear",
					reason ?? "Commander reports loss area clear", GetTransportLossDangerEvidenceCount(lossIncident.LatestLossCell));

			if (commander == FransCommanderKind.Ground)
				return false;

			if (seaTransportBeachSecureRequests.ContainsKey(secureTargetActorId))
			{
				if (commander != FransCommanderKind.Sea)
					return false;
				domainSecureClearWorldTick[(secureTargetActorId, commander)] = world.WorldTick;
				domainSecureClearCells[(secureTargetActorId, commander)] = clearCell;
				lastPublishedWorldTick = -1;
				FransBotLog.BotDebug(world,
					"{0}: GENERAL accepts Sea transport-beach SECURE CLEAR {1} at {2}: {3}. The lease stays open while GroundTransfer is active; Sea re-bids only after newer relevant intel.",
					player, secureTargetActorId, clearCell, reason ?? "landing beach clear");
				return true;
			}

			if (!activeSecureTargets.ContainsKey(secureTargetActorId))
				return false;

			// Air/Sea CLEAR is domain memory, not territorial control. Record when this domain
			// proved the target clear, close the current opportunity, and immediately rebuild the
			// board so Ground can take the same SECURE without a target-wide cooldown. The same
			// Air/Sea domain must see newer relevant enemy intel before it may bid again.
			domainSecureClearWorldTick[(secureTargetActorId, commander)] = world.WorldTick;
			domainSecureClearCells[(secureTargetActorId, commander)] = clearCell;
			activeSecureTargets.Remove(secureTargetActorId);
			activeSecurePublishedWorldTick.Remove(secureTargetActorId);
			secureTargetCooldownUntil.Remove(secureTargetActorId);
			if (standaloneFactSecureTargets.Contains(secureTargetActorId))
				standaloneFactSecureTargets.Remove(secureTargetActorId);
			lastPublishedWorldTick = -1;

			FransBotLog.BotDebug(world,
				"{0}: GENERAL accepts {1} domain SECURE CLEAR for target {2} at {3}: {4}. {1} will not bid this target again until newer domain-relevant enemy intel appears; Ground may SECURE it immediately. Ground ANCHOR, GROUND-SECURED MCV permission and ore foothold state are unchanged.",
				player, commander, secureTargetActorId, clearCell, reason ?? "domain area clear");
			return true;
		}

		public bool TryGetDomainSecureClearWorldTick(uint secureTargetActorId, FransCommanderKind commander, out int clearWorldTick)
		{
			if (secureTargetActorId == 0 || commander == FransCommanderKind.Ground)
			{
				clearWorldTick = -1;
				return false;
			}

			return domainSecureClearWorldTick.TryGetValue((secureTargetActorId, commander), out clearWorldTick);
		}

		public bool TryGetRecentDomainSecureClearNear(CPos objectiveCell, int radius, int notBeforeWorldTick, out FransCommanderKind commander, out int clearWorldTick)
		{
			commander = default;
			clearWorldTick = -1;
			var radiusSquared = Math.Max(0, radius) * Math.Max(0, radius);
			foreach (var pair in domainSecureClearWorldTick)
			{
				if (pair.Key.Commander == FransCommanderKind.Ground || pair.Value < notBeforeWorldTick || pair.Value <= clearWorldTick)
					continue;
				if (!domainSecureClearCells.TryGetValue(pair.Key, out var clearCell) || (clearCell - objectiveCell).LengthSquared > radiusSquared)
					continue;

				commander = pair.Key.Commander;
				clearWorldTick = pair.Value;
			}

			return clearWorldTick >= 0;
		}

		public void ReportSecureRetreat(uint secureTargetActorId, string reason)
		{
			if (secureTargetActorId == 0)
				return;

			if (transportLossSecureIncidents.ContainsKey(secureTargetActorId))
			{
				domainSecureClearWorldTick.Remove((secureTargetActorId, FransCommanderKind.Air));
				domainSecureClearWorldTick.Remove((secureTargetActorId, FransCommanderKind.Sea));
				lastPublishedWorldTick = -1;
				FransBotLog.BotDebug(world,
					"{0}: GENERAL receives LST-loss SECURE RETREAT for incident {1}: {2}. The observed loss incident stays open with no target-wide cooldown so another capable Ground/Air/Sea bidder may respond.",
					player, secureTargetActorId, reason ?? "Commander RETREAT");
				return;
			}

			if (seaTransportBeachSecureRequests.ContainsKey(secureTargetActorId))
			{
				domainSecureClearWorldTick.Remove((secureTargetActorId, FransCommanderKind.Sea));
				lastPublishedWorldTick = -1;
				FransBotLog.BotDebug(world,
					"{0}: GENERAL receives Sea transport-beach SECURE RETREAT for {1}: {2}. The support lease stays open without territorial cooldown so another Sea capacity may respond.",
					player, secureTargetActorId, reason ?? "Sea support RETREAT");
				return;
			}

			var standaloneFact = standaloneFactSecureTargets.Contains(secureTargetActorId);
			pendingSecureFootholds.Remove(secureTargetActorId);
			if (hasLatestGroundAnchor && latestGroundAnchorTargetId == secureTargetActorId && !completedSecureFootholds.Contains(secureTargetActorId))
			{
				hasLatestGroundAnchor = false;
				latestGroundAnchorTargetId = 0;
				latestGroundAnchorPoint = default;
			}
			if (!completedSecureFootholds.Contains(secureTargetActorId))
			{
				establishedSecureAnchorPoints.Remove(secureTargetActorId);
				secureAnchorEstablishedWorldTick.Remove(secureTargetActorId);
				establishedSecureDefenseHoldUntil.Remove(secureTargetActorId);
			}
			activeSecureTargets.Remove(secureTargetActorId);
			activeSecurePublishedWorldTick.Remove(secureTargetActorId);
			secureTargetCooldownUntil[secureTargetActorId] = world.WorldTick + Info.SecureTargetCooldownTicks;
			FransBotLog.BotDebug(world,
				"{0}: GENERAL receives SECURE RETREAT for {1} {2}: {3}. Intel-derived undeveloped ANCHOR/development state is cleared and retry cooldown runs through WT {4}.",
				player, standaloneFact ? "enemy FACT" : "MineCluster", secureTargetActorId, reason ?? "Commander RETREAT", secureTargetCooldownUntil[secureTargetActorId]);
			if (standaloneFact)
				standaloneFactSecureTargets.Remove(secureTargetActorId);
			lastPublishedWorldTick = -1;
		}

		void AbortSecureFoothold(uint secureTargetActorId, string reason, bool applyCooldown = true)
		{
			if (secureTargetActorId == 0 || !pendingSecureFootholds.Remove(secureTargetActorId))
				return;

			// Fresh enemy return reopens this SECURE target, but does not erase the strategic
			// Ground ANCHOR earned by clearing it. Only a true abort/cooldown invalidates an
			// undeveloped latest anchor. The reopened territory can therefore be cleared again
			// while retreat/regroup still uses the latest won ground.
			if (applyCooldown && hasLatestGroundAnchor && latestGroundAnchorTargetId == secureTargetActorId && !completedSecureFootholds.Contains(secureTargetActorId))
			{
				hasLatestGroundAnchor = false;
				latestGroundAnchorTargetId = 0;
				latestGroundAnchorPoint = default;
			}

			if (!completedSecureFootholds.Contains(secureTargetActorId))
			{
				establishedSecureAnchorPoints.Remove(secureTargetActorId);
				secureAnchorEstablishedWorldTick.Remove(secureTargetActorId);
				establishedSecureDefenseHoldUntil.Remove(secureTargetActorId);
			}

			if (applyCooldown)
				secureTargetCooldownUntil[secureTargetActorId] = world.WorldTick + Info.SecureTargetCooldownTicks;
			else
				secureTargetCooldownUntil.Remove(secureTargetActorId);

			FransBotLog.BotDebug(world,
				applyCooldown
					? "{0}: GENERAL releases undeveloped SECURE ANCHOR MineCluster {1}: {2}. Cooldown through WT {3}; {4} pending foothold(s) remain."
					: "{0}: GENERAL reopens cleared SECURE MineCluster {1}: {2}. No cooldown is applied; the latest Ground ANCHOR is retained while the territory becomes eligible for SECURE again immediately; {4} pending foothold(s) remain.",
				player, secureTargetActorId, reason ?? "foothold no longer valid",
				applyCooldown ? secureTargetCooldownUntil[secureTargetActorId] : world.WorldTick, pendingSecureFootholds.Count);
			lastPublishedWorldTick = -1;
		}

		public IReadOnlyList<FransSecureFoothold> PendingSecureFootholds => pendingSecureFootholds.Values
			.OrderBy(f => f.ControlObservedWorldTick)
			.ThenBy(f => f.TargetActorId)
			.ToArray();

		bool HasPhysicalOwnedFactAtSecureFoothold(uint secureTargetActorId)
		{
			if (secureTargetActorId == 0 || !pendingSecureFootholds.TryGetValue(secureTargetActorId, out var pending))
				return false;

			var radiusSquared = Info.SecureAlliedClaimRadius * Info.SecureAlliedClaimRadius;
			return combatIntelService.OwnedActors.Any(a => a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null &&
				FransActorClass.IsConyard(a.Info) && (a.Location - pending.Cell).LengthSquared <= radiusSquared);
		}

		public bool IsSecureFootholdDevelopmentReady(uint secureTargetActorId) =>
			secureTargetActorId != 0 && pendingSecureFootholds.ContainsKey(secureTargetActorId) &&
			HasPhysicalOwnedFactAtSecureFoothold(secureTargetActorId);

		public bool TryGetSecureDefensePoint(out uint secureTargetActorId, out CPos secureCell, out int strategicPriority)
		{
			CleanupExpiredSecureDefenseHolds();
			var pending = pendingSecureFootholds.Values
				.Where(f => IsSecureFootholdDevelopmentReady(f.TargetActorId))
				.OrderBy(f => f.ControlObservedWorldTick)
				.ThenBy(f => f.TargetActorId)
				.FirstOrDefault();
			if (pending.TargetActorId != 0)
			{
				secureTargetActorId = pending.TargetActorId;
				secureCell = pending.Cell;
				strategicPriority = Info.SecureStrategicPriority;
				return true;
			}

			foreach (var pair in establishedSecureDefenseHoldUntil.OrderBy(kv => kv.Key))
				if (world.WorldTick <= pair.Value && establishedSecureAnchorPoints.TryGetValue(pair.Key, out var anchor))
				{
					secureTargetActorId = pair.Key;
					secureCell = anchor;
					strategicPriority = Info.SecureStrategicPriority;
					return true;
				}

			secureTargetActorId = 0;
			secureCell = default;
			strategicPriority = Info.SecureStrategicPriority;
			return false;
		}

		public bool TryGetSecureDefensePoint(uint secureTargetActorId, out CPos secureCell, out int strategicPriority)
		{
			CleanupExpiredSecureDefenseHolds();
			strategicPriority = Info.SecureStrategicPriority;
			if (secureTargetActorId != 0 && IsSecureFootholdDevelopmentReady(secureTargetActorId) &&
				pendingSecureFootholds.TryGetValue(secureTargetActorId, out var pending))
			{
				secureCell = pending.Cell;
				return true;
			}

			if (secureTargetActorId != 0 &&
				establishedSecureDefenseHoldUntil.TryGetValue(secureTargetActorId, out var until) &&
				world.WorldTick <= until && establishedSecureAnchorPoints.TryGetValue(secureTargetActorId, out var anchor))
			{
				secureCell = anchor;
				return true;
			}

			secureCell = default;
			return false;
		}

		void CleanupExpiredSecureDefenseHolds()
		{
			foreach (var id in establishedSecureDefenseHoldUntil.Keys
				.Where(id => world.WorldTick > establishedSecureDefenseHoldUntil[id]).ToArray())
				establishedSecureDefenseHoldUntil.Remove(id);
		}

		public bool IsSecureAnchor(CPos cell)
		{
			var radiusSquared = Info.SecureAlliedClaimRadius * Info.SecureAlliedClaimRadius;
			if (pendingSecureFootholds.Values.Any(p => (cell - p.Cell).LengthSquared <= radiusSquared))
				return true;

			return establishedSecureAnchorPoints.Values.Any(anchor =>
				(cell - anchor).LengthSquared <= radiusSquared);
		}

		public bool CompleteSecureFoothold(uint secureTargetActorId, CPos establishedCell, string reason)
		{
			if (!IsSecureFootholdDevelopmentReady(secureTargetActorId) || !pendingSecureFootholds.Remove(secureTargetActorId))
				return false;

			secureTargetCooldownUntil[secureTargetActorId] = world.WorldTick + Info.SecureTargetCooldownTicks;
			// The strategic ANCHOR already existed from IntelScan CLEAR. Physical development may
			// refine its exact cell to the autonomous FACT without being the event that creates it.
			establishedSecureAnchorPoints[secureTargetActorId] = establishedCell;
			completedSecureFootholds.Add(secureTargetActorId);
			establishedSecureDefenseHoldUntil[secureTargetActorId] = world.WorldTick + Info.SecureDefenseHoldTicks;
			FransBotLog.BotDebug(world,
				"{0}: GENERAL SECURE ANCHOR DEVELOPED for MineCluster {1} at {2}: {3}. The ANCHOR was created earlier by CLEAR; FACT + two armed defenses + required local TENT/BARR/WEAP are now physical. Ground SECURE already completed at CLEAR -> ANCHOR and was released immediately so the next SECURE can begin without waiting for foothold construction. {4} other undeveloped anchor(s) remain.",
				player, secureTargetActorId, establishedCell, reason ?? "FACT + support established", pendingSecureFootholds.Count);
			lastPublishedWorldTick = -1;
			return true;
		}

		void WriteStrategicAssessmentIfDue()
		{
			if (world.WorldTick < nextStrategicAssessmentTick)
				return;

			nextStrategicAssessmentTick = world.WorldTick + Info.StrategicAssessmentInterval;
			combatIntelService.EnsureCurrentSnapshot();

			if (mineClusterService == null)
			{
				FransBotLog.BotDebug(world,
					"{0}: GENERAL STRATEGIC ASSESSMENT read-only unavailable: no FransMineCluster service. DEFEND/SECURE/RECON/RAID board remains available.",
					player);
				return;
			}

			// The long game does NOT divide the whole map into arbitrary grid sectors.
			// A MineCluster is the only strategic resource sector: if no ore/gem mine exists there,
			// General has no resource-control reason to score the area in this assessment.
			var mineClusters = mineClusterService.VisibleClusters
				.Where(IsLiveMineCluster)
				.ToArray();

			var ownRefineries = combatIntelService.OwnedActors
				.Where(a => IsLiveOwnedEconomyActor(a, true))
				.ToArray();
			var ownHarvesters = combatIntelService.OwnedActors
				.Where(a => IsLiveOwnedEconomyActor(a, false))
				.ToArray();
			var friendlyRefineries = combatIntelService.VisibleActors
				.Where(a => IsLiveFriendlyEconomyActor(a, true))
				.ToArray();
			var friendlyHarvesters = combatIntelService.VisibleActors
				.Where(a => IsLiveFriendlyEconomyActor(a, false))
				.ToArray();

			var knownEnemyRefineries = combatIntelService.EnemyCombatContacts
				.Where(c => c.IsBuilding && c.ActorType != null
					&& world.Map.Rules.Actors.TryGetValue(c.ActorType, out var ri)
					&& FransActorClass.IsRefinery(ri))
				.ToArray();
			var visibleEnemyHarvesters = combatIntelService.VisibleEnemies
				.Where(a => IsLiveVisibleEnemyEconomyActor(a, false))
				.ToArray();

			var friendlyProductiveClusters = mineClusters
				.Where(c => friendlyRefineries.Any(a => IsEconomyActorNearCluster(a.Location, c)) ||
					friendlyHarvesters.Any(a => IsEconomyActorNearCluster(a.Location, c)))
				.ToArray();
			var enemyProductiveClusters = mineClusters
				.Where(c => knownEnemyRefineries.Any(e => IsEconomyActorNearCluster(e.LastSeenCell, c)) ||
					visibleEnemyHarvesters.Any(a => IsEconomyActorNearCluster(a.Location, c)))
				.ToArray();

			var friendlyClusterIds = friendlyProductiveClusters.Select(GetMineClusterKey).ToHashSet();
			var enemyClusterIds = enemyProductiveClusters.Select(GetMineClusterKey).ToHashSet();
			var contestedClusters = friendlyClusterIds.Intersect(enemyClusterIds).Count();
			var friendlyMineNodes = CountLiveMineNodes(friendlyProductiveClusters);
			var enemyMineNodes = CountLiveMineNodes(enemyProductiveClusters);

			var newestEnemyEconomyTick = -1;
			foreach (var refinery in knownEnemyRefineries)
				newestEnemyEconomyTick = Math.Max(newestEnemyEconomyTick, refinery.LastSeenWorldTick);
			if (visibleEnemyHarvesters.Length > 0)
				newestEnemyEconomyTick = world.WorldTick;

			var enemyEconomyIntelAge = newestEnemyEconomyTick >= 0
				? Math.Max(0, world.WorldTick - newestEnemyEconomyTick)
				: -1;
			var intelQuality = GetStrategicIntelQuality(enemyEconomyIntelAge);
			var resourcePosition = GetKnownResourcePosition(
				friendlyMineNodes,
				enemyMineNodes,
				friendlyProductiveClusters.Length,
				enemyProductiveClusters.Length,
				intelQuality,
				knownEnemyRefineries.Length + visibleEnemyHarvesters.Length);

			var throughputState = economicSaturationService != null
				? economicSaturationService.State.ToString()
				: "Unavailable";
			var busyQueues = economicSaturationService?.BusyQueueCount ?? -1;
			var availableQueues = economicSaturationService?.AvailableQueueCount ?? -1;
			var queueSummary = busyQueues >= 0 && availableQueues >= 0
				? $"{busyQueues}/{availableQueues}"
				: "n/a";
			var intelAgeSummary = enemyEconomyIntelAge >= 0 ? enemyEconomyIntelAge.ToString() : "none";

			FransBotLog.BotDebug(world,
				"{0}: GENERAL STRATEGIC ASSESSMENT read-only: ore-mine sectors friendly {1} ({2} mine nodes), known enemy {3} ({4} mine nodes), contested {5}; known team resource position {6}. Own economy {7} refinery/{8} harvester; throughput {9}, queues busy {10}. Enemy economy intel {11}: known refinery {12}, visible harvester {13}, newest age {14} WT. Enemy combat visible {15} value {16}; believed value {17}. MineClusters only; no full-map grid. This assessment line is diagnostic only; RECON publication is handled separately.",
				player,
				friendlyProductiveClusters.Length,
				friendlyMineNodes,
				enemyProductiveClusters.Length,
				enemyMineNodes,
				contestedClusters,
				resourcePosition,
				ownRefineries.Length,
				ownHarvesters.Length,
				throughputState,
				queueSummary,
				intelQuality,
				knownEnemyRefineries.Length,
				visibleEnemyHarvesters.Length,
				intelAgeSummary,
				combatIntelService.VisibleEnemyCombatUnitCount,
				combatIntelService.VisibleEnemyCombatValue,
				combatIntelService.EstimatedEnemyCombatValue);
		}

		bool IsLiveMineCluster(FransMineCluster cluster)
		{
			return cluster != null && cluster.Mines.Any(m => m != null && m.IsInWorld && !m.IsDead);
		}

		uint GetMineClusterKey(FransMineCluster cluster)
		{
			return cluster.Mines
				.Where(m => m != null && m.IsInWorld && !m.IsDead)
				.Select(m => m.ActorID)
				.DefaultIfEmpty(uint.MaxValue)
				.Min();
		}

		int CountLiveMineNodes(IEnumerable<FransMineCluster> clusters)
		{
			return clusters.Sum(c => c.Mines.Count(m => m != null && m.IsInWorld && !m.IsDead));
		}

		bool IsEconomyActorNearCluster(CPos location, FransMineCluster cluster)
		{
			var radiusSquared = Info.StrategicMineEconomyLinkRadius * Info.StrategicMineEconomyLinkRadius;
			return cluster.Mines.Any(m => m != null && m.IsInWorld && !m.IsDead &&
				(m.Location - location).LengthSquared <= radiusSquared);
		}

		string GetStrategicIntelQuality(int enemyEconomyIntelAge)
		{
			if (enemyEconomyIntelAge < 0)
				return "Unknown";
			if (enemyEconomyIntelAge <= Info.StrategicIntelGoodAgeTicks)
				return "Good";
			if (enemyEconomyIntelAge <= Info.StrategicIntelAgingAgeTicks)
				return "Aging";
			return "Poor";
		}

		string GetKnownResourcePosition(int friendlyMineNodes, int enemyMineNodes,
			int friendlyProductiveClusters, int enemyProductiveClusters, string intelQuality, int knownEnemyEconomyAssets)
		{
			if (knownEnemyEconomyAssets <= 0 || enemyProductiveClusters <= 0 ||
				intelQuality == "Unknown" || intelQuality == "Poor")
				return "Unknown";
			if (friendlyMineNodes > enemyMineNodes)
				return "Advantage";
			if (friendlyMineNodes < enemyMineNodes)
				return "Disadvantage";
			if (friendlyProductiveClusters > enemyProductiveClusters)
				return "Advantage";
			if (friendlyProductiveClusters < enemyProductiveClusters)
				return "Disadvantage";
			return "Parity";
		}

		bool IsLiveFriendlyEconomyActor(Actor actor, bool building)
		{
			if (actor == null || !actor.IsInWorld || actor.IsDead || actor.OccupiesSpace == null ||
				!Info.EconomyTargetTypes.Contains(actor.Info.Name) ||
				(actor.Owner != player && !PlayerRelationship.Ally.HasRelationship(player.RelationshipWith(actor.Owner))))
				return false;
			return actor.Info.HasTraitInfo<BuildingInfo>() == building;
		}

		bool IsLiveOwnedEconomyActor(Actor actor, bool building)
		{
			if (actor == null || actor.Owner != player || !actor.IsInWorld || actor.IsDead || actor.OccupiesSpace == null ||
				!Info.EconomyTargetTypes.Contains(actor.Info.Name))
				return false;
			return actor.Info.HasTraitInfo<BuildingInfo>() == building;
		}

		bool IsLiveVisibleEnemyEconomyActor(Actor actor, bool building)
		{
			if (!IsValidVisibleEnemy(actor) || !Info.EconomyTargetTypes.Contains(actor.Info.Name))
				return false;
			return actor.Info.HasTraitInfo<BuildingInfo>() == building;
		}

		public bool TryGetMission(Actor target, out FransMission mission)
		{
			EnsureCurrentMissions();
			if (target != null && missionsByActorId.TryGetValue(target.ActorID, out mission))
				return true;
			mission = default;
			return false;
		}

		public bool TryGetMission(uint targetActorId, out FransMission mission)
		{
			EnsureCurrentMissions();
			return missionsByActorId.TryGetValue(targetActorId, out mission);
		}

		public bool TryRefreshAcceptedSecureMission(uint targetActorId, out FransMission mission)
		{
			combatIntelService.EnsureCurrentSnapshot();
			if (targetActorId != 0 && commandBidService != null &&
				commandBidService.TryGetActiveMissionForTarget(targetActorId, out var active) &&
				active.MissionType == FransMissionType.Secure)
			{
				var siteIntel = BuildSiteIntel(active.LastVisibleTargetCell, Info.SecureRiskAssessmentRadius,
					Info.StrategicIntelAgingAgeTicks);
				mission = new FransMission(
					null, active.TargetActorId, active.TargetActorType, null, active.LastVisibleTargetCell,
					false, active.TargetIsBuilding, siteIntel, FransMissionType.Secure,
					active.StrategicPriority, world.WorldTick, active.MissionId);
				return true;
			}

			mission = default;
			return false;
		}

		public bool TryGetDefendIncident(uint missionId, out FransMission mission)
		{
			CleanupDefenseIncidents();
			foreach (var pair in defendIncidentMissionIds.OrderBy(p => p.Key))
			{
				if (pair.Value != missionId || !defendTargetUntil.TryGetValue(pair.Key, out var until) || world.WorldTick >= until)
					continue;

				var representative = world.GetActorById(pair.Key);
				var visibleRepresentative = IsValidVisibleEnemy(representative);
				var center = defendIncidentOrigins.TryGetValue(pair.Key, out var incidentOrigin)
					? incidentOrigin
					: representative?.Location ?? default;
				var siteIntel = visibleRepresentative
					? BuildSiteIntel(center, Info.DefenseClusterRadius, Info.DefenseMemoryTicks, representative)
					: default;
				mission = new FransMission(
					visibleRepresentative ? representative : null,
					pair.Key,
					representative?.Info?.Name ?? string.Empty,
					representative?.Owner,
					center,
					!visibleRepresentative,
					representative?.Info?.HasTraitInfo<BuildingInfo>() ?? false,
					siteIntel,
					FransMissionType.Defend,
					defendTargetPriority.TryGetValue(pair.Key, out var priority) ? priority : 0,
					world.WorldTick,
					missionId,
					defendIncidentThreatValues.TryGetValue(pair.Key, out var threatValue) ? threatValue : 0,
					defendIncidentAssetValues.TryGetValue(pair.Key, out var assetValue) ? assetValue : 0);
				return true;
			}

			mission = default;
			return false;
		}

		public bool IsDefenseTarget(Actor target)
		{
			return target != null && defendTargetUntil.TryGetValue(target.ActorID, out var until) && world.WorldTick < until;
		}

		public bool TrySelectAnchorPoint(FransCommanderKind commander, FransMissionType missionType, IReadOnlyCollection<uint> committedActorIds, Actor subject, CPos missionObjective, out CPos anchorPoint)
		{
			anchorPoint = default;
			if (subject == null || !subject.IsInWorld || subject.IsDead || strategicMapService == null || riskModelService == null)
				return false;

			// Ground SECURE assembly is a property of the committed force, not of one bid subject
			// or the previous territorial anchor. Pick a safe medoid from the exact committed
			// snapshot so the 80% assembly gate concentrates units where the army already is.
			if (commander == FransCommanderKind.Ground && missionType == FransMissionType.Secure && committedActorIds != null)
			{
				var committed = committedActorIds
					.Select(id => world.GetActorById(id))
					.Where(a => a != null && a.IsInWorld && !a.IsDead && a.Owner == player)
					.OrderBy(a => a.ActorID)
					.ToArray();
				if (committed.Length > 0)
				{
					var forceAnchor = committed
						.Select(a => new
						{
							Actor = a,
							Spread = committed.Sum(b => (long)Math.Abs(a.Location.X - b.Location.X) + Math.Abs(a.Location.Y - b.Location.Y)),
							MissionDistance = Math.Abs(a.Location.X - missionObjective.X) + Math.Abs(a.Location.Y - missionObjective.Y)
						})
						.OrderBy(x => x.Spread)
						.ThenBy(x => x.MissionDistance)
						.ThenBy(x => x.Actor.ActorID)
						.Select(x => (CPos?)x.Actor.Location)
						.FirstOrDefault(c => c.HasValue && !riskModelService.EvaluateStrategicCell(c.Value, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced).IsCritical);

					if (forceAnchor.HasValue)
					{
						anchorPoint = forceAnchor.Value;
						FransBotLog.BotDebug(world,
							"{0}: GENERAL assigns FORCE-AWARE Ground SECURE assembly ANCHOR {1} for objective {2}; medoid selected from {3} exact committed actors instead of reusing an unrelated historical anchor.",
							player, anchorPoint, missionObjective, committed.Length);
						return true;
					}
				}
			}

			if (commander == FransCommanderKind.Air)
			{
				// Cameo port: upstream split helipad (hpad) vs airfield (afld) by RA aircraft id.
				// Both are "air producers"; use the nearest own building that produces aircraft.
				var service = world.ActorsHavingTrait<Building>()
					.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player)
					.Where(a => FransActorClass.IsAircraft(subject.Info)
						&& a.Info.TraitInfos<ProductionInfo>().Any(p =>
							p.Produces.Any(q => q.Contains("aircraft", StringComparison.OrdinalIgnoreCase)
								|| q.Contains("plane", StringComparison.OrdinalIgnoreCase)
								|| q.Contains("helicopter", StringComparison.OrdinalIgnoreCase))))
					.OrderBy(a => (a.Location - subject.Location).LengthSquared)
					.ThenBy(a => a.ActorID)
					.FirstOrDefault();
				if (service == null)
					return false;

				anchorPoint = service.Location;
				FransBotLog.BotDebug(world,
					"{0}: GENERAL assigns AIR ANCHOR {1} at {2} for {3} {4}; Air uses its nearest compatible aircraft-production base and never a generic StrategicMap ground anchor.",
					player, service.Info.Name, anchorPoint, subject.Info.Name, subject.ActorID);
				return true;
			}

			if (commander == FransCommanderKind.Ground && TryGetLatestGroundAnchor(out anchorPoint))
			{
				FransBotLog.BotDebug(world,
					"{0}: GENERAL assigns latest successful SECURE ANCHOR {1} for Ground mission objective {2}. DEFEND may temporarily pull units away but never moves this ANCHOR.",
					player, anchorPoint, missionObjective);
				return true;
			}

			var movementLayer = commander == FransCommanderKind.Sea
				? FransStrategicMovementLayer.Naval
				: FransStrategicMovementLayer.Ground;
			var riskRole = commander switch
			{
				FransCommanderKind.Air => FransRiskRole.Aircraft,
				FransCommanderKind.Sea => FransRiskRole.NavalCombat,
				FransCommanderKind.SpecOps => FransRiskRole.Capturer,
				_ => FransRiskRole.GroundCombat
			};

			var candidates = new List<FransAnchorPointCandidate>();
			foreach (var secured in establishedSecureAnchorPoints.OrderBy(kv => kv.Key))
			{
				if (!strategicMapService.TryGetSector(secured.Value, out var sector) ||
					!strategicMapService.TryGetSectorMetrics(secured.Value, out var securedMetrics) ||
					securedMetrics.OwnControlScore <= 0 ||
					securedMetrics.OwnControlScore < securedMetrics.EnemyControlScore)
					continue;
				CPos? resolved = movementLayer == FransStrategicMovementLayer.Naval
					? sector.NavalCenter
					: sector.GroundCenter;
				if (resolved.HasValue)
					candidates.Add(new FransAnchorPointCandidate(resolved.Value, FransAnchorPointKind.SecuredFoothold, 10000));
			}

			candidates.AddRange(strategicMapService.GetAnchorPointCandidates(movementLayer, 32));
			if (candidates.Count == 0)
				return false;

			var bestScore = long.MinValue;
			var found = false;
			var seen = new HashSet<CPos>();
			foreach (var candidate in candidates)
			{
				if (!seen.Add(candidate.Cell) || !world.Map.Contains(candidate.Cell))
					continue;

				var localRisk = riskModelService.EvaluateStrategicCell(candidate.Cell, riskRole, FransRiskTolerance.Balanced);
				if (localRisk.IsCritical)
					continue;
				var routeRisk = riskModelService.EvaluateDirectRoute(subject, subject.Location, candidate.Cell, riskRole, FransRiskTolerance.Balanced);
				if (routeRisk.IsCritical)
					continue;

				var kindScore = candidate.Kind switch
				{
					FransAnchorPointKind.SecuredFoothold => 6000,
					FransAnchorPointKind.Base => 5000,
					FransAnchorPointKind.Choke => 3500,
					_ => 2000
				};
				var distanceToMission = Math.Abs(candidate.Cell.X - missionObjective.X) + Math.Abs(candidate.Cell.Y - missionObjective.Y);
				var distanceFromSubject = Math.Abs(candidate.Cell.X - subject.Location.X) + Math.Abs(candidate.Cell.Y - subject.Location.Y);
				var score =
					(long)kindScore * 100000L +
					(long)candidate.StrategicScore * 100L -
					(long)distanceToMission * 30L -
					(long)distanceFromSubject * 10L -
					(long)localRisk.Score * 20L -
					(long)routeRisk.PeakScore * 30L;

				if (found && score <= bestScore)
					continue;
				bestScore = score;
				anchorPoint = candidate.Cell;
				found = true;
			}

			if (found)
				FransBotLog.BotDebug(world,
					"{0}: GENERAL assigns ANCHOR POINT {1} for {2} mission objective {3}; StrategicMap supplied the natural candidate and RiskModel validated the recovery route.",
					player, anchorPoint, commander, missionObjective);
			return found;
		}

		static int GetTargetValue(Actor actor) => Math.Max(1, actor?.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1);

		int GetDefendedAssetPriority(Actor owned)
		{
			if (owned == null)
				return 0;
			var type = owned.Info.Name;
			if (Info.CommandTargetTypes.Contains(type))
				return Info.CommandTargetPriority;
			if (Info.SuperweaponTargetTypes.Contains(type))
				return Info.SuperweaponTargetPriority;
			if (Info.EconomyTargetTypes.Contains(type))
				return Info.EconomyTargetPriority;
			if (Info.ProductionTargetTypes.Contains(type))
				return Info.ProductionTargetPriority;
			if (Info.TechTargetTypes.Contains(type))
				return Info.TechTargetPriority;
			if (Info.SupportAssetTypes.Contains(type))
				return Info.SupportAssetDefensePriority;
			if (owned.Info.HasTraitInfo<BuildingInfo>())
				return Info.OtherOwnedStructureDefensePriority;
			return 0;
		}

		int GetVisibleEnemyPressure(CPos center, Player preferredEnemy, out int mobileThreats)
		{
			mobileThreats = 0;
			var radiusSquared = Info.DefenseClusterRadius * Info.DefenseClusterRadius;
			foreach (var enemy in combatIntelService.VisibleEnemies)
			{
				if (!IsValidVisibleEnemy(enemy) || !combatIntelService.IsCombatThreat(enemy) || !enemy.Info.HasTraitInfo<MobileInfo>())
					continue;
				if (preferredEnemy != null && enemy.Owner != preferredEnemy)
					continue;
				if ((enemy.Location - center).LengthSquared <= radiusSquared)
					mobileThreats++;
			}

			combatIntelService.EstimateEnemyCombatValueNear(center, Info.DefenseClusterRadius, preferredEnemy,
				out var visibleValue, out _);
			return visibleValue;
		}

		bool TryFastRefreshSameAttackerDefenseIncident(Actor attacker)
		{
			if (attacker == null || !defendTargetUntil.TryGetValue(attacker.ActorID, out var previousUntil) ||
				world.WorldTick >= previousUntil || !defendIncidentOrigins.TryGetValue(attacker.ActorID, out var origin))
				return false;

			var radiusSquared = Info.DefenseIncidentMergeRadius * Info.DefenseIncidentMergeRadius;
			if ((origin - attacker.Location).LengthSquared > radiusSquared)
				return false;
			if (!defendIncidentLastAssessmentTicks.TryGetValue(attacker.ActorID, out var lastAssessmentTick) ||
				world.WorldTick - lastAssessmentTick >= Info.DefenseIncidentReassessmentInterval)
				return false;

			defendTargetUntil[attacker.ActorID] = world.WorldTick + Info.DefenseMemoryTicks;

			// If the actor reappeared after a visibility gap, force one board refresh so the live DEFEND mission
			// returns. While it is already published, do not rebuild the board for each damage callback.
			var currentlyPublished = missionsByActorId.TryGetValue(attacker.ActorID, out var publishedMission) &&
				publishedMission.Type == FransMissionType.Defend;
			if (!currentlyPublished)
				lastPublishedWorldTick = -1;

			return true;
		}

		bool TryRefreshSameAttackerDefenseIncident(Actor attacker, int until, int defensePriority, int visibleThreatValue, int defendedAssetValue)
		{
			if (attacker == null || !defendTargetUntil.TryGetValue(attacker.ActorID, out var previousUntil))
				return false;

			if (world.WorldTick >= previousUntil)
			{
				RemoveDefenseIncident(attacker.ActorID);
				return false;
			}

			var previousPriority = defendTargetPriority.TryGetValue(attacker.ActorID, out var p) ? p : 0;
			defendTargetUntil[attacker.ActorID] = Math.Max(previousUntil, until);
			defendTargetPriority[attacker.ActorID] = Math.Max(previousPriority, defensePriority);
			defendIncidentThreatValues[attacker.ActorID] = Math.Max(
				defendIncidentThreatValues.TryGetValue(attacker.ActorID, out var previousThreat) ? previousThreat : 0,
				visibleThreatValue);
			defendIncidentAssetValues[attacker.ActorID] = Math.Max(
				defendIncidentAssetValues.TryGetValue(attacker.ActorID, out var previousAsset) ? previousAsset : 0,
				defendedAssetValue);
			defendIncidentLastAssessmentTicks[attacker.ActorID] = world.WorldTick;

			// Do not rebuild the General board for every bullet/burst callback while this same actor is already
			// the published DEFEND target. Rebuild only when it reappears after a visibility gap (there is no
			// current DEFEND mission) or when the observed pressure raises strategic priority.
			var currentlyPublished = missionsByActorId.TryGetValue(attacker.ActorID, out var publishedMission) &&
				publishedMission.Type == FransMissionType.Defend;
			if (!currentlyPublished || defensePriority > previousPriority)
				lastPublishedWorldTick = -1;

			return true;
		}

		uint? FindNearbyDefenseIncidentRepresentativeId(CPos attackCell)
		{
			var radiusSquared = Info.DefenseIncidentMergeRadius * Info.DefenseIncidentMergeRadius;
			foreach (var pair in defendTargetUntil.OrderBy(p => p.Key))
			{
				if (world.WorldTick >= pair.Value)
					continue;
				if (defendIncidentOrigins.TryGetValue(pair.Key, out var origin) &&
					(origin - attackCell).LengthSquared <= radiusSquared)
					return pair.Key;
			}
			return null;
		}


		uint EnsureDefenseIncidentMissionId(uint representativeActorId)
		{
			if (representativeActorId == 0)
				return 0;
			if (defendIncidentMissionIds.TryGetValue(representativeActorId, out var existing))
				return existing;

			// Reserve the high half of uint for synthetic strategic incident identity. Actor IDs remain
			// tactical target data, so representative swaps do not restart the Broker bid window.
			do
			{
				nextDefenseIncidentSequence = (nextDefenseIncidentSequence + 1u) & 0x7FFFFFFFu;
			}
			while (nextDefenseIncidentSequence == 0);

			var missionId = 0x80000000u | nextDefenseIncidentSequence;
			defendIncidentMissionIds[representativeActorId] = missionId;
			return missionId;
		}

		void CleanupDefenseIncidents()
		{
			foreach (var id in defendTargetUntil.Keys.ToArray())
				// Representative death/visibility does not erase strategic incident identity. The next
				// nearby observed attacker inherits it; only the defense-memory lease expires the incident.
				if (world.WorldTick >= defendTargetUntil[id])
					RemoveDefenseIncident(id);
		}

		void RemoveDefenseIncident(uint actorId)
		{
			defendTargetUntil.Remove(actorId);
			defendTargetPriority.Remove(actorId);
			defendIncidentOrigins.Remove(actorId);
			defendIncidentMissionIds.Remove(actorId);
			defendIncidentThreatValues.Remove(actorId);
			defendIncidentAssetValues.Remove(actorId);
			defendIncidentLastAssessmentTicks.Remove(actorId);
		}

		void ClearDefenseIncidents()
		{
			defendTargetUntil.Clear();
			defendTargetPriority.Clear();
			defendIncidentOrigins.Clear();
			defendIncidentMissionIds.Clear();
			defendIncidentThreatValues.Clear();
			defendIncidentAssetValues.Clear();
			defendIncidentLastAssessmentTicks.Clear();
			nextDefenseIncidentSequence = 0;
		}

		bool IsValidVisibleEnemy(Actor target)
		{
			if (target == null || !target.IsInWorld || target.IsDead || target.OccupiesSpace == null ||
				!target.CanBeViewedByPlayer(player) || !PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(target.Owner)))
				return false;

			var type = target.Info.Name;
			return !target.Info.HasTraitInfo<HuskInfo>() &&
				!type.EndsWith(".husk", StringComparison.OrdinalIgnoreCase) &&
				!type.EndsWith("husk", StringComparison.OrdinalIgnoreCase);
		}
	}
}
