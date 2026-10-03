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
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	public enum BotUrgency { Normal, Pressured, Emergency }

	public sealed class EnemyProfile
	{
		public OpenRA.Player Player;
		public string Name;
		public string FactionName;
		public bool Alive;
		public int ArmyValue;

		// §12.14 PL: net seen army growth since the previous snapshot (can go negative; 0 on the first).
		public int ArmyValueDelta;
		public int InfantryValue, VehicleValue, AirValue, NavalValue;
		public int DefenceCount, DefenceValue;
		public int TechBuildings;
		public int ProductionBuildings;
		public int BuildingCount;
		public int ExpansionClusters;
		public int Harvesters, Refineries;
		public int HarvesterCount;
		public int KnownRegions;
		public int PressureValue;
		public int StealthShare;
		public int NearestCells;
		public int LastSeenTick;
		public int Score;
	}

	public sealed class CounterDemand
	{
		public int AntiAir, AntiArmour, AntiInfantry, Detector, Artillery;
	}

	public sealed class BotSituation
	{
		public int Tick;
		public OpenRA.Player MainTarget;
		public string Personality = "";
		public BotUrgency Urgency;
		public IReadOnlyDictionary<OpenRA.Player, EnemyProfile> Enemies;
		public CounterDemand Demand;
		public BotMission Mission;
		public BotMissionAssignment MissionAssignment;
		public int DefenceFractionHint, ExpansionAppetiteHint;

		// ZG-c: spatial value memory. Index space is either the fixed square grid or — when this
		// bot has an enabled, built TacticalMapBotModule and UseZoneTopology is on — that zone
		// topology's region ids (check Regions.ZoneBacked/Generation before assuming geometry).
		public RegionMemory Regions;

		// IM-1 (AI_DEEP_RESEARCH §3.3): the per-region influence layers — threat_ground/threat_air
		// (remembered enemy value decaying toward a per-zone average), interest, own strength and
		// staleness — published in Regions' index space. Live handle like FogMemory: republished in
		// place every snapshot. Null when UseInfluenceLayers is off.
		public IBotInfluenceMap Influence;
		internal int OwnArmyValue, OwnDefenceValue, OwnBuildings, OwnHarvesters;
		internal int OwnKillsCostWindow, OwnDeathsCostWindow;
		internal int SquadCount, SquadUnitCount;

		// Record-only combat prediction (AI_DEEP_RESEARCH.md §2.3, phase CP): the square-law ratio x100 of the own
		// army against the enemy army this bot REMEMBERS, and against that army plus remembered defences.
		// Above 100 the own side is predicted to win. No decision reads these yet.
		internal int CombatRatioPct, CombatRatioDefendedPct;

		// ZG-b (zone territory/ownership): the fog-memory tables this snapshot's profiles were built
		// from. Live handle, not a copy — but the tables only change inside MasterAiBotModule.Rebuild
		// (Observe runs there), so a read between snapshots sees exactly what the last snapshot saw.
		// Null before the first snapshot; stays empty when UseFoggedObservation is off, which is the
		// honest answer there ("we have seen nothing"), not an error.
		internal BotFogMemory FogMemory;

		/// <summary>
		/// This bot's remembered actors of one enemy — BELIEF under fog, possibly stale, empty when
		/// nothing of theirs was ever seen. The fog-honest replacement for enumerating their actors
		/// live (the donor's omniscient `world.Actors` scans).
		/// </summary>
		internal IReadOnlyCollection<ObservedActor> Remembered(OpenRA.Player enemy) =>
			FogMemory == null ? [] : FogMemory.Remembered(enemy);

		// §12.14 personality-lead telemetry (record-only): Steamroller's out-produce side is the
		// arsenal ledger's created-cost delta per game minute; Rush's pressure side is the
		// cumulative offensive-squad launches, their per-minute rate and first launch tick, plus
		// the seen-cost of enemy economy types (harvester/refinery) this bot's units destroyed.
		internal long ProductionValueWindow, ProductionPerGameMin;
		internal long EnemyEconValueDestroyedWindow, EnemyEconValueDestroyedTotal, AttacksPerGameMin;
		internal int AttacksLaunched, FirstAttackTick = -1;

		// §12.14 PL-1 leads, computed on every snapshot (UsePersonalityLeads gates only the
		// consumers): the remembered enemy production estimate behind Steamroller (cost per
		// game minute — positive army growth plus the per-seen-production-building proxy),
		// Steamroller's out-produce ratio own/enemy (1 when nothing of the enemy is
		// remembered — no denominator means at-target, not infinite or zero), and Rush's
		// pressure score (min of the launch-rate and first-attack-timing scores; 0 until
		// the first launch).
		internal long EnemyProductionPerGameMin;
		internal double SteamrollerLead = 1, RushLead;
		// §12.14 Guerrilla map-control lead (record-only): regions where this bot holds fresh
		// intel (seen within ScoutBotModule's StaleAfterTicks horizon — empty-but-visible counts,
		// a region we look at and find empty IS fresh information), the total region count, and
		// the union across enemies of regions with remembered enemy presence. GuerrillaLead is
		// the lead ratio own-fresh/enemy-presence — 1 (at-target) while no enemy region is
		// remembered, matching Steamroller's unseen-enemy convention.
		internal int RegionsFresh, RegionsTotal, RegionsEnemyPresence;
		internal double GuerrillaLead = 1;
		// §13.1 discipline telemetry (record-only): the "never do" failures a top-tier bot
		// drives to zero — banked cash (Cash+Resources at snapshot), brownout ticks
		// (ExcessPower < 0), and idle-production ticks (per enabled queue sitting with no
		// current item and nothing queued — each idle factory counts separately).
		// Own-side scalars only; a disabled master never accumulates and publishes zeros.
		internal long BankedCash, BrownoutTicks, IdleProductionTicks;
		internal int ProductionQueues;

		// RV1 (AI_MASTER_PLAN §3, DESIGN §19.3), cumulative: repair orders the one repair owner sent on a hit and
		// from its sweep, and the hits where master's second repair module would have toggled a repair back OFF.
		internal int RepairOrders, RepairSweepOrders, RepairTogglesAvoided;

		// Phase DF step 1 (AI_DEEP_RESEARCH.md §14), record-only: the enemy groups seen this snapshot, heaviest
		// first, with their tracked velocity and, when moving, the own asset they head for and when.
		internal List<(BotThreatTracker.Group Group, BotThreatTracker.Prediction? Prediction)> Threats = new();

		// Cumulative unit losses by the role the unit held (squad type or "idle"), and the part lost
		// away from the base; summed over every squad manager, disabled personalities included.
		internal SortedDictionary<string, int> LossesByRole = new(StringComparer.Ordinal), AwayLossesByRole = new(StringComparer.Ordinal);
		internal string OwnPersonality = "";

		// UT-1 (AI_DEEP_RESEARCH.md §5.1), record-only: the bipolar posture axes as of this
		// snapshot, each [0,100] with 100 the SECOND-named pole. Consumers read them through
		// IBotUtilityAxes on the master module, not from here.
		internal int UtilityTurtleRush = IBotUtilityAxes.Neutral;
		internal int UtilityTechRushExpansion = IBotUtilityAxes.Neutral;
		internal int UtilitySteamrollerGuerrilla = IBotUtilityAxes.Neutral;
		// DI-1 (AI_ARCHITECTURE §12.16), record-only: the pacing Director's tension [0,100]
		// and wave phase as of this snapshot. Nothing consumes them; DI-2 adds the
		// attack-timing consumer (pacing and aggression only — DESIGN §19.2).
		internal int DirectorTension;
		internal DirectorPhase DirectorPhase;

		// ST (DESIGN 19.10, AI_ARCHITECTURE 12.22), record-only: the scale-targets inputs and targets of the provider's
		// last recompute. Null (and omitted from the log) while no ScaleTargetsBotModule is enabled.
		internal ScaleTargetsSnapshot ScaleTargets;

		// BO-1 (AI_ARCHITECTURE 12.25), record-only: the build-order knob vector, opening and react events of the provider's last update.
		// Null (and omitted from the log) while no BuildOrderKnobsBotModule is enabled.
		internal BuildOrderSnapshot BuildOrder;
		// FE-0 (AI_ARCHITECTURE 12.24), record-only: the field-economy picture as of this snapshot (the `expansion` object).
		internal ExpansionSnapshot Expansion;

		// TC-1 (AI_ARCHITECTURE §12.17), record-only: the allied team blackboard as of
		// this snapshot — the caller's own broadcast is never folded in, so these read
		// the allies' half only; all zeros in 1v1 or without an allied bot.
		internal int TeamAlliedBots, TeamArmyValue, TeamMaxTension, TeamDefendRequests, TeamSharedTarget, TeamAnyClimax;

		// TC-3 (AI_ARCHITECTURE §12.18), record-only: the folded coalition directive as of
		// this snapshot — the team phase ordinal (0 BuildUp, 1 Push, 2 Defend) and the
		// shared MainTarget's name. BuildUp/"" while UseCoalitionPlan is off, which is the
		// Empty directive's honest answer.
		internal int CoalitionPhase;
		internal string CoalitionMainTarget = "";
	}

	internal sealed class MasterAiBotSavedState
	{
		public bool CostCountersInitialized;
		public int PreviousDeathsCost;
		public int PreviousKillsCost;
		public BotUrgency CurrentUrgency;
		public int LastPersonalitySwitchTick;
		public int PersonalityCandidateSince;
		public string PersonalityCandidate = "";
		public bool EmergencyPersonalityHandled;
		public Dictionary<string, int> CounterDemandCandidateSince = new(StringComparer.Ordinal);
		public string[] LastIssuedCounterDemands = Array.Empty<string>();
		public (int Tick, int Delta)[] LossSamples = Array.Empty<(int, int)>();
		public (int Tick, int Delta)[] KillSamples = Array.Empty<(int, int)>();
		public int[] ProductionLossTicks = Array.Empty<int>();
		public uint[] ProductionBuildings = Array.Empty<uint>();
	}

	public class MasterAiBotModuleInfo : ConditionalTraitInfo
	{
		public readonly BitSet<TargetableType> InfantryTargetTypes = new("Infantry");
		public readonly BitSet<TargetableType> VehicleTargetTypes = new("Vehicle");
		public readonly BitSet<TargetableType> NavalTargetTypes = new("Water", "Ship");
		public readonly BitSet<TargetableType> DefenceTargetTypes = new("Defense");

		[Desc("Value per unit of garrison weight of an enemy-held garrisonable building that has no Valued cost",
			"(the civilian houses), so fog memory prices the garrison, not the house (AI_ARCHITECTURE §12.12).",
			"0 keeps the house's own cost, which is none.")]
		public readonly int GarrisonOccupantValue = 0;

		public readonly int ClusterRadius = 12;
		public readonly int PressureRadius = 15;
		public readonly int LossWindowTicks = 750;
		public readonly int EmergencyLossThreshold = 600;

		[Desc("Loss-window value below which an active emergency de-escalates. Kept below " +
			"EmergencyLossThreshold so the urgency state has on/off hysteresis — a window " +
			"bouncing across a single threshold flickered Emergency on and off every check " +
			"interval, which starved the sustained-candidate timer and latched the " +
			"personality (observed: turtle held ~38k ticks while the candidate stayed rush).")]
		public readonly int EmergencyLossClearThreshold = 300;

		[Desc("Emergency means LOSING (maintainer ruling 2026-10-03, AI_ARCHITECTURE open question 10). " +
			"0 keeps the legacy rule: a loss window above EmergencyLossThreshold alone is an emergency. " +
			"Above 0 the loss branch also needs losses > this percentage of (current own army + losses in the " +
			"window), so a wiped army reads 100%, AND a net loss (deaths > kills in the same window). " +
			"EmergencyLossThreshold stays as an absolute floor; a lost production building still triggers. " +
			"An active emergency clears at half this percentage (or once the window is no longer a net loss).")]
		public readonly int EmergencyLossArmyPct = 0;

		[Desc("When true an emergency changes urgency (and what keys off it) but never the personality: " +
			"no forced turtle at the transition and no turtle candidate just because urgency is Emergency; " +
			"candidates proceed as under Pressured. False keeps the legacy emergency-turtle override.")]
		public readonly bool EmergencyKeepsPersonality = false;
		public readonly int PressuredArmyRatio = 60;
		public readonly int EmergencyCheckInterval = 25;
		public readonly int SnapshotInterval = 150;
		public readonly int DecisionInterval = 1500;
		public readonly int WeightReach = 250;
		public readonly int WeightWeak = 200;
		public readonly int WeightEcon = 150;
		public readonly int WeightKill = 100;
		public readonly int WeightDefence = 150;
		public readonly int WeightAlly = 100;

		[Desc("CA-6 (§12.9): remembered static defences join the enemy force the own",
			"army must outmass for a target to be 'beatable' — weak measures",
			"ownArmy vs ArmyValue + DefenceValue instead of ArmyValue alone.",
			"False = pre-CA-6 scoring, bit-identical.")]
		public readonly bool WeakIncludesDefence = false;

		[Desc("CA-2c (§12.6 rule 5): world ticks a failed-siege memory stays fresh.",
			"Older entries contribute no avoidance weight. ~30 game-minutes at",
			"standard speed.")]
		public readonly int SiegeFailureMemoryTicks = 45000;

		[Desc("CA-2c: remembered-obstacle weight added per failed siege against the",
			"region, percent — the wall reads 25% heavier per failed attempt.")]
		public readonly int SiegeFailureWeightPercent = 25;

		[Desc("w_hurt weight: an enemy winning the exchange against us loses target score (§4.3).",
			"hurt = taken/(taken+dealt) — the bounded share form of the spec's dealt/taken",
			"ratio, so 'damage dealt to us' only penalises once we have fought back some too.")]
		public readonly int WeightHurt = 150;

		[Desc("CA-6 (§12.9): intel-freshness weight — the score penalty grows toward the",
			"never-seen maximum as a sighting ages past IntelStaleTicks. Freshly-scouted",
			"enemies win over forgotten ones, so scouting and target choice close the loop.",
			"0 = pre-CA-6 scoring, bit-identical.")]
		public readonly int WeightIntelAge = 0;

		[Desc("World ticks until a sighting counts as fully stale for WeightIntelAge.")]
		public readonly int IntelStaleTicks = 4500;

		[Desc("Nemesis score that counts as 'actively killing our base' — mandatory re-target,",
			"bypassing the decision interval and the incumbent hold (§4.3 override).")]
		public readonly int NemesisOverrideWeight = 60;
		public readonly int IncumbentMomentum = 75;
		public readonly int MinimumHoldTicks = 3000;
		public readonly int FortifiedDefenceCount = 6;
		public readonly int SteamrollerMinArmyValue = 3000;
		public readonly int GuerrillaMinClusters = 3;
		public readonly int TechEnemyTechBuildings = 4;
		public readonly int RushMaxEnemyArmyValue = 1500;
		public readonly int RushMaxEnemyDefenceCount = 2;
		public readonly int EliminationBuildingSaturation = 8;
		public readonly int PersonalityHoldTicks = 3000;
		[Desc("Fallback reaction delay in ticks when the bot player has no enabled BotLimits. Negative disables personality switching and counter demand.")]
		public readonly int DefaultPersonalityReactionDelay = 7500;
		[Desc("Signal threshold to enable anti-air counter demand.")]
		public readonly int AntiAirDemandOn = 25;
		[Desc("Signal threshold below which held anti-air counter demand is removed.")]
		public readonly int AntiAirDemandOff = 15;
		[Desc("Signal threshold to enable anti-armour counter demand.")]
		public readonly int AntiArmourDemandOn = 40;
		[Desc("Signal threshold below which held anti-armour counter demand is removed.")]
		public readonly int AntiArmourDemandOff = 30;
		[Desc("Signal threshold to enable anti-infantry counter demand.")]
		public readonly int AntiInfantryDemandOn = 40;
		[Desc("Signal threshold below which held anti-infantry counter demand is removed.")]
		public readonly int AntiInfantryDemandOff = 30;
		[Desc("Signal threshold to enable detector counter demand.")]
		public readonly int DetectorDemandOn = 20;
		[Desc("Signal threshold below which held detector counter demand is removed.")]
		public readonly int DetectorDemandOff = 10;
		[Desc("Signal threshold to enable artillery counter demand.")]
		public readonly int ArtilleryDemandOn = 40;
		[Desc("Signal threshold below which held artillery counter demand is removed.")]
		public readonly int ArtilleryDemandOff = 25;
		[Desc("Limit enemy observations to what the bot player can see plus remembered sightings. False reproduces the legacy omniscient scan.")]
		public readonly bool UseFoggedObservation = true;
		[Desc("Cell-edge length of one spatial memory region.")]
		public readonly int RegionCellSize = 8;
		[Desc("ZG-c: index spatial memory and threat routing by the TacticalMapBotModule's zone graph",
			"(one region per chokepoint-bounded pocket of ground) whenever an enabled, built topology",
			"exists; the square RegionCellSize grid stays the fallback. False forces the grid always.")]
		public readonly bool UseZoneTopology = false; // off until the next increment A/B (WORKFLOW §3; group D)
		[Desc("IM-1 (AI_DEEP_RESEARCH §3.3): publish per-region influence layers (threat_ground,",
			"threat_air, interest, own_strength, staleness) on each situation snapshot, so",
			"consumers read one publisher instead of re-deriving RegionMemory. Off until the",
			"next increment A/B (same convention as UseZoneTopology; switch group F).")]
		public readonly bool UseInfluenceLayers = false;
		[Desc("IM-1: EMA weight percent per snapshot on each zone's remembered-threat history —",
			"the 'where they usually are' average a stale sighting decays toward.")]
		public readonly int InfluenceHistoryAlphaPercent = 20;
		[Desc("IM-1: staleness horizon in ticks at which a published threat is fully the zone",
			"history rather than the last sighting.")]
		public readonly int InfluenceDecayTicks = 7500;
		[Desc("IM-1: staleness a region reports when no enemy memory has ever seen it",
			"(mirrors ScoutBotModule.StaleAfterTicks).")]
		public readonly int InfluenceStaleAfterTicks = 2500;
		[Desc("IM-1: percent of each neighbour region's believed threat that bleeds across the",
			"boundary — a remembered unit's reach covers the ground past the gate it holds.",
			"One adjacency hop only; 0 disables the spread.")]
		public readonly int InfluenceSpreadPercent = 50;
		[Desc("Offer squads coarse waypoints that skirt regions with remembered enemy threat (6e risk routing). Squads fall back to direct routing when this is off.")]
		public readonly bool UseRiskRouting = true;
		[Desc("Remembered enemy value that makes one region cost an extra hop to route through. Lower = squads skirt weaker threats.")]
		public readonly int RiskRoutingThreatWeight = 1000;
		[Desc("Ticks after which a remembered non-building that was never seen again is dropped.")]
		public readonly int ObservationTimeoutTicks = 30000;

		[Desc("DF threat tracking: enemy combat units within this many cells of a group's centre join that group.")]
		public readonly int ThreatGroupRadiusCells = 10;

		[Desc("DF threat tracking: a group keeps its identity (and gets a velocity) if last snapshot's group was this close.")]
		public readonly int ThreatMatchRadiusCells = 30;

		[Desc("DF threat tracking: the predicted target must lie within this cone around the heading (cosine x100).")]
		public readonly int ThreatConeCosPercent = 70;

		[Desc("DF threat tracking: slower than this (cells per 1000 ticks) counts as standing, with no prediction.")]
		public readonly int ThreatMinSpeedCellsPerKiloTick = 10;

		[Desc("DF threat tracking: how many of the heaviest groups the situation log records.")]
		public readonly int ThreatsLogged = 3;
		[Desc("Publish fog-honest Raid and Defend missions from the latest situation snapshot.")]
		public readonly bool PublishMissions = true;
		[Desc("Percentage of remembered enemy army and defence value required before attempting a Raid.")]
		public readonly int RaidForceRatioPercent = 120;
		[Desc("LC8: consecutive failed attempts (units lost) of one mission id before it goes on the dormant shelf. 0 = off.")]
		public readonly int RaidFailuresBeforeDormant = 0;
		[Desc("LC8: ticks a dormant mission stays off the shelf of published missions before it is reopened.")]
		public readonly int RaidDormantTicks = 4500;
		[Desc("Minimum Raid priority required before publishing a mission.")]
		public readonly int RaidPriorityThreshold = 40;
		[Desc("Minimum Defend priority required before publishing a mission.")]
		public readonly int DefendPriorityThreshold = 25;
		[Desc("Ticks for which a taken mission pair remains reserved from other consumers.")]
		public readonly int MissionReservationTicks = 1500;

		[Desc("PL-1 (§12.14): while this bot's personality lead trails its target, lean that",
			"personality's budget knobs toward the lead's driver — Steamroller relaxes the",
			"unit builder's cash floors, Rush shortens the squad attack-force delay.",
			"The leads themselves are computed on every snapshot either way.")]
		public readonly bool UsePersonalityLeads = false; // off until the next increment A/B (WORKFLOW §3; group G)

		[Desc("PL-1: assumed enemy output per seen production building, cost per game",
			"minute, inside the Steamroller lead's enemy-side estimate.")]
		public readonly int PersonalityLeadEnemyProductionPerBuildingPerMin = 200;

		[Desc("PL-1: Rush lead target — offensive-squad launches per game minute that read as at-target pressure.")]
		public readonly double PersonalityLeadRushAttacksPerGameMinTarget = 2;

		[Desc("PL-1: Rush lead target — a first attack at or before this tick reads as on time.")]
		public readonly int PersonalityLeadRushFirstAttackTargetTick = 4500;

		[Desc("PL-1: cap, percent, on how far a trailing lead may move a consumer knob.")]
		public readonly int PersonalityLeadMaxLeanPercent = 50;

		[Desc("UT-1 (AI_DEEP_RESEARCH.md §5.1): per-personality resting point of the",
			"Turtle<->Rush utility axis on [0,100] — 100 = Rush. Keyed by personality name",
			"(rush, turtle, ...); a personality missing here rests at the 50 neutral point.")]
		public readonly Dictionary<string, int> UtilityTurtleRushRest = new(StringComparer.Ordinal);

		[Desc("UT-1: per-personality resting point of the TechRush<->Expansion axis,",
			"100 = Expansion. Same keying and neutral default as UtilityTurtleRushRest.")]
		public readonly Dictionary<string, int> UtilityTechRushExpansionRest = new(StringComparer.Ordinal);

		[Desc("UT-1: per-personality resting point of the Steamroller<->Guerrilla axis,",
			"100 = Guerrilla. Same keying and neutral default as UtilityTurtleRushRest.")]
		public readonly Dictionary<string, int> UtilitySteamrollerGuerrillaRest = new(StringComparer.Ordinal);

		[Desc("UT-1: percent of the distance to each axis target (rest + inputs) the published",
			"axis travels per snapshot — the EMA that decays an axis back to rest once its",
			"inputs go quiet. 0 freezes the axes at their starting point, 100 tracks instantly.")]
		public readonly int UtilityAxisDecayPercent = 5;

		[Desc("UT-1: percent scaling on each axis's summed input terms before they move the",
			"target off its rest. 0 pins every axis at rest (pure personality), 100 = the",
			"documented term caps.")]
		public readonly int UtilityInputWeightPercent = 100;

		[Desc("TC-2d (AI_ARCHITECTURE §12.17): role split — allied bots spread their TechRush<->Expansion",
			"rest by ClientIndex rank (lowest takes the Expansion pole, highest TechRush), so a mirrored",
			"team covers the arsenal instead of mirroring. Static per team — cannot oscillate.",
			"Inert in 1v1.")]
		public readonly bool UseTeamRoleSplit = false;

		[Desc("TC-2d: axis points the team-endpoint rests spread apart (a 2-bot team gets -/+ this).")]
		public readonly int TeamRoleSplitShift = 20;

		[Desc("TC-3 (AI_ARCHITECTURE §12.18): fold own + allied team-blackboard broadcasts into",
			"the coalition directive — the shared MainTarget vote, rescue elections and sector",
			"anchors — and publish the three broadcast fields it consumes (army centroid,",
			"expansion assist, spawn anchor). Inert in 1v1.")]
		public readonly bool UseCoalitionPlan = false;

		[Desc("TC-3 (AI_ARCHITECTURE §12.18): master-side target bias — adopt the folded",
			"coalition MainTarget when it is still one of this bot's own attackable",
			"candidates. The nemesis override still trumps it; inert without UseCoalitionPlan.")]
		public readonly bool UseCoalitionTargetBias = false;

		[Desc("DI-1 Director (AI_ARCHITECTURE §12.16): own army value that counts as massed —",
			"tension only builds while there is an army to send.")]
		public readonly int DirectorArmyMassValue = 2500;
		[Desc("DI-1: tension added per snapshot while the own army is massed.")]
		public readonly int DirectorTensionRisePerSnapshot = 3;
		[Desc("DI-1: tension shed per snapshot while the own army is below DirectorArmyMassValue.")]
		public readonly int DirectorTensionDecayPerSnapshot = 2;
		[Desc("DI-1: while massed, one extra tension per this many ticks since the last",
			"delivered attack (since game start when none was launched), added per snapshot.")]
		public readonly int DirectorImpatienceTicksPerPoint = 1500;
		[Desc("DI-1: cap on the impatience tension added in one snapshot.")]
		public readonly int DirectorImpatienceMaxPerSnapshot = 10;
		[Desc("DI-1: tension at which BuildUp promotes to Pressure — the attack is overdue.")]
		public readonly int DirectorPressureThreshold = 60;
		[Desc("DI-1: tension at which the wave crests into Climax — or a launch while already Pressure.")]
		public readonly int DirectorClimaxThreshold = 85;
		[Desc("DI-1: Pressure only relaxes back to BuildUp this far below",
			"DirectorPressureThreshold — hysteresis so the phase cannot flutter on the boundary.")]
		public readonly int DirectorHysteresis = 10;
		[Desc("DI-1: tension the wave resets to when it breaks into Relief.")]
		public readonly int DirectorReliefTension = 20;
		[Desc("DI-1: tension at which Relief re-arms to BuildUp.")]
		public readonly int DirectorReliefExitThreshold = 45;
		[Desc("DI-1: ticks without a launched attack or a fresh kill delta before",
			"Climax relaxes into Relief.")]
		public readonly int DirectorReliefQuietTicks = 750;
		[Desc("DI-1: own-loss value accrued since the previous snapshot that breaks",
			"a Pressure or Climax wave straight into Relief.")]
		public readonly int DirectorLossSpikeValue = 600;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			ValidateDemandThreshold("AntiAir", AntiAirDemandOn, AntiAirDemandOff);
			ValidateDemandThreshold("AntiArmour", AntiArmourDemandOn, AntiArmourDemandOff);
			ValidateDemandThreshold("AntiInfantry", AntiInfantryDemandOn, AntiInfantryDemandOff);
			ValidateDemandThreshold("Detector", DetectorDemandOn, DetectorDemandOff);
			ValidateDemandThreshold("Artillery", ArtilleryDemandOn, ArtilleryDemandOff);
			ValidateUtilityRest(nameof(UtilityTurtleRushRest), UtilityTurtleRushRest);
			ValidateUtilityRest(nameof(UtilityTechRushExpansionRest), UtilityTechRushExpansionRest);
			ValidateUtilityRest(nameof(UtilitySteamrollerGuerrillaRest), UtilitySteamrollerGuerrillaRest);
			if (UtilityAxisDecayPercent < 0 || UtilityAxisDecayPercent > 100)
				throw new YamlException("UtilityAxisDecayPercent must be within [0,100].");
			if (UtilityInputWeightPercent < 0 || UtilityInputWeightPercent > 100)
				throw new YamlException("UtilityInputWeightPercent must be within [0,100].");
			ValidateDirectorThresholds();
		}

		public override object Create(ActorInitializer init) { return new MasterAiBotModule(init.Self, this); }

		static void ValidateDemandThreshold(string name, int on, int off)
		{
			if (off > on)
				throw new YamlException($"{name}DemandOff must be less than or equal to {name}DemandOn.");
		}

		static void ValidateUtilityRest(string name, IReadOnlyDictionary<string, int> rests)
		{
			if (rests == null)
				return;
			foreach (var kv in rests)
				if (kv.Value < 0 || kv.Value > 100)
					throw new YamlException($"{name}[{kv.Key}] must be within [0,100].");
		}
		void ValidateDirectorThresholds()
		{
			if (DirectorPressureThreshold < 0 || DirectorPressureThreshold > 100 ||
				DirectorClimaxThreshold < 0 || DirectorClimaxThreshold > 100 ||
				DirectorReliefTension < 0 || DirectorReliefTension > 100 ||
				DirectorReliefExitThreshold < 0 || DirectorReliefExitThreshold > 100)
				throw new YamlException("Director tension thresholds must be within [0,100].");
			if (DirectorPressureThreshold > DirectorClimaxThreshold)
				throw new YamlException("DirectorPressureThreshold must not exceed DirectorClimaxThreshold.");
			if (DirectorReliefTension > DirectorReliefExitThreshold)
				throw new YamlException("DirectorReliefTension must not exceed DirectorReliefExitThreshold.");
			if (DirectorHysteresis < 0 || DirectorHysteresis >= DirectorPressureThreshold)
				throw new YamlException("DirectorHysteresis must be within [0, DirectorPressureThreshold).");
			if (DirectorTensionRisePerSnapshot < 0 || DirectorTensionDecayPerSnapshot < 0 ||
				DirectorImpatienceTicksPerPoint < 0 || DirectorImpatienceMaxPerSnapshot < 0 ||
				DirectorReliefQuietTicks < 0 || DirectorArmyMassValue < 0)
				throw new YamlException("Director rates, windows and the army-mass value must be non-negative.");
			if (DirectorLossSpikeValue <= 0)
				throw new YamlException("DirectorLossSpikeValue must be positive (0 would relieve every armed wave).");
		}
	}

	public class MasterAiBotModule : ConditionalTrait<MasterAiBotModuleInfo>, IBotTick, IGameSaveTraitData, IBotMainTargetProvider, IBotRegionThreatProvider, IBotFoggedEnemyProvider, IBotRouteThreatRouter, IBotMissionProvider, IBotMissionOutcomeSink, IBotEnemyCompositionProvider, IBotThreatPredictionProvider, IBotRememberedDefenceProvider, IBotSiegeFailureMemory, IBotPersonalityLeadProvider, IBotUtilityAxes, IBotDirector, IBotTeamMember, IBotCoalition
	{
		static readonly string[] DefaultPersonalities = { "rush", "turtle", "tech", "expansion", "steamroller", "guerrilla" };
		internal static readonly string[] DemandNames = { "antiair", "antiarmour", "antiinfantry", "detector", "artillery" };
		readonly OpenRA.Player player;
		readonly BotFogMemory fogMemory;

		// IM-1: the persistent layers object — its EMA history lives across snapshots, so it is
		// constructed once and republished in place (Situation.Influence hands out the live read).
		readonly BotInfluenceLayers influenceLayers;
		// §13.1 discipline telemetry: cached own-Player trait refs (filled lazily on the
		// first tick — PlayerActor traits don't change) plus the per-tick counters the
		// snapshot publishes. Record-only: deliberately not in MasterAiBotSavedState —
		// a save/load restarts the counters at 0, the honest reset for telemetry.
		PlayerResources cachedResources;
		PowerManager cachedPower;
		ProductionQueue[] cachedQueues;
		long brownoutTicks, idleProductionTicks;
		int productionQueueCount;
		readonly List<BotSituation> pendingSituations = [];
		readonly Queue<(int Tick, int Delta)> lossSamples = new();
		readonly Queue<(int Tick, int Delta)> killSamples = new();
		readonly Queue<int> productionLossTicks = new();
		readonly HashSet<uint> productionBuildings = [];
		readonly Dictionary<(BotMissionType Type, int RegionIndex), int> missionReservations = [];
		List<BotMission> missions = [];
		readonly Dictionary<string, int> missionFailStreak = new(StringComparer.Ordinal);
		readonly Dictionary<string, int> dormantUntil = new(StringComparer.Ordinal);
		int missionTick;
		int nextSnapshotTick;
		int nextEmergencyTick;
		int lastDecisionTick;
		OpenRA.Player incumbentTarget;
		string incumbentPersonality = "";
		int incumbentSince;
		int previousDeathsCost;
		int previousKillsCost;
		bool costCountersInitialized;
		BotUrgency currentUrgency;
		int lastPersonalitySwitchTick;
		int personalityCandidateSince;
		string sustainedCandidate = "";
		bool emergencyPersonalityHandled;
		// Own combat-army value from the latest snapshot (the emergency check runs more often than Rebuild).
		// Not persisted: -1 after a load means "unknown", which blocks the relative loss test until the next snapshot.
		int emergencyOwnArmy = -1;
		readonly Dictionary<string, int> counterDemandCandidateSince = new(StringComparer.Ordinal);
		string[] lastIssuedCounterDemands = Array.Empty<string>();

		// UT-1 (AI_DEEP_RESEARCH.md §5.1): the EMA-smoothed posture axes, refreshed
		// every snapshot in Rebuild and published through IBotUtilityAxes.
		readonly BotUtilityAxes utilityAxes = new();
		// DI-1 (AI_ARCHITECTURE §12.16): the pacing wave — tension and phase, refreshed
		// every snapshot in Rebuild and published through IBotDirector and the situation log.
		readonly BotDirector director = new();

		// TC-1 (AI_ARCHITECTURE §12.17): the team blackboard broadcast — refreshed at the
		// same per-snapshot point as the Director fold and published through
		// IBotTeamMember; a disabled or never-snapshotted master reads Empty instead.
		TeamBroadcast broadcast = TeamBroadcast.Empty;

		// TC-3 (AI_ARCHITECTURE §12.18): the coalition directive folded from own +
		// allied broadcasts at the same snapshot cadence and published through
		// IBotCoalition — Empty while UseCoalitionPlan is off, so every consumer
		// degrades to today's behaviour.
		CoalitionDirective coalition = CoalitionDirective.Empty;

		// §12.14 PL telemetry state: last snapshot's cumulative counters and per-type caches.
		long prevLedgerCreatedCost = -1, prevEconDestroyed;
		int prevSnapshotTick = -1, prevAttacksLaunched, firstAttackTick = -1;
		readonly Dictionary<OpenRA.Player, int> prevEnemyArmyValue = new();
		readonly Dictionary<string, int> ledgerTypeCosts = new(StringComparer.Ordinal);
		readonly Dictionary<string, bool> econVictimTypes = new(StringComparer.Ordinal);

		public BotSituation Situation { get; private set; }
		internal int DeathsCostWindow { get; private set; }
		internal int KillsCostWindow { get; private set; }
		internal IReadOnlyList<BotSituation> PendingSituations => pendingSituations;

		// FE-0 (12.24), record-only: the field-economy collector the snapshots and the placement log share.
		ExpansionTelemetry expansionTelemetry;
		internal ExpansionTelemetry ExpansionTelemetry => expansionTelemetry ??= new ExpansionTelemetry();
		OpenRA.Player IBotMainTargetProvider.MainTarget => IsTraitDisabled ? null : Situation?.MainTarget;

		// UT-1: the cooked posture axes for consumers; a disabled master reads as neutral.
		int IBotUtilityAxes.UtilityTurtleRush => IsTraitDisabled ? IBotUtilityAxes.Neutral : utilityAxes.TurtleRush;
		int IBotUtilityAxes.UtilityTechRushExpansion => IsTraitDisabled ? IBotUtilityAxes.Neutral : utilityAxes.TechRushExpansion;
		int IBotUtilityAxes.UtilitySteamrollerGuerrilla => IsTraitDisabled ? IBotUtilityAxes.Neutral : utilityAxes.SteamrollerGuerrilla;
		// DI-1: the pacing wave for consumers; a disabled or not-yet-snapshotted master
		// reads as a fresh wave — never a behaviour change.
		int IBotDirector.DirectorTension => IsTraitDisabled ? 0 : director.Tension;
		DirectorPhase IBotDirector.DirectorPhase => IsTraitDisabled ? DirectorPhase.BuildUp : director.Phase;

		// TC-1: what allies read off this bot on the team blackboard; a disabled or
		// not-yet-snapshotted master publishes the empty broadcast — never a
		// behaviour change.
		TeamBroadcast IBotTeamMember.Broadcast => IsTraitDisabled ? TeamBroadcast.Empty : broadcast;

		// TC-3: the folded team directive consumers read as demand bias; a disabled or
		// not-yet-folded master reads Empty — never a behaviour change.
		CoalitionDirective IBotCoalition.Coalition => IsTraitDisabled ? CoalitionDirective.Empty : coalition;
		public IReadOnlyList<BotMission> Missions => IsTraitDisabled || !Info.PublishMissions
			? Array.Empty<BotMission>()
			: missions.Where(m => (!missionReservations.TryGetValue((m.Type, m.RegionIndex), out var reservedTick) ||
				!ReservationActive(reservedTick, missionTick, Info.MissionReservationTicks)) &&
				!IsDormant(dormantUntil, m.EffectiveMissionId, player.World.WorldTick)).ToArray();

		// LC8: the dormant shelf. A mission id whose squads keep dying rests for
		// RaidDormantTicks instead of being re-published into the same grinder.
		internal static bool GoesDormant(int failStreak, int threshold) => threshold > 0 && failStreak >= threshold;

		internal static bool IsDormant(Dictionary<string, int> shelf, string missionId, int tick) =>
			shelf.Count > 0 && missionId != null && shelf.TryGetValue(missionId, out var until) && tick < until;

		// Streak step: Failed adds one, Success clears, anything else (Released...) leaves it.
		internal static int NextFailStreak(int streak, BotMissionAttemptState state) =>
			state == BotMissionAttemptState.Failed ? streak + 1 : state == BotMissionAttemptState.Success ? 0 : streak;

		static string MissionTypeOf(string missionId)
		{
			var i = missionId?.IndexOf(':') ?? -1;
			return i > 0 ? missionId[..i] : "raid";
		}

		void IBotMissionOutcomeSink.Report(string missionId, int attemptId, BotMissionAttemptState state, string reason, int tick)
		{
			if (IsTraitDisabled || missionId == null || Info.RaidFailuresBeforeDormant <= 0)
				return;

			var streak = NextFailStreak(missionFailStreak.GetValueOrDefault(missionId), state);
			if (streak == 0)
				missionFailStreak.Remove(missionId);
			else
				missionFailStreak[missionId] = streak;

			if (!GoesDormant(streak, Info.RaidFailuresBeforeDormant))
				return;

			missionFailStreak.Remove(missionId);
			dormantUntil[missionId] = tick + Info.RaidDormantTicks;
			BotMissionLog.Write(new BotMissionRecord
			{
				Player = player, MissionId = missionId, Event = BotMissionEvent.Dormant, Reason = BotMissionReasons.Outmatched,
				Executor = "Master", MissionType = MissionTypeOf(missionId), Tick = tick
			});
		}

		void ReopenDormant(int tick)
		{
			if (dormantUntil.Count == 0)
				return;

			List<string> expired = null;
			foreach (var kv in dormantUntil)
				if (tick >= kv.Value)
					(expired ??= []).Add(kv.Key);

			if (expired == null)
				return;

			foreach (var id in expired)
			{
				dormantUntil.Remove(id);
				BotMissionLog.Write(new BotMissionRecord
				{
					Player = player, MissionId = id, Event = BotMissionEvent.Reopened, Reason = BotMissionReasons.Timeout,
					Executor = "Master", MissionType = MissionTypeOf(id), Tick = tick
				});
			}
		}

		public void MissionTaken(BotMission mission)
		{
			if (mission == null || mission.Type != BotMissionType.Raid)
				return;

			// Reservations are advisory unsynchronized state. They intentionally do
			// not survive save/load because a fresh snapshot republishes intent.
			missionReservations[(mission.Type, mission.RegionIndex)] = missionTick;
		}

		// The 6c risk gate's fog-honest read: remembered enemy combat value in the
		// region containing the cell. AntiAir is deliberately excluded (a ground
		// squad's pre-commit check); air squads do not consult this gate yet.
		int IBotRegionThreatProvider.RememberedEnemyThreatAt(CPos cell)
		{
			var regions = Situation?.Regions;
			if (IsTraitDisabled || regions == null)
				return 0;

			return RememberedThreatAtRegion(regions, regions.IndexOf(cell), false);
		}

		// CA-2c (§12.6 rule 5): durable per-(enemy, region) failed-siege memory.
		// RegionMemory is rebuilt every Rebuild, so the counts live here and are
		// stamped onto the snapshot each pass. Reads apply a staleness window —
		// a wall that beat us an hour ago no longer steers the plan.
		readonly Dictionary<OpenRA.Player, Dictionary<int, (int Count, int Tick)>> failedSieges = new();

		// ZG-c: the index space the durable tables (failedSieges, missionReservations) were
		// last keyed under. A zone re-cut or a grid<->zone backing switch re-shuffles every
		// region id, so both drop on the change rather than alias onto different ground.
		bool lastRegionsZoned;
		int lastRegionsGeneration = -1;

		void IBotSiegeFailureMemory.RecordFailedSiege(OpenRA.Player enemy, CPos cell, int tick)
		{
			var regions = Situation?.Regions;
			if (IsTraitDisabled || enemy == null || regions == null)
				return;

			// Zone-backed IndexOf answers -1 for cells beyond every zone: a siege failing
			// there has no region to hang the memory on.
			var index = regions.IndexOf(cell);
			if (index < 0)
				return;

			if (!failedSieges.TryGetValue(enemy, out var table))
				failedSieges[enemy] = table = new Dictionary<int, (int, int)>();

			if (table.TryGetValue(index, out var e) && tick - e.Tick <= Info.SiegeFailureMemoryTicks)
				table[index] = (e.Count + 1, tick);
			else
				table[index] = (1, tick);
		}

		int IBotSiegeFailureMemory.FailedSiegeWeightPercentAt(CPos cell, int tick)
		{
			var regions = Situation?.Regions;
			if (IsTraitDisabled || regions == null || failedSieges.Count == 0)
				return 100;

			var index = regions.IndexOf(cell);
			if (index < 0)
				return 100;

			var extra = 0;
			foreach (var table in failedSieges.Values)
				if (table.TryGetValue(index, out var e) && tick - e.Tick <= Info.SiegeFailureMemoryTicks)
					extra += e.Count * Info.SiegeFailureWeightPercent;
			return 100 + extra;
		}

		// The per-region threat read, split by the leader's domain: ground squads
		// pay remembered Army+Defence; air squads (CA-5, §12.8) pay remembered
		// AntiAir — the "things that can hurt aircraft" layer RegionMemory keeps.
		internal static int RememberedThreatAtRegion(RegionMemory.Region region, bool airborne)
		{
			return region == null ? 0 : airborne ? region.AntiAirValue : region.ArmyValue + region.DefenceValue;
		}

		// Summed remembered threat across every enemy's region table — the
		// shared read for the 6c gate (ground) and the 6e router (per-domain).
		// index can be -1 under a zone backing (cell beyond every zone): no region, no threat.
		static int RememberedThreatAtRegion(RegionMemory regions, int index, bool airborne)
		{
			if (index < 0)
				return 0;

			var threat = 0;
			foreach (var enemyRegions in regions.ByEnemy.Values)
				if (index < enemyRegions.Length)
					threat += RememberedThreatAtRegion(enemyRegions[index], airborne);

			return threat;
		}

		// 6e risk routing: coarse waypoints around remembered threat. The squad's
		// locomotor filters out waypoints it cannot reach (region centers can land
		// on water or cliffs); aircraft overfly every cell, so they skip the
		// reachability filter and pay remembered anti-air coverage instead
		// (CA-5 air-threat routing, AI_ARCHITECTURE §12.8).
		List<CPos> IBotRouteThreatRouter.RouteAroundThreat(Actor leader, CPos to, int maxWaypoints)
		{
			var regions = Situation?.Regions;
			if (IsTraitDisabled || !Info.UseRiskRouting || regions == null || leader == null || leader.IsDead || !leader.IsInWorld)
				return null;

			var airborne = leader.Info.HasTraitInfo<AircraftInfo>();
			Func<CPos, CPos, bool> reachable = null;
			if (!airborne)
			{
				var mobile = leader.TraitOrDefault<Mobile>();
				if (mobile != null)
					reachable = (a, b) => mobile.PathFinder.PathExistsForLocomotor(mobile.Locomotor, a, b);
			}

			// IM-2: prefer the published influence layers (EMA-blended and spread over the
			// boundary) as the risk map; the raw per-region remembered threat stays the
			// fallback whenever the layers are off or answer in a different index space.
			var influence = Situation?.Influence;
			var layered = influence != null && influence.MatchesIndexSpace(regions);

			return RegionRouter.Route(regions, leader.Location, to,
				i => layered
					? (airborne ? influence.ThreatAir[i] : influence.ThreatGround[i])
					: RememberedThreatAtRegion(regions, i, airborne),
				Info.RiskRoutingThreatWeight, maxWaypoints, reachable);
		}

		// The 6d fogged-scan switch: squads observe fog only when the master AI is
		// configured to (UseFoggedObservation) and the map actually has shroud —
		// the same condition Rebuild uses to fog its own snapshot.
		bool IBotFoggedEnemyProvider.FoggedObservation =>
			!IsTraitDisabled && Info.UseFoggedObservation && player.Shroud != null;

		// CA-2 stand-off input (AI_ARCHITECTURE §12.6): the static defences this
		// bot has actually seen, each projected with its observed type's longest
		// weapon range. Range comes from public ruleset data for a seen type —
		// fog-honest. Empty when nothing has been observed, never a claim that
		// no defences exist.
		IEnumerable<BotRememberedDefence> IBotRememberedDefenceProvider.RememberedDefences()
		{
			if (IsTraitDisabled)
				yield break;

			foreach (var enemy in player.World.Players)
			{
				if (enemy == player || enemy.NonCombatant || player.RelationshipWith(enemy) != PlayerRelationship.Enemy)
					continue;

				foreach (var seen in fogMemory.Remembered(enemy))
				{
					if (!seen.Defence || seen.Info == null)
						continue;

					var maxRange = 0;
					foreach (var armament in seen.Info.TraitInfos<ArmamentInfo>())
						if (armament.WeaponInfo != null && armament.WeaponInfo.Range.Length > maxRange)
							maxRange = armament.WeaponInfo.Range.Length;

					// Frozen actors without resolvable cost report Value 0; the
					// observed type's ruleset Valued cost is fog-honest (the type
					// itself was seen) and keeps siege scoring non-degenerate.
					var value = seen.Value > 0 ? seen.Value : seen.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;

					yield return new BotRememberedDefence(seen.Location, value, (maxRange + 1023) / 1024, seen.LastSeenTick, enemy, seen.Info);
				}
			}
		}

		// CN3 detector seam (AI_MASTER_PLAN §3): the remembered DetectCloaked carriers,
		// read by StealthDoctrineBotModule (the IBotStealthDoctrine provider the
		// `cn3_stealth_squads` condition arms). The fog tables are only fed while
		// fogged observation runs, so with the memory off this is empty - "none
		// observed", never "no detectors exist".
		internal IEnumerable<BotKnownDetector> KnownDetectors(int maxAgeTicks)
		{
			return fogMemory?.KnownDetectors(maxAgeTicks) ?? Enumerable.Empty<BotKnownDetector>();
		}

		// The enemy army as this bot has SEEN it, for adaptive counter-production (DESIGN §19.1). Only when it
		// observes through fog; otherwise false, and the unit builder falls back to its omniscient sample.
		bool IBotEnemyCompositionProvider.TryGetEnemyComposition(out IReadOnlyDictionary<string, int> valueByActorType)
		{
			valueByActorType = null;
			if (!((IBotFoggedEnemyProvider)this).FoggedObservation)
				return false;

			var composition = new Dictionary<string, int>();
			foreach (var enemy in player.World.Players)
			{
				if (enemy == player || enemy.NonCombatant || player.RelationshipWith(enemy) != PlayerRelationship.Enemy)
					continue;

				foreach (var seen in fogMemory.Remembered(enemy))
					if (seen.Combat && !seen.Building && seen.Info != null)
						composition[seen.Info.Name] = composition.GetValueOrDefault(seen.Info.Name) + Math.Max(1, seen.Value);
			}

			valueByActorType = composition;
			return true;
		}

		public MasterAiBotModule(Actor self, MasterAiBotModuleInfo info)
			: base(info)
		{
			player = self.Owner;
			fogMemory = new BotFogMemory(player, info);
			influenceLayers = new BotInfluenceLayers(info);
			costCountersInitialized = !player.World.IsLoadingGameSave;
			lastDecisionTick = -Math.Max(1, info.DecisionInterval);
			lastPersonalitySwitchTick = -Math.Max(1, info.PersonalityHoldTicks);
			nextSnapshotTick = Math.Abs(player.ClientIndex * 37) % Math.Max(1, info.SnapshotInterval);
			nextEmergencyTick = nextSnapshotTick;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (IsTraitDisabled || bot.Player != player)
				return;

			// §13.1: per-tick discipline counters — brownout (ExcessPower < 0) and
			// fully-idle enabled production queues (each idle factory counts).
			if (cachedPower == null)
			{
				cachedResources = player.PlayerActor.TraitOrDefault<PlayerResources>();
				cachedPower = player.PlayerActor.TraitOrDefault<PowerManager>();
				cachedQueues = player.PlayerActor.TraitsImplementing<ProductionQueue>().ToArray();
				productionQueueCount = cachedQueues.Length;
			}

			if (cachedPower != null && cachedPower.ExcessPower < 0)
				brownoutTicks++;
			foreach (var queue in cachedQueues)
				if (queue.Enabled && queue.CurrentItem() == null && !queue.AllQueued().Any())
					idleProductionTicks++;

			var tick = player.World.WorldTick;
			ReopenDormant(tick);
			if (tick >= nextEmergencyTick)
			{
				nextEmergencyTick = tick + Math.Max(1, Info.EmergencyCheckInterval);
				CheckEmergency(tick);
			}
			if (tick < nextSnapshotTick)
				return;

			nextSnapshotTick = tick + Math.Max(1, Info.SnapshotInterval);
			Rebuild(tick, bot);
		}

		void Rebuild(int tick, IBot bot)
		{
			var actors = player.World.Actors.Where(a => a.IsInWorld && !a.IsDead).ToArray();
			var actorsByOwner = actors.GroupBy(a => a.Owner).ToDictionary(g => g.Key, g => g.ToArray());
			var ownActors = actorsByOwner.TryGetValue(player, out var ownedActors) ? ownedActors : Array.Empty<Actor>();
			var ownBuildings = ownActors.Where(IsBuilding).ToArray();
			var ownArmy = ownActors.Where(IsCombatUnit).Sum(Value);
			emergencyOwnArmy = ownArmy;
			var combatRatios = CombatRatios(ownActors);
			var ownDefence = ownBuildings.Where(IsDefence).Sum(Value);
			var ownHarvesters = ownActors.Count(a => a.Info.HasTraitInfo<HarvesterInfo>());
			var ownRefineries = ownBuildings.Count(b => b.Info.HasTraitInfo<RefineryInfo>());
			var enemies = player.World.Players.Where(IsEligible)
				.Where(p => p != player && player.RelationshipWith(p) == PlayerRelationship.Enemy)
				.ToArray();
			var fogged = Info.UseFoggedObservation && player.Shroud != null;

			// ZG-c: run the spatial memory on the zone topology when this bot has an enabled,
			// built TacticalMapBotModule (genericbot only — classic never attaches one); the
			// square RegionCellSize grid stays the fallback for a missing, disabled or
			// still-unbuilt topology, and when the yaml lever is off.
			var zoneTopology = Info.UseZoneTopology
				? player.PlayerActor.TraitOrDefault<TacticalMapBotModule>()
				: null;
			var regions = zoneTopology != null && !zoneTopology.IsTraitDisabled && zoneTopology.TopologyReady
				? new RegionMemory(player.World.Map, Info.RegionCellSize, zoneTopology)
				: new RegionMemory(player.World.Map, Info.RegionCellSize);

			// Region-index-keyed durable state belongs to the index space it was recorded in:
			// a zone re-cut or a backing switch re-shuffles every id, so these tables drop on
			// the change rather than alias onto different ground. BotMission.EffectiveMissionId
			// embeds the region index too, so the dormant shelf and fail streaks are the same
			// kind of state — they go with it.
			if (regions.ZoneBacked != lastRegionsZoned || regions.Generation != lastRegionsGeneration)
			{
				lastRegionsZoned = regions.ZoneBacked;
				lastRegionsGeneration = regions.Generation;
				failedSieges.Clear();
				missionReservations.Clear();
				missionFailStreak.Clear();
				dormantUntil.Clear();
			}

			var profiles = new Dictionary<OpenRA.Player, EnemyProfile>();
			foreach (var enemy in enemies)
			{
				var enemyActors = actorsByOwner.TryGetValue(enemy, out var ownedEnemyActors) ? ownedEnemyActors : Array.Empty<Actor>();
				EnemyProfile profile;
				if (fogged)
				{
					var visibleHarvesters = fogMemory.Observe(enemy, enemyActors, tick);
					profile = BuildObservedProfile(enemy, fogMemory.Remembered(enemy), ownBuildings, tick);
					profile.HarvesterCount = visibleHarvesters;
					regions.SetRegions(enemy, BuildRegions(regions, fogMemory.Remembered(enemy)));
				}
				else
				{
					profile = BuildProfile(enemy, enemyActors, ownBuildings, tick);
					profile.HarvesterCount = profile.Harvesters;
					regions.SetRegions(enemy, BuildRegions(regions,
						enemyActors.Where(a => a.Info.HasTraitInfo<IOccupySpaceInfo>())
							.Select(a => BotFogMemory.Classify(a.Info, a.ActorID, a.Location, a.GetEnabledTargetTypes(), tick, Info))));
				}

				// CA-2c: stamp the durable failed-siege counts onto the fresh
				// snapshot (the published Region fields are read-only memory).
				if (failedSieges.TryGetValue(enemy, out var sieges) && sieges.Count > 0 &&
					regions.ByEnemy.TryGetValue(enemy, out var stampedRegions))
					foreach (var kv in sieges)
						if (kv.Key < stampedRegions.Length && stampedRegions[kv.Key] != null)
						{
							stampedRegions[kv.Key].FailedSiegeCount = kv.Value.Count;
							stampedRegions[kv.Key].LastFailedSiegeTick = kv.Value.Tick;
						}

				profile.KnownRegions = regions.KnownRegionCount(enemy);
				profiles.Add(enemy, profile);
			}

			// §12.14: seen army growth per enemy since the last snapshot; players that left the
			// enemy list drop out of the remembered table with the rebuild below.
			foreach (var profile in profiles.Values)
				profile.ArmyValueDelta = prevEnemyArmyValue.TryGetValue(profile.Player, out var prevArmy)
					? profile.ArmyValue - prevArmy : 0;
			prevEnemyArmyValue.Clear();
			foreach (var profile in profiles.Values)
				prevEnemyArmyValue[profile.Player] = profile.ArmyValue;

			// §12.14 Guerrilla map-control inputs: fresh = our intel on the region is no older than
			// the scout staleness horizon (currently visible counts as fresh — an empty look is still
			// information); presence = any enemy's remembered army/defence/economy sits there. Both
			// are unions over the per-enemy region tables, so one enemy's stale sightings don't hide
			// behind another's fresh look and two enemies in one region still count once.
			var staleAfterTicks = player.PlayerActor.TraitsImplementing<ScoutBotModule>()
				.FirstEnabledTraitOrDefault()?.Info.StaleAfterTicks ?? 2500;
			var regionsFresh = 0;
			var regionsEnemyPresence = 0;
			for (var i = 0; i < regions.CellCount; i++)
			{
				var fresh = false;
				var presence = false;
				foreach (var enemyRegions in regions.ByEnemy.Values)
				{
					if (i >= enemyRegions.Length)
						continue;
					var r = enemyRegions[i];
					if (r == null)
						continue;
					if (!fresh && r.EverSeen && tick - r.LastSeenTick <= staleAfterTicks)
						fresh = true;
					if (!presence && r.ArmyValue + r.DefenceValue + r.EconomyValue > 0)
						presence = true;
					if (fresh && presence)
						break;
				}

				regionsFresh += fresh ? 1 : 0;
				regionsEnemyPresence += presence ? 1 : 0;
			}

			var threats = TrackThreats(tick, enemies, actorsByOwner, ownBuildings, fogged);
			var enemyArmy = profiles.Values.Sum(p => p.ArmyValue);
			var urgency = currentUrgency == BotUrgency.Emergency
				? BotUrgency.Emergency
				: profiles.Values.Any(p => p.PressureValue > 0) ||
					(enemyArmy > 0 && (long)ownArmy * 100 < (long)enemyArmy * Info.PressuredArmyRatio)
					? BotUrgency.Pressured : BotUrgency.Normal;
			currentUrgency = urgency;
			if (urgency != BotUrgency.Emergency)
				emergencyPersonalityHandled = false;

			var threatAnalysis = player.PlayerActor.TraitsImplementing<IBotThreatAnalysis>()
				.FirstEnabledTraitOrDefault();

			var econTotal = profiles.Values.Where(p => p.Alive).Sum(EconProxy);
			foreach (var profile in profiles.Values.Where(p => p.Alive))
				profile.Score = TargetScore(profile, ownArmy, AlliedCommitments(profile.Player), econTotal,
					threatAnalysis == null ? 0 : HurtShare((int)threatAnalysis.GetNemesisScore(profile.Player),
						(int)threatAnalysis.GetDealtScore(profile.Player)), tick, Info);

			var targetProfile = profiles.Values.FirstOrDefault(p => p.Player == incumbentTarget);
			var decision = ShouldEvaluateTargetDecision(
				incumbentTarget != null, targetProfile != null,
				lastDecisionTick, tick, Info.DecisionInterval);
			OpenRA.Player target = incumbentTarget;
			if (decision)
			{
				var candidates = profiles.Values.Where(p => p.Alive && p.NearestCells >= 0).ToArray();
				var chosen = ChooseTarget(candidates, targetProfile, incumbentSince, tick, Info);
				target = chosen?.Player;
				targetProfile = chosen;
				if (target != incumbentTarget)
					incumbentSince = tick;
				incumbentTarget = target;

				// TC-3 BE (§12.18): the directive folded last snapshot is a demand bias —
				// adopt the coalition MainTarget when it is still one of this bot's own
				// attackable candidates (an alive, reached enemy per this snapshot's
				// profiles); otherwise keep the chosen target. The nemesis override
				// below and the next decision interval still trump it.
				if (Info.UseCoalitionTargetBias && coalition.MainTarget != null)
				{
					var coalitionProfile = candidates.FirstOrDefault(p => p.Player == coalition.MainTarget);
					if (coalitionProfile != null)
					{
						if (coalitionProfile.Player != incumbentTarget)
							incumbentSince = tick;
						target = incumbentTarget = coalitionProfile.Player;
						targetProfile = coalitionProfile;
					}
				}
			}

			// §4.3 override: a player actively killing our base is the mandatory target,
			// bypassing both the decision interval and MinimumHoldTicks.
			var nemesis = threatAnalysis?.GetNemesis();
			if (nemesis != null && nemesis != incumbentTarget &&
				threatAnalysis.GetNemesisScore(nemesis) >= Info.NemesisOverrideWeight)
			{
				var nemesisProfile = profiles.Values.FirstOrDefault(p => p.Alive && p.NearestCells >= 0 && p.Player == nemesis);
				if (nemesisProfile != null)
				{
					incumbentTarget = nemesis;
					incumbentSince = tick;
					target = nemesis;
					targetProfile = nemesisProfile;
				}
			}

			var currentPersonality = CurrentPersonality();
			var personalityCandidate = UnfilteredCandidatePersonality(urgency, targetProfile, ownArmy,
				profiles.Values, currentPersonality, Info);
			var availablePersonalities = AvailablePersonalities();
			var candidatePersonality = CandidatePersonality(urgency, targetProfile, ownArmy,
				profiles.Values, currentPersonality, availablePersonalities, Info);
			incumbentPersonality = candidatePersonality;
			personalityCandidateSince = SustainedCandidateSince(candidatePersonality, sustainedCandidate,
				personalityCandidateSince, tick);
			sustainedCandidate = candidatePersonality;

			var emergencyTransition = urgency == BotUrgency.Emergency && !emergencyPersonalityHandled &&
				!Info.EmergencyKeepsPersonality;
			var botLimits = player.PlayerActor.TraitsImplementing<BotLimits>().FirstEnabledTraitOrDefault();
			var reactionDelay = botLimits?.Info.PersonalityReactionDelay ?? Info.DefaultPersonalityReactionDelay;
			if (ShouldSwitchPersonality(currentPersonality, candidatePersonality, lastPersonalitySwitchTick, tick,
				emergencyTransition, reactionDelay, personalityCandidateSince, Info))
			{
				bot.QueueOrder(new Order("SetBotPersonality", player.PlayerActor, false)
				{
					TargetString = candidatePersonality,
					SuppressVisualFeedback = true
				});
				lastPersonalitySwitchTick = tick;
			}

			if (emergencyTransition)
				emergencyPersonalityHandled = true;

			if (decision)
				lastDecisionTick = tick;

			var demand = BuildDemand(profiles.Values, targetProfile, enemyArmy);
			var demandController = player.PlayerActor.TraitOrDefault<BotCounterDemandController>();
			var activeDemands = demandController?.ActiveDemands.ToHashSet(StringComparer.Ordinal) ??
				new HashSet<string>(StringComparer.Ordinal);
			var heldDemands = activeDemands.Count > 0 ? activeDemands :
				lastIssuedCounterDemands.ToHashSet(StringComparer.Ordinal);
			var resolvedDemands = ResolveDemands(demand, heldDemands, tick, reactionDelay,
				counterDemandCandidateSince, Info);
			if (demandController != null && !activeDemands.SetEquals(resolvedDemands))
			{
				bot.QueueOrder(new Order("SetBotCounterDemand", player.PlayerActor, false)
				{
					TargetString = string.Join(",", resolvedDemands),
					SuppressVisualFeedback = true
				});
				lastIssuedCounterDemands = resolvedDemands;
			}

			var ownLiveActors = ownActors.Where(a => a.IsInWorld && !a.IsDead && a.OccupiesSpace != null).ToArray();
			var ownLiveBuildings = ownBuildings.Where(a => a.IsInWorld && !a.IsDead && a.OccupiesSpace != null).ToArray();
			var ownBase = ownLiveBuildings.FirstOrDefault(a => a.Info.HasTraitInfo<BaseBuildingInfo>())
				?? ownLiveBuildings.FirstOrDefault()
				?? ownLiveActors.FirstOrDefault();
			var ownBaseRegionIndex = ownBase == null ? 0 : regions.IndexOf(ownBase.Location);
			var ownNearBaseValue = ownLiveActors
				.Where(a => IsNearRegion(regions, ownBaseRegionIndex, a.Location))
				.Sum(Value);
			missions = Info.PublishMissions
				? DeriveMissions(regions, enemies, ownBaseRegionIndex, ownNearBaseValue, Info)
				: [];
			missionTick = tick;

			var squadCount = 0;
			var squadUnitCount = 0;
			var missionAssignment = player.PlayerActor.TraitsImplementing<IBotMissionAssignmentProvider>()
				.Select(p => p.LastMissionAssignment)
				.FirstOrDefault(a => a != null);
			foreach (var sm in player.PlayerActor.TraitsImplementing<SquadManagerBotModuleCA>())
			{
				if (!sm.IsTraitEnabled())
					continue;

				squadCount += sm.Squads.Count;
				squadUnitCount += sm.Squads.Sum(q => q.Units.Count);
			}

			var lossesByRole = new SortedDictionary<string, int>(StringComparer.Ordinal);
			var awayLossesByRole = new SortedDictionary<string, int>(StringComparer.Ordinal);
			var attacksLaunched = 0;
			foreach (var sm in player.PlayerActor.TraitsImplementing<SquadManagerBotModuleCA>())
			{
				foreach (var (role, cost) in sm.LossesByRole)
					lossesByRole[role] = lossesByRole.GetValueOrDefault(role) + cost;
				foreach (var (role, cost) in sm.AwayLossesByRole)
					awayLossesByRole[role] = awayLossesByRole.GetValueOrDefault(role) + cost;
				attacksLaunched += sm.OffensiveSquadsLaunched;
			}

			int repairOrders = 0, repairSweepOrders = 0, repairTogglesAvoided = 0;
			foreach (var rm in player.PlayerActor.TraitsImplementing<BaseRepairBotModule>())
			{
				repairOrders += rm.RepairOrders;
				repairSweepOrders += rm.SweepOrders;
				repairTogglesAvoided += rm.TogglesAvoided;
			}

			// §12.14 PL telemetry (record-only): production and enemy-econ-kill windows off the
			// arsenal ledger, plus offensive launches off the squad managers, per game minute.
			var ledger = player.PlayerActor.TraitOrDefault<BotArsenalLedger>();
			var ledgerCreatedCost = LedgerCreatedCost(ledger);
			var econDestroyed = EconValueDestroyed(ledger);
			var productionWindow = prevLedgerCreatedCost < 0 || ledgerCreatedCost < 0
				? 0 : Math.Max(0, ledgerCreatedCost - prevLedgerCreatedCost);
			var econWindow = Math.Max(0, econDestroyed - prevEconDestroyed);
			if (ledgerCreatedCost >= 0)
				prevLedgerCreatedCost = ledgerCreatedCost;
			prevEconDestroyed = econDestroyed;
			var attacksDelta = Math.Max(0, attacksLaunched - prevAttacksLaunched);
			prevAttacksLaunched = attacksLaunched;
			if (firstAttackTick < 0 && attacksLaunched > 0)
				firstAttackTick = tick;

			// DI-1 (AI_ARCHITECTURE §12.16): fold the snapshot into the pacing wave.
			// Fog-honest scalars only — the fresh loss/kill windows are the samples
			// accrued since the previous snapshot (prevSnapshotTick still points at it).
			director.Observe(tick, ownArmy, attacksDelta,
				killSamples.Where(s => s.Tick > prevSnapshotTick).Sum(s => s.Delta),
				lossSamples.Where(s => s.Tick > prevSnapshotTick).Sum(s => s.Delta), Info);

			// TC-1 (AI_ARCHITECTURE §12.17): publish this bot's broadcast to the team
			// blackboard at the same snapshot cadence — the scalars this pass already
			// computed (own army, the urgency ordinal, the fresh Director wave, the
			// chosen target), never new enemy data. The defend position is the own
			// base centre while under pressure, Zero when help isn't needed or no
			// base stands.
			var requestsDefence = urgency >= BotUrgency.Pressured;
			var expansionClaim = player.PlayerActor.TraitsImplementing<IBotExpansionTargetProvider>()
				.FirstEnabledTraitOrDefault()?.ExpansionTarget;

			// TC-2e (§12.17): the live capture/contest claims of every enabled claim source,
			// unioned — own-side intent published unconditionally, exactly like ExpansionClaim.
			// Consumers arbitrate on participant key (TeamBlackboard.ClaimsAheadOf); nothing reading
			// it means no behaviour change.
			var captureClaims = player.PlayerActor.TraitsImplementing<IBotCaptureClaimSource>()
				.Where(t => t.IsTraitEnabled())
				.SelectMany(t => t.CaptureClaimPositions ?? Array.Empty<WPos>())
				.ToList();

			// TC-3 (§12.18): the broadcast fields the coalition fold consumes — the own
			// army's mean position for the rescue election, an expansion claim that
			// wants a bodyguard, and the spawn anchor for the sector partition. All
			// own-side or provider-published; Zero while UseCoalitionPlan is off.
			var armyCentroid = WPos.Zero;
			var expansionAssist = WPos.Zero;
			var spawnPoint = WPos.Zero;
			if (Info.UseCoalitionPlan)
			{
				var ownMobileArmy = ownLiveActors.Where(IsCombatUnit).ToArray();
				if (ownMobileArmy.Length > 0)
					armyCentroid = new WPos(
						(int)(ownMobileArmy.Sum(a => (long)a.CenterPosition.X) / ownMobileArmy.Length),
						(int)(ownMobileArmy.Sum(a => (long)a.CenterPosition.Y) / ownMobileArmy.Length),
						(int)(ownMobileArmy.Sum(a => (long)a.CenterPosition.Z) / ownMobileArmy.Length));

				expansionAssist = player.PlayerActor.TraitsImplementing<IBotExpansionAssistProvider>()
					.FirstEnabledTraitOrDefault()?.ExpansionAssistTarget ?? WPos.Zero;
				spawnPoint = player.HomeLocation != CPos.Zero
					? player.World.Map.CenterOfCell(player.HomeLocation)
					: OwnBaseCenter(player.World, ownLiveBuildings);
			}

			broadcast = new TeamBroadcast(tick, ownArmy, (int)urgency, director.Tension, director.Phase,
				target, requestsDefence,
				requestsDefence ? OwnBaseCenter(player.World, ownLiveBuildings) : WPos.Zero,
				player.ClientIndex,
				expansionClaim.HasValue ? player.World.Map.CenterOfCell(expansionClaim.Value) : WPos.Zero,
				armyCentroid: armyCentroid, expansionAssist: expansionAssist, spawnPoint: spawnPoint,
				captureClaims: captureClaims, participantId: player.InternalName);

			// TC-3 (§12.18): fold own + allied broadcasts into the coalition directive —
			// every member runs the identical function over the identical set, so all
			// members hold the identical directive without an electable command unit.
			// Off flag or a solo board reads Empty; consumers degrade to today's behaviour.
			coalition = Info.UseCoalitionPlan
				? CoalitionFold.Compute(broadcast, TeamBlackboard.CollectBroadcasts(player))
				: CoalitionDirective.Empty;

			// TC-1: and read the allies' half of the board for the situation log —
			// the caller's own broadcast stays out of the summary by design; a 1v1
			// or a team without an allied bot provider reads all zeros.
			var team = TeamBlackboard.Collect(player);

			var actualDeltaTicks = prevSnapshotTick < 0 ? 0 : tick - prevSnapshotTick;
			prevSnapshotTick = tick;
			var ticksPerGameMin = 60000L / Math.Max(1, player.World.Timestep);
			var productionPerGameMin = actualDeltaTicks > 0 ? productionWindow * ticksPerGameMin / actualDeltaTicks : 0;
			var attacksPerGameMin = actualDeltaTicks > 0 ? (long)attacksDelta * ticksPerGameMin / actualDeltaTicks : 0;

			// §12.14 PL-1: the leads over every seen enemy combined, computed always —
			// UsePersonalityLeads only gates the consumers that lean on them.
			var enemyProductionPerGameMin = EnemyProductionPerGameMin(profiles.Values,
				actualDeltaTicks, ticksPerGameMin, Info.PersonalityLeadEnemyProductionPerBuildingPerMin);
			var steamrollerLead = SteamrollerLead(productionPerGameMin, enemyProductionPerGameMin);
			var rushLead = RushLead(attacksPerGameMin, Info.PersonalityLeadRushAttacksPerGameMinTarget,
				firstAttackTick, Info.PersonalityLeadRushFirstAttackTargetTick, econDestroyed);

			// IM-1 (AI_DEEP_RESEARCH §3.3): the one publisher — refresh the influence layers once
			// per snapshot, after ByEnemy is complete. Enemy inputs are the fog-gated region tables;
			// own strength is real data. Zone resource cells come from the topology when the memory
			// is zone-backed, else from the resource map's sites.
			if (Info.UseInfluenceLayers)
				influenceLayers.Refresh(regions, ownActors, zoneTopology,
					player.PlayerActor.TraitsImplementing<ResourceMapBotModule>().FirstEnabledTraitOrDefault(), tick);

			// UT-1 (AI_DEEP_RESEARCH.md §5.1): fold this snapshot into the bipolar posture
			// axes. Every input is fog-honest — enemy figures are the remembered profile
			// sums, own figures are always visible. Cluster counts use the same ClusterRadius
			// rule on both sides.
			var utilitySample = new UtilityAxisSample
			{
				CombatRatioDefendedPct = combatRatios.Defended,
				EnemyArmyValue = enemyArmy,
				EnemyPressureValue = profiles.Values.Sum(p => p.PressureValue),
				EnemyDefenceValue = profiles.Values.Sum(p => p.DefenceValue),
				EnemyExpansionClusters = profiles.Values.Where(p => p.Alive).Sum(p => p.ExpansionClusters),
				EnemyStealthShare = enemyArmy == 0 ? 0
					: (int)(profiles.Values.Sum(p => (long)p.ArmyValue * p.StealthShare) / enemyArmy),
				OwnEconomy = ownHarvesters + ownRefineries * 2,
				OwnExpansionClusters = ClusterCount(ownBuildings
					.Where(b => b.Info.HasTraitInfo<BaseBuildingInfo>() || b.Info.HasTraitInfo<RefineryInfo>())
					.Select(b => b.Location)),
				OwnDeathsCostWindow = DeathsCostWindow,
				OwnKillsCostWindow = KillsCostWindow
			};
			// TC-2d (§12.17): role split — spread the TechRush<->Expansion rest by participant rank
			// among allied bots (static per team composition, so it converges by construction;
			// a 1v1 collects no allied broadcasts and passes 0).
			var roleBias = 0;
			if (Info.UseTeamRoleSplit)
			{
				var allyKeys = TeamBlackboard.CollectBroadcasts(player)
					.Where(b => b != null && b.SnapshotTick > 0)
					.Select(CoalitionFold.ParticipantKey)
					.ToList();
				roleBias = RoleSplitBias(TeamRoleRank(player.InternalName, allyKeys),
					allyKeys.Count + 1, Info.TeamRoleSplitShift);
			}

			utilityAxes.Observe(utilitySample, currentPersonality, Info, roleBias);

			var situation = new BotSituation
			{
				Tick = tick,
				MainTarget = target,
				Personality = personalityCandidate,
				Urgency = urgency,
				Enemies = profiles,
				Demand = demand,
				Mission = Missions.FirstOrDefault(),
				MissionAssignment = missionAssignment,
				Regions = regions,
				Influence = Info.UseInfluenceLayers ? influenceLayers : null,
				FogMemory = fogMemory,
				DefenceFractionHint = Clamp(urgency == BotUrgency.Emergency ? 80 : urgency == BotUrgency.Pressured ? 55 : 30),
				ExpansionAppetiteHint = Clamp(urgency == BotUrgency.Normal && ownArmy > 0 ? 60 : 20),
				OwnArmyValue = ownArmy,
				OwnDefenceValue = ownDefence,
				OwnBuildings = ownBuildings.Length,
				OwnHarvesters = ownHarvesters,
				OwnKillsCostWindow = KillsCostWindow,
				OwnDeathsCostWindow = DeathsCostWindow,
				SquadCount = squadCount,
				SquadUnitCount = squadUnitCount,
				Threats = threats,
				CombatRatioPct = combatRatios.Army,
				CombatRatioDefendedPct = combatRatios.Defended,
				LossesByRole = lossesByRole,
				AwayLossesByRole = awayLossesByRole,
				ProductionValueWindow = productionWindow,
				ProductionPerGameMin = productionPerGameMin,
				EnemyEconValueDestroyedWindow = econWindow,
				EnemyEconValueDestroyedTotal = econDestroyed,
				AttacksLaunched = attacksLaunched,
				FirstAttackTick = firstAttackTick,
				AttacksPerGameMin = attacksPerGameMin,
				EnemyProductionPerGameMin = enemyProductionPerGameMin,
				SteamrollerLead = steamrollerLead,
				RushLead = rushLead,
				RepairOrders = repairOrders,
				RepairSweepOrders = repairSweepOrders,
				RepairTogglesAvoided = repairTogglesAvoided,
				RegionsFresh = regionsFresh,
				RegionsTotal = regions.CellCount,
				RegionsEnemyPresence = regionsEnemyPresence,
				GuerrillaLead = GuerrillaLeadFor(regionsFresh, regionsEnemyPresence),
				OwnPersonality = CurrentPersonality(),
				UtilityTurtleRush = utilityAxes.TurtleRush,
				UtilityTechRushExpansion = utilityAxes.TechRushExpansion,
				UtilitySteamrollerGuerrilla = utilityAxes.SteamrollerGuerrilla,
				DirectorTension = director.Tension,
				DirectorPhase = director.Phase,
				TeamAlliedBots = team.AlliedBots,
				TeamArmyValue = team.TotalArmyValue,
				TeamMaxTension = team.MaxTension,
				TeamDefendRequests = team.DefendRequests,
				TeamSharedTarget = team.SharedTargetCount,
				TeamAnyClimax = team.AnyClimax ? 1 : 0,
				CoalitionPhase = (int)coalition.Phase,
				CoalitionMainTarget = coalition.MainTarget?.InternalName ?? "",
				BankedCash = cachedResources == null ? 0 : cachedResources.Cash + cachedResources.Resources,
				BrownoutTicks = brownoutTicks,
				IdleProductionTicks = idleProductionTicks,
				ProductionQueues = productionQueueCount,
				ScaleTargets = player.PlayerActor.TraitsImplementing<ScaleTargetsBotModule>().FirstEnabledTraitOrDefault()?.Snapshot,
				BuildOrder = player.PlayerActor.TraitsImplementing<BuildOrderKnobsBotModule>().FirstEnabledTraitOrDefault()?.Snapshot,
				Expansion = ExpansionTelemetry.Capture(player, ownLiveBuildings)
			};
			Situation = situation;
			pendingSituations.Add(situation);
			if (pendingSituations.Count > 2000)
				pendingSituations.RemoveRange(1000, pendingSituations.Count - 2000);
		}

		string CurrentPersonality()
		{
			return player.PlayerActor.TraitOrDefault<BotPersonalityController>()?.CurrentPersonality
				?? player.PlayerActor.TraitOrDefault<AiMatchLogRecorder>()?.CurrentPersonality
				?? "";
		}

		IEnumerable<string> AvailablePersonalities()
		{
			var controller = player.PlayerActor.TraitOrDefault<BotPersonalityController>();
			return controller == null
				? DefaultPersonalities
				: controller.Info.Conditions.Select(c => BotPersonalityController.PersonalityName(c, controller.Info.PersonalityPrefix));
		}

		// Pure emergency decision. ownArmy < 0 = unknown (relative test cannot pass).
		internal static bool IsLossEmergency(int deaths, int kills, int ownArmy, bool wasEmergency,
			bool productionLost, MasterAiBotModuleInfo info)
		{
			if (productionLost)
				return true;

			if (info.EmergencyLossArmyPct <= 0)
				return deaths > (wasEmergency ? info.EmergencyLossClearThreshold : info.EmergencyLossThreshold);

			if (ownArmy < 0 || deaths <= (wasEmergency ? info.EmergencyLossClearThreshold : info.EmergencyLossThreshold))
				return false;

			var pct = wasEmergency ? info.EmergencyLossArmyPct / 2 : info.EmergencyLossArmyPct;
			var lossPct = (long)deaths * 100 / ((long)ownArmy + deaths);
			return lossPct > pct && deaths > kills;
		}

		void CheckEmergency(int tick)
		{
			var stats = player.PlayerActor.TraitOrDefault<PlayerStatistics>();
			var deaths = stats?.DeathsCost ?? 0;
			var kills = stats?.KillsCost ?? 0;
			var (delta, killDelta) = CostDeltas(deaths, kills,
				ref previousDeathsCost, ref previousKillsCost, ref costCountersInitialized);
			if (delta > 0)
				lossSamples.Enqueue((tick, delta));
			if (killDelta > 0)
				killSamples.Enqueue((tick, killDelta));

			while (lossSamples.Count > 0 && tick - lossSamples.Peek().Tick > Info.LossWindowTicks)
				lossSamples.Dequeue();
			while (killSamples.Count > 0 && tick - killSamples.Peek().Tick > Info.LossWindowTicks)
				killSamples.Dequeue();

			var liveProduction = player.World.ActorsHavingTrait<Production>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && a.Info.HasTraitInfo<ProductionInfo>())
				.Select(a => a.ActorID)
				.ToHashSet();
			if (productionBuildings.Count > 0 && productionBuildings.Any(id => !liveProduction.Contains(id)))
				productionLossTicks.Enqueue(tick);
			productionBuildings.Clear();
			foreach (var id in liveProduction)
				productionBuildings.Add(id);
			while (productionLossTicks.Count > 0 && tick - productionLossTicks.Peek() > Info.LossWindowTicks)
				productionLossTicks.Dequeue();

			DeathsCostWindow = lossSamples.Sum(s => s.Delta);
			KillsCostWindow = killSamples.Sum(s => s.Delta);
			var emergency = IsLossEmergency(DeathsCostWindow, KillsCostWindow, emergencyOwnArmy,
				currentUrgency == BotUrgency.Emergency, productionLossTicks.Count > 0, Info);
			currentUrgency = emergency ? BotUrgency.Emergency : BotUrgency.Normal;
		}

		internal static List<BotMission> DeriveMissions(
			RegionMemory regions,
			OpenRA.Player[] enemies,
			int ownBaseRegionIndex,
			int ownNearBaseValue,
			MasterAiBotModuleInfo info)
		{
			var result = new List<BotMission>();
			foreach (var enemy in enemies ?? Array.Empty<OpenRA.Player>())
			{
				if (!regions.ByEnemy.TryGetValue(enemy, out var enemyRegions))
					continue;

				for (var index = 0; index < enemyRegions.Length; index++)
				{
					var region = enemyRegions[index];
					if (region == null || !region.EverSeen || region.EconomyValue <= 0)
						continue;

					var denominator = (long)region.EconomyValue + region.ArmyValue + region.DefenceValue + 1;
					var priority = (int)Math.Clamp(100L * region.EconomyValue / Math.Max(1, denominator), 0, 100);
					if (priority < info.RaidPriorityThreshold)
						continue;

					result.Add(new BotMission
					{
						Type = BotMissionType.Raid,
						Location = regions.CenterOf(index),
						TargetPlayer = enemy,
						RegionIndex = index,
						RequiredValue = (int)Math.Clamp((long)(region.ArmyValue + region.DefenceValue) *
							info.RaidForceRatioPercent / 100, 0, int.MaxValue),
						Priority = priority
					});
				}
			}

			var threat = 0L;
			if (regions.ZoneBacked)
			{
				// Zone adjacency stands in for the grid's 3x3 ring: remembered value in the
				// base's own zone plus every zone a gate corridor joins it to. Zones are far
				// bigger than grid cells, so the ring itself is the adjacency list.
				var near = new List<int>(regions.NeighborsOf(ownBaseRegionIndex)) { ownBaseRegionIndex };
				foreach (var index in near)
				{
					if (index < 0)
						continue;

					foreach (var enemyRegions in regions.ByEnemy.Values)
						if (index < enemyRegions.Length && enemyRegions[index] != null)
							threat += enemyRegions[index].ArmyValue +
								(index == ownBaseRegionIndex ? enemyRegions[index].DefenceValue : 0);
				}
			}
			else
			{
				var baseRow = ownBaseRegionIndex / regions.Columns;
				var baseColumn = ownBaseRegionIndex - baseRow * regions.Columns;
				for (var row = Math.Max(0, baseRow - 1); row <= Math.Min(regions.Rows - 1, baseRow + 1); row++)
					for (var column = Math.Max(0, baseColumn - 1); column <= Math.Min(regions.Columns - 1, baseColumn + 1); column++)
					{
						var index = row * regions.Columns + column;
						foreach (var enemyRegions in regions.ByEnemy.Values)
							if (index < enemyRegions.Length && enemyRegions[index] != null)
								threat += enemyRegions[index].ArmyValue +
									(index == ownBaseRegionIndex ? enemyRegions[index].DefenceValue : 0);
					}
			}

			var defendPriority = threat <= ownNearBaseValue
				? 0
				: (int)Math.Min(100, 100L * (threat - ownNearBaseValue) / (threat + 1));
			if (defendPriority >= info.DefendPriorityThreshold)
				result.Add(new BotMission
				{
					Type = BotMissionType.Defend,
					Location = regions.CenterOf(ownBaseRegionIndex),
					TargetPlayer = null,
					RegionIndex = ownBaseRegionIndex,
					RequiredValue = 0,
					Priority = defendPriority
				});

			result.Sort(CompareMissions);
			return result;
		}

		static int CompareMissions(BotMission left, BotMission right)
		{
			var comparison = right.Priority.CompareTo(left.Priority);
			if (comparison != 0)
				return comparison;

			comparison = (left.Type == BotMissionType.Defend ? 0 : 1).CompareTo(right.Type == BotMissionType.Defend ? 0 : 1);
			if (comparison != 0)
				return comparison;

			comparison = left.RegionIndex.CompareTo(right.RegionIndex);
			if (comparison != 0)
				return comparison;

			comparison = string.Compare(left.TargetPlayer?.InternalName ?? "", right.TargetPlayer?.InternalName ?? "", StringComparison.Ordinal);
			if (comparison != 0)
				return comparison;

			comparison = left.Location.X.CompareTo(right.Location.X);
			if (comparison != 0)
				return comparison;
			comparison = left.Location.Y.CompareTo(right.Location.Y);
			if (comparison != 0)
				return comparison;
			return left.RequiredValue.CompareTo(right.RequiredValue);
		}

		internal static bool IsNearRegion(RegionMemory regions, int regionIndex, CPos location)
		{
			var locationIndex = regions.IndexOf(location);
			if (regions.ZoneBacked)
			{
				// "Near" under zones is the zone itself or one gated straight onto it —
				// the same one-ring reach the grid's 3x3 window meant.
				return locationIndex >= 0 && regionIndex >= 0 &&
					(locationIndex == regionIndex || regions.NeighborsOf(regionIndex).Contains(locationIndex));
			}

			var row = regionIndex / regions.Columns;
			var column = regionIndex - row * regions.Columns;
			var locationRow = locationIndex / regions.Columns;
			var locationColumn = locationIndex - locationRow * regions.Columns;
			return Math.Abs(row - locationRow) <= 1 && Math.Abs(column - locationColumn) <= 1;
		}

		internal static bool ReservationActive(int reservedTick, int tick, int reservationTicks)
		{
			return tick >= reservedTick && tick - reservedTick <= Math.Max(0, reservationTicks);
		}

		EnemyProfile BuildProfile(OpenRA.Player enemy, Actor[] enemyActors, Actor[] ownBuildings, int tick)
		{
			var profile = new EnemyProfile
			{
				Player = enemy,
				Name = enemy.InternalName,
				FactionName = enemy.Faction?.InternalName ?? "",
				Alive = enemy.WinState == WinState.Undefined && enemyActors.Length > 0,
				NearestCells = -1,
				LastSeenTick = tick,
				BuildingCount = enemyActors.Count(IsBuilding)
			};
			var enemyBuildings = enemyActors.Where(IsBuilding).ToArray();
			var combat = enemyActors.Where(IsCombatUnit).ToArray();
			profile.Harvesters = enemyActors.Count(a => a.Info.HasTraitInfo<HarvesterInfo>());
			foreach (var actor in combat)
			{
				var value = Value(actor);
				profile.ArmyValue += value;
				if (actor.Info.HasTraitInfo<AircraftInfo>())
					profile.AirValue += value;
				else
				{
					var types = actor.GetEnabledTargetTypes();
					if (types.Overlaps(Info.InfantryTargetTypes))
						profile.InfantryValue += value;
					if (types.Overlaps(Info.VehicleTargetTypes))
						profile.VehicleValue += value;
					if (types.Overlaps(Info.NavalTargetTypes))
						profile.NavalValue += value;
				}
				if (actor.Info.HasTraitInfo<CloakInfo>())
					profile.StealthShare += value;
				if (ownBuildings.Any(b => (actor.Location - b.Location).Length <= Info.PressureRadius))
					profile.PressureValue += value;
			}

			foreach (var building in enemyBuildings)
			{
				var value = Value(building);
				if (IsDefence(building))
				{
					profile.DefenceCount++;
					profile.DefenceValue += value;
				}
				if (building.Info.HasTraitInfo<ProvidesPrerequisiteInfo>())
					profile.TechBuildings++;
				if (building.Info.HasTraitInfo<ProductionInfo>())
					profile.ProductionBuildings++;
				if (building.Info.HasTraitInfo<RefineryInfo>())
					profile.Refineries++;
			}

			profile.StealthShare = profile.ArmyValue == 0 ? 0 : Clamp(profile.StealthShare * 100 / profile.ArmyValue);
			profile.ExpansionClusters = ClusterCount(enemyBuildings
				.Where(a => a.Info.HasTraitInfo<BaseBuildingInfo>() || a.Info.HasTraitInfo<RefineryInfo>())
				.Select(a => a.Location));
			if (enemyBuildings.Length > 0)
			{
				var ownBase = ownBuildings.Where(a => a.Info.HasTraitInfo<BaseBuildingInfo>()).ToArray();
				var baseActors = ownBase.Length > 0 ? ownBase : ownBuildings.Take(1).ToArray();
				if (baseActors.Length > 0)
				{
					var ownCenter = new CPos(baseActors.Sum(a => a.Location.X) / baseActors.Length,
						baseActors.Sum(a => a.Location.Y) / baseActors.Length);
					profile.NearestCells = enemyBuildings.Min(a => (a.Location - ownCenter).Length);
				}
			}
			return profile;
		}

		EnemyProfile BuildObservedProfile(OpenRA.Player enemy, IReadOnlyCollection<ObservedActor> observed,
			Actor[] ownBuildings, int tick)
		{
			var profile = new EnemyProfile
			{
				Player = enemy,
				Name = enemy.InternalName,
				FactionName = enemy.Faction?.InternalName ?? "",
				Alive = enemy.WinState == WinState.Undefined && observed.Count > 0,
				NearestCells = -1,
				LastSeenTick = 0
			};
			var buildingLocations = new List<CPos>();
			foreach (var actor in observed.OrderBy(a => a.ActorID))
			{
				if (actor.LastSeenTick > profile.LastSeenTick)
					profile.LastSeenTick = actor.LastSeenTick;

				if (actor.Building)
					profile.BuildingCount++;
				if (actor.Harvester)
					profile.Harvesters++;

				if (actor.Combat)
				{
					var value = actor.Value;
					profile.ArmyValue += value;
					if (actor.Aircraft)
						profile.AirValue += value;
					else
					{
						if (actor.Infantry)
							profile.InfantryValue += value;
						if (actor.Vehicle)
							profile.VehicleValue += value;
						if (actor.Naval)
							profile.NavalValue += value;
					}

					if (actor.Cloaked)
						profile.StealthShare += value;
					if (ownBuildings.Any(b => (actor.Location - b.Location).Length <= Info.PressureRadius))
						profile.PressureValue += value;
				}

				if (actor.Building)
				{
					buildingLocations.Add(actor.Location);
					if (actor.Defence)
					{
						profile.DefenceCount++;
						profile.DefenceValue += actor.Value;
					}
					if (actor.Tech)
						profile.TechBuildings++;
					if (actor.Production)
						profile.ProductionBuildings++;
					if (actor.Refinery)
						profile.Refineries++;
				}
			}

			profile.StealthShare = profile.ArmyValue == 0 ? 0 : Clamp(profile.StealthShare * 100 / profile.ArmyValue);
			profile.ExpansionClusters = ClusterCount(observed.Where(a => a.Building && (a.BaseBuilding || a.Refinery)).Select(a => a.Location));
			if (buildingLocations.Count > 0)
			{
				var ownBase = ownBuildings.Where(a => a.Info.HasTraitInfo<BaseBuildingInfo>()).ToArray();
				var baseActors = ownBase.Length > 0 ? ownBase : ownBuildings.Take(1).ToArray();
				if (baseActors.Length > 0)
				{
					var ownCenter = new CPos(baseActors.Sum(a => a.Location.X) / baseActors.Length,
						baseActors.Sum(a => a.Location.Y) / baseActors.Length);
					profile.NearestCells = buildingLocations.Min(l => (l - ownCenter).Length);
				}
			}
			return profile;
		}

		RegionMemory.Region[] BuildRegions(RegionMemory regions, IEnumerable<ObservedActor> observed)
		{
			var cells = new RegionMemory.Region[regions.CellCount];
			foreach (var actor in observed.OrderBy(a => a.ActorID))
			{
				var index = regions.IndexOf(actor.Location);
				if (index < 0 || index >= cells.Length)
					continue;   // zone-backed: a sighting beyond every zone (deep water, off-map) has no memory

				var region = cells[index] ??= new RegionMemory.Region();
				if (actor.Combat)
					region.ArmyValue += actor.Value;
				if (actor.Defence)
					region.DefenceValue += actor.Value;
				if (actor.AntiAir)
					region.AntiAirValue += actor.Value;
				if (actor.Harvester || actor.Refinery)
					region.EconomyValue += actor.Value;
				if (actor.Production || actor.Tech)
					region.ProductionTechValue += actor.Value;
				region.EverSeen = true;
				if (actor.LastSeenTick > region.LastSeenTick)
					region.LastSeenTick = actor.LastSeenTick;
			}

			var shroud = player.Shroud;
			for (var i = 0; i < cells.Length; i++)
			{
				if (cells[i] == null)
				{
					// A visible region with no observed actors is still an observation —
					// stamp it so scout staleness ordering doesn't treat it as never-seen.
					if (shroud.IsVisible(regions.CenterOf(i)))
						cells[i] = new RegionMemory.Region { EverSeen = true, LastSeenTick = player.World.WorldTick };
				}
				else if (!cells[i].EverSeen && shroud.IsVisible(regions.CenterOf(i)))
					cells[i].EverSeen = true;
			}

			return cells;
		}

		int ClusterCount(IEnumerable<CPos> buildingLocations)
		{
			var seeds = new List<CPos>();
			foreach (var location in buildingLocations)
				if (!seeds.Any(seed => (location - seed).Length <= Info.ClusterRadius))
					seeds.Add(location);
			return seeds.Count;
		}

		internal static EnemyProfile ChooseTarget(IEnumerable<EnemyProfile> candidates, EnemyProfile incumbent,
			int incumbentSince, int tick, MasterAiBotModuleInfo info)
		{
			var list = candidates.ToList();
			if (incumbent != null && tick - incumbentSince < info.MinimumHoldTicks)
			{
				if (list.Contains(incumbent))
					return incumbent;
			}
			return list.OrderByDescending(p => Momentum(p, p == incumbent ? info.IncumbentMomentum : 0))
				.ThenBy(p => p.Name ?? p.Player?.InternalName ?? "", StringComparer.Ordinal).FirstOrDefault();
		}

		internal static int Momentum(EnemyProfile profile, int bonus)
		{
			return ClampScore(profile.Score + profile.Score * bonus / 1000);
		}

		internal static int SustainedCandidateSince(string candidate, string previousCandidate,
			int previousSince, int tick)
		{
			return string.IsNullOrEmpty(candidate) || candidate != previousCandidate ? tick : previousSince;
		}

		internal static bool ShouldSwitchPersonality(string current, string candidate, int lastSwitchTick, int tick,
			bool emergencyTransition, int reactionDelayTicks, int candidateSince, MasterAiBotModuleInfo info)
		{
			if (string.IsNullOrEmpty(candidate) || candidate == current)
				return false;
			if (emergencyTransition)
				return true;
			if (reactionDelayTicks < 0)
				return false;
			var hold = Math.Min(info.PersonalityHoldTicks, reactionDelayTicks);
			return tick - candidateSince >= reactionDelayTicks &&
				tick - lastSwitchTick >= hold;
		}

		internal static int Saturate(int x, int k)
		{
			if (x <= 0)
				return 0;
			if (k < 0)
				k = 0;
			return ClampSignal((long)100 * x / (x + (long)k));
		}

		/// <summary>
		/// §4.3's w_hurt as the bounded share form of dealt/taken: what fraction of
		/// the exchange's total damage the enemy dealt us. 0-100; 0 until any damage
		/// has flowed either way. Ordered identically to the raw ratio (winning the
		/// exchange lowers hurt, losing raises it) without dividing by a near-zero
		/// taken score.
		/// </summary>
		internal static int HurtShare(int taken, int dealt)
		{
			var total = taken + dealt;
			return total <= 0 ? 0 : (int)((long)100 * taken / total);
		}

		/// <summary>
		/// TC-2d (§12.17): this bot's rank among the allied bots by participant key —
		/// the count of allied keys below mine ordinally. InternalName is the identity:
		/// map-side bots share the host ClientIndex (audit 4.4), which would collapse
		/// every rank to 0 and give the whole team one role. Static per team composition:
		/// the precedence can never oscillate however the axes drift. Pure, for the tests.
		/// </summary>
		internal static int TeamRoleRank(string myParticipantKey, IEnumerable<string> allyParticipantKeys)
		{
			var rank = 0;
			foreach (var key in allyParticipantKeys)
				if (string.Compare(key, myParticipantKey, StringComparison.Ordinal) < 0)
					rank++;

			return rank;
		}

		/// <summary>
		/// TC-2d: the TechRush&lt;-&gt;Expansion rest bias for rank `rank` of `teamSize` allied
		/// bots — endpoints land at ±`shift`, evenly spread between; rank 0 (lowest ClientIndex)
		/// takes the Expansion pole. A lone bot (`teamSize` 1) gets 0 — nothing to split.
		/// </summary>
		internal static int RoleSplitBias(int rank, int teamSize, int shift)
		{
			if (teamSize < 2)
				return 0;

			return shift * (teamSize - 1 - 2 * Math.Clamp(rank, 0, teamSize - 1)) / (teamSize - 1);
		}

		internal static int TargetScore(EnemyProfile profile, int ownArmy, MasterAiBotModuleInfo info)
			=> TargetScore(profile, ownArmy, 0, 0, 0, 0, info);

		internal static int TargetScore(EnemyProfile profile, int ownArmy, int ally, long econTotal, int hurt,
			MasterAiBotModuleInfo info)
			=> TargetScore(profile, ownArmy, ally, econTotal, hurt, 0, info);

		internal static int TargetScore(EnemyProfile profile, int ownArmy, int ally, long econTotal, int hurt,
			int tick, MasterAiBotModuleInfo info)
		{
			var reach = profile.NearestCells < 0 ? 0 : 100 - Saturate(profile.NearestCells, 25);
			var weak = Saturate(ownArmy, profile.ArmyValue + (info.WeakIncludesDefence ? profile.DefenceValue : 0));
			var econProxy = profile.Harvesters + profile.Refineries * 2;
			var econ = econTotal <= 0 ? 0 : ClampSignal((long)econProxy * 100 / econTotal);
			var kill = 100 - Saturate(profile.BuildingCount, info.EliminationBuildingSaturation);
			var fort = Saturate(profile.DefenceValue, 1500);
			var stale = info.WeightIntelAge <= 0 ? 0 :
				profile.LastSeenTick <= 0 ? 100 : Saturate(tick - profile.LastSeenTick, info.IntelStaleTicks);
			var total = Math.Max(1, info.WeightReach + info.WeightWeak + info.WeightEcon + info.WeightKill + info.WeightDefence + info.WeightAlly + info.WeightHurt + info.WeightIntelAge);
			var score = (long)info.WeightReach * reach + (long)info.WeightWeak * weak + (long)info.WeightEcon * econ +
				(long)info.WeightKill * kill - (long)info.WeightDefence * fort - (long)info.WeightAlly * ally -
				(long)info.WeightHurt * hurt - (long)info.WeightIntelAge * stale;
			return ClampScore(score * 10 / total);
		}

		internal static bool ShouldEvaluateDecision(int lastDecisionTick, int tick, int decisionInterval)
		{
			return tick - lastDecisionTick >= Math.Max(1, decisionInterval);
		}

		internal static bool ShouldEvaluateTargetDecision(bool hasIncumbent, bool incumbentAvailable,
			int lastDecisionTick, int tick, int decisionInterval)
		{
			return !hasIncumbent || !incumbentAvailable ||
				ShouldEvaluateDecision(lastDecisionTick, tick, decisionInterval);
		}

		internal static (int Deaths, int Kills) CostDeltas(int deaths, int kills,
			ref int previousDeaths, ref int previousKills, ref bool initialized)
		{
			if (!initialized)
			{
				previousDeaths = deaths;
				previousKills = kills;
				initialized = true;
				return (0, 0);
			}

			var result = (Math.Max(0, deaths - previousDeaths), Math.Max(0, kills - previousKills));
			previousDeaths = deaths;
			previousKills = kills;
			return result;
		}

		int AlliedCommitments(OpenRA.Player enemy)
		{
			return player.World.Players
				.Where(p => p != player && p.IsBot && IsEligible(p) && player.IsAlliedWith(p))
				.Select(p => p.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation)
				.Count(s => s?.MainTarget == enemy);
		}

		// TC-1: where a defend request should rally — the centroid of the own
		// construction-yard class (BaseBuilding), or the one building left standing;
		// WPos.Zero when nothing stands. The same own-base convention NearestCells
		// scoring uses, read off ownLiveBuildings so only in-world actors count.
		static WPos OwnBaseCenter(World world, Actor[] ownLiveBuildings)
		{
			if (ownLiveBuildings.Length == 0)
				return WPos.Zero;

			var ownBase = ownLiveBuildings.Where(a => a.Info.HasTraitInfo<BaseBuildingInfo>()).ToArray();
			var baseActors = ownBase.Length > 0 ? ownBase : ownLiveBuildings.Take(1).ToArray();
			var center = new CPos(baseActors.Sum(a => a.Location.X) / baseActors.Length,
				baseActors.Sum(a => a.Location.Y) / baseActors.Length);
			return world.Map.CenterOfCell(center);
		}

		internal static string CandidatePersonality(BotUrgency urgency, EnemyProfile target, int ownArmy,
			IEnumerable<EnemyProfile> enemies, string incumbent, IEnumerable<string> availablePersonalities,
			MasterAiBotModuleInfo info)
		{
			var available = availablePersonalities.ToHashSet(StringComparer.Ordinal);
			foreach (var candidate in PersonalityCandidates(urgency, target, ownArmy, enemies, info))
				if (available.Contains(candidate))
					return candidate;

			return incumbent != null && available.Contains(incumbent) ? incumbent : "";
		}

		internal static string UnfilteredCandidatePersonality(BotUrgency urgency, EnemyProfile target, int ownArmy,
			IEnumerable<EnemyProfile> enemies, string incumbent, MasterAiBotModuleInfo info)
		{
			return PersonalityCandidates(urgency, target, ownArmy, enemies, info).FirstOrDefault() ?? incumbent ?? "";
		}

		static IEnumerable<string> PersonalityCandidates(BotUrgency urgency, EnemyProfile target, int ownArmy,
			IEnumerable<EnemyProfile> enemies, MasterAiBotModuleInfo info)
		{
			if (urgency == BotUrgency.Emergency && !info.EmergencyKeepsPersonality)
				yield return "turtle";
			if (target != null && target.DefenceCount >= info.FortifiedDefenceCount && ownArmy >= info.SteamrollerMinArmyValue)
				yield return "steamroller";
			if (target != null && target.ExpansionClusters >= info.GuerrillaMinClusters)
				yield return "guerrilla";
			if (target != null && target.TechBuildings >= info.TechEnemyTechBuildings &&
				target.ArmyValue < info.RushMaxEnemyArmyValue * 2)
				yield return "tech";
			if (target != null && target.ArmyValue <= info.RushMaxEnemyArmyValue &&
				target.DefenceCount <= info.RushMaxEnemyDefenceCount)
				yield return "rush";
			if (!enemies.Any(e => e.Alive && e.NearestCells >= 0))
				yield return "expansion";

			// Terminal posture so a thin fogged enemy profile cannot latch the
			// incumbent forever: under pressure consolidate defensively, when
			// calm keep spreading out.
			yield return urgency >= BotUrgency.Pressured ? "turtle" : "expansion";
		}

		static CounterDemand BuildDemand(IEnumerable<EnemyProfile> enemies, EnemyProfile target, int totalArmy)
		{
			var values = enemies.ToArray();
			var air = values.Sum(e => e.AirValue);
			var armour = values.Sum(e => e.VehicleValue);
			var infantry = values.Sum(e => e.InfantryValue);
			var stealth = values.Sum(e => e.StealthShare);
			return new CounterDemand
			{
				AntiAir = totalArmy == 0 ? 0 : ClampSignal((long)air * 100 / totalArmy),
				AntiArmour = totalArmy == 0 ? 0 : ClampSignal((long)armour * 100 / totalArmy),
				AntiInfantry = totalArmy == 0 ? 0 : ClampSignal((long)infantry * 100 / totalArmy),
				Detector = totalArmy == 0 ? 0 : ClampSignal(values.Sum(e => (long)e.ArmyValue * e.StealthShare / 100) * 100 / totalArmy),
				Artillery = Saturate(target?.DefenceValue ?? values.Select(e => e.DefenceValue).DefaultIfEmpty().Max(), 1500)
			};
		}

		internal static string[] ResolveDemands(CounterDemand demand, IReadOnlyCollection<string> held,
			int tick, int reactionDelay, IDictionary<string, int> candidateSince, MasterAiBotModuleInfo info)
		{
			if (reactionDelay < 0)
			{
				candidateSince.Clear();
				return Array.Empty<string>();
			}

			var heldSet = held.ToHashSet(StringComparer.Ordinal);
			var resolved = new List<string>();
			foreach (var name in DemandNames)
			{
				var value = DemandValue(demand, name);
				if (heldSet.Contains(name))
				{
					candidateSince.Remove(name);
					if (value >= DemandOff(info, name))
						resolved.Add(name);
					continue;
				}

				if (value < DemandOn(info, name))
				{
					candidateSince.Remove(name);
					continue;
				}

				if (!candidateSince.TryGetValue(name, out var since))
					candidateSince[name] = since = tick;
				if (tick - since >= reactionDelay)
					resolved.Add(name);
			}

			foreach (var name in candidateSince.Keys.Where(name => !DemandNames.Contains(name, StringComparer.Ordinal)).ToArray())
				candidateSince.Remove(name);

			return resolved.ToArray();
		}

		static int DemandValue(CounterDemand demand, string name)
		{
			return name switch
			{
				"antiair" => demand?.AntiAir ?? 0,
				"antiarmour" => demand?.AntiArmour ?? 0,
				"antiinfantry" => demand?.AntiInfantry ?? 0,
				"detector" => demand?.Detector ?? 0,
				"artillery" => demand?.Artillery ?? 0,
				_ => 0
			};
		}

		static int DemandOn(MasterAiBotModuleInfo info, string name)
		{
			return name switch
			{
				"antiair" => info.AntiAirDemandOn,
				"antiarmour" => info.AntiArmourDemandOn,
				"antiinfantry" => info.AntiInfantryDemandOn,
				"detector" => info.DetectorDemandOn,
				"artillery" => info.ArtilleryDemandOn,
				_ => int.MaxValue
			};
		}

		static int DemandOff(MasterAiBotModuleInfo info, string name)
		{
			return name switch
			{
				"antiair" => info.AntiAirDemandOff,
				"antiarmour" => info.AntiArmourDemandOff,
				"antiinfantry" => info.AntiInfantryDemandOff,
				"detector" => info.DetectorDemandOff,
				"artillery" => info.ArtilleryDemandOff,
				_ => int.MaxValue
			};
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			return SerializeState(new MasterAiBotSavedState
			{
				CostCountersInitialized = costCountersInitialized,
				PreviousDeathsCost = previousDeathsCost,
				PreviousKillsCost = previousKillsCost,
				CurrentUrgency = currentUrgency,
				LastPersonalitySwitchTick = lastPersonalitySwitchTick,
				PersonalityCandidateSince = personalityCandidateSince,
				PersonalityCandidate = sustainedCandidate,
				EmergencyPersonalityHandled = emergencyPersonalityHandled,
				CounterDemandCandidateSince = new Dictionary<string, int>(counterDemandCandidateSince, StringComparer.Ordinal),
				LastIssuedCounterDemands = lastIssuedCounterDemands.ToArray(),
				LossSamples = lossSamples.ToArray(),
				KillSamples = killSamples.ToArray(),
				ProductionLossTicks = productionLossTicks.ToArray(),
				ProductionBuildings = productionBuildings.OrderBy(id => id).ToArray()
			});
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			var state = DeserializeState(data);
			costCountersInitialized = state.CostCountersInitialized;
			previousDeathsCost = state.PreviousDeathsCost;
			previousKillsCost = state.PreviousKillsCost;
			currentUrgency = state.CurrentUrgency;
			lastPersonalitySwitchTick = state.LastPersonalitySwitchTick;
			personalityCandidateSince = state.PersonalityCandidateSince;
			sustainedCandidate = state.PersonalityCandidate;
			emergencyPersonalityHandled = state.EmergencyPersonalityHandled;
			counterDemandCandidateSince.Clear();
			foreach (var candidate in state.CounterDemandCandidateSince)
				counterDemandCandidateSince[candidate.Key] = candidate.Value;
			lastIssuedCounterDemands = state.LastIssuedCounterDemands;

			lossSamples.Clear();
			foreach (var sample in state.LossSamples)
				lossSamples.Enqueue(sample);
			killSamples.Clear();
			foreach (var sample in state.KillSamples)
				killSamples.Enqueue(sample);
			DeathsCostWindow = lossSamples.Sum(s => s.Delta);
			KillsCostWindow = killSamples.Sum(s => s.Delta);

			productionLossTicks.Clear();
			foreach (var tick in state.ProductionLossTicks)
				productionLossTicks.Enqueue(tick);

			productionBuildings.Clear();
			foreach (var id in state.ProductionBuildings)
				productionBuildings.Add(id);
		}

		internal static List<MiniYamlNode> SerializeState(MasterAiBotSavedState state)
		{
			return new List<MiniYamlNode>
			{
				new("CostCountersInitialized", FieldSaver.FormatValue(state.CostCountersInitialized)),
				new("PreviousDeathsCost", FieldSaver.FormatValue(state.PreviousDeathsCost)),
				new("PreviousKillsCost", FieldSaver.FormatValue(state.PreviousKillsCost)),
				new("CurrentUrgency", FieldSaver.FormatValue(state.CurrentUrgency)),
				new("LastPersonalitySwitchTick", FieldSaver.FormatValue(state.LastPersonalitySwitchTick)),
				new("PersonalityCandidateSince", FieldSaver.FormatValue(state.PersonalityCandidateSince)),
				new("PersonalityCandidate", FieldSaver.FormatValue(state.PersonalityCandidate)),
				new("EmergencyPersonalityHandled", FieldSaver.FormatValue(state.EmergencyPersonalityHandled)),
				new("CounterDemandCandidateSince", "", state.CounterDemandCandidateSince
					.OrderBy(candidate => candidate.Key, StringComparer.Ordinal)
					.Select(candidate => new MiniYamlNode(candidate.Key, FieldSaver.FormatValue(candidate.Value))).ToList()),
				new("LastIssuedCounterDemands", FieldSaver.FormatValue(state.LastIssuedCounterDemands)),
				new("LossSamples", "", state.LossSamples.Select(SampleNode).ToList()),
				new("KillSamples", "", state.KillSamples.Select(SampleNode).ToList()),
				new("ProductionLossTicks", FieldSaver.FormatValue(state.ProductionLossTicks)),
				new("ProductionBuildings", FieldSaver.FormatValue(state.ProductionBuildings))
			};
		}

		internal static MasterAiBotSavedState DeserializeState(MiniYaml data)
		{
			var state = new MasterAiBotSavedState();
			var nodes = data.ToDictionary();
			if (nodes.TryGetValue("CostCountersInitialized", out var initializedNode))
				state.CostCountersInitialized = FieldLoader.GetValue<bool>("CostCountersInitialized", initializedNode.Value);
			if (nodes.TryGetValue("PreviousDeathsCost", out var deathsNode))
				state.PreviousDeathsCost = FieldLoader.GetValue<int>("PreviousDeathsCost", deathsNode.Value);
			if (nodes.TryGetValue("PreviousKillsCost", out var killsNode))
				state.PreviousKillsCost = FieldLoader.GetValue<int>("PreviousKillsCost", killsNode.Value);
			if (nodes.TryGetValue("CurrentUrgency", out var urgencyNode))
				state.CurrentUrgency = FieldLoader.GetValue<BotUrgency>("CurrentUrgency", urgencyNode.Value);
			if (nodes.TryGetValue("LastPersonalitySwitchTick", out var switchNode))
				state.LastPersonalitySwitchTick = FieldLoader.GetValue<int>("LastPersonalitySwitchTick", switchNode.Value);
			if (nodes.TryGetValue("PersonalityCandidateSince", out var candidateSinceNode))
				state.PersonalityCandidateSince = FieldLoader.GetValue<int>("PersonalityCandidateSince", candidateSinceNode.Value);
			if (nodes.TryGetValue("PersonalityCandidate", out var candidateNode))
				state.PersonalityCandidate = FieldLoader.GetValue<string>("PersonalityCandidate", candidateNode.Value);
			if (nodes.TryGetValue("EmergencyPersonalityHandled", out var handledNode))
				state.EmergencyPersonalityHandled = FieldLoader.GetValue<bool>("EmergencyPersonalityHandled", handledNode.Value);
			if (nodes.TryGetValue("CounterDemandCandidateSince", out var demandCandidatesNode))
				foreach (var candidate in demandCandidatesNode.Nodes)
					state.CounterDemandCandidateSince[candidate.Key] = FieldLoader.GetValue<int>(candidate.Key, candidate.Value.Value);
			if (nodes.TryGetValue("LastIssuedCounterDemands", out var issuedDemandsNode))
				state.LastIssuedCounterDemands = FieldLoader.GetValue<string[]>("LastIssuedCounterDemands", issuedDemandsNode.Value);

			state.LossSamples = ReadSamples(nodes, "LossSamples");
			state.KillSamples = ReadSamples(nodes, "KillSamples");
			if (nodes.TryGetValue("ProductionLossTicks", out var productionLossNode))
				state.ProductionLossTicks = FieldLoader.GetValue<int[]>("ProductionLossTicks", productionLossNode.Value);
			if (nodes.TryGetValue("ProductionBuildings", out var productionBuildingsNode))
				state.ProductionBuildings = FieldLoader.GetValue<uint[]>("ProductionBuildings", productionBuildingsNode.Value);
			return state;
		}

		static MiniYamlNode SampleNode((int Tick, int Delta) sample)
		{
			return new MiniYamlNode("Sample", FieldSaver.FormatValue(new[] { sample.Tick, sample.Delta }));
		}

		static (int Tick, int Delta)[] ReadSamples(Dictionary<string, MiniYaml> nodes, string key)
		{
			if (!nodes.TryGetValue(key, out var node))
				return Array.Empty<(int, int)>();

			var samples = new List<(int Tick, int Delta)>();
			foreach (var sampleNode in node.Nodes)
			{
				var values = FieldLoader.GetValue<int[]>("Sample", sampleNode.Value.Value);
				if (values.Length == 2)
					samples.Add((values[0], values[1]));
			}

			return samples.ToArray();
		}

		// A map-side bot (Playable: False + Bot:) is a real opponent too: campaign enemy AIs and the A/B duel
		// harness's two duelists. `Playable` alone made the master AI blind to them: in every Nuclear Winter
		// A/B match (2026-09-28) the fog-honest bot saw NO enemy for the whole game (0 of 253 snapshots; 246 of
		// 246 after). A declared-NonCombatant slot stays out, as in #594's match writer.
		static bool IsEligible(OpenRA.Player p) => !p.NonCombatant && !p.PlayerReference.NonCombatant && (p.Playable || p.IsBot);
		static int EconProxy(EnemyProfile profile) => profile.Harvesters + profile.Refineries * 2;

		// §12.14 PL telemetry reads: cumulative produced cost, and cumulative destroyed value of
		// victim types classified ECON (harvester or refinery). -1 = ledger trait absent.
		long LedgerCreatedCost(BotArsenalLedger ledger)
		{
			if (ledger == null)
				return -1;

			var total = 0L;
			foreach (var (type, entry) in ledger.ByType)
				total += (long)entry.Created * LedgerTypeCost(type);
			return total;
		}

		int LedgerTypeCost(string name)
		{
			if (!ledgerTypeCosts.TryGetValue(name, out var cost))
			{
				cost = player.World.Map.Rules.Actors.TryGetValue(name, out var info)
					? info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0
					: 0;
				ledgerTypeCosts[name] = cost;
			}

			return cost;
		}

		long EconValueDestroyed(BotArsenalLedger ledger)
		{
			if (ledger == null)
				return 0;

			var total = 0L;
			foreach (var entry in ledger.ByType.Values)
				foreach (var (victim, value) in entry.KilledValueByVictim)
					if (IsEconVictimType(victim))
						total += value;
			return total;
		}

		bool IsEconVictimType(string name)
		{
			if (!econVictimTypes.TryGetValue(name, out var econ))
			{
				econ = player.World.Map.Rules.Actors.TryGetValue(name, out var info) &&
					(info.HasTraitInfo<HarvesterInfo>() || info.HasTraitInfo<RefineryInfo>());
				econVictimTypes[name] = econ;
			}

			return econ;
		}

		// §12.14 PL-1: the remembered enemy production estimate behind Steamroller's lead,
		// cost per game minute — every enemy's positive seen army growth over the window
		// (a shrinking army is not negative production) plus a flat proxy per remembered
		// production building. No baseline window (first snapshot) reads 0, not a guess.
		internal static long EnemyProductionPerGameMin(IEnumerable<EnemyProfile> enemies,
			int deltaTicks, long ticksPerGameMin, int perBuildingPerMin)
		{
			if (deltaTicks <= 0)
				return 0;

			long growth = 0, buildings = 0;
			if (enemies != null)
				foreach (var profile in enemies)
				{
					growth += Math.Max(0, (long)profile.ArmyValueDelta);
					buildings += Math.Max(0, (long)profile.ProductionBuildings);
				}

			return growth * ticksPerGameMin / deltaTicks + buildings * perBuildingPerMin;
		}

		// Steamroller's out-produce ratio. An empty enemy-side estimate reads as
		// at-target (1), not infinite or zero: until something of the enemy's output
		// is remembered there is nothing to trail.
		internal static double SteamrollerLead(long ownProductionPerGameMin, long enemyProductionPerGameMin)
		{
			return enemyProductionPerGameMin <= 0 ? 1.0 : ownProductionPerGameMin / (double)enemyProductionPerGameMin;
		}

		// Rush's pressure score: the minimum of the launch-rate score and the
		// first-attack-timing score — fast once but silent since reads as trailing, as does
		// steady pressure that started late. No launches yet scores 0. Any remembered
		// enemy-economy kill credits the attack score a flat quarter point (EconLeadBonus):
		// having already bled their economy lightly relieves the launch-rate ask without
		// ever carrying the lead alone.
		internal const double RushEconLeadBonus = 0.25;

		internal static double RushLead(long attacksPerGameMin, double attacksPerGameMinTarget,
			int firstAttackTick, int firstAttackTargetTick, long econValueDestroyed)
		{
			var attackScore = attacksPerGameMin / Math.Max(1e-9, attacksPerGameMinTarget) +
				(econValueDestroyed > 0 ? RushEconLeadBonus : 0);
			var timingScore = firstAttackTick > 0
				? Math.Clamp(firstAttackTargetTick / (double)firstAttackTick, 0.0, 1.0)
				: 0.0;
			return Math.Min(attackScore, timingScore);
		}

		// The shared consumer lean: while a lead trails, its budget knob moves toward the
		// driver by up to maxLeanPercent, linear in the deficit — and never past it.
		// (0,1] always: a lead at/above target leans nothing, so flag-off and at-target
		// consumers keep their unscaled values bit-identically.
		internal static double LeadLeanMultiplier(double lead, int maxLeanPercent)
		{
			return 1.0 - (1.0 - Math.Clamp(lead, 0.0, 1.0)) * Math.Clamp(maxLeanPercent, 0, 100) / 100.0;
		}

		// PL-1 gate, pure for tests: the flag, the running personality matching the asked
		// one, and the snapshot's published lead all decide the multiplier together.
		// Unknown personalities lean nothing.
		internal static double PersonalityLeadLean(bool traitDisabled, bool usePersonalityLeads,
			BotSituation situation, string personality, int maxLeanPercent)
		{
			if (traitDisabled || !usePersonalityLeads || situation == null || personality == null ||
				!string.Equals(situation.OwnPersonality, personality, StringComparison.Ordinal))
				return 1.0;

			var lead = personality == "steamroller" ? situation.SteamrollerLead
				: personality == "rush" ? situation.RushLead
				: personality == "guerrilla" ? situation.GuerrillaLead
				: 1.0;
			return LeadLeanMultiplier(lead, maxLeanPercent);
		}

		double IBotPersonalityLeadProvider.PersonalityLeadLean(string personality)
		{
			return PersonalityLeadLean(IsTraitDisabled, Info.UsePersonalityLeads, Situation,
				personality, Info.PersonalityLeadMaxLeanPercent);
		}

		static bool IsBuilding(Actor a) => a.Info.HasTraitInfo<BuildingInfo>();
		bool IsDefence(Actor a) => IsBuilding(a) && (a.Info.HasTraitInfo<AttackBaseInfo>() ||
			a.GetEnabledTargetTypes().Overlaps(Info.DefenceTargetTypes));
		List<BotThreatTracker.Group> previousThreatGroups = new();
		List<BotPredictedThreat> predictedThreats = new();

		IReadOnlyList<BotPredictedThreat> IBotThreatPredictionProvider.PredictedThreats => predictedThreats;

		bool IBotThreatPredictionProvider.PerceivedBaseThreat =>
			Situation != null && (Situation.Urgency != BotUrgency.Normal || Situation.Enemies.Values.Any(e => e.PressureValue > 0));

		// DF step 1: enemy combat units SEEN this snapshot (fogged: remembered entries refreshed at this tick),
		// grouped, tracked against the previous snapshot, and extrapolated to the own building they head for.
		List<(BotThreatTracker.Group, BotThreatTracker.Prediction?)> TrackThreats(int tick, OpenRA.Player[] enemies,
			Dictionary<OpenRA.Player, Actor[]> actorsByOwner, Actor[] ownBuildings, bool fogged)
		{
			var seen = new List<BotThreatTracker.Unit>();
			foreach (var enemy in enemies)
			{
				if (fogged)
					seen.AddRange(fogMemory.Remembered(enemy).Where(s => s.Combat && s.LastSeenTick == tick)
						.Select(s => new BotThreatTracker.Unit(s.Location, Math.Max(1, s.Value))));
				else if (actorsByOwner.TryGetValue(enemy, out var list))
					seen.AddRange(list.Where(IsCombatUnit).Select(a => new BotThreatTracker.Unit(a.Location, Math.Max(1, Value(a)))));
			}

			var groups = BotThreatTracker.Track(previousThreatGroups,
				BotThreatTracker.Cluster(seen, Info.ThreatGroupRadiusCells, tick), Info.ThreatMatchRadiusCells);
			previousThreatGroups = groups;

			var assets = ownBuildings.Select(b => (b.Location, Value(b))).ToList();
			var predicted = groups.OrderByDescending(g => g.Value)
				.Select(g => (g, BotThreatTracker.Predict(g, assets, Info.ThreatConeCosPercent / 100.0,
					Info.ThreatMinSpeedCellsPerKiloTick / 1000.0)))
				.ToList();

			predictedThreats = predicted.Where(t => t.Item2.HasValue)
				.Select(t => new BotPredictedThreat(t.Item2.Value.Target, t.Item2.Value.EtaTicks, t.Item1.Value, tick)).ToList();

			return predicted.Take(Math.Max(0, Info.ThreatsLogged)).ToList();
		}

		(int Army, int Defended) CombatRatios(IEnumerable<Actor> ownActors)
		{
			var rules = player.World.Map.Rules;
			var own = ownActors.Where(IsCombatUnit).GroupBy(a => a.Info)
				.Select(g => (BotUnitProfiles.Get(rules, g.Key), g.Count())).ToList();

			var army = new Dictionary<ActorInfo, int>();
			var defences = new Dictionary<ActorInfo, int>();
			foreach (var enemy in player.World.Players)
			{
				if (enemy == player || enemy.NonCombatant || player.RelationshipWith(enemy) != PlayerRelationship.Enemy)
					continue;

				// Fog memory marks buildings Combat=false and flags armed ones Defence instead.
				foreach (var seen in fogMemory.Remembered(enemy))
				{
					if (seen.Info == null || !(seen.Combat || seen.Defence))
						continue;

					var bucket = seen.Combat ? army : defences;
					bucket[seen.Info] = bucket.GetValueOrDefault(seen.Info) + 1;
				}
			}

			var enemyArmy = army.Select(kv => (BotUnitProfiles.Get(rules, kv.Key), kv.Value)).ToList();
			// Walls count as defences for targeting but cannot shoot back: only armed defences join the fight.
			var enemyAll = enemyArmy.Concat(defences.Select(kv => (BotUnitProfiles.Get(rules, kv.Key), kv.Value))
				.Where(d => d.Item1.Weapons.Length > 0)).ToList();
			return (RatioPct(BotCombatPredictor.Predict(own, enemyArmy)), RatioPct(BotCombatPredictor.Predict(own, enemyAll)));
		}

		static int RatioPct(BotCombatPredictor.Prediction p) => (int)Math.Round(p.Ratio * 100);

		// IM-1: internal so the influence layers classify and price own actors the same way.
		internal static bool IsCombatUnit(Actor a) => a.Info.HasTraitInfo<AttackBaseInfo>() && !IsBuilding(a) && !a.Info.HasTraitInfo<HarvesterInfo>();
		internal static int Value(Actor a) => a.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
		/// <summary>§12.14 Guerrilla lead: fresh-intel regions per region with remembered enemy
		/// presence (the share denominators cancel). No remembered presence reads as at-target
		/// (1.0) — an unseen enemy is never a lead reason to scout harder.</summary>
		public static double GuerrillaLeadFor(int regionsFresh, int regionsEnemyPresence) =>
			regionsEnemyPresence <= 0 ? 1.0 : (double)regionsFresh / regionsEnemyPresence;

		static int Clamp(long value) => (int)Math.Max(0, Math.Min(100, value));
		static int ClampSignal(long value) => (int)Math.Max(0, Math.Min(100, value));
		static int ClampScore(long value) => (int)Math.Max(0, Math.Min(1000, value));
	}
}
