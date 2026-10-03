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
using System.Linq;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>What the order gate does with one unit order (DESIGN §19.6).</summary>
	public enum BotOrderVerdict
	{
		/// <summary>No claim on the unit, or the issuer holds it.</summary>
		Allow,

		/// <summary>Another module holds the unit; the gate only watches, so the order goes through and is counted.</summary>
		Conflict,

		/// <summary>Another module holds the unit; the order is dropped.</summary>
		Refuse,

		/// <summary>An emergency order from a listed module: it takes the claim over and the old holder is told.</summary>
		Preempt,
	}

	/// <summary>
	/// The order-gate rule and its counters, free of world state so tests can drive it with plain keys. The caller (Cameo's
	/// ModularBot, the one funnel every bot module's orders pass through) supplies who issued the order, who holds the
	/// unit's lease, and whether the order came from an attack response.
	/// </summary>
	public sealed class BotOrderGate<TKey>
	{
		readonly Dictionary<TKey, (string Issuer, int Tick, bool Held)> lastIssuer = new();
		readonly Dictionary<(string Issuer, string Holder, BotOrderVerdict Verdict), int> pairs = new();
		readonly Dictionary<(string First, string Second), int> crossed = new();

		public int Refused { get; private set; }
		public int Preempted { get; private set; }
		public int Conflicts { get; private set; }
		public int Crossed { get; private set; }
		public int Unattributed { get; private set; }

		/// <summary>(issuer, holder, verdict) → orders, for the match log.</summary>
		public IReadOnlyDictionary<(string Issuer, string Holder, BotOrderVerdict Verdict), int> Pairs => pairs;

		/// <summary>(earlier issuer, later issuer) → orders that reached one unit from two modules inside the window.</summary>
		public IReadOnlyDictionary<(string First, string Second), int> CrossedPairs => crossed;

		/// <summary>
		/// The rule. `holder` is the lease owner (null = unclaimed); `issuer` the module that queued the order (null = an
		/// order queued outside a module call, never refused). An emergency is an order a listed module queued from an
		/// attack response: it preempts instead of being refused (maintainer 2026-09-30).
		/// </summary>
		public static BotOrderVerdict Decide(string issuer, string holder, bool enforce, bool emergency, ICollection<string> emergencyModules)
		{
			if (holder == null || issuer == null || issuer == holder)
				return BotOrderVerdict.Allow;

			if (!enforce)
				return BotOrderVerdict.Conflict;

			return emergency && emergencyModules != null && emergencyModules.Contains(issuer)
				? BotOrderVerdict.Preempt : BotOrderVerdict.Refuse;
		}

		/// <summary>Decide, count, and return the verdict plus whether this (issuer, holder, verdict) pair is new (log it once).</summary>
		public (BotOrderVerdict Verdict, bool FirstOfPair) Judge(string issuer, string holder, bool enforce, bool emergency,
			ICollection<string> emergencyModules)
		{
			if (issuer == null)
				Unattributed++;

			var verdict = Decide(issuer, holder, enforce, emergency, emergencyModules);
			switch (verdict)
			{
				case BotOrderVerdict.Allow: return (verdict, false);
				case BotOrderVerdict.Conflict: Conflicts++; break;
				case BotOrderVerdict.Refuse: Refused++; break;
				case BotOrderVerdict.Preempt: Preempted++; break;
			}

			var key = (issuer, holder, verdict);
			var n = pairs.GetValueOrDefault(key);
			pairs[key] = n + 1;
			return (verdict, n == 0);
		}

		/// <summary>
		/// Crossed orders: a unit ordered by one module and then by a different module within `window` ticks is two
		/// owners in fact — unless the earlier issuer's claim ended in between. `holder` is the unit's lease owner at
		/// this order; the earlier issuer holding the lease at ITS order and holding it no longer (squad dissolved,
		/// escort finished, the pool re-drafted the unit) is a clean hand-off, not a fight. An earlier issuer that
		/// never held the lease cannot prove a release, so it keeps the old "two issuers" signal. Returns the earlier
		/// issuer when this order crosses one (null otherwise). Call only for orders that will be issued.
		/// </summary>
		public string NoteIssued(TKey unit, string issuer, int tick, int window, string holder)
		{
			if (issuer == null || window <= 0)
				return null;

			string earlier = null;
			if (lastIssuer.TryGetValue(unit, out var last) && last.Issuer != issuer && tick - last.Tick <= window)
			{
				var released = last.Held && holder != last.Issuer;
				if (!released)
				{
					earlier = last.Issuer;
					Crossed++;
					crossed[(last.Issuer, issuer)] = crossed.GetValueOrDefault((last.Issuer, issuer)) + 1;
				}
			}

			lastIssuer[unit] = (issuer, tick, issuer == holder);
			return earlier;
		}

		/// <summary>Forget units that are gone, so the crossed-order table stays bounded.</summary>
		public void Prune(System.Func<TKey, bool> gone)
		{
			foreach (var k in lastIssuer.Keys.Where(gone).ToList())
				lastIssuer.Remove(k);
		}
	}
}
