#region Copyright & License Information
/*
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// CA-2c (AI_ARCHITECTURE §12.6 rule 5): a failed siege writes the loss into
	/// the region memory so the next plan avoids it. The store is keyed by
	/// (enemy, region index) and survives BotSituation publishes — RegionMemory
	/// itself is rebuilt per pass, so the durable count lives on the provider.
	/// </summary>
	public interface IBotSiegeFailureMemory
	{
		/// <summary>Record one failed siege against the region containing <paramref name="cell"/>.</summary>
		void RecordFailedSiege(OpenRA.Player enemy, CPos cell, int tick);

		/// <summary>
		/// Threat multiplier in percent (100 = no memory) for the remembered
		/// failures recorded against the region containing <paramref name="cell"/>.
		/// Entries older than the provider's memory window contribute nothing.
		/// </summary>
		int FailedSiegeWeightPercentAt(CPos cell, int tick);
	}
}
