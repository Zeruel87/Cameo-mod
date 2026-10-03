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
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// TC-2f (AI_ARCHITECTURE.md 12.27): EMBER's raid dead-end — a Raid card's
	// RequiredValue is sized for a dedicated force, so the launch-time
	// affordability gate (RequiredValue <= idle pool) never lets one ride.
	// BestRaidForSteering re-picks among Raids alone under a relaxed cap;
	// deterministic: Priority desc, RequiredValue asc, publish order.
	[TestFixture]
	public class RaidSteeringTest
	{
		sealed class StubMissionProvider : IBotMissionProvider
		{
			public IReadOnlyList<BotMission> Missions { get; set; } = Array.Empty<BotMission>();
			public void MissionTaken(BotMission mission) { }
		}

		static BotMission Raid(int requiredValue, int priority = 0, int region = 0)
		{
			return new BotMission
			{
				Type = BotMissionType.Raid,
				RequiredValue = requiredValue,
				Priority = priority,
				RegionIndex = region
			};
		}

		[Test]
		public void NullOrEmptyProvidersReturnNull()
		{
			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(null, 1000), Is.Null);
			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(
				Array.Empty<IBotMissionProvider>(), 1000), Is.Null);
			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(
				new[] { new StubMissionProvider() }, 1000), Is.Null);
			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(
				new IBotMissionProvider[] { null }, 1000), Is.Null);
		}

		[Test]
		public void TheDeadEndItselfIsProven()
		{
			// The EMBER finding in one assertion pair: the card publishes at a
			// dedicated-force price, so the launch gate never takes it — the
			// relaxed cap does.
			var raid = Raid(12000, priority: 60);
			var providers = new[] { new StubMissionProvider { Missions = new[] { raid } } };

			Assert.That(SquadManagerBotModuleCA.BestAffordableMission(providers, 5000), Is.Null);
			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(providers, 15000), Is.SameAs(raid));
		}

		[Test]
		public void CapBoundaryIsInclusive()
		{
			var raid = Raid(9000);
			var providers = new[] { new StubMissionProvider { Missions = new[] { raid } } };

			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(providers, 9000), Is.SameAs(raid));
			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(providers, 8999), Is.Null);
		}

		[Test]
		public void NonRaidTypesNeverSteer()
		{
			var recon = new BotMission { Type = BotMissionType.Recon, RequiredValue = 0, Priority = 99 };
			var secure = new BotMission { Type = BotMissionType.Secure, RequiredValue = 0, Priority = 99 };
			var defend = new BotMission { Type = BotMissionType.Defend, RequiredValue = 0, Priority = 99 };
			var providers = new[]
			{
				new StubMissionProvider { Missions = new BotMission[] { defend, secure, recon } }
			};

			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(providers, int.MaxValue), Is.Null);
		}

		[Test]
		public void ZeroCapStillTakesAFreeRaid()
		{
			// RaidMissionSteerMinValue is a cap floor, not a RequiredValue floor —
			// cap 0 admits the 0-priced raid.
			var raid = Raid(0);
			var providers = new[] { new StubMissionProvider { Missions = new[] { raid } } };

			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(providers, 0), Is.SameAs(raid));
		}

		[Test]
		public void HighestPriorityWinsOverLowerRequiredValue()
		{
			var cheap = Raid(100, priority: 50, region: 1);
			var dear = Raid(900, priority: 80, region: 2);
			var providers = new[]
			{
				new StubMissionProvider { Missions = new[] { cheap, dear } }
			};

			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(providers, 1000), Is.SameAs(dear));
		}

		[Test]
		public void LowestRequiredValueBreaksAPriorityTie()
		{
			var dear = Raid(900, priority: 80, region: 1);
			var cheap = Raid(100, priority: 80, region: 2);
			var providers = new[]
			{
				new StubMissionProvider { Missions = new[] { dear, cheap } }
			};

			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(providers, 1000), Is.SameAs(cheap));
		}

		[Test]
		public void PublishOrderIsStableOnAFullTie()
		{
			var first = Raid(500, priority: 60, region: 1);
			var second = Raid(500, priority: 60, region: 2);
			var providers = new[]
			{
				new StubMissionProvider { Missions = new[] { first } },
				new StubMissionProvider { Missions = new[] { second } }
			};

			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(providers, 1000), Is.SameAs(first));
		}

		[Test]
		public void NullEntriesInTheMissionListAreSkipped()
		{
			var raid = Raid(500, priority: 10);
			var providers = new[]
			{
				new StubMissionProvider { Missions = new BotMission[] { null, raid } }
			};

			Assert.That(SquadManagerBotModuleCA.BestRaidForSteering(providers, 1000), Is.SameAs(raid));
		}
	}
}
