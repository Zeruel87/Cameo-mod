#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software.
 * It is made available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class ScoutBotModuleTest
	{
		static OpenRA.Actor ActorIdentityOnly()
		{
			// The ownership helper only stores or compares this reference; it never reads world or trait state.
			return (OpenRA.Actor)RuntimeHelpers.GetUninitializedObject(typeof(OpenRA.Actor));
		}

		[Test]
		public void ScoutsReturnToIdlePoolWhenNoRegionsNeedRecon()
		{
			var actor = ActorIdentityOnly();
			var scout = new UnitWposWrapper(actor);
			var scouts = new List<UnitWposWrapper> { scout };
			var targets = new Dictionary<OpenRA.Actor, (int Region, int AssignedTick)> { { actor, (4, 100) } };
			var idlePool = new List<UnitWposWrapper>();

			var noStaleRegions = ScoutBotModule.ReleaseScoutsIfNoStaleRegions(false, scouts, targets, idlePool);

			Assert.That(noStaleRegions, Is.True);
			Assert.That(scouts, Is.Empty);
			Assert.That(idlePool, Has.Count.EqualTo(1));
			Assert.That(idlePool[0], Is.SameAs(scout));
			Assert.That(targets.ContainsKey(actor), Is.False);
		}

		[Test]
		public void ReturningAlreadyIdleScoutPreservesExistingWrapperWithoutDuplicate()
		{
			var actor = ActorIdentityOnly();
			var scout = new UnitWposWrapper(actor);
			var existingPoolWrapper = new UnitWposWrapper(actor);
			var scouts = new List<UnitWposWrapper> { scout };
			var targets = new Dictionary<OpenRA.Actor, (int Region, int AssignedTick)> { { actor, (4, 100) } };
			var idlePool = new List<UnitWposWrapper> { existingPoolWrapper };

			ScoutBotModule.ReleaseScoutsIfNoStaleRegions(false, scouts, targets, idlePool);

			Assert.That(scouts, Is.Empty);
			Assert.That(idlePool, Has.Count.EqualTo(1));
			Assert.That(idlePool[0], Is.SameAs(existingPoolWrapper));
			Assert.That(targets.ContainsKey(actor), Is.False);
		}

		[Test]
		public void ScoutsStayClaimedWhileReconIsStillNeeded()
		{
			var actor = ActorIdentityOnly();
			var scout = new UnitWposWrapper(actor);
			var scouts = new List<UnitWposWrapper> { scout };
			var targets = new Dictionary<OpenRA.Actor, (int Region, int AssignedTick)> { { actor, (4, 100) } };
			var idlePool = new List<UnitWposWrapper>();

			var noStaleRegions = ScoutBotModule.ReleaseScoutsIfNoStaleRegions(true, scouts, targets, idlePool);

			Assert.That(noStaleRegions, Is.False);
			Assert.That(scouts, Is.EqualTo(new[] { scout }));
			Assert.That(idlePool, Is.Empty);
			Assert.That(targets.ContainsKey(actor), Is.True);
		}

		[Test]
		public void ScoutsRemainOwnedWhenIdlePoolIsUnavailable()
		{
			var actor = ActorIdentityOnly();
			var scout = new UnitWposWrapper(actor);
			var scouts = new List<UnitWposWrapper> { scout };
			var targets = new Dictionary<OpenRA.Actor, (int Region, int AssignedTick)> { { actor, (4, 100) } };

			var noStaleRegions = ScoutBotModule.ReleaseScoutsIfNoStaleRegions(false, scouts, targets, null);

			Assert.That(noStaleRegions, Is.True);
			Assert.That(scouts, Is.EqualTo(new[] { scout }));
			Assert.That(targets.ContainsKey(actor), Is.True);
		}

		[Test]
		public void ScoutRequestsAreRationedByTheCooldown()
		{
			// AI_ARCHITECTURE §12.12: 0 keeps the old behaviour (a request on every scan).
			Assert.That(ScoutBotModule.MayRequest(100, 50, 0), Is.True);

			// The first request is always allowed; after that, one per cooldown.
			Assert.That(ScoutBotModule.MayRequest(10, -1, 3000), Is.True);
			Assert.That(ScoutBotModule.MayRequest(2999, 0, 3000), Is.False);
			Assert.That(ScoutBotModule.MayRequest(3000, 0, 3000), Is.True);
		}
	}
}
