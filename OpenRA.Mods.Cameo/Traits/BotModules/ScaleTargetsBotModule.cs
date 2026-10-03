#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// One size category's line of the growth law (DESIGN 19.10). Every fraction is an integer in thousandths
	/// (1000 = 1.0) so the synced math never touches a float. Every tier writes every field (DESIGN 19.1).
	/// </summary>
	public class ScaleCategory
	{
		[Desc("Own line at the easiest tier, thousandths of a unit (3000 = 3.0). For `army` it multiplies the personality's SquadValue.")]
		public readonly int Min = 0;

		[Desc("Own line at cameogod, thousandths. The tier index interpolates linearly between Min and Max; the one rounding step is the final floor.")]
		public readonly int Max = 0;

		[Desc("Enemy ratio at the easiest tier, thousandths: the target follows RatioMin x what was SEEN of the enemy.")]
		public readonly int RatioMin = 0;

		[Desc("Enemy ratio at cameogod, thousandths.")]
		public readonly int RatioMax = 0;

		[Desc("Safety margin for the unscouted map, thousandths: 1000 means a fully dark map doubles what was seen.")]
		public readonly int Margin = 0;

		[Desc("Growth per game HOUR, thousandths: 500 = +50% of the own line per hour. Linear, never capped (long games grow without limit).")]
		public readonly int Growth = 0;

		[Desc("Lower clamp, in units (not thousandths). A physical cap still wins over it.")]
		public readonly int Floor = 0;

		[Desc("Percent this category leans at the poles of the Turtle<->Rush utility axis (signed: negative = more toward Turtle, positive = more toward Rush). 0 = no lean.")]
		public readonly int TurtleRushLean = 0;

		[Desc("Percent this category leans at the poles of the TechRush<->Expansion utility axis (signed: negative = more toward TechRush, positive = more toward Expansion). 0 = no lean.")]
		public readonly int TechRushExpansionLean = 0;

		public ScaleLine Line => new(Min, Max, RatioMin, RatioMax, Margin, Growth, Floor);
	}

	/// <summary>Published inputs and targets of the last recompute, for the situation log. Immutable once built.</summary>
	public sealed class ScaleTargetsSnapshot
	{
		public int Tick, Tier, TeamSize, UnscoutedMilli, GameMinutesMilli, ArmyBaseline;
		public string Personality = "";
		public string[] Categories = Array.Empty<string>();
		public long[] Seen = Array.Empty<long>();
		public int[] Targets = Array.Empty<int>();
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Scale targets (DESIGN 19.10, AI_ARCHITECTURE 12.22): HOW BIG the base and army should be. One target per size category,",
		"grown from the difficulty line, the enemy the bot has SEEN (fog memory only), the unscouted share of the map,",
		"the personality (and the utility axes) and game time. Publishes IBotScaleTargets; the existing builders read it.",
		"It never builds and never issues orders. With no enabled provider every consumer keeps its own limit.",
		"",
		"FIXED POINT: every fraction in this block is an integer in THOUSANDTHS (Min: 1000 = 1.0, Max: 3250 = 3.25).",
		"Bots run in lockstep, so the synced math is integer only; the single rounding step is a floor at the end.")]
	public class ScaleTargetsBotModuleInfo : ConditionalTraitInfo
	{
		public static readonly string[] CategoryNames =
		{
			"army", "harvester", "refinery", "production", "conyard", "tech", "superweapon", "defence", "aircraft"
		};

		[Desc("Bot type names, EASIEST FIRST: the index of the active BotLimits tier on this list is the tier index of the line.")]
		public readonly string[] Difficulties =
		{
			"easiest", "veryeasy", "easy", "medium", "hard",
			"veryhard", "brutal", "challenger", "unbeatable", "cameogod"
		};

		[Desc("Ticks between recomputes. The targets are cached in between.")]
		public readonly int RecomputeTicks = 125;

		[Desc("A region not seen for this many ticks (or never seen) counts as unscouted. Mirrors ScoutBotModule.StaleAfterTicks.")]
		public readonly int ScoutStaleTicks = 2500;

		[Desc("Lean the personality multiplier by the utility axes (BotUtilityAxes), each category by its TurtleRushLean / TechRushExpansionLean.",
			"Off or no axis provider: the personality table alone.")]
		public readonly bool UseUtilityAxes = true;

		[FieldLoader.LoadUsing(nameof(LoadCategories))]
		[Desc("One block per size category (army, harvester, refinery, production, conyard, tech, superweapon, defence, aircraft).")]
		public readonly Dictionary<string, ScaleCategory> Categories = [];

		[FieldLoader.LoadUsing(nameof(LoadPersonalityMultipliers))]
		[Desc("Personality -> category -> multiplier in thousandths (1250 = x1.25). A missing entry is 1000.")]
		public readonly Dictionary<string, Dictionary<string, int>> PersonalityMultipliers = [];

		static object LoadCategories(MiniYaml yaml)
		{
			var categories = new Dictionary<string, ScaleCategory>();
			var node = yaml.NodeWithKeyOrDefault("Categories");
			if (node == null)
				return categories;

			foreach (var child in node.Value.Nodes)
			{
				if (Array.IndexOf(CategoryNames, child.Key) < 0)
					throw new YamlException($"ScaleTargetsBotModule: unknown category '{child.Key}'; known: {string.Join(", ", CategoryNames)}.");

				var category = new ScaleCategory();
				FieldLoader.Load(category, child.Value);
				if (category.Min > category.Max)
					throw new YamlException($"ScaleTargetsBotModule: category '{child.Key}' has Min above Max.");

				categories[child.Key] = category;
			}

			return categories;
		}

		static object LoadPersonalityMultipliers(MiniYaml yaml)
		{
			var result = new Dictionary<string, Dictionary<string, int>>();
			var node = yaml.NodeWithKeyOrDefault("PersonalityMultipliers");
			if (node == null)
				return result;

			foreach (var personality in node.Value.Nodes)
			{
				var perCategory = new Dictionary<string, int>();
				foreach (var entry in personality.Value.Nodes)
				{
					if (Array.IndexOf(CategoryNames, entry.Key) < 0)
						throw new YamlException($"ScaleTargetsBotModule: PersonalityMultipliers.{personality.Key} names unknown category '{entry.Key}'.");

					perCategory[entry.Key] = int.Parse(entry.Value.Value, CultureInfo.InvariantCulture);
				}

				result[personality.Key] = perCategory;
			}

			return result;
		}

		public override object Create(ActorInitializer init) { return new ScaleTargetsBotModule(init.Self, this); }
	}

	public class ScaleTargetsBotModule : ConditionalTrait<ScaleTargetsBotModuleInfo>, IBotTick, IBotScaleTargets
	{
		readonly World world;
		readonly OpenRA.Player player;

		// Cached once, on the first recompute (the player's traits do not change).
		bool resolved;
		MasterAiBotModule master;
		BotPersonalityController personalityController;
		IBotUtilityAxes axes;
		IBotZoneTopology topology;
		IBotUnitRoles roles;
		BotGlobalUnitBudget budget;
		HashSet<string> superweaponNames;

		int nextRecomputeTick;
		int tier = -1;
		int lastArmyBaseline;
		readonly Dictionary<string, int> targets = new(StringComparer.Ordinal);
		readonly Dictionary<string, int> targetByBuilding = new(StringComparer.Ordinal);

		// Inputs of the last recompute, kept so the army target (which depends on the caller's baseline) can be
		// evaluated on demand against the same picture of the world.
		long armySeen;
		int unscoutedMilli, teamSize = 1, personalityArmyMilli = ScaleTargetsEval.One;
		long gameTicksAtRecompute;
		int ticksPerMinute = 1500;

		public ScaleTargetsSnapshot Snapshot { get; private set; }

		public ScaleTargetsBotModule(Actor self, ScaleTargetsBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (IsTraitDisabled)
				return;

			var tick = world.WorldTick;
			if (resolved && tick < nextRecomputeTick)
				return;

			Recompute(tick);
			nextRecomputeTick = tick + Math.Max(1, Info.RecomputeTicks);
		}

		void Resolve()
		{
			var playerActor = player.PlayerActor;
			master = playerActor.TraitsImplementing<MasterAiBotModule>().FirstEnabledTraitOrDefault();
			personalityController = playerActor.TraitOrDefault<BotPersonalityController>();
			axes = Info.UseUtilityAxes ? playerActor.TraitsImplementing<IBotUtilityAxes>().FirstEnabledTraitOrDefault() : null;
			topology = playerActor.TraitsImplementing<IBotZoneTopology>().FirstOrDefault();
			roles = playerActor.TraitsImplementing<IBotUnitRoles>().FirstEnabledTraitOrDefault();
			budget = playerActor.TraitsImplementing<BotGlobalUnitBudget>().FirstEnabledTraitOrDefault();

			// The same rules-derived superweapon tag the squad manager's target priorities use; no actor id is typed.
			superweaponNames = new HashSet<string>(StringComparer.Ordinal);
			foreach (var kv in BotTargetTags.BuildTagMap(world.Map.Rules))
				if (kv.Value.Contains(BotTargetTags.Superweapon))
					superweaponNames.Add(kv.Key);

			resolved = true;

			// One debug.log line: how many of the hand-written BuildingLimits entries the tech / superweapon categories take over.
			var limits = playerActor.TraitsImplementing<BaseBuilderBotModuleCA>().FirstEnabledTraitOrDefault()?.Info.BuildingLimits;
			if (limits != null)
			{
				var superweapons = limits.Keys.Count(k => superweaponNames.Contains(k));
				var tech = limits.Keys.Count(k => !superweaponNames.Contains(k) && IsTech(k));
				Log.Write("debug", $"AI ({player.ClientIndex}): ST BuildingLimits entries taken over by a category: tech {tech}, superweapon {superweapons} of {limits.Count}");
			}
		}

		/// <summary>The tier index from the active BotLimits (its condition, `<tier>bot`), else the owner's bot type. -1 = unranked.</summary>
		int ResolveTier()
		{
			var expression = BotLimitsResolver.Describe(BotLimitsResolver.Current(player));
			if (expression.EndsWith("bot", StringComparison.Ordinal))
			{
				var index = Array.IndexOf(Info.Difficulties, expression[..^3]);
				if (index >= 0)
					return index;
			}

			return BotDifficultyLadder.RankOf(player, Info.Difficulties, BotDifficultyLadder.DefaultAliases);
		}

		void Recompute(int tick)
		{
			if (!resolved)
				Resolve();

			tier = ResolveTier();
			ticksPerMinute = (int)(60000L / Math.Max(1, world.Timestep));
			gameTicksAtRecompute = tick;
			teamSize = AliveTeamSize();

			var situation = master?.Situation;
			unscoutedMilli = UnscoutedShareMilli(situation, tick);

			var seen = SeenNumbers(situation);
			var personality = personalityController?.CurrentPersonality ?? "";

			var turtleRush = axes?.UtilityTurtleRush ?? IBotUtilityAxes.Neutral;
			var techExpansion = axes?.UtilityTechRushExpansion ?? IBotUtilityAxes.Neutral;

			var names = ScaleTargetsBotModuleInfo.CategoryNames;
			var seenArray = new long[names.Length];
			var targetArray = new int[names.Length];
			targets.Clear();
			armySeen = seen["army"];
			for (var i = 0; i < names.Length; i++)
			{
				var name = names[i];
				seenArray[i] = seen[name];
				if (tier < 0 || !Info.Categories.TryGetValue(name, out var category))
					continue;

				var p = PersonalityMilli(personality, name, category, turtleRush, techExpansion);
				if (name == "army")
				{
					personalityArmyMilli = p;
					targetArray[i] = ArmyTarget(lastArmyBaseline);
					continue;
				}

				var target = ScaleTargetsEval.Target(category.Line, tier, Info.Difficulties.Length, tick, ticksPerMinute,
					seen[name], unscoutedMilli, teamSize, p, 1, PhysicalCap(name));
				targets[name] = target;
				targetArray[i] = target;
			}

			targetByBuilding.Clear();
			Snapshot = new ScaleTargetsSnapshot
			{
				Tick = tick,
				Tier = tier,
				TeamSize = teamSize,
				UnscoutedMilli = unscoutedMilli,
				GameMinutesMilli = (int)Math.Min(int.MaxValue, 1000L * tick / Math.Max(1, ticksPerMinute)),
				ArmyBaseline = lastArmyBaseline,
				Personality = personality,
				Categories = names,
				Seen = seenArray,
				Targets = targetArray
			};
		}

		int PersonalityMilli(string personality, string name, ScaleCategory category, int turtleRush, int techExpansion)
		{
			var multiplier = ScaleTargetsEval.One;
			if (Info.PersonalityMultipliers.TryGetValue(personality, out var perCategory) && perCategory.TryGetValue(name, out var m))
				multiplier = m;

			return ScaleTargetsEval.Personality(multiplier,
				ScaleTargetsEval.AxisLeanFactor(turtleRush, category.TurtleRushLean),
				ScaleTargetsEval.AxisLeanFactor(techExpansion, category.TechRushExpansionLean));
		}

		// The physical caps (DESIGN 19.10: only these stop growth): the aircraft count never exceeds this bot's share of
		// BotGlobalUnitBudget. No planner exposes the resource fields in reach, so refineries carry no cap yet.
		int PhysicalCap(string category)
		{
			if (category == "aircraft" && budget != null)
				return budget.CurrentShare();

			return -1;
		}

		int AliveTeamSize()
		{
			var count = 0;
			foreach (var p in world.Players)
				if (!p.NonCombatant && p.WinState == WinState.Undefined &&
					(p == player || p.RelationshipWith(player) == PlayerRelationship.Ally))
					count++;

			return Math.Max(1, count);
		}

		/// <summary>
		/// Seen_k from fog memory ONLY: the master's per-enemy profiles and remembered actors (BotFogMemory), summed over every
		/// enemy. Nothing here enumerates an enemy actor in the world.
		/// </summary>
		Dictionary<string, long> SeenNumbers(BotSituation situation)
		{
			var seen = new Dictionary<string, long>(StringComparer.Ordinal);
			foreach (var name in ScaleTargetsBotModuleInfo.CategoryNames)
				seen[name] = 0;

			if (situation?.Enemies == null)
				return seen;

			var perName = new Dictionary<string, int>(StringComparer.Ordinal);
			foreach (var enemy in situation.Enemies.Values)
			{
				if (!enemy.Alive)
					continue;

				seen["army"] += enemy.ArmyValue;
				seen["defence"] += enemy.ArmyValue;
				seen["harvester"] += enemy.Harvesters;
				seen["refinery"] += enemy.Refineries;

				perName.Clear();
				foreach (var actor in situation.Remembered(enemy.Player))
				{
					if (actor.Building)
					{
						if (actor.BaseBuilding)
							seen["conyard"]++;
						if (actor.Production)
							perName[actor.Info.Name] = perName.GetValueOrDefault(actor.Info.Name) + 1;
						if (superweaponNames.Contains(actor.Info.Name))
							seen["superweapon"]++;
						else if (IsTech(actor.Info.Name))
							seen["tech"]++;
					}
					else if (actor.Aircraft && actor.Combat)
						seen["aircraft"]++;
				}

				// Production is a PER-TYPE limit: what one enemy fields of its most numerous production type.
				var most = 0;
				foreach (var count in perName.Values)
					most = Math.Max(most, count);
				seen["production"] += most;
			}

			return seen;
		}

		bool IsTech(string actorName) =>
			roles != null && roles.ActorRoles.TryGetValue(actorName, out var set) && set.Contains(BotUnitRole.Tech);

		/// <summary>
		/// The share of the map's area (zone cell counts, else region count) never seen or not seen for ScoutStaleTicks, own
		/// territory excluded, in thousandths. No situation yet reads as fully dark.
		/// </summary>
		int UnscoutedShareMilli(BotSituation situation, int tick)
		{
			var regions = situation?.Regions;
			if (regions == null)
				return ScaleTargetsEval.One;

			var useTerritory = topology != null && topology.Generation >= 0;
			long total = 0, dark = 0;
			for (var i = 0; i < regions.CellCount; i++)
			{
				if (useTerritory && topology.IsInTerritory(regions.CenterOf(i)))
					continue;

				long weight = regions.ZoneBacked && useTerritory && i < topology.Regions.Count
					? Math.Max(1, topology.Regions[i].Size) : 1;
				total += weight;

				var fresh = false;
				foreach (var enemyRegions in regions.ByEnemy.Values)
				{
					if (i >= enemyRegions.Length)
						continue;

					var r = enemyRegions[i];
					if (r != null && r.EverSeen && tick - r.LastSeenTick <= Info.ScoutStaleTicks)
					{
						fresh = true;
						break;
					}
				}

				if (!fresh)
					dark += weight;
			}

			return total <= 0 ? 0 : (int)(dark * ScaleTargetsEval.One / total);
		}

		int ArmyTarget(int baselineValue)
		{
			if (tier < 0 || !Info.Categories.TryGetValue("army", out var category))
				return 0;

			return ScaleTargetsEval.Target(category.Line, tier, Info.Difficulties.Length, gameTicksAtRecompute, ticksPerMinute,
				armySeen, unscoutedMilli, teamSize, personalityArmyMilli, Math.Max(0, baselineValue), -1);
		}

		bool IBotScaleTargets.TryGetTarget(string category, out int target)
		{
			target = 0;
			return !IsTraitDisabled && resolved && tier >= 0 && targets.TryGetValue(category, out target);
		}

		bool IBotScaleTargets.TryGetArmyValueTarget(int baselineValue, out int value)
		{
			value = 0;
			if (IsTraitDisabled || !resolved || tier < 0 || !Info.Categories.ContainsKey("army"))
				return false;

			lastArmyBaseline = baselineValue;
			value = ArmyTarget(baselineValue);
			return true;
		}

		bool IBotScaleTargets.TryGetBuildingTarget(string actorName, out int target)
		{
			target = 0;
			if (IsTraitDisabled || !resolved || tier < 0)
				return false;

			if (targetByBuilding.TryGetValue(actorName, out target))
			{
				if (target >= 0)
					return true;

				target = 0;
				return false;
			}

			var category = superweaponNames.Contains(actorName) ? "superweapon" : IsTech(actorName) ? "tech" : null;
			if (category == null || !targets.TryGetValue(category, out target))
			{
				targetByBuilding[actorName] = -1;
				target = 0;
				return false;
			}

			targetByBuilding[actorName] = target;
			return true;
		}
	}
}
