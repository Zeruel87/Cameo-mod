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
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// ENG-T (maintainer 2026-09-30): an infiltration RUN — one transport (APC, transport helicopter) carries 1-5 capturers
	/// into the enemy base along a route around the enemy army and defences and visits several buildings: at each it drops
	/// ONE capturer right next to the building, who starts capturing at once, and drives on to the next. A transport that
	/// can only unload everyone at once (the stock "Unload" order; the engine's UnloadCargo activity supports a single
	/// passenger only when issued as such) drops them all at the first stop, and each capturer then runs to its OWN
	/// building. The contract is neutral (CA) so the engineer owner (Cameo) never depends on a transport implementation;
	/// the intended provider is Fransbot's capture-transport service (FB1/FB2, DESIGN §22: one transport system).
	/// The provider owns every passenger of an accepted run until that passenger is delivered or the run aborts.
	/// </summary>
	public interface IBotCaptureTransportProvider
	{
		/// <summary>
		/// Carry `passengers[i]` to `targets[i]` (same length, 1-5; targets in visiting order). False when it cannot now
		/// (no craft, no safe route): the caller sends them on foot.
		/// </summary>
		bool TryRequestCaptureRun(IBot bot, IReadOnlyList<Actor> passengers, IReadOnlyList<Actor> targets);

		/// <summary>True while the passenger waits for, rides in or is being unloaded from a transport.</summary>
		bool IsHandlingPassenger(Actor passenger);

		/// <summary>True exactly once after the passenger was dropped for its target; the caller then orders the capture.</summary>
		bool TryConsumeDelivered(Actor passenger, out Actor target);
	}
}
