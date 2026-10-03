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
using OpenRA;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// CA-2 (AI_ARCHITECTURE.md 12.6): FransGroundDefendForcePreservationGuard's
	// shape ported to the protect/preposition draft — a defence response keeps a
	// reserve instead of stripping the idle pool, unless the attacker is already
	// inside the base (emergency) or the pool is too small to split.
	[TestFixture]
	public class DefendDraftLimitTest
	{
		static SquadManagerBotModuleCAInfo Armed() => FieldLoader.Load<SquadManagerBotModuleCAInfo>(
			new MiniYaml("", new[] { new MiniYamlNode("UseDefendPreservation", new MiniYaml("true")) }));

		[Test]
		public void FlagOffDraftsEverything()
		{
			var info = new SquadManagerBotModuleCAInfo();
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(20, false, info), Is.EqualTo(20),
				"flag-off must commit the whole pool — bit-identical pre-CA-2 behaviour");
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(0, false, info), Is.EqualTo(0));
		}

		[Test]
		public void EmergencyDraftsEverything()
		{
			var info = Armed();
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(20, true, info), Is.EqualTo(20),
				"attacker inside the base radius = the donor's short-ETA emergency: full commit");
		}

		[Test]
		public void SmallPoolDraftsEverything()
		{
			var info = Armed();
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(5, false, info), Is.EqualTo(5),
				"below DefendPreservationTriggerUnits (6) there is nothing to split");
		}

		[Test]
		public void GuardKeepsTheLargerFloor()
		{
			var info = Armed();

			// 10 draftable: 25% = 2.5 -> 2, but MinReserveUnits=4 is the floor: keep 4, draft 6.
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(10, false, info), Is.EqualTo(6));

			// 40 draftable: 25% = 10 > MinReserveUnits: keep 10, draft 30.
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(40, false, info), Is.EqualTo(30));
		}

		[Test]
		public void ReserveNeverExceedsThePool()
		{
			var info = Armed();
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(6, false, info),
				Is.GreaterThanOrEqualTo(0).And.LessThanOrEqualTo(6));
		}
	}
}
