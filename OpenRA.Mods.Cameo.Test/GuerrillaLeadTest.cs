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
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// §12.14 (AI_ARCHITECTURE.md) Guerrilla map-control lead — the telemetry ratio
	// "regions we hold fresh intel on" per "region with remembered enemy presence".
	// The share denominators cancel, so the raw counts divide directly; an unseen
	// enemy reads as at-target (1.0), never as infinite or zero.
	[TestFixture]
	public class GuerrillaLeadTest
	{
		[Test]
		public void NoEnemyPresenceReadsAtTarget()
		{
			Assert.That(MasterAiBotModule.GuerrillaLeadFor(0, 0), Is.EqualTo(1.0),
				"nothing seen, nothing remembered: at-target, not zero");
			Assert.That(MasterAiBotModule.GuerrillaLeadFor(40, 0), Is.EqualTo(1.0),
				"full coverage with no remembered enemy is still at-target — scouting harder is pointless");
		}

		[Test]
		public void LeadIsFreshPerPresence()
		{
			Assert.That(MasterAiBotModule.GuerrillaLeadFor(10, 10), Is.EqualTo(1.0),
				"fresh coverage matching enemy presence is parity");
			Assert.That(MasterAiBotModule.GuerrillaLeadFor(5, 10), Is.EqualTo(0.5),
				"half the contested map fresh reads as half a lead");
			Assert.That(MasterAiBotModule.GuerrillaLeadFor(20, 10), Is.EqualTo(2.0),
				"coverage beyond the contested regions reads above target — the lead is allowed to exceed 1");
		}

		[Test]
		public void EdgeCountsAreSane()
		{
			Assert.That(MasterAiBotModule.GuerrillaLeadFor(0, 10), Is.EqualTo(0.0),
				"zero fresh intel on a remembered enemy is a zero lead, the worst case");
			Assert.That(MasterAiBotModule.GuerrillaLeadFor(0, 0), Is.EqualTo(1.0));
		}

		// PL-2 (§12.14): the consumer leg — behind on map control grows the scout cap,
		// linear in the deficit, capped at base + extra. lean >= 1 (at target, flag off,
		// wrong personality) keeps the configured cap bit-identical.
		[Test]
		public void TrailingLeadRaisesTheScoutCap()
		{
			Assert.That(ScoutBotModule.EffectiveMaxScouts(2, 1.0, 2), Is.EqualTo(2),
				"at target: configured cap, untouched");
			Assert.That(ScoutBotModule.EffectiveMaxScouts(2, 0.5, 2), Is.EqualTo(3),
				"half a lead adds half the extra allowance");
			Assert.That(ScoutBotModule.EffectiveMaxScouts(2, 0.0, 2), Is.EqualTo(4),
				"full deficit adds the whole extra allowance");
			Assert.That(ScoutBotModule.EffectiveMaxScouts(2, 1.0, 0), Is.EqualTo(2),
				"zero extra configured: nothing to add");
		}

		[Test]
		public void TheGuerrillaLeadReachesTheConsumerSeam()
		{
			var situation = new BotSituation { OwnPersonality = "guerrilla" };
			situation.GuerrillaLead = 0.4;

			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, true, situation, "guerrilla", 50),
				Is.EqualTo(0.7).Within(1e-9), "0.4 lead, 50% max lean: multiplier 1 - 0.6 x 0.5");
			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, true, situation, "steamroller", 50),
				Is.EqualTo(1.0), "a different personality asks and leans nothing");
			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, false, situation, "guerrilla", 50),
				Is.EqualTo(1.0), "flag off: bit-identical no-lean");
		}

		// PL-2 squad leg: while the lead trails, the join chance rises toward 100 —
		// more raiders crossing the map are incidental scouts feeding regions_fresh.
		// A configured 0 is a hard off-switch the lean must not revive.
		[Test]
		public void TrailingLeadRaisesTheJoinChanceTowardFull()
		{
			Assert.That(SquadManagerBotModuleCA.EffectiveJoinGuerrilla(50, 1.0), Is.EqualTo(50),
				"at target: the configured roll, untouched");
			Assert.That(SquadManagerBotModuleCA.EffectiveJoinGuerrilla(50, 0.0), Is.EqualTo(100),
				"full deficit: every new raider joins");
			Assert.That(SquadManagerBotModuleCA.EffectiveJoinGuerrilla(50, 0.5), Is.EqualTo(75),
				"half-deficit at 50% max-lean: halfway to full");
			Assert.That(SquadManagerBotModuleCA.EffectiveJoinGuerrilla(0, 0.0), Is.EqualTo(0),
				"JoinGuerrilla 0 means never — the lean cannot create guerrilla squads from nothing");
		}
	}
}
