#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 *
 * Ported from the Crystallized Nexus CombatAnalysisBotModule (crystallized-nexus
 * commit 30cf70a, GPLv3, Copyright (c) The Crystallized Nexus Developers).
 * Adaptations: CN's DefenseRole enum -> BotThreatRoles strings matching the
 * demand.* suffixes; BotCapabilitiesInfo economy tags -> Harvester trait;
 * CNBotLog/CNBotPerf -> AIUtils.BotDebug / plain IBotTick.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;
using CAAIUtils = OpenRA.Mods.CA.AIUtils;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Tracks enemy attack patterns and exposes per-role threat weights and a nemesis player.",
		"Producer only: consumed through IBotThreatAnalysis; nothing is wired into scoring yet.")]
	public class CombatAnalysisBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Target type strings that classify an attacker as an air threat (maps to the antiair role).")]
		public readonly FrozenSet<string> AirTargetTypes = new HashSet<string> { "Air", "Aircraft", "Plane", "Helicopter" }.ToFrozenSet();

		[Desc("Target type strings that classify an attacker as an infantry threat (maps to the antiinfantry role).")]
		public readonly FrozenSet<string> InfantryTargetTypes = new HashSet<string> { "Infantry" }.ToFrozenSet();

		[Desc("Target type strings that classify an attacker as a vehicle threat (maps to the antiarmour role).")]
		public readonly FrozenSet<string> VehicleTargetTypes = new HashSet<string> { "Vehicle", "Tank" }.ToFrozenSet();

		[Desc("Base threat weight added per qualifying damage event, before value- and category-scaling.")]
		public readonly float WeightPerHit = 10f;

		[Desc("Attacker cost (ValuedInfo.Cost) at which the value-based weight multiplier is 1.0.",
			"Cheaper attackers scale down towards MinValueWeightMultiplier, pricier ones scale up towards MaxValueWeightMultiplier.")]
		public readonly float ValueWeightReference = 1000f;

		[Desc("Floor for the value-based weight multiplier, so a cheap attacker's hits still register instead of scaling away to nothing.")]
		public readonly float MinValueWeightMultiplier = 0.3f;

		[Desc("Ceiling for the value-based weight multiplier, so a single hit from an expensive attacker cannot saturate a threat role by itself.")]
		public readonly float MaxValueWeightMultiplier = 3f;

		[Desc("Fraction of the (value-scaled) weight recorded when a combat unit — neither a building nor an economy actor — is hit,",
			"versus the full weight for buildings/economy. Set to 0 to ignore combat-unit hits entirely.")]
		public readonly float CombatUnitWeightFraction = 0.275f;

		[Desc("Minimum ticks between recording direct threat-role damage events against buildings or economy actors.")]
		public readonly int ThreatRecordInterval = 25;

		[Desc("Minimum ticks between recording threat-role damage events against combat units.",
			"Tracked on its own counter from ThreatRecordInterval: combat units get hit far more often than",
			"buildings/economy, and a shared counter would let that noise crowd out the rarer, more important signal.")]
		public readonly int CombatUnitThreatRecordInterval = 25;

		[Desc("Minimum raw damage value for a hit to count as a threat (filters negligible hits).")]
		public readonly int MinDamageThreshold = 1;

		[Desc("Minimum accumulated threat weight required to trigger reactive defense building.")]
		public readonly float ReactThreshold = 20f;

		[Desc("Fraction of weight removed per decay interval (0.0-1.0). 0.1 = lose 10% every interval.")]
		public readonly float DecayRate = 0.1f;

		[Desc("Interval in ticks between weight decay steps.")]
		public readonly int DecayInterval = 1000;

		[Desc("Nemesis score added when an enemy attacks one of our units or buildings.")]
		public readonly float NemesisWeightPerHit = 5f;

		[Desc("Minimum ticks between recording nemesis damage events.")]
		public readonly int NemesisRecordInterval = 25;

		[Desc("Additional nemesis score added when an enemy attacks an ally (not us).")]
		public readonly float NemesisAllyWeightPerHit = 2f;

		[Desc("Minimum nemesis score required before a player is considered the nemesis.")]
		public readonly float NemesisThreshold = 15f;

		public override object Create(ActorInitializer init) { return new CombatAnalysisBotModule(init.Self, this); }
	}

	public class CombatAnalysisBotModule : ConditionalTrait<CombatAnalysisBotModuleInfo>, IBotTick, IBotRespondToAttack, IBotThreatAnalysis, INotifyAppliedDamage
	{
		readonly Dictionary<string, float> weights = new()
		{
			[BotThreatRoles.AntiInfantry] = 0f,
			[BotThreatRoles.AntiArmour] = 0f,
			[BotThreatRoles.AntiAir] = 0f,

			// No artillery entry: ClassifyAttacker only ever yields antiair, antiinfantry
			// or antiarmour, so its weight could never leave zero and GetHighestThreatRole
			// could never name it. It is a worth marker, not a threat something attacks with.
		};

		// Per-enemy-player nemesis score: higher = this player attacked us more
		readonly Dictionary<OpenRA.Player, float> nemesisScores = [];

		// Per-enemy-player dealt score: higher = we damaged this player more — the
		// 'damage we have dealt to e' side of §4.3's w_hurt ratio. Shares
		// NemesisWeightPerHit deliberately: both halves must carry the same units
		// for the taken/(taken+dealt) share to stay meaningful.
		readonly Dictionary<OpenRA.Player, float> dealtScores = [];
		readonly Dictionary<string, string> attackerRoleCache = [];
		readonly Dictionary<string, bool> economyActorCache = [];
		readonly Dictionary<string, float> attackerValueMultiplierCache = [];

		readonly OpenRA.Player self;
		readonly World world;
		int decayTicks;
		int nextThreatRecordTick;
		int nextCombatUnitThreatRecordTick;

		// Per attacker, because the score it throttles is per attacker too. One shared tick let whoever
		// struck first in a frame mute everybody else until the interval expired.
		readonly Dictionary<OpenRA.Player, int> nextNemesisRecordTickByAttacker = [];

		// Same per-victim-owner throttling for the dealt side.
		readonly Dictionary<OpenRA.Player, int> nextDealtRecordTickByVictim = [];

		public CombatAnalysisBotModule(Actor self, CombatAnalysisBotModuleInfo info)
			: base(info)
		{
			this.self = self.Owner;
			world = self.World;
		}

		public float GetThreatWeight(string role) =>
			weights.TryGetValue(role, out var w) ? w : 0f;

		public bool HasActiveThreat() =>
			weights.Values.Any(w => w >= Info.ReactThreshold);

		/// <summary>
		/// How hard this role is currently being pressed, from 0 at ReactThreshold to 1 once the
		/// weight has grown to <paramref name="saturationFactor"/> times the threshold. Returns 0
		/// while the role is not an active threat at all.
		/// <para>
		/// A ramp rather than a switch, so a single raid and a sustained assault are told apart, and
		/// callers scaling something by it fall back on their own as BotTick decays the weights.
		/// </para>
		/// </summary>
		public float GetThreatIntensity(string role, float saturationFactor)
		{
			var threshold = Info.ReactThreshold;
			if (threshold <= 0f)
				return 0f;

			var weight = GetThreatWeight(role);
			if (weight < threshold)
				return 0f;

			var saturation = threshold * Math.Max(1f, saturationFactor);
			if (saturation <= threshold)
				return 1f;

			return Math.Clamp((weight - threshold) / (saturation - threshold), 0f, 1f);
		}

		/// <summary>Returns the role with the highest threat weight at or above ReactThreshold, or null if none.</summary>
		public string GetHighestThreatRole()
		{
			// Seeded just below ReactThreshold, not at ReactThreshold - 1: the old seed let a role
			// one point under the threshold win, so this reported an active role while HasActiveThreat()
			// (which tests >= ReactThreshold) still said there was no threat. Callers like
			// UnitBuilderBotModuleCA panic-building gate on one and pick with the other.
			string bestRole = null;
			var bestWeight = 0f;
			foreach (var kv in weights)
			{
				if (kv.Value < Info.ReactThreshold || kv.Value <= bestWeight)
					continue;

				bestWeight = kv.Value;
				bestRole = kv.Key;
			}

			return bestRole;
		}

		/// <summary>
		/// Returns the enemy player who has attacked us (or our allies) the most.
		/// Returns null if no player has crossed NemesisThreshold yet.
		/// </summary>
		public OpenRA.Player GetNemesis()
		{
			OpenRA.Player nemesis = null;
			var best = Info.NemesisThreshold - 1f;
			foreach (var kv in nemesisScores)
			{
				if (kv.Value > best)
				{
					best = kv.Value;
					nemesis = kv.Key;
				}
			}

			return nemesis;
		}

		public float GetNemesisScore(OpenRA.Player attacker)
		{
			return attacker != null && nemesisScores.TryGetValue(attacker, out var score) ? score : 0;
		}

		public float GetDealtScore(OpenRA.Player victim)
		{
			return victim != null && dealtScores.TryGetValue(victim, out var score) ? score : 0;
		}

		/// <summary>
		/// Called by the squad manager when an ally is attacked.
		/// Increments the ally-attack weight for the attacker.
		/// </summary>
		public void RegisterAllyAttack(OpenRA.Player attacker)
		{
			if (IsTraitDisabled)
				return;
			if (attacker == null || attacker == self)
				return;
			if (attacker.RelationshipWith(self) != PlayerRelationship.Enemy)
				return;

			nemesisScores.TryGetValue(attacker, out var current);
			nemesisScores[attacker] = Math.Min(100f, current + Info.NemesisAllyWeightPerHit);
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (IsTraitDisabled)
				return;
			if (e.Attacker == null || e.Attacker.Disposed)
				return;
			if (e.Attacker.Owner.RelationshipWith(self.Owner) != PlayerRelationship.Enemy)
				return;
			if (e.Damage.Value < Info.MinDamageThreshold)
				return;

			// Defense threat tracking. Buildings and economy actors (harvesters, refineries, ...) count at
			// full weight; combat units count too, but at a reduced fraction, so a skirmish out on the
			// field registers as a signal without drowning out an attack on something that actually
			// matters. Each category is throttled on its own counter: combat units get hit far more
			// often than buildings/economy, and a shared counter would let that noise crowd out the
			// rarer, more important signal (e.g. harvesters being sniped) almost every time.
			var isSubstance = self.Info.HasTraitInfo<BuildingInfo>() || IsEconomyActor(self.Info);
			var throttleTick = isSubstance ? nextThreatRecordTick : nextCombatUnitThreatRecordTick;
			if (world.WorldTick >= throttleTick)
			{
				var role = ClassifyAttacker(e.Attacker);
				if (role != null)
				{
					var categoryFraction = isSubstance ? 1f : Info.CombatUnitWeightFraction;
					var weight = Info.WeightPerHit * GetValueWeightMultiplier(e.Attacker) * categoryFraction;
					var before = weights[role];
					weights[role] = Math.Min(100f, before + weight);

					ReportThreatTransition(role, before, self, e.Attacker, isSubstance);
				}

				if (isSubstance)
					nextThreatRecordTick = world.WorldTick + Math.Max(1, Info.ThreatRecordInterval);
				else
					nextCombatUnitThreatRecordTick = world.WorldTick + Math.Max(1, Info.CombatUnitThreatRecordInterval);
			}

			// Nemesis tracking — all owned actors (buildings + units).
			// Throttled per attacker, not globally. The score is kept per enemy but the window was shared,
			// so in a free-for-all whichever attacker's hit landed first in the event order silenced every
			// other player for the whole interval - and could end up crowned nemesis while somebody else
			// was doing more damage.
			var attacker = e.Attacker.Owner;
			if (nextNemesisRecordTickByAttacker.TryGetValue(attacker, out var nextTick) && world.WorldTick < nextTick)
				return;

			nemesisScores.TryGetValue(attacker, out var current);
			nemesisScores[attacker] = Math.Min(100f, current + Info.NemesisWeightPerHit);
			nextNemesisRecordTickByAttacker[attacker] = world.WorldTick + Math.Max(1, Info.NemesisRecordInterval);
		}

		// The dealt half of §4.3's w_hurt ratio: INotifyAppliedDamage fires on the
		// ATTACKER's player actor (Health.cs), the exact mirror of INotifyDamage on
		// the victim's side. Credited against the victim's owner, throttled per
		// victim the same way nemesis throttles per attacker.
		void INotifyAppliedDamage.AppliedDamage(Actor self, Actor damaged, AttackInfo e)
		{
			if (IsTraitDisabled)
				return;
			if (damaged == null || damaged.Disposed)
				return;

			var victim = damaged.Owner;
			if (victim == null || victim.RelationshipWith(this.self) != PlayerRelationship.Enemy)
				return;
			if (e.Damage.Value < Info.MinDamageThreshold)
				return;

			if (nextDealtRecordTickByVictim.TryGetValue(victim, out var nextTick) && world.WorldTick < nextTick)
				return;

			dealtScores.TryGetValue(victim, out var current);
			dealtScores[victim] = Math.Min(100f, current + Info.NemesisWeightPerHit);
			nextDealtRecordTickByVictim[victim] = world.WorldTick + Math.Max(1, Info.NemesisRecordInterval);
		}

		/// <summary>
		/// Logs the two moments in a threat role's life that actually mean something: the point where it
		/// crosses ReactThreshold and the bot starts building against it, and the point where it pins at
		/// the cap. Logging every recorded hit would bury both in noise.
		/// <para>
		/// This exists because the module's failure mode is silence. Sniping harvesters registered
		/// nothing at all until the economy actors were added, and nobody noticed for the length of a
		/// match — there was no way to see that the table had stayed at zero. It also lets the combat-unit
		/// weighting be judged in practice: if a role pins at 100 during every field engagement,
		/// CombatUnitWeightFraction is too high, and the log is what shows it.
		/// </para>
		/// </summary>
		void ReportThreatTransition(string role, float before, Actor damaged, Actor attacker, bool isSubstance)
		{
			var now = weights[role];

			if (before < Info.ReactThreshold && now >= Info.ReactThreshold)
				CAAIUtils.BotDebug("{0} threat {1} reached react threshold ({2:0.0}) — hit on {3} by {4} [{5}]",
					self, role, now, damaged.Info.Name, attacker.Info.Name,
					isSubstance ? "substance" : "combat unit");
			else if (before < 100f && now >= 100f)
				CAAIUtils.BotDebug("{0} threat {1} pinned at the cap — hit on {2} by {3} [{4}]",
					self, role, damaged.Info.Name, attacker.Info.Name,
					isSubstance ? "substance" : "combat unit");
		}

		bool IsEconomyActor(ActorInfo info)
		{
			if (economyActorCache.TryGetValue(info.Name, out var cached))
				return cached;

			// CN keyed this off BotCapabilitiesInfo capability tags; Cameo has no
			// capability-tag trait, so economy derives from traits instead: a mobile
			// Harvester is the only non-building economy case (refineries are
			// buildings and already count at full weight via BuildingInfo).
			var isEconomy = info.HasTraitInfo<HarvesterInfo>();
			economyActorCache[info.Name] = isEconomy;
			return isEconomy;
		}

		float GetValueWeightMultiplier(Actor attacker)
		{
			if (attackerValueMultiplierCache.TryGetValue(attacker.Info.Name, out var cached))
				return cached;

			// No ValuedInfo (e.g. a walking husk or a scripted actor) is treated as reference-cost,
			// i.e. a neutral 1.0 multiplier, rather than falling to the floor.
			var cost = attacker.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? Info.ValueWeightReference;
			var multiplier = Info.ValueWeightReference > 0f
				? Math.Clamp(cost / Info.ValueWeightReference, Info.MinValueWeightMultiplier, Info.MaxValueWeightMultiplier)
				: 1f;

			attackerValueMultiplierCache[attacker.Info.Name] = multiplier;
			return multiplier;
		}

		string ClassifyAttacker(Actor attacker)
		{
			if (attackerRoleCache.TryGetValue(attacker.Info.Name, out var cachedRole))
				return cachedRole;

			var isAir = false;
			var isInfantry = false;
			var isVehicle = false;

			foreach (var targetable in attacker.TraitsImplementing<ITargetable>())
			{
				foreach (var targetType in targetable.TargetTypes)
				{
					var targetTypeString = targetType.ToString();
					isAir |= Info.AirTargetTypes.Contains(targetTypeString);
					isInfantry |= Info.InfantryTargetTypes.Contains(targetTypeString);
					isVehicle |= Info.VehicleTargetTypes.Contains(targetTypeString);
				}
			}

			string role = null;
			if (isAir)
				role = BotThreatRoles.AntiAir;
			else if (isInfantry)
				role = BotThreatRoles.AntiInfantry;
			else if (isVehicle)
				role = BotThreatRoles.AntiArmour;

			attackerRoleCache[attacker.Info.Name] = role;
			return role;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (IsTraitDisabled)
				return;
			if (--decayTicks > 0)
				return;

			decayTicks = Info.DecayInterval;
			var decay = 1f - Info.DecayRate;
			foreach (var key in weights.Keys.ToList())
				weights[key] = Math.Max(0f, weights[key] * decay);
			foreach (var key in nemesisScores.Keys.ToList())
				nemesisScores[key] = Math.Max(0f, nemesisScores[key] * decay);
			foreach (var key in dealtScores.Keys.ToList())
				dealtScores[key] = Math.Max(0f, dealtScores[key] * decay);
		}
	}
}
