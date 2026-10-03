#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// TC-1 (AI_DEEP_RESEARCH.md §11, AI_ARCHITECTURE.md §12.17): one allied bot's
	/// broadcast on the team blackboard — what it would say on voice chat, as
	/// fog-honest scalars refreshed once per situation snapshot. An immutable
	/// value carrier: own-side readings plus the DI-1 pacing wave, never an
	/// enumeration of enemy actors.
	/// </summary>
	public class TeamBroadcast
	{
		/// <summary>Tick of the snapshot that produced this broadcast; 0 = never published.</summary>
		public readonly int SnapshotTick;

		/// <summary>The bot's own army value — an own-side scalar, no enemy knowledge.</summary>
		public readonly int OwnArmyValue;

		/// <summary>
		/// Urgency as 0 = Normal, 1 = Pressured, 2 = Emergency — the Cameo
		/// <c>BotUrgency</c> ordinals carried as an int because that enum lives in
		/// an assembly this one cannot reference.
		/// </summary>
		public readonly int UrgencyLevel;

		/// <summary>The DI-1 Director's tension in [0,100], forwarded verbatim.</summary>
		public readonly int DirectorTension;

		/// <summary>The DI-1 Director's wave phase, forwarded verbatim.</summary>
		public readonly DirectorPhase DirectorPhase;

		/// <summary>The enemy this bot is currently committed to, or null.</summary>
		public readonly Player MainTarget;

		/// <summary>True while the bot is under pressure (UrgencyLevel &gt;= 1) and wants help.</summary>
		public readonly bool RequestsDefence;

		/// <summary>
		/// Where help is needed — the bot's own base centre while under pressure;
		/// <see cref="WPos.Zero"/> when none (not pressured, or no base stands).
		/// </summary>
		public readonly WPos DefendPosition;

		/// <summary>
		/// TC-2c (AI_ARCHITECTURE §12.17): the publisher's own client index — the deterministic
		/// precedence when two allies claim the same resource field (lower index keeps its claim).
		/// </summary>
		public readonly int ClientIndex;

		/// <summary>
		/// TC-2c: the resource field this bot is currently expanding toward (its planner's
		/// expansion target), <see cref="WPos.Zero"/> when none. Own-side intent shared with
		/// allies so expansion claims do not collide.
		/// </summary>
		public readonly WPos ExpansionClaim;

		/// <summary>
		/// TC-3 (AI_ARCHITECTURE §12.18): the centroid of the publisher's own mobile army —
		/// own-side, honest. Feeds the nearest-army rescue election.
		/// <see cref="WPos.Zero"/> when none.
		/// </summary>
		public readonly WPos ArmyCentroid;

		/// <summary>
		/// TC-3: an expansion claim the publisher wants escorted — a thin army claiming a
		/// contested field asks for a bodyguard. <see cref="WPos.Zero"/> when none.
		/// </summary>
		public readonly WPos ExpansionAssist;

		/// <summary>
		/// TC-3: the publisher's spawn anchor (map spawn point / home location) — public
		/// map data shared so every member folds the identical Voronoi sector partition.
		/// <see cref="WPos.Zero"/> when none.
		/// </summary>
		public readonly WPos SpawnPoint;

		/// <summary>
		/// TC-2e (AI_ARCHITECTURE §12.17): the cell centres (Map.CenterOfCell) of the
		/// capture/contest targets this bot is actively working — own-side intent shared
		/// with allies so capture claims do not collide; the lower <see cref="ClientIndex"/>
		/// claimant keeps its claim. Empty when none.
		/// </summary>
		public readonly IReadOnlyList<WPos> CaptureClaims;

		/// <summary>
		/// TC-3 review (post-merge audit 4.4): the publisher's match-local identity —
		/// Player.InternalName. <see cref="ClientIndex"/> orders lobby slots, but map-side
		/// bots can share the host's index, so coalition identity (rescue elections,
		/// sector anchors) keys on this instead. Null on old-version publishers.
		/// </summary>
		public readonly string ParticipantId;

		public TeamBroadcast(int snapshotTick, int ownArmyValue, int urgencyLevel, int directorTension,
			DirectorPhase directorPhase, Player mainTarget, bool requestsDefence, WPos defendPosition,
			int clientIndex = 0, WPos expansionClaim = default, WPos armyCentroid = default,
			WPos expansionAssist = default, WPos spawnPoint = default, IReadOnlyList<WPos> captureClaims = null,
			string participantId = null)
		{
			SnapshotTick = snapshotTick;
			OwnArmyValue = ownArmyValue;
			UrgencyLevel = urgencyLevel;
			DirectorTension = directorTension;
			DirectorPhase = directorPhase;
			MainTarget = mainTarget;
			RequestsDefence = requestsDefence;
			DefendPosition = defendPosition;
			ClientIndex = clientIndex;
			ExpansionClaim = expansionClaim;
			ArmyCentroid = armyCentroid;
			ExpansionAssist = expansionAssist;
			SpawnPoint = spawnPoint;
			CaptureClaims = captureClaims ?? Array.Empty<WPos>();
			ParticipantId = participantId;
		}

		/// <summary>What an absent, disabled or never-snapshotted provider publishes.</summary>
		public static readonly TeamBroadcast Empty =
			new(0, 0, 0, 0, DirectorPhase.BuildUp, null, false, WPos.Zero);
	}

	/// <summary>
	/// TC-1 (AI_DEEP_RESEARCH.md §11, AI_ARCHITECTURE.md §12.17): the publish end
	/// of the team blackboard. Every bot of a match runs on the host
	/// (AI_ARCHITECTURE.md §1.1), so allied bots read each other's PlayerActor
	/// traits directly — an unsynced blackboard, no sync or network work, and no
	/// cheat: only own-side scalars and ally-published data cross it. Publish-only:
	/// nothing consumes it yet; TC-2 adds the consumers (synchronised attack
	/// windows, defend-request answering, expansion-claim deconfliction, role-split
	/// bias, human-ally beacons). Providers live in OpenRA.Mods.Cameo and must not
	/// be referenced by name from this assembly; absent or disabled providers
	/// publish <see cref="TeamBroadcast.Empty"/> — never a behaviour change.
	/// </summary>
	public interface IBotTeamMember
	{
		/// <summary>The bot's latest snapshot broadcast; <see cref="TeamBroadcast.Empty"/> when none.</summary>
		TeamBroadcast Broadcast { get; }
	}

	/// <summary>The TC-1 summary of what a bot's allies published.</summary>
	public sealed class TeamBlackboardSummary
	{
		/// <summary>Allied bots whose broadcast joined this summary.</summary>
		public int AlliedBots;

		/// <summary>Sum of allied <see cref="TeamBroadcast.OwnArmyValue"/>.</summary>
		public int TotalArmyValue;

		/// <summary>Highest allied <see cref="TeamBroadcast.DirectorTension"/>.</summary>
		public int MaxTension;

		/// <summary>True while at least one ally's Director wave is at Climax.</summary>
		public bool AnyClimax;

		/// <summary>Allies currently asking for defence.</summary>
		public int DefendRequests;

		/// <summary>
		/// Size of the largest group of broadcasts sharing the same non-null
		/// <see cref="TeamBroadcast.MainTarget"/> — allies committed to the same enemy.
		/// </summary>
		public int SharedTargetCount;
	}

	/// <summary>
	/// TC-1 (AI_ARCHITECTURE.md §12.17): reads the allied half of the team
	/// blackboard. The caller's own broadcast is deliberately NOT folded in — a
	/// bot reads its own scalars directly, so the summary answers "what is the
	/// rest of the team doing". Fog-honest: <see cref="World.Players"/> filtered
	/// to allied bots plus their published broadcasts — the same seam
	/// AlliedCommitments already uses — never an actor enumeration. Pure
	/// aggregation in <see cref="Aggregate"/> keeps the logic testable without a
	/// World.
	/// </summary>
	public static class TeamBlackboard
	{
		/// <summary>Fold broadcasts into one summary; null or empty input yields all zeros.</summary>
		public static TeamBlackboardSummary Aggregate(IEnumerable<TeamBroadcast> broadcasts)
		{
			var summary = new TeamBlackboardSummary();
			if (broadcasts == null)
				return summary;

			var sharedTargets = new Dictionary<Player, int>();
			foreach (var broadcast in broadcasts)
			{
				if (broadcast == null)
					continue;

				summary.AlliedBots++;
				summary.TotalArmyValue += broadcast.OwnArmyValue;
				summary.MaxTension = Math.Max(summary.MaxTension, broadcast.DirectorTension);
				if (broadcast.DirectorPhase == DirectorPhase.Climax)
					summary.AnyClimax = true;
				if (broadcast.RequestsDefence)
					summary.DefendRequests++;
				if (broadcast.MainTarget != null)
					sharedTargets[broadcast.MainTarget] = sharedTargets.GetValueOrDefault(broadcast.MainTarget) + 1;
			}

			foreach (var count in sharedTargets.Values)
				summary.SharedTargetCount = Math.Max(summary.SharedTargetCount, count);

			return summary;
		}

		/// <summary>
		/// TC-2e review (post-merge audit 4.2): the ONE liveness rule every team
		/// aggregation shares. A broadcast counts only while its publisher is
		/// alive (<see cref="WinState.Undefined"/>) and its snapshot is fresh —
		/// OpenRA keeps a defeated player's traits readable, so without this a
		/// dead ally's last broadcast keeps electing responders, holding sectors
		/// and claiming fields. <see cref="BroadcastMaxAgeTicks"/> covers a few
		/// staggered snapshot intervals, not a live match's worth of drift.
		/// </summary>
		public const int BroadcastMaxAgeTicks = 500;

		public static bool IsLive(TeamBroadcast broadcast, Player publisher, int now) =>
			broadcast != null && broadcast.SnapshotTick > 0 && now - broadcast.SnapshotTick <= BroadcastMaxAgeTicks
				&& (publisher == null || publisher.WinState == WinState.Undefined);

		/// <summary>
		/// Read every allied bot's latest broadcast — allies only, never the caller:
		/// the caller's own state is already on its own snapshot. Host-side and
		/// unsynced by design (every bot runs on the host); an ally without an
		/// enabled provider contributes nothing, so a 1v1 yields a zeroed summary.
		/// Dead or stale publishers are filtered centrally — no consumer solves
		/// freshness on its own.
		/// </summary>
		public static TeamBlackboardSummary Collect(Player me) => Aggregate(CollectBroadcasts(me));

		/// <summary>
		/// The allied broadcasts themselves (allies only, never the caller) — for
		/// consumers that need per-ally detail the summary drops, like which ally is
		/// asking for help and where. Only live publishers (<see cref="IsLive"/>).
		/// </summary>
		public static List<TeamBroadcast> CollectBroadcasts(Player me)
		{
			var broadcasts = new List<TeamBroadcast>();
			if (me?.World == null)
				return broadcasts;

			var now = me.World.WorldTick;
			foreach (var p in me.World.Players.Where(p => p != me && p.IsBot && me.IsAlliedWith(p)))
			{
				var member = p.PlayerActor?.TraitsImplementing<IBotTeamMember>().FirstEnabledTraitOrDefault();
				if (member != null && IsLive(member.Broadcast, p, now))
					broadcasts.Add(member.Broadcast);
			}

			return broadcasts;
		}

		/// <summary>
		/// TC-2b: the ally most worth answering — highest urgency level first; a tie
		/// goes to the weakest ally (lowest published army value is the most desperate
		/// defence). Broadcasts without a usable defend position are skipped; null or
		/// empty input yields null.
		/// </summary>
		public static TeamBroadcast TopDefendRequest(IEnumerable<TeamBroadcast> broadcasts)
		{
			if (broadcasts == null)
				return null;

			return broadcasts
				.Where(b => b != null && b.RequestsDefence && b.DefendPosition != WPos.Zero)
				.OrderByDescending(b => b.UrgencyLevel).ThenBy(b => b.OwnArmyValue)
				.FirstOrDefault();
		}

		/// <summary>
		/// TC-2e (AI_ARCHITECTURE §12.17): positions claimed by allied broadcasts whose
		/// publisher outranks the caller — lower <see cref="CoalitionFold.ParticipantKey"/>
		/// (InternalName, ClientIndex only as an old-broadcast fallback) wins, so a
		/// contested capture or contest target converges on one claimant instead of
		/// every ally walking at it. ClientIndex alone cannot order this: map-side
		/// bots share the host's index (post-merge audit 4.4). Pure, for the tests;
		/// null or empty input yields an empty set.
		/// </summary>
		public static HashSet<WPos> ClaimsAheadOf(IEnumerable<TeamBroadcast> broadcasts, string myParticipantKey)
		{
			var claims = new HashSet<WPos>();
			if (broadcasts == null || myParticipantKey == null)
				return claims;

			foreach (var broadcast in broadcasts)
			{
				if (broadcast == null || broadcast.CaptureClaims == null
					|| string.Compare(CoalitionFold.ParticipantKey(broadcast), myParticipantKey, StringComparison.Ordinal) >= 0)
					continue;

				foreach (var claim in broadcast.CaptureClaims)
					claims.Add(claim);
			}

			return claims;
		}

		/// <summary>
		/// BF-2 prefer-shard (AI_ARCHITECTURE §12.26): the deterministic ownership tier that
		/// closes the simultaneous-pick window — two allies committing the same capturable
		/// inside one snapshot interval can't be arbitrated by claims that aren't published
		/// yet, so the targets are pre-partitioned instead. Rank is the caller's position in
		/// the ordinal-sorted union of own + allied participant keys; CaptureShard maps a cell
		/// to a shard index. A bot prefers in-shard targets; out-of-shard stays eligible once
		/// the own tier is exhausted, so the shard orders but never walls off. Pure, for the
		/// tests — 1v1 or no allies yields (0,1) and every cell is in-shard.
		/// </summary>
		public static (int Rank, int Size) ClaimRank(string ownKey, IEnumerable<string> alliedKeys)
		{
			var keys = new List<string> { ownKey };
			if (alliedKeys != null)
				keys.AddRange(alliedKeys.Where(k => k != null && k != ownKey));

			keys.Sort(StringComparer.Ordinal);
			var rank = keys.IndexOf(ownKey);
			return (rank < 0 ? 0 : rank, keys.Count);
		}

		public static (int Rank, int Size) ClaimRank(Player player)
		{
			var broadcasts = CollectBroadcasts(player);
			var ownKey = player.InternalName ?? "#" + player.ClientIndex;
			var alliedKeys = broadcasts.Where(b => b != null).Select(CoalitionFold.ParticipantKey);
			return ClaimRank(ownKey, alliedKeys);
		}

		public static int CaptureShard(CPos cell, int size)
		{
			if (size <= 0)
				return 0;

			return ((cell.X * 31 + cell.Y) % size + size) % size;
		}
	}
}
