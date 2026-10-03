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
	/// DI-1 (AI_DEEP_RESEARCH.md §7, DESIGN.md §19.2): the pacing Director's wave
	/// phase. BuildUp — tension accumulates while an army idles; Pressure — an
	/// attack is overdue, the army is massed; Climax — the attack is delivering;
	/// Relief — the wave broke, tension resets until the next build-up.
	/// </summary>
	public enum DirectorPhase { BuildUp, Pressure, Climax, Relief }

	/// <summary>
	/// DI-1 (AI_ARCHITECTURE.md §12.16): the fog-honest pacing Director's published
	/// telemetry — a tension value in [0,100] and the wave phase it puts the bot in.
	/// Publish-only: nothing consumes it yet; DI-2 adds the attack-timing consumer.
	/// Pacing and aggression telemetry only — it never touches income, unit stats or
	/// vision (DESIGN §19.2). Providers live in OpenRA.Mods.Cameo and must not be
	/// referenced by name from this assembly; absent or disabled providers read as a
	/// fresh wave (0 tension, BuildUp) — never a behaviour change.
	/// </summary>
	public interface IBotDirector
	{
		/// <summary>Current tension in [0,100] — how overdue the next attack wave is.</summary>
		int DirectorTension { get; }

		/// <summary>Current wave phase.</summary>
		DirectorPhase DirectorPhase { get; }
	}
}
