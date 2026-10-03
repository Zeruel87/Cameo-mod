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
using OpenRA.Mods.CA.Traits.BotModules.Squads;

namespace OpenRA.Mods.Cameo.Test
{
	// CA-5 (AI_ARCHITECTURE.md 12.8): the doctrine split maps role members to
	// Fighter/Gunship/Bomber squads; with AirDoctrineEnabled off (or an unroled
	// transport/scout) everything stays in generic Air squads.
	[TestFixture]
	public class AirDoctrineSquadTypeTest
	{
		static readonly IReadOnlySet<string> Fighters = new HashSet<string> { "mig" };
		static readonly IReadOnlySet<string> Gunships = new HashSet<string> { "orca" };
		static readonly IReadOnlySet<string> Bombers = new HashSet<string> { "b2" };

		static SquadCAType Classify(bool enabled, string name) =>
			SquadManagerBotModuleCA.AirSquadTypeFor(enabled, name, Fighters, Gunships, Bombers);

		[Test]
		public void DoctrineOffKeepsGenericAir()
		{
			Assert.That(Classify(false, "mig"), Is.EqualTo(SquadCAType.Air));
			Assert.That(Classify(false, "orca"), Is.EqualTo(SquadCAType.Air));
			Assert.That(Classify(false, "b2"), Is.EqualTo(SquadCAType.Air));
		}

		[Test]
		public void DoctrineOnMapsRoles()
		{
			Assert.That(Classify(true, "mig"), Is.EqualTo(SquadCAType.Fighter));
			Assert.That(Classify(true, "orca"), Is.EqualTo(SquadCAType.Gunship));
			Assert.That(Classify(true, "b2"), Is.EqualTo(SquadCAType.Bomber));
		}

		[Test]
		public void UnroledStaysGenericAir()
		{
			Assert.That(Classify(true, "chinook"), Is.EqualTo(SquadCAType.Air));
		}

		// §12.8 ordering rule (PR #663 review): a WRITTEN GuerrillaTypes listing
		// outranks a derived air role - but only with the doctrine on. Flag off
		// keeps master's air-first order so @classic's overlap actors
		// (ixian_airdrone, ra2_allies_harrier) keep routing to Air as written.
		[Test]
		public void WrittenGuerrillaOutranksDerivedAirRole()
		{
			var guerrilla = new HashSet<string> { "raider_jet" };

			Assert.That(SquadManagerBotModuleCA.GuerrillaOutranksAir(true, "raider_jet", guerrilla), Is.True);
			Assert.That(SquadManagerBotModuleCA.GuerrillaOutranksAir(false, "raider_jet", guerrilla), Is.False);
			Assert.That(SquadManagerBotModuleCA.GuerrillaOutranksAir(true, "mig", guerrilla), Is.False);
		}

		// LC6 semantic fog canary: a violation is exactly "fog is binding AND the
		// consumed actor was not observable". No fog provider -> legacy omniscient
		// scans are honest by design -> silent; observed actor -> silent.
		[Test]
		public void FogCanaryFiresOnlyOnUnseenConsumedActor()
		{
			var lines = new List<string>();
			void Log(string s) => lines.Add(s);

			Assert.That(SquadManagerBotModuleCA.FogCanaryViolation(true, false, "site", "sam", Log), Is.True);
			Assert.That(lines, Has.Count.EqualTo(1));
			Assert.That(lines[0], Does.Contain("FOGCANARY-VIOLATION").And.Contain("site").And.Contain("sam"));

			lines.Clear();
			Assert.That(SquadManagerBotModuleCA.FogCanaryViolation(false, false, "site", "sam", Log), Is.False);
			Assert.That(SquadManagerBotModuleCA.FogCanaryViolation(true, true, "site", "harv", Log), Is.False);
			Assert.That(lines, Is.Empty);
		}

		// §12.8 strike/CAS lists as shipped defaults - a yaml override can change
		// them, but the code defaults pin the doctrine's intent.
		[Test]
		public void PriorityTagDefaultsMatchTheDoctrine()
		{
			var info = new SquadManagerBotModuleCAInfo();

			Assert.That(info.BomberPriorityTags, Is.SupersetOf(new[]
				{ "superweapon", "conyard", "production", "refinery", "power" }));
			Assert.That(info.GunshipPriorityTags, Is.SupersetOf(new[] { "artillery", "harvester" }));
			Assert.That(info.FighterPriorityTags, Is.SupersetOf(new[] { "harvester" }));
			Assert.That(info.AirDoctrineEnabled, Is.False);
		}
	}
}
