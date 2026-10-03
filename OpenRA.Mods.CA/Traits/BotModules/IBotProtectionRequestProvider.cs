#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License,
 * either version 3 of the License, or (at your option) any later version.
 * For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// A standing guard job - e.g. an MCV driving to an expansion site or an outpost that needs
	/// a screen. The publisher re-emits the request while the job is live (short ExpiresTick);
	/// the squad manager releases the escort when no live request covers it any more. `Value`
	/// uses the same army_value scale as situation/army telemetry.
	/// </summary>
	public readonly record struct BotProtectionRequest(CPos Location, int Value, int ExpiresTick);

	/// <summary>Published by modules that need a guard somewhere (expansion MCVs, outposts); read by the squad manager.</summary>
	public interface IBotProtectionRequestProvider
	{
		IReadOnlyList<BotProtectionRequest> ProtectionRequests { get; }
	}
}
