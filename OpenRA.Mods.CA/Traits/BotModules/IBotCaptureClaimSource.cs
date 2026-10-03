#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// TC-2e (AI_ARCHITECTURE.md §12.17): the publish end of capture-claim
	/// arbitration. A bot module that is actively working a capture or contest
	/// target (an engineer walking at a capturable, infantry claiming a
	/// garrisonable) exposes the positions it holds so the situation snapshot can
	/// carry them to the team blackboard as <see cref="TeamBroadcast.CaptureClaims"/>.
	/// Fog-honest: every position is a target the publishing bot itself chose —
	/// own-side intent, never an enumeration of enemies. Consumers read the union
	/// through <see cref="TeamBlackboard.ClaimsAheadOf"/>; the lower
	/// <see cref="TeamBroadcast.ClientIndex"/> claimant keeps its claim.
	/// </summary>
	public interface IBotCaptureClaimSource
	{
		/// <summary>The positions (map cell centers, Map.CenterOfCell) of capture/contest targets this bot is actively working on.</summary>
		IReadOnlyList<WPos> CaptureClaimPositions { get; }
	}
}
