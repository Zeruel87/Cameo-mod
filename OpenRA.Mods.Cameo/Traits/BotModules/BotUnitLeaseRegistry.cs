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

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// The lease table itself, free of world state so tests can drive it with plain keys. One unexpired lease per key;
	/// the same owner may re-claim (and change purpose), a different owner is refused until release or expiry.
	/// </summary>
	public sealed class BotLeaseTable<TKey>
	{
		readonly Dictionary<TKey, BotLease> leases = new();

		public int Count => leases.Count;

		static bool Active(BotLease l, int now) => now < l.ExpiresTick;

		public bool TryClaim(TKey key, string owner, BotLeasePurpose purpose, int now, int durationTicks)
		{
			var held = leases.TryGetValue(key, out var l) && Active(l, now);
			if (held && l.Owner != owner)
				return false;

			var expires = durationTicks > 0 ? now + durationTicks : int.MaxValue;
			leases[key] = new BotLease(owner, purpose, held ? l.AcquiredTick : now, expires);
			return true;
		}

		public void Release(TKey key, string owner)
		{
			if (leases.TryGetValue(key, out var l) && l.Owner == owner)
				leases.Remove(key);
		}

		/// <summary>Take the key over whoever holds it; returns the previous active owner (null if none).</summary>
		public string Preempt(TKey key, string owner, BotLeasePurpose purpose, int now, int durationTicks)
		{
			var previous = leases.TryGetValue(key, out var l) && Active(l, now) ? l.Owner : null;
			leases[key] = new BotLease(owner, purpose, now, durationTicks > 0 ? now + durationTicks : int.MaxValue);
			return previous;
		}

		/// <summary>The negotiated handoff: re-key the lease to a new owner whoever held it (or was free).</summary>
		public void Transfer(TKey key, string newOwner, BotLeasePurpose purpose, int now, int durationTicks)
		{
			leases[key] = new BotLease(newOwner, purpose, now, durationTicks > 0 ? now + durationTicks : int.MaxValue);
		}

		public bool IsClaimedByOther(TKey key, string owner, int now) =>
			leases.TryGetValue(key, out var l) && Active(l, now) && l.Owner != owner;

		public BotLease? LeaseOf(TKey key, int now) =>
			leases.TryGetValue(key, out var l) && Active(l, now) ? l : null;

		/// <summary>Drops expired leases and those whose key is gone; returns (expired, gone).</summary>
		public (int Expired, int Gone) Prune(int now, Func<TKey, bool> gone)
		{
			var expired = 0;
			var dead = 0;
			foreach (var (key, l) in leases.ToList())
			{
				if (gone(key))
				{
					leases.Remove(key);
					dead++;
				}
				else if (!Active(l, now))
				{
					leases.Remove(key);
					expired++;
				}
			}

			return (expired, dead);
		}

		public IEnumerable<(TKey Key, BotLease Lease)> ActiveLeases(int now) =>
			leases.Where(kv => Active(kv.Value, now)).Select(kv => (kv.Key, kv.Value));
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("LC1 (AI_MASTER_PLAN §3, docs/design/AI_REVIEW_FRANSOTTO_2026-09-30.md): the unit-claim contract. Modules that",
		"send a unit on a long-lived job claim it here first and skip units another module holds. Load it for genericbot",
		"only: consumers that find no registry behave as before, so classic stays untouched.")]
	public class BotUnitLeaseRegistryInfo : ConditionalTraitInfo
	{
		[Desc("Ticks between prunes (expired leases, dead or lost units) and the debug.log summary.")]
		public readonly int PruneIntervalTicks = 250;

		[Desc("DESIGN §19.6: the order gate (Cameo's ModularBot) REFUSES a unit order from a module that does not hold the",
			"unit's lease. False = it only counts the conflicts (the default until its A/B).")]
		public readonly bool EnforceAtOrderGate = false;

		[Desc("Modules whose orders from an attack response (an emergency) take a claimed unit over instead of being",
			"refused; the old holder is told (IBotUnitLeaseLost).")]
		public readonly HashSet<string> EmergencyModules = ["SquadManagerBotModuleCA"];

		[Desc("Ticks an emergency keeps a preempted unit before the lease expires (its module may renew it).")]
		public readonly int EmergencyLeaseTicks = 500;

		[Desc("Two different modules ordering one unit within this many ticks count as a crossed order. 0 disables.")]
		public readonly int CrossedOrderWindowTicks = 100;

		public override object Create(ActorInitializer init) { return new BotUnitLeaseRegistry(init.Self, this); }
	}

	public class BotUnitLeaseRegistry : ConditionalTrait<BotUnitLeaseRegistryInfo>, IBotUnitLeases, IBotTick
	{
		readonly World world;
		readonly OpenRA.Player player;
		readonly BotLeaseTable<Actor> table = new();
		int pruneTicks;
		(int, int, int, int, int) lastSummary;

		// Telemetry: Denied counts the claims the contract refused because another module held the unit — each one
		// is a pair of competing orders that no longer happens (review P0b).
		public int Claims { get; private set; }
		public int Denied { get; private set; }
		public int Expired { get; private set; }
		public int Gone { get; private set; }

		public BotUnitLeaseRegistry(Actor self, BotUnitLeaseRegistryInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		bool IsGone(Actor a) => a.IsDead || !a.IsInWorld || a.Owner != player;

		bool IBotUnitLeases.TryClaim(Actor actor, string owner, BotLeasePurpose purpose, int durationTicks)
		{
			if (actor == null || IsGone(actor))
				return false;

			if (table.TryClaim(actor, owner, purpose, world.WorldTick, durationTicks))
			{
				Claims++;
				return true;
			}

			Denied++;
			var holder = table.LeaseOf(actor, world.WorldTick);
			Log.Write("debug", $"AI ({player.ClientIndex}): LC1 lease denied: {owner} wanted {actor.Info.Name} {actor.ActorID} for {purpose}; {holder?.Owner} holds it for {holder?.Purpose} since tick {holder?.AcquiredTick} (tick {world.WorldTick})");
			return false;
		}

		void IBotUnitLeases.Release(Actor actor, string owner)
		{
			if (actor != null)
				table.Release(actor, owner);
		}

		bool IBotUnitLeases.IsClaimedByOther(Actor actor, string owner) =>
			actor != null && table.IsClaimedByOther(actor, owner, world.WorldTick);

		BotLease? IBotUnitLeases.LeaseOf(Actor actor) => actor == null ? null : table.LeaseOf(actor, world.WorldTick);

		public int Preempts { get; private set; }

		bool IBotUnitLeases.Preempt(Actor actor, string owner, BotLeasePurpose purpose, int durationTicks)
		{
			if (actor == null || IsGone(actor))
				return false;

			var previous = table.Preempt(actor, owner, purpose, world.WorldTick, durationTicks);
			Preempts++;
			if (previous != null && previous != owner)
			{
				Log.Write("debug", $"AI ({player.ClientIndex}): LC1 lease preempted: {owner} took {actor.Info.Name} {actor.ActorID} from {previous} for {purpose} (tick {world.WorldTick})");
				foreach (var lost in player.PlayerActor.TraitsImplementing<IBotUnitLeaseLost>())
					if (lost.GetType().Name == previous)
						lost.LeaseLost(actor, owner, purpose);
			}

			return true;
		}

		bool IBotUnitLeases.Transfer(Actor actor, string newOwner, BotLeasePurpose purpose, int durationTicks)
		{
			if (actor == null || IsGone(actor))
				return false;

			table.Transfer(actor, newOwner, purpose, world.WorldTick, durationTicks);
			return true;
		}

		/// <summary>Every unexpired lease, for the ownership watchdog (LC5) and tests.</summary>
		public IEnumerable<(Actor Actor, BotLease Lease)> ActiveLeases => table.ActiveLeases(world.WorldTick);

		void IBotTick.BotTick(IBot bot)
		{
			if (--pruneTicks > 0)
				return;

			pruneTicks = Info.PruneIntervalTicks;
			var (expired, gone) = table.Prune(world.WorldTick, IsGone);
			Expired += expired;
			Gone += gone;
			var summary = (table.Count, Claims, Denied, Expired, Gone);
			if (summary != lastSummary)
				Log.Write("debug", $"AI ({player.ClientIndex}): LC1 leases: {table.Count} held, claims {Claims}, denied {Denied}, expired {Expired}, gone {Gone} at tick {world.WorldTick}");

			lastSummary = summary;
		}
	}
}
