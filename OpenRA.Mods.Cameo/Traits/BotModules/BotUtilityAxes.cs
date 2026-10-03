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
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// UT-1 (AI_DEEP_RESEARCH.md §5.1): one snapshot's raw inputs for the utility axes.
	/// Every field already sits on BotSituation or is derived from the same fog-honest
	/// data — enemy values are remembered sightings under fog, own values are always
	/// visible. All zeros is a valid "nothing seen, nothing lost" sample.
	/// </summary>
	internal sealed class UtilityAxisSample
	{
		/// <summary>CP predictor x100 vs the remembered enemy army plus defences; 100 = coin flip, above = predicted win.</summary>
		public int CombatRatioDefendedPct;

		/// <summary>Remembered enemy army value (cost). 0 gates the win/loss terms — no contact is no evidence.</summary>
		public int EnemyArmyValue;

		/// <summary>Remembered enemy combat value within PressureRadius of an own building (cost).</summary>
		public int EnemyPressureValue;

		/// <summary>Remembered enemy static-defence value, summed over enemies (cost).</summary>
		public int EnemyDefenceValue;

		/// <summary>Remembered enemy base/refinery building clusters, summed over alive enemies.</summary>
		public int EnemyExpansionClusters;

		/// <summary>Army-value-weighted mean of the enemies' StealthShare (0-100).</summary>
		public int EnemyStealthShare;

		/// <summary>Own harvesters + 2x refineries — the EconProxy shape; the own side is never fogged.</summary>
		public int OwnEconomy;

		/// <summary>Own base/refinery building clusters — the own-side symmetric of EnemyExpansionClusters.</summary>
		public int OwnExpansionClusters;

		/// <summary>Cost of own units lost inside the master's LossWindowTicks.</summary>
		public int OwnDeathsCostWindow;

		/// <summary>Cost of enemy units destroyed inside the same window.</summary>
		public int OwnKillsCostWindow;
	}

	/// <summary>
	/// UT-1 (AI_DEEP_RESEARCH.md §5.1): the strategist's bipolar posture axes —
	/// Turtle↔Rush, TechRush↔Expansion, Steamroller↔Guerrilla — each in [0,100]
	/// with 100 the SECOND-named pole.
	///
	/// Every snapshot recomputes a TARGET per axis:
	///   target = clamp(rest[personality] + terms * UtilityInputWeightPercent / 100)
	/// and EMA-steps the published axis toward it by UtilityAxisDecayPercent
	/// (the integer step floors at one point, so a target is always reached).
	/// Inputs gone quiet ⇒ target = rest ⇒ the axis decays to its personality's
	/// resting value; a personality switch moves the rest, not the axis. The first
	/// observation parks each axis ON its rest — a personality is a starting point.
	///
	/// Term units: each raw input is first squashed to 0-100 by
	/// MasterAiBotModule.Saturate (k = the raw value reaching half the cap) or
	/// HurtShare, then contributes at most its CAP in axis points — no single term
	/// can dominate whatever the raw magnitude.
	/// </summary>
	public sealed class BotUtilityAxes
	{
		// TurtleRush term caps (axis points): winning → Rush; pressure, losses and a
		// fortified enemy → Turtle.
		const int WinTermCap = 25;        // CombatRatioDefendedPct above the 100 par; k=300
		const int LosingTermCap = 15;     // below par; k=100
		const int HomePressureCap = 25;   // EnemyPressureValue; k=1500 cost
		const int OwnLossesCap = 20;      // OwnDeathsCostWindow; k=EmergencyLossThreshold
		const int EnemyDefenceCap = 15;   // EnemyDefenceValue; k=2000 cost

		// TechRushExpansion term caps: enemy sprawl lead and economy headroom →
		// Expansion; pressure at home → TechRush.
		const int EnemySprawlLeadCap = 20;  // EnemyExpansionClusters - OwnExpansionClusters; k=3 clusters
		const int EconomyHeadroomCap = 15;  // OwnEconomy; k=6 (harvesters + 2x refineries)

		// SteamrollerGuerrilla term caps: losing the exchange, a sprawling enemy and
		// enemy stealth → Guerrilla; winning the exchange → Steamroller.
		const int TradeBalanceCap = 25;   // HurtShare(deaths, kills) off the 50 midpoint; k=50
		const int EnemySprawlCap = 20;    // EnemyExpansionClusters; k=4 clusters
		const int EnemyStealthCap = 15;   // EnemyStealthShare, already 0-100

		public int TurtleRush { get; private set; } = IBotUtilityAxes.Neutral;
		public int TechRushExpansion { get; private set; } = IBotUtilityAxes.Neutral;
		public int SteamrollerGuerrilla { get; private set; } = IBotUtilityAxes.Neutral;
		bool started;

		internal void Observe(UtilityAxisSample s, string personality, MasterAiBotModuleInfo info,
			int techRushExpansionBias = 0)
		{
			var turtleRushRest = Rest(info.UtilityTurtleRushRest, personality);
			// TC-2d: role split moves the EFFECTIVE rest — the axis parks on it at start and
			// decays back to it once inputs quieten, exactly as an authored rest does.
			var techRushExpansionRest = Math.Clamp(
				Rest(info.UtilityTechRushExpansionRest, personality) + techRushExpansionBias, 0, 100);
			var steamrollerGuerrillaRest = Rest(info.UtilitySteamrollerGuerrillaRest, personality);
			if (!started)
			{
				started = true;
				TurtleRush = turtleRushRest;
				TechRushExpansion = techRushExpansionRest;
				SteamrollerGuerrilla = steamrollerGuerrillaRest;
			}

			var weight = info.UtilityInputWeightPercent;
			var decay = info.UtilityAxisDecayPercent;
			TurtleRush = Step(TurtleRush, Target(turtleRushRest, TurtleRushTerms(s, info), weight), decay);
			TechRushExpansion = Step(TechRushExpansion, Target(techRushExpansionRest, TechRushExpansionTerms(s), weight), decay);
			SteamrollerGuerrilla = Step(SteamrollerGuerrilla, Target(steamrollerGuerrillaRest, SteamrollerGuerrillaTerms(s), weight), decay);
		}

		internal static int Rest(IReadOnlyDictionary<string, int> rests, string personality)
		{
			return !string.IsNullOrEmpty(personality) && rests != null &&
				rests.TryGetValue(personality, out var rest)
					? Math.Clamp(rest, 0, 100)
					: IBotUtilityAxes.Neutral;
		}

		internal static int Target(int rest, int terms, int weightPercent)
		{
			return Math.Clamp(rest + terms * Math.Clamp(weightPercent, 0, 100) / 100, 0, 100);
		}

		internal static int Step(int axis, int target, int decayPercent)
		{
			if (axis == target || decayPercent <= 0)
				return axis;

			var delta = (target - axis) * Math.Min(decayPercent, 100) / 100;
			if (delta == 0)
				delta = target > axis ? 1 : -1;
			return Math.Clamp(axis + delta, 0, 100);
		}

		internal static int TurtleRushTerms(UtilityAxisSample s, MasterAiBotModuleInfo info)
		{
			var terms = 0;
			if (s.EnemyArmyValue > 0)
			{
				terms += WinTermCap * MasterAiBotModule.Saturate(s.CombatRatioDefendedPct - 100, 300) / 100;
				terms -= LosingTermCap * MasterAiBotModule.Saturate(100 - s.CombatRatioDefendedPct, 100) / 100;
			}

			terms -= HomePressureCap * MasterAiBotModule.Saturate(s.EnemyPressureValue, 1500) / 100;
			terms -= OwnLossesCap * MasterAiBotModule.Saturate(s.OwnDeathsCostWindow, Math.Max(1, info.EmergencyLossThreshold)) / 100;
			terms -= EnemyDefenceCap * MasterAiBotModule.Saturate(s.EnemyDefenceValue, 2000) / 100;
			return terms;
		}

		internal static int TechRushExpansionTerms(UtilityAxisSample s)
		{
			var terms = EnemySprawlLeadCap * MasterAiBotModule.Saturate(s.EnemyExpansionClusters - s.OwnExpansionClusters, 3) / 100;
			terms += EconomyHeadroomCap * MasterAiBotModule.Saturate(s.OwnEconomy, 6) / 100;
			terms -= HomePressureCap * MasterAiBotModule.Saturate(s.EnemyPressureValue, 1500) / 100;
			return terms;
		}

		internal static int SteamrollerGuerrillaTerms(UtilityAxisSample s)
		{
			var terms = 0;
			if (s.OwnKillsCostWindow + s.OwnDeathsCostWindow > 0)
			{
				// The bounded share form of the trade: our part of the window's total
				// losses. Losing the exchange (above 50) pushes toward Guerrilla —
				// stop trading head-on; winning pulls toward Steamroller.
				var lostShare = MasterAiBotModule.HurtShare(s.OwnDeathsCostWindow, s.OwnKillsCostWindow);
				terms += lostShare >= 50
					? TradeBalanceCap * MasterAiBotModule.Saturate(lostShare - 50, 50) / 100
					: -TradeBalanceCap * MasterAiBotModule.Saturate(50 - lostShare, 50) / 100;
			}

			terms += EnemySprawlCap * MasterAiBotModule.Saturate(s.EnemyExpansionClusters, 4) / 100;
			terms += EnemyStealthCap * Math.Clamp(s.EnemyStealthShare, 0, 100) / 100;
			return terms;
		}
	}
}
