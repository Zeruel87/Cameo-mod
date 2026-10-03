#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits.BotModules.Squads;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Mods.AS.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;
using static OpenRA.GameInformation;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Manages AI squads.")]
	public class SquadManagerBotModuleCAInfo : ConditionalTraitInfo
	{
		[Desc("Actor types that are valid for naval squads.")]
		public readonly HashSet<string> NavalUnitsTypes = new HashSet<string>();

		[Desc("Artillery squad members by ROLE: BotRoleSets fills this from the actor-declared",
			"`artillery` role (the ^ArtilleryTemplate/^ArtilleryTankTemplate actors). AI_ARCHITECTURE.md",
			"12.4a: artillery squads are these units ONLY - not any unit that reaches a range threshold.")]
		public readonly HashSet<string> ArtilleryTypes = new HashSet<string>();

		[Desc("Fire-support escort members by ROLE: BotRoleSets fills this from the actor-declared",
			"`firesupport` role (the ^FireSupportTemplate actors). 12.4a: they form their own squads",
			"with tanks and protect the artillery - never assault or raid units.")]
		public readonly HashSet<string> FireSupportTypes = new HashSet<string>();

		[Desc("Frontline escorts a fire-support squad pulls per artillery unit it protects.")]
		public readonly int FireSupportEscortPerArtillery = 2;

		[Desc("Actor types that are excluded from ground attacks.")]
		public readonly HashSet<string> AirUnitsTypes = new HashSet<string>();

		[Desc("Actor types that should generally be excluded from attack squads.")]
		public readonly HashSet<string> ExcludeFromSquadsTypes = new HashSet<string>();

		[Desc("Actor types that are considered construction yards (base builders).")]
		public readonly HashSet<string> ConstructionYardTypes = new HashSet<string>();

		[Desc("Enemy building types around which to scan for targets for naval squads.")]
		public readonly HashSet<string> NavalProductionTypes = new HashSet<string>();

		/*
		[Desc("Own actor types that are prioritized when defending.")]
		public readonly HashSet<string> ProtectionTypes = new HashSet<string>();
		*/

		[Desc("Minimum number of units AI must have before attacking.")]
		public readonly int SquadSize = 8;

		[Desc("Random number of up to this many units is added to squad size when creating an attack squad.")]
		public readonly int SquadSizeRandomBonus = 30;

		[Desc("Maximum number of units AI can have idle.")]
		public readonly int MaxIdleUnits = 36;

		[ActorReference]
		[Desc("Units that form a guerrilla squad.")]
		public readonly HashSet<string> GuerrillaTypes = new();

		[Desc("Percent chance (0-100) that a pass of new GuerrillaTypes units joins the guerrilla squad. " +
			"Cameo: the engine this came from compared the other way round (join chance = 100 - value); flipped 2026-09-27.")]
		public readonly int JoinGuerrilla = 50;

		[Desc("Max number of units AI has in guerrilla squad")]
		public readonly int MaxGuerrillaSize = 10;

		[Desc("Cameo (maintainer 2026-09-28): how many guerrilla squads may exist at once. New guerrilla units fill the",
			"smallest open squad and a full set opens another, so several small raiding parties work at the same time.",
			"1 keeps the single guerrilla squad of the classic bot.")]
		public readonly int MaxGuerrillaSquads = 1;

		[Desc("Cameo (maintainer 2026-09-28): the guerrilla squad cap grows with game time from MaxGuerrillaSquads to",
			"this value over GuerrillaSquadRampTicks — the later the game, the more fast squads. Below",
			"MaxGuerrillaSquads means no ramp.")]
		public readonly int MaxGuerrillaSquadsLate = 0;

		[Desc("Ticks over which the guerrilla squad cap ramps from MaxGuerrillaSquads to MaxGuerrillaSquadsLate.")]
		public readonly int GuerrillaSquadRampTicks = 30000;

		[Desc("Cameo (AI_DEEP_RESEARCH.md §2.3, CP): ground squads decide to engage and to retreat with the Lanchester",
			"combat predictor over the enemies they can SEE, instead of the fuzzy health/count rule. They retreat when the",
			"predicted ratio drops below the tier's BotLimits.RetreatRatioPct and engage only at EngageMarginPct of it.")]
		public readonly bool UseCombatPredictor = false;

		[Desc("Engage threshold as a percent of the retreat threshold (hysteresis, so a squad does not dither at the line).")]
		public readonly int EngageMarginPct = 150;

		[Desc("Retreat threshold when no BotLimits trait is enabled (percent of predicted strength ratio).")]
		public readonly int DefaultRetreatRatioPct = 50;

		[Desc("Cameo DF-2 (AI_DEEP_RESEARCH.md §14): when the master predicts an enemy group heading for an own asset,",
			"draft the idle pool into the protection squad and send it to the own defence nearest that asset BEFORE the",
			"enemy arrives; the squad holds there instead of wandering home, and falls back to it (the lure) when the",
			"combat predictor says it loses alone. False = classic behaviour.")]
		public readonly bool PrepositionDefence = false;

		[Desc("DF-2: only threats predicted to arrive within this many ticks are met in advance.")]
		public readonly int PrepositionMaxEtaTicks = 1500;

		[Desc("DF-2: only threats worth at least this much (cost of the group) are met in advance.")]
		public readonly int PrepositionMinThreatValue = 1500;

		[Desc("DF-2: the rally point is the own armed building within this many cells of the predicted target.")]
		public readonly int PrepositionDefenceSearchCells = 12;

		[Desc("DF-2: a protection squad farther than this from its rally point falls back when it would lose alone.")]
		public readonly int LureRallyRadiusCells = 5;

		[Desc("Cameo DF-3/4 (AI_DEEP_RESEARCH.md §14, maintainer 2026-09-28): when a predicted attack is met, each fast",
			"(guerrilla / harass) squad that can reach the rally point before the enemy JOINS the defence; one that cannot",
			"PUNISHES instead — it strikes a remembered enemy building (its priority tags first: harvesters, production)",
			"while the enemy army is away. Needs PrepositionDefence.")]
		public readonly bool FastSquadsReactToThreats = false;

		[Desc("DF-3/4: a squad reacts to one predicted attack at most once per this many ticks.")]
		public readonly int FastSquadReactionCooldownTicks = 1500;

		[Desc("Protection release: after this many ticks with no enemy in range, no valid or visible target, no",
			"perceived threat to the base (pressure at home, master Pressured/Emergency) and no predicted attack on an",
			"own asset, the protection squad is released — raiders back to guerrilla squads, spec ops to harass",
			"squads, the rest to the attack pool. 0 = classic behaviour (the squad never releases).")]
		public readonly int ProtectionIdleDissolveTicks = 0;

		[Desc("Escort requests (EX): consume IBotProtectionRequestProvider jobs - a module asking for a guard",
			"(e.g. an MCV driving to an expansion site) drafts the same idle pool into the protection squad, which",
			"rallies AT the guarded point. Live requests count as a task against ProtectionIdleDissolveTicks;",
			"a real predicted threat outranks any request. False = classic behaviour (the",
			"frankenstein instances flip it on for the A/B).")]
		public readonly bool UseProtectionRequests = false;

		[Desc("Anti-air escort (CA-3): every assault force must field at least",
			"AntiAirEscortMinUnits AA-capable units AND enough AA value to cover the",
			"share ramp (AntiAirEscortMinSharePct early up to AntiAirEscortMaxSharePct",
			"late, over AntiAirEscortRampTicks) - the longer the game, the more air the",
			"enemy fields. A shortfall is requested from unit production (cheapest",
			"buildable AA-capable unit). False = classic behaviour.")]
		public readonly bool EnsureAntiAirEscort = false;

		[Desc("Anti-air escort: flat floor - an assault never fields fewer AA-capable",
			"units than this.")]
		public readonly int AntiAirEscortMinUnits = 3;

		[Desc("Anti-air escort: required share of the assault's value in AA-capable",
			"units at game start, percent.")]
		public readonly int AntiAirEscortMinSharePct = 20;

		[Desc("Anti-air escort: required share of assault value at ramp end, percent -",
			"the late-game floor (a third of the force must answer air).")]
		public readonly int AntiAirEscortMaxSharePct = 33;

		[Desc("Anti-air escort: game ticks over which the required share ramps from",
			"min to max.")]
		public readonly int AntiAirEscortRampTicks = 60000;

		[Desc("Anti-air escort: the share the requirement falls to when a confident",
			"enemy-army read shows NO air units - token cover against unseen tech.")]
		public readonly int AntiAirEscortRelaxedSharePct = 10;

		[Desc("Anti-air escort: respond to observed enemy air at this percent of the",
			"enemy's air share of their army value (150 = answer 30% air with a 45%",
			"AA share).")]
		public readonly int AntiAirEscortResponsePct = 150;

		[Desc("Anti-air escort: absolute cap on the required AA share, percent - the",
			"assault still needs a ground punch.")]
		public readonly int AntiAirEscortCapSharePct = 60;

		[Desc("Anti-air escort: observed enemy army value at which the air read is",
			"trusted - below this the mixed-army time ramp stays the prior.")]
		public readonly int AntiAirEscortMinArmySample = 3000;

		[Desc("Siege artillery (CA-3): the main army always fields guns that outrange",
			"base defences - at least ArtillerySiegeMinUnits pieces plus artillery worth",
			"ArtillerySiegeSharePct of the assault's value. A shortfall is requested from",
			"unit production (cheapest buildable artillery). False = classic behaviour.")]
		public readonly bool EnsureArtillerySiege = false;

		[Desc("Siege artillery: flat floor - the main army never fields fewer pieces.")]
		public readonly int ArtillerySiegeMinUnits = 2;

		[Desc("Siege artillery: required share of the assault's value in artillery, percent.")]
		public readonly int ArtillerySiegeSharePct = 15;

		[Desc("Units that form harasser squads — high-value-target raids that launch once a",
			"quorum gathers (upstream CA harasser port; empty = off). Shares the guerrilla",
			"hit/run-adjacent routing exemption but fights with ordinary attack states.")]
		public readonly HashSet<string> HarasserTypes = new HashSet<string>();

		[Desc("Harasser squads wait for at least this many units before launching.")]
		public readonly int HarassMinLaunchSize = 3;

		[Desc("Distinct route candidates a harasser squad requests — the flanking breadth.",
			"It then picks randomly from the last (least direct) routes.")]
		public readonly int HarassRouteCount = 12;

		[Desc("Delay (in ticks) between giving out orders to units.")]
		public readonly int AssignRolesInterval = 50;

		[Desc("Delay (in ticks) between issuing a protection order.")]
		public readonly int ProtectInterval = 50;

		[Desc("Delay (in ticks) between updating squads.")]
		public readonly int AttackForceInterval = 75;

		[Desc("Minimum delay (in ticks) between creating squads.")]
		public readonly int MinimumAttackForceDelay = 0;

		[Desc("DI-2 (12.16): the assault dispatch bar scales with the pacing Director's wave phase —",
			"Climax releases on a smaller pool, Relief holds for a rebuild. The bar is re-targeted",
			"every dispatch check so a phase change mid-wait takes effect immediately.",
			"False = the Director publishes telemetry only, bit-identical.")]
		public readonly bool UseDirectorPacing = false;

		[Desc("TC-2 (12.17): an allied bot's Director Climax also opens this bot's launch window —",
			"team waves surge together. Applies DirectorClimaxForceScalePercent as a cap on the",
			"effective scale even when own pacing is off (scale 100). Reads the TC-1 ally",
			"blackboard (ally-published data only); a 1v1 or absent ally provider is bit-identical.")]
		public readonly bool UseTeamSyncAttacks = false;

		[Desc("TC-2b (12.17): answer an allied bot's broadcast defend request — a protect squad",
			"rallies at the ally's published defend position, below own threat and own escort",
			"requests in priority. The draft still honours the CA-2 reserve (the ally's position",
			"is outside our base radius, so it is never treated as an emergency).",
			"False = allies are never answered, bit-identical.")]
		public readonly bool UseTeamDefendAnswers = false;

		[Desc("Minimum idle units at home before an ally defend request is answered — a thin",
			"pool stays home regardless of how loud the request is.")]
		public readonly int TeamDefendAnswerMinPoolUnits = 8;

		[Desc("Ticks a released defend_answer/assist_answer id stays unanswerable — a standing",
			"request the squad kept getting pulled off otherwise re-drafts every pass (observed",
			"16 commit/release cycles on one requester+cell). 0 = off, bit-identical.")]
		public readonly int AllyAnswerCooldownTicks = 0;

		[Desc("TC-3 (12.18): the coalition fold elects exactly one allied responder per defend",
			"request (nearest ArmyCentroid to the defend position) — answer only our own",
			"assignment; the unelected allies stand down. Needs UseTeamDefendAnswers. A missing",
			"provider or an empty election keeps today's TopDefendRequest pick, bit-identical.")]
		public readonly bool UseCoalitionRescue = false;

		[Desc("TC-3 (12.18): the squad's main-target preference folds to the coalition's voted",
			"MainTarget while one is published — the merged-army effect under one directive.",
			"A null coalition target keeps today's provider pick, bit-identical.")]
		public readonly bool UseCoalitionTarget = false;

		[Desc("TC-3 (12.18, assist pass 12.28): answer our own elected expansion-assist",
			"assignment — a protect squad rallies at the ally's published ExpansionAssist",
			"field, strictly below a defend answer (the fold drains the rescue pool first,",
			"and this channel never overrides an own threat or escort). Same pool floor as",
			"UseTeamDefendAnswers. False = assist requests are never answered, bit-identical.")]
		public readonly bool UseCoalitionAssist = false;

		[Desc("Percent of the desired attack force bar required while the Director is in BuildUp.",
			"A disabled/absent Director also reads BuildUp — 100 keeps the baseline bar.")]
		public readonly int DirectorBuildUpForceScalePercent = 100;

		[Desc("Percent of the desired attack force bar required while the Director is in Pressure.")]
		public readonly int DirectorPressureForceScalePercent = 85;

		[Desc("Percent of the desired attack force bar required while the Director is in Climax —",
			"the wave's release: launch with less than the baseline bar demands.")]
		public readonly int DirectorClimaxForceScalePercent = 55;

		[Desc("Percent of the desired attack force bar required while the Director is in Relief —",
			"the wave broke; rebuild above the baseline bar before committing again.")]
		public readonly int DirectorReliefForceScalePercent = 150;

		[Desc("Radius in cells around the base that should be scanned for units to be protected.")]
		public readonly int ProtectUnitScanRadius = 15;

		[Desc("Maximum distance in cells from center of the base when checking for MCV deployment location.",
			"Only applies if RestrictMCVDeploymentFallbackToBase is enabled and there's at least one construction yard.")]
		public readonly int MaxBaseRadius = 20;

		[Desc("Radius in cells that squads should scan for enemies around their position while idle.")]
		public readonly int IdleScanRadius = 10;

		[Desc("Radius in cells that squads should scan for danger around their position to make flee decisions.")]
		public readonly int DangerScanRadius = 10;

		[Desc("Radius in cells that attack squads should scan for enemies around their position when trying to attack.")]
		public readonly int AttackScanRadius = 12;

		[Desc("Radius in cells that protecting squads should scan for enemies around their position.")]
		public readonly int ProtectionScanRadius = 8;

		[Desc("CA-2 (§12.6, Fransbot donor port): the defend draft keeps a reserve instead of",
			"committing the whole idle pool on every attack ping. Waived when the attacker is",
			"already inside MaxBaseRadius of the base centre (the donor's short-ETA emergency).",
			"False = draft everything, bit-identical.")]
		public readonly bool UseDefendPreservation = false;

		[Desc("Idle units the defend draft refuses to commit below (DefendPreservationReservePercent",
			"raises the floor for bigger pools).")]
		public readonly int DefendPreservationMinReserveUnits = 4;

		[Desc("Percent of the draftable idle pool kept in reserve when the preservation guard engages.")]
		public readonly int DefendPreservationReservePercent = 25;

		[Desc("Pools smaller than this always commit fully — a reserve only exists once the",
			"idle force is large enough to split.")]
		public readonly int DefendPreservationTriggerUnits = 6;

		[Desc("UT-3 (§5.1 'defence share'): the TurtleRush axis scales the CA-2 reserve — turtles dig",
			"in deeper, rushers strip the pool for the wave. Only modulates the reserve when",
			"UseDefendPreservation also engages; never creates one on its own. False = yaml",
			"percent verbatim, bit-identical.")]
		public readonly bool UseUtilityDefendReserve = false;

		[Desc("Reserve scale at the Turtle pole (axis 0), percent of the CA-2 reserve.",
			"Interpolates linearly to 100 at neutral.")]
		public readonly int DefendReserveTurtleFactorPercent = 200;

		[Desc("Reserve scale at the Rush pole (axis 100), percent of the CA-2 reserve.",
			"Interpolates linearly to 100 at neutral.")]
		public readonly int DefendReserveRushFactorPercent = 50;

		[Desc("Radius in cells that naval squads should scan for targets.")]
		public readonly int NavalScanRadius = 8;

		[Desc("Enemy target types to never target.")]
		public readonly BitSet<TargetableType> IgnoredEnemyTargetTypes = default(BitSet<TargetableType>);

		// CA additions
		[Desc("Minimum value of units AI must have before attacking.")]
		public readonly int SquadValue = 0;

		[Desc("Random number of up to this value units is added to squad valuee when creating an attack squad.")]
		public readonly int SquadValueRandomBonus = 0;

		[Desc("Maximum random bonus added to squad value at the start of the match.")]
		public readonly int SquadValueMaxEarlyBonus = 0;

		[Desc("Minimum random bonus added to squad value at the end of the ramp.")]
		public readonly int SquadValueMinLateBonus = 0;

		[Desc("Maximum random bonus added to squad value at the end of the ramp.")]
		public readonly int SquadValueMaxLateBonus = 0;

		[Desc("Percent change for ground squads to attack a random priority target rather than the closest enemy.")]
		public readonly int HighValueTargetPriority = 0;

		[Desc("CA-3 (AI_ARCHITECTURE.md 12.5): target army composition by role, percent of own mobile combat units.",
			"Production fills the largest deficit against this mix; absent or empty keeps the proportional pick.",
			"Keys must be combat roles (BotUnitRole.PrimaryRoleOrder); classic carries no mix on purpose -",
			"verbatim upstream behaviour.")]
		public readonly Dictionary<string, int> RoleMix = null;

		[Desc("CA-3 (12.5): arm this personality's RoleMix — production deficit-fills toward it.",
			"Off until the increment A/B (switch group J_rolemix_production); a mix without the flag is inert data.")]
		public readonly bool UseRoleMix = false;

		[Desc("Minimum target share for every role a buildable member exists for, when RoleMix is set.",
			"Explicit mix entries win over the floor; roles the mix omits still get produced at this share.")]
		public readonly int RoleMixRoleFloorPct = 5;

		[Desc("CA-3 (12.5): max ticks a ready attack force waits for the idle pool to cover every role in StageRequiredRoles before launching anyway. 0 disables the composition gate.")]
		public readonly int StageCompositionTicks = 0;

		[Desc("CA-3 (12.5): roles a staged assault must contain at least one pool member of (e.g. frontline, anti_air). Empty disables the stage gate.")]
		public readonly HashSet<string> StageRequiredRoles = new HashSet<string>();

		[Desc("CA-4 (12.7): assault (Rush) squads move in formation - frontline leads at its slowest member's pace, anti-air sits inside, other ground trails behind the frontline centroid, scouts run free.")]
		public readonly bool FormationMovement = false;

		[Desc("CA-4 (12.7): cells behind the frontline centroid that trailing members aim for.")]
		public readonly int FormationTrailCells = 3;

		[Desc("CA-4 (12.7): cells a frontline member may outrun the slowest frontline member before it holds.")]
		public readonly int FormationMaxLeadCells = 6;

		[Desc("CA-4 (12.7, fransbot donor): temporary lead cells granted when the rear frontline member has not moved for a while (chokepoint stall). Reverts to FormationMaxLeadCells the moment the rear moves again.")]
		public readonly int FormationMaxStalledLeadCells = 12;

		[Desc("Contact-first all-in (§12.7b, maintainer 2026-10-02): a Rush squad with a visible enemy inside AttackScanRadius of ANY member",
			"commits wholesale through the attack state (no staging mid-fight). False keeps the leader-scan engage only (classic, the A/B reference).")]
		public readonly bool ContactFirstAllIn = true;

		[Desc("Assault fan (Rush, inside FormationMovement): radius in cells around the squad target at which the approach arc slots sit.")]
		public readonly int AssaultFanRadiusCells = 10;

		[Desc("Assault fan: minimum number of distinct approach headings (arc slots) a Rush squad spreads across for the final approach.")]
		public readonly int AssaultFanMinSlots = 3;

		[Desc("Assault fan: maximum number of distinct approach headings (arc slots) a Rush squad spreads across for the final approach.")]
		public readonly int AssaultFanMaxSlots = 8;

		[Desc("Assault fan: distance in cells to the squad target at which a Rush squad breaks column into the arc fan instead of marching on.")]
		public readonly int AssaultEngageRadiusCells = 18;

		[Desc("Assault fan: ticks early arrivers hold at their arc slot while another prong is still inbound, before the synchronized push anyway.")]
		public readonly int AssaultSyncHoldTicks = 125;

		[Desc("MI: Rush squads micro inside a fight - focus-fire the fastest-kill observed target, damaged members pull back behind the formation anchor, outranging members hold a kite standoff. Micro orders spend IBotActionBudget actions when a producer is present. Own cell, independent of FormationMovement.")]
		public readonly bool SquadMicroEnabled = false;

		[Desc("MI: percent of max HP at or below which a squad member pulls back (at the threshold pulls back).")]
		public readonly int SquadMicroRetreatPct = 35;

		[Desc("MI: cells beyond the target's own range that a kiting member keeps as standoff margin.")]
		public readonly int SquadMicroKiteMarginCells = 2;

		[Desc("6f: Rush squads gather at the own building nearest the target before committing, so the wave arrives together.")]
		public readonly bool StageBeforeAssault = false;

		[Desc("Percent of squad units that must reach the staging point before the assault proceeds.")]
		public readonly int StageAssemblePercent = 60;

		[Desc("Cells around the staging point within which a unit counts as assembled.")]
		public readonly int StageRadiusCells = 8;

		[Desc("Ticks a staging squad waits before committing regardless of assembly.")]
		public readonly int StageTimeoutTicks = 750;

		[Desc("Extra units to treat as heal/repair support squads, beyond the derived set. " +
			"Derived at rules load: every armament must carry a negative-damage, ally-valid " +
			"warhead for the carrier to count as support — no central ids.")]
		public readonly HashSet<string> SupportUnitTypes = [];

		[Desc("Cells a support squad may trail behind its assault squad before catching up.")]
		public readonly int SupportFollowRangeCells = 6;

		[Desc("Prefer actors owned by the bot's main target player when picking a proactive attack target. Falls back to the nearest enemy when that player has no valid candidates.")]
		public readonly bool PreferMainTarget = false;
		[Desc("Allow published master-AI missions to defer or focus newly formed attack forces.")]
		public readonly bool UseMissions = true;
		[Desc("Maximum number of ticks a Defend mission may hold an otherwise ready attack force.")]
		public readonly int MissionDefendHoldTicks = 1500;

		[Desc("TC-2f (AI_ARCHITECTURE.md 12.27): when no published mission is affordable, a Raid card may still",
			"ride the launching wave up to the overcommit cap - the wave commits anyway, steering changes where,",
			"not whether. Off = unchanged classic behaviour.")]
		public readonly bool UseRaidMissionSteering = false;
		[Desc("Percent of the idle force value a steered Raid's RequiredValue may reach (300 = up to 3x overcommit;",
			"RequiredValue is calibrated for a dedicated force).")]
		public readonly int RaidMissionSteerOvercommitPercent = 300;
		[Desc("Floor for the steered-raid cap regardless of the idle pool's value. 0 = ratio only.")]
		public readonly int RaidMissionSteerMinValue = 0;

		[Desc("6g (CN A3): rules-derived BotTargetTags each squad type prefers when choosing targets (artillery, harvester, production, superweapon).")]
		public readonly HashSet<string> AssaultPriorityTags = [];
		public readonly HashSet<string> RushPriorityTags = [];
		public readonly HashSet<string> ArtilleryPriorityTags = [];
		public readonly HashSet<string> AirPriorityTags = [];
		public readonly HashSet<string> NavalPriorityTags = [];
		public readonly HashSet<string> GuerrillaPriorityTags = [];
		public readonly HashSet<string> HarassPriorityTags = [];
		public readonly HashSet<string> ProtectionPriorityTags = [];

		[Desc("Actor tags the support squads prefer to target.")]
		public readonly HashSet<string> SupportPriorityTags = [];

		[Desc("CA-5 (AI_ARCHITECTURE.md 12.8): split air units into fighter/gunship/bomber doctrine squads instead of one generic Air pool per actor type. Off = unchanged classic behaviour.")]
		public readonly bool AirDoctrineEnabled = false;

		[Desc("LC6: log a FOGCANARY-VIOLATION line when a decision consumes an actor this bot cannot observe (unfiltered enumeration or stale target). Diagnostic only - behavior unchanged.")]
		public readonly bool FogCanaryEnabled = false;

		[Desc("12.8: air-superiority role - hunt enemy aircraft, then pick off isolated units. Filled by BotRoleSets.")]
		public readonly HashSet<string> FighterTypes = [];

		[Desc("12.8: close air support role - attach to the main assault and engage what the frontline engages. Filled by BotRoleSets.")]
		public readonly HashSet<string> GunshipTypes = [];

		[Desc("12.8: strike-team role - mass, hit tag-priority targets through the air-threat router, regroup. Filled by BotRoleSets.")]
		public readonly HashSet<string> BomberTypes = [];

		[Desc("Bomber strike teams wait for this many members before flying (12.8: 2-4 aircraft).")]
		public readonly int BomberSquadMinSize = 2;

		[Desc("Bomber strike team cap; further bombers form another team.")]
		public readonly int BomberSquadMaxSize = 4;

		[Desc("Fighters pick off an enemy unit that has at most this many armed allies within DangerScanRadius of it (12.8: isolated targets).")]
		public readonly int FighterPickoffMaxEscorts = 3;

		[Desc("Gunships engage enemies within this many cells of their anchor squad's centre (12.8 CAS radius).")]
		public readonly int GunshipCASRadiusCells = 8;

		[Desc("Priority target tags for fighter pick-offs (e.g. harvester).")]
		public readonly HashSet<string> FighterPriorityTags = [BotTargetTags.Harvester];

		[Desc("Priority target tags for gunship CAS scans near the frontline: kill enemy artillery and straying harvesters first.")]
		public readonly HashSet<string> GunshipPriorityTags = [BotTargetTags.Artillery, BotTargetTags.Harvester];

		[Desc("Priority target tags for bomber strike teams (12.8 strike list: superweapon, conyard, production, refinery, power, harvester, artillery). 'defence' exists in BotTargetTags but is siege-conditional and stays off.")]
		public readonly HashSet<string> BomberPriorityTags = [BotTargetTags.Superweapon, BotTargetTags.Conyard, BotTargetTags.Production, BotTargetTags.Refinery, BotTargetTags.Power, BotTargetTags.Harvester, BotTargetTags.Artillery];

		[Desc("CN3: members per stealth squad - a full squad makes the next cloak-capable unit start another one.")]
		public readonly int StealthSquadMaxSize = 3;

		[Desc("CN3: stealth squads ambush soft high-value targets first (harvesters, then artillery).")]
		public readonly HashSet<string> StealthPriorityTags = [BotTargetTags.Harvester, BotTargetTags.Artillery];

		[Desc("Pre-commit risk gate (AI_FRANSBOT_RESEARCH.md 6c): a proactive ground squad only commits to a target when its unit value beats the remembered enemy threat at that region by this percent margin. Negative disables the gate.")]
		public readonly int AttackRiskMargin = 25;

		[Desc("Actor types to prioritise based on HighValueTargetPriority.")]
		public readonly HashSet<string> HighValueTargetTypes = new HashSet<string>();

		[Desc("Percent change for air squads (that can attack aircraft) to prioritise enemy aircraft.")]
		public readonly int AirToAirPriority = 85;

		[Desc("Limit target types for specific air unit squads.")]
		public readonly Dictionary<string, BitSet<TargetableType>> AirSquadTargetTypes = null;

		[Desc("CA F2p2 (162f00bb6): limit the targets of specific air unit squads by the ARMOR type of the target (key: air unit actor type,",
			"value: armor type names, matched against the target's Armor traits). Squads whose unit type has no entry are unaffected.",
			"Empty (the default) keeps the targetable-type behaviour of AirSquadTargetTypes.")]
		public readonly Dictionary<string, HashSet<string>> AirSquadTargetArmorTypes = null;

		[Desc("CA F2p2 (upstream 'Prioritize buildings over other enemy units', maintainer ruling 2026-10-01): the general squad target search picks the",
			"closest VISIBLE enemy building before other enemy units. Candidates stay the observed, fog-honest ones.")]
		public readonly bool PreferBuildingTargets = false;

		[Desc("CA F2p2 (upstream value-only attack force, maintainer ruling 2026-10-01): launch an attack squad on idle unit value alone (SquadValue > 0),",
			"without the SquadSize unit-count gate. MaxIdleUnits still forces a launch.")]
		public readonly bool ValueOnlyAttackLaunch = false;

		[Desc("CA F2p2 (2bad89a77): harass / indirect routes start from the own base building closest to the target (or the squad leader when closer)",
			"instead of from the squad leader. Falls back to the leader when no route is found from the building.")]
		public readonly bool RouteFromNearestOwnBuilding = false;

		[Desc("CA F2p2 (2bad89a77, 9a68fea15, b831676de): upstream squad state tweaks.",
			"Idle squads return to base with AttackMove instead of Move; an attacking ground squad that loses its target picks an opportunity target",
			"in AttackScanRadius or resumes AttackMove instead of fleeing; its stuck-drop-to-idle delay is 100 ticks instead of 63;",
			"buildings are recognised by RepairableBuilding instead of Building (walls and some defences stop counting as buildings).")]
		public readonly bool UseUpstreamStateTweaks = false;

		[Desc("Enemy building types around which to scan for targets for naval squads.")]
		public readonly HashSet<string> StaticAntiAirTypes = new HashSet<string>();

		[Desc("Air threats to prioritise above all others.")]
		public readonly HashSet<string> BigAirThreats = new HashSet<string>();

		[Desc("Locomotor used by pathfinding leader for squads")]
		public readonly HashSet<string> SuggestedGroundLeaderLocomotor = new();

		[Desc("Locomotor used by pathfinding leader for squads")]
		public readonly HashSet<string> SuggestedNavyLeaderLocomotor = new();

		[Desc("Percent chance that a regular assault squad will take an indirect (flanking) route instead of the most direct path. 0 to disable.")]
		public readonly int IndirectRouteChance = 0;

		[Desc("Ask region-memory routers (IBotRouteThreatRouter) for waypoints that skirt remembered enemy threat (AI_FRANSBOT_RESEARCH.md 6e). Squads fall back to normal routing when no router answers.")]
		public readonly bool UseRiskRouting = true;

		[Desc("DEPRECATED (AI_ARCHITECTURE.md 12.4a): artillery membership prefers ArtilleryTypes,",
			"the role-derived list; this field is the FALLBACK when that list is empty - @classic",
			"still relies on it. Kept so existing yaml entries load silently.")]
		public readonly int ArtilleryMinRangeCells = 10;

		[Desc("Cells an artillery squad trails its parent assault squad, measured away from the parent's target.")]
		public readonly int ArtilleryHangBackCells = 8;

		[Desc("UT-1 (AI_DEEP_RESEARCH.md §5.1): the MinimumAttackForceDelay reset scales by the",
			"master's Turtle<->Rush utility axis (IBotUtilityAxes) — 100 (Rush) x0.6, 50 x1.0,",
			"0 (Turtle) x1.5. Off, or no enabled provider, keeps the unchanged delay.")]
		public readonly bool UseUtilityAxes = false;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (DangerScanRadius <= 0)
				throw new YamlException("DangerScanRadius must be greater than zero.");

			if (SquadValueMaxEarlyBonus > SquadValueMaxLateBonus)
				throw new YamlException("SquadValueMaxEarlyBonus cannot be greater than SquadValueMaxLateBonus.");

			if (SquadValueMinLateBonus > SquadValueMaxLateBonus)
				throw new YamlException("SquadValueMinLateBonus cannot be greater than SquadValueMaxLateBonus.");

			if (DirectorBuildUpForceScalePercent < 0 || DirectorPressureForceScalePercent < 0 ||
				DirectorClimaxForceScalePercent < 0 || DirectorReliefForceScalePercent < 0)
				throw new YamlException("Director force scale percents cannot be negative.");

			if (DirectorBuildUpForceScalePercent > 400 || DirectorPressureForceScalePercent > 400 ||
				DirectorClimaxForceScalePercent > 400 || DirectorReliefForceScalePercent > 400)
				throw new YamlException("Director force scale percents above 400 are not supported.");

			if (DefendReserveTurtleFactorPercent < 0 || DefendReserveRushFactorPercent < 0)
				throw new YamlException("Defend-reserve axis factor percents cannot be negative.");

			if (DefendReserveTurtleFactorPercent > 400 || DefendReserveRushFactorPercent > 400)
				throw new YamlException("Defend-reserve axis factor percents above 400 are not supported.");

			if (SquadValueRandomBonus != 0 &&
				(SquadValueMaxEarlyBonus != 0 || SquadValueMinLateBonus != 0 || SquadValueMaxLateBonus != 0))
				throw new YamlException("SquadValueRandomBonus cannot be combined with squad value ramp bonuses.");

			// A RoleMix key outside the combat taxonomy can never be counted or filled —
			// fail at load like a predicate typo instead of silently starving the queue.
			if (RoleMix != null)
				foreach (var role in RoleMix.Keys)
					if (!BotUnitRole.CombatRoles.Contains(role))
						throw new YamlException($"RoleMix key `{role}` is not a combat role (valid: {string.Join(", ", BotUnitRole.PrimaryRoleOrder)}).");

			// Derive support units from weapon metadata: an actor is support only when
			// EVERY armament it carries heals (negative-damage, ally-valid warhead).
			// Requiring all armaments excludes hybrids that also fight — the RA2 IFVs,
			// Tesla Trooper, WC2 knights/paladins and the SCV each carry a heal weapon
			// alongside damage weapons and must not be pulled out of combat squads.
			foreach (var actor in rules.Actors.Values)
			{
				// Support must be mobile to follow a squad — a heal-armament building
				// (repair aura/depot) is not a squad member.
				if (actor.Name.StartsWith('^') ||
					(!actor.HasTraitInfo<MobileInfo>() && !actor.HasTraitInfo<AircraftInfo>()))
					continue;

				var armaments = actor.TraitInfos<ArmamentInfo>()
					.Where(a => !string.IsNullOrEmpty(a.Weapon))
					.ToList();

				if (armaments.Count == 0)
					continue;

				// An unresolvable weapon cannot be proven to heal, so it disqualifies.
				if (armaments.All(a =>
					rules.Weapons.TryGetValue(a.Weapon.ToLowerInvariant(), out var weapon) &&
					weapon.Warheads.Any(w => w is DamageWarhead dw && dw.Damage < 0 &&
						dw.ValidRelationships.HasRelationship(PlayerRelationship.Ally))))
				{
					SupportUnitTypes.Add(actor.Name);
				}
			}
		}

		public override object Create(ActorInitializer init) { return new SquadManagerBotModuleCA(init.Self, this); }
	}

	public class SquadManagerBotModuleCA : ConditionalTrait<SquadManagerBotModuleCAInfo>, IBotEnabled, IBotTick, IBotRespondToAttack, IBotPositionsUpdated, IGameSaveTraitData, INotifyActorDisposing, IBotMissionAssignmentProvider
	{
		const float SquadValueRampDurationTicks = 20f * 60f * 25f; // Assumes the default 25 ticks per second.

		// CA F2p2 (2bad89a77): own base buildings for route planning, from the construction yard index (no world scan).
		public IEnumerable<Actor> OwnBaseBuildings => constructionYardBuildings.Actors;

		public CPos GetRandomBaseCenter()
		{
			var randomConstructionYard = constructionYardBuildings.Actors.RandomOrDefault(World.LocalRandom);

			return randomConstructionYard?.Location ?? initialBaseCenter;
		}

		public readonly World World;
		public readonly Player Player;

		public readonly Predicate<Actor> unitCannotBeOrdered;
		readonly List<UnitWposWrapper> unitsHangingAroundTheBase = new();

		// Units that the bot already knows about. Any unit not on this list needs to be given a role.
		readonly List<Actor> activeUnits = new();

		public List<SquadCA> Squads = new();

		// §12.14 PL: attacks-launched telemetry (record-only).
		public int OffensiveSquadsLaunched;
		readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> constructionYardBuildings;

		IBot bot;
		IBotPositionsUpdated[] notifyPositionsUpdated;
		IBotNotifyIdleBaseUnits[] notifyIdleBaseUnits;
		IBotAircraftBuilder[] aircraftBuilders;
		IBotMainTargetProvider[] mainTargetProviders;
		IBotRegionThreatProvider[] threatProviders;
		IBotFoggedEnemyProvider[] fogProviders;
		IBotRouteThreatRouter[] routeRouters;
		IBotPersonalityLeadProvider[] leadProviders;
		IBotMissionProvider[] missionProviders;
		IBotMissionOutcomeSink[] missionOutcomeSinks;
		IBotSiegeAdvisor[] siegeAdvisors;
		IBotUnitRoles unitRoles;

		// The merged roles provider (§12.4, Cameo assembly) is a genericbot-gated
		// ConditionalTrait, so resolve lazily — at Created its condition may not be
		// granted yet. Null provider = every roles-driven feature stays off.
		internal IBotUnitRoles UnitRoles =>
			unitRoles ??= Player.PlayerActor.TraitsImplementing<IBotUnitRoles>().FirstEnabledTraitOrDefault();

		// Squad states read the actor->roles map through here (12.7 formation).
		internal IReadOnlyDictionary<string, HashSet<string>> ActorRoles => UnitRoles?.ActorRoles;

		CPos initialBaseCenter;
		Actor airStrikeTarget;
		public CPos[] airStrikeGrid;

		int rushTicks;
		int assignRolesTicks;
		int attackForceTicks;
		int protectionForceTicks;

		// DF-2: where the protection squad waits for a predicted attack, and until when.
		CPos? protectionRally;
		int protectionHoldUntilTick = -1;

		// TC-2b/TC-3 (§12.17/§12.18): the requester whose defend attempt record is open
		// on the ally-answer protect rally — null while the squad serves an own threat or
		// escort. The record lets team_coordination_report count the answers its
		// defend_missions metric exists for.
		// TC-2b/TC-3 (§12.17/§12.18): the mission id of the defend_answer attempt open
		// on the protect rally — null while the squad serves an own threat or escort.
		// One open attempt per id: the rolling hold refresh extends it, a new requester
		// or a new rally cell supersedes it.
		string allyDefendOpen;

		// TC-3 (§12.28): the mission id of the assist_answer attempt open on the same
		// rally — tracked apart from allyDefendOpen so a defend<->assist switch closes
		// the superseded record with its own kind instead of crossing the grammars.
		string allyAssistOpen;

		// The mission id of the open shared-push (secure:<player>) attempt — each
		// Rush launch supersedes the last wave's record; a destroyed wave closes it.
		string securePushOpen;

		// Attempt numbering prefers the per-player BotMissionAttemptTracker: a
		// personality rotation swaps this instance for a sibling with an empty
		// missionAttemptCounters, and attempt 1 re-issued collides the
		// (mission_id, attempt) identity the jsonl schema declares unique.
		int NextMissionAttempt(string id)
		{
			var tracker = Player.PlayerActor.TraitOrDefault<BotMissionAttemptTracker>();
			if (tracker != null)
				return tracker.NextAttemptNumber(id);

			var attempt = missionAttemptCounters.GetValueOrDefault(id) + 1;
			missionAttemptCounters[id] = attempt;
			return attempt;
		}

		int CurrentMissionAttempt(string id)
		{
			return Player.PlayerActor.TraitOrDefault<BotMissionAttemptTracker>()?.CurrentAttemptNumber(id)
				?? missionAttemptCounters.GetValueOrDefault(id);
		}
		Player securePushTarget;

		// Answer ids released while the squad pivoted away — re-picking them inside the
		// cooldown reproduces the commit/release churn the metric flagged (off at 0).
		readonly Dictionary<string, int> allyAnswerCooldownUntil = new();
		int nextPrepositionTick;
		IBotThreatPredictionProvider[] threatPredictionProviders;

		// DESIGN 19.12: the army staging planner, null while no enabled provider exists (classic, switch off = today's behaviour).
		// Looked up once per tick; the planner only plans, this module remains the one that orders the idle pool.
		IBotArmyStaging armyStaging;
		int armyStagingTick = -1;
		int nextStagingTick;
		readonly Dictionary<Actor, (CPos Cell, int Tick)> stagingOrders = new();

		internal IBotArmyStaging ArmyStaging
		{
			get
			{
				if (armyStagingTick != World.WorldTick)
				{
					armyStagingTick = World.WorldTick;
					armyStaging = Player.PlayerActor.TraitsImplementing<IBotArmyStaging>().FirstEnabledTraitOrDefault();
				}

				return armyStaging;
			}
		}
		IBotProtectionRequestProvider[] protectionRequestProviders;
		IBotRequestUnitProduction[] unitRequesters;
		IBotUtilityAxes[] utilityAxesProviders;
		IBotScaleTargets[] scaleTargetProviders;

		// CN3: the detector-memory providers the stealth squads read. Conditional
		// (`cn3_stealth_squads`), so enablement is resolved per use, never cached.
		IBotStealthDoctrine[] stealthDoctrines;
		readonly Dictionary<SquadCA, int> fastSquadReactedUntil = new();
		int protectionQuietSinceTick = -1;
		int minAttackForceDelayTicks;
		BotMission heldDefendMission;
		int defendMissionHeldSince = -1;
		readonly HashSet<int> defendMissionExhaustedRegions = [];
		public BotMissionAssignment LastMissionAssignment { get; private set; }

		int protectOwnTicks;
		Actor protectOwnFrom;

		int desiredAttackForceValue;
		int desiredAttackForceSize;
		int stageSinceTick = -1;
		readonly Dictionary<string, int> cachedUnitValues = new();

		// Loss telemetry (situation log): the role, cost and position each unit held at the last
		// role pass. Squads drop dead units at several sites, so a death is detected here, on the
		// next pass, from this snapshot rather than at any one removal site.
		readonly Dictionary<Actor, (string Role, int Cost, CPos Location)> lastKnownRoles = new();
		readonly Dictionary<string, int> lossesByRole = new();
		readonly Dictionary<string, int> awayLossesByRole = new();

		/// <summary>Cumulative cost of units lost, by the role they held: a squad type or "idle".</summary>
		public IReadOnlyDictionary<string, int> LossesByRole => lossesByRole;

		/// <summary>The part of <see cref="LossesByRole"/> lost outside MaxBaseRadius of the base centre.</summary>
		public IReadOnlyDictionary<string, int> AwayLossesByRole => awayLossesByRole;

		BotLimits botLimits;
		int initialAttackDelay;
		bool limitsRechecked;

		// H1 attention consumer: null when no IBotActionBudget producer is on the
		// player (then squads act unconditionally, as before). squadCursor rotates
		// the per-round pass order so a spent budget staggers rather than starves.
		IBotActionBudget actionBudget;
		int squadCursor;

		// MI order consumer: micro orders (focus-fire, pull-back, kite) spend
		// action budget; a null producer (no HumanPace module) means unlimited,
		// as before. Per-squad attention is already spent by the update loop —
		// callers must not consume TryConsumeAttention again.
		internal bool TryConsumeMicroActions(int count = 1)
		{
			return actionBudget == null || actionBudget.TryConsumeActions(count);
		}

		public SquadManagerBotModuleCA(Actor self, SquadManagerBotModuleCAInfo info)
			: base(info)
		{
			World = self.World;
			Player = self.Owner;

			unitCannotBeOrdered = a => a == null || a.Owner != Player || a.IsDead || !a.IsInWorld || a.CurrentActivity is Enter;
			constructionYardBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(World, info.ConstructionYardTypes, Player);
		}

		IReadOnlyDictionary<string, HashSet<string>> targetTagMap;

		// Lazily built per ruleset: actor name -> rules-derived BotTargetTags.
		internal IReadOnlyDictionary<string, HashSet<string>> TargetTags =>
			targetTagMap ??= BotTargetTags.BuildTagMap(World.Map.Rules);

		internal HashSet<string> PriorityTagsFor(SquadCAType type)
		{
			return type switch
			{
				SquadCAType.Air => Info.AirPriorityTags,
				SquadCAType.Fighter => Info.FighterPriorityTags,
				SquadCAType.Gunship => Info.GunshipPriorityTags,
				SquadCAType.Bomber => Info.BomberPriorityTags,
				SquadCAType.Artillery => Info.ArtilleryPriorityTags,
				SquadCAType.Naval => Info.NavalPriorityTags,
				SquadCAType.Rush => Info.RushPriorityTags,
				SquadCAType.Guerrilla => Info.GuerrillaPriorityTags,
				SquadCAType.Harass => Info.HarassPriorityTags,
				SquadCAType.Protection => Info.ProtectionPriorityTags,
				SquadCAType.Support => Info.SupportPriorityTags,
				SquadCAType.FireSupport => Info.SupportPriorityTags,
				SquadCAType.Stealth => Info.StealthPriorityTags,
				_ => Info.AssaultPriorityTags,
			};
		}

		internal HashSet<string> TagsOf(Actor a)
		{
			return a != null && TargetTags.TryGetValue(a.Info.Name, out var tags) ? tags : null;
		}

		internal HashSet<string> TagsOf(ActorInfo info)
		{
			return info != null && TargetTags.TryGetValue(info.Name, out var tags) ? tags : null;
		}

		internal List<T> PreferSquadTargets<T>(List<T> candidates, SquadCA owner, Func<T, HashSet<string>> tagsOf)
		{
			return owner == null ? candidates : BotTargetTags.PreferTagged(candidates, owner.PriorityTags, tagsOf);
		}

		bool IsValidEnemyUnit(Actor a)
		{
			if (a == null || a.IsDead || Player.RelationshipWith(a.Owner) != PlayerRelationship.Enemy || a.Info.HasTraitInfo<HuskInfo>() || a.Info.HasTraitInfo<CarrierSlaveInfo>())
				return false;

			var targetTypes = a.GetEnabledTargetTypes();
			return !targetTypes.IsEmpty && !targetTypes.Overlaps(Info.IgnoredEnemyTargetTypes);
		}

		// Use for proactive targeting.
		public bool IsPreferredEnemyUnit(Actor a)
		{
			return IsValidEnemyUnit(a) && !a.Info.HasTraitInfo<AircraftInfo>();
		}

		public bool IsPreferredEnemyBuilding(Actor a)
		{
			return IsValidEnemyUnit(a) && (Info.UseUpstreamStateTweaks
				? a.Info.HasTraitInfo<RepairableBuildingInfo>()
				: a.Info.HasTraitInfo<BuildingInfo>());
		}

		public bool IsPreferredEnemyAircraft(Actor a)
		{
			return IsValidEnemyUnit(a) && a.Info.HasTraitInfo<AircraftInfo>() && a.Info.HasTraitInfo<AttackBaseInfo>();
		}

		public bool IsHighValueTarget(Actor a)
		{
			return IsValidEnemyUnit(a) && Info.HighValueTargetTypes.Contains(a.Info.Name);
		}

		public bool IsAirSquadTargetType(Actor a, SquadCA owner)
		{
			if (a == null || a.IsDead)
				return false;

			var airSquadUnitType = owner.Units[0].Actor.Info.Name;

			// CA F2p2 (162f00bb6): per-type armor filter; only for unit types that have an entry.
			var armorTypes = owner.SquadManager.Info.AirSquadTargetArmorTypes;
			if (armorTypes != null && armorTypes.TryGetValue(airSquadUnitType, out var desiredArmorTypes)
				&& !a.Info.TraitInfos<ArmorInfo>().Any(ai => desiredArmorTypes.Contains(ai.Type)))
				return false;

			if (owner.SquadManager.Info.AirSquadTargetTypes.ContainsKey(airSquadUnitType))
			{
				var targetTypes = a.GetEnabledTargetTypes();

				if (targetTypes.IsEmpty || !targetTypes.Overlaps(owner.SquadManager.Info.AirSquadTargetTypes[airSquadUnitType]))
					return false;
			}

			return true;
		}

		public bool IsNotHiddenUnit(Actor a)
		{
			return a.CanBeViewedByPlayer(Player);
		}

		// 6d fogged observation: when a provider reports fogged scans, squads only
		// pick targets they can see (or remember via FrozenActorLayer). Without a
		// provider the legacy omniscient scans run unchanged — same degradation
		// rule as the risk gate.
		internal bool FoggedScans => FoggedScansActive(IsTraitDisabled, fogProviders);

		// LC6 semantic fog canary: when enabled, every actor a decision consumes must
		// already be observable to this bot — an unfiltered enumeration, a stale
		// remembered target, or a gate counted on an unseen unit all surface as a
		// greppable FOGCANARY-VIOLATION line. Log-only: behavior is unchanged, the
		// line is the evidence the harness greps for.
		internal void CanaryObserved(Actor a, string site)
		{
			if (!Info.FogCanaryEnabled || a == null)
				return;

			FogCanaryViolation(FoggedScans, IsNotHiddenUnit(a), site, a.Info.Name,
				line => AIUtils.BotDebug("AI ({0}): {1}", Player.ClientIndex, line));
		}

		// LC6: same canary over a consumed list — each element is a decision
		// input. Violations stay zero while every upstream filter holds; the
		// list overload keeps per-call-site loops out of the states.
		internal void CanaryObservedAll(IEnumerable<Actor> actors, string site)
		{
			if (!Info.FogCanaryEnabled || actors == null)
				return;

			foreach (var a in actors)
				CanaryObserved(a, site);
		}

		// The pure core so tests can drive it without an Actor/World: a violation is
		// exactly "fog is binding AND the consumed actor was not observable".
		public static bool FogCanaryViolation(bool foggedScans, bool observed, string site, string actorName, Action<string> log)
		{
			if (!foggedScans || observed)
				return false;

			log?.Invoke($"FOGCANARY-VIOLATION site={site} actor={actorName} — decision consumed an unseen actor");
			return true;
		}

		// 6e risk routing: ask region-memory routers for waypoints that skirt
		// remembered threat. Returns null (caller keeps direct routing) when
		// disabled, no router answers, or the router has no useful detour.
		internal List<CPos> RouteAroundThreat(Actor leader, CPos target, int maxWaypoints = 4)
		{
			if (!Info.UseRiskRouting || IsTraitDisabled || routeRouters == null)
				return null;

			foreach (var router in routeRouters)
			{
				var route = router.RouteAroundThreat(leader, target, maxWaypoints);
				if (route != null && route.Count > 0)
					return route;
			}

			return null;
		}

		public static bool FoggedScansActive(bool traitDisabled, IBotFoggedEnemyProvider[] providers)
		{
			return !traitDisabled && providers != null && providers.Any(p => p.FoggedObservation);
		}

		// 6f + 12.4a: role-derived artillery classification - members of the artillery
		// role (ArtilleryTypes). The range rule this replaced is kept as MaximumEnabledRange
		// for the combat predictor and other callers.
		internal bool IsArtilleryUnit(Actor a)
		{
			if (a == null || a.Info.HasTraitInfo<AircraftInfo>() || a.Info.HasTraitInfo<BuildingInfo>())
				return false;

			// The role list wins when populated; an unapplied instance (e.g. @classic,
			// which stays on its written config) keeps the old range rule so the A/B
			// reference does not move (cameo-mod#633 convention).
			if (Info.ArtilleryTypes.Count > 0)
				return Info.ArtilleryTypes.Contains(a.Info.Name);

			return Info.ArtilleryMinRangeCells >= 0
				&& MaximumEnabledRange(a) >= WDist.FromCells(Info.ArtilleryMinRangeCells);
		}

		// ActorInfo twin of IsArtilleryUnit - the same role-list-first rule applied to a
		// buildable candidate (MaxRange comes from the unit profile, not live traits).
		internal bool IsArtilleryUnit(ActorInfo ai)
		{
			if (ai == null || ai.HasTraitInfo<AircraftInfo>() || ai.HasTraitInfo<BuildingInfo>())
				return false;

			if (Info.ArtilleryTypes.Count > 0)
				return Info.ArtilleryTypes.Contains(ai.Name);

			return Info.ArtilleryMinRangeCells >= 0
				&& BotUnitProfiles.Get(World.Map.Rules, ai).MaxRange >= WDist.FromCells(Info.ArtilleryMinRangeCells);
		}

		// A ship is a `naval` locomotor (the navalunit role's rule); hover and amphibious
		// units move on land and stay ground units (12.4a). NavalUnitsTypes stays as a
		// belt for naval actors carried on other locomotors - a ship must never reach a
		// ground or air squad even when the list misses it.
		internal bool IsNavalUnit(Actor a) =>
			a != null && (a.Info.TraitInfoOrDefault<MobileInfo>()?.Locomotor == "naval" || Info.NavalUnitsTypes.Contains(a.Info.Name));

		// CA-5 (12.8): air-family squad bookkeeping (NewUnits/Waiting/Rearming) applies
		// to the generic Air squads and the three doctrine types alike.
		internal static bool IsAirFamily(SquadCAType type) =>
			type is SquadCAType.Air or SquadCAType.Fighter or SquadCAType.Gunship or SquadCAType.Bomber;

		// CA-5 (12.8): which squad an air actor joins when AirDoctrineEnabled splits the
		// air pool by role. Unroled air (transports, scouts) stays in generic Air squads.
		// Pure so tests can drive it without a World.
		public static SquadCAType AirSquadTypeFor(
			bool doctrineEnabled, string actorName,
			IReadOnlySet<string> fighterTypes, IReadOnlySet<string> gunshipTypes, IReadOnlySet<string> bomberTypes)
		{
			if (!doctrineEnabled)
				return SquadCAType.Air;

			if (fighterTypes.Contains(actorName))
				return SquadCAType.Fighter;

			if (gunshipTypes.Contains(actorName))
				return SquadCAType.Gunship;

			if (bomberTypes.Contains(actorName))
				return SquadCAType.Bomber;

			return SquadCAType.Air;
		}

		// CA-5 ordering rule (12.8): a WRITTEN GuerrillaTypes listing outranks a derived
		// fighter/gunship/bomber role — but only when the doctrine is on. With the flag
		// off the master order stands (the air branch runs before guerrilla), so
		// @classic's overlap actors keep routing to Air squads exactly as written.
		public static bool GuerrillaOutranksAir(
			bool doctrineEnabled, string actorName, IReadOnlySet<string> guerrillaTypes)
		{
			return doctrineEnabled && guerrillaTypes.Contains(actorName);
		}

		// A member of the written AirUnitsTypes list or - only when the doctrine split is
		// enabled - an actor the role derivation classes as fighter/gunship/bomber. The
		// role lists heal actors the written list misses, but never pull one out of
		// a role squad into generic Air.
		internal bool IsAirUnit(Actor a)
		{
			if (a == null)
				return false;

			if (Info.AirUnitsTypes.Contains(a.Info.Name))
				return true;

			return AirSquadTypeFor(
				Info.AirDoctrineEnabled, a.Info.Name,
				Info.FighterTypes, Info.GunshipTypes, Info.BomberTypes) != SquadCAType.Air;
		}

		internal SquadCAType AirSquadTypeFor(string actorName) =>
			AirSquadTypeFor(Info.AirDoctrineEnabled, actorName, Info.FighterTypes, Info.GunshipTypes, Info.BomberTypes);

		static readonly BitSet<TargetableType> InfantryTargetTypes = new("Infantry");
		static readonly BitSet<TargetableType> GroundTargetTypes = new("Ground");
		static readonly BitSet<TargetableType> AirTargetTypes = new("Air");

		// An artillery escort is the screen's frontline: an armed ground vehicle that
		// can hit ground targets. Infantry cannot keep up, AA-only platforms and
		// support units cannot win the flanker fight, ships cannot screen land guns
		// (12.4a review: the escort pull must pick fighters, not any-kind units).
		internal bool CanEscortArtillery(Actor a) =>
			a.Info.HasTraitInfo<AttackBaseInfo>()
			&& !a.Info.HasTraitInfo<AircraftInfo>()
			&& !a.Info.HasTraitInfo<HarvesterInfo>()
			&& !a.Info.HasTraitInfo<BuildingInfo>()
			&& !IsNavalUnit(a)
			&& !Info.SupportUnitTypes.Contains(a.Info.Name)
			&& !a.GetAllTargetTypes().Overlaps(InfantryTargetTypes)
			&& BotUnitProfiles.Get(World.Map.Rules, a.Info).Weapons.Any(w => w.CanTarget(GroundTargetTypes));

		// A unit covers its squad against air if any of its weapons can hit an air
		// target - the unit-profile weapon table keeps this faction-agnostic (no
		// hard-coded type lists, 12.4a/CA-3).
		internal bool CanHitAir(Actor a) =>
			a.Info.HasTraitInfo<AttackBaseInfo>()
			&& BotUnitProfiles.Get(World.Map.Rules, a.Info).Weapons.Any(w => w.CanTarget(AirTargetTypes));

		// Fog-honest enemy mix read via the canonical composition provider: the
		// master AI's fog memory carries remembered mobile combat value by actor
		// type, buildings already excluded. A caller with no provider (no fog
		// observation) gets (0, 0) - below the sample floor, so the mixed-army
		// prior stands and nothing omniscient leaks in.
		internal (double Air, double Total) ObservedEnemyMix()
		{
			var provider = Player.PlayerActor.TraitsImplementing<IBotEnemyCompositionProvider>().FirstOrDefault();
			if (provider == null || !provider.TryGetEnemyComposition(out var valueByActorType))
				return (0, 0);

			var air = 0.0;
			var total = 0.0;
			foreach (var (name, value) in valueByActorType)
			{
				if (!World.Map.Rules.Actors.TryGetValue(name, out var info))
					continue;

				total += value;
				if (info.HasTraitInfo<AircraftInfo>())
					air += value;
			}

			return (air, total);
		}

		// The required AA share of the assault's value. Base = the time ramp (the
		// mixed-army prior); with a confident enemy read it instead answers the
		// OBSERVED air share at AntiAirEscortResponsePct - or relaxes to the token
		// floor when the enemy provably fields no air.
		internal double RequiredAntiAirShare()
		{
			var baseShare = Info.AntiAirEscortRampTicks <= 0
				? Info.AntiAirEscortMaxSharePct / 100.0
				: (Info.AntiAirEscortMinSharePct
					+ (Info.AntiAirEscortMaxSharePct - Info.AntiAirEscortMinSharePct)
						* Math.Min(1.0, (double)World.WorldTick / Info.AntiAirEscortRampTicks)) / 100.0;

			var (air, total) = ObservedEnemyMix();
			if (total < Info.AntiAirEscortMinArmySample)
				return baseShare;

			if (air <= 0)
				return Math.Min(baseShare, Info.AntiAirEscortRelaxedSharePct / 100.0);

			var respond = air / total * Info.AntiAirEscortResponsePct / 100.0;
			return Math.Min(Info.AntiAirEscortCapSharePct / 100.0, Math.Max(baseShare, respond));
		}

		// The cheapest buildable ground unit that can hit air - it fields fastest and
		// masses easiest. Returns null when no queue can make one (e.g. tech not up).
		ActorInfo PickAntiAirUnit()
		{
			var rules = World.Map.Rules;
			return Player.PlayerActor.TraitsImplementing<ProductionQueue>()
				.SelectMany(q => q.BuildableItems())
				.Where(ai => !ai.HasTraitInfo<BuildingInfo>() && !ai.HasTraitInfo<AircraftInfo>()
					&& ai.HasTraitInfo<MobileInfo>()
					&& ai.TraitInfoOrDefault<MobileInfo>()?.Locomotor != "naval"
					&& BotUnitProfiles.Get(rules, ai).Weapons.Any(w => w.CanTarget(AirTargetTypes)))
				.OrderBy(ai => ai.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? int.MaxValue)
				.FirstOrDefault();
		}

		// The cheapest buildable ground artillery - a siege piece must trail a land
		// assault, so ships are out (same locomotor rule as the AA pick).
		ActorInfo PickArtilleryUnit()
		{
			return Player.PlayerActor.TraitsImplementing<ProductionQueue>()
				.SelectMany(q => q.BuildableItems())
				.Where(ai => ai.HasTraitInfo<MobileInfo>()
					&& ai.TraitInfoOrDefault<MobileInfo>()?.Locomotor != "naval"
					&& IsArtilleryUnit(ai))
				.OrderBy(ai => ai.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? int.MaxValue)
				.FirstOrDefault();
		}

		// CA-3 siege artillery: the main army always carries guns that outrange base
		// defences - at least ArtillerySiegeMinUnits pieces plus ArtillerySiegeSharePct
		// of assault value. Artillery already fielded in squads counts (it is the same
		// siege asset); a shortfall is pushed to production like the AA coverage.
		void RequestSiegeArtillery(IBot bot, SquadCA attackForce, List<UnitWposWrapper> freshArtillery)
		{
			var requester = unitRequesters.FirstOrDefault();
			if (requester == null)
				return;

			var candidate = PickArtilleryUnit();
			if (candidate == null)
				return;

			var fieldedCount = freshArtillery.Count;
			var fieldedValue = freshArtillery.Sum(u => UnitValue(u.Actor));
			foreach (var sq in Squads.Where(s => s.Type == SquadCAType.Artillery && s.IsValid))
			{
				fieldedCount += sq.Units.Count;
				fieldedValue += sq.Units.Sum(u => UnitValue(u.Actor));
			}

			var forceValue = attackForce.Units.Sum(u => UnitValue(u.Actor)) + fieldedValue;
			var share = Info.ArtillerySiegeSharePct / 100.0;
			var unitCost = candidate.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
			var neededForShare = unitCost > 0 && share > 0 && share < 1
				? (int)Math.Ceiling(Math.Max(0, share * forceValue - fieldedValue) / (unitCost * (1 - share)))
				: 0;
			var needed = Math.Max(Info.ArtillerySiegeMinUnits - fieldedCount, neededForShare);
			if (needed <= 0)
				return;

			var queued = requester.RequestedProductionCount(bot, candidate.Name);
			for (var i = queued; i < needed; i++)
				requester.RequestUnitProduction(bot, candidate.Name);

			AIUtils.BotDebug("AI ({0}): siege artillery {1} pieces - requested {2}x {3}",
				Player.ClientIndex, fieldedCount, needed - queued, candidate.Name);
		}

		// CA-3 anti-air coverage: an assault without AA dies to the first gunship it
		// cannot shoot back at. Required = the larger of a flat unit floor (never
		// fewer than AntiAirEscortMinUnits) and a share of the force's value ramping
		// 20->33% over the match. The idle pool is already drafted whole, so a
		// shortfall can only be fixed by production - request the missing escorts;
		// produced AA joins the pool and rides the next assault or protection draft.
		void RequestAntiAirCoverage(IBot bot, SquadCA attackForce)
		{
			var requester = unitRequesters.FirstOrDefault();
			if (requester == null)
				return;

			var candidate = PickAntiAirUnit();
			if (candidate == null)
				return;

			var aaCount = 0;
			var aaValue = 0;
			var forceValue = 0;
			foreach (var u in attackForce.Units)
			{
				var v = UnitValue(u.Actor);
				forceValue += v;
				if (CanHitAir(u.Actor))
				{
					aaCount++;
					aaValue += v;
				}
			}

			// Units needed for the value share - each requested unit also grows the
			// force, so solve the fixpoint: x >= (share*V - aa) / (cost*(1-share)).
			var share = RequiredAntiAirShare();
			var unitCost = candidate.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
			var neededForShare = unitCost > 0 && share > 0 && share < 1
				? (int)Math.Ceiling(Math.Max(0, share * forceValue - aaValue) / (unitCost * (1 - share)))
				: 0;
			var needed = Math.Max(Info.AntiAirEscortMinUnits - aaCount, neededForShare);
			if (needed <= 0)
				return;

			// Don't stack requests: only ask for what isn't already queued.
			var queued = requester.RequestedProductionCount(bot, candidate.Name);
			for (var i = queued; i < needed; i++)
				requester.RequestUnitProduction(bot, candidate.Name);

			AIUtils.BotDebug("AI ({0}): assault AA coverage {1} units / {2}% of value - requested {3}x {4} (target share {5}%)",
				Player.ClientIndex, aaCount, aaValue * 100 / Math.Max(1, forceValue), needed - queued, candidate.Name, (int)(share * 100));
		}

		// Longest range over the actor's enabled attack traits. Never TraitOrDefault<AttackBase>:
		// 76 mobile ground actors carry two or more (e.g. AttackFrontal + AttackFollow on
		// ts_nod_attackbuggy), and TraitOrDefault throws on the second one.
		internal static WDist MaximumEnabledRange(Actor a)
		{
			var range = WDist.Zero;
			foreach (var attack in a.TraitsImplementing<AttackBase>())
			{
				if (attack.IsTraitDisabled)
					continue;

				var r = attack.GetMaximumRange();
				if (r > range)
					range = r;
			}

			return range;
		}

		// The assault squad an artillery squad trails: nearest living Rush squad.
		internal SquadCA FindAttachableAssault(SquadCA artillery)
		{
			if (!artillery.IsValid)
				return null;

			var from = artillery.Units[0].Actor.CenterPosition;
			SquadCA best = null;
			var bestDistance = long.MaxValue;
			foreach (var squad in Squads)
			{
				if (squad == artillery || !squad.IsValid || squad.Type != SquadCAType.Rush)
					continue;

				var distance = (squad.CenterPosition - from).HorizontalLengthSquared;
				if (distance < bestDistance)
				{
					bestDistance = distance;
					best = squad;
				}
			}

			return best;
		}

		// Point hangBackLength behind the parent's position, away from the target.
		public static WPos HangBackAnchor(WPos parentPos, WPos targetPos, int hangBackLength)
		{
			var offset = parentPos - targetPos;
			var distance = offset.HorizontalLength;
			if (distance <= 0)
				return parentPos;

			return parentPos + new WVec(
				(int)((long)offset.X * hangBackLength / distance),
				(int)((long)offset.Y * hangBackLength / distance),
				0);
		}

		// IsPreferredEnemyUnit restricted to what the bot can currently observe.
		internal bool IsPreferredObservedEnemyUnit(Actor a)
		{
			return IsPreferredEnemyUnit(a) && (!FoggedScans || IsNotHiddenUnit(a));
		}

		// Fogged fallback target: an enemy building the engine's FrozenActorLayer
		// remembers under shroud. The layer invalidates the record when the cell
		// is re-observed empty, so a stale frozen target drops out on its own.
		internal FrozenActor FindFrozenEnemyTarget(WPos from, int attackerValue, SquadCA owner = null, Player targetPlayer = null)
		{
			var layer = Player.FrozenActorLayer;
			if (layer == null)
				return null;

			var map = World.Map;
			// Mirrors Target.IsValidFor's FrozenActor predicate: only rendered
			// ghosts count — hidden (revealed-empty) and invalid records drop out.
			var candidates = layer.FrozenActorsInRegion(map.AllCells)
				.Where(fa => fa.IsValid && fa.Visible && !fa.Hidden && fa.Owner != null
					&& Player.RelationshipWith(fa.Owner) == PlayerRelationship.Enemy
					&& (targetPlayer == null || fa.Owner == targetPlayer)
					&& !fa.TargetTypes.IsEmpty && !fa.TargetTypes.Overlaps(Info.IgnoredEnemyTargetTypes))
				.ToList();

			var mainTarget = EffectiveMainTarget();
			candidates = PreferOwned(candidates, mainTarget == null ? null : fa => fa.Owner == mainTarget);
			candidates = PreferSquadTargets(candidates, owner, fa => TagsOf(fa.Info));

			if (attackerValue >= 0)
				candidates.RemoveAll(fa => !PassesRiskGate(map.CellContaining(fa.CenterPosition), attackerValue));

			FrozenActor closest = null;
			var closestDistance = long.MaxValue;
			foreach (var fa in candidates)
			{
				var delta = fa.CenterPosition - from;
				var distance = (long)delta.LengthSquared;
				if (distance < closestDistance)
				{
					closestDistance = distance;
					closest = fa;
				}
			}

			return closest;
		}

		public bool IsValidAllyUnit(Actor a)
		{
			if (a == null || a.IsDead || Player.RelationshipWith(a.Owner) != PlayerRelationship.Ally || a.Info.HasTraitInfo<HuskInfo>() || a.Info.HasTraitInfo<CarrierSlaveInfo>())
				return false;

			return true;
		}

		public CPos[] AirstrikeGrid(Actor self)
		{
			var map = self.World.Map;
			var dangerRadius = Info.DangerScanRadius;

			var columnCount = (map.MapSize.Width + dangerRadius - 1) / dangerRadius;
			var rowCount = (map.MapSize.Height + dangerRadius - 1) / dangerRadius;

			var checkIndices = Exts.MakeArray(columnCount * rowCount, i => new MPos((i % columnCount) * dangerRadius + dangerRadius / 2, (i / columnCount) * dangerRadius + dangerRadius / 2).ToCPos(map));

			return checkIndices;
		}

		protected override void Created(Actor self)
		{
			notifyPositionsUpdated = self.Owner.PlayerActor.TraitsImplementing<IBotPositionsUpdated>().ToArray();
			notifyIdleBaseUnits = self.Owner.PlayerActor.TraitsImplementing<IBotNotifyIdleBaseUnits>().ToArray();
			aircraftBuilders = self.Owner.PlayerActor.TraitsImplementing<IBotAircraftBuilder>().ToArray();
			mainTargetProviders = self.Owner.PlayerActor.TraitsImplementing<IBotMainTargetProvider>().ToArray();
			threatProviders = self.Owner.PlayerActor.TraitsImplementing<IBotRegionThreatProvider>().ToArray();
			threatPredictionProviders = self.Owner.PlayerActor.TraitsImplementing<IBotThreatPredictionProvider>().ToArray();
			protectionRequestProviders = self.Owner.PlayerActor.TraitsImplementing<IBotProtectionRequestProvider>().ToArray();
			unitRequesters = self.Owner.PlayerActor.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
			fogProviders = self.Owner.PlayerActor.TraitsImplementing<IBotFoggedEnemyProvider>().ToArray();
			routeRouters = self.Owner.PlayerActor.TraitsImplementing<IBotRouteThreatRouter>().ToArray();
			leadProviders = self.Owner.PlayerActor.TraitsImplementing<IBotPersonalityLeadProvider>().ToArray();
			missionProviders = self.Owner.PlayerActor.TraitsImplementing<IBotMissionProvider>().ToArray();
			missionOutcomeSinks = self.Owner.PlayerActor.TraitsImplementing<IBotMissionOutcomeSink>().ToArray();
			siegeAdvisors = self.Owner.PlayerActor.TraitsImplementing<IBotSiegeAdvisor>().ToArray();
			utilityAxesProviders = self.Owner.PlayerActor.TraitsImplementing<IBotUtilityAxes>().ToArray();
			scaleTargetProviders = self.Owner.PlayerActor.TraitsImplementing<IBotScaleTargets>().ToArray();
			stealthDoctrines = self.Owner.PlayerActor.TraitsImplementing<IBotStealthDoctrine>().ToArray();
			airStrikeGrid = AirstrikeGrid(self);
		}

		protected override void TraitEnabled(Actor self)
		{
			botLimits = self.Owner.PlayerActor.TraitsImplementing<BotLimits>().FirstEnabledTraitOrDefault();
			actionBudget = self.Owner.PlayerActor.TraitsImplementing<IBotActionBudget>().FirstEnabledTraitOrDefault();

			if (botLimits != null)
				initialAttackDelay = botLimits.Info.InitialAttackDelay;

			limitsRechecked = false;

			// Avoid all AIs reevaluating assignments on the same tick, randomize their initial evaluation delay.
			assignRolesTicks = World.LocalRandom.Next(0, Info.AssignRolesInterval);
			attackForceTicks = World.LocalRandom.Next(0, Info.AttackForceInterval);
			protectionForceTicks = World.LocalRandom.Next(0, Info.ProtectInterval);
			minAttackForceDelayTicks = World.LocalRandom.Next(0, Info.MinimumAttackForceDelay) +
				RemainingInitialAttackDelay(initialAttackDelay, World.WorldTick);

			// Without this the desired force stays 0/0 and the very first
			// `idleUnits >= desired` check passes unconditionally — an empty Rush
			// squad on the first tick the module runs (and after every load).
			SetNextDesiredAttackForce();
		}

		protected override void TraitDisabled(Actor self)
		{
			heldDefendMission = null;
			defendMissionHeldSince = -1;
			defendMissionExhaustedRegions.Clear();
			foreach (var squad in Squads)
				DismissSquad(squad);

			Squads.Clear();
			activeUnits.Clear();
			unitsHangingAroundTheBase.Clear();

			// The next personality's manager takes these units over; counting their deaths here too
			// when this one is re-enabled would book them twice.
			lastKnownRoles.Clear();
			foreach (var n in notifyIdleBaseUnits)
				n.UpdatedIdleBaseUnits(unitsHangingAroundTheBase);
		}

		public static int RemainingInitialAttackDelay(int initialAttackDelay, int worldTick)
		{
			return Math.Max(0, initialAttackDelay - worldTick);
		}

		void IBotEnabled.BotEnabled(IBot bot)
		{
			this.bot = bot;
		}

		void IBotTick.BotTick(IBot bot)
		{
			// LC4: the BotLimits cached in TraitEnabled can predate the tier condition (BotLimitsResolver). A corrected
			// tier also corrects the initial attack delay; it only ever lengthens the wait already scheduled.
			if (!limitsRechecked)
			{
				limitsRechecked = true;
				var limits = BotLimitsResolver.Recheck(Player, botLimits, nameof(SquadManagerBotModuleCA));
				if (limits != botLimits)
				{
					botLimits = limits;
					initialAttackDelay = botLimits?.Info.InitialAttackDelay ?? 0;
					minAttackForceDelayTicks = Math.Max(minAttackForceDelayTicks, RemainingInitialAttackDelay(initialAttackDelay, World.WorldTick));
				}

				actionBudget ??= Player.PlayerActor.TraitsImplementing<IBotActionBudget>().FirstEnabledTraitOrDefault();
			}

			// A secure push resolves when its named enemy is decided — the wave's objective
			// is gone either way, so the open attempt books done rather than dangle to
			// supersede or match_end. WinState is scoreboard state, not a fog peek.
			if (securePushTarget != null && securePushTarget.WinState != WinState.Undefined)
				CloseSecurePush(BotMissionAttemptState.Success, BotMissionReasons.Done);

			AssignRolesToIdleUnits(bot);
			StageIdlePool(bot);
		}

		// DESIGN 19.12: the idle pool waits at the front. The provider says which group each unit joins and where that group stands;
		// this module (the pool's one owner) issues the AttackMove, at most once per StagingInterval per unit and only to units
		// that are far from their point. Units another module holds a lease on are left alone (DESIGN 19.6).
		void StageIdlePool(IBot bot)
		{
			var staging = ArmyStaging;
			if (staging == null || World.WorldTick < nextStagingTick)
				return;

			var interval = Math.Max(1, staging.StagingIntervalTicks);
			nextStagingTick = World.WorldTick + interval;

			var leases = BotUnitLeases.Of(Player);
			var pool = new List<ArmyStagingUnit>();
			foreach (var u in unitsHangingAroundTheBase)
			{
				var a = u.Actor;
				if (unitCannotBeOrdered(a) || Info.ExcludeFromSquadsTypes.Contains(a.Info.Name)
					|| !a.Info.HasTraitInfo<AttackBaseInfo>() || a.Info.HasTraitInfo<BuildingInfo>()
					|| a.Info.HasTraitInfo<HarvesterInfo>() || a.Info.HasTraitInfo<AircraftInfo>() || IsNavalUnit(a)
					|| BotUnitLeases.IsClaimedByOther(leases, a, LeaseOwner))
					continue;

				pool.Add(new ArmyStagingUnit(a, UnitValue(a)));
			}

			var assigned = new List<ArmyStagingOrder>();
			staging.AssignIdlePool(pool, assigned);

			var radius = (long)staging.StagingRadiusCells * staging.StagingRadiusCells;
			var byCell = new Dictionary<CPos, List<Actor>>();
			foreach (var o in assigned)
			{
				if ((o.Actor.Location - o.Cell).LengthSquared <= radius)
				{
					stagingOrders.Remove(o.Actor);
					continue;
				}

				// A unit already walking to this very cell keeps walking; an idle one (or one sent elsewhere) is re-ordered.
				if (stagingOrders.TryGetValue(o.Actor, out var last) && last.Cell == o.Cell && !o.Actor.IsIdle
					&& World.WorldTick - last.Tick < interval * 4)
					continue;

				if (!byCell.TryGetValue(o.Cell, out var list))
					byCell[o.Cell] = list = new List<Actor>();

				list.Add(o.Actor);
				stagingOrders[o.Actor] = (o.Cell, World.WorldTick);
			}

			foreach (var kv in byCell)
				bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(World, kv.Key), false, groupedActors: kv.Value.ToArray()));

			if (stagingOrders.Count > 256)
				foreach (var dead in stagingOrders.Keys.Where(a => a.IsDead || !a.IsInWorld).ToList())
					stagingOrders.Remove(dead);
		}

		internal Actor FindClosestEnemy(Actor sourceActor, SquadCA owner = null)
		{
			var units = World.Actors.Where(IsPreferredEnemyUnit).ToList();
			var mainTarget = EffectiveMainTarget();
			units = PreferOwned(units, mainTarget == null ? null : a => a.Owner == mainTarget);
			units = PreferSquadTargets(units, owner, TagsOf);
			var visible = units.Where(IsNotHiddenUnit).ToList();

			// CA F2p2 (A5-1): visible enemy buildings first; only the already-observed candidates are re-ordered.
			if (Info.PreferBuildingTargets)
			{
				var visibleBuildings = visible.Where(IsPreferredEnemyBuilding).ToList();
				if (visibleBuildings.Count > 0)
					visible = visibleBuildings;
			}

			// Fogged scans never fall back to actors the bot cannot see; remembered
			// enemy buildings are offered separately as FrozenActor targets.
			var picked = FoggedScans
				? visible.ClosestToIgnoringPath(sourceActor.CenterPosition)
				: visible.ClosestToIgnoringPath(sourceActor.CenterPosition) ?? units.Where(IsPreferredEnemyBuilding).ClosestToIgnoringPath(sourceActor.CenterPosition) ?? units.ClosestToIgnoringPath(sourceActor.CenterPosition);
			CanaryObserved(picked, "find-closest-enemy");
			return picked;
		}

		// 6c pre-commit risk gate: as FindClosestEnemy, but candidates whose region's
		// remembered enemy threat exceeds attackerValue by more than AttackRiskMargin
		// are skipped — an unknown region (threat 0) never blocks. When every
		// candidate fails the gate the squad holds instead of suiciding.
		internal Actor FindClosestEnemy(Actor sourceActor, int attackerValue, SquadCA owner = null)
		{
			var units = World.Actors.Where(IsPreferredEnemyUnit).ToList();
			var mainTarget = EffectiveMainTarget();
			units = PreferOwned(units, mainTarget == null ? null : a => a.Owner == mainTarget);
			units = PreferSquadTargets(units, owner, TagsOf);
			units.RemoveAll(u => !PassesRiskGate(u.Location, attackerValue));
			var visible = units.Where(IsNotHiddenUnit).ToList();

			var picked = FoggedScans
				? visible.ClosestToIgnoringPath(sourceActor.CenterPosition)
				: visible.ClosestToIgnoringPath(sourceActor.CenterPosition) ?? units.Where(IsPreferredEnemyBuilding).ClosestToIgnoringPath(sourceActor.CenterPosition) ?? units.ClosestToIgnoringPath(sourceActor.CenterPosition);
			CanaryObserved(picked, "find-closest-enemy");
			return picked;
		}

		// Fogged scans require a currently visible actor; mission consumers add remembered
		// FrozenActor targets separately. With FoggedScans disabled, the fallback may
		// select an unseen actor, inheriting the existing omniscient behavior of that
		// mode rather than introducing a mission-layer cheat.
		internal Actor FindClosestEnemy(CPos location, int attackerValue, Player targetPlayer, SquadCA owner = null)
		{
			if (targetPlayer == null)
				return null;

			var units = World.Actors
				.Where(a => a.Owner == targetPlayer && IsPreferredEnemyUnit(a))
				.ToList();
			units = PreferSquadTargets(units, owner, TagsOf);
			units.RemoveAll(u => !PassesRiskGate(u.Location, attackerValue));
			var visible = units.Where(IsNotHiddenUnit).ToList();
			var targetPosition = World.Map.CenterOfCell(location);
			var picked = FoggedScans
				? visible.ClosestToIgnoringPath(targetPosition)
				: visible.ClosestToIgnoringPath(targetPosition) ??
					units.Where(IsPreferredEnemyBuilding).ClosestToIgnoringPath(targetPosition) ??
					units.ClosestToIgnoringPath(targetPosition);
			CanaryObserved(picked, "find-closest-enemy-loc");
			return picked;
		}

		internal Actor FindHighValueTarget(WPos pos)
		{
			var units = World.Actors.Where(IsHighValueTarget).ToList();
			if (FoggedScans)
				units = units.Where(IsNotHiddenUnit).ToList();

			var mainTarget = EffectiveMainTarget();
			units = PreferOwned(units, mainTarget == null ? null : a => a.Owner == mainTarget);
			var picked = units.RandomOrDefault(World.LocalRandom);
			CanaryObserved(picked, "find-hv-target");
			return picked;
		}

		internal Actor FindHighValueTarget(WPos pos, int attackerValue)
		{
			var units = World.Actors.Where(IsHighValueTarget).ToList();
			if (FoggedScans)
				units = units.Where(IsNotHiddenUnit).ToList();

			var mainTarget = EffectiveMainTarget();
			units = PreferOwned(units, mainTarget == null ? null : a => a.Owner == mainTarget);
			units.RemoveAll(u => !PassesRiskGate(u.Location, attackerValue));
			var picked = units.RandomOrDefault(World.LocalRandom);
			CanaryObserved(picked, "find-hv-target");
			return picked;
		}

		internal int SquadValueOf(SquadCA squad)
		{
			var value = 0;
			foreach (var u in squad.Units)
			{
				if (!cachedUnitValues.TryGetValue(u.Actor.Info.Name, out var unitCost))
				{
					unitCost = u.Actor.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
					cachedUnitValues[u.Actor.Info.Name] = unitCost;
				}

				value += unitCost;
			}

			return value;
		}

		internal bool PassesRiskGate(Actor target, int attackerValue)
		{
			return PassesRiskGate(target.Location, attackerValue);
		}

		internal bool PassesRiskGate(CPos cell, int attackerValue)
		{
			var threat = threatProviders?.Sum(p => p.RememberedEnemyThreatAt(cell)) ?? 0;
			var pass = PassesRiskGate(attackerValue, threat, Info.AttackRiskMargin);
			if (!pass)
				AIUtils.BotDebug("AI ({0}): risk gate held a {1}-value squad off {2} (remembered threat {3}, margin {4}%)",
					Player.ClientIndex, attackerValue, cell, threat, Info.AttackRiskMargin);

			return pass;
		}

		public static bool PassesRiskGate(int attackerValue, int threat, int marginPercent)
		{
			if (marginPercent < 0 || threat <= 0)
				return true;

			return (long)attackerValue * 100 >= (long)threat * (100 + marginPercent);
		}

		// CA-2 siege consult (§12.6): ask the siege advisors what an advancing
		// assault squad should do. No advisor or all advising Advance leaves the
		// state machine's behaviour bit-identical to before.
		internal SiegeVerdict EvaluateSiege(SquadCA squad, out CPos standOffCell)
		{
			if (siegeAdvisors != null)
				foreach (var advisor in siegeAdvisors)
				{
					var verdict = advisor.VerdictFor(squad, out standOffCell);
					if (verdict != SiegeVerdict.Advance)
						return verdict;
				}

			standOffCell = CPos.Zero;
			return SiegeVerdict.Advance;
		}

		internal Actor FindClosestEnemy(Actor sourceActor, WDist radius, SquadCA owner = null)
		{
			var candidates = VisibleEnemiesNear(sourceActor.CenterPosition, radius);
			candidates = PreferSquadTargets(candidates, owner, TagsOf);
			return candidates.ClosestToIgnoringPath(sourceActor);
		}

		// Enemies this bot can SEE within `radius` (the one radius scan this file keeps for squad targeting).
		internal List<Actor> VisibleEnemiesNear(WPos center, WDist radius)
		{
			var enemies = World.FindActorsInCircle(center, radius)
				.Where(a => IsPreferredEnemyUnit(a) && IsNotHiddenUnit(a)).ToList();
			CanaryObservedAll(enemies, "visible-enemies-near");
			return enemies;
		}

		/// <summary>DF-2: the protection squad's rally point while a predicted attack is pending.</summary>
		internal bool TryGetProtectionRally(out CPos rally)
		{
			rally = protectionRally ?? CPos.Zero;
			return protectionRally.HasValue && World.WorldTick <= protectionHoldUntilTick;
		}

		/// <summary>DF-2: the most valuable predicted attack that arrives soon enough and is big enough to meet, or null.</summary>
		public static BotPredictedThreat? SelectPrepositionThreat(IEnumerable<BotPredictedThreat> threats, int maxEtaTicks, int minValue) =>
			threats.Where(t => t.EtaTicks <= maxEtaTicks && t.Value >= minValue)
				.OrderByDescending(t => t.Value).ThenBy(t => t.EtaTicks).Cast<BotPredictedThreat?>().FirstOrDefault();

		// DF-2: meet the most valuable predicted attack at the own defence nearest its target.
		void PrepositionDefenceTick(IBot bot)
		{
			var prepositionOn = Info.PrepositionDefence && threatPredictionProviders is { Length: > 0 };
			var requestsOn = Info.UseProtectionRequests && protectionRequestProviders is { Length: > 0 };
			var teamAnswersOn = Info.UseTeamDefendAnswers;
			var assistAnswersOn = Info.UseCoalitionAssist;
			if ((!prepositionOn && !requestsOn && !teamAnswersOn && !assistAnswersOn) || World.WorldTick < nextPrepositionTick)
				return;

			nextPrepositionTick = World.WorldTick + Math.Max(1, Info.ProtectInterval);
			var threat = prepositionOn
				? SelectPrepositionThreat(threatPredictionProviders.SelectMany(p => p.PredictedThreats),
					Info.PrepositionMaxEtaTicks, Info.PrepositionMinThreatValue)
				: null;

			// DESIGN 19.12: with a staging provider the live-reaction assignment decides which idle units answer an attack that
			// aims inside the base, so DF-2's prediction there is an input of that plan (it feeds the provider) and not a second
			// owner of the same pool. A threat aimed at a forward asset outside the ring keeps the draft below.
			var staging = ArmyStaging;
			if (threat != null && staging != null && staging.Covers(threat.Value.Target))
				threat = null;

			// An escort request is a standing defence job on the same army_value
			// scale - but a real incoming attack always outranks a guard job.
			var request = threat == null ? SelectProtectionRequest() : null;

			// TC-2b: an ally's broadcast defend request is a third channel, below own
			// threat and own escort. Synthesised as a BotProtectionRequest so rally,
			// draft, AttackMove and hold-expiry all reuse the escort path verbatim —
			// the rolling hold lets a retracted request release within one interval.
			// A thin home pool stays home regardless of how loud the request is.
			TeamBroadcast allyDefendAnswer = null;
			if (threat == null && request == null && teamAnswersOn &&
				unitsHangingAroundTheBase.Count >= Info.TeamDefendAnswerMinPoolUnits)
			{
				// TC-3 (§12.18): the coalition fold elects exactly one responder per defend
				// request — the nearest free ally by ArmyCentroid. A published election is
				// binding: we answer only our own assignment, and not being elected is a
				// stand-down, not a fallback. No provider or an empty election keeps today's
				// TopDefendRequest pick verbatim.
				var election = Info.UseCoalitionRescue
					? Player.PlayerActor.TraitsImplementing<IBotCoalition>().FirstEnabledTraitOrDefault()?.Coalition?.RescueAssignments
					: null;
				TeamBroadcast answered = null;
				if (election is { Count: > 0 })
				{
					// Participant identity is InternalName (map-side bots can share a
					// ClientIndex); a null id on the assignment is the pre-id broadcast,
					// matched by the marked ClientIndex fallback.
					var myId = Player.InternalName ?? "#" + Player.ClientIndex;
					var elected = election.FirstOrDefault(a =>
						a.ResponderId == myId || (a.ResponderId == null && a.ResponderClientIndex == Player.ClientIndex));
					if (elected != null)
					{
						var broadcasts = TeamBlackboard.CollectBroadcasts(Player);
						var rallyCell = World.Map.CellContaining(elected.DefendPosition);
						if (!AnswerOnCooldown("defend_answer",
							elected.RequesterId ?? "#" + elected.RequesterClientIndex, rallyCell))
						{
							answered = broadcasts.FirstOrDefault(b => b != null
								&& (CoalitionFold.ParticipantKey(b) == elected.RequesterId
									|| (elected.RequesterId == null && b.ClientIndex == elected.RequesterClientIndex)));
							var armyValue = answered?.OwnArmyValue
								?? broadcasts.Where(b => b != null).Select(b => b.OwnArmyValue).DefaultIfEmpty().Max();
							request = new BotProtectionRequest(rallyCell,
								armyValue, World.WorldTick + Info.ProtectInterval * 10);
						}
					}
				}
				else
				{
					answered = TeamBlackboard.TopDefendRequest(TeamBlackboard.CollectBroadcasts(Player)
						.Where(b => b == null || b.DefendPosition == WPos.Zero
							|| !AnswerOnCooldown("defend_answer", CoalitionFold.ParticipantKey(b),
								World.Map.CellContaining(b.DefendPosition))));
					if (answered != null)
						request = new BotProtectionRequest(World.Map.CellContaining(answered.DefendPosition),
							answered.OwnArmyValue, World.WorldTick + Info.ProtectInterval * 10);
				}

				allyDefendAnswer = answered;
			}

			// TC-3 (§12.28): the fold's second election pass — an ally's contested
			// expansion claim elects the nearest free army as its escort. Strictly
			// below a defend answer: a defend pick above already claimed `request`,
			// and the fold itself drained the rescue pool before electing assists.
			// Election-only, no fallback — the assist field exists only through the
			// coalition fold, so there is no pre-fold pick to preserve. Same thin-pool
			// floor; the answer holds while the requester's assist broadcast stays
			// live (CollectBroadcasts freshness + the next refold retracting it).
			CoalitionAssistAssignment allyAssistAssignment = null;
			TeamBroadcast allyAssistAnswer = null;
			if (threat == null && request == null && assistAnswersOn &&
				unitsHangingAroundTheBase.Count >= Info.TeamDefendAnswerMinPoolUnits)
			{
				var assistElection = Player.PlayerActor.TraitsImplementing<IBotCoalition>()
					.FirstEnabledTraitOrDefault()?.Coalition?.AssistAssignments;
				if (assistElection is { Count: > 0 })
				{
					var myId = Player.InternalName ?? "#" + Player.ClientIndex;
					var elected = assistElection.FirstOrDefault(a =>
						a.ResponderId == myId || (a.ResponderId == null && a.ResponderClientIndex == Player.ClientIndex));
					if (elected != null)
					{
						var broadcasts = TeamBlackboard.CollectBroadcasts(Player);
						var rallyCell = World.Map.CellContaining(elected.AssistPosition);
						if (!AnswerOnCooldown("assist_answer",
							elected.RequesterId ?? "#" + elected.RequesterClientIndex, rallyCell))
						{
							var requester = broadcasts.FirstOrDefault(b => b != null
								&& (CoalitionFold.ParticipantKey(b) == elected.RequesterId
									|| (elected.RequesterId == null && b.ClientIndex == elected.RequesterClientIndex)));
							var armyValue = requester?.OwnArmyValue
								?? broadcasts.Where(b => b != null).Select(b => b.OwnArmyValue).DefaultIfEmpty().Max();
							request = new BotProtectionRequest(rallyCell,
								armyValue, World.WorldTick + Info.ProtectInterval * 10);
							allyAssistAssignment = elected;
							allyAssistAnswer = requester;
						}
					}
				}
			}

			if (threat == null && request == null)
				return;

			CPos rally;
			if (request.HasValue)
			{
				// Escorts go TO the guarded point - no defensive-building snap:
				// the MCV/outpost is usually nowhere near a building.
				rally = request.Value.Location;
			}
			else
			{
				var target = threat.Value.Target;
				var searchSquared = Info.PrepositionDefenceSearchCells * Info.PrepositionDefenceSearchCells;
				rally = World.ActorsHavingTrait<AttackBase>()
					.Where(a => a.Owner == Player && !a.IsDead && a.Info.HasTraitInfo<BuildingInfo>()
						&& (a.Location - target).LengthSquared <= searchSquared)
					.OrderBy(a => (a.Location - target).LengthSquared)
					.Select(a => (CPos?)a.Location).FirstOrDefault() ?? target;
			}

			var protectSq = GetSquadOfType(SquadCAType.Protection) ?? RegisterNewSquad(bot, SquadCAType.Protection);
			var draftable = unitsHangingAroundTheBase.Where(u => !Info.ExcludeFromSquadsTypes.Contains(u.Actor.Info.Name)
				&& u.Actor.Info.HasTraitInfo<AttackBaseInfo>() && !u.Actor.Info.HasTraitInfo<BuildingInfo>()
				&& !u.Actor.Info.HasTraitInfo<HarvesterInfo>() && !u.Actor.Info.HasTraitInfo<AircraftInfo>()
				&& !IsNavalUnit(u.Actor)).ToList();

			// CA-2: forward defence keeps a reserve too — the rally outside the base
			// radius is the donor's non-emergency case; a rally inside it means the
			// threat is at the doorstep and gets the full pool.
			var emergency = (rally - initialBaseCenter).LengthSquared <=
				(long)Info.MaxBaseRadius * Info.MaxBaseRadius;
			var toDraft = DefendDraftLimit(draftable.Count, emergency, Info, utilityAxesProviders);
			for (var i = 0; i < toDraft; i++)
			{
				var u = draftable[i];
				protectSq.Units.Add(u);
				unitsHangingAroundTheBase.Remove(u);
			}

			if (!protectSq.IsValid)
				return;

			protectionRally = rally;

			// Threat path: hold for the attack's ETA plus grace. Request path: the
			// publisher refreshes its request every ProtectInterval, so the hold is a
			// rolling window - a retracted request lets the escort release within one
			// interval, and ExpiresTick is the failsafe bound for a dead publisher.
			protectionHoldUntilTick = request.HasValue
				? Math.Min(request.Value.ExpiresTick, World.WorldTick + Info.ProtectInterval * 10)
				: World.WorldTick + threat.Value.EtaTicks + Info.ProtectInterval * 10;
			bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(World, rally), false,
				groupedActors: protectSq.Units.Select(u => u.Actor).ToArray()));

			if (allyDefendAnswer != null)
				CommitAllyDefend(allyDefendAnswer, rally, protectSq.Units.Count);
			else
				CloseAllyDefend(BotMissionAttemptState.Released, BotMissionReasons.Superseded);

			if (allyAssistAssignment != null)
				CommitAllyAssist(allyAssistAssignment, allyAssistAnswer, rally, protectSq.Units.Count);
			else
				CloseAllyAssist(BotMissionAttemptState.Released, BotMissionReasons.Superseded);

			if (request == null && Info.FastSquadsReactToThreats)
				ReactWithFastSquads(bot, protectSq, rally, threat.Value.EtaTicks);
		}

		// The ally-answer protect squad is a defend action the mission-card grammar
		// can't see through providers — the answer writes a `defend_answer` record so
		// the team report can count it (without it this channel is invisible in
		// cameo-ai-missions.jsonl by construction). Written at the confirmed rally, not
		// the synthesis — a rally the squad can't take commits nothing. One open attempt
		// per requester+rally id: the rolling hold refresh extends it, a new requester
		// or a new rally cell supersedes it.
		void CommitAllyDefend(TeamBroadcast answered, CPos rally, int units)
		{
			var id = $"defend_answer:{CoalitionFold.ParticipantKey(answered)}:{rally}";
			if (allyDefendOpen == id)
				return;

			if (allyDefendOpen != null)
				CloseAllyDefend(BotMissionAttemptState.Released, BotMissionReasons.Superseded);

			var attempt = NextMissionAttempt(id);
			allyDefendOpen = id;
			BotMissionLog.Write(new BotMissionRecord
			{
				Player = Player,
				MissionId = id,
				Attempt = attempt,
				State = BotMissionAttemptState.Committed,
				Executor = "Squads",
				MissionType = "defend_answer",
				TargetCell = rally,
				Units = units,
				Value = answered.OwnArmyValue
			});
		}

		void CloseAllyDefend(BotMissionAttemptState state, string reason)
		{
			if (allyDefendOpen == null)
				return;

			BotMissionLog.Write(new BotMissionRecord
			{
				Player = Player,
				MissionId = allyDefendOpen,
				Attempt = CurrentMissionAttempt(allyDefendOpen),
				State = state,
				Reason = reason,
				Executor = "Squads",
				MissionType = "defend_answer"
			});
			if (state == BotMissionAttemptState.Released && reason == BotMissionReasons.Superseded
				&& Info.AllyAnswerCooldownTicks > 0)
			{
				var until = World.WorldTick + Info.AllyAnswerCooldownTicks;
				allyAnswerCooldownUntil[allyDefendOpen] = until;
				Player.PlayerActor.TraitOrDefault<BotMissionAttemptTracker>()?.CoolAnswer(allyDefendOpen, until);
			}
			allyDefendOpen = null;
		}

		// The elected assist answer is the same grammar gap as the defend answer: the
		// record is `assist_answer:<requesterKey>:<rallyCell>` so the team report can
		// count escorts separately from rescues. The requester broadcast can be null
		// (stale between the fold and this tick) — the assignment still carries the
		// requester's participant key, so the record never goes anonymous.
		void CommitAllyAssist(CoalitionAssistAssignment assignment, TeamBroadcast requester, CPos rally, int units)
		{
			var id = $"assist_answer:{assignment.RequesterId ?? "#" + assignment.RequesterClientIndex}:{rally}";
			if (allyAssistOpen == id)
				return;

			if (allyAssistOpen != null)
				CloseAllyAssist(BotMissionAttemptState.Released, BotMissionReasons.Superseded);

			var attempt = NextMissionAttempt(id);
			allyAssistOpen = id;
			BotMissionLog.Write(new BotMissionRecord
			{
				Player = Player,
				MissionId = id,
				Attempt = attempt,
				State = BotMissionAttemptState.Committed,
				Executor = "Squads",
				MissionType = "assist_answer",
				TargetCell = rally,
				Units = units,
				Value = requester?.OwnArmyValue ?? 0
			});
		}

		bool AnswerOnCooldown(string kind, string requesterKey, CPos rally)
		{
			if (Info.AllyAnswerCooldownTicks <= 0)
				return false;

			var id = $"{kind}:{requesterKey}:{rally}";
			if (allyAnswerCooldownUntil.TryGetValue(id, out var until) && World.WorldTick < until)
				return true;

			return Player.PlayerActor.TraitOrDefault<BotMissionAttemptTracker>()?.AnswerCooling(id, World.WorldTick) ?? false;
		}

		void CloseAllyAssist(BotMissionAttemptState state, string reason)
		{
			if (allyAssistOpen == null)
				return;

			BotMissionLog.Write(new BotMissionRecord
			{
				Player = Player,
				MissionId = allyAssistOpen,
				Attempt = CurrentMissionAttempt(allyAssistOpen),
				State = state,
				Reason = reason,
				Executor = "Squads",
				MissionType = "assist_answer"
			});
			if (state == BotMissionAttemptState.Released && reason == BotMissionReasons.Superseded
				&& Info.AllyAnswerCooldownTicks > 0)
			{
				var until = World.WorldTick + Info.AllyAnswerCooldownTicks;
				allyAnswerCooldownUntil[allyAssistOpen] = until;
				Player.PlayerActor.TraitOrDefault<BotMissionAttemptTracker>()?.CoolAnswer(allyAssistOpen, until);
			}
			allyAssistOpen = null;
		}

		// The cardless assault wave still needs a record for the shared-push metric:
		// one attempt per launch, superseded by the next wave, failed with the squad.
		void CommitSecurePush(Player target, int units)
		{
			CloseSecurePush(BotMissionAttemptState.Released, BotMissionReasons.Superseded);
			var id = $"secure:{target.InternalName}";
			var attempt = NextMissionAttempt(id);
			securePushOpen = id;
			securePushTarget = target;
			BotMissionLog.Write(new BotMissionRecord
			{
				Player = Player,
				MissionId = id,
				Attempt = attempt,
				State = BotMissionAttemptState.Committed,
				Executor = "Squads",
				MissionType = "secure",
				Units = units
			});
		}

		void CloseSecurePush(BotMissionAttemptState state, string reason)
		{
			if (securePushOpen == null)
				return;

			BotMissionLog.Write(new BotMissionRecord
			{
				Player = Player,
				MissionId = securePushOpen,
				Attempt = CurrentMissionAttempt(securePushOpen),
				State = state,
				Reason = reason,
				Executor = "Squads",
				MissionType = "secure"
			});
			securePushOpen = null;
			securePushTarget = null;
		}

		/// <summary>The most valuable live protection request, or null. Requests refresh
		/// every tick from their publishers; expired or retracted ones are skipped.</summary>
		public static BotProtectionRequest? SelectProtectionRequest(
			IEnumerable<BotProtectionRequest> requests, int now, int minValue)
		{
			return requests
				.Where(r => r.ExpiresTick > now && r.Value >= minValue)
				.OrderByDescending(r => r.Value).ThenBy(r => r.ExpiresTick)
				.Cast<BotProtectionRequest?>().FirstOrDefault();
		}

		BotProtectionRequest? SelectProtectionRequest()
		{
			if (!Info.UseProtectionRequests || protectionRequestProviders == null || protectionRequestProviders.Length == 0)
				return null;

			return SelectProtectionRequest(
				protectionRequestProviders.SelectMany(p => p.ProtectionRequests ?? []),
				World.WorldTick, Info.PrepositionMinThreatValue);
		}

		// A harasser joins the harass squad of its own type, or starts one.
		void AddToHarassSquad(IBot bot, UnitWposWrapper unit)
		{
			var squad = Squads.FirstOrDefault(s => s.Type == SquadCAType.Harass && s.Units.Any(u => u.Actor.Info.Name == unit.Actor.Info.Name))
				?? RegisterNewSquad(bot, SquadCAType.Harass);
			squad.Units.Add(unit);
		}

		/// <summary>
		/// DF release (maintainer 2026-09-28): after a successful defence every defender goes back to its job — raider
		/// types re-form guerrilla squads (within MaxGuerrillaSquads), spec-ops types their harass squads, the rest the
		/// idle pool, from which attack forces form and take the open missions. The one release path for protection squads.
		/// </summary>
		internal void ReleaseDefenders(IBot bot, SquadCA protectSq)
		{
			foreach (var u in protectSq.Units.ToList())
			{
				if (unitCannotBeOrdered(u.Actor))
					continue;

				var name = u.Actor.Info.Name;
				var guerrilla = Info.GuerrillaTypes.Contains(name) && Info.JoinGuerrilla > 0 ? OpenGuerrillaSquad(bot) : null;
				if (guerrilla != null)
					guerrilla.Units.Add(u);
				else if (Info.HarasserTypes.Contains(name))
					AddToHarassSquad(bot, u);
				else if (Info.FireSupportTypes.Contains(name) && OpenFireSupportSquad(bot) is { } releasedFs)
					releasedFs.Units.Add(u);
				else
					unitsHangingAroundTheBase.Add(u);
			}

			protectSq.Units.Clear();
			protectionRally = null;
			protectionHoldUntilTick = -1;
			protectionQuietSinceTick = -1;
			CloseAllyDefend(BotMissionAttemptState.Released, BotMissionReasons.Done);
			CloseAllyAssist(BotMissionAttemptState.Released, BotMissionReasons.Done);
			foreach (var n in notifyIdleBaseUnits)
				n.UpdatedIdleBaseUnits(unitsHangingAroundTheBase);
		}

		// Protection release trigger (maintainer 2026-09-28: "only disband defense squads if there is no more
		// perceived and predicted threat to the base"): the squad's own threat-free test reports quiet (no enemy
		// in range, no valid or visible target) plus no PERCEIVED threat (pressure at home, Pressured/Emergency)
		// and no PREDICTED attack on an own asset — all of it for ProtectionIdleDissolveTicks. This is the ONE
		// release trigger (§10.1); it calls ReleaseDefenders.
		internal bool ShouldReleaseDefenders(bool quiet)
		{
			// Live escort requests are a standing task: the escort must survive the
			// quiet-dissolve while a publisher still wants the guard (12.4a review).
			var threatened = (threatPredictionProviders != null && threatPredictionProviders.Any(p =>
				p.PerceivedBaseThreat || p.PredictedThreats.Count > 0))
				|| SelectProtectionRequest() != null;
			if (Info.ProtectionIdleDissolveTicks <= 0 || !quiet || threatened)
			{
				protectionQuietSinceTick = -1;
				return false;
			}

			if (protectionQuietSinceTick < 0)
				protectionQuietSinceTick = World.WorldTick;

			return World.WorldTick - protectionQuietSinceTick >= Info.ProtectionIdleDissolveTicks;
		}

		/// <summary>DF-3/4: can this squad be at `rally` before the enemy? Travel time at its slowest unit's speed.</summary>
		public static bool ArrivesInTime(double distanceCells, double slowestSpeedCellsPerTick, int etaTicks) =>
			slowestSpeedCellsPerTick > 0 && distanceCells / slowestSpeedCellsPerTick <= etaTicks;

		// DF-3 join the defence if in reach; DF-4 punish the enemy base if not.
		void ReactWithFastSquads(IBot bot, SquadCA protectSq, CPos rally, int etaTicks)
		{
			foreach (var sq in Squads.Where(s => (s.Type == SquadCAType.Guerrilla || s.Type == SquadCAType.Harass) && s.IsValid).ToList())
			{
				if (fastSquadReactedUntil.TryGetValue(sq, out var until) && World.WorldTick < until)
					continue;

				fastSquadReactedUntil[sq] = World.WorldTick + Math.Max(1, Info.FastSquadReactionCooldownTicks);
				var leader = sq.Units[0].Actor;
				var slowest = sq.Units.Min(u => (u.Actor.Info.TraitInfoOrDefault<MobileInfo>()?.Speed ?? 0) / 1024.0);
				var distance = (leader.Location - rally).Length;
				if (ArrivesInTime(distance, slowest, etaTicks))
				{
					// DF-3: join the defence for this attack; protection release returns them to the pool afterwards.
					protectSq.Units.AddRange(sq.Units);
					sq.Units.Clear();
					bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(World, rally), false,
						groupedActors: protectSq.Units.Select(u => u.Actor).ToArray()));
					continue;
				}

				// DF-4: too far to help — hit the enemy's base while its army is out.
				var target = FindFrozenEnemyTarget(leader.CenterPosition, SquadValueOf(sq), sq);
				if (target != null)
					sq.Target = Target.FromFrozenActor(target);
			}

			foreach (var gone in fastSquadReactedUntil.Keys.Where(s => !Squads.Contains(s)).ToList())
				fastSquadReactedUntil.Remove(gone);
		}

		Player EffectiveMainTarget()
		{
			var preferred = Info.PreferMainTarget && mainTargetProviders != null
				? mainTargetProviders
					.Select(p => p.MainTarget)
					.FirstOrDefault(target => target != null && target.WinState == WinState.Undefined)
				: null;

			// TC-3 (§12.18): the coalition's voted MainTarget trumps the provider pick —
			// the whole team folds onto one enemy. Only a non-null published target binds;
			// a missing provider or an Empty directive keeps today's result, bit-identical.
			if (Info.UseCoalitionTarget)
			{
				var coalitionTarget = Player.PlayerActor.TraitsImplementing<IBotCoalition>()
					.FirstEnabledTraitOrDefault()?.Coalition?.MainTarget;
				if (coalitionTarget != null)
					return coalitionTarget;
			}

			return preferred;
		}

		public static List<T> PreferOwned<T>(List<T> candidates, Func<T, bool> ownedByMainTarget)
		{
			if (ownedByMainTarget == null)
				return candidates;

			var preferred = candidates.Where(ownedByMainTarget).ToList();
			return preferred.Count > 0 ? preferred : candidates;
		}

		public static BotMission BestAffordableMission(IEnumerable<IBotMissionProvider> providers, int idleForceValue,
			Func<BotMission, bool> exclude = null)
		{
			if (providers == null)
				return null;

			foreach (var provider in providers)
				foreach (var mission in provider?.Missions ?? Array.Empty<BotMission>())
					if (mission != null && mission.RequiredValue <= idleForceValue && (exclude == null || !exclude(mission)))
						return mission;

			return null;
		}

		// TC-2f (§12.27): the affordability gate leaves Raid cards published but
		// never taken - their RequiredValue is sized for a dedicated force, the
		// launch bar is not. Steering re-picks among Raids alone under a relaxed
		// cap; deterministic: Priority desc, RequiredValue asc, publish order.
		// No exclude: the only filter in the launch path is Defend-hold
		// exhaustion, which can never match a Raid.
		public static BotMission BestRaidForSteering(IEnumerable<IBotMissionProvider> providers, int valueCap)
		{
			if (providers == null)
				return null;

			return providers
				.SelectMany(provider => provider?.Missions ?? Array.Empty<BotMission>())
				.Where(mission => mission != null && mission.Type == BotMissionType.Raid && mission.RequiredValue <= valueCap)
				.OrderByDescending(mission => mission.Priority)
				.ThenBy(mission => mission.RequiredValue)
				.FirstOrDefault();
		}

		// MissionCard lineage (fransotto's model): a MissionId identifies the
		// strategic reason; every take is a numbered attempt carried by the squad
		// for its lifetime, so "General -> commander -> actors -> result" resolves
		// as one grep-able chain in the debug log. Counters persist per match, so
		// a mission that dies and re-publishes continues the lineage (Attempt 2+).
		readonly Dictionary<string, int> missionAttemptCounters = new();
		readonly Dictionary<SquadCA, MissionAttempt> squadMissions = new();

		sealed class MissionAttempt
		{
			public BotMission Mission;
			public int Number;

			// The mission's own objective: the actor the squad was aimed at when the
			// attempt opened (MissionTaken runs after SelectMission set the target).
			// Null for a remembered (frozen) target — then only the squad's fate
			// decides, never whatever unit it happens to shoot next.
			public Actor CommittedTarget;
		}

		// The verdict on an open attempt from state the squad already holds. World-free so
		// it is testable: null = still running, otherwise the state and reason to book.
		public static (BotMissionAttemptState State, string Reason)? AttemptVerdict(
			bool targetGone, bool targetOursOrAllied, bool retargeted, bool squadEmpty, bool anyMemberDied)
		{
			if (squadEmpty && anyMemberDied)
				return (BotMissionAttemptState.Failed, BotMissionReasons.LostUnits);
			if (targetGone || targetOursOrAllied)
				return (BotMissionAttemptState.Success, BotMissionReasons.Done);
			if (squadEmpty)
				return (BotMissionAttemptState.Released, BotMissionReasons.Reserved);
			if (retargeted)
				return (BotMissionAttemptState.Released, BotMissionReasons.Superseded);
			return null;
		}

		void CheckAttemptVerdict(SquadCA squad)
		{
			if (!squadMissions.TryGetValue(squad, out var attempt))
				return;

			// Only the objective's fate decides. A squad switching to the enemy in front
			// of it is not a new mission (attack squads retarget constantly), so the
			// retarget clause stays false here; DismissSquad books the real supersede.
			var committed = attempt.CommittedTarget;
			if (committed == null)
				return;

			var gone = committed.IsDead;
			var oursOrAllied = !gone && committed.Owner != null && committed.Owner.RelationshipWith(Player) != PlayerRelationship.Enemy;
			var verdict = AttemptVerdict(gone, oursOrAllied, false, !squad.IsValid, false);
			if (verdict != null)
				ResolveMissionAttempt(squad, verdict.Value.State, verdict.Value.Reason);
		}

		// LC1 (AI_ARCHITECTURE 10.1): squad membership is a lease. The pool stays
		// unclaimed so engineers/scouts/collectors can borrow it; squad members are
		// claimed with a heartbeat so nothing else can take them mid-job, and a
		// member another module holds is handed off, never fought over. Null
		// service = no contract, which keeps classic byte-identical.
		const string LeaseOwner = nameof(SquadManagerBotModuleCA);
		readonly HashSet<Actor> claimedBySquads = new();

		int LeaseHeartbeatTicks() => Math.Max(200, Info.AttackForceInterval * 4);

		void ReconcileSquadLeases()
		{
			var leases = BotUnitLeases.Of(Player);
			if (leases == null)
			{
				claimedBySquads.Clear();
				return;
			}

			// The pool is unowned: drop entries another module claimed since they
			// entered, before any draft site can pull them this pass. They leave
			// activeUnits too, so FindNewUnits re-adopts them once released.
			unitsHangingAroundTheBase.RemoveAll(u =>
			{
				if (u.Actor == null || !BotUnitLeases.IsClaimedByOther(leases, u.Actor, LeaseOwner))
					return false;

				activeUnits.Remove(u.Actor);
				return true;
			});

			var held = new HashSet<Actor>();
			foreach (var squad in Squads)
			{
				if (!squad.IsValid)
					continue;

				var handedOff = false;
				foreach (var u in squad.Units.ToList())
				{
					var a = u.Actor;
					if (a == null)
						continue;

					if (BotUnitLeases.TryClaim(leases, a, LeaseOwner, BotLeasePurpose.Squad, LeaseHeartbeatTicks()))
						held.Add(a);
					else
					{
						// Another owner holds it — hand the unit off cleanly: out of the
						// squad and out of activeUnits, so FindNewUnits re-adopts it once
						// the other module releases.
						squad.Units.Remove(u);
						activeUnits.Remove(a);
						handedOff = true;
					}
				}

				// A hand-off is not a loss: a squad emptied by it is released as reserved,
				// so CleanSquads never books it as lost_units.
				if (handedOff && !squad.IsValid)
				{
					var verdict = AttemptVerdict(false, false, false, true, false);
					ResolveMissionAttempt(squad, verdict.Value.State, verdict.Value.Reason);
				}
			}

			claimedBySquads.RemoveWhere(a =>
			{
				if (held.Contains(a))
					return false;

				leases.Release(a, LeaseOwner);
				return true;
			});
			claimedBySquads.UnionWith(held);
		}

		void MissionTaken(BotMission mission, SquadCA taker)
		{
			foreach (var provider in missionProviders ?? Array.Empty<IBotMissionProvider>())
				if ((provider.Missions ?? Array.Empty<BotMission>()).Any(candidate => ReferenceEquals(candidate, mission)))
				{
					provider.MissionTaken(mission);
					var id = mission.EffectiveMissionId;
					var attempt = NextMissionAttempt(id);
					squadMissions[taker] = new MissionAttempt
					{
						Mission = mission,
						Number = attempt,
						CommittedTarget = taker.Target.Type == TargetType.Actor ? taker.Target.Actor : null
					};
					ReportMissionAttempt(mission, attempt, BotMissionAttemptState.Committed, null);
					return;
				}
		}

		void ReportMissionAttempt(BotMission mission, int attempt, BotMissionAttemptState state, string reason)
		{
			BotMissionLog.Write(new BotMissionRecord
			{
				Player = Player,
				MissionId = mission.EffectiveMissionId,
				Attempt = attempt,
				State = state,
				Reason = reason,
				Executor = "Squads",
				MissionType = mission.Type.ToString().ToLowerInvariant(),
				RegionIndex = mission.RegionIndex,
				Tick = World.WorldTick
			});
			foreach (var sink in missionOutcomeSinks ?? Array.Empty<IBotMissionOutcomeSink>())
				sink.Report(mission.EffectiveMissionId, attempt, state, reason, World.WorldTick);
		}

		void ResolveMissionAttempt(SquadCA squad, BotMissionAttemptState state, string reason)
		{
			if (squadMissions.TryGetValue(squad, out var attempt) && squadMissions.Remove(squad))
				ReportMissionAttempt(attempt.Mission, attempt.Number, state, reason);
		}

		void CleanSquads()
		{
			foreach (var s in Squads.Where(s => !s.IsValid))
			{
				ResolveMissionAttempt(s, BotMissionAttemptState.Failed, BotMissionReasons.LostUnits);
				if (s.Type == SquadCAType.Protection)
				{
					CloseAllyDefend(BotMissionAttemptState.Failed, BotMissionReasons.LostUnits);
					CloseAllyAssist(BotMissionAttemptState.Failed, BotMissionReasons.LostUnits);
				}
				else if (s.Type == SquadCAType.Rush)
					CloseSecurePush(BotMissionAttemptState.Failed, BotMissionReasons.LostUnits);
			}
			Squads.RemoveAll(s => !s.IsValid);
			foreach (var s in Squads)
			{
				s.Units.RemoveAll(u => unitCannotBeOrdered(u.Actor));

				if (IsAirFamily(s.Type))
				{
					s.NewUnits.RemoveWhere(unitCannotBeOrdered);
					s.RearmingUnits.RemoveWhere(unitCannotBeOrdered);
					s.WaitingUnits.RemoveWhere(unitCannotBeOrdered);
				}
			}
		}

		// HACK: Use of this function requires that there is one squad of this type.
		SquadCA GetSquadOfType(SquadCAType type)
		{
			return Squads.FirstOrDefault(s => s.Type == type);
		}

		IEnumerable<SquadCA> GetSquadsOfType(SquadCAType type)
		{
			return Squads.Where(s => s.Type == type);
		}

		SquadCA RegisterNewSquad(IBot bot, SquadCAType type, Actor target = null)
		{
			var ret = new SquadCA(bot, this, type, target);
			ret.PriorityTags = PriorityTagsFor(type);
			Squads.Add(ret);
			if (type is SquadCAType.Rush or SquadCAType.Harass or SquadCAType.Guerrilla
				or SquadCAType.Air or SquadCAType.Naval or SquadCAType.Fighter
				or SquadCAType.Gunship or SquadCAType.Bomber or SquadCAType.Stealth)
				OffensiveSquadsLaunched++;
			return ret;
		}

		public void DismissSquad(SquadCA squad)
		{
			var leases = BotUnitLeases.Of(Player);
			if (leases != null)
				foreach (var u in squad.Units)
					if (u.Actor != null && claimedBySquads.Remove(u.Actor))
						leases.Release(u.Actor, LeaseOwner);

			ResolveMissionAttempt(squad, BotMissionAttemptState.Released, BotMissionReasons.Superseded);

			// An intact stand-down is not a wipe: close the squad's open telemetry here or
			// CleanSquads sees the empty Units list and books it Failed/LostUnits.
			if (squad.Type == SquadCAType.Protection)
			{
				CloseAllyDefend(BotMissionAttemptState.Released, BotMissionReasons.Superseded);
				CloseAllyAssist(BotMissionAttemptState.Released, BotMissionReasons.Superseded);
			}
			else if (squad.Type == SquadCAType.Rush)
				CloseSecurePush(BotMissionAttemptState.Released, BotMissionReasons.Superseded);

			unitsHangingAroundTheBase.AddRange(squad.Units);

			squad.Units.Clear();
		}

		// Squads kick stuck/blocked units out of their Units list; without a route
		// back those actors stay in activeUnits but in no squad and no pool — the
		// manager never touches them again. Return them to the idle pool so
		// FindNewUnits can reclassify them.
		internal void ReturnToIdlePool(Actor actor)
		{
			if (actor == null || unitCannotBeOrdered(actor))
				return;

			unitsHangingAroundTheBase.Add(new UnitWposWrapper(actor));
		}

		int UnitValue(Actor actor)
		{
			if (!cachedUnitValues.TryGetValue(actor.Info.Name, out var cost))
			{
				cost = actor.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
				cachedUnitValues[actor.Info.Name] = cost;
			}

			return cost;
		}

		void TrackRoleLosses()
		{
			var maxRadiusSquared = Info.MaxBaseRadius * Info.MaxBaseRadius;
			foreach (var (actor, known) in lastKnownRoles)
			{
				if (!actor.IsDead)
					continue;

				lossesByRole[known.Role] = lossesByRole.GetValueOrDefault(known.Role) + known.Cost;
				if ((known.Location - initialBaseCenter).LengthSquared > maxRadiusSquared)
					awayLossesByRole[known.Role] = awayLossesByRole.GetValueOrDefault(known.Role) + known.Cost;
			}

			lastKnownRoles.Clear();
			foreach (var squad in Squads)
			{
				var role = squad.Type.ToString().ToLowerInvariant();
				foreach (var unit in squad.Units)
					if (unit.Actor != null && !unit.Actor.IsDead && unit.Actor.IsInWorld)
						lastKnownRoles[unit.Actor] = (role, UnitValue(unit.Actor), unit.Actor.Location);
			}

			foreach (var unit in unitsHangingAroundTheBase)
				if (unit.Actor != null && !unit.Actor.IsDead && unit.Actor.IsInWorld)
					lastKnownRoles.TryAdd(unit.Actor, ("idle", UnitValue(unit.Actor), unit.Actor.Location));
		}

		void AssignRolesToIdleUnits(IBot bot)
		{
			// Telemetry only: a snapshot every role pass is fresh enough for a death's position.
			if (World.WorldTick % Math.Max(1, Info.AssignRolesInterval) == 0)
				TrackRoleLosses();

			CleanSquads();
			ReconcileSquadLeases();

			activeUnits.RemoveAll(unitCannotBeOrdered);
			unitsHangingAroundTheBase.RemoveAll(u => unitCannotBeOrdered(u.Actor));
			foreach (var n in notifyIdleBaseUnits)
				n.UpdatedIdleBaseUnits(unitsHangingAroundTheBase);

			if (--attackForceTicks <= 0)
			{
				attackForceTicks = Info.AttackForceInterval;
				foreach (var s in Squads)
					s.Units.RemoveAll(u => unitCannotBeOrdered(u.Actor));

				// H1: squads consult the attention budget before acting. The cursor
				// rotates the pass order so a spent budget staggers squads instead of
				// starving the tail of the list.
				if (Squads.Count > 0)
				{
					var start = squadCursor % Squads.Count;
					for (var i = 0; i < Squads.Count; i++)
					{
						var index = (start + i) % Squads.Count;
						var s = Squads[index];

						// The Units pruning above can empty a squad after CleanSquads ran —
						// a corpse must not burn an attention slot on a no-op Update.
						if (!s.IsValid)
							continue;
						if (actionBudget != null && !actionBudget.TryConsumeAttention(s))
							continue;

						CheckAttemptVerdict(s);
						s.Update();
						squadCursor = index + 1;
					}
				}
			}

			if (--assignRolesTicks <= 0)
			{
				assignRolesTicks = Info.AssignRolesInterval;
				unitsHangingAroundTheBase.RemoveAll(u => unitCannotBeOrdered(u.Actor));
				activeUnits.RemoveAll(unitCannotBeOrdered);
				FindNewUnits(bot);
			}

			if (--minAttackForceDelayTicks <= 0)
			{
				// §12.14 PL-1 lead lean composed with the UT-1 TurtleRush axis scale —
				// two independent multipliers on the same reset; each is neutral (x1.0)
				// while its own flag is off or its provider absent.
				minAttackForceDelayTicks = BotPersonalityLeads.Scaled(
					MinAttackDelayResetTicks(Info, utilityAxesProviders),
					BotPersonalityLeads.Lean(leadProviders, "rush"));
				unitsHangingAroundTheBase.RemoveAll(u => unitCannotBeOrdered(u.Actor));
				CreateAttackForce(bot);
			}

			if (--protectOwnTicks <= 0 && protectOwnFrom != null)
				ProtectOwn(protectOwnFrom);

			PrepositionDefenceTick(bot);
		}

		public void SetAirStrikeTarget(Actor target)
		{
			airStrikeTarget = target;
		}

		public Actor PopAirStrikeTarget()
		{
			var target = airStrikeTarget;
			airStrikeTarget = null;
			return target;
		}

		// The smallest guerrilla squad with room, or a new one while fewer than MaxGuerrillaSquads exist; null when all are full.
		SquadCA OpenGuerrillaSquad(IBot bot)
		{
			var guerrillas = Squads.Where(s => s.Type == SquadCAType.Guerrilla).ToList();
			var open = guerrillas.Where(s => s.Units.Count < Info.MaxGuerrillaSize).MinByOrDefault(s => s.Units.Count);
			if (open != null)
				return open;

			return guerrillas.Count < GuerrillaSquadCap(Info, World.WorldTick, utilityAxesProviders) ? RegisterNewSquad(bot, SquadCAType.Guerrilla) : null;
		}

		// 12.4a: one fire-support squad is enough - the role's members plus their tank
		// escorts trail the artillery squad and fight whatever threatens it.
		SquadCA OpenFireSupportSquad(IBot bot)
		{
			var open = Squads.FirstOrDefault(s => s.Type == SquadCAType.FireSupport && s.IsValid);
			return open ?? RegisterNewSquad(bot, SquadCAType.FireSupport);
		}

		/// <summary>The guerrilla squad cap at `tick`: MaxGuerrillaSquads, ramping linearly to MaxGuerrillaSquadsLate.</summary>
		public static int GuerrillaSquadCap(SquadManagerBotModuleCAInfo info, int tick)
		{
			var early = Math.Max(1, info.MaxGuerrillaSquads);
			if (info.MaxGuerrillaSquadsLate <= early || info.GuerrillaSquadRampTicks <= 0)
				return early;

			var t = Math.Min(1.0, (double)tick / info.GuerrillaSquadRampTicks);
			return early + (int)Math.Round((info.MaxGuerrillaSquadsLate - early) * t);
		}

		// UT-2: the time-ramped cap above scales by the Steamroller<->Guerrilla utility axis —
		// 100 (Guerrilla) x1.5, 50 x1.0, 0 (Steamroller) x0.5 — same lean shape as the attack
		// delay. UseUtilityAxes off or no provider: the yaml ramp unchanged.
		public static int GuerrillaSquadCap(SquadManagerBotModuleCAInfo info, int tick, IBotUtilityAxes[] providers)
		{
			var cap = GuerrillaSquadCap(info, tick);
			if (!info.UseUtilityAxes)
				return cap;

			var axis = providers?.FirstEnabledTraitOrDefault()?.UtilitySteamrollerGuerrilla ?? IBotUtilityAxes.Neutral;
			return (int)Math.Round(cap * (50 + axis) / 100.0);
		}

		// UT-1 (AI_DEEP_RESEARCH.md §5.1): the MinimumAttackForceDelay reset in percent of the
		// yaml value, piecewise-linear on the TurtleRush axis — 100 (Rush) -> 60, 50 -> 100,
		// 0 (Turtle) -> 150. Axis input is clamped to [0,100].
		public static int UtilityAttackDelayPercent(int turtleRushAxis)
		{
			var axis = Math.Clamp(turtleRushAxis, 0, 100);
			return axis >= 50 ? 100 - (axis - 50) * 40 / 50 : 150 - axis;
		}

		/// <summary>The MinimumAttackForceDelay reset: the plain yaml value unless UseUtilityAxes
		/// is on, in which case it scales by the first enabled provider's TurtleRush axis.</summary>
		public static int MinAttackDelayResetTicks(SquadManagerBotModuleCAInfo info, IBotUtilityAxes[] providers)
		{
			if (!info.UseUtilityAxes)
				return info.MinimumAttackForceDelay;

			var axis = providers?.FirstEnabledTraitOrDefault()?.UtilityTurtleRush ?? IBotUtilityAxes.Neutral;
			return info.MinimumAttackForceDelay * UtilityAttackDelayPercent(axis) / 100;
		}

		/// <summary>PL-2 (§12.14): while the guerrilla lead trails, the join chance rises toward 100,
		/// linear in the deficit (lean is (0,1] — the lead's multiplier). A configured 0 stays 0:
		/// personalities that never form guerrilla squads are not revived by the lean.</summary>
		public static int EffectiveJoinGuerrilla(int basePct, double lean) =>
			basePct <= 0 ? 0 : basePct + (int)Math.Round((1 - Math.Clamp(lean, 0.0, 1.0)) * (100 - basePct));

		// CP (AI_DEEP_RESEARCH.md §2.3): the square-law ratio of this squad against the enemies it can see that can fight.
		internal double PredictedRatio(SquadCA squad, IEnumerable<Actor> enemies)
		{
			var enemyList = enemies as IReadOnlyList<Actor> ?? enemies.ToList();
			CanaryObservedAll(enemyList, "predicted-ratio");

			var rules = World.Map.Rules;
			var own = squad.Units.Where(u => !unitCannotBeOrdered(u.Actor)).GroupBy(u => u.Actor.Info)
				.Select(g => (BotUnitProfiles.Get(rules, g.Key), g.Count())).ToList();
			var foes = enemyList.Where(e => e.Info.HasTraitInfo<AttackBaseInfo>()).GroupBy(e => e.Info)
				.Select(g => (BotUnitProfiles.Get(rules, g.Key), g.Count())).ToList();
			return BotCombatPredictor.Predict(own, foes).Ratio;
		}

		int RetreatRatioPct => botLimits?.Info.RetreatRatioPct ?? Info.DefaultRetreatRatioPct;

		internal bool PredictsLoss(SquadCA squad, IEnumerable<Actor> enemies) =>
			PredictedRatio(squad, enemies) * 100 < RetreatRatioPct;

		internal bool PredictsWin(SquadCA squad, IEnumerable<Actor> enemies) =>
			PredictedRatio(squad, enemies) * 100 >= (double)RetreatRatioPct * Info.EngageMarginPct / 100;

		// CN3: remembered DetectCloaked coverage, aggregated across the enabled
		// stealth-doctrine providers. Empty when `cn3_stealth_squads` arms no
		// provider or nothing was observed - "none seen", never "none exist".
		internal IEnumerable<BotKnownDetector> RememberedDetectors()
		{
			if (stealthDoctrines == null)
				yield break;

			foreach (var doctrine in stealthDoctrines)
				if (doctrine.IsTraitEnabled())
					foreach (var detector in doctrine.RememberedDetectors())
						yield return detector;
		}

		// CN3: dedicated stealth squads draft armed cloak-capable ground units -
		// an unarmed infiltrator kills nothing, naval and air units never reach
		// this branch anyway (they are claimed above), and a cloak that is not
		// enabled by default may never come online.
		public static bool IsStealthDraftable(bool hasCloakTrait, bool hasAttackTrait, bool isNaval, bool isAir)
			=> hasCloakTrait && hasAttackTrait && !isNaval && !isAir;

		void FindNewUnits(IBot bot)
		{
			var leases = BotUnitLeases.Of(Player);
			var newUnits = World.ActorsHavingTrait<IPositionable>()
				.Where(a => a.Owner == Player &&
					!Info.ExcludeFromSquadsTypes.Contains(a.Info.Name) &&
					!activeUnits.Contains(a) && a.IsInWorld &&
					!BotUnitLeases.IsClaimedByOther(leases, a, LeaseOwner));

			// JoinGuerrilla gates creation too: 0 means this personality never forms
			// guerrilla squads, not "the first unit always joins". The size cap is
			// evaluated per actor — a single pass may add a whole production wave.
			// PL-2 (§12.14): a guerrilla personality trailing its map-control lead fills
			// raider squads faster — raiders crossing the map ARE incidental scouts, they
			// feed the same regions_fresh the lead measures. lean >= 1 keeps the roll exact.
			var joinGuerrilla = EffectiveJoinGuerrilla(Info.JoinGuerrilla,
				BotPersonalityLeads.Lean(leadProviders, "guerrilla"));
			var guerrillaRoll = joinGuerrilla > 0 && World.LocalRandom.Next(100) < joinGuerrilla;

			foreach (var a in newUnits)
			{
				// 12.4a naval guard FIRST: an armed `naval` locomotor ships off to a Naval
				// squad before any other branch - a ship missing from NavalUnitsTypes
				// can never land in a guerrilla/ground squad or the idle pool. Unarmed
				// ships (wc2 oil tankers, transports) are not squad material: they fall
				// through to the armed-only idle gate below and stay unmanaged.
				if (IsNavalUnit(a) && a.Info.HasTraitInfo<AttackBaseInfo>())
				{
					var navalSquads = Squads.Where(s => s.Type == SquadCAType.Naval);
					var matchingNavalSquadFound = false;

					foreach (var navalSquad in navalSquads)
					{
						if (navalSquad.Units.Any(u => u.Actor.Info.Name == a.Info.Name))
						{
							navalSquad.Units.Add(new UnitWposWrapper(a));
							matchingNavalSquadFound = true;
							break;
						}
					}

					if (!matchingNavalSquadFound)
					{
						var newNavalSquad = RegisterNewSquad(bot, SquadCAType.Naval);
						newNavalSquad.Units.Add(new UnitWposWrapper(a));
					}
				}
				else if (IsAirUnit(a))
				{
					// CA-5 (12.8): with the doctrine split on, fighter/gunship/bomber
					// members form role squads; unroled air keeps generic Air squads.
					// Bomber teams are capped (a full team becomes its own strike team);
					// role squads merge across actor types - the doctrine is the
					// formation, not the chassis - but a same-name squad is preferred.
					// Ordering rule: a WRITTEN GuerrillaTypes listing outranks a
					// derived air role, but only when the doctrine is on - flag off
					// keeps master's air-first order so @classic is unmoved.
					if (GuerrillaOutranksAir(Info.AirDoctrineEnabled, a.Info.Name, Info.GuerrillaTypes)
						&& guerrillaRoll && OpenGuerrillaSquad(bot) is { } airGuerrilla)
					{
						airGuerrilla.Units.Add(new UnitWposWrapper(a));
						AIUtils.BotDebug("AI ({0}): Added {1} to squad {2}", Player.ClientIndex, a, airGuerrilla.Type);
					}
					else
					{
						var squadType = AirSquadTypeFor(a.Info.Name);
						var openSquads = Squads.Where(s => s.Type == squadType &&
							(squadType != SquadCAType.Bomber || s.Units.Count < Info.BomberSquadMaxSize)).ToList();

						var airSquad = openSquads.FirstOrDefault(s => s.Units.Any(u => u.Actor.Info.Name == a.Info.Name));
						if (airSquad == null && squadType != SquadCAType.Air)
							airSquad = openSquads.MinByOrDefault(s => s.Units.Count);

						if (airSquad != null)
						{
							airSquad.Units.Add(new UnitWposWrapper(a));
							airSquad.NewUnits.Add(a);
						}
						else
						{
							var newAirSquad = RegisterNewSquad(bot, squadType);
							newAirSquad.Units.Add(new UnitWposWrapper(a));
							newAirSquad.NewUnits.Add(a);
						}
					}
				}
				else if (stealthDoctrines?.FirstEnabledTraitOrDefault() != null
					&& IsStealthDraftable(a.Info.TraitInfos<CloakInfo>().Any(c => c.EnabledByDefault),
						a.Info.HasTraitInfo<AttackBaseInfo>(), IsNavalUnit(a), IsAirUnit(a)))
				{
					// CN3: cloak-capable armed ground forms a stealth squad - out of
					// guerrilla, so a stealth tank never raids half-decloaked. Same-type
					// squads are preferred (one chassis per ambush), then the smallest
					// squad with room.
					var stealthSquads = Squads.Where(s => s.Type == SquadCAType.Stealth && s.Units.Count < Info.StealthSquadMaxSize).ToList();
					var stealthSquad = stealthSquads.FirstOrDefault(s => s.Units.Any(u => u.Actor.Info.Name == a.Info.Name))
						?? stealthSquads.MinByOrDefault(s => s.Units.Count)
						?? RegisterNewSquad(bot, SquadCAType.Stealth);
					stealthSquad.Units.Add(new UnitWposWrapper(a));
					AIUtils.BotDebug("AI ({0}): Added {1} to squad {2}", Player.ClientIndex, a, stealthSquad.Type);
				}
				else if (Info.FireSupportTypes.Contains(a.Info.Name) && OpenFireSupportSquad(bot) is { } fsSquad)
				{
					// 12.4a: fire-support units form their own squads and never raid.
					fsSquad.Units.Add(new UnitWposWrapper(a));
					AIUtils.BotDebug("AI ({0}): Added {1} to squad {2}", Player.ClientIndex, a, fsSquad.Type);
				}
				else if (Info.GuerrillaTypes.Contains(a.Info.Name) && guerrillaRoll && OpenGuerrillaSquad(bot) is { } guerrillaForce)
				{
					guerrillaForce.Units.Add(new UnitWposWrapper(a));
					AIUtils.BotDebug("AI ({0}): Added {1} to squad {2}", Player.ClientIndex, a, guerrillaForce.Type);
				}
				else if (Info.HarasserTypes.Contains(a.Info.Name))
					AddToHarassSquad(bot, new UnitWposWrapper(a));
				else if (Info.SupportUnitTypes.Contains(a.Info.Name))
				{
					var supportSquad = Squads.FirstOrDefault(s => s.Type == SquadCAType.Support);
					if (supportSquad == null)
					{
						supportSquad = RegisterNewSquad(bot, SquadCAType.Support);
						AIUtils.BotDebug("AI ({0}): Created support squad {1}", Player.ClientIndex, supportSquad.Type);
					}

					supportSquad.Units.Add(new UnitWposWrapper(a));
				}
				else if (a.Info.HasTraitInfo<AttackBaseInfo>())
					unitsHangingAroundTheBase.Add(new UnitWposWrapper(a));

				activeUnits.Add(a);
			}

			// Notifying here rather than inside the loop, should be fine and saves a bunch of notification calls
			foreach (var n in notifyIdleBaseUnits)
				n.UpdatedIdleBaseUnits(unitsHangingAroundTheBase);
		}

		void CreateAttackForce(IBot bot)
		{
			// Create an attack force when we have enough units around our base.
			// (don't bother leaving any behind for defense)
			var idleUnitsValue = 0;

			if (Info.SquadValue > 0)
			{
				foreach (var a in unitsHangingAroundTheBase)
				{
					if (!cachedUnitValues.TryGetValue(a.Actor.Info.Name, out var unitCost))
					{
						unitCost = a.Actor.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
						cachedUnitValues[a.Actor.Info.Name] = unitCost;
					}

					idleUnitsValue += unitCost;
				}
			}

			// DI-2 (12.16): the Director re-targets the launch bar every dispatch check —
			// Climax releases on a smaller pool, Relief holds for a rebuild. Scaling the
			// bar itself (not the stored desired force) lets a phase change mid-wait
			// take effect immediately; flag-off or no provider = scale 100, identical.
			var forceScale = 100;
			if (Info.UseDirectorPacing)
			{
				var director = Player.PlayerActor.TraitsImplementing<IBotDirector>().FirstOrDefault();
				if (director != null)
					forceScale = DirectorForceScalePercent(director.DirectorPhase, Info);
			}

			// TC-2 (12.17): an allied Director's Climax opens our launch window too —
			// team waves surge together. The min keeps a slacker own phase from
			// skipping a fleeting ally climax; a shredded pool can't launch anyway.
			if (Info.UseTeamSyncAttacks && TeamBlackboard.Collect(Player).AnyClimax)
				forceScale = TeamSyncForceScale(forceScale, true, Info.DirectorClimaxForceScalePercent);

			// Scale targets (DESIGN 19.10): an enabled provider's army value target replaces SquadValue and its fixed time
			// ramp (growth lives in the provider), and MaxIdleUnits scales by the same factor. The Director / team force
			// scale and ValueOnlyAttackLaunch apply on top, exactly as before. No provider: the yaml numbers.
			var desiredValue = desiredAttackForceValue;
			var maxIdleUnits = Info.MaxIdleUnits;
			if (Info.SquadValue > 0 && scaleTargetProviders.TryArmyValue(Info.SquadValue, out var armyTarget))
			{
				desiredValue = armyTarget;
				maxIdleUnits = Math.Max(1, (int)((long)Info.MaxIdleUnits * armyTarget / Info.SquadValue));
			}

			var requiredValue = ApplyForceScale(desiredValue, forceScale);
			var requiredSize = ApplyForceScale(desiredAttackForceSize, forceScale);

			// CA F2p2 (A5-2): ValueOnlyAttackLaunch drops the unit-count gate when a squad value threshold is configured; MaxIdleUnits still applies.
			var countGateMet = (Info.ValueOnlyAttackLaunch && Info.SquadValue > 0) || unitsHangingAroundTheBase.Count >= requiredSize;
			if (unitsHangingAroundTheBase.Count >= maxIdleUnits || (idleUnitsValue >= requiredValue && countGateMet))
			{
				// 12.5: squads form to the same mix production builds - an assault
				// missing a required role stages until the pool covers it, bounded
				// by StageCompositionTicks, instead of trickling out under-strength.
				if (!StagedCompositionReady())
				{
					if (stageSinceTick < 0)
						stageSinceTick = World.WorldTick;
					else if (World.WorldTick - stageSinceTick < Info.StageCompositionTicks)
						return;
				}

				stageSinceTick = -1;
				BotMission mission = null;
				Actor missionTarget = null;
				FrozenActor missionFrozenTarget = null;
				if (Info.UseMissions && missionProviders?.Length > 0)
				{
					// A Defend whose hold window already lapsed this cycle is excluded at
					// selection time so it can't shadow a Raid sitting behind it in the
					// published order (Defend has RequiredValue 0 and would always win).
					mission = SelectMission();
					while (mission?.Type == BotMissionType.Defend)
					{
						if (heldDefendMission == null)
						{
							heldDefendMission = mission;
							defendMissionHeldSince = World.WorldTick;
						}
						else
						{
							// A different region re-published as Defend must not inherit the
							// previous region's elapsed hold (it could exhaust instantly).
							if (heldDefendMission.RegionIndex != mission.RegionIndex)
								defendMissionHeldSince = World.WorldTick;
							heldDefendMission = mission;
						}

						var heldTicks = World.WorldTick - defendMissionHeldSince;
						if (heldTicks <= Math.Max(0, Info.MissionDefendHoldTicks))
						{
							AIUtils.BotDebug("AI ({0}): holding {1} idle units for Defend mission in region {2} ({3}/{4} ticks)",
								Player.ClientIndex, unitsHangingAroundTheBase.Count, mission.RegionIndex, heldTicks, Info.MissionDefendHoldTicks);
							return;
						}

						AIUtils.BotDebug("AI ({0}): releasing Defend mission in region {1} after {2} ticks",
							Player.ClientIndex, mission.RegionIndex, heldTicks);
						defendMissionExhaustedRegions.Add(mission.RegionIndex);
						heldDefendMission = null;
						defendMissionHeldSince = -1;
						mission = SelectMission();
					}

					// TC-2f (§12.27): nothing affordable won — a Raid card may still
					// ride this wave at the overcommit cap. It lands above the
					// Defend-clear below on purpose: a steered Raid IS a non-Defend
					// commit, so it releases the hold machinery like any won card.
					mission ??= SelectRaidForSteering();

					// Null is "no mission published this tick", not "a non-Defend won" —
					// clearing here would re-arm an exhausted region between publishes.
					if (mission != null && mission.Type != BotMissionType.Defend)
					{
						heldDefendMission = null;
						defendMissionHeldSince = -1;
						defendMissionExhaustedRegions.Clear();
					}

					if (mission?.Type == BotMissionType.Raid)
					{
						missionTarget = FindClosestEnemy(mission.Location, idleUnitsValue, mission.TargetPlayer);
						if (missionTarget == null && FoggedScans)
							missionFrozenTarget = FindFrozenEnemyTarget(
								World.Map.CenterOfCell(mission.Location), idleUnitsValue, null, mission.TargetPlayer);
					}
				}

				BotMission SelectMission()
				{
					return BestAffordableMission(missionProviders, idleUnitsValue,
						m => m.Type == BotMissionType.Defend
							&& defendMissionExhaustedRegions.Contains(m.RegionIndex));
				}

				// TC-2f (§12.27): the cap is the larger of the overcommit ratio and
				// the flat floor; long math, a deep pool x the percent passes int.
				BotMission SelectRaidForSteering()
				{
					if (!Info.UseRaidMissionSteering)
						return null;

					var cap = (int)Math.Min(int.MaxValue, Math.Max(
						(long)idleUnitsValue * Info.RaidMissionSteerOvercommitPercent / 100,
						(long)Info.RaidMissionSteerMinValue));
					return BestRaidForSteering(missionProviders, cap);
				}

				var attackForce = RegisterNewSquad(bot, SquadCAType.Rush);

				// 6f: long-range units peel off into an artillery squad that trails
				// the assault and bombards its target, instead of charging with it.
				// 12.4a: fire-support members never raid either - they route to the
				// screen squad (release/load paths can leave them in the pool).
				var artilleryUnits = unitsHangingAroundTheBase.Where(u => IsArtilleryUnit(u.Actor)).ToList();
				var fireSupportUnits = unitsHangingAroundTheBase.Where(u => !IsArtilleryUnit(u.Actor)
					&& Info.FireSupportTypes.Contains(u.Actor.Info.Name)).ToList();
				attackForce.Units.AddRange(unitsHangingAroundTheBase.Where(u => !IsArtilleryUnit(u.Actor)
					&& !Info.FireSupportTypes.Contains(u.Actor.Info.Name)
					&& u.Actor.Info.HasTraitInfo<AttackBaseInfo>()));
				if (Info.EnsureAntiAirEscort)
					RequestAntiAirCoverage(bot, attackForce);
				if (Info.EnsureArtillerySiege)
					RequestSiegeArtillery(bot, attackForce, artilleryUnits);
				if (missionTarget != null)
					attackForce.Target = Target.FromActor(missionTarget);
				else if (missionFrozenTarget != null)
					attackForce.Target = Target.FromFrozenActor(missionFrozenTarget);

				if (artilleryUnits.Count > 0)
				{
					var artillerySquad = RegisterNewSquad(bot, SquadCAType.Artillery);
					artillerySquad.Units.AddRange(artilleryUnits);
					artillerySquad.Parent = attackForce.IsValid ? attackForce : null;
					AIUtils.BotDebug("AI ({0}): Added {1} units to squad {2} (escorts {3})", Player.ClientIndex, artilleryUnits.Count, artillerySquad.Type, artillerySquad.Parent);
				}

				// Orphaned artillery squads (e.g. after a load) re-attach to the new assault.
				foreach (var squad in Squads.Where(s => s.Type == SquadCAType.Artillery && (s.Parent == null || !s.Parent.IsValid)))
					squad.Parent = attackForce.IsValid ? attackForce : squad.Parent;

				// 12.4a: the fire-support squad protects the artillery - it trails the
				// artillery squad and pulls a frontline escort of FireSupportEscortPerArtillery
				// tanks per artillery unit out of the assault.
				var fsSquad = Squads.FirstOrDefault(s => s.Type == SquadCAType.FireSupport && s.IsValid);
				if (fireSupportUnits.Count > 0 && fsSquad == null)
					fsSquad = RegisterNewSquad(bot, SquadCAType.FireSupport);
				if (fsSquad != null)
				{
					foreach (var u in fireSupportUnits)
						fsSquad.Units.Add(u);

					var artilleryParent = Squads.Where(s => s.Type == SquadCAType.Artillery && s.IsValid)
						.MaxByOrDefault(s => s.Units.Count);
					if (artilleryParent != null)
					{
						fsSquad.Parent = artilleryParent;
						// Ground vehicles that can hit ground, at most a third of the
						// assault: the screen must win the flanker fight without
						// stripping the raid itself (12.4a review item).
						var escortsNeeded = Math.Min(artilleryParent.Units.Count * Info.FireSupportEscortPerArtillery,
							attackForce.Units.Count / 3);
						foreach (var escort in attackForce.Units
							.Where(u => !Info.FireSupportTypes.Contains(u.Actor.Info.Name) && CanEscortArtillery(u.Actor))
							.OrderByDescending(u => UnitValue(u.Actor))
							.Take(escortsNeeded)
							.ToList())
						{
							attackForce.Units.Remove(escort);
							fsSquad.Units.Add(escort);
						}
					}
					else if (fsSquad.Parent == null || !fsSquad.Parent.IsValid)
						fsSquad.Parent = attackForce.IsValid ? attackForce : null;
				}

				// 6f: support squads trail the newest assault, healing/repairing in its wake.
				foreach (var squad in Squads.Where(s => s.Type == SquadCAType.Support && (s.Parent == null || !s.Parent.IsValid)))
					squad.Parent = attackForce.IsValid ? attackForce : squad.Parent;

				AIUtils.BotDebug("AI ({0}): Added {1} units to squad {2}", Player.ClientIndex, attackForce.Units.Count, attackForce.Type);
				unitsHangingAroundTheBase.Clear();
				foreach (var n in notifyIdleBaseUnits)
					n.UpdatedIdleBaseUnits(unitsHangingAroundTheBase);

				SetNextDesiredAttackForce();
				if (mission?.Type == BotMissionType.Raid && (missionTarget != null || missionFrozenTarget != null))
				{
					LastMissionAssignment = new BotMissionAssignment
					{
						Type = mission.Type,
						RegionIndex = mission.RegionIndex,
						Frozen = missionFrozenTarget != null
					};
					MissionTaken(mission, attackForce);
				}
				else
				{
					// No provider card rode this wave — the squad still committed against
					// an enemy the bot can name: the card it couldn't afford, else the
					// coalition/provider steering target. secure:<player> is the shared
					// push event the coordination report's grammar was designed for;
					// unarmed games have no main target and emit nothing.
					var pushTarget = mission?.TargetPlayer ?? EffectiveMainTarget();
					if (pushTarget != null && pushTarget != Player && attackForce.IsValid)
						CommitSecurePush(pushTarget, attackForce.Units.Count);
				}
				heldDefendMission = null;
				defendMissionHeldSince = -1;
			}
		}

		// 12.5: the staged assault must cover every StageRequiredRoles entry with
		// at least one pool member (any of the unit's roles count). Disabled when
		// unconfigured or when the faction's role map is unavailable.
		bool StagedCompositionReady()
		{
			if (Info.StageCompositionTicks <= 0 || Info.StageRequiredRoles.Count == 0)
				return true;

			var roles = UnitRoles;
			if (roles == null)
				return true;

			var needed = new HashSet<string>(Info.StageRequiredRoles);
			foreach (var u in unitsHangingAroundTheBase)
			{
				if (!roles.ActorRoles.TryGetValue(u.Actor.Info.Name, out var actorRoles))
					continue;

				needed.ExceptWith(actorRoles);
				if (needed.Count == 0)
					return true;
			}

			return false;
		}

		void SetNextDesiredAttackForce()
		{
			desiredAttackForceSize = Info.SquadSize + World.LocalRandom.Next(Info.SquadSizeRandomBonus);
			desiredAttackForceValue = 0;

			if (Info.SquadValue > 0)
			{
				if (Info.SquadValueMaxEarlyBonus == 0 &&
					Info.SquadValueMinLateBonus == 0 &&
					Info.SquadValueMaxLateBonus == 0)
					desiredAttackForceValue = Info.SquadValue + World.LocalRandom.Next(Info.SquadValueRandomBonus);
				else
				{
					desiredAttackForceValue = Info.SquadValue;
					// Add a random bonus between a min and max that scale over the first 20 minutes.
					// Min scales from 0 to SquadValueMinLateBonus; max scales from SquadValueMaxEarlyBonus to SquadValueMaxLateBonus.
					var t = Math.Min(1f, World.WorldTick / SquadValueRampDurationTicks);
					var minBonus = (int)(Info.SquadValueMinLateBonus * t);
					var maxBonus = (int)(Info.SquadValueMaxEarlyBonus + (Info.SquadValueMaxLateBonus - Info.SquadValueMaxEarlyBonus) * t);

					if (maxBonus <= minBonus)
						desiredAttackForceValue += minBonus;
					else
						desiredAttackForceValue += World.LocalRandom.Next(minBonus, maxBonus);
				}
			}
		}

		// DI-2 (12.16): the Director's wave phase scales the assault launch bar — this
		// is the wave's release valve. BuildUp is also what a disabled or absent
		// provider reports, so 100 keeps it neutral by default. Static for tests.
		public static int DirectorForceScalePercent(DirectorPhase phase, SquadManagerBotModuleCAInfo info)
		{
			return phase switch
			{
				DirectorPhase.Pressure => info.DirectorPressureForceScalePercent,
				DirectorPhase.Climax => info.DirectorClimaxForceScalePercent,
				DirectorPhase.Relief => info.DirectorReliefForceScalePercent,
				_ => info.DirectorBuildUpForceScalePercent,
			};
		}

		// TC-2 (12.17): the effective launch-bar scale after an ally's wave is folded in —
		// an allied Climax caps the scale at our own climax scale; no climax = unchanged.
		public static int TeamSyncForceScale(int ownPhaseScale, bool allyClimax, int climaxScale) =>
			allyClimax ? Math.Min(ownPhaseScale, climaxScale) : ownPhaseScale;

		// Zero stays zero: a SquadValue 0 bar trivially passes and must keep passing.
		public static int ApplyForceScale(int threshold, int scalePercent)
		{
			var scaled = (int)((long)threshold * scalePercent / 100);
			return threshold > 0 ? Math.Max(1, scaled) : scaled;
		}

		void ProtectOwn(Actor attacker)
		{
			protectOwnFrom = null;
			protectOwnTicks = Info.ProtectInterval;

			// Fogged scans only chase an attacker the bot can actually see; an
			// unseen attacker still updates the defence center above, and the
			// protection squad's own radius scan picks up anything it can see.
			var protectTarget = FoggedScans && !IsNotHiddenUnit(attacker) ? null : attacker;

			var protectSq = GetSquadOfType(SquadCAType.Protection);
			if (protectSq == null)
				protectSq = RegisterNewSquad(bot, SquadCAType.Protection, protectTarget);

			if (!protectSq.IsValid)
			{
				// Draft from the idle pool only. activeUnits contains both squad members
				// and hanging units, so a world scan would draft units already assigned
				// to Rush/Guerrilla/etc. — dual membership and competing orders.
				var draftable = unitsHangingAroundTheBase
					.Where(u => !Info.ExcludeFromSquadsTypes.Contains(u.Actor.Info.Name) && u.Actor.Info.HasTraitInfo<AttackBaseInfo>()
						&& !u.Actor.Info.HasTraitInfo<BuildingInfo>() && !u.Actor.Info.HasTraitInfo<HarvesterInfo>() && !u.Actor.Info.HasTraitInfo<AircraftInfo>()
						&& !IsNavalUnit(u.Actor))
					.ToList();

				// CA-2 (§12.6): keep a reserve when the response would strip the idle pool —
				// FransGroundDefendForcePreservationGuard's shape ported to the draft site.
				// The donor's short-ETA emergency maps to an attacker already inside the
				// base radius: near threats get the full pool.
				var emergency = attacker == null ||
					(long)(attacker.Location - initialBaseCenter).LengthSquared <=
						(long)Info.MaxBaseRadius * Info.MaxBaseRadius;
				var toDraft = DefendDraftLimit(draftable.Count, emergency, Info, utilityAxesProviders);

				for (var i = 0; i < toDraft; i++)
				{
					var u = draftable[i];
					protectSq.Units.Add(u);
					unitsHangingAroundTheBase.Remove(u);
				}
			}

			if (protectSq.IsValid && !protectSq.IsTargetValid && protectTarget != null)
				protectSq.TargetActor = protectTarget;
		}

		// CA-2: how much of the draftable idle pool a protect-squad refill may take.
		// Full commit when the flag is off, the pool is too small to split, or the
		// attacker is already inside the base (emergency — the donor's short-ETA case).
		// UT-3: when UseUtilityDefendReserve is also on, the TurtleRush axis scales the
		// reserve — turtles dig in deeper, rushers strip the pool for the wave. A missing
		// or disabled provider reads neutral = the plain CA-2 reserve.
		public static int DefendDraftLimit(int draftableCount, bool emergency, SquadManagerBotModuleCAInfo info, IBotUtilityAxes[] providers = null)
		{
			if (!info.UseDefendPreservation || emergency || draftableCount < info.DefendPreservationTriggerUnits)
				return draftableCount;
			var reservePercent = info.DefendPreservationReservePercent;
			if (info.UseUtilityDefendReserve)
			{
				var axis = providers?.FirstEnabledTraitOrDefault()?.UtilityTurtleRush ?? IBotUtilityAxes.Neutral;
				reservePercent = reservePercent *
					DefendReserveAxisPercent(axis, info.DefendReserveTurtleFactorPercent, info.DefendReserveRushFactorPercent) / 100;
			}

			var reserve = Math.Max(info.DefendPreservationMinReserveUnits,
				(int)((long)draftableCount * reservePercent / 100));
			return Math.Max(0, draftableCount - reserve);
		}

		/// <summary>Reserve scale in percent: 100 at neutral, the turtle factor at axis 0, the rush
		/// factor at axis 100, interpolated linearly between the poles.</summary>
		public static int DefendReserveAxisPercent(int turtleRushAxis, int turtleFactor, int rushFactor)
		{
			var axis = Math.Max(0, Math.Min(100, turtleRushAxis));
			return axis >= 50
				? 100 + (axis - 50) * (rushFactor - 100) / 50
				: 100 - (50 - axis) * (100 - turtleFactor) / 50;
		}

		void IBotPositionsUpdated.UpdatedBaseCenter(CPos newLocation)
		{
			initialBaseCenter = newLocation;
		}

		void IBotPositionsUpdated.UpdatedDefenseCenter(CPos newLocation) { }

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (!IsPreferredEnemyUnit(e.Attacker))
				return;

			// Protected priority assets, MCVs, harvesters and buildings
			// TODO: Use *CommonNames, instead of hard-coding trait(info)s.
			if (self.Info.HasTraitInfo<HarvesterInfo>() || self.Info.HasTraitInfo<BuildingInfo>() || self.Info.HasTraitInfo<BaseBuildingInfo>())
			{
				foreach (var n in notifyPositionsUpdated)
					n.UpdatedDefenseCenter(e.Attacker.Location);

				ProtectOwn(e.Attacker);
			}
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			return new List<MiniYamlNode>()
			{
				new("Squads", "", Squads.ConvertAll(s => new MiniYamlNode("Squad", s.Serialize()))),
				new("InitialBaseCenter", FieldSaver.FormatValue(initialBaseCenter)),
				new("UnitsHangingAroundTheBase", FieldSaver.FormatValue(unitsHangingAroundTheBase
					.Where(u => !unitCannotBeOrdered(u.Actor))
					.Select(u => u.Actor.ActorID)
					.ToArray())),
				new("ActiveUnits", FieldSaver.FormatValue(activeUnits
					.Where(a => !unitCannotBeOrdered(a))
					.Select(a => a.ActorID)
					.ToArray())),
				new("RushTicks", FieldSaver.FormatValue(rushTicks)),
				new("AssignRolesTicks", FieldSaver.FormatValue(assignRolesTicks)),
				new("protectionForceTicks", FieldSaver.FormatValue(protectionForceTicks)),
				new("AttackForceTicks", FieldSaver.FormatValue(attackForceTicks)),
				new("MinAttackForceDelayTicks", FieldSaver.FormatValue(minAttackForceDelayTicks)),
			};
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			defendMissionExhaustedRegions.Clear();

			var nodes = data.ToDictionary();

			if (nodes.TryGetValue("InitialBaseCenter", out var initialBaseCenterNode))
				initialBaseCenter = FieldLoader.GetValue<CPos>("InitialBaseCenter", initialBaseCenterNode.Value);

			if (nodes.TryGetValue("UnitsHangingAroundTheBase", out var unitsHangingAroundTheBaseNode))
			{
				unitsHangingAroundTheBase.Clear();
				foreach (var a in FieldLoader.GetValue<uint[]>("UnitsHangingAroundTheBase", unitsHangingAroundTheBaseNode.Value)
					.Select(a => self.World.GetActorById(a)).Where(a => a != null))
				{
					unitsHangingAroundTheBase.Add(new UnitWposWrapper(a));
				}
			}

			if (nodes.TryGetValue("ActiveUnits", out var activeUnitsNode))
			{
				activeUnits.Clear();
				activeUnits.AddRange(FieldLoader.GetValue<uint[]>("ActiveUnits", activeUnitsNode.Value)
					.Select(a => self.World.GetActorById(a)).Where(a => a != null));
			}

			if (nodes.TryGetValue("RushTicks", out var rushTicksNode))
				rushTicks = FieldLoader.GetValue<int>("RushTicks", rushTicksNode.Value);

			if (nodes.TryGetValue("AssignRolesTicks", out var assignRolesTicksNode))
				assignRolesTicks = FieldLoader.GetValue<int>("AssignRolesTicks", assignRolesTicksNode.Value);

			if (nodes.TryGetValue("protectionForceTicks", out var protectionForceTicksNode))
				protectionForceTicks = FieldLoader.GetValue<int>("protectionForceTicks", protectionForceTicksNode.Value);

			if (nodes.TryGetValue("AttackForceTicks", out var attackForceTicksNode))
				attackForceTicks = FieldLoader.GetValue<int>("AttackForceTicks", attackForceTicksNode.Value);

			if (nodes.TryGetValue("MinAttackForceDelayTicks", out var minAttackForceDelayTicksNode))
				minAttackForceDelayTicks = FieldLoader.GetValue<int>("MinAttackForceDelayTicks", minAttackForceDelayTicksNode.Value);

			if (nodes.TryGetValue("Squads", out var squadsNode))
			{
				Squads.Clear();
				foreach (var n in squadsNode.Nodes)
					Squads.Add(SquadCA.Deserialize(bot, this, n.Value));
			}

			// Reconcile stranded units: an actor restored into activeUnits that belongs to
			// no squad and no idle pool would never be managed again — park it in the pool.
			var inSquads = Squads.SelectMany(s => s.Units.Select(u => u.Actor)).ToHashSet();
			var inPool = unitsHangingAroundTheBase.Select(u => u.Actor).ToHashSet();
			foreach (var a in activeUnits.Where(a => !inSquads.Contains(a) && !inPool.Contains(a) && !unitCannotBeOrdered(a)))
				unitsHangingAroundTheBase.Add(new UnitWposWrapper(a));
		}

		public bool CanBuildMoreOfAircraft(ActorInfo actorInfo)
		{
			foreach (var aircraftBuilder in aircraftBuilders)
			{
				if (!aircraftBuilder.IsTraitEnabled())
					continue;

				if (aircraftBuilder.CanBuildMoreOfAircraft(actorInfo))
					return true;
			}

			return false;
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			constructionYardBuildings.Dispose();
		}
	}
}
