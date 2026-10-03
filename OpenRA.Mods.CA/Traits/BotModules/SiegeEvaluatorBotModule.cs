#region Copyright & License Information
/*
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits.BotModules.Squads;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;
using OpenRA;

namespace OpenRA.Mods.CA.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("CA-2a siege telemetry (AI_ARCHITECTURE §12.6): every EvaluationInterval ticks, logs what",
		"stand-off / artillery-first / commit / retreat WOULD have decided for each ground assault",
		"squad, from fog-honest remembered defences and regional threat. Issues no orders — the",
		"behaviour lands in CA-2b behind a switch, after this telemetry validates the inputs.")]
	public class SiegeEvaluatorBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("World ticks between evaluation passes.")]
		public readonly int EvaluationInterval = 100;

		[Desc("Cells of safety margin added to the longest remembered defence range when computing the stand-off line (DESIGN §19.1 equal-step margin placeholder until per-difficulty margins land).")]
		public readonly int StandOffMarginCells = 2;

		[Desc("Remembered defence this close to the squad's target (cells) counts as covering the approach.")]
		public readonly int RelevantDefenceRadiusCells = 24;

		[Desc("Commit when the squad's summed unit value reaches this percent of the remembered defence+army value around the target (rule 4's R, x100). Personality moves this later.")]
		public readonly int CommitRatioPercent = 150;

		[Desc("Minimum summed squad unit value worth evaluating — empty or token squads are noise.")]
		public readonly int MinimumSquadValue = 500;

		[Desc("CA-2b: feed the verdict back to assault squads through IBotSiegeAdvisor (stand-off / retreat). False = telemetry only.")]
		public readonly bool BehaviourEnabled = false;

		[Desc("CA-2c (§12.6 rule 5): a retreat verdict writes a failed-siege memory into the target",
			"region and remembered failures inflate the obstacle value on later evaluations,",
			"so the next plan avoids the wall that beat it. False = verdicts compute against",
			"raw memory only (control-arm identical).")]
		public readonly bool SiegeMemoryEnabled = false;

		public override object Create(ActorInitializer init) => new SiegeEvaluatorBotModule(init.Self, this);
	}

	public class SiegeEvaluatorBotModule : ConditionalTrait<SiegeEvaluatorBotModuleInfo>, IBotTick, IBotSiegeAdvisor
	{
		readonly World world;
		readonly Player player;
		SquadManagerBotModuleCA[] squadManagers;
		IBotRegionThreatProvider[] threatProviders;
		IBotRememberedDefenceProvider[] defenceProviders;
		IBotSiegeFailureMemory[] failureMemory;
		readonly Dictionary<SquadCA, (SiegeVerdict Verdict, CPos StandOff)> verdicts = new();
		readonly Dictionary<SquadCA, SiegeVerdict> lastVerdictBySquad = new();
		int lastEvaluationTick = -1;

		public SiegeEvaluatorBotModule(Actor self, SiegeEvaluatorBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (IsTraitDisabled || world.WorldTick == lastEvaluationTick ||
				world.WorldTick % Info.EvaluationInterval != player.ClientIndex % Info.EvaluationInterval)
				return;
			lastEvaluationTick = world.WorldTick;

			// Personality-named squad managers (@rush/@turtle/…) enable only after
			// the personality latch and re-latch on switch — never cache an empty
			// or stale set (the first pass predates the latch).
			if (squadManagers == null || squadManagers.Length == 0 || squadManagers.Any(t => t.IsTraitDisabled))
				squadManagers = player.PlayerActor.TraitsImplementing<SquadManagerBotModuleCA>()
					.Where(t => !t.IsTraitDisabled).ToArray();
			threatProviders ??= player.PlayerActor.TraitsImplementing<IBotRegionThreatProvider>().ToArray();
			defenceProviders ??= player.PlayerActor.TraitsImplementing<IBotRememberedDefenceProvider>().ToArray();
			failureMemory ??= player.PlayerActor.TraitsImplementing<IBotSiegeFailureMemory>().ToArray();
			if (squadManagers.Length == 0 || defenceProviders.Length == 0)
				return;

			var defences = defenceProviders.SelectMany(p => p.RememberedDefences()).ToArray();
			var rules = world.Map.Rules;
			verdicts.Clear();
			var evaluated = 0;

			foreach (var squad in squadManagers.SelectMany(m => m.Squads))
			{
				if (!squad.IsValid || squad.Units.Count == 0 ||
					(squad.Type != SquadCAType.Rush && squad.Type != SquadCAType.Guerrilla && squad.Type != SquadCAType.Harass))
					continue;

				var squadValue = squad.Units.Sum(u => u.Actor?.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0);
				if (squadValue < Info.MinimumSquadValue)
					continue;

				evaluated++;

				var target = squad.Target;
				if (target.Type == TargetType.Invalid)
					continue;

				var targetCell = world.Map.CellContaining(target.CenterPosition);
				var squadCell = world.Map.CellContaining(squad.CenterPosition);

				var radiusSq = (long)Info.RelevantDefenceRadiusCells * Info.RelevantDefenceRadiusCells;
				var covering = defences
					.Where(d => (d.Cell - targetCell).LengthSquared <= radiusSq)
					.ToArray();

				var rememberedThreat = threatProviders.Sum(p => p.RememberedEnemyThreatAt(targetCell));
				var defenceValue = covering.Sum(d => d.Value);

				// CA-2c: regions that already beat a siege read heavier — the
				// next plan avoids the wall (§12.6 rule 5, "the next plan avoids it").
				var siegeMem = 100;
				if (Info.SiegeMemoryEnabled && failureMemory.Length > 0)
					siegeMem = failureMemory.Sum(p => p.FailedSiegeWeightPercentAt(targetCell, world.WorldTick));
				var obstacleValue = (defenceValue + rememberedThreat) * siegeMem / 100;

				// §12.6 rule order: hold at stand-off -> artillery works the defences ->
				// commit on cleared area or overwhelming effective value -> retreat on loss.
				// "Effective" is Versus-weighted: BotCombatPredictor.Predict with the
				// remembered defences as the enemy set — one engagement authority.
				string verdict;
				var standOffCells = 0;
				var verdictKind = SiegeVerdict.Advance;
				var standOffCell = CPos.Zero;
				if (covering.Length == 0)
					verdict = obstacleValue > 0 ? "commit-no-defences(army-covered)" : "free-advance";
				else
				{
					var own = squad.Units.Where(u => u.Actor != null)
						.GroupBy(u => u.Actor.Info)
						.Select(g => (BotUnitProfiles.Get(rules, g.Key), g.Count()))
						.ToList();
					var enemy = covering.GroupBy(d => d.Observed)
						.Select(g => (BotUnitProfiles.Get(rules, g.Key), g.Count()))
						.ToList();
					var prediction = BotCombatPredictor.Predict(own, enemy);

					standOffCells = covering.Max(d => d.MaxRangeCells) + Info.StandOffMarginCells;
					var standOffSq = (long)standOffCells * standOffCells;
					var nearest = covering.Aggregate((a, b) =>
						(a.Cell - squadCell).LengthSquared <= (b.Cell - squadCell).LengthSquared ? a : b);
					var distToNearestDefenceSq = (nearest.Cell - squadCell).LengthSquared;
					var insideLine = distToNearestDefenceSq <= standOffSq;
					var committed = prediction.OwnWins &&
						(long)squadValue * 100 >= (long)Info.CommitRatioPercent * obstacleValue;

					// The hold point sits on the stand-off line, on the defence->squad bearing.
					if (!committed)
					{
						var delta = squadCell - nearest.Cell;
						var distCells = (int)Math.Sqrt((double)distToNearestDefenceSq);
						var hx = distCells >= standOffCells ? squadCell.X
							: nearest.Cell.X + (int)((long)delta.X * standOffCells / Math.Max(1, distCells));
						var hy = distCells >= standOffCells ? squadCell.Y
							: nearest.Cell.Y + (int)((long)delta.Y * standOffCells / Math.Max(1, distCells));
						standOffCell = new CPos(hx, hy);
					}

					if (committed)
					{
						verdict = insideLine ? "overrun-line(commit anyway)" : "commit";
					}
					else if (!prediction.OwnWins)
					{
						verdict = "retreat(predicted-loss)";
						verdictKind = SiegeVerdict.Retreat;

						// The failed siege writes the loss into the wall's region
						// memory — once per retreat transition, not per pass spent
						// pinned (a standing-off squad does not stack the count).
						if (Info.SiegeMemoryEnabled &&
							(!lastVerdictBySquad.TryGetValue(squad, out var prev) || prev != SiegeVerdict.Retreat))
							foreach (var p in failureMemory)
								p.RecordFailedSiege(nearest.Enemy, nearest.Cell, world.WorldTick);
					}
					else
					{
						verdict = insideLine ? "inside-defence-range(HOLD-FAIL)" : "stand-off";
						verdictKind = SiegeVerdict.StandOff;
					}
				}

				verdicts[squad] = (verdictKind, standOffCell);
				lastVerdictBySquad[squad] = verdictKind;

				var artilleryAttached = squadManagers.Any(m => m.Squads.Any(s =>
					s.IsValid && s.Type == SquadCAType.Artillery && s.Parent == squad && s.Units.Count > 0));
				// Log.Write direct: AIUtils.BotDebug is gated on Game.Settings.Debug.BotDebug,
				// which the match harness does not set — the FransBotLog pattern.
				Log.Write("debug", string.Format("[SIEGE-EVAL][WT {0}] AI {1} {2} squad v={3} units={4} at {5} -> {6}: defences={7} v={8} maxRange={9} threat={10} verdict={11} artillery={12} siegeMem={13}",
					world.WorldTick, player.ClientIndex, squad.Type, squadValue, squad.Units.Count, squadCell, targetCell,
					covering.Length, defenceValue, standOffCells, rememberedThreat, verdict,
					artilleryAttached ? "attached" : "none", siegeMem));
			}

			// Drop transition entries for squads that left evaluation (dissolved
			// or below value floor) — the dict must not grow with squad churn.
			foreach (var stale in lastVerdictBySquad.Keys.Where(k => !verdicts.ContainsKey(k)).ToArray())
				lastVerdictBySquad.Remove(stale);

			// Heartbeat: distinguishes "module silent" from "no assault squads
			// qualified" — a whole batch of silence means formation starves.
			Log.Write("debug", string.Format("[SIEGE-EVAL][WT {0}] AI {1} pass: squads={2} evaluated={3} defences={4}",
				world.WorldTick, player.ClientIndex,
				squadManagers.Sum(m => m.Squads.Count(s => s.IsValid)), evaluated, defences.Length));
		}

		// IBotSiegeAdvisor — serves the cached evaluation. Disabled or stale
		// answers Advance so the state machine behaves exactly as without the
		// module (CA-2b switch: BehaviourEnabled).
		public SiegeVerdict VerdictFor(SquadCA squad, out CPos standOffCell)
		{
			standOffCell = CPos.Zero;
			if (IsTraitDisabled || !Info.BehaviourEnabled ||
				!verdicts.TryGetValue(squad, out var cached))
				return SiegeVerdict.Advance;

			standOffCell = cached.StandOff;
			return cached.Verdict;
		}
	}
}
