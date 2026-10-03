#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License,
 * either version 3 of the License, or (at your option) any later version.
 * For more information, see COPYING.
 */
#endregion

using System.Linq;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>Why a module holds a unit (LC1, AI_MASTER_PLAN §3). Logged, and read by the ownership watchdog (LC5).</summary>
	public enum BotLeasePurpose { Squad, Scout, Beacon, Capture, Engineer, Crate, McvExpansion, Mission, Emergency, Repair, Garrison }

	/// <summary>One module's claim on one unit. `ExpiresTick` is the failsafe: a holder that stops renewing loses it.</summary>
	public readonly record struct BotLease(string Owner, BotLeasePurpose Purpose, int AcquiredTick, int ExpiresTick);

	/// <summary>
	/// LC1: the common unit-claim contract (docs/design/AI_REVIEW_FRANSOTTO_2026-09-30.md, review P0 — "Actor.IsIdle is
	/// not an ownership primitive"). A module that sends a unit on a long-lived job claims it first and skips units
	/// another module holds; holders either release, or renew every evaluation (a heartbeat) and let the lease expire
	/// when they drop the unit. Not a scheduler: modules keep their own logic and only ask "may I?".
	/// </summary>
	public interface IBotUnitLeases
	{
		/// <summary>Claim or re-claim for `durationTicks` (≤ 0 = until released). False when another owner holds it.</summary>
		bool TryClaim(Actor actor, string owner, BotLeasePurpose purpose, int durationTicks);

		/// <summary>End this owner's lease (a no-op when someone else holds it).</summary>
		void Release(Actor actor, string owner);

		/// <summary>True when an unexpired lease of a DIFFERENT owner covers the unit.</summary>
		bool IsClaimedByOther(Actor actor, string owner);

		BotLease? LeaseOf(Actor actor);

		/// <summary>
		/// DESIGN §19.6 (maintainer 2026-09-30): an emergency takes a claimed unit over. The holder loses the lease and is
		/// told through <see cref="IBotUnitLeaseLost"/>; false when the unit is gone.
		/// </summary>
		bool Preempt(Actor actor, string owner, BotLeasePurpose purpose, int durationTicks);

		/// <summary>
		/// The negotiated handoff: atomically re-keys the unit's lease to `newOwner`, whoever currently holds it — one
		/// module passing a unit to another it agreed to work with (e.g. an engineer run's passengers going to the
		/// transport provider for the ride, so §19.6's order gate counts the rider orders as owned). Cooperation, not
		/// an emergency: no <see cref="IBotUnitLeaseLost"/> fires and the takeover is not counted as a preempt.
		/// False when the unit is gone.
		/// </summary>
		bool Transfer(Actor actor, string newOwner, BotLeasePurpose purpose, int durationTicks);
	}

	/// <summary>
	/// Implemented by a lease holder that wants to hear when an emergency took its unit (DESIGN §19.6). Matched by owner
	/// name: the registry notifies the Player traits whose type name is the old lease owner (the `nameof(...)` convention
	/// every holder uses). A holder without it learns on its next heartbeat, when its re-claim is denied.
	/// </summary>
	public interface IBotUnitLeaseLost
	{
		void LeaseLost(Actor actor, string newOwner, BotLeasePurpose purpose);
	}

	public static class BotUnitLeases
	{
		/// <summary>
		/// The player's enabled lease service, or null. Resolved at every use, never cached: the registry is conditional
		/// (genericbot), and a cache taken before the condition lands stays null for the match (LC4's bug class).
		/// Null means "no contract": callers behave exactly as before, which keeps `classic` untouched.
		/// </summary>
		public static IBotUnitLeases Of(Player player) =>
			player?.PlayerActor.TraitsImplementing<IBotUnitLeases>().FirstOrDefault(l => l.IsTraitEnabled());

		/// <summary>Claim through a possibly-absent service: without one, every claim succeeds (the old behaviour).</summary>
		public static bool TryClaim(IBotUnitLeases leases, Actor actor, string owner, BotLeasePurpose purpose, int durationTicks) =>
			leases == null || leases.TryClaim(actor, owner, purpose, durationTicks);

		public static bool IsClaimedByOther(IBotUnitLeases leases, Actor actor, string owner) =>
			leases != null && leases.IsClaimedByOther(actor, owner);

		/// <summary>Hand off through a possibly-absent service: without one, the transfer "succeeds" (the old behaviour).</summary>
		public static bool Transfer(IBotUnitLeases leases, Actor actor, string newOwner, BotLeasePurpose purpose, int durationTicks) =>
			leases == null || leases.Transfer(actor, newOwner, purpose, durationTicks);
	}
}
