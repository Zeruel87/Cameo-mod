#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// The defence-role names a threat analysis reports, matched to the
	/// <c>demand.*</c> prerequisite suffixes (<c>demand.antiair</c>,
	/// <c>demand.antiarmour</c>, <c>demand.antiinfantry</c>) so a consumer can
	/// feed threat straight into demand or target scoring without re-mapping.
	/// </summary>
	public static class BotThreatRoles
	{
		public const string AntiAir = "antiair";
		public const string AntiArmour = "antiarmour";
		public const string AntiInfantry = "antiinfantry";
	}

	/// <summary>
	/// How hard the enemy is pressing us, per defence role, learned from being
	/// attacked — the pairwise-attribution (<c>w_hurt</c>) producer that
	/// AI_ARCHITECTURE.md §4.3 reserves for target scoring. Fog-honest by
	/// construction: it is fed by <c>IBotRespondToAttack</c>, not by observation.
	/// Implemented by <c>CombatAnalysisBotModule</c>, which lives in
	/// OpenRA.Mods.Cameo and must not be referenced by name from this assembly.
	/// </summary>
	public interface IBotThreatAnalysis
	{
		/// <summary>Current decayed weight for a <see cref="BotThreatRoles"/> role; 0 for unknown roles.</summary>
		float GetThreatWeight(string role);

		/// <summary>True while any role's weight is at or above its react threshold.</summary>
		bool HasActiveThreat();

		/// <summary>
		/// How hard a role is pressed, ramping from 0 at the react threshold to 1 at
		/// <paramref name="saturationFactor"/> times the threshold. 0 while not an active threat.
		/// </summary>
		float GetThreatIntensity(string role, float saturationFactor);

		/// <summary>Highest-weighted role at or above the react threshold, or null when none.</summary>
		string GetHighestThreatRole();

		/// <summary>The enemy player who has attacked us (or our allies) the most, or null below threshold.</summary>
		Player GetNemesis();

		/// <summary>
		/// Nemesis score for a specific enemy player — the 'damage that player has dealt
		/// to us' side of §4.3's w_hurt term. 0 for players that have never hit us.
		/// </summary>
		float GetNemesisScore(Player attacker);

		/// <summary>
		/// Dealt score for a specific enemy player — the 'damage we have dealt to that
		/// player' side of §4.3's w_hurt term, fed by <c>INotifyAppliedDamage</c> on the
		/// attacker's player actor. 0 for players we have never damaged.
		/// </summary>
		float GetDealtScore(Player victim);

		/// <summary>Record that an enemy player attacked an ally of ours (not us directly).</summary>
		void RegisterAllyAttack(Player attacker);
	}
}
