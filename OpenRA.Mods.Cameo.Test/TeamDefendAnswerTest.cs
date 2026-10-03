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

using NUnit.Framework;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// TC-2b (AI_ARCHITECTURE.md 12.17): TopDefendRequest picks the ally most worth
	// answering — highest urgency level, ties to the weakest army. Broadcasts without
	// a defend position or not requesting defence never win.
	[TestFixture]
	public class TeamDefendAnswerTest
	{
		static TeamBroadcast B(int urgency, int army, bool requests, int x = 1000) =>
			new(1000, army, urgency, 40, DirectorPhase.Pressure, null, requests,
				new WPos(x * 1024, 0, 0));

		[Test]
		public void PicksTheHighestUrgency()
		{
			var pressured = B(1, 9000, true);
			var emergency = B(2, 3000, true);
			Assert.That(TeamBlackboard.TopDefendRequest(new[] { pressured, emergency }),
				Is.SameAs(emergency));
		}

		[Test]
		public void TieGoesToTheWeakestAlly()
		{
			var strong = B(1, 9000, true);
			var weak = B(1, 2000, true);
			Assert.That(TeamBlackboard.TopDefendRequest(new[] { strong, weak }), Is.SameAs(weak),
				"equal urgency — the ally with the least army needs help most");
		}

		[Test]
		public void SkipsNonRequestsAndPositionless()
		{
			var quiet = B(2, 100, false);                    // urgent but not asking
			var nowhere = B(2, 100, true, 0);                // asking but WPos.Zero position
			var asking = B(0, 5000, true);
			Assert.That(TeamBlackboard.TopDefendRequest(new[] { quiet, nowhere, asking }),
				Is.SameAs(asking));
		}

		[Test]
		public void EmptyInputIsNull()
		{
			Assert.That(TeamBlackboard.TopDefendRequest(null), Is.Null);
			Assert.That(TeamBlackboard.TopDefendRequest(new TeamBroadcast[0]), Is.Null);
			Assert.That(TeamBlackboard.TopDefendRequest(new[] { B(0, 5000, false) }), Is.Null,
				"a 1v1 reading — nobody asking — is the honest null, not a default");
		}
	}
}
