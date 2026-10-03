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
using OpenRA.Mods.Common.Traits.Radar;
using OpenRA.Support;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>The knob vector, opening and react events of the last update, for the situation log. Immutable once built.</summary>
	public sealed class BuildOrderSnapshot
	{
		public int Tick;
		public string Personality = "", Faction = "", EnemyFaction = "", Opening = "", OpeningEnd = "", Events = "";
		public int OpeningStep, OpeningSteps, Reactions;
		public string[] KnobNames = Array.Empty<string>();
		public int[] Base = Array.Empty<int>();
		public int[] Now = Array.Empty<int>();
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Build-order knobs (DESIGN 19.2, AI_ARCHITECTURE 12.25): HOW and WHEN the base builder builds. Publishes eight bounded",
		"multipliers (tempo, greed, production, tech, defence, power_margin, expansion, support) and an opening through IBotBuildOrderKnobs;",
		"the shared base builder reads them only from an enabled provider. It never builds and never issues orders.",
		"Value = personality preset x learned (committed offline file) x per-match jitter, clamped to [KnobMin, KnobMax]; a fog-honest react layer",
		"multiplies it mid-match and decays back. FIXED POINT: every knob and factor is an integer in THOUSANDTHS (1000 = x1.0).")]
	public class BuildOrderKnobsBotModuleInfo : ConditionalTraitInfo
	{
		public static readonly string[] ReactionNames = { "air", "rush", "turtle", "out_earned" };

		static readonly string[] OpeningCategories =
		{
			BuildOrderCategory.Power, BuildOrderCategory.Refinery, BuildOrderCategory.Barracks, BuildOrderCategory.Factory,
			BuildOrderCategory.Production, BuildOrderCategory.Tech, BuildOrderCategory.Defence, BuildOrderCategory.Support,
			BuildOrderCategory.Superweapon
		};

		[Desc("Lowest value any knob may take, thousandths (preset x learned x jitter is clamped to [KnobMin, KnobMax]).")]
		public readonly int KnobMin = 600;

		[Desc("Highest value any knob may take, thousandths.")]
		public readonly int KnobMax = 1600;

		[Desc("Per-knob random jitter drawn ONCE per match from the host bot's random: +-JitterPct percent of the value.")]
		public readonly int JitterPct = 8;

		[Desc("Use the committed learned multipliers and opening posteriors (LearnedFile). False (default) = presets and jitter only.")]
		public readonly bool UseLearnedBuildOrder = false;

		[Desc("Mod-relative path of the file written by tools/ai/tune_build_order.py --write.")]
		public readonly string LearnedFile = "ai/learned/build_order_knobs.yaml";

		[Desc("Ticks between react evaluations.")]
		public readonly int ReactEvalTicks = 125;

		[Desc("How far per evaluation a react factor moves toward its target while a reaction holds, thousandths.")]
		public readonly int ReactStep = 100;

		[Desc("How fast a react factor decays back toward 1000 once no reaction pushes it, thousandths per game minute.")]
		public readonly int ReactDecayPerMinute = 150;

		[Desc("Bounds of a react factor, thousandths: the react layer can never move a knob by more than this.")]
		public readonly int ReactMin = 700;

		[Desc("Upper bound of a react factor, thousandths.")]
		public readonly int ReactMax = 1500;

		[Desc("Enemy air: the summed seen enemy air value at or above which the `air` reaction holds.")]
		public readonly int ReactAirValue = 600;

		[Desc("Rush: a reaction only before this tick.")]
		public readonly int ReactRushWindowTicks = 9000;

		[Desc("Rush: the summed seen enemy value near our base at or above which the `rush` reaction holds.")]
		public readonly int ReactRushPressureValue = 800;

		[Desc("Turtle: the seen enemy defence value at or above which the `turtle` reaction can hold.")]
		public readonly int ReactTurtleDefenceValue = 1500;

		[Desc("Turtle: and the defence must be at least this percent of the defence plus army value seen.")]
		public readonly int ReactTurtleDefenceSharePct = 40;

		[Desc("Out-earned: the seen economy proxy (harvesters + 2 x refineries) of the average scouted enemy must exceed ours by this percent (130 = 30% more).")]
		public readonly int ReactOutEarnPct = 130;

		[Desc("Out-earned: and be at least this many proxy points.")]
		public readonly int ReactOutEarnMinEconomy = 6;

		[Desc("The opening ends after this tick whatever it has built.")]
		public readonly int OpeningMaxTicks = 7500;

		[Desc("An opening step not satisfied after this many ticks is skipped (not buildable yet, or already present).")]
		public readonly int OpeningStepTimeoutTicks = 1500;

		[Desc("The opening is chosen once the personality is known, or after this tick whatever happens.")]
		public readonly int OpeningDecideTicks = 250;

		[FieldLoader.LoadUsing(nameof(LoadPresets))]
		[Desc("Personality -> knob -> value in thousandths (1250 = x1.25). A missing knob or personality is 1000.")]
		public readonly Dictionary<string, Dictionary<string, int>> Presets = [];

		[FieldLoader.LoadUsing(nameof(LoadOpenings))]
		[Desc("Opening name -> ordered building categories: power, refinery, barracks, factory, production (any), tech, defence, support, superweapon.")]
		public readonly Dictionary<string, string[]> Openings = [];

		[FieldLoader.LoadUsing(nameof(LoadOpeningWeights))]
		[Desc("Personality -> opening name -> preferred weight. A zero weight is never chosen; the weights tilt the bandit's draw.")]
		public readonly Dictionary<string, Dictionary<string, int>> OpeningWeights = [];

		[FieldLoader.LoadUsing(nameof(LoadReactTargets))]
		[Desc("Reaction (air, rush, turtle, out_earned) -> knob -> target react factor in thousandths.")]
		public readonly Dictionary<string, Dictionary<string, int>> ReactTargets = [];

		static Dictionary<string, Dictionary<string, int>> LoadNested(MiniYaml yaml, string key, Func<string, bool> validInner, string innerKind)
		{
			var result = new Dictionary<string, Dictionary<string, int>>(StringComparer.Ordinal);
			var node = yaml.NodeWithKeyOrDefault(key);
			if (node == null)
				return result;

			foreach (var outer in node.Value.Nodes)
			{
				var inner = new Dictionary<string, int>(StringComparer.Ordinal);
				foreach (var entry in outer.Value.Nodes)
				{
					if (!validInner(entry.Key))
						throw new YamlException($"BuildOrderKnobsBotModule: {key}.{outer.Key} names unknown {innerKind} '{entry.Key}'.");

					inner[entry.Key] = int.Parse(entry.Value.Value, CultureInfo.InvariantCulture);
				}

				result[outer.Key] = inner;
			}

			return result;
		}

		static bool IsKnob(string name) => Array.IndexOf(BuildOrderKnob.All, name) >= 0;

		static object LoadPresets(MiniYaml yaml) => LoadNested(yaml, "Presets", IsKnob, "knob");

		static object LoadReactTargets(MiniYaml yaml)
		{
			var result = LoadNested(yaml, "ReactTargets", IsKnob, "knob");
			foreach (var reaction in result.Keys)
				if (Array.IndexOf(ReactionNames, reaction) < 0)
					throw new YamlException($"BuildOrderKnobsBotModule: ReactTargets names unknown reaction '{reaction}'; known: {string.Join(", ", ReactionNames)}.");

			return result;
		}

		static object LoadOpeningWeights(MiniYaml yaml) => LoadNested(yaml, "OpeningWeights", _ => true, "opening");

		static object LoadOpenings(MiniYaml yaml)
		{
			var result = new Dictionary<string, string[]>(StringComparer.Ordinal);
			var node = yaml.NodeWithKeyOrDefault("Openings");
			if (node == null)
				return result;

			foreach (var opening in node.Value.Nodes)
			{
				var steps = opening.Value.Value.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
				foreach (var step in steps)
					if (Array.IndexOf(OpeningCategories, step) < 0)
						throw new YamlException($"BuildOrderKnobsBotModule: opening '{opening.Key}' names unknown category '{step}'; known: {string.Join(", ", OpeningCategories)}.");

				result[opening.Key] = steps;
			}

			return result;
		}

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (KnobMin > KnobMax || ReactMin > ReactMax)
				throw new YamlException("BuildOrderKnobsBotModule: KnobMin/ReactMin must not exceed KnobMax/ReactMax.");

			foreach (var personality in OpeningWeights)
				foreach (var opening in personality.Value.Keys)
					if (!Openings.ContainsKey(opening))
						throw new YamlException($"BuildOrderKnobsBotModule: OpeningWeights.{personality.Key} names opening '{opening}' that Openings does not define.");
		}

		public override object Create(ActorInitializer init) { return new BuildOrderKnobsBotModule(init.Self, this); }
	}

	public class BuildOrderKnobsBotModule : ConditionalTrait<BuildOrderKnobsBotModuleInfo>, IBotTick, IBotBuildOrderKnobs
	{
		static readonly string[] Knobs = BuildOrderKnob.All;

		readonly World world;
		readonly OpenRA.Player player;

		bool resolved;
		MasterAiBotModule master;
		BotPersonalityController personalityController;
		BaseBuilderBotModuleCA baseBuilder;
		IBotUnitRoles roles;
		IReadOnlyDictionary<string, HashSet<string>> tags;
		BuildOrderLearned learned = new();
		readonly Dictionary<string, string> categories = new(StringComparer.Ordinal);

		// Drawn once per match from the host's random: one jitter draw per knob, in Knobs order.
		int[] jitterDraws;
		string basePersonality;
		readonly int[] baseKnobs = new int[Knobs.Length];
		readonly int[] react = new int[Knobs.Length];
		readonly int[] now = new int[Knobs.Length];

		BuildOrderOpening opening;
		bool openingDecided;
		string enemyFaction = "";
		BuildOrderReaction active;
		int lastReactTick;
		int nextReactTick;
		readonly List<string> events = new();
		int ticksPerMinute = 1500;

		public BuildOrderSnapshot Snapshot { get; private set; }

		public BuildOrderKnobsBotModule(Actor self, BuildOrderKnobsBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			for (var i = 0; i < Knobs.Length; i++)
			{
				baseKnobs[i] = BuildOrderKnob.Neutral;
				react[i] = BuildOrderKnob.Neutral;
				now[i] = BuildOrderKnob.Neutral;
			}
		}

		bool IBotBuildOrderKnobs.Enabled => !IsTraitDisabled && resolved;

		int IBotBuildOrderKnobs.KnobMilli(string knob)
		{
			if (IsTraitDisabled || !resolved)
				return BuildOrderKnob.Neutral;

			var index = Array.IndexOf(Knobs, knob);
			return index < 0 ? BuildOrderKnob.Neutral : now[index];
		}

		string IBotBuildOrderKnobs.OpeningWanted => IsTraitDisabled || !resolved ? null : opening?.Wanted;

		string IBotBuildOrderKnobs.CategoryOf(string actorName)
		{
			if (!categories.TryGetValue(actorName, out var category))
				categories[actorName] = category = Classify(actorName);

			return category;
		}

		void IBotBuildOrderKnobs.NotifyQueued(string actorName)
		{
			if (IsTraitDisabled || !resolved || opening == null || !opening.Active)
				return;

			opening.NotifyQueued(((IBotBuildOrderKnobs)this).CategoryOf(actorName), world.WorldTick);
			if (!opening.Active)
				LogOpeningEnd(world.WorldTick);
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (IsTraitDisabled)
				return;

			var tick = world.WorldTick;
			if (!resolved)
				Resolve();

			var personality = personalityController?.CurrentPersonality ?? "";
			if (basePersonality == null || personality != basePersonality)
				RecomputeBase(personality);

			if (!openingDecided && (personality.Length > 0 || tick >= Info.OpeningDecideTicks))
				ChooseOpening(personality, tick);

			if (opening != null && opening.Active)
			{
				opening.Update(tick);
				if (!opening.Active)
					LogOpeningEnd(tick);
			}

			if (tick >= nextReactTick)
			{
				React(tick);
				nextReactTick = tick + Math.Max(1, Info.ReactEvalTicks);
			}
		}

		void Resolve()
		{
			var playerActor = player.PlayerActor;
			master = playerActor.TraitsImplementing<MasterAiBotModule>().FirstEnabledTraitOrDefault();
			personalityController = playerActor.TraitOrDefault<BotPersonalityController>();
			baseBuilder = playerActor.TraitsImplementing<BaseBuilderBotModuleCA>().FirstEnabledTraitOrDefault();
			roles = playerActor.TraitsImplementing<IBotUnitRoles>().FirstEnabledTraitOrDefault();
			tags = BotTargetTags.BuildTagMap(world.Map.Rules);
			ticksPerMinute = (int)(60000L / Math.Max(1, world.Timestep));

			// One jitter draw per knob and nothing else, in a fixed order, from the host's random.
			jitterDraws = new int[Knobs.Length];
			for (var i = 0; i < Knobs.Length; i++)
				jitterDraws[i] = world.LocalRandom.Next(0, 2001);

			if (Info.UseLearnedBuildOrder)
				LoadLearned();

			resolved = true;
		}

		void LoadLearned()
		{
			var fs = Game.ModData.DefaultFileSystem;
			if (!fs.Exists(Info.LearnedFile))
			{
				Log.Write("debug", $"AI {player.InternalName}: BO learned: {Info.LearnedFile} missing, everything neutral");
				return;
			}

			using (var stream = fs.Open(Info.LearnedFile))
				learned = BuildOrderLearned.Parse(MiniYaml.FromStream(stream, Info.LearnedFile));

			Log.Write("debug", $"AI {player.InternalName}: BO learned: {learned.ScopeCount} knob scopes, {learned.OpeningScopeCount} opening scopes");
		}

		/// <summary>The preset x learned x jitter vector for a personality. The jitter draws are kept, so a personality switch only re-reads the preset.</summary>
		void RecomputeBase(string personality)
		{
			basePersonality = personality;
			var faction = player.Faction?.InternalName ?? "";
			Info.Presets.TryGetValue(personality, out var preset);

			for (var i = 0; i < Knobs.Length; i++)
			{
				var presetMilli = preset != null && preset.TryGetValue(Knobs[i], out var p) ? p : BuildOrderKnob.Neutral;
				var learnedMilli = Info.UseLearnedBuildOrder ? learned.Multiplier(personality, faction, Knobs[i]) : BuildOrderKnob.Neutral;
				var jitter = BuildOrderKnobsEval.JitterMilli(Info.JitterPct, jitterDraws?[i] ?? 1000);
				baseKnobs[i] = BuildOrderKnobsEval.Combine(presetMilli, learnedMilli, jitter, Info.KnobMin, Info.KnobMax);
			}

			ApplyReact();
			Publish(world.WorldTick);
		}

		void ChooseOpening(string personality, int tick)
		{
			openingDecided = true;
			enemyFaction = EnemyFaction();
			if (!Info.OpeningWeights.TryGetValue(personality, out var weights) || weights.Count == 0)
				return;

			var faction = player.Faction?.InternalName ?? "";
			var name = BuildOrderKnobsEval.ChooseOpening(weights,
				o => Info.UseLearnedBuildOrder ? learned.Posterior(personality, faction, enemyFaction, o) : (1, 1),
				() => world.LocalRandom.NextFloat());
			if (name == null || !Info.Openings.TryGetValue(name, out var steps))
				return;

			opening = new BuildOrderOpening(name, steps, Info.OpeningMaxTicks, Info.OpeningStepTimeoutTicks, tick);
			events.Add($"{tick}:opening_{name}");
			Publish(tick);
		}

		void LogOpeningEnd(int tick)
		{
			events.Add($"{tick}:opening_end_{opening.EndReason}");
			Publish(tick);
		}

		// Player-level information only (the lobby faction of the main target, else the most common enemy faction), never actors.
		string EnemyFaction()
		{
			var main = player.PlayerActor.TraitsImplementing<IBotMainTargetProvider>()
				.Select(p => p.MainTarget).FirstOrDefault(t => t != null);
			if (main != null)
				return main.Faction?.InternalName ?? "";

			return world.Players
				.Where(p => p != player && !p.NonCombatant && !p.Spectating && player.RelationshipWith(p) == PlayerRelationship.Enemy)
				.GroupBy(p => p.Faction?.InternalName).Where(g => g.Key != null)
				.OrderByDescending(g => g.Count()).ThenBy(g => g.Key, StringComparer.Ordinal)
				.Select(g => g.Key).FirstOrDefault() ?? "";
		}

		void React(int tick)
		{
			var elapsed = Math.Max(0, tick - lastReactTick);
			lastReactTick = tick;

			var situation = master?.Situation;
			var reactions = BuildOrderReaction.None;
			if (situation?.Enemies != null)
			{
				var inputs = ReactInputs(situation, tick);
				reactions = BuildOrderKnobsEval.Evaluate(inputs, new BuildOrderReactThresholds(Info.ReactAirValue, Info.ReactRushWindowTicks,
					Info.ReactRushPressureValue, Info.ReactTurtleDefenceValue, Info.ReactTurtleDefenceSharePct, Info.ReactOutEarnPct,
					Info.ReactOutEarnMinEconomy));
			}

			var changed = reactions ^ active;
			if (changed != BuildOrderReaction.None)
			{
				foreach (var reaction in new[] { BuildOrderReaction.Air, BuildOrderReaction.Rush, BuildOrderReaction.Turtle, BuildOrderReaction.OutEarned })
					if ((changed & reaction) != 0)
						events.Add($"{tick}:{BuildOrderKnobsEval.ReactionName(reaction)}{((reactions & reaction) != 0 ? "+" : "-")}");

				// The rush rule abandons the opening: the plan assumed a peaceful start.
				if ((changed & reactions & BuildOrderReaction.Rush) != 0 && opening != null && opening.Active)
				{
					opening.Invalidate("react_rush");
					LogOpeningEnd(tick);
				}

				active = reactions;
			}

			for (var i = 0; i < Knobs.Length; i++)
			{
				var target = BuildOrderKnobsEval.CombinedTarget(Knobs[i], active, Info.ReactTargets);
				react[i] = BuildOrderKnobsEval.ReactStep(react[i], target, Info.ReactStep, Info.ReactDecayPerMinute, elapsed,
					ticksPerMinute, Info.ReactMin, Info.ReactMax);
			}

			ApplyReact();
			Publish(tick);
		}

		// What the bot SAW, from the published snapshot: the personality-lead inputs (BotSituation enemy profiles, the same
		// economy proxy as the Expansion lead). Air/pressure/defence/army are summed over living enemies; the economy is the MEAN
		// over living enemies with an observed economy (so out_earned does not depend on the player count). Own side is the bot's own state.
		BuildOrderReactInputs ReactInputs(BotSituation situation, int tick)
		{
			int air = 0, pressure = 0, defence = 0, army = 0;
			var enemyEconomies = new List<int>();
			foreach (var enemy in situation.Enemies.Values)
			{
				if (!enemy.Alive)
					continue;

				air += enemy.AirValue;
				pressure += enemy.PressureValue;
				defence += enemy.DefenceValue;
				army += enemy.ArmyValue;
				enemyEconomies.Add(enemy.Harvesters + enemy.Refineries * 2);
			}

			var ownRefineries = baseBuilder?.RefineryBuildings.Actors.Count(a => !a.IsDead) ?? 0;
			return new BuildOrderReactInputs(tick, air, pressure, defence, army, BuildOrderKnobsEval.EnemyEconomyPerEnemy(enemyEconomies), situation.OwnHarvesters + ownRefineries * 2);
		}

		void ApplyReact()
		{
			for (var i = 0; i < Knobs.Length; i++)
				now[i] = BuildOrderKnobsEval.Clamp((int)((long)baseKnobs[i] * react[i] / BuildOrderKnob.Neutral), Info.KnobMin, Info.KnobMax);
		}

		void Publish(int tick)
		{
			if (events.Count > 60)
				events.RemoveRange(0, events.Count - 60);

			Snapshot = new BuildOrderSnapshot
			{
				Tick = tick,
				Personality = basePersonality ?? "",
				Faction = player.Faction?.InternalName ?? "",
				EnemyFaction = enemyFaction,
				Opening = opening?.Name ?? "",
				OpeningEnd = opening?.EndReason ?? "",
				OpeningStep = opening?.StepIndex ?? 0,
				OpeningSteps = opening?.StepCount ?? 0,
				Reactions = (int)active,
				Events = string.Join(";", events),
				KnobNames = Knobs,
				Base = (int[])baseKnobs.Clone(),
				Now = (int[])now.Clone()
			};
		}

		/// <summary>
		/// The category of a building, from the rules: the base builder's own type lists first (they are the ruleset's intent for
		/// power, refinery, production and defence), then rules-derived tags and roles. No actor id is typed here.
		/// </summary>
		string Classify(string name)
		{
			var info = baseBuilder?.Info;
			if (info != null)
			{
				if (info.ConstructionYardTypes.Contains(name))
					return BuildOrderCategory.Conyard;
				if (info.PowerTypes.Contains(name))
					return BuildOrderCategory.Power;
				if (info.RefineryTypes.Contains(name))
					return BuildOrderCategory.Refinery;
				if (info.BarracksTypes.Contains(name))
					return BuildOrderCategory.Barracks;
				if (info.VehiclesFactoryTypes.Contains(name))
					return BuildOrderCategory.Factory;
				if (info.ProductionTypes.Contains(name) || info.NavalProductionTypes.Contains(name))
					return BuildOrderCategory.Production;
				if (info.AntiAirTypes.Contains(name) || info.DefenseTypes.Contains(name))
					return BuildOrderCategory.Defence;
			}

			HashSet<string> set = null;
			tags?.TryGetValue(name, out set);
			set ??= new HashSet<string>();

			if (set.Contains(BotTargetTags.Superweapon))
				return BuildOrderCategory.Superweapon;
			if (set.Contains(BotTargetTags.Conyard))
				return BuildOrderCategory.Conyard;
			if (set.Contains(BotTargetTags.Power))
				return BuildOrderCategory.Power;
			if (set.Contains(BotTargetTags.Refinery))
				return BuildOrderCategory.Refinery;

			if (world.Map.Rules.Actors.TryGetValue(name, out var actorInfo)
				&& (actorInfo.HasTraitInfo<ProvidesRadarInfo>() || actorInfo.HasTraitInfo<RepairsUnitsInfo>()))
				return BuildOrderCategory.Support;

			if (set.Contains(BotTargetTags.Defence))
				return BuildOrderCategory.Defence;
			if (set.Contains(BotTargetTags.Production))
				return BuildOrderCategory.Production;
			if (roles != null && roles.ActorRoles.TryGetValue(name, out var roleSet) && roleSet.Contains(BotUnitRole.Tech))
				return BuildOrderCategory.Tech;

			return BuildOrderCategory.Other;
		}
	}
}
