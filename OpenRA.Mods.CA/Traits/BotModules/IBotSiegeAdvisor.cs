#region Copyright & License Information
/*
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using OpenRA.Mods.CA.Traits.BotModules.Squads;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>What a siege advisor wants an advancing ground assault squad to do this tick.</summary>
	public enum SiegeVerdict
	{
		/// <summary>No objection — the normal advance/engage path runs.</summary>
		Advance,

		/// <summary>Hold at <c>standOffCell</c> (max remembered defence range + margin) while artillery works.</summary>
		StandOff,

		/// <summary>Pull out — the projected trade loses (§12.6 rule 5).</summary>
		Retreat,
	}

	/// <summary>
	/// CA-2 siege advisor (AI_ARCHITECTURE §12.6): supplies the
	/// stand-off / commit / retreat verdict for ground assault squads.
	/// Implemented by the module that reads remembered defences; the squad
	/// state machine stays the single order authority and only consults this.
	/// An absent or disabled advisor means <see cref="SiegeVerdict.Advance"/> —
	/// identical to no advisor at all.
	/// </summary>
	public interface IBotSiegeAdvisor
	{
		/// <summary>
		/// Per-tick verdict for one assault squad. Called every AttackMove tick —
		/// implementations must be cheap (cache the evaluation, serve lookups).
		/// <paramref name="standOffCell"/> is valid only for <see cref="SiegeVerdict.StandOff"/>.
		/// </summary>
		SiegeVerdict VerdictFor(SquadCA squad, out CPos standOffCell);
	}
}
