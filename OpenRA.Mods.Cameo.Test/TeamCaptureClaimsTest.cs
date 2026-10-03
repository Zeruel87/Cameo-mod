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
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// TC-2e (AI_ARCHITECTURE.md §12.17): capture-claim arbitration on the team
	// blackboard. ClaimsAheadOf is the pure half — the union of every allied
	// CaptureClaims position whose publisher outranks the caller (strictly lower
	// participant key — InternalName, not ClientIndex — wins; map-side bots share
	// the host's ClientIndex, post-merge audit 4.4). The module ticks that consume
	// it stay integration-side.
	[TestFixture]
	public sealed class TeamCaptureClaimsTest
	{
		static readonly WPos ClaimA = new(1024, 2048, 0);
		static readonly WPos ClaimB = new(5120, 4096, 0);

		static TeamBroadcast Broadcast(string participantId, params WPos[] captureClaims) =>
			new(1500, 0, 0, 0, DirectorPhase.BuildUp, null, false, WPos.Zero,
				0, default, default, default, default, captureClaims, participantId);

		[Test]
		public void NullOrEmptyInputYieldsNoClaims()
		{
			Assert.That(TeamBlackboard.ClaimsAheadOf(null, "Multi3"), Is.Empty);
			Assert.That(TeamBlackboard.ClaimsAheadOf(new List<TeamBroadcast>(), "Multi3"), Is.Empty);
			Assert.That(TeamBlackboard.ClaimsAheadOf(new[] { Broadcast("Multi1", ClaimA) }, null), Is.Empty);
		}

		[Test]
		public void LowerKeyAllyClaimsAhead()
		{
			var claims = TeamBlackboard.ClaimsAheadOf(new[] { Broadcast("Multi1", ClaimA) }, "Multi3");
			Assert.That(claims, Does.Contain(ClaimA));
			Assert.That(claims, Has.Count.EqualTo(1));
		}

		[Test]
		public void HigherKeyAllyNeverOutranks()
		{
			var claims = TeamBlackboard.ClaimsAheadOf(new[] { Broadcast("Multi5", ClaimA) }, "Multi3");
			Assert.That(claims, Is.Empty,
				"an ally that publishes the same cell but keys below ours keeps its claim unchallenged");
		}

		[Test]
		public void SameKeyIsNotAhead()
		{
			var claims = TeamBlackboard.ClaimsAheadOf(new[] { Broadcast("Multi3", ClaimA) }, "Multi3");
			Assert.That(claims, Is.Empty);
		}

		[Test]
		public void SharedClientIndexMapSideBotsStillArbitrate()
		{
			// Audit 4.4 regression: every broadcast here carries ClientIndex 0 — the
			// map-side reality the int ordering could not see. Multi1 must still
			// outrank Multi3.
			var claims = TeamBlackboard.ClaimsAheadOf(new[] { Broadcast("Multi1", ClaimA) }, "Multi3");
			Assert.That(claims, Does.Contain(ClaimA),
				"identical ClientIndex must not disable precedence — participant key decides");
		}

		[Test]
		public void MissingParticipantIdFallsBackToClientIndex()
		{
			// An old-version broadcast (no ParticipantId) keys as "#<ClientIndex>" —
			// ordinal "#" < "M", so it outranks every InternalName publisher. The
			// order stays total and deterministic across a mixed-version board.
			var old = new TeamBroadcast(1500, 0, 0, 0, DirectorPhase.BuildUp, null, false,
				WPos.Zero, 7, default, default, default, default, new[] { ClaimA });
			var claims = TeamBlackboard.ClaimsAheadOf(new[] { old }, "Multi0");
			Assert.That(claims, Does.Contain(ClaimA));
		}

		[Test]
		public void MultipleClaimantsOnOnePositionStillResolveToLowest()
		{
			// Two allies claim the same cell: Multi1 outranks Multi3, so Multi4 and
			// Multi3 both read the cell as claimed-ahead while Multi1 reads none.
			var broadcasts = new[] { Broadcast("Multi3", ClaimA), Broadcast("Multi1", ClaimA) };
			Assert.That(TeamBlackboard.ClaimsAheadOf(broadcasts, "Multi4"), Does.Contain(ClaimA));
			Assert.That(TeamBlackboard.ClaimsAheadOf(broadcasts, "Multi2"), Does.Contain(ClaimA));
			Assert.That(TeamBlackboard.ClaimsAheadOf(broadcasts, "Multi1"), Is.Empty,
				"the lowest-key claimant sees nothing ahead — it is the winner by construction");
		}

		[Test]
		public void ClaimsUnionAcrossBroadcastsAndSkipNulls()
		{
			var broadcasts = new TeamBroadcast[] { null, Broadcast("Multi0", ClaimA), Broadcast("Multi1", ClaimB) };
			var claims = TeamBlackboard.ClaimsAheadOf(broadcasts, "Multi2");
			Assert.That(claims, Is.EquivalentTo(new[] { ClaimA, ClaimB }));
		}

		[Test]
		public void BroadcastWithoutClaimsContributesNothing()
		{
			// captureClaims left at the ctor default stores an empty list, never null.
			var claims = TeamBlackboard.ClaimsAheadOf(new[] { Broadcast("Multi0") }, "Multi2");
			Assert.That(claims, Is.Empty);
		}
	}
}
