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
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>The ownership invariants LC5 checks (AI_MASTER_PLAN §3; the Fransbot author's review P1e).</summary>
	public enum BotOwnershipViolation
	{
		/// <summary>A squad holds a unit another module has leased: two owners order one actor.</summary>
		DoubleOwner,

		/// <summary>One unit sits in two squads (of one squad manager or of two).</summary>
		TwoSquads,

		/// <summary>A disabled squad manager still holds a unit (its TraitDisabled hand-back did not run or was undone).</summary>
		HeldByDisabled,

		/// <summary>A dead, lost or captured unit is still leased or in a squad after the grace window.</summary>
		DeadHeld,

		/// <summary>A live unit the squad layer should own sits in no squad, no pool and no lease after the grace window —
		/// the "released but never returned to the idle pool" class.</summary>
		Orphan,
	}

	/// <summary>
	/// The LC5 check, free of world state so tests can drive it with plain keys (the <see cref="BotLeaseTable{TKey}"/>
	/// pattern). Each pass the caller declares who holds what; the ledger keeps the only cross-pass state — how long a
	/// key has been dead-but-held or unowned — and reports each (violation, key) once, the first time it trips.
	/// </summary>
	public sealed class BotOwnershipLedger<TKey>
	{
		sealed class Holdings
		{
			public string LeaseOwner;
			public readonly List<string> Squads = new();
			public readonly List<string> DisabledHolders = new();
			public bool InPool;
		}

		readonly Dictionary<TKey, Holdings> pass = new();
		readonly Dictionary<TKey, int> deadSince = new();
		readonly Dictionary<TKey, int> unownedSince = new();
		readonly HashSet<(BotOwnershipViolation, TKey)> reported = new();
		readonly Dictionary<BotOwnershipViolation, int> counts = new();

		/// <summary>The lease owner name squads use (LC1, #681): a squad member leased under it is consistent, not double.</summary>
		public string SquadLeaseOwner = "SquadManagerBotModuleCA";

		public int Passes { get; private set; }

		/// <summary>Distinct (violation, unit) pairs reported so far.</summary>
		public IReadOnlyDictionary<BotOwnershipViolation, int> Counts => counts;

		Holdings Of(TKey key)
		{
			if (!pass.TryGetValue(key, out var h))
				pass[key] = h = new Holdings();

			return h;
		}

		public void Begin() => pass.Clear();

		public void Lease(TKey key, string owner) => Of(key).LeaseOwner = owner;

		public void Squad(TKey key, string holder, bool holderEnabled)
		{
			var h = Of(key);
			if (holderEnabled)
				h.Squads.Add(holder);
			else
				h.DisabledHolders.Add(holder);
		}

		public void Pool(TKey key) => Of(key).InPool = true;

		/// <summary>
		/// Evaluate one pass. `gone` = dead, out of the world or no longer ours. `candidates` = the live units the squad
		/// layer is responsible for (the caller filters excluded types, cargo and units mid-Enter). Returns the violations
		/// first seen in this pass, with a short detail naming the holders.
		/// </summary>
		public List<(BotOwnershipViolation Kind, TKey Key, string Detail)> Evaluate(int tick, Func<TKey, bool> gone,
			IEnumerable<TKey> candidates, int deadGraceTicks, int orphanGraceTicks)
		{
			Passes++;
			var found = new List<(BotOwnershipViolation, TKey, string)>();
			void Report(BotOwnershipViolation kind, TKey key, string detail)
			{
				if (!reported.Add((kind, key)))
					return;

				counts[kind] = counts.GetValueOrDefault(kind) + 1;
				found.Add((kind, key, detail));
			}

			foreach (var (key, h) in pass)
			{
				var held = h.LeaseOwner != null || h.Squads.Count > 0 || h.DisabledHolders.Count > 0;
				if (gone(key))
				{
					if (!held)
						continue;

					if (!deadSince.TryGetValue(key, out var since))
						deadSince[key] = since = tick;
					else if (tick - since > deadGraceTicks)
						Report(BotOwnershipViolation.DeadHeld, key, Describe(h));

					continue;
				}

				deadSince.Remove(key);
				if (h.Squads.Count > 1)
					Report(BotOwnershipViolation.TwoSquads, key, string.Join(" + ", h.Squads));

				if (h.Squads.Count > 0 && h.LeaseOwner != null && h.LeaseOwner != SquadLeaseOwner)
					Report(BotOwnershipViolation.DoubleOwner, key, $"{h.Squads[0]} + lease {h.LeaseOwner}");

				if (h.DisabledHolders.Count > 0)
					Report(BotOwnershipViolation.HeldByDisabled, key, string.Join(" + ", h.DisabledHolders));
			}

			// Units that left the pass entirely are no longer dead-but-held.
			foreach (var key in deadSince.Keys.Where(k => !pass.ContainsKey(k)).ToList())
				deadSince.Remove(key);

			var live = new HashSet<TKey>();
			foreach (var key in candidates)
			{
				live.Add(key);
				var owned = pass.TryGetValue(key, out var h) && (h.LeaseOwner != null || h.Squads.Count > 0 || h.InPool);
				if (owned)
				{
					unownedSince.Remove(key);
					continue;
				}

				if (!unownedSince.TryGetValue(key, out var since))
					unownedSince[key] = tick;
				else if (tick - since > orphanGraceTicks)
					Report(BotOwnershipViolation.Orphan, key, $"unowned for {tick - since} ticks");
			}

			foreach (var key in unownedSince.Keys.Where(k => !live.Contains(k)).ToList())
				unownedSince.Remove(key);

			return found;
		}

		static string Describe(Holdings h)
		{
			var parts = new List<string>();
			if (h.LeaseOwner != null)
				parts.Add("lease " + h.LeaseOwner);

			parts.AddRange(h.Squads);
			parts.AddRange(h.DisabledHolders.Select(d => d + " (disabled)"));
			return string.Join(" + ", parts);
		}
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("LC5 (AI_MASTER_PLAN §3): the ownership watchdog. Every CheckIntervalTicks it reads who holds each of this bot's",
		"units — the LC1 lease registry, every squad manager's squads and idle pool — and logs, once per unit, any broken",
		"invariant: two owners, two squads, a unit held by a disabled manager, a dead unit still held, or a live unit",
		"nobody owns. Read-only: it never orders, claims or releases anything, so it cannot change a decision.",
		"Runs in bot-only matches (the A/B harness) and whenever Debug.BotDebug is on; idle in games with a human.")]
	public class BotOwnershipWatchdogInfo : ConditionalTraitInfo
	{
		[Desc("Ticks between checks.")]
		public readonly int CheckIntervalTicks = 100;

		[Desc("A dead/lost unit may stay held this long before it counts: the lease registry prunes every 250 ticks and",
			"squads clean on their own cadence.")]
		public readonly int DeadGraceTicks = 400;

		[Desc("A live squad-eligible unit may stay unowned this long before it counts: new units wait for the squad",
			"manager's next AssignRolesInterval pass.")]
		public readonly int OrphanGraceTicks = 750;

		[Desc("Also run in matches with a human player (normally only bot-only matches and Debug.BotDebug).")]
		public readonly bool AlwaysActive = false;

		public override object Create(ActorInitializer init) { return new BotOwnershipWatchdog(init.Self, this); }
	}

	public class BotOwnershipWatchdog : ConditionalTrait<BotOwnershipWatchdogInfo>, IBotTick, IBotNotifyIdleBaseUnits
	{
		readonly World world;
		readonly OpenRA.Player player;
		readonly BotOwnershipLedger<Actor> ledger = new();

		// Each squad manager hands its live idle-pool list to every IBotNotifyIdleBaseUnits; the lists are the managers'
		// own, so reading them each pass sees the current pool without touching the squad manager.
		readonly List<List<UnitWposWrapper>> pools = new();
		readonly Dictionary<(BotOwnershipViolation, string), int> byType = new();
		SquadManagerBotModuleCA[] managers;
		bool? active;
		int ticks;

		public BotOwnershipWatchdog(Actor self, BotOwnershipWatchdogInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		public int Passes => ledger.Passes;

		public IReadOnlyDictionary<BotOwnershipViolation, int> Counts => ledger.Counts;

		/// <summary>(violation, actor type) → distinct units, for the match log.</summary>
		public IReadOnlyDictionary<(BotOwnershipViolation Kind, string Type), int> CountsByType => byType;

		void IBotNotifyIdleBaseUnits.UpdatedIdleBaseUnits(List<UnitWposWrapper> unitsHangingAroundTheBase)
		{
			if (unitsHangingAroundTheBase != null && !pools.Any(p => ReferenceEquals(p, unitsHangingAroundTheBase)))
				pools.Add(unitsHangingAroundTheBase);
		}

		bool Active()
		{
			// A bot-only match is a test match (the A/B harness); decided once, the player set never changes. The harness
			// seats its client in the map's NonCombatant "Referee" slot, and lobby clients ignore
			// PlayerReference.NonCombatant, so the declared flag is checked too (as AiMatchLogWriter does).
			active ??= Info.AlwaysActive || Game.Settings.Debug.BotDebug
				|| !world.Players.Any(p => p.Playable && !p.IsBot && !p.NonCombatant && !p.PlayerReference.NonCombatant);
			return active.Value;
		}

		bool Gone(Actor a) => a.IsDead || !a.IsInWorld || a.Owner != player;

		void IBotTick.BotTick(IBot bot)
		{
			if (IsTraitDisabled || --ticks > 0 || !Active())
				return;

			ticks = Info.CheckIntervalTicks;

			// Every instance, enabled or not (one per personality): the set is fixed, only IsTraitDisabled moves, and that
			// is read each pass — caching the ENABLED subset would be LC4's bug class.
			if (managers == null)
			{
				managers = player.PlayerActor.TraitsImplementing<SquadManagerBotModuleCA>().ToArray();

				// One line when it starts, so a silent log reads as "no violations", never as "never ran".
				Log.Write("debug", $"AI {player.InternalName}: LC5 ownership watchdog active: {managers.Length} squad manager(s), "
					+ $"lease registry {(BotUnitLeases.Of(player) != null ? "on" : "off")}, every {Info.CheckIntervalTicks} ticks, tick={world.WorldTick}");
			}

			ledger.Begin();
			var leases = BotUnitLeases.Of(player) as BotUnitLeaseRegistry;
			if (leases != null)
				foreach (var (actor, lease) in leases.ActiveLeases)
					ledger.Lease(actor, lease.Owner);

			var excluded = new HashSet<string>();
			var anyEnabled = false;
			foreach (var m in managers)
			{
				var name = m.Info.InstanceName ?? "squads";
				if (!m.IsTraitDisabled)
				{
					anyEnabled = true;
					excluded.UnionWith(m.Info.ExcludeFromSquadsTypes);
				}

				for (var i = 0; i < m.Squads.Count; i++)
				{
					var squad = m.Squads[i];
					var holder = $"{name}/{squad.Type}#{i}";
					foreach (var u in squad.Units)
						if (u.Actor != null)
							ledger.Squad(u.Actor, holder, !m.IsTraitDisabled);
				}
			}

			foreach (var pool in pools)
				foreach (var u in pool)
					if (u.Actor != null)
						ledger.Pool(u.Actor);

			// Without an enabled squad manager nobody is responsible for the army, so there is nothing to orphan.
			var candidates = anyEnabled
				? world.ActorsHavingTrait<IPositionable>().Where(a => a.Owner == player && a.IsInWorld && !a.IsDead
					&& !excluded.Contains(a.Info.Name) && a.Info.HasTraitInfo<MobileInfo>() && a.CurrentActivity is not Enter)
				: Enumerable.Empty<Actor>();

			var found = ledger.Evaluate(world.WorldTick, Gone, candidates, Info.DeadGraceTicks, Info.OrphanGraceTicks);
			foreach (var (kind, actor, detail) in found)
			{
				var type = actor.Info.Name;
				byType[(kind, type)] = byType.GetValueOrDefault((kind, type)) + 1;
				Log.Write("debug", $"AI {player.InternalName}: LC5 OWNERSHIP {kind.ToString().ToUpperInvariant()} {type} {actor.ActorID}: {detail} tick={world.WorldTick}");
			}

			if (found.Count > 0)
				Log.Write("debug", $"AI {player.InternalName}: LC5 ownership totals after {ledger.Passes} checks: "
					+ string.Join(", ", ledger.Counts.OrderBy(kv => kv.Key).Select(kv => $"{kv.Key} {kv.Value}")) + $" tick={world.WorldTick}");
		}
	}
}
