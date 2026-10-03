#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// PL-1 (docs/design/AI_ARCHITECTURE.md §12.14): the personality-lead budget
	/// lean. Implemented by master-AI modules that compute the fog-honest leads on
	/// their situation snapshot; consumers (unit builder, squad manager) read the
	/// published multiplier and never re-derive the lead themselves.
	/// </summary>
	public interface IBotPersonalityLeadProvider
	{
		/// <summary>
		/// The budget-lean multiplier for <paramref name="personality"/> ("steamroller",
		/// "rush"): a value in (0, 1] read off the latest situation snapshot.
		/// 1.0 — no lean — whenever the provider is disabled, the leads switch
		/// (UsePersonalityLeads) is off, this bot runs a different personality, no
		/// snapshot exists yet, or the lead is at/above target. While the lead trails
		/// the multiplier drops toward 1 - PersonalityLeadMaxLeanPercent/100, linear
		/// in the deficit — trailing consumers move their knob toward more budget,
		/// never past it.
		/// </summary>
		double PersonalityLeadLean(string personality);
	}

	/// <summary>
	/// Shared consumer math for <see cref="IBotPersonalityLeadProvider"/>: take the
	/// strongest (lowest) lean any provider reports, then scale a knob by it.
	/// </summary>
	public static class BotPersonalityLeads
	{
		/// <summary>Lowest lean multiplier across the providers; 1.0 when none answer.</summary>
		public static double Lean(IEnumerable<IBotPersonalityLeadProvider> providers, string personality)
		{
			var lean = 1.0;
			if (providers == null)
				return lean;

			foreach (var provider in providers)
				if (provider != null)
					lean = System.Math.Min(lean, provider.PersonalityLeadLean(personality));

			return lean;
		}

		/// <summary>The leaned knob: baseValue x lean while trailing, baseValue untouched at lean &gt;= 1.</summary>
		public static int Scaled(int baseValue, double lean)
		{
			return lean >= 1.0 ? baseValue : System.Math.Max(0, (int)(baseValue * lean));
		}
	}
}
