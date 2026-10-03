#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License as
 * published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	// Recon remains owned by ScoutBotModule; Secure is reserved for a later phase.
	public enum BotMissionType { Recon, Raid, Secure, Defend }

	public sealed class BotMission
	{
		public BotMissionType Type;
		public CPos Location;
		public Player TargetPlayer;
		public int RegionIndex;
		public int RequiredValue;
		public int Priority;

		// MissionCard id (docs/design/AI_MISSION_CARDS.md §2.1): the owner
		// allocates the string key; null = unallocated, consumers fall back to
		// IdentityKey until owner allocation lands (MC1).
		public string MissionId;

		// The identity key — deterministic from (Type, TargetPlayer, RegionIndex),
		// in the contract's grammar (raid:<target internal name>:r<region>).
		// InternalName, never ClientIndex — every non-human player carries the
		// host's ClientIndex (Player.cs). Re-derived instances of the same
		// underlying mission share the key, so attempts accumulate against it.
		public string IdentityKey =>
			$"{Type.ToString().ToLowerInvariant()}:{TargetPlayer?.InternalName ?? "self"}:r{RegionIndex}";

		public string EffectiveMissionId => MissionId ?? IdentityKey;
	}

	// The return path (AI_MISSION_CARDS.md §2.3): executors report attempt
	// transitions; the owner alone decides what a failure means. The shared
	// state/reason vocabulary lives in BotMissionLog.cs (BotMissionAttemptState,
	// BotMissionReasons) — one contract, ruled under §22. Opt-in: providers
	// adopt without forcing every provider to implement it.
	public interface IBotMissionOutcomeSink
	{
		void Report(string missionId, int attemptId, BotMissionAttemptState state, string reason, int tick);
	}

	public sealed class BotMissionAssignment
	{
		public BotMissionType Type;
		public int RegionIndex;
		public bool Frozen;
	}

	public interface IBotMissionProvider
	{
		IReadOnlyList<BotMission> Missions { get; }
		void MissionTaken(BotMission mission);
	}

	public interface IBotMissionAssignmentProvider
	{
		BotMissionAssignment LastMissionAssignment { get; }
	}
}
