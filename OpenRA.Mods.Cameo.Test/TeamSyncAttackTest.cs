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
	// TC-2a (AI_ARCHITECTURE.md 12.17): an allied Director's Climax opens our launch
	// window too — team waves surge together. The effective scale is min(own, climax)
	// while an ally climaxes; no ally climax or no allied bots = the own phase's
	// scale verbatim (a 1v1 reads AnyClimax=false and is bit-identical).
	[TestFixture]
	public class TeamSyncAttackTest
	{
		[Test]
		public void AllyClimaxCapsAtTheClimaxScale()
		{
			Assert.That(SquadManagerBotModuleCA.TeamSyncForceScale(100, true, 55), Is.EqualTo(55),
				"BuildUp own phase + ally climax = join the push at the climax bar");
			Assert.That(SquadManagerBotModuleCA.TeamSyncForceScale(150, true, 55), Is.EqualTo(55),
				"even Relief's rebuild joins a fleeting ally climax");
			Assert.That(SquadManagerBotModuleCA.TeamSyncForceScale(85, true, 55), Is.EqualTo(55));
		}

		[Test]
		public void OwnClimaxIsNotRaisedByAnAlly()
		{
			Assert.That(SquadManagerBotModuleCA.TeamSyncForceScale(55, true, 55), Is.EqualTo(55));
			Assert.That(SquadManagerBotModuleCA.TeamSyncForceScale(40, true, 55), Is.EqualTo(40),
				"a custom lower climax scale keeps its own urgency — min only lowers");
		}

		[Test]
		public void NoAllyClimaxLeavesTheOwnScaleAlone()
		{
			Assert.That(SquadManagerBotModuleCA.TeamSyncForceScale(100, false, 55), Is.EqualTo(100));
			Assert.That(SquadManagerBotModuleCA.TeamSyncForceScale(150, false, 55), Is.EqualTo(150));
			Assert.That(SquadManagerBotModuleCA.TeamSyncForceScale(85, false, 55), Is.EqualTo(85));
		}
	}
}
